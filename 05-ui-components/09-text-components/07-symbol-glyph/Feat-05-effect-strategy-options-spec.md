# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolGlyph 动效策略与选项 |
| 特性编号 | Func-05-09-07-Feat-05 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 11/12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`07-symbol-glyph/design.md`
- 源码定位：`symbol_model_ng.cpp`（SetSymbolEffect/SetSymbolEffectOptions/UpdateSymbolEffect）、`symbol_effect_options.h:26`、`constants.h:27`（SymbolEffectType）

## 用户故事

### US-1: 旧版 effectStrategy
作为开发者，我希望经 effectStrategy 设置旧版 NONE/SCALE/HIERARCHICAL 动效策略。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `effectStrategy(SymbolEffectStrategy.SCALE)` THEN 写 SymbolEffectStrategy=SCALE | 正常 |
| AC-1.2 | WHEN `effectStrategy(NONE)` THEN 无动效 | 正常 |

### US-2: 新版 symbolEffect + 选项
作为开发者，我希望经 symbolEffect + SymbolEffectOptions 设置可触发动效。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `symbolEffect(effect, isActive=true)` THEN 触发对应 effectType 动效 | 正常 |
| AC-2.2 | WHEN `symbolEffect(effect, triggerValue=n)` THEN 按数值触发 | 正常 |
| AC-2.3 | WHEN isActive=false THEN 停止动效 | 正常 |
| AC-2.4 | WHEN 设置 SymbolEffectOptions（scope/fillStyle/replaceType）THEN 按选项派生动效参数 | 正常 |
| AC-2.5 | WHEN C-API `updateSymbolEffect(type, isActive, isTxtActiveSource)` THEN 按来源区分文本/控件触发 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-05 | 单测 | text_layout_property.h:256 |
| AC-2.1 | R-2 | TASK-05 | 单测 | symbol_model_ng.h:76 |
| AC-2.2 | R-3 | TASK-05 | 单测 | symbolglyph.d.ts:668 |
| AC-2.3 | R-2 | TASK-05 | 单测 | — |
| AC-2.4 | R-4 | TASK-05 | 单测 | symbol_effect_options.h:26 |
| AC-2.5 | R-5 | TASK-05 | C-API 单测 | arkoala_api.h:8517 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | effectStrategy(NONE/SCALE/HIERARCHICAL) | 写 SymbolEffectStrategy(uint32, MEASURE_SELF) | 枚举 0/1/2 | AC-1.1,1.2 |
| R-2 | 行为 | symbolEffect(effect, isActive=true/false) | 触发/停止对应 effectType 动效 | effect 为 SymbolEffect 子类 | AC-2.1,2.3 |
| R-3 | 行为 | symbolEffect(effect, triggerValue=n) | 按数值触发 | n≥0 | AC-2.2 |
| R-4 | 行为 | 设置 SymbolEffectOptions | 派生 scope/fillStyle/replaceType 参数 | scope∈LAYER/WHOLE, fillStyle∈CUMULATIVE/ITERATIVE | AC-2.4 |
| R-5 | 行为 | updateSymbolEffect(type, isActive, isTxtActiveSource) | 区分文本/控件触发源 | isTxtActiveSource bool | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 旧版策略 | 单测 | SymbolEffectStrategy |
| VM-2 | R-2/R-3 触发 | 单测 | active/trigger |
| VM-3 | R-4 选项 | 单测 | options 派生 |
| VM-4 | R-5 C-API | C-API 单测 | 来源区分 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `effectStrategy(value: SymbolEffectStrategy)` | Public | 枚举 | this | 无 | 旧版策略 @since 11/12 | AC-1.1 |
| `symbolEffect(symbolEffect, isActive?)` | Public | SymbolEffect, bool | this | 无 | 触发/停止 @since 12 | AC-2.1 |
| `symbolEffect(symbolEffect, triggerValue?)` | Public | SymbolEffect, number | this | 无 | 数值触发 @since 12 | AC-2.2 |
| C-API `setEffectStrategy`/`resetEffectStrategy` | System | KNode, uint32 | void | 无 | 旧版下发 | AC-1.1 |
| C-API `updateSymbolEffect(node, type, isActive, isTxtActiveSource)` | System | KNode, uint32, bool, bool | void | 无 | 运行时切换 | AC-2.5 |
| C-API `setSymbolEffectOptions` | System | KNode, options | void | 无 | 选项下发 | AC-2.4 |

## 接口规格

### 接口定义

**symbolEffect(symbolEffect, isActive?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `symbolEffect(symbolEffect: SymbolEffect, isActive?: boolean): SymbolGlyphAttribute` |
| 返回值 | `SymbolGlyphAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| symbolEffect | SymbolEffect | 是 | — | 7 子类之一（见 Feat-06） |
| isActive | boolean | 否 | — | true 触发/false 停止 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isActive=true | 触发动效 | AC-2.1 |
| 2 | isActive=false | 停止动效 | AC-2.3 |
| 3 | triggerValue=n | 数值触发 | AC-2.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** effectStrategy @since 11/12；symbolEffect @since 12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| MEASURE_SELF | 策略/选项变更重测 | 全部 |
| 触发源区分 | isTxtActiveSource | AC-2.5 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 动效起播无卡顿 | 帧率测试 | — |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 动效不影响语义 | — |

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
    query: "SymbolGlyph SymbolEffectOptions 派生与 isTxtActiveSource"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`
