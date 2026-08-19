from __future__ import annotations

import logging
import sys

from agent_tray.runtime import InstanceLock, configure_logging


LOG = logging.getLogger(__name__)


def run() -> int:
    configure_logging()
    lock = InstanceLock()
    if not lock.acquire():
        LOG.info("Another AgentTray instance is already running")
        return 0
    try:
        if sys.platform.startswith("linux"):
            try:
                from agent_tray.linux_indicator import LinuxIndicatorApp

                return LinuxIndicatorApp().run()
            except (ImportError, ValueError) as error:
                LOG.warning("Native AppIndicator unavailable, trying portable tray: %s", error)
        from agent_tray.portable_tray import PortableTrayApp

        return PortableTrayApp().run()
    except Exception:
        LOG.exception("AgentTray terminated unexpectedly")
        return 1
    finally:
        lock.release()
