# 特性规格

> Func-05-09-02-Feat-07 编辑生命周期与内容变化事件：固化 RichEditor 组件编辑生命周期回调（`onReady`、`onEditingChange`、`onSubmit`）、删除事件（`aboutToDelete`、`onDeleteComplete`）、内容变化事件（`onWillChange`、`onDidChange`）与选区事件（`onSelect`、`onSelectionChange`）的行为规格。这些事件覆盖组件就绪、编辑态切换、提交、删除拦截与完成、内容变更前/后拦截、选区变更等场景，不涉及 IME 输入与剪贴板（见 Feat-06 与 Feat-09）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 编辑生命周期与内容变化事件 (Editing Lifecycle & Content Change Events) |
| 特性编号 | Func-05-09-02-Feat-07 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10+ 至 API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 `onReady` 行为规格 | 组件首次布局完成后触发一次，不可重复 |
| MODIFIED | 补齐 `onEditingChange` 行为规格 | 编辑态切换（获焦/失焦）时触发，带状态去重 |
| MODIFIED | 补齐 `onSubmit` 行为规格 | 回车键提交时触发，含 `KeepEditable` 拦截与 `NEW_LINE` 换行 |
| MODIFIED | 补齐 `aboutToDelete` 行为规格 | 删除前拦截回调，返回 boolean 控制是否放行 |
| MODIFIED | 补齐 `onDeleteComplete` 行为规格 | 删除完成后触发，含 UiSession 上报 |
| MODIFIED | 补齐 `onWillChange` 行为规格 | 内容变更前拦截回调，返回 boolean 控制是否放行 |
| MODIFIED | 补齐 `onDidChange` 行为规格 | 内容变更完成后触发，与 `onWillChange` 构成 will/did 时序 |
| MODIFIED | 补齐 `onSelect` 行为规格 | 选区变化时携带完整 spans 信息触发 |
| MODIFIED | 补齐 `onSelectionChange` 行为规格 | 选区范围变化时携带 range 触发，带范围去重 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/09-text-components/02-rich-editor/design.md` | 已创建 |

---

## 用户故事

### US-1: 组件就绪事件（onReady）

**作为** 应用开发者,
**我想要** 在 RichEditor 组件首次布局完成时收到通知,
**以便** 在组件可交互后执行初始化逻辑（如设置光标、注入内容）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `OnDirtyLayoutWrapperSwap` 执行且 `isRichEditorInit_` 为 false THEN 调用 `FireOnReady()`（`rich_editor_pattern.cpp:841`），事件中心执行 `onReady_` 回调后通过 `AddAfterRenderTask` 注册 `MarkDirtyNode(PROPERTY_UPDATE_MEASURE)` 后渲染任务（`rich_editor_event_hub.cpp:30-37`） | 正常 |
| AC-1.2 | WHEN `FireOnReady()` 执行完毕 THEN 设置 `isRichEditorInit_ = true` 和 `isFirstCallOnReady_ = true`（`rich_editor_pattern.cpp:933-934`），后续布局交换不再触发 `onReady` | 边界 |
| AC-1.3 | WHEN 未注册 `onReady` 回调 THEN `FireOnReady` 中 `onReady_` 为空不执行回调，但仍设置 `isRichEditorInit_` 标志位（`rich_editor_event_hub.cpp:30` 空检查） | 边界 |

### US-2: 编辑态切换事件（onEditingChange）

**作为** 应用开发者,
**我想要** 在 RichEditor 编辑态（获焦/失焦）切换时收到通知,
**以便** 根据编辑状态驱动业务逻辑（如显示/隐藏工具栏）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 单击获焦（`focusHub->IsCurrentFocus()` 为 true）THEN 调用 `HandleOnEditChanged(true)`（`rich_editor_pattern.cpp:3776`），经 `isEditing_ != isEditing` 去重后设置 `isEditing_ = true` 并触发 `FireOnEditingChange(true)`（`rich_editor_pattern.cpp:12125-12126`） | 正常 |
| AC-2.2 | WHEN 组件失焦（`OnBlur` 执行且 `BlurReason != WINDOW_BLUR`）THEN 调用 `HandleOnEditChanged(false)`（`rich_editor_pattern.cpp:4220`），触发 `FireOnEditingChange(false)` | 正常 |
| AC-2.3 | WHEN 双击或长按进入编辑 THEN 调用 `HandleOnEditChanged(true)`（`rich_editor_pattern.cpp:3882, 4675, 13658`） | 正常 |
| AC-2.4 | WHEN `isEditing_` 已等于目标值 THEN `CHECK_NULL_VOID(isEditing_ != isEditing)` 直接返回，不触发回调（`rich_editor_pattern.cpp:12118`） | 边界 |
| AC-2.5 | WHEN 进入编辑态且 `CanStartAITask()` 为 true THEN 触发 `FireOnEditingChange` 后调用 `dataDetectorAdapter_->StartAITask()`（`rich_editor_pattern.cpp:12128-12130`）；否则若 `isEditing` 为 true 则重置 `previewLongPress_` 并 `MarkDirtyNode`（`rich_editor_pattern.cpp:12132-12136`） | 正常 |

### US-3: 提交事件（onSubmit）

**作为** 应用开发者,
**我想要** 在 RichEditor 回车键提交时收到回车键类型与事件对象,
**以便** 控制提交后是否保持编辑态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `PerformAction(action, forceCloseKeyboard)` 被调用 THEN 若 `action == TextInputAction::NEW_LINE` 先执行 `InsertValue(u"\n", true)` 插入换行（`rich_editor_pattern.cpp:12234-12237`） | 正常 |
| AC-3.2 | WHEN 构造 `TextFieldCommonEvent event` 并调用 `eventHub->FireOnSubmit(static_cast<int32_t>(action), event)` THEN 事件中心将 `action` 与 `event` 传递给 `onSubmit_` 回调（`rich_editor_pattern.cpp:12240-12242`, `rich_editor_event_hub.cpp:319-323`） | 正常 |
| AC-3.3 | WHEN 回调中 `event.IsKeepEditable()` 为 true 或 `action == NEW_LINE` THEN 不调用 `StopEditing()`，保持编辑态（`rich_editor_pattern.cpp:12244-12245`） | 边界 |
| AC-3.4 | WHEN 回调未设置 `KeepEditable` 且 `action != NEW_LINE` THEN 调用 `StopEditing()` → `FocusHub::LostFocusToViewRoot()` 退出编辑态（`rich_editor_pattern.cpp:12248`, `12251-12256`） | 正常 |

### US-4: 删除前拦截事件（aboutToDelete）

**作为** 应用开发者,
**我想要** 在 RichEditor 内容被删除前收到删除值信息并拦截,
**以便** 控制是否允许删除操作执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `DoDeleteActions(currentPosition, length, info, isIME)` 执行 THEN 调用 `eventHub->FireAboutToDelete(info)` 获取 `allowDelete` 返回值（`rich_editor_pattern.cpp:7206`） | 正常 |
| AC-4.2 | WHEN 未注册 `aboutToDelete` 回调 THEN `FireAboutToDelete` 返回 `true`（默认放行）（`rich_editor_event_hub.cpp:83-84`） | 边界 |
| AC-4.3 | WHEN 回调返回 false（拦截删除）且 `!IsPreviewTextInputting()` THEN `doDelete = allowDelete` 为 false，不执行 `DeleteByDeleteValueInfo`（`rich_editor_pattern.cpp:7209-7210`） | 正常 |
| AC-4.4 | WHEN 回调返回 false 但 `IsPreviewTextInputting()` 为 true THEN `doDelete = allowDelete || IsPreviewTextInputting()` 为 true，仍执行删除（预览输入态覆盖拦截）（`rich_editor_pattern.cpp:7209`） | 边界 |
| AC-4.5 | WHEN `FireAboutToDelete` 返回后 THEN 调用 `info.ResetRichEditorDeleteSpans()` 清空再 `CalcDeleteValueObj` 重新计算删除值（`rich_editor_pattern.cpp:7207-7208`） | 正常 |

### US-5: 删除完成事件（onDeleteComplete）

**作为** 应用开发者,
**我想要** 在 RichEditor 删除操作完成后收到通知,
**以便** 在删除生效后刷新依赖状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `doDelete` 为 true 且删除执行完毕 THEN 调用 `eventHub->FireOnDeleteComplete()`（`rich_editor_pattern.cpp:7221`） | 正常 |
| AC-5.2 | WHEN `FireOnDeleteComplete` 执行且 `onDeleteComplete_` 已注册 THEN 调用回调并通过 `UiSessionManager::ReportComponentChangeEvent` 上报 `"RichEditor.onDeleteComplete"` 事件（`rich_editor_event_hub.cpp:96-102`） | 正常 |
| AC-5.3 | WHEN `doDelete` 为 false（删除被拦截）THEN 不调用 `FireOnDeleteComplete`（`rich_editor_pattern.cpp:7209-7221` 分支跳过） | 边界 |

### US-6: 内容变更前拦截事件（onWillChange）

**作为** 应用开发者,
**我想要** 在 RichEditor 内容变更前收到变更值并拦截,
**以便** 控制是否允许内容变更执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `BeforeChangeText` 执行且 `HasOnWillChange()` 或 `HasOnDidChange()` 为 true THEN 构造 `RichEditorChangeValue`（含 `rangeBefore`/`replacedSpans`/`replacedImageSpans`/`replacedSymbolSpans`/`changeReason`）并调用 `FireOnWillChange(changeValue)` 返回布尔值（`rich_editor_pattern.cpp:12700-12706, 12952-12960`） | 正常 |
| AC-6.2 | WHEN 未注册 `onWillChange` 回调 THEN `FireOnWillChange` 返回 `true`（默认放行）（`rich_editor_event_hub.cpp:142-143`） | 边界 |
| AC-6.3 | WHEN `BeforeChangeText` 中 `!HasOnWillChange() && !HasOnDidChange()` THEN 直接返回 `true`，不构造变更值（`rich_editor_pattern.cpp:12704-12706, 12958-12960`） | 边界 |
| AC-6.4 | WHEN 添加 SymbolSpan 前 THEN `BeforeAddSymbol` 构造 `RichEditorChangeValue` 并调用 `FireOnWillChange`，若 `!HasOnWillChange()` 直接返回 true（`rich_editor_pattern.cpp:1898-1902, 1927`） | 正常 |
| AC-6.5 | WHEN `DeleteSpans` 执行 THEN 构造 `RichEditorChangeValue`（`rangeBefore`/`rangeAfter` 均为 `{start, start}`），调用 `FireOnWillChange`，返回 false 则 `CHECK_NULL_VOID` 中止删除（`rich_editor_pattern.cpp:2003-2008`） | 正常 |

### US-7: 内容变更完成事件（onDidChange）

**作为** 应用开发者,
**我想要** 在 RichEditor 内容变更完成后收到变更值,
**以便** 在内容生效后执行后续逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `AfterContentChange` 执行 THEN 先调用 `ReportTextChange()`，再检查 `eventHub->HasOnDidChange()`（`rich_editor_pattern.cpp:1933-1935`） | 正常 |
| AC-7.2 | WHEN `HasOnDidChange()` 为 true THEN `HasOnDidChange` 内部调用 `pattern->SetContentChange(true)` 后返回 `onDidChange_` 是否注册（`rich_editor_event_hub.cpp:166-174`），随后调用 `FireOnDidChange(changeValue)`（`rich_editor_pattern.cpp:1936`） | 正常 |
| AC-7.3 | WHEN `FireOnDidChange` 执行完毕 THEN 调用 `ForceTriggerAvoidOnCaretChange()` 和 `ReportAfterContentChangeEvent()`（`rich_editor_pattern.cpp:1938-1939`） | 正常 |
| AC-7.4 | WHEN 未注册 `onDidChange` 回调 THEN `HasOnDidChange` 返回 false，不触发 `FireOnDidChange`（但 `SetContentChange(true)` 仍被调用）（`rich_editor_event_hub.cpp:170-173`） | 边界 |

### US-8: 选区事件（onSelect）

**作为** 应用开发者,
**我想要** 在 RichEditor 选区变化时收到完整选区信息（含 spans）,
**以便** 获取用户选中的内容详情。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN `FireOnSelect(selectStart, selectEnd)` 被调用 THEN 通过 `GetSpansInfo(selectStart, selectEnd, GetSpansMethod::ONSELECT)` 构造 `TextSelectionInfo`（`rich_editor_pattern.cpp:9230`） | 正常 |
| AC-8.2 | WHEN `textSelectInfo.GetSelection().resultObjects` 非空 THEN 调用 `eventHub->FireOnSelect(&textSelectInfo)` 传递选区信息（`rich_editor_pattern.cpp:9231-9232`） | 正常 |
| AC-8.3 | WHEN `resultObjects` 为空 THEN 不触发 `FireOnSelect`（`rich_editor_pattern.cpp:9231` 条件不满足） | 边界 |
| AC-8.4 | WHEN 手势选择、双击选择、全选、鼠标选择、长按选择触发 THEN 分别调用 `FireOnSelect` 携带当前 `textSelector_` 的 TextStart/TextEnd（`rich_editor_pattern.cpp:4603, 4725, 7907, 7970, 8773`） | 正常 |

### US-9: 选区范围事件（onSelectionChange）

**作为** 应用开发者,
**我想要** 在 RichEditor 选区范围变化时收到轻量 range 信息,
**以便** 高频监听光标/选区范围变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN `FireOnSelectionChange(start, end, isForced)` 被调用 THEN 检查 `isForced || HasFocus() || hasClickedMenuOption_`，不满足则直接返回（`rich_editor_pattern.cpp:2556`） | 正常 |
| AC-9.2 | WHEN `start < 0` 或 `end < 0` THEN 直接返回不触发（`rich_editor_pattern.cpp:2560-2561`） | 边界 |
| AC-9.3 | WHEN `start == end` 且 `!caretTwinkling_` 且 `!isSingleHandle` THEN 直接返回不触发（光标无闪烁且非单句柄场景）（`rich_editor_pattern.cpp:2563-2564`） | 边界 |
| AC-9.4 | WHEN `start > end` THEN `std::swap(start, end)` 交换后继续（`rich_editor_pattern.cpp:2566-2567`） | 边界 |
| AC-9.5 | WHEN 构造 `SelectionRangeInfo(start, end)` 等于 `lastSelectionRange_` THEN 直接返回（范围去重）（`rich_editor_pattern.cpp:2569-2572`） | 边界 |
| AC-9.6 | WHEN 范围通过去重 THEN 更新 `lastSelectionRange_` 并调用 `eventHub->FireOnSelectionChange(&range)`（`rich_editor_pattern.cpp:2573-2574`） | 正常 |
| AC-9.7 | WHEN 布局交换、光标更新、光标闪烁启动、长按选择触发 THEN 分别调用 `FireOnSelectionChange`（`rich_editor_pattern.cpp:906, 2520, 3643, 8777`） | 正常 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1, R-2 | N/A（存量） | 代码审查 | `rich_editor_pattern.cpp:841, 928-935`, `rich_editor_event_hub.cpp:28-38` |
| AC-2.1~2.5 | R-3, R-4 | N/A | 代码审查 | `rich_editor_pattern.cpp:3776, 4220, 12116-12138`, `rich_editor_event_hub.cpp:123-133` |
| AC-3.1~3.4 | R-5, R-6 | N/A | 代码审查 | `rich_editor_pattern.cpp:12228-12256`, `rich_editor_event_hub.cpp:314-324` |
| AC-4.1~4.5 | R-7, R-8 | N/A | 代码审查 | `rich_editor_pattern.cpp:7201-7225`, `rich_editor_event_hub.cpp:76-88` |
| AC-5.1~5.3 | R-9, R-10 | N/A | 代码审查 | `rich_editor_pattern.cpp:7221`, `rich_editor_event_hub.cpp:90-103` |
| AC-6.1~6.5 | R-11, R-12 | N/A | 代码审查 | `rich_editor_pattern.cpp:12700-12706, 12952-12960, 1898-1929, 2003-2008`, `rich_editor_event_hub.cpp:135-147` |
| AC-7.1~7.4 | R-13, R-14 | N/A | 代码审查 | `rich_editor_pattern.cpp:1931-1939`, `rich_editor_event_hub.cpp:154-174` |
| AC-8.1~8.4 | R-15, R-16 | N/A | 代码审查 | `rich_editor_pattern.cpp:9226-9234, 4603, 4725, 7907, 7970, 8773`, `rich_editor_event_hub.cpp:273-283` |
| AC-9.1~9.7 | R-17, R-18 | N/A | 代码审查 | `rich_editor_pattern.cpp:2552-2575, 906, 2520, 3643`, `rich_editor_event_hub.cpp:285-295` |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 首次 `OnDirtyLayoutWrapperSwap` 且 `!isRichEditorInit_` | 调用 `FireOnReady` → 执行回调 → 注册 AfterRenderTask 标脏 | `isRichEditorInit_` 初始 false（`rich_editor_pattern.h:1345`） | AC-1.1 |
| R-2 | 边界 | `FireOnReady` 后设置 `isRichEditorInit_ = true` | 后续布局交换不再触发 onReady | 一次性触发，不可重复 | AC-1.2, AC-1.3 |
| R-3 | 行为 | `HandleOnEditChanged(isEditing)` 且 `isEditing_ != isEditing` | 设置 `isEditing_` → `FireOnEditingChange(isEditing)` → 按需启动 AI 任务或 MarkDirtyNode | `isEditing_` 初始 false（`rich_editor_pattern.h:1414`） | AC-2.1~2.3, AC-2.5 |
| R-4 | 边界 | `isEditing_` 已等于目标值 | `CHECK_NULL_VOID` 直接返回，不触发回调 | 状态去重 | AC-2.4 |
| R-5 | 行为 | `PerformAction(action)` 被调用 | NEW_LINE 先插换行 → 构造 `TextFieldCommonEvent` → `FireOnSubmit(action, event)` | `action_` 默认 `TextInputAction::NEW_LINE`（`rich_editor_pattern.h:1417`） | AC-3.1, AC-3.2 |
| R-6 | 边界 | 回调设置 `KeepEditable` 或 `action == NEW_LINE` | 不调用 `StopEditing`，保持编辑态；否则 `LostFocusToViewRoot` 退出 | `TextFieldCommonEvent::IsKeepEditable()` 控制拦截 | AC-3.3, AC-3.4 |
| R-7 | 行为 | `DoDeleteActions` 执行 | `FireAboutToDelete(info)` 返回 `allowDelete`；返回后 `ResetRichEditorDeleteSpans` + `CalcDeleteValueObj` 重算 | `RichEditorDeleteValue` 含 offset/direction/length/spans（`rich_editor_value.h:68-123`） | AC-4.1, AC-4.5 |
| R-8 | 边界 | 回调返回 false（拦截）| `doDelete = allowDelete \|\| IsPreviewTextInputting()`；预览输入态覆盖拦截 | 未注册回调时 `FireAboutToDelete` 返回 true（`rich_editor_event_hub.cpp:83-84`） | AC-4.2~4.4 |
| R-9 | 行为 | `doDelete` 为 true 且删除执行完毕 | 调用 `FireOnDeleteComplete` → 执行回调 + `UiSessionManager` 上报 | 上报事件类型 `COMPONENT_EVENT_TEXT_INPUT` | AC-5.1, AC-5.2 |
| R-10 | 边界 | `doDelete` 为 false（删除被拦截）| 不触发 `FireOnDeleteComplete` | 分支跳过（`rich_editor_pattern.cpp:7211` 条件不满足） | AC-5.3 |
| R-11 | 行为 | `BeforeChangeText` 且 `HasOnWillChange() \|\| HasOnDidChange()` | 构造 `RichEditorChangeValue` → `FireOnWillChange` 返回布尔 | `RichEditorChangeValue` 含 rangeBefore/rangeAfter/replacedSpans/changeReason（`rich_editor_value.h:125-214`） | AC-6.1, AC-6.4, AC-6.5 |
| R-12 | 边界 | 未注册 `onWillChange` | `FireOnWillChange` 返回 true（默认放行）；`BeforeChangeText` 中若无 will/did 回调直接返回 true | `TextChangeReason` 枚举 13 值（`constants.h:359-373`） | AC-6.2, AC-6.3 |
| R-13 | 行为 | `AfterContentChange` 且 `HasOnDidChange()` 为 true | `SetContentChange(true)` → `FireOnDidChange(changeValue)` → `ForceTriggerAvoidOnCaretChange` + `ReportAfterContentChangeEvent` | will/did 时序：will 在变更前，did 在变更后 | AC-7.1~7.3 |
| R-14 | 边界 | 未注册 `onDidChange` | `HasOnDidChange` 返回 false（但 `SetContentChange(true)` 仍执行），不触发 `FireOnDidChange` | `HasOnDidChange` 副作用：调用 `SetContentChange`（`rich_editor_event_hub.cpp:172`） | AC-7.4 |
| R-15 | 行为 | `FireOnSelect(start, end)` 被调用 | `GetSpansInfo(ONSELECT)` 构造选区信息 → `resultObjects` 非空时 `FireOnSelect(&info)` | `RichEditorSelection` 含 `selection: [int32, int32]` + `spans`（`richEditor.ets:1233-1236`） | AC-8.1, AC-8.2, AC-8.4 |
| R-16 | 边界 | `resultObjects` 为空 | 不触发 `FireOnSelect`（条件不满足） | 空选区保护 | AC-8.3 |
| R-17 | 行为 | `FireOnSelectionChange(start, end, isForced)` 通过全部守卫 | 更新 `lastSelectionRange_` → `FireOnSelectionChange(&range)` | `SelectionRangeInfo` 含 start_/end_（`selection_info.h:171-181`）；`RichEditorRange` 含 start?/end?（`richEditor.ets:1179-1182`） | AC-9.1, AC-9.6, AC-9.7 |
| R-18 | 边界 | 范围守卫不满足 | start/end <0 返回；start==end 且无闪烁且非单句柄返回；range 去重返回；start>end 交换 | `lastSelectionRange_` 初始 `{-1, -1}`（`rich_editor_pattern.h:1410`） | AC-9.2~9.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.3（onReady） | 代码审查 | `isRichEditorInit_` 一次性守卫、AfterRenderTask 注册、回调空检查 |
| VM-2 | AC-2.1~2.5（onEditingChange） | 代码审查 | `HandleOnEditChanged` 状态去重、获焦/失焦/双击/长按触发路径、AI 任务分支 |
| VM-3 | AC-3.1~3.4（onSubmit） | 代码审查 | `PerformAction` 换行插入、`KeepEditable` 拦截、`StopEditing` 退出路径 |
| VM-4 | AC-4.1~4.5（aboutToDelete） | 代码审查 | `FireAboutToDelete` 返回值、预览输入态覆盖、`ResetRichEditorDeleteSpans` 重算 |
| VM-5 | AC-5.1~5.3（onDeleteComplete） | 代码审查 | `doDelete` 守卫、`UiSessionManager` 上报、拦截时不触发 |
| VM-6 | AC-6.1~6.5（onWillChange） | 代码审查 | `BeforeChangeText` 双重守卫、SymbolSpan 路径、DeleteSpans 路径、默认放行 |
| VM-7 | AC-7.1~7.4（onDidChange） | 代码审查 | `HasOnDidChange` 副作用、will/did 时序、`ForceTriggerAvoidOnCaretChange` |
| VM-8 | AC-8.1~8.4（onSelect） | 代码审查 | `GetSpansInfo` 构造、`resultObjects` 空保护、多触发路径 |
| VM-9 | AC-9.1~9.7（onSelectionChange） | 代码审查 | 四层守卫（焦点/负值/闪烁/去重）、`lastSelectionRange_` 去重、多触发路径 |

## API 变更分析

> 本特性为存量规格补录，记录各 API 的引入版本和当前签名。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `onReady(callback: VoidCallback \| undefined)` | Public (@since 10) | `VoidCallback` 无参回调或 `undefined` | `this` | N/A | 组件首次布局完成就绪回调 | AC-1.1~1.3 |
| `onEditingChange(callback: Callback<boolean, void> \| undefined)` | Public (@since 12) | `Callback<boolean>` 布尔回调或 `undefined` | `this` | N/A | 编辑态切换回调 | AC-2.1~2.5 |
| `onSubmit(callback: SubmitCallback \| undefined)` | Public (@since 12) | `SubmitCallback = (enterKey, event) => void` 或 `undefined` | `this` | N/A | 回车提交回调 | AC-3.1~3.4 |
| `aboutToDelete(callback: Callback<RichEditorDeleteValue, boolean> \| undefined)` | Public (@since 10) | `Callback<RichEditorDeleteValue, boolean>` 拦截回调或 `undefined` | `this` | N/A | 删除前拦截回调 | AC-4.1~4.5 |
| `onDeleteComplete(callback: VoidCallback \| undefined)` | Public (@since 10) | `VoidCallback` 无参回调或 `undefined` | `this` | N/A | 删除完成回调 | AC-5.1~5.3 |
| `onWillChange(callback: Callback<RichEditorChangeValue, boolean> \| undefined)` | Public (@since 12) | `Callback<RichEditorChangeValue, boolean>` 拦截回调或 `undefined` | `this` | N/A | 内容变更前拦截回调 | AC-6.1~6.5 |
| `onDidChange(callback: OnDidChangeCallback \| undefined)` | Public (@since 12) | `OnDidChangeCallback` 变更完成回调或 `undefined` | `this` | N/A | 内容变更完成回调 | AC-7.1~7.4 |
| `onSelect(callback: Callback<RichEditorSelection, void> \| undefined)` | Public (@since 10) | `Callback<RichEditorSelection, void>` 选区回调或 `undefined` | `this` | N/A | 选区变化回调（含 spans） | AC-8.1~8.4 |
| `onSelectionChange(callback: Callback<RichEditorRange, void> \| undefined)` | Public (@since 12) | `Callback<RichEditorRange, void>` 范围回调或 `undefined` | `this` | N/A | 选区范围变化回调（轻量） | AC-9.1~9.7 |

### 变更/废弃 API

无。

## 接口规格

> 所有 API 均为 `RichEditorAttribute` 上的事件方法，返回 `this` 链式调用，开放范围 Public，无错误码。

| API | 函数签名 | 参数约束 | 关联 AC |
|-----|----------|----------|---------|
| onReady | `onReady(callback: VoidCallback \| undefined): this` | undefined 时清空回调；仅首次布局完成触发一次 | AC-1.1~1.3 |
| onEditingChange | `onEditingChange(callback: Callback<boolean, void> \| undefined): this` | 参数 isEditing=true 进入/false 退出；状态去重 | AC-2.1~2.5 |
| onSubmit | `onSubmit(callback: SubmitCallback \| undefined): this` | `SubmitCallback = (enterKey: EnterKeyType, event: SubmitEvent) => void`；event 可设 KeepEditable 拦截退出 | AC-3.1~3.4 |
| aboutToDelete | `aboutToDelete(callback: Callback<RichEditorDeleteValue, boolean> \| undefined): this` | 返回 true 放行/false 拦截；预览输入态覆盖拦截 | AC-4.1~4.5 |
| onDeleteComplete | `onDeleteComplete(callback: VoidCallback \| undefined): this` | 仅删除实际执行后触发；含 UiSession 上报 | AC-5.1~5.3 |
| onWillChange | `onWillChange(callback: Callback<RichEditorChangeValue, boolean> \| undefined): this` | 返回 true 放行/false 拦截；含 rangeBefore/replacedSpans/changeReason | AC-6.1~6.5 |
| onDidChange | `onDidChange(callback: OnDidChangeCallback \| undefined): this` | 变更完成后触发；`HasOnDidChange` 有 `SetContentChange(true)` 副作用 | AC-7.1~7.4 |
| onSelect | `onSelect(callback: Callback<RichEditorSelection, void> \| undefined): this` | 携带完整 `selection: [start, end]` + `spans` 数组；空选区不触发 | AC-8.1~8.4 |
| onSelectionChange | `onSelectionChange(callback: Callback<RichEditorRange, void> \| undefined): this` | 携带轻量 `{start?, end?}`；四层守卫去重，高频触发 | AC-9.1~9.7 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — `onReady`/`aboutToDelete`/`onDeleteComplete`/`onSelect` 自 API 10+ 引入；`onEditingChange`/`onSubmit`/`onWillChange`/`onDidChange`/`onSelectionChange` 自 API 12+ 引入
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（onReady/aboutToDelete/onDeleteComplete/onSelect），API 12（onEditingChange/onSubmit/onWillChange/onDidChange/onSelectionChange）
- **API 版本号策略:** 各事件按引入版本标注 `@since`；拦截型回调（aboutToDelete/onWillChange）返回 boolean 控制放行

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| onReady 一次性触发 | `isRichEditorInit_` 守卫确保仅首次布局完成触发，不可重复 | AC-1.1, AC-1.2 |
| onEditingChange 状态去重 | `isEditing_ != isEditing` 守卫避免重复触发同态切换 | AC-2.4 |
| onSubmit 拦截与换行 | `KeepEditable` 控制是否退出编辑；`NEW_LINE` 默认插入换行且不退出 | AC-3.3, AC-3.4 |
| aboutToDelete 预览输入态覆盖与重算 | `doDelete = allowDelete \|\| IsPreviewTextInputting()`；返回后 `ResetRichEditorDeleteSpans` + `CalcDeleteValueObj` 重算 | AC-4.4, AC-4.5 |
| onWillChange/onDidChange will/did 时序与双重守卫 | will 在变更前拦截返回布尔，did 在变更后通知；`BeforeChangeText`/`AfterContentChange` 配对；`!HasOnWillChange() && !HasOnDidChange()` 直接返回 true | AC-6.1, AC-6.3, AC-7.1 |
| onDidChange 副作用 | `HasOnDidChange` 调用 `SetContentChange(true)` 即使未注册回调也执行 | AC-7.4 |
| onSelect 空选区保护 / onSelectionChange 四层守卫 | `resultObjects` 为空不触发；焦点/负值/闪烁单句柄/范围去重四层过滤降低高频回调噪声 | AC-8.3, AC-9.2~9.5 |
| 事件不涉及 IME/剪贴板 | 本规格仅覆盖生命周期/删除/变更/选区事件，IME 输入见 Feat-06，剪贴板见 Feat-09 | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可测试性 | 拦截型回调（aboutToDelete/onWillChange）返回值可通过返回 false 验证拦截效果 | 代码审查 | `rich_editor_event_hub.cpp:81-88, 140-147` |
| 可靠性 | 所有 Fire 方法对回调空值做 CHECK 保护，未注册时不崩溃 | 代码审查 | `rich_editor_event_hub.cpp:30, 83, 96, 130, 142, 161, 278, 290` |
| 性能 | onSelectionChange 四层守卫去重降低高频回调开销 | 代码审查 | `rich_editor_pattern.cpp:2556-2572` |

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
| 无障碍 | 是 | 选区事件（onSelect/onSelectionChange）为无障碍服务提供选区变化通知 | AC-8.1~8.4, AC-9.1~9.7 |
| 大字体 | N/A | 事件回调不涉及大字体适配 | — |
| 深色模式 | N/A | 事件回调不涉及颜色/主题 | — |
| 多窗口/分屏 | 是 | 失焦（WINDOW_BLUR 除外）触发 onEditingChange(false)，窗口失焦不触发 | AC-2.2 |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | 事件分 API 10/12 两批引入，需关注版本兼容性 | AC-1.1~9.7 |
| 生态兼容 | N/A | — | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RichEditor 编辑生命周期与内容变化事件
  作为应用开发者
  我想要监听 RichEditor 的编辑生命周期与内容变化
  以便在关键节点执行业务逻辑

  Scenario: 组件就绪一次性触发与编辑态去重
    Given RichEditor 组件 isRichEditorInit_ 为 false 且 isEditing_ 为 false
    When 首次 OnDirtyLayoutWrapperSwap 执行
    Then 调用 FireOnReady 触发 onReady 回调并设置 isRichEditorInit_ = true
    When 单击获焦调用 HandleOnEditChanged(true)
    Then 通过 isEditing_ != isEditing 守卫并触发 FireOnEditingChange(true)
    When 再次调用 HandleOnEditChanged(true)
    Then 守卫直接返回不触发

  Scenario: 删除拦截与预览输入态覆盖
    Given RichEditor 组件注册了 aboutToDelete 回调
    When DoDeleteActions 执行且回调返回 false
    Then 若非预览输入态 doDelete 为 false 不执行删除
    When IsPreviewTextInputting 为 true
    Then doDelete 为 true 仍执行删除并触发 onDeleteComplete

  Scenario: 内容变更 will/did 时序
    Given RichEditor 组件注册了 onWillChange 和 onDidChange
    When 内容变更前调用 BeforeChangeText
    Then 构造 RichEditorChangeValue 调用 FireOnWillChange 返回 true 放行
    When 变更执行后调用 AfterContentChange
    Then HasOnDidChange 为 true 时调用 FireOnDidChange

  Scenario: 选区范围四层守卫去重
    Given RichEditor 组件 lastSelectionRange_ 为 {-1, -1}
    When FireOnSelectionChange(2, 5) 被调用且有焦点
    Then 通过焦点/负值/闪烁/去重四层守卫并触发 onSelectionChange
    When 再次 FireOnSelectionChange(2, 5)
    Then range == lastSelectionRange_ 去重守卫直接返回
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（编辑生命周期与内容变化事件，不含 IME 输入、剪贴板、布局算法、渲染细节）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern FireOnReady isRichEditorInit_ HandleOnEditChanged isEditing_ FireOnEditingChange PerformAction FireOnSubmit KeepEditable"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern DoDeleteActions FireAboutToDelete IsPreviewTextInputting FireOnDeleteComplete BeforeChangeText AfterContentChange FireOnWillChange FireOnDidChange"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern FireOnSelect GetSpansInfo FireOnSelectionChange SelectionRangeInfo lastSelectionRange_ guard dedup RichEditorChangeValue RichEditorDeleteValue"
```

**关键文档：**
- SDK 静态版声明: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets`
- 事件中心声明: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_event_hub.h`
- 事件中心实现: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_event_hub.cpp`
- Pattern 事件触发: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.cpp`
- Pattern 成员变量: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.h`
- 变更值类型定义: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_value.h`
- 选区范围类型: `frameworks/core/components_ng/pattern/text/selection_info.h`
- TextChangeReason 枚举: `frameworks/core/components/common/layout/constants.h`
