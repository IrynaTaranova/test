#!/usr/bin/env python3
"""Пробний збір топ-лістингів Prom.ua (SSR ApolloCacheState) -> CSV."""
import csv, json, re, sys, time, urllib.parse, urllib.request, ssl

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "uk"})
    with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as r:
        return r.read().decode("utf8", "replace")

def parse(html):
    m = re.search(r"window\.ApolloCacheState\s*=\s*", html)
    if not m:
        return None
    o, _ = json.JSONDecoder().raw_decode(html[m.end():])
    for k, v in o.get("_FAST_CACHE", {}).items():
        if k.startswith(("CategoryListingQuery", "SearchListingQuery", "ListingQuery")) or "listing" in str(v.get("result", {}))[:200]:
            lst = v["result"]["listing"]
            return lst
    return None

def rows(label, url):
    lst = None
    for attempt in range(3):
        try:
            lst = parse(fetch(url))
        except Exception:
            lst = None
        if lst and lst["page"]["products"]:
            break
        time.sleep(3 * (attempt + 1))
    if not lst:
        return []
    pg = lst["page"]
    out = []
    for p in pg["products"]:
        p = p.get("product", p)
        c = p.get("company") or {}
        oc = p.get("productOpinionCounters") or {}
        out.append(dict(
            query=label, total_in_listing=pg.get("total"), id=p["id"], name=p["name"],
            price=p.get("price"), disc_price=p.get("discountedPrice") if p.get("hasDiscount") else "",
            rating=oc.get("rating"), reviews=oc.get("count"),
            seller=c.get("name"), seller_reviews=(c.get("opinionStats") or {}).get("opinionTotal"),
            avail=(p.get("presence") or {}).get("isAvailable"),
            url="https://prom.ua/ua/p%s-%s.html" % (p["id"], p.get("urlText")),
        ))
    return out

if __name__ == "__main__":
    out_path, pages, *terms = sys.argv[1:]
    pages = int(pages)
    if terms and terms[0].startswith('@'):
        terms = [l.strip() for l in open(terms[0][1:], encoding='utf8') if l.strip()]
    allr = []
    for t in terms:
        r = []
        for pg in range(1, pages + 1):
            url = "https://prom.ua/ua/search?" + urllib.parse.urlencode({"search_term": t, "page": pg})
            r += rows(t, url)
            time.sleep(2)
        print(f"{t}: {len(r)} товарів, total={r[0]['total_in_listing'] if r else '-'}")
        allr += r
    if allr:
        with open(out_path, "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=list(allr[0])); w.writeheader(); w.writerows(allr)
