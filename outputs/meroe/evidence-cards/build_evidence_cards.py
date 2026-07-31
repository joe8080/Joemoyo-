#!/usr/bin/env python3
"""Generate OGX 'DECLASSIFIED'-style evidence receipt cards for Meroë (1920x1080 PNG)."""
import base64, os
from playwright.sync_api import sync_playwright

BASE="/tmp/claude-0/-home-user-Joemoyo-/210a1ab8-a6fd-5b12-8f74-165fd863cf6f/scratchpad"
def b64(p):
    with open(p,"rb") as f: return "data:image/jpeg;base64,"+base64.b64encode(f.read()).decode()

CARDS=[
 {"file":"card1_head","kicker":"ARCHAEOLOGICAL EVIDENCE","head":"THE MEROË HEAD","sub":"THE BRONZE HEAD OF AUGUSTUS — BURIED AT MEROË",
  "doc":"Taken from a Roman statue at Aswan, carried 800 miles south, and buried beneath a temple threshold at Meroë — so that Rome's emperor would be trodden underfoot.",
  "stamp":"ON DISPLAY","img":b64(f"{BASE}/card_img_8.jpg"),
  "meta":[("FIND","Meroë · Temple M292"),("EXCAVATED","John Garstang, 1910"),("HELD","British Museum · BM 1911,0901.1"),("VERDICT","AUTHENTIC ARTEFACT")]},
 {"file":"card2_kandake","kicker":"THE RULING RECORD","head":"THE KANDAKES","sub":"AFRICA'S RULING WARRIOR QUEENS",
  "doc":"Meroë was ruled, again and again, by women — kandakes who commanded armies and were carved on temple walls at the same height as the king.",
  "stamp":"VERIFIED","img":b64(f"{BASE}/card_img_44.jpg"),
  "meta":[("FIGURES","Amanirenas · Amanishakheto · Amanitore"),("RECORD","Naqa & Musawwarat reliefs"),("SOURCE","OGX Archive — verified"),("VERDICT","DOCUMENTED")]},
 {"file":"card3_strabo","kicker":"PRIMARY SOURCE","head":"THE ROMAN RECORD","sub":"STRABO — GEOGRAPHICA, 1ST CENTURY CE",
  "doc":"'The queen of the Ethiopians, a masculine sort of woman…' — she led her army into Roman Egypt, sacking Aswan, Philae and Elephantine.",
  "stamp":"ON THE RECORD","img":b64(f"{BASE}/card_img_118.jpg"),
  "meta":[("AUTHOR","Strabo (c.64 BCE – 24 CE)"),("REFERENCE","Geographica 17.1.53–54"),("EVENT","Kushite–Roman War, 25 BCE"),("VERDICT","EYEWITNESS-ERA ACCOUNT")]},
 {"file":"card4_treaty","kicker":"THE SETTLEMENT","head":"THE TREATY OF SAMOS","sub":"ROME WITHDRAWS — AND WAIVES THE TRIBUTE",
  "doc":"In 21 BCE Rome pulled its frontier back south, exempted Meroë from tribute, and made peace on the queen's terms. The peace held for 300 years.",
  "stamp":"SETTLED","img":b64(f"{BASE}/card_img_135.jpg"),
  "meta":[("SOURCES","Cassius Dio 54.5 · Strabo 17.1.54"),("DATE","21 BCE"),("TERMS","Frontier withdrawn · no tribute"),("VERDICT","HISTORICAL FACT")]},
 {"file":"card5_ezana","kicker":"INSCRIBED IN STONE","head":"THE EZANA STONE","sub":"THE LAST CHAPTER OF MEROË — c. 350 CE",
  "doc":"The Aksumite king Ezana records his campaign against the Noba and the taking of Kush — the end of six centuries of the Meroitic kingdom.",
  "stamp":"THE FALL","img":b64(f"{BASE}/card_img_20.jpg"),
  "meta":[("MONUMENT","Ezana Stone · Aksum"),("SCRIPT","Ge'ez · Sabaean · Greek"),("DATE","c. 350 CE"),("VERDICT","CONTEMPORARY INSCRIPTION")]},
]

HTML="""<!doctype html><html><head><meta charset=utf-8><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden}
body{background:#0c0b09;font-family:'Arial Narrow',Arial,sans-serif;color:#eee;position:relative}
.bg{position:absolute;inset:0;background:
  radial-gradient(120% 90% at 30% 20%,#211d16 0%,#0c0b09 60%,#060504 100%);}
.grain{position:absolute;inset:0;opacity:.06;background-image:repeating-linear-gradient(0deg,#fff 0 1px,transparent 1px 3px);mix-blend-mode:overlay}
.frame{position:absolute;inset:26px;border:3px solid #c9a84c;box-shadow:0 0 0 1px #6b571f inset,0 0 40px #000 inset}
.frame:before{content:"";position:absolute;inset:7px;border:1px solid #6b571f}
.pad{position:absolute;inset:70px 70px 66px 70px;display:flex;flex-direction:column}
.kicker{color:#c9a84c;font-weight:700;letter-spacing:5px;font-size:26px;margin-bottom:4px;font-family:Arial}
.head{font-family:'Arial Black',Arial;font-weight:900;color:#d8b64f;font-size:104px;line-height:.94;letter-spacing:2px;text-shadow:0 3px 0 #000}
.sub{color:#efe9dc;font-weight:700;letter-spacing:3px;font-size:30px;margin-top:14px;border-top:2px solid #6b571f;padding-top:14px;width:1180px;font-family:Arial}
.row{display:flex;gap:44px;margin-top:34px;flex:1}
.doc{width:1050px;background:linear-gradient(#efe7d2,#e5dcc2);color:#2a2117;border-radius:3px;padding:40px 44px;position:relative;
  box-shadow:0 18px 40px rgba(0,0,0,.6);transform:rotate(-.5deg)}
.doc .ts{font-family:'Courier New',monospace;font-size:22px;letter-spacing:1px;color:#3a2f20;display:flex;justify-content:space-between;border-bottom:1px solid #b7a985;padding-bottom:10px}
.doc .quote{font-family:'Courier New',monospace;font-size:41px;line-height:1.32;margin-top:26px;color:#241c12}
.stamp{position:absolute;right:34px;bottom:26px;color:#a5271d;border:6px solid #a5271d;border-radius:8px;
  font-family:'Arial Black',Arial;font-weight:900;font-size:46px;letter-spacing:3px;padding:6px 20px;transform:rotate(-9deg);opacity:.88}
.side{flex:1;display:flex;flex-direction:column;gap:22px}
.photo{width:100%;height:300px;border:2px solid #6b571f;object-fit:cover;object-position:center;filter:sepia(.5) contrast(1.05) brightness(.9)}
.meta{display:flex;flex-direction:column;gap:16px;margin-top:4px}
.mrow{border-bottom:1px solid #3a3122;padding-bottom:12px}
.ml{color:#c9a84c;font-weight:700;letter-spacing:3px;font-size:19px;font-family:Arial}
.mv{color:#f3efe6;font-weight:700;font-size:26px;margin-top:3px;font-family:Arial}
.foot{position:absolute;left:70px;bottom:30px;color:#8a7a4e;letter-spacing:4px;font-size:20px;font-family:Arial;font-weight:700}
</style></head><body>
<div class=bg></div><div class=grain></div><div class=frame></div>
<div class=pad>
 <div class=kicker>%KICKER%</div>
 <div class=head>%HEAD%</div>
 <div class=sub>%SUB%</div>
 <div class=row>
  <div class=doc>
    <div class=ts><span>OGX EVIDENCE FILE</span><span>ORIGINEX HUMAN ARCHIVES</span></div>
    <div class=quote>%DOC%</div>
    <div class=stamp>%STAMP%</div>
  </div>
  <div class=side>
    <img class=photo src="%IMG%">
    <div class=meta>%META%</div>
  </div>
 </div>
</div>
<div class=foot>OGX · THE RECEIPTS — VERIFIED AGAINST PRIMARY SOURCES</div>
</body></html>"""

def build(c):
    meta="".join(f'<div class=mrow><div class=ml>{k}</div><div class=mv>{v}</div></div>' for k,v in c["meta"])
    h=(HTML.replace("%KICKER%",c["kicker"]).replace("%HEAD%",c["head"]).replace("%SUB%",c["sub"])
       .replace("%DOC%",c["doc"]).replace("%STAMP%",c["stamp"]).replace("%IMG%",c["img"]).replace("%META%",meta))
    return h

with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",args=["--no-sandbox"])
    pg=b.new_page(viewport={"width":1920,"height":1080},device_scale_factor=1)
    for c in CARDS:
        hp=f"{BASE}/{c['file']}.html"; open(hp,"w").write(build(c))
        pg.goto("file://"+hp); pg.wait_for_timeout(150)
        out=f"{BASE}/{c['file']}.png"; pg.screenshot(path=out,clip={"x":0,"y":0,"width":1920,"height":1080})
        print("wrote",out,os.path.getsize(out)//1024,"KB")
    b.close()
