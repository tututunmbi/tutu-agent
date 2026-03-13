"""
Voice note transcription using OpenAI Whisper.
Handles Twilio media URLs → transcription.
"""
import os
import tempfile
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


async def transcribe_voice_note(media_url: str) -> str:
    """Download voice note from Twilio and transcribe with Whisper."""
    if not OPENAI_API_KEY:
        return "[Voice note received but transcription not configured. Set OPENAI_API_KEY.]"

    try:
        # Download the audio file from Twilio
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN", "")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                media_url,
                auth=(twilio_sid, twilio_token),
                follow_redirects=True
            )
            audio_data = response.content

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(audio_data)
            temp_path = f.name

        # Transcribe with Whisper API
        async with httpx.AsyncClient() as client:
            with open(temp_path, "rb") as audio_file:
                response = await client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                    files={"file": ("voice.ogg", audio_file, "audio/ogg")},
                    data={"model": "whisper-1"}
                )

            result = response.json()
            transcription = result.get("text", "[Could not transcribe voice note]")

        # Clean up
        os.unlink(temp_path)

        return f"[Voice note] {transcription}"

    except Exception as e:
        return f"[Voice note received but transcription failed: {str(e)}]"
