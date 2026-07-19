# Icpc Statement Builder

Icpc Statement Builder 可以根据 polygon 打包出来的 contest package 中的 `problems/` 和 `statements/` 两个目录，自动组装成一整本 ICPC/CCPC 风格的**中文** PDF 题面。

## 用法

1. 在根目录克隆本仓库：

```bash
$ git clone https://github.com/nopostpone/icpc-statement-builder.git
```

2. 把 polygon 打包出来的 contest package 解压，将 `problems/` 和 `statements/` 两个目录复制到根目录下。
4. 把比赛 logo 放到 `pic/logo.png`。
5. 运行代码编译：

```bash
python build.py
```

该脚本会：
- 读取 `statements/chinese/statements.tex` 中的题目顺序与题号
- 扫描 `problems/`
- 读取每道题的 `statements/chinese/problem.tex`
- 生成 `generated-problems.tex`
- 调用 XeLaTeX 编译 `main.tex`

## 约定

- 当前版本默认只读取中文题面：`problems/<slug>/statements/chinese/problem.tex`
- 比赛信息写在 `contest-info.tex`
- `\ContestProblemCount` 和 `\ContestPageCount` 由 `build.py` 自动回填，请不要手动维护
- 封面 logo 大小默认由 `\ContestLogoWidth` 控制，可按需要手动调整
- 封面 logo 不属于 `problems/`，统一使用项目资源路径：`pic/logo.png`
- `main.tex` 作为主模板，尽量不需要手动修改

## 依赖

- Python 3.10+
- XeLaTeX

## 输出

默认会在项目根目录生成：
- `generated-problems.tex`
- `main.pdf`
- `.build/`（中间生成文件）
