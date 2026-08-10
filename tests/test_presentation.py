import unittest

from cc_indicator.models import SessionStatus
from cc_indicator.presentation import session_row, session_row_markup, shorten, summary_text
from cc_indicator.service import SessionView


class PresentationTests(unittest.TestCase):
    def test_uses_three_dots_for_long_names(self) -> None:
        self.assertEqual(shorten("123456789", 8), "12345...")

    def test_remote_row_is_short_and_identifies_host(self) -> None:
        session = SessionView(
            session_id="ssh:host:id",
            thread_id="id",
            status=SessionStatus.WORKING,
            project="robot-project",
            title="很长的对话名称" * 20,
            cwd="/root/robot-project",
            updated_at=1,
            source_host="robot-server",
        )
        row = session_row(session)
        self.assertIn("robot-s...:robot-pro...", row)
        self.assertTrue(row.endswith("..."))
        self.assertLess(len(row), 90)

    def test_row_marks_the_tool(self) -> None:
        session = SessionView(
            session_id="claude-1",
            thread_id="claude-1",
            status=SessionStatus.DONE,
            project="robot-project",
            title="short",
            cwd="/workspace",
            updated_at=1,
            tool="claude",
        )
        self.assertIn("[Claude]", session_row(session))
        codex = SessionView(
            session_id="codex-1",
            thread_id="codex-1",
            status=SessionStatus.DONE,
            project="robot-project",
            title="short",
            cwd="/workspace",
            updated_at=1,
        )
        self.assertIn("[Codex]", session_row(codex))

    def test_markup_separates_status_and_tool_accents(self) -> None:
        session = SessionView(
            session_id="codex-1",
            thread_id="codex-1",
            status=SessionStatus.ATTENTION,
            project="zotero",
            title="approve this",
            cwd="/workspace",
            updated_at=1,
        )
        markup = session_row_markup(session)
        self.assertIn("#e5a50a", markup)
        self.assertIn("[Codex]", markup)

    def test_summary_counts_both_tools(self) -> None:
        sessions = [
            SessionView("c1", "c1", SessionStatus.WORKING, "one", "one", "/one", 1),
            SessionView("c2", "c2", SessionStatus.DONE, "two", "two", "/two", 1, tool="claude"),
        ]
        self.assertIn("Codex 1", summary_text(sessions))
        self.assertIn("Claude 1", summary_text(sessions))
