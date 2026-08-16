# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 执行器退化产出质量门禁 |
| 特性编号 | BUG-ISSUE-22 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | arkui-specs-next |
| SIG 归属 | arkui_architecture |
| 状态 | Approved |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | NV 检查证据义务、组合退化检测、一次完整重试、executor_quality_failed、聚合遥测 | evaluator 0.1.18 生效 |
| MODIFIED | Claim evidence downgrade、Job statistics、HTTP/metrics/UI | 历史 0.1.17 保持兼容 |
| REMOVED | evaluator 0.1.18 的 evidence-free NOT_VERIFIABLE | 不回写历史运行 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Requirement | proposal.md | Approved |

## 用户故事

### US-1: 识别并恢复执行器退化输出

作为 evaluator 运维者，我想要无证据的批量 NOT_VERIFIABLE 被拒绝并有限重试，以便避免退化结果污染报告，同时保留真实证据不足场景。

| AC编号 | 验收标准 | 可观察表面 | 类型 |
|--------|----------|--------------|------|
| AC-1.1 | WHEN evaluator 0.1.18 接收到 NOT_VERIFIABLE observation、Claim 或 atomic unit，且未提供 review_record 检查证据或未说明检查范围、缺失证据和不足原因 THEN 校验结果返回明确错误并拒绝该候选 | 终端用户（evaluator 运维者） | 异常 |
| AC-1.2 | WHEN 一个至少包含 10 条 Claim 的观察结果同时达到不低于 60% 的 NOT_VERIFIABLE、检查证据崩塌，并出现重复文本、零 SUPPORTED 或 CONFLICT、或异常稀疏 observation 中至少一个信号 THEN 服务完整重试该 work item 一次；若重试结果仍退化，Job 失败事件为 executor_quality_failed | 终端用户（evaluator 运维者） | 恢复 |
| AC-1.3 | WHEN 高 NOT_VERIFIABLE 结果引用 review_record 检查证据并给出具体缺口说明 THEN 服务不因 NOT_VERIFIABLE 比例单独拒绝该结果 | 终端用户（evaluator 运维者） | 边界 |
| AC-1.4 | WHEN Codex CLI 输出受支持的稳定 JSONL 工具事件 THEN Job 详情和 metrics 返回工具调用、命令调用、已访问输入及证据路径的聚合计数且不包含原始路径；WHEN JSONL 形态未知 THEN telemetry 显示未报告且 Job 不因此失败 | 终端用户（evaluator 运维者） | 正常 |
| AC-1.5 | WHEN evaluator 恢复 0.1.17 staged run 或服务打开 schema v1、v2、v3 数据库 THEN 0.1.17 继续允许其历史 NV evidence 基数，并且数据库无损升级为 schema v4 | 终端用户（evaluator 运维者） | 兼容 |

## 验收追溯

| AC | 关联规则 | 可观察表面 | 关联 Task | 验证方式 | 证据 |
|----|----------|--------------|-----------|----------|------|
| AC-1.1 | R-1 | 终端用户看到 staged validation error | TASK-1 | Python unittest | evidence/reviews/verification.md |
| AC-1.2 | R-2、R-3 | 终端用户看到 retry 事件或 executor_quality_failed | TASK-2 | Python unittest | evidence/reviews/verification.md |
| AC-1.3 | R-4 | 终端用户看到合法高 NV 被接受 | TASK-2 | Python unittest | evidence/reviews/verification.md |
| AC-1.4 | R-5 | 终端用户看到 Job API、metrics 和 UI 聚合遥测 | TASK-3 | Python unittest、JS syntax | evidence/reviews/verification.md |
| AC-1.5 | R-6 | 终端用户可恢复历史运行并打开旧数据库 | TASK-1、TASK-3 | Python unittest | evidence/reviews/verification.md |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界或约束 | 关联AC |
|--------|------|----------|----------|------------|--------|
| R-1 | 异常 | evaluator 0.1.18 的 NV 缺少 inspection evidence 或三段式缺口说明 | 返回定位到 observation、Claim 或 unit 的校验错误 | 只对 0.1.18 及以后生效 | AC-1.1 |
| R-2 | 行为 | 高 NV、evidence collapse 与 corroborating signal 同时成立 | 产生一次完整 quality retry | Claim 数至少 10，单一信号不触发 | AC-1.2 |
| R-3 | 恢复 | quality retry 再次退化或 executor 无法成功返回 | Job 失败并产生 executor_quality_failed | 每个 work item 最多重试一次 | AC-1.2 |
| R-4 | 边界 | 高 NV 但 inspection coverage 充分 | 不因 NV 比例单独失败 | 合法证据不足必须保留具体检查记录 | AC-1.3 |
| R-5 | 行为 | 识别到稳定 item.completed 工具事件 | 返回非敏感聚合计数 | 未知 JSONL 只标记 unavailable | AC-1.4 |
| R-6 | 恢复 | 历史 evaluator 0.1.17 或 schema v1-v3 输入 | 保持旧运行可读并升级存储 | 不重写历史评价语义 | AC-1.5 |

## 验证映射

| 编号 | 对应规格项 | 测试入口 | 验证方式 | Red 条件（实现前失败信号） | 通过标准 |
|------|------------|----------|----------|---------------------------|----------|
| VM-1 | R-1 / AC-1.1 | tools/spec_eval/tests/test_next_007_skill.py::test_staged_v2_0118_not_verifiable_requires_inspection_evidence | 单测 | 旧规则允许 NV observation、Claim 和 unit 使用空 evidence_ids | 缺失 review_record 或具体说明时返回校验错误，合法记录通过 |
| VM-2 | R-2、R-3 / AC-1.2 | tools/spec_eval/tests/test_next_012_contract_alignment.py::test_issue_22_degenerate_observation_is_retried_as_full_work_item | 单测 | 旧服务直接进入普通 semantic failure 且不重试 | 首次退化完整重试，第二次退化产生 executor_quality_failed |
| VM-3 | R-4 / AC-1.3 | tools/spec_eval/tests/test_next_012_contract_alignment.py::test_issue_22_high_nv_with_inspection_evidence_is_not_degenerate | 单测 | 固定 NV 比例硬门槛会误伤合法高 NV | 高 NV 有 inspection evidence 时不触发退化重试 |
| VM-4 | R-5 / AC-1.4 | tools/spec_eval/tests/test_next_011_codex_executor.py::test_unknown_jsonl_shape_leaves_telemetry_unavailable | 单测 | 旧 ExecutionResult、Job API 和 metrics 没有 telemetry | 已知形态计数正确，未知形态 reported 为 false 且不失败 |
| VM-5 | R-6 / AC-1.5 | tools/spec_eval/tests/test_next_012_rolling_reports.py::test_v3_database_adds_executor_telemetry_columns | 单测 | 旧 schema 缺少 v4 telemetry 列且 0.1.17 可能被新规则误拒 | v1-v3 均升级，0.1.17 回归继续通过 |

## API 变更分析

### 新增 API

N/A：不新增 OpenHarmony Public、System 或 InnerAPI。

### 变更/废弃 API

N/A：不变更或废弃 OpenHarmony Public、System 或 InnerAPI。

### API 与错误码事实

N/A：本变更仅调整 evaluator 内部数据契约、事件分类和运维展示，不涉及 OpenHarmony API 或错误码。

## 接口规格

无新增对外接口规格。现有 Job 详情文档增加 executor_telemetry 字段，现有 metrics 文档增加 executor_telemetry 汇总；两者均属于服务内部运维表面。

## 兼容性声明

- 已有 API 行为变更：否，OpenHarmony API 无变化。
- 配置文件格式变更：否。
- 数据存储格式变更：是，SQLite schema 3 升级为 4，v1-v3 增量迁移。
- 最低支持版本：evaluator 0.1.18 启用新质量规则；0.1.17 历史运行保持旧规则。
- API 版本号策略：N/A，无 Public/System API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 版本隔离 | 新 NV 规则仅对 0.1.18 开启 | AC-1.1、AC-1.5 |
| 组合判断 | 单一 NV 比例或单一 telemetry 信号不得触发失败 | AC-1.2、AC-1.3 |
| 有界恢复 | 每个退化 work item 最多完整重试一次 | AC-1.2 |
| 非敏感遥测 | 仅返回聚合计数，不持久化原始命令或路径 | AC-1.4 |

## 非功能性需求

| 类型 | 指标或阈值 | 验证方式 | 证据 |
|------|------------|----------|------|
| 性能 | 质量退化最多额外执行一次完整 work item | pipeline 单测 | evidence/reviews/verification.md |
| 安全 | telemetry 输出不包含原始路径或命令字符串 | executor 和 serializer 单测 | evidence/reviews/verification.md |
| 可靠性 | 未知 JSONL 不成为独立失败条件 | executor 单测 | evidence/reviews/verification.md |
| 可测试性 | 所有 AC 均有自动化 unittest 入口 | 全量 unittest | evidence/reviews/verification.md |

## 多设备适配声明

无差异：该变更是主机侧 Python evaluator 服务，与设备形态无关。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | N/A | 无产品 UI 变化 | 无 |
| 大字体 | N/A | 无产品 UI 变化 | 无 |
| 深色模式 | N/A | 运维 UI 沿用现有样式 | AC-1.4 |
| 多窗口或分屏 | N/A | 无产品 UI 变化 | 无 |
| 多用户 | N/A | 无用户数据变化 | 无 |
| 版本升级 | 是 | evaluator 0.1.17 和 schema v1-v3 兼容 | AC-1.5 |
| 生态兼容 | 是 | 历史 staged run 可恢复 | AC-1.5 |

## Spec 自审清单

- [x] 无未解决占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可独立测试
- [x] 每个 AC 声明终端用户可观察表面
- [x] THEN 未描述内部类、方法、锁或算法
- [x] 范围边界明确
- [x] AC 与规则表交叉一致
- [x] 无 OpenHarmony API 和错误码事实需要登记
- [x] 每个 AC 的验证映射包含真实入口、Red 条件和通过标准

## context-references

未使用外部架构查询；以 Issue 22、AGENTS.md、仓内源码和测试为事实来源。
