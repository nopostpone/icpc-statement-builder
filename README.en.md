[简体中文版本](README.md)

# ICPC Statement Builder

Polygon's bundled `.sty` files have poor support for Chinese and cannot compile Chinese problem statements out of the box.

ICPC Statement Builder takes a complete contest package exported from Polygon and automatically assembles it into a full ICPC/CCPC-style **Chinese** PDF statement booklet.

> Some known limitations remain, e.g. limited support for customized content (oversized images may overflow, a very long single line in examples does not wrap, etc.). These need manual fixes in the problem's TeX files.

## Usage

1. Clone this repository:

```bash
git clone https://github.com/nopostpone/icpc-statement-builder.git
```

2. Unzip the contest package exported from Polygon and copy the whole folder into the repository root; or just keep the zip — both the commands and the exes accept either a folder or a zip.
3. Put your contest logo at `pic/logo.png`.
4. Edit `contest-info.tex` with your contest info: name, date, organizer, etc.
5. Choose a run mode:

Compile locally with XeLaTeX:

```bash
python build.py build <contest-package-folder-or-zip>
```

Export a directory that can be uploaded directly to Overleaf or any other online LaTeX platform:

```bash
python build.py overleaf <contest-package-folder-or-zip>
```

For example, if your contest package is named `contest-123` and you want a local PDF, unzip `contest-123.zip` in the root and run:

```bash
python build.py build contest-123
```

If you only have the zip, this works too:

```bash
python build.py build contest-123.zip
```

To also export a directory for Overleaf, run:

```bash
python build.py overleaf contest-123
```

or:

```bash
python build.py overleaf contest-123.zip
```

On Windows, you can simply drag a zip or a contest folder onto one of these programs:
- `icpc-statement-builder-pdf.exe`: build a local PDF
- `icpc-statement-builder-overleaf.exe`: export an Overleaf directory

Both exes are self-contained: on first run they unpack `main.tex`, `contest-info.tex`, `styles/` and `pic/` next to the executable. Afterwards you can edit `contest-info.tex` and `pic/logo.png` right there, no repackaging needed. The script will:
- read the problem order and letters from `statements/chinese/statements.tex` of the contest
- scan `problems/`
- read each problem's `problems/<slug>/statements/chinese/problem.tex`
- generate `generated-problems.tex`
- in `build` mode, invoke XeLaTeX to compile `main.tex`
- in `overleaf` mode, generate a self-contained Overleaf export directory

## File responsibilities

- `main.tex`: master template, loads packages and styles and drives the statement output
- `contest-info.tex`: contest configuration — name, organizer, date, logos, plus the problem count auto-filled by `build.py`
- `styles/olymp.sty`: Polygon statement typesetting layer (`problem`, input/output, examples, etc.)
- `styles/contest-style.sty`: project-specific layout layer (cover page, headers and footers)

## Conventions

- Only Chinese statements are read: `<contest-package-folder>/problems/<slug>/statements/chinese/problem.tex`
- `\ContestProblemCount` in `contest-info.tex` is auto-filled by `build.py` — do not maintain it by hand; the page counts on the cover and in footers are resolved via `\pageref{LastPage}` automatically, both locally and on Overleaf
- The cover logo size is controlled by `\ContestLogoWidth`, adjust as needed
- The cover logo is not part of the Polygon package; it always uses the project resource path `pic/logo.png`
- `main.tex` is the master template and rarely needs manual changes

## Dependencies

- Python 3.10+
- XeLaTeX (only needed for local PDF builds; not needed for Overleaf export)

## Packaging the exes

### Automatic releases (recommended)

Push a tag starting with `v` (e.g. `v1.0.0`) and GitHub Actions will automatically build both exes on Windows and publish them to Releases:

```bash
git tag v1.0.0
git push origin v1.0.0
```

You can also trigger it manually from the repository's Actions page (Run workflow); this only builds and produces a downloadable artifact without creating a Release.

### Local packaging

```bash
pyinstaller pdf.spec
pyinstaller overleaf.spec
```

This produces in `dist/`:
- `icpc-statement-builder-pdf.exe`
- `icpc-statement-builder-overleaf.exe`

Both exes support dragging a contest zip or an extracted contest folder onto the program icon.

## Output

`build` mode generates in the project root:
- `generated-problems.tex`
- `main.pdf`
- `.build/` (intermediate files)

`overleaf` mode additionally generates:
- `exports/<contest-package-folder>/overleaf/` (the cleaned-up export directory)

The Overleaf export directory contains only the files needed for compilation, e.g.:
- `main.tex`
- `contest-info.tex`
- `generated-problems.tex`
- `styles/`
- the logos actually referenced from `pic/`
- `problems/<slug>/problem.tex`
- `problems/<slug>/assets/`
