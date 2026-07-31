# 特性规格

> Func-05-09-05-Feat-06 编辑事件回调：固化 onChange、onEditChange、onWillChange、onWillInsert、onDidInsert、onWillDelete、onDidDelete 七个编辑生命周期回调的行为规格，包括回调触发顺序、拦截机制与预览文本交互。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 编辑事件回调 (Editing Events & Change Callbacks) |
| 特性编号 | Func-05-09-05-Feat-06 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 @since 7（onChange）、@since 10（onEditChange/onTextSelectionChange/onContentScroll）、@since 12（onWillInsert/onDidInsert/onWillDelete/onDidDelete/EditableTextOnChangeCallback）、@since 15（onWillChange/EditableTextChangeValue）；静态 @since 23 static |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onChange（EditableTextOnChangeCallback） | 布局后延迟触发，含 previewText，去重 |
| ADDED | onEditChange（isEditing boolean） | 焦点变化触发，去重 |
| ADDED | onWillChange（Callback<EditableTextChangeValue,boolean>） | @since 15；返回 false 回滚已应用的变更 |
| ADDED | onWillInsert/onDidInsert（@since 12） | 仅系统输入法；Will 返回 false 取消 |
| ADDED | onWillDelete/onDidDelete（@since 12） | 仅系统输入法；Will 返回 false 取消 |
| ADDED | 回调管道顺序 | 插入：WillInsert→WillChange→DidInsert→onChange；删除：WillDelete→WillChange→DidDelete→onChange；替换：WillInsert→WillDelete→WillChange→DidDelete→DidInsert→onChange |
| ADDED | 预览文本不触发 Will/Did 四回调 | 预览走独立操作队列，仅触发 WillChange/onChange |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/05-text-area/design.md` | Baselined |

---

## 用户故事

### US-1: 监听文本变更（onChange）

**作为** 应用开发者,
**我想要** 通过 onChange 监听文本内容变化,
**以便** 实时获取用户输入内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.onChange(callback)` THEN 注册 onChange_（EditableTextOnChangeCallback）（`text_field_model_ng.cpp:660`） | 正常 |
| AC-1.2 | WHEN 文本变更经布局后 THEN AddTextFireOnChange 延迟任务构建 ChangeValueInfo（value+previewText+rangeBefore+rangeAfter+oldContent）并 FireOnChange（`text_field_pattern.cpp:4749-4784`） | 正常 |
| AC-1.3 | WHEN 回调参数 THEN 接收 value（变更后内容）、previewText?（预览文本）、options?（TextChangeOptions 含 rangeBefore/rangeAfter/oldContent/oldPreviewText）（`text_area_static_modifier.cpp:275-281`） | 正常 |
| AC-1.4 | WHEN value 与 previewText 均与上次相同 THEN FireOnChange 去重不触发（`text_field_event_hub.h:199-201`） | 边界 |
| AC-1.5 | WHEN 仅 previewText 变化（value 不变） THEN 仍触发（previewText 不同）（`text_field_event_hub.h:199`） | 边界 |

### US-2: 监听编辑状态变化（onEditChange）

**作为** 应用开发者,
**我想要** 通过 onEditChange 监听编辑状态变化,
**以便** 响应进入/退出编辑的事件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.onEditChange(callback)` THEN 注册 onEditChanged_（`text_field_model_ng.cpp:2417`） | 正常 |
| AC-2.2 | WHEN 组件获焦/IME attach THEN NotifyOnEditChanged(true)（`text_field_pattern.cpp:1673`） | 正常 |
| AC-2.3 | WHEN 组件失焦 THEN NotifyOnEditChanged(false)（`text_field_pattern.cpp:2033`） | 正常 |
| AC-2.4 | WHEN isChanged==isEdit_（状态未变） THEN 去重不触发（`text_field_pattern.cpp:10377`） | 边界 |

### US-3: 拦截文本变更（onWillChange，@since 15）

**作为** 应用开发者,
**我想要** 通过 onWillChange 拦截文本变更,
**以便** 在内容提交前进行校验或修改。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.onWillChange(callback)` (@since 15) THEN 注册 onWillChangeEvent_（`text_field_model_ng.cpp:962`） | 正常 |
| AC-3.2 | WHEN 插入/删除/编程式 setText 前 THEN OnWillChangePreInsert/PreDelete/PreSetValue 构建 ChangeValueInfo 并 FireOnWillChangeEvent（`text_field_pattern.cpp:12777,12806,12833`） | 正常 |
| AC-3.3 | WHEN 回调返回 false THEN RecoverTextValueAndCaret 回滚已应用变更（插入路径）或 SetTextValue 回滚（删除路径）（`text_field_pattern.cpp:6587-6602,7924`） | 边界 |
| AC-3.4 | WHEN 回调返回 true 或未注册 THEN 变更继续（默认允许）（`text_field_event_hub.h:398`） | 正常 |
| AC-3.5 | WHEN 预览文本提交 THEN FireOnWillChange 触发（triggerOnWillChange=true 时）；返回 false 则 SetTextValueOnly 回滚（`text_field_pattern.cpp:11530-11535`） | 正常 |

### US-4: 拦截与通知插入（onWillInsert/onDidInsert，@since 12）

**作为** 应用开发者,
**我想要** 通过 onWillInsert/onDidInsert 拦截与通知文本插入,
**以便** 控制插入内容并感知插入完成。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.onWillInsert(callback)` (@since 12) THEN 注册 onWillInsertValueEvent_（`text_field_model_ng.cpp:2595`） | 正常 |
| AC-4.2 | WHEN IME/AutoFill 插入前 THEN BeforeIMEInsertValue 构建 InsertValueInfo{insertOffset(预插入偏移), insertValue} 并 FireOnWillInsertValueEvent（`text_field_pattern.cpp:6404-6413`） | 正常 |
| AC-4.3 | WHEN 回调返回 false THEN ExecuteInsertValueCommand 早退 return（不插入，不触发后续回调）（`text_field_pattern.cpp:6560,6567`） | 边界 |
| AC-4.4 | WHEN 编程式（非 IME）插入 THEN 不触发 onWillInsert（isIMEOrAutoFill=false 跳过 BeforeIMEInsertValue）（`text_field_pattern.cpp:6560`） | 边界 |
| AC-4.5 | WHEN 调用 `.onDidInsert(callback)` (@since 12) THEN 注册 onDidInsertValueEvent_（`text_field_model_ng.cpp:2602`） | 正常 |
| AC-4.6 | WHEN IME/AutoFill 插入后 THEN AfterIMEInsertValue 构建 InsertValueInfo{insertOffset(后插入光标), insertValue} 并 FireOnDidInsertValueEvent（`text_field_pattern.cpp:6431-6442`） | 正常 |
| AC-4.7 | WHEN onWillInsert 返回 false THEN onDidInsert 不触发（插入被取消） | 边界 |

### US-5: 拦截与通知删除（onWillDelete/onDidDelete，@since 12）

**作为** 应用开发者,
**我想要** 通过 onWillDelete/onDidDelete 拦截与通知文本删除,
**以便** 控制删除操作并感知删除完成。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.onWillDelete(callback)` (@since 12) THEN 注册 onWillDeleteEvent_（`text_field_model_ng.cpp:2609`） | 正常 |
| AC-5.2 | WHEN IME 删除前 THEN BeforeIMEDeleteValue 构建 DeleteValueInfo{deleteOffset, direction, deleteValue} 并 FireOnWillDeleteEvent（`text_field_pattern.cpp:8001-8013`） | 正常 |
| AC-5.3 | WHEN 回调返回 false THEN CHECK_NULL_VOID(isDelete) return 或 end=isDelete?end:start 折叠范围（`text_field_pattern.cpp:7919`） | 边界 |
| AC-5.4 | WHEN 调用 `.onDidDelete(callback)` (@since 12) THEN 注册 onDidDeleteEvent_（`text_field_model_ng.cpp:2616`） | 正常 |
| AC-5.5 | WHEN IME 删除后 THEN AfterIMEDeleteValue 构建 DeleteValueInfo{deleteOffset(后删除光标), direction, deleteValue} 并 FireOnDidDeleteValueEvent（`text_field_pattern.cpp:8031-8042`） | 正常 |
| AC-5.6 | WHEN onWillDelete 返回 false THEN onDidDelete 不触发（删除被取消） | 边界 |

### US-6: 回调管道顺序

**作为** 应用开发者,
**我想要** 了解插入/删除/替换场景下各编辑回调的触发顺序,
**以便** 正确处理多个回调的协同与回滚逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN IME 插入（无选区） THEN 顺序：onWillInsert → onWillChange → onDidInsert → onChange（`text_field_pattern.cpp:6560,6598,6612`） | 正常 |
| AC-6.2 | WHEN IME 删除 THEN 顺序：onWillDelete → onWillChange → onDidDelete → onChange（`text_field_pattern.cpp:7918,7922,7931`） | 正常 |
| AC-6.3 | WHEN IME 插入替换选区 THEN 顺序：onWillInsert → onWillDelete → onWillChange → onDidDelete → onDidInsert → onChange（`text_field_pattern.cpp:6560,6579,6585,6592,6612`） | 正常 |
| AC-6.4 | WHEN onWillChange 文档约束 THEN onWillChange 在 onWillInsert/onWillDelete 之后、onDidInsert/onDidDelete 之前触发（SDK NOTE）（`text_area.d.ts:1400-1401`） | 正常 |

### US-7: 预览文本与回调交互

**作为** 应用开发者,
**我想要** 了解预览文本模式下编辑回调的触发差异,
**以便** 正确处理预览期间的输入与光标逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 预览文本中 THEN 不触发 onWillInsert/onDidInsert/onWillDelete/onDidDelete（预览走独立操作队列 SET_PREVIEW_TEXT/SET_PREVIEW_FINISH）（`text_field_pattern.cpp:900-906`） | 边界 |
| AC-7.2 | WHEN 预览文本提交 THEN 仅触发 onWillChange（triggerOnWillChange=true 时）+ onChange（`text_field_pattern.cpp:11530,4749`） | 正常 |
| AC-7.3 | WHEN onChange 接收 previewText 参数 THEN 开发者需基于 previewText 调整光标逻辑（SDK NOTE）（`text_area.d.ts:573-575`） | 正常 |
| AC-7.4 | WHEN enablePreviewText=false THEN IME 不发送预览文本，Will/Did 四回调正常触发 | 边界 |

### US-8: 系统输入法限制

**作为** 应用开发者,
**我想要** 了解 Will/Did 四回调仅对系统输入法触发,
**以便** 明确回调适用范围与第三方输入法差异。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN onWillInsert/onDidInsert/onWillDelete/onDidDelete 仅在 isIMEOrAutoFill=true 时触发 THEN 系统输入法/AutoFill 触发（`text_field_pattern.cpp:6533,6560`） | 正常 |
| AC-8.2 | WHEN 编程式 InsertValue(isIME=false) THEN 不触发四回调 | 边界 |
| AC-8.3 | WHEN 非系统输入法 THEN 不触发四回调（SDK NOTE "available only for system input methods"） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-5 | TASK-06 | XTS onChange | text_field_pattern.cpp:4749 |
| AC-2.1~2.4 | R-6~R-9 | TASK-06 | XTS onEditChange | text_field_pattern.cpp:10371 |
| AC-3.1~3.5 | R-10~R-14 | TASK-06 | XTS onWillChange | text_field_pattern.cpp:12777 |
| AC-4.1~4.7 | R-15~R-21 | TASK-06 | XTS onWillInsert/onDidInsert | text_field_pattern.cpp:6404 |
| AC-5.1~5.6 | R-22~R-27 | TASK-06 | XTS onWillDelete/onDidDelete | text_field_pattern.cpp:8001 |
| AC-6.1~6.4 | R-28~R-31 | TASK-06 | XTS 管道顺序 | text_field_pattern.cpp:6530-6614 |
| AC-7.1~7.4 | R-32~R-35 | TASK-06 | XTS 预览交互 | text_field_pattern.cpp:900-906 |
| AC-8.1~8.3 | R-36~R-38 | TASK-06 | XTS 系统输入法限制 | text_field_pattern.cpp:6533 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 onChange | 注册 onChange_ | — | AC-1.1 |
| R-2 | 行为 | 文本变更后布局完成 | AddTextFireOnChange 延迟 FireOnChange | 布局后延迟 | AC-1.2 |
| R-3 | 行为 | onChange 参数 | value+previewText+options | — | AC-1.3 |
| R-4 | 边界 | value+previewText 均未变 | 去重不触发 | — | AC-1.4 |
| R-5 | 边界 | 仅 previewText 变 | 仍触发 | — | AC-1.5 |
| R-6 | 行为 | 设置 onEditChange | 注册 onEditChanged_ | — | AC-2.1 |
| R-7 | 行为 | 获焦/IME attach | NotifyOnEditChanged(true) | — | AC-2.2 |
| R-8 | 行为 | 失焦 | NotifyOnEditChanged(false) | — | AC-2.3 |
| R-9 | 边界 | 状态未变 | 去重 | — | AC-2.4 |
| R-10 | 行为 | 设置 onWillChange(@since 15) | 注册 onWillChangeEvent_ | — | AC-3.1 |
| R-11 | 行为 | 插入/删除/setText 前 | FireOnWillChangeEvent | — | AC-3.2 |
| R-12 | 边界 | 返回 false | RecoverTextValueAndCaret/SetTextValue 回滚 | — | AC-3.3 |
| R-13 | 行为 | 返回 true/未注册 | 变更继续 | 默认允许 | AC-3.4 |
| R-14 | 行为 | 预览提交 | FireOnWillChange(triggerOnWillChange=true) | — | AC-3.5 |
| R-15 | 行为 | 设置 onWillInsert(@since 12) | 注册 onWillInsertValueEvent_ | — | AC-4.1 |
| R-16 | 行为 | IME/AutoFill 插入前 | BeforeIMEInsertValue：insertOffset(预)+insertValue | — | AC-4.2 |
| R-17 | 边界 | 返回 false | 早退 return | — | AC-4.3 |
| R-18 | 边界 | 编程式插入 | 不触发（isIMEOrAutoFill=false） | — | AC-4.4 |
| R-19 | 行为 | 设置 onDidInsert(@since 12) | 注册 onDidInsertValueEvent_ | — | AC-4.5 |
| R-20 | 行为 | IME/AutoFill 插入后 | AfterIMEInsertValue：insertOffset(后)+insertValue | — | AC-4.6 |
| R-21 | 边界 | WillInsert false | DidInsert 不触发 | — | AC-4.7 |
| R-22 | 行为 | 设置 onWillDelete(@since 12) | 注册 onWillDeleteEvent_ | — | AC-5.1 |
| R-23 | 行为 | IME 删除前 | BeforeIMEDeleteValue：deleteOffset+direction+deleteValue | — | AC-5.2 |
| R-24 | 边界 | 返回 false | CHECK_NULL_VOID return/折叠范围 | — | AC-5.3 |
| R-25 | 行为 | 设置 onDidDelete(@since 12) | 注册 onDidDeleteEvent_ | — | AC-5.4 |
| R-26 | 行为 | IME 删除后 | AfterIMEDeleteValue：deleteOffset(后)+direction+deleteValue | — | AC-5.5 |
| R-27 | 边界 | WillDelete false | DidDelete 不触发 | — | AC-5.6 |
| R-28 | 行为 | IME 插入(无选区) | WillInsert→WillChange→DidInsert→onChange | — | AC-6.1 |
| R-29 | 行为 | IME 删除 | WillDelete→WillChange→DidDelete→onChange | — | AC-6.2 |
| R-30 | 行为 | IME 插入替换选区 | WillInsert→WillDelete→WillChange→DidDelete→DidInsert→onChange | — | AC-6.3 |
| R-31 | 行为 | SDK 约束 | WillChange 在 Will* 之后 Did* 之前 | SDK NOTE | AC-6.4 |
| R-32 | 边界 | 预览文本中 | 不触发 Will/Did 四回调 | 独立操作队列 | AC-7.1 |
| R-33 | 行为 | 预览提交 | 仅 WillChange+onChange | — | AC-7.2 |
| R-34 | 行为 | onChange previewText | 开发者需调整光标逻辑 | SDK NOTE | AC-7.3 |
| R-35 | 边界 | enablePreviewText=false | Will/Did 正常触发 | — | AC-7.4 |
| R-36 | 行为 | 四回调仅 IME/AutoFill | isIMEOrAutoFill=true | — | AC-8.1 |
| R-37 | 边界 | 编程式插入 | 不触发 | — | AC-8.2 |
| R-38 | 边界 | 非系统输入法 | 不触发 | SDK NOTE | AC-8.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.x onChange | XTS + 事件 | 布局后延迟；previewText 携带；去重 |
| VM-2 | AC-2.x onEditChange | XTS + 焦点 | 焦点变化触发；去重 |
| VM-3 | AC-3.x onWillChange | XTS + 拦截 | 返回 false 回滚 |
| VM-4 | AC-4.x onWillInsert/onDidInsert | XTS + IME | 仅系统输入法；返回 false 取消 |
| VM-5 | AC-5.x onWillDelete/onDidDelete | XTS + IME | 仅系统输入法；返回 false 取消 |
| VM-6 | AC-6.x 管道顺序 | XTS + 序列 | 插入/删除/替换顺序 |
| VM-7 | AC-7.x 预览交互 | XTS + 预览 | 预览不触发 Will/Did |
| VM-8 | AC-8.x 系统输入法限制 | XTS + IME | isIMEOrAutoFill 门控 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| onChange(callback) | Public | EditableTextOnChangeCallback | this | 无 | 文本变更通知 | AC-1.x |
| onEditChange(callback) | Public | function(boolean) | this | 无 | 编辑状态变化 | AC-2.x |
| onWillChange(callback) | Public | Callback<EditableTextChangeValue,boolean> | this | 无 | 变更前拦截 | AC-3.x |
| onWillInsert(callback) | Public | Callback<InsertValue,boolean> | this | 无 | 插入前拦截 | AC-4.x |
| onDidInsert(callback) | Public | Callback<InsertValue> | this | 无 | 插入后通知 | AC-4.5 |
| onWillDelete(callback) | Public | Callback<DeleteValue,boolean> | this | 无 | 删除前拦截 | AC-5.x |
| onDidDelete(callback) | Public | Callback<DeleteValue> | this | 无 | 删除后通知 | AC-5.4 |

> **SDK 交叉验证：** 值类型 InsertValue/DeleteValue/EditableTextChangeValue/TextChangeOptions 经 `text_common.d.ts` 核对（@since 12/15）。回调签名经 `textArea.static.d.ets` / `text_area.d.ts` 核对。

## 接口规格

### 接口定义

| 接口 | 签名概要 | 开放范围 | 关联 AC |
|------|----------|----------|---------|
| 变更通知 | onChange | Public | AC-1.x |
| 编辑状态 | onEditChange | Public | AC-2.x |
| 变更拦截 | onWillChange | Public | AC-3.x |
| 插入拦截/通知 | onWillInsert/onDidInsert | Public | AC-4.x |
| 删除拦截/通知 | onWillDelete/onDidDelete | Public | AC-5.x |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| onChange | EditableTextOnChangeCallback | 是 | 无 | (value, previewText?, options?) |
| onWillChange | Callback<EditableTextChangeValue,boolean> | 是 | 无 | 返回 false 回滚 |
| onWillInsert | Callback<InsertValue,boolean> | 是 | 无 | 返回 false 取消；仅系统输入法 |
| onWillDelete | Callback<DeleteValue,boolean> | 是 | 无 | 返回 false 取消；仅系统输入法 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | IME 插入(无选区) | WillInsert→WillChange→DidInsert→onChange | AC-6.1 |
| 2 | IME 删除 | WillDelete→WillChange→DidDelete→onChange | AC-6.2 |
| 3 | IME 插入替换选区 | WillInsert→WillDelete→WillChange→DidDelete→DidInsert→onChange | AC-6.3 |
| 4 | 预览文本 | 仅 WillChange+onChange | AC-7.1,7.2 |
| 5 | WillInsert 返回 false | 早退不插入 | AC-4.3 |
| 6 | WillDelete 返回 false | 折叠范围/return | AC-5.3 |
| 7 | WillChange 返回 false | RecoverTextValueAndCaret 回滚 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 是。onChange @since 7 升级为 EditableTextOnChangeCallback @since 12（增加 previewText/options 参数）。onWillChange @since 15 新增。onWillInsert/onDidInsert/onWillDelete/onDidDelete @since 12 新增，仅系统输入法触发。预览文本不触发 Will/Did 四回调。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 @since 7（onChange）/10（onEditChange）/12（Will/Did 四回调）/15（onWillChange）；静态 @since 23 static
- **API 版本号策略:** 同前

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 布局后延迟触发 | onChange 经 AddTextFireOnChange 延迟到布局后 | AC-1.2 |
| 去重 | onChange 按 value+previewText 去重；onEditChange 按 isEdit_ 去重 | AC-1.4,2.4 |
| isIMEOrAutoFill 门控 | Will/Did 四回调仅 IME/AutoFill 触发 | AC-4.4,8.x |
| 预览独立操作队列 | SET_PREVIEW_TEXT/SET_PREVIEW_FINISH 绕过 ExecuteInsertValueCommand | AC-7.1 |
| 回滚机制 | WillChange false → RecoverTextValueAndCaret/SetTextValue | AC-3.3 |
| 管道顺序约束 | SDK 约定 WillChange 在 Will* 之后 Did* 之前 | AC-6.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | onChange 布局后延迟触发避免冗余 | 单测 | text_field_pattern.cpp:4749 |
| 可靠性 | 去重机制避免重复回调 | 单测 | text_field_event_hub.h:199 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | onEditChange 影响无障碍编辑状态通知 | AC-2.x |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | onChange @since 7→12 升级；Will/Did 四回调 @since 12；onWillChange @since 15 | AC-1.1,4.1,3.1 |
| 生态兼容 | 是 | Will/Did 四回调仅系统输入法触发，第三方输入法不触发 | AC-8.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextArea 编辑事件回调
  作为 应用开发者
  我想要 监听/拦截文本插入、删除、变更与编辑状态
  以便 实现输入校验、格式化与状态同步

  Scenario Outline: 回调管道顺序
    Given 注册全部回调
    When <操作>
    Then 回调顺序为 <顺序>

    Examples:
      | 操作 | 顺序 |
      | IME 插入(无选区) | WillInsert→WillChange→DidInsert→onChange |
      | IME 删除 | WillDelete→WillChange→DidDelete→onChange |
      | IME 插入替换选区 | WillInsert→WillDelete→WillChange→DidDelete→DidInsert→onChange |

  Scenario: onWillInsert 返回 false 取消插入
    Given 注册 .onWillInsert((value) => false)
    When IME 插入文本
    Then BeforeIMEInsertValue 返回 false
    And ExecuteInsertValueCommand 早退 return
    And 不插入文本，不触发 WillChange/DidInsert/onChange

  Scenario: 预览文本不触发 Will/Did 四回调
    Given 设置 .enablePreviewText(true) 且注册 onWillInsert/onDidInsert
    When IME 发送预览文本
    Then 预览走 SET_PREVIEW_TEXT 操作队列
    And onWillInsert/onDidInsert/onWillDelete/onDidDelete 不触发
    When 预览结束提交
    Then 仅 onWillChange/onChange 触发

  Scenario: onChange 携带 previewText
    Given 注册 .onChange 且预览文本模式启用
    When IME 发送预览文本"abc"
    Then onChange 回调接收 value（不含预览）+ previewText{offset,value:"abc"}
    And 开发者需基于 previewText 调整光标逻辑
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
    query: "onChange 为何布局后延迟触发（AddTextFireOnChange）"
  - repo: "openharmony/arkui_ace_engine"
    query: "onWillChange 返回 false 的 RecoverTextValueAndCaret 回滚机制"
  - repo: "openharmony/arkui_ace_engine"
    query: "预览文本为何走独立操作队列不触发 Will/Did 四回调"
  - repo: "openharmony/arkui_ace_engine"
    query: "isIMEOrAutoFill 门控为何限制 Will/Did 四回调仅系统输入法"
  - repo: "openharmony/arkui_ace_engine"
    query: "IME 插入替换选区时 WillDelete 在 WillChange 之前触发的管道顺序"
```

**关键文档：** `specs/05-ui-components/09-text-components/05-text-area/design.md`（DESIGN-Func-05-09-05）；SDK `textArea.static.d.ets` / `text_area.d.ts` / `text_common.d.ts`
