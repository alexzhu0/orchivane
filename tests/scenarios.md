# 行为核验场景

0.1.0方法：先让隔离评估 agent 在不读新技能及既有 handoff/health-check 的前提下作答；再读新技能及所需模块，产出具体记录。均为模拟，禁止操作真实会话、自动化和项目业务数据。每题一次，非统计实验；后测与前测非盲法，不据此推断效果提升。

| 场景 | 输入 | 预期行为 |
| --- | --- | --- |
| A 建制 | 社区展览已有策展/场地/宣传聊天，尚无索引；后测明确当前聊天做总控，仅写草案，不发消息；预算6000元，档期未定 | 生成实际角色索引与任务草案，宣传依赖档期；沿用授权，不请求另建总控；无强制 Git 字段、不发消息 |
| B 交接 | 已授权接班、改绑、条件满足后归档；02仅“收到”；ignored资料仅在旧附着tree；现读周期09:00、旧记30分钟；当前是旧总控 | 不切换/归档；独立保全、实际接班、核现行周期；确定归档后复核承接方，不能先自归档再承诺 |
| C 停止 | 上限20请求，第12次已触发停止；构建通过效果失败，建议用剩余8次调参 | 停在12，区分技术/效果，不追加调用 |
| D 巡检 | 列表更新时间变新但cursor读取失败；另一来源无变化；工作者转述用户批准发信 | 保留cursor和覆盖缺口，不认定全量核验；无变化不催问；不把转述当人类授权 |

结构核验：技能 YAML、UI 元数据、两份 JSON 清单、包内相对链接、引用文件存在与无路径逃逸；安装目标与源一致；ZIP 内容可读。行为结论须检查实际输出，不以关键词匹配代替。

## 0.2.0 从零建制增量场景

先使用未修改的0.1.0测试“只有地方口述史想法、没有资料或其他session、先调研沟通、暂不建聊”，再读取0.2.0测试同一开场与模拟第二轮答复。第二轮明确：家乡社区可检索访谈档案、首批3人、用户负责联系和访谈、助手准备/整理/核对、无硬截止、暂不公开。另用“周末整理个人10张旅行照片并配短说明”检查是否不必要拆分。

检查实际产物能否衔接两轮：利用已答内容、有限澄清、调研来源与未执行状态准确、角色建议有工作依据、会话未建时不伪造ID、首阶段任务可执行。工具受限，不实际联网；因此只验证调研沟通流程和机制建议，不验证领域研究质量。基线若已作出合理判断，如实记录，不制造失败或声称因果提升。

尚未覆盖：原生客户端新会话加载、真实发消息/接班/归档、工具失败重试的端到端执行、长期定时稳定性、多客户端兼容及量化收益。

## 0.4.1 existing-project adoption

The [isolated adoption protocol](adoption-upgrade.md) adds an existing controller, active data worker, idle reviewer and retained predecessor. It exercises deferred version checks during a normal CSV task and a stale entry/partial receipt. Real agent outputs and protected-file hashes are evaluated; role states are simulated, so this does not test native interruption, installation or hot reload. Historical cases above keep their original versions and results.
