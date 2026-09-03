from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

ROOT = Path.cwd()

DATA_FILES = [
    (str(ROOT / "main.tex"), "."),
    (str(ROOT / "contest-info.tex"), "."),
    (str(ROOT / "styles"), "styles"),
    (str(ROOT / "pic"), "pic"),
]
