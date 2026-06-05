# 特性规格

> Func-05-09-04-Feat-04 装饰与样式：固化 decoration/textShadow/textCase/shaderStyle/contentTransition/marqueeOptions 六个装饰与视觉样式属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 装饰与样式 (Decoration & Styles) |
| 特性编号 | Func-05-09-04-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10/11/12/18/20/23 有 API 新增或变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | decoration 完整行为（type/color/style/thicknessScale） | @since 7, @since 12 类型变更, @since 20 新增 thicknessScale |
| ADDED | textShadow 单/多阴影 | @since 10 单阴影, @since 11 支持数组 |
| ADDED | textCase 大小写变换 | @since 7 |
| ADDED | shaderStyle 渐变着色 | @since 20 |
| ADDED | contentTransition 数字翻页动画 | @since 20 |
| ADDED | marqueeOptions 跑马灯配置 | @since 18, @since 23 新增 spacing/marqueeUpdatePolicy |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/04-text/design.md` | Baselined |

---

## 用户故事

### US-1: 设置文本装饰线

**作为** 应用开发者,
**我想要** 通过 `.decoration()` 设置 Text 组件的装饰线（下划线/上划线/删除线），
**以便** 实现文本的装饰排版效果。

**验收标准：**

- **AC-1.1:** WHEN 调用 `.decoration({ type: TextDecorationType.Underline })` THEN 文本渲染下划线
- **AC-1.2:** WHEN 调用 `.decoration({ type: TextDecorationType.Overline })` THEN 文本渲染上划线
- **AC-1.3:** WHEN 调用 `.decoration({ type: TextDecorationType.LineThrough })` THEN 文本渲染删除线
- **AC-1.4:** WHEN 调用 `.decoration({ type: TextDecorationType.None })` 或未设置 THEN 无装饰线
- **AC-1.5:** WHEN 设置 `color` 字段（如 `{ type: TextDecorationType.Underline, color: Color.Red }`） THEN 装饰线使用指定颜色渲染；WHEN 未设置 color THEN 装饰线颜色为 Color.Black
- **AC-1.6:** WHEN 设置 `style` 字段为 TextDecorationStyle.DOUBLE/DOTTED/DASHED/WAVY (@since 12) THEN 装饰线以对应样式渲染；WHEN 未设置 style THEN 默认 SOLID
- **AC-1.7:** WHEN 设置 `thicknessScale` 为正数 (@since 20) THEN 装饰线粗细按该倍率缩放；WHEN thicknessScale < 0 THEN 回退到默认值 1.0（`js_text.cpp:875-879` — `lineThicknessScale < 0 ? 1.0f : lineThicknessScale`）
- **AC-1.8:** WHEN 在 `style` 属性值为 TextDecorationStyle 以外的类型时 THEN 回退到 SOLID（`js_text.cpp:870`）
- **AC-1.9:** WHEN decoration 属性从 NONE 切换到 UNDERLINE（或反向） THEN 装饰线 alpha 通道渐变动画过渡（`text_content_modifier.cpp:1331-1343` — `textDecorationAnimatable_`）
- **AC-1.10:** WHEN decoration 属性在 OVERLINE/LINE_THROUGH/DOUBLE 等非 NONE-UNDERLINE 对之间切换 THEN 无动画过渡，立即生效
- **AC-1.11:** WHEN 通过 C API `NODE_TEXT_DECORATION` 设置 THEN `.value[0].i32` 为 type, `.value[1].u32` 为 color (ARGB), `.value[2].i32` 为 style, `.value[3].f32` 为 thicknessScale
- **AC-1.12:** WHEN @since 7~11 调用 `.decoration(value)` 且 value 类型为 `object` THEN 按 `{type, color}` 解析；WHEN @since 12+ 调用 THEN 按 `DecorationStyleInterface` 解析，新增 `style` 和 `thicknessScale` 字段

### US-2: 设置文本阴影

**作为** 应用开发者,
**我想要** 通过 `.textShadow()` 设置文本阴影效果,
**以便** 增强文本的视觉层次。

**验收标准：**

- **AC-2.1:** WHEN 调用 `.textShadow({ radius: 10, color: Color.Gray, offsetX: 5, offsetY: 5 })` THEN 文本按指定参数渲染阴影
- **AC-2.2:** WHEN radius 为 0 或负数 THEN 不渲染阴影
- **AC-2.3:** WHEN 未设置 color THEN 阴影颜色默认为 Black；WHEN 未设置 offsetX/offsetY THEN 默认偏移为 0
- **AC-2.4:** WHEN 调用 `.textShadow([shadow1, shadow2, ...])` (@since 11) THEN 多阴影按数组顺序叠加渲染
- **AC-2.5:** WHEN `type` 设置为 `ShadowType.COLOR` (默认) THEN 使用 color 值渲染阴影；WHEN `type` 设置为 `ShadowType.BLUR` (@since 10) THEN 使用模糊类型阴影
- **AC-2.6:** WHEN `fill` 字段设置为 true THEN 在 textShadow 中**不生效**（SDK 文档明确说明 "does not work with fill attribute"；`text.d.ts:1322` 注释 / `text.static.d.ets:401` NOTE）
- **AC-2.7:** WHEN textShadow 与 `foregroundColor(ColoringStrategy)` 同时设置 THEN textShadow **不生效**（`text.d.ts:1322` 注释）
- **AC-2.8:** WHEN textShadow 属性变更 THEN 阴影的 blurRadius/offsetX/offsetY/color 支持动画过渡（`text_content_modifier.cpp:1307-1329` — `ShadowProp` 包含 AnimatablePropertyFloat）
- **AC-2.9:** WHEN 通过 C API `NODE_TEXT_TEXT_SHADOW` 设置 THEN `.value[0].f32` = radius, `.value[1].i32` = type, `.value[2].u32` = color (ARGB), `.value[3].f32` = offsetX, `.value[4].f32` = offsetY；支持多阴影时通过 `ArkUI_AttributeItem.size` 传入数量
- **AC-2.10:** WHEN 重置 textShadow THEN 回退为单个全零 Shadow（`node_text_modifier.cpp:1443-1452`）

### US-3: 设置文本大小写变换

**作为** 应用开发者,
**我想要** 通过 `.textCase()` 控制文本的大小写显示,
**以便** 实现全大写/全小写的排版需求。

**验收标准：**

- **AC-3.1:** WHEN 调用 `.textCase(TextCase.Normal)` 或未设置 THEN 文本保持原始大小写
- **AC-3.2:** WHEN 调用 `.textCase(TextCase.LowerCase)` THEN 文本全部转为小写显示（原始数据不变）
- **AC-3.3:** WHEN 调用 `.textCase(TextCase.UpperCase)` THEN 文本全部转为大写显示（原始数据不变）
- **AC-3.4:** WHEN 文本包含 Unicode 字符（如 `é`/`Ñ`） THEN 使用 `std::towupper`/`std::towlower` 进行区域感知转换（`string_utils.cpp:762-767` — `std::u16string` 特化）
- **AC-3.5:** WHEN 文本包含 CJK/数字/符号等非字母字符 THEN 这些字符不受 textCase 影响
- **AC-3.6:** WHEN 在 Span 级别设置 textCase THEN 触发 `ChangeFlag::RE_CREATE`（段落重建），而非仅 RE_LAYOUT（`span_node.h:1060`）
- **AC-3.7:** WHEN 通过 C API `NODE_TEXT_CASE` 设置 THEN `.value[0].i32` 为 TextCase 枚举值（0=Normal, 1=LowerCase, 2=UpperCase）
- **AC-3.8:** WHEN 传入的枚举值超出 [0, 2] 范围 THEN 重置为默认值 Normal（`arkts_native_text_bridge.cpp:579` — `>SIZE_OF_TEXT_CASES` 时调用 reset）

### US-4: 设置文本渐变着色

**作为** 应用开发者,
**我想要** 通过 `.shaderStyle()` (@since 20) 为文本设置渐变或纯色着色效果,
**以便** 实现渐变文字等视觉效果。

**验收标准：**

- **AC-4.1:** WHEN 调用 `.shaderStyle(new LinearGradientStyle(options))` THEN 文本以线性渐变着色渲染
- **AC-4.2:** WHEN 调用 `.shaderStyle(new RadialGradientStyle(options))` THEN 文本以径向渐变着色渲染
- **AC-4.3:** WHEN 调用 `.shaderStyle(new ColorShaderStyle(color))` THEN 文本以指定纯色着色，等效于替换 fontColor
- **AC-4.4:** WHEN 设置 GradientShaderStyle 后再设置 ColorShaderStyle THEN GradientShaderStyle 被重置（`text_model_ng.cpp:2010-2013` — `SetColorShaderStyle` 先调用 `ResetGradientShaderStyle`）；反之亦然（`text_model_ng.cpp:2006` — `SetGradientShaderStyle` 先 reset `ColorShaderStyle`）
- **AC-4.5:** WHEN shaderStyle 与 fontColor 同时设置 THEN shaderStyle 优先生效（`multiple_paragraph_layout_algorithm.cpp:207-222` — `UpdateShaderStyle` 覆盖 fontColor）
- **AC-4.6:** WHEN shaderStyle 与 `foregroundColor()` 同时设置 THEN shaderStyle 的 foregroundBrush 覆盖 foregroundColor 效果
- **AC-4.7:** WHEN 传入 undefined 或调用重置 THEN 清除渐变和纯色着色，回退到 fontColor 渲染
- **AC-4.8:** WHEN 在 Span 级别继承 shaderStyle THEN 子 Span 继承父 Text 的 shaderStyle（`span_node.cpp:857-868` — 继承优先级判断）
- **AC-4.9:** WHEN 通过静态版 ArkTS 设置 `shaderStyle(shader)` (@since 24 static) THEN 行为与动态版一致

### US-5: 设置文本内容过渡动画

**作为** 应用开发者,
**我想要** 通过 `.contentTransition()` (@since 20) 为数字文本内容变化设置翻页动画,
**以便** 实现数字滚动等动态效果。

**验收标准：**

- **AC-5.1:** WHEN 调用 `.contentTransition(new NumericTextTransition())` 且文本内容为纯数字 THEN 数字变化时按 FLIP 策略播放翻页动画
- **AC-5.2:** WHEN `flipDirection` 设为 `FlipDirection.DOWN` (默认) THEN 数字向下翻转；WHEN 设为 `FlipDirection.UP` THEN 数字向上翻转
- **AC-5.3:** WHEN `enableBlur` 设为 true THEN 翻页过程中启用模糊效果；WHEN 设为 false (默认) THEN 无模糊
- **AC-5.4:** WHEN 文本内容不是纯数字 THEN contentTransition 不触发动画（`text_pattern.cpp:5372` — 仅数字文本时创建 TextEffect）
- **AC-5.5:** WHEN 传入 undefined THEN 重置并停止动画效果（`text_model_ng.cpp:604-610` — `ResetContentTransition` 重置 TextEffectStrategy/FlipDirection/EnableBlur）
- **AC-5.6:** WHEN 通过静态版 ArkTS 设置 `contentTransition(transition)` (@since 24 static) THEN 行为与动态版一致

### US-6: 设置跑马灯选项

**作为** 应用开发者,
**我想要** 通过 `.marqueeOptions()` (@since 18) 配置 Text 组件跑马灯的滚动行为,
**以便** 精细控制文本滚动参数。

**验收标准：**

- **AC-6.1:** WHEN 调用 `.marqueeOptions({ start: true })` 且已设置 `textOverflow(TextOverflow.MARQUEE)` THEN 启动跑马灯滚动
- **AC-6.2:** WHEN 未设置 `textOverflow(TextOverflow.MARQUEE)` THEN marqueeOptions 不生效（`text_pattern.cpp:8041-8046` — `IsMarqueeOverflow()` 守卫全部跑马灯逻辑）
- **AC-6.3:** WHEN `step` 为正数 THEN 每帧滚动步长为 step（VP 转 px）；WHEN step 未设置 THEN 默认 `RACE_DURATION_RATIO` 驱动的速度
- **AC-6.4:** WHEN `loop` 为正整数 N THEN 滚动 N 圈后停止（`text_content_modifier.cpp:1860-1872` — `marqueeCount_ >= loop`）；WHEN loop ≤ 0 或未设置 THEN 无限循环（内部映射为 -1）
- **AC-6.5:** WHEN `delay` 为正数 ms THEN 每圈结束后等待 delay 毫秒再开始下一圈；WHEN delay < 0 THEN 钳位到 0
- **AC-6.6:** WHEN `fromStart` 为 true THEN 从文本起始方向滚动（`MarqueeDirection::DEFAULT`）；WHEN 为 false THEN 反向（`MarqueeDirection::DEFAULT_REVERSE`）；实际方向受 RTL/LTR 布局影响
- **AC-6.7:** WHEN `fadeout` 为 true THEN 跑马灯两端显示渐隐效果（`text_content_modifier.cpp:1893-1953` — 计算 `marqueeGradientPercent_`）
- **AC-6.8:** WHEN `marqueeStartPolicy` 为 `MarqueeStartPolicy.DEFAULT` THEN 跑马灯立即启动；WHEN 为 `ON_FOCUS` THEN 仅在组件获得焦点或鼠标悬停时启动（`text_content_modifier.cpp:1866-1870` — `AllowTextRace` 检查 `focused_ || hovered_`）
- **AC-6.9:** WHEN `spacing` 设置为合法 LengthMetrics (@since 23) THEN 两圈文本之间的间距为 spacing 值；WHEN 未设置 THEN 默认 48vp（`marquee_option.h:42` — `RACE_SPACE_WIDTH`）
- **AC-6.10:** WHEN `marqueeUpdatePolicy` 为 `MarqueeUpdatePolicy.DEFAULT` (@since 23) THEN 文本内容更新时按默认策略重启滚动；WHEN 为 `PRESERVE_POSITION` THEN 保持当前滚动位置继续
- **AC-6.11:** WHEN 注册 `onMarqueeStateChange(callback)` THEN 在 START（开始滚动）、BOUNCE（一圈结束回弹）、FINISH（全部结束）三个时机分别回调
- **AC-6.12:** WHEN 通过 C API `NODE_TEXT_MARQUEE_OPTIONS` 设置 THEN 使用 `OH_ArkUI_TextMarqueeOptions` 结构体传入各参数（`text_native_impl.cpp:517-643`）
- **AC-6.13:** WHEN `start` 设为 false THEN 停止正在运行的跑马灯动画

---

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.4 | FR-1, BR-1 | 存量实现 | UT + 手工验证 | text_pattern_test |
| AC-1.5~1.6 | FR-2 | 存量实现 | UT | text_pattern_test |
| AC-1.7 | FR-3, ER-1 | 存量实现 | UT | capi_all_modifiers_test |
| AC-1.8 | ER-1 | 存量实现 | UT | text_pattern_test |
| AC-1.9~1.10 | FR-4 | 存量实现 | 手工验证 | 动画表现 |
| AC-1.11 | FR-5 | 存量实现 | UT | capi_all_modifiers_test |
| AC-1.12 | BR-2 | 存量实现 | UT | text_pattern_test |
| AC-2.1~2.3 | FR-6, BR-3 | 存量实现 | UT + 手工验证 | text_pattern_test |
| AC-2.4 | FR-7 | 存量实现 | UT | text_pattern_test |
| AC-2.5 | FR-8 | 存量实现 | 手工验证 | 渲染表现 |
| AC-2.6~2.7 | BR-4, BR-5 | 存量实现 | 手工验证 | SDK 文档声明 |
| AC-2.8 | FR-9 | 存量实现 | 手工验证 | 动画表现 |
| AC-2.9~2.10 | FR-10 | 存量实现 | UT | capi_all_modifiers_test |
| AC-3.1~3.3 | FR-11 | 存量实现 | UT | text_pattern_test |
| AC-3.4~3.5 | FR-12 | 存量实现 | UT | string_utils_test |
| AC-3.6 | FR-13, BR-6 | 存量实现 | 代码验证 | span_node.h:1060 |
| AC-3.7~3.8 | FR-14, ER-2 | 存量实现 | UT | capi_all_modifiers_test |
| AC-4.1~4.3 | FR-15 | 存量实现 | 手工验证 | 渲染表现 |
| AC-4.4 | BR-7, FR-16 | 存量实现 | 代码验证 | text_model_ng.cpp:2006-2013 |
| AC-4.5~4.6 | BR-8 | 存量实现 | 手工验证 | 渲染优先级 |
| AC-4.7~4.9 | FR-17 | 存量实现 | 手工验证 | 渲染表现 |
| AC-5.1~5.3 | FR-18 | 存量实现 | 手工验证 | 动画表现 |
| AC-5.4 | BR-9 | 存量实现 | 代码验证 | text_pattern.cpp:5372 |
| AC-5.5~5.6 | FR-19 | 存量实现 | 手工验证 | 动画表现 |
| AC-6.1 | FR-20, BR-10 | 存量实现 | UT + 手工验证 | text_pattern_test |
| AC-6.2 | BR-10 | 存量实现 | 代码验证 | text_pattern.cpp:8041 |
| AC-6.3~6.6 | FR-21, FR-22, FR-23 | 存量实现 | UT + 手工验证 | text_pattern_test |
| AC-6.7 | FR-24 | 存量实现 | 手工验证 | 渐隐效果 |
| AC-6.8 | FR-25 | 存量实现 | 手工验证 | 焦点交互 |
| AC-6.9~6.10 | FR-26, FR-27 | 存量实现 | 手工验证 | @since 23 新增 |
| AC-6.11 | FR-28 | 存量实现 | UT | text_pattern_test |
| AC-6.12~6.13 | FR-29 | 存量实现 | UT | capi_all_modifiers_test |

---

## 业务规则

- **BR-1:** decoration 默认值为 `{ type: TextDecorationType.None, color: Color.Black, style: TextDecorationStyle.SOLID }`
- **BR-2:** @since 12 起 decoration 参数类型从 `object` 变更为 `DecorationStyleInterface`，增加 `style` 字段（TextDecorationStyle 枚举）；@since 20 增加 `thicknessScale` 字段
- **BR-3:** textShadow 默认不渲染阴影（无默认 shadow）
- **BR-4:** textShadow 的 `fill` 属性在 Text 组件上不生效（SDK 注释限制）
- **BR-5:** textShadow 与 `foregroundColor(ColoringStrategy)` 互斥——同时设置时 textShadow 不生效
- **BR-6:** textCase 变更 Span 级别内容触发 `RE_CREATE`（段落重建），而非 `RE_LAYOUT`，因为文本内容实质性变化
- **BR-7:** shaderStyle 的 GradientShaderStyle 和 ColorShaderStyle 内部互斥——设置一个自动重置另一个
- **BR-8:** shaderStyle 优先级高于 fontColor——当 shaderStyle 生效时，通过 Rosen `foregroundBrush` 覆盖字体颜色
- **BR-9:** contentTransition 仅在文本内容为纯数字时生效
- **BR-10:** marqueeOptions 必须与 `textOverflow(TextOverflow.MARQUEE)` 配合使用——`IsMarqueeOverflow()` 在 13+ 处守卫全部跑马灯逻辑

## 功能规则

- **FR-1:** decoration type 支持 4 个枚举值：NONE (0) / UNDERLINE (1) / OVERLINE (2) / LINE_THROUGH (3)，内部以 `std::vector<TextDecoration>` 存储（`text_layout_property.h:130`）
- **FR-2:** decoration style 支持 5 个枚举值：SOLID (0) / DOUBLE (1) / DOTTED (2) / DASHED (3) / WAVY (4)（@since 12）
- **FR-3:** thicknessScale 默认值 1.0，负值回退到 1.0（`js_text.cpp:875-879`，`style_modifier.cpp:13447-13451`）
- **FR-4:** decoration NONE↔UNDERLINE 切换支持 alpha 通道渐变动画（`text_content_modifier.cpp:1331-1343`），其他类型切换无动画
- **FR-5:** C-API `NODE_TEXT_DECORATION` 四参数格式：type(i32) + color(u32 ARGB) + style(i32) + thicknessScale(f32)
- **FR-6:** textShadow 参数：radius (blur radius, px), type (ShadowType), color (ARGB), offsetX (px), offsetY (px), fill (bool)
- **FR-7:** textShadow 支持数组——多阴影按数组顺序叠加渲染，内部以 `std::vector<Shadow>` 存储
- **FR-8:** textShadow type 默认 `ShadowType.COLOR`
- **FR-9:** textShadow 属性变更时，blurRadius/offsetX/offsetY/color 四个维度支持 AnimatablePropertyFloat 动画过渡
- **FR-10:** C-API `NODE_TEXT_TEXT_SHADOW` 支持多阴影通过 `ArkUI_AttributeItem.size` 传入数量
- **FR-11:** textCase 三值枚举：Normal (0) / LowerCase (1) / UpperCase (2)（`text_enums.h:58-62`）
- **FR-12:** textCase 在字符串层面预处理——在 `paragraph->AddText()` 前通过 `StringUtils::TransformStrCase()` 变换，Unicode 使用 `std::towupper`/`std::towlower`
- **FR-13:** textCase 触发 `PROPERTY_UPDATE_MEASURE`（Layout Property 层），Span 层面触发 `RE_CREATE`
- **FR-14:** C-API `NODE_TEXT_CASE` 单参数 `.value[0].i32`，枚举值 0/1/2
- **FR-15:** shaderStyle 支持 3 种子类：LinearGradientStyle（线性渐变）、RadialGradientStyle（径向渐变）、ColorShaderStyle（纯色）
- **FR-16:** 设置 GradientShaderStyle 时自动 reset ColorShaderStyle（`text_model_ng.cpp:2006`），反之亦然（`text_model_ng.cpp:2012`）
- **FR-17:** shaderStyle 通过 Rosen `TextStyle.foregroundBrush` 渲染，LinearGradient/RadialGradient 使用 `DrawingDecorationPainter::CreateGradientShader()` 创建 RSBrush
- **FR-18:** contentTransition 配置项：TextEffectStrategy (NONE/FLIP) + TextFlipDirection (DOWN/UP) + enableBlur (bool)
- **FR-19:** contentTransition 的翻页动画由 Rosen 图形引擎 `RSTextEffectFactoryCreator` 实现，ACE 通过 `TextEffect` 抽象类委托
- **FR-20:** marqueeOptions 的 `start` 字段控制启停；`start: true` 启动，`start: false` 停止
- **FR-21:** marqueeOptions.step > 0 时覆盖默认速度计算；duration 计算公式：`(textWidth + spaceWidth) * RACE_DURATION_RATIO / step`（`text_content_modifier.cpp:1721-1723`）
- **FR-22:** marqueeOptions.loop ≤ 0 或 MAX_INT 映射为 -1（无限循环）（`js_text.cpp:1770`）
- **FR-23:** marqueeOptions.delay 钳位 ≥ 0（`js_text.cpp:1784`）
- **FR-24:** marqueeOptions.fadeout 启用时两端渐隐宽度由 `marqueeGradientPercent_` 控制
- **FR-25:** marqueeOptions.marqueeStartPolicy = ON_FOCUS 时，仅 `marqueeFocused_ || marqueeHovered_` 为 true 才启动
- **FR-26:** marqueeOptions.spacing (@since 23) 指定两圈间距，默认 48vp
- **FR-27:** marqueeOptions.marqueeUpdatePolicy (@since 23) 控制文本更新时的滚动策略：DEFAULT（重启）或 PRESERVE_POSITION（保持位置）
- **FR-28:** onMarqueeStateChange 回调传入 3 种状态：START (0) / BOUNCE (1) / FINISH (2)
- **FR-29:** C-API `NODE_TEXT_MARQUEE_OPTIONS` 通过 `OH_ArkUI_TextMarqueeOptions` 结构体传入，支持 Create/Dispose/Get/Set 全套访问器

## 异常/豁免规则

- **EX-1:** decoration thicknessScale 为负值时回退到 1.0，不报错
- **EX-2:** textCase 枚举值超出 [0, 2] 范围时重置为 Normal，不报错
- **EX-3:** textShadow 传入空数组时等效于重置（无阴影）
- **EX-4:** shaderStyle 传入 undefined 时重置渐变和纯色，回退到 fontColor
- **EX-5:** contentTransition 在非数字文本上设置时静默忽略，不报错
- **EX-6:** marqueeOptions 在未设置 textOverflow(MARQUEE) 时静默忽略
- **EX-7:** marqueeOptions.delay 为负值时钳位到 0

## 恢复契约

- **RC-1:** decoration 重置时，4 个子属性均恢复默认值：type=NONE, color=Black, style=SOLID, thicknessScale=1.0（`node_text_modifier.cpp:1123-1134`）
- **RC-2:** textShadow 重置时恢复为单个全零 Shadow（radius=0, offsetX=0, offsetY=0, color=0）
- **RC-3:** textCase 重置时恢复为 Normal
- **RC-4:** shaderStyle 重置时同时清除 GradientShaderStyle 和 ColorShaderStyle
- **RC-5:** contentTransition 重置时 TextEffectStrategy 恢复为 NONE，清除 flipDirection 和 enableBlur
- **RC-6:** marqueeOptions 重置时所有子属性恢复默认值（start=true, step=4.0, loop=-1, direction=DEFAULT, delay=0, fadeout=false, startPolicy=DEFAULT, updatePolicy=DEFAULT, spacing=48vp）

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | UT | decoration type 四种枚举值渲染正确 |
| VM-2 | AC-1.5~AC-1.6 | UT | color + style 字段生效 |
| VM-3 | AC-1.7~AC-1.8 | UT | thicknessScale 边界值/负值/非法 style 回退 |
| VM-4 | AC-1.9~AC-1.10 | 手工验证 | NONE↔UNDERLINE alpha 动画过渡 |
| VM-5 | AC-1.11, AC-1.12 | UT | C-API 四参数格式；API 版本兼容 |
| VM-6 | AC-2.1~AC-2.3 | UT | 单阴影基本参数 |
| VM-7 | AC-2.4 | UT | 多阴影叠加 |
| VM-8 | AC-2.6~AC-2.7 | 手工验证 | fill 不生效 + coloringStrategy 互斥 |
| VM-9 | AC-2.8 | 手工验证 | 阴影动画过渡 |
| VM-10 | AC-3.1~AC-3.3 | UT | 三种 textCase 渲染 |
| VM-11 | AC-3.4~AC-3.5 | UT | Unicode + CJK 大小写转换 |
| VM-12 | AC-3.6 | 代码走查 | Span RE_CREATE flag |
| VM-13 | AC-4.1~AC-4.3 | 手工验证 | 三种 shader 子类渲染 |
| VM-14 | AC-4.4~AC-4.6 | 手工验证 + 代码走查 | 互斥逻辑 + fontColor 覆盖 |
| VM-15 | AC-5.1~AC-5.4 | 手工验证 | 数字翻页 + 非数字静默 |
| VM-16 | AC-6.1~AC-6.2 | UT | marqueeOptions 启动 + textOverflow 守卫 |
| VM-17 | AC-6.3~AC-6.6 | UT + 手工验证 | step/loop/delay/fromStart 参数 |
| VM-18 | AC-6.7~AC-6.8 | 手工验证 | fadeout 渐隐 + ON_FOCUS 策略 |
| VM-19 | AC-6.9~AC-6.10 | 手工验证 | spacing + updatePolicy (@since 23) |
| VM-20 | AC-6.11~AC-6.13 | UT | 状态回调 + C-API + 停止 |

---

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `decoration(value: DecorationStyleInterface)` | Public | 设置装饰线类型/颜色/样式/粗细 | AC-1.1~AC-1.12 |
| `textShadow(value: ShadowOptions \| Array<ShadowOptions>)` | Public | 设置文本阴影 | AC-2.1~AC-2.10 |
| `textCase(value: TextCase)` | Public | 设置大小写变换 | AC-3.1~AC-3.8 |
| `shaderStyle(shader: ShaderStyle)` | Public | 设置渐变着色 (@since 20) | AC-4.1~AC-4.9 |
| `contentTransition(transition: Optional<ContentTransition>)` | Public | 设置数字翻页动画 (@since 20) | AC-5.1~AC-5.6 |
| `marqueeOptions(options: Optional<TextMarqueeOptions>)` | Public | 跑马灯配置 (@since 18) | AC-6.1~AC-6.13 |
| `onMarqueeStateChange(callback: Callback<MarqueeState>)` | Public | 跑马灯状态回调 (@since 18) | AC-6.11 |

### 变更/废弃 API

| API 名称 | 变更类型 | 变更内容 | 关联 AC |
|----------|----------|----------|---------|
| `decoration(value)` | 变更 | @since 12: 参数类型从 `object` 变为 `DecorationStyleInterface`；@since 20: 新增 `thicknessScale` 字段 | AC-1.12 |
| `textShadow(value)` | 变更 | @since 11: 参数类型从 `ShadowOptions` 扩展为 `ShadowOptions \| Array<ShadowOptions>` | AC-2.4 |
| `marqueeOptions(options)` | 变更 | @since 23: TextMarqueeOptions 新增 `spacing`(LengthMetrics) 和 `marqueeUpdatePolicy` 字段 | AC-6.9, AC-6.10 |
| `contentTransition(transition)` | 变更 | @since 23: 新增 `@crossplatform` 标记 | AC-5.6 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — decoration @since 12 参数类型变更（object → DecorationStyleInterface）；textShadow @since 11 支持数组；decoration @since 20 新增 thicknessScale 字段
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** decoration/textCase @since 7；textShadow @since 10；marqueeOptions @since 18；shaderStyle/contentTransition @since 20
- **API 版本号策略:** 各 API 按 @since 标注引入版本，新增字段向后兼容（缺省使用默认值）

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| decoration 所有子属性触发 PROPERTY_UPDATE_MEASURE | 装饰线变更会导致完整重测量，影响性能 | AC-1.1~AC-1.10 |
| textShadow 触发 PROPERTY_UPDATE_MEASURE | 阴影变更触发重测量 | AC-2.1~AC-2.10 |
| textCase 实质改变文本内容 | TransformStrCase 在 AddText 前修改字符串，Span 级别触发 RE_CREATE | AC-3.1~AC-3.8 |
| shaderStyle gradient 存储在 AdvancedTextLayoutProperty | 渐变属性存储在高级扩展属性中，与 ColorShaderStyle 互斥 | AC-4.1~AC-4.9 |
| contentTransition 依赖 Rosen TextEffect | 翻页动画完全委托 Rosen 图形引擎，ACE 不自行实现 | AC-5.1~AC-5.6 |
| marqueeOptions 依赖 textOverflow(MARQUEE) | IsMarqueeOverflow() 在 13+ 处守卫，无 MARQUEE 模式时所有跑马灯逻辑跳过 | AC-6.1~AC-6.13 |
| shaderStyle/contentTransition 无 C-API | NDK 开发者无法通过 C-API 设置这两个属性 | AC-4.9, AC-5.6 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | decoration/textShadow/textCase 变更触发 MEASURE 不应导致额外帧延迟 | 帧率监控 | N/A（存量能力） |
| 内存 | 多阴影数组不应无上限增长 | 代码走查 | `std::vector<Shadow>` 由用户控制长度 |
| 安全 | N/A | — | — |
| 可靠性 | decoration 动画中途属性再次变更应正确取消旧动画 | UT | text_content_modifier_test |
| 问题定位 | decoration/textShadow/textCase/shaderStyle 属性序列化到 JSON 支持 Inspector 查看 | 代码走查 | text_layout_property.cpp:221 |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | decoration/shadow/textCase 为视觉装饰，不影响无障碍语义 | — |
| 大字体 | 部分 | textCase 不受字号影响；decoration/textShadow 跟随字号缩放 | AC-1.7 thicknessScale |
| 深色模式 | 是 | fontColor/decoration color 可通过 Resource 适配深色模式 | AC-1.5, AC-4.3 |
| 多窗口/分屏 | 否 | 无特殊影响 | — |
| 多用户 | 否 | 无特殊影响 | — |
| 版本升级 | 是 | decoration @since 12 类型变更需兼容旧版 | AC-1.12 |
| 生态兼容 | 部分 | shaderStyle/contentTransition 无 C-API，NDK 生态无法使用 | AC-4.9, AC-5.6 |

---

## 行为场景（Gherkin）

```gherkin
Feature: Text 装饰与样式
  作为应用开发者
  我想要为 Text 组件设置装饰线、阴影、大小写、渐变着色、翻页动画和跑马灯
  以便实现丰富的文本视觉效果

  # --- decoration ---

  Scenario Outline: 设置装饰线类型
    Given 一个 Text 组件
    When 调用 decoration({ type: <type> })
    Then 文本渲染 <result>

    Examples:
      | type                          | result         |
      | TextDecorationType.None       | 无装饰线       |
      | TextDecorationType.Underline  | 下划线         |
      | TextDecorationType.Overline   | 上划线         |
      | TextDecorationType.LineThrough| 删除线         |

  Scenario: decoration 装饰线样式和颜色
    Given 一个 Text 组件
    When 调用 decoration({ type: Underline, color: Color.Red, style: TextDecorationStyle.DASHED })
    Then 文本渲染红色虚线下划线

  Scenario: decoration thicknessScale 负值回退
    Given 一个 Text 组件
    When 调用 decoration({ type: Underline, thicknessScale: -2 })
    Then thicknessScale 回退为 1.0，装饰线以默认粗细渲染

  Scenario: decoration NONE 到 UNDERLINE alpha 动画
    Given 一个 Text 组件当前 decoration type 为 None
    When 将 decoration type 变更为 Underline
    Then 装饰线以 alpha 渐变动画过渡出现

  # --- textShadow ---

  Scenario: 单阴影效果
    Given 一个 Text 组件
    When 调用 textShadow({ radius: 10, color: Color.Gray, offsetX: 5, offsetY: 5 })
    Then 文本渲染灰色阴影，模糊半径 10px，偏移 (5, 5)

  Scenario: 多阴影叠加
    Given 一个 Text 组件
    When 调用 textShadow([shadow1, shadow2])
    Then 两层阴影按数组顺序叠加渲染

  Scenario: textShadow fill 属性不生效
    Given 一个 Text 组件
    When 调用 textShadow({ radius: 10, fill: true })
    Then fill 设置被忽略，仅渲染普通阴影

  # --- textCase ---

  Scenario Outline: 大小写变换
    Given 一个 Text 组件内容为 "Hello World"
    When 调用 textCase(<case>)
    Then 文本显示为 <display>

    Examples:
      | case               | display       |
      | TextCase.Normal    | Hello World   |
      | TextCase.LowerCase | hello world   |
      | TextCase.UpperCase | HELLO WORLD   |

  Scenario: Unicode 大小写转换
    Given 一个 Text 组件内容为 "café résumé"
    When 调用 textCase(TextCase.UpperCase)
    Then 文本显示为 "CAFÉ RÉSUMÉ"

  # --- shaderStyle ---

  Scenario: 线性渐变着色
    Given 一个 Text 组件
    When 调用 shaderStyle(new LinearGradientStyle({ colors: [[Color.Red, 0], [Color.Blue, 1]] }))
    Then 文本以红到蓝线性渐变着色渲染

  Scenario: shaderStyle 与 fontColor 互斥
    Given 一个 Text 组件设置了 fontColor(Color.Green)
    When 再调用 shaderStyle(new ColorShaderStyle(Color.Red))
    Then 文本以红色渲染（shaderStyle 覆盖 fontColor）

  Scenario: shaderStyle gradient 与 color 互斥
    Given 一个 Text 组件设置了 shaderStyle(new LinearGradientStyle(...))
    When 再调用 shaderStyle(new ColorShaderStyle(Color.Red))
    Then 渐变被清除，文本以纯红色渲染

  # --- contentTransition ---

  Scenario: 数字翻页动画
    Given 一个 Text 组件内容为 "123"
    And 已设置 contentTransition(new NumericTextTransition({ flipDirection: DOWN }))
    When 文本内容变为 "456"
    Then 数字以向下翻转动画过渡

  Scenario: 非数字文本无动画
    Given 一个 Text 组件内容为 "abc"
    And 已设置 contentTransition(new NumericTextTransition())
    When 文本内容变为 "def"
    Then 无翻页动画，文本直接切换

  # --- marqueeOptions ---

  Scenario: 跑马灯基本启动
    Given 一个 Text 组件已设置 textOverflow(TextOverflow.MARQUEE)
    When 调用 marqueeOptions({ start: true, loop: 3 })
    Then 文本滚动 3 圈后停止

  Scenario: 跑马灯依赖 textOverflow
    Given 一个 Text 组件未设置 textOverflow(TextOverflow.MARQUEE)
    When 调用 marqueeOptions({ start: true })
    Then 跑马灯不启动

  Scenario: 跑马灯 fadeout 效果
    Given 一个 Text 组件已设置 textOverflow(TextOverflow.MARQUEE)
    When 调用 marqueeOptions({ start: true, fadeout: true })
    Then 跑马灯两端显示渐隐效果

  Scenario: 跑马灯 ON_FOCUS 策略
    Given 一个 Text 组件已设置 textOverflow(TextOverflow.MARQUEE)
    And marqueeOptions({ start: true, marqueeStartPolicy: MarqueeStartPolicy.ON_FOCUS })
    When 组件未获得焦点
    Then 跑马灯不启动
    When 组件获得焦点
    Then 跑马灯开始滚动

  Scenario: onMarqueeStateChange 回调
    Given 一个 Text 组件已设置 textOverflow(TextOverflow.MARQUEE) 和 marqueeOptions({ start: true, loop: 1 })
    And 注册了 onMarqueeStateChange 回调
    When 跑马灯开始滚动
    Then 收到 MarqueeState.START 回调
    When 一圈滚动完毕回弹
    Then 收到 MarqueeState.BOUNCE 回调
    When 所有圈数完成
    Then 收到 MarqueeState.FINISH 回调
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Text decoration/textShadow/textCase 属性存储层级与脏标记策略"
  - repo: "openharmony/ace_engine"
    query: "shaderStyle foregroundBrush 渲染路径及与 fontColor 优先级"
  - repo: "openharmony/ace_engine"
    query: "contentTransition TextEffect Rosen 委托机制"
  - repo: "openharmony/ace_engine"
    query: "marqueeOptions 跑马灯动画生命周期与状态机"
```

**关键文档：**

- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/text.d.ts`
- SDK 静态版: `interface/sdk-js/api/arkui/component/text.static.d.ets`
- SDK 公共类型: `interface/sdk-js/api/@internal/component/ets/text_common.d.ts`
- 属性存储: `frameworks/core/components_ng/pattern/text/text_layout_property.h`
- 跑马灯动画: `frameworks/core/components_ng/pattern/text/text_content_modifier.cpp`
- C-API: `interfaces/native/native_node.h`, `interfaces/native/node/node_text_modifier.cpp`
