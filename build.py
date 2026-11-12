"""Turn a recording from the atomizer page into the HyperFrames composition.

Usage:  python build.py rekaman/contoh.json [--label] [--no-label]
Writes index.html next to this file. Then: npx hyperframes render --format mov
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    sys.exit("pakai: python build.py rekaman/<file>.json")
rec = json.loads(pathlib.Path(args[0]).read_text(encoding="utf-8"))
show_labels = "--no-label" not in sys.argv
dur = round(float(rec["dur"]) + 0.5, 2)  # short tail so the last motion settles

tpl = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
parts = (ROOT / "src" / "parts.json").read_text(encoding="utf-8")
tpl = tpl.replace("__PARTS__", parts)

def sub(src, old, new):
    assert old in src, old
    return src.replace(old, new)

# video only: no wall-clock code paths (the replay drives every frame), bigger callout type
tpl = re.sub(r"\} else \{\n  let prev=performance\.now\(\);.*?requestAnimationFrame\(loop\);\n\}", "}", tpl, flags=re.S)
tpl = re.sub(r"const waitUntil = \(cond, g\)=>new Promise\(res=>\{.*?\}\);\n", "const waitUntil = ()=>Promise.resolve(false);\n", tpl, count=1, flags=re.S)
# thicker callouts for video: bold type with a dark halo, wider chips, heavier leader lines
tpl = sub(tpl, """  cc.font='500 19px "IBM Plex Mono", ui-monospace, monospace'; cc.textBaseline='middle'; cc.fillStyle=INK; cc.fillText(title,x,y-13);""",
      """  cc.font='700 25px "IBM Plex Mono", ui-monospace, monospace'; cc.textBaseline='middle';
  cc.lineJoin='round'; cc.lineWidth=6; cc.strokeStyle='rgba(0,0,0,.7)'; cc.strokeText(title,x,y-17);
  cc.fillStyle=INK; cc.fillText(title,x,y-17);""")
tpl = sub(tpl, "cc.font='500 15px", "cc.font='700 19px")
tpl = sub(tpl, "cc.roundRect(x,y+2,w,22,4) : cc.rect(x,y+2,w,22)", "cc.roundRect(x,y+2,w,30,5) : cc.rect(x,y+2,w,30)")
tpl = sub(tpl, "cc.fillText(status,x+8,y+14)", "cc.fillText(status,x+8,y+18)")
tpl = sub(tpl, "'rgba(255,255,255,.7)' : 'rgba(43,93,138,.55)'; cc.lineWidth=1.2;",
      "'rgba(255,255,255,.95)' : 'rgba(43,93,138,.55)'; cc.lineWidth=3.2; cc.shadowColor='rgba(0,0,0,.6)'; cc.shadowBlur=4;")
tpl = sub(tpl, "cc.beginPath(); cc.arc(x0,y0,3,0,6.283); cc.fill(); }", "cc.beginPath(); cc.arc(x0,y0,6,0,6.283); cc.fill(); cc.shadowBlur=0; }")
tpl = sub(tpl, "'rgba(255,255,255,.45)' : 'rgba(43,93,138,.35)'; lc.setLineDash([7,6]); lc.lineWidth=2;",
      "'rgba(255,255,255,.75)' : 'rgba(43,93,138,.35)'; lc.setLineDash([12,9]); lc.lineWidth=4;")
tpl = sub(tpl, "LBLX = 680", "LBLX = 652")
tpl = sub(tpl, "font-size:19px;color:var(--ink)", "font-size:26px;color:var(--ink)")
tpl = re.sub(r"// ---------- local export.*?(?=// ---------- replay)", "", tpl, flags=re.S)
assert "performance.now" not in tpl and "Date.now" not in tpl and "requestAnimationFrame" not in tpl

style = re.search(r"<style>(.*?)</style>", tpl, re.S).group(1)
markup = re.search(r'(<div class="wrap">.*?</div>\s*)<script>', tpl, re.S).group(1)
script = re.search(r"<script>(.*)</script>", tpl, re.S).group(1)

overrides = """
html,body{margin:0;width:1080px;height:1920px;overflow:hidden;background:transparent!important;padding:0!important}
#root{position:absolute;inset:0}
.wrap{max-width:none;width:1080px;height:1920px;margin:0;display:flex;flex-direction:column;justify-content:center;gap:0}
header,.rail,.recbox,.explain,p.note{display:none!important}
.plate{background:transparent!important;border:0!important;border-radius:0}
.lbl{color:#fff!important;font-size:26px!important;font-weight:700;gap:14px!important;text-shadow:0 0 3px rgba(0,0,0,.9),0 0 8px rgba(0,0,0,.6),0 2px 3px rgba(0,0,0,.7)}
.lbl i{background:#fff!important;height:4px!important;opacity:1!important;border-radius:2px;box-shadow:0 0 4px rgba(0,0,0,.7)}
.lbl b{opacity:.85!important;font-weight:700!important}
:root{--display:"Inter",sans-serif;--body:"Inter",sans-serif;--mono:"IBM Plex Mono",monospace}
""" + ("" if show_labels else "#cut,.lbl{display:none!important}\n")

html = f"""<!doctype html>
<html lang="id" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>{style}{overrides}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{dur}" data-width="1080" data-height="1920">
      {markup}
    </div>
    <script>window.__HF_REPLAY = true; window.__HF_REC = {json.dumps(rec)};</script>
    <script>{script}
// ---- HyperFrames clock ----
const __ready = Promise.all(imgs.map(i => i.decode ? i.decode().catch(() => {{}}) : 0));
window.__hf = window.__hf || {{}}; window.__hf.buildReady = window.__hf.buildReady || {{}};
window.__hf.buildReady.atomizer = __ready;
window.addEventListener("hf-seek", (e) => {{
  const t = e.detail.time;
  if (e.detail.waitUntil) e.detail.waitUntil(__ready.then(() => window.__atomizerSeek(t)));
  else window.__atomizerSeek(t);
}});
__ready.then(() => window.__atomizerSeek(0));
const tl = gsap.timeline({{ paused: true }});
tl.to({{}}, {{ duration: {dur} }});
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
</script>
  </body>
</html>
"""
(ROOT / "index.html").write_text(html, encoding="utf-8")
print(f"index.html siap: {dur} s, {len(rec['ev'])} aksi, label={'ya' if show_labels else 'tidak'}")
