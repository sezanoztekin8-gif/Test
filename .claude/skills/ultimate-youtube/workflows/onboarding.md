# Onboarding: build the channel profile

Goal: a `channel-profile.md` in the user's project that every other workflow
reads first. It replaces re-asking the same questions every session. Keep it
short (one page) and factual.

## 1. Ask (one message, skip what you already know)

1. Channel link or @handle (or "not created yet").
2. What the channel is about, in one sentence. Push for specifics: not "tech"
   but "budget Android phone reviews for students".
3. Who it is for: age range, country/region, language(s), what they want from
   the channel (learn, laugh, relax, decide what to buy...).
4. Formats: long-form, Shorts, live, podcasts; typical length; faceless or
   on-camera; how videos are made (filmed, animated, screen recording, AI voice...).
5. Languages: which ones, and whether that means separate channels, one channel
   with several audio tracks, or translated titles only (see `references/multilingual.md`).
6. Goal for the next 90 days: growth, monetization, authority, community.
7. 3-5 channels they see as competitors or inspiration.
8. Constraints: uploads per week they can sustain, budget, tools, topics to avoid,
   tone/voice rules, accuracy rules (e.g. cite sources).

## 2. Pull data (if credentials exist)

- Own channel: `yt_auth.py whoami` and `yt_competitors.py scan @their_handle --max 50`
  (public view of their own channel: formats, cadence, outliers).
- Analytics if a read token exists: `yt_analytics.py overview --days 90` and
  `yt_analytics.py audience --days 90`.
- Competitors: `yt_competitors.py compare @a @b @c --max 50`.
- Size tier from subscribers: New < 1K, Growing 1K-10K, Established 10K-100K,
  Authority 100K+. Tier changes advice (cadence, Shorts mix, monetization).

## 3. Save

Fill `templates/channel-profile.md` and save it as `channel-profile.md` in the
current project directory. Add the competitors to the watchlist if the user
agrees: `yt_competitors.py watch add @a @b @c`.

Show the user the profile and ask them to correct anything wrong. Update the
file whenever their answers or the data change.
