# 特性规格

> Func-04-03-11-Feat-01 核心字体属性：固化 fontSize/fontColor/fontWeight(+变体字体重载)/fontStyle/fontFamily 五项核心字体通用属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 核心字体属性 (Core Font Attributes) |
| 特性编号 | Func-04-03-11-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 11/12/15/20/24 有行为变更或新增 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | fontSize/fontColor/fontWeight/fontStyle/fontFamily 五项核心字体属性行为规格 | SDK @since 7 已有 API，本次补录行为规格 |
| ADDED | fontWeight 变体字体重载（weight, FontSettingOptions）行为规格 | @since 12 新增 API 补录 |
| ADDED | EnableVariableFontWeight / VariableFontWeight / EnableDeviceFontWeightCategory 内部属性行为规格 | 渲染转换期互斥解析行为补录 |
| ADDED | C-API NODE_FONT_COLOR/SIZE/STYLE/WEIGHT/FAMILY + NODE_IMMUTABLE_FONT_WEIGHT 行为规格 | @since 12/15 C-API 补录 |
| ADDED | styled-string C-API OH_ArkUI_TextStyle_SetFont* 行为规格 | @since 24 C-API 补录 |
| ADDED | option-object C-API OH_ArkUI_FontConfigs/FontWeightConfigs 行为规格 | @since 24 C-API 补录 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: 设置文本字号

**作为** 应用开发者,
**我想要** 通过 `.fontSize(value)` 设置文本承载组件的字号,
**以便** 控制文字显示大小。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.fontSize(16)` THEN 文本字号为 16fp（number 默认单位 fp） | 正常 |
| AC-1.2 | WHEN 调用 `.fontSize('20vp')` THEN 文本字号为 20vp（string 带单位后缀解析） | 正常 |
| AC-1.3 | WHEN 调用 `.fontSize($r('app.size.text'))` THEN 文本字号为 Resource 解析后的 Dimension 值 | 正常 |
| AC-1.4 | WHEN 调用 `.fontSize(undefined)` THEN 字号重置为默认值（theme `text_font_size`） | 异常 |
| AC-1.5 | WHEN 调用 `.fontSize(-10)` THEN 解析失败/负值回退到 theme `text_font_size` 默认值（js_text.cpp:225-231 回退逻辑） | 异常 |
| AC-1.6 | WHEN 设置 Resource 类型字号且系统配置变更（如字体缩放） THEN 通过 RegisterResource("FontSize",...) 注册的监听触发重新解析，字号更新 | 正常 |
| AC-1.7 | WHEN 在 Text 组件设置 fontSize THEN 写入 TextLayoutProperty::FontStyle::FontSize，触发 PROPERTY_UPDATE_MEASURE + propNeedReCreateParagraph_=true，下帧段落重建 | 正常 |
| AC-1.8 | WHEN 在 Button 组件设置 fontSize THEN 写入 ButtonLayoutProperty::FontSize（PROPERTY_UPDATE_NORMAL），并重置内部 Text 子节点的 AdaptMinFontSize/AdaptMaxFontSize | 正常 |
| AC-1.9 | WHEN 在 Marquee 组件设置 fontSize THEN 写入 MarqueeLayoutProperty::FontSize 并设置 LPX_FONT_SIZE attribute | 正常 |

### US-2: 设置文本颜色

**作为** 应用开发者,
**我想要** 通过 `.fontColor(value)` 设置文本颜色,
**以便** 控制文字颜色表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.fontColor(Color.Red)` THEN 文本颜色为 Color 枚举对应的 0xARGB 值 | 正常 |
| AC-2.2 | WHEN 调用 `.fontColor(0xFFFF0000)` THEN 文本颜色为该 number 表示的 0xARGB 红色 | 正常 |
| AC-2.3 | WHEN 调用 `.fontColor('#FFFF0000')` THEN 文本颜色为该 string 解析的 0xARGB 红色 | 正常 |
| AC-2.4 | WHEN 调用 `.fontColor($r('app.color.text'))` THEN 文本颜色为 Resource 解析后的 Color 值 | 正常 |
| AC-2.5 | WHEN 调用 `.fontColor(undefined)` 或解析失败 THEN 调用 ResetTextColor 重置为默认值（BLACK @ 0.9 opacity） | 异常 |
| AC-2.6 | WHEN 在 Text 组件设置 fontColor THEN 通过 UpdateTextColorByRender 仅触发 PROPERTY_UPDATE_RENDER（非 MEASURE，性能优化），同步更新 RenderContext::ForegroundColor，设置 TextColorFlagByUser=true | 正常 |
| AC-2.7 | WHEN Resource 类型 fontColor 且配置变更 THEN 通过 RegisterResource("TextColor", resourceObject, textColor, true) 注册（第 4 参 true 表示 isMaterial），重新解析 | 正常 |
| AC-2.8 | WHEN fontColor 传入 LinearGradient/SolidColor 类型 THEN **不支持**（ResourceColor = Color\|number\|string\|Resource，不含渐变色），按解析失败处理 | 边界 |

### US-3: 设置静态字重

**作为** 应用开发者,
**我想要** 通过 `.fontWeight(value)` 设置文本字重,
**以便** 控制文字粗细。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.fontWeight(FontWeight.Bold)` THEN 文本字重为 Bold 枚举（≡700） | 正常 |
| AC-3.2 | WHEN 调用 `.fontWeight(700)` THEN number 输入：variableFontWeight=700，fontWeightEnum=ConvertStrToFontWeight("700")=W700 | 正常 |
| AC-3.3 | WHEN 调用 `.fontWeight('bold')` THEN string 输入：ParseFontWeight 匹配命名 → variableFontWeight=GetFontWeightNumericValue(BOLD)=700，fontWeightEnum=BOLD | 正常 |
| AC-3.4 | WHEN 调用 `.fontWeight('800')` THEN string 数字：variableFontWeight=800，fontWeightEnum=W800 | 正常 |
| AC-3.5 | WHEN 调用 `.fontWeight('unknown')` THEN 未知 string：variableFontWeight=IsNumber("unknown")?...:400，即回退 400，fontWeightEnum=NORMAL | 异常 |
| AC-3.6 | WHEN 调用 `.fontWeight($r('app.weight.x'))` (API 20+) THEN ResourceStr 类型（@since 20）解析为 string 后按 string 路径处理 | 正常 |
| AC-3.7 | WHEN 调用 fontWeight THEN **总是同时设置** VariableFontWeight(int) **和** FontWeight(enum)，由运行期 EnableVariableFontWeight 标志决定胜者（js_text.cpp:263-264 副作用） | 边界 |
| AC-3.8 | WHEN 未启用变体字体（EnableVariableFontWeight=false，默认）THEN 渲染转换期使用静态 FontWeight 派生的数字值 (ConvertTxtFontWeight+1)*100，并按 EnableDeviceFontWeightCategory 应用设备字重缩放 | 正常 |
| AC-3.9 | WHEN 设置 fontWeight 后未显式设置 EnableDeviceFontWeightCategory（Text 默认）THEN 应用 GetFontWeightScale() 缩放（constants_converter.cpp:621-623） | 正常 |

### US-4: 启用变体字体重载

**作为** 应用开发者,
**我想要** 通过 `.fontWeight(weight, {enableVariableFontWeight: true})` 启用变体字体精细控制,
**以便** 在变体字体上使用任意 100-900 的字重值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.fontWeight(550, {enableVariableFontWeight: true})` (API 12+) THEN 启用变体字体重载，VariableFontWeight=550，EnableVariableFontWeight=true | 正常 |
| AC-4.2 | WHEN EnableVariableFontWeight=true THEN 渲染转换期 (constants_converter.cpp:606-611) 使用 VariableFontWeight 数值覆盖静态 FontWeight 派生值，并 clamp 到 [100,900]，越界回退 400 | 边界 |
| AC-4.3 | WHEN EnableVariableFontWeight=true **且** 未显式设置 EnableDeviceFontWeightCategory（Text 默认）THEN **不应用** GetFontWeightScale() 设备字重缩放（constants_converter.cpp:621-623 条件 `!GetEnableVariableFontWeight()`） | 边界 |
| AC-4.4 | WHEN 调用 `.fontWeight(550)`（不带 options）THEN 默认 enableVariableFontWeight=false，仅设置 VariableFontWeight=550 + FontWeight=W550，但运行期按静态路径处理 | 正常 |
| AC-4.5 | WHEN 在 Span/SymbolGlyph/SymbolSpan 组件使用 fontWeight 第二重载 THEN 使用 `FontWeightConfigs`（非 `FontSettingOptions`），含 enableVariableFontWeight + enableDeviceFontWeightCategory 两字段 | 边界 |
| AC-4.6 | WHEN 变体字体重载仅在 TextAttribute 拥有；在 Button/Marquee/Span 等组件不暴露 THEN 仅 Text 组件可启用变体字体；其它组件仅使用静态 FontWeight 路径 | 边界 |

### US-5: 设置斜体样式

**作为** 应用开发者,
**我想要** 通过 `.fontStyle(value)` 设置文本斜体,
**以便** 控制文字倾斜表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.fontStyle(FontStyle.Normal)` THEN ItalicFontStyle=NORMAL，文本不倾斜 | 正常 |
| AC-5.2 | WHEN 调用 `.fontStyle(FontStyle.Italic)` THEN ItalicFontStyle=ITALIC，文本倾斜 | 正常 |
| AC-5.3 | WHEN 调用 `.fontStyle(-1)`（越界，API < 12）THEN 静默返回（不设置） | 异常 |
| AC-5.4 | WHEN 调用 `.fontStyle(99)`（越界，API ≥ 12）THEN clamp 到 0（NORMAL） | 异常 |
| AC-5.5 | WHEN 在 Marquee 组件尝试设置 fontStyle THEN **不支持**（MarqueeLayoutProperty 无 FontStyle 项；MarqueeAttribute 也未声明 fontStyle 方法） | 边界 |

### US-6: 设置字体族

**作为** 应用开发者,
**我想要** 通过 `.fontFamily(value)` 设置字体族,
**以便** 使用指定字体（含注册字体与系统字体）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.fontFamily('HarmonyOS Sans')` THEN FontFamily 存储为 `["HarmonyOS Sans"]` 单元素 vector | 正常 |
| AC-6.2 | WHEN 调用 `.fontFamily('HarmonyOS Sans, serif, monospace')` THEN 通过 ConvertStrToFontFamilies（utils.h:322-331）按逗号切分为 `["HarmonyOS Sans", "serif", "monospace"]`，按优先级应用 | 正常 |
| AC-6.3 | WHEN 调用 `.fontFamily($r('app.font.family'))` THEN 通过 ParseJsFontFamilies（js_view_abstract.cpp:7643-7682）解析 Resource，返回单元素 vector | 正常 |
| AC-6.4 | WHEN 调用 `.fontFamily(undefined)` 或空字符串 THEN 重置为默认 theme fontFamilies；非标准系统回退 `"sans-serif"` | 异常 |
| AC-6.5 | WHEN 设置 fontFamily 后某一字体在系统中未注册 THEN 按优先级回退到 vector 中下一个字体名 | 正常 |
| AC-6.6 | WHEN 通过 `fontFamily` 引用 `loadFontSync` 注册的自定义字体 THEN 需先调用字体注册 API（@ohos.font.loadFontSync），再设置 fontFamily | 正常 |
| AC-6.7 | WHEN 在 Text 组件设置 fontFamily THEN 写入 TextLayoutProperty::FontStyle::FontFamily (std::vector<std::string>)，触发 propNeedReCreateParagraph_=true | 正常 |

### US-7: 通过 font() 聚合设置

**作为** 应用开发者,
**我想要** 通过 `.font({fontSize, fontWeight, fontFamily, fontStyle})` 一次性设置字体属性,
**以便** 减少代码量并保持原子性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.font({fontSize: 16, fontWeight: FontWeight.Bold, fontFamily: 'serif', fontStyle: FontStyle.Italic})` THEN 等效于分别调用各项 setter | 正常 |
| AC-7.2 | WHEN font() 中某字段缺失 THEN 该字段回退到 TextTheme::GetTextStyle() 默认值（js_text.cpp:148-151 seed 逻辑） | 正常 |
| AC-7.3 | WHEN 调用 `.font(font, {enableVariableFontWeight: true})`（2nd arg） THEN 通过 SetEnableVariableFontWeight(true) 启用变体字重 | 正常 |

### US-8: 通过 C-API 设置字体属性

**作为** NDK 开发者,
**我想要** 通过 `setAttribute(NODE_FONT_*, item)` 设置文本字体属性,
**以便** 在 C 代码中控制文本表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `setAttribute(node, NODE_FONT_SIZE, {value[0].f32: 16.0})` THEN 设置 fontSize=16fp，支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON 节点 | 正常 |
| AC-8.2 | WHEN 调用 `setAttribute(node, NODE_FONT_COLOR, {value[0].u32: 0xFFFF0000})` THEN 设置 fontColor=红色 0xARGB，支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON | 正常 |
| AC-8.3 | WHEN 调用 `setAttribute(node, NODE_FONT_WEIGHT, {value[0].i32: 4})` THEN 设置 fontWeight=ARKUI_FONT_WEIGHT_BOLD（枚举 0..14），支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON | 正常 |
| AC-8.4 | WHEN 调用 `setAttribute(node, NODE_FONT_STYLE, {value[0].i32: 1})` THEN 设置 fontStyle=ITALIC，支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA，**不支持 BUTTON**（缺口） | 边界 |
| AC-8.5 | WHEN 调用 `setAttribute(node, NODE_FONT_FAMILY, {string: "serif, monospace"})` THEN 设置 fontFamily 切分数组（TextArea 传 raw string），支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA；**BUTTON 静默 no-op**（缺口） | 边界 |
| AC-8.6 | WHEN NODE_FONT_SIZE 传入 `item.size == 0` 或 `value[0].f32 <= 0` THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |
| AC-8.7 | WHEN NODE_FONT_STYLE 传入 `value[0].i32 < 0` 或 `> ARKUI_FONT_STYLE_ITALIC(1)` THEN 返回 PARAM_INVALID (401) | 异常 |
| AC-8.8 | WHEN NODE_FONT_WEIGHT 传入 `value[0].i32 < 0` 或 `> ARKUI_FONT_WEIGHT_REGULAR(14)` THEN 返回 PARAM_INVALID (401) | 异常 |
| AC-8.9 | WHEN 在不支持节点类型（如 TEXT_EDITOR）调用 NODE_FONT_* THEN 返回 PARAM_INVALID (401)（default 分支） | 异常 |
| AC-8.10 | WHEN 调用 `setAttribute(node, NODE_IMMUTABLE_FONT_WEIGHT, {value[0].i32: 4})` (@since 15) THEN 设置不受系统字体权重设置影响的 fontWeight，**仅 TEXT 节点支持 set**，其它节点返回 PARAM_INVALID | 边界 |
| AC-8.11 | WHEN 调用 `getAttribute(node, NODE_IMMUTABLE_FONT_WEIGHT)` 或 `resetAttribute` THEN 复用 GetFontWeight/ResetFontWeight 处理器，覆盖 TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON（set/get 非对称） | 边界 |
| AC-8.12 | WHEN 连续调用 getAttribute 多次 THEN 共用 thread_local 单缓冲（g_numberValues/g_attributeItem），须先复制再调下一次 Get，否则被覆盖 | 边界 |

### US-9: 通过样式字符串 C-API 设置（@since 24）

**作为** NDK 开发者,
**我想要** 通过 `OH_ArkUI_TextStyle_SetFont*` 在样式字符串上设置字体属性,
**以便** 在 StyledString 场景精细控制文本样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 `OH_ArkUI_TextStyle_SetFontColor(style, 0xFFFF0000)` (@since 24) THEN 设置 textStyle.fontColor=0xFFFF0000，返回 ARKUI_ERROR_CODE_NO_ERROR | 正常 |
| AC-9.2 | WHEN 调用 `OH_ArkUI_TextStyle_SetFontFamily(style, "serif")` THEN 设置 textStyle.fontFamily=std::string("serif") | 正常 |
| AC-9.3 | WHEN 调用 `OH_ArkUI_TextStyle_SetFontSize(style, 16.0f)` THEN 设置 textStyle.fontSize=16.0f | 正常 |
| AC-9.4 | WHEN 调用 `OH_ArkUI_TextStyle_SetFontWeight(style, 700)` THEN 设置 textStyle.fontWeight=700（**数字 100..900，非枚举**） | 正常 |
| AC-9.5 | WHEN 调用 `OH_ArkUI_TextStyle_SetFontStyle(style, ARKUI_FONT_STYLE_ITALIC)` THEN 设置 textStyle.fontStyle=ITALIC | 正常 |
| AC-9.6 | WHEN 任何 `OH_ArkUI_TextStyle_SetFont*` 第一参数 textStyle 为 nullptr THEN 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | 异常 |
| AC-9.7 | WHEN `OH_ArkUI_TextStyle_GetFontFamily` 缓冲区不足 THEN 返回 ARKUI_ERROR_CODE_BUFFER_SIZE_ERROR (106202) | 异常 |

### US-10: 通过 option-object C-API 配置变体字重（@since 24）

**作为** NDK 开发者,
**我想要** 通过 `OH_ArkUI_FontConfigs`/`OH_ArkUI_FontWeightConfigs` 配置变体字重与设备字重分类,
**以便** 在 Span 节点上精细控制字体权重行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `OH_ArkUI_FontWeightConfigs_Create()` (@since 24) THEN 返回新建的 OH_ArkUI_FontWeightConfigs* 对象 | 正常 |
| AC-10.2 | WHEN 调用 `OH_ArkUI_FontWeightConfigs_SetEnableVariableFontWeight(option, true)` THEN 设置 enableVariableFontWeight=true（默认 false） | 正常 |
| AC-10.3 | WHEN 调用 `OH_ArkUI_FontWeightConfigs_SetEnableDeviceFontWeightCategory(option, true)` THEN 设置 enableDeviceFontWeightCategory=true（默认 true） | 正常 |
| AC-10.4 | WHEN 调用 `OH_ArkUI_FontConfigs_Create()` + `OH_ArkUI_FontConfigs_SetFontWeightConfigs(fontConfig, weightConfig)` THEN 关联子配置对象 | 正常 |
| AC-10.5 | WHEN 通过 `setAttribute(span, NODE_SPAN_FONT_WEIGHT, {value[0].i32: 550, object: fontWeightConfigs})` THEN ProcessFontWeightConfigs 执行：若 isEnableVariableFontWeightSet → setSpanEnableVariableFontWeight + setSpanVariableFontWeight；否则 setSpanEnableVariableFontWeight(false) | 正常 |
| AC-10.6 | WHEN NODE_SPAN_FONT_WEIGHT 的 value[0].i32 传入 `< 100` 或 `> 900` THEN 返回 PARAM_INVALID（**数字编码，非枚举**） | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.9 | R-1, R-2, R-7, R-25~R-27 | 已有实现 | 单测 | `test/unittest/core/components_ng/text/` |
| AC-2.1~2.8 | R-3, R-4, R-8, R-28 | 已有实现 | 单测 | 同上 |
| AC-3.1~3.9 | R-5, R-9, R-10, R-29 | 已有实现 | 单测 | 同上 |
| AC-4.1~4.6 | R-11, R-12, R-30 | 已有实现 | 单测 | `test/unittest/core/components/font/` |
| AC-5.1~5.5 | R-13, R-14 | 已有实现 | 单测 | 同上 |
| AC-6.1~6.7 | R-15, R-16, R-31 | 已有实现 | 单测 | 同上 |
| AC-7.1~7.3 | R-17 | 已有实现 | 单测 | 同上 |
| AC-8.1~8.12 | R-18~R-24, R-32~R-34 | 已有实现 | 单测 | `test/unittest/interfaces/native_node_test.cpp:5370-5676` |
| AC-9.1~9.7 | R-35~R-38 | 已有实现 | 单测 | `test/unittest/interfaces/native_styled_string_test.cpp` |
| AC-10.1~10.6 | R-39~R-42 | 已有实现 | 单测 | 同上 |

---

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 SetFontSize | FontSize 存储为 Dimension（FP 单位），写入 TextLayoutProperty::FontStyle::FontSize，触发 PROPERTY_UPDATE_MEASURE + propNeedReCreateParagraph_=true | number 默认 fp 单位；string 带后缀；Resource 解析为 Dimension | AC-1.1~1.3, AC-1.7 |
| R-2 | 行为 | 在 Button/Marquee 设置 fontSize | 写入各自 LayoutProperty::FontSize（ButtonLayoutProperty 使用 PROPERTY_UPDATE_NORMAL；MarqueeLayoutProperty 使用 PROPERTY_UPDATE_MEASURE 并设 LPX_FONT_SIZE attribute），Button 同时重置内部 Text 子节点 AdaptMin/MaxFontSize | 逐组件存储路径不同 | AC-1.8, AC-1.9 |
| R-3 | 行为 | 调用 SetTextColor (fontColor) | 通过 UpdateTextColorByRender 仅触发 PROPERTY_UPDATE_RENDER（性能优化，不触发 MEASURE）；同步更新 RenderContext::ForegroundColor；设置 TextColorFlagByUser=true；调用 textPattern->UpdateFontColor | ResourceColor = Color\|number\|string\|Resource（不含渐变色） | AC-2.1~2.4, AC-2.6 |
| R-4 | 行为 | fontColor Resource 类型 + 配置变更 | 通过 RegisterResource("TextColor", resourceObject, textColor, true) 注册监听（第 4 参 true=isMaterial），配置变更时重新解析 | Material 资源策略生效 | AC-2.7 |
| R-5 | 行为 | 调用 SetFontWeight | FontWeight (enum) 与 VariableFontWeight (int) 同时设置（js_text.cpp:263-264 副作用）；运行期由 EnableVariableFontWeight 标志决定胜者 | 总是同时设置两者 | AC-3.1~3.7 |
| R-6 | 行为 | 渲染转换期 (constants_converter.cpp:601-626) | (1) Rosen::FontWeight = ConvertTxtFontWeight(静态 FontWeight)；(2) fontWeightValue = (静态 FontWeight 派生数字)；(3) if EnableVariableFontWeight → 覆盖为 VariableFontWeight，clamp [100,900]，越界→400；(4) 应用 EnableDeviceFontWeightCategory 三态缩放；(5) fontVariations wght=fontWeightValue | 渲染转换层才是真正决策点 | AC-3.8, AC-3.9, AC-4.2 |
| R-7 | 行为 | EnableVariableFontWeight=false（默认） | 使用静态 FontWeight 派生数字值；Text 默认未设 EnableDeviceFontWeightCategory 时应用 GetFontWeightScale() 缩放 | 默认行为 | AC-3.8, AC-3.9 |
| R-8 | 行为 | 调用 SetFontStyle | ItalicFontStyle 存储为 Ace::FontStyle（NORMAL/ITALIC），写入 FontStyle 组，触发 propNeedReCreateParagraph_=true | FONT_STYLES={NORMAL,ITALIC} 数组索引 | AC-5.1, AC-5.2 |
| R-9 | 行为 | 调用 SetFontFamily | FontFamily 存储为 std::vector<string>，string 输入按逗号切分（ConvertStrToFontFamilies）；Resource 输入通过 ParseJsFontFamilies 解析为单元素 vector；触发 propNeedReCreateParagraph_=true | 多字体按优先级应用 | AC-6.1~6.3, AC-6.7 |
| R-10 | 行为 | 调用 font() 聚合 | 先 seed theme 默认值，再解析 font 对象各字段，调用对应 setter；可选 2nd arg {enableVariableFontWeight} 调用 SetEnableVariableFontWeight | 字段缺失回退 theme | AC-7.1~7.3 |
| R-11 | 行为 | 启用变体字体重载 (API 12+) | fontWeight(weight, {enableVariableFontWeight: true}) → 设置 VariableFontWeight + EnableVariableFontWeight=true；运行期覆盖静态 FontWeight 派生值 | 仅 TextAttribute 拥有 | AC-4.1, AC-4.2 |
| R-12 | 边界 | EnableVariableFontWeight=true 且未设 EnableDeviceFontWeightCategory（Text 默认） | **不应用** GetFontWeightScale() 设备字重缩放（constants_converter.cpp:621-623 条件 `!GetEnableVariableFontWeight()`） | Text 默认三态 | AC-4.3 |
| R-13 | 边界 | Span/SymbolGlyph/SymbolSpan fontWeight 第二重载 | 使用 FontWeightConfigs（非 FontSettingOptions），含 enableVariableFontWeight + enableDeviceFontWeightCategory 两字段；与 Text 的 FontSettingOptions 类型不兼容 | 类型不可混用 | AC-4.5, AC-4.6 |
| R-14 | 异常 | fontStyle 越界 | API < 12：静默返回（不设置）；API ≥ 12：clamp 到 0（NORMAL） | FONT_STYLES 数组越界 | AC-5.3, AC-5.4 |
| R-15 | 行为 | fontFamily 解析失败或空 | 重置为 theme fontFamilies；非标准系统回退 "sans-serif" | text_styles.cpp:175-176 | AC-6.4 |
| R-16 | 行为 | 字体未注册 | 按 vector 优先级回退到下一字体名 | 多字体回退 | AC-6.5 |
| R-17 | 行为 | font() 字段缺失 | 缺失字段回退到 TextTheme::GetTextStyle() 默认值（fontSize/fontWeight/fontFamilies/fontStyle） | js_text.cpp:148-151 seed | AC-7.2 |
| R-18 | 行为 | C-API NODE_FONT_SIZE set | value[0].f32 写入 fontSize（fp）；支持 TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON；其它节点 default 分支返回 PARAM_INVALID | 不支持 TEXT_EDITOR | AC-8.1 |
| R-19 | 行为 | C-API NODE_FONT_COLOR set | value[0].u32 写入 fontColor（0xARGB）；按节点类型分发到各 modifier：TEXT→textModifier.setFontColor；SPAN→spanModifier.setSpanFontColor；TEXT_INPUT→textInputModifier.setTextInputFontColor；TEXT_AREA→textAreaModifier；BUTTON→buttonModifier.setButtonFontColorPtr | 5 节点支持 | AC-8.2 |
| R-20 | 行为 | C-API NODE_FONT_WEIGHT set | value[0].i32 取 ArkUI_FontWeight 枚举（0..14）；分发到各 modifier（Button 用 setButtonFontWeightEnum）；越界返回 PARAM_INVALID | 枚举编码（区别于 SPAN 数字） | AC-8.3 |
| R-21 | 边界 | C-API NODE_FONT_STYLE 不支持 BUTTON | SetFontStyle/GetFontStyle/ResetFontStyle 均无 BUTTON 分支；BUTTON 调用返回 PARAM_INVALID（set）/ size=0（get）/ no-op（reset） | C-API 缺口 | AC-8.4 |
| R-22 | 边界 | C-API NODE_FONT_FAMILY set 对 BUTTON 静默 no-op | if/else 链无 default 分支，BUTTON 落入无操作的 fall-through，返回 ERROR_CODE_NO_ERROR (0) | C-API 缺口 | AC-8.5 |
| R-23 | 边界 | C-API NODE_FONT_FAMILY reset 不覆盖 SPAN | ResetTextFontFamily (style_modifier.cpp:11207-11217) 仅处理 TEXT_INPUT/TEXT/TEXT_AREA，SPAN reset 静默 no-op | C-API 缺口 | AC-8.5 |
| R-24 | 边界 | C-API NODE_IMMUTABLE_FONT_WEIGHT (@since 15) | set 仅支持 TEXT（其它返回 PARAM_INVALID）；get/reset 复用 GetFontWeight/ResetFontWeight 处理器，覆盖 TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON（set/get 非对称） | set 与 get/reset 节点支持不一致 | AC-8.10, AC-8.11 |
| R-25 | 异常 | C-API NODE_FONT_SIZE item.size==0 或 value[0].f32 ≤ 0 | 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | style_modifier.cpp:5235-5264 校验 | AC-8.6 |
| R-26 | 异常 | C-API NODE_FONT_STYLE value[0].i32 越界 (< 0 或 > 1) | 返回 PARAM_INVALID (401) | style_modifier.cpp:5282-5310 | AC-8.7 |
| R-27 | 异常 | C-API NODE_FONT_WEIGHT value[0].i32 越界 (< 0 或 > 14) | 返回 PARAM_INVALID (401) | style_modifier.cpp:5169-5201 | AC-8.8 |
| R-28 | 边界 | ResourceColor 不含 LinearGradient/SolidColor | units.d.ts:1947 定义为 Color\|number\|string\|Resource；渐变色不支持，按解析失败处理 | 实际定义 | AC-2.8 |
| R-29 | 行为 | EnableDeviceFontWeightCategory 三态 | 未设置(has_value==false)：Text 默认，缩放静态权重除非 variable 启用；set true：Span/styledString，即使 variable 启用也缩放；set false：不缩放 | 可选 bool 三态 | AC-3.9, AC-4.3 |
| R-30 | 边界 | Marquee 无 fontStyle | MarqueeLayoutProperty 无 FontStyle 项；MarqueeAttribute 也未声明 fontStyle 方法 | 逐组件适用性 | AC-5.5 |
| R-31 | 行为 | loadFontSync 注册自定义字体 | 需先调用 @ohos.font.loadFontSync 注册，再通过 fontFamily 引用 | 注册顺序 | AC-6.6 |
| R-32 | 行为 | styled-string C-API OH_ArkUI_TextStyle_SetFont* (@since 24) | 直接赋值到 OH_ArkUI_TextStyle 结构体字段（fontColor uint32/fontFamily string/fontSize float/fontWeight uint32/fontStyle enum），返回 NO_ERROR 或 PARAM_INVALID | @since 24（非文件头 14） | AC-9.1~9.5 |
| R-33 | 异常 | styled-string textStyle 为 nullptr | 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401) | CHECK_NULL_RETURN | AC-9.6 |
| R-34 | 异常 | OH_ArkUI_TextStyle_GetFontFamily 缓冲区不足 | 返回 ARKUI_ERROR_CODE_BUFFER_SIZE_ERROR (106202) | bufferSize < contentLength+1 | AC-9.7 |
| R-35 | 行为 | option-object C-API (@since 24) | OH_ArkUI_FontConfigs/FontWeightConfigs 创建/设置/获取，关联后通过 NODE_SPAN_FONT_WEIGHT 的 .object 字段传入 | 仅作用于 SPAN 路径 | AC-10.1~10.4 |
| R-36 | 行为 | NODE_SPAN_FONT_WEIGHT 编码为数字 100..900 | value[0].i32 取数字（非 ArkUI_FontWeight 枚举），通过 ConvertSpanFontWeightValueToEnum 转换为枚举后 setSpanFontWeight | 编码区别于 NODE_FONT_WEIGHT | AC-10.5 |
| R-37 | 边界 | option-object 控制 Span 变体字重 | ProcessFontWeightConfigs：若 isEnableVariableFontWeightSet → setSpanEnableVariableFontWeight(enable) + setSpanVariableFontWeight(weight)；否则 setSpanEnableVariableFontWeight(false)。若 isEnableDeviceFontWeightCategorySet → setSpanEnableDeviceFontWeightCategory(enable)；否则 setSpanEnableDeviceFontWeightCategory(true) | Span 默认 device category=true | AC-10.5 |
| R-38 | 异常 | NODE_SPAN_FONT_WEIGHT value[0].i32 越界 (< 100 或 > 900) | 返回 PARAM_INVALID (401) | style_modifier.cpp:15052 | AC-10.6 |
| R-39 | 边界 | C-API Get 返回 thread_local 单缓冲 | g_numberValues[20]/g_attributeItem 为 thread_local static，多次 Get 须先复制 | style_modifier.cpp:245-248 | AC-8.12 |
| R-40 | 行为 | C-API NODE_FONT_FAMILY TextArea 传 raw string | TextArea 分支调用 textAreaModifier.setTextAreaFontFamily(handle, item->string) 传 raw string（非切分数组）；其它节点传切分后的 char*[] | TextArea 特殊 | AC-8.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, R-2, AC-1.1~1.9 | 单测 | fontSize 各类型解析与逐组件存储路径 |
| VM-2 | R-3, R-4, AC-2.1~2.8 | 单测 | fontColor ResourceColor 子形式与 Material 资源策略 |
| VM-3 | R-5, R-6, R-7, AC-3.1~3.9 | 单测 | fontWeight 双路径与运行期互斥解析 |
| VM-4 | R-11, R-12, R-29, AC-4.1~4.6 | 单测 | 变体字体重载 + EnableDeviceFontWeightCategory 三态 |
| VM-5 | R-8, R-14, AC-5.1~5.5 | 单测 | fontStyle 越界处理与 Marquee 不支持 |
| VM-6 | R-9, R-15, R-16, AC-6.1~6.7 | 单测 | fontFamily 切分与回退 |
| VM-7 | R-10, R-17, AC-7.1~7.3 | 单测 | font() 聚合与默认值 seed |
| VM-8 | R-18~R-27, R-39, R-40, AC-8.1~8.12 | 单测/native_node_test.cpp | C-API 各枚举分发与缺口 |
| VM-9 | R-32~R-34, AC-9.1~9.7 | 单测 | styled-string C-API @since 24 |
| VM-10 | R-35~R-38, AC-10.1~10.6 | 单测 | option-object C-API @since 24 |
| VM-11 | 全量 | XTS/集成 | 端到端字体属性渲染正确 |

---

## API 变更分析

### 新增 API

> 本特性为已有实现补录，下表为现存 API 的清单。

**ArkTS 动态 API (TextAttribute)：**

| API 签名 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|----------|--------|-----------|----------|---------|
| `fontColor(value: ResourceColor)` | Public | ResourceColor = Color\|number\|string\|Resource | TextAttribute | N/A (ArkTS 无错误码) | 设置文本颜色 | AC-2.1~2.8 |
| `fontSize(value: number\|string\|Resource)` | Public | number 默认 fp；string 带单位；Resource | TextAttribute | N/A | 设置字号 | AC-1.1~1.9 |
| `fontStyle(value: FontStyle)` | Public | FontStyle 枚举 (Normal/Italic) | TextAttribute | N/A | 设置斜体 | AC-5.1~5.5 |
| `fontWeight(value: number\|FontWeight\|ResourceStr)` | Public | number [100,900]；FontWeight 枚举；ResourceStr @since 20 | TextAttribute | N/A | 设置静态字重 | AC-3.1~3.9 |
| `fontWeight(weight, options?)` | Public | 同上 + FontSettingOptions (@since 12) | TextAttribute | N/A | 变体字重重载（仅 TextAttribute） | AC-4.1~4.6 |
| `fontFamily(value: string\|Resource)` | Public | string 逗号分隔；Resource | TextAttribute | N/A | 设置字体族 | AC-6.1~6.7 |
| `font(value: Font, options?)` | Public | Font 对象 + 可选 enableVariableFontWeight | TextAttribute | N/A | 聚合设置 | AC-7.1~7.3 |

**逐组件签名差异矩阵（动态 API）：**

| 组件 Attribute | fontColor | fontSize | fontStyle | fontWeight | fontFamily | 差异说明 |
|----------------|-----------|----------|-----------|------------|------------|----------|
| TextAttribute | ResourceColor | number\|string\|Resource | FontStyle | number\|FontWeight\|ResourceStr (+变体重载) | string\|Resource | 基线 |
| ButtonAttribute | ResourceColor | **Length** | FontStyle | number\|FontWeight\|**string** (无变体重载) | string\|Resource | fontSize 取 Length；fontWeight 无 ResourceStr |
| MarqueeAttribute | ResourceColor | Length | **无** | number\|FontWeight\|string | string\|Resource | 无 fontStyle |
| SpanAttribute | ResourceColor | number\|string\|Resource | FontStyle | +**FontWeightConfigs** 重载 (非 FontSettingOptions) | string\|Resource | 变体重载类型不同 |
| SymbolGlyphAttribute | **Array<ResourceColor\|ColorMetrics>** | number\|string\|Resource | **无** | +FontWeightConfigs 重载 | **无** | 多色层；无 fontStyle/family |
| MenuAttribute | ResourceColor | **@deprecated since 10** | 无 | 无 | 无 | 仅 fontColor；fontSize 已废弃 |
| SecurityComponentAttribute | ResourceColor | **Dimension** | FontStyle | number\|FontWeight\|string\|Resource | string\|Resource | fontSize 取 Dimension |
| TextInputAttribute | ResourceColor | Length | FontStyle | number\|FontWeight\|ResourceStr | **ResourceStr** | fontFamily 取 ResourceStr |

**ArkTS 静态 API (TextAttribute, @since 23 static)：**

| API 签名 | 入参类型 | 备注 |
|----------|---------|------|
| `fontColor(value: ResourceColor\|undefined)` | ResourceColor 可空 | 返回 this |
| `fontSize(value: double\|string\|Resource\|undefined)` | double 而非 number | 返回 this |
| `fontStyle(value: FontStyle\|undefined)` | FontStyle 可空 | 返回 this |
| `fontWeight(weight: int\|FontWeight\|ResourceStr\|undefined, options?: FontSettingOptions\|undefined)` | **合并双重载**；int 而非 number | 返回 this |
| `fontFamily(value: string\|Resource\|undefined)` | 可空 | 返回 this |

**C-API (NDK)：**

| 属性枚举 | 值格式 | @since | 支持节点 | 关联 AC |
|----------|--------|--------|----------|---------|
| NODE_FONT_COLOR=1001 | value[0].u32 (0xARGB) | 12 | TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON | AC-8.2 |
| NODE_FONT_SIZE=1002 | value[0].f32 (fp) | 12 | TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON | AC-8.1 |
| NODE_FONT_STYLE=1003 | value[0].i32 (ArkUI_FontStyle 0..1) | 12 | TEXT/SPAN/TEXT_INPUT/TEXT_AREA (不支持 BUTTON) | AC-8.4 |
| NODE_FONT_WEIGHT=1004 | value[0].i32 (ArkUI_FontWeight 0..14) | 12 | TEXT/SPAN/TEXT_INPUT/TEXT_AREA/BUTTON | AC-8.3 |
| NODE_FONT_FAMILY=1012 | string (逗号分隔) | 12 | TEXT/SPAN/TEXT_INPUT/TEXT_AREA (BUTTON 静默 no-op) | AC-8.5 |
| NODE_IMMUTABLE_FONT_WEIGHT=1030 | value[0].i32 (ArkUI_FontWeight) | 15 | set 仅 TEXT；get/reset 复用处理器覆盖更广 | AC-8.10, AC-8.11 |
| NODE_SPAN_FONT=2003 | 复合 | 24 | SPAN | AC-10.5 |
| NODE_SPAN_FONT_WEIGHT=2004 | value[0].i32 (数字 100..900) + 可选 object | 24 | SPAN | AC-10.5, AC-10.6 |

**样式字符串 C-API (@since 24)：**

| 函数 | 签名 | 入参 | 返回 | 关联 AC |
|------|------|------|------|---------|
| OH_ArkUI_TextStyle_SetFontColor | (OH_ArkUI_TextStyle*, uint32_t) | uint32 颜色 | ArkUI_ErrorCode | AC-9.1 |
| OH_ArkUI_TextStyle_SetFontFamily | (OH_ArkUI_TextStyle*, const char*) | C-string | ArkUI_ErrorCode | AC-9.2 |
| OH_ArkUI_TextStyle_SetFontSize | (OH_ArkUI_TextStyle*, float) | float 字号 | ArkUI_ErrorCode | AC-9.3 |
| OH_ArkUI_TextStyle_SetFontWeight | (OH_ArkUI_TextStyle*, uint32_t) | uint32 数字 100..900 | ArkUI_ErrorCode | AC-9.4 |
| OH_ArkUI_TextStyle_SetFontStyle | (OH_ArkUI_TextStyle*, ArkUI_FontStyle) | 枚举 | ArkUI_ErrorCode | AC-9.5 |

**Option-object C-API (@since 24)：**

| 函数 | 签名 | 关联 AC |
|------|------|---------|
| OH_ArkUI_FontWeightConfigs_Create | () -> OH_ArkUI_FontWeightConfigs* | AC-10.1 |
| OH_ArkUI_FontWeightConfigs_SetEnableVariableFontWeight | (option, bool) -> void | AC-10.2 |
| OH_ArkUI_FontWeightConfigs_SetEnableDeviceFontWeightCategory | (option, bool) -> void | AC-10.3 |
| OH_ArkUI_FontConfigs_Create | () -> OH_ArkUI_FontConfigs* | AC-10.4 |
| OH_ArkUI_FontConfigs_SetFontWeightConfigs | (option, OH_ArkUI_FontWeightConfigs*) -> void | AC-10.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| MenuAttribute.fontSize(value: Length) | 废弃 (@deprecated since 10) | Menu 组件单独设置 fontSize | 迁移至 `font(value: Font)` 聚合设置 | — |

---

## 接口规格

### 接口定义

**fontSize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontSize(value: number \| string \| Resource): TextAttribute` |
| 返回值 | TextAttribute — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A (ArkTS 无错误码) |
| 关联 AC | AC-1.1~1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| string \| Resource | 是 | theme `text_font_size` (16fp; 穿戴 15fp) | number > 0；string 带单位后缀（'px'/'vp'/'fp'/'lpx'）；Resource 解析为 Dimension；负值或解析失败回退 theme 默认 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 为正数 | 写入 FontStyle::FontSize (Dimension, fp 单位)，触发段落重建 | AC-1.1 |
| 2 | value 为带单位 string | ParseJsDimensionFpNG 解析为 CalcDimension | AC-1.2 |
| 3 | value 为 Resource | 解析并 RegisterResource 监听配置变更 | AC-1.3, AC-1.6 |
| 4 | value 为 undefined/负值 | 回退 theme 默认 | AC-1.4, AC-1.5 |
| 5 | Button 组件 | 写入 ButtonLayoutProperty::FontSize (NORMAL flag) + 重置子 Text AdaptMin/MaxFontSize | AC-1.8 |

---

**fontColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontColor(value: ResourceColor): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor = Color \| number \| string \| Resource | 是 | BLACK @ 0.9 opacity (穿戴 #c5ffffff) | Color 枚举 12 色；number 0xARGB；string 颜色字符串；Resource 颜色资源；**不含 LinearGradient/SolidColor** |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 为 Color 枚举 | 解析为对应 0xARGB | AC-2.1 |
| 2 | value 为 number | 直接作为 0xARGB | AC-2.2 |
| 3 | value 为 string | ParseJsColorForMaterial 解析颜色字符串 | AC-2.3 |
| 4 | value 为 Resource | 解析 + RegisterResource(isMaterial=true) | AC-2.4, AC-2.7 |
| 5 | 解析失败/undefined | ResetTextColor 回退默认 | AC-2.5 |
| 6 | value 为 LinearGradient/SolidColor | 不支持，按解析失败处理 | AC-2.8 |

---

**fontWeight (静态重载)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontWeight(value: number \| FontWeight \| ResourceStr): TextAttribute` (@since 7; ResourceStr @since 20) |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| FontWeight \| ResourceStr | 是 | FontWeight.Normal (W400) | number [100,900] 间隔 100（@since 12 变体重载允许任意整数）；FontWeight 6 命名 + W100..W900；ResourceStr = string\|Resource (@since 20) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 为 FontWeight 枚举 | ParseFontWeight 匹配 → variableFontWeight=GetFontWeightNumericValue(enum) | AC-3.1 |
| 2 | value 为 number | variableFontWeight=number; fontWeightEnum=ConvertStrToFontWeight(to_string(number)) | AC-3.2 |
| 3 | value 为 string "bold"/"normal"/... | ParseFontWeight 匹配命名 | AC-3.3 |
| 4 | value 为 string "800" | IsNumber → variableFontWeight=800 | AC-3.4 |
| 5 | value 为未知 string | 回退 variableFontWeight=400, enum=NORMAL | AC-3.5 |
| 6 | value 为 Resource (@since 20) | 解析为 string 后按 string 路径 | AC-3.6 |
| 7 | 总是同时设置 VariableFontWeight + FontWeight | 运行期 EnableVariableFontWeight 决定胜者 | AC-3.7 |
| 8 | EnableVariableFontWeight=false (默认) | 静态路径 + 设备缩放 | AC-3.8, AC-3.9 |

---

**fontWeight (变体字体重载)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontWeight(weight: number \| FontWeight \| ResourceStr, options?: FontSettingOptions): TextAttribute` (@since 12) |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| weight | number \| FontWeight \| ResourceStr | 是 | 同静态重载 | 同上 |
| options | FontSettingOptions | 否 | {enableVariableFontWeight: false} | 仅含 enableVariableFontWeight?: boolean |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | options.enableVariableFontWeight=true | SetEnableVariableFontWeight(true)，运行期使用 VariableFontWeight 覆盖 | AC-4.1, AC-4.2 |
| 2 | 启用变体 + Text 默认未设 device category | 不应用 GetFontWeightScale() 缩放 | AC-4.3 |
| 3 | 不传 options | 默认 enableVariableFontWeight=false | AC-4.4 |
| 4 | 在 Span/SymbolGlyph 使用 | 使用 FontWeightConfigs（非 FontSettingOptions），类型不兼容 | AC-4.5 |
| 5 | 在非 Text 组件 | 不暴露此重载 | AC-4.6 |

---

**fontStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontStyle(value: FontStyle): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1~5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | FontStyle (Normal=0/Italic=1) | 是 | FontStyle.Normal | 越界：API<12 静默返回；API≥12 clamp 到 0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=Normal | ItalicFontStyle=NORMAL | AC-5.1 |
| 2 | value=Italic | ItalicFontStyle=ITALIC | AC-5.2 |
| 3 | 越界 API<12 | 静默返回 | AC-5.3 |
| 4 | 越界 API≥12 | clamp 到 0 | AC-5.4 |
| 5 | Marquee 组件 | 不支持 | AC-5.5 |

---

**fontFamily**

| 属性 | 值 |
|------|-----|
| 函数签名 | `fontFamily(value: string \| Resource): TextAttribute` |
| 返回值 | TextAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1~6.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string \| Resource | 是 | theme GetFontFamilies() (HarmonyOS Sans; 非标准系统 sans-serif) | string 逗号分隔多字体；Resource 解析为单元素 vector；空字符串回退默认 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | string 单字体 | vector 单元素 | AC-6.1 |
| 2 | string 多字体逗号分隔 | ConvertStrToFontFamilies 切分 | AC-6.2 |
| 3 | Resource | ParseJsFontFamilies 解析 | AC-6.3 |
| 4 | 空字符串/undefined | 回退默认 | AC-6.4 |
| 5 | 字体未注册 | 按 vector 优先级回退 | AC-6.5 |
| 6 | 自定义字体 | 需先 loadFontSync 注册 | AC-6.6 |
| 7 | Text 组件 | 写入 FontStyle::FontFamily (vector<string>) + 段落重建 | AC-6.7 |

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 11**: FontWeight/FontStyle 枚举在 SDK 显式 `@since 11 dynamic`（实际方法 @since 7，枚举类型本身 @since 11）
  - **API 12**: 新增变体字体重载 `fontWeight(weight, options?: FontSettingOptions)`；新增 ResourceStr 类型支持；新增 enableVariableFontWeight 行为
  - **API 15**: 新增 C-API NODE_IMMUTABLE_FONT_WEIGHT（set 仅 TEXT）
  - **API 20**: fontWeight/letterSpacing/baselineOffset 参数增加 ResourceStr 类型（param-level @since 20）
  - **API 23 static**: 静态范式 TextAttribute（合并双 fontWeight 重载）
  - **API 24**: styled-string C-API OH_ArkUI_TextStyle_SetFont*；option-object C-API OH_ArkUI_FontConfigs/FontWeightConfigs；NODE_SPAN_FONT/FONT_WEIGHT
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（ArkTS）；API 12（C-API NODE_FONT_*）；API 15（NODE_IMMUTABLE_FONT_WEIGHT）；API 24（styled-string + option-object）
- **API 版本号策略:** @since 7 基础；@since 12/15/20/24 标注新增；param-level @since 20 标注 ResourceStr 类型扩展；逐组件签名差异在接口规格表标注

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| 共享存储 + 逐组件声明 | 「通用」是 TextLayoutProperty::FontStyle 组共享存储，非 ViewAbstract 公共方法；逐组件 SDK 声明以适配签名差异 | AC-1.7, AC-1.8, AC-1.9 |
| FontWeight 双路径运行期决策 | FontWeight 与 VariableFontWeight 总同时设置，渲染转换期由 EnableVariableFontWeight 决定胜者 | AC-3.7, AC-4.2 |
| EnableDeviceFontWeightCategory 三态 | 可选 bool：未设置/true/false 行为不同 | AC-3.9, AC-4.3 |
| propNeedReCreateParagraph_ 触发 | FontStyle 组任一项变更触发段落重建（同帧合并） | AC-1.7, AC-6.7 |
| C-API 编码不一致 | NODE_FONT_WEIGHT 枚举(0..14) vs NODE_SPAN_FONT_WEIGHT 数字(100..900) | AC-8.3, AC-10.6 |
| C-API 节点支持缺口 | NODE_FONT_STYLE 不支持 BUTTON；NODE_FONT_FAMILY reset 不覆盖 SPAN；NODE_IMMUTABLE_FONT_WEIGHT set/get 非对称 | AC-8.4, AC-8.5, AC-8.10, AC-8.11 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | FontStyle 组单次设置 + 标记脏 < 1μs；多个字体属性同时设置仅触发一次段落重建（同帧合并） | benchmark | — |
| 内存 | FontStyle 组使用 std::optional 字段避免无用分配；FontFamily 使用 vector<string> 仅在设置时分配 | hidumper | — |
| 可靠性 | 字体未注册时按优先级回退，不崩溃 | 集成测试 | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |
| 穿戴 | 默认值差异：fontSize=15fp（非 16fp）；fontColor=#c5ffffff（非 BLACK@0.9）；fontWeight 默认 Regular（非 Normal） | text.d.ts:132,147,262 JSDoc | 文档标注 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | fontColor/fontSize 影响可读性但无障碍语义由组件本身提供 | — |
| 大字体 | 是 | fontSize 使用 fp 单位随系统字体缩放变化；EnableDeviceFontWeightCategory 控制字重缩放 | AC-1.1, AC-3.9 |
| 深色模式 | 是 | fontColor 通常通过 Resource 引用主题颜色，深色模式下重新解析 | AC-2.7 |
| 多窗口/分屏 | 否 | 字体属性不直接受窗口尺寸影响（除非 Resource 引用 dimens） | — |
| 多用户 | 否 | 字体属性无用户态差异 | — |
| 版本升级 | 是 | API 11/12/15/20/24 行为变更与新增须通过 API 版本守护 | AC-3.6, AC-4.1, AC-8.10, AC-9.1, AC-10.1 |
| 生态兼容 | 是 | C-API (NDK) 多通道（NODE_FONT_*/styled-string/option-object）应与 ArkTS 行为一致 | AC-8.*, AC-9.*, AC-10.* |

---

## 行为场景

```gherkin
Feature: 核心字体属性
  作为 应用开发者
  我想要 通过声明式 API 与 C-API 控制文本承载组件的字号、颜色、字重、斜体与字体族
  以便 实现统一的文本样式表现

  # ─── fontSize 基础 ─────────────────────────────────

  Scenario: 设置字号（number 类型，默认 fp 单位）
    Given 一个 Text 组件
    When 调用 .fontSize(16)
    Then Text 字号为 16fp
    And FontStyle::FontSize 更新，propNeedReCreateParagraph_=true
    And 下一帧段落重建

  Scenario: 设置字号（string 带单位）
    Given 一个 Text 组件
    When 调用 .fontSize('20vp')
    Then Text 字号为 20vp

  Scenario: 设置字号（Resource 类型）
    Given 一个 Text 组件
    And 系统资源 app.size.text = 18fp
    When 调用 .fontSize($r('app.size.text'))
    Then Text 字号为 18fp
    And 注册 Resource 监听配置变更

  Scenario: 字号负值回退
    Given 一个 Text 组件
    When 调用 .fontSize(-10)
    Then 解析失败，字号回退到 theme text_font_size 默认值

  Scenario: Button 设置字号同步子 Text
    Given 一个 Button 组件含内部 Text 子节点
    When 调用 .fontSize(14)
    Then 写入 ButtonLayoutProperty::FontSize (PROPERTY_UPDATE_NORMAL)
    And 重置内部 Text 子节点 AdaptMinFontSize/AdaptMaxFontSize

  # ─── fontColor 基础 ────────────────────────────────

  Scenario: 设置文本颜色（Color 枚举）
    Given 一个 Text 组件
    When 调用 .fontColor(Color.Red)
    Then Text 颜色为 Color.Red 对应 0xARGB

  Scenario: 设置文本颜色（number 0xARGB）
    Given 一个 Text 组件
    When 调用 .fontColor(0xFFFF0000)
    Then Text 颜色为 0xFFFF0000 红色

  Scenario: fontColor 仅触发 RENDER（不触发 MEASURE）
    Given 一个 Text 组件
    When 调用 .fontColor(Color.Blue)
    Then 通过 UpdateTextColorByRender 仅设置 PROPERTY_UPDATE_RENDER
    And 同步更新 RenderContext::ForegroundColor
    And 设置 TextColorFlagByUser=true

  Scenario: fontColor 不支持渐变色
    Given 一个 Text 组件
    When 尝试 .fontColor(LinearGradient(...))
    Then ResourceColor 不含 LinearGradient，按解析失败处理
    And 调用 ResetTextColor 回退默认

  # ─── fontWeight 双路径 ────────────────────────────

  Scenario: 设置静态字重（FontWeight 枚举）
    Given 一个 Text 组件
    When 调用 .fontWeight(FontWeight.Bold)
    Then 同时设置 VariableFontWeight=700 和 FontWeight=BOLD
    And 运行期 EnableVariableFontWeight=false（默认）→ 使用静态路径

  Scenario: 设置字重（number 700）
    Given 一个 Text 组件
    When 调用 .fontWeight(700)
    Then variableFontWeight=700, fontWeightEnum=W700
    And 同时写入两者

  Scenario Outline: 渲染转换期字重决策
    Given 一个 Text 组件已设置 .fontWeight(<weight>, {enableVariableFontWeight: <enabled>})
    And EnableDeviceFontWeightCategory <deviceState>
    When ConvertTxtStyle 执行
    Then 最终 wght 轴值 = <expectedWght>

    Examples:
      | weight | enabled | deviceState | expectedWght |
      | 700 | false | unset | 700 × fontWeightScale |
      | 550 | true | unset | 550（不应用 scale） |
      | 550 | true | set true | 550 × fontWeightScale |
      | 550 | true | set false | 550 |

  Scenario: 变体字体重载仅在 TextAttribute
    Given 一个 Span 组件
    When 尝试 .fontWeight(550, {enableVariableFontWeight: true})
    Then Span 第二重载使用 FontWeightConfigs（非 FontSettingOptions）
    And 类型不兼容，需使用 FontWeightConfigs

  # ─── fontStyle 基础 ───────────────────────────────

  Scenario: 设置斜体
    Given 一个 Text 组件
    When 调用 .fontStyle(FontStyle.Italic)
    Then ItalicFontStyle=ITALIC

  Scenario: fontStyle 越界（API < 12）
    Given 目标 API 版本 < 12
    And 一个 Text 组件
    When 调用 .fontStyle(-1)
    Then 静默返回，不设置

  Scenario: fontStyle 越界（API >= 12）
    Given 目标 API 版本 >= 12
    And 一个 Text 组件
    When 调用 .fontStyle(99)
    Then clamp 到 0（NORMAL）

  Scenario: Marquee 不支持 fontStyle
    Given 一个 Marquee 组件
    When 尝试 .fontStyle(FontStyle.Italic)
    Then MarqueeAttribute 未声明 fontStyle 方法，不支持

  # ─── fontFamily 基础 ──────────────────────────────

  Scenario: 设置单字体族
    Given 一个 Text 组件
    When 调用 .fontFamily('HarmonyOS Sans')
    Then FontFamily = ["HarmonyOS Sans"]

  Scenario: 设置多字体族（逗号分隔）
    Given 一个 Text 组件
    When 调用 .fontFamily('HarmonyOS Sans, serif, monospace')
    Then ConvertStrToFontFamilies 切分为 ["HarmonyOS Sans", "serif", "monospace"]
    And 按优先级应用

  Scenario: 字体未注册按优先级回退
    Given 一个 Text 组件设置 .fontFamily('NonExistentFont, serif')
    And NonExistentFont 未注册
    When 渲染执行
    Then 回退到 serif

  # ─── C-API (NDK) ──────────────────────────────────

  Scenario: C-API 设置 fontSize
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_FONT_SIZE, {value[0].f32: 16.0})
    Then fontSize=16fp 写入

  Scenario: C-API NODE_FONT_STYLE 不支持 BUTTON
    Given 一个 ARKUI_NODE_BUTTON 节点
    When 调用 setAttribute(node, NODE_FONT_STYLE, {value[0].i32: 1})
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401)

  Scenario: C-API NODE_FONT_FAMILY 对 BUTTON 静默 no-op
    Given 一个 ARKUI_NODE_BUTTON 节点
    When 调用 setAttribute(node, NODE_FONT_FAMILY, {string: "serif"})
    Then 返回 ARKUI_ERROR_CODE_NO_ERROR (0) 但无操作

  Scenario: C-API NODE_IMMUTABLE_FONT_WEIGHT 仅 TEXT 支持 set
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_IMMUTABLE_FONT_WEIGHT, {value[0].i32: 4})
    Then 设置不受系统字体权重设置影响的 fontWeight
    Given 一个 ARKUI_NODE_BUTTON 节点
    When 调用 setAttribute(node, NODE_IMMUTABLE_FONT_WEIGHT, {value[0].i32: 4})
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401)

  Scenario: C-API NODE_FONT_WEIGHT 枚举编码 vs NODE_SPAN_FONT_WEIGHT 数字编码
    Given 一个 ARKUI_NODE_TEXT 节点
    When 调用 setAttribute(node, NODE_FONT_WEIGHT, {value[0].i32: 4})
    Then 4 解释为 ARKUI_FONT_WEIGHT_BOLD 枚举
    Given 一个 ARKUI_NODE_SPAN 节点
    When 调用 setAttribute(node, NODE_SPAN_FONT_WEIGHT, {value[0].i32: 700})
    Then 700 解释为数字字重值（非枚举）

  # ─── styled-string C-API (@since 24) ──────────────

  Scenario: 样式字符串设置字体属性
    Given 一个 OH_ArkUI_TextStyle 对象
    When 调用 OH_ArkUI_TextStyle_SetFontColor(style, 0xFFFF0000)
    And 调用 OH_ArkUI_TextStyle_SetFontSize(style, 16.0f)
    And 调用 OH_ArkUI_TextStyle_SetFontWeight(style, 700)
    Then textStyle.fontColor=0xFFFF0000, fontSize=16.0, fontWeight=700

  Scenario: 样式字符串 nullptr 返回错误
    When 调用 OH_ArkUI_TextStyle_SetFontColor(nullptr, 0xFFFF0000)
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID (401)

  # ─── option-object C-API (@since 24) ──────────────

  Scenario: 配置 Span 变体字重
    Given 一个 ARKUI_NODE_SPAN 节点
    When 创建 OH_ArkUI_FontWeightConfigs 并 SetEnableVariableFontWeight(true)
    And 创建 OH_ArkUI_FontConfigs 并 SetFontWeightConfigs(weightConfig)
    And 调用 setAttribute(span, NODE_SPAN_FONT_WEIGHT, {value[0].i32: 550, object: fontConfig})
    Then ProcessFontWeightConfigs 执行 setSpanEnableVariableFontWeight(true) + setSpanVariableFontWeight(550)
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（覆盖 fontSize/fontColor/fontWeight(+变体重载)/fontStyle/fontFamily 五项；不含 decoration/textCase/letterSpacing/lineHeight/baselineOffset/textShadow/fontFeature/fontVariations/minFontScale/maxFontScale/AdaptMin/MaxFontSize，这些属 Feat-02~05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TextLayoutProperty FontStyle property group ACE_DEFINE_PROPERTY_ITEM_WITH_GROUP propNeedReCreateParagraph"
  - repo: "openharmony/ace_engine"
    query: "ConvertTxtStyle constants_converter FontWeight VariableFontWeight EnableVariableFontWeight EnableDeviceFontWeightCategory"
  - repo: "openharmony/ace_engine"
    query: "JSText SetFontWeight SetFontSize SetTextColor SetFontFamily js_text.cpp ParseFontWeightInfo"
  - repo: "openharmony/ace_engine"
    query: "style_modifier.cpp SetFontColor SetFontSize SetFontStyle SetFontWeight SetTextFontFamily NODE_FONT"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_TextStyle_SetFont OH_ArkUI_FontConfigs OH_ArkUI_FontWeightConfigs native_styled_string_descriptor"
```

**关键文档：**
- 架构设计：`specs/04-common-capability/03-common-attributes/11-text-common-attributes/design.md`
- SDK 类型定义：`interface/sdk-js/api/@internal/component/ets/text.d.ts`、`text_common.d.ts`、`enums.d.ts`、`units.d.ts`
- 静态范式：`interface/sdk-js/api/arkui/component/text.static.d.ets`
- C-API：`interfaces/native/native_node.h`、`interfaces/native/node_attributes/text.h`、`interfaces/native/native_styled_string_descriptor.h`
