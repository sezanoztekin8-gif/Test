---
name: kokoro
description: Kokoro-82M (hexgrad/kokoro, Apache-2.0) local TTS for English, Spanish, French, Hindi, Italian, Japanese, Portuguese, Mandarin. NO Turkish - for Turkish use omnivoice-tr. Use only for foreign-language voice lines.
---
# Kokoro TTS (no Turkish)
Install: `uv pip install kokoro soundfile` (needs espeak-ng for English fallback).
```python
from kokoro import KPipeline; import soundfile as sf
p = KPipeline(lang_code='a')   # a/b English, e es, f fr, h hi, i it, j ja, p pt-br, z zh
for i, (_, _, audio) in enumerate(p('Hello there!', voice='af_heart')): sf.write(f'{i}.wav', audio, 24000)
```
Turkish text through Kokoro comes out with a foreign accent; do not use it for Turkish videos.
