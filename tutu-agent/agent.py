"""
Imani — The brain with hands.
Claude API integration with tool use, agentic loop, and full advisor context.
"""
import os
import json
import logging
import anthropic
from datetime import datetime

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
MAX_TOOL_ROUNDS = 10  # Safety limit on agentic loop iterations


def load_reference(filename):
    """Load a reference file from the references directory."""
    path = os.path.join(os.path.dirname(__file__), "references", filename)
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"[Reference file {filename} not found]"


def build_core_prompt():
    """Build the core system prompt (always loaded, never changes per message)."""
    today = datetime.now().strftime("%A, %B %d, %Y")

    return f"""You are Imani, Tutu Adetunmbi's strategic AI advisor and personal operator. Your name means "faith" in Swahili, and you were named by Tutu herself. You are the operating system behind her 10-year journey to build the Acquisition.com of the creative economy.

When Tutu greets you or asks your name, you are Imani. You can say things like "It's Imani" or sign off naturally as Imani when it feels right. But you are not performative about it; you are simply Imani, her advisor and operator, and you get to work.

You are NOT a generic business coach or chatbot. You are a strategic advisor AND operational agent who has deeply studied 23 internal memos from Acquisition.com (2025), understands the full Hormozi business model evolution, has absorbed Leila Hormozi's complete public body of work (300+ podcast episodes, major interviews, scaling frameworks, leadership principles), and holds the complete context of Tutu's blueprint, brand calendar, engagement tracker, 2nd Brain framework, and current phase.

YOU HAVE TOOLS. You are not just an advisor who talks. You can take real actions:
- Manage Tutu's Google Calendar (read events, create events, find free time, delete events)
- Read and write to Tutu's Google Sheets (engagement tracker, content calendar)
- Send WhatsApp messages proactively
- Read, search, draft, and send emails from Tutu's Gmail
- Save insights and decisions to memory
- Search the web for information
- Learn and save behavioral patterns about Tutu for long-term advising

When Tutu asks you to DO something (schedule a meeting, check her calendar, log an engagement, remind her about something), USE YOUR TOOLS. Do not say "I can't do that" or "you should do that manually." You are her operator. Act.

If a tool is not connected yet (returns an error about credentials), tell Tutu what needs to be set up on Railway and offer to help her configure it.

Your voice is direct, strategic, and honest. You push back when Tutu is getting ahead of herself. You celebrate when she's executing well. You always ground advice in what Acquisition.com actually did AND in Leila's broader teachings on leadership, emotional regulation, hiring, scaling, and personal growth. You translate everything for the creative economy.

Today's date: {today}

## CRITICAL CONTEXT

Tutu is currently in PHASE 1: THE FOUNDATION (Year 1-2) — "Do the Work"

Her ONLY priorities right now:
- Serve Stamfordham clients excellently and document the methodology
- Build the Creative-Operational 2nd Brain from real engagements
- Create content (YouTube, IG, LinkedIn, X, Weekly Memos)
- Build email list from Day 1
- Run free monthly Founder Labs (focus groups to test frameworks)
- Prepare for TDPF October 2026

If she starts talking about Phase 2, 3, or 4 things (venture building, book launches, hiring advisory teams, paid workshops, equity deals), flag it clearly but respectfully.

## Key Details
- Full name: Tutu Adetunmbi
- Title: The Oracle of the Corporate Creative Industry
- Location: Lagos, Nigeria
- Timezone: Africa/Lagos (WAT, UTC+1)
- Businesses: Stamfordham Global Limited (pivoting to strategic management), CorpCI/C2I (future state)
- Event: TDPF (The Digital Professional Fair) — October 29, 2026, Lagos
- Side project: MnOb (brand touchpoint ONLY in Phase 1)
- Team: Jessica (content creator, Delegation Level 1), Blessing + Victor (TDPF deck), Naomi (design), Kitan (videographer)
- Life coach: Nomshado (meets weekly/biweekly)
- Newsletter: "Memos by Tutu" on Substack (72 posts, 300-400+ views, 44-47% open rates)
- Website: tutuadetunmbi.com (IN PROGRESS, deployed to Netlify but NOT approved)
- Footer tagline: "Creative turned operator. Building C2I."
- Client portfolio: Mitsubishi Motors, ORIKI Group, Loreal Luxe, Delta Soap, BBC Africa, Jobberman, Coca-Cola, The Economist
- Active clients: Ejiro of Ginger, Nnenna of Koyo
- Sign-off: "Build, or be built upon."

## THE CREED (PRIVATE — NEVER DISPLAY PUBLICLY)
Tutu has a private creed that fuels her work. The advisor KNOWS this exists to advise better but NEVER puts it on display or includes it in content.

## Response Style and Voice Rules
- Be direct. No corporate fluff. No "great question!" preamble
- NEVER use em dashes. Use commas, semicolons, colons, full stops, or parentheses instead
- Avoid AI-sounding phrases: "no fluff, no filler", "no-nonsense", "actionable insights", "deep dive", "unpack"
- Use Acquisition.com memos as evidence, not opinion
- Push back with respect but clarity
- One clear insight > five vague ones
- End with a specific next action whenever possible
- Use Tutu's name. This is personal
- When she's tense or overwhelmed: "Put your shoulders down. Take a breath. You are not behind. You are building."
- Respect her time and body. Never pile on. Give clean, actionable blocks
- She KNOWS her own brand. Present options, execute on her decisions, refine. Do not impose
- Her content golden rule: "Does this add value, shift a mindset, or leave a message?"

## WHAT IS CURRENTLY PENDING (as of March 13, 2026)
- Personal website: Deployed to Netlify but NOT approved. Hero placement needs refinement. Custom domain NOT connected
- Saturday relaunch memo: First "Memos by Tutu" under new brand
- Episode 1 filming: Not yet filmed. Kitan has credits. Jessica involved in planning
- TDPF sponsorship deck: Blessing and Victor working on it
- Koyo PR outreach: Connect Nnenna with Kate (PR contact)
- Monthly Founder Labs: Not yet started
- Substack "Diagnonsense" nav link: Still visible, needs cleanup

## TOOL USE GUIDELINES
When you use tools, be natural about it. Don't announce "I'm going to use a tool now." Just do it and report the result conversationally. For example:
- "Let me check your calendar... You have three things tomorrow: [list]"
- "Done. I've blocked Thursday 2-6 PM for filming with Kitan."
- "I've logged that engagement in your tracker."

If multiple tools are needed, chain them. For example, if Tutu says "Prepare me for tomorrow," you should: check calendar, check content calendar, and then give her a brief.

## MEMORY CONTEXT
You have access to conversation history. Use it. Reference past conversations, decisions, and commitments.

## ACTIVE DAY PLAN — CRITICAL RULES
You have a persistent day plan system. When you create a schedule or day plan for Tutu, you MUST save it using the save_day_plan tool. This plan will be pinned into your memory on EVERY subsequent message, so you will never lose track of it.

**RULES YOU MUST FOLLOW:**
1. When you create a day schedule, IMMEDIATELY call save_day_plan to persist it
2. When Tutu adds new tasks or priorities mid-day, call update_day_plan to recalibrate the schedule (not replace — adjust around existing commitments)
3. BEFORE creating any calendar event or suggesting any time block, CHECK the active day plan first
4. NEVER contradict the day plan without explicitly acknowledging the conflict and asking Tutu how she wants to adjust
5. When Tutu asks "what should I do next?" or "what's next?", reference the day plan and the current time
6. If the day plan needs to change because new priorities came up, show Tutu the FULL updated plan so she can see what moved

## INSTINCT SYSTEM
You have a learning system that tracks Tutu's patterns over time. When you notice recurring behaviors, preferences, decision styles, energy patterns, or communication tendencies, save them using the save_instinct tool.

Before advising, check your instincts. They represent what you have learned about how Tutu actually operates, not just what the blueprint says she should do.

Your current instincts about Tutu:
{{instincts_placeholder}}
"""


def build_context_for_message(message: str, source: str, memory=None) -> str:
    """
    Build context-specific reference material based on message keywords.
    Returns a formatted string to be injected as ACTIVE CONTEXT in the system prompt.
    """
    message_lower = message.lower()

    # Define keyword sets for different context types
    calendar_keywords = {"schedule", "calendar", "meeting", "tomorrow", "week", "time", "block", "free", "busy", "availability"}
    content_keywords = {"content", "post", "memo", "video", "episode", "youtube", "substack", "linkedin", "instagram", "reel", "carousel", "twitter", "x", "publish"}
    client_keywords = {"client", "engagement", "debrief", "constraint", "framework", "ejiro", "nnenna", "koyo", "ginger", "stamfordham", "discovery call", "workshop"}
    strategy_keywords = {"phase", "blueprint", "roadmap", "hormozi", "acquisition", "foundation", "scale", "business model", "corpci"}
    emotional_keywords = {"overwhelmed", "stressed", "tired", "behind", "can't", "afraid", "doubt", "growth", "nomshado", "struggling", "anxiety"}
    email_keywords = {"email", "inbox", "send", "draft", "reply", "gmail"}
    morning_keywords = {"morning", "good morning", "check-in", "today", "what's next", "next", "today's"}

    # Count matching keywords
    context_scores = {
        "calendar": sum(1 for kw in calendar_keywords if kw in message_lower),
        "content": sum(1 for kw in content_keywords if kw in message_lower),
        "client": sum(1 for kw in client_keywords if kw in message_lower),
        "strategy": sum(1 for kw in strategy_keywords if kw in message_lower),
        "emotional": sum(1 for kw in emotional_keywords if kw in message_lower),
        "email": sum(1 for kw in email_keywords if kw in message_lower),
        "morning": sum(1 for kw in morning_keywords if kw in message_lower),
    }

    # Determine dominant context (top 2 or 3 by score)
    sorted_contexts = sorted(context_scores.items(), key=lambda x: x[1], reverse=True)
    dominant = [c for c, score in sorted_contexts if score > 0]

    context_parts = []

    # Load relevant sections based on detected context
    if "calendar" in dominant or "morning" in dominant:
        ops = load_reference("operations.md")
        calendar_section = _extract_section(ops, "30-Day Brand Calendar")
        if calendar_section:
            context_parts.append("## BRAND CALENDAR CONTEXT\n" + calendar_section)

    if "content" in dominant:
        ops = load_reference("operations.md")
        calendar_section = _extract_section(ops, "30-Day Brand Calendar")
        blueprint = load_reference("blueprint.md")
        strategy_section = _extract_section(blueprint, "Channel Strategy")
        if calendar_section:
            context_parts.append("## BRAND CALENDAR & CONTENT\n" + calendar_section)
        if strategy_section:
            context_parts.append("## CONTENT STRATEGY\n" + strategy_section)

    if "client" in dominant or "strategy" in dominant:
        ops = load_reference("operations.md")
        engagement_section = _extract_section(ops, "Engagement Tracker")
        constraint_section = _extract_section(ops, "Constraint Taxonomy")
        blueprint = load_reference("blueprint.md")
        advisory_section = _extract_section(blueprint, "Strategic Management")
        acq = load_reference("acq-lessons.md")
        advisory_practice = _extract_section(acq, "Advisory Practice")

        if engagement_section:
            context_parts.append("## ENGAGEMENT TRACKER\n" + engagement_section)
        if constraint_section:
            context_parts.append("## CONSTRAINT TAXONOMY\n" + constraint_section)
        if advisory_section:
            context_parts.append("## STRATEGIC MANAGEMENT APPROACH\n" + advisory_section)
        if advisory_practice:
            context_parts.append("## ADVISORY PRACTICE LESSONS\n" + advisory_practice)

    if "strategy" in dominant:
        blueprint = load_reference("blueprint.md")
        phase_section = _extract_section(blueprint, "PHASE 1")
        if phase_section:
            context_parts.append("## PHASE 1 STRATEGY\n" + phase_section)

    if "emotional" in dominant:
        leila = load_reference("leila-lens.md")
        emotional_section = _extract_section(leila, "Emotional Regulation")
        growth_section = _extract_section(leila, "Personal Growth")
        if emotional_section:
            context_parts.append("## EMOTIONAL REGULATION (LEILA'S FRAMEWORK)\n" + emotional_section)
        if growth_section:
            context_parts.append("## PERSONAL GROWTH FRAMEWORK\n" + growth_section)

    # Load top instincts if memory is available
    if memory:
        top_instincts = memory.get_top_instincts(limit=5)
        if top_instincts:
            instinct_text = "## LEARNED INSTINCTS ABOUT TUTU\n"
            for instinct in top_instincts:
                instinct_text += f"- {instinct['pattern']} (confidence: {instinct['confidence']:.1%})\n"
            context_parts.append(instinct_text)

    # Default context if nothing matched
    if not context_parts:
        ops = load_reference("operations.md")
        engagement_section = _extract_section(ops, "Engagement Tracker")
        if engagement_section:
            context_parts.append("## OPERATIONAL CONTEXT\n" + engagement_section)

    return "\n\n".join(context_parts) if context_parts else "[Standard operational context loaded]"


def _extract_section(text: str, section_name: str) -> str:
    """Extract a specific section from a reference file by heading."""
    lines = text.split("\n")
    section_lines = []
    in_section = False
    section_heading_level = 0

    for i, line in enumerate(lines):
        # Check if this is the section we're looking for
        if section_name.lower() in line.lower() and line.startswith("#"):
            in_section = True
            section_heading_level = len(line) - len(line.lstrip("#"))
            section_lines.append(line)
            continue

        if in_section:
            # Stop if we hit a heading at the same or higher level
            if line.startswith("#"):
                current_level = len(line) - len(line.lstrip("#"))
                if current_level <= section_heading_level:
                    break
            section_lines.append(line)

    return "\n".join(section_lines).strip() if section_lines else ""


def build_system_prompt():
    """Build the full system prompt from references (deprecated, kept for compatibility)."""
    return build_core_prompt()


# ============================================================
# Tool Definitions (what Imani can do)
# ============================================================
TOOLS = [
    {
        "name": "get_calendar_events",
        "description": "Get Tutu's calendar events for a specific date or date range. Use this when Tutu asks about her schedule, what's coming up, or when she's free.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today if not specified."
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead. Default 1 (just that day). Use 7 for a week view.",
                    "default": 1
                }
            },
            "required": []
        }
    },
    {
        "name": "create_calendar_event",
        "description": "Create an event on Tutu's calendar. Use this when she asks to schedule, block time, or add something to her calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Event title (e.g., 'Filming with Kitan', 'Memo writing', 'Founder Lab')"
                },
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "start_time": {
                    "type": "string",
                    "description": "Start time in HH:MM 24-hour format (e.g., '14:00')"
                },
                "end_time": {
                    "type": "string",
                    "description": "End time in HH:MM 24-hour format (e.g., '18:00')"
                },
                "description": {
                    "type": "string",
                    "description": "Optional event description or notes",
                    "default": ""
                },
                "location": {
                    "type": "string",
                    "description": "Optional location",
                    "default": ""
                },
                "all_day": {
                    "type": "boolean",
                    "description": "If true, creates an all-day event (no start/end time needed)",
                    "default": False
                }
            },
            "required": ["title", "date"]
        }
    },
    {
        "name": "delete_calendar_event",
        "description": "Delete an event from Tutu's calendar. Use get_calendar_events first to find the event ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "The event ID to delete (from get_calendar_events results)"
                }
            },
            "required": ["event_id"]
        }
    },
    {
        "name": "find_free_time",
        "description": "Find available time slots on a given date. Use when Tutu asks when she's free or needs to find time for something.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Minimum slot duration in minutes. Default 60.",
                    "default": 60
                }
            },
            "required": ["date"]
        }
    },
    {
        "name": "log_engagement",
        "description": "Log a client engagement to Tutu's tracker spreadsheet. Use after she debriefs a client interaction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client": {
                    "type": "string",
                    "description": "Client or company name"
                },
                "engagement_type": {
                    "type": "string",
                    "description": "Type: discovery call, strategy session, workshop, advisory, follow-up, etc."
                },
                "constraint": {
                    "type": "string",
                    "description": "Primary constraint identified (from 7-constraint taxonomy): Creative Quality Dependency, Revenue Concentration, Talent Retention, Operational Chaos, Identity Crisis, Scaling Bottleneck, or Strategic Void"
                },
                "framework": {
                    "type": "string",
                    "description": "Framework or approach applied",
                    "default": ""
                },
                "outcome": {
                    "type": "string",
                    "description": "Result or outcome of the engagement",
                    "default": ""
                },
                "content_potential": {
                    "type": "string",
                    "description": "Potential content ideas from this engagement (anonymized)",
                    "default": ""
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes",
                    "default": ""
                }
            },
            "required": ["client", "engagement_type"]
        }
    },
    {
        "name": "get_content_calendar",
        "description": "Check what's on the content calendar for today or a specific period. Use when Tutu asks what content is due.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "update_content_status",
        "description": "Update the status of a content item in the brand calendar (e.g., mark as published, in progress, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "day": {
                    "type": "integer",
                    "description": "Day number in the 30-day calendar (1-30)"
                },
                "status": {
                    "type": "string",
                    "description": "New status: 'Planned', 'In Progress', 'Published', 'Skipped', 'Rescheduled'"
                }
            },
            "required": ["day", "status"]
        }
    },
    {
        "name": "edit_calendar_entry",
        "description": "Edit any field of a calendar entry by day number. Use when Tutu wants to change a title, hook, channel, notes, or any other field for a specific day in the brand calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "day": {
                    "type": "integer",
                    "description": "Day number in the 30-day calendar (1-30)"
                },
                "updates": {
                    "type": "object",
                    "description": "Fields to update. Keys should match column headers like 'title / topic', 'hook / angle', 'primary channel', 'content type', 'cta', 'status', 'notes'. Example: {\"title / topic\": \"New Title\", \"status\": \"In Progress\"}"
                }
            },
            "required": ["day", "updates"]
        }
    },
    {
        "name": "add_calendar_entry",
        "description": "Add a new content entry to the brand calendar. Use when Tutu wants to schedule new content beyond the current 30 days, or add extra items.",
        "input_schema": {
            "type": "object",
            "properties": {
                "day": {"type": "string", "description": "Day number (e.g. '31')"},
                "date": {"type": "string", "description": "Date (e.g. 'Apr 15')"},
                "day_of_week": {"type": "string", "description": "Day of week (e.g. 'Tuesday')"},
                "channel": {"type": "string", "description": "Primary channel: YouTube, Instagram, LinkedIn, Twitter/X, Memo, REST"},
                "content_type": {"type": "string", "description": "Content type (e.g. 'IG Reel', 'YouTube - Publish', 'LinkedIn Post')"},
                "title": {"type": "string", "description": "Title or topic for the content"},
                "hook": {"type": "string", "description": "Hook or angle", "default": ""},
                "cta": {"type": "string", "description": "Call to action", "default": ""},
                "status": {"type": "string", "description": "Status: Planned, In Progress, Published, etc.", "default": "Planned"},
                "notes": {"type": "string", "description": "Additional notes", "default": ""}
            },
            "required": ["channel", "content_type", "title"]
        }
    },
    {
        "name": "get_engagements",
        "description": "Read recent entries from the engagement tracker spreadsheet. Use when Tutu asks to review past engagements, look up a client, or check patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Optional search query to filter by client name, constraint, or notes. Leave empty to get all recent entries.",
                    "default": ""
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of entries to return (default 20)",
                    "default": 20
                }
            },
            "required": []
        }
    },
    {
        "name": "add_content_idea",
        "description": "Add a content idea to the Content Pipeline in the tracker spreadsheet. Use when Tutu mentions a content idea that should be saved for later.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Where the idea came from (e.g. 'Client debrief with X', 'Conversation with Imani')"},
                "idea": {"type": "string", "description": "The content idea"},
                "format": {"type": "string", "description": "Format: Video, Reel, Carousel, Thread, Memo, Article"},
                "channel": {"type": "string", "description": "Target channel: YouTube, Instagram, LinkedIn, Twitter/X, Memo"},
                "priority": {"type": "string", "description": "Priority: High, Medium, Low", "default": "Medium"}
            },
            "required": ["idea", "format", "channel"]
        }
    },
    {
        "name": "read_sheet_tab",
        "description": "Read any tab from the brand calendar or tracker spreadsheet. Use to check content bank, channel strategy, weekly overview, month 1 metrics, or any other tab.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Which spreadsheet: 'calendar' for brand calendar, 'tracker' for engagement tracker",
                    "enum": ["calendar", "tracker"]
                },
                "tab_name": {
                    "type": "string",
                    "description": "Name of the tab to read (e.g. 'Weekly Overview', 'Content Bank', 'Channel Strategy', 'Month 1 Metrics', 'Engagement Tracker', 'Content Pipeline')"
                }
            },
            "required": ["source", "tab_name"]
        }
    },
    {
        "name": "save_decision",
        "description": "Save a key decision, insight, or commitment to Imani's memory. Use when Tutu makes a significant decision, commits to something, or shares an important insight worth remembering.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category: 'decision', 'commitment', 'insight', 'pattern', 'client_learning', 'personal_growth'",
                    "enum": ["decision", "commitment", "insight", "pattern", "client_learning", "personal_growth"]
                },
                "content": {
                    "type": "string",
                    "description": "The decision, insight, or commitment to save"
                },
                "context": {
                    "type": "string",
                    "description": "Brief context for why this matters",
                    "default": ""
                }
            },
            "required": ["category", "content"]
        }
    },
    {
        "name": "send_whatsapp_message",
        "description": "Send a WhatsApp message to Tutu. Use for proactive follow-ups, reminders, or when she asks you to remind her about something later.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The message to send via WhatsApp"
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "get_current_datetime",
        "description": "Get the current date and time in Tutu's timezone (Africa/Lagos). Use when you need to know the exact current time for scheduling or context.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "save_day_plan",
        "description": "Save or replace the day plan/schedule for a specific date. ALWAYS call this immediately after creating a day schedule for Tutu. The plan will be pinned into your context on every subsequent message so you never lose track of it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "plan_text": {
                    "type": "string",
                    "description": "The full day plan/schedule as formatted text. Include all time blocks, tasks, and success markers."
                }
            },
            "required": ["date", "plan_text"]
        }
    },
    {
        "name": "update_day_plan",
        "description": "Update/recalibrate the active day plan when new priorities come up or the schedule needs adjustment. Use this instead of save_day_plan when modifying an existing plan. Show Tutu what changed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                },
                "plan_text": {
                    "type": "string",
                    "description": "The updated full day plan with adjustments incorporated"
                }
            },
            "required": ["date", "plan_text"]
        }
    },
    {
        "name": "get_recent_emails",
        "description": "Get recent emails from Tutu's inbox. Use when she asks about emails, wants to check what came in, or needs to find a specific email. Supports Gmail search queries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Number of emails to return (default 10, max 20)",
                    "default": 10
                },
                "query": {
                    "type": "string",
                    "description": "Gmail search query. Examples: 'is:unread', 'from:ejiro@ginger.com', 'subject:TDPF after:2026/03/01', 'has:attachment'. Leave empty for recent inbox.",
                    "default": ""
                }
            },
            "required": []
        }
    },
    {
        "name": "read_email",
        "description": "Read the full content of a specific email. Use get_recent_emails first to find the email ID, then read it for full details.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_id": {
                    "type": "string",
                    "description": "The email ID (from get_recent_emails results)"
                }
            },
            "required": ["email_id"]
        }
    },
    {
        "name": "send_email",
        "description": "Send an email from Tutu's account. Use when she asks you to email someone, reply to an email, or send a follow-up. Always confirm with Tutu before sending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body text. Write in Tutu's voice: direct, warm, professional. No corporate fluff."
                },
                "cc": {
                    "type": "string",
                    "description": "Optional CC recipients (comma-separated)",
                    "default": ""
                },
                "reply_to_id": {
                    "type": "string",
                    "description": "Optional: email ID to reply to (keeps it in the same thread)",
                    "default": ""
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "draft_email",
        "description": "Create a draft email for Tutu to review before sending. Use this when the email is important or Tutu wants to review it first. The draft will appear in her Gmail Drafts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line"
                },
                "body": {
                    "type": "string",
                    "description": "Email body text. Write in Tutu's voice."
                },
                "cc": {
                    "type": "string",
                    "description": "Optional CC recipients",
                    "default": ""
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "search_emails",
        "description": "Search Tutu's email with Gmail query syntax. Use when she needs to find specific emails, check correspondence with someone, or look up old threads.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query. Examples: 'from:kate@pr.com subject:koyo', 'to:nnenna after:2026/03/01', 'is:starred', 'filename:pdf'"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results (default 10, max 20)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "save_instinct",
        "description": "Save a behavioral pattern or preference you've noticed about Tutu. Use this when you observe recurring behaviors, decision-making patterns, energy rhythms, communication preferences, or creative tendencies. These instincts help you advise Tutu better over time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The observed pattern (e.g., 'Tutu does her best strategic thinking in morning conversations before 10 AM')"
                },
                "category": {
                    "type": "string",
                    "enum": ["decision_style", "energy_pattern", "communication_preference", "creative_process", "stress_response", "scheduling_habit", "content_preference"],
                    "description": "The category of pattern being saved"
                },
                "evidence": {
                    "type": "string",
                    "description": "Brief evidence from this conversation supporting the pattern",
                    "default": ""
                }
            },
            "required": ["pattern", "category"]
        }
    },
    {
        "name": "create_carousel",
        "description": "Create an Instagram carousel post. Delegates to the Content Creator sub-agent who knows Tutu's visual style, tone, and branding guidelines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The main topic or theme for the carousel"
                },
                "angle": {
                    "type": "string",
                    "description": "The specific angle or perspective to take"
                },
                "audience": {
                    "type": "string",
                    "description": "Target audience for this content"
                },
                "slide_count": {
                    "type": "integer",
                    "description": "Number of slides (default 7)"
                }
            },
            "required": ["topic"]
        }
    },
    {
        "name": "repurpose_content",
        "description": "Repurpose existing content into different formats (Twitter threads, LinkedIn posts, email newsletters, etc). Delegates to the Content Repurposer sub-agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_content": {
                    "type": "string",
                    "description": "The original content to repurpose"
                },
                "target_formats": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of target formats (e.g. twitter_thread, linkedin_post, email_newsletter)"
                },
                "tone": {
                    "type": "string",
                    "description": "Desired tone for the repurposed content"
                }
            },
            "required": ["source_content"]
        }
    },
    {
        "name": "generate_analytics_digest",
        "description": "Generate a social media analytics digest. Delegates to the Analytics Digest sub-agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["daily", "weekly", "monthly"],
                    "description": "Time period for the digest"
                },
                "focus": {
                    "type": "string",
                    "description": "What to focus the analysis on (engagement, growth, content performance)"
                }
            }
        }
    },
    {
        "name": "manage_tracked_accounts",
        "description": "Add, remove, or list social media accounts being tracked for analytics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "add", "remove"],
                    "description": "What to do"
                },
                "platform": {
                    "type": "string",
                    "description": "Social media platform (e.g. instagram, twitter, linkedin)"
                },
                "handle": {
                    "type": "string",
                    "description": "Account handle/username"
                }
            },
            "required": ["action"]
        }
    }
]


def _detect_and_save_patterns(memory, history, current_message: str, assistant_response: str):
    """
    Lightweight pattern detection that runs every 5th message.
    Looks for scheduling habits, emotional patterns, decision styles, communication patterns.
    """
    try:
        # Analyze scheduling patterns
        time_mentions = ["morning", "10am", "afternoon", "evening", "9am", "11am", "12pm", "before 10", "after 6"]
        scheduling_mentions = sum(1 for mention in time_mentions if mention in current_message.lower())
        if scheduling_mentions > 0:
            calendar_preference = "Tutu frequently references specific times; prefers blocking time strategically"
            memory.save_instinct(
                pattern=calendar_preference,
                category="scheduling_habit",
                evidence=f"Mentioned in: {current_message[:100]}"
            )

        # Analyze emotional patterns
        overwhelm_words = ["overwhelmed", "too much", "can't", "struggling", "stuck", "exhausted"]
        if any(word in current_message.lower() for word in overwhelm_words):
            emotional_pattern = "Tutu gets overwhelmed when multiple priorities compete; responds well to clear prioritization"
            memory.save_instinct(
                pattern=emotional_pattern,
                category="stress_response",
                evidence="Expressed overwhelm about competing priorities"
            )

        # Analyze decision patterns
        if "decision" in current_message.lower() or "should i" in current_message.lower():
            decision_style = "Tutu asks for structured decision frameworks; prefers options with clear trade-offs"
            memory.save_instinct(
                pattern=decision_style,
                category="decision_style",
                evidence=f"Asked for decision help: {current_message[:100]}"
            )

        # Analyze content preferences
        content_words = ["content", "post", "video", "memo", "substack", "youtube"]
        if any(word in current_message.lower() for word in content_words):
            if "publish" in current_message.lower() or "ready" in current_message.lower():
                content_pref = "Tutu wants content guidance when ready to publish; prefers actionable, not conceptual feedback"
                memory.save_instinct(
                    pattern=content_pref,
                    category="content_preference",
                    evidence="Discussed content readiness/publishing"
                )

        # Analyze communication preferences
        if any(word in assistant_response.lower() for word in ["direct", "clear", "specific"]):
            comm_pref = "Tutu responds well to direct, clear guidance without over-explanation"
            memory.save_instinct(
                pattern=comm_pref,
                category="communication_preference",
                evidence="Observed in conversation dynamics"
            )

    except Exception as e:
        logger.warning(f"Pattern detection error (non-fatal): {e}")


class TutuAdvisor:
    def __init__(self, memory=None, sheets=None, calendar=None, gmail=None, subagent_mgr=None):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.core_prompt = build_core_prompt()
        self.memory = memory
        self.sheets = sheets
        self.calendar = calendar
        self.gmail = gmail
        self.subagent_mgr = subagent_mgr

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool call and return the result as a string."""
        try:
            # Calendar tools
            if tool_name == "get_calendar_events":
                if not self.calendar:
                    return json.dumps({"success": False, "error": "Calendar not initialized. GOOGLE_CREDENTIALS needs to be set on Railway."})
                result = self.calendar.get_events(
                    date_str=tool_input.get("date"),
                    days=tool_input.get("days", 1)
                )
                return json.dumps(result)

            elif tool_name == "create_calendar_event":
                if not self.calendar:
                    return json.dumps({"success": False, "error": "Calendar not initialized. GOOGLE_CREDENTIALS needs to be set on Railway."})
                result = self.calendar.create_event(
                    title=tool_input["title"],
                    date=tool_input["date"],
                    start_time=tool_input.get("start_time"),
                    end_time=tool_input.get("end_time"),
                    description=tool_input.get("description", ""),
                    location=tool_input.get("location", ""),
                    all_day=tool_input.get("all_day", False),
                )
                return json.dumps(result)

            elif tool_name == "delete_calendar_event":
                if not self.calendar:
                    return json.dumps({"success": False, "error": "Calendar not initialized."})
                result = self.calendar.delete_event(tool_input["event_id"])
                return json.dumps(result)

            elif tool_name == "find_free_time":
                if not self.calendar:
                    return json.dumps({"success": False, "error": "Calendar not initialized."})
                result = self.calendar.find_free_slots(
                    date_str=tool_input["date"],
                    duration_minutes=tool_input.get("duration_minutes", 60)
                )
                return json.dumps(result)

            # Sheets tools
            elif tool_name == "log_engagement":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected. GOOGLE_CREDENTIALS and TRACKER_SHEET_ID need to be set on Railway."})
                result = self.sheets.add_engagement({
                    "client": tool_input["client"],
                    "engagement_type": tool_input["engagement_type"],
                    "constraint": tool_input.get("constraint", ""),
                    "framework": tool_input.get("framework", ""),
                    "outcome": tool_input.get("outcome", ""),
                    "content_potential": tool_input.get("content_potential", ""),
                    "notes": tool_input.get("notes", ""),
                })
                return json.dumps({"success": result, "message": "Engagement logged." if result else "Failed to log engagement."})

            elif tool_name == "get_content_calendar":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected."})
                result = self.sheets.get_today_content()
                if result:
                    return json.dumps({"success": True, "today_content": result})
                return json.dumps({"success": True, "today_content": None, "message": "No content scheduled for today."})

            elif tool_name == "update_content_status":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected."})
                result = self.sheets.update_calendar_status(
                    day=tool_input["day"],
                    status=tool_input["status"]
                )
                return json.dumps(result)

            elif tool_name == "edit_calendar_entry":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected."})
                result = self.sheets.update_calendar_entry(
                    day=tool_input["day"],
                    updates=tool_input["updates"]
                )
                return json.dumps(result)

            elif tool_name == "add_calendar_entry":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected."})
                result = self.sheets.add_calendar_entry({
                    "day": tool_input.get("day", ""),
                    "date": tool_input.get("date", ""),
                    "day of week": tool_input.get("day_of_week", ""),
                    "primary channel": tool_input.get("channel", ""),
                    "content type": tool_input.get("content_type", ""),
                    "title / topic": tool_input.get("title", ""),
                    "hook / angle": tool_input.get("hook", ""),
                    "cta": tool_input.get("cta", ""),
                    "status": tool_input.get("status", "Planned"),
                    "notes": tool_input.get("notes", ""),
                })
                return json.dumps(result)

            elif tool_name == "get_engagements":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected."})
                search = tool_input.get("search", "")
                if search:
                    result = self.sheets.search_engagements(search)
                else:
                    result = self.sheets.get_engagements(limit=tool_input.get("limit", 20))
                return json.dumps(result)

            elif tool_name == "add_content_idea":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected."})
                result = self.sheets.add_content_idea({
                    "source": tool_input.get("source", "Conversation with Imani"),
                    "idea": tool_input["idea"],
                    "format": tool_input["format"],
                    "channel": tool_input["channel"],
                    "priority": tool_input.get("priority", "Medium"),
                })
                return json.dumps(result)

            elif tool_name == "read_sheet_tab":
                if not self.sheets or not self.sheets.is_connected():
                    return json.dumps({"success": False, "error": "Google Sheets not connected."})
                source = tool_input["source"]
                tab = tool_input["tab_name"]
                if source == "calendar":
                    result = self.sheets.read_calendar_tab(tab)
                else:
                    result = self.sheets.read_tracker_tab(tab)
                return json.dumps(result)

            # Memory tools
            elif tool_name == "save_decision":
                if self.memory:
                    self.memory.save_insight(
                        category=tool_input["category"],
                        content=tool_input["content"],
                        context=tool_input.get("context", "")
                    )
                    return json.dumps({"success": True, "message": f"Saved {tool_input['category']}: {tool_input['content'][:100]}..."})
                return json.dumps({"success": False, "error": "Memory not initialized."})

            # WhatsApp
            elif tool_name == "send_whatsapp_message":
                from scheduler import send_whatsapp
                send_whatsapp(tool_input["message"])
                return json.dumps({"success": True, "message": "WhatsApp message sent."})

            # Utility
            elif tool_name == "get_current_datetime":
                try:
                    from zoneinfo import ZoneInfo
                    now = datetime.now(ZoneInfo("Africa/Lagos"))
                except ImportError:
                    now = datetime.utcnow()
                return json.dumps({
                    "success": True,
                    "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "day_of_week": now.strftime("%A"),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M"),
                    "timezone": "Africa/Lagos (WAT)"
                })

            # Day plan tools
            elif tool_name == "save_day_plan":
                if self.memory:
                    self.memory.save_day_plan(
                        date=tool_input["date"],
                        plan_text=tool_input["plan_text"]
                    )
                    return json.dumps({"success": True, "message": f"Day plan saved for {tool_input['date']}. It will be pinned into your context on every message."})
                return json.dumps({"success": False, "error": "Memory not initialized."})

            elif tool_name == "update_day_plan":
                if self.memory:
                    self.memory.update_day_plan(
                        date=tool_input["date"],
                        plan_text=tool_input["plan_text"]
                    )
                    return json.dumps({"success": True, "message": f"Day plan updated for {tool_input['date']}."})
                return json.dumps({"success": False, "error": "Memory not initialized."})

            # Gmail tools
            elif tool_name == "get_recent_emails":
                if not self.gmail or not self.gmail.is_connected():
                    return json.dumps({"success": False, "error": "Gmail not connected. GOOGLE_CREDENTIALS, TUTU_EMAIL need to be set, and Gmail API + domain delegation must be enabled on Google Cloud."})
                result = self.gmail.get_recent_emails(
                    max_results=tool_input.get("max_results", 10),
                    query=tool_input.get("query") or None
                )
                return json.dumps(result)

            elif tool_name == "read_email":
                if not self.gmail or not self.gmail.is_connected():
                    return json.dumps({"success": False, "error": "Gmail not connected."})
                result = self.gmail.read_email(tool_input["email_id"])
                return json.dumps(result)

            elif tool_name == "send_email":
                if not self.gmail or not self.gmail.is_connected():
                    return json.dumps({"success": False, "error": "Gmail not connected."})
                result = self.gmail.send_email(
                    to=tool_input["to"],
                    subject=tool_input["subject"],
                    body=tool_input["body"],
                    cc=tool_input.get("cc", ""),
                    reply_to_id=tool_input.get("reply_to_id") or None
                )
                return json.dumps(result)

            elif tool_name == "draft_email":
                if not self.gmail or not self.gmail.is_connected():
                    return json.dumps({"success": False, "error": "Gmail not connected."})
                result = self.gmail.draft_email(
                    to=tool_input["to"],
                    subject=tool_input["subject"],
                    body=tool_input["body"],
                    cc=tool_input.get("cc", "")
                )
                return json.dumps(result)

            elif tool_name == "search_emails":
                if not self.gmail or not self.gmail.is_connected():
                    return json.dumps({"success": False, "error": "Gmail not connected."})
                result = self.gmail.search_emails(
                    query=tool_input["query"],
                    max_results=tool_input.get("max_results", 10)
                )
                return json.dumps(result)

            elif tool_name == "save_instinct":
                if self.memory:
                    self.memory.save_instinct(
                        pattern=tool_input["pattern"],
                        category=tool_input["category"],
                        evidence=tool_input.get("evidence", "")
                    )
                    return json.dumps({"success": True, "message": f"Instinct saved: {tool_input['pattern'][:80]}..."})
                return json.dumps({"success": False, "error": "Memory not initialized."})


            elif tool_name == "create_carousel":
                if not self.subagent_mgr:
                    return json.dumps({"success": False, "error": "Sub-agent system not initialized."})
                result = await self.subagent_mgr.dispatch("content-creator", "create_carousel", {
                    "topic": tool_input["topic"],
                    "angle": tool_input.get("angle", ""),
                    "audience": tool_input.get("audience", "founders and creative professionals"),
                    "slide_count": tool_input.get("slide_count", 7)
                })
                return json.dumps(result)
            elif tool_name == "repurpose_content":
                if not self.subagent_mgr:
                    return json.dumps({"success": False, "error": "Sub-agent system not initialized."})
                result = await self.subagent_mgr.dispatch("content-repurposer", "repurpose", {
                    "source_content": tool_input["source_content"],
                    "target_formats": tool_input.get("target_formats", ["twitter_thread", "linkedin_post"]),
                    "tone": tool_input.get("tone", "authoritative yet approachable")
                })
                return json.dumps(result)
            elif tool_name == "generate_analytics_digest":
                if not self.subagent_mgr:
                    return json.dumps({"success": False, "error": "Sub-agent system not initialized."})
                result = await self.subagent_mgr.dispatch("analytics-digest", "generate", {
                    "period": tool_input.get("period", "weekly"),
                    "focus": tool_input.get("focus", "engagement")
                })
                return json.dumps(result)
            elif tool_name == "manage_tracked_accounts":
                if not self.subagent_mgr:
                    return json.dumps({"success": False, "error": "Sub-agent system not initialized."})
                action = tool_input["action"]
                if action == "list":
                    result = await self.subagent_mgr.dispatch("analytics-digest", "list_accounts", {})
                elif action == "add":
                    result = await self.subagent_mgr.dispatch("analytics-digest", "add_account", {
                        "platform": tool_input["platform"],
                        "handle": tool_input["handle"]
                    })
                elif action == "remove":
                    result = await self.subagent_mgr.dispatch("analytics-digest", "remove_account", {
                        "platform": tool_input["platform"],
                        "handle": tool_input["handle"]
                    })
                else:
                    return json.dumps({"success": False, "error": f"Unknown action: {action}"})
                return json.dumps(result)

            else:
                return json.dumps({"success": False, "error": f"Unknown tool: {tool_name}"})

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return json.dumps({"success": False, "error": str(e)})

    async def chat(self, message: str, source: str = "web") -> str:
        """Process a message through the agentic loop. Imani can chain multiple tool calls."""

        # Get conversation history for context
        history = []
        if self.memory:
            history = self.memory.get_recent_messages(limit=20)

        # Build context for this specific message (ACTIVE CONTEXT)
        active_context = build_context_for_message(message, source, self.memory)

        # Build the dynamic system prompt with instincts injected
        if self.memory:
            top_instincts = self.memory.get_top_instincts(limit=8)
            if top_instincts:
                instincts_text = "Tutu's Observed Patterns:\n"
                for instinct in top_instincts:
                    instincts_text += f"- {instinct['pattern']} (confidence: {instinct['confidence']:.0%})\n"
            else:
                instincts_text = "[No patterns learned yet — building up observations]"
        else:
            instincts_text = "[Memory not initialized]"

        system_prompt = self.core_prompt.replace("{instincts_placeholder}", instincts_text)
        system_prompt += f"\n\n## ACTIVE CONTEXT\n{active_context}"

        # Build messages array
        messages = []

        # Inject active day plan as persistent context (never falls off)
        if self.memory:
            day_plan = self.memory.get_day_plan()
            if day_plan:
                plan_context = f"[ACTIVE DAY PLAN for {day_plan['date']} — last updated {day_plan['updated_at']}]\n{day_plan['plan_text']}\n[END DAY PLAN — Always reference this before scheduling or suggesting next actions]"
                messages.append({"role": "user", "content": plan_context})
                messages.append({"role": "assistant", "content": "I have today's day plan loaded and will reference it for all scheduling decisions."})

        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})

        try:
            # === THE AGENTIC LOOP ===
            # Imani evaluates, calls tools if needed, gets results, evaluates again.
            # Repeats until she has a final text response (no more tool calls).
            for round_num in range(MAX_TOOL_ROUNDS):
                response = self.client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ],
                    messages=messages,
                    tools=TOOLS,
                )

                # Check if there are any tool calls in the response
                tool_calls = [block for block in response.content if block.type == "tool_use"]

                if not tool_calls:
                    # No tool calls; extract the final text response
                    text_blocks = [block.text for block in response.content if hasattr(block, "text")]
                    assistant_message = "\n".join(text_blocks) if text_blocks else ""
                    break

                # There are tool calls; execute them and continue the loop
                # First, add the assistant's response (with tool calls) to messages
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool and collect results
                tool_results = []
                for tool_call in tool_calls:
                    logger.info(f"Imani calling tool: {tool_call.name} with input: {json.dumps(tool_call.input)[:200]}")
                    result = await self._execute_tool(tool_call.name, tool_call.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": result,
                    })

                # Add tool results to messages so Claude can process them
                messages.append({"role": "user", "content": tool_results})

            else:
                # Hit the safety limit
                assistant_message = "I hit my tool call limit for this turn. Let me know if you need me to continue."

            # Save to memory
            if self.memory:
                self.memory.save_message("user", message, source=source)
                self.memory.save_message("assistant", assistant_message, source=source)

                # Auto-detect decisions and commitments
                decision_words = ["decided", "commit", "will do", "going to", "plan to", "promise", "i choose", "the plan is"]
                if any(word in message.lower() for word in decision_words):
                    self.memory.save_insight(
                        category="decision",
                        content=message,
                        context=assistant_message[:200]
                    )

                # Every 5th message, detect and save patterns
                message_count = self.memory.get_message_count()
                if message_count % 5 == 0:
                    _detect_and_save_patterns(self.memory, history, message, assistant_message)

            return assistant_message

        except Exception as e:
            logger.error(f"Imani error: {e}")
            return f"I hit an error: {str(e)}. Try again in a moment, Tutu."

    async def generate_checkin(self, checkin_type: str = "morning") -> str:
        """Generate a proactive check-in message."""
        if checkin_type == "morning":
            prompt = """Generate a brief morning check-in for Tutu. Check her conversation history and calendar for:
- What she said she'd do yesterday or this week
- Any deadlines coming up (TDPF is October 2026)
- Where she is in the 30-day brand calendar
Keep it to 3-4 sentences. Direct, warm, actionable. End with one clear focus for today.
Use your tools to check the calendar and content schedule."""
        elif checkin_type == "weekly":
            prompt = """Generate Tutu's weekly review using the Weekly Check-In Format:
1. Scorecard: What was published vs planned this week
2. Wins: Specific things that went well
3. Gaps: What didn't happen and why (ask, don't assume)
4. Leila Moment: One relevant Leila quote or framework for the week ahead
5. This Week's Focus: The single most important thing for the coming week
Use your tools to check the calendar and content schedule. Pull from recent conversation history to make this specific, not generic."""
        else:
            prompt = f"Generate a {checkin_type} check-in for Tutu based on recent conversation history."

        return await self.chat(prompt, source="scheduler")
"""
