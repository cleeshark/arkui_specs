# 特性规格

> Func-05-12-01-Feat-02 PluginComponent跨组件Push/Request Manager：固化 @ohos.pluginComponentManager push/request/on/off 跨组件通信机制的行为规格，涵盖 FA 模型和 Stage 模型两条 IPC 通道。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | PluginComponent跨组件Push/Request Manager |
| 特性编号 | Func-05-12-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8+（public FA 模型），API 9+（@systemapi Stage 模型） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | push 跨组件推送规格 | 补录 push (FA model PushParameters) 和 push (Stage model PushParameterForStage) 的参数解析、IPC 通道和回调行为 |
| ADDED | request 跨组件请求规格 | 补录 request (FA model RequestParameters) 和 request (Stage model RequestParameterForStage) 的参数解析、IPC 通道和回调行为 |
| ADDED | on/off 事件注册规格 | 补录 on(eventType, callback) 事件注册和 off(want, callback) 注销行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/01-plugin-component/design.md` | Baselined |

---

## 用户故事

### US-1: 通过 push 向 Plugin 推送数据

**作为** 应用开发者,
**我想要** 通过 pluginComponentManager.push() 向目标 Plugin 推送模板和数据,
**以便** 宿主应用主动向 Plugin 传递更新内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `push({ want, name, data, extraData }, callback)` (FA 模型) THEN PluginComponentManager 通过 UIServiceMgrClient IPC 将 want + name + data + extraData 推送到目标 Plugin | 正常 |
| AC-1.2 | WHEN 调用 `push({ owner, target, name, data, extraData }, callback)` (Stage 模型) THEN 仅系统应用可调用（@systemapi）；PluginComponentManager 通过 UIServiceMgrClient IPC 推送到目标 Plugin | 正常 |
| AC-1.3 | WHEN push 成功 THEN AsyncCallback 回调无错误 | 正常 |
| AC-1.4 | WHEN push 失败（目标 Plugin 未注册）THEN AsyncCallback 回调携带错误码 | 异常 |

### US-2: 通过 request 向 Plugin 请求内容

**作为** 应用开发者,
**我想要** 通过 pluginComponentManager.request() 向目标 Plugin 请求模板和数据,
**以便** 宿主应用获取 Plugin 的当前内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `request({ want, name, data }, callback)` (FA 模型) THEN PluginComponentManager 通过 UIServiceMgrClient IPC 向目标 Plugin 发送 request | 正常 |
| AC-2.2 | WHEN 调用 `request({ owner, target, name, data }, callback)` (Stage 模型) THEN 仅系统应用可调用（@systemapi）；PluginComponentManager 通过 UIServiceMgrClient IPC 向目标 Plugin 发送 request | 正常 |
| AC-2.3 | WHEN request 成功且目标 Plugin 返回内容 THEN AsyncCallback 回调收到 RequestCallbackParameters { componentTemplate, data, extraData } | 正常 |
| AC-2.4 | WHEN request 中 jsonPath 非空 THEN PluginComponentManager 本地解析 JSON 文件（不走 IPC），直接返回模板 | 正常 |
| AC-2.5 | WHEN request 失败（目标 Plugin 未注册或未返回）THEN AsyncCallback 回调携带错误码 | 异常 |

### US-3: 通过 on 注册 Plugin 事件回调

**作为** 应用开发者,
**我想要** 通过 pluginComponentManager.on() 注册 push/request 事件回调,
**以便** 当其他应用向本应用 Plugin 推送或请求时收到通知。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `on('push', callback)` (FA 模型 2 参数) THEN 注册 OnPushEventCallback 到 JSPluginCallbackMgr + UIServiceListener | 正常 |
| AC-3.2 | WHEN 调用 `on(want, 'push', callback)` (Stage 模型 3 参数) THEN 注册 OnPushEventCallback 并绑定到指定 want | 正常 |
| AC-3.3 | WHEN 调用 `on('request', callback)` THEN 注册 OnRequestEventCallback 到 JSPluginCallbackMgr + UIServiceListener | 正常 |
| AC-3.4 | WHEN eventType 不是 'push' 或 'request' THEN 返回 null（注册失败） | 异常 |

### US-4: 通过 off 注销 Plugin 事件回调

**作为** 应用开发者,
**我想要** 通过 pluginComponentManager.off() 注销已注册的 push/request 事件回调,
**以便** 不再接收跨组件通知。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `off(want, callback)` (Stage 模型 2 参数) THEN 从 JSPluginCallbackMgr 注销回调 + 通过 UIServiceMgrClient IPC 注销 UIService 注册 | 正常 |
| AC-4.2 | WHEN off 注销后 THEN 后续 push/request 事件不再触发已注销的回调 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1, R-2, R-5 | 已有实现 | 代码评审 | `js_plugin_component.cpp`, `plugin_component_manager.cpp` |
| AC-2.1~2.5 | R-3, R-4, R-6 | 已有实现 | 代码评审 | `js_plugin_component.cpp`, `plugin_component_manager.cpp` |
| AC-3.1~3.4 | R-7, R-8 | 已有实现 | 代码评审 | `js_plugin_component.cpp` |
| AC-4.1~4.2 | R-9 | 已有实现 | 代码评审 | `js_plugin_component.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | push FA 模型调用 | JSPlugin::JSPush 解析 PushParameters → PluginComponentManager::Push(want, name, jsonPath, data, extraData) → UIServiceMgrClient::Push(want, name, jsonPath, data, extraData) → IPC 到目标 Plugin | FA 模型：ability 非空 | AC-1.1 |
| R-2 | 行为 | push Stage 模型调用 | UnwrapOwnerWantFromJS 检查 IsSystemAppByFullTokenID → 解析 PushParameterForStage → PluginComponentManager::Push → UIServiceMgrClient::Push → IPC | Stage 模型：@systemapi 仅系统应用 | AC-1.2 |
| R-3 | 行为 | request FA 模型调用 | JSPlugin::JSRequest 解析 RequestParameters → PluginComponentManager::Request → IPC 或本地 JSON 解析 | — | AC-2.1 |
| R-4 | 行为 | request Stage 模型调用 | 系统应用检查 → 解析 RequestParameterForStage → PluginComponentManager::Request → IPC 或本地 JSON 解析 | — | AC-2.2 |
| R-5 | 异常 | push 目标 Plugin 未注册 | UIServiceMgrClient::Push 返回错误 → AsyncCallback 回调携带错误码 | — | AC-1.4 |
| R-6 | 行为 | request jsonPath 非空 | PluginComponentManager::Request 本地解析 JSON 文件 → listener_->RequestByJsonPath → 不走 IPC 路径 | 本地 JSON 解析为替代路径 | AC-2.4 |
| R-7 | 行为 | on('push', callback) FA 模型 | JSPluginCallbackMgr::RegisterOnEvent → PluginComponentManager::RegisterCallBack → UIServiceMgrClient::RegisterCallBack → IPC 注册 IUIService | FA 模型 2 参数 | AC-3.1 |
| R-8 | 行为 | on eventType 非法 | eventType 不是 'push' 或 'request' → 返回 null（napi_value nullptr） | — | AC-3.4 |
| R-9 | 行为 | off(want, callback) Stage 模型 | JSPluginCallbackMgr::UnregisterCallBack → PluginComponentManager::UnregisterCallBack → UIServiceMgrClient::UnregisterCallBack → IPC 注销 | off 仅支持 Stage 模型 2 参数形式 | AC-4.1 |
| R-10 | 边界 | IPC 通道：UIServiceMgr SA ID 7001 | 所有 push/request/on/off IPC 通过 IUIServiceMgr (SA ID 7001) 实现 Binder IPC | SA ID 固定 | AC-1.1~4.2 |
| R-11 | 边界 | off 未在 d.ts 中声明 | NAPI 实现 JSOff 存在，但 @ohos.pluginComponent.d.ts 未声明 off 函数 | SDK 声明缺失（推测） | AC-4.1 |
| R-12 | 行为 | push 回调链 | UIServiceStub::OnRemoteRequest → OnPushCallBackInner → UIServiceListener::OnPushCallBack → JSPluginCallback::OnPushEvent → uv_async → JS callback | 回调通过 uv_async 异步传递到 JS 线程 | AC-1.1 |
| R-13 | 行为 | request 回调链 | 目标 Plugin 处理 request → ReturnRequest → UIServiceListener::OnReturnRequest → JSPluginCallback::OnRequestCallBack → AsyncCallback/Promise resolve | — | AC-2.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1 | 代码评审 | push FA 模型 IPC 通道完整性 |
| VM-2 | AC-1.2, R-2 | 代码评审 | push Stage 模型系统应用检查 + IPC |
| VM-3 | AC-2.1, R-3 | 代码评审 | request FA 模型 IPC 通道 |
| VM-4 | AC-2.4, R-6 | 代码评审 | request jsonPath 本地解析路径 |
| VM-5 | AC-3.1~3.3, R-7 | 代码评审 | on 注册回调链 |
| VM-6 | AC-4.1, R-9 | 代码评审 | off 注销回调链 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `push(param: PushParameters, callback: AsyncCallback<void>)` | Public | FA 模型向 Plugin 推送数据 | `@ohos.pluginComponent.d.ts` | 8 | - |
| `push(param: PushParameterForStage, callback: AsyncCallback<void>)` | System | Stage 模型向 Plugin 推送数据 | `@ohos.pluginComponent.d.ts` | 9 | @systemapi |
| `request(param: RequestParameters, callback: AsyncCallback<RequestCallbackParameters>)` | Public | FA 模型向 Plugin 请求内容 | `@ohos.pluginComponent.d.ts` | 8 | - |
| `request(param: RequestParameterForStage, callback: AsyncCallback<RequestCallbackParameters>)` | System | Stage 模型向 Plugin 请求内容 | `@ohos.pluginComponent.d.ts` | 9 | @systemapi |
| `on(eventType: string, callback: OnPushEventCallback | OnRequestEventCallback)` | Public | 注册事件回调 | `@ohos.pluginComponent.d.ts` | 8 | - |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `PushParameters` | `{ want: Want; name: string; data: KVObject; extraData: KVObject; jsonPath?: string }` | `@ohos.pluginComponent.d.ts` |
| `PushParameterForStage` | `{ owner: Want; target: Want; name: string; data: KVObject; extraData: KVObject; jsonPath?: string }` | `@ohos.pluginComponent.d.ts` |
| `RequestParameters` | `{ want: Want; name: string; data: KVObject; jsonPath?: string }` | `@ohos.pluginComponent.d.ts` |
| `RequestParameterForStage` | `{ owner: Want; target: Want; name: string; data: KVObject; jsonPath?: string }` | `@ohos.pluginComponent.d.ts` |
| `RequestCallbackParameters` | `{ componentTemplate: PluginComponentTemplate; data: KVObject; extraData: KVObject }` | `@ohos.pluginComponent.d.ts` |
| `RequestEventResult` | `{ template?: string; data?: KVObject; extraData?: KVObject }` | `@ohos.pluginComponent.d.ts` |
| `KVObject` | `{ [key: string]: number | string | boolean | [] | KVObject }` (递归) | `@ohos.pluginComponent.d.ts` |
| `OnPushEventCallback` | `(source: Want, template: PluginComponentTemplate, data: KVObject, extraData: KVObject) => void` | `@ohos.pluginComponent.d.ts` |
| `OnRequestEventCallback` | `(source: Want, name: string, data: KVObject) => RequestEventResult` | `@ohos.pluginComponent.d.ts` |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| `off` | NAPI 实现存在但 d.ts 未声明（推测：SDK 声明缺失） | AC-4.1 |

---

## 接口规格

### 接口定义 — push(param, callback) [FA 模型]

| 属性 | 值 |
|------|-----|
| 函数签名 | `void push(PushParameters param, AsyncCallback<void> callback)` |
| 返回值 | void（异步回调） |
| 开放范围 | Public |
| 错误码 | 目标 Plugin 未注册时 AsyncCallback 携带错误码 |
| 关联 AC | AC-1.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| param.want | Want | 是 | — | 目标 Plugin 的 Ability Want |
| param.name | string | 是 | — | Plugin 名称标识 |
| param.data | KVObject | 是 | — | 推送数据 |
| param.extraData | KVObject | 是 | — | 额外推送数据 |
| param.jsonPath | string | 否 | undefined | JSON 配置路径 |
| callback | AsyncCallback<void> | 是 | — | 异步回调 |

### 接口定义 — push(param, callback) [Stage 模型]

| 属性 | 值 |
|------|-----|
| 函数签名 | `void push(PushParameterForStage param, AsyncCallback<void> callback)` |
| 返回值 | void（异步回调） |
| 开放范围 | System (@systemapi, @StageModelOnly) |
| 错误码 | 非系统应用调用失败；目标 Plugin 未注册 |
| 关联 AC | AC-1.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| param.owner | Want | 是 | — | 调用方自身 Ability Want（系统应用） |
| param.target | Want | 是 | — | 目标 Plugin Ability Want |
| param.name | string | 是 | — | Plugin 名称标识 |
| param.data | KVObject | 是 | — | 推送数据 |
| param.extraData | KVObject | 是 | — | 额外推送数据 |
| param.jsonPath | string | 否 | undefined | JSON 配置路径 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 系统应用调用 push Stage 模型 | 通过 UIServiceMgrClient IPC 推送到目标 Plugin | AC-1.2 |
| 2 | 非系统应用调用 push Stage 模型 | UnwrapOwnerWantFromJS 检查失败，调用不执行 | 异常 |
| 3 | push 成功 | AsyncCallback 无错误 | AC-1.3 |
| 4 | push 目标 Plugin 未注册 | AsyncCallback 携带错误码 | AC-1.4 |

### 接口定义 — request(param, callback) [FA 模型]

| 属性 | 值 |
|------|-----|
| 函数签名 | `void request(RequestParameters param, AsyncCallback<RequestCallbackParameters> callback)` |
| 返回值 | void（异步回调返回 RequestCallbackParameters） |
| 开放范围 | Public |
| 错误码 | 目标 Plugin 未注册或未返回 |
| 关联 AC | AC-2.1 |

### 接口定义 — request(param, callback) [Stage 模型]

| 属性 | 值 |
|------|-----|
| 函数签名 | `void request(RequestParameterForStage param, AsyncCallback<RequestCallbackParameters> callback)` |
| 返回范围 | System (@systemapi, @StageModelOnly) |
| 关联 AC | AC-2.2 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | request 成功且 Plugin 返回 | AsyncCallback 收到 RequestCallbackParameters { componentTemplate, data, extraData } | AC-2.3 |
| 2 | request 中 jsonPath 非空 | 本地解析 JSON 文件，不走 IPC | AC-2.4 |
| 3 | request 失败 | AsyncCallback 携带错误码 | AC-2.5 |

### 接口定义 — on(eventType, callback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void on(string eventType, OnPushEventCallback | OnRequestEventCallback callback)` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | eventType 非法返回 null |
| 关联 AC | AC-3.1~3.4 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| eventType | string | 是 | — | 仅接受 'push' 或 'request' |
| callback | OnPushEventCallback 或 OnRequestEventCallback | 是 | — | 根据 eventType 类型选择 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | on('push', callback) FA 模型 | 注册 OnPushEventCallback | AC-3.1 |
| 2 | on(want, 'push', callback) Stage 模型 | 注册 OnPushEventCallback 并绑定 want | AC-3.2 |
| 3 | on('request', callback) | 注册 OnRequestEventCallback | AC-3.3 |
| 4 | eventType 不是 'push' 或 'request' | 返回 null | AC-3.4 |

### 接口定义 — off(want, callback) [Stage 模型，NAPI-only]

| 属性 | 值 |
|------|-----|
| 函数签名 | `void off(Want want, callback)` |
| 返回值 | void |
| 开放范围 | NAPI-only（d.ts 未声明） |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | off(want, callback) | 注销回调 + 通过 IPC 注销 UIService 注册 | AC-4.1 |
| 2 | off 注销后 | 后续事件不再触发已注销回调 | AC-4.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（FA 模型 public），API 9（Stage 模型 @systemapi）
- **API 版本号策略:** FA 模型 since 8 public；Stage 模型 since 9 @systemapi；KVObject/Template/Callback since 12 @atomicservice
- **off 函数 SDK 声明缺失:** NAPI 实现 JSOff 存在但 d.ts 未声明，推测为 SDK 声明遗漏

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| IPC 通过 UIServiceMgr (SA ID 7001) | push/request/on/off 均通过 Binder IPC 传递 Want + 数据 | AC-1.1~4.2 |
| FA 模型 vs Stage 模型双通道 | FA 用 PushParameters/RequestParameters + 2 参数 on；Stage 用 PushParameterForStage/RequestParameterForStage + 3 参数 on + 2 参数 off | AC-1.1~4.2 |
| Stage 模型 @systemapi 限制 | 非系统应用调用 Stage push/request 时 UnwrapOwnerWantFromJS 检查失败 | AC-1.2, AC-2.2 |
| request jsonPath 本地解析 | jsonPath 非空时不走 IPC，直接读取本地 JSON | AC-2.4 |
| 回调通过 uv_async 异步传递 | IPC 回调通过 uv_async 传递到 JS 线程，不阻塞宿主线程 | AC-1.1, AC-2.3 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | IPC push/request 延迟由 Binder 通信决定，不设量化指标 | 集成测试 | — |
| 安全 | Stage 模型 @systemapi 限制系统应用；FA 模型 public 对所有应用开放 | API 评审 | @ohos.pluginComponent.d.ts |
| 可测试性 | push/request/on/off 可通过 Mock UIServiceMgrClient 验证 | 单测 | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | 无差异 | — | 集成测试 | — |
| 折叠屏 | 无差异 | — | 集成测试 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Manager 级 API 为数据通信接口，不涉及 UI 渲染 | — |
| 大字体 | 否 | Manager 级 API 不涉及 UI 渲染 | — |
| 深色模式 | 否 | Manager 级 API 不涉及 UI 渲染 | — |
| 多窗口/分屏 | 否 | Manager 级 API 为 IPC 通信，不受窗口影响 | — |
| 多用户 | 否 | IPC 通道基于 Want，不涉及多用户 | — |
| 版本升级 | 否 | API 8/9 起行为不变 | — |
| 生态兼容 | 是 | FA 模型 public + Stage 模型 @systemapi 共存 | AC-1.1~4.2 |

---

## 行为场景

```gherkin
Feature: PluginComponentManager 跨组件通信
  作为 应用开发者
  我想要 通过 pluginComponentManager push/request/on/off 实现跨组件通信
  以便 在宿主应用和 Plugin 之间传递数据和模板

  # ─── push ───────────────────────────────

  Scenario: push FA 模型向 Plugin 推送数据
    Given 一个宿主应用（FA 模型）
    And 目标 Plugin 已注册 UIService
    When 调用 pluginComponentManager.push({ want, name, data, extraData }, callback)
    Then PluginComponentManager 通过 UIServiceMgrClient IPC 推送数据到目标 Plugin
    And AsyncCallback 回调无错误

  Scenario: push Stage 模型系统应用向 Plugin 推送
    Given 一个系统应用（Stage 模型）
    And 目标 Plugin 已注册 UIService
    When 调用 pluginComponentManager.push({ owner, target, name, data, extraData }, callback)
    Then UnwrapOwnerWantFromJS 通过 IsSystemAppByFullTokenID 检查通过
    And 通过 UIServiceMgrClient IPC 推送数据到目标 Plugin

  Scenario: push 目标 Plugin 未注册
    Given 目标 Plugin 未注册 UIService
    When 调用 pluginComponentManager.push(...)
    Then AsyncCallback 回调携带错误码

  # ─── request ────────────────────────────

  Scenario: request FA 模型向 Plugin 请求内容
    Given 一个宿主应用（FA 模型）
    And 目标 Plugin 已注册 UIService
    When 调用 pluginComponentManager.request({ want, name, data }, callback)
    Then PluginComponentManager 通过 IPC 向目标 Plugin 发送 request
    And AsyncCallback 收到 RequestCallbackParameters

  Scenario: request jsonPath 本地解析
    Given 一个宿主应用
    When 调用 pluginComponentManager.request({ want, name, data, jsonPath: 'external.json' }, callback)
    Then PluginComponentManager 本地解析 JSON 文件
    And 不走 IPC 路径

  # ─── on ─────────────────────────────────

  Scenario: on 注册 push 事件回调 FA 模型
    Given 一个 Plugin 应用（FA 模型）
    When 调用 pluginComponentManager.on('push', onPushCallback)
    Then 注册 OnPushEventCallback 到 JSPluginCallbackMgr
    And 通过 UIServiceMgrClient IPC 注册 IUIService

  Scenario: on 注册 push 事件回调 Stage 模型
    Given 一个 Plugin 应用（Stage 模型）
    When 调用 pluginComponentManager.on(want, 'push', onPushCallback)
    Then 注册 OnPushEventCallback 并绑定到指定 want

  Scenario: on eventType 非法
    Given 一个应用
    When 调用 pluginComponentManager.on('invalid', callback)
    Then 返回 null（注册失败）

  # ─── off ────────────────────────────────

  Scenario: off 注销回调 Stage 模型
    Given 一个 Plugin 应用已注册 on push 回调
    When 调用 pluginComponentManager.off(want, callback)
    Then 从 JSPluginCallbackMgr 注销回调
    And 通过 UIServiceMgrClient IPC 注销 UIService 注册
    And 后续 push 事件不再触发该回调
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：push/request/on/off 跨组件通信；不做什么：PluginComponent 创建/模板/事件回调）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "PluginComponentManager push request on off IPC mechanism UIServiceMgrClient"
  - repo: "openharmony/ace_engine"
    query: "js_plugin_component.cpp JSPush JSRequest JSOn JSOff NAPI mapping"
  - repo: "openharmony/ace_engine"
    query: "IUIServiceMgr IUIService UIServiceStub Binder IPC dispatch"
  - repo: "openharmony/ace_engine"
    query: "FA model vs Stage model push request parameter parsing"
```

**关键文档：**
- SDK API：`interface/sdk-js/api/@ohos.pluginComponent.d.ts`
- NAPI 层：`interfaces/napi/kits/plugincomponent/js_plugin_component.cpp`
- Manager 层：`frameworks/core/components/plugin/plugin_component_manager.h`
- IPC 接口：`interfaces/inner_api/ui_service_manager/include/ui_service_interface.h`
