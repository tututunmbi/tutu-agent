"""
Imani Sub-Agents — Specialized operators that extend Imani's capabilities.

Sub-Agent Architecture:
  - Each sub-agent is a focused AI operator with its own prompt, memory, and tools
  - Imani (the orchestrator) dispatches tasks to sub-agents
  - Sub-agents produce drafts that go to Tutu/Jessica for review
  - Each sub-agent learns from feedback and improves over time

Current Sub-Agents:
  1. Content Repurposer — Takes YouTube content and generates platform-specific versions
  2. Analytics Digest — Weekly performance intelligence + competitor/inspiration tracking
  3. Content Creator — Produces carousel drafts and visual content via Canva

Future:
  4. Trend Scout — Monitors trends across platforms
  5. Brand Voice Guardian — Ensures consistency
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sub-Agent Base
# ---------------------------------------------------------------------------

class SubAgentMemory:
    """Simple file-based memory for sub-agent preferences and feedback."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.memory_dir = os.path.join(os.path.dirname(__file__), "subagent_data")
        os.makedirs(self.memory_dir, exist_ok=True)
        self._file = os.path.join(self.memory_dir, f"{agent_id}.json")
        self._data = self._load()

    def _load(self) -> dict:
        try:
            with open(self._file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "preferences": {},
                "feedback_log": [],
                "style_notes": [],
                "accounts_tracking": [],
                "created": datetime.utcnow().isoformat(),
            }

    def save(self):
        with open(self._file, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()

    def add_feedback(self, item_id: str, feedback: str, rating: str = "neutral"):
        """Log feedback on a produced item (carousel, post, digest)."""
        self._data["feedback_log"].append({
            "item_id": item_id,
            "feedback": feedback,
            "rating": rating,  # "approved", "revised", "rejected"
            "timestamp": datetime.utcnow().isoformat(),
        })
        # Keep last 200 feedback entries
        self._data["feedback_log"] = self._data["feedback_log"][-200:]
        self.save()

    def add_style_note(self, note: str):
        """Store a voice/style observation learned from feedback."""
        self._data["style_notes"].append({
            "note": note,
            "timestamp": datetime.utcnow().isoformat(),
        })
        self._data["style_notes"] = self._data["style_notes"][-50:]
        self.save()

    def get_style_notes(self) -> list:
        return [n["note"] for n in self._data.get("style_notes", [])]

    def add_tracked_account(self, platform: str, handle: str, category: str = "inspiration"):
        """Add a competitor/inspiration account to track."""
        self._data.setdefault("accounts_tracking", [])
        # Avoid duplicates
        for acct in self._data["accounts_tracking"]:
            if acct["handle"].lower() == handle.lower() and acct["platform"].lower() == platform.lower():
                acct["category"] = category  # update category
                self.save()
                return
        self._data["accounts_tracking"].append({
            "platform": platform,
            "handle": handle,
            "category": category,  # "competitor", "inspiration", "industry_leader"
            "added": datetime.utcnow().isoformat(),
        })
        self.save()

    def remove_tracked_account(self, platform: str, handle: str):
        self._data["accounts_tracking"] = [
            a for a in self._data.get("accounts_tracking", [])
            if not (a["handle"].lower() == handle.lower() and a["platform"].lower() == platform.lower())
        ]
        self.save()

    def get_tracked_accounts(self) -> list:
        return self._data.get("accounts_tracking", [])

    def get_recent_feedback(self, limit: int = 20) -> list:
        return self._data.get("feedback_log", [])[-limit:]


# ---------------------------------------------------------------------------
# 1. Content Repurposer Sub-Agent
# ---------------------------------------------------------------------------

class ContentRepurposer:
    """
    Takes a YouTube video transcript/content and generates platform-specific versions:
    - Instagram carousel (3-5 key points)
    - LinkedIn post (B2B reframe of the core idea)
    - Twitter/X thread (hooks + key insights)
    - TikTok script (short, punchy cut suggestions)
    - Memo section (if relevant to Saturday newsletter)
    """

    AGENT_ID = "content-repurposer"
    STATUS_ACTIVE = "active"

    def __init__(self):
        self.memory = SubAgentMemory(self.AGENT_ID)
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._client

    def status(self) -> dict:
        return {
            "id": self.AGENT_ID,
            "name": "Content Repurposer",
            "status": self.STATUS_ACTIVE,
            "description": "Takes YouTube content and generates platform-specific versions",
            "icon": "&#9998;",
            "color": "var(--accent)",
            "bg": "var(--accent-subtle)",
            "stats": {
                "items_produced": len(self.memory.get("produced_items", [])),
                "style_notes": len(self.memory.get_style_notes()),
            },
        }

    async def repurpose(self, source_content: str, source_platform: str = "youtube",
                        target_platforms: list = None, context: str = "") -> dict:
        """
        Generate repurposed content for multiple platforms from a single source.

        Args:
            source_content: The original content (transcript, script, or text)
            source_platform: Where the content originated
            target_platforms: List of platforms to generate for (default: all)
            context: Additional context (topic, CTA, audience notes)

        Returns:
            Dict with platform keys and generated content
        """
        if target_platforms is None:
            target_platforms = ["instagram", "linkedin", "twitter", "tiktok", "memo"]

        style_notes = self.memory.get_style_notes()
        recent_feedback = self.memory.get_recent_feedback(10)

        style_context = ""
        if style_notes:
            style_context = "\n\nSTYLE NOTES (learned from Tutu's feedback):\n" + "\n".join(f"- {n}" for n in style_notes[-10:])

        feedback_context = ""
        if recent_feedback:
            approved = [f for f in recent_feedback if f["rating"] == "approved"]
            revised = [f for f in recent_feedback if f["rating"] == "revised"]
            if approved:
                feedback_context += f"\n\nRecent approved items: {len(approved)}. "
            if revised:
                feedback_context += f"Items needing revision: {len(revised)}. Common revision notes: "
                feedback_context += "; ".join(r["feedback"][:100] for r in revised[-3:])

        prompt = f"""You are the Content Repurposer sub-agent for Imani, Tutu Adetunmbi's strategic AI advisor.

Your job: Take content from {source_platform} and create platform-specific versions that maintain Tutu's voice and brand.

TUTU'S VOICE RULES:
- Direct, strategic, honest. No corporate fluff
- NEVER use em dashes. Use commas, semicolons, colons, or full stops
- Avoid: "no fluff, no filler", "no-nonsense", "actionable insights", "deep dive", "unpack"
- Golden rule: "Does this add value, shift a mindset, or leave a message?"
- Bio reference: "Creative turned operator. Building the business that builds corporate creative institutions."
- Sign-off: "Build, or be built upon."
- She is The Oracle of the Corporate Creative Industry
{style_context}
{feedback_context}

CHANNEL STRATEGY:
- YouTube: Long-form frameworks + Build With Me vlogs. Authority. Top of funnel
- Instagram: Clips, punchy reframes, BTS. Familiarity. Middle of funnel. Carousels on Saturday
- LinkedIn: Written thought leadership. B2B credibility. Bottom of funnel
- Twitter/X: Real-time thinking, threads, industry reactions. Discovery
- Memos: Deepest, most honest content. Follower to true believer conversion. Saturday morning

EVERY piece of content needs a CTA driving somewhere (email list, YouTube, Founder Lab signup).

SOURCE CONTENT ({source_platform}):
{source_content}

{f"ADDITIONAL CONTEXT: {context}" if context else ""}

Generate content for these platforms: {", ".join(target_platforms)}

For each platform, output JSON with this structure:
{{
  "platform": "platform_name",
  "content_type": "type (carousel/post/thread/script/memo_section)",
  "headline": "the hook or first line",
  "body": "the full content",
  "cta": "the call to action",
  "hashtags": ["relevant", "hashtags"],
  "notes": "production notes for Jessica"
}}

Return a JSON array of all platform outputs."""

        try:
            client = self._get_client()
            response = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse the response
            text = response.content[0].text
            # Try to extract JSON from the response
            try:
                # Find JSON array in response
                start = text.index("[")
                end = text.rindex("]") + 1
                results = json.loads(text[start:end])
            except (ValueError, json.JSONDecodeError):
                results = [{"platform": "raw", "content_type": "text", "body": text}]

            # Log production
            item_id = f"repurpose-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            produced = self.memory.get("produced_items", [])
            produced.append({
                "id": item_id,
                "source_platform": source_platform,
                "targets": target_platforms,
                "timestamp": datetime.utcnow().isoformat(),
            })
            self.memory.set("produced_items", produced[-100:])

            return {
                "success": True,
                "item_id": item_id,
                "results": results,
                "source_platform": source_platform,
            }

        except Exception as e:
            logger.error("Content Repurposer error: %s", e)
            return {"success": False, "error": str(e)}

    def submit_feedback(self, item_id: str, platform: str, feedback: str, rating: str):
        """Process feedback on a repurposed item."""
        self.memory.add_feedback(item_id, f"[{platform}] {feedback}", rating)

        # If revised or rejected, extract a style learning
        if rating in ("revised", "rejected") and feedback:
            self.memory.add_style_note(f"Feedback on {platform}: {feedback[:200]}")

        return {"success": True, "message": f"Feedback recorded for {item_id}"}


# ---------------------------------------------------------------------------
# 2. Analytics Digest Sub-Agent
# ---------------------------------------------------------------------------

class AnalyticsDigest:
    """
    Weekly intelligence briefing:
    - Performance summary across all platforms
    - Week-over-week trends
    - Top performing content analysis
    - Competitor/inspiration account tracking
    - Hook and strategy observations from tracked accounts
    - Recommendations for next week
    """

    AGENT_ID = "analytics-digest"
    STATUS_ACTIVE = "active"

    def __init__(self, metricool_client=None):
        self.memory = SubAgentMemory(self.AGENT_ID)
        self.metricool = metricool_client
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._client

    def status(self) -> dict:
        tracked = self.memory.get_tracked_accounts()
        return {
            "id": self.AGENT_ID,
            "name": "Analytics Digest",
            "status": self.STATUS_ACTIVE,
            "description": "Weekly performance intelligence + competitor tracking",
            "icon": "&#9783;",
            "color": "var(--instagram)",
            "bg": "var(--instagram-bg)",
            "stats": {
                "tracked_accounts": len(tracked),
                "digests_produced": len(self.memory.get("digests", [])),
            },
        }

    def add_account(self, platform: str, handle: str, category: str = "inspiration") -> dict:
        """Add a competitor/inspiration account to track."""
        self.memory.add_tracked_account(platform, handle, category)
        return {
            "success": True,
            "message": f"Now tracking @{handle} on {platform} as {category}",
            "total_tracked": len(self.memory.get_tracked_accounts()),
        }

    def remove_account(self, platform: str, handle: str) -> dict:
        """Remove a tracked account."""
        self.memory.remove_tracked_account(platform, handle)
        return {
            "success": True,
            "message": f"Stopped tracking @{handle} on {platform}",
            "total_tracked": len(self.memory.get_tracked_accounts()),
        }

    def list_accounts(self) -> list:
        """List all tracked accounts."""
        return self.memory.get_tracked_accounts()

    async def generate_digest(self, days: int = 7) -> dict:
        """
        Generate the weekly analytics digest.
        Pulls Metricool data and produces an AI-analyzed intelligence brief.
        """
        # Gather platform data
        platform_data = {}
        if self.metricool and self.metricool.is_connected():
            try:
                overview = await self.metricool.dashboard_overview(days=days)
                platform_data = overview
            except Exception as e:
                logger.error("Analytics Digest: Metricool error: %s", e)

        tracked_accounts = self.memory.get_tracked_accounts()
        previous_digests = self.memory.get("digests", [])
        last_digest_summary = ""
        if previous_digests:
            last = previous_digests[-1]
            last_digest_summary = f"Last digest ({last.get('date', 'unknown')}): {last.get('summary', 'No summary')}"

        prompt = f"""You are the Analytics Digest sub-agent for Imani, Tutu Adetunmbi's strategic AI advisor.

Your job: Produce a weekly intelligence briefing that helps Tutu make smart content decisions.

TUTU'S CONTEXT:
- Phase 1: The Foundation. Building the media engine
- Channels: YouTube (authority), Instagram (familiarity), LinkedIn (B2B credibility), Twitter/X (discovery), TikTok (growth), Memos (conversion)
- Key metrics: engagement rate, follower growth, content velocity, email signups
- Goal: Small but engaged audience. Quality over vanity metrics

PLATFORM DATA (last {days} days):
{json.dumps(platform_data, indent=2, default=str)[:6000]}

TRACKED ACCOUNTS FOR COMPETITOR INTELLIGENCE:
{json.dumps(tracked_accounts, indent=2) if tracked_accounts else "No accounts tracked yet. Recommend Tutu adds 5-10 inspiration/competitor accounts."}

{f"PREVIOUS DIGEST CONTEXT: {last_digest_summary}" if last_digest_summary else "This is the first digest."}

Produce a digest with these sections:
1. PERFORMANCE SNAPSHOT: Key numbers across all platforms (engagement, reach, growth)
2. TOP PERFORMERS: Which posts did best and why (hook analysis, format analysis)
3. TRENDS: Week-over-week changes, patterns emerging
4. COMPETITOR/INSPIRATION INTEL: Observations on tracked accounts (what hooks are working in her space, content formats trending, posting patterns)
5. RECOMMENDATIONS: 3-5 specific, actionable recommendations for next week
6. CONTENT OPPORTUNITIES: Timely topics or formats to try based on what's working

Keep it operator-level. No fluff. Tutu needs intelligence, not a report card.

Output as JSON:
{{
  "summary": "One-line summary of the week",
  "snapshot": {{ "platform_summaries": [...] }},
  "top_performers": [...],
  "trends": [...],
  "competitor_intel": [...],
  "recommendations": [...],
  "content_opportunities": [...]
}}"""

        try:
            client = self._get_client()
            response = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                digest = json.loads(text[start:end])
            except (ValueError, json.JSONDecodeError):
                digest = {"summary": "Digest generated", "raw": text}

            # Save digest to memory
            digest_entry = {
                "date": datetime.utcnow().isoformat(),
                "days_covered": days,
                "summary": digest.get("summary", ""),
                "tracked_accounts_count": len(tracked_accounts),
            }
            digests = self.memory.get("digests", [])
            digests.append(digest_entry)
            self.memory.set("digests", digests[-52:])  # Keep a year of weekly digests

            return {
                "success": True,
                "digest": digest,
                "period": f"Last {days} days",
                "tracked_accounts": len(tracked_accounts),
            }

        except Exception as e:
            logger.error("Analytics Digest error: %s", e)
            return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# 3. Content Creator Sub-Agent
# ---------------------------------------------------------------------------

class ContentCreator:
    """
    Creates visual content drafts:
    - Instagram carousels (structure, copy, visual direction)
    - Post graphics (quotes, stats, tips)
    - Story templates

    Future: Direct Canva API integration for automated design.
    Currently: Produces structured drafts with visual direction for Jessica/Tutu.

    Delegation Level: 1 (investigate and report / produce drafts for review)
    Goal: Graduate to Level 4 (full autonomy) as trust builds.
    """

    AGENT_ID = "content-creator"
    STATUS_ACTIVE = "active"

    def __init__(self):
        self.memory = SubAgentMemory(self.AGENT_ID)
        self._client = None

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._client

    def status(self) -> dict:
        return {
            "id": self.AGENT_ID,
            "name": "Content Creator",
            "status": self.STATUS_ACTIVE,
            "description": "Carousel drafts and visual content with Canva integration (coming)",
            "icon": "&#9998;",
            "color": "var(--accent)",
            "bg": "var(--accent-subtle)",
            "stats": {
                "drafts_produced": len(self.memory.get("drafts", [])),
                "approved": len([f for f in self.memory.get_recent_feedback(100) if f["rating"] == "approved"]),
                "delegation_level": self.memory.get("delegation_level", 1),
            },
        }

    async def create_carousel(self, topic: str, platform: str = "instagram",
                               slides: int = 5, context: str = "",
                               reference_content: str = "") -> dict:
        """
        Create a carousel draft with slide-by-slide content and visual direction.

        Args:
            topic: The carousel topic/theme
            platform: Target platform (instagram, linkedin)
            slides: Number of slides (3-10)
            context: Additional context or angle
            reference_content: Source material to draw from (transcript, notes, etc.)

        Returns:
            Structured carousel draft ready for review
        """
        style_notes = self.memory.get_style_notes()
        carousel_examples = self.memory.get("carousel_examples", [])
        delegation_level = self.memory.get("delegation_level", 1)

        style_context = ""
        if style_notes:
            style_context = "\nSTYLE NOTES (learned from feedback):\n" + "\n".join(f"- {n}" for n in style_notes[-10:])

        examples_context = ""
        if carousel_examples:
            examples_context = "\nCAROUSEL EXAMPLES TUTU LIKES:\n"
            for ex in carousel_examples[-5:]:
                examples_context += f"- {ex.get('description', 'Example')}: {ex.get('notes', '')}\n"

        prompt = f"""You are the Content Creator sub-agent for Imani, Tutu Adetunmbi's strategic AI advisor.

Your job: Create a {slides}-slide carousel draft for {platform} on the topic: "{topic}"

TUTU'S BRAND:
- The Oracle of the Corporate Creative Industry
- Creative turned operator. Building C2I
- Bio: "Creative turned operator. Building the business that builds corporate creative institutions."
- Colors: Deep warm tones, gold accents (like her crest: gold eagle with laurel wreath)
- Font feel: Premium, editorial, not corporate. Think high-end magazine meets strategic operator
- Imagery: Bold, African identity, professional but not sterile
- NEVER use em dashes. Use commas, semicolons, colons, or full stops
- Sign-off: "Build, or be built upon."

DELEGATION LEVEL: {delegation_level}/4 ({"Draft for review" if delegation_level <= 2 else "Ready to post with light review" if delegation_level == 3 else "Full autonomy"})
{style_context}
{examples_context}

{f"REFERENCE CONTENT: {reference_content[:3000]}" if reference_content else ""}
{f"ADDITIONAL CONTEXT: {context}" if context else ""}

Create a carousel with this structure for each slide:

{{
  "carousel": {{
    "topic": "...",
    "platform": "{platform}",
    "total_slides": {slides},
    "hook_headline": "The cover slide headline (this is the hook that stops the scroll)",
    "slides": [
      {{
        "slide_number": 1,
        "type": "cover",
        "headline": "The big hook headline",
        "subtext": "Optional supporting line",
        "visual_direction": "Description of what this slide should look like (colors, layout, imagery)",
        "notes": "Why this hook works"
      }},
      {{
        "slide_number": 2,
        "type": "content",
        "headline": "Slide headline",
        "body": "The main text content for this slide (keep concise)",
        "visual_direction": "Visual notes",
        "notes": "Production notes"
      }},
      ...
      {{
        "slide_number": {slides},
        "type": "cta",
        "headline": "Call to action headline",
        "body": "What you want them to do",
        "cta_type": "follow/save/link_in_bio/newsletter",
        "visual_direction": "Visual notes"
      }}
    ],
    "caption": "The full Instagram/LinkedIn caption to accompany the carousel",
    "hashtags": ["relevant", "hashtags"],
    "posting_notes": "Best time to post, any scheduling notes"
  }}
}}"""

        try:
            client = self._get_client()
            response = client.messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text
            try:
                start = text.index("{")
                end = text.rindex("}") + 1
                carousel = json.loads(text[start:end])
            except (ValueError, json.JSONDecodeError):
                carousel = {"raw": text, "topic": topic}

            # Log the draft
            draft_id = f"carousel-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            drafts = self.memory.get("drafts", [])
            drafts.append({
                "id": draft_id,
                "type": "carousel",
                "topic": topic,
                "platform": platform,
                "slides": slides,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "draft",
            })
            self.memory.set("drafts", drafts[-100:])

            return {
                "success": True,
                "draft_id": draft_id,
                "carousel": carousel,
                "delegation_level": delegation_level,
                "status": "draft_for_review" if delegation_level <= 2 else "ready_to_post",
            }

        except Exception as e:
            logger.error("Content Creator error: %s", e)
            return {"success": False, "error": str(e)}

    def add_example(self, description: str, notes: str, url: str = "") -> dict:
        """Add a carousel example that Tutu likes for style reference."""
        examples = self.memory.get("carousel_examples", [])
        examples.append({
            "description": description,
            "notes": notes,
            "url": url,
            "added": datetime.utcnow().isoformat(),
        })
        self.memory.set("carousel_examples", examples[-20:])
        return {"success": True, "message": f"Example added: {description}"}

    def submit_feedback(self, draft_id: str, feedback: str, rating: str) -> dict:
        """Process feedback on a draft."""
        self.memory.add_feedback(draft_id, feedback, rating)

        if rating in ("revised", "rejected") and feedback:
            self.memory.add_style_note(f"Carousel feedback: {feedback[:200]}")

        # Check if we should upgrade delegation level
        recent = self.memory.get_recent_feedback(20)
        approved_count = sum(1 for f in recent if f["rating"] == "approved")
        if approved_count >= 15 and self.memory.get("delegation_level", 1) < 4:
            current_level = self.memory.get("delegation_level", 1)
            self.memory.set("delegation_level", min(current_level + 1, 4))
            return {
                "success": True,
                "message": f"Feedback recorded. Delegation level upgraded to {current_level + 1}/4!",
                "delegation_level": current_level + 1,
            }

        return {"success": True, "message": f"Feedback recorded for {draft_id}"}

    def set_delegation_level(self, level: int) -> dict:
        """Manually set delegation level (1-4)."""
        level = max(1, min(4, level))
        self.memory.set("delegation_level", level)
        labels = {1: "Draft for review", 2: "Draft with suggestions", 3: "Ready to post (light review)", 4: "Full autonomy"}
        return {"success": True, "level": level, "description": labels[level]}


# ---------------------------------------------------------------------------
# Sub-Agent Manager (Orchestrator)
# ---------------------------------------------------------------------------

class SubAgentManager:
    """
    Central manager that Imani uses to dispatch to and coordinate sub-agents.
    """

    def __init__(self, metricool_client=None):
        self.repurposer = ContentRepurposer()
        self.analytics = AnalyticsDigest(metricool_client=metricool_client)
        self.creator = ContentCreator()

        self._agents = {
            "content-repurposer": self.repurposer,
            "analytics-digest": self.analytics,
            "content-creator": self.creator,
        }

    def list_agents(self) -> list:
        """Return status of all sub-agents."""
        return [agent.status() for agent in self._agents.values()]

    def get_agent(self, agent_id: str):
        return self._agents.get(agent_id)

    async def dispatch(self, agent_id: str, action: str, params: dict) -> dict:
        """
        Dispatch a task to a sub-agent.

        Args:
            agent_id: The sub-agent to dispatch to
            action: The action to perform
            params: Parameters for the action

        Returns:
            Result from the sub-agent
        """
        agent = self._agents.get(agent_id)
        if not agent:
            return {"success": False, "error": f"Unknown sub-agent: {agent_id}"}

        # Content Repurposer actions
        if agent_id == "content-repurposer":
            if action == "repurpose":
                return await self.repurposer.repurpose(**params)
            elif action == "feedback":
                return self.repurposer.submit_feedback(**params)

        # Analytics Digest actions
        elif agent_id == "analytics-digest":
            if action == "generate":
                return await self.analytics.generate_digest(**params)
            elif action == "add_account":
                return self.analytics.add_account(**params)
            elif action == "remove_account":
                return self.analytics.remove_account(**params)
            elif action == "list_accounts":
                return {"success": True, "accounts": self.analytics.list_accounts()}

        # Content Creator actions
        elif agent_id == "content-creator":
            if action == "create_carousel":
                return await self.creator.create_carousel(**params)
            elif action == "add_example":
                return self.creator.add_example(**params)
            elif action == "feedback":
                return self.creator.submit_feedback(**params)
            elif action == "set_delegation_level":
                return self.creator.set_delegation_level(**params)

        return {"success": False, "error": f"Unknown action '{action}' for {agent_id}"}
