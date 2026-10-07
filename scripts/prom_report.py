#!/usr/bin/env python3
"""CSV збору -> markdown-таблиця з оцінкою ніш під односторінковий сайт.

Score (0-100), прості прозорі правила:
  попит      (0-35): сума відгуків топ-товарів (лог-шкала) - проксі продажів
  слабка конк.(0-30): мало продавців з великою кількістю відгуків, низька медіана відгуків
  ціна       (0-20): оптимум 250-1500 грн (є запас під рекламу й наложку)
  якість-gap (0-15): низький рейтинг лідерів = можна зробити краще
"""
import csv, math, statistics as st, sys
from collections import defaultdict

def f(x):
    try: return float(x)
    except (TypeError, ValueError): return 0.0

def score(rs):
    rv = [f(r["reviews"]) for r in rs]
    pr = [f(r["price"]) for r in rs if f(r["price"]) > 0]
    top = sorted(rv, reverse=True)[:10]
    demand = min(35, 35 * math.log10(1 + sum(top)) / 3.0)
    strong = sum(1 for x in rv if x >= 50)
    comp = max(0, 30 - 6 * strong - 1.0 * st.median(rv)) if rv else 0
    mp = st.median(pr) if pr else 0
    price = 20 if 250 <= mp <= 1500 else 12 if 150 <= mp < 250 or 1500 < mp <= 2500 else 4
    rated = [f(r["rating"]) for r in rs if f(r["reviews"]) >= 5]
    gap = 15 * max(0, min(1, (4.8 - st.mean(rated)) / 0.6)) if rated else 7
    return round(demand + comp + price + gap), mp, st.median(rv), strong, (st.mean(rated) if rated else 0)

def main(path):
    g = defaultdict(list)
    for r in csv.DictReader(open(path, encoding="utf8")):
        g[r["query"]].append(r)
    res = []
    for q, rs in g.items():
        s, mp, mrv, strong, rt = score(rs)
        top = max(rs, key=lambda r: f(r["reviews"]))
        res.append((s, q, rs[0]["total_in_listing"], len(rs), mp, mrv, strong, rt, top))
    res.sort(reverse=True)
    print("| # | Запит (біль) | Оцінка | Товарів у видачі | Медіана ціни ₴ | Медіана відгуків | Товарів ≥50 відгуків | Сер. рейтинг | Лідер (відгуки / ціна) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for i, (s, q, tot, n, mp, mrv, strong, rt, top) in enumerate(res, 1):
        print(f"| {i} | {q} | **{s}** | {tot} | {mp:.0f} | {mrv:.0f} | {strong} | {rt:.1f} | {top['name'][:40]} ({top['reviews']} / {top['price']}) |")

if __name__ == "__main__":
    main(sys.argv[1])
