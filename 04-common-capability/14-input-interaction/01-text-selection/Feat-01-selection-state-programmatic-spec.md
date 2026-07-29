# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 选区状态模型与编程式选区 |
| 特性编号 | Func-04-14-01-Feat-01 |
| 所属 Epic | 04-通用能力层 / 14-输入交互 / 01-文本选择 |
| 优先级 | P1 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | TextSelector 选区状态结构规格化 | 方向无关 baseOffset/destinationOffset 模型，含 handle rects、AI 选区、高亮区间 |
| ADDED | selection 属性规格化（Text @since 11） | 声明式选区设置 |
| ADDED | setTextSelection 控制器方法规格化 | TextController @23 / TextInput @10 / TextArea @10 / Search @12 / RichEditor @11 |
| ADDED | textSelectable + TextSelectableMode 规格化（@since 12） | 可选择模式控制 |
| ADDED | copyOption/copyOptions 选区权限规格化 | None/InApp/LocalDevice/CrossDevice |
| ADDED | getSelection 查询规格化 | RichEditorController @11 / TextContentControllerBase @15 |
| ADDED | SelectionOptions + MenuPolicy 规格化（@since 12） | 选区菜单策略 |
| ADDED | 无障碍驱动选区规格化 | ACTION_SET_SELECTION / ACTION_CLEAR_SELECTION / GetTextSelectionStart/End |
| ADDED | C-API 选区属性规格化 | NODE_TEXT_TEXT_SELECTION @23 / NODE_TEXT_INPUT_TEXT_SELECTION / NODE_TEXT_AREA_TEXT_SELECTION / ArkUI_SelectionOptions @23 |

## 输入文档

| 类型 | 路径 |
|------|------|
| 设计文档 | `04-common-capability/14-input-interaction/01-text-selection/design.md` |
| SDK 动态 API | `interface/sdk-js/api/@internal/component/ets/text.d.ts`、`text_input.d.ts`、`text_area.d.ts`、`search.d.ts`、`rich_editor.d.ts`、`common.d.ts`、`enums.d.ts`、`text_common.d.ts` |
| SDK 静态 API | `interface/sdk-js/api/arkui/component/text.static.d.ets`、`textInput.static.d.ets`、`textArea.static.d.ets` |
| C-API 头文件 | `interfaces/native/native_node.h`、`interfaces/native/native_type.h`、`interfaces/native/node/node_extened.h` |

> 需求基线、不涉及项详见 design.md，本文档不重复摘录。design.md 与本文档并行产出。

## 用户故事

### US-1: 声明式选区设置

作为应用开发者，我想要通过 `selection(start, end)` 属性在 Text 组件创建时预设高亮选区，以便在首次渲染时即向用户展示选中文本。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN Text 设置 `selection(start, end)` 且 `0 <= start < end <= textLength` 且 `textSelectableMode != UNSELECTABLE` 且 `copyOption != None` 且 `textOverflow != MARQUEE` 且无 textEffect THEN 选区高亮显示 `[start, end)` 范围文本且触发 `onTextSelectionChange(start, end)` | 正常 |
| AC-1.2 | WHEN Text 设置 `selection(start, end)` 且 `start >= end` THEN JS 桥接层 `JSText::SetTextSelection` 仍调用 `TextModel::SetTextSelection`，Pattern 层不设置有效选区（`TextSelector::IsValid()` 返回 false） | 边界 |
| AC-1.3 | WHEN Text 设置 `selection` 且 `textSelectableMode == UNSELECTABLE` THEN `TextPattern::SetTextSelection` 静默返回，不设置选区 | 异常 |
| AC-1.4 | WHEN Text 设置 `selection` 且 `copyOption == CopyOptions::None` THEN `TextPattern::SetTextSelection` 静默返回，不设置选区 | 异常 |
| AC-1.5 | WHEN Text 设置 `selection` 且 `textOverflow == TextOverflow::MARQUEE` THEN `TextPattern::SetTextSelection` 静默返回，不设置选区 | 异常 |
| AC-1.6 | WHEN Text 设置 `selection` 且组件存在 textEffect_ THEN `TextPattern::SetTextSelection` 静默返回，不设置选区 | 异常 |

### US-2: 编程式选区设置（控制器方法）

作为应用开发者，我想要通过控制器 `setTextSelection` / `setSelection` 方法在运行时动态选中文本，以便根据业务逻辑控制选区。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `TextInputController.setTextSelection(start, end)` 且 `start <= end` THEN 选区设置为 `[start, end)`，`start`/`end` 自动 clamp 到 `[0, textLength]` | 正常 |
| AC-2.2 | WHEN `TextInputController.setTextSelection(start, end)` 且 `start > end` THEN `TextFieldController::SetTextSelection` 静默返回，选区不变 | 边界 |
| AC-2.3 | WHEN `TextAreaController.setTextSelection(start, end)` THEN 行为与 AC-2.1/AC-2.2 一致 | 正常 |
| AC-2.4 | WHEN `SearchController.setTextSelection(start, end)` THEN 行为与 AC-2.1/AC-2.2 一致，选区限制在搜索文本宽度内 | 正常 |
| AC-2.5 | WHEN `RichEditorBaseController.setSelection(start, end)` 且组件已获焦 THEN 选区设置并触发 `onSelectionChange` | 正常 |
| AC-2.6 | WHEN `RichEditorBaseController.setSelection(start, end)` 且组件未获焦 THEN 选区不设置 | 异常 |
| AC-2.7 | WHEN `TextController.setTextSelection(start, end, options)` 且 `options.menuPolicy == MenuPolicy::SHOW` THEN 选区设置且选择菜单强制显示 | 正常 |
| AC-2.8 | WHEN `TextController.setTextSelection(start, end, options)` 且 `options.menuPolicy == MenuPolicy::HIDE` THEN 选区设置但选择菜单隐藏（手柄仍绘制） | 正常 |
| AC-2.9 | WHEN `TextInputController.setTextSelection(start, end)` 未传 `options`（`nullopt`）THEN 选区设置但选择菜单不显示 | 边界 |
| AC-2.10 | WHEN `TextInputController.setTextSelection(start, end, options)` 且 `options.menuPolicy == MenuPolicy::DEFAULT` THEN 选区设置，菜单可见性保留当前状态 | 正常 |
| AC-2.11 | WHEN `TextFieldController::SetTextSelection` 被调用 THEN 选区设置延迟到布局完成后执行（`ScheduleTaskWithLayoutDeferral`） | 边界 |

### US-3: 可选择模式控制

作为应用开发者，我想要通过 `textSelectable(mode)` 控制 Text 组件的可选择行为，以便按需启用或禁用文本选择。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN Text 设置 `textSelectable(TextSelectableMode.SELECTABLE_UNFOCUSABLE)` THEN 文本可通过长按/鼠标选择，但组件不可获焦（`focusHub->SetFocusable(false)`） | 正常 |
| AC-3.2 | WHEN Text 设置 `textSelectable(TextSelectableMode.SELECTABLE_FOCUSABLE)` THEN 文本可选择且组件可获焦（`focusHub->SetFocusable(true)`, `SetIsFocusOnTouch(true)`） | 正常 |
| AC-3.3 | WHEN Text 设置 `textSelectable(TextSelectableMode.UNSELECTABLE)` THEN 文本不可选择，`IsSelectableAndCopy()` 返回 false | 正常 |
| AC-3.4 | WHEN Text 未设置 `textSelectable` THEN 默认值为 `SELECTABLE_UNFOCUSABLE` | 边界 |

### US-4: 选区复制权限

作为应用开发者，我想要通过 `copyOption` / `copyOptions` 控制选区复制权限范围，以便限制复制能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN Text 设置 `copyOption(CopyOptions.None)` THEN 选区完全禁用（含编程式 `selection`/`setTextSelection` 静默返回），无障碍 `ACTION_SET_SELECTION` 不可用 | 正常 |
| AC-4.2 | WHEN Text 设置 `copyOption(CopyOptions.InApp)` THEN 选区允许，复制仅限应用内 | 正常 |
| AC-4.3 | WHEN Text 未设置 `copyOption` THEN `copyOption_` 默认为 `CopyOptions::None`（选区默认禁用） | 边界 |
| AC-4.4 | WHEN TextInput/TextArea 未设置 `copyOption` THEN 默认为 `CopyOptions::Local`（选区+复制默认启用） | 边界 |
| AC-4.5 | WHEN TextInput 设置 `copyOption(CopyOptions.None)` THEN 选区仍然可用（copyOption 不门控 TextField 选区） | 边界 |
| AC-4.6 | WHEN RichEditor 设置 `copyOptions(CopyOptions.None)` THEN 选区仍可用，但 copy/cut 命令禁用 | 边界 |
| AC-4.7 | WHEN RichEditor 未设置 `copyOptions` THEN 默认为 `CopyOptions::Local` | 边界 |

### US-5: 选区查询

作为应用开发者，我想要通过 `getSelection()` 查询当前选区范围，以便获取用户选择状态。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 `RichEditorController.getSelection()` 且存在选区 THEN 返回 `RichEditorSelection { selection: [start, end], spans: [...] }` | 正常 |
| AC-5.2 | WHEN 调用 `TextContentControllerBase.getSelection()` 且存在选区 THEN 返回 `TextRange { start, end }`（@since 15） | 正常 |
| AC-5.3 | WHEN 无选区时调用 `getSelection()` THEN 返回 `{ start: 0, end: 0 }` 或等价空选区 | 边界 |

### US-6: 无障碍驱动选区

作为无障碍辅助工具，我想要通过 `ACTION_SET_SELECTION` / `ACTION_CLEAR_SELECTION` 驱动文本选区，以便支持屏幕阅读器选区操作。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 无障碍服务调用 `ACTION_SET_SELECTION(start, end, isForward)` on Text 且 `copyOption != None` 且 `textSelectableMode != UNSELECTABLE` THEN 选区设置 | 正常 |
| AC-6.2 | WHEN 无障碍服务调用 `ACTION_SET_SELECTION` on Text 且 `copyOption == None` THEN 操作不执行 | 异常 |
| AC-6.3 | WHEN 无障碍服务调用 `ACTION_CLEAR_SELECTION` THEN `CloseSelectOverlay(true)` + `ResetSelection()` 执行，选区清除 | 正常 |
| AC-6.4 | WHEN 无障碍服务查询 `GetTextSelectionStart()` / `GetTextSelectionEnd()` THEN 返回 `TextSelector.GetTextStart()` / `GetTextEnd()`（`min(baseOffset, destinationOffset)` / `max(...)`） | 正常 |
| AC-6.5 | WHEN TextField 无障碍查询 `GetTextSelectionStart/End` THEN 返回 `TextSelectController::GetStartIndex()` / `GetEndIndex()`（`min(firstHandle.index, secondHandle.index)` / `max(...)`） | 正常 |

### US-7: C-API (NDK) 选区操作

作为 NDK 开发者，我想要通过 C-API 属性设置/获取选区，以便在 C 代码中操作选区。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-7.1 | WHEN `setAttribute(node, NODE_TEXT_TEXT_SELECTION, {value[0].i32=start, value[1].i32=end, object=ArkUI_SelectionOptions*})` 且 `start < end` THEN Text 选区设置（@since 23） | 正常 |
| AC-7.2 | WHEN `setAttribute(NODE_TEXT_TEXT_SELECTION)` 且 `start >= end` THEN 返回 `ERROR_CODE_PARAM_INVALID` 且调用 `resetTextTextSelection` | 异常 |
| AC-7.3 | WHEN `setAttribute(node, NODE_TEXT_INPUT_TEXT_SELECTION, {value[0].i32=start, value[1].i32=end})` 且 `start <= end` THEN TextInput 选区设置（不传 options，不支持 MenuPolicy） | 正常 |
| AC-7.4 | WHEN `setAttribute(NODE_TEXT_INPUT_TEXT_SELECTION)` 且 `start > end` THEN 返回 `ERROR_CODE_PARAM_INVALID` | 异常 |
| AC-7.5 | WHEN `setAttribute(node, NODE_TEXT_AREA_TEXT_SELECTION, {start, end})` THEN 行为与 AC-7.3/AC-7.4 一致 | 正常 |
| AC-7.6 | WHEN `getAttribute(node, NODE_TEXT_TEXT_SELECTION)` THEN 返回 `{value[0].i32=start, value[1].i32=end, object=new ArkUI_SelectionOptions*}`（堆分配，调用方需 Dispose） | 边界 |
| AC-7.7 | WHEN `OH_ArkUI_SelectionOptions_Create()` THEN 返回 `menuPolicy = ARKUI_MENU_POLICY_DEFAULT` 的选项对象（@since 23） | 正常 |
| AC-7.8 | WHEN `OH_ArkUI_SelectionOptions_SetMenuPolicy(options, ARKUI_MENU_POLICY_SHOW)` THEN 后续 `setAttribute` 使用此 options 时菜单强制显示 | 正常 |
| AC-7.9 | WHEN `OH_ArkUI_TextEditorStyledStringController_SetSelection(controller, start, end, menuPolicy)` THEN RichEditor 选区设置（@since 24） | 正常 |
| AC-7.10 | WHEN `OH_ArkUI_TextEditorStyledStringController_GetSelection(controller, &start, &end)` THEN 返回选区范围 out-params（@since 24） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1, R-3 | TASK-01 | 单元测试 + UI 集成 | text_pattern.cpp:1629 |
| AC-1.2 | R-1, R-16 | TASK-01 | 单元测试 | text_selector.h:168 |
| AC-1.3 | R-3 | TASK-01 | 单元测试 | text_pattern.cpp:1631 |
| AC-1.4 | R-3, R-8 | TASK-01 | 单元测试 | text_pattern.cpp:1634 |
| AC-1.5 | R-3 | TASK-01 | 单元测试 | text_pattern.cpp:1636 |
| AC-1.6 | R-3 | TASK-01 | 单元测试 | text_pattern.cpp:1637 |
| AC-2.1 | R-2, R-14 | TASK-01 | 单元测试 | text_field_controller.cpp:70 |
| AC-2.2 | R-17 | TASK-01 | 单元测试 | text_field_controller.cpp:73 |
| AC-2.5 | R-5, R-6 | TASK-01 | 单元测试 | rich_editor_pattern.cpp:10521 |
| AC-2.6 | R-5 | TASK-01 | 单元测试 | rich_editor_pattern.cpp:10521 |
| AC-2.7 | R-9, R-10 | TASK-01 | 单元测试 | text_pattern.cpp:7443 |
| AC-2.8 | R-11 | TASK-01 | 单元测试 | text_pattern.cpp:7443 |
| AC-2.9 | R-12 | TASK-01 | 单元测试 | text_field_pattern.cpp:8343 |
| AC-2.11 | R-18 | TASK-01 | 单元测试 | text_field_controller.cpp:82 |
| AC-3.1–3.4 | R-4 | TASK-01 | 单元测试 | text_pattern.cpp:3849 |
| AC-4.1 | R-8 | TASK-01 | 单元测试 | text_pattern.cpp:1634 |
| AC-4.3 | R-8 | TASK-01 | 单元测试 | js_text.cpp:1055 |
| AC-4.4 | R-8 | TASK-01 | 单元测试 | js_textfield.cpp:1495 |
| AC-4.5 | R-8 | TASK-01 | 单元测试 | text_field_pattern.cpp（无 gate） |
| AC-4.6 | R-8 | TASK-01 | 单元测试 | rich_editor_pattern.cpp:10521 |
| AC-5.1 | R-13 | TASK-01 | 单元测试 | rich_editor_controller_accessor.cpp:972 |
| AC-5.2 | R-13 | TASK-01 | 单元测试 | text_content_controller_base_accessor.cpp:105 |
| AC-6.1 | R-14, R-3 | TASK-01 | 无障碍测试 | text_pattern.cpp:6422 |
| AC-6.3 | R-15 | TASK-01 | 无障碍测试 | text_pattern.cpp:6437 |
| AC-6.4 | R-19 | TASK-01 | 无障碍测试 | text_accessibility_property.cpp:57 |
| AC-7.1 | R-6, R-20 | TASK-01 | C-API 单元测试 | style_modifier.cpp:14153 |
| AC-7.2 | R-6 | TASK-01 | C-API 单元测试 | style_modifier.cpp:14161 |
| AC-7.3 | R-7, R-21 | TASK-01 | C-API 单元测试 | style_modifier.cpp:6267 |
| AC-7.4 | R-7 | TASK-01 | C-API 单元测试 | style_modifier.cpp:6273 |
| AC-7.6 | R-22 | TASK-01 | C-API 单元测试 | style_modifier.cpp:14185 |
| AC-7.7 | R-20 | TASK-01 | C-API 单元测试 | native_node_extented.cpp:1497 |
| AC-7.9 | R-23 | TASK-01 | C-API 单元测试 | rich_editor_native_impl.cpp:192 |
| AC-7.10 | R-24 | TASK-01 | C-API 单元测试 | rich_editor_native_impl.cpp:970 |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | Text 组件设置 `selection(start, end)` 属性 | JS 桥接 `JSText::SetTextSelection` 调用 `TextModel::SetTextSelection(start, end)`，不携带 MenuPolicy | 仅 2 参数，MenuPolicy 不可达 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 控制器 `setTextSelection(start, end, options?)` 调用 | 通过 `SelectionOptions` 携带 `MenuPolicy`，控制器层转发到 Pattern `SetSelectionFlag` | TextController 用值传递 `const SelectionOptions`；TextFieldController 用 `const std::optional<SelectionOptions>&` | AC-2.1–2.10 |
| R-3 | 边界 | Text 编程式选区设置（`SetTextSelection`/`SetSelectionFlag`）触发 | 受四重门控：`textSelectableMode != UNSELECTABLE && copyOption != None && textOverflow != MARQUEE && !textEffect_`，任一不满足则静默返回 | 无错误码返回，调用方无法感知失败 | AC-1.3–1.6, AC-6.2 |
| R-4 | 行为 | `textSelectable(mode)` 设置 | `SELECTABLE_FOCUSABLE` 时 `focusHub->SetFocusable(true) + SetIsFocusOnTouch(true)`；其它两值 `false`；`UNSELECTABLE` 时 `IsSelectableAndCopy()` 返回 false | `textSelectableMode` 同时持久化到 `TextLayoutProperty` 和 Pattern | AC-3.1–3.4 |
| R-5 | 边界 | RichEditor `setSelection` 调用 | 需组件已获焦，否则选区不设置 | `RichEditorPattern::SetSelection` 前置检查 `HasFocus()` | AC-2.5, AC-2.6 |
| R-6 | 异常 | C-API `NODE_TEXT_TEXT_SELECTION` 设置且 `start >= end` | 返回 `ERROR_CODE_PARAM_INVALID`，调用 `resetTextTextSelection` 重置 | Text 要求严格 `start < end`（空选区被拒绝） | AC-7.1, AC-7.2 |
| R-7 | 异常 | C-API `NODE_TEXT_INPUT_TEXT_SELECTION` / `NODE_TEXT_AREA_TEXT_SELECTION` 设置且 `start > end` | 返回 `ERROR_CODE_PARAM_INVALID` | TextInput/TextArea 允许 `start == end`（空选区/光标定位） | AC-7.3, AC-7.4, AC-7.5 |
| R-8 | 边界 | copyOption 语义因组件不同 | Text: `None` 完全禁用选区（含编程式）；TextField: copyOption 不门控选区；RichEditor: 仅门控 copy/cut 命令，不门控编程式选区 | 默认值：Text=None, TextInput/TextArea/RichEditor=Local | AC-4.1–4.7 |
| R-9 | 行为 | `MenuPolicy::DEFAULT` | Text/RichEditor: 保留当前菜单可见性；TextField: `nullopt` → 不显示菜单，显式 `DEFAULT` → 保留当前状态 | — | AC-2.10 |
| R-10 | 行为 | `MenuPolicy::SHOW` | 选区设置且选择菜单强制显示 | — | AC-2.7 |
| R-11 | 行为 | `MenuPolicy::HIDE` | 选区设置但选择菜单隐藏（手柄可能仍绘制，RichEditor 的 `HandlePolicy::HIDE` 关闭整个 overlay） | — | AC-2.8 |
| R-12 | 边界 | `TextFieldController::SetTextSelection` 传 `nullopt` options | `IsShowMenu` 返回 false（菜单不显示） | 与显式 `DEFAULT` 行为不同 | AC-2.9 |
| R-13 | 行为 | `getSelection()` 调用 | RichEditor 返回 `SelectionInfo`（含 resultObjects）；TextField/TextContentControllerBase 返回 `SelectionInfo`，C-API 转为 `TextRange { start, end }` | C-API 层丢弃 resultObjects | AC-5.1–5.3 |
| R-14 | 行为 | 无障碍 `ACTION_SET_SELECTION(start, end, isForward)` | Text: 受与编程式相同的门控（copyOption + textSelectableMode）；TextField: 调用 `SetSelectionFlag(start, end, nullopt, isForward)`；RichEditor: 调用 `SetSelection(start, end, nullopt, isForward)` | Text 的 `SetSpecificSupportAction` 仅在 `copyOption != None` 时注册 `ACTION_SET_SELECTION` | AC-6.1, AC-6.2 |
| R-15 | 恢复 | 无障碍 `ACTION_CLEAR_SELECTION` | Text: `CloseSelectOverlay(true) + ResetSelection()`；TextField: 设 `SelectionMode::NONE`，选区收缩为光标，启动光标闪烁；RichEditor: 关闭菜单 + 重置选区 + 启动闪烁 | — | AC-6.3 |
| R-16 | 边界 | `TextSelector::IsValid()` 判定 | `baseOffset > -1 && destinationOffset > -1` 时返回 true；`SelectNothing()` = `!IsValid() || baseOffset == destinationOffset` | `baseOffset`/`destinationOffset` 初始值均为 -1 | AC-1.2 |
| R-17 | 边界 | `TextFieldController::SetTextSelection` 传 `start > end` | 方法静默返回（`return`），选区不变 | 与 C-API `NODE_TEXT_INPUT_TEXT_SELECTION` 返回 PARAM_INVALID 不同 | AC-2.2 |
| R-18 | 边界 | TextField 选区设置延迟到布局完成 | `ScheduleTaskWithLayoutDeferral` 将 `SetSelectionFlag` 调用延迟到布局后执行 | Text 不延迟；RichEditor 也不延迟 | AC-2.11 |
| R-19 | 行为 | 无障碍查询 `GetTextSelectionStart/End` | Text: 返回 `TextSelector.GetTextStart()/GetTextEnd()` = `min/max(baseOffset, destinationOffset)`；TextField: 返回 `TextSelectController::GetStartIndex()/GetEndIndex()` = `min/max(firstHandle.index, secondHandle.index)` | 有序化返回（非 raw baseOffset） | AC-6.4, AC-6.5 |
| R-20 | 行为 | `OH_ArkUI_SelectionOptions_Create()` | 创建堆对象，`menuPolicy` 初始为 `ARKUI_MENU_POLICY_DEFAULT` | 调用方需 `_Dispose()` 释放 | AC-7.7 |
| R-21 | 边界 | C-API `NODE_TEXT_INPUT_TEXT_SELECTION` 不支持 `.object` options | 仅 `value[0].i32` + `value[1].i32`，MenuPolicy 不可通过属性设置，仅通过控制器方法可达 | 与 Text 的 `NODE_TEXT_TEXT_SELECTION` 支持 `.object` 不对称 | AC-7.3 |
| R-22 | 边界 | C-API `getAttribute(NODE_TEXT_TEXT_SELECTION)` 返回值 | 在 `g_attributeItem.object` 中堆分配新 `ArkUI_SelectionOptions*` | 静态全局缓冲区，生命周期注意 | AC-7.6 |
| R-23 | 行为 | `OH_ArkUI_TextEditorStyledStringController_SetSelection(controller, start, end, menuPolicy)` | `menuPolicy` 直接作为参数传递（非通过 options 对象），分发到 `setRichEditorSelection(handle, start, end, menuPolicy)` | @since 24 | AC-7.9 |
| R-24 | 行为 | `OH_ArkUI_TextEditorStyledStringController_GetSelection(controller, &start, &end)` | 通过 out-params 返回 `uint32_t` start/end，内部调用 `getSelectionRangeInfo(handle)` 返回 `std::pair` | @since 24；NULL controller/node/params 返回 `ARKUI_ERROR_CODE_PARAM_INVALID` | AC-7.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|---------|
| VM-1 | AC-1.1–1.6 | 单元测试 `text_pattern_test` | selection 属性门控逻辑与选区设置 |
| VM-2 | AC-2.1–2.11 | 单元测试 `text_field_controller_test`、`text_controller_test` | 控制器 setTextSelection 参数校验、clamp、延迟 |
| VM-3 | AC-3.1–3.4 | 单元测试 `text_pattern_test` | textSelectableMode 对 focusHub 的影响 |
| VM-4 | AC-4.1–4.7 | 单元测试 + 集成测试 | copyOption 在 Text/TextField/RichEditor 中的不同语义 |
| VM-5 | AC-5.1–5.3 | 单元测试 | getSelection 返回值结构 |
| VM-6 | AC-6.1–6.5 | 无障碍测试 | ACTION_SET_SELECTION/CLEAR_SELECTION 门控与执行 |
| VM-7 | AC-7.1–7.10 | C-API 单元测试 `native_node_test` | NODE_TEXT_TEXT_SELECTION 等属性的设置/获取/校验 |
| VM-8 | R-3 | 单元测试 | Text 多重门控组合矩阵 |
| VM-9 | R-6, R-7 | C-API 单元测试 | start vs end 校验差异 |
| VM-10 | R-8 | 集成测试 | copyOption 跨组件行为差异 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `TextAttribute.selection(start, end)` | Public | `number, number` | `TextAttribute` | N/A | 声明式 Text 选区设置 | AC-1.1 |
| `TextAttribute.textSelectable(mode)` | Public | `TextSelectableMode` | `TextAttribute` | N/A | Text 可选择模式 | AC-3.1 |
| `TextAttribute.copyOption(value)` | Public | `CopyOptions` | `TextAttribute` | N/A | Text 选区复制权限 | AC-4.1 |
| `TextAttribute.selectedBackgroundColor(color)` | Public | `ResourceColor` | `TextAttribute` | N/A | 选区高亮背景色 | — |
| `TextController.setTextSelection(start, end, options?)` | Public | `number \| undefined, number \| undefined, SelectionOptions?` | `void` | N/A | Text 编程式选区 | AC-2.7 |
| `TextInputController.setTextSelection(start, end, options?)` | Public | `number, number, SelectionOptions?` | `void` | N/A | TextInput 编程式选区 | AC-2.1 |
| `TextAreaController.setTextSelection(start, end, options?)` | Public | `number, number, SelectionOptions?` | `void` | N/A | TextArea 编程式选区 | AC-2.3 |
| `SearchController.setTextSelection(start, end, options?)` | Public | `number, number, SelectionOptions?` | `void` | N/A | Search 编程式选区 | AC-2.4 |
| `RichEditorBaseController.setSelection(start, end, options?)` | Public | `number, number, SelectionOptions?` | `void` | N/A | RichEditor 编程式选区 | AC-2.5 |
| `RichEditorController.getSelection()` | Public | 无 | `RichEditorSelection` | N/A | 查询 RichEditor 选区+spans | AC-5.1 |
| `TextContentControllerBase.getSelection()` | Public | 无 | `TextRange` | N/A | 查询 TextField 选区范围 | AC-5.2 |
| `SelectionOptions`（接口） | Public | `{ menuPolicy?: MenuPolicy }` | — | — | 选区选项 | AC-2.7 |
| `MenuPolicy`（枚举） | Public | `DEFAULT=0, HIDE=1, SHOW=2` | — | — | 选区菜单策略 | AC-2.7 |
| `CopyOptions`（枚举） | Public | `None=0, InApp=1, LocalDevice=2, CrossDevice=3` | — | — | 复制权限范围 | AC-4.1 |
| `TextSelectableMode`（枚举） | Public | `SELECTABLE_UNFOCUSABLE=0, SELECTABLE_FOCUSABLE=1, UNSELECTABLE=2` | — | — | 可选择模式 | AC-3.1 |
| C-API `NODE_TEXT_TEXT_SELECTION` (=1046) | Public | `value[0].i32, value[1].i32, object=ArkUI_SelectionOptions*` | `ArkUI_AttributeItem` | `ERROR_CODE_PARAM_INVALID` | C-API Text 选区 | AC-7.1 |
| C-API `NODE_TEXT_INPUT_TEXT_SELECTION` | Public | `value[0].i32, value[1].i32` | `ArkUI_AttributeItem` | `ERROR_CODE_PARAM_INVALID` | C-API TextInput 选区 | AC-7.3 |
| C-API `NODE_TEXT_AREA_TEXT_SELECTION` | Public | `value[0].i32, value[1].i32` | `ArkUI_AttributeItem` | `ERROR_CODE_PARAM_INVALID` | C-API TextArea 选区 | AC-7.5 |
| C-API `OH_ArkUI_SelectionOptions_Create/Dispose/SetMenuPolicy/GetMenuPolicy` | Public | `ArkUI_SelectionOptions*` / `ArkUI_MenuPolicy` | `ArkUI_SelectionOptions*` / `ArkUI_MenuPolicy` | N/A | C-API 选区选项对象 | AC-7.7 |
| C-API `OH_ArkUI_TextEditorStyledStringController_SetSelection` | Public | `controller, uint32_t start, uint32_t end, ArkUI_MenuPolicy` | `ArkUI_ErrorCode` | `ARKUI_ERROR_CODE_PARAM_INVALID` | C-API RichEditor 选区设置 | AC-7.9 |
| C-API `OH_ArkUI_TextEditorStyledStringController_GetSelection` | Public | `controller, uint32_t* start, uint32_t* end` | `ArkUI_ErrorCode` | `ARKUI_ERROR_CODE_PARAM_INVALID` | C-API RichEditor 选区查询 | AC-7.10 |

### 变更/废弃 API

无变更或废弃 API。本特性为已有实现的规格补录，不引入 API 变更。

## 接口规格

### 接口定义

**TextAttribute.selection(selectionStart, selectionEnd)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextAttribute selection(number selectionStart, number selectionEnd)` |
| 返回值 | `TextAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A（JS 层静默） |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| selectionStart | number | 是 | — | 应 >= 0；负值/NaN 不设置选区 |
| selectionEnd | number | 是 | — | 应 > selectionStart；否则选区无效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | start < end 且所有门控通过 | 选区高亮 + onTextSelectionChange 触发 | AC-1.1 |
| 2 | start >= end | Pattern 层不设置有效选区 | AC-1.2 |
| 3 | textSelectableMode = UNSELECTABLE | 静默返回 | AC-1.3 |
| 4 | copyOption = None | 静默返回 | AC-1.4 |

---

**TextInputController.setTextSelection(selectionStart, selectionEnd, options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void setTextSelection(number selectionStart, number selectionEnd, SelectionOptions? options)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2, AC-2.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| selectionStart | number | 是 | — | 自动 clamp 到 [0, textLength]；start > end 时静默返回 |
| selectionEnd | number | 是 | — | 自动 clamp 到 [0, textLength] |
| options | SelectionOptions | 否 | undefined (nullopt) | nullopt 时菜单不显示；显式 DEFAULT 保留当前状态 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | start <= end | 选区设置 [start, end) + 延迟到布局后执行 | AC-2.1, AC-2.11 |
| 2 | start > end | 静默返回 | AC-2.2 |
| 3 | options = undefined | 菜单不显示 | AC-2.9 |
| 4 | options.menuPolicy = SHOW | 菜单强制显示 | AC-2.7 |

---

**C-API setAttribute(node, NODE_TEXT_TEXT_SELECTION, item)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t setAttribute(ArkUI_NodeHandle node, ArkUI_NodeAttributeType type, const ArkUI_AttributeItem* item)` |
| 返回值 | `int32_t` — `ERROR_CODE_NO_ERROR` 或 `ERROR_CODE_PARAM_INVALID` |
| 开放范围 | Public |
| 错误码 | `ERROR_CODE_PARAM_INVALID` (start >= end) |
| 关联 AC | AC-7.1, AC-7.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| item.value[0].i32 | int32_t | 是 | — | start 位置；必须 < end |
| item.value[1].i32 | int32_t | 是 | — | end 位置 |
| item.object | ArkUI_SelectionOptions* | 否 | nullptr | 携带 menuPolicy；nullptr 时使用 DEFAULT |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | start < end | 选区设置 + 按 menuPolicy 控制菜单 | AC-7.1 |
| 2 | start >= end | 返回 PARAM_INVALID + resetTextTextSelection | AC-7.2 |
| 3 | object != nullptr | 读取 menuPolicy | AC-7.8 |

---

**C-API OH_ArkUI_SelectionOptions_Create()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_SelectionOptions* OH_ArkUI_SelectionOptions_Create()` |
| 返回值 | `ArkUI_SelectionOptions*` — 堆分配对象 |
| 开放范围 | Public (@since 23) |
| 错误码 | N/A |
| 关联 AC | AC-7.7 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 Create | 返回 menuPolicy=DEFAULT 的对象 | AC-7.7 |
| 2 | 调用 SetMenuPolicy(SHOW) | 后续 setTextSelection 菜单强制显示 | AC-7.8 |
| 3 | 调用 Dispose | 释放堆内存 | AC-7.7 |

## 兼容性声明

- **已有 API 行为变更:** 否。本特性为已有实现的规格补录，不修改任何 API 行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7（最早的 `caretPosition` / `copyOption` 出现于 API 7–9）。
- **API 版本号策略:** 全版本 @since 标注（API 7→26）。关键里程碑：API 9 `copyOption`、API 10 `setTextSelection`(TextInput/TextArea)、API 11 `selection`/`getSelection`(RichEditor)、API 12 `textSelectable`/`SelectionOptions`/`MenuPolicy`/`setTextSelection`(Search)、API 15 `getSelection`(TextContentControllerBase)、API 23 `NODE_TEXT_TEXT_SELECTION` C-API/`OH_ArkUI_SelectionOptions`/`TextController.setTextSelection`、API 24 `OH_ArkUI_TextEditorStyledStringController_SetSelection/GetSelection`、API 26 `NODE_TEXT_ON_TEXT_SELECTION_CHANGE` 事件。

### 已知兼容性风险

| 风险 | 说明 | 影响 |
|------|------|------|
| C-API MenuPolicy 支持不对称 | Text 的 `NODE_TEXT_TEXT_SELECTION` 支持 `.object` 传 `ArkUI_SelectionOptions`，但 TextInput/TextArea 的选区属性不支持 `.object`——MenuPolicy 仅通过控制器方法可达 | 中 |
| copyOption 语义因组件不同 | Text 的 `None` 完全禁用选区；TextField 的 `None` 不门控选区；RichEditor 的 `None` 仅禁用 copy/cut 命令 | 高 |
| 默认 copyOption 因组件不同 | Text 默认 `None`（选区默认禁用）；TextInput/TextArea/RichEditor 默认 `Local`（选区默认启用） | 高 |
| C-API 选区校验规则不同 | Text 要求 `start < end`（严格）；TextInput/TextArea 要求 `start <= end`（允许空选区） | 中 |
| Text 编程式选区静默失败 | `SetTextSelection` 在门控不通过时静默返回，无错误码，调用方无法感知失败 | 中 |
| C-API getter 堆分配 | `GetTextTextSelection` 在 `g_attributeItem.object` 中堆分配 `ArkUI_SelectionOptions*`，使用静态全局缓冲区 | 低 |
| CopyOptions 枚举值命名差异 | SDK `.d.ts` 定义为 `LocalDevice`/`CrossDevice`；C++ 源码命名为 `Local`/`Distributed` | 低 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|---------|
| 选区状态为运行时态 | `TextSelector` 选区范围不持久化到 `LayoutProperty`，仅在 Pattern 层维护；`textSelectableMode` 则同时持久化到 `TextLayoutProperty` | AC-1.1, AC-3.1 |
| 方向无关选区模型 | `TextSelector` 使用 `baseOffset`/`destinationOffset`（方向无关），`GetTextStart()/GetTextEnd()` 有序化返回 | AC-6.4 |
| 控制器→Model→Pattern 分层 | 控制器方法 → Model 静态方法 → Pattern `SetSelectionFlag`，不直接操作 LayoutProperty | AC-2.1, AC-2.7 |
| 三种 SelectionOptions 类型 | 运行时 `SelectionOptions`(text_field_model.h:204) / 缓存态 `TextSelectionOptions`(text_model.h:57) / C-API `ArkUI_SelectionOptions`(node_extened.h:250) | AC-2.7, AC-7.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 编程式选区设置到高亮渲染 < 1 帧 | 单元测试 + Trace | text_field_controller.cpp:82 |
| 内存 | `ArkUI_SelectionOptions` 每次 Create 堆分配 ~16 字节 | C-API 单元测试 | native_node_extented.cpp:1499 |
| 可靠性 | 选区设置在组件未布局时延迟执行，不丢失 | 单元测试 | text_field_controller.cpp:82 |
| 可测试性 | 所有选区 API 可通过单元测试 + C-API 测试验证 | 单元测试 | — |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

> 选区状态模型与编程式选区在所有设备类型上行为一致。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 是 | `ACTION_SET_SELECTION`/`ACTION_CLEAR_SELECTION`/`GetTextSelectionStart/End` 驱动选区，受与编程式相同的门控 | AC-6.1–6.5 |
| 大字体 | 否 | 选区范围不受字体大小影响 | — |
| 深色模式 | 否 | 选区高亮颜色 `selectedBackgroundColor` 可由主题适配，但选区逻辑不涉及 | — |
| 多窗口/分屏 | 否 | 选区为组件级状态，不受窗口影响 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 7→26 逐步新增选区能力，@since 差异见兼容性声明 | AC-1.1–7.10 |
| 生态兼容 | 否 | — | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 选区状态模型与编程式选区
  作为应用开发者
  我想要通过属性和控制器方法设置/查询文本选区
  以便在运行时动态控制选中文本

  Scenario: Text 声明式选区正常设置
    Given Text 组件已创建，copyOption != None，textSelectableMode != UNSELECTABLE，textOverflow != MARQUEE，无 textEffect
    When 设置 selection(2, 8)
    Then 选区高亮显示 [2, 8) 范围文本
    And onTextSelectionChange(2, 8) 被触发

  Scenario: Text 声明式选区因 copyOption=None 被门控
    Given Text 组件 copyOption = None
    When 设置 selection(2, 8)
    Then 选区不设置，无高亮
    And onTextSelectionChange 不触发

  Scenario: TextInput 编程式选区正常设置
    Given TextInput 组件已创建，textLength = 10
    When 调用 TextInputController.setTextSelection(3, 7)
    Then 选区设置为 [3, 7)
    And 选择菜单不显示（options 未传）

  Scenario: C-API Text 选区 start >= end 被拒绝
    Given ArkUI_NodeHandle 指向 ARKUI_NODE_TEXT
    When setAttribute(node, NODE_TEXT_TEXT_SELECTION, {value[0].i32=5, value[1].i32=3})
    Then 返回 ERROR_CODE_PARAM_INVALID
    And 调用 resetTextTextSelection

  Scenario Outline: C-API TextInput 选区校验
    Given ArkUI_NodeHandle 指向 ARKUI_NODE_TEXT_INPUT
    When setAttribute(node, NODE_TEXT_INPUT_TEXT_SELECTION, {value[0].i32=<start>, value[1].i32=<end>})
    Then 返回 <errorCode>

    Examples:
      | start | end | errorCode |
      | 2 | 8 | ERROR_CODE_NO_ERROR |
      | 5 | 5 | ERROR_CODE_NO_ERROR |
      | 8 | 3 | ERROR_CODE_PARAM_INVALID |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰——光标/菜单/剪贴板/事件留给 04-14-03）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TextSelector 选区状态结构 baseOffset/destinationOffset 方向无关模型实现"
  - repo: "openharmony/ace_engine"
    query: "TextPattern::SetSelectionFlag 多重门控逻辑（textSelectableMode + copyOption + marquee + textEffect）"
  - repo: "openharmony/ace_engine"
    query: "C-API NODE_TEXT_TEXT_SELECTION 选区属性设置分发链路 style_modifier.cpp → TextModifier"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_SelectionOptions_Create/Dispose/SetMenuPolicy C-API 对象生命周期"
  - repo: "openharmony/ace_engine"
    query: "copyOption 跨组件语义差异（Text 禁用选区 vs TextField 不门控 vs RichEditor 仅门控命令）"
```

**关键文档：** `design.md`（架构设计）、`interface/sdk-js/api/@internal/component/ets/text.d.ts`（SDK 动态 API）、`interfaces/native/native_node.h`（C-API 枚举定义）
