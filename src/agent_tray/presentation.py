from __future__ import annotations

import html

from agent_tray.i18n import COLOR_SYMBOLS, STATUS_COLORS, SYMBOLS, status_text, text
from agent_tray.models import SessionStatus
from agent_tray.service import SessionView


TOOL_COLORS = {
    "codex": "#3584e4",
    "claude": "#9141ac",
}


def shorten(value: str, limit: int) -> str:
    cleaned = " ".join((value or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: max(1, limit - 3)].rstrip() + "..."


def session_location(session: SessionView) -> str:
    if session.source_host:
        return f"{shorten(session.source_host, 10)}:{shorten(session.project, 12)}"
    return shorten(session.project, 16)


def tool_label(tool: str) -> str:
    return text("tool_claude") if tool == "claude" else text("tool_codex")


def session_row(session: SessionView) -> str:
    return (
        f"{COLOR_SYMBOLS[session.status]} {status_text(session.status)} · "
        f"[{tool_label(session.tool)}] {session_location(session)} — {shorten(session.title, 12)}"
    )


def session_row_markup(session: SessionView) -> str:
    """Readable GTK markup with separate status and tool accents."""
    status = html.escape(f"{SYMBOLS[session.status]} {status_text(session.status)}")
    tool = html.escape(f"[{tool_label(session.tool)}]")
    location = html.escape(session_location(session))
    title = html.escape(shorten(session.title, 18))
    status_color = STATUS_COLORS[session.status]
    tool_color = TOOL_COLORS.get(session.tool, TOOL_COLORS["codex"])
    return (
        f'<span foreground="{status_color}"><b>{status}</b></span>  '
        f'<span foreground="{tool_color}"><b>{tool}</b></span>  '
        f'<b>{location}</b> — {title}'
    )


def status_summary(sessions: list[SessionView]) -> str:
    values = {status: 0 for status in STATUS_COLORS}
    for session in sessions:
        values[session.status] += 1
    parts = [
        f"{SYMBOLS[status]}{values[status]}"
        for status in (SessionStatus.WORKING, SessionStatus.ATTENTION, SessionStatus.DONE)
        if values[status]
    ]
    return " ".join(parts) if parts else "0"


def tool_summary(sessions: list[SessionView]) -> str:
    codex = sum(session.tool != "claude" for session in sessions)
    claude = sum(session.tool == "claude" for session in sessions)
    return f"{text('tool_codex')} {codex} · {text('tool_claude')} {claude}"


def summary_text(sessions: list[SessionView]) -> str:
    codex = sum(session.tool != "claude" for session in sessions)
    claude = sum(session.tool == "claude" for session in sessions)
    return text("summary").format(total=len(sessions), codex=codex, claude=claude)
