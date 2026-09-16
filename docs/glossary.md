---
schema: tao.project.glossary/v0.1
id: DOC_20260914_728EZ364G48T3QRK
title: 术语与缩写
locale: zh-Hans
status: draft
created: '2026-09-14'
---

# 术语与缩写

通用术语由 skill 的运行参考定义；本文提供本项目的语境说明和阅读入口，使用方的领域术语仍由其项目自己维护。

<!-- tao:section terms -->
## 术语与类型

标识符、对象同一性、规格、设计、证据与审查等概念统一见 [术语表](../plugins/tao-dev/skills/tao-dev/references/glossary.md)。

```{term} 自举
:english: Self-hosting
:scope: tao-dev development

用本仓库内的 skill 源码及其规则开发 tao-dev；无需将产品全局安装。
```

### ID 类型前缀

DOC、REQ、UC、ADR、TASK、CHG、EVD 的英文全称、用途及区别在 [术语表](../plugins/tao-dev/skills/tao-dev/references/glossary.md) 定义；精确语法由 [文档规程](../plugins/tao-dev/skills/tao-dev/references/documents.md) 与 [格式注册表](../plugins/tao-dev/skills/tao-dev/assets/document-profiles.json) 定义，不在这里重复。

<!-- tao:section abbreviations -->
## 缩写与使用规则

SDD 的项目特定含义见 [术语表](../plugins/tao-dev/skills/tao-dev/references/glossary.md)。VCS（版本控制系统）、CLI（命令行接口）、AST（抽象语法树）与 i18n（国际化）沿用通常技术含义。当前完整开发流程依赖 Git；独立文档校验不要求版本控制系统。

### 本项目用语

通用用词规则见术语表。tao-dev 自身以简体中文维护权威正文，代码标识、文件名、机器字段与提交日志使用英文；这不限制使用方语言。理由见 {need}`ADR_20260914_WX7BFBRXENPN4CT7`，模板和诊断遵循 [本地化规程](../plugins/tao-dev/skills/tao-dev/references/localization.md)。
