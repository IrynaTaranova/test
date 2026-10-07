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
    lst = parse(fetch(url))
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
    out_path, *terms = sys.argv[1:]
    allr = []
    for t in terms:
        url = "https://prom.ua/ua/search?" + urllib.parse.urlencode({"search_term": t})
        try:
            r = rows(t, url)
        except Exception as e:
            print("ERR", t, e); r = []
        print(f"{t}: {len(r)} товарів, total={r[0]['total_in_listing'] if r else '-'}")
        allr += r
        time.sleep(2)
    if allr:
        with open(out_path, "w", newline="", encoding="utf8") as f:
            w = csv.DictWriter(f, fieldnames=list(allr[0])); w.writeheader(); w.writerows(allr)
