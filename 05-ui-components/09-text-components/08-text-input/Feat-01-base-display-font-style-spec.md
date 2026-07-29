# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 基础显示与字体样式 |
| 特性编号 | Func-05-09-08-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_model_ng.h`（SetType/SetFontColor/SetFontSize/SetFontWeight/SetFontFamily/SetLetterSpacing/SetLineHeight/SetHalfLeading/SetTextOverflow/SetWordBreak/SetLineBreakStrategy/SetEllipsisMode/SetNumberOfLines/SetIncludeFontPadding/SetFallbackLineSpacing/SetCompressLeadingPunctuation/SetOrphanCharOptimization/SetPunctuationOverflow/SetTextDirection/SetBarStyle/SetTextDecoration 系列/SetGradientShaderStyle/SetColorShaderStyle/SetStrokeWidth 系列）

## 用户故事

### US-1: 字体样式
作为开发者，我希望设置 fontColor/fontSize/fontWeight/fontFamily/fontStyle/fontFeature。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `fontColor(value)` THEN 写入 TextColorFlagByUser+TextColor | 正常 |
| AC-1.2 | WHEN `fontSize(value)`/`fontWeight(value)`/`fontFamily(value)`/`fontStyle(value)` THEN 写入 FontStyle 组 | 正常 |
| AC-1.3 | WHEN `fontFeature(value)`（@since 12）THEN 写入 FontFeature | 正常 |

### US-2: 排版与行控制
作为开发者，我希望控制 textAlign/textIndent/letterSpacing/lineHeight/halfLeading/textOverflow/wordBreak/lineBreakStrategy/ellipsisMode/numberOfLines/includeFontPadding/fallbackLineSpacing/compressLeadingPunctuation/orphanCharOptimization/punctuationOverflow/direction。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `textAlign(TextAlign)` THEN 写入 TextAlign | 正常 |
| AC-2.2 | WHEN `letterSpacing(value)`（@since 12）/`lineHeight(value)`（@since 12）THEN 写入对应字段 | 正常 |
| AC-2.3 | WHEN `halfLeading(value)`（@since 16/18）THEN 写入 HalfLeading | 正常 |
| AC-2.4 | WHEN `textOverflow(value)`（@since 12/24）/`ellipsisMode(value)`（@since 24）THEN 写入对应字段 | 正常 |
| AC-2.5 | WHEN `wordBreak`/`lineBreakStrategy`（@since 12）THEN 写入对应字段 | 正常 |
| AC-2.6 | WHEN `numberOfLines`/`includeFontPadding`（@since 23）/`fallbackLineSpacing`（@since 23）/`compressLeadingPunctuation`（@since 23）/`orphanCharOptimization`/`punctuationOverflow`（@since 26）/`direction`（@since 23）THEN 写入 TextLineStyle 组 | 正常 |

### US-3: 装饰与渐变
作为开发者，我希望设置 decoration/linearGradient/radialGradient。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `decoration(TextDecorationOptions)`（@since 12/26）THEN 写入 TextDecoration×4 + LineThicknessScale | 正常 |
| AC-3.2 | WHEN `linearGradient`/`radialGradient`（@since 26，C-API NODE_TEXT_INPUT_LINEAR_GRADIENT/RADIAL_GRADIENT）THEN 写入 GradientShaderStyle | 正常 |

### US-4: 样式与滚动条
作为开发者，我希望设置 style(InputStyle)/barState。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN `style(TextInputStyle.DEFAULT\|INLINE)` THEN 写入 InputStyle | 正常 |
| AC-4.2 | WHEN `barState(value)` THEN 写入 BarState | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-01 | 单测 | text_field_paint_property.h |
| AC-1.2 | R-1 | TASK-TI-01 | 单测 | text_field_model_ng.h:57–59 |
| AC-2.1 | R-2 | TASK-TI-01 | 单测 | text_field_layout_property.h |
| AC-2.2 | R-2 | TASK-TI-01 | 单测 | text_field_model_ng.h:140 |
| AC-3.1 | R-3 | TASK-TI-01 | 单测 | text_field_model_ng.h:149 |
| AC-3.2 | R-3 | TASK-TI-01 | C-API 单测 | native_node.h:4417/4449 |
| AC-4.1 | R-4 | TASK-TI-01 | 单测 | text_field_paint_property.h |
| AC-4.2 | R-4 | TASK-TI-01 | 单测 | text_field_model_ng.h |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 设置 fontColor/fontSize/fontWeight/fontFamily/fontStyle/fontFeature | 写入 FontStyle 组 + 对应 FlagByUser | fontSize≥0 | AC-1.1,1.2,1.3 |
| R-2 | 行为 | 设置排版/行控制属性 | 写入 TextLineStyle 组 | @since 版本见 AC | AC-2.1..2.6 |
| R-3 | 行为 | 设置 decoration/linearGradient/radialGradient | 写入 TextDecoration×4/GradientShaderStyle + LineThicknessScale | 渐变 @since 26 | AC-3.1,3.2 |
| R-4 | 行为 | 设置 style/barState | 写入 InputStyle/BarState | — | AC-4.1,4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 字体写入 | 单测 | FlagByUser |
| VM-2 | R-2 行控制 | 单测 | @since 分支 |
| VM-3 | R-3 渐变 | C-API 单测 | NODE_TEXT_INPUT_LINEAR_GRADIENT |
| VM-4 | R-4 样式 | 单测 | InputStyle |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `type`（见 Feat-03）/`style(value)` | Public | TextInputStyle | this | 无 | 输入样式 @since 9/10/11 | AC-4.1 |
| `fontColor/fontSize/fontWeight/fontFamily/fontStyle` | Public | — | this | 无 | 字体 @since 7/10/11 | AC-1.1,1.2 |
| `fontFeature(value)` | Public | string | this | 无 | 字体特性 @since 12 | AC-1.3 |
| `textAlign/textIndent/textOverflow/letterSpacing/lineHeight/wordBreak/lineBreakStrategy` | Public | — | this | 无 | 排版 @since 7–24 | AC-2.1,2.2,2.4,2.5 |
| `halfLeading/ellipsisMode/numberOfLines/includeFontPadding/fallbackLineSpacing/compressLeadingPunctuation/direction` | Public | — | this | 无 | 行控制 @since 16–26 | AC-2.3,2.4,2.6 |
| `decoration(value)` | Public | TextDecorationOptions | this | 无 | 装饰 @since 12/26 | AC-3.1 |
| C-API `NODE_TEXT_INPUT_LINEAR_GRADIENT`/`RADIAL_GRADIENT`/`PUNCTUATION_OVERFLOW`/`DECORATION` | System | KNode, gradient/options | void | 无 | 渐变/装饰 @since 26 | AC-3.2,3.1 |
| `barState(value)` | Public | BarState | this | 无 | 滚动条 @since 11/12 | AC-4.2 |

## 接口规格

### 接口定义

**fontSize(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontSize(value: Length): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Length | 是 | — | 负数按既有约束 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法字号 | 写入 FontStyle | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** 基线 @since 7/10/11；fontFeature/letterSpacing/lineHeight/textOverflow/wordBreak/lineBreakStrategy/decoration @since 12；halfLeading @since 16/18；ellipsisMode @since 24；includeFontPadding/fallbackLineSpacing/compressLeadingPunctuation/direction @since 23；linearGradient/radialGradient/punctuationOverflow/decoration(C-API) @since 26
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| FontStyle/TextLineStyle 组 | 属性分存 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 样式写入可单测 | 单测 | text_field_layout_property.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 大字体 | 是 | fontSize/adaptive 见 Feat-04 | — |
| 深色模式 | 是 | 颜色随主题 | — |

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
    query: "TextInput FontStyle/TextLineStyle 组写入与渐变 C-API"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
