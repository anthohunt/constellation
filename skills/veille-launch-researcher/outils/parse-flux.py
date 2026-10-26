#!/usr/bin/env python3
"""parse-flux.py — un flux RSS/Atom en lignes « date<TAB>url<TAB>titre »."""
import sys, re, email.utils, datetime

s = sys.stdin.read()
for m in re.finditer(r"<(item|entry)\b.*?</\1>", s, re.S):
    b = m.group(0)

    def g(*noms):
        for x in noms:
            r = re.search(r"<%s[^>]*>(.*?)</%s>" % (x, x), b, re.S)
            if r:
                return re.sub(r"<[^>]+>", "", r.group(1)).strip()
            r = re.search(r'<%s[^>]*href="([^"]+)"' % x, b)
            if r:
                return r.group(1)
        return ""

    d = g("published", "pubDate", "updated")
    try:
        dt = email.utils.parsedate_to_datetime(d)
    except Exception:
        try:
            dt = datetime.datetime.fromisoformat(d.replace("Z", "+00:00"))
        except Exception:
            continue
    print("%s\t%s\t%s" % (dt.strftime("%Y%m%d"), g("link", "guid"), g("title")))
