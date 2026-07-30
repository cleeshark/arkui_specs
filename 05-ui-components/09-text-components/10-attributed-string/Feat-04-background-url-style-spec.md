# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 背景/超链接 Style |
| 特性编号 | Func-05-09-10-Feat-04 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 14 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`10-attributed-string/design.md`
- 源码定位：`span_object.h:348/566`（BackgroundColorSpan/UrlSpan）、`js_span_object.cpp:2710/2774`（JSBackgroundColorSpan→"BackgroundColorStyle"/JSUrlSpan→"UrlStyle"）、`styled_string.d.ts:712/1032`

## 用户故事

### US-1: 背景色
作为开发者，我希望经 `BackgroundColorStyle` 设置文本背景。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new BackgroundColorStyle(textBackgroundStyle)`（@since 14）THEN 创建 BackgroundColorSpan | 正常 |

### US-2: 超链接
作为开发者，我希望经 `UrlStyle` 为区间附加 URL。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `new UrlStyle(url)`（@since 14）THEN 创建 UrlSpan | 正常 |
| AC-2.2 | WHEN StyledStringKey.URL（@since 14）THEN 查询 URL 样式 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-04 | 单测 | span_object.h:348 |
| AC-2.1 | R-2 | TASK-AS-04 | 单测 | span_object.h:566 |
| AC-2.2 | R-2 | TASK-AS-04 | 单测 | styled_string.d.ts:1032 |

## 规则定义

| 觅则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | BackgroundColorStyle(textBackgroundStyle) | 创建 BackgroundColorSpan（@since 14） | TextBackgroundStyle | AC-1.1 |
| R-2 | 行为 | UrlStyle(url)/StyledStringKey.URL | 创建 UrlSpan（@since 14） | url string | AC-2.1,2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 背景 | 单测 | BackgroundColorSpan |
| VM-2 | R-2 URL | 单测 | UrlSpan |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class BackgroundColorStyle` | Public | TextBackgroundStyle | 实例 | 无 | 背景 @since 14 | AC-1.1 |
| `class UrlStyle` | Public | url | 实例 | 无 | 超链接 @since 14 | AC-2.1 |

## 接口规格

### 接口定义

**UrlStyle(url)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class UrlStyle { url: string }` |
| 返回值 | 实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| url | string | 是 | — | URL 字符串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 url | 创建 UrlSpan | AC-2.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** BackgroundColorStyle/UrlStyle @since 14
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SpanType=BACKGROUND_COLOR=6/URL=7 | span_object.h:40 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 背景/URL 可单测 | 单测 | span_object.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 是 | 背景色随主题 | AC-1.1 |

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
    query: "BackgroundColorStyle/UrlStyle Span"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
