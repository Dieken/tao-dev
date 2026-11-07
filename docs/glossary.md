---
schema: tao.project.glossary/v0.1
id: DOC_20260914_728EZ364G48T3QRK
title: 术语与缩写
locale: zh-Hans
status: draft
---

# 术语与缩写

通用术语由技能附带的参考文档定义；本文说明这些术语在本项目中的含义，并提供阅读入口。使用方的领域术语仍由各项目维护。

<!-- tao:section terms -->
## 术语与类型

标识符、对象同一性、规格、设计、证据与审查等概念统一见 [tao 术语](../skills/tao-dev/references/glossary.md)。

```{term} 自举
:english: Self-hosting
:scope: tao-dev 开发

用本仓库内的技能源码及其规则开发 tao-dev，无需全局安装。
```

### ID 类型前缀

DOC、REQ、UC、ADR、TASK、CHG 的用途及区别见 [tao 术语](../skills/tao-dev/references/glossary.md)；精确语法见 [文档规程](../skills/tao-dev/references/documents.md) 与 [格式注册表](../skills/tao-dev/assets/document-profiles.json)，此处不重复定义。

<!-- tao:section abbreviations -->
## 缩写与使用规则

VCS（版本控制系统）、CLI（命令行接口）、AST（抽象语法树）与 i18n（国际化）沿用通常技术含义。管理文档和计划进度、使用辅助命令均不要求 Git；版本管理遵循项目既有约定。

### 本项目用语

通用用词规则见术语表。tao-dev 自身以简体中文维护权威正文，优先使用通俗、规范的中文术语；没有合适译名或英文更准确时保留英文。代码标识、文件名、机器字段与提交信息使用英文。这不限制使用方的语言选择。理由见 {need}`ADR_20260914_WX7BFBRXENPN4CT7`，模板和诊断遵循 [本地化](../skills/tao-dev/references/localization.md)。
