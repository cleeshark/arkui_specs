# 特性规格

> Func-07-02-04-Feat-05 ConfigureStateMgmt 特性开关：固化 `ConfigureStateMgmt`（`common/state_mgmt_configure.ts:20-70`，单例）的 `needsV2Observe()`(67-69) V2 观察检测、`usingV2ObservedTrack`(43-46)/`usingPUObservedTrack`(56-59) 特性跟踪、V1/V2 范式检测行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ConfigureStateMgmt 特性开关 |
| 特性编号 | Func-07-02-04-Feat-05 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | V1/V2 范式检测 API 7 起；V2 观察（needsV2Observe）API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 低 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Draft |
| ConfigureStateMgmt | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_configure.ts` | — |
| 状态管理原理介绍 | `docs/zh-cn/application-dev/ui/state-management/arkts-state-management-introduce.md` | — |

---

## 用户故事

### US-1: needsV2Observe V2 观察检测

**作为** 框架维护者,
**我想要** 通过 `ConfigureStateMgmt.needsV2Observe()` 检测应用是否使用了 V2 观察,
**以便** 框架在 V1/V2 共存场景正确选择运行时路径。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 任何 `usingV2ObservedTrack`(43-46) 调用发生（`@ObservedV2`/`@Trace`/`@Monitor` 应用）THEN `v2ObservedTrackInUse_`(26) 置 true | 正常 |
| AC-1.2 | WHEN `needsV2Observe()`(67-69) 被调用 THEN 返回 `v2ObservedTrackInUse_` 标志 | 正常 |
| AC-1.3 | WHEN 应用未使用任何 V2 装饰器 THEN `needsV2Observe()` 返回 false | 边界 |

### US-2: PU 观察跟踪

**作为** 框架维护者,
**我想要** 通过 `ConfigureStateMgmt.usingPUObservedTrack` 跟踪 PU 观察使用,
**以便** 框架感知 @Track 等 PU 特性的应用情况。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `usingPUObservedTrack`(56-59) 调用（PU Observed/@Track 应用）THEN `puObservedTrackInUse_`(27) 置 true | 正常 |
| AC-2.2 | WHEN `usingPUObservedTrack`(56-59) 调用（@Track 等应用）THEN `puObservedTrackInUse_`(27) 置 true | 正常 |
| AC-2.3 | WHEN `ConfigureStateMgmt` 是单例（`instance__`(24) 懒加载）THEN 全局唯一 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 usingV2ObservedTrack |
| AC-1.2 | US-1 | R-1 | 单元测试 needsV2Observe |
| AC-1.3 | US-1 | R-1 | 单元测试 未使用 V2 |
| AC-2.1 | US-2 | R-2 | 单元测试 usingPUObservedTrack |
| AC-2.2 | US-2 | R-2 | 代码审查 单例 |
| AC-2.3 | US-2 | R-2 | 代码审查 PU/FU 协调 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `usingV2ObservedTrack`(43-46) 调用 / `needsV2Observe()`(67-69) 查询 | 任何 `@ObservedV2`/`@Trace`/`@Monitor` 应用时框架调 `usingV2ObservedTrack` 置 `v2ObservedTrackInUse_`(26) 为 true；`needsV2Observe()` 返回该标志；未使用 V2 装饰器返回 false | 单例（懒加载 `instance__`(24)） | AC-1.1~AC-1.3 |
| R-2 | 行为 | `usingPUObservedTrack`(56-59) 调用 | PU Observed/@Track 应用时置 `puObservedTrackInUse_`(27) 为 true；API 9 起统一 PU（无 FU/FU 开关） | API 9+ 统一 PU | AC-2.1~AC-2.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `common_tests/` usingV2ObservedTrack |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` needsV2Observe |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` 未使用 V2 |
| VM-4 | AC-2.1 | 单元测试 | `common_tests/` usingPUObservedTrack |
| VM-5 | AC-2.2 | 代码审查 | `state_mgmt_configure.ts:24` 单例 |
| VM-6 | AC-2.3 | 代码审查 | 单例 instance__ |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `ConfigureStateMgmt` | `common/state_mgmt_configure.ts:20-70` | 特性开关单例 |
| `v2ObservedTrackInUse_` | `common/state_mgmt_configure.ts:26` | V2 观察标志 |
| `puObservedTrackInUse_` | `common/state_mgmt_configure.ts:27` | PU 观察标志 |
| `usingV2ObservedTrack` | `common/state_mgmt_configure.ts:43-46` | 标记 V2 观察使用 |
| `usingPUObservedTrack` | `common/state_mgmt_configure.ts:56-59` | 标记 PU 观察使用 |
| `needsV2Observe()` | `common/state_mgmt_configure.ts:67-69` | 查询是否需要 V2 观察 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | V1/V2 范式检测引入；FU 为 API 9 前历史路径 | V1 范式检测 | 无需迁移 |
| API 9 | PU 统一：API 9 起统一为 PU，FU 废弃，无开关 | 统一渲染路径 | 无需迁移 |
| API 12 | needsV2Observe V2 观察检测引入 | V1/V2 共存路径选择 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| V2 专属 | ConfigureStateMgmt 的 needsV2Observe 归 V2（07-02-04）；ConfigureStateMgmt 负责 V1/V2 范式检测（非 PU/FU 路径选择）；API 9 起统一 PU（无开关） |
| 单例 | `ConfigureStateMgmt` 通过 `instance__` 懒加载单例 |
| V2 观察触发 | 任何 @ObservedV2/@Trace/@Monitor 应用都会触发 usingV2ObservedTrack |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file 信息
- [x] 变更范围 Delta 明确标注为已有实现补录

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_configure.ts:20-70` | `ConfigureStateMgmt` 特性开关单例 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_configure.ts:43-46/56-59/67-69` | `usingV2ObservedTrack`/`usingPUObservedTrack`/`needsV2Observe` |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | ConfigureStateMgmt 行为回归测试 |
