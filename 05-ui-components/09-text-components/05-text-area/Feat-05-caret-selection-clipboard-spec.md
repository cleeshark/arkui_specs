# 特性规格

> Func-05-09-05-Feat-05 光标选择与剪贴板：固化 caretColor/caretStyle、selectedBackgroundColor、editMenuOptions、onCopy/onWillCopy/onCut/onWillCut/onPaste、copyOption、onTextSelectionChange/onContentScroll、selectedDragPreviewStyle、enableSelectedDataDetector、scrollBarColor、barState、selectionMenuHidden 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 光标选择与剪贴板 (Caret, Selection & Clipboard) |
| 特性编号 | Func-05-09-05-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 @since 7（onPaste）、@since 8（onCopy/onCut）、@since 9（copyOption）、@since 10（enableKeyboardOnFocus/maxLength/showCounter/style/barState/selectionMenuHidden/onTextSelectionChange/onContentScroll/onEditChange）、@since 12（caretStyle/selectedBackgroundColor）、@since 22（scrollBarColor/enableSelectedDataDetector/onWillAttachIME）、@since 23（selectedDragPreviewStyle/textDirection）、@since 26（onWillCopy/onWillCut）；静态 @since 23 static |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | caretColor/caretStyle | caretColor 驱动光标+手柄+拖拽手柄颜色（API12 起）；caretStyle 拆为 width+color |
| ADDED | selectedBackgroundColor | 不透明输入自动 ChangeOpacity(0.2) |
| ADDED | editMenuOptions | 自定义选区菜单（onCreateMenu/onMenuItemClick/onPrepareMenu） |
| ADDED | onCopy/onWillCopy/onCut/onWillCut/onPaste | onWillCopy/onWillCut 返回 false 取消（@since 26） |
| ADDED | copyOption | None 禁用复制/剪切/分享/拖拽 |
| ADDED | onTextSelectionChange/onContentScroll | 选区变化/内容滚动偏移报告 |
| ADDED | selectedDragPreviewStyle | 拖拽预览背景色 |
| ADDED | enableSelectedDataDetector | 选中文本 AI 实体检测 |
| ADDED | scrollBarColor | 滚动条 thumb 颜色 |
| ADDED | barState | Auto/On/Off 滚动条可见性 |
| ADDED | selectionMenuHidden | true 隐藏系统选区菜单 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/05-text-area/design.md` | Baselined |

---

## 用户故事

### US-1: 设置光标与手柄颜色

**作为** 应用开发者,
**我想要** 通过 caretColor/selectedBackgroundColor 自定义光标与选区手柄颜色,
**以便** 适配应用主题视觉风格。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.caretColor(value)` THEN 写 paint CursorColor + CaretColorFlagByUser=true；光标用此色绘制（`text_field_model_ng.cpp:452`；`text_field_overlay_modifier.cpp:361`） | 正常 |
| AC-1.2 | WHEN 未设置 caretColor THEN 使用主题 cursorColor_（Brand token）；主题切换时 CaretColorFlagByUser=false 回退主题（`text_field_pattern.cpp:6379-6382`） | 异常 |
| AC-1.3 | WHEN 调用 `.caretStyle({ width, color })` THEN 拆写 CursorWidth(paint) + CursorColor(paint)；color 经 SetCaretColor，width 经 SetCaretWidth（`text_area_static_modifier.cpp:227`；`text_field_model_ng.cpp:464`） | 正常 |
| AC-1.4 | WHEN API>=12 THEN 手柄颜色=光标颜色（`text_field_select_overlay.cpp:379-380,879-885`） | 正常 |
| AC-1.5 | WHEN 拖拽选中文本 THEN CreateTextDragInfo 用 caretColor 作为 handleColor（`text_field_pattern.cpp:3110`） | 正常 |

### US-2: 设置选区背景色

**作为** 应用开发者,
**我想要** 通过 selectedBackgroundColor 控制选中文本背景色,
**以便** 视觉区分选区与未选区。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.selectedBackgroundColor(value)` 且 value 不透明(alpha=255) THEN ChangeOpacity(0.2) 后存储（`text_field_model_static.cpp:259-263`） | 正常 |
| AC-2.2 | WHEN value 已设置透明度 THEN 按原值使用 | 边界 |
| AC-2.3 | WHEN 未设置 THEN 使用主题 selectedColor_（`text_field_paint_method.cpp:190`） | 异常 |
| AC-2.4 | WHEN API>=26 THEN 额外设 SelectedBackgroundColorFlagByUser=true（`text_field_model_ng.cpp:485-487`） | 边界 |

### US-3: 自定义选区菜单

**作为** 应用开发者,
**我想要** 通过 selectionMenuOptions 自定义选区菜单项,
**以便** 控制复制/粘贴/全选等菜单的显示与行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.editMenuOptions({ onCreateMenu, onMenuItemClick, onPrepareMenu })` THEN 注册三个回调到 BaseTextSelectOverlay（`text_area_static_modifier.cpp:694`；`base_text_select_overlay.h:429-431`） | 正常 |
| AC-3.2 | WHEN 选区菜单显示 THEN onCreateMenu 回调被调用，返回自定义菜单项（text/icon/action）（`base_text_select_overlay.h:265-286`） | 正常 |
| AC-3.3 | WHEN 点击菜单项 THEN onMenuItemClick 回调返回 bool（是否消费）（`text_area_static_modifier.cpp:718-731`） | 正常 |
| AC-3.4 | WHEN 设置 onPrepareMenu THEN 菜单显示前 onPrepareMenu 回调被调用（`base_text_select_overlay.h:283`） | 正常 |
| AC-3.5 | WHEN editMenuOptions 传 undefined THEN 清除三个回调（传 nullptr）（`text_area_static_modifier.cpp:745`） | 边界 |

### US-4: 剪贴板回调

**作为** 应用开发者,
**我想要** 通过 onCut/onCopy/onPaste 监听剪贴板操作,
**以便** 拦截或感知剪贴行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.onCopy(callback)` THEN 注册 onCopy_ 回调（`text_field_model_ng.cpp:703`） | 正常 |
| AC-4.2 | WHEN 复制操作触发 THEN HandleOnCopy：检查 copyOption!=None + 有选区 + FireOnWillCopy(value)→若 true 则 clipboard SetData + FireOnCopy（`text_field_pattern.cpp:2361-2397`） | 正常 |
| AC-4.3 | WHEN 调用 `.onWillCopy(callback)` (@since 26) THEN 注册 onWillCopy_（Callback<string,boolean>）；返回 false 取消复制（`text_area_static_modifier.cpp:350`） | 正常 |
| AC-4.4 | WHEN onWillCopy 返回 false THEN 跳过 clipboard SetData（`text_field_pattern.cpp:2387`） | 边界 |
| AC-4.5 | WHEN 调用 `.onCut(callback)` THEN 注册 onCut_（`text_field_model_ng.cpp:717`） | 正常 |
| AC-4.6 | WHEN 剪切操作触发 THEN HandleOnCut：检查 + FireOnWillCut→若 true 则 clipboard SetData + DeleteRange + FireOnCut（`text_field_pattern.cpp:2712-2755`） | 正常 |
| AC-4.7 | WHEN onWillCut 返回 false THEN 隐藏菜单并 return（不删除）（`text_field_pattern.cpp:2739-2746`） | 边界 |
| AC-4.8 | WHEN 调用 `.onPaste(callback)` THEN 注册 onPasteWithEvent_（`text_field_model_ng.cpp:731`） | 正常 |
| AC-4.9 | WHEN 粘贴操作触发 THEN HandleOnPaste→HandleOnPasteCommon：FireOnPasteWithEvent→若 preventDefault 则跳过插入；否则 AddInsertCommand(PASTE)（`text_field_pattern.cpp:2444-2463`） | 正常 |
| AC-4.10 | WHEN onPaste 回调调用 event.preventDefault() THEN 跳过插入、关闭覆盖层、重置手柄、启动光标闪烁（`text_field_pattern.cpp:2455-2461`） | 边界 |

### US-5: 复制权限控制

**作为** 应用开发者,
**我想要** 通过 copyOption 控制复制权限,
**以便** 限制或允许用户复制文本内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.copyOption(CopyOptions.None)` THEN 禁用复制/剪切/分享/拖拽（`text_field_pattern.cpp:2368`；`text_field_pattern.cpp:3045-3058`） | 正常 |
| AC-5.2 | WHEN copyOption=None THEN HandleOnCopy/HandleOnCut 早退；InitDragEvent 不注册拖拽 | 边界 |
| AC-5.3 | WHEN copyOption=LocalDevice（默认） THEN 允许本设备复制/剪切/拖拽 | 正常 |
| AC-5.4 | WHEN copyOption=Distributed THEN 允许跨设备分布式剪贴板 | 正常 |

### US-6: 选区变化与内容滚动回调

**作为** 应用开发者,
**我想要** 通过 onTextSelectionChange/onScroll 监听选区变化与内容滚动,
**以便** 响应用户选区与滚动操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.onTextSelectionChange(callback)` THEN 注册 onSelectionChange_（`text_field_model_ng.cpp:667`） | 正常 |
| AC-6.2 | WHEN 选区 start/end 变化（手柄拖动/光标移动/全选/编程式选区）THEN TextSelectController 比较 prev vs new index，变化时 FireOnSelectionChange(min,max)（`text_select_controller.cpp:711-734`） | 正常 |
| AC-6.3 | WHEN 调用 `.onContentScroll(callback)` THEN 注册 onScrollChangeEvent_（`text_field_model_ng.cpp:689`） | 正常 |
| AC-6.4 | WHEN 内容偏移变化（滚动/手柄自动滚动）THEN UpdateOverlayModifier 计算 totalOffsetX/Y，变化时 FireOnScrollChangeEvent（`text_field_paint_method.cpp:75-93`） | 正常 |
| AC-6.5 | WHEN totalOffset 未变化 THEN 不触发回调（去重） | 边界 |

### US-7: 拖拽预览与数据检测

**作为** 应用开发者,
**我想要** 通过 dragPreviewStyle/dataDetectorConfig 配置拖拽预览与数据检测,
**以便** 自定义拖拽外观与自动识别文本中的链接/邮箱等。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.selectedDragPreviewStyle(value)` (@since 23) THEN 设 SelectedDragPreviewStyle(Color)；CreateTextDragInfo 用作 dragBackgroundColor（`text_field_pattern.cpp:3131-3132`） | 正常 |
| AC-7.2 | WHEN 未设置且 API>=26 THEN 回退主题 GetDragBackgroundColor（`text_field_pattern.cpp:3133-3139`） | 边界 |
| AC-7.3 | WHEN 调用 `.enableSelectedDataDetector(true)` (@since 22/24) THEN 设 selectDetectEnabled_=true；选区 AI 实体检测启用（`text_field_pattern.cpp:5175-5181`） | 正常 |
| AC-7.4 | WHEN 选中文本含 AI 实体 THEN PrepareAIMenuOptions 扫描 aiSpanMap 构建菜单；UpdateAIMenuOptions 仅 copyOption 非 None 时执行（`text_field_pattern.cpp:3983-4020`） | 正常 |
| AC-7.5 | WHEN enableSelectedDataDetector=false THEN AI 菜单不显示 | 边界 |

### US-8: 滚动条与菜单控制

**作为** 应用开发者,
**我想要** 通过 barState/scrollBarColor/selectionMenuHidden 控制滚动条可见性与选区菜单,
**以便** 管理滚动条显示及菜单弹出策略。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.barState(BarState.Auto)` THEN 设 DisplayMode=AUTO（默认）；scrollBarVisible_=true（`text_field_model_ng.cpp:849`；`text_field_pattern.cpp:4254-4259`） | 正常 |
| AC-8.2 | WHEN barState=Off THEN scrollBarVisible_=false（内部滚动启用但条隐藏）（`text_field_pattern.cpp:4254`） | 边界 |
| AC-8.3 | WHEN 调用 `.scrollBarColor(value)` (@since 22/24) THEN 设 ScrollBarColor；thumb 用此色（`text_field_free_scroller.cpp:243-258`） | 正常 |
| AC-8.4 | WHEN 未设置 scrollBarColor THEN 默认 Color(0x66182431)（`text_field_layout_property.h:164`） | 异常 |
| AC-8.5 | WHEN 调用 `.selectionMenuHidden(true)` THEN 设 SelectionMenuHidden=true；系统选区菜单不显示（`text_field_select_overlay.cpp:322,334-340`） | 正常 |
| AC-8.6 | WHEN selectionMenuHidden=true + 鼠标右键 THEN PreProcessOverlay return false（右键菜单不显示）（`text_field_select_overlay.cpp:65-69`） | 边界 |
| AC-8.7 | WHEN selectionMenuHidden=false（默认） THEN 长按/双击/三击/右击显示系统选区菜单 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-5 | TASK-05 | XTS caretColor/caretStyle | text_field_model_ng.cpp:452 |
| AC-2.1~2.4 | R-6~R-9 | TASK-05 | XTS selectedBackgroundColor | text_field_model_static.cpp:259 |
| AC-3.1~3.5 | R-10~R-14 | TASK-05 | XTS editMenuOptions | base_text_select_overlay.h:429 |
| AC-4.1~4.10 | R-15~R-24 | TASK-05 | XTS 剪贴板回调 | text_field_pattern.cpp:2361 |
| AC-5.1~5.4 | R-25~R-28 | TASK-05 | XTS copyOption | text_field_pattern.cpp:2368 |
| AC-6.1~6.5 | R-29~R-33 | TASK-05 | XTS 选区/滚动回调 | text_select_controller.cpp:711 |
| AC-7.1~7.5 | R-34~R-38 | TASK-05 | XTS 拖拽预览/数据检测 | text_field_pattern.cpp:3131 |
| AC-8.1~8.7 | R-39~R-45 | TASK-05 | XTS barState/scrollBarColor/selectionMenuHidden | text_field_pattern.cpp:4254 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 caretColor | 写 CursorColor+FlagByUser | 主题默认 Brand | AC-1.1,1.2 |
| R-2 | 行为 | 设置 caretStyle | 拆写 CursorWidth+CursorColor | — | AC-1.3 |
| R-3 | 行为 | API>=12 手柄颜色 | = 光标颜色 | — | AC-1.4 |
| R-4 | 行为 | 拖拽选中文本 | handleColor=caretColor | — | AC-1.5 |
| R-6 | 行为 | 设置 selectedBackgroundColor(不透明) | ChangeOpacity(0.2) | alpha=255 触发 | AC-2.1,2.2 |
| R-7 | 边界 | 未设置 | 主题 selectedColor_ | — | AC-2.3 |
| R-8 | 边界 | API>=26 | 额外设 FlagByUser | — | AC-2.4 |
| R-10 | 行为 | 设置 editMenuOptions | 注册三回调 | — | AC-3.1 |
| R-11 | 行为 | 选区菜单显示 | onCreateMenu 返回自定义项 | — | AC-3.2 |
| R-12 | 行为 | 点击菜单项 | onMenuItemClick 返回 bool | — | AC-3.3 |
| R-13 | 行为 | 设置 onPrepareMenu | 菜单前回调 | — | AC-3.4 |
| R-14 | 边界 | editMenuOptions=undefined | 清除回调 | — | AC-3.5 |
| R-15 | 行为 | 设置 onCopy | 注册 onCopy_ | — | AC-4.1 |
| R-16 | 行为 | 复制触发 | HandleOnCopy：copyOption 检查+WillCopy+SetData+Copy | — | AC-4.2 |
| R-17 | 行为 | 设置 onWillCopy(@since 26) | 注册 WillCopy；返回 false 取消 | — | AC-4.3,4.4 |
| R-19 | 行为 | 剪切触发 | HandleOnCut：WillCut+SetData+Delete+Cut | — | AC-4.6 |
| R-20 | 边界 | onWillCut 返回 false | 隐藏菜单不删除 | — | AC-4.7 |
| R-21 | 行为 | 设置 onPaste | 注册 onPasteWithEvent_ | — | AC-4.8 |
| R-22 | 行为 | 粘贴触发 | FireOnPasteWithEvent→preventDefault 则跳过 | — | AC-4.9 |
| R-24 | 边界 | preventDefault | 跳过插入+关覆盖+重置手柄+闪烁 | — | AC-4.10 |
| R-25 | 行为 | 设置 copyOption=None | 禁用复制/剪切/分享/拖拽 | — | AC-5.1,5.2 |
| R-26 | 行为 | copyOption=LocalDevice | 允许本设备 | 默认 | AC-5.3 |
| R-27 | 行为 | copyOption=Distributed | 允许分布式 | — | AC-5.4 |
| R-29 | 行为 | 设置 onTextSelectionChange | 注册 onSelectionChange_ | — | AC-6.1 |
| R-30 | 行为 | 选区变化 | FireOnSelectionChange(min,max) | 去重 | AC-6.2 |
| R-31 | 行为 | 设置 onContentScroll | 注册 onScrollChangeEvent_ | — | AC-6.3 |
| R-32 | 行为 | 内容偏移变化 | FireOnScrollChangeEvent(x,y) | 去重 | AC-6.4,6.5 |
| R-34 | 行为 | 设置 selectedDragPreviewStyle | 用作 dragBackgroundColor | @since 23 | AC-7.1 |
| R-35 | 边界 | 未设+API>=26 | 回退主题 GetDragBackgroundColor | — | AC-7.2 |
| R-36 | 行为 | 设置 enableSelectedDataDetector | selectDetectEnabled_=true | @since 22/24 | AC-7.3 |
| R-37 | 行为 | 选区含 AI 实体 | PrepareAIMenuOptions+UpdateAIMenuOptions | 仅 copyOption 非 None | AC-7.4 |
| R-38 | 边界 | enableSelectedDataDetector=false | AI 菜单不显示 | — | AC-7.5 |
| R-39 | 行为 | 设置 barState=Auto | DisplayMode=AUTO | 默认 | AC-8.1 |
| R-40 | 边界 | barState=Off | scrollBarVisible_=false（内部滚动启用） | — | AC-8.2 |
| R-41 | 行为 | 设置 scrollBarColor | thumb 用此色 | 默认 0x66182431 | AC-8.3,8.4 |
| R-43 | 行为 | 设置 selectionMenuHidden=true | 系统菜单不显示 | — | AC-8.5 |
| R-44 | 边界 | selectionMenuHidden+鼠标右键 | PreProcessOverlay return false | — | AC-8.6 |
| R-45 | 行为 | selectionMenuHidden=false | 长按/双击/三击/右击显示菜单 | 默认 | AC-8.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.x caretColor/caretStyle | XTS + Inspector | 光标/手柄颜色一致性 |
| VM-2 | AC-2.x selectedBackgroundColor | XTS + 透明度 | alpha=255→0.2 |
| VM-3 | AC-3.x editMenuOptions | XTS + 菜单 | 自定义菜单项/拦截 |
| VM-4 | AC-4.x 剪贴板回调 | XTS + 剪贴板 | WillCopy/WillCut 拦截；preventDefault |
| VM-5 | AC-5.x copyOption | XTS + 权限 | None 禁用 |
| VM-6 | AC-6.x 选区/滚动回调 | XTS + 事件 | 选区变化去重；偏移报告 |
| VM-7 | AC-7.x 拖拽预览/数据检测 | XTS + AI | dragBackgroundColor；AI 菜单 |
| VM-8 | AC-8.x barState/scrollBarColor/selectionMenuHidden | XTS + 滚动条 | 可见性；thumb 颜色；菜单隐藏 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| caretColor(value) | Public | ResourceColor | this | 无 | 光标颜色 | AC-1.x |
| caretStyle(value) | Public | CaretStyle | this | 无 | 光标样式 | AC-1.3 |
| selectedBackgroundColor(value) | Public | ResourceColor | this | 无 | 选区背景 | AC-2.x |
| editMenuOptions(editMenu) | Public | EditMenuOptions | this | 无 | 自定义菜单 | AC-3.x |
| onCopy(callback) | Public | function | this | 无 | 复制回调 | AC-4.1 |
| onWillCopy(callback) | Public | Callback<string,boolean> | this | 无 | 复制前拦截 | AC-4.3 |
| onCut(callback) | Public | function | this | 无 | 剪切回调 | AC-4.5 |
| onWillCut(callback) | Public | Callback<string,boolean> | this | 无 | 剪切前拦截 | AC-4.7 |
| onPaste(callback) | Public | function(value,PasteEvent) | this | 无 | 粘贴回调 | AC-4.8 |
| copyOption(value) | Public | CopyOptions | this | 无 | 复制权限 | AC-5.x |
| onTextSelectionChange(callback) | Public | function(int,int) | this | 无 | 选区变化 | AC-6.1 |
| onContentScroll(callback) | Public | function(double,double) | this | 无 | 内容滚动 | AC-6.3 |
| selectedDragPreviewStyle(value) | Public | SelectedDragPreviewStyle | this | 无 | 拖拽预览 | AC-7.1 |
| enableSelectedDataDetector(enable) | Public | boolean | this | 无 | 数据检测 | AC-7.3 |
| scrollBarColor(thumbColor) | Public | ColorMetrics | this | 无 | 滚动条颜色 | AC-8.3 |
| barState(value) | Public | BarState | this | 无 | 滚动条状态 | AC-8.1 |
| selectionMenuHidden(value) | Public | boolean | this | 无 | 菜单隐藏 | AC-8.5 |

> **SDK 交叉验证：** 均经 `textArea.static.d.ets` 与 `text_area.d.ts` 核对。onWillCopy/onWillCut @since 26.0.0 static。

## 接口规格

### 接口定义

| 接口 | 签名概要 | 开放范围 | 关联 AC |
|------|----------|----------|---------|
| 光标样式 | caretColor/caretStyle | Public | AC-1.x |
| 选区背景 | selectedBackgroundColor | Public | AC-2.x |
| 选区菜单 | editMenuOptions | Public | AC-3.x |
| 剪贴板 | onCopy/onWillCopy/onCut/onWillCut/onPaste | Public | AC-4.x |
| 复制权限 | copyOption | Public | AC-5.x |
| 选区滚动回调 | onTextSelectionChange/onContentScroll | Public | AC-6.x |
| 拖拽数据 | selectedDragPreviewStyle/enableSelectedDataDetector | Public | AC-7.x |
| 滚动条菜单 | barState/scrollBarColor/selectionMenuHidden | Public | AC-8.x |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| selectedBackgroundColor | ResourceColor | 是 | 主题 selectedColor_ | 不透明自动 0.2 |
| copyOption | CopyOptions | 是 | LocalDevice | None 禁用复制/剪切/拖拽 |
| barState | BarState | 是 | Auto | Off 内部滚动启用但条隐藏 |
| selectionMenuHidden | boolean | 是 | false | — |
| scrollBarColor | ColorMetrics | 是 | 0x66182431 | — |

## 兼容性声明

- **已有 API 行为变更:** 是。caretColor 自 API12 起同时驱动手柄颜色；onWillCopy/onWillCut 为 @since 26 新增拦截回调；selectedBackgroundColor 在 API>=26 额外设 FlagByUser。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 @since 7/8/9/10/12/22/23/26；静态 @since 23 static
- **API 版本号策略:** 同前；onWillCopy/onWillCut @since 26.0.0 static

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| caretColor 驱动三处颜色 | 光标+手柄+拖拽手柄 | AC-1.x |
| selectedBackgroundColor 透明度处理 | alpha=255 自动 0.2 | AC-2.1 |
| copyOption=None 全局禁用 | 复制/剪切/分享/拖拽 | AC-5.1 |
| onWillCopy/onWillCut 拦截模式 | 返回 false 取消 | AC-4.4,4.7 |
| onPaste preventDefault | 跳过插入 | AC-4.10 |
| 选区变化去重 | prev vs new index 比较 | AC-6.2 |
| barState=Off | 内部滚动启用但条隐藏 | AC-8.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 选区变化回调去重，避免冗余触发 | 单测 | text_select_controller.cpp:711 |
| 可靠性 | copyOption=None 幂等禁用所有复制路径 | 单测 | text_field_pattern.cpp:2368 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | selectionMenuHidden 影响无障碍菜单；copyOption 影响复制操作可访问性 | AC-8.5,5.1 |
| 大字体 | 否 | — | — |
| 深色模式 | 是 | caretColor/selectedBackgroundColor 默认值取主题 token | AC-1.2,2.3 |
| 多窗口/分屏 | 是 | 剪贴板跨窗口；拖拽跨窗口 | AC-4.x,7.x |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | caretColor 手柄颜色 API12；onWillCopy/onWillCut @since 26；selectedBackgroundColor FlagByUser API26 | AC-1.4,4.3,2.4 |
| 生态兼容 | 是 | enableSelectedDataDetector 依赖系统 AI 检测能力 | AC-7.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextArea 光标选择与剪贴板
  作为 应用开发者
  我想要 控制光标颜色、选区菜单、剪贴板拦截、复制权限、滚动条
  以便 精确管理选区与剪贴板交互

  Scenario: onWillCopy 返回 false 取消复制
    Given 注册 .onWillCopy((value) => false) 且选中文本
    When 触发复制操作
    Then FireOnWillCopy 返回 false
    And clipboard SetData 被跳过
    And onCopy 不触发

  Scenario: copyOption=None 禁用全部复制路径
    Given 设置 .copyOption(CopyOptions.None)
    When 触发复制/剪切/拖拽
    Then HandleOnCopy/HandleOnCut 早退
    And InitDragEvent 不注册拖拽
    And 菜单 Copy/Cut 项不显示

  Scenario: selectedBackgroundColor 透明度处理
    When 调用 .selectedBackgroundColor(Color.Red)（alpha=255）
    Then 存储前 ChangeOpacity(0.2)
    When 调用 .selectedBackgroundColor(Color.Red.alpha(0.5))
    Then 按原 alpha=0.5 使用
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "caretColor 为何自 API12 起同时驱动手柄颜色"
  - repo: "openharmony/arkui_ace_engine"
    query: "selectedBackgroundColor 不透明自动 0.2 的 ChangeOpacity 实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "onWillCopy/onWillCut @since 26 拦截模式与返回 false 取消的实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "copyOption=None 为何禁用拖拽 InitDragEvent"
  - repo: "openharmony/arkui_ace_engine"
    query: "barState=Off 为何内部滚动启用但条隐藏"
```

**关键文档：** `specs/05-ui-components/09-text-components/05-text-area/design.md`（DESIGN-Func-05-09-05）；SDK `textArea.static.d.ets` / `text_area.d.ts`
