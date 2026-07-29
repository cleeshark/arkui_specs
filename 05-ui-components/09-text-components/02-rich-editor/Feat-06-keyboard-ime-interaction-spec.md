# 特性规格

> Func-05-09-02-Feat-06 键盘与输入法交互：固化 RichEditor 组件键盘配置属性（自定义键盘 `customKeyboard`、聚焦拉起键盘 `enableKeyboardOnFocus`、回车键类型 `enterKeyType`、键盘外观 `keyboardAppearance`、预上屏开关 `enablePreviewText`）与 IME 输入交互事件（输入前拦截 `aboutToIMEInput`、输入完成后 `onDidIMEInput`、IME 输入完成 `onIMEInputComplete`、IME 绑定前 `onWillAttachIME`）的行为规格。属性用于配置键盘行为，事件用于监控和拦截 IME 交互过程。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 键盘与输入法交互 (Keyboard & IME Interaction) |
| 特性编号 | Func-05-09-02-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10+ 至 API 22+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 `customKeyboard` 行为规格 | 自定义键盘替换系统键盘，含 CustomBuilder 和 ComponentContent 双路径，支持 KeyboardOptions 避让配置 |
| MODIFIED | 补齐 `enableKeyboardOnFocus` 行为规格 | 聚焦时是否自动拉起键盘开关，存储于 `needToRequestKeyboardOnFocus_` |
| MODIFIED | 补齐 `enterKeyType` 行为规格 | 回车键类型配置，映射为 TextInputAction 枚举，影响 IME 回车键行为 |
| MODIFIED | 补齐 `keyboardAppearance` 行为规格 | 键盘外观配置（沉浸式/渐变/流光），在 IME 绑定前传递给输入法框架 |
| MODIFIED | 补齐 `enablePreviewText` 行为规格 | 预上屏开关，控制 IME 组词阶段预览文本的显示与提交 |
| MODIFIED | 补齐 `aboutToIMEInput` 行为规格 | IME 输入前拦截回调，返回布尔值决定是否接受输入，含预上屏内容路径 |
| MODIFIED | 补齐 `onDidIMEInput` 行为规格 | IME 输入完成后回调，返回 TextRange 标识变更范围 |
| MODIFIED | 补齐 `onIMEInputComplete` 行为规格 | IME 输入完成回调，返回 RichEditorAbstractSpanResult 含完整 Span 信息 |
| MODIFIED | 补齐 `onWillAttachIME` 行为规格 | IME 绑定前回调（API 22+），允许通过 IMEClient 自定义输入法配置 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/09-text-components/02-rich-editor/design.md` | 已创建 |

---

## 用户故事

### US-1: 自定义键盘（customKeyboard）

**作为** 应用开发者,
**我想要** 使用自定义构建器替换 RichEditor 的系统键盘,
**以便** 提供特定场景下的自定义输入面板（如数字键盘、表情面板等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `customKeyboard(value: CustomBuilder | ComponentContentBase, options?: KeyboardOptions)` 传入 ComponentContentBase THEN Bridge 从参数对象提取 `builderNode_.nodePtr_`，调用 `setRichEditorCustomKeyboard(nativeNode, nodeHandle, supportAvoidance, false)`（`arkts_native_rich_editor_bridge.cpp:2706-2738`） | 正常 |
| AC-1.2 | WHEN 传入 CustomBuilder（JsView 模式）THEN Bridge 通过 `SetCustomKeyboardJS` 解析 builder 函数和 `supportAvoidance` 布尔值，调用 `setRichEditorCustomKeyboard`（`arkts_native_rich_editor_bridge.cpp:2740-2810`） | 正常 |
| AC-1.3 | WHEN 设置自定义键盘后组件获得焦点 THEN `RequestKeyboard` 检测到 `customKeyboardNode_` 或 `customKeyboardBuilder_` 非空，调用 `RequestCustomKeyboard()` 替代系统键盘路径（`rich_editor_pattern.cpp:5830-5831`） | 正常 |
| AC-1.4 | WHEN `RequestCustomKeyboard` 执行 THEN 先调用 `InputMethodController::RequestHideInput` 关闭系统键盘，再通过 `overlayManager->BindKeyboard` 或 `BindKeyboardWithNode` 绑定自定义键盘节点，设置 `isCustomKeyboardAttached_ = true`（`rich_editor_pattern.cpp:6319-6374`） | 正常 |
| AC-1.5 | WHEN options.supportAvoidance 为 true THEN 存储到 `keyboardAvoidance_`，`overlayManager->SetCustomKeyboardOption(keyboardAvoidance_)` 启用自定义键盘避让（`rich_editor_pattern.cpp:6289-6291, 6360`） | 正常 |
| AC-1.6 | WHEN 调用 `customKeyboard(undefined)` 或参数非对象 THEN Bridge 调用 `resetRichEditorCustomKeyboard(nativeNode)`（`arkts_native_rich_editor_bridge.cpp:2736`） | 边界 |
| AC-1.7 | WHEN 自定义键盘已附加且设置新的 ComponentContentBase 键盘 THEN `SetCustomKeyboardWithNode` 先调用 `CloseCustomKeyboard()` 关闭当前键盘，再刷新 `customKeyboardNode_`（`rich_editor_pattern.cpp:6297-6302`） | 边界 |
| AC-1.8 | WHEN 关闭自定义键盘 THEN `CloseCustomKeyboard` 调用 `overlayManager->CloseKeyboard(frameNode->GetId())`，设置 `isCustomKeyboardAttached_ = false`（`rich_editor_pattern.cpp:6393-6408`） | 正常 |

### US-2: 聚焦拉起键盘开关（enableKeyboardOnFocus）

**作为** 应用开发者,
**我想要** 控制 RichEditor 组件获得焦点时是否自动拉起键盘,
**以便** 在特定场景下阻止焦点自动触发键盘弹出。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `enableKeyboardOnFocus(value: boolean)` 传入 true THEN Bridge 调用 `setRichEditorEnableKeyboardOnFocus(nativeNode, true)`，ModelNG 调用 `SetRequestKeyboardOnFocus(true)` 存储到 `needToRequestKeyboardOnFocus_ = true`（`arkts_native_rich_editor_bridge.cpp:2374-2391`, `rich_editor_model_ng.cpp:793-798`, `rich_editor_pattern.cpp:14948-14952`） | 正常 |
| AC-2.2 | WHEN 调用 `enableKeyboardOnFocus(false)` THEN `needToRequestKeyboardOnFocus_` 设为 false，焦点获取时不自动请求键盘（`rich_editor_pattern.cpp:14950-14951`） | 正常 |
| AC-2.3 | WHEN 调用 `enableKeyboardOnFocus(undefined)` 或非布尔值 THEN Bridge 调用 `resetRichEditorEnableKeyboardOnFocus(nativeNode)`（`arkts_native_rich_editor_bridge.cpp:2384-2386`） | 边界 |
| AC-2.4 | WHEN 未设置该属性 THEN `needToRequestKeyboardOnFocus_` 默认为 true，组件获得焦点时自动拉起键盘（`rich_editor_pattern.h:1442`） | 边界 |

### US-3: 回车键类型（enterKeyType）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件的回车键类型,
**以便** 控制输入法回车键的行为样式（如完成、前往、搜索等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `enterKeyType(value: EnterKeyType)` 传入有效枚举值 THEN Bridge 将 EnterKeyType 转为 uint32，调用 `setRichEditorEnterKeyType(nativeNode, enterKeyType)`，ModelNG 调用 `SetEnterKeyType` 映射为 `TextInputAction` 存储到 `action_`（`arkts_native_rich_editor_bridge.cpp:2477-2504`, `rich_editor_model_ng.cpp:565-573`） | 正常 |
| AC-3.2 | WHEN 传入 `EnterKeyType.UNSPECIFIED` THEN ModelNG 将其映射为 `TextInputAction::NEW_LINE`（`rich_editor_model_ng.cpp:570-572`） | 边界 |
| AC-3.3 | WHEN JsView 模式且 enterKeyType 值超出 `[TextInputAction::BEGIN, TextInputAction::END]` 范围 THEN Bridge 回退为 `TextInputAction::NEW_LINE`（`arkts_native_rich_editor_bridge.cpp:2495-2498`） | 边界 |
| AC-3.4 | WHEN IME 配置变更 THEN `OnConfigurationChange` 调用 `config.SetEnterKeyType(static_cast<MiscServices::EnterKeyType>(action_))` 将回车键类型传递给输入法框架（`rich_editor_pattern.cpp:12162`） | 正常 |
| AC-3.5 | WHEN 回车键按下且 `action_` 为 `NEW_LINE` THEN `PerformAction` 执行 `InsertValue(u"\n", true)` 插入换行符，不退出编辑状态（`rich_editor_pattern.cpp:12234-12238`） | 正常 |
| AC-3.6 | WHEN 回车键按下且 `action_` 非 `NEW_LINE` THEN `PerformAction` 触发 `FireOnSubmit` 回调，若 `event.IsKeepEditable()` 为 false 则调用 `StopEditing()` 退出编辑（`rich_editor_pattern.cpp:12240-12248`） | 正常 |
| AC-3.7 | WHEN 未设置 enterKeyType THEN `action_` 默认为 `TextInputAction::NEW_LINE`，`GetDefaultTextInputAction()` 返回 `NEW_LINE`（`rich_editor_pattern.h:1417`, `rich_editor_pattern.cpp:12259-12262`） | 边界 |

### US-4: 键盘外观（keyboardAppearance）

**作为** 应用开发者,
**我想要** 设置 RichEditor 组件的键盘外观模式,
**以便** 控制系统键盘的沉浸式效果、渐变和流光等视觉效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `keyboardAppearance(value: KeyboardAppearance)` 传入有效枚举值 THEN Bridge 将值转为 uint32 调用 `setRichEditorKeyboardAppearance(nativeNode, value)`，ModelNG 调用 `SetKeyboardAppearance` 存储到 `keyboardAppearance_`（`arkts_native_rich_editor_bridge.cpp:2675-2691`, `rich_editor_model_ng.cpp:1046-1051`, `rich_editor_pattern.cpp:15059-15063`） | 正常 |
| AC-4.2 | WHEN `keyboardAppearance` 设为 `IMMERSIVE`/`LIGHT_IMMERSIVE`/`DARK_IMMERSIVE` THEN 在 IME 绑定前 `BeforeAttachInputMethod` 将 `keyboardAppearance_` 值通过 `textConfig` 传递给输入法框架（`rich_editor_pattern.cpp:6006-6015`） | 正常 |
| AC-4.3 | WHEN `keyboardAppearance` 设为 `IMMERSIVE` 且配置了 `KeyboardAppearanceConfig` THEN `SetKeyboardAppearanceConfig` 将 `gradientMode` 存入 `imeGradientMode_`，`fluidLightMode` 存入 `imeFluidLightMode_`，在 `BeforeAttachInputMethod` 中传递给 `textConfig.inputAttribute`（`rich_editor_pattern.cpp:15065-15071, 6010-6011`） | 正常 |
| AC-4.4 | WHEN 调用 `keyboardAppearance(undefined)` 或非数字值 THEN Bridge 不执行设置操作，`keyboardAppearance_` 保持默认值 `NONE_IMMERSIVE`（`arkts_native_rich_editor_bridge.cpp:2685`, `rich_editor_pattern.h:1465`） | 边界 |
| AC-4.5 | WHEN 未设置 keyboardAppearance THEN `keyboardAppearance_` 默认为 `KeyboardAppearance::NONE_IMMERSIVE`，`GetKeyboardAppearance()` 返回该默认值（`rich_editor_pattern.h:1465`, `rich_editor_pattern.cpp:15073-15076`） | 边界 |

### US-5: 预上屏开关（enablePreviewText）

**作为** 应用开发者,
**我想要** 控制 RichEditor 组件是否启用预上屏功能,
**以便** 在 IME 组词阶段实时显示候选文本，提升输入法交互体验。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `enablePreviewText(value: boolean)` 传入 true THEN Bridge 调用 `setRichEditorEnablePreviewText(nativeNode, true)`，ModelNG 调用 `SetSupportPreviewText(true)` 存储到 `isTextPreviewSupported_ = true`（`arkts_native_rich_editor_bridge.cpp:2407-2424`, `rich_editor_model_ng.cpp:461-467`, `rich_editor_pattern.cpp:14460-14464`） | 正常 |
| AC-5.2 | WHEN `isTextPreviewSupported_` 为 true 且 IME 发送预上屏文本 THEN `SetPreviewText` 被调用，初始化 `PreviewTextRecord` 并通过 `ProcessInsertValue` 以 `OperationType::IME` 插入预览文本（`rich_editor_pattern.cpp:6425-6447, 6490-6516`） | 正常 |
| AC-5.3 | WHEN IME 更新预上屏文本（已处于预上屏状态）THEN `UpdatePreviewText` 被调用，替换当前预览内容并更新光标位置（`rich_editor_pattern.cpp:6569`） | 正常 |
| AC-5.4 | WHEN IME 完成预上屏（确认输入）THEN `FinishTextPreview` 清除预览文本并重新插入最终内容，以 `OperationType::FINISH_PREVIEW` 调用 `ProcessInsertValue`（`rich_editor_pattern.cpp:6648-6664`） | 正常 |
| AC-5.5 | WHEN 预上屏期间处于拖拽状态 THEN `CheckPreviewTextValidate` 返回 `ERROR_BAD_PARAMETERS`，拒绝预上屏操作（`rich_editor_pattern.cpp:6411-6418`） | 边界 |
| AC-5.6 | WHEN 调用 `enablePreviewText(undefined)` 或非布尔值 THEN Bridge 调用 `resetRichEditorEnablePreviewText(nativeNode)`（`arkts_native_rich_editor_bridge.cpp:2417-2419`） | 边界 |
| AC-5.7 | WHEN 未设置 enablePreviewText THEN `isTextPreviewSupported_` 默认为 true，组件初始化时从 `pipelineContext->GetSupportPreviewText()` 获取初始值（`rich_editor_pattern.h:1426`, `rich_editor_model_ng.cpp:101`） | 边界 |

### US-6: IME 输入前拦截（aboutToIMEInput）

**作为** 应用开发者,
**我想要** 在 IME 输入内容前拦截并决定是否接受输入,
**以便** 实现输入内容过滤、格式校验等自定义逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN IME 发起输入且已注册 `aboutToIMEInput` 回调 THEN `BeforeIMEInsertValue` 构造 `RichEditorInsertValue`，设置 `insertOffset`（当前光标位置）和 `insertValue`（或 `previewText`），调用 `FireAboutToIMEInput`（`rich_editor_pattern.cpp:7123-7135`） | 正常 |
| AC-6.2 | WHEN `aboutToIMEInput` 回调返回 true THEN 允许输入继续，`BeforeIMEInsertValue` 返回 true，后续执行文本插入流程（`rich_editor_event_hub.cpp:45-52`） | 正常 |
| AC-6.3 | WHEN `aboutToIMEInput` 回调返回 false THEN 拒绝输入，`BeforeIMEInsertValue` 返回 false，文本不会被插入（`rich_editor_event_hub.cpp:50-51`） | 正常 |
| AC-6.4 | WHEN 处于预上屏状态 THEN `BeforeIMEInsertValue` 将 `previewTextRecord_.newPreviewContent` 设置到 `RichEditorInsertValue.previewText` 而非 `insertValue` 字段（`rich_editor_pattern.cpp:7129-7133`） | 正常 |
| AC-6.5 | WHEN 未注册回调 THEN `FireAboutToIMEInput` 直接返回 true，默认允许所有输入（`rich_editor_event_hub.cpp:47-48`） | 边界 |
| AC-6.6 | WHEN Bridge 层回调返回值非布尔 THEN 默认返回 true，允许输入（`arkts_native_rich_editor_bridge.cpp:2005-2008`） | 边界 |
| AC-6.7 | WHEN 调用 `aboutToIMEInput(undefined)` 或非函数 THEN Bridge 调用 `resetRichEditorAboutToIMEInput(nativeNode)` 清除回调（`arkts_native_rich_editor_bridge.cpp:1983-1987`） | 边界 |

### US-7: IME 输入完成后（onDidIMEInput）

**作为** 应用开发者,
**我想要** 在 IME 输入完成后获取变更的文本范围,
**以便** 进行后续处理（如自动格式化、内容同步等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN IME 输入完成且已注册 `onDidIMEInput` 回调 THEN `AfterIMEInsertValue` 构造 `TextRange{ caretPosition_, caretPosition_ + insertValueLength }`，调用 `FireOnDidIMEInput`（`rich_editor_pattern.cpp:7192-7196`） | 正常 |
| AC-7.2 | WHEN 回调被触发 THEN Bridge 将 `TextRange` 包装为含 `start` 和 `end` 属性的 JS 对象传递给回调函数（`arkts_native_rich_editor_bridge.cpp:2831-2848`） | 正常 |
| AC-7.3 | WHEN 未注册回调 THEN `FireOnDidIMEInput` 检查 `onDidIMEInput_` 为空直接返回，不执行任何操作（`rich_editor_event_hub.cpp:70-73`） | 边界 |
| AC-7.4 | WHEN 调用 `onDidIMEInput(undefined)` 或非函数 THEN Bridge 调用 `resetRichEditorOnDidIMEInput(nativeNode)` 清除回调（`arkts_native_rich_editor_bridge.cpp:2821-2825`） | 边界 |
| AC-7.5 | WHEN 非预上屏的 IME 输入完成 THEN `onDidIMEInput` 在 `onIMEInputComplete` 之后被触发，两者在同一次 `AfterIMEInsertValue` 调用中依次触发（`rich_editor_pattern.cpp:7194-7196`） | 正常 |

### US-8: IME 输入完成（onIMEInputComplete）

**作为** 应用开发者,
**我想要** 在 IME 输入完成后获取插入 Span 的完整信息,
**以便** 获取插入文本的样式、位置等详细信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN IME 输入完成且已注册 `onIMEInputComplete` 回调 THEN `AfterIMEInsertValue` 构造 `RichEditorAbstractSpanResult`，设置 spanIndex、spanRange、value、fontColor、fontSize 等属性，调用 `FireOnIMEInputComplete`（`rich_editor_pattern.cpp:7161-7194`） | 正常 |
| AC-8.2 | WHEN 处于预上屏状态 THEN `RichEditorAbstractSpanResult` 的 value 字段设置为 `previewTextRecord_.newPreviewContent` 而非 `spanItem->content`（`rich_editor_pattern.cpp:7165-7168`） | 正常 |
| AC-8.3 | WHEN 回调被触发 THEN Bridge 通过 `CreateAbstractSpanResult` 将 `RichEditorAbstractSpanResult` 序列化为 JS 对象，设置 NativePointer 字段供开发者访问（`arkts_native_rich_editor_bridge.cpp:878-891`） | 正常 |
| AC-8.4 | WHEN 未注册回调 THEN `FireOnIMEInputComplete` 检查 `onIMEInputComplete_` 为空直接返回（`rich_editor_event_hub.cpp:59-63`） | 边界 |
| AC-8.5 | WHEN 调用 `onIMEInputComplete(undefined)` 或非函数 THEN Bridge 调用 `resetRichEditorOnIMEInputComplete(nativeNode)` 清除回调（`arkts_native_rich_editor_bridge.cpp:868-872`） | 边界 |

### US-9: IME 绑定前回调（onWillAttachIME）

**作为** 应用开发者,
**我想要** 在 IME 绑定到组件前获取 IMEClient 并自定义输入法配置,
**以便** 实现高级输入法定制（如配置 extraInfo 等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 组件获得焦点并准备绑定 IME THEN `BeforeAttachInputMethod` 调用 `GetIMEClientInfo()` 构造 `IMEClient`（含 `nodeId`），再调用 `FireOnWillAttachIME(clientInfo)`（`rich_editor_pattern.cpp:6006-6009`） | 正常 |
| AC-9.2 | WHEN `onWillAttachIME` 回调被触发 THEN 回调可通过 `IMEClient.extraInfo` 设置额外输入法配置，`BeforeAttachInputMethod` 将 `extraInfo->GetExtraInfo()` 传递给 `textConfig.inputAttribute.extraConfig`（`rich_editor_pattern.cpp:6012-6014`） | 正常 |
| AC-9.3 | WHEN 回调中设置了 `extraInfo` 且 `gradientMode`/`fluidLightMode` 非默认 THEN `BeforeAttachInputMethod` 将 `imeGradientMode_` 和 `imeFluidLightMode_` 传递给 `textConfig.inputAttribute`（`rich_editor_pattern.cpp:6010-6011`） | 正常 |
| AC-9.4 | WHEN 未注册回调 THEN `FireOnWillAttachIME` 检查 `onWillAttachIME_` 为空直接返回，IME 正常绑定（`rich_editor_event_hub.cpp:331-336`） | 边界 |
| AC-9.5 | WHEN 调用 `onWillAttachIME(undefined)` 或非函数 THEN Bridge 调用 `resetRichEditorOnWillAttachIME(nativeNode)` 清除回调（`arkts_native_rich_editor_bridge.cpp:2881-2883`） | 边界 |
| AC-9.6 | WHEN Bridge 解析回调 THEN 通过 `parseAndCreateIMEAttachCallback` 将 JS 函数包装为 `IMEAttachCallback`（`arkts_native_rich_editor_bridge.cpp:2887`） | 正常 |

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.8 | R-1, R-2, R-3 | N/A（存量） | 代码审查 | `arkts_native_rich_editor_bridge.cpp:2706-2738, 2740-2810`, `rich_editor_pattern.cpp:5830-5831, 6294-6317, 6319-6374, 6393-6408`, `rich_editor_pattern.h:1349, 1385, 1423, 1468` |
| AC-2.1~2.4 | R-4, R-5 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:2374-2391`, `rich_editor_model_ng.cpp:793-814`, `rich_editor_pattern.cpp:14948-14957`, `rich_editor_pattern.h:1442` |
| AC-3.1~3.7 | R-6, R-7, R-8 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:2477-2504`, `rich_editor_model_ng.cpp:565-583`, `rich_editor_pattern.cpp:12162, 12228-12248, 12259-12262`, `rich_editor_pattern.h:1417` |
| AC-4.1~4.5 | R-9, R-10 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:2675-2691`, `rich_editor_model_ng.cpp:1046-1051, 1154-1175`, `rich_editor_pattern.cpp:15059-15076, 6006-6015`, `rich_editor_pattern.h:1465-1467` |
| AC-5.1~5.7 | R-11, R-12, R-13 | N/A | 代码审查 | `arkts_native_rich_editor_bridge.cpp:2407-2424`, `rich_editor_model_ng.cpp:461-467, 101`, `rich_editor_pattern.cpp:6425-6447, 6490-6516, 6569, 6648-6664, 14460-14469`, `rich_editor_pattern.h:1426, 270-285` |
| AC-6.1~6.7 | R-14, R-15 | N/A | 代码审查 | `rich_editor_pattern.cpp:7123-7135`, `rich_editor_event_hub.cpp:40-52`, `arkts_native_rich_editor_bridge.cpp:1969-2013`, `rich_editor_value.h:24-63` |
| AC-7.1~7.5 | R-16, R-17 | N/A | 代码审查 | `rich_editor_pattern.cpp:7192-7196`, `rich_editor_event_hub.cpp:65-74`, `arkts_native_rich_editor_bridge.cpp:2810-2852` |
| AC-8.1~8.5 | R-18, R-19 | N/A | 代码审查 | `rich_editor_pattern.cpp:7161-7194`, `rich_editor_event_hub.cpp:54-63`, `arkts_native_rich_editor_bridge.cpp:857-895` |
| AC-9.1~9.6 | R-20, R-21 | N/A | 代码审查 | `rich_editor_pattern.cpp:5845-5861, 6006-6015`, `rich_editor_event_hub.cpp:326-336`, `arkts_native_rich_editor_bridge.cpp:2870-2905`, `text_field_event_hub.h:90-96` |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `customKeyboard(value, options?)` 传入 ComponentContentBase | Bridge 提取 `builderNode_.nodePtr_` → `setRichEditorCustomKeyboard` → `SetCustomKeyboardWithNode` 存入 `customKeyboardNode_` | 支持两种路径：ComponentContentBase 和 CustomBuilder（`rich_editor_pattern.h:1468`） | AC-1.1, AC-1.3 |
| R-2 | 行为 | 组件获得焦点且已配置自定义键盘 | `RequestKeyboard` 走自定义键盘分支 → `RequestCustomKeyboard` 关闭系统键盘 → 绑定自定义节点 → `isCustomKeyboardAttached_ = true` | 先关闭系统键盘再绑定自定义键盘（`rich_editor_pattern.cpp:6319-6374`） | AC-1.3, AC-1.4 |
| R-3 | 边界 | 自定义键盘已附加时设置新键盘 | `SetCustomKeyboardWithNode` 先 `CloseCustomKeyboard()` 再刷新 `customKeyboardNode_`，若正在编辑则重新 `RequestKeyboard` | 避免键盘叠加，确保平滑切换（`rich_editor_pattern.cpp:6294-6317`） | AC-1.7, AC-1.8 |
| R-4 | 行为 | 调用 `enableKeyboardOnFocus(value: boolean)` | Bridge → `setRichEditorEnableKeyboardOnFocus` → `SetRequestKeyboardOnFocus` 存入 `needToRequestKeyboardOnFocus_` | `needToRequestKeyboardOnFocus_` 类型 bool，默认 true（`rich_editor_pattern.h:1442`） | AC-2.1, AC-2.2 |
| R-5 | 边界 | 未设置 `enableKeyboardOnFocus` 或重置 | `needToRequestKeyboardOnFocus_` 默认 true，组件获得焦点时自动拉起键盘 | 默认行为为自动拉起键盘（`rich_editor_pattern.cpp:14954-14957`） | AC-2.3, AC-2.4 |
| R-6 | 行为 | 调用 `enterKeyType(value: EnterKeyType)` 传入有效值 | Bridge 转 uint32 → `SetEnterKeyType` 映射为 `TextInputAction` → `UpdateTextInputAction` 存入 `action_` | `action_` 类型 `TextInputAction`，默认 `NEW_LINE`（`rich_editor_pattern.h:1417`） | AC-3.1 |
| R-7 | 行为 | IME 回车键按下 | `PerformAction` 根据 `action_` 值决定行为：`NEW_LINE` 插入换行不退出，其他类型触发 `FireOnSubmit` 并可能退出编辑 | `NEW_LINE` 之外的动作需 `event.IsKeepEditable() == false` 才退出（`rich_editor_pattern.cpp:12228-12248`） | AC-3.5, AC-3.6 |
| R-8 | 边界 | `enterKeyType` 值超出有效范围 | JsView 模式回退为 `TextInputAction::NEW_LINE`；`UNSPECIFIED` 映射为 `NEW_LINE` | 有效范围 `[BEGIN, END]`（`arkts_native_rich_editor_bridge.cpp:2495-2498`） | AC-3.2, AC-3.3 |
| R-9 | 行为 | 调用 `keyboardAppearance(value: KeyboardAppearance)` 传入有效值 | Bridge → `setRichEditorKeyboardAppearance` → `SetKeyboardAppearance` 存入 `keyboardAppearance_` | `keyboardAppearance_` 类型 `KeyboardAppearance`，默认 `NONE_IMMERSIVE`（`rich_editor_pattern.h:1465`） | AC-4.1, AC-4.2 |
| R-10 | 边界 | 未设置 `keyboardAppearance` | `keyboardAppearance_` 默认 `NONE_IMMERSIVE`，`GetKeyboardAppearance()` 返回默认值；IME 绑定时不传递沉浸式配置 | 默认不启用沉浸式（`rich_editor_pattern.cpp:15073-15076`） | AC-4.4, AC-4.5 |
| R-11 | 行为 | 调用 `enablePreviewText(true)` 且 IME 发送预上屏文本 | `SetSupportPreviewText(true)` → `SetPreviewText` → `InitPreviewText` 初始化 `PreviewTextRecord` 并插入预览文本 | `isTextPreviewSupported_` 类型 bool，默认 true（`rich_editor_pattern.h:1426`） | AC-5.1, AC-5.2 |
| R-12 | 行为 | IME 完成预上屏 | `FinishTextPreview` 删除预览文本 → 以 `FINISH_PREVIEW` 操作类型重新插入最终内容 → `previewTextRecord_.Reset()` | 预上屏完成时先删除预览内容再插入最终文本（`rich_editor_pattern.cpp:6648-6664`） | AC-5.4 |
| R-13 | 边界 | 预上屏期间处于拖拽状态 | `CheckPreviewTextValidate` 返回 `ERROR_BAD_PARAMETERS`，拒绝预上屏操作 | 拖拽期间不允许预上屏（`rich_editor_pattern.cpp:6411-6418`） | AC-5.5 |
| R-14 | 行为 | IME 发起输入且已注册 `aboutToIMEInput` | `BeforeIMEInsertValue` 构造 `RichEditorInsertValue`（含 insertOffset/insertValue/previewText）→ `FireAboutToIMEInput` → 回调返回值决定是否接受 | 返回 true 接受，false 拒绝（`rich_editor_event_hub.cpp:45-52`） | AC-6.1, AC-6.2, AC-6.3 |
| R-15 | 边界 | 未注册 `aboutToIMEInput` 或回调返回非布尔值 | `FireAboutToIMEInput` 返回 true（默认允许）；Bridge 层非布尔返回值默认 true | 默认允许所有输入（`rich_editor_event_hub.cpp:47-48`, `arkts_native_rich_editor_bridge.cpp:2005-2008`） | AC-6.5, AC-6.6 |
| R-16 | 行为 | IME 输入完成且已注册 `onDidIMEInput` | `AfterIMEInsertValue` 构造 `TextRange{caret, caret+length}` → `FireOnDidIMEInput` → 回调接收 TextRange 对象 | `onDidIMEInput_` 类型 `std::function<void(TextRange&)>`（`rich_editor_event_hub.h:108`） | AC-7.1, AC-7.2 |
| R-17 | 边界 | 未注册 `onDidIMEInput` | `FireOnDidIMEInput` 检查回调为空直接返回 | 无副作用（`rich_editor_event_hub.cpp:70-73`） | AC-7.3 |
| R-18 | 行为 | IME 输入完成且已注册 `onIMEInputComplete` | `AfterIMEInsertValue` 构造 `RichEditorAbstractSpanResult`（含 spanIndex/spanRange/value/fontColor 等）→ `FireOnIMEInputComplete` | 结果对象含完整 Span 样式信息（`rich_editor_pattern.cpp:7161-7194`） | AC-8.1, AC-8.3 |
| R-19 | 边界 | 预上屏状态下的 `onIMEInputComplete` | `RichEditorAbstractSpanResult.value` 设为 `previewTextRecord_.newPreviewContent` 而非 `spanItem->content` | 预上屏时结果对象携带预览内容而非最终内容（`rich_editor_pattern.cpp:7165-7168`） | AC-8.2 |
| R-20 | 行为 | 组件获得焦点准备绑定 IME 且已注册 `onWillAttachIME` | `BeforeAttachInputMethod` → `GetIMEClientInfo` 构造 `IMEClient{nodeId}` → `FireOnWillAttachIME` → 回调可修改 `IMEClient.extraInfo` | `IMEClient` 含 `nodeId` 和 `extraInfo`（`text_field_event_hub.h:90-93`） | AC-9.1, AC-9.2 |
| R-21 | 边界 | 未注册 `onWillAttachIME` | `FireOnWillAttachIME` 检查回调为空直接返回，IME 正常绑定 | `onWillAttachIME_` 类型 `IMEAttachCallback`（`rich_editor_event_hub.h:120`） | AC-9.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.8（自定义键盘） | 代码审查 | ComponentContentBase/CustomBuilder 双路径、`customKeyboardNode_`/`customKeyboardBuilder_` 存储、`RequestCustomKeyboard`/`CloseCustomKeyboard` 生命周期 |
| VM-2 | AC-2.1~2.4（聚焦拉起键盘） | 代码审查 | `needToRequestKeyboardOnFocus_` 存储、默认 true、reset 路径 |
| VM-3 | AC-3.1~3.7（回车键类型） | 代码审查 | EnterKeyType → TextInputAction 映射、`action_` 存储、`PerformAction` 行为分支、范围校验 |
| VM-4 | AC-4.1~4.5（键盘外观） | 代码审查 | `keyboardAppearance_`/`imeGradientMode_`/`imeFluidLightMode_` 存储、`BeforeAttachInputMethod` 传递路径 |
| VM-5 | AC-5.1~5.7（预上屏开关） | 代码审查 | `isTextPreviewSupported_` 存储、`PreviewTextRecord` 生命周期、`SetPreviewText`/`FinishTextPreview` 流程 |
| VM-6 | AC-6.1~6.7（IME 输入前拦截） | 代码审查 | `RichEditorInsertValue` 构造、`FireAboutToIMEInput` 返回值拦截、预上屏内容路径 |
| VM-7 | AC-7.1~7.5（IME 输入完成后） | 代码审查 | `TextRange` 构造、`FireOnDidIMEInput` 触发时序、Bridge 序列化 |
| VM-8 | AC-8.1~8.5（IME 输入完成） | 代码审查 | `RichEditorAbstractSpanResult` 构造、Span 样式信息填充、预上屏差异 |
| VM-9 | AC-9.1~9.6（IME 绑定前回调） | 代码审查 | `IMEClient` 构造、`FireOnWillAttachIME` 触发时序、`extraInfo` 传递路径 |

## API 变更分析

> 本特性为存量规格补录，记录各 API 的引入版本和当前签名。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `customKeyboard(value: CustomBuilder \| ComponentContentBase \| undefined, options?: KeyboardOptions)` | Public (@since 10) | `CustomBuilder` 或 `ComponentContentBase` 构建器，`KeyboardOptions` 可选避让配置 | `this` | N/A | 设置自定义键盘 | AC-1.1~1.8 |
| `enableKeyboardOnFocus(value: boolean \| undefined)` | Public (@since 10) | `boolean` 开关或 `undefined` | `this` | N/A | 设置聚焦时是否自动拉起键盘 | AC-2.1~2.4 |
| `enterKeyType(value: EnterKeyType \| undefined)` | Public (@since 12) | `EnterKeyType` 枚举或 `undefined` | `this` | N/A | 设置回车键类型 | AC-3.1~3.7 |
| `keyboardAppearance(value: KeyboardAppearance \| undefined)` | Public (@since 15) | `KeyboardAppearance` 枚举或 `undefined` | `this` | N/A | 设置键盘外观 | AC-4.1~4.5 |
| `enablePreviewText(value: boolean \| undefined)` | Public (@since 12) | `boolean` 开关或 `undefined` | `this` | N/A | 设置预上屏开关 | AC-5.1~5.7 |
| `aboutToIMEInput(callback: Callback<RichEditorInsertValue, boolean> \| undefined)` | Public (@since 10) | 回调函数，入参 `RichEditorInsertValue`，返回 `boolean` | `this` | N/A | IME 输入前拦截回调 | AC-6.1~6.7 |
| `onDidIMEInput(callback: Callback<TextRange, void> \| undefined)` | Public (@since 12) | 回调函数，入参 `TextRange` | `this` | N/A | IME 输入完成后回调 | AC-7.1~7.5 |
| `onIMEInputComplete(callback: Callback<RichEditorTextSpanResult, void> \| undefined)` | Public (@since 10) | 回调函数，入参 `RichEditorTextSpanResult` | `this` | N/A | IME 输入完成回调 | AC-8.1~8.5 |
| `onWillAttachIME(callback: Callback<IMEClient, void> \| undefined)` | Public (@since 22) | 回调函数，入参 `IMEClient` | `this` | N/A | IME 绑定前回调 | AC-9.1~9.6 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**customKeyboard**

| 属性 | 值 |
|------|-----|
| 函数签名 | `customKeyboard(value: CustomBuilder \| ComponentContentBase \| undefined, options?: KeyboardOptions): this` |
| 返回值 | `this` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | CustomBuilder \| ComponentContentBase \| undefined | 否 | undefined | undefined 时重置为系统键盘；ComponentContentBase 从 `builderNode_.nodePtr_` 提取节点 |
| options | KeyboardOptions | 否 | supportAvoidance=false | 含 `supportAvoidance` 布尔字段控制避让行为 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 ComponentContentBase | 提取 builderNode 节点，存入 `customKeyboardNode_` | AC-1.1 |
| 2 | 传入 CustomBuilder（JsView） | 解析 builder 函数，存入 `customKeyboardBuilder_` | AC-1.2 |
| 3 | 组件获得焦点 | `RequestKeyboard` 走自定义键盘分支 | AC-1.3 |
| 4 | options.supportAvoidance 为 true | `keyboardAvoidance_` 设为 true，启用避让 | AC-1.5 |

**enableKeyboardOnFocus**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableKeyboardOnFocus(value: boolean \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean \| undefined | 否 | true | 控制聚焦时是否自动拉起键盘 |

**enterKeyType**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enterKeyType(value: EnterKeyType \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | EnterKeyType \| undefined | 否 | `TextInputAction::NEW_LINE` | 映射为 TextInputAction 枚举；UNSPECIFIED 映射为 NEW_LINE |

**keyboardAppearance**

| 属性 | 值 |
|------|-----|
| 函数签名 | `keyboardAppearance(value: KeyboardAppearance \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | KeyboardAppearance \| undefined | 否 | `NONE_IMMERSIVE` | 枚举值：NONE_IMMERSIVE=0, IMMERSIVE=1, LIGHT_IMMERSIVE=2, DARK_IMMERSIVE=3 |

**enablePreviewText**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enablePreviewText(value: boolean \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1~5.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean \| undefined | 否 | true | 控制预上屏（IME 组词阶段预览文本）功能 |

**aboutToIMEInput**

| 属性 | 值 |
|------|-----|
| 函数签名 | `aboutToIMEInput(callback: Callback<RichEditorInsertValue, boolean> \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1~6.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback<RichEditorInsertValue, boolean> \| undefined | 否 | undefined | 回调入参含 insertOffset/insertValue/previewText；返回 true 接受输入，false 拒绝 |

**onDidIMEInput**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onDidIMEInput(callback: Callback<TextRange, void> \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-7.1~7.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback<TextRange, void> \| undefined | 否 | undefined | 回调入参含 start/end 标识变更文本范围 |

**onIMEInputComplete**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onIMEInputComplete(callback: Callback<RichEditorTextSpanResult, void> \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-8.1~8.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback<RichEditorTextSpanResult, void> \| undefined | 否 | undefined | 回调入参含 spanIndex/spanRange/value/fontColor/fontSize 等完整 Span 信息 |

**onWillAttachIME**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onWillAttachIME(callback: Callback<IMEClient, void> \| undefined): this` |
| 返回值 | `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-9.1~9.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback<IMEClient, void> \| undefined | 否 | undefined | 回调入参含 nodeId 和 extraInfo；API 22+ 引入 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — `customKeyboard`/`enableKeyboardOnFocus`/`aboutToIMEInput`/`onIMEInputComplete` 自 API 10+ 引入；`enterKeyType`/`enablePreviewText`/`onDidIMEInput` 自 API 12+ 引入；`keyboardAppearance` 自 API 15+ 引入；`onWillAttachIME` 自 API 22+ 引入
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（customKeyboard/enableKeyboardOnFocus/aboutToIMEInput/onIMEInputComplete），API 12（enterKeyType/enablePreviewText/onDidIMEInput），API 15（keyboardAppearance），API 22（onWillAttachIME）
- **API 版本号策略:** 各属性和事件按引入版本标注 `@since`；属性与事件自然配对（属性配置键盘行为，事件监控 IME 交互）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 自定义键盘完全替代系统键盘 | `customKeyboard` 设置后，`RequestKeyboard` 走 `RequestCustomKeyboard` 分支，不调用 `EnableStandardInput` | AC-1.3, AC-1.4 |
| 自定义键盘切换需先关闭再绑定 | `SetCustomKeyboardWithNode` 在编辑状态下先 `CloseCustomKeyboard` 再 `RequestKeyboard`，避免键盘叠加 | AC-1.7 |
| enterKeyType 的 UNSPECIFIED 回退 | `EnterKeyType.UNSPECIFIED` 映射为 `TextInputAction::NEW_LINE`，RichEditor 默认行为为换行 | AC-3.2, AC-3.7 |
| keyboardAppearance 在 IME 绑定前传递 | `BeforeAttachInputMethod` 将 `keyboardAppearance_`/`imeGradientMode_`/`imeFluidLightMode_` 传递给输入法框架，仅在 IME 绑定时生效 | AC-4.2, AC-4.3 |
| enablePreviewText 受 Pipeline 全局配置影响 | 组件初始化时从 `pipelineContext->GetSupportPreviewText()` 获取初始值，`enablePreviewText` 可覆盖 | AC-5.7 |
| aboutToIMEInput 是唯一可拦截输入的事件 | 回调返回 false 拒绝输入，返回 true 接受；未注册时默认 true | AC-6.2, AC-6.3, AC-6.5 |
| onIMEInputComplete 和 onDidIMEInput 在同一流程中依次触发 | `AfterIMEInsertValue` 先 `FireOnIMEInputComplete`（含完整 Span 信息），后 `FireOnDidIMEInput`（含 TextRange） | AC-7.5 |
| onWillAttachIME 触发时机最早 | 在 `BeforeAttachInputMethod` 中触发，先于 IME 绑定和任何输入事件 | AC-9.1 |
| 预上屏期间 IME 事件携带预览内容 | `aboutToIMEInput` 和 `onIMEInputComplete` 在预上屏状态下将 `previewText` 而非 `insertValue`/`spanItem->content` 填入事件对象 | AC-6.4, AC-8.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可测试性 | 所有属性和事件支持 Get/Fire 方法用于回读和触发验证 | 代码审查 | `rich_editor_model_ng.cpp:808-814, 1170-1175`, `rich_editor_event_hub.cpp:45-74, 326-336` |
| 可靠性 | 自定义键盘切换时先关闭再绑定，避免键盘叠加 | 代码审查 | `rich_editor_pattern.cpp:6294-6317` |
| 可靠性 | 预上屏期间拖拽状态拒绝预上屏操作，返回错误码 | 代码审查 | `rich_editor_pattern.cpp:6411-6418` |
| 安全性 | `aboutToIMEInput` 回调可拦截输入，防止非法内容注入 | 代码审查 | `rich_editor_pattern.cpp:7123-7135`, `rich_editor_event_hub.cpp:45-52` |
| 性能 | IME 事件回调避免在主线程执行耗时操作，Bridge 使用 `PipelineContext::SetCallBackNode` 确保线程安全 | 代码审查 | `arkts_native_rich_editor_bridge.cpp:1994, 2835, 882` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 自定义键盘和系统键盘均支持 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 自定义键盘避让行为受 `keyboardAvoidance_` 控制 | 折叠屏展开/折叠时键盘避让区域变化 | 代码审查 | `rich_editor_pattern.cpp:6360-6364` |
| 智慧屏 | 系统键盘通过 `EnableStandardInput` 绑定，自定义键盘通过 OverlayManager 绑定 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | `enableKeyboardOnFocus` 影响无障碍用户的焦点键盘弹出行为；`aboutToIMEInput` 可用于输入内容无障碍校验 | AC-2.1~2.4, AC-6.1~6.7 |
| 大字体 | N/A | 键盘配置属性不涉及大字体适配 | — |
| 深色模式 | 是 | `keyboardAppearance` 的 `LIGHT_IMMERSIVE`/`DARK_IMMERSIVE` 与深色模式相关 | AC-4.1~4.5 |
| 多窗口/分屏 | 是 | 自定义键盘通过 OverlayManager 绑定，受窗口模式影响；`BeforeAttachInputMethod` 获取 `systemWindowId` 用于 IME 绑定 | AC-1.4, AC-9.1 |
| 多用户 | N/A | — | — |
| 版本升级 | 是 | 各 API 跨 API 10-22+ 引入，`onWillAttachIME` 为最新（API 22+） | AC-1.1~9.6 |
| 生态兼容 | 是 | `customKeyboard` 支持第三方输入面板；`onWillAttachIME` 允许第三方 IME 配置 | AC-1.1~1.8, AC-9.1~9.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RichEditor 键盘与输入法交互
  作为应用开发者
  我想要配置 RichEditor 的键盘行为并监控 IME 交互
  以便实现自定义输入面板和输入内容控制

  Scenario: 设置自定义键盘
    Given RichEditor 组件已创建
    When 调用 customKeyboard(myBuilder, { supportAvoidance: true })
    Then customKeyboardNode_ 或 customKeyboardBuilder_ 被设置
    And keyboardAvoidance_ 设为 true
    When 组件获得焦点
    Then RequestKeyboard 走 RequestCustomKeyboard 分支
    And 系统键盘被关闭，自定义键盘被绑定

  Scenario: 聚焦拉起键盘开关
    Given RichEditor 组件 enableKeyboardOnFocus 默认为 true
    When 组件获得焦点
    Then 自动拉起键盘
    When 调用 enableKeyboardOnFocus(false)
    And 组件获得焦点
    Then 不自动拉起键盘

  Scenario: 回车键类型配置
    Given RichEditor 组件 action_ 默认为 NEW_LINE
    When 调用 enterKeyType(EnterKeyType.SEARCH)
    Then action_ 更新为 TextInputAction::SEARCH
    When IME 配置变更
    Then config.SetEnterKeyType 传递 SEARCH 给输入法框架
    When 回车键按下且 action_ 为 NEW_LINE
    Then 插入换行符，不退出编辑
    When 回车键按下且 action_ 非 NEW_LINE
    Then 触发 FireOnSubmit 回调

  Scenario: 键盘外观配置
    Given RichEditor 组件 keyboardAppearance_ 默认为 NONE_IMMERSIVE
    When 调用 keyboardAppearance(KeyboardAppearance.IMMERSIVE)
    Then keyboardAppearance_ 设为 IMMERSIVE
    When 组件获得焦点准备绑定 IME
    Then BeforeAttachInputMethod 将 IMMERSIVE 传递给 textConfig

  Scenario: 预上屏控制
    Given RichEditor 组件 isTextPreviewSupported_ 默认为 true
    When IME 发送预上屏文本
    Then SetPreviewText 初始化 PreviewTextRecord
    And 以 OperationType::IME 插入预览文本
    When IME 确认预上屏输入
    Then FinishTextPreview 删除预览文本
    And 以 OperationType::FINISH_PREVIEW 重新插入最终内容

  Scenario: IME 输入前拦截
    Given 已注册 aboutToIMEInput 回调
    When IME 发起输入
    Then BeforeIMEInsertValue 构造 RichEditorInsertValue
    And FireAboutToIMEInput 触发回调
    When 回调返回 false
    Then 输入被拒绝，文本不插入
    When 回调返回 true
    Then 输入被接受，继续插入流程

  Scenario: IME 输入完成事件
    Given 已注册 onIMEInputComplete 和 onDidIMEInput 回调
    When IME 输入完成
    Then AfterIMEInsertValue 构造 RichEditorAbstractSpanResult
    And FireOnIMEInputComplete 先触发（含完整 Span 信息）
    And FireOnDidIMEInput 后触发（含 TextRange）

  Scenario: IME 绑定前回调
    Given 已注册 onWillAttachIME 回调（API 22+）
    When 组件获得焦点准备绑定 IME
    Then BeforeAttachInputMethod 调用 GetIMEClientInfo 构造 IMEClient
    And FireOnWillAttachIME 触发回调
    When 回调设置 IMEClient.extraInfo
    Then extraInfo 传递给 textConfig.inputAttribute.extraConfig
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（键盘配置属性与 IME 交互事件，不含文本内容逻辑、布局算法、选择句柄、剪贴板）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern customKeyboardNode_ customKeyboardBuilder_ RequestCustomKeyboard CloseCustomKeyboard lifecycle"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern needToRequestKeyboardOnFocus_ SetRequestKeyboardOnFocus enableKeyboardOnFocus"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern action_ enterKeyType PerformAction TextInputAction SetEnterKeyType OnConfigurationChange"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern keyboardAppearance_ imeGradientMode_ imeFluidLightMode_ BeforeAttachInputMethod SetKeyboardAppearance"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern isTextPreviewSupported_ PreviewTextRecord SetPreviewText InitPreviewText FinishTextPreview enablePreviewText"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern BeforeIMEInsertValue AfterIMEInsertValue FireAboutToIMEInput FireOnIMEInputComplete FireOnDidIMEInput"
  - repo: "openharmony/ace_engine"
    query: "RichEditorPattern GetIMEClientInfo FireOnWillAttachIME BeforeAttachInputMethod IMEClient extraInfo"
  - repo: "openharmony/ace_engine"
    query: "RichEditorBridge SetCustomKeyboard SetEnableKeyboardOnFocus SetEnterKeyType SetKeyboardAppearance SetEnablePreviewText"
  - repo: "openharmony/ace_engine"
    query: "RichEditorBridge SetAboutToIMEInput SetOnIMEInputComplete SetOnDidIMEInput SetOnWillAttachIME"
```

**关键文档：**
- SDK 静态版声明: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/generated/component/richEditor.ets`
- Pattern 成员变量: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.h`
- Pattern IME 实现: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.cpp`
- Event Hub: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_event_hub.h`
- ModelNG: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_model_ng.cpp`
- Bridge 层: `frameworks/core/components_ng/pattern/rich_editor/bridge/arkts_native_rich_editor_bridge.cpp`
- 值类型: `frameworks/core/components_ng/pattern/rich_editor/rich_editor_value.h`
- IMEClient 定义: `frameworks/core/components_ng/pattern/text_field/text_field_event_hub.h`
- 键盘外观枚举: `frameworks/core/components/common/layout/constants.h`
- 键盘配置类型: `frameworks/core/components_ng/pattern/text_field/text_keyboard_common_type.h`
- TextInputAction 枚举: `frameworks/core/common/ime/text_input_action.h`
