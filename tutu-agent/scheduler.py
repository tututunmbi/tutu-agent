"""
Scheduled tasks — morning check-ins, weekly reviews, reminders.
Uses APScheduler with Railway's always-on workers.
"""
import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER", "")  # e.g., "whatsapp:+14155238886"
TUTU_WHATSAPP = os.getenv("TUTU_WHATSAPP_NUMBER", "")  # e.g., "whatsapp:+44..."


def send_whatsapp(message: str):
    """Send a WhatsApp message to Tutu."""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_WHATSAPP, TUTU_WHATSAPP]):
        logger.warning("WhatsApp not configured — skipping message send")
        return

    try:
        client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        # Split long messages
        if len(message) <= 1500:
            client.messages.create(
                body=message,
                from_=TWILIO_WHATSAPP,
                to=TUTU_WHATSAPP
            )
        else:
            chunks = message.split("\n\n")
            current = ""
            for chunk in chunks:
                if len(current) + len(chunk) + 2 > 1500:
                    if current:
                        client.messages.create(body=current.strip(), from_=TWILIO_WHATSAPP, to=TUTU_WHATSAPP)
                    current = chunk
                else:
                    current += "\n\n" + chunk if current else chunk
            if current:
                client.messages.create(body=current.strip(), from_=TWILIO_WHATSAPP, to=TUTU_WHATSAPP)

        logger.info(f"WhatsApp message sent to Tutu")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp: {e}")


def setup_schedules(scheduler: AsyncIOScheduler, advisor, memory):
    """Configure all scheduled tasks."""

    async def morning_checkin():
        """7:30 AM daily — morning focus message."""
        logger.info("Running morning check-in...")
        message = await advisor.generate_checkin("morning")
        send_whatsapp(f"Good morning, Tutu.\n\n{message}")

    async def weekly_review():
        """Sunday 6 PM — weekly review and planning."""
        logger.info("Running weekly review...")
        message = await advisor.generate_checkin("weekly")
        send_whatsapp(f"Weekly Review\n\n{message}")

    async def memo_reminder():
        """Friday 9 AM — reminder to write the weekly memo."""
        send_whatsapp(
            "Tutu — it's Friday. Your memo publishes tomorrow morning.\n\n"
            "If you haven't started drafting, now's the time. "
            "Remember: Problem → Insight → Framework → Invitation. Under 800 words.\n\n"
            "What's this week's memo about? Tell me and I'll help you outline it."
        )

    async def content_reminder():
        """Monday 8 AM — what's on the calendar this week."""
        sheets = advisor.sheets
        if sheets and sheets.is_connected():
            today_content = sheets.get_today_content()
            if today_content:
                send_whatsapp(
                    f"Monday. New week.\n\n"
                    f"Today's calendar: {today_content['content_type']}\n"
                    f"Topic: {today_content['title']}\n\n"
                    f"What's your plan for this week? Talk to me."
                )
            else:
                send_whatsapp("Monday. New week. What are we focused on?")
        else:
            send_whatsapp("Monday. New week. What are we focused on?")

    # Schedule everything (times in UTC — adjust for your timezone)
    # If you're in UK (GMT/BST), these are approximately right
    scheduler.add_job(morning_checkin, "cron", hour=7, minute=30, id="morning_checkin")
    scheduler.add_job(weekly_review, "cron", day_of_week="sun", hour=18, minute=0, id="weekly_review")
    scheduler.add_job(memo_reminder, "cron", day_of_week="fri", hour=9, minute=0, id="memo_reminder")
    scheduler.add_job(content_reminder, "cron", day_of_week="mon", hour=8, minute=0, id="content_reminder")

    logger.info("Schedules configured: morning check-in (7:30 daily), weekly review (Sun 6PM), memo reminder (Fri 9AM), content reminder (Mon 8AM)")
