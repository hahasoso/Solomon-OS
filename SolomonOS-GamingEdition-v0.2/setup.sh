#!/usr/bin/env bash
# Install the Solomon OS desktop hub on an existing Debian/Ubuntu/Linux Mint desktop.
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$(id -u)" -eq 0 ]; then
  echo "Run this script as your normal desktop user (not with sudo)." >&2
  exit 1
fi
if ! command -v apt-get >/dev/null; then
  echo "This installer currently supports Debian, Ubuntu and Linux Mint only." >&2
  exit 1
fi
if ! command -v sudo >/dev/null; then
  echo "Please install sudo or have an administrator install flatpak and python3-tk." >&2
  exit 1
fi
echo "Installing Flatpak, tkinter and desktop dependencies..."
sudo apt-get update
sudo apt-get install -y flatpak python3 python3-tk xdg-utils ca-certificates
INSTALL_DIR="$HOME/.local/share/solomon-os/app"
mkdir -p "$INSTALL_DIR/demo" "$HOME/.local/share/applications"
install -m 0644 "$SCRIPT_DIR/app/solomon_hub.py" "$INSTALL_DIR/solomon_hub.py"
install -m 0644 "$SCRIPT_DIR/app/game_library.py" "$INSTALL_DIR/game_library.py"
install -m 0644 "$SCRIPT_DIR/demo/redder7-training.html" "$INSTALL_DIR/demo/redder7-training.html"
cat > "$HOME/.local/share/applications/solomon-os.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Solomon OS Gaming Hub
Comment=Manage Steam, emulators and Redder7 games
Exec=python3 $INSTALL_DIR/solomon_hub.py
Terminal=false
Icon=applications-games
Categories=Game;
EOF
flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
printf '\nInstalled Solomon OS Gaming Hub.\nLaunch from the applications menu, or run:\n  python3 %s/solomon_hub.py\n' "$INSTALL_DIR"
echo 'Steam, emulators and game runtimes are installed separately from the Hub as you choose.'
