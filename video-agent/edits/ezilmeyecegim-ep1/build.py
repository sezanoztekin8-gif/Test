"""Bu Sefer Ezilmeyeceğim — Bölüm 1. Trims the Chatterbox lines, plans the timeline, writes index.html
(flat 2D SVG scenes, HyperFrames) and mixes assets/master.m4a.   Usage: python3 build.py [--no-mix]"""
import json, os, sys, subprocess
from art import person, wall, window, frame_pic, table, breakfast, bed, mirror_room, diary_page, CAST

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LIB = os.path.join(ROOT, '.claude/skills/editing-videos/library')
MUSIC2 = os.path.join(ROOT, '.claude/skills/short-editing/assets/music')
S = json.load(open(os.path.join(HERE, 'script.json')))
TTS, VO = os.path.join(HERE, 'assets', 'tts'), os.path.join(HERE, 'assets', 'vo')
os.makedirs(VO, exist_ok=True)


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))


# ------------------------------------------------------------------ voice: trim silence, inner voice gets a soft echo
lines = S['lines']
for l in lines:
    src, dst = os.path.join(TTS, l['id'] + '.wav'), os.path.join(VO, l['id'] + '.wav')
    if not os.path.exists(src):                  # preview before all lines are voiced
        l['dur'] = len(l['text']) * 0.075; continue
    if True:
        af = ('atrim=0:3.75,' if l['id'] == 'l11' else '') + ('silenceremove=stop_periods=-1:stop_duration=0.35:stop_threshold=-40dB:stop_silence=0.3,atempo=1.05,silenceremove=start_periods=1:start_threshold=-42dB,areverse,silenceremove=start_periods=1:start_threshold=-42dB,'
              'areverse,adelay=40,apad=pad_dur=0.08,highpass=f=70,acompressor=threshold=0.12:ratio=2.5:attack=8:release=120')
        if l['inner']:
            af += ',aecho=0.85:0.6:45|90:0.22|0.12'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', af, '-ar', '48000', dst], check=True)
    l['dur'] = dur(dst)

# ------------------------------------------------------------------ timeline
TITLE_LEN, TAIL = 2.6, 6.0
t = 0.35
for i, l in enumerate(lines):
    if i:
        new_scene = l['scene'] != lines[i - 1]['scene'] and not {l['scene'], lines[i - 1]['scene']} <= {'table', 'turn'}
        t += 0.8 if new_scene else 0.28
    if l['id'] == 'l05':
        TS = t; t += TITLE_LEN
    if l['id'] in ('l13', 'l18'):
        t += 0.55                       # the pause before she answers
    if l['id'] == 'l22':
        t += 0.5
    l['start'] = round(t, 3); t += l['dur']
L = {l['id']: l for l in lines}
SPEECH_END = t
TOTAL = round(t + TAIL, 2)
TE = TS + TITLE_LEN

# scenes (table + turn share one kitchen; the camera does the turn)
SC = [('bedroom', 'l01'), ('mirror', 'l03'), ('door', 'l05'), ('kitchen', 'l08'), ('night', 'l19'), ('diary', 'l21')]
scenes = []
for k, (name, first) in enumerate(SC):
    st0 = 0.0 if k == 0 else (TE if name == 'door' else L[first]['start'] - 0.55)
    scenes.append({'name': name, 'start': round(st0, 3), 'first': first})
for k, s in enumerate(scenes):
    s['end'] = scenes[k + 1]['start'] if k + 1 < len(scenes) else TOTAL
SCENE_OF = {}
for l in lines:
    SCENE_OF[l['id']] = 'kitchen' if l['scene'] in ('table', 'turn') else l['scene']

# people per scene: who, cx, feet, scale, [(from line, expr, arms)], behind (drawn before table)
PEOPLE = {
    'bedroom': [('nermin', 850, 1640, 0.92, [('l01', 'angry', 'down')], False),
                ('zehra', 420, 1800, 1.0, [('l01', 'shock', 'head'), ('l02', 'sad', 'down')], False)],
    'mirror': [('zehra', 540, 1500, 1.32, [('l03', 'shock', 'down'), ('l04', 'sad', 'down')], False)],
    'door': [('ali', 720, 1740, 1.0, [('l05', 'sad', 'down'), ('l07', 'smile', 'down')], False),
             ('zehra', 330, 1820, 1.0, [('l05', 'neutral', 'down'), ('l06', 'sad', 'down'), ('l07', 'smile', 'down')], False)],
    'kitchen': [('kenan', 600, 1560, 1.0, [('l08', 'angry', 'down'), ('l13', 'shock', 'down'), ('l16', 'neutral', 'down'), ('l17', 'angry', 'down')], True),
                ('nermin', 870, 1520, 0.95, [('l08', 'angry', 'down'), ('l13', 'shock', 'down')], True),
                ('ali', 380, 1440, 1.0, [('l08', 'sad', 'down'), ('l13', 'shock', 'down'), ('l16', 'smile', 'down')], True),
                ('zehra', 175, 1860, 1.0, [('l08', 'sad', 'down'), ('l13', 'angry', 'cross'), ('l15', 'calm', 'cross'), ('l18', 'calm', 'down')], False)],
    'night': [('ali', 700, 1620, 1.0, [('l19', 'smile', 'down')], False),
              ('zehra', 360, 1780, 1.0, [('l19', 'calm', 'down'), ('l20', 'smile', 'down')], False)],
    'diary': [],
}
SPK = {'defne': 'zehra', 'kenan': 'kenan', 'nermin': 'nermin', 'ali': 'ali'}


def head(who, cx, feet, sc):
    h = CAST[who]['h'] * sc
    r = h * (0.13 if who == 'ali' else 0.105)
    return cx, feet - h + r


js = []
def a(x): js.append(x)
def to(sel, props, t): a(f'tl.to({json.dumps(sel)}, {props}, {round(t, 3)});')
def fr(sel, props, t): a(f'tl.from({json.dumps(sel)}, {props}, {round(t, 3)});')
def st(sel, props, t): a(f'tl.set({json.dumps(sel)}, {props}, {round(t, 3)});')


def background(name):
    if name == 'bedroom':
        s = wall('#ecd9c3', floor='#a77c58', paper='#e0c8ab') + window(110, 230, 360, 440)
        s += '<rect x="680" y="620" width="360" height="1100" fill="#6b4d36"/><rect x="700" y="640" width="320" height="1080" fill="#3b2c25"/>'
        s += '<rect x="700" y="640" width="320" height="1080" fill="#f7d9a0" opacity="0.25"/>'
        s += bed(30, 1420, 560) + frame_pic(480, 330, 170, 210)
        return s
    if name == 'mirror':
        return mirror_room()
    if name == 'door':
        s = wall('#d4e0e6', floor='#9b7656', floor_y=1460)
        s += '<rect x="80" y="420" width="420" height="1060" fill="#7a5a3d"/><rect x="100" y="440" width="380" height="1040" fill="#a3825f"/><circle cx="440" cy="980" r="18" fill="#e5c36b"/>'
        s += frame_pic(640, 360, 300, 230, '#e8c6a0') + '<rect x="0" y="1300" width="1080" height="12" fill="#ffffff55"/>'
        return s
    if name == 'kitchen':
        s = wall('#f3e2c2', floor='#9a6f4f', floor_y=1300)
        for x in range(0, 1080, 108):
            for y in range(860, 1300, 108):
                s += f'<rect x="{x + 4}" y="{y + 4}" width="100" height="100" fill="#efd8b1"/>'
        s += window(330, 200, 420, 400) + '<rect x="40" y="250" width="200" height="420" rx="10" fill="#c98f62"/><rect x="840" y="250" width="200" height="420" rx="10" fill="#c98f62"/>'
        s += '<circle cx="140" cy="460" r="10" fill="#6b4d36"/><circle cx="940" cy="460" r="10" fill="#6b4d36"/>'
        return s
    if name == 'night':
        s = wall('#2d3452', floor='#3b3046', paper='#353d5e') + window(560, 260, 400, 460, night=True)
        s += bed(40, 1500, 560, night=True) + '<circle cx="120" cy="1090" r="260" fill="#f6d36b" opacity="0.10"/>'
        s += '<rect x="90" y="1060" width="70" height="140" fill="#e9b96e"/><path d="M60 1060 L190 1060 L160 980 L90 980Z" fill="#f2d39a"/>'
        return s
    return diary_page()


scene_html = []
for k, sc in enumerate(scenes):
    name, sid = sc['name'], f's{k}'
    body = background(name)
    front = ''
    for who, cx, feet, s_, states, behind in PEOPLE[name]:
        g = ''
        for j, (lid, expr, arms) in enumerate(states):
            pid = f'{sid}-{who}-{j}'
            g += person(who, cx, feet, expr, s_, mid=f'{pid}-m', arms=arms, pid=pid).replace(
                f'<g id="{pid}"', f'<g id="{pid}" opacity="{1 if j == 0 else 0}"', 1)
            if j:
                st(f'#{pid}', '{opacity:1}', L[lid]['start'] - 0.12)
                st(f'#{sid}-{who}-{j - 1}', '{opacity:0}', L[lid]['start'] - 0.12)
        wrap = f'<g id="{sid}-{who}" class="breathe">{g}</g>'
        if name == 'mirror':
            wrap = f'<g clip-path="url(#mclip)">{wrap}</g>'
        if behind:
            body += wrap
        else:
            front += wrap
        n = max(1, int((sc['end'] - sc['start']) / 1.7))
        st(f'#{sid}-{who}', '{transformOrigin:"50% 100%"}', 0)
        to(f'#{sid}-{who}', f'{{scaleY:1.012, scaleX:0.996, duration:0.85, ease:"sine.inOut", yoyo:true, repeat:{n * 2 - 1}}}', sc['start'] + (k * 0.3) % 0.6)
    if name == 'kitchen':
        body += table(1180) + breakfast(1180)
    if name == 'mirror':
        body = '<defs><clipPath id="mclip"><rect x="200" y="190" width="680" height="920" rx="340"/></clipPath></defs>' + body
        front += '<rect x="200" y="190" width="680" height="920" rx="340" fill="url(#shine)" opacity="0.35"/>'
        body = '<defs><linearGradient id="shine" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.9"/><stop offset="0.35" stop-color="#fff" stop-opacity="0"/><stop offset="0.6" stop-color="#fff" stop-opacity="0.25"/><stop offset="0.7" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>' + body
    svg = f'<svg width="1080" height="1920" viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg">{body}{front}</svg>'
    d = round(sc['end'] - sc['start'] + (0.6 if k + 1 < len(scenes) else 0), 3)
    scene_html.append(f'<div class="scene clip" id="{sid}" data-start="{sc["start"]}" data-duration="{d}" data-track-index="{1 + k % 2}" '
                      f'style="z-index:{10 + k}{";opacity:0" if k else ""}"><div class="cam" id="{sid}-cam">{svg}</div></div>')
    if k:
        to(f'#{sid}', '{opacity:1, duration:0.55, ease:"sine.inOut"}', sc['start'])

# mouths: closed by default, flap while a character speaks (not on inner voice)
st('.mouth', '{scaleY:0, transformOrigin:"50% 50%"}', 0)
st('.mouth.open', '{scaleY:1}', 0)


def scene_idx(lid):
    return next(k for k, s in enumerate(scenes) if s['name'] == SCENE_OF[lid])


for l in lines:
    if l['inner'] or l['scene'] == 'diary':
        continue
    k = scene_idx(l['id'])
    sel = f'#s{k} .m-{SPK[l["who"]]}'
    n = int(l['dur'] / 0.16)
    to(sel, f'{{scaleY:1, duration:0.08, ease:"sine.inOut", yoyo:true, repeat:{n * 2 - 1}}}', l['start'] + 0.05)
    to(sel, '{scaleY:0, duration:0.06}', l['start'] + l['dur'])

# camera: push in on whoever speaks (Zehra for the inner voice)
FOCUS_Y = 760
pos = {}
for k, sc in enumerate(scenes):
    for who, cx, feet, s_, _, _ in PEOPLE[sc['name']]:
        pos[(k, who)] = head(who, cx, feet, s_)


def cam(z, hx, hy):
    x = min(0, max(1080 - 1080 * z, 540 - hx * z))
    y = min(0, max(1920 - 1920 * z, FOCUS_Y - hy * z))
    return f'scale:{z:.3f}, x:{x:.0f}, y:{y:.0f}'


ZOOM = {'l01': 1.25, 'l02': 1.45, 'l03': 1.15, 'l04': 1.4, 'l11': 1.55, 'l13': 1.7, 'l14': 1.6, 'l15': 1.45, 'l16': 1.0,
        'l17': 1.45, 'l18': 1.55, 'l19': 1.35, 'l20': 1.35}
for k, sc in enumerate(scenes):
    st(f'#s{k}-cam', '{transformOrigin:"0% 0%", scale:1, x:0, y:0}', 0)
for l in lines:
    k = scene_idx(l['id'])
    if scenes[k]['name'] == 'diary':
        continue
    who = 'zehra' if l['inner'] else SPK[l['who']]
    hx, hy = pos[(k, who)]
    z = ZOOM.get(l['id'], 1.3 if not l['inner'] else 1.18)
    if l['id'] == 'l16':                       # everybody frozen: wide shot
        hx, hy = 540, 760
    fast = l['id'] in ('l11', 'l13', 'l14')
    t0 = l['start'] - (0.05 if fast else 0.35)
    to(f'#s{k}-cam', f'{{{cam(z, hx, hy)}, duration:{0.25 if fast else 0.8}, ease:"{"power4.out" if fast else "power2.inOut"}"}}', t0)
    to(f'#s{k}-cam', f'{{{cam(z * 1.05, hx, hy)}, duration:{max(0.5, l["dur"] - 0.3):.2f}, ease:"none"}}', t0 + (0.25 if fast else 0.8))
# Kenan slams the table on l11: shake
to('#stage', '{x:16, duration:0.045, yoyo:true, repeat:9, ease:"none"}', L['l11']['start'] + 0.05)
to('#stage', '{x:0, duration:0.04}', L['l11']['start'] + 0.52)
# l13: a beat of white then the line
to('#flash', '{opacity:0.7, duration:0.06}', L['l13']['start'] - 0.12)
to('#flash', '{opacity:0, duration:0.5}', L['l13']['start'] - 0.06)

# diary: pages of handwriting, then the last line
D = scenes[-1]['start']
to('#s5-cam', '{scale:1.08, x:-40, y:-60, duration:%.2f, ease:"sine.inOut"}' % (TOTAL - D), D)
fr('.dl', '{opacity:0, x:-20, duration:0.5, ease:"power2.out", stagger:0.55}', D + 0.6)
fr('#dlast', '{opacity:0, scale:1.15, duration:0.8, ease:"power2.out"}', L['l22']['start'] + 1.6)
to('#torch', '{x:60, y:40, duration:3, ease:"sine.inOut", yoyo:true, repeat:%d}' % max(1, int((TOTAL - D) / 3)), D)

# series chip + hook + title
fr('#chip', '{y:-120, duration:0.6, ease:"back.out(2)"}', 0.2)
fr('#hook', '{scale:0.6, opacity:0, duration:0.45, ease:"back.out(2.5)"}', 0.25)
to('#hook', '{opacity:0, y:-30, duration:0.35}', L['l02']['start'] + L['l02']['dur'] - 0.2)
to('#title-in', '{opacity:1, duration:0.35}', TS)
fr('#t1', '{y:80, opacity:0, duration:0.55, ease:"power3.out"}', TS + 0.15)
fr('#t2', '{scale:2.4, opacity:0, duration:0.5, ease:"power4.out"}', TS + 0.55)
fr('#t3', '{y:30, opacity:0, duration:0.4, ease:"power2.out"}', TS + 1.1)
to('#title-in', '{opacity:0, duration:0.3}', TE - 0.35)
st('#title-in', '{opacity:0}', TE - 0.04)

# end card
CT = SPEECH_END + 0.5
to('#end-in', '{opacity:1, duration:0.5}', CT)
fr('#e1', '{y:60, opacity:0, duration:0.55, ease:"back.out(2)"}', CT + 0.2)
fr('#e2', '{y:40, opacity:0, duration:0.45, ease:"power3.out"}', CT + 0.9)
fr('#e3', '{scale:0.3, opacity:0, duration:0.55, ease:"back.out(3)"}', CT + 1.6)
to('#e3', '{scale:1.07, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:5}', CT + 2.2)
to('#fade', '{opacity:1, duration:0.9, ease:"power1.in"}', TOTAL - 0.95)

# captions: words spread over the line by length (Chatterbox gives no timings)
COL = {'defne': '#ffb4c8', 'kenan': '#9fc4ff', 'nermin': '#ffcf7a', 'ali': '#a6f0c6'}
NAME = {'kenan': 'KENAN', 'nermin': 'NERMİN HANIM', 'ali': 'ALİ'}
caps, cid = [], 0
for l in lines:
    words = l['text'].split()
    tot = sum(len(w) + 1.5 for w in words)
    span = l['dur'] - 0.2
    acc, wt = 0.04, []
    for w in words:
        wt.append(acc); acc += (len(w) + 1.5) / tot * span
    chunks, c = [], []
    for j, w in enumerate(words):
        c.append(j)
        if len(c) >= 4 or (w[-1] in '.!?,' and len(c) >= 2):
            chunks.append(c); c = []
    if c:
        if chunks and len(c) == 1: chunks[-1] += c
        else: chunks.append(c)
    who = l['who']
    label = ('DEFNE · iç ses' if l['inner'] else 'ZEHRA') if who == 'defne' else NAME[who]
    for k, ch in enumerate(chunks):
        cid += 1
        t0 = l['start'] + wt[ch[0]] - 0.06
        t1 = l['start'] + (wt[chunks[k + 1][0]] - 0.06 if k + 1 < len(chunks) else l['dur'] + 0.2)
        spans = ''.join(f'<span class="w" id="c{cid}w{j}">{words[j]}</span> ' for j in ch)
        caps.append(f'<div class="cap{" inner" if l["inner"] else ""}" id="cap{cid}"><div class="who" style="background:{COL[who]}">{label}</div><div class="txt">{spans}</div></div>')
        st(f'#cap{cid}', '{opacity:1}', t0)
        for j in ch:
            fr(f'#c{cid}w{j}', '{y:14, opacity:0, duration:0.15, ease:"back.out(2)"}', l['start'] + wt[j] - 0.03)
        st(f'#cap{cid}', '{opacity:0}', t1)

LAT = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
EXT = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"
ff = ''
for fam, w, sty, base in [('BH Fredoka', 700, 'normal', 'fredoka-{}-700-normal'), ('BH Nunito', 900, 'normal', 'nunito-{}-900-normal'), ('BH Nunito', 800, 'italic', 'nunito-{}-800-italic')]:
    for sub, rng in [('latin', LAT), ('latin-ext', EXT)]:
        ff += '@font-face{font-family:"%s";font-weight:%d;font-style:%s;src:url(fonts/%s.woff2) format("woff2");unicode-range:%s}\n' % (fam, w, sty, base.format(sub), rng)

css = ff + '''
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#000}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#000}
#stage{position:absolute;inset:0}
.scene{position:absolute;inset:0;overflow:hidden;background:#000}
.cam{position:absolute;left:0;top:0;width:1080px;height:1920px;will-change:transform}
.cam svg{display:block}
#vig{position:absolute;inset:0;z-index:40;pointer-events:none;background:radial-gradient(ellipse at 50% 45%,rgba(0,0,0,0) 55%,rgba(0,0,0,0.45) 100%),linear-gradient(180deg,rgba(0,0,0,0.25) 0%,rgba(0,0,0,0) 14%,rgba(0,0,0,0) 62%,rgba(0,0,0,0.5) 100%)}
#grain{position:absolute;inset:0;z-index:41;pointer-events:none;opacity:0.06;background:repeating-linear-gradient(0deg,#000 0 2px,transparent 2px 4px)}
#flash{position:absolute;inset:0;z-index:45;background:#fff;opacity:0}
#fade{position:absolute;inset:0;z-index:99;background:#000;opacity:0}
#chip{position:absolute;left:50%;top:150px;margin-left:-400px;width:800px;white-space:nowrap;z-index:60;text-align:center;padding:12px 0;border-radius:40px;background:rgba(30,16,36,0.78);color:#fff;font:700 36px "BH Fredoka",sans-serif;letter-spacing:1px;border:3px solid #ff6f91}
#chip b{color:#ff6f91}
#hook{position:absolute;left:70px;right:70px;top:250px;z-index:61;text-align:center;font:900 64px/1.1 "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:12px #1d1022;paint-order:stroke fill}
#hook em{font-style:normal;color:#ff6f91}
.cap{position:absolute;left:46px;right:46px;bottom:400px;opacity:0;display:flex;flex-direction:column;align-items:center;gap:10px}
.who{padding:5px 22px;border-radius:30px;color:#1d1022;font:700 34px "BH Fredoka",sans-serif;letter-spacing:1px;border:4px solid #1d1022}
.txt{text-align:center;font:900 68px/1.15 "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:12px #1d1022;paint-order:stroke fill;max-width:990px}
.cap.inner .txt{font-style:italic;font-weight:800;color:#ffe3ec}
.w{display:inline-block}
#title{position:absolute;inset:0;z-index:80}
#title-in{position:absolute;inset:0;opacity:0;background:radial-gradient(ellipse at 50% 45%,#5a1f3a 0%,#2a0f22 60%,#12060f 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;padding:0 60px}
#t1{font:700 96px/1.02 "BH Fredoka",sans-serif;color:#fff;text-align:center}
#t2{font:700 132px/1 "BH Fredoka",sans-serif;color:#ff6f91;text-align:center;text-shadow:0 8px 0 #12060f}
#t3{padding:10px 36px;border-radius:40px;border:4px solid #fff;color:#fff;font:900 46px "BH Nunito",sans-serif}
#diary{position:absolute;left:170px;top:600px;width:740px;z-index:5;transform:rotate(-3deg);font:800 46px/60px "BH Nunito",sans-serif;font-style:italic;color:#2f3f6b}
.dl{display:block;height:60px}
#dlast{display:block;margin-top:60px;color:#9b1d3a;font-size:54px;line-height:66px}
#torch{position:absolute;left:-200px;top:200px;width:1500px;height:1500px;z-index:6;pointer-events:none;background:radial-gradient(circle at 50% 50%,rgba(255,230,160,0.0) 0%,rgba(255,230,160,0) 30%,rgba(10,6,14,0.55) 60%)}
#end{position:absolute;inset:0;z-index:85}
#end-in{position:absolute;inset:0;opacity:0;background:rgba(18,6,15,0.82);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px;padding:0 70px}
#e1{font:700 84px/1.08 "BH Fredoka",sans-serif;color:#fff;text-align:center}
#e1 span{color:#ff6f91}
#e2{font:900 54px/1.2 "BH Nunito",sans-serif;color:#ffe3ec;text-align:center}
#e3{padding:18px 50px;border-radius:50px;background:#ff6f91;color:#1d1022;font:700 66px "BH Fredoka",sans-serif;border:6px solid #fff}
'''
diary_lines = ['3 Mart — Bugün yine sustum.', 'Ali uyurken ağladım.', 'Kenan telefonu yine kilitledi.', 'O gece duyduklarımı', 'kimseye söyleyemem...']
hook = 'Ezilen bir kadının<br>bedeninde <em>uyandı</em>'
html = f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=1080, height=1920">
<script src="lib/gsap.min.js"></script><style>{css}</style></head><body>
<div id="root" data-composition-id="ezilmeyecegim-ep1" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
 <div id="stage">{''.join(scene_html)}</div>
 <div id="diarytext" class="clip" data-start="{scenes[-1]['start']}" data-duration="{round(TOTAL - scenes[-1]['start'], 3)}" data-track-index="3" style="position:absolute;inset:0;z-index:30">
  <div id="diary">{''.join(f'<span class="dl">{x}</span>' for x in diary_lines)}<span id="dlast">Yarın her şeyi anlatacağım...<br>Eğer bana bir şey olmazsa.</span></div><div id="torch"></div></div>
 <div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="4"></div>
 <div id="grain" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="5"></div>
 <div id="flash" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="6"></div>
 <div id="chip" class="clip" data-start="0" data-duration="{round(SPEECH_END, 3)}" data-track-index="7">BU SEFER EZİLMEYECEĞİM · <b>BÖLÜM 1</b></div>
 <div id="hook" class="clip" data-start="0" data-duration="{round(L['l02']['start'] + L['l02']['dur'] + 0.2, 3)}" data-track-index="8">{hook}</div>
 <div id="caps" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9" style="position:absolute;inset:0;z-index:70">{''.join(caps)}</div>
 <div id="title" class="clip" data-start="{round(TS, 3)}" data-duration="{round(TE - TS, 3)}" data-track-index="10"><div id="title-in">
  <div id="t1">BU SEFER</div><div id="t2">EZİLMEYECEĞİM</div><div id="t3">1. BÖLÜM · UYANIŞ</div></div></div>
 <div id="end" class="clip" data-start="{round(CT, 3)}" data-duration="{round(TOTAL - CT, 3)}" data-track-index="11"><div id="end-in">
  <div id="e1">Sizce Zehra'nın <span>sırrı</span> ne?</div><div id="e2">Tahminini yorumlara yaz.<br>Takip et, kaçırma.</div><div id="e3">BÖLÜM 2 YARIN</div></div></div>
 <div id="fade" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="12"></div>
 <audio id="mix" data-start="0" data-duration="{TOTAL}" data-track-index="13" src="assets/master.m4a" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["ezilmeyecegim-ep1"] = tl;
</script></body></html>'''
open(os.path.join(HERE, 'index.html'), 'w').write(html)
json.dump({'total': TOTAL, 'title': [TS, TE], 'end_card': CT, 'scenes': scenes,
           'lines': [{k: l[k] for k in ('id', 'who', 'scene', 'start', 'dur', 'text')} for l in lines]},
          open(os.path.join(HERE, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
print('index.html', len(html) // 1024, 'KB; total', TOTAL, 's; speech ends', round(SPEECH_END, 2))
if '--no-mix' in sys.argv:
    sys.exit(0)

# ------------------------------------------------------------------ audio
sfx = [(L['l01']['start'] - 0.25, 'sfx/impact-soft-1', 0.5), (L['l03']['start'] - 0.5, 'sfx/swell-soft-3s', 0.45),
       (L['l03']['start'] + 0.2, 'sfx/stinger-serious-low', 0.5), (TS, 'sfx/whoosh-long-2s', 0.4), (TS + 0.55, 'sfx/impact-soft-3', 0.6),
       (L['l08']['start'] - 0.6, 'sfx/whoosh-soft', 0.3), (L['l11']['start'] + 0.05, 'sfx/impact-wood-light', 0.9),
       (L['l11']['start'] + 0.12, 'sfx/dry-thud', 0.7), (L['l13']['start'] - 1.9, 'sfx/reverse-cymbal-2s', 0.45),
       (L['l13']['start'] - 0.12, 'sfx/impact-soft-2', 0.7), (L['l15']['start'] + L['l15']['dur'] + 0.1, 'sfx/stinger-pizzicato-short', 0.4),
       (L['l19']['start'] - 0.7, 'sfx/whoosh-soft', 0.25), (scenes[-1]['start'] + 0.1, 'sfx/book-open', 0.7),
       (scenes[-1]['start'] + 1.2, 'sfx/page-turn', 0.6), (L['l22']['start'] - 0.2, 'sfx/riser-medium-4s', 0.3),
       (L['l22']['start'] + 1.6, 'sfx/stinger-serious-low', 0.6), (CT + 1.6, 'sfx/stinger-outro-soft', 0.5)]
for s in scenes[1:]:
    if s['name'] not in ('door', 'diary'):
        sfx.append((s['start'], 'sfx/whoosh-short', 0.2))
inputs, f = [], []
def add(p):
    inputs.extend(['-i', p]); return inputs.count('-i') - 1
voice = []
for l in lines:
    i = add(os.path.join(VO, l['id'] + '.wav'))
    f.append(f'[{i}]volume={1.0 if not l["inner"] else 0.92},adelay={int(l["start"] * 1000)}:all=1[v{i}]'); voice.append(f'[v{i}]')
f.append(f'{"".join(voice)}amix=inputs={len(voice)}:normalize=0,apad,atrim=0:{TOTAL},asplit=2[vox][key]')
fx = []
for k, (t0, name, vol) in enumerate(sfx):
    i = add(os.path.join(LIB, name + '.wav'))
    f.append(f'[{i}]aresample=48000,volume={vol},adelay={int(t0 * 1000)}:all=1[s{k}]'); fx.append(f'[s{k}]')
f.append(f'{"".join(fx)}amix=inputs={len(fx)}:normalize=0,apad,atrim=0:{TOTAL}[fx]')
sec = [  # (start, end, file, volume)
    (0, TS + 0.3, os.path.join(LIB, 'music/music-tension-soft.mp3'), 0.5),
    (TE - 0.3, L['l08']['start'] - 0.4, os.path.join(LIB, 'music/music-emotional-piano-loop.mp3'), 0.45),
    (L['l08']['start'] - 0.6, L['l13']['start'] - 0.2, os.path.join(LIB, 'music/music-tension-22s.mp3'), 0.42),
    (L['l13']['start'] + 0.6, L['l19']['start'] - 0.3, os.path.join(LIB, 'music/music-inspiring-orchestral.mp3'), 0.45),
    (L['l19']['start'] - 0.8, scenes[-1]['start'] + 0.3, os.path.join(LIB, 'music/music-emotional-piano-loop.mp3'), 0.42),
    (scenes[-1]['start'], TOTAL, os.path.join(MUSIC2, 'thriller.mp3'), 0.5)]
mus = []
for k, (a0, a1, trk, vol) in enumerate(sec):
    i = add(trk); d0 = a1 - a0
    f.append(f'[{i}]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{d0:.2f},afade=t=in:d=0.8,afade=t=out:st={max(0, d0 - 0.9):.2f}:d=0.9,volume={vol},adelay={int(a0 * 1000)}:all=1[mu{k}]')
    mus.append(f'[mu{k}]')
f.append(f'{"".join(mus)}amix=inputs={len(mus)}:normalize=0,apad,atrim=0:{TOTAL}[mus]')
f.append('[mus][key]sidechaincompress=threshold=0.05:ratio=4:attack=25:release=350[duck]')
i = add(os.path.join(LIB, 'sfx/ambience-room-tone-30s.wav'))
f.append(f'[{i}]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{TOTAL},volume=0.35[amb]')
i = add(os.path.join(LIB, 'sfx/clock-tick.wav'))
nd = scenes[-1]['start'] - scenes[4]['start']
f.append(f'[{i}]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{nd:.2f},volume=0.12,adelay={int(scenes[4]["start"] * 1000)}:all=1,apad,atrim=0:{TOTAL}[tick]')
f.append(f'[vox][fx][duck][amb][tick]amix=inputs=5:normalize=0,afade=t=out:st={TOTAL - 1.0}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:{TOTAL}[out]')
out = os.path.join(HERE, 'assets', 'master.m4a')
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(f), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', out], check=True)
print('wrote', out)
