# 特性规格

> Func-05-09-03-Feat-05 键盘与输入控制：覆盖 enableKeyboardOnFocus/enterKeyType/autoCapitalizationMode/inputFilter/customKeyboard+KeyboardOptions/keyboardAppearance/type(SearchType)/maxLength/enablePreviewText/enableHapticFeedback/stopBackPress 共 11 个属性。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 键盘与输入控制（Keyboard & Input Control） |
| 特性编号 | Func-05-09-03-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10(enableKeyboardOnFocus/customKeyboard)、API 11(type/maxLength)、API 12(enterKeyType/inputFilter/enablePreviewText)、API 13(enableHapticFeedback)、API 15(keyboardAppearance/stopBackPress)、API 20(autoCapitalizationMode) |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 键盘弹出与回车键规格 | 补录：enableKeyboardOnFocus(@since 10)、enterKeyType(@since 12) |
| ADDED | 输入类型与最大长度规格 | 补录：type/SearchType(@since 11)、maxLength(@since 11) |
| ADDED | 输入过滤规格 | 补录：inputFilter(@since 12) |
| ADDED | 自定义键盘规格 | 补录：customKeyboard+KeyboardOptions(@since 10/options @since 12) |
| ADDED | 键盘外观与预览规格 | 补录：keyboardAppearance(@since 15)、enablePreviewText(@since 12)、autoCapitalizationMode(@since 20) |
| ADDED | 触感与返回键规格 | 补录：enableHapticFeedback(@since 13, 需 VIBRATE)、stopBackPress(@since 15) |

## 输入文档

- 设计文档：`design.md`（DESIGN-Func-05-09-03，Feat-05 增量合并）
- 源码定位：
  - 全部委托子 TextField：`search_model_ng.cpp` 各 setter 经 `frameNode->GetChildren().front()` 获取子文本框
  - 状态位置：4 个存于 TextFieldLayoutProperty（InputFilter/TextInputType+TypeChanged/MaxLength/StopBackPress），7 个存于 TextFieldPattern 运行时（needToRequestKeyboardOnFocus_/TextInputAction/AutoCapitalizationMode/customKeyboard_/KeyboardAppearance/supportPreviewText_/isEnableHapticFeedback_）
  - SearchType 重映射：`frameworks/core/common/ime/text_input_type.cpp:20-32` CastToTextInputType
  - haptic 权限：`adapter/ohos/entrance/vibrator/vibrator_utils.cpp:76-83` Sensors::StartVibrator
  - stopBackPress 返回值：`frameworks/core/components_ng/pattern/text_field/text_field_pattern.cpp:8405-8444` OnBackPressed→IsStopBackPress
  - SDK：`interface/sdk-js/api/@internal/component/ets/search.d.ts`

## 用户故事

### US-1: 键盘弹出与回车键

**作为** 应用开发者,
**我想要** 控制搜索框聚焦时是否弹出软键盘，以及回车键的类型,
**以便** 控制键盘弹出时机与提交行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 调用 `.enableKeyboardOnFocus(true)`（@since 10，默认 true） THEN 子 TextFieldPattern.needToRequestKeyboardOnFocus_=true，聚焦时弹出软键盘 | 正常 |
| AC-1.2 | WHEN 调用 `.enableKeyboardOnFocus(false)` THEN 聚焦时不弹出软键盘 | 正常 |
| AC-1.3 | WHEN 调用 `.enterKeyType(EnterKeyType.Go)`（@since 12） THEN 子 TextFieldPattern.TextInputAction=Go，传入 IME | 正常 |
| AC-1.4 | WHEN enterKeyType=UNSPECIFIED THEN 静默重映射为 SEARCH（默认） | 边界 |
| AC-1.5 | WHEN 未设 enterKeyType THEN 默认 EnterKeyType.Search | 正常 |

### US-2: 输入类型与最大长度

**作为** 应用开发者,
**我想要** 设置搜索框的输入类型与最大字符数,
**以便** 限制用户输入的内容格式与长度。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.type(SearchType.NUMBER)`（@since 11） THEN CastToTextInputType pass-through(2)，子 TextFieldLayoutProperty.TextInputType=NUMBER + TypeChanged=true + IsFilterChanged=true，触发 MEASURE | 正常 |
| AC-2.2 | WHEN 调用 `.type(SearchType.URL)` THEN SDK URL(13) 经 CastToTextInputType 重映射为内部 URL(6) | 边界 |
| AC-2.3 | WHEN 调用 `.type(SearchType.ONE_TIME_CODE)`（@since 20） THEN SDK(14) 重映射为内部 ONE_TIME_CODE(13) | 边界 |
| AC-2.4 | WHEN 未设 type THEN 默认 SearchType.NORMAL(=TextInputType.TEXT) | 正常 |
| AC-2.5 | WHEN 调用 `.maxLength(100)`（@since 11） THEN 子 TextFieldLayoutProperty.MaxLength=100，触发 MEASURE | 正常 |
| AC-2.6 | WHEN maxLength < 0 THEN 重置（无限制） | 边界 |
| AC-2.7 | WHEN 未设 maxLength THEN 无限制 | 正常 |

### US-3: 输入过滤

**作为** 应用开发者,
**我想要** 通过正则表达式过滤用户输入,
**以便** 按规则拦截或放行用户输入的字符。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.inputFilter("[0-9]", (e) => {})`（@since 12） THEN 子 TextFieldLayoutProperty.InputFilter 设正则 + TextFieldEventHub.SetOnInputFilterError 回调，触发 MEASURE | 正常 |
| AC-3.2 | WHEN inputFilter 已设 THEN type 属性的内置过滤不生效（inputFilter 覆盖 type 过滤） | 正常 |
| AC-3.3 | WHEN 输入字符不匹配正则 THEN 触发 error 回调返回被过滤内容 | 正常 |
| AC-3.4 | WHEN inputFilter 为空字符串 THEN 清除过滤 | 边界 |

### US-4: 自定义键盘

**作为** 应用开发者,
**我想要** 使用自定义组件替代系统输入法,
**以便** 使用自定义键盘界面替换系统输入法。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 调用 `.customKeyboard(builder, { supportAvoidance: true })`（@since 10/options @since 12） THEN 子 TextFieldPattern.customKeyboard_=builder + customKeyboardOption_.supportAvoidance=true | 正常 |
| AC-4.2 | WHEN supportAvoidance 未设 THEN 默认 false（页面不被避让提升） | 正常 |
| AC-4.3 | WHEN customKeyboard 传 undefined THEN 关闭自定义键盘，恢复系统输入法 | 正常 |
| AC-4.4 | WHEN 在 attributeModifier 中调用 customKeyboard THEN 不生效（SDK 注明不可在 attributeModifier 中调用） | 边界 |
| AC-4.5 | WHEN 自定义键盘激活且焦点丢失 THEN 默认关闭自定义键盘 | 正常 |

### US-5: 键盘外观、预览与自动大写

**作为** 应用开发者,
**我想要** 控制键盘外观、预览文本与自动大写模式,
**以便** 控制键盘视觉样式与输入预览行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 `.keyboardAppearance(KeyboardAppearance.LIGHT_IMMERSIVE)`（@since 15） THEN 子 TextFieldPattern.KeyboardAppearance 设值，默认 NONE_IMMERSIVE | 正常 |
| AC-5.2 | WHEN 调用 `.enablePreviewText(true)`（@since 12，默认 true） THEN 子 TextFieldPattern.supportPreviewText_=true | 正常 |
| AC-5.3 | WHEN 调用 `.enablePreviewText(false)` THEN 预览文本不展示（预览=未提交的临时输入态） | 正常 |
| AC-5.4 | WHEN 调用 `.autoCapitalizationMode(AutoCapitalizationMode.SENTENCES)`（@since 20） THEN 子 TextFieldPattern.AutoCapitalizationMode 设值；实际生效取决于输入法应用 | 正常 |
| AC-5.5 | WHEN 未设 autoCapitalizationMode THEN 默认 NONE（不自动大写） | 正常 |

### US-6: 触感反馈与返回键

**作为** 应用开发者,
**我想要** 控制文本交互的触感反馈与返回键传播,
**以便** 控制交互振动与返回键的键盘关闭行为。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 调用 `.enableHapticFeedback(true)`（@since 13，默认 true）且应用声明 ohos.permission.VIBRATE THEN 光标滑动/长按时触发 Sensors::StartVibrator | 正常 |
| AC-6.2 | WHEN 调用 `.enableHapticFeedback(false)` THEN isEnableHapticFeedback_=false，CHECK_NULL_VOID 守卫短路，不触发振动 | 正常 |
| AC-6.3 | WHEN 未声明 VIBRATE 权限 THEN 振动调用无效果（需在 module.json5 requestPermissions 声明） | 异常 |
| AC-6.4 | WHEN 调用 `.stopBackPress(true)`（@since 15，默认 true） THEN OnBackPressed 返回 true，消费 back 事件关闭键盘/选区不导航 | 正常 |
| AC-6.5 | WHEN 调用 `.stopBackPress(false)` THEN OnBackPressed 返回 false，关闭键盘后 back 事件传播至页面导航 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-05 | UITest | search_model_ng.cpp:1161 RequestKeyboardOnFocus |
| AC-1.2 | R-1 | TASK-05 | UITest | 同上 |
| AC-1.3 | R-2 | TASK-05 | UITest | search_model_ng.cpp:1376 SetSearchEnterKeyType |
| AC-1.4 | R-3 | TASK-05 | UITest | search_model_ng.cpp:1384 UNSPECIFIED→SEARCH |
| AC-1.5 | R-3 | TASK-05 | UITest | search.d.ts:764 默认 Search |
| AC-2.1 | R-4 | TASK-05 | UITest | search_model_ng.cpp:1051 SetType |
| AC-2.2 | R-5 | TASK-05 | UITest | text_input_type.cpp:25 URL remap |
| AC-2.3 | R-5 | TASK-05 | UITest | text_input_type.cpp:28 OTC remap |
| AC-2.4 | R-4 | TASK-05 | UITest | search.d.ts:1172 默认 NORMAL |
| AC-2.5 | R-6 | TASK-05 | UITest | search_model_ng.cpp:1401 SetMaxLength |
| AC-2.6 | R-7 | TASK-05 | UITest | search.d.ts:940 <0→默认 |
| AC-2.7 | R-6 | TASK-05 | UITest | 同上 |
| AC-3.1 | R-8 | TASK-05 | UITest | search_model_ng.cpp:604 SetInputFilter |
| AC-3.2 | R-9 | TASK-05 | UITest | search.d.ts:672 inputFilter 覆盖 type |
| AC-3.3 | R-8 | TASK-05 | UITest | TextFieldEventHub.SetOnInputFilterError |
| AC-3.4 | R-8 | TASK-05 | UITest | 空字符串清除 |
| AC-4.1 | R-10 | TASK-05 | UITest | search_model_ng.cpp:959 SetCustomKeyboard |
| AC-4.2 | R-11 | TASK-05 | UITest | search_model_static.cpp:795 value_or(false) |
| AC-4.3 | R-10 | TASK-05 | UITest | undefined 关闭 |
| AC-4.4 | R-12 | TASK-05 | UITest | search.d.ts:1095 不可 attributeModifier |
| AC-4.5 | R-10 | TASK-05 | UITest | 焦点丢失关闭 |
| AC-5.1 | R-13 | TASK-05 | UITest | search_model_ng.cpp:929 SetKeyboardAppearance |
| AC-5.2 | R-14 | TASK-05 | UITest | search_model_ng.cpp:907 SetEnablePreviewText |
| AC-5.3 | R-14 | TASK-05 | UITest | 同上 |
| AC-5.4 | R-15 | TASK-05 | UITest | search_model_ng.cpp:1390 SetSearchCapitalizationMode |
| AC-5.5 | R-15 | TASK-05 | UITest | search.d.ts:1340 默认 NONE |
| AC-6.1 | R-16 | TASK-05 | UITest | vibrator_utils.cpp:82 StartVibrator |
| AC-6.2 | R-16 | TASK-05 | UITest | text_field_pattern.cpp:2944 CHECK_NULL_VOID |
| AC-6.3 | R-17 | TASK-05 | UITest | search.d.ts:1320 需 VIBRATE |
| AC-6.4 | R-18 | TASK-05 | UITest | text_field_pattern.cpp:8418 OnBackPressed |
| AC-6.5 | R-18 | TASK-05 | UITest | 同上 |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | `enableKeyboardOnFocus(bool)` 设置 | 子 TextFieldPattern.needToRequestKeyboardOnFocus_ 设值 | 默认 true；存于 Pattern 运行时 | AC-1.1, AC-1.2 |
| R-2 | 行为 | `enterKeyType(EnterKeyType)` 设置 | 子 TextFieldPattern.TextInputAction 设值传入 IME | 存于 Pattern 运行时 | AC-1.3 |
| R-3 | 边界 | enterKeyType=UNSPECIFIED 或未设 | 静默重映射为 SEARCH | search_model_ng.cpp:1384 | AC-1.4, AC-1.5 |
| R-4 | 行为 | `type(SearchType)` 设置 | CastToTextInputType 转换 + TextInputType + TypeChanged=true + IsFilterChanged=true，触发 MEASURE | 存于 TextFieldLayoutProperty | AC-2.1, AC-2.4 |
| R-5 | 边界 | type=URL(13) 或 ONE_TIME_CODE(14) | CastToTextInputType 特殊重映射：URL(13)→URL(6)，OTC(14)→OTC(13) | text_input_type.cpp:25-29 | AC-2.2, AC-2.3 |
| R-6 | 行为 | `maxLength(N)` 设置正数 | 子 TextFieldLayoutProperty.MaxLength=N，触发 MEASURE | 存于 TextFieldLayoutProperty；默认无限制 | AC-2.5, AC-2.7 |
| R-7 | 边界 | maxLength < 0 | 重置为无限制 | SDK 约束 | AC-2.6 |
| R-8 | 行为 | `inputFilter(regex, error?)` 设置 | 子 TextFieldLayoutProperty.InputFilter 设正则 + EventHub 错误回调，触发 MEASURE | 存于 TextFieldLayoutProperty | AC-3.1, AC-3.3, AC-3.4 |
| R-9 | 行为 | inputFilter 已设 | type 属性的内置过滤不生效（inputFilter 覆盖 type 过滤） | SDK 互斥约束 | AC-3.2 |
| R-10 | 行为 | `customKeyboard(builder/node, options?)` 设置 | 子 TextFieldPattern.customKeyboard_ + customKeyboardOption_.supportAvoidance 设值 | 存于 Pattern 运行时；undefined 关闭 | AC-4.1, AC-4.3, AC-4.5 |
| R-11 | 边界 | supportAvoidance 未设 | 默认 false（页面不被避让提升） | search_model_static.cpp:795 | AC-4.2 |
| R-12 | 边界 | 在 attributeModifier 中调用 customKeyboard | 不生效 | SDK 注明 | AC-4.4 |
| R-13 | 行为 | `keyboardAppearance(KeyboardAppearance)` 设置 | 子 TextFieldPattern.KeyboardAppearance 设值 | 默认 NONE_IMMERSIVE；存于 Pattern 运行时 | AC-5.1 |
| R-14 | 行为 | `enablePreviewText(bool)` 设置 | 子 TextFieldPattern.supportPreviewText_ 设值 | 默认 true；预览=临时未提交输入态 | AC-5.2, AC-5.3 |
| R-15 | 行为 | `autoCapitalizationMode(AutoCapitalizationMode)` 设置 | 子 TextFieldPattern.AutoCapitalizationMode 设值 | 默认 NONE；实际生效取决于输入法应用 | AC-5.4, AC-5.5 |
| R-16 | 行为 | `enableHapticFeedback(bool)` 设置（@since 13） | 子 TextFieldPattern.isEnableHapticFeedback_ 设值；true 时光标滑动/长按触发 Sensors::StartVibrator | 默认 true；需 VIBRATE 权限 | AC-6.1, AC-6.2 |
| R-17 | 异常 | 未声明 VIBRATE 权限 | 振动调用无效果 | 需 module.json5 requestPermissions | AC-6.3 |
| R-18 | 行为 | `stopBackPress(bool)` 设置（@since 15） | OnBackPressed 返回 IsStopBackPress()：true 消费 back 关闭键盘不导航；false 传播给页面导航 | 默认 true；存于 TextFieldLayoutProperty(NORMAL) | AC-6.4, AC-6.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | US-1 键盘弹出与回车键 | UITest | 验证 enableKeyboardOnFocus 运行时标志；enterKeyType UNSPECIFIED→SEARCH |
| VM-2 | US-2 输入类型与最大长度 | UITest | 验证 SearchType URL/OTC 值重映射；maxLength <0 重置 |
| VM-3 | US-3 输入过滤 | UITest | 验证 inputFilter 覆盖 type 过滤；error 回调 |
| VM-4 | US-4 自定义键盘 | UITest | 验证 builder/node 两路径；supportAvoidance 默认 false；不可 attributeModifier |
| VM-5 | US-5 键盘外观与预览 | UITest | 验证 keyboardAppearance/enablePreviewText/autoCapitalizationMode 默认值 |
| VM-6 | US-6 触感与返回键 | UITest | 验证 VIBRATE 权限门控；stopBackPress 返回值语义 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `enableKeyboardOnFocus(value: boolean)` | Public | boolean | SearchAttribute | 无 | 聚焦弹键盘 | AC-1.1..AC-1.2 |
| `enterKeyType(value: EnterKeyType)` | Public | EnterKeyType | SearchAttribute | 无 | 回车键类型 | AC-1.3..AC-1.5 |
| `type(value: SearchType)` | Public | SearchType 枚举 | SearchAttribute | 无 | 输入类型 | AC-2.1..AC-2.4 |
| `maxLength(value: number)` | Public | number | SearchAttribute | 无 | 最大字符数 | AC-2.5..AC-2.7 |
| `inputFilter(value: ResourceStr, error?: Callback<string>)` | Public | ResourceStr+Callback | SearchAttribute | 无 | 正则过滤 | AC-3.1..AC-3.4 |
| `customKeyboard(value: CustomBuilder\|ComponentContent\|undefined, options?: KeyboardOptions)` | Public | CustomBuilder/ComponentContent+KeyboardOptions | SearchAttribute | 无 | 自定义键盘 | AC-4.1..AC-4.5 |
| `keyboardAppearance(appearance: Optional<KeyboardAppearance>)` | Public | KeyboardAppearance | SearchAttribute | 无 | 键盘外观 | AC-5.1 |
| `enablePreviewText(enable: boolean)` | Public | boolean | SearchAttribute | 无 | 预览文本 | AC-5.2, AC-5.3 |
| `autoCapitalizationMode(mode: AutoCapitalizationMode)` | Public | AutoCapitalizationMode | SearchAttribute | 无 | 自动大写 | AC-5.4, AC-5.5 |
| `enableHapticFeedback(isEnabled: boolean)` | Public | boolean | SearchAttribute | 无 | 触感反馈(需VIBRATE) | AC-6.1..AC-6.3 |
| `stopBackPress(isStopped: Optional<boolean>)` | Public | boolean | SearchAttribute | 无 | 返回键传播 | AC-6.4, AC-6.5 |
| `enum SearchType { NORMAL/NUMBER/PHONE_NUMBER/EMAIL/NUMBER_DECIMAL/URL/ONE_TIME_CODE }` | Public | — | — | 无 | 输入类型枚举 | AC-2.1..AC-2.4 |
| `interface KeyboardOptions { supportAvoidance?: boolean }` | Public | — | — | 无 | 键盘选项 | AC-4.1..AC-4.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 11 属性跨版本引入 | 变更 | @since 10/11/12/13/15/20 分批 | 低版本不支持 | 全部 AC |
| enableHapticFeedback 需 VIBRATE 权限 | 变更 | @since 13 引入权限要求 | 需 module.json5 声明 | AC-6.1, AC-6.3 |

## 接口规格

> L2+ 复杂度。以下仅列代表性接口。

### 接口定义

**type(value: SearchType)** — SearchType 值重映射

| 属性 | 值 |
|------|-----|
| 函数签名 | `type(value: SearchType): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1..AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | SearchType | 是 | NORMAL | URL(13)→内部(6)、OTC(14)→内部(13) 经 CastToTextInputType 重映射；设值触发 TypeChanged+IsFilterChanged |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | type=NUMBER | pass-through(2) | AC-2.1 |
| 2 | type=URL | 13→6 重映射 | AC-2.2 |
| 3 | type=ONE_TIME_CODE | 14→13 重映射 | AC-2.3 |
| 4 | 未设 | NORMAL(=TEXT) | AC-2.4 |

---

**enableHapticFeedback(isEnabled: boolean)** — 唯一需权限的 Search API

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableHapticFeedback(isEnabled: boolean): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1..AC-6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isEnabled | boolean | 是 | true | 需 ohos.permission.VIBRATE；false 时 CHECK_NULL_VOID 短路 |

---

**stopBackPress(isStopped: Optional<boolean>)** — 返回值语义

| 属性 | 值 |
|------|-----|
| 函数签名 | `stopBackPress(isStopped: Optional<boolean>): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.4, AC-6.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| isStopped | boolean | 否 | true | true=OnBackPressed 返回 true 消费 back；false=传播导航 |

## 兼容性声明

- **已有 API 行为变更:** 是。11 属性跨 API 10-20 引入；SearchType.URL/ONE_TIME_CODE 经 CastToTextInputType 值重映射；enterKeyType UNSPECIFIED 静默重映射为 SEARCH；inputFilter 覆盖 type 过滤；enableHapticFeedback 需 VIBRATE 权限；stopBackPress 默认 true 消费 back 事件。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（enableKeyboardOnFocus/customKeyboard）
- **API 版本号策略:** @since 10/11/12/13/15/20 分批标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 全委托子节点 | 11 个 API 全部委托子 TextFieldPattern/TextFieldLayoutProperty，零个存于 SearchLayoutProperty | 全部 AC |
| 状态位置分裂 | 4 个存于 TextFieldLayoutProperty(InputFilter/TextInputType/MaxLength/StopBackPress)，7 个存于 TextFieldPattern 运行时 | 全部 AC |
| SearchType 值重映射 | URL(13)→(6)、OTC(14)→(13) 经 CastToTextInputType 特殊处理 | AC-2.2, AC-2.3 |
| haptic 需 VIBRATE 权限 | 唯一需权限的 Search API，门控 Sensors::StartVibrator | AC-6.1..AC-6.3 |
| stopBackPress 返回值语义 | OnBackPressed 返回 bool：true 消费 false 传播 | AC-6.4, AC-6.5 |
| enterKeyType 默认强制 | UNSPECIFIED→SEARCH 静默重映射 | AC-1.4 |
| inputFilter 覆盖 type | inputFilter 设后 type 内置过滤不生效 | AC-3.2 |
| customKeyboard 不可 attributeModifier | SDK 注明限制 | AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | type 变更触发 MEASURE + TypeChanged/IsFilterChanged 正则重建 | UITest | search_model_ng.cpp:1051-1067 |
| 安全 | enableHapticFeedback 需 VIBRATE 权限，未声明时振动无效 | 权限检查 | vibrator_utils.cpp:82 |
| 可测试性 | enableKeyboardOnFocus/enableHapticFeedback/keyboardAppearance 经 Inspector 输出 | Inspector dump | search_pattern.cpp:1927-1928,1942 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 全部属性支持 | — | UITest | — |
| 平板/折叠屏 | 同手机 | 无差异 | UITest | — |
| 穿戴 | 同手机 | 无差异 | UITest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不影响无障碍语义 | — |
| 大字体 | 否 | 键盘/输入控制不直接涉及大字体 | — |
| 深色模式 | 否 | keyboardAppearance 可控制键盘外观但与深色模式独立 | — |
| 多窗口/分屏 | 否 | 无特殊行为 | — |
| 多用户 | 否 | 无特殊行为 | — |
| 版本升级 | 是 | 11 属性跨 API 10-20 引入；VIBRATE 权限 @since 13 | 全部 AC |
| 生态兼容 | 是 | 动态+静态+C-API+Cangjie FFI 全覆盖；customKeyboard 有 builder/node 两路径 | 全部 AC |

## 行为场景（Gherkin）

```gherkin
Feature: Search 键盘与输入控制
  作为应用开发者
  我想要控制搜索框的键盘行为与输入约束
  以便提供一致的输入交互

  Scenario Outline: SearchType 值重映射
    Given Search 组件已创建
    When 调用 .type(<sdkType>)
    Then 内部 TextInputType 为 <internal>

    Examples:
      | sdkType | internal |
      | NORMAL | TEXT(0) |
      | NUMBER | NUMBER(2) |
      | URL | URL(6) |
      | ONE_TIME_CODE | ONE_TIME_CODE(13) |

  Scenario: enterKeyType UNSPECIFIED 重映射
    Given Search 组件已创建
    When 调用 .enterKeyType(EnterKeyType.UNSPECIFIED)
    Then TextInputAction 被静默重映射为 SEARCH

  Scenario: inputFilter 覆盖 type 过滤
    Given Search 组件已创建且 type = SearchType.NUMBER
    When 调用 .inputFilter("[a-z]")
    Then type 的数字过滤不生效
    And 仅允许 a-z 输入

  Scenario: enableHapticFeedback 权限门控
    Given Search 组件已创建且 enableHapticFeedback = true
    When 用户长按文本触发触感
    Then 若应用声明 VIBRATE 权限 THEN Sensors::StartVibrator 触发
    And 若未声明 THEN 振动无效

  Scenario: stopBackPress 返回值语义
    Given Search 组件已创建且 stopBackPress = <value>
    When 用户按下返回键
    Then OnBackPressed 返回 <result>
    And back 事件 <propagation>

    Examples:
      | value | result | propagation |
      | true | true | 被消费(关闭键盘不导航) |
      | false | false | 传播(页面导航) |
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
    query: "11 个键盘/输入 API 全部委托子 TextFieldPattern/TextFieldLayoutProperty 而非 SearchLayoutProperty"
  - repo: "openharmony/arkui_ace_engine"
    query: "CastToTextInputType 对 SearchType.URL(13)→URL(6) 和 ONE_TIME_CODE(14)→OTC(13) 的值重映射"
  - repo: "openharmony/arkui_ace_engine"
    query: "enableHapticFeedback 经 VibratorUtils::StartVibraFeedback→Sensors::StartVibrator 的 VIBRATE 权限门控"
  - repo: "openharmony/arkui_ace_engine"
    query: "stopBackPress OnBackPressed 返回 IsStopBackPress() 的 bool 消费/传播语义"
  - repo: "openharmony/arkui_ace_engine"
    query: "enterKeyType UNSPECIFIED 静默重映射为 SEARCH"
  - repo: "openharmony/arkui_ace_engine"
    query: "inputFilter 设置后 type 属性内置过滤不生效的互斥约束"
  - repo: "openharmony/interface_sdk-js"
    query: "search.d.ts 中 11 个键盘/输入属性与 SearchType 枚举的 @since/默认/权限"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/search.d.ts`；`frameworks/core/components_ng/pattern/search/search_model_ng.cpp`；`frameworks/core/common/ime/text_input_type.cpp`；`design.md`(DESIGN-Func-05-09-03)
