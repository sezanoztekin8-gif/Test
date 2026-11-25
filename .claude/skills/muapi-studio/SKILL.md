---
name: muapi-studio
description: Default visual engine for all our videos - Open-Generative-AI (github.com/Anil-matcha/Open-Generative-AI) models through MuAPI, reached with the Clodu MCP tools (mcp__Clodu__muapi_*). Use for every new episode's images and moving clips.
---

# MuAPI studio (Open-Generative-AI)

Open-Generative-AI is a UI over MuAPI (api.muapi.ai, 600+ models). We do not run its web app;
we call the same models directly with the Clodu MCP tools (load them with ToolSearch "+Clodu").

## Flow for every episode
1. `muapi_account_balance` first. If balance is 0 or too low, tell the user (Turkish, one line)
   and fall back to the Figma still + Ken Burns pipeline. Never top up without the user's "evet".
2. Stills: `muapi_image_generate` (9:16, 3D animated-film style, same character prompt every scene).
   Good picks: nano-banana-pro, flux. Find exact ids with `search_models`.
3. Motion: `muapi_video_from_image` per scene (5 s clips). Cheap/fast: seedance-2.5-flash-image-to-video,
   kling-v3.0-standard-image-to-video; top quality: veo3.1-fast-image-to-video, kling-v3.0-pro-image-to-video.
4. Poll with `muapi_predict_result`, download into `video-agent/edits/<slug>/scenes/` (git-ignored assets stay out of git).
5. Voices, music, captions and assembly stay as in CLAUDE.md (OmniVoice/ElevenLabs + HyperFrames render).
6. Lip sync if a character talks on screen: `muapi_edit_lipsync`. Upscale: `muapi_enhance_upscale`.

## Rules
- Use only "safe" models; skip the "spicy" variants.
- Estimate the cost before a full episode and say it; spend only after balance check.
- No API key in the repo or chat: the MCP connection holds the auth.
