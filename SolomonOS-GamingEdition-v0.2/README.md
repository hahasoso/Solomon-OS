# Solomon OS — Gaming Edition v0.2

**Status: working Linux gaming launcher + Debian 13 Live ISO build source.**

This ZIP does **not** contain a finished Linux ISO. The source was assembled and the import logic was tested, but a full ISO was **not built or VM-boot-tested** in the development environment because the Debian package servers were unreachable. The provided ISO builder needs a Debian/Ubuntu Linux computer with internet, or the included GitHub Actions workflow.

## What is included

- **Solomon Gaming Hub**: graphical app with a game library and launch/install buttons.
- **Steam + Proton path**: Flatpak Steam; enable Steam Play in Steam Settings > Compatibility after installation.
- **RetroArch**: classic console emulator frontend. You must add your own legally obtained game files.
- **Heroic**, **Lutris**, **Bottles**, **ProtonUp-Qt**: installable from Flathub with buttons in the hub.
- **Redder7 game installer**: imports an existing local `.html` or a `.zip` containing an HTML game and its assets, then runs it in your browser.
- **Redder7: Training Arena (demo)**: small playable original browser game you can install with one click; NOT the full Redder7 game.
- **Debian-based ISO build script** and **GitHub Actions workflow** to produce a bootable **x86-64 live** Linux desktop image.

No Mario, Sonic, FNAF, Windows games, commercial ROMs, BIOS files, copyrighted artwork, Steam accounts or paid software are distributed in this ZIP. You must install or supply your own legally acquired games. Game compatibility is not guaranteed. Some games require native Windows and won't run under Proton.

## Option A — Install the gaming hub on an existing Linux desktop (easiest way to keep game installs)

Supports Debian, Ubuntu, and Linux Mint, with an internet connection:

```sh
unzip SolomonOS-GamingEdition-v0.2.zip
cd SolomonOS-GamingEdition-v0.2
bash setup.sh
```

The script installs Flatpak and Python/Tk dependencies from your distro's repositories, installs the launcher into `~/.local/share/solomon-os/`, and creates an applications-menu shortcut named **Solomon OS Gaming Hub**. It does **not** replace your existing OS.

You can also start it without installing it, provided `python3-tk` is available:

```sh
./run-hub.sh
```

Inside the hub, click **Install** next to Steam, RetroArch, Heroic, etc. The hub then fetches the official Flatpak software from Flathub (internet required). These are launchers, not the paid games themselves.

### Getting real games working

**Steam/FNAF/compatible PC games:** install Steam, sign into your Steam account, enable Steam Play for other titles under **Steam > Settings > Compatibility**, select a suitable Proton version and install a game you own. Proton depends on your graphics driver and game compatibility. Some games may be unavailable on ARM-based computers or blocked by anti-cheat.

**Mario/Sonic classic games:** install RetroArch, download compatible emulator cores, and import your own legally obtained game dumps. Don't distribute ROMs or copyrighted data.

**Redder7:** use **My games > Install Redder7 game** and select an HTML file or ZIP containing an HTML game's entry page (ideally `index.html`). The installer copies it safely into `~/.local/share/solomon-os/games/`. If no build is available yet, use **Install demo** for a small original game.

### Demo controls

- Move: arrow keys or WASD
- Shoot: spacebar
- Pause/resume: P

## Option B — Build a bootable Solomon OS Linux ISO

This creates a **Debian 13 (Trixie) XFCE live desktop ISO**, with the Solomon Hub and browser included. Steam and other game platforms are *not preinstalled*; install them with the launcher once booted and online. The ISO must fetch multiple gigabytes of official Debian packages during its build.

**Important: the live ISO is NOT a hard-drive installer.** Its changes, including games installed while running the ISO, will disappear after reboot unless you set up persistence. For games that stay installed, use Option A with a normal installed Linux distro. Running graphics-intensive PC games inside VirtualBox usually performs poorly or fails due to limited graphics acceleration.

### Build it on a Linux computer

From inside the extracted directory:

```sh
sudo bash iso/build-iso.sh
```

The script installs `live-build`, `debootstrap`, `xorriso`, and bootloader dependencies if absent; then creates an output directory with:

`output/SolomonOS-GamingEdition-v0.2-amd64.iso`

`output/SolomonOS-GamingEdition-v0.2-amd64.iso.sha256`

Required: x86-64 Debian/Ubuntu, sudo, functioning internet, and enough free disk space (plan on 15–20 GB). The build is UNTESTED end-to-end in this environment, so if the package mirror changes a dependency the script may need updating.

### Build it using GitHub Actions (without a Linux PC)

1. Create a **new GitHub repository** and upload **the contents** of this ZIP folder to the root of the repository, including `.github/workflows/build-iso.yml`.
2. In the GitHub repository, open **Actions** > **Build Solomon OS Gaming Edition ISO**.
3. Choose **Run workflow** and wait for the job to finish. Building a desktop image can take a while and needs sufficient GitHub Actions storage/quota.
4. Download the workflow's **SolomonOS-GamingEdition-v0.2** artifact ZIP and extract the actual `*.iso` file.
5. Attach the ISO to an x86-64 VM (VirtualBox/VMware/QEMU) and boot in Legacy BIOS mode first. An ARM Mac cannot natively run this x86-64 ISO without x86 emulation.

GitHub Actions creation/build success is not guaranteed without a build test, but the pipeline is supplied to make the OS practical to build with network access.

## Folder layout

- `app/solomon_hub.py` — graphical launcher (Tkinter)
- `app/game_library.py` — HTML/ZIP importer, local game database
- `demo/redder7-training.html` — playable demo
- `setup.sh` — setup on an *installed* Linux desktop
- `iso/build-iso.sh` — Debian Live ISO builder
- `iso/packages.list.chroot` — Debian packages inside the ISO
- `.github/workflows/build-iso.yml` — hosted ISO build automation
- `tests/` — ZIP/game-library tests

## Test the importer

```sh
python3 -m unittest discover -s tests -v
python3 app/solomon_hub.py --help
```

## Safety and architecture

- Base: **Debian GNU/Linux**; not an official Debian release, and not affiliated with Valve, Nintendo, Sega or Scott Cawthon.
- The **original 16-bit Solomon OS v0.1 ISO is not compatible** with Linux or Steam. This is a *separate* Linux build and new game launcher.
- ZIP imports reject `../` directory traversal and symlink entries, and limit decompressed size. Still, run only games you trust; HTML can contain executable JavaScript.
- Booting an OS from an ISO is different from permanently installing it to disk. **Back up important files before repartitioning or writing USB devices.** No disk-writing or partitioning commands are included in this project.
