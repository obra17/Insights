#!/usr/bin/env python3
"""Crawl a locally served site and report broken internal links/assets. Usage: check_links.py http://localhost:8787"""
import sys, re, json, urllib.request, urllib.parse
base = sys.argv[1].rstrip("/"); seen, bad, todo = set(), [], ["/","/sitemap.xml","/robots.txt","/llms.txt","/404.html"]
while todo:
    p = todo.pop()
    if p in seen: continue
    seen.add(p)
    try: r = urllib.request.urlopen(base+p); body = r.read().decode("utf-8","ignore"); ct = r.headers.get("content-type","")
    except Exception as e: bad.append((p, str(e))); continue
    if "html" in ct:
        for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', body, re.S): json.loads(m)
        for h in re.findall(r'(?:href|src)="([^"]+)"', body):
            u = urllib.parse.urlparse(h)
            if u.scheme in ("mailto","tel"): continue
            if u.scheme in ("http","https") and not h.startswith("https://obrainsights.com"): continue
            path = u.path if u.scheme else urllib.parse.urljoin(p, h).split("#")[0]
            if path: todo.append(path)
print(f"checked {len(seen)} URLs, {len(bad)} broken"); [print(" BROKEN", b) for b in bad]; sys.exit(1 if bad else 0)
