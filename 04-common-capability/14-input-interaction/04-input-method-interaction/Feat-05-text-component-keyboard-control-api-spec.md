# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 输入法交互公共 API |
| 特性编号 | Func-04-14-04-Feat-05 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8–12（动态 @since 8–12；静态 @since 23） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
重定范围补录。本 Feat 覆盖输入法交互公共 API（customKeyboard/keyboardAppearance/enableKeyboardOnFocus/onWillAttachIME/onEditChange/stopEditing + IMEClient）。拥有这些 API 的**输入法交互语义**；04-14-03 Feat-05 保留非键盘交互触发。

## 输入文档
- 设计文档：`04-input-method-interaction/design.md`
- 源码定位：`frameworks/bridge/declarative_frontend/ark_modifier/src/text_input_modifier.ts`、`rich_editor_modifier.ts`、`search_pattern.cpp`(序列化)、`text_field_model.h`/`text_field_model_ng.h`/`rich_editor_model.h`/`search_model.h`、`arkts_native_rich_editor_bridge.h`

## 用户故事

### US-1: customKeyboard
作为开发者，我希望经 customKeyboard 挂载自定义键盘（含避让）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `customKeyboard(builder, options?)` THEN 挂载自定义键盘（@since 10/23） | 正常 |
| AC-1.2 | WHEN KeyboardOptions.supportAvoidance=true THEN 自定义键盘避让 | 正常 |
| AC-1.3 | WHEN RichEditor customKeyboard(builder\|ComponentContent, options?) THEN 挂载（@since 10/23） | 正常 |

### US-2: keyboardAppearance
作为开发者，我希望经 keyboardAppearance 设置键盘外观。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `keyboardAppearance(KeyboardAppearance)` THEN 设置外观（默认 NONE_IMMERSIVE，@since 10/23） | 正常 |

### US-3: enableKeyboardOnFocus
作为开发者，我希望经 enableKeyboardOnFocus 控制聚焦拉键盘。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `enableKeyboardOnFocus(boolean)` THEN 设置 needToRequestKeyboardOnFocus_（@since 10/23） | 正常 |
| AC-3.2 | WHEN false THEN 聚焦不拉键盘 | 边界 |

### US-4: onWillAttachIME / onEditChange / stopEditing / IMEClient
作为开发者，我希望经这些回调控制 IME 与编辑态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN `onWillAttachIME(Callback<IMEClient>)` THEN attach 前回调（@since 12/23） | 正常 |
| AC-4.2 | WHEN `onEditChange(Callback<boolean>)` THEN 编辑态切换回调（@since 8/23） | 正常 |
| AC-4.3 | WHEN `controller.stopEditing()` THEN 退出编辑/关闭键盘 | 正常 |
| AC-4.4 | WHEN IMEClient 类型 THEN {nodeId, extraInfo}（@since 12） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-KC-05 | 单测 | text_input_modifier.ts:286 |
| AC-1.2 | R-1 | TASK-KC-05 | 单测 | text_field_pattern.cpp:6210 |
| AC-1.3 | R-1 | TASK-KC-05 | 单测 | rich_editor_modifier.ts:126 |
| AC-2.1 | R-2 | TASK-KC-05 | 单测 | text_input_modifier.ts:466 |
| AC-3.1 | R-3 | TASK-KC-05 | 单测 | text_input_modifier.ts:242 |
| AC-4.1 | R-4 | TASK-KC-05 | 单测 | text_input_modifier.ts:516 |
| AC-4.2 | R-5 | TASK-KC-05 | 单测 | text_input_modifier.ts:117 |
| AC-4.3 | R-6 | TASK-KC-05 | 单测 | 控制器 stopEditing |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | customKeyboard(builder, options?) | 挂载自定义键盘；supportAvoidance→keyboardAvoidance_ | @since 10/23 | AC-1.1..1.3 |
| R-2 | 行为 | keyboardAppearance | 设置外观（默认 NONE_IMMERSIVE） | @since 10/23 | AC-2.1 |
| R-3 | 行为 | enableKeyboardOnFocus | 设置 needToRequestKeyboardOnFocus_ | @since 10/23 | AC-3.1,3.2 |
| R-4 | 行为 | onWillAttachIME | attach 前回调 IMEClient | @since 12/23 | AC-4.1,4.4 |
| R-5 | 行为 | onEditChange | 编辑态回调 | @since 8/23 | AC-4.2 |
| R-6 | 行为 | stopEditing | 退出编辑/关键盘 | controller | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 customKeyboard | 单测 | supportAvoidance |
| VM-2 | R-2..R-3 外观/聚焦 | 单测 | NONE_IMMERSIVE/needToRequest |
| VM-3 | R-4..R-6 回调/停止 | 单测 | IMEClient/onEditChange |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `customKeyboard(builder, options?)` | Public | CustomBuilder, KeyboardOptions? | this | 无 | 自定义键盘 @since 10/23 | AC-1.1 |
| `keyboardAppearance(value)` | Public | KeyboardAppearance | this | 无 | 键盘外观 @since 10/23 | AC-2.1 |
| `enableKeyboardOnFocus(value)` | Public | boolean | this | 无 | 聚焦拉键盘 @since 10/23 | AC-3.1 |
| `onWillAttachIME(callback)` | Public | Callback<IMEClient> | this | 无 | attach 前回调 @since 12/23 | AC-4.1 |
| `onEditChange(callback)` | Public | Callback<boolean> | this | 无 | 编辑态 @since 8/23 | AC-4.2 |
| `stopEditing()` | Public | — | void | 无 | 退出编辑 | AC-4.3 |
| `IMEClient` 类型 | Public | {nodeId, extraInfo} | — | 无 | 回调参数 @since 12 | AC-4.4 |

## 接口规格

### 接口定义

**customKeyboard(value, options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `customKeyboard(value: CustomBuilder, options?: KeyboardOptions): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | CustomBuilder | 是 | — | 自定义键盘 builder |
| options | KeyboardOptions | 否 | — | supportAvoidance |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 builder | 挂载 | AC-1.1 |
| 2 | supportAvoidance=true | 避让 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** onEditChange @since 8；customKeyboard/keyboardAppearance/enableKeyboardOnFocus @since 10；onWillAttachIME/IMEClient @since 12（静态 @since 23）
- **API 版本号策略:** 公共 API 全量 @since 标注（@since 源自 modifier bridge + 03 design，需外部 SDK 仓确认）

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 与 04-14-03 Feat-05 边界 | 本域拥有输入法交互语义 | 全部 |
| 跨 4 组件 | TextInput/TextArea/RichEditor/Search | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | API 可单测 | 单测 | text_input_modifier.ts |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 跨平台 | 静态 @since 23 | 单测 | — | rich_editor_modifier.ts |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 输入法交互支持无障碍 | 全部 |

## Spec 自审清单
- [x] 无占位符
- [x] AC 用 WHEN/THEN
- [x] 范围明确
- [x] 无模糊表述
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项检查

## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "customKeyboard/keyboardAppearance/enableKeyboardOnFocus/onWillAttachIME/onEditChange/IMEClient"
```
**关键文档：** `frameworks/bridge/declarative_frontend/ark_modifier/src/text_input_modifier.ts`、`rich_editor_modifier.ts`
