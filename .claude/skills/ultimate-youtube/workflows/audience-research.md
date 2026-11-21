# Audience research from comments

Goal: learn what viewers want, ask, love and dislike - in their own words.

## Commands

- One video: `yt_comments.py video <url> --max 300`
- A channel's recent uploads (any channel): `yt_comments.py channel @handle --videos 15 --per-video 100 [--skip-shorts]`
- Your channel: `yt_comments.py mine --videos 15`

Output: counts per category (question, request, pain_point, criticism, praise,
monetization_signal, timestamp), the most-liked examples in each, frequent
words and phrases, and a raw sample. Full comments are saved to a file.

Category rules are English keywords. For other languages (or mixed-script
comments), read the `sample` and the saved file yourself and classify them.

## Analyse

1. **Requests** - specific videos people ask for. Group duplicates, count them,
   note which channel's audience asked. These are the strongest idea signals.
2. **Questions** - what the video didn't answer. Each recurring question is a
   possible follow-up video, FAQ section, pinned comment or Short.
3. **Pain points** - problems and frustrations in the viewer's life related to the niche.
4. **Criticism** - audio, pacing, length, accuracy, clickbait. Separate fixable
   production feedback from disagreement.
5. **Moments** - timestamps people quote: what landed. Compare with retention bumps if it's your video.
6. **Language** - the words viewers use for the topic. Reuse them in titles and
   descriptions (they are what people search).
7. **Monetization signals** - asks for products, courses, merch, resources.

## Deliver

A short report: top 5 requests (with counts and example quotes under 25 words),
top questions, what viewers love, what to fix, words to use in packaging, and 3-5
video ideas that answer real requests. Quote briefly; don't reproduce long
comments, and don't name commenters.
