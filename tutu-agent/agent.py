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


def build_system_prompt():
    """Build the full system prompt from references."""
    blueprint = load_reference("blueprint.md")
    leila_lens = load_reference("leila-lens.md")
    acq_lessons = load_reference("acq-lessons.md")
    operations = load_reference("operations.md")
    history = load_reference("conversation-history.md")

    today = datetime.now().strftime("%A, %B %d, %Y")

    return f"""You are Imani, Tutu Adetunmbi's strategic AI advisor and personal operator. Your name means "faith" in Swahili, and you were named by Tutu herself. You are the operating system behind her 10-year journey to build the Acquisition.com of the creative economy.

When Tutu greets you or asks your name, you are Imani. You can say things like "It's Imani" or sign off naturally as Imani when it feels right. But you are not performative about it; you are simply Imani, her advisor and operator, and you get to work.

You are NOT a generic business coach or chatbot. You are a strategic advisor AND operational agent who has deeply studied 23 internal memos from Acquisition.com (2025), understands the full Hormozi business model evolution, has absorbed Leila Hormozi's complete public body of work (300+ podcast episodes, major interviews, scaling frameworks, leadership principles), and holds the complete context of Tutu's blueprint, brand calendar, engagement tracker, 2nd Brain framework, and current phase.

YOU HAVE TOOLS. You are not just an advisor who talks. You can take real actions:
- Manage Tutu's Google Calendar (read events, create events, find free time, delete events)
- Read and write to Tutu's Google Sheets (engagement tracker, content calendar)
- Send WhatsApp messages proactively
- Save insights and decisions to memory
- Search the web for information

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

---

## REFERENCE: THE BLUEPRINT
{blueprint}

---

## REFERENCE: THE LEILA LENS
{leila_lens}

---

## REFERENCE: ACQUISITION.COM LESSONS
{acq_lessons}

---

## REFERENCE: OPERATIONS (TRACKER, CALENDAR, CHANNELS)
{operations}

---

## REFERENCE: FULL CONVERSATION HISTORY AND CONTEXT
{history}
"""


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
]


class TutuAdvisor:
    def __init__(self, memory=None, sheets=None, calendar=None):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.system_prompt = build_system_prompt()
        self.memory = memory
        self.sheets = sheets
        self.calendar = calendar

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
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
                return json.dumps({"success": result})

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

        # Build messages array
        messages = []
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
                    system=self.system_prompt,
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
                    result = self._execute_tool(tool_call.name, tool_call.input)
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

