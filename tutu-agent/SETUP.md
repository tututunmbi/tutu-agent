# Tutu's AI Advisor — Setup Guide

## What This Is

Your personal strategic AI advisor, deployed as a web app on Railway, connected to WhatsApp. It has persistent memory (remembers every conversation), can read/write to your Google Sheets tracker, sends you morning check-ins, weekly reviews, and memo reminders, and accepts voice notes.

## What You Need Before Starting

1. **A Claude API key** — Get one at https://console.anthropic.com
2. **A Railway account** — Sign up at https://railway.app (free tier works to start)
3. **A Twilio account** — Sign up at https://twilio.com (for WhatsApp connection)
4. **Python 3.10+** on your laptop (for local testing)
5. **(Optional)** An OpenAI API key — for voice note transcription
6. **(Optional)** A Google Cloud service account — for Google Sheets integration

## Step-by-Step Deployment

### Step 1: Get Your API Keys

**Claude API:**
1. Go to https://console.anthropic.com
2. Create an API key
3. Save it somewhere safe

**Twilio (for WhatsApp):**
1. Go to https://twilio.com and create an account
2. Go to Console → Account Info → copy your Account SID and Auth Token
3. Go to Messaging → Try it out → Send a WhatsApp Message
4. Follow the sandbox setup instructions (you'll get a WhatsApp number)
5. Note: For production, you'll want to register your own WhatsApp Business number

### Step 2: Deploy to Railway

1. Go to https://railway.app and sign in
2. Click "New Project" → "Deploy from GitHub repo" (or "Empty Project")
3. If using GitHub: push this folder to a GitHub repo first, then connect it
4. If using empty project: install the Railway CLI and run `railway up` from this folder

**Set environment variables in Railway:**
Go to your service → Variables tab → add each variable from `.env.example`:
- `ANTHROPIC_API_KEY` (required)
- `TWILIO_ACCOUNT_SID` (required for WhatsApp)
- `TWILIO_AUTH_TOKEN` (required for WhatsApp)
- `TWILIO_WHATSAPP_NUMBER` (from Twilio sandbox)
- `TUTU_WHATSAPP_NUMBER` (your WhatsApp number with country code)
- `CLAUDE_MODEL` (default: claude-sonnet-4-20250514)

### Step 3: Connect WhatsApp

1. In Twilio Console → Messaging → Settings → WhatsApp Sandbox Settings
2. Set the webhook URL to: `https://your-railway-url.up.railway.app/whatsapp`
3. Method: POST
4. Send "join [your-sandbox-keyword]" to the Twilio WhatsApp number from your phone
5. You should now be able to message your advisor on WhatsApp!

### Step 4: Test It

1. Visit `https://your-railway-url.up.railway.app` in your browser — you should see the web chat interface
2. Send a WhatsApp message — you should get a response
3. Check `https://your-railway-url.up.railway.app/health` — should return "alive"

### Step 5: (Optional) Connect Google Sheets

1. Go to Google Cloud Console → Create a project
2. Enable the Google Sheets API
3. Create a service account → Create a JSON key
4. Share your Google Sheets with the service account email
5. Add the JSON key as `GOOGLE_CREDENTIALS` in Railway (paste the entire JSON)
6. Add your sheet IDs as `TRACKER_SHEET_ID` and `CALENDAR_SHEET_ID`

### Step 6: (Optional) Voice Notes

1. Get an OpenAI API key from https://platform.openai.com
2. Add it as `OPENAI_API_KEY` in Railway
3. Now when you send voice notes on WhatsApp, they'll be transcribed and processed

## Scheduled Messages

The agent sends you messages automatically:
- **Every morning at 7:30 AM** — Daily focus check-in
- **Every Monday at 8:00 AM** — Week plan and calendar reminder
- **Every Friday at 9:00 AM** — Memo writing reminder
- **Every Sunday at 6:00 PM** — Weekly review

Times are in UTC. To adjust for your timezone, edit the `hour` values in `scheduler.py`.

## File Structure

```
tutu-agent/
├── main.py           # FastAPI server (web + WhatsApp endpoints)
├── agent.py          # Claude API brain with full advisor context
├── memory.py         # SQLite persistent memory
├── sheets.py         # Google Sheets read/write
├── voice.py          # Voice note transcription (Whisper)
├── scheduler.py      # Scheduled check-ins and reminders
├── references/       # Your knowledge base (blueprint, Leila Lens, etc.)
│   ├── blueprint.md
│   ├── leila-lens.md
│   ├── acq-lessons.md
│   └── operations.md
├── requirements.txt  # Python dependencies
├── Procfile          # Railway process config
├── railway.toml      # Railway deployment config
└── .env.example      # Environment variable template
```

## Updating Your Advisor

To update the advisor's knowledge (new memos, updated blueprint, new Leila content):
1. Edit the files in `references/`
2. Push to GitHub (or `railway up` again)
3. Railway auto-redeploys

To change the advisor's personality or behavior:
1. Edit the `build_system_prompt()` function in `agent.py`
2. Redeploy

## Costs

- **Railway:** ~$5-20/month (usage-based)
- **Claude API:** ~$50-150/month (depends on conversation volume)
- **Twilio:** ~$15-30/month (WhatsApp messages)
- **OpenAI Whisper:** ~$5/month (voice notes, optional)
- **Google Sheets API:** Free

## Getting Help

Open this project folder in Claude Code on your laptop. Claude Code can help you:
- Debug any issues
- Add new features
- Update the reference files
- Adjust the scheduler
- Connect new integrations
