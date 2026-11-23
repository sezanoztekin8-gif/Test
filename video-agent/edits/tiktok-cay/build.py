"""Tea-kettle short (TikTok, 1080x1920): kitchen, talking kettle and tea glass, captions, music. Usage: python3 build.py [--no-mix]"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LIB = os.path.join(ROOT, '.claude/skills/editing-videos/library')
S = json.load(open(os.path.join(HERE, 'script.json')))
TTS = os.path.join(HERE, 'assets', 'tts')
def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]))
t = 0.3
for l in S['lines']:
    l['dur'] = dur(os.path.join(TTS, l['id'] + '.wav'))
    l['start'] = round(t, 3); t += l['dur'] + 0.35
END = round(t + 0.4, 2)
TOTAL = round(END + 3.6, 2)
NAME = {'kettle': 'ÇAYDANLIK', 'glass': 'BARDAK'}
COL = {'kettle': '#c9ced6', 'glass': '#ffd9a0'}
K = '#333'
svg = f'''<svg width="1080" height="1920" viewBox="0 0 1080 1920" xmlns="http://www.w3.org/2000/svg">
<rect width="1080" height="1920" fill="#f3e5cf"/>
<rect x="60" y="180" width="960" height="560" rx="30" fill="#bfe3f2" stroke="{K}" stroke-width="10"/>
<circle cx="860" cy="300" r="60" fill="#fff3c4"/>
{''.join(f'<rect x="{x}" y="{y}" width="120" height="60" fill="#e8d1ad" stroke="#c9b08a" stroke-width="3"/>' for x in range(0,1080,120) for y in range(900,1280,60))}
<rect y="1300" width="1080" height="620" fill="#8b6b4a"/><rect y="1290" width="1080" height="40" fill="#6b4a33"/>
<path d="M140 930 Q40 980 140 1080" stroke="#444" stroke-width="26" fill="none"/>
<g id="kettle">
 <rect x="330" y="1000" width="60" height="0" fill="none"/>
 <path d="M570 1020 Q660 960 700 860 L725 880 Q690 1000 590 1080 Z" fill="{COL['kettle']}" stroke="{K}" stroke-width="10"/>
 <ellipse cx="360" cy="980" rx="230" ry="260" fill="{COL['kettle']}" stroke="{K}" stroke-width="10"/>
 <ellipse cx="360" cy="735" rx="110" ry="26" fill="#aab1bb" stroke="{K}" stroke-width="8"/>
 <circle cx="360" cy="700" r="26" fill="#444"/>
 <ellipse cx="290" cy="960" rx="34" ry="38" fill="#fff" stroke="{K}" stroke-width="6"/><circle cx="296" cy="966" r="14" fill="{K}"/>
 <ellipse cx="430" cy="960" rx="34" ry="38" fill="#fff" stroke="{K}" stroke-width="6"/><circle cx="436" cy="966" r="14" fill="{K}"/>
 <path d="M250 900 L320 920 M470 900 L400 920" stroke="{K}" stroke-width="8" stroke-linecap="round"/>
 <ellipse class="mouth mouth-kettle" cx="360" cy="1070" rx="44" ry="12" fill="#7a2f3a" stroke="{K}" stroke-width="5"/>
</g>
<g id="glass">
 <path d="M690 1010 L910 1010 Q900 1170 835 1200 L835 1290 L905 1320 L715 1320 L785 1290 L785 1200 Q700 1170 690 1010 Z" fill="#f5f7fa" stroke="{K}" stroke-width="10"/>
 <path d="M706 1060 L894 1060 Q884 1170 830 1196 Q776 1170 706 1060 Z" fill="#c97a2a" opacity="0.9"/>
 <ellipse cx="750" cy="1090" rx="20" ry="24" fill="#fff" stroke="{K}" stroke-width="5"/><circle cx="755" cy="1096" r="9" fill="{K}"/>
 <ellipse cx="850" cy="1090" rx="20" ry="24" fill="#fff" stroke="{K}" stroke-width="5"/><circle cx="855" cy="1096" r="9" fill="{K}"/>
 <ellipse class="mouth mouth-glass" cx="800" cy="1150" rx="26" ry="10" fill="#7a2f3a" stroke="{K}" stroke-width="4"/>
</g>
</svg>'''
html_css = '''@font-face{font-family:"BH Fredoka";font-weight:700;src:url(fonts/fredoka-latin-700-normal.woff2) format("woff2")}
@font-face{font-family:"BH Nunito";font-weight:900;src:url(fonts/nunito-latin-900-normal.woff2) format("woff2")}
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1080px;height:1920px;overflow:hidden;background:#111}
#root{position:relative;width:1080px;height:1920px;overflow:hidden}
#scene{position:absolute;inset:0}#scene svg{display:block}
.mouth{transform-box:fill-box;transform-origin:center;transform:scaleY(0)}
#hook{position:absolute;left:60px;right:60px;top:300px;text-align:center;font:700 118px/1.05 "BH Fredoka",sans-serif;color:#fff;-webkit-text-stroke:14px #111;paint-order:stroke fill;z-index:5}
.cap{position:absolute;left:50px;right:50px;bottom:360px;opacity:0;display:flex;flex-direction:column;align-items:center;gap:14px;z-index:6}
.who{padding:6px 26px;border-radius:30px;color:#111;font:700 40px "BH Fredoka",sans-serif;border:5px solid #111}
.txt{text-align:center;font:900 74px/1.15 "BH Nunito",sans-serif;color:#fff;-webkit-text-stroke:12px #111;paint-order:stroke fill}
#end{position:absolute;inset:0;background:rgba(15,12,20,0.9);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:40px;opacity:0;z-index:20}
#e1{font:700 110px/1.05 "BH Fredoka",sans-serif;color:#fff;text-align:center;padding:0 60px}#e1 span{color:#ffd166}
#e2{font:900 60px "BH Nunito",sans-serif;color:#ffe3ec}
'''
caps = []
for l in S['lines']:
    caps.append(f'<div class="cap" id="cap-{l["id"]}"><div class="who" style="background:{COL[l["who"]]}">{NAME[l["who"]]}</div><div class="txt">{l["text"]}</div></div>')
js = [
      'tl.fromTo("#hook", {scale:0.4, opacity:0}, {scale:1, opacity:1, duration:0.35, ease:"back.out(2.5)"}, 0.1);',
      'tl.to("#hook", {opacity:0, y:-40, duration:0.4}, 2.6);',
      'tl.fromTo("#kettle", {x:0}, {x:18, duration:0.05, yoyo:true, repeat:9, ease:"none"}, 0.2);',
      'tl.to("#scene", {scale:1.04, duration:%.2f, ease:"none"}, 0);' % TOTAL]
for l in S['lines']:
    mouth = 'mouth-kettle' if l['who'] == 'kettle' else 'mouth-glass'
    js.append(f'tl.set("#cap-{l["id"]}", {{opacity:1}}, {l["start"]});')
    js.append(f'tl.set("#cap-{l["id"]}", {{opacity:0}}, {round(l["start"] + l["dur"] + 0.15, 3)});')
    n = max(1, int(l['dur'] / 0.16))
    js.append(f'tl.to(".{mouth}", {{scaleY:1, duration:0.08, ease:"sine.inOut", yoyo:true, repeat:{2*n-1}}}, {l["start"]});')
    js.append(f'tl.set(".{mouth}", {{scaleY:0}}, {round(l["start"] + l["dur"], 3)});')
js.append(f'tl.fromTo("#end", {{opacity:0}}, {{opacity:1, duration:0.5}}, {END});')
js.append(f'tl.fromTo("#e1", {{y:50,opacity:0}}, {{y:0,opacity:1,duration:0.5,ease:"power3.out"}}, {END+0.2});')
js.append(f'tl.fromTo("#e2", {{y:30,opacity:0}}, {{y:0,opacity:1,duration:0.5,ease:"power3.out"}}, {END+0.8});')
html = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=1080, height=1920">
<script src="lib/gsap.min.js"></script><style>{html_css}</style></head><body>
<div id="root" data-composition-id="tiktok-cay" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
<div id="scene" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="1">{svg}</div>
<div id="hook" class="clip" data-start="0" data-duration="3" data-track-index="2">Çaydanlık bugün isyan etti!</div>
{''.join(caps)}
<div id="end" class="clip" data-start="{END}" data-duration="{round(TOTAL-END,2)}" data-track-index="3"><div id="e1">Sen <span>çay</span> mı kahve mi?</div><div id="e2">Yorumlara yaz 👇</div></div>
<audio id="mix" data-start="0" data-duration="{TOTAL}" data-track-index="4" src="assets/master.m4a"></audio>
</div><script>window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
{chr(10).join(js)}
window.__timelines["tiktok-cay"]=tl;</script></body></html>'''
open(os.path.join(HERE, 'index.html'), 'w').write(html)
print('index.html total', TOTAL, 's')
if '--no-mix' in sys.argv:
    sys.exit(0)
inputs, f, voice = [], [], []
def add(p):
    inputs.extend(['-i', p]); return inputs.count('-i') - 1
for l in S['lines']:
    i = add(os.path.join(TTS, l['id'] + '.wav'))
    f.append(f'[{i}]aresample=48000,adelay={int(l["start"] * 1000)}:all=1[v{i}]'); voice.append(f'[v{i}]')
f.append(f'{"".join(voice)}amix=inputs={len(voice)}:normalize=0,apad,atrim=0:{TOTAL},asplit=2[vox1][vox2]')
i = add(os.path.join(LIB, 'music/music-happy-clap-17s.mp3'))
f.append(f'[{i}]aresample=48000,aloop=loop=-1:size=2e9,atrim=0:{TOTAL},volume=0.22[mus]')
f.append(f'[mus][vox1]sidechaincompress=threshold=0.05:ratio=4:attack=25:release=300[duck]')
f.append(f'[vox2][duck]amix=inputs=2:normalize=0,afade=t=out:st={TOTAL-1.0}:d=1.0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:{TOTAL}[out]')
out = os.path.join(HERE, 'assets', 'master.m4a')
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(f), '-map', '[out]', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', out], check=True)
print('wrote', out)
