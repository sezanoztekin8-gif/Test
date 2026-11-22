"""Flat 2D characters and rooms for 'Bu Sefer Ezilmeyeceğim' (original designs). Returns SVG strings."""

INK = '#2b2233'
SKIN = {'zehra': '#f1c7a5', 'kenan': '#d9a882', 'nermin': '#eec3a2', 'ali': '#f4cfae'}

CAST = {
    'zehra': dict(h=880, hair='#5a3825', hair_style='long', top='#8fae8b', bottom='#e7dcc8', dress=False, female=True),
    'kenan': dict(h=960, hair='#1f1a1d', hair_style='short', top='#4a4f5a', bottom='#2c2f36', dress=False, female=False, beard=True),
    'nermin': dict(h=840, hair='#a9a5a2', hair_style='bun', top='#7d2f3d', bottom='#7d2f3d', dress=True, female=True, glasses=True),
    'ali': dict(h=560, hair='#6b4429', hair_style='kid', top='#f2c23b', bottom='#4c6ea8', dress=False, female=False),
}

BROWS = {  # (left inner y, left outer y) offsets; mirrored for the right brow
    'neutral': (0, 0), 'sad': (-8, 6), 'shock': (-14, -14), 'angry': (10, -6), 'calm': (-2, 2), 'smile': (-3, -3),
}


def face(cx, cy, r, who, expr, mid):
    c = CAST[who]
    ey = cy - r * 0.05
    ex = r * 0.38
    er = r * (0.17 if who == 'ali' else 0.14)
    eyes = ''
    for s in (-1, 1):
        x = cx + s * ex
        eyes += f'<ellipse cx="{x:.0f}" cy="{ey:.0f}" rx="{er * 1.05:.0f}" ry="{er * (1.25 if expr == "shock" else 1.0):.0f}" fill="#fff"/>'
        eyes += f'<circle cx="{x:.0f}" cy="{ey + 2:.0f}" r="{er * 0.62:.0f}" fill="{INK}"/>'
        eyes += f'<circle cx="{x + er * 0.25:.0f}" cy="{ey - er * 0.2:.0f}" r="{er * 0.2:.0f}" fill="#fff"/>'
        if c['female'] and who != 'ali':
            eyes += f'<path d="M{x - s * er * 0.2:.0f} {ey - er:.0f} l{s * er * 1.2:.0f} {-er * 0.5:.0f}" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
    bi, bo = BROWS[expr]
    brows = ''
    for s in (-1, 1):
        xi, xo = cx + s * ex * 0.45, cx + s * ex * 1.45
        by = ey - er * 2.1
        brows += f'<path d="M{xi:.0f} {by + bi:.0f} L{xo:.0f} {by + bo:.0f}" stroke="{c["hair"] if who != "nermin" else "#7a746f"}" stroke-width="{r * 0.07:.0f}" stroke-linecap="round"/>'
    my = cy + r * 0.48
    mw = r * 0.26
    if expr in ('smile', 'calm'):
        lip = f'<path d="M{cx - mw:.0f} {my - 4:.0f} Q{cx:.0f} {my + (16 if expr == "smile" else 9):.0f} {cx + mw:.0f} {my - 4:.0f}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    elif expr == 'sad':
        lip = f'<path d="M{cx - mw * 0.8:.0f} {my + 6:.0f} Q{cx:.0f} {my - 8:.0f} {cx + mw * 0.8:.0f} {my + 6:.0f}" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    elif expr == 'angry':
        lip = f'<path d="M{cx - mw:.0f} {my + 2:.0f} L{cx + mw:.0f} {my - 2:.0f}" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
    else:
        lip = f'<path d="M{cx - mw * 0.6:.0f} {my:.0f} L{cx + mw * 0.6:.0f} {my:.0f}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    mouth_ry = r * (0.16 if expr == 'shock' else 0.12)
    mouth = (f'<g class="lips">{lip}</g><ellipse class="mouth m-{who}{' open' if expr == 'shock' else ''}" id="{mid}" cx="{cx:.0f}" cy="{my + 4:.0f}" rx="{mw * 0.62:.0f}" '
             f'ry="{mouth_ry:.0f}" fill="#7a2f3a"/>')
    cheeks = ''
    if c['female'] or who == 'ali':
        for s in (-1, 1):
            cheeks += f'<ellipse cx="{cx + s * r * 0.55:.0f}" cy="{cy + r * 0.28:.0f}" rx="{r * 0.13:.0f}" ry="{r * 0.08:.0f}" fill="#e8908a" opacity="0.45"/>'
    extra = ''
    if c.get('beard'):
        extra += f'<ellipse cx="{cx:.0f}" cy="{cy + r * 0.62:.0f}" rx="{r * 0.62:.0f}" ry="{r * 0.36:.0f}" fill="#3a3033" opacity="0.14"/>'
        extra += f'<path d="M{cx - r * 0.3:.0f} {cy + r * 0.38:.0f} Q{cx:.0f} {cy + r * 0.26:.0f} {cx + r * 0.3:.0f} {cy + r * 0.38:.0f} Q{cx:.0f} {cy + r * 0.33:.0f} {cx - r * 0.3:.0f} {cy + r * 0.38:.0f}Z" fill="#2a2226"/>'
    if c.get('glasses'):
        for s in (-1, 1):
            extra += f'<circle cx="{cx + s * ex:.0f}" cy="{ey:.0f}" r="{er * 1.7:.0f}" fill="none" stroke="#5b4a3a" stroke-width="5"/>'
        extra += f'<path d="M{cx - ex + er * 1.7:.0f} {ey:.0f} L{cx + ex - er * 1.7:.0f} {ey:.0f}" stroke="#5b4a3a" stroke-width="5"/>'
    return eyes + brows + cheeks + extra + mouth


def hair_back(cx, cy, r, who):
    c = CAST[who]
    if c['hair_style'] == 'long':
        return f'<path d="M{cx - r * 1.15:.0f} {cy - r * 0.2:.0f} Q{cx - r * 1.35:.0f} {cy + r * 2.6:.0f} {cx - r * 0.7:.0f} {cy + r * 3.0:.0f} L{cx + r * 0.7:.0f} {cy + r * 3.0:.0f} Q{cx + r * 1.35:.0f} {cy + r * 2.6:.0f} {cx + r * 1.15:.0f} {cy - r * 0.2:.0f}Z" fill="{c["hair"]}"/>'
    if c['hair_style'] == 'bun':
        return f'<circle cx="{cx:.0f}" cy="{cy - r * 1.05:.0f}" r="{r * 0.45:.0f}" fill="{c["hair"]}"/>'
    return ''


def hair_front(cx, cy, r, who):
    c = CAST[who]
    col = c['hair']
    if c['hair_style'] == 'long':
        return f'<path d="M{cx - r * 1.08:.0f} {cy + r * 0.2:.0f} Q{cx - r * 1.1:.0f} {cy - r * 1.25:.0f} {cx:.0f} {cy - r * 1.12:.0f} Q{cx + r * 1.1:.0f} {cy - r * 1.25:.0f} {cx + r * 1.08:.0f} {cy + r * 0.2:.0f} Q{cx + r * 0.7:.0f} {cy - r * 0.55:.0f} {cx + r * 0.05:.0f} {cy - r * 0.62:.0f} Q{cx - r * 0.5:.0f} {cy - r * 0.35:.0f} {cx - r * 1.08:.0f} {cy + r * 0.2:.0f}Z" fill="{col}"/>'
    if c['hair_style'] == 'bun':
        return f'<path d="M{cx - r * 1.02:.0f} {cy - r * 0.05:.0f} Q{cx - r * 1.0:.0f} {cy - r * 1.15:.0f} {cx:.0f} {cy - r * 1.08:.0f} Q{cx + r * 1.0:.0f} {cy - r * 1.15:.0f} {cx + r * 1.02:.0f} {cy - r * 0.05:.0f} Q{cx:.0f} {cy - r * 0.7:.0f} {cx - r * 1.02:.0f} {cy - r * 0.05:.0f}Z" fill="{col}"/>'
    if c['hair_style'] == 'short':
        return f'<path d="M{cx - r * 1.02:.0f} {cy - r * 0.1:.0f} Q{cx - r * 1.05:.0f} {cy - r * 1.2:.0f} {cx:.0f} {cy - r * 1.12:.0f} Q{cx + r * 1.05:.0f} {cy - r * 1.2:.0f} {cx + r * 1.02:.0f} {cy - r * 0.1:.0f} L{cx + r * 0.9:.0f} {cy - r * 0.5:.0f} Q{cx:.0f} {cy - r * 0.75:.0f} {cx - r * 0.9:.0f} {cy - r * 0.5:.0f}Z" fill="{col}"/>'
    return f'<path d="M{cx - r * 1.05:.0f} {cy:.0f} Q{cx - r * 1.1:.0f} {cy - r * 1.25:.0f} {cx:.0f} {cy - r * 1.15:.0f} Q{cx + r * 1.1:.0f} {cy - r * 1.25:.0f} {cx + r * 1.05:.0f} {cy:.0f} Q{cx + r * 0.6:.0f} {cy - r * 0.45:.0f} {cx + r * 0.2:.0f} {cy - r * 0.55:.0f} Q{cx - r * 0.3:.0f} {cy - r * 0.35:.0f} {cx - r * 1.05:.0f} {cy:.0f}Z" fill="{col}"/>'


def person(who, cx, feet, expr='neutral', scale=1.0, mid=None, arms='down', pid=None):
    """Front-facing figure; feet = y of the soles. Returns an SVG <g> with id pid (for animation)."""
    c = CAST[who]
    h = c['h'] * scale
    r = h * (0.13 if who == 'ali' else 0.105)
    head_cy = feet - h + r
    neck_y = head_cy + r * 0.95
    sh_w = r * (1.25 if not c['female'] else 1.05) * (1.0 if who != 'ali' else 0.95)
    torso_h = h * 0.36
    hip_y = neck_y + torso_h
    skin = SKIN[who]
    g = [f'<g id="{pid}" class="who-{who}">'] if pid else ['<g>']
    g.append(hair_back(cx, head_cy, r, who))
    # legs
    leg_w = r * 0.42
    for s in (-1, 1):
        g.append(f'<rect x="{cx + s * r * 0.35 - leg_w / 2:.0f}" y="{hip_y - 10:.0f}" width="{leg_w:.0f}" height="{feet - hip_y - 6:.0f}" rx="{leg_w / 2:.0f}" fill="{c["bottom"] if not c["dress"] else skin}"/>')
        g.append(f'<ellipse cx="{cx + s * r * 0.42:.0f}" cy="{feet - 8:.0f}" rx="{leg_w * 0.85:.0f}" ry="{leg_w * 0.45:.0f}" fill="#3b3138"/>')
    # torso / dress
    if c['dress']:
        g.append(f'<path d="M{cx - sh_w:.0f} {neck_y + 10:.0f} Q{cx:.0f} {neck_y - 6:.0f} {cx + sh_w:.0f} {neck_y + 10:.0f} L{cx + sh_w * 1.25:.0f} {feet - h * 0.2:.0f} L{cx - sh_w * 1.25:.0f} {feet - h * 0.2:.0f}Z" fill="{c["top"]}"/>')
    else:
        g.append(f'<path d="M{cx - sh_w:.0f} {neck_y + 10:.0f} Q{cx:.0f} {neck_y - 6:.0f} {cx + sh_w:.0f} {neck_y + 10:.0f} L{cx + sh_w * 0.92:.0f} {hip_y:.0f} L{cx - sh_w * 0.92:.0f} {hip_y:.0f}Z" fill="{c["top"]}"/>')
        if c['female'] and who != 'ali':
            g.append(f'<path d="M{cx - sh_w * 0.95:.0f} {hip_y - 4:.0f} L{cx + sh_w * 0.95:.0f} {hip_y - 4:.0f} L{cx + sh_w * 1.15:.0f} {hip_y + torso_h * 0.75:.0f} L{cx - sh_w * 1.15:.0f} {hip_y + torso_h * 0.75:.0f}Z" fill="{c["bottom"]}"/>')
    # arms
    arm_w = r * 0.36
    for s in (-1, 1):
        ax = cx + s * (sh_w + arm_w * 0.1)
        if arms == 'cross':
            g.append(f'<rect x="{cx - sh_w * 0.85:.0f}" y="{neck_y + torso_h * 0.42 + (s + 1) * 12:.0f}" width="{sh_w * 1.7:.0f}" height="{arm_w:.0f}" rx="{arm_w / 2:.0f}" fill="{c["top"]}" stroke="{INK}" stroke-opacity="0.15" stroke-width="3"/>')
        elif arms == 'head' and s == -1:
            g.append(f'<path d="M{ax:.0f} {neck_y + 20:.0f} L{cx - r * 0.95:.0f} {head_cy - r * 0.2:.0f}" stroke="{c["top"]}" stroke-width="{arm_w:.0f}" stroke-linecap="round"/>')
            g.append(f'<circle cx="{cx - r * 0.95:.0f}" cy="{head_cy - r * 0.25:.0f}" r="{arm_w * 0.55:.0f}" fill="{skin}"/>')
        else:
            g.append(f'<rect x="{ax - arm_w / 2:.0f}" y="{neck_y + 12:.0f}" width="{arm_w:.0f}" height="{torso_h * 0.95:.0f}" rx="{arm_w / 2:.0f}" fill="{c["top"]}"/>')
            g.append(f'<circle cx="{ax:.0f}" cy="{neck_y + torso_h * 1.02:.0f}" r="{arm_w * 0.55:.0f}" fill="{skin}"/>')
    # neck + head
    g.append(f'<rect x="{cx - r * 0.22:.0f}" y="{head_cy + r * 0.7:.0f}" width="{r * 0.44:.0f}" height="{r * 0.45:.0f}" fill="{skin}"/>')
    g.append(f'<ellipse cx="{cx:.0f}" cy="{head_cy:.0f}" rx="{r * 0.95:.0f}" ry="{r:.0f}" fill="{skin}"/>')
    for s in (-1, 1):
        g.append(f'<ellipse cx="{cx + s * r * 0.95:.0f}" cy="{head_cy + r * 0.1:.0f}" rx="{r * 0.12:.0f}" ry="{r * 0.2:.0f}" fill="{skin}"/>')
    g.append(face(cx, head_cy, r, who, expr, mid or f'm-{pid}'))
    g.append(hair_front(cx, head_cy, r, who))
    g.append('</g>')
    return ''.join(g)


# ------------------------------------------------------------------ rooms (1080 x 1920)
def wall(col, floor='#b88a63', floor_y=1420, paper=None):
    s = f'<rect width="1080" height="1920" fill="{col}"/>'
    if paper:
        for x in range(0, 1080, 90):
            for y in range(0, floor_y, 120):
                s += f'<circle cx="{x + (45 if (y // 120) % 2 else 0)}" cy="{y + 60}" r="6" fill="{paper}"/>'
    s += f'<rect y="{floor_y}" width="1080" height="{1920 - floor_y}" fill="{floor}"/>'
    s += f'<rect y="{floor_y - 18}" width="1080" height="18" fill="#00000022"/>'
    return s


def window(x, y, w, h, sky='#cfe6f5', night=False):
    s = f'<rect x="{x - 14}" y="{y - 14}" width="{w + 28}" height="{h + 28}" rx="10" fill="#f6efe2"/>'
    s += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{"#1d2b4a" if night else sky}"/>'
    if night:
        for i in range(14):
            s += f'<rect x="{x + 20 + (i * 47) % (w - 40)}" y="{y + h - 60 - (i * 37) % 160}" width="16" height="22" fill="#f6d36b" opacity="0.8"/>'
        s += f'<circle cx="{x + w - 70}" cy="{y + 70}" r="34" fill="#f4ecd0"/>'
    else:
        s += f'<circle cx="{x + 80}" cy="{y + 80}" r="42" fill="#fff6cf"/>'
    s += f'<rect x="{x + w / 2 - 6}" y="{y}" width="12" height="{h}" fill="#f6efe2"/><rect x="{x}" y="{y + h / 2 - 6}" width="{w}" height="12" fill="#f6efe2"/>'
    s += f'<path d="M{x - 30} {y - 30} Q{x + 40} {y + h * 0.6} {x - 10} {y + h + 40} L{x - 70} {y + h + 40} L{x - 70} {y - 30}Z" fill="#c8746a"/>'
    s += f'<path d="M{x + w + 30} {y - 30} Q{x + w - 40} {y + h * 0.6} {x + w + 10} {y + h + 40} L{x + w + 70} {y + h + 40} L{x + w + 70} {y - 30}Z" fill="#c8746a"/>'
    return s


def frame_pic(x, y, w, h, inner='#9cb8a0'):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#7a5a3d"/><rect x="{x + 14}" y="{y + 14}" width="{w - 28}" height="{h - 28}" fill="{inner}"/><path d="M{x + 14} {y + h - 14} L{x + w * 0.4} {y + h * 0.45} L{x + w * 0.65} {y + h * 0.7} L{x + w - 14} {y + h * 0.35} L{x + w - 14} {y + h - 14}Z" fill="#6f8f74"/>'


def table(y=1180, col='#8a5a3b'):
    return (f'<rect x="60" y="{y}" width="960" height="40" rx="12" fill="{col}"/>'
            f'<rect x="80" y="{y + 40}" width="920" height="300" fill="#f4ede1"/>'
            f'<path d="M80 {y + 40} L1000 {y + 40} L1000 {y + 120} Q540 {y + 160} 80 {y + 120}Z" fill="#e5dccb"/>'
            f'<rect x="110" y="{y + 340}" width="34" height="300" fill="{col}"/><rect x="936" y="{y + 340}" width="34" height="300" fill="{col}"/>')


def breakfast(y=1180):
    s = ''
    for x in (250, 540, 830):
        s += f'<ellipse cx="{x}" cy="{y - 6}" rx="80" ry="18" fill="#fff" stroke="#d7cfc0" stroke-width="4"/>'
    s += f'<path d="M500 {y - 70} L520 {y - 8} L560 {y - 8} L580 {y - 70}Z" fill="#c8e1ea" opacity="0.8"/><rect x="505" y="{y - 52}" width="70" height="40" fill="#b5532f" opacity="0.8"/>'
    s += f'<ellipse cx="380" cy="{y - 14}" rx="40" ry="12" fill="#f2c94c"/><ellipse cx="690" cy="{y - 16}" rx="55" ry="14" fill="#e0a85e"/>'
    return s


def bed(x, y, w=760, night=False):
    blanket = '#6c7bb0' if night else '#a7b7d9'
    return (f'<rect x="{x}" y="{y - 260}" width="{w}" height="300" rx="30" fill="#7a5a3d"/>'
            f'<rect x="{x + 20}" y="{y - 40}" width="{w - 40}" height="140" rx="20" fill="#f3efe7"/>'
            f'<rect x="{x + 10}" y="{y + 40}" width="{w - 20}" height="200" rx="26" fill="{blanket}"/>'
            f'<rect x="{x}" y="{y + 230}" width="{w}" height="60" rx="10" fill="#6a4c33"/>')


def mirror_room():
    s = wall('#cfe3e0', floor='#e9e4da', floor_y=1700)
    for x in range(0, 1080, 120):
        for y in range(1000, 1700, 120):
            s += f'<rect x="{x + 4}" y="{y + 4}" width="112" height="112" fill="#bcd6d2"/>'
    s += '<rect x="170" y="160" width="740" height="980" rx="370" fill="#a98b62"/><rect x="200" y="190" width="680" height="920" rx="340" fill="#e4f1f3"/>'
    s += '<rect x="120" y="1180" width="840" height="60" rx="14" fill="#f7f7f5"/><ellipse cx="540" cy="1210" rx="210" ry="26" fill="#d8e4e6"/>'
    return s


def diary_page():
    s = '<rect width="1080" height="1920" fill="#1d1a22"/>'
    s += '<ellipse cx="540" cy="900" rx="620" ry="760" fill="#3a3027" opacity="0.9"/>'
    s += '<rect x="130" y="520" width="820" height="980" rx="14" fill="#f4ead2" transform="rotate(-3 540 1010)"/>'
    s += '<rect x="520" y="520" width="10" height="980" fill="#d9cbaa" transform="rotate(-3 540 1010)"/>'
    for i in range(14):
        s += f'<line x1="170" y1="{620 + i * 60}" x2="910" y2="{620 + i * 60}" stroke="#c9d6e6" stroke-width="3" transform="rotate(-3 540 1010)"/>'
    s += '<circle cx="900" cy="260" r="160" fill="#f6d36b" opacity="0.18"/>'
    return s
