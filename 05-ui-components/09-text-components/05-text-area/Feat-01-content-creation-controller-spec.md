# 特性规格

> Func-05-09-05-Feat-01 内容创建与控制器：固化 TextAreaOptions（placeholder/text/controller）、TextArea 构造、setTextAreaOptions、TextAreaController（caretPosition/setTextSelection/stopEditing）四组创建与控制器能力的行为规格。TextArea 与 TextInput 共用 TextFieldPattern/TextFieldController，靠 `IsTextArea()` 属性判别区分多行行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 内容创建与控制器 (Content Creation & Controller) |
| 特性编号 | Func-05-09-05-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持（placeholder/text 构造），API 8 起支持 controller/caretPosition，API 10 起支持 setTextSelection/stopEditing；静态版 @since 23 static；setTextAreaOptions @since 26.1.0 staticonly @unpublished |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。TextArea 复用 TextFieldPattern，通过 TEXTAREA_ETS_TAG + PlaceholderMaxLines=Infinity 配置使 IsTextArea() 返回 true。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | TextAreaOptions（placeholder/text/controller）解析行为 | 动态版 @since 7/8，静态版 @since 23 static 含 Bindable 联合 |
| ADDED | TextArea 构造创建 FrameNode 行为 | TEXTAREA_ETS_TAG + TextFieldPattern + PlaceholderMaxLines=Infinity |
| ADDED | TextAreaController.caretPosition 行为 | @since 8 动态 / @since 23 static；API 12 负值钳制边界 |
| ADDED | TextAreaController.setTextSelection 行为 | @since 10 动态 / @since 23 static；早退+钳制+相等即光标+MenuPolicy |
| ADDED | TextAreaController.stopEditing 行为 | @since 10 动态 / @since 23 static；五步且幂等 |
| ADDED | setTextAreaOptions 行为 | @since 26.1.0 staticonly @unpublished，静态专属，动态版无对应 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/05-text-area/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 TextArea 组件

**作为** 应用开发者,
**我想要** 通过 `TextArea({ placeholder, text, controller })` 创建多行文本输入区域,
**以便** 接收用户多行文本输入。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `TextArea()` 不传参 THEN 创建 FrameNode（tag=`TEXTAREA_ETS_TAG`=`"TextArea"`），Pattern 为 TextFieldPattern，`IsTextArea()` 返回 true（`text_field_model_ng.cpp:139` `MakeRefPtr<TextFieldPattern>()`；`text_field_model_ng.cpp:144` `UpdatePlaceholderMaxLines(Infinity)`） | 正常 |
| AC-1.2 | WHEN 调用 `TextArea({ placeholder: "请输入" })` 且 placeholder 为 string THEN placeholder 写入 `TextFieldLayoutProperty::Placeholder`（u16string），dirty flag 为 `PROPERTY_UPDATE_MEASURE`（`text_field_model_ng.cpp:143`；`text_field_layout_property.h:290`） | 正常 |
| AC-1.3 | WHEN 调用 `TextArea({ placeholder: $r('app.string.placeholder') })` 且 placeholder 为 Resource THEN 从资源解析为 u16string 后写入 Placeholder 属性 | 正常 |
| AC-1.4 | WHEN 调用 `TextArea({ text: "初始文本" })` 且 text 为 string THEN text 经 `ProcessBindableText` 走 `Ark_ResourceStr` 分支转为 u16string，存入 `ContentController::content_`（`text_area_static_modifier.cpp:47-49`；`content_controller.h:110`），无 onChange 回调注册 | 正常 |
| AC-1.5 | WHEN 调用 `TextArea({ text: $r('app.string.init') })` 且 text 为 Resource THEN 同 AC-1.4，ResourceStr 分支转 u16string | 正常 |
| AC-1.6 | WHEN 创建后未设置 placeholder THEN Placeholder 默认为空串 u""（`text_field_model_ng.cpp:143` `placeholder.value_or(u"")`） | 边界 |
| AC-1.7 | WHEN 创建后未设置 text THEN ContentController 初始化为空串（`UpdateTextFieldPattern` → `InitEditingValueText`） | 边界 |

### US-2: 绑定 TextAreaController

**作为** 应用开发者,
**我想要** 在 TextAreaOptions 中传入 controller 实例,
**以便** 后续编程式控制光标、选区与编辑状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `TextArea({ controller: this.controller })` 且 controller 为 TextAreaController 实例 THEN C-API 桥解析 controller peer（`text_area_static_modifier.cpp:104-107`），调 `TextFieldModelStatic::GetController(frameNode, placeholder, text)` 获取/创建 TextFieldController，`peerPtr->SetController(controller)` 绑定（`text_area_static_modifier.cpp:110-124`） | 正常 |
| AC-2.2 | WHEN 不传 controller THEN 创建时 `TextFieldModelNG::CreateTextArea` 内部 `pattern->SetTextFieldController(MakeRefPtr<TextFieldController>())` 自动创建（`text_field_model_ng.cpp` CreateNode 流程） | 边界 |
| AC-2.3 | WHEN controller 参数类型为非 TextAreaController 对象 THEN `Converter::GetOpt` 解析失败，controller 为 nullopt，按未传处理 | 异常 |

### US-3: 使用 Bindable 双向绑定 text

**作为** 应用开发者,
**我想要** 在静态版通过 `Bindable<string>` / `Bindable<ResourceStr>` 绑定 text（@since 23 static）,
**以便** 实现文本内容双向同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN text 为 `Bindable<string>`（含 value + onChange） THEN `ProcessBindableText` 走 `Ark_Bindable_String` 分支，提取 `src.value` 为字符串值，并通过 `CallbackHelper(src.onChange)` 注册回调到 `TextFieldModelStatic::SetOnChangeEvent`（`text_area_static_modifier.cpp:50-58`） | 正常 |
| AC-3.2 | WHEN text 为 `Bindable<ResourceStr>` THEN `ProcessBindableText` 走 `Ark_Bindable_ResourceStr` 分支，提取 value 并注册 onChange 回调（回调内转回 Ark_ResourceStr）（`text_area_static_modifier.cpp:59-67`） | 正常 |
| AC-3.3 | WHEN text 为 `Bindable<Resource>` THEN `ProcessBindableText` 走 `Ark_Bindable_Resource` 分支，**no-op**，不设置 text 值也不注册回调（注释"Invalid case, should be deleted from SDK"）（`text_area_static_modifier.cpp:68-70`） | 异常 |
| AC-3.4 | WHEN Bindable onChange 回调被触发（文本内容变化） THEN 通过 `SetOnChangeEvent` 注册的回调以新内容调用 JS 侧 onChange | 正常 |

### US-4: 编程式设置光标位置

**作为** 应用开发者,
**我想要** 通过 `controller.caretPosition(value)` 设置光标位置,
**以便** 程序控制光标落在指定字符索引。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `caretPosition(value)` 且 value 为正整数且组件已聚焦 THEN `SetCaretPosition` 调 `MoveCaretToContentRect(value, DOWNSTREAM)`、`UpdateCaretInfoToController`、`StartTwinkling`（因 HasFocus 且无放大镜）、`CloseSelectOverlay`、`TriggerAvoidOnCaretChange`、`MarkDirtyNode(PROPERTY_UPDATE_RENDER)`（`text_field_pattern.cpp:8311-8327`） | 正常 |
| AC-4.2 | WHEN 调用 `caretPosition(value)` 且组件未聚焦 THEN `StartTwinkling` 不执行（`HasFocus()` 为 false），其余光标移动与 MarkDirtyNode 仍执行 | 边界 |
| AC-4.3 | WHEN value 为负数且运行环境 API >= 12（C++ JS 桥） THEN 负值钳为 0 后调用（`js_text_editable_controller.cpp:69` `GreatOrEqualTargetAPIVersion(VERSION_TWELVE)`） | 边界 |
| AC-4.4 | WHEN value 为负数且运行环境 API < 12（C++ JS 桥） THEN 负值原样透传给 `controller->CaretPosition`（不钳制） | 边界 |
| AC-4.5 | WHEN 通过 C-API 调用 `CaretPositionImpl` THEN 无论 API 版本始终 `std::max(value, 0)` 钳制（`text_area_controller_accessor.cpp:40`） | 边界 |
| AC-4.6 | WHEN value 超过文本长度 THEN `MoveCaretToContentRect` 将光标移动到末尾位置（由 selectController 内部钳制） | 边界 |
| AC-4.7 | WHEN 多实例场景调用 THEN `FREE_NODE_CHECK` 转发到 `SetCaretPositionMultiThread`，延迟到 `PostAfterAttachMainTreeTask` 执行（`text_field_pattern_multi_thread.cpp:226`） | 边界 |

### US-5: 编程式设置文本选区

**作为** 应用开发者,
**我想要** 通过 `controller.setTextSelection(start, end, options?)` 选中文本范围,
**以便** 程序控制选区并可选控制菜单显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `setTextSelection(start, end)` 且 start<=end 且组件已聚焦且非预览文本 THEN Controller 钳制 start/end 到 `[0, textLength]`，`ScheduleTaskWithLayoutDeferral` 延迟调 `SetSelectionFlag`（`text_field_controller.cpp:70-88`） | 正常 |
| AC-5.2 | WHEN `selectionEnd < selectionStart` THEN Controller 直接 return，不执行选区操作（`text_field_controller.cpp:72-73`） | 边界 |
| AC-5.3 | WHEN start==end（钳制后） THEN `SetSelectionFlag` 走光标分支：`MoveCaretToContentRect(end, DOWNSTREAM)` + `StartTwinkling`，不创建选区手柄（`text_field_pattern.cpp:8349-8352`） | 正常 |
| AC-5.4 | WHEN start<end（钳制后） THEN 走选区分支：`cursorVisible_=false`、`showSelect_=true`、`HandleSetSelection`、按 isForward 顺序 `MoveFirstHandleToContentRect`/`MoveSecondHandleToContentRect`（`text_field_pattern.cpp:8353-8362`） | 正常 |
| AC-5.5 | WHEN start/end 超过文本长度 THEN Controller 钳制到 textLength；Pattern 内再次 re-clamp（`text_field_controller.cpp:80-82`；`text_field_pattern.cpp:8346-8347`） | 边界 |
| AC-5.6 | WHEN start/end 为负数 THEN 钳制到 0（`std::clamp(value, 0, length)`） | 边界 |
| AC-5.7 | WHEN 组件未聚焦或处于预览文本状态 THEN `SetSelectionFlag` 直接 return，不执行选区（`text_field_pattern.cpp:8341-8342` `!HasFocus() || GetIsPreviewText()`） | 边界 |
| AC-5.8 | WHEN options.menuPolicy 为 `MenuPolicy.SHOW` THEN `IsShowMenu` 返回 true，`ProcessOverlay` 显示选区菜单（`text_field_pattern.cpp:8374-8379`；`text_field_pattern.cpp:8391-8403`） | 正常 |
| AC-5.9 | WHEN options.menuPolicy 为 `MenuPolicy.HIDE` THEN `IsShowMenu` 返回 false，菜单不显示 | 正常 |
| AC-5.10 | WHEN options.menuPolicy 为 `MenuPolicy.DEFAULT` 或不传 options THEN `IsShowMenu` 返回 defaultValue（先前菜单可见性） | 正常 |
| AC-5.11 | WHEN options.forceShowHandle 为 true 且 `!IsShowHandle()` THEN 不走 CloseSelectOverlay(true)，而是走 else 分支显示手柄（用于 PC 触笔选区）（`text_field_pattern.cpp:8369-8379`） | 边界 |
| AC-5.12 | WHEN 选区设置成功且 `RequestKeyboardNotByFocusSwitch(SET_SELECTION)` 成功 THEN `NotifyOnEditChanged(true)` 触发编辑状态变更通知（`text_field_pattern.cpp:8365-8366`） | 正常 |
| AC-5.13 | WHEN 鼠标场景且 isShowMenu 为 false THEN `CloseSelectOverlay()` 关闭选区覆盖层（无菜单）（`text_field_pattern.cpp:8376-8377`） | 边界 |
| AC-5.14 | WHEN 多实例场景 THEN `FREE_NODE_CHECK` 转发到 `SetSelectionFlagMultiThread` 延迟执行（`text_field_pattern_multi_thread.cpp:270`） | 边界 |

### US-6: 停止编辑并退出编辑状态

**作为** 应用开发者,
**我想要** 通过 `controller.stopEditing()` 退出编辑状态并关闭键盘,
**以便** 程序式结束文本输入会话。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `stopEditing()` 且组件已聚焦 THEN `StopEditing` 执行五步：`FocusHub::LostFocusToViewRoot()` 失焦 → `UpdateSelection(caretIndex)` 提交选区 → `StopTwinkling()` 停光标闪烁 → `CloseKeyboard(true)` 关 IME → `MarkDirtyNode(PROPERTY_UPDATE_RENDER)`（`text_field_pattern.cpp:9803-9818`） | 正常 |
| AC-6.2 | WHEN 调用 `stopEditing()` 且组件未聚焦 THEN `!HasFocus()` 直接 return，不执行任何步骤（幂等）（`text_field_pattern.cpp:9807-9808`） | 边界 |
| AC-6.3 | WHEN 多实例场景调用 THEN `FREE_NODE_CHECK` 转发到 `StopEditingMultiThread`，延迟到 `PostAfterAttachMainTreeTask` 执行（`text_field_pattern_multi_thread.cpp:325`） | 边界 |
| AC-6.4 | WHEN 多次连续调用 `stopEditing()` THEN 仅第一次（已聚焦时）执行五步，后续调用因 `!HasFocus()` 幂等返回 | 正常 |

### US-7: 静态版运行时重设 options

**作为** 应用开发者（静态版/ASTC 平面）,
**我想要** 通过 `setTextAreaOptions(value?)` 运行时重设 placeholder/text/controller（@since 26.1.0 staticonly @unpublished）,
**以便** 在静态版组件创建后动态更新初始选项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 静态版调用 `setTextAreaOptions({ placeholder, text, controller })` THEN `SetTextAreaOptionsImpl` 解析 Opt_TextAreaOptions，分别处理 placeholder/text/controller（`text_area_static_modifier.cpp:92-126`） | 正常 |
| AC-7.2 | WHEN 传入 text 为 Bindable 形式 THEN 经 `ProcessBindableText` 分发（同 US-3） | 正常 |
| AC-7.3 | WHEN 传入 controller THEN `GetController` 获取/创建 TextFieldController，`peerPtr->SetController` 绑定（`text_area_static_modifier.cpp:110-124`） | 正常 |
| AC-7.4 | WHEN value 为 undefined 或不传 THEN 重置为默认（静态版 reset-to-default 语义） | 边界 |
| AC-7.5 | WHEN 动态版调用 setTextAreaOptions THEN 不存在该方法（动态 API 无 setTextAreaOptions），仅静态版 @since 26.1.0 staticonly @unpublished 支持 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-01 | XTS/Inspector 验证 tag=TextArea | text_field_model_ng.cpp:139,144 |
| AC-1.2 | R-2 | TASK-01 | XTS 验证 placeholder 渲染 | text_field_model_ng.cpp:143 |
| AC-1.3 | R-2 | TASK-01 | XTS 验证 Resource placeholder | 同上 |
| AC-1.4 | R-3 | TASK-01 | 单测 ProcessBindableText ResourceStr 分支 | text_area_static_modifier.cpp:47-49 |
| AC-1.5 | R-3 | TASK-01 | 同上 | 同上 |
| AC-1.6 | R-4 | TASK-01 | XTS 验证空 placeholder | text_field_model_ng.cpp:143 |
| AC-1.7 | R-4 | TASK-01 | XTS 验证空 text | UpdateTextFieldPattern |
| AC-2.1 | R-5 | TASK-01 | XTS 验证 controller 绑定 | text_area_static_modifier.cpp:104-124 |
| AC-2.2 | R-5 | TASK-01 | XTS 验证自动创建 controller | CreateNode 流程 |
| AC-2.3 | R-6 | TASK-01 | 异常测试 | Converter::GetOpt |
| AC-3.1 | R-7 | TASK-01 | 集成测试 Bindable string | text_area_static_modifier.cpp:50-58 |
| AC-3.2 | R-7 | TASK-01 | 集成测试 Bindable ResourceStr | text_area_static_modifier.cpp:59-67 |
| AC-3.3 | R-8 | TASK-01 | 风险标注 | text_area_static_modifier.cpp:68-70 |
| AC-3.4 | R-7 | TASK-01 | 回调触发验证 | SetOnChangeEvent |
| AC-4.1 | R-9 | TASK-01 | XTS caretPosition 正常 | text_field_pattern.cpp:8311-8327 |
| AC-4.2 | R-9 | TASK-01 | XTS 未聚焦场景 | 同上 |
| AC-4.3 | R-10 | TASK-01 | API12+ 负值测试 | js_text_editable_controller.cpp:69 |
| AC-4.4 | R-10 | TASK-01 | API<12 负值测试 | 同上 |
| AC-4.5 | R-10 | TASK-01 | C-API 钳制测试 | text_area_controller_accessor.cpp:40 |
| AC-4.6 | R-9 | TASK-01 | 超长索引测试 | MoveCaretToContentRect |
| AC-4.7 | R-11 | TASK-01 | 多实例测试 | text_field_pattern_multi_thread.cpp:226 |
| AC-5.1 | R-12 | TASK-01 | XTS setTextSelection 正常 | text_field_controller.cpp:70-88 |
| AC-5.2 | R-13 | TASK-01 | 反向早退测试 | text_field_controller.cpp:72-73 |
| AC-5.3 | R-14 | TASK-01 | 相等即光标测试 | text_field_pattern.cpp:8349-8352 |
| AC-5.4 | R-14 | TASK-01 | 选区分支测试 | text_field_pattern.cpp:8353-8362 |
| AC-5.5 | R-12 | TASK-01 | 超范围钳制测试 | std::clamp |
| AC-5.6 | R-12 | TASK-01 | 负值钳制测试 | 同上 |
| AC-5.7 | R-15 | TASK-01 | 未聚焦/预览早退测试 | text_field_pattern.cpp:8341-8342 |
| AC-5.8 | R-16 | TASK-01 | MenuPolicy SHOW 测试 | IsShowMenu |
| AC-5.9 | R-16 | TASK-01 | MenuPolicy HIDE 测试 | 同上 |
| AC-5.10 | R-16 | TASK-01 | MenuPolicy DEFAULT 测试 | 同上 |
| AC-5.11 | R-17 | TASK-01 | forceShowHandle 测试 | text_field_pattern.cpp:8369 |
| AC-5.12 | R-12 | TASK-01 | NotifyOnEditChanged 测试 | text_field_pattern.cpp:8365 |
| AC-5.13 | R-18 | TASK-01 | 鼠标场景测试 | text_field_pattern.cpp:8376 |
| AC-5.14 | R-11 | TASK-01 | 多实例测试 | text_field_pattern_multi_thread.cpp:270 |
| AC-6.1 | R-19 | TASK-01 | XTS stopEditing 五步测试 | text_field_pattern.cpp:9803-9818 |
| AC-6.2 | R-20 | TASK-01 | 幂等测试 | text_field_pattern.cpp:9807 |
| AC-6.3 | R-11 | TASK-01 | 多实例测试 | text_field_pattern_multi_thread.cpp:325 |
| AC-6.4 | R-20 | TASK-01 | 连续调用幂等测试 | 同上 |
| AC-7.1 | R-21 | TASK-01 | 静态版测试 | text_area_static_modifier.cpp:92-126 |
| AC-7.2 | R-7 | TASK-01 | Bindable 静态测试 | ProcessBindableText |
| AC-7.3 | R-5 | TASK-01 | controller 静态绑定测试 | text_area_static_modifier.cpp:110-124 |
| AC-7.4 | R-22 | TASK-01 | undefined 重置测试 | 静态版 reset 语义 |
| AC-7.5 | R-23 | TASK-01 | 动态版缺失验证 | text_area.d.ts 无此方法 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `TextArea()` 或 `TextArea(value)` 创建组件 | 创建 FrameNode，tag=`TEXTAREA_ETS_TAG`，Pattern=TextFieldPattern，PlaceholderMaxLines=Infinity，IsTextArea()=true | tag 必须为 "TextArea"；PlaceholderMaxLines 必须为 Infinity | AC-1.1 |
| R-2 | 行为 | TextAreaOptions.placeholder 为 string 或 Resource | 转 u16string 写入 TextFieldLayoutProperty::Placeholder，dirty=PROPERTY_UPDATE_MEASURE | 空串为默认 | AC-1.2, AC-1.3 |
| R-3 | 行为 | TextAreaOptions.text 为 ResourceStr（string 或 Resource） | ProcessBindableText 走 Ark_ResourceStr 分支转 u16string 存入 ContentController::content_，不注册 onChange | 无双向绑定 | AC-1.4, AC-1.5 |
| R-4 | 边界 | 未设置 placeholder 或 text | placeholder 默认 u""，text 默认空串 | — | AC-1.6, AC-1.7 |
| R-5 | 行为 | TextAreaOptions.controller 为 TextAreaController 实例 | GetController 获取/创建 TextFieldController，SetController 绑定 peer | 不传则自动创建 | AC-2.1, AC-2.2, AC-7.3 |
| R-6 | 异常 | controller 参数非 TextAreaController | Converter::GetOpt 失败，按未传处理 | — | AC-2.3 |
| R-7 | 行为 | text 为 Bindable<string> 或 Bindable<ResourceStr> | 提取 value + 注册 onChange 到 SetOnChangeEvent | 回调在文本变化时触发 | AC-3.1, AC-3.2, AC-3.4, AC-7.2 |
| R-8 | 异常 | text 为 Bindable<Resource> | no-op，不设值不注册回调 | SDK 注释"应删除"——风险项 | AC-3.3 |
| R-9 | 行为 | 调用 caretPosition(value) 且 value>=0 | MoveCaretToContentRect + UpdateCaretInfo + (聚焦则 StartTwinkling) + CloseSelectOverlay + TriggerAvoidOnCaretChange + MarkDirtyNode(RENDER) | value 超长由 selectController 钳到末尾 | AC-4.1, AC-4.2, AC-4.6 |
| R-10 | 边界 | 调用 caretPosition(value) 且 value<0 | C++ JS 桥：API>=12 钳为 0，API<12 透传；C-API：始终钳为 0 | API 12 行为边界 | AC-4.3, AC-4.4, AC-4.5 |
| R-11 | 边界 | 多实例场景调用 controller 方法 | FREE_NODE_CHECK 转发到 MultiThread 变体，PostAfterAttachMainTask 延迟执行 | 不可重入 | AC-4.7, AC-5.14, AC-6.3 |
| R-12 | 行为 | 调用 setTextSelection(start,end) 且 start<=end 且已聚焦且非预览 | Controller 钳制 [0,length] + ScheduleTaskWithLayoutDeferral → SetSelectionFlag re-clamp + 选区/光标分支 + RequestKeyboard + NotifyOnEditChanged | 负值钳为 0；超长钳到 length | AC-5.1, AC-5.5, AC-5.6, AC-5.12 |
| R-13 | 边界 | setTextSelection 且 selectionEnd < selectionStart | Controller 直接 return，不执行 | — | AC-5.2 |
| R-14 | 行为 | SetSelectionFlag 且 start==end（钳制后） | 走光标分支：MoveCaretToContentRect + StartTwinkling | 不创建选区手柄 | AC-5.3, AC-5.4 |
| R-15 | 边界 | SetSelectionFlag 且 !HasFocus() 或 GetIsPreviewText() | 直接 return，不执行选区 | — | AC-5.7 |
| R-16 | 行为 | options.menuPolicy 设值 | SHOW→显示菜单；HIDE→不显示；DEFAULT或不传→保持先前可见性 | IsShowMenu 解析 | AC-5.8, AC-5.9, AC-5.10 |
| R-17 | 边界 | options.forceShowHandle=true 且 !IsShowHandle() | 不走 CloseSelectOverlay(true)，走 else 显示手柄 | PC 触笔场景 | AC-5.11 |
| R-18 | 边界 | 鼠标场景且 isShowMenu=false | CloseSelectOverlay() 关闭覆盖层 | 无菜单 | AC-5.13 |
| R-19 | 行为 | 调用 stopEditing() 且已聚焦 | 五步：LostFocusToViewRoot→UpdateSelection→StopTwinkling→CloseKeyboard(true)→MarkDirtyNode(RENDER) | — | AC-6.1 |
| R-20 | 恢复 | 调用 stopEditing() 且未聚焦 | 直接 return（幂等） | 多次调用仅首次生效 | AC-6.2, AC-6.4 |
| R-21 | 行为 | 静态版调用 setTextAreaOptions(value) | SetTextAreaOptionsImpl 解析 placeholder/text/controller 并绑定 | 静态专属 @since 26.1.0 staticonly @unpublished | AC-7.1 |
| R-22 | 边界 | setTextAreaOptions 传 undefined 或不传 | 重置为默认（静态版 reset-to-default 语义） | — | AC-7.4 |
| R-23 | 异常 | 动态版调用 setTextAreaOptions | 方法不存在（动态 API 无此方法），不生效 | 仅静态版支持 | AC-7.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.1 创建与 IsTextArea | Inspector/Dump 验证 tag 与 Pattern 类型 | tag="TextArea"；IsTextArea()=true |
| VM-2 | AC-1.2~1.3 placeholder 写入 | XTS 设置后读 LayoutProperty Placeholder 值 | u16string 正确；PROPERTY_UPDATE_MEASURE |
| VM-3 | AC-1.4~1.5 text 写入 | 单测 ProcessBindableText ResourceStr 分支 | content_ 正确；无 onChange 注册 |
| VM-4 | AC-3.1~3.4 Bindable 双向绑定 | 集成测试：修改 Bindable value 验证回写；文本变化验证回调触发 | onChange 回调注册；双向同步 |
| VM-5 | AC-4.1~4.7 caretPosition | XTS：设置后读光标位置/选区状态；API12 边界；多实例 | 光标位置正确；选区关闭；闪烁启停 |
| VM-6 | AC-5.1~5.14 setTextSelection | XTS：选区范围/相等/反向/超范围/MenuPolicy/forceShowHandle/鼠标 | 选区手柄/菜单正确；早退正确 |
| VM-7 | AC-6.1~6.4 stopEditing | XTS：聚焦/未聚焦/连续调用 | 五步执行；幂等；IME 关闭 |
| VM-8 | AC-7.1~7.5 setTextAreaOptions | 静态版测试：运行时重设 options；动态版缺失验证 | 静态专属；reset 语义 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| TextArea(value?: TextAreaOptions) | Public | placeholder?: ResourceStr; text?: ResourceStr \| Bindable<...>; controller?: TextAreaController | TextAreaAttribute | 无 | 创建多行文本输入区域 | AC-1.1~1.5 |
| TextAreaController() | Public | 无 | TextAreaController 实例 | 无 | 控制器构造 | AC-2.1 |
| TextAreaController.caretPosition(value) | Public | value: number(int) | void | 无 | 设置光标位置 | AC-4.1~4.7 |
| TextAreaController.setTextSelection(start, end, options?) | Public | start: number(int); end: number(int); options?: SelectionOptions | void | 无 | 设置文本选区 | AC-5.1~5.14 |
| TextAreaController.stopEditing() | Public | 无 | void | 无 | 停止编辑退出编辑状态 | AC-6.1~6.4 |
| TextAreaAttribute.setTextAreaOptions(value?) | InnerApi(未发布) | value?: TextAreaOptions | this | 无 | 静态版运行时重设 options | AC-7.1~7.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| caretPosition(value: number)→(value: int) | 变更 | 动态版 number → 静态版 int | 参数类型收窄，语义不变；静态版 ASTC 类型系统 | AC-4.x |
| setTextSelection(start: number,...)→(start: int,...) | 变更 | 同上 | 同上 | AC-5.x |
| text?: ResourceStr → text?: ResourceStr \| Bindable<...> | 变更 | 静态版新增 Bindable 联合 | 动态版用 $$/!! 语法；静态版用 Bindable 类型 | AC-3.x |

> **SDK 交叉验证：** 上述签名均经 `api/@internal/component/ets/text_area.d.ts`（动态）与 `api/arkui/component/textArea.static.d.ets`（静态）交叉核对。setTextAreaOptions 仅存在于静态版（`textArea.static.d.ets:1238` @since 26.1.0 staticonly @unpublished），动态版 `text_area.d.ts` 无此方法。

## 接口规格

### 接口定义

**TextArea 构造**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextArea(value?: TextAreaOptions): TextAreaAttribute` |
| 返回值 | `TextAreaAttribute` — 属性链实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.placeholder | ResourceStr | 否 | u"" | string 或 Resource；空串为默认 |
| value.text | ResourceStr \| Bindable<ResourceStr> \| Bindable<Resource> \| Bindable<string> | 否 | 空串 | 静态版支持 Bindable 联合；Bindable<Resource> 无效（no-op） |
| value.controller | TextAreaController | 否 | 自动创建 | 必须为 TextAreaController 实例 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传 placeholder(string) | 写入 Placeholder 属性，PROPERTY_UPDATE_MEASURE | AC-1.2 |
| 2 | 传 placeholder(Resource) | 解析后写入 Placeholder 属性 | AC-1.3 |
| 3 | 传 text(string) | ProcessBindableText ResourceStr 分支转 u16string 存 content_ | AC-1.4 |
| 4 | 传 text(Bindable<string>) | 提取 value + 注册 onChange 到 SetOnChangeEvent | AC-3.1 |
| 5 | 传 text(Bindable<Resource>) | no-op（无效，风险项） | AC-3.3 |
| 6 | 传 controller | GetController + SetController 绑定 | AC-2.1 |
| 7 | 不传 controller | 自动创建 TextFieldController | AC-2.2 |

**TextAreaController.caretPosition**

| 属性 | 值 |
|------|-----|
| 函数签名 | `caretPosition(value: int): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | int | 是 | 无 | 负值：API>=12(JS桥)/C-API 钳为 0；API<12(JS桥) 透传；超长钳到末尾 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value>=0 且已聚焦 | MoveCaret+StartTwinkling+CloseSelectOverlay+MarkDirtyNode | AC-4.1 |
| 2 | value>=0 且未聚焦 | MoveCaret+CloseSelectOverlay+MarkDirtyNode（不 StartTwinkling） | AC-4.2 |
| 3 | value<0 且 API>=12(JS桥) | 钳为 0 后执行 | AC-4.3 |
| 4 | value<0 且 API<12(JS桥) | 透传负值给 MoveCaretToContentRect | AC-4.4 |
| 5 | C-API 调用 value<0 | 始终钳为 0 | AC-4.5 |
| 6 | value>文本长度 | selectController 内部钳到末尾 | AC-4.6 |
| 7 | 多实例场景 | 转发 SetCaretPositionMultiThread 延迟 | AC-4.7 |

**TextAreaController.setTextSelection**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setTextSelection(selectionStart: int, selectionEnd: int, options?: SelectionOptions): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1~5.14 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| selectionStart | int | 是 | 无 | 钳制 [0, length]；end<start 时整体早退 |
| selectionEnd | int | 是 | 无 | 钳制 [0, length] |
| options.menuPolicy | MenuPolicy | 否 | DEFAULT | DEFAULT/HIDE/SHOW |
| options.handlePolicy | HandlePolicy | 否 | DEFAULT | — |
| options.forceShowHandle | boolean | 否 | false | PC 触笔场景 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | start<=end 且已聚焦非预览 | 钳制+延迟+SetSelectionFlag 选区/光标分支 | AC-5.1 |
| 2 | end<start | 直接 return | AC-5.2 |
| 3 | start==end | 光标分支 | AC-5.3 |
| 4 | start<end | 选区分支+手柄移动 | AC-5.4 |
| 5 | start/end 超长 | 钳到 length | AC-5.5 |
| 6 | start/end 负值 | 钳到 0 | AC-5.6 |
| 7 | 未聚焦或预览文本 | SetSelectionFlag 早退 | AC-5.7 |
| 8 | menuPolicy=SHOW | 显示菜单 | AC-5.8 |
| 9 | menuPolicy=HIDE | 不显示菜单 | AC-5.9 |
| 10 | menuPolicy=DEFAULT | 保持先前可见性 | AC-5.10 |
| 11 | forceShowHandle=true | 显示手柄 | AC-5.11 |
| 12 | RequestKeyboard 成功 | NotifyOnEditChanged(true) | AC-5.12 |
| 13 | 鼠标且 isShowMenu=false | CloseSelectOverlay | AC-5.13 |
| 14 | 多实例 | 转发 SetSelectionFlagMultiThread | AC-5.14 |

**TextAreaController.stopEditing**

| 属性 | 值 |
|------|-----|
| 函数签名 | `stopEditing(): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1~6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | — | — | — | 无入参；未聚焦时幂等返回 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 已聚焦 | 五步：失焦→提交选区→停闪烁→关IME→标记渲染 | AC-6.1 |
| 2 | 未聚焦 | 直接 return（幂等） | AC-6.2 |
| 3 | 多实例 | 转发 StopEditingMultiThread 延迟 | AC-6.3 |
| 4 | 连续调用 | 仅首次执行，后续幂等 | AC-6.4 |

**TextAreaAttribute.setTextAreaOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setTextAreaOptions(value?: TextAreaOptions): this` |
| 返回值 | this（链式） |
| 开放范围 | InnerApi（@unpublished @since 26.1.0 staticonly） |
| 错误码 | N/A |
| 关联 AC | AC-7.1~7.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | TextAreaOptions | 否 | undefined | undefined 重置默认；静态专属，动态版无此方法 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 静态版传完整 options | SetTextAreaOptionsImpl 解析并绑定 | AC-7.1 |
| 2 | 传 Bindable text | ProcessBindableText 分发 | AC-7.2 |
| 3 | 传 controller | GetController+SetController | AC-7.3 |
| 4 | 传 undefined | 重置默认 | AC-7.4 |
| 5 | 动态版调用 | 方法不存在，不生效 | AC-7.5 |

## 兼容性声明

- **已有 API 行为变更:** 是。`caretPosition` 负值处理在 API 12 存在行为边界：API<12 C++ JS 桥透传负值，API>=12 钳为 0；C-API 访问器始终钳制。`text` 属性静态版新增 Bindable 联合类型（动态版仅 ResourceStr，用 `$$`/`!!` 语法实现双向绑定）。`setTextAreaOptions` 为静态专属未发布 API，动态版无对应。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（placeholder/text 构造）、API 8（controller/caretPosition）、API 10（setTextSelection/stopEditing）；静态版 @since 23 static；setTextAreaOptions @since 26.1.0 staticonly @unpublished
- **API 版本号策略:** 动态版保留各 API 历史 @since（7/8/10）；静态版统一 @since 23 static，API 24/26 static/26.0.0 static 分别标注新增；setTextAreaOptions 标注 staticonly + @unpublished

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 共享 Pattern | TextArea 必须使用 TextFieldPattern（非 TextAreaPattern），靠 IsTextArea() 属性判别 | AC-1.1 |
| TEXTAREA_ETS_TAG + PlaceholderMaxLines=Infinity | 创建时必须设置此二者使 IsTextArea()=true | AC-1.1 |
| Controller 共享 | TextAreaController(TS)=TextFieldController(C++) via JSTextEditableController 别名 | AC-2.x, AC-4.x~6.x |
| 三层桥接 | 视图创建在 ArkTS+C-API 桥；C++ JS 桥仅控制器 | AC-1.x, AC-3.x |
| Bindable 仅 C-API 桥处理 | ProcessBindableText 是唯一 Bindable 处理点 | AC-3.x |
| ScheduleTaskWithLayoutDeferral | setTextSelection 延迟到布局后执行 SetSelectionFlag | AC-5.1 |
| FREE_NODE_CHECK 多实例转发 | 所有 Pattern 方法经 FREE_NODE_CHECK 检测多实例 | AC-4.7, AC-5.14, AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | caretPosition/stopEditing 调用后PROPERTY_UPDATE_RENDER 单帧内刷新 | XTS 帧率监控 | text_field_pattern.cpp:8326,9817 |
| 可靠性 | stopEditing 幂等，多次调用无副作用 | 单测连续调用 | text_field_pattern.cpp:9807 |
| 可测试性 | IsTextArea() 可通过 Inspector/Dump 验证 | Inspector | text_field_pattern.cpp:1311 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | TextArea 作为可编辑文本节点暴露给无障碍；stopEditing 失焦影响无障碍焦点 | AC-6.1（LostFocusToViewRoot） |
| 大字体 | 否 | 本 Feat 不涉及字体缩放（属 Feat-02/03） | — |
| 深色模式 | 否 | 本 Feat 不涉及颜色主题（placeholder/text 默认值取主题，属 Feat-02） | — |
| 多窗口/分屏 | 是 | stopEditing 的 CloseKeyboard(true) 影响多窗口 IME；多实例场景经 FREE_NODE_CHECK 处理 | AC-4.7, AC-5.14, AC-6.3 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | caretPosition API 12 负值行为边界；setTextAreaOptions 静态专属未发布 | AC-4.3~4.5, AC-7.5 |
| 生态兼容 | 是 | 动态版 Bindable 用 $$/!! 语法；静态版用 Bindable 类型；setTextAreaOptions 动态版缺失 | AC-3.x, AC-7.5 |

## 行为场景（可选，Gherkin）

> 本 Feat 为 L2 复杂（多分支行为），使用 Gherkin 场景表达关键行为。

```gherkin
Feature: TextArea 内容创建与控制器
  作为 应用开发者
  我想要 创建 TextArea 并通过控制器管理光标、选区与编辑状态
  以便 程序式控制多行文本输入会话

  Scenario: 创建 TextArea 并设置 placeholder 与 text
    Given 未创建 TextArea 组件
    When 调用 TextArea({ placeholder: "请输入", text: "初始" })
    Then 创建 FrameNode 且 tag 为 "TextArea"
    And Pattern 为 TextFieldPattern 且 IsTextArea() 返回 true
    And placeholder "请输入" 写入 LayoutProperty（PROPERTY_UPDATE_MEASURE）
    And text "初始" 存入 ContentController::content_

  Scenario: caretPosition 在 API 12+ 钳制负值
    Given 组件已聚焦且运行环境 API >= 12
    When 调用 controller.caretPosition(-5)
    Then 负值钳为 0
    And 光标移动到位置 0 且 StartTwinkling 且 CloseSelectOverlay

  Scenario Outline: setTextSelection 按相等与否走不同分支
    Given 组件已聚焦且非预览文本
    When 调用 controller.setTextSelection(<start>, <end>)
    Then <预期>

    Examples:
      | start | end | 预期 |
      | 0 | 0 | 走光标分支：MoveCaret+StartTwinkling |
      | 2 | 5 | 走选区分支：HandleSetSelection+MoveHandle |
      | 5 | 2 | 直接 return（end<start 早退） |
      | -1 | 100 | 钳制为 0 和 length 后走选区分支 |

  Scenario: stopEditing 幂等
    Given 组件已聚焦
    When 连续调用 controller.stopEditing() 两次
    Then 第一次执行五步（失焦→提交选区→停闪烁→关IME→标记渲染）
    And 第二次因 !HasFocus() 幂等返回不执行
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰——本 Feat 仅覆盖创建与控制器三方法 + Bindable + setTextAreaOptions）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "TextArea 与 TextField 共享 Pattern 的架构决策；TextAreaPattern 为何从未实例化"
  - repo: "openharmony/arkui_ace_engine"
    query: "ProcessBindableText 如何处理 Bindable<ResourceStr>/Bindable<string>/Bindable<Resource> 三种联合类型"
  - repo: "openharmony/arkui_ace_engine"
    query: "TextAreaController.caretPosition 在 API 12 前后的负值钳制行为差异"
  - repo: "openharmony/arkui_ace_engine"
    query: "setTextSelection 的 ScheduleTaskWithLayoutDeferral 延迟执行机制与 SetSelectionFlag 分支"
  - repo: "openharmony/arkui_ace_engine"
    query: "stopEditing 五步骤与幂等性实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "setTextAreaOptions 静态专属未发布 API 的归属平面"
```

**关键文档：** `specs/05-ui-components/09-text-components/05-text-area/design.md`（DESIGN-Func-05-09-05）；SDK `api/@internal/component/ets/text_area.d.ts`（动态）、`api/arkui/component/textArea.static.d.ets`（静态）
