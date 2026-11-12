"""Local atomizer page with a one-click video export.

Run "Buka Atomizer.bat" (or: python server.py). Opens http://localhost:8770 in the browser.
Only listens on this computer (127.0.0.1).
"""
import json, subprocess, sys, threading, webbrowser, datetime, pathlib, os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT = pathlib.Path(__file__).resolve().parent
PORT = 8770
render_lock = threading.Lock()
# what the page polls while an export runs
PROGRESS = {"busy": False, "pct": 0, "stage": ""}
STAGES = {"compile": "Menyiapkan", "extract": "Menyiapkan", "setup": "Menyiapkan", "capture": "Merekam frame",
          "encode": "Menyandikan video", "assemble": "Menyatukan video"}


def page():
    tpl = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    parts = (ROOT / "src" / "parts.json").read_text(encoding="utf-8")
    head = ('<!doctype html>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<script>window.__LOCAL_EXPORT = true;</script>\n')
    return (head + tpl.replace("__PARTS__", parts)).encode("utf-8")


def export(rec, label):
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"atomizer-{stamp}"
    (ROOT / "rekaman").mkdir(exist_ok=True)
    (ROOT / "renders").mkdir(exist_ok=True)
    rec_path = ROOT / "rekaman" / f"{name}.json"
    rec_path.write_text(json.dumps(rec), encoding="utf-8")
    out = ROOT / "renders" / f"{name}.mov"
    with render_lock:
        PROGRESS.update(busy=True, pct=0, stage="Menyiapkan")
        try:
            return _export_locked(rec_path, out, label)
        finally:
            PROGRESS.update(busy=False)


def _export_locked(rec_path, out, label):
    build = [sys.executable, str(ROOT / "build.py"), str(rec_path)] + ([] if label else ["--no-label"])
    b = subprocess.run(build, cwd=ROOT, capture_output=True, text=True)
    if b.returncode:
        return {"ok": False, "error": (b.stderr or b.stdout)[-400:]}
    print(f"  Merender {out.name} ...", flush=True)
    p = subprocess.Popen(f'npx hyperframes render --format mov --output "renders/{out.name}"',
                         cwd=ROOT, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace")
    tail = []
    for line in p.stdout:
        tail = (tail + [line])[-30:]
        if line.startswith("@hf-progress"):
            try:
                j = json.loads(line.split(" ", 1)[1])
                PROGRESS.update(pct=max(PROGRESS["pct"], int(j.get("pct", 0))),
                                stage=STAGES.get(j.get("code", ""), "Merender"))
            except ValueError:
                pass
    p.wait()
    if p.returncode or not out.exists():
        return {"ok": False, "error": "".join(tail)[-400:]}
    PROGRESS.update(pct=100, stage="Selesai")
    print(f"  Selesai: {out}", flush=True)
    if os.name == "nt":
        subprocess.Popen(["explorer", "/select,", str(out)])
    return {"ok": True, "file": f"renders/{out.name}"}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, page(), "text/html; charset=utf-8")
        elif self.path == "/progress":
            self._send(200, json.dumps(PROGRESS).encode("utf-8"), "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/export":
            return self._send(404, b"not found", "text/plain")
        try:
            data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            result = export(data["rec"], bool(data.get("label", True)))
        except Exception as e:  # report the failure to the page instead of dropping the request
            result = {"ok": False, "error": str(e)}
        self._send(200, json.dumps(result).encode("utf-8"), "application/json")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}"
    print(f"Atomizer jalan di {url}\nBiarkan jendela ini terbuka selama dipakai. Tutup jendela ini untuk berhenti.\n", flush=True)
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    srv.serve_forever()
