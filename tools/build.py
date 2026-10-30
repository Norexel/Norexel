"""Builds the profile SVGs. Text is converted to outlines (Bahnschrift) so it renders
identically on GitHub, which cannot load web fonts inside an <img>.

Run: python tools/build.py   (needs: pip install fonttools; uses the Bahnschrift font that ships with Windows)
"""
import re
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).parent.parent
OUT = ROOT / "assets"

GROUND = "#101214"
FIELD = "#1A1E22"
INK = "#F2F3F0"
SOFT = "#A9AFB5"
ACCENT = "#FF5A1F"

_fonts = {}


def font(weight):
    if weight not in _fonts:
        f = TTFont("C:/Windows/Fonts/bahnschrift.ttf")
        f = instancer.instantiateVariableFont(f, {"wght": weight, "wdth": 100})
        _fonts[weight] = f
    return _fonts[weight]


def glyph(ch, size, x, y, weight):
    f = font(weight)
    upm = f["head"].unitsPerEm
    gs = f.getGlyphSet()
    name = f.getBestCmap()[ord(ch)]
    s = size / upm
    pen = SVGPathPen(gs)
    gs[name].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
    return pen.getCommands(), gs[name].width * s


def width(text, size, weight, track=0.0):
    w = 0.0
    for ch in text:
        _, adv = glyph(ch, size, 0, 0, weight)
        w += adv + track * size
    return w - track * size


def text(t, x, y, size, fill, weight=700, track=0.0, per_letter=False, cls=""):
    """Outlined text. per_letter=True returns one <path> per letter (for stagger)."""
    parts, cx = [], x
    for i, ch in enumerate(t):
        if ch == " ":
            _, adv = glyph("n", size, 0, 0, weight)
            cx += adv * 0.55 + track * size
            continue
        d, adv = glyph(ch, size, cx, y, weight)
        parts.append((i, d))
        cx += adv + track * size
    if per_letter:
        return "".join(
            f'<path class="l {cls}" style="--i:{n}" fill="{fill}" d="{d}"/>'
            for n, (_, d) in enumerate(parts)
        )
    return f'<path class="{cls}" fill="{fill}" d="{"".join(d for _, d in parts)}"/>'


def fit_size(t, target_w, weight, track):
    return target_w / (width(t, 100, weight, track) / 100)


def svg(w, h, body, title, desc=""):
    css = """
    @keyframes rise{from{transform:translateY(70px);opacity:0}}
    @keyframes fade{from{opacity:0}}
    @keyframes draw{from{stroke-dashoffset:1}}
    @keyframes pop{from{transform:scale(0);opacity:0}}
    .l{animation:rise 1s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--i)*70ms + 150ms)}
    .in{animation:fade .8s ease-out both;animation-delay:calc(var(--d,0)*1ms)}
    .line{stroke-dasharray:1;animation:draw 2.6s cubic-bezier(.45,.05,.2,1) .4s both}
    .pt{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--d,0)*1ms)}
    @media (prefers-reduced-motion:reduce){*{animation:none!important}}
    """
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
        f"<title>{title}</title><desc>{desc}</desc><style>{css}</style>{body}</svg>"
    )


def write(name, s):
    (OUT / name).write_text(s, encoding="utf-8")
    print("wrote", name, len(s) // 1024, "KB")


# ---------------------------------------------------------------- hero
def hero():
    W, H = 1200, 600
    track = -0.02
    size = fit_size("NOREXEL", 700, 700, track)
    b = [f'<rect width="{W}" height="{H}" fill="{GROUND}"/>']
    b.append(f'<rect x="800" width="400" height="{H}" fill="{ACCENT}"/>')
    b.append(text("NOREXEL", 56, 300, size, INK, 700, track, per_letter=True))
    b.append(text("I am Norex.", 60, 392, 54, INK, 700, 0, cls="in") .replace('class="in"', 'class="in" style="--d:900"'))
    b.append(text("Software developer from Kyiv region.", 60, 462, 31, INK, 400, 0, cls="in").replace('class="in"', 'class="in" style="--d:1050"'))
    b.append(text("Web products, games and AI agents.", 60, 505, 31, SOFT, 400, 0, cls="in").replace('class="in"', 'class="in" style="--d:1150"'))
    # awards, the proof, at the second size
    b.append(text("Gold", 840, 178, 128, GROUND, 700, -0.02, cls="in").replace('class="in"', 'class="in" style="--d:1000"'))
    b.append(text("Infomatrix 2026", 842, 228, 32, GROUND, 700, cls="in").replace('class="in"', 'class="in" style="--d:1100"'))
    b.append(text("Software Development", 842, 266, 26, GROUND, 400, cls="in").replace('class="in"', 'class="in" style="--d:1100"'))
    b.append(text("Silver", 840, 434, 128, GROUND, 700, -0.02, cls="in").replace('class="in"', 'class="in" style="--d:1250"'))
    b.append(text("Genius Olympiad 2025", 842, 484, 32, GROUND, 700, cls="in").replace('class="in"', 'class="in" style="--d:1350"'))
    b.append(text("AI, 2nd place, national final", 842, 522, 24, GROUND, 400, cls="in").replace('class="in"', 'class="in" style="--d:1350"'))
    write("hero.svg", svg(W, H, "".join(b), "Norexel", "Norex, software developer from Kyiv region. Gold at Infomatrix 2026, silver at Genius Olympiad 2025."))


# ---------------------------------------------------------------- flight profile
def flight():
    W, H = 1200, 640
    pts = [
        ("First sites", "Mar 2025"),
        ("C++ apps", "Jun 2025"),
        ("AI silver", "Genius Olympiad"),
        ("KAI", "Enrolled 2025"),
        ("Software gold", "Infomatrix 2026"),
        ("Zalizna Zmina", "Web developer 2026"),
    ]
    x0, x1 = 110, 1090
    ybase, ytop = 560, 250
    xs = [x0 + i * (x1 - x0) / (len(pts) - 1) for i in range(len(pts))]
    # altitude climbs with each milestone (ordinal, not a measured scale)
    ys = [ybase - 40 - i * (ybase - 40 - ytop) / (len(pts) - 1) for i in range(len(pts))]
    b = [f'<rect width="{W}" height="{H}" fill="{GROUND}"/>']
    b.append(text("Flight profile", 60, 120, 76, INK, 700, -0.02, cls="in"))
    b.append(text("Every point is something shipped, built or won.", 62, 170, 30, SOFT, 400))
    area = f"M{xs[0]},{ybase} " + " ".join(f"L{x:.1f},{y:.1f}" for x, y in zip(xs, ys)) + f" L{xs[-1]},{ybase} Z"
    b.append(f'<path d="{area}" fill="{FIELD}"/>')
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    b.append(f'<path class="line" pathLength="1" d="{line}" fill="none" stroke="{ACCENT}" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>')
    for i, ((t, s), x, y) in enumerate(zip(pts, xs, ys)):
        d = 900 + i * 380
        b.append(f'<circle class="pt" style="--d:{d}" cx="{x:.1f}" cy="{y:.1f}" r="15" fill="{GROUND}" stroke="{ACCENT}" stroke-width="8"/>')
        tw = width(t, 28, 700)
        sw = width(s, 21, 400)
        lx = x - max(tw, sw) / 2
        lx = min(max(lx, 40), W - 40 - max(tw, sw))
        b.append(f'<g class="in" style="--d:{d + 150}">' + text(t, lx, y - 44 - 30, 28, INK, 700) + text(s, lx, y - 44, 21, SOFT, 400) + "</g>")
    write("flight.svg", svg(W, H, "".join(b), "Flight profile", "Six milestones from first websites in March 2025 to web developer at Zalizna Zmina in 2026."))


# ---------------------------------------------------------------- stack
def icon_path(name):
    raw = (ROOT / "tools" / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    vb = re.search(r'viewBox="([^"]+)"', raw).group(1).split()
    ds = re.findall(r'<path[^>]*\sd="([^"]+)"', raw)
    return float(vb[2]), ds


def stack():
    W, H = 1200, 520
    b = [f'<rect width="{W}" height="{H}" fill="{GROUND}"/>']
    b.append(text("Tools", 60, 120, 76, INK, 700, -0.02))
    items = [("C++", "cplusplus"), ("C#", "csharp"), ("JavaScript", "javascript"), ("HTML", "html5")]
    tx, ty, tw, th, gap = 60, 170, 255, 290, 12
    for i, (label, ic) in enumerate(items):
        x = tx + i * (tw + gap)
        b.append(f'<rect class="in" style="--d:{300 + i * 120}" x="{x}" y="{ty}" width="{tw}" height="{th}" fill="{FIELD}"/>')
        vw, ds = icon_path(ic)
        sc = 110 / vw
        paths = "".join(f'<path d="{d}"/>' for d in ds)
        b.append(f'<g class="in" style="--d:{400 + i * 120}" transform="translate({x + 32},{ty + 36}) scale({sc:.4f})" fill="{INK}">{paths}</g>')
        b.append(text(label, x + 32, ty + th - 36, 40, INK, 700, -0.01))
    ax = tx + 4 * (tw + gap)
    aw = W - 60 - ax
    b.append(f'<rect class="in" style="--d:900" x="{ax}" y="{ty}" width="{aw}" height="{th}" fill="{ACCENT}"/>')
    b.append(text("AI", ax + 28, ty + 150, 128, GROUND, 700, -0.03, cls="in").replace('class="in"', 'class="in" style="--d:1000"'))
    b.append(text("agents", ax + 28, ty + th - 36, 40, GROUND, 700, -0.01, cls="in").replace('class="in"', 'class="in" style="--d:1000"'))
    write("stack.svg", svg(W, H, "".join(b), "Tools", "C++, C#, JavaScript, HTML and AI agents."))


# ---------------------------------------------------------------- project tiles
def wrap(t, size, weight, maxw):
    words, lines, cur = t.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if width(trial, size, weight) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def tile(name, w, h, bg, fg, soft, title, body, tag, tsize):
    b = [f'<rect width="{w}" height="{h}" fill="{bg}"/>']
    tl = wrap(title, tsize, 700, w - 90)
    y = 32 + tsize
    for ln in tl:
        b.append(text(ln, 45, y, tsize, fg, 700, -0.02))
        y += tsize * 1.0
    y += 22
    for ln in wrap(body, 27, 400, w - 90):
        b.append(text(ln, 45, y, 27, fg, 400))
        y += 38
    b.append(text(tag, 45, h - 36, 24, soft, 700))
    write(name, svg(w, h, "".join(b), title, body))


def projects():
    # header
    b = [f'<rect width="1200" height="150" fill="{GROUND}"/>', text("Selected work", 60, 120, 76, INK, 700, -0.02)]
    write("projects-head.svg", svg(1200, 150, "".join(b), "Selected work"))
    tile("tile-zalizna.svg", 1200, 380, ACCENT, GROUND, GROUND,
         "Zalizna Zmina",
         "Web developer for a project that develops talented young people in Ukraine. I built its website, educational platform and help support service.",
         "ironsquad.org.ua", 96)
    tile("tile-launcher.svg", 600, 420, FIELD, INK, SOFT,
         "Hotkey Launcher",
         "A Windows desktop app in C++ that starts and stops programs from global hotkeys. WinAPI, GDI+, tray icon.",
         "C++  |  WinAPI", 56)
    tile("tile-algebra.svg", 600, 420, INK, GROUND, "#4A5056",
         "Algebra Platform",
         "A classroom server for algebra with sessions and progress tracking. Flask and MySQL, forked from MedanMv.",
         "Python  |  Flask  |  MySQL", 56)


# ---------------------------------------------------------------- footer
def footer():
    W, H = 1200, 420
    track = -0.02
    size = fit_size("NOREXEL", 1080, 700, track)
    b = [f'<rect width="{W}" height="{H}" fill="{ACCENT}"/>']
    b.append(text("NOREXEL", 60, 250, size, GROUND, 700, track, per_letter=True))
    b.append(text("Open to hackathons, internships and team projects.", 62, 335, 34, GROUND, 700))
    b.append(text("Kyiv Aviation Institute, 2025-2029", 62, 380, 27, GROUND, 400))
    write("footer.svg", svg(W, H, "".join(b), "Norexel", "Open to hackathons, internships and team projects."))


if __name__ == "__main__":
    hero(); flight(); stack(); projects(); footer()
