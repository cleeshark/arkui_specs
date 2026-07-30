# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextStyle 字体属性 |
| 特性编号 | Func-05-09-10-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`10-attributed-string/design.md`
- 源码定位：`span_object.h:164`（FontSpan）、`js_span_object.cpp:146`（JSFontSpan→"TextStyle"）、`styled_string.d.ts:357/441`

## 用户故事

### US-1: 字体属性
作为开发者，我希望经 `TextStyle` 设置 fontColor/fontFamily/fontSize/fontWeight/fontStyle。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new TextStyle({fontColor, fontFamily, fontSize, fontWeight, fontStyle})`（@since 12）THEN 创建 FontSpan | 正常 |
| AC-1.2 | WHEN 各属性可选 THEN 缺省按默认 | 边界 |

### US-2: 桥接扩展
作为开发者，我希望经 JSFontSpan 使用 SDK 之外的文本效果扩展（strokeWidth/superscript/fontConfigs/fontVariations）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN JSFontSpan 设置 strokeWidth/strokeColor/strokeJoinStyle THEN 应用描边（桥接扩展，非公共 .d.ts） | 正常 |
| AC-2.2 | WHEN 设置 superscript/fontConfigs/fontVariations THEN 应用（桥接扩展） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-02 | 单测 | span_object.h:164 |
| AC-1.2 | R-2 | TASK-AS-02 | 单测 | — |
| AC-2.1 | R-3 | TASK-AS-02 | 单测 | js_span_object.cpp JSFontSpan |
| AC-2.2 | R-3 | TASK-AS-02 | 单测 | js_span_object.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | TextStyle({fontColor,fontFamily,fontSize,fontWeight,fontStyle}) | 创建 FontSpan（@since 12） | 各属性可选 | AC-1.1 |
| R-2 | 边界 | 属性缺省 | 按默认派生 | — | AC-1.2 |
| R-3 | 行为 | JSFontSpan 扩展（strokeWidth/superscript/fontConfigs/fontVariations） | 应用文本效果（非公共 .d.ts） | — | AC-2.1,2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 TextStyle | 单测 | FontSpan |
| VM-2 | R-3 扩展 | 单测 | 非公共面 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class TextStyle` + `TextStyleInterface` | Public | fontColor?/fontFamily?/fontSize?/fontWeight?/fontStyle? | 实例 | 无 | 字体样式 @since 12 | AC-1.1 |
| JSFontSpan 扩展（strokeWidth/strokeColor/strokeJoinStyle/superscript/fontConfigs/fontVariations） | InnerApi | — | — | 无 | 桥接扩展（非公共 .d.ts） | AC-2.1,2.2 |

## 接口规格

### 接口定义

**TextStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class TextStyle { fontColor?: ResourceColor; fontFamily?: ResourceStr; fontSize?: number\|string\|Resource; fontWeight?: number\|FontWeight\|string; fontStyle?: FontStyle }` |
| 返回值 | `TextStyle` 实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| fontColor | ResourceColor | 否 | 默认 | — |
| fontFamily | ResourceStr | 否 | 默认 | — |
| fontSize | number\|string\|Resource | 否 | 默认 | ≥0 |
| fontWeight | number\|FontWeight\|string | 否 | 默认 | — |
| fontStyle | FontStyle | 否 | 默认 | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 全属性 | 创建 FontSpan | AC-1.1 |
| 2 | 缺省 | 默认派生 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** TextStyle @since 12
- **API 版本号策略:** 全量 @since 标注；JSFontSpan 扩展不在公共 .d.ts（记风险）

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| FontSpan | SpanType=FONT(span_object.h:40) | AC-1.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | TextStyle 可单测 | 单测 | span_object.h:164 |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 大字体 | 是 | fontSize 支持 | AC-1.1 |

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
    query: "TextStyle/FontSpan 与桥接扩展"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
