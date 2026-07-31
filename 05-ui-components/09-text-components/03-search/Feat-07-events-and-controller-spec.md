# 特性规格

> Func-05-09-03-Feat-07 事件回调与控制器：覆盖 17 个事件（onSubmit×2/onChange/onWillChange/onWillInsert/onDidInsert/onWillDelete/onDidDelete/onCopy/onWillCopy/onCut/onWillCut/onPaste/onTextSelectionChange/onContentScroll/onEditChange/onWillAttachIME）+ SearchController。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件回调与控制器（Events & SearchController） |
| 特性编号 | Func-05-09-03-Feat-07 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8(onSubmit/onChange/onCopy/onCut/onPaste/caretPosition)、API 10(onTextSelectionChange/onContentScroll/stopEditing)、API 12(onWillInsert/onDidInsert/onWillDelete/onDidDelete/onEditChange/setTextSelection)、API 14(onSubmit SubmitEvent)、API 15(onWillChange)、API 20(onWillAttachIME)、API 26(onWillCopy/onWillCut) |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 提交事件规格 | 补录：onSubmit Callback<string>(@since 8, NG no-op) + SearchSubmitCallback(@since 14, SubmitEvent.keepEditableState) |
| ADDED | 内容变更事件规格 | 补录：onChange(@since 8)、onWillChange(@since 15)、onWillInsert/onDidInsert/onWillDelete/onDidDelete(@since 12) |
| ADDED | 复制剪切粘贴事件规格 | 补录：onCopy/onCut/onPaste(@since 8)、onWillCopy/onWillCut(@since 26) |
| ADDED | 选区滚动与编辑事件规格 | 补录：onTextSelectionChange/onContentScroll(@since 10)、onEditChange(@since 12)、onWillAttachIME(@since 20) |
| ADDED | SearchController 规格 | 补录：caretPosition(@since 8)、stopEditing(@since 10)、setTextSelection(@since 12) + 继承方法 |

## 输入文档

- 设计文档：`design.md`（DESIGN-Func-05-09-03，Feat-07 增量合并）
- 源码定位：
  - 事件存储分裂：仅 onSubmit(@since 14) 存于 SearchEventHub（`search_event_hub.h:140`），其余 15 个委托子 TextFieldEventHub
  - onSubmit 双重载：`search_model_ng.h:68`(@since 8 no-op) `:69`(@since 14)；FireOnSubmit `search_event_hub.h:45-65`；keepEditable `search_pattern.cpp:847`
  - 事件链：onWill* 返回 bool 否决，onDid* 通知；`text_field_event_hub.h:393/423/443/462/482`
  - Controller 代理：`search_pattern.cpp:713-752` InitSearchController→Handle* 方法→子 TextFieldPattern
  - SDK：`interface/sdk-js/api/@internal/component/ets/search.d.ts`

## 用户故事

### US-1: 提交事件

**作为** 应用开发者,
**我想要** 在搜索提交时接收回调并控制是否保持编辑态,
**以便** 在搜索提交时执行业务逻辑并控制编辑态保持。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 点击搜索按钮/搜索图标/软键盘搜索键 THEN `OnClickButtonAndImage` 构造 TextFieldCommonEvent，调用 `SearchEventHub::FireOnSubmit(text, event)` | 正常 |
| AC-1.2 | WHEN onSubmit 使用 @since 14 SearchSubmitCallback 且回调调用 `event.keepEditableState()` THEN `IsKeepEditable()=true`，不退出编辑态 | 正常 |
| AC-1.3 | WHEN onSubmit 回调未调用 keepEditableState THEN `IsKeepEditable()=false`，调用 `StopEditing()` 退出编辑态 | 正常 |
| AC-1.4 | WHEN onSubmit 使用 @since 8 Callback<string> THEN NG 管线下为 no-op 空实现（不触发） | 边界 |
| AC-1.5 | WHEN FireOnSubmit 执行 THEN 记录 Recorder::SEARCH_SUBMIT 事件 | 正常 |

### US-2: 内容变更事件

**作为** 应用开发者,
**我想要** 监听文本变更的各个阶段并可否决变更,
**以便** 在文本变更的各阶段感知并可选否决变更。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 文本内容变化 THEN onChange 回调触发（存于子 TextFieldEventHub），SearchEventHub::UpdateChangeEvent 同步触发 | 正常 |
| AC-2.2 | WHEN 插入文本前 THEN onWillInsert 回调触发，返回 false 否决插入，true 允许 | 正常 |
| AC-2.3 | WHEN 插入文本后 THEN onDidInsert 回调触发（通知，无否决） | 正常 |
| AC-2.4 | WHEN 删除文本前 THEN onWillDelete 回调触发，返回 false 否决删除 | 正常 |
| AC-2.5 | WHEN 删除文本后 THEN onDidDelete 回调触发（通知） | 正常 |
| AC-2.6 | WHEN 文本变更前 THEN onWillChange 回调触发（在 onWillInsert/onWillDelete 之后、onDidInsert/onDidDelete 之前），返回 false 取消整个变更 | 正常 |

### US-3: 复制剪切粘贴事件

**作为** 应用开发者,
**我想要** 监听复制/剪切/粘贴操作并可否决,
**以便** 感知并可否决剪贴板操作。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 复制操作 THEN onCopy 回调触发（@since 8，通知，存于 SearchEventHub） | 正常 |
| AC-3.2 | WHEN 复制前 THEN onWillCopy 回调触发（@since 26），返回 false 否决复制 | 正常 |
| AC-3.3 | WHEN 剪切操作 THEN onCut 回调触发（@since 8，通知） | 正常 |
| AC-3.4 | WHEN 剪切前 THEN onWillCut 回调触发（@since 26），返回 false 否决剪切 | 正常 |
| AC-3.5 | WHEN 粘贴操作 THEN onPaste 回调触发（@since 8，OnPasteCallback，存于子 TextFieldEventHub） | 正常 |

### US-4: 选区滚动与编辑事件

**作为** 应用开发者,
**我想要** 监听选区变化、内容滚动、编辑态变化与 IME 绑定,
**以便** 全面感知搜索框交互状态变化。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 选区/光标位置变化 THEN onTextSelectionChange 回调触发（@since 10，存于子 TextFieldEventHub） | 正常 |
| AC-4.2 | WHEN 文本内容滚动 THEN onContentScroll 回调触发（@since 10） | 正常 |
| AC-4.3 | WHEN 编辑态（进入/退出）变化 THEN onEditChange 回调触发（@since 12，Callback<boolean>） | 正常 |
| AC-4.4 | WHEN 搜索框绑定输入法前 THEN onWillAttachIME 回调触发（@since 20，Callback<IMEClient>） | 正常 |
| AC-4.5 | WHEN onWillAttachIME 在 attributeModifier 中调用 THEN 不生效（SDK 注明不可在 attributeModifier 中调用） | 边界 |

### US-5: SearchController

**作为** 应用开发者,
**我想要** 通过 SearchController 编程控制光标、选区与编辑态,
**以便** 编程式控制光标位置、选区范围与编辑状态。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 `controller.caretPosition(5)`（@since 8） THEN 委托 SearchPattern::HandleCaretPosition→子 TextFieldPattern.SetCaretPosition(5) | 正常 |
| AC-5.2 | WHEN caretPosition < 0 THEN 定位至 0；> 长度 THEN 末尾 | 边界 |
| AC-5.3 | WHEN 调用 `controller.stopEditing()`（@since 10） THEN 委托 SearchPattern::StopEditing→子 TextFieldPattern.StopEditing() | 正常 |
| AC-5.4 | WHEN 调用 `controller.setTextSelection(0, 5)`（@since 12） THEN 直接继承 TextFieldController.SetTextSelection→子 TextFieldPattern.SetSelectionFlag | 正常 |
| AC-5.5 | WHEN Controller 方法调用 THEN 全部代理至子 TextFieldPattern（Controller 是薄代理，无独立状态） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-07 | UITest | search_pattern.cpp:845 FireOnSubmit |
| AC-1.2 | R-2 | TASK-07 | UITest | search_pattern.cpp:847 IsKeepEditable |
| AC-1.3 | R-2 | TASK-07 | UITest | 同上 |
| AC-1.4 | R-3 | TASK-07 | UITest | search_model_ng.h:68 no-op |
| AC-1.5 | R-1 | TASK-07 | UITest | search_event_hub.h:51 SEARCH_SUBMIT |
| AC-2.1 | R-4 | TASK-07 | UITest | search_model_ng.cpp:714 SetOnChange |
| AC-2.2 | R-5 | TASK-07 | UITest | search_model_ng.cpp:858 SetOnWillInsert |
| AC-2.3 | R-6 | TASK-07 | UITest | search_model_ng.cpp:867 SetOnDidInsert |
| AC-2.4 | R-5 | TASK-07 | UITest | search_model_ng.cpp:876 SetOnWillDelete |
| AC-2.5 | R-6 | TASK-07 | UITest | search_model_ng.cpp:885 SetOnDidDelete |
| AC-2.6 | R-5 | TASK-07 | UITest | search_model_ng.cpp:849 SetOnWillChange |
| AC-3.1 | R-7 | TASK-07 | UITest | search_model_ng.cpp:781 SetOnCopy |
| AC-3.2 | R-8 | TASK-07 | UITest | search_model_ng.cpp:772 SetOnWillCopy |
| AC-3.3 | R-7 | TASK-07 | UITest | search_model_ng.cpp:810 SetOnCut |
| AC-3.4 | R-8 | TASK-07 | UITest | search_model_ng.cpp:790 SetOnWillCut |
| AC-3.5 | R-7 | TASK-07 | UITest | search_model_ng.cpp:829 SetOnPasteWithEvent |
| AC-4.1 | R-9 | TASK-07 | UITest | search_model_ng.cpp:738 SetOnTextSelectionChange |
| AC-4.2 | R-9 | TASK-07 | UITest | search_model_ng.cpp:749 SetOnContentScroll |
| AC-4.3 | R-9 | TASK-07 | UITest | search_model_ng.cpp:636 SetOnEditChange |
| AC-4.4 | R-9 | TASK-07 | UITest | search_model_ng.cpp:2996 SetOnWillAttachIME |
| AC-4.5 | R-10 | TASK-07 | UITest | search.d.ts:1280 不可 attributeModifier |
| AC-5.1 | R-11 | TASK-07 | UITest | search_pattern.cpp:776 HandleCaretPosition |
| AC-5.2 | R-11 | TASK-07 | UITest | search.d.ts:55 边界 |
| AC-5.3 | R-12 | TASK-07 | UITest | search_pattern.cpp:821 StopEditing |
| AC-5.4 | R-13 | TASK-07 | UITest | text_field_controller.h:45 SetTextSelection |
| AC-5.5 | R-11 | TASK-07 | 源码检查 | search_pattern.cpp:713 InitSearchController |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|----------|----------|-----------|---------|
| R-1 | 行为 | 点击搜索按钮/图标/软键盘搜索 | OnClickButtonAndImage→FireOnSubmit(text, event)；记录 SEARCH_SUBMIT | onSubmit @since 14 存于 SearchEventHub | AC-1.1, AC-1.5 |
| R-2 | 行为 | onSubmit 回调调用 keepEditableState | IsKeepEditable()=true 不退出编辑；否则 StopEditing | @since 14 SubmitEvent 否决机制 | AC-1.2, AC-1.3 |
| R-3 | 边界 | onSubmit 使用 @since 8 Callback<string> | NG 管线下 no-op 空实现，不触发 | search_model_ng.h:68 | AC-1.4 |
| R-4 | 行为 | 文本内容变化 | onChange 回调触发（存于子 TextFieldEventHub）+ SearchEventHub.UpdateChangeEvent 同步 | @since 8 | AC-2.1 |
| R-5 | 行为 | 插入/删除/变更前 | onWillInsert/onWillDelete/onWillChange 回调触发，返回 false 否决 | 事件链：WillInsert→WillDelete→WillChange→apply→DidInsert→DidDelete | AC-2.2..AC-2.6 |
| R-6 | 行为 | 插入/删除后 | onDidInsert/onDidDelete 回调触发（通知，无否决） | — | AC-2.3, AC-2.5 |
| R-7 | 行为 | 复制/剪切/粘贴操作 | onCopy/onCut/onPaste 回调触发（通知） | onCopy/onCut 存于 SearchEventHub；onPaste 存于子 TextFieldEventHub | AC-3.1, AC-3.3, AC-3.5 |
| R-8 | 行为 | 复制/剪切前 | onWillCopy/onWillCut 回调触发，返回 false 否决 | @since 26 | AC-3.2, AC-3.4 |
| R-9 | 行为 | 选区变化/滚动/编辑态变化/IME 绑定 | onTextSelectionChange/onContentScroll/onEditChange/onWillAttachIME 回调触发 | 均存于子 TextFieldEventHub | AC-4.1..AC-4.4 |
| R-10 | 边界 | onWillAttachIME 在 attributeModifier 中调用 | 不生效 | SDK 注明 | AC-4.5 |
| R-11 | 行为 | controller.caretPosition(N) | 委托 HandleCaretPosition→子 TextFieldPattern.SetCaretPosition(N) | N<0→0；N>长度→末尾；Controller 薄代理无独立状态 | AC-5.1, AC-5.2, AC-5.5 |
| R-12 | 行为 | controller.stopEditing() | 委托 StopEditing→子 TextFieldPattern.StopEditing() | @since 10 | AC-5.3 |
| R-13 | 行为 | controller.setTextSelection(start, end) | 直接继承 TextFieldController.SetTextSelection→子 SetSelectionFlag | @since 12 | AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | US-1 提交事件 | UITest | 验证 FireOnSubmit；keepEditable 否决；@since 8 no-op |
| VM-2 | US-2 内容变更事件 | UITest | 验证事件链顺序；onWill* 否决；onDid* 通知 |
| VM-3 | US-3 复制剪切粘贴 | UITest | 验证 onWillCopy/onWillCut @since 26 否决 |
| VM-4 | US-4 选区滚动与编辑 | UITest | 验证 4 个事件委托子 TextFieldEventHub；onWillAttachIME 不可 attributeModifier |
| VM-5 | US-5 SearchController | UITest | 验证 Controller 薄代理；caretPosition 边界；setTextSelection 继承 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `onSubmit(callback: Callback<string>)` | Public | Callback<string> | SearchAttribute | 无 | 提交回调(@since 8, NG no-op) | AC-1.4 |
| `onSubmit(callback: SearchSubmitCallback)` | Public | SearchSubmitCallback(string, SubmitEvent) | SearchAttribute | 无 | 提交回调(@since 14, keepEditable) | AC-1.1..AC-1.3, AC-1.5 |
| `onChange(callback: EditableTextOnChangeCallback)` | Public | EditableTextOnChangeCallback | SearchAttribute | 无 | 内容变更 | AC-2.1 |
| `onWillChange(callback: Callback<EditableTextChangeValue, boolean>)` | Public | Callback<EditableTextChangeValue, boolean> | SearchAttribute | 无 | 变更否决(@since 15) | AC-2.6 |
| `onWillInsert/onDidInsert(callback)` | Public | Callback<InsertValue, boolean>/Callback<InsertValue> | SearchAttribute | 无 | 插入前/后(@since 12) | AC-2.2, AC-2.3 |
| `onWillDelete/onDidDelete(callback)` | Public | Callback<DeleteValue, boolean>/Callback<DeleteValue> | SearchAttribute | 无 | 删除前/后(@since 12) | AC-2.4, AC-2.5 |
| `onCopy(callback: Callback<string>)` | Public | Callback<string> | SearchAttribute | 无 | 复制(@since 8) | AC-3.1 |
| `onWillCopy(callback: Callback<string, boolean>)` | Public | Callback<string, boolean> | SearchAttribute | 无 | 复制否决(@since 26) | AC-3.2 |
| `onCut(callback: Callback<string>)` | Public | Callback<string> | SearchAttribute | 无 | 剪切(@since 8) | AC-3.3 |
| `onWillCut(callback: Callback<string, boolean>)` | Public | Callback<string, boolean> | SearchAttribute | 无 | 剪切否决(@since 26) | AC-3.4 |
| `onPaste(callback: OnPasteCallback)` | Public | OnPasteCallback | SearchAttribute | 无 | 粘贴(@since 8) | AC-3.5 |
| `onTextSelectionChange(callback)` | Public | OnTextSelectionChangeCallback | SearchAttribute | 无 | 选区变化(@since 10) | AC-4.1 |
| `onContentScroll(callback)` | Public | OnContentScrollCallback | SearchAttribute | 无 | 内容滚动(@since 10) | AC-4.2 |
| `onEditChange(callback: Callback<boolean>)` | Public | Callback<boolean> | SearchAttribute | 无 | 编辑态变化(@since 12) | AC-4.3 |
| `onWillAttachIME(callback: Callback<IMEClient>)` | Public | Callback<IMEClient> | SearchAttribute | 无 | IME 绑定前(@since 20) | AC-4.4 |
| `SearchController.caretPosition(value: number)` | Public | number | void | 无 | 光标位置(@since 8) | AC-5.1..AC-5.2 |
| `SearchController.stopEditing()` | Public | — | void | 无 | 停止编辑(@since 10) | AC-5.3 |
| `SearchController.setTextSelection(start, end, options?)` | Public | number, number, SelectionOptions? | void | 无 | 设置选区(@since 12) | AC-5.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| onSubmit @since 8 在 NG no-op | 变更 | NG 管线下 Callback<string> 不触发 | 应迁移至 @since 14 SearchSubmitCallback | AC-1.4 |
| onWillCopy/onWillCut @since 26 | 新增 | API < 26 不支持 | — | AC-3.2, AC-3.4 |

## 接口规格

> L2+ 复杂度。以下仅列代表性接口。

### 接口定义

**onSubmit(callback: SearchSubmitCallback)** — 双重载与 keepEditable 否决

| 属性 | 值 |
|------|-----|
| 函数签名 | `onSubmit(callback: SearchSubmitCallback): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1..AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | SearchSubmitCallback | 是 | — | (searchContent: string, event?: SubmitEvent) => void；event.keepEditableState() 保持编辑；存于 SearchEventHub |
| callback(@since 8) | Callback<string> | 是 | — | NG 管线下 no-op 空实现；仅非 NG 管线生效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 点击搜索按钮/图标/键盘搜索 | FireOnSubmit | AC-1.1 |
| 2 | keepEditableState() | 不退出编辑 | AC-1.2 |
| 3 | 未调用 keepEditableState | StopEditing | AC-1.3 |
| 4 | @since 8 Callback<string> | NG no-op | AC-1.4 |

---

**onWillChange(callback)** — 事件链否决

| 属性 | 值 |
|------|-----|
| 函数签名 | `onWillChange(callback: Callback<EditableTextChangeValue, boolean>): SearchAttribute` |
| 返回值 | `SearchAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback<EditableTextChangeValue, boolean> | 是 | — | 返回 false 取消变更；在 onWillInsert/onWillDelete 之后、onDidInsert/onDidDelete 之前触发 |

## 兼容性声明

- **已有 API 行为变更:** 是。onSubmit @since 8 在 NG 管线下 no-op（应迁移至 @since 14）；17 事件跨 API 8-26 引入；onWill* 返回 bool 否决，onDid* 通知；事件链顺序固定；onWillAttachIME 不可在 attributeModifier 中调用；SearchController 薄代理子 TextFieldPattern。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（onSubmit/onChange/onCopy/onCut/onPaste/caretPosition）
- **API 版本号策略:** @since 8/10/12/14/15/20/26 分批标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 事件存储分裂 | 17 事件中仅 onSubmit(@since 14) 存于 SearchEventHub，其余 15 个委托子 TextFieldEventHub；onChange 额外包装调用 UpdateChangeEvent | 全部 AC |
| onSubmit 双重载 | @since 8 Callback<string> NG no-op；@since 14 SearchSubmitCallback 携带 keepEditableState 否决 | AC-1.4 |
| 事件链否决 | onWillInsert→onWillDelete→onWillChange→apply→onDidInsert→onDidDelete；onWill* 返回 bool false 否决，onDid* 通知 | AC-2.2..AC-2.6 |
| Controller 薄代理 | SearchController 是子 TextFieldController 代理，经 InitSearchController Handle* 方法转发；setTextSelection 直接继承；无独立状态 | AC-5.1..AC-5.5 |
| onWillAttachIME 限制 | 不可在 attributeModifier 中调用 | AC-4.5 |
| onCopy/onCut 存于 SearchEventHub | 不同于其他事件存于子 TextFieldEventHub | AC-3.1, AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 事件回调在 UI 线程同步触发；onWill* 否决需在变更前完成 | UITest | text_field_event_hub.h FireOn* |
| 可测试性 | onSubmit 经 SearchEventHub.FireOnSubmit；onChange 经 UpdateChangeEvent 同步 NodeDataCache | Inspector dump | search_event_hub.h:45/:27-47 |
| 可靠性 | Controller Handle* 方法经 weak claim 防悬空 | 源码检查 | search_pattern.cpp:715 WeakClaim |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 全部事件+Controller 支持 | — | UITest | — |
| 平板/折叠屏 | 同手机 | 无差异 | UITest | — |
| 穿戴 | 同手机 | 无差异 | UITest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Controller.caretPosition/setTextSelection 经无障碍路径调用；onClickButtonAndImage 触发无障碍 REQUEST_FOCUS | AC-5.1, AC-5.4 |
| 大字体 | 否 | 不直接涉及 | — |
| 深色模式 | 否 | 不影响 | — |
| 多窗口/分屏 | 否 | 无特殊行为 | — |
| 多用户 | 否 | 无特殊行为 | — |
| 版本升级 | 是 | 17 事件+Controller 跨 API 8-26 引入；onSubmit @since 8 NG no-op 需迁移 | 全部 AC |
| 生态兼容 | 是 | 动态+静态+C-API 全覆盖；onSubmit 双重载双绑定路径 | 全部 AC |

## 行为场景（Gherkin）

```gherkin
Feature: Search 事件回调与控制器
  作为应用开发者
  我想要监听搜索框的各类事件并控制编辑态
  以便提供完整的搜索交互

  Scenario: onSubmit keepEditable 否决
    Given Search 组件已创建且 onSubmit 使用 @since 14 SearchSubmitCallback
    When 用户点击搜索按钮
    Then FireOnSubmit 触发
    When 回调调用 event.keepEditableState()
    Then 搜索框保持编辑态（不退出）
    When 回调未调用 keepEditableState()
    Then 搜索框退出编辑态(StopEditing)

  Scenario: onSubmit @since 8 no-op
    Given Search 组件已创建且 onSubmit 使用 @since 8 Callback<string>
    When NG 管线下点击搜索按钮
    Then onSubmit 不触发（NG no-op 空实现）

  Scenario Outline: 事件链否决
    Given Search 组件已创建
    When 插入文本且 onWillInsert 返回 <insertVeto>
    And onWillChange 返回 <changeVeto>
    Then 插入 <result>

    Examples:
      | insertVeto | changeVeto | result |
      | true | true | 允许插入 |
      | false | true | 否决插入 |
      | true | false | 否决变更 |

  Scenario: SearchController 薄代理
    Given Search 组件已创建
    When 调用 controller.caretPosition(5)
    Then 委托 SearchPattern.HandleCaretPosition
    And 转发至子 TextFieldPattern.SetCaretPosition(5)
    When 调用 controller.setTextSelection(0, 3)
    Then 直接继承 TextFieldController.SetTextSelection（不经 Handle* 包装）
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
    query: "17 事件中仅 onSubmit 存于 SearchEventHub 其余委托子 TextFieldEventHub 的存储分裂"
  - repo: "openharmony/arkui_ace_engine"
    query: "onSubmit @since 8 Callback<string> 在 NG 管线下 no-op 空实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "onWillInsert→onWillDelete→onWillChange→onDidInsert→onDidDelete 事件链与 bool 否决"
  - repo: "openharmony/arkui_ace_engine"
    query: "SearchController 经 InitSearchController Handle* 方法代理子 TextFieldPattern 的薄代理架构"
  - repo: "openharmony/interface_sdk-js"
    query: "search.d.ts 中 17 事件与 SearchController 的 @since/回调类型/双重载"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/search.d.ts`；`frameworks/core/components_ng/pattern/search/search_event_hub.h`；`search_pattern.cpp`；`design.md`(DESIGN-Func-05-09-03)
