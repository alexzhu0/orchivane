# Orchivane 0.4.1

[English](README.md) · **简体中文** · [MIT](LICENSE) · [贡献与本地验证](CONTRIBUTING.md)

**一个目标，多方协作，持续接班。** Orchivane 取 orchestration（编排）与 vane（方向标）的意象：让专业角色协同推进同一个目标。

## AI 写代码之后，谁来把整个项目推进下去？

一个需求跨越前端、后端、研究和测试时，你可能已经开了几个 AI 对话：每个都能处理自己的任务，但协作工作又回到了你身上。

- **你在搬运上下文。** 把这个窗口的结论复制给另一个，反复解释目标、约束和已经做过的决定。
- **并行开始互相干扰。** 两个会话改了同一份文件，一个仍按旧接口实现，最后需要你辨认哪一版有效。
- **换个对话就要重新交代。** 长对话结束了，新会话看到了摘要，却不知道哪些结论已确认、哪里有未提交成果、谁正在接着做。
- **“完成”很难判断。** 代码写完、测试通过、需求验收、推送和部署混成一句“已完成”，遗留问题没有明确的承接人。
- **你仍然是项目协调员。** 要决定下一步叫谁、给多少背景、何时验收，还要防止已经否定的方案被再次执行。

Orchivane 把这些协作责任交给一个总控入口：总控先澄清目标，再按实际需要组织专业会话，明确每项成果的唯一主责、输入版本、写入范围和验收条件。专业角色交付可核验的成果；换班时连同决定、证据、限制和下一步一起交接。小任务可以留在一个对话中完成。

例如，你只需告诉总控“为现有产品增加登录功能”：它先核对现有身份方案和接口，再判断实施与独立验收如何分工；收到交付后，分别说明实现、验证、推送与部署的状态。你继续参与目标和关键取舍，无须在每个角色窗口重复描述需求。以上是预期使用方式，实际工具能力和已验证范围见文末。

**尚未证明协调成本更低。** 2026-10-20的[配对试跑](tests/paired/README.md)使用相同任务、模型及轮次预算上限：两组各完成三题，额外协调请求均为零；Orchivane 组累计执行时长和 token 更高。没有测量真人时间，也没有形成长期多角色协作，不能把机制设计当成已证实的效能收益。

0.4.1 新增[已有项目平滑接入与升级](skills/orchivane/references/adoption.md)：核验实际来源和版本，让各角色在下次正常任务时读取必要模块并留回执。安装、实际加载和行为核验分别记录；不会仅为升级唤醒忙碌或闲置角色。

[0.4.1原生复核](tests/codex-041-adoption.md)实际执行本机升级，并用两个新对话、四轮验证接入、普通任务加载、回执与总控验收；这些限定路径通过。旧缓存清理/恢复及历史读取截短均保留为限制，不能宣称正在进行的项目升级全程无中断。

0.4.0 新增 Claude Code 支持：插件清单，以及面向 Claude 桌面 App Code 标签页的 [Claude Code 适配说明](skills/orchivane/references/claude-code.md)。在[三轮桌面原生验收](tests/claude-code-desktop.md)中，新总控创建两个长期角色，完成派工，并验收一份附独立评审的简报；最后一轮 16 项中 13 项通过、3 项部分通过，此后的措辞修订未再复测。从 GitHub 安装插件尚未实测。

[2026-10-22 Codex 0.4.0 复核](tests/codex-040.zh-CN.md)确认本机已安装插件的八个文件与仓库一致，并用两个新对话、四轮完成加载、只读接班、接续执行和重复派工检查。功能路径通过；一处源记录路径错误由总控更正并保留证据。这是有限兼容性证据，不代表全面无退化。

0.3.2 将技能正文、插件展示及默认文档改为英文；可继续用中文对话。[0.3.2 原生复核](tests/bilingual-032.zh-CN.md)已确认本机升级、四个新对话加载、中英文规划及英文材料到中文接班的执行；反向接班因宿主容量中断，最终记录一致性也需总控收尾。这是部分证据，不能宣称翻译后完全无退化。

## 从一个想法开始

从一个项目想法开始，先调研并与用户沟通，判断适合什么协作机制，再形成分工与启动方案。没有已有 session 或资料也可使用；已有项目则复用其角色和入口。进入多会话执行后，用户在总控提出需求，总控统一派工、验收和收口。适用于开发、研究、内容与运营项目。

本套件包含一个可独立安装的 Skill 和轻量插件清单。核心入口短，按任务加载建制、派工验收、巡检、handoff、Codex 与 Claude Code 适配模块；没有后台服务、额外依赖或自动唤醒 hook。

## 直接使用

在已加载该技能的新对话中输入：

```text
使用 $orchivane，我有一个新项目想法，目前没有其他 session。
先帮我调研并和我沟通，判断需要什么协作机制，再给出具体分工和启动方案。
```

在 Claude Code 中可说“使用 orchivane”，或执行 `/orchivane:orchivane`（插件）或 `/orchivane`（独立复制）；`$orchivane` 是 Codex 写法。

常用请求：

- 从零设计：`使用 $orchivane，我想做……，先了解需求和关键约束，调研后建议是否需要拆 session、怎么拆。`
- 接管现有项目：`使用 $orchivane，核对已有 session 的职责与当前 TODO，不派新任务。`
- 统一派工：`使用 $orchivane，按我已确认的任务清单向对应 session 派工，并读取交付结果。`
- 换班：`使用 $orchivane，给当前总控准备交接包，先不创建或归档。`
- 执行换班：`使用 $orchivane，按这份交接包创建接班会话、核验接班并转接关联自动化；保全资料且条件满足后归档旧会话并做归档后复核。`
- 单次巡检：`使用 $orchivane，检查这个项目的多会话协作，只报告新异常、关键缺口和下一步。`

流程是“理解目标 → 必要调研与分轮沟通 → 推荐协作结构 → 具体启动方案 → 按授权落地”。按长期上下文、工作依赖和独立验收需要拆分，也可以建议暂留当前对话。角色数量与命名按项目确定；已有授权直接沿用，真实新增的创建/发消息等动作才集中补问。长期角色与临时 subagent 分开管理。

## 安装与迁移

### Codex 插件安装（推荐）

使用与其他 Codex 插件相同的“添加来源 → 安装插件”流程。无需先克隆仓库：

```sh
codex plugin marketplace add alexzhu0/orchivane
codex plugin add orchivane@orchivane-local
codex plugin list --marketplace orchivane-local --json
```

上述命令已在 Codex CLI 0.157.1 实际完成：0.3.1 插件安装并启用，技能从插件缓存发现为 `orchivane:orchivane`；第三行用于核对安装状态。

2026-10-19，本机用户已确认桌面插件目录可见；两个新建桌面对话实际从插件缓存读取0.3.1并使用规则，其中一个请求正文未点名技能。本轮无需重启。目录可见由用户观察，启用状态和实际读取由工具核验，详见[桌面验收与复现](tests/desktop-plugin.md)。流程依据 [OpenAI插件打包文档](https://developers.openai.com/plugins/build/plugins)，具体命令以本机CLI帮助为准。这是通过公开GitHub来源分发，尚未上架官方精选目录。

插件安装后，可以说“使用 Orchivane 帮我组织这个项目”，或选择客户端显示的 `orchivane:orchivane` 技能。下文及独立安装的 `$orchivane` 示例指同一套规则。若此前已安装独立Skill，先完整备份到技能扫描目录之外，确认插件可用后仅保留一个活跃来源，避免重复加载；不要删除本地定制。

**是否需要“启动”？** 本包是按任务读取的技能，没有需要手动启动的后台进程。`installed=true`、`enabled=true` 表示已安装并启用；再用一个新对话核验实际加载。可直接输入：

```text
请检查本轮可用技能清单是否有 Orchivane。
若有，读取声明入口，报告版本，并用它建议一个需求尚不明确的新项目是否需要多个长期角色。
若没有就报告未发现，不自行搜索文件补救。本轮只读，不创建或派工。
```

清单出现、实际读取、按规则行动是三个不同检查点。自然语言触发受宿主、模型及其他技能影响；需要稳定选用时明确点名。此核验无需新增项目文件、脚本或角色。

### 已有项目接入与升级

向现有总控提出：

```text
使用 $orchivane，接入或升级这个项目的协作机制。
先核验实际可用来源、版本和你实际读取的模块。
保留已有角色和进行中的任务；各角色在下次正常任务时核验并留回执，
没有任务的角色继续待核验。不要打断工作、群发升级消息或重启对话。
```

总控复用项目规则与职责索引，登记已核目标，按需补充指引。各角色在自己的任务回执中记录实际读取的入口/模块、版本或内容摘要、任务/轮次、职责与预算边界、实际产物和验证；总控逐项核收。部分读取、旧版与无法访问均保留明确缺口，不能因为插件已安装就宣布全部旧对话完成升级。

安装包更新是另一项操作：在获得相应授权后使用宿主支持的方式，保留本地定制并仅保留一个活跃来源。显式路径加载须如实注明。完整字段与边界见[接入与升级模块](skills/orchivane/references/adoption.md)，已测行为及限制见[隔离演练记录](tests/adoption-upgrade.md)。

安装包替换可能影响旧路径：[0.4.1原生升级](tests/codex-041-adoption.md)中，升级器删除了旧版缓存；虽已从事先校验的备份恢复，仍不能证明全程可用。若正在进行的工作必须持续读取旧来源，应将安装更新安排在安全窗口；总控可先准备延后接入记录，无须立即替换插件。

### Claude Code 插件安装

在 Claude Code 中添加 GitHub 来源并安装：

```text
/plugin marketplace add alexzhu0/orchivane
/plugin install orchivane@orchivane
```

也可在终端执行 `claude plugin marketplace add alexzhu0/orchivane` 和 `claude plugin install orchivane@orchivane`。清单已通过 `claude plugin validate`，以 `--plugin-dir` 临时加载时能发现并调用 `orchivane:orchivane`；从该 GitHub 来源安装尚未实测。独立复制安装时，把完整的 `skills/orchivane` 目录放到 `~/.claude/skills/orchivane` 或项目的 `.claude/skills/`，只保留一个活跃来源。创建、发消息和归档长期会话需要 Claude 桌面 App Code 标签页的会话工具，见 [Claude Code 适配说明](skills/orchivane/references/claude-code.md)与[桌面验收记录](tests/claude-code-desktop.md)。

### 独立 Skill 安装

独立 Skill 的完整目录是 [`skills/orchivane`](skills/orchivane/SKILL.md)，运行它无需 Python 或新依赖。下载/克隆本仓库后，在仓库根目录执行下面命令：前两行跨平台，`mkdir` 起的后两行是 macOS/Linux 写法，目标已有文件或链接时拒绝覆盖。

```sh
git clone https://github.com/alexzhu0/orchivane.git
cd orchivane
mkdir -p "$HOME/.agents/skills"
test ! -e "$HOME/.agents/skills/orchivane" && test ! -L "$HOME/.agents/skills/orchivane" && cp -R skills/orchivane "$HOME/.agents/skills/orchivane"
```

安装后可用一条只读命令核验副本（逐项输出 PASS/FAIL，退出码 0/1；不带路径时核验仓库内的打包副本）：

```sh
python scripts/verify_install.py ~/.agents/skills/orchivane
```

目录必须包含 `references/` 与 `agents/`，不要只复制 SKILL.md。Windows 可把整个目录复制到用户目录下 `.agents/skills/`。旧客户端使用 `~/.codex/skills/` 的安装须实际核验发现能力。选择一个安装来源；更新前核对其路径和版本，保留本地定制。目录规则依据 [Codex 技能文档](https://learn.chatgpt.com/docs/build-skills)。

0.3.1 更名自 Session Control，调用入口改为 `$orchivane`。已有 `session-control` 安装者，先将旧目录及本地定制备份到技能扫描目录之外，再安装新目录，避免两个入口同时生效。历史测试与冻结示例保留原名，不能把更名当作重新验证。

旧名0.3.0的本机独立复制安装曾被CLI发现，但三个新桌面对话均未列出该技能，原路径的根因仍未确认。后续0.3.1插件安装路线已通过新桌面对话加载验证；没有重测旧独立安装，也不将插件成功改写为旧路线已修复。当前验证结果见[验证记录](tests/evaluation.md)。

自动发现尚未生效时，可以明确要求助手“读取我安装目录中的 `orchivane/SKILL.md` 并按其流程工作”，提供真实完整路径。这是显式加载方式，应单独记录，不能当成自动发现或插件安装通过。

仓库内 `.agents/plugins/marketplace.json` 定义插件来源，根 `plugin.json` 为 portable 格式，`.codex-plugin/plugin.json` 为 Codex 兼容格式，`.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json` 供 Claude Code 使用。本包没有后台调度或自动执行 hook。

旧的个人 `session-handoff` / `session-health-check` 可以继续保留。新技能内部已有完整交接与巡检流程，无运行时依赖；明确使用 `$orchivane` 即可进入统一机制。旧技能未自动改写，以免影响已有项目。

## 内容与证据

| 内容 | 入口 |
| --- | --- |
| 核心规则与路由 | [SKILL.md](skills/orchivane/SKILL.md) |
| 从零调研沟通、机制设计、项目接管和恢复 | [setup.md](skills/orchivane/references/setup.md) |
| 已有项目接入、升级与版本回执 | [接入与升级](skills/orchivane/references/adoption.md) |
| 任务说明、一次确认与验收 | [dispatch.md](skills/orchivane/references/dispatch.md) |
| 交接、资料保全、自动化转接、归档后复核 | [handoff.md](skills/orchivane/references/handoff.md) |
| 按变化巡检与通知 | [health-check.md](skills/orchivane/references/health-check.md) |
| 原生能力与降级方式 | [codex.md](skills/orchivane/references/codex.md) · [claude-code.md](skills/orchivane/references/claude-code.md) |
| Ponytail / Superpowers 源码研究与取舍 | [研究记录](docs/research.zh-CN.md) |
| 项目定位、同类方案与下一步取舍 | [价值与优化评估](docs/value-assessment.zh-CN.md) |
| 桌面插件发现、启用与使用复现 | [桌面验收](tests/desktop-plugin.md) |
| 隔离接班、依赖恢复、旧回执及重复派工 | [接班恢复实验](tests/handoff-recovery.md) |
| 单会话对照、协调请求与资源用量 | [配对试跑及复现](tests/paired/README.md) |
| 当前标准、平台支持与边界 | [兼容性说明](docs/compatibility.md) |
| 真实多会话案例（最终19/20，未通过） | [借物小站完整记录](examples/tool-library/README.md) |
| 原生端到端实验的复现步骤 | [native-e2e.md](tests/native-e2e.md) |
| 行为测试条件与实测边界 | [场景](tests/scenarios.md)、[结果](tests/evaluation.md) |

## 语言与贡献约定

默认首页为英文，可在顶部切换完整中文说明。代码标识符、注释、插件展示及维护中的技能指令以英文为主；对话仍按用户偏好的语言进行。研究与价值文档提供中英文版本；历史中文记录与冻结夹具保留原文，英文读者可从[证据索引](docs/evidence.md)查看结果、版本和限制。贡献时同步更新两份 README 的安装步骤、功能与证据口径，避免语言版本漂移。

## 能力边界

技能规定工作方法，客户端提供创建/读取/消息/自动化工具。缺少工具时可生成任务和交接材料，不能实际操控其他会话。检查或建制不自动授权创建新聊天、发消息、修复产品或归档。调度只在用户要求时建立。

0.3.0 根据真实原生会话实验补上技能版本标识、创建窗口登记与共享目录及冻结依赖核验，并提供开发校验、CI、MIT许可及贡献说明。静态验证不会创建聊天或调用供应商；运行方法见贡献文档。具体实测覆盖与未验证项以测试记录为准，不把单次流程成功推为所有客户端或所有项目有效。
