---
name: omnivoice-tr
description: Free, local, unlimited Turkish voices with OmniVoice (k2-fsa, Apache-2.0; the default engine of VoiceStudio, rampall/voicestudio). Designs a voice per character from attributes (gender, age, pitch) and clones it for every line, so each character keeps one voice. Use for Turkish voice-over, character dialogue, "ses", "seslendirme", when ElevenLabs credits are out.
---

# OmniVoice Turkish voices

Speaks Turkish well (checked with whisper), 600+ languages, runs on CPU (~20-30 s per line), no key, no limit.

## Install (once per session, ~3 min)
```bash
V=$SCRATCH/omni; mkdir -p $V && cd $V && uv venv -q --python 3.11 .venv && uv pip install -q --python .venv/bin/python omnivoice
```
Always run with `HF_HUB_DISABLE_XET=1` (weights come from huggingface.co: `k2-fsa/OmniVoice`).

## Use
```python
import soundfile as sf, torch
from omnivoice import OmniVoice
m = OmniVoice.from_pretrained('k2-fsa/OmniVoice', device_map='cpu', dtype=torch.float32)
# 1) design a character voice (attributes only: male/female; child, teenager, young adult, middle-aged, elderly;
#    very low / low / moderate / high / very high pitch)
ref = m.generate(text=SEED, language='tr', instruct='female, elderly, moderate pitch')[0]
sf.write('ref.wav', ref, m.sampling_rate)
# 2) every line cloned from that reference -> same voice all episode
a = m.generate(text='Zehra! Kahvaltı hâlâ hazır değil mi?', language='tr', ref_audio='ref.wav', ref_text=SEED)[0]
```
Working example: `video-agent/edits/ezilmeyecegim-ep1/tts_omnivoice.py`.

## Rules
- Women must sound like women: measure pitch (median f0 > 180 Hz) before using a female voice.
- Check each line with whisper-cli (Turkish) before the edit.
- Designed voices only; never clone a real person's voice without their consent.
