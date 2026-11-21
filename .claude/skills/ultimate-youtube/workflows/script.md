# Hooks and scripts

Goal: a script that keeps the viewer watching and pays off the title's promise.
Reference: `references/retention-and-hooks.md`. Read `channel-profile.md` for
voice, language, length, format and accuracy rules.

## Inputs

Topic and the packaging (title + thumbnail concept) - write the script to
deliver what the packaging promises. If there is no packaging yet, draft it first
(`workflows/packaging.md`), because the hook must confirm the click.
Also: target length, format (talking head, narration over visuals, animation,
screen recording, documentary, list, story), language, and any sources the user
wants used.

## Learn from what works (optional, recommended)

Pick 2-3 strong videos on similar topics (competitor outliers or the user's own
winners) and read their openings: `yt_transcripts.py hook <url> --seconds 45 --lang xx`.
Map their beats; note the shared order. Use the pattern, not the words.

## Write

1. **Hooks first** - write 3-5 different hook options (first 15-30 seconds), each a
   different beat order (e.g. bold claim, cold open in the middle of the action,
   question, result-first, contrast). Rate each for drop-off risk and say why.
   Let the user pick, or pick the strongest and say why.
2. **Beat sheet** - outline with timestamps: hook, promise, stakes, open loops,
   proof, re-hooks every 60-90 seconds (long-form), mini-payoffs, the main
   payoff, the call to action. The main payoff comes late but not at the very end.
3. **Full script** - in the user's language and voice. Spoken-language sentences.
   Mark visuals/B-roll/on-screen text in brackets: `[VISUAL: ...]`, `[TEXT: ...]`, `[SFX: ...]`.
   For animated or faceless channels, describe each scene so it can be produced.
4. **Ending** - deliver the payoff, then point to one next video (end screen) instead
   of a long outro. Ask for the subscription only after delivering value.
5. **Check** - read the script against the title: is every promise paid off? Cut
   anything that doesn't serve the promise. Estimate length at the channel's
   words-per-minute (`yt_transcripts.py stats` on one of their videos) or ~140-160 wpm.

## Accuracy

- Facts, quotes, dates and figures must come from sources the user accepts.
  List sources at the end. Never invent quotations or statistics.
- When stories, traditions or interpretations differ between sources, say which
  version you are following.
- Flag claims that need checking with `[VERIFY]`.

## Output

Fill `templates/script.md`: hook options, chosen hook, beat sheet with times,
full script, on-screen text list, Shorts cut-down ideas (2-3 moments that work
standalone), sources. Offer `workflows/seo.md` next for the upload package.
