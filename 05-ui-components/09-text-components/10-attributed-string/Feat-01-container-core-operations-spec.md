# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | StyledString 容器与核心操作 |
| 特性编号 | Func-05-09-10-Feat-01 |
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
- 源码定位：`frameworks/core/components_ng/pattern/text/span/span_string.h`（SpanString）、`mutable_span_string.h`（MutableSpanString）、`span_object.h:40`（SpanType）、`tlv_util.h`、`js_span_string.cpp:193/1092`（JSSpanString/JSMutableSpanString）

## 用户故事

### US-1: 不可变容器
作为开发者，我希望经 `StyledString` 构造属性字符串并查询。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new StyledString(value, styles?)`（@since 12）THEN 构造不可变 SpanString | 正常 |
| AC-1.2 | WHEN `getString()`/`length` THEN 返回纯文本与长度 | 正常 |
| AC-1.3 | WHEN `getStyles(start,length,styledKey?)` THEN 返回 SpanStyle 数组（越界抛 401） | 边界 |
| AC-1.4 | WHEN `equals(other)` THEN 比较 | 正常 |
| AC-1.5 | WHEN `subStyledString(start,length?)` THEN 返回子串（越界抛 401） | 边界 |

### US-2: 可变容器
作为开发者，我希望经 `MutableStyledString` 增删改。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `replaceString/insertString/removeString` THEN 修改文本并通知 SpanWatcher | 正常 |
| AC-2.2 | WHEN `replaceStyle/setStyle/removeStyle/removeStyles/clearStyles` THEN 修改样式 | 正常 |
| AC-2.3 | WHEN `replaceStyledString/insertStyledString/appendStyledString` THEN 嵌入其他 StyledString | 正常 |

### US-3: 序列化与 HTML
作为开发者，我希望经 marshalling/HTML 往返。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `StyledString.fromHtml(html)`（@since 12，越界抛 401）THEN Promise<StyledString> | 正常 |
| AC-3.2 | WHEN `StyledString.toHtml(styledString)`（@since 14，越界抛 401）THEN string | 正常 |
| AC-3.3 | WHEN `marshalling(styledString)`（@since 13 systemapi）THEN ArrayBuffer | 正常 |
| AC-3.4 | WHEN `marshalling(styledString, callback)`/`unmarshalling(buffer, callback)`（@since 18 systemapi，越界抛 401）THEN 含 UserDataSpan 回调 | 正常 |

### US-4: 枚举与选项
作为开发者，我希望使用 StyledStringKey 枚举与 StyleOptions/SpanStyle。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 使用 StyledStringKey（FONT/DECORATION/BASELINE_OFFSET/LETTER_SPACING/TEXT_SHADOW/LINE_HEIGHT/BACKGROUND_COLOR @since 14/URL @since 14/GESTURE/PARAGRAPH_STYLE/IMAGE/CUSTOM_SPAN/USER_DATA）THEN 正确映射 SpanType | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-01 | 单测 | span_string.h:34 |
| AC-1.2 | R-1 | TASK-AS-01 | 单测 | span_string.h |
| AC-1.3 | R-2 | TASK-AS-01 | 单测 | styled_string.d.ts:122 |
| AC-1.5 | R-2 | TASK-AS-01 | 单测 | styled_string.d.ts:151 |
| AC-2.1 | R-3 | TASK-AS-01 | 单测 | mutable_span_string.h |
| AC-2.2 | R-3 | TASK-AS-01 | 单测 | mutable_span_string.h |
| AC-2.3 | R-3 | TASK-AS-01 | 单测 | mutable_span_string.h |
| AC-3.1 | R-4 | TASK-AS-01 | 单测 | styled_string.d.ts:166 |
| AC-3.2 | R-4 | TASK-AS-01 | 单测 | styled_string.d.ts:182 |
| AC-3.3 | R-5 | TASK-AS-01 | 单测 | styled_string.d.ts:221 |
| AC-3.4 | R-5 | TASK-AS-01 | 单测 | styled_string.d.ts:194/210 |
| AC-4.1 | R-6 | TASK-AS-01 | 单测 | span_object.h:40 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | StyledString 构造/getString/length/equals | 构造 SpanString 并查询（@since 12） | value string\|ImageAttachment\|CustomSpan | AC-1.1,1.2,1.4 |
| R-2 | 边界 | getStyles/subStyledString 越界 | 抛 401 | start/length 越界 | AC-1.3,1.5 |
| R-3 | 行为 | MutableStyledString 增删改 | 修改并通知 SpanWatcher | — | AC-2.1..2.3 |
| R-4 | 行为 | fromHtml（@since 12）/toHtml（@since 14） | HTML 往返（越界抛 401） | — | AC-3.1,3.2 |
| R-5 | 行为 | marshalling（@since 13）/unmarshalling/marshalling(callback)（@since 18） | TLV 序列化；UserDataSpan 回调 | systemapi | AC-3.3,3.4 |
| R-6 | 行为 | StyledStringKey 枚举 | 映射 SpanType | 12 值 | AC-4.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 容器 | 单测 | 越界 401 |
| VM-2 | R-3 可变 | 单测 | SpanWatcher |
| VM-3 | R-4/R-5 序列化 | 单测 | TLV/HTML 版本 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `StyledString` 构造 | Public | value, styles? | 实例 | 401（越界） | 不可变 @since 12 | AC-1.1 |
| `getString`/`length`/`equals`/`subStyledString` | Public | — | string/number/bool/StyledString | 401 | 查询 @since 12 | AC-1.2,1.4,1.5 |
| `getStyles` | Public | start,length,styledKey? | SpanStyle[] | 401 | 查询样式 @since 12 | AC-1.3 |
| `MutableStyledString` 全方法 | Public | — | void | — | 可变操作 @since 12 | AC-2.1..2.3 |
| `StyledString.fromHtml`/`toHtml` | Public | html/StyledString | Promise/string | 401 | HTML @since 12/14 | AC-3.1,3.2 |
| `StyledString.marshalling`/`unmarshalling`（+callback） | System | StyledString/ArrayBuffer | ArrayBuffer/Promise | 401 | TLV @since 13/18 | AC-3.3,3.4 |
| `StyleOptions`/`SpanStyle`/`StyledStringKey` | Public | — | — | — | 选项/枚举 @since 12/14 | AC-4.1 |

## 接口规格

### 接口定义

**StyledString(value, styles?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(value: string \| ImageAttachment \| CustomSpan, styles?: Array<StyleOptions>)` |
| 返回值 | `StyledString` |
| 开放范围 | Public |
| 错误码 | 401（styles 越界） |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string\|ImageAttachment\|CustomSpan | 是 | — | — |
| styles | Array<StyleOptions> | 否 | — | start/length 越界抛 401 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法构造 | 创建 SpanString | AC-1.1 |
| 2 | 越界 styles | 抛 401 | AC-1.3 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** 容器/getStyles/subStyledString/fromHtml @since 12；toHtml/BackgroundColorStyle/UrlStyle @since 14；marshalling @since 13；marshalling(callback)/unmarshalling(callback) @since 18
- **API 版本号策略:** 全量 @since 标注；SpanType 与 SDK StyledStringKey 微差异记风险

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| TLV 序列化 | marshalling 经 tlv_util | AC-3.3 |
| SpanType vs StyledStringKey | 内部 LineSpacing=8/HalfLeading/ExtSpan=500 | AC-4.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | TLV 编解码无明显开销 | 性能测试 | tlv_util.h |
| 可测试性 | 容器可单测 | 单测 | span_string_test_ng.cpp |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 国际化 | 是 | 文本/HTML 支持多语言 | AC-3.1 |

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
    query: "StyledString/MutableStyledString TLV 序列化与 SpanType 映射"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
