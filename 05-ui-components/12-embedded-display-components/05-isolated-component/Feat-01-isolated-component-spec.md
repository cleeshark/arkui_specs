# 特性规格

> Func-05-12-05-Feat-01 IsolatedComponent完整规格：固化 IsolatedComponent 创建流程、Want → IsolatedInfo 解析机制、RestrictedWorker 线程内 DynamicComponentRenderer 渲染、onError 事件回调与错误码、Worker 约束和嵌套约束的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | IsolatedComponent完整规格 |
| 特性编号 | Func-05-12-05-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12+（@systemapi, @stagemodelonly, @dynamiconly, @noninterop） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | IsolatedComponent 创建与 Want 解析规格 | 补录 IsolatedComponent(options) 创建流程、IsolatedOptions { want, worker } 解析、Want → IsolatedInfo { abcPath, resourcePath, entryPoint, registerComponents } 提取规格 |
| ADDED | RestrictedWorker 线程渲染规格 | 补录 DynamicComponentRendererImpl 在 RestrictedWorker NativeEngine 中创建 UIContent、同进程隔离线程渲染规格 |
| ADDED | onError 事件回调与错误码规格 | 补录 onError(ErrorCallback) 回调触发条件与错误码 10001 (paramError)、10002 (restrictedWorkerError) 规格 |
| ADDED | Worker 约束规格 | 补录最大 1 Worker、每个 Worker 最多 4 组件约束规格 |
| ADDED | 嵌套约束规格 | 补录禁止在 IsolatedComponent 或 DynamicComponent 内嵌套的约束规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/12-embedded-display-components/05-isolated-component/design.md` | Baselined |

---

## 用户故事

### US-1: 创建 IsolatedComponent 与 Want/Worker

**作为** 系统应用开发者,
**我想要** 通过 IsolatedComponent(options) 创建组件并传入 want 和 worker,
**以便** 在宿主页面中通过 RestrictedWorker 线程加载外部 ABC 包的 UI 内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `IsolatedComponent({ want: wantObj, worker: restrictedWorker })` THEN 创建 IsolatedPattern → 注册 Worker 环境回调 → Worker 环境就绪后 InitializeIsolatedComponent → 解析 Want 为 IsolatedInfo → DynamicComponentRenderer::Create 在 RestrictedWorker NativeEngine 中创建 UIContent 加载 ABC 包内容 | 正常 |
| AC-1.2 | WHEN Want 中 abcPath 为空 THEN 不创建 DynamicComponentRenderer；FireOnErrorCallback(10001, "paramError", "The param is empty") | 异常 |
| AC-1.3 | WHEN Want 中 resourcePath 为空 THEN 不创建 DynamicComponentRenderer；FireOnErrorCallback(10001, "paramError", "The param is empty") | 异常 |
| AC-1.4 | WHEN Want 中 entryPoint 为空 THEN 不创建 DynamicComponentRenderer；FireOnErrorCallback(10001, "paramError", "The param is empty") | 异常 |
| AC-1.5 | WHEN runtime (Worker NativeEngine) 为空 THEN 不创建 DynamicComponentRenderer；FireOnErrorCallback(10001, "paramError", "The param is empty") | 异常 |

### US-2: onError 回调与错误码

**作为** 系统应用开发者,
**我想要** 通过 onError(ErrorCallback) 监听 IsolatedComponent 加载错误,
**以便** 在 IsolatedComponent 初始化失败时执行相应处理逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 注册 onError(callback) THEN UIExtensionModel::SetPlatformOnError 注册回调到 IsolatedPattern::onErrorCallback_ | 正常 |
| AC-2.2 | WHEN IsolatedInfo 参数为空（abcPath/resourcePath/entryPoint/runtime 任一空）THEN FireOnErrorCallback → PlatformPattern::FireOnErrorCallback → ArkTS onError 回调收到 { code: 10001, name: "paramError", message: "The param is empty" } | 异常 |
| AC-2.3 | WHEN DynamicComponentRenderer 运行环境不是 RestrictedWorker 线程 THEN FireOnErrorCallbackOnUI → 回调收到 { code: 10002, name: "restrictedWorkerError", message: "Run not in restricted worker thread" } | 异常 |

### US-3: RestrictedWorker 约束

**作为** 系统应用开发者,
**我想要** 了解 IsolatedComponent 的 Worker 使用约束和嵌套约束,
**以便** 正确使用 IsolatedComponent 避免违反约束导致组件创建失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 创建 IsolatedComponent 时 Worker 数量已达上限 (WORKER_MAX_NUM=1) THEN CheckWorkerMaxConstraint 返回 false，不创建 DynamicComponentRenderer | 异常 |
| AC-3.2 | WHEN 单 Worker 内组件数量已达上限 (DC_MAX_NUM_IN_WORKER=4) THEN CheckDCMaxConstraintInWorker 返回 false，不创建 DynamicComponentRenderer | 异常 |
| AC-3.3 | WHEN IsolatedComponent 尝试嵌套在 IsolatedComponent 内 THEN CheckConstraint 检测 UIContentType=ISOLATED_COMPONENT，返回 false，不创建 DynamicComponentRenderer | 异常 |
| AC-3.4 | WHEN IsolatedComponent 尝试嵌套在 DynamicComponent 内 THEN CheckConstraint 检测 UIContentType=DYNAMIC_COMPONENT，返回 false，不创建 DynamicComponentRenderer | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-2, R-3, R-4 | 已有实现 | 代码评审 | `isolated_pattern.cpp`, `js_isolated_component.cpp`, `dynamic_component_renderer_impl.cpp` |
| AC-1.2~1.5 | R-5 | 已有实现 | 代码评审 | `isolated_pattern.cpp` |
| AC-2.1~2.3 | R-6, R-7, R-8 | 已有实现 | 代码评审 | `js_isolated_component.cpp`, `isolated_pattern.cpp` |
| AC-3.1~3.2 | R-9, R-10 | 已有实现 | 代码评审 | `dynamic_component_renderer_impl.cpp` |
| AC-3.3~3.4 | R-11 | 已有实现 | 代码评审 | `isolated_pattern.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `IsolatedComponent(options)` 被调用 | JSIsolatedComponent::Create 解析 want/worker → UIExtensionModel::Create(sessionType=ISOLATED_COMPONENT) 创建 IsolatedPattern FrameNode → 注册 Worker 环境回调 | Worker 环境就绪后才执行初始化 | AC-1.1 |
| R-2 | 行为 | Worker 环境就绪回调触发 | PostTask 到 UI 线程 → UIExtensionModel::InitializeIsolatedComponent(frameNode, want, env) | 初始化必须在宿主 UI 线程执行 | AC-1.1 |
| R-3 | 行为 | IsolatedPattern::InitializeIsolatedComponent | 从 WantWrap 解析 IsolatedInfo（abcPath、resourcePath、entryPoint、registerComponents） → 若参数完整则调用 InitializeRender | — | AC-1.1 |
| R-4 | 行为 | IsolatedPattern::InitializeRender | CheckConstraint → 创建 DynamicComponentRenderer → IsRestrictedWorkerThread 检查 → SetUIContentType/SetAdaptiveSize/SetBackgroundTransparent → CreateContent → CreateIsolatedContent → InitUiContent | 同进程线程渲染 | AC-1.1 |
| R-5 | 异常 | abcPath/resourcePath/entryPoint/runtime 任一为空 | FireOnErrorCallback(10001, "paramError", "The param is empty") | 不创建 DynamicComponentRenderer | AC-1.2~1.5 |
| R-6 | 行为 | 注册 onError(callback) | JSIsolatedComponent::JsOnError → UIExtensionModel::SetPlatformOnError → PlatformPattern::SetOnErrorCallback | 回调参数为 { code, name, message } | AC-2.1 |
| R-7 | 异常 | IsolatedInfo 参数为空 | PlatformPattern::FireOnErrorCallback → ArkTS onError 回调收到 ErrorObject { code: 10001, name: "paramError", message: "The param is empty" } | 错误码固定 10001 | AC-2.2 |
| R-8 | 异常 | 运行环境不是 RestrictedWorker 线程 | DynamicComponentRendererImpl::IsRestrictedWorkerThread 返回 false → IsolatedPattern::FireOnErrorCallbackOnUI(10002) → 回调收到 { code: 10002, name: "restrictedWorkerError", message: "Run not in restricted worker thread" } | 错误码固定 10002 | AC-2.3 |
| R-9 | 边界 | Worker 数量约束 | WORKER_MAX_NUM=1：usingWorkers_.size() < 1 才允许新 Worker | 超限拒绝创建 | AC-3.1 |
| R-10 | 边界 | 单 Worker 组件数量约束 | DC_MAX_NUM_IN_WORKER=4：iter->second < 4 才允许新组件 | 超限拒绝创建 | AC-3.2 |
| R-11 | 边界 | 嵌套约束 | CheckConstraint 检测宿主 UIContentType ∈ { ISOLATED_COMPONENT, DYNAMIC_COMPONENT } 则返回 false | 禁止嵌套 | AC-3.3, AC-3.4 |
| R-12 | 行为 | DynamicComponentRendererImpl::CreateIsolatedContent | 通过 UVTaskWrapper 在 Worker 线程中执行 InitUiContent(nullptr) | IsolatedComponent 不传入 abilityContext | AC-1.1 |
| R-13 | 行为 | IsolatedPattern::OnDetachFromFrameNode | 调用 DynamicComponentRenderer::DestroyContent → dynamicComponentRenderer_ = nullptr | — | AC-1.1 |
| R-14 | 行为 | IsolatedPattern::OnDirtyLayoutWrapperSwap | 获取内容尺寸 → UpdateViewportConfig 更新隔离组件视口 | — | AC-1.1 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1, R-2, R-3, R-4, R-12, R-13, R-14 | 代码评审 | Isolated 创建流程完整性（JSIsolated→Model→Pattern→Renderer） |
| VM-2 | AC-1.2~1.5, R-5 | 代码评审 | 空 IsolatedInfo 参数的错误处理 |
| VM-3 | AC-2.1~2.3, R-6, R-7, R-8 | 代码评审 | onError 回调注册与错误码触发链完整性 |
| VM-4 | AC-3.1~3.2, R-9, R-10 | 代码评审 | Worker 约束和组件数量约束检查逻辑 |
| VM-5 | AC-3.3~3.4, R-11 | 代码评审 | 嵌套约束检查逻辑 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `IsolatedComponent(options: IsolatedOptions)` | System | 创建隔离组件 | `@internal/component/ets/isolated_component.d.ts` | 12 | @systemapi, @stagemodelonly, @dynamiconly, @noninterop |
| `IsolatedOptions { want: Want, worker: RestrictedWorker }` | System | 创建选项 | `@internal/component/ets/isolated_component.d.ts` | 12 | @systemapi, @stagemodelonly, @dynamiconly |
| `onError(callback: ErrorCallback)` | System | 错误回调 | `@internal/component/ets/isolated_component.d.ts` | 12 | @systemapi, @stagemodelonly, @dynamiconly, @noninterop |

**C-API (NDK) 接口：**

无。IsolatedComponent 为 @dynamiconly + @noninterop 组件，不提供 C-API modifier。

**Static ArkTS (Arkoala) 接口：**

无。IsolatedComponent 为 @dynamiconly 组件，不提供 Static ArkTS 桥接。

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `IsolatedOptions` | `{ want: Want; worker: RestrictedWorker }` | `isolated_component.d.ts` |
| `RestrictedWorker` | `import('../api/@ohos.worker').default.RestrictedWorker` | `isolated_component.d.ts` |
| `ErrorCallback` | `import('../api/@ohos.base').ErrorCallback` | `isolated_component.d.ts` |
| `Want` | `import('../api/@ohos.app.ability.Want').default` | `isolated_component.d.ts` |
| `IsolatedInfo` | C++ 内部结构：abcPath, resourcePath, entryPoint, registerComponents | `dynamic_component_renderer.h` |

### 变更/废弃 API

无变更/废弃 API。

---

## 接口规格

### 接口定义 — IsolatedComponent(options: IsolatedOptions)

| 属性 | 值 |
|------|-----|
| 函数签名 | `IsolatedComponentAttribute IsolatedComponent(IsolatedOptions options)` |
| 返回值 | `IsolatedComponentAttribute` — 组件属性对象 |
| 开放范围 | System (@systemapi, @stagemodelonly, @dynamiconly, @noninterop) |
| 错误码 | 10001 (paramError), 10002 (restrictedWorkerError) |
| 关联 AC | AC-1.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | IsolatedOptions | 是 | — | want 和 worker 必填；want 中 abcPath/resourcePath/entryPoint 非空 |
| options.want | Want | 是 | — | 必包含 abcPath、resourcePath、entryPoint 参数 |
| options.worker | RestrictedWorker | 是 | — | 必须为 RestrictedWorker 实例；最多 1 Worker、每 Worker 最多 4 组件 |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | want 中 abcPath/resourcePath/entryPoint 非空，worker 为 RestrictedWorker | 注册 Worker 环境回调 → Worker 就绪后解析 Want → IsolatedInfo → 创建 DynamicComponentRenderer → 在 RestrictedWorker NativeEngine 中加载 ABC 包 | AC-1.1 |
| 2 | want 中 abcPath 为空 | FireOnErrorCallback(10001, "paramError") | AC-1.2 |
| 3 | want 中 resourcePath 为空 | FireOnErrorCallback(10001, "paramError") | AC-1.3 |
| 4 | want 中 entryPoint 为空 | FireOnErrorCallback(10001, "paramError") | AC-1.4 |
| 5 | runtime (Worker NativeEngine) 为空 | FireOnErrorCallback(10001, "paramError") | AC-1.5 |
| 6 | Worker 数量已达上限 | CheckWorkerMaxConstraint 返回 false，不创建 | AC-3.1 |
| 7 | Worker 内组件数量已达上限 | CheckDCMaxConstraintInWorker 返回 false，不创建 | AC-3.2 |

### 接口定义 — onError(callback: ErrorCallback)

| 属性 | 值 |
|------|-----|
| 函数签名 | `IsolatedComponentAttribute onError(ErrorCallback callback)` |
| 返回值 | `IsolatedComponentAttribute` — 属性链对象 |
| 开放范围 | System (@systemapi, @stagemodelonly, @dynamiconly, @noninterop) |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束：**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | ErrorCallback (err: Error) => void | 是 | — | err.code 为 number；err.name 为 string；err.message 为 string |

**行为场景：**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | IsolatedInfo 参数为空 | callback 收到 { code: 10001, name: "paramError", message: "The param is empty" } | AC-2.2 |
| 2 | 运行环境非 RestrictedWorker 线程 | callback 收到 { code: 10002, name: "restrictedWorkerError", message: "Run not in restricted worker thread" } | AC-2.3 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** @since 12 为唯一版本号，全部标注 @stagemodelonly + @dynamiconly + @noninterop

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| 组件级 API 为 @systemapi + @stagemodelonly + @dynamiconly + @noninterop | 仅动态范式系统应用可使用；无 C-API 和 Static ArkTS 桥接 | AC-1.1 |
| DynamicComponentRenderer 使用 RestrictedWorker 线程渲染 | 同进程线程隔离，不跨进程 | AC-1.1 |
| Worker 最大数量 WORKER_MAX_NUM=1 | 全局最多 1 个 Worker | AC-3.1 |
| 单 Worker 组件最大数量 DC_MAX_NUM_IN_WORKER=4 | 每个 Worker 最多 4 组件 | AC-3.2 |
| 嵌套约束禁止 Isolated/Dynamic 内嵌套 | CheckConstraint 硬性拒绝 | AC-3.3, AC-3.4 |
| 无 Proxy 对象（无 send/sendSync） | 仅 onError 回调，无双向通信 | AC-2.1 |

---

## 非性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | RestrictedWorker 初始化和 ABC 加载延迟由包大小决定，不设量化指标 | 集成测试 | `isolated_pattern.cpp` |
| 安全 | @systemapi + @stagemodelonly + @dynamiconly 限制系统应用使用 | API 评审 | `isolated_component.d.ts` |
| 可测试性 | onError 可通过 Mock RestrictedWorker 验证 | 单测 | `isolated_pattern.cpp` |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | 集成测试 | — |
| 平板 | 无差异 | — | 集成测试 | — |
| 折叠屏 | DynamicComponentRenderer 需响应折叠状态变化更新视口尺寸 | 需监听 display 变化 | 集成测试 | `isolated_pattern.cpp` |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | IsolatedComponent 通过 AccessibilitySessionAdapterIsolatedComponent 接入宿主无障碍树 | AC-1.1 |
| 大字体 | 否 | IsolatedComponent 在隔离线程渲染，大字体设置通过 Worker 环境传递 | — |
| 深色模式 | 否 | 同上 | — |
| 多窗口/分屏 | 是 | DynamicComponentRenderer 需响应分屏视口尺寸变化 | AC-1.1 |
| 多用户 | 否 | 同进程线程隔离，不跨用户 | — |
| 版本升级 | 否 | API 12 起行为不变 | — |
| 生态兼容 | 否 | @noninterop 明确排除静态范式 | — |

---

## 行为场景

```gherkin
Feature: IsolatedComponent 创建与事件回调
  作为 系统应用开发者
  我想要 通过 IsolatedComponent 创建组件并监听加载错误
  以便 在宿主页面中通过 RestrictedWorker 线程加载外部 ABC 包 UI 内容

  # ─── 创建与 Want 解析 ─────────────────────

  Scenario: 正常创建 IsolatedComponent
    Given 一个宿主页面
    And 一个 RestrictedWorker 实例
    When 调用 IsolatedComponent({ want: { abcPath: '/data/abc/test.abc', resourcePath: '/data/res', entryPoint: 'Entry' }, worker: restrictedWorker })
    Then 创建 IsolatedPattern FrameNode
    And 注册 Worker 环境回调
    And Worker 环境就绪后解析 Want 为 IsolatedInfo
    And 创建 DynamicComponentRenderer 在 RestrictedWorker NativeEngine 中创建 UIContent
    And 加载 ABC 包内容渲染

  Scenario: Want 中 abcPath 为空
    Given 一个宿主页面
    When 调用 IsolatedComponent({ want: { abcPath: '', resourcePath: '/data/res', entryPoint: 'Entry' }, worker: restrictedWorker })
    Then 不创建 DynamicComponentRenderer
    And onError 回调被触发，ErrorObject { code: 10001, name: "paramError", message: "The param is empty" }

  Scenario: Want 中 resourcePath 为空
    Given 一个宿主页面
    When 调用 IsolatedComponent({ want: { abcPath: '/data/abc/test.abc', resourcePath: '', entryPoint: 'Entry' }, worker: restrictedWorker })
    Then 不创建 DynamicComponentRenderer
    And onError 回调被触发，ErrorObject { code: 10001, name: "paramError", message: "The param is empty" }

  Scenario: Want 中 entryPoint 为空
    Given 一个宿主页面
    When 调用 IsolatedComponent({ want: { abcPath: '/data/abc/test.abc', resourcePath: '/data/res', entryPoint: '' }, worker: restrictedWorker })
    Then 不创建 DynamicComponentRenderer
    And onError 回调被触发，ErrorObject { code: 10001, name: "paramError", message: "The param is empty" }

  # ─── 事件回调 ─────────────────────────────

  Scenario: 注册 onError 回调
    Given 一个宿主页面
    When 调用 IsolatedComponent(options).onError(callback)
    Then PlatformPattern::SetOnErrorCallback 注册回调

  Scenario: 运行环境非 RestrictedWorker 线程
    Given 一个 IsolatedComponent 已创建
    And DynamicComponentRenderer 检测运行环境不是 RestrictedWorker 线程
    Then FireOnErrorCallbackOnUI 被触发
    And ArkTS onError 回调收到 { code: 10002, name: "restrictedWorkerError", message: "Run not in restricted worker thread" }

  # ─── Worker 约束 ──────────────────────────

  Scenario: Worker 数量已达上限
    Given 已有 1 个 Worker 正在使用
    When 尝试创建新的 IsolatedComponent 使用不同 Worker
    Then CheckWorkerMaxConstraint 返回 false
    And 不创建 DynamicComponentRenderer

  Scenario: 单 Worker 内组件数量已达上限
    Given 一个 Worker 已承载 4 个组件
    When 尝试在该 Worker 上创建第 5 个组件
    Then CheckDCMaxConstraintInWorker 返回 false
    And 不创建 DynamicComponentRenderer

  # ─── 嵌套约束 ─────────────────────────────

  Scenario: 在 IsolatedComponent 内嵌套 IsolatedComponent
    Given 一个 IsolatedComponent 容器
    When 尝试在其内部创建 IsolatedComponent
    Then CheckConstraint 检测 UIContentType=ISOLATED_COMPONENT
    And 返回 false，不创建 DynamicComponentRenderer

  Scenario: 在 DynamicComponent 内嵌套 IsolatedComponent
    Given 一个 DynamicComponent 容器
    When 尝试在其内部创建 IsolatedComponent
    Then CheckConstraint 检测 UIContentType=DYNAMIC_COMPONENT
    And 返回 false，不创建 DynamicComponentRenderer
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么：创建/Want解析/Worker线程渲染/onError回调/错误码/Worker约束/嵌套约束；不做什么：C-API modifier、Static ArkTS桥接、send/sendSync通信、onComplete回调）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "IsolatedPattern 如何解析 Want 为 IsolatedInfo 并处理空参数错误"
  - repo: "openharmony/ace_engine"
    query: "DynamicComponentRendererImpl 在 RestrictedWorker NativeEngine 中创建 UIContent 的完整流程"
  - repo: "openharmony/ace_engine"
    query: "CheckWorkerMaxConstraint 和 CheckDCMaxConstraintInWorker 的 Worker 约束检查逻辑"
  - repo: "openharmony/ace_engine"
    query: "IsolatedPattern CheckConstraint 嵌套约束检测 UIContentType ISOLATED_COMPONENT DYNAMIC_COMPONENT"
```

**关键文档：**
- SDK API：`interface/sdk-js/api/@internal/component/ets/isolated_component.d.ts`
- Pattern 层：`frameworks/core/components_ng/pattern/ui_extension/isolated_component/isolated_pattern.h`
- Renderer 抽象层：`frameworks/core/common/dynamic_component_renderer.h`
- Renderer 实现层：`adapter/ohos/entrance/dynamic_component/dynamic_component_renderer_impl.h`
- JS Bridge 层：`frameworks/bridge/declarative_frontend/jsview/js_isolated_component.h`
- Platform Pattern：`frameworks/core/components_ng/pattern/ui_extension/platform_pattern.h`
