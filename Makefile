doog-player: player.c bassmod.h libbassmod.so
	gcc -D__USELARGEFILE64 -D_FILE_OFFSET_BITS=64 -o doog-player player.c libbassmod.so -lmp3lame -lavcodec -lavformat -lavutil
