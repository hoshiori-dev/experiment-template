# experiment-template

> 本文是 [README.md](README.md) 的中文译本。两者有出入时，以英文版为准。

一个研究项目的模板：人决定方向，人接受结论，中间的工作交给 Agent。每一个结果都要满足两件事：能复现，没参与的人也能看懂。

设计以机器学习项目为蓝本，但规则管的是边界，不是方法。本文提到容器、锁文件或 GPU
的地方，说的都是机器学习范例；背后的规则适用于任何类型的实验。

## 一页读完

**三个阶段。** 项目从搭好仓库和 harness
开始。之后在整备阶段和实验阶段之间循环，走多少轮，看证据什么时候够。在某一次整备阶段，研究者和 Agent
一致认为证据已经足够，项目就离开循环，去写报告、发布代码。这个判断人必须参与；写的过程中发现缺口，再回头补实验。

**整备与实验交替。** 整备阶段只改共享部分：`docs/` 里已接受的知识、`packages/` 里的共享库，以及
harness。实验只改自己的目录。实验阶段共享部分冻结，人和 Agent 并行工作而不会产生合并冲突；实验做完之后，它自己也冻结。

**Epic、Experiment、Formal Run。** 一个 Epic 是一轮研究：一个 GitHub issue，由维护者打上 `epic:approved`
标签发布，写明目标、范围、约束和预算政策。每个 Experiment 是 Epic 下的一个 sub-issue，有一个具体的目标；它的 ID（如
`exp-023-normalization-instability`）同时命名 spec 目录、实验目录和分支。一次 Formal Run
是一个研究决定加一次可复现的启动，记在 `experiments/<id>/runs/R001.yaml` 里。只有 Formal Run
算证据。调试和冒烟运行随便跑，但证明不了任何东西。

**两道闸门属于人。** 每个 Epic 由人发布（方向闸门），每个综合 pull request 由人合并进
`docs/`（验收闸门）。模板出厂的高度自动化模型下，Agent 自己规划 Epic 下的实验，每份 spec 由一个上下文干净的独立 Agent
审批，只改了自己目录的实验 pull request 由 Agent 合并。

**预算由机器把关。** 每个实验的 spec 都写有上限。每次 Run
启动前预留，结束后记实际用量，失败的也算，总和不能超过上限。预算用完，Agent 停下来告知人；只有人能提高预算。

**受保护路径。** Agent 不能放宽约束自己的东西。规则、检查、权限表、`docs/` 和 `packages/`
可以在分支上改，但只有人能合并。最后一道防线是托管平台上的分支保护，由所有者亲手配置。

**围栏里的工作区。** harness
给每个实验一块工作区，用方向、范围、预算和证据要求围起来，再把工具递进去。在围栏里怎么探索、怎么构建、怎么运行，由 Agent
自己决定。递出来的是 README、代码，以及支撑结论的 Formal Run。

**每个事实只有一个出处。** 没有状态数据库。凡是能从 Git、Run 记录和 tracker 推导出来的东西，都不存第二份。

## 出厂配置

| 设置             | 出厂值                                                                                                         |
| ---------------- | -------------------------------------------------------------------------------------------------------------- |
| 治理模型         | 高度自动化：Agent 规划 Epic 下的实验、写 spec，独立的 Agent 审批，Agent 合并实验的 pull request                |
| 外部写入         | 开启：Agent 推送自己的分支、开 issue 和 pull request、评论、打标签；从不推送 `main`，从不强制推送              |
| 预算             | 开启：实验一级的上限写在 spec 头部，由 `scripts/budget.py` 离线检查                                            |
| Epic 一级硬上限  | 不由机器强制；审批的人把 Epic 下各实验的账加起来核对                                                           |
| 审批记录         | 实验 pull request 上的 `spec:approved` 标签，用 `gh` 读取                                                      |
| Epic 有效性      | issue 打开、`epic:approved` 在创建之后打上、打标签后正文未编辑                                                 |
| 发布安全         | 公开仓库标准：gitleaks 加扩展的个人数据和路径规则，再加 Agent 通读                                             |
| Agent 署名       | 提交、issue、PR 和评论里一律禁止；Claude Code 的署名已在设置里关闭；人类共同作者用 noreply 地址                |
| 提交地址         | 只接受平台的 noreply 地址                                                                                      |
| 执行环境（范例） | 本地 Docker，CPU 或恰好一块 GPU，无网络                                                                        |
| Tracker（范例）  | Trackio，本地存储在 `.local/trackio/`                                                                          |
| 平台             | GitHub；`gh` 用于查询和上述写入                                                                                |
| 分支             | `main`，每个实验一条分支（`exp-NNN-slug`），run 分支 `run/<exp-id>/R###`，`synthesis/<epic#>`，`<type>/<slug>` |
| 示例实验         | 无；`template/experiment/` 是起步模板                                                                          |

## 快速开始

1. 用这个模板创建一个仓库。
2. 在 devcontainer 里打开，或者在本地运行 `uv sync && pre-commit install --install-hooks`。devcontainer
   会替你跑这两步。研究命令已经装进了 Spec Kit；只有改过 `speckit/` 之后才需要运行 `just speckit-install`（见
   [speckit/README.md](speckit/README.md)）。
3. 手动配置 GitHub，仓库里的任何东西都替代不了这一步：
   - 按 `.github/labels.yml` 创建标签，运行 labels 工作流或者用 `gh label create`；
   - 在 `.github/CODEOWNERS` 里定下受保护路径的所有者。
4. 在第一个 Epic 之前，为一个会写入的 Agent 配好平台。没有这一步，“受保护路径只能由人合并”只是一条没有东西执行的约定：
   - `main` 上的分支保护规则或 ruleset：要求 pull request 和代码所有者审查，只允许合并提交（Run 的历史必须保留）。
     仓库管理员保留绕过权限，这样你可以自己合并 harness 的 pull request；合并者是谁就是审计信号；
   - 给 Agent 一个没有管理员权限的凭据：一个只有写权限的机器账号，或者一个细粒度 token，只给
     `Contents: write`（推送和合并）、`Pull requests: write`、`Issues: write`。用你自己的管理员账号创建的细粒度 token
     是否继承绕过权限，这里没有验证过；用机器账号可以避开这个问题；
   - 审批的 Agent 和执行的 Agent 共用这个凭据，所以平台分不出 `spec:approved` 是谁打的，审批的独立性靠流程保证。
     需要平台记录这一点时，再给审批方单独的账号或 token。
5. 打开你的 Agent，用 `/speckit-research-epic` 起草第一个 Epic。Agent 写草稿，你发布 issue 并打上 `epic:approved`。

之后，说出你想要什么，Agent 运行对应的命令。

## 日常命令

这些命令是为 Claude Code 安装的 Spec Kit skill；Codex 通过 `.agents/skills/` 里的符号链接使用它们，OpenCode 直接读取
`.claude/skills/`，所以三者的命令名相同。

| 你想要              | 让 Agent                                 | 命令                                                    | 最后一步由谁做                         |
| ------------------- | ---------------------------------------- | ------------------------------------------------------- | -------------------------------------- |
| 开启一轮研究        | 起草 Epic                                | `/speckit-research-epic`                                | 你：发布 issue 并打上 `epic:approved`  |
| 规划这一轮          | 为已发布的 Epic 提出实验并创建实验 issue | `/speckit-research-experiments`                         | Agent                                  |
| 研究一个问题        | 从一个实验 issue 开始 Experiment         | `/speckit-specify`                                      | Agent：推送、开 PR、申请审批           |
| 对照 Epic 核对 spec | 审阅 spec                                | `/speckit-research-approve`                             | 上下文干净的 Agent：打 `spec:approved` |
| 继续推进            | 迭代该 Experiment                        | `/speckit-plan`、`/speckit-tasks`、`/speckit-implement` | Agent                                  |
| 产出证据            | 执行一次 Formal Run                      | `/speckit-research-run`                                 | Agent                                  |
| 结束一个问题        | 收尾该 Experiment                        | `/speckit-research-finish`                              | Agent：只改了自己目录时合并            |
| 收束一轮            | 综合这个 Epic                            | `/speckit-research-synthesize`                          | 你：合并综合 pull request              |
| 了解当前进展        | 显示研究状态（只读）                     | `/speckit-research-status`                              | 无                                     |

最后一列对应高度自动化模型。人类主导模型下，spec 审批和实验的合并转回给你。

命令背后是一些你自己也能运行的普通工具：`just check`、`just status`、`just budget <exp>`、`just preflight <exp> <run>`、`just epic-status <n>`、`just scan`。`just --list`
列出全部 recipe。

## 仓库布局

```text
.
│   给 Agent 的文件
├── AGENTS.md                  入口文件：Agent 工作前先读的地图
├── CLAUDE.md                  某个框架自己的入口，只引入 AGENTS.md
├── .agents/
│   ├── knowledge/             harness 知识库：规则、约束、运作方式
│   └── skills/                流程：分步的操作程序
├── .claude/                   Claude Code 的配置和权限表
├── .codex/                    Codex 的配置和权限表
├── opencode.json              OpenCode 的配置和权限表
├── speckit/                   研究 preset 和扩展的源文件
├── .specify/                  Spec Kit 的工作目录，要提交
│
│   工具和检查
├── justfile                   一条 recipe 一个动作
├── scripts/                   检查脚本
│   └── tests/                 脚本和 harness 文件的测试
├── .pre-commit-config.yaml    提交、提交信息、推送时的钩子
├── .gitleaks.toml             扫描器规则
├── pyproject.toml             根 workspace：管理工具和共享库
├── uv.lock                    根锁文件；Run 不从这里装任何东西
├── .devcontainer/             装好上述工具的开发容器
├── .github/                   issue 和 PR 模板、标签、持续集成
├── template/                  新实验的起步模板
│
│   共享的内容（有东西要放之前为空，用 .gitkeep 占位）
├── packages/<name>/           一个共享库，自带 pyproject 和测试
├── docs/                      已接受的实验知识
│
│   实验
├── specs/<id>/                一个 Experiment 的 spec、plan、tasks
├── experiments/<id>/          README、代码、自己的 pyproject、测试
│   └── runs/                  Run 记录和冻结的依赖清单
│
│   交付（写报告之前为空）
├── reports/                   论文和报告
├── demos/                     演示，永远不是证据
│
│   只在本地，Git 忽略
└── .local/                    数据、Run 输出、tracker 存储、草稿
```

`specs/` 以上的都是共享部分，整备阶段由人合并。`specs/<id>/` 和 `experiments/<id>/` 是一个实验唯一会改动的路径。

## 怎样适配

上表里的每一项都是所有者的决定。Agent
可以列出选项和代价，但不能借着改设置给自己扩权。[.agents/knowledge/adaptation.md](.agents/knowledge/adaptation.md)
逐项说明：治理模型，预算和它的单位，Epic 一级的硬上限，受保护路径，Agent
署名，提交地址，审批标签的自动化，外部写入，发布安全的标准，以及更换执行环境、tracker 或平台。

两道闸门不能调掉：每个 Epic 由人发布，每次综合由人合并。

## 尚未实现或未验证

- 没有示例实验。结果不能编造，真做一个需要真实算力；`template/experiment/` 是起点。
- 没有任何东西端到端跑过：两种治理模型下都还没有 Epic、Experiment 或 Formal Run 走完整个循环。
- 独立的审批 Agent 只靠流程保证：命令要求另起一个上下文干净的子 Agent
  来审，但没有任何检查核对审批者不是作者。要不要给它单独的账号，由所有者决定（快速开始第 4 步）。
- 其他执行环境、其他 tracker 和 GitLab 只有适配说明，都没有运行过。
- Epic 一级的预算上限由审批的人核对，没有脚本检查。
- 审批标签的自动化（spec 改动后自动摘掉 `spec:approved`、核对打标签的账号）只有说明，没有启用。

## 许可证

[Apache License 2.0](LICENSE)。
