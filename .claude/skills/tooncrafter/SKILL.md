---
name: tooncrafter
description: ToonCrafter (Doubiiu/ToonCrafter, Apache-2.0, SIGGRAPH Asia 2024) - generates in-between frames between two cartoon images. Use when the user needs smooth animation between two 2D drawn keyframes (cartoon morphing, character poses, scene-to-scene motion). Needs an NVIDIA GPU with ~12 GB VRAM; not runnable on the CPU-only cloud container.
homepage: https://github.com/Doubiiu/ToonCrafter
---

# ToonCrafter (cartoon interpolation)

Takes two cartoon/anime keyframes and generates the frames between them (512x320 model).

## What it is not
- Not a text-to-video or a general video editor.
- Not a voice or caption tool.

## Requirements
- NVIDIA GPU, about 12 GB VRAM (community reports work with ~10 GB; the original needed 24-27 GB).
- Python 3.8.5 env, `requirements.txt` from the repo.
- Model weights (`tooncrafter_512_interp-fp16.safetensors` or `model.ckpt`) from Hugging Face, placed in `checkpoints/tooncrafter_512_interp_v1/model.ckpt`. Weights are large and must be downloaded separately.

## Setup (on a GPU machine)
```bash
git clone https://github.com/Doubiiu/ToonCrafter && cd ToonCrafter
conda create -n tooncrafter python=3.8.5 && conda activate tooncrafter
pip install -r requirements.txt
# place the checkpoint, then:
python gradio_app.py        # web UI
```

## In this studio
- Cloud container (this repo's environment): **cannot run** - no GPU, and the weights are too big for the session disk. Say so plainly; do not fake the output.
- Use it only if the user has a GPU machine and asks for it. Keyframes must be original or the user's own art.
- Output frames go into the episode folder; then continue with HyperFrames/ffmpeg for timing and mix.
