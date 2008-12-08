import os, time
from subprocess import Popen, PIPE
from random import choice, shuffle

import icecast
import radiocontrol
import playlist
import radio_settings

# returns "title" or "artist - title"
def get_metadata(song):
    # strip directory stuff
    song = os.path.basename(song)
    # strip extension
    song = os.path.splitext(song)[0]
    song = song.replace("_"," ")
    # try to split on " - ", and then try on "-"
    parts = song.split(" - ")
    if len(parts) == 1:
        parts = parts[0].split("-")
    if len(parts) == 1:
        return parts[0]
    title = parts[-1]
    for part in parts[:-1]:
        if not part.isdigit():
            artist = part
            break
    else:
        return title
    return "%s - %s" % (artist, title)

class ShutdownMessage: # shutdown the player
    pass
class NextSongMessage: # go to the next song
    pass
class RestartMessage: # restart the current song
    pass

# check control messages
def handle_messages():
    messages = radiocontrol.get_all_messages()
    for msg in messages:
        if msg[0] == "shutdown":
            raise ShutdownMessage
        elif msg[0] == "next_song":
            raise NextSongMessage
        elif msg[0] == "restart":
            raise RestartMessage       
        elif msg[0] == "jump":
            if playlist.jump(msg[1]):
                raise RestartMessage
        elif msg[0] == "enqueue":
            if playlist.enqueue_after_current(msg[1]):
                raise RestartMessage
        elif msg[0] == "rescan":
            # the rescan is taking place in another thread
            # just start playing the song and then restart when it's done
            icecast.update_metadata(radio_settings.rescan_title)
            play_one_song(radio_settings.rescan_song, update_metadata = False)
            raise RestartMessage

# check control messages, read data from player and send to icecast
def play_loop(player):
    while 1:
        handle_messages()
        packet = player.read(4096)
        # this call blocks to maintain the bitrate
        icecast.send(packet)
        if len(packet) == 0: # no more data from player
            return

# set up the player to play a new song and enter the main play loop
def play_one_song(song, update_metadata=True):
    if update_metadata:
        icecast.update_metadata(get_metadata(song))
    player = Popen([radio_settings.player, song], bufsize=4096, stdout=PIPE).stdout
    print "playing %s..." % song
    try:
        play_loop(player)
    finally: # close the player when any exception is thrown
        player.close()

# play a random ident clip
def play_ident():
    icecast.update_metadata(radio_settings.ident_title)
    ident = os.path.join(radio_settings.ident_directory,
        choice(os.listdir(radio_settings.ident_directory)))
    play_one_song(ident, update_metadata=False)

# return "title" or format "artist - title" according to the given format
def song_format(song, format_string):
    parts = song.split(" - ")
    if len(parts) == 1:
        return parts[0]
    else:
        return format_string % {'artist':parts[0], 'title':parts[1]}

# the announcement contents to pipe to the announcer process
def announcer_contents(ann):
    # ann.write("<prosody rate='-0.1' pitch='low'>\n")
    if len(song_history) > 0:
        ann.write("You just heard %s.\n" % song_format(song_history[-1], "%(title)s by the artist %(artist)s"))
    if len(song_history) > 1:
        ann.write("Before that was %s.\n" % song_format(song_history[-2], "%(artist)s with %(title)s"))
    ann.write("Next up is %s.\n" % song_format(get_metadata(playlist.current()), "%(title)s, by %(artist)s"))
    
# play an announcement with a random announcement BGM
def play_announce():
    # write text file for announcer
    announce_text = open('announce.txt','w')
    announcer_contents(announce_text)
    announce_text.close()
    # make announce.wav using announcer program
    announcer = Popen(radio_settings.announcer, shell=True, stdin=PIPE)
    announcer_contents(announcer.stdin)
    announcer.stdin.close()
    # update title and pick bgm while we're waiting for announcer to finish
    icecast.update_metadata(radio_settings.announce_title)
    announce_bgm = os.path.join(radio_settings.announce_bgm_directory,
        choice(os.listdir(radio_settings.announce_bgm_directory)))
    announcer.wait()
    # play announce.wav mixed with bgm
    player = Popen([radio_settings.player, announce_bgm, "announce.wav"], bufsize=4096, stdout=PIPE).stdout
    print "announcement... %s %s %s" % (radio_settings.player, announce_bgm, "announce.wav")
    try:
        play_loop(player)
    finally:
        player.close()

def do_countdowns():
    global ident_countdown, announce_countdown
    if radio_settings.enable_ident:
        ident_countdown -= 1
    if radio_settings.enable_announce:
        announce_countdown -= 1
    if ident_countdown < 1:
        ident_countdown = radio_settings.ident_interval
    if announce_countdown < 1:
        announce_countdown = radio_settings.announce_interval

def radio_loop():
    global ident_countdown, announce_countdown
    ident_countdown = radio_settings.ident_interval
    announce_countdown = radio_settings.announce_interval
    while 1:
        try:
            if(ident_countdown == 1):
                play_ident()
            if(announce_countdown == 1):
                play_announce()
            play_one_song(playlist.current())
        except ShutdownMessage:
            return
        except NextSongMessage:
            pass
        except RestartMessage:
            continue
        if(len(song_history) > 2):
           song_history.pop(0)
        song_history.append(get_metadata(playlist.current()))
        do_countdowns()
        playlist.next()


def main():
    global playlist, control, song_history
    
    playlist = playlist.Playlist()
    
    control = radiocontrol.RadioControlThread(playlist)
    
    song_history = []

    print "connecting..."
    icecast.connect()

    radio_loop()
    
    print "shutting down..."
    icecast.close()
    
if __name__ == "__main__":
    main()