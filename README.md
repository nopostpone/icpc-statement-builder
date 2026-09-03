# ICPC Statement Builder

polygon 自带的 sty 文件对中文支持不佳，无法直接编译中文题面。

ICPC Statement Builder 可以根据 polygon 打包出来的完整 contest package，自动组装成一整本 ICPC/CCPC 风格的**中文** PDF 题面。

> 仍然有一些问题，比如对客制化内容支持不佳（大尺寸图片会超出去、样例中非常长的一行无法换行等），这些需要自己到题目的 tex 文件中改。

## 用法

1. 在根目录克隆本仓库：

```bash
git clone https://github.com/nopostpone/icpc-statement-builder.git
```

2. 把 polygon 打包出来的 contest package 解压，并将整个文件夹复制到仓库根目录下；或者直接保留 zip，后面的命令和 exe 都支持 zip / 文件夹 两种输入。
3. 把比赛 logo 放到 `pic/logo.png`。
4. 根据你的比赛信息，编辑 `contest-info.tex`，修改比赛名称、日期、主办方等。
5. 根据需要选择运行模式：

本地 XeLaTeX 直接编译：

```bash
python build.py build <contest-package-folder-or-zip>
```

导出一个目录，可以直接上传至 Overleaf 或其他在线 LaTeX 平台进行编译：

```bash
python build.py overleaf <contest-package-folder-or-zip>
```

例如，如果你的 contest package 名字是 `contest-123`，我需要本地编译一个题面 pdf，那么在根目录解压 `contest-123.zip` 后：

```bash
python build.py build contest-123
```

如果手上只有 zip，也可以直接：

```bash
python build.py build contest-123.zip
```

如果还想要导出成一个目录上传到 Overleaf，运行：

```bash
python build.py overleaf contest-123
```

或者：

```bash
python build.py overleaf contest-123.zip
```

Windows 拖拽使用时，可以直接把 zip 或 contest 文件夹拖到以下程序上：
- `icpc-statement-builder-pdf.exe`：生成本地 PDF
- `icpc-statement-builder-overleaf.exe`：导出 Overleaf 目录

两个 exe 均可独立运行：首次运行时会把 `main.tex`、`contest-info.tex`、`styles/`、`pic/` 解包到 exe 所在目录，之后可直接修改旁边的 `contest-info.tex` 和 `pic/logo.png`，无需重新打包。
该脚本会：
- 读取 `<contest-package-folder-or-zip>` 对应 contest 中 `statements/chinese/statements.tex` 的题目顺序与题号
- 扫描 `problems/`
- 读取每道题的 `problems/<slug>/statements/chinese/problem.tex`
- 生成 `generated-problems.tex`
- 在 `build` 模式下调用 XeLaTeX 编译 `main.tex`
- 在 `overleaf` 模式下生成自包含的 Overleaf 导出目录

## 文件职责

- `main.tex`：主模板，负责加载宏包、样式文件和题面输出
- `contest-info.tex`：比赛配置文件，保存比赛名称、主办方、日期、logo，以及由 `build.py` 自动回填的题数和页数
- `styles/olymp.sty`：Polygon 题面排版层，负责 `problem`、输入输出、样例等环境
- `styles/contest-style.sty`：本项目固定布局层，负责封面、页眉页脚等宏

## 约定

- 当前版本默认只读取中文题面：`<contest-package-folder>/problems/<slug>/statements/chinese/problem.tex`
- `contest-info.tex` 中的 `\ContestProblemCount` 由 `build.py` 自动回填，请不要手动维护；封面与页脚的页数通过 `\pageref{LastPage}` 自动解析，本地编译和 Overleaf 上均无需维护
- 封面 logo 大小默认由 `\ContestLogoWidth` 控制，可按需要手动调整
- 封面 logo 不属于 Polygon package，统一使用项目资源路径：`pic/logo.png`
- `main.tex` 作为主模板，尽量不需要手动修改

## 依赖

- Python 3.10+
- XeLaTeX（本地 PDF 编译需要；仅导出 Overleaf 目录时不需要）

## 打包为 exe

### 自动发布（推荐）

推送一个 `v` 开头的 tag（如 `v1.0.0`），GitHub Actions 会自动在 Windows 环境打包两个 exe 并发布到 Releases：

```bash
git tag v1.0.0
git push origin v1.0.0
```

也可以在仓库的 Actions 页面手动触发（Run workflow），仅构建并生成可下载的 artifact，不创建 Release。

### 本地打包

```bash
pyinstaller pdf.spec
pyinstaller overleaf.spec
```

生成后在 `dist/` 中可得到：
- `icpc-statement-builder-pdf.exe`
- `icpc-statement-builder-overleaf.exe`

这两个 exe 都支持把 contest zip 或已解压的 contest 文件夹直接拖到程序图标上运行。

## 输出

`build` 模式默认会在项目根目录生成：
- `generated-problems.tex`
- `main.pdf`
- `.build/`（中间生成文件）

`overleaf` 模式会额外生成：
- `exports/<contest-package-folder>/overleaf/`（整理后的导出目录）

Overleaf 导出目录中只包含编译所需文件，例如：
- `main.tex`
- `contest-info.tex`
- `generated-problems.tex`
- `styles/`
- `pic/` 中实际被引用的 logo
- `problems/<slug>/problem.tex`
- `problems/<slug>/assets/`
