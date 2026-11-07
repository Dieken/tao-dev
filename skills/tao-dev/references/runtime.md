# 运行环境与项目安装

阅读 SKILL.md 和参考不需要 Python、文档解析依赖或出版工具。安装管理只用 Python 标准库文件操作，不调用原生插件注册，不准备出版环境。

完整 skill 包括入口、references、assets 和 scripts。用受支持的 Python（3.11–3.14）调用当前已加载 skill 的 `scripts/tao.py`，显式 `--project` 定位项目；不依赖全局 launcher。辅助文档命令可能需要解析依赖，HTML 构建另外需要出版依赖；doctor 报告实际能力，缺依赖不得伪造通过。依赖准备必须显式授权，不因读 skill 或安装而触发。

安装、升级、查看和卸载只针对项目，显式选择支持的 client；具体操作见 [工具入口](tools.md)。项目内 metadata 记录归属，拒绝覆盖非受管路径、符号链接逃逸或用户改动；失败回滚本次管理写入。卸载不删除项目文档，也不触碰用户级配置或其他项目。源码与发布包使用 skills/tao-dev，不提供 hook、marketplace 或全局安装。

## 显式准备辅助工具

需要文档命令时在目标项目用 `python3 -m venv .venv` 创建环境，再用该环境 Python 执行 `-m pip install --require-hashes -r <skill>/scripts/requirements.txt`；HTML 构建另装 scripts/requirements-publication.txt。随后用同一解释器调用 <skill>/scripts/tao.py。没有 env prepare 或自动环境选择，安装文件本身不触发 pip。

## 项目安装接口

`tao <install|upgrade|list|uninstall> --project <已存在项目> --client <claude|codex|cursor|kiro>`；list 可以不指定 client，列本项目四种适配。install/upgrade 可加 --source <本地仓库或完整skill>，默认使用当前运行副本；升级前取得新源码。没有 --scope、--all 或 --yes。

目的地依次是 .claude/skills/tao-dev、.agents/skills/tao-dev、.cursor/skills/tao-dev、.kiro/skills/tao-dev；记录 .tao-install.json 位于受管 skill 内。重复 install 可替换未改动的受管副本，upgrade 要求已有安装。修改、缺失、额外文件或目录都会阻止升级/卸载；先另外保存改动并恢复受管内容，不强制删除。客户端可能发现本项目其他原生路径，不承诺客户端独占。旧全局安装不自动迁移或清理。
