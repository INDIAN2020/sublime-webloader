
Webloader - a Sublime Text 2 plugin
===================================

Updates css/less on a page _live as you type_, or when saving js/html/php.

Uses websockets, works without a webserver, with multiple pages or files at once. You can run javascript on a page directly from Sublime, define custom actions when you edit/save/load, or add more file extensions. Nothing else to install but the plugin.

__Still very much in development, but suggestions and fixes are welcome.__

How to use:
-----------
- no package control yet, but it's quite easy to install manually!
- unzip the repo, move the Webloader folder under your Sublime Packages folder:
  - windows: `youruserfolder\AppData\Roaming\Sublime Text 2\Packages`
  - os x: `~/Library/Application Support/Sublime Text 2`
  - linux: `~/.config/sublime-text-2`
- restart Sublime (the console should show a `[Webloader]` message if the plugin loaded)
- open `Webloader/demo/index.html` in a browser (the javascript console shows if it's connected to the plugin)
- edit `sample.css` with Sublime, and see the changes on the page *as you type*
- open `index.html` with Sublime, and save it, this should refresh the page
- if you put this under your webserver (not opened as file:///), `.less` files can be updated live too!

More options:
-------------
- to use it in your own project, include a less.js, a prototype.js, and the webloader.js (works with the included versions)
- be sure to put webloader.js __after__ any link or script tags you want to update!
- if the web page sees your machine on a different ip than localhost, include that ip:
  - `<script src='webloader.js?server=192.168.0.100:9000'></script>`
- customize settings in the Packages/Webloader/Webloader.sublime-settings file
  - not every setting is supported yet, but this should be mentioned in the comments

Credits:
--------

- plugin code on the [sublime API] and standard python library
- uses less.js for compiling [lesscss.org], and [prototype] for simplifying life

License:
--------

- Contact: <http://rozsahegyi.info>
- License: [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License][license]. ![Creative Commons License][image]


----

TODO:
-----

- file urls can be urlencoded, which is often the case in file:/// mode, handle this; test file mode more
- complete js command: quick panel if multiple clients, send to selected (or a single) client
- hotkey for page reload for the selected/single client?
- add menu items for options and commands
- submit to package control <http://wbond.net/sublime_packages/package_control/package_developers>
- revisit and test bigger css updates, like whole less blocks, fix selector updates (not updated on edit, only with saving)
  - faster updates: could only send the current key-value pair, between previous and next semicolons or brackets, maybe validate them
  - multiple selections: with less you probably factor out frequently used values into variables, so not a priority
  - a full refresh would be is necessary, which is slow with large files + typing; could timeout for 0.5-1sec when multiple selections



  [sublime API]: http://www.sublimetext.com/docs/2/api_reference.html
  [lesscss.org]: http://lesscss.org/
  [prototype]: http://prototypejs.org/
  [image]: http://i.creativecommons.org/l/by-nc-sa/3.0/88x31.png
  [license]: http://creativecommons.org/licenses/by-nc-sa/3.0/
