"""Demo console: the control room of the lab.

Serves the dashboard (GET /, see dashboard.html), plays the shoppers of a
simulated shop under /shop/, and keeps one bucket of numbers per second.
Everything else is a GET that returns JSON:

  /api/state                    settings, per-second metrics, recent requests
  /api/set?cache=0&rate=30      change settings
  /api/do?action=purge|crash|restart|flash|reset
"""
import http.client
import json
import os
import random
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

TARGETS = {"edge": ("edge", 80), "origin": ("origin", 9000)}
SHOW_BODY = ("text/plain", "application/json")
HERE = os.path.dirname(os.path.abspath(__file__))


def fetch(target, path, headers=None, method="GET"):
    start = time.perf_counter()
    try:
        conn = http.client.HTTPConnection(*TARGETS[target], timeout=15)
        conn.request(method, path, headers=headers or {})
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
    except (OSError, http.client.HTTPException):
        return {"status": 0, "ms": round((time.perf_counter() - start) * 1000)}
    ctype = resp.getheader("Content-Type", "")
    body = raw.decode("utf-8", "replace").strip() if ctype.startswith(SHOW_BODY) else ""
    return {
        "status": resp.status,
        "cache": resp.getheader("X-Cache"),
        "age": resp.getheader("Age") if target == "edge" else None,
        "ms": round((time.perf_counter() - start) * 1000),
        "body": body[:200],
    }


def origin_admin(path):
    try:
        conn = http.client.HTTPConnection(*TARGETS["origin"], timeout=5)
        conn.request("GET", "/_demo/" + path)
        return json.loads(conn.getresponse().read())
    except (OSError, http.client.HTTPException, ValueError):
        return {"count": 0, "shop": 0, "active": 0, "down": True, "lines": [], "unreachable": True}


WINDOW = 120   # seconds of history
SALE_FOR = 15  # seconds a flash sale lasts
SALE_RATE = 40
USERS = 30

cfg = {
    "traffic": False,    # shoppers are browsing
    "rate": 20,          # requests per second
    "cache": True,       # edge may cache at all
    "strip_utm": False,  # edge drops utm_* from the cache key
    "collapse": True,    # edge merges identical requests in flight
    "stale": False,      # edge serves expired copies when the origin fails
    "private": False,    # origin marks the account page private (the fix)
}
EVENTS = {
    "traffic": ("Traffic on", "Traffic off"),
    "cache": ("Cache on", "Cache off"),
    "strip_utm": ("utm ignored", "utm in key"),
    "collapse": ("Merging on", "Merging off"),
    "stale": ("Stale on", "Stale off"),
    "private": ("Account private", "Account public"),
}
lock = threading.Lock()
buckets = {}
events = deque(maxlen=30)
recent = deque(maxlen=14)
state = {"sale_until": 0.0, "pending": 0, "origin_seen": None, "down": False, "active": 0}
pool = ThreadPoolExecutor(128)


def bucket(sec):
    return buckets.setdefault(sec, {"req": 0, "origin": 0, "hit": 0, "stale": 0, "miss": 0, "err": 0, "wrong": 0, "ms": []})


def note(label):
    with lock:
        events.append({"t": int(time.time()), "label": label})


def pick():
    """One page view: (path, user or None)."""
    roll = random.random()
    item = int(random.paretovariate(1.1)) % 20 + 1  # a few products get most of the views
    if roll < 0.55:
        path = f"/shop/p/{item}"
        if random.random() < 0.5:  # arrived through an ad
            source = random.choice(["facebook", "zalo", "tiktok", "google", "email"])
            path += f"?utm_source={source}&utm_campaign={random.randint(1, 12)}"
        return path, None
    if roll < 0.75:
        return f"/shop/api/stock/{item}", None
    if roll < 0.90:
        return "/shop/", None
    user = f"user{random.randint(1, USERS)}"
    return ("/shop/me-fixed" if cfg["private"] else "/shop/me"), user


def visit(path, user):
    headers = {}
    if not cfg["cache"]:
        headers["X-Demo-No-Cache"] = "1"
    if cfg["strip_utm"]:
        headers["X-Demo-Strip-Utm"] = "1"
    if not cfg["collapse"]:
        headers["X-Demo-No-Collapse"] = "1"
    if cfg["stale"]:
        headers["X-Demo-Stale"] = "1"
    if user:
        headers["Cookie"] = "user=" + user
    res = fetch("edge", path, headers)

    ok = res["status"] == 200
    kind = "err" if not ok else {"MISS": "miss", "HIT": "hit"}.get(res["cache"], "stale")
    wrong = False
    if ok and user:
        try:
            wrong = json.loads(res["body"]).get("user") != user
        except ValueError:
            pass
    with lock:
        state["pending"] -= 1
        b = bucket(int(time.time()))
        b["req"] += 1
        b[kind] += 1
        b["wrong"] += wrong
        b["ms"].append(res["ms"])
        recent.appendleft({"t": time.strftime("%H:%M:%S"), "user": user or "", "path": path,
                           "status": res["status"], "kind": kind, "ms": res["ms"], "wrong": wrong})


def submit(path, user):
    with lock:
        if state["pending"] > 300:  # the lab is saturated: drop rather than queue forever
            return
        state["pending"] += 1
    pool.submit(visit, path, user)


def shoppers():
    owed = 0.0
    last_sample = 0
    while True:
        time.sleep(0.1)
        now = time.time()
        if cfg["traffic"]:
            owed += cfg["rate"] / 10
            while owed >= 1:
                owed -= 1
                submit(*pick())
            if now < state["sale_until"]:
                for _ in range(SALE_RATE // 10):
                    submit("/shop/sale", None)
        if int(now) != last_sample:  # once a second: ask the origin how much it really did
            last_sample = int(now)
            info = origin_admin("log?since=999999999")
            with lock:
                seen = state["origin_seen"]
                if seen is not None and info["shop"] >= seen:
                    bucket(last_sample - 1)["origin"] = info["shop"] - seen
                state["origin_seen"] = info["shop"]
                state["down"], state["active"] = info["down"], info["active"]
                for sec in [s for s in buckets if s < last_sample - WINDOW - 5]:
                    del buckets[sec]


def percentile(values, p):
    return sorted(values)[min(len(values) - 1, int(len(values) * p))] if values else None


def snapshot():
    now = int(time.time())
    with lock:
        series = []
        for sec in range(now - WINDOW, now):  # the current second is still filling up
            b = buckets.get(sec)
            row = {"t": sec}
            if b:
                row.update({k: b[k] for k in ("req", "origin", "hit", "stale", "miss", "err", "wrong")})
                row["p50"], row["p95"] = percentile(b["ms"], 0.5), percentile(b["ms"], 0.95)
            series.append(row)
        return {
            "now": now,
            "cfg": dict(cfg),
            "sale": max(0, round(state["sale_until"] - time.time())),
            "origin": {"down": state["down"], "active": state["active"]},
            "series": series,
            "events": list(events),
            "recent": list(recent),
        }


def change(q):
    for key, values in q.items():
        if key == "rate":
            cfg["rate"] = max(1, min(int(values[0]), 80))
        elif key in cfg:
            value = values[0] in ("1", "true")
            if cfg[key] != value:
                cfg[key] = value
                note(EVENTS[key][0 if value else 1])
    return dict(cfg)


def act(action):
    if action == "purge":
        fetch("edge", "/", method="BAN")
        note("Purge")
    elif action in ("crash", "restart"):
        origin_admin(f"state?down={int(action == 'crash')}")
        note("Origin down" if action == "crash" else "Origin up")
    elif action == "flash":
        state["sale_until"] = time.time() + SALE_FOR
        note("Flash sale")
    elif action == "reset":
        cfg.update(traffic=False, rate=20, cache=True, strip_utm=False, collapse=True, stale=False, private=False)
        origin_admin("reset")
        fetch("edge", "/", method="BAN")
        with lock:
            buckets.clear()
            events.clear()
            recent.clear()
            state.update(sale_until=0.0, origin_seen=None)
    return {"ok": True}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        q = parse_qs(url.query)
        if url.path == "/":
            with open(os.path.join(HERE, "dashboard.html"), "rb") as page:
                return self.send(page.read(), "text/html; charset=utf-8")
        if url.path == "/api/state":
            out = snapshot()
        elif url.path == "/api/set":
            out = change(q)
        elif url.path == "/api/do":
            out = act(q.get("action", [""])[0])
        else:
            out = {"error": "unknown"}
        self.send(json.dumps(out).encode(), "application/json")

    def send(self, data, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=shoppers, daemon=True).start()
    print("console listening on :8090", flush=True)
    ThreadingHTTPServer(("", 8090), Handler).serve_forever()
