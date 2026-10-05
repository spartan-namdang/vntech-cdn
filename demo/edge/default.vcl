vcl 4.1;

import std;

backend origin {
    .host = "origin";
    .port = "9000";
    .probe = {
        .url = "/healthz";
        .interval = 1s;
        .timeout = 1s;
        .window = 3;
        .threshold = 2;
    }
}

sub vcl_recv {
    # Reset between rehearsals: BAN empties the whole cache.
    if (req.method == "BAN") {
        ban("obj.status != 0");
        return (synth(200, "Cache emptied"));
    }
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }

    # Demo switch for the cache-key scene: tracking parameters do not change
    # the response, so they are removed before the key is computed.
    if (req.http.X-Demo-Strip-Utm) {
        set req.url = regsuball(req.url, "([?&])utm_[a-z]+=[^&]*&?", "\1");
        set req.url = regsub(req.url, "[?&]$", "");
    }

    # Demo switch for the stampede scene: do not wait for a fetch that is
    # already in flight, so every concurrent MISS goes to the origin.
    if (req.http.X-Demo-No-Collapse) {
        set req.hash_ignore_busy = true;
    }

    # Dashboard switch "Cache at the edge" off: everything goes to the origin.
    if (req.http.X-Demo-No-Cache) {
        return (pass);
    }

    # While the origin is healthy, serve stale for at most 10 s (the
    # stale-while-revalidate window of /api/news). When it is down, the full
    # grace set in vcl_backend_response applies.
    # /shop/ is the dashboard's traffic: there, stale is an edge setting
    # (X-Demo-Stale) rather than something the origin asks for.
    if (req.url ~ "^/shop/" && !req.http.X-Demo-Stale) {
        set req.grace = 0s;
    } else if (std.healthy(req.backend_hint)) {
        set req.grace = 10s;
    }

    # Like most commercial CDNs: a Cookie neither blocks caching nor enters
    # the cache key. The origin's Cache-Control decides.
    return (hash);
}

sub vcl_backend_response {
    if (bereq.url ~ "^/shop/") {
        # keep expired copies around so the dashboard's stale switch can use them
        set beresp.grace = 10m;
    } else if (beresp.http.Cache-Control ~ "stale-if-error=\d+") {
        set beresp.grace = std.duration(
            regsub(beresp.http.Cache-Control, ".*stale-if-error=(\d+).*", "\1s"), 0s);
    }
}

sub vcl_backend_error {
    # Dashboard traffic: answer 503 without storing an error object, so the
    # expired copy survives and the stale switch can still use it later.
    if (bereq.url ~ "^/shop/") {
        return (abandon);
    }
}

sub vcl_deliver {
    if (obj.hits == 0) {
        set resp.http.X-Cache = "MISS";
    } else if (obj.ttl < 0s) {
        set resp.http.X-Cache = "HIT (stale)";
    } else {
        set resp.http.X-Cache = "HIT";
    }
}
