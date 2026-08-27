# M3DC1-docs

M3D-C1 `C1input` 参数用户指南与源码快照。

本仓库面向运行 M3D-C1 case 的用户，参数说明以仓库内保存的 M3D-C1 源码实际读取和使用行为为准，并将托卡马克与仿星器的设置路径分别说明。该整理文档不是 Princeton University 或 PPPL 的官方文档。

## 在线阅读

- GitHub Pages：<https://yihui-l.github.io/M3DC1-docs/>
- 仓库内入口：[index.html](./index.html)

克隆仓库后，也可以直接在浏览器中打开 `Documents/index.html`：

```bash
git clone https://github.com/Yihui-L/M3DC1-docs.git
cd M3DC1-docs
open Documents/index.html
```

页面使用 MathJax CDN 排版 LaTeX 公式。离线时正文仍可阅读，公式会保留为 LaTeX 原文。

## 目录

- `../M3DC1/`：未经修改的上游 M3D-C1 源码快照，不包含上游 `.git` 历史。
- `index.html`：参数指南网页与 GitHub Pages 发布内容。
- `docs-data/`：完整参数表、简化表、源码使用统计、官方文档差异清单和输入模板。
- `tools/extract_m3dc1_params.py`：从相邻 `M3DC1/` 源码快照重新生成参数资料的脚本。
- `SOURCE_VERSION.md`：上游来源、提交版本和同步说明。

## 源码来源

上游项目：<https://github.com/PrincetonUniversity/M3DC1>

本仓库中的 M3D-C1 源码遵循其原许可证，详见 [`M3DC1/LICENSE`](../M3DC1/LICENSE)。

## 更新网页

在仓库根目录运行：

```bash
python3 Documents/tools/extract_m3dc1_params.py
```

生成脚本当前仍按本次整理工作区的源码结构设计。更新上游版本后，应重新核查参数注册、默认值和实际使用分支，再发布新的网页。
