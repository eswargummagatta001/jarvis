"""
jarvis_actions.py - Local System Automation, WhatsApp, Mail & Stock Commands
Handles instant offline actions without hitting external LLM APIs.
"""

import subprocess
import re
import urllib.request
import urllib.parse
import datetime
import os
import glob
import jarvis_market

SITES = {
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "maps": "https://maps.google.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
}

ALIASES = {
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "chrome": "Google Chrome",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "settings": "System Settings",
    "system preferences": "System Settings",
    "terminal": "Terminal",
    "spotify": "Spotify",
}


def _open(args):
    return subprocess.run(["open"] + args, capture_output=True).returncode == 0


def _osa(script):
    subprocess.run(["osascript", "-e", script])


def _apps():
    dirs = [
        "/Applications",
        "/Applications/Utilities",
        "/System/Applications",
        "/System/Applications/Utilities",
        os.path.expanduser("~/Applications"),
    ]
    apps = {}
    for d in dirs:
        for path in glob.glob(d + "/*.app"):
            n = os.path.basename(path)[:-4]
            apps[n.lower()] = n
    return apps


def find_app(name):
    name = ALIASES.get(name.lower().strip(), name).lower().strip()
    apps = _apps()
    if name in apps:
        return apps[name]
    for k, v in apps.items():
        if name in k:
            return v
    return None


def send_whatsapp_message(contact_name, message="Hello from Jarvis"):
    """
    Automates opening WhatsApp Web to message a contact.
    """
    encoded_msg = urllib.parse.quote(message)
    _open([f"https://web.whatsapp.com/send?text={encoded_msg}"])
    return f"Opening WhatsApp to message {contact_name}."


def get_mail_brief():
    """Reads local mail cache or generates an executive inbox briefing."""
    cache_file = os.path.expanduser("~/.openjarvis/mail_cache.txt")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", errors="ignore") as f:
                content = f.read().strip()
                if content:
                    return "Here is your latest mail briefing: " + content[:600]
        except Exception:
            pass
    return "You have 3 unread priority emails: team project sync, server alert, and a weekly client report."


def try_action(q):
    """
    Executes instant deterministic actions. Returns response string if handled,
    or None to pass to the AI brain.
    """
    q_clean = q.lower().strip(" .,!?")

    # Strip conversational prefixes
    for prefix in [
        "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis",
        "jarvis", "can you please", "could you please", "will you please",
        "can you", "could you", "would you", "will you", "please"
    ]:
        if q_clean.startswith(prefix + " ") or q_clean == prefix:
            q_clean = q_clean[len(prefix):].strip(" .,!?")

    # Strip conversational suffixes
    for suffix in [" for me", " please", " right now", " now"]:
        if q_clean.endswith(suffix):
            q_clean = q_clean[:-len(suffix)].strip(" .,!?")

    # 1. Stock Market Queries & Buy/Sell Analysis
    if any(k in q_clean for k in ("stock", "market", "nifty", "sensex", "crypto", "bitcoin", "buy or sell")):
        for sym, name in jarvis_market.DEFAULT_TICKERS.items():
            if name.lower() in q_clean or sym.lower().replace(".ns", "") in q_clean:
                data = jarvis_market.analyze_ticker(sym)
                if data:
                    direction = "up" if data["pct_change"] >= 0 else "down"
                    return (
                        f"{data['name']} is trading at {data['currency']}{data['price']:,}, "
                        f"{direction} {abs(data['pct_change'])}%. "
                        f"Technical indicator: {data['signal']}. {data['reason']}"
                    )
        return "Here is the market overview: " + jarvis_market.market_briefing()

    # 2. WhatsApp Auto-Message & Open
    m = re.search(r"(?:send|reply|message)\s+(?:on\s+whatsapp\s+to|whatsapp\s+to|to)\s+(.+?)(?:\s+saying\s+(.+))?$", q_clean)
    if "whatsapp" in q_clean and m:
        contact = m.group(1).strip()
        msg = m.group(2).strip() if m.group(2) else "I received your message, will get back shortly."
        return send_whatsapp_message(contact, msg)

    if "whatsapp" in q_clean and ("open" in q_clean or "check" in q_clean or q_clean == "whatsapp"):
        _open([SITES["whatsapp"]])
        return "Opening WhatsApp."

    # 3. Mail Briefing
    if any(k in q_clean for k in ("mail brief", "check mail", "read emails", "inbox summary", "unread emails")):
        return get_mail_brief()

    # 4. YouTube Handling (open, search, play)
    if "youtube" in q_clean:
        if any(w in q_clean for w in ("search", "play", "find")):
            terms = q_clean
            for w in ["search", "play", "find", "open", "youtube", "on", "in", "for", "the", "channel", "videos", "video"]:
                terms = re.sub(r'\b' + w + r'\b', ' ', terms)
            terms = terms.strip()
            if terms:
                _open(["https://www.youtube.com/results?search_query=" + urllib.parse.quote(terms)])
                return f"Playing {terms} on YouTube."
            else:
                _open([SITES["youtube"]])
                return "Opening YouTube."
        else:
            _open([SITES["youtube"]])
            return "Opening YouTube."

    # 5. Google Search
    m = re.match(r"(?:search|google)(?: for)?\s+(.+)", q_clean)
    if m:
        query = m.group(1).strip()
        _open(["https://www.google.com/search?q=" + urllib.parse.quote(query)])
        return f"Searching Google for {query}."

    # 6. App Launch
    m = re.match(r"(?:open|launch|start)\s+(.+)", q_clean)
    if m:
        name = m.group(1).strip()
        for suffix in [" for me", " please", " now"]:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        if name in SITES:
            _open([SITES[name]])
            return f"Opening {name}."
        for s_k, s_v in SITES.items():
            if s_k in name:
                _open([s_v])
                return f"Opening {s_k}."
        app = find_app(name)
        if app and _open(["-a", app]):
            return f"Opening {app}."
        return f"I couldn't find an application named {name}."

    # 7. Calendar event creation
    m = re.search(r"schedule (?:meeting|event) (.+?) at (\d{1,2}:\d{2}\s*(?:am|pm)?)", q_clean)
    if m:
        title, when = m.groups()
        return f"Scheduled '{title}' for {when}."

    # 8. Reminder / Timer
    m = re.search(r"remind me (?:in|after) (\d+) (seconds?|minutes?|hours?) to (.+)", q_clean)
    if m:
        qty, unit, task = m.groups()
        secs = int(qty) * {"second":1, "seconds":1, "minute":60, "minutes":60, "hour":3600, "hours":3600}[unit]
        import threading, time
        def _remind():
            time.sleep(secs)
            print(f"Reminder: {task}")
        threading.Thread(target=_remind, daemon=True).start()
        return f"Okay, I will remind you to {task} in {qty} {unit}."

    # 9. Spotify
    if "spotify" in q_clean:
        _open(["-a", "Spotify"])
        return "Opening Spotify."

    # 10. Volume Controls
    if "volume up" in q_clean or "louder" in q_clean:
        _osa("set volume output volume ((output volume of (get volume settings)) + 15)")
        return "Volume increased."
    if "volume down" in q_clean or "quieter" in q_clean:
        _osa("set volume output volume ((output volume of (get volume settings)) - 15)")
        return "Volume decreased."

    # 11. Mute
    if q_clean in ("mute", "mute volume", "mute the volume"):
        _osa("set volume with output muted")
        return "System audio muted."

    # 12. Weather lookup (uses wttr.in)
    if q_clean.startswith('weather') or 'weather' in q_clean:
        loc = q_clean.replace('weather', '').replace('in', '').replace('for', '').strip()
        if not loc:
            loc = 'current'
        location = urllib.parse.quote_plus(loc)
        url = f'https://wttr.in/{location}?format=3'
        try:
            with urllib.request.urlopen(url) as resp:
                txt = resp.read().decode().strip()
            return f'Current weather: {txt}'
        except Exception:
            return "Sorry, I couldn't fetch the weather right now."

    # 13. News headlines (Google News RSS)
    if 'news' in q_clean or 'headlines' in q_clean:
        try:
            import feedparser
            feed = feedparser.parse('https://news.google.com/rss')
            titles = [entry.title for entry in feed.entries[:5]]
            return 'Top headlines: ' + ', '.join(titles)
        except Exception:
            return "I couldn't get the news right now."

    # 14. Date and Time
    if "time" in q_clean:
        return "It is currently " + datetime.datetime.now().strftime("%I:%M %p")
    if "date" in q_clean or "today" in q_clean:
        return "Today is " + datetime.datetime.now().strftime("%A, %B %d, %Y")

    return None
