"""Voices script.json with OmniVoice (k2-fsa, Apache-2.0, local, Turkish).
Each character gets one designed voice (gender/age/pitch attributes, no real person), saved as a reference;
every line is then cloned from that reference so the character sounds the same all episode.
Run with the OmniVoice venv:  HF_HUB_DISABLE_XET=1 <venv>/bin/python tts_omnivoice.py"""
import json, os, time
import soundfile as sf, torch
from omnivoice import OmniVoice

HERE = os.path.dirname(os.path.abspath(__file__))
OUT, REF = os.path.join(HERE, 'assets', 'tts'), os.path.join(HERE, 'assets', 'refs_omni')
os.makedirs(OUT, exist_ok=True); os.makedirs(REF, exist_ok=True)
S = json.load(open(os.path.join(HERE, 'script.json')))
m = OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cpu', dtype=torch.float32)

DESIGN = {'defne': 'female, young adult, moderate pitch', 'nermin': 'female, elderly, moderate pitch',
          'kenan': 'male, middle-aged, low pitch', 'ali': 'male, child, high pitch'}
SEED = 'Bugün hava çok güzel. Akşam hep birlikte yemek yiyelim, sonra da biraz yürüyelim.'
for who, ins in DESIGN.items():
    p = os.path.join(REF, who + '.wav')
    if not os.path.exists(p):
        torch.manual_seed(7)
        sf.write(p, m.generate(text=SEED, language='tr', instruct=ins)[0], m.sampling_rate)

for l in S['lines']:
    p = os.path.join(OUT, l['id'] + '.wav')
    if os.path.exists(p):
        continue
    t = time.time()
    a = m.generate(text=l['text'], language='tr', ref_audio=os.path.join(REF, l['who'] + '.wav'), ref_text=SEED)
    sf.write(p, a[0], m.sampling_rate)
    print(l['id'], l['who'], round(time.time() - t, 1), 's', flush=True)
