#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
VERSION=${1:-1.0.0}
ARCH=${2:-$(dpkg --print-architecture)}
BUILD_ROOT=${PROJECT_ROOT}/build/deb
PACKAGE_ROOT=${BUILD_ROOT}/agent-tray_${VERSION}_${ARCH}
OUTPUT=${PROJECT_ROOT}/dist/agent-tray_${VERSION}_${ARCH}.deb

rm -rf "$BUILD_ROOT"
install -d \
    "$PACKAGE_ROOT/DEBIAN" \
    "$PACKAGE_ROOT/usr/bin" \
    "$PACKAGE_ROOT/usr/lib/agent-tray" \
    "$PACKAGE_ROOT/usr/share/applications" \
    "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps" \
    "$PROJECT_ROOT/dist"

cp -R "$PROJECT_ROOT/src/agent_tray" "$PACKAGE_ROOT/usr/lib/agent-tray/"
find "$PACKAGE_ROOT/usr/lib/agent-tray" -type f -name '*.pyc' -delete
find "$PACKAGE_ROOT/usr/lib/agent-tray" -type d -name '__pycache__' -empty -delete

{
    printf '%s\n' 'Package: agent-tray'
    printf 'Version: %s\n' "$VERSION"
    printf 'Architecture: %s\n' "$ARCH"
    printf '%s\n' 'Maintainer: Heimao-c'
    printf '%s\n' 'Depends: python3 (>= 3.10), python3-gi, gir1.2-gtk-3.0, gir1.2-ayatanaappindicator3-0.1, gir1.2-atspi-2.0, libayatana-appindicator3-1, libx11-6, libxtst6, x11-utils'
    printf '%s\n' 'Section: devel'
    printf '%s\n' 'Priority: optional'
    printf '%s\n' 'Homepage: https://github.com/Heimao-c/agent-tray'
    printf '%s\n' 'Description: System-tray manager for local and SSH Codex CLI and Claude Code CLI sessions'
    printf '%s\n' ' Shows state, project, and conversation title without storing prompts or replies.'
} > "$PACKAGE_ROOT/DEBIAN/control"

{
    printf '%s\n' '#!/bin/sh'
    printf '%s\n' 'AGENT_TRAY_LAUNCHER=/usr/bin/agent-tray PYTHONPATH=/usr/lib/agent-tray exec /usr/bin/python3 -m agent_tray "$@"'
} > "$PACKAGE_ROOT/usr/bin/agent-tray"
chmod 0755 "$PACKAGE_ROOT/usr/bin/agent-tray"

{
    printf '%s\n' '[Desktop Entry]'
    printf '%s\n' 'Type=Application'
    printf '%s\n' 'Name=AgentTray'
    printf '%s\n' 'Exec=agent-tray'
    printf '%s\n' 'Icon=agent-tray-symbolic'
    printf '%s\n' 'Terminal=false'
    printf '%s\n' 'Categories=Development;Utility;'
    printf '%s\n' 'Comment=Show and manage Codex and Claude CLI session status'
} > "$PACKAGE_ROOT/usr/share/applications/agent-tray.desktop"

for icon in "$PROJECT_ROOT"/src/agent_tray/assets/*.svg; do
    install -m 0644 "$icon" \
        "$PACKAGE_ROOT/usr/share/icons/hicolor/scalable/apps/$(basename "$icon")"
done

dpkg-deb --root-owner-group --build "$PACKAGE_ROOT" "$OUTPUT"
printf '%s\n' "$OUTPUT"
