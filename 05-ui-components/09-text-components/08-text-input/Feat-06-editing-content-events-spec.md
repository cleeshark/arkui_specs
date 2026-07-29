# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 编辑与内容事件回调 |
| 特性编号 | Func-05-09-08-Feat-06 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_event_hub.h`、`text_field_model_ng.h`（SetOnChange/SetOnWillChangeEvent/SetOnSubmit/SetOnWillInsertValueEvent/SetOnDidInsertValueEvent/SetOnWillDeleteEvent/SetOnDidDeleteEvent/SetOnWillCopy/SetOnCopy/SetOnWillCut/SetOnCut/SetOnPaste/SetOnSecurityStateChange）

## 用户故事

### US-1: 内容变更事件
作为开发者，我希望监听 onChange/onWillChange/onChangeWithPreviewText。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 文本变更 THEN `onChange(callback)` 回调（@since 7/12） | 正常 |
| AC-1.2 | WHEN `onWillChange(callback)` 返回 false（@since 15/20）THEN 拦截变更 | 正常 |
| AC-1.3 | WHEN 预览文本变更 THEN `onChangeWithPreviewText`（C-API @since 16） | 正常 |

### US-2: 提交/编辑态
作为开发者，我希望监听 onSubmit/onEditChange。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 按回车提交 THEN `onSubmit(OnSubmitCallback)`（@since 7/18）回调含 EnterKeyType+SubmitEvent | 正常 |
| AC-2.2 | WHEN 编辑态切换 THEN `onEditChange(Callback<boolean>)`（@since 8/18） | 正常 |
| AC-2.3 | WHEN `onEditChanged`（@deprecated since 8）THEN 仍兼容旧回调 | 边界 |

### US-3: 插入/删除 will/did
作为开发者，我希望经 onWillInsert/onDidInsert/onWillDelete/onDidDelete 拦截/通知。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `onWillInsert` 返回 false（@since 12）THEN 拦截插入 | 正常 |
| AC-3.2 | WHEN 插入完成 THEN `onDidInsert`（@since 12）通知 InsertValue | 正常 |
| AC-3.3 | WHEN `onWillDelete` 返回 false（@since 12）THEN 拦截删除 | 正常 |
| AC-3.4 | WHEN 删除完成 THEN `onDidDelete`（@since 12）通知 DeleteValue | 正常 |

### US-4: 复制/剪切/粘贴
作为开发者，我希望监听 onCopy/onWillCopy/onCut/onWillCut/onPaste。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 复制 THEN `onCopy(Callback<string>)`（@since 8/18） | 正常 |
| AC-4.2 | WHEN `onWillCopy`（C-API @since 26）THEN 可拦截 | 正常 |
| AC-4.3 | WHEN 剪切 THEN `onCut`（@since 8/18）/`onWillCut`（@since 26） | 正常 |
| AC-4.4 | WHEN 粘贴 THEN `onPaste(OnPasteCallback)`（@since 8/18，C-API @since 26） | 正常 |

### US-5: 安全态
作为开发者，我希望监听密码可见态切换。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 密码可见切换 THEN `onSecurityStateChange(Callback<boolean>)`（@since 12） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-06 | 单测 | text_field_model_ng.h:74 |
| AC-1.2 | R-2 | TASK-TI-06 | 单测 | text_field_model_ng.h:75 |
| AC-1.3 | R-1 | TASK-TI-06 | C-API 单测 | native_node.h:10975 |
| AC-2.1 | R-3 | TASK-TI-06 | 单测 | text_field_model_ng.h:72 |
| AC-2.2 | R-3 | TASK-TI-06 | 单测 | text_field_model_ng.h SetOnEditChange |
| AC-2.3 | R-4 | TASK-TI-06 | 单测 | text_input.d.ts onEditChanged deprecated |
| AC-3.1 | R-5 | TASK-TI-06 | 单测 | text_field_model_ng.h:154 |
| AC-3.2 | R-5 | TASK-TI-06 | 单测 | text_field_model_ng.h:155 |
| AC-3.3 | R-5 | TASK-TI-06 | 单测 | text_field_model_ng.h:156 |
| AC-3.4 | R-5 | TASK-TI-06 | 单测 | text_field_model_ng.h:157 |
| AC-4.1 | R-6 | TASK-TI-06 | 单测 | text_field_model_ng.h:79–80 |
| AC-4.2 | R-6 | TASK-TI-06 | C-API 单测 | native_node.h:11013 |
| AC-4.3 | R-6 | TASK-TI-06 | 单测 | text_field_model_ng.h:82–83 |
| AC-4.4 | R-6 | TASK-TI-06 | 单测/C-API | text_field_model_ng.h:84, native_node.h:10849 |
| AC-5.1 | R-7 | TASK-TI-06 | 单测 | text_field_model_ng.h:77 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | onChange/onChangeWithPreviewText | 回调内容（@since 7/12/16） | — | AC-1.1,1.3 |
| R-2 | 行为 | onWillChange 返回 bool（@since 15/20） | false 拦截变更 | — | AC-1.2 |
| R-3 | 行为 | onSubmit/onEditChange | 回调提交/编辑态（@since 7/8/18） | onEditChanged @deprecated since 8 | AC-2.1,2.2 |
| R-4 | 边界 | onEditChanged（@deprecated since 8） | 兼容旧回调 | 改用 onEditChange | AC-2.3 |
| R-5 | 行为 | onWillInsert/onDidInsert/onWillDelete/onDidDelete（@since 12） | will 拦截/did 通知 InsertValue/DeleteValue | will 返回 bool | AC-3.1..3.4 |
| R-6 | 行为 | onCopy/onWillCopy/onCut/onWillCut/onPaste | 回调/拦截（@since 8/18，C-API @since 26） | will 可拦截 | AC-4.1..4.4 |
| R-7 | 行为 | onSecurityStateChange（@since 12） | 密码可见态回调 | bool | AC-5.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 内容事件 | 单测 | will 拦截 |
| VM-2 | R-5 插入/删除 | 单测 | will/did |
| VM-3 | R-6 复制粘贴 | 单测+C-API 单测 | @since 26 will |
| VM-4 | R-7 安全态 | 单测 | @since 12 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `onChange(callback)` | Public | EditableTextOnChangeCallback | this | 无 | 内容变更 @since 7/12 | AC-1.1 |
| `onWillChange(callback)` | Public | Callback<EditableTextChangeValue,boolean> | this | 无 | 拦截变更 @since 15/20 | AC-1.2 |
| `onSubmit(callback)` | Public | OnSubmitCallback | this | 无 | 提交 @since 7/18 | AC-2.1 |
| `onEditChange(callback)` | Public | Callback<boolean> | this | 无 | 编辑态 @since 8/18 | AC-2.2 |
| `onEditChanged(callback)` | Public（@deprecated since 8） | function | this | 无 | 旧编辑态 @since 7 | AC-2.3 |
| `onWillInsert(callback)` | Public | Callback<InsertValue,boolean> | this | 无 | 拦截插入 @since 12 | AC-3.1 |
| `onDidInsert(callback)` | Public | Callback<InsertValue> | this | 无 | 插入通知 @since 12 | AC-3.2 |
| `onWillDelete(callback)` | Public | Callback<DeleteValue,boolean> | this | 无 | 拦截删除 @since 12 | AC-3.3 |
| `onDidDelete(callback)` | Public | Callback<DeleteValue> | this | 无 | 删除通知 @since 12 | AC-3.4 |
| `onCopy(callback)` | Public | Callback<string> | this | 无 | 复制 @since 8/18 | AC-4.1 |
| `onCut(callback)` | Public | Callback<string> | this | 无 | 剪切 @since 8/18 | AC-4.3 |
| `onPaste(callback)` | Public | OnPasteCallback | this | 无 | 粘贴 @since 8/18 | AC-4.4 |
| `onSecurityStateChange(callback)` | Public | Callback<boolean> | this | 无 | 安全态 @since 12 | AC-5.1 |
| C-API `NODE_TEXT_INPUT_ON_CHANGE`/`ON_WILL_CHANGE`/`ON_CHANGE_WITH_PREVIEW_TEXT`/`ON_SUBMIT`/`ON_EDIT_CHANGE`/`ON_WILL_INSERT`/`ON_DID_INSERT`/`ON_WILL_DELETE`/`ON_DID_DELETE`/`ON_COPY`/`ON_WILL_COPY`/`ON_CUT`/`ON_WILL_CUT`/`ON_PASTE` | System | KNode, callback | void | 无 | C-API 事件 @since 12/16/20/26 | 全部 |

## 接口规格

### 接口定义

**onWillChange(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onWillChange(callback: Callback<EditableTextChangeValue, boolean>): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback<EditableTextChangeValue,boolean> | 是 | — | 返回 false 拦截 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 返回 true | 应用变更 | AC-1.2 |
| 2 | 返回 false | 拦截变更 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** onChange/onSubmit/onCopy/onCut/onPaste @since 7/8（Callback 类型 @since 12/18）；onWillChange @since 15/20；onWillInsert/onDidInsert/onWillDelete/onDidDelete/onSecurityStateChange @since 12；onChangeWithPreviewText @since 16；onWillCopy/onWillCut/onPaste(C-API) @since 26；onEditChanged @deprecated since 8
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| will 返回值经 OH_ArkUI_NodeEvent_SetReturnNumberValue | 拦截需返回值管道 | AC-1.2,3.1,4.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 事件可单测 | 单测 | text_field_event_hub.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 事件支持无障碍通知 | AC-2.2 |

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
    query: "TextInput will/did 事件与返回值拦截管道"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
