# 特性规格

> Func-04-03-11-Feat-04 文本阴影与 OpenType 特性：固化 textShadow/fontFeature/fontVariations 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 文本阴影与 OpenType 特性 (Text Shadow & OpenType Features) |
| 特性编号 | Func-04-03-11-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10/11 textShadow（数组 @since 11）；API 11/12 fontFeature；API 12 C-API；API 24 styled-string；API 26 fontVariations |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | textShadow 多阴影行为规格 | @since 10（数组 @since 11）；vector<Shadow> 存储 |
| ADDED | fontFeature OpenType 特性行为规格 | @since 12（TextClock @since 11）；FontFeaturesList 存储 |
| ADDED | fontVariations 字体变体行为规格 | @since 26.0.0（公开 API，非内部）；FONT_VARIATIONS_LIST 存储 |
| ADDED | C-API NODE_TEXT_TEXT_SHADOW/NODE_TEXT_FONT_FEATURE 行为规格 | @since 12 |
| ADDED | styled-string C-API OH_ArkUI_TextShadowStyle/OH_ArkUI_ShadowOptions 行为规格 | @since 24 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: 设置文本阴影

**作为** 应用开发者,
**我想要** 通过 `.textShadow(value)` 设置文本阴影（支持多阴影）,
**以便** 为文字添加阴影/光晕效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.textShadow({radius: 5, color: Color.Black, offsetX: 1, offsetY: 1})` (API 10+) THEN TextShadow 存为 `vector{Shadow}`，绘制单阴影 | 正常 |
| AC-1.2 | WHEN 调用 `.textShadow([{...}, {...}])` (API 11+) THEN 数组解析为多阴影 vector，按顺序绘制 | 正常 |
| AC-1.3 | WHEN textShadow 参数非 Number/Object/Array THEN 拒绝（不设置） | 异常 |
| AC-1.4 | WHEN 数组中某元素解析失败 THEN 跳过该元素（continue），其余正常入 vector | 异常 |
| AC-1.5 | WHEN ShadowOptions 缺失 radius THEN 默认 0.0（text-shadow 路径，js_view_abstract.cpp:11161） | 异常 |
| AC-1.6 | WHEN ShadowOptions 缺失 color THEN 默认 Black；ParseJsShadowColorStrategy 优先，否则 ParseJsColor | 异常 |
| AC-1.7 | WHEN ShadowOptions 缺失 offsetX/offsetY THEN 默认 0（px） | 异常 |
| AC-1.8 | WHEN ShadowOptions.type 为 BLUR THEN 按 BLUR 类型处理；默认 COLOR | 正常 |
| AC-1.9 | WHEN ShadowOptions.fill 设置 THEN **对 textShadow 不生效**（common.d.ts:8904 明示 "does not take effect in textShadow"） | 边界 |
| AC-1.10 | WHEN 在 Text 组件设置 textShadow THEN 写入 FontStyle::TextShadow (vector<Shadow>)；每阴影注册独立 resObj key "shadow_"+index（text_model_ng.cpp:837-857） | 正常 |
| AC-1.11 | WHEN 在 Span 组件设置 textShadow THEN 通过 ACE_UPDATE_SPAN_PROPERTY 写入 SpanNode（span_node.h:1061, RE_LAYOUT） | 正常 |
| AC-1.12 | WHEN 多阴影动画 THEN TextContentModifier 内部 shadows_ vector 可伸缩，每阴影独立动画（blurRadius/offsetX/offsetY/color 各自 AnimatableProperty，text_content_modifier.cpp:1307-1329） | 正常 |
| AC-1.13 | WHEN 渲染转换期 THEN 每个 Shadow 转 Rosen::TextShadow 并 push 到 txtStyle.shadows（constants_converter.cpp:404-411, 693-700） | 正常 |
| AC-1.14 | WHEN 在 TextClock/TextTimer 设置 textShadow THEN 支持（@since 11） | 正常 |
| AC-1.15 | WHEN 在 TextInput/TextArea/Search 设置 textShadow THEN **不支持**（未声明） | 边界 |

### US-2: 设置 OpenType 特性

**作为** 应用开发者,
**我想要** 通过 `.fontFeature(value)` 设置 OpenType 特性（如等宽数字）,
**以便** 控制字体的高级排版特性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.fontFeature('"ss01" on')` (API 12+) THEN 解析为 `FontFeaturesList{("ss01", 1)}` | 正常 |
| AC-2.2 | WHEN 调用 `.fontFeature('"liga" off')` THEN 解析为 `("liga", 0)` | 正常 |
| AC-2.3 | WHEN 调用 `.fontFeature('"pnum" 1, "liga" 0')` THEN 逗号切分多特性 `list{("pnum",1), ("liga",0)}` | 正常 |
| AC-2.4 | WHEN 调用 `.fontFeature('normal')` THEN 返回**空 list**（text_style_parser.cpp:344-346） | 正常 |
| AC-2.5 | WHEN fontFeature 字符串为空 THEN 返回空 list | 异常 |
| AC-2.6 | WHEN feature tag key 长度 ≠ 6（4 字符 + 2 引号）THEN 静默拒绝该 segment（text_style_parser.cpp:320） | 边界 |
| AC-2.7 | WHEN 单 segment 仅 1 token（如 `'"ss01"'`）THEN 默认 on=1（text_style_parser.cpp:331-333） | 正常 |
| AC-2.8 | WHEN 在 Text 设置 fontFeature THEN 写入 FontStyle::FontFeature (FontFeaturesList=list<pair<string,int32_t>>) | 正常 |
| AC-2.9 | WHEN 在 TextInput/TextArea/Search 设置 fontFeature THEN 支持（@since 12） | 正常 |
| AC-2.10 | WHEN 在 TextClock 设置 fontFeature THEN 支持（@since 11，早于 Text 的 12） | 正常 |
| AC-2.11 | WHEN 在 Span 尝试 fontFeature THEN **Span JS API 不暴露**；仅通过 StyledString/SpanObject 可达（span_node.h:1059 存储） | 边界 |
| AC-2.12 | WHEN 渲染转换期 THEN FontFeaturesList 转 Rosen::FontFeatures，每 (tag, value) 调 features.SetFeature（constants_converter.cpp:434-441, 716-723） | 正常 |

### US-3: 设置字体变体（API 26+）

**作为** 应用开发者,
**我想要** 通过 `.fontVariations(value)` 设置字体变体轴值,
**以便** 在变体字体上控制任意轴（wght/wdth/ital/自定义）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.fontVariations([{axis: 'wght', value: 700}])` (API 26+) THEN FontVariations 存为 `vector{FontVariation{axis:'wght', value:700.0}}` | 正常 |
| AC-3.2 | WHEN 调用 `.fontVariations([{axis: 'wdth', value: 80}, {axis: 'ital', value: 1}])` THEN 多轴存入 vector | 正常 |
| AC-3.3 | WHEN fontVariations 参数非数组 THEN 解析失败 → ResetFontVariations（js_text.cpp:1307-1318） | 异常 |
| AC-3.4 | WHEN 数组元素非对象或缺失 axis/value THEN 跳过该元素（js_utils.cpp:280-306） | 异常 |
| AC-3.5 | WHEN FontVariation.isNormalized 设置 (API 24+) THEN 传给 Rosen SetAxisValue 第 3 参（true=归一化 -1..1，false=原始范围） | 边界 |
| AC-3.6 | WHEN 在 fontVariations 供应 wght 轴 THEN **覆盖** VariableFontWeight 派生的 wght 值（在之后应用，constants_converter.cpp:627-632） | 边界 |
| AC-3.7 | WHEN fontVariations 与 fontWeight 同时设置 THEN fontVariations 优先级**高于** fontWeight（styled_string.d.ts:750） | 边界 |
| AC-3.8 | WHEN 在 Span 设置 fontVariations THEN 支持（@since 26，span.d.ts:375） | 正常 |
| AC-3.9 | WHEN 在 TextInput/TextArea/Search/TextClock/TextTimer 设置 fontVariations THEN **不支持**（未声明） | 边界 |
| AC-3.10 | WHEN 渲染转换期 THEN 先设 wght 轴（VariableFontWeight 派生值），再应用用户 fontVariations 各轴（constants_converter.cpp:626-632） | 正常 |

### US-4: 通过 C-API 设置阴影与特性

**作为** NDK 开发者,
**我想要** 通过 `setAttribute(NODE_TEXT_TEXT_SHADOW/NODE_TEXT_FONT_FEATURE, item)` 设置,
**以便** 在 C 代码中控制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `setAttribute(node, NODE_TEXT_TEXT_SHADOW, {value[0].f32: 5.0, value[1].i32: 0, value[2].u32: 0xFF000000, value[3].f32: 1.0, value[4].f32: 1.0})` THEN 设置单阴影（radius/type/color/offsetX/offsetY）；支持 TEXT/SPAN | 正常 |
| AC-4.2 | WHEN NODE_TEXT_TEXT_SHADOW item.size < 5 THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |
| AC-4.3 | WHEN NODE_TEXT_TEXT_SHADOW 调用 THEN **仅支持单阴影**（converter 硬编 1 元素 vector，style_modifier.cpp:9904-9907）；多阴影须用 styled-string | 边界 |
| AC-4.4 | WHEN NODE_TEXT_TEXT_SHADOW 调用 THEN **fill 字段未暴露**（内部 ArkUITextShadowStruct 有 fill 但 converter 仅填 5 槽） | 边界 |
| AC-4.5 | WHEN 调用 `setAttribute(node, NODE_TEXT_FONT_FEATURE, {string: '"ss01" on'})` THEN 解析为 FontFeaturesList；支持 TEXT/TEXT_INPUT/TEXT_AREA | 正常 |
| AC-4.6 | WHEN NODE_TEXT_FONT_FEATURE item.string 为 nullptr THEN 返回 PARAM_INVALID (401) | 异常 |
| AC-4.7 | WHEN 在 SPAN 调用 NODE_TEXT_FONT_FEATURE THEN **被拒绝**（不在 SPAN_ATTRIBUTES_MAP），返回 ERROR_CODE_NATIVE_IMPL_TYPE_NOT_SUPPORTED (106102) | 边界 |
| AC-4.8 | WHEN 在不支持节点（如 TEXT_INPUT 调用 NODE_TEXT_TEXT_SHADOW）THEN 静默 no-op，返回 NO_ERROR（converter 无分支落入 default） | 边界 |
| AC-4.9 | WHEN C-API 尝试设置 fontVariations THEN **不存在 NODE_TEXT_FONT_VARIATIONS 枚举**（ArkTS 独有，无 C-API 对应） | 边界 |
| AC-4.10 | WHEN GetTextShadow 调用 THEN 返回单阴影 5 槽（g_attributeItem.size=5） | 正常 |

### US-5: 通过样式字符串 C-API 设置阴影（@since 24）

**作为** NDK 开发者,
**我想要** 通过 `OH_ArkUI_TextShadowStyle`/`OH_ArkUI_ShadowOptions` 在样式字符串上设置多阴影,
**以便** 在 StyledString 场景精细控制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `OH_ArkUI_TextShadowStyle_Create()` (@since 24) THEN 返回新对象（内部 vector<OH_ArkUI_ShadowOptions>） | 正常 |
| AC-5.2 | WHEN 调用 `OH_ArkUI_TextShadowStyle_SetTextShadow(style, optionsArray, length)` THEN 设置多阴影 vector | 正常 |
| AC-5.3 | WHEN OH_ArkUI_TextShadowStyle_SetTextShadow length == 0 或 nullptr THEN 返回 PARAM_INVALID (401) | 异常 |
| AC-5.4 | WHEN 调用 `OH_ArkUI_ShadowOptions_Create()` THEN 返回单阴影对象（默认 color=0xFF000000, radius=0, type=COLOR, offsetX/Y=0, isFill=false） | 正常 |
| AC-5.5 | WHEN 调用 `OH_ArkUI_ShadowOptions_SetRadius/SetType/SetColor/SetOffsetX/SetOffsetY/SetFill` THEN 设置对应字段 | 正常 |
| AC-5.6 | WHEN OH_ArkUI_ShadowOptions_Set* 第一参数 nullptr THEN 返回 PARAM_INVALID (401) | 异常 |
| AC-5.7 | WHEN 调用 `OH_ArkUI_SpanStyle_SetTextShadowStyle(spanStyle, textShadowStyle)` THEN 拷贝 vector 并设 styledKey=TEXT_SHADOW | 正常 |
| AC-5.8 | WHEN `OH_ArkUI_SpanStyle_GetTextShadowStyle` 在 styledKey != TEXT_SHADOW 调用 THEN 返回 PARAM_INVALID (401) | 异常 |
| AC-5.9 | WHEN `OH_ArkUI_TextShadowStyle_GetTextShadow` 缓冲区不足 THEN header 文档说返回 BUFFER_SIZE_ERROR (106202)，但 impl 返回 PARAM_INVALID (401)（文档-代码差异） | 边界 |
| AC-5.10 | WHEN OH_ArkUI_ShadowOptions 设置 isFill THEN **对 styled-string textShadow 有效**（区别于 NODE_TEXT_TEXT_SHADOW 不暴露 fill） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.15 | R-1~R-9 | 已有实现 | 单测 | `test/unittest/core/components_ng/text/` |
| AC-2.1~2.12 | R-10~R-17 | 已有实现 | 单测 | 同上 + `text_style_parser_test` |
| AC-3.1~3.10 | R-18~R-24 | 已有实现 | 单测 | 同上 |
| AC-4.1~4.10 | R-25~R-32 | 已有实现 | 单测 | `test/unittest/interfaces/native_node_test.cpp` |
| AC-5.1~5.10 | R-33~R-40 | 已有实现 | 单测 | `test/unittest/interfaces/native_styled_string_test.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 SetTextShadow (Text/Span) | 解析 ShadowOptions/Array → vector<Shadow>；写入 FontStyle::TextShadow；触发 propNeedReCreateParagraph_=true | 单对象或数组 | AC-1.1, AC-1.2, AC-1.10 |
| R-2 | 异常 | textShadow 参数非 Number/Object/Array | 拒绝（不设置） | js_utils.cpp:257 | AC-1.3 |
| R-3 | 异常 | 数组元素解析失败 | 跳过该元素（continue） | js_utils.cpp:268-277 | AC-1.4 |
| R-4 | 行为 | ShadowOptions 缺失字段 | radius 默认 0.0（text-shadow）；color 默认 Black（ParseJsShadowColorStrategy 优先）；offsetX/Y 默认 0；type 默认 COLOR | js_view_abstract.cpp:11104-11153 | AC-1.5~1.8 |
| R-5 | 边界 | ShadowOptions.fill 设置 | 对 textShadow **不生效**（common.d.ts:8904 明示） | fill 仅对 view shadow 有效 | AC-1.9 |
| R-6 | 行为 | Span textShadow 写入 | 通过 ACE_UPDATE_SPAN_PROPERTY 写入 SpanNode（span_node.h:1061, RE_LAYOUT） | Span 并行存储 | AC-1.11 |
| R-7 | 行为 | 多阴影动画 | TextContentModifier shadows_ vector 可伸缩，每阴影独立 AnimatableProperty（blurRadius/offsetX/offsetY/color） | text_content_modifier.cpp:1307-1329 | AC-1.12 |
| R-8 | 行为 | 渲染转换期 | 每 Shadow 转 Rosen::TextShadow push 到 txtStyle.shadows | constants_converter.cpp:404-411, 693-700 | AC-1.13 |
| R-9 | 边界 | textShadow 逐组件适用 | Text/Span/TextClock/TextTimer 支持（@since 10/11）；TextInput/TextArea/Search 不支持 | 逐组件矩阵 | AC-1.14, AC-1.15 |
| R-10 | 行为 | 调用 SetFontFeature | 字符串解析为 FontFeaturesList=list<pair<string,int32_t>>；写入 FontStyle::FontFeature | OpenType tag 格式 | AC-2.1~2.3, AC-2.8 |
| R-11 | 行为 | fontFeature='normal' | 返回空 list | text_style_parser.cpp:344-346 | AC-2.4 |
| R-12 | 异常 | fontFeature 字符串空 | 返回空 list | text_style_parser.cpp:344 | AC-2.5 |
| R-13 | 边界 | feature tag key 长度 ≠ 6 | 静默拒绝该 segment（4 字符 + 2 引号 = 6） | text_style_parser.cpp:320 | AC-2.6 |
| R-14 | 行为 | 单 segment 仅 1 token | 默认 on=1 | text_style_parser.cpp:331-333 | AC-2.7 |
| R-15 | 行为 | 渲染转换期 | FontFeaturesList 转 Rosen::FontFeatures，每 (tag,value) 调 SetFeature | constants_converter.cpp:434-441, 716-723 | AC-2.12 |
| R-16 | 边界 | fontFeature 逐组件适用 | Text/TextInput/TextArea/Search/TextClock 支持；Span JS API 不暴露（仅 StyledString 可达）；TextTimer 不支持 | 逐组件矩阵 | AC-2.9~2.11 |
| R-17 | 行为 | fontFeature @since | Text @since 12；TextClock @since 11（早于 Text） | 版本差异 | AC-2.10 |
| R-18 | 行为 | 调用 SetFontVariations (API 26+) | 数组解析为 vector<FontVariation{axis,value,isNormalized?}>；写入 FontStyle::FontVariations | 公开 API @since 26 | AC-3.1, AC-3.2, AC-3.8 |
| R-19 | 异常 | fontVariations 非数组 | 解析失败 → ResetFontVariations | js_text.cpp:1307-1318 | AC-3.3 |
| R-20 | 异常 | 数组元素非对象或缺失 axis/value | 跳过该元素 | js_utils.cpp:280-306 | AC-3.4 |
| R-21 | 边界 | FontVariation.isNormalized (API 24+) | 传给 Rosen SetAxisValue 第 3 参（true=归一化 -1..1，0=默认；false=原始范围） | text_style.h:90-99 | AC-3.5 |
| R-22 | 边界 | fontVariations 供应 wght 轴 | **覆盖** VariableFontWeight 派生 wght 值（在之后应用） | constants_converter.cpp:627-632 | AC-3.6 |
| R-23 | 边界 | fontVariations 与 fontWeight 同时 | fontVariations 优先级**高于** fontWeight | styled_string.d.ts:750 | AC-3.7 |
| R-24 | 边界 | fontVariations 逐组件适用 | 仅 Text/Span 支持（@since 26）；TextInput/TextArea/Search/TextClock/TextTimer 不支持 | 逐组件矩阵 | AC-3.9 |
| R-25 | 行为 | C-API NODE_TEXT_TEXT_SHADOW set | value[0..4] = radius/type/color/offsetX/offsetY；支持 TEXT/SPAN | style_modifier.cpp:9896 | AC-4.1 |
| R-26 | 异常 | C-API item.size < 5 | 返回 PARAM_INVALID (401) | style_modifier.cpp:9899 | AC-4.2 |
| R-27 | 边界 | C-API 仅单阴影 | converter 硬编 1 元素 vector；多阴影须用 styled-string | style_modifier.cpp:9904-9907 | AC-4.3 |
| R-28 | 边界 | C-API fill 未暴露 | 内部 ArkUITextShadowStruct 有 fill 但 converter 仅填 5 槽 | arkoala_api.h:661-672 | AC-4.4 |
| R-29 | 行为 | C-API NODE_TEXT_FONT_FEATURE set | item.string 解析为 FontFeaturesList；支持 TEXT/TEXT_INPUT/TEXT_AREA | style_modifier.cpp:14443 | AC-4.5 |
| R-30 | 异常 | C-API item.string nullptr | 返回 PARAM_INVALID (401) | style_modifier.cpp:14446 | AC-4.6 |
| R-31 | 边界 | C-API SPAN 调用 NODE_TEXT_FONT_FEATURE | 被拒绝（不在 SPAN_ATTRIBUTES_MAP），返回 106102 | style_modifier.cpp:193-211 | AC-4.7 |
| R-32 | 边界 | C-API 不支持节点静默 no-op | SetTextShadow/SetFontFeature 在无分支节点返回 NO_ERROR（落入 default） | style_modifier.cpp | AC-4.8 |
| R-33 | 边界 | C-API 无 NODE_TEXT_FONT_VARIATIONS | fontVariations 是 ArkTS 独有，无 C-API 对应 | NDK 枚举缺失 | AC-4.9 |
| R-34 | 行为 | C-API GetTextShadow | 返回单阴影 5 槽（size=5） | style_modifier.cpp:11273 | AC-4.10 |
| R-35 | 行为 | styled-string OH_ArkUI_TextShadowStyle (@since 24) | Create/Destroy；SetTextShadow(optionsArray, length) 设置多阴影 vector | span_style_native_impl.cpp:1740-1780 | AC-5.1, AC-5.2 |
| R-36 | 异常 | styled-string SetTextShadow length==0 或 nullptr | 返回 PARAM_INVALID (401) | span_style_native_impl.cpp:1751 | AC-5.3 |
| R-37 | 行为 | OH_ArkUI_ShadowOptions_Create | 默认 color=0xFF000000, radius=0, type=COLOR, offsetX/Y=0, isFill=false | rich_editor_native_impl.cpp:470 | AC-5.4 |
| R-38 | 行为 | OH_ArkUI_ShadowOptions_Set* | 设置 Radius/Type/Color/OffsetX/OffsetY/Fill | rich_editor_native_impl.cpp:488-565 | AC-5.5 |
| R-39 | 异常 | OH_ArkUI_ShadowOptions_Set* nullptr | 返回 PARAM_INVALID (401) | CHECK_NULL_RETURN | AC-5.6 |
| R-40 | 边界 | styled-string GetTextShadow 缓冲不足 | header 文档说 BUFFER_SIZE_ERROR (106202)，impl 返回 PARAM_INVALID (401)（文档-代码差异） | span_style_native_impl.cpp:1777 vs native_styled_string_descriptor.h:2105 | AC-5.9 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-9, AC-1.1~1.15 | 单测 | textShadow 多阴影 + 逐阴影动画 + 逐组件适用 |
| VM-2 | R-10~R-17, AC-2.1~2.12 | 单测 | fontFeature 字符串解析 + OpenType 特性 |
| VM-3 | R-18~R-24, AC-3.1~3.10 | 单测 | fontVariations 多轴 + wght 覆盖 + 优先级 |
| VM-4 | R-25~R-34, AC-4.1~4.10 | 单测/native_node_test | C-API 单阴影 + fontFeature + 缺失枚举 |
| VM-5 | R-35~R-40, AC-5.1~5.10 | 单测 | styled-string C-API @since 24 |
| VM-6 | 全量 | XTS/集成 | 端到端阴影与 OpenType 渲染 |

---

## API 变更分析

### 新增 API

**ArkTS 动态 API：**

| API 签名 | 开放范围 | @since | 关联 AC |
|----------|---------|--------|---------|
| `textShadow(value: ShadowOptions \| Array<ShadowOptions>): TextAttribute` (Text/Span/TextClock/TextTimer) | Public | 10 (array 11; Span/TextClock/TextTimer 11) | AC-1.* |
| `fontFeature(value: string): TextAttribute` (Text/TextInput/TextArea/Search/TextClock) | Public | 12 (TextClock 11) | AC-2.* |
| `fontVariations(fontVariations: Array<FontVariation>): TextAttribute` (Text/Span) | Public | 26.0.0 | AC-3.* |

**逐组件适用性矩阵（动态 API）：**

| 组件 | textShadow | fontFeature | fontVariations |
|------|------------|-------------|---------------|
| TextAttribute | ✓ (@since 10, array 11) | ✓ (@since 12) | ✓ (@since 26) |
| SpanAttribute | ✓ (@since 11) | ✗ JS API（仅 StyledString 可达） | ✓ (@since 26) |
| TextInputAttribute | ✗ | ✓ (@since 12) | ✗ |
| TextAreaAttribute | ✗ | ✓ (@since 12) | ✗ |
| SearchAttribute | ✗ | ✓ (@since 12) | ✗ |
| TextClockAttribute | ✓ (@since 11) | ✓ (@since 11) | ✗ |
| TextTimerAttribute | ✓ (@since 11) | ✗ | ✗ |

**类型定义：**

| 类型 | 定义 | 位置 |
|------|------|------|
| ShadowOptions | {radius: number\|Resource; type?: ShadowType; color?: Color\|string\|Resource\|ColoringStrategy; offsetX?: number\|Resource; offsetY?: number\|Resource; fill?: boolean} | common.d.ts:8786 |
| FontVariation | {axis: string; value: double; isNormalized?: boolean} | @ohos.graphics.text.d.ts:1108 |

**C-API (NDK)：**

| 属性枚举 | 值 | 格式 | @since | 支持节点 | 关联 AC |
|----------|-----|------|--------|----------|---------|
| NODE_TEXT_TEXT_SHADOW | 1015 | value[0].f32 radius + value[1].i32 type + value[2].u32 color + value[3].f32 offsetX + value[4].f32 offsetY | 12 | TEXT/SPAN | AC-4.1 |
| NODE_TEXT_FONT_FEATURE | 1024 | .string (OpenType 特性字符串) | 12 | TEXT/TEXT_INPUT/TEXT_AREA | AC-4.5 |

**样式字符串 C-API (@since 24)：**

| 函数 | 签名 | 关联 AC |
|------|------|---------|
| OH_ArkUI_TextShadowStyle_Create | () -> OH_ArkUI_TextShadowStyle* | AC-5.1 |
| OH_ArkUI_TextShadowStyle_SetTextShadow | (style, const OH_ArkUI_ShadowOptions** options, uint32_t length) -> ArkUI_ErrorCode | AC-5.2 |
| OH_ArkUI_TextShadowStyle_GetTextShadow | (style, OH_ArkUI_ShadowOptions**, uint32_t shadowOptionsSize, uint32_t* writeLength) -> ArkUI_ErrorCode | AC-5.9 |
| OH_ArkUI_ShadowOptions_Create | () -> OH_ArkUI_ShadowOptions* | AC-5.4 |
| OH_ArkUI_ShadowOptions_SetRadius/SetType/SetColor/SetOffsetX/SetOffsetY/SetFill | (option, value) -> ArkUI_ErrorCode | AC-5.5 |
| OH_ArkUI_SpanStyle_SetTextShadowStyle | (spanStyle, const OH_ArkUI_TextShadowStyle*) -> ArkUI_ErrorCode | AC-5.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无变更/废弃 API | — |

---

## 接口规格

### 接口定义

**textShadow**

| 属性 | 值 |
|------|-----|
| 函数签名 | `textShadow(value: ShadowOptions \| Array<ShadowOptions>): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.15 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ShadowOptions \| Array<ShadowOptions> | 是 | 无（空 vector） | 单对象或数组；数组每元素可独立解析失败跳过；fill 对 textShadow 不生效 |

---

**fontFeature**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontFeature(value: string): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.12 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | 无（空 list） | 格式：normal \| <feature-tag-value>；feature-tag-value = <string> [on\|off\|1\|0]；多特性逗号分隔；tag key 长度 6（4 字符+2 引号） |

---

**fontVariations (API 26+)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontVariations(fontVariations: Array<FontVariation>): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| fontVariations | Array<FontVariation> | 是 | 无（空 vector） | 非数组→Reset；每元素须有 axis(string)+value(number)；isNormalized 可选；wght 轴覆盖 VariableFontWeight；优先级 > fontWeight |

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 10/11**: textShadow 单对象 @since 10，数组 @since 11
  - **API 11/12**: fontFeature TextClock @since 11，Text @since 12
  - **API 24**: styled-string C-API OH_ArkUI_TextShadowStyle/OH_ArkUI_ShadowOptions；FontVariation.isNormalized 字段
  - **API 26**: fontVariations 公开 API（Text/Span）；优先级 > fontWeight
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（textShadow）；API 11（fontFeature TextClock）；API 12（fontFeature Text + C-API NODE_TEXT_*）；API 24（styled-string C-API）；API 26（fontVariations）
- **API 版本号策略:** @since 10/11/12/24/26 标注新增

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| fontVariations 是公开 API @since 26 | 非内部；Text/Span 暴露；优先级 > fontWeight | AC-3.1, AC-3.7 |
| fontFeature 字符串格式 | OpenType 4 字符 tag 包引号（key length 6）；normal 返回空 list | AC-2.6, AC-2.4 |
| TextShadow vector + 逐阴影动画 | vector<Shadow> 有序；TextContentModifier shadows_ 可伸缩；每阴影独立 AnimatableProperty | AC-1.12 |
| fontVariations vs VariableFontWeight | VariableFontWeight 仅 wght 轴便利；FontVariations 通用；wght 覆盖（在之后应用） | AC-3.6 |
| C-API textShadow 单阴影 + fill 未暴露 | 5 槽 value[]；多阴影须 styled-string @since 24 | AC-4.3, AC-4.4 |
| C-API fontVariations 缺失 | ArkTS 独有，无 C-API 对应 | AC-4.9 |
| C-API 静默 no-op + 文档-代码差异 | 不支持节点返回 NO_ERROR；GetTextShadow 缓冲不足 header 说 106202 但 impl 返 401 | AC-4.8, AC-5.9 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | textShadow/fontFeature/fontVariations 设置 + 标记脏 < 1μs；多阴影动画每阴影独立 | benchmark | — |
| 内存 | vector<Shadow>/list<pair>/vector<FontVariation> 仅在设置时分配 | hidumper | — |
| 可靠性 | fontFeature tag 格式错误静默拒绝；fontVariations 非数组 Reset | 集成测试 | — |

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
| 无障碍 | 是 | 阴影影响可读性但无障碍语义由组件提供 | — |
| 大字体 | 否 | 阴影/特性/变体不受系统字体缩放影响 | — |
| 深色模式 | 是 | textShadow.color 可通过 Resource 引用主题色 | AC-1.6 |
| 多窗口/分屏 | 否 | 不受窗口尺寸影响 | — |
| 多用户 | 否 | 无用户态差异 | — |
| 版本升级 | 是 | API 10/11/12/24/26 版本差异须通过 API 版本守护 | AC-1.1, AC-2.1, AC-3.1, AC-4.1, AC-5.1 |
| 生态兼容 | 是 | C-API（NODE_TEXT_TEXT_SHADOW/FONT_FEATURE + styled-string）应与 ArkTS 一致；fontVariations 无 C-API 对应是已知缺口 | AC-4.*, AC-5.* |

---

## 行为场景

```gherkin
Feature: 文本阴影与 OpenType 特性
  作为 应用开发者
  我想要 通过声明式 API 与 C-API 控制文本阴影、OpenType 特性与字体变体
  以便 实现高级文本表现

  # ─── textShadow ──────────────────────────────────

  Scenario: 设置单阴影
    Given 一个 Text 组件
    When 调用 .textShadow({radius: 5, color: Color.Black, offsetX: 1, offsetY: 1})
    Then TextShadow = vector{Shadow{radius=5, color=Black, offsetX=1, offsetY=1}}

  Scenario: 设置多阴影（API 11+）
    Given 目标 API 版本 >= 11
    And 一个 Text 组件
    When 调用 .textShadow([{radius: 5, color: Color.Red}, {radius: 10, color: Color.Blue}])
    Then TextShadow = vector{Shadow{...Red}, Shadow{...Blue}}（按顺序）

  Scenario: 数组元素解析失败跳过
    Given 一个 Text 组件
    When 调用 .textShadow([{radius: 5}, "invalid"])
    Then 仅 Shadow{radius=5} 入 vector，"invalid" 跳过

  Scenario: fill 对 textShadow 不生效
    Given 一个 Text 组件
    When 调用 .textShadow({radius: 5, fill: true})
    Then fill 字段被忽略（common.d.ts:8904 明示）

  Scenario: TextInput 不支持 textShadow
    Given 一个 TextInput 组件
    When 尝试 .textShadow({...})
    Then 不支持（TextInputAttribute 未声明 textShadow）

  # ─── fontFeature ─────────────────────────────────

  Scenario: 设置 OpenType 特性
    Given 一个 Text 组件
    When 调用 .fontFeature('"ss01" on')
    Then FontFeaturesList = list{("ss01", 1)}

  Scenario: fontFeature normal 返回空 list
    Given 一个 Text 组件
    When 调用 .fontFeature('normal')
    Then FontFeaturesList = 空 list

  Scenario: feature tag key 长度 ≠ 6 静默拒绝
    Given 一个 Text 组件
    When 调用 .fontFeature('"abc" 1')
    Then key 长度 5 ≠ 6，该 segment 静默拒绝

  Scenario: Span JS API 不暴露 fontFeature
    Given 一个 Span 组件
    When 尝试 .fontFeature('"ss01" on')
    Then SpanAttribute 未声明 fontFeature 方法
    But 可通过 StyledString/SpanObject 设置

  # ─── fontVariations (API 26+) ────────────────────

  Scenario: 设置多轴变体
    Given 目标 API 版本 >= 26
    And 一个 Text 组件
    When 调用 .fontVariations([{axis: 'wght', value: 700}, {axis: 'wdth', value: 80}])
    Then FontVariations = vector{{wght, 700}, {wdth, 80}}

  Scenario: fontVariations wght 覆盖 VariableFontWeight
    Given 一个 Text 组件已 .fontWeight(550, {enableVariableFontWeight: true})
    When 调用 .fontVariations([{axis: 'wght', value: 900}])
    Then 渲染时 wght=900（覆盖 550）

  Scenario: fontVariations 优先级 > fontWeight
    Given 一个 Text 组件已 .fontWeight(FontWeight.Bold)
    When 调用 .fontVariations([{axis: 'wght', value: 300}])
    Then 渲染时 wght=300（覆盖 Bold=700）

  Scenario: fontVariations 非数组 Reset
    Given 一个 Text 组件
    When 调用 .fontVariations(123)
    Then 解析失败，调用 ResetFontVariations

  # ─── C-API ──────────────────────────────────────

  Scenario: C-API 设置单阴影
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_TEXT_TEXT_SHADOW, {value[0].f32: 5.0, value[1].i32: 0, value[2].u32: 0xFF000000, value[3].f32: 1.0, value[4].f32: 1.0})
    Then 设置单阴影

  Scenario: C-API textShadow 仅单阴影
    Given 一个 ARKUI_NODE_TEXT 节点
    When 尝试通过 NODE_TEXT_TEXT_SHADOW 设置多阴影
    Then 不支持（converter 硬编 1 元素 vector）；多阴影须用 OH_ArkUI_TextShadowStyle (@since 24)

  Scenario: C-API 无 fontVariations 枚举
    When 尝试 setAttribute(node, NODE_TEXT_FONT_VARIATIONS, ...)
    Then 枚举不存在（ArkTS 独有，无 C-API 对应）

  Scenario: C-API SPAN 调用 NODE_TEXT_FONT_FEATURE 被拒绝
    Given 一个 ARKUI_NODE_SPAN 节点
    When 调用 setAttribute(span, NODE_TEXT_FONT_FEATURE, ...)
    Then 不在 SPAN_ATTRIBUTES_MAP，返回 106102

  # ─── styled-string C-API (@since 24) ─────────────

  Scenario: 样式字符串多阴影
    Given 一个 OH_ArkUI_TextShadowStyle 对象
    When 创建多个 OH_ArkUI_ShadowOptions 并设置字段
    And 调用 OH_ArkUI_TextShadowStyle_SetTextShadow(style, optionsArray, length)
    Then 多阴影 vector 设置

  Scenario: styled-string isFill 有效
    Given 一个 OH_ArkUI_ShadowOptions 设置 isFill=true
    When 通过 OH_ArkUI_TextShadowStyle_SetTextShadow 设置
    Then isFill 对 styled-string textShadow 有效（区别于 NODE_TEXT_TEXT_SHADOW 不暴露 fill）
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（覆盖 textShadow/fontFeature/fontVariations；不含 fontSize/fontColor/fontWeight/fontStyle/fontFamily（Feat-01）、decoration/textCase/lineThicknessScale（Feat-02）、letterSpacing/lineHeight/baselineOffset（Feat-03）、minFontSize/maxFontSize/minFontScale/maxFontScale（Feat-05））
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TextLayoutProperty FontStyle TextShadow FontFeature FontVariations vector Shadow FontFeaturesList"
  - repo: "openharmony/ace_engine"
    query: "ParseTextShadowFromShadowObject ParseShadowPropsInner js_view_abstract shadow radius color offsetX offsetY fill"
  - repo: "openharmony/ace_engine"
    query: "ParseFontFeatureSettings ParseFontFeatureSetting text_style_parser OpenType tag key length 6"
  - repo: "openharmony/ace_engine"
    query: "ParseJsFontVariations FontVariation axis value isNormalized js_utils"
  - repo: "openharmony/ace_engine"
    query: "constants_converter ConvertTxtStyle Rosen TextShadow FontFeatures fontVariations SetAxisValue wght override"
  - repo: "openharmony/ace_engine"
    query: "style_modifier.cpp SetTextShadow SetFontFeature NODE_TEXT_TEXT_SHADOW NODE_TEXT_FONT_FEATURE"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_TextShadowStyle OH_ArkUI_ShadowOptions span_style_native_impl native_styled_string_descriptor"
```

**关键文档：**
- 架构设计：`specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md`
- SDK 类型定义：`interface/sdk-js/api/@internal/component/ets/text.d.ts`、`common.d.ts`、`text_common.d.ts`
- C-API：`interfaces/native/native_node.h`、`interfaces/native/native_styled_string_descriptor.h`、`interfaces/native/native_type.h`
