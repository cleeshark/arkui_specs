# 特性规格

> Func-05-09-05-Feat-04 键盘与输入法交互：固化 enterKeyType/onSubmit、enableKeyboardOnFocus、customKeyboard/keyboardAppearance、autoCapitalizationMode、onWillAttachIME、enablePreviewText、enableHapticFeedback、enableAutoFill/contentType、stopBackPress、voiceButton、type/TextAreaType、maxLength/inputFilter/showCounter 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 键盘与输入法交互 (Keyboard & IME Interaction) |
| 特性编号 | Func-05-09-05-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 @since 7（onPaste/onChange）、@since 10（enableKeyboardOnFocus/customKeyboard/maxLength/showCounter/style/selectionMenuHidden/maxLines/setTextSelection/stopEditing/onTextSelectionChange/onContentScroll/onEditChange）、@since 11（enterKeyType/onSubmit/type/TextAreaType）、@since 12（enableAutoFill/contentType/fontFeature/onWillInsert/onDidInsert/onWillDelete/onDidDelete/editMenuOptions/enablePreviewText）、@since 13（enableHapticFeedback）、@since 15（stopBackPress/onWillChange/keyboardAppearance）、@since 20（autoCapitalizationMode）、@since 22（scrollBarColor/enableSelectedDataDetector/onWillAttachIME）、@since 23（voiceButton）；静态 @since 23 static |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | enterKeyType/onSubmit | TextArea 默认 NEW_LINE；onSubmit 不触发于 NEW_LINE |
| ADDED | enableKeyboardOnFocus | showKeyBoardOnFocus_ 主开关 |
| ADDED | customKeyboard/keyboardAppearance | 自定义键盘 builder/node + overlay 呈现 + supportAvoidance |
| ADDED | autoCapitalizationMode | NONE/WORDS/SENTENCES/ALL_CHARACTERS 传 IME |
| ADDED | onWillAttachIME | IME attach 前回调，可注入 extraConfig |
| ADDED | enablePreviewText | 控制预览文本模式；IME 决定是否发送 |
| ADDED | enableHapticFeedback | 长按/手柄拖动振动 |
| ADDED | enableAutoFill/contentType | 系统自动填充；contentType 决定填充类型 |
| ADDED | stopBackPress | 控制返回键消费 |
| ADDED | voiceButton | 系统API；语音输入按钮 |
| ADDED | type/TextAreaType | 输入类型决定键盘模式 |
| ADDED | maxLength/inputFilter/showCounter | 长度限制+正则过滤+计数器+超限抖动 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/05-text-area/design.md` | Baselined |

---

## 用户故事

### US-1: 设置回车键类型与提交回调

**作为** 应用开发者,
**我想要** 通过 enterKeyType 控制回车键类型并接收提交回调,
**以便** 适配不同场景的输入提交交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.enterKeyType(EnterKeyType.Go)` THEN 传 IME inputAttribute.enterKeyType；TextArea 默认 NEW_LINE（`text_field_model_ng.cpp:435`） | 正常 |
| AC-1.2 | WHEN TextArea + action==NEW_LINE + !textAreaBlurOnSubmit THEN 插入换行符（除非 inputFilter 拒绝）（`text_field_pattern.cpp:7313`） | 正常 |
| AC-1.3 | WHEN action 非 NEW_LINE THEN 调用 FireSubmitAction：触发 onSubmit 回调 + 若 textInputBlurOnSubmit_ 则关键盘（`text_field_pattern.cpp:7343-7376`） | 正常 |
| AC-1.4 | WHEN enterKeyType=NEW_LINE THEN onSubmit 不触发（SDK NOTE） | 边界 |

### US-2: 控制聚焦时是否请求键盘

**作为** 应用开发者,
**我想要** 通过 enableKeyboardOnFocus 控制聚焦时是否自动弹出键盘,
**以便** 灵活管理键盘显示时机。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.enableKeyboardOnFocus(true)` THEN 设 showKeyBoardOnFocus_=true（`text_field_model_ng.cpp:2756`） | 正常 |
| AC-2.2 | WHEN enableKeyboardOnFocus=false THEN RequestKeyboard 在 `!showKeyBoardOnFocus_` 时 return false（不弹键盘）（`text_field_pattern.cpp:5914`） | 正常 |
| AC-2.3 | WHEN 聚焦时切换 showKeyBoardOnFocus_ THEN 若变 true 请求键盘，变 false 关键盘（RequestKeyboardReason::SHOW_KEYBOARD_ON_FOCUS）（`text_field_pattern.cpp:11697-11715`） | 正常 |

### US-3: 使用自定义键盘

**作为** 应用开发者,
**我想要** 通过 customKeyboard 绑定自定义键盘构建器,
**以便** 替换系统默认键盘实现定制输入界面。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.customKeyboard(builder, { supportAvoidance: true })` THEN 设 customKeyboardBuilder_ + keyboardAvoidance_（`text_field_model_ng.cpp:981`） | 正常 |
| AC-3.2 | WHEN 聚焦且有自定义键盘 THEN RequestCustomKeyboard：关闭系统 IME → overlay BindKeyboard → isCustomKeyboardAttached_=true → AvoidCustomKeyboard（`text_field_pattern.cpp:6215-6272`） | 正常 |
| AC-3.3 | WHEN customKeyboard 传 undefined THEN 重置为默认系统键盘：关闭自定义键盘 → 请求系统键盘（`text_field_pattern.cpp:13253-13279`） | 正常 |
| AC-3.4 | WHEN 另一节点获焦且前节点有自定义键盘 THEN ProcessCustomKeyboard：!matched 关闭，nodeId 不同则 reset isCustomKeyboardAttached_（`text_field_pattern.cpp:2079`） | 正常 |
| AC-3.5 | WHEN stopEditing 调用且自定义键盘已 attach THEN CloseKeyboard 路由到 CloseCustomKeyboard（`text_field_pattern.cpp:6175`） | 正常 |
| AC-3.6 | WHEN 自定义键盘已设置 THEN 不支持相机输入（SDK NOTE） | 边界 |
| AC-3.7 | WHEN 自定义键盘已设置 + stopBackPress=false THEN 警告日志：返回可能无法关闭自定义键盘（`text_field_pattern.cpp:2214-2217`） | 边界 |

### US-4: 设置键盘外观与大写模式

**作为** 应用开发者,
**我想要** 通过 keyboardAppearance/autoCapitalizationMode 控制键盘外观与大写策略,
**以便** 适配不同输入场景的键盘样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.keyboardAppearance(IMMERSIVE)` THEN 设 keyboardAppearance_，传 IME immersiveMode（`text_field_pattern.cpp:6097`） | 正常 |
| AC-4.2 | WHEN 调用 `.autoCapitalizationMode(WORDS)` (@since 20) THEN 设 AutoCapitalizationMode，传 IME capitalizeMode（`text_field_pattern.cpp:6100`） | 正常 |
| AC-4.3 | WHEN 未设置 autoCapitalizationMode THEN 默认 NONE | 异常 |

### US-5: IME attach 前回调

**作为** 应用开发者,
**我想要** 通过 onWillAttachIME 在 IME 挂载前执行自定义逻辑,
**以便** 在键盘弹出前注入额外配置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.onWillAttachIME(callback)` (@since 22/24) THEN 注册 IMEAttachCallback（`text_field_model_ng.cpp:3278`） | 正常 |
| AC-5.2 | WHEN IME attach 前 THEN FireOnWillAttachIME：构建 IMEClient{nodeId} 调用回调；回调可填充 extraInfo→ 注入 textConfig.inputAttribute.extraConfig（`text_field_pattern.cpp:5936-5941`） | 正常 |
| AC-5.3 | WHEN callback 传 undefined THEN 移除已注册回调 | 边界 |

### US-6: 预览文本模式

**作为** 应用开发者,
**我想要** 通过 enablePreviewText 启用预览文本模式,
**以便** IME 可实时预览输入效果而不立即提交。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.enablePreviewText(true)` THEN 设 hasSupportedPreviewText_=true，传 IME isTextPreviewSupported=true（`text_field_pattern.cpp:6096`） | 正常 |
| AC-6.2 | WHEN IME 发送预览文本 THEN SetPreviewText 入队 → SetPreviewTextOperation：ReplaceSelectedValue + UpdatePreviewIndex + hasPreviewText_=true（`text_field_pattern.cpp:11417-11479`） | 正常 |
| AC-6.3 | WHEN 预览结束 THEN FinishTextPreviewOperation：替换预览为提交值 + hasPreviewText_=false + reset previewStart/End（`text_field_pattern.cpp:11490-11548`） | 正常 |
| AC-6.4 | WHEN enablePreviewText=false THEN IME 不发送预览文本；hasSupportedPreviewText_=false | 边界 |
| AC-6.5 | WHEN 预览文本中 THEN 不触发 onWillInsert/onDidInsert/onWillDelete/onDidDelete（SDK NOTE） | 边界 |

### US-7: 触感反馈

**作为** 应用开发者,
**我想要** 通过 enableHapticFeedback 控制长按与拖动时的振动反馈,
**以便** 提升交互触感体验。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.enableHapticFeedback(true)` THEN 设 isEnableHapticFeedback_=true（默认 true）（`text_field_model_ng.cpp:2658`） | 正常 |
| AC-7.2 | WHEN 长按文本 THEN StartVibratorByLongPress：isEnableHapticFeedback_ 为 true 时调 VibratorUtils "longPress.light"（`text_field_pattern.cpp:4982-4986`） | 正常 |
| AC-7.3 | WHEN 手柄拖动索引变化 THEN StartVibratorByIndexChange：isEnableHapticFeedback_ 为 true 且索引变化时调 "slide"（`text_field_pattern.cpp:2944-2948`） | 正常 |
| AC-7.4 | WHEN enableHapticFeedback=false THEN 长按/拖动无振动 | 边界 |
| AC-7.5 | WHEN 需振动 THEN 需声明 ohos.permission.VIBRATE 权限（SDK NOTE） | 边界 |

### US-8: 自动填充

**作为** 应用开发者,
**我想要** 通过 enableAutoFill/contentType 启用自动填充,
**以便** 系统密码管理器自动填充表单内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.enableAutoFill(true)` THEN 设 EnableAutoFill=true（默认 true）（`text_field_model_ng.cpp:1008`） | 正常 |
| AC-8.2 | WHEN 调用 `.contentType(ContentType.UserPassword)` THEN 设 TextContentType + UpdateTextContentTypeChanged(true)（`text_field_model_ng.cpp:405`） | 正常 |
| AC-8.3 | WHEN enableAutoFill=false THEN CheckAutoFill 返回 false，不触发填充（`text_field_pattern.cpp:3877`） | 正常 |
| AC-8.4 | WHEN 聚焦 + enableAutoFill + password 类型 + API>=18 THEN ProcessAutoFillOnFocus 触发 DoProcessAutoFill(FIELD_FOCUS_EVENT)（`text_field_pattern.cpp:1606-1622`） | 正常 |
| AC-8.5 | WHEN API<18 THEN ProcessAutoFillOnFocus 早退不触发（`text_field_pattern.cpp:1611`） | 边界 |

### US-9: 返回键控制

**作为** 应用开发者,
**我想要** 通过 stopBackPress 控制返回键是否关闭键盘,
**以便** 防止返回键意外退出编辑状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 `.stopBackPress(true)` THEN 设 StopBackPress=true（默认 true）（`text_field_model_ng.cpp:2996`） | 正常 |
| AC-9.2 | WHEN stopBackPress=true 且键盘/IME/自定义键盘已显示 THEN OnBackPressed 关闭键盘并返回 true（消费返回）（`text_field_pattern.cpp:8405-8437`） | 正常 |
| AC-9.3 | WHEN stopBackPress=false THEN OnBackPressed 关闭键盘但返回 false（不消费返回，事件传播）（`text_field_pattern.cpp:8436`） | 边界 |
| AC-9.4 | WHEN 选区覆盖层开启 THEN 先折叠选区；返回 IsStopBackPress() | 边界 |

### US-10: 语音按钮（系统API）

**作为** 系统应用开发者,
**我想要** 通过 voiceButton 配置语音输入按钮,
**以便** 在键盘区域提供语音输入入口。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `.voiceButton({ enabled: true })` (系统API) THEN 设 IsShowVoiceButton=true（`text_area_static_modifier.cpp:986-994`） | 正常 |
| AC-10.2 | WHEN IsShowVoiceButtonMode()=true 需满足：IsShowVoiceButton + 非 INLINE + type=UNSPECIFIED/TEXT + 无自定义键盘（`text_field_pattern.cpp:10448-10456`） | 正常 |
| AC-10.3 | WHEN 按语音按钮 THEN HandleOnVoiceInput：请求 VOICE_NODE 焦点 + HandleOnTextMethodInput(VOICE_INPUT)（`text_field_pattern.cpp:2657-2667`） | 正常 |

### US-11: 输入类型

**作为** 应用开发者,
**我想要** 通过 type 设置 TextInputType,
**以便** 指定文本/数字/密码等输入模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN 调用 `.type(TextAreaType.Number)` THEN 设 TextInputType + UpdateTypeChanged(true) + SetIsFilterChanged(true)（`text_field_model_ng.cpp:371`） | 正常 |
| AC-11.2 | WHEN type 变化 THEN FilterInitializeText 重新按新类型过滤（`text_field_pattern.cpp:4828`） | 正常 |
| AC-11.3 | WHEN 未设置 type THEN 默认 TextAreaType.NORMAL（TextInputType::TEXT）（`text_area_dynamic_modifier.cpp:975-980`） | 异常 |
| AC-11.4 | WHEN type 设置 THEN 传 IME inputAttribute.inputPattern（`text_field_pattern.cpp:6094`） | 正常 |

### US-12: 长度限制、输入过滤与计数器

**作为** 应用开发者,
**我想要** 通过 maxLength/inputFilter/counter 配置长度限制、输入过滤与计数器,
**以便** 控制输入内容格式与长度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-12.1 | WHEN 调用 `.maxLength(100)` THEN 设 MaxLength；达到上限时不可再输入 + showCountBorderStyle_=true + 边框变红 + UltralimitShake（`text_field_pattern.cpp:6476-6528`，`text_field_pattern.cpp:4377-4417`） | 正常 |
| AC-12.2 | WHEN IME 输入超过 maxLength THEN UpdateEditingValue 截断到 maxLength（`text_field_pattern.cpp:7410-7428`） | 正常 |
| AC-12.3 | WHEN 未设置 maxLength THEN 默认无限（Infinity<uint32_t>） | 异常 |
| AC-12.4 | WHEN 调用 `.inputFilter(regex, onError)` THEN 设 InputFilter + 注册 onInputFilterError 回调（`text_field_model_ng.cpp:607-614`） | 正常 |
| AC-12.5 | WHEN 输入匹配正则 THEN 正常输入；不匹配字符被剥离并触发 onError 回调（`content_controller.cpp:314-411`） | 正常 |
| AC-12.6 | WHEN inputFilter 正则无效 THEN CheckRegexValid 失败，重置为空串（`arkts_native_text_area_bridge.cpp:261-285`） | 异常 |
| AC-12.7 | WHEN 调用 `.showCounter(true, { thresholdPercentage: 80, highlightBorder: true })` THEN 设 ShowCounter + SetCounter(thresholdPercentage) + ShowHighlightBorder；计数器在输入数>limit*阈值%时显示（`text_field_model_ng.cpp:806-840`） | 正常 |
| AC-12.8 | WHEN showCounter=true + highlightBorder=true + 达到上限 THEN 边框变红 + 计数器变红 + 抖动（`text_field_pattern.cpp:4377-4417`） | 正常 |
| AC-12.9 | WHEN highlightBorder=false THEN 达到上限时边框不变红（SDK NOTE） | 边界 |
| AC-12.10 | WHEN INLINE 模式 THEN 计数器不显示（`text_component_decorator.cpp:336`） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | TASK-04 | XTS enterKeyType/onSubmit | text_field_pattern.cpp:7313 |
| AC-2.1~2.3 | R-5~R-7 | TASK-04 | XTS enableKeyboardOnFocus | text_field_pattern.cpp:5914 |
| AC-3.1~3.7 | R-8~R-14 | TASK-04 | XTS customKeyboard | text_field_pattern.cpp:6215 |
| AC-4.1~4.3 | R-15~R-17 | TASK-04 | XTS keyboardAppearance/autoCap | text_field_pattern.cpp:6097 |
| AC-5.1~5.3 | R-18~R-20 | TASK-04 | XTS onWillAttachIME | text_field_pattern.cpp:5936 |
| AC-6.1~6.5 | R-21~R-25 | TASK-04 | XTS enablePreviewText | text_field_pattern.cpp:11417 |
| AC-7.1~7.5 | R-26~R-30 | TASK-04 | XTS enableHapticFeedback | text_field_pattern.cpp:4982 |
| AC-8.1~8.5 | R-31~R-35 | TASK-04 | XTS enableAutoFill/contentType | text_field_pattern.cpp:3869 |
| AC-9.1~9.4 | R-36~R-39 | TASK-04 | XTS stopBackPress | text_field_pattern.cpp:8405 |
| AC-10.1~10.3 | R-40~R-42 | TASK-04 | 系统测试 voiceButton | text_field_pattern.cpp:10448 |
| AC-11.1~11.4 | R-43~R-46 | TASK-04 | XTS type/TextAreaType | text_field_model_ng.cpp:371 |
| AC-12.1~12.10 | R-47~R-56 | TASK-04 | XTS maxLength/inputFilter/showCounter | text_field_pattern.cpp:6476 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 enterKeyType | 传 IME；TextArea 默认 NEW_LINE | — | AC-1.1 |
| R-2 | 行为 | TextArea+NEW_LINE+!blurOnSubmit | 插入换行 | filter 可能拒绝 | AC-1.2 |
| R-3 | 行为 | action 非 NEW_LINE | FireSubmitAction+可能关键盘 | — | AC-1.3 |
| R-4 | 边界 | NEW_LINE | onSubmit 不触发 | SDK NOTE | AC-1.4 |
| R-5 | 行为 | 设置 enableKeyboardOnFocus=true | showKeyBoardOnFocus_=true | 默认 true | AC-2.1 |
| R-6 | 边界 | enableKeyboardOnFocus=false | RequestKeyboard return false | — | AC-2.2 |
| R-7 | 行为 | 聚焦时切换值 | true→请求键盘；false→关键盘 | — | AC-2.3 |
| R-8 | 行为 | 设置 customKeyboard(builder) | 设 customKeyboardBuilder_+keyboardAvoidance_ | — | AC-3.1 |
| R-9 | 行为 | 聚焦+有自定义键盘 | RequestCustomKeyboard：关系统IME→BindKeyboard→attach→avoid | — | AC-3.2 |
| R-10 | 行为 | customKeyboard=undefined | 关自定义→请求系统 | — | AC-3.3 |
| R-11 | 行为 | 另一节点获焦 | ProcessCustomKeyboard 跨主机关闭 | — | AC-3.4 |
| R-12 | 行为 | stopEditing+自定义键盘已attach | CloseCustomKeyboard | — | AC-3.5 |
| R-13 | 边界 | 自定义键盘+相机输入 | 不支持相机输入 | SDK NOTE | AC-3.6 |
| R-14 | 边界 | 自定义键盘+stopBackPress=false | 警告日志 | — | AC-3.7 |
| R-15 | 行为 | 设置 keyboardAppearance | 传 IME immersiveMode | 默认 NONE_IMMERSIVE | AC-4.1 |
| R-16 | 行为 | 设置 autoCapitalizationMode | 传 IME capitalizeMode | 默认 NONE @since 20 | AC-4.2,4.3 |
| R-18 | 行为 | 设置 onWillAttachIME | 注册 IMEAttachCallback | @since 22/24 | AC-5.1 |
| R-19 | 行为 | IME attach 前 | FireOnWillAttachIME→可注入 extraConfig | — | AC-5.2 |
| R-21 | 行为 | 设置 enablePreviewText=true | hasSupportedPreviewText_=true→IME isTextPreviewSupported | 默认 true | AC-6.1 |
| R-22 | 行为 | IME 发送预览 | SetPreviewTextOperation：replace+updateIndex | — | AC-6.2 |
| R-23 | 行为 | 预览结束 | FinishTextPreviewOperation：替换为提交值 | — | AC-6.3 |
| R-25 | 边界 | 预览中 | 不触发 onWillInsert/onDidInsert/onWillDelete/onDidDelete | SDK NOTE | AC-6.5 |
| R-26 | 行为 | 设置 enableHapticFeedback=true | isEnableHapticFeedback_=true | 默认 true | AC-7.1 |
| R-27 | 行为 | 长按 | StartVibratorByLongPress "longPress.light" | 需 VIBRATE 权限 | AC-7.2,7.5 |
| R-28 | 行为 | 手柄拖动索引变化 | StartVibratorByIndexChange "slide" | — | AC-7.3 |
| R-31 | 行为 | 设置 enableAutoFill=true | EnableAutoFill=true | 默认 true | AC-8.1 |
| R-32 | 行为 | 设置 contentType | TextContentType+TypeChanged | — | AC-8.2 |
| R-33 | 边界 | enableAutoFill=false | CheckAutoFill false | — | AC-8.3 |
| R-34 | 行为 | 聚焦+autoFill+password+API>=18 | ProcessAutoFillOnFocus | — | AC-8.4 |
| R-35 | 边界 | API<18 | ProcessAutoFillOnFocus 早退 | — | AC-8.5 |
| R-36 | 行为 | 设置 stopBackPress=true | StopBackPress=true | 默认 true | AC-9.1 |
| R-37 | 行为 | 返回键+键盘显示 | 关键盘+返回 true（消费） | stopBackPress=true | AC-9.2 |
| R-39 | 边界 | stopBackPress=false | 关键盘+返回 false（不消费） | 事件传播 | AC-9.3 |
| R-40 | 行为 | 设置 voiceButton(系统API) | IsShowVoiceButton=true | — | AC-10.1 |
| R-41 | 行为 | IsShowVoiceButtonMode | 需非INLINE+type=UNSPECIFIED/TEXT+无自定义键盘 | — | AC-10.2 |
| R-43 | 行为 | 设置 type | TextInputType+TypeChanged+IsFilterChanged | 默认 TEXT | AC-11.1,11.3 |
| R-44 | 行为 | type 变化 | FilterInitializeText 重新过滤 | — | AC-11.2 |
| R-47 | 行为 | 设置 maxLength | 达上限→不可输入+边框红+抖动 | 默认无限 | AC-12.1,12.3 |
| R-48 | 行为 | IME 超 maxLength | UpdateEditingValue 截断 | — | AC-12.2 |
| R-49 | 行为 | 设置 inputFilter(regex,onError) | 设 InputFilter+注册 error 回调 | — | AC-12.4 |
| R-50 | 行为 | 输入匹配正则 | 正常输入；不匹配剥离+onError | — | AC-12.5 |
| R-51 | 异常 | 正则无效 | CheckRegexValid 失败→重置空串 | — | AC-12.6 |
| R-52 | 行为 | 设置 showCounter(true,options) | ShowCounter+thresholdPercentage+ShowHighlightBorder | 需配合 maxLength | AC-12.7 |
| R-53 | 行为 | showCounter+highlightBorder+达上限 | 边框红+计数器红+抖动 | — | AC-12.8 |
| R-55 | 边界 | highlightBorder=false | 达上限边框不变红 | — | AC-12.9 |
| R-56 | 边界 | INLINE 模式 | 计数器不显示 | — | AC-12.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.x enterKeyType/onSubmit | XTS + IME | action 分发；NEW_LINE 换行 |
| VM-2 | AC-2.x enableKeyboardOnFocus | XTS + 焦点 | 聚焦弹键盘门控 |
| VM-3 | AC-3.x customKeyboard | XTS + overlay | 自定义键盘生命周期；跨主机关闭 |
| VM-4 | AC-4.x keyboardAppearance/autoCap | XTS + IME | immersiveMode/capitalizeMode 传 IME |
| VM-5 | AC-5.x onWillAttachIME | XTS + IME | extraConfig 注入 |
| VM-6 | AC-6.x enablePreviewText | XTS + IME | 预览文本生命周期；不触发 Will/Did |
| VM-7 | AC-7.x enableHapticFeedback | XTS + 振动 | 长按/拖动振动；权限 |
| VM-8 | AC-8.x enableAutoFill/contentType | XTS + autofill | 填充触发；API18 门控 |
| VM-9 | AC-9.x stopBackPress | XTS + 返回键 | 返回消费/传播 |
| VM-10 | AC-10.x voiceButton | 系统测试 | 语音按钮门控 |
| VM-11 | AC-11.x type/TextAreaType | XTS + IME | 类型变化过滤；键盘模式 |
| VM-12 | AC-12.x maxLength/inputFilter/showCounter | XTS + 计数器 | 超限抖动；正则过滤；计数器显示 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| enterKeyType(value) | Public | EnterKeyType | this | 无 | 回车键类型 | AC-1.x |
| onSubmit(callback) | Public | TextAreaSubmitCallback | this | 无 | 提交回调 | AC-1.3 |
| enableKeyboardOnFocus(value) | Public | boolean | this | 无 | 聚焦弹键盘 | AC-2.x |
| customKeyboard(value, options?) | Public | CustomBuilder/ComponentContent, KeyboardOptions? | this | 无 | 自定义键盘 | AC-3.x |
| keyboardAppearance(value) | Public | KeyboardAppearance | this | 无 | 键盘外观 | AC-4.1 |
| autoCapitalizationMode(mode) | Public | AutoCapitalizationMode | this | 无 | 大写模式 | AC-4.2 |
| onWillAttachIME(callback) | Public | Callback<IMEClient> | this | 无 | IME attach 前回调 | AC-5.x |
| enablePreviewText(enable) | Public | boolean | this | 无 | 预览文本 | AC-6.x |
| enableHapticFeedback(isEnabled) | Public | boolean | this | 无 | 触感反馈 | AC-7.x |
| enableAutoFill(value) | Public | boolean | this | 无 | 自动填充 | AC-8.x |
| contentType(contentType) | Public | ContentType | this | 无 | 填充类型 | AC-8.2 |
| stopBackPress(isStopped) | Public | boolean | this | 无 | 返回键控制 | AC-9.x |
| voiceButton(options) | System | VoiceButtonOptions | this | 无 | 语音按钮 | AC-10.x |
| type(value) | Public | TextAreaType | this | 无 | 输入类型 | AC-11.x |
| maxLength(value) | Public | number | this | 无 | 最大长度 | AC-12.1 |
| inputFilter(value, error?) | Public | ResourceStr, function? | this | 无 | 输入过滤 | AC-12.4 |
| showCounter(value, options?) | Public | boolean, InputCounterOptions? | this | 无 | 计数器 | AC-12.7 |

> **SDK 交叉验证：** 均经 `textArea.static.d.ets` 与 `text_area.d.ts` 核对。voiceButton 为 @systemapi。

## 接口规格

### 接口定义

| 接口 | 签名概要 | 开放范围 | 关联 AC |
|------|----------|----------|---------|
| 回车提交 | enterKeyType/onSubmit | Public | AC-1.x |
| 键盘控制 | enableKeyboardOnFocus/customKeyboard/keyboardAppearance/autoCapitalizationMode | Public | AC-2.x,3.x,4.x |
| IME 回调 | onWillAttachIME/enablePreviewText | Public | AC-5.x,6.x |
| 触感自动填充 | enableHapticFeedback/enableAutoFill/contentType/stopBackPress | Public | AC-7.x,8.x,9.x |
| 语音按钮 | voiceButton | System | AC-10.x |
| 输入类型 | type/TextAreaType | Public | AC-11.x |
| 长度过滤计数 | maxLength/inputFilter/showCounter | Public | AC-12.x |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enableKeyboardOnFocus | boolean | 是 | true | — |
| customKeyboard | CustomBuilder/ComponentContent/undefined | 是 | 无 | undefined 重置默认 |
| keyboardAppearance | KeyboardAppearance | 是 | NONE_IMMERSIVE | — |
| autoCapitalizationMode | AutoCapitalizationMode | 是 | NONE | @since 20 |
| enablePreviewText | boolean | 是 | true | — |
| enableHapticFeedback | boolean | 是 | true | 需 VIBRATE 权限 |
| enableAutoFill | boolean | 是 | true | — |
| stopBackPress | boolean | 是 | true | — |
| maxLength | number | 是 | 无限 | — |
| showCounter.thresholdPercentage | int | 否 | — | 计数器显示阈值 |
| showCounter.highlightBorder | boolean | 否 | true | false 则边框不变红 |

## 兼容性声明

- **已有 API 行为变更:** 是。ProcessAutoFillOnFocus 在 API<18 早退（API 18 门控）；enableAutoFill 默认 true。customKeyboard + stopBackPress=false 会产生警告。enablePreviewText 预览中不触发 onWillInsert/onDidInsert/onWillDelete/onDidDelete。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 @since 10/11/12/13/15/20/22/23；静态 @since 23 static
- **API 版本号策略:** 同前；voiceButton 为系统 API

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| showKeyBoardOnFocus_ 主开关 | RequestKeyboard 第一道门控 | AC-2.x |
| 自定义键盘 overlay 呈现 | 不压缩/抬升原屏（除非 avoidance 启用） | AC-3.x |
| 自定义键盘不获焦但阻断手势 | SDK NOTE | AC-3.x |
| IME attach 前回调注入 extraConfig | onWillAttachIME 可改 IME 配置 | AC-5.2 |
| 预览文本独立操作队列 | 绕过 ExecuteInsertValueCommand | AC-6.5 |
| isIMEOrAutoFill 门控 | onWillInsert/onDidInsert/onWillDelete/onDidDelete 仅系统输入法 | — |
| API18 autofill 门控 | ProcessAutoFillOnFocus 早退 | AC-8.5 |
| maxLength emoji 感知截断 | TextEmojiProcessor::SubU16string | AC-12.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | maxLength 超限抖动 InterpolatingSpring 单帧启动 | XTS 帧率 | text_field_pattern.cpp:6678 |
| 安全 | enableHapticFeedback 需 VIBRATE 权限 | 权限检查 | SDK NOTE |
| 可靠性 | stopEditing 幂等关闭自定义键盘 | 单测 | text_field_pattern.cpp:6175 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | enableAutoFill/contentType 影响无障碍填充提示 | AC-8.x |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 是 | customKeyboard overlay 跨窗口；多实例自定义键盘关闭 | AC-3.4 |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | autoCapitalizationMode @since 20；onWillAttachIME @since 22；ProcessAutoFillOnFocus API18 门控 | AC-4.2,5.1,8.5 |
| 生态兼容 | 是 | customKeyboard 阻断系统 IME；enablePreviewText 依赖系统输入法支持 | AC-3.x,6.x |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextArea 键盘与输入法交互
  作为 应用开发者
  我想要 控制键盘、IME、自动填充、触感、返回键、输入类型、长度过滤
  以便 精确管理文本输入会话

  Scenario: 自定义键盘生命周期
    Given 设置 .customKeyboard(builder, { supportAvoidance: true })
    When TextArea 获焦
    Then 关闭系统 IME
    And overlay BindKeyboard 呈现自定义键盘
    And isCustomKeyboardAttached_=true
    When 调用 controller.stopEditing()
    Then CloseCustomKeyboard 关闭自定义键盘

  Scenario Outline: maxLength 超限行为
    Given 设置 .maxLength(10) .showCounter(true, { highlightBorder: <highlight> })
    When 输入字符使总数 > 10
    Then 边框 <borderResult>
    And 计数器变红
    And UltralimitShake 抖动

    Examples:
      | highlight | borderResult |
      | true | 变红 |
      | false | 不变红 |

  Scenario: 预览文本不触发 Will/Did 回调
    Given 设置 .enablePreviewText(true) 且注册 onWillInsert/onDidInsert
    When IME 发送预览文本
    Then 预览文本替换选中区域
    And onWillInsert/onDidInsert 不触发
    When 预览结束提交
    Then onWillChange/onChange 触发
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
    query: "customKeyboard overlay 呈现与跨主机关闭机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "enablePreviewText 预览文本独立操作队列为何绕过 ExecuteInsertValueCommand"
  - repo: "openharmony/arkui_ace_engine"
    query: "maxLength 超限 emoji 感知截断与 UltralimitShake 实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "inputFilter 正则编译失败的处理与 error 回调触发"
  - repo: "openharmony/arkui_ace_engine"
    query: "onWillAttachIME 注入 extraConfig 到 IME attach 的流程"
```

**关键文档：** `specs/05-ui-components/09-text-components/05-text-area/design.md`（DESIGN-Func-05-09-05）；SDK `textArea.static.d.ets` / `text_area.d.ts`
