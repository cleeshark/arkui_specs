# 特性规格

> Func-05-09-02-Feat-09 剪贴板、数据检测与菜单定制：固化 RichEditor 组件的剪贴板事件拦截（onPaste/onCut/onCopy）、复制权限控制（copyOptions）、文本实体数据检测（enableDataDetector/dataDetectorConfig）、选中文本 AI 数据检测（enableSelectedDataDetector）、自定义选择菜单（bindSelectionMenu）和标准编辑菜单定制（editMenuOptions）六大子能力的现有实现行为规格。重点记录 `copyOption_` 作为剪贴板操作总开关的守卫逻辑、`TextCommonEvent.preventDefault()` 拦截机制、`DataDetectorAdapter` 双实例（全文检测 vs 选区检测）架构，以及 `selectionMenuMap_` 以 `(TextSpanType, TextResponseType)` 为键的菜单注册模型。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 剪贴板、数据检测与菜单定制 (Clipboard, Data Detection & Menu Customization) |
| 特性编号 | Func-05-09-02-Feat-09 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 10+（copyOptions），API 11+（onPaste/enableDataDetector/dataDetectorConfig），API 12+（onCut/onCopy/editMenuOptions），API 22+（enableSelectedDataDetector） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐剪贴板事件拦截行为规格 | 固化 onPaste/onCut/onCopy 三个事件的 `preventDefault` 拦截机制和 Fire 回调分发路径 |
| MODIFIED | 补齐 copyOptions 权限守卫规格 | 记录 `copyOption_` 作为 copy/cut/drag 操作总开关的守卫逻辑，`None` 值阻断全部剪贴板操作 |
| MODIFIED | 补齐数据检测双适配器规格 | 固化 `dataDetectorAdapter_`（全文检测）和 `selectDetectorAdapter_`（选区检测）双实例架构 |
| MODIFIED | 补齐选择菜单注册规格 | 记录 `selectionMenuMap_` 以 `(TextSpanType, TextResponseType)` 为键的菜单注册/覆盖/清除模型 |
| MODIFIED | 补齐编辑菜单定制规格 | 固化 `EditMenuOptions` 三回调（onCreateMenu/onMenuItemClick/onPrepareMenu）解析与下发路径 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/02-rich-editor/design.md` | 未创建 |

---

## 用户故事

### US-1: 剪贴板事件拦截

**作为** 应用开发者,
**我想要** 通过 onPaste/onCut/onCopy 回调拦截并自定义剪贴板操作,
**以便** 在粘贴/剪切/复制前后执行业务逻辑或阻止默认行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `onPaste(callback)` THEN 通过 `RichEditorModelNG::SetOnPaste` 将回调存入 `RichEditorEventHub::onPaste_`（`rich_editor_model_ng.cpp:371-384`） | 正常 |
| AC-1.2 | WHEN `HandleOnPaste()` 执行 THEN 创建 `TextCommonEvent` 并调用 `eventHub->FireOnPaste(event)`，若 `event.IsPreventDefault()` 为 true 则关闭选择菜单、重置选区、不执行粘贴（`rich_editor_pattern.cpp:9679-9703`） | 正常 |
| AC-1.3 | WHEN `HandleOnPaste()` 中 `preventDefault` 为 false THEN 通过 `clipboard_->GetSpanStringData(CreatePasteCallback())` 获取剪贴板数据并执行粘贴（`rich_editor_pattern.cpp:9704-9716`） | 正常 |
| AC-1.4 | WHEN 调用 `onCut(callback)` THEN 通过 `RichEditorModelNG::SetOnCut` 将回调存入 `RichEditorEventHub::onCut_`（`rich_editor_model_ng.cpp:739-752`） | 正常 |
| AC-1.5 | WHEN `HandleOnCut()` 执行且 `copyOption_ == CopyOptions::None` THEN 直接返回不执行剪切（`rich_editor_pattern.cpp:9837-9840`） | 边界 |
| AC-1.6 | WHEN `HandleOnCut()` 中 `textSelector_.IsValid()` 为 false THEN 直接返回不执行剪切（`rich_editor_pattern.cpp:9841-9844`） | 边界 |
| AC-1.7 | WHEN `HandleOnCut()` 中 `preventDefault` 为 false THEN 调用 `OnCopyOperation()` 复制内容后调用 `DeleteBackward(1, TextChangeReason::CUT)` 删除选中内容（`rich_editor_pattern.cpp:9858-9860`） | 正常 |
| AC-1.8 | WHEN 调用 `onCopy(callback)` THEN 通过 `RichEditorModelNG::SetOnCopy` 将回调存入 `RichEditorEventHub::onCopy_`（`rich_editor_model_ng.cpp:754-767`） | 正常 |
| AC-1.9 | WHEN `HandleOnCopy()` 执行且 `copyOption_ == CopyOptions::None` THEN 直接返回不执行复制（`rich_editor_pattern.cpp:9612-9614`） | 边界 |
| AC-1.10 | WHEN `HandleOnCopy()` 中 `preventDefault` 为 false THEN 调用 `OnCopyOperation(isUsingExternalKeyboard)` 执行复制，并根据鼠标/键盘状态关闭或隐藏菜单（`rich_editor_pattern.cpp:9619-9624`） | 正常 |

### US-2: 复制权限控制

**作为** 应用开发者,
**我想要** 通过 `copyOptions` 控制组件的复制/剪切权限级别,
**以便** 禁止复制或限制为本地/分布式复制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `copyOptions(value)` THEN 通过 `RichEditorModelNG::SetCopyOption` 将值写入 `TextLayoutProperty::CopyOption`（`rich_editor_model_ng.cpp:338-341`） | 正常 |
| AC-2.2 | WHEN `OnModifyDone()` 执行 THEN 从 `TextLayoutProperty` 读取 `copyOption_`，缺省值为 `CopyOptions::Local`（`rich_editor_pattern.cpp:712`） | 正常 |
| AC-2.3 | WHEN `CopyOptions` 枚举取值 THEN `None=0, InApp, Local, Distributed`（`constants.h:735-740`） | 正常 |
| AC-2.4 | WHEN `copyOption_ == CopyOptions::None` THEN `HandleDraggableFlag` 中 `SetIsTextDraggable(false)`，拖拽被禁用（`rich_editor_pattern.cpp:4355-4363`） | 边界 |
| AC-2.5 | WHEN `HandleCopyOrCutCommand` 收到注入命令且 `copyOption_ == CopyOptions::None` THEN 记录错误日志并返回不执行（`rich_editor_pattern.cpp:1601-1604`） | 异常 |

### US-3: 文本实体数据检测

**作为** 应用开发者,
**我想要** 通过 `enableDataDetector` 和 `dataDetectorConfig` 启用文本实体识别（电话/URL/邮箱/地址/日期）,
**以便** 自动识别文本中的实体并提供交互入口。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `enableDataDetector(true)` THEN 通过 `RichEditorBridge::SetEnableDataDetector` 调用 `SetTextDetectEnable(true)`，设置 `textDetectEnable_=true` 并注册 `SetConfigChangedCallback`（`text_pattern.cpp:7049-7074`） | 正常 |
| AC-3.2 | WHEN `enableDataDetector` 传入 null/undefined THEN 调用 `resetRichEditorEnableDataDetector` 重置（`arkts_native_rich_editor_bridge.cpp:482-501`） | 边界 |
| AC-3.3 | WHEN 调用 `enableDataDetector(false)` THEN 设置 `textDetectEnable_=false` 并调用 `dataDetectorAdapter_->CancelAITask()` 取消检测任务（`text_pattern.cpp:7070-7073`） | 正常 |
| AC-3.4 | WHEN `enable` 值等于当前 `textDetectEnable_` THEN 直接返回不重复设置（`text_pattern.cpp:7056-7058`） | 边界 |
| AC-3.5 | WHEN 调用 `dataDetectorConfig(config)` THEN 通过 `SetTextDetectConfig` 设置 `dataDetectorAdapter_` 的 types、onResult、entityColor、entityDecoration 系列属性（`text_pattern.cpp:6049-6067`） | 正常 |
| AC-3.6 | WHEN `dataDetectorConfig` 的 types 字段为非数组 THEN 调用 `resetRichEditorDataDetectorConfigWithEvent` 重置（`arkts_native_rich_editor_bridge.cpp:660-663`） | 异常 |
| AC-3.7 | WHEN 支持的检测类型 THEN `TEXT_DETECT_TYPES = {"phoneNum", "url", "email", "location", "datetime"}`（`text_model.h:44`） | 正常 |
| AC-3.8 | WHEN `dataDetectorConfig` 的 configStr 与缓存值不同 THEN 调用 `MarkAISpanStyleChanged()` 触发 AI span 样式更新（`text_pattern.cpp:6064-6066`） | 正常 |

### US-4: 选中文本 AI 数据检测

**作为** 应用开发者,
**我想要** 通过 `enableSelectedDataDetector` 控制选中文本时是否启用 AI 菜单 (@since 22),
**以便** 为选中文本提供 AI 智能识别能力。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `enableSelectedDataDetector(value)` THEN 通过静态/动态 modifier 调用 `RichEditorModelNG::SetSelectDetectEnable`，再委托 `TextPattern::SetSelectDetectEnable` 设置 `selectDetectEnabled_`（`text_pattern.cpp:6905-6913`） | 正常 |
| AC-4.2 | WHEN `SetSelectDetectEnable` 执行 THEN 同时设置 `selectDetectEnabledIsUserSet_=true` 标记用户已显式设置（`text_pattern.cpp:6911`） | 正常 |
| AC-4.3 | WHEN 未设置 `enableSelectedDataDetector` THEN `selectDetectEnabled_` 默认值为 `true`（`text_pattern.h:676`） | 边界 |
| AC-4.4 | WHEN 调用 `ResetSelectDetectEnable` THEN `selectDetectEnabledIsUserSet_=false`，`selectDetectEnabled_` 重置为 `true`（`text_pattern.cpp:6920-6924`） | 正常 |
| AC-4.5 | WHEN `MaybeNeedShowSelectAIDetect()` 被调用 THEN 返回 `selectDetectEnabled_ && !selectDetectorAdapter_->aiSpanMap_.empty()`（`text_pattern.cpp:7093-7097`） | 正常 |

### US-5: 自定义选择菜单

**作为** 应用开发者,
**我想要** 通过 `bindSelectionMenu` 按 span 类型和响应类型绑定自定义选择菜单,
**以便** 在不同选区场景下展示不同的自定义菜单内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `bindSelectionMenu(spanType, content, responseType, options)` THEN 通过 `RichEditorModelNG::BindSelectionMenu` 委托 `RichEditorPattern::BindSelectionMenu`，最终调用 `TextPattern::BindSelectionMenu`（`rich_editor_model_ng.cpp:343-361`，`rich_editor_pattern.cpp:10655-10661`） | 正常 |
| AC-5.2 | WHEN `TextPattern::BindSelectionMenu` 注册菜单 THEN 以 `(TextSpanType, TextResponseType)` 为键存入 `selectionMenuMap_`，值为 `SelectionMenuParams`（`text_pattern.cpp:7105-7126`） | 正常 |
| AC-5.3 | WHEN 键已存在且 `menuBuilder != nullptr` THEN 更新已有项的 buildFunc、onAppear、onDisappear、onMenuShow、onMenuHide、isValid（`text_pattern.cpp:7107-7118`） | 正常 |
| AC-5.4 | WHEN 键已存在且 `menuBuilder == nullptr` THEN 从 `selectionMenuMap_` 中 erase 该键（`text_pattern.cpp:7108-7111`） | 边界 |
| AC-5.5 | WHEN `IsTextInSelectionContainer()` 为 true THEN 直接返回不注册菜单（`text_pattern.cpp:7102-7104`） | 边界 |
| AC-5.6 | WHEN 菜单注册成功 THEN 调用 `host->MarkDirtyWithOnProChange(PROPERTY_UPDATE_MEASURE_SELF)` 触发重测量（`text_pattern.cpp:7129`） | 正常 |
| AC-5.7 | WHEN `SelectionMenuOptions` 接口字段 THEN 含 onAppear、onDisappear、menuType、onMenuShow、onMenuHide、previewMenuOptions（`richEditor.ets:1261-1268`） | 正常 |
| AC-5.8 | WHEN 调用 `ResetBindSelectionMenu` THEN 通过 `pattern->ClearSelectionMenu()` 清除所有已注册菜单（`rich_editor_model_ng.cpp:363-369`） | 正常 |
| AC-5.9 | WHEN `bindSelectionMenu` 的 spanType 为 undefined THEN 默认为 `TextSpanType::TEXT`；responseType 为 undefined 时默认为 `TextResponseType::LONG_PRESS`（`arkts_native_rich_editor_bridge.cpp:380-403`） | 边界 |

### US-6: 编辑菜单定制

**作为** 应用开发者,
**我想要** 通过 `editMenuOptions` 定制标准编辑菜单（剪切/复制/粘贴/全选）的创建和响应行为 (@since 12),
**以便** 替换或扩展系统默认的编辑菜单项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `editMenuOptions(value)` THEN 通过 `RichEditorBridge::SetEditMenuOptions` 调用 `ParseSelectionMenuOptions` 解析三个回调（`arkts_native_rich_editor_bridge.cpp:2440-2461`） | 正常 |
| AC-6.2 | WHEN `ParseSelectionMenuOptions` 解析失败 THEN 调用 `resetRichEditorEditMenuOptions` 重置并返回（`arkts_native_rich_editor_bridge.cpp:2452-2456`） | 异常 |
| AC-6.3 | WHEN 解析成功 THEN 调用 `setRichEditorEditMenuOptions` 下发，最终委托 `selectOverlay_->OnSelectionMenuOptionsUpdate`（`rich_editor_pattern.cpp:13592-13597`） | 正常 |
| AC-6.4 | WHEN `EditMenuOptions` 结构体 THEN 含 onCreateMenu、onMenuItemClick、onPrepareMenu 三个回调字段（`arkoala_api_generated.h:16142-16147`） | 正常 |
| AC-6.5 | WHEN `OnSelectionMenuOptionsUpdate` 执行 THEN 将三个回调存入 `BaseTextSelectOverlay` 的 `onCreateMenuCallback_`、`onMenuItemClick_` 成员（`base_text_select_overlay.h:429-430`） | 正常 |
| AC-6.6 | WHEN 调用 `SetSelectionMenuOptions` THEN 通过 `RichEditorPattern::OnSelectionMenuOptionsUpdate` 委托 select overlay（`rich_editor_model_ng.cpp:784-789, 832-839`） | 正常 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.10 | R-1, R-2, R-3, R-4, R-5 | N/A（存量） | 代码审查 | `rich_editor_model_ng.cpp:371-384, 739-767`，`rich_editor_pattern.cpp:9607-9861` |
| AC-2.1~2.5 | R-6, R-7, R-8 | N/A | 代码审查 | `rich_editor_model_ng.cpp:338-341, 432-439`，`constants.h:735-740` |
| AC-3.1~3.8 | R-9, R-10, R-11, R-12 | N/A | 代码审查 | `text_pattern.cpp:6049-6067, 7049-7075`，`text_model.h:44` |
| AC-4.1~4.5 | R-13, R-14 | N/A | 代码审查 | `text_pattern.cpp:6905-6924, 7093-7097` |
| AC-5.1~5.9 | R-15, R-16, R-17, R-18 | N/A | 代码审查 | `rich_editor_model_ng.cpp:343-369`，`text_pattern.cpp:7099-7130` |
| AC-6.1~6.6 | R-19, R-20 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:2440-2475`，`rich_editor_pattern.cpp:13592-13597` |

---

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 注册 onPaste 回调 | `SetOnPaste` 将 `std::function` 存入 `RichEditorEventHub::onPaste_`，支持 ViewStackProcessor 和 FrameNode 两种重载 | 回调类型为 `void(TextCommonEvent&)`（`rich_editor_event_hub.h:102`） | AC-1.1 |
| R-2 | 行为 | `HandleOnPaste` 执行 | `FireOnPaste(event)` 分发事件；若 `preventDefault` 则关闭菜单、重置选区、不粘贴；否则从剪贴板获取数据粘贴 | `preventDefault` 检查在 `clipboard_->GetSpanStringData` 之前（`rich_editor_pattern.cpp:9696-9716`） | AC-1.2, AC-1.3 |
| R-3 | 行为 | 注册 onCut/onCopy 回调 | 分别通过 `SetOnCut`/`SetOnCopy` 存入 `onCut_`/`onCopy_` | 均为 `TextCommonEvent` 类型回调（`rich_editor_event_hub.h:115-116`） | AC-1.4, AC-1.8 |
| R-4 | 边界 | `HandleOnCut` 时 `copyOption_==None` 或 `textSelector_` 无效 | 直接返回，设置 `suppressAccessibilityEvent_=true` | 两重守卫：copyOption 和选区有效性（`rich_editor_pattern.cpp:9837-9844`） | AC-1.5, AC-1.6 |
| R-5 | 行为 | `HandleOnCopy/Cut` 中 `preventDefault` 为 false | Copy: 调用 `OnCopyOperation`；Cut: 调用 `OnCopyOperation` + `DeleteBackward(CUT)` | Copy 后根据鼠标/键盘状态关闭或隐藏菜单（`rich_editor_pattern.cpp:9619-9624, 9858-9860`） | AC-1.7, AC-1.10 |
| R-6 | 行为 | 调用 `copyOptions(value)` | 通过 `ACE_UPDATE_LAYOUT_PROPERTY(TextLayoutProperty, CopyOption, ...)` 写入布局属性 | 支持 ViewStackProcessor 和 FrameNode 两种重载（`rich_editor_model_ng.cpp:338-341, 432-434`） | AC-2.1 |
| R-7 | 行为 | `OnModifyDone` 读取 copyOption | `copyOption_ = layoutProperty->GetCopyOption().value_or(CopyOptions::Local)` | 缺省值为 `Local`（`rich_editor_pattern.cpp:712`）；TextPattern 基类默认为 `None`（`text_pattern.h:648`） | AC-2.2 |
| R-8 | 边界 | `copyOption_ == CopyOptions::None` | 阻断 copy/cut/drag 全部操作：`HandleOnCopy` 返回、`HandleOnCut` 返回、`HandleDraggableFlag` 禁用拖拽、`HandleCopyOrCutCommand` 拒绝注入命令 | `None=0` 为枚举首值（`constants.h:736`） | AC-2.4, AC-2.5, AC-1.5, AC-1.9 |
| R-9 | 行为 | 调用 `enableDataDetector(true)` | `SetTextDetectEnable(true)` 设置 `textDetectEnable_=true`，注册 `pipeline->SetConfigChangedCallback` | 若值与当前相同则直接返回（`text_pattern.cpp:7056-7058`） | AC-3.1, AC-3.4 |
| R-10 | 行为 | 调用 `enableDataDetector(false)` | 设置 `textDetectEnable_=false`，调用 `dataDetectorAdapter_->CancelAITask()` 取消检测 | 取消后不再识别实体（`text_pattern.cpp:7070-7073`） | AC-3.3 |
| R-11 | 行为 | 调用 `dataDetectorConfig(config)` | `SetTextDetectConfig` 设置 types、onResult、entityColor、entityDecorationType/Color/Style、enablePreviewMenu | types 为逗号分隔字符串（`text_pattern.cpp:6049-6067`） | AC-3.5 |
| R-12 | 边界 | dataDetectorConfig types 为非数组 | 调用 `resetRichEditorDataDetectorConfigWithEvent` 重置配置 | 桥接层校验在 `arkts_native_rich_editor_bridge.cpp:660-663` | AC-3.6 |
| R-13 | 行为 | 调用 `enableSelectedDataDetector(value)` | `SetSelectDetectEnable` 设置 `selectDetectEnabled_=value` 和 `selectDetectEnabledIsUserSet_=true` | 默认值为 `true`（`text_pattern.h:676`）；reset 后恢复为 `true`（`text_pattern.cpp:6920-6924`） | AC-4.1, AC-4.2, AC-4.3, AC-4.4 |
| R-14 | 行为 | `MaybeNeedShowSelectAIDetect()` 查询 | 返回 `selectDetectEnabled_ && !aiSpanMap_.empty()` | 需用户启用且有 AI span 结果（`text_pattern.cpp:7093-7097`） | AC-4.5 |
| R-15 | 行为 | 调用 `bindSelectionMenu` | 以 `(TextSpanType, TextResponseType)` 为键存入 `selectionMenuMap_`，触发 `PROPERTY_UPDATE_MEASURE_SELF` | RichEditorPattern 委托 TextPattern::BindSelectionMenu（`rich_editor_pattern.cpp:10655-10661`） | AC-5.1, AC-5.2 |
| R-16 | 边界 | 键已存在且 menuBuilder 为 null | 从 `selectionMenuMap_` 中 erase 该键 — 清除单个菜单注册 | 不影响其他键的菜单（`text_pattern.cpp:7108-7111`） | AC-5.4 |
| R-17 | 边界 | `IsTextInSelectionContainer()` 为 true | 直接返回不注册菜单 | 防止在选择容器内重复注册（`text_pattern.cpp:7102-7104`） | AC-5.5 |
| R-18 | 行为 | spanType/responseType 为 undefined | spanType 默认 `TextSpanType::TEXT`，responseType 默认 `TextResponseType::LONG_PRESS` | 桥接层默认值（`arkts_native_rich_editor_bridge.cpp:380-403`） | AC-5.9 |
| R-19 | 行为 | 调用 `editMenuOptions(value)` | `ParseSelectionMenuOptions` 解析三个回调后调用 `setRichEditorEditMenuOptions`，委托 `OnSelectionMenuOptionsUpdate` | 三个回调：onCreateMenu、onMenuItemClick、onPrepareMenu（`arkts_native_rich_editor_bridge.cpp:2440-2461`） | AC-6.1, AC-6.3 |
| R-20 | 异常 | `ParseSelectionMenuOptions` 解析失败 | 调用 `resetRichEditorEditMenuOptions` 重置并返回 | 解析失败不修改现有配置（`arkts_native_rich_editor_bridge.cpp:2452-2456`） | AC-6.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.10（剪贴板事件拦截） | 代码审查 | SetOnPaste/Cut/Copy 注册路径、HandleOnPaste/Cut/Copy 的 preventDefault 拦截和默认行为 |
| VM-2 | AC-2.1~2.5（复制权限控制） | 代码审查 | CopyOption 写入布局属性、OnModifyDone 读取、None 守卫阻断逻辑 |
| VM-3 | AC-3.1~3.8（文本实体数据检测） | 代码审查 | SetTextDetectEnable/SetTextDetectConfig 实现、TEXT_DETECT_TYPES 类型清单、configStr 变化触发更新 |
| VM-4 | AC-4.1~4.5（选中文本 AI 检测） | 代码审查 | SetSelectDetectEnable/ResetSelectDetectEnable 实现、默认值和用户设置标记 |
| VM-5 | AC-5.1~5.9（自定义选择菜单） | 代码审查 | selectionMenuMap_ 注册/覆盖/清除模型、SelectionMenuOptions 接口字段、默认值 |
| VM-6 | AC-6.1~6.6（编辑菜单定制） | 代码审查 | EditMenuOptions 三回调解析与下发、ParseSelectionMenuOptions 失败处理 |

## API 变更分析

> 本特性为存量规格补录，记录各 API 的引入版本和当前签名。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `copyOptions(value)` | Public (@since 10) | `CopyOptions \| undefined` | `this` | N/A | 设置复制/剪切权限级别 | AC-2.1~2.5 |
| `onPaste(callback)` | Public (@since 11) | `PasteEventCallback \| undefined` | `this` | N/A | 粘贴事件回调，支持 preventDefault 拦截 | AC-1.1~1.3 |
| `onCut(callback)` | Public (@since 12) | `Callback<CutEvent, void> \| undefined` | `this` | N/A | 剪切事件回调，支持 preventDefault 拦截 | AC-1.4~1.7 |
| `onCopy(callback)` | Public (@since 12) | `Callback<CopyEvent, void> \| undefined` | `this` | N/A | 复制事件回调，支持 preventDefault 拦截 | AC-1.8~1.10 |
| `enableDataDetector(value)` | Public (@since 11) | `boolean \| undefined` | `this` | N/A | 启用/禁用文本实体数据检测 | AC-3.1~3.4 |
| `dataDetectorConfig(value)` | Public (@since 11) | `TextDataDetectorConfig \| undefined` | `this` | N/A | 配置数据检测类型和回调 | AC-3.5~3.8 |
| `enableSelectedDataDetector(value)` | Public (@since 22) | `boolean \| undefined` | `this` | N/A | 启用/禁用选中文本 AI 数据检测 | AC-4.1~4.5 |
| `bindSelectionMenu(spanType, content, responseType, options?)` | Public (@since 10) | `RichEditorSpanType, CustomBuilder, ResponseType\|RichEditorResponseType, SelectionMenuOptions?` | `this` | N/A | 按 span 类型和响应类型绑定自定义选择菜单 | AC-5.1~5.9 |
| `editMenuOptions(value)` | Public (@since 12) | `EditMenuOptions \| undefined` | `this` | N/A | 定制标准编辑菜单创建和响应回调 | AC-6.1~6.6 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

> 本特性为已有实现补录，下表汇总各接口的关键行为场景。API 签名以 SDK 声明层 `richEditor.ets` 为准。

| 接口 | 开放范围 | 参数约束 | 行为场景 | 关联 AC |
|------|----------|----------|----------|---------|
| `copyOptions(value)` | Public (@since 10) | `value`: `CopyOptions` 枚举（None/InApp/Local/Distributed），undefined 时 reset | 写入 `TextLayoutProperty::CopyOption`，`OnModifyDone` 读取到 `copyOption_`，`None` 阻断全部剪贴板操作 | AC-2.1~2.5 |
| `onPaste(callback)` | Public (@since 11) | `callback`: `PasteEventCallback`，undefined 时清除 | 存入 `onPaste_`，`HandleOnPaste` 时 Fire 并检查 `preventDefault` | AC-1.1~1.3 |
| `onCut(callback)` | Public (@since 12) | `callback`: `Callback<CutEvent, void>`，undefined 时清除 | 存入 `onCut_`，`HandleOnCut` 时先检查 `copyOption_` 和选区有效性，再 Fire 并检查 `preventDefault` | AC-1.4~1.7 |
| `onCopy(callback)` | Public (@since 12) | `callback`: `Callback<CopyEvent, void>`，undefined 时清除 | 存入 `onCopy_`，`HandleOnCopy` 时先检查 `copyOption_`，再 Fire 并检查 `preventDefault` | AC-1.8~1.10 |
| `enableDataDetector(value)` | Public (@since 11) | `value`: `boolean`，undefined 时 reset | 设置 `textDetectEnable_`，true 注册 config 回调，false 取消 AI 任务 | AC-3.1~3.4 |
| `dataDetectorConfig(value)` | Public (@since 11) | `value`: `TextDataDetectorConfig`（含 types 数组、onResult 回调、entityColor 等） | 设置 `dataDetectorAdapter_` 属性，configStr 变化时触发 AI span 更新 | AC-3.5~3.8 |
| `enableSelectedDataDetector(value)` | Public (@since 22) | `value`: `boolean`，undefined 时 reset 为 `true` | 设置 `selectDetectEnabled_` 和 `selectDetectEnabledIsUserSet_`，控制选区 AI 菜单 | AC-4.1~4.5 |
| `bindSelectionMenu(spanType, content, responseType, options?)` | Public (@since 10) | `spanType`: RichEditorSpanType（默认 TEXT）；`content`: CustomBuilder；`responseType`: ResponseType（默认 LONG_PRESS）；`options?`: SelectionMenuOptions | 以 `(spanType, responseType)` 为键注册到 `selectionMenuMap_`，null builder 清除 | AC-5.1~5.9 |
| `editMenuOptions(value)` | Public (@since 12) | `value`: `EditMenuOptions`（含 onCreateMenu/onMenuItemClick/onPrepareMenu） | 解析三回调后委托 `selectOverlay_->OnSelectionMenuOptionsUpdate` | AC-6.1~6.6 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — API 10 引入 `copyOptions` 和 `bindSelectionMenu`；API 11 新增 `onPaste`、`enableDataDetector`、`dataDetectorConfig`；API 12 新增 `onCut`、`onCopy`、`editMenuOptions`；API 22 新增 `enableSelectedDataDetector`
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（copyOptions/bindSelectionMenu），API 11（onPaste/enableDataDetector/dataDetectorConfig），API 12（onCut/onCopy/editMenuOptions），API 22（enableSelectedDataDetector）
- **API 版本号策略:** copyOptions/bindSelectionMenu 自 API 10 起；onPaste/enableDataDetector/dataDetectorConfig 自 API 11 起；onCut/onCopy/editMenuOptions 自 API 12 起；enableSelectedDataDetector 自 API 22 起

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| copyOption_ 作为剪贴板总开关 | `copyOption_ == CopyOptions::None` 在 `HandleOnCopy`、`HandleOnCut`、`HandleDraggableFlag`、`HandleCopyOrCutCommand`、`CheckAIPreviewMenuEnable` 中均作为前置守卫 — 单一属性控制全部剪贴板相关操作 | AC-1.5, AC-1.9, AC-2.4, AC-2.5 |
| copyOption_ 存储在 TextPattern 基类 | `copyOption_` 定义在 `TextPattern`（`text_pattern.h:648`），RichEditor 通过继承访问 — Text 和 RichEditor 共用同一复制权限模型 | AC-2.2 |
| copyOption_ 读取默认值为 Local | `OnModifyDone` 中 `GetCopyOption().value_or(CopyOptions::Local)`，但 TextPattern 基类成员默认初始化为 `None` — 两者在不同阶段生效 | AC-2.2 |
| DataDetectorAdapter 双实例 | `dataDetectorAdapter_`（全文检测，API 11+）和 `selectDetectorAdapter_`（选区检测，API 22+）为独立适配器实例，分别管理各自的 AI span 和检测配置 | AC-3.5, AC-4.5 |
| preventDefault 拦截机制 | onPaste/onCut/onCopy 均通过 `TextCommonEvent` 传递，调用 `event.IsPreventDefault()` 判断是否阻止默认行为 — 统一拦截模型 | AC-1.2, AC-1.7, AC-1.10 |
| selectionMenuMap_ 键模型 | 以 `(TextSpanType, TextResponseType)` 二元组为键，同一键重复注册为覆盖语义 — 支持多 span 类型多响应类型的菜单组合 | AC-5.2, AC-5.3 |
| RichEditorPattern::BindSelectionMenu 委托基类 | `RichEditorPattern::BindSelectionMenu` 直接调用 `TextPattern::BindSelectionMenu`（`rich_editor_pattern.cpp:10660`）— 无 RichEditor 特有逻辑 | AC-5.1 |
| EditMenuOptions 通过 select overlay 下发 | `OnSelectionMenuOptionsUpdate` 委托 `selectOverlay_->OnSelectionMenuOptionsUpdate` — 菜单定制逻辑在 `BaseTextSelectOverlay` 中实现 | AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可测试性 | copyOption_ 值可通过 `copyOptions()` 设置并从布局属性读取 | 代码审查 | `rich_editor_model_ng.cpp:338-341` |
| 可靠性 | enableDataDetector 重复设置相同值时直接返回，避免重复注册回调 | 代码审查 | `text_pattern.cpp:7056-7058` |
| 可靠性 | dataDetectorConfig 变化时仅当 configStr 不同才触发 AI span 更新，避免冗余刷新 | 代码审查 | `text_pattern.cpp:6064-6066` |
| 安全 | copyOption_==None 阻断注入命令的 copy/cut 操作并记录错误日志 | 代码审查 | `rich_editor_pattern.cpp:1601-1604` |

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
| 无障碍 | 是 | `HandleOnCut` 中 `copyOption_==None` 或选区无效时设置 `suppressAccessibilityEvent_=true` | AC-1.5, AC-1.6 |
| 大字体 | N/A | 剪贴板和菜单操作不涉及大字体适配 | — |
| 深色模式 | N/A | 数据检测和菜单不涉及主题模式 | — |
| 多窗口/分屏 | N/A | 剪贴板操作通过系统 Clipboard 服务，跨窗口行为一致 | — |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | API 10→11→12→22 逐步新增 onPaste/enableDataDetector/onCut/onCopy/editMenuOptions/enableSelectedDataDetector | AC-1.1~1.10, AC-3.1~3.8, AC-6.1~6.6 |
| 生态兼容 | 是 | `copyOption_==Distributed` 支持分布式剪贴板复制 | AC-2.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RichEditor 剪贴板、数据检测与菜单定制
  作为应用开发者
  我想要拦截剪贴板操作、启用实体检测并定制选择菜单
  以便控制内容的复制权限和交互体验

  Scenario: onPaste 拦截默认粘贴
    Given RichEditor 已注册 onPaste 回调
    When 用户触发粘贴操作
    Then HandleOnPaste 调用 FireOnPaste 分发事件
    When 回调中调用 preventDefault
    Then 关闭选择菜单、重置选区、不执行粘贴
    When 回调中未调用 preventDefault
    Then 从剪贴板获取 SpanString 数据并执行粘贴

  Scenario: copyOptions None 阻断剪贴板操作
    Given RichEditor 设置 copyOptions(CopyOptions.None)
    When 用户触发复制操作
    Then HandleOnCopy 检测 copyOption_==None 直接返回不执行
    When 用户触发剪切操作
    Then HandleOnCut 检测 copyOption_==None 直接返回不执行
    And 设置 suppressAccessibilityEvent_=true

  Scenario: enableDataDetector 启用全文实体检测
    Given RichEditor 设置 enableDataDetector(true)
    When SetTextDetectEnable 执行
    Then 设置 textDetectEnable_=true
    And 注册 pipeline->SetConfigChangedCallback
    When enableDataDetector(false)
    Then 调用 dataDetectorAdapter_->CancelAITask 取消检测

  Scenario: bindSelectionMenu 按 span 类型注册自定义菜单
    Given RichEditor 调用 bindSelectionMenu(TEXT, builder, LONG_PRESS, options)
    When TextPattern::BindSelectionMenu 执行
    Then 以 (TEXT, LONG_PRESS) 为键存入 selectionMenuMap_
    And 调用 MarkDirtyWithOnProChange 触发重测量
    When 同键重复注册且 builder 为 null
    Then 从 selectionMenuMap_ 中移除该键

  Scenario: editMenuOptions 定制标准编辑菜单
    Given RichEditor 设置 editMenuOptions(EditMenuOptions)
    When SetEditMenuOptions 桥接执行
    Then ParseSelectionMenuOptions 解析 onCreateMenu/onMenuItemClick/onPrepareMenu
    And 委托 selectOverlay_->OnSelectionMenuOptionsUpdate 下发
    When 解析失败
    Then 调用 resetRichEditorEditMenuOptions 重置不修改现有配置
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（剪贴板事件、复制权限、数据检测、菜单定制，不含 span 内容管理、布局算法、渲染细节）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditor clipboard events: HandleOnPaste/HandleOnCut/HandleOnCopy preventDefault interception and copyOption_ guard logic"
  - repo: "openharmony/ace_engine"
    query: "RichEditor data detector: DataDetectorAdapter dual instance (dataDetectorAdapter_ vs selectDetectorAdapter_), SetTextDetectEnable, SetTextDetectConfig, TEXT_DETECT_TYPES"
  - repo: "openharmony/ace_engine"
    query: "RichEditor selection menu: selectionMenuMap_ registration by (TextSpanType, TextResponseType) key, BindSelectionMenu, EditMenuOptions OnSelectionMenuOptionsUpdate"
  - repo: "openharmony/interface_sdk-js"
    query: "RichEditor copyOptions onPaste onCut onCopy enableDataDetector dataDetectorConfig bindSelectionMenu editMenuOptions enableSelectedDataDetector API signatures and since versions"
```

**关键文档：**
- SDK 静态版声明: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets`
- CopyOptions 枚举: `frameworks/core/components/common/layout/constants.h`
- 剪贴板事件 Hub: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_event_hub.h`
- 数据检测基类: `frameworks/core/components_ng/pattern/text/text_pattern.h` / `text_pattern.cpp`
- 选择菜单基类: `frameworks/core/components_ng/pattern/text/base_text_select_overlay.h`
- EditMenuOptions 结构体: `frameworks/core/interfaces/native/generated/interface/arkoala_api_generated.h`
