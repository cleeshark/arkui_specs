# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolEffect 子类与参数 |
| 特性编号 | Func-05-09-07-Feat-06 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`07-symbol-glyph/design.md`
- 源码定位：`symbolglyph.d.ts:282–525`（7 个 effect 子类）、`constants.h:27`（SymbolEffectType 10 值）

## 用户故事

### US-1: 各 effect 子类构造
作为开发者，我希望使用 7 个 typed effect 子类表达不同动效语义。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new ScaleSymbolEffect(scope, direction)` THEN effectType=SCALE，按 scope/direction 派生 | 正常 |
| AC-1.2 | WHEN `new HierarchicalSymbolEffect(fillStyle)` THEN effectType=HIERARCHICAL，按 fillStyle 派生 | 正常 |
| AC-1.3 | WHEN `new AppearSymbolEffect(scope)` THEN effectType=APPEAR | 正常 |
| AC-1.4 | WHEN `new DisappearSymbolEffect(scope)` THEN effectType=DISAPPEAR | 正常 |
| AC-1.5 | WHEN `new BounceSymbolEffect(scope, direction)` THEN effectType=BOUNCE | 正常 |
| AC-1.6 | WHEN `new PulseSymbolEffect()` THEN effectType=PULSE | 正常 |
| AC-1.7 | WHEN `new ReplaceSymbolEffect(scope, replaceType)` THEN effectType=REPLACE，按 replaceType 派生 | 正常 |

### US-2: 参数可选性
作为开发者，我希望所有 effect 参数可选，缺省时按默认派生。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 构造 effect 不传参数 THEN 按默认 scope/fillStyle/direction 派生 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-06 | 单测 | symbolglyph.d.ts:302 |
| AC-1.2 | R-2 | TASK-06 | 单测 | symbolglyph.d.ts:347 |
| AC-1.3 | R-3 | TASK-06 | 单测 | symbolglyph.d.ts:380 |
| AC-1.4 | R-3 | TASK-06 | 单测 | symbolglyph.d.ts:413 |
| AC-1.5 | R-4 | TASK-06 | 单测 | symbolglyph.d.ts:446 |
| AC-1.6 | R-5 | TASK-06 | 单测 | symbolglyph.d.ts:524 |
| AC-1.7 | R-6 | TASK-06 | 单测 | symbolglyph.d.ts:491 |
| AC-2.1 | R-7 | TASK-06 | 单测 | — |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | ScaleSymbolEffect(scope?, direction?) | effectType=SCALE，派生 scope/direction | scope∈LAYER/WHOLE, direction∈DOWN/UP | AC-1.1 |
| R-2 | 行为 | HierarchicalSymbolEffect(fillStyle?) | effectType=HIERARCHICAL，派生 fillStyle | fillStyle∈CUMULATIVE/ITERATIVE | AC-1.2 |
| R-3 | 行为 | Appear/DisappearSymbolEffect(scope?) | effectType=APPEAR/DISAPPEAR | scope 同上 | AC-1.3,1.4 |
| R-4 | 行为 | BounceSymbolEffect(scope?, direction?) | effectType=BOUNCE | 同 R-1 参数 | AC-1.5 |
| R-5 | 行为 | PulseSymbolEffect() | effectType=PULSE | 无参数 | AC-1.6 |
| R-6 | 行为 | ReplaceSymbolEffect(scope?, replaceType?) | effectType=REPLACE，派生 replaceType | replaceType∈SEQUENTIAL/CROSS_FADE/SLASH_OVERLAY | AC-1.7 |
| R-7 | 边界 | 参数缺省 | 按默认派生 | — | AC-2.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-6 各子类 | 单测 | effectType 映射 |
| VM-2 | R-7 缺省 | 单测 | 默认派生 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class SymbolEffect` | Public | — | — | 无 | 基类 @since 12 | 全部 |
| `class ScaleSymbolEffect extends SymbolEffect` | Public | scope?, direction? | 实例 | 无 | 缩放 @since 12 | AC-1.1 |
| `class HierarchicalSymbolEffect` | Public | fillStyle? | 实例 | 无 | 层级 @since 12 | AC-1.2 |
| `class AppearSymbolEffect` | Public | scope? | 实例 | 无 | 出现 @since 12 | AC-1.3 |
| `class DisappearSymbolEffect` | Public | scope? | 实例 | 无 | 消失 @since 12 | AC-1.4 |
| `class BounceSymbolEffect` | Public | scope?, direction? | 实例 | 无 | 弹跳 @since 12 | AC-1.5 |
| `class PulseSymbolEffect` | Public | — | 实例 | 无 | 脉冲 @since 12 | AC-1.6 |
| `class ReplaceSymbolEffect` | Public | scope?, replaceType? | 实例 | 无 | 替换 @since 12 | AC-1.7 |
| 枚举 `EffectDirection/EffectScope/EffectFillStyle` | Public | DOWN/UP, LAYER/WHOLE, CUMULATIVE/ITERATIVE | — | 无 | 参数枚举 @since 12 | 全部 |

## 接口规格

### 接口定义

**ScaleSymbolEffect(scope?, direction?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(scope?: EffectScope, direction?: EffectDirection)` |
| 返回值 | `ScaleSymbolEffect` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| scope | EffectScope | 否 | 默认 | LAYER/WHOLE |
| direction | EffectDirection | 否 | 默认 | DOWN/UP |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 全参 | effectType=SCALE | AC-1.1 |
| 2 | 缺省 | 默认派生 | AC-2.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** 全部 @since 12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| effectType 映射 | 子类→SymbolEffectType(constants.h:27) | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 子类映射可单测 | 单测 | constants.h:27 |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 动效不携带语义 | — |

## Spec 自审清单
- [x] 无占位符
- [x] AC 用 WHEN/THEN
- [x] 范围明确
- [x] 无模糊表述
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项检查

## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SymbolEffect 子类到 SymbolEffectType 映射"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`
