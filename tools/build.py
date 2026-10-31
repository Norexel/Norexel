"""Builds the profile SVGs. Text is converted to outlines (Bahnschrift) so it renders
identically on GitHub, which cannot load web fonts inside an <img>.

Run: python tools/build.py   (needs: pip install fonttools; uses the Bahnschrift font that ships with Windows)

House rules kept from the design brief: no gradients, shadows, thin rules, monospace, emoji,
eyebrows or index numbers. One accent colour. Sharp corners. Motion only where it carries meaning.
"""
import re
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).parent.parent
OUT = ROOT / "assets"
FONT = "C:/Windows/Fonts/bahnschrift.ttf"

GROUND = "#101214"
FIELD = "#1A1E22"
FIELD2 = "#232930"
FIELD3 = "#2D343B"
INK = "#F2F3F0"
SOFT = "#A9AFB5"
DARK_SOFT = "#4A5056"
ACCENT = "#FF5A1F"
ACCENT_DEEP = "#EC4C12"

_fonts = {}


def font(weight):
    if weight not in _fonts:
        f = TTFont(FONT)
        _fonts[weight] = instancer.instantiateVariableFont(f, {"wght": weight, "wdth": 100})
    return _fonts[weight]


def _n(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def glyph(ch, size, x, y, weight):
    f = font(weight)
    cmap = f.getBestCmap()
    if ord(ch) not in cmap:
        raise ValueError(f"font has no glyph for {ch!r}")
    gs = f.getGlyphSet()
    name = cmap[ord(ch)]
    s = size / f["head"].unitsPerEm
    pen = SVGPathPen(gs, ntos=_n)
    gs[name].draw(TransformPen(pen, (s, 0, 0, -s, x, y)))
    return pen.getCommands(), gs[name].width * s


def width(t, size, weight, track=0.0):
    w = 0.0
    for ch in t:
        w += glyph(ch, size, 0, 0, weight)[1] + track * size
    return w - track * size


def text(t, x, y, size, fill, weight=700, track=0.0, per_letter=False):
    """Outlined text. per_letter=True returns one <path> per letter, staggered by --i."""
    parts, cx = [], x
    for ch in t:
        if ch == " ":
            cx += glyph("n", size, 0, 0, weight)[1] * 0.55 + track * size
            continue
        d, adv = glyph(ch, size, cx, y, weight)
        parts.append(d)
        cx += adv + track * size
    if per_letter:
        return "".join(f'<path class="l" style="--i:{i}" fill="{fill}" d="{d}"/>' for i, d in enumerate(parts))
    return f'<path fill="{fill}" d="{"".join(parts)}"/>'


def reveal(content, d):
    return f'<g class="in" style="--d:{d}">{content}</g>'


def fit_size(t, target_w, weight, track):
    return target_w / (width(t, 100, weight, track) / 100)


def fit_line(t, maxw, top, weight):
    """Largest size <= top at which the one-line text fits maxw."""
    s = top
    while width(t, s, weight) > maxw:
        s -= 1
    return s


def wrap(t, size, weight, maxw):
    lines, cur = [], ""
    for w in t.split():
        trial = (cur + " " + w).strip()
        if width(trial, size, weight) <= maxw:
            cur = trial
        else:
            if not cur:
                raise ValueError(f"word {w!r} does not fit {maxw}px at {size}px")
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def fit_wrap(t, maxw, sizes, weight):
    """Largest size from `sizes` (descending) whose longest word fits, and its lines."""
    for s in sizes:
        try:
            return s, wrap(t, s, weight, maxw)
        except ValueError:
            continue
    raise ValueError(f"cannot fit {t!r} in {maxw}px")


def para(t, x, y, size, fill, weight, maxw, lh):
    """Wrapped paragraph; returns (svg, baseline of the last line)."""
    ls = wrap(t, size, weight, maxw)
    out = "".join(text(l, x, y + i * lh, size, fill, weight) for i, l in enumerate(ls))
    return out, y + (len(ls) - 1) * lh


CSS = """
@keyframes rise{from{transform:translateY(70px);opacity:0}}
@keyframes fade{from{opacity:0}}
@keyframes lift{from{transform:translateY(28px);opacity:0}}
@keyframes grow{from{transform:scaleY(0)}}
@keyframes pop{from{transform:scale(0);opacity:0}}
@keyframes ping{0%{transform:scale(1);opacity:.9}100%{transform:scale(2.8);opacity:0}}
.l{animation:rise 1s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--i)*70ms + 150ms)}
.in{animation:fade .8s ease-out both;animation-delay:calc(var(--d,0)*1ms)}
.up{animation:lift .9s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--d,0)*1ms)}
.grow{transform-box:fill-box;transform-origin:50% 100%;animation:grow .9s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--d,0)*1ms)}
.pt{transform-box:fill-box;transform-origin:center;animation:pop .5s cubic-bezier(.16,1,.3,1) both;animation-delay:calc(var(--d,0)*1ms)}
.ring{transform-box:fill-box;transform-origin:center;opacity:0;animation:ping 2.4s ease-out infinite;animation-delay:7.4s}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def svg(w, h, body, title, desc="", extra_css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img">'
        f"<title>{title}</title><desc>{desc}</desc><style>{CSS}{extra_css}</style>{body}</svg>"
    )


def write(name, s):
    (OUT / name).write_text(s, encoding="utf-8")
    print("wrote", name, len(s) // 1024, "KB")


def rect(x, y, w, h, fill, cls="", d=None):
    c = f' class="{cls}"' if cls else ""
    st = f' style="--d:{d}"' if d is not None else ""
    return f'<rect{c}{st} x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>'


# ---------------------------------------------------------------- hero
def hero():
    W, H, PH = 1200, 640, 560
    track = -0.02
    size = fit_size("NOREXEL", 700, 700, track)
    b = [rect(0, 0, W, H, GROUND), rect(800, 0, 400, PH, ACCENT, "grow", 150)]
    b.append(text("NOREXEL", 56, 240, size, INK, 700, track, per_letter=True))
    b.append(reveal(text("I am Norex.", 60, 330, 54, INK, 700), 900))
    b.append(reveal(text("Software developer from Kyiv region.", 60, 402, 31, INK, 400), 1050))
    b.append(reveal(text("Web products, games and AI agents.", 60, 445, 31, SOFT, 400), 1150))

    px, pw = 840, 320
    b.append(reveal(text("Gold", px, 150, 120, GROUND, 700, -0.02), 1000))
    s1 = fit_line("Infomatrix 2026", pw, 30, 700)
    b.append(reveal(text("Infomatrix 2026", px + 2, 196, s1, GROUND, 700) + text("Software, my own app", px + 2, 230, 24, GROUND, 400), 1100))
    b.append(reveal(text("Silver", px, 350, 120, GROUND, 700, -0.02), 1250))
    s2 = fit_line("Genius Olympiad 2025", pw, 30, 700)
    b.append(reveal(text("Genius Olympiad 2025", px + 2, 396, s2, GROUND, 700) + text("2nd place in Ukraine", px + 2, 430, 24, GROUND, 400), 1350))
    extra, _ = para("Also silver at the Infomatrix 2025 hackathon and a world finalist.", px + 2, 484, 22, GROUND, 400, pw, 29)
    b.append(reveal(extra, 1450))

    # one marquee on the page: the skills, which need no individual attention
    items = ["Software development", "C++", "C#", "Python", "JavaScript", "HTML/CSS", "SQL", "AI agents", "API integration", "System design"]
    gap, x, parts = 40, 0, []
    for it in items:
        parts.append(text(it, x, PH + 52, 30, INK, 700))
        x += width(it, 30, 700) + gap
        parts.append(rect(round(x, 1), PH + 35, 12, 12, ACCENT))
        x += 12 + gap
    wc = round(x, 1)
    band = rect(0, PH, W, H - PH, FIELD)
    copy = "".join(parts)
    css = f"@keyframes marq{{to{{transform:translateX({-wc}px)}}}}.marqwrap{{animation:marq 40s linear infinite}}"
    marq = f'<g transform="translate(60,0)"><g class="marqwrap"><g>{copy}</g><g transform="translate({wc},0)">{copy}</g></g></g>'
    b.append(band + marq)
    write("hero.svg", svg(W, H, "".join(b), "Norexel",
                          "Norex, software developer from Kyiv region. Gold at Infomatrix 2026, silver at Genius Olympiad 2025, silver at the Infomatrix 2025 hackathon.", css))


# ---------------------------------------------------------------- about
def about():
    W = 1200
    b = [text("About", 60, 120, 76, INK, 700, -0.02)]
    stm, last = para("Two years in web, app and game development. I turn ideas into practical digital solutions and I am drawn to automation, robotics and AI.",
                     62, 195, 36, INK, 400, 1080, 52)
    b.append(reveal(stm, 300))
    cards = [
        (FIELD2, INK, SOFT, "Studying", "Kyiv Aviation Institute. Automation, Computer-Integrated Technologies and Robotics.", "Since September 2026"),
        (FIELD2, INK, SOFT, "Competing", "Infomatrix and Genius Olympiad, with the Small Academy of Sciences of Ukraine.", "2025 and 2026"),
        (ACCENT, GROUND, GROUND, "Working", "Web and product developer at Zalizna Zmina. Websites, apps and AI agents for workflows.", "Now"),
    ]
    cw, gap, cy, ch = 352, 12, last + 64, 330
    for i, (bg, fg, sf, t, body, tag) in enumerate(cards):
        x = 60 + i * (cw + gap)
        g = [rect(x, cy, cw, ch, bg), text(t, x + 28, cy + 74, 44, fg, 700, -0.01)]
        pp, _ = para(body, x + 28, cy + 134, 24, fg, 400, cw - 56, 33)
        g.append(pp)
        g.append(text(tag, x + 28, cy + ch - 28, 22, sf, 700))
        b.append(f'<g class="up" style="--d:{500 + i * 150}">' + "".join(g) + "</g>")
    H = cy + ch + 50
    b.insert(0, rect(0, 0, W, H, GROUND))
    write("about.svg", svg(W, H, "".join(b), "About", "Studying at Kyiv Aviation Institute, competing in olympiads, working as web developer at Zalizna Zmina."))


# ---------------------------------------------------------------- career ladder
def ladder():
    W, H = 1200, 880
    gap = 8
    sw = (W - 5 * gap) / 6
    heights = [300, 360, 420, 480, 540, 600]
    steps = [
        ("Mar 2025", "Silver", "Infomatrix 2025, Ukraine hackathon.", FIELD2, INK, SOFT),
        ("Jun 2025", "World final", "Infomatrix 2025 in Romania. International finalist.", FIELD2, INK, SOFT),
        ("2025", "2nd place", "Genius Olympiad, national stage. I built my own ecological AI.", FIELD2, INK, SOFT),
        ("Mar 2026", "Gold", "Infomatrix 2026, Software. I built my own app.", INK, GROUND, DARK_SOFT),
        ("Sep 2026", "KAI", "Enrolled at the Kyiv Aviation Institute.", FIELD2, INK, SOFT),
        ("Now", "Zalizna Zmina", "Building apps, websites and more.", ACCENT, GROUND, GROUND),
    ]
    b = [rect(0, 0, W, H, GROUND), text("Career ladder", 60, 120, 76, INK, 700, -0.02)]
    b.append(reveal(text("Each step is something won, built or started.", 62, 170, 30, SOFT, 400), 300))
    pts = []
    for i, ((date, title, detail, bg, fg, soft), hgt) in enumerate(zip(steps, heights)):
        x = i * (sw + gap)
        top = H - hgt
        d0 = 200 + i * 260
        b.append(rect(round(x, 1), top, round(sw, 1), hgt, bg, "grow", d0))
        pad = 22
        inner = sw - 2 * pad
        ts, tl = fit_wrap(title, inner, [32, 30, 28, 26, 24], 700)
        g = [text(date, x + pad, top + 54, 36, soft, 700, -0.01)]
        y = top + 54 + 12 + ts
        for ln in tl:
            g.append(text(ln, x + pad, y, ts, fg, 700))
            y += ts + 4
        y += 12
        dl = wrap(detail, 22, 400, inner)
        for ln in dl:
            g.append(text(ln, x + pad, y, 22, fg, 400))
            y += 30
        assert y < H - 14, f"step {i} text overflows"
        b.append(f'<g class="in" style="--d:{d0 + 450}">' + "".join(g) + "</g>")
        pts.append((x + sw / 2, top - 40))
    # the marker climbs the ladder and rests above the last step
    fx, fy = pts[-1]
    rel = [(px - fx, py - fy) for px, py in pts]
    path = f"M{_n(rel[0][0])},{_n(rel[0][1])}"
    for (ax, ay), (bx, by) in zip(rel, rel[1:]):
        path += f" Q{_n((ax + bx) / 2)},{_n(min(ay, by) - 64)} {_n(bx)},{_n(by)}"
    b.append(f'<circle class="ring" cx="{_n(fx)}" cy="{_n(fy)}" r="17" fill="none" stroke="{ACCENT}" stroke-width="5"/>')
    b.append(
        f'<circle r="17" fill="{ACCENT}" opacity="0" transform="translate({_n(fx)},{_n(fy)})">'
        f'<set attributeName="opacity" to="1" begin="2.4s" fill="freeze"/>'
        f'<animateMotion dur="5s" begin="2.4s" fill="freeze" path="{path}"/></circle>'
    )
    write("ladder.svg", svg(W, H, "".join(b), "Career ladder",
                            "Silver at the Infomatrix 2025 hackathon in March 2025, world final in June 2025, second place at Genius Olympiad with my own ecological AI, gold at Infomatrix in March 2026 with my own app, Kyiv Aviation Institute in September 2026, now building apps and websites at Zalizna Zmina."))


# ---------------------------------------------------------------- skills
def icon(name):
    raw = (ROOT / "tools" / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    vb = float(re.search(r'viewBox="([^"]+)"', raw).group(1).split()[2])
    return vb, re.findall(r'<path[^>]*\sd="([^"]+)"', raw)


def icon_g(name, x, y, px, fill):
    vb, ds = icon(name)
    return f'<g transform="translate({x},{y}) scale({px / vb:.4f})" fill="{fill}">' + "".join(f'<path d="{d}"/>' for d in ds) + "</g>"


def skills():
    W, H = 1200, 900
    b = [rect(0, 0, W, H, GROUND), text("Skills", 60, 170, 76, INK, 700, -0.02)]
    gap = 12
    inner = W - 120
    # row 1: four languages
    w1, h1, y1 = (inner - 3 * gap) / 4, 230, 220
    row1 = [("C", ["c"]), ("C++", ["cplusplus"]), ("C#", ["csharp"]), ("Python", ["python"])]
    # row 2: three, wider
    w2, h2, y2 = (inner - 2 * gap) / 3, 200, y1 + h1 + gap
    row2 = [("JavaScript", ["javascript"]), ("HTML/CSS", ["html5", "css3"]), ("SQL", None)]
    # row 3: four text tiles
    h3, y3 = 250, y2 + h2 + gap
    row3 = [
        ("Software development", "Web, desktop and game products, from idea to release.", FIELD3, INK),
        ("AI agents", "Agents that automate tasks and improve workflows.", ACCENT, GROUND),
        ("API integration", "Connecting services and data into one working product.", FIELD3, INK),
        ("System design", "Planning how the parts of a product fit together.", FIELD3, INK),
    ]
    k = 0
    for i, (label, ics) in enumerate(row1):
        x = 60 + i * (w1 + gap)
        g = [rect(round(x, 1), y1, round(w1, 1), h1, FIELD2), icon_g(ics[0], round(x + 28, 1), y1 + 28, 84, INK), text(label, x + 28, y1 + h1 - 28, 42, INK, 700, -0.01)]
        b.append(f'<g class="up" style="--d:{300 + k * 90}">' + "".join(g) + "</g>"); k += 1
    for i, (label, ics) in enumerate(row2):
        x = 60 + i * (w2 + gap)
        g = [rect(round(x, 1), y2, round(w2, 1), h2, FIELD2)]
        if ics:
            for j, ic in enumerate(ics):
                g.append(icon_g(ic, round(x + 28 + j * 100, 1), y2 + 28, 76, INK))
        else:
            g.append(text("SQL", x + 24, y2 + 100, 96, INK, 700, -0.03))
            label = "Databases and queries"
        g.append(text(label, x + 28, y2 + h2 - 28, 42 if ics else 30, INK if ics else SOFT, 700, -0.01))
        b.append(f'<g class="up" style="--d:{300 + k * 90}">' + "".join(g) + "</g>"); k += 1
    for i, (title, body, bg, fg) in enumerate(row3):
        x = 60 + i * (w1 + gap)
        ts, tl = fit_wrap(title, w1 - 56, [34, 32, 30, 28, 26], 700)
        g = [rect(round(x, 1), y3, round(w1, 1), h3, bg)]
        y = y3 + 28 + ts
        for ln in tl:
            g.append(text(ln, x + 28, y, ts, fg, 700, -0.01)); y += ts + 4
        pp, _ = para(body, x + 28, y + 22, 22, fg, 400, w1 - 56, 30)
        g.append(pp)
        b.append(f'<g class="up" style="--d:{300 + k * 90}">' + "".join(g) + "</g>"); k += 1
    H = int(y3 + h3 + 40)
    b[0] = rect(0, 0, W, H, GROUND)
    write("skills.svg", svg(W, H, "".join(b), "Skills", "C, C++, C#, Python, JavaScript, HTML and CSS, SQL, software development, AI agents, API integration, system design."))


# ---------------------------------------------------------------- selected work
def tile(name, w, h, bg, fg, soft, title, body, tag, tsize, extra=""):
    b = [f'<clipPath id="c"><rect width="{w}" height="{h}"/></clipPath>', rect(0, 0, w, h, bg)]
    if extra:
        b.append(f'<g clip-path="url(#c)">{extra}</g>')
    ts, tl = fit_wrap(title, w - 90 if not extra else w - 90, [tsize, tsize - 8, tsize - 16, tsize - 24], 700)
    y = 36 + ts
    for ln in tl:
        b.append(text(ln, 45, y, ts, fg, 700, -0.02))
        y += ts
    body_w = (w - 90) if not extra else 440
    pp, last = para(body, 45, y + 24, 26, fg, 400, body_w, 36)
    b.append(pp)
    b.append(text(tag, 45, h - 38, 24, soft, 700))
    assert last < h - 80, f"{name}: body overflows ({last} vs {h})"
    body_svg = "".join(b)
    write(name, svg(w, h, f'<g class="up" style="--d:100">{body_svg}</g>', title, body))


def work():
    b = [rect(0, 0, 1200, 150, GROUND), text("Selected work", 60, 120, 76, INK, 700, -0.02)]
    write("work-head.svg", svg(1200, 150, "".join(b), "Selected work"))
    giant = text("Z", 545, 560, 520, ACCENT_DEEP, 700)
    tile("tile-zalizna.svg", 800, 480, ACCENT, GROUND, GROUND, "Zalizna Zmina",
         "Web and product developer for a project that supports talented young people in Ukraine: its website, educational platform and help support.",
         "ironsquad.org.ua", 96, giant)
    tile("tile-eco.svg", 400, 480, FIELD2, INK, SOFT, "Ecological AI",
         "My own AI project for the Genius Olympiad. 2nd place in Ukraine.", "Genius Olympiad 2025", 60)
    tile("tile-infomatrix.svg", 400, 420, INK, GROUND, DARK_SOFT, "Infomatrix 2026 app",
         "The app I built for the Software category. Gold medal.", "Infomatrix 2026", 56)
    tile("tile-launcher.svg", 400, 420, FIELD2, INK, SOFT, "Hotkey Launcher",
         "A Windows app in C++ that starts and stops programs from global hotkeys.", "C++  /  WinAPI", 56)
    tile("tile-algebra.svg", 400, 420, FIELD3, INK, SOFT, "Algebra Platform",
         "A classroom server for algebra with classes and sessions. Fork of a Flask and MySQL project.", "Fork  /  Python", 56)


# ---------------------------------------------------------------- footer
def footer():
    W, H = 1200, 560
    track = -0.02
    size = fit_size("NOREXEL", 1080, 700, track)
    tops = [200, 160, 120, 80, 40, 0]
    sw = W / 6
    b = [rect(0, 0, W, H, GROUND)]
    for i, t in enumerate(tops):
        extra = 4 if i < len(tops) - 1 else 0
        b.append(rect(round(i * sw, 1), t, round(sw + extra, 1), H - t, ACCENT, "grow", 100 + i * 140))
    b.append(text("NOREXEL", 60, 410, size, GROUND, 700, track, per_letter=True))
    b.append(reveal(text("Open to hackathons, internships and team projects.", 62, 482, 34, GROUND, 700), 1000))
    b.append(reveal(text("Kyiv Aviation Institute, since September 2026", 62, 526, 27, GROUND, 400), 1100))
    write("footer.svg", svg(W, H, "".join(b), "Norexel", "Open to hackathons, internships and team projects."))


# ---------------------------------------------------------------- link buttons
def button(name, label, bg, fg):
    w = int(width(label, 28, 700)) + 72
    b = rect(0, 0, w, 64, bg) + text(label, 36, 42, 28, fg, 700)
    write(name, svg(w, 64, b, label))


def buttons():
    button("btn-linkedin.svg", "LinkedIn", ACCENT, GROUND)
    button("btn-zalizna.svg", "Zalizna Zmina", FIELD3, INK)
    button("btn-projects.svg", "Projects", FIELD3, INK)


if __name__ == "__main__":
    hero(); about(); ladder(); skills(); work(); footer(); buttons()
