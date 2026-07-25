# 特性规格

> Func-05-12-03-Feat-03 UIExtensionComponent废弃事件与兼容性：固化 UIExtensionComponent onResult/onRelease 1.2 compat 废逝行为的规格。onResult 和 onRelease 仅在 IsCompatibleOldVersion()=true（即 onTerminatedCallback_=nullptr 且 sessionType_=UI_EXTENSION_ABILITY）时触发，新注册 onTerminated 的应用不再走 onResult/onRelease 路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIExtensionComponent废弃事件与兼容性 |
| 特性编号 | Func-05-12-03-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 10+（1.2 compat only） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | onResult 1.2 compat 行为规格 | 补录 onResult(callback: OnResultCallback) 注册、IsCompatibleOldVersion()=true 条件下 SessionWrapperImpl::InitTransferAbilityResultFunc 路径选择、FireOnResultCallback 触发链规格 |
| ADDED | onRelease 1.2 compat 行为规格 | 补录 onRelease(callback: OnReleaseCallback) 注册、SessionWrapperImpl::OnDisconnect 且 IsCompatibleOldVersion()=true 条件下 FireOnReleaseCallback 触发链规格 |
| ADDED | onResult/onRelease 与 onTerminated 路径互斥规格 | 补录 IsCompatibleOldVersion() 判断逻辑（onTerminatedCallback_=nullptr → onResult 路径；onTerminatedCallback_≠nullptr → onTerminated 路径）规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/03-ui-extension-component/design.md` | Baselined |
| Feat-01 | `specs/05-ui-components/12-embedded-display-components/03-ui-extension-component/Feat-01-ui-extension-creation-proxy-spec.md` | Baselined |
| Feat-02 | `specs/05-ui-components/12-embedded-display-components/03-ui-extension-component/Feat-02-ui-extension-events-spec.md` | Baselined |

---

## 用户故事

### US-1: onResult 兼容性行为

**作为** 使用 1.2 compat 版本的系统应用开发者,
**我想要** 通过 onResult(callback) 接收 ExtensionAbility 返回结果 {code, data},
**以便** 在未注册 onTerminated 的旧版本应用中处理 ExtensionAbility 终止返回的数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `onResult(callback)` THEN UIExtensionModel::SetOnResult 将 callback 注册到 UIExtensionPattern.onResultCallback_ | 正常 |
| AC-1.2 | WHEN 远端 UIExtensionAbility 调用 terminateWithResult(code, want) 且 IsCompatibleOldVersion()=true THEN SessionWrapperImpl::InitTransferAbilityResultFunc 判断 sessionType_=UI_EXTENSION_ABILITY && IsCompatibleOldVersion() → FireOnResultCallback(code, want) → callback(code, Want) | 正常 |
| AC-1.3 | WHEN IsCompatibleOldVersion()=false（即 onTerminatedCallback_≠nullptr）THEN terminateWithResult 走 onTerminated 路径，onResult 不触发 | 正常 |
| AC-1.4 | WHEN onResult 回调触发 THEN UIExtensionPattern 状态变为 DESTRUCTION | 正常 |
| AC-1.5 | WHEN UIExtensionPattern 状态已为 DESTRUCTION THEN onResult 回调不触发（state_ != DESTRUCTION 检查） | 边界 |
| AC-1.6 | WHEN onResultCallback_ 为空 THEN 不触发 onResult 回调 | 异常 |

### US-2: onRelease 兼容性行为

**作为** 使用 1.2 compat 版本的系统应用开发者,
**我想要** 通过 onRelease(callback) 接收 ExtensionAbility 释放通知 {code},
**以便** 在未注册 onTerminated 的旧版本应用中处理 ExtensionAbility 断开连接事件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `onRelease(callback)` THEN UIExtensionModel::SetOnRelease 将 callback 注册到 UIExtensionPattern.onReleaseCallback_ | 正常 |
| AC-2.2 | WHEN SessionWrapperImpl::OnDisconnect 且 IsCompatibleOldVersion()=true THEN FireOnReleaseCallback(static_cast<int32_t>(isAbnormal)) → callback(releaseCode) | 正常 |
| AC-2.3 | WHEN IsCompatibleOldVersion()=false THEN OnDisconnect 走 onTerminated 或 onError 路径，onRelease 不触发 | 正常 |
| AC-2.4 | WHEN onRelease 回调触发 THEN UIExtensionPattern 状态变为 DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；sessionWrapper_->OnReleaseDone() | 正常 |
| AC-2.5 | WHEN onReleaseCallback_ 为空 THEN 不触发 onRelease 回调 | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1, R-2, R-3, R-4, R-5, R-6 | 已有实现 | 代码评审 | `ui_extension_pattern.cpp:1629-1648`, `session_wrapper_impl.cpp:280-321` |
| AC-2.1~2.5 | R-7, R-8, R-9, R-10, R-11 | 已有实现 | 代码评审 | `ui_extension_pattern.cpp:1570-1588`, `session_wrapper_impl.cpp:1162-1165` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `onResult(callback)` 被调用 | UIExtensionModel::SetOnResult → UIExtensionPattern::SetOnResultCallback(std::move(callback)) | 仅 UI_EXTENSION_ABILITY SessionType | AC-1.1 |
| R-2 | 行为 | 远端 terminateWithResult 且 IsCompatibleOldVersion()=true | SessionWrapperImpl::InitTransferAbilityResultFunc 判断 sessionType_=UI_EXTENSION_ABILITY && IsCompatibleOldVersion() → FireOnResultCallback(code, want) → callback(code, Want) | onResult 与 onTerminated 路径互斥 | AC-1.2 |
| R-3 | 行为 | IsCompatibleOldVersion()=false | terminateWithResult 走 onTerminated 路径；onResult 不触发 | IsCompatibleOldVersion() = (sessionType_=UI_EXTENSION_ABILITY && onTerminatedCallback_=nullptr) | AC-1.3 |
| R-4 | 行为 | FireOnResultCallback 执行 | 检查 state_ != DESTRUCTION → ContainerScope(instanceId_) → onResultCallback_(code, want) → state_ = DESTRUCTION | 防止重复回调 | AC-1.4 |
| R-5 | 边界 | UIExtensionPattern.state_=DESTRUCTION 时 onResult 触发 | onResultCallback_ 检查 state_ != DESTRUCTION；若已为 DESTRUCTION 则不回调 | — | AC-1.5 |
| R-6 | 异常 | onResultCallback_ 为空 | 不触发 onResult 回调 | — | AC-1.6 |
| R-7 | 行为 | `onRelease(callback)` 被调用 | UIExtensionModel::SetOnRelease → UIExtensionPattern::SetOnReleaseCallback(std::move(callback)) | 仅 UI_EXTENSION_ABILITY SessionType | AC-2.1 |
| R-8 | 行为 | SessionWrapperImpl::OnDisconnect 且 IsCompatibleOldVersion()=true | FireOnReleaseCallback(static_cast<int32_t>(isAbnormal)) → callback(releaseCode)；return 不继续走 onTerminated/onError 路径 | onRelease 与 onTerminated/onError 路径互斥 | AC-2.2 |
| R-9 | 行为 | IsCompatibleOldVersion()=false | OnDisconnect 走 onTerminated(isAbnormal=false) 或 onError(isAbnormal=true) 路径；onRelease 不触发 | — | AC-2.3 |
| R-10 | 行为 | FireOnReleaseCallback 执行 | state_ = DESTRUCTION；SetEventProxyFlag(EVENT_NONE)；onReleaseCallback_(releaseCode)；sessionWrapper_->OnReleaseDone() | OnReleaseDone 释放 Session | AC-2.4 |
| R-11 | 异常 | onReleaseCallback_ 为空 | 不触发 onRelease 回调 | — | AC-2.5 |
| R-12 | 定义 | IsCompatibleOldVersion() 判断 | ContainerScope(instanceId_)；return (sessionType_ == SessionType::UI_EXTENSION_ABILITY) && (onTerminatedCallback_ == nullptr) | 仅 UI_EXTENSION_ABILITY + 未注册 onTerminated 时返回 true | AC-1.2, AC-2.2 |
| R-13 | 边界 | onResult/onRelease 仅用于 1.2 compat | "only for 1.2 begin/end" 注释标记在 C++ 源码中；新应用应使用 onTerminated 替代 | SecurityUIExtension/Embedded/Dynamic/Isolated 不支持 onResult/onRelease | 全 AC |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3, R-1, R-2, R-3 | 代码评审 | onResult 注册与 IsCompatibleOldVersion 路径选择 |
| VM-2 | AC-1.4~1.6, R-4, R-5, R-6 | 代码评审 | onResult 触发、状态检查、空回调 |
| VM-3 | AC-2.1~2.3, R-7, R-8, R-9 | 代码评审 | onRelease 注册与 IsCompatibleOldVersion 路径选择 |
| VM-4 | AC-2.4~2.5, R-10, R-11 | 代码评审 | onRelease 触发、OnReleaseDone、空回调 |
| VM-5 | R-12, R-13 | 代码评审 | IsCompatibleOldVersion 判断逻辑 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `onResult(callback: OnResultCallback)` | System (1.2 compat) | Extension 返回结果回调（仅兼容旧版本） | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |
| `onRelease(callback: OnReleaseCallback)` | System (1.2 compat) | Extension 释放回调（仅兼容旧版本） | `@internal/component/ets/ui_extension_component.d.ts` | 10 | @systemapi |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `OnResultCallback` | `(code: number, data: Want) => void` | `ui_extension_component.d.ts` |
| `OnReleaseCallback` | `(code: number) => void` | `ui_extension_component.d.ts` |
| `IsCompatibleOldVersion()` (C++) | `return (sessionType_ == SessionType::UI_EXTENSION_ABILITY) && (onTerminatedCallback_ == nullptr)` | `ui_extension_pattern.cpp:1644-1648` |

### 变更/废弃 API

| API | 废弃状态 | 替代 API | 说明 |
|-----|----------|----------|------|
| onResult | 1.2 compat only（不推荐新应用使用） | onTerminated | 仅在 IsCompatibleOldVersion()=true 时触发 |
| onRelease | 1.2 compat only（不推荐新应用使用） | onTerminated + onError | 仅在 IsCompatibleOldVersion()=true 时触发 |

---

## 接口规格

### 接口定义 — onResult(callback: OnResultCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onResult(callback: OnResultCallback)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi, 1.2 compat only) |
| 错误码 | N/A |
| 废弃状态 | 1.2 compat only — 新应用应使用 onTerminated 替代 |
| 关联 AC | AC-1.1~1.6 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | OnResultCallback (code: number, data: Want) => void | 是 | — | 仅在 IsCompatibleOldVersion()=true 时触发 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | terminateWithResult + IsCompatibleOldVersion()=true | FireOnResultCallback(code, want) → callback(code, Want) | AC-1.2 |
| 2 | terminateWithResult + IsCompatibleOldVersion()=false | 走 onTerminated 路径；onResult 不触发 | AC-1.3 |
| 3 | state_=DESTRUCTION | 不触发 callback | AC-1.5 |
| 4 | onResultCallback_ 为空 | 不触发 callback | AC-1.6 |

**兼容性规则：**

| 条件 | 路径选择 | 说明 |
|------|----------|------|
| onTerminatedCallback_=nullptr 且 sessionType_=UI_EXTENSION_ABILITY | onResult 路径 | IsCompatibleOldVersion()=true |
| onTerminatedCallback_≠nullptr | onTerminated 路径 | IsCompatibleOldVersion()=false |

### 接口定义 — onRelease(callback: OnReleaseCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIExtensionComponentAttribute onRelease(callback: OnReleaseCallback)` |
| 返回值 | `UIExtensionComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi, 1.2 compat only) |
| 错误码 | N/A |
| 废弃状态 | 1.2 compat only — 新应用应使用 onTerminated 替代 |
| 关联 AC | AC-2.1~2.5 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | OnReleaseCallback (code: number) => void | 是 | — | 仅在 IsCompatibleOldVersion()=true 时触发 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | OnDisconnect + IsCompatibleOldVersion()=true | FireOnReleaseCallback(isAbnormal) → callback(releaseCode) | AC-2.2 |
| 2 | OnDisconnect + IsCompatibleOldVersion()=false | 走 onTerminated/onError 路径；onRelease 不触发 | AC-2.3 |
| 3 | onRelease 触发后 | state_=DESTRUCTION；OnReleaseDone 释放 Session | AC-2.4 |
| 4 | onReleaseCallback_ 为空 | 不触发 callback | AC-2.5 |

**兼容性规则：**

| 条件 | OnDisconnect 路径选择 | 说明 |
|------|----------------------|------|
| IsCompatibleOldVersion()=true | onRelease 路径 | return 不继续走 onTerminated/onError |
| IsCompatibleOldVersion()=false, isAbnormal=true | onError 路径 | FireOnErrorCallback(EXITED_ABNORMALLY) |
| IsCompatibleOldVersion()=false, isAbnormal=false | onTerminated 路径 | FireOnTerminatedCallback(0, nullptr) |

---

## 兼容性声明

- **已有 API 行为变更:** 否（onResult/onRelease 行为不变，但明确标注为 1.2 compat only）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（onResult/onRelease 从 API 10 存在）
- **废弃策略:** onResult/onRelease 仅在 IsCompatibleOldVersion()=true 时触发；新应用注册 onTerminated 后自动走 onTerminated 路径，onResult/onRelease 不再触发
- **向前兼容:** 注册 onTerminated 的应用不受 onResult/onRelease 影响

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| IsCompatibleOldVersion() 判断基于 onTerminatedCallback_ 是否注册 | 未注册 onTerminated → 老版本兼容路径（onResult/onRelease）；已注册 onTerminated → 新路径 | AC-1.2, AC-1.3, AC-2.2, AC-2.3 |
| onResult/onRelease 仅适用于 SessionType=UI_EXTENSION_ABILITY | Embedded/Security/Dynamic/Isolated 组件不支持 onResult/onRelease | 全 AC |
| onRelease 回调后 return 不继续走 onTerminated/onError | onRelease 与 onTerminated/onError 路径互斥 | AC-2.2 |
| "only for 1.2 begin/end" 注释标记 | 源码中明确标记 compat 代码范围 | AC-1.1, AC-2.1 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无额外性能开销 | 集成测试 | ui_extension_pattern.cpp |
| 安全 | @systemapi 限制系统应用使用 | API 评审 | ui_extension_component.d.ts |
| 可测试性 | IsCompatibleOldVersion() 可通过注册/不注册 onTerminated 切换路径验证 | 单测 | ui_extension_pattern.cpp |
| 兼容性 | 旧版本应用（未注册 onTerminated）行为不受影响 | 集成测试 | session_wrapper_impl.cpp |

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
| 无障碍 | 否 | compat 事件不影响无障碍树 | — |
| 大字体 | 否 | compat 事件不涉及字体 | — |
| 深色模式 | 否 | compat 事件不涉及配色 | — |
| 多窗口/分屏 | 否 | compat 事件不受窗口模式影响 | — |
| 多用户 | 否 | Extension 运行在独立进程 | — |
| 版本升级 | 是 | 旧版本应用需注意 onResult/onRelease 仅 1.2 compat 路径 | AC-1.2 |
| 生态兼容 | 是 | 新应用推荐使用 onTerminated 替代 onResult/onRelease | 全 AC |

---

## 行为场景

```gherkin
Feature: UIExtensionComponent 废弃事件 onResult/onRelease 与兼容性
  作为 旧版本系统应用开发者
  我想要 通过 onResult/onReceive 接收 ExtensionAbility 终止和释放事件
  以便 在未使用 onTerminated 的旧版本应用中处理 Extension 生命周期事件

  # ─── onResult 兼容性行为 ────────────────────

  Scenario: 注册 onResult 回调
    Given 一个 UIExtensionComponent 已创建
    When 调用 .onResult(callback)
    Then UIExtensionModel::SetOnResult 注册 callback 到 UIExtensionPattern.onResultCallback_

  Scenario: IsCompatibleOldVersion=true 时 terminateWithResult 走 onResult 路径
    Given UIExtensionPattern.onResultCallback_ 已注册
    And UIExtensionPattern.onTerminatedCallback_ 为 nullptr
    And sessionType_ = UI_EXTENSION_ABILITY
    When 远端 UIExtensionAbility 调用 terminateWithResult(0, want)
    Then IsCompatibleOldVersion() 返回 true
    And FireOnResultCallback(0, want)
    And callback 收到 (code=0, data=Want)
    And UIExtensionPattern state_ = DESTRUCTION

  Scenario: IsCompatibleOldVersion=false 时 terminateWithResult 走 onTerminated 路径
    Given UIExtensionPattern.onTerminatedCallback_ 已注册（非 nullptr）
    When 远端 UIExtensionAbility 调用 terminateWithResult(0, want)
    Then IsCompatibleOldVersion() 返回 false
    And FireOnTerminatedCallback(0, WantWrapOhos(want))
    And onResult 不触发

  Scenario: onResult state_=DESTRUCTION 时不回调
    Given UIExtensionPattern.state_ = DESTRUCTION
    And UIExtensionPattern.onResultCallback_ 已注册
    When terminateWithResult 事件到达
    Then onResultCallback_ 检查 state_==DESTRUCTION
    And 不触发 callback

  # ─── onRelease 兼容性行为 ────────────────────

  Scenario: 注册 onRelease 回调
    Given 一个 UIExtensionComponent 已创建
    When 调用 .onRelease(callback)
    Then UIExtensionModel::SetOnRelease 注册 callback 到 UIExtensionPattern.onReleaseCallback_

  Scenario: IsCompatibleOldVersion=true 时 OnDisconnect 走 onRelease 路径
    Given UIExtensionPattern.onReleaseCallback_ 已注册
    And UIExtensionPattern.onTerminatedCallback_ 为 nullptr
    And sessionType_ = UI_EXTENSION_ABILITY
    When SessionWrapperImpl::OnDisconnect(isAbnormal=false)
    Then IsCompatibleOldVersion() 返回 true
    And FireOnReleaseCallback(static_cast<int32_t>(false)) → callback(0)
    And UIExtensionPattern state_ = DESTRUCTION
    And sessionWrapper_->OnReleaseDone()

  Scenario: IsCompatibleOldVersion=false 时 OnDisconnect 走 onTerminated/onError 路径
    Given UIExtensionPattern.onTerminatedCallback_ 已注册（非 nullptr）
    When SessionWrapperImpl::OnDisconnect(isAbnormal=false)
    Then IsCompatibleOldVersion() 返回 false
    And FireOnTerminatedCallback(0, nullptr)
    And onRelease 不触发

  Scenario: IsCompatibleOldVersion=false 时 OnDisconnect 异常走 onError 路径
    Given UIExtensionPattern.onTerminatedCallback_ 已注册（非 nullptr）
    When SessionWrapperImpl::OnDisconnect(isAbnormal=true)
    Then IsCompatibleOldVersion() 返回 false
    And FireOnErrorCallback(ERROR_CODE_UIEXTENSION_EXITED_ABNORMALLY, ...)
    And onRelease 不触发

  # ─── IsCompatibleOldVersion 判断 ─────────────

  Scenario: IsCompatibleOldVersion 返回 true
    Given sessionType_ = SessionType::UI_EXTENSION_ABILITY
    And onTerminatedCallback_ = nullptr
    When 调用 IsCompatibleOldVersion()
    Then 返回 true

  Scenario: IsCompatibleOldVersion 返回 false（注册了 onTerminated）
    Given sessionType_ = SessionType::UI_EXTENSION_ABILITY
    And onTerminatedCallback_ ≠ nullptr
    When 调用 IsCompatibleOldVersion()
    Then 返回 false

  Scenario: IsCompatibleOldVersion 返回 false（非 UI_EXTENSION_ABILITY SessionType）
    Given sessionType_ = SessionType::EMBEDDED_UI_EXTENSION
    And onTerminatedCallback_ = nullptr
    When 调用 IsCompatibleOldVersion()
    Then 返回 false（仅 UI_EXTENSION_ABILITY 考虑 compat）
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：onResult/onRelease 1.2 compat 废逝行为规格、IsCompatibleOldVersion 判断逻辑；不做什么：onReceive/onError/onTerminated/onDrawReady 触发条件（Feat-02）、Proxy send/sendSync（Feat-01）、Security/Embedded/Dynamic/Isolated 组件）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern IsCompatibleOldVersion 判断 onTerminatedCallback_ nullptr sessionType UI_EXTENSION_ABILITY"
  - repo: "openharmony/ace_engine"
    query: "SessionWrapperImpl InitTransferAbilityResultFunc IsCompatibleOldVersion onResult vs onTerminated 路径选择"
  - repo: "openharmony/ace_engine"
    query: "SessionWrapperImpl OnDisconnect IsCompatibleOldVersion onRelease vs onTerminated/onError 路径选择"
  - repo: "openharmony/ace_engine"
    query: "UIExtensionPattern FireOnResultCallback FireOnReleaseCallback onResultCallback_ onReleaseCallback_"
  - repo: "openharmony/ace_engine"
    query: "only for 1.2 begin end 注释标记范围 GetIsTransferringCaller SetIsTransferringCaller"
```

**关键文档：**
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.cpp:1644-1648`
- Pattern 层回调：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.cpp:1575-1648`
- SessionWrapper 路径选择：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/session_wrapper_impl.cpp:280-321, 1162-1175`
- Pattern 层声明：`frameworks/core/components_ng/pattern/ui_extension/ui_extension_component/ui_extension_pattern.h:164-167`
