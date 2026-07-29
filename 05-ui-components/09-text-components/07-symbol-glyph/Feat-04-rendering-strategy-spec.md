# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolGlyph 渲染策略 |
| 特性编号 | Func-05-09-07-Feat-04 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 11/12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`07-symbol-glyph/design.md`
- 源码定位：`symbol_model_ng.cpp`（SetSymbolRenderingStrategy）、`text_layout_property.h:255`、`symbolglyph.d.ts:75`（SymbolRenderingStrategy 枚举）

## 用户故事

### US-1: 渲染策略选择
作为开发者，我希望经 renderingStrategy 控制多层符号的着色方式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `renderingStrategy(SymbolRenderingStrategy.SINGLE)` THEN 单色单层渲染 | 正常 |
| AC-1.2 | WHEN `renderingStrategy(MULTIPLE_COLOR)` THEN 按 SymbolColorList 多层多色渲染 | 正常 |
| AC-1.3 | WHEN `renderingStrategy(MULTIPLE_OPACITY)` THEN 按多层透明度渲染 | 正常 |
| AC-1.4 | WHEN C-API `resetRenderingStrategy` THEN 回退默认策略 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-04 | 单测 | text_layout_property.h:255 |
| AC-1.2 | R-1 | TASK-04 | 单测 | constants.h |
| AC-1.3 | R-1 | TASK-04 | 单测 | constants.h |
| AC-1.4 | R-2 | TASK-04 | C-API 单测 | arkoala_api.h:8512 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 设置 renderingStrategy(SINGLE/MULTIPLE_COLOR/MULTIPLE_OPACITY) | 写 SymbolRenderingStrategy(uint32, MEASURE_SELF)，按策略渲染 | 枚举 0/1/2 | AC-1.1..1.3 |
| R-2 | 恢复 | C-API resetRenderingStrategy | 回退默认策略 | — | AC-1.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 三策略 | 单测 | MEASURE_SELF |
| VM-2 | R-2 reset | C-API 单测 | 回退默认 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `renderingStrategy(value: SymbolRenderingStrategy)` | Public | 枚举 | this | 无 | 渲染策略 @since 11/12 | AC-1.1 |
| 枚举 `SymbolRenderingStrategy` | Public | SINGLE=0/MULTIPLE_COLOR=1/MULTIPLE_OPACITY=2 | — | 无 | 策略枚举 @since 11/12 | 全部 |
| C-API `setRenderingStrategy`/`resetRenderingStrategy` | System | KNode, uint32 | void | 无 | 下发/重置 | AC-1.1,1.4 |

## 接口规格

### 接口定义

**renderingStrategy(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `renderingStrategy(value: SymbolRenderingStrategy): SymbolGlyphAttribute` |
| 返回值 | `SymbolGlyphAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | SymbolRenderingStrategy | 是 | SINGLE | 越界值按实现既有约束 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SINGLE | 单色单层 | AC-1.1 |
| 2 | MULTIPLE_COLOR | 多层多色 | AC-1.2 |
| 3 | MULTIPLE_OPACITY | 多层透明度 | AC-1.3 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** @since 11/12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| MEASURE_SELF | 策略变更重测 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 策略分支可单测 | 单测 | text_layout_property.h:255 |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 策略不影响语义 | — |

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
    query: "SymbolGlyph renderingStrategy MEASURE_SELF 路径"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`
