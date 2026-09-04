[English version](README.en.md)

# ICPC Statement Builder

polygon 自带的 sty 文件对中文支持不佳，无法直接编译中文题面。

ICPC Statement Builder 可以根据 polygon 导出的完整 contest package，自动组装成一整本 ICPC/CCPC 风格的**中文** PDF 题面。

> 已知限制：对客制化内容支持不佳（大尺寸图片会超出去、样例中非常长的一行无法换行等），这些需要自己到题目的 tex 文件中改。

## 快速开始（推荐）

1. 从 [Releases](https://github.com/nopostpone/icpc-statement-builder/releases/latest) 下载 `icpc-statement-builder.exe`。
2. 准备两样东西：
   - **contest 包**：从 **Polygon** 导出的完整 contest package（zip 或文件夹均可）。**务必确保里面已经录入中文题面**（即存在 `statements/chinese/`），否则无法使用；
   - **logo 图片**：用于封面和页眉的 logo。
3. 运行 exe，该 exe 是一个简易的 gui 页面，在页面中你需要：
   1. 选择 contest 包和 logo 图片（均**必选**）；
   2. 按需填写比赛名称、主办方、日期；
   3. 勾选「生成 PDF」和/或「导出 Overleaf 目录」，点击「生成」。「生成 PDF」需要本地有 XeLaTeX。

生成的文件位置在你选的 contest 包的所在目录：`<包名>.pdf` 与 `<包名>/overleaf/`，后者可直接上传至 Overleaf 后使用 XeLaTeX 来编译。

## 从源码运行

```bash
git clone https://github.com/nopostpone/icpc-statement-builder.git
cd icpc-statement-builder
```

依赖：Python 3.10+；本地编译 PDF 还需要 XeLaTeX（仅导出 Overleaf 目录时不需要）。contest 包的准备方式与「快速开始」相同。

```bash
# 本地编译 PDF（在项目根目录生成 main.pdf）
python build.py build <contest-package-folder-or-zip>

# 导出 Overleaf 目录（在 exports/<包名>/overleaf/）
python build.py overleaf <contest-package-folder-or-zip>
```

## 文件职责

- `app-gui.py`：图形界面入口，发布的 exe 由它打包而成
- `build.py`：核心引擎，同时是命令行入口——解析比赛包、读取题面顺序与题号、组装 LaTeX、调用 XeLaTeX、导出 Overleaf 目录
- `main.tex`：主模板，负责加载宏包、样式文件和题面输出
- `contest-info.tex`：比赛配置文件，保存比赛名称、主办方、日期、logo 路径；题数由 `build.py` 自动回填
- `generated-problems.tex`：由 `build.py` 生成的题面汇总文件（勿手动编辑）
- `styles/olymp.sty`：Polygon 题面排版层，负责 `problem`、输入输出、样例等环境
- `styles/contest-style.sty`：本项目固定布局层，负责封面、页眉页脚等宏
- `gui.spec` / `pdf.spec` / `overleaf.spec`：PyInstaller 打包配置（GUI 版 / 旧版拖拽版）
- `.build/`、`exports/`：运行时的中间产物目录与命令行模式的导出目录

## 约定

- 当前版本默认只读取中文题面：`<contest-package-folder>/problems/<slug>/statements/chinese/problem.tex`
- `contest-info.tex` 中的 `\ContestProblemCount` 由 `build.py` 自动回填，请不要手动维护；封面与页脚的页数通过 `\pageref{LastPage}` 自动解析，本地编译和 Overleaf 上均无需维护
- 封面 logo 大小默认由 `\ContestLogoWidth` 控制，可按需要手动调整
- 封面 logo 不属于 Polygon package，统一使用项目资源路径：`pic/logo.png`（仓库不自带，需自行提供）
- `main.tex` 作为主模板，尽量不需要手动修改
