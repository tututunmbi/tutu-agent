"""
Tutu's Strategic AI Advisor — API Agent
Deployed on Railway, connected via WhatsApp (Twilio)

Dashboard V3 — Imani: dark theme, per-platform content pages, LIVE analytics via Metricool
"""
import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from twilio.twiml.messaging_response import MessagingResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

from agent import TutuAdvisor
from memory import ConversationMemory
from sheets import SheetsManager, CALENDAR_SHEET_ID, TRACKER_SHEET_ID
from calendar_tool import CalendarManager
from gmail import GmailManager
from metricool import MetricoolClient
from subagents import SubAgentManager
from scheduler import setup_schedules

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
memory = ConversationMemory()
sheets = SheetsManager()
calendar = CalendarManager()
gmail = GmailManager()
metricool = MetricoolClient()
subagent_mgr = SubAgentManager(metricool_client=metricool)
advisor = TutuAdvisor(memory=memory, sheets=sheets, calendar=calendar, gmail=gmail, subagent_mgr=subagent_mgr)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    setup_schedules(scheduler, advisor, memory, gmail=gmail)
    scheduler.start()
    logger.info("Imani is online. Calendar: %s | Sheets: %s | Gmail: %s | Metricool: %s",
                "connected" if calendar.is_connected() else "not configured",
                "connected" if sheets.is_connected() else "not configured",
                "connected" if gmail.is_connected() else "not configured",
                "connected" if metricool.is_connected() else "not configured")
    yield
    scheduler.shutdown()
    await metricool.close()
    logger.info("Imani is shutting down.")


app = FastAPI(title="Imani — Tutu's Operator", lifespan=lifespan)


# ============================================================
# Dashboard V2 HTML (dark theme, per-platform, analytics)
# ============================================================

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Imani — Strategic Advisor</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/11.1.1/marked.min.js"></script>

  <style>
    :root {
      --bg-deep: #0C0C0F;
      --bg-base: #111114;
      --bg-surface: #18181C;
      --bg-elevated: #1F1F24;
      --bg-hover: #26262C;
      --border: #2A2A32;
      --border-subtle: #1F1F26;
      --text-primary: #E8E4DF;
      --text-secondary: #8A8590;
      --text-muted: #5A5560;
      --accent: #C75B3A;
      --accent-hover: #D4673F;
      --accent-subtle: rgba(199, 91, 58, 0.12);
      --accent-glow: rgba(199, 91, 58, 0.06);
      --glass: rgba(199, 91, 58, 0.08);
      --instagram: #E1306C;
      --instagram-bg: rgba(225, 48, 108, 0.12);
      --twitter: #1DA1F2;
      --twitter-bg: rgba(29, 161, 242, 0.12);
      --tiktok: #FE2C55;
      --tiktok-bg: rgba(254, 44, 85, 0.12);
      --linkedin: #0A66C2;
      --linkedin-bg: rgba(10, 102, 194, 0.12);
      --youtube: #FF0000;
      --youtube-bg: rgba(255, 0, 0, 0.12);
      --success: #34D399;
      --warning: #FBBF24;
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --radius-full: 9999px;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; width: 100%; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg-deep);
      color: var(--text-primary);
      line-height: 1.6;
      overflow: hidden;
    }

    .app { display: flex; height: 100vh; }

    /* ===== SIDEBAR ===== */
    .sidebar {
      width: 260px;
      background: var(--bg-base);
      border-right: 1px solid var(--border-subtle);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }

    .sidebar-brand {
      padding: 24px 20px 20px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .imani-avatar {
      width: 40px; height: 40px;
      border-radius: 12px;
      position: relative; overflow: hidden; flex-shrink: 0;
    }
    .imani-avatar svg { width: 100%; height: 100%; }

    .brand-text { display: flex; flex-direction: column; gap: 2px; }
    .brand-name {
      font-family: 'Crimson Text', Georgia, serif;
      font-size: 22px; font-weight: 600;
      color: var(--text-primary);
      letter-spacing: -0.3px; line-height: 1;
    }
    .brand-role {
      font-size: 11px; font-weight: 500;
      color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 0.8px;
    }

    .sidebar-nav {
      flex: 1; padding: 12px 0;
      overflow-y: auto;
      display: flex; flex-direction: column; gap: 2px;
    }

    .nav-divider { height: 1px; background: var(--border-subtle); margin: 8px 16px; }
    .nav-label {
      font-size: 10px; font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 1px;
      padding: 12px 20px 6px;
    }

    .nav-item {
      margin: 0 8px; padding: 10px 12px;
      cursor: pointer; color: var(--text-secondary);
      font-size: 13px; font-weight: 500;
      display: flex; align-items: center; gap: 12px;
      border-radius: var(--radius-sm);
      transition: all 0.15s ease; user-select: none;
    }
    .nav-item:hover { color: var(--text-primary); background: var(--bg-hover); }
    .nav-item.active { color: var(--accent); background: var(--accent-subtle); }

    .nav-icon {
      width: 20px; height: 20px;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .nav-icon svg {
      width: 18px; height: 18px;
      stroke: currentColor; fill: none;
      stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round;
    }

    .platform-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

    .sidebar-footer {
      padding: 16px 20px;
      border-top: 1px solid var(--border-subtle);
      display: flex; align-items: center; gap: 12px;
    }

    .tools-status {
      display: flex; gap: 6px; flex-wrap: wrap;
      padding: 0 20px 12px;
    }
    .tool-dot {
      font-size: 10px; padding: 2px 8px;
      border-radius: var(--radius-full);
      font-weight: 500;
    }
    .tool-dot.on { background: rgba(52,211,153,0.12); color: var(--success); border: 1px solid rgba(52,211,153,0.3); }
    .tool-dot.off { background: var(--bg-elevated); color: var(--text-muted); border: 1px solid var(--border); }

    .user-avatar {
      width: 32px; height: 32px; border-radius: 50%;
      background: var(--bg-elevated);
      display: flex; align-items: center; justify-content: center;
      font-size: 13px; font-weight: 600;
      color: var(--text-secondary); flex-shrink: 0;
    }
    .user-info { display: flex; flex-direction: column; gap: 1px; flex: 1; min-width: 0; }
    .user-name { font-size: 13px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .user-role-text { font-size: 11px; color: var(--text-muted); }

    /* ===== MAIN AREA ===== */
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg-deep); }
    .panel { display: none; flex: 1; flex-direction: column; overflow: hidden; }
    .panel.active { display: flex; }

    /* ===== SHARED PAGE HEADER ===== */
    .page-header {
      padding: 28px 40px 20px;
      border-bottom: 1px solid var(--border-subtle);
      background: var(--bg-base);
    }
    .page-header-row { display: flex; justify-content: space-between; align-items: center; }
    .page-title {
      font-family: 'Crimson Text', Georgia, serif;
      font-size: 28px; font-weight: 600; color: var(--text-primary);
    }
    .page-subtitle { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }

    .btn {
      padding: 9px 18px; border-radius: var(--radius-full);
      font-size: 13px; font-weight: 600;
      cursor: pointer; transition: all 0.15s ease;
      display: inline-flex; align-items: center; gap: 8px; border: none;
    }
    .btn-accent { background: var(--accent); color: #fff; }
    .btn-accent:hover { background: var(--accent-hover); }
    .btn-ghost { background: var(--bg-elevated); color: var(--text-secondary); border: 1px solid var(--border); }
    .btn-ghost:hover { background: var(--bg-hover); color: var(--text-primary); }

    /* ===== CHAT PAGE ===== */
    .chat-page { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
    .chat-messages {
      flex: 1; overflow-y: auto; padding: 32px 40px;
      display: flex; flex-direction: column; gap: 20px; scroll-behavior: smooth;
    }
    .chat-empty {
      flex: 1; display: flex; flex-direction: column;
      align-items: center; justify-content: center; gap: 16px;
    }
    .chat-empty-avatar { margin-bottom: 8px; }
    .chat-greeting {
      font-family: 'Crimson Text', Georgia, serif;
      font-size: 42px; font-weight: 600;
      color: var(--text-primary); text-align: center; line-height: 1.15;
    }
    .chat-greeting-accent { color: var(--accent); }
    .chat-hint { font-size: 14px; color: var(--text-muted); text-align: center; max-width: 400px; }

    .msg { display: flex; gap: 12px; align-items: flex-start; }
    .msg-user { justify-content: flex-end; }
    .msg-avatar {
      width: 28px; height: 28px; border-radius: 8px; overflow: hidden;
      flex-shrink: 0; display: flex; align-items: center; justify-content: center;
      background: var(--bg-elevated);
    }
    .msg-avatar svg { width: 100%; height: 100%; }
    .msg-bubble { max-width: 560px; word-wrap: break-word; }
    .msg-user .msg-bubble {
      background: var(--accent-subtle); border: 1px solid rgba(199,91,58,0.2);
      color: var(--text-primary); padding: 12px 16px;
      border-radius: 18px 18px 4px 18px; font-size: 14px; line-height: 1.5;
    }
    .msg-ai .msg-bubble { color: var(--text-primary); font-size: 14px; line-height: 1.65; }
    .msg-ai .msg-bubble p { margin-bottom: 8px; }
    .msg-ai .msg-bubble p:last-child { margin-bottom: 0; }
    .msg-ai .msg-bubble strong { color: var(--accent); font-weight: 600; }
    .msg-ai .msg-bubble ul, .msg-ai .msg-bubble ol { margin: 8px 0; padding-left: 20px; }
    .msg-ai .msg-bubble li { margin-bottom: 4px; }

    .typing-indicator {
      display: flex; gap: 12px; align-items: flex-start;
    }
    .typing-dots {
      display: flex; gap: 4px; padding: 14px 16px;
      background: var(--bg-surface); border-radius: 18px;
    }
    .typing-dots span {
      width: 6px; height: 6px; background: var(--accent);
      border-radius: 50%; opacity: 0.3;
      animation: typePulse 1.2s infinite;
    }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typePulse { 0%,100% { opacity: 0.3; } 50% { opacity: 1; } }

    .chat-input-bar {
      padding: 20px 40px 28px; display: flex; justify-content: center;
      background: linear-gradient(to top, var(--bg-deep) 60%, transparent);
    }
    .chat-input-wrap { width: 100%; max-width: 640px; display: flex; gap: 10px; align-items: flex-end; }
    .chat-input {
      flex: 1; padding: 14px 18px;
      background: var(--bg-surface); border: 1px solid var(--border);
      border-radius: 24px; font-family: 'Inter', sans-serif;
      font-size: 14px; color: var(--text-primary);
      outline: none; resize: none; min-height: 48px; max-height: 120px;
      transition: border-color 0.2s;
    }
    .chat-input::placeholder { color: var(--text-muted); }
    .chat-input:focus { border-color: var(--accent); }
    .chat-send {
      width: 48px; height: 48px; background: var(--accent);
      border: none; border-radius: 50%; cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: background 0.15s;
    }
    .chat-send:hover { background: var(--accent-hover); }
    .chat-send svg { width: 20px; height: 20px; stroke: #fff; fill: none; stroke-width: 2; }

    /* ===== PLATFORM PAGES ===== */
    .platform-page { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
    .platform-body { flex: 1; overflow-y: auto; padding: 24px 40px 40px; }
    .platform-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 28px; }
    .mini-stat {
      background: var(--bg-surface); border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md); padding: 16px 18px;
    }
    .mini-stat-label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
    .mini-stat-value { font-size: 22px; font-weight: 700; }
    .mini-stat-change { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
    .mini-stat-change.up { color: var(--success); }

    .content-section-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 14px; }
    .content-list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 32px; }
    .content-row {
      background: var(--bg-surface); border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md); padding: 16px 20px;
      display: flex; align-items: center; gap: 16px;
      transition: border-color 0.15s; cursor: default;
    }
    .content-row:hover { border-color: var(--border); }
    .content-status { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
    .status-scheduled { background: var(--warning); }
    .status-published { background: var(--success); }
    .status-draft { background: var(--text-muted); }
    .content-info { flex: 1; min-width: 0; }
    .content-title { font-size: 14px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .content-meta { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
    .content-engagement { text-align: right; min-width: 80px; }
    .content-eng-value { font-size: 14px; font-weight: 600; color: var(--text-primary); }
    .content-eng-label { font-size: 11px; color: var(--text-muted); }
    .content-actions { display: flex; gap: 6px; }
    .content-action-btn {
      width: 32px; height: 32px; border-radius: 8px; border: none;
      background: var(--bg-elevated); color: var(--text-muted);
      cursor: pointer; display: flex; align-items: center; justify-content: center;
      transition: all 0.15s;
    }
    .content-action-btn:hover { background: var(--bg-hover); color: var(--text-primary); }
    .content-action-btn svg { width: 14px; height: 14px; stroke: currentColor; fill: none; stroke-width: 2; }

    /* ===== ANALYTICS PAGE ===== */
    .analytics-page { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
    .analytics-body { flex: 1; overflow-y: auto; padding: 24px 40px 40px; }
    .analytics-tabs { display: flex; gap: 4px; margin-bottom: 28px; }
    .analytics-tab {
      padding: 8px 16px; border-radius: var(--radius-full);
      font-size: 13px; font-weight: 500;
      color: var(--text-secondary); background: transparent; border: none;
      cursor: pointer; transition: all 0.15s;
    }
    .analytics-tab:hover { background: var(--bg-hover); color: var(--text-primary); }
    .analytics-tab.active { background: var(--accent-subtle); color: var(--accent); }

    .analytics-overview { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 28px; }
    .stat-card {
      background: var(--bg-surface); border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md); padding: 20px;
    }
    .stat-label { font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
    .stat-value { font-size: 28px; font-weight: 700; color: var(--accent); }
    .stat-change { font-size: 12px; color: var(--text-muted); margin-top: 6px; }
    .stat-change.up { color: var(--success); }

    .chart-card {
      background: var(--bg-surface); border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md); padding: 24px; margin-bottom: 16px;
    }
    .chart-card-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 16px; }
    .chart-area { position: relative; height: 280px; }
    .charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

    /* ===== AGENTS PAGE ===== */
    .agents-page { display: flex; flex-direction: column; flex: 1; overflow: hidden; }
    .agents-body { flex: 1; overflow-y: auto; padding: 24px 40px 40px; }
    .agents-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
    .agent-card {
      background: var(--bg-surface); border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md); padding: 24px;
      display: flex; flex-direction: column; gap: 12px; transition: all 0.15s;
    }
    .agent-card:hover { border-color: var(--border); }
    .agent-card-head { display: flex; align-items: center; gap: 14px; }
    .agent-icon {
      width: 40px; height: 40px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center; font-size: 18px;
    }
    .agent-name { font-size: 15px; font-weight: 600; color: var(--text-primary); }
    .agent-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
    .agent-badge {
      display: inline-flex; padding: 4px 10px;
      background: var(--bg-elevated); color: var(--text-muted);
      border-radius: var(--radius-full); font-size: 11px; font-weight: 600;
      text-transform: uppercase; letter-spacing: 0.3px; align-self: flex-start;
    }
    .agent-badge.active {
      background: rgba(52, 211, 153, 0.15); color: var(--success);
    }
    .agent-card.agent-active {
      border-color: rgba(52, 211, 153, 0.3);
    }
    .agent-card.agent-active:hover {
      border-color: rgba(52, 211, 153, 0.5);
    }
    .agent-status-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: var(--text-muted); margin-left: auto;
    }
    .agent-status-dot.active {
      background: var(--success);
      box-shadow: 0 0 8px rgba(52, 211, 153, 0.4);
    }
    .agent-stats {
      display: flex; gap: 12px; flex-wrap: wrap;
    }
    .agent-stat {
      font-size: 12px; color: var(--text-secondary);
    }
    .agent-stat strong {
      color: var(--text-primary);
    }
    .agent-actions {
      display: flex; gap: 8px; margin-top: 4px;
    }
    .btn-sm {
      padding: 6px 14px; font-size: 12px;
    }
    .btn-ghost {
      background: transparent; color: var(--text-secondary);
      border: 1px solid var(--border); border-radius: var(--radius-sm);
      cursor: pointer; font-size: 13px; font-weight: 500;
      padding: 8px 16px; transition: all 0.15s ease;
    }
    .btn-ghost:hover { color: var(--text-primary); border-color: var(--text-muted); }

    /* Sub-agent result display */
    .sa-result { background: var(--bg-elevated); border-radius: var(--radius-md); padding: 16px; margin-top: 12px; }
    .sa-result h4 { color: var(--text-primary); font-size: 14px; margin-bottom: 8px; }
    .sa-result pre { font-size: 12px; color: var(--text-secondary); white-space: pre-wrap; word-break: break-word; line-height: 1.6; max-height: 400px; overflow-y: auto; }
    .sa-slide { background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px; margin-bottom: 8px; }
    .sa-slide-num { font-size: 11px; font-weight: 600; color: var(--accent); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
    .sa-slide-headline { font-size: 15px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
    .sa-slide-body { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
    .sa-slide-visual { font-size: 12px; color: var(--text-muted); font-style: italic; margin-top: 4px; }

    .tracked-account {
      display: flex; align-items: center; gap: 10px; padding: 8px 12px;
      background: var(--bg-elevated); border-radius: var(--radius-sm); margin-bottom: 6px;
    }
    .tracked-account .ta-handle { flex: 1; font-size: 13px; color: var(--text-primary); font-weight: 500; }
    .tracked-account .ta-platform { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; }
    .tracked-account .ta-category { font-size: 11px; padding: 2px 8px; border-radius: var(--radius-full); background: var(--accent-subtle); color: var(--accent); }
    .tracked-account .ta-remove { cursor: pointer; color: var(--text-muted); font-size: 16px; }
    .tracked-account .ta-remove:hover { color: #ef4444; }

    /* ===== MODAL ===== */
    .modal-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.5); backdrop-filter: blur(4px);
      z-index: 500; align-items: center; justify-content: center;
    }
    .modal-overlay.active { display: flex; }
    .modal-box {
      background: var(--bg-surface); border: 1px solid var(--border);
      border-radius: var(--radius-lg); padding: 28px;
      width: 440px; max-width: 90vw;
      box-shadow: 0 24px 80px rgba(0,0,0,0.4);
    }
    .modal-title {
      font-family: 'Crimson Text', Georgia, serif;
      font-size: 22px; font-weight: 600;
      color: var(--text-primary); margin-bottom: 20px;
    }
    .field { margin-bottom: 14px; display: flex; flex-direction: column; gap: 5px; }
    .field-label { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
    .field-input {
      padding: 10px 12px; background: var(--bg-elevated);
      border: 1px solid var(--border); border-radius: var(--radius-sm);
      font-family: 'Inter', sans-serif; font-size: 14px; color: var(--text-primary);
      outline: none; transition: border-color 0.15s;
    }
    .field-input:focus { border-color: var(--accent); }
    .field-input::placeholder { color: var(--text-muted); }
    .modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px; }

    /* ===== DAILY PLANNER ===== */
    .planner-page { display:flex; flex-direction:column; height:100%; }
    .planner-header { padding:32px 40px 0; }
    .planner-date-nav { display:flex; align-items:center; gap:16px; margin-top:12px; }
    .planner-date-nav button { background:var(--bg-elevated); border:1px solid var(--border); color:var(--text-secondary); border-radius:8px; padding:6px 12px; cursor:pointer; font-size:13px; transition:all 0.2s; }
    .planner-date-nav button:hover { color:var(--text-primary); border-color:var(--accent); }
    .planner-date-nav .planner-date-label { font-family:'Crimson Text',serif; font-size:22px; color:var(--text-primary); min-width:180px; text-align:center; }
    .planner-body { flex:1; overflow-y:auto; padding:20px 40px 40px; }
    .planner-columns { display:grid; grid-template-columns:1fr 340px; gap:24px; }
    .planner-schedule { background:var(--bg-surface); border:1px solid var(--border); border-radius:12px; overflow:hidden; }
    .planner-schedule-header { padding:14px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; }
    .planner-schedule-title { font-size:14px; font-weight:600; color:var(--text-primary); display:flex; align-items:center; gap:8px; }
    .planner-time-grid { }
    .planner-slot { display:grid; grid-template-columns:72px 1fr; border-bottom:1px solid var(--border-subtle); min-height:44px; transition:background 0.15s; border-left:3px solid transparent; }
    .planner-slot:last-child { border-bottom:none; }
    .planner-slot:hover { background:var(--bg-hover); }
    .planner-slot[data-category="stamfordham"] { border-left-color:#E74C3C; }
    .planner-slot[data-category="bddm"] { border-left-color:#3498DB; }
    .planner-slot[data-category="spiritual"] { border-left-color:#ECF0F1; }
    .planner-slot[data-category="impact"] { border-left-color:#27AE60; }
    .planner-slot[data-category="brand"] { border-left-color:#2ECC71; }
    .planner-slot[data-category="financial"] { border-left-color:#E91E63; }
    .planner-slot[data-category="health"] { border-left-color:#FFC107; }
    .planner-slot[data-category="career"] { border-left-color:#5DADE2; }
    .planner-slot[data-category="proficio"] { border-left-color:#F0B27A; }
    .planner-cat-select { background:var(--bg-card); border:1px solid var(--border-subtle); color:var(--text-muted); font-size:10px; border-radius:4px; padding:2px 4px; cursor:pointer; display:none; max-width:90px; }
    .planner-slot.has-task .planner-cat-select { display:inline-block; }
    .planner-slot-time { padding:10px 16px; font-size:12px; font-weight:500; color:var(--text-muted); font-variant-numeric:tabular-nums; display:flex; align-items:flex-start; padding-top:12px; }
    .planner-slot-content { padding:8px 16px 8px 0; display:flex; align-items:center; gap:8px; min-height:28px; }
    .planner-slot-task { font-size:13px; color:var(--text-primary); flex:1; }
    .planner-slot-task.empty { color:var(--text-muted); font-style:italic; font-size:12px; }
    .planner-slot-category { width:4px; height:24px; border-radius:2px; flex-shrink:0; }
    .planner-slot-input { background:transparent; border:none; color:var(--text-primary); font-size:13px; flex:1; padding:4px 0; outline:none; font-family:inherit; }
    .planner-slot-input::placeholder { color:var(--text-muted); font-style:italic; }
    .planner-slot-input:focus { border-bottom:1px solid var(--accent); }
    .planner-slot-remove { background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:14px; padding:2px 6px; border-radius:4px; opacity:0; transition:opacity 0.15s; }
    .planner-slot:hover .planner-slot-remove { opacity:1; }
    .planner-slot-remove:hover { color:var(--accent); background:var(--accent-subtle); }
    .planner-sidebar { display:flex; flex-direction:column; gap:16px; }
    .planner-card { background:var(--bg-surface); border:1px solid var(--border); border-radius:12px; overflow:hidden; }
    .planner-card-header { padding:14px 20px; border-bottom:1px solid var(--border); font-size:14px; font-weight:600; color:var(--text-primary); display:flex; align-items:center; gap:8px; }
    .planner-card-body { padding:16px 20px; }
    .priority-item { display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid var(--border-subtle); }
    .priority-item:last-child { border-bottom:none; }
    .priority-item .pri-edit-label { background:transparent; border:none; color:var(--text-muted); font-size:11px; font-weight:600; width:100%; outline:none; font-family:inherit; }
    .priority-item .pri-edit-label:focus { border-bottom:1px solid var(--accent); }
    .priority-item .pri-edit-value { background:transparent; border:none; color:var(--text-primary); font-size:12px; width:100%; outline:none; font-family:inherit; }
    .priority-item .pri-edit-value:focus { border-bottom:1px solid var(--accent); }
    .priority-item .pri-color-dot { width:12px; height:12px; border-radius:50%; cursor:pointer; flex-shrink:0; border:2px solid transparent; }
    .priority-item .pri-color-dot:hover { border-color:var(--text-primary); }
    .priority-item .pri-remove { background:none; border:none; color:var(--text-muted); cursor:pointer; font-size:12px; padding:2px 4px; opacity:0; transition:opacity 0.15s; }
    .priority-item:hover .pri-remove { opacity:1; }
    .pri-add-btn { background:none; border:1px dashed var(--border-subtle); color:var(--text-muted); font-size:11px; padding:6px 12px; border-radius:6px; cursor:pointer; width:100%; margin-top:8px; }
    .pri-add-btn:hover { border-color:var(--accent); color:var(--accent); }
    .priority-color { width:4px; height:28px; border-radius:2px; flex-shrink:0; }
    .priority-label { font-size:12px; color:var(--text-secondary); flex:1; }
    .priority-task { font-size:13px; color:var(--text-primary); }
    .task-item { display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid var(--border-subtle); }
    .task-item:last-child { border-bottom:none; }
    .task-check { width:18px; height:18px; border-radius:4px; border:2px solid var(--border); background:transparent; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; flex-shrink:0; }
    .task-check.checked { background:var(--accent); border-color:var(--accent); }
    .task-check.checked::after { content:'\2713'; color:white; font-size:11px; }
    .task-text { font-size:13px; color:var(--text-primary); flex:1; }
    .task-text.done { text-decoration:line-through; color:var(--text-muted); }
    .add-task-row { display:flex; gap:8px; margin-top:8px; }
    .add-task-input { flex:1; background:var(--bg-elevated); border:1px solid var(--border); border-radius:6px; padding:6px 10px; color:var(--text-primary); font-size:12px; font-family:inherit; outline:none; }
    .add-task-input:focus { border-color:var(--accent); }
    .add-task-btn { background:var(--accent); border:none; color:white; border-radius:6px; padding:6px 12px; font-size:12px; cursor:pointer; }

        /* ===== ROUTINES ===== */
    .routines-page { display:flex; flex-direction:column; height:100%; }
    .routines-header { padding:32px 40px 0; }
    .routines-body { flex:1; overflow-y:auto; padding:20px 40px 40px; }
    .routines-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:24px; }
    .routine-card { background:var(--bg-surface); border:1px solid var(--border); border-radius:16px; overflow:hidden; }
    .routine-card-top { padding:20px 24px 16px; display:flex; align-items:center; gap:12px; border-bottom:1px solid var(--border); }
    .routine-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; }
    .routine-icon.morning { background:rgba(251,191,36,0.12); color:#FBB724; }
    .routine-icon.afternoon { background:rgba(251,146,60,0.12); color:#FB923C; }
    .routine-icon.night { background:rgba(129,140,248,0.12); color:#818CF8; }
    .routine-title { font-size:16px; font-weight:600; color:var(--text-primary); }
    .routine-subtitle { font-size:12px; color:var(--text-muted); }
    .routine-items { padding:16px 24px 20px; }
    .routine-item { display:flex; align-items:center; gap:12px; padding:10px 0; border-bottom:1px solid var(--border-subtle); }
    .routine-item:last-child { border-bottom:none; }
    .routine-check { width:22px; height:22px; border-radius:6px; border:2px solid var(--border); background:transparent; cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.25s; flex-shrink:0; }
    .routine-check.checked { border-color:var(--accent); background:var(--accent); }
    .routine-check.checked::after { content:'\2713'; color:white; font-size:13px; font-weight:700; }
    .routine-check-label { font-size:14px; color:var(--text-primary); flex:1; }
    .routine-check-label.done { color:var(--text-muted); text-decoration:line-through; }
    .routine-progress { padding:0 24px 20px; }
    .routine-progress-bar { height:6px; background:var(--bg-elevated); border-radius:3px; overflow:hidden; }
    .routine-progress-fill { height:100%; border-radius:3px; transition:width 0.4s ease; }
    .routine-progress-fill.morning { background:linear-gradient(90deg, #FBB724, #F59E0B); }
    .routine-progress-fill.afternoon { background:linear-gradient(90deg, #FB923C, #F97316); }
    .routine-progress-fill.night { background:linear-gradient(90deg, #818CF8, #6366F1); }
    .routine-progress-text { font-size:11px; color:var(--text-muted); margin-top:6px; text-align:right; }
    .routine-add-row { display:flex; gap:8px; margin-top:8px; padding:0 24px 16px; }
    .routine-add-input { flex:1; background:var(--bg-elevated); border:1px solid var(--border); border-radius:6px; padding:8px 12px; color:var(--text-primary); font-size:13px; font-family:inherit; outline:none; }
    .routine-add-input:focus { border-color:var(--accent); }
    .routine-add-btn { background:var(--accent); border:none; color:white; border-radius:6px; padding:8px 14px; font-size:13px; cursor:pointer; font-weight:500; }
    .routines-streak { margin-top:24px; background:var(--bg-surface); border:1px solid var(--border); border-radius:16px; padding:24px; }
    .streak-title { font-size:14px; font-weight:600; color:var(--text-primary); margin-bottom:12px; }
    .streak-row { display:flex; gap:4px; flex-wrap:wrap; }
    .streak-dot { width:14px; height:14px; border-radius:3px; background:var(--bg-elevated); }
    .streak-dot.done { background:var(--accent); }
    .streak-dot.partial { background:rgba(199, 91, 58, 0.4); }

        /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 900px) {
      .sidebar { width: 220px; }
      .platform-stats, .analytics-overview { grid-template-columns: repeat(2, 1fr); }
      .charts-row { grid-template-columns: 1fr; }
      .planner-columns { grid-template-columns: 1fr; }
      .routines-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 640px) {
      .sidebar { position: absolute; left: 0; top: 0; height: 100%; z-index: 200; box-shadow: 0 0 40px rgba(0,0,0,0.5); }
      .chat-messages, .chat-input-bar, .platform-body, .analytics-body, .agents-body, .planner-body, .routines-body { padding-left: 20px; padding-right: 20px; }
      .platform-stats, .analytics-overview { grid-template-columns: 1fr; }
      .planner-columns { grid-template-columns: 1fr; }
      .routines-grid { grid-template-columns: 1fr; }
    }
  
    .mobile-menu-btn {
      display: none;
      position: fixed;
      top: 12px;
      left: 12px;
      z-index: 1001;
      background: var(--bg-base);
      border: 1px solid var(--border-subtle);
      color: var(--text-primary);
      font-size: 22px;
      width: 40px;
      height: 40px;
      border-radius: 8px;
      cursor: pointer;
      align-items: center;
      justify-content: center;
      line-height: 1;
    }
    .mobile-menu-overlay {
      display: none;
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.5);
      z-index: 999;
    }
    .mobile-menu-overlay.active { display: block; }
    @media (max-width: 768px) {
      .mobile-menu-btn { display: flex; }
      .sidebar {
        position: fixed;
        top: 0; left: 0; bottom: 0;
        z-index: 1000;
        transform: translateX(-100%);
        transition: transform 0.25s ease;
        width: 280px;
      }
      .sidebar.open { transform: translateX(0); }
      .main { width: 100% !important; }
      .chat-messages { padding-top: 60px; }
      .page-content { padding-top: 60px; }
    }
    </style>
</head>
<body>
  <div class="app">

    <!-- ===== SIDEBAR ===== -->
    <div class="sidebar">
      <div class="sidebar-brand">
        <div class="imani-avatar">
          <svg viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="glass-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#C75B3A;stop-opacity:0.6"/>
                <stop offset="50%" style="stop-color:#E88A6D;stop-opacity:0.3"/>
                <stop offset="100%" style="stop-color:#C75B3A;stop-opacity:0.5"/>
              </linearGradient>
              <radialGradient id="face-glow" cx="50%" cy="40%" r="50%">
                <stop offset="0%" style="stop-color:#E88A6D;stop-opacity:0.4"/>
                <stop offset="100%" style="stop-color:#C75B3A;stop-opacity:0.1"/>
              </radialGradient>
            </defs>
            <rect width="40" height="40" rx="12" fill="#1F1F24"/>
            <rect width="40" height="40" rx="12" fill="url(#glass-grad)" opacity="0.5"/>
            <circle cx="20" cy="16" r="8" fill="url(#face-glow)" stroke="#C75B3A" stroke-width="0.5" opacity="0.8"/>
            <ellipse cx="16.5" cy="14.5" rx="1.5" ry="1.8" fill="#C75B3A" opacity="0.7"/>
            <ellipse cx="23.5" cy="14.5" rx="1.5" ry="1.8" fill="#C75B3A" opacity="0.7"/>
            <path d="M17 19 Q20 21.5 23 19" stroke="#C75B3A" stroke-width="0.8" fill="none" opacity="0.5" stroke-linecap="round"/>
            <path d="M13 28 Q20 34 27 28" fill="#C75B3A" opacity="0.15"/>
            <line x1="20" y1="24" x2="20" y2="28" stroke="#C75B3A" stroke-width="0.5" opacity="0.3"/>
            <rect x="2" y="2" width="36" height="36" rx="11" fill="none" stroke="#C75B3A" stroke-width="0.3" opacity="0.3"/>
          </svg>
        </div>
        <div class="brand-text">
          <div class="brand-name">Imani</div>
          <div class="brand-role">Strategic Advisor</div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-item active" data-panel="chat">
          <div class="nav-icon"><svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></div>
          <span>Chat</span>
        </div>

        <div class="nav-divider"></div>
        <div class="nav-label">Platforms</div>

        <div class="nav-item" data-panel="instagram">
          <div class="platform-dot" style="background:var(--instagram)"></div>
          <span>Instagram</span>
        </div>
        <div class="nav-item" data-panel="twitter">
          <div class="platform-dot" style="background:var(--twitter)"></div>
          <span>Twitter / X</span>
        </div>
        <div class="nav-item" data-panel="tiktok">
          <div class="platform-dot" style="background:var(--tiktok)"></div>
          <span>TikTok</span>
        </div>
        <div class="nav-item" data-panel="youtube">
          <div class="platform-dot" style="background:var(--youtube)"></div>
          <span>YouTube</span>
        </div>
        <div class="nav-item" data-panel="linkedin">
          <div class="platform-dot" style="background:var(--linkedin)"></div>
          <span>LinkedIn</span>
        </div>

        <div class="nav-divider"></div>

        <div class="nav-item" data-panel="analytics">
          <div class="nav-icon"><svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>
          <span>Analytics</span>
        </div>
        <div class="nav-item" data-panel="agents">
          <div class="nav-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg></div>
          <span>Sub-Agents</span>
        </div>

        <div class="nav-divider"></div>
        <div class="nav-label">My Day</div>

        <div class="nav-item" data-panel="planner">
          <div class="nav-icon"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div>
          <span>Daily Planner</span>
        </div>
        <div class="nav-item" data-panel="routines">
          <div class="nav-icon"><svg viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
          <span>Routines</span>
        </div>
      </nav>

      <div id="tools-status" class="tools-status"></div>

      <div class="sidebar-footer">
        <div class="user-avatar">T</div>
        <div class="user-info">
          <div class="user-name">Tutu Adetunmbi</div>
          <div class="user-role-text">Operator</div>
        </div>
      </div>
    </div>

    <!-- ===== MAIN CONTENT ===== -->
    <div class="main">

      <!-- CHAT -->
      <div class="panel active" id="panel-chat">
        <div class="chat-page">
          <div class="chat-messages" id="chat-messages">
            <div class="chat-empty" id="chat-empty">
              <div class="chat-empty-avatar">
                <svg width="64" height="64" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                  <rect width="40" height="40" rx="12" fill="#1F1F24"/>
                  <rect width="40" height="40" rx="12" fill="url(#glass-grad)" opacity="0.5"/>
                  <circle cx="20" cy="16" r="8" fill="url(#face-glow)" stroke="#C75B3A" stroke-width="0.5" opacity="0.8"/>
                  <ellipse cx="16.5" cy="14.5" rx="1.5" ry="1.8" fill="#C75B3A" opacity="0.7"/>
                  <ellipse cx="23.5" cy="14.5" rx="1.5" ry="1.8" fill="#C75B3A" opacity="0.7"/>
                  <path d="M17 19 Q20 21.5 23 19" stroke="#C75B3A" stroke-width="0.8" fill="none" opacity="0.5" stroke-linecap="round"/>
                  <path d="M13 28 Q20 34 27 28" fill="#C75B3A" opacity="0.15"/>
                  <line x1="20" y1="24" x2="20" y2="28" stroke="#C75B3A" stroke-width="0.5" opacity="0.3"/>
                </svg>
              </div>
              <div class="chat-greeting">
                Good <span class="chat-greeting-accent" id="tod">morning</span>,<br>Tutu
              </div>
              <div class="chat-hint">I'm here to help you think through strategy, content, and what's next. What's on your mind?</div>
            </div>
          </div>
          <div class="chat-input-bar">
            <div class="chat-input-wrap">
              <input type="text" class="chat-input" id="chat-input" placeholder="Ask Imani anything..." autocomplete="off">
              <button class="chat-send" id="chat-send">
                <svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- INSTAGRAM -->
      <div class="panel" id="panel-instagram">
        <div class="platform-page">
          <div class="page-header">
            <div class="page-header-row">
              <div>
                <div class="page-title" style="display:flex;align-items:center;gap:12px;">
                  <span class="platform-dot" style="background:var(--instagram);width:10px;height:10px;"></span> Instagram
                </div>
                <div class="page-subtitle">Manage your Instagram content and track performance</div>
              </div>
              <button class="btn btn-accent" onclick="openModal('instagram')">+ New Post</button>
            </div>
          </div>
          <div class="platform-body">
            <div class="platform-stats">
              <div class="mini-stat"><div class="mini-stat-label">Followers</div><div class="mini-stat-value" id="ig-followers" style="color:var(--instagram)">—</div><div class="mini-stat-change" id="ig-followers-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Engagement</div><div class="mini-stat-value" id="ig-engagement" style="color:var(--instagram)">—</div><div class="mini-stat-change" id="ig-engagement-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Reach</div><div class="mini-stat-value" id="ig-reach" style="color:var(--instagram)">—</div><div class="mini-stat-change" id="ig-reach-note">Last 30 days</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Posts This Month</div><div class="mini-stat-value" id="ig-posts" style="color:var(--instagram)">—</div><div class="mini-stat-change" id="ig-posts-note">Loading...</div></div>
            </div>
            <div class="content-section-title">Recent & Scheduled</div>
            <div class="content-list" id="ig-content"></div>
          </div>
        </div>
      </div>

      <!-- TWITTER -->
      <div class="panel" id="panel-twitter">
        <div class="platform-page">
          <div class="page-header">
            <div class="page-header-row">
              <div>
                <div class="page-title" style="display:flex;align-items:center;gap:12px;">
                  <span class="platform-dot" style="background:var(--twitter);width:10px;height:10px;"></span> Twitter / X
                </div>
                <div class="page-subtitle">Manage your Twitter threads, posts, and engagement</div>
              </div>
              <button class="btn btn-accent" onclick="openModal('twitter')">+ New Post</button>
            </div>
          </div>
          <div class="platform-body">
            <div class="platform-stats">
              <div class="mini-stat"><div class="mini-stat-label">Followers</div><div class="mini-stat-value" id="tw-followers" style="color:var(--twitter)">—</div><div class="mini-stat-change" id="tw-followers-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Engagement</div><div class="mini-stat-value" id="tw-engagement" style="color:var(--twitter)">—</div><div class="mini-stat-change" id="tw-engagement-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Impressions</div><div class="mini-stat-value" id="tw-reach" style="color:var(--twitter)">—</div><div class="mini-stat-change" id="tw-reach-note">Last 30 days</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Posts This Month</div><div class="mini-stat-value" id="tw-posts" style="color:var(--twitter)">—</div><div class="mini-stat-change" id="tw-posts-note">Loading...</div></div>
            </div>
            <div class="content-section-title">Recent & Scheduled</div>
            <div class="content-list" id="tw-content"></div>
          </div>
        </div>
      </div>

      <!-- TIKTOK -->
      <div class="panel" id="panel-tiktok">
        <div class="platform-page">
          <div class="page-header">
            <div class="page-header-row">
              <div>
                <div class="page-title" style="display:flex;align-items:center;gap:12px;">
                  <span class="platform-dot" style="background:var(--tiktok);width:10px;height:10px;"></span> TikTok
                </div>
                <div class="page-subtitle">Manage your TikTok videos, drafts, and analytics</div>
              </div>
              <button class="btn btn-accent" onclick="openModal('tiktok')">+ New Video</button>
            </div>
          </div>
          <div class="platform-body">
            <div class="platform-stats">
              <div class="mini-stat"><div class="mini-stat-label">Followers</div><div class="mini-stat-value" id="tt-followers" style="color:var(--tiktok)">—</div><div class="mini-stat-change" id="tt-followers-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Avg Views</div><div class="mini-stat-value" id="tt-views" style="color:var(--tiktok)">—</div><div class="mini-stat-change" id="tt-views-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Engagement</div><div class="mini-stat-value" id="tt-engagement" style="color:var(--tiktok)">—</div><div class="mini-stat-change" id="tt-engagement-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Videos This Month</div><div class="mini-stat-value" id="tt-posts" style="color:var(--tiktok)">—</div><div class="mini-stat-change" id="tt-posts-note">Loading...</div></div>
            </div>
            <div class="content-section-title">Recent & Scheduled</div>
            <div class="content-list" id="tt-content"></div>
          </div>
        </div>
      </div>

      <!-- LINKEDIN -->
      <div class="panel" id="panel-linkedin">
        <div class="platform-page">
          <div class="page-header">
            <div class="page-header-row">
              <div>
                <div class="page-title" style="display:flex;align-items:center;gap:12px;">
                  <span class="platform-dot" style="background:var(--linkedin);width:10px;height:10px;"></span> LinkedIn
                </div>
                <div class="page-subtitle">Manage your LinkedIn articles, posts, and professional presence</div>
              </div>
              <button class="btn btn-accent" onclick="openModal('linkedin')">+ New Post</button>
            </div>
          </div>
          <div class="platform-body">
            <div class="platform-stats">
              <div class="mini-stat"><div class="mini-stat-label">Connections</div><div class="mini-stat-value" id="li-followers" style="color:var(--linkedin)">—</div><div class="mini-stat-change" id="li-followers-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Engagement</div><div class="mini-stat-value" id="li-engagement" style="color:var(--linkedin)">—</div><div class="mini-stat-change" id="li-engagement-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Impressions</div><div class="mini-stat-value" id="li-reach" style="color:var(--linkedin)">—</div><div class="mini-stat-change" id="li-reach-note">Last 30 days</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Posts This Month</div><div class="mini-stat-value" id="li-posts" style="color:var(--linkedin)">—</div><div class="mini-stat-change" id="li-posts-note">Loading...</div></div>
            </div>
            <div class="content-section-title">Recent & Scheduled</div>
            <div class="content-list" id="li-content"></div>
          </div>
        </div>
      </div>

      <!-- YOUTUBE -->
      <div class="panel" id="panel-youtube">
        <div class="platform-page">
          <div class="page-header">
            <div class="page-header-row">
              <div>
                <div class="page-title" style="display:flex;align-items:center;gap:12px;">
                  <span class="platform-dot" style="background:var(--youtube);width:10px;height:10px;"></span> YouTube
                </div>
                <div class="page-subtitle">Manage your YouTube videos, shorts, and channel growth</div>
              </div>
              <button class="btn btn-accent" onclick="openModal('youtube')">+ New Video</button>
            </div>
          </div>
          <div class="platform-body">
            <div class="platform-stats">
              <div class="mini-stat"><div class="mini-stat-label">Subscribers</div><div class="mini-stat-value" id="yt-followers" style="color:var(--youtube)">—</div><div class="mini-stat-change" id="yt-followers-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Engagement</div><div class="mini-stat-value" id="yt-engagement" style="color:var(--youtube)">—</div><div class="mini-stat-change" id="yt-engagement-note">Loading...</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Views</div><div class="mini-stat-value" id="yt-reach" style="color:var(--youtube)">—</div><div class="mini-stat-change" id="yt-reach-note">Last 30 days</div></div>
              <div class="mini-stat"><div class="mini-stat-label">Videos This Month</div><div class="mini-stat-value" id="yt-posts" style="color:var(--youtube)">—</div><div class="mini-stat-change" id="yt-posts-note">Loading...</div></div>
            </div>
            <div class="content-section-title">Recent & Scheduled</div>
            <div class="content-list" id="yt-content"></div>
          </div>
        </div>
      </div>

      <!-- ANALYTICS -->
      <div class="panel" id="panel-analytics">
        <div class="analytics-page">
          <div class="page-header">
            <div class="page-header-row">
              <div>
                <div class="page-title">Analytics</div>
                <div class="page-subtitle">Cross-platform performance at a glance</div>
              </div>
              <div style="display:flex;gap:8px;">
                <button class="btn btn-ghost">Last 7 Days</button>
                <button class="btn btn-ghost">Export</button>
              </div>
            </div>
          </div>
          <div class="analytics-body">
            <div class="analytics-tabs" id="analytics-tabs">
              <button class="analytics-tab active" data-tab="all">All Platforms</button>
              <button class="analytics-tab" data-tab="instagram">Instagram</button>
              <button class="analytics-tab" data-tab="twitter">Twitter / X</button>
              <button class="analytics-tab" data-tab="tiktok">TikTok</button>
              <button class="analytics-tab" data-tab="youtube">YouTube</button>
              <button class="analytics-tab" data-tab="linkedin">LinkedIn</button>
            </div>
            <div class="analytics-overview">
              <div class="stat-card"><div class="stat-label">Total Reach</div><div class="stat-value" id="a-reach">52.1K</div><div class="stat-change up" id="a-reach-c">+12% from last week</div></div>
              <div class="stat-card"><div class="stat-label">Engagement Rate</div><div class="stat-value" id="a-eng">5.1%</div><div class="stat-change up" id="a-eng-c">+0.4% from last week</div></div>
              <div class="stat-card"><div class="stat-label">Total Followers</div><div class="stat-value" id="a-fol">15.6K</div><div class="stat-change up" id="a-fol-c">+1,135 new followers</div></div>
              <div class="stat-card"><div class="stat-label">Content Published</div><div class="stat-value" id="a-pub">50</div><div class="stat-change" id="a-pub-c">19 scheduled</div></div>
            </div>
            <div class="charts-row">
              <div class="chart-card">
                <div class="chart-card-title">Reach Over Time</div>
                <div class="chart-area"><canvas id="chart-reach"></canvas></div>
              </div>
              <div class="chart-card">
                <div class="chart-card-title">Platform Breakdown</div>
                <div class="chart-area"><canvas id="chart-platform"></canvas></div>
              </div>
            </div>
            <div class="chart-card">
              <div class="chart-card-title">Engagement by Platform</div>
              <div class="chart-area"><canvas id="chart-engagement"></canvas></div>
            </div>
          </div>
        </div>
      </div>

      <!-- SUB-AGENTS -->
      <div class="panel" id="panel-agents">
        <div class="agents-page">
          <div class="page-header">
            <div class="page-header-row">
              <div>
                <div class="page-title">Sub-Agents</div>
                <div class="page-subtitle">Specialized operators extending Imani's capabilities</div>
              </div>
            </div>
          </div>
          <div class="agents-body">
            <div class="agents-grid" id="agents-grid">
              <!-- Active Sub-Agents -->
              <div class="agent-card agent-active" data-agent="content-repurposer">
                <div class="agent-card-head">
                  <div class="agent-icon" style="background:var(--accent-subtle);color:var(--accent);">&#9998;</div>
                  <div class="agent-name">Content Repurposer</div>
                  <div class="agent-status-dot active"></div>
                </div>
                <div class="agent-desc">Takes YouTube content and generates platform-specific versions: IG carousels, LinkedIn posts, X threads, TikTok scripts, memo sections.</div>
                <div class="agent-stats" id="repurposer-stats">
                  <span class="agent-stat"><strong id="repurposer-produced">0</strong> items produced</span>
                  <span class="agent-stat"><strong id="repurposer-notes">0</strong> style notes</span>
                </div>
                <div class="agent-badge active">Active</div>
                <div class="agent-actions">
                  <button class="btn btn-sm btn-accent" onclick="openRepurposeModal()">Repurpose Content</button>
                </div>
              </div>

              <div class="agent-card agent-active" data-agent="analytics-digest">
                <div class="agent-card-head">
                  <div class="agent-icon" style="background:var(--instagram-bg);color:var(--instagram);">&#9783;</div>
                  <div class="agent-name">Analytics Digest</div>
                  <div class="agent-status-dot active"></div>
                </div>
                <div class="agent-desc">Weekly intelligence briefing: performance analysis, competitor/inspiration tracking, hook study, content strategy recommendations.</div>
                <div class="agent-stats" id="analytics-stats">
                  <span class="agent-stat"><strong id="analytics-tracked">0</strong> accounts tracked</span>
                  <span class="agent-stat"><strong id="analytics-digests">0</strong> digests</span>
                </div>
                <div class="agent-badge active">Active</div>
                <div class="agent-actions">
                  <button class="btn btn-sm btn-accent" onclick="generateDigest()">Generate Digest</button>
                  <button class="btn btn-sm btn-ghost" onclick="openTrackedAccountsModal()">Manage Accounts</button>
                </div>
              </div>

              <div class="agent-card agent-active" data-agent="content-creator">
                <div class="agent-card-head">
                  <div class="agent-icon" style="background:var(--youtube-bg);color:var(--youtube);">&#9733;</div>
                  <div class="agent-name">Content Creator</div>
                  <div class="agent-status-dot active"></div>
                </div>
                <div class="agent-desc">Creates carousel drafts with slide-by-slide copy and visual direction. Canva integration coming. Learns from your feedback.</div>
                <div class="agent-stats" id="creator-stats">
                  <span class="agent-stat"><strong id="creator-drafts">0</strong> drafts</span>
                  <span class="agent-stat"><strong id="creator-approved">0</strong> approved</span>
                  <span class="agent-stat">Level <strong id="creator-level">1</strong>/4</span>
                </div>
                <div class="agent-badge active">Active — Draft Mode</div>
                <div class="agent-actions">
                  <button class="btn btn-sm btn-accent" onclick="openCarouselModal()">Create Carousel</button>
                </div>
              </div>

              <!-- Future Sub-Agents -->
              <div class="agent-card">
                <div class="agent-card-head">
                  <div class="agent-icon" style="background:rgba(52,211,153,0.12);color:var(--success);">&#10003;</div>
                  <div class="agent-name">Trend Scout</div>
                </div>
                <div class="agent-desc">Monitors trends across platforms and recommends timely content opportunities to ride the wave.</div>
                <div class="agent-badge">Coming Soon</div>
              </div>
              <div class="agent-card">
                <div class="agent-card-head">
                  <div class="agent-icon" style="background:var(--linkedin-bg);color:var(--linkedin);">&#9878;</div>
                  <div class="agent-name">Brand Voice Guardian</div>
                </div>
                <div class="agent-desc">Ensures all content maintains consistent tone, voice, and brand alignment across platforms.</div>
                <div class="agent-badge">Coming Soon</div>
              </div>
              <div class="agent-card">
                <div class="agent-card-head">
                  <div class="agent-icon" style="background:var(--tiktok-bg);color:var(--tiktok);">&#9881;</div>
                  <div class="agent-name">Campaign Manager</div>
                </div>
                <div class="agent-desc">Plans, schedules, and optimizes multi-platform content campaigns with clear milestones.</div>
                <div class="agent-badge">Coming Soon</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- DAILY PLANNER -->
      <div class="panel" id="panel-planner">
        <div class="planner-page">
          <div class="planner-header">
            <div class="page-header-row">
              <div>
                <div class="page-title">Daily Planner</div>
                <div class="page-subtitle">Plan your day with Imani — time-block everything</div>
              </div>
              <button class="btn btn-accent" onclick="planWithImani()">Plan with Imani</button>
            </div>
            <div class="planner-date-nav">
              <button onclick="plannerPrevDay()">&larr; Prev</button>
              <div class="planner-date-label" id="planner-date-label">Today</div>
              <button onclick="plannerNextDay()">Next &rarr;</button>
              <button onclick="plannerToday()" style="margin-left:8px;background:var(--accent-subtle);color:var(--accent);border-color:var(--accent);">Today</button>
            </div>
          </div>
          <div class="planner-body">
            <div class="planner-columns">
              <div class="planner-schedule">
                <div class="planner-schedule-header">
                  <div class="planner-schedule-title">&#9925; Schedule</div>
                  <span style="font-size:11px;color:var(--text-muted);">Click a slot to add a task</span>
                </div>
                <div class="planner-time-grid" id="planner-time-grid"></div>
              </div>
              <div class="planner-sidebar">
                <div class="planner-card">
                  <div class="planner-card-header">&#127919; Priorities</div>
                  <div class="planner-card-body" id="planner-priorities"><!-- JS fills dynamically -->
                  </div>
                </div>
                <div class="planner-card">
                  <div class="planner-card-header">&#9889; Important Tasks</div>
                  <div class="planner-card-body" id="planner-tasks"></div>
                  <div class="add-task-row" style="padding:0 20px 16px;">
                    <input type="text" class="add-task-input" id="add-task-input" placeholder="Add a task..." onkeydown="if(event.key==='Enter')addImportantTask()">
                    <button class="add-task-btn" onclick="addImportantTask()">+</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

            <!-- ROUTINES -->
      <div class="panel" id="panel-routines">
        <div class="routines-page">
          <div class="routines-header">
            <div class="page-header-row">
              <div>
                <div class="page-title">Routine Tracker</div>
                <div class="page-subtitle">Morning, afternoon, and night — build the habits that build you</div>
              </div>
            </div>
          </div>
          <div class="routines-body">
            <div class="routines-grid">
              <div class="routine-card" id="routine-morning">
                <div class="routine-card-top">
                  <div class="routine-icon morning">&#9728;</div>
                  <div><div class="routine-title">Morning</div><div class="routine-subtitle">Start strong</div></div>
                </div>
                <div class="routine-items" id="routine-morning-items"></div>
                <div class="routine-progress"><div class="routine-progress-bar"><div class="routine-progress-fill morning" id="routine-morning-bar" style="width:0%"></div></div><div class="routine-progress-text" id="routine-morning-pct">0%</div></div>
                <div class="routine-add-row">
                  <input type="text" class="routine-add-input" id="routine-morning-input" placeholder="Add habit..." onkeydown="if(event.key==='Enter')addRoutineItem('morning')">
                  <button class="routine-add-btn" onclick="addRoutineItem('morning')">+</button>
                </div>
              </div>
              <div class="routine-card" id="routine-afternoon">
                <div class="routine-card-top">
                  <div class="routine-icon afternoon">&#9788;</div>
                  <div><div class="routine-title">Afternoon</div><div class="routine-subtitle">Stay focused</div></div>
                </div>
                <div class="routine-items" id="routine-afternoon-items"></div>
                <div class="routine-progress"><div class="routine-progress-bar"><div class="routine-progress-fill afternoon" id="routine-afternoon-bar" style="width:0%"></div></div><div class="routine-progress-text" id="routine-afternoon-pct">0%</div></div>
                <div class="routine-add-row">
                  <input type="text" class="routine-add-input" id="routine-afternoon-input" placeholder="Add habit..." onkeydown="if(event.key==='Enter')addRoutineItem('afternoon')">
                  <button class="routine-add-btn" onclick="addRoutineItem('afternoon')">+</button>
                </div>
              </div>
              <div class="routine-card" id="routine-night">
                <div class="routine-card-top">
                  <div class="routine-icon night">&#9790;</div>
                  <div><div class="routine-title">Night</div><div class="routine-subtitle">Wind down well</div></div>
                </div>
                <div class="routine-items" id="routine-night-items"></div>
                <div class="routine-progress"><div class="routine-progress-bar"><div class="routine-progress-fill night" id="routine-night-bar" style="width:0%"></div></div><div class="routine-progress-text" id="routine-night-pct">0%</div></div>
                <div class="routine-add-row">
                  <input type="text" class="routine-add-input" id="routine-night-input" placeholder="Add habit..." onkeydown="if(event.key==='Enter')addRoutineItem('night')">
                  <button class="routine-add-btn" onclick="addRoutineItem('night')">+</button>
                </div>
              </div>
            </div>
            <div class="routines-streak" id="routines-streak">
              <div class="streak-title">&#128293; Streak — Last 30 Days</div>
              <div class="streak-row" id="streak-dots"></div>
            </div>
          </div>
        </div>
      </div>

            <!-- REPURPOSE MODAL -->
      <div class="modal-overlay" id="repurpose-modal" style="display:none">
        <div class="modal-box" style="max-width:600px">
          <div class="modal-title">Repurpose Content</div>
          <form id="repurpose-form" onsubmit="submitRepurpose(event)">
            <div class="field">
              <label class="field-label">Source Platform</label>
              <select class="field-input" id="repurpose-source">
                <option value="youtube">YouTube</option>
                <option value="linkedin">LinkedIn</option>
                <option value="memo">Memo / Newsletter</option>
                <option value="instagram">Instagram</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label">Content (paste transcript, script, or text)</label>
              <textarea class="field-input" id="repurpose-content" rows="6" placeholder="Paste your YouTube transcript, LinkedIn post, memo text..." required style="resize:vertical;min-height:100px;font-family:inherit"></textarea>
            </div>
            <div class="field">
              <label class="field-label">Additional Context (optional)</label>
              <input type="text" class="field-input" id="repurpose-context" placeholder="e.g. Focus on the hiring framework, CTA to newsletter...">
            </div>
            <div class="modal-actions">
              <button type="button" class="btn btn-ghost" onclick="closeRepurposeModal()">Cancel</button>
              <button type="submit" class="btn btn-accent" id="repurpose-submit">Repurpose</button>
            </div>
          </form>
          <div id="repurpose-results" style="display:none;margin-top:16px"></div>
        </div>
      </div>

      <!-- CAROUSEL MODAL -->
      <div class="modal-overlay" id="carousel-modal" style="display:none">
        <div class="modal-box" style="max-width:600px">
          <div class="modal-title">Create Carousel</div>
          <form id="carousel-form" onsubmit="submitCarousel(event)">
            <div class="field">
              <label class="field-label">Topic</label>
              <input type="text" class="field-input" id="carousel-topic" placeholder="e.g. 5 Signs Your Creative Business Needs Structure" required>
            </div>
            <div class="field">
              <label class="field-label">Platform</label>
              <select class="field-input" id="carousel-platform">
                <option value="instagram">Instagram</option>
                <option value="linkedin">LinkedIn</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label">Number of Slides</label>
              <select class="field-input" id="carousel-slides">
                <option value="5">5 slides</option>
                <option value="7">7 slides</option>
                <option value="10">10 slides</option>
                <option value="3">3 slides (quick)</option>
              </select>
            </div>
            <div class="field">
              <label class="field-label">Reference Content (optional)</label>
              <textarea class="field-input" id="carousel-reference" rows="3" placeholder="Paste source material, notes, or transcript to draw from..." style="resize:vertical;font-family:inherit"></textarea>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn btn-ghost" onclick="closeCarouselModal()">Cancel</button>
              <button type="submit" class="btn btn-accent" id="carousel-submit">Create Draft</button>
            </div>
          </form>
          <div id="carousel-results" style="display:none;margin-top:16px"></div>
        </div>
      </div>

      <!-- TRACKED ACCOUNTS MODAL -->
      <div class="modal-overlay" id="accounts-modal" style="display:none">
        <div class="modal-box" style="max-width:550px">
          <div class="modal-title">Tracked Accounts</div>
          <div id="accounts-list" style="margin-bottom:16px;max-height:300px;overflow-y:auto"></div>
          <form id="accounts-form" onsubmit="addTrackedAccount(event)">
            <div style="display:flex;gap:8px;align-items:end">
              <div class="field" style="flex:1">
                <label class="field-label">Platform</label>
                <select class="field-input" id="account-platform">
                  <option value="instagram">Instagram</option>
                  <option value="linkedin">LinkedIn</option>
                  <option value="youtube">YouTube</option>
                  <option value="twitter">Twitter/X</option>
                  <option value="tiktok">TikTok</option>
                </select>
              </div>
              <div class="field" style="flex:2">
                <label class="field-label">Handle</label>
                <input type="text" class="field-input" id="account-handle" placeholder="@username" required>
              </div>
              <div class="field" style="flex:1">
                <label class="field-label">Type</label>
                <select class="field-input" id="account-category">
                  <option value="inspiration">Inspiration</option>
                  <option value="competitor">Competitor</option>
                  <option value="industry_leader">Industry Leader</option>
                </select>
              </div>
            </div>
            <div class="modal-actions">
              <button type="button" class="btn btn-ghost" onclick="closeAccountsModal()">Close</button>
              <button type="submit" class="btn btn-accent">Add Account</button>
            </div>
          </form>
        </div>
      </div>

    </div>
  </div>

  <!-- MODAL -->
  <div class="modal-overlay" id="modal">
    <div class="modal-box">
      <div class="modal-title" id="modal-title">New Content</div>
      <form id="modal-form">
        <input type="hidden" id="modal-platform" value="">
        <div class="field">
          <label class="field-label">Title</label>
          <input type="text" class="field-input" id="field-title" placeholder="e.g. Behind the scenes of our new launch" required>
        </div>
        <div class="field">
          <label class="field-label">Type</label>
          <select class="field-input" id="field-type">
            <option value="post">Post</option>
            <option value="reel">Reel / Video</option>
            <option value="story">Story</option>
            <option value="thread">Thread</option>
            <option value="article">Article</option>
          </select>
        </div>
        <div class="field">
          <label class="field-label">Scheduled Date</label>
          <input type="date" class="field-input" id="field-date">
        </div>
        <div class="field">
          <label class="field-label">Notes</label>
          <input type="text" class="field-input" id="field-notes" placeholder="Any extra context...">
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-ghost" onclick="closeModal()">Cancel</button>
          <button type="submit" class="btn btn-accent">Add Content</button>
        </div>
      </form>
    </div>
  </div>

  <script>
    // ===== DATA (loaded from Metricool via /api endpoints) =====
    const platformData = {
      instagram: { content: [], listId: 'ig-content' },
      twitter:   { content: [], listId: 'tw-content' },
      tiktok:    { content: [], listId: 'tt-content' },
      youtube:   { content: [], listId: 'yt-content' },
      linkedin:  { content: [], listId: 'li-content' },
    };

    // Fallback placeholder data (shown while Metricool loads or if not configured)
    const fallbackData = {
      instagram: [
        { title: 'Loading live data from Metricool...', type: 'Post', date: '', status: 'draft', engagement: '\u2014' }
      ],
      twitter: [
        { title: 'Loading live data from Metricool...', type: 'Post', date: '', status: 'draft', engagement: '\u2014' }
      ],
      tiktok: [
        { title: 'Loading live data from Metricool...', type: 'Video', date: '', status: 'draft', engagement: '\u2014' }
      ],
      youtube: [
        { title: 'Loading live data from Metricool...', type: 'Video', date: '', status: 'draft', engagement: '\u2014' }
      ],
      linkedin: [
        { title: 'Loading live data from Metricool...', type: 'Post', date: '', status: 'draft', engagement: '\u2014' }
      ],
    };

    // Set fallback immediately
    Object.keys(fallbackData).forEach(p => { platformData[p].content = fallbackData[p]; });

    // Fetch live data from backend
    async function loadLiveData() {
      try {
        const res = await fetch('/api/overview?days=30');
        const json = await res.json();
        if (json.data && json.data.posts) {
          const posts = json.data.posts;
          if (posts.instagram && posts.instagram.length) platformData.instagram.content = posts.instagram;
          if (posts.twitter && posts.twitter.length)   platformData.twitter.content = posts.twitter;
          if (posts.tiktok && posts.tiktok.length)     platformData.tiktok.content = posts.tiktok;
          if (posts.youtube && posts.youtube.length)    platformData.youtube.content = posts.youtube;
          if (posts.linkedin && posts.linkedin.length)  platformData.linkedin.content = posts.linkedin;

          // Re-render all platform lists
          Object.keys(platformData).forEach(renderContent);

          // Update analytics stats if aggregation data is available
          if (json.data.aggregations) updateStatsFromAggregations(json.data.aggregations);

          // Update charts if timeline data is available
          if (json.data.timeline) updateChartsFromTimeline(json.data.timeline);

          console.log('Imani: Live Metricool data loaded.');

          // Sync calendar statuses with published posts
          try {
            await fetch('/api/calendar/sync', { method: 'POST' });
            console.log('Imani: Calendar sync completed.');
          } catch(syncErr) {
            console.log('Imani: Calendar sync skipped.');
          }
        }
      } catch(e) {
        console.log('Imani: Metricool not available, using dashboard placeholders.');
      }
    }

    // Load platform-specific detail when navigating to a platform page
    async function loadPlatformDetail(platform) {
      try {
        const res = await fetch('/api/platform/' + platform + '?days=30');
        const json = await res.json();
        if (json.data) {
          // Merge posts + reels for Instagram content list
          let allContent = [];
          if (json.data.posts) allContent = allContent.concat(json.data.posts);
          if (json.data.reels) allContent = allContent.concat(json.data.reels);
          if (allContent.length) {
            // Sort by date descending
            allContent.sort((a, b) => new Date(b.date) - new Date(a.date));
            platformData[platform].content = allContent;
          }
          renderContent(platform);

          // Update stats from aggregation or computed_stats
          if (json.data.aggregation) {
            updatePlatformStatsFromAgg(platform, json.data.aggregation);
          } else if (json.data.computed_stats) {
            updatePlatformStatsFromComputed(platform, json.data.computed_stats);
          }
        }
      } catch(e) { console.log('Error loading platform data:', e); }

      // Also load calendar items for this platform
      loadCalendarForPlatform(platform);
    }

    // Load content calendar from Google Sheets
    async function loadCalendarForPlatform(platform) {
      try {
        const res = await fetch('/api/calendar?platform=' + platform);
        const json = await res.json();
        if (json.data && json.data.length) {
          // Add scheduled items to the content list
          const scheduled = json.data.map(item => ({
            title: item.title || item.hook || 'Scheduled content',
            type: item.content_type || 'Post',
            date: item.date || '',
            status: 'scheduled',
            engagement: '\u2014',
            from_calendar: true
          }));
          // Prepend scheduled items before published ones
          const existing = platformData[platform].content.filter(c => !c.from_calendar);
          platformData[platform].content = scheduled.concat(existing);
          renderContent(platform);
        }
      } catch(e) { /* calendar not configured */ }
    }

    function updateStatsFromAggregations(aggs) {
      // Update the analytics overview cards with real aggregation data
      let totalReach = 0, totalFollowers = 0, totalPosts = 0;
      ['instagram', 'twitter', 'youtube', 'linkedin'].forEach(p => {
        const a = aggs[p];
        if (!a) return;
        totalReach += (a.reach || a.impressions || a.views || 0);
        totalFollowers += (a.followers || a.connections || a.subscribers || 0);
        totalPosts += (a.posts || a.tweets || a.videos || 0);
      });
      if (totalReach) document.getElementById('a-reach').textContent = formatNum(totalReach);
      if (totalFollowers) document.getElementById('a-fol').textContent = formatNum(totalFollowers);
      if (totalPosts) document.getElementById('a-pub').textContent = totalPosts;
    }

    function updatePlatformStatsFromAgg(platform, agg) {
      // Update stats from Metricool aggregation data
      const prefixMap = { instagram: 'ig', twitter: 'tw', tiktok: 'tt', youtube: 'yt', linkedin: 'li' };
      const prefix = prefixMap[platform] || platform;
      const fEl = document.getElementById(prefix + '-followers');
      const eEl = document.getElementById(prefix + '-engagement');
      const rEl = document.getElementById(prefix + '-reach');
      const pEl = document.getElementById(prefix + '-posts');
      if (fEl) fEl.textContent = formatNum(agg.followers || agg.subscribers || 0);
      if (eEl && agg.engagement !== undefined) eEl.textContent = (agg.engagement * 100).toFixed(1) + '%';
      if (rEl) rEl.textContent = formatNum(agg.reach || agg.impressions || agg.views || 0);
      if (pEl) pEl.textContent = agg.posts || agg.videos || 0;
      // Update notes
      const fNote = document.getElementById(prefix + '-followers-note');
      if (fNote) fNote.textContent = 'From Metricool';
      const eNote = document.getElementById(prefix + '-engagement-note');
      if (eNote) eNote.textContent = 'Average rate';
    }

    function updatePlatformStatsFromComputed(platform, stats) {
      // Update stats computed from actual post data (fallback when aggregations are null)
      const prefixMap2 = { instagram: 'ig', twitter: 'tw', tiktok: 'tt', youtube: 'yt', linkedin: 'li' };
      const prefix = prefixMap2[platform] || platform;
      const fEl = document.getElementById(prefix + '-followers');
      const eEl = document.getElementById(prefix + '-engagement');
      const rEl = document.getElementById(prefix + '-reach');
      const pEl = document.getElementById(prefix + '-posts');
      if (fEl && stats.followers) {
        fEl.textContent = formatNum(stats.followers);
        const fNote = document.getElementById(prefix + '-followers-note');
        if (fNote) fNote.textContent = 'Current';
      }
      if (eEl && stats.avg_engagement_rate !== undefined) {
        eEl.textContent = stats.avg_engagement_rate + '%';
        const eNote = document.getElementById(prefix + '-engagement-note');
        if (eNote) eNote.textContent = 'Avg from ' + stats.posts_count + ' posts';
      }
      if (rEl && stats.total_reach) {
        rEl.textContent = formatNum(stats.total_reach);
      }
      if (pEl && stats.posts_count) {
        pEl.textContent = stats.posts_count;
        const pNote = document.getElementById(prefix + '-posts-note');
        if (pNote) pNote.textContent = 'Last 30 days';
      }
    }

    function updatePlatformStats(platform, agg) {
      updatePlatformStatsFromAgg(platform, agg);
    }

    function updateChartsFromTimeline(timeline) {
      // Update reach chart with real timeline data if available
      if (window.reachChart && timeline.instagram_reach && timeline.instagram_reach.length) {
        const labels = timeline.instagram_reach.map(d => d.label);
        window.reachChart.data.labels = labels;
        window.reachChart.data.datasets[0].data = timeline.instagram_reach.map(d => d.value);
        if (timeline.twitter_impressions) {
          window.reachChart.data.datasets[1].data = timeline.twitter_impressions.map(d => d.value);
        }
        if (timeline.youtube_views) {
          window.reachChart.data.datasets[3].data = timeline.youtube_views.map(d => d.value);
        }
        if (timeline.linkedin_impressions) {
          window.reachChart.data.datasets[4].data = timeline.linkedin_impressions.map(d => d.value);
        }
        window.reachChart.update();
      }
    }

    function formatNum(n) {
      if (n >= 1000000) return (n/1000000).toFixed(1) + 'M';
      if (n >= 1000) return (n/1000).toFixed(1) + 'K';
      return String(n);
    }

    // Kick off live data load
    loadLiveData();
    // Also load detailed data for each platform (including computed stats)
    ['instagram', 'twitter', 'tiktok', 'youtube', 'linkedin'].forEach(p => loadPlatformDetail(p));

    // ===== NAVIGATION =====
    document.querySelector('.sidebar-nav').addEventListener('click', function(e) {
      const item = e.target.closest('.nav-item');
      if (!item) return;
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      item.classList.add('active');
      const panelName = item.dataset.panel;
      const panel = document.getElementById('panel-' + panelName);
      if (panel) panel.classList.add('active');
      if (['instagram', 'twitter', 'tiktok', 'youtube', 'linkedin'].includes(panelName)) {
        loadPlatformDetail(panelName);
      }
    });

    // ===== TIME OF DAY =====
    const h = new Date().getHours();
    document.getElementById('tod').textContent = h < 12 ? 'morning' : h < 17 ? 'afternoon' : 'evening';

    // ===== TOOL STATUS (loaded from /health) =====
    async function loadToolStatus() {
      try {
        const res = await fetch('/health');
        const data = await res.json();
        const el = document.getElementById('tools-status');
        if (data.tools) {
          el.innerHTML = Object.entries(data.tools).map(([k, v]) => {
            const on = v === 'connected' || v === 'configured';
            return '<span class="tool-dot ' + (on ? 'on' : 'off') + '">' + k.charAt(0).toUpperCase() + k.slice(1) + '</span>';
          }).join('');
        }
      } catch(e) { /* preview mode — skip */ }
    }
    loadToolStatus();

    // ===== CHAT (wired to real /chat and /messages endpoints) =====
    const imaniAvatarSVG = '<svg viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg" width="28" height="28">' +
      '<rect width="28" height="28" rx="8" fill="#1F1F24"/>' +
      '<rect width="28" height="28" rx="8" fill="url(#glass-grad)" opacity="0.5"/>' +
      '<circle cx="14" cy="11" r="5.5" fill="url(#face-glow)" stroke="#C75B3A" stroke-width="0.4" opacity="0.8"/>' +
      '<ellipse cx="11.5" cy="10" rx="1" ry="1.2" fill="#C75B3A" opacity="0.7"/>' +
      '<ellipse cx="16.5" cy="10" rx="1" ry="1.2" fill="#C75B3A" opacity="0.7"/>' +
      '<path d="M12 13 Q14 14.8 16 13" stroke="#C75B3A" stroke-width="0.6" fill="none" opacity="0.5" stroke-linecap="round"/>' +
      '<path d="M9 19 Q14 23.5 19 19" fill="#C75B3A" opacity="0.12"/>' +
      '</svg>';

    function addMessage(role, text) {
      const container = document.getElementById('chat-messages');
      const empty = document.getElementById('chat-empty');
      if (empty) empty.remove();

      const div = document.createElement('div');
      div.className = 'msg ' + (role === 'user' ? 'msg-user' : 'msg-ai');

      if (role === 'user') {
        div.innerHTML = '<div class="msg-bubble">' + escapeHtml(text) + '</div>';
      } else {
        let parsed;
        try { parsed = marked.parse(text); } catch(e) { parsed = text.replace(/\n/g,'<br>'); }
        div.innerHTML = '<div class="msg-avatar">' + imaniAvatarSVG + '</div><div class="msg-bubble">' + parsed + '</div>';
      }

      container.appendChild(div);
      container.scrollTop = container.scrollHeight;
    }

    function escapeHtml(text) {
      const d = document.createElement('div');
      d.textContent = text;
      return d.innerHTML;
    }

    function showTyping() {
      const container = document.getElementById('chat-messages');
      const t = document.createElement('div');
      t.className = 'typing-indicator msg-ai';
      t.id = 'typing';
      t.innerHTML = '<div class="msg-avatar">' + imaniAvatarSVG + '</div>' +
        '<div class="typing-dots"><span></span><span></span><span></span></div>';
      container.appendChild(t);
      container.scrollTop = container.scrollHeight;
    }

    function hideTyping() {
      const t = document.getElementById('typing');
      if (t) t.remove();
    }

    async function sendChat() {
      const input = document.getElementById('chat-input');
      const msg = input.value.trim();
      if (!msg) return;
      addMessage('user', msg);
      input.value = '';
      showTyping();

      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        hideTyping();
        addMessage('assistant', data.response || "I'm processing that. Give me a moment.");
      } catch(e) {
        hideTyping();
        addMessage('assistant', "Connection issue. I'm still here \u2014 try again in a moment.");
      }
    }

    document.getElementById('chat-send').addEventListener('click', sendChat);
    document.getElementById('chat-input').addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
    });

    // Load chat history from backend
    async function loadHistory() {
      try {
        const res = await fetch('/messages?limit=50');
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          const empty = document.getElementById('chat-empty');
          if (empty) empty.remove();
          data.messages.forEach(m => {
            addMessage(m.role === 'user' ? 'user' : 'assistant', m.content);
          });
        }
      } catch(e) { /* preview mode — keep greeting */ }
    }
    loadHistory();

    // ===== RENDER PLATFORM CONTENT =====
    function renderContent(platformKey) {
      const data = platformData[platformKey];
      const list = document.getElementById(data.listId);
      list.innerHTML = '';

      data.content.forEach(item => {
        const row = document.createElement('div');
        row.className = 'content-row';
        const isScheduled = item.status === 'scheduled' || item.from_calendar;
        const statusClass = isScheduled ? 'status-scheduled' : 'status-' + item.status;
        const calendarBadge = item.from_calendar ? ' <span style="color:var(--warning);font-size:11px;opacity:0.8">&#x1f4c5; from calendar</span>' : '';
        row.innerHTML =
          '<div class="content-status ' + statusClass + '"></div>' +
          '<div class="content-info">' +
            '<div class="content-title">' + item.title + calendarBadge + '</div>' +
            '<div class="content-meta">' + item.type + ' &middot; ' + item.date + ' &middot; <span style="text-transform:capitalize">' + item.status + '</span></div>' +
          '</div>' +
          '<div class="content-engagement">' +
            '<div class="content-eng-value">' + item.engagement + '</div>' +
            '<div class="content-eng-label">' + (item.engagement === '\u2014' ? '' : 'engagements') + '</div>' +
          '</div>' +
          '<div class="content-actions">' +
            '<button class="content-action-btn" title="Edit"><svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>' +
            '<button class="content-action-btn" title="More"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/></svg></button>' +
          '</div>';
        list.appendChild(row);
      });
    }

    Object.keys(platformData).forEach(renderContent);

    // ===== MODAL =====
    function openModal(platform) {
      document.getElementById('modal-platform').value = platform;
      const names = { instagram: 'Instagram', twitter: 'Twitter / X', tiktok: 'TikTok', youtube: 'YouTube', linkedin: 'LinkedIn' };
      document.getElementById('modal-title').textContent = 'New ' + (names[platform] || '') + ' Content';
      document.getElementById('modal').classList.add('active');
    }

    function closeModal() {
      document.getElementById('modal').classList.remove('active');
      document.getElementById('modal-form').reset();
    }

    document.getElementById('modal').addEventListener('click', e => {
      if (e.target.id === 'modal') closeModal();
    });

    document.getElementById('modal-form').addEventListener('submit', e => {
      e.preventDefault();
      const platform = document.getElementById('modal-platform').value;
      const title = document.getElementById('field-title').value;
      const type = document.getElementById('field-type').value;
      const date = document.getElementById('field-date').value;

      if (platformData[platform]) {
        const dateStr = date ? new Date(date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : 'TBD';
        const typeNames = { post: 'Post', reel: 'Reel / Video', story: 'Story', thread: 'Thread', article: 'Article' };
        platformData[platform].content.unshift({
          title: title, type: typeNames[type] || type, date: dateStr, status: 'draft', engagement: '\u2014'
        });
        renderContent(platform);
      }
      closeModal();
    });

    // ===== ANALYTICS TABS =====
    // These start as placeholders and get updated when live data loads
    const analyticsData = {
      all:       { reach: '--', reachC: 'Loading from Metricool...', eng: '--', engC: '', fol: '--', folC: '', pub: '--', pubC: '' },
      instagram: { reach: '--', reachC: 'Loading...', eng: '--', engC: '', fol: '--', folC: '', pub: '--', pubC: '' },
      twitter:   { reach: '--', reachC: 'Loading...', eng: '--', engC: '', fol: '--', folC: '', pub: '--', pubC: '' },
      tiktok:    { reach: '--', reachC: 'Loading...', eng: '--', engC: '', fol: '--', folC: '', pub: '--', pubC: '' },
      youtube:   { reach: '--', reachC: 'Loading...', eng: '--', engC: '', fol: '--', folC: '', pub: '--', pubC: '' },
      linkedin:  { reach: '--', reachC: 'Loading...', eng: '--', engC: '', fol: '--', folC: '', pub: '--', pubC: '' },
    };

    // Fetch real analytics data for each platform tab
    async function loadAnalyticsData() {
      try {
        const res = await fetch('/api/overview?days=7');
        const json = await res.json();
        if (!json.data || !json.data.aggregations) return;
        const aggs = json.data.aggregations;

        // Map aggregation data to analytics tab format
        ['instagram', 'twitter', 'youtube', 'linkedin'].forEach(p => {
          const a = aggs[p];
          if (!a) return;
          analyticsData[p] = {
            reach: formatNum(a.reach || a.impressions || a.views || 0),
            reachC: 'Last 7 days',
            eng: a.engagement !== undefined ? (a.engagement * 100).toFixed(1) + '%' : '--',
            engC: 'Average engagement',
            fol: formatNum(a.followers || a.connections || a.subscribers || 0),
            folC: 'Total followers',
            pub: String(a.posts || a.tweets || a.videos || 0),
            pubC: 'This period',
          };
        });

        // Calculate "all" totals
        let tReach = 0, tFol = 0, tPub = 0;
        ['instagram', 'twitter', 'youtube', 'linkedin'].forEach(p => {
          const a = aggs[p];
          if (!a) return;
          tReach += (a.reach || a.impressions || a.views || 0);
          tFol += (a.followers || a.connections || a.subscribers || 0);
          tPub += (a.posts || a.tweets || a.videos || 0);
        });
        analyticsData.all = {
          reach: formatNum(tReach), reachC: 'All platforms, last 7 days',
          eng: '--', engC: 'Weighted average',
          fol: formatNum(tFol), folC: 'Total across platforms',
          pub: String(tPub), pubC: 'This period',
        };

        // Refresh active tab display
        const activeTab = document.querySelector('.analytics-tab.active');
        if (activeTab) {
          const d = analyticsData[activeTab.dataset.tab];
          if (d) {
            document.getElementById('a-reach').textContent = d.reach;
            document.getElementById('a-reach-c').textContent = d.reachC;
            document.getElementById('a-eng').textContent = d.eng;
            document.getElementById('a-eng-c').textContent = d.engC;
            document.getElementById('a-fol').textContent = d.fol;
            document.getElementById('a-fol-c').textContent = d.folC;
            document.getElementById('a-pub').textContent = d.pub;
            document.getElementById('a-pub-c').textContent = d.pubC;
          }
        }
      } catch(e) { /* keep placeholders */ }
    }
    loadAnalyticsData();

    document.querySelectorAll('.analytics-tab').forEach(tab => {
      tab.addEventListener('click', function() {
        document.querySelectorAll('.analytics-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
        const d = analyticsData[this.dataset.tab];
        if (d) {
          document.getElementById('a-reach').textContent = d.reach;
          document.getElementById('a-reach-c').textContent = d.reachC;
          document.getElementById('a-eng').textContent = d.eng;
          document.getElementById('a-eng-c').textContent = d.engC;
          document.getElementById('a-fol').textContent = d.fol;
          document.getElementById('a-fol-c').textContent = d.folC;
          document.getElementById('a-pub').textContent = d.pub;
          document.getElementById('a-pub-c').textContent = d.pubC;
        }
      });
    });

    // ===== CHARTS =====
    const chartColors = { grid: 'rgba(42,42,50,0.5)', tick: '#5A5560' };
    Chart.defaults.color = chartColors.tick;
    Chart.defaults.borderColor = chartColors.grid;

    window.reachChart = new Chart(document.getElementById('chart-reach'), {
      type: 'line',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
          { label: 'Instagram', data: [1800,2200,1900,2800,2600,3100,2400], borderColor: '#E1306C', backgroundColor: 'rgba(225,48,108,0.05)', borderWidth: 2, tension: 0.4, fill: true, pointRadius: 3 },
          { label: 'Twitter', data: [3200,4100,3800,5200,4800,5100,4600], borderColor: '#1DA1F2', backgroundColor: 'rgba(29,161,242,0.05)', borderWidth: 2, tension: 0.4, fill: true, pointRadius: 3 },
          { label: 'TikTok', data: [800,1200,3200,1400,900,1100,2100], borderColor: '#FE2C55', backgroundColor: 'rgba(254,44,85,0.05)', borderWidth: 2, tension: 0.4, fill: true, pointRadius: 3 },
          { label: 'YouTube', data: [500,800,600,1200,900,1100,700], borderColor: '#FF0000', backgroundColor: 'rgba(255,0,0,0.05)', borderWidth: 2, tension: 0.4, fill: true, pointRadius: 3 },
          { label: 'LinkedIn', data: [1200,1500,1300,1800,2100,1600,1400], borderColor: '#0A66C2', backgroundColor: 'rgba(10,102,194,0.05)', borderWidth: 2, tension: 0.4, fill: true, pointRadius: 3 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 11 } } } },
        scales: {
          y: { beginAtZero: true, grid: { color: chartColors.grid }, ticks: { font: { size: 11 } } },
          x: { grid: { display: false }, ticks: { font: { size: 11 } } }
        }
      }
    });

    new Chart(document.getElementById('chart-platform'), {
      type: 'doughnut',
      data: {
        labels: ['Instagram', 'Twitter / X', 'TikTok', 'YouTube', 'LinkedIn'],
        datasets: [{ data: [22,32,16,14,16], backgroundColor: ['#E1306C','#1DA1F2','#FE2C55','#FF0000','#0A66C2'], borderColor: '#18181C', borderWidth: 3 }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '65%',
        plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 11 } } } }
      }
    });

    new Chart(document.getElementById('chart-engagement'), {
      type: 'bar',
      data: {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [
          { label: 'Instagram', data: [120,180,150,220,200,280,190], backgroundColor: '#E1306C', borderRadius: 4 },
          { label: 'Twitter', data: [200,280,250,340,310,290,260], backgroundColor: '#1DA1F2', borderRadius: 4 },
          { label: 'TikTok', data: [80,120,420,140,90,110,200], backgroundColor: '#FE2C55', borderRadius: 4 },
          { label: 'YouTube', data: [40,70,55,95,80,100,65], backgroundColor: '#FF0000', borderRadius: 4 },
          { label: 'LinkedIn', data: [60,90,75,110,130,85,70], backgroundColor: '#0A66C2', borderRadius: 4 },
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 11 } } } },
        scales: {
          y: { beginAtZero: true, stacked: true, grid: { color: chartColors.grid }, ticks: { font: { size: 11 } } },
          x: { stacked: true, grid: { display: false }, ticks: { font: { size: 11 } } }
        }
      }
    });

    // ============================================================
    // SUB-AGENTS FUNCTIONALITY
    // ============================================================

    // Load sub-agent status
    async function loadSubAgentStatus() {
      try {
        const resp = await fetch('/api/subagents');
        const data = await resp.json();
        if (data.data) {
          data.data.forEach(agent => {
            if (agent.id === 'content-repurposer') {
              document.getElementById('repurposer-produced').textContent = agent.stats.items_produced || 0;
              document.getElementById('repurposer-notes').textContent = agent.stats.style_notes || 0;
            } else if (agent.id === 'analytics-digest') {
              document.getElementById('analytics-tracked').textContent = agent.stats.tracked_accounts || 0;
              document.getElementById('analytics-digests').textContent = agent.stats.digests_produced || 0;
            } else if (agent.id === 'content-creator') {
              document.getElementById('creator-drafts').textContent = agent.stats.drafts_produced || 0;
              document.getElementById('creator-approved').textContent = agent.stats.approved || 0;
              document.getElementById('creator-level').textContent = agent.stats.delegation_level || 1;
            }
          });
        }
      } catch (e) { console.log('Sub-agent status load error:', e); }
    }

    // Repurpose Modal
    function openRepurposeModal() {
      document.getElementById('repurpose-modal').style.display = 'flex';
      document.getElementById('repurpose-results').style.display = 'none';
    }
    function closeRepurposeModal() {
      document.getElementById('repurpose-modal').style.display = 'none';
    }
    async function submitRepurpose(e) {
      e.preventDefault();
      const btn = document.getElementById('repurpose-submit');
      btn.textContent = 'Generating...'; btn.disabled = true;
      try {
        const resp = await fetch('/api/subagents/content-repurposer/repurpose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_content: document.getElementById('repurpose-content').value,
            source_platform: document.getElementById('repurpose-source').value,
            context: document.getElementById('repurpose-context').value,
          })
        });
        const data = await resp.json();
        const resultsDiv = document.getElementById('repurpose-results');
        if (data.success && data.results) {
          let html = '<div class="sa-result"><h4>Repurposed Content</h4>';
          data.results.forEach(r => {
            html += '<div class="sa-slide">';
            html += '<div class="sa-slide-num">' + (r.platform || 'Output') + ' — ' + (r.content_type || '') + '</div>';
            if (r.headline) html += '<div class="sa-slide-headline">' + r.headline + '</div>';
            html += '<div class="sa-slide-body">' + (r.body || r.content || JSON.stringify(r)).replace(/\n/g, '<br>') + '</div>';
            if (r.cta) html += '<div class="sa-slide-visual">CTA: ' + r.cta + '</div>';
            if (r.hashtags && r.hashtags.length) html += '<div class="sa-slide-visual">' + r.hashtags.map(h => '#' + h).join(' ') + '</div>';
            html += '</div>';
          });
          html += '</div>';
          resultsDiv.innerHTML = html;
        } else {
          resultsDiv.innerHTML = '<div class="sa-result"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
        }
        resultsDiv.style.display = 'block';
        loadSubAgentStatus();
      } catch (err) {
        document.getElementById('repurpose-results').innerHTML = '<div class="sa-result"><pre>Error: ' + err.message + '</pre></div>';
        document.getElementById('repurpose-results').style.display = 'block';
      }
      btn.textContent = 'Repurpose'; btn.disabled = false;
    }

    // Carousel Modal
    function openCarouselModal() {
      document.getElementById('carousel-modal').style.display = 'flex';
      document.getElementById('carousel-results').style.display = 'none';
    }
    function closeCarouselModal() {
      document.getElementById('carousel-modal').style.display = 'none';
    }
    async function submitCarousel(e) {
      e.preventDefault();
      const btn = document.getElementById('carousel-submit');
      btn.textContent = 'Creating...'; btn.disabled = true;
      try {
        const resp = await fetch('/api/subagents/content-creator/create_carousel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic: document.getElementById('carousel-topic').value,
            platform: document.getElementById('carousel-platform').value,
            slides: parseInt(document.getElementById('carousel-slides').value),
            reference_content: document.getElementById('carousel-reference').value,
          })
        });
        const data = await resp.json();
        const resultsDiv = document.getElementById('carousel-results');
        if (data.success && data.carousel) {
          const c = data.carousel.carousel || data.carousel;
          let html = '<div class="sa-result">';
          html += '<h4>Carousel Draft — ' + (c.topic || data.carousel.topic || '') + '</h4>';
          html += '<div style="font-size:12px;color:var(--text-muted);margin-bottom:12px">Draft ID: ' + data.draft_id + ' | Status: ' + data.status + '</div>';
          if (c.slides) {
            c.slides.forEach(s => {
              html += '<div class="sa-slide">';
              html += '<div class="sa-slide-num">Slide ' + s.slide_number + ' — ' + (s.type || 'content') + '</div>';
              html += '<div class="sa-slide-headline">' + (s.headline || '') + '</div>';
              if (s.body) html += '<div class="sa-slide-body">' + s.body.replace(/\n/g, '<br>') + '</div>';
              if (s.subtext) html += '<div class="sa-slide-body">' + s.subtext + '</div>';
              if (s.visual_direction) html += '<div class="sa-slide-visual">Visual: ' + s.visual_direction + '</div>';
              html += '</div>';
            });
          }
          if (c.caption) {
            html += '<div class="sa-slide"><div class="sa-slide-num">Caption</div>';
            html += '<div class="sa-slide-body">' + c.caption.replace(/\n/g, '<br>') + '</div></div>';
          }
          html += '</div>';
          resultsDiv.innerHTML = html;
        } else {
          resultsDiv.innerHTML = '<div class="sa-result"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
        }
        resultsDiv.style.display = 'block';
        loadSubAgentStatus();
      } catch (err) {
        document.getElementById('carousel-results').innerHTML = '<div class="sa-result"><pre>Error: ' + err.message + '</pre></div>';
        document.getElementById('carousel-results').style.display = 'block';
      }
      btn.textContent = 'Create Draft'; btn.disabled = false;
    }

    // Analytics Digest
    async function generateDigest() {
      const btn = event.target;
      btn.textContent = 'Generating...'; btn.disabled = true;
      try {
        const resp = await fetch('/api/subagents/analytics-digest/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ days: 7 })
        });
        const data = await resp.json();
        if (data.success && data.digest) {
          const d = data.digest;
          let msg = 'Weekly Digest Generated!\n\n';
          msg += 'Summary: ' + (d.summary || 'See details below') + '\n\n';
          if (d.recommendations) {
            msg += 'Recommendations:\n';
            d.recommendations.forEach((r, i) => {
              msg += (i + 1) + '. ' + (typeof r === 'string' ? r : JSON.stringify(r)) + '\n';
            });
          }
          alert(msg);
        } else {
          alert('Digest generation: ' + JSON.stringify(data));
        }
        loadSubAgentStatus();
      } catch (err) { alert('Error: ' + err.message); }
      btn.textContent = 'Generate Digest'; btn.disabled = false;
    }

    // Tracked Accounts Modal
    function openTrackedAccountsModal() {
      document.getElementById('accounts-modal').style.display = 'flex';
      loadTrackedAccounts();
    }
    function closeAccountsModal() {
      document.getElementById('accounts-modal').style.display = 'none';
    }
    async function loadTrackedAccounts() {
      try {
        const resp = await fetch('/api/subagents/analytics-digest/accounts');
        const data = await resp.json();
        const list = document.getElementById('accounts-list');
        if (data.data && data.data.length > 0) {
          list.innerHTML = data.data.map(a =>
            '<div class="tracked-account">' +
            '<span class="ta-platform">' + a.platform + '</span>' +
            '<span class="ta-handle">@' + a.handle + '</span>' +
            '<span class="ta-category">' + a.category + '</span>' +
            '<span class="ta-remove" onclick="removeTrackedAccount(\'' + a.platform + '\',\'' + a.handle + '\')">&times;</span>' +
            '</div>'
          ).join('');
        } else {
          list.innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:13px">No accounts tracked yet. Add competitor and inspiration accounts below.</div>';
        }
      } catch (e) { console.log('Load tracked accounts error:', e); }
    }
    async function addTrackedAccount(e) {
      e.preventDefault();
      const handle = document.getElementById('account-handle').value.replace('@', '');
      await fetch('/api/subagents/analytics-digest/accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: document.getElementById('account-platform').value,
          handle: handle,
          category: document.getElementById('account-category').value,
        })
      });
      document.getElementById('account-handle').value = '';
      loadTrackedAccounts();
      loadSubAgentStatus();
    }
    async function removeTrackedAccount(platform, handle) {
      await fetch('/api/subagents/analytics-digest/accounts', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform, handle })
      });
      loadTrackedAccounts();
      loadSubAgentStatus();
    }

    // Load sub-agent status on page load
    loadSubAgentStatus();

    // ===== DAILY PLANNER =====
    let plannerDate = new Date();
    plannerDate.setHours(0,0,0,0);

    function fmtPlannerDate(d) {
      const opts = { weekday:'long', year:'numeric', month:'long', day:'numeric' };
      const today = new Date(); today.setHours(0,0,0,0);
      const diff = (d - today) / 86400000;
      if (diff === 0) return 'Today \u2014 ' + d.toLocaleDateString('en-US', opts);
      if (diff === 1) return 'Tomorrow \u2014 ' + d.toLocaleDateString('en-US', opts);
      if (diff === -1) return 'Yesterday \u2014 ' + d.toLocaleDateString('en-US', opts);
      return d.toLocaleDateString('en-US', opts);
    }

    function dateKey(d) {
      return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
    }

    function plannerPrevDay() { plannerDate.setDate(plannerDate.getDate()-1); loadPlanner(); }
    function plannerNextDay() { plannerDate.setDate(plannerDate.getDate()+1); loadPlanner(); }
    function plannerToday() { plannerDate = new Date(); plannerDate.setHours(0,0,0,0); loadPlanner(); }

    function buildTimeGrid() {
      const grid = document.getElementById('planner-time-grid');
      grid.innerHTML = '';
      for (let h = 6; h <= 21; h++) {
        for (let m = 0; m < 60; m += 30) {
          const time = String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0');
          const slot = document.createElement('div');
          slot.className = 'planner-slot';
          slot.dataset.time = time;
          const timeDiv = document.createElement('div');
          timeDiv.className = 'planner-slot-time';
          timeDiv.textContent = time;
          const contentDiv = document.createElement('div');
          contentDiv.className = 'planner-slot-content';
          const inp = document.createElement('input');
          inp.className = 'planner-slot-input';
          inp.placeholder = 'Click to add...';
          inp.dataset.time = time;
          inp.addEventListener('focus', function(){ this.placeholder = ''; });
          inp.addEventListener('blur', function(){ savePlannerSlot(this); });
          const catSelect = document.createElement('select');
          catSelect.className = 'planner-cat-select';
          catSelect.dataset.time = time;
          const defOpt = document.createElement('option');
          defOpt.value = 'general';
          defOpt.textContent = '--';
          catSelect.appendChild(defOpt);
          if (window._plannerCategories) {
            window._plannerCategories.forEach(function(c) {
              const opt = document.createElement('option');
              opt.value = c.id;
              opt.textContent = c.label;
              catSelect.appendChild(opt);
            });
          }
          catSelect.addEventListener('change', function(){ updateSlotCategory(this); });
          const removeBtn = document.createElement('button');
          removeBtn.className = 'planner-slot-remove';
          removeBtn.innerHTML = '&times;';
          removeBtn.title = 'Clear';
          removeBtn.addEventListener('click', function(){ clearPlannerSlot(this); });
          contentDiv.appendChild(inp);
          contentDiv.appendChild(catSelect);
          contentDiv.appendChild(removeBtn);
          slot.appendChild(timeDiv);
          slot.appendChild(contentDiv);
          grid.appendChild(slot);
        }
      }
    }

    async function loadPlanner() {
      document.getElementById('planner-date-label').textContent = fmtPlannerDate(plannerDate);
      const dk = dateKey(plannerDate);
      try {
        const res = await fetch('/api/planner/' + dk);
        const data = await res.json();
        document.querySelectorAll('.planner-slot').forEach(function(slot) {
          const inp = slot.querySelector('.planner-slot-input');
          const catSel = slot.querySelector('.planner-cat-select');
          const removeBtn = slot.querySelector('.planner-slot-remove');
          inp.value = '';
          inp.placeholder = 'Click to add...';
          removeBtn.style.display = 'none';
          slot.classList.remove('has-task');
          slot.removeAttribute('data-category');
          if (catSel) catSel.value = 'general';
        });
        if (data.slots) {
          Object.entries(data.slots).forEach(function([time, val]) {
            var task, category;
            if (typeof val === 'object' && val !== null) {
              task = val.task || '';
              category = val.category || 'general';
            } else {
              task = val || '';
              category = 'general';
            }
            const inp = document.querySelector('.planner-slot-input[data-time="' + time + '"]');
            if (inp && task) {
              const slot = inp.closest('.planner-slot');
              inp.value = task;
              slot.classList.add('has-task');
              slot.dataset.category = category;
              inp.parentElement.querySelector('.planner-slot-remove').style.display = '';
              const catSel = inp.parentElement.querySelector('.planner-cat-select');
              if (catSel) catSel.value = category;
            }
          });
        }
        renderPriorities(data.priorities || {});
        renderImportantTasks(data.tasks || []);
        highlightCurrentSlot();
      } catch(e) { console.log('Planner load skipped:', e); }
    }

    function highlightCurrentSlot() {
      const now = new Date();
      const today = new Date(); today.setHours(0,0,0,0);
      if (plannerDate.getTime() !== today.getTime()) return;
      const currentTime = String(now.getHours()).padStart(2,'0') + ':' + (now.getMinutes() < 30 ? '00' : '30');
      document.querySelectorAll('.planner-slot').forEach(s => {
        s.style.background = s.dataset.time === currentTime ? 'var(--accent-subtle)' : '';
      });
    }

    async function savePlannerSlot(inp) {
      inp.placeholder = 'Click to add...';
      const time = inp.dataset.time;
      const task = inp.value.trim();
      const dk = dateKey(plannerDate);
      const slot = inp.closest('.planner-slot');
      const catSel = inp.parentElement.querySelector('.planner-cat-select');
      const category = catSel ? catSel.value : 'general';
      inp.parentElement.querySelector('.planner-slot-remove').style.display = task ? '' : 'none';
      if (task) { slot.classList.add('has-task'); } else { slot.classList.remove('has-task'); slot.removeAttribute('data-category'); }
      try {
        await fetch('/api/planner/' + dk + '/slot', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ time, task, category })
        });
      } catch(e) {}
    }

    async function updateSlotCategory(sel) {
      const time = sel.dataset.time;
      const category = sel.value;
      const slot = sel.closest('.planner-slot');
      slot.dataset.category = category;
      const inp = slot.querySelector('.planner-slot-input');
      const task = inp.value.trim();
      if (!task) return;
      const dk = dateKey(plannerDate);
      try {
        await fetch('/api/planner/' + dk + '/slot', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ time, task, category })
        });
      } catch(e) {}
    }

    async function clearPlannerSlot(btn) {
      const inp = btn.parentElement.querySelector('.planner-slot-input');
      inp.value = '';
      btn.style.display = 'none';
      const slot = inp.closest('.planner-slot');
      slot.classList.remove('has-task');
      slot.removeAttribute('data-category');
      await savePlannerSlot(inp);
    }

    function renderImportantTasks(tasks) {
      const container = document.getElementById('planner-tasks');
      container.innerHTML = tasks.map((t, i) =>
        '<div class="task-item">' +
        '<div class="task-check ' + (t.done ? 'checked' : '') + '" onclick="togglePlannerTask(' + i + ')"></div>' +
        '<div class="task-text ' + (t.done ? 'done' : '') + '">' + escapeHtml(t.text) + '</div>' +
        '</div>'
      ).join('') || '<div style="color:var(--text-muted);font-size:12px;padding:4px 0;">No tasks yet</div>';
    }

    async function togglePlannerTask(index) {
      const dk = dateKey(plannerDate);
      try { await fetch('/api/planner/' + dk + '/task/' + index + '/toggle', { method: 'POST' }); loadPlanner(); } catch(e) {}
    }

    async function addImportantTask() {
      const inp = document.getElementById('add-task-input');
      const text = inp.value.trim();
      if (!text) return;
      inp.value = '';
      const dk = dateKey(plannerDate);
      try {
        await fetch('/api/planner/' + dk + '/task', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        loadPlanner();
      } catch(e) {}
    }

    function planWithImani() {
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      document.querySelector('[data-panel="chat"]').classList.add('active');
      document.getElementById('panel-chat').classList.add('active');
      const chatInput = document.getElementById('chat-input');
      chatInput.value = "Let's plan my day. What do I have coming up and what should I prioritize today?";
      chatInput.focus();
    }

    window._plannerCategories = [];
    const defaultCatColors = ['#E74C3C','#3498DB','#ECF0F1','#27AE60','#2ECC71','#E91E63','#FFC107','#5DADE2','#F0B27A','#9B59B6','#1ABC9C','#E67E22'];

    async function loadCategories() {
      try {
        const res = await fetch('/api/planner/categories');
        const data = await res.json();
        window._plannerCategories = data.categories || [];
        buildTimeGrid();
        updateCategoryCSS();
      } catch(e) { console.log('Categories load failed:', e); }
    }

    function updateCategoryCSS() {
      var style = document.getElementById('dynamic-cat-css');
      if (!style) { style = document.createElement('style'); style.id = 'dynamic-cat-css'; document.head.appendChild(style); }
      var css = '';
      window._plannerCategories.forEach(function(c) {
        css += '.planner-slot[data-category="' + c.id + '"] { border-left-color:' + c.color + '; }\n';
      });
      style.textContent = css;
    }

    function renderPriorities(savedPriorities) {
      const container = document.getElementById('planner-priorities');
      container.innerHTML = '';
      var cats = window._plannerCategories;
      if (!cats || cats.length === 0) return;
      cats.forEach(function(cat) {
        var item = document.createElement('div');
        item.className = 'priority-item';
        item.dataset.catId = cat.id;
        var colorDot = document.createElement('input');
        colorDot.type = 'color';
        colorDot.className = 'pri-color-dot';
        colorDot.value = cat.color;
        colorDot.title = 'Change color';
        colorDot.style.cssText = 'width:24px;height:24px;padding:0;border:none;cursor:pointer;background:transparent;';
        colorDot.addEventListener('change', function() { cat.color = this.value; saveCategories(); updateCategoryCSS(); });
        var textDiv = document.createElement('div');
        textDiv.style.flex = '1';
        var labelInp = document.createElement('input');
        labelInp.className = 'pri-edit-label';
        labelInp.value = cat.label;
        labelInp.addEventListener('blur', function() { cat.label = this.value.trim(); saveCategories(); });
        var valInp = document.createElement('input');
        valInp.className = 'pri-edit-value';
        valInp.placeholder = 'Today\u2019s focus...';
        valInp.value = savedPriorities[cat.id] || '';
        valInp.addEventListener('blur', function() { savePriority(cat.id, this.value.trim()); });
        textDiv.appendChild(labelInp);
        textDiv.appendChild(valInp);
        var removeBtn = document.createElement('button');
        removeBtn.className = 'pri-remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.title = 'Remove category';
        removeBtn.addEventListener('click', function() {
          window._plannerCategories = window._plannerCategories.filter(function(c) { return c.id !== cat.id; });
          saveCategories();
          loadPlanner();
        });
        item.appendChild(colorDot);
        item.appendChild(textDiv);
        item.appendChild(removeBtn);
        container.appendChild(item);
      });
      var addBtn = document.createElement('button');
      addBtn.className = 'pri-add-btn';
      addBtn.textContent = '+ Add Category';
      addBtn.addEventListener('click', function() {
        var newId = 'cat_' + Date.now();
        var colorIdx = window._plannerCategories.length % defaultCatColors.length;
        window._plannerCategories.push({ id: newId, label: 'New Category', color: defaultCatColors[colorIdx], sort_order: window._plannerCategories.length });
        saveCategories();
        loadPlanner();
      });
      container.appendChild(addBtn);
    }

    async function saveCategories() {
      try {
        await fetch('/api/planner/categories', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ categories: window._plannerCategories })
        });
        buildTimeGrid();
        updateCategoryCSS();
      } catch(e) {}
    }

    async function savePriority(catId, value) {
      var dk = dateKey(plannerDate);
      try {
        await fetch('/api/planner/' + dk + '/priority', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ category: catId, value: value })
        });
      } catch(e) {}
    }

    loadCategories().then(function() { loadPlanner(); });
    setInterval(highlightCurrentSlot, 60000);

    // ===== ROUTINES =====
    const defaultRoutines = {
      morning: ['Prayer / Meditation', 'Journaling', 'Exercise', 'Healthy Breakfast', 'Review Day Plan'],
      afternoon: ['Lunch Break (no screen)', 'Networking Calls/DMs', 'Personal Development Reading', 'Hydration Check'],
      night: ['Evening Reflection', 'Gratitude Journal', 'Prepare Tomorrow', 'Screen Off by 10pm', 'Skincare Routine']
    };

    async function loadRoutines() {
      const dk = dateKey(new Date());
      try {
        const res = await fetch('/api/routines/' + dk);
        const data = await res.json();
        ['morning', 'afternoon', 'night'].forEach(period => {
          const items = data[period] || [];
          renderRoutineItems(period, items);
        });
        loadStreak();
      } catch(e) {
        ['morning', 'afternoon', 'night'].forEach(period => {
          renderRoutineItems(period, defaultRoutines[period].map(name => ({name, done: false})));
        });
      }
    }

    function renderRoutineItems(period, items) {
      const container = document.getElementById('routine-' + period + '-items');
      container.innerHTML = '';
      items.forEach((item, i) => {
        const name = typeof item === 'string' ? item : item.name;
        const done = typeof item === 'object' ? item.done : false;
        const div = document.createElement('div');
        div.className = 'routine-item';
        const check = document.createElement('div');
        check.className = 'routine-check' + (done ? ' checked' : '');
        check.addEventListener('click', function() { toggleRoutine(period, i); });
        const label = document.createElement('div');
        label.className = 'routine-check-label' + (done ? ' done' : '');
        label.textContent = name;
        div.appendChild(check);
        div.appendChild(label);
        container.appendChild(div);
      });
      const total = items.length;
      const checked = items.filter(it => typeof it === 'object' ? it.done : false).length;
      const pct = total > 0 ? Math.round(checked / total * 100) : 0;
      document.getElementById('routine-' + period + '-bar').style.width = pct + '%';
      document.getElementById('routine-' + period + '-pct').textContent = pct + '% complete';
    }

    async function toggleRoutine(period, index) {
      const dk = dateKey(new Date());
      try { await fetch('/api/routines/' + dk + '/' + period + '/' + index + '/toggle', { method: 'POST' }); loadRoutines(); } catch(e) {}
    }

    async function addRoutineItem(period) {
      const inp = document.getElementById('routine-' + period + '-input');
      const name = inp.value.trim();
      if (!name) return;
      inp.value = '';
      const dk = dateKey(new Date());
      try {
        await fetch('/api/routines/' + dk + '/' + period, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name })
        });
        loadRoutines();
      } catch(e) {}
    }

    async function loadStreak() {
      try {
        const res = await fetch('/api/routines/streak');
        const data = await res.json();
        const container = document.getElementById('streak-dots');
        container.innerHTML = (data.days || []).map(d =>
          '<div class="streak-dot ' + (d.pct >= 80 ? 'done' : d.pct > 0 ? 'partial' : '') + '" title="' + d.date + ': ' + d.pct + '%"></div>'
        ).join('');
      } catch(e) {}
    }

    loadRoutines();
  </script>

<button class="mobile-menu-btn" id="mobileMenuBtn">&#9776;</button>
<div class="mobile-menu-overlay" id="mobileMenuOverlay"></div>
<script>
(function() {
  var btn = document.getElementById('mobileMenuBtn');
  var overlay = document.getElementById('mobileMenuOverlay');
  var sidebar = document.querySelector('.sidebar');
  if (!btn || !sidebar) return;
  function openMenu() { sidebar.classList.add('open'); overlay.classList.add('active'); }
  function closeMenu() { sidebar.classList.remove('open'); overlay.classList.remove('active'); }
  btn.addEventListener('click', function() { sidebar.classList.contains('open') ? closeMenu() : openMenu(); });
  overlay.addEventListener('click', closeMenu);
  sidebar.addEventListener('click', function(e) {
    if (window.innerWidth <= 768 && (e.target.tagName === 'A' || e.target.closest('a') || e.target.closest('.nav-item'))) {
      closeMenu();
    }
  });
})();
</script>
</body>
</html>"""


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
# Web Dashboard V2 + Chat API
# ============================================================
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the Imani V2 dashboard."""
    return DASHBOARD_HTML


@app.get("/messages")
async def get_messages(limit: int = 50):
    """Return recent conversation history for the web UI."""
    messages = memory.get_recent_messages(limit=limit)
    return {"messages": messages}


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
    return {
        "status": "alive",
        "agent": "Imani",
        "phase": "Phase 3: Live Analytics",
        "tools": {
            "calendar": "connected" if calendar.is_connected() else "not configured",
            "sheets": "connected" if sheets.is_connected() else "not configured",
            "whatsapp": "configured" if os.getenv("TWILIO_ACCOUNT_SID") else "not configured",
            "voice": "configured" if os.getenv("OPENAI_API_KEY") else "not configured",
            "metricool": "connected" if metricool.is_connected() else "not configured",
        },
        "sheets_service_account": sheets.get_service_account_email() if sheets.is_connected() else None,
        "sheets_config": {
            "calendar_sheet_id": CALENDAR_SHEET_ID[:8] + "..." if CALENDAR_SHEET_ID else "not set",
            "tracker_sheet_id": TRACKER_SHEET_ID[:8] + "..." if TRACKER_SHEET_ID else "not set",
        },
    }


# ============================================================
# Metricool Analytics API (serves live data to the dashboard)
# ============================================================
@app.get("/api/overview")
async def api_overview(days: int = 7):
    """Dashboard overview: aggregations + timeline + recent posts for all platforms."""
    if not metricool.is_connected():
        return {"error": "Metricool not configured", "data": None}
    data = await metricool.dashboard_overview(days=days)
    return {"data": data}


@app.get("/api/platform/{platform}")
async def api_platform(platform: str, days: int = 30):
    """Detailed data for a single platform page."""
    if not metricool.is_connected():
        return {"error": "Metricool not configured", "data": None}
    if platform not in ("instagram", "twitter", "tiktok", "youtube", "linkedin"):
        return {"error": "Unknown platform", "data": None}
    data = await metricool.platform_detail(platform, days=days)
    return {"data": data}


@app.get("/api/calendar")
async def api_calendar(platform: str = None):
    """Serve upcoming content from the Google Sheets brand calendar."""
    if not sheets.is_connected():
        return {"error": "Google Sheets not configured", "data": []}
    try:
        items = sheets.get_upcoming_content(platform=platform)
        # Normalize items into dashboard-friendly format
        formatted = []
        for item in items:
            formatted.append({
                "day": item.get("day", ""),
                "date": item.get("date", ""),
                "day_of_week": item.get("day of week", "") or item.get("day_of_week", ""),
                "channel": item.get("channel", "") or item.get("platform", ""),
                "content_type": item.get("content type", "") or item.get("content_type", "") or item.get("format", ""),
                "title": item.get("title/topic", "") or item.get("title", "") or item.get("topic", ""),
                "hook": item.get("hook/angle", "") or item.get("hook", ""),
                "cta": item.get("cta", ""),
                "status": item.get("status", "planned"),
                "notes": item.get("notes", ""),
            })
        return {"data": formatted}
    except Exception as e:
        logger.error("Calendar API error: %s", e)
        return {"error": str(e), "data": []}


# ------------------------------------------------------------------
# Calendar Sync — Match Metricool published posts to calendar entries
# ------------------------------------------------------------------

@app.post("/api/calendar/sync")
async def api_calendar_sync():
    """Sync published posts from Metricool back to the calendar sheet.
    Matches by date and platform, updates status to 'Published'."""
    if not sheets.is_connected() or not metricool.is_connected():
        return {"error": "Sheets or Metricool not configured", "synced": 0}

    try:
        # Get all calendar items
        calendar_items = sheets.get_full_calendar()
        if not calendar_items:
            return {"synced": 0, "message": "No calendar items found"}

        # Get recent posts from all platforms (last 30 days)
        ig_posts = await metricool.instagram_posts(days=30)
        ig_reels = await metricool.instagram_reels(days=30)
        tw_posts = await metricool.twitter_posts(days=30)
        li_posts = await metricool.linkedin_posts(days=30)
        yt_posts = await metricool.youtube_posts(days=30)

        # Build a set of published dates per platform
        published = {}
        for post in (ig_posts or []) + (ig_reels or []):
            pub = post.get("published") or post.get("created") or post.get("date")
            if pub:
                date_str = _format_sync_date(pub)
                if date_str:
                    published.setdefault("instagram", set()).add(date_str)

        for post in (tw_posts or []):
            pub = post.get("created") or post.get("published") or post.get("date")
            if pub:
                date_str = _format_sync_date(pub)
                if date_str:
                    published.setdefault("twitter", set()).add(date_str)

        for post in (li_posts or []):
            pub = post.get("published") or post.get("created") or post.get("date")
            if pub:
                date_str = _format_sync_date(pub)
                if date_str:
                    published.setdefault("linkedin", set()).add(date_str)

        for post in (yt_posts or []):
            pub = post.get("published") or post.get("created") or post.get("date")
            if pub:
                date_str = _format_sync_date(pub)
                if date_str:
                    published.setdefault("youtube", set()).add(date_str)

        # Match calendar items and update status
        synced = 0
        for item in calendar_items:
            status = (item.get("status", "") or "").lower().strip()
            if status in ("published", "posted", "done"):
                continue  # Already marked

            cal_date = (item.get("date", "") or "").strip()
            channel = (item.get("primary channel", "") or item.get("channel", "") or item.get("platform", "")).lower().strip()
            row_num = item.get("_row")

            if not cal_date or not row_num:
                continue

            # Check if this platform has a published post on this date
            for platform, dates in published.items():
                if platform in channel and cal_date in dates:
                    sheets.update_calendar_status(row_num - 1, "Published")
                    synced += 1
                    break

        return {"synced": synced, "message": f"Updated {synced} calendar entries to Published"}
    except Exception as e:
        logger.error("Calendar sync error: %s", e)
        return {"error": str(e), "synced": 0}


def _format_sync_date(raw) -> str:
    """Convert Metricool date formats to match calendar date format (e.g. 'Mar 25')."""
    if not raw:
        return ""
    try:
        if isinstance(raw, (int, float)):
            ts = raw / 1000 if raw > 1e12 else raw
            dt = datetime.utcfromtimestamp(ts)
        elif isinstance(raw, str):
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y%m%d"):
                try:
                    dt = datetime.strptime(raw[:19], fmt)
                    break
                except ValueError:
                    continue
            else:
                return ""
        else:
            return ""
        return dt.strftime("%b %d").replace(" 0", " ")  # "Mar 5" not "Mar 05"
    except Exception:
        return ""


# ------------------------------------------------------------------
# Daily Planner & Routine Tracker — SQLite persistence
# ------------------------------------------------------------------

PLANNER_DB = os.getenv("PLANNER_DB_PATH", "planner.db")


def _planner_db():
    conn = sqlite3.connect(PLANNER_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS planner_slots (date TEXT, time TEXT, task TEXT, category TEXT DEFAULT 'general', PRIMARY KEY(date, time))")
    conn.execute("CREATE TABLE IF NOT EXISTS planner_categories (id TEXT PRIMARY KEY, label TEXT, color TEXT, sort_order INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS planner_tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, text TEXT, done INTEGER DEFAULT 0, sort_order INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS planner_priorities (date TEXT, category TEXT, value TEXT, PRIMARY KEY(date, category))")
    conn.execute("CREATE TABLE IF NOT EXISTS routine_templates (period TEXT, name TEXT, sort_order INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS routine_checks (date TEXT, period TEXT, item_index INTEGER, done INTEGER DEFAULT 0, name TEXT, PRIMARY KEY(date, period, item_index))")
    conn.execute("CREATE TABLE IF NOT EXISTS audit_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, date TEXT, task TEXT, category TEXT, energy_before INTEGER, energy_after INTEGER, feeling TEXT, focus_level TEXT, requires_me TEXT, could_delegate TEXT, could_automate TEXT, interruptions TEXT, trigger_reason TEXT, notes TEXT)")
    conn.row_factory = sqlite3.Row
    return conn


def _init_routine_defaults(conn, date_str, period):
    existing = conn.execute("SELECT COUNT(*) FROM routine_checks WHERE date=? AND period=?", (date_str, period)).fetchone()[0]
    if existing > 0:
        return
    templates = conn.execute("SELECT name, sort_order FROM routine_templates WHERE period=? ORDER BY sort_order", (period,)).fetchall()
    if templates:
        for i, t in enumerate(templates):
            conn.execute("INSERT INTO routine_checks (date, period, item_index, done, name) VALUES (?,?,?,0,?)", (date_str, period, i, t["name"]))
    else:
        defaults = {
            "morning": ["Prayer / Meditation", "Journaling", "Exercise", "Healthy Breakfast", "Review Day Plan"],
            "afternoon": ["Lunch Break (no screen)", "Networking Calls/DMs", "Personal Development Reading", "Hydration Check"],
            "night": ["Evening Reflection", "Gratitude Journal", "Prepare Tomorrow", "Screen Off by 10pm", "Skincare Routine"]
        }
        for i, name in enumerate(defaults.get(period, [])):
            conn.execute("INSERT INTO routine_checks (date, period, item_index, done, name) VALUES (?,?,?,0,?)", (date_str, period, i, name))
    conn.commit()



@app.get("/api/planner/categories")
async def api_get_categories():
    conn = _planner_db()
    cats = []
    for row in conn.execute("SELECT id, label, color, sort_order FROM planner_categories ORDER BY sort_order, id"):
        cats.append({"id": row["id"], "label": row["label"], "color": row["color"], "sort_order": row["sort_order"]})
    conn.close()
    if not cats:
        cats = [
            {"id": "stamfordham", "label": "Stamfordham Global", "color": "#E74C3C", "sort_order": 0},
            {"id": "bddm", "label": "BDDM Collective", "color": "#3498DB", "sort_order": 1},
            {"id": "spiritual", "label": "Spiritual / Personal Growth", "color": "#ECF0F1", "sort_order": 2},
            {"id": "impact", "label": "Impact", "color": "#27AE60", "sort_order": 3},
            {"id": "brand", "label": "My Brand", "color": "#2ECC71", "sort_order": 4},
            {"id": "financial", "label": "Financial & Property", "color": "#E91E63", "sort_order": 5},
            {"id": "health", "label": "Health & Self-care", "color": "#FFC107", "sort_order": 6},
            {"id": "career", "label": "Career & Professional", "color": "#5DADE2", "sort_order": 7},
            {"id": "proficio", "label": "Proficio", "color": "#F0B27A", "sort_order": 8},
        ]
    return {"categories": cats}


@app.post("/api/planner/categories")
async def api_save_categories(request: Request):
    body = await request.json()
    cats = body.get("categories", [])
    conn = _planner_db()
    conn.execute("DELETE FROM planner_categories")
    for i, c in enumerate(cats):
        conn.execute("INSERT INTO planner_categories (id, label, color, sort_order) VALUES (?,?,?,?)",
                     (c.get("id", ""), c.get("label", ""), c.get("color", "#888"), i))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/planner/{date}")
async def api_get_planner(date: str):
    conn = _planner_db()
    slots = {}
    for row in conn.execute("SELECT time, task, category FROM planner_slots WHERE date=?", (date,)):
        slots[row["time"]] = {"task": row["task"], "category": row["category"] or "general"}
    priorities = {}
    for row in conn.execute("SELECT category, value FROM planner_priorities WHERE date=?", (date,)):
        priorities[row["category"]] = row["value"]
    tasks = []
    for row in conn.execute("SELECT id, text, done FROM planner_tasks WHERE date=? ORDER BY sort_order, id", (date,)):
        tasks.append({"id": row["id"], "text": row["text"], "done": bool(row["done"])})
    conn.close()
    return {"date": date, "slots": slots, "priorities": priorities, "tasks": tasks}


@app.post("/api/planner/{date}/slot")
async def api_set_planner_slot(date: str, request: Request):
    body = await request.json()
    time = body.get("time", "")
    task = body.get("task", "").strip()
    category = body.get("category", "general")
    conn = _planner_db()
    if task:
        conn.execute("INSERT OR REPLACE INTO planner_slots (date, time, task, category) VALUES (?,?,?,?)", (date, time, task, category))
    else:
        conn.execute("DELETE FROM planner_slots WHERE date=? AND time=?", (date, time))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/planner/{date}/task")
async def api_add_planner_task(date: str, request: Request):
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        return {"error": "empty text"}
    conn = _planner_db()
    conn.execute("INSERT INTO planner_tasks (date, text, done) VALUES (?,?,0)", (date, text))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/planner/{date}/task/{index}/toggle")
async def api_toggle_planner_task(date: str, index: int):
    conn = _planner_db()
    tasks = conn.execute("SELECT id, done FROM planner_tasks WHERE date=? ORDER BY sort_order, id", (date,)).fetchall()
    if 0 <= index < len(tasks):
        tid = tasks[index]["id"]
        new_done = 0 if tasks[index]["done"] else 1
        conn.execute("UPDATE planner_tasks SET done=? WHERE id=?", (new_done, tid))
        conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/planner/{date}/priority")
async def api_set_priority(date: str, request: Request):
    body = await request.json()
    category = body.get("category", "")
    value = body.get("value", "")
    conn = _planner_db()
    conn.execute("INSERT OR REPLACE INTO planner_priorities (date, category, value) VALUES (?,?,?)", (date, category, value))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/planner/{date}/bulk")
async def api_bulk_planner(date: str, request: Request):
    body = await request.json()
    conn = _planner_db()
    if "slots" in body:
        for time, val in body["slots"].items():
            if isinstance(val, dict):
                task = val.get("task", "").strip()
                category = val.get("category", "general")
            else:
                task = str(val).strip() if val else ""
                category = "general"
            if task:
                conn.execute("INSERT OR REPLACE INTO planner_slots (date, time, task, category) VALUES (?,?,?,?)", (date, time, task, category))
            else:
                conn.execute("DELETE FROM planner_slots WHERE date=? AND time=?", (date, time))
    if "priorities" in body:
        for cat, val in body["priorities"].items():
            conn.execute("INSERT OR REPLACE INTO planner_priorities (date, category, value) VALUES (?,?,?)", (date, cat, val))
    if "tasks" in body:
        for t in body["tasks"]:
            conn.execute("INSERT INTO planner_tasks (date, text, done) VALUES (?,?,0)", (date, t))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/audit/log")
async def api_log_audit(request: Request):
    body = await request.json()
    conn = _planner_db()
    from datetime import datetime as _dt
    ts = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    date = body.get("date", _dt.now().strftime("%Y-%m-%d"))
    conn.execute(
        "INSERT INTO audit_entries (timestamp, date, task, category, energy_before, energy_after, feeling, focus_level, requires_me, could_delegate, could_automate, interruptions, trigger_reason, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ts, date, body.get("task",""), body.get("category",""), body.get("energy_before"), body.get("energy_after"), body.get("feeling",""), body.get("focus_level",""), body.get("requires_me",""), body.get("could_delegate",""), body.get("could_automate",""), body.get("interruptions",""), body.get("trigger",""), body.get("notes",""))
    )
    conn.commit()
    entry_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"ok": True, "id": entry_id, "timestamp": ts}


@app.get("/api/audit/entries")
async def api_get_audit_entries(date: str = None):
    conn = _planner_db()
    if date:
        rows = conn.execute("SELECT * FROM audit_entries WHERE date=? ORDER BY timestamp", (date,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_entries ORDER BY timestamp DESC LIMIT 200").fetchall()
    entries = [dict(r) for r in rows]
    conn.close()
    return {"entries": entries}


@app.get("/api/audit/summary")
async def api_get_audit_summary():
    conn = _planner_db()
    total = conn.execute("SELECT COUNT(*) FROM audit_entries").fetchone()[0]
    by_category = [dict(r) for r in conn.execute("SELECT category, COUNT(*) as count, AVG(energy_before) as avg_energy_before, AVG(energy_after) as avg_energy_after FROM audit_entries GROUP BY category ORDER BY count DESC").fetchall()]
    by_feeling = [dict(r) for r in conn.execute("SELECT feeling, COUNT(*) as count FROM audit_entries GROUP BY feeling ORDER BY count DESC").fetchall()]
    by_date = [dict(r) for r in conn.execute("SELECT date, COUNT(*) as count FROM audit_entries GROUP BY date ORDER BY date").fetchall()]
    conn.close()
    return {"total": total, "by_category": by_category, "by_feeling": by_feeling, "by_date": by_date}


@app.get("/api/routines/{date}")
async def api_get_routines(date: str):
    conn = _planner_db()
    result = {}
    for period in ["morning", "afternoon", "night"]:
        _init_routine_defaults(conn, date, period)
        items = conn.execute("SELECT name, done FROM routine_checks WHERE date=? AND period=? ORDER BY item_index", (date, period)).fetchall()
        result[period] = [{"name": r["name"], "done": bool(r["done"])} for r in items]
    conn.close()
    return result


@app.post("/api/routines/{date}/{period}/{index}/toggle")
async def api_toggle_routine(date: str, period: str, index: int):
    conn = _planner_db()
    _init_routine_defaults(conn, date, period)
    row = conn.execute("SELECT done FROM routine_checks WHERE date=? AND period=? AND item_index=?", (date, period, index)).fetchone()
    if row:
        conn.execute("UPDATE routine_checks SET done=? WHERE date=? AND period=? AND item_index=?", (0 if row["done"] else 1, date, period, index))
        conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/routines/{date}/{period}")
async def api_add_routine_item(date: str, period: str, request: Request):
    body = await request.json()
    name = body.get("name", "").strip()
    if not name:
        return {"error": "empty"}
    conn = _planner_db()
    _init_routine_defaults(conn, date, period)
    max_idx = conn.execute("SELECT MAX(item_index) FROM routine_checks WHERE date=? AND period=?", (date, period)).fetchone()[0] or 0
    new_idx = max_idx + 1
    conn.execute("INSERT INTO routine_checks (date, period, item_index, done, name) VALUES (?,?,?,0,?)", (date, period, new_idx, name))
    tmpl_count = conn.execute("SELECT COUNT(*) FROM routine_templates WHERE period=? AND name=?", (period, name)).fetchone()[0]
    if not tmpl_count:
        tmpl_max = conn.execute("SELECT MAX(sort_order) FROM routine_templates WHERE period=?", (period,)).fetchone()[0] or 0
        conn.execute("INSERT INTO routine_templates (period, name, sort_order) VALUES (?,?,?)", (period, name, tmpl_max + 1))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/routines/streak")
async def api_routine_streak():
    conn = _planner_db()
    days = []
    today = datetime.now().date()
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        dk = d.isoformat()
        total = conn.execute("SELECT COUNT(*) FROM routine_checks WHERE date=?", (dk,)).fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM routine_checks WHERE date=? AND done=1", (dk,)).fetchone()[0]
        pct = round(done / total * 100) if total > 0 else 0
        days.append({"date": dk, "pct": pct})
    conn.close()
    return {"days": days}


# ------------------------------------------------------------------
# Sub-Agent API Endpoints
# ------------------------------------------------------------------

@app.get("/api/subagents")
async def api_subagents():
    """List all sub-agents and their status."""
    return {"data": subagent_mgr.list_agents()}


@app.post("/api/subagents/{agent_id}/{action}")
async def api_subagent_action(agent_id: str, action: str, request: Request):
    """Dispatch an action to a sub-agent."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    result = await subagent_mgr.dispatch(agent_id, action, body)
    return result


@app.get("/api/subagents/analytics-digest/accounts")
async def api_tracked_accounts():
    """List tracked competitor/inspiration accounts."""
    return {"data": subagent_mgr.analytics.list_accounts()}


@app.post("/api/subagents/analytics-digest/accounts")
async def api_add_tracked_account(request: Request):
    """Add a tracked account."""
    body = await request.json()
    result = subagent_mgr.analytics.add_account(
        platform=body.get("platform", ""),
        handle=body.get("handle", ""),
        category=body.get("category", "inspiration"),
    )
    return result


@app.delete("/api/subagents/analytics-digest/accounts")
async def api_remove_tracked_account(request: Request):
    """Remove a tracked account."""
    body = await request.json()
    result = subagent_mgr.analytics.remove_account(
        platform=body.get("platform", ""),
        handle=body.get("handle", ""),
    )
    return result
