# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolGlyph 多范式接口与通用能力 |
| 特性编号 | Func-05-09-07-Feat-08 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 11/12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`07-symbol-glyph/design.md`
- 源码定位：`arkoala_api.h:8493–8536`（ArkUISymbolGlyphModifier）、`symbol_glyph_dynamic_modifier.cpp:472–566`、`cj_symbol_glyph_ffi.h`、`ArkSymbolGlyphComponent`、`js_view_abstract.cpp:7929/13645`

## 用户故事

### US-1: 多范式接入一致性
作为开发者，我希望在动态 ArkTS、静态 ArkTS、CJ、C-API 四路都能创建并配置 SymbolGlyph。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态 ArkTS 经 `SymbolGlyphModifier`/`applySymbolGlyphModifierToNode` THEN 属性下发到 SymbolModelNG | 正常 |
| AC-1.2 | WHEN 静态 ArkTS 经 `symbolglyph.ets` 生成的 ArkSymbolGlyphComponent THEN 走静态 modifier | 正常 |
| AC-1.3 | WHEN CJ 前端经 `cj_symbol_glyph_ffi` THEN 下发到 SymbolModelNG | 正常 |
| AC-1.4 | WHEN C-API 经 `getSymbolGlyphModifier`（43 函数指针）THEN 下发到 SymbolModelNG | 正常 |

### US-2: 通用能力继承
作为开发者，我希望 SymbolGlyph 继承 CommonMethod 通用属性与 attributeModifier。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `attributeModifier(modifier)` THEN 应用自定义 modifier | 正常 |
| AC-2.2 | WHEN 继承通用属性（size/margin/position/opacity 等）THEN 与 TextPattern 通用路径一致 | 正常 |
| AC-2.3 | WHEN C-API `jsClip`/SetClipEdge THEN 按 ClipEdge 裁剪 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-08 | 单测 | js_view_abstract.cpp:7929 |
| AC-1.2 | R-1 | TASK-08 | 单测 | symbolglyph.ets |
| AC-1.3 | R-1 | TASK-08 | 单测 | cj_symbol_glyph_ffi.h |
| AC-1.4 | R-1 | TASK-08 | C-API 单测 | arkoala_api.h:8493 |
| AC-2.1 | R-2 | TASK-08 | 单测 | ArkSymbolGlyphComponent |
| AC-2.2 | R-3 | TASK-08 | 单测 | CommonMethod |
| AC-2.3 | R-4 | TASK-08 | C-API 单测 | arkoala_api.h:8527 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 四范式任意路创建/配置 | 统一下发到 SymbolModelNG | 路径差异在 bridge 层 | AC-1.1..1.4 |
| R-2 | 行为 | attributeModifier(modifier) | 应用自定义 modifier | modifier 实现 AttributeModifier | AC-2.1 |
| R-3 | 行为 | 继承通用属性 | 走 TextPattern/CommonMethod 通用路径 | — | AC-2.2 |
| R-4 | 行为 | C-API jsClip/SetClipEdge | 按 ClipEdge 裁剪 | bool | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 四范式一致 | 单测+C-API 单测 | 统一下发 |
| VM-2 | R-2/R-3 通用 | 单测 | CommonMethod 继承 |
| VM-3 | R-4 clip | C-API 单测 | ClipEdge |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `attributeModifier(value: AttributeModifier<SymbolGlyphAttribute>)` | Public | modifier | this | 无 | 自定义 modifier @since 11/12 | AC-2.1 |
| C-API `getSymbolGlyphModifier`（含 create/createFrameNode/set*/reset* 共 43 指针） | System | KNode,... | void/ptr | 无 | NDK modifier 面 @since 12 | AC-1.4 |
| C-API `jsClip` | System | KNode, bool | void | 无 | 裁剪 | AC-2.3 |

## 接口规格

### 接口定义

**attributeModifier(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `attributeModifier(value: AttributeModifier<SymbolGlyphAttribute> \| AttributeModifier<CommonMethod>): SymbolGlyphAttribute` |
| 返回值 | `SymbolGlyphAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | AttributeModifier | 是 | — | 实现 AttributeModifier 接口 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 modifier | 应用 | AC-2.1 |
| 2 | 四范式任一路 | 统一下发 | AC-1.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** attributeModifier/通用继承 @since 11/12；C-API @since 12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 四范式一致下发 | bridge 层差异，Model 统一 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 四范式可单测 | 单测 | symbol_glyph_dynamic_modifier.cpp |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 复用 TextPattern 无障碍 | AC-2.2 |

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
    query: "SymbolGlyph 四范式 bridge 一致性"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`
