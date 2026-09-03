from __future__ import annotations

import re
import shutil
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


class UserFacingError(Exception):
    pass



def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT = app_root()
BUILD_DIR = ROOT / ".build"
WRAPPERS_DIR = BUILD_DIR / "wrappers"
ASSETS_DIR = BUILD_DIR / "assets"
EXPORTS_DIR = ROOT / "exports"
GENERATED_PROBLEMS_TEX = ROOT / "generated-problems.tex"
CONTEST_INFO_TEX = ROOT / "contest-info.tex"
MAIN_TEX = ROOT / "main.tex"
MAIN_PDF = ROOT / "main.pdf"
DROP_DIR = BUILD_DIR / "drop"

# Templates the engine materialises into the work root when missing. In frozen
# (PyInstaller onefile) builds they come from sys._MEIPASS, in a repo checkout
# from the repository itself. pic/ is intentionally absent: logos are provided
# by the user.
BUNDLED_ASSETS = ("main.tex", "contest-info.tex", "styles")



def set_work_root(path: Path) -> None:
    """Repoint every engine path at an arbitrary work root.

    The GUI builds inside a throwaway temp directory so the executable's own
    folder stays completely clean; the CLI and the legacy drag-and-drop exes
    keep the default (the directory containing build.py / the exe).
    """
    global ROOT, BUILD_DIR, WRAPPERS_DIR, ASSETS_DIR, EXPORTS_DIR
    global GENERATED_PROBLEMS_TEX, CONTEST_INFO_TEX, MAIN_TEX, MAIN_PDF, DROP_DIR
    ROOT = Path(path)
    BUILD_DIR = ROOT / ".build"
    WRAPPERS_DIR = BUILD_DIR / "wrappers"
    ASSETS_DIR = BUILD_DIR / "assets"
    EXPORTS_DIR = ROOT / "exports"
    GENERATED_PROBLEMS_TEX = ROOT / "generated-problems.tex"
    CONTEST_INFO_TEX = ROOT / "contest-info.tex"
    MAIN_TEX = ROOT / "main.tex"
    MAIN_PDF = ROOT / "main.pdf"
    DROP_DIR = BUILD_DIR / "drop"

TITLE_RE = re.compile(r"\\begin\{problem\}\{((?:[^{}]|\{[^{}]*\})*)\}")
IMPORT_RE = re.compile(
    r"\\graphicspath\{\{\.\./\.\./problems/([^/]+)/statements/chinese/\}\}\s*"
    r"\\def\\ProblemIndex\{([^}]*)\}\s*"
    r"\\import\{\.\./\.\./problems/\1/statements/chinese/\}\{\./problem\.tex\}",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ProblemStatement:
    slug: str
    title: str
    letter: str
    statement_tex: Path
    wrapper_tex: Path


@dataclass(frozen=True)
class BuildContext:
    contest_root: Path
    problems: list[ProblemStatement]


@dataclass(frozen=True)
class ResolvedContestInput:
    contest_root: Path



def ensure_templates() -> None:
    """Materialise the bundled templates into the work root if they are missing.

    In frozen builds the source is sys._MEIPASS; in a repo checkout it is the
    repository itself, so a redirected work root gets a fresh copy while the
    default work root already has everything in place.
    """
    if getattr(sys, "frozen", False):
        source_dir = Path(getattr(sys, "_MEIPASS", ""))
    else:
        source_dir = app_root()
    for name in BUNDLED_ASSETS:
        source = source_dir / name
        target = ROOT / name
        if target.exists() or not source.exists():
            continue
        try:
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        except OSError as exc:
            raise UserFacingError(
                "Could not set up the working directory for the build.\n\n"
                f"Failed to copy {source} to {target}"
            ) from exc



def cleanup_drop() -> None:
    shutil.rmtree(DROP_DIR, ignore_errors=True)



def contest_root_for(package_name: str) -> Path:
    package_path = Path(package_name)
    if package_path.is_absolute():
        return package_path
    return (Path.cwd() / package_path).resolve()



def is_contest_root(path: Path) -> bool:
    return path.is_dir() and (path / "problems").is_dir() and (path / "statements" / "chinese" / "statements.tex").is_file()



def find_contest_root(search_root: Path) -> Path:
    if is_contest_root(search_root):
        return search_root
    matches = [path for path in search_root.iterdir() if path.is_dir() and is_contest_root(path)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise UserFacingError(
            "Could not find a valid contest package root.\n\n"
            "Expected to find both:\n"
            "- problems/\n"
            "- statements/chinese/statements.tex\n\n"
            f"Checked under: {search_root}"
        )
    raise UserFacingError(
        "Found multiple possible contest package roots.\n\n"
        "Please keep only one contest package in the input folder.\n\n"
        f"Checked under: {search_root}\n"
        f"Matches: {matches}"
    )



def extract_zip_to_temp(zip_path: Path) -> ResolvedContestInput:
    extract_root = (DROP_DIR / zip_path.stem).resolve()
    if not extract_root.is_relative_to(DROP_DIR):
        raise UserFacingError(
            f"Cannot use this zip file name as an extraction folder:\n{zip_path}"
        )
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
    except zipfile.BadZipFile as exc:
        raise UserFacingError(
            f"The zip file is invalid or corrupted:\n{zip_path}"
        ) from exc
    contest_root = find_contest_root(extract_root)
    return ResolvedContestInput(contest_root=contest_root)



def resolve_contest_input(package_name: str) -> ResolvedContestInput:
    input_path = contest_root_for(package_name)
    if not input_path.exists():
        raise UserFacingError(f"Input path does not exist:\n{input_path}")
    if input_path.is_file() and input_path.suffix.lower() == ".zip":
        return extract_zip_to_temp(input_path)
    if input_path.is_dir():
        return ResolvedContestInput(contest_root=find_contest_root(input_path))
    raise UserFacingError(
        "Expected a contest folder or a .zip file as input.\n\n"
        f"Got: {input_path}"
    )



def require_problems_dir(problems_dir: Path, statements_order_tex: Path) -> None:
    if not problems_dir.is_dir():
        raise UserFacingError(
            "This does not look like a valid contest package.\n\n"
            f"Missing directory: {problems_dir}"
        )
    if not statements_order_tex.is_file():
        raise UserFacingError(
            "This does not look like a valid contest package.\n\n"
            f"Missing file: {statements_order_tex}"
        )



def problem_order_from_statements(statements_order_tex: Path) -> list[tuple[str, str]]:
    text = statements_order_tex.read_text(encoding="utf-8")
    matches = IMPORT_RE.findall(text)
    if not matches:
        raise UserFacingError(
            "Could not parse problem order from statements.tex.\n\n"
            "Please check whether statements/chinese/statements.tex contains valid problem imports.\n\n"
            f"File: {statements_order_tex}"
        )
    return [(slug, letter) for slug, letter in matches]



def discover_problem_dirs(problems_dir: Path, order: list[tuple[str, str]]) -> list[Path]:
    problem_dirs = {path.name: path for path in problems_dir.iterdir() if path.is_dir()}
    ordered: list[Path] = []
    missing: list[str] = []
    for slug, _ in order:
        problem_dir = problem_dirs.get(slug)
        if problem_dir is None:
            missing.append(slug)
        else:
            ordered.append(problem_dir)
    if missing:
        raise UserFacingError(
            "Some problems listed in statements.tex were not found in problems/.\n\n"
            f"Missing problem directories: {missing}"
        )
    return ordered



def statement_path_for(problem_dir: Path) -> Path:
    statement_tex = problem_dir / "statements" / "chinese" / "problem.tex"
    if not statement_tex.is_file():
        raise UserFacingError(
            "A problem is missing its Chinese statement file.\n\n"
            f"Missing file: {statement_tex}"
        )
    return statement_tex



def extract_title(statement_tex: Path) -> str:
    text = statement_tex.read_text(encoding="utf-8")
    match = TITLE_RE.search(text)
    if not match:
        raise UserFacingError(
            "Could not extract the problem title from a statement file.\n\n"
            f"File: {statement_tex}"
        )
    return match.group(1).strip()



def to_posix(path: Path) -> str:
    return path.as_posix()



def make_wrapper(problem_dir: Path, statement_tex: Path) -> Path:
    try:
        relative_statement = statement_tex.relative_to(ROOT)
    except ValueError:
        # Package on a different drive than the work root: fall back to an
        # absolute path. Local PDF builds handle it fine, and the Overleaf
        # export rewrites wrappers with relative paths anyway.
        relative_statement = statement_tex
    wrapper_path = WRAPPERS_DIR / f"{problem_dir.name}.tex"
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    asset_dir = ASSETS_DIR / problem_dir.name
    relative_asset_dir = asset_dir.relative_to(ROOT)
    asset_part = "{" + to_posix(relative_asset_dir) + "/}"
    statement_dir_part = "{" + to_posix(relative_statement.parent) + "/}"
    wrapper_content = "\n".join(
        [
            r"\begingroup",
            r"\makeatletter",
            "\\def\\input@path{" + asset_part + statement_dir_part + "}",
            r"\makeatother",
            "\\graphicspath{" + asset_part + statement_dir_part + "}",
            rf"\input{{{to_posix(relative_statement)}}}",
            r"\endgroup",
            "",
        ]
    )
    wrapper_path.write_text(wrapper_content, encoding="utf-8")
    return wrapper_path



def collect_problems(problems_dir: Path, statements_order_tex: Path) -> list[ProblemStatement]:
    problems: list[ProblemStatement] = []
    order = problem_order_from_statements(statements_order_tex)
    problem_dirs = discover_problem_dirs(problems_dir, order)
    for (slug, letter), problem_dir in zip(order, problem_dirs):
        statement_tex = statement_path_for(problem_dir)
        wrapper_tex = make_wrapper(problem_dir, statement_tex)
        problems.append(
            ProblemStatement(
                slug=slug,
                title=extract_title(statement_tex),
                letter=letter,
                statement_tex=statement_tex,
                wrapper_tex=wrapper_tex,
            )
        )
    return problems



def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)



def render_generated_tex(problems: list[ProblemStatement]) -> str:
    lines: list[str] = [
        "% Auto-generated by build.py",
        r"\RenderContestTitlePage{%",
        r"\begin{center}",
        r"\setlength{\tabcolsep}{10pt}",
        r"\begin{tabular}{|>{\centering\arraybackslash}p{1cm}|>{\centering\arraybackslash}p{6cm}|}",
        r"\hline",
        r"题号 & 题目名称 \\",
        r"\hline",
    ]
    for problem in problems:
        lines.append(
            rf"{problem.letter} & {latex_escape(problem.title)} \\"
        )
    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\end{center}",
            r"}",
            "",
        ]
    )
    for problem in problems:
        relative_wrapper = problem.wrapper_tex.relative_to(ROOT)
        lines.append(rf"\input{{{to_posix(relative_wrapper)}}}")
        lines.append("")
    return "\n".join(lines)



def write_generated_tex(problems: list[ProblemStatement]) -> None:
    GENERATED_PROBLEMS_TEX.write_text(render_generated_tex(problems), encoding="utf-8")



def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)



def copy_tree(source_dir: Path, destination_dir: Path) -> None:
    if destination_dir.exists():
        shutil.rmtree(destination_dir)
    shutil.copytree(source_dir, destination_dir)



def export_wrapper_content(problem: ProblemStatement) -> str:
    problem_dir = Path("problems") / problem.slug
    problem_part = "{" + to_posix(problem_dir) + "/}"
    asset_part = "{" + to_posix(problem_dir / "assets") + "/}"
    statement_path = problem_dir / "problem.tex"
    return "\n".join(
        [
            r"\begingroup",
            r"\makeatletter",
            "\\def\\input@path{" + asset_part + problem_part + "}",
            r"\makeatother",
            "\\graphicspath{" + asset_part + problem_part + "}",
            rf"\input{{{to_posix(statement_path)}}}",
            r"\endgroup",
            "",
        ]
    )



def output_paths_for(package: Path) -> tuple[Path, Path]:
    """Delivery locations for a given contest package: (pdf, overleaf base).

    Both sit next to the package itself: <name>.pdf and <name>/overleaf/.
    """
    package = Path(package)
    # Decide by suffix, not by touching the filesystem: the package may be a
    # path that does not exist yet, and folders must keep their full name.
    stem = package.stem if package.suffix.lower() == ".zip" else package.name
    return package.parent / f"{stem}.pdf", package.parent / stem



def export_overleaf_bundle(build: BuildContext, destination_dir: Path | None = None) -> Path:
    if destination_dir is None:
        bundle_root = EXPORTS_DIR / build.contest_root.name / "overleaf"
    else:
        bundle_root = Path(destination_dir) / "overleaf"
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    copy_file(MAIN_TEX, bundle_root / "main.tex")
    copy_file(CONTEST_INFO_TEX, bundle_root / "contest-info.tex")
    copy_file(GENERATED_PROBLEMS_TEX, bundle_root / "generated-problems.tex")
    copy_tree(ROOT / "styles", bundle_root / "styles")

    info_content = CONTEST_INFO_TEX.read_text(encoding="utf-8")
    for name in ("ContestLeftLogo", "ContestRightLogo"):
        match = re.search(rf"\\newcommand\{{\\{name}\}}\{{([^}}]*)\}}", info_content)
        if not match or not match.group(1).strip():
            continue
        logo_path = Path(match.group(1).strip())
        source_logo = (ROOT / logo_path).resolve()
        try:
            relative_logo = source_logo.relative_to(ROOT)
        except ValueError:
            raise UserFacingError(
                f"\\{name} must point to a file inside the project folder.\n\n"
                f"Got: {logo_path}"
            ) from None
        if not source_logo.is_file():
            raise UserFacingError(
                f"The logo configured as \\{name} does not exist.\n\n"
                f"Missing file: {source_logo}"
            )
        copy_file(source_logo, bundle_root / relative_logo)

    generated_content = GENERATED_PROBLEMS_TEX.read_text(encoding="utf-8")
    for problem in build.problems:
        destination_problem_dir = bundle_root / "problems" / problem.slug
        destination_assets_dir = destination_problem_dir / "assets"
        destination_problem_dir.mkdir(parents=True, exist_ok=True)
        copy_file(problem.statement_tex, destination_problem_dir / "problem.tex")
        source_assets_dir = ASSETS_DIR / problem.slug
        if source_assets_dir.is_dir():
            copy_tree(source_assets_dir, destination_assets_dir)
        wrapper_relative = problem.wrapper_tex.relative_to(ROOT)
        generated_content = generated_content.replace(
            rf"\input{{{to_posix(wrapper_relative)}}}",
            export_wrapper_content(problem).rstrip(),
        )

    (bundle_root / "generated-problems.tex").write_text(generated_content + "\n", encoding="utf-8")
    return bundle_root


def update_contest_info(problem_count: int) -> None:
    content = CONTEST_INFO_TEX.read_text(encoding="utf-8")
    content, replaced = re.subn(
        r"\\newcommand\{\\ContestProblemCount\}\{\d+\}",
        rf"\\newcommand{{\\ContestProblemCount}}{{{problem_count}}}",
        content,
    )
    if replaced == 0:
        raise UserFacingError(
            "Could not update the problem count in contest-info.tex.\n\n"
            "Expected a line of the exact form:\n"
            "\\newcommand{\\ContestProblemCount}{3}\n\n"
            f"File: {CONTEST_INFO_TEX}"
        )
    CONTEST_INFO_TEX.write_text(content, encoding="utf-8")



INFO_MACROS = ("ContestName", "ContestOrganizer", "ContestDate", "ContestLeftLogo")

UNESCAPE_ORDER = (
    (r"\textbackslash{}", "\\"),
    (r"\textasciitilde{}", "~"),
    (r"\textasciicircum{}", "^"),
    (r"\&", "&"),
    (r"\%", "%"),
    (r"\$", "$"),
    (r"\#", "#"),
    (r"\_", "_"),
    (r"\{", "{"),
    (r"\}", "}"),
)


def latex_unescape(text: str) -> str:
    for escaped, raw in UNESCAPE_ORDER:
        text = text.replace(escaped, raw)
    return text



def read_contest_info_values(path: Path | None = None) -> dict[str, str]:
    content = (
        Path(path).read_text(encoding="utf-8")
        if path is not None
        else CONTEST_INFO_TEX.read_text(encoding="utf-8")
    )
    values: dict[str, str] = {}
    for macro in INFO_MACROS:
        match = re.search(rf"\\newcommand\{{\\{macro}\}}\{{([^}}]*)\}}", content)
        values[macro] = latex_unescape(match.group(1)) if match else ""
    return values



def set_contest_info(
    name: str | None = None,
    organizer: str | None = None,
    date: str | None = None,
    logo_path: str | None = None,
) -> None:
    content = CONTEST_INFO_TEX.read_text(encoding="utf-8")
    updates = {
        "ContestName": None if name is None else latex_escape(name),
        "ContestOrganizer": None if organizer is None else latex_escape(organizer),
        "ContestDate": None if date is None else latex_escape(date),
        # Path("") would normalize to ".", so keep empty as a bare empty value.
        "ContestLeftLogo": None if logo_path is None else (to_posix(Path(logo_path)) if logo_path else ""),
    }
    for macro, value in updates.items():
        if value is None:
            continue
        content, replaced = re.subn(
            rf"\\newcommand\{{\\{macro}\}}\{{[^}}]*\}}",
            rf"\\newcommand{{\\{macro}}}{{{value}}}",
            content,
        )
        if replaced == 0:
            raise UserFacingError(
                f"Could not update \\{macro} in contest-info.tex.\n\n"
                "Expected a line of the exact form:\n"
                f"\\newcommand{{\\{macro}}}{{...}}\n\n"
                f"File: {CONTEST_INFO_TEX}"
            )
    CONTEST_INFO_TEX.write_text(content, encoding="utf-8")



def copy_assets_for_problem(problem: ProblemStatement) -> None:
    source_dir = problem.statement_tex.parent
    target_dir = ASSETS_DIR / problem.slug
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate_dirs = [source_dir]
    statement_sections_dir = source_dir.parent.parent / "statement-sections" / source_dir.name
    if statement_sections_dir.is_dir():
        candidate_dirs.append(statement_sections_dir)
    for directory in candidate_dirs:
        for source in directory.iterdir():
            if source.is_file():
                shutil.copy2(source, target_dir / source.name)



def prepare_build_dir(problems: list[ProblemStatement]) -> None:
    if WRAPPERS_DIR.exists():
        shutil.rmtree(WRAPPERS_DIR)
    if ASSETS_DIR.exists():
        shutil.rmtree(ASSETS_DIR)
    WRAPPERS_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for problem in problems:
        copy_assets_for_problem(problem)
        make_wrapper(problem.statement_tex.parent.parent.parent, problem.statement_tex)



def run_xelatex() -> None:
    command = [
        "xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        MAIN_TEX.name,
    ]
    try:
        for _ in range(2):
            # CREATE_NO_WINDOW keeps xelatex from flashing a console window when
            # the builder runs from the windowed GUI executable.
            subprocess.run(
                command,
                cwd=ROOT,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
    except FileNotFoundError as exc:
        raise UserFacingError(
            "xelatex was not found.\n\n"
            "Please install TeX Live or MiKTeX and make sure xelatex is available in PATH.\n"
            "If you only need an online build, use the Overleaf export mode instead."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise UserFacingError(
            "XeLaTeX build failed.\n\n"
            f"See this file for details:\n{MAIN_TEX.with_suffix('.log')}\n\n"
            "Common causes include LaTeX syntax errors in a problem statement, missing images, or missing statement assets."
        ) from exc



def parse_args() -> tuple[str, str]:
    if len(sys.argv) == 2:
        return "both", sys.argv[1]
    if len(sys.argv) != 3:
        raise SystemExit(
            f"usage: python {Path(__file__).name} <build|overleaf> <contest-package-folder-or-zip>"
        )
    mode = sys.argv[1]
    if mode not in {"build", "overleaf", "both"}:
        raise SystemExit("mode must be one of: build, overleaf, both")
    return mode, sys.argv[2]



def prepare_build(package_name: str) -> BuildContext:
    ensure_templates()
    resolved = resolve_contest_input(package_name)
    contest_root = resolved.contest_root

    problems_dir = contest_root / "problems"
    statements_order_tex = contest_root / "statements" / "chinese" / "statements.tex"

    require_problems_dir(problems_dir, statements_order_tex)
    problems = collect_problems(problems_dir, statements_order_tex)
    if not problems:
        raise UserFacingError(
            "No problem directories were found in the contest package.\n\n"
            f"Problems folder: {problems_dir}"
        )
    prepare_build_dir(problems)
    update_contest_info(problem_count=len(problems))
    write_generated_tex(problems)
    return BuildContext(contest_root=contest_root, problems=problems)



def build_pdf(build: BuildContext) -> None:
    # Two passes are required: the cover and footers reference \pageref{LastPage},
    # which is only resolvable after the first pass has written the aux file.
    run_xelatex()
    run_xelatex()
    print(f"Built {MAIN_PDF}")



def run_pdf_mode(package_name: str) -> None:
    build = prepare_build(package_name)
    build_pdf(build)



def run_overleaf_mode(package_name: str) -> None:
    build = prepare_build(package_name)
    bundle_root = export_overleaf_bundle(build)
    print(f"Exported {bundle_root}")



def main() -> None:
    mode, package_name = parse_args()
    if mode in {"build", "both"}:
        run_pdf_mode(package_name)
    if mode in {"overleaf", "both"}:
        run_overleaf_mode(package_name)


if __name__ == "__main__":
    try:
        main()
    except UserFacingError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
    cleanup_drop()
