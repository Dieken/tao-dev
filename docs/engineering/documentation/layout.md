---
schema: tao.project.design/v0.1
id: DOC_20260914_Y5RR8BVF6065JTYP
title: 文档组织与产物保存
locale: zh-Hans
status: draft
created: '2026-09-14'
---

# 文档组织与产物保存

本文规定产品模板与出版实现的目标规则，落实 {need}`REQ_20260914_NN0AEQ2E1GTVSMTV`、{need}`REQ_20260914_3JQXRKWXKAZSNJ5R` 和 {need}`REQ_20260914_0J68SDKV86ENKER2`。[文档规程](../../../plugins/tao-dev/skills/tao-dev/references/documents.md) 和格式注册表维护使用方的统一格式与模板；本篇解释内容组织的设计理由。变更骨架生成、源文件格式与关系校验、本地书籍导航已实现。既有目录可映射；未接入格式不得宣称通过，结构校验也不代替内容语义审查。

<!-- tao:section overview -->
## 目标与边界

让项目文档随内容增长保持明确归属和可检查的结构。统一规则见 skill 的文档组织规程；本篇记录选择的理由。

<!-- tao:section architecture -->
## 内容组织

内容归属的权威规则见 [文档组织规程](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。设计依据是让长期规格、实现设计和一次变更各有唯一维护位置；书籍按主题组合阅读，不按流程阶段复制正文。

退役记录是项目自身的追溯数据，默认按退役日期存入 docs/retired/，随源文档保留；.tao/ 仅用于工具及 skill 配置。可重建状态使用生成产物目录，避免项目文档生命周期依赖某个工具的私有状态。日期分组控制文件增长，并不提供跨分支互斥；读取全部日期文件后仍需统一检查 ID 和替代关系。

保留 retired 命名，因为本记录描述已移除条目的追溯占位；deprecations 容易被理解为仍可使用的功能弃用通知。HTTP 领域的 [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html#section-5) 明确说明弃用本身不改变资源行为，[RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html#section-1) 另行处理停止服务的时间；这里只借鉴语义区别，不将 HTTP 标准当作文档目录命名规范。

### 篇章导航的实现取舍

采用有语义的子目录与统一 navigation profile，允许单页章和多页章，目录页只维护导读与阅读顺序。父子关系以 MyST toctree 为唯一来源，不在元数据中再存 parent／order，避免移动或重排需要同步多个索引；新的目录页仍使用 DOC，不引入另一套篇章编号系统。

Sphinx 的 toctree 支持嵌套目录，并由文档关系产生前后页导航；物理目录不是阅读顺序的唯一决定因素。MyST 可直接用 Markdown 围栏表达该指令，适合让 agent 和人工编辑同一份源目录。[Sphinx toctree](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-toctree)、[MyST 内容组织](https://myst-parser.readthedocs.io/en/latest/syntax/organising_content.html#using-toctree-to-include-other-documents-as-children)

未来出版实现从源目录提取图并检查闭环、重复主位置、漏挂、越界和指向排除文件等问题；不能只检查文件夹是否存在。运行规程定义可观察结果，具体 Sphinx 主题、HTML 侧栏与 PDF 篇章映射留在出版实现阶段验证；新增模板与静态夹具不构成真实书籍构建验收。目录只随实际内容建立，不为展示层级提前创建空篇章。

<!-- tao:section contracts -->
## 拆分与命名

### 拆分规则

任务数量、设计长度、并行写入与计划总长的阈值只在 [文档组织规程](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md) 维护。这些是控制维护负担的操作约定，不是行业质量标准；本项目不维护另一组自举阈值。

### 命名规则

变更计划按创建月份分组，默认路径为 `docs/changes/<yyyy-mm>/<yyyymmdd>-<slug>.md`；附件目录与计划同处该月份，年月与 created 及文件名日期一致。精确规则见 [文档组织规程](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。日期便于浏览，slug 区分同日目标；重名在创建或集成时显式处理，不需要跨开发者协调计数。调整文件名不会改变条目标识符。

<!-- tao:section invariants -->
## 自举与唯一来源

现有长期开发资料包括协议、格式契约、术语、文档组织、插件设计和 [命令设计](../cli-design.md)。协议维护 REQ／UC，decisions/ 中的独立文档维护长期 ADR，实施计划维护既有研发任务，专题文档维护实现设计并引用 skill 中的规则，README 只负责导航。它们是长期文档，保留语义文件名。

使用方模板及中英文显示资源已随 skill 提供，当前可手工填写；源文件校验器可运行，生成与出版能力仍需验收。后续以真实文件验证拆分前后 ID、退役记录、并发分配、证据保存和书籍构建；不能以模板存在宣称自动生成或校验已实现。

项目交付文档采用 skill 定义的 tao.project.* profile；本仓库的文档检查范围由 [文档契约](contract.md) 维护。格式检查与工具行为验收分别报告。

<!-- tao:section errors -->
## 重名与数据保护

创建文件时不覆盖已有计划或附件；跨分支合并需分别保留不同变更。路径解析后不越出项目，引用或退役关系损坏时报错。

<!-- tao:section verification -->
## 报告与验证

目录示意、报告类型、VCS 归属、持久保存与输入识别边界见 [文档组织规程](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。默认使用 tmp/tao/，以临时目录表达生成文件的可丢弃性，并允许复用项目已有生成目录；.tao/ 保持只放配置。普通验证结论随计划保存，原始日志默认不进 VCS；独立摘要与必要报告按需保留。产品实现需分别表示历史结果、原始材料可用性和当前复用资格，不能因日志过期取消历史任务完成状态。

拆分和移动后重新校验全局 ID、引用及导航关系；出版后另检查稳定入口。
