# 特性规格

> Func-04-03-11-Feat-03 文本间距与度量：固化 letterSpacing/lineHeight(+min/max/multiple)/baselineOffset 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 文本间距与度量 (Text Spacing & Metrics) |
| 特性编号 | Func-04-03-11-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持 letterSpacing/lineHeight/baselineOffset，API 20 param ResourceStr（动态），API 22 min/max/multiple，API 24 静态 min/max/multiple + styled-string，API 26 styled-string lineHeightMultiple |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | letterSpacing 字间距行为规格 | @since 7；param ResourceStr @since 20（仅动态） |
| ADDED | lineHeight 行高行为规格 | @since 7；接受 Resource（动态静态均有） |
| ADDED | minLineHeight/maxLineHeight/lineHeightMultiple 行为规格 | @since 22 dynamic / @since 24 static（Text 独有公开 API） |
| ADDED | baselineOffset 基线偏移行为规格 | @since 7；param ResourceStr @since 20（仅动态） |
| ADDED | C-API NODE_TEXT_LETTER_SPACING/NODE_TEXT_LINE_HEIGHT/NODE_TEXT_BASELINE_OFFSET + NODE_TEXT_MIN/MAX_LINE_HEIGHT/LINE_HEIGHT_MULTIPLE + NODE_SPAN/IMAGE_SPAN_BASELINE_OFFSET + NODE_TEXT_INPUT/AREA_LETTER_SPACING/LINE_HEIGHT 行为规格 | @since 12/16/20/22 |
| ADDED | styled-string C-API OH_ArkUI_LetterSpacingStyle/LineHeightStyle/BaselineOffsetStyle 行为规格 | @since 24（lineHeightMultiple @since 26） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: 设置字间距

**作为** 应用开发者,
**我想要** 通过 `.letterSpacing(value)` 设置字间距,
**以便** 调整文字字符间距（可负值压缩）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.letterSpacing(2)` THEN LetterSpacing=2fp，每字符间距增加 2fp | 正常 |
| AC-1.2 | WHEN 调用 `.letterSpacing(-1)` THEN LetterSpacing=-1fp，字符间距压缩（负值允许） | 正常 |
| AC-1.3 | WHEN 调用 `.letterSpacing('5vp')` THEN LetterSpacing=5vp | 正常 |
| AC-1.4 | WHEN 调用 `.letterSpacing($r('app.letter.x'))` (API 20+) THEN ResourceStr 类型解析为 Dimension | 正常 |
| AC-1.5 | WHEN letterSpacing 解析失败或百分比或 0 THEN 回退默认（0，不调整） | 异常 |
| AC-1.6 | WHEN 设置 LetterSpacing THEN 写入 FontStyle::LetterSpacing (Dimension, PROPERTY_UPDATE_MEASURE) + propNeedReCreateParagraph_=true；渲染时 ConvertToPxDistributeWithEnv 下传 Rosen txtStyle.letterSpacing (constants_converter.cpp:652-654) | 正常 |
| AC-1.7 | WHEN 在 Span 组件设置 letterSpacing THEN 写入 spanItem_->fontStyle (span_model_ng.cpp:302) | 正常 |
| AC-1.8 | WHEN 在 TextInput/TextArea/Search 设置 letterSpacing THEN 写入 TextFieldLayoutProperty（Search 委托 TextField 子节点） | 正常 |

### US-2: 设置行高

**作为** 应用开发者,
**我想要** 通过 `.lineHeight(value)` 设置行高,
**以便** 控制文本行间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.lineHeight(30)` THEN LineHeight=30fp；heightScale = 30/fontSize | 正常 |
| AC-2.2 | WHEN 调用 `.lineHeight('40vp')` THEN LineHeight=40vp | 正常 |
| AC-2.3 | WHEN 调用 `.lineHeight($r('app.line.h'))` THEN Resource 类型解析（动态静态均支持） | 正常 |
| AC-2.4 | WHEN 调用 `.lineHeight(-10)` 或负值 THEN JS bridge 重置 value.Reset()（负值不允许） | 异常 |
| AC-2.5 | WHEN lineHeight ≤ 0 或未设置 THEN 行高不受限，按字体大小自适应 | 正常 |
| AC-2.6 | WHEN lineHeight ≈ fontSize 或 lineHeight == 0 THEN heightOnly=false（不覆盖，向后兼容，constants_converter.cpp:427-429） | 边界 |
| AC-2.7 | WHEN lineHeight 为百分比 THEN heightOnly=true, heightScale=lineHeight.Value()（百分比比例） | 正常 |
| AC-2.8 | WHEN lineHeight 与 lineSpacing 同时设置 THEN heightScale = lineHeightScale + lineSpacingScale (constants_converter.cpp:705-706) | 正常 |
| AC-2.9 | WHEN 在 Span 设置 lineHeight THEN 参数类型为 Length（span.d.ts:348, @since 10） | 正常 |

### US-3: 设置行高倍数（lineHeightMultiple, API 22+）

**作为** 应用开发者,
**我想要** 通过 `.lineHeightMultiple(value)` 设置行高倍数,
**以便** 按字体高度比例设置行高。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.lineHeightMultiple(1.5)` (API 22+) THEN LineHeightMultiply=1.5；行高 = 1.5 × fontHeight | 正常 |
| AC-3.2 | WHEN 设置 lineHeightMultiple THEN **同时预设** LineHeight = DEFAULT_LINE_HEIGHT(28px)（js_text.cpp:647, style_modifier.cpp:14145-14147） | 边界 |
| AC-3.3 | WHEN 同时设置 lineHeight 与 lineHeightMultiple THEN **仅 lineHeightMultiple 生效**；Rosen 层 multiply 覆盖 lineHeight 派生的 heightScale (constants_converter.cpp:541-543) | 边界 |
| AC-3.4 | WHEN 调用 `.lineHeightMultiple(0)` 或负值 THEN ResetLineHeightMultiply（不设置） | 异常 |
| AC-3.5 | WHEN Reset lineHeightMultiple THEN LineHeight 不恢复原值（28px 预设保留，除非重新设置 lineHeight） | 边界 |
| AC-3.6 | WHEN lineHeightMultiple 仅 TextAttribute 暴露 THEN Span/TextInput/TextArea/Search/Button 不支持 | 边界 |
| AC-3.7 | WHEN 静态范式 lineHeightMultiple (@since 24 static) THEN 类型为 double\|undefined | 正常 |

### US-4: 设置行高最小/最大值（API 22+）

**作为** 应用开发者,
**我想要** 通过 `.minLineHeight(value)`/`.maxLineHeight(value)` 设置行高范围,
**以便** 约束行高在合理区间。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.minLineHeight(20)` (API 22+) THEN MinimumLineHeight=20；txtStyle.minLineHeight 下传 Rosen (constants_converter.cpp:521) | 正常 |
| AC-4.2 | WHEN 调用 `.maxLineHeight(50)` THEN MaximumLineHeight=50；txtStyle.maxLineHeight 下传 Rosen (constants_converter.cpp:534) | 正常 |
| AC-4.3 | WHEN maxLineHeight < minLineHeight THEN max 被 clamp 上调到 min（constants_converter.cpp:529） | 边界 |
| AC-4.4 | WHEN minLineHeight ≤ 0 或 maxLineHeight ≤ 0 THEN 不设置（回退默认） | 异常 |
| AC-4.5 | WHEN min/max 不支持百分比 THEN 参数类型为 LengthMetrics（text.d.ts:337,357）；百分比不支持 | 边界 |
| AC-4.6 | WHEN 实际按行 clamp 由 Rosen 引擎执行 THEN ace_engine 仅计算并转发 bounds | 正常 |
| AC-4.7 | WHEN min/max 仅 TextAttribute 暴露 (@since 22 dyn / @since 24 static) THEN Span/TextInput/TextArea/Search/Button 不支持 | 边界 |

### US-5: 设置基线偏移

**作为** 应用开发者,
**我想要** 通过 `.baselineOffset(value)` 设置基线偏移,
**以便** 调整文本基线垂直位置（正上负下）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.baselineOffset(10)` THEN BaselineOffset=10fp；正数内容上移 | 正常 |
| AC-5.2 | WHEN 调用 `.baselineOffset(-5)` THEN BaselineOffset=-5fp；负数内容下移 | 正常 |
| AC-5.3 | WHEN 调用 `.baselineOffset($r('app.baseline.x'))` (API 20+) THEN ResourceStr 类型解析 | 正常 |
| AC-5.4 | WHEN baselineOffset 百分比 THEN 按默认显示行为处理（text.d.ts:647-649） | 边界 |
| AC-5.5 | WHEN 渲染转换期 THEN txtStyle.baseLineShift = -ConvertToPxDistributeWithEnv(...)（取负，constants_converter.cpp:655-657）；ace 语义正数上移 = Rosen 负 baseLineShift | 正常 |
| AC-5.6 | WHEN baselineOffset 设置 THEN ace_engine 把 fabs(baselineOffset) 加到测量高度（text_layout_algorithm.cpp:230），不改变段落内在高度 | 正常 |
| AC-5.7 | WHEN 在 Span 设置 baselineOffset THEN 参数类型为 LengthMetrics（BaseSpan<T>.baselineOffset, span.d.ts:99, @since 12） | 正常 |
| AC-5.8 | WHEN 在 Span baselineOffset 百分比 THEN 拒绝（js_span.cpp:386-405, DimensionUnit::PERCENT 回退） | 边界 |
| AC-5.9 | WHEN 在 TextInput/TextArea/Search 设置 baselineOffset THEN **不支持**（未暴露） | 边界 |
| AC-5.10 | WHEN selection overlay / drag 使用 baselineOffset THEN 通过 TextPattern::GetBaselineOffset() 读取缓存值（text_pattern.cpp:9010） | 正常 |

### US-6: 通过 C-API 设置间距与度量

**作为** NDK 开发者,
**我想要** 通过 `setAttribute(NODE_TEXT_*, item)` 设置间距与度量,
**以便** 在 C 代码中控制文本表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `setAttribute(node, NODE_TEXT_LETTER_SPACING, {value[0].f32: 2.0})` THEN 设置 letterSpacing=2fp；支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA | 正常 |
| AC-6.2 | WHEN 调用 `setAttribute(node, NODE_TEXT_LINE_HEIGHT, {value[0].f32: 30.0})` THEN 设置 lineHeight=30fp；支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA | 正常 |
| AC-6.3 | WHEN 调用 `setAttribute(node, NODE_TEXT_BASELINE_OFFSET, {value[0].f32: 10.0})` THEN 设置 baselineOffset=10fp；支持 TEXT（SPAN 用 NODE_SPAN_BASELINE_OFFSET） | 正常 |
| AC-6.4 | WHEN 调用 `setAttribute(node, NODE_TEXT_MIN_LINE_HEIGHT, {value[0].f32: 20.0})` (@since 22) THEN 设置 MinimumLineHeight=20fp；**仅 TEXT** | 正常 |
| AC-6.5 | WHEN 调用 `setAttribute(node, NODE_TEXT_MAX_LINE_HEIGHT, {value[0].f32: 50.0})` (@since 22) THEN 设置 MaximumLineHeight=50fp；**仅 TEXT** | 正常 |
| AC-6.6 | WHEN 调用 `setAttribute(node, NODE_TEXT_LINE_HEIGHT_MULTIPLE, {value[0].f32: 1.5})` (@since 22) THEN 设置 LineHeightMultiply=1.5；同时预设 LineHeight=28px（style_modifier.cpp:14145-14147）；**仅 TEXT** | 正常 |
| AC-6.7 | WHEN 调用 `setAttribute(span, NODE_SPAN_BASELINE_OFFSET, {value[0].f32: 10.0})` THEN 设置 Span baselineOffset | 正常 |
| AC-6.8 | WHEN 调用 `setAttribute(imageSpan, NODE_IMAGE_SPAN_BASELINE_OFFSET, {value[0].f32: 10.0})` THEN 设置 ImageSpan baselineOffset | 正常 |
| AC-6.9 | WHEN 调用 `setAttribute(textInput, NODE_TEXT_INPUT_LETTER_SPACING, {value[0].f32: 2.0})` (@since 16) THEN 设置 TextInput letterSpacing | 正常 |
| AC-6.10 | WHEN 调用 `setAttribute(textInput, NODE_TEXT_INPUT_LINE_HEIGHT, {value[0].i32: 30})` (@since 20) THEN 设置 TextInput lineHeight（**i32 编码**，非 f32） | 边界 |
| AC-6.11 | WHEN 调用 `setAttribute(textArea, NODE_TEXT_AREA_LETTER_SPACING, {value[0].f32: 2.0})` (@since 16) THEN 设置 TextArea letterSpacing | 正常 |
| AC-6.12 | WHEN 调用 `setAttribute(textArea, NODE_TEXT_AREA_LINE_HEIGHT, {value[0].i32: 30})` (@since 20) THEN 设置 TextArea lineHeight（**i32 编码**） | 边界 |
| AC-6.13 | WHEN NODE_TEXT_MIN/MAX_LINE_HEIGHT/LINE_HEIGHT_MULTIPLE value[0].f32 < 0 THEN 仍调用 setter（传 0）但返回 ERROR_CODE_PARAM_INVALID (401) | 异常 |
| AC-6.14 | WHEN 在不支持节点（如 SPAN 调用 NODE_TEXT_MIN_LINE_HEIGHT）THEN no-op（SPAN_ATTRIBUTES_MAP 不含 min/max/multiple） | 边界 |
| AC-6.15 | WHEN 在 TEXT_INPUT/TEXT_AREA 调用 NODE_TEXT_BASELINE_OFFSET (1014) THEN SetBaseLineOffset else 分支调 getTextModifier()->setTextBaselineOffset（可能静默 no-op） | 边界 |

### US-7: 通过样式字符串 C-API 设置（@since 24/26）

**作为** NDK 开发者,
**我想要** 通过 `OH_ArkUI_LetterSpacingStyle/LineHeightStyle/BaselineOffsetStyle` 在样式字符串上设置间距,
**以便** 在 StyledString 场景精细控制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `OH_ArkUI_LetterSpacingStyle_Create()` (@since 24) THEN 返回新对象 | 正常 |
| AC-7.2 | WHEN 调用 `OH_ArkUI_LetterSpacingStyle_SetLetterSpacing(style, 2.0f)` THEN 设置 letterSpacing 字段 | 正常 |
| AC-7.3 | WHEN 调用 `OH_ArkUI_LineHeightStyle_Create()` THEN 返回新对象（含 lineHeight + optional lineHeightMultiple） | 正常 |
| AC-7.4 | WHEN 调用 `OH_ArkUI_LineHeightStyle_SetLineHeight(style, 30.0f)` THEN 设置 lineHeight 字段 | 正常 |
| AC-7.5 | WHEN 调用 `OH_ArkUI_LineHeightStyle_SetLineHeightMultiple(style, 1.5f)` (@since 26) THEN 设置 lineHeightMultiple（optional） | 正常 |
| AC-7.6 | WHEN 调用 `OH_ArkUI_LineHeightStyle_GetLineHeightMultiple` 且 optional 未设置 THEN 返回 0.0f | 异常 |
| AC-7.7 | WHEN 调用 `OH_ArkUI_BaselineOffsetStyle_Create/SetBaselineOffset` (@since 24) THEN 设置 baselineOffset 字段 | 正常 |
| AC-7.8 | WHEN 调用 `OH_ArkUI_SpanStyle_SetLetterSpacingStyle(spanStyle, letterSpacingStyle)` THEN 拷贝并设 styledKey=LETTER_SPACING | 正常 |
| AC-7.9 | WHEN `OH_ArkUI_SpanStyle_GetLineHeightStyle` 读取 THEN 仅拷出 lineHeight（**不拷出 lineHeightMultiple**，缺口 span_style_native_impl.cpp:1069-1077） | 边界 |
| AC-7.10 | WHEN styled-string lineHeightMultiple 为负 THEN ConvertToOriginLineHeightStyle 静默丢弃（span_style_native_impl.cpp:255） | 边界 |
| AC-7.11 | WHEN `OH_ArkUI_SpanStyle_Get*Style` 在 styledKey 不匹配时调用 THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.8 | R-1~R-5 | 已有实现 | 单测 | `test/unittest/core/components_ng/text/` |
| AC-2.1~2.9 | R-6~R-12 | 已有实现 | 单测 | 同上 |
| AC-3.1~3.7 | R-13~R-17 | 已有实现 | 单测 | 同上 |
| AC-4.1~4.7 | R-18~R-22 | 已有实现 | 单测 | 同上 |
| AC-5.1~5.10 | R-23~R-28 | 已有实现 | 单测 | 同上 |
| AC-6.1~6.15 | R-29~R-40 | 已有实现 | 单测 | `test/unittest/interfaces/native_node_test.cpp` |
| AC-7.1~7.11 | R-41~R-48 | 已有实现 | 单测 | `test/unittest/interfaces/native_styled_string_test.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 SetLetterSpacing | LetterSpacing 存为 Dimension（FP 单位）；写入 FontStyle::LetterSpacing；触发 propNeedReCreateParagraph_=true | 负值允许（压缩）；百分比/0 回退默认 | AC-1.1~1.3, AC-1.6 |
| R-2 | 行为 | letterSpacing 为 Resource (API 20+) | ResourceStr 类型解析（仅动态 API；静态不支持 Resource） | param-level @since 20 | AC-1.4 |
| R-3 | 异常 | letterSpacing 解析失败/百分比/0 | 回退默认（0，不调整） | text.d.ts:618 | AC-1.5 |
| R-4 | 行为 | Span letterSpacing | 写入 spanItem_->fontStyle (span_model_ng.cpp:302) | Span 并行存储 | AC-1.7 |
| R-5 | 行为 | TextInput/TextArea/Search letterSpacing | 写入 TextFieldLayoutProperty；Search 委托 TextField 子节点 | 逐组件路径 | AC-1.8 |
| R-6 | 行为 | 调用 SetLineHeight | LineHeight 存为 Dimension；heightScale = lineHeight_px / fontSize_px（constants_converter.cpp:478-479） | 负值不允许（JS Reset） | AC-2.1~2.3 |
| R-7 | 异常 | lineHeight 负值 | JS bridge value.Reset()（清除） | js_text.cpp:613-632 | AC-2.4 |
| R-8 | 行为 | lineHeight ≤ 0 或未设置 | 行高不受限，按字体大小自适应 | text.d.ts:460-462 | AC-2.5 |
| R-9 | 边界 | lineHeight ≈ fontSize 或 == 0 | heightOnly=false（不覆盖，向后兼容） | constants_converter.cpp:427-429 | AC-2.6 |
| R-10 | 行为 | lineHeight 为百分比 | heightOnly=true, heightScale=Value()（百分比比例） | constants_converter.cpp:413-415 | AC-2.7 |
| R-11 | 行为 | lineHeight + lineSpacing 同时设置 | heightScale = lineHeightScale + lineSpacingScale | constants_converter.cpp:705-706 | AC-2.8 |
| R-12 | 边界 | Span lineHeight 参数类型 | Length（span.d.ts:348, @since 10） | Span 窄类型 | AC-2.9 |
| R-13 | 行为 | 调用 SetLineHeightMultiple (API 22+) | LineHeightMultiply 存为 double；行高 = value × fontHeight | 仅 TextAttribute | AC-3.1 |
| R-14 | 边界 | 设置 lineHeightMultiple 同时预设 LineHeight=28px | DEFAULT_LINE_HEIGHT=28px 预设（js_text.cpp:647, style_modifier.cpp:14145-14147） | 副作用 | AC-3.2 |
| R-15 | 边界 | lineHeightMultiple 与 lineHeight 同时设置 | 仅 lineHeightMultiple 生效；Rosen 层 multiply 覆盖 heightScale (constants_converter.cpp:541-543) | 互斥优先级 | AC-3.3 |
| R-16 | 异常 | lineHeightMultiple ≤ 0 | ResetLineHeightMultiply（不设置） | js_text.cpp:634-649 | AC-3.4 |
| R-17 | 边界 | Reset lineHeightMultiple | LineHeight 不恢复原值（28px 预设保留） | js_text.cpp Reset 不还原 | AC-3.5 |
| R-18 | 行为 | 调用 SetMinimumLineHeight (API 22+) | MinimumLineHeight 存为 Dimension；txtStyle.minLineHeight 下传 Rosen | 仅 TextAttribute | AC-4.1 |
| R-19 | 行为 | 调用 SetMaximumLineHeight | MaximumLineHeight 存为 Dimension；txtStyle.maxLineHeight 下传 Rosen | 仅 TextAttribute | AC-4.2 |
| R-20 | 边界 | maxLineHeight < minLineHeight | max 被 clamp 上调到 min（constants_converter.cpp:529） | min 优先 | AC-4.3 |
| R-21 | 异常 | min/max ≤ 0 | 不设置（回退默认） | js_text.cpp:651-681 | AC-4.4 |
| R-22 | 边界 | min/max 不支持百分比 | 参数类型 LengthMetrics；百分比不支持 | text.d.ts:327-328 | AC-4.5 |
| R-23 | 行为 | 调用 SetBaselineOffset | BaselineOffset 存为 Dimension；正数内容上移，负数下移 | 负值允许 | AC-5.1, AC-5.2 |
| R-24 | 行为 | baselineOffset 为 Resource (API 20+) | ResourceStr 类型解析（仅动态；静态不支持） | param-level @since 20 | AC-5.3 |
| R-25 | 边界 | baselineOffset 百分比 | 按默认显示行为处理 | text.d.ts:647-649 | AC-5.4 |
| R-26 | 行为 | 渲染转换期 baselineOffset | txtStyle.baseLineShift = -ConvertToPxDistributeWithEnv(...)（取负） | constants_converter.cpp:655-657 | AC-5.5 |
| R-27 | 行为 | baselineOffset 高度扩展 | ace_engine 把 fabs(baselineOffset) 加到测量高度（text_layout_algorithm.cpp:230），不改变段落内在高度 | 布局层补偿 | AC-5.6 |
| R-28 | 边界 | Span baselineOffset 参数类型 | LengthMetrics（BaseSpan<T>, span.d.ts:99, @since 12）；百分比拒绝 | js_span.cpp:386-405 | AC-5.7, AC-5.8 |
| R-29 | 行为 | C-API NODE_TEXT_LETTER_SPACING | value[0].f32 (fp)；支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA | style_modifier.cpp:13630 | AC-6.1 |
| R-30 | 行为 | C-API NODE_TEXT_LINE_HEIGHT | value[0].f32 (fp)；支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA | style_modifier.cpp:13443 | AC-6.2 |
| R-31 | 行为 | C-API NODE_TEXT_BASELINE_OFFSET | value[0].f32 (fp)；支持 TEXT；SPAN 用 NODE_SPAN_BASELINE_OFFSET | style_modifier.cpp:9868 | AC-6.3 |
| R-32 | 行为 | C-API NODE_TEXT_MIN/MAX_LINE_HEIGHT/LINE_HEIGHT_MULTIPLE (@since 22) | value[0].f32；**仅 TEXT**；lineHeightMultiple 同时预设 LineHeight=28px | style_modifier.cpp:14133,14197,14215 | AC-6.4~6.6 |
| R-33 | 行为 | C-API NODE_SPAN_BASELINE_OFFSET | value[0].f32 (fp)；仅 SPAN | style_modifier.cpp:9868 (Span 分支) | AC-6.7 |
| R-34 | 行为 | C-API NODE_IMAGE_SPAN_BASELINE_OFFSET | value[0].f32 (fp)；仅 IMAGE_SPAN | style_modifier.cpp:15265 | AC-6.8 |
| R-35 | 行为 | C-API NODE_TEXT_INPUT/AREA_LETTER_SPACING (@since 16) | value[0].f32 (fp) | style_modifier.cpp 分发 | AC-6.9, AC-6.11 |
| R-36 | 边界 | C-API NODE_TEXT_INPUT/AREA_LINE_HEIGHT (@since 20) 用 i32 | value[0].i32（非 f32）；内部 cast 到 f32 调同一 modifier | 编码不一致 | AC-6.10, AC-6.12 |
| R-37 | 异常 | C-API min/max/multiple 负值 | 仍调用 setter（传 0）但返回 PARAM_INVALID (401) | style_modifier.cpp:14140,14205,14223 | AC-6.13 |
| R-38 | 边界 | C-API SPAN 不支持 min/max/multiple | SPAN_ATTRIBUTES_MAP 不含 min/max/multiple；调用 no-op | style_modifier.cpp:193-211 | AC-6.14 |
| R-39 | 边界 | C-API SetBaseLineOffset 非节点严格 | else 分支对非 Span 节点调 getTextModifier()->setTextBaselineOffset；TextInput/TextArea 可能静默 no-op | style_modifier.cpp:9876-9882 | AC-6.15 |
| R-40 | 边界 | ResetLetterSpacing TextArea 缺 break | ARKUI_NODE_TEXT_AREA case 后无 break 落入 default（功能正常但潜在 bug） | style_modifier.cpp:16429-16433 | — |
| R-41 | 行为 | styled-string OH_ArkUI_LetterSpacingStyle (@since 24) | 创建/设置 letterSpacing 字段 | span_style_native_impl.cpp:1932 | AC-7.1, AC-7.2 |
| R-42 | 行为 | styled-string OH_ArkUI_LineHeightStyle (@since 24) | 创建含 lineHeight + optional lineHeightMultiple；SetLineHeight 设置 lineHeight | span_style_native_impl.cpp:1960 | AC-7.3, AC-7.4 |
| R-43 | 行为 | styled-string OH_ArkUI_LineHeightStyle_SetLineHeightMultiple (@since 26) | 设置 optional lineHeightMultiple | span_style_native_impl.cpp:1977 | AC-7.5 |
| R-44 | 异常 | styled-string GetLineHeightMultiple 未设置 | 返回 0.0f（optional 未 has_value） | span_style_native_impl.cpp:1985-1993 | AC-7.6 |
| R-45 | 行为 | styled-string OH_ArkUI_BaselineOffsetStyle (@since 24) | 创建/设置 baselineOffset 字段 | span_style_native_impl.cpp:1904 | AC-7.7 |
| R-46 | 行为 | styled-string OH_ArkUI_SpanStyle_Set*Style | 拷贝字段并设 styledKey | span_style_native_impl.cpp:1018-1067 | AC-7.8 |
| R-47 | 边界 | styled-string GetLineHeightStyle 不拷出 multiple | 仅拷出 lineHeight，不拷出 lineHeightMultiple（缺口） | span_style_native_impl.cpp:1069-1077 | AC-7.9 |
| R-48 | 边界 | styled-string lineHeightMultiple 负值 | ConvertToOriginLineHeightStyle 静默丢弃（不设置 optional） | span_style_native_impl.cpp:255 | AC-7.10 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~1.8 | 单测 | letterSpacing 各类型解析与逐组件路径 |
| VM-2 | R-6~R-12, AC-2.1~2.9 | 单测 | lineHeight heightScale 计算与负值处理 |
| VM-3 | R-13~R-17, AC-3.1~3.7 | 单测 | lineHeightMultiple 28px 预设与 Rosen 覆盖 |
| VM-4 | R-18~R-22, AC-4.1~4.7 | 单测 | min/max clamp 与百分比不支持 |
| VM-5 | R-23~R-28, AC-5.1~5.10 | 单测 | baselineOffset 取负 + 高度扩展 |
| VM-6 | R-29~R-40, AC-6.1~6.15 | 单测/native_node_test | C-API 各枚举分发与缺口 |
| VM-7 | R-41~R-48, AC-7.1~7.11 | 单测 | styled-string C-API @since 24/26 |
| VM-8 | 全量 | XTS/集成 | 端到端间距与度量渲染 |

---

## API 变更分析

### 新增 API

**ArkTS 动态 API (TextAttribute)：**

| API 签名 | 开放范围 | @since | 关联 AC |
|----------|---------|--------|---------|
| `letterSpacing(value: number \| ResourceStr)` | Public | 7 (ResourceStr @since 20) | AC-1.* |
| `lineHeight(value: number \| string \| Resource)` | Public | 7 | AC-2.* |
| `lineHeightMultiple(value: number \| undefined)` | Public | 22 | AC-3.* |
| `minLineHeight(value: LengthMetrics \| undefined)` | Public | 22 | AC-4.* |
| `maxLineHeight(value: LengthMetrics \| undefined)` | Public | 22 | AC-4.* |
| `baselineOffset(value: number \| ResourceStr)` | Public | 7 (ResourceStr @since 20) | AC-5.* |

**逐组件适用性矩阵（动态 API）：**

| 组件 | letterSpacing | lineHeight | baselineOffset | lineHeightMultiple | minLineHeight | maxLineHeight |
|------|---------------|------------|----------------|-------------------|---------------|---------------|
| TextAttribute | number\|ResourceStr (@since 7, Resource @since 20) | number\|string\|Resource | number\|ResourceStr (@since 7, Resource @since 20) | number\|undefined (@since 22) | LengthMetrics\|undefined (@since 22) | LengthMetrics\|undefined (@since 22) |
| SpanAttribute | number\|ResourceStr (@since 7, Resource @since 20) | Length (@since 10) | LengthMetrics (@since 12, BaseSpan 继承) | ✗ | ✗ | ✗ |
| ImageSpanAttribute | ✗ | ✗ | LengthMetrics (@since 12, 继承) | ✗ | ✗ | ✗ |
| TextInputAttribute | number\|string\|Resource (@since 12) | number\|string\|Resource (@since 12) | ✗ | ✗ | ✗ | ✗ |
| TextAreaAttribute | number\|string\|Resource (@since 12) | number\|string\|Resource (@since 12) | ✗ | ✗ | ✗ | ✗ |
| SearchAttribute | number\|string\|Resource (@since 12) | number\|string\|Resource (@since 12) | ✗ | ✗ | ✗ | ✗ |
| ButtonAttribute | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**静态 API (TextAttribute, @since 23/24 static)：**

| API | 入参类型 | @since static |
|-----|----------|---------------|
| letterSpacing | double\|string\|undefined（**不含 Resource**） | 23 |
| lineHeight | double\|string\|Resource\|undefined | 23 |
| baselineOffset | double\|string\|undefined（**不含 Resource**） | 23 |
| lineHeightMultiple | double\|undefined | 24 |
| minLineHeight | LengthMetrics\|undefined | 24 |
| maxLineHeight | LengthMetrics\|undefined | 24 |

**C-API (NDK)：**

| 属性枚举 | 值 | 格式 | @since | 支持节点 | 关联 AC |
|----------|-----|------|--------|----------|---------|
| NODE_TEXT_LINE_HEIGHT | 1005 | value[0].f32 (fp) | 12 | TEXT/SPAN/TEXT_INPUT/TEXT_AREA | AC-6.2 |
| NODE_TEXT_LETTER_SPACING | 1008 | value[0].f32 (fp) | 12 | TEXT/SPAN/TEXT_INPUT/TEXT_AREA | AC-6.1 |
| NODE_TEXT_BASELINE_OFFSET | 1014 | value[0].f32 (fp) | 12 | TEXT（SPAN 用 2002） | AC-6.3 |
| NODE_TEXT_MIN_LINE_HEIGHT | 1040 | value[0].f32 | 22 | TEXT | AC-6.4 |
| NODE_TEXT_MAX_LINE_HEIGHT | 1041 | value[0].f32 | 22 | TEXT | AC-6.5 |
| NODE_TEXT_LINE_HEIGHT_MULTIPLE | 1042 | value[0].f32 | 22 | TEXT | AC-6.6 |
| NODE_SPAN_BASELINE_OFFSET | 2002 | value[0].f32 (fp) | 12 | SPAN | AC-6.7 |
| NODE_IMAGE_SPAN_BASELINE_OFFSET | 3003 | value[0].f32 (fp) | 12 | IMAGE_SPAN | AC-6.8 |
| NODE_TEXT_INPUT_LETTER_SPACING | 7032 | value[0].f32 | 16 | TEXT_INPUT | AC-6.9 |
| NODE_TEXT_INPUT_LINE_HEIGHT | 7037 | value[0].**i32** | 20 | TEXT_INPUT | AC-6.10 |
| NODE_TEXT_AREA_LETTER_SPACING | 8023 | value[0].f32 | 16 | TEXT_AREA | AC-6.11 |
| NODE_TEXT_AREA_LINE_HEIGHT | 8031 | value[0].**i32** | 20 | TEXT_AREA | AC-6.12 |

**样式字符串 C-API：**

| 函数 | @since | 关联 AC |
|------|--------|---------|
| OH_ArkUI_LetterSpacingStyle_Create/SetLetterSpacing/GetLetterSpacing | 24 | AC-7.1, AC-7.2 |
| OH_ArkUI_LineHeightStyle_Create/SetLineHeight/GetLineHeight | 24 | AC-7.3, AC-7.4 |
| OH_ArkUI_LineHeightStyle_SetLineHeightMultiple/GetLineHeightMultiple | 26 | AC-7.5, AC-7.6 |
| OH_ArkUI_BaselineOffsetStyle_Create/SetBaselineOffset/GetBaselineOffset | 24 | AC-7.7 |
| OH_ArkUI_SpanStyle_SetLetterSpacingStyle/SetLineHeightStyle/SetBaselineOffsetStyle | 24 | AC-7.8 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无变更/废弃 API | — |

---

## 接口规格

### 接口定义

**letterSpacing**

| 属性 | 值 |
|------|-----|
| 函数签名 | `letterSpacing(value: number \| ResourceStr): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| ResourceStr | 是 | 0 (fp) | 负值允许（压缩）；百分比/0 回退默认；ResourceStr @since 20（仅动态；静态仅 double\|string） |

---

**lineHeight**

| 属性 | 值 |
|------|-----|
| 函数签名 | `lineHeight(value: number \| string \| Resource): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| string \| Resource | 是 | 0 (不受限) | 负值 Reset；≤0 不受限；百分比按比例；≈fontSize 不覆盖 |

---

**lineHeightMultiple (API 22+)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `lineHeightMultiple(value: number \| undefined): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| undefined | 是 | 0 (默认行高) | ≤0 Reset；同时预设 LineHeight=28px；与 lineHeight 互斥（multiple 优先） |

---

**minLineHeight / maxLineHeight (API 22+)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `minLineHeight(value: LengthMetrics \| undefined)` / `maxLineHeight(value: LengthMetrics \| undefined)` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | LengthMetrics \| undefined | 是 | 0 | ≤0 不设置；不支持百分比；max < min 时 max clamp 到 min |

---

**baselineOffset**

| 属性 | 值 |
|------|-----|
| 函数签名 | `baselineOffset(value: number \| ResourceStr): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1~5.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| ResourceStr | 是 | 0 | 正数上移，负数下移；百分比按默认显示；ResourceStr @since 20（仅动态；静态仅 double\|string） |

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 20**: letterSpacing/baselineOffset param 增加 ResourceStr 类型（仅动态 API；静态 API 不含 Resource 重载）
  - **API 22**: 新增 minLineHeight/maxLineHeight/lineHeightMultiple（Text 独有，动态）；C-API NODE_TEXT_MIN/MAX_LINE_HEIGHT/LINE_HEIGHT_MULTIPLE
  - **API 24**: 静态范式 min/max/multiple（@since 24 static）；styled-string C-API OH_ArkUI_LetterSpacingStyle/LineHeightStyle/BaselineOffsetStyle
  - **API 26**: styled-string OH_ArkUI_LineHeightStyle_SetLineHeightMultiple
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（ArkTS letterSpacing/lineHeight/baselineOffset）；API 12（C-API NODE_TEXT_*）；API 16（C-API TEXT_INPUT/AREA_LETTER_SPACING）；API 20（C-API TEXT_INPUT/AREA_LINE_HEIGHT, i32 编码）；API 22（min/max/multiple + C-API）；API 24（静态 min/max/multiple + styled-string）；API 26（styled-string lineHeightMultiple）
- **API 版本号策略:** @since 7 基础；@since 16/20/22/24/26 标注新增；param-level @since 20 标注 ResourceStr（动态专属）

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| min/max/multiple 是公开 API（非内部） | TextAttribute 独有，@since 22 dyn / @since 24 static；区别于 lineThicknessScale 内部 | AC-3.6, AC-4.7 |
| lineHeightMultiple 覆盖 lineHeight | 设置 multiple 预设 LineHeight=28px + Rosen 层 multiply 覆盖 heightScale | AC-3.2, AC-3.3 |
| maxLineHeight clamp 到 min | max < min 时 max 上调到 min | AC-4.3 |
| baselineOffset 取负 + 高度扩展 | Rosen baseLineShift 取负；ace 加 fabs 到测量高度 | AC-5.5, AC-5.6 |
| param @since 20 仅动态有 Resource | 静态 letterSpacing/baselineOffset 不含 Resource 重载 | AC-1.4, AC-5.3 |
| C-API i32 vs f32 不一致 | NODE_TEXT_INPUT/AREA_LINE_HEIGHT 用 i32；NODE_TEXT_LINE_HEIGHT 用 f32 | AC-6.10, AC-6.12 |
| C-API 节点支持与 bug | SetBaseLineOffset 非节点严格；Span 重用 TEXT 枚举；ResetLetterSpacing TextArea 缺 break | AC-6.14, AC-6.15 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 间距/度量设置 + 标记脏 < 1μs；同帧多字段仅触发一次段落重建 | benchmark | — |
| 内存 | Dimension 使用 std::optional；LineHeightMultiply 用 std::optional<double> | hidumper | — |
| 可靠性 | lineHeightMultiple 预设 28px 副作用须文档化；负值统一处理 | 集成测试 | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 间距/度量影响可读性但无障碍语义由组件提供 | — |
| 大字体 | 是 | letterSpacing/lineHeight 用 fp/vp 随系统字体缩放；baselineOffset 同 | AC-1.1, AC-2.1, AC-5.1 |
| 深色模式 | 否 | 间距/度量与颜色无关 | — |
| 多窗口/分屏 | 否 | 不直接受窗口尺寸影响 | — |
| 多用户 | 否 | 无用户态差异 | — |
| 版本升级 | 是 | API 16/20/22/24/26 版本差异须通过 API 版本守护 | AC-1.4, AC-3.1, AC-4.1, AC-6.9, AC-7.1, AC-7.5 |
| 生态兼容 | 是 | C-API 多通道（值数组/styled-string）应与 ArkTS 一致 | AC-6.*, AC-7.* |

---

## 行为场景

```gherkin
Feature: 文本间距与度量
  作为 应用开发者
  我想要 通过声明式 API 与 C-API 控制文本字间距、行高、行高范围与基线偏移
  以便 实现精确的文本排版

  # ─── letterSpacing ───────────────────────────────

  Scenario: 设置正字间距
    Given 一个 Text 组件
    When 调用 .letterSpacing(2)
    Then 每字符间距增加 2fp

  Scenario: 设置负字间距（压缩）
    Given 一个 Text 组件
    When 调用 .letterSpacing(-1)
    Then 字符间距压缩 1fp

  # ─── lineHeight ──────────────────────────────────

  Scenario: 设置绝对行高
    Given 一个 Text 组件 fontSize=16
    When 调用 .lineHeight(30)
    Then heightScale = 30/16 = 1.875
    And heightOnly=true

  Scenario: lineHeight 负值重置
    Given 一个 Text 组件
    When 调用 .lineHeight(-10)
    Then JS bridge value.Reset()，行高不受限

  Scenario Outline: lineHeight 与 fontSize 关系
    Given 一个 Text 组件 fontSize=<fs>
    When 调用 .lineHeight(<lh>)
    Then heightOnly=<ho>, heightScale=<hs>

    Examples:
      | fs | lh | ho | hs |
      | 16 | 30 | true | 1.875 |
      | 16 | 16 | false | 1.0 |
      | 16 | 0 | false | 1.0 |

  # ─── lineHeightMultiple ──────────────────────────

  Scenario: 设置行高倍数 (API 22+)
    Given 目标 API 版本 >= 22
    And 一个 Text 组件
    When 调用 .lineHeightMultiple(1.5)
    Then LineHeightMultiply=1.5
    And LineHeight 预设为 28px（DEFAULT_LINE_HEIGHT）
    And Rosen 层 heightScale=1.5 覆盖 28px 派生值

  Scenario: lineHeightMultiple 与 lineHeight 同时设置
    Given 一个 Text 组件
    When 调用 .lineHeight(40).lineHeightMultiple(1.5)
    Then 仅 lineHeightMultiple 生效
    And LineHeight 被预设为 28px（覆盖 40）

  Scenario: lineHeightMultiple ≤ 0
    Given 一个 Text 组件
    When 调用 .lineHeightMultiple(0)
    Then ResetLineHeightMultiply（不设置）

  # ─── min/maxLineHeight ───────────────────────────

  Scenario: 设置行高范围
    Given 目标 API 版本 >= 22
    And 一个 Text 组件
    When 调用 .minLineHeight(20).maxLineHeight(50)
    Then 每行高度 clamp 到 [20, 50]

  Scenario: maxLineHeight < minLineHeight
    Given 一个 Text 组件
    When 调用 .minLineHeight(50).maxLineHeight(20)
    Then max 被 clamp 上调到 50（= min）

  Scenario: min/max 不支持百分比
    Given 一个 Text 组件
    When 尝试 .minLineHeight('50%')
    Then 参数类型 LengthMetrics 不支持百分比

  # ─── baselineOffset ─────────────────────────────

  Scenario: 设置正基线偏移（上移）
    Given 一个 Text 组件
    When 调用 .baselineOffset(10)
    Then BaselineOffset=10fp，内容上移
    And Rosen baseLineShift = -10（取负）

  Scenario: 设置负基线偏移（下移）
    Given 一个 Text 组件
    When 调用 .baselineOffset(-5)
    Then 内容下移
    And 测量高度 += fabs(-5) = 5

  Scenario: Span baselineOffset 百分比拒绝
    Given 一个 Span 组件
    When 尝试 .baselineOffset('50%')
    Then DimensionUnit::PERCENT 被拒绝，回退 Reset

  # ─── C-API ──────────────────────────────────────

  Scenario: C-API 设置 letterSpacing
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_TEXT_LETTER_SPACING, {value[0].f32: 2.0})
    Then letterSpacing=2fp

  Scenario: C-API TEXT_INPUT lineHeight i32 编码
    Given 一个 ARKUI_NODE_TEXT_INPUT 节点
    When 调用 setAttribute(node, NODE_TEXT_INPUT_LINE_HEIGHT, {value[0].i32: 30})
    Then 内部 cast 到 f32，调 textInputModifier.setTextInputLineHeight
    # 注意：与 NODE_TEXT_LINE_HEIGHT (f32) 编码不同

  Scenario: C-API lineHeightMultiple 预设 28px
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_TEXT_LINE_HEIGHT_MULTIPLE, {value[0].f32: 1.5})
    Then 同时预设 LineHeight=28px（DEFAULT_LINE_HEIGHT, UNIT_PX）
    And 设置 LineHeightMultiply=1.5

  Scenario: C-API SPAN 不支持 min/max/multiple
    Given 一个 ARKUI_NODE_SPAN 节点
    When 调用 setAttribute(span, NODE_TEXT_MIN_LINE_HEIGHT, ...)
    Then SPAN_ATTRIBUTES_MAP 不含，no-op

  # ─── styled-string C-API ────────────────────────

  Scenario: 样式字符串设置 lineHeight + multiple
    Given 一个 OH_ArkUI_LineHeightStyle 对象
    When 调用 OH_ArkUI_LineHeightStyle_SetLineHeight(style, 30.0f)
    And 调用 OH_ArkUI_LineHeightStyle_SetLineHeightMultiple(style, 1.5f) (@since 26)
    Then lineHeight=30, lineHeightMultiple=1.5（optional）

  Scenario: 样式字符串 lineHeightMultiple 负值静默丢弃
    Given 一个 OH_ArkUI_LineHeightStyle 设置 lineHeightMultiple=-1.0
    When ConvertToOriginLineHeightStyle 执行
    Then 负值静默丢弃，optional 不设置

  Scenario: 样式字符串 GetLineHeightStyle 不返回 multiple
    Given 一个 OH_ArkUI_SpanStyle 已 SetLineHeightStyle
    When 调用 OH_ArkUI_SpanStyle_GetLineHeightStyle
    Then 仅返回 lineHeight，不返回 lineHeightMultiple（缺口）
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（覆盖 letterSpacing/lineHeight/minLineHeight/maxLineHeight/lineHeightMultiple/baselineOffset；不含 fontSize/fontColor/fontWeight/fontStyle/fontFamily（Feat-01）、decoration/textCase/lineThicknessScale（Feat-02）、textShadow/fontFeature/fontVariations（Feat-04）、minFontSize/maxFontSize/minFontScale/maxFontScale（Feat-05））
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TextLayoutProperty TextLineStyle LetterSpacing LineHeight BaselineOffset LineHeightMultiply MinimumLineHeight MaximumLineHeight"
  - repo: "openharmony/ace_engine"
    query: "constants_converter ConvertSpacingAndHeigh CheckMinMaxLineHeight heightScale lineHeightMultiply override"
  - repo: "openharmony/ace_engine"
    query: "text_layout_algorithm baselineOffset fabs height Final SetContentHeight"
  - repo: "openharmony/ace_engine"
    query: "style_modifier.cpp SetLetterSpacing SetLineHeight SetBaseLineOffset SetMinLineHeight SetMaxLineHeight SetLineHeightMultiple"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_LetterSpacingStyle OH_ArkUI_LineHeightStyle OH_ArkUI_BaselineOffsetStyle span_style_native_impl"
```

**关键文档：**
- 架构设计：`specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md`
- SDK 类型定义：`interface/sdk-js/api/@internal/component/ets/text.d.ts`、`units.d.ts`
- C-API：`interfaces/native/native_node.h`、`interfaces/native/native_styled_string_descriptor.h`
