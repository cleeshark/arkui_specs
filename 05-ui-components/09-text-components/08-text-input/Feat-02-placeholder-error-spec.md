# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput Placeholder 与错误提示 |
| 特性编号 | Func-05-09-08-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_model_ng.h`（SetPlaceholderColor/ResetPlaceholderColor/SetPlaceholderFont）、`text_field_layout_property.h`（PlaceholderFontStyle/PlaceholderTextLineStyle 组）

## 用户故事

### US-1: Placeholder
作为开发者，我希望设置 placeholder 文本、颜色、字体。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 构造 `TextInput({placeholder:'提示'})` 或经属性 THEN 写入 Placeholder | 正常 |
| AC-1.2 | WHEN `placeholderColor(value)` THEN 写入 PlaceholderColor | 正常 |
| AC-1.3 | WHEN `placeholderFont(value)` THEN 写入 PlaceholderFontStyle（size/weight/family/italic） | 正常 |

### US-2: 错误提示/单位/下划线
作为开发者，我希望经 showError/showUnit/showUnderline/underlineColor 提示错误与状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `showError(value?)`（@since 12）THEN 显示错误文本 | 正常 |
| AC-2.2 | WHEN `showUnit(builder)` THEN 渲染单位 builder | 正常 |
| AC-2.3 | WHEN `showUnderline(true)` THEN 显示下划线 | 正常 |
| AC-2.4 | WHEN `underlineColor({typing,normal,error,disable})`（@since 12）THEN 按状态着色下划线 | 正常 |
| AC-2.5 | WHEN underlineColor 单值 THEN 写入 normal 色 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-02 | 单测 | text_field_layout_property.h |
| AC-1.2 | R-2 | TASK-TI-02 | 单测 | text_field_model_ng.h:40 |
| AC-1.3 | R-2 | TASK-TI-02 | 单测 | text_field_model_ng.h:42 |
| AC-2.1 | R-3 | TASK-TI-02 | 单测 | text_input.d.ts showError |
| AC-2.2 | R-4 | TASK-TI-02 | 单测 | — |
| AC-2.3 | R-5 | TASK-TI-02 | 单测 | text_field_model_ng.h SetShowUnderline |
| AC-2.4 | R-5 | TASK-TI-02 | 单测 | text_field_model_ng.h:99–108 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 设置 placeholder | 写入 Placeholder | ResourceStr | AC-1.1 |
| R-2 | 行为 | 设置 placeholderColor/placeholderFont | 写入 PlaceholderColor/PlaceholderFontStyle | — | AC-1.2,1.3 |
| R-3 | 行为 | showError(value?) | 显示错误文本（@since 12） | value 可选 | AC-2.1 |
| R-4 | 行为 | showUnit(builder) | 渲染单位 builder | CustomBuilder | AC-2.2 |
| R-5 | 行为 | showUnderline(true)/underlineColor(状态) | 显示下划线并按状态着色 | typing/normal/error/disable | AC-2.3,2.4,2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-2 placeholder | 单测 | PlaceholderFontStyle |
| VM-2 | R-5 下划线状态 | 单测 | 4 状态色 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `placeholder`（option） | Public | ResourceStr | — | 无 | placeholder 文本 @since 7 | AC-1.1 |
| `placeholderColor(value)` | Public | ResourceColor | this | 无 | placeholder 色 @since 7 | AC-1.2 |
| `placeholderFont(value?)` | Public | Font | this | 无 | placeholder 字体 @since 7 | AC-1.3 |
| `showError(value?)` | Public | ResourceStr? | this | 无 | 错误提示 @since 12 | AC-2.1 |
| `showUnit(value)` | Public | CustomBuilder | this | 无 | 单位 @since 11 | AC-2.2 |
| `showUnderline(value)` | Public | boolean | this | 无 | 下划线 @since 11 | AC-2.3 |
| `underlineColor(value)` | Public | ResourceColor\|UnderlineColor | this | 无 | 下划线色 @since 12 | AC-2.4 |
| C-API `NODE_TEXT_INPUT_SHOW_UNDERLINE`/`UNDERLINE_COLOR` | System | KNode, bool/color | void | 无 | 下划线 @since 12 | AC-2.3,2.4 |

## 接口规格

### 接口定义

**underlineColor(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `underlineColor(value: ResourceColor \| UnderlineColor \| undefined): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor\|UnderlineColor | 是 | — | 单值→normal；UnderlineColor 含 typing/normal/error/disable |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | UnderlineColor 对象 | 按状态着色 | AC-2.4 |
| 2 | 单值 | 写入 normal | AC-2.5 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** placeholder/placeholderColor/placeholderFont @since 7；showError/showUnderline/underlineColor @since 12；showUnit @since 11
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| PlaceholderFontStyle 组 | placeholder 字体独立 | AC-1.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | placeholder 写入可单测 | 单测 | text_field_layout_property.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 是 | placeholder 色随主题 | AC-1.2 |

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
    query: "TextInput PlaceholderFontStyle 与 UnderlineColor 状态"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
