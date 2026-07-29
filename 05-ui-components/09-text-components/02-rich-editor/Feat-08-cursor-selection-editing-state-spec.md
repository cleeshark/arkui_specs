# 特性规格

> Func-05-09-02-Feat-08 光标选择与编辑状态控制：固化 RichEditorBaseController（双模式共享基类）暴露的光标位置、选区、编辑状态、预输入样式与布局查询共 14 个控制器方法的行为规格。这些方法在旧框架模式（RichEditorController）与属性字符串模式（RichEditorStyledStringController）下共享同一实现路径，仅 `getSelection()` 因模式差异返回不同类型。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 光标选择与编辑状态控制 (Cursor Selection & Editing State Control) |
| 特性编号 | Func-05-09-02-Feat-08 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10+ 至 API 20+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐光标位置管理规格 | `getCaretOffset`/`setCaretOffset`/`getCaretRect` 行为，含预输入态拦截与无焦点/无光标回退 |
| MODIFIED | 补齐选区管理规格 | `setSelection`/`getSelection`/`closeSelectionMenu` 行为，含双模式返回类型差异与 SelectionOptions 策略 |
| MODIFIED | 补齐编辑状态控制规格 | `isEditing`/`stopEditing` 行为，含焦点校验与失焦路径 |
| MODIFIED | 补齐可视区域滚动规格 | `scrollToVisible` 行为，含区间默认值与 clamp 约束 |
| MODIFIED | 补齐预输入样式规格 | `getTypingStyle`/`setTypingStyle`/`setTypingParagraphStyle` 行为，含重置判定与光标样式联动 |
| MODIFIED | 补齐布局与预览查询规格 | `getLayoutManager`/`getPreviewText` 行为，含 LayoutInfoInterface 委托与 PreviewTextRecord 读取 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/09-text-components/02-rich-editor/design.md` | 已创建 |

---

## 用户故事

### US-1: 光标位置管理（getCaretOffset / setCaretOffset / getCaretRect）

**作为** 应用开发者,
**我想要** 通过控制器读取、设置光标位置并获取光标矩形,
**以便** 精确控制编辑光标在 RichEditor 文本中的位置与可视性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `getCaretOffset()` THEN `RichEditorBaseController::GetCaretOffset` 委托 `RichEditorPattern::GetCaretPosition` 返回成员 `caretPosition_`（默认 0），pattern 为空时返回 -1（`rich_editor_base_controller.cpp:50-57`, `rich_editor_pattern.cpp:2397-2401`, `rich_editor_pattern.h:1357`） | 正常 |
| AC-1.2 | WHEN 调用 `setCaretOffset(offset)` 且处于预输入态（`IsPreviewTextInputting()` 为 true）THEN `SetCaretOffset` 直接返回 false 不移动光标（`rich_editor_pattern.cpp:2405-2408`） | 边界 |
| AC-1.3 | WHEN 调用 `setCaretOffset(offset)` 且非预输入态 THEN 依次执行 `AdjustSelector(HandleType::SECOND)` → `SetCaretPosition(caretPosition)` → 若已获焦点则 `isCursorAlwaysDisplayed_=false` 并 `StartTwinkling()` → `CloseSelectOverlay()` → `ResetSelection()`，返回 SetCaretPosition 结果（`rich_editor_pattern.cpp:2409-2424`） | 正常 |
| AC-1.4 | WHEN `setCaretOffset` 执行完成 THEN 控制器层额外调用 `ForceTriggerAvoidOnCaretChange(true)` 以在避让模式下移动内容（`rich_editor_base_controller.cpp:71`, `rich_editor_pattern.cpp:14974-14980`） | 正常 |
| AC-1.5 | WHEN 调用 `getCaretRect()` THEN 委托 `RichEditorPattern::GetCaretRelativeRect`，若 `caretTwinkling_` 为 false 返回 `RectF(-1,-1,-1,-1)`，否则由 `CalculateCaretOffsetAndHeight()` 与 overlay 光标宽度组合返回（`rich_editor_base_controller.cpp:59-64`, `rich_editor_pattern.cpp:14165-14172`, `rich_editor_pattern.h:1344`） | 正常 |
| AC-1.6 | WHEN `getCaretRect` 中 overlay 不存在 THEN 返回 `RectF(0,0,0,0)`（`rich_editor_pattern.cpp:14169`） | 边界 |

### US-2: 选区管理（setSelection / getSelection / closeSelectionMenu）

**作为** 应用开发者,
**我想要** 设置文本选区、获取当前选区、关闭选择菜单,
**以便** 编程化控制文本选择范围与选择菜单的显隐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `setSelection(start, end, options?)` 且组件无焦点 THEN `CHECK_NULL_VOID(HasFocus())` 直接返回，不执行选区操作（`rich_editor_pattern.cpp:10590, 10593`） | 边界 |
| AC-2.2 | WHEN 处于预输入态调用 `setSelection` THEN 打印警告并直接返回（`rich_editor_pattern.cpp:10594-10597`） | 边界 |
| AC-2.3 | WHEN `start == -1 && end == -1` THEN 自动设为 `start=0, end=GetTextContentLength()`（全选），否则 `std::clamp` 到 `[0, GetTextContentLength()]`（`rich_editor_pattern.cpp:10598-10604`） | 正常 |
| AC-2.4 | WHEN 选区有效且 `start != end` THEN `StopTwinkling()`、若起止变化则 `FireOnSelect` 与 `ReportSelectionChangeEvent`，随后 `SetCaretPosition`、`MoveCaretToContentRect`、`CalculateHandleOffsetAndShowOverlay`、`UpdateSelectionInfo`、`ProcessOverlayOnSetSelection(options)`、`MarkContentNodeForRender`（`rich_editor_pattern.cpp:10608-10623`） | 正常 |
| AC-2.5 | WHEN `options.handlePolicy == SHOW` THEN `ProcessOverlay({animation=true})` 显示句柄；`HIDE` 则 `CloseSelectOverlay()`；`DEFAULT` 继续后续菜单策略（`rich_editor_pattern.cpp:10625-10632`） | 正常 |
| AC-2.6 | WHEN `options.menuPolicy == HIDE` 且非鼠标场景 THEN `ProcessOverlay({menuIsShow=false, animation=true})` 隐藏菜单；`SHOW` 则强制 `ProcessOverlay({animation=true})` 显示菜单；`DEFAULT` 沿用当前可见性（`rich_editor_pattern.cpp:10636-10652`） | 正常 |
| AC-2.7 | WHEN 旧框架模式调用 `getSelection()` THEN `RichEditorController::GetSelectionSpansInfo` 返回 `SelectionInfo`（对应 `RichEditorSelection`）：读取 `GetTextSelector()` 起止，若 `start==end` 回退到 `caretPosition_`，调用 `GetSpansInfo(GETSPANS)`（`rich_editor_controller.cpp:82-97`） | 正常 |
| AC-2.8 | WHEN 属性字符串模式调用 `getSelection()` THEN `RichEditorStyledStringController::GetSelection` 返回 `SelectionRangeInfo`（对应 `RichEditorRange`）：同样读取选择器起止并在无选区时回退到光标位置，仅返回 `(start, end)` 区间（`rich_editor_styled_string_controller.cpp:44-58`） | 正常 |
| AC-2.9 | WHEN 无选区（`start==end`）调用 `getSelection` THEN 两种模式均回退到 `GetCaretPosition()` 作为 start/end（`rich_editor_controller.cpp:89-92`, `rich_editor_styled_string_controller.cpp:51-54`） | 边界 |
| AC-2.10 | WHEN 调用 `closeSelectionMenu()` THEN 委托 `RichEditorPattern::CloseSelectionMenu` → `CloseSelectOverlay` → `selectOverlay_->CloseOverlay(true, CloseReason::CLOSE_REASON_NORMAL)`（`rich_editor_base_controller.cpp:108-113`, `rich_editor_pattern.cpp:10119-10124, 10132-10137`） | 正常 |

### US-3: 编辑状态控制（isEditing / stopEditing）

**作为** 应用开发者,
**我想要** 查询编辑状态并主动停止编辑,
**以便** 控制组件的聚焦与失焦以配合输入法与业务流程。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `isEditing()` THEN 委托 `RichEditorPattern::IsEditing` 返回成员 `isEditing_`（默认 false），pattern 为空返回 false（`rich_editor_base_controller.cpp:115-120`, `rich_editor_pattern.cpp:12111-12114`, `rich_editor_pattern.h:1414`） | 正常 |
| AC-3.2 | WHEN 调用 `stopEditing()` 且组件无焦点 THEN `CHECK_NULL_VOID(HasFocus())` 直接返回，不执行失焦（`rich_editor_pattern.cpp:12253`） | 边界 |
| AC-3.3 | WHEN 调用 `stopEditing()` 且组件有焦点 THEN 调用 `FocusHub::LostFocusToViewRoot()` 令组件失焦以阻止物理键盘继续输入（`rich_editor_pattern.cpp:12251-12257`） | 正常 |
| AC-3.4 | WHEN `HandleOnEditChanged(false)` 触发 THEN 置 `isEditing_=false` 并 `FireOnEditingChange(false)`，若 `CanStartAITask()` 启动 AI 任务，否则 `MarkContentNodeForRender`（`rich_editor_pattern.cpp:12116-12138`） | 正常 |

### US-4: 可视区域滚动（scrollToVisible）

**作为** 应用开发者,
**我想要** 将指定文本区间滚动到可视区域,
**以便** 在长文本场景下定位到关注内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `scrollToVisible(range?)` THEN 取 `maxLen=GetTextContentLength()`，`rangeStart=clamp(start.value_or(0),0,maxLen)`，`rangeEnd=clamp(end.value_or(maxLen),0,maxLen)`，委托 `scrollController_->ScrollToVisible(rangeStart, rangeEnd)`（`rich_editor_base_controller.cpp:129-134`, `rich_editor_pattern.cpp:10943-10950`, `rich_editor_pattern.h:981`） | 正常 |
| AC-4.2 | WHEN 未传 `range`（start/end 均为 nullopt）THEN 默认 `start=0, end=maxLen` 即滚动覆盖全文区间（`rich_editor_pattern.cpp:10946-10947`） | 边界 |
| AC-4.3 | WHEN 传入负数 start 或超出文本长度的 end THEN 经 `std::clamp` 收敛到 `[0, maxLen]`（`rich_editor_pattern.cpp:10946-10947`） | 边界 |

### US-5: 预输入样式（getTypingStyle / setTypingStyle / setTypingParagraphStyle）

**作为** 应用开发者,
**我想要** 预设后续输入文本的字符与段落样式,
**以便** 在用户键入前确定下一段文本的视觉样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `getTypingStyle()` THEN 委托 `RichEditorPattern::GetTypingStyle` 返回 `styleManager_->GetTypingFontStyle()`（`std::optional<UpdateSpanStyle>`），pattern 为空返回空 optional（`rich_editor_base_controller.cpp:84-89`, `rich_editor_pattern.cpp:2675-2678`） | 正常 |
| AC-5.2 | WHEN 调用 `setTypingStyle(value)` 且当前已有 typing 字体样式且新值为空 THEN `isReset=true`，`styleManager_->SetTypingStyle` 后调用 `UpdateCaretStyleByTypingStyle(true)` 重置光标样式（`rich_editor_pattern.cpp:2647-2650`） | 边界 |
| AC-5.3 | WHEN 调用 `setTypingStyle(value)` 传入有效样式 THEN `styleManager_->SetTypingStyle(typingStyle, textStyle)` 后 `UpdateCaretStyleByTypingStyle(isReset)`，控制器层追加 `ForceTriggerAvoidOnCaretChange()`（`rich_editor_base_controller.cpp:75-82`, `rich_editor_pattern.cpp:2643-2650`） | 正常 |
| AC-5.4 | WHEN 调用 `setTypingParagraphStyle(style)` THEN `isReset = HasTypingParagraphStyle() && !typingParagraphStyle.has_value()`，`styleManager_->SetTypingParagraphStyle` 后 `UpdateCaretStyleByTypingStyle(isReset)`，控制器层追加 `ForceTriggerAvoidOnCaretChange()`（`rich_editor_base_controller.cpp:91-97`, `rich_editor_pattern.cpp:2662-2668`） | 正常 |
| AC-5.5 | WHEN `setTypingParagraphStyle(undefined)` 传入空值且当前已有段落样式 THEN 触发 `isReset=true` 重置段落样式与光标样式（`rich_editor_pattern.cpp:2665-2667`） | 边界 |

### US-6: 布局与预览查询（getLayoutManager / getPreviewText）

**作为** 应用开发者,
**我想要** 获取布局管理器与预览文本信息,
**以便** 查询段落/光标几何信息并读取输入法预输入内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `getLayoutManager()` THEN 控制器 `GetLayoutInfoInterface` 委托 `richEditorPattern->GetLayoutInfoInterface()` 返回 `WeakPtr<LayoutInfoInterface>`，pattern 为空返回 nullptr（`rich_editor_base_controller.cpp:43-48`） | 正常 |
| AC-6.2 | WHEN 调用 `getPreviewText()` THEN 委托 `RichEditorPattern::GetPreviewTextInfo`：若 `previewTextRecord_.previewContent` 非空则填充 `info.value=previewContent` 与 `info.offset=startOffset`，否则返回默认空 `PreviewTextInfo`（`rich_editor_base_controller.cpp:152-157`, `rich_editor_pattern.cpp:6613-6621`, `rich_editor_pattern.h:1425`） | 正常 |
| AC-6.3 | WHEN 无预输入内容时调用 `getPreviewText()` THEN 返回默认构造的 `PreviewTextInfo`（value 与 offset 均为默认值）（`rich_editor_pattern.cpp:6615-6620`） | 边界 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1, R-2, R-3 | N/A（存量） | 代码审查 | 见 AC 内 file:line 引用 |
| AC-2.1~2.10 | R-4, R-5, R-6, R-7 | N/A | 代码审查 | 见 AC 内 file:line 引用 |
| AC-3.1~3.4 | R-8, R-9 | N/A | 代码审查 | 见 AC 内 file:line 引用 |
| AC-4.1~4.3 | R-10 | N/A | 代码审查 | 见 AC 内 file:line 引用 |
| AC-5.1~5.5 | R-11, R-12 | N/A | 代码审查 | 见 AC 内 file:line 引用 |
| AC-6.1~6.3 | R-13, R-14 | N/A | 代码审查 | 见 AC 内 file:line 引用 |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `getCaretOffset()` | 返回 `caretPosition_`（默认 0），pattern 空返回 -1 | int32_t，初始 0（`rich_editor_pattern.h:1357`） | AC-1.1 |
| R-2 | 行为 | `setCaretOffset` 非预输入态 | AdjustSelector → SetCaretPosition → StartTwinkling → CloseSelectOverlay → ResetSelection，控制器追加 ForceTriggerAvoidOnCaretChange(true) | 预输入态返回 false（`rich_editor_pattern.cpp:2405-2408`） | AC-1.2~1.4 |
| R-3 | 行为 | 调用 `getCaretRect()` | caretTwinkling_ false 返回 (-1,-1,-1,-1)，否则组合 offset/height/width | overlay 不存在返回 (0,0,0,0)（`rich_editor_pattern.cpp:14169`） | AC-1.5, AC-1.6 |
| R-4 | 边界 | `setSelection` 无焦点或预输入态 | 直接返回 | CHECK_NULL_VOID(HasFocus())（`rich_editor_pattern.cpp:10593`） | AC-2.1, AC-2.2 |
| R-5 | 行为 | `setSelection` 正常调用 | -1 全选，否则 clamp；UpdateSelector 后 FireOnSelect + ProcessOverlayOnSetSelection | SelectionOptions 含 menuPolicy/handlePolicy/forceShowHandle（`text_field_model.h:204-208`） | AC-2.3~2.6 |
| R-6 | 行为 | 旧框架模式 `getSelection()` | 返回 SelectionInfo（RichEditorSelection），无选区回退 caretPosition | GetSpansInfo(GETSPANS) 构造（`rich_editor_controller.cpp:94`） | AC-2.7, AC-2.9 |
| R-7 | 行为 | 属性字符串模式 `getSelection()` | 返回 SelectionRangeInfo（RichEditorRange），仅 (start,end)，无选区回退 caretPosition | C-API 同路径（`rich_editor_model_ng.cpp:1471-1483`） | AC-2.8, AC-2.9 |
| R-8 | 行为 | 调用 `isEditing()` | 返回 `isEditing_`（默认 false） | bool，初始 false（`rich_editor_pattern.h:1414`） | AC-3.1 |
| R-9 | 行为 | 调用 `stopEditing()` | 有焦点 LostFocusToViewRoot 失焦，触发 HandleOnEditChanged(false) | 无焦点直接返回（`rich_editor_pattern.cpp:12253`） | AC-3.2~3.4 |
| R-10 | 行为 | 调用 `scrollToVisible(range?)` | start 默认 0、end 默认 maxLen，均 clamp，委托 scrollController_ | RefPtr<RichEditorScrollController>（`rich_editor_pattern.h:981`） | AC-4.1~4.3 |
| R-11 | 行为 | 调用 `getTypingStyle()` | 返回 styleManager_->GetTypingFontStyle() | pattern 空返回空 optional | AC-5.1 |
| R-12 | 行为 | `setTypingStyle`/`setTypingParagraphStyle` | isReset 判定 → styleManager 写入 → UpdateCaretStyleByTypingStyle → ForceTriggerAvoidOnCaretChange() | isMoveContent=false（无参） | AC-5.2~5.5 |
| R-13 | 行为 | 调用 `getLayoutManager()` | 委托 pattern->GetLayoutInfoInterface() 返回 WeakPtr<LayoutInfoInterface> | pattern 空返回 nullptr | AC-6.1 |
| R-14 | 行为 | 调用 `getPreviewText()` | 读取 previewTextRecord_，非空填充 value/offset，否则返回默认 PreviewTextInfo | PreviewTextRecord（`rich_editor_pattern.h:1425`） | AC-6.2, AC-6.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.6（光标位置管理） | 代码审查 | caretPosition_ 存储、预输入态拦截、ForceTriggerAvoidOnCaretChange(true)、GetCaretRelativeRect 回退 |
| VM-2 | AC-2.1~2.10（选区管理） | 代码审查 | 焦点校验、clamp、ProcessOverlayOnSetSelection 策略、双模式 getSelection 返回类型差异 |
| VM-3 | AC-3.1~3.4（编辑状态） | 代码审查 | isEditing_ 存储、LostFocusToViewRoot、HandleOnEditChanged 链路 |
| VM-4 | AC-4.1~4.3（可视区域滚动） | 代码审查 | 默认值、clamp、scrollController_ 委托 |
| VM-5 | AC-5.1~5.5（预输入样式） | 代码审查 | styleManager_ 委托、isReset 判定、UpdateCaretStyleByTypingStyle 联动 |
| VM-6 | AC-6.1~6.3（布局与预览查询） | 代码审查 | LayoutInfoInterface 委托、PreviewTextRecord 读取与空值回退 |

## API 变更分析

> 本特性为存量规格补录，记录各控制器方法的引入版本与当前签名。所有方法均属于 `RichEditorBaseController`，在旧框架模式与属性字符串模式下共享实现。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `getCaretOffset(): int32` | Public (@since 10) | 无 | `int32` 光标位置，pattern 为空返回 -1 | N/A | 获取光标位置 | AC-1.1 |
| `setCaretOffset(offset: int32): boolean` | Public (@since 10) | `int32` 光标偏移 | `boolean` 是否成功 | N/A | 设置光标位置 | AC-1.2~1.4 |
| `getCaretRect(): RectResult` | Public (@since 18) | 无 | `RectResult` 光标矩形 | N/A | 获取光标矩形 | AC-1.5, AC-1.6 |
| `setSelection(selectionStart: int32, selectionEnd: int32, options?: SelectionOptions): void` | Public (@since 11) | `int32` 起止，可选 `SelectionOptions` | `void` | N/A | 设置选区 | AC-2.1~2.6 |
| `getSelection(): RichEditorSelection \| RichEditorRange` | Public (@since 10) | 无 | 旧模式 `RichEditorSelection`，属性字符串模式 `RichEditorRange` | N/A | 获取当前选区 | AC-2.7~2.9 |
| `closeSelectionMenu(): void` | Public (@since 10) | 无 | `void` | N/A | 关闭选择菜单 | AC-2.10 |
| `isEditing(): boolean` | Public (@since 10) | 无 | `boolean` 编辑状态 | N/A | 查询编辑状态 | AC-3.1 |
| `stopEditing(): void` | Public (@since 10) | 无 | `void` | N/A | 停止编辑 | AC-3.2~3.4 |
| `scrollToVisible(range?: TextRange): void` | Public | 可选 `TextRange` 区间 | `void` | N/A | 滚动到可视区域 | AC-4.1~4.3 |
| `getTypingStyle(): RichEditorTextStyle` | Public (@since 11) | 无 | `RichEditorTextStyle` 预输入样式 | N/A | 获取预输入样式 | AC-5.1 |
| `setTypingStyle(value: RichEditorTextStyle): void` | Public (@since 11) | `RichEditorTextStyle` 样式 | `void` | N/A | 设置预输入样式 | AC-5.2, AC-5.3 |
| `setTypingParagraphStyle(style: RichEditorParagraphStyle \| undefined): void` | Public (@since 20) | `RichEditorParagraphStyle` 或 `undefined` | `void` | N/A | 设置预输入段落样式 | AC-5.4, AC-5.5 |
| `getLayoutManager(): LayoutManager` | Public (@since 12) | 无 | `LayoutManager` 布局管理器 | N/A | 获取布局管理器 | AC-6.1 |
| `getPreviewText(): PreviewText` | Public | 无 | `PreviewText` 预览文本 | N/A | 获取预览文本 | AC-6.2, AC-6.3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

> 行为详见关联 AC；下表仅列签名与参数约束，避免与 AC 重复。

| 接口 | 签名 | 参数约束 | 关联 AC |
|------|------|----------|---------|
| getCaretOffset | `(): int32` | 无参；返回 `caretPosition_`（默认 0），pattern 空返回 -1 | AC-1.1 |
| setCaretOffset | `(offset: int32): boolean` | offset 必填；预输入态返回 false；经 AdjustSelector 调整 | AC-1.2~1.4 |
| getCaretRect | `(): RectResult` | 无参；`caretTwinkling_` false 返回 `(-1,-1,-1,-1)`；API 18+ | AC-1.5, AC-1.6 |
| setSelection | `(selectionStart: int32, selectionEnd: int32, options?: SelectionOptions): void` | start/end 必填，-1 触发全选，否则 clamp [0,textLength]；options 默认 menuPolicy/handlePolicy=DEFAULT, forceShowHandle=false | AC-2.1~2.6 |
| getSelection | `(): RichEditorSelection \| RichEditorRange` | 无参；旧模式返回 RichEditorSelection，属性字符串模式返回 RichEditorRange | AC-2.7~2.9 |
| closeSelectionMenu | `(): void` | 无参 | AC-2.10 |
| isEditing | `(): boolean` | 无参；返回 `isEditing_`（默认 false） | AC-3.1 |
| stopEditing | `(): void` | 无参；无焦点直接返回 | AC-3.2~3.4 |
| scrollToVisible | `(range?: TextRange): void` | range 可选，默认 start=0/end=textLength，均 clamp [0,textLength] | AC-4.1~4.3 |
| getTypingStyle | `(): RichEditorTextStyle` | 无参；返回 `styleManager_->GetTypingFontStyle()` | AC-5.1 |
| setTypingStyle | `(value: RichEditorTextStyle): void` | value 必填 | AC-5.2, AC-5.3 |
| setTypingParagraphStyle | `(style: RichEditorParagraphStyle \| undefined): void` | style 可选，undefined 且当前有样式触发 isReset | AC-5.4, AC-5.5 |
| getLayoutManager | `(): LayoutManager` | 无参；API 12+ | AC-6.1 |
| getPreviewText | `(): PreviewText` | 无参；无内容返回默认 PreviewTextInfo | AC-6.2, AC-6.3 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — `getCaretOffset`/`setCaretOffset`/`getSelection`/`closeSelectionMenu`/`isEditing`/`stopEditing` 自 API 10+ 引入；`setSelection`/`getTypingStyle`/`setTypingStyle` 自 API 11+ 引入；`getLayoutManager` 自 API 12+ 引入；`getCaretRect` 自 API 18+ 引入；`setTypingParagraphStyle` 自 API 20+ 引入；`scrollToVisible`/`getPreviewText` 随 RichEditor 控制器一同引入
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（多数方法），API 11（setSelection/getTypingStyle/setTypingStyle），API 12（getLayoutManager），API 18（getCaretRect），API 20（setTypingParagraphStyle）
- **API 版本号策略:** 各方法按引入版本标注 `@since`；`getSelection` 在 API 10 引入，属性字符串模式返回 `RichEditorRange` 的行为随属性字符串模式引入而生效

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双模式共享基类 | 所有 14 方法均定义于 `RichEditorBaseController`，委托 `RichEditorPattern` 实现；仅 `getSelection()` 因模式返回不同类型 | AC-2.7, AC-2.8 |
| 预输入态拦截 | `setCaretOffset` 与 `setSelection` 在 `IsPreviewTextInputting()` 为 true 时拒绝操作（返回 false 或直接返回） | AC-1.2, AC-2.2 |
| 焦点前置校验 | `setSelection` 与 `stopEditing` 均通过 `HasFocus()` 校验，无焦点直接返回 | AC-2.1, AC-3.2 |
| ForceTriggerAvoidOnCaretChange 联动 | `setCaretOffset`(isMoveContent=true)、`setSelection`/`setTypingStyle`/`setTypingParagraphStyle`(isMoveContent=false) 在控制器层追加调用，仅在 `UsingCaretAvoidMode()` 时生效 | AC-1.4, AC-5.3, AC-5.4 |
| SelectionOptions 策略 | `menuPolicy`(DEFAULT/HIDE/SHOW) 与 `handlePolicy`(DEFAULT/HIDE/SHOW) 及 `forceShowHandle` 共同决定 overlay 与菜单显隐 | AC-2.5, AC-2.6 |
| 选区 clamp 约束 | `setSelection` 与 `scrollToVisible` 的数值参数均经 `std::clamp` 收敛到 `[0, GetTextContentLength()]` | AC-2.3, AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可测试性 | 所有查询型方法（getCaretOffset/isEditing/getTypingStyle/getPreviewText）支持无副作用回读 | 代码审查 | `rich_editor_pattern.cpp:2397-2401, 12111-12114, 2675-2678, 6613-6621` |
| 可靠性 | pattern 为空时所有方法均有安全回退（-1/false/默认构造/nullptr） | 代码审查 | `rich_editor_base_controller.cpp:54, 62, 69, 87, 118, 155` |
| 安全性 | stopEditing 通过失焦阻止物理键盘继续输入 | 代码审查 | `rich_editor_pattern.cpp:12255-12256` |

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
| 无障碍 | 是 | 光标位置与选区 API 影响无障碍服务对编辑态的可访问性 | AC-1.1, AC-2.7~2.9 |
| 大字体 | N/A | 控制器方法不涉及大字体适配 | — |
| 深色模式 | N/A | 控制器方法不直接涉及颜色/主题 | — |
| 多窗口/分屏 | 是 | ForceTriggerAvoidOnCaretChange 在避让模式下影响多窗口光标避让 | AC-1.4, AC-5.3, AC-5.4 |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | 方法跨 API 10-20+ 引入，需关注版本兼容性与 @since 标注 | AC-1.1~6.3 |
| 生态兼容 | N/A | — | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（控制器层光标/选区/编辑状态/预输入样式/布局查询方法，不含 Span 增删、渲染细节、键盘交互）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditorBaseController GetCaretOffset SetCaretOffset GetCaretRect delegation to RichEditorPattern and ForceTriggerAvoidOnCaretChange"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern SetSelection ProcessOverlayOnSetSelection HandlePolicy MenuPolicy SelectionOptions clamp and ResetOnInvalidSelection"
  - repo: "openharmony/ace_engine"
    query: "RichEditorController GetSelectionSpansInfo vs RichEditorStyledStringController GetSelection dual mode return type SelectionInfo SelectionRangeInfo"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern IsEditing StopEditing LostFocusToViewRoot HandleOnEditChanged isEditing_ state transition"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern SetTypingStyle SetTypingParagraphStyle styleManager_ UpdateCaretStyleByTypingStyle isReset"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern ScrollToVisible scrollController_ GetPreviewTextInfo previewTextRecord_ GetLayoutInfoInterface"
```

**关键文档：**
- 控制器基类声明: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_base_controller.h`
- 控制器基类实现: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_base_controller.cpp`
- Pattern 实现: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.cpp`
- 旧模式控制器: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_controller.cpp`
- 属性字符串控制器: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_styled_string_controller.cpp`
- 模型基类: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_model.h`
- SelectionOptions 定义: `frameworks/core/components_ng/pattern/text_field/text_field_model.h`
- 静态 ArkTS 桥接: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets`
