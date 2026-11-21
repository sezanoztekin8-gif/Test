"""30 Günde Futbolcu — episode 1. Plans the timeline, writes index.html (HyperFrames) and mixes assets/master.m4a.
Usage: python3 build.py [--no-mix]"""
import json, os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SFX = os.path.join(ROOT, '.claude/skills/editing-videos/library/sfx')
MUSIC = os.path.join(ROOT, '.claude/skills/short-editing/assets/music')
TOTAL = None
S = json.load(open(os.path.join(HERE, 'script.json')))
TTS = os.path.join(HERE, 'assets', 'tts')

def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))

# ------------------------------------------------------------------ timeline
lines = S['lines']
for l in lines:
    l['dur'] = dur(os.path.join(TTS, l['id'] + '.mp3'))
    l['al'] = json.load(open(os.path.join(TTS, l['id'] + '.json')))
TITLE_AFTER, TITLE_LEN, TAIL = 'l03', 4.2, 9.0
pre = {}
for i, l in enumerate(lines):
    new_scene = i == 0 or l['img'] != lines[i - 1]['img']
    pre[l['id']] = 0.5 if i == 0 else (0.75 if new_scene else 0.3)
pre['l04'] += TITLE_LEN
TOTAL = round(sum(pre.values()) + sum(l['dur'] for l in lines) + TAIL, 2)
t = 0
for l in lines:
    t += pre[l['id']]; l['start'] = round(t, 3); t += l['dur']
L = {l['id']: l for l in lines}
def wt(lid, word):
    l = L[lid]; al = l['al']; chars = al['characters']; txt = ''.join(chars).lower(); i = txt.find(word.lower())
    return l['start'] + (al['character_start_times_seconds'][i] if i >= 0 else 0)
TS = L[TITLE_AFTER]['start'] + L[TITLE_AFTER]['dur'] + 0.5
TE = TS + TITLE_LEN - 0.4

# scenes: each image from (first line start - lead) to next scene start
scenes = []
for i, l in enumerate(lines):
    if i == 0 or l['img'] != lines[i - 1]['img']:
        scenes.append({'img': l['img'], 'start': 0.0 if i == 0 else round(l['start'] - 0.45, 3), 'first': l['id']})
for k, s in enumerate(scenes):
    s['end'] = scenes[k + 1]['start'] if k + 1 < len(scenes) else TOTAL
# the title card sits between scene s02 and s04
for s in scenes:
    if s['img'] == 's04':
        s['start'] = round(TE, 3)
    if s['img'] == 's02':
        s['end'] = round(TE, 3)

# ------------------------------------------------------------------ html
js = []
def a(x): js.append(x)
def to(sel, props, t): a(f'tl.to({json.dumps(sel)}, {props}, {round(t, 3)});')
def fr(sel, props, t): a(f'tl.from({json.dumps(sel)}, {props}, {round(t, 3)});')
def st(sel, props, t): a(f'tl.set({json.dumps(sel)}, {props}, {round(t, 3)});')

MOVES = [  # Ken Burns: (from scale, to scale, from x, to x, from y, to y)
    (1.05, 1.22, 0, -40, 0, -60), (1.22, 1.06, -40, 30, -50, 10), (1.06, 1.24, 40, -20, 30, -40),
    (1.2, 1.05, 0, 0, -60, 30), (1.05, 1.2, -45, 40, 0, -45)]
PUNCH = {'l11': ('kanepe', 0), 'l13': ('merdiven', 0), 'l20b': ('dede!', 0)}
scene_html = []
for k, s in enumerate(scenes):
    sid = f'sc{k}'
    if s['img'] == 'cta':
        bg = 'scenes/s16.jpg'
    else:
        bg = f"scenes/{s['img']}.jpg"
    scene_html.append(f'<div class="scene clip" id="{sid}" data-start="{s["start"]}" data-duration="{round(s["end"] - s["start"] + (0.5 if k + 1 < len(scenes) else 0), 3)}" data-track-index="{1 + k % 2}" style="z-index:{10 + k}{';opacity:0' if k > 0 else ''}">'
                      f'<div class="kb" id="{sid}-kb"><img src="{bg}" alt=""></div></div>')
    f0, f1, x0, x1, y0, y1 = MOVES[k % len(MOVES)]
    d = s['end'] - s['start'] + 0.5
    st(f'#{sid}-kb', f'{{scale:{f0}, x:{x0}, y:{y0}, transformOrigin:"50% 50%"}}', s['start'])
    to(f'#{sid}-kb', f'{{scale:{f1}, x:{x1}, y:{y1}, duration:{round(d, 2)}, ease:"sine.inOut"}}', s['start'])
    if k > 0:   # transition in: soft zoom-fade over the previous scene
        to(f'#{sid}', '{opacity:1, duration:0.6, ease:"sine.inOut"}', s['start'])
for lid, (wd, _) in PUNCH.items():
    tp = wt(lid, wd)
    sc = next(k for k, s in enumerate(scenes) if s['start'] <= tp < s['end'])
    to(f'#sc{sc}', '{scale:1.12, duration:0.18, ease:"power4.out"}', tp)
    to(f'#sc{sc}', '{scale:1, duration:0.9, ease:"power2.inOut"}', tp + 0.9)
# the miss: shake
ms = wt('l15', 'ıskal')
to('#stage', '{x:14, duration:0.05, yoyo:true, repeat:9, ease:"none"}', ms)
to('#stage', '{x:0, duration:0.05}', ms + 0.55)

# day chip and countdown
fr('#day', '{x:-300, duration:0.6, ease:"back.out(2)"}', 0.3)
fr('#count', '{x:-300, duration:0.6, ease:"power3.out"}', 0.55)

# title card
fr('#title', '{clipPath:"circle(0% at 50% 50%)", duration:0.6, ease:"power3.inOut"}', TS)
fr('#t-ball', '{y:-500, rotation:-360, duration:0.9, ease:"bounce.out"}', TS + 0.2)
fr('#t-1', '{x:-600, duration:0.55, ease:"power4.out"}', TS + 0.6)
fr('#t-2', '{x:600, duration:0.55, ease:"expo.out"}', TS + 0.8)
fr('#t-sub', '{scale:0.3, opacity:0, duration:0.6, ease:"back.out(3)"}', TS + 1.4)
to('#title', '{clipPath:"circle(0% at 50% 50%)", duration:0.45, ease:"power3.in"}', TE - 0.45)

# phone message bubble on s17
mt = wt('l20', 'elif')
fr('#msg', '{y:-220, opacity:0, duration:0.55, ease:"back.out(2)"}', mt)
to('#msg', '{y:-220, opacity:0, duration:0.4, ease:"power2.in"}', L['l21']['start'] - 1.2)
# notebook stamp on s16
fr('#note', '{scale:2.2, rotation:-20, opacity:0, duration:0.45, ease:"back.out(2)"}', wt('l19', 'yirmi'))
to('#note', '{opacity:0, duration:0.3}', L['l20']['start'] - 1.0)

# call to action
CT = L['l21']['start'] - 0.6
to('#sc' + str(len(scenes) - 1) + '-kb', '{filter:"blur(10px) brightness(0.45)", duration:0.6}', CT)
fr('#cta-head', '{y:-80, opacity:0, duration:0.6, ease:"back.out(2)"}', CT + 0.3)
fr('.bar', '{scaleX:0, transformOrigin:"0% 50%", duration:0.7, ease:"power3.out", stagger:0.2}', CT + 0.8)
fr('.stat', '{x:-40, opacity:0, duration:0.4, ease:"power2.out", stagger:0.2}', CT + 0.7)
fr('#btn-a', '{x:-320, rotation:-12, opacity:0, duration:0.55, ease:"back.out(2.5)"}', L['l21']['start'] + 3.4)
fr('#btn-b', '{x:320, rotation:12, opacity:0, duration:0.55, ease:"back.out(2.5)"}', L['l21']['start'] + 4.0)
fr('#cta-write', '{y:40, opacity:0, duration:0.45, ease:"power3.out"}', L['l21']['start'] + 6.0)
to('#btn-a', '{scale:1.06, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:9}', L['l21']['start'] + 4.2)
to('#btn-b', '{scale:1.06, duration:0.45, ease:"sine.inOut", yoyo:true, repeat:9}', L['l21']['start'] + 4.65)
fr('#cta-next', '{scale:0.3, opacity:0, duration:0.6, ease:"back.out(3)"}', L['l21']['start'] + L['l21']['dur'] + 0.4)
to('#fade', '{opacity:1, duration:1.0, ease:"power1.in"}', TOTAL - 1.05)
st('#sc' + str(len(scenes) - 1) + '-kb', '{filter:"blur(0px) brightness(1)"}', 0)

# captions
COL = {'anlatici': '#9fd3ff', 'emre': '#ff6b6b', 'dede': '#ffd166', 'burak': '#06d6a0'}
NAME = {'anlatici': 'ANLATICI', 'emre': 'EMRE', 'dede': 'HÜSNÜ DEDE', 'burak': 'BURAK'}
caps, cid = [], 0
for l in lines:
    al = l['al']; words, cur, intag = [], '', False
    for ch, s, e in zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']):
        if ch == '[': intag = True; continue
        if ch == ']': intag = False; continue
        if intag: continue
        if ch == ' ':
            if cur: words.append((cur, cs, pe)); cur = ''
            continue
        if not cur: cs = s
        cur += ch; pe = e
    if cur: words.append((cur, cs, pe))
    chunks, c = [], []
    for w in words:
        c.append(w)
        if len(c) >= 5 or (w[0][-1] in '.!?:,' and len(c) >= 3):
            chunks.append(c); c = []
    if c:
        if chunks and len(c) <= 1: chunks[-1] += c
        else: chunks.append(c)
    for k, ch in enumerate(chunks):
        cid += 1
        t0 = l['start'] + ch[0][1] - 0.08
        t1 = l['start'] + (chunks[k + 1][0][1] - 0.1 if k + 1 < len(chunks) else l['dur'] + 0.25)
        narr = ' narr' if l['who'] == 'anlatici' else ''
        spans = ''.join(f'<span class="w" id="c{cid}w{j}">{w[0]}</span> ' for j, w in enumerate(ch))
        caps.append(f'<div class="cap{narr}" id="cap{cid}"><div class="chip" style="background:{COL[l["who"]]}">{NAME[l["who"]]}</div><div class="txt">{spans}</div></div>')
        st(f'#cap{cid}', '{opacity:1}', t0)
        for j, w in enumerate(ch):
            fr(f'#c{cid}w{j}', '{y:16, opacity:0, duration:0.16, ease:"back.out(2.5)"}', l['start'] + w[1] - 0.04)
        st(f'#cap{cid}', '{opacity:0}', t1)

LAT = "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"
EXT = "U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF"
ff = ''
for fam, w, sty, base in [('BH Fredoka', 700, 'normal', 'fredoka-{}-700-normal'), ('BH Nunito', 900, 'normal', 'nunito-{}-900-normal'), ('BH Nunito', 800, 'italic', 'nunito-{}-800-italic')]:
    for sub, rng in [('latin', LAT), ('latin-ext', EXT)]:
        ff += '@font-face{font-family:"%s";font-weight:%d;font-style:%s;src:url(fonts/%s.woff2) format("woff2");unicode-range:%s}\n' % (fam, w, sty, base.format(sub), rng)

css = ff + '''
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#111}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#111}
#stage{position:absolute;inset:0}
.scene{position:absolute;inset:0;overflow:hidden;background:#111}
.kb{position:absolute;inset:-20px;will-change:transform}
.kb img{width:100%;height:100%;object-fit:cover;display:block}
#vig{position:absolute;inset:0;z-index:40;pointer-events:none;background:linear-gradient(180deg,rgba(0,0,0,0.35) 0%,rgba(0,0,0,0) 18%,rgba(0,0,0,0) 55%,rgba(0,0,0,0.55) 100%)}
#whiteflash{position:absolute;inset:0;z-index:45;background:#fff;opacity:0}
#fade{position:absolute;inset:0;z-index:99;background:#000;opacity:0}
#day{position:absolute;left:50px;top:170px;z-index:60;padding:10px 26px;border-radius:40px;background:#ff3b5c;color:#fff;font:700 46px "BH Fredoka",sans-serif;box-shadow:0 6px 0 #1b1b2f;border:4px solid #1b1b2f}
#count{position:absolute;left:50px;top:256px;z-index:60;padding:6px 20px;border-radius:30px;background:rgba(20,20,40,0.75);color:#fff;font:900 34px "BH Nunito",sans-serif}
.cap{position:absolute;left:50px;right:50px;bottom:420px;z-index:70;opacity:0;display:flex;flex-direction:column;align-items:center;gap:12px}
.chip{padding:5px 22px;border-radius:30px;color:#1b1b2f;font:700 36px "BH Fredoka",sans-serif;letter-spacing:2px;border:4px solid #1b1b2f}
.txt{text-align:center;font:900 70px/1.16 "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:12px #111;paint-order:stroke fill;max-width:980px}
.cap.narr .txt{font-style:italic;font-weight:800;color:#fff7d6}
.w{display:inline-block}
#title{position:absolute;inset:0;z-index:80;clip-path:circle(150% at 50% 50%);background:radial-gradient(ellipse at 50% 40%,#2f8f4e 0%,#14532d 60%,#0b2e1a 100%);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;padding:0 50px}
#title:before{content:"";position:absolute;left:50%;top:0;bottom:0;width:8px;background:rgba(255,255,255,0.25)}
#title:after{content:"";position:absolute;left:50%;top:50%;width:420px;height:420px;margin:-210px 0 0 -210px;border:8px solid rgba(255,255,255,0.25);border-radius:50%}
#t-ball{width:170px;height:170px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#fff 0%,#e9e9e9 60%,#bdbdbd 100%);border:8px solid #111;position:relative;z-index:2}
#t-ball:before{content:"";position:absolute;left:50%;top:50%;width:54px;height:54px;margin:-27px 0 0 -27px;background:#111;clip-path:polygon(50% 0,100% 38%,82% 100%,18% 100%,0 38%)}
.tl{position:relative;z-index:2;font:700 128px/1 "BH Fredoka",sans-serif;color:#fff;text-align:center;-webkit-text-stroke:10px #111;paint-order:stroke fill;text-shadow:0 10px 0 #ff3b5c}
#t-2{font-size:150px;color:#ffd166}
#t-sub{position:relative;z-index:2;padding:12px 34px;border-radius:50px;background:#ff3b5c;color:#fff;font:900 54px "BH Nunito",sans-serif;border:6px solid #111}
#msg{position:absolute;left:90px;right:90px;top:430px;z-index:65;background:#fff;border-radius:36px;padding:26px 34px;box-shadow:0 14px 40px rgba(0,0,0,0.45);display:flex;flex-direction:column;gap:8px;border:5px solid #111}
#msg .from{font:700 36px "BH Fredoka",sans-serif;color:#ff3b5c}
#msg .body{font:900 56px/1.15 "BH Nunito",sans-serif;color:#111}
#note{position:absolute;left:250px;top:560px;z-index:65;padding:18px 40px;border:10px solid #ff3b5c;border-radius:24px;color:#ff3b5c;font:700 92px "BH Fredoka",sans-serif;transform:rotate(-8deg);background:rgba(255,255,255,0.85)}
#cta{position:absolute;inset:0;z-index:85;display:flex;flex-direction:column;align-items:center;gap:30px;padding:330px 60px 0}
#cta-head{font:700 84px/1.05 "BH Fredoka",sans-serif;color:#fff;text-align:center;-webkit-text-stroke:10px #111;paint-order:stroke fill;text-shadow:0 10px 0 #ff3b5c}
.stats{width:860px;display:flex;flex-direction:column;gap:18px;background:rgba(10,10,25,0.7);border-radius:30px;padding:26px 34px;border:4px solid rgba(255,255,255,0.25)}
.stat{display:flex;align-items:center;gap:20px;font:900 40px "BH Nunito",sans-serif;color:#fff}
.stat span{width:250px}
.track{flex:1;height:30px;border-radius:15px;background:rgba(255,255,255,0.18);overflow:hidden}
.bar{height:100%;border-radius:15px}
.stat b{width:110px;text-align:right;font-variant-numeric:tabular-nums}
.btns{display:flex;gap:40px;margin-top:10px}
.btn{width:400px;padding:36px 0;border-radius:40px;border:8px solid #111;text-align:center;font:700 100px "BH Fredoka",sans-serif;color:#fff;box-shadow:0 14px 0 #111;-webkit-text-stroke:6px #111;paint-order:stroke fill}
#btn-a{background:#ff8a3d} #btn-b{background:#2ec4b6}
#cta-write{font:900 52px "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:8px #111;paint-order:stroke fill}
#cta-next{padding:12px 40px;border-radius:50px;background:#ff3b5c;color:#fff;font:700 54px "BH Fredoka",sans-serif;border:6px solid #111}
'''
last = len(scenes) - 1
html = f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=1080, height=1920">
<script src="lib/gsap.min.js"></script><style>{css}</style></head><body>
<div id="root" data-composition-id="futbolcu-ep1" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
 <div id="stage">{''.join(scene_html)}</div>
 <div id="vig" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="3"></div>
 <div id="whiteflash" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="4"></div>
 <div id="day" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="5">GÜN 1/30</div>
 <div id="count" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="6">Seçmelere 29 gün</div>
 <div id="note" class="clip" data-start="{L['l19']['start']}" data-duration="{round(L['l20']['start'] - L['l19']['start'], 3)}" data-track-index="7">29 GÜN!</div>
 <div id="msg" class="clip" data-start="{L['l20']['start']}" data-duration="{round(L['l21']['start'] - L['l20']['start'], 3)}" data-track-index="8"><div class="from">Elif</div><div class="body">Yarın sahada mısın?</div></div>
 <div id="caps" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="9" style="position:absolute;inset:0;z-index:70">{''.join(caps)}</div>
 <div id="title" class="clip" data-start="{round(TS, 3)}" data-duration="{round(TE - TS, 3)}" data-track-index="10">
  <div id="t-ball"></div><div class="tl" id="t-1">30 GÜNDE</div><div class="tl" id="t-2">FUTBOLCU</div><div id="t-sub">1. GÜN · İLK DÜDÜK</div></div>
 <div id="cta" class="clip" data-start="{round(CT, 3)}" data-duration="{round(TOTAL - CT, 3)}" data-track-index="11">
  <div id="cta-head">EMRE YARIN NE YAPSIN?</div>
  <div class="stats">
   <div class="stat"><span>Kondisyon</span><div class="track"><div class="bar" style="width:3%;background:#ff6b6b"></div></div><b>%3</b></div>
   <div class="stat"><span>Teknik</span><div class="track"><div class="bar" style="width:2%;background:#ffd166"></div></div><b>%1</b></div>
   <div class="stat"><span>Özgüven</span><div class="track"><div class="bar" style="width:12%;background:#06d6a0"></div></div><b>%12</b></div>
  </div>
  <div class="btns"><div class="btn" id="btn-a">KOŞU</div><div class="btn" id="btn-b">TOP</div></div>
  <div id="cta-write">Yorumlara tek kelime yaz!</div><div id="cta-next">YARIN · 2. GÜN</div></div>
 <div id="fade" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="12"></div>
 <audio id="mix" data-start="0" data-duration="{TOTAL}" data-track-index="13" src="assets/master.m4a" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["futbolcu-ep1"] = tl;
</script></body></html>'''
open(os.path.join(HERE, 'index.html'), 'w').write(html)
json.dump({'total': TOTAL, 'title': [TS, TE], 'cta': CT,
           'scenes': scenes, 'lines': [{k: l[k] for k in ('id', 'who', 'img', 'start', 'dur', 'text')} for l in lines]},
          open(os.path.join(HERE, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
print('index.html', len(html) // 1024, 'KB;', len(scenes), 'scenes; speech ends', round(lines[-1]['start'] + lines[-1]['dur'], 2))

if '--no-mix' in sys.argv:
    sys.exit(0)

# ------------------------------------------------------------------ audio
whistle = os.path.join(HERE, 'assets', 'whistle.wav')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=f=2950:d=0.9', '-f', 'lavfi', '-i', 'sine=f=3150:d=0.9',
                '-filter_complex', '[0][1]amix=2,tremolo=f=28:d=0.7,afade=t=in:d=0.03,afade=t=out:st=0.75:d=0.15,volume=0.5,aresample=48000',
                whistle], check=True)
sfx = [(L['l04']['start'] + o, 'bell-ding', 0.35) for o in (0.6, 1.6, 2.6, 3.6)] + [
    (TS + 0.05, 'stinger-intro-bells', 0.55), (TE - 0.6, 'whoosh-reverse-1s', 0.45),
    (L['l05']['start'] - 0.9, whistle, 0.8), (L['l08']['start'] - 0.3, 'riser-short-2s', 0.4),
    (L['l09']['start'] + 0.2, 'stinger-sax-short', 0.4), (L['l11']['start'] + 1.0, 'stinger-hit-short', 0.45),
    (L['l13']['start'] + 0.6, 'impact-soft-1', 0.5), (ms - 0.25, 'whoosh-short', 0.6),
    (ms, 'impact-soft-2', 0.8), (wt('l17', 'çöpe'), 'paper-crumple', 0.7), (wt('l17', 'çöpe') + 0.3, 'impact-wood-light', 0.7),
    (wt('l19', 'yirmi'), 'stinger-hit-short', 0.4), (mt - 0.1, 'notification-2', 0.8),
    (L['l20b']['start'] + 1.6, 'stinger-energetic-hit', 0.5), (L['l21']['start'] + 3.4, 'pop-2', 0.7),
    (L['l21']['start'] + 4.0, 'pop-2', 0.7), (L['l21']['start'] + L['l21']['dur'] + 0.4, 'stinger-win-vibraphone', 0.5)]
for s in scenes[1:]:
    if s['img'] != 's04':
        sfx.append((s['start'], 'whoosh-short', 0.22))
inputs, f = [], []
def add(p):
    inputs.extend(['-i', p]); return inputs.count('-i') - 1
voice = []
for l in lines:
    i = add(os.path.join(TTS, l['id'] + '.mp3'))
    f.append(f'[{i}]aresample=48000,adelay={int(l["start"] * 1000)}[v{i}]'); voice.append(f'[v{i}]')
f.append(f'{"".join(voice)}amix=inputs={len(voice)}:normalize=0,apad,atrim=0:{TOTAL},asplit=2[vox][key]')
fx = []
for k, (t0, name, vol) in enumerate(sfx):
    i = add(name if name.endswith('.wav') and os.path.isabs(name) else os.path.join(SFX, name + '.wav'))
    f.append(f'[{i}]aresample=48000,volume={vol},adelay={int(t0 * 1000)}[s{k}]'); fx.append(f'[s{k}]')
f.append(f'{"".join(fx)}amix=inputs={len(fx)}:normalize=0,apad,atrim=0:{TOTAL}[fx]')
LIB = os.path.join(ROOT, '.claude/skills/editing-videos/library')
sec = [  # (start, end, track, volume)
    (0, L['l08']['start'] - 0.8, 'music/music-lofi-tea.mp3', 0.55),
    (L['l08']['start'] - 1.2, L['l16']['start'] - 0.6, 'music/music-energetic-jazz-funk.mp3', 0.5),
    (L['l16']['start'] - 1.0, CT - 0.2, 'music/music-ambient-piano.mp3', 0.6),
    (CT - 0.6, TOTAL, 'music/music-happy-clap-17s.mp3', 0.5)]
mus = []
for k, (a0, a1, trk, vol) in enumerate(sec):
    i = add(os.path.join(LIB, trk)); d0 = a1 - a0
    f.append(f'[{i}]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{d0:.2f},afade=t=in:d=1.2,afade=t=out:st={max(0, d0 - 1.2):.2f}:d=1.2,volume={vol},adelay={int(a0 * 1000)}[mu{k}]')
    mus.append(f'[mu{k}]')
amb = []
INDOOR = {'s01', 's02', 's04', 's05', 's06', 's15', 's16', 's17'}
PITCH = {'s10', 's11', 's12', 's13', 's14'}
for k, sc in enumerate(scenes):
    src = None
    if sc['img'] in INDOOR: src, vol = 'sfx/ambience-room-tone-30s.wav', 0.5
    elif sc['img'] in PITCH: src, vol = 'sfx/ambience-office-busy-45s.wav', 0.12
    if not src: continue
    i = add(os.path.join(LIB, src)); d0 = sc['end'] - sc['start'] + 0.4
    f.append(f'[{i}]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{d0:.2f},afade=t=in:d=0.4,afade=t=out:st={max(0, d0 - 0.4):.2f}:d=0.4,volume={vol},adelay={int(sc["start"] * 1000)}[am{k}]')
    amb.append(f'[am{k}]')
f.append(f'{"".join(mus)}amix=inputs={len(mus)}:normalize=0,apad,atrim=0:{TOTAL}[mus]')
f.append('[mus][key]sidechaincompress=threshold=0.06:ratio=3:attack=30:release=400[duckm]')
f.append(f'{"".join(amb)}amix=inputs={len(amb)}:normalize=0,apad,atrim=0:{TOTAL}[ambs]')
f.append('[duckm][ambs]amix=inputs=2:normalize=0[duck]')
f.append(f'[vox][fx][duck]amix=inputs=3:normalize=0,afade=t=out:st={TOTAL - 1.0}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:{TOTAL}[out]')
out = os.path.join(HERE, 'assets', 'master.m4a')
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(f), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', out], check=True)
print('wrote', out)
