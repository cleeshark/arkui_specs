# 执行计划

## Plan 元数据

| 字段 | 内容 |
|------|------|
| Plan ID | PLAN-ISSUE-22 |
| 关联 Feature 或 Bug | BUG-ISSUE-22 |
| 关联文档 | proposal.md、spec.md、design.md |
| 复杂度 | 标准 |
| 状态 | Approved |
| Owner | arkui_architecture |

## 输入状态

| 输入 | 路径 | 要求状态 |
|------|------|----------|
| Requirement | proposal.md | Approved |
| Design | design.md | Approved |
| Spec | spec.md | Approved |

## 执行原则

- Spec 是用户可观察行为的权威来源，版本兼容和一次重试上限不得在实现中漂移。
- 每个 Task 使用直接覆盖其 AC 的自动化测试和 fresh 全量回归作为证据。
- 只能修改受影响文件全量清单中的路径；本次没有生成文件和外部依赖变更。
- STATE-1、STATE-2、STATE-3 的 Owner 和 INV-1、INV-2、INV-3 必须与 design.md 一致。
- 实际 Code Ref、Commit、Review Evidence 和 Actual Result 均回填真实值。

## 受影响文件全量清单

| 仓 | 层 | 文件路径 | 修改类型 | 说明 |
|----|----|----------|----------|------|
| arkui-specs | 契约层 | skills/ohos-design-arkui-spec-evaluator/SKILL.md | 修改 | 发布 0.1.18 NV 检查证据义务 |
| arkui-specs | 契约层 | skills/ohos-design-arkui-spec-evaluator/references/input-output-contract.md | 修改 | 记录退化检测、重试和兼容性 |
| arkui-specs | 契约层 | skills/ohos-design-arkui-spec-evaluator/references/staged-run-contract.md | 修改 | 定义 NV evidence 与 quality retry |
| arkui-specs | 契约层 | skills/ohos-design-arkui-spec-evaluator/scripts/create_pilot_template.py | 修改 | 默认 evaluator 版本升级 |
| arkui-specs | 契约层 | skills/ohos-design-arkui-spec-evaluator/scripts/staged_run_support.py | 修改 | 校验 NV review_record、解释和历史隔离 |
| arkui-specs | 文档层 | tools/spec_eval/README.md | 修改 | 记录 evaluator 0.1.18 行为 |
| arkui-specs | 文档层 | tools/spec_eval/SEMANTIC_SERVICE.md | 修改 | 记录质量门禁、重试和 schema v4 |
| arkui-specs | 存储层 | tools/spec_eval/service/domain/models.py | 修改 | JobStatistics 增加 telemetry 计数 |
| arkui-specs | 执行器层 | tools/spec_eval/service/executors/codex_cli.py | 修改 | 采集 telemetry 并强化 quality retry prompt |
| arkui-specs | 执行器层 | tools/spec_eval/service/executors/contract.py | 修改 | executor 0.4 与 telemetry result fields |
| arkui-specs | 执行器层 | tools/spec_eval/service/executors/telemetry.py | 新增 | 保守解析稳定 Codex JSONL 并聚合计数 |
| arkui-specs | 存储层 | tools/spec_eval/service/governance.py | 修改 | schema 版本同步为 4 |
| arkui-specs | 可观察层 | tools/spec_eval/service/http/serializers.py | 修改 | Job detail 输出 executor_telemetry |
| arkui-specs | 可观察层 | tools/spec_eval/service/metrics.py | 修改 | metrics 汇总 telemetry 和 quality failure |
| arkui-specs | 流水线层 | tools/spec_eval/service/pipeline/context.py | 修改 | 默认 evaluator 版本升级 |
| arkui-specs | 流水线层 | tools/spec_eval/service/pipeline/observation_quality.py | 新增 | 多信号退化判断 |
| arkui-specs | 流水线层 | tools/spec_eval/service/pipeline/result_payload.py | 修改 | quality retry 和 claim repair contract |
| arkui-specs | 流水线层 | tools/spec_eval/service/pipeline/semantic_stage.py | 修改 | 一次完整重试和 executor_quality_failed |
| arkui-specs | 存储层 | tools/spec_eval/service/store/repositories.py | 修改 | 原子累计 telemetry 计数 |
| arkui-specs | 存储层 | tools/spec_eval/service/store/schema.sql | 修改 | schema v4 新列 |
| arkui-specs | 存储层 | tools/spec_eval/service/store/sqlite_store.py | 修改 | v1-v3 到 v4 增量迁移 |
| arkui-specs | 可观察层 | tools/spec_eval/service/ui/app.js | 修改 | Job detail 展示聚合 telemetry |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_007_skill.py | 修改 | NV 契约和 0.1.17 兼容测试 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_011_codex_executor.py | 修改 | telemetry 和 retry prompt 测试 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_011_governance.py | 修改 | metrics telemetry 测试 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_011_http.py | 修改 | Job detail telemetry 测试 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_011_phase4.py | 修改 | schema v4 fixture 同步 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_011_pipeline.py | 修改 | schema v4 fixture 同步 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_011_semantic_service.py | 修改 | repository telemetry 累计测试 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_012_contract_alignment.py | 修改 | Issue 22 重试、失败和合法高 NV 测试 |
| arkui-specs | 验证层 | tools/spec_eval/tests/test_next_012_rolling_reports.py | 修改 | schema v3 到 v4 迁移测试 |

## AC 到 Task 追溯

| AC | 来源 | Task | 计划代码范围 | 实际 Code Ref | Commit | Review Evidence | 验证状态 |
|----|------|------|--------------|-----------------|--------|-----------------|----------|
| AC-1.1 | spec.md | TASK-1 | evaluator Skill 与 staged_run_support | staged_run_support.py:95、827、854 | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | Pass |
| AC-1.2 | spec.md | TASK-2 | observation_quality、semantic_stage、result_payload、executor prompt | observation_quality.py:39、semantic_stage.py:181、684 | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | Pass |
| AC-1.3 | spec.md | TASK-2 | 多信号反例和 pipeline 测试 | observation_quality.py:87、test_next_012_contract_alignment.py:1100 | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | Pass |
| AC-1.4 | spec.md | TASK-3 | telemetry、store、HTTP、metrics、UI | telemetry.py:31、serializers.py:83、app.js:257 | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | Pass |
| AC-1.5 | spec.md | TASK-1、TASK-3 | evaluator version gate 与 schema migration | staged_run_support.py:95、sqlite_store.py:30 | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | Pass |

## 首批实现边界

首批必须实现：0.1.18 NV evidence contract、组合退化检测、一次完整重试、独立失败分类、非敏感 telemetry、schema v4 和回归测试。

可后置：基于真实运行数据调整阈值和支持更多 JSONL 事件类型。

不建议延后：0.1.17 兼容、合法高 NV 反例和 v1-v3 数据迁移。

## Task 依赖

| Task | 前置依赖 | Produces | Consumes |
|------|----------|----------|----------|
| TASK-1 | proposal、spec、design Approved | evaluator 0.1.18 NV contract | Issue 22 基线和历史 0.1.17 contract |
| TASK-2 | TASK-1 | quality assessment、quality retry 和 failure event | TASK-1 发布的 NV contract |
| TASK-3 | TASK-2 | telemetry、schema v4 和运维展示 | TASK-2 的 ExecutionResult 和事件分类 |

## Task 列表

| Task ID | 目标 | 文件范围 | AC 映射 | 前置依赖 | 完成判据 | 验证命令 | 状态 |
|---------|------|----------|---------|----------|----------|----------|------|
| TASK-1 | 收紧 NV 契约并保持历史版本兼容 | evaluator Skill、staged_run_support、契约测试 | AC-1.1、AC-1.5 | 无 | 0.1.18 拒绝无检查证据 NV，0.1.17 继续通过 | 全量 unittest | Done |
| TASK-2 | 检测退化、完整重试一次并分类失败 | quality、semantic pipeline、executor prompt、pipeline 测试 | AC-1.2、AC-1.3 | TASK-1 | 退化正例重试，重复退化独立失败，合法高 NV 不误报 | 全量 unittest | Done |
| TASK-3 | 采集和展示非敏感遥测并升级 schema v4 | executor、store、HTTP、metrics、UI、文档和测试 | AC-1.4、AC-1.5 | TASK-2 | 已知 JSONL 计数正确，未知形态不失败，旧库迁移 | 全量 unittest 与静态门禁 | Done |

## Task 详情

### TASK-1: NV evidence contract and compatibility

| 字段 | 内容 |
|------|------|
| 任务目标 | evaluator 0.1.18 的 NV observation、Claim 和 unit 都具备 review_record 与具体缺口说明，同时 0.1.17 保持旧行为 |
| AC 映射 | AC-1.1、AC-1.5 |
| 前置依赖 | proposal、spec、design Approved |
| 非目标 | 不修改历史运行文件，不引入新的对外 API |
| 完成判据 | 0.1.18 正反例和 0.1.17 兼容测试均通过 |
| 停止条件 | 新规则需要回溯应用到 0.1.17 或改变 Public/System API |
| Design 状态或不变量 | INV-3 |

**状态所有权和生命周期**

| Design Ref | 状态 | Owner | Key 或 Index | 创建 | 读取或更新 | 清理触发 | 生命周期不变量 |
|------------|------|-------|-------------|------|------------|----------|----------------|
| INV-3 | evaluator version contract | staged_run_support | evaluator_version | staged contract 创建时 | validation 读取 | run 结束 | 0.1.17 不采用 0.1.18 NV evidence minimum |

**任务间接口（Produces / Consumes）**

| Direction | Contract | Provider 或 Consumer | Dependency | Compatibility Constraint |
|-----------|----------|----------------------|------------|--------------------------|
| Produces | evaluator 0.1.18 NV evidence and explanation contract | TASK-2 | quality gate 以合法 contract 为后续校验基线 | 0.1.17 规则不变 |
| Consumes | Issue 22 failure evidence and evaluator 0.1.17 contract | proposal、现有源码 | 确定新旧版本边界 | 不修改历史 payload |

**Read-only Context**

| 路径 | 读取目的 |
|------|----------|
| AGENTS.md | 验证和工作区边界 |
| GitCode Issue 22 | 现场和修复目标 |

**Files**

| 操作 | 文件 | 说明 |
|------|------|------|
| Modify | skills/ohos-design-arkui-spec-evaluator | Skill、contract、staged validator 和 version |
| Test | tools/spec_eval/tests/test_next_007_skill.py | 0.1.18 NV 与 0.1.17 兼容回归 |

**禁止修改文件**

| 文件或路径 | 原因 |
|------------|------|
| evaluation/reviews | 正式人工 Review 归档不属于自动修复范围 |
| 父仓未提交文件 | 用户工作区边界 |

**Spec Context**

AC-1.1 要求 0.1.18 的 NV 使用 review_record 并说明检查范围、缺失证据和不足原因；AC-1.5 要求 0.1.17 保持历史 evidence 基数。

**Design Context**

ADR-1 采用版本隔离的最低检查证据义务；INV-3 禁止新规则破坏历史运行。

**Required Rules**

| Rule ID | Must 或 Must Not |
|---------|------------------|
| OH-ARCH-COMPAT | 必须按 evaluator version 隔离，禁止回写历史语义 |

**Steps**

- [x] 增加失败和合法 NV 契约测试
- [x] 升级默认 evaluator 到 0.1.18
- [x] 实现 observation、Claim、unit 的 inspection evidence 和解释校验
- [x] 同步 claim evidence downgrade contract
- [x] 运行全量回归

**Reference Pattern**

| 参考实现 | 复用约定 | 偏差及理由 |
|----------|----------|------------|
| staged_run_support.py:38 | 使用 evaluator version 集合控制规则 | 无 |

**Anti-Fake Completion**

| Check | Required Evidence |
|-------|-------------------|
| AC closed | 0.1.18 缺失 evidence 失败、合法 review_record 通过、0.1.17 兼容三类测试均在 503 项回归中通过 |
| Scope respected | git show e630d949 仅修改已声明 evaluator contract 和对应测试 |
| State lifecycle complete | INV-3 由 evaluator_version 创建和读取，run 结束后无持久状态 |
| Interface contract matched | staged_output_contract 与 validate_observation_document 使用同一版本集合 |
| Relevant verification | test_next_007_skill.py 的 Issue 22 用例包含在全量 unittest |

**Verification**

| 证据类型 | 命令或路径 | Expected Result | Actual Result |
|----------|------------|-----------------|---------------|
| 测试 | PYTHONPATH=tools python3 -m unittest discover -s tools/spec_eval/tests -p test_*.py | 相关 NV 和历史兼容用例通过且全套无失败 | 2026-08-16 fresh run：Ran 503 tests in 105.323s，OK，skipped=1，PASS |
| 静态检查 | python3 tools/spec_eval/protocol_validator.py | protocol valid | rubric 0.3.0、complexity 0.2.0 valid，PASS |

**Handoff Summary**

| 项 | 内容 |
|----|------|
| 任务描述 | 收紧 evaluator 0.1.18 NV contract 并保持 0.1.17 兼容 |
| 允许修改 | skills/ohos-design-arkui-spec-evaluator、test_next_007_skill.py |
| 允许新建 | 无 |
| 只读参考 | AGENTS.md、Issue 22 |
| Spec 摘要 | AC-1.1、AC-1.5 和 R-1、R-6 |
| Design 摘要 | ADR-1、INV-3 |
| 执行步骤 | 测试、版本隔离、契约实现、全量回归 |
| 验证命令 | 全量 unittest，期望 PASS |
| 完成规则 | 不扩大文件范围；没有 fresh verification evidence 不得完成 |

**Review Handoff**

| Reviewer | Input |
|----------|-------|
| Spec Compliance | AC-1.1、AC-1.5 到 staged validator 和测试的追溯 |
| Code Quality | version gate 和 error message 一致性 |
| Verification | 503 项回归和 protocol validator 输出 |

### TASK-2: Degeneration detection and bounded full retry

| 字段 | 内容 |
|------|------|
| 任务目标 | 使用多信号识别退化，完整重试一次并将重复退化分类为 executor_quality_failed |
| AC 映射 | AC-1.2、AC-1.3 |
| 前置依赖 | TASK-1 |
| 非目标 | 不使用 telemetry 作为独立失败条件，不循环重试 |
| 完成判据 | 正例、重复退化和合法高 NV 反例全部通过 |
| 停止条件 | 需要超过一次重试或仅凭单一 NV 比例失败 |
| Design 状态或不变量 | STATE-1、INV-1 |

**状态所有权和生命周期**

| Design Ref | 状态 | Owner | Key 或 Index | 创建 | 读取或更新 | 清理触发 | 生命周期不变量 |
|------------|------|-------|-------------|------|------------|----------|----------------|
| STATE-1、INV-1 | quality retry budget | semantic_stage | 当前 work item | 首次 assessment 前 | 疑似退化时消费一次 | work item 返回 | 最多一次完整 retry |

**任务间接口（Produces / Consumes）**

| Direction | Contract | Provider 或 Consumer | Dependency | Compatibility Constraint |
|-----------|----------|----------------------|------------|--------------------------|
| Produces | quality assessment payload、retry events、executor_quality_failed | TASK-3 | metrics 统计新失败类型并记录 executor invocation | retry 次数固定为一 |
| Consumes | evaluator 0.1.18 NV contract | TASK-1 | 先执行质量判断，再走普通 candidate contract | 0.1.17 不启用 quality gate |

**Read-only Context**

| 路径 | 读取目的 |
|------|----------|
| semantic_stage.py 既有 repair 路由 | 复用有界执行和事件桥接模式 |
| Issue 22 现场指标 | 设计组合信号和失败分类 |

**Files**

| 操作 | 文件 | 说明 |
|------|------|------|
| Create | tools/spec_eval/service/pipeline/observation_quality.py | deterministic composite assessment |
| Modify | tools/spec_eval/service/pipeline/semantic_stage.py | full retry、events、failure type |
| Modify | tools/spec_eval/service/pipeline/result_payload.py | retry contract |
| Modify | tools/spec_eval/service/executors/codex_cli.py | retry prompt constraints |
| Test | tools/spec_eval/tests/test_next_012_contract_alignment.py、test_next_011_codex_executor.py | 正例、反例和 prompt 测试 |

**禁止修改文件**

| 文件或路径 | 原因 |
|------------|------|
| frozen evaluation inputs | retry 必须只读原始冻结输入 |
| aggregation scoring rules | Issue 22 在 observation 阶段解决 |

**Spec Context**

AC-1.2 要求高 NV、evidence collapse 和独立退化信号组合后完整重试一次；AC-1.3 要求合法高 NV 不被比例误伤。

**Design Context**

ADR-2 组合质量信号，ADR-3 独立完整重评，INV-1 限制最多一次。

**Required Rules**

| Rule ID | Must 或 Must Not |
|---------|------------------|
| OH-ARCH-RELIABILITY | 必须组合判断，禁止单一 NV 阈值和无限重试 |
| OH-ARCH-ERROR-LOG | 重复退化必须使用 executor_quality_failed |

**Steps**

- [x] 写退化、重复退化和合法高 NV 测试
- [x] 实现 deterministic assessment 和 reason codes
- [x] 建立独立 quality retry result path 和 prompt contract
- [x] 将 retry executor failure 和第二次退化映射为 executor_quality_failed
- [x] 运行全量回归

**Reference Pattern**

| 参考实现 | 复用约定 | 偏差及理由 |
|----------|----------|------------|
| semantic_stage.py:181 | 有界 executor 调用、独立事件和完整状态处理 | quality retry 不读取或修补旧 candidate |

**Anti-Fake Completion**

| Check | Required Evidence |
|-------|-------------------|
| AC closed | 正例断言 retry started/completed，重复退化断言独立失败，反例断言不重试 |
| Scope respected | git show e630d949 的 quality 变更仅位于声明文件和测试 |
| State lifecycle complete | INV-1 由单次函数调用栈保证，第二次 assessment 后直接接受或失败 |
| Interface contract matched | retry prompt mode 与 Codex executor constraints 名称一致 |
| Relevant verification | test_issue_22 三个 pipeline 用例包含在 503 项回归 |

**Verification**

| 证据类型 | 命令或路径 | Expected Result | Actual Result |
|----------|------------|-----------------|---------------|
| 测试 | PYTHONPATH=tools python3 -m unittest discover -s tools/spec_eval/tests -p test_*.py | 退化正例、重复失败和合法高 NV 反例均通过 | 2026-08-16 fresh run：Ran 503 tests in 105.323s，OK，skipped=1，PASS |
| 语法 | python3 -m compileall -q tools/spec_eval skills/ohos-design-arkui-spec-evaluator/scripts | 无 Python syntax error | exit code 0，无输出，PASS |

**Handoff Summary**

| 项 | 内容 |
|----|------|
| 任务描述 | 组合判断退化并从原始输入完整重试一次 |
| 允许修改 | quality、semantic_stage、result_payload、codex executor 和相关测试 |
| 允许新建 | observation_quality.py |
| 只读参考 | Issue 22、既有 semantic repair 路由 |
| Spec 摘要 | AC-1.2、AC-1.3 和 R-2、R-3、R-4 |
| Design 摘要 | ADR-2、ADR-3、STATE-1、INV-1 |
| 执行步骤 | 测试、assessment、retry contract、失败分类、回归 |
| 验证命令 | 全量 unittest 和 compileall，期望 PASS |
| 完成规则 | 一次 retry 上限和合法高 NV 反例必须同时成立 |

**Review Handoff**

| Reviewer | Input |
|----------|-------|
| Spec Compliance | AC-1.2、AC-1.3 的正反例与事件序列 |
| Code Quality | 组合条件、重试状态分支和 scope-preserving repair |
| Verification | 503 项回归、compileall 与测试断言 |

### TASK-3: Telemetry, schema v4 and observability

| 字段 | 内容 |
|------|------|
| 任务目标 | 从受支持 JSONL 聚合非敏感计数，持久化到 schema v4，并通过 Job API、metrics 和 UI 展示 |
| AC 映射 | AC-1.4、AC-1.5 |
| 前置依赖 | TASK-2 |
| 非目标 | 不保存原始命令、路径或未知 JSONL 内容，不修改产品 UI |
| 完成判据 | executor、repository、migration、HTTP、metrics 和 JS 检查通过 |
| 停止条件 | 需要持久化原始敏感字符串或破坏旧库 |
| Design 状态或不变量 | STATE-2、STATE-3、INV-2、INV-3 |

**状态所有权和生命周期**

| Design Ref | 状态 | Owner | Key 或 Index | 创建 | 读取或更新 | 清理触发 | 生命周期不变量 |
|------------|------|-------|-------------|------|------------|----------|----------------|
| STATE-2、INV-2 | invocation telemetry | ExecutionTelemetryAccumulator | invocation local | executor 启动 | JSONL line_sink 更新 | invocation 结束 | snapshot 仅四个非负整数 |
| STATE-3、INV-2、INV-3 | Job telemetry totals | JobStatisticsRepository | job_id | Job 创建默认零 | 每次 invocation 原子累加 | Job governance 清理 | 旧库迁移后值非负且旧统计保留 |

**任务间接口（Produces / Consumes）**

| Direction | Contract | Provider 或 Consumer | Dependency | Compatibility Constraint |
|-----------|----------|----------------------|------------|--------------------------|
| Produces | executor_telemetry Job detail 和 metrics summary | 运维 UI 和 operator | 展示辅助诊断计数 | 不包含原始字符串 |
| Consumes | ExecutionResult telemetry 和 executor_quality_failed | TASK-2、Codex executor | 累计 invocation 和错误统计 | telemetry unreported 不失败 |

**Read-only Context**

| 路径 | 读取目的 |
|------|----------|
| codex-cli JSONL 稳定 event examples in tests | 确认支持的 item.completed shape |
| schema v1-v3 migration tests | 保持旧库兼容 |

**Files**

| 操作 | 文件 | 说明 |
|------|------|------|
| Create | tools/spec_eval/service/executors/telemetry.py | JSONL aggregate parser |
| Modify | executor contract、codex_cli、models、store、repository | 传递和持久化计数 |
| Modify | serializers、metrics、ui/app.js | 暴露和展示计数 |
| Modify | README、SEMANTIC_SERVICE | 运维说明 |
| Test | executor、service、governance、HTTP、rolling reports tests | telemetry 和 migration 回归 |

**禁止修改文件**

| 文件或路径 | 原因 |
|------------|------|
| raw executor event archives | 不扩大敏感数据持久化 |
| BUILD.gn、bundle.json | 无构建和依赖变化 |

**Spec Context**

AC-1.4 要求已知事件提供聚合计数且未知形态不失败；AC-1.5 要求 schema v1-v3 无损升级到 v4。

**Design Context**

ADR-4 只保存聚合整数；STATE-2 和 STATE-3 分别归 executor invocation 与 Job repository；INV-2 和 INV-3 约束隐私与兼容性。

**Required Rules**

| Rule ID | Must 或 Must Not |
|---------|------------------|
| OH-ARCH-PRIVACY | 不得返回或持久化原始命令和路径 |
| OH-ARCH-DATA-MIGRATION | 必须支持 v1-v3 additive migration |

**Steps**

- [x] 写已知和未知 JSONL telemetry 测试
- [x] 实现 aggregate-only accumulator 并接入 ExecutionResult
- [x] 新增 schema v4 列和 v1-v3 migration
- [x] 接入 Job detail、metrics 和 UI
- [x] 更新文档并运行全量回归和 JS syntax check

**Reference Pattern**

| 参考实现 | 复用约定 | 偏差及理由 |
|----------|----------|------------|
| sqlite_store.py:90 | 缺列检测、ALTER TABLE、版本推进 | v4 新增五个非负列 |
| usage.py accumulator pattern | invocation 内聚合并在 ExecutionResult snapshot | telemetry 不解析 token usage 字段 |

**Anti-Fake Completion**

| Check | Required Evidence |
|-------|-------------------|
| AC closed | 已知 JSONL、未知 JSONL、repository 累计、HTTP、metrics、v3 migration 均有自动测试 |
| Scope respected | git show e630d949 不包含原始事件归档和外部依赖修改 |
| State lifecycle complete | STATE-2 invocation 后 snapshot，STATE-3 事务累计并由 governance 清理 |
| Interface contract matched | ExecutionResult、JobStatistics、serializer 和 metrics 字段名称一致 |
| Relevant verification | 503 项回归、node --check 和 schema migration tests |

**Verification**

| 证据类型 | 命令或路径 | Expected Result | Actual Result |
|----------|------------|-----------------|---------------|
| 测试 | PYTHONPATH=tools python3 -m unittest discover -s tools/spec_eval/tests -p test_*.py | telemetry、HTTP、metrics 和 migration 测试通过 | 2026-08-16 fresh run：Ran 503 tests in 105.323s，OK，skipped=1，PASS |
| JS 语法 | node --check tools/spec_eval/service/ui/app.js | 无 syntax error | exit code 0，无输出，PASS |
| 规格校验 | python3 tools/validate_specs.py --quiet | 0 errors | 0 errors、39 warnings，PASS |

**Handoff Summary**

| 项 | 内容 |
|----|------|
| 任务描述 | 聚合非敏感 executor telemetry，持久化 schema v4 并展示 |
| 允许修改 | executors、store、HTTP、metrics、UI、文档和对应测试 |
| 允许新建 | telemetry.py |
| 只读参考 | JSONL fixtures、schema migration tests |
| Spec 摘要 | AC-1.4、AC-1.5 和 R-5、R-6 |
| Design 摘要 | ADR-4、STATE-2、STATE-3、INV-2、INV-3 |
| 执行步骤 | 测试、accumulator、migration、observability、回归 |
| 验证命令 | 全量 unittest、node --check、validate_specs，期望 PASS |
| 完成规则 | telemetry unavailable 不失败，输出不含原始路径或命令 |

**Review Handoff**

| Reviewer | Input |
|----------|-------|
| Spec Compliance | AC-1.4、AC-1.5 到 telemetry 和 migration tests |
| Code Quality | privacy、schema additive migration 和字段一致性 |
| Verification | 503 项回归、JS syntax、validate_specs |

## 代码范围映射

| Task ID | 计划文件或符号 | 实际文件或符号 | 操作 | Commit | Spec Compliance | Code Quality | Verification | 偏差 |
|---------|----------------|----------------|------|--------|-----------------|--------------|--------------|------|
| TASK-1 | evaluator Skill、staged_run_support、contract tests | staged_run_support.py:95、827、854；test_next_007_skill.py:968 | Modify | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | evidence/reviews/code-quality.md | evidence/reviews/verification.md | 无 |
| TASK-2 | observation quality、semantic retry、executor prompt | observation_quality.py:39；semantic_stage.py:181、684；result_payload.py:168 | Add、Modify | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | evidence/reviews/code-quality.md | evidence/reviews/verification.md | 无 |
| TASK-3 | telemetry、schema v4、API、metrics、UI、docs | telemetry.py:31；sqlite_store.py:30；serializers.py:83；app.js:257 | Add、Modify | e630d94953fa4a1d34cb4f3914fa5bea33f570f3 | evidence/reviews/spec-compliance.md | evidence/reviews/code-quality.md | evidence/reviews/verification.md | 无 |

## 实现偏差和开放问题

| Task ID | 类型 | 问题或偏差 | 处理状态 | 回退能力或 Owner |
|---------|------|------------|----------|-------------------|
| TASK-1 | scope | 无实现偏差 | Resolved | ohos-plan |
| TASK-2 | design | 采用组合信号而非 Issue 建议的单一 60% 硬阈值 | Resolved，符合推荐方案的误报控制目标 | ohos-design |
| TASK-3 | compatibility | 未知 JSONL 不作为失败条件 | Resolved，明确记录 telemetry unavailable | arkui_architecture |

## Plan 自审清单

- [x] 每个 AC 至少映射到一个 Task
- [x] 每个 Task 文件范围明确
- [x] 每个 Task 有前置依赖、非目标、完成判据和停止条件
- [x] 每个 Task 有验证命令和 fresh Actual Result
- [x] Produces 与 Consumes 可双向核对
- [x] STATE 和 INV 已映射到 Task 和验证
- [x] 受影响文件全量清单覆盖实际 31 个实现文件
- [x] 没有未解决占位符或生成文件手改
- [x] AC→Task→Code→Commit→Review 已回填
- [x] Anti-Fake Completion 证据完整
