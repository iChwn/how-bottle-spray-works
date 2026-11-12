"""Turn a recording from the atomizer page into the HyperFrames composition.

Usage:  python build.py rekaman/contoh.json [--no-label] [--no-sound]
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
with_sound = "--no-sound" not in sys.argv

tpl = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
parts = (ROOT / "src" / "parts.json").read_text(encoding="utf-8")
tpl = tpl.replace("__PARTS__", parts).replace("__SFX__", "{}")  # video gets its sound from <audio> clips


def sfx_events(rec, end):
    """Replay the pump at the page's fixed step and list (time, sound, volume).

    Mirrors update() and sfxDetect() in src/template.html, so the video hits the same moments the page plays."""
    STAG, PART_TIME = 0.09, 1.4
    ASM_TOTAL = 6 * STAG + PART_TIME
    DOWN_TIME, UP_TIME, DT = 0.3, 0.55, 1 / 60
    clamp = lambda v: min(1.0, max(0.0, v))
    ease = lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
    s = rec["start"]
    asm, asm_t, pr, pr_t, primed = s["asm"], s["asmTarget"], s["pr"], s["prTarget"], s["primed"]
    ev, ei, t, d_prev, landed, flip, out = rec["ev"], 0, 0.0, 0, None, 0, []
    while t + DT <= end + 1e-6:
        while ei < len(ev) and ev[ei][0] <= t + 1e-6:
            _, k, v = ev[ei]; ei += 1
            if k == "asm": asm_t = v
            elif k == "pr": pr_t = v
        a_end = 1 if asm_t else 0
        if asm < a_end: asm = min(a_end, asm + DT / ASM_TOTAL)
        elif asm > a_end: asm = max(a_end, asm - DT / ASM_TOTAL)
        if asm_t == 0 and asm <= 0: primed = 0
        prev = pr
        if pr < pr_t: pr = min(pr_t, pr + DT / DOWN_TIME)
        elif pr > pr_t: pr = max(pr_t, pr - DT / UP_TIME)
        d = pr - prev
        if d < 0: primed += -d
        a_min = min(ease(clamp((asm * ASM_TOTAL - abs(i - 6) * STAG) / PART_TIME)) for i in range(10))
        at = t + DT
        direction = 1 if d > 0 else -1 if d < 0 else 0
        if direction == 1 and d_prev != 1:
            out.append((at, "click", 0.9))
            if primed >= 0.95 and a_min > 0.99: out.append((at, "spray", 0.85))
        if direction == -1 and d_prev != -1: out.append((at, "release", 0.8))
        d_prev = direction
        now = [asm * ASM_TOTAL - abs(i - 6) * STAG >= PART_TIME - 1e-9 for i in range(10)]
        if landed is None: landed = now
        if any(n and not l for n, l in zip(now, landed)):
            out.append((at, "snap-2" if flip else "snap-1", 0.75)); flip ^= 1
        if any(l and not n for n, l in zip(now, landed)): out.append((at, "snap-2", 0.4))
        landed = now
        t += DT
    return out

def sub(src, old, new):
    assert old in src, old
    return src.replace(old, new)

# video only: no wall-clock code paths (the replay drives every frame), bigger callout type
tpl = re.sub(r"\} else \{\n  let prev=performance\.now\(\);.*?requestAnimationFrame\(loop\);\n\}", "}", tpl, flags=re.S)
tpl = re.sub(r"const waitUntil = \(cond, g\)=>new Promise\(res=>\{.*?\}\);\n", "const waitUntil = ()=>Promise.resolve(false);\n", tpl, count=1, flags=re.S)
# thicker callouts for video: bold type with a dark halo, wider chips, heavier leader lines
tpl = sub(tpl, """  cc.font='500 26px "IBM Plex Mono", ui-monospace, monospace'; cc.textBaseline='middle'; cc.fillStyle=INK; cc.fillText(title,x,y-17);""",
      """  cc.font='700 30px "IBM Plex Mono", ui-monospace, monospace'; cc.textBaseline='middle';
  cc.lineJoin='round'; cc.lineWidth=7; cc.strokeStyle='rgba(0,0,0,.7)'; cc.strokeText(title,x,y-20);
  cc.fillStyle=INK; cc.fillText(title,x,y-20);""")
tpl = sub(tpl, "cc.font='500 19px", "cc.font='700 22px")
tpl = sub(tpl, "cc.roundRect(x,y+2,w,28,4) : cc.rect(x,y+2,w,28)", "cc.roundRect(x,y+2,w,34,5) : cc.rect(x,y+2,w,34)")
tpl = sub(tpl, "cc.fillText(status,x+8,y+17)", "cc.fillText(status,x+8,y+20)")
tpl = sub(tpl, "'rgba(255,255,255,.7)' : 'rgba(43,93,138,.55)'; cc.lineWidth=2;",
      "'rgba(255,255,255,.95)' : 'rgba(43,93,138,.55)'; cc.lineWidth=4; cc.shadowColor='rgba(0,0,0,.6)'; cc.shadowBlur=4;")
tpl = sub(tpl, "cc.beginPath(); cc.arc(x0,y0,4,0,6.283); cc.fill(); }", "cc.beginPath(); cc.arc(x0,y0,7,0,6.283); cc.fill(); cc.shadowBlur=0; }")
tpl = sub(tpl, "'rgba(255,255,255,.45)' : 'rgba(43,93,138,.35)'; lc.setLineDash([7,6]); lc.lineWidth=2;",
      "'rgba(255,255,255,.75)' : 'rgba(43,93,138,.35)'; lc.setLineDash([12,9]); lc.lineWidth=4;")
tpl = sub(tpl, "LBLX = 680", "LBLX = 652")
tpl = sub(tpl, "font-size:19px;color:var(--ink)", "font-size:26px;color:var(--ink)")
tpl = re.sub(r"// ---------- local export.*?(?=// ---------- replay)", "", tpl, flags=re.S)
tpl = sub(tpl, "transition:width .4s ease", "")  # export-overlay bar is never shown in video
assert "performance.now" not in tpl and "Date.now" not in tpl and "requestAnimationFrame" not in tpl

import wave
def wav_len(name):
    with wave.open(str(ROOT / "assets" / "sfx" / f"{name}.wav")) as w:
        return w.getnframes() / w.getframerate()

audio_tags = ""
if with_sound:
    for n, (at, name, vol) in enumerate(sfx_events(rec, dur)):
        ln = min(wav_len(name), dur - at)
        if ln <= 0.01: continue
        audio_tags += (f'\n      <audio id="sfx-{n}" src="assets/sfx/{name}.wav" data-start="{at:.3f}" '
                       f'data-duration="{ln:.3f}" data-track-index="{2 + n % 4}" data-volume="{vol}"></audio>')

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
      {markup}{audio_tags}
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
print(f"index.html siap: {dur} s, {len(rec['ev'])} aksi, {audio_tags.count('<audio')} suara, label={'ya' if show_labels else 'tidak'}")
