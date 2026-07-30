# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolGlyph 颜色与渐变填充 |
| 特性编号 | Func-05-09-07-Feat-03 |
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
- 源码定位：`symbol_model_ng.cpp`（SetFontColor/SetShaderStyle/ResetShaderStyle）、`constants.h:60–124`（SymbolGradient/SymbolGradientType/SDKGradientDirection）

## 用户故事

### US-1: 多色填充
作为开发者，我希望经 fontColor 数组为多层符号指定多色。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `fontColor([Color.Red, Color.Blue])` THEN 写入 SymbolColorList（MEASURE_SELF）并按层着色 | 正常 |
| AC-1.2 | WHEN fontColor 数组为空 THEN 按默认/主题色处理，不崩溃 | 边界 |
| AC-1.3 | WHEN fontColor 使用 Resource THEN 经资源注册（IsFontColorResource/FontColorResource）异步加载 | 正常 |

### US-2: 增强颜色度量 (symbolColor)
作为开发者，我希望经 C-API/koala 的 symbolColor 使用 ColorMetrics 增强颜色表达。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN C-API `setFontColor` 传入 ColorMetrics THEN 按度量解析多层颜色 | 正常 |

### US-3: 渐变着色 (shaderStyle)
作为开发者，我希望经 shaderStyle 为符号施加线性/径向/颜色着色器渐变。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `shaderStyle(ShaderStyle)` 或数组 THEN 写入 ShaderStyle（vector<SymbolGradient>），按 SymbolGradientType 渲染 | 正常 |
| AC-3.2 | WHEN SymbolGradientType=LINEAR_GRADIENT THEN 按 SDKGradientDirection（9 方向）与 angle 渲染 | 正常 |
| AC-3.3 | WHEN SymbolGradientType=RADIAL_GRADIENT THEN 按 radialCenterX/Y、radius 渲染 | 正常 |
| AC-3.4 | WHEN C-API `resetShaderStyle` THEN 清除渐变回到纯色 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-03 | 单测 | text_layout_property.h:252 |
| AC-1.2 | R-2 | TASK-03 | 单测 | — |
| AC-1.3 | R-3 | TASK-03 | 单测 | symbol_model_ng.cpp 资源路径 |
| AC-2.1 | R-1 | TASK-03 | C-API 单测 | arkoala_api.h:8497 |
| AC-3.1 | R-4 | TASK-03 | 单测 | text_layout_property.h:261 |
| AC-3.2 | R-5 | TASK-03 | 单测 | constants.h:72 |
| AC-3.3 | R-5 | TASK-03 | 单测 | constants.h:96 |
| AC-3.4 | R-6 | TASK-03 | C-API 单测 | arkoala_api.h:8534 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 设置 fontColor(Array<ResourceColor>) | 写 SymbolColorList（MEASURE_SELF），按层着色 | 数组长度对应层数 | AC-1.1,2.1 |
| R-2 | 边界 | 数组为空 | 按默认/主题色 | — | AC-1.2 |
| R-3 | 行为 | fontColor 使用 Resource | 经 RegisterSymbolFontColorResource/IsFontColorResource 异步加载 | 资源解析失败回退 | AC-1.3 |
| R-4 | 行为 | 设置 shaderStyle | 写 ShaderStyle(vector<SymbolGradient>)，按 SymbolGradientType 渲染 | COLOR_SHADER/RADIAL/LINEAR | AC-3.1 |
| R-5 | 行为 | LINEAR→direction+angle；RADIAL→center+radius | 按几何参数渲染 | direction∈9 方向，angle/radius≥0 | AC-3.2,3.3 |
| R-6 | 恢复 | C-API resetShaderStyle | 清除渐变回纯色 | — | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 多色写入 | 单测 | MEASURE_SELF 刷新 |
| VM-2 | R-3 资源态 | 单测 | 资源回退 |
| VM-3 | R-4/R-5 渐变 | 单测 | gradientType 分支 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `fontColor(value: Array<ResourceColor>)` | Public | 颜色数组 | this | 无 | 多色填充 @since 11/12 | AC-1.1 |
| C-API `setFontColor`/`resetFontColor`/`setFontColorWithPlaceholder`/`setFontColorJs` | System | KNode, colors | void | 无 | 颜色下发 | AC-1.1,2.1 |
| C-API `getIsFontColorResource` | System | KNode | bool | 无 | 资源态查询 | AC-1.3 |
| `symbolColor(value)` | InnerApi/koala | Array<ResourceColor\|ColorMetrics> | this | 无 | 增强颜色（非公共 .d.ts） | AC-2.1 |
| `shaderStyle(value)` | InnerApi/koala | Array<ShaderStyle>\|ShaderStyle | this | 无 | 渐变着色（非公共 .d.ts） | AC-3.1 |
| C-API `setShaderStyle`/`resetShaderStyle` | System | KNode, gradients | void | 无 | 渐变下发/重置 | AC-3.1,3.4 |

## 接口规格

### 接口定义

**fontColor(value: Array<ResourceColor>)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontColor(value: Array<ResourceColor>): SymbolGlyphAttribute` |
| 返回值 | `SymbolGlyphAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Array<ResourceColor> | 是 | — | 空数组触发 R-2；元素可为 Color/number/string/Resource |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多色数组 | 按层着色 | AC-1.1 |
| 2 | Resource | 异步加载 | AC-1.3 |
| 3 | 空数组 | 默认色 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** fontColor @since 11/12；symbolColor/shaderStyle 不在公共 ArkTS，仅 C-API/koala（记风险）
- **API 版本号策略:** 全量 @since 标注；公共缺口在风险表标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SymbolColorList MEASURE_SELF | 颜色变更重测自绘 | AC-1.1 |
| 公共 ArkTS 缺 symbolColor/shaderStyle | 见风险 | AC-2.1,3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 渐变分支可单测 | 单测 | constants.h |

## 多设备适配声明
无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 是 | 颜色随主题/Resource | AC-1.3 |

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
    query: "SymbolGlyph ShaderStyle SymbolGradient 渲染路径"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`（注：symbolColor/shaderStyle 不在公共 .d.ts，源于 koala/C-API）
