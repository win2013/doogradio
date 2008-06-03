#include <stdlib.h>  //added newly
#include <string.h> //also added
#include <unistd.h> //also

#include <stdio.h>
#include <sys/io.h>
#include "lame/lame.h"
#include "./bassmod.h"
#ifdef __MINGW32__
/* Required header file */
#include <fcntl.h>
#endif



FILE *announce_file = 0;
short *announce_data = 0;
int announce_len = 0;
double announce_pos = 0;
int input_samplerate = 44100;

// here is the worst .wav reading code ever
// oh by the way i hope your wav file is 16bit 44khz mono!
void load_announce_file() {
	int c;
	int want = 'd';
	int len = 0;
	while((c = fgetc(announce_file)) != EOF) {
		long int pos = ftell(announce_file);
		if(c == 'd' && fgetc(announce_file) == 'a' && fgetc(announce_file) == 't' && fgetc(announce_file) == 'a') {
			len =  fgetc(announce_file) |
				(fgetc(announce_file) << 8) |
				(fgetc(announce_file) << 16) |
				(fgetc(announce_file) << 24);
			break;
		}
		else {
			fseek(announce_file, pos, SEEK_SET);
		}
	}
	if(len > 90*1024*1024) { // don't allocate huge buffer in case it's broken
		announce_data = 0;
		announce_file = 0;
		announce_len = 0;	
		return;
	}
	announce_len = len;
	announce_data = malloc(announce_len);
	if(fread(announce_data, 1, len, announce_file) != len) {
		announce_data = 0;
		announce_file = 0;
		announce_len = 0;
	}
}
													
int load(char *filename) {
	lame_global_flags *gfp;
	char mp3buffer[8192];
	FILE *mp3file = 0;
	mp3data_struct mp3data = {0};	
	if(!BASSMOD_Init(-3, 44100, 0)) return 1;
	if(!BASSMOD_MusicLoad(0, filename, 0, 0, BASS_MUSIC_RAMPS | BASS_MUSIC_NONINTER | BASS_MUSIC_STOPBACK)) {
		char filebuf[100];
		short leftbuf[1152]; short rightbuf[1152];
		lame_decode_init();
		mp3file = fopen(filename, "rb");
		if(!mp3file) return 1;
		while(!mp3data.header_parsed) {
			if(fread(filebuf, 1, sizeof(filebuf), mp3file) < 100)
				return 1;
			if(lame_decode1_headers(filebuf, 100, leftbuf, rightbuf, &mp3data) < 0)
				return 1;
		}
		lame_decode_exit();
		lame_decode_init();
		fseek(mp3file, 0, SEEK_SET);
		
	}
	if(isatty(fileno(stdout))) return 1;
#ifdef __MINGW32__
	/* Switch to binary mode */
	_setmode(_fileno(stdout),_O_BINARY);
#endif	
	BASSMOD_MusicPlay();
	gfp = lame_init();
	lame_set_num_channels(gfp,2);
	if(mp3file) {
		lame_set_in_samplerate(gfp,mp3data.samplerate);
		input_samplerate = 44100;
	}
	else
		lame_set_in_samplerate(gfp,44100);
	lame_set_out_samplerate(gfp,44100);
	lame_set_brate(gfp,96);
	lame_set_mode(gfp,1);
	lame_set_bWriteVbrTag(gfp,0);
	if(lame_init_params(gfp) < 0)
		return 1;
	if(mp3file) {
		char filebuf[50];
		short leftbuf[1152], rightbuf[1152];
		while(1) {
			int nout;
			int len = fread(filebuf, 1, sizeof(filebuf), mp3file);
			if(len == 0) { // no more data in file
				if(lame_decode(filebuf, len, leftbuf, rightbuf) <= 0) {
					// but only exit after lame_decode stops returning data
					if(announce_file && (int)(announce_pos*2) < announce_len) {
						// song is over, but announcement isn't, so pretend we got 1152 samples of silence
						nout = 1152;
						memset(leftbuf, 0, nout);
						memset(rightbuf, 0, nout);
						//fprintf(stderr, "file ended, generating 1152 more samples");
					}
					else {
						//fprintf(stderr, "nout < 0");
						lame_decode_exit();
						break;
					}
				}
			}
			else {
				nout = lame_decode(filebuf, len, leftbuf, rightbuf);
				if(nout < 0) {
					if(announce_file && (int)(announce_pos*2) < announce_len) {
						// song is over, but announcement isn't, so pretend we got 1152 samples of silence
						nout = 1152;
						memset(leftbuf, 0, nout);
						memset(rightbuf, 0, nout);
					}
					else {
						//fprintf(stderr, "nout < 0");
						lame_decode_exit();
						break;
					}
				}
				if(nout == 0) continue;
			}
			
			// overdub
			if(announce_file) {
				int i;
				for(i=0;i<nout;i++) {
					leftbuf[i] /= 3;
					rightbuf[i] /= 3;
					if((int)(announce_pos*2) < announce_len) {
						leftbuf[i] += announce_data[(int)announce_pos];
						rightbuf[i] += announce_data[(int)announce_pos];
						announce_pos+=16000.0/input_samplerate;
					}
				}
			}
			
			if(mp3data.stereo == 2)
				nout = lame_encode_buffer(gfp, leftbuf, rightbuf, nout, mp3buffer, 4096);
			else
				nout = lame_encode_buffer(gfp, leftbuf, leftbuf, nout, mp3buffer, 4096);
			if(nout != fwrite(mp3buffer, 1, nout, stdout))
				goto DONE;
		}
	}
	else while(BASSMOD_MusicIsActive() == BASS_ACTIVE_PLAYING) {
		int c; int i; short bassbuffer[300*2];
		short leftbuffer[300], rightbuffer[300];
		// bass is interlaced, lame isn't
		BASSMOD_MusicDecode(bassbuffer, 300*2*2);
		for(i=0;i<600;i++) {
			if(i & 1)
				rightbuffer[i >> 1] = bassbuffer[i];
			else
				leftbuffer[i >> 1] = bassbuffer[i];
		}
		c = lame_encode_buffer(gfp, leftbuffer, rightbuffer, 300, mp3buffer, 4096);
		if(c != fwrite(mp3buffer, 1, c, stdout))
			goto DONE;
	}
	{ int c;
	c = lame_encode_flush(gfp, mp3buffer, 8192);
	fwrite(mp3buffer, 1, c, stdout);
	}
	DONE:
	if(mp3file) fclose(mp3file);
	lame_close(gfp);
}

int usage() {
	printf("usage: %s filename [announce]");
	return 1;
}

int main(int argc, char *argv[]) {
	if(argc == 1)
		return usage();
	if(argc == 2)
		return load(argv[1]);
	if(argc == 3) {
		announce_file = fopen(argv[2], "rb");
		if(!announce_file) return 1;
		load_announce_file();
		return load(argv[1]);
	}
	return usage();
}

