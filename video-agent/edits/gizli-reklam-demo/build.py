"""Gizli Reklam — örnek bölüm (uydurma kafe 'Kahve Durağı'). 70 s, text-on-screen + music.
Writes index.html (HyperFrames) and assets/master.m4a.  python3 build.py [--no-mix]"""
import json, os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LIB = os.path.join(ROOT, '.claude/skills/editing-videos/library')
SM = os.path.join(ROOT, '.claude/skills/short-editing/assets/music')
TOTAL = 70.0

# (image, start, end, ad_section, texts[(t_abs, text, kind)])   kind: hook | line | big | ad | brand | cta
SC = [
    ('c01', 0.0, 7.2, False, [(0.15, 'BU KAFENİN GİZLİ REKLAMINI YAPIYORUZ', 'hook'),
                             (2.7, 'Sahibinin hiç haberi yok...', 'line'),
                             (4.7, 'Video tutarsa kafeyi etiketleyin, haberi olsun!', 'line')]),
    ('c03', 7.2, 13.6, False, [(7.6, 'Saat 15:00.', 'line'), (9.8, 'İçeride tek bir müşteri yok.', 'line')]),
    ('c02', 13.6, 22.0, False, [(14.0, 'Bu Kemal Usta.', 'line'), (16.2, '28 yıldır her sabah 07:00\'de kapıyı açıyor.', 'line'),
                               (19.2, 'Son haftalarda kimse uğramıyor.', 'line')]),
    ('black', 22.0, 25.2, False, [(22.2, 'O zaman reklamını biz yapalım.', 'big')]),
    ('c05', 25.2, 31.4, True, [(25.8, 'Her fincan, elde.', 'ad')]),
    ('c06', 31.4, 37.6, True, [(32.0, 'Ev yapımı San Sebastian.', 'ad')]),
    ('c07', 37.6, 44.2, True, [(38.2, 'Yağmurlu akşamların en sıcak köşesi.', 'ad')]),
    ('c09', 44.2, 52.4, True, [(44.8, 'Kemal Usta seni bekliyor.', 'ad'), (47.6, 'KAHVE DURAĞI', 'brand')]),
    ('c08', 52.4, 60.4, False, [(53.0, 'Hadi bu kafeyi birlikte dolduralım.', 'line'), (56.4, 'Bugün bir kahve için.', 'line')]),
    ('cta', 60.4, TOTAL, False, []),
]

js = []
def a(x): js.append(x)
def to(sel, props, t): a(f'tl.to({json.dumps(sel)}, {props}, {round(t, 3)});')
def fr(sel, props, t): a(f'tl.from({json.dumps(sel)}, {props}, {round(t, 3)});')
def st(sel, props, t): a(f'tl.set({json.dumps(sel)}, {props}, {round(t, 3)});')

MOVES = [(1.04, 1.2, 0, -30, 0, -50), (1.2, 1.05, -30, 30, -40, 10), (1.05, 1.22, 30, -20, 30, -30), (1.18, 1.04, 0, 0, -50, 30)]
scene_html, text_html, cuts = [], [], []
for k, (img, s0, s1, ad, texts) in enumerate(SC):
    sid = f'sc{k}'
    if img == 'black':
        inner = '<div class="blackcard"></div>'
    elif img == 'cta':
        inner = '<div class="kb" id="sc{0}-kb"><img src="scenes/c08.jpg" alt=""></div>'.format(k)
    else:
        inner = f'<div class="kb" id="{sid}-kb"><img src="scenes/{img}.jpg" alt=""></div>'
    vis = ';opacity:0' if k > 0 else ''
    scene_html.append(f'<div class="scene clip{" ad" if ad else ""}" id="{sid}" data-start="{s0}" data-duration="{round(s1 - s0 + 0.4, 3)}" data-track-index="{1 + k % 2}" style="z-index:{10 + k}{vis}">{inner}</div>')
    if img not in ('black',):
        f0, f1, x0, x1, y0, y1 = MOVES[k % len(MOVES)]
        st(f'#{sid}-kb', f'{{scale:{f0}, x:{x0}, y:{y0}, transformOrigin:"50% 50%"}}', s0)
        to(f'#{sid}-kb', f'{{scale:{f1}, x:{x1}, y:{y1}, duration:{round(s1 - s0 + 0.4, 2)}, ease:"sine.inOut"}}', s0)
    if k > 0:
        cuts.append(s0)
        if ad or SC[k - 1][3]:
            to(f'#{sid}', '{opacity:1, duration:0.7, ease:"sine.inOut"}', s0)
        else:
            st(f'#{sid}', '{scale:1.15}', s0)
            to(f'#{sid}', '{opacity:1, scale:1, duration:0.32, ease:"power3.out"}', s0)
            to('#flash', '{opacity:0.5, duration:0.06}', s0)
            to('#flash', '{opacity:0, duration:0.3}', s0 + 0.06)
            st('#flash', '{opacity:0}', s0 + 0.38)
    nxt = [t for t, _, _ in texts[1:]] + [s1 + 0.2]
    for j, (t0, txt, kind) in enumerate(texts):
        tid = f't{k}_{j}'
        end = nxt[j] - 0.1 if kind in ('line',) else s1 + 0.2
        text_html.append(f'<div class="tx {kind} clip" id="{tid}" data-start="{round(t0, 3)}" data-duration="{round(end - t0, 3)}" data-track-index="{20 + j}"><span>{txt}</span></div>')
        if kind == 'hook':
            fr(f'#{tid}', '{scale:2.2, opacity:0, duration:0.35, ease:"power4.out"}', t0)
            to(f'#{tid}', '{scale:1.05, duration:0.12, yoyo:true, repeat:1}', t0 + 0.45)
        elif kind == 'big':
            fr(f'#{tid}', '{y:60, opacity:0, duration:0.5, ease:"back.out(2)"}', t0)
        elif kind == 'ad':
            fr(f'#{tid}', '{y:30, scale:1.08, opacity:0, duration:1.0, ease:"power2.out"}', t0)
        elif kind == 'brand':
            fr(f'#{tid}', '{scale:0.6, opacity:0, duration:0.8, ease:"expo.out"}', t0)
        else:
            fr(f'#{tid}', '{y:24, opacity:0, duration:0.3, ease:"back.out(2.5)"}', t0)

# letterbox bars during the ad
AD0, AD1 = SC[4][1], SC[7][2]
fr('#bars-top', '{yPercent:-100, duration:0.6, ease:"power3.out"}', AD0)
fr('#bars-bot', '{yPercent:100, duration:0.6, ease:"power3.out"}', AD0)
to('#bars-top', '{yPercent:-100, duration:0.5, ease:"power2.in"}', AD1 - 0.5)
to('#bars-bot', '{yPercent:100, duration:0.5, ease:"power2.in"}', AD1 - 0.5)
fr('#adlabel', '{opacity:0, duration:0.6}', AD0 + 0.3)

# badge + demo tag
fr('#badge', '{x:-320, duration:0.5, ease:"back.out(2)"}', 0.4)
# call to action
C0 = SC[9][1]
to('#sc9-kb', '{filter:"blur(12px) brightness(0.4)", duration:0.6}', C0)
st('#sc9-kb', '{filter:"blur(0px) brightness(1)"}', 0)
fr('#cta-1', '{y:-60, opacity:0, duration:0.5, ease:"back.out(2)"}', C0 + 0.3)
fr('#cta-2', '{scale:0.5, opacity:0, duration:0.5, ease:"back.out(3)"}', C0 + 2.6)
fr('#cta-3', '{y:40, opacity:0, duration:0.45, ease:"power3.out"}', C0 + 4.4)
fr('#cta-4', '{scale:0.3, opacity:0, duration:0.6, ease:"elastic.out(1,0.5)"}', C0 + 6.4)
to('#cta-2', '{scale:1.06, duration:0.4, yoyo:true, repeat:5, ease:"sine.inOut"}', C0 + 3.3)
to('#fade', '{opacity:1, duration:0.9, ease:"power1.in"}', TOTAL - 0.95)

LAT = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
EXT = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"
ff = ''
for fam, w, sty, base in [('BH Fredoka', 700, 'normal', 'fredoka-{}-700-normal'), ('BH Nunito', 900, 'normal', 'nunito-{}-900-normal'), ('BH Nunito', 800, 'italic', 'nunito-{}-800-italic')]:
    for sub, rng in [('latin', LAT), ('latin-ext', EXT)]:
        ff += '@font-face{font-family:"%s";font-weight:%d;font-style:%s;src:url(fonts/%s.woff2) format("woff2");unicode-range:%s}\n' % (fam, w, sty, base.format(sub), rng)
css = ff + '''
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0d0d0d}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#0d0d0d}
.scene{position:absolute;inset:0;overflow:hidden;background:#0d0d0d}
.kb{position:absolute;inset:-24px;will-change:transform}
.kb img{width:100%;height:100%;object-fit:cover;display:block}
.blackcard{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 50%,#2a1a10 0%,#0d0d0d 70%)}
#shade{position:absolute;inset:0;z-index:40;pointer-events:none;background:linear-gradient(180deg,rgba(0,0,0,0.45) 0%,rgba(0,0,0,0) 22%,rgba(0,0,0,0) 50%,rgba(0,0,0,0.6) 100%)}
#flash{position:absolute;inset:0;z-index:45;background:#fff;opacity:0}
#fade{position:absolute;inset:0;z-index:99;background:#000;opacity:0}
.bar{position:absolute;left:0;right:0;height:190px;background:#000;z-index:46}
#bars-top{top:0} #bars-bot{bottom:0}
#adlabel{position:absolute;top:70px;left:0;right:0;text-align:center;z-index:47;color:#d9b779;font:700 34px "BH Fredoka",sans-serif;letter-spacing:10px}
#badge{position:absolute;left:46px;top:150px;z-index:60;padding:10px 24px;border-radius:14px;background:#111;color:#ffd166;font:700 38px "BH Fredoka",sans-serif;letter-spacing:3px;border:3px solid #ffd166}
#demo{position:absolute;right:40px;top:158px;z-index:60;padding:6px 16px;border-radius:10px;background:rgba(255,255,255,0.85);color:#111;font:900 26px "BH Nunito",sans-serif}
.tx{position:absolute;left:60px;right:60px;z-index:55;display:flex;justify-content:center;text-align:center}
.tx span{display:inline-block}
.tx.hook{top:520px}
.tx.hook span{font:700 104px/1.04 "BH Fredoka",sans-serif;color:#fff;-webkit-text-stroke:12px #111;paint-order:stroke fill;text-shadow:0 10px 0 #ff3b5c}
.tx.line{bottom:470px}
.tx.line span{font:900 70px/1.15 "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:12px #111;paint-order:stroke fill;max-width:960px}
.tx.big{top:820px}
.tx.big span{font:700 96px/1.08 "BH Fredoka",sans-serif;color:#ffd166;-webkit-text-stroke:10px #111;paint-order:stroke fill}
.tx.ad{bottom:300px}
.tx.ad span{font:800 italic 64px/1.2 "BH Nunito",sans-serif;color:#fff4e0;letter-spacing:2px;text-shadow:0 4px 30px rgba(0,0,0,0.8)}
.tx.brand{top:300px}
.tx.brand span{font:700 120px/1 "BH Fredoka",sans-serif;color:#fff;letter-spacing:12px;text-shadow:0 6px 40px rgba(0,0,0,0.85);border-top:4px solid #d9b779;border-bottom:4px solid #d9b779;padding:18px 10px}
#cta{position:absolute;inset:0;z-index:80;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:44px;padding:0 60px}
#cta-1{font:900 66px/1.15 "BH Nunito",sans-serif;color:#fff;text-align:center;-webkit-text-stroke:10px #111;paint-order:stroke fill}
#cta-2{padding:30px 40px;border-radius:36px;background:#ff3b5c;color:#fff;font:700 78px/1.08 "BH Fredoka",sans-serif;text-align:center;border:7px solid #111;box-shadow:0 14px 0 #111}
#cta-3{font:900 58px/1.15 "BH Nunito",sans-serif;color:#ffd166;text-align:center;-webkit-text-stroke:9px #111;paint-order:stroke fill}
#cta-4{padding:12px 40px;border-radius:50px;background:#ffd166;color:#111;font:700 54px "BH Fredoka",sans-serif;border:6px solid #111}
'''
html = f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=1080, height=1920">
<script src="lib/gsap.min.js"></script><style>{css}</style></head><body>
<div id="root" data-composition-id="gizli-reklam-demo" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
 {''.join(scene_html)}
 <div id="shade" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="3"></div>
 <div id="bars-top" class="bar clip" data-start="{AD0}" data-duration="{round(AD1 - AD0, 3)}" data-track-index="4"></div>
 <div id="bars-bot" class="bar clip" data-start="{AD0}" data-duration="{round(AD1 - AD0, 3)}" data-track-index="5"></div>
 <div id="adlabel" class="clip" data-start="{AD0}" data-duration="{round(AD1 - AD0, 3)}" data-track-index="6">REKLAM</div>
 <div id="badge" class="clip" data-start="0" data-duration="{SC[9][1]}" data-track-index="7">GİZLİ REKLAM #1</div>
 <div id="demo" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="8">ÖRNEK BÖLÜM</div>
 {''.join(text_html)}
 <div id="cta" class="clip" data-start="{SC[9][1]}" data-duration="{round(TOTAL - SC[9][1], 3)}" data-track-index="9">
  <div id="cta-1">Kemal Usta'yı etiketleyin, bu video ona ulaşsın!</div>
  <div id="cta-2">YARIN KİMİN GİZLİ REKLAMINI YAPALIM?</div>
  <div id="cta-3">Mahallendeki kafeyi yorumlara yaz!</div>
  <div id="cta-4">BÖLÜM 1</div></div>
 <div id="flash" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="10"></div>
 <div id="fade" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="11"></div>
 <audio id="mix" data-start="0" data-duration="{TOTAL}" data-track-index="12" src="assets/master.m4a" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["gizli-reklam-demo"] = tl;
</script></body></html>'''
open(os.path.join(HERE, 'index.html'), 'w').write(html)
print('index.html', len(html) // 1024, 'KB')
if '--no-mix' in sys.argv:
    sys.exit(0)

# ---------------------------------------------------------------- audio
os.makedirs(os.path.join(HERE, 'assets'), exist_ok=True)
inputs, f = [], []
def add(p):
    inputs.extend(['-i', p]); return inputs.count('-i') - 1
def sfx(name): return os.path.join(LIB, 'sfx', name + '.wav')
ev = [(0.1, 'impact-soft-2', 0.8), (0.12, 'whoosh-short', 0.5)]
for img, s0, s1, ad, texts in SC:
    for t0, _, kind in texts:
        if kind in ('line', 'big'): ev.append((t0, 'pop-2', 0.35))
for c in [s for _, s, _, _, _ in SC[1:4]] + [SC[8][1], SC[9][1]]:
    ev.append((c - 0.15, 'whoosh-short', 0.4))
ev += [(SC[3][1] - 2.0, 'riser-short-2s', 0.5), (SC[3][1], 'stinger-hit-short', 0.6), (SC[4][1] - 0.9, 'reverse-cymbal-2s', 0.5),
       (SC[7][1] + 3.4, 'stinger-win-strings', 0.5), (SC[9][1] + 2.6, 'stinger-energetic-hit', 0.5), (SC[9][1] + 6.4, 'pop-2', 0.6)]
fx = []
for k, (t0, n, v) in enumerate(ev):
    i = add(sfx(n)); f.append(f'[{i}]aresample=48000,volume={v},adelay={int(max(0, t0) * 1000)}[s{k}]'); fx.append(f'[s{k}]')
f.append(f'{"".join(fx)}amix=inputs={len(fx)}:normalize=0,apad,atrim=0:{TOTAL}[fx]')
secs = [(0, SC[3][1] + 0.3, os.path.join(SM, 'filature.mp3'), 0.8),
        (SC[3][1] + 0.2, TOTAL, os.path.join(LIB, 'music', 'music-inspiring-orchestral.mp3'), 0.85)]
mus = []
for k, (a0, a1, p, vol) in enumerate(secs):
    i = add(p); d0 = a1 - a0
    f.append(f'[{i}]aresample=48000,atrim=0:{d0:.2f},afade=t=in:d=0.4,afade=t=out:st={max(0, d0 - 1.0):.2f}:d=1.0,volume={vol},adelay={int(a0 * 1000)}[m{k}]')
    mus.append(f'[m{k}]')
i = add(os.path.join(LIB, 'sfx', 'ambience-room-tone-30s.wav'))
f.append(f'[{i}]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{SC[3][1] - SC[1][1]:.2f},volume=0.4,adelay={int(SC[1][1] * 1000)}[amb]')
f.append(f'{"".join(mus)}[fx][amb]amix=inputs={len(mus) + 2}:normalize=0,apad,atrim=0:{TOTAL},afade=t=out:st={TOTAL - 1.0}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[out]')
out = os.path.join(HERE, 'assets', 'master.m4a')
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(f), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', out], check=True)
print('wrote', out)
