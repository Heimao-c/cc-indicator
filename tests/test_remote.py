import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_tray.models import SessionStatus
from agent_tray.remote import (
    LinuxRemoteScanner,
    REMOTE_CLAUDE_TOGGLE,
    RemoteSession,
    SshConnection,
    _socket_source_port,
    ssh_target,
)


class RemoteScannerTests(unittest.TestCase):
    def test_ignores_its_own_probe_ssh_process(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            process = root / "1234"
            (process / "fd").mkdir(parents=True)
            (process / "comm").write_text("ssh\n", encoding="utf-8")
            (process / "fd" / "0").symlink_to("/dev/null")
            command = b"ssh\0-T\0robot\0python3 -c '# AGENT_TRAY_REMOTE_PROBE'\0"
            (process / "cmdline").write_bytes(command)
            self.assertEqual(LinuxRemoteScanner(root).connections(), [])

    def test_claude_toggle_targets_only_hosts_with_claude_settings(self) -> None:
        scanner = LinuxRemoteScanner()
        scanner._claude_info = {
            "codex-only": {"exists": False, "bypass": False},
            "claude-host": {"exists": True, "bypass": False},
        }
        self.assertEqual(scanner.claude_hosts(), ["claude-host"])

    def test_disconnected_hosts_are_removed_from_claude_state(self) -> None:
        scanner = LinuxRemoteScanner()
        scanner._claude_info = {"gone": {"exists": True, "bypass": True}}
        scanner.connections = lambda: []  # type: ignore[method-assign]
        scanner._probe = lambda _host, _connections: []  # type: ignore[method-assign]
        scanner.discover(force=True)
        self.assertEqual(scanner.claude_hosts(), [])

    def test_deduplicates_ssh_aliases_by_remote_thread_id(self) -> None:
        scanner = LinuxRemoteScanner()
        scanner.connections = lambda: [  # type: ignore[method-assign]
            SshConnection("interactive-alias", "/dev/pts/0"),
            SshConnection("reverse-alias", "unknown"),
        ]

        def probe(host: str, _connections: list[SshConnection]) -> list[RemoteSession]:
            local_tty = "/dev/pts/0" if host == "interactive-alias" else "unknown"
            return [
                RemoteSession(
                    session_id="same-thread",
                    pid=123,
                    cwd="/workspace",
                    terminal_id=f"SSH:{local_tty}:{host}:pts/2",
                    status=SessionStatus.WORKING,
                    updated_at=10,
                    title="thread",
                    project="workspace",
                    host=host,
                )
            ]

        scanner._probe = probe  # type: ignore[method-assign]
        sessions = scanner.discover(force=True)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].host, "interactive-alias")

    def test_extracts_ssh_alias_after_options(self) -> None:
        self.assertEqual(
            ssh_target(["ssh", "-p", "2222", "-o", "BatchMode=yes", "robot-server"]),
            "robot-server",
        )

    def test_extracts_user_at_host(self) -> None:
        self.assertEqual(ssh_target(["/usr/bin/ssh", "root@10.0.0.2"]), "root@10.0.0.2")

    def test_reads_ssh_source_port_from_process_socket(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            process = Path(temp) / "123"
            (process / "fd").mkdir(parents=True)
            (process / "net").mkdir()
            (process / "fd" / "3").symlink_to("socket:[45678]")
            header = "sl local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode"
            row = "0: 0100007F:CFAE 0100007F:0016 01 0:0 0:0 0 1000 0 45678"
            (process / "net" / "tcp").write_text(f"{header}\n{row}\n", encoding="utf-8")
            self.assertEqual(_socket_source_port(process), 0xCFAE)

    @staticmethod
    def _run_toggle(settings_dir: Path, *args: str) -> None:
        environment = dict(os.environ, CLAUDE_CONFIG_DIR=str(settings_dir))
        subprocess.run(
            ["python3", "-c", REMOTE_CLAUDE_TOGGLE, *args],
            check=True,
            capture_output=True,
            env=environment,
        )

    def test_remote_toggle_script_sets_and_removes_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            settings_dir = Path(temp) / "claude-cc"
            settings = settings_dir / "settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(
                json.dumps(
                    {
                        "env": {"ANTHROPIC_AUTH_TOKEN": "sk-test"},
                        "permissions": {"defaultMode": "acceptEdits", "deny": ["Bash(rm -rf /)"]},
                    }
                ),
                encoding="utf-8",
            )

            self._run_toggle(settings_dir, "on")
            document = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(document["permissions"]["defaultMode"], "bypassPermissions")
            self.assertEqual(document["permissions"]["deny"], ["Bash(rm -rf /)"])
            self.assertEqual(document["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-test")

            self._run_toggle(settings_dir, "off")
            document = json.loads(settings.read_text(encoding="utf-8"))
            self.assertNotIn("defaultMode", document["permissions"])
            self.assertEqual(document["permissions"]["deny"], ["Bash(rm -rf /)"])
            self.assertEqual(document["env"]["ANTHROPIC_AUTH_TOKEN"], "sk-test")

    def test_remote_toggle_script_creates_missing_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            settings_dir = Path(temp) / "claude-cc"
            self._run_toggle(settings_dir, "on")
            document = json.loads((settings_dir / "settings.json").read_text(encoding="utf-8"))
            self.assertEqual(document["permissions"]["defaultMode"], "bypassPermissions")
            self._run_toggle(settings_dir, "off")
            document = json.loads((settings_dir / "settings.json").read_text(encoding="utf-8"))
            self.assertNotIn("permissions", document)
