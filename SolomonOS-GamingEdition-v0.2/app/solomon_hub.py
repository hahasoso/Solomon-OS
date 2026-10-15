#!/usr/bin/env python3
"""Solomon OS gaming launcher, install tools and local Redder7 HTML games."""
from __future__ import annotations
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
from game_library import DATA_DIR, install_html_game, installed_games, remove_game

APPS = [
    ('Steam', 'com.valvesoftware.Steam', 'PC games and Proton compatibility'),
    ('RetroArch', 'org.libretro.RetroArch', 'Classic game emulator frontend'),
    ('Heroic', 'com.heroicgameslauncher.hgl', 'Epic / GOG / Amazon games'),
    ('Lutris', 'net.lutris.Lutris', 'Game library and compatibility runners'),
    ('Bottles', 'com.usebottles.bottles', 'Run supported Windows game installers'),
    ('ProtonUp-Qt', 'net.davidotek.pupgui2', 'Manage community Proton builds'),
]
DARK = '#11131b'
PANEL = '#1c202c'
TEXT = '#f5f5f7'
MUTED = '#a7abb7'
ORANGE = '#ff922b'
BORDER = '#383c4b'


def flatpak_installed(app_id: str) -> bool:
    if not shutil.which('flatpak'):
        return False
    for mode in ('--user', '--system'):
        if subprocess.run(['flatpak', 'info', mode, app_id], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, check=False).returncode == 0:
            return True
    return False


class Hub:
    def __init__(self, root):
        self.root = root
        root.title('Solomon OS — Gaming Edition')
        root.geometry('980x720')
        root.minsize(680, 520)
        root.configure(bg=DARK)
        self.messages = queue.Queue()
        self.busy = False
        header = tk.Frame(root, bg=DARK)
        header.pack(fill='x', padx=26, pady=(24, 8))
        tk.Label(header, text='SOLOMON OS', fg=ORANGE, bg=DARK, font=('DejaVu Sans', 23, 'bold')).pack(side='left')
        tk.Label(header, text='GAMING EDITION  /  0.2', fg=MUTED, bg=DARK,
                 font=('DejaVu Sans', 10)).pack(side='left', padx=15, pady=(12, 0))
        tk.Label(root, text='Your games. Your computer. Install compatible game launchers below.',
                 fg=MUTED, bg=DARK, font=('DejaVu Sans', 11)).pack(anchor='w', padx=28, pady=(0, 14))
        nav = tk.Frame(root, bg=DARK)
        nav.pack(fill='x', padx=24)
        self.content = tk.Frame(root, bg=DARK)
        self.content.pack(fill='both', expand=True, padx=25, pady=14)
        for label, handler in [('Game platforms', self.show_platforms),
                               ('My games', self.show_games), ('Help', self.show_help)]:
            self.button(nav, label, handler, colored=False).pack(side='left', padx=(0, 9))
        self.status = tk.StringVar(value='Ready. Internet is required to install Steam or emulators.')
        tk.Label(root, textvariable=self.status, fg=MUTED, bg=DARK,
                 anchor='w', font=('DejaVu Sans', 9), wraplength=900).pack(fill='x', padx=26, pady=(0, 8))
        self.show_platforms()
        self.root.after(150, self.drain_queue)

    def button(self, parent, text, command, colored=True):
        return tk.Button(parent, text=text, command=command, relief='flat', cursor='hand2',
                         bg=ORANGE if colored else PANEL, fg='#171717' if colored else TEXT,
                         activebackground='#ffb166' if colored else BORDER, borderwidth=0,
                         padx=17, pady=10, font=('DejaVu Sans', 10, 'bold'))

    def section(self, title, note):
        for widget in self.content.winfo_children():
            widget.destroy()
        tk.Label(self.content, text=title, font=('DejaVu Sans', 19, 'bold'),
                 bg=DARK, fg=TEXT).pack(anchor='w', pady=(5, 3))
        tk.Label(self.content, text=note, bg=DARK, fg=MUTED, wraplength=850,
                 justify='left', font=('DejaVu Sans', 10)).pack(anchor='w', pady=(0, 16))

    def show_platforms(self):
        self.section('Game platforms', 'Install official launcher software through Flathub. Games are NOT included.')
        for name, appid, note in APPS:
            block = tk.Frame(self.content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
            block.pack(fill='x', pady=4)
            left = tk.Frame(block, bg=PANEL)
            left.pack(side='left', fill='both', expand=True, padx=16, pady=9)
            tk.Label(left, text=name, bg=PANEL, fg=TEXT, font=('DejaVu Sans', 12, 'bold')).pack(anchor='w')
            tk.Label(left, text=note, bg=PANEL, fg=MUTED, font=('DejaVu Sans', 9)).pack(anchor='w')
            installed = flatpak_installed(appid)
            self.button(block, 'Open' if installed else 'Install',
                        lambda app=appid, ready=installed: self.launch_app(app) if ready else self.install_app(app),
                        colored=not installed).pack(side='right', padx=14)

    def install_app(self, app_id):
        if self.busy:
            messagebox.showinfo('Solomon OS', 'An installation is already running.')
            return
        if not shutil.which('flatpak'):
            messagebox.showerror('Flatpak missing', 'Install Flatpak first. See README/setup.sh.')
            return
        self.busy = True
        self.status.set(f'Installing {app_id} from Flathub. This can take several minutes...')
        def work():
            commands = [
                ['flatpak', 'remote-add', '--user', '--if-not-exists', 'flathub',
                 'https://flathub.org/repo/flathub.flatpakrepo'],
                ['flatpak', 'install', '--user', '--noninteractive', '-y', 'flathub', app_id]
            ]
            try:
                for cmd in commands:
                    outcome = subprocess.run(cmd, text=True, capture_output=True, timeout=3600,
                                             check=False)
                    if outcome.returncode:
                        detail = (outcome.stderr or outcome.stdout)[-1700:]
                        self.messages.put(('error', f'Installation failed:\n{detail}'))
                        return
                self.messages.put(('success', f'{app_id} installed successfully.'))
            except (OSError, subprocess.TimeoutExpired) as exc:
                self.messages.put(('error', str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def launch_app(self, app_id):
        try:
            subprocess.Popen(['flatpak', 'run', app_id], start_new_session=True)
            self.status.set(f'Opened {app_id}')
        except OSError as exc:
            messagebox.showerror('Unable to launch', str(exc))

    def drain_queue(self):
        try:
            while True:
                kind, message = self.messages.get_nowait()
                self.busy = False
                self.status.set(message.splitlines()[0])
                if kind == 'error':
                    messagebox.showerror('Install failed', message)
                self.show_platforms()
        except queue.Empty:
            pass
        self.root.after(200, self.drain_queue)

    def show_games(self):
        self.section('My installed games', 'Import a game you own as .html or a .zip containing HTML game files.')
        nav = tk.Frame(self.content, bg=DARK)
        nav.pack(fill='x', pady=(0, 10))
        self.button(nav, 'Install Redder7 game', self.import_redder7).pack(side='left', padx=(0, 8))
        self.button(nav, 'Install another HTML game', self.import_any, colored=False).pack(side='left', padx=(0, 8))
        self.button(nav, 'Install demo', self.install_demo, colored=False).pack(side='left', padx=(0, 8))
        games = installed_games()
        if not games:
            tk.Label(self.content, text='No HTML games installed yet. Start with the Redder7 demo.',
                     fg=MUTED, bg=DARK, font=('DejaVu Sans', 11)).pack(anchor='w', pady=25)
        for game in games:
            item = tk.Frame(self.content, bg=PANEL)
            item.pack(fill='x', pady=4)
            tk.Label(item, text=game['name'], bg=PANEL, fg=TEXT,
                     font=('DejaVu Sans', 11, 'bold')).pack(side='left', padx=15, pady=16)
            self.button(item, 'Remove', lambda g=game: self.remove(g), colored=False).pack(side='right', padx=10)
            self.button(item, 'Play', lambda g=game: self.play(g)).pack(side='right')

    def import_redder7(self):
        self.import_file('Redder7: The Game')

    def import_any(self):
        self.import_file(None)

    def import_file(self, title):
        location = filedialog.askopenfilename(title='Choose a game file',
                    filetypes=[('HTML game or ZIP', '*.html *.zip'), ('All files', '*.*')])
        if not location:
            return
        if not messagebox.askyesno('Trust this game?',
                'Only install games from people you trust. HTML games can run code in your browser. Continue?'):
            return
        try:
            game = install_html_game(location, title)
            self.status.set(f"Installed {game['name']}")
            self.show_games()
        except (ValueError, OSError, ImportError, Exception) as exc:
            messagebox.showerror('Import failed', str(exc))

    def install_demo(self):
        demo = Path(__file__).resolve().parent.parent / 'demo' / 'redder7-training.html'
        if not demo.is_file():
            # Built ISO stores demo alongside app code.
            demo = Path(__file__).resolve().parent / 'demo' / 'redder7-training.html'
        if not demo.is_file():
            messagebox.showerror('Missing demo', 'The Redder7 demo file is missing.')
            return
        try:
            install_html_game(demo, 'Redder7: Training Arena (Demo)')
            self.status.set('Redder7 demo installed!')
            self.show_games()
        except (ValueError, OSError) as exc:
            messagebox.showerror('Unable to install', str(exc))

    def play(self, game):
        address = Path(game['main']).as_uri()
        if not webbrowser.open(address):
            messagebox.showinfo('Open this game', f'Open this file in a web browser:\n{game["main"]}')
        self.status.set(f"Launched {game['name']} in your web browser.")

    def remove(self, game):
        if not messagebox.askyesno('Uninstall game?', f"Remove {game['name']} from Solomon OS?"):
            return
        try:
            remove_game(game)
            self.show_games()
        except (OSError, ValueError) as exc:
            messagebox.showerror('Unable to remove', str(exc))

    def show_help(self):
        self.section('How to play', 'Game installers need internet and a compatible graphics driver.')
        helptext = (
            'STEAM + PROTON\n'
            'Install Steam, sign in to your account, open Steam Settings > Compatibility, '
            'and enable Steam Play for other titles. Install purchased games from Steam.\n\n'
            'CLASSIC MARIO / SONIC\n'
            'Install RetroArch, add emulator cores, and open game files you legally possess. '
            'No Nintendo or Sega games are included.\n\n'
            'FNAF / WINDOWS GAMES\n'
            'Use a compatible release from Steam, or try Bottles / Lutris / Heroic. '
            'Compatibility and performance depend on the game and hardware.\n\n'
            'REDDER7\n'
            'Click My games > Install Redder7 game, then select your existing .html or '
            '.zip HTML game build. Or click Install demo for the included original prototype.\n\n'
            'VIRTUAL MACHINES\n'
            'VirtualBox usually has limited gaming GPU acceleration. Real games run best '
            'on a real Linux installation with proper graphics drivers.\n\n'
            'LIVE ISO\n'
            'Changes to a live ISO are temporary unless your boot drive is persistent. '
            'For saved game installs use a normal installed Linux desktop with setup.sh.'
        )
        tk.Label(self.content, text=helptext, justify='left', bg=DARK, fg=TEXT,
                 wraplength=840, font=('DejaVu Sans', 11)).pack(anchor='w', pady=5)


def main():
    if '--help' in sys.argv:
        print('Solomon OS Gaming Edition hub. Run with a Linux desktop or use --help.')
        return
    try:
        root = tk.Tk()
        Hub(root)
        root.mainloop()
    except tk.TclError as exc:
        print(f'A graphical Linux desktop is required: {exc}', file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
