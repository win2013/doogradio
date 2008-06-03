"""icecast.py -- icecast2 source in pure python

connection settings are in stream_settings.py.
takes care of protocol and timing.
example:
    icecast.connect()
    while 1:
        ...
        icecast.send(mp3data) # bitrate is maintained by sleeping in this function
    icecast.close()
"""
import socket
import stream_settings
import time
import shoutpy
from base64 import b64encode
from urllib import urlencode

# format a dict as HTTP request headers, but with configurable line endings
# (since icecast wants \n instead of \r\n in some places)
def request_format(request, line_separator="\n"):
    return line_separator.join(["%s: %s" % (key, str(val)) for (key, val) in request.items()])

def connect():
    global s, packets_sent, start_time
    s = shoutpy.Shout()
    s.host = stream_settings.host
    s.port = stream_settings.port
    s.password = stream_settings.password
    s.mount = stream_settings.mount_point
    s.format = shoutpy.FORMAT_MP3
    
    s.name = stream_settings.name
    s.url = stream_settings.url
    s.genre = stream_settings.genre
    s.bitrate = stream_settings.bitrate
    s.description = stream_settings.description
    s.set_audio_info( "bitrate", str( stream_settings.bitrate ) )
    s.set_audio_info( "samplerate", str( stream_settings.samplerate ) )
    s.set_audio_info( "channels", str( stream_settings.channels ) )
    
    s.open()
        
# update the metadata using a new socket -- i guess there's no other useful keys besides "song"
def update_metadata(song):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((stream_settings.host, stream_settings.port))
    s.sendall("GET /admin/metadata?%s HTTP/1.0\r\n%s\r\n\r\n" % (
        urlencode({
            'mode': 'updinfo',
            'pass': stream_settings.password,
            'mount': stream_settings.mount_point,
            'song': song
        }),
        request_format({
            'Authorization': 'Basic ' + b64encode("source:" + stream_settings.password),
            'User-Agent': stream_settings.user_agent
        }, "\r\n")
    ))
    s.shutdown(1)
    s.close()

def send(buf):
    global s, packets_sent, start_time
    recon_success = 0
    try:
        s.send(buf)
        send_success = 1
    except:
        s.close()
        while recon_success == 0:
            try:
                s.open()
                recon_success = 1
            except:
                recon_success = 0
                # nada

    s.sync()

def close():
#    s.shutdown(1)
    s.close()
