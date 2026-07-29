# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 装饰排版 Style |
| 特性编号 | Func-05-09-10-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`10-attributed-string/design.md`
- 源码定位：`span_object.h:188/239/259/328/477/503`（DecorationSpan/BaselineOffsetSpan/LetterSpacingSpan/TextShadowSpan/LineHeightSpan/LineSpacingSpan）、`js_span_object.cpp:695/855/911/1061/1811/1889`、`styled_string.d.ts:506/608/643/678/996`

## 用户故事

### US-1: 装饰
作为开发者，我希望经 `DecorationStyle` 设置文本装饰（type/color/style）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new DecorationStyle({type, color?, style?})`（@since 12）THEN 创建 DecorationSpan | 正常 |
| AC-1.2 | WHEN 多装饰区间重叠 THEN ProcessMultiDecorationSpan 合并逻辑生效 | 正常 |

### US-2: 基线偏移/字间距/行高/文本阴影
作为开发者，我希望经 BaselineOffsetStyle/LetterSpacingStyle/LineHeightStyle/TextShadowStyle 设置排版。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `new BaselineOffsetStyle(baselineOffset)`（@since 12，LengthMetrics）THEN 创建 BaselineOffsetSpan | 正常 |
| AC-2.2 | WHEN `new LetterSpacingStyle(letterSpacing)`（@since 12）THEN 创建 LetterSpacingSpan | 正常 |
| AC-2.3 | WHEN `new LineHeightStyle(lineHeight)`（@since 12）THEN 创建 LineHeightSpan | 正常 |
| AC-2.4 | WHEN `new TextShadowStyle(textShadow)`（@since 12，Array<ShadowOptions>）THEN 创建 TextShadowSpan | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-03 | 单测 | span_object.h:188 |
| AC-1.2 | R-2 | TASK-AS-03 | 单测 | ProcessMultiDecorationSpan |
| AC-2.1 | R-3 | TASK-AS-03 | 单测 | span_object.h:239 |
| AC-2.2 | R-3 | TASK-AS-03 | 单测 | span_object.h:259 |
| AC-2.3 | R-3 | TASK-AS-03 | 单测 | span_object.h:477 |
| AC-2.4 | R-3 | TASK-AS-03 | 单测 | span_object.h:328 |

## 规则定义

| 觅则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | DecorationStyle({type,color?,style?}) | 创建 DecorationSpan（@since 12） | type 必填 | AC-1.1 |
| R-2 | 行为 | 多装饰区间重叠 | ProcessMultiDecorationSpan 合并 | — | AC-1.2 |
| R-3 | 行为 | BaselineOffsetStyle/LetterSpacingStyle/LineHeightStyle/TextShadowStyle | 创建对应 Span（@since 12） | 各取值 | AC-2.1..2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 装饰 | 单测 | DecorationSpan |
| VM-2 | R-2 多装饰合并 | 单测 | ProcessMultiDecorationSpan |
| VM-3 | R-3 排版 | 单测 | 各 Span |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class DecorationStyle` + `DecorationStyleInterface` | Public | type,color?,style? | 实例 | 无 | 装饰 @since 12 | AC-1.1 |
| `class BaselineOffsetStyle` | Public | LengthMetrics | 实例 | 无 | 基线偏移 @since 12 | AC-2.1 |
| `class LetterSpacingStyle` | Public | letterSpacing | 实例 | 无 | 字间距 @since 12 | AC-2.2 |
| `class LineHeightStyle` | Public | lineHeight | 实例 | 无 | 行高 @since 12 | AC-2.3 |
| `class TextShadowStyle` | Public | Array<ShadowOptions> | 实例 | 无 | 文本阴影 @since 12 | AC-2.4 |

## 接口规格

### 接口定义

**DecorationStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class DecorationStyle { type: TextDecoration; color?: ResourceColor; style?: TextDecorationStyle }` |
| 返回值 | 实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | TextDecoration | 是 | — | — |
| color | ResourceColor | 否 | 默认 | — |
| style | TextDecorationStyle | 否 | 默认 | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 单装饰 | 创建 DecorationSpan | AC-1.1 |
| 2 | 多装饰重叠 | 合并 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** 全部 @since 12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ProcessMultiDecorationSpan | 多装饰交集合并 | AC-1.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 装饰合并可单测 | 单测 | span_object.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 是 | 装饰色随主题 | AC-1.1 |

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
    query: "Decoration/BaselineOffset/LetterSpacing/LineHeight/TextShadow Span 与多装饰合并"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
