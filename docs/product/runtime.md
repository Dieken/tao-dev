---
schema: tao.project.spec/v0.1
id: DOC_20260914_E1B61A3F8V1TYAZB
title: Skill 运行依赖与项目隔离
locale: zh-Hans
status: draft
---

# Skill 运行依赖与项目隔离

<!-- tao:section scope -->
## 目标与边界

阅读与复制完整 skill 无需 Python 或依赖准备；tao 不管理安装生命周期。文档辅助命令按需使用显式创建的项目虚拟环境；不提供自动环境管理、系统 Python 安装器或常驻服务。

操作系统、Python 和客户端支持矩阵以实际验收记录为准；不以路径模拟测试宣称真实平台支持。

<!-- tao:section terms -->
## 术语

通用术语见 [术语表](../glossary.md)。项目安装范围与显式选择的 Python 环境是不同边界；二者均不允许隐式修改用户环境或其他项目。

<!-- tao:section requirements -->
## 需求

```{req} 无需 uv 的辅助工具运行
:id: REQ_20260914_W1NDXAS6DMV7D7HH
:status: proposed

复制完整 skill 不依赖 Python 或 uv。当使用者需要辅助工具时，可用受支持的 Python、标准 venv 与 pip 显式准备依赖，在没有 uv 的 PATH 中执行文档命令。

<!-- tao:field acceptance -->
用干净虚拟环境准备发布包，移除 uv 后运行核心检查；缺 Python、venv、pip 或依赖时返回明确未完成。

<!-- tao:field source -->
用户的项目级纯 skill 与显式依赖准备要求。
```

```{req} 依赖和项目作用域分离
:id: REQ_20260914_GH69P66HSM6HDZXF
:status: proposed

当客户端从项目原生 skill 目录加载 tao-dev 时，配置和生成输出应保留在选定项目内，不依赖用户级索引或安装。

<!-- tao:field acceptance -->
在两个隔离项目中只安装一个；确认另一个项目、个人配置、系统 Python 与安装源未变。文件部署成功不等于真实客户端行为通过。

<!-- tao:field source -->
用户的项目隔离与不修改全局配置要求。
```

```{req} 按需准备且不破坏已有环境
:id: REQ_20260914_WAHF2CDHEJFSBGDC
:status: proposed

读取、复制 skill 和普通命令都不隐式安装依赖。缺少解析或出版依赖时明确报告，提示使用显式项目 .venv；不自动下载、切换环境或写入用户目录。

<!-- tao:field acceptance -->
在无第三方依赖环境中可读取和复制 skill；文档命令缺依赖如实失败且不写环境；只缺出版依赖不应阻断可用的核心操作。

<!-- tao:field source -->
用户的按需准备与用户环境保护要求。
```

```{req} 可复现的开发和发布依赖
:id: REQ_20260914_5PFGD8NJKSAVG2NT
:status: proposed

系统应从单一依赖声明和开发锁文件生成带版本及哈希的发布清单，并在发布验收中拒绝不同步的清单。

<!-- tao:field acceptance -->
uv 锁定开发；独立包用 pip 校验完整依赖，导出无差异；开发文件不成为运行依赖。

<!-- tao:field source -->
可复现依赖与发布一致性的既有要求。
```

<!-- tao:section cases -->
## 验收场景

```{uc} 验证无需 uv 的辅助工具运行
:id: UC_20260914_PX0NTCBHR8ZB4RWP
:status: proposed
:verifies: REQ_20260914_W1NDXAS6DMV7D7HH

<!-- tao:field given -->
隔离安装副本、独立运行目录以及本用例需要的正常与故障输入。

<!-- tao:field when -->
执行对应需求列出的准备、运行或故障操作。

<!-- tao:field then -->
用干净虚拟环境准备发布包，移除 uv 后运行核心检查；缺 Python、venv、pip 或依赖时返回明确未完成。
```

```{uc} 验证依赖和项目作用域分离
:id: UC_20260914_5TF0JH192ZDV99BK
:status: proposed
:verifies: REQ_20260914_GH69P66HSM6HDZXF

<!-- tao:field given -->
隔离安装副本、独立运行目录以及本用例需要的正常与故障输入。

<!-- tao:field when -->
执行对应需求列出的准备、运行或故障操作。

<!-- tao:field then -->
仅目标项目的 skill 副本变化；另一项目、个人配置、系统 Python 与来源不变，不使用文件部署结果冒充真实客户端行为。
```

```{uc} 验证按需准备且不破坏已有环境
:id: UC_20260914_GCRGHS1KTN3HA6W3
:status: proposed
:verifies: REQ_20260914_WAHF2CDHEJFSBGDC

<!-- tao:field given -->
隔离安装副本、独立运行目录以及本用例需要的正常与故障输入。

<!-- tao:field when -->
执行对应需求列出的准备、运行或故障操作。

<!-- tao:field then -->
无第三方依赖时仍可读取和复制 skill；缺文档或出版依赖时诊断真实能力且不隐式准备环境。
```

```{uc} 验证可复现的开发和发布依赖
:id: UC_20260914_ZX3QESKNVE7A22SM
:status: proposed
:verifies: REQ_20260914_5PFGD8NJKSAVG2NT

<!-- tao:field given -->
隔离安装副本、独立运行目录以及本用例需要的正常与故障输入。

<!-- tao:field when -->
执行对应需求列出的准备、运行或故障操作。

<!-- tao:field then -->
uv 锁定开发；独立包用 pip 校验完整依赖，导出无差异；开发文件不成为运行依赖。
```

<!-- tao:section questions -->
## 待确认事项

无。
