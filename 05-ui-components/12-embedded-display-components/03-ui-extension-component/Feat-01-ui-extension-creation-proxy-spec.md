# 特性规格

> Func-05-12-03-Feat-01 UIExtensionComponent创建/选项/Proxy通信：固化 UIExtensionComponent 创建流程、Want + UIExtensionOptions 传递机制、SessionWrapperImpl 跨进程 Session 加载、UIExtensionProxy send/sendSync 通信、Placeholder 占位机制、DpiFollowStrategy/WindowModeFollowStrategy 配置的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIExtensionComponent创建/选项/Proxy通信 |
| 特性编号 | Func-05-12-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10+（@systemapi） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIExtensionComponent 创建与 Want/Options 规格 | 补录 UIExtensionComponent(want, options) 创建流程、Want 定位远端 UIExtensionAbility、UIExtensionOptions 各字段传递规格 |
| ADDED | SessionWrapperImpl 跨进程 Session 加载规格 | 补录 Rosen ExtensionSession 创建、RequestStartUIExtensionAbility 跨进程启动、SurfaceNode 挂载规格 |
| ADDED | UIExtensionProxy 通信规格 | 补录 send/sendSync/on/offAsyncReceiverRegister/on/offSyncReceiverRegister 行为规格 |
| ADDED | Placeholder 机制规格 | 补录 PlaceholderType 占位节点挂载/移除、curPlaceholderType_ 状态追踪规格 |
| ADDED | DPI/WindowMode 策略规格 | 补录 DpiFollowStrategy/WindowModeFollowStrategy 配置传递与 SessionViewportConfig 映射规格 |
| ADDED | C-API Static modifier 与 Proxy accessor 规格 | 补录 GENERATED_ArkUIUIExtensionComponentModifier 覆盖范围（实现 + stub）、GENERATED_ArkUIUIExtensionProxyAccessor 覆盖范围规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/03-ui-extension-component/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 UIExtensionComponent 并加载远端 UIExtensionAbility

**作为** 系统应用开发者,
**我想要** 通过 UIExtensionComponent(want, options) 创建组件并传入 Want 和 Options,
**以便** 在宿主页面中嵌入远端 UIExtensionAbility 的 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `UIExtensionComponent(want, { isTransferringCaller: true, dpiFollowStrategy: DpiFollowStrategy.FOLLOW_HOST_DPI })` THEN 创建 UIExtensionPattern(isTransferringCaller=true) → 创建 SessionWrapperImpl(instanceId, isTransferringCaller=true, SessionType::UI_EXTENSION_ABILITY) → 通过 Rosen SessionService 跨进程启动 UIExtensionAbility → 挂载 SurfaceNode | 正常 |
| AC-1.2 | WHEN Want 为空或缺少 bundleName/abilityName THEN 不创建有效 Session；onError 回调传递错误信息 | 异常 |
| AC-1.3 | WHEN WINDOW_SCENE_SUPPORTED 编译开关关闭 THEN UIExtensionPattern 方法为空壳实现，不创建 Session | 边界 |
| AC-1.4 | WHEN options.isTransferringCaller 未指定 THEN 默认为 false；UIExtensionPattern 的 isTransferringCaller_ = false | 正常 |
| AC-1.5 | WHEN options.dpiFollowStrategy 为 FOLLOW_HOST_DPI THEN SessionViewportConfig.isDensityFollowHost_ = true，density_ 取宿主 density | 正常 |
| AC-1.6 | WHEN options.windowModeFollowStrategy 为 FOLLOW_HOST_WINDOW_MODE THEN UIExtensionPattern.isWindowModeFollowHost_ = true，NotifyHostWindowMode 传递宿主 WindowMode | 正常 |

### US-2: 通过 UIExtensionProxy 进行宿主→远端数据通信

**作为** 系统应用开发者,
**我想要** 通过 onRemoteReady 回调获取 UIExtensionProxy，并使用 proxy.send/proxy.sendSync 发送数据,
**以便** 实现宿主与远端 UIExtensionAbility 之间的双向通信。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN UIExtensionAbility 连接成功 THEN SessionWrapperImpl::OnConnect → UIExtensionPattern::FireOnRemoteReadyCallback → ArkTS onRemoteReady 回调收到 UIExtensionProxy 对象 | 正常 |
| AC-2.2 | WHEN 调用 `proxy.send(data)` THEN UIExtensionProxy::SendDataAsync → SessionWrapperImpl::SendDataAsync → ExtensionSession 跨进程传递 WantParams | 正常 |
| AC-2.3 | WHEN 调用 `proxy.sendSync(data)` THEN UIExtensionProxy::SendDataSync → SessionWrapperImpl::SendDataSync → 同步等待远端回复 WantParams；返回远端回复数据 | 正常 |
| AC-2.4 | WHEN sendSync 远端未注册 syncReceiver THEN 抛出 BusinessError 100011 "No callback has been registered" | 异常 |
| AC-2.5 | WHEN sendSync 传输失败 THEN 抛出 BusinessError 100012 "Transferring data failed" | 异常 |
| AC-2.6 | WHEN 调用 `proxy.on('asyncReceiverRegister', callback)` THEN 注册回调到 onAsyncOnCallbackList_；远端注册 async 数据接收回调时触发 callback(proxy) | 正常 |
| AC-2.7 | WHEN 调用 `proxy.on('syncReceiverRegister', callback)` THEN 注册回调到 onSyncOnCallbackList_；远端注册 sync 数据接收回调时触发 callback(proxy) | 正常 |
| AC-2.8 | WHEN 调用 `proxy.off('asyncReceiverRegister', callback)` THEN 从 onAsyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | 正常 |
| AC-2.9 | WHEN 调用 `proxy.off('syncReceiverRegister', callback)` THEN 从 onSyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | 正常 |

### US-3: Placeholder 占位机制

**作为** 系统应用开发者,
**我想要** 通过 options.placeholder 和 areaChangePlaceholder 设置占位内容,
**以便** 在远端连接未建立或尺寸变化时显示占位 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN options.placeholder 设置了 ComponentContent THEN PlaceholderType=UNDEFINED 对应的 FrameNode 被挂载到 UIExtensionNode 下作为初始占位 | 正常 |
| AC-3.2 | WHEN 远端 Session 连接成功（OnConnect）THEN RemovePlaceholderNode 移除占位节点；挂载远端 SurfaceNode 替代 | 正常 |
| AC-3.3 | WHEN 折叠屏状态变化 THEN PlaceholderType=FOLD_TO_EXPAND 对应的 FrameNode 被挂载作为折叠占位；PostDelayRemovePlaceholder 延迟移除 | 正常 |
| AC-3.4 | WHEN 旋转状态变化 THEN PlaceholderType=ROTATION 对应的 FrameNode 被挂载作为旋转占位 | 正常 |
| AC-3.5 | WHEN curPlaceholderType_ 状态为 NONE THEN 不显示任何占位节点；IsShowPlaceholder() 返回 false | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1, R-2, R-3, R-4, R-5, R-6, R-7, R-8 | 已有实现 | 代码评审 | `ui_extension_pattern.cpp`, `ui_extension_model_ng.cpp`, `session_wrapper_impl.cpp` |
| AC-2.1~2.9 | R-9, R-10, R-11, R-12, R-13, R-14, R-15, R-16 | 已有实现 | 代码评审 | `ui_extension_proxy.cpp`, `js_ui_extension.cpp`, `ui_extension_proxy_accessor.cpp` |
| AC-3.1~3.5 | R-17, R-18, R-19, R-20, R-21 | 已有实现 | 代码评审 | `ui_extension_pattern.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `UIExtensionComponent(want, options)` 被调用 | JSUIExtension::Create 解析 Want/Options → UIExtensionModelNG::Create → 创建 UIExtensionNode + UIExtensionPattern → 设置 Want/Options/Placeholder/DPI | — | AC-1.1 |
| R-2 | 行为 | UIExtensionPattern::OnAttachToFrameNode | 初始化 SessionWrapper（通过 SessionWrapperFactory::Create）→ 设置 Placeholder 节点 → 注册 WindowStateChanged 回调 | — | AC-1.1 |
| R-3 | 行为 | SessionWrapperImpl 创建 Rosen ExtensionSession | 创建 ExtensionSession → RequestStartUIExtensionAbility → 注册 OnConnect/OnDisconnect/OnRelease/OnTransfer 回调 → 挂载 SurfaceNode | 依赖 WINDOW_SCENE_SUPPORTED 编译开关 | AC-1.1 |
| R-4 | 行为 | UIExtensionAbility 连接成功 | SessionWrapperImpl::OnConnect → UIExtensionPattern::FireOnRemoteReadyCallback → ArkTS onRemoteReady(UIExtensionProxy) | Proxy 封装 SessionWrapper + Pattern | AC-2.1 |
| R-5 | 异常 | Want 为空或缺少必要字段 | 不创建有效 Session；UIExtensionPattern 进入错误状态；onError 回调 | — | AC-1.2 |
| R-6 | 边界 | WINDOW_SCENE_SUPPORTED 编译开关关闭 | UIExtensionPattern 方法为空壳实现；SessionWrapper 不创建；C-API ConstructImpl 返回 nullptr | — | AC-1.3 |
| R-7 | 行为 | options.isTransferringCaller 未指定 | 默认 false；UIExtensionPattern(isTransferringCaller=false) | — | AC-1.4 |
| R-8 | 行为 | dpiFollowStrategy = FOLLOW_HOST_DPI | SessionViewportConfig.isDensityFollowHost_ = true；density_ 取宿主 PipelineContext density | 默认 FOLLOW_UI_EXTENSION_ABILITY_DPI | AC-1.5 |
| R-9 | 行为 | proxy.send(data) 被调用 | UIExtensionProxy::SendDataAsync → SessionWrapper::SendDataAsync → ExtensionSession 跨进程传递 WantParams | 异步发送，不等待回复 | AC-2.2 |
| R-10 | 行为 | proxy.sendSync(data) 被调用 | UIExtensionProxy::SendDataSync → SessionWrapper::SendDataSync → 同步等待远端回复 WantParams；返回回复数据 | 可能抛出 BusinessError | AC-2.3 |
| R-11 | 异常 | sendSync 远端未注册 syncReceiver | 抛出 BusinessError 100011 | — | AC-2.4 |
| R-12 | 异常 | sendSync 传输失败 | 抛出 BusinessError 100012 | — | AC-2.5 |
| R-13 | 行为 | proxy.on('asyncReceiverRegister', callback) | 注册回调到 UIExtensionPattern.onAsyncOnCallbackList_；远端注册 async 数据接收回调时触发 | — | AC-2.6 |
| R-14 | 行为 | proxy.on('syncReceiverRegister', callback) | 注册回调到 UIExtensionPattern.onSyncOnCallbackList_；远端注册 sync 数据接收回调时触发 | — | AC-2.7 |
| R-15 | 行为 | proxy.off('asyncReceiverRegister', callback) | 从 onAsyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | — | AC-2.8 |
| R-16 | 行为 | proxy.off('syncReceiverRegister', callback) | 从 onSyncOnCallbackList_ 移除指定 callback；若 callback 为空则清空列表 | — | AC-2.9 |
| R-17 | 行为 | options.placeholder 设置 | PlaceholderType=UNDEFINED 对应 FrameNode 挂载到 UIExtensionNode 下 | placeholderMap_ 映射 | AC-3.1 |
| R-18 | 行为 | 远端 Session 连接成功 | RemovePlaceholderNode 移除占位 → 挂载远端 SurfaceNode 替代 | — | AC-3.2 |
| R-19 | 行为 | 折叠屏状态变化 | PlaceholderType=FOLD_TO_EXPAND 对应 FrameNode 挂载 → PostDelayRemovePlaceholder 延迟移除 | 延迟移除防止闪烁 | AC-3.3 |
| R-20 | 行为 | 旋转状态变化 | PlaceholderType=ROTATION 对应 FrameNode 挂载 | — | AC-3.4 |
| R-21 | 行为 | curPlaceholderType_ = NONE | IsShowPlaceholder() 返回 false；不显示占位节点 | — | AC-3.5 |
| R-22 | 行为 | windowModeFollowStrategy = FOLLOW_HOST_WINDOW_MODE | UIExtensionPattern.isWindowModeFollowHost_ = true；NotifyHostWindowMode 传递宿主 WindowMode | 默认 FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE | AC-1.6 |
| R-23 | 边界 | UIExtensionUsage 决定 | SessionConfig.uiExtensionUsage = MODAL/EMBEDDED/CONSTRAINED_EMBEDDED/PREVIEW_EMBEDDED；影响 Session 创建参数 | — | AC-1.1 |
| R-24 | 边界 | SessionType = UI_EXTENSION_ABILITY (1) | UIExtensionPattern 使用的 SessionType；SessionWrapperFactory 根据此值创建 SessionWrapperImpl | 非 EMBEDDED_UI_EXTENSION/SECURITY/DYNAMIC/ISOLATED 类型 | AC-1.1 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1, R-2, R-3 | 代码评审 | UIExtension 创建流程完整性（JSUIExtension→Model→Pattern→SessionWrapper→Rosen Session） |
| VM-2 | AC-1.2, R-5 | 代码评审 | Want 为空的错误处理 |
| VM-3 | AC-1.3, R-6 | 代码评审 | 编译开关影响 |
| VM-4 | AC-1.4~1.6, R-7, R-8, R-22 | 代码评审 | Options 各字段传递 |
| VM-5 | AC-2.1, R-4 | 代码评审 | onRemoteReady 回调链完整性 |
| VM-6 | AC-2.2~2.3, R-9, R-10 | 代码评审 | Proxy send/sendSync 通信 |
| VM-7 | AC-2.4~2.5, R-11, R-12 | 代码评审 | sendSync 错误处理 |
| VM-8 | AC-2.6~2.9, R-13~R-16 | 代码评审 | Proxy on/offReceiverRegister |
| VM-9 | AC-3.1~3.5, R-17~R-21 | 代码评审 | Placeholder 机制 |
| VM-10 | C-API Static modifier | C-API 单测 | ConstructImpl + SetOnRemoteReadyImpl 实现；其余 stub |
| VM-11 | C-API Proxy accessor | C-API 单测 | on/offAsync/SyncReceiverRegister 实现；send/sendSync stub |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `UIExtensionComponent(want: Want, options?: UIExtensionOptions)` | System | 创建UIExtension组件 | `@internal/component/ets/ui_extension_component.d.ts` | 10/11 | @systemapi |
| `UIExtensionOptions { isTransferringCaller?, placeholder?, dpiFollowStrategy?, areaChangePlaceholder?, windowModeFollowStrategy? }` | System | 创建选项 | `@internal/component/ets/ui_extension_component.d.ts` | 11/12/14/18 | @systemapi |
| `onRemoteReady(callback: Callback<UIExtensionProxy>)` | System | 远端连接就绪回调 | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |
| `UIExtensionProxy { send, sendSync, on/off('asyncReceiverRegister'), on/off('syncReceiverRegister') }` | System | 代理通信接口 | `@internal/component/ets/ui_extension_component.d.ts` | 10/11/18 | @systemapi |
| `DpiFollowStrategy { FOLLOW_HOST_DPI=0, FOLLOW_UI_EXTENSION_ABILITY_DPI=1 }` | System | DPI策略枚举 | `@internal/component/ets/ui_extension_component.d.ts` | 12 | @systemapi |
| `WindowModeFollowStrategy { FOLLOW_HOST_WINDOW_MODE=0, FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE=1 }` | System | 窗口模式策略枚举 | `@internal/component/ets/ui_extension_component.d.ts` | 18 | @systemapi |
| `PlaceholderType { NONE=0, UNDEFINED=1, ROTATION=2, FOLD_TO_EXPAND=3, INITIAL=4 }` | System (内部) | 占位类型枚举 | `ui_extension_config.h` | — | — |
| `UIExtensionUsage { MODAL=0, EMBEDDED=1, CONSTRAINED_EMBEDDED=2, PREVIEW_EMBEDDED=3 }` | System (内部) | 用途枚举 | `session_wrapper.h` | — | — |

**C-API (NDK) 接口：**

| Modifier 类型 | 属性枚举 | 功能 | 实现状态 | @since |
|---------------|----------|------|----------|--------|
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::construct` | 创建 FrameNode | 实现 | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setUIExtensionComponentOptions` | 设置 Want + Options | stub（LOGE "areaChangePlaceholder not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnRemoteReady` | 注册 onRemoteReady 回调 | 实现 | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnReceive` | 注册 onReceive 回调 | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnError` | 注册 onError 回调 | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnTerminated` | 注册 onTerminated 回调 | stub（LOGE "not supported"） | — |
| Static (Arkoala) | `GENERATED_ArkUIUIExtensionComponentModifier::setOnDrawReady` | 注册 onDrawReady 回调 | stub（LOGE "not supported"） | — |
| Proxy accessor | `GENERATED_ArkUIUIExtensionProxyAccessor::onAsyncReceiverRegister` | 注册 asyncReceiver 回调 | 实现 | — |
| Proxy accessor | `GENERATED_ArkUIUIExtensionProxyAccessor::onSyncReceiverRegister` | 注册 syncReceiver 回调 | 实现 | — |
| Proxy accessor | `GENERATED_ArkUIUIExtensionProxyAccessor::offAsyncReceiverRegister` | 移除 asyncReceiver 回调 | 实现 | — |
| Proxy accessor | `GENERATED_ArkUIUIExtensionProxyAccessor::offSyncReceiverRegister` | 移除 syncReceiver 回调 | 实现 | — |
| Proxy accessor | `GENERATED_ArkUIUIExtensionProxyAccessor::send` | Proxy send 数据 | stub（LOGE "not supported"） | — |
| Proxy accessor | `GENERATED_ArkUIUIExtensionProxyAccessor::sendSync` | Proxy sendSync 数据 | stub（LOGE "not supported"，返回空 Map） | — |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `UIExtensionOptions` | `{ isTransferringCaller?: boolean, placeholder?: ComponentContent, dpiFollowStrategy?: DpiFollowStrategy, areaChangePlaceholder?: Record<string, ComponentContent>, windowModeFollowStrategy?: WindowModeFollowStrategy }` | `ui_extension_component.d.ts` |
| `DpiFollowStrategy` | `enum { FOLLOW_HOST_DPI = 0, FOLLOW_UI_EXTENSION_ABILITY_DPI = 1 }` | `ui_extension_component.d.ts` |
| `WindowModeFollowStrategy` | `enum { FOLLOW_HOST_WINDOW_MODE = 0, FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE = 1 }` | `ui_extension_component.d.ts` |
| `UIExtensionProxy` | `interface { send(data: Record<string, Object>): void, sendSync(data: Record<string, Object>): Record<string, Object>, on/off('asyncReceiverRegister'/'syncReceiverRegister') }` | `ui_extension_component.d.ts` |
| `PlaceholderType` | `enum class { NONE=0, UNDEFINED=1, ROTATION=2, FOLD_TO_EXPAND=3, INITIAL=4 }` | `ui_extension_config.h` |
| `UIExtensionUsage` | `enum class { MODAL=0, EMBEDDED=1, CONSTRAINED_EMBEDDED=2, PREVIEW_EMBEDDED=3 }` | `session_wrapper.h` |
| `SessionType` | `enum class { UI_EXTENSION_ABILITY=1 }` | `session_wrapper.h` |
| `SessionViewportConfig` | `struct { isDensityFollowHost_, density_, displayId_, orientation_, transform_ }` | `ui_extension_pattern.h` |
| `UIExtensionProxy (C++)` | `class { sessionWrapper_, pattern_ (WeakPtr), SendData/SendDataSync, GetPattern }` | `ui_extension_proxy.h` |
| `SessionWrapperImpl (C++)` | `class { hostPattern_ (WeakPtr), instanceId_, isTransferringCaller_, session_ (sptr<ExtensionSession>) }` | `session_wrapper_impl.h` |

### 变更/废弃 API

无变更/废弃 API（onResult/onRelease 废逝由 Feat-03 覆盖）。

---

## 接口规格

### 接口定义 — UIExtensionComponent(want: Want, options?: UIExtensionOptions)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute UIExtensionComponent(want: Want, options?: UIExtensionOptions)` |
| 返回值 | `UIExtensionComponentAttribute` — 组件属性对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| want | Want | 是 | — | 必须包含 bundleName + abilityName 定位远端 UIExtensionAbility |
| options | UIExtensionOptions | 否 | {} | — |
| options.isTransferringCaller | boolean | 否 | false | 控制当前 token 是否作为 Caller 设置为 rootToken |
| options.placeholder | ComponentContent | 否 | undefined | 设置 PlaceholderType=UNDEFINED 的占位内容 |
| options.dpiFollowStrategy | DpiFollowStrategy | 否 | FOLLOW_UI_EXTENSION_ABILITY_DPI | 控制远端 DPI 是否跟随宿主 |
| options.areaChangePlaceholder | Record<string, ComponentContent> | 否 | undefined | 设置区域变化占位内容（since 14） |
| options.windowModeFollowStrategy | WindowModeFollowStrategy | 否 | FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE | 控制远端窗口模式是否跟随宿主（since 18） |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | want 包含有效 bundleName + abilityName | 创建 UIExtensionPattern → SessionWrapperImpl → Rosen ExtensionSession → 跨进程启动 UIExtensionAbility | AC-1.1 |
| 2 | want 为空或缺少必要字段 | 不创建有效 Session；触发 onError | AC-1.2 |
| 3 | options.isTransferringCaller = true | UIExtensionPattern(isTransferringCaller=true) | AC-1.4 |
| 4 | options.dpiFollowStrategy = FOLLOW_HOST_DPI | SessionViewportConfig.isDensityFollowHost_ = true | AC-1.5 |
| 5 | options.windowModeFollowStrategy = FOLLOW_HOST_WINDOW_MODE | isWindowModeFollowHost_ = true | AC-1.6 |

### 接口定义 — onRemoteReady(callback: Callback<UIExtensionProxy>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onRemoteReady(callback: Callback<UIExtensionProxy>)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | Callback<UIExtensionProxy> | 是 | — | callback 参数为 UIExtensionProxy 对象 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | UIExtensionAbility 连接成功 | SessionWrapperImpl::OnConnect → UIExtensionPattern::FireOnRemoteReadyCallback → callback(proxy) | AC-2.1 |

### 接口定义 — UIExtensionProxy.send(data: Record<string, Object>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void send(data: Record<string, Object>)` |
| 返回值 | void |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| data | Record<string, Object> | 是 | — | 异步发送，不等待回复 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | proxy.send(data) 被调用 | UIExtensionProxy::SendDataAsync → SessionWrapper::SendDataAsync → 跨进程传递 | AC-2.2 |

### 接口定义 — UIExtensionProxy.sendSync(data: Record<string, Object>)

| 属性 | 值 |
|------|-----|
| 函数签名 | `Record<string, Object> sendSync(data: Record<string, Object>)` |
| 返回值 | Record<string, Object> — 远端回复数据 |
| 开放范围 | System (@systemapi) |
| 错误码 | 100011 (无注册回调), 100012 (传输失败) |
| 关联 AC | AC-2.3, AC-2.4, AC-2.5 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| data | Record<string, Object> | 是 | — | 同步发送，等待远端回复 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | proxy.sendSync(data) 被调用 | UIExtensionProxy::SendDataSync → SessionWrapper::SendDataSync → 同步等待回复 | AC-2.3 |
| 2 | 远端未注册 syncReceiver | 抛出 BusinessError 100011 | AC-2.4 |
| 3 | 传输失败 | 抛出 BusinessError 100012 | AC-2.5 |

### 接口定义 — UIExtensionProxy.on(type, callback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void on(type: 'asyncReceiverRegister' | 'syncReceiverRegister', callback: Callback<UIExtensionProxy>)` |
| 返回值 | void |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-2.6, AC-2.7 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| type | 'asyncReceiverRegister' | 'syncReceiverRegister' | 是 | — | type 必须为指定字符串 |
| callback | Callback<UIExtensionProxy> | 是 | — | callback 参数为 UIExtensionProxy 对象 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | proxy.on('asyncReceiverRegister', callback) | 注册到 onAsyncOnCallbackList_ | AC-2.6 |
| 2 | proxy.on('syncReceiverRegister', callback) | 注册到 onSyncOnCallbackList_ | AC-2.7 |

### 接口定义 — UIExtensionProxy.off(type, callback?)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void off(type: 'asyncReceiverRegister' | 'syncReceiverRegister', callback?: Callback<UIExtensionProxy>)` |
| 返回值 | void |
| 开放范围 | System (@systemapi) |
| 错误码 | N/A |
| 关联 AC | AC-2.8, AC-2.9 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| type | 'asyncReceiverRegister' | 'syncReceiverRegister' | 是 | — | type 必须为指定字符串 |
| callback | Callback<UIExtensionProxy> | 否 | undefined | 不传则清空全部回调 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | proxy.off('asyncReceiverRegister', callback) | 移除指定 callback | AC-2.8 |
| 2 | proxy.off('asyncReceiverRegister') | 清空 onAsyncOnCallbackList_ | AC-2.8 |
| 3 | proxy.off('syncReceiverRegister', callback) | 移除指定 callback | AC-2.9 |
| 4 | proxy.off('syncReceiverRegister') | 清空 onSyncOnCallbackList_ | AC-2.9 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10
- **API 版本号策略:** @since 10 为基础创建接口；@since 11 补充 isTransferringCaller；@since 12 补充 placeholder/dpiFollowStrategy；@since 14 补充 areaChangePlaceholder；@since 18 补充 windowModeFollowStrategy + 匿名对象 rectification

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| 组件级 API 为 @systemapi | 仅系统应用可使用；EmbeddedComponent 为 @atomicservice 替代 | AC-1.1 |
| UIExtensionPattern 继承 Pattern（非 PlatformPattern） | 完整 NG Pattern 生命周期 | AC-1.1 |
| SessionWrapperImpl 使用 Rosen ExtensionSession | 跨进程渲染挂载，依赖 Rosen SessionService | AC-1.1 |
| SessionType = UI_EXTENSION_ABILITY (1) | 区分于 Embedded/Security/Dynamic/Isolated 类型 | AC-1.1 |
| WINDOW_SCENE_SUPPORTED 编译开关 | 控制完整编译/空壳编译 | AC-1.3 |
| C-API Static modifier 仅 setOnRemoteReady 实现 | 其余事件回调为 stub | AC-2.1 |
| C-API Proxy accessor send/sendSync 为 stub | C-API 场景下仅 on/offReceiverRegister 可用 | AC-2.2, AC-2.3 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Session 创建延迟由 Rosen SessionService 和远端 Ability 启动决定，不设量化指标 | 集成测试 | session_wrapper_impl.cpp |
| 安全 | @systemapi 限制系统应用使用 | API 评审 | ui_extension_component.d.ts |
| 可测试性 | onRemoteReady 可通过 Mock SessionWrapper 验证 | 单测 | ui_extension_pattern.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | 无差异 | — | 集成测试 | — |
| 折叠屏 | Placeholder FOLD_TO_EXPAND 占位；SessionViewportConfig.orientation/transform 需响应折叠变化 | 需监听 display 变化 | 集成测试 | ui_extension_pattern.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | UIExtension 有 AccessibilitySessionAdapterUIExtension，通过 AccessibilityChildTreeCallback 接入宿主无障碍树 | AC-1.1 |
| 大字体 | 是 | dpiFollowStrategy = FOLLOW_HOST_DPI 时远端跟随宿主 DPI（含大字体缩放因子） | AC-1.5 |
| 深色模式 | 是 | SessionWrapper::NotifyConfigurationUpdate 传递宿主配置变更到远端 | AC-1.1 |
| 多窗口/分屏 | 是 | SessionViewportConfig 需响应分屏尺寸变化；windowModeFollowStrategy 控制窗口模式跟随 | AC-1.6 |
| 多用户 | 否 | UIExtensionAbility 运行在独立进程 | — |
| 版本升级 | 是 | API 10 起行为不变；后续版本补充 Options 子字段 | AC-1.1 |
| 生态兼容 | 是 | @systemapi 与 EmbeddedComponent (@atomicservice) 共存 | AC-1.1 |

---

## 行为场景

```gherkin
Feature: UIExtensionComponent 创建与 Proxy 通信
  作为 系统应用开发者
  我想要 通过 UIExtensionComponent 创建组件并获取 UIExtensionProxy 进行通信
  以便 在宿主页面中嵌入远端 UIExtensionAbility 的 UI 内容并实现双向数据传递

  # ─── 创建与 Want/Options ──────────────────

  Scenario: 正常创建 UIExtensionComponent
    Given 一个宿主页面
    When 调用 UIExtensionComponent(want, { isTransferringCaller: true, dpiFollowStrategy: FOLLOW_HOST_DPI })
    Then 创建 UIExtensionPattern(isTransferringCaller=true)
    And 创建 SessionWrapperImpl(instanceId, isTransferringCaller=true, SessionType::UI_EXTENSION_ABILITY)
    And 通过 Rosen SessionService 跨进程启动 UIExtensionAbility
    And SessionViewportConfig.isDensityFollowHost_ = true

  Scenario: Want 为空
    Given 一个宿主页面
    When 调用 UIExtensionComponent(emptyWant)
    Then 不创建有效 Session
    And onError 回调被触发

  Scenario: Options 各字段默认值
    Given 一个宿主页面
    When 调用 UIExtensionComponent(want) 不指定 options
    Then isTransferringCaller_ = false
    And dpiFollowStrategy 默认 FOLLOW_UI_EXTENSION_ABILITY_DPI
    And windowModeFollowStrategy 默认 FOLLOW_UI_EXTENSION_ABILITY_WINDOW_MODE

  # ─── Proxy 通信 ───────────────────────────

  Scenario: UIExtensionAbility 连接成功触发 onRemoteReady
    Given 一个 UIExtensionComponent 已创建
    And SessionWrapperImpl 成功连接远端 UIExtensionAbility
    When SessionWrapperImpl::OnConnect 被调用
    Then UIExtensionPattern::FireOnRemoteReadyCallback 被触发
    And ArkTS onRemoteReady 回调收到 UIExtensionProxy 对象

  Scenario: Proxy 异步发送数据
    Given 一个 UIExtensionProxy 已通过 onRemoteReady 获得
    When 调用 proxy.send({ key: 'value' })
    Then UIExtensionProxy::SendDataAsync → SessionWrapper::SendDataAsync
    And ExtensionSession 跨进程传递 WantParams

  Scenario: Proxy 同步发送数据并等待回复
    Given 一个 UIExtensionProxy 已通过 onRemoteReady 获得
    When 调用 proxy.sendSync({ key: 'request' })
    Then UIExtensionProxy::SendDataSync → SessionWrapper::SendDataSync
    And 同步等待远端回复 WantParams
    And 返回远端回复数据

  Scenario: Proxy sendSync 远端未注册回调
    Given 一个 UIExtensionProxy 已通过 onRemoteReady 获得
    And 远端 UIExtensionAbility 未注册 syncReceiver
    When 调用 proxy.sendSync({ key: 'request' })
    Then 抛出 BusinessError 100011

  Scenario: Proxy 注册 asyncReceiver
    Given 一个 UIExtensionProxy 已通过 onRemoteReady 获得
    When 调用 proxy.on('asyncReceiverRegister', callback)
    Then callback 被注册到 onAsyncOnCallbackList_
    And 远端注册 async 数据接收回调时触发 callback(proxy)

  Scenario: Proxy 移除 asyncReceiver
    Given 一个已注册 asyncReceiver 的 UIExtensionProxy
    When 调用 proxy.off('asyncReceiverRegister', specificCallback)
    Then 从 onAsyncOnCallbackList_ 移除 specificCallback

  Scenario: Proxy 清空所有 asyncReceiver
    Given 一个已注册多个 asyncReceiver 的 UIExtensionProxy
    When 调用 proxy.off('asyncReceiverRegister')
    Then onAsyncOnCallbackList_ 被清空

  # ─── Placeholder 机制 ────────────────────

  Scenario: 设置 placeholder 占位内容
    Given 一个宿主页面
    When 调用 UIExtensionComponent(want, { placeholder: myPlaceholder })
    Then PlaceholderType=UNDEFINED 对应的 FrameNode 被挂载到 UIExtensionNode 下

  Scenario: Session 连接成功移除 placeholder
    Given 一个 UIExtensionComponent 已创建且有 placeholder
    And 远端 Session 连接成功
    When OnConnect 回调被触发
    Then RemovePlaceholderNode 移除占位节点
    And 挂载远端 SurfaceNode 替代

  Scenario: 折叠屏变化挂载 FOLD_TO_EXPAND 占位
    Given 一个 UIExtensionComponent 已创建且设置了折叠占位
    When 折叠屏状态变化
    Then PlaceholderType=FOLD_TO_EXPAND 对应的 FrameNode 被挂载
    And PostDelayRemovePlaceholder 延迟移除防止闪烁

  # ─── DPI/WindowMode 策略 ──────────────────

  Scenario: DPI 跟随宿主策略
    Given 一个宿主页面
    When 调用 UIExtensionComponent(want, { dpiFollowStrategy: FOLLOW_HOST_DPI })
    Then SessionViewportConfig.isDensityFollowHost_ = true
    And density_ 取宿主 PipelineContext density

  Scenario: 窗口模式跟随宿主策略
    Given 一个宿主页面
    When 调用 UIExtensionComponent(want, { windowModeFollowStrategy: FOLLOW_HOST_WINDOW_MODE })
    Then UIExtensionPattern.isWindowModeFollowHost_ = true
    And NotifyHostWindowMode 传递宿主 WindowMode 到远端

  # ─── C-API Static Modifier ────────────────

  Scenario: C-API ConstructImpl 创建 UIExtensionComponent
    Given Arkoala 静态范式环境且 WINDOW_SCENE_SUPPORTED 开启
    When 调用 GENERATED_ArkUIUIExtensionComponentModifier::construct(id, flags)
    Then 创建 UIExtensionNode（UIExtensionPattern）

  Scenario: C-API SetOnRemoteReadyImpl 注册回调
    Given 一个已创建的 UIExtensionComponent FrameNode
    When 调用 GENERATED_ArkUIUIExtensionComponentModifier::setOnRemoteReady(node, callback)
    Then UIExtensionStatic::SetOnRemoteReady 注册回调到 UIExtensionPattern
    And onRemoteReady 触发时构造 UIExtensionProxyPeer 并传递到 ArkTS callback

  Scenario: C-API stub 方法不修改状态
    Given 一个已创建的 UIExtensionComponent FrameNode
    When 调用 GENERATED_ArkUIUIExtensionComponentModifier::setOnReceive(node, callback)
    Then 仅输出 LOGE "not supported"，不修改 FrameNode 状态

  # ─── C-API Proxy Accessor ─────────────────

  Scenario: C-API Proxy onAsyncReceiverRegister
    Given 一个 UIExtensionProxyPeer
    When 调用 GENERATED_ArkUIUIExtensionProxyAccessor::onAsyncReceiverRegister(peer, callback)
    Then 添加回调到 peer.onAsyncCallbackList_
    And 调用 Pattern::SetAsyncCallbacks(funcList)

  Scenario: C-API Proxy send stub
    Given 一个 UIExtensionProxyPeer
    When 调用 GENERATED_ArkUIUIExtensionProxyAccessor::send(peer, data)
    Then 仅输出 LOGE "not supported"，不实际发送数据
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：创建/选项/Proxy通信/Placeholder/DPI/WindowMode/C-API；不做什么：事件回调 onReceive/onError/onTerminated/onDrawReady 的详细触发条件（Feat-02）、废弃事件 onResult/onRelease（Feat-03）、SecurityUIExtension/DynamicComponent/IsolatedComponent）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern 如何初始化 SessionWrapper 并管理 Rosen ExtensionSession 生命周期"
  - repo: "openharmony/ace_engine"
    query: "SessionWrapperImpl 创建 ExtensionSession 的完整流程与回调注册"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionProxy send/sendSync 如何通过 SessionWrapper 实现跨进程通信"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern Placeholder 机制 PlaceholderType 挂载与移除逻辑"
  - repo: "openharmony/ace_engine"
    query: "C-API UIExtensionComponentModifier 与 UIExtensionProxyAccessor 的实现状态与 stub 覆盖"
  - repo: "openharmony/ace_engine"
    query: "DpiFollowStrategy 和 WindowModeFollowStrategy 如何映射到 SessionViewportConfig"
```

**关键文档：**
- SDK API：`interface/sdk-js/api/@internal/component/ets/ui_extension_component.d.ts`
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.h`
- Proxy 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_proxy.h`
- SessionWrapper 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/session_wrapper_impl.h`
- C-API Modifier：`frameworks/core/interfaces/native/implementation/ui_extension_component_modifier.cpp`
- C-API ProxyAccessor：`frameworks/core/interfaces/native/implementation/ui_extension_proxy_accessor.cpp`
- Config：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_config.h`
- Session 抽象：`frameworks/core/components_ng/pattern/ui_extension/session_wrapper.h`
