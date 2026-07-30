# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolGlyph 字体属性 |
| 特性编号 | Func-05-09-07-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 11/12/18 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`07-symbol-glyph/design.md`
- 源码定位：`symbol_model_ng.cpp`、`text_layout_property.h`（FontStyle 组）、`symbol_model_ng.h:30–53`

## 用户故事

### US-1: 字号/字重/字体族设置
作为开发者，我希望设置符号的 fontSize/fontWeight/fontFamily。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `fontSize(20)` THEN 写入 TextLayoutProperty.FontSize 并重测 | 正常 |
| AC-1.2 | WHEN `fontWeight(FontWeight.BOLD)` 或数值/字符串 THEN 写入 FontWeight | 正常 |
| AC-1.3 | WHEN `fontFamily("HMSymbol")` THEN 写入 FontFamily | 正常 |
| AC-1.4 | WHEN fontSize 为负数/0 THEN 不应用或按 0 处理，不崩溃 | 边界 |

### US-2: 字体缩放上下限
作为开发者，我希望经 minFontScale/maxFontScale 限制符号随系统字体的缩放范围。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `minFontScale(0.5)` THEN 系统字体缩放低于 0.5 时符号固定 0.5 | 正常 |
| AC-2.2 | WHEN `maxFontScale(2.0)` THEN 系统字体缩放高于 2.0 时符号固定 2.0 | 正常 |
| AC-2.3 | WHEN minFontScale > maxFontScale THEN 按实现既有约束处理（不崩溃） | 边界 |

### US-3: 可变字体
作为开发者，我希望经可变字体能力细粒度控制字重。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN C-API `setVariableFontWeight`/`setEnableVariableFontWeight(true)` THEN 启用可变字重 | 正常 |
| AC-3.2 | WHEN `setEnableDeviceFontWeightCategory(true)` THEN 按设备字重类别派生 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-02 | 单测 | text_layout_property.h FontStyle |
| AC-1.2 | R-1 | TASK-02 | 单测 | symbol_model_ng.h:30 |
| AC-1.3 | R-1 | TASK-02 | 单测 | symbol_model_ng.h:29 |
| AC-1.4 | R-2 | TASK-02 | 单测 | — |
| AC-2.1 | R-3 | TASK-02 | 单测 | symbol_model_ng.h:37 |
| AC-2.2 | R-3 | TASK-02 | 单测 | symbol_model_ng.h:38 |
| AC-2.3 | R-4 | TASK-02 | 单测 | — |
| AC-3.1 | R-5 | TASK-02 | C-API 单测 | arkoala_api.h:8500 |
| AC-3.2 | R-5 | TASK-02 | C-API 单测 | arkoala_api.h:8508 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 设置 fontSize/fontWeight/fontFamily | 写入 TextLayoutProperty.FontStyle 组并触发 MEASURE | fontSize≥0 | AC-1.1..1.3 |
| R-2 | 边界 | fontSize≤0 | 不应用/按 0 处理 | — | AC-1.4 |
| R-3 | 行为 | 设置 minFontScale/maxFontScale (@since 18) | 写入 FontStyle 组，限制系统字体缩放范围 | scale∈[0,∞)，Resource 可选 | AC-2.1,2.2 |
| R-4 | 边界 | minFontScale > maxFontScale | 不崩溃，按既有约束处理 | — | AC-2.3 |
| R-5 | 行为 | 启用可变字体/设备字重类别 | 经 VariableFontWeight/EnableVariableFontWeight/EnableDeviceFontWeightCategory 写入 | 仅 C-API/内部 | AC-3.1,3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 字号字重写入 | 单测 | FontStyle 组刷新 |
| VM-2 | R-3 缩放上下限 | 单测 | @since 18 路径 |
| VM-3 | R-5 可变字体 | C-API 单测 | setVariableFontWeight |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `fontSize(value: number\|string\|Resource)` | Public | 字号 | this | 无 | 设置字号 @since 11/12 | AC-1.1 |
| `fontWeight(value: number\|FontWeight\|string)` | Public | 字重 | this | 无 | 设置字重 @since 11/12 | AC-1.2 |
| C-API `setSymbolFontFamilies(node, family)` | System | KNode,string | void | 无 | 设置符号字体族 | AC-1.3 |
| `minFontScale(scale)` | Public | number\|Resource | this | 无 | 最小缩放 @since 18 | AC-2.1 |
| `maxFontScale(scale)` | Public | number\|Resource | this | 无 | 最大缩放 @since 18 | AC-2.2 |
| C-API `setVariableFontWeight`/`setEnableVariableFontWeight`/`setEnableDeviceFontWeightCategory` (+reset) | System | KNode,... | void | 无 | 可变字体 | AC-3.1,3.2 |
| 静态重载 `fontWeight(value, fontWeightConfigs?)` | Public | value+FontWeightConfigs | this | 无 | 字重配置（koala 生成） | AC-1.2 |

## 接口规格

### 接口定义

**fontSize(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontSize(value: number \| string \| Resource): SymbolGlyphAttribute` |
| 返回值 | `SymbolGlyphAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number\|string\|Resource | 是 | — | 负数/0 触发 R-2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=20 | 写入 FontSize 重测 | AC-1.1 |
| 2 | value≤0 | 不应用/按 0 | AC-1.4 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** fontSize/fontWeight @since 11/12；minFontScale/maxFontScale @since 18
- **API 版本号策略:** 全量 @since 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| FontStyle 组共享 | 字体属性存于 TextLayoutProperty FontStyle | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | FontStyle 写入可单测 | 单测 | text_layout_property.h |

## 多设备适配声明
无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 大字体 | 是 | minFontScale/maxFontScale 限制缩放 | AC-2.1,2.2 |

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
    query: "SymbolGlyph FontStyle 组写入与可变字体路径"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`
