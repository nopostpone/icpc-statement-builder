from __future__ import annotations

import sys
import traceback

from build import UserFacingError, cleanup_drop, run_pdf_mode



def pause_before_exit() -> None:
    try:
        input("\nPress Enter to close...")
    except EOFError:
        pass



def main() -> None:
    if len(sys.argv) != 2:
        raise UserFacingError("Usage: app-pdf.py <contest-package-folder-or-zip>")
    run_pdf_mode(sys.argv[1])


if __name__ == "__main__":
    try:
        main()
    except UserFacingError as exc:
        print(exc, file=sys.stderr)
        pause_before_exit()
        raise SystemExit(1) from exc
    except Exception:
        traceback.print_exc()
        pause_before_exit()
        raise SystemExit(1) from exc
    cleanup_drop()
