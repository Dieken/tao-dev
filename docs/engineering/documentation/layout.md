---
schema: tao.project.design/v0.1
id: DOC_20260914_Y5RR8BVF6065JTYP
title: 文档组织与产物保存
locale: zh-Hans
status: draft
created: '2026-09-14'
updated: "2026-09-18"
spec_docs: ["DOC_20260914_4C7N0XHQSP7CY69P"]
---

# 文档组织与产物保存

本文规定产品模板与出版实现的目标规则，落实 {need}`REQ_20260914_NN0AEQ2E1GTVSMTV`、{need}`REQ_20260914_3JQXRKWXKAZSNJ5R` 和 {need}`REQ_20260914_0J68SDKV86ENKER2`。[文档规程](../../../plugins/tao-dev/skills/tao-dev/references/documents.md) 和格式注册表维护使用方的统一格式与模板；本篇解释内容组织的设计理由。变更骨架生成、源文件格式与关系校验、本地书籍导航已实现。既有目录可映射；未接入格式不得宣称通过，结构校验也不代替内容语义审查。

<!-- tao:section overview -->
## 目标与边界

让项目文档随内容增长保持明确归属和可检查的结构。统一规则见 skill 的文档组织规程；本篇记录选择的理由。

<!-- tao:section architecture -->
## 内容组织

内容归属的权威规则见 [文档组织](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。设计依据是让长期规格、实现设计和一次变更各有唯一维护位置；书籍按主题组合阅读，不按流程阶段复制正文。

退役记录是项目自身的追溯数据，默认按退役日期存入 docs/retired/，随源文档保留；.tao/ 保存项目配置和必要工作流检查点；可重建缓存使用生成产物目录。正式任务和交接仍使用受管理文档，文档读取与索引不要求运行某个客户端。日期分组控制文件增长，并不提供跨分支互斥；读取全部日期文件后仍需统一检查 ID 和替代关系。

保留 retired 命名，因为本记录描述已移除条目的追溯占位；deprecations 容易被理解为仍可使用的功能弃用通知。HTTP 领域的 [RFC 9745](https://www.rfc-editor.org/rfc/rfc9745.html#section-5) 明确说明弃用本身不改变资源行为，[RFC 8594](https://www.rfc-editor.org/rfc/rfc8594.html#section-1) 另行处理停止服务的时间；这里只借鉴语义区别，不将 HTTP 标准当作文档目录命名规范。

### 篇章导航的实现取舍

采用有语义的子目录与统一 navigation profile，允许单页章和多页章，目录页只维护导读与阅读顺序。父子关系以 MyST toctree 为唯一来源，不在元数据中再存 parent／order，避免移动或重排需要同步多个索引；新的目录页仍使用 DOC，不引入另一套篇章编号系统。

Sphinx 的 toctree 支持嵌套目录，并由文档关系产生前后页导航；物理目录不是阅读顺序的唯一决定因素。MyST 可直接用 Markdown 围栏表达该指令，适合让 agent 和人工编辑同一份源目录。[Sphinx toctree](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-toctree)、[MyST 内容组织](https://myst-parser.readthedocs.io/en/latest/syntax/organising_content.html#using-toctree-to-include-other-documents-as-children)

出版实现从源目录提取图并检查环、重复主位置、漏挂、越界和指向排除文件的问题。HTML 构建器在根 toctree 的 AST 节点上启用 Sphinx numbered 属性；标准收集完成后，按已校验的导航图校正编号表与 TOC 引用节点，使正文、左侧书籍导航和页内目录共用编号。navigation 页保留页标题编号，排除固定导读和目录标题造成的虚假层级。

<!-- tao:section contracts -->
## 拆分与命名

### 拆分规则

任务数量、并行写入与计划总长的阈值只在 [文档组织](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md) 维护。这些是控制维护负担的操作约定，不是行业质量标准；本项目不维护另一组自举阈值。

### 命名规则

变更计划按创建月份分组，默认路径为 `docs/plans/<yyyy-mm>/<yyyymmdd>-<slug>.md`；附件目录与计划同处该月份，年月与 created 及文件名日期一致。精确规则见 [文档组织](../../../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。日期便于浏览，slug 区分同日目标；重名在创建或集成时显式处理，不需要跨开发者协调计数。调整文件名不会改变条目标识符。

<!-- tao:section invariants -->
## 自举与唯一来源

现有长期开发资料包括协议、格式契约、术语、文档组织、插件设计和 [命令设计](../cli-design.md)。协议维护 REQ／UC，decisions/ 中的独立文档维护长期 ADR，实施计划维护既有研发任务，专题文档维护实现设计并引用 skill 中的规则，README 只负责导航。它们是长期文档，保留语义文件名。

使用方模板及中英文显示资源随 skill 提供，生成器、源文件校验器和 HTML 出版层使用同一契约。当前能力以工具规程及 doctor 为准；具体版本的实测结果保留在变更记录中。

项目交付文档采用 skill 定义的 tao.project.* profile；本仓库的文档检查范围由 [文档契约](contract.md) 维护。格式检查与工具行为验收分别报告。

<!-- tao:section errors -->
## 重名与数据保护

创建文件时不覆盖已有计划或附件；跨分支合并需分别保留不同变更。路径解析后不越出项目，引用或退役关系损坏时报错。

<!-- tao:section verification -->
## 报告与验证

目录示意、报告类型、VCS 归属、持久保存与输入识别边界见 [证据保存](../../../plugins/tao-dev/skills/tao-dev/references/evidence-retention.md)。默认使用 tmp/tao/，以临时目录表达生成文件的可丢弃性，并允许复用项目已有生成目录；.tao/ 保存配置及不可当作缓存丢弃的工作流检查点。普通验证结论随计划保存，原始日志默认不进 VCS；独立摘要与必要报告按需保留。正式审查报告与裁决沿用 evidence profile；计划前或跨事项的报告归工程篇 reviews/，有计划时归计划附件。这样审查所有产品、设计及代码的结论具有统一入口，同时保持与本次事项的关系；无须为 review 新建平行 schema。产品实现需分别表示历史结果、原始材料可用性和当前复用资格，不能因日志过期取消历史任务完成状态。

拆分和移动后重新校验全局 ID、引用及导航关系。出版回归覆盖正文、左侧导航和页内目录的编号一致性、编号重排、标题更新、特殊字符、改名、退役说明及失效删除；实际访问旧稳定入口，不能从 AST 或配置存在推导链接可用。

### 出版器回归

修改出版实现时，在测试项目中构建 HTML，检查正文、左侧导航和页内目录的编号一致性、唯一 DOM 锚点、引用文字与复制链接。再改标题、移动文件、重排导航并重访旧固定入口；编号可变，href 不包含显示编号。该变动序列属于出版器回归，使用方项目日常构建只检查实际生成结果及本次受影响入口。

覆盖引用标题的纯文本转义、无标题时回退 ID、退役说明及替代目标、前向与反向关系表和内嵌任务链接；无关系时不生成空表。章节重定向按片段定位，即使旧 DOC 退役仍生成入口，禁用 JavaScript 时提供普通链接。构建与源检查共用索引，失败不替换旧书籍。
