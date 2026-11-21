"""Mixes voices, chorus, music, fridge hum and sound effects into assets/master.m4a (-14 LUFS)."""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SFX = os.path.join(ROOT, '.claude/skills/editing-videos/library/sfx')
MUSIC = os.path.join(ROOT, '.claude/skills/short-editing/assets/music')
T = json.load(open(os.path.join(HERE, 'timeline.json')))
E = json.load(open(os.path.join(HERE, 'events.json')))
L = {l['id']: l for l in T['lines']}
TOTAL = T['total']
D1, D2, D3, FR = E['door1'], E['door2'], E['door3'], E['freeze']
TS, TE = E['title']
end = lambda i: L[i]['start'] + L[i]['dur']

sfx = [  # (time, file, volume)
    (D1 - 0.2, 'whoosh-long-2s', 0.55), (D1, 'impact-soft-1', 0.7), (D1 + 2.6, 'pop-2', 0.7),
    (D1 + 2.9, 'whoosh-short', 0.5), (D1 + 5.0, 'impact-wood-light', 0.8),
    (TS + 0.1, 'stinger-intro-bells', 0.55), (TE - 0.9, 'whoosh-reverse-1s', 0.45),
    (L['l04']['start'] - 0.35, 'whoosh-short', 0.3), (L['l05']['start'] - 0.35, 'whoosh-short', 0.3),
    (L['l05']['start'] + 1.6, 'whoosh-short', 0.3), (L['l05']['start'] + 3.3, 'whoosh-short', 0.3),
    (L['l08']['start'] - 0.05, 'stinger-hit-short', 0.45), (end('l16') + 0.05, 'stinger-sax-short', 0.55),
    (D2 - 0.2, 'whoosh-long-2s', 0.55), (D2, 'impact-soft-1', 0.7), (D2 + 3.25, 'impact-wood-light', 0.8),
    (D2 + 3.7, 'whoosh-short', 0.45), (D2 + 5.9, 'impact-wood-light', 0.8),
    (L['l18']['start'] - 0.1, 'stinger-pizzicato-short', 0.45), (end('l21') - 0.2, 'bell-ding', 0.4),
    (D3 - 0.2, 'whoosh-long-2s', 0.55), (D3, 'impact-soft-2', 0.75), (FR - 8.0, 'riser-long-8s', 0.55),
    (FR, 'stinger-energetic-hit', 0.8), (L['l26']['start'] + 2.0, 'pop-2', 0.7), (L['l26']['start'] + 2.7, 'pop-2', 0.7),
    (L['l26']['start'] + 4.6, 'click-sharp', 0.5), (L['l26']['start'] + 7.6, 'stinger-win-vibraphone', 0.5),
]

inputs, f = [], []
def add(path):
    inputs.extend(['-i', path]); return len(inputs) // 2 - 1

voice = []
for l in T['lines']:
    i = add(os.path.join(HERE, 'assets/tts', l['id'] + '.mp3'))
    ms = int(l['start'] * 1000)
    if l['who'] == 'yumurtalar':   # three-egg chorus: original + two pitched copies, slightly late
        f.append(f'[{i}]aresample=48000,asplit=3[{i}a][{i}b][{i}c]')
        f.append(f'[{i}b]asetrate=48000*1.26,aresample=48000,atempo=0.7937,adelay=30[{i}b2]')
        f.append(f'[{i}c]asetrate=48000*1.12,aresample=48000,atempo=0.8929,adelay=55[{i}c2]')
        f.append(f'[{i}a][{i}b2][{i}c2]amix=inputs=3:normalize=0,volume=0.55,adelay={ms}[v{i}]')
    else:
        f.append(f'[{i}]aresample=48000,adelay={ms}[v{i}]')
    voice.append(f'[v{i}]')
f.append(f'{"".join(voice)}amix=inputs={len(voice)}:normalize=0,apad,atrim=0:{TOTAL},asplit=2[vox][key]')

fx = []
for k, (t, name, vol) in enumerate(sfx):
    i = add(os.path.join(SFX, name + '.wav'))
    f.append(f'[{i}]aresample=48000,volume={vol},adelay={int(t * 1000)}[s{k}]')
    fx.append(f'[s{k}]')
f.append(f'{"".join(fx)}amix=inputs={len(fx)}:normalize=0,apad,atrim=0:{TOTAL}[fx]')

m1 = add(os.path.join(MUSIC, 'filature.mp3'))
m2 = add(os.path.join(MUSIC, 'compte-a-rebours.mp3'))
m3 = add(os.path.join(SFX, 'stinger-calm-pad.wav'))
c1 = D3 - 1.0
f.append(f'[{m1}]aresample=48000,atrim=0:{c1 + 2},afade=t=in:d=1.5,afade=t=out:st={c1}:d=2,volume=0.30[mu1]')
f.append(f'[{m2}]aresample=48000,atrim=0:{FR - c1},afade=t=in:d=1.5,afade=t=out:st={FR - c1 - 0.15}:d=0.15,volume=0.32,adelay={int(c1 * 1000)}[mu2]')
f.append(f'[{m3}]aresample=48000,volume=0.35,adelay={int((FR + 0.4) * 1000)}[mu3]')
f.append(f'[mu1][mu2][mu3]amix=inputs=3:normalize=0,apad,atrim=0:{TOTAL}[mus]')
f.append('[mus][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck]')

hum = ['-f', 'lavfi', '-i', f'anoisesrc=color=brown:amplitude=0.5:duration={TOTAL}:sample_rate=48000']
inputs.extend(hum); h = len(inputs) // 2 - 1 - 1   # lavfi adds 3 tokens; index by counting -i
h = sum(1 for x in inputs if x == '-i') - 1
f.append(f'[{h}]lowpass=f=140,volume=0.05[hum]')
f.append(f'[vox][fx][duck][hum]amix=inputs=4:normalize=0,afade=t=out:st={TOTAL - 1.0}:d=1.0,'
         f'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,atrim=0:{TOTAL}[out]')

out = os.path.join(HERE, 'assets', 'master.m4a')
cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', ';'.join(f), '-map', '[out]',
                                                   '-c:a', 'aac', '-b:a', '192k', '-ac', '2', out]
subprocess.run(cmd, check=True)
print('wrote', out)
