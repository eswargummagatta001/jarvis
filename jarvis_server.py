"""
jarvis_server.py - Integrated Jarvis Server
Runs the holographic UI on http://localhost:8080 AND listens for voice commands
in a background thread. Everything is in one process so the UI reflects
live voice activity in real time.
"""

import os, sys, json, time, datetime, threading, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

# ── Path setup ────────────────────────────────────────────────────────────────
project_root = os.path.abspath(os.path.dirname(__file__))
package_path = os.path.join(project_root, "Jarvis_Setup_Package")
for p in (project_root, package_path):
    if p not in sys.path:
        sys.path.insert(0, p)

# Auto-load GROQ_API_KEY from ~/.openjarvis/free.key or .env if not set
if not os.environ.get("GROQ_API_KEY"):
    keyfile = os.path.expanduser("~/.openjarvis/free.key")
    if os.path.exists(keyfile):
        os.environ["GROQ_API_KEY"] = open(keyfile).read().strip()
import jarvis_brain  # noqa: E402

# ── Shared live state (updated by voice thread, read by HTTP thread) ──────────
_lock     = threading.Lock()
_chat_idx = 0
STATE = {
    "state":       "idle",
    "note":        "Ready",
    "mode":        "hybrid",
    "model":       "Groq / GPT-OSS-120B",
    "last_you":    "",
    "last_tool":   "",
    "tools":       0,
    "facts":       0,
    "mail_age":    None,
    "t_rec":       0.0,
    "t_think":     0.0,
    "tool_active": False,
    "chat":        [],
    "cards":       [],
    "stocks":      [],
    "sys":         {},
    "mic":         {"n": 0, "a": []},
}

def _ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

def _add_chat(kind, text):
    global _chat_idx
    with _lock:
        _chat_idx += 1
        STATE["chat"].append({"i": _chat_idx, "k": kind, "x": text, "t": _ts()})
        if len(STATE["chat"]) > 80:
            STATE["chat"] = STATE["chat"][-80:]

def _set(key, val):
    with _lock:
        STATE[key] = val

def _sys_vitals():
    out = {}
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        out["disk"] = round(used / total * 100, 1)
        out["free"] = round(free / (1024**3), 1)
    except Exception:
        pass
    return out

# ── Speak helper ──────────────────────────────────────────────────────────────
def _speak(text):
    """Speak aloud on macOS and also push to chat."""
    if not text:
        return
    _add_chat("jarvis", text)
    print(f"\n[JARVIS]: {text}\n")
    if sys.platform == "darwin":
        subprocess.Popen(["say", "-v", "Samantha", text])

# ── Process a command (shared by voice + HTTP) ────────────────────────────────
def _process(query: str):
    q = query.strip()
    if not q:
        return

    _add_chat("you", query)
    _set("last_you", query)
    _set("state", "thinking")

    t0 = time.time()
    reply = jarvis_brain.think(q)
    dt = round(time.time() - t0, 2)

    with _lock:
        STATE["state"]   = "speaking"
        STATE["t_think"] = dt
        STATE["tools"]  += 1

    _speak(reply)
    time.sleep(0.4)
    _set("state", "listening")

# ── Voice listener thread ─────────────────────────────────────────────────────
def _voice_loop():
    try:
        import speech_recognition as sr
    except ImportError:
        _add_chat("sys", "speech_recognition not installed – voice disabled. Use /command endpoint.")
        return

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8

    try:
        mic = sr.Microphone()
    except Exception as e:
        _add_chat("sys", f"Microphone unavailable: {e}. Use /command endpoint.")
        return

    with mic as source:
        _add_chat("sys", "Microphone ready – calibrating ambient noise…")
        _set("state", "starting")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)

    _add_chat("sys", "Jarvis is listening. Speak your command.")
    _set("state", "listening")

    while True:
        try:
            with mic as source:
                _set("state", "listening")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=8)

            _set("state", "recognizing")
            query = recognizer.recognize_google(audio).strip()
            print(f"[Heard]: {query}")
            _process(query)

        except sr.WaitTimeoutError:
            _set("state", "listening")
        except sr.UnknownValueError:
            _set("state", "listening")
        except KeyboardInterrupt:
            break
        except Exception as e:
            _add_chat("sys", f"Notice: {e}")
            time.sleep(0.5)

# ── HTTP server ───────────────────────────────────────────────────────────────
HTML_PATH = os.path.join(package_path, "jarvis_workplace.html")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def _send(self, body, ct="application/json", status=200):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        if path in ("/", "/index.html"):
            try:
                with open(HTML_PATH, "rb") as f:
                    self._send(f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(b"<h1>jarvis_workplace.html not found</h1>", "text/html", 404)
            return

        if path == "/api/state":
            with _lock:
                snap      = dict(STATE)
                snap["sys"] = _sys_vitals()
            self._send(snap)
            return

        if path == "/command":
            qs   = parse_qs(parsed.query)
            text = qs.get("text", [""])[0].strip()
            if not text:
                self._send({"error": "Missing 'text' parameter"}, status=400)
                return
            threading.Thread(target=_process, args=(text,), daemon=True).start()
            self._send({"status": "ok", "message": "Processing…"})
            return

        self._send({"error": "Not found"}, status=404)

    def do_POST(self):
        if self.path == "/command":
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(length))
                text = data.get("text", "").strip()
            except Exception:
                self._send({"error": "Invalid JSON"}, status=400)
                return
            if not text:
                self._send({"error": "Missing 'text' field"}, status=400)
                return
            threading.Thread(target=_process, args=(text,), daemon=True).start()
            self._send({"status": "ok", "message": "Processing…"})
        else:
            self._send({"error": "Not found"}, status=404)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    _add_chat("sys", "Jarvis server starting…")

    # Start voice listener in background
    vt = threading.Thread(target=_voice_loop, daemon=True)
    vt.start()

    print("=" * 52)
    print("  JARVIS WORKPLACE  →  http://localhost:8080")
    print("  Speak to the microphone OR visit the URL.")
    print("=" * 52)

    server = HTTPServer(("0.0.0.0", 8080), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Jarvis. Goodbye!")
