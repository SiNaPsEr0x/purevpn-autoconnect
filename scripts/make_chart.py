#!/usr/bin/env python3
"""Statistiche del repository: aggiorna i CSV e rigenera i grafici a barre (SVG).

  make_chart.py downloads TOTALE        totale cumulato dei download delle release
  make_chart.py clones FILE_JSON        risposta di GET /repos/.../traffic/clones

I CSV sono in docs/stats/, i grafici in docs/. Solo libreria standard.
"""
import csv, datetime, json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STATS = os.path.join(ROOT, "docs", "stats")
DOCS = os.path.join(ROOT, "docs")
DAYS = 30


def read_csv(path, ncols):
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as f:
        return {r[0]: [int(x) for x in r[1:ncols]] for r in csv.reader(f) if r and r[0] != "data"}


def write_csv(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for d in sorted(rows):
            w.writerow([d] + rows[d])


def render(path, title, total, series, caption):
    """series: [(data, valore)] già in ordine; barre alte quanto il valore."""
    data = series[-DAYS:]
    W, H = 720, 260
    left, right, top, base = 36, 24, 92, 206
    area_w, area_h = W - left - right, base - top
    slot = area_w / max(len(data), DAYS)
    bw = max(slot * 0.72, 3)
    vmax = max(max(v for _, v in data), 1)
    bars = []
    for i, (d, v) in enumerate(data):
        h = max(area_h * v / vmax, 3)
        x = left + i * slot + (slot - bw) / 2
        op = "0.35" if v == 0 else "1"
        bars.append(f'  <rect x="{x:.1f}" y="{base - h:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="2.5" '
                    f'fill="url(#g)" opacity="{op}"><title>{d}: {v}</title></rect>')
    font = "Inter,'Segoe UI',Roboto,Arial,sans-serif"
    mono = "ui-monospace,Consolas,monospace"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-label="{title}: {total}">
  <title>{title} (ultimi {DAYS} giorni)</title>
  <defs>
    <linearGradient id="g" x1="0" y1="1" x2="0" y2="0">
      <stop offset="0" stop-color="#0ea5e9"/><stop offset="1" stop-color="#22d3a6"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="18" fill="#0b1220"/>
  <text x="{left}" y="42" font-family="{font}" font-size="15" fill="#9fb3c8">{title}</text>
  <text x="{left}" y="78" font-family="{font}" font-size="34" font-weight="800" fill="#ffffff">{total}</text>
  <text x="{W-right}" y="42" text-anchor="end" font-family="{font}" font-size="13" fill="#6b829c">{caption}</text>
  <line x1="{left}" y1="{base}" x2="{W-right}" y2="{base}" stroke="#ffffff" stroke-opacity="0.15"/>
{chr(10).join(bars)}
  <text x="{left}" y="{base+24}" font-family="{mono}" font-size="12" fill="#6b829c">{data[0][0]}</text>
  <text x="{W-right}" y="{base+24}" text-anchor="end" font-family="{mono}" font-size="12" fill="#6b829c">{data[-1][0]}</text>
</svg>
'''
    with open(path, "w") as f:
        f.write(svg)


def downloads(total):
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    csv_path = os.path.join(STATS, "downloads.csv")
    rows = read_csv(csv_path, 2)
    rows[today] = [total]
    write_csv(csv_path, ["data", "totale"], rows)
    series = [(d, rows[d][0]) for d in sorted(rows)]
    render(os.path.join(DOCS, "downloads.svg"), "Download cumulati", total, series, f"ultimi {DAYS} giorni")
    print(f"download: totale {total}, {len(rows)} giorni")


def clones(json_path):
    with open(json_path) as f:
        api = json.load(f)
    csv_path = os.path.join(STATS, "clones.csv")
    rows = read_csv(csv_path, 3)          # data -> [count, uniques]
    for c in api.get("clones", []):
        d = c["timestamp"][:10]
        old = rows.get(d, [0, 0])
        rows[d] = [max(old[0], c["count"]), max(old[1], c["uniques"])]  # l'API tiene solo 14 giorni
    write_csv(csv_path, ["data", "clone", "unici"], rows)
    run, series = 0, []
    for d in sorted(rows):
        run += rows[d][0]
        series.append((d, run))
    if not series:
        series = [(datetime.date.today().isoformat(), 0)]
    render(os.path.join(DOCS, "clones.svg"), "Git clone cumulati", run, series, f"ultimi {DAYS} giorni")
    print(f"clone: totale {run}, {len(rows)} giorni")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "downloads":
        downloads(int(sys.argv[2]))
    elif len(sys.argv) == 3 and sys.argv[1] == "clones":
        clones(sys.argv[2])
    else:
        sys.exit(__doc__)
