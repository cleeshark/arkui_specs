# 特性规格

> Func-05-12-06-Feat-02 SecurityUIExtensionComponent事件回调：固化 SecurityUIExtensionComponent onRemoteReady/onReceive/onError/onTerminated 事件回调注册、触发条件、回调数据格式、回调链路（SecuritySessionWrapperImpl→SecurityUIExtensionPattern→UIExtensionHub→ArkTS）的行为规格。SecurityUIExtensionProxy receiver 注册/注销机制（on/offAsyncReceiverRegister/on/offSyncReceiverRegister）由 Feat-01 覆盖，本规格补录事件触发条件与回调参数细节。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SecurityUIExtensionComponent事件回调 |
| 特性编号 | Func-05-12-06-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 20+（static）；Proxy receiver @since 22 static |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onRemoteReady 事件注册与回调参数规格 | 补录 onRemoteReady(callback: Callback<SecurityUIExtensionProxy>) 注册到 SecurityUIExtensionPattern/UIExtensionHub.onRemoteReadyCallback_、回调参数 SecurityUIExtensionProxy 对象构造规格 |
| ADDED | onReceive 事件回调规格 | 补录 onReceive(callback: ReceiveCallback) 注册到 UIExtensionHub.onReceiveCallback_、SecuritySessionWrapperImpl → FireOnReceiveCallback 触发链、ReceiveCallback type Callback<Record<string, RecordData>> 数据格式规格 |
| ADDED | onError 事件回调规格 | 补录 onError(callback: ErrorCallback<BusinessError>) 注册、多场景触发条件（启动失败/前台失败/后台失败/销毁失败/异常退出/超时/级联禁止）、错误码规格 |
| ADDED | onTerminated 事件回调规格 | 补录 onTerminated(callback: Callback<TerminationInfo>) 注册到 UIExtensionHub.onTerminatedCallback_、SecuritySessionWrapperImpl → FireOnTerminatedCallback 触发链、TerminationInfo { code } 数据格式规格 |
| ADDED | SecurityUIExtensionProxy receiver 注册/注销规格 | 补录 Proxy.on/offAsyncReceiverRegister/on/offSyncReceiverRegister @since 22 static 注册/注销到 SecurityUIExtensionPattern onAsyncOnCallbackList_/onSyncOnCallbackList_ 规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/06-security-ui-extension-component/design.md` | Baselined |
| Feat-01 | `specs/05-ui-components/12-embedded-display-components/06-security-ui-extension-component/Feat-01-security-creation-proxy-spec.md` | Baselined |

---

## 用户故事

### US-1: onRemoteReady 回调获取 SecurityUIExtensionProxy

**作为** 应用开发者,
**我想要** 通过 onRemoteReady(callback) 注册回调并在 SecurityUIExtensionAbility 连接成功时获取 SecurityUIExtensionProxy,
**以便** 使用 SecurityProxy 进行安全级数据通信。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `onRemoteReady(callback)` THEN JSSecurityUIExtension::OnRemoteReady 解析 callback → SecurityUIExtensionModelStatic::SetOnRemoteReady 注册到 SecurityUIExtensionPattern/UIExtensionHub.onRemoteReadyCallback_ | 正常 |
| AC-1.2 | WHEN SecurityUIExtensionAbility 连接成功 THEN SecuritySessionWrapperImpl::OnConnect → SecurityUIExtensionPattern::FireOnRemoteReadyCallback → UIExtensionHub::FireOnRemoteReadyCallback(SecurityUIExtensionProxy) → callback 收到 SecurityUIExtensionProxy(sessionWrapper_, pattern_) 对象 | 正常 |
| AC-1.3 | WHEN callback 为空 THEN 不注册回调；onRemoteReady 触发时无法传递 SecurityProxy | 异常 |

### US-2: onReceive 数据接收回调

**作为** 应用开发者,
**我想要** 通过 onReceive(callback) 注册回调并在收到 SecurityUIExtensionAbility 发送的数据时触发,
**以便** 处理安全级 Extension 主动推送的数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `onReceive(callback)` THEN JSSecurityUIExtension::OnReceive 解析 callback → UIExtensionHub::SetOnReceiveCallback 注册到 onReceiveCallback_ | 正常 |
| AC-2.2 | WHEN 远端 SecurityUIExtensionAbility sendData THEN SecuritySessionWrapperImpl::InitTransferExtensionDataFunc 注册 transferExtensionDataFunc_ → ExtensionSession 回调 → PostTask 到 UI 线程 → SecurityUIExtensionPattern::FireOnReceiveCallback(WantParams) → UIExtensionHub::FireOnReceiveCallback(params) → callback 收到 Record<string, RecordData> 数据 | 正常 |
| AC-2.3 | WHEN callback 为空 THEN 不注册回调；onReceive 触发时数据丢失 | 异常 |

### US-3: onTerminated 终止处理回调

**作为** 应用开发者,
**我想要** 通过 onTerminated(callback) 注册回调并在 SecurityUIExtensionAbility 终止时收到 TerminationInfo,
**以便** 根据终止码执行安全级 Extension 后续处理逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `onTerminated(callback)` THEN JSSecurityUIExtension::OnTerminated 解析 callback → UIExtensionHub::SetOnTerminatedCallback 注册到 onTerminatedCallback_ | 正常 |
| AC-3.2 | WHEN 远端 SecurityUIExtensionAbility 调用 terminateSelf 或正常断开 THEN SecuritySessionWrapperImpl → SecurityUIExtensionPattern::FireOnTerminatedCallback → UIExtensionHub::FireOnTerminatedCallback(code, wantWrap) → callback 收到 TerminationInfo { code } | 正常 |
| AC-3.3 | WHEN SecurityUIExtensionPattern.state_=DESTRUCTION THEN onTerminated 回调不触发 | 边界 |
| AC-3.4 | WHEN onTerminated 回调触发 THEN state_=DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；DestroySession | 正常 |
| AC-3.5 | WHEN callback 为空 THEN 不注册回调 | 异常 |

### US-4: onError 错误处理回调

**作为** 应用开发者,
**我想要** 通过 onError(callback) 注册回调并在 SecurityUIExtensionAbility 加载或运行失败时收到 BusinessError,
**以便** 根据错误码执行安全级错误恢复逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `onError(callback)` THEN JSSecurityUIExtension::OnError 解析 callback → SecurityUIExtensionPattern 注册 onError 回调 | 正常 |
| AC-4.2 | WHEN SecurityUIExtensionAbility 启动失败 THEN SecuritySessionWrapperImpl → SecurityUIExtensionPattern::FireOnErrorCallback → PlatformPattern::FireOnErrorCallback → UIExtensionHub 分发 → callback 收到 BusinessError | 正常 |
| AC-4.3 | WHEN SecurityUIExtensionAbility 异常退出 THEN SecuritySessionWrapperImpl::OnDisconnect isAbnormal=true → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY) | 正常 |
| AC-4.4 | WHEN SecurityUIExtensionAbility 超时 THEN SecuritySessionWrapperImpl::OnExtensionTimeout → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT/LIFECYCLE_TIMEOUT) | 正常 |
| AC-4.5 | WHEN 级联嵌套禁止 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE) | 正常 |
| AC-4.6 | WHEN onError 回调触发 THEN state_=NONE；DestroySession | 正常 |
| AC-4.7 | WHEN callback 为空 THEN 不注册回调 | 异常 |

### US-5: SecurityUIExtensionProxy receiver 注册/注销

**作为** 应用开发者,
**我想要** 通过 SecurityUIExtensionProxy.on/offAsyncReceiverRegister/on/offSyncReceiverRegister 注册和注销 receiver 回调,
**以便** 在远端注册数据接收回调时收到通知（用于判断是否可以 sendSync）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `proxy.on('asyncReceiverRegister', callback)` THEN SecurityUIExtensionPattern 注册回调到 onAsyncOnCallbackList_；远端注册 async receiver 时触发 callback(proxy) | 正常 |
| AC-5.2 | WHEN 调用 `proxy.on('syncReceiverRegister', callback)` THEN SecurityUIExtensionPattern 注册回调到 onSyncOnCallbackList_；远端注册 sync receiver 时触发 callback(proxy) | 正常 |
| AC-5.3 | WHEN 调用 `proxy.off('asyncReceiverRegister', callback)` THEN 从 onAsyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | 正常 |
| AC-5.4 | WHEN 调用 `proxy.off('syncReceiverRegister', callback)` THEN 从 onSyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1, R-2, R-3 | 已有实现 | 代码评审 | `js_security_ui_extension.cpp`, `security_ui_extension_pattern.cpp` |
| AC-2.1~2.3 | R-4, R-5, R-6 | 已有实现 | 代码评审 | `security_ui_extension_pattern.cpp:700-708`, `security_session_wrapper_impl.cpp` |
| AC-3.1~3.5 | R-7, R-8, R-9, R-10, R-11 | 已有实现 | 代码评审 | `security_ui_extension_pattern.cpp:665-687`, `security_session_wrapper_impl.cpp` |
| AC-4.1~4.7 | R-12, R-13, R-14, R-15, R-16, R-17, R-18 | 已有实现 | 代码评审 | `security_ui_extension_pattern.cpp:689-698`, `security_session_wrapper_impl.cpp` |
| AC-5.1~5.4 | R-19, R-20, R-21, R-22 | 已有实现 | 代码评审 | `security_ui_extension_proxy.cpp`, `js_security_ui_extension.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `onRemoteReady(callback)` 被调用 | JSSecurityUIExtension::OnRemoteReady 解析 callback → UIExtensionHub::SetOnRemoteReadyCallback(std::move(callback)) | — | AC-1.1 |
| R-2 | 行为 | SecurityUIExtensionAbility 连接成功 | SecuritySessionWrapperImpl::OnConnect → SecurityUIExtensionPattern::FireOnRemoteReadyCallback → UIExtensionHub::FireOnRemoteReadyCallback(SecurityUIExtensionProxy) → callback(proxy) | Proxy 封装 SecuritySessionWrapper + WeakPtr<SecurityUIExtensionPattern> | AC-1.2 |
| R-3 | 异常 | callback 为空 | 不注册回调 | — | AC-1.3 |
| R-4 | 行为 | `onReceive(callback)` 被调用 | JSSecurityUIExtension::OnReceive 解析 callback → UIExtensionHub::SetOnReceiveCallback(std::move(callback)) | — | AC-2.1 |
| R-5 | 行为 | 远端 SecurityUIExtensionAbility sendData | SecuritySessionWrapperImpl::InitTransferExtensionDataFunc → transferExtensionDataFunc_ → PostTask(UI线程) → SecurityUIExtensionPattern::FireOnReceiveCallback(WantParams) → UIExtensionHub::FireOnReceiveCallback(params) → callback(params) | PostTask 确保 UI 线程执行 | AC-2.2 |
| R-6 | 异常 | callback 为空 | 不注册回调 | — | AC-2.3 |
| R-7 | 行为 | `onTerminated(callback)` 被调用 | JSSecurityUIExtension::OnTerminated 解析 callback → UIExtensionHub::SetOnTerminatedCallback(std::move(callback)) | — | AC-3.1 |
| R-8 | 行为 | SecurityUIExtensionAbility terminateSelf 或正常断开 | SecuritySessionWrapperImpl → SecurityUIExtensionPattern::FireOnTerminatedCallback → UIExtensionHub::FireOnTerminatedCallback(code, wantWrap) → callback(TerminationInfo) | SecurityUIExtension 不走 onResult/onRelease compat 路径 | AC-3.2 |
| R-9 | 边界 | SecurityUIExtensionPattern.state_=DESTRUCTION 时 onTerminated 触发 | onTerminatedCallback_ 检查 state_==DESTRUCTION → 不回调 | 防止重复终止回调 | AC-3.3 |
| R-10 | 行为 | onTerminated 回调触发后 | state_ = DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；DestroySession | SecurityUIExtension 总是销毁 Session | AC-3.4 |
| R-11 | 异常 | callback 为空 | 不注册回调 | — | AC-3.5 |
| R-12 | 行为 | `onError(callback)` 被调用 | JSSecurityUIExtension::OnError 解析 callback → SecurityUIExtensionPattern 注册 onError 回调 | — | AC-4.1 |
| R-13 | 行为 | SecurityUIExtensionAbility 启动/运行失败 | SecuritySessionWrapperImpl → SecurityUIExtensionPattern::FireOnErrorCallback → PlatformPattern::FireOnErrorCallback → UIExtensionHub 分发 → callback(BusinessError) | ErrorCallback 类型为 ErrorCallback<BusinessError> | AC-4.2 |
| R-14 | 行为 | 异常退出 | SecuritySessionWrapperImpl::OnDisconnect isAbnormal=true → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY) | — | AC-4.3 |
| R-15 | 行为 | 超时 | SecuritySessionWrapperImpl::OnExtensionTimeout → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT/LIFECYCLE_TIMEOUT) | — | AC-4.4 |
| R-16 | 行为 | 级联嵌套禁止 | FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE) | SecurityUIExtension 也受级联限制 | AC-4.5 |
| R-17 | 行为 | onError 回调触发后 | state_ = NONE；SetEventProxyFlag(EVENT_NONE)；DestroySession | — | AC-4.6 |
| R-18 | 异常 | callback 为空 | 不注册回调 | — | AC-4.7 |
| R-19 | 行为 | `proxy.on('asyncReceiverRegister', callback)` | SecurityUIExtensionPattern 注册回调到 onAsyncOnCallbackList_；远端注册 async receiver 时触发 callback(proxy) | @since 22 static | AC-5.1 |
| R-20 | 行为 | `proxy.on('syncReceiverRegister', callback)` | SecurityUIExtensionPattern 注册回调到 onSyncOnCallbackList_；远端注册 sync receiver 时触发 callback(proxy) | @since 22 static | AC-5.2 |
| R-21 | 行为 | `proxy.off('asyncReceiverRegister', callback)` | 从 onAsyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | — | AC-5.3 |
| R-22 | 行为 | `proxy.off('syncReceiverRegister', callback)` | 从 onSyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | — | AC-5.4 |
| R-23 | 边界 | SecurityUIExtension 不支持 onResult/onRelease/onDrawReady | 仅四种事件：onRemoteReady/onReceive/onError/onTerminated | 安全级生命周期更严格 | — |
| R-24 | 边界 | 无 C-API modifier (@noninterop) | 仅 ArkTS static 范式可用 | — | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3, R-1, R-2, R-3 | 代码评审 | onRemoteReady 注册与 SecurityProxy 传递 |
| VM-2 | AC-2.1~2.3, R-4, R-5, R-6 | 代码评审 | onReceive 注册、触发链、WantParams 数据传递 |
| VM-3 | AC-3.1~3.5, R-7~R-11 | 代码评审 | onTerminated 注册、触发链、TerminationInfo 格式、状态检查 |
| VM-4 | AC-4.1~4.7, R-12~R-18 | 代码评审 | onError 注册、多场景触发、错误码格式 |
| VM-5 | AC-5.1~5.4, R-19~R-22 | 代码评审 | Proxy receiver 注册/注销 |
| VM-6 | R-23 | 代码评审 | 不支持 onResult/onRelease/onDrawReady |
| VM-7 | R-24 | 代码评审 | 无 C-API modifier |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `onRemoteReady(callback: Callback<SecurityUIExtensionProxy>)` | Static | 远端就绪回调 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `onReceive(callback: ReceiveCallback)` | Static | 收到 Extension 数据回调 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `onError(callback: ErrorCallback<BusinessError>)` | Static | 加载失败回调 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `onTerminated(callback: Callback<TerminationInfo>)` | Static | Extension 终止回调 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `SecurityUIExtensionProxy.on('asyncReceiverRegister', callback)` | Static | 注册异步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |
| `SecurityUIExtensionProxy.on('syncReceiverRegister', callback)` | Static | 注册同步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |
| `SecurityUIExtensionProxy.off('asyncReceiverRegister', callback?)` | Static | 注销异步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |
| `SecurityUIExtensionProxy.off('syncReceiverRegister', callback?)` | Static | 注销同步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `ReceiveCallback` | `Callback<Record<string, RecordData>>` — WantParams 到 Record 的映射 | `security_ui_extension_component.d.ts` |
| `ErrorCallback<BusinessError>` | `(error: BusinessError) => void` — BusinessError 包含 code/name/message | `security_ui_extension_component.d.ts` |
| `TerminationInfo` | `{ code: number }` — SecurityUIExtension 的 TerminationInfo 仅包含 code（无 want） | `security_ui_extension_component.d.ts` |
| `SecurityUIExtensionProxy` | `class { send, sendSync, on/offAsyncReceiverRegister, on/offSyncReceiverRegister }` | `security_ui_extension_component.d.ts` |
| `UIExtensionHub` (C++) | `class EventHub { onRemoteReadyCallback_, onTerminatedCallback_, onReceiveCallback_ }` — SecurityUIExtension 使用 UIExtensionHub 分发事件 | `ui_extension_hub.h` |
| `SecurityUIExtensionProxy` (C++) | `class { sessionWrapper_, pattern_ (WeakPtr), SendData/SendDataSync, GetPattern }` | `security_ui_extension_proxy.h` |
| `WantParams` (C++) | `AAFwk::WantParams` — 远端传递的数据结构 | `security_session_wrapper_impl.cpp` |

**C-API (NDK) 接口：**

| 说明 | 结论 |
|------|------|
| 无 C-API modifier | SecurityUIExtensionComponent 标记为 @noninterop，不提供 C-API modifier |

### 变更/废弃 API

无变更/废弃 API。

---

## 接口规格

### 接口定义 — onRemoteReady(callback: Callback<SecurityUIExtensionProxy>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `SecurityUIExtensionComponentAttribute onRemoteReady(callback: Callback<SecurityUIExtensionProxy>)` |
| 返回值 | `SecurityUIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | Static (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | Callback<SecurityUIExtensionProxy> | 是 | — | callback 参数为 SecurityUIExtensionProxy 对象 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SecurityUIExtensionAbility 连接成功 | callback(SecurityUIExtensionProxy) | AC-1.2 |
| 2 | callback 为空 | 不注册回调 | AC-1.3 |

### 接口定义 — onReceive(callback: ReceiveCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `SecurityUIExtensionComponentAttribute onReceive(callback: ReceiveCallback)` |
| 返回值 | `SecurityUIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | Static (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | ReceiveCallback (data: Record<string, RecordData>) => void | 是 | — | data 为 WantParams 到 Record<string, RecordData> 的映射 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 远端 SecurityUIExtensionAbility sendData | SecuritySessionWrapperImpl transferExtensionDataFunc_ → PostTask(UI) → FireOnReceiveCallback(WantParams) → UIExtensionHub::FireOnReceiveCallback → callback(data) | AC-2.2 |
| 2 | callback 为空 | 不注册回调 | AC-2.3 |

### 接口定义 — onError(callback: ErrorCallback<BusinessError>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `SecurityUIExtensionComponentAttribute onError(callback: ErrorCallback<BusinessError>)` |
| 返回值 | `SecurityUIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | Static (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.7 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | ErrorCallback<BusinessError> (error: BusinessError) => void | 是 | — | BusinessError 包含 code/name/message |

**错误码定义：**

| 错误码 | 名称 | 触发场景 | 关联 AC |
|--------|------|----------|---------|
| ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED | START_FAIL_NAME | 启动失败 | AC-4.2 |
| ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY | EXIT_ABNORMALLY_NAME | 异常退出 | AC-4.3 |
| ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT | EVENT_TIMEOUT_NAME | 超时 | AC-4.4 |
| ERROR_CODE_UIEXTENSION_FORBID_CASCADE | PULL_FAIL_NAME | 级联禁止 | AC-4.5 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 启动失败 | callback(BusinessError { code: FOREGROUND_FAILED, ... }) | AC-4.2 |
| 2 | 异常退出 | callback(BusinessError { code: EXITED_ABNORMALLY, ... }) | AC-4.3 |
| 3 | 超时 | callback(BusinessError { code: EVENT_TIMEOUT, ... }) | AC-4.4 |
| 4 | 级联禁止 | callback(BusinessError { code: FORBID_CASCADE, ... }) | AC-4.5 |
| 5 | onError 触发后 | state_=NONE；DestroySession | AC-4.6 |
| 6 | callback 为空 | 不注册回调 | AC-4.7 |

### 接口定义 — onTerminated(callback: Callback<TerminationInfo>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `SecurityUIExtensionComponentAttribute onTerminated(callback: Callback<TerminationInfo>)` |
| 返回值 | `SecurityUIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | Static (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.5 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | Callback<TerminationInfo> (info: { code: number }) => void | 是 | — | code 为终止码；0 表示正常终止 |

**TerminationInfo 定义：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | number | 是 | 终止码；0 表示正常终止 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SecurityUIExtensionAbility terminateSelf | FireOnTerminatedCallback(code, wantWrap) → callback({ code }) | AC-3.2 |
| 2 | OnDisconnect isAbnormal=false | FireOnTerminatedCallback(0, nullptr) → callback({ code: 0 }) | AC-3.2 |
| 3 | state_=DESTRUCTION | 不触发 callback | AC-3.3 |
| 4 | onTerminated 触发后 | state_=DESTRUCTION；DestroySession | AC-3.4 |
| 5 | callback 为空 | 不注册回调 | AC-3.5 |

### 接口定义 — SecurityUIExtensionProxy.on(type, callback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void on(type: 'asyncReceiverRegister' | 'syncReceiverRegister', callback: Callback<SecurityUIExtensionProxy>)` |
| 返回值 | void |
| 开放范围 | Static (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-5.1, AC-5.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| type | 'asyncReceiverRegister' | 'syncReceiverRegister' | 是 | — | type 必须为指定字符串 |
| callback | Callback<SecurityUIExtensionProxy> | 是 | — | callback 参数为 SecurityUIExtensionProxy 对象 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | proxy.on('asyncReceiverRegister', callback) | 注册到 onAsyncOnCallbackList_ | AC-5.1 |
| 2 | proxy.on('syncReceiverRegister', callback) | 注册到 onSyncOnCallbackList_ | AC-5.2 |

### 接口定义 — SecurityUIExtensionProxy.off(type, callback?)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void off(type: 'asyncReceiverRegister' | 'syncReceiverRegister', callback?: Callback<SecurityUIExtensionProxy>)` |
| 返回值 | void |
| 开放范围 | Static (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-5.3, AC-5.4 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| type | 'asyncReceiverRegister' | 'syncReceiverRegister' | 是 | — | type 必须为指定字符串 |
| callback | Callback<SecurityUIExtensionProxy> | 否 | undefined | 不传则清空全部回调 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | proxy.off('asyncReceiverRegister', callback) | 移除指定 callback | AC-5.3 |
| 2 | proxy.off('asyncReceiverRegister') | 清空 onAsyncOnCallbackList_ | AC-5.3 |
| 3 | proxy.off('syncReceiverRegister', callback) | 移除指定 callback | AC-5.4 |
| 4 | proxy.off('syncReceiverRegister') | 清空 onSyncOnCallbackList_ | AC-5.4 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 20（组件级事件）；API 22（Proxy receiver 注册/注销）
- **API 版本号策略:** onRemoteReady/onReceive/onError/onTerminated @since 20；Proxy on/offAsyncReceiverRegister/on/offSyncReceiverRegister @since 22

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| SecurityUIExtension 使用独立 UIExtensionHub 分发事件 | Pattern→UIExtensionHub→ArkTS 三层回调链 | AC-1.2, AC-2.2, AC-3.2 |
| SecurityUIExtension 不支持 onResult/onRelease/onDrawReady | 仅四种事件：onRemoteReady/onReceive/onError/onTerminated | — |
| TerminationInfo 仅包含 code（无 want） | 安全级 Extension 终止不携带 Want 数据 | AC-3.2 |
| onReceive 使用 ReceiveCallback type（而非 UIExtensionComponent 的 OnReceiveCallback） | ReceiveCallback = Callback<Record<string, RecordData>> | AC-2.2 |
| onError 使用 ErrorCallback<BusinessError> | BusinessError 包含 code/name/message | AC-4.2 |
| 无 C-API modifier (@noninterop) | 仅 ArkTS static 范式可用 | — |
| Proxy receiver 注册/注销 @since 22 | 晚于组件级事件 @since 20 | AC-5.1~5.4 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 事件回调通过 PostTask 到 UI 线程 | 集成测试 | security_session_wrapper_impl.cpp |
| 安全 | isTransferringCaller Token 提升需安全评审 | 安全评审 | security_session_wrapper_impl.cpp |
| 可测试性 | onRemoteReady/onError/onTerminated 可通过 Mock ExtensionSession 验证 | 单测 | security_ui_extension_pattern.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | DPI 策略影响错误码触发场景 | 需正确配置 DPI | 集成测试 | security_ui_extension_pattern.h |
| 折叠屏 | DPI 策略需响应折叠变化 | FOLLOW_HOST_DPI 时需监听 display 变化 | 集成测试 | security_session_wrapper_impl.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | SecurityUIExtensionPattern 继承 PlatformAccessibilityBase | AC-1.1 |
| 大字体 | 是 | DPI 策略影响字体大小 | — |
| 深色模式 | 否 | Extension 使用独立管线 | — |
| 多窗口/分屏 | 是 | onError 可能由分屏冲突触发 | AC-4.5 |
| 多用户 | 否 | Extension 运行在独立会话 | — |
| 版本升级 | 否 | API 20 起新增，无历史兼容负担 | — |
| 生态兼容 | 否 | 仅 static 范式，无 C-API | — |

---

## 行为场景

```gherkin
Feature: SecurityUIExtensionComponent 事件回调
  作为 应用开发者
  我想要 通过 onRemoteReady/onReceive/onError/onTerminated 监听 SecurityUIExtensionAbility 状态
  以便 在宿主页面中响应安全级 Extension 的连接/数据/错误/终止事件

  # ─── onRemoteReady ──────────────────────────

  Scenario: 注册 onRemoteReady 回调
    Given 一个 SecurityUIExtensionComponent 已创建
    When 调用 .onRemoteReady(callback)
    Then UIExtensionHub::SetOnRemoteReadyCallback 注册 callback

  Scenario: SecurityUIExtensionAbility 连接成功触发 onRemoteReady
    Given UIExtensionHub.onRemoteReadyCallback_ 已注册
    And SecuritySessionWrapperImpl 成功连接远端 SecurityUIExtensionAbility
    When SecuritySessionWrapperImpl::OnConnect 被调用
    Then SecurityUIExtensionPattern::FireOnRemoteReadyCallback
    And UIExtensionHub::FireOnRemoteReadyCallback(SecurityUIExtensionProxy)
    And callback 收到 SecurityUIExtensionProxy(sessionWrapper_, pattern_) 对象

  # ─── onReceive ──────────────────────────────

  Scenario: 注册 onReceive 回调
    Given 一个 SecurityUIExtensionComponent 已创建
    When 调用 .onReceive(callback)
    Then UIExtensionHub::SetOnReceiveCallback 注册 callback

  Scenario: 远端 sendData 触发 onReceive
    Given UIExtensionHub.onReceiveCallback_ 已注册
    And SecuritySessionWrapperImpl transferExtensionDataFunc_ 已注册
    When 远端 SecurityUIExtensionAbility 调用 sendData(WantParams)
    Then ExtensionSession 回调 transferExtensionDataFunc_
    And PostTask 到 UI 线程
    And SecurityUIExtensionPattern::FireOnReceiveCallback(WantParams)
    And UIExtensionHub::FireOnReceiveCallback(params)
    And callback 收到 Record<string, RecordData> 数据

  # ─── onError ─────────────────────────────────

  Scenario: 注册 onError 回调
    Given 一个 SecurityUIExtensionComponent 已创建
    When 调用 .onError(callback)
    Then SecurityUIExtensionPattern 注册 onError 回调

  Scenario: 启动失败触发 onError
    Given onError 回调已注册
    When SecurityUIExtensionAbility 启动失败
    Then SecurityUIExtensionPattern::FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, ...)
    And PlatformPattern::FireOnErrorCallback 分发
    And callback 收到 BusinessError

  Scenario: 异常退出触发 onError
    Given onError 回调已注册
    When SecuritySessionWrapperImpl::OnDisconnect(isAbnormal=true)
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, ...)
    And state_ = NONE
    And DestroySession

  Scenario: 级联嵌套禁止触发 onError
    Given onError 回调已注册
    And SecurityUIExtensionComponent 嵌套在另一个 UIExtensionComponent 中
    When 检测级联嵌套
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, PULL_FAIL_NAME, PULL_FAIL_MESSAGE)

  Scenario: 超时触发 onError
    Given onError 回调已注册
    When SecuritySessionWrapperImpl::OnExtensionTimeout
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT, EVENT_TIMEOUT_NAME, EVENT_TIMEOUT_MESSAGE)

  # ─── onTerminated ────────────────────────────

  Scenario: 注册 onTerminated 回调
    Given 一个 SecurityUIExtensionComponent 已创建
    When 调用 .onTerminated(callback)
    Then UIExtensionHub::SetOnTerminatedCallback 注册 callback

  Scenario: SecurityUIExtensionAbility 终止触发 onTerminated
    Given UIExtensionHub.onTerminatedCallback_ 已注册
    When 远端 SecurityUIExtensionAbility terminateSelf(code)
    Then SecuritySessionWrapperImpl → SecurityUIExtensionPattern::FireOnTerminatedCallback(code, wantWrap)
    And UIExtensionHub::FireOnTerminatedCallback(code, wantWrap)
    And callback 收到 TerminationInfo { code }

  Scenario: 正常断开触发 onTerminated
    Given UIExtensionHub.onTerminatedCallback_ 已注册
    When SecuritySessionWrapperImpl::OnDisconnect(isAbnormal=false)
    Then FireOnTerminatedCallback(0, nullptr)
    And callback 收到 TerminationInfo { code: 0 }

  Scenario: 重复终止不触发回调
    Given SecurityUIExtensionPattern.state_ = DESTRUCTION
    When onTerminated 事件到达
    Then onTerminatedCallback_ 检查 state_==DESTRUCTION
    And 不触发 callback

  # ─── Proxy receiver 注册/注销 ──────────────

  Scenario: Proxy 注册 asyncReceiver
    Given SecurityUIExtensionProxy 已通过 onRemoteReady 获取
    When 调用 proxy.on('asyncReceiverRegister', callback)
    Then SecurityUIExtensionPattern 注册 callback 到 onAsyncOnCallbackList_
    And 远端注册 async receiver 时触发 callback(proxy)

  Scenario: Proxy 注册 syncReceiver
    Given SecurityUIExtensionProxy 已通过 onRemoteReady 获取
    When 调用 proxy.on('syncReceiverRegister', callback)
    Then SecurityUIExtensionPattern 注册 callback 到 onSyncOnCallbackList_
    And 远端注册 sync receiver 时触发 callback(proxy)

  Scenario: Proxy 移除 asyncReceiver
    Given 已注册 asyncReceiver 的 SecurityUIExtensionProxy
    When 调用 proxy.off('asyncReceiverRegister', specificCallback)
    Then 从 onAsyncOnCallbackList_ 移除 specificCallback

  Scenario: Proxy 清空所有 asyncReceiver
    Given 已注册多个 asyncReceiver 的 SecurityUIExtensionProxy
    When 调用 proxy.off('asyncReceiverRegister')
    Then onAsyncOnCallbackList_ 被清空

  Scenario: Proxy 移除 syncReceiver
    Given 已注册 syncReceiver 的 SecurityUIExtensionProxy
    When 调用 proxy.off('syncReceiverRegister', specificCallback)
    Then 从 onSyncOnCallbackList_ 移除 specificCallback

  Scenario: Proxy 清空所有 syncReceiver
    Given 已注册多个 syncReceiver 的 SecurityUIExtensionProxy
    When 调用 proxy.off('syncReceiverRegister')
    Then onSyncOnCallbackList_ 被清空
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：onRemoteReady/onReceive/onError/onTerminated 注册与触发条件规格、Proxy receiver 注册/注销规格；不做什么：创建/选项/Proxy send/sendSync（Feat-01）、onResult/onRelease/onDrawReady（不支持）、C-API modifier（@noninterop））
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "SecurityUIExtensionPattern FireOnRemoteReadyCallback FireOnReceiveCallback FireOnTerminatedCallback FireOnErrorCallback 实现细节"
  - repo: "openharmony/ace_engine"
    query: "SecuritySessionWrapperImpl InitTransferExtensionDataFunc OnDisconnect OnExtensionTimeout 触发链"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionHub FireOnRemoteReadyCallback FireOnReceiveCallback FireOnTerminatedCallback SecurityUIExtensionProxy 分发"
  - repo: "openharmony/ace_engine"
    query: "SecurityUIExtensionProxy on off asyncReceiverRegister syncReceiverRegister 实现"
  - repo: "openharmony/ace_engine"
    query: "SecurityUIExtension 不支持 onResult onRelease onDrawReady 的原因"
```

**关键文档：**
- JS Bridge 层：`frameworks/bridge/declarative_frontend/jsview/js_security_ui_extension.cpp`
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/security_ui_extension_component/security_ui_extension_pattern.h`
- Pattern 层实现：`frameworks/core/components_ng/pattern/ui_extension/security_ui_extension_component/security_ui_extension_pattern.cpp:660-708`
- Hub 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_hub.h`
- SessionWrapper 层：`frameworks/core/components_ng/pattern/ui_extension/security_ui_extension_component/security_session_wrapper_impl.cpp`
- Proxy 层：`frameworks/core/components_ng/pattern/ui_extension/security_ui_extension_component/security_ui_extension_proxy.h`
