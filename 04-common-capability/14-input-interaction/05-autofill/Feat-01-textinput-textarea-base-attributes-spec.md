# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput/TextArea AutoFill 基础属性与类型枚举 |
| 特性编号 | Func-04-14-05-Feat-01 |
| 所属 Epic | 04-通用能力层 / 14-输入交互 / 05-自动补全能力（AutoFill） |
| 优先级 | P1 |
| 目标版本 | API 12–24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `.enableAutoFill(bool)` ArkTS 属性规格化（TextInput/TextArea, @since 12） | 启用/禁用自动填充；默认 `true` |
| ADDED | `.contentType(TextContentType)` ArkTS 属性规格化（TextInput/TextArea, @since 12） | 字段语义类型；39 项内部枚举（NDK 仅暴露 33 项） |
| ADDED | `.passwordRules(string)` ArkTS 属性规格化（TextInput 独有, @since 12） | 密码生成规则透传 Password Vault |
| ADDED | `.enableAutoFillAnimation(bool)` ArkTS 属性规格化（TextInput 独有, @since 12） | 启用/禁用填充动画；默认 `true` |
| ADDED | NDK 属性枚举规格化（@since 12, 部分扩展 @since 18/20/24） | `NODE_TEXT_INPUT_ENABLE_AUTO_FILL`/`NODE_TEXT_INPUT_CONTENT_TYPE`/`NODE_TEXT_INPUT_PASSWORD_RULES`/`NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION`/`NODE_TEXT_AREA_ENABLE_AUTO_FILL`/`NODE_TEXT_AREA_CONTENT_TYPE` |
| ADDED | `ArkUI_TextInputContentType` C-API 枚举规格化（33 项, @since 12 基础 21 项 + @since 18 扩展 12 项） | NDK 公开枚举 |
| ADDED | 内部 `TextContentType`/`AceAutoFillType` 枚举与映射规格化 | 39 项内部枚举；`+5 CONVERT_CONTENT_TYPE` 偏移；`VISIBLE_PASSWORD↔ACE_PASSWORD` 名称发散 |
| ADDED | `AceAutoFillError`/`AceAutoFillTriggerType` 内部枚举规格化 | 错误码 12 项；触发类型 4 项 |
| ADDED | 菜单项枚举存在性规格化（@since 24） | `ARKUI_TEXT_MENU_ITEM_ID_AUTO_FILL`/`ARKUI_TEXT_MENU_ITEM_ID_PASSWORD_VAULT`（菜单 UI 行为详见 Feat-03） |

## 输入文档

| 类型 | 路径 |
|------|------|
| 设计文档 | `04-common-capability/14-input-interaction/05-autofill/design.md` |
| SDK 动态 API | `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`、`text_area.d.ts`（注：本仓不含 SDK 头文件，签名以 in-repo 镜像 `frameworks/bridge/declarative_frontend/ark_component/export/arkComponent.d.ts:867-868` 为参考，未经 d.ts 验证——见兼容性声明） |
| C-API 头文件 | `interfaces/native/native_node.h`、`interfaces/native/node_attributes/text_input.h`、`interfaces/native/node_attributes/text_common.h` |
| 内部枚举头文件 | `frameworks/base/view_data/ace_auto_fill_type.h`、`ace_auto_fill_error.h`、`frameworks/core/components_ng/pattern/text_field/text_content_type.h` |

> 需求基线、不涉及项详见 design.md，本文档不重复摘录。design.md 与本文档并行产出。

## 用户故事

### US-1: enableAutoFill 属性设置

作为应用开发者，我想要通过 `.enableAutoFill(bool)` 在 TextInput/TextArea 上启用或禁用自动填充，以便控制字段是否参与系统自动填充能力。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN TextInput `.enableAutoFill(true)` 且原值非 true THEN `TextFieldLayoutProperty::EnableAutoFill = true`，触发 `PROPERTY_UPDATE_MEASURE` 脏标志 | 正常 |
| AC-1.2 | WHEN TextInput `.enableAutoFill(false)` 且原值非 false THEN `EnableAutoFill = false`，触发 `PROPERTY_UPDATE_MEASURE` | 正常 |
| AC-1.3 | WHEN TextInput `.enableAutoFill()` 未传参（undefined）THEN `JSTextField::SetEnableAutoFill` 将非 boolean 视为默认值 `true`，调用 `SetEnableAutoFill(true)`（`js_textfield.cpp:1905`） | 边界 |
| AC-1.4 | WHEN TextInput `.enableAutoFill("false")`（字符串而非 boolean）THEN 行为同 AC-1.3：默认 `true`（`!jsValue->IsBoolean()` 早返回） | 异常 |
| AC-1.5 | WHEN TextArea `.enableAutoFill(false)` THEN 行为与 AC-1.2 一致（TextArea 复用 `JSTextField::SetEnableAutoFill`，`js_textarea.cpp:117`） | 正常 |
| AC-1.6 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_ENABLE_AUTO_FILL, {.value[0].i32 = 0})` THEN `EnableAutoFill = false`，返回 `ERROR_CODE_NONE`（参数 ≥ 1 满足 `CheckAttributeItemArray(REQUIRED_ONE_PARAM)`，`style_modifier.cpp:6363-6366`） | 正常 |
| AC-1.7 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_ENABLE_AUTO_FILL, {})`（零参数）THEN 返回 `ERROR_CODE_PARAM_INVALID`，不修改属性（`style_modifier.cpp:6363`） | 异常 |
| AC-1.8 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_ENABLE_AUTO_FILL, {.value[0].i32 = 5})`（非 0/1 整数）THEN 经 u32→bool cast 后变为 `true`，无 0/1 范围校验（`style_modifier.cpp:6367-6368` → `node_text_input_modifier.cpp:413`） | 边界 |
| AC-1.9 | WHEN NDK `ResetArkUITextInputAttribute(node, NODE_TEXT_INPUT_ENABLE_AUTO_FILL)` THEN `EnableAutoFill` 重置为默认 `true`（`DEFAULT_ENABLE_AUTO_FILL = true`，`node_text_input_modifier.cpp:50`） | 正常 |
| AC-1.10 | WHEN NDK `SetArkUITextAreaAttribute(node, NODE_TEXT_AREA_ENABLE_AUTO_FILL, {.value[0].i32 = 0})` THEN 路由经 TextInput-named `SetTextInputEnableAutoFill` dispatcher（`style_modifier.cpp:21382`），最终行为与 AC-1.6 一致（路由不对称但结果等价） | 正常 |
| AC-1.11 | WHEN 重复设置 `.enableAutoFill(true)` 后再次 `.enableAutoFill(true)`（同值）THEN `Update` 宏因 `NearEqual` 提前返回，不触发 `PROPERTY_UPDATE_MEASURE` | 边界 |

### US-2: contentType 属性设置

作为应用开发者，我想要通过 `.contentType(TextContentType)` 在 TextInput/TextArea 上声明字段语义类型，以便系统自动填充服务据此选择合适的凭据。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN TextInput `.contentType(TextContentType.USER_NAME)` 且原值不同 THEN `TextContentType = USER_NAME (0)`，同时设置 companion flag `TextContentTypeChanged = true`（同为 `PROPERTY_UPDATE_MEASURE`，`text_field_model_ng.cpp:406-408`） | 正常 |
| AC-2.2 | WHEN TextInput `.contentType()` 未传参（undefined）THEN `SetContentType(TextContentType::UNSPECIFIED)` 被调用（`js_textfield.cpp:310`） | 边界 |
| AC-2.3 | WHEN TextInput `.contentType("USER_NAME")`（字符串非 number）THEN 静默返回，不调用 Model，属性未修改（`!jsValue->IsNumber()` 早返回，`js_textfield.cpp:312`） | 异常 |
| AC-2.4 | WHEN TextInput ArkTS `.contentType(999)`（超出 NDK 定义范围 0–32）THEN ArkTS 路径 raw `static_cast<TextContentType>(999)` 原样存入（**不调用** `CastToTextContentType` clamp，`js_textfield.cpp:316`）；NDK 路径下 bridge 检测 `> END(37)` 并 clamp 至 `-1 (UNSPECIFIED)` 并打日志 `"TextInput content type is invalid"`（`node_text_input_modifier.cpp:502-505`）—— **ArkTS/NDK 校验不对称** | 异常 |
| AC-2.5 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_CONTENT_TYPE, {.value[0].i32 = 18 /*NICKNAME*/})` THEN dispatcher 应用 `+5 CONVERT_CONTENT_TYPE` 偏移（`style_modifier.cpp:6478-6482`），实际存入内部 `TextContentType::NICKNAME = 23`（`text_content_type.h:50`） | 正常 |
| AC-2.6 | WHEN NDK `GetArkUITextInputAttribute(node, NODE_TEXT_INPUT_CONTENT_TYPE)` 且内部值为 `TextContentType::NICKNAME (23)` THEN dispatcher 应用 `-5` 偏移（`style_modifier.cpp:6493-6498`），返回 NDK 值 `18` | 正常 |
| AC-2.7 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_CONTENT_TYPE, {.value[0].i32 = 33})`（NDK 未定义值，> 32）THEN dispatcher 不应用 +5 偏移（仅对 18–32 应用），原值 33 传入 bridge；bridge 检测 `33 > END(37) ?` 否，接受为有效内部值 33（**校验缺口**：未定义 NDK 值被错误接受） | 异常 |
| AC-2.8 | WHEN TextArea `.contentType(TextContentType.USER_NAME)` THEN 行为与 AC-2.1 一致（TextArea 复用 `JSTextField::SetContentType`） | 正常 |
| AC-2.9 | WHEN TextArea NDK `SetArkUITextAreaAttribute(node, NODE_TEXT_AREA_CONTENT_TYPE, {.value[0].i32 = 18})` THEN 路由经 TextInput-named `SetTextInputContentType` dispatcher（与 TextInput 共用），`+5` 偏移同样应用，内部值为 23（**TextArea 复用 TextInput-named dispatcher**，`style_modifier.cpp:21382`） | 正常 |

### US-3: passwordRules 属性设置

作为应用开发者，我想要通过 `.passwordRules(string)` 在 TextInput 上声明密码生成规则，以便 Password Vault 在 NEW_PASSWORD 自动填充时按规则生成新密码。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN TextInput `.passwordRules("minLen:8;maxLen:16;...")` THEN `PasswordRules = "minLen:8;..."` 字符串原样存入（无内容校验，任何字符串都被接受，`js_textfield.cpp:1898`） | 正常 |
| AC-3.2 | WHEN TextInput `.passwordRules()` 未传参（undefined）THEN 静默返回，不调用 Model，属性未修改（`!jsValue->IsString()` 早返回，`js_textfield.cpp:1893`；**注意：无 `info.Length()` 守卫**，直接读 `info[0]`） | 异常 |
| AC-3.3 | WHEN TextInput `.passwordRules(123)`（非字符串）THEN 同 AC-3.2：静默返回，属性未修改 | 异常 |
| AC-3.4 | WHEN TextArea `.passwordRules("...")` THEN 该 API 不存在（TextArea ArkTS 层无 `passwordRules` 绑定）；NDK 亦无 `NODE_TEXT_AREA_PASSWORD_RULES`——`passwordRules` 为 TextInput 独有 | 边界 |
| AC-3.5 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_PASSWORD_RULES, {.string = "minLen:8"})` THEN `PasswordRules = "minLen:8"`（dispatcher **不调用** `CheckAttributeItemArray`，仅 null-guards `item->string` 至 `""`，`style_modifier.cpp:6514-6517`） | 正常 |
| AC-3.6 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_PASSWORD_RULES, {.string = nullptr})` THEN `item->string` null-guard 至 `""`，`PasswordRules = ""` | 边界 |
| AC-3.7 | WHEN NDK `ResetArkUITextInputAttribute(node, NODE_TEXT_INPUT_PASSWORD_RULES)` THEN bridge 调用 `TextFieldModelNG::SetPasswordRules(frameNode, "")`（reset = 设置空字符串，**无独立 reset 路径**，`node_text_input_modifier.cpp:406`） | 正常 |

### US-4: enableAutoFillAnimation 属性设置（TextInput 独有）

作为应用开发者，我想要通过 `.enableAutoFillAnimation(bool)` 在 TextInput 上启用或禁用自动填充动画（icon show → text translation → icon hide），以便控制填充过程的视觉效果（动画管线详见 Feat-02）。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN TextInput `.enableAutoFillAnimation(false)` THEN `EnableAutoFillAnimation = false`，触发 `PROPERTY_UPDATE_MEASURE` | 正常 |
| AC-4.2 | WHEN TextInput `.enableAutoFillAnimation()` 未传参 THEN 默认 `true`（`SetEnableAutoFillAnimation(true)`，`js_textfield.cpp:1915`） | 边界 |
| AC-4.3 | WHEN TextArea `.enableAutoFillAnimation(false)` THEN 该 API 不存在（TextArea ArkTS 与 NDK 均无对应，`enableAutoFillAnimation` 为 TextInput 独有） | 边界 |
| AC-4.4 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION, {.value[0].i32 = 0})` THEN `EnableAutoFillAnimation = false`（**注意 NDK 公开枚举名为 `NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION`（无 `AUTO_`，值 `7036`，@since 20，`native_node.h:4180`）；dispatcher 函数名为 `SetTextInputEnableAutoFillAnimation`（有 `Auto`）——枚举名与函数名不匹配**） | 正常 |
| AC-4.5 | WHEN NDK `SetArkUITextInputAttribute(node, NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION, {.value[0].i32 = 5})` THEN 经 u32→bool cast 后变为 `true`（无 0/1 范围校验，`style_modifier.cpp:6394`） | 边界 |
| AC-4.6 | WHEN NDK `ResetArkUITextInputAttribute(node, NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION)` THEN `EnableAutoFillAnimation` 重置为默认 `true`（`DEFAULT_ENABLE_AUTO_FILL_ANIMATION = true`，`node_text_input_modifier.cpp:51`） | 正常 |

### US-5: 内容类型枚举完整性与版本演进

作为应用开发者，我想要了解 `TextContentType` / `ArkUI_TextInputContentType` 枚举的完整成员列表及版本演进，以便正确选择字段类型。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 在 API 12 设备上查询 `ArkUI_TextInputContentType` 枚举成员 THEN 可用 21 项（USER_NAME=0…FORMAT_ADDRESS=20，`text_input.h:97-149`） | 正常 |
| AC-5.2 | WHEN 在 API 18+ 设备上查询 THEN 额外可用 12 项扩展成员（PASSPORT_NUMBER=21…LICENSE_CHASSIS_NUMBER=32），共 33 项 NDK 成员（`text_input.h:155-220`） | 正常 |
| AC-5.3 | WHEN 在 API 17 设备上使用 `ARKUI_TEXTINPUT_CONTENT_TYPE_PASSPORT_NUMBER` (=21) THEN 行为未定义（NDK @since 18，早于 18 的设备不支持） | 边界 |
| AC-5.4 | WHEN 内部 `TextContentType` 枚举（C++ 层）查询 THEN 共 39 项（含 NDK 未暴露的 5 项 time/date 类型：`PRECISE_TIME=18`/`HOUR_AND_MINUTE=19`/`DATE=20`/`MONTH=21`/`YEAR=22`，加 `UNSPECIFIED=-1`，`text_content_type.h:22-65`） | 正常 |
| AC-5.5 | WHEN 内部 `AceAutoFillType` 枚举查询 THEN 共 39 项（与 `TextContentType` 名称 1:1 对应，加 `ACE_` 前缀，**但唯一名称发散**：`TextContentType::VISIBLE_PASSWORD` ↔ `AceAutoFillType::ACE_PASSWORD`，同值 =1，`text_field_pattern.cpp:194-261`） | 正常 |

### US-6: AutoFill 类型解析优先级

作为运行时系统，我想要在 `GetAutoFillType()` 解析时遵循确定的优先级（content type > input type > hint），以便字段最终确定的 AutoFill 类型可预测（触发管线详见 Feat-03）。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN 字段设置 `contentType(USER_NAME)` THEN `GetAutoFillType()` 返回 `ACE_USER_NAME`（优先级 1：contentType，`text_field_pattern.cpp:3802-3803`） | 正常 |
| AC-6.2 | WHEN 字段未设置 contentType 但 `inputType = VISIBLE_PASSWORD` THEN `GetAutoFillType()` 返回 `ACE_PASSWORD`（优先级 2：input type，经 `ConvertToAceAutoFillType`，`text_field_pattern.cpp:3804`） | 正常 |
| AC-6.3 | WHEN 字段既无 contentType 也无相关 inputType，且 `isNeedToHitType=true` 且 `!IsTriggerAutoFillPassword()` THEN `GetAutoFillType()` 经 `GetHintType()` 解析（优先级 3：hint，`text_field_pattern.cpp:3812`） | 正常 |
| AC-6.4 | WHEN 字段无任何可识别类型 THEN `GetAutoFillType()` 返回 `ACE_UNSPECIFIED`（回退，`text_field_pattern.cpp:3815`） | 边界 |
| AC-6.5 | WHEN 字段已设置 `enableAutoFill=false` THEN 在存储层 `EnableAutoFill` 仍为 false，但 `GetAutoFillType()` 本身不查询 `enableAutoFill`；实际门控发生在后续 `CheckAutoFill`（`text_field_pattern.cpp:3844-3860`，**存储层 4 属性彼此独立**） | 边界 |

### US-7: 平台/系统门控

作为系统，我想要在 `IsShowAutoFill()` 平台门控失败时静默禁用 AutoFill UI，以便在不支持的环境（锁屏、SceneBoardWindow、未支持 AutoFill 的设备）下不显示自动填充入口。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-7.1 | WHEN `Container::Current()->IsSceneBoardWindow()` 为 true THEN `IsShowAutoFill()` 立即返回 false（不显示 AutoFill UI，`text_field_pattern.cpp:2510-2511`） | 正常 |
| AC-7.2 | WHEN `ScreenLockManager::IsScreenLocked()` 为 true THEN `IsShowAutoFill()` 立即返回 false（`text_field_pattern.cpp:2513-2514`） | 正常 |
| AC-7.3 | WHEN `SystemProperties::IsAutoFillSupport()` 为 false THEN `IsShowAutoFill()` 返回 false（最终返回，`text_field_pattern.cpp:2516`） | 正常 |
| AC-7.4 | WHEN 三者均不触发 early-exit THEN `IsShowAutoFill()` 返回 `SystemProperties::IsAutoFillSupport()` 的值 | 正常 |
| AC-7.5 | WHEN Search 组件的 `SearchTextFieldPattern::IsNeedProcessAutoFill()` 被调用 THEN 始终返回 false（Search 显式禁用 AutoFill 处理，**无论存储的 `enableAutoFill`/`contentType`/`passwordRules` 值如何**，`search_text_field.cpp:167`） | 正常 |

### US-8: 静态前端 TextFieldModelStatic nullopt 行为

作为 ArkTS 静态前端运行时，我想要 `TextFieldModelStatic` 在 `std::optional` 为 `nullopt` 时回退到默认值或执行 reset，以便与静态 ArkTS 的"未设置"语义保持一致。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-8.1 | WHEN 静态前端 `TextFieldModelStatic::SetEnableAutoFill(node, std::nullopt)` THEN `value_or(true)` 委托到 NG `SetEnableAutoFill(node, true)`（**永不 reset**，`text_field_model_static.cpp:778-781`） | 边界 |
| AC-8.2 | WHEN 静态前端 `TextFieldModelStatic::SetEnableAutoFillAnimation(node, std::nullopt)` THEN 同 AC-8.1：委托到 NG `SetEnableAutoFillAnimation(node, true)` | 边界 |
| AC-8.3 | WHEN 静态前端 `TextFieldModelStatic::SetPasswordRules(node, std::nullopt)` THEN `ACE_RESET_NODE_LAYOUT_PROPERTY(PasswordRules)` 执行 reset（reset 本身不触发 dirty flag，`text_field_model_static.cpp:525-532`） | 边界 |
| AC-8.4 | WHEN 静态前端 `TextFieldModelStatic::SetContentType(node, std::nullopt)` THEN 若当前已设置且 `!= UNSPECIFIED`，设 `TextContentTypeChanged=true`；然后 `ACE_RESET_NODE_LAYOUT_PROPERTY(TextContentType)`（reset 本身不触发 dirty flag，由 Changed flag 携带 `PROPERTY_UPDATE_MEASURE`，`text_field_model_static.cpp:283-297`） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1–1.11 | R-1, R-2, R-3, R-8 | TASK-01 | 单元测试（JSTextField + TextFieldModelNG） | `js_textfield.cpp:1901-1909`、`text_field_model_ng.cpp:1003-1006,1716-1719`、`style_modifier.cpp:6360-6385`、`node_text_input_modifier.cpp:409-428,50-51` |
| AC-2.1–2.9 | R-4, R-5, R-6, R-7, R-9 | TASK-01 | 单元测试 + NDK 测试 | `js_textfield.cpp:303-318`、`text_field_model_ng.cpp:400-410,1405-1414`、`style_modifier.cpp:6470-6509,279`、`node_text_input_modifier.cpp:498-520`、`text_content_type.h:22-65` |
| AC-3.1–3.7 | R-10, R-11 | TASK-01 | 单元测试 + NDK 测试 | `js_textfield.cpp:1891-1899`、`text_field_model_ng.cpp:998-1001,1711-1714`、`style_modifier.cpp:6511-6535`、`node_text_input_modifier.cpp:386-407` |
| AC-4.1–4.6 | R-12, R-13 | TASK-01 | 单元测试 + NDK 测试 | `js_textfield.cpp:1911-1919`、`text_field_model_ng.cpp:1008-1011,1721-1725`、`style_modifier.cpp:6387-6412`、`native_node.h:4180`、`node_text_input_modifier.cpp:430-449,51` |
| AC-5.1–5.5 | R-14, R-15 | TASK-01 | 静态枚举检查 | `text_input.h:97-220`、`text_content_type.h:22-65`、`ace_auto_fill_type.h:22-63` |
| AC-6.1–6.5 | R-16 | TASK-01 | 单元测试 | `text_field_pattern.cpp:3798-3816,194-261,6123-6129` |
| AC-7.1–7.5 | R-17, R-18 | TASK-01 | 单元测试 + 环境模拟 | `text_field_pattern.cpp:2507-2517`、`search_text_field.cpp:165-168` |
| AC-8.1–8.4 | R-19, R-20 | TASK-01 | 单元测试（静态前端） | `text_field_model_static.cpp:283-297,525-532,778-781,1001-1004` |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|---------|---------|----------|---------|
| R-1 | 行为 | ArkTS `.enableAutoFill(bool)` 在 TextInput/TextArea 上调用 | `EnableAutoFill` 写入 `TextFieldLayoutProperty`，触发 `PROPERTY_UPDATE_MEASURE`（仅当值实际变化） | 默认值 `true`；ArkTS undefined/非 boolean → 默认 `true` | AC-1.1–1.5, AC-1.11 |
| R-2 | 行为 | NDK `NODE_TEXT_INPUT_ENABLE_AUTO_FILL` 设置/查询/重置 | dispatcher 校验 `REQUIRED_ONE_PARAM`，u32→bool cast 写入；reset 回落到 `DEFAULT_ENABLE_AUTO_FILL = true` | 非零 i32 → `true`（无 0/1 范围校验）；零参数 → `ERROR_CODE_PARAM_INVALID` | AC-1.6–1.9 |
| R-3 | 行为 | NDK `NODE_TEXT_AREA_ENABLE_AUTO_FILL` 设置 | 路由经 TextInput-named `SetTextInputEnableAutoFill` dispatcher（与 TextInput 共用），最终调用相同 `TextFieldModelNG::SetEnableAutoFill` | NDK 公开 API 路由不对称但结果等价 | AC-1.10 |
| R-4 | 行为 | ArkTS `.contentType(TextContentType)` 在 TextInput/TextArea 上调用 | `TextContentType` 写入，触发 `PROPERTY_UPDATE_MEASURE`；值变化时同时设置 companion flag `TextContentTypeChanged=true` | undefined → `UNSPECIFIED`；非 number → 静默返回不调用 Model | AC-2.1–2.3, AC-2.8 |
| R-5 | 边界 | ArkTS `.contentType(999)`（超出 NDK 定义范围 0–32） | ArkTS 路径 raw `static_cast` 不调用 `CastToTextContentType` clamp，值原样存入 | 与 NDK 路径（bridge clamp 至 `-1` + 日志）**校验不对称** | AC-2.4 |
| R-6 | 行为 | NDK `NODE_TEXT_INPUT_CONTENT_TYPE` 设置 | dispatcher 对 NICKNAME(18)…LICENSE_CHASSIS_NUMBER(32) 应用 `+5 CONVERT_CONTENT_TYPE` 偏移，对 0–17 与 > 32 不应用 | `CONVERT_CONTENT_TYPE = 5`（`style_modifier.cpp:279`）；源于内部 5 项 time/date 类型未在 NDK 暴露 | AC-2.5 |
| R-7 | 边界 | NDK `NODE_TEXT_INPUT_CONTENT_TYPE` 查询 | dispatcher 对内部值 23–37 应用 `-5` 偏移返回 NDK 值；其它范围原样返回 | set/get 偏移对称 | AC-2.6 |
| R-8 | 异常 | NDK `NODE_TEXT_INPUT_CONTENT_TYPE` 设置值 = 33（NDK 未定义值，> 32 且 ≤ 37） | dispatcher 不应用 +5 偏移，原值 33 传入 bridge；bridge 检测 `33 > END(37) ?` 否，错误地接受为有效内部值 | **校验缺口**：未定义 NDK 值被错误接受 | AC-2.7 |
| R-9 | 行为 | NDK `NODE_TEXT_AREA_CONTENT_TYPE` 设置 | 路由经 TextInput-named `SetTextInputContentType` dispatcher，`+5` 偏移同样应用 | 与 TextInput 共用 dispatcher | AC-2.9 |
| R-10 | 行为 | ArkTS `.passwordRules(string)` 在 TextInput 上调用 | `PasswordRules` 字符串原样存入，触发 `PROPERTY_UPDATE_MEASURE` | 无内容校验；undefined/非 string → 静默返回不调用 Model；**无 `info.Length()` 守卫** | AC-3.1–3.3 |
| R-11 | 边界 | TextArea 调用 `.passwordRules(...)` 或 NDK `NODE_TEXT_AREA_PASSWORD_RULES` | 该 API 不存在（TextArea ArkTS 与 NDK 均无对应）——`passwordRules` 为 TextInput 独有 | API 不对称 | AC-3.4 |
| R-12 | 行为 | ArkTS `.enableAutoFillAnimation(bool)` 在 TextInput 上调用 | `EnableAutoFillAnimation` 写入，触发 `PROPERTY_UPDATE_MEASURE` | 默认值 `true`；undefined/非 boolean → 默认 `true` | AC-4.1, AC-4.2 |
| R-13 | 边界 | TextArea 调用 `.enableAutoFillAnimation(...)` 或 NDK `NODE_TEXT_AREA_*_ANIMATION` | 该 API 不存在——`enableAutoFillAnimation` 为 TextInput 独有 | API 不对称 | AC-4.3 |
| R-14 | 行为 | NDK `NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION` 设置/查询/重置 | dispatcher u32→bool cast 写入；reset 回落到 `DEFAULT_ENABLE_AUTO_FILL_ANIMATION = true` | **NDK 公开枚举名 `NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION`（无 `AUTO_`，值 `7036`，@since 20）；dispatcher 函数名 `SetTextInputEnableAutoFillAnimation`（有 `Auto`）——枚举名与函数名不匹配** | AC-4.4–4.6 |
| R-15 | 行为 | 内部 `TextContentType` 与 `AceAutoFillType` 枚举映射 | 名称 1:1 对应（加 `ACE_` 前缀），**唯一名称发散**：`TextContentType::VISIBLE_PASSWORD` (=1) ↔ `AceAutoFillType::ACE_PASSWORD` (=1) | 同值异名；NDK 枚举仅 33 项，内部 39 项（多 5 项 time/date + UNSPECIFIED） | AC-5.4, AC-5.5 |
| R-16 | 行为 | `GetAutoFillType()` 解析优先级 | 1) `TextContentType` → 2) `TextInputType` → 3) `GetHintType()`（条件：`isNeedToHitType && !IsTriggerAutoFillPassword`）→ 4) `ACE_UNSPECIFIED` 回退 | 存储层 4 属性彼此独立；`enableAutoFill` 门控发生在后续 `CheckAutoFill` | AC-6.1–6.5 |
| R-17 | 行为 | `IsShowAutoFill()` 平台门控 | 1) `Container::Current()->IsSceneBoardWindow()` true → false；2) `ScreenLockManager::IsScreenLocked()` true → false；3) 返回 `SystemProperties::IsAutoFillSupport()` | **不查询字段级 `enableAutoFill`/`contentType`**——仅平台/系统状态门控 | AC-7.1–7.4 |
| R-18 | 行为 | Search 组件的 `SearchTextFieldPattern::IsNeedProcessAutoFill()` | 始终返回 false——Search 显式禁用 AutoFill 处理 | 无论存储的 `enableAutoFill`/`contentType`/`passwordRules` 值如何 | AC-7.5 |
| R-19 | 边界 | 静态前端 `TextFieldModelStatic::SetEnableAutoFill(node, std::nullopt)` | `value_or(true)` 委托到 NG `SetEnableAutoFill(node, true)`，**永不 reset** | 同样适用于 `SetEnableAutoFillAnimation(nullopt)` | AC-8.1, AC-8.2 |
| R-20 | 边界 | 静态前端 `TextFieldModelStatic::SetPasswordRules(node, std::nullopt)` 或 `SetContentType(node, std::nullopt)` | 执行 `ACE_RESET_NODE_LAYOUT_PROPERTY`；`SetContentType` nullopt 额外在已设置且 `!= UNSPECIFIED` 时设置 `TextContentTypeChanged=true`（由 Changed flag 携带 dirty flag） | reset 本身不触发 dirty flag（与 NG 路径不同） | AC-8.3, AC-8.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1–1.11 | 单元测试（JSTextField+TextFieldModelNG） | enableAutoFill ArkTS 路径：默认值/类型守卫/同值不触发 dirty flag |
| VM-2 | AC-1.6–1.10 | C-API 单元测试（capi_all_modifiers_test） | NDK 路径：参数校验/u32→bool cast/路由不对称 |
| VM-3 | AC-2.1–2.9 | 单元测试 + C-API 单元测试 | contentType：companion flag/+5 偏移/ArkTS-NDK 校验不对称/路由不对称 |
| VM-4 | AC-2.7 | C-API 单元测试 | NDK 未定义值（=33）校验缺口 |
| VM-5 | AC-3.1–3.7 | 单元测试 + C-API 单元测试 | passwordRules：无内容校验/null-guard/reset=空字符串 |
| VM-6 | AC-4.4 | C-API 单元测试 + 静态枚举扫描 | NDK 枚举名 `NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION` 与 dispatcher 函数名 `...EnableAutoFillAnimation` 不匹配 |
| VM-7 | AC-5.1–5.5 | 静态枚举扫描 + 单元测试 | NDK 33 项/内部 39 项/VISIBLE_PASSWORD↔ACE_PASSWORD 名称发散 |
| VM-8 | AC-6.1–6.5 | 单元测试（TextFieldPattern::GetAutoFillType） | 解析优先级 contentType > inputType > hint > UNSPECIFIED |
| VM-9 | AC-7.1–7.5 | 单元测试 + 环境模拟 | IsShowAutoFill 平台门控/Search 禁用 |
| VM-10 | AC-8.1–8.4 | 单元测试（TextFieldModelStatic） | nullopt→value_or(true)/reset 不触发 dirty flag |

## API 变更分析

### 新增 API

> 本域为已有实现补录，以下 API 均已存在于 SDK，不新增。**注意**：本仓不含 `interface/sdk-js/api/` 目录（属独立 interface 仓）；ArkTS 公共方法签名以 in-repo 镜像 `frameworks/bridge/declarative_frontend/ark_component/export/arkComponent.d.ts` 为参考，未经 d.ts 验证——见兼容性声明。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| `TextInputAttribute.enableAutoFill(value: boolean)` | Public | `value: boolean`，默认 `true` | `TextInputAttribute`（链式） | N/A | 启用/禁用 TextInput 自动填充 | AC-1.1–1.4 |
| `TextAreaAttribute.enableAutoFill(value: boolean)` | Public | `value: boolean`，默认 `true` | `TextAreaAttribute` | N/A | 启用/禁用 TextArea 自动填充 | AC-1.5 |
| `TextInputAttribute.contentType(value: TextContentType)` | Public | `value: TextContentType`（39 项内部枚举，NDK 暴露 33 项） | `TextInputAttribute` | N/A | 声明字段语义类型 | AC-2.1–2.4 |
| `TextAreaAttribute.contentType(value: TextContentType)` | Public | 同上 | `TextAreaAttribute` | N/A | 声明 TextArea 字段语义类型 | AC-2.8 |
| `TextInputAttribute.passwordRules(value: string)` | Public | `value: string`，密码生成规则 | `TextInputAttribute` | N/A | 透传 Password Vault | AC-3.1–3.3 |
| `TextInputAttribute.enableAutoFillAnimation(value: boolean)` | Public | `value: boolean`，默认 `true` | `TextInputAttribute` | N/A | 启用/禁用 TextInput 自动填充动画 | AC-4.1, AC-4.2 |
| NDK `NODE_TEXT_INPUT_ENABLE_AUTO_FILL` (=7034) | Public | `.value[0].i32` | i32 | `ERROR_CODE_NONE` / `ERROR_CODE_PARAM_INVALID` | TextInput 启用/禁用自动填充 | AC-1.6–1.9 |
| NDK `NODE_TEXT_INPUT_CONTENT_TYPE` (=7035) | Public | `.value[0].i32`（`ArkUI_TextInputContentType`） | i32 | 同上 | TextInput autofill 类型 | AC-2.5–2.7 |
| NDK `NODE_TEXT_INPUT_PASSWORD_RULES` (=7037) | Public | `.string` | string | 不调用 `CheckAttributeItemArray`，无错误码 | TextInput 密码生成规则 | AC-3.5–3.7 |
| NDK `NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION` (=7036, @since 20) | Public | `.value[0].i32` | i32 | 同 `NODE_TEXT_INPUT_ENABLE_AUTO_FILL` | TextInput 启用/禁用填充动画 | AC-4.4–4.6 |
| NDK `NODE_TEXT_AREA_ENABLE_AUTO_FILL` | Public | `.value[0].i32` | i32 | 同上 | TextArea 启用/禁用自动填充 | AC-1.10 |
| NDK `NODE_TEXT_AREA_CONTENT_TYPE` | Public | `.value[0].i32` | i32 | 同上 | TextArea autofill 类型 | AC-2.9 |
| NDK enum `ArkUI_TextInputContentType`（33 项, @since 12/18） | Public | — | — | — | C-API autofill 类型枚举 | AC-5.1–5.3 |
| NDK enum `ARKUI_TEXT_MENU_ITEM_ID_AUTO_FILL` (=16, @since 24) | Public | — | — | — | 菜单项枚举（菜单 UI 行为详见 Feat-03） | — |
| NDK enum `ARKUI_TEXT_MENU_ITEM_ID_PASSWORD_VAULT` (=17, @since 24) | Public | — | — | — | 菜单项枚举（菜单 UI 行为详见 Feat-03） | — |

### 变更/废弃 API

无。本域为已有实现补录，不修改任何已有 API 的签名或语义。

## 接口规格

### 接口定义

**`TextInputAttribute.enableAutoFill(value: boolean)`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextInputAttribute& TextInputAttribute::enableAutoFill(bool value)` |
| 返回值 | `TextInputAttribute&`（链式） |
| 开放范围 | Public |
| 错误码 | N/A（ArkTS 层无错误码机制） |
| 关联 AC | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 否 | `true`（undefined 或非 boolean 时） | 无范围限制；非 boolean 类型视为默认 `true`，**不抛错** |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.enableAutoFill(true)` 且原值非 true | `EnableAutoFill = true`，触发 `PROPERTY_UPDATE_MEASURE` | AC-1.1 |
| 2 | `.enableAutoFill(false)` 且原值非 false | `EnableAutoFill = false`，触发 `PROPERTY_UPDATE_MEASURE` | AC-1.2 |
| 3 | `.enableAutoFill()` 或 `.enableAutoFill("false")` | 默认 `true`，调用 `SetEnableAutoFill(true)` | AC-1.3, AC-1.4 |
| 4 | 重复设置同值 | `NearEqual` 提前返回，不触发 dirty flag | AC-1.11 |

---

**`TextInputAttribute.contentType(value: TextContentType)`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextInputAttribute& TextInputAttribute::contentType(TextContentType value)` |
| 返回值 | `TextInputAttribute&` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1–2.4, AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `TextContentType`（int32 enum） | 否 | `UNSPECIFIED` (-1)（undefined 时） | 范围 -1…37（内部）；NDK 暴露 0–32；**ArkTS 路径不调用 `CastToTextContentType` clamp**，越界值原样存入 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.contentType(USER_NAME)` 且原值不同 | `TextContentType = USER_NAME (0)`，设 `TextContentTypeChanged=true`，触发 `PROPERTY_UPDATE_MEASURE` | AC-2.1 |
| 2 | `.contentType()` undefined | 调用 `SetContentType(UNSPECIFIED)` | AC-2.2 |
| 3 | `.contentType("USER_NAME")` 非数字 | 静默返回，不调用 Model | AC-2.3 |
| 4 | `.contentType(999)` ArkTS 越界 | raw `static_cast` 原样存入（**不 clamp**） | AC-2.4 |

---

**`TextInputAttribute.passwordRules(value: string)`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextInputAttribute& TextInputAttribute::passwordRules(std::string value)` |
| 返回值 | `TextInputAttribute&` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1–3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 否 | `""`（empty，未传或非 string 时不修改属性） | 无内容校验；任何字符串原样存入；非 string → 静默返回不调用 Model；**实现无 `info.Length()` 守卫** |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.passwordRules("minLen:8")` | `PasswordRules = "minLen:8"`，触发 `PROPERTY_UPDATE_MEASURE` | AC-3.1 |
| 2 | `.passwordRules()` 或 `.passwordRules(123)` | 静默返回，属性未修改 | AC-3.2, AC-3.3 |

---

**`TextInputAttribute.enableAutoFillAnimation(value: boolean)`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TextInputAttribute& TextInputAttribute::enableAutoFillAnimation(bool value)` |
| 返回值 | `TextInputAttribute&` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1, AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 否 | `true` | 非 boolean → 默认 `true` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.enableAutoFillAnimation(false)` | `EnableAutoFillAnimation = false`，触发 `PROPERTY_UPDATE_MEASURE` | AC-4.1 |
| 2 | `.enableAutoFillAnimation()` | 默认 `true` | AC-4.2 |

---

**NDK `NODE_TEXT_INPUT_ENABLE_AUTO_FILL` / `NODE_TEXT_AREA_ENABLE_AUTO_FILL`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode SetArkUI{TextInput,TextArea}Attribute(node, NODE_*_ENABLE_AUTO_FILL, ArkUI_AttributeItem* item)` |
| 返回值 | `ArkUI_ErrorCode`（`ERROR_CODE_NONE` / `ERROR_CODE_PARAM_INVALID`） |
| 开放范围 | Public |
| 错误码 | `ERROR_CODE_PARAM_INVALID`（零参数） |
| 关联 AC | AC-1.6–1.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `.value[0].i32` | int32 | 是 | 文档默认 `true`（reset 时） | **无 0/1 范围校验**——非零 i32 经 u32→bool cast 后为 `true` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.value[0].i32 = 0` | `EnableAutoFill = false` | AC-1.6 |
| 2 | 零参数 | `ERROR_CODE_PARAM_INVALID` | AC-1.7 |
| 3 | `.value[0].i32 = 5` | 经 cast → `true`（无范围校验） | AC-1.8 |
| 4 | Reset | `EnableAutoFill = true`（`DEFAULT_ENABLE_AUTO_FILL`） | AC-1.9 |
| 5 | TextArea NDK 设置 | 路由经 TextInput-named dispatcher，结果等价 | AC-1.10 |

---

**NDK `NODE_TEXT_INPUT_CONTENT_TYPE` / `NODE_TEXT_AREA_CONTENT_TYPE`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_ErrorCode SetArkUI{TextInput,TextArea}Attribute(node, NODE_*_CONTENT_TYPE, ArkUI_AttributeItem* item)` |
| 返回值 | `ArkUI_ErrorCode` |
| 开放范围 | Public |
| 错误码 | `ERROR_CODE_PARAM_INVALID`（零参数） |
| 关联 AC | AC-2.5–2.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `.value[0].i32` | int32（`ArkUI_TextInputContentType`） | 是 | `UNSPECIFIED` (-1)（reset 时） | dispatcher 对 NDK 值 18–32 应用 `+5` 偏移；bridge 在 `> END(37)` 时 clamp 至 `-1`；**值 33–37 范围内被错误接受为有效**（校验缺口） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.value[0].i32 = 18` (NICKNAME) | +5 偏移，内部存 23 | AC-2.5 |
| 2 | Get 查询内部值 23 | -5 偏移，返回 18 | AC-2.6 |
| 3 | `.value[0].i32 = 33` (NDK 未定义) | 不应用偏移，bridge 接受为有效值 33（**校验缺口**） | AC-2.7 |
| 4 | TextArea NDK 设置 | 路由经 TextInput-named dispatcher，+5 偏移同样应用 | AC-2.9 |

## 兼容性声明

- **已有 API 行为变更:** 否。本特性为已有实现补录，不改 API 签名或语义。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。`TextContentType` 与 `TextContentTypeChanged` 不参与 `ToJsonValue`/`Reset`/`Clone`（`text_field_layout_property.h:107-183,62-105,344-390`）；`PasswordRules`/`EnableAutoFill`/`EnableAutoFillAnimation` 参与。Inspector dump 不显示 `contentType`——**已记录为已知限制（非缺陷，源码现状如此，详见风险表）**。
- **最低支持版本:** API 12（NDK 属性 `NODE_TEXT_INPUT_*` / `NODE_TEXT_AREA_*` @since 12；`enableAutoFillAnimation` NDK 枚举 `NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION` @since 20；菜单项 `ARKUI_TEXT_MENU_ITEM_ID_AUTO_FILL`/`PASSWORD_VAULT` @since 24）。
- **API 版本号策略:** 全版本标注。NDK 枚举成员 `@since` 12/18/20/24 在表中明确分列；ArkTS 公共方法 `@since` 因 `interface/sdk-js/api/` 不在本仓而未经 d.ts 验证——见风险表。
- **跨层校验不对称:** ArkTS `.contentType(999)` 路径 raw `static_cast` 不 clamp，NDK 路径 bridge 检测并 clamp 至 `UNSPECIFIED`——已记录为风险（不修改，源码现状）。
- **跨载体 API 不对称:** TextArea 不暴露 `passwordRules` 与 `enableAutoFillAnimation`（ArkTS 与 NDK 均无对应）——已记录为已知行为。
- **枚举名称发散:** `TextContentType::VISIBLE_PASSWORD` ↔ `AceAutoFillType::ACE_PASSWORD`（同值 =1，异名）——已记录为风险（跨 NDK/内部边界按名称 switch 的代码将出错）。
- **NDK 枚举名与 dispatcher 函数名不匹配:** NDK 公开枚举 `NODE_TEXT_INPUT_ENABLE_FILL_ANIMATION`（无 `AUTO_`，`native_node.h:4180`）；dispatcher 函数 `SetTextInputEnableAutoFillAnimation`（有 `Auto`，`style_modifier.cpp:6387`）——已记录为风险。
- **TextArea NDK 路由不对称:** `NODE_TEXT_AREA_*` 路由经 TextInput-named dispatcher，而非 `arkoala_api.h:6069-6072` 的 dedicated TextArea 函数指针（后者仅 ArkTS 桥使用，`arkts_native_text_area_bridge.cpp:2223`）——已记录为已知行为，结果等价。
- **静态前端 nullopt 行为:** `TextFieldModelStatic::SetEnableAutoFill(nullopt)` 始终委托到 NG `SetEnableAutoFill(node, true)`，**永不 reset**——已记录为已知行为。
- **PageNodeInfoWrap 默认值跨层不一致:** ArkTS/NDK/LayoutProperty `enableAutoFill` 默认 `true`，但 `PageNodeInfoWrap::GetEnableAutoFill` 基类默认 `false`（具体子类覆写）——已记录为风险。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|---------|
| 调用方向严格自上而下 | SDK → JS Bridge → Model → LayoutProperty，无逆向调用 | AC-1.1, AC-2.1, AC-3.1, AC-4.1 |
| 存储层属性独立 | `EnableAutoFill`/`EnableAutoFillAnimation`/`TextContentType`/`PasswordRules` 在 `Update` 宏中互不读取；仅 `SetContentType` 设置 `TextContentTypeChanged` companion flag | AC-6.5 |
| NDK 与内部枚举偏移约束 | NDK `ArkUI_TextInputContentType`（33 项, 0–32）与内部 `TextContentType`（39 项, -1…37）通过 `+5 CONVERT_CONTENT_TYPE` 偏移桥接；NICKNAME(18)→23, LICENSE_CHASSIS_NUMBER(32)→37 | AC-2.5, AC-2.6, AC-5.4 |
| 平台/系统门控先于字段门控 | `IsShowAutoFill()` 仅查平台状态，不查字段属性；字段门控（`enableAutoFill`/`contentType`）发生在后续 `CheckAutoFill` | AC-7.1–7.5, AC-6.5 |
| TextArea 路由复用约束 | NDK TextArea autofill 属性经 TextInput-named dispatcher 路由，结果等价；如未来重命名 TextInput dispatcher，TextArea 静默破裂 | AC-1.10, AC-2.9 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 同值重复设置不触发 dirty flag（`NearEqual` 早返回） | 单元测试 | `property.h:248-251`（`ACE_DEFINE_PROPERTY_ITEM_WITHOUT_GROUP` 生成的 `Update` 方法） |
| 安全 | `passwordRules` 字符串原样透传 Password Vault，本层不验证内容（信任边界在 Password Vault 侧） | 代码评审 | `js_textfield.cpp:1898`、`node_text_input_modifier.cpp:391` |
| 可测试性 | 4 个属性均可通过 `TextFieldModelNG::Get{EnableAutoFill,EnableAutoFillAnimation,ContentType,PasswordRules}(FrameNode*)` 静态查询 | 单元测试 | `text_field_model_ng.cpp:2418-2453` |
| 自动化维测 | `enableAutoFill`/`enableAutoFillAnimation`/`passwordRules` 参与 `ToJsonValue`，可通过 inspector dump 查询；`contentType` 不参与（已知限制） | Inspector dump | `text_field_layout_property.h:107-183` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|---------|---------|------|
| 手机 | 无差异 | `IsShowAutoFill()` 平台门控对所有设备类型一致 | 单元测试 | `text_field_pattern.cpp:2507-2517` |
| 平板 | 无差异 | 同上 | 同上 | 同上 |
| 折叠屏 | 无差异 | 同上 | 同上 | 同上 |

> `IsShowAutoFill()` 的设备差异由 `SystemProperties::IsAutoFillSupport()` 决定（产品维度），本特性不引入新的设备差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 否 | AutoFill 基础属性不直接关联无障碍语义；菜单 UI 无障碍由 Feat-03 处理 | — |
| 大字体 | 否 | 基础属性与大字体无交互 | — |
| 深色模式 | 否 | 基础属性与深色模式无交互 | — |
| 多窗口/分屏 | 是 | `IsShowAutoFill()` 在 `IsSceneBoardWindow()` 为 true 时返回 false——多窗口场景下 SceneBoardWindow 禁用 AutoFill UI | AC-7.1 |
| 多用户 | 否 | 基础属性与多用户无交互 | — |
| 版本升级 | 是 | API 12→18→20→24 演进明确：12 基础 21 项 + 18 扩展 12 项 + 20 NDK animation 枚举 + 24 菜单项枚举 | AC-5.1–5.3, AC-4.4, AC-1.6 |
| 生态兼容 | 是 | ArkTS 与 NDK 路径校验不对称（contentType 越界处理），NDK 枚举名与函数名不匹配，TextArea 路由不对称——均为生态兼容风险 | AC-2.4, AC-4.4, AC-1.10 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰——`passwordRules`/`enableAutoFillAnimation` 为 TextInput 独有；菜单 UI 行为属 Feat-03；动画管线属 Feat-02；触发管线属 Feat-03；Web 管线属 Feat-05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/interface/sdk-js"
    query: "ArkTS 公共方法 enableAutoFill / contentType / passwordRules / enableAutoFillAnimation 的 @since 版本与签名（interface/sdk-js/api/@internal/component/ets/text_input.d.ts 与 text_area.d.ts）——本仓不含此目录，需在 interface 仓验证"
  - repo: "openharmony/interface/sdk-js"
    query: "是否存在 popupForAutoFill / AutoFillCallbackInfo / AutoFillRequestData / autoFillContent / ContentFilter 公共 TS 类型——ace_engine 仓内零匹配，疑似 SDK 侧概念"
  - repo: "openharmony/ability_base"
    query: "AbilityBase::AutoFillType 枚举成员与 AceAutoFillType 的桥接（ViewDataWrap::ViewDataToType/HintToAutoFillType）——桥接行为详见 Feat-03 触发管线"
```

**关键文档：**
- design.md: `04-common-capability/14-input-interaction/05-autofill/design.md`
- SDK 镜像（本仓）: `frameworks/bridge/declarative_frontend/ark_component/export/arkComponent.d.ts`（仅 `enableAutoFill`/`passwordRules` 在 `:867-868`，无 `@since`）
- NDK 头文件: `interfaces/native/native_node.h`、`interfaces/native/node_attributes/text_input.h`、`text_common.h`
- 内部枚举头: `frameworks/base/view_data/ace_auto_fill_type.h`、`ace_auto_fill_error.h`、`frameworks/core/components_ng/pattern/text_field/text_content_type.h`
