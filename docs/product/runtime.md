---
schema: tao.project.spec/v0.1
id: DOC_20260914_E1B61A3F8V1TYAZB
title: 插件运行环境
locale: zh-Hans
status: draft
created: "2026-09-14"
---

# 插件运行环境

<!-- tao:section scope -->
## 目标与边界

为已安装的 agent 插件准备可诊断、可隔离的 Python 环境。无需 uv；Python 为显式前提。完整 install 协调客户端注册与安装作用域，并准备 tao 专用依赖；不提供系统 Python 安装器或常驻服务。

<!-- tao:section terms -->
## 术语

通用术语见 [术语表](../glossary.md)。运行环境是 tao-dev 专用虚拟环境；插件 scope 表示客户端启用范围，不表示 Python 安装目录。

<!-- tao:section requirements -->
## 需求

```{req} 无需 uv 的插件运行
:id: REQ_20260914_W1NDXAS6DMV7D7HH
:status: proposed

当使用者已提供受支持的 Python 并明确准备依赖时，系统应仅用标准 venv 和 pip 建立独立环境，使核心命令可在没有 uv 的 PATH 中执行。

<!-- tao:field acceptance -->
用干净虚拟环境准备发布包，移除 uv 后运行核心检查；缺 Python、venv、pip 或依赖时返回明确未完成。

<!-- tao:field source -->
用户批准的独立运行环境方案与插件作用域约束。
```

```{req} 依赖和项目作用域分离
:id: REQ_20260914_GH69P66HSM6HDZXF
:status: proposed

当客户端以 user、project 或 local 作用域启用插件时，系统应使用客户端提供的源码与数据位置，并将项目配置和验证输出保留在对应项目中。

<!-- tao:field acceptance -->
只读插件、独立数据目录、两个项目及范围外会话；检查无安装源、业务环境或个人配置写入。Codex 只声明实测支持的方式。

<!-- tao:field source -->
用户批准的独立运行环境方案与插件作用域约束。
```

```{req} 按需准备且不破坏已有环境
:id: REQ_20260914_WAHF2CDHEJFSBGDC
:status: proposed

当依赖组合变化、并发准备或安装失败时，系统应仅选择匹配且验证完成的环境，保留正在使用的已有环境；普通命令和 hook 不安装依赖。

<!-- tao:field acceptance -->
覆盖版本隔离、锁等待上限、失败后重试、离线使用、完整环境仍可用；出版依赖缺失不影响核心。

<!-- tao:field source -->
用户批准的独立运行环境方案与插件作用域约束。
```

```{req} 可复现的开发和发布依赖
:id: REQ_20260914_5PFGD8NJKSAVG2NT
:status: proposed

系统应从单一依赖声明和开发锁文件生成带版本及哈希的发布清单，并在发布验收中拒绝不同步的清单。

<!-- tao:field acceptance -->
uv 锁定开发；独立包用 pip 校验完整依赖，导出无差异；开发文件不成为运行依赖。

<!-- tao:field source -->
用户批准的独立运行环境方案与插件作用域约束。
```

<!-- tao:section cases -->
## 验收场景

```{uc} 验证无需 uv 的插件运行
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
只读插件、独立数据目录、两个项目及范围外会话；检查无安装源、业务环境或个人配置写入。Codex 只声明实测支持的方式。
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
覆盖版本隔离、锁等待上限、失败后重试、离线使用、完整环境仍可用；出版依赖缺失不影响核心。
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
## 待定

操作系统、Python 和客户端支持矩阵以实际验收记录为准；不以路径模拟测试宣称真实平台支持。

