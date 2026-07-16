# icpc-statement-builder

`icpc-statement-builder` 用来把一份 `problems/` 目录自动组装成一整本 ICPC/ACM 风格的中文 PDF 题面。

## 用法

1. 克隆本仓库。
2. 把题库目录复制到项目根目录，目录名必须为 `problems/`。
3. 运行：

```bash
python build.py
```

脚本会：
- 扫描 `problems/`
- 读取每道题的 `statements/chinese/problem.tex`
- 生成 `generated-problems.tex`
- 调用 XeLaTeX 编译 `main.tex`

## 约定

- 当前版本默认只读取中文题面：`problems/<slug>/statements/chinese/problem.tex`
- 题目顺序默认按题目目录名排序
- 比赛信息写在 `contest-info.tex`
- `main.tex` 作为主模板，尽量不需要手动修改

## 依赖

- Python 3.10+
- XeLaTeX

## 输出

默认会在项目根目录生成：
- `generated-problems.tex`
- `main.pdf`
- `.build/`（中间生成文件）
