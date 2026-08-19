#!/bin/sh
set -eu

DATA_HOME=${XDG_DATA_HOME:-"$HOME/.local/share"}
BIN_PATH=${HOME}/.local/bin/agent-tray

if [ -x "$BIN_PATH" ]; then
    "$BIN_PATH" --uninstall-hooks || true
    if [ -f "$HOME/.config/systemd/user/agent-tray.service" ]; then
        systemctl --user stop agent-tray.service || true
    fi
    "$BIN_PATH" --uninstall-autostart || true
fi

rm -f "$BIN_PATH"
rm -f "$DATA_HOME/applications/agent-tray.desktop"
for icon in symbolic attention working done idle; do
    rm -f "$DATA_HOME/icons/hicolor/scalable/apps/agent-tray-${icon}.svg"
done
rm -rf "$DATA_HOME/agent-tray"

printf '%s\n' 'AgentTray was removed. Session-status cache was kept in the platform state directory.'
