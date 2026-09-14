---
schema: tao.document-layout/v0.2
id: DOC_20260914_Y5RR8BVF6065JTYP
title: 文档组织与产物保存
locale: zh-Hans
status: draft
created: "2026-09-14"
bootstrap: manual
---

# 文档组织与产物保存

本文规定产品模板与出版实现的目标规则，落实 {need}`REQ_20260914_NN0AEQ2E1GTVSMTV`、{need}`REQ_20260914_3JQXRKWXKAZSNJ5R` 和 {need}`REQ_20260914_0J68SDKV86ENKER2`。随包 [文档规程](../plugins/tao-dev/skills/tao-dev/references/documents.md) 和格式注册表维护使用方的统一格式与模板；本篇解释内容组织的设计理由。生成器与完整校验器尚未实现，既有目录可映射，未接入格式不得宣称通过。

<!-- tao:section ownership -->
## 一、内容放在哪里

内容归属的权威规则见随包 [文档组织规程](../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。设计依据是让长期规格、实现设计和一次变更各有唯一维护位置；书籍按主题组合阅读，不按流程阶段复制正文。

### 篇章导航的实现取舍

采用有语义的子目录与统一 navigation profile，允许单页章和多页章，目录页只维护导读与阅读顺序。父子关系以 MyST toctree 为唯一来源，不在元数据中再存 parent／order，避免移动或重排需要同步多个索引；新的目录页仍使用 DOC，不引入另一套篇章编号系统。

Sphinx 的 toctree 支持嵌套目录，并由文档关系产生前后页导航；物理目录不是阅读顺序的唯一决定因素。MyST 可直接用 Markdown 围栏表达该指令，适合让 agent 和人工编辑同一份源目录。[Sphinx toctree](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-toctree)、[MyST 内容组织](https://myst-parser.readthedocs.io/en/latest/syntax/organising_content.html#using-toctree-to-include-other-documents-as-children)

未来出版实现从源目录提取图并检查闭环、重复主位置、漏挂、越界和指向排除文件等问题；不能只检查文件夹是否存在。运行规程定义可观察结果，具体 Sphinx 主题、HTML 侧栏与 PDF 篇章映射留在出版实现阶段验证；新增模板与静态夹具不构成真实书籍构建验收。本项目既有文档待单独迁移，不为展示层级提前创建空篇章。

<!-- tao:section splitting -->
## 二、变更文件的固定拆分规则

任务数量、设计长度、并行写入与计划总长的阈值只在 [随包组织规程](../plugins/tao-dev/skills/tao-dev/references/document-layout.md) 维护。这些是控制维护负担的操作约定，不是行业质量标准；本项目不维护另一组自举阈值。

<!-- tao:section naming -->
## 三、日期与命名

变更文件以创建日期与语义 slug 命名，精确规则见 [随包组织规程](../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。日期便于浏览，slug 区分同日目标；重名在创建或集成时显式处理，不需要跨开发者协调计数。调整文件名不会改变条目标识符。

<!-- tao:section artifacts -->
## 四、报告与证据保存

目录示意、报告类型、VCS 归属、持久保存与输入指纹边界见 [随包组织规程](../plugins/tao-dev/skills/tao-dev/references/document-layout.md)。artifacts/ 是可重建执行产物，不能作为长期完成声明的唯一依据；产品实现需验证清理与证据引用的关系。

<!-- tao:section bootstrap -->
## 五、本项目自举边界

现有长期开发资料包括协议、格式契约、术语、文档组织、插件设计和 [命令设计](cli-design.md)。协议维护 REQ／UC／ADR 和实施路线，专题文档维护实现设计并引用随包规则，README 只负责导航。它们是长期文档，保留语义文件名。

使用方模板及中英文显示资源已随 skill 提供，当前可手工填写；完整脚本尚未实现。后续以真实文件验证拆分前后 ID、退役记录、并发分配、证据保存和书籍构建；不能以模板存在宣称自动生成或校验已实现。

新建项目交付文档采用随包 tao.project.* profile；现有六篇长期文档的内部 profile 是待迁移范围，不作为新文档模板，也不宣称已经通过共享格式校验。整体迁移需要单独规划条目位置与引用，保留已有 ID 和项目内容。自举从实际使用随包规则、模板和项目局部入口开始，完整格式迁移与工具验收分别报告。
