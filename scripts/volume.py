#!/usr/bin/env python3
"""Render my commit history as a volumetric 3D scatter in a wireframe cube (scientific-visualization look).

Axes: x = date, y = hour of day (Europe/Bucharest), z = project. Colour = lines changed (log scale, jet colormap).
Each commit is drawn as a small glowing cluster; the cluster is a visual splat, the position and colour are real.

  python3 scripts/volume.py data/commits.json assets/
"""
import json, math, random, sys
from datetime import datetime
from zoneinfo import ZoneInfo

data = json.load(open(sys.argv[1]))
outdir = sys.argv[2].rstrip("/")
TZ = ZoneInfo("Europe/Bucharest")
pts = []
for c in data:
    d = datetime.fromisoformat(c["t"].replace("Z", "+00:00")).astimezone(TZ)
    pts.append((d, d.hour + d.minute / 60, c["p"], c["n"]))
t0 = min(p[0] for p in pts).replace(hour=0, minute=0, second=0, microsecond=0)
t1 = max(p[0] for p in pts)
span = (t1 - t0).total_seconds()
nproj = max(p[2] for p in pts) + 1
nmax = max(p[3] for p in pts)
LMAX = math.log1p(nmax)

def clamp(v): return max(0.0, min(1.0, v))
def jet(t):
    t = .1 + .9 * clamp(t)
    r, g, b = (clamp(1.5 - abs(4 * t - k)) for k in (3, 2, 1))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))

YAW, PITCH, DIST = math.radians(-33), math.radians(17), 3.4

def rot(x, y, z):
    x1, z1 = x * math.cos(YAW) + z * math.sin(YAW), -x * math.sin(YAW) + z * math.cos(YAW)
    return x1, y * math.cos(PITCH) - z1 * math.sin(PITCH), y * math.sin(PITCH) + z1 * math.cos(PITCH)

def make_proj(cx, cy, S):
    def proj(x, y, z):
        x2, y2, z2 = rot(x, y, z)
        f = DIST / (DIST - z2)
        return cx + S * x2 * f, cy - S * y2 * f, z2
    return proj

def cloud(proj, S):
    dots = []
    for d, hour, p, n in pts:
        rnd = random.Random(f"{d.isoformat()}{p}{n}")
        tc = math.log1p(n) / LMAX
        cx_ = (d - t0).total_seconds() / span - .5
        cy_ = hour / 24 - .5
        cz_ = (p + .5) / nproj - .5
        sx, sy = .02 + .025 * tc, .008 + .012 * tc   # clusters stretch along time, like the streaks in the reference
        for _ in range(int(5 + 26 * tc ** 1.4)):
            ox, oy, oz = rnd.gauss(0, sx), rnd.gauss(0, sy), rnd.gauss(0, .008)
            r = min(1, math.sqrt((ox / sx) ** 2 + (oy / sy) ** 2) / 2.6)
            x, y, z = max(-.5, min(.5, cx_ + ox)), max(-.5, min(.5, cy_ + oy)), max(-.5, min(.5, cz_ + oz))
            px, py, depth = proj(x, y, z)
            dots.append((depth, px, py, jet(tc * (1 - .75 * r) + rnd.gauss(0, .03)), 1.3 + 1.2 * (1 - r) * tc + .5 * rnd.random()))
    dots.sort()
    return "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}"/>' for _, x, y, c, r in dots)

def cube(proj):
    V = [(x, y, z) for x in (-.5, .5) for y in (-.5, .5) for z in (-.5, .5)]
    P = {v: proj(*v) for v in V}
    far = min(V, key=lambda v: P[v][2])
    edges = [(a, b) for a in V for b in V if a < b and sum(i != j for i, j in zip(a, b)) == 1]
    s = ""
    for a, b in edges:
        hid = far in (a, b)
        s += (f'<line x1="{P[a][0]:.1f}" y1="{P[a][1]:.1f}" x2="{P[b][0]:.1f}" y2="{P[b][1]:.1f}" '
              + ('class="h"/>' if hid else 'class="e"/>'))
    return s, P

def labels(proj, P):
    near = max((v for v in P if v[1] == -.5), key=lambda v: P[v][2])
    s = ""
    months, m = [], t0.replace(day=1)
    while m <= t1:
        months.append(m)
        m = m.replace(year=m.year + (m.month == 12), month=m.month % 12 + 1)
    for m in months:
        f = (m - t0).total_seconds() / span
        if 0 <= f <= 1:
            x, y, _ = proj(f - .5, -.5, near[2])
            s += f'<text class="l" x="{x:.0f}" y="{y + 24:.0f}" text-anchor="middle">{m.strftime("%b")}</text>'
    nearv = max((v for v in P if v[0] == -.5 and v[1] == -.5), key=lambda v: P[v][2])
    for h in (0, 12, 24):
        x, y, _ = proj(-.5, h / 24 - .5, nearv[2])
        s += f'<text class="l" x="{x - 12:.0f}" y="{y + 5:.0f}" text-anchor="end">{h}h</text>'
    return s

def gizmo(x0, y0, L=54):
    s = ""
    for (dx, dy, dz), col, name in (((1, 0, 0), "#7c7cff", "time"), ((0, 1, 0), "#6df06d", "hour"), ((0, 0, 1), "#ff6060", "project")):
        x, y, _ = rot(dx, dy, dz)
        ex, ey = x0 + x * L, y0 - y * L
        s += (f'<line x1="{x0}" y1="{y0}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="{col}" stroke-width="3" stroke-linecap="round"/>'
              f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="4" fill="{col}"/>'
              f'<text class="g" x="{ex + (8 if x >= 0 else -8):.0f}" y="{ey + 4:.0f}" text-anchor="{"start" if x >= 0 else "end"}" fill="{col}">{name}</text>')
    return s

def fmt(v):
    return f"{v/1000:.1f}k" if v >= 1000 else f"{v:.0f}"

def colorbar(x, y, w, h):
    steps = 24
    s = ""
    for i in range(steps):
        t = 1 - i / (steps - 1)
        s += f'<rect x="{x}" y="{y + i * h / steps:.1f}" width="{w}" height="{h / steps + .6:.1f}" fill="{jet(t)}"/>'
        if i % 3 == 0:
            s += f'<text class="l" x="{x + w + 8}" y="{y + i * h / steps + 9:.0f}">{fmt(math.expm1(t * LMAX))}</text>'
    s += f'<text class="l" x="{x}" y="{y - 12}">lines changed</text>'
    return s

STYLE = '''<style>
.e{stroke:#fff;stroke-width:2.4;stroke-linecap:round}
.h{stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-dasharray:.1 7}
.l{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#cfd4d8}
.g{font:12px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
.n{font:400 68px system-ui,-apple-system,"SF Pro Display","Segoe UI",sans-serif;letter-spacing:-.04em;fill:#f5f5f5}
.s{font:400 22px system-ui,-apple-system,"SF Pro Text","Segoe UI",sans-serif;fill:#f5f5f5;fill-opacity:.62}
.k{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:#f5f5f5;fill-opacity:.55;letter-spacing:.04em}
@media (prefers-reduced-motion:no-preference){.pts{animation:in 1.4s ease-out backwards}.rise{animation:rise .9s cubic-bezier(.2,.8,.2,1) backwards}}
@keyframes in{from{opacity:0}}@keyframes rise{from{opacity:0;transform:translateY(12px)}}
</style>'''

def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">'
            f'<title id="t">{title}</title>{STYLE}<rect width="{w}" height="{h}" rx="24" fill="#000"/>{body}</svg>')

# --- full volume ---
W, H = 1200, 800
pr = make_proj(640, 400, 470)
cb, P = cube(pr)
body = (cb + f'<g class="pts">{cloud(pr, 470)}</g>' + labels(pr, P) + colorbar(40, 70, 18, 300) + gizmo(90, 735)
        + f'<text class="k" x="{W - 40}" y="{H - 28}" text-anchor="end">{len(pts)} COMMITS · {t0.strftime("%d %b").upper()} – {t1.strftime("%d %b %Y").upper()}</text>')
open(f"{outdir}/volume.svg", "w").write(svg(W, H, f"3D volume of {len(pts)} commits by date, hour and project, coloured by lines changed", body))

# --- hero ---
W, H = 1200, 460
pr = make_proj(985, 232, 250)
cb, P = cube(pr)
body = (f'<g transform="translate(0 0)">{cb}<g class="pts">{cloud(pr, 250)}</g></g>'
        '<g class="rise"><text class="k" x="64" y="132">ALVAROP100 · SOFTWARE &amp; SYSTEMS DEVELOPER</text>'
        '<text class="n" x="60" y="218">Alvaro Patru.</text>'
        '<text class="n" x="60" y="296" fill-opacity=".5" style="fill-opacity:.5">I build things that work.</text>'
        '<text class="s" x="64" y="350">Apps, AI workflows and the systems behind them.</text></g>')
open(f"{outdir}/hero-volume.svg", "w").write(svg(W, H, "Alvaro Patru. I build things that work.", body))
print("ok", len(pts), "commits")
