# 特性规格

> Func-05-09-02-Feat-02 Span 内容管理-增删改查与跨模式转换：固化 RichEditor 旧框架模式下 `RichEditorController` 的 Span 增删改查接口行为规格，覆盖 `addTextSpan`/`addImageSpan`/`addBuilderSpan`/`addSymbolSpan` 四类 Span 添加、`deleteSpans`/`deleteBackward` 删除、`getSpans`/`getParagraphs` 查询、`updateSpanStyle`/`updateParagraphStyle` 样式更新，以及 `fromStyledString`/`toStyledString` StyledString 双向转换共 12 个 API，重点记录各 Span 类型的字符长度约定、`maxLength` 截断、offset 边界 clamp、`OnWillChange` 事件触发、Undo/Redo 记录等关键实现细节。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Span 内容管理-增删改查与跨模式转换 (Span Content Management - CRUD & Cross-Mode Conversion) |
| 特性编号 | Func-05-09-02-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10+（增删改查），API 11+（addSymbolSpan），API 12+（StyledString 转换） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐四类 Span 添加接口行为规格 | 固化 `addTextSpan`/`addImageSpan`/`addBuilderSpan`/`addSymbolSpan` 的 offset clamp、maxLength 截断、Span 字符长度约定 |
| MODIFIED | 补齐 Span 删除接口行为规格 | 记录 `deleteSpans` 的范围 clamp 与 swap 逻辑、`deleteBackward` 的预览态跳过与委托路径 |
| MODIFIED | 补齐 Span 与段落查询接口行为规格 | 固化 `getSpans`/`getParagraphs` 的范围处理与段落分割逻辑 |
| MODIFIED | 补齐样式更新接口行为规格 | 记录 `updateSpanStyle` 的部分 Span 拆分更新与 `updateParagraphStyle` 的段落级样式应用 |
| MODIFIED | 补齐 StyledString 双向转换接口行为规格 | 固化 `fromStyledString`/`toStyledString` 的范围 clamp 与 SpanItem 转换逻辑 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/09-text-components/02-rich-editor/design.md` | 已创建 |
| Feat-01 规格 | `05-ui-components/09-text-components/02-rich-editor/Feat-01-component-init-dual-mode-spec.md` | Baselined |

---

## 用户故事

### US-1: 添加文本 Span

**作为** 应用开发者,
**我想要** 通过 `addTextSpan(content, options?)` 在 RichEditor 中插入文本内容,
**以便** 以编程方式构建富文本内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `addTextSpan(content, options)` THEN 控制器通过 `pattern_.Upgrade()` 委托给 `RichEditorPattern::AddTextSpan(options, TextChangeReason::CONTROLLER)`（`rich_editor_controller.cpp:27-32`） | 正常 |
| AC-1.2 | WHEN `GetTextContentLength() >= maxLength` THEN 返回 0，不执行添加（`rich_editor_pattern.cpp:1448-1451`） | 边界 |
| AC-1.3 | WHEN 文本追加后超出 maxLength THEN 调用 `CalculateTruncationLength` 截断至剩余可用长度，截断后长度为 0 则返回 -1（`rich_editor_pattern.cpp:1452-1456`） | 边界 |
| AC-1.4 | WHEN `options.offset` 有值 THEN offset 被 `std::clamp` 限制在 `[0, textContentLength]` 范围内（`rich_editor_pattern.cpp:1463-1466`） | 边界 |
| AC-1.5 | WHEN 添加成功 THEN 触发 `BeforeChangeText` 校验，记录 `OperationRecord`，调用 `AfterContentChange` 触发 `OnDidChange` 事件，返回 spanIndex（`rich_editor_pattern.cpp:1483-1492`） | 正常 |

### US-2: 添加图片 Span 与 Builder Span

**作为** 应用开发者,
**我想要** 通过 `addImageSpan` 和 `addBuilderSpan` 插入图片和自定义构建器内容,
**以便** 在富文本中嵌入多媒体和自定义 UI 组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `addImageSpan(value, options)` THEN 委托给 `RichEditorPattern::AddImageSpan(options, TextChangeReason::CONTROLLER)`（`rich_editor_controller.cpp:20-25`） | 正常 |
| AC-2.2 | WHEN 添加图片 Span THEN 创建 `ImageSpanNode`（tag=`V2::IMAGE_ETS_TAG`），Span 内容设为 `u" "`（1 字符），`placeholderCount_` 递增（`rich_editor_pattern.cpp:1100-1135`） | 正常 |
| AC-2.3 | WHEN 调用 `addBuilderSpan(value, options)` THEN 委托给 `RichEditorPattern::AddPlaceholderSpan(customNode, options, TextChangeReason::CONTROLLER)`（`rich_editor_controller.cpp:41-46`） | 正常 |
| AC-2.4 | WHEN 添加 Builder Span THEN 创建 `PlaceholderSpanNode`（tag=`V2::PLACEHOLDER_SPAN_ETS_TAG`），自定义节点挂载到 placeholder 节点，Span 内容设为 `u" "`（1 字符），`placeholderCount_` 递增（`rich_editor_pattern.cpp:1347-1373`） | 正常 |
| AC-2.5 | WHEN 图片/Builder Span 的 `options.offset` 有值 THEN insertIndex = `min(offset, textContentLength)`，并调用 `AdjustSelectorForSymbol`（`rich_editor_pattern.cpp:1106, 1355`） | 边界 |
| AC-2.6 | WHEN `GetTextContentLength() >= maxLength` THEN 图片/Builder Span 均返回 0，不执行添加（`rich_editor_pattern.cpp:1091-1094, 1338-1341`） | 边界 |

### US-3: 添加符号 Span

**作为** 应用开发者,
**我想要** 通过 `addSymbolSpan(value, options?)` (@since 11) 插入符号图标,
**以便** 在富文本中添加矢量符号内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `addSymbolSpan(value, options)` THEN 委托给 `RichEditorPattern::AddSymbolSpan(options, TextChangeReason::CONTROLLER)`（`rich_editor_controller.cpp:34-39`） | 正常 |
| AC-3.2 | WHEN 添加 Symbol Span THEN 创建 `SpanNode`（tag=`V2::SYMBOL_SPAN_ETS_TAG`），Span 内容设为 `u"  "`（2 字符），`spanItemType = SpanItemType::SYMBOL`（`rich_editor_pattern.cpp:1860, 1884-1885`） | 正常 |
| AC-3.3 | WHEN maxLength 校验 THEN 使用 `maxLength - 1` 作为阈值（SymbolSpan 占 2 字符），达到阈值返回 0（`rich_editor_pattern.cpp:1826-1829`） | 边界 |
| AC-3.4 | WHEN `options.offset` 有值 THEN offset 被 `std::clamp` 限制在 `[0, textContentLength]`（`rich_editor_pattern.cpp:1835-1838`） | 边界 |

### US-4: 删除 Span

**作为** 应用开发者,
**我想要** 通过 `deleteSpans` 按范围删除内容，或通过 `deleteBackward` 向后删除一个单位,
**以便** 以编程方式移除富文本内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `deleteSpans(value)` THEN 委托给 `RichEditorPattern::DeleteSpans(options, TextChangeReason::CONTROLLER)`（`rich_editor_controller.cpp:99-104`） | 正常 |
| AC-4.2 | WHEN `deleteSpans` 的 `start`/`end` 未指定 THEN start 默认为 0，end 默认为 `GetTextContentLength()`（`rich_editor_pattern.cpp:1985-1986`） | 正常 |
| AC-4.3 | WHEN `deleteSpans` 的 start > end THEN 自动交换 start 和 end；start 被 `max(0)` 限制，end 被 `min(length)` 限制；若 `start > length` 或 `end < 0` 或 `start == end` 则直接返回不操作（`rich_editor_pattern.cpp:1987-1995`） | 边界 |
| AC-4.4 | WHEN `deleteSpans` 执行 THEN 触发 `FireOnWillChange` 事件，校验通过后记录 `OperationRecord` 和 `UndoRedoRecord`，调用 `DeleteSpansOperation` 执行删除，最后 `AfterContentChange` 触发 `OnDidChange`（`rich_editor_pattern.cpp:2002-2016`） | 正常 |
| AC-4.5 | WHEN 调用 `deleteBackward()` THEN 委托给 `RichEditorBaseController::DeleteBackward()` → `pattern->DeleteBackwardFunction()`（`rich_editor_base_controller.cpp:136-141`） | 正常 |
| AC-4.6 | WHEN 预览态输入中（`IsPreviewTextInputting()`）调用 `deleteBackward` THEN 打印日志并直接返回，不执行删除（`rich_editor_pattern.cpp:2022-2025`）；非预览态调用 `HandleOnDelete(true)` → `DeleteBackward(1, TextChangeReason::INPUT)`（`rich_editor_pattern.cpp:7245-7252`） | 边界 |

### US-5: 查询 Span 与段落

**作为** 应用开发者,
**我想要** 通过 `getSpans` 查询指定范围内的 Span 信息，通过 `getParagraphs` 查询段落信息,
**以便** 获取富文本的结构化内容描述。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `getSpans(value)` THEN 委托给 `GetSpansInfo(start, end)` → `GetSpansInfoByRange(start, end)` → `GetSpansInfo(start, end, GetSpansMethod::GETSPANS)`（`rich_editor_controller.cpp:74-80`, `rich_editor_pattern.cpp:3161-3163`） | 正常 |
| AC-5.2 | WHEN `getSpans` 返回 THEN 返回 `SelectionInfo`，包含 `resultObjects` 列表，每个结果包含 `spanPosition`（spanIndex, spanRange）、`offsetInSpan`、`value`、`textStyle`/`imageStyle` 等字段（`rich_editor_abstract_span_result.h:25-437`） | 正常 |
| AC-5.3 | WHEN 调用 `getParagraphs(value)` THEN 委托给 `GetParagraphsInfo(start, end)` → `GetParagraphInfo(start, end)`（`rich_editor_controller.cpp:113-121`） | 正常 |
| AC-5.4 | WHEN 查询段落 THEN 按 `\n` 字符分割段落，每个 `ParagraphInfo` 包含 `textAlign`、`wordBreak`、`lineBreakStrategy`、`paragraphSpacing`、`leadingMargin`、`range` 等字段（`rich_editor_pattern.cpp:3426-3458`） | 正常 |
| AC-5.5 | WHEN `getParagraphs` 的 start == end THEN `GetParagraphNodes` 返回空列表，结果为空数组（`rich_editor_pattern.cpp:3482`） | 边界 |

### US-6: 更新 Span 样式与段落样式

**作为** 应用开发者,
**我想要** 通过 `updateSpanStyle` 更新指定范围内 Span 的样式，通过 `updateParagraphStyle` 更新段落样式,
**以便** 动态修改富文本的视觉呈现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `updateSpanStyle(value)` THEN 控制器对 start/end 进行 clamp（`max(0, start)`、`end > length` 则 `end = length`），若 `start > end` 则交换，若 `start == end` 或越界则直接返回（`rich_editor_controller.cpp:48-67`） | 边界 |
| AC-6.2 | WHEN `updateSpanStyle` 执行 THEN 遍历子节点，对完全包含在 `[start, end]` 范围内的 SpanNode 调用 `UpdateTextStyle`/`UpdateSymbolStyle`，对 ImageNode 调用 `UpdateImageStyle`；对部分重叠的 Span 调用 `TextSpanSplit` 拆分后更新（`rich_editor_pattern.cpp:2911-2944`） | 正常 |
| AC-6.3 | WHEN `updateSpanStyle` 入参为 `RichEditorUpdateTextSpanStyleOptions` THEN 应用 `textStyle` 字段；为 `RichEditorUpdateImageSpanStyleOptions` THEN 应用 `imageStyle` 字段；为 `RichEditorUpdateSymbolSpanStyleOptions` THEN 应用 `symbolStyle` 字段（`richEditor.ets:4438-4441, 1219-1228`） | 正常 |
| AC-6.4 | WHEN 调用 `updateParagraphStyle(value)` THEN 委托给 `RichEditorPattern::UpdateParagraphStyle(start, end, style)`，并调用 `ForceTriggerAvoidOnCaretChange()`（`rich_editor_controller.cpp:106-112`） | 正常 |
| AC-6.5 | WHEN `updateParagraphStyle` 执行 THEN 获取 `[start, end]` 范围内的段落 SpanNode 列表，对每个节点调用 `UpdateParagraphStyle(spanNode, style)`，更新 `textAlign`/`wordBreak`/`lineBreakStrategy`/`textVerticalAlign`/`textDirection`/`paragraphSpacing`/`gradient`/`leadingMargin` 等属性（`rich_editor_pattern.cpp:3554-3602`） | 正常 |
| AC-6.6 | WHEN 段落样式的某属性未指定 THEN 使用默认值：`TextAlign::START`、`WordBreak::BREAK_WORD`、`LineBreakStrategy::GREEDY`、`TextVerticalAlign::BASELINE`、`TextDirection::INHERIT`（`rich_editor_pattern.cpp:3573-3577`） | 边界 |

### US-7: StyledString 双向转换

**作为** 应用开发者,
**我想要** 通过 `toStyledString` 将 Span 内容转为 StyledString，通过 `fromStyledString` 将 StyledString 转为 Span 结果 (@since 12),
**以便** 在旧框架 Span 模型与 StyledString 数据模型之间进行跨模式数据转换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `toStyledString(value)` THEN 委托给 `RichEditorPattern::ToStyledString(start, end)`（`rich_editor_controller.cpp:123-128`） | 正常 |
| AC-7.2 | WHEN `toStyledString` 的 start/end 为 -1 THEN start 默认为 0，end 默认为 `GetTextContentLength()`；否则被 `std::clamp` 限制在 `[0, length]`；若 start > end 则交换（`rich_editor_pattern.cpp:5096-5101`） | 边界 |
| AC-7.3 | WHEN `toStyledString` 执行 THEN 创建 `SpanString`，若存在 AI 写适配器则走 `SetSubSpansWithAIWrite`，否则走 `SetSubSpans` 从 `spans_` 列表提取子 Span，最后 `SetSubMap` 设置样式映射（`rich_editor_pattern.cpp:5102-5110`） | 正常 |
| AC-7.4 | WHEN 调用 `fromStyledString(value)` THEN 委托给 `RichEditorPattern::FromStyledString(spanString)`，将 `spanStringBase` 动态转换为 `SpanString` 类型后传入（`rich_editor_controller.cpp:130-137`） | 正常 |
| AC-7.5 | WHEN `fromStyledString` 执行 THEN 遍历 SpanString 的 `spanItems`，对每个 SpanItem 调用 `GetSpanResultObject` 生成 `ResultObject`，ImageSpanItem 额外提取 `imageStyle`，非 CustomSpanItem 额外提取 `textStyle`，返回包含 `resultObjects` 的 `SelectionInfo`（`rich_editor_pattern.cpp:5118-5149`） | 正常 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1, R-2, R-3, R-4 | N/A（存量） | 代码审查 | `rich_editor_controller.cpp:27-32`, `rich_editor_pattern.cpp:1444-1493` |
| AC-2.1~2.6 | R-1, R-5, R-6, R-7 | N/A | 代码审查 | `rich_editor_controller.cpp:20-25, 41-46`, `rich_editor_pattern.cpp:1087-1148, 1334-1386` |
| AC-3.1~3.4 | R-1, R-8, R-9 | N/A | 代码审查 | `rich_editor_controller.cpp:34-39`, `rich_editor_pattern.cpp:1822-1896` |
| AC-4.1~4.6 | R-10, R-11, R-12, R-13 | N/A | 代码审查 | `rich_editor_controller.cpp:99-104`, `rich_editor_base_controller.cpp:136-141`, `rich_editor_pattern.cpp:1980-2027, 7245-7260` |
| AC-5.1~5.5 | R-14, R-15, R-16 | N/A | 代码审查 | `rich_editor_controller.cpp:74-80, 113-121`, `rich_editor_pattern.cpp:3161-3174, 3416-3462` |
| AC-6.1~6.6 | R-17, R-18, R-19, R-20 | N/A | 代码审查 | `rich_editor_controller.cpp:48-67, 106-112`, `rich_editor_pattern.cpp:2896-2947, 3554-3602` |
| AC-7.1~7.5 | R-21, R-22, R-23 | N/A | 代码审查 | `rich_editor_controller.cpp:123-137`, `rich_editor_pattern.cpp:5094-5150` |

---

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Controller 调用任意 Add* 方法 | 通过 `pattern_.Upgrade()` 委托给 `RichEditorPattern` 对应方法，传入 `TextChangeReason::CONTROLLER` 标记来源为控制器调用 | pattern 为弱引用，Upgrade 失败返回 0 或 -1（`rich_editor_controller.cpp:20-46`） | AC-1.1, AC-2.1, AC-2.3, AC-3.1 |
| R-2 | 行为 | `AddTextSpan` 执行 | 先校验 `maxLength`，再 `CalculateTruncationLength` 截断文本，触发 `BeforeChangeText` 校验，记录 `OperationRecord`，调用 `AddTextSpanOperation` 执行挂载 | 截断后长度为 0 则返回 -1（`rich_editor_pattern.cpp:1448-1492`） | AC-1.2~1.5 |
| R-3 | 边界 | `AddTextSpan` 的 `options.offset` 有值 | offset 被 `std::clamp` 限制在 `[0, textContentLength]`，并调用 `AdjustSelectorForSymbol` 调整选择器 | offset 超出范围时 clamp 到边界（`rich_editor_pattern.cpp:1463-1466`） | AC-1.4 |
| R-4 | 行为 | TextSpan 添加成功 | 返回 spanIndex（Span 在子节点列表中的位置索引）；触发 `AfterContentChange` → `OnDidChange` 事件 | spanIndex 用于后续 `getSpans`/`updateSpanStyle` 定位（`rich_editor_pattern.cpp:1487-1492`） | AC-1.5 |
| R-5 | 行为 | `AddImageSpan` 执行 | 创建 `ImageSpanNode`（tag=`V2::IMAGE_ETS_TAG`，使用 `ImagePattern`），设置同步加载 `SetSyncLoad(true)`，Span 内容设为 `u" "`（1 字符） | 图片 Span 占 1 个字符位置用于计算偏移（`rich_editor_pattern.cpp:1100-1128`） | AC-2.2 |
| R-6 | 行为 | `AddBuilderSpan` → `AddPlaceholderSpan` 执行 | 创建 `PlaceholderSpanNode`（tag=`V2::PLACEHOLDER_SPAN_ETS_TAG`），自定义节点挂载到 placeholder 节点，设置 `SetFocusable(false)`，Span 内容设为 `u" "`（1 字符） | Builder Span 占 1 个字符位置；`placeholderCount_` 递增（`rich_editor_pattern.cpp:1347-1373`） | AC-2.4 |
| R-7 | 边界 | Image/Builder Span 的 offset 有值 | insertIndex = `min(offset, textContentLength)`，调用 `AdjustSelectorForSymbol(insertIndex, HandleType::SECOND, SelectorAdjustPolicy::INCLUDE)` | offset 超过文本长度时取文本长度（`rich_editor_pattern.cpp:1106, 1355`） | AC-2.5 |
| R-8 | 行为 | `AddSymbolSpan` 执行 | 创建 `SpanNode`（tag=`V2::SYMBOL_SPAN_ETS_TAG`），Span 内容设为 `u"  "`（2 字符，`SYMBOL_SPAN_LENGTH = 2`），`spanItemType = SpanItemType::SYMBOL` | Symbol Span 占 2 个字符位置（`rich_editor_pattern.cpp:127, 1860, 1884-1885`） | AC-3.2 |
| R-9 | 边界 | `AddSymbolSpan` 的 maxLength 校验 | 阈值为 `maxLength - 1`（因 SymbolSpan 占 2 字符），达到阈值返回 0 | 与其他 Span 类型的 `maxLength` 直接比较不同（`rich_editor_pattern.cpp:1826-1829`） | AC-3.3 |
| R-10 | 行为 | `DeleteSpans` 执行 | start 默认 0，end 默认 `GetTextContentLength()`；触发 `FireOnWillChange` 校验；记录 `OperationRecord` 和 `UndoRedoRecord`；调用 `DeleteSpansOperation` 执行删除；`AfterContentChange` 触发 `OnDidChange` | 删除前需通过 `OnWillChange` 事件校验（`rich_editor_pattern.cpp:1984-2016`） | AC-4.2, AC-4.4 |
| R-11 | 边界 | `DeleteSpans` 的 start/end 越界 | start > end 时自动交换；start 被 `max(0)` 限制，end 被 `min(length)` 限制；`start > length` 或 `end < 0` 或 `start == end` 时直接返回不操作 | 空范围或完全越界时不触发任何事件（`rich_editor_pattern.cpp:1987-1995`） | AC-4.3 |
| R-12 | 行为 | `deleteBackward()` 调用 | `RichEditorBaseController::DeleteBackward()` → `pattern->DeleteBackwardFunction()` → `HandleOnDelete(true)` → `DeleteBackward(1, TextChangeReason::INPUT)` | 从 `RichEditorBaseController` 继承，非 `RichEditorController` 自身方法（`rich_editor_base_controller.cpp:136-141`, `rich_editor_pattern.cpp:7245-7252`） | AC-4.5 |
| R-13 | 边界 | 预览态输入中调用 `deleteBackward` | `IsPreviewTextInputting()` 为 true 时打印日志并直接返回，不执行删除 | 预览态保护，避免与预览文本逻辑冲突（`rich_editor_pattern.cpp:2022-2025`） | AC-4.6 |
| R-14 | 行为 | `getSpans(value)` 调用 | 委托链：`GetSpansInfo(start, end)` → `GetSpansInfoByRange(start, end)` → `GetSpansInfo(start, end, GetSpansMethod::GETSPANS)`；返回 `SelectionInfo` 含 `resultObjects` 列表 | 每个结果对象含 `spanPosition`、`offsetInSpan`、`value`、样式字段（`rich_editor_abstract_span_result.h:25-437`） | AC-5.1, AC-5.2 |
| R-15 | 行为 | `getParagraphs(value)` 调用 | 委托给 `GetParagraphInfo(start, end)`；按 `\n` 字符分割段落，每个 `ParagraphInfo` 含 `textAlign`/`wordBreak`/`lineBreakStrategy`/`paragraphSpacing`/`leadingMargin`/`range` 等 | 段落分割依据为 SpanItem content 末尾的 `\n`（`rich_editor_pattern.cpp:3426-3458`） | AC-5.3, AC-5.4 |
| R-16 | 边界 | `getParagraphs` 的 start == end | `GetParagraphNodes` 返回空列表，结果为空数组 | 空范围查询返回空结果（`rich_editor_pattern.cpp:3482`） | AC-5.5 |
| R-17 | 边界 | `updateSpanStyle` 的 start/end 处理 | Controller 层：`start = max(0, start)`，`end > length` 则 `end = length`，`start > end` 则交换，`start == end` 或越界则直接返回 | Controller 层完成边界 clamp 后再委托 Pattern（`rich_editor_controller.cpp:48-67`） | AC-6.1 |
| R-18 | 行为 | `updateSpanStyle` Pattern 层执行 | 调用 `AdjustSelector`；遍历子节点：完全包含 → 直接更新样式；部分重叠 → `TextSpanSplit` 拆分后更新；跨过 end → break | TextSpan 和 ImageSpan 的更新路径不同（`rich_editor_pattern.cpp:2906-2944`） | AC-6.2 |
| R-19 | 行为 | `updateSpanStyle` 入参类型分发 | `RichEditorUpdateTextSpanStyleOptions` → 应用 `textStyle`；`RichEditorUpdateImageSpanStyleOptions` → 应用 `imageStyle`；`RichEditorUpdateSymbolSpanStyleOptions` → 应用 `symbolStyle` | 三种入参类型为 union，SDK 层通过 selector 分发（`richEditor.ets:4438-4441, 1219-1228`） | AC-6.3 |
| R-20 | 行为 | `updateParagraphStyle` 执行 | 获取 `[start, end]` 范围内段落 SpanNode 列表，对每个节点更新 `textAlign`/`wordBreak`/`lineBreakStrategy`/`textVerticalAlign`/`textDirection`/`paragraphSpacing`/`gradient`/`leadingMargin`；未指定的属性使用默认值 | 默认值：`TextAlign::START`/`WordBreak::BREAK_WORD`/`LineBreakStrategy::GREEDY`/`TextVerticalAlign::BASELINE`/`TextDirection::INHERIT`（`rich_editor_pattern.cpp:3573-3577`） | AC-6.4~6.6 |
| R-21 | 边界 | `toStyledString` 的 start/end 为 -1 | start 默认 0，end 默认 `GetTextContentLength()`；否则 `std::clamp` 到 `[0, length]`；start > end 则交换 | -1 为"未指定"的哨兵值（`rich_editor_pattern.cpp:5096-5101`） | AC-7.2 |
| R-22 | 行为 | `toStyledString` 执行 | 创建 `SpanString`，若存在 AI 写适配器走 `SetSubSpansWithAIWrite`，否则走 `SetSubSpans` 从 `spans_` 提取子 Span，最后 `SetSubMap` | AI 写适配器路径为增量写入场景（`rich_editor_pattern.cpp:5102-5110`） | AC-7.3 |
| R-23 | 行为 | `fromStyledString` 执行 | 遍历 SpanString 的 `spanItems`，对每个 SpanItem 调用 `GetSpanResultObject` 生成 `ResultObject`；ImageSpanItem 提取 `imageStyle`，非 CustomSpanItem 提取 `textStyle`；返回 `SelectionInfo` 含 `resultObjects` 和 selection 范围 | CustomSpanItem 不提取 textStyle（`rich_editor_pattern.cpp:5118-5149`） | AC-7.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5（addTextSpan） | 代码审查 | Controller 委托、maxLength 截断、offset clamp、OnWillChange/OnDidChange 事件触发 |
| VM-2 | AC-2.1~2.6（addImageSpan/addBuilderSpan） | 代码审查 | ImageSpanNode/PlaceholderSpanNode 创建、1 字符内容约定、offset 处理 |
| VM-3 | AC-3.1~3.4（addSymbolSpan） | 代码审查 | SymbolSpanNode 创建、2 字符内容约定、maxLength-1 阈值 |
| VM-4 | AC-4.1~4.6（deleteSpans/deleteBackward） | 代码审查 | 范围 clamp/swap、OnWillChange 校验、预览态保护、委托路径 |
| VM-5 | AC-5.1~5.5（getSpans/getParagraphs） | 代码审查 | 委托链、ResultObject 结构、段落分割逻辑 |
| VM-6 | AC-6.1~6.6（updateSpanStyle/updateParagraphStyle） | 代码审查 | Controller 层 clamp、Pattern 层遍历更新、部分 Span 拆分、默认值 |
| VM-7 | AC-7.1~7.5（fromStyledString/toStyledString） | 代码审查 | 范围 clamp、SpanString 创建、SpanItem 转换、AI 写适配器分支 |

## API 变更分析

> 本特性为存量规格补录，记录各 API 的引入版本和当前签名。所有 API 均属于 `RichEditorController`，仅适用于旧框架模式。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `addTextSpan` | Public (@since 10) | `content: ResourceStr`, `options?: RichEditorTextSpanOptions` | `int32`（spanIndex） | N/A | 添加文本 Span | AC-1.1~1.5 |
| `addImageSpan` | Public (@since 10) | `value: PixelMap \| ResourceStr`, `options?: RichEditorImageSpanOptions` | `int32`（spanIndex） | N/A | 添加图片 Span | AC-2.1~2.6 |
| `addBuilderSpan` | Public (@since 10) | `value: CustomBuilder`, `options?: RichEditorBuilderSpanOptions` | `int32`（spanIndex） | N/A | 添加 Builder Span | AC-2.1~2.6 |
| `addSymbolSpan` | Public (@since 11) | `value: Resource`, `options?: RichEditorSymbolSpanOptions` | `int32`（spanIndex） | N/A | 添加符号 Span | AC-3.1~3.4 |
| `deleteSpans` | Public (@since 10) | `value?: RichEditorRange` | `void` | N/A | 按范围删除 Span | AC-4.1~4.4 |
| `deleteBackward` | Public (@since 10) | 无 | `void` | N/A | 向后删除一个单位（从 RichEditorBaseController 继承） | AC-4.5~4.6 |
| `getSpans` | Public (@since 10) | `value?: RichEditorRange` | `Array<RichEditorSpan>` | N/A | 查询 Span 信息 | AC-5.1~5.2 |
| `getParagraphs` | Public (@since 10) | `value?: RichEditorRange` | `Array<RichEditorParagraphResult>` | N/A | 查询段落信息 | AC-5.3~5.5 |
| `updateSpanStyle` | Public (@since 10) | `value: RichEditorUpdateTextSpanStyleOptions \| RichEditorUpdateImageSpanStyleOptions \| RichEditorUpdateSymbolSpanStyleOptions` | `void` | N/A | 更新 Span 样式 | AC-6.1~6.3 |
| `updateParagraphStyle` | Public (@since 10) | `value: RichEditorParagraphStyleOptions` | `void` | N/A | 更新段落样式 | AC-6.4~6.6 |
| `fromStyledString` | Public (@since 12) | `value: StyledString` | `Array<RichEditorSpan>` | N/A | StyledString 转 Span 结果 | AC-7.4~7.5 |
| `toStyledString` | Public (@since 12) | `value: RichEditorRange` | `StyledString` | N/A | Span 内容转 StyledString | AC-7.1~7.3 |

### 变更/废弃 API

无。本特性为已有实现补录，不涉及 API 签名变更或废弃。

## 接口规格

### 接口定义

> 以下为各 API 的函数签名、返回值、开放范围、参数约束和行为场景。所有方法签名引用自 `richEditor.ets:4418-4471`。

#### addTextSpan

| 属性 | 值 |
|------|-----|
| 函数签名 | `addTextSpan(content: ResourceStr, options?: RichEditorTextSpanOptions): int32` |
| 返回值 | spanIndex（Span 在子节点列表中的位置索引），pattern 不可用时返回 0 |
| 开放范围 | Public (@since 10) |
| 参数约束 | `content`: ResourceStr（string 或 Resource）；`options.offset`: int32，clamp 到 `[0, textContentLength]`；`options.style`: RichEditorTextStyle |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常添加 | content 非空，未超 maxLength | 截断文本至剩余可用长度，创建 SpanNode 挂载到 contentHost，返回 spanIndex |
| maxLength 达到 | `GetTextContentLength() >= maxLength` | 返回 0，不执行添加 |
| 截断后为空 | `CalculateTruncationLength` 返回 0 | 返回 -1 |
| offset 越界 | offset > textContentLength | clamp 到 textContentLength |

#### addImageSpan

| 属性 | 值 |
|------|-----|
| 函数签名 | `addImageSpan(value: PixelMap \| ResourceStr, options?: RichEditorImageSpanOptions): int32` |
| 返回值 | spanIndex，pattern 不可用时返回 0，BeforeAddImage 校验失败返回 -1 |
| 开放范围 | Public (@since 10) |
| 参数约束 | `value`: PixelMap 或 ResourceStr；`options.offset`: int32，`min(offset, textContentLength)`；`options.imageStyle`: RichEditorImageSpanStyle |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常添加 | value 有效，未超 maxLength | 创建 ImageSpanNode，Span 内容设为 `u" "`（1 字符），返回 spanIndex |
| maxLength 达到 | `GetTextContentLength() >= maxLength` | 返回 0 |
| BeforeAddImage 失败 | 非 UndoRedo 且 BeforeAddImage 返回 false | 返回 -1 |

#### addBuilderSpan

| 属性 | 值 |
|------|-----|
| 函数签名 | `addBuilderSpan(value: CustomBuilder, options?: RichEditorBuilderSpanOptions): int32` |
| 返回值 | spanIndex，pattern/customNode 不可用时返回 0 |
| 开放范围 | Public (@since 10) |
| 参数约束 | `value`: CustomBuilder；`options.offset`: int32，`min(offset, textContentLength)`；`options.dragBackgroundColor`/`isDragShadowNeeded`/`accessibilitySpanOptions` 可选 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常添加 | customNode 有效，未超 maxLength | 创建 PlaceholderSpanNode，自定义节点挂载到 placeholder，Span 内容设为 `u" "`（1 字符），返回 spanIndex |
| maxLength 达到 | `GetTextContentLength() >= maxLength` | 返回 0 |
| customNode 为空 | customNode 为 null | 返回 0 |

#### addSymbolSpan

| 属性 | 值 |
|------|-----|
| 函数签名 | `addSymbolSpan(value: Resource, options?: RichEditorSymbolSpanOptions): int32` |
| 返回值 | spanIndex，pattern 不可用时返回 0，BeforeAddSymbol 校验失败返回 -1 |
| 开放范围 | Public (@since 11) |
| 参数约束 | `value`: Resource（symbolId）；`options.offset`: int32，clamp 到 `[0, textContentLength]`；`options.style`: RichEditorSymbolSpanStyle |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常添加 | value 有效，未超 maxLength-1 | 创建 SymbolSpanNode，Span 内容设为 `u"  "`（2 字符），返回 spanIndex |
| maxLength-1 达到 | `GetTextContentLength() >= maxLength - 1` | 返回 0 |
| offset 越界 | offset > textContentLength | clamp 到 textContentLength |

#### deleteSpans

| 属性 | 值 |
|------|-----|
| 函数签名 | `deleteSpans(value?: RichEditorRange): void` |
| 返回值 | void |
| 开放范围 | Public (@since 10) |
| 参数约束 | `value.start`: int32，默认 0；`value.end`: int32，默认 `GetTextContentLength()`；start > end 自动交换 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常删除 | 范围有效，OnWillChange 通过 | 触发 FireOnWillChange，记录 OperationRecord/UndoRedoRecord，执行 DeleteSpansOperation，触发 OnDidChange |
| 空范围 | start == end | 直接返回，不操作 |
| 完全越界 | start > length 或 end < 0 | 直接返回 |
| 未指定范围 | value 为 undefined | start=0, end=length，删除全部内容 |

#### deleteBackward

| 属性 | 值 |
|------|-----|
| 函数签名 | `deleteBackward(): void` |
| 返回值 | void |
| 开放范围 | Public (@since 10)，从 RichEditorBaseController 继承 |
| 参数约束 | 无参数 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常删除 | 非预览态 | HandleOnDelete(true) → DeleteBackward(1, TextChangeReason::INPUT) |
| 预览态保护 | IsPreviewTextInputting() 为 true | 打印日志，直接返回 |

#### getSpans

| 属性 | 值 |
|------|-----|
| 函数签名 | `getSpans(value?: RichEditorRange): Array<RichEditorSpan>` |
| 返回值 | `Array<RichEditorImageSpanResult \| RichEditorTextSpanResult>`，pattern 不可用时返回空 |
| 开放范围 | Public (@since 10) |
| 参数约束 | `value.start`/`value.end`: int32，可选 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常查询 | 范围有效 | 返回 SelectionInfo 的 resultObjects，每个含 spanPosition/offsetInSpan/value/textStyle/imageStyle |
| pattern 不可用 | pattern_.Upgrade() 失败 | 返回空 SelectionInfo |

#### getParagraphs

| 属性 | 值 |
|------|-----|
| 函数签名 | `getParagraphs(value?: RichEditorRange): Array<RichEditorParagraphResult>` |
| 返回值 | `Array<RichEditorParagraphResult>`，pattern 不可用时返回空 |
| 开放范围 | Public (@since 10) |
| 参数约束 | `value.start`/`value.end`: int32，可选 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常查询 | 范围有效，start != end | 按 `\n` 分割段落，返回 ParagraphInfo 列表 |
| 空范围 | start == end | 返回空数组 |

#### updateSpanStyle

| 属性 | 值 |
|------|-----|
| 函数签名 | `updateSpanStyle(value: RichEditorUpdateTextSpanStyleOptions \| RichEditorUpdateImageSpanStyleOptions \| RichEditorUpdateSymbolSpanStyleOptions): void` |
| 返回值 | void |
| 开放范围 | Public (@since 10) |
| 参数约束 | `value.start`/`value.end`: int32（继承自 RichEditorSpanStyleOptions）；Controller 层 clamp start/end 并交换；`value.textStyle`/`imageStyle`/`symbolStyle` 根据 union 类型选择 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常更新 | 范围有效 | 遍历子节点，完全包含 → 直接更新；部分重叠 → TextSpanSplit 拆分后更新 |
| 空范围 | start == end | 直接返回 |
| 越界 | start > length 或 end < 0 | 直接返回 |

#### updateParagraphStyle

| 属性 | 值 |
|------|-----|
| 函数签名 | `updateParagraphStyle(value: RichEditorParagraphStyleOptions): void` |
| 返回值 | void |
| 开放范围 | Public (@since 10) |
| 参数约束 | `value.start`/`value.end`: int32（继承自 RichEditorRange）；`value.style`: RichEditorParagraphStyle，各属性可选，未指定使用默认值 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常更新 | 范围有效 | 获取段落 SpanNode 列表，逐个更新段落样式属性 |
| 属性未指定 | style 中某属性为 undefined | 使用默认值（TextAlign::START 等） |

#### fromStyledString

| 属性 | 值 |
|------|-----|
| 函数签名 | `fromStyledString(value: StyledString): Array<RichEditorSpan>` |
| 返回值 | `Array<RichEditorSpan>`，pattern/spanString 不可用时返回空 SelectionInfo |
| 开放范围 | Public (@since 12) |
| 参数约束 | `value`: StyledString，需可 DynamicCast 为 SpanString |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常转换 | spanString 非空且有 spanItems | 遍历 spanItems，生成 ResultObject 列表，返回 SelectionInfo |
| spanString 为空 | spanString 为 null 或无 spanItems | 返回空 SelectionInfo（start=0, end=0） |

#### toStyledString

| 属性 | 值 |
|------|-----|
| 函数签名 | `toStyledString(value: RichEditorRange): StyledString` |
| 返回值 | StyledString，pattern 不可用时返回 nullptr |
| 开放范围 | Public (@since 12) |
| 参数约束 | `value.start`/`value.end`: int32，-1 为"未指定"哨兵值 |

| 行为场景 | 触发条件 | 预期行为 |
|----------|----------|----------|
| 正常转换 | 范围有效 | 创建 SpanString，从 spans_ 提取子 Span，设置样式映射 |
| 未指定范围 | start/end 为 -1 | start=0, end=length，转换全部内容 |
| start > end | 范围倒序 | 自动交换 start 和 end |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — API 12 引入 `fromStyledString`/`toStyledString` 双向转换接口，为旧框架 Span 模型与 StyledString 数据模型提供跨模式转换能力；API 11 引入 `addSymbolSpan`
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否 — Span 内容仍存储在 `spans_` 列表和 SpanNode 子节点树中
- **最低支持版本:** API 10（增删改查接口），API 11（addSymbolSpan），API 12（fromStyledString/toStyledString）
- **API 版本号策略:** `addTextSpan`/`addImageSpan`/`addBuilderSpan`/`deleteSpans`/`deleteBackward`/`getSpans`/`getParagraphs`/`updateSpanStyle`/`updateParagraphStyle` 自 API 10 起；`addSymbolSpan` 自 API 11 起；`fromStyledString`/`toStyledString` 自 API 12 起

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 旧框架模式专用 | 所有 12 个 API 均属于 `RichEditorController`，仅适用于旧框架模式（`isSpanStringMode_=false`）；StyledString 模式使用 `RichEditorStyledStringController` | AC-1.1~7.5 |
| Controller 委托模式 | 所有方法通过 `pattern_.Upgrade()` 委托给 `RichEditorPattern`，pattern 为弱引用，Upgrade 失败时返回默认值（0/-1/空） | AC-1.1, AC-2.1, AC-3.1, AC-4.5 |
| Span 字符长度约定 | TextSpan 按实际文本长度计算；ImageSpan 和 BuilderSpan 占 1 字符（`u" "`）；SymbolSpan 占 2 字符（`u"  "`，`SYMBOL_SPAN_LENGTH=2`） | AC-2.2, AC-2.4, AC-3.2 |
| maxLength 校验差异 | TextSpan 使用 `CalculateTruncationLength` 按字符截断；ImageSpan/BuilderSpan 直接比较 `GetTextContentLength() >= maxLength`；SymbolSpan 比较 `>= maxLength - 1` | AC-1.2, AC-2.6, AC-3.3 |
| OnWillChange 事件门控 | `DeleteSpans` 和 `AddTextSpan` 在执行前需通过 `FireOnWillChange`/`BeforeChangeText` 事件校验，校验失败则中止操作 | AC-1.5, AC-4.4 |
| Undo/Redo 记录 | Add* 和 Delete* 方法均记录 `OperationRecord` 和/或 `UndoRedoRecord`，支持撤销重做；UndoRedo 来源（`OptionSource::UNDO_REDO`）跳过部分校验和记录 | AC-1.5, AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | Controller 持有 `WeakPtr<RichEditorPattern>`，Upgrade 失败时返回安全默认值，不崩溃 | 代码审查 | `rich_editor_controller.cpp:22-23, 29-30, 36-37` |
| 可测试性 | 各 Add* 方法返回 spanIndex，可通过 `getSpans` 验证添加结果 | 代码审查 | `rich_editor_pattern.cpp:1147, 1386, 1492, 1895` |
| 性能 | `GetSpansInfo` 使用 `ACE_SCOPED_TRACE` 标记性能追踪点 | 代码审查 | `rich_editor_controller.cpp:78` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |
| 预览模式 | `HandleOnDelete` 在 PREVIEW 宏下 forward/backward 方向反转 | `#if defined(PREVIEW)` 编译时决定 | 代码审查 | `rich_editor_pattern.cpp:7248-7258` |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | `AddPlaceholderSpan` 调用 `InitPlaceholderAccessibility` 设置无障碍级别/文本/描述 | AC-2.4 |
| 大字体 | 是 | `AddTextSpan`/`AddSymbolSpan` 获取 `GetEnvFontScaleFromLayout()` 用于日志和样式计算 | AC-1.1, AC-3.1 |
| 深色模式 | N/A | Span 内容管理操作不直接涉及主题模式 | — |
| 多窗口/分屏 | N/A | Span 内容管理操作不直接涉及窗口模式 | — |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | API 11 引入 `addSymbolSpan`，API 12 引入 `fromStyledString`/`toStyledString` | AC-3.1, AC-7.1, AC-7.4 |
| 生态兼容 | N/A | — | — |
| AI 写适配 | 是 | `toStyledString` 在存在 AI 写适配器时走 `SetSubSpansWithAIWrite` 增量路径 | AC-7.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RichEditor Span 内容管理
  作为应用开发者
  我想要通过 RichEditorController 增删改查 Span 内容
  以便以编程方式构建和编辑富文本

  Scenario: 添加文本 Span
    Given 一个旧框架模式的 RichEditor 组件
    When 调用 addTextSpan("Hello", { offset: 0 })
    Then 文本被截断至 maxLength 剩余可用长度
    And offset 被 clamp 到 [0, textContentLength]
    And 触发 BeforeChangeText 校验
    And 返回 spanIndex
    And 触发 OnDidChange 事件

  Scenario: 添加图片 Span 超出 maxLength
    Given RichEditor 内容长度已达到 maxLength
    When 调用 addImageSpan(pixelMap)
    Then 返回 0
    And 不执行任何添加操作

  Scenario: 添加 Symbol Span 的字符长度约定
    Given 一个旧框架模式的 RichEditor 组件
    When 调用 addSymbolSpan(symbolResource)
    Then 创建 SymbolSpanNode，Span 内容为 2 字符
    And maxLength 校验阈值为 maxLength - 1

  Scenario: 按范围删除 Span
    Given RichEditor 中有文本内容 "Hello World"
    When 调用 deleteSpans({ start: 5, end: 11 })
    Then 触发 FireOnWillChange 事件校验
    And 记录 OperationRecord 和 UndoRedoRecord
    And 删除范围 [5, 11] 的内容
    And 触发 OnDidChange 事件

  Scenario: 删除范围越界处理
    Given RichEditor 内容长度为 10
    When 调用 deleteSpans({ start: 15, end: 20 })
    Then start > length，直接返回不操作
    And 不触发任何事件

  Scenario: deleteBackward 在预览态被保护
    Given RichEditor 处于预览文本输入态
    When 调用 deleteBackward()
    Then 打印日志并直接返回
    And 不执行删除操作

  Scenario: 更新 Span 样式时部分 Span 拆分
    Given RichEditor 有一个 Span 范围为 [0, 10]
    When 调用 updateSpanStyle({ start: 3, end: 7, textStyle: { fontColor: Color.Red } })
    Then 调用 TextSpanSplit 在 index 3 和 7 处拆分 Span
    And 对拆分后的子 Span 应用新样式

  Scenario: toStyledString 未指定范围
    Given RichEditor 有文本内容 "ABC"
    When 调用 toStyledString({ start: -1, end: -1 })
    Then start 默认为 0，end 默认为 3
    And 从 spans_ 列表提取全部子 Span 创建 SpanString

  Scenario: fromStyledString 转换
    Given 一个包含文本和图片 Span 的 StyledString
    When 调用 fromStyledString(styledString)
    Then 遍历 spanItems 生成 ResultObject 列表
    And ImageSpanItem 提取 imageStyle
    And 非 CustomSpanItem 提取 textStyle
    And 返回包含 resultObjects 的 SelectionInfo
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Span 增删改查与 StyledString 转换，不含组件初始化、布局算法、渲染细节、事件回调签名）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）
- [x] 所有源引用使用真实 file:line 格式
- [x] 所有 API 签名引用自 SDK 生成文件（`richEditor.ets`）
- [x] 接口规格覆盖全部 12 个 API

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditorController AddTextSpan AddImageSpan AddSymbolSpan AddPlaceholderSpan delegation to RichEditorPattern"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern DeleteSpans DeleteBackwardFunction GetSpansInfo GetParagraphInfo UpdateSpanStyle UpdateParagraphStyle"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern ToStyledString FromStyledString StyledString conversion spans_ list"
  - repo: "openharmony/ace_engine"
    query: "RichEditor SYMBOL_SPAN_LENGTH maxLength CalculateTruncationLength offset clamp span content length"
  - repo: "openharmony/interface_sdk-js"
    query: "RichEditorController addTextSpan addImageSpan addBuilderSpan addSymbolSpan deleteSpans getSpans getParagraphs updateSpanStyle fromStyledString toStyledString API signatures"
```

**关键文档：**
- SDK 静态版声明: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets`
- 控制器声明: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_controller.h`
- 控制器实现: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_controller.cpp`
- 基类控制器: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_base_controller.h/cpp`
- Pattern 实现: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.cpp`
- Span 结果类型: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_abstract_span_result.h`
