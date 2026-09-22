# 特性规格

> Func-07-04-19-Feat-02 事件数据与分发：固化事件上下文统一 shape（`{componentId, eventData}`）、各组件 `eventData` 载荷（click=`{x,y}`、onChange=`{value}`/`{isOn}`/`{isChecked}`/`{value,status}`）、事件上下文解析（path 引用 + 深度上限）、handler 链执行（condition/as/break/dispatcher 链）、内置 action（`dispatchEvent`/`setDataModel`/`setAttributes`）、action 消息回传格式（`ClientToServerActionMessage`）与错误码（`ACTION_NOT_REGISTER=3001`/`ACTION_PARSE_FAILED=3201`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件数据与分发 |
| 特性编号 | Func-07-04-19-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 + 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-19 第二个 Feat，承接 Feat-01 事件模型 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/19-common-events/design.md` | Baselined |
| 事件上下文解析（C++） | `genui/src/main/cpp/functions/EventContextResolver.cpp` | — |
| 分发链执行（C++） | `genui/src/main/cpp/components/actions/EventHandlerChainExecutor.cpp` | — |
| 内置 action（C++） | `genui/src/main/cpp/components/actions/BuiltInActions.cpp` | — |
| 跨语言回传（C++） | `genui/src/main/cpp/functions/ActionDispatchBridge.cpp` | — |
| 控制器/桥接（ArkTS） | `genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`NativeEngineBridge.ets` | — |
| 错误码（ArkTS/C++） | `genui/src/main/ets/interface/Types.ets`、`genui/src/main/cpp/SurfaceErrorCodes.h` | — |
| 消息格式（Docs） | `reference/messages.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 事件上下文数据构建

**作为** 生成式 UI 宿主开发者,
**我想要** handler 内以统一 shape 访问事件上下文,
**以便** 稳定读取来源组件与事件载荷。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 组件派发事件且 extraContext 非 `{componentId|eventData}` 结构 THEN 上下文构建为 `{componentId: <id>, eventData: <extraContext>}`（`EventHandlerChainExecutor.cpp:350-364,333-348`） | 正常 |
| AC-1.2 | WHEN extraContext 已含 `componentId` 或 `eventData` 键（`IsEventContextObject` 为 true） THEN 保留该对象并仅在缺 `componentId` 时补写（`EventHandlerChainExecutor.cpp:328-331,352-361`） | 边界 |
| AC-1.3 | WHEN 点击事件触发 THEN `BuildClickContext` 返回 `{x: number, y: number}`（`A2UIComponent.cpp:292-311`） | 正常 |
| AC-1.4 | WHEN TextInput onChange 触发 THEN 载荷 `{value: string}`（`ExtendedTextInputComponent.cpp:70-79,1436`） | 正常 |
| AC-1.5 | WHEN Checkbox/Toggle/Radio/CheckboxGroup onChange 触发 THEN 载荷分别为 `{value:bool}`/`{isOn:bool}`/`{isChecked:bool}`/`{value:string[],status:string}`（`ExtendedCheckboxComponent.cpp:60-69,759`、`ExtendedToggleComponent.cpp:43-52,365`、`ExtendedRadioComponent.cpp:45-54,360`、`ExtendedCheckboxGroupComponent.cpp:67-83,625`） | 正常 |

### US-2: 事件上下文解析（path 引用）

**作为** 生成式 UI 宿主开发者,
**我想要** action.event.context 中的路径引用被解析为数据模型值,
**以便** 回传服务端前上下文化为具体数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `action.event.context` 子值含 `path` 或 `call` THEN `EventContextResolver::Resolve` 经 `DynamicValueResolver::ResolveRecursively` 解析为实际值（`EventContextResolver.cpp:152-162,145-149`） | 正常 |
| AC-2.2 | WHEN `rawContextDescriptor` 非对象（null/数组/标量） THEN `Resolve` 回落为 `{}`（`EventContextResolver.cpp:203-206`） | 异常 |
| AC-2.3 | WHEN 上下文某键为 malformed function descriptor（含 call/args/returnType 但缺 call 或 call 非 string/空） THEN 派发 schema warning 并跳过该键（`EventContextResolver.cpp:31-82,214-217`） | 异常 |
| AC-2.4 | WHEN 上下文某键解析失败 THEN 告警并跳过该键，不影响其余键（`EventContextResolver.cpp:224-227`） | 恢复 |
| AC-2.5 | WHEN `action.event.context` 递归深度超过 `MAX_EVENT_CONTEXT_DEPTH=20` THEN `ValidateEventContext` 返回 false，丢弃 action 并派发 `SURFACE_ERROR_ACTION_PARSE_FAILED`（`ActionParser.cpp:40-62,76-87,130-139`） | 边界 |

### US-3: handler 链执行

**作为** 生成式 UI 宿主开发者,
**我想要** handler 链按序执行并支持条件跳过、链中断与局部变量,
**以便** 表达多步事件响应流程。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 事件触发且存在对应 handler 集 THEN `DispatchEventToHandlers` 构造 `ExecutionContext` 并执行 `ExecuteChain`（`EventHandlerChainExecutor.cpp:425-457`） | 正常 |
| AC-3.2 | WHEN 事件名无对应 handler 或 handler 集为空 THEN `DispatchEventToHandlers` 返回 false 不打执行（`EventHandlerChainExecutor.cpp:427-432`） | 边界 |
| AC-3.3 | WHEN step `condition` 求值为 false THEN 跳过该 handler，链继续（`EventHandlerChainExecutor.cpp:391-394`） | 正常 |
| AC-3.4 | WHEN step `call == "break"` THEN 立即中断链（`EventHandlerChainExecutor.cpp:396-399`） | 正常 |
| AC-3.5 | WHEN step `as` 非空且 dispatch 结果有效 THEN 结果绑定到 `context.localVariables[step.as]`（`EventHandlerChainExecutor.cpp:419-421`） | 正常 |
| AC-3.6 | WHEN handler 执行抛出异常（std::exception/unknown） THEN 记录错误日志并中断链（`EventHandlerChainExecutor.cpp:403-417`） | 异常 |

### US-4: 内置 action

**作为** 生成式 UI 宿主开发者,
**我想要** 使用内置 action 完成事件转发与本地数据/属性更新,
**以便** 无需自定义函数即可编排常见交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN handler call 为 `dispatchEvent` 且 `args.eventName` 非空 THEN 经 `ActionDispatchBridge::Dispatch` 回传事件（`BuiltInActions.cpp:118-136`） | 正常 |
| AC-4.2 | WHEN `dispatchEvent` 的 `eventName` 为空 THEN 告警返回空，不回传（`BuiltInActions.cpp:121-125`） | 异常 |
| AC-4.3 | WHEN handler call 为 `setDataModel` 且 `args.path` 非空 THEN `DataModel::UpdateByPath` + `NotifyPathUpdate`（`BuiltInActions.cpp:138-160`） | 正常 |
| AC-4.4 | WHEN `setDataModel` 的 `path` 为空 THEN 告警返回空，不更新（`BuiltInActions.cpp:150-154`） | 异常 |
| AC-4.5 | WHEN handler call 为 `setAttributes` 且 `componentId` 非空、`value` 为对象、目标组件存在 THEN 应用描述符（`BuiltInActions.cpp:162-199`） | 正常 |
| AC-4.6 | WHEN `setAttributes` 的 `componentId` 空/value 非对象/surface 或 component 不存在 THEN 告警返回空，不更新（`BuiltInActions.cpp:164-191`） | 异常 |
| AC-4.7 | WHEN 内置 action 由 `RegisterBuiltInActions` 注册为 `dispatchEvent`/`setDataModel`/`setAttributes` 三者 THEN `NativeActionRegistry::HasAction` 命中（`BuiltInActions.cpp:203-208`） | 正常 |

### US-5: action 消息回传格式

**作为** 生成式 UI 宿主开发者,
**我想要** 回传 action 消息格式稳定,
**以便** 服务端可解析并继续处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN native 事件需回传服务端 THEN `ActionDispatchBridge::Dispatch` 构造 napi 请求对象 `{renderId, surfaceId, sourceComponentId, name, context}`（`ActionDispatchBridge.cpp:85-105`） | 正常 |
| AC-5.2 | WHEN ArkTS 收到 `NativeActionEventRequest` THEN `emitActionEvent` 组装 `ClientToServerActionMessage`：`version` 取默认协议版本、`action{name,surfaceId,sourceComponentId,timestamp,context}`（`SurfaceControllerImpl.ets:585-596`） | 正常 |
| AC-5.3 | WHEN `request.timestamp` 缺省或空 THEN 回落 `new Date().toISOString()`（`SurfaceControllerImpl.ets:585-586`） | 边界 |
| AC-5.4 | WHEN `request.context` 未定义 THEN 回落 `{}`（`SurfaceControllerImpl.ets:580-583`） | 边界 |
| AC-5.5 | WHEN 组装完成 THEN `onAction(JSON.stringify(actionPayload))` 以 JSON 字符串回调（`SurfaceControllerImpl.ets:597`） | 正常 |

### US-6: 事件错误码契约

**作为** 生成式 UI 宿主开发者,
**我想要** 事件相关错误以稳定错误码上报,
**以便** 宿主分类处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 触发 action 但宿主未注册 `onAction` THEN 上报 `SurfaceErrorCode.ACTION_NOT_REGISTER`（值 3001）（`SurfaceControllerImpl.ets:567-577`、`Types.ets:104`） | 异常 |
| AC-6.2 | WHEN `ActionParser::Parse` 解析失败或 context 超深 THEN native 经 `RuntimeErrorDispatchBridge` 派发 `SURFACE_ERROR_ACTION_PARSE_FAILED`（值 3201）（`ActionParser.cpp:31-38`、`SurfaceErrorCodes.h:61`） | 异常 |
| AC-6.3 | WHEN native 常量与 ArkTS 枚举比对 THEN `SurfaceErrorCodes.h:59,61` 与 `Types.ets:104,110` 数值对齐（3001/3201） | 正常 |
| AC-6.4 | WHEN 控制器已销毁 THEN `emitActionEvent` 直接返回，不回传（`SurfaceControllerImpl.ets:564-566`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-2 | C++ UT：`BuildDispatchEventContext`/`Build*EventContext` | `EventHandlerChainExecutor.cpp:328-364`、各 `Extended*Component.cpp` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-3,R-4 | T-2 | C++ UT：`EventContextResolver::Resolve` | `EventContextResolver.cpp:191-233`、`ActionParser.cpp:40-87` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-5,R-6 | T-2 | C++ UT：`ExecuteChain`/`DispatchEventToHandlers` | `EventHandlerChainExecutor.cpp:384-457` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 | R-7,R-8 | T-2 | C++ UT：`BuiltInActions` | `BuiltInActions.cpp:118-208` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-9 | T-2 | ArkTS 单测 + C++ UT | `ActionDispatchBridge.cpp:85-105`、`SurfaceControllerImpl.ets:563-598` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-10 | T-2 | 静态比对 + ArkTS 单测 | `Types.ets:104,110`、`SurfaceErrorCodes.h:59,61` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 事件派发，extraContext 非事件上下文对象 | 构造 `{componentId, eventData}` | 统一外层 shape | AC-1.1 |
| R-2 | 边界 | extraContext 已含 componentId/eventData | 保留并仅补 componentId | `IsEventContextObject` 判定 | AC-1.2 |
| R-3 | 行为 | action.event.context 子值含 path/call | 解析为数据模型实际值 | allowExpression=true | AC-2.1 |
| R-4 | 异常 | context 非对象/键解析失败/malformed descriptor | 回落 `{}` 或跳过该键 | 单键失败不影响其余 | AC-2.2,AC-2.3,AC-2.4 |
| R-5 | 行为 | 事件名命中 handler 集 | 构造上下文并执行链 | 无 handler 返回 false | AC-3.1,AC-3.2 |
| R-6 | 行为 | condition 为 false / call==break / as 绑定 / 异常 | 跳过/中断/绑定/中断 | 异常即中断 | AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| R-7 | 行为 | call 命中内置 action | 执行事件转发/数据/属性更新 | 三者注册于 Registry | AC-4.1,AC-4.3,AC-4.5,AC-4.7 |
| R-8 | 异常 | 内置 action 参数非法（eventName/path 空、componentId 空、value 非对象、目标不存在） | 告警并返回空，无副作用 | 链继续 | AC-4.2,AC-4.4,AC-4.6 |
| R-9 | 行为 | 事件需回传服务端 | 构造 napi 请求 → 组装 ClientToServerActionMessage → onAction(JSON) | timestamp/context 有回落 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| R-10 | 异常 | onAction 未注册 / 解析失败 / 已销毁 | 报 3001 / 派发 3201 / 直接返回 | 数值双层对齐 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 上下文构建 | C++ UT | `{componentId,eventData}` 与各组件载荷 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 上下文解析 | C++ UT | path 引用、malformed、深度上限 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 链执行 | C++ UT | condition/as/break/异常中断 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 内置 action | C++ UT | dispatchEvent/setDataModel/setAttributes |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 消息回传 | ArkTS 单测 | ClientToServerActionMessage 组装 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 错误码 | 静态比对 | 3001/3201 数值对齐 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceErrorCode.ACTION_NOT_REGISTER` | 既有 | onAction 未注册错误 | 数值 3001 稳定 | AC-6.1 |
| `SurfaceErrorCode.ACTION_PARSE_FAILED` | 既有 | action 解析失败错误 | 数值 3201 稳定 | AC-6.2 |
| `ActionReceiver`（`(action: string) => void`） | 既有 | action 回传回调 | 入参为 JSON 字符串 | AC-5.5 |

> d.ts 位置：`genui/src/main/ets/interface/Types.ets`、`SurfaceController.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ActionDispatchBridge::Dispatch(renderId, surfaceId, sourceComponentId, eventName, context)`（内部，`ActionDispatchBridge.cpp:64`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool Dispatch(int32_t renderId, const std::string& surfaceId, const std::string& sourceComponentId, const std::string& eventName, const JsonValue& context) const` |
| 返回值 | `bool` — napi 调用是否成功 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | 桥未安装/打开 handle scope 失败/回调缺失时返回 false 并告警（`ActionDispatchBridge.cpp:68-83`） |
| 关联 AC | AC-5.1 |

**`SurfaceControllerImpl.emitActionEvent(request)`（私有，`SurfaceControllerImpl.ets:563`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `private emitActionEvent(request: NativeActionEventRequest): void` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | onAction 未注册→`ACTION_NOT_REGISTER`(3001)；已销毁→直接返回 |
| 关联 AC | AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-6.1,AC-6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| eventName | string | 是 | — | 非空（dispatchEvent 内置 action 校验，`BuiltInActions.cpp:121`） |
| context | JsonValue | 否 | `{}` | 任意 JSON，可为 `{componentId,eventData}` |
| request.timestamp | string | 否 | `new Date().toISOString()` | 空串回落 |
| request.context | A2UIValueType | 否 | `{}` | undefined 回落 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | native 事件回传，桥已安装 | 构造 napi 对象并回调 | AC-5.1 |
| 2 | onAction 未注册 | reportError(3001)，不回传 | AC-6.1 |
| 3 | 控制器已销毁 | 直接返回 | AC-6.4 |
| 4 | timestamp/context 缺省 | 回落 ISO 时间/`{}` | AC-5.3,AC-5.4 |
| 5 | 组装完成 | onAction(JSON 字符串) | AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** `ClientToServerActionMessage.version` 取 `CapabilitiesCore.getDefaultA2UIProtocolVersion()`（`SurfaceControllerImpl.ets:588`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 事件上下文统一 shape | handler 内 `$context` 为 `{componentId, eventData}` | AC-1.1,AC-1.2 |
| 事件上下文深度上限 | `MAX_EVENT_CONTEXT_DEPTH=20`，超限丢弃 | AC-2.5 |
| 错误码双层对齐 | native 常量 ↔ ArkTS 枚举数值一致 | AC-6.3 |
| 分发链有序 | NativeAction → NativeFunction → BridgeFunction 依序命中 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | handler 异常不崩溃，记录并中断链 | C++ UT | `EventHandlerChainExecutor.cpp:403-417` |
| 性能 | 事件上下文深度受 20 约束 | C++ UT | `ActionParser.cpp:29,40-62` |
| 可测试性 | 内置 action 可独立单测 | C++ UT | `BuiltInActions.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 事件数据/分发设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 事件数据层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 多 Surface 归 07-04-01 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | action 消息 `version` 随协议版本 | AC-5.2 |
| 生态兼容 | 是 | action 消息格式对齐 A2UI v0.9 `action` 契约 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 事件数据与分发
  作为 生成式 UI 宿主开发者
  我想要 事件携带上下文并经分发链回传服务端
  以便 服务端据此继续交互流程

  Scenario: onChange 事件回传
    Given 组件 TextInput 定义了 onChange handler
    When 用户输入导致值变更
    Then 组件 DispatchEvent("onChange", {value:"hi"})
    And 上下文构建为 {componentId:"<id>", eventData:{value:"hi"}}
    And dispatchEvent 内置 action 经 ActionDispatchBridge 回传
    And 宿主 onAction 收到 {"version":"v0.9","action":{"name":"...","surfaceId":"main","sourceComponentId":"<id>","timestamp":"...","context":{...}}}

  Scenario: handler 链条件跳过与中断
    Given onClick 链为 [{"call":"setDataModel","args":{"path":"/a","value":1}},{"call":"break","condition":"{{ $context.eventData.x == 0 }}"},{"call":"openUrl","args":{"url":"https://x"}}]
    When 触发 onClick 且 eventData.x == 0
    Then 第一个 handler 执行，第二个 break 命中中断，第三个不执行
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做事件数据与分发；事件模型与触发契约见 Feat-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "EventHandlerChainExecutor ExecuteChain DispatchEventToHandlers BuildDispatchEventContext condition break as"
  - repo: "GenerativeUI/A2UIRender"
    query: "BuiltInActions dispatchEvent setDataModel setAttributes ActionDispatchBridge EventContextResolver"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceControllerImpl emitActionEvent ClientToServerActionMessage ACTION_NOT_REGISTER 3001 ACTION_PARSE_FAILED 3201"
```

**关键文档：** `genui/src/main/cpp/components/actions/EventHandlerChainExecutor.cpp`、`genui/src/main/cpp/components/actions/BuiltInActions.cpp`、`genui/src/main/cpp/functions/EventContextResolver.cpp`、`genui/src/main/cpp/functions/ActionDispatchBridge.cpp`、`genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/cpp/SurfaceErrorCodes.h`