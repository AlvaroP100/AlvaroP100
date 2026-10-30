#!/usr/bin/env python3
"""Render monthly GitHub contributions for the last year as a 3D bar chart (oblique projection).

gh api graphql -f query='{user(login:"AlvaroP100"){contributionsCollection{contributionCalendar{
  totalContributions weeks{contributionDays{date contributionCount}}}}}}' \
  | python3 scripts/contrib3d.py > assets/activity-3d.svg
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

out = [f'<polygon class="plate" points="{pts((-.3,-.1,0),(n+.3-1+1,-.1,0),(n+.3,DEPTH+.3,0),(-.3,DEPTH+.3,0))}"/>']
for i, (k, v) in enumerate(data):
    h = 4 + MAXH * v / peak
    a, b = i + GAP / 2, i + 1 - GAP / 2
    d = DEPTH
    out.append(
        f'<g class="bar{" z" if not v else ""}" style="animation-delay:{i*45}ms">'
        f'<polygon class="r" points="{pts((b,0,0),(b,d,0),(b,d,h),(b,0,h))}"/>'
        f'<polygon class="t" points="{pts((a,0,h),(b,0,h),(b,d,h),(a,d,h))}"/>'
        f'<polygon class="f" points="{pts((a,0,0),(b,0,0),(b,0,h),(a,0,h))}"/></g>'
    )
    cx, cy = p(i + .5 + d * DX / 1, d, h)
    if v:
        tx, ty = p(i + .5, d / 2, h)
        out.append(f'<text class="v" x="{tx:.1f}" y="{ty-12:.1f}" text-anchor="middle">{v}</text>')
    mx, my = p(i + .5, 0, 0)
    out.append(f'<text class="m" x="{mx:.1f}" y="{my+34:.1f}" text-anchor="middle">{calendar.month_abbr[int(k[5:])]}</text>')

x0, x1 = p(-.3, 0, 0)[0] - 20, p(n + .3, DEPTH + .3, 0)[0] + 20
y0, y1 = -MAXH - 60, 60
print(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.0f} {y0} {x1-x0:.0f} {y1-y0}" role="img" aria-labelledby="t">
<title id="t">3D bar chart of monthly GitHub contributions over the last year, {cal["totalContributions"]} in total</title>
<style>
:root{{--f:#007aff;--t:#5ac8fa;--r:#0051d5;--zf:#d1d1d6;--zt:#e5e5ea;--zr:#aeaeb2;--plate:#f2f2f7;--fg:#1d1d1f;--sub:#8e8e93}}
@media (prefers-color-scheme:dark){{:root{{--f:#0a84ff;--t:#64d2ff;--r:#0040a8;--zf:#3a3a3c;--zt:#48484a;--zr:#2c2c2e;--plate:#1c1c1e;--fg:#f5f5f7;--sub:#98989d}}}}
.plate{{fill:var(--plate)}}.f{{fill:var(--f)}}.t{{fill:var(--t)}}.r{{fill:var(--r)}}
.z .f{{fill:var(--zf)}}.z .t{{fill:var(--zt)}}.z .r{{fill:var(--zr)}}
text{{font-family:-apple-system,"SF Pro Text","Helvetica Neue",Helvetica,Arial,sans-serif}}
.m{{font-size:16px;fill:var(--sub)}}.v{{font-size:20px;font-weight:600;fill:var(--fg)}}
@media (prefers-reduced-motion:no-preference){{.bar{{transform-box:fill-box;transform-origin:bottom;animation:up .8s cubic-bezier(.2,.8,.2,1) backwards}}}}
@keyframes up{{from{{transform:scaleY(.02)}}}}
</style>
{chr(10).join(out)}
</svg>''')
