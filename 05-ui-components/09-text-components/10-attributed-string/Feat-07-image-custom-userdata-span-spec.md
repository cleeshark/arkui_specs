# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 图片/自定义/UserData Span |
| 特性编号 | Func-05-09-10-Feat-07 |
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
- 源码定位：`span_object.h:370`（ImageSpan）、`js_span_object.cpp:1157`（JSImageAttachment→"ImageAttachment"）、`styled_string.d.ts:1409/1864/1908`、`CustomSpan` 抽象

## 用户故事

### US-1: 图片附件
作为开发者，我希望经 `ImageAttachment` 在属性字符串中嵌入图片。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `new ImageAttachment({value,size,verticalAlign,objectFit,layoutStyle,colorFilter?})`（@since 12，colorFilter @since 15）THEN 创建 ImageSpan | 正常 |
| AC-1.2 | WHEN `new ImageAttachment(attachment: AttachmentType)`（@since 15）THEN 经 ResourceImageAttachmentOptions 构造 | 正常 |
| AC-1.3 | WHEN layoutStyle（margin/padding/borderRadius）THEN 应用布局样式 | 正常 |

### US-2: 自定义 Span
作为开发者，我希望经 `CustomSpan` 自定义 measure/draw。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 实现 `onMeasure/onDraw`（@since 12）THEN 自定义测量/绘制 | 正常 |
| AC-2.2 | WHEN `invalidate()`（@since 13）THEN 触发重绘 | 正常 |
| AC-2.3 | WHEN CustomSpanMeasureInfo/DrawInfo/Metrics 缺省 THEN 按默认 | 边界 |

### US-3: UserData Span
作为开发者，我希望经 `UserDataSpan` 携带自定义数据并参与序列化。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 继承 `UserDataSpan`（@since 12）THEN 携带自定义数据 | 正常 |
| AC-3.2 | WHEN marshalling(callback)（@since 18）THEN ExtSpan↔UserDataSpan 序列化回调 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-07 | 单测 | span_object.h:370 |
| AC-1.2 | R-1 | TASK-AS-07 | 单测 | styled_string.d.ts:1431 |
| AC-1.3 | R-2 | TASK-AS-07 | 单测 | styled_string.d.ts:1703 |
| AC-2.1 | R-3 | TASK-AS-07 | 单测 | styled_string.d.ts:1864 |
| AC-2.2 | R-3 | TASK-AS-07 | 单测 | styled_string.d.ts:1897 |
| AC-2.3 | R-4 | TASK-AS-07 | 单测 | — |
| AC-3.1 | R-5 | TASK-AS-07 | 单测 | styled_string.d.ts:1908 |
| AC-3.2 | R-5 | TASK-AS-07 | 单测 | styled_string.d.ts:194 |

## 觅则定义

| 觅则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | ImageAttachment({...})/AttachmentType 构造（@since 12，colorFilter @since 15） | 创建 ImageSpan | value PixelMap | AC-1.1,1.2 |
| R-2 | 行为 | layoutStyle(margin/padding/borderRadius) | 应用布局样式 | — | AC-1.3 |
| R-3 | 行为 | CustomSpan onMeasure/onDraw/invalidate（@since 12/13） | 自定义测量/绘制/重绘 | 抽象类 | AC-2.1,2.2 |
| R-4 | 边界 | CustomSpan Metrics/DrawInfo/MeasureInfo 缺省 | 按默认 | — | AC-2.3 |
| R-5 | 行为 | UserDataSpan（@since 12）+ marshalling(callback)（@since 18） | 携带数据 + ExtSpan 序列化回调 | systemapi callback | AC-3.1,3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 图片 | 单测 | ImageSpan |
| VM-2 | R-3 自定义 | 单测 | onMeasure/onDraw |
| VM-3 | R-5 UserData | 单测 | ExtSpan 序列化 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class ImageAttachment`（+ @since 15 AttachmentType ctor） | Public | value,size?,verticalAlign?,objectFit?,layoutStyle?,colorFilter? | 实例 | 无 | 图片附件 @since 12/15 | AC-1.1,1.2 |
| `ResourceImageAttachmentOptions`/`AttachmentType`/`ColorFilterType`/`ImageAttachmentInterface`/`ImageAttachmentLayoutStyle` | Public | — | — | 无 | 图片类型 @since 12/15 | AC-1.1..1.3 |
| `abstract class CustomSpan` + `CustomSpanMetrics`/`DrawInfo`/`MeasureInfo` | Public | onMeasure/onDraw | — | 无 | 自定义 @since 12 | AC-2.1,2.3 |
| `CustomSpan.invalidate()` | Public | — | void | 无 | 重绘 @since 13 | AC-2.2 |
| `abstract class UserDataSpan` | Public | — | — | 无 | 用户数据 @since 12 | AC-3.1 |
| `StyledStringMarshallingValue`/`StyledStringMarshallCallback`/`StyledStringUnmarshallCallback` | System | — | — | 无 | 序列化回调 @since 18 | AC-3.2 |

## 接口规格

### 接口定义

**ImageAttachment**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class ImageAttachment { value: PixelMap; size?: SizeOptions; verticalAlign?: ImageAlignment; objectFit?: ImageFit; layoutStyle?: ImageAttachmentLayoutStyle; colorFilter?: ColorFilterType }` |
| 返回值 | 实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | PixelMap | 是 | — | — |
| colorFilter | ColorFilterType | 否 | — | @since 15 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法图片 | 创建 ImageSpan | AC-1.1 |
| 2 | CustomSpan invalidate | 重绘 | AC-2.2 |
| 3 | marshalling callback | ExtSpan 序列化 | AC-3.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** ImageAttachment/CustomSpan/UserDataSpan @since 12；colorFilter/AttachmentType @since 15；invalidate @since 13；marshalling(callback) @since 18
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SpanType=IMAGE=300/CUSTOM_SPAN=400/USER_DATA=500 | span_object.h:40 | 全部 |
| ExtSpan=500↔UserDataSpan | 序列化回调 | AC-3.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 图片 measure 无明显开销 | 性能测试 | span_object.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 图片 span 需无障碍描述 | AC-1.1 |

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
    query: "ImageAttachment/CustomSpan/UserDataSpan 与 ExtSpan 序列化"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
