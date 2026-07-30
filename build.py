from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_DIR = ROOT / ".build"
WRAPPERS_DIR = BUILD_DIR / "wrappers"
ASSETS_DIR = BUILD_DIR / "assets"
EXPORTS_DIR = ROOT / "exports"
GENERATED_PROBLEMS_TEX = ROOT / "generated-problems.tex"
CONTEST_INFO_TEX = ROOT / "contest-info.tex"
MAIN_TEX = ROOT / "main.tex"
MAIN_PDF = ROOT / "main.pdf"
MAIN_AUX = ROOT / "main.aux"

TITLE_RE = re.compile(r"\\begin\{problem\}\{([^}]*)\}")
LASTPAGE_RE = re.compile(r"\\newlabel\{LastPage\}\{\{\}\{(\d+)\}")
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



def contest_root_for(package_name: str) -> Path:
    return ROOT / package_name



def require_problems_dir(problems_dir: Path, statements_order_tex: Path) -> None:
    if not problems_dir.is_dir():
        raise SystemExit(f"missing problems directory: {problems_dir}")
    if not statements_order_tex.is_file():
        raise SystemExit(f"missing statements order file: {statements_order_tex}")



def problem_order_from_statements(statements_order_tex: Path) -> list[tuple[str, str]]:
    text = statements_order_tex.read_text(encoding="utf-8")
    matches = IMPORT_RE.findall(text)
    if not matches:
        raise ValueError(f"cannot parse problem order from: {statements_order_tex}")
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
        raise FileNotFoundError(f"missing problem directories referenced by statements order: {missing}")
    return ordered



def statement_path_for(problem_dir: Path) -> Path:
    statement_tex = problem_dir / "statements" / "chinese" / "problem.tex"
    if not statement_tex.is_file():
        raise FileNotFoundError(f"missing chinese statement tex: {statement_tex}")
    return statement_tex



def extract_title(statement_tex: Path) -> str:
    text = statement_tex.read_text(encoding="utf-8")
    match = TITLE_RE.search(text)
    if not match:
        raise ValueError(f"cannot extract title from: {statement_tex}")
    return match.group(1).strip()



def problem_letter(index: int) -> str:
    if index < 0:
        raise ValueError("index must be non-negative")

    label = ""
    value = index
    while True:
        value, remainder = divmod(value, 26)
        label = chr(ord("A") + remainder) + label
        if value == 0:
            return label
        value -= 1



def to_posix(path: Path) -> str:
    return path.as_posix()



def make_wrapper(problem_dir: Path, statement_tex: Path) -> Path:
    relative_statement = statement_tex.relative_to(ROOT)
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
    for problem_dir, (_, letter) in zip(discover_problem_dirs(problems_dir, order), order):
        statement_tex = statement_path_for(problem_dir)
        wrapper_tex = make_wrapper(problem_dir, statement_tex)
        problems.append(
            ProblemStatement(
                slug=problem_dir.name,
                title=extract_title(statement_tex),
                letter=letter,
                statement_tex=statement_tex,
                wrapper_tex=wrapper_tex,
            )
        )
    return problems



def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\\textbackslash{}",
        "&": r"\\&",
        "%": r"\\%",
        "$": r"\\$",
        "#": r"\\#",
        "_": r"\\_",
        "{": r"\\{",
        "}": r"\\}",
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



def export_overleaf_bundle(build: BuildContext) -> Path:
    export_root = EXPORTS_DIR / build.contest_root.name
    bundle_root = export_root / "overleaf"
    if export_root.exists():
        shutil.rmtree(export_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    copy_file(MAIN_TEX, bundle_root / "main.tex")
    copy_file(CONTEST_INFO_TEX, bundle_root / "contest-info.tex")
    copy_file(GENERATED_PROBLEMS_TEX, bundle_root / "generated-problems.tex")
    copy_tree(ROOT / "styles", bundle_root / "styles")

    info_content = CONTEST_INFO_TEX.read_text(encoding="utf-8")
    logo_paths = []
    for name in ("ContestLeftLogo", "ContestRightLogo"):
        match = re.search(rf"\\newcommand\{{\\{name}\}}\{{([^}}]*)\}}", info_content)
        if match and match.group(1).strip():
            logo_paths.append(Path(match.group(1).strip()))
    for logo_path in logo_paths:
        source_logo = ROOT / logo_path
        if source_logo.is_file():
            copy_file(source_logo, bundle_root / logo_path)

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


def update_contest_info(problem_count: int, page_count: int) -> None:
    content = CONTEST_INFO_TEX.read_text(encoding="utf-8")
    content = re.sub(
        r"\\newcommand\{\\ContestProblemCount\}\{\d+\}",
        rf"\\newcommand{{\\ContestProblemCount}}{{{problem_count}}}",
        content,
    )
    content = re.sub(
        r"\\newcommand\{\\ContestPageCount\}\{\d+\}",
        rf"\\newcommand{{\\ContestPageCount}}{{{page_count}}}",
        content,
    )
    CONTEST_INFO_TEX.write_text(content, encoding="utf-8")



def extract_page_count() -> int:
    if not MAIN_AUX.is_file():
        raise FileNotFoundError(f"missing aux file: {MAIN_AUX}")
    text = MAIN_AUX.read_text(encoding="utf-8", errors="ignore")
    match = LASTPAGE_RE.search(text)
    if not match:
        raise ValueError("cannot determine total page count from main.aux")
    return int(match.group(1))



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
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
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
    for _ in range(2):
        subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )



def parse_args() -> tuple[str, str]:
    if len(sys.argv) != 3:
        raise SystemExit(
            f"usage: python {Path(__file__).name} <build|overleaf> <contest-package-folder>"
        )
    mode = sys.argv[1]
    if mode not in {"build", "overleaf"}:
        raise SystemExit("mode must be one of: build, overleaf")
    return mode, sys.argv[2]



def prepare_build(package_name: str) -> BuildContext:
    contest_root = contest_root_for(package_name)
    if not contest_root.is_dir():
        raise SystemExit(f"missing contest package directory: {contest_root}")

    problems_dir = contest_root / "problems"
    statements_order_tex = contest_root / "statements" / "chinese" / "statements.tex"

    require_problems_dir(problems_dir, statements_order_tex)
    problems = collect_problems(problems_dir, statements_order_tex)
    if not problems:
        raise SystemExit(f"no problem directories found under {problems_dir}")
    prepare_build_dir(problems)
    update_contest_info(problem_count=len(problems), page_count=0)
    write_generated_tex(problems)
    return BuildContext(contest_root=contest_root, problems=problems)



def build_pdf(build: BuildContext) -> None:
    run_xelatex()
    page_count = extract_page_count()
    update_contest_info(problem_count=len(build.problems), page_count=page_count)
    run_xelatex()
    print(f"Built {MAIN_PDF}")



def main() -> None:
    mode, package_name = parse_args()
    build = prepare_build(package_name)
    if mode == "build":
        build_pdf(build)
    else:
        bundle_root = export_overleaf_bundle(build)
        print(f"Exported {bundle_root}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"build failed with exit code {exc.returncode}", file=sys.stderr)
        raise
