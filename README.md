# 🎓 Autonomous Student Outreach Agent

Find a matching opportunity. Draft the outreach. Send it yourself. 

No scraping, no API key setup, no risky automation.

A Streamlit app that takes a student's resume or profile, finds a real job listing that fits them, scores the match, and drafts a personalized cold-outreach email in the student's own voice — ready to copy or send.

This project was built for Unbound Hackathon at Waterloo Tech Week.

## How it works

1. **Paste a profile** — resume text, GitHub bio, or a skills summary, plus an optional name.
2. **Find an opportunity** — type a keyword/tech stack, or leave it blank and the app reads the profile itself to figure out what to search for. Results are pulled from two free, public, keyless job boards ([Remotive](https://remotive.com) and [RemoteOK](https://remoteok.com)), merged and deduplicated.
3. **Match & outreach** — the profile and the job are sent to Gemini, which returns a fit score out of 100, a one-line reason for the score, and a short cold-outreach email written as if the student is sending it themselves.
4. **Send it** — the message is shown in a copyable box with a button that opens it as a pre-filled email draft. Nothing is sent automatically.

> **Try it live:** [add your Streamlit Community Cloud link here once deployed]
>
> This demo runs on a shared Gemini free-tier key, so if you hit a rate-limit error, it just means the daily quota is temporarily used up — try again later, or run it locally with your own key (see below).

## Why no auto-DM

The original brief called for automatically DMing strangers on LinkedIn and Instagram. This app deliberately doesn't do that:

- Automated bulk messaging violates both platforms' terms of service and risks getting real accounts flagged or banned.
- A scripted sender is also the single most likely thing to fail live, mid-demo.
- The app still delivers the same end result — a finished, personalized message — just one click away from being sent by a human instead of a bot.

## Getting started

```bash
pip install streamlit google-genai requests
```

Add your Gemini API key so visitors never need their own:

```
.streamlit/secrets.toml
```
```toml
GEMINI_API_KEY = "your-key-here"
```

> Add `.streamlit/secrets.toml` to `.gitignore` — never commit a real key.

Run it:

```bash
streamlit run app.py
```

## Tech stack

- **Streamlit** — UI, single-page Python app
- **Google Gemini API** (`gemini-3.5-flash-lite`) — keyword detection, match scoring, outreach generation
- **Remotive API** + **RemoteOK API** — free, public, keyless job data

## Roadmap

- Session-level rate limiting to protect shared API quota once shared more widely
- Additional job sources for broader, more relevant coverage
- Deployment to a persistent public host (e.g. Streamlit Community Cloud) for a stable link

## Authors

- **Sourodeep Bhowmik**
- **Reuben Phillips**
- **Claude** (Anthropic) — pair-programmed the app logic, debugging, and this README
