# add image_text to ImageDraw
import ImageDraw
def image_text(self, xy, text, font=None):
    if font is None:
        font = self.getfont()
    try:
        mask, offset = font.getmask2(text, self.fontmode)
        xy = xy[0] + offset[0], xy[1] + offset[1]
    except AttributeError:
        try:
            mask = font.getmask(text, self.fontmode)
        except TypeError:
            mask = font.getmask(text)
        bbox = mask.getbbox()
    self.im.paste(mask, (xy[0], xy[1], xy[0] + bbox[2], xy[1] + bbox[3]))
    
ImageDraw.ImageDraw.image_text = image_text