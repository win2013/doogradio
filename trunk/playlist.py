"""playlist.py -- generic playlist class

settings are in playlist_settings.py
"""
from random import shuffle
import playlist_settings
import os

class Playlist:
    def __init__(self):
        self.playlist = []
        self.position = 0
        self.load_from_file()

    # load the playlist from an m3u file
    def load_from_file(self, filename=playlist_settings.filename):
        playlist_file = open(filename)
        self.playlist = [line.rstrip("\r\n") for line in playlist_file]
        playlist_file.close()
        self.reshuffle()
    
    # save to m3u file (note: they'll be in a random order unless you call it from rescan())
    def save_to_file(self, filename=playlist_settings.filename):
        playlist_file = open(filename, "wb")
        playlist_file.writelines(path + "\r\n" for path in self.playlist)
        playlist_file.close()
    
    # scan all the song directories for files and repopulate the playlist
    def rescan(self, dirs=playlist_settings.scan_directories, extensions=playlist_settings.scan_extensions, save_to=playlist_settings.filename):
        self.playlist = []
        extensions = dict([(ext, 1) for ext in extensions])
        for dir in dirs:
            for (dirpath, dirnames, filenames) in os.walk(dir):
                for filename in filenames:
                    (name, ext) = os.path.splitext(filename)
                    if ext.lower() in extensions:
                        full_path = os.path.join(dirpath, filename)
                        self.playlist.append(full_path)
        self.save_to_file(save_to)
        self.reshuffle()
        
    # try to jump to the song, and return whether it was actually found in the playlist
    def jump(self, path):
        try:
            self.position = self.playlist.index(path)
            return True
        except ValueError:
            return False
            
    def enqueue_after_current(self, path):
        try:
            self.playlist.remove(path)
            self.playlist.insert(self.position + 1, path)
            return True
        except ValueError:
            return False

    def reshuffle(self):
        self.position = 0
        shuffle(self.playlist)

    def next(self):
        self.position += 1
        if(self.position == len(self.playlist)):
            self.reshuffle()
    
    def current(self):
        return self.playlist[self.position]