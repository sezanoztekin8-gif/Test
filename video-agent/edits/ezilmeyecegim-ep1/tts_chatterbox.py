"""Voices every line of script.json with Chatterbox Multilingual (local, free, MIT).
Character timbres come from synthetic references: the default voice, pitch/formant-shifted with ffmpeg,
then fed back as audio_prompt so Chatterbox speaks naturally in that timbre. No real person's voice is cloned.
Run with the Chatterbox venv:  HF_HUB_DISABLE_XET=1 <venv>/bin/python tts_chatterbox.py"""
import json, os, subprocess, time
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'assets', 'tts'); REF = os.path.join(HERE, 'assets', 'refs')
os.makedirs(OUT, exist_ok=True); os.makedirs(REF, exist_ok=True)
S = json.load(open(os.path.join(HERE, 'script.json')))
m = ChatterboxMultilingualTTS.from_pretrained(device='cpu')

# 1) a neutral seed sentence in the default voice, then shifted copies as character references
seed = os.path.join(REF, 'seed.wav')
if not os.path.exists(seed):
    w = m.generate('Merhaba, bugün hava çok güzel. Akşam hep birlikte yemek yiyelim, sonra da biraz yürüyüş yapalım.',
                   language_id='tr', exaggeration=0.5)
    ta.save(seed, w, m.sr)
shift = {'ref_kenan': (0.80, 1.0), 'ref_nermin': (0.90, 0.95), 'ref_ali': (1.30, 1.0)}
for name, (rate, tempo) in shift.items():
    p = os.path.join(REF, name + '.wav')
    if not os.path.exists(p):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', seed, '-af',
                        f'asetrate={m.sr}*{rate},aresample={m.sr},atempo={1 / rate * tempo:.4f}', p], check=True)

for l in S['lines']:
    p = os.path.join(OUT, l['id'] + '.wav')
    if os.path.exists(p):
        continue
    t = time.time()
    v = S['voices'][l['who']]
    kw = {} if v == 'default' else {'audio_prompt_path': os.path.join(REF, v + '.wav')}
    w = m.generate(l['text'], language_id='tr', exaggeration=l.get('ex', 0.5), cfg_weight=0.5, **kw)
    ta.save(p, w, m.sr)
    print(l['id'], l['who'], round(time.time() - t, 1), 's', flush=True)
