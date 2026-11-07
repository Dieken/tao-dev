# 可选项目接入

项目配置不是 status、ID 分配或计划骨架生成的前置条件。读取以显式 `--project <root>` 为界，不创建配置或扫描其他项目。

1. `tao --project <root> project inspect` 读取现有配置并发现检查候选，不运行命令。
2. 核对 manifest、CI、已有命令和副作用，优先复用既有工具；空项目待技术栈明确后再选最小检查集合。
3. 在已有授权内准备必要的业务工具，保留项目门槛，不修改全局客户端或用户环境。
4. 在项目临时目录写 TOML 草稿，保留现有无关配置。用 `tao project configure --from <项目相对草稿>` 写入；已有配置使用 inspect 返回的 config_digest 配合 `--expect` 检测冲突。
5. 明确 docs 与 temporary 的项目内路径、书根与检查范围，忽略临时产物；只在实际运行检查后报告结果。

无需 workflow 目录、全局索引、hook 或正式交接文件。下一步：已有计划 continue；新目标 new；仅调查则返回建议，不自动配置。
