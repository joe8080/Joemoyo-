from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np
from render import font, GOLD, CREAM, cover
W,H=1280,720
def grade(im):
    im=ImageEnhance.Contrast(im).enhance(1.15); return ImageEnhance.Color(im).enhance(0.95)
def vignette(im,strength=0.75):
    y,x=np.ogrid[:H,:W]; r=np.sqrt(((x-W/2)/(W/2))**2+((y-H/2)/(H/2))**2)
    m=np.clip(1-strength*np.clip(r-0.35,0,1),0,1)[...,None]
    return Image.fromarray((np.asarray(im).astype(np.float32)*m).astype(np.uint8))
def shadow_text(base,xy,txt,f,fill,anchor="la",blur=8,off=4):
    sh=Image.new("RGBA",base.size,(0,0,0,0)); d=ImageDraw.Draw(sh)
    d.text((xy[0]+off,xy[1]+off),txt,font=f,fill=(0,0,0,230),anchor=anchor)
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(base).text(xy,txt,font=f,fill=fill,anchor=anchor)
def tag(base,txt):
    d=ImageDraw.Draw(base); f=font("Lora.ttf",20); tw=d.textlength(txt,font=f)
    d.rounded_rectangle((W-tw-44,H-48,W-16,H-16),6,fill=(10,14,14,200)); d.text((W-30,H-32),txt,font=f,fill=CREAM+(230,),anchor="rm")
# A: the hidden army rises (Z16)
im=vignette(grade(cover(Image.open("ai/Z16.png").convert("RGB"),W,H))).convert("RGBA")
shadow_text(im,(56,60),"THE ARMY",font("Cinzel.ttf",118,900),CREAM)
shadow_text(im,(56,184),"NOBODY SAW",font("Cinzel.ttf",118,900),GOLD)
shadow_text(im,(60,318),"ISANDLWANA · 1879",font("Cinzel.ttf",44,700),CREAM)
tag(im,"AI reconstruction"); im.convert("RGB").save("deliver/OGX_Isandlwana_thumb_A_army_nobody_saw.jpg",quality=92)
# B: horns of the buffalo map
im=grade(cover(Image.open("preview/map_horns_open_7.jpg").convert("RGB"),W,H)).convert("RGBA")
ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); d.rectangle((0,0,W,250),fill=(6,9,9,170)); im.alpha_composite(ov)
shadow_text(im,(W//2,40),"THE HORNS OF THE BUFFALO",font("Cinzel.ttf",72,900),GOLD,anchor="ma")
shadow_text(im,(W//2,140),"How the Zulu army won Isandlwana",font("Lora-Italic.ttf",52),CREAM,anchor="ma")
tag(im,"Satellite image 2025 · movements schematic"); im.convert("RGB").save("deliver/OGX_Isandlwana_thumb_B_horns_map.jpg",quality=92)
