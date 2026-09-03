from __future__ import annotations

import queue
import shutil
import sys
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

from build import (
    ROOT,
    UserFacingError,
    build_pdf,
    cleanup_drop,
    ensure_runtime_assets,
    export_overleaf_bundle,
    output_paths_for,
    prepare_build,
    read_contest_info_values,
    set_contest_info,
)



class BuilderGUI:
    def __init__(self, root_window: tk.Tk) -> None:
        self.window = root_window
        self.window.title("ICPC Statement Builder")
        self.window.resizable(False, False)
        self.messages: queue.Queue[tuple[str, str]] = queue.Queue()
        self.worker: threading.Thread | None = None

        current = read_contest_info_values()

        frame = ttk.Frame(self.window, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")

        row = 0
        ttk.Label(frame, text="contest 包（zip 或文件夹）：").grid(row=row, column=0, sticky="w")
        self.package_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.package_var, width=46, state="readonly").grid(
            row=row, column=1, padx=6
        )
        ttk.Button(frame, text="选择 zip…", command=self.pick_package_zip).grid(row=row, column=2)
        ttk.Button(frame, text="选择文件夹…", command=self.pick_package_dir).grid(row=row, column=3)

        row += 1
        ttk.Label(frame, text="logo 图片（必选）：").grid(row=row, column=0, sticky="w")
        self.logo_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.logo_var, width=46, state="readonly").grid(
            row=row, column=1, padx=6
        )
        ttk.Button(frame, text="选择图片…", command=self.pick_logo).grid(row=row, column=2)
        ttk.Button(frame, text="清除", command=lambda: self.logo_var.set("")).grid(row=row, column=3)

        row += 1
        ttk.Label(frame, text="比赛名称：").grid(row=row, column=0, sticky="w")
        self.name_var = tk.StringVar(value=current.get("ContestName", ""))
        ttk.Entry(frame, textvariable=self.name_var, width=56).grid(
            row=row, column=1, columnspan=3, sticky="we", padx=6, pady=(8, 0)
        )

        row += 1
        ttk.Label(frame, text="主办方：").grid(row=row, column=0, sticky="w")
        self.organizer_var = tk.StringVar(value=current.get("ContestOrganizer", ""))
        ttk.Entry(frame, textvariable=self.organizer_var, width=56).grid(
            row=row, column=1, columnspan=3, sticky="we", padx=6, pady=(8, 0)
        )

        row += 1
        ttk.Label(frame, text="日期：").grid(row=row, column=0, sticky="w")
        self.date_var = tk.StringVar(value=current.get("ContestDate", ""))
        ttk.Entry(frame, textvariable=self.date_var, width=56).grid(
            row=row, column=1, columnspan=3, sticky="we", padx=6, pady=(8, 0)
        )

        row += 1
        self.pdf_mode = tk.BooleanVar(value=True)
        self.overleaf_mode = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text="生成 PDF（需要本地 XeLaTeX）", variable=self.pdf_mode).grid(
            row=row, column=1, sticky="w", padx=6, pady=(10, 0)
        )
        ttk.Checkbutton(frame, text="导出 Overleaf 目录", variable=self.overleaf_mode).grid(
            row=row, column=2, columnspan=2, sticky="w", pady=(10, 0)
        )

        row += 1
        self.generate_button = ttk.Button(
            frame, text="生成", command=self.start_generate
        )
        self.generate_button.grid(row=row, column=0, columnspan=4, sticky="we", pady=(12, 6))

        row += 1
        self.log = scrolledtext.ScrolledText(
            frame, width=72, height=14, state="disabled", wrap="word"
        )
        self.log.grid(row=row, column=0, columnspan=4, sticky="nsew", pady=(6, 0))

        self.window.after(100, self.drain_messages)

    def pick_package_zip(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 contest 包", filetypes=[("contest 包", "*.zip"), ("所有文件", "*.*")]
        )
        if path:
            self.package_var.set(path)

    def pick_package_dir(self) -> None:
        path = filedialog.askdirectory(title="选择 contest 文件夹")
        if path:
            self.package_var.set(path)

    def pick_logo(self) -> None:
        path = filedialog.askopenfilename(
            title="选择 logo 图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.pdf"), ("所有文件", "*.*")],
        )
        if path:
            self.logo_var.set(path)

    def log_line(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def drain_messages(self) -> None:
        while True:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "log":
                self.log_line(payload)
            elif kind == "done":
                self.generate_button.configure(state="normal")
                messagebox.showinfo("完成", payload)
            elif kind == "failed":
                self.generate_button.configure(state="normal")
                messagebox.showerror("失败", payload)
        self.window.after(100, self.drain_messages)

    def start_generate(self) -> None:
        package = self.package_var.get().strip()
        if not package:
            messagebox.showwarning("提示", "请先选择 contest 包（zip 或文件夹）。")
            return
        if not self.logo_var.get().strip():
            messagebox.showwarning("提示", "请先选择 logo 图片。")
            return
        if not self.pdf_mode.get() and not self.overleaf_mode.get():
            messagebox.showwarning("提示", "请至少勾选一种输出：生成 PDF 或导出 Overleaf 目录。")
            return
        # Read all tkinter variables here in the main thread; tkinter is not
        # thread-safe and must not be touched from the worker.
        job = {
            "package": package,
            "logo": self.logo_var.get().strip(),
            "name": self.name_var.get().strip(),
            "organizer": self.organizer_var.get().strip(),
            "date": self.date_var.get().strip(),
            "pdf": self.pdf_mode.get(),
            "overleaf": self.overleaf_mode.get(),
        }
        self.generate_button.configure(state="disabled")
        self.log_line(f"任务开始：{package}")
        self.worker = threading.Thread(target=self.run_build, args=(job,), daemon=True)
        self.worker.start()

    def run_build(self, job: dict) -> None:
        try:
            ensure_runtime_assets()
            logo = job["logo"]
            if logo:
                target = ROOT / "pic" / ("logo" + Path(logo).suffix.lower())
                target.parent.mkdir(parents=True, exist_ok=True)
                if Path(logo).resolve() != target.resolve():
                    shutil.copyfile(logo, target)
                set_contest_info(logo_path=target.relative_to(ROOT))
                self.post("log", f"logo 已设置为：{logo}")

            fields = {
                key: job[key]
                for key in ("name", "organizer", "date")
                if job[key]
            }
            if fields:
                set_contest_info(**fields)
                self.post("log", "比赛信息已写入 contest-info.tex")

            build = prepare_build(job["package"])
            self.post("log", f"已解析比赛包：{len(build.problems)} 道题")

            # Deliver outputs next to the selected contest package.
            pdf_target, overleaf_base = output_paths_for(Path(job["package"]))
            outputs = []
            if job["pdf"]:
                self.post("log", "正在编译 PDF（两遍 XeLaTeX，可能需要一两分钟）…")
                build_pdf(build)
                shutil.move(str(ROOT / "main.pdf"), str(pdf_target))
                outputs.append(f"PDF：{pdf_target}")
                self.post("log", f"PDF 编译完成：{pdf_target}")
            if job["overleaf"]:
                self.post("log", "正在导出 Overleaf 目录…")
                bundle = export_overleaf_bundle(build, destination_dir=overleaf_base)
                outputs.append(f"Overleaf 目录：{bundle}")
                self.post("log", f"Overleaf 导出完成：{bundle}")

            self.post(
                "done",
                "生成成功！\n\n" + "\n".join(outputs),
            )
        except UserFacingError as exc:
            self.post("failed", str(exc))
        except Exception:
            self.post("failed", "发生未预期的错误：\n\n" + traceback.format_exc())
        finally:
            cleanup_drop()

    def post(self, kind: str, payload: str) -> None:
        self.messages.put((kind, payload))



def enable_high_dpi() -> None:
    """Declare DPI awareness so Windows renders text sharply on scaled displays.

    Without this the system bitmap-stretches the whole window, which looks
    blurry at 125%/150% scaling. System-DPI awareness is the best tkinter
    supports reliably; dragging between monitors with different scaling may
    still rescale once.
    """
    if sys.platform != "win32":
        return
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass



def main() -> None:
    # Unpack the bundled templates before anything reads contest-info.tex;
    # on a frozen exe's very first run they do not exist next to the exe yet.
    ensure_runtime_assets()
    enable_high_dpi()
    window = tk.Tk()
    try:
        # Scale Tk fonts to the real display DPI now that we are DPI-aware,
        # before any widget is created, otherwise the UI would render sharp
        # but too small.
        window.tk.call("tk", "scaling", window.winfo_fpixels("1i") / 72.0)
    except tk.TclError:
        pass
    BuilderGUI(window)
    window.mainloop()


if __name__ == "__main__":
    main()
