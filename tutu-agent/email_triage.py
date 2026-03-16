"""
Email Triage â Imani's proactive email intelligence.
Scans unread emails, categorizes them, flags opportunities, marks routine ones as read.
Sends Tutu a WhatsApp digest.
"""
import os
import json
import logging
import anthropic
from datetime import datetime

logger = logging.getLogger(__name__)

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Categories for email triage
CATEGORIES = {
    "opportunity": "Speaking engagements, partnership proposals, collaboration requests, press/media inquiries, potential client leads, TDPF-related inbound, event invitations, interview requests, anything mentioning Stamfordham or C2I",
    "needs_response": "Direct personal emails requiring Tutu's specific input or decision, emails from known contacts or clients expecting a reply, meeting requests needing confirmation",
    "informational": "Industry news, newsletters Tutu subscribed to that contain useful info, Google Workspace notifications, project updates from team members (Blessing, Victor, Jessica, Kitan, Naomi)",
    "routine": "Marketing emails, automated notifications, receipts, social media alerts, promotional content, newsletters with no actionable content, spam-adjacent, subscription confirmations, app notifications",
}

TRIAGE_SYSTEM_PROMPT = """You are Imani's email triage engine. Your job is to categorize emails for Tutu Adetunmbi.

Tutu is the founder of Stamfordham Global Limited (strategic consultancy) and CorpCI/C2I (creative economy infrastructure). She runs The Digital Professional Fair (TDPF). She is based in Lagos, Nigeria.

For each email, respond with ONLY valid JSON. No other text.

Categorize each email into exactly one category:
- "opportunity": Speaking engagements, partnerships, collaboration, press/media, potential clients, event invites, anything mentioning Stamfordham/C2I/TDPF, interviews, brand deals, consulting inquiries
- "needs_response": Direct personal emails needing Tutu's reply, client communications, meeting confirmations, team questions requiring her input
- "informational": Useful industry news, team updates, project notifications, Google Workspace alerts
- "routine": Marketing, automated notifications, receipts, social media alerts, promotional, newsletters with no action needed, spam-adjacent

Also provide a one-line summary of each email (max 80 chars) and an urgency score 1-5 (5 = most urgent).

Respond with this exact JSON structure:
{
  "results": [
    {
      "email_id": "the_id",
      "category": "opportunity|needs_response|informational|routine",
      "summary": "Brief one-line summary",
      "urgency": 3,
      "reason": "Why this category"
    }
  ]
}"""


async def run_email_triage(gmail, advisor=None):
    """
    Run the full email triage cycle:
    1. Fetch unread emails
    2. Categorize with Claude
    3. Star opportunities
    4. Mark routine as read
    5. Return digest

    Args:
        gmail: GmailManager instance
        advisor: TutuAdvisor instance (optional, for generating smart responses)

    Returns:
        Dict with triage results and digest text
    """
    if not gmail or not gmail.is_connected():
        logger.warning("Email triage skipped: Gmail not connected")
        return {"success": False, "error": "Gmail not connected"}

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("Email triage skipped: No Anthropic API key")
        return {"success": False, "error": "No Anthropic API key"}

    # 1. Fetch unread emails
    logger.info("Email triage: fetching unread emails...")
    unread_result = gmail.get_recent_emails(max_results=20, query="is:unread")

    if not unread_result.get("success"):
        logger.error("Email triage: failed to fetch emails: %s", unread_result.get("error"))
        return {"success": False, "error": unread_result.get("error")}

    emails = unread_result.get("emails", [])
    if not emails:
        logger.info("Email triage: no unread emails")
        return {"success": True, "digest": None, "message": "No unread emails"}

    logger.info("Email triage: found %d unread emails", len(emails))

    # 2. Read full content of each email for better categorization
    email_details = []
    for email in emails:
        full = gmail.read_email(email["id"])
        if full.get("success"):
            email_details.append({
                "email_id": email["id"],
                "from": full.get("from", ""),
                "subject": full.get("subject", ""),
                "date": full.get("date", ""),
                "body_preview": full.get("body", "")[:500],  # First 500 chars for categorization
            })
        else:
            # Fallback to metadata only
            email_details.append({
                "email_id": email["id"],
                "from": email.get("from", ""),
                "subject": email.get("subject", ""),
                "date": email.get("date", ""),
                "body_preview": email.get("snippet", ""),
            })

    # 3. Categorize with Claude
    logger.info("Email triage: categorizing %d emails with Claude...", len(email_details))
    client = anthropic.Anthropic(api_key=api_key)

    categorization_prompt = f"Categorize these {len(email_details)} emails:\n\n"
    for i, ed in enumerate(email_details):
        categorization_prompt += f"---\nEmail {i+1} (ID: {ed['email_id']}):\nFrom: {ed['from']}\nSubject: {ed['subject']}\nDate: {ed['date']}\nPreview: {ed['body_preview']}\n\n"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=TRIAGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": categorization_prompt}]
        )

        response_text = response.content[0].text.strip()
        # Parse JSON from response (handle markdown code blocks)
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        categorized = json.loads(response_text)
        results = categorized.get("results", [])
    except Exception as e:
        logger.error("Email triage: categorization failed: %s", e)
        return {"success": False, "error": f"Categorization failed: {e}"}

    # 4. Take action based on categories
    opportunities = []
    needs_response = []
    informational = []
    routine_ids = []

    for result in results:
        eid = result.get("email_id", "")
        category = result.get("category", "routine")
        summary = result.get("summary", "")
        urgency = result.get("urgency", 1)

        # Find the original email details
        original = next((ed for ed in email_details if ed["email_id"] == eid), None)
        entry = {
            "email_id": eid,
            "from": original.get("from", "") if original else "",
            "subject": original.get("subject", "") if original else "",
            "summary": summary,
            "urgency": urgency,
            "reason": result.get("reason", ""),
        }

        if category == "opportunity":
            opportunities.append(entry)
            # Star opportunities
            gmail.add_star(eid)
        elif category == "needs_response":
            needs_response.append(entry)
        elif category == "informational":
            informational.append(entry)
            # Mark informational as read
            routine_ids.append(eid)
        elif category == "routine":
            routine_ids.append(eid)

    # Mark routine + informational as read in batch
    if routine_ids:
        gmail.mark_as_read_batch(routine_ids)
        logger.info("Email triage: marked %d routine/informational emails as read", len(routine_ids))

    # 5. Build the digest
    now = datetime.now().strftime("%I:%M %p")
    digest_parts = [f"*Email Triage Report* ({now})"]
    digest_parts.append(f"{len(emails)} unread emails processed\n")

    if opportunities:
        digest_parts.append(f"*OPPORTUNITIES ({len(opportunities)}):*")
        for i, opp in enumerate(opportunities, 1):
            sender = opp["from"].split("<")[0].strip() if "<" in opp["from"] else opp["from"]
            digest_parts.append(f"{i}. {opp['subject']}")
            digest_parts.append(f"   From: {sender}")
            digest_parts.append(f"   {opp['summary']}")
        digest_parts.append("")

    if needs_response:
        digest_parts.append(f"*NEEDS YOUR REPLY ({len(needs_response)}):*")
        for i, nr in enumerate(needs_response, 1):
            sender = nr["from"].split("<")[0].strip() if "<" in nr["from"] else nr["from"]
            digest_parts.append(f"{i}. {nr['subject']}")
            digest_parts.append(f"   From: {sender}")
            digest_parts.append(f"   {nr['summary']}")
        digest_parts.append("")

    routine_count = len(routine_ids)
    if routine_count > 0:
        digest_parts.append(f"*{routine_count} routine emails marked as read.*")

    if not opportunities and not needs_response:
        digest_parts.append("Nothing urgent. Inbox is clean.")

    digest = "\n".join(digest_parts)

    logger.info("Email triage complete: %d opportunities, %d needs response, %d routine",
                len(opportunities), len(needs_response), routine_count)

    return {
        "success": True,
        "digest": digest,
        "opportunities": opportunities,
        "needs_response": needs_response,
        "informational": informational,
        "routine_count": routine_count,
        "total_processed": len(emails),
    }
