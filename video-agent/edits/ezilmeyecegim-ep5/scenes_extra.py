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


def park():
    s = '<rect width="1080" height="1920" fill="#cfeedd"/><circle cx="860" cy="240" r="90" fill="#fff6c9"/>'
    for x, h in [(60, 420), (300, 500), (640, 460), (900, 380)]:
        s += f'<rect x="{x + 40}" y="{1420 - h}" width="28" height="{h}" fill="#7a5a3d"/>'
        s += f'<circle cx="{x + 54}" cy="{1420 - h}" r="150" fill="#6fb37a"/><circle cx="{x + 10}" cy="{1460 - h}" r="100" fill="#5da56b"/>'
    s += '<rect y="1420" width="1080" height="500" fill="#8fc98f"/><rect y="1400" width="1080" height="30" fill="#c9b79c"/>'
    s += '<rect x="330" y="1290" width="420" height="26" rx="8" fill="#9b6b4a"/><rect x="350" y="1316" width="20" height="110" fill="#6b4a33"/><rect x="710" y="1316" width="20" height="110" fill="#6b4a33"/>'
    return s


def car():
    s = '<rect width="1080" height="1920" fill="#2a2f3a"/>'
    s += '<rect x="90" y="260" width="900" height="760" rx="90" fill="#8fb8cf"/>'
    s += '<rect x="120" y="290" width="840" height="700" rx="70" fill="#a9cfe0" opacity="0.7"/>'
    s += '<rect x="0" y="1020" width="1080" height="900" fill="#3c4150"/><rect x="0" y="1000" width="1080" height="60" rx="20" fill="#50586a"/>'
    s += '<rect x="170" y="1120" width="740" height="220" rx="50" fill="#5b6378"/>'
    for x in (110, 880):
        s += f'<circle cx="{x}" cy="1560" r="8" fill="#e8e8e8"/>'
    s += '<rect x="250" y="1040" width="580" height="50" rx="12" fill="#2b303c"/>'
    return s


def office():
    s = '<rect width="1080" height="1920" fill="#efe6d6"/>'
    for y in range(120, 900, 150):
        s += f'<rect x="60" y="{y}" width="960" height="120" fill="#8c6d4f"/>'
        for x in range(90, 1000, 90):
            s += f'<rect x="{x}" y="{y + 10}" width="60" height="90" fill="#d9c4a0" opacity="0.85"/>'
    s += '<rect y="1420" width="1080" height="500" fill="#a48364"/>'
    s += '<rect x="180" y="1220" width="720" height="60" rx="12" fill="#6b4a33"/><rect x="200" y="1280" width="680" height="160" fill="#5a3d2a"/>'
    s += '<rect x="450" y="1080" width="180" height="140" rx="6" fill="#ffffff"/><rect x="470" y="1110" width="140" height="10" fill="#9aa8b6"/><rect x="470" y="1135" width="120" height="10" fill="#9aa8b6"/>'
    return s


def market():
    s = '<rect width="1080" height="1920" fill="#f6e7c8"/>'
    for x in range(0, 1080, 120):
        col = '#d9534f' if (x // 120) % 2 else '#fff7e8'
        s += f'<rect x="{x}" y="160" width="120" height="200" fill="{col}"/>'
    s += '<rect x="380" y="430" width="320" height="90" rx="14" fill="#2e7a5c"/>'
    s += '<rect y="1420" width="1080" height="500" fill="#b5a28a"/>'
    s += '<rect x="60" y="1080" width="960" height="80" rx="10" fill="#8b6b4a"/><rect x="90" y="1160" width="30" height="260" fill="#6b4a33"/><rect x="960" y="1160" width="30" height="260" fill="#6b4a33"/>'
    cols = ['#e04848', '#f2b233', '#6cb34a', '#f08a4b']
    for i in range(12):
        s += f'<circle cx="{120 + i * 80}" cy="1060" r="30" fill="{cols[i % 4]}"/>'
    return s


def school():
    s = wall('#f2efe3', floor='#c9b38f', floor_y=1420)
    s += '<rect x="160" y="280" width="760" height="380" rx="12" fill="#2f4a3a"/><rect x="160" y="280" width="760" height="380" rx="12" fill="none" stroke="#8b6b4a" stroke-width="18"/>'
    s += '<circle cx="900" cy="200" r="60" fill="#ffffff" stroke="#333" stroke-width="8"/><line x1="900" y1="200" x2="900" y2="160" stroke="#333" stroke-width="6"/><line x1="900" y1="200" x2="930" y2="200" stroke="#333" stroke-width="6"/>'
    for x in (60, 920):
        s += f'<rect x="{x}" y="200" width="100" height="300" fill="#bfe3f2"/>'
    for x in (150, 540, 800):
        s += f'<rect x="{x}" y="1210" width="200" height="50" rx="6" fill="#9a7b5a"/><rect x="{x + 20}" y="1260" width="20" height="150" fill="#6b4a33"/>'
    return s


def court():
    s = wall('#ddd3c2', floor='#7a5c44', floor_y=1420)
    s += '<rect x="60" y="300" width="50" height="1120" fill="#e9e1d2"/><rect x="970" y="300" width="50" height="1120" fill="#e9e1d2"/>'
    s += '<rect x="380" y="500" width="320" height="920" rx="8" fill="#6b4a33"/><rect x="400" y="520" width="280" height="880" rx="6" fill="#7c5a3f"/>'
    s += '<rect x="520" y="220" width="40" height="200" fill="#b58a3c"/><rect x="420" y="250" width="240" height="18" rx="8" fill="#b58a3c"/>'
    s += '<rect x="120" y="1250" width="220" height="50" rx="8" fill="#5a3d2a"/><rect x="740" y="1250" width="220" height="50" rx="8" fill="#5a3d2a"/>'
    return s
