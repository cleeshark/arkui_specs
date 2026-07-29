# 特性规格

> Func-05-09-02-Feat-05 视觉样式与交互反馈：固化 RichEditor 组件视觉外观属性（光标颜色 `caretColor`、选中背景色 `selectedBackgroundColor`、滚动条颜色 `scrollBarColor`、滚动条状态 `barState`、占位符 `placeholder`、拖拽预览样式 `selectedDragPreviewStyle`）与交互反馈开关（返回拦截 `stopBackPress`、触觉反馈 `enableHapticFeedback`）的行为规格。这些属性仅影响视觉呈现与基础交互反馈，不涉及文本内容逻辑。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 视觉样式与交互反馈 (Visual Style & Interaction Feedback) |
| 特性编号 | Func-05-09-02-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 10+ 至 API 21+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 `caretColor` 行为规格 | 光标颜色属性存储与渲染路径，含主题回退默认值 |
| MODIFIED | 补齐 `selectedBackgroundColor` 行为规格 | 选中背景色属性含不透明度自动降级逻辑 |
| MODIFIED | 补齐 `scrollBarColor` 行为规格 | 滚动条颜色通过 ScrollController 更新，使用 ColorMetrics 解析 |
| MODIFIED | 补齐 `barState` 行为规格 | 滚动条显示状态存储于 LayoutProperty DisplayMode |
| MODIFIED | 补齐 `placeholder` 行为规格 | 占位符文本与样式（PlaceholderStyle）的解析与存储 |
| MODIFIED | 补齐 `selectedDragPreviewStyle` 行为规格 | 拖拽预览背景色存储于 LayoutProperty，含 JsView/非 JsView 双路径 |
| MODIFIED | 补齐 `stopBackPress` 行为规格 | 返回键拦截开关，影响自定义键盘场景的返回事件传递 |
| MODIFIED | 补齐 `enableHapticFeedback` 行为规格 | 触觉反馈开关，控制长按与滑动索引变化时的振动反馈 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/09-text-components/02-rich-editor/design.md` | 已创建 |

---

## 用户故事

### US-1: 光标颜色设置（caretColor）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件的光标颜色,
**以便** 自定义编辑光标的视觉外观以匹配应用主题。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `caretColor(value: ResourceColor)` 传入有效颜色 THEN 通过 Bridge 解析颜色后调用 `ModelNG::SetCaretColor`，存储到 `RichEditorPattern::caretColor_`（`rich_editor_pattern.h:1383`），并触发 `selectOverlay_->UpdateHandleColor()` 更新选择句柄颜色（`rich_editor_pattern.cpp:14856-14861`） | 正常 |
| AC-1.2 | WHEN 调用 `caretColor(undefined)` THEN Bridge 调用 `resetRichEditorCaretColor`，Pattern 调用 `ResetCaretColor` 将 `caretColor_` 设为 `std::nullopt`（`rich_editor_pattern.cpp:14863-14868`） | 正常 |
| AC-1.3 | WHEN 未设置 `caretColor` 或重置后 THEN `GetCaretColor()` 回退到 `RichEditorTheme::GetCaretColor()` 默认值 `Color(0xff007dff)`，若主题不可用回退到常量 `SYSTEM_CARET_COLOR`（`rich_editor_pattern.cpp:11914-11922`, `rich_editor_theme.h:282`） | 边界 |
| AC-1.4 | WHEN 光标绘制 THEN `RichEditorOverlayModifier::PaintCaret` 使用 `caretColor_->Get()` 作为画笔颜色绘制光标线段（`rich_editor_overlay_modifier.cpp:231`） | 正常 |
| AC-1.5 | WHEN 预览文本下划线绘制 THEN 使用 `caretColor_->Get()` 作为下划线颜色（`rich_editor_overlay_modifier.cpp:196`） | 正常 |

### US-2: 选中背景色设置（selectedBackgroundColor）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件的文本选中背景色,
**以便** 自定义选中文本的高亮颜色。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `selectedBackgroundColor(value: ResourceColor)` 传入有效颜色 THEN 存储到 `RichEditorPattern::selectedBackgroundColor_`（`rich_editor_pattern.h:1384`）（`rich_editor_pattern.cpp:14870-14875`） | 正常 |
| AC-2.2 | WHEN 调用 `selectedBackgroundColor(undefined)` THEN Bridge 调用 `resetRichEditorSelectedBackgroundColor`（`arkts_native_rich_editor_bridge.cpp:2198-2207`） | 正常 |
| AC-2.3 | WHEN 未设置或重置 THEN `GetSelectedBackgroundColor()` 回退到 `RichEditorTheme::GetSelectedBackgroundColor()` 默认值 `Color(0xff007dff)`，若主题不可用回退到 `SYSTEM_SELECT_BACKGROUND_COLOR`（`rich_editor_pattern.cpp:11924-11933`, `rich_editor_theme.h:283`） | 边界 |
| AC-2.4 | WHEN 选中背景色 Alpha 值 == 255（完全不透明） THEN 自动调用 `ChangeOpacity(0.2f)` 将不透明度降为 0.2（`rich_editor_pattern.cpp:11935-11936`） | 边界 |
| AC-2.5 | WHEN Overlay 绘制内容 THEN `DrawContent` 调用 `SetSelectedColor(GetSelectedBackgroundColor().GetValue())` 设置选中文本的高亮背景色（`rich_editor_overlay_modifier.cpp:307`） | 正常 |

### US-3: 滚动条颜色设置（scrollBarColor）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件的滚动条颜色,
**以便** 自定义滚动条外观以匹配应用主题。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `scrollBarColor(value: arkui_Graphics_ColorMetrics)` THEN Bridge 使用 `ParseColorMetricsToColor` 解析 ColorMetrics 为 Color，调用 `scrollController_->UpdateScrollBarColor(value, true)` 更新滚动条颜色（`arkts_native_rich_editor_bridge.cpp:3131-3149`, `rich_editor_model_ng.cpp:1147-1151`） | 正常 |
| AC-3.2 | WHEN 调用 `scrollBarColor(undefined)` 或解析失败 THEN Bridge 调用 `resetRichEditorScrollBarColor`（`arkts_native_rich_editor_bridge.cpp:3144`） | 正常 |
| AC-3.3 | WHEN 未设置滚动条颜色 THEN `GetScrollBarColor()` 从 `RichEditorLayoutProperty::GetScrollBarColor()` 读取，若未设置则回退到 `ScrollBarTheme::GetForegroundColor()`（`rich_editor_pattern.cpp:14274-14283`） | 边界 |
| AC-3.4 | WHEN 颜色配置更新（深色模式切换等）THEN `HandleColorConfigurationUpdate` 调用 `scrollController_->UpdateScrollBarColor(GetScrollBarColor())` 刷新滚动条颜色（`rich_editor_pattern.cpp:6192`） | 正常 |

### US-4: 滚动条状态设置（barState）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件的滚动条显示状态,
**以便** 控制滚动条的显示策略（始终显示、自动、隐藏）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `barState(value: BarState)` 传入有效值 THEN Bridge 将 BarState 映射为 `DisplayMode` 枚举值，存储到 `RichEditorLayoutProperty::DisplayMode`（`arkts_native_rich_editor_bridge.cpp:2519-2544`, `rich_editor_model_ng.cpp:850-852`） | 正常 |
| AC-4.2 | WHEN JsView 模式且参数非 Number 或 Undefined THEN 不执行任何操作直接返回（`arkts_native_rich_editor_bridge.cpp:2530-2531`） | 边界 |
| AC-4.3 | WHEN JsView 模式且 BarState 值超出 `[DisplayMode::OFF, DisplayMode::ON]` 范围 THEN 不执行设置操作（`arkts_native_rich_editor_bridge.cpp:2540-2541`） | 边界 |
| AC-4.4 | WHEN 未设置 barState THEN `GetBarState()` 返回默认值 `DisplayMode::AUTO`（`rich_editor_model_ng.cpp:860-863`） | 边界 |

### US-5: 占位符设置（placeholder）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件的占位符文本和样式,
**以便** 在编辑器内容为空时显示提示信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `placeholder(value: ResourceStr, style?: PlaceholderStyle)` THEN Bridge 解析文本值和可选样式，将各属性写入 `RichEditorLayoutProperty`（Placeholder/PlaceholderFontSize/PlaceholderFontWeight/PlaceholderItalicFontStyle/PlaceholderTextColor/PlaceholderFontFamily）（`arkts_native_rich_editor_bridge.cpp:1672-1714`, `rich_editor_model_ng.cpp:386-404`） | 正常 |
| AC-5.2 | WHEN PlaceholderStyle 含 font 子对象 THEN `ParsePlaceholderStyle` 从 font 对象解析 fontSize/fontStyle/fontWeight/fontFamilies（`arkts_native_rich_editor_bridge.cpp:1644-1648`） | 正常 |
| AC-5.3 | WHEN PlaceholderStyle 含 fontColor THEN 解析为 Color 存入 fontColorOpt（`arkts_native_rich_editor_bridge.cpp:1649-1656`） | 正常 |
| AC-5.4 | WHEN PlaceholderStyle 未提供 font 属性 THEN 从 `TextTheme::GetTextStyle()` 获取默认字体大小、字族、字重、字体样式（`arkts_native_rich_editor_bridge.cpp:1661-1666`） | 边界 |
| AC-5.5 | WHEN 调用 `placeholder(undefined)` THEN Bridge 调用 `resetRichEditorPlaceholder`（`arkts_native_rich_editor_bridge.cpp:1717-1726`） | 正常 |

### US-6: 拖拽预览样式设置（selectedDragPreviewStyle）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件选中文本拖拽时的预览样式,
**以便** 自定义拖拽预览的背景颜色。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `selectedDragPreviewStyle(value: SelectedDragPreviewStyle)` THEN Bridge 解析颜色值，存储到 `RichEditorLayoutProperty::SelectedDragPreviewStyle`（`arkts_native_rich_editor_bridge.cpp:3166-3201`, `rich_editor_model_ng.cpp:1218-1221`） | 正常 |
| AC-6.2 | WHEN JsView 模式且参数为对象 THEN 从对象的 `color` 属性解析颜色（`arkts_native_rich_editor_bridge.cpp:3183-3191`） | 正常 |
| AC-6.3 | WHEN 非 JsView 模式 THEN 直接通过 `ParseJsColorAlpha` 解析颜色参数（`arkts_native_rich_editor_bridge.cpp:3194-3198`） | 正常 |
| AC-6.4 | WHEN 未设置 selectedDragPreviewStyle THEN `GetSelectedDragPreviewStyleColor()` 回退到 `RichEditorTheme::GetDragBackgroundColor()` 默认值 `Color::WHITE`（`rich_editor_pattern.cpp:11619-11628`, `rich_editor_theme.h:284`） | 边界 |
| AC-6.5 | WHEN 创建拖拽节点 THEN `CreateDragNode` 使用 `GetSelectedDragPreviewStyleColor()` 设置 `info.dragBackgroundColor`（`rich_editor_pattern.cpp:9987`） | 正常 |

### US-7: 返回键拦截（stopBackPress）

**作为** 应用开发者,
**我想要** 控制 RichEditor 组件是否拦截返回键,
**以便** 在自定义键盘场景下决定是否将返回事件传递给应用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `stopBackPress(value: boolean)` THEN 存储到 `RichEditorPattern::isStopBackPress_`（默认 true）（`rich_editor_pattern.h:1460`, `rich_editor_pattern.cpp:15017-15019`） | 正常 |
| AC-7.2 | WHEN 调用 `stopBackPress(undefined)` 或非布尔值 THEN Bridge 调用 `resetRichEditorStopBackPress`（`arkts_native_rich_editor_bridge.cpp:2643-2657`） | 正常 |
| AC-7.3 | WHEN 自定义键盘已附加且组件有焦点且 `IsStopBackPress()` 为 false THEN `HandleOnKeyBack` 返回 false 以确保 `OnBackPressed` 能被正确触发，并调用 `HandleOnEscape()`（`rich_editor_pattern.cpp:8048-8053`） | 边界 |
| AC-7.4 | WHEN Android 平台且编辑状态同步 THEN `editingValue.stopBackPress` 设为 `IsStopBackPress()` 的值（`rich_editor_pattern.cpp:6254`） | 正常 |

### US-8: 触觉反馈开关（enableHapticFeedback）

**作为** 应用开发者,
**我想要** 控制 RichEditor 组件是否启用触觉反馈,
**以便** 在长按和滑动选择时控制振动反馈的开启与关闭。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `enableHapticFeedback(value: boolean)` THEN 存储到 `RichEditorPattern::isEnableHapticFeedback_`（默认 true）（`rich_editor_pattern.h:1446`, `rich_editor_pattern.cpp:14937-14940`） | 正常 |
| AC-8.2 | WHEN 调用 `enableHapticFeedback(undefined)` 或非布尔值 THEN Bridge 调用 `resetRichEditorEnableHapticFeedback`（`arkts_native_rich_editor_bridge.cpp:2907-2922`） | 正常 |
| AC-8.3 | WHEN 长按事件触发且 `isEnableHapticFeedback_` 为 true THEN `StartVibratorByLongPress` 调用 `VibratorUtils::StartVibraFeedback("longPress.light")` 触发长按振动反馈（`rich_editor_pattern.cpp:4682-4685`） | 正常 |
| AC-8.4 | WHEN 长按事件触发且 `isEnableHapticFeedback_` 为 false THEN `StartVibratorByLongPress` 因 `CHECK_NULL_VOID` 直接返回，不触发振动（`rich_editor_pattern.cpp:4684`） | 边界 |
| AC-8.5 | WHEN 滑动索引变化且 `isEnableHapticFeedback_` 为 true 且 `currentIndex != preIndex` THEN `StartVibratorByIndexChange` 调用 `VibratorUtils::StartVibraFeedback("slide")` 触发滑动振动反馈（`rich_editor_pattern.cpp:8935-8938`） | 正常 |
| AC-8.6 | WHEN 滑动索引变化但 `currentIndex == preIndex` THEN 不触发振动反馈（`rich_editor_pattern.cpp:8937`） | 边界 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1, R-2 | N/A（存量） | 代码审查 | `rich_editor_pattern.cpp:14856-14868, 11914-11922`, `rich_editor_overlay_modifier.cpp:196, 231` |
| AC-2.1~2.5 | R-3, R-4 | N/A | 代码审查 | `rich_editor_pattern.cpp:14870-14875, 11924-11936`, `rich_editor_overlay_modifier.cpp:307` |
| AC-3.1~3.4 | R-5, R-6 | N/A | 代码审查 | `rich_editor_model_ng.cpp:1147-1151, 1210-1215`, `rich_editor_pattern.cpp:14274-14283, 6192` |
| AC-4.1~4.4 | R-7, R-8 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:2519-2544`, `rich_editor_model_ng.cpp:850-863` |
| AC-5.1~5.5 | R-9, R-10 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:1637-1714`, `rich_editor_model_ng.cpp:386-404` |
| AC-6.1~6.5 | R-11, R-12 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:3166-3201`, `rich_editor_pattern.cpp:11619-11628, 9987` |
| AC-7.1~7.4 | R-13, R-14 | N/A | 代码审查 | `rich_editor_pattern.cpp:15017-15024, 8048-8053, 6254` |
| AC-8.1~8.6 | R-15, R-16 | N/A | 代码审查 | `rich_editor_pattern.cpp:14937-14945, 4682-4685, 8935-8938` |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `caretColor(value: ResourceColor)` 传入有效颜色 | Bridge 解析颜色 → `SetCaretColor` → 存入 `caretColor_` → 若 SelectOverlay 在线则 `UpdateHandleColor()` | `caretColor_` 类型为 `std::optional<Color>`（`rich_editor_pattern.h:1383`） | AC-1.1, AC-1.4 |
| R-2 | 边界 | 未设置 caretColor 或调用 reset | `GetCaretColor()` 回退到 `RichEditorTheme::GetCaretColor()` = `Color(0xff007dff)`；主题不可用时回退到 `SYSTEM_CARET_COLOR` | 主题回退链：用户值 → 主题默认 → 编译期常量 | AC-1.2, AC-1.3 |
| R-3 | 行为 | 调用 `selectedBackgroundColor(value: ResourceColor)` 传入有效颜色 | `SetSelectedBackgroundColor` 存入 `selectedBackgroundColor_` | `selectedBackgroundColor_` 类型为 `std::optional<Color>`（`rich_editor_pattern.h:1384`） | AC-2.1, AC-2.5 |
| R-4 | 边界 | 选中背景色 Alpha == 255（完全不透明） | 自动调用 `ChangeOpacity(0.2f)` 将不透明度降为 0.2 | 常量 `COLOR_OPAQUE = 255`，`DEFAILT_OPACITY = 0.2f`（`rich_editor_pattern.cpp:134-135`） | AC-2.3, AC-2.4 |
| R-5 | 行为 | 调用 `scrollBarColor(value: arkui_Graphics_ColorMetrics)` 传入有效值 | Bridge 使用 `ParseColorMetricsToColor` 解析 → `scrollController_->UpdateScrollBarColor(value, true)` | 参数类型为 `arkui_Graphics_ColorMetrics`，非普通 ResourceColor | AC-3.1 |
| R-6 | 边界 | 未设置 scrollBarColor | `GetScrollBarColor()` 从 LayoutProperty 读取，未设置则回退到 `ScrollBarTheme::GetForegroundColor()` | 回退链：LayoutProperty → ScrollBarTheme | AC-3.3, AC-3.4 |
| R-7 | 行为 | 调用 `barState(value: BarState)` 传入有效值 | Bridge 映射为 `DisplayMode` → 存入 `RichEditorLayoutProperty::DisplayMode` | DisplayMode 枚举：OFF / AUTO / ON | AC-4.1 |
| R-8 | 边界 | JsView 模式 BarState 值超出 `[OFF, ON]` 范围 | 不执行设置操作 | 校验：`barStateVal >= OFF && <= ON`（`arkts_native_rich_editor_bridge.cpp:2540-2541`） | AC-4.3, AC-4.4 |
| R-9 | 行为 | 调用 `placeholder(value, style?)` 传入有效文本和样式 | Bridge 解析文本和 PlaceholderStyle，写入 7 个 LayoutProperty 字段 | PlaceholderStyle 含 font（fontSize/fontStyle/fontWeight/fontFamilies）和 fontColor | AC-5.1, AC-5.2 |
| R-10 | 边界 | PlaceholderStyle 未提供 font 属性 | 从 `TextTheme::GetTextStyle()` 获取默认字体属性 | 默认值来源：`arkts_native_rich_editor_bridge.cpp:1661-1666` | AC-5.4 |
| R-11 | 行为 | 调用 `selectedDragPreviewStyle(value)` 传入有效值 | JsView 从对象 `color` 属性解析；非 JsView 直接 `ParseJsColorAlpha` → 存入 LayoutProperty | 存储于 `RichEditorLayoutProperty::SelectedDragPreviewStyle`，含 `PROPERTY_UPDATE_MEASURE` 标志 | AC-6.1, AC-6.2, AC-6.3 |
| R-12 | 边界 | 未设置 selectedDragPreviewStyle | `GetSelectedDragPreviewStyleColor()` 回退到 `RichEditorTheme::GetDragBackgroundColor()` = `Color::WHITE` | 主题不可用时回退到 `Color::WHITE` | AC-6.4, AC-6.5 |
| R-13 | 行为 | 调用 `stopBackPress(value: boolean)` | 存入 `isStopBackPress_`（默认 true） | `isStopBackPress_` 类型 bool，初始值 true（`rich_editor_pattern.h:1460`） | AC-7.1, AC-7.2 |
| R-14 | 边界 | 自定义键盘附加且焦点有效且 `isStopBackPress_` 为 false | `HandleOnKeyBack` 返回 false，调用 `HandleOnEscape()`，允许 `OnBackPressed` 被触发 | 仅 Android 平台生效（`#ifdef ANDROID_PLATFORM`） | AC-7.3, AC-7.4 |
| R-15 | 行为 | 调用 `enableHapticFeedback(value: boolean)` | 存入 `isEnableHapticFeedback_`（默认 true） | `isEnableHapticFeedback_` 类型 bool，初始值 true（`rich_editor_pattern.h:1446`） | AC-8.1, AC-8.2 |
| R-16 | 行为 | 长按或滑动索引变化且 `isEnableHapticFeedback_` 为 true | 长按触发 `StartVibraFeedback("longPress.light")`；滑动（索引变化）触发 `StartVibraFeedback("slide")` | 滑动需 `currentIndex != preIndex` 才触发 | AC-8.3~8.6 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5（光标颜色） | 代码审查 | `caretColor_` 存储、主题回退、OverlayModifier 绘制路径 |
| VM-2 | AC-2.1~2.5（选中背景色） | 代码审查 | `selectedBackgroundColor_` 存储、不透明度降级、Overlay 高亮绘制 |
| VM-3 | AC-3.1~3.4（滚动条颜色） | 代码审查 | ColorMetrics 解析、ScrollController 更新、主题回退 |
| VM-4 | AC-4.1~4.4（滚动条状态） | 代码审查 | BarState → DisplayMode 映射、范围校验、默认值 |
| VM-5 | AC-5.1~5.5（占位符） | 代码审查 | PlaceholderStyle 解析、LayoutProperty 写入、默认字体回退 |
| VM-6 | AC-6.1~6.5（拖拽预览样式） | 代码审查 | JsView/非 JsView 双路径、LayoutProperty 存储、主题回退 |
| VM-7 | AC-7.1~7.4（返回键拦截） | 代码审查 | `isStopBackPress_` 存储、HandleOnKeyBack 逻辑、编辑状态同步 |
| VM-8 | AC-8.1~8.6（触觉反馈） | 代码审查 | `isEnableHapticFeedback_` 存储、长按/滑动振动触发路径 |

## API 变更分析

> 本特性为存量规格补录，记录各 API 的引入版本和当前签名。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `caretColor(value: ResourceColor \| undefined)` | Public (@since 12) | `ResourceColor` 颜色值或 `undefined` | `this` | N/A | 设置光标颜色 | AC-1.1~1.5 |
| `selectedBackgroundColor(value: ResourceColor \| undefined)` | Public (@since 12) | `ResourceColor` 颜色值或 `undefined` | `this` | N/A | 设置选中文本背景色 | AC-2.1~2.5 |
| `scrollBarColor(value: arkui_Graphics_ColorMetrics \| undefined)` | Public (@since 21) | `arkui_Graphics_ColorMetrics` 颜色值或 `undefined` | `this` | N/A | 设置滚动条颜色 | AC-3.1~3.4 |
| `barState(value: BarState \| undefined)` | Public (@since 13) | `BarState` 枚举值或 `undefined` | `this` | N/A | 设置滚动条显示状态 | AC-4.1~4.4 |
| `placeholder(value: ResourceStr \| undefined, style?: PlaceholderStyle)` | Public (@since 12) | `ResourceStr` 文本值，`PlaceholderStyle` 可选样式 | `this` | N/A | 设置占位符文本和样式 | AC-5.1~5.5 |
| `selectedDragPreviewStyle(value: SelectedDragPreviewStyle \| undefined)` | Public | `SelectedDragPreviewStyle` 样式或 `undefined` | `this` | N/A | 设置拖拽预览背景样式 | AC-6.1~6.5 |
| `stopBackPress(value: boolean \| undefined)` | Public (@since 18) | `boolean` 开关或 `undefined` | `this` | N/A | 设置返回键拦截开关 | AC-7.1~7.4 |
| `enableHapticFeedback(value: boolean \| undefined)` | Public (@since 13) | `boolean` 开关或 `undefined` | `this` | N/A | 设置触觉反馈开关 | AC-8.1~8.6 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**caretColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `caretColor(value: ResourceColor \| undefined): this` |
| 返回值 | `this` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor \| undefined | 否 | 主题默认 `Color(0xff007dff)` | undefined 时重置为主题默认值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 ResourceColor | 存入 `caretColor_`，更新选择句柄颜色 | AC-1.1 |
| 2 | 传入 undefined | 重置 `caretColor_` 为 nullopt，回退到主题默认值 | AC-1.2 |
| 3 | 光标绘制 | OverlayModifier 使用 `caretColor_` 绘制光标线段和预览文本下划线 | AC-1.4, AC-1.5 |

**selectedBackgroundColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selectedBackgroundColor(value: ResourceColor \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor \| undefined | 否 | 主题默认 `Color(0xff007dff)` | Alpha=255 时自动降为 0.2 不透明度 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效颜色 | 存入 `selectedBackgroundColor_` | AC-2.1 |
| 2 | 颜色完全不透明（Alpha=255） | 自动 `ChangeOpacity(0.2f)` | AC-2.4 |
| 3 | Overlay 绘制 | 通过 `SetSelectedColor` 设置选中文本高亮背景 | AC-2.5 |

**scrollBarColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `scrollBarColor(value: arkui_Graphics_ColorMetrics \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | arkui_Graphics_ColorMetrics \| undefined | 否 | `ScrollBarTheme::GetForegroundColor()` | 使用 `ParseColorMetricsToColor` 解析，非普通颜色解析 |

**barState**

| 属性 | 值 |
|------|-----|
| 函数签名 | `barState(value: BarState \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | BarState \| undefined | 否 | `DisplayMode::AUTO` | BarState 映射为 DisplayMode：OFF/AUTO/ON |

**placeholder**

| 属性 | 值 |
|------|-----|
| 函数签名 | `placeholder(value: ResourceStr \| undefined, style?: PlaceholderStyle): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1~5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceStr \| undefined | 否 | 空字符串 | 占位符文本 |
| style | PlaceholderStyle | 否 | TextTheme 默认 | 含 font（fontSize/fontStyle/fontWeight/fontFamilies）和 fontColor |

**selectedDragPreviewStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `selectedDragPreviewStyle(value: SelectedDragPreviewStyle \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1~6.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | SelectedDragPreviewStyle \| undefined | 否 | `Color::WHITE` | JsView 从对象 `color` 属性解析；非 JsView 直接 ParseJsColorAlpha |

**stopBackPress**

| 属性 | 值 |
|------|-----|
| 函数签名 | `stopBackPress(value: boolean \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-7.1~7.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean \| undefined | 否 | `true` | 控制 Android 平台自定义键盘场景的返回事件传递 |

**enableHapticFeedback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableHapticFeedback(value: boolean \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-8.1~8.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean \| undefined | 否 | `true` | 控制长按和滑动索引变化时的振动反馈 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — `caretColor`/`selectedBackgroundColor`/`placeholder` 自 API 12+ 引入；`barState`/`enableHapticFeedback` 自 API 13+ 引入；`stopBackPress` 自 API 18+ 引入；`scrollBarColor` 自 API 21+ 引入
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12（caretColor/selectedBackgroundColor/placeholder），API 13（barState/enableHapticFeedback），API 18（stopBackPress），API 21（scrollBarColor）
- **API 版本号策略:** 各属性按引入版本标注 `@since`；`selectedDragPreviewStyle` 无独立版本标注，随 RichEditor 组件一同引入

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 颜色属性多级回退 | `caretColor`/`selectedBackgroundColor`/`scrollBarColor`/`selectedDragPreviewStyle` 均采用"用户值 → LayoutProperty → 主题默认 → 编译期常量"的多级回退策略 | AC-1.3, AC-2.3, AC-3.3, AC-6.4 |
| 选中背景色不透明度自动降级 | 当 Alpha=255 时自动降为 0.2，避免完全不透明背景遮挡文本 | AC-2.4 |
| scrollBarColor 使用 ColorMetrics 解析 | 与其他颜色属性不同，`scrollBarColor` 使用 `arkui_Graphics_ColorMetrics` 类型和 `ParseColorMetricsToColor` 解析器 | AC-3.1 |
| barState 存储于 LayoutProperty | `BarState` 映射为 `DisplayMode` 枚举后存入 `RichEditorLayoutProperty::DisplayMode`，非 Pattern 成员变量 | AC-4.1 |
| stopBackPress 仅 Android 平台生效 | 返回键拦截逻辑在 `#ifdef ANDROID_PLATFORM` 条件编译内，仅 Android 平台有效 | AC-7.3 |
| 触觉反馈需索引变化才触发 | 滑动振动反馈需 `currentIndex != preIndex`，相同索引不触发 | AC-8.5, AC-8.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可测试性 | 所有颜色属性支持 Get 方法用于回读验证 | 代码审查 | `rich_editor_model_ng.cpp:542, 518, 1311, 1228` |
| 可靠性 | 颜色属性采用 `std::optional` 存储，主题不可用时有多级回退 | 代码审查 | `rich_editor_pattern.h:1383-1384` |
| 安全性 | stopBackPress 不影响非自定义键盘场景的返回行为 | 代码审查 | `rich_editor_pattern.cpp:8043-8055` |

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
| 无障碍 | 是 | 触觉反馈开关影响无障碍用户的振动反馈体验 | AC-8.3~8.6 |
| 大字体 | N/A | 视觉样式属性不涉及大字体适配 | — |
| 深色模式 | 是 | `HandleColorConfigurationUpdate` 在深色模式切换时刷新光标颜色、选中背景色、滚动条颜色 | AC-1.1, AC-3.4 |
| 多窗口/分屏 | N/A | 视觉样式属性不涉及窗口模式 | — |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | 各属性跨 API 12-21+ 引入，需关注版本兼容性 | AC-1.1~8.6 |
| 生态兼容 | N/A | — | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RichEditor 视觉样式与交互反馈
  作为应用开发者
  我想要自定义 RichEditor 的视觉外观和交互反馈
  以便匹配应用主题和交互需求

  Scenario: 设置光标颜色
    Given RichEditor 组件已创建
    When 调用 caretColor(Color.Red)
    Then 光标颜色存储为 caretColor_ = Color.Red
    And 选择句柄颜色同步更新
    When 光标绘制时
    Then OverlayModifier 使用 Color.Red 绘制光标线段

  Scenario: 选中背景色不透明度降级
    Given RichEditor 组件已创建
    When 调用 selectedBackgroundColor(Color(0xFFFF0000))（Alpha=255）
    Then selectedBackgroundColor_ 存储原始颜色
    When GetSelectedBackgroundColor() 被调用
    Then 返回颜色 Alpha 自动降为 0.2（ChangeOpacity(0.2f)）

  Scenario: 滚动条颜色设置与回退
    Given RichEditor 组件未设置 scrollBarColor
    When GetScrollBarColor() 被调用
    Then 回退到 ScrollBarTheme::GetForegroundColor()
    When 调用 scrollBarColor(ColorMetrics)
    Then scrollController_ 更新滚动条颜色

  Scenario: 占位符样式默认值回退
    Given 调用 placeholder("hint", { font: {} })
    When ParsePlaceholderStyle 解析 font 属性
    Then 未提供的字体属性从 TextTheme::GetTextStyle() 获取默认值

  Scenario: 触觉反馈控制
    Given RichEditor 组件 enableHapticFeedback 默认为 true
    When 长按事件触发
    Then 调用 VibratorUtils::StartVibraFeedback("longPress.light")
    When 调用 enableHapticFeedback(false)
    And 长按事件触发
    Then 不触发振动反馈（CHECK_NULL_VOID 返回）

  Scenario: 返回键拦截（Android 平台）
    Given 自定义键盘已附加且组件有焦点
    And stopBackPress 为 false
    When 返回键按下
    Then HandleOnKeyBack 返回 false
    And 调用 HandleOnEscape()
    And 确保 OnBackPressed 能被触发
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（视觉样式与交互反馈，不含文本内容逻辑、布局算法、渲染细节）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern caretColor_ selectedBackgroundColor_ storage and theme fallback in GetCaretColor GetSelectedBackgroundColor"
  - repo: "openharmony/ace_engine"
    query: "RichEditorModelNG SetScrollBarColor UpdateScrollBarColor via ScrollController and ColorMetrics parsing"
  - repo: "openharmony/ace_engine"
    query: "RichEditorOverlayModifier PaintCaret caretColor_ SetSelectedColor rendering path"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern enableHapticFeedback_ StartVibratorByLongPress StartVibratorByIndexChange VibratorUtils"
  - repo: "openharmony/ace_engine"
    query: "RichEditorBridge SetPlaceholder ParsePlaceholderStyle PlaceholderStyle font fontColor parsing"
```

**关键文档：**
- SDK 静态版声明: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets`
- 主题定义: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_theme.h`
- Pattern 成员变量: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.h`
- Overlay 渲染: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_overlay_modifier.cpp`
