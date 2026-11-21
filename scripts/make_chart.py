#!/usr/bin/env python3
"""Aggiorna docs/stats/downloads.csv e rigenera docs/downloads.svg (barre che salgono).

Uso: make_chart.py TOTALE_DOWNLOAD
Il CSV contiene una riga al giorno: data,totale_cumulato. Solo libreria standard.
"""
import csv, datetime, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CSV = os.path.join(ROOT, "docs", "stats", "downloads.csv")
SVG = os.path.join(ROOT, "docs", "downloads.svg")
DAYS = 30

total = int(sys.argv[1]) if len(sys.argv) > 1 else 0
today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()

rows = []
if os.path.exists(CSV):
    with open(CSV, newline="") as f:
        rows = [(r[0], int(r[1])) for r in csv.reader(f) if r and r[0] != "data"]
rows = [r for r in rows if r[0] != today] + [(today, total)]
rows.sort()
os.makedirs(os.path.dirname(CSV), exist_ok=True)
with open(CSV, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["data", "totale"])
    w.writerows(rows)

data = rows[-DAYS:]
W, H = 720, 260
left, right, top, base = 36, 24, 92, 206
area_w = W - left - right
area_h = base - top
n = len(data)
slot = area_w / max(n, DAYS)
bw = max(slot * 0.72, 3)
vmax = max(max(v for _, v in data), 1)

bars = []
for i, (d, v) in enumerate(data):
    h = max(area_h * v / vmax, 3)
    x = left + i * slot + (slot - bw) / 2
    y = base - h
    op = "0.35" if v == 0 else "1"
    bars.append(
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2.5" '
        f'fill="url(#g)" opacity="{op}"><title>{d}: {v} download</title></rect>'
    )

first, last = data[0][0], data[-1][0]
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="Download cumulati: {total}">
  <title>Download cumulati (ultimi {DAYS} giorni)</title>
  <defs>
    <linearGradient id="g" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#0ea5e9"/><stop offset="1" stop-color="#22d3a6"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="18" fill="#0b1220"/>
  <text x="{left}" y="42" font-family="Inter,'Segoe UI',Roboto,Arial,sans-serif" font-size="15" fill="#9fb3c8">Download cumulati</text>
  <text x="{left}" y="78" font-family="Inter,'Segoe UI',Roboto,Arial,sans-serif" font-size="34" font-weight="800" fill="#ffffff">{total}</text>
  <text x="{W-right}" y="42" text-anchor="end" font-family="Inter,'Segoe UI',Roboto,Arial,sans-serif" font-size="13" fill="#6b829c">ultimi {DAYS} giorni</text>
  <line x1="{left}" y1="{base}" x2="{W-right}" y2="{base}" stroke="#ffffff" stroke-opacity="0.15"/>
  {chr(10).join("  " + b for b in bars)}
  <text x="{left}" y="{base+24}" font-family="ui-monospace,Consolas,monospace" font-size="12" fill="#6b829c">{first}</text>
  <text x="{W-right}" y="{base+24}" text-anchor="end" font-family="ui-monospace,Consolas,monospace" font-size="12" fill="#6b829c">{last}</text>
</svg>
'''
with open(SVG, "w") as f:
    f.write(svg)
print(f"{today}: totale {total}, {len(rows)} giorni registrati")
