# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ParagraphStyle 段落属性 |
| 特性编号 | Func-05-09-10-Feat-05 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 12–18 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`10-attributed-string/design.md`
- 源码定位：`span_object.h:435`（ParagraphStyleSpan）、`js_span_object.cpp:1984`（JSParagraphStyleSpan→"ParagraphStyle"）、`styled_string.d.ts:801/909`

## 用户故事

### US-1: 段落属性
作为开发者，我希望经 `ParagraphStyle` 设置段落排版。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new ParagraphStyle({textAlign,textIndent,maxLines,overflow,wordBreak,leadingMargin,paragraphSpacing})`（@since 12，paragraphSpacing @since 18）THEN 创建 ParagraphStyleSpan | 正常 |

### US-2: 桥接扩展
作为开发者，我希望经 JSParagraphStyleSpan 使用 SDK 之外的扩展（textVerticalAlign/textDirection/shaderStyle/tailIndents）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 textVerticalAlign/textDirection（桥接扩展）THEN 应用 | 正常 |
| AC-2.2 | WHEN 设置 shaderStyle/tailIndents（桥接扩展）THEN 应用 | 正常 |
| AC-2.3 | WHEN leadingMargin 含 LeadingMarginPlaceholder + 自定义绘制回调 THEN 按占位符渲染 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-05 | 单测 | span_object.h:435 |
| AC-2.1 | R-2 | TASK-AS-05 | 单测 | js_span_object.cpp JSParagraphStyleSpan |
| AC-2.2 | R-2 | TASK-AS-05 | 单测 | js_span_object.cpp |
| AC-2.3 | R-3 | TASK-AS-05 | 单测 | — |

## 觅则定义

| 觅则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | ParagraphStyle({...}) | 创建 ParagraphStyleSpan（@since 12，paragraphSpacing @since 18） | 各属性可选 | AC-1.1 |
| R-2 | 行为 | JSParagraphStyleSpan 扩展（textVerticalAlign/textDirection/shaderStyle/tailIndents） | 应用（非公共 .d.ts） | — | AC-2.1,2.2 |
| R-3 | 行为 | leadingMargin LeadingMarginPlaceholder + 自定义绘制回调 | 按占位符渲染 | — | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 段落 | 单测 | ParagraphStyleSpan |
| VM-2 | R-2 扩展 | 单测 | 非公共面 |
| VM-3 | R-3 占位符 | 单测 | leadingMargin |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class ParagraphStyle` + `ParagraphStyleInterface` | Public | textAlign?/textIndent?/maxLines?/overflow?/wordBreak?/leadingMargin?/paragraphSpacing? | 实例 | 无 | 段落 @since 12/18 | AC-1.1 |
| JSParagraphStyleSpan 扩展 | InnerApi | textVerticalAlign/textDirection/shaderStyle/tailIndents | — | 无 | 桥接扩展（非公共 .d.ts） | AC-2.1,2.2 |

## 接口规格

### 接口定义

**ParagraphStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class ParagraphStyle { textAlign?: TextAlign; textIndent?: Dimension; maxLines?: number; overflow?: TextOverflow; wordBreak?: WordBreak; leadingMargin?: LeadingMarginOptions; paragraphSpacing?: Length }` |
| 返回值 | 实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| paragraphSpacing | Length | 否 | — | @since 18 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 全属性 | 创建 ParagraphStyleSpan | AC-1.1 |
| 2 | paragraphSpacing | @since 18 | AC-1.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** ParagraphStyle @since 12（paragraphSpacing @since 18）
- **API 版本号策略:** 全量 @since 标注；桥接扩展记风险

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SpanType=PARAGRAPH_STYLE=200 | span_object.h:40 | AC-1.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 段落可单测 | 单测 | span_object.h:435 |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 全设备 | RTL | textDirection 扩展支持 | 单测 | js_span_object.cpp |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 国际化 | 是 | textAlign/textDirection 支持 RTL | AC-2.1 |

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
    query: "ParagraphStyleSpan 与桥接扩展/leadingMargin 占位符"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
