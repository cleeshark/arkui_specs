# 特性规格

> Func-05-12-03-Feat-02 UIExtensionComponent事件回调：固化 UIExtensionComponent onRemoteReady/onReceive/onResult/onRelease/onError/onTerminated/onDrawReady 事件回调注册、触发条件、回调数据格式、回调链路（SessionWrapperImpl→Pattern→EventHub/直接回调→ArkTS）的行为规格。onRemoteReady 触发链已在 Feat-01 覆盖，本规格补录事件注册与回调参数细节；onResult/onRelease 1.2 compat 废逝行为由 Feat-03 覆盖。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIExtensionComponent事件回调 |
| 特性编号 | Func-05-12-03-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10+（@systemapi）；onTerminated @since 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onRemoteReady 事件注册与回调参数规格 | 补录 onRemoteReady(callback: Callback<UIExtensionProxy>) 注册到 UIExtensionPattern.onRemoteReadyCallback_、回调参数 UIExtensionProxy 对象构造规格；触发链已在 Feat-01 覆盖 |
| ADDED | onReceive 事件回调规格 | 补录 onReceive(callback: OnReceiveCallback) 注册、SessionWrapperImpl::InitTransferExtensionDataFunc → FireOnReceiveCallback 触发链、WantParams 数据格式规格 |
| ADDED | onError 事件回调规格 | 补录 onError(callback: ErrorCallback) 注册、多场景触发条件（启动失败/前台失败/后台失败/销毁失败/异常退出/超时/级联禁止）、错误码/code/name/message 格式规格 |
| ADDED | onTerminated 事件回调规格 | 补录 onTerminated(callback: Callback<TerminationInfo>) 注册、SessionWrapperImpl OnDisconnect→FireOnTerminatedCallback 触发链、TerminationInfo { code, want? } 数据格式规格 |
| ADDED | onDrawReady 事件回调规格 | 补录 onDrawReady(callback: VoidCallback) 注册、UIExtCallbackEventId::ON_DRAW_FIRST → FireOnDrawReadyCallback 触发链、ReplacePlaceholderByContent 行为规格 |
| ADDED | onResult/onRelease 事件存在声明 | 声明 onResult/onRelease API 存在但仅用于 1.2 compat；详细废逝行为由 Feat-03 覆盖 |
| ADDED | C-API Static modifier 事件回调 stub/实现规格 | 补录 GENERATED_ArkUIUIExtensionComponentModifier setOnReceive/setOnError/setOnTerminated/setOnDrawReady stub（LOGE "not supported"）规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/03-ui-extension-component/design.md` | Baselined |
| Feat-01 | `specs/05-ui-components/12-embedded-display-components/03-ui-extension-component/Feat-01-ui-extension-creation-proxy-spec.md` | Baselined |

---

## 用户故事

### US-1: onRemoteReady 回调获取 UIExtensionProxy

**作为** 系统应用开发者,
**我想要** 通过 onRemoteReady(callback) 注册回调并在 UIExtensionAbility 连接成功时获取 UIExtensionProxy,
**以便** 使用 Proxy 进行宿主→远端数据通信。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `onRemoteReady(callback)` THEN UIExtensionModel::SetOnRemoteReady 将 callback 注册到 UIExtensionPattern.onRemoteReadyCallback_ | 正常 |
| AC-1.2 | WHEN UIExtensionAbility 连接成功 THEN SessionWrapperImpl::OnConnect → UIExtensionPattern::FireOnRemoteReadyCallback → callback 收到 UIExtensionProxy(sessionWrapper_, pattern_) 对象 | 正常 |
| AC-1.3 | WHEN callback 为空或无效 THEN 不注册回调；onRemoteReady 触发时无法传递 Proxy | 异常 |

### US-2: onReceive 数据接收回调

**作为** 系统应用开发者,
**我想要** 通过 onReceive(callback) 注册回调并在收到 ExtensionAbility 发送的数据时触发,
**以便** 处理远端 UIExtensionAbility 主动推送的数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `onReceive(callback)` THEN UIExtensionModel::SetOnReceive 将 callback 注册到 UIExtensionPattern.onReceiveCallback_ | 正常 |
| AC-2.2 | WHEN 远端 UIExtensionAbility 调用 sendData THEN SessionWrapperImpl::InitTransferExtensionDataFunc 注册 transferExtensionDataFunc_ → ExtensionSession 回调 → PostTask 到 UI 线程 → UIExtensionPattern::FireOnReceiveCallback(WantParams) → callback 收到 WantParams 数据 | 正常 |
| AC-2.3 | WHEN UIExtensionPattern 状态非 DESTRUCTION THEN onReceive 回调正常触发 | 正常 |
| AC-2.4 | WHEN callback 为空 THEN 不注册回调；onReceive 触发时数据丢失 | 异常 |

### US-3: onTerminated 终止处理回调

**作为** 系断应用开发者,
**我想要** 通过 onTerminated(callback) 注册回调并在 ExtensionAbility 终止时收到 TerminationInfo,
**以便** 根据终止码和可选 Want 执行后续处理逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `onTerminated(callback)` THEN UIExtensionModel::SetOnTerminated 将 callback 注册到 UIExtensionPattern.onTerminatedCallback_ | 正常 |
| AC-3.2 | WHEN 远端 UIExtensionAbility 调用 terminateWithResult(code, want) 且 onTerminatedCallback_ 已注册 THEN SessionWrapperImpl::InitTransferAbilityResultFunc 判断 IsCompatibleOldVersion()=false → FireOnTerminatedCallback(code, WantWrapOhos(want)) → callback 收到 TerminationInfo { code: number, want?: Want } | 正常 |
| AC-3.3 | WHEN SessionWrapperImpl::OnDisconnect 且 isAbnormal=false 且 IsCompatibleOldVersion()=false THEN FireOnTerminatedCallback(0, nullptr) → callback 收到 TerminationInfo { code: 0, want: undefined } | 正常 |
| AC-3.4 | WHEN UIExtensionPattern 状态已为 DESTRUCTION THEN onTerminated 回调不触发（state_ != DESTRUCTION 检查） | 边界 |
| AC-3.5 | WHEN onTerminated 回调触发 THEN UIExtensionPattern 状态变为 DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；若 sessionType_=UI_EXTENSION_ABILITY 且 usage_≠MODAL 则 DestroySession | 正常 |
| AC-3.6 | WHEN callback 为空 THEN 不注册回调；onTerminated 触发时无法传递 TerminationInfo | 异常 |

### US-4: onError 错误处理回调

**作为** 系统应用开发者,
**我想要** 通过 onError(callback) 注册回调并在 ExtensionAbility 加载或运行失败时收到错误信息,
**以便** 根据错误码执行错误恢复或提示逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `onError(callback)` THEN UIExtensionModel::SetOnError 将 callback 注册到 UIExtensionPattern.onErrorCallback_ | 正常 |
| AC-4.2 | WHEN onError 回调注册时 lastError_ 有缓存错误 THEN 立即 FireOnErrorCallback(lastError_.code, lastError_.name, lastError_.message) 并清空 lastError_ | 正常 |
| AC-4.3 | WHEN UIExtensionAbility 启动失败（foregroundCallback_ 收到 WSError）THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, START_FAIL_NAME, START_FAIL_MESSAGE) → callback(code, name, message) | 正常 |
| AC-4.4 | WHEN UIExtensionAbility 后台失败 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_BACKGROUND_FAILED, BACKGROUND_FAIL_NAME, BACKGROUND_FAIL_MESSAGE) | 正常 |
| AC-4.5 | WHEN UIExtensionAbility 销毁失败 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_DESTRUCTION_FAILED, TERMINATE_FAIL_NAME, TERMINATE_FAIL_MESSAGE) | 正常 |
| AC-4.6 | WHEN UIExtensionAbility 异常退出（OnDisconnect isAbnormal=true 且 IsCompatibleOldVersion()=false）THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, EXIT_ABNORMALLY_NAME, EXIT_ABNORMALLY_MESSAGE) | 正常 |
| AC-4.7 | WHEN UIExtensionAbility 超时 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT, EVENT_TIMEOUT_NAME, EVENT_TIMEOUT_MESSAGE) | 正常 |
| AC-4.8 | WHEN 级联嵌套禁止 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, PULL_FAIL_NAME, PULL_FAIL_MESSAGE) | 正常 |
| AC-4.9 | WHEN onError 回调触发 THEN UIExtensionPattern 状态变为 NONE；SetEventProxyFlag(EVENT_NONE)；若 name≠"extension_node_transparent" 则 sessionWrapper_->NotifyDestroy(false) + DestroySession；RemoveChildAtIndex(0) + MarkDirtyNode | 正常 |
| AC-4.10 | WHEN callback 为空 THEN 不注册回调；错误触发时缓存到 lastError_，下次注册时补发 | 异常 |

### US-5: onDrawReady 首帧绘制完成回调

**作为** 系统应用开发者,
**我想要** 通过 onDrawReady(callback) 注册回调并在 ExtensionAbility 首帧绘制完成时触发,
**以便** 在首帧就绪后执行 UI 状态更新（如移除 placeholder、显示内容）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `onDrawReady(callback)` THEN UIExtensionModel::SetOnDrawReady 将 callback 注册到 UIExtensionPattern.onDrawReadyCallback_ | 正常 |
| AC-5.2 | WHEN ExtensionAbility 首帧绘制完成 THEN UIExtensionPattern 收到 UIExtCallbackEventId::ON_DRAW_FIRST → FireOnDrawReadyCallback → ReplacePlaceholderByContent → callback() | 正常 |
| AC-5.3 | WHEN onDrawReady 回调触发 THEN 先执行 ReplacePlaceholderByContent 替换 placeholder 为 Extension 内容，再触发 callback | 正常 |
| AC-5.4 | WHEN callback 为空 THEN 不注册回调；onDrawReady 触发时仅执行 ReplacePlaceholderByContent | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1, R-2, R-3 | 已有实现 | 代码评审 | `js_ui_extension.cpp`, `ui_extension_pattern.cpp` |
| AC-2.1~2.4 | R-4, R-5, R-6, R-7 | 已有实现 | 代码评审 | `js_ui_extension.cpp:493-511`, `session_wrapper_impl.cpp:324-360`, `ui_extension_pattern.cpp:1672-1684` |
| AC-3.1~3.6 | R-8, R-9, R-10, R-11, R-12, R-13 | 已有实现 | 代码评审 | `js_ui_extension.cpp:608-632`, `session_wrapper_impl.cpp:280-321`, `ui_extension_pattern.cpp:1650-1670` |
| AC-4.1~4.10 | R-14, R-15, R-16, R-17, R-18, R-19, R-20, R-21, R-22, R-23 | 已有实现 | 代码评审 | `js_ui_extension.cpp:580-596`, `session_wrapper_impl.cpp`, `ui_extension_pattern.cpp:1601-1627` |
| AC-5.1~5.4 | R-24, R-25, R-26, R-27 | 已有实现 | 代码评审 | `js_ui_extension.cpp:644-656`, `ui_extension_pattern.cpp:2370-2376` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `onRemoteReady(callback)` 被调用 | JSUIExtension::OnRemoteReady 解析 callback → UIExtensionModel::SetOnRemoteReady → UIExtensionPattern::SetOnRemoteReadyCallback(std::move(callback)) | Feat-01 已覆盖触发链 | AC-1.1 |
| R-2 | 行为 | UIExtensionAbility 连接成功 | SessionWrapperImpl::OnConnect → UIExtensionPattern::FireOnRemoteReadyCallback → callback(UIExtensionProxy) | Proxy 封装 sessionWrapper_ + WeakPtr<Pattern> | AC-1.2 |
| R-3 | 异常 | callback 为空 | 不注册回调；onRemoteReady 触发时无法传递 Proxy | — | AC-1.3 |
| R-4 | 行为 | `onReceive(callback)` 被调用 | JSUIExtension::OnReceive 解析 callback → UIExtensionModel::SetOnReceive → UIExtensionPattern::SetOnReceiveCallback(std::move(callback)) | — | AC-2.1 |
| R-5 | 行为 | 远端 UIExtensionAbility sendData | SessionWrapperImpl::InitTransferExtensionDataFunc 注册 transferExtensionDataFunc_ → ExtensionSession 回调 → PostTask(UI线程) → UIExtensionPattern::FireOnReceiveCallback(WantParams) → callback(params) | PostTask 确保 UI 线程执行 | AC-2.2 |
| R-6 | 行为 | FireOnReceiveCallback 执行 | 检查 onReceiveCallback_ 是否存在 → ContainerScope(instanceId_) → onReceiveCallback_(params) | 状态检查：仅记录当前状态，不阻止回调 | AC-2.3 |
| R-7 | 异常 | callback 为空 | 不注册回调；onReceive 触发时数据丢失 | — | AC-2.4 |
| R-8 | 行为 | `onTerminated(callback)` 被调用 | JSUIExtension::OnTerminated 解析 callback → UIExtensionModel::SetOnTerminated → UIExtensionPattern::SetOnTerminatedCallback(std::move(callback)) | — | AC-3.1 |
| R-9 | 行为 | 远端 terminateWithResult 且 IsCompatibleOldVersion()=false | SessionWrapperImpl::InitTransferAbilityResultFunc 判断 sessionType_=UI_EXTENSION_ABILITY && !IsCompatibleOldVersion() → FireOnTerminatedCallback(code, WantWrapOhos(want)) → callback(code, wantWrap) | IsCompatibleOldVersion()=true 时走 onResult 路径（Feat-03） | AC-3.2 |
| R-10 | 行为 | OnDisconnect isAbnormal=false 且 !IsCompatibleOldVersion() | FireOnTerminatedCallback(0, nullptr) → callback 收到 { code: 0, want: undefined } | — | AC-3.3 |
| R-11 | 边界 | UIExtensionPattern.state_=DESTRUCTION 时 onTerminated 触发 | onTerminatedCallback_ 检查 state_ != DESTRUCTION；若已为 DESTRUCTION 则不回调 | 防止重复终止回调 | AC-3.4 |
| R-12 | 行为 | onTerminated 回调触发后 | state_ = DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；若 sessionType_=UI_EXTENSION_ABILITY && usage_≠MODAL && sessionWrapper_->IsSessionValid() → DestroySession | 非 MODAL 用法销毁 Session | AC-3.5 |
| R-13 | 异常 | callback 为空 | 不注册回调；onTerminated 触发时无法传递 TerminationInfo | — | AC-3.6 |
| R-14 | 行为 | `onError(callback)` 被调用 | JSUIExtension::OnError 解析 callback → UIExtensionModel::SetOnError → UIExtensionPattern::SetOnErrorCallback(std::move(callback))；若 lastError_ 有缓存错误则立即补发 | lastError_ 补发机制 | AC-4.1, AC-4.2 |
| R-15 | 行为 | 启动失败（foregroundCallback_ WSError） | SessionWrapperImpl::InitForegroundCallback → IsCompatibleOldVersion()=false → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, ...) → callback(code, name, message) | IsCompatibleOldVersion()=true 时使用原始 WSError code | AC-4.3 |
| R-16 | 行为 | 后台失败 | FireOnErrorCallback(ERROR_CODE_UIEXTENSION_BACKGROUND_FAILED, BACKGROUND_FAIL_NAME, BACKGROUND_FAIL_MESSAGE) | — | AC-4.4 |
| R-17 | 行为 | 销毁失败 | FireOnErrorCallback(ERROR_CODE_UIEXTENSION_DESTRUCTION_FAILED, TERMINATE_FAIL_NAME, TERMINATE_FAIL_MESSAGE) | — | AC-4.5 |
| R-18 | 行为 | 异常退出（OnDisconnect isAbnormal=true, !IsCompatibleOldVersion） | FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, EXIT_ABNORMALLY_NAME, EXIT_ABNORMALLY_MESSAGE) | — | AC-4.6 |
| R-19 | 行为 | 超时 | SessionWrapperImpl::OnExtensionTimeout → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT/LIFECYCLE_TIMEOUT, ...) | transparent 错误使用 ERROR_CODE_UIEXTENSION_TRANSPARENT | AC-4.7 |
| R-20 | 行为 | 级联嵌套禁止 | UIExtensionPattern::NotifyForeground/NotifyBackground 检查级联 → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, ...) | — | AC-4.8 |
| R-21 | 行为 | onError 回调触发后 | state_ = NONE；SetEventProxyFlag(EVENT_NONE)；若 !IsShowPlaceholder() → RemoveChildAtIndex(0) + MarkDirtyNode；若 name≠"extension_node_transparent" → NotifyDestroy(false) + DestroySession | name="extension_node_transparent" 时不销毁 Session | AC-4.9 |
| R-22 | 边界 | lastError_ 缓存 | SetOnErrorCallback 注册时检查 lastError_.code != 0 → 若有缓存错误则 swap 后 FireOnErrorCallback 补发 | 注册前发生的错误不丢失 | AC-4.2 |
| R-23 | 异常 | callback 为空 | 不注册回调；错误缓存到 lastError_ | — | AC-4.10 |
| R-24 | 行为 | `onDrawReady(callback)` 被调用 | JSUIExtension::OnDrawReady 解析 callback → UIExtensionModel::SetOnDrawReady → UIExtensionPattern::SetOnDrawReadyCallback(std::move(callback)) | — | AC-5.1 |
| R-25 | 行为 | ExtensionAbility 首帧绘制完成 | UIExtensionPattern 收到 UIExtCallbackEventId::ON_DRAW_FIRST → OnExtensionEvent → FireOnDrawReadyCallback → ReplacePlaceholderByContent → callback() | ON_DRAW_FIRST 由 ExtensionSession 回调触发 | AC-5.2 |
| R-26 | 行为 | FireOnDrawReadyCallback 执行 | 先 ReplacePlaceholderByContent 替换 placeholder → 再 onDrawReadyCallback_() | 先替换内容再回调 | AC-5.3 |
| R-27 | 异常 | callback 为空 | 不注册回调；FireOnDrawReadyCallback 仅执行 ReplacePlaceholderByContent | — | AC-5.4 |
| R-28 | 声明 | onResult/onRelease API 存在 | onResult(callback: OnResultCallback) 和 onRelease(callback: OnReleaseCallback) 在 UIExtensionComponent 上存在但仅用于 1.2 compat；详细废逝行为由 Feat-03 覆盖 | — | — |
| R-29 | 边界 | C-API Static modifier 事件 stub | GENERATED_ArkUIUIExtensionComponentModifier::setOnReceive/setOnError/setOnTerminated/setOnDrawReady 为 stub（LOGE "not supported"） | 仅 setOnRemoteReady 为实现 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3, R-1, R-2, R-3 | 代码评审 | onRemoteReady 注册与 Proxy 传递 |
| VM-2 | AC-2.1~2.4, R-4, R-5, R-6, R-7 | 代码评审 | onReceive 注册、触发链、WantParams 数据传递 |
| VM-3 | AC-3.1~3.6, R-8~R-13 | 代码评审 | onTerminated 注册、触发链、TerminationInfo 格式、状态检查 |
| VM-4 | AC-4.1~4.10, R-14~R-23 | 代码评审 | onError 注册、多场景触发、错误码格式、lastError_ 补发 |
| VM-5 | AC-5.1~5.4, R-24~R-27 | 代码评审 | onDrawReady 注册、ON_DRAW_FIRST 触发、ReplacePlaceholderByContent |
| VM-6 | R-28 | 代码评审 | onResult/onRelease API 存在声明（详细由 Feat-03 覆盖） |
| VM-7 | R-29 | C-API 单测 | Static modifier 事件 stub 行为 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `onRemoteReady(callback: Callback<UIExtensionProxy>)` | System | 远端连接就绪回调 | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |
| `onReceive(callback: OnReceiveCallback)` | System | 收到 Extension 数据回调 | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |
| `onResult(callback: OnResultCallback)` | System (1.2 compat) | Extension 返回结果回调 | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |
| `onRelease(callback: OnReleaseCallback)` | System (1.2 compat) | Extension 释放回调 | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |
| `onError(callback: ErrorCallback)` | System | 加载失败回调 | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |
| `onTerminated(callback: Callback<TerminationInfo>)` | System | Extension 终止回调 | `@internal/component/ets/ui_extension_component.d.ts` | 12 | @systemapi |
| `onDrawReady(callback: VoidCallback)` | System | 首帧绘制完成回调 | `@internal/component/ets/ui_extension_component.d.ts` | — | @systemapi |
| `TerminationInfo { code: number, want?: Want }` | System | 终止信息 | `@internal/component/ets/ui_extension_component.d.ts` | 12 | @systemapi |

**C-API (NDK) 接口：**

| Modifier 类型 | 属性枚举 | 功能 | 实现状态 | @since |
|---------------|----------|------|----------|--------|
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnRemoteReady` | 注册 onRemoteReady 回调 | 实现 | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnReceive` | 注册 onReceive 回调 | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnError` | 注册 onError 回调 | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnTerminated` | 注册 onTerminated 回调 | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnDrawReady` | 注册 onDrawReady 回调 | stub（LOGE "not supported"） | — |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `OnReceiveCallback` | `(data: { [key: string]: Object }) => void`（WantParams 映射） | `ui_extension_component.d.ts` |
| `OnResultCallback` | `(code: number, data: Want) => void` | `ui_extension_component.d.ts` |
| `OnReleaseCallback` | `(code: number) => void` | `ui_extension_component.d.ts` |
| `ErrorCallback` | `(code: number, name: string, message: string) => void` | `ui_extension_component.d.ts` |
| `TerminationInfo` | `{ code: number; want?: Want }` | `ui_extension_component.d.ts` |
| `UIExtensionProxy` | `interface { send, sendSync, on/off('asyncReceiverRegister'/'syncReceiverRegister') }` | `ui_extension_component.d.ts` |
| `WantParams` (C++) | `AAFwk::WantParams` — 远端传递的数据结构 | `session_wrapper_impl.cpp` |
| `ErrorMsg` (C++) | `struct { int32_t code = 0; std::string name; std::string message }` | `ui_extension_pattern.h` |

### 变更/废弃 API

onResult 和 onRelease 为 1.2 compat 废逝事件，详细行为由 Feat-03 覆盖。

---

## 接口规格

### 接口定义 — onRemoteReady(callback: Callback<UIExtensionProxy>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onRemoteReady(callback: Callback<UIExtensionProxy>)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |
| Feat-01 交叉 | 触发链已在 Feat-01 AC-2.1/R-4 覆盖；本规格补录注册细节 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | Callback<UIExtensionProxy> | 是 | — | callback 参数为 UIExtensionProxy 对象；Proxy 封装 sessionWrapper_ + WeakPtr<Pattern> |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | UIExtensionAbility 连接成功 | callback(UIExtensionProxy) | AC-1.2 |
| 2 | callback 为空 | 不注册回调 | AC-1.3 |

### 接口定义 — onReceive(callback: OnReceiveCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onReceive(callback: OnReceiveCallback)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | OnReceiveCallback (data: { [key: string]: Object }) => void | 是 | — | data 为 WantParams 到 Record<string, Object> 的映射 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 远端 UIExtensionAbility sendData | SessionWrapperImpl transferExtensionDataFunc_ → PostTask(UI) → FireOnReceiveCallback(WantParams) → callback(data) | AC-2.2 |
| 2 | callback 为空 | 不注册回调 | AC-2.4 |

### 接口定义 — onError(callback: ErrorCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onError(callback: ErrorCallback)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.10 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | ErrorCallback (code: number, name: string, message: string) => void | 是 | — | code 为预定义错误码；name 为错误名称；message 为错误描述 |

**错误码定义：**

| 错误码 | 名称 | 触发场景 | 关联 AC |
|--------|------|----------|---------|
| ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED | START_FAIL_NAME | 启动失败 | AC-4.3 |
| ERROR_CODE_UIEXTENSION_BACKGROUND_FAILED | BACKGROUND_FAIL_NAME | 后台失败 | AC-4.4 |
| ERROR_CODE_UIEXTENSION_DESTRUCTION_FAILED | TERMINATE_FAIL_NAME | 销毁失败 | AC-4.5 |
| ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY | EXIT_ABNORMALLY_NAME | 异常退出 | AC-4.6 |
| ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT | EVENT_TIMEOUT_NAME | 超时 | AC-4.7 |
| ERROR_CODE_UIEXTENSION_FORBID_CASCADE | PULL_FAIL_NAME | 级联嵌套禁止 | AC-4.8 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 启动失败 | callback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, START_FAIL_NAME, START_FAIL_MESSAGE) | AC-4.3 |
| 2 | 后台失败 | callback(ERROR_CODE_UIEXTENSION_BACKGROUND_FAILED, ...) | AC-4.4 |
| 3 | 销毁失败 | callback(ERROR_CODE_UIEXTENSION_DESTRUCTION_FAILED, ...) | AC-4.5 |
| 4 | 异常退出 | callback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, ...) | AC-4.6 |
| 5 | 超时 | callback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT, ...) | AC-4.7 |
| 6 | 级联禁止 | callback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, ...) | AC-4.8 |
| 7 | 注册时 lastError_ 有缓存 | 立即补发缓存错误 | AC-4.2 |
| 8 | callback 为空 | 错误缓存到 lastError_ | AC-4.10 |
| 9 | onError 触发后 | state_=NONE；DestroySession；RemoveChild | AC-4.9 |

### 接口定义 — onTerminated(callback: Callback<TerminationInfo>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onTerminated(callback: Callback<TerminationInfo>)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.6 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | Callback<TerminationInfo> (info: { code: number, want?: Want }) => void | 是 | — | code 为终止码；want 为可选 Want 参数 |

**TerminationInfo 定义：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | number | 是 | 终止码；0 表示正常终止 |
| want | Want | 否 | 终止时携带的 Want 数据；OnDisconnect 正常终止时为 undefined |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 远端 terminateWithResult 且 !IsCompatibleOldVersion | callback({ code, want }) | AC-3.2 |
| 2 | OnDisconnect isAbnormal=false 且 !IsCompatibleOldVersion | callback({ code: 0, want: undefined }) | AC-3.3 |
| 3 | state_=DESTRUCTION 时不回调 | 不触发 callback | AC-3.4 |
| 4 | onTerminated 触发后 | state_=DESTRUCTION；DestroySession（非 MODAL） | AC-3.5 |
| 5 | callback 为空 | 不注册回调 | AC-3.6 |

### 接口定义 — onDrawReady(callback: VoidCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onDrawReady(callback: VoidCallback)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-5.1, AC-5.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | VoidCallback () => void | 是 | — | 无参数回调 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | ExtensionAbility 首帧绘制完成 | ReplacePlaceholderByContent → callback() | AC-5.2, AC-5.3 |
| 2 | callback 为空 | 仅执行 ReplacePlaceholderByContent | AC-5.4 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（onRemoteReady/onReceive/onError/onResult/onRelease）；API 12（onTerminated）
- **API 版本号策略:** @since 10 为基础事件接口；@since 12 增加 onTerminated；onResult/onRelease 1.2 compat 废逝行为由 Feat-03 覆盖

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| onRemoteReady 触发链已在 Feat-01 覆盖 | 本规格仅补录注册细节，不重复触发链规格 | AC-1.1 |
| IsCompatibleOldVersion() 决定 onResult vs onTerminated 路径 | onTerminatedCallback_=nullptr 时走 onResult 路径（1.2 compat）；否则走 onTerminated 路径 | AC-3.2 |
| onError lastError_ 补发机制 | 注册 onError 之前发生的错误缓存到 lastError_，注册后立即补发 | AC-4.2 |
| FireOnDrawReadyCallback 先 ReplacePlaceholderByContent | 确保首帧绘制完成时 placeholder 已被替换 | AC-5.3 |
| C-API Static modifier 事件回调为 stub | 仅 setOnRemoteReady 为实现；其余事件为 stub | — |
| UIExtensionPattern.state_ 防止重复回调 | onTerminated/onResult 检查 state_!=DESTRUCTION 防止重复触发 | AC-3.4 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 事件回调通过 PostTask 到 UI 线程，延迟由 TaskExecutor 决定 | 集成测试 | session_wrapper_impl.cpp |
| 安全 | @systemapi 限制系统应用使用 | API 评审 | ui_extension_component.d.ts |
| 可测试性 | onReceive/onError/onTerminated 可通过 Mock ExtensionSession 验证 | 单测 | ui_extension_pattern.cpp |
| 可测试性 | onError lastError_ 补发可通过延迟注册验证 | 单测 | ui_extension_pattern.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | 无差异 | — | 集成测试 | — |
| 折叠屏 | onDrawReady 触发后需正确 ReplacePlaceholderByContent | 需监听 display 变化 | 集成测试 | ui_extension_pattern.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | onError 事件不影响无障碍树 | — |
| 大字体 | 否 | 事件回调不涉及字体 | — |
| 深色模式 | 否 | 事件回调不涉及配色 | — |
| 多窗口/分屏 | 是 | onError 可能由分屏冲突触发 | AC-4.8 |
| 多用户 | 否 | Extension 运行在独立进程 | — |
| 版本升级 | 是 | onResult/onRelease 废逝策略影响旧版本兼容 | AC-3.2 |
| 生态兼容 | 是 | onTerminated 替代 onResult/onRelease 的新应用推荐路径 | AC-3.2 |

---

## 行为场景

```gherkin
Feature: UIExtensionComponent 事件回调
  作为 系统应用开发者
  我想要 通过 onRemoteReady/onReceive/onError/onTerminated/onDrawReady 监听 UIExtensionAbility 状态
  以便 在宿主页面中响应远端 Extension 的连接/数据/错误/终止/首帧事件

  # ─── onRemoteReady ──────────────────────────

  Scenario: 注册 onRemoteReady 回调
    Given 一个 UIExtensionComponent 已创建
    When 调用 .onRemoteReady(callback)
    Then UIExtensionModel::SetOnRemoteReady 注册 callback 到 UIExtensionPattern.onRemoteReadyCallback_

  Scenario: UIExtensionAbility 连接成功触发 onRemoteReady
    Given UIExtensionPattern.onRemoteReadyCallback_ 已注册
    And SessionWrapperImpl 成功连接远端 UIExtensionAbility
    When SessionWrapperImpl::OnConnect 被调用
    Then UIExtensionPattern::FireOnRemoteReadyCallback 被触发
    And callback 收到 UIExtensionProxy(sessionWrapper_, pattern_) 对象

  # ─── onReceive ───────────────────────────────

  Scenario: 注册 onReceive 回调
    Given 一个 UIExtensionComponent 已创建
    When 调用 .onReceive(callback)
    Then UIExtensionModel::SetOnReceive 注册 callback 到 UIExtensionPattern.onReceiveCallback_

  Scenario: 远端 sendData 触发 onReceive
    Given UIExtensionPattern.onReceiveCallback_ 已注册
    And SessionWrapperImpl transferExtensionDataFunc_ 已注册
    When 远端 UIExtensionAbility 调用 sendData(WantParams)
    Then ExtensionSession 回调 transferExtensionDataFunc_
    And PostTask 到 UI 线程
    And UIExtensionPattern::FireOnReceiveCallback(WantParams)
    And callback 收到 WantParams 数据

  # ─── onError ─────────────────────────────────

  Scenario: 注册 onError 回调
    Given 一个 UIExtensionComponent 已创建
    When 调用 .onError(callback)
    Then UIExtensionModel::SetOnError 注册 callback 到 UIExtensionPattern.onErrorCallback_

  Scenario: 注册 onError 时补发缓存错误
    Given UIExtensionPattern.lastError_ 有缓存错误 { code: 123, name: "err", message: "msg" }
    When 调用 .onError(callback)
    Then swap lastError_ → ErrorMsg
    And 立即 FireOnErrorCallback(123, "err", "msg")
    And callback 收到缓存错误

  Scenario: 启动失败触发 onError
    Given UIExtensionPattern.onErrorCallback_ 已注册
    And SessionWrapperImpl foregroundCallback_ 收到 WSError
    When UIExtensionAbility 启动失败
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, START_FAIL_NAME, START_FAIL_MESSAGE)
    And callback 收到错误码

  Scenario: 异常退出触发 onError
    Given UIExtensionPattern.onErrorCallback_ 已注册
    And IsCompatibleOldVersion() 返回 false
    When SessionWrapperImpl::OnDisconnect 且 isAbnormal=true
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, ...)
    And state_ = NONE
    And DestroySession 执行

  Scenario: 级联嵌套禁止触发 onError
    Given UIExtensionPattern.onErrorCallback_ 已注册
    And UIExtensionComponent 嵌套在另一个 UIExtensionComponent 中
    When NotifyForeground 检测级联嵌套
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, PULL_FAIL_NAME, PULL_FAIL_MESSAGE)

  # ─── onTerminated ────────────────────────────

  Scenario: 注册 onTerminated 回调
    Given 一个 UIExtensionComponent 已创建
    When 调用 .onTerminated(callback)
    Then UIExtensionModel::SetOnTerminated 注册 callback 到 UIExtensionPattern.onTerminatedCallback_

  Scenario: 远端 terminateWithResult 触发 onTerminated
    Given UIExtensionPattern.onTerminatedCallback_ 已注册
    And IsCompatibleOldVersion() 返回 false
    When 远端 UIExtensionAbility 调用 terminateWithResult(0, want)
    Then FireOnTerminatedCallback(0, WantWrapOhos(want))
    And callback 收到 TerminationInfo { code: 0, want }

  Scenario: 正常断开触发 onTerminated
    Given UIExtensionPattern.onTerminatedCallback_ 已注册
    And IsCompatibleOldVersion() 返回 false
    When SessionWrapperImpl::OnDisconnect 且 isAbnormal=false
    Then FireOnTerminatedCallback(0, nullptr)
    And callback 收到 TerminationInfo { code: 0, want: undefined }

  Scenario: 重复终止不触发回调
    Given UIExtensionPattern.state_ = DESTRUCTION
    When onTerminated 事件到达
    Then onTerminatedCallback_ 检查 state_==DESTRUCTION
    And 不触发 callback

  # ─── onDrawReady ─────────────────────────────

  Scenario: 注册 onDrawReady 回调
    Given 一个 UIExtensionComponent 已创建
    When 调用 .onDrawReady(callback)
    Then UIExtensionModel::SetOnDrawReady 注册 callback 到 UIExtensionPattern.onDrawReadyCallback_

  Scenario: 首帧绘制完成触发 onDrawReady
    Given UIExtensionPattern.onDrawReadyCallback_ 已注册
    When UIExtensionPattern 收到 UIExtCallbackEventId::ON_DRAW_FIRST
    Then ReplacePlaceholderByContent 替换 placeholder 为 Extension 内容
    And onDrawReadyCallback_() 触发 callback

  # ─── C-API Static Modifier Stub ─────────────

  Scenario: C-API Static modifier setOnReceive stub
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIUIExtensionComponentModifier::setOnReceive(node, callback)
    Then 输出 LOGE "not supported"，不修改 FrameNode 状态

  Scenario: C-API Static modifier setOnError stub
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIUIExtensionComponentModifier::setOnError(node, callback)
    Then 输出 LOGE "not supported"，不修改 FrameNode 状态

  Scenario: C-API Static modifier setOnTerminated stub
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIUIExtensionComponentModifier::setOnTerminated(node, callback)
    Then 输出 LOGE "not supported"，不修改 FrameNode 状态

  Scenario: C-API Static modifier setOnDrawReady stub
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIUIExtensionComponentModifier::setOnDrawReady(node, callback)
    Then 输出 LOGE "not supported"，不修改 FrameNode 状态
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：onRemoteReady/onReceive/onError/onTerminated/onDrawReady 注册与触发条件规格；不做什么：创建/选项/Proxy send/sendSync/on-offReceiver（Feat-01）、onResult/onRelease 废逝行为（Feat-03）、Embedded/Security/Dynamic/Isolated 组件事件）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern FireOnReceiveCallback FireOnTerminatedCallback FireOnErrorCallback FireOnDrawReadyCallback 实现细节"
  - repo: "openharmony/ace_engine"
    query: "SessionWrapperImpl InitTransferExtensionDataFunc InitTransferAbilityResultFunc InitForegroundCallback InitBackgroundCallback InitDestructionCallback 触发链"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern IsCompatibleOldVersion 如何决定 onResult vs onTerminated 路径"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern onError lastError_ 补发机制 SetOnErrorCallback"
  - repo: "openharmony/ace_engine"
    query: "C-API UIExtensionComponentModifier setOnReceive/setOnError/setOnTerminated/setOnDrawReady stub 行为"
  - repo: "openharmony/ace_engine"
    query: "UIExtCallbackEventId ON_DRAW_FIRST 触发条件和 FireOnDrawReadyCallback ReplacePlaceholderByContent"
```

**关键文档：**
- JS Bridge 层：`frameworks/bridge/declarative_frontend/jsview/js_ui_extension.cpp`
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.h`
- SessionWrapper 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/session_wrapper_impl.cpp`
- C-API Modifier：`frameworks/core/interfaces/native/implementation/ui_extension_component_modifier.cpp`
