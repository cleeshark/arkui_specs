# 特性规格

> Func-05-12-06-Feat-01 SecurityUIExtension创建/Proxy/安全策略：固化 SecurityUIExtensionComponent 创建流程、Want 与 SecurityUIExtensionOptions 传递机制、isTransferringCaller Token 提升安全策略、dpiFollowStrategy DPI 策略、以及 SecurityUIExtensionProxy send/sendSync/receiver 注册/注销通信机制的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SecurityUIExtension创建/Proxy/安全策略 |
| 特性编号 | Func-05-12-06-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 20+（static）；Proxy send/sendSync/receiver @since 22 static |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SecurityUIExtensionComponent 创建与 Want 规格 | 补录 SecurityUIExtensionComponent(want, options?, content_?) 创建流程、Want 解析、SecuritySessionWrapperImpl 独立管线加载规格 |
| ADDED | 安全策略规格 | 补录 isTransferringCaller Token 提升机制（isTransferringCaller=true → rootToken）规格 |
| ADDED | DPI 策略规格 | 补录 SecurityDpiFollowStrategy enum（FOLLOW_HOST_DPI/FOLLOW_UI_EXTENSION_ABILITY_DPI）及默认值规格 |
| ADDED | SecurityUIExtensionProxy 通信规格 | 补录 SecurityUIExtensionProxy send/sendSync/receiver 注册/注销通信机制规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/06-security-ui-extension-component/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 SecurityUIExtensionComponent 并传入 Want 与选项

**作为** 应用开发者,
**我想要** 通过 SecurityUIExtensionComponent(want, options?, content_?) 创建组件并传入 Want 和 SecurityUIExtensionOptions,
**以便** 在宿主页面中嵌入安全级 UIExtensionAbility 的 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `SecurityUIExtensionComponent(want, { isTransferringCaller: false, dpiFollowStrategy: SecurityDpiFollowStrategy.FOLLOW_UI_EXTENSION_ABILITY_DPI })` THEN 创建 SecurityUIExtensionPattern → 创建 SecuritySessionWrapperImpl（SessionType=SECURITY_UI_EXTENSION_ABILITY(3)）加载 Extension 会话 | 正常 |
| AC-1.2 | WHEN Want 参数无效（action/entity 不匹配任何已注册 SecurityUIExtensionAbility）THEN 不创建 SecuritySessionWrapperImpl；FireOnError 回调传递错误信息 | 异常 |
| AC-1.3 | WHEN SecuritySessionWrapperImpl 创建失败（Extension 启动错误、Session 连接失败）THEN FireOnError 回调传递错误信息 | 异常 |
| AC-1.4 | WHEN 调用 `SecurityUIExtensionComponent(want, options, content_)` 且 content_ 为 CustomBuilder THEN 显示 placeholder 内容直到 Extension 会话加载完成 | 正常 |

### US-2: 通过 SecurityUIExtensionProxy send/sendSync 传递数据

**作为** 应用开发者,
**我想要** 通过 SecurityUIExtensionProxy 的 send 和 sendSync 方法向安全级 Extension 传递数据,
**以便** 宿主应用与安全级 Extension 之间进行安全级数据通信。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN onRemoteReady 回调返回 SecurityUIExtensionProxy THEN 调用 proxy.send(data) 异步发送数据到 Extension 端 | 正常 |
| AC-2.2 | WHEN 调用 proxy.sendSync(data) 同步发送数据到 Extension 端 THEN 返回 Extension 端响应数据 | 正常 |
| AC-2.3 | WHEN proxy.sendSync 连接失败 THEN 抛出错误码 100011 | 异常 |
| AC-2.4 | WHEN proxy.sendSync 发送失败 THEN 抛出错误码 100012 | 异常 |

### US-3: isTransferringCaller 安全策略 Token 提升

**作为** 安全级应用开发者,
**我想要** 通过设置 isTransferringCaller=true 将调用方 Token 提升为 rootToken,
**以便** 安全级 Extension 以更高权限运行以访问受限系统资源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN options.isTransferringCaller=false（默认）THEN SecuritySessionWrapperImpl 使用调用方原始 Token 创建 Extension 会话 | 正常 |
| AC-3.2 | WHEN options.isTransferringCaller=true THEN SecuritySessionWrapperImpl 将调用方 Token 提升为 rootToken 创建 Extension 会话 | 正常 |
| AC-3.3 | WHEN isTransferringCaller 属性从 false 变为 true THEN OnModifyDone 触发 SessionWrapper 重新初始化，Token 提升为 rootToken | 正常 |

### US-4: DPI 策略配置

**作为** 应用开发者,
**我想要** 通过 dpiFollowStrategy 配置 SecurityUIExtension 的 DPI 跟随策略,
**以便** 控制 Extension 界面的 DPI 是跟随宿主还是跟随 Extension 自身。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN options.dpiFollowStrategy=SecurityDpiFollowStrategy.FOLLOW_HOST_DPI(0) THEN Extension 界面 DPI 跟随宿主应用 | 正常 |
| AC-4.2 | WHEN options.dpiFollowStrategy=SecurityDpiFollowStrategy.FOLLOW_UI_EXTENSION_ABILITY_DPI(1)（默认）THEN Extension 界面 DPI 跟随 Extension 自身 | 正常 |
| AC-4.3 | WHEN dpiFollowStrategy 属性变化 THEN OnModifyDone 更新 DPI 策略并触发 Extension 界面重新配置 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1, R-2, R-3, R-4, R-5 | 已有实现 | 代码评审 | `security_ui_extension_pattern.cpp`, `security_session_wrapper_impl.cpp` |
| AC-2.1~2.4 | R-6, R-7, R-8, R-9 | 已有实现 | 代码评审 | `security_ui_extension_proxy.cpp` |
| AC-3.1~3.3 | R-10, R-11, R-12 | 已有实现 | 安全评审 | `security_session_wrapper_impl.cpp` |
| AC-4.1~4.3 | R-13, R-14, R-15 | 已有实现 | 代码评审 | `security_ui_extension_layout_property.h` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `SecurityUIExtensionComponent(want, options)` 被调用 | JSSecurityUIExtension::Create 解析 want/options → SecurityUIExtensionModelNG::Create → 创建 SecurityUIExtensionPattern → 创建 SecuritySessionWrapperImpl | 仅 static 范式 | AC-1.1 |
| R-2 | 行为 | SecurityUIExtensionPattern::OnAttachToFrameNode | 注册 onRemoteReady/onReceive/onError/onTerminated 到 SecurityUIExtensionEventHub；创建 SecuritySessionWrapperImpl；注册到 UIExtensionManager aliveSecurityUIExtensions_ | — | AC-1.1 |
| R-3 | 行为 | SecuritySessionWrapperImpl 创建 | 基于 ExtensionSession 创建独立渲染管线，SessionType=SECURITY_UI_EXTENSION_ABILITY(3)；根据 isTransferringCaller 决定 Token 提升策略 | SessionType 固定为 3 | AC-1.1 |
| R-4 | 异常 | Want 参数无效 | SecuritySessionWrapperImpl 无法连接到目标 SecurityUIExtensionAbility → FireOnError 回调 | — | AC-1.2 |
| R-5 | 异常 | SecuritySessionWrapperImpl 创建失败 | Extension 启动错误或 Session 连接失败 → FireOnError 回调传递错误信息 | — | AC-1.3 |
| R-6 | 行为 | SecurityUIExtensionProxy.send(data) | 异步发送数据到 Extension 端，通过 IPC 通道传递 | — | AC-2.1 |
| R-7 | 行为 | SecurityUIExtensionProxy.sendSync(data) | 同步发送数据到 Extension 端，返回 Extension 端响应数据 | — | AC-2.2 |
| R-8 | 异常 | proxy.sendSync 连接失败 | 抛出错误码 100011 | 100011 为连接失败专用错误码 | AC-2.3 |
| R-9 | 异常 | proxy.sendSync 发送失败 | 抛出错误码 100012 | 100012 为发送失败专用错误码 | AC-2.4 |
| R-10 | 行为 | isTransferringCaller=false（默认） | SecuritySessionWrapperImpl 使用调用方原始 Token 创建 Extension 会话 | 默认安全策略：不提升权限 | AC-3.1 |
| R-11 | 行为 | isTransferringCaller=true | SecuritySessionWrapperImpl 将调用方 Token 提升为 rootToken 创建 Extension 会话 | rootToken 提升是安全级核心区别 | AC-3.2 |
| R-12 | 行为 | isTransferringCaller 属性从 false 变为 true | OnModifyDone 检测属性变化 → 触发 SessionWrapper 重新初始化 → Token 提升为 rootToken | 属性变更触发重新初始化 | AC-3.3 |
| R-13 | 行为 | dpiFollowStrategy=FOLLOW_HOST_DPI(0) | Extension 界面 DPI 跟随宿主应用 DPI 设置 | — | AC-4.1 |
| R-14 | 行为 | dpiFollowStrategy=FOLLOW_UI_EXTENSION_ABILITY_DPI(1)（默认） | Extension 界面 DPI 跟随 Extension 自身 DPI 设置 | 默认值 | AC-4.2 |
| R-15 | 行为 | dpiFollowStrategy 属性变化 | OnModifyDone 更新 DPI 策略 → 触发 Extension 界面重新配置 | — | AC-4.3 |
| R-16 | 边界 | 无 C-API modifier | @noninterop 标记明确限制，NDK 场景不适用 SecurityUIExtensionComponent | 仅 ArkTS static 范式 | AC-1.1 |
| R-17 | 边界 | 不支持 onRelease/onResult/onDrawReady | SecurityUIExtension 仅支持四种回调：onRemoteReady/onReceive/onError/onTerminated | 安全级生命周期更严格 | AC-1.1 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1, R-2, R-3 | 代码评审 | SecurityUIExtension 创建流程完整性（JSBridge→ModelNG→Pattern→SessionWrapper） |
| VM-2 | AC-1.2, R-4 | 代码评审 | 无效 Want 的错误处理 |
| VM-3 | AC-1.3, R-5 | 代码评审 | SessionWrapper 创建失败的错误处理 |
| VM-4 | AC-2.1~2.2, R-6, R-7 | 代码评审 | Proxy send/sendSync 通信机制 |
| VM-5 | AC-2.3~2.4, R-8, R-9 | 代码评审 | Proxy sendSync 异常错误码 |
| VM-6 | AC-3.1~3.2, R-10, R-11 | 安全评审 | isTransferringCaller Token 提升机制 |
| VM-7 | AC-3.3, R-12 | 代码评审 | isTransferringCaller 属性变更触发重新初始化 |
| VM-8 | AC-4.1~4.3, R-13, R-14, R-15 | 代码评审 | DPI 策略配置与变更 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `SecurityUIExtensionComponent(want: Want, options?: SecurityUIExtensionOptions, content_?: CustomBuilder)` | Static | 创建安全嵌入组件 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `SecurityUIExtensionOptions { isTransferringCaller?, placeholder?, dpiFollowStrategy? }` | Static | 创建选项 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `SecurityDpiFollowStrategy { FOLLOW_HOST_DPI = 0, FOLLOW_UI_EXTENSION_ABILITY_DPI = 1 }` | Static | DPI 策略枚举 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `onRemoteReady(callback: (proxy: SecurityUIExtensionProxy) => void)` | Static | 远端就绪回调 | `@internal/component/ets/security_ui_extension_component.d.ts` | 20 | — |
| `SecurityUIExtensionProxy.send(data)` | Static | 异步发送数据 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |
| `SecurityUIExtensionProxy.sendSync(data)` | Static | 同步发送数据 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | throws 100011/100012 |
| `SecurityUIExtensionProxy.onAsyncReceiverRegister` | Static | 注册异步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |
| `SecurityUIExtensionProxy.onSyncReceiverRegister` | Static | 注册同步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |
| `SecurityUIExtensionProxy.offAsyncReceiverRegister` | Static | 注销异步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |
| `SecurityUIExtensionProxy.offSyncReceiverRegister` | Static | 注销同步接收器 | `@internal/component/ets/security_ui_extension_component.d.ts` | 22 | — |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `SecurityUIExtensionOptions` | `{ isTransferringCaller?: boolean; placeholder?: CustomBuilder; dpiFollowStrategy?: SecurityDpiFollowStrategy }` | `security_ui_extension_component.d.ts` |
| `SecurityDpiFollowStrategy` | `{ FOLLOW_HOST_DPI = 0, FOLLOW_UI_EXTENSION_ABILITY_DPI = 1 }` | `security_ui_extension_component.d.ts` |
| `SecurityUIExtensionProxy` | `class { send(data), sendSync(data), onAsyncReceiverRegister, onSyncReceiverRegister, offAsyncReceiverRegister, offSyncReceiverRegister }` | `security_ui_extension_component.d.ts` |
| `TerminationInfo` | `{ code: number }` | `security_ui_extension_component.d.ts` |
| `ReceiveCallback` | `(data: Object) => void` | `security_ui_extension_component.d.ts` |
| `ErrorCallback` | `(error: Object) => void` | `security_ui_extension_component.d.ts` |

**C-API (NDK) 接口：**

| 说明 | 结论 |
|------|------|
| 无 C-API modifier | SecurityUIExtensionComponent 标记为 @noninterop，不提供 C-API modifier |

### 变更/废弃 API

无变更/废弃 API。

---

## 接口规格

### 接口定义 — SecurityUIExtensionComponent(want, options?, content_?)

| 属性 | 值 |
|------|-----|
| 函数签名 | `SecurityUIExtensionComponentAttribute SecurityUIExtensionComponent(Want want, SecurityUIExtensionOptions? options, CustomBuilder? content_)` |
| 返回值 | `SecurityUIExtensionComponentAttribute` — 组件属性对象 |
| 开放范围 | Static (@since 20) |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| want | Want | 是 | — | action/entity 必须匹配已注册 SecurityUIExtensionAbility |
| options | SecurityUIExtensionOptions | 否 | { isTransferringCaller: false, dpiFollowStrategy: FOLLOW_UI_EXTENSION_ABILITY_DPI } | 无约束 |
| options.isTransferringCaller | boolean | 否 | false | true 时 Token 提升为 rootToken |
| options.dpiFollowStrategy | SecurityDpiFollowStrategy | 否 | FOLLOW_UI_EXTENSION_ABILITY_DPI(1) | 仅接受枚举值 0 或 1 |
| options.placeholder | CustomBuilder | 否 | undefined | Extension 加载前显示的占位内容 |
| content_ | CustomBuilder | 否 | undefined | 同 placeholder，加载前显示 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | want 有效，options 为默认值 | 创建 SecuritySessionWrapperImpl（原始 Token，DPI 跟随 Extension） | AC-1.1 |
| 2 | want 无效（action/entity 不匹配） | FireOnError 回调 | AC-1.2 |
| 3 | SessionWrapper 创建失败 | FireOnError 回调 | AC-1.3 |
| 4 | content_/placeholder 非空 | 显示占位内容直到 Extension 加载完成 | AC-1.4 |

### 接口定义 — SecurityUIExtensionProxy.send(data)

| 属性 | 值 |
|------|-----|
| 函数签名 | `void SecurityUIExtensionProxy.send(Object data)` |
| 返回值 | void（异步发送） |
| 开放范围 | Static (@since 22) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| data | Object | 是 | — | 通过 IPC 传递到 Extension 端 |

### 接口定义 — SecurityUIExtensionProxy.sendSync(data)

| 属性 | 值 |
|------|-----|
| 函数签名 | `Object SecurityUIExtensionProxy.sendSync(Object data)` |
| 返回值 | Object — Extension 端响应数据 |
| 开放范围 | Static (@since 22) |
| 错误码 | 100011（连接失败），100012（发送失败） |
| 关联 AC | AC-2.2 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| data | Object | 是 | — | 通过 IPC 同步传递到 Extension 端 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | sendSync 成功 | 返回 Extension 端响应数据 | AC-2.2 |
| 2 | sendSync 连接失败 | 抛出 100011 | AC-2.3 |
| 3 | sendSync 发送失败 | 抛出 100012 | AC-2.4 |

### 接口定义 — SecurityDpiFollowStrategy

| 属性 | 值 |
|------|-----|
| 函数签名 | `enum SecurityDpiFollowStrategy` |
| 开放范围 | Static (@since 20) |
| 关联 AC | AC-4.1, AC-4.2 |

**枚举值：**

| 枚举值 | 数值 | 说明 | 关联 AC |
|--------|------|------|---------|
| FOLLOW_HOST_DPI | 0 | Extension 界面 DPI 跟随宿主应用 | AC-4.1 |
| FOLLOW_UI_EXTENSION_ABILITY_DPI | 1 | Extension 界面 DPI 跟随 Extension 自身（默认） | AC-4.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 20（组件级），API 22（Proxy send/sendSync/receiver）
- **API 版本号策略:** 组件创建/Options/DPI 策略 @since 20；Proxy 通信 @since 22

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| SecurityUIExtension 使用独立 SecurityUIExtensionProxy | Proxy 独立于 UIExtensionProxy，有独立权限边界 | AC-2.1~2.4 |
| isTransferringCaller Token 提升为 rootToken | 安全级核心区别，仅在 SecurityUIExtension 支持 | AC-3.1~3.3 |
| SessionType=SECURITY_UI_EXTENSION_ABILITY(3) | 区别于 UI_EXTENSION_ABILITY(1) 和 ISOLATED_EXTENSION_ABILITY(2) | AC-1.1 |
| 无 C-API modifier (@noninterop) | 仅 ArkTS static 范式可用，NDK 场景不适用 | AC-1.1 |
| 不支持 onRelease/onResult/onDrawReady | 安全级仅四种回调 | AC-1.1 |
| UIExtensionManager 独立追踪 aliveSecurityUIExtensions_ | 安全级 Extension 在 Manager 中独立管理 | AC-1.1 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | SecuritySessionWrapperImpl 创建独立管线有固有初始化延迟，不设量化指标 | 集成测试 | security_session_wrapper_impl.cpp |
| 安全 | isTransferringCaller=true 提升 Token 为 rootToken，需安全评审 | 安全评审 | security_session_wrapper_impl.cpp |
| 可测试性 | onRemoteReady/onError 可通过 Mock ExtensionSession 验证 | 单测 | security_ui_extension_pattern.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | DPI 策略影响更大 | dpiFollowStrategy 需正确配置 | 集成测试 | security_ui_extension_layout_property.h |
| 折叠屏 | DPI 策略需响应折叠状态变化 | FOLLOW_HOST_DPI 时需监听 display 变化 | 集成测试 | security_session_wrapper_impl.cpp |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | SecurityUIExtensionPattern 继承 PlatformAccessibilityBase | AC-1.1 |
| 大字体 | 是 | DPI 策略影响字体大小 | AC-4.1~4.3 |
| 深色模式 | 否 | Extension 使用独立管线 | — |
| 多窗口/分屏 | 是 | DPI 策略需响应分屏变化 | AC-4.1~4.3 |
| 多用户 | 否 | Extension 运行在独立会话 | — |
| 版本升级 | 否 | API 20 起新增，无历史兼容负担 | — |
| 生态兼容 | 否 | 仅 static 范式，无 C-API | — |

---

## 行为场景

```gherkin
Feature: SecurityUIExtension 创建/Proxy/安全策略
  作为 应用开发者
  我想要 通过 SecurityUIExtensionComponent 创建安全级嵌入组件并通过 Proxy 通信
  以便 在宿主页面中嵌入安全级 UIExtensionAbility 的 UI 内容

  # ─── 创建与 Want ─────────────────────────

  Scenario: 正常创建 SecurityUIExtensionComponent
    Given 一个宿主页面
    When 调用 SecurityUIExtensionComponent(want, { isTransferringCaller: false, dpiFollowStrategy: FOLLOW_UI_EXTENSION_ABILITY_DPI })
    Then 创建 SecurityUIExtensionPattern → SecuritySessionWrapperImpl (SessionType=3)
    And UIExtensionManager 注册到 aliveSecurityUIExtensions_
    And ExtensionSession 加载 SecurityUIExtensionAbility 内容

  Scenario: Want 无效
    Given 一个宿主页面
    When 调用 SecurityUIExtensionComponent(want_invalid, {})
    Then SecuritySessionWrapperImpl 无法连接到目标 SecurityUIExtensionAbility
    And onError 回调被触发，传递错误信息

  Scenario: SessionWrapper 创建失败
    Given 一个宿主页面
    When SecuritySessionWrapperImpl 创建过程中 Extension 启动错误
    Then onError 回调被触发，传递错误信息

  Scenario: placeholder 显示占位内容
    Given 一个宿主页面
    When 调用 SecurityUIExtensionComponent(want, { placeholder: placeholderBuilder })
    Then 在 Extension 加载完成前显示 placeholder 内容
    And Extension 加载完成后替换为 Extension 界面

  # ─── Proxy 通信 ──────────────────────────

  Scenario: Proxy send 异步发送数据
    Given SecurityUIExtensionProxy 已通过 onRemoteReady 获取
    When 调用 proxy.send({ key: 'value' })
    Then 数据通过 IPC 异步传递到 Extension 端

  Scenario: Proxy sendSync 同步发送数据
    Given SecurityUIExtensionProxy 已通过 onRemoteReady 获取
    When 调用 proxy.sendSync({ key: 'value' })
    Then 数据通过 IPC 同步传递到 Extension 端
    And 返回 Extension 端响应数据

  Scenario: Proxy sendSync 连接失败
    Given SecurityUIExtensionProxy 连接断开
    When 调用 proxy.sendSync(data)
    Then 抛出错误码 100011

  Scenario: Proxy sendSync 发送失败
    Given SecurityUIExtensionProxy 连接正常但发送失败
    When 调用 proxy.sendSync(data)
    Then 抛出错误码 100012

  # ─── 安全策略 ────────────────────────────

  Scenario: isTransferringCaller=false 默认不提升 Token
    Given 一个宿主页面
    When 调用 SecurityUIExtensionComponent(want, { isTransferringCaller: false })
    Then SecuritySessionWrapperImpl 使用调用方原始 Token 创建 Extension 会话

  Scenario: isTransferringCaller=true Token 提升为 rootToken
    Given 一个宿主页面
    When 调用 SecurityUIExtensionComponent(want, { isTransferringCaller: true })
    Then SecuritySessionWrapperImpl 将调用方 Token 提升为 rootToken 创建 Extension 会话

  Scenario: isTransferringCaller 属性从 false 变为 true
    Given SecurityUIExtensionComponent 已创建且 isTransferringCaller=false
    When 开发者更新 isTransferringCaller 为 true
    Then OnModifyDone 检测属性变化
    And 触发 SessionWrapper 重新初始化，Token 提升为 rootToken

  # ─── DPI 策略 ────────────────────────────

  Scenario: dpiFollowStrategy=FOLLOW_HOST_DPI
    Given 一个宿主页面
    When 调用 SecurityUIExtensionComponent(want, { dpiFollowStrategy: SecurityDpiFollowStrategy.FOLLOW_HOST_DPI })
    Then Extension 界面 DPI 跟随宿主应用

  Scenario: dpiFollowStrategy=FOLLOW_UI_EXTENSION_ABILITY_DPI 默认
    Given 一个宿主页面
    When 调用 SecurityUIExtensionComponent(want, {}) 或 { dpiFollowStrategy: SecurityDpiFollowStrategy.FOLLOW_UI_EXTENSION_ABILITY_DPI }
    Then Extension 界面 DPI 跟随 Extension 自身

  Scenario: dpiFollowStrategy 属性变化
    Given SecurityUIExtensionComponent 已创建且 dpiFollowStrategy=FOLLOW_HOST_DPI
    When 开发者更新 dpiFollowStrategy 为 FOLLOW_UI_EXTENSION_ABILITY_DPI
    Then OnModifyDone 更新 DPI 策略
    And 触发 Extension 界面重新配置
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：创建/Proxy/安全策略/DPI 策略；不做什么：onRelease/onResult/onDrawReady、C-API modifier）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "SecurityUIExtensionPattern OnAttachToFrameNode OnModifyDone lifecycle"
  - repo: "openharmony/ace_engine"
    query: "SecuritySessionWrapperImpl isTransferringCaller token elevation rootToken"
  - repo: "openharmony/ace_engine"
    query: "SecurityUIExtensionProxy send sendSync onAsyncReceiverRegister onSyncReceiverRegister"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionManager aliveSecurityUIExtensions securityUiExtensionFocused"
```

**关键文档：**
- SDK API：`interface/sdk-js/api/@internal/component/ets/security_ui_extension_component.d.ts`
- Pattern 层：`frameworks/core/components_ng/pattern/security_ui_extension/security_ui_extension_pattern.h`
- Session Wrapper 层：`frameworks/core/components_ng/pattern/security_ui_extension/security_session_wrapper_impl.h`
- Proxy 层：`frameworks/core/components_ng/pattern/security_ui_extension/security_ui_extension_proxy.h`
- Manager 层：`frameworks/core/components_ng/manager/ui_extension_manager/ui_extension_manager.h`
