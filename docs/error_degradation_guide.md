# 错误降级机制完整指南

## 目录

1. [概述](#概述)
2. [降级策略层次](#降级策略层次)
3. [错误分类体系](#错误分类体系)
4. [降级决策流程](#降级决策流程)
5. [实现位置和机制](#实现位置和机制)
6. [添加新的降级错误](#添加新的降级错误)
7. [案例分析](#案例分析)
8. [故障排查](#故障排查)

---

## 概述

### 什么是错误降级？

错误降级（Error Degradation）是一种容错机制，允许某些**有界的数据质量问题**不阻断评估报告的发布，而是：
- 扣除相应的置信度分数
- 在报告中记录缺陷
- 保持报告结构完整可消费

### 核心原则

1. **结构完整性优先**：只有不影响报告结构完整性的错误才能降级
2. **可见性**：降级的错误必须在置信度报告中可见，扣分明确
3. **有界性**：降级错误必须是有界的（不会无限累积或扩散）
4. **一致性**：同类错误在不同阶段应有一致的降级策略

### 适用场景

✅ **应该降级**：
- 模型难以自动修复的数据质量问题
- 不影响报告核心结构的缺陷
- 有明确扣分标准的问题
- 人工修正成本高于发布降级报告的价值

❌ **不应该降级**：
- 结构性损坏（schema 违反、必需字段缺失）
- 逻辑矛盾（如 PASS 却有 Critical Finding）
- 可自动修复的问题
- 会导致下游消费失败的错误

---

## 降级策略层次

评估系统有**三层降级防护**，从内到外依次为：

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: Kernel (核心验证层)                        │
│ - 定义错误分类和置信层级                             │
│ - POST_CORRECTION_WARNING_CODES                     │
│ - 位置: tools/spec_eval/kernel/errors.py           │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: Judgment Flow (判决流程层)                 │
│ - 协调 Correction 和 degraded publish               │
│ - 使用 kernel 的分类决策是否降级                     │
│ - 位置: tools/spec_eval/kernel/judgment_flow.py    │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: Skill Scripts (技能脚本层)                 │
│ - 针对特定阶段的额外降级策略                         │
│ - split_*_warnings() 函数族                         │
│ - 位置: skills/*/scripts/*_warning_policy.py        │
└─────────────────────────────────────────────────────┘
```

### Layer 1: Kernel 核心层

**职责**：定义错误的本质分类

**关键常量**：
- `NON_BLOCKING_WARNING_CODES`: 从不阻断的警告
- `POST_CORRECTION_WARNING_CODES`: Correction 后可降级的错误

**影响范围**：所有使用 kernel 验证的组件

### Layer 2: Judgment Flow 判决层

**职责**：协调 Correction 和 degraded publish

**关键函数**：
- `is_non_blocking_warning()`: 检查是否为非阻断警告
- `is_post_correction_warning()`: 检查 Correction 后是否可降级
- `degraded_publish()`: 决定是否允许降级发布

**决策逻辑**：
```python
if correction_failed:
    residual_errors = validate(corrected_document)
    blocking = [e for e in residual_errors 
                if not is_post_correction_warning(e)]
    if not blocking:
        return publish_with_degraded_confidence()
    else:
        return CORRECTION_INVALID_TERMINAL
```

### Layer 3: Skill Scripts 技能层

**职责**：针对特定阶段的额外降级策略

**典型场景**：
- Schema 最小项约束 vs 语义空缺
- 特定阶段的字符串匹配降级
- 服务端生成的警告信息

**实现模式**：
```python
def split_xxx_warnings(errors):
    blocking = []
    warnings = []
    for error in errors:
        if matches_warning_pattern(error):
            warnings.append(error)
        else:
            blocking.append(error)
    return blocking, warnings
```

---

## 错误分类体系

### 置信层级（Confidence Layer）

| 层级 | 扣分 | 语义 | 示例 |
|---|---|---|---|
| `LAYER_HARD` | 100 | 结构性损坏，报告不可用 | Schema 违反、必需字段缺失 |
| `LAYER_MAJOR` | 20 | 严重质量问题，影响可信度 | 证据类型缺失、Finding 无证据 |
| `LAYER_MINOR` | 5 | 轻微质量问题，有限影响 | 证据引用不在 allowlist、unmapped claim |

### 错误类型（Error Category）

| 类型 | 含义 | 是否触发 Correction |
|---|---|---|
| `MODEL_CORRECTION` | 模型可尝试修复 | ✅ 是 |
| `SERVICE_CORRECTION` | 服务端可自动修复 | ❌ 否（直接修复） |
| `OBSERVATION` | 观察阶段的数据问题 | ✅ 是 |
| `VALIDATION` | 纯验证错误，无法修复 | ❌ 否 |

### 当前降级错误清单

#### Kernel 层（POST_CORRECTION_WARNING_CODES）

| 错误码 | 层级 | 扣分 | 含义 | 添加于 |
|---|---|---|---|---|
| `MAPPING_CLAIM_UNMAPPED` | MINOR | -5 | Claim ID 未映射到 Criterion | 原有 |
| `CRITERION_EVIDENCE_UNKNOWN` | MINOR | -5 | 证据 ID 不在 allowlist | PR #192 |
| `EVIDENCE_TYPE_MISSING` | MAJOR | -20 | 证据类型不符合要求 | PR #192 |

#### Skill 层（aggregation_warning_policy.py）

| 错误模式 | 层级 | 扣分 | 含义 | 添加于 |
|---|---|---|---|---|
| Ownership warnings | MAJOR | -20 | defect_ownership 交叉不一致 | PR #186 |
| Mapping warnings | MINOR | -5 | Correction 后仍有 unmapped claim | PR #186 |
| Finding evidence warnings | MAJOR | -20 | Finding 证据被服务移除 | PR #189 |
| Contradiction basis warnings | MINOR | -5 | 矛盾根因覆盖不完整 | PR #186 |

#### Skill 层（final candidate）

| 错误模式 | 层级 | 扣分 | 含义 | 添加于 |
|---|---|---|---|---|
| `evidence must include one of` | MAJOR | -20 | Final 阶段证据类型缺失 | PR #191 |

---

## 降级决策流程

### 完整生命周期

```
┌─────────────────┐
│ 1. 初始验证      │
│ validate()      │
└────────┬────────┘
         │
         ├─ 无错误 ──────────────────────→ PUBLISHED ✅
         │
         ├─ 非阻断警告 ─────────────────→ PUBLISHED (降级) ⚠️
         │
         └─ 阻断错误
              │
              ↓
┌──────────────────────────────────────┐
│ 2. 判断是否可 Correction              │
│ - MODEL_CORRECTION: 可尝试修复        │
│ - OBSERVATION: 可尝试修复              │
│ - 其他: 直接 TERMINAL                 │
└────────┬─────────────────────────────┘
         │
         ├─ 不可修复 ──────────────────→ VALIDATION_FAILED ❌
         │
         └─ 可修复
              │
              ↓
┌──────────────────────────────────────┐
│ 3. 执行 Model Correction              │
│ - 最多 1 次修复机会                    │
│ - 受 allowed_edits 约束                │
└────────┬─────────────────────────────┘
         │
         ├─ Correction 成功 ────────────→ 重新验证 → PUBLISHED ✅
         │
         └─ Correction 后仍有错误
              │
              ↓
┌──────────────────────────────────────┐
│ 4. Post-Correction 判决               │
│ degraded_publish()                   │
└────────┬─────────────────────────────┘
         │
         ├─ 剩余错误 ∈ POST_CORRECTION_WARNING_CODES
         │     ↓
         │   PUBLISHED (降级) ⚠️
         │
         └─ 剩余错误包含 blocking
               ↓
         CORRECTION_INVALID_TERMINAL ❌
```

### 关键决策点

#### 决策点 1: 初始验证后

```python
errors = validate(document)
non_blocking = [e for e in errors if is_non_blocking_warning(e)]

if len(errors) == len(non_blocking):
    # 全是非阻断警告 → 直接发布（降级）
    return publish_with_warnings(non_blocking)
```

#### 决策点 2: 判断是否触发 Correction

```python
correctable = [e for e in errors 
               if e.category in [MODEL_CORRECTION, OBSERVATION]]

if not correctable:
    # 没有可修复的错误 → 直接失败
    return VALIDATION_FAILED
```

#### 决策点 3: Correction 后判决

```python
residual = validate(corrected_document)
post_corr_warnings = [e for e in residual 
                      if is_post_correction_warning(e)]
blocking = [e for e in residual 
            if e not in post_corr_warnings]

if not blocking:
    # 只剩 post-correction warnings → 降级发布
    return publish_with_degraded_confidence(post_corr_warnings)
else:
    # 仍有阻断错误 → Correction 失败
    return CORRECTION_INVALID_TERMINAL
```

---

## 实现位置和机制

### Kernel 层实现

**文件**: `tools/spec_eval/kernel/errors.py`

```python
# 从不阻断的警告（初始验证即可降级）
NON_BLOCKING_WARNING_CODES: frozenset[str] = frozenset([
    # 示例：轻微的格式问题
])

# Correction 后可降级的错误
POST_CORRECTION_WARNING_CODES: frozenset[str] = frozenset([
    "MAPPING_CLAIM_UNMAPPED",        # PR 原有
    "CRITERION_EVIDENCE_UNKNOWN",     # PR #192
    "EVIDENCE_TYPE_MISSING",          # PR #192
])

def is_non_blocking_warning(error: TypedError) -> bool:
    """初始验证阶段的非阻断警告"""
    return error.code in NON_BLOCKING_WARNING_CODES

def is_post_correction_warning(error: TypedError) -> bool:
    """Correction 后可降级的警告"""
    return error.code in POST_CORRECTION_WARNING_CODES
```

### Judgment Flow 层实现

**文件**: `tools/spec_eval/kernel/judgment_flow.py`

```python
def degraded_publish(
    state: dict,
    stage_name: str,
    residual: list[TypedError],
    ...
) -> bool:
    """判断是否允许降级发布"""
    # 过滤掉可降级的警告
    filtered = [
        error for error in residual
        if not is_post_correction_warning(error)
        and not is_model_correction_error(error)
    ]
    
    if has_hard_errors(filtered) or any(is_fatal_error(e) for e in filtered):
        return False  # 仍有阻断错误
    
    # 只剩可降级警告 → 允许发布
    record_degraded_confidence(residual)
    return True
```

### Skill 层实现（aggregation_warning_policy.py）

**文件**: `skills/ohos-design-arkui-spec-evaluator/scripts/aggregation_warning_policy.py`

```python
# 定义降级标记
OWNERSHIP_WARNING_MARKERS = (
    "one defect may produce at most one Critical Finding",
    "a Critical Finding must belong to the primary Criterion",
    "must own one mapped Finding",
)

def split_aggregation_warnings(errors: list[str]) -> tuple[list[str], list[str]]:
    """分离 aggregation 阶段的 blocking 和 warning"""
    blocking = []
    warnings = []
    for error in errors:
        if any(marker in error for marker in OWNERSHIP_WARNING_MARKERS):
            warnings.append(error)
        else:
            blocking.append(error)
    return blocking, warnings

def record_ownership_warning(run_dir: Path, warnings: list[str]) -> None:
    """记录 ownership 质量警告并扣除置信度"""
    if not warnings:
        return
    _record_confidence_warning(
        run_dir, warnings,
        code="OWNERSHIP_CRITICALITY",
        layer="MAJOR",
        deduction=20,
        message="defect ownership contains non-structural inconsistencies",
        warning_path="aggregation.defect_ownership",
    )
```

### Skill 层实现（assemble_semantic_result.py）

**文件**: `skills/ohos-design-arkui-spec-evaluator/scripts/assemble_semantic_result.py`

```python
from aggregation_warning_policy import (
    split_aggregation_warnings,
    split_final_candidate_warnings,
    record_aggregation_warnings,
)

def main(args):
    # Aggregation 阶段
    aggregation_errors = validate_stage(run_dir, "aggregation")
    blocking, warnings = split_aggregation_warnings(aggregation_errors)
    
    if blocking:
        return 1  # 阻断错误
    
    if warnings:
        record_aggregation_warnings(run_dir, warnings)
    
    # Final candidate 阶段
    final_errors = validate_final_candidate(candidate, aggregation)
    blocking, warnings = split_final_candidate_warnings(final_errors)
    
    if blocking:
        return 1  # 阻断错误
    
    if warnings:
        record_evidence_type_warning(run_dir, warnings)
    
    return 0  # 成功（可能带警告）
```

---

## 添加新的降级错误

### 评估清单

在添加新的降级错误前，确认以下问题：

#### ✅ 必须满足的条件

- [ ] 错误是**有界的**（不会无限累积或扩散）
- [ ] 错误**不影响报告结构完整性**（schema 仍然有效）
- [ ] 错误有**明确的置信度扣分标准**
- [ ] 错误**模型难以自动修复**（或修复成本高于降级）
- [ ] 降级后报告**仍可被下游消费**

#### ❌ 禁止降级的情况

- [ ] Schema 违反（必需字段缺失、类型错误）
- [ ] 逻辑矛盾（如结论 PASS 但有 Critical Finding）
- [ ] 会导致下游消费崩溃的错误
- [ ] 可通过简单规则自动修复的问题

### 实现步骤

#### 步骤 1: 确定降级层次

根据错误特征选择合适的层次：

| 选择 Kernel 层 | 选择 Skill 层 |
|---|---|
| 错误由 kernel 验证器产生 | 错误在 skill 脚本中产生 |
| 错误有明确的错误码 | 错误是字符串匹配模式 |
| 错误在多个阶段都可能出现 | 错误只在特定阶段出现 |
| 希望全局一致的降级策略 | 需要阶段特定的降级逻辑 |

#### 步骤 2: Kernel 层添加（如果适用）

编辑 `tools/spec_eval/kernel/errors.py`：

```python
POST_CORRECTION_WARNING_CODES: frozenset[str] = frozenset([
    "MAPPING_CLAIM_UNMAPPED",
    "CRITERION_EVIDENCE_UNKNOWN",
    "EVIDENCE_TYPE_MISSING",
    "YOUR_NEW_ERROR_CODE",  # 添加新错误码，附带注释说明
])
```

**测试要求**：
- 编写单元测试验证 `is_post_correction_warning()` 返回 `True`
- 模拟 judgment flow 验证 `degraded_publish()` 允许发布

#### 步骤 3: Skill 层添加（如果适用）

编辑 `aggregation_warning_policy.py`：

```python
# 1. 定义错误标记
YOUR_WARNING_MARKER = "specific error string pattern"
YOUR_WARNING_CODE = "YOUR_WARNING_CODE"
YOUR_WARNING_DEDUCTION = 20  # MAJOR 或 5 # MINOR

# 2. 在 split_*_warnings 中添加匹配逻辑
def split_aggregation_warnings(errors: list[str]):
    for error in errors:
        if YOUR_WARNING_MARKER in error:
            warnings.append(error)
        # ...

# 3. 添加 record 函数
def record_your_warning(run_dir: Path, warnings: list[str]):
    _record_confidence_warning(
        run_dir, warnings,
        code=YOUR_WARNING_CODE,
        layer="MAJOR",  # 或 "MINOR"
        deduction=YOUR_WARNING_DEDUCTION,
        message="简短描述此警告的含义",
        warning_path="aggregation.相关字段路径",
    )

# 4. 在 record_aggregation_warnings 中调用
def record_aggregation_warnings(run_dir, warnings):
    # ...
    record_your_warning(run_dir, [w for w in warnings if YOUR_MARKER in w])
```

编辑 `assemble_semantic_result.py` 或 `validate_staged_run.py`：

```python
from aggregation_warning_policy import record_your_warning

# 在适当的验证点调用 split 和 record
blocking, warnings = split_xxx_warnings(errors)
if warnings:
    record_your_warning(run_dir, warnings)
```

**测试要求**：
- 测试 `split_*_warnings()` 正确分离 blocking 和 warnings
- 测试 `record_*_warning()` 正确写入 confidence-result.json
- 测试扣分是幂等的（多次调用只扣一次）
- 端到端测试：assemble/validate 通过，confidence 正确扣分

#### 步骤 4: 文档和测试

1. **更新本文档**：在"当前降级错误清单"章节添加新错误
2. **添加回归测试**：确保修复不破坏现有行为
3. **添加案例**：在"案例分析"章节添加实际触发场景

#### 步骤 5: 代码审查重点

- [ ] 降级逻辑不会导致误降（正确识别 blocking vs warning）
- [ ] 置信度扣分合理（HARD=100, MAJOR=20, MINOR=5）
- [ ] 扣分是幂等的（同一错误多次出现只扣一次）
- [ ] 错误信息清晰，便于用户理解缺口
- [ ] 测试覆盖充分（包括边界情况）

---

## 案例分析

### 案例 1: Finding 证据缺失 (PR #189)

#### 问题描述

Criterion 判为 MISSING，有 1 个 Finding，但 Finding 的 `evidence_ids` 为空。

**验证失败点**：
- Schema: `findings[].evidence_ids` 要求 `minItems: 1`
- Protocol: Finding 必须有至少一条证据支撑

**阻断位置**：
- Aggregation 验证通过（aggregation.json 中 Finding 有 evidence_ids）
- Assemble 阶段 `build_final_candidate()` 构建 semantic-result.json 时，某些 Finding 的 evidence_ids 被过滤为空
- `validate_final_candidate()` 报 schema 错误

#### 为什么难以自动修复？

模型无法在不进行新的语义评估的情况下伪造有效证据。

#### 解决方案

**Skill 层防护** + **占位修复**：

1. 在 `build_final_candidate()` 中检测空 evidence_ids
2. 插入一条明确标注的占位证据：
   ```python
   {
       "evidence_id": "EV-PLACEHOLDER-NO-REPRO-EVIDENCE",
       "evidence_type": "spec_location",
       "description": "No reproducible evidence; gap recorded for manual review"
   }
   ```
3. 记录 confidence 警告（-20 MAJOR）

**关键点**：
- 占位证据**不伪造内容**，明确标注为"记录缺口"
- 满足 schema `minItems: 1` 约束
- 不影响报告结构和下游消费

#### 相关文件

- `skills/.../staged_run_support.py`: `repair_missing_finding_evidence()`
- `skills/.../aggregation_warning_policy.py`: `record_finding_evidence_warning()`

---

### 案例 2: 证据类型缺失 (PR #191 + #192)

#### 问题描述

Criterion `CORRECTNESS-SDK-CONTRACT` 的 `required_evidence_types` 是 `[sdk_declaration, source_citation]`，但 Finding 的证据都是 `design_location` / `spec_location` 类型。

**验证失败点**：
- Final candidate 验证：`evidence must include one of ['sdk_declaration', 'source_citation']`

**阻断位置**：
1. **Aggregation 阶段**（kernel）：`EVIDENCE_TYPE_MISSING` 触发 Correction
2. Correction 无法修复（模型拒绝伪造 sdk_declaration 类型）
3. **Post-correction 判决**：因不在 `POST_CORRECTION_WARNING_CODES`，被视为 blocking
4. 设置 `CORRECTION_INVALID_TERMINAL`

#### 为什么难以自动修复？

模型正确地拒绝伪造 `sdk_declaration` 类型的证据，因为：
- 没有实际的 SDK 声明来源
- 伪造类型会误导用户"已验证 SDK 契约"

#### 解决方案

**双层防护**：

**PR #192 (Kernel 层)**：
- 将 `EVIDENCE_TYPE_MISSING` 加入 `POST_CORRECTION_WARNING_CODES`
- Correction 后允许降级发布（-20 MAJOR）

**PR #191 (Skill 层)**：
- 在 `assemble_semantic_result.py` 添加 `split_final_candidate_warnings()`
- Final candidate 验证时降级此错误

**关键点**：
- **不伪造证据类型**（与案例 1 不同）
- 纯降级为 warning，诚实保留"证据类型不达标"的缺口
- 两层防护确保无论在哪个阶段检测到都能降级

#### 相关文件

- `tools/spec_eval/kernel/errors.py`: `POST_CORRECTION_WARNING_CODES`
- `skills/.../aggregation_warning_policy.py`: `split_final_candidate_warnings()`
- `skills/.../assemble_semantic_result.py`: 调用 split 和 record

---

### 案例 3: 证据引用不在 Allowlist (PR #192)

#### 问题描述

Criterion 引用了 `EV-xxx` 证据 ID，但该 ID 不在该 Criterion 的 `evidence_allowlist` 中。

**验证失败点**：
- Aggregation 验证：`CRITERION_EVIDENCE_UNKNOWN`

**阻断位置**：
1. Aggregation 验证发现 `CRITERION_EVIDENCE_UNKNOWN`（MINOR）
2. 触发 Correction
3. Correction 无法修复（allowlist 是冻结的）
4. Post-correction 判决：不在 `POST_CORRECTION_WARNING_CODES` → TERMINAL

#### 为什么难以自动修复？

Evidence allowlist 是从 frozen criterion catalog 加载的，模型：
- 无权修改 allowlist
- 无法在不重新评估的情况下找到替代证据

#### 解决方案

**Kernel 层防护**（PR #192）：
- 将 `CRITERION_EVIDENCE_UNKNOWN` 加入 `POST_CORRECTION_WARNING_CODES`
- Correction 后允许降级发布（-5 MINOR）

**关键点**：
- 这是**有界的数据质量问题**，不是结构损坏
- 报告仍可消费，但标注该 Criterion 的证据引用有缺陷
- 置信度扣分较轻（MINOR -5），因为不影响核心结论

#### 相关文件

- `tools/spec_eval/kernel/errors.py`: `POST_CORRECTION_WARNING_CODES`
- `tools/spec_eval/kernel/judgment_flow.py`: `degraded_publish()`

---

## 故障排查

### 问题 1: Job 进入 CORRECTION_INVALID_TERMINAL

#### 症状

- Run state: `"aggregation:final": "CORRECTION_INVALID_TERMINAL"`
- Logs 中有 Correction 执行记录
- Correction 后仍有错误

#### 诊断步骤

1. **查看 Correction 后的残留错误**：
   ```bash
   cat .evaluator/.../runs/run-N/logs/correct-aggregation-*.executor-result.json | jq '.errors'
   ```

2. **检查错误是否在降级列表中**：
   ```python
   from spec_eval.kernel.errors import is_post_correction_warning, TypedError
   
   for error in residual_errors:
       typed = TypedError(error['code'], error['layer'], ...)
       print(f"{error['code']}: {is_post_correction_warning(typed)}")
   ```

3. **常见原因**：
   - 错误码**不在** `POST_CORRECTION_WARNING_CODES` 中
   - 错误层级是 `LAYER_HARD`（硬阻断）
   - Correction 引入了新的结构性错误

#### 解决方案

**如果错误应该降级**：
- 评估是否满足降级条件（见"评估清单"）
- 添加到 `POST_CORRECTION_WARNING_CODES`（Kernel 层）
- 或在 skill 层添加 `split_*_warnings()` 逻辑

**如果错误不应该降级**：
- 检查为什么 Correction 无法修复
- 可能需要改进 Correction prompt
- 或标记为需要人工介入

---

### 问题 2: Confidence 扣分不正确

#### 症状

- Job 成功发布
- `confidence-result.json` 中扣分与预期不符
  - 扣分过多
  - 扣分过少
  - 同一错误重复扣分

#### 诊断步骤

1. **查看所有 violation 条目**：
   ```bash
   cat confidence-result.json | jq '{
     hard: .hard_errors,
     major: .major_violations,
     minor: .minor_violations,
     total: .deduction_total
   }'
   ```

2. **检查是否有重复**：
   ```bash
   cat confidence-result.json | jq '[
     .hard_errors[].code,
     .major_violations[].code,
     .minor_violations[].code
   ] | group_by(.) | map({code: .[0], count: length}) | .[]'
   ```

3. **常见原因**：
   - `record_*_warning()` 被多次调用
   - 缺少幂等性检查（`if any(item.get("code") == code for item in target)`）
   - 不同阶段重复记录同一错误

#### 解决方案

**确保幂等性**：
```python
def record_your_warning(run_dir, warnings):
    if not warnings:
        return  # 无警告，跳过
    
    confidence = load_confidence_result(run_dir)
    target = confidence.get("major_violations", [])
    
    # 检查是否已记录
    if any(item.get("code") == YOUR_CODE for item in target):
        return  # 已存在，跳过
    
    # 添加新记录
    target.append({"code": YOUR_CODE, "deduction": 20, ...})
```

---

## 最佳实践

### 1. 优先 Kernel 层降级

**优势**：
- 一次定义，到处生效
- 与 judgment flow 深度集成
- 易于维护和理解

### 2. Skill 层作为补充

**注意事项**：
- 保持与 Kernel 层的一致性
- 避免重复记录同一错误
- 确保幂等性

### 3. 置信度扣分指导

| 错误影响 | 扣分层级 | 典型场景 |
|---|---|---|
| 结构性损坏 | HARD (100) | Schema 违反，不可降级 |
| 严重质量问题 | MAJOR (20) | 证据缺失、类型错误、ownership 不一致 |
| 轻微质量问题 | MINOR (5) | 引用不在 allowlist、unmapped claim |

---

## 参考资料

### 相关 PR

- **PR #184**: 修复 observation 覆盖码死区
- **PR #186**: 聚合降级（Correction 返回文档后降级）
- **PR #187**: Executor 失败时降级
- **PR #188**: 修复 retry CORRECTION_PENDING 死锁
- **PR #189**: Finding 证据缺口违反 schema minItems
- **PR #191**: Skill 层 EVIDENCE_TYPE_MISSING 降级
- **PR #192**: Kernel 层 CRITERION_EVIDENCE_UNKNOWN 和 EVIDENCE_TYPE_MISSING 降级

### 关键文件

**Kernel 层**：
- `tools/spec_eval/kernel/errors.py` - 错误分类和降级列表
- `tools/spec_eval/kernel/judgment_flow.py` - Correction 和 degraded publish 逻辑

**Skill 层**：
- `skills/ohos-design-arkui-spec-evaluator/scripts/aggregation_warning_policy.py` - 降级策略和记录函数
- `skills/ohos-design-arkui-spec-evaluator/scripts/assemble_semantic_result.py` - Assemble 阶段降级
- `skills/ohos-design-arkui-spec-evaluator/scripts/validate_staged_run.py` - Validate 阶段降级

**测试**：
- `tools/spec_eval/tests/test_assemble_semantic_result.py` - 降级逻辑测试

---

**文档版本**: v1.0  
**最后更新**: 2026-08-27  
**维护者**: ArkUI Spec Evaluator Team
