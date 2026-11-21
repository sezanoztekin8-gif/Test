# Setup: credentials, step by step

Run `python SKILL_DIR/scripts/yt_auth.py doctor` first. It says what is
missing. Walk the user through only the parts they need, one step at a time,
and wait for them to finish each step. Never ask the user to paste a client
secret, password or token into the chat. They save files themselves; you only
run the commands.

All parts use one Google Cloud project. Free; no billing account is needed for
the YouTube APIs at default quota.

## Part A: API key (public research, 5 minutes)

Enough for: competitor scans, video stats, comments, search, trending, SEO
audits of public videos.

1. Open https://console.cloud.google.com/ and create a project (any name).
2. APIs & Services -> Library -> enable **YouTube Data API v3**.
3. APIs & Services -> Credentials -> Create credentials -> **API key**.
4. Recommended: Edit the key -> API restrictions -> restrict to YouTube Data API v3.
5. The user saves it with one of:
   - `python SKILL_DIR/scripts/yt_auth.py set-key THEIR_KEY` (stored in `~/.ultimate-youtube/config.json`)
   - or the environment variable `YOUTUBE_API_KEY`.

   Tell the user to run this in their own terminal, so the key never appears in
   the chat. `set-key` makes one test call and reports whether the key works.

## Part B: read token (your analytics, 10 minutes)

Enough for: private analytics, retention, traffic sources, search terms,
audience, your private and scheduled videos, CTR via the Reporting API.

1. In the same project enable **YouTube Analytics API** and **YouTube Reporting API**.
2. APIs & Services -> **OAuth consent screen** (Google Auth Platform):
   - User type **External** (or Internal for Workspace orgs).
   - App name, support email, developer email: anything sensible.
   - Scopes: you can skip; the script requests them.
   - **Audience -> Test users: add the Google account that owns the channel.**
3. Credentials -> Create credentials -> **OAuth client ID** -> Application type
   **Desktop app**. Download the JSON.
4. Save it as `~/.ultimate-youtube/client_secret.json` (Windows:
   `%USERPROFILE%\.ultimate-youtube\client_secret.json`).
5. Run `python SKILL_DIR/scripts/yt_auth.py login`. A browser opens. Sign in with
   the channel's account. If the channel is a Brand Account, pick the brand
   channel on the account chooser. "Google hasn't verified this app" is expected
   for your own test app: Advanced -> Continue.
6. Monetized channel? Use `login --revenue` to add revenue metrics.
7. The command prints the channel name. Confirm it with the user.

No browser on this machine (SSH, server)? Use `login --manual` and follow the
copy-paste instructions.

## Part C: write token (upload, edit, delete)

1. Same client_secret.json. Run `python SKILL_DIR/scripts/yt_auth.py login --write`.
2. This is a **separate** token with only the `youtube.force-ssl` scope. Analytics
   and research never use it. Deleting `~/.ultimate-youtube/token_write.json`
   removes all write access.
3. Confirm the channel name it prints.

## Things that surprise people

- **Testing-mode tokens expire after 7 days.** While the consent screen is in
  "Testing", refresh tokens stop working after a week and you see "invalid_grant".
  Re-run `login` (and `login --write`), or publish the app (Audience -> Publish
  app). Personal use apps can stay unverified; Google shows a warning screen.
- **Uploads from unaudited projects are locked to private.** Videos uploaded
  through the API by a project that hasn't passed Google's YouTube API compliance
  audit are restricted to private. Upload private (the default), then change
  visibility in YouTube Studio, or apply for the audit in the API console
  (https://support.google.com/youtube/contact/yt_api_form) if you publish via API
  regularly.
- **Custom thumbnails** need a phone-verified channel (youtube.com/verify).
- **Quota**: 10,000 units/day plus separate 100/day buckets for search and
  uploads, reset at midnight Pacific. `yt_auth.py quota` shows local usage.
  Need more? Cloud Console -> YouTube Data API v3 -> Quotas -> request increase.
- **Wrong account**: `yt_auth.py revoke` (or `revoke --write`), then `login` again.
- **Transcripts fail with "blocked"**: see `references/transcripts.md`.

## Done when

`doctor` shows `capabilities` true for what the user needs, and the user has
confirmed the channel name. Then return to the task they asked for.
