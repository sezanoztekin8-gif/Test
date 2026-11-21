# Shorts

Reference: `references/shorts.md`.

## Is the channel using Shorts well?

- `yt_competitors.py scan @own --max 100` -> `formats.short` vs `formats.long`
  (counts, median views, outliers). Use `--verify-shorts` for exact detection.
- `yt_analytics.py audience` -> `creator_content_type` splits views and watch
  time between Shorts and long-form; `traffic` shows SHORTS feed share.
- Compare competitors' Shorts strategy with `compare`.

Questions to answer: do Shorts bring subscribers who watch long-form, or a
separate audience? Which Shorts topics win (`outliers` filtered to format short)?

## Make Shorts

1. **Cut-downs**: from long videos (yours), find standalone moments: a surprising
   fact, a strong claim, a punchline, a satisfying result. Use the timed transcript
   (`yt_transcripts.py get VIDEO --timed`) and retention bumps (`yt_analytics.py retention`).
   Each needs its own hook in the first 1-2 seconds and must make sense alone.
2. **Native Shorts**: one idea, hook in the first second (visual + words), payoff
   before the end, loopable ending if natural. Up to 3 minutes is allowed; most
   ideas need far less.
3. **Bridge**: link the Short to the related long video (the "related video" link
   in the Shorts editor) so Shorts viewers can continue.

## Output per Short

Title (short, curiosity or keyword), the hook line, the beat list with
seconds, on-screen text, source segment (if cut-down: start-end timestamps),
related long video, and the 1-2 hashtags. Batch 5-10 at once for a week of Shorts.
