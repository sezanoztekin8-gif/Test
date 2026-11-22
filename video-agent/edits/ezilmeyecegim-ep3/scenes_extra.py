"""Extra locations for the series: street, bank lobby, night balcony. Returns SVG strings (1080x1920)."""
from art import wall, window


def street():
    s = '<rect width="1080" height="1920" fill="#bfe3f2"/><circle cx="880" cy="260" r="80" fill="#fff3c4"/>'
    s += '<rect x="0" y="180" width="360" height="1240" fill="#d8b49a"/><rect x="720" y="150" width="360" height="1270" fill="#c9a88e"/>'
    for y in (260, 460, 660):
        for x in (40, 180, 760, 900):
            s += f'<rect x="{x}" y="{y}" width="110" height="130" rx="6" fill="#7fb3c9"/><rect x="{x + 52}" y="{y}" width="6" height="130" fill="#f6efe2"/>'
    s += '<rect x="380" y="560" width="300" height="110" rx="10" fill="#2e6f8e"/>'
    s += '<rect x="400" y="590" width="260" height="50" rx="8" fill="#ffffff" opacity="0.85"/>'
    s += '<rect y="1420" width="1080" height="500" fill="#7a7f88"/><rect y="1380" width="1080" height="60" fill="#b9b2a6"/>'
    s += '<rect y="1690" width="1080" height="8" fill="#f0e08a"/>'
    return s


def bank():
    s = wall('#e8eef2', floor='#c9d3da', floor_y=1420)
    for x in range(0, 1080, 120):
        s += f'<rect x="{x}" y="1420" width="2" height="500" fill="#b1bcc5"/>'
    s += '<rect x="80" y="240" width="920" height="70" rx="10" fill="#2e5d7a"/>'
    for i in range(3):
        s += f'<rect x="{200 + i * 300}" y="110" width="160" height="16" rx="8" fill="#fffbe6"/>'
    s += '<rect x="120" y="980" width="840" height="60" rx="12" fill="#8b6f57"/><rect x="120" y="1040" width="840" height="380" fill="#b9a18a"/>'
    s += '<rect x="820" y="420" width="170" height="120" rx="10" fill="#ffffff"/><rect x="840" y="450" width="130" height="14" fill="#9aa8b6"/>'
    return s


def balcony():
    s = '<rect width="1080" height="1920" fill="#141b2e"/>'
    for k in range(60):
        s += f'<circle cx="{(k * 131) % 1080}" cy="{(k * 57) % 700}" r="2" fill="#ffffff" opacity="0.6"/>'
    for k in range(10):
        x, h = k * 110, 300 + ((k * 73) % 400)
        s += f'<rect x="{x}" y="{1000 - h}" width="100" height="{h}" fill="#1f2a44"/>'
        for wy in range(1000 - h + 30, 980, 70):
            s += f'<rect x="{x + 20}" y="{wy}" width="16" height="22" fill="#f6d36b" opacity="0.8"/>'
    s += '<rect y="1300" width="1080" height="620" fill="#2b2b3a"/><rect y="1220" width="1080" height="18" fill="#6c6c7c"/>'
    for x in range(0, 1080, 90):
        s += f'<rect x="{x}" y="1238" width="8" height="82" fill="#6c6c7c"/>'
    return s
