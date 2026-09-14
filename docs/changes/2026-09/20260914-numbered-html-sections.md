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

Sphinx 扩展在读取书籍根文档的 doctree 时，对其唯一的主 toctree 启用章节编号。编号深度沿用 Sphinx 的完整章节编号能力，目录顺序仍由源 toctree 唯一决定；使用方不需要在每份导航文档重复填写出版选项。

编号由 Sphinx 作为标题的显示节点输出。现有扩展继续把首页、二级章节和正式条目的 DOM `id` 替换为稳定 ID，并把标题永久链接重写到 `refs/<DOC-ID>.html#<stable-fragment>`。构建验收直接检查可见编号与 href，避免从配置存在推断结果正确。

<!-- tao:section tasks -->
## 任务

- [ ] `TASK_20260914_70KWBRARDN0W1NF0` 生成章节显示编号并保持固定链接
  - relates: ["CHG_20260914_4FMEGWFGCT4HCYPN"]
  - depends_on: []
  - verify: 先确认缺少编号的 HTML 回归测试按预期失败；实现后测试显示编号、稳定 DOM ID、固定永久链接及重排后 href 不变，并完成文档校验和实际书籍构建。

<!-- tao:section verification -->
## 验证

计划执行出版单元测试、完整文档校验和本项目书籍构建。结果在实现完成后记录；当前尚未执行，不能据此判断交付完成。

<!-- tao:section questions -->
## 未决问题

无。显示编号属于 HTML 出版层，源文档及正式引用继续只使用稳定 ID。
