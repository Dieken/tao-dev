---
schema: tao.project.evidence/v0.1
id: "DOC_20260914_8YCWJXDGRT728KXD"
title: "共享规则与自举文档检查"
locale: "zh-Hans"
status: draft
created: "2026-09-14"
evidence: "EVD_20260914_6M5WB4VYYSZ4BM89"
change: "CHG_20260914_MPNFR3H9WQ7KHFAD"
recorded_at: "2026-09-14T11:50:51+08:00"
result: passed
coverage: partial
---

# 共享规则与自举文档检查

<!-- tao:section scope -->
## 目标与边界

本次规则归位、包内引用与新增自举文档的静态检查。完整 AST、HTML 出版和双 CLI 行为不在本记录的覆盖范围。

<!-- tao:section inputs -->
## 输入与环境

<!-- tao:field fingerprint -->
**受检输入:** 本仓库 Git 提交 `1a22ec3beb311be6d3abba49c28167419be654c5`；范围为该版本的计划、长期开发文档、入口、分配记录及完整插件源码，共 39 个受检文件，排除证据目录。后续逐项核对原清单确认这 39 个文件的内容全部与该版本一致，故使用版本引用替代独立清单；这不表示原检查执行时工作区已经提交，也不表示该结果适用于当前版本。证据自身的结构另经静态检查。

<!-- tao:field environment -->
**环境:** Darwin 24.6.0，Python 3.14.7、PyYAML 6.0.3，当前工作副本；使用既有依赖，未进行全局安装。

<!-- tao:section checks -->
## 检查记录

<!-- tao:field command -->
**命令或观察步骤:** 执行临时文档结构检查、模板夹具检查、自举与独立包检查、skill-creator 的 quick_validate.py 和 git diff --check。实际命令名称、脚本摘要、环境、开始／结束时刻与退出结果保存在报告中；本机绝对路径不进入项目文档。

<!-- tao:field expected -->
**预期:** 原有 ID 不变，新增文档遵循共享格式，模板正反例符合预期；包内链接不依赖开发仓库，未执行的能力不宣称通过。

<!-- tao:field observed -->
**实际观察:** 所列检查均返回 0。原有 37 个正式 ID 保留，新建 5 个 ID 唯一；两份新文档采用共享 profile，10 种模板在两种语言下检查通过，16 个损坏夹具被拒绝。独立包的 36 个文件引用解析成功，故意注入的包外依赖被拒绝。

<!-- tao:field reports -->
**报告:** [执行输出](validation.txt) 的 SHA-256 为 `222fa99bce0fe8198d7014b4499d19fdb72c96aa44373b898bf8c0e8c6a89b16`；受检内容由上述固定版本定位。

<!-- tao:section findings -->
## 发现与限制

<!-- tao:field limits -->
**限制:** 临时检查不是产品校验器；已有六篇长期文档按内部格式单独检查，不能计入共享格式通过。未运行真实 CLI 加载、跨模型审查或 HTML 构建。临时检查脚本未作为维护工具交付，报告保存其摘要与输出，不宣称仅凭本记录即可重放整套临时工具；后续应以正式校验器重验。

<!-- tao:section retention -->
## 证据保存

<!-- tao:field retention -->
**保存位置与期限:** 该证据和必要小型报告随本项目 VCS 保留，不随 skill 分发；不依赖临时目录作为唯一记录。
