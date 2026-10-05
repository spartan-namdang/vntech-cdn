"""Demo origin: a far-away server that logs every request it has to answer.

The log is the point of the demo. When the edge answers from cache, nothing
is printed here.

/_demo/* is the control channel used by the console: read the counters, play
dead, reset.
"""
import json
import os
import threading
import time
from collections import deque
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

DELAY = int(os.environ.get("ORIGIN_DELAY_MS", "200")) / 1000  # simulated distance
YEAR = 31536000

count = 0
shop_count = 0
active = 0  # requests being answered right now
down = False
log = deque(maxlen=300)
lock = threading.Lock()


def now():
    return time.strftime("%H:%M:%S")


def route(path, user):
    """Return (status, cache_control, content_type, body, extra_delay)."""
    if path == "/assets/app.3f9a1c.js":
        return 200, f"public, max-age={YEAR}, immutable", "text/javascript", "console.log('app');\n", 0
    built = json.dumps({"built": now()}) + "\n"  # proves which render a visitor got
    if path.startswith("/shop/"):  # the dashboard's simulated shop
        if path == "/shop/me":
            return 200, "public, max-age=60", "application/json", json.dumps({"user": user}) + "\n", 0
        if path == "/shop/me-fixed":
            return 200, "private, no-store", "application/json", json.dumps({"user": user}) + "\n", 0
        if path.startswith("/shop/api/"):
            return 200, "public, s-maxage=3", "application/json", built, 0
        if path.startswith("/shop/sale"):
            return 200, "public, s-maxage=5", "application/json", built, 1
        return 200, "public, s-maxage=10", "application/json", built, 0
    if path == "/products":
        return 200, "public, s-maxage=60", "application/json", built, 0
    if path == "/api/news":
        cc = "s-maxage=5, stale-while-revalidate=10, stale-if-error=600"
        return 200, cc, "application/json", built, 0
    if path == "/api/prices":
        return 200, "s-maxage=5", "application/json", built, 0
    if path == "/slow":
        return 200, "s-maxage=5", "application/json", built, 1
    if path == "/me":  # the bug: personal content marked as shareable
        return 200, "public, max-age=60", "application/json", json.dumps({"user": user}) + "\n", 0
    if path == "/me-fixed":
        return 200, "private, no-store", "application/json", json.dumps({"user": user}) + "\n", 0
    return 404, "no-store", "text/plain", "not found\n", 0


def control(path, query):
    """The /_demo/ control channel. Returns a JSON-able dict."""
    global count, shop_count, down
    with lock:
        if path == "/_demo/state":
            down = query.get("down", ["0"])[0] == "1"
            print(f"{now()}  \033[1;31m-- origin {'DOWN' if down else 'UP'} --\033[0m", flush=True)
        elif path == "/_demo/reset":
            count, shop_count, down = 0, 0, False
            log.clear()
            print(f"{now()}  -- reset --", flush=True)
        since = int(query.get("since", ["0"])[0])
        return {"count": count, "shop": shop_count, "active": active, "down": down,
                "lines": [l for l in log if l["n"] > since]}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        global count, shop_count, active
        url = urlsplit(self.path)
        path = url.path
        if path.startswith("/_demo/"):
            return self.reply(200, "no-store", "application/json", json.dumps(control(path, parse_qs(url.query))))
        if down:  # play dead: drop the connection without answering
            self.close_connection = True
            return
        if path == "/healthz":  # edge health probe: no delay, not logged
            return self.reply(200, "no-store", "text/plain", "ok\n")

        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        user = cookie["user"].value if "user" in cookie else "khách"
        status, cc, ctype, body, extra = route(path, user)

        with lock:
            active += 1
            busy = active
            if path.startswith("/shop/"):  # dashboard traffic: counted, not logged line by line
                shop_count += 1
                n = 0
            else:
                count += 1
                n = count
                log.append({"n": n, "path": self.path, "status": status})
        if n:
            colour = "\033[32m" if status < 400 else "\033[31m"
            print(f"{now()}  \033[1m#{n:<4}\033[0m {self.command} {self.path}  {colour}{status}\033[0m", flush=True)

        try:
            # a small server: past 4 requests at once, every one of them gets slower
            time.sleep((DELAY + extra) * (1 + max(0, busy - 4) / 16))
            self.reply(status, cc, ctype, body)
        finally:
            with lock:
                active -= 1

    do_HEAD = do_GET

    def reply(self, status, cc, ctype, body):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Cache-Control", cc)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def log_message(self, *args):  # replaced by the line printed in do_GET
        pass


if __name__ == "__main__":
    print(f"origin listening on :9000, {int(DELAY * 1000)} ms away", flush=True)
    ThreadingHTTPServer(("", 9000), Handler).serve_forever()
