# 特性规格

> Func-05-09-05-Feat-02 字体与文本样式：固化 fontColor/fontSize/fontStyle/fontWeight/fontFamily、placeholderColor/placeholderFont、letterSpacing/lineHeight/lineSpacing、fontFeature/decoration/textIndent、halfLeading/includeFontPadding/fallbackLineSpacing/enableAutoSpacing、strokeWidth/strokeColor/strokeJoinStyle/shaderStyle、attributeModifier 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 字体与文本样式 (Font & Text Styles) |
| 特性编号 | Func-05-09-05-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态版 @since 7（fontColor/fontSize/fontStyle/fontWeight/fontFamily/placeholderColor/placeholderFont）、@since 12（letterSpacing/lineHeight/lineSpacing/fontFeature/decoration/textIndent）、@since 18（halfLeading）、@since 23 static（含 includeFontPadding/fallbackLineSpacing/selectedDragPreviewStyle）、@since 24 static（strokeWidth/strokeColor/enableAutoSpacing）、@since 26.0.0 static（strokeJoinStyle/shaderStyle） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐。所有字体/文本样式属性复用 TextFieldLayoutProperty/TextFieldPaintProperty，通过 TextFieldModelNG/Static 设置，经 constants_converter/txt_paragraph 转换到 Rosen 排版引擎。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 字体核心五属性（fontColor/fontSize/fontStyle/fontWeight/fontFamily） | FontStyle 组，PROPERTY_UPDATE_MEASURE/MEASURE_SELF |
| ADDED | 占位文本样式（placeholderColor/placeholderFont） | PlaceholderFontStyle 组；placeholderColor 双存储（paint flag + layout color） |
| ADDED | 间距与行高（letterSpacing/lineHeight/lineSpacing） | TextLineStyle 组，负值/百分比特殊处理 |
| ADDED | 装饰与特性（fontFeature/decoration/textIndent） | decoration 拆为四属性；fontFeature 字符串解析 |
| ADDED | 排版辅助（halfLeading/includeFontPadding/fallbackLineSpacing/enableAutoSpacing） | bool 属性，透传 Rosen |
| ADDED | 描边与着色（strokeWidth/strokeColor/strokeJoinStyle/shaderStyle） | 负 strokeWidth 切换为 fill-brush；shader 互斥 |
| ADDED | attributeModifier（TextAreaModifier） | ArkTS 修饰器链式应用 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/05-text-area/design.md` | Baselined |

---

## 用户故事

### US-1: 设置字体核心属性

**作为** 应用开发者,
**我想要** 通过 fontColor/fontSize/fontStyle/fontWeight/fontFamily 控制文本字体,
**以便** 自定义文本视觉。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.fontColor(value)` 且 value 为合法 ResourceColor THEN 文本以指定颜色渲染，写入 LayoutProperty TextColor（PROPERTY_UPDATE_MEASURE_SELF）+ RenderContext ForegroundColor + paint flag ForegroundColorFlag（`text_field_model_ng.cpp:556-562`） | 正常 |
| AC-1.2 | WHEN 未设置 fontColor THEN 使用主题默认 textColor_（`textfield_theme.h:119`；token FontPrimary）；禁用态用 disableTextColor_ | 异常 |
| AC-1.3 | WHEN 调用 `.fontSize(value)` 且 value 为正数（number/string/Resource） THEN 以 value（单位 fp）渲染，写 LayoutProperty FontSize（PROPERTY_UPDATE_MEASURE）+ PreferredTextLineHeightNeedToUpdate=true（`text_field_model_ng.cpp:545-549`） | 正常 |
| AC-1.4 | WHEN fontSize 为百分比 THEN ValidateNonPercent 拒绝，不生效 | 异常 |
| AC-1.5 | WHEN fontSize 为负数 THEN ValidateNonNegative 拒绝，不生效 | 异常 |
| AC-1.6 | WHEN 调用 `.fontStyle(FontStyle.Italic)` THEN 文本斜体渲染，写 ItalicFontStyle（`text_field_model_ng.cpp:576-579`） | 正常 |
| AC-1.7 | WHEN 调用 `.fontWeight(value)` 且 value 为 100~900 number / FontWeight 枚举 / 合法字符串 THEN 按对应字重渲染（`text_field_model_ng.cpp:551-554`） | 正常 |
| AC-1.8 | WHEN 未设置 fontWeight THEN 默认 FontWeight.Normal（`textfield_theme.h:1018`） | 异常 |
| AC-1.9 | WHEN 调用 `.fontFamily(value)` 且 value 为有效字族 THEN 使用指定字族；卡片场景仅 HarmonyOS Sans 生效（`text_field_model_ng.cpp:581-584`） | 正常 |
| AC-1.10 | WHEN 未设置 fontFamily THEN 默认 sans-serif（`text_field_layout_algorithm.cpp:834`） | 异常 |

### US-2: 设置占位文本样式

**作为** 应用开发者,
**我想要** 通过 placeholderColor/placeholderFont 自定义占位文本,
**以便** 区分占位与输入态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.placeholderColor(value)` THEN 写 LayoutProperty PlaceholderTextColor + paint bool PlaceholderColorFlagByUser=true（`text_field_model_ng.cpp:387-390`） | 正常 |
| AC-2.2 | WHEN 未设置 placeholderColor THEN 使用主题 placeholderColor_（`textfield_theme.h:121`；token FontSecondary）（`text_field_layout_algorithm.cpp:876-887`） | 异常 |
| AC-2.3 | WHEN 调用 `.placeholderFont({ size, weight, family, style })` THEN 仅设置 has_value 字段，未指定字段保持原值/默认（`text_field_model_ng.cpp:1727-1747`） | 正常 |
| AC-2.4 | WHEN 未设置 placeholderFont 各字段 THEN 默认回退到主文本 fontSize/fontWeight（`text_field_layout_algorithm.cpp:946-950`） | 异常 |
| AC-2.5 | WHEN 禁用态 THEN placeholderColor 经 BlendOpacity(DisableOpacityRatio) 调暗（`text_field_layout_algorithm.cpp:878`） | 边界 |

### US-3: 设置间距与行高

**作为** 应用开发者,
**我想要** 通过 letterSpacing/lineHeight/lineSpacing 控制字间距与行高,
**以便** 精细排版。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.letterSpacing(value)` THEN 写 LetterSpacing（PROPERTY_UPDATE_MEASURE），经 NormalizeToPx 传入 Rosen textStyle.letterSpacing（`text_field_model_ng.cpp:1113`；`drawing_prop_convertor.cpp:270`） | 正常 |
| AC-3.2 | WHEN 调用 `.lineHeight(value)` 且 value 为正数 THEN lineHeightScale=lineHeight/fontSize（`constants_converter.cpp:467-488`）；负值跳过不生效（`text_field_pattern.cpp:6785`） | 正常 |
| AC-3.3 | WHEN 调用 `.lineSpacing(value, options)` THEN 写 LineSpacing + IsOnlyBetweenLines；百分比→lineSpacingScale=Value()，否则 lineSpacingScale=lineSpacing/fontSize（`constants_converter.cpp:490-510`） | 正常 |
| AC-3.4 | WHEN lineSpacing options.isOnlyBetweenLines=true THEN txt_paragraph 设 textHeightBehavior=DISABLE_LAST_ASCENT/DISABLE_ALL（`txt_paragraph.cpp:100`） | 正常 |
| AC-3.5 | WHEN letterSpacing/lineSpacing 为百分比 THEN ValidateNonPercent 拒绝 letterSpacing；lineSpacing 百分比按比例处理 | 边界 |

### US-4: 设置 OpenType 特性与装饰

**作为** 应用开发者,
**我想要** 通过 fontFeature/decoration/textIndent 启用高级排版,
**以便** 连字/装饰线/缩进。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.fontFeature("ss01 on, liga off")` THEN 字符串经 ParseFontFeatureSettings 解析为 FONT_FEATURES_LIST，写 FontFeature（`text_style_parser.cpp:341-354`；`text_field_model_ng.cpp:189-191`） | 正常 |
| AC-4.2 | WHEN 调用 `.fontFeature("normal")` 或空串 THEN 解析返回空列表，使用字体默认特性 | 异常 |
| AC-4.3 | WHEN 调用 `.decoration({ type, color, style })` THEN 拆写 TextDecoration/TextDecorationColor/TextDecorationStyle/LineThicknessScale 四属性（`text_field_model_ng.cpp:1158-1173`） | 正常 |
| AC-4.4 | WHEN 未设置 decoration THEN 默认 { type: None, color: Black, style: SOLID } | 异常 |
| AC-4.5 | WHEN lineThicknessScale 为负数 THEN 钳为 DEFAULT_LINE_THICKNESS_SCALE（`text_field_model_static.cpp:691`） | 边界 |
| AC-4.6 | WHEN 禁用态 THEN decorationColor 经 BlendOpacity(TEXT_DECORATION_DISABLED_COLOR_ALPHA) 调暗（`text_field_layout_algorithm.cpp:1553-1554`） | 边界 |
| AC-4.7 | WHEN 调用 `.textIndent(value)` THEN 写 TextIndent（PROPERTY_UPDATE_MEASURE），传给 textStyle（`text_field_model_ng.cpp:1289-1292`） | 正常 |

### US-5: 设置排版辅助属性

**作为** 应用开发者,
**我想要** 通过 halfLeading/includeFontPadding/fallbackLineSpacing/enableAutoSpacing 控制排版细节,
**以便** 防止行重叠/中英文间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.halfLeading(true)` THEN 写 HalfLeading，未设则回退 pipeline->GetHalfLeading()（`text_field_layout_algorithm.cpp:1525`；`txt_paragraph.cpp:89`） | 正常 |
| AC-5.2 | WHEN 调用 `.includeFontPadding(true)` THEN 写 IncludeFontPadding，默认 false，传 Rosen includeFontPadding（`txt_paragraph.cpp:97`） | 正常 |
| AC-5.3 | WHEN 调用 `.fallbackLineSpacing(true)` THEN 写 FallbackLineSpacing，默认 false，传 Rosen fallbackLineSpacing（`txt_paragraph.cpp:98`） | 正常 |
| AC-5.4 | WHEN 调用 `.enableAutoSpacing(true)` THEN 写 EnableAutoSpacing，默认 false，传 Rosen enableAutoSpace（`txt_paragraph.cpp:96`） | 正常 |

### US-6: 设置描边与着色

**作为** 应用开发者,
**我想要** 通过 strokeWidth/strokeColor/strokeJoinStyle/shaderStyle 实现描边/渐变,
**以便** 文本视觉效果增强。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.strokeWidth(value)` 且 value>0 THEN 构造 RSPen，width=abs(ConvertToPx)，color=strokeColor，设 foregroundPen（`constants_converter.cpp:671-680`） | 正常 |
| AC-6.2 | WHEN strokeWidth 为负数 THEN 切换为 RSBrush fill 模式，使用 textColor 着色（`constants_converter.cpp:682-686`） | 边界 |
| AC-6.3 | WHEN strokeWidth=0（DEFAULT_STROKE_WIDTH） THEN 不构造 pen/brush | 边界 |
| AC-6.4 | WHEN 调用 `.strokeColor(value)` THEN 设 StrokeColor，pen 用此色；未设则回退 textColor（`text_field_layout_algorithm.cpp:852`） | 正常 |
| AC-6.5 | WHEN 调用 `.strokeJoinStyle(value)` THEN 设 StrokeJoinStyle，默认 MITER_JOIN，pen.SetJoinStyle（`constants_converter.cpp:583-595`） | 正常 |
| AC-6.6 | WHEN 调用 `.shaderStyle(linearGradient)` THEN 设 GradientShaderStyle 并 reset ColorShaderStyle（互斥）；构造渐变 brush（`text_field_model_ng.cpp:3074-3094`） | 正常 |
| AC-6.7 | WHEN 调用 `.shaderStyle(color)` THEN 设 ColorShaderStyle 并 reset GradientShaderStyle（互斥）；仅当 strokeWidth=0 时构造 color shader brush（`constants_converter.cpp:687-692`） | 正常 |
| AC-6.8 | WHEN 同时设 gradient 与 color shader THEN 后设的 reset 先设的（互斥）（`text_field_model_ng.cpp:3088/3093/3099`） | 边界 |

### US-7: 使用 attributeModifier

**作为** 应用开发者,
**我想要** 通过 attributeModifier 链式应用多个样式属性,
**以便** 动态/可复用样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.attributeModifier(modifier)` 且 modifier 实现 AttributeModifier<TextAreaAttribute> THEN applyNormalAttribute 调用 ModifierUtils.applyAndMergeModifier 回放 ModifierMap（`text_area_modifier.ts:491-494`） | 正常 |
| AC-7.2 | WHEN modifier 中某属性未设置 THEN 该属性保持原值（不 reset） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.10 | R-1~R-4 | TASK-02 | XTS 字体属性渲染 | text_field_model_ng.cpp:545-584 |
| AC-2.1~2.5 | R-5~R-7 | TASK-02 | XTS 占位样式 | text_field_model_ng.cpp:387-390 |
| AC-3.1~3.5 | R-8~R-10 | TASK-02 | XTS 间距行高 | constants_converter.cpp:467-510 |
| AC-4.1~4.7 | R-11~R-14 | TASK-02 | XTS fontFeature/decoration/textIndent | text_style_parser.cpp:341 |
| AC-5.1~5.4 | R-15~R-18 | TASK-02 | XTS 排版辅助 | txt_paragraph.cpp:89-109 |
| AC-6.1~6.8 | R-19~R-22 | TASK-02 | XTS 描边着色 | constants_converter.cpp:671-693 |
| AC-7.1~7.2 | R-23~R-24 | TASK-02 | 集成测试 modifier | text_area_modifier.ts:491 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 fontColor | 写 TextColor+ForegroundColor+flag | 主题默认 FontPrimary | AC-1.1,1.2 |
| R-2 | 行为 | 设置 fontSize | 写 FontSize+PreferredTextLineHeightNeedToUpdate | 负数/百分比拒绝；默认 16fp | AC-1.3,1.4,1.5 |
| R-3 | 行为 | 设置 fontStyle | 写 ItalicFontStyle | 默认 Normal | AC-1.6 |
| R-4 | 行为 | 设置 fontWeight/fontFamily | 写 FontWeight/FontFamily | 默认 Normal/sans-serif | AC-1.7,1.8,1.9,1.10 |
| R-5 | 行为 | 设置 placeholderColor | 写 PlaceholderTextColor+PlaceholderColorFlagByUser | 主题默认 FontSecondary | AC-2.1,2.2 |
| R-6 | 行为 | 设置 placeholderFont | 仅设 has_value 字段 | 未设字段回退主文本 | AC-2.3,2.4 |
| R-7 | 边界 | 禁用态 placeholderColor | BlendOpacity(DisableOpacityRatio) | — | AC-2.5 |
| R-8 | 行为 | 设置 letterSpacing | 写 LetterSpacing，NormalizeToPx 传 Rosen | 百分比拒绝 | AC-3.1,3.5 |
| R-9 | 行为 | 设置 lineHeight(正) | lineHeightScale=lineHeight/fontSize | 负值跳过 | AC-3.2 |
| R-10 | 行为 | 设置 lineSpacing | 写 LineSpacing+IsOnlyBetweenLines；百分比按比例 | — | AC-3.3,3.4 |
| R-11 | 行为 | 设置 fontFeature | ParseFontFeatureSettings 解析为列表 | "normal"=空列表 | AC-4.1,4.2 |
| R-12 | 行为 | 设置 decoration | 拆写四属性 | 默认 None/Black/SOLID | AC-4.3,4.4 |
| R-13 | 边界 | lineThicknessScale 负 | 钳为 DEFAULT_LINE_THICKNESS_SCALE | — | AC-4.5 |
| R-14 | 边界 | 禁用态 decorationColor | BlendOpacity 调暗 | — | AC-4.6 |
| R-15 | 行为 | 设置 halfLeading | 写 HalfLeading；未设回退 pipeline 默认 | 默认 false(pipeline) | AC-5.1 |
| R-16 | 行为 | 设置 includeFontPadding | 写 IncludeFontPadding | 默认 false | AC-5.2 |
| R-17 | 行为 | 设置 fallbackLineSpacing | 写 FallbackLineSpacing | 默认 false | AC-5.3 |
| R-18 | 行为 | 设置 enableAutoSpacing | 写 EnableAutoSpacing | 默认 false | AC-5.4 |
| R-19 | 行为 | strokeWidth>0 | RSPen，width=abs(px)，color=strokeColor | — | AC-6.1 |
| R-20 | 边界 | strokeWidth<0 | 切换 RSBrush fill 模式 | 用 textColor | AC-6.2 |
| R-21 | 边界 | strokeWidth=0 | 不构造 pen/brush | DEFAULT_STROKE_WIDTH=0 | AC-6.3 |
| R-22 | 行为 | 设置 shaderStyle | gradient/color 互斥；后设 reset 先设 | color shader 仅 strokeWidth=0 时生效 | AC-6.6,6.7,6.8 |
| R-23 | 行为 | 设置 strokeColor/strokeJoinStyle | 设对应属性；未设回退 textColor/MITER_JOIN | — | AC-6.4,6.5 |
| R-24 | 行为 | 设置 attributeModifier | applyAndMergeModifier 回放 ModifierMap | 未设属性保持原值 | AC-7.1,7.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.1~1.10 字体五属性 | XTS 渲染 + Inspector | TextColor/FontSize 等值正确 |
| VM-2 | AC-2.1~2.5 占位样式 | XTS + Inspector | PlaceholderTextColor/FlagByUser |
| VM-3 | AC-3.1~3.5 间距行高 | XTS + 布局测量 | lineHeightScale/lineSpacingScale 正确 |
| VM-4 | AC-4.1~4.7 特性装饰 | XTS + Rosen 验证 | fontFeature 列表；decoration 四属性 |
| VM-5 | AC-5.1~5.4 排版辅助 | XTS + Rosen 验证 | halfLeading/includeFontPadding 透传 |
| VM-6 | AC-6.1~6.8 描边着色 | XTS + RS 验证 | pen/brush 构造；shader 互斥 |
| VM-7 | AC-7.1~7.2 modifier | 集成测试 | ModifierMap 回放 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| fontColor(value) | Public | ResourceColor | this | 无 | 文本颜色 | AC-1.1 |
| fontSize(value) | Public | Length | this | 无 | 文本字号 | AC-1.3 |
| fontStyle(value) | Public | FontStyle | this | 无 | 斜体 | AC-1.6 |
| fontWeight(value) | Public | number/FontWeight/ResourceStr | this | 无 | 字重 | AC-1.7 |
| fontFamily(value) | Public | ResourceStr | this | 无 | 字族 | AC-1.9 |
| placeholderColor(value) | Public | ResourceColor | this | 无 | 占位颜色 | AC-2.1 |
| placeholderFont(value) | Public | Font | this | 无 | 占位字体 | AC-2.3 |
| letterSpacing(value) | Public | number/string/Resource | this | 无 | 字间距 | AC-3.1 |
| lineHeight(value) | Public | number/string/Resource | this | 无 | 行高 | AC-3.2 |
| lineSpacing(value, options?) | Public | LengthMetrics, LineSpacingOptions? | this | 无 | 行间距 | AC-3.3 |
| fontFeature(value) | Public | string | this | 无 | OpenType 特性 | AC-4.1 |
| decoration(value) | Public | TextDecorationOptions | this | 无 | 装饰线 | AC-4.3 |
| textIndent(value) | Public | Dimension | this | 无 | 首行缩进 | AC-4.7 |
| halfLeading(value) | Public | boolean | this | 无 | 半行距 | AC-5.1 |
| includeFontPadding(value) | Public | boolean | this | 无 | 字体 padding | AC-5.2 |
| fallbackLineSpacing(value) | Public | boolean | this | 无 | 回退行距 | AC-5.3 |
| enableAutoSpacing(value) | Public | boolean | this | 无 | 中英文间距 | AC-5.4 |
| strokeWidth(value) | Public | LengthMetrics | this | 无 | 描边宽度 | AC-6.1 |
| strokeColor(value) | Public | ResourceColor | this | 无 | 描边颜色 | AC-6.4 |
| strokeJoinStyle(value) | Public | StrokeJoinStyle | this | 无 | 描边连接 | AC-6.5 |
| shaderStyle(value) | Public | ShaderStyle | this | 无 | 着色器 | AC-6.6 |
| attributeModifier(modifier) | Public | AttributeModifier | this | 无 | 属性修饰器 | AC-7.1 |

> **SDK 交叉验证：** 签名均经 `textArea.static.d.ets`（静态）与 `text_area.d.ts`（动态）核对。动态版 @since 7/12/18/23/24/26 与静态版 @since 23 static/24 static/26.0.0 static 对应。

## 接口规格

> 鉴于 Feat-02 API 数量较多（22 个），接口规格按能力组给出参数约束摘要；详细行为场景见 AC 与规则表。

### 接口定义

| 接口 | 签名概要 | 开放范围 | 关联 AC |
|------|----------|----------|---------|
| font 五属性 | fontColor/fontSize/fontStyle/fontWeight/fontFamily | Public | AC-1.x |
| placeholder 二属性 | placeholderColor/placeholderFont | Public | AC-2.x |
| 间距行高三属性 | letterSpacing/lineHeight/lineSpacing | Public | AC-3.x |
| 特性装饰三属性 | fontFeature/decoration/textIndent | Public | AC-4.x |
| 排版辅助四属性 | halfLeading/includeFontPadding/fallbackLineSpacing/enableAutoSpacing | Public | AC-5.x |
| 描边着色四属性 | strokeWidth/strokeColor/strokeJoinStyle/shaderStyle | Public | AC-6.x |
| attributeModifier | attributeModifier(modifier) | Public | AC-7.x |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| fontSize | Length | 是 | 16fp | 非负、非百分比 |
| letterSpacing | Dimension | 是 | 无 | 非百分比 |
| lineHeight | Dimension | 是 | 无 | 负值跳过 |
| lineSpacing | Dimension | 是 | 0 | 非负 |
| fontFeature | string | 是 | "normal" | "normal"=空列表 |
| decoration.lineThicknessScale | float | 否 | DEFAULT | 负值钳为默认 |
| strokeWidth | Dimension | 是 | 0 | 负值→fill-brush |
| strokeJoinStyle | StrokeJoinStyle | 是 | MITER_JOIN | — |
| shaderStyle | ShaderStyle | 是 | 无 | gradient/color 互斥 |

## 兼容性声明

- **已有 API 行为变更:** 否。字体/样式属性行为在 API 版本间无运行时 guard（均为无条件应用）。strokeWidth 负值切换 fill-brush 是固有行为非版本变更。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 @since 7（核心字体）；静态 @since 23 static
- **API 版本号策略:** 动态保留历史 @since（7/12/18/23/24/26）；静态统一 @since 23 static，新属性按 24 static/26.0.0 static 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| FontStyle 组属性 | 字体五属性均在 FontStyle 组，PROPERTY_UPDATE_MEASURE/MEASURE_SELF | AC-1.x |
| placeholderColor 双存储 | paint bool flag + layout color；paint 的 PlaceholderColor 字段为 inspector-only 从不写入 | AC-2.x |
| PreferredTextLineHeightNeedToUpdate | fontSize/fontStyle/fontWeight/fontFamily 设置后触发行高重算 | AC-1.x |
| decoration 拆四属性 | TextDecorationOptions 在桥层拆为四独立 layout 属性 | AC-4.3 |
| shader 互斥 | gradient/color shader 互斥，后设 reset 先设 | AC-6.6~6.8 |
| strokeWidth 符号语义 | >0=pen stroke；<0=brush fill；=0=无 | AC-6.1~6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 字体属性变更触发 PROPERTY_UPDATE_MEASURE 单帧重布局 | XTS 帧率 | text_field_layout_property.h:218-227 |
| 内存 | fontFeature 列表仅存储非空特性对 | 单测 | text_style_parser.cpp:341 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 字体属性影响无障碍文本渲染 | AC-1.x |
| 大字体 | 是 | fontSize/fontWeight 受系统字体缩放影响（minFontScale/maxFontScale 属 Feat-03） | AC-1.3 |
| 深色模式 | 是 | fontColor/placeholderColor 默认值取主题 token，主题切换时 CaretColorFlagByUser=false 回退主题 | AC-1.2, AC-2.2 |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | halfLeading @since 18；includeFontPadding/fallbackLineSpacing @since 23；strokeWidth/strokeColor @since 24；strokeJoinStyle/shaderStyle @since 26 | AC-5.1,5.2,5.3,6.5,6.6 |
| 生态兼容 | 是 | 卡片场景 fontFamily 仅 HarmonyOS Sans | AC-1.9 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextArea 字体与文本样式
  作为 应用开发者
  我想要 控制文本字体、占位样式、间距行高、装饰描边
  以便 精细排版与视觉增强

  Scenario Outline: strokeWidth 符号决定渲染模式
    Given 已设置 strokeColor
    When 调用 .strokeWidth(<width>)
    Then <预期>

    Examples:
      | width | 预期 |
      | 2.0vp | 构造 RSPen stroke 模式 |
      | -1.0vp | 构造 RSBrush fill 模式（用 textColor） |
      | 0 | 不构造 pen/brush |

  Scenario: shaderStyle gradient 与 color 互斥
    Given 已设置 .shaderStyle(linearGradient)
    When 调用 .shaderStyle(Color.Red)
    Then ColorShaderStyle 生效，GradientShaderStyle 被 reset
    And 仅当 strokeWidth=0 时 color shader brush 生效
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "placeholderColor 为何双存储（paint flag + layout color）；paint PlaceholderColor 字段为何从不写入"
  - repo: "openharmony/arkui_ace_engine"
    query: "strokeWidth 负值切换 fill-brush 的渲染逻辑"
  - repo: "openharmony/arkui_ace_engine"
    query: "shaderStyle gradient/color 互斥机制与 strokeWidth 联动"
  - repo: "openharmony/arkui_ace_engine"
    query: "fontFeature 字符串解析为 Rosen FontFeatures 的流程"
```

**关键文档：** `specs/05-ui-components/09-text-components/05-text-area/design.md`（DESIGN-Func-05-09-05）；SDK `textArea.static.d.ets` / `text_area.d.ts`
