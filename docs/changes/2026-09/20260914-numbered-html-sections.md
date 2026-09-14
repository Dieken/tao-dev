---
schema: tao.project.change/v0.1
id: DOC_20260914_Z9JYQ4JG1V0VPA52
title: Sphinx HTML 章节显示编号
locale: zh-Hans
status: draft
created: "2026-09-14"
change: CHG_20260914_4FMEGWFGCT4HCYPN
---

# Sphinx HTML 章节显示编号

<!-- tao:section scope -->
## 目标与边界

`tao docs build` 为纳入主目录树的 HTML 章节显示按阅读顺序生成的数字编号；编号只属于出版显示，不写入标题、正式 ID、章节键或 URL。调整章节顺序后允许编号变化，现有固定入口和标题永久链接仍须解析到同一正式对象。

本次修改覆盖 Sphinx HTML 构建、出版回归测试和随 skill 分发的文档规程。不改变源 Markdown schema、ID 格式、目录文件命名、PDF 行为或外部站点迁移规则。

<!-- tao:section references -->
## 规格引用

文档层级、阅读顺序和显示编号的既有约束见 [文档组织规程](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md)；稳定锚点和实际 HTML 验收见 [出版规程](../../../plugins/tao-dev/skills/tao-dev/references/publication.md)。

<!-- tao:section design -->
## 设计

Sphinx 扩展先在根 toctree 的 AST 节点上设置 `numbered`，启动 Sphinx 对正文和导航的完整编号流程。标准目录收集完成后，扩展读取已校验的导航图，为每份页面分配由父级位置和同级顺序组成的编号，再从页面目录节点生成内容章节的后续层级，并把结果同步到标题编号表和 TOC 引用节点。navigation 页本身取得所在篇章编号，但固定的导读和目录标题显式不编号，避免结构性包装制造虚假深度。目录顺序仍由源 toctree 唯一决定；使用方不需要在每份导航文档重复填写出版选项。

编号由 Sphinx 作为标题的显示节点输出。现有扩展继续把首页、二级章节和正式条目的 DOM `id` 替换为稳定 ID，并把标题永久链接重写到 `refs/<DOC-ID>.html#<stable-fragment>`。构建验收直接检查可见编号与 href，避免从配置存在推断结果正确。

<!-- tao:section tasks -->
## 任务

- [x] `TASK_20260914_70KWBRARDN0W1NF0` 生成章节显示编号并保持固定链接
  - relates: ["CHG_20260914_4FMEGWFGCT4HCYPN"]
  - depends_on: []
  - verify: 先确认缺少编号的 HTML 回归测试按预期失败；实现后测试显示编号、稳定 DOM ID、固定永久链接及重排后 href 不变，并完成文档校验和实际书籍构建。
  - evidence: [本计划验证记录](20260914-numbered-html-sections.md#DOC_20260914_Z9JYQ4JG1V0VPA52--verification)

<!-- tao:section verification -->
## 验证

受检实现固定为提交 `a4a97294b3ca8085aae0a69385587cfa9e41f241`。记录时间为 `2026-09-15T00:04:26+08:00`，环境为 Darwin、Python 3.12.13、Sphinx 9.1.0。

测试先后观察到三种预期失败：原输出没有编号；直接启用 Sphinx numbered toctree 时，navigation 页的固定章节制造了 `1.2.1` 虚假深度；改由导航图计算后，固定导读标题又因 Sphinx 回退到页编号而重复显示 `1`。每项均在相应实现前得到失败结果，并在最小修正后通过。

| 检查 | 结果 |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_publication.py tests/test_relationships.py` | 38 项通过；覆盖嵌套导航、同级重排、navigation 标题排除、稳定 DOM ID 与永久链接 |
| `.venv/bin/python -m pytest -q` | 237 项通过，耗时 287.82 秒 |
| `.venv/bin/python -m ruff check --select E9,F63,F7,F82 plugins/tao-dev/skills/tao-dev/scripts tests` | 通过，无诊断 |
| skill 快速校验 | `Skill is valid!` |
| 全部开发文档源校验 | 28 份文档、81 个定义通过结构与关系校验 |
| 本项目 Sphinx HTML 构建 | 81 个定义、0 个章节重定向；稳定链接检查通过 |

实际 HTML 抽查显示产品规格为 `1.1`、其二级章节为 `1.1.1`，多页工程章为 `2.2.1`；navigation 页的导读和目录标题没有编号。标题链接仍使用 `refs/<DOC-ID>.html#<stable-fragment>`，显示编号没有进入 href。生成书籍保存在忽略的 `tmp/tao/book/`，原始命令输出未纳入 VCS。

隔离的 tao 核心运行时未准备，因此没有通过 CLI 汇总完整 `tao verify` receipt；本记录直接保存实际检查结果。项目配置要求的独立实现审查也未在本任务中执行，所以这里只确认本项实现与回归结果，不据此声明整个项目达到发布就绪状态。

<!-- tao:section questions -->
## 未决问题

无。显示编号属于 HTML 出版层，源文档及正式引用继续只使用稳定 ID。
