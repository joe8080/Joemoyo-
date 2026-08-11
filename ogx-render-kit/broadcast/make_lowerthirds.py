import base64, os
from playwright.sync_api import sync_playwright
BASE="/tmp/claude-0/-home-user-Joemoyo-/210a1ab8-a6fd-5b12-8f74-165fd863cf6f/scratchpad"
def b64(p): return base64.b64encode(open(p,"rb").read()).decode()
ANTON=b64(f"{BASE}/fonts/Anton.ttf"); OSWALD=b64(f"{BASE}/fonts/Oswald.ttf")
CARDS=[
 {"file":"lt1","kicker":"ARCHAEOLOGICAL EVIDENCE","primary":"THE MEROË HEAD","secondary":"Bronze head of Augustus · British Museum BM 1911,0901.1"},
 {"file":"lt2","kicker":"THE RULING RECORD","primary":"THE KANDAKES","secondary":"Warrior queens of Meroë · Naqa & Musawwarat reliefs"},
 {"file":"lt3","kicker":"PRIMARY SOURCE","primary":"STRABO","secondary":"Geographica 17.1.53–54 · The war of 25 BCE"},
 {"file":"lt4","kicker":"THE SETTLEMENT","primary":"TREATY OF SAMOS","secondary":"21 BCE · Rome withdraws and waives the tribute"},
 {"file":"lt5","kicker":"INSCRIBED IN STONE","primary":"THE EZANA STONE","secondary":"c. 350 CE · Aksum ends the Meroitic kingdom"},
]
CSS = """
@font-face{font-family:'Anton';src:url(data:font/ttf;base64,__ANTON__) format('truetype')}
@font-face{font-family:'Oswald';src:url(data:font/ttf;base64,__OSWALD__) format('truetype')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;background:transparent;overflow:hidden}
.scrim{position:absolute;left:0;bottom:0;width:1150px;height:360px;background:linear-gradient(90deg, rgba(9,8,6,0.92) 0%, rgba(9,8,6,0.78) 42%, rgba(9,8,6,0) 100%)}
.scrim2{position:absolute;left:0;bottom:0;width:1150px;height:360px;background:linear-gradient(0deg, rgba(9,8,6,0.55) 0%, rgba(9,8,6,0) 55%)}
.wrap{position:absolute;left:192px;bottom:120px;width:1050px}
.rule{width:96px;height:5px;background:#C9A84C;margin-bottom:20px}
.kicker{font-family:'Oswald';font-weight:600;color:#C9A84C;font-size:27px;letter-spacing:3.2px;text-transform:uppercase;margin-bottom:10px}
.primary{font-family:'Anton';color:#F6F3EC;font-size:86px;line-height:0.98;text-shadow:0 3px 14px rgba(0,0,0,0.6);letter-spacing:0.5px}
.uline{width:150px;height:4px;background:#E63946;margin:16px 0 14px}
.secondary{font-family:'Oswald';font-weight:400;color:#E9E4D8;font-size:32px;letter-spacing:0.4px}
""".replace("__ANTON__",ANTON).replace("__OSWALD__",OSWALD)
TPL = "<!doctype html><html><head><meta charset=utf-8><style>"+CSS+"</style></head><body>"\
 "<div class=scrim></div><div class=scrim2></div><div class=wrap>"\
 "<div class=rule></div><div class=kicker>__K__</div><div class=primary>__P__</div>"\
 "<div class=uline></div><div class=secondary>__S__</div></div></body></html>"
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1920,"height":1080},device_scale_factor=1)
    for c in CARDS:
        h=TPL.replace("__K__",c["kicker"]).replace("__P__",c["primary"]).replace("__S__",c["secondary"])
        hp=f"{BASE}/{c['file']}.html"; open(hp,"w").write(h)
        pg.goto("file://"+hp); pg.wait_for_timeout(250)
        pg.screenshot(path=f"{BASE}/{c['file']}.png",omit_background=True,clip={"x":0,"y":0,"width":1920,"height":1080})
        print("wrote",c["file"])
    b.close()
