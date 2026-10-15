#!/usr/bin/env bash
# Build Solomon OS Gaming Edition as a Debian 13 x86_64 Live ISO.
# Requires a Debian/Ubuntu x86_64 host with internet and sudo/root.
set -Eeuo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
OUT="${OUTPUT_DIR:-$ROOT/output}"
WORK="${WORK_DIR:-$ROOT/.iso-work}"
if [ "$(id -u)" -ne 0 ]; then
    echo 'Run with sudo: sudo ./iso/build-iso.sh' >&2
    exit 1
fi
if [ "$(uname -m)" != 'x86_64' ]; then
    echo 'This version only builds an x86-64 PC ISO.' >&2; exit 1
fi
for cmd in lb debootstrap mksquashfs xorriso; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing $cmd. Installing the ISO build requirements..."
    apt-get update
    apt-get install -y live-build debootstrap debian-archive-keyring squashfs-tools xorriso isolinux syslinux-common grub-pc-bin grub-efi-amd64-bin
    break
  fi
done
mkdir -p "$WORK" "$OUT"
cd "$WORK"
# 'lb config' writes its settings, then we add our custom files into config/.
lb config \
    --distribution trixie \
    --architectures amd64 \
    --binary-image iso-hybrid \
    --bootloaders 'syslinux grub-efi' \
    --debian-installer none \
    --archive-areas 'main contrib non-free-firmware' \
    --bootappend-live 'boot=live components locales=en_US.UTF-8 keyboard-layouts=us' \
    --iso-application 'Solomon OS Gaming Edition 0.2' \
    --iso-publisher 'Solomon OS Community Project'
mkdir -p config/package-lists config/includes.chroot/usr/local/share/solomon-os/app/demo \
    config/includes.chroot/usr/local/bin config/includes.chroot/usr/share/applications \
    config/includes.chroot/etc/skel/.config/autostart \
    config/includes.chroot/etc/skel/Desktop
cp "$HERE/packages.list.chroot" config/package-lists/gaming.list.chroot
cp "$ROOT/app/solomon_hub.py" config/includes.chroot/usr/local/share/solomon-os/app/solomon_hub.py
cp "$ROOT/app/game_library.py" config/includes.chroot/usr/local/share/solomon-os/app/game_library.py
cp "$ROOT/demo/redder7-training.html" config/includes.chroot/usr/local/share/solomon-os/app/demo/redder7-training.html
cp "$HERE/solomon-hub" config/includes.chroot/usr/local/bin/solomon-hub
chmod +x config/includes.chroot/usr/local/bin/solomon-hub
cp "$HERE/solomon-os.desktop" config/includes.chroot/usr/share/applications/solomon-os.desktop
cp "$HERE/solomon-os.desktop" config/includes.chroot/etc/skel/Desktop/solomon-os.desktop
cp "$HERE/solomon-os.desktop" config/includes.chroot/etc/skel/.config/autostart/solomon-os.desktop
chmod +x config/includes.chroot/etc/skel/Desktop/solomon-os.desktop
printf 'solomon-gaming\n' > config/includes.chroot/etc/hostname
# apt repositories accessed ONLY from the builder; no paid or copyrighted games included.
lb build
FILE="$(find . -maxdepth 1 -type f \( -name '*.iso' -o -name '*.hybrid.iso' \) | head -1)"
if [ -z "$FILE" ]; then echo 'Build finished, but no ISO was found.' >&2; exit 1; fi
cp "$FILE" "$OUT/SolomonOS-GamingEdition-v0.2-amd64.iso"
sha256sum "$OUT/SolomonOS-GamingEdition-v0.2-amd64.iso" > "$OUT/SolomonOS-GamingEdition-v0.2-amd64.iso.sha256"
echo "ISO created: $OUT/SolomonOS-GamingEdition-v0.2-amd64.iso"
