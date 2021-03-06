# encoding: utf-8

import os, urllib, urlparse, json, re, itertools, operator
import websocket

class Message(dict):
	"""Dict with attribute access, credits to: http://stackoverflow.com/a/14620633/1393194"""
	def __init__(self, content, *args, **kw):
		if isinstance(content, (str, unicode)):
			content = self.unpack(content)
		elif not hasattr(content, 'iteritems'):
			raise Exception('Message with %s argument' % type(content))
		super(Message, self).__init__(content, *args, **kw)
		self.__dict__ = self

	def pack(self): return json.dumps(self, ensure_ascii=False)
	def unpack(self, content): return json.loads(content)


class Server(websocket.Server):

	def __init__(self, address=None, requesthandler=None, plugin=None, client_ips=None, *args, **kw):
		if not requesthandler: requesthandler = Client
		websocket.Server.__init__(self, address, requesthandler, *args, **kw)
		self.plugin = plugin
		self.client_ips = client_ips

	# do not call in same thread as serve_forever, that will deadlock
	def shutdown(self, reason=''):
		if not self.running: return
		self.log('-', 'server stopped' + ((' (%s)' % reason) if reason else ''))
		# also close socket - it's not closed by default, but this server
		# can be restarted on the same port, so free up the socket
		websocket.Server.shutdown(self)
		self.socket.close()

	def server_active(self):
		websocket.Server.server_active(self)
		self.log('listening on %s:%d%s' % (self.server_address + \
			(self.test_mode and ' in test mode (stopping after %d clients)' % self.test_mode or '',)))

	def verify_request(self, request, client_address):
		if not self.client_ips: return True
		ip = client_address[0]
		return next((False for k, v in self.client_ips.iteritems() if (v.match(ip) if v else ip == k)), True)

	def command(self, cmd, filename='', content='', client=None):
		if not (cmd and len(cmd)): return False
		message = Message({'cmd': cmd, 'filename': filename, 'content': content})
		if isinstance(client, (Client, int)):
			if isinstance(filename, int):
				client = self.clients[client] if 0 <= client < len(self.clients) else None
			return [client.send(message)] if client else [None]
		return self.for_each_client(self.send_command, message)

	def send_command(self, client, message):
		return client.send(message)

	def watch_events(self):
		return self.plugin and self.plugin.watch_events

	def clients_watching(self, filename):
		return filter(operator.methodcaller('watches', filename), self.clients)

	def on_message(self, client, message):
		self.plugin.message(client, message)


class Client(websocket.Client):
	"""Stores which files to watch, so there is less traffic when broadcasting events."""

	def setup(self):
		websocket.Client.setup(self) # parse request, set self.path, etc

		# these types should match only against the watched file list, but not patterns
		self.noregexp_extensions = ['css', 'less', 'sass', 'scss', 'js']
		self.files = {}
		self.patterns = {}
		if not hasattr(self, 'path'): self.path = ''

		# clients should send their full page url (path is /?client=pageurl)
		url = urlparse.urlparse(self.path) # original url parts
		q = urlparse.parse_qs(url.query, True) # params
		url = urlparse.urlparse(q.get('client', [''])[0]) # pageurl

		# all empty if no client param
		self.protocol = url.scheme
		self.host = url.netloc
		self.path = url.path
		self.page = url.netloc + url.path
		if self.protocol == 'file': self.page = self.page[self.page.find('/', 1):]

		# assume virthost if not localhost, the domain has a dot, and is not an ip
		self.localhost = url.netloc in ['localhost', '127.0.0.1', '::1']
		self.virthost = not self.localhost and self.host.find('.') > -1 and not self.host.replace('.', '').isdigit()

		self.log('+', 'connection from %s:%d %s://%s' % (self.client_address + (self.protocol, self.page)))

	def on_read(self, message):
		self.log("<", "'%s' (%d)" % (message.replace('\n', '\\n')[0:80], len(message)))
		message = Message(message)
		cmd, filename, content = message.get('cmd'), message.get('filename'), message.get('content')

		if cmd == 'watch': self.watch_files(content) # replaces existing watchlist
		elif cmd == 'message': self.server.on_message(self, content)
		elif cmd == 'parsed_less': self.save_parsed_less(filename, content)
		elif cmd == 'js_results': self.show_js_results(filename, content)
		return True # continue reading

	def on_send(self, message):
		# leave the original message intact, it's passed around
		message = Message(message)
		filename = message.get('filename')
		# if no filename, any message can go on, otherwise only matching files
		if filename:
			matched = self.watches(filename)
			if not matched: return
			if isinstance(matched, tuple):
				# a regexp match should fit the domain+basepath of the client
				if not self.page.startswith(matched[0]): return
				matched = '...'.join(matched)
				message['cmd'] = 'reload_page'
			# don't send the full filename, just the matched part (privacy)
			message['filename'] = matched
		message = message.pack()
		self.log(">", "'%s' (%d)" % (message.replace('\n', '\\n')[0:140], len(message)))
		return message

	def watch_files(self, files):
		if not (files and isinstance(files, list)): return
		self.files = dict.fromkeys(files)
		self.update_patterns()

	# make tests
	def update_patterns(self, reset=0):
		"""
		With a new file list, create a pattern for matching certain files.

		Resource files (css/less/js) can be matched based on their url.
		Types like html or php can be matched if they match the page's url,
		but this is not always the case. (See docs for more on this.)

		The method finds longest common folder between the page's url and
		the resource files, and creates a "common/*.html" -like pattern.
		"""

		# no plugin, no settings, no patterns
		events = self.server and self.server.watch_events()
		if not events or not isinstance(events, dict): return

		if reset:
			self.files = dict(f for f in self.files.iteritems() if f[1] is None)
			self.patterns = {}

		# end patterns with watched file extensions, except js/css/less
		extensions = [x.strip() for x in events.keys() \
			if x and not x in self.noregexp_extensions and isinstance(x, (str, unicode))]
		if not extensions: return
		filepaths = r'([\w\._/-]+\.(?:%s))$' % '|'.join(extensions)

		sites = self.server.plugin.sites
		if sites:
			# store patterns by 'url folder', so multiple folders can point to
			# the same url, and we can still retrieve the url (by first space)
			sites = ((v + ' ' + k, re.compile('.*%s(.+)' % k)) for k, v in sites.iteritems() if k)
			self.patterns.update(dict(sites))

		# TODO: refactor/simplify
		def longest_common(path, files, sep='/'):
			watched_url = lambda url, value: value is None and url[0] == sep
			exploded = lambda url: [url] + url[1:].split(sep)
			decoded = lambda url: urllib.unquote_plus(url)

			path = path.split(sep)
			files = [exploded(decoded(u)) for u, v in files.iteritems() if watched_url(u, v)]

			res = None
			for i in xrange(1, len(path)):
				files = [x for x in files if x[i] == path[i]]
				if files: res = files[0], i
				else: break
			if not res: return sep
			return sep + sep.join(res[0][1:res[1] + 1]) + sep

		path = urllib.unquote_plus(self.path)

		# in file mode, clients use the same regexp, and send only file paths
		# so drop the "domain" (first segment) of the page path
		if self.protocol == 'file': path = path[path.find('/', 1):]

		common = longest_common(path, self.files)
		if self.virthost: common = '/' + self.host + common
		self.common = common
		if len(common) < 2: return # don't make too simple patterns (like */*.html)

		# don't replace user-defined stuff
		key = self.host + common
		if key not in self.patterns: self.patterns[key] = re.compile('.*' + common + filepaths)

	def file_matches(self, pattern, path):
		"""Returns whether path matches pattern."""

		# path is a full filepath + filename (always with '/' separators)

		# pattern is a tuple of either:   # meaning and return values:
		# (/nonmatching/file.html, False) # already checked, return false
		# (/www/x/a/b.html, /a/b.html)    # already checked match, pattern[1]
		# (/a/b.html, None)               # if path.endswith(url), return url
		# (*/path/*.html dirpath, regexp) # if path matches, (url part, match)

		if not pattern or not isinstance(pattern, tuple) or len(pattern) != 2: return False
		patt, value = pattern
		if value is False or patt == path: return value
		if value is None: return path.endswith(urllib.unquote_plus(patt)) and patt
		try: return (patt.split(' ', 1)[0], value.match(path).group(1))
		except: pass
		return False

	def watches(self, filename):
		"""Returns whether this client watches this file."""
		if not isinstance(filename, (str, unicode)): return False
		if not filename in self.files:
			# check exact file paths first, then patterns, then cache the result
			patterns = (x for x in itertools.chain(self.files.iteritems(), self.patterns.iteritems()))
			matches = lambda x: self.file_matches(x, filename)
			self.files[filename] = next(itertools.ifilter(None, itertools.imap(matches, patterns)), False)
		return filename if self.files[filename] is None else self.files[filename]

	def save_parsed_less(self, filename, parsed):
		try:
			save = self.server.plugin.save_parsed_less
			if not save or not filename.endswith('.less'): return
			related = next((k for k, v in self.files.iteritems() if k and v == filename), None)
			self.log('related file:', related)
			if not related or not os.path.isfile(related): return
			related = related[0:-4] + 'css'
			self.log('saving to:', related)
			if save == 1 and os.path.isfile(related):
				self.server.plugin.status_message("can't overwrite %s" % os.path.basename(related))
				self.server.plugin.console_message("%s already exists - allow css overwrites with the 'save_parsed_less' setting" % related)
				return
			with open(related, 'w') as f: f.write(parsed);
			self.server.plugin.status_message("converted and saved to %s" % related)
		except Exception as e:
			self.log('while saving parsed less:', e)

	def show_js_results(self, js, content):
		self.server.plugin.console_message('javascript results of "%s": %s' % (js, content), open=1)


if __name__ == '__main__':
	import threading
	from time import sleep
	print 'starting server'
	server = Server(('localhost', 9000), Client, debug=2).start()
	print threading.enumerate()
	print 'server running:', server
	sleep(10)
	print 'shutting down'
	server.shutdown()
	sleep(1)
	print threading.enumerate()
	print 'restarting server'
	server = Server(('localhost', 9000), Client, debug=2).start()
	print threading.enumerate()
	print 'server running:', server
	sleep(5)
	server.shutdown()
	sleep(1)
	print threading.enumerate()
	print 'done'
