# Railway Deployment

This project should run as a Railway Cron Job, not a long-running web service.

## Required Variables

Set these in Railway service variables:

```env
NAUKRI_EMAIL=...
NAUKRI_PASSWORD=...
HEADLESS=true

GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash

OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5-mini

RESUME_TEXT_PATH=resume.txt
TECH_STACK=.NET, React, Vue.js, REST API, GraphQL, SQL, Azure, AI integrations
EXPERIENCE=3.5+ years
TARGET_ROLE=Full Stack Developer
NAUKRI_HEADLINE=Fallback headline if AI providers fail
```

`OPENAI_API_KEY` is optional if you only want Gemini. `NAUKRI_HEADLINE` is the final fallback.

## Start Command

The Dockerfile default command is:

```bash
python main.py
```

## Cron

In Railway service settings, set a cron schedule. Railway cron schedules use UTC.

Example: run every day at 9:00 AM, 12:00 PM, 2:00 PM, and 7:00 PM India time:

```cron
30 3,6,8,13 * * *
```

This is UTC, which maps to IST as:

- `03:30 UTC` -> `09:00 IST`
- `06:30 UTC` -> `12:00 IST`
- `08:30 UTC` -> `14:00 IST`
- `13:30 UTC` -> `19:00 IST`

## Notes

- Railway builds from the `Dockerfile` when it is present.
- The job is expected to finish and exit after updating the headline.
- Runtime files such as logs, screenshots, session storage, and generated outputs are not committed or included in the Docker build.
