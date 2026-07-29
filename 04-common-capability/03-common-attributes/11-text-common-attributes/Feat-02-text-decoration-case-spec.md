# 特性规格

> Func-04-03-11-Feat-02 文本装饰与大小写：固化 decoration（type/color/style/thicknessScale）与 textCase 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 文本装饰与大小写 (Text Decoration & Case) |
| 特性编号 | Func-04-03-11-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持 decoration/textCase，API 12 style 字段，API 20 thicknessScale (Text/Span)，API 22/23 C-API thickness，API 24 styled-string，API 26 TextInput/TextArea/Search thicknessScale |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | decoration 聚合接口（type/color/style/thicknessScale）行为规格 | SDK @since 7 已有 API，本次补录 |
| ADDED | textCase 大小写转换行为规格 | SDK @since 7 已有 API，本次补录 |
| ADDED | lineThicknessScale 内部属性 + thicknessScale 公开字段行为规格 | @since 20 (Text/Span) / @since 26 (TextInput/TextArea/Search) |
| ADDED | C-API NODE_TEXT_DECORATION + NODE_TEXT_CASE 行为规格 | @since 12，thickness @since 22/23 |
| ADDED | 对象式 C-API NODE_TEXT_INPUT_DECORATION/NODE_TEXT_AREA_DECORATION 行为规格 | @since 26 |
| ADDED | styled-string C-API OH_ArkUI_DecorationStyle_* 行为规格 | @since 24 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: 在 Text/Span 上设置文本装饰

**作为** 应用开发者,
**我想要** 通过 `.decoration({type, color, style, thicknessScale})` 设置 Text/Span 的下划线/上划线/删除线,
**以便** 装饰文本表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.decoration({type: TextDecorationType.Underline})` THEN TextDecoration 存为 `vector{UNDERLINE}`，绘制下划线 | 正常 |
| AC-1.2 | WHEN 调用 `.decoration({type: TextDecorationType.LineThrough, color: Color.Red, style: TextDecorationStyle.DOTTED})` THEN TextDecoration={LINE_THROUGH}, TextDecorationColor=Red, TextDecorationStyle=DOTTED | 正常 |
| AC-1.3 | WHEN 调用 `.decoration({type: TextDecorationType.None})` 或 `.decoration(undefined)` THEN TextDecoration 设为 NONE（清除装饰） | 正常 |
| AC-1.4 | WHEN decoration 参数对象缺失 type 字段 THEN type 回退到 theme `GetTextDecoration()` | 异常 |
| AC-1.5 | WHEN decoration 参数对象缺失 color 字段 THEN color 回退：深色模式用 theme GetTextColor，否则用 theme GetTextDecorationColor | 异常 |
| AC-1.6 | WHEN decoration 参数对象缺失 style 字段 THEN style 默认 `TextDecorationStyle.SOLID` (DEFAULT_TEXT_DECORATION_STYLE) | 异常 |
| AC-1.7 | WHEN decoration 参数为非对象类型（如 number）THEN 直接返回（不设置任何装饰字段） | 异常 |
| AC-1.8 | WHEN 在 Text 组件调用 decoration THEN 写入 TextLayoutProperty::FontStyle::{TextDecoration/TextDecorationColor/TextDecorationStyle}，触发 PROPERTY_UPDATE_MEASURE + propNeedReCreateParagraph_=true | 正常 |
| AC-1.9 | WHEN 在 Span 组件调用 decoration THEN 通过 ACE_UPDATE_SPAN_PROPERTY 写入 SpanNode（span_node.h:1054-1058），TextCase 用 RE_CREATE 标志，装饰项用 RE_LAYOUT | 正常 |

### US-2: 设置装饰线厚度比例

**作为** 应用开发者,
**我想要** 通过 `decoration({..., thicknessScale})` 设置装饰线厚度倍数,
**以便** 调整装饰线粗细。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 在 Text/Span 调用 `decoration({type: Underline, thicknessScale: 2.0})` (API 20+) THEN LineThicknessScale=2.0f，装饰线厚度 = baseThickness × 2.0 | 正常 |
| AC-2.2 | WHEN thicknessScale 缺失 THEN 默认 `1.0f`（不缩放） | 正常 |
| AC-2.3 | WHEN thicknessScale 为负数 THEN JS bridge clamp 到 `1.0f`（js_text.cpp:875-879） | 异常 |
| AC-2.4 | WHEN LineThicknessScale > 1.0 THEN text_pattern.cpp:6716-6722 在计算 hit-test/bounds rect 时扩展 boundsHeight += thickness | 边界 |
| AC-2.5 | WHEN 渲染转换期 (constants_converter.cpp:666) THEN txtStyle.decorationThicknessScale = static_cast<double>(textStyle.GetLineThicknessScale())，下传给 Rosen 文本引擎 | 正常 |
| AC-2.6 | WHEN 使用静态范式 Text.decoration（API 23 static）THEN **无法设置 thicknessScale**（静态 DecorationStyleInterface 无此字段，缺口） | 边界 |

### US-3: 在 TextInput/TextArea/Search 上设置装饰

**作为** 应用开发者,
**我想要** 通过 `.decoration({type, color, style, thicknessScale})` 设置可编辑组件的装饰,
**以便** 装饰输入框文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 在 TextInput/TextArea/Search 调用 `decoration({type, color, style})` (API 12+) THEN 参数类型为 `TextDecorationOptions`（非 `DecorationStyleInterface`） | 正常 |
| AC-3.2 | WHEN 在 TextInput/TextArea/Search 调用 `decoration({..., thicknessScale})` (API 26+) THEN 厚度字段生效（TextDecorationOptions.thicknessScale @since 26 dynamic / 26 static） | 边界 |
| AC-3.3 | WHEN Search 调用 decoration THEN 委托给内部 TextField 子节点的 TextFieldLayoutProperty（search_model_ng.cpp:2070-2181） | 正常 |
| AC-3.4 | WHEN decoration 参数非对象 THEN JSTextField::SetDecoration 重置四项 setter（含 SetLineThicknessScale(DEFAULT)） | 异常 |
| AC-3.5 | WHEN 在 TextInput/TextArea/Search 尝试 `textCase()` THEN **不支持**（textCase 仅 Text/Span 暴露） | 边界 |

### US-4: 设置文本大小写转换

**作为** 应用开发者,
**我想要** 通过 `.textCase(value)` 设置文本大小写,
**以便** 强制文本以小写/大写/首字母大写形式显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.textCase(TextCase.LowerCase)` THEN TextCase=LOWERCASE，显示文本转为小写 | 正常 |
| AC-4.2 | WHEN 调用 `.textCase(TextCase.UpperCase)` THEN TextCase=UPPERCASE，显示文本转为大写 | 正常 |
| AC-4.3 | WHEN 调用 `.textCase(TextCase.Normal)` THEN TextCase=NORMAL，按原样显示 | 正常 |
| AC-4.4 | WHEN 设置 textCase THEN **存储的 Content (std::u16string) 不变**；仅在渲染/布局时对 content 副本执行 StringUtils::TransformStrCase（text_layout_algorithm.cpp:1080-1083） | 边界 |
| AC-4.5 | WHEN 设置 textCase 后复制/选择文本 THEN 复制/选择的是原始 content（未转换），保留语义 | 正常 |
| AC-4.6 | WHEN textCase 越界（API < 12）THEN JSText 静默返回；JSSpan 不 clamp 也不设置（行为差异） | 异常 |
| AC-4.7 | WHEN textCase 越界（API ≥ 12）THEN JSText clamp 到 0（NORMAL） | 异常 |
| AC-4.8 | WHEN 在 TextInput/TextArea/Search 尝试 textCase THEN **不支持**（textCase 仅 Text/Span 暴露，编辑组件不可用） | 边界 |
| AC-4.9 | WHEN StringUtils::TransformStrCase 处理 Unicode 字符（如 é→É）THEN 使用 std::towlower/std::towupper（string_utils.cpp:761-780） | 正常 |

### US-5: 多装饰共存

**作为** 应用开发者,
**我想要** 同时应用多种装饰（如下划线+删除线）,
**以便** 复合装饰文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN TextDecoration 存为 `vector{UNDERLINE, LINE_THROUGH}` THEN 渲染时 ConvertTxtTextDecoration (constants_converter.cpp:316-343) 位 OR 合并，同时绘制下划线与删除线 | 正常 |
| AC-5.2 | WHEN vector 含 NONE THEN NONE 不贡献装饰位（不绘制） | 正常 |
| AC-5.3 | WHEN 公开 JS API `decoration({type: Underline})` 调用 THEN bridge 将单个 type 包装为 `{value}` vector（js_text.cpp:849-856），每次调用仅设单值 | 边界 |
| AC-5.4 | WHEN Inspector 序列化多装饰 THEN 用逗号连接（utils.h:321-332），如 "TextDecorationType.Underline,TextDecorationType.LineThrough" | 正常 |

### US-6: 通过 C-API 设置装饰与大小写

**作为** NDK 开发者,
**我想要** 通过 `setAttribute(NODE_TEXT_DECORATION/NODE_TEXT_CASE, item)` 设置装饰与大小写,
**以便** 在 C 代码中控制文本表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `setAttribute(node, NODE_TEXT_DECORATION, {value[0].i32: 1, value[1].u32: 0xFFFF0000, value[2].i32: 2})` THEN 设置 type=UNDERLINE, color=Red, style=DOTTED；支持 TEXT/SPAN | 正常 |
| AC-6.2 | WHEN NODE_TEXT_DECORATION 含 `value[3].f32` (thicknessScale) 且 API ≥ 23 THEN 设置 LineThicknessScale（文档标注 @since 22，运行期门槛 API 23，差异） | 边界 |
| AC-6.3 | WHEN NODE_TEXT_DECORATION 在 SPAN 节点调用 THEN thicknessScale 被忽略（硬编 1.0f，style_modifier.cpp:13505-13506）；Get 仅返回 3 字段（无 thickness） | 边界 |
| AC-6.4 | WHEN 调用 `setAttribute(node, NODE_TEXT_CASE, {value[0].i32: 2})` THEN 设置 TextCase=UPPER；支持 TEXT/SPAN | 正常 |
| AC-6.5 | WHEN NODE_TEXT_DECORATION 的 `value[0].i32` 越界（>3）或 `value[2].i32` 越界（>4）THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |
| AC-6.6 | WHEN NODE_TEXT_CASE 的 `value[0].i32` 越界（>2）THEN 返回 PARAM_INVALID (401) | 异常 |
| AC-6.7 | WHEN 在 TEXT_INPUT/TEXT_AREA/BUTTON 节点调用 NODE_TEXT_DECORATION/NODE_TEXT_CASE THEN no-op（仅 TEXT/SPAN 支持） | 边界 |

### US-7: 通过对象式 C-API 设置 TextInput/TextArea 装饰（@since 26）

**作为** NDK 开发者,
**我想要** 通过 `setAttribute(NODE_TEXT_INPUT_DECORATION/NODE_TEXT_AREA_DECORATION, {object})` 设置装饰,
**以便** 在可编辑节点上精细控制装饰。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `setAttribute(textInput, NODE_TEXT_INPUT_DECORATION, {object: decorationStyleOptions})` (@since 26) THEN SetComponentDecoration 解析 OH_ArkUI_DecorationStyleOptions，分发到 textInputModifier.setTextInputDecoration | 正常 |
| AC-7.2 | WHEN 调用 `setAttribute(textArea, NODE_TEXT_AREA_DECORATION, {object})` THEN 分发到 textAreaModifier.setTextAreaDecoration | 正常 |
| AC-7.3 | WHEN item.object 为 null THEN 调用 ResetComponentDecoration 并返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |
| AC-7.4 | WHEN 对象式 C-API 设置 thicknessScale 为负数 THEN clamp 到 DEFAULT_LINE_THICKNESS_SCALE (1.0f)（style_modifier.cpp:13557），无 API 版本门槛 | 边界 |
| AC-7.5 | WHEN GetComponentDecoration 返回 THEN 使用 thread_local static OH_ArkUI_DecorationStyleOptions 默认对象（NONE/BLACK/SOLID/1.0f），须先复制再调下一次 Get | 边界 |

### US-8: 通过样式字符串 C-API 设置装饰（@since 24）

**作为** NDK 开发者,
**我想要** 通过 `OH_ArkUI_DecorationStyle_*` 在样式字符串上设置装饰,
**以便** 在 StyledString/SpanStyle 场景精细控制装饰。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `OH_ArkUI_DecorationStyle_Create()` (@since 24) THEN 返回新对象，默认 {NONE/0/SOLID/1.0f/enableMultiType=false} | 正常 |
| AC-8.2 | WHEN 调用 `OH_ArkUI_DecorationStyle_SetTextDecorationType(style, ArkUI_TextDecorationType)` THEN 设置 type 字段 | 正常 |
| AC-8.3 | WHEN 调用 `OH_ArkUI_DecorationStyle_SetColor(style, uint32_t)` THEN 设置 color 字段 | 正常 |
| AC-8.4 | WHEN 调用 `OH_ArkUI_DecorationStyle_SetTextDecorationStyle(style, ArkUI_TextDecorationStyle)` THEN 设置 style 字段 | 正常 |
| AC-8.5 | WHEN 调用 `OH_ArkUI_DecorationStyle_SetThicknessScale(style, float)` THEN 设置 thicknessScale，**不做范围检查或负值 clamp**（与值数组/对象式路径不同） | 边界 |
| AC-8.6 | WHEN 调用 `OH_ArkUI_DecorationStyle_SetEnableMultiType(style, bool)` THEN 设置 enableMultiType 字段 | 正常 |
| AC-8.7 | WHEN 任何 `OH_ArkUI_DecorationStyle_Set*` 第一参数为 nullptr THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |
| AC-8.8 | WHEN 通过 `OH_ArkUI_SpanStyle_SetDecorationStyle(spanStyle, decorationStyle)` (@since 24) THEN 拷贝 type/color/style/thicknessScale/enableMultiType 到 spanStyle->decorationStyle，设 styledKey=DECORATION | 正常 |
| AC-8.9 | WHEN `OH_ArkUI_SpanStyle_GetDecorationStyle` 在 styledKey != DECORATION 时调用 THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.9 | R-1~R-5, R-22 | 已有实现 | 单测 | `test/unittest/core/components_ng/text/` |
| AC-2.1~2.6 | R-6~R-10, R-23 | 已有实现 | 单测 | 同上 + `test/unittest/core/components/font/` |
| AC-3.1~3.5 | R-11~R-13 | 已有实现 | 单测 | `test/unittest/core/components_ng/text_field/` |
| AC-4.1~4.9 | R-14~R-19 | 已有实现 | 单测 | 同上 |
| AC-5.1~5.4 | R-20, R-21 | 已有实现 | 单测 | 同上 |
| AC-6.1~6.7 | R-24~R-29 | 已有实现 | 单测 | `test/unittest/interfaces/native_node_test.cpp` |
| AC-7.1~7.5 | R-30~R-33 | 已有实现 | 单测 | 同上 |
| AC-8.1~8.9 | R-34~R-40 | 已有实现 | 单测 | `test/unittest/interfaces/native_styled_string_test.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 SetDecoration (Text/Span) | 解析 type/color/style/thicknessScale 四字段；写入 FontStyle::{TextDecoration/TextDecorationColor/TextDecorationStyle/LineThicknessScale}；触发 propNeedReCreateParagraph_=true | Text 用 DecorationStyleInterface (@since 7) | AC-1.1, AC-1.2, AC-1.8 |
| R-2 | 行为 | decoration.type 缺失 | type 回退 theme `GetTextDecoration()` | js_text.cpp:849-856 | AC-1.4 |
| R-3 | 行为 | decoration.color 缺失 | 深色模式回退 theme GetTextColor；否则回退 theme GetTextDecorationColor | js_text.cpp:857-870 | AC-1.5 |
| R-4 | 行为 | decoration.style 缺失 | 默认 `TextDecorationStyle.SOLID` (DEFAULT_TEXT_DECORATION_STYLE) | js_text.cpp:871-874 | AC-1.6 |
| R-5 | 异常 | decoration 参数非对象 | 直接返回（不设置任何装饰字段） | js_text.cpp:839-841 | AC-1.7 |
| R-6 | 行为 | thicknessScale 设置 (Text/Span, API 20+) | LineThicknessScale 存为 float，下传给 Rosen decorationThicknessScale (constants_converter.cpp:666) | DecorationStyleInterface.thicknessScale @since 20 | AC-2.1, AC-2.5 |
| R-7 | 行为 | thicknessScale 缺失 | 默认 1.0f（不缩放） | 多处 value_or(1.0f) | AC-2.2 |
| R-8 | 异常 | thicknessScale 为负数 | JS bridge clamp 到 1.0f（js_text.cpp:875-879）；C-API 值数组与对象式路径同样 clamp；styled-string 路径**不** clamp | 负值处理三路不同 | AC-2.3 |
| R-9 | 行为 | LineThicknessScale > 1.0 | text_pattern.cpp:6716-6722 扩展 hit-test/bounds rect 的 boundsHeight += thickness | 仅 > 1.0 触发 | AC-2.4 |
| R-10 | 边界 | 静态范式 Text.decoration (API 23 static) | 静态 DecorationStyleInterface **无 thicknessScale 字段**，无法设置厚度（缺口） | styledString.static.d.ets:622-650 | AC-2.6 |
| R-11 | 行为 | TextInput/TextArea/Search decoration (API 12+) | 参数类型为 `TextDecorationOptions`（非 DecorationStyleInterface）；写入 TextFieldLayoutProperty | text_input.d.ts:1986 等 | AC-3.1 |
| R-12 | 边界 | TextInput/TextArea/Search thicknessScale (API 26+) | TextDecorationOptions.thicknessScale @since 26 dynamic / 26 static | common.d.ts:363 | AC-3.2 |
| R-13 | 行为 | Search decoration 委托 | Search 调用委托给内部 TextField 子节点的 TextFieldLayoutProperty | search_model_ng.cpp:2070-2181 | AC-3.3 |
| R-14 | 行为 | textCase=LowerCase | TextCase=LOWERCASE；显示文本转小写；存储 Content 不变 | text_layout_algorithm.cpp:1080-1083 | AC-4.1, AC-4.4 |
| R-15 | 行为 | textCase=UpperCase | TextCase=UPPERCASE；显示文本转大写；存储 Content 不变 | 同上 | AC-4.2, AC-4.4 |
| R-16 | 行为 | textCase=Normal | TextCase=NORMAL；按原样显示 | 同上 | AC-4.3 |
| R-17 | 边界 | textCase 复制/选择语义 | 复制/选择的是原始 content（未转换），保留语义 | 存储不变 | AC-4.5 |
| R-18 | 异常 | textCase 越界 | JSText: API<12 静默返回；API≥12 clamp 到 0。JSSpan: 不 clamp 也不设置（行为差异） | js_text.cpp:802-811 vs js_span.cpp:407-413 | AC-4.6, AC-4.7 |
| R-19 | 边界 | textCase 仅 Text/Span 暴露 | TextInput/TextArea/Search/Button 不暴露 textCase（仅展示型组件可用） | 逐组件适用性 | AC-4.8 |
| R-20 | 行为 | 多 TextDecoration 共存 | vector 存储 + ConvertTxtTextDecoration 位 OR 合并（constants_converter.cpp:316-343）；NONE 不贡献位 | vector<TextDecoration> | AC-5.1, AC-5.2 |
| R-21 | 边界 | 公开 JS API 单值设置 | bridge 将单个 type 包装为 `{value}` vector，每次 decoration() 调用仅设单值 | js_text.cpp:849-856 | AC-5.3 |
| R-22 | 行为 | Span decoration 写入 | 通过 ACE_UPDATE_SPAN_PROPERTY 写入 SpanNode（span_node.h:1054-1058），装饰项用 RE_LAYOUT 标志 | SpanNode 并行存储 | AC-1.9 |
| R-23 | 行为 | Span TextCase 用 RE_CREATE 标志 | Span 的 TextCase 项 change flag 为 RE_CREATE（段落重建），因大小写改变字形 | span_node.h:1060 | AC-4.1 |
| R-24 | 行为 | C-API NODE_TEXT_DECORATION set | value[0].i32 type + value[1]?.u32 color + value[2]?.i32 style + value[3]?.f32 thicknessScale；支持 TEXT/SPAN | style_modifier.cpp:13474 | AC-6.1 |
| R-25 | 边界 | C-API thickness @since 22 vs API 23 | 文档标注 @since 22，运行期门槛 API 23（VERSION_TWENTY_THREE）；API < 23 忽略 value[3] | 文档-代码差异 | AC-6.2 |
| R-26 | 边界 | C-API SPAN 忽略 thickness | SetDecoration 对 SPAN 硬编 1.0f（style_modifier.cpp:13505-13506）；GetDecoration 对 SPAN 返回 3 字段（无 thickness） | SPAN thickness 缺口 | AC-6.3 |
| R-27 | 行为 | C-API NODE_TEXT_CASE set | value[0].i32 取 ArkUI_TextCase 枚举（0..2）；支持 TEXT/SPAN | style_modifier.cpp:13607 | AC-6.4 |
| R-28 | 异常 | C-API type/style 越界 | type > 3 或 style > 4 → PARAM_INVALID (401) | style_modifier.cpp:13481,13484 | AC-6.5 |
| R-29 | 异常 | C-API textCase 越界 | value[0].i32 > 2 → PARAM_INVALID (401) | style_modifier.cpp:13614 | AC-6.6 |
| R-30 | 行为 | 对象式 C-API (@since 26) | NODE_TEXT_INPUT_DECORATION/NODE_TEXT_AREA_DECORATION 通过 item.object 接收 OH_ArkUI_DecorationStyleOptions*；SetComponentDecoration 解析 | style_modifier.cpp:13533 | AC-7.1, AC-7.2 |
| R-31 | 异常 | 对象式 item.object 为 null | 调用 ResetComponentDecoration 并返回 PARAM_INVALID (401) | style_modifier.cpp:13536-13538 | AC-7.3 |
| R-32 | 边界 | 对象式 thicknessScale 负值 | clamp < 0 到 DEFAULT_LINE_THICKNESS_SCALE (1.0f)，无 API 版本门槛 | style_modifier.cpp:13557 | AC-7.4 |
| R-33 | 边界 | 对象式 Get thread_local 单缓冲 | GetComponentDecoration 返回 static thread_local OH_ArkUI_DecorationStyleOptions，须先复制 | style_modifier.cpp:13576-13581 | AC-7.5 |
| R-34 | 行为 | styled-string C-API (@since 24) | OH_ArkUI_DecorationStyle 创建/设置 type/color/style/thicknessScale/enableMultiType | span_style_native_impl.cpp:1793-1888 | AC-8.1~8.6 |
| R-35 | 异常 | styled-string nullptr | 任何 Set*/Get* 第一参数为 nullptr 返回 PARAM_INVALID (401) | CHECK_NULL_RETURN | AC-8.7 |
| R-36 | 行为 | OH_ArkUI_SpanStyle_SetDecorationStyle | 拷贝 type/color/style/thicknessScale/enableMultiType 到 spanStyle->decorationStyle；设 styledKey=DECORATION | span_style_native_impl.cpp:990-1000 | AC-8.8 |
| R-37 | 异常 | styledKey != DECORATION 时 GetDecorationStyle | 返回 PARAM_INVALID (401) | span_style_native_impl.cpp:1008-1009 | AC-8.9 |
| R-38 | 边界 | styled-string thicknessScale 不 clamp | OH_ArkUI_DecorationStyle_SetThicknessScale 不做范围检查或负值 clamp（与值数组/对象式路径不同） | span_style_native_impl.cpp:1859-1865 | AC-8.5 |
| R-39 | 行为 | textCase Unicode 转换 | StringUtils::TransformStrCase u16string 特化版本用 std::towlower/std::towupper（é→É 等） | string_utils.cpp:761-780 | AC-4.9 |
| R-40 | 边界 | Button 非 Feat-02 消费者 | ButtonLayoutProperty 无 decoration/textCase/lineThicknessScale 项；Button SDK 也未暴露 | button_layout_property.h | AC-3.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~1.9 | 单测 | decoration 四字段解析与默认值回退 |
| VM-2 | R-6~R-10, AC-2.1~2.6 | 单测 | thicknessScale 设置 + Rosen 下传 + 静态缺口 |
| VM-3 | R-11~R-13, AC-3.1~3.5 | 单测 | TextInput/TextArea/Search TextDecorationOptions |
| VM-4 | R-14~R-19, R-39, AC-4.1~4.9 | 单测 | textCase 转换 + 存储不变 + Unicode |
| VM-5 | R-20, R-21, AC-5.1~5.4 | 单测 | 多装饰共存 + 位 OR + 单值 API |
| VM-6 | R-24~R-29, AC-6.1~6.7 | 单测/native_node_test | C-API 值数组装饰与大小写 |
| VM-7 | R-30~R-33, AC-7.1~7.5 | 单测 | 对象式 C-API @since 26 |
| VM-8 | R-34~R-38, AC-8.1~8.9 | 单测 | styled-string C-API @since 24 |
| VM-9 | 全量 | XTS/集成 | 端到端装饰与大小写渲染 |

---

## API 变更分析

### 新增 API

**ArkTS 动态 API：**

| API 签名 | 开放范围 | 入参概要 | 返回值 | @since | 关联 AC |
|----------|---------|----------|--------|--------|---------|
| `decoration(value: DecorationStyleInterface): TextAttribute` (Text/Span) | Public | type/color/style/thicknessScale (@since 20) | TextAttribute/SpanAttribute | 7 | AC-1.* |
| `decoration(value: TextDecorationOptions): TextInputAttribute` (TextInput/TextArea/Search) | Public | type/color/style/thicknessScale (@since 26) | 各 Attribute | 12 | AC-3.* |
| `textCase(value: TextCase): TextAttribute` (Text/Span) | Public | TextCase 枚举 (Normal/LowerCase/UpperCase) | TextAttribute/SpanAttribute | 7 | AC-4.* |

**逐组件适用性矩阵（动态 API）：**

| 组件 | decoration 参数类型 | textCase | 厚度支持 |
|------|---------------------|----------|----------|
| TextAttribute | DecorationStyleInterface | ✓ | thicknessScale @since 20 |
| SpanAttribute | DecorationStyleInterface | ✓ | thicknessScale @since 20 |
| TextInputAttribute | TextDecorationOptions | ✗ | thicknessScale @since 26 |
| TextAreaAttribute | TextDecorationOptions | ✗ | thicknessScale @since 26 |
| SearchAttribute | TextDecorationOptions | ✗ | thicknessScale @since 26 |
| ButtonAttribute | ✗（不暴露） | ✗ | ✗ |
| RichEditorAttribute | 通过 UpdateSpanStyle.decoration 字段 | 通过 span-style | 通过 span-style |

**类型定义：**

| 类型 | 定义 | 位置 |
|------|------|------|
| DecorationStyleInterface | {type: TextDecorationType; color?: ResourceColor; style?: TextDecorationStyle; thicknessScale?: number} | styled_string.d.ts:920-977 |
| TextDecorationOptions | {type: TextDecorationType; color?: ResourceColor; style?: TextDecorationStyle; thicknessScale?: number} | common.d.ts:316-364 |
| TextDecorationType | enum {None=0, Underline=1, Overline=2, LineThrough=3} | enums.d.ts:5949 |
| TextDecorationStyle | enum {SOLID=0, DOUBLE=1, DOTTED=2, DASHED=3, WAVY=4} | enums.d.ts:8761 |
| TextCase | enum {Normal=0, LowerCase=1, UpperCase=2} | enums.d.ts:6113 |

**C-API (NDK)：**

| 属性枚举 | 值 | 格式 | @since | 支持节点 | 关联 AC |
|----------|-----|------|--------|----------|---------|
| NODE_TEXT_DECORATION | 133 | value[0].i32 type + value[1]?.u32 color + value[2]?.i32 style + value[3]?.f32 thickness (@since 22/23) | 12 | TEXT/SPAN | AC-6.1~6.3 |
| NODE_TEXT_CASE | 134 | value[0].i32 (ArkUI_TextCase 0..2) | 12 | TEXT/SPAN | AC-6.4 |
| NODE_TEXT_INPUT_DECORATION | 7050 | .object = OH_ArkUI_DecorationStyleOptions* | 26 | TEXT_INPUT | AC-7.1 |
| NODE_TEXT_AREA_DECORATION | 8047 | .object = OH_ArkUI_DecorationStyleOptions* | 26 | TEXT_AREA | AC-7.2 |

**样式字符串 C-API (@since 24)：**

| 函数 | 签名 | 关联 AC |
|------|------|---------|
| OH_ArkUI_DecorationStyle_Create | () -> OH_ArkUI_DecorationStyle* | AC-8.1 |
| OH_ArkUI_DecorationStyle_SetTextDecorationType | (style, ArkUI_TextDecorationType) -> ArkUI_ErrorCode | AC-8.2 |
| OH_ArkUI_DecorationStyle_SetColor | (style, uint32_t) -> ArkUI_ErrorCode | AC-8.3 |
| OH_ArkUI_DecorationStyle_SetTextDecorationStyle | (style, ArkUI_TextDecorationStyle) -> ArkUI_ErrorCode | AC-8.4 |
| OH_ArkUI_DecorationStyle_SetThicknessScale | (style, float) -> ArkUI_ErrorCode | AC-8.5 |
| OH_ArkUI_DecorationStyle_SetEnableMultiType | (style, bool) -> ArkUI_ErrorCode | AC-8.6 |
| OH_ArkUI_SpanStyle_SetDecorationStyle | (spanStyle, const OH_ArkUI_DecorationStyle*) -> void | AC-8.8 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无变更/废弃 API | — |

---

## 接口规格

### 接口定义

**decoration (Text/Span)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `decoration(value: DecorationStyleInterface): TextAttribute` |
| 返回值 | TextAttribute / SpanAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.type | TextDecorationType | 是 | theme GetTextDecoration() | None/Underline/Overline/LineThrough |
| value.color | ResourceColor | 否 | 深色 mode→theme GetTextColor；否则→theme GetTextDecorationColor | ResourceColor = Color\|number\|string\|Resource |
| value.style | TextDecorationStyle | 否 | SOLID (@since 12) | SOLID/DOUBLE/DOTTED/DASHED/WAVY |
| value.thicknessScale | number | 否 | 1.0 (@since 20) | 负数 clamp 到 1.0；范围 [0, +∞) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | type/color/style/thicknessScale 齐全 | 写入 FontStyle 组，触发段落重建 | AC-1.1, AC-1.2 |
| 2 | type=None 或 undefined | 清除装饰 | AC-1.3 |
| 3 | 字段缺失 | 各字段回退默认 | AC-1.4~1.6 |
| 4 | 非对象参数 | 直接返回 | AC-1.7 |

---

**decoration (TextInput/TextArea/Search)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `decoration(value: TextDecorationOptions): TextInputAttribute` |
| 返回值 | TextInputAttribute / TextAreaAttribute / SearchAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.type | TextDecorationType | 是 | — | 同上 |
| value.color | ResourceColor | 否 | — | 同上 |
| value.style | TextDecorationStyle | 否 | SOLID | @since 12 |
| value.thicknessScale | number | 否 | 1.0 | @since 26 dynamic / 26 static |

---

**textCase**

| 属性 | 值 |
|------|-----|
| 函数签名 | `textCase(value: TextCase): TextAttribute` |
| 返回值 | TextAttribute / SpanAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | TextCase | 是 | Normal | Normal/LowerCase/UpperCase；越界 JSText API<12 静默，API≥12 clamp 0；JSSpan 不 clamp |

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 12**: decoration 参数类型从匿名 object 升级为 `DecorationStyleInterface`/`TextDecorationOptions`；style 字段正式可用
  - **API 20**: DecorationStyleInterface 新增 thicknessScale 字段（Text/Span）
  - **API 22/23**: C-API NODE_TEXT_DECORATION value[3].f32 thicknessScale（文档 @since 22，运行期门槛 API 23）
  - **API 23 static**: 静态范式 decoration/textCase（**静态 DecorationStyleInterface 无 thicknessScale**，缺口）
  - **API 24**: styled-string C-API OH_ArkUI_DecorationStyle_*
  - **API 26**: TextDecorationOptions 新增 thicknessScale（TextInput/TextArea/Search）；对象式 C-API NODE_TEXT_INPUT_DECORATION/NODE_TEXT_AREA_DECORATION
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（ArkTS decoration/textCase）；API 12（C-API NODE_TEXT_*）；API 22/23（C-API thickness）；API 24（styled-string）；API 26（对象式 + TextInput/TextArea thickness）
- **API 版本号策略:** @since 7 基础；@since 12/20/22/23/24/26 标注新增；param-level @since 标注字段扩展

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| 两套 decoration 参数类型 | Text/Span 用 DecorationStyleInterface (thicknessScale @since 20)；TextInput/TextArea/Search 用 TextDecorationOptions (thicknessScale @since 26) | AC-1.*, AC-3.* |
| lineThicknessScale 内部 vs thicknessScale 公开 | 无公开 lineThicknessScale 方法；通过 decoration() 参数对象 thicknessScale 字段设置；静态范式缺口 | AC-2.6 |
| textCase 仅 Text/Span | 编辑组件不暴露，仅展示型组件可用 | AC-4.8 |
| Button 非 Feat-02 消费者 | ButtonLayoutProperty 无 decoration/textCase 项 | AC-3.5 |
| 多装饰共存 | vector + 位 OR 合并；但公开 API 单值设置 | AC-5.1, AC-5.3 |
| textCase 仅转显示 | 存储 Content 不变，保留复制/选择语义 | AC-4.4, AC-4.5 |
| C-API 两套表面 + 版本/负值不一致 | 值数组 vs 对象式；@since 22 vs API 23；SPAN 忽略 thickness；负值三路不同 | AC-6.2, AC-6.3, AC-7.4, AC-8.5 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | decoration/textCase 设置 + 标记脏 < 1μs；同帧多字段仅触发一次段落重建 | benchmark | — |
| 内存 | TextDecoration 使用 vector<TextDecoration> 仅在设置时分配；Color/Style/TextCase 使用 std::optional | hidumper | — |
| 可靠性 | textCase 转换不修改原 Content，复制/选择语义保留 | 集成测试 | — |

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
| 无障碍 | 是 | 装饰与大小写影响可读性但无障碍语义由组件提供 | — |
| 大字体 | 否 | 装饰与大小写不受系统字体缩放影响（thicknessScale 独立于 fpScale） | — |
| 深色模式 | 是 | decoration.color 缺失时深色模式回退 theme GetTextColor | AC-1.5 |
| 多窗口/分屏 | 否 | 装饰与大小写不受窗口尺寸影响 | — |
| 多用户 | 否 | 无用户态差异 | — |
| 版本升级 | 是 | API 12/20/22/23/24/26 版本差异须通过 API 版本守护 | AC-2.1, AC-2.6, AC-6.2, AC-7.1, AC-8.1 |
| 生态兼容 | 是 | C-API 多通道（值数组/对象式/styled-string）应与 ArkTS 一致 | AC-6.*, AC-7.*, AC-8.* |

---

## 行为场景

```gherkin
Feature: 文本装饰与大小写
  作为 应用开发者
  我想要 通过声明式 API 与 C-API 控制文本装饰（类型/颜色/样式/厚度）与大小写转换
  以便 实现复合文本表现

  # ─── decoration 基础 ─────────────────────────────

  Scenario: 设置下划线
    Given 一个 Text 组件
    When 调用 .decoration({type: TextDecorationType.Underline, color: Color.Red, style: TextDecorationStyle.SOLID})
    Then TextDecoration={UNDERLINE}, TextDecorationColor=Red, TextDecorationStyle=SOLID
    And propNeedReCreateParagraph_=true

  Scenario: decoration 字段缺失回退默认
    Given 一个 Text 组件
    When 调用 .decoration({type: TextDecorationType.Underline})
    Then color 回退 theme GetTextDecorationColor（深色模式用 GetTextColor）
    And style 默认 SOLID

  Scenario: decoration 非对象参数
    Given 一个 Text 组件
    When 调用 .decoration(123)
    Then 直接返回，不设置任何装饰字段

  Scenario: Span decoration 写入 SpanNode
    Given 一个 Span 组件
    When 调用 .decoration({type: LineThrough})
    Then 通过 ACE_UPDATE_SPAN_PROPERTY 写入 SpanNode
    And 装饰项用 RE_LAYOUT 标志

  # ─── thicknessScale ──────────────────────────────

  Scenario: 设置厚度比例 (Text, API 20+)
    Given 目标 API 版本 >= 20
    And 一个 Text 组件
    When 调用 .decoration({type: Underline, thicknessScale: 2.0})
    Then LineThicknessScale=2.0f
    And 渲染时 decorationThicknessScale=2.0 下传 Rosen
    And hit-test boundsHeight += 2.0

  Scenario: thicknessScale 负值 clamp
    Given 一个 Text 组件
    When 调用 .decoration({type: Underline, thicknessScale: -1.0})
    Then JS bridge clamp 到 1.0f

  Scenario: 静态范式无 thicknessScale（缺口）
    Given 目标 API 版本 >= 23 static
    And 一个静态 Text 组件
    When 尝试 .decoration({type: Underline, thicknessScale: 2.0})
    Then 静态 DecorationStyleInterface 无 thicknessScale 字段，无法设置

  Scenario: TextInput thicknessScale (API 26+)
    Given 目标 API 版本 >= 26
    And 一个 TextInput 组件
    When 调用 .decoration({type: Underline, thicknessScale: 1.5})
    Then 厚度字段生效（TextDecorationOptions.thicknessScale @since 26）

  # ─── textCase ────────────────────────────────────

  Scenario: 设置大写转换
    Given 一个 Text 组件内容为 "hello"
    When 调用 .textCase(TextCase.UpperCase)
    Then 显示文本为 "HELLO"
    And 存储的 Content 仍为 "hello"（不变）

  Scenario: textCase 复制语义保留
    Given 一个 Text 组件已 .textCase(TextCase.UpperCase)
    When 用户复制显示文本
    Then 复制的是原始 content（未转换）

  Scenario: textCase Unicode 转换
    Given 一个 Text 组件内容为 "café"
    When 调用 .textCase(TextCase.UpperCase)
    Then 显示文本为 "CAFÉ"（é→É via std::towupper）

  Scenario: textCase 越界（JSText vs JSSpan）
    Given 目标 API 版本 >= 12
    And 一个 Text 组件
    When 调用 .textCase(99)
    Then JSText clamp 到 0（NORMAL）
    Given 一个 Span 组件
    When 调用 .textCase(99)
    Then JSSpan 不 clamp 也不设置

  Scenario: textCase 仅 Text/Span 可用
    Given 一个 TextInput 组件
    When 尝试 .textCase(TextCase.UpperCase)
    Then 不支持（TextInputAttribute 未声明 textCase）

  # ─── 多装饰共存 ──────────────────────────────────

  Scenario: 下划线+删除线共存
    Given 一个 Text 组件设置 TextDecoration={UNDERLINE, LINE_THROUGH}
    When 渲染执行
    Then ConvertTxtTextDecoration 位 OR 合并
    And 同时绘制下划线与删除线

  Scenario: 公开 API 单值设置
    Given 一个 Text 组件
    When 调用 .decoration({type: Underline})
    Then bridge 包装为 {UNDERLINE} vector（单值）
    And 每次 decoration() 调用仅设单值

  # ─── C-API ──────────────────────────────────────

  Scenario: C-API 设置装饰
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_TEXT_DECORATION, {value[0].i32: 1, value[1].u32: 0xFFFF0000, value[2].i32: 2})
    Then type=UNDERLINE, color=Red, style=DOTTED

  Scenario: C-API thickness @since 22 vs API 23
    Given 目标 API 版本 = 22
    And 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_TEXT_DECORATION, {value[0].i32: 1, value[3].f32: 2.0})
    Then 文档标注 @since 22，但运行期门槛 API 23，value[3] 被忽略，thicknessScale=1.0
    Given 目标 API 版本 = 23
    When 调用同上
    Then thicknessScale=2.0 生效

  Scenario: C-API SPAN 忽略 thickness
    Given 一个 ARKUI_NODE_SPAN 节点
    When 调用 setAttribute(node, NODE_TEXT_DECORATION, {value[0].i32: 1, value[3].f32: 2.0})
    Then SPAN 路径硬编 1.0f，thicknessScale 被忽略
    And GetDecoration 返回 3 字段（无 thickness）

  Scenario: 对象式 C-API (@since 26)
    Given 一个 ARKUI_NODE_TEXT_INPUT 节点
    When 创建 OH_ArkUI_DecorationStyleOptions 并 SetType/SetColor/SetStyle/SetThicknessScale
    And 调用 setAttribute(node, NODE_TEXT_INPUT_DECORATION, {object: options})
    Then SetComponentDecoration 解析对象并分发到 textInputModifier.setTextInputDecoration

  Scenario: 对象式 thicknessScale 负值
    Given 一个 OH_ArkUI_DecorationStyleOptions 设置 thicknessScale=-1.0
    When 调用 setAttribute(textInput, NODE_TEXT_INPUT_DECORATION, {object})
    Then clamp 到 DEFAULT_LINE_THICKNESS_SCALE (1.0f)

  # ─── styled-string C-API (@since 24) ─────────────

  Scenario: 样式字符串装饰
    Given 一个 OH_ArkUI_DecorationStyle 对象
    When 调用 OH_ArkUI_DecorationStyle_SetTextDecorationType(style, ARKUI_TEXT_DECORATION_TYPE_UNDERLINE)
    And 调用 OH_ArkUI_DecorationStyle_SetThicknessScale(style, 2.0f)
    Then type=UNDERLINE, thicknessScale=2.0（不 clamp）

  Scenario: 样式字符串 nullptr 错误
    When 调用 OH_ArkUI_DecorationStyle_SetTextDecorationType(nullptr, ...)
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401)
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（覆盖 decoration/textCase/lineThicknessScale；不含 fontSize/fontColor/fontWeight/fontStyle/fontFamily（Feat-01）、letterSpacing/lineHeight/baselineOffset（Feat-03）、textShadow/fontFeature/fontVariations（Feat-04）、minFontSize/maxFontSize/minFontScale/maxFontScale（Feat-05））
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TextLayoutProperty FontStyle TextDecoration TextDecorationColor TextDecorationStyle TextCase LineThicknessScale"
  - repo: "openharmony/ace_engine"
    query: "ConvertTxtTextDecoration constants_converter decoration bitwise OR merge"
  - repo: "openharmony/ace_engine"
    query: "StringUtils TransformStrCase TextCase lowercase uppercase TransformStrCase u16string"
  - repo: "openharmony/ace_engine"
    query: "style_modifier.cpp SetDecoration GetDecoration ResetDecoration SetTextCase NODE_TEXT_DECORATION NODE_TEXT_CASE"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_DecorationStyle_SetTextDecorationType SetColor SetTextDecorationStyle SetThicknessScale native_styled_string_descriptor"
```

**关键文档：**
- 架构设计：`specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md`
- SDK 类型定义：`interface/sdk-js/api/@internal/component/ets/text.d.ts`、`styled_string.d.ts`、`common.d.ts`、`text_common.d.ts`、`enums.d.ts`
- C-API：`interfaces/native/native_node.h`、`interfaces/native/node_attributes/text_common.h`、`interfaces/native/native_styled_string_descriptor.h`
