"""Local, user-provided HTML game imports for Solomon OS Gaming Edition."""
from __future__ import annotations
import json
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

DATA_DIR = Path.home() / '.local' / 'share' / 'solomon-os' / 'games'
MAX_EXTRACTED_BYTES = 600 * 1024 * 1024
MAX_ENTRIES = 2000


def safe_name(value: str) -> str:
    result = re.sub(r'[^a-z0-9-]+', '-', value.lower().strip()).strip('-')
    return (result[:60] or 'game')


def _find_html(root: Path) -> Path:
    pages = [p for p in root.rglob('*.html') if p.is_file()]
    if not pages:
        raise ValueError('This archive does not contain an HTML game (.html).')
    preferred = [p for p in pages if p.name.lower() == 'index.html']
    return min(preferred or pages, key=lambda p: (len(p.relative_to(root).parts), str(p)))


def _extract_zip(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        records = zf.infolist()
        if len(records) > MAX_ENTRIES:
            raise ValueError('Too many entries in ZIP.')
        total = sum(info.file_size for info in records)
        if total > MAX_EXTRACTED_BYTES:
            raise ValueError('ZIP is too large when extracted (limit: 600 MB).')
        for info in records:
            # Reject symlink entries, file traversal and absolute paths.
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise ValueError('ZIP includes a symbolic link.')
            item = Path(info.filename.replace('\\', '/'))
            if not info.filename or item.is_absolute() or '..' in item.parts:
                raise ValueError('Unsafe path found in ZIP.')
            if info.is_dir():
                continue
            target = (destination / item).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError('Unsafe path found in ZIP.')
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, 'r') as src, target.open('wb') as dst:
                shutil.copyfileobj(src, dst, length=1024 * 1024)


def install_html_game(file: str | Path, name: str | None = None, data_dir: Path | None = None) -> dict:
    """Import a trusted local .html or .zip, atomically, without running it."""
    source = Path(file).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() not in {'.html', '.zip'}:
        raise ValueError('Choose a .html game or .zip containing HTML game files.')
    library = (data_dir or DATA_DIR).expanduser().resolve()
    library.mkdir(parents=True, exist_ok=True)
    label = (name or source.stem).strip()[:90] or 'Untitled Game'
    stem = safe_name(label)
    target = library / stem
    suffix = 2
    while target.exists():
        target = library / f'{stem}-{suffix}'
        suffix += 1
    with tempfile.TemporaryDirectory(prefix='.solomon-import-', dir=library) as temp:
        folder = Path(temp)
        if source.suffix.lower() == '.zip':
            _extract_zip(source, folder)
        else:
            shutil.copy2(source, folder / 'index.html')
        start = _find_html(folder).relative_to(folder).as_posix()
        manifest = {'name': label, 'start': start, 'type': 'html', 'source': 'user-import'}
        (folder / 'solomon-game.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        folder.rename(target)
    manifest['path'] = str(target)
    return manifest


def installed_games(data_dir: Path | None = None) -> list[dict]:
    library = (data_dir or DATA_DIR).expanduser()
    if not library.exists():
        return []
    output = []
    for folder in sorted(library.iterdir()):
        meta_path = folder / 'solomon-game.json'
        if not folder.is_dir() or not meta_path.exists():
            continue
        try:
            obj = json.loads(meta_path.read_text(encoding='utf-8'))
            main = (folder / obj['start']).resolve()
            if main.is_file() and main.is_relative_to(folder.resolve()):
                obj['path'] = str(folder)
                obj['main'] = str(main)
                output.append(obj)
        except (KeyError, ValueError, OSError, TypeError):
            continue
    return output


def remove_game(game: dict, data_dir: Path | None = None) -> None:
    root = (data_dir or DATA_DIR).expanduser().resolve()
    target = Path(game['path']).resolve()
    if target.parent != root or not (target / 'solomon-game.json').is_file():
        raise ValueError('Not an installed game directory.')
    shutil.rmtree(target)
