"""Builds index.html (HyperFrames composition) for Buzdolabındaki Hayat episode 1 from timeline.json."""
import json, os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, 'timeline.json')))
TOTAL = T['total']
L = {l['id']: l for l in T['lines']}
W, H = 1080, 1920
CX, CY = 540, 800          # where a framed subject lands in the frame (above the captions)

# ---------------------------------------------------------------- world layout (end-state CSS)
CHAR = {   # id: (left, top, w, h) in world px
    'kemal': (150, 460, 300, 260), 'arda': (640, 420, 240, 300), 'yeliz': (120, 870, 240, 280),
    'nuri': (420, 810, 260, 340), 'kamil': (790, 810, 160, 340), 'eggs': (110, 1290, 500, 220),
    'sosis': (700, 1390, 200, 120),
}
CENTER = {k: (v[0] + v[2] / 2, v[1] + v[3] / 2) for k, v in CHAR.items()}

SHOTS = {
    'full': (540, 960, 1.0), 'freezer': (540, 200, 1.7), 'shelf1': (540, 590, 1.4), 'shelf2': (540, 1000, 1.4),
    'drawer': (540, 1720, 1.4), 'kemal': (300, 590, 2.0), 'kemal_snap': (300, 600, 2.5), 'kemal_arda': (530, 580, 1.55),
    'arda': (760, 560, 2.0), 'yeliz': (240, 1010, 2.0), 'yeliz_push': (240, 1000, 2.5), 'nuri': (550, 990, 2.0),
    'nuri_snap': (550, 960, 2.7), 'kamil': (860, 990, 2.0), 'eggs': (370, 1400, 1.8), 'shelf2_wide': (540, 1000, 1.15),
    'kemal_wide': (450, 600, 1.4), 'kemal_hand': (340, 600, 1.95),
}

def cam(shot):
    fx, fy, s = SHOTS[shot]
    x, y = CX - fx * s, CY - fy * s
    x = min(0, max(W - W * s, x)); y = min(0, max(H - H * s, y))
    return round(x, 1), round(y, 1), s

# ---------------------------------------------------------------- SVG characters
INK = '#1d1b2f'
def eyes(cx1, cy1, cx2, cy2, r=24, pr=10, extra=''):
    return f'''<g class="eyes-react"><g class="eyes-blink">
  <circle cx="{cx1}" cy="{cy1}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="6"/>
  <circle cx="{cx2}" cy="{cy2}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="6"/>
  <g class="pupils"><circle cx="{cx1}" cy="{cy1 + 2}" r="{pr}" fill="{INK}"/><circle cx="{cx2}" cy="{cy2 + 2}" r="{pr}" fill="{INK}"/>
  <circle cx="{cx1 + 4}" cy="{cy1 - 3}" r="3.5" fill="#fff"/><circle cx="{cx2 + 4}" cy="{cy2 - 3}" r="3.5" fill="#fff"/></g>
  {extra}</g></g>'''

def mouth(cx, cy, rx=24, ry=16):
    return f'<ellipse class="mouth" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#6b1d2a" stroke="{INK}" stroke-width="5"/>'

SVG = {}
SVG['kemal'] = f'''<svg viewBox="0 0 300 260" width="300" height="260">
<path d="M18 250 L282 250 L282 96 Q160 18 18 112 Z" fill="#ffcf3f" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>
<path d="M18 112 Q160 18 282 96 L282 120 Q160 50 18 136 Z" fill="#ffe27a"/>
<ellipse cx="60" cy="215" rx="16" ry="12" fill="#e9a91d"/><ellipse cx="245" cy="205" rx="20" ry="15" fill="#e9a91d"/>
<ellipse cx="250" cy="140" rx="11" ry="9" fill="#e9a91d"/><ellipse cx="45" cy="160" rx="9" ry="7" fill="#e9a91d"/>
<rect x="90" y="104" width="44" height="10" rx="5" fill="{INK}" transform="rotate(-12 112 109)"/>
<rect x="168" y="100" width="44" height="10" rx="5" fill="{INK}" transform="rotate(10 190 105)"/>
{eyes(112, 142, 190, 138, extra='<circle cx="190" cy="138" r="33" fill="none" stroke="#c9a227" stroke-width="6"/><path d="M222 146 Q240 190 228 232" fill="none" stroke="#c9a227" stroke-width="3"/>')}
{mouth(150, 208, 26, 16)}
<path d="M104 186 Q128 172 150 184 Q172 172 196 186 Q176 198 150 190 Q124 198 104 186 Z" fill="#5a3a1a" stroke="{INK}" stroke-width="4"/>
</svg>'''
SVG['nuri'] = f'''<svg viewBox="0 0 260 340" width="260" height="340">
<rect x="22" y="70" width="216" height="262" rx="44" fill="rgba(205,235,255,0.35)" stroke="#7fb3d5" stroke-width="7"/>
<path d="M29 170 L231 170 L231 290 Q231 326 194 326 L66 326 Q29 326 29 290 Z" fill="rgba(170,215,110,0.38)"/>
<path d="M130 92 C196 92 196 140 192 210 C188 290 176 318 130 318 C84 318 72 290 68 210 C64 140 64 92 130 92 Z" fill="#6aa84f" stroke="{INK}" stroke-width="7"/>
<circle cx="88" cy="250" r="6" fill="#4f8a3a"/><circle cx="172" cy="270" r="7" fill="#4f8a3a"/><circle cx="160" cy="230" r="5" fill="#4f8a3a"/><circle cx="96" cy="292" r="5" fill="#4f8a3a"/>
<path d="M78 134 q12 -22 30 -6 q12 -16 22 4 q-6 14 -26 10 q-18 6 -26 -8z" fill="#fff" stroke="{INK}" stroke-width="3"/>
<path d="M132 130 q10 -20 28 -6 q14 -12 22 6 q-8 12 -26 8 q-18 6 -24 -8z" fill="#fff" stroke="{INK}" stroke-width="3"/>
{eyes(105, 160, 158, 160, r=19, pr=8, extra='<rect x="84" y="140" width="42" height="18" fill="#6aa84f"/><rect x="137" y="140" width="42" height="18" fill="#6aa84f"/>')}
{mouth(131, 210, 20, 12)}
<path d="M104 196 Q131 184 158 196" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/>
<g class="lid"><rect x="34" y="30" width="192" height="48" rx="12" fill="#d4a017" stroke="{INK}" stroke-width="7"/>
<rect x="34" y="62" width="192" height="12" fill="#b8860b"/></g>
<circle cx="60" cy="120" r="7" fill="rgba(255,255,255,0.7)"/><circle cx="205" cy="190" r="5" fill="rgba(255,255,255,0.7)"/>
</svg>'''
SVG['yeliz'] = f'''<svg viewBox="0 0 240 280" width="240" height="280">
<path d="M28 70 L212 70 L192 262 Q120 278 48 262 Z" fill="#fffdf7" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>
<path d="M38 176 L202 176 L198 214 L42 214 Z" fill="#ff8fb1"/>
<text x="120" y="204" text-anchor="middle" font-family="BH Nunito" font-weight="900" font-size="25" fill="#fff">SKT: 3 GÜN</text>
<rect x="16" y="50" width="208" height="30" rx="12" fill="#ff8fb1" stroke="{INK}" stroke-width="7"/>
<path d="M196 54 q34 -26 30 8" fill="#ffb3c8" stroke="{INK}" stroke-width="5"/>
{eyes(88, 118, 152, 118, r=23, pr=10, extra='<path d="M62 100 l-10 -8 M70 94 l-6 -11 M178 100 l10 -8 M170 94 l6 -11" stroke="#1d1b2f" stroke-width="4" stroke-linecap="round"/>')}
<circle cx="60" cy="152" r="13" fill="#ffb3c8"/><circle cx="180" cy="152" r="13" fill="#ffb3c8"/>
{mouth(120, 156, 18, 13)}
</svg>'''
SVG['arda'] = f'''<svg viewBox="0 0 240 300" width="240" height="300">
<path d="M120 12 C176 12 196 92 214 168 C236 250 196 292 120 292 C44 292 4 250 26 168 C44 92 64 12 120 12 Z" fill="#2f6b2f" stroke="{INK}" stroke-width="8"/>
<path d="M120 34 C164 34 180 102 194 170 C210 240 180 272 120 272 C60 272 30 240 46 170 C60 102 76 34 120 34 Z" fill="#c5e384"/>
<circle cx="120" cy="210" r="46" fill="#8b5a2b" stroke="{INK}" stroke-width="6"/><circle cx="106" cy="196" r="10" fill="#a8743f"/>
{eyes(94, 112, 146, 112, r=17, pr=8)}
<g class="shades"><rect x="66" y="94" width="52" height="34" rx="12" fill="{INK}"/><rect x="122" y="94" width="52" height="34" rx="12" fill="{INK}"/>
<rect x="114" y="104" width="12" height="6" fill="{INK}"/><rect x="74" y="100" width="18" height="6" rx="3" fill="#6b7bbf"/><rect x="130" y="100" width="18" height="6" rx="3" fill="#6b7bbf"/></g>
{mouth(122, 150, 18, 10)}
<path d="M104 148 Q124 162 146 146" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>
</svg>'''
SVG['kamil'] = f'''<svg viewBox="0 0 160 340" width="160" height="340">
<rect x="20" y="84" width="120" height="248" rx="44" fill="#e0262c" stroke="{INK}" stroke-width="7"/>
<rect x="44" y="22" width="72" height="72" rx="16" fill="#f4f4f4" stroke="{INK}" stroke-width="7"/>
<rect x="66" y="4" width="28" height="24" rx="6" fill="#f4f4f4" stroke="{INK}" stroke-width="6"/>
<ellipse cx="80" cy="262" rx="44" ry="40" fill="#fff" stroke="{INK}" stroke-width="5"/>
<circle cx="80" cy="264" r="22" fill="#e0262c"/><path d="M72 244 q8 -10 16 0" fill="#4f8a3a"/>
{eyes(58, 150, 102, 150, r=18, pr=8, extra='<rect x="38" y="130" width="40" height="14" fill="#e0262c"/><rect x="82" y="130" width="40" height="14" fill="#e0262c"/>')}
{mouth(82, 196, 18, 12)}
<path d="M64 194 Q84 206 104 190" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>
</svg>'''
eggs = ''
for i in range(6):
    x = 50 + i * 80
    eggs += f'''<g class="egg" id="egg{i}"><ellipse cx="{x}" cy="96" rx="34" ry="44" fill="#fff3e0" stroke="{INK}" stroke-width="5"/>
{eyes(x - 12, 88, x + 12, 88, r=8, pr=4)}<ellipse class="mouth" cx="{x}" cy="114" rx="8" ry="6" fill="#6b1d2a" stroke="{INK}" stroke-width="3"/></g>'''
SVG['eggs'] = f'''<svg viewBox="0 0 500 220" width="500" height="220">{eggs}
<path d="M6 128 L494 128 L470 214 L30 214 Z" fill="#c9b8a0" stroke="{INK}" stroke-width="6"/>
<path d="M50 128 v70 M130 128 v70 M210 128 v70 M290 128 v70 M370 128 v70 M450 128 v70" stroke="#a8977f" stroke-width="5"/>
</svg>'''
SVG['sosis'] = f'''<svg viewBox="0 0 200 120" width="200" height="120">
<rect x="6" y="20" width="188" height="94" rx="20" fill="#ffb3c1" stroke="{INK}" stroke-width="6"/>
<rect x="22" y="34" width="156" height="22" rx="11" fill="#d9534f" stroke="{INK}" stroke-width="3"/>
<rect x="22" y="62" width="156" height="22" rx="11" fill="#d9534f" stroke="{INK}" stroke-width="3"/>
<circle cx="80" cy="98" r="5" fill="{INK}"/><circle cx="120" cy="98" r="5" fill="{INK}"/><path d="M88 108 q12 -8 24 0" fill="none" stroke="{INK}" stroke-width="4"/>
</svg>'''
HAND = f'''<svg viewBox="0 0 1100 320" width="1100" height="320">
<rect x="560" y="92" width="560" height="140" rx="30" fill="#4b6cb7" stroke="{INK}" stroke-width="8"/>
<rect x="540" y="86" width="60" height="152" rx="18" fill="#3a56a0" stroke="{INK}" stroke-width="8"/>
<g class="fingers">
<rect x="250" y="86" width="210" height="44" rx="22" fill="#f2c09a" stroke="{INK}" stroke-width="7"/>
<rect x="232" y="132" width="230" height="44" rx="22" fill="#f2c09a" stroke="{INK}" stroke-width="7"/>
<rect x="248" y="178" width="214" height="44" rx="22" fill="#f2c09a" stroke="{INK}" stroke-width="7"/>
<rect x="280" y="222" width="180" height="40" rx="20" fill="#f2c09a" stroke="{INK}" stroke-width="7"/></g>
<ellipse cx="470" cy="160" rx="100" ry="96" fill="#f2c09a" stroke="{INK}" stroke-width="8"/>
<rect x="360" y="40" width="140" height="48" rx="24" fill="#f2c09a" stroke="{INK}" stroke-width="7" transform="rotate(-24 430 64)"/>
</svg>'''
HAND_GRIP = (300, 160)       # point between the fingers, local px

# ---------------------------------------------------------------- timeline
js = []
def a(s): js.append(s)

def to(sel, props, t):
    a(f'tl.to({json.dumps(sel)}, {props}, {round(t, 3)});')
def fr(sel, props, t):
    a(f'tl.from({json.dumps(sel)}, {props}, {round(t, 3)});')
def st(sel, props, t):
    a(f'tl.set({json.dumps(sel)}, {props}, {round(t, 3)});')

def camera(shot, t, d=0.8, ease='power2.inOut'):
    x, y, s = cam(shot)
    to('#world', f'{{x:{x}, y:{y}, scale:{s}, duration:{d}, ease:"{ease}"}}', t)

FREEZE = 155.9
x0, y0, s0 = cam('full')
st('#world', f'{{x:{x0}, y:{y0}, scale:{s0}, transformOrigin:"0 0"}}', 0)
st('.mouth', '{scaleY:0.2, transformOrigin:"50% 50%"}', 0)
st('#world', '{filter:"grayscale(0) brightness(1) blur(0px)"}', 0)
to('#night', '{opacity:1, duration:0.5, ease:"power1.out"}', 0.05)
st('.eyes-react, .eyes-blink, .pupils, .rig, .bob, .fingers, .shades', '{transformOrigin:"50% 50%"}', 0)

# idle bob + blinks (deterministic)
seed = 7
def rnd():
    global seed
    seed = (seed * 1103515245 + 12345) % 2**31
    return seed / 2**31
for i, c in enumerate(['kemal', 'arda', 'yeliz', 'nuri', 'kamil', 'eggs']):
    d = 1.3 + 0.15 * i
    rep = int((FREEZE - 0.3) / d) - 1
    rep -= rep % 2 == 0          # odd repeat count so yoyo ends at rest
    to(f'#{c} .bob', f'{{y:-6, duration:{d}, ease:"sine.inOut", yoyo:true, repeat:{rep}}}', 0.3 + 0.1 * i)
    t = 1.0 + rnd() * 2
    while t < FREEZE - 1:
        to(f'#{c} .eyes-blink', '{scaleY:0.1, duration:0.07, ease:"power1.in"}', t)
        to(f'#{c} .eyes-blink', '{scaleY:1, duration:0.09, ease:"power1.out"}', t + 0.1)
        t += 2.8 + rnd() * 2.2

# mouths from the TTS alignment
VOW = set('aeıioöuüAEIİOÖUÜ')
MOUTH = {'kemal': '#kemal .mouth', 'arda': '#arda .mouth', 'yeliz': '#yeliz .mouth', 'nuri': '#nuri .mouth',
         'kamil': '#kamil .mouth', 'yumurtalar': '#eggs .mouth'}
for l in T['lines']:
    if l['who'] not in MOUTH:
        continue
    al = l['alignment']
    iv = []
    for ch, s, e in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if ch in VOW:
            s, e = l['start'] + s, l['start'] + max(e, s + 0.08)
            if iv and s - iv[-1][1] < 0.05:
                iv[-1][1] = e
            else:
                iv.append([s, e])
    for s, e in iv:
        o = min(0.06, (e - s) / 2)
        to(MOUTH[l['who']], f'{{scaleY:1, duration:{round(o, 3)}, ease:"power1.out"}}', s)
        to(MOUTH[l['who']], f'{{scaleY:0.2, duration:0.06, ease:"power1.in"}}', max(s + o, e - 0.03))

# listeners look at the speaker
POS = {'kemal': CENTER['kemal'], 'arda': CENTER['arda'], 'yeliz': CENTER['yeliz'], 'nuri': CENTER['nuri'],
       'kamil': CENTER['kamil'], 'yumurtalar': CENTER['eggs']}
CH_OF = {'yumurtalar': 'eggs'}
for l in T['lines']:
    if l['who'] not in POS:
        continue
    sx = POS[l['who']][0]
    for c in ['kemal', 'yeliz', 'nuri', 'kamil', 'eggs'] + (['arda'] if l['start'] > 96 else []):
        if c == CH_OF.get(l['who'], l['who']):
            to(f'#{c} .pupils', '{x:0, y:0, duration:0.25, ease:"power2.out"}', l['start'])
        else:
            dx = 5 if sx > CENTER[c][0] else -5
            to(f'#{c} .pupils', f'{{x:{dx}, duration:0.3, ease:"power2.out"}}', l['start'] + 0.1)

# ---- lighting: the door
def door_open(t):
    to('#night', '{opacity:0, duration:0.25, ease:"power2.out"}', t)
    to('#light', '{opacity:0.9, duration:0.15, ease:"power3.out"}', t)
    to('#light', '{opacity:0.3, duration:0.7, ease:"power2.out"}', t + 0.2)
    to('#lamp-glow', '{opacity:1, duration:0.2}', t)
    to('.eyes-react', '{scale:1.25, duration:0.35, ease:"back.out(3)"}', t + 0.1)
def door_close(t):
    to('#light', '{opacity:0, duration:0.35, ease:"power2.in"}', t)
    to('#lamp-glow', '{opacity:0, duration:0.3}', t)
    to('#night', '{opacity:1, duration:0.4, ease:"power2.in"}', t + 0.05)
    to('.eyes-react', '{scale:1, duration:0.5, ease:"power2.out"}', t + 0.6)

# ---- shots per line
SHOT = {'l01': 'full', 'l02': 'kamil', 'l04': 'freezer', 'l05b': 'full', 'l06': 'kemal', 'l07': 'kamil',
        'l09': 'yeliz', 'l10': 'yeliz_push', 'l11': 'yeliz', 'l12': 'nuri', 'l13': 'yeliz', 'l14': 'nuri', 'l15': 'kamil',
        'l17': 'arda', 'l18': 'eggs', 'l19': 'kemal', 'l19b': 'eggs', 'l20': 'arda', 'l21': 'kamil', 'l22': 'shelf2_wide',
        'l23': 'yeliz', 'l23b': 'arda', 'l23c': 'kemal', 'l23d': 'full'}
for lid, shot in SHOT.items():
    camera(shot, L[lid]['start'] - 0.35)
camera('kemal_snap', L['l08']['start'] - 0.05, 0.25, 'power4.out')
camera('nuri_snap', L['l16']['start'] - 0.05, 0.25, 'power4.out')
# tour pan
t5 = L['l05']['start']
camera('shelf1', t5 - 0.35); camera('shelf2', t5 + 1.6, 1.0); camera('drawer', t5 + 3.3, 1.0)
to('#world', '{scale:"+=0.08", x:"-=43", y:"-=40", duration:4, ease:"sine.inOut"}', L['l22']['start'] + 0.5)

# hook: door 1, the hand takes Sosis Sinan
D1 = L['l01']['start'] + L['l01']['dur'] + 0.4
door_open(D1)
hx, hy = CENTER['sosis'][0] - HAND_GRIP[0], CENTER['sosis'][1] - HAND_GRIP[1]
st('#hand', f'{{left:{hx}, top:{hy}, x:900, rotation:0}}', 0)
to('#hand', '{x:0, rotation:-4, duration:2.0, ease:"power2.out"}', D1 + 0.5)
to('#hand .fingers', '{scaleX:0.82, duration:0.15, ease:"power2.in"}', D1 + 2.6)
to('#sosis .rig', '{rotation:-8, duration:0.2}', D1 + 2.6)
to('#hand', '{x:900, rotation:6, duration:1.5, ease:"power2.in"}', D1 + 2.9)
to('#sosis', '{x:900, duration:1.5, ease:"power2.in"}', D1 + 2.9)
to('#hand .fingers', '{scaleX:1, duration:0.1}', D1 + 4.5)
door_close(D1 + 5.0)
to('#tag', '{opacity:1, duration:0.01}', 0)

# Kemal "Sus!" puff; panic shakes; "Duymadım"
to('#kemal .rig', '{scale:1.08, duration:0.25, ease:"back.out(4)"}', L['l08']['start'])
to('#kemal .rig', '{scale:1, duration:0.4, ease:"power2.out"}', L['l08']['start'] + 1.2)
for lid in ['l09', 'l11', 'l23']:
    s, d = L[lid]['start'], L[lid]['dur']
    rep = int(d / 0.12) | 1
    to('#yeliz .rig', f'{{x:6, duration:0.06, ease:"sine.inOut", yoyo:true, repeat:{rep}}}', s)
    to('#yeliz .rig', '{x:0, duration:0.1}', s + 0.06 * (rep + 1) + 0.05)
to('#nuri .eyes-blink', '{scaleY:0.1, duration:0.15}', L['l16']['start'])
to('#nuri .eyes-blink', '{scaleY:1, duration:0.2}', L['l16']['start'] + 1.3)
to('#kamil .rig', '{y:-30, duration:0.25, ease:"power2.out", yoyo:true, repeat:3}', L['l21']['start'])
to('#nuri .lid', '{rotation:-8, duration:0.3, ease:"back.out(3)", transformOrigin:"50% 100%"}', L['l12']['start'] + 0.3)

# door 2: the avocado arrives
D2 = L['l16']['start'] + L['l16']['dur'] + 0.9
st('#arda', '{x:800}', 0)
ax, ay = CENTER['arda'][0] - HAND_GRIP[0], CENTER['arda'][1] - HAND_GRIP[1]
st('#hand', f'{{left:{ax}, top:{ay}, x:800, rotation:0}}', D2 - 0.1)
st('#hand .fingers', '{scaleX:0.82}', D2 - 0.1)
camera('full', D2 - 0.3, 0.6)
door_open(D2)
to('#hand', '{x:0, duration:2.6, ease:"power2.out"}', D2 + 0.6)
to('#arda', '{x:0, duration:2.6, ease:"power2.out"}', D2 + 0.6)
to('#arda .rig', '{scaleY:0.88, duration:0.12, ease:"power2.in", transformOrigin:"50% 100%"}', D2 + 3.25)
to('#arda .rig', '{scaleY:1, duration:0.5, ease:"elastic.out(1,0.4)"}', D2 + 3.4)
to('#hand .fingers', '{scaleX:1, duration:0.15}', D2 + 3.4)
to('#hand', '{x:800, duration:1.5, ease:"power2.in"}', D2 + 3.7)
door_close(D2 + 5.9)
camera('kemal_arda', D2 + 6.3, 0.9)
to('#arda .shades', '{y:14, duration:0.5, ease:"back.out(2)"}', L['l17']['start'] + 0.4)
fr('#eggs .egg', '{y:-24, duration:0.35, ease:"back.out(3)", stagger:0.05}', L['l18']['start'])

# climax: door 3, the hand reaches for Kemal
D3 = L['l23d']['start'] + L['l23d']['dur'] + 0.5
kx, ky = CENTER['kemal'][0] - HAND_GRIP[0], CENTER['kemal'][1] - HAND_GRIP[1]
st('#hand', f'{{left:{kx}, top:{ky}, x:1100, rotation:0}}', D3 - 0.1)
door_open(D3)
camera('kemal_wide', D3 + 1.4, 1.0)
to('#hand', '{x:520, duration:1.2, ease:"power2.out"}', D3 + 0.8)
to('#hand', '{x:70, duration:' + str(round(FREEZE - (D3 + 2.2), 2)) + ', ease:"sine.inOut"}', D3 + 2.2)
to('#world', '{x:' + str(cam("kemal_hand")[0]) + ', y:' + str(cam("kemal_hand")[1]) + ', scale:' + str(cam("kemal_hand")[2]) + ', duration:' + str(round(L["l25"]["start"] - 0.1 - (D3 + 2.6), 2)) + ', ease:"sine.inOut"}', D3 + 2.6)
rep = int((FREEZE - (D3 + 4)) / 0.1) | 1
to('#kemal .rig', f'{{x:4, duration:0.05, yoyo:true, repeat:{rep}}}', D3 + 4)
camera('nuri_snap', L['l25']['start'] - 0.05, 0.25, 'power4.out')
camera('kemal_hand', L['l25']['start'] + L['l25']['dur'] + 0.2, 0.25, 'power4.out')

# freeze + call to action
to('#flash', '{opacity:0.9, duration:0.08}', FREEZE)
to('#flash', '{opacity:0, duration:0.5, ease:"power2.out"}', FREEZE + 0.1)
to('#world', '{filter:"grayscale(1) brightness(0.55) blur(3px)", duration:0.6}', FREEZE + 0.1)
to('#night', '{opacity:0.6, duration:0.6}', FREEZE + 0.1)
fr('#cta-head', '{y:-80, opacity:0, duration:0.6, ease:"back.out(2)"}', FREEZE + 0.6)
fr('#cta-sub', '{scale:0.6, opacity:0, duration:0.5, ease:"elastic.out(1,0.5)"}', FREEZE + 1.2)
fr('#btn-tost', '{x:-300, rotation:-12, opacity:0, duration:0.55, ease:"back.out(2.5)"}', L['l26']['start'] + 2.0)
fr('#btn-kurtar', '{x:300, rotation:12, opacity:0, duration:0.55, ease:"back.out(2.5)"}', L['l26']['start'] + 2.7)
fr('#cta-write', '{y:40, opacity:0, duration:0.45, ease:"power3.out"}', L['l26']['start'] + 4.6)
fr('#cta-next', '{scale:0.3, opacity:0, duration:0.6, ease:"back.out(3)"}', L['l26']['start'] + 7.6)
to('#btn-tost', '{scale:1.06, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:9}', L['l26']['start'] + 3.0)
to('#btn-kurtar', '{scale:1.06, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:9}', L['l26']['start'] + 3.45)
to('#fade', '{opacity:1, duration:1.0, ease:"power1.in"}', TOTAL - 1.05)

# title card (between the hook and the tour)
TS, TE = L['l03']['start'] - 0.7, L['l04']['start'] - 0.7
fr('#title', '{clipPath:"circle(0% at 50% 50%)", duration:0.6, ease:"power3.inOut"}', TS)
fr('#title-fridge', '{y:-200, rotation:-15, opacity:0, duration:0.8, ease:"bounce.out"}', TS + 0.3)
fr('#title-1', '{x:-500, opacity:0, duration:0.6, ease:"power4.out"}', TS + 0.7)
fr('#title-2', '{x:500, opacity:0, duration:0.6, ease:"expo.out"}', TS + 0.9)
fr('#title-sub', '{scale:0.4, opacity:0, duration:0.6, ease:"back.out(3)"}', TS + 1.6)
fr('.flake', '{scale:0, opacity:0, duration:0.5, ease:"back.out(3)", stagger:0.06}', TS + 0.4)
to('#title', '{clipPath:"circle(0% at 50% 50%)", duration:0.55, ease:"power3.in"}', TE - 0.55)
fr('#tag', '{x:-260, duration:0.5, ease:"back.out(2)"}', TE + 0.1)

# ---------------------------------------------------------------- captions
COLORS = {'anlatici': '#9fd3ff', 'kemal': '#ffcf3f', 'nuri': '#8fd16f', 'yeliz': '#ff8fb1', 'arda': '#c5e384',
          'kamil': '#ff5a5f', 'yumurtalar': '#ffe8c2'}
NAMES = {'anlatici': 'ANLATICI', 'kemal': 'KAŞAR KEMAL', 'nuri': 'TURŞU NURİ DEDE', 'yeliz': 'YOĞURT YELİZ',
         'arda': 'AVOKADO ARDA', 'kamil': 'KETÇAP KÂMİL', 'yumurtalar': 'YUMURTALAR'}
caps_html = []
cid = 0
for l in T['lines']:
    if l['id'] == 'l03':
        continue
    al = l['alignment']
    chars, ss, es = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
    words, cur, cs = [], '', None
    for ch, s, e in zip(chars, ss, es):
        if ch == ' ':
            if cur: words.append((cur, cs, pe)); cur = ''
            continue
        if not cur: cs = s
        cur += ch; pe = e
    if cur: words.append((cur, cs, pe))
    chunks, c = [], []
    for w in words:
        c.append(w)
        if len(c) >= 6 or (w[0][-1] in '.!?:' and len(c) >= 2):
            chunks.append(c); c = []
    if c:
        if chunks and len(c) == 1: chunks[-1] += c
        else: chunks.append(c)
    for k, ch in enumerate(chunks):
        cid += 1
        t0 = l['start'] + ch[0][1] - 0.08
        t1 = l['start'] + (chunks[k + 1][0][1] - 0.1 if k + 1 < len(chunks) else l['dur'] + 0.3)
        narr = ' narr' if l['who'] == 'anlatici' else ''
        spans = ''.join(f'<span class="w" id="c{cid}w{j}">{w[0]}</span> ' for j, w in enumerate(ch))
        caps_html.append(f'<div class="cap{narr}" id="cap{cid}"><div class="chip" style="background:{COLORS[l["who"]]}">{NAMES[l["who"]]}</div><div class="txt">{spans}</div></div>')
        st(f'#cap{cid}', '{opacity:1}', t0)
        for j, w in enumerate(ch):
            fr(f'#c{cid}w{j}', '{y:18, opacity:0, duration:0.18, ease:"back.out(2.5)"}', l['start'] + w[1] - 0.04)
        st(f'#cap{cid}', '{opacity:0}', t1)

# ---------------------------------------------------------------- html
def char_div(c, z):
    lft, top, w, h = CHAR[c]
    return f'<div class="char" id="{c}" style="left:{lft}px;top:{top}px;width:{w}px;height:{h}px;z-index:{z}"><div class="rig"><div class="bob">{SVG[c]}</div></div></div>'

flakes = ''.join(f'<div class="flake" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px"></div>'
                 for x, y, s in [(120, 300, 26), (900, 260, 34), (180, 1450, 30), (860, 1500, 22), (520, 180, 18),
                                 (90, 860, 20), (960, 900, 28), (300, 1640, 18), (760, 1700, 24)])

html = f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=1080, height=1920">
<script src="lib/gsap.min.js"></script>
<style>
@font-face{{font-family:"BH Fredoka";font-weight:700;font-style:normal;src:url(fonts/fredoka-latin-700-normal.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}
@font-face{{font-family:"BH Fredoka";font-weight:700;font-style:normal;src:url(fonts/fredoka-latin-ext-700-normal.woff2) format("woff2");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}}
@font-face{{font-family:"BH Nunito";font-weight:900;font-style:normal;src:url(fonts/nunito-latin-900-normal.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}
@font-face{{font-family:"BH Nunito";font-weight:900;font-style:normal;src:url(fonts/nunito-latin-ext-900-normal.woff2) format("woff2");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}}
@font-face{{font-family:"BH Nunito";font-weight:800;font-style:italic;src:url(fonts/nunito-latin-800-italic.woff2) format("woff2");unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}
@font-face{{font-family:"BH Nunito";font-weight:800;font-style:italic;src:url(fonts/nunito-latin-ext-800-italic.woff2) format("woff2");unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1080px;height:1920px;overflow:hidden;background:#0f1b33}}
#root{{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0f1b33}}
#world{{position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:visible;will-change:transform}}
.wall{{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,#eef7fc 0%,#dcecf6 45%,#b9d3e6 100%)}}
.rib{{position:absolute;top:340px;bottom:0;width:6px;background:rgba(150,185,210,0.35)}}
.side{{position:absolute;top:0;bottom:0;width:44px;background:#c7dceb;border:6px solid #9fbdd3}}
.freezer{{position:absolute;left:44px;right:44px;top:30px;height:300px;border-radius:0 0 28px 28px;
  background:radial-gradient(ellipse at 50% 30%,#ffffff 0%,#d6ecfa 60%,#a9cfe8 100%);border:8px solid #8fb8d6;border-top:none}}
.freezer .label{{position:absolute;left:50%;top:118px;transform:translateX(-50%);font:700 64px "BH Fredoka",sans-serif;color:#2a4a7a;letter-spacing:6px}}
.freezer .icicle{{position:absolute;top:296px;width:0;height:0;border-left:14px solid transparent;border-right:14px solid transparent;border-top:46px solid #cde8f8}}
.shelf{{position:absolute;left:44px;right:44px;height:24px;background:linear-gradient(#e7f5fd,#a9d4ee);border:5px solid #7fb3d5;border-radius:6px}}
.sign{{position:absolute;padding:8px 20px;border-radius:14px;background:#1d1b2f;color:#fff;font:700 30px "BH Fredoka",sans-serif;letter-spacing:1px;transform:translateX(-50%)}}
.drawer{{position:absolute;left:70px;right:70px;top:1572px;height:300px;border-radius:24px 24px 10px 10px;
  background:rgba(190,225,245,0.55);border:8px solid #7fb3d5;overflow:hidden}}
.veg{{position:absolute;border:6px solid #1d1b2f}}
.char{{position:absolute}} .char .rig,.char .bob{{width:100%;height:100%}} .char svg{{display:block;overflow:visible}}
#hand{{position:absolute;width:1100px;height:320px;z-index:30}}
#lamp{{position:absolute;left:950px;top:360px;width:60px;height:60px;border-radius:50%;background:#f6f1d5;border:6px solid #9fbdd3}}
#lamp-glow{{position:absolute;left:780px;top:190px;width:400px;height:400px;border-radius:50%;opacity:0;
  background:radial-gradient(circle,rgba(255,247,224,0.95) 0%,rgba(255,247,224,0) 70%)}}
#night{{position:absolute;inset:0;z-index:40;pointer-events:none;opacity:0;
  background:radial-gradient(ellipse at 50% 42%,rgba(25,45,90,0.22) 0%,rgba(10,20,45,0.55) 100%)}}
#light{{position:absolute;inset:0;z-index:41;opacity:0;pointer-events:none;
  background:radial-gradient(ellipse at 85% 30%,rgba(255,250,232,1) 0%,rgba(255,247,224,0.55) 45%,rgba(255,247,224,0.15) 100%)}}
#flash{{position:absolute;inset:0;z-index:60;background:#fff7e0;opacity:0}}
#fade{{position:absolute;inset:0;z-index:90;background:#000;opacity:0}}
#tag{{position:absolute;left:56px;top:190px;z-index:55;padding:10px 26px;border-radius:40px;background:#ff4d6d;
  color:#fff;font:700 44px "BH Fredoka",sans-serif;letter-spacing:2px;box-shadow:0 6px 0 #1d1b2f;opacity:0}}
.cap{{position:absolute;left:60px;right:60px;bottom:400px;z-index:50;opacity:0;display:flex;flex-direction:column;align-items:center;gap:14px}}
.chip{{padding:6px 22px;border-radius:30px;color:#1d1b2f;font:700 36px "BH Fredoka",sans-serif;letter-spacing:2px;border:4px solid #1d1b2f}}
.txt{{text-align:center;font:900 68px/1.18 "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:12px #1d1b2f;paint-order:stroke fill;max-width:960px}}
.cap.narr .txt{{font-style:italic;font-weight:800;color:#d9efff}}
.w{{display:inline-block}}
#title{{position:absolute;inset:0;z-index:70;clip-path:circle(150% at 50% 50%);background:radial-gradient(ellipse at 50% 40%,#3a2a6a 0%,#1a1838 55%,#0f1b33 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px;padding:200px 60px}}
#title-fridge{{width:220px;height:320px;border-radius:36px;background:#eef7fc;border:10px solid #1d1b2f;position:relative;box-shadow:0 14px 0 #ff4d6d}}
#title-fridge:before{{content:"";position:absolute;left:0;right:0;top:110px;height:10px;background:#1d1b2f}}
#title-fridge:after{{content:"";position:absolute;right:26px;top:150px;width:16px;height:80px;border-radius:8px;background:#1d1b2f}}
.tline{{font:700 118px/1 "BH Fredoka",sans-serif;color:#fff;text-align:center;-webkit-text-stroke:10px #1d1b2f;paint-order:stroke fill;text-shadow:0 10px 0 #ff4d6d}}
#title-2{{font-size:200px;color:#ffcf3f}}
#title-sub{{padding:14px 36px;border-radius:50px;background:#ff4d6d;color:#fff;font:900 52px "BH Nunito",sans-serif;border:6px solid #1d1b2f}}
.flake{{position:absolute;border-radius:50%;background:#cde8f8;box-shadow:0 0 18px #9fd3ff}}
#cta{{position:absolute;inset:0;z-index:80;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;gap:34px;padding:300px 60px 0}}
#cta-head{{font:700 92px/1.05 "BH Fredoka",sans-serif;color:#fff;text-align:center;-webkit-text-stroke:10px #1d1b2f;paint-order:stroke fill;text-shadow:0 10px 0 #ff4d6d}}
#cta-sub{{font:900 50px "BH Nunito",sans-serif;color:#ffcf3f;-webkit-text-stroke:8px #1d1b2f;paint-order:stroke fill}}
.btns{{display:flex;gap:40px;margin-top:20px}}
.btn{{width:420px;padding:40px 0;border-radius:40px;border:8px solid #1d1b2f;text-align:center;font:700 96px "BH Fredoka",sans-serif;color:#fff;box-shadow:0 14px 0 #1d1b2f;-webkit-text-stroke:6px #1d1b2f;paint-order:stroke fill}}
#btn-tost{{background:#ff8a3d}} #btn-kurtar{{background:#2ec4b6}}
#cta-write{{font:900 54px "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:8px #1d1b2f;paint-order:stroke fill}}
#cta-next{{padding:14px 40px;border-radius:50px;background:#ff4d6d;color:#fff;font:700 56px "BH Fredoka",sans-serif;border:6px solid #1d1b2f}}
</style></head>
<body>
<div id="root" data-composition-id="buzdolabi-ep1" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
 <div id="world" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1">
  <div class="wall"></div>
  {''.join(f'<div class="rib" style="left:{x}px"></div>' for x in (220, 400, 680, 860))}
  <div class="side" style="left:0"></div><div class="side" style="right:0"></div>
  <div class="freezer"><div class="label">SİBİRYA</div>
   {''.join(f'<div class="icicle" style="left:{x}px"></div>' for x in (60, 190, 330, 520, 700, 860))}</div>
  <div id="lamp-glow"></div><div id="lamp"></div>
  <div class="shelf" style="top:720px"></div><div class="shelf" style="top:1150px"></div><div class="shelf" style="top:1510px"></div>
  <div class="sign" style="left:540px;top:752px">ZENGİNLER MAHALLESİ</div>
  <div class="sign" style="left:860px;top:1182px">SOS SOKAĞI</div>
  <div class="drawer">
   <div class="veg" style="left:60px;top:60px;width:240px;height:190px;border-radius:50% 50% 40% 40%;background:#7cc36b"></div>
   <div class="veg" style="left:330px;top:110px;width:150px;height:150px;border-radius:50%;background:#e8473f"></div>
   <div class="veg" style="left:520px;top:70px;width:90px;height:220px;border-radius:45px 45px 20px 20px;background:#f28c28;transform:rotate(18deg)"></div>
   <div class="veg" style="left:680px;top:90px;width:170px;height:160px;border-radius:50%;background:#9b5de5"></div>
   <div class="sign" style="left:470px;top:20px">SEBZE ÇEKMECESİ</div>
  </div>
  {char_div('kemal', 10)}{char_div('arda', 11)}{char_div('nuri', 10)}{char_div('yeliz', 11)}{char_div('kamil', 10)}
  {char_div('eggs', 10)}{char_div('sosis', 9)}
  <div id="hand">{HAND}</div>
 </div>
 <div id="night" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="2"></div>
 <div id="light" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="3"></div>
 <div id="tag" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="4">1. GÜN</div>
 <div id="caps" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="5" style="position:absolute;inset:0;z-index:50">{''.join(caps_html)}</div>
 <div id="title" class="clip" data-start="{round(TS, 3)}" data-duration="{round(TE - TS, 3)}" data-track-index="6">
  {flakes}<div id="title-fridge"></div><div class="tline" id="title-1">BUZDOLABINDAKİ</div><div class="tline" id="title-2">HAYAT</div>
  <div id="title-sub">1. GÜN · BÜYÜK IŞIK</div></div>
 <div id="cta" class="clip" data-start="{FREEZE}" data-duration="{round(TOTAL - FREEZE, 3)}" data-track-index="7">
  <div id="cta-head">KAŞAR KEMAL'İN KADERİ SENİN ELİNDE</div><div id="cta-sub">Yorumlara tek kelime yaz:</div>
  <div class="btns"><div class="btn" id="btn-tost">TOST</div><div class="btn" id="btn-kurtar">KURTAR</div></div>
  <div id="cta-write">Kemal'i sen kurtar!</div><div id="cta-next">YARIN · 2. GÜN</div></div>
 <div id="flash" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="8"></div>
 <div id="fade" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9"></div>
 <audio id="mix" data-start="0" data-duration="{TOTAL}" data-track-index="10" src="assets/master.m4a" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["buzdolabi-ep1"] = tl;
</script>
</body></html>
'''
open(os.path.join(HERE, 'index.html'), 'w').write(html)
json.dump({'door1': D1, 'door2': D2, 'door3': D3, 'freeze': FREEZE, 'title': [TS, TE]},
          open(os.path.join(HERE, 'events.json'), 'w'), indent=1)
print('index.html', len(html) // 1024, 'KB,', len(js), 'tweens; doors', round(D1, 2), round(D2, 2), round(D3, 2))
