#!/usr/bin/env python3
"""Render monthly GitHub contributions for the last year as a 3D bar chart (oblique projection),
styled like ap.patru.eu: slate-to-rose gradient, light bars, the peak month in rose.

gh api graphql -f query='{user(login:"AlvaroP100"){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount}}}}}}' \
  | python3 scripts/contrib3d.py > assets/activity.svg
"""
import calendar, json, sys
from collections import OrderedDict

cal = json.load(sys.stdin)["data"]["user"]["contributionsCollection"]["contributionCalendar"]
months = OrderedDict()
for w in cal["weeks"]:
    for d in w["contributionDays"]:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["contributionCount"]
data = list(months.items())[-12:]

S, DEPTH, MAXH, GAP = 64, 0.9, 170, 0.18   # bar pitch, depth (in bars), tallest bar, inter-bar gap
DX, DY = 0.5, 0.32                         # how depth shifts right / up
peak = max(v for _, v in data) or 1
n = len(data)

def p(x, y, z):  # x right, y back, z up
    return (x * S + y * S * DX, -z - y * S * DY)

def pts(*q):
    return " ".join(f"{p(*v)[0]:.1f},{p(*v)[1]:.1f}" for v in q)

out = [f'<polygon class="plate" points="{pts((-.3,-.1,0),(n+.3,-.1,0),(n+.3,DEPTH+.3,0),(-.3,DEPTH+.3,0))}"/>']
for i, (k, v) in enumerate(data):
    h = 4 + MAXH * v / peak
    a, b, d = i + GAP / 2, i + 1 - GAP / 2, DEPTH
    cls = "bar" + (" z" if not v else " pk" if v == peak else "")
    out.append(
        f'<g class="{cls}" style="animation-delay:{i*45}ms">'
        f'<polygon class="r" points="{pts((b,0,0),(b,d,0),(b,d,h),(b,0,h))}"/>'
        f'<polygon class="t" points="{pts((a,0,h),(b,0,h),(b,d,h),(a,d,h))}"/>'
        f'<polygon class="f" points="{pts((a,0,0),(b,0,0),(b,0,h),(a,0,h))}"/></g>'
    )
    if v:
        tx, ty = p(i + .5, d / 2, h)
        out.append(f'<text class="v" x="{tx:.1f}" y="{ty-12:.1f}" text-anchor="middle">{v}</text>')
    mx, my = p(i + .5, 0, 0)
    out.append(f'<text class="m" x="{mx:.1f}" y="{my+34:.1f}" text-anchor="middle">{calendar.month_abbr[int(k[5:])]}</text>')

PAD = 44
x0, x1 = p(-.3, 0, 0)[0] - PAD, p(n + .3, DEPTH + .3, 0)[0] + PAD
y0, y1 = -MAXH - 90, 80
W, H = x1 - x0, y1 - y0
print(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0} {W:.0f} {H}" role="img" aria-labelledby="t">
<title id="t">3D bar chart of monthly GitHub contributions over the last year, {cal["totalContributions"]} in total</title>
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2228"/><stop offset=".6" stop-color="#353f44"/><stop offset="1" stop-color="#b98582"/></linearGradient></defs>
<style>
.f{{fill:#d9dcde}}.t{{fill:#f5f5f5}}.r{{fill:#8f969a}}
.pk .f{{fill:#d39794}}.pk .t{{fill:#ecc3c0}}.pk .r{{fill:#9c6865}}
.z .f{{fill:#2b3238}}.z .t{{fill:#363e45}}.z .r{{fill:#20262b}}
.plate{{fill:#fff;fill-opacity:.07}}
text{{font-family:system-ui,-apple-system,"SF Pro Text","Segoe UI",sans-serif}}
.m{{font-size:16px;fill:#f5f5f5;fill-opacity:.55}}.v{{font-size:20px;font-weight:600;fill:#f5f5f5}}
.title{{font-size:20px;font-weight:500;fill:#f5f5f5;letter-spacing:-.01em}}.cap{{font-size:14px;fill:#f5f5f5;fill-opacity:.55}}
@media (prefers-reduced-motion:no-preference){{.bar{{transform-box:fill-box;transform-origin:bottom;animation:up .8s cubic-bezier(.2,.8,.2,1) backwards}}}}
@keyframes up{{from{{transform:scaleY(.02)}}}}
</style>
<rect x="{x0:.0f}" y="{y0}" width="{W:.0f}" height="{H}" rx="28" fill="url(#bg)"/>
<text class="title" x="{x0+PAD:.0f}" y="{y0+50}">Activity</text>
<text class="cap" x="{x0+PAD:.0f}" y="{y0+74}">{cal["totalContributions"]} contributions in the last year</text>
{chr(10).join(out)}
</svg>''')
