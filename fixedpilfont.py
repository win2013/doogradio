# write a PIL file for a fixed-width text image

import getopt, sys

def puti16(fp, values):
    # write network order (big-endian) 16-bit sequence
    for v in values:
        if v < 0:
            v = v + 65536
        fp.write(chr(v>>8&255) + chr(v&255))
        
def usage():
    sys.stderr.write("usage: %s -w 16 -h 16 -nc font.txt\n" % sys.argv[0])
    sys.stderr.write("where largefont.txt contains the layout of the\n")
    sys.stderr.write("characters in font.png/gif\n\n")
    sys.stderr.write("args:\n")
    sys.stderr.write("-w, --width=: width of a letter\n")    
    sys.stderr.write("-h, --height=: height of a letter\n")
    sys.stderr.write("-nc, --no-case: font only contains one case\n")

def main():
    global width, height
    try:
        opts, args = getopt.getopt(sys.argv[1:], "w:h:", ["width","height"])
        chars = open(args[0])
    except (getopt.GetoptError, IndexError):
        usage()
        sys.exit(2)
    except IOError:
        sys.stderr.write("File not found\n")
        usage()
        sys.exit(2)

    width = 16
    height = 16
    nc = False
    for o, a in opts:
        if o in ("-w", "--width"):
            width = int(a)
        if o in ("-h", "--height"):
            height = int(a)
        if o in ("-nc", "--no-case"):
            nocase = True

    charlines = chars.readlines()
    metrics = [None] * 256
    for y in range(len(charlines)):
        for x in range(len(charlines[y])):
            delta = width, 0
            dst = 0, 0, width, height
            src = x*width, y*height, x*width + width, y*height + height
            if nocase:
                metrics[ ord(charlines[y][x].upper()) ] = delta, dst, src
                metrics[ ord(charlines[y][x].lower()) ] = delta, dst, src
            else:
                metrics[ ord(charlines[y][x]) ] = delta, dst, src
    metrics[ ord(' ') ] = ((width, 0), (0, 0, 0, 0), (0, 0, 0, 0))
    metrics[ ord("\n") ] = None
    fp = open(args[0].replace(".txt", ".pil"), "wb")
    fp.write("PILfont\n")
    fp.write("\n")
    fp.write("DATA\n")
    for id in range(256):
        m = metrics[id]
        if not m:
            puti16(fp, [0] * 10)
        else:
            puti16(fp, m[0] + m[1] + m[2])
    fp.close()
    
if __name__ == "__main__":
    main()


