# Icpc Statement Builder

Icpc Statement Builder 可以根据 polygon 打包出来的完整 contest package，自动组装成一整本 ICPC/CCPC 风格的**中文** PDF 题面。

## 用法

1. 在根目录克隆本仓库：

```bash
git clone https://github.com/nopostpone/icpc-statement-builder.git
```

2. 把 polygon 打包出来的 contest package 解压，并将整个文件夹复制到仓库根目录下。
3. 把比赛 logo 放到 `pic/logo.png`。
4. 如需修改比赛名称、日期、主办方或 logo 等配置，编辑 `contest-info.tex`。
5. 运行代码编译：

```bash
python build.py <contest-package-folder>
```

例如：

```bash
python build.py contest-59409
```

该脚本会：
- 读取 `<contest-package-folder>/statements/chinese/statements.tex` 中的题目顺序与题号
- 扫描 `<contest-package-folder>/problems/`
- 读取每道题的 `problems/<slug>/statements/chinese/problem.tex`
- 生成 `generated-problems.tex`
- 调用 XeLaTeX 编译 `main.tex`

## 文件职责

- `main.tex`：主模板，负责加载宏包、样式文件和题面输出
- `contest-info.tex`：比赛配置文件，保存比赛名称、主办方、日期、logo，以及由 `build.py` 自动回填的题数和页数
- `styles/olymp.sty`：Polygon 题面排版层，负责 `problem`、输入输出、样例等环境
- `styles/contest-style.sty`：本项目固定布局层，负责封面、页眉页脚等宏

## 约定

- 当前版本默认只读取中文题面：`<contest-package-folder>/problems/<slug>/statements/chinese/problem.tex`
- `contest-info.tex` 中的 `\ContestProblemCount` 和 `\ContestPageCount` 由 `build.py` 自动回填，请不要手动维护
- 封面 logo 大小默认由 `\ContestLogoWidth` 控制，可按需要手动调整
- 封面 logo 不属于 Polygon package，统一使用项目资源路径：`pic/logo.png`
- `main.tex` 作为主模板，尽量不需要手动修改

## 依赖

- Python 3.10+
- XeLaTeX

## 输出

默认会在项目根目录生成：
- `generated-problems.tex`
- `main.pdf`
- `.build/`（中间生成文件）
