"""
Tutu's Strategic AI Advisor — API Agent
Deployed on Railway, connected via WhatsApp (Twilio)
"""
import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from agent import TutuAdvisor
from memory import ConversationMemory
from sheets import SheetsManager
from scheduler import setup_schedules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
memory = ConversationMemory()
sheets = SheetsManager()
advisor = TutuAdvisor(memory=memory, sheets=sheets)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    setup_schedules(scheduler, advisor, memory)
    scheduler.start()
    logger.info("Tutu's Advisor is online.")
    yield
    scheduler.shutdown()
    logger.info("Tutu's Advisor is shutting down.")


app = FastAPI(title="Tutu's Strategic Advisor", lifespan=lifespan)


# ============================================================
# WhatsApp Webhook (Twilio)
# ============================================================
@app.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages via Twilio."""
    form = await request.form()
    incoming_msg = form.get("Body", "").strip()
    from_number = form.get("From", "")
    num_media = int(form.get("NumMedia", 0))

    logger.info(f"Message from {from_number}: {incoming_msg[:100]}...")

    # Handle voice notes (Twilio sends media URL)
    if num_media > 0:
        media_url = form.get("MediaUrl0", "")
        media_type = form.get("MediaContentType0", "")
        if "audio" in media_type:
            # Transcribe voice note using OpenAI Whisper
            from voice import transcribe_voice_note
            incoming_msg = await transcribe_voice_note(media_url)
            logger.info(f"Transcribed voice note: {incoming_msg[:100]}...")

    # Get response from advisor
    response_text = await advisor.chat(incoming_msg, source="whatsapp")

    # WhatsApp has a 1600 char limit per message
    # Split long responses into multiple messages
    resp = MessagingResponse()
    if len(response_text) <= 1500:
        resp.message(response_text)
    else:
        chunks = split_message(response_text, 1500)
        for chunk in chunks:
            resp.message(chunk)

    return Response(content=str(resp), media_type="application/xml")


# ============================================================
# Web Chat Interface (backup / desktop access)
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def home():
    """Simple web chat interface."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tutu's Advisor</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Inter', -apple-system, sans-serif; background: #0f0f1a; color: #e0e0e0; height: 100vh; display: flex; flex-direction: column; }
            .header { padding: 20px; background: #1a1a2e; border-bottom: 2px solid #e94560; text-align: center; }
            .header h1 { font-size: 1.4rem; color: #e94560; }
            .header p { font-size: 0.85rem; color: #888; margin-top: 4px; }
            .chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 16px; }
            .msg { max-width: 80%; padding: 14px 18px; border-radius: 16px; line-height: 1.6; font-size: 0.95rem; white-space: pre-wrap; }
            .msg.user { align-self: flex-end; background: #0f3460; color: #fff; border-bottom-right-radius: 4px; }
            .msg.advisor { align-self: flex-start; background: #1a1a2e; border: 1px solid #333; border-bottom-left-radius: 4px; }
            .input-area { padding: 16px 20px; background: #1a1a2e; border-top: 1px solid #333; display: flex; gap: 12px; }
            .input-area textarea { flex: 1; background: #0f0f1a; color: #e0e0e0; border: 1px solid #444; border-radius: 12px; padding: 12px 16px; font-size: 0.95rem; font-family: inherit; resize: none; outline: none; }
            .input-area textarea:focus { border-color: #e94560; }
            .input-area button { background: #e94560; color: #fff; border: none; border-radius: 12px; padding: 12px 24px; font-size: 0.95rem; cursor: pointer; font-weight: 600; }
            .input-area button:hover { background: #c73550; }
            .typing { color: #888; font-style: italic; padding: 8px 18px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Tutu's Strategic Advisor</h1>
            <p>Powered by the Leila Lens &bull; Phase 1: The Foundation</p>
        </div>
        <div class="chat" id="chat"></div>
        <div class="input-area">
            <textarea id="input" rows="2" placeholder="Talk to your advisor..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send()}"></textarea>
            <button onclick="send()">Send</button>
        </div>
        <script>
            const chat = document.getElementById('chat');
            const input = document.getElementById('input');
            function addMsg(text, type) {
                const d = document.createElement('div');
                d.className = 'msg ' + type;
                d.textContent = text;
                chat.appendChild(d);
                chat.scrollTop = chat.scrollHeight;
            }
            async function send() {
                const text = input.value.trim();
                if (!text) return;
                addMsg(text, 'user');
                input.value = '';
                const typing = document.createElement('div');
                typing.className = 'typing';
                typing.textContent = 'Thinking...';
                chat.appendChild(typing);
                chat.scrollTop = chat.scrollHeight;
                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({message: text})
                    });
                    const data = await res.json();
                    typing.remove();
                    addMsg(data.response, 'advisor');
                } catch(e) {
                    typing.remove();
                    addMsg('Connection error. Try again.', 'advisor');
                }
            }
            addMsg("Hey Tutu. I'm here. What are we working on today?", 'advisor');
        </script>
    </body>
    </html>
    """


@app.post("/chat")
async def web_chat(request: Request):
    """Web chat endpoint."""
    data = await request.json()
    message = data.get("message", "")
    response = await advisor.chat(message, source="web")
    return {"response": response}


# ============================================================
# Health Check (Railway needs this)
# ============================================================
@app.get("/health")
async def health():
    return {"status": "alive", "phase": "Phase 1: The Foundation"}


def split_message(text, max_len=1500):
    """Split long messages at paragraph breaks."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    current = ""
    for para in text.split("\n\n"):
        if len(current) + len(para) + 2 > max_len:
            if current:
                chunks.append(current.strip())
            current = para
        else:
            current += "\n\n" + para if current else para
    if current:
        chunks.append(current.strip())
    return chunks if chunks else [text[:max_len]]
