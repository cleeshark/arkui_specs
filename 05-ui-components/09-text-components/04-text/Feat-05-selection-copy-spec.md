# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Text 选择与复制 |
| 特性编号 | Feat-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 9 起支持（copyOption），API 11/12/14/22/23/26 有 API 新增 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 存量补录——文档化 Text 组件已有的选择与复制能力。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Feat-05 规格文档 | 补录已有选择与复制相关属性的行为规格 |
| MODIFIED | design.md 增量合并 | 追加 Feat-05 ADR/架构图/数据模型/详细设计/风险到现有设计文档 |

## 输入文档

- **需求基线:** 无独立 proposal.md（已有能力补录）
- **设计文档:** `specs/05-ui-components/09-text-components/04-text/design.md`（DESIGN-Func-05-09-04）
- **源码定位:** `frameworks/core/components_ng/pattern/text/text_pattern.cpp`, `text_layout_property.h`, `text_select_overlay.cpp`

## 用户故事

### US-1: 复制权限控制

> 作为开发者，我想要控制 Text 组件内容是否可被复制及复制范围，以便保护应用内敏感文本或启用文本共享。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `copyOption(CopyOptions.None)` THEN 文本不可选择、不可复制、不可拖拽 | 正常 |
| AC-1.2 | WHEN `copyOption(CopyOptions.InApp)` THEN 复制的内容仅可在同一应用内粘贴 | 正常 |
| AC-1.3 | WHEN `copyOption(CopyOptions.LocalDevice)` THEN 复制的内容可在同一设备的任意应用内粘贴 | 正常 |
| AC-1.4 | WHEN `copyOption` 未设置 THEN 默认值为 `CopyOptions.None`（不可复制） | 异常 |
| AC-1.5 | WHEN `textOverflow` 为 `MARQUEE` 模式 THEN `copyOption` 强制为 `CopyOptions.None`（`text_pattern.cpp:2969`），选择与复制不可用 | 异常 |
| AC-1.6 | WHEN `copyOption != None` 且 `textSelectable != UNSELECTABLE` 且无文本动效 THEN `IsSelectableAndCopy()` 返回 true，选择与复制功能可用（`text_pattern.cpp:3816-3822`） | 正常 |
| AC-1.7 | WHEN SpanString 模式下执行复制 THEN 剪贴板同时写入纯文本、HTML、SpanString TLV 二进制三种格式（`text_pattern.cpp:1222-1248`） | 正常 |
| AC-1.8 | WHEN 非 SpanString 模式（纯文本或 Span 子节点）下执行复制 THEN 剪贴板同时写入纯文本、HTML、SpanString TLV 三种格式（`text_pattern.cpp:1366-1408`） | 正常 |
| AC-1.9 | WHEN HTML 生成完成前用户再次触发复制 THEN 后台线程异步生成 HTML 不阻塞 UI 线程 | 正常 |
| AC-1.10 | WHEN 用户按 Ctrl+C THEN 触发复制流程，行为与菜单"复制"一致（`text_pattern.cpp:3632-3637`） | 正常 |
| AC-1.11 | WHEN 用户按 Ctrl+A THEN 全选文本（`text_pattern.cpp:3640-3648`），选择范围为 `[0, textSize]` | 正常 |

### US-2: 可选择性控制

> 作为开发者，我想要控制 Text 组件的文本是否可被用户选择以及选择后的焦点行为，以便在不同场景下提供合适的交互体验。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `textSelectable(TextSelectableMode.SELECTABLE_UNFOCUSABLE)` THEN 文本可选择，但组件不可获取焦点 | 正常 |
| AC-2.2 | WHEN `textSelectable(TextSelectableMode.SELECTABLE_FOCUSABLE)` THEN 文本可选择，且组件可获取焦点（`focusHub->SetFocusable(true)`, `SetIsFocusOnTouch(true)`）（`text_pattern.cpp:3801-3813`） | 正常 |
| AC-2.3 | WHEN `textSelectable(TextSelectableMode.UNSELECTABLE)` THEN 文本不可选择，长按/双击/鼠标拖选均无效 | 异常 |
| AC-2.4 | WHEN `textSelectable` 未设置 THEN 默认值为 `SELECTABLE_UNFOCUSABLE` | 异常 |
| AC-2.5 | WHEN 用户长按文本 THEN 以词边界为单位选中初始文本（`pManager_->GetWordBoundary()`，`text_pattern.cpp:344-364`），若无词边界则选中单个字符簇 | 边界 |
| AC-2.6 | WHEN 用户双击文本 THEN 选中光标所在的词（与长按相同的词边界逻辑，`text_pattern.cpp:2440-2474`） | 边界 |
| AC-2.7 | WHEN 用户鼠标左键按下并拖动 THEN 实时更新选区范围（`text_pattern.cpp:3397-3426`） | 正常 |
| AC-2.8 | WHEN 用户在 SELECTABLE_FOCUSABLE 模式下按 Shift+方向键 THEN 逐字符（Left/Right）或逐行（Up/Down）扩展选区（`text_pattern.cpp:3659-3680`） | 正常 |

### US-3: 编程式选区设置

> 作为开发者，我想要通过代码设置 Text 组件的选区范围，以便实现搜索高亮、程序联动等功能。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `selection(startIndex, endIndex)` 且 `startIndex < endIndex` THEN 文本从 startIndex 到 endIndex 处于选中状态，显示选择手柄 | 边界 |
| AC-3.2 | WHEN `selection(startIndex, endIndex)` 且 `startIndex >= endIndex` THEN 选区无效，不显示选中效果 | 异常 |
| AC-3.3 | WHEN `selection` 的索引超出文本长度 THEN 自动钳位到 `[0, textLength]`（`text_pattern.cpp:4999`） | 边界 |
| AC-3.4 | WHEN `textSelectable == UNSELECTABLE` 或 `copyOption == None` THEN `selection()` 调用被忽略（`text_pattern.cpp:1589` 守卫条件） | 正常 |
| AC-3.5 | WHEN `selection()` 在布局完成前调用 THEN 通过 `AfterLayoutTask` 延迟执行，确保选区坐标正确（`text_pattern.cpp:1589`） | 正常 |

### US-4: 选区外观定制

> 作为开发者，我想要自定义选中文本的背景色和选择手柄颜色，以便与应用主题风格一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `selectedBackgroundColor(color)` THEN 选中文本区域的背景色为指定颜色 | 正常 |
| AC-4.2 | WHEN `selectedBackgroundColor` 传入的颜色 alpha 为 255（完全不透明）THEN 自动应用 20% 不透明度（`js_text.cpp:459`） | 正常 |
| AC-4.3 | WHEN `selectedBackgroundColor` 未设置 THEN 使用 `TextTheme` 提供的默认选中背景色 | 异常 |
| AC-4.4 | WHEN `caretColor(color)` THEN 选择手柄颜色变为指定颜色（存储为 `CursorColor`，`text_layout_property.h:210`） | 正常 |
| AC-4.5 | WHEN `caretColor` 未设置 THEN 手柄颜色取 `TextTheme::GetCaretColor()` 默认值 | 异常 |
| AC-4.6 | WHEN `caretColor` 设置后 THEN 选择覆盖层的 `handlerColor` 使用该颜色（`text_select_overlay.cpp:386`），拖拽手柄和选择手柄颜色一致 | 正常 |

### US-5: 选中文本拖拽

> 作为开发者，我想要支持选中文本的拖拽操作，以便用户可以将文本拖放到其他组件或应用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `draggable(true)` 且 `IsSelectableAndCopy() == true` THEN 可拖拽选中的文本 | 正常 |
| AC-5.2 | WHEN 用户长按已选中文本区域 THEN 触发拖拽手势，拖拽优先于重新选择（`text_pattern.cpp:718-727`） | 正常 |
| AC-5.3 | WHEN 用户长按未选中文本区域 THEN 触发正常的选择流程（不触发拖拽） | 正常 |
| AC-5.4 | WHEN 拖拽含 Span 子节点的选中文本 THEN 拖拽数据包含 UDMF 格式：纯文本 + SpanString TLV + 图片记录（`text_pattern.cpp:3877-3895`） | 正常 |
| AC-5.5 | WHEN 拖拽无子节点的纯文本 THEN 拖拽数据仅包含纯文本 UDMF 记录（`text_pattern.cpp:3960-3997`） | 正常 |
| AC-5.6 | WHEN 拖拽失败（未成功投放）THEN 选区恢复到拖拽前状态（`text_pattern.cpp:4067-4070`） | 异常 |
| AC-5.7 | WHEN `selectedDragPreviewStyle({ color: Color })` THEN 拖拽预览背景色为指定颜色 | 正常 |
| AC-5.8 | WHEN `selectedDragPreviewStyle` 未设置 THEN 亮色模式默认 `#f2ffffff`，暗色模式默认 `#202224` | 异常 |
| AC-5.9 | WHEN 拖拽预览生成 THEN 显示带圆角背景（18vp，2in1 设备 8vp）和选择手柄的文本片段缩略图 | 正常 |

### US-6: 选择菜单绑定

> 作为开发者，我想要为不同类型的选中内容（文本/图片/混合）绑定自定义选择菜单，以便提供针对性的操作选项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `bindSelectionMenu(TextSpanType.TEXT, builder, TextResponseType.LONG_PRESS)` THEN 长按选中纯文本时显示自定义菜单（builder 渲染的 UI 替换系统默认菜单） | 正常 |
| AC-6.2 | WHEN `bindSelectionMenu(TextSpanType.IMAGE, builder, TextResponseType.RIGHT_CLICK)` THEN 右键点击选中图片时显示自定义菜单 | 正常 |
| AC-6.3 | WHEN `bindSelectionMenu(TextSpanType.DEFAULT, builder, TextResponseType.DEFAULT)` THEN 对所有内容类型和响应方式生效（通配匹配） | 正常 |
| AC-6.4 | WHEN 精确匹配的菜单绑定不存在 THEN 按 4 级回退查找：精确匹配 → span 通配 → response 通配 → 双通配（`text_pattern.cpp:6897-6917`） | 异常 |
| AC-6.5 | WHEN `bindSelectionMenu` 的 builder 传 null THEN 移除对应的菜单绑定（`text_pattern.cpp:6819-6850`） | 异常 |
| AC-6.6 | WHEN `SelectionMenuOptions.onAppear` 设置 THEN 菜单显示时回调 `(selectionStart, selectionEnd)` 参数 | 正常 |
| AC-6.7 | WHEN `SelectionMenuOptions.onDisappear` 设置 THEN 菜单消失时触发回调 | 正常 |

### US-7: 编辑菜单定制

> 作为开发者，我想要定制系统默认选择菜单的菜单项列表和点击行为，以便在保留系统菜单框架的同时添加自定义操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `editMenuOptions({ onCreateMenu, onMenuItemClick })` THEN `onCreateMenu` 在每次菜单显示前被调用，接收系统默认菜单项数组，返回定制后的菜单项数组 | 正常 |
| AC-7.2 | WHEN `onMenuItemClick` 返回 `true` THEN 拦截系统默认点击行为；返回 `false` THEN 执行系统默认行为 | 正常 |
| AC-7.3 | WHEN `editMenuOptions` 与 `bindSelectionMenu` 同时设置 THEN 两者互补——`bindSelectionMenu` 的自定义 builder 替换整个菜单 UI，`editMenuOptions` 的回调仍挂载在 overlay 上但不影响自定义 builder 的渲染 | 正常 |
| AC-7.4 | WHEN `bindSelectionMenu` 未匹配到任何绑定 THEN 显示系统默认菜单，此时 `editMenuOptions` 的 `onCreateMenu` 可定制系统菜单项 | 正常 |
| AC-7.5 | WHEN Text 组件的系统菜单显示 THEN 菜单包含"复制"（不包含"剪切"和"粘贴"，因为 Text 是只读组件）（`text_select_overlay.cpp:348-375`） | 正常 |
| AC-7.6 | WHEN 全部文本已选中 THEN "全选"菜单项隐藏（`showCopyAll = !textPattern->IsSelectAll()`） | 正常 |

### US-8: 选择覆盖层交互

> 作为开发者，我想要选择覆盖层提供直观的手柄拖动和放大镜辅助，以便用户能精确调整选区。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 用户拖动选择手柄 THEN 选区范围实时更新，手柄位置对应最近的字符索引（`GetHandleIndex` → `pManager_->GetGlyphIndexByCoordinate()`，`text_pattern.cpp:6685`） | 正常 |
| AC-8.2 | WHEN 用户拖动选择手柄 THEN 触发振动反馈（`StartVibratorByIndexChange()`），每次字符索引变化时振动一次 | 正常 |
| AC-8.3 | WHEN 用户拖动选择手柄 THEN 显示放大镜（magnifier），跟随手柄位置实时移动（`text_select_overlay.cpp:175-177`） | 正常 |
| AC-8.4 | WHEN 用户释放选择手柄 THEN 放大镜隐藏（`RemoveMagnifierFrameNode()`，`text_select_overlay.cpp:229-231`） | 正常 |
| AC-8.5 | WHEN 长按初始选择文本 THEN 也显示放大镜（`text_pattern.cpp:744-747`），手指移动时放大镜跟随 | 正常 |
| AC-8.6 | WHEN 用户点击选区外部 THEN 清除选区并关闭覆盖层（`text_select_overlay.cpp:512-526`） | 正常 |
| AC-8.7 | WHEN 选择手柄的第一个手柄越过第二个手柄位置 THEN 选区仍有效（`GetTextStart()`/`GetTextEnd()` 使用 `std::min`/`std::max` 保证范围正确） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 | R-1, R-6 | TASK-5 | 单测 | text_pattern_test |
| AC-1.2 | R-1 | TASK-5 | 单测 | clipboard scope test |
| AC-1.3 | R-1 | TASK-5 | 单测 | clipboard scope test |
| AC-1.4 | R-6 | TASK-5 | 单测 | default value test |
| AC-1.5 | R-2 | TASK-5 | 单测 | marquee + copyOption test |
| AC-1.6 | R-1, R-2 | TASK-5 | 单测 | IsSelectableAndCopy test |
| AC-1.7 | R-7 | TASK-5 | 单测 | SpanString copy test |
| AC-1.8 | R-7 | TASK-5 | 单测 | plain text copy test |
| AC-1.9 | R-7 | TASK-5 | 代码审查 | async HTML generation |
| AC-1.10 | R-8 | TASK-5 | 单测 | keyboard shortcut test |
| AC-1.11 | R-8 | TASK-5 | 单测 | select all test |
| AC-2.1 | R-3, R-9 | TASK-5 | 单测 | textSelectable mode test |
| AC-2.2 | R-3, R-9 | TASK-5 | 单测 | focus behavior test |
| AC-2.3 | R-3, R-9 | TASK-5 | 单测 | unselectable test |
| AC-2.4 | R-9 | TASK-5 | 单测 | default mode test |
| AC-2.5 | R-10 | TASK-5 | 单测 | word boundary test |
| AC-2.6 | R-10 | TASK-5 | 单测 | double click test |
| AC-2.7 | R-10 | TASK-5 | 单测 | mouse drag test |
| AC-2.8 | R-11 | TASK-5 | 单测 | keyboard selection test |
| AC-3.1 | R-12 | TASK-5 | 单测 | programmatic selection test |
| AC-3.2 | R-26 | TASK-5 | 单测 | invalid range test |
| AC-3.3 | R-27 | TASK-5 | 单测 | clamp test |
| AC-3.4 | R-1, R-3 | TASK-5 | 单测 | guard condition test |
| AC-3.5 | R-12 | TASK-5 | 代码审查 | AfterLayoutTask |
| AC-4.1 | R-13 | TASK-5 | 单测 | selectedBgColor test |
| AC-4.2 | R-13 | TASK-5 | 单测 | alpha auto-adjust test |
| AC-4.3 | R-13 | TASK-5 | 单测 | default color test |
| AC-4.4 | R-14 | TASK-5 | 单测 | caretColor test |
| AC-4.5 | R-14 | TASK-5 | 单测 | default handle color test |
| AC-4.6 | R-14 | TASK-5 | 代码审查 | overlay handlerColor |
| AC-5.1 | R-4, R-15 | TASK-5 | 单测 | draggable + selection test |
| AC-5.2 | R-4, R-15 | TASK-5 | 单测 | long press drag priority |
| AC-5.3 | R-15 | TASK-5 | 单测 | non-selected area test |
| AC-5.4 | R-16 | TASK-5 | 单测 | UDMF data format test |
| AC-5.5 | R-16 | TASK-5 | 单测 | plain text drag test |
| AC-5.6 | R-32 | TASK-5 | 单测 | drag cancel recovery |
| AC-5.7 | R-17 | TASK-5 | 单测 | drag preview color test |
| AC-5.8 | R-17 | TASK-5 | 单测 | default preview color test |
| AC-5.9 | R-17 | TASK-5 | 代码审查 | drag node layout |
| AC-6.1 | R-18 | TASK-5 | 单测 | bindSelectionMenu test |
| AC-6.2 | R-18 | TASK-5 | 单测 | image span menu test |
| AC-6.3 | R-19 | TASK-5 | 单测 | default wildcard test |
| AC-6.4 | R-19 | TASK-5 | 单测 | fallback lookup test |
| AC-6.5 | R-18 | TASK-5 | 单测 | unbind menu test |
| AC-6.6 | R-20 | TASK-5 | 单测 | onAppear callback test |
| AC-6.7 | R-20 | TASK-5 | 单测 | onDisappear callback test |
| AC-7.1 | R-21 | TASK-5 | 单测 | editMenuOptions test |
| AC-7.2 | R-21 | TASK-5 | 单测 | onMenuItemClick test |
| AC-7.3 | R-5 | TASK-5 | 代码审查 | overlay update sequence |
| AC-7.4 | R-5, R-21 | TASK-5 | 单测 | system menu + editMenuOptions |
| AC-7.5 | R-22 | TASK-5 | 单测 | menu item visibility test |
| AC-7.6 | R-22 | TASK-5 | 单测 | select all hide test |
| AC-8.1 | R-23 | TASK-5 | 单测 | handle move test |
| AC-8.2 | R-24 | TASK-5 | 代码审查 | vibrator feedback |
| AC-8.3 | R-25 | TASK-5 | 代码审查 | magnifier show |
| AC-8.4 | R-25 | TASK-5 | 代码审查 | magnifier hide |
| AC-8.5 | R-25 | TASK-5 | 代码审查 | magnifier on long press |
| AC-8.6 | R-23 | TASK-5 | 单测 | external touch test |
| AC-8.7 | R-28 | TASK-5 | 单测 | handle crossover test |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | `IsSelectableAndCopy()` 三重门控：`textSelectable != UNSELECTABLE` 且 `copyOption != None` 且 `!textEffect_`（无跑马灯/动效），三者缺一不可。这是选择、复制、拖拽功能的统一入口守卫（`text_pattern.cpp:3816-3822`） | — | — |
| R-2 | 行为 | — | `textOverflow` 为 MARQUEE 模式时，`CalcCopyOption()` 强制将 `copyOption_` 设为 `CopyOptions.None`（`text_pattern.cpp:2969`），导致 R-1 门控失败，选择与复制完全禁用 | — | — |
| R-3 | 行为 | — | `TextSelectableMode` 控制选择能力和焦点行为：`SELECTABLE_UNFOCUSABLE`（可选不可焦）、`SELECTABLE_FOCUSABLE`（可选可焦）、`UNSELECTABLE`（不可选）。焦点能力仅在 `SELECTABLE_FOCUSABLE` 模式下启用（`text_pattern.cpp:3801-3813`） | — | — |
| R-4 | 行为 | — | 拖拽优先于重新选择：长按已选中文本区域时，`IsDraggable(localOffset)` 检查通过后设置 `gestureHub->SetIsTextDraggable(true)` 并直接返回，阻止 `InitSelectionOnLongPress` 执行（`text_pattern.cpp:718-727`） | — | — |
| R-5 | 行为 | — | `bindSelectionMenu` 与 `editMenuOptions` 互补关系：`bindSelectionMenu` 在 `OnUpdateSelectOverlayInfo` 中先执行（line 383），设置 `menuBuilder` 替换整个菜单 UI；`editMenuOptions` 后执行（line 387），设置 `onCreateMenuCallback` 定制系统菜单项。两者同时设置时，自定义 builder 优先渲染，`editMenuOptions` 回调仍挂载但不影响 builder 渲染 | — | — |
| R-6 | 行为 | — | `copyOption` 通过 `ACE_UPDATE_LAYOUT_PROPERTY(TextLayoutProperty, CopyOption, copyOption)` 存储，脏标记为 `PROPERTY_UPDATE_MEASURE`（`text_layout_property.h:207`） | — | — |
| R-7 | 行为 | — | 剪贴板写入三种格式：纯文本（`SetPlainText`）+ HTML（`SetHtmlText`，后台线程 `HtmlUtils::ToHtml` 异步生成）+ SpanString TLV 二进制（`EncodeTlv`），通过 `MultiTypeRecordImpl` 打包为 `PasteDataMix`，最终 `clipboard_->SetData(pasteData, copyOption)` 写入系统剪贴板（`text_pattern.cpp:1222-1248`） | — | — |
| R-8 | 行为 | — | 键盘快捷键支持：Ctrl+C 触发 `HandleOnCopy()`（`text_pattern.cpp:3632-3637`）；Ctrl+A 触发全选 `HandleSelectionChange(0, textSize)`（`text_pattern.cpp:3640-3648`）；Shift+方向键逐字符/逐行扩展选区（`text_pattern.cpp:3659-3680`） | — | — |
| R-9 | 行为 | — | `textSelectable` 存储为 `ACE_DEFINE_PROPERTY_ITEM_WITHOUT_GROUP(TextSelectableMode, TextSelectableMode, PROPERTY_UPDATE_MEASURE_SELF)`（`text_layout_property.h:213`），变更仅触发自身重测量 | — | — |
| R-10 | 行为 | — | 选择初始化使用词边界检测：`pManager_->GetWordBoundary(extend, start, end)` 获取 ICU 词边界（`text_pattern.cpp:344-364`）；若无词边界则回退到单字符簇选择 | — | — |
| R-11 | 行为 | — | 焦点模式下键盘选择：`SELECTABLE_FOCUSABLE` 模式下 Shift+Left/Right 逐字符移动选区末端，Shift+Up/Down 逐行移动（`text_pattern.cpp:3659-3680`） | — | — |
| R-12 | 行为 | — | 编程式选区 `selection(start, end)` 通过 `AfterLayoutTask` 延迟执行（`text_pattern.cpp:1589`），在布局完成后调用 `ActSetSelection(start, end)` 钳位并设置选区（`text_pattern.cpp:4999`） | — | — |
| R-13 | 行为 | — | `selectedBackgroundColor` 存储为 `ACE_DEFINE_PROPERTY_ITEM_WITHOUT_GROUP(SelectedBackgroundColor, Color, PROPERTY_UPDATE_MEASURE_SELF)`（`text_layout_property.h:211`）；传入 alpha=255 时自动降为 20% 不透明度（`js_text.cpp:459`） | — | — |
| R-14 | 行为 | — | `caretColor` 存储为 `CursorColor`（`text_layout_property.h:210`），实际用于选择手柄颜色（`text_select_overlay.cpp:386` 设置 `handlerColor`），Text 组件为只读无可见光标 | — | — |
| R-15 | 行为 | — | 拖拽初始化在 `InitCopyOption()` 中完成：当 `IsSelectableAndCopy()` 且 `host->IsDraggable()` 且 `!shiftFlag_` 时调用 `InitDragEvent()`（`text_pattern.cpp:3085`） | — | — |
| R-16 | 行为 | — | 拖拽数据格式区分：有 Span 子节点走 `OnDragStart()`（UDMF 含纯文本 + SpanString + 图片记录，`text_pattern.cpp:3877-3895`）；无子节点走 `OnDragStartNoChild()`（仅纯文本，`text_pattern.cpp:3960-3997`） | — | — |
| R-17 | 行为 | — | `selectedDragPreviewStyle` 仅含 `color` 字段（`SelectedDragPreviewStyle` 接口），存储为 `ACE_DEFINE_PROPERTY_ITEM_WITHOUT_GROUP(SelectedDragPreviewStyle, Color, PROPERTY_UPDATE_MEASURE)`（`text_layout_property.h:142`），通过 `TextDragInfo.dragBackgroundColor` 传递给拖拽预览渲染器 | — | — |
| R-18 | 行为 | — | `bindSelectionMenu` 以 `(TextSpanType, TextResponseType)` 为 key 存储在 `selectionMenuMap_` 中（`text_pattern.h:629`）；传 null builder 时移除对应条目 | — | — |
| R-19 | 行为 | — | 菜单查找使用 4 级回退：精确匹配 `(spanType, responseType)` → `(spanType, NONE)` → `(NONE, responseType)` → `(NONE, NONE)`（`text_pattern.cpp:6897-6917`） | — | — |
| R-20 | 行为 | — | `SelectionMenuOptions` 回调通过 `OnHandleSelectionMenuCallback` 分发，传入当前选区范围 `(start, end)`（`text_pattern.cpp:6953-6974`） | — | — |
| R-21 | 行为 | — | `editMenuOptions` 回调通过 `BaseTextSelectOverlay::OnUpdateOnCreateMenuCallback` 挂载到 `SelectOverlayInfo.onCreateCallback`（`base_text_select_overlay.h:251-272`） | — | — |
| R-22 | 行为 | — | Text 系统默认菜单项：`showCopy = true`（选区非空时）、`showCopyAll = true`（未全选时）；`showCut = false`、`showPaste = false`（只读组件）（`text_select_overlay.cpp:348-375`） | — | — |
| R-23 | 行为 | — | 选择手柄拖动通过 `UpdateSelectorOnHandleMove` 更新选区：第一手柄更新 `baseOffset`，第二手柄更新 `destinationOffset`（`text_select_overlay.cpp:210-222`） | — | — |
| R-24 | 行为 | — | 手柄拖动时每次字符索引变化触发振动反馈（`StartVibratorByIndexChange()`） | — | — |
| R-25 | 行为 | — | 放大镜（Magnifier）在三个场景显示：(1) 长按初始选择（`text_pattern.cpp:744-747`）；(2) 手指拖动扩展选区（`text_pattern.cpp:8156-8160`）；(3) 手柄拖动（`text_select_overlay.cpp:175-178`）。释放手指或手柄时隐藏（`RemoveMagnifierFrameNode()`） | — | — |
| R-26 | 异常 | — | `selection(start, end)` 当 `start >= end` 时选区无效，不显示选中效果 | — | — |
| R-27 | 异常 | — | `selection(start, end)` 当索引超出 `[0, textLength]` 时自动钳位到合法范围（`text_pattern.cpp:4999`） | — | — |
| R-28 | 异常 | — | 选择手柄可以交叉（第一手柄越过第二手柄位置），`GetTextStart()`/`GetTextEnd()` 使用 `std::min`/`std::max` 保证选区渲染始终正确 | — | — |
| R-29 | 异常 | — | 文本内容为空时，长按、双击、鼠标拖选均不触发选择（各入口有 `HasContent()` 检查） | — | — |
| R-30 | 异常 | — | `copyOption` 传入非法枚举值时，JS Bridge 层做 range check，超出范围使用 `CopyOptions::None`（`js_text.cpp:1050`） | — | — |
| R-31 | 异常 | — | 容器选择场景（`selectionChild_` 非空）时，`GetOrCreateMagnifier()` 返回 nullptr，不显示放大镜（`text_pattern.cpp:9295-9308`） | — | — |
| R-32 | 恢复 | — | 拖拽失败恢复：当 `DragRet != DRAG_SUCCESS` 时，选区恢复到拖拽前的 `recoverStart_`/`recoverEnd_` 范围，重新显示选择覆盖层（`text_pattern.cpp:4067-4076, 4090-4096`） | — | — |
| R-33 | 恢复 | — | 触摸取消恢复：`DoTextSelectionTouchCancel()` 时移除放大镜、重置选区（`text_pattern.cpp:8382-8386`） | — | — |
| R-34 | 恢复 | — | 组件卸载清理：Pattern detach 时清理放大镜和选择覆盖层（`text_pattern.cpp:127-128`） | — | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~AC-1.6, R-1, R-2 | 单测 | copyOption 各枚举值下选择/复制功能开关、MARQUEE 模式强制禁用、三重门控逻辑 |
| VM-2 | AC-1.7~AC-1.9, R-7 | 单测 + 代码审查 | 剪贴板写入三种格式（纯文本/HTML/SpanString TLV）、异步 HTML 生成 |
| VM-3 | AC-2.1~AC-2.4, R-3 | 单测 | TextSelectableMode 三种模式下的选择能力和焦点行为 |
| VM-4 | AC-2.5~AC-2.8, R-10, R-11 | 单测 | 长按/双击/鼠标拖选/键盘扩展选区的触发和词边界检测 |
| VM-5 | AC-3.1~AC-3.5, R-12 | 单测 | 编程式选区设置、钳位、守卫条件、AfterLayoutTask 延迟 |
| VM-6 | AC-4.1~AC-4.6, R-13, R-14 | 单测 | selectedBackgroundColor alpha 自动降低、caretColor 映射到选择手柄 |
| VM-7 | AC-5.1~AC-5.9, R-4, R-15~R-17 | 单测 + 代码审查 | 拖拽优先于重选、UDMF 数据格式、拖拽预览样式 |
| VM-8 | AC-6.1~AC-6.7, R-18~R-20 | 单测 | bindSelectionMenu 绑定/解绑/4 级回退查找/回调 |
| VM-9 | AC-7.1~AC-7.6, R-5, R-21, R-22 | 单测 + 代码审查 | editMenuOptions 定制、与 bindSelectionMenu 互补、系统菜单项可见性 |
| VM-10 | AC-8.1~AC-8.7, R-23~R-25, R-28 | 单测 + 代码审查 | 手柄拖动/放大镜/振动反馈/手柄交叉 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `copyOption(value: CopyOptions)` | Public | 设置文本复制权限 | AC-1.1~AC-1.4 |
| `selection(selectionStart: number, selectionEnd: number)` | Public | 编程式设置选区 | AC-3.1~AC-3.5 |
| `textSelectable(mode: TextSelectableMode)` | Public | 控制文本可选择性和焦点行为 | AC-2.1~AC-2.4 |
| `selectedBackgroundColor(color: ResourceColor)` | Public | 设置选中文本背景色 | AC-4.1~AC-4.3 |
| `caretColor(color: ResourceColor)` | Public | 设置选择手柄颜色 | AC-4.4~AC-4.6 |
| `draggable(value: boolean)` | Public (CommonMethod) | 启用/禁用选中文本拖拽 | AC-5.1~AC-5.3 |
| `selectedDragPreviewStyle(value: SelectedDragPreviewStyle)` | Public | 设置拖拽预览背景色 | AC-5.7~AC-5.9 |
| `bindSelectionMenu(spanType, content, responseType, options?)` | Public | 绑定自定义选择菜单 | AC-6.1~AC-6.7 |
| `editMenuOptions(editMenu: EditMenuOptions)` | Public | 定制系统选择菜单项 | AC-7.1~AC-7.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| `CopyOptions.CROSS_DEVICE` | 废弃（@deprecated since 12） | AC-1.2 |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** copyOption @since 9（动态版）；textSelectable/bindSelectionMenu @since 12；selectedBackgroundColor/caretColor @since 14；selectedDragPreviewStyle @since 23；onWillCopy @since 26.0.0（不在本 spec 范围）
- **API 版本号策略:** 各属性按实际引入版本标注 @since；CopyOptions.CROSS_DEVICE @deprecated since 12；静态版所有属性 @since 23 static

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 三重门控不可绕过 | `IsSelectableAndCopy()` 是选择/复制/拖拽的统一入口守卫，任何路径都不可跳过 | AC-1.6, AC-3.4, AC-5.1 |
| 剪贴板写入必须异步 | HTML 格式通过后台线程生成，再 Post 回 UI 线程写入剪贴板，避免 UI 阻塞 | AC-1.9 |
| 拖拽依赖选区 | `IsDraggable()` 要求触摸点位于已选中区域内（`LocalOffsetInSelectedArea`），无选区时不可拖拽 | AC-5.2, AC-5.3 |
| caretColor 非光标用途 | Text 是只读组件，`CursorColor` 属性仅用于选择手柄着色，不渲染可见光标 | AC-4.4~AC-4.6 |
| bindSelectionMenu 无 BUILDER 类型 | JS 层 TextSpanType 枚举值 3 映射到 C++ `NONE`（通配），不映射到 `BUILDER` | AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | HTML 生成在后台线程异步执行，不阻塞 UI 帧率 | 代码审查 | AsyncHandleOnCopySpanStringHtml 使用 TaskExecutor::BACKGROUND |
| 性能 | 拖拽预览圆角半径 18vp（2in1 设备 8vp），`TEXT_DRAG_RADIUS` 常量 | 代码审查 | text_drag_pattern.h |
| 内存 | 选择覆盖层（selectOverlay_）和剪贴板（clipboard_）懒初始化，未使用时不分配 | 代码审查 | GetSelectOverlay() / InitCopyOption() 延迟创建 |
| 安全 | `CopyOptions` 限制剪贴板共享范围（InApp/Local/Distributed），由系统剪贴板服务强制执行 | 单测 | clipboard scope enforcement |
| 可靠性 | 拖拽失败后选区自动恢复到拖拽前状态 | 单测 | R-32 |
| 问题定位 | 选区变化通过 `FireOnSelectionChange(start, end)` 上报（不在本 spec 范围，但可用于调试） | 代码审查 | text_pattern.cpp:7057 |

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
| 无障碍 | 是 | 选择菜单项通过系统无障碍框架上报 | 系统菜单/自定义菜单 |
| 大字体 | 是 | 字体缩放不影响选择功能，手柄和放大镜尺寸独立 | 全部 |
| 深色模式 | 是 | selectedBackgroundColor/caretColor/selectedDragPreviewStyle 需配合主题色适配 | AC-4.1, AC-4.4, AC-5.8 |
| 多窗口/分屏 | 是 | 选择覆盖层需跟随窗口变换（Transform-aware），`base_text_select_overlay` 处理坐标转换 | AC-8.1 |
| 多用户 | N/A | 无多用户差异 | — |
| 版本升级 | 是 | CopyOptions.CROSS_DEVICE @deprecated since 12；各属性 @since 版本差异见兼容性声明 | AC-1.2 |
| 生态兼容 | 是 | 三通道入口（ArkTS 动态版/静态版/C API）能力对等性见 C API 映射表 | 全部 |

## 行为场景（Gherkin）

```gherkin
Feature: Text 选择与复制
  作为 ArkUI 开发者
  我想要控制 Text 组件的选择与复制行为
  以便提供安全且可定制的文本交互体验

  Scenario: 默认状态不可复制
    Given Text 组件未设置 copyOption
    When 用户长按文本
    Then 文本不可选择
    And 无选择菜单显示

  Scenario: 启用复制后长按选择
    Given Text 组件设置 copyOption(CopyOptions.InApp)
    And textSelectable 未设置（默认 SELECTABLE_UNFOCUSABLE）
    When 用户长按文本中的某个词
    Then 该词被选中（词边界检测）
    And 显示选择手柄和放大镜
    And 放大镜跟随手指位置

  Scenario: 选择手柄拖动扩展选区
    Given 文本已选中一个词
    When 用户拖动第二个选择手柄向右移动
    Then 选区实时扩展到手柄对应的字符位置
    And 每次字符索引变化时触发振动反馈
    And 放大镜跟随手柄位置
    When 用户释放手柄
    Then 放大镜消失
    And 选择菜单显示

  Scenario: Ctrl+C 复制选中文本
    Given 文本有选中内容
    And copyOption 为 CopyOptions.LocalDevice
    When 用户按下 Ctrl+C
    Then 选中文本写入系统剪贴板（纯文本 + HTML + SpanString TLV）
    And 剪贴板作用域为 LocalDevice

  Scenario: MARQUEE 模式禁用选择
    Given Text 组件设置 textOverflow(MARQUEE)
    And copyOption 为 CopyOptions.InApp
    When 用户长按文本
    Then 文本不可选择（MARQUEE 强制 copyOption=None）

  Scenario: 编程式选区设置
    Given Text 组件设置 copyOption(CopyOptions.InApp)
    When 调用 selection(5, 15)
    Then 第 5 到第 15 个字符被选中
    And 显示选择手柄

  Scenario Outline: textSelectable 模式行为
    Given Text 组件设置 copyOption(CopyOptions.InApp)
    And textSelectable 设置为 <mode>
    When 用户长按文本
    Then 选择结果为 <result>

    Examples:
      | mode                     | result                      |
      | SELECTABLE_UNFOCUSABLE   | 可选择，组件不可获取焦点     |
      | SELECTABLE_FOCUSABLE     | 可选择，组件可获取焦点       |
      | UNSELECTABLE             | 不可选择                     |

  Scenario: 拖拽选中文本
    Given 文本已选中且 draggable(true)
    When 用户长按已选中文本区域
    Then 触发拖拽（不触发重新选择）
    And 显示带圆角背景的拖拽预览缩略图

  Scenario: 自定义选择菜单
    Given bindSelectionMenu(TEXT, customBuilder, LONG_PRESS)
    When 用户长按选中纯文本
    Then 显示 customBuilder 渲染的自定义菜单
    And onAppear 回调被触发，参数为 (selectionStart, selectionEnd)

  Scenario: 编辑菜单定制
    Given editMenuOptions 设置了 onCreateMenu 和 onMenuItemClick
    And 无 bindSelectionMenu 绑定
    When 选择菜单显示
    Then onCreateMenu 被调用，接收系统默认菜单项
    And 开发者可添加/移除/重排菜单项
    When 用户点击自定义菜单项
    Then onMenuItemClick 被调用
    And 返回 true 时拦截默认行为
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Text 组件选择与复制的完整实现，包括 copyOption、selection、textSelectable、selectedBackgroundColor、caretColor、draggable、selectedDragPreviewStyle、bindSelectionMenu、editMenuOptions"
```

**关键文档：**
- `frameworks/core/components_ng/pattern/text/text_pattern.cpp` — 选择/复制/拖拽核心逻辑
- `frameworks/core/components_ng/pattern/text/text_select_overlay.cpp` — 选择覆盖层（手柄/菜单/放大镜）
- `frameworks/core/components_ng/pattern/text/text_layout_property.h` — 属性存储定义
- `frameworks/bridge/declarative_frontend/jsview/js_text.cpp` — JS Bridge 入口
- `interfaces/native/native_node.h` — C API 属性枚举
