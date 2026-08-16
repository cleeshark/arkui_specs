# 架构设计

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-ISSUE-22 |
| 关联需求 | proposal.md |
| 关联 Epic | 无 |
| 目标 Feature | BUG-ISSUE-22 |
| 复杂度 | 标准 |
| 目标版本 | arkui-specs-next |
| Owner | arkui_architecture |
| 状态 | Approved |

## 需求基线

| 项 | 补充说明 |
|----|----------|
| NV evidence obligation | evaluator 0.1.18 才启用，0.1.17 保持兼容 |
| degeneration detection | 高 NV 必须与 evidence collapse 和独立质量信号组合 |
| recovery budget | 一个 work item 最多完整重试一次 |
| telemetry privacy | 只跨 executor 边界传递聚合计数 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 补充架构说明 |
|------|-------------|
| arkui-specs | evaluator Skill 定义契约；tools/spec_eval service 执行、校验、存储并展示结果 |

### 代码事实基线

| 代码引用（文件:行或符号） | 已验证事实 | 关联架构规则 | 对本设计的约束 | 验证来源或可信度 |
|---------------------------|------------|--------------|----------------|------------------|
| skills/ohos-design-arkui-spec-evaluator/scripts/staged_run_support.py:95 | NV_INSPECTION_EVIDENCE_EVALUATOR_VERSIONS 只包含默认 evaluator 0.1.18 | OH-ARCH-COMPAT | 新证据义务不得回溯应用到 0.1.17 | 源码与版本回归测试，高 |
| skills/ohos-design-arkui-spec-evaluator/scripts/staged_run_support.py:827 | NV reason 和 fact 通过检查范围、缺失证据与不足后果三类术语判定 | OH-ARCH-CONTRACT | observation、Claim、unit 必须采用同一解释义务 | 源码与契约测试，高 |
| tools/spec_eval/service/pipeline/observation_quality.py:39 | 质量判断组合 NV 比例、证据覆盖、重复文本、decisive outcome 和 observation 数量 | OH-ARCH-RELIABILITY | 不得使用单一 NV 阈值作为失败依据 | 源码与正反例测试，高 |
| tools/spec_eval/service/pipeline/semantic_stage.py:223 | 重试 executor 失败或第二次退化都转换为 executor_quality_failed | OH-ARCH-ERROR-LOG | 质量失败与 semantic_failed 必须分流 | 源码与 pipeline 测试，高 |
| tools/spec_eval/service/executors/telemetry.py:31 | accumulator 仅输出四个整数计数且不返回路径 | OH-ARCH-PRIVACY | HTTP、metrics 和 DB 不得保存原始 command/path | 源码与 executor 测试，高 |
| tools/spec_eval/service/store/sqlite_store.py:30 | schema 版本为 4，v1-v3 通过缺列检测增量升级 | OH-ARCH-DATA-MIGRATION | 新列必须有非负默认值并保持旧库可打开 | 源码与 migration 测试，高 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| 契约层 | evaluator Skill 与 staged_run_support | 发布并校验 0.1.18 NV 证据规则 | 修改 |
| 流水线层 | observation_quality 与 semantic_stage | 组合判断、一次完整重试和失败分类 | 新增、修改 |
| 执行器层 | codex_cli、contract、telemetry | 强化重试 prompt 并采集稳定 JSONL 聚合计数 | 新增、修改 |
| 存储层 | models、repositories、schema、sqlite_store | 持久化 schema v4 计数并迁移旧库 | 修改 |
| 可观察层 | serializers、metrics、UI | 暴露聚合遥测和质量失败事件 | 修改 |
| 验证层 | tools/spec_eval/tests | 覆盖契约、重试、反例、遥测和迁移 | 修改 |

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-COMPAT | evaluator 版本和 DB schema 均有历史输入 | 规则按 evaluator version 隔离，DB 采用 additive migration | 兼容单测 |
| OH-ARCH-RELIABILITY | LLM 输出存在随机退化 | 多信号判断且最多重试一次 | pipeline 正反例单测 |
| OH-ARCH-ERROR-LOG | 排障需要区分协议错误和质量失败 | 新增 executor_quality_failed 事件类型 | events 与 metrics 单测 |
| OH-ARCH-PRIVACY | executor 事件可能包含路径或命令 | 只持久化整数计数 | executor、serializer 单测 |

### 既有模式复用

| 模式 | 参考代码（文件:行或符号） | 适用架构规则 | 必须复用的约定 | 本设计的复用方式 | 偏差及理由 | 关联 Task |
|------|---------------------------|--------------|------------------|------------------|------------|-----------|
| evaluator version feature gate | skills/ohos-design-arkui-spec-evaluator/scripts/staged_run_support.py:38 | OH-ARCH-COMPAT | 新规则由 evaluator version 集合控制 | 增加 NV_INSPECTION_EVIDENCE_EVALUATOR_VERSIONS | 无 | TASK-1 |
| bounded semantic repair | tools/spec_eval/service/pipeline/semantic_stage.py:181 | OH-ARCH-RELIABILITY | 独立结果路径、一次尝试、完整复验 | quality retry 复用 WorkItemInput replace 和事件桥接 | quality retry 是完整重评，不复用 candidate | TASK-2 |
| additive schema migration | tools/spec_eval/service/store/sqlite_store.py:90 | OH-ARCH-DATA-MIGRATION | 检查缺列后 ALTER TABLE，再推进版本 | schema v4 增加五个非负计数列 | 无 | TASK-3 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 性能 | 只在组合退化命中时增加一次完整执行，禁止循环重试 |
| 兼容性 | 0.1.17 使用旧 evidence minimum；schema v1-v3 增量迁移 |
| 数据迁移 | v4 列均为 NOT NULL DEFAULT 0，旧统计保持不变 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|-------------------|----------|------|
| ADR-1 | 如何堵住 NV 免证据出口 | 0.1.18 要求 review_record 且 Claim/unit 引用并说明三段式缺口 | 只要求非空 reason；所有版本统一收紧 | 前者仍可套话，后者破坏历史恢复 | 契约、Skill、repair |
| ADR-2 | 如何识别退化 | 高 NV 加 evidence collapse 加 corroborating signal | 单一 NV 阈值；仅命令数或时长 | 组合信号能保留合法高 NV，且不依赖易变 executor 事件 | quality gate、测试 |
| ADR-3 | 如何恢复随机退化 | 从原始冻结输入完整重试一次 | 修补退化 candidate；无限重试 | 完整重评避免继承污染，一次上限控制成本 | semantic pipeline、executor prompt |
| ADR-4 | 如何记录执行器活动 | 解析稳定 JSONL 并只累计整数 | 保存原始 JSONL；把 telemetry 当硬门禁 | 聚合计数降低敏感性，未知形态不会制造新失败 | executor、DB、API、UI |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|------------|------|
| TASK-1 | 收紧 0.1.18 NV 契约并保持 0.1.17 兼容 | evaluator Skill、staged_run_support、契约测试 | proposal.md、spec.md Approved |
| TASK-2 | 组合质量判断、完整重试和独立失败分类 | observation_quality、semantic_stage、result_payload、executor prompt、pipeline 测试 | TASK-1 |
| TASK-3 | 聚合遥测、schema v4、API/metrics/UI 和文档 | executor telemetry、store、HTTP、metrics、UI、文档和测试 | TASK-2 |

## API 签名、Kit 与权限

无 OpenHarmony Public、System 或 InnerAPI 变更，无权限和 SysCap 影响。

## 构建系统影响

无 BUILD.gn、bundle.json、生成文件或外部依赖变化。

## 可选设计扩展

### 数据流/控制流

| 步骤 | 调用方 | 被调用方 | 数据或接口 | 说明 |
|------|--------|----------|------------|------|
| 1 | semantic_stage | executor | 原始 WorkItemInput | 首次完整评价并收集聚合 telemetry |
| 2 | semantic_stage | observation_quality | observation payload | 计算组合质量信号 |
| 3 | semantic_stage | executor | retry_degenerate_observation contract | 疑似退化时从原始输入完整重试一次 |
| 4 | semantic_stage | staged_run_support | candidate observation | 通过 NV evidence 和完整契约校验 |
| 5 | job statistics | HTTP、metrics、UI | 非敏感整数计数 | 提供辅助排障信息 |

### 状态归属与不变量

#### 状态归属

| State ID | 状态或资源 | 唯一 Owner | 存储或 Key | 创建与初始化 | 读取或更新方 | 清理、恢复或回滚触发 | 并发模型 | 代码事实或规则来源 |
|----------|------------|------------|-------------|--------------|----------------|----------------------|----------|----------------------|
| STATE-1 | 单 work item quality retry budget | semantic_stage | 当前 run_semantic 调用栈 | 首次 quality assessment 前为零次 | semantic_stage 在退化时消费一次 | work item 返回后释放 | worker 内线程封闭 | ADR-2、ADR-3 |
| STATE-2 | 单 executor invocation telemetry | ExecutionTelemetryAccumulator | invocation 内集合和计数器 | executor 启动时归零 | line_sink 更新，ExecutionResult 读取 | executor 返回后转为 snapshot | invocation 内线程封闭 | ADR-4 |
| STATE-3 | Job 聚合 telemetry | JobStatisticsRepository | job_statistics 行 | Job 创建时默认零 | 每次 executor invocation 原子累加 | Job 保留策略统一清理 | SQLite immediate transaction | ADR-4 |

#### 不变量追溯

| Invariant ID | State ID 或范围 | 必须始终成立的约束 | 关联 AC | 关联 Task | 验证方式与通过标准 | 违反时处理 |
|--------------|-----------------|--------------------|---------|-----------|--------------------|------------|
| INV-1 | STATE-1 | 一个 work item 最多执行一次 quality retry | AC-1.2 | TASK-2 | pipeline 单测断言 executor 调用次数为二且无循环 | 以 executor_quality_failed 结束 |
| INV-2 | STATE-2、STATE-3 | telemetry 跨边界只包含非负整数计数，不包含原始命令或路径 | AC-1.4 | TASK-3 | executor、repository 和 serializer 单测检查字段和值 | 丢弃非法值并记零 |
| INV-3 | evaluator 0.1.17、schema v1-v3 | 新规则不得破坏历史运行或旧库打开 | AC-1.5 | TASK-1、TASK-3 | 历史版本和迁移回归测试通过 | 停止发布并修复兼容层 |

### 算法与状态机

| 转移 | 触发条件 | Guard | 状态变化或副作用 | 关联不变量 | 异常与恢复 | 验证方式 |
|------|----------|-------|------------------|------------|------------|----------|
| First result → Retry | 组合退化判断为 true | STATE-1 尚未消费 | INV-1 消费唯一重试预算并写独立结果路径 | INV-1 | retry executor 失败则 quality failed | pipeline 单测 |
| Retry → Accepted | 第二次质量判断为 false | staged contract 继续校验 | 使用 retry payload | INV-1、INV-3 | 普通契约错误仍走 semantic_failed | pipeline 单测 |
| Retry → Failed | 第二次仍退化 | 已消费唯一预算 | 产生 executor_quality_failed | INV-1 | 不再重试 | pipeline 单测 |
| JSONL event → Snapshot | 已知稳定事件 | item.completed 且工具类型受支持 | STATE-2 更新，随后累加到 STATE-3 | INV-2 | 未知形态 reported 为 false | executor 和 store 单测 |

### 资源所有权矩阵

| 资源或 State ID | 创建方 | 持有方 | 借用或只读消费者 | 销毁触发 | 实际释放 | 异常回收 | 关联不变量 |
|-----------------|--------|--------|--------------------|----------|----------|----------|------------|
| STATE-1 | semantic_stage | 当前 work item | event payload | work item 完成或失败 | Python 调用栈 | 返回失败结果 | INV-1 |
| STATE-2 | CodexCliExecutor | telemetry accumulator | ExecutionResult | invocation 完成 | Python 对象生命周期 | snapshot 保留零值 | INV-2 |
| STATE-3 | JobStatisticsRepository | SQLite job_statistics | serializers、metrics | Job 清理 | governance 清理流程 | 事务回滚 | INV-2、INV-3 |

### 测试性设计

| 测试层级 | 测试目标 | Mock 策略 | 验证方式 |
|----------|----------|-----------|----------|
| 单元测试 | NV 契约、退化判断、重试、遥测、迁移 | ScriptedExecutor、临时 SQLite、模拟 JSONL | PYTHONPATH=tools python3 -m unittest discover -s tools/spec_eval/tests -p test_*.py |
| 静态检查 | Python 和 JS 语法、协议、索引与规格 | 无 | compileall、node --check、protocol_validator、generate_index、validate_specs |

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| Codex JSONL 增加新事件形态 | 兼容性 | telemetry coverage 降低 | 保守标记 unreported，不影响 Job 成败 | arkui_architecture |
| 组合阈值需要长期校准 | 可靠性 | 误报或漏报 | 事件 payload 保存 reason_codes 与 metrics，后续基于真实运行调整 | arkui_architecture |
| quality retry 增加单次成本 | 性能 | 退化场景执行时间增加 | INV-1 限制最多一次 | arkui_architecture |

## 设计审批

- [x] 需求基线已确认并覆盖所有 AC
- [x] 不涉及项已承接
- [x] 调用链层级和职责清楚
- [x] 代码事实均有文件和行号
- [x] 已记录既有模式复用
- [x] 分层和模块边界合规
- [x] STATE 和 INV 的 Owner、生命周期、AC、Task 与验证完整
- [x] 无 OpenHarmony API、BUILD.gn 或 bundle.json 影响
- [x] 关键决策包含备选方案和取舍
- [x] 风险有 Owner 和缓解措施

结论：通过。Reviewer 为 Codex，证据为源码审阅和 503 项全量回归。
