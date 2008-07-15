"""radiocontrol.py -- HTTP server for controlling & getting information from the radio station.

getting information is done by keeping a reference to the playlist object.
controlling the radio is done using a message queue that the radio checks periodically.
"""
from threading import Thread, Lock
from Queue import Queue, Empty
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from urllib import unquote
import re, time

import radio_settings

# queue for communication between radio and control threads
messages = None

def get_all_messages():
    returned_messages = []
    try:
        while 1:
            returned_messages.append(messages.get_nowait())
    except Empty:
        pass
    return returned_messages
    
# for the handler to tell the server to shut down
class ShutdownException:
    pass

# handles requests to the http server
class RadioControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Cache-control", "no-cache")
        self.send_header("Expires", "Thu, 01 Dec 1994 16:00:00 GMT")
        self.end_headers()
        path_components = [unquote(c) for c in self.path.split('/')[1:]]
        
        # either respond to these urls or put them in the message queue
        if path_components[0] == "":
            page = open("admin.html")
            self.wfile.write(page.read())
            page.close()
        elif path_components[0] == "list":
            for song in playlist.playlist:
                self.wfile.write("%s\n" % song)
        elif path_components[0] == "current":
            self.wfile.write(playlist.position)
        else:
            messages.put(path_components)

        # urls the control server responds to directly
        if path_components[0] == "rescan":
            print "rescan started"
            start_time = time.time()
            playlist.rescan()
            print "rescan took %g seconds" % (time.time() - start_time)
            self.wfile.write("done")
            return
        elif path_components[0] == "shutdown":
            self.wfile.write("Bye!")
            self.wfile.close()
            raise ShutdownException
            
class RadioControlThread(Thread):
    def __init__(self, playlist_obj):
        global playlist, messages
        playlist = playlist_obj
        
        messages = Queue()

        Thread.__init__(self)
        self.setDaemon(True)
        self.start()
        
    def do_nothing(*args):
        return

    def run(self):
        # stop HTTPServer from barfing all over my stderr
        BaseHTTPRequestHandler.log_message = self.do_nothing
        HTTPServer.handle_error = self.do_nothing 
       
        server = HTTPServer((radio_settings.control_host, radio_settings.control_port), RadioControlHandler)
        try:
            server.serve_forever()
        except (KeyboardInterrupt, ShutdownException):
            pass
        server.server_close()