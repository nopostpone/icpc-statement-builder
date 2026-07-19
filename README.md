# icpc-statement-builder

`icpc-statement-builder` 用来把一份 `problems/` 目录自动组装成一整本 ICPC/ACM 风格的中文 PDF 题面。

## 用法

1. 克隆本仓库。
2. 把题库目录复制到项目根目录，目录名必须为 `problems/`。
3. 把比赛 statement 目录复制到项目根目录，目录名必须为 `statements/`。
4. 把比赛 logo 放到 `pic/logo.png`。
5. 运行：

```bash
python build.py
```

脚本会：
- 读取 `statements/chinese/statements.tex` 中的题目顺序与题号
- 扫描 `problems/`
- 读取每道题的 `statements/chinese/problem.tex`
- 生成 `generated-problems.tex`
- 调用 XeLaTeX 编译 `main.tex`

## 约定

- 当前版本默认只读取中文题面：`problems/<slug>/statements/chinese/problem.tex`
- 题目顺序与题号来自 `statements/chinese/statements.tex`，不再按目录名字典序猜测
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
