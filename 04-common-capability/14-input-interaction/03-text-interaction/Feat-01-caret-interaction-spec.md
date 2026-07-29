# 特性规格

> Func-04-14-03-Feat-01 光标交互：固化 caretColor/caretStyle/caretPosition/setCaretOffset/getCaretOffset/getCaretRect 六项光标交互能力的行为规格，覆盖 Text/TextInput/TextArea/RichEditor 四组件。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 光标交互 (Caret Interaction) |
| 特性编号 | Func-04-14-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 10/11/12/14/18/22/23/24/26 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | caretColor 行为规格 | 覆盖 Text/TextInput/TextArea/RichEditor 四组件，含存储层、默认值、undefined 处理 |
| ADDED | caretStyle 行为规格 | 覆盖 TextInput/TextArea，含 width/color 分拆、C-API 不对称 |
| ADDED | caretPosition 行为规格 | 覆盖 TextInput 属性与控制器方法，含 API 12 负值行为变更、超范围钳位 |
| ADDED | setCaretOffset/getCaretOffset/getCaretRect 行为规格 | 覆盖 RichEditor，含失败语义、未闪烁返回 undefined、坐标系与索引单位 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/14-input-interaction/03-text-interaction/design.md` | Baselined |

---

## 用户故事

### US-1: 设置光标颜色

**作为** 应用开发者,
**我想要** 通过 `.caretColor(color)` 设置文本组件的光标颜色,
**以便** 自定义光标与选择句柄的视觉外观以匹配应用主题。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 TextInput/TextArea 调用 `.caretColor(color: ResourceColor)` 且 color 为合法颜色 THEN 光标绘制颜色等于 color，且选择句柄颜色同步更新为 color（API 12+ 句柄颜色等同光标颜色） | 正常 |
| AC-1.2 | WHEN 在 RichEditor 调用 `.caretColor(value: ResourceColor)` THEN `RichEditorPattern::caretColor_` 被赋值，`selectOverlay_->UpdateHandleColor()` 被同步调用，绘制时光标与句柄颜色均为 value | 正常 |
| AC-1.3 | WHEN 在 Text 调用 `.caretColor(color: ResourceColor)` THEN `TextLayoutProperty::CursorColor` 被更新，触发 `PROPERTY_UPDATE_MEASURE_SELF` 脏标记；选择句柄颜色取自 `GetHandleColor` | 正常 |
| AC-1.4 | WHEN 在 TextInput/TextArea 调用 `.caretColor(undefined)` THEN 调用 `ResetCaretColor`，`CursorColor` PaintProperty 被重置，`CaretColorFlagByUser` 置为 false，光标颜色回退到主题默认（token `colors->Brand()`） | 异常 |
| AC-1.5 | WHEN 在 RichEditor 调用 `.caretColor(undefined)` THEN `ResetRichEditorCaretColor` 将 `caretColor_` 重置为 `richEditorTheme->GetCaretColor()`（#007DFF） | 异常 |
| AC-1.6 | WHEN 在 Text 调用 `.caretColor(undefined)` 或颜色解析失败 THEN fallback 到 `theme->GetCaretColor()`（硬编码 `#006CDE`），并将该 fallback 值写入 `CursorColor` LayoutProperty（非 reset，是 set） | 异常 |
| AC-1.7 | WHEN TextInput/TextArea 的 `CaretColorFlagByUser` 为 false 且主题/色盲模式变更 THEN 重新应用 `textFieldTheme->GetCursorColor()` 到 `CursorColor` PaintProperty，触发 `PROPERTY_UPDATE_RENDER` | 恢复 |
| AC-1.8 | WHEN 已通过 `.caretColor(A)` 设置颜色后再通过 `.caretStyle({color: B})` 设置颜色 THEN `CursorColor` PaintProperty 最终值为 B（last-write-wins，无优先级规则） | 边界 |

### US-2: 设置光标样式（宽度与颜色）

**作为** 应用开发者,
**我想要** 通过 `.caretStyle({width, color})` 一次性设置光标宽度与颜色,
**以便** 精确控制光标的视觉粗细与色调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 在 TextInput/TextArea 调用 `.caretStyle({width: w})` 且 w 为合法正数 Length THEN `TextFieldPaintProperty::CursorWidth` 被更新为 w（vp），触发 `PROPERTY_UPDATE_RENDER`，绘制时光标线宽度为 w | 正常 |
| AC-2.2 | WHEN 在 TextInput/TextArea 调用 `.caretStyle({color: c})` 且 c 为合法颜色 THEN `CursorColor` PaintProperty 被更新为 c（等同调用 `.caretColor(c)`），`CaretColorFlagByUser` 置为 true | 正常 |
| AC-2.3 | WHEN `.caretStyle({width})` 中 width 缺失、解析失败或为负值 THEN width fallback 到 `theme->GetCursorWidth()`（默认 2vp，`textfield_theme.h:187`），不早退 | 异常 |
| AC-2.4 | WHEN `.caretStyle` 对象不含 `color` 字段 THEN 不触及 `CursorColor`（`js_textfield.cpp:562` 检查 `HasProperty("color")`），光标颜色保持原值 | 异常 |
| AC-2.5 | WHEN 在 RichEditor 调用 `.caretStyle(...)` THEN 无此 API（RichEditor 不支持 caretStyle），光标宽度固定为常量 `CARET_WIDTH = 2vp`（`rich_editor_pattern.cpp:123`） | 边界 |
| AC-2.6 | WHEN 通过 C-API `NODE_TEXT_INPUT_CARET_STYLE` 设置 THEN 仅设置 `CursorWidth`（width），**不设置 color**（C-API 与 ArkTS 不对称） | 边界 |
| AC-2.7 | WHEN 通过 C-API 设置 TextArea `caretStyle` THEN 无对应 C-API 枚举（`NODE_TEXT_AREA_CARET_STYLE` 不存在），TextArea caretStyle 仅可通过 ArkTS 设置 | 边界 |

### US-3: 设置光标位置（TextInput）

**作为** 应用开发者,
**我想要** 通过 `.caretPosition(value)` 属性或 `TextInputController.caretPosition(value)` 方法设置光标在文本中的位置,
**以便** 程序化控制光标插入点（如验证后定位到错误字段末尾）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `TextInputController.caretPosition(value)` 且 0 ≤ value ≤ textLength THEN 光标移动到 value 位置（UTF-16 码元索引），`MoveCaretToContentRect` 执行 `std::clamp(value, 0, length)`，`UpdateCaretInfoToController` 更新控制器，`MarkDirtyNode(PROPERTY_UPDATE_RENDER)` | 正常 |
| AC-3.2 | WHEN 调用 `.caretPosition(value)` 属性且 value > textLength THEN value 被 `std::clamp` 钳位到 textLength，光标移动到文本末尾（移动生效） | 边界 |
| AC-3.3 | WHEN 在 API ≥ 12 调用 `caretPosition(value)` 且 value < 0 或解析失败 THEN value 钳为 0，光标移动到文本开头 | 异常 |
| AC-3.4 | WHEN 在 API < 12 调用 `caretPosition(value)` 且 value < 0 或解析失败 THEN 早退（no-op），光标位置不变 | 异常 |
| AC-3.5 | WHEN 调用 `.caretPosition(undefined)` 属性（静态 API） THEN 解析为 0，光标移动到文本开头 | 异常 |
| AC-3.6 | WHEN 调用 `caretPosition(value)` 时 TextInput 已聚焦（`HasFocus()` 为 true） THEN `StartTwinkling()` 被调用，光标开始闪烁 | 正常 |
| AC-3.7 | WHEN 调用 `caretPosition(value)` 时 TextInput 未聚焦 THEN `SetCaretPosition` 不调用 `RequestFocus`/`RequestKeyboard`，光标内部位置更新但**不闪烁**，不拉起 IME | 边界 |
| AC-3.8 | WHEN 调用 `caretPosition(value)` THEN `CloseSelectOverlay()` + `CancelDelayProcessOverlay()` + `TriggerAvoidOnCaretChange()` 被调用，已有选择浮层关闭 | 正常 |
| AC-3.9 | WHEN `caretPosition` 属性被设置 THEN 不存储为 Layout/Paint Property（一次性调用 `pattern->SetCaretPosition`），属性重建时不会自动重新应用 | 边界 |

### US-4: 读写光标偏移与矩形（RichEditor）

**作为** 应用开发者,
**我想要** 通过 `setCaretOffset/getCaretOffset/getCaretRect` 程序化设置与读取 RichEditor 的光标位置和矩形,
**以便** 实现精准的光标定位与避让计算（如弹窗避免遮挡光标）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `setCaretOffset(offset)` 且 0 ≤ offset ≤ textContentLength THEN `caretPosition_` 被更新为 offset，`FireOnSelectionChange(offset)` 触发，返回 true | 正常 |
| AC-4.2 | WHEN 调用 `setCaretOffset(offset)` 且 offset > textContentLength THEN `std::clamp` 计算 `correctPos = textContentLength`，`pos != correctPos` → 返回 false，`caretPosition_` **不被更新** | 边界 |
| AC-4.3 | WHEN 调用 `setCaretOffset(offset)` 且 offset < 0 THEN JS 桥接归一化为 -1（`js_richeditor.cpp:1602`），`correctPos = 0`，`pos != correctPos` → 返回 false，`caretPosition_` 不更新 | 异常 |
| AC-4.4 | WHEN 调用 `setCaretOffset(offset)` 时 RichEditor 处于预览文本态（`IsPreviewTextInputting()` 为 true） THEN 直接返回 false，不移动光标 | 异常 |
| AC-4.5 | WHEN 调用 `setCaretOffset(offset)` 时 RichEditor 已聚焦 THEN `StartTwinkling()` 被调用，光标开始闪烁，`CloseSelectOverlay()` + `ResetSelection()` 执行 | 正常 |
| AC-4.6 | WHEN 调用 `setCaretOffset(offset)` 时 RichEditor 未聚焦 THEN `caretPosition_` 仍被更新（若 offset 合法），但 `StartTwinkling` 因 `!IsCurrentFocus` 不执行，光标不闪烁；后续聚焦时光标出现在预置位置 | 边界 |
| AC-4.7 | WHEN 调用 `getCaretOffset()` 且控制器已绑定 Pattern THEN 返回 `caretPosition_`（int，静态返回 `int \| undefined`；动态返回 number，默认 -1 当未绑定）；**非聚焦仍返回存储值** | 正常 |
| AC-4.8 | WHEN 调用 `getCaretOffset()` 且控制器未绑定 Pattern（`pattern_` 弱引用升级失败） THEN 静态返回 undefined；动态返回 -1 | 异常 |
| AC-4.9 | WHEN 调用 `getCaretRect()` 且光标正在闪烁（`caretTwinkling_` 为 true） THEN 返回 `RectResult{x, y, width, height}`，坐标系相对 RichEditor 组件，width 为 `caretWidth`（2vp），height 为计算的光标高度 | 正常 |
| AC-4.10 | WHEN 调用 `getCaretRect()` 且光标未闪烁（`caretTwinkling_` 为 false，即未聚焦/未编辑） THEN `GetCaretRelativeRect` 返回 `RectF(-1,-1,-1,-1)`，JS 桥接 `CHECK_EQUAL_VOID(IsValid(), false)` 转为 undefined | 边界 |
| AC-4.11 | WHEN 调用 `getCaretRect()` 且控制器未绑定 Pattern THEN 返回 undefined（JS 桥接 `CHECK_NULL_VOID`） | 异常 |
| AC-4.12 | WHEN 通过 C-API `OH_ArkUI_TextEditorStyledStringController_SetCaretOffset` 调用且 controller/node 为 null THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`；否则返回 `ARKUI_ERROR_CODE_NO_ERROR`（**不传播 Pattern 的 boolean 结果**） | 边界 |
| AC-4.13 | WHEN 通过 C-API `OH_ArkUI_TextEditorStyledStringController_GetCaretRect` 调用且光标未闪烁 THEN Pattern 返回 `RectF(-1,-1,-1,-1)` 被原样拷贝到 out `ArkUI_Rect`（**C-API 无 undefined 路径**，调用方需自行检查负值） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1, R-5 | TASK-01 | 单测：设置 caretColor 后绘制颜色断言 | `text_field_paint_method.cpp:182`, `text_field_overlay_modifier.cpp:315` |
| AC-1.2 | R-1, R-6 | TASK-01 | 单测：RichEditor caretColor 设置后 caretColor_ 与 handleColor 同步 | `rich_editor_pattern.cpp:14906-14909`, `:9904` |
| AC-1.3 | R-2 | TASK-01 | 单测：Text caretColor 触发 MEASURE_SELF 脏标记 | `text_layout_property.h:210`, `text_model_ng.cpp:715` |
| AC-1.4 | R-3 | TASK-01 | 单测：TextInput undefined 触发 ResetCaretColor + flag 清零 | `js_textfield.cpp:515-517`, `text_field_model_ng.cpp:453-457` |
| AC-1.5 | R-3 | TASK-01 | 单测：RichEditor undefined 重置到主题 #007DFF | `rich_editor_dynamic_modifier.cpp:368-379` |
| AC-1.6 | R-4 | TASK-01 | 单测：Text undefined/解析失败 fallback #006CDE 并 set（非 reset） | `js_text.cpp:446-451`, `text_theme.cpp:35` |
| AC-1.7 | R-7 | TASK-01 | 单测：主题变更 + flag=false 重新应用主题色 | `text_field_pattern.cpp:6338-6341` |
| AC-1.8 | R-8 | TASK-01 | 单测：先 caretColor(A) 后 caretStyle({color:B}) → 最终 B | `js_textfield.cpp:562-574`, `text_field_model_ng.cpp:447-450` |
| AC-2.1 | R-9 | TASK-01 | 单测：caretStyle({width}) 设置 CursorWidth + RENDER | `js_textfield.cpp:543-558`, `text_field_model_ng.cpp:459-465` |
| AC-2.2 | R-8, R-9 | TASK-01 | 单测：caretStyle({color}) 等同 caretColor(color) | `js_textfield.cpp:562-574` |
| AC-2.3 | R-10 | TASK-01 | 单测：width 缺失/负值 fallback 2vp | `js_textfield.cpp:543,548,554`, `textfield_theme.h:187` |
| AC-2.4 | R-11 | TASK-01 | 单测：无 color 字段时不触及 CursorColor | `js_textfield.cpp:562` |
| AC-2.5 | R-12 | TASK-01 | 单测：RichEditor caretStyle 不存在；GetCaretWidth 返回 2vp 常量 | `rich_editor_pattern.cpp:123`, `:14236-14239` |
| AC-2.6 | R-13 | TASK-01 | 单测：C-API NODE_TEXT_INPUT_CARET_STYLE 仅设宽 | `style_modifier.cpp:5438-5450`, `node_text_input_modifier.cpp:2577-2594` |
| AC-2.7 | R-14 | TASK-01 | 单测：C-API 派发表无 NODE_TEXT_AREA_CARET_STYLE | `style_modifier.cpp:21316+` |
| AC-3.1 | R-15 | TASK-01 | 单测：caretPosition 合法值移动光标 + clamp | `text_field_pattern.cpp:8263-8279`, `text_select_controller.cpp:540-546` |
| AC-3.2 | R-16 | TASK-01 | 单测：超 textLength 钳位到末尾并移动 | `text_select_controller.cpp:546` |
| AC-3.3 | R-17 | TASK-01 | 单测：API>=12 负值钳为 0 | `js_textfield.cpp:586-588`, `js_text_editable_controller.cpp:69-70` |
| AC-3.4 | R-17 | TASK-01 | 单测：API<12 负值早退 | `js_textfield.cpp:591-596` |
| AC-3.5 | R-18 | TASK-01 | 单测：静态 undefined → 0 | `text_field_model_static.cpp:367-373` |
| AC-3.6 | R-19 | TASK-01 | 单测：已聚焦时 StartTwinkling | `text_field_pattern.cpp:8269-8271`, `:4090-4110` |
| AC-3.7 | R-20 | TASK-01 | 单测：未聚焦时不 RequestFocus/IME | `text_field_pattern.cpp:8263-8279` |
| AC-3.8 | R-21 | TASK-01 | 单测：CloseSelectOverlay + TriggerAvoidOnCaretChange | `text_field_pattern.cpp:8272-8274` |
| AC-3.9 | R-22 | TASK-01 | 单测：caretPosition 属性不存储，重建不重新应用 | `text_field_model_ng.cpp:467-473` |
| AC-4.1 | R-23 | TASK-01 | 单测：合法 offset 更新 caretPosition_ + 返回 true | `rich_editor_pattern.cpp:2389-2406`, `:2490-2510` |
| AC-4.2 | R-24 | TASK-01 | 单测：超范围返回 false 不更新 | `rich_editor_pattern.cpp:2491-2495` |
| AC-4.3 | R-24 | TASK-01 | 单测：负值返回 false 不更新 | `js_richeditor.cpp:1602`, `rich_editor_pattern.cpp:2491-2495` |
| AC-4.4 | R-25 | TASK-01 | 单测：预览文本态返回 false | `rich_editor_pattern.cpp:2386-2389` |
| AC-4.5 | R-19, R-26 | TASK-01 | 单测：已聚焦时 StartTwinkling | `rich_editor_pattern.cpp:2400-2402` |
| AC-4.6 | R-27 | TASK-01 | 单测：未聚焦时更新位置但不闪烁 | `rich_editor_pattern.cpp:2400` |
| AC-4.7 | R-28 | TASK-01 | 单测：非聚焦仍返回 caretPosition_ | `rich_editor_base_controller.cpp:32-39`, `rich_editor_pattern.cpp:2378-2382` |
| AC-4.8 | R-29 | TASK-01 | 单测：未绑定返回 undefined/-1 | `rich_editor_base_controller.cpp:32-39` |
| AC-4.9 | R-30 | TASK-01 | 单测：闪烁时返回 RectResult | `rich_editor_pattern.cpp:14218-14225` |
| AC-4.10 | R-31 | TASK-01 | 单测：未闪烁返回 undefined | `rich_editor_pattern.cpp:14220`, `js_richeditor.cpp:1586` |
| AC-4.11 | R-29 | TASK-01 | 单测：未绑定返回 undefined | `js_richeditor.cpp:1581-1585` |
| AC-4.12 | R-32 | TASK-01 | 单测：C-API null 返回 PARAM_INVALID | `rich_editor_native_impl.cpp:173-180` |
| AC-4.13 | R-33 | TASK-01 | 单测：C-API GetCaretRect 未闪烁返回 -1 矩形 | `rich_editor_native_impl.cpp:241-249` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | TextInput/TextArea 设置合法 caretColor | CursorColor PaintProperty 写入，CaretColorFlagByUser=true，PROPERTY_UPDATE_RENDER，绘制时光标与句柄颜色同步 | 颜色范围：合法 ResourceColor | AC-1.1 |
| R-2 | 行为 | Text 设置合法 caretColor | CursorColor LayoutProperty 写入，PROPERTY_UPDATE_MEASURE_SELF，绘制时选择浮层 GetHandleColor 派发 | 同上 | AC-1.3 |
| R-3 | 异常 | TextInput/TextArea caretColor(undefined) 或解析失败 | ResetCaretColor：CursorColor 重置，CaretColorFlagByUser=false，回退主题 token `colors->Brand()` | undefined 是唯一 reset 触发 | AC-1.4 |
| R-4 | 异常 | Text caretColor(undefined) 或解析失败 | fallback `theme->GetCaretColor()`（硬编码 #006CDE），**写入** CursorColor（非 reset） | Text 无 CaretColorFlagByUser 机制 | AC-1.6 |
| R-5 | 行为 | TextInput/TextArea 绘制阶段 | PaintCursor 使用 `cursorColor_->Get().ToColor()` 绘制光标线（RSPen + ROUND_CAP）；句柄颜色 `paintProperty->GetCursorColorValue(theme->GetCursorColor())` | 颜色在 OverlayModifier 缓存 | AC-1.1 |
| R-6 | 行为 | RichEditor 设置合法 caretColor | caretColor_ 赋值，selectOverlay_->UpdateHandleColor() 同步调用，绘制时 PaintCaret 使用 caretColor_->Get() | 无 dirty flag | AC-1.2 |
| R-7 | 恢复 | 主题/色盲模式变更 + CaretColorFlagByUser=false | 重新应用 textFieldTheme->GetCursorColor() 到 CursorColor PaintProperty，PROPERTY_UPDATE_RENDER | 仅 TextField 有此机制；Text/RichEditor 无 | AC-1.7 |
| R-8 | 边界 | 先 caretColor(A) 后 caretStyle({color:B}) | CursorColor 最终为 B（last-write-wins，无优先级） | caretStyle.color 与 caretColor 写同一字段 | AC-1.8, AC-2.2 |
| R-9 | 行为 | TextInput/TextArea 设置 caretStyle({width:w}) 合法正数 | CursorWidth PaintProperty 写入，PROPERTY_UPDATE_RENDER | width 单位 vp | AC-2.1 |
| R-10 | 异常 | caretStyle({width}) 缺失/解析失败/负值 | width fallback theme->GetCursorWidth()（默认 2vp），不早退 | 负值不抛异常 | AC-2.3 |
| R-11 | 异常 | caretStyle 对象无 color 字段 | 不触及 CursorColor，光标颜色保持原值 | HasProperty("color") 检查 | AC-2.4 |
| R-12 | 边界 | RichEditor 调用 caretStyle | 无此 API；GetCaretWidth 返回常量 CARET_WIDTH=2vp | RichEditor caretWidth 不可配置 | AC-2.5 |
| R-13 | 边界 | C-API NODE_TEXT_INPUT_CARET_STYLE 设置 | 仅设置 CursorWidth（width），不设置 color | C-API 与 ArkTS 不对称 | AC-2.6 |
| R-14 | 边界 | C-API 设置 TextArea caretStyle | 无对应枚举 NODE_TEXT_AREA_CARET_STYLE；SetTextAreaCaretStyle 实现存在但未接入派发表 | TextArea caretStyle 仅 ArkTS 可用 | AC-2.7 |
| R-15 | 行为 | TextInput caretPosition 合法值 [0, textLength] | MoveCaretToContentRect 执行 std::clamp(value, 0, length)，UpdateCaretInfoToController，MarkDirtyNode(RENDER) | UTF-16 码元索引 | AC-3.1 |
| R-16 | 边界 | caretPosition > textLength | 钳位到 textLength，光标移动到末尾（移动生效） | 与 RichEditor setCaretOffset 不对称 | AC-3.2 |
| R-17 | 异常 | caretPosition < 0 | API>=12：钳为 0；API<12：早退 no-op | VERSION_TWELVE 分支在 JS 桥接 | AC-3.3, AC-3.4 |
| R-18 | 异常 | 静态 caretPosition(undefined) | 解析为 0，光标移动到文本开头 | 静态 API 独有 | AC-3.5 |
| R-19 | 行为 | caretPosition 时 HasFocus()=true | StartTwinkling 启动闪烁；守卫：isTransparent_/!HasFocus()/focusIndex_==CANCEL/UNIT/autoFillStatus!=INIT 时早退 | 闪烁由 ScheduledTask 驱动 | AC-3.6, AC-4.5 |
| R-20 | 边界 | caretPosition 时未聚焦 | 不调用 RequestFocus/RequestKeyboard，内部位置更新但不闪烁，不拉起 IME | 仅移动视觉光标 | AC-3.7 |
| R-21 | 行为 | caretPosition 调用 | CloseSelectOverlay + CancelDelayProcessOverlay + TriggerAvoidOnCaretChange 执行 | 关闭已有选择浮层 | AC-3.8 |
| R-22 | 边界 | caretPosition 属性存储 | 不存储为 Layout/Paint Property；一次性调用 pattern->SetCaretPosition；属性重建不重新应用 | 与可存储属性行为不同 | AC-3.9 |
| R-23 | 行为 | RichEditor setCaretOffset 合法 [0, textContentLength] | caretPosition_ 更新，FireOnSelectionChange 触发，caretChangeListener_ 回调，返回 true | UTF-16 码元索引 | AC-4.1 |
| R-24 | 边界 | RichEditor setCaretOffset 超范围（>length 或 <0） | std::clamp 计算 correctPos，pos != correctPos 返回 false，caretPosition_ 不更新 | 与 TextInput caretPosition 钳位移动不对称 | AC-4.2, AC-4.3 |
| R-25 | 异常 | RichEditor setCaretOffset 时 IsPreviewTextInputting()=true | 直接返回 false，不移动光标 | 预览文本态守卫 | AC-4.4 |
| R-26 | 行为 | setCaretOffset 后 | CloseSelectOverlay + ResetSelection + ForceTriggerAvoidOnCaretChange(true) 执行 | 与 TextInput 一致 | AC-4.5 |
| R-27 | 边界 | setCaretOffset 时未聚焦 | caretPosition_ 仍更新（若合法），StartTwinkling 因 !IsCurrentFocus 不执行；后续聚焦光标在预置位置 | 允许预置位置 | AC-4.6 |
| R-28 | 行为 | getCaretOffset 已绑定 Pattern | 返回 caretPosition_（int），非聚焦仍返回存储值 | 静态返回 int\|undefined，动态返回 number(-1 哨兵) | AC-4.7 |
| R-29 | 异常 | getCaretOffset/getCaretRect 控制器未绑定 Pattern | 静态返回 undefined；动态 getCaretOffset 返回 -1；getCaretRect 返回 undefined | 弱引用升级失败 | AC-4.8, AC-4.11 |
| R-30 | 行为 | getCaretRect 时光标闪烁（caretTwinkling_=true） | 返回 RectResult{x,y,width,height}，相对 RichEditor 组件坐标系，width=2vp | caretWidth 固定 | AC-4.9 |
| R-31 | 边界 | getCaretRect 时光标未闪烁（caretTwinkling_=false） | GetCaretRelativeRect 返回 RectF(-1,-1,-1,-1)，JS 桥接 IsValid()=false 转 undefined | 未聚焦即未闪烁 | AC-4.10 |
| R-32 | 边界 | C-API SetCaretOffset controller/node null | 返回 ARKUI_ERROR_CODE_PARAM_INVALID；否则返回 NO_ERROR（不传播 boolean） | C-API 错误码语义 | AC-4.12 |
| R-33 | 边界 | C-API GetCaretRect 光标未闪烁 | Pattern 返回 RectF(-1,-1,-1,-1) 原样拷贝到 out ArkUI_Rect；C-API 无 undefined 路径，调用方需检查负值 | C-API 与 ArkTS 不对称 | AC-4.13 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, AC-1.3 | 单测（Pattern 层） | caretColor 写入 PaintProperty/LayoutProperty/成员变量；绘制颜色断言 |
| VM-2 | AC-1.4, AC-1.5, AC-1.6 | 单测（JS 桥接 + Model 层） | undefined 触发 reset/fallback 分支；flag 清零 |
| VM-3 | AC-1.7 | 单测（Pattern 层） | 主题变更 + flag=false 重新应用 |
| VM-4 | AC-1.8, AC-2.1, AC-2.2 | 单测（JS 桥接） | caretStyle.color 与 caretColor last-write-wins |
| VM-5 | AC-2.3, AC-2.4 | 单测（JS 桥接） | width fallback 2vp；无 color 不触及 |
| VM-6 | AC-2.5, AC-2.6, AC-2.7 | 单测 + C-API 测试 | RichEditor 无 caretStyle；C-API 仅 width；TextArea 无 C-API |
| VM-7 | AC-3.1, AC-3.2 | 单测（Pattern + SelectController） | clamp 逻辑与移动生效 |
| VM-8 | AC-3.3, AC-3.4, AC-3.5 | 单测（JS 桥接，API 版本分支） | VERSION_TWELVE 负值处理差异 |
| VM-9 | AC-3.6, AC-3.7, AC-3.8 | 单测（Pattern 层） | HasFocus 分支；CloseSelectOverlay 副作用 |
| VM-10 | AC-3.9 | 单测（Model 层） | 属性不存储，重建不重新应用 |
| VM-11 | AC-4.1, AC-4.2, AC-4.3 | 单测（RichEditorPattern） | setCaretOffset 成功/失败语义 |
| VM-12 | AC-4.4 | 单测（RichEditorPattern） | 预览文本态守卫 |
| VM-13 | AC-4.5, AC-4.6 | 单测（RichEditorPattern + FocusHub） | IsCurrentFocus 分支闪烁 |
| VM-14 | AC-4.7, AC-4.8 | 单测（Controller 层） | 已绑定/未绑定返回值差异 |
| VM-15 | AC-4.9, AC-4.10, AC-4.11 | 单测（Controller + Pattern） | caretTwinkling_ 状态决定返回 |
| VM-16 | AC-4.12, AC-4.13 | C-API 测试 | null 返回 PARAM_INVALID；未闪烁返回 -1 矩形 |

## API 变更分析

### 新增 API

> 本特性为已有能力补录，无新增 API。下表为 Feat-01 涉及的存量公共 API 清单（按 SDK 静态声明为准，C-API 同步列出）。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|--------|
| `Text.caretColor(color)` | Public | color: ResourceColor \| undefined | this | N/A | 设置 Text 选择句柄颜色 | AC-1.3, AC-1.6 |
| `TextInput.caretColor(value)` | Public | value: ResourceColor \| undefined | this | N/A | 设置 TextInput 光标与句柄颜色 | AC-1.1, AC-1.4, AC-1.8 |
| `TextArea.caretColor(value)` | Public | value: ResourceColor \| undefined | this | N/A | 设置 TextArea 光标与句柄颜色 | AC-1.1, AC-1.4 |
| `RichEditor.caretColor(value)` | Public | value: ResourceColor \| undefined | this | N/A | 设置 RichEditor 光标与句柄颜色 | AC-1.2, AC-1.5 |
| `TextInput.caretStyle(value)` | Public | value: CaretStyle \| undefined | this | N/A | 设置 TextInput 光标宽度与颜色 | AC-2.1~AC-2.4, AC-2.6 |
| `TextArea.caretStyle(value)` | Public | value: CaretStyle \| undefined | this | N/A | 设置 TextArea 光标宽度与颜色 | AC-2.1~AC-2.4, AC-2.7 |
| `TextInput.caretPosition(value)` 属性 | Public | value: int \| undefined | this | N/A | 设置 TextInput 光标位置（一次性） | AC-3.1~AC-3.9 |
| `TextInputController.caretPosition(value)` | Public | value: int | void | N/A | 设置 TextInput 光标位置（控制器方法） | AC-3.1~AC-3.8 |
| `TextEditControllerEx.setCaretOffset(offset)` | Public | offset: int | boolean \| undefined | N/A | 设置 RichEditor 光标偏移 | AC-4.1~AC-4.6 |
| `TextEditControllerEx.getCaretOffset()` | Public | 无 | int \| undefined | N/A | 读取 RichEditor 光标偏移 | AC-4.7, AC-4.8 |
| `RichEditorBaseController.getCaretRect()` | Public | 无 | RectResult \| undefined | N/A | 读取 RichEditor 光标矩形 | AC-4.9~AC-4.11 |
| C-API `NODE_TEXT_INPUT_CARET_COLOR` | Public (NDK) | .value[0].u32 (0xARGB) | void | N/A | 设置 TextInput 光标颜色 | AC-1.1 |
| C-API `NODE_TEXT_INPUT_CARET_STYLE` | Public (NDK) | .value[0].f32 (vp) | void | N/A | 设置 TextInput 光标宽度（仅 width） | AC-2.6 |
| C-API `NODE_TEXT_AREA_CARET_COLOR` | Public (NDK) | .value[0].u32 (0xARGB) | void | N/A | 设置 TextArea 光标颜色 | AC-1.1 |
| C-API `NODE_TEXT_EDITOR_CARET_COLOR` (@since 24) | Public (NDK) | .value[0].u32 (0xARGB) | void | N/A | 设置 RichEditor 光标颜色 | AC-1.2 |
| C-API `NODE_TEXT_INPUT_CARET_OFFSET` | Public (NDK) | set: .value[0].i32；get: 返回 i32+f32+f32 | void / ArkUI_AttributeItem | N/A | 设置/读取 TextInput 光标偏移与坐标 | AC-3.1, AC-4.7 |
| C-API `OH_ArkUI_TextEditorStyledStringController_SetCaretOffset` (@since 24) | Public (NDK) | controller, offset(int) | ArkUI_ErrorCode | PARAM_INVALID / NO_ERROR | 设置 RichEditor 光标偏移 | AC-4.12 |
| C-API `OH_ArkUI_TextEditorStyledStringController_GetCaretOffset` (@since 24) | Public (NDK) | controller, *offset(int*) | ArkUI_ErrorCode | PARAM_INVALID / NO_ERROR | 读取 RichEditor 光标偏移 | AC-4.7 |
| C-API `OH_ArkUI_TextEditorStyledStringController_GetCaretRect` (@since 24) | Public (NDK) | controller, *rect(ArkUI_Rect*) | ArkUI_ErrorCode | PARAM_INVALID / NO_ERROR | 读取 RichEditor 光标矩形 | AC-4.13 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|--------|
| `TextInput.caretColor` (dynamic @since 7) | 变更 | 静态 API @since 23 接受 undefined 重置 | 动态 API 仅接受 ResourceColor；静态增加 undefined reset 能力 | AC-1.4 |
| `Text.caretColor` (dynamic @since 14) | 变更 | 静态 API @since 23 | 动态描述为"selection handle color"，静态描述为"caret color for selected text" | AC-1.3, AC-1.6 |
| `RichEditor.caretColor` (dynamic @since 12) | 变更 | 静态 API @since 23 | 动态描述含"caret and selection handle"，静态描述"caret color" | AC-1.2 |
| `TextInput.caretStyle` (dynamic @since 10) | 变更 | 静态 API @since 23 | 静态 CaretStyle 字段无默认值标注；动态 width 默认 2vp、color 默认 #ff007dff | AC-2.1, AC-2.3 |
| `TextArea.caretStyle` (dynamic @since 12) | 变更 | 静态 API @since 23 | 同上 | AC-2.1, AC-2.3 |
| `TextInput.caretPosition` 属性 (dynamic @since 10) | 变更 | 静态 API @since 23 接受 undefined | 静态 undefined → 0；动态仅接受 number | AC-3.5 |
| `TextInputController.caretPosition` (dynamic @since 8) | 变更 | 静态 API @since 23 | 行为一致 | AC-3.1 |
| `getCaretOffset` (dynamic @since 10, returns number) | 变更 | 静态 API @since 23 返回 int\|undefined | 下游需适配 -1 哨兵 → undefined 的类型迁移 | AC-4.7, AC-4.8 |
| `getCaretRect` (dynamic @since 18) | 变更 | 静态 API @since 23 | 行为一致，仅版本号差异 | AC-4.9, AC-4.10 |
| `setCaretOffset` (dynamic @since 10, returns boolean) | 变更 | 静态 API @since 23 返回 boolean\|undefined | 静态返回类型增加 undefined 路径 | AC-4.1, AC-4.2 |

## 接口规格

### 接口定义

**TextInput.caretColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextInputAttribute::caretColor(value: ResourceColor \| undefined): this` |
| 返回值 | `this` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.4, AC-1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor \| undefined | 否 | 主题 token `colors->Brand()` | undefined 触发 ResetCaretColor；非法颜色解析失败等同 undefined |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 ResourceColor | CursorColor 写入，CaretColorFlagByUser=true，RENDER 脏标记，绘制光标与句柄颜色同步 | AC-1.1 |
| 2 | undefined 或解析失败 | ResetCaretColor：CursorColor 重置，flag 清零，回退主题默认 | AC-1.4 |
| 3 | 主题变更 + flag=false | 重新应用 textFieldTheme->GetCursorColor() | AC-1.7 |

**TextInput.caretStyle**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextInputAttribute::caretStyle(value: CaretStyle \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.4, AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.width | Length \| undefined | 否 | 2vp | 缺失/负值/解析失败 → fallback 2vp |
| value.color | ResourceColor \| undefined | 否 | 不触及 | 缺失（无 color 字段）→ 不触及 CursorColor；解析失败 → fallback theme cursor color |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | {width: 正数} | CursorWidth 写入，RENDER 脏标记 | AC-2.1 |
| 2 | {color: 合法} | 等同 caretColor(color)，CursorColor 写入 | AC-2.2 |
| 3 | {width: 负值/缺失} | fallback 2vp | AC-2.3 |
| 4 | 无 color 字段 | 不触及 CursorColor | AC-2.4 |
| 5 | C-API NODE_TEXT_INPUT_CARET_STYLE | 仅设 width，不设 color | AC-2.6 |

**TextInputController.caretPosition**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextInputController::caretPosition(value: int): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | int | 是 | N/A | [0, textLength] 合法；负值 API>=12 钳为 0，API<12 早退；>textLength 钳位到末尾；UTF-16 码元索引 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 0 ≤ value ≤ textLength | 光标移动到 value，UpdateCaretInfoToController，MarkDirtyNode(RENDER) | AC-3.1 |
| 2 | value > textLength | 钳位到 textLength，移动到末尾 | AC-3.2 |
| 3 | value < 0, API>=12 | 钳为 0，移动到开头 | AC-3.3 |
| 4 | value < 0, API<12 | 早退 no-op | AC-3.4 |
| 5 | 已聚焦 | StartTwinkling 启动闪烁 | AC-3.6 |
| 6 | 未聚焦 | 不 RequestFocus/IME，仅更新内部位置 | AC-3.7 |
| 7 | 调用 | CloseSelectOverlay + TriggerAvoidOnCaretChange | AC-3.8 |

**RichEditorBaseController.setCaretOffset**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RichEditorBaseController::setCaretOffset(offset: int): boolean \| undefined` |
| 返回值 | `boolean \| undefined` — true 成功；false 失败（超范围/预览态）；undefined 未绑定 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| offset | int | 是 | N/A | [0, textContentLength] 合法返回 true；负值 JS 归一化为 -1 触发 false；超范围返回 false 不更新；预览文本态返回 false |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 0 ≤ offset ≤ textContentLength | caretPosition_ 更新，FireOnSelectionChange，返回 true | AC-4.1 |
| 2 | offset > textContentLength | correctPos=textContentLength, pos!=correctPos 返回 false, 不更新 | AC-4.2 |
| 3 | offset < 0 | JS 归一化 -1, 返回 false, 不更新 | AC-4.3 |
| 4 | IsPreviewTextInputting()=true | 返回 false, 不移动 | AC-4.4 |
| 5 | 已聚焦 | StartTwinkling + CloseSelectOverlay + ResetSelection | AC-4.5 |
| 6 | 未聚焦 | caretPosition_ 更新但不闪烁 | AC-4.6 |

**RichEditorBaseController.getCaretRect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RichEditorBaseController::getCaretRect(): RectResult \| undefined` |
| 返回值 | `RectResult \| undefined` — 闪烁时返回矩形；未闪烁/未绑定返回 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.9~AC-4.11 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | caretTwinkling_=true | 返回 RectResult{x,y,width=2vp,height}，相对 RichEditor 组件坐标系 | AC-4.9 |
| 2 | caretTwinkling_=false | RectF(-1,-1,-1,-1) → JS 转 undefined | AC-4.10 |
| 3 | 控制器未绑定 | undefined | AC-4.11 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - `caretPosition` 负值处理在 API 12 变更：API<12 早退 no-op；API>=12 钳为 0（`js_textfield.cpp:586-596`）。
  - 动态/静态返回类型分歧：`getCaretOffset` 动态返回 number(-1)，静态返回 int\|undefined；`setCaretOffset` 动态返回 boolean，静态返回 boolean\|undefined（`rich_editor.d.ts:2341/2355` vs `richEditor.static.d.ets:1645/1655`）。
  - `caretColor` 静态 API 新增 undefined reset 能力（动态仅接受 ResourceColor）。
  - Text caretColor fallback `#006CDE` 与 SDK 文档 `#007DFF` 不一致（`text_theme.cpp:35`）。
  - C-API `NODE_TEXT_INPUT_CARET_STYLE` 仅设 width 不设 color，与 ArkTS `caretStyle({width,color})` 不对称（`style_modifier.cpp:5438-5450`）。
  - TextArea caretStyle 无对应 C-API（`SetTextAreaCaretStyle` 实现存在但未接入派发表）。
  - C-API `NODE_TEXT_AREA_CARET_COLOR` 文档注释误写为 "background color"（`native_node.h:4510`）。
  - RichEditor 无 caretStyle API（caretWidth 固定 2vp 常量）。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（TextInput caretColor 动态）、API 8（TextInputController.caretPosition 动态）、API 10（TextInput caretStyle 动态 + caretPosition 属性动态）、API 11（Text caretColor 动态）、API 12（RichEditor caretColor 动态 + TextArea caretStyle 动态）、API 18（getCaretRect 动态）、API 22（enableSelectedDataDetector，非本 Feat）、API 23（全部静态 API 基线）、API 24（NODE_TEXT_EDITOR_CARET_COLOR + OH_ArkUI_TextEditorStyledStringController_* C-API）
- **API 版本号策略:** 静态 API 统一标注 `@since 23 static`；动态 API 按实际引入版本标注 `@since N dynamic`；C-API 按实际引入版本标注 `@since N`。版本差异在 AC 与规则中显式区分。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 存储层分裂 | caretColor 在 Text=LayoutProperty(MEASURE_SELF)、TextField=PaintProperty(RENDER)、RichEditor=Pattern 成员(无 dirty flag) 三层存储，不可跨层混用 | AC-1.1~AC-1.6 |
| C-API 不对称 | C-API caretStyle 仅 TextInput 暴露且仅 width；TextArea/RichEditor caretStyle 无 C-API | AC-2.6, AC-2.7 |
| UTF-16 码元索引 | caretPosition/setCaretOffset 使用 UTF-16 码元索引而非字形索引；代理对（emoji）计为 2 单位 | AC-3.1, AC-4.1 |
| 光标位置一次性 | caretPosition 属性不存储为 Property，一次性调用 Pattern；属性重建不重新应用 | AC-3.9 |
| 闪烁依赖聚焦 | StartTwinkling 守卫 HasFocus/IsCurrentFocus；未聚焦时光标位置可更新但不闪烁 | AC-3.6, AC-3.7, AC-4.5, AC-4.6 |
| getCaretRect 依赖闪烁 | caretTwinkling_=false 时返回 undefined；C-API 返回 RectF(-1,-1,-1,-1) | AC-4.9~AC-4.13 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | caretColor 变更触发脏标记后单帧重测/重绘 < 16ms（60fps） | 帧率测试 | PROPERTY_UPDATE_MEASURE_SELF/RENDER 脏节点仅重测脏子树 |
| 性能 | caretPosition/caretOffset 调用为同步操作，无异步等待 | 单测时序断言 | `text_field_pattern.cpp:8263` 同步调用链 |
| 内存 | RichEditor caretColor_ 为 std::optional<Color>，无额外堆分配 | 静态分析 | `rich_editor_pattern.h:1377` |
| 可靠性 | caretPosition 属性重建不重新应用（一次性），应用需在重建后重新调用 | 文档+单测 | `text_field_model_ng.cpp:467-473` |
| 可测试性 | 所有 API 通过 Pattern/Controller 层单测可验证，无需 UI 渲染 | 单测覆盖 | VM-1~VM-16 |
| 自动化维测 | C-API 错误码可机器解析；getCaretOffset -1 哨兵可自动化检测 | C-API 测试 | `rich_editor_native_impl.cpp:173-180` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | caretColor/caretStyle/caretPosition 跨设备行为一致 | 同单测 | N/A |
| 平板 | 无差异 | 同上 | 同单测 | N/A |
| 折叠屏 | 无差异 | 同上；caretPosition 索引基于 UTF-16 不受折叠影响 | 同单测 | N/A |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | caretColor 不影响无障碍语义；光标位置变化通过 onTextSelectionChange 通知（非本 Feat） | N/A |
| 大字体 | 是 | caretPosition/caretOffset 使用 UTF-16 码元索引不受字体缩放影响；caretRect 坐标随字体缩放变化 | getCaretRect 在大字体下矩形尺寸增大 |
| 深色模式 | 是 | TextField CaretColorFlagByUser=false 时主题变更重新应用 cursor color；Text/RichEditor 无此机制，深色模式下 fallback 颜色不变 | AC-1.7 |
| 多窗口/分屏 | 否 | caretPosition 内部状态不跨窗口共享 | N/A |
| 多用户 | 否 | 光标状态不跨用户共享 | N/A |
| 版本升级 | 是 | API 12 负值行为变更；静态 API @since 23 返回类型差异需迁移 | 兼容性声明 |
| 生态兼容 | 是 | C-API caretStyle 不对称、TextArea/RichEditor caretStyle 缺 C-API；下游 NDK 应用需适配 | 兼容性声明 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "caretColor 在 Text/TextField/RichEditor 三层存储的脏标记差异（MEASURE_SELF/RENDER/无 dirty flag）如何影响脏节点重测范围"
  - repo: "openharmony/arkui_ace_engine"
    query: "C-API NODE_TEXT_INPUT_CARET_STYLE 为何仅设 width 不设 color，与 ArkTS caretStyle({width,color}) 的不对称是否为历史遗留"
  - repo: "openharmony/arkui_ace_engine"
    query: "RichEditor setCaretOffset 超范围返回 false 不移动 vs TextInput caretPosition 超范围钳位移动，行为不对称的语义依据"
  - repo: "openharmony/arkui_ace_engine"
    query: "getCaretRect 在 caretTwinkling_=false 时返回 undefined 的设计动机，以及 C-API 返回 RectF(-1,-1,-1,-1) 的下游处理约定"
  - repo: "openharmony/interface_sdk-js"
    query: "动态 getCaretOffset 返回 number(-1) vs 静态返回 int|undefined 的类型迁移策略"
```

**关键文档：**
- SDK 静态声明: `interface/sdk-js/api/arkui/component/text.static.d.ets` / `textInput.static.d.ets` / `textArea.static.d.ets` / `richEditor.static.d.ets` / `textCommon.static.d.ets`
- SDK 动态声明: `interface/sdk-js/api/@internal/component/ets/text.d.ts` / `text_input.d.ts` / `text_area.d.ts` / `rich_editor.d.ts` / `text_common.d.ts`
- C-API 声明: `interfaces/native/native_node.h` / `interfaces/native/native_type.h`
- 知识库: `docs/pattern/text/Text_Knowledge_Base_CN.md` / `docs/pattern/text_input/TextInput_Knowledge_Base_CN.md` / `docs/pattern/rich_editor/RichEditor_Knowledge_Base_CN.md`
