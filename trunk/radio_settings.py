# path to the audio generator
player = "./doog-player"

# enable playing "idents" (station identification clips)
enable_ident = True
# how many songs before we play an ident
ident_interval = 4
# song title to use during idents
ident_title = "-= Doogtopia Radio =-"
ident_directory = "jingles"

# enable song announcements
enable_announce = False
# how many songs before we do announcements
announce_interval = 3
# song title to use during announcements
announce_title = "-= Announcements =-"
announce_bgm_directory = "announce_bgm"
announcer = '"C:\\program files\\cepstral\\bin\\swift\" -n Emily -p audio/deadair=500 -f announce.txt -o announce.wav'

rescan_title = "-= Regenerating Playlist... =-"
rescan_song = "./Regen.mp3"

# Admin panel socket settings
control_host = "localhost"
control_port = 8900
