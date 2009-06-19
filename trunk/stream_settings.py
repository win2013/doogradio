host = "localhost"
port = 8000
mount_point = '/halcycast.mp3'
password = 'muh'
name = 'halcycast'
url = 'http://doogtopia.iiichan.net'
genre = 'Awesome'
samplerate = 44100
bitrate = 96
channels = 2
description = 'The Best Music you Never Heard'
user_agent = 'icecast-python'

# make sure the server has at least this many extra packets of data
# where a packet is 4096 bytes = approx. 340ms at 96kbps
# higher numbers increase source-to-listener latency, but guard
# against the server killing your connection during traffic congestion
# default:  6
buffer_packets = 18
# total latency is even higher, because the server keeps a buffer as well
