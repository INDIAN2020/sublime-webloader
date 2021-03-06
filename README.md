
Webloader - a Sublime Text 2 plugin
===================================

Updates css/less on a page _live as you type_, or when saving js/html/php.

Uses websockets, works without a webserver, with multiple pages or files at once. You can run javascript on a page directly from Sublime, define custom actions when you edit/save/load, or add more file extensions. Nothing else to install but the plugin.

__Still very much in development, but suggestions and fixes are welcome.__

How to use:
-----------
- install with Package Control: `ctrl-shift-p`, `Package Control: Install Package`, `Webloader`
- if not available there yet, it's quite easy to install manually:
  - download as zip, unzip, and copy the root folder's contents into Packages/Webloader/
  - windows: `youruserfolder\AppData\Roaming\Sublime Text 2\Packages\Webloader`
  - os x: `~/Library/Application Support/Sublime Text 2/Webloader`
  - linux: `~/.config/sublime-text-2/Webloader`
  - restart Sublime (the console should show a `Webloader:` message if the plugin loaded)
- open `Webloader/demo/index.html` in a browser (the javascript console should tell if it started watching files)
- edit `demo.css` with Sublime, and see the changes on the page *as you type*
- open `index.html` with Sublime, add some text, save it, this should refresh the page
- if you put this under your webserver (opened as `http://.../index.html`), `.less` files can be updated live too!

Used in your projects:
----------------------
- __in one line__: install the plugin, and include webloader.js (and if you need it, less.js) in your page
- webloader.js works standalone, no js framework necessary; only needs a less.js if you use .less files (tested with less-1.3.3)
- non-localhost websites:
  - if the page is not on your machine, or sees you as a different ip than localhost/127.0.0.1/::1
  - define your ip: `<script src='webloader.js?server=192.168.0.100:9000'></script>`
  - and you may have to enable this port in your firewall
- check out the settings in the `Packages/Webloader/Webloader.sublime-settings` file:
  - server: if you want to change the above port
  - clients: if you do not trust your lan, or opened the above port to the wide internet
  - save\_parsed\_less: if you want to enable converting `.less` to `.css` on save
  - watch_events: if you want to add or remove file types
  - sites: if you use virthosts, symlink directories to your docroot, or similar
- you can run javascript on a page directly from Sublime with `ctrl-shift-j`
- you can send commands to the server with `ctrl-shift-c` (currently only supports stop/restart/start)

Future plans:
-------------
- more polished codebase, as I'm still changing it around daily
- more/simpler options and Sublime file-actions
- I may release under a less restrictive license later, when I feel it's ready

License:
--------
- Contact: <http://rozsahegyi.info>
- License: [Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported License][license].
- Summary: free to download/share/use, but you have to credit me, and you can't sell, alter, or bundle this.
- ![Creative Commons License][image]

Credits:
--------
- plugin code on the [sublime API] and standard python library
- uses [less.js] for compiling .less files



  [sublime API]: http://www.sublimetext.com/docs/2/api_reference.html
  [less.js]: http://lesscss.org/
  [image]: http://i.creativecommons.org/l/by-nc-nd/3.0/88x31.png
  [license]: http://creativecommons.org/licenses/by-nc-nd/3.0/
