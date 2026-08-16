---
phase: define
phase_status: approved
approval:
  status: approved
  approver: "user"
  evidence: "2026-08-16 direct instruction: 按照推荐进行修改，完成后提交PR并关联issue"
  approved_at: "2026-08-16T15:00:00+08:00"
target_release:
  id: arkui-specs-next
  status: proposed
---

# 需求文档

## 一、原始需求

### 基本信息

| 字段 | 内容 |
|------|------|
| 需求ID | ISSUE-22 |
| 需求名称 | 执行器退化产出检测、重试与独立失败分类 |
| 来源 | GitCode Issue 22 |
| 提出人 | arkui_architecture |
| 目标发行版本 | arkui-specs-next |
| 候选 Profile | none，仓库 arkui-specs 未命中产品代码 Profile |
| 优先级 | P1 |
| Define 阶段状态 | Approved |

### 原始描述

Issue 22 报告 evaluator 0.1.17 的一次观察阶段产出未读取证据切片、Spec、Design 或源码，却将 49/70 条 Claim 判为 NOT_VERIFIABLE。现有校验依赖模型同时遗漏其他结构才拦截，NOT_VERIFIABLE 仍可成为免证据逃生门，服务也缺少退化检测、自动重试和独立失败分类。

期望结果是：NOT_VERIFIABLE 具备最低检查证据义务；疑似退化产出被组合信号识别并完整重试一次；重复退化以 executor_quality_failed 分类；执行器检查活动可通过非敏感聚合遥测辅助排障。

### 背景证据

| 证据类型 | 链接或路径 | 说明 |
|----------|------------|------|
| Issue | https://gitcode.com/arkui_architecture/arkui-specs/issues/22 | 原始现场、根因和修复建议 |
| 基线提交 | 313e7217849142c9771d4a0534455368e29a62a8 | Issue 21 合入后的 main 基线 |
| 实现提交 | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | 本次实现和回归测试 |

### 初始范围

包含 evaluator 0.1.18 的观察契约、质量判断、一次完整重试、失败事件、Codex JSONL 聚合遥测、SQLite schema v4、HTTP/metrics/UI 展示、文档与回归测试。

明确不包含模型供应商策略调整、无限重试、原始命令或路径持久化、生产 ArkUI 组件代码、Public/System API 变更和历史 0.1.17 结果语义重写。

### Agent Scope Guard

| 维度 | 允许范围或限制 | 越界触发条件 | 处理规则 |
|------|----------------|--------------|----------|
| 允许检索仓库 | arkui-specs 单仓 | 需要修改 ace_engine、sdk-js 或 sdk_c | 停止并重新确认范围 |
| 允许模块或目录 | skills/ohos-design-arkui-spec-evaluator、tools/spec_eval、.codespec | 需要修改功能规格正文或其他工具 | 更新 proposal 并重新批准 |
| 禁止访问或修改 | 父仓未提交文件、凭据、历史评价归档、生成结果 | 任何修改命中禁止项 | 标记 Blocked 并停止 |
| 外部网络或私有知识源 | GitCode Issue 22 与仓库 remote；不需要私有知识源 | 需要新增授权来源 | 请求用户授权 |

### 初始假设

| 假设 | 类型 | 验证方式 | 状态 |
|------|------|----------|------|
| 单一 NOT_VERIFIABLE 比例不能区分合法证据不足与执行器退化 | 技术 | 对比 Issue 现场与合法高 NV 测试 | 已验证 |
| 稳定 Codex JSONL 事件可提供非敏感计数 | 技术 | executor 单测覆盖已知和未知事件形态 | 已验证 |
| 历史 evaluator 0.1.17 必须保持可恢复 | 兼容性 | 版本隔离回归测试 | 已验证 |

### 初始分级判断

| 判断项 | 结果 | 依据 |
|--------|------|------|
| 复杂度 | 标准 | 单仓但跨契约、流水线、执行器、存储、API 和 UI |
| 涉及仓数量 | 1 | arkui-specs |
| 是否涉及 Public/System API | 否 | 仅 evaluator 内部协议和运维展示 |
| 是否涉及安全或性能关键路径 | 否 | 遥测不保存原始路径或命令内容 |
| 是否跨 SIG | 否 | spec evaluator 内部变更 |

## 二、澄清记录

### 待澄清问题

| 编号 | 问题 | 为什么需要澄清 | 状态 |
|------|------|----------------|------|
| Q-1 | 是否仅凭高 NV 比例失败 | 可能误伤真实证据不足 | 已澄清：必须组合证据崩塌和独立退化信号 |
| Q-2 | 退化后重试粒度和次数 | 控制成本并避免局部修补污染 | 已澄清：完整 work item，最多一次 |
| Q-3 | 历史运行是否采用新 NV 规则 | 避免破坏恢复兼容性 | 已澄清：0.1.17 保持旧规则 |
| Q-4 | 遥测是否可作为独立失败条件 | JSONL 形态可能随 CLI 变化 | 已澄清：仅辅助诊断，不独立失败 |

### 讨论记录

| 日期 | 参与人 | 讨论主题 | 结论 | 后续动作 |
|------|--------|----------|------|----------|
| 2026-08-16 | user、Codex | Issue 22 推荐方案 | 用户授权按推荐方案实施并提交 PR | 实施、验证、提交并关联 Issue 22 |

### 方案探索

| 编号 | 方案概述 | 优势 | 风险或代价 | 选择结论 |
|------|----------|------|------------|----------|
| A-1 | 固定 NV 比例硬失败 | 简单 | 合法高 NV 场景误报，无法证明是否检查过证据 | 放弃 |
| A-2 | NV 检查证据义务加组合质量信号加一次完整重试 | 区分合法证据不足与退化，具有恢复能力 | 增加一次执行成本和版本契约 | 推荐 |
| A-3 | 仅依赖命令数和时长 | 接近 Issue 现场 | JSONL 兼容性和运行环境差异导致脆弱 | 作为遥测，不作独立门禁 |

取舍理由：A-2 同时堵住免证据出口并保留合法高 NV，且只在多个独立信号同时成立时重试，误报和成本可控。

### 上下文与知识源检索日志

| 编号 | 来源 | 查询或读取内容 | 关键发现 | 可信度 | 用于 | 命中或原因 |
|------|------|----------------|----------|--------|------|------------|
| K-1 | GitCode Issue 22 | 现场指标、根因、修复建议 | 退化输出零证据读取、49/70 NV、缺少重试与分类 | 高 | 范围和 AC | 命中 |
| K-2 | AGENTS.md | 仓库验证、KB-first 和工作区边界 | 需真实源码证据并保护父仓改动 | 高 | 执行约束 | 命中 |
| K-3 | docs/kb_search.py evaluator | evaluator 关键词 | 仅命中动画插值知识库，与 spec evaluator 无关 | 高 | 检索路由 | 弱命中，转源码 |
| K-4 | 仓内源码和测试 | staged_run_support、semantic_stage、executor、store、tests | 确认版本门控、修复路由、迁移和测试入口 | 高 | design 和验证 | 命中 |

### API 变更评估

| 问题 | 回答 | 确认人 | 状态 |
|------|------|--------|------|
| 是否需要新增或修改 Public API | 否 | user 授权范围 | 已确认 |
| 是否需要新增 System API | 否 | user 授权范围 | 已确认 |
| 是否会废弃已有 API | 否 | user 授权范围 | 已确认 |
| 是否需要新增权限声明 | 否 | user 授权范围 | 已确认 |

### 兼容性与非功能需求

| 类别 | 核心问题 | 结论 | 确认人 | 状态 |
|------|----------|------|--------|------|
| 兼容性 | 0.1.17 历史运行能否恢复 | 保留旧 NV evidence 基数，0.1.18 才启用新规则 | user、Codex | 已确认 |
| 性能 | 重试是否无限放大成本 | 每个退化 work item 最多完整重试一次 | user、Codex | 已确认 |
| 安全 | 是否记录敏感命令或路径 | 只持久化聚合计数，不返回原始字符串 | user、Codex | 已确认 |
| 可靠性 | 未知 JSONL 是否导致任务失败 | telemetry_reported 为 false，不单独失败 | user、Codex | 已确认 |

### 澄清结论

- [x] 功能范围已完全明确
- [x] 子系统影响已识别
- [x] API 变更已评估
- [x] 兼容性和非功能需求已确认
- [x] 依赖和风险已识别且有缓解方案
- [x] AC 完整可测试
- [x] 标准复杂度已完成三方案探索

结论：通过。

## 三、需求基线

### 基线信息

| 字段 | 内容 |
|------|------|
| 基线版本 | v1.0 |
| 基线日期 | 2026-08-16 |
| Owner | arkui_architecture |
| 确认人 | user |
| 复杂度 | 标准 |
| Profile | none |
| 目标发行版本 | arkui-specs-next |
| 版本状态 | proposed |

### 问题陈述

spec evaluator 允许 NOT_VERIFIABLE 在无检查证据时通过，且无法识别一次执行器随机退化，也无法将退化失败与普通语义契约错误分流，导致无证据结论可能污染评分或让长任务无恢复机会。

### 目标和成功指标

| 目标 | 成功指标 | 验证方式 |
|------|----------|----------|
| 堵住 NV 免证据出口 | evaluator 0.1.18 的 NV observation、Claim 和 unit 均有 review_record 证据与具体缺口说明 | 契约单测 |
| 自动恢复随机退化 | 组合信号命中后完整重试一次；再次退化独立失败 | pipeline 单测 |
| 保留合法高 NV | 有检查证据的高 NV 不因比例单独失败 | 反例单测 |
| 提供辅助遥测 | 已知 JSONL 产生聚合计数，未知形态不失败 | executor、store、HTTP、metrics 单测 |
| 保持兼容 | 0.1.17 和 schema v1-v3 可继续读取或迁移 | 兼容回归测试 |

### 用户故事与 AC

| Story ID | 用户故事 | 优先级 |
|----------|----------|--------|
| US-1 | 作为 evaluator 运维者，我希望无证据退化输出被识别并有限重试，以免污染报告并缩短随机失败恢复时间 | P1 |

| AC编号 | 验收标准 | 类型 | 关联Story |
|--------|----------|------|-----------|
| AC-1.1 | WHEN evaluator 0.1.18 提交 NOT_VERIFIABLE 结果 THEN 无 review_record 引用或无具体缺口说明的结果被拒绝 | 异常 | US-1 |
| AC-1.2 | WHEN 观察结果同时满足高 NV、检查证据崩塌和独立退化信号 THEN 完整重试一次，重复退化以 executor_quality_failed 结束 | 恢复 | US-1 |
| AC-1.3 | WHEN 高 NV 结果具有检查证据和具体说明 THEN 不因 NV 比例单独被判退化 | 边界 | US-1 |
| AC-1.4 | WHEN Codex 输出已知稳定 JSONL 工具事件 THEN 运维界面可观察聚合计数；未知形态不导致任务失败 | 正常 | US-1 |
| AC-1.5 | WHEN 恢复 evaluator 0.1.17 运行或打开 schema v1-v3 数据库 THEN 历史 NV 规则保持且数据库升级到 v4 | 兼容 | US-1 |

### 范围边界

包含：evaluator 契约、语义流水线、Codex executor、Job statistics、HTTP/metrics/UI、测试和说明文档。

不包含：模型参数或供应商切换、无限重试、保存原始命令和路径、ArkUI 产品代码、Public/System API。

### 影响范围

| 子系统 | 仓库 | 模块或路径 | 当前职责 | 影响类型 | Owner |
|--------|------|------------|----------|----------|-------|
| Spec evaluator | arkui-specs | skills/ohos-design-arkui-spec-evaluator | 评价契约和执行说明 | 修改 | arkui_architecture |
| Semantic service | arkui-specs | tools/spec_eval | 执行、校验、存储和 UI | 修改 | arkui_architecture |

### API 变更项清单

N/A：不新增、修改或废弃 OpenHarmony Public、System 或 InnerAPI。

### 不涉及项确认

| 维度 | 涉及？ | 依据 | 若涉及，进入哪个下游文档 |
|------|--------|------|--------------------------|
| 性能 | 是 | 自动重试次数必须有上限 | design.md、spec.md |
| 安全与权限 | N/A | 不引入权限、凭据或敏感数据存储 | 无 |
| 兼容性 | 是 | evaluator 0.1.17 与 schema v1-v3 | spec.md、design.md |
| API/SDK | N/A | 无 OpenHarmony API 或 SDK 变化 | 无 |
| IPC/跨进程 | N/A | 单进程 Python 服务 | 无 |
| 构建与部件 | N/A | 无 BUILD.gn 或 bundle.json 改动 | 无 |
| 国际化/无障碍 | N/A | 仅增加英文运维指标标签 | 无 |
| 数据迁移 | 是 | SQLite schema v4 增量迁移 | design.md、spec.md |

### 进入设计或 Spec 条件

- [x] 所有 P0/P1 用户故事有 AC
- [x] 每条 AC 可测试、可度量
- [x] 范围内外已确认
- [x] 目标版本已明确
- [x] manifest.profile 已明确为 none
- [x] 涉及仓和模块已识别
- [x] 不涉及项已标记 N/A 并说明依据
- [x] Agent Scope Guard 已基线化
- [x] 上下文与知识源检索日志已填写
- [x] AGENTS.md 已读取并记录关键约束

基线结论：通过。用户对推荐方案的直接实施授权作为本次 Define approval evidence。
