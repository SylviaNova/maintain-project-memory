# Maintain Project Memory

`maintain-project-memory` 是一套跨 AI 的项目记忆协议，用本地 Markdown 文档保存已经实现、能够验证的项目背景、当前状态、技术决策和修改记录。

它适用于 Git 仓库和普通本地项目。Git 项目默认采用本地私有模式，`.project-memory/` 不会被默认提交或发布；只有用户明确授权后才允许进入版本控制。

## 设计目标

- 新对话可以快速读取项目现状，不依赖旧聊天记录。
- 只记录能由代码、配置、测试、运行结果或 Git 状态验证的事实。
- 每次代码任务结束后自动判断是否需要更新，并在最终回复中明确回执。
- 不记录 AI 工具、模型、提示词或内部推理。
- 使用 Markdown、JSON 和 Python 标准库，降低平台绑定。

## 仓库结构

~~~text
maintain-project-memory/
├── README.md
├── LICENSE
├── adapters/
│   ├── generic-project-instructions.md
│   └── manual-session-prompt.md
├── skills/
│   └── maintain-project-memory/
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── scripts/project_memory.py
│       ├── references/
│       └── assets/context-template/
└── tests/
    └── test_project_memory.py
~~~

## 安装

支持原生 Skill 的 AI 工具，可以安装或复制下面的目录：

~~~text
skills/maintain-project-memory/
~~~

不支持相同 Skill 格式的工具，将 [generic-project-instructions.md](adapters/generic-project-instructions.md) 中的指令放入其项目规则、自定义指令或工作区说明中。

如果平台无法保存持久项目指令，每次新对话使用 [manual-session-prompt.md](adapters/manual-session-prompt.md) 中的启动提示。

不同 AI 产品的自动触发机制并不统一。跨平台兼容的是项目记忆格式和维护协议；自动执行依赖目标平台能够读取项目指令并写入工作区。

## 项目中的文件

初始化后，目标项目将包含：

~~~text
.project-memory/
├── config.json
├── INDEX.md
├── OVERVIEW.md
├── STATUS.md
├── DECISIONS.md
├── CHANGELOG.md
└── archive/
~~~

Git 项目会优先通过 `.git/info/exclude` 在本地忽略该目录。如果本地排除文件不可写，才会回退到项目的 `.gitignore`。初始化完成后会再次验证忽略状态。

## 使用方式

通常只需要告诉 AI：

~~~text
使用 maintain-project-memory 接手并维护这个项目的项目记忆。
~~~

也可以直接运行辅助脚本：

~~~bash
python3 skills/maintain-project-memory/scripts/project_memory.py inspect --project /path/to/project
python3 skills/maintain-project-memory/scripts/project_memory.py init --project /path/to/project
python3 skills/maintain-project-memory/scripts/project_memory.py validate --project /path/to/project --strict
~~~

初始化脚本只创建安全的文档骨架和元数据。AI仍需检查实际项目，并用验证过的事实填充内容。

## 隐私原则

- 默认配置为 `local-private`。
- 不自动执行 `git add`、commit 或 push。
- 不自动取消跟踪、重置暂存区或修改 Git 历史。
- 发现记忆目录已被跟踪或暂存时停止更新并警告。
- 只有用户明确授权时才允许使用 `tracked` 模式。
- 即使用户允许跟踪，也必须重新检查密钥、个人信息和内部数据。

## 验证

在仓库根目录运行：

~~~bash
python3 -m unittest discover -s tests -v
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/maintain-project-memory
~~~

第二条命令中的校验器路径可替换为本机 Skill Creator 提供的路径。

## License

本项目采用 [MIT License](LICENSE)。允许使用、复制、修改和再发布，但需保留原始版权声明和许可证文本。
