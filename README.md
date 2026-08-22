#
Exception in thread Thread-1 (run_flask):
Traceback (most recent call last):
  File "/usr/lib/python3.13/threading.py", line 1043, in _bootstrap_inner
    self.run()
    ~~~~~~~~^^
  File "/usr/lib/python3.13/threading.py", line 994, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/admin/Desktop/display/display-main.py", line 724, in run_flask
    socketio.run(flask_app, debug=True, use_reloader=False, host='192.168.1.76', port=5000)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3/dist-packages/flask_socketio/__init__.py", line 650, in run
    raise RuntimeError('The Werkzeug web server is not '
    ...<2 lines>...
                       'run() method to disable this error.')
RuntimeError: The Werkzeug web server is not designed to run in production. Pass allow_unsafe_werkzeug=True to the run() method to disable this error.
qt.qpa.xcb: could not connect to display 
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to load the Qt xcb platform plugin.
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: wayland, eglfs, minimal, offscreen, vnc, minimalegl, xcb, linuxfb, vkkhrdisplay, wayland-egl.

Aborted
