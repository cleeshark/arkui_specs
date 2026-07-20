# 特性规格

> Func-05-12-04-Feat-02 EmbeddedComponent事件回调：固化 EmbeddedComponent onTerminated/onError/onDrawReady 事件回调注册、触发条件、回调数据格式、回调链路（SessionWrapperImpl→Pattern→直接回调→ArkTS）的行为规格。EmbeddedComponent 使用 UIExtensionPattern（sessionType_=EMBEDDED_UI_EXTENSION）共享回调基础设施，但仅支持三种事件回调。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | EmbeddedComponent事件回调 |
| 特性编号 | Func-05-12-04-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 12+（@atomicservice @stagemodelonly）；onDrawReady @since 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onTerminated 事件回调规格 | 补录 onTerminated(callback: Callback<TerminationInfo>) 注册到 UIExtensionPattern.onTerminatedCallback_、SessionWrapperImpl OnDisconnect→FireOnTerminatedCallback 触发链、TerminationInfo { code, want? } 数据格式规格 |
| ADDED | onError 事件回调规格 | 补录 onError(callback: ErrorCallback) 注册、多场景触发条件（启动失败/异常退出/超时/级联禁止）、错误码/code/name/message 格式规格 |
| ADDED | onDrawReady 事件回调规格 | 补录 onDrawReady(callback: Callback<void>) @since 26.0.0 注册、UIExtCallbackEventId::ON_DRAW_FIRST → FireOnDrawReadyCallback 触发链、ReplacePlaceholderByContent 行为规格 |
| ADDED | C-API Dynamic modifier 事件回调规格 | 补录 ArkUIEmbeddedComponentModifier setOnError/resetOnError/setOnTerminated/resetOnTerminated 规格 |
| ADDED | C-API Static modifier 事件 stub 规格 | 补录 GENERATED_ArkUIEmbeddedComponentModifier SetOnTerminatedImpl/SetOnErrorImpl/SetOnDrawReadyImpl stub（LOGE "not supported"）规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/04-embedded-component/design.md` | Baselined |
| Feat-01 | `specs/05-ui-components/12-embedded-display-components/04-embedded-component/Feat-01-embedded-creation-dpi-spec.md` | Baselined |

---

## 用户故事

### US-1: onTerminated 终止处理回调

**作为** 三方应用开发者,
**我想要** 通过 onTerminated(callback) 注册回调并在 ExtensionAbility 终止时收到 TerminationInfo,
**以便** 根据终止码和可选 Want 执行后续处理逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `onTerminated(callback)` THEN JSEmbeddedComponent::OnTerminated 解析 callback → UIExtensionModel::SetOnTerminated 注册到 UIExtensionPattern.onTerminatedCallback_ | 正常 |
| AC-1.2 | WHEN 远端 ExtensionAbility 调用 terminateWithResult(code, want) 且 sessionType_=EMBEDDED_UI_EXTENSION THEN SessionWrapperImpl::InitTransferAbilityResultFunc 判断 !IsCompatibleOldVersion() → FireOnTerminatedCallback(code, WantWrapOhos(want)) → callback 收到 TerminationInfo { code: number, want?: Want } | 正常 |
| AC-1.3 | WHEN SessionWrapperImpl::OnDisconnect 且 isAbnormal=false 且 !IsCompatibleOldVersion() THEN FireOnTerminatedCallback(0, nullptr) → callback 收到 TerminationInfo { code: 0, want: undefined } | 正常 |
| AC-1.4 | WHEN UIExtensionPattern.state_=DESTRUCTION THEN onTerminated 回调不触发（state_ != DESTRUCTION 检查） | 边界 |
| AC-1.5 | WHEN onTerminated 回调触发 THEN state_=DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；DestroySession（sessionType_=EMBEDDED_UI_EXTENSION 且 usage_=EMBEDDED） | 正常 |
| AC-1.6 | WHEN callback 为空 THEN 不注册回调；onTerminated 触发时无法传递 TerminationInfo | 异常 |

### US-2: onError 错误处理回调

**作为** 三方应用开发者,
**我想要** 通过 onError(callback) 注册回调并在 ExtensionAbility 加载或运行失败时收到错误信息,
**以便** 根据错误码执行错误恢复或提示逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `onError(callback)` THEN JSEmbeddedComponent::OnError 解析 callback → UIExtensionModel::SetOnError 注册到 UIExtensionPattern.onErrorCallback_ | 正常 |
| AC-2.2 | WHEN onError 回调注册时 lastError_ 有缓存错误 THEN 立即 FireOnErrorCallback(lastError_.code, lastError_.name, lastError_.message) 并清空 lastError_ | 正常 |
| AC-2.3 | WHEN UIExtensionAbility 启动失败 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, START_FAIL_NAME, START_FAIL_MESSAGE) → callback(code, name, message) | 正常 |
| AC-2.4 | WHEN UIExtensionAbility 异常退出（OnDisconnect isAbnormal=true 且 !IsCompatibleOldVersion）THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, EXIT_ABNORMALLY_NAME, EXIT_ABNORMALLY_MESSAGE) | 正常 |
| AC-2.5 | WHEN UIExtensionAbility 超时 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT, EVENT_TIMEOUT_NAME, EVENT_TIMEOUT_MESSAGE) | 正常 |
| AC-2.6 | WHEN 级联嵌套禁止 THEN FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, PULL_FAIL_NAME, PULL_FAIL_MESSAGE) | 正常 |
| AC-2.7 | WHEN onError 回调触发 THEN state_=NONE；SetEventProxyFlag(EVENT_NONE)；DestroySession；RemoveChildAtIndex(0) + MarkDirtyNode | 正常 |
| AC-2.8 | WHEN C-API 设置 NODE_EMBEDDED_COMPONENT_OPTION 且 option->onError 非空 THEN ArkUIEmbeddedComponentModifier::setEmbeddedComponentOption → UIExtensionAdapter::SetEmbeddedComponentOnError → Pattern::SetOnErrorCallback | 正常 |
| AC-2.9 | WHEN callback 为空 THEN 不注册回调；错误缓存到 lastError_ | 异常 |

### US-3: onDrawReady 首帧绘制完成回调

**作为** 三方应用开发者,
**我想要** 通过 onDrawReady(callback) 注册回调并在 ExtensionAbility 首帧绘制完成时触发,
**以便** 在首帧就绪后执行 UI 状态更新（如移除 placeholder、显示内容）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `onDrawReady(callback)` THEN JSEmbeddedComponent::OnDrawReady 解析 callback → UIExtensionModel::SetOnDrawReady 注册到 UIExtensionPattern.onDrawReadyCallback_ | 正常 |
| AC-3.2 | WHEN ExtensionAbility 首帧绘制完成 THEN UIExtensionPattern 收到 UIExtCallbackEventId::ON_DRAW_FIRST → FireOnDrawReadyCallback → ReplacePlaceholderByContent → callback() | 正常 |
| AC-3.3 | WHEN onDrawReady 回调触发 THEN 先执行 ReplacePlaceholderByContent 替换 placeholder 为 Extension 内容，再触发 callback | 正常 |
| AC-3.4 | WHEN callback 为空 THEN 不注册回调；onDrawReady 触发时仅执行 ReplacePlaceholderByContent | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1, R-2, R-3, R-4, R-5, R-6 | 已有实现 | 代码评审 | `js_ui_extension.cpp:608-632`, `ui_extension_pattern.cpp:1650-1670`, `session_wrapper_impl.cpp` |
| AC-2.1~2.9 | R-7, R-8, R-9, R-10, R-11, R-12, R-13, R-14, R-15 | 已有实现 | 代码评审 + C-API 单测 | `js_ui_extension.cpp:580-596`, `ui_extension_pattern.cpp:1601-1627`, `embeddedComponent_modifier.cpp` |
| AC-3.1~3.4 | R-16, R-17, R-18, R-19 | 已有实现 | 代码评审 | `js_ui_extension.cpp:644-656`, `ui_extension_pattern.cpp:2370-2376` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `onTerminated(callback)` 被调用 | JSEmbeddedComponent::OnTerminated 解析 callback → UIExtensionModel::SetOnTerminated → UIExtensionPattern::SetOnTerminatedCallback(std::move(callback)) | EMBEDDED_UI_EXTENSION 不走 onResult compat 路径 | AC-1.1 |
| R-2 | 行为 | 远端 terminateWithResult 且 sessionType_=EMBEDDED_UI_EXTENSION | SessionWrapperImpl::InitTransferAbilityResultFunc 判断 !IsCompatibleOldVersion() → FireOnTerminatedCallback(code, WantWrapOhos(want)) → callback 收到 TerminationInfo | EMBEDDED_UI_EXTENSION IsCompatibleOldVersion()=false（sessionType≠UI_EXTENSION_ABILITY） | AC-1.2 |
| R-3 | 行为 | OnDisconnect isAbnormal=false 且 !IsCompatibleOldVersion() | FireOnTerminatedCallback(0, nullptr) → callback 收到 { code: 0, want: undefined } | — | AC-1.3 |
| R-4 | 边界 | UIExtensionPattern.state_=DESTRUCTION 时 onTerminated 触发 | onTerminatedCallback_ 检查 state_ != DESTRUCTION；若已为 DESTRUCTION 则不回调 | 防止重复终止回调 | AC-1.4 |
| R-5 | 行为 | onTerminated 回调触发后 | state_ = DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；EMBEDDED_UI_EXTENSION 且 usage_=EMBEDDED → DestroySession | EMBEDDED 类型总是销毁 Session | AC-1.5 |
| R-6 | 异常 | callback 为空 | 不注册回调 | — | AC-1.6 |
| R-7 | 行为 | `onError(callback)` 被调用 | JSEmbeddedComponent::OnError 解析 callback → UIExtensionModel::SetOnError → UIExtensionPattern::SetOnErrorCallback(std::move(callback))；若 lastError_ 有缓存错误则立即补发 | lastError_ 补发机制 | AC-2.1, AC-2.2 |
| R-8 | 行为 | 启动失败 | SessionWrapperImpl::InitForegroundCallback → FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, START_FAIL_NAME, START_FAIL_MESSAGE) → callback(code, name, message) | EMBEDDED 不走 compat 路径 | AC-2.3 |
| R-9 | 行为 | 异常退出（OnDisconnect isAbnormal=true, !IsCompatibleOldVersion） | FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, EXIT_ABNORMALLY_NAME, EXIT_ABNORMALLY_MESSAGE) | — | AC-2.4 |
| R-10 | 行为 | 超时 | FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT, EVENT_TIMEOUT_NAME, EVENT_TIMEOUT_MESSAGE) | — | AC-2.5 |
| R-11 | 行为 | 级联嵌套禁止 | FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, PULL_FAIL_NAME, PULL_FAIL_MESSAGE) | EMBEDDED 也受级联限制 | AC-2.6 |
| R-12 | 行为 | onError 回调触发后 | state_ = NONE；SetEventProxyFlag(EVENT_NONE)；DestroySession；RemoveChildAtIndex(0) + MarkDirtyNode | name≠"extension_node_transparent" 时销毁 Session | AC-2.7 |
| R-13 | 边界 | lastError_ 缓存 | SetOnErrorCallback 注册时检查 lastError_.code != 0 → swap 后 FireOnErrorCallback 补发 | 注册前发生的错误不丢失 | AC-2.2 |
| R-14 | 行为 | C-API NODE_EMBEDDED_COMPONENT_OPTION onError | setEmbeddedComponentOption → 提取 option->onError → UIExtensionAdapter::SetEmbeddedComponentOnError → Pattern::SetOnErrorCallback | — | AC-2.8 |
| R-15 | 异常 | callback 为空 | 不注册回调；错误缓存到 lastError_ | — | AC-2.9 |
| R-16 | 行为 | `onDrawReady(callback)` 被调用 | JSEmbeddedComponent::OnDrawReady 解析 callback → UIExtensionModel::SetOnDrawReady → UIExtensionPattern::SetOnDrawReadyCallback(std::move(callback)) | @since 26.0.0 | AC-3.1 |
| R-17 | 行为 | ExtensionAbility 首帧绘制完成 | UIExtCallbackEventId::ON_DRAW_FIRST → FireOnDrawReadyCallback → ReplacePlaceholderByContent → callback() | — | AC-3.2 |
| R-18 | 行为 | FireOnDrawReadyCallback 执行 | 先 ReplacePlaceholderByContent → 再 onDrawReadyCallback_() | 先替换内容再回调 | AC-3.3 |
| R-19 | 异常 | callback 为空 | 不注册回调；FireOnDrawReadyCallback 仅执行 ReplacePlaceholderByContent | — | AC-3.4 |
| R-20 | 边界 | EmbeddedComponent 不支持 onResult/onRelease/onRemoteReady（事件级） | sessionType_=EMBEDDED_UI_EXTENSION 时 IsCompatibleOldVersion()=false；无 onResult/onRelease compat 路径；onRemoteReady 仅用于 UIExtensionComponent | EMBEDDED 与 UI_EXTENSION_ABILITY 事件集差异 | — |
| R-21 | 边界 | C-API Static modifier 事件 stub | GENERATED_ArkUIEmbeddedComponentModifier::SetOnTerminatedImpl/SetOnErrorImpl/SetOnDrawReadyImpl 为 stub（LOGE "not supported"） | 仅 ConstructImpl 有效 | — |
| R-22 | 边界 | C-API Dynamic modifier resetOnError/resetOnTerminated | setOnError → 注册 Pattern::SetOnErrorCallback；resetOnError → 设置 nullptr；setOnTerminated → 注册 Pattern::SetOnTerminatedCallback；resetOnTerminated → 设置 nullptr | — | AC-2.8 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.6, R-1~R-6 | 代码评审 | onTerminated 注册、触发链、TerminationInfo 格式、状态检查 |
| VM-2 | AC-2.1~2.7, R-7~R-12, R-14 | 代码评审 + C-API 单测 | onError 注册、多场景触发、错误码格式、lastError_ 补发、C-API |
| VM-3 | AC-2.8~2.9, R-14, R-15, R-22 | C-API 单测 | Dynamic modifier onError/onTerminated/reset |
| VM-4 | AC-3.1~3.4, R-16~R-19 | 代码评审 | onDrawReady 注册、ON_DRAW_FIRST 触发、ReplacePlaceholderByContent |
| VM-5 | R-20 | 代码评审 | EmbeddedComponent 不支持 onResult/onRelease/onRemoteReady |
| VM-6 | R-21 | 代码评审 | Static modifier 事件 stub |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `onTerminated(callback: Callback<TerminationInfo>)` | AtomicService | Extension 终止回调 | SDK repo | 12 | @atomicservice |
| `onError(callback: ErrorCallback)` | AtomicService | 加载失败回调 | SDK repo | 12 | @atomicservice |
| `onDrawReady(callback: Callback<void>)` | AtomicService | 首帧绘制完成回调 | SDK repo | 26.0.0 | @atomicservice |
| `TerminationInfo { code: number, want?: Want }` | AtomicService | 终止信息 | SDK repo | 12 | @atomicservice |

**C-API (NDK) 接口：**

| Modifier 类型 | 属性枚举/接口 | 功能 | @since |
|---------------|---------------|------|--------|
| Dynamic | `ArkUIEmbeddedComponentModifier::setOnTerminated` | 注册 onTerminated 回调 | 20 |
| Dynamic | `ArkUIEmbeddedComponentModifier::resetOnTerminated` | 重置 onTerminated 回调 | 20 |
| Dynamic | `ArkUIEmbeddedComponentModifier::setOnError` | 注册 onError 回调 | 20 |
| Dynamic | `ArkUIEmbeddedComponentModifier::resetOnError` | 重置 onError 回调 | 20 |
| Static (Arkoala) | `GENERATED_ArkUIEmbeddedComponentModifier::SetOnTerminatedImpl` | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIEmbeddedComponentModifier::SetOnErrorImpl` | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIEmbeddedComponentModifier::SetOnDrawReadyImpl` | stub（LOGE "not supported"） | — |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `TerminationInfo` | `{ code: number; want?: Want }` | SDK repo |
| `ErrorCallback` (ArkTS) | `(code: number, name: string, message: string) => void` | SDK repo |
| `ErrorMsg` (C++) | `struct { int32_t code = 0; std::string name; std::string message }` | `ui_extension_pattern.h` |
| `UIExtensionAdapter` (C++) | `class { SetEmbeddedComponentOnError, SetEmbeddedComponentOnTerminated }` | `ui_extension_adapter.h` |

### 变更/废弃 API

无变更/废弃 API（EmbeddedComponent 不支持 onResult/onRelease，无 compat 废逝）。

---

## 接口规格

### 接口定义 — onTerminated(callback: Callback<TerminationInfo>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `EmbeddedComponentAttribute onTerminated(callback: Callback<TerminationInfo>)` |
| 返回值 | `EmbeddedComponentAttribute` — 属性链对象 |
| 开放范围 | AtomicService (@atomicservice @stagemodelonly) |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.6 |

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
| 1 | 远端 terminateWithResult | FireOnTerminatedCallback(code, wantWrap) → callback({ code, want }) | AC-1.2 |
| 2 | OnDisconnect isAbnormal=false | FireOnTerminatedCallback(0, nullptr) → callback({ code: 0, want: undefined }) | AC-1.3 |
| 3 | state_=DESTRUCTION | 不触发 callback | AC-1.4 |
| 4 | onTerminated 触发后 | state_=DESTRUCTION；DestroySession | AC-1.5 |
| 5 | callback 为空 | 不注册回调 | AC-1.6 |

### 接口定义 — onError(callback: ErrorCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `EmbeddedComponentAttribute onError(callback: ErrorCallback)` |
| 返回值 | `EmbeddedComponentAttribute` — 属性链对象 |
| 开放范围 | AtomicService (@atomicservice @stagemodelonly) |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.9 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | ErrorCallback (code: number, name: string, message: string) => void | 是 | — | code 为预定义错误码 |

**错误码定义：**

| 错误码 | 名称 | 触发场景 | 关联 AC |
|--------|------|----------|---------|
| ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED | START_FAIL_NAME | 启动失败 | AC-2.3 |
| ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY | EXIT_ABNORMALLY_NAME | 异常退出 | AC-2.4 |
| ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT | EVENT_TIMEOUT_NAME | 超时 | AC-2.5 |
| ERROR_CODE_UIEXTENSION_FORBID_CASCADE | PULL_FAIL_NAME | 级联禁止 | AC-2.6 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 启动失败 | callback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, ...) | AC-2.3 |
| 2 | 异常退出 | callback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, ...) | AC-2.4 |
| 3 | 超时 | callback(ERROR_CODE_UIEXTENSION_EVENT_TIMEOUT, ...) | AC-2.5 |
| 4 | 级联禁止 | callback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, ...) | AC-2.6 |
| 5 | 注册时 lastError_ 有缓存 | 立即补发缓存错误 | AC-2.2 |
| 6 | callback 为空 | 错误缓存到 lastError_ | AC-2.9 |
| 7 | onError 触发后 | state_=NONE；DestroySession；RemoveChild | AC-2.7 |
| 8 | C-API NODE_EMBEDDED_COMPONENT_OPTION onError | setEmbeddedComponentOption → Pattern::SetOnErrorCallback | AC-2.8 |

### 接口定义 — onDrawReady(callback: Callback<void>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `EmbeddedComponentAttribute onDrawReady(callback: Callback<void>)` |
| 返回值 | `EmbeddedComponentAttribute` — 属性链对象 |
| 开放范围 | AtomicService (@atomicservice @since 26.0.0) |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.4 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | Callback<void> () => void | 是 | — | 无参数回调 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | ExtensionAbility 首帧绘制完成 | ReplacePlaceholderByContent → callback() | AC-3.2, AC-3.3 |
| 2 | callback 为空 | 仅执行 ReplacePlaceholderByContent | AC-3.4 |

### 接口定义 — ArkUIEmbeddedComponentModifier::setOnTerminated/resetOnTerminated (C-API)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void setOnTerminated(ArkUINodeHandle node, void(*callback)(int32_t code, void* userData), void* userData)` |
| 返回值 | void |
| 开放范围 | NDK public (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-2.8 |

**参数约束：**

| 参数 | 类型 | 必填 | 约束条件 |
|------|------|------|----------|
| node | ArkUINodeHandle | 是 | EmbeddedComponent FrameNode |
| callback | void(*)(int32_t, void*) | 是 | onTerminated 回调 |
| userData | void* | 否 | 用户数据 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | setOnTerminated(node, callback, userData) | Pattern::SetOnTerminatedCallback 注册回调 | AC-2.8 |
| 2 | resetOnTerminated(node) | 设置 nullptr | AC-2.8 |

### 接口定义 — ArkUIEmbeddedComponentModifier::setOnError/resetOnError (C-API)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void setOnError(ArkUINodeHandle node, void(*callback)(int32_t code, const char* name, const char* message, void* userData), void* userData)` |
| 返回值 | void |
| 开放范围 | NDK public (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-2.8 |

**参数约束：**

| 参数 | 类型 | 必填 | 约束条件 |
|------|------|------|----------|
| node | ArkUINodeHandle | 是 | EmbeddedComponent FrameNode |
| callback | void(*)(int32_t, const char*, const char*, void*) | 是 | onError 回调 |
| userData | void* | 否 | 用户数据 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | setOnError(node, callback, userData) | Pattern::SetOnErrorCallback 注册回调 | AC-2.8 |
| 2 | resetOnError(node) | 设置 nullptr | AC-2.8 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12（@atomicservice @stagemodelonly）；onDrawReady @since 26.0.0；C-API @since 20
- **API 版本号策略:** onTerminated/onError @since 12；onDrawReady @since 26.0.0

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| EmbeddedComponent 使用 UIExtensionPattern 共享回调基础设施 | sessionType_=EMBEDDED_UI_EXTENSION 区分行为；IsCompatibleOldVersion()=false 不走 onResult/onRelease compat 路径 | AC-1.2 |
| EmbeddedComponent 不支持 onResult/onRelease/onRemoteReady（事件级） | 仅三种事件：onTerminated/onError/onDrawReady | — |
| EmbeddedComponent 为 @atomicservice | 三方应用可直接使用 | AC-1.1 |
| C-API Static modifier 事件为 stub | 仅 ConstructImpl 有效；SetOnTerminatedImpl/SetOnErrorImpl/SetOnDrawReadyImpl 为 stub | — |
| C-API Dynamic modifier 支持 onError/onTerminated | 通过 NODE_EMBEDDED_COMPONENT_OPTION 或 setOnError/setOnTerminated 注册 | AC-2.8 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 事件回调通过 PostTask 到 UI 线程 | 集成测试 | session_wrapper_impl.cpp |
| 安全 | @atomicservice 面向三方应用开放 | API 评审 | SDK repo d.ts |
| 可测试性 | onError/onTerminated 可通过 Mock ExtensionSession 验证 | 单测 | ui_extension_pattern.cpp |
| 可测试性 | C-API onError/onTerminated 可通过 embeddedComponent_modifier 单测验证 | C-API 单测 | embeddedComponent_modifier.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | DPI 策略影响错误码触发场景 | 需正确配置 DPI | 集成测试 | ui_extension_pattern.cpp |
| 折叠屏 | onDrawReady 触发后需正确 ReplacePlaceholderByContent | 需监听 display 变化 | 集成测试 | ui_extension_pattern.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Extension 内容通过 AccessibilityChildTreeCallback 进入宿主无障碍树 | AC-1.1 |
| 大字体 | 是 | DPI 策略影响字体大小 | — |
| 深色模式 | 否 | Extension 使用独立进程 | — |
| 多窗口/分屏 | 是 | onError 可能由分屏冲突触发 | AC-2.6 |
| 多用户 | 否 | Extension 运行在独立进程 | — |
| 版本升级 | 否 | API 12 起行为不变 | — |
| 生态兼容 | 是 | @atomicservice 与 @systemapi（UIExtensionComponent）共存 | AC-1.1 |

---

## 行为场景

```gherkin
Feature: EmbeddedComponent 事件回调
  作为 三方应用开发者
  我想要 通过 onTerminated/onError/onDrawReady 监听 ExtensionAbility 状态
  以便 在宿主页面中响应远端 Extension 的终止/错误/首帧事件

  # ─── onTerminated ──────────────────────────

  Scenario: 注册 onTerminated 回调
    Given 一个 EmbeddedComponent 已创建
    When 调用 .onTerminated(callback)
    Then JSEmbeddedComponent::OnTerminated 解析 callback
    And UIExtensionModel::SetOnTerminated 注册到 UIExtensionPattern.onTerminatedCallback_

  Scenario: 远端 terminateWithResult 触发 onTerminated
    Given UIExtensionPattern.onTerminatedCallback_ 已注册
    And sessionType_ = EMBEDDED_UI_EXTENSION
    When 远端 ExtensionAbility 调用 terminateWithResult(0, want)
    Then IsCompatibleOldVersion() 返回 false（sessionType≠UI_EXTENSION_ABILITY）
    And FireOnTerminatedCallback(0, WantWrapOhos(want))
    And callback 收到 TerminationInfo { code: 0, want }

  Scenario: 正常断开触发 onTerminated
    Given UIExtensionPattern.onTerminatedCallback_ 已注册
    When SessionWrapperImpl::OnDisconnect(isAbnormal=false)
    Then FireOnTerminatedCallback(0, nullptr)
    And callback 收到 TerminationInfo { code: 0, want: undefined }

  Scenario: 重复终止不触发回调
    Given UIExtensionPattern.state_ = DESTRUCTION
    When onTerminated 事件到达
    Then onTerminatedCallback_ 检查 state_==DESTRUCTION
    And 不触发 callback

  # ─── onError ───────────────────────────────

  Scenario: 注册 onError 回调
    Given 一个 EmbeddedComponent 已创建
    When 调用 .onError(callback)
    Then JSEmbeddedComponent::OnError 解析 callback
    And UIExtensionModel::SetOnError 注册到 UIExtensionPattern.onErrorCallback_

  Scenario: 注册 onError 时补发缓存错误
    Given UIExtensionPattern.lastError_ 有缓存错误 { code: 123, name: "err", message: "msg" }
    When 调用 .onError(callback)
    Then swap lastError_ → ErrorMsg
    And 立即 FireOnErrorCallback(123, "err", "msg")

  Scenario: 启动失败触发 onError
    Given UIExtensionPattern.onErrorCallback_ 已注册
    When ExtensionAbility 启动失败
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FOREGROUND_FAILED, START_FAIL_NAME, START_FAIL_MESSAGE)
    And callback 收到错误码

  Scenario: 异常退出触发 onError
    Given UIExtensionPattern.onErrorCallback_ 已注册
    And IsCompatibleOldVersion() 返回 false
    When SessionWrapperImpl::OnDisconnect(isAbnormal=true)
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, ...)
    And state_ = NONE

  Scenario: 级联嵌套禁止触发 onError
    Given UIExtensionPattern.onErrorCallback_ 已注册
    When 检测级联嵌套
    Then FireOnErrorCallback(ERROR_CODE_UIEXTENSION_FORBID_CASCADE, PULL_FAIL_NAME, PULL_FAIL_MESSAGE)

  # ─── onDrawReady ──────────────────────────

  Scenario: 注册 onDrawReady 回调
    Given 一个 EmbeddedComponent 已创建
    When 调用 .onDrawReady(callback)
    Then JSEmbeddedComponent::OnDrawReady 解析 callback
    And UIExtensionModel::SetOnDrawReady 注册到 UIExtensionPattern.onDrawReadyCallback_

  Scenario: 首帧绘制完成触发 onDrawReady
    Given UIExtensionPattern.onDrawReadyCallback_ 已注册
    When UIExtensionPattern 收到 UIExtCallbackEventId::ON_DRAW_FIRST
    Then ReplacePlaceholderByContent 替换 placeholder 为 Extension 内容
    And onDrawReadyCallback_() 触发 callback

  # ─── C-API Dynamic Modifier ────────────────

  Scenario: C-API 设置 onError 回调
    Given NDK 开发环境和 EmbeddedComponent FrameNode
    When 设置 NODE_EMBEDDED_COMPONENT_OPTION 且 option->onError 非空
    Then setEmbeddedComponentOption → UIExtensionAdapter::SetEmbeddedComponentOnError → Pattern::SetOnErrorCallback

  Scenario: C-API resetOnError
    Given NDK 开发环境和已注册 onError 的 EmbeddedComponent FrameNode
    When 调用 resetOnError(node)
    Then Pattern::SetOnErrorCallback(nullptr)

  Scenario: C-API 设置 onTerminated 回调
    Given NDK 开发环境和 EmbeddedComponent FrameNode
    When 设置 NODE_EMBEDDED_COMPONENT_OPTION 且 option->onTerminated 非空
    Then setEmbeddedComponentOption → UIExtensionAdapter::SetEmbeddedComponentOnTerminated → Pattern::SetOnTerminatedCallback

  Scenario: C-API resetOnTerminated
    Given NDK 开发环境和已注册 onTerminated 的 EmbeddedComponent FrameNode
    When 调用 resetOnTerminated(node)
    Then Pattern::SetOnTerminatedCallback(nullptr)

  # ─── C-API Static Modifier Stub ─────────────

  Scenario: C-API Static modifier SetOnTerminatedImpl stub
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIEmbeddedComponentModifier::SetOnTerminatedImpl(node, callback)
    Then 输出 LOGE "not supported"，不修改 FrameNode 状态

  Scenario: C-API Static modifier SetOnErrorImpl stub
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIEmbeddedComponentModifier::SetOnErrorImpl(node, callback)
    Then 输出 LOGE "not supported"，不修改 FrameNode 状态

  Scenario: C-API Static modifier SetOnDrawReadyImpl stub
    Given Arkoala 静态范式环境
    When 调用 GENERATED_ArkUIEmbeddedComponentModifier::SetOnDrawReadyImpl(node, callback)
    Then 输出 LOGE "not supported"，不修改 FrameNode 状态
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：onTerminated/onError/onDrawReady 注册与触发条件规格、C-API Dynamic/Static modifier 事件规格；不做什么：创建/选项/DPI/Placeholder（Feat-01）、onResult/onRelease（不支持）、onRemoteReady/onReceive（不支持））
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "JSEmbeddedComponent OnTerminated OnError OnDrawReady 注册回调到 UIExtensionPattern 的流程"
  - repo: "openharmony/ace_engine"
    query: "SessionWrapperImpl InitTransferAbilityResultFunc InitForegroundCallback EMBEDDED_UI_EXTENSION 路径选择"
  - repo: "openharmony/ace_engine"
    query: "ArkUIEmbeddedComponentModifier setOnTerminated setOnError resetOnTerminated resetOnError 实现"
  - repo: "openharmony/ace_engine"
    query: "GENERATED_ArkUIEmbeddedComponentModifier SetOnTerminatedImpl SetOnErrorImpl SetOnDrawReadyImpl stub"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern FireOnDrawReadyCallback ReplacePlaceholderByContent ON_DRAW_FIRST"
  - repo: "openharmony/ace_engine"
    query: "EmbeddedComponent 不支持 onResult/onRelease/onRemoteReady 的事件级差异"
```

**关键文档：**
- JS Bridge 层：`frameworks/bridge/declarative_frontend/jsview/js_ui_extension.cpp:580-656`
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.h`
- Pattern 层回调实现：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.cpp:1601-1670, 2370-2376`
- SessionWrapper 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/session_wrapper_impl.cpp`
- C-API Dynamic：`interfaces/native/node/embeddedComponent_modifier.cpp`
- C-API Static：`frameworks/core/interfaces/native/implementation/embedded_component_modifier.cpp`
