# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIContext实例解析与作用域调度 |
| 特性编号 | Func-04-12-01-Feat-02 |
| 优先级 | P1 |
| 目标版本 | API 10+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

UIContext 是 ArkUI 框架中 UI 实例的上下文入口对象。本特性规格定义 UIContext 实例解析、身份查询、无窗容器管理及作用域调度能力。在多窗口/多实例环境下，ContainerScope 维护全局实例注册表与调用域栈，InstanceIdGenReason 提供解析原因追踪；Window-Free Container 为原子化服务场景提供全局单例无窗实例；runScopedTask/getHostContext/getSharedLocalStorage 在调用域内执行回调与获取宿主上下文资源。

底层由 Container（AceContainer）作为实例载体，ContainerScope 维护全局实例注册表与调用域栈。Window-Free Container（原子化服务场景）使用全局单例 + PseudoEventCallback 模式，不参与前台/焦点追踪。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIContext.getId(): number | 实例身份-ID，@since 10 |
| ADDED | UIContext.getWindowName(): string \| undefined | 实例身份-窗口名，@since 12 |
| ADDED | UIContext.getWindowId(): number \| undefined | 实例身份-窗口ID，@since 12 |
| ADDED | UIContext.isAvailable(): boolean | 实例可用性，@since 12 |
| ADDED | new UIContext() | 构造器，@since 22 |
| ADDED | UIContext.resolveUIContext(): ResolvedUIContext | 静态解析，@since 22 |
| ADDED | UIContext.getCallingScopeUIContext(): UIContext \| undefined | 静态-调用域，@since 22 |
| ADDED | UIContext.getLastFocusedUIContext(): UIContext \| undefined | 静态-焦点，@since 22 |
| ADDED | UIContext.getLastForegroundUIContext(): UIContext \| undefined | 静态-前台，@since 22 |
| ADDED | UIContext.getAllUIContexts(): Array\<UIContext\> | 静态-枚举，@since 22 |
| ADDED | ResolveStrategy 枚举 | CALLING_SCOPE=0, LAST_FOCUS=1, MAX_INSTANCE_ID=2, UNIQUE=3, LAST_FOREGROUND=4, UNDEFINED=5，@since 22 |
| ADDED | ResolvedUIContext extends UIContext + strategy | 解析结果类，@since 22 |
| ADDED | UIContext.createUIContextWithoutWindow(context) | 无窗创建，@since 17，atomicservice only |
| ADDED | UIContext.destroyUIContextWithoutWindow(): void | 无窗销毁，@since 17，atomicservice only |
| ADDED | UIContext.runScopedTask(callback): void | 作用域回调，@since 12 |
| ADDED | UIContext.getHostContext(): Context \| undefined | 宿主上下文，@since 12 |
| ADDED | UIContext.getSharedLocalStorage(): LocalStorage \| undefined | 共享LocalStorage，@since 12 |
| ADDED | InstanceIdGenReason 枚举 (C++) | SCOPE=0, ACTIVE=1, DEFAULT=2, SINGLETON=3, FOREGROUND=4, UNDEFINED=5 |
| ADDED | ContainerScope::CurrentIdWithReason | C++，返回 pair\<int32_t, InstanceIdGenReason\> |
| ADDED | ContainerScope::RemoveAndCheck | C++，Remove + 清除 recentActive/foreground |
| ADDED | destroyedUIContextCache_ | AceEngine 内，上限 10 条 |
| ADDED | UIContextCacheInfo | instanceId, createTime, destroyTime, windowId, windowName |
| ADDED | AceEngine::GetEnhancedContextBNotFoundMessage | C++，增强错误信息 |

## 输入文档

| 文档 | 位置 |
|------|------|
| UIContext JS 定义 | frameworks/bridge/declarative_frontend/engine/jsUIContext.js |
| UIContext ArkTS 定义 | frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts |
| ContainerScope 头文件 | frameworks/core/common/container_scope.h |
| ContainerScope 实现 | frameworks/core/common/container_scope.cpp:403-425 |
| InstanceIdGenReason 枚举 | frameworks/core/common/container_scope.h:29-36 |
| JSScopeUtil 实现 | frameworks/bridge/declarative_frontend/jsview/js_scope_util.cpp:126-134 |
| AceEngine 头文件 | frameworks/core/common/ace_engine.h:40-47 |
| UIContextCacheInfo | frameworks/core/common/ace_engine.h:40-47 |
| destroyedUIContextCache_ | frameworks/core/common/ace_engine.h:84-85 |
| Container 常量 | frameworks/core/common/container_consts.h:22-41 |
| NAPI container_utils | interfaces/napi/kits/container_utils/js_container_utils.cpp |

## 用户故事

| US-ID | 用户故事 | 关联 AC |
|--------|----------|---------|
| US-2.1 | 开发者在多窗口应用中使用 resolveUIContext() 获取当前有效 UIContext 及其解析策略，无需手动判断调用域 | AC-2.1~AC-2.6 |
| US-2.2 | 开发者在异步回调中使用 getCallingScopeUIContext() 获取发起回调的原始实例 UIContext，并通过 isAvailable() 确认其有效性 | AC-2.7, AC-2.10 |
| US-2.3 | 原子化服务开发者使用 createUIContextWithoutWindow 创建无窗 UI 实例进行离屏渲染或后台逻辑处理 | AC-2.11, AC-2.12 |
| US-2.4 | 开发者使用 getId() 在多实例场景中区分不同 UI 实例对象 | AC-2.8 |
| US-2.5 | 开发者使用 getAllUIContexts() 遍历当前所有存活实例 | AC-2.9 |
| US-2.6 | 开发者在异步回调中使用 runScopedTask() 在特定 UIContext 实例的作用域内执行操作，确保 API 调用绑定正确实例 | AC-2.13 |
| US-2.7 | 开发者使用 getHostContext() 获取 UIContext 所属的 Ability/Extension 上下文，以访问系统资源 | AC-2.14 |
| US-2.8 | 开发者使用 getSharedLocalStorage() 获取跨页面共享的 LocalStorage 实例 | AC-2.15 |

## 验收追溯

| AC-ID | WHEN | THEN |
|--------|------|------|
| AC-2.1 | 调用 resolveUIContext() 时存在调用域（ContainerScope::CurrentId() ≥ 0） | 返回 ResolvedUIContext，strategy = CALLING_SCOPE，UIContext 对应调用域实例 |
| AC-2.2 | 调用 resolveUIContext() 时无调用域且全局仅有 1 个实例 | 返回 ResolvedUIContext，strategy = UNIQUE |
| AC-2.3 | 调用 resolveUIContext() 时无调用域、多实例且存在最近焦点实例 | 返回 ResolvedUIContext，strategy = LAST_FOCUS |
| AC-2.4 | 调用 resolveUIContext() 时无调用域、多实例且无焦点但存在最近前台实例 | 返回 ResolvedUIContext，strategy = LAST_FOREGROUND |
| AC-2.5 | 调用 resolveUIContext() 时无调用域、多实例、无焦点/前台 | 返回 ResolvedUIContext，strategy = MAX_INSTANCE_ID，取最大 instanceId |
| AC-2.6 | 调用 resolveUIContext() 时全局无任何存活实例 | 返回 ResolvedUIContext，strategy = UNDEFINED，getId() = -1 |
| AC-2.7 | 调用 getCallingScopeUIContext() 时存在调用域 | 返回该域 UIContext；无调用域时返回 undefined |
| AC-2.8 | 调用 getId() | 返回 number ∈ [-1, +∞)；构造器创建的 UIContext 返回 -1；有效实例返回 ≥ 0 的 instanceId |
| AC-2.9 | 调用 getAllUIContexts() | 返回 UIContext[] 包含所有 ContainerScope::containerSet_ 中存活实例；无实例时返回空数组 |
| AC-2.10 | 调用 isAvailable() | 对应后端 Container 存活时返回 true；构造器创建（instanceId=-1）或 Container 已销毁时返回 false |
| AC-2.11 | 调用 createUIContextWithoutWindow(context) 且 g_WindowFreeContainer 为 null | 创建 AceContainer（instanceId ∈ [900000, 999999]），使用 PseudoEventCallback，width=0, height=0，返回 UIContext |
| AC-2.12 | 调用 destroyUIContextWithoutWindow() | 销毁 g_WindowFreeContainer，调用 DestroyContainer + RemoveAndCheck，g_WindowFreeContainer 重置为 null |
| AC-2.13 | 调用 runScopedTask(callback) | 在该 UIContext 的 instanceId 作用域内（ContainerScope RAII）执行 callback，完成后恢复原作用域 |
| AC-2.14 | 调用 getHostContext() | 在该 UIContext 作用域内返回 getContext() 对应的 Ability/Extension Context；实例不可用时返回 undefined |
| AC-2.15 | 调用 getSharedLocalStorage() | 在该 UIContext 作用域内返回 NativeLocalStorage.GetShared()；实例不可用时返回 undefined |
| AC-2.16 | 调用 getLastFocusedUIContext() | 返回 ContainerScope::RecentActiveId() 对应 UIContext 或 undefined |
| AC-2.17 | 调用 getLastForegroundUIContext() | 返回 ContainerScope::RecentForegroundId() 对应 UIContext 或 undefined |
| AC-2.18 | 调用 getWindowName() | 返回窗口名称字符串或 undefined（无窗场景返回 undefined） |
| AC-2.19 | 调用 getWindowId() | 返回窗口 ID number 或 undefined |

## 规则定义

### R-1: ContainerScope::CurrentIdWithReason 解析链优先级 [行为]

| 属性 | 值 |
|------|-----|
| 规则ID | R-1 |
| 类型 | 行为 |
| 触发条件 | 调用 resolveUIContext()、getCallingScopeUIContext() 等静态工厂方法时触发 CurrentIdWithReason |
| 预期行为 | 严格按序执行：SCOPE → UNDEFINED(0容器) → SINGLETON(1容器) → ACTIVE → FOREGROUND → DEFAULT，任何条件满足即返回，后续步骤不再执行 |
| 边界/约束 | containerCount==0 时返回 {INSTANCE_ID_UNDEFINED, UNDEFINED}；所有分支互斥不可跳步 |
| 关联AC | AC-2.1~AC-2.6 |

源码验证: container_scope.cpp:403-425

### R-2: InstanceIdGenReason 与 ResolveStrategy 映射 [行为]

| 属性 | 值 |
|------|-----|
| 规则ID | R-2 |
| 类型 | 行为 |
| 触发条件 | resolveUIContext() 返回 ResolvedUIContext 时，strategy 值由 C++ InstanceIdGenReason 映射 |
| 预期行为 | SCOPE=CALLING_SCOPE(0), ACTIVE=LAST_FOCUS(1), DEFAULT=MAX_INSTANCE_ID(2), SINGLETON=UNIQUE(3), FOREGROUND=LAST_FOREGROUND(4), UNDEFINED=UNDEFINED(5) |
| 边界/约束 | 数值对齐但语义偏移：LAST_FOCUS 对应 ACTIVE（最近获焦），MAX_INSTANCE_ID 对应 DEFAULT（最大 ID） |
| 关联AC | AC-2.1~AC-2.6 |

源码验证: container_scope.h:29-36, js_scope_util.cpp:126-134

### R-3: UIContent Foreground/Focus 触发 ContainerScope 更新 [行为]

| 属性 | 值 |
|------|-----|
| 规则ID | R-3 |
| 类型 | 行为 |
| 触发条件 | 窗口 Foreground/Focus 事件发生 |
| 预期行为 | Foreground → UpdateRecentForeground(instanceId)；Focus → UpdateRecentActive(instanceId) |
| 边界/约束 | Background 不清除 recentForegroundId_；Destroy 通过 RemoveAndCheck 清除匹配缓存 |
| 关联AC | AC-2.3, AC-2.4, AC-2.16, AC-2.17 |

### R-4: Window-Free Container 全局单例与零窗模型 [行为]

| 属性 | 值 |
|------|-----|
| 规则ID | R-4 |
| 类型 | 行为 |
| 触发条件 | 调用 createUIContextWithoutWindow(context) |
| 预期行为 | g_WindowFreeContainer 为进程级单例，若已存在直接返回；instanceId 由 GenerateId\<WINDOW_FREE_CONTAINER\>() 生成（基数 900000）；使用 PseudoEventCallback，width=0, height=0，单线程模型 |
| 边界/约束 | instanceId ∈ [900000, 999999]；isDynamicRender_=true 不参与前台/焦点追踪；多次调用幂等 |
| 关联AC | AC-2.11 |

源码验证: window_free_container.cpp:176-227

### R-5: new UIContext() 创建未绑定实例 [边界]

| 属性 | 值 |
|------|-----|
| 规则ID | R-5 |
| 类型 | 边界 |
| 触发条件 | 调用 new UIContext() |
| 预期行为 | instanceId = -1，isAvailable() = false，不绑定任何后端 Container |
| 边界/约束 | getId() 返回 -1（jsUIContext.js:596）；所有需要后端 Container 的方法均不可用 |
| 关联AC | AC-2.8, AC-2.10 |

源码验证: jsUIContext.js:595-596

### R-6: 静态工厂方法返回的 UIContext 可能指向已销毁实例 [异常]

| 属性 | 值 |
|------|-----|
| 规则ID | R-6 |
| 类型 | 异常 |
| 触发条件 | 在异步回调中调用 getCallingScopeUIContext/getLastFocusedUIContext/getLastForegroundUIContext，目标实例可能在回调执行前已被销毁 |
| 预期行为 | 返回的 UIContext 对象 instanceId 有效但后端 Container 已销毁；调用者必须用 isAvailable() 验证 |
| 边界/约束 | isAvailable() 基于 __availableInstanceIds__.has(instanceId_) 检查（jsUIContext.js:1062） |
| 关联AC | AC-2.10 |

### R-7: DestroyContainer 与 RemoveAndCheck 清理流程 [行为]

| 属性 | 值 |
|------|-----|
| 规则ID | R-7 |
| 类型 | 行为 |
| 触发条件 | 容器销毁（包括 destroyUIContextWithoutWindow） |
| 预期行为 | SubwindowManager::CloseDialog → container->Destroy → UnRegisterWatchDog → DestroyView → RemoveContainer；RemoveAndCheck 在 Remove 后检查 recentActiveId_/recentForegroundId_，若匹配则清为 -1 |
| 边界/约束 | RemoveAndCheck(container_scope.cpp:662-671)：先 Remove(id)，再条件清除缓存 |
| 关联AC | AC-2.12 |

### R-8: ContainerScope RAII 线程局部机制 [行为]

| 属性 | 值 |
|------|-----|
| 规则ID | R-8 |
| 类型 | 行为 |
| 触发条件 | ContainerScope 构造器入栈 |
| 预期行为 | CurrentId 使用线程局部 currentId_，RAII 构造器设置、析构恢复；不可跨线程传递 |
| 边界/约束 | runScopedTask 使用 withInstanceId(instanceId, callback) 实现同步/恢复（jsUIContext.js:2036-2043） |
| 关联AC | AC-2.13 |

源码验证: jsUIContext.js:721-726, jsUIContext.js:2036-2043

### R-9: isDynamicRender 容器排除前台/焦点追踪 [边界]

| 属性 | 值 |
|------|-----|
| 规则ID | R-9 |
| 类型 | 边界 |
| 触发条件 | Window-Free / DynamicComponent 容器（isDynamicRender_=true） |
| 预期行为 | 不参与 UpdateRecentActive/UpdateRecentForeground，getLastFocusedUIContext/getLastForegroundUIContext 不会返回这些实例 |
| 边界/约束 | Window-Free 容器无窗口生命周期事件（Foreground/Background/Focus/Destroy 事件不触发） |
| 关联AC | AC-2.16, AC-2.17 |

### R-10: API 平台可见性限定 [边界]

| 属性 | 值 |
|------|-----|
| 规则ID | R-10 |
| 类型 | 边界 |
| 触发条件 | 跨不同 @since 版本和平台限定调用 API |
| 预期行为 | createUIContextWithoutWindow/destroyUIContextWithoutWindow @since 17 仅 atomicservice；resolveUIContext 系列 @since 22 crossplatform；runScopedTask/getHostContext/getSharedLocalStorage @since 12 crossplatform |
| 边界/约束 | 版本差 5+，不可混用平台限定 |
| 关联AC | AC-2.11, AC-2.12 |

### R-11: destroyedUIContextCache_ 缓存策略 [恢复]

| 属性 | 值 |
|------|-----|
| 规则ID | R-11 |
| 类型 | 恢复 |
| 触发条件 | 容器销毁后 AddContainer 时 instanceId 重用 |
| 预期行为 | destroyedUIContextCache_ 上限 10 条，溢出时淘汰 destroyTime_ 最小条目；AddContainer 时若 instanceId 在缓存中存在，先删除旧条目再插入 |
| 边界/约束 | MAX_DESTROYED_CACHE_SIZE=10（ace_engine.cpp:83） |
| 关联AC | AC-2.6 |

源码验证: ace_engine.h:84-85, ace_engine.cpp:150-158

### R-12: getHostContext 与 getSharedLocalStorage 作用域绑定 [行为]

| 属性 | 值 |
|------|-----|
| 规则ID | R-12 |
| 类型 | 行为 |
| 触发条件 | 调用 getHostContext() 或 getSharedLocalStorage() |
| 预期行为 | 在该 UIContext 的 instanceId 作用域内（withInstanceId RAII）执行 getContext()/NativeLocalStorage.GetShared() |
| 边界/约束 | getContext() 返回宿主 Ability/Extension Context；getSharedLocalStorage() 返回进程级共享 LocalStorage |
| 关联AC | AC-2.14, AC-2.15 |

源码验证: jsUIContext.js:808-818

### R-13: resolveUIContext 子容器 ID 映射 [边界]

| 属性 | 值 |
|------|-----|
| 规则ID | R-13 |
| 类型 | 边界 |
| 触发条件 | resolveUIContext() 解析结果中的 instanceId 为子容器 ID |
| 预期行为 | 对子容器 ID（≥MIN_SUBCONTAINER_ID 且 \< MIN_PLUGIN_SUBCONTAINER_ID）通过 SubwindowManager::GetParentContainerId 映射到主容器 ID |
| 边界/约束 | GetMainInstanceId(pair.first) 在 JS 层执行映射（js_scope_util.cpp:130） |
| 关联AC | AC-2.1 |

### R-14: runScopedTask callback undefined 处理 [异常]

| 属性 | 值 |
|------|-----|
| 规则ID | R-14 |
| 类型 | 异常 |
| 触发条件 | 调用 runScopedTask(undefined) 或 runScopedTask(null) |
| 预期行为 | withInstanceId 设置作用域后检查 callback !== undefined，若为 undefined 则不执行回调，但仍完成作用域恢复 |
| 边界/约束 | 作用域设置和恢复始终执行，无论 callback 是否有效 |
| 关联AC | AC-2.13 |

源码验证: jsUIContext.js:721-726

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-2.1, R-1 | 单元测试 | ContainerScope(instanceId)，resolveUIContext strategy=CALLING_SCOPE；container_scope.cpp:403-407 |
| VM-2 | AC-2.2, R-1 | 单元测试 | 仅注册 1 个 Container，不设 ContainerScope，strategy=UNIQUE；container_scope.cpp:413-414 |
| VM-3 | AC-2.3, R-1 | 单元测试 | 多 Container + UpdateRecentActive，strategy=LAST_FOCUS；container_scope.cpp:416-418 |
| VM-4 | AC-2.4, R-1 | 单元测试 | 多 Container + UpdateRecentForeground，strategy=LAST_FOREGROUND；container_scope.cpp:420-422 |
| VM-5 | AC-2.5, R-1 | 单元测试 | 多 Container 无 Active/Foreground，strategy=MAX_INSTANCE_ID；container_scope.cpp:424 |
| VM-6 | AC-2.6, R-1 | 单元测试 | containerSet_ 空，strategy=UNDEFINED；container_scope.cpp:409-411 |
| VM-7 | AC-2.7, R-1 | NAPI 测试 | getCallingScopeUIContext 存在调用域返回 UIContext；jsUIContext.js:429-435 |
| VM-8 | AC-2.8, R-5 | NAPI 测试 | new UIContext() → getId()=-1；window.getUIContext().getId()≥0；jsUIContext.js:595-596 |
| VM-9 | AC-2.9, R-1 | 单元测试 | ContainerScope::GetAllUIContexts() 返回 containerSet_；container_scope.h:86 |
| VM-10 | AC-2.10, R-5, R-6 | NAPI 测试 | isAvailable() 对销毁实例返回 false；jsUIContext.js:1061-1062 |
| VM-11 | AC-2.11, R-4 | NAPI 测试 | createUIContextWithoutWindow instanceId ∈ [900000,999999]；window_free_container.cpp:176-227 |
| VM-12 | AC-2.12, R-4, R-7 | NAPI 测试 | destroyUIContextWithoutWindow 销毁后 g_WindowFreeContainer=null；window_free_container.cpp:229-238 |
| VM-13 | AC-2.13, R-8, R-14 | NAPI 测试 | runScopedTask 在 withInstanceId 作用域内执行 callback；jsUIContext.js:721-726 |
| VM-14 | AC-2.14, R-12 | NAPI 测试 | getHostContext 返回 getContext()；jsUIContext.js:808-812 |
| VM-15 | AC-2.15, R-12 | NAPI 测试 | getSharedLocalStorage 返回 NativeLocalStorage.GetShared()；jsUIContext.js:814-818 |
| VM-16 | AC-2.16, R-3 | NAPI 测试 | getLastFocusedUIContext 返回 RecentActiveId 对应 UIContext 或 undefined |
| VM-17 | AC-2.17, R-3 | NAPI 测试 | getLastForegroundUIContext 返回 RecentForegroundId 对应 UIContext 或 undefined |
| VM-18 | AC-2.18 | NAPI 测试 | getWindowName 返回窗口名称字符串或 undefined |
| VM-19 | AC-2.19 | NAPI 测试 | getWindowId 返回窗口 ID number 或 undefined |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| UIContext.getId() | Public | 无 | number | N/A | 获取实例唯一 ID | AC-2.8 |
| UIContext.getWindowName() | Public | 无 | string \| undefined | N/A | 获取窗口名称 | AC-2.18 |
| UIContext.getWindowId() | Public | 无 | number \| undefined | N/A | 获取窗口 ID | AC-2.19 |
| UIContext.isAvailable() | Public | 无 | boolean | N/A | 验证实例可用性 | AC-2.10 |
| new UIContext() | Public | 无 | UIContext | N/A | 创建未绑定实例的 UIContext | AC-2.8 |
| UIContext.resolveUIContext() | Public | 无 | ResolvedUIContext | N/A | 静态方法，按决策链解析 UIContext | AC-2.1~AC-2.6 |
| UIContext.getCallingScopeUIContext() | Public | 无 | UIContext \| undefined | N/A | 静态方法，获取调用域 UIContext | AC-2.7 |
| UIContext.getLastFocusedUIContext() | Public | 无 | UIContext \| undefined | N/A | 静态方法，获取最近焦点 UIContext | AC-2.16 |
| UIContext.getLastForegroundUIContext() | Public | 无 | UIContext \| undefined | N/A | 静态方法，获取最近前台 UIContext | AC-2.17 |
| UIContext.getAllUIContexts() | Public | 无 | Array\<UIContext\> | N/A | 静态方法，获取全部 UIContext 数组 | AC-2.9 |
| ResolveStrategy 枚举 | Public | 无 | const enum | N/A | 解析策略枚举 | AC-2.1~AC-2.6 |
| ResolvedUIContext 类 | Public | instanceId: number, strategy: ResolveStrategy | UIContext 子类 | N/A | 解析结果类 | AC-2.1~AC-2.6 |
| UIContext.createUIContextWithoutWindow(context) | Public (atomicservice) | UIAbilityContext \| ExtensionContext | UIContext \| undefined | N/A | 创建无窗 UI 实例 | AC-2.11 |
| UIContext.destroyUIContextWithoutWindow() | Public (atomicservice) | 无 | void | N/A | 销毁无窗 UI 实例 | AC-2.12 |
| UIContext.runScopedTask(callback) | Public | () => void | void | N/A | 作用域内执行回调 | AC-2.13 |
| UIContext.getHostContext() | Public | 无 | Context \| undefined | N/A | 获取宿主上下文 | AC-2.14 |
| UIContext.getSharedLocalStorage() | Public | 无 | LocalStorage \| undefined | N/A | 获取共享 LocalStorage | AC-2.15 |

### 变更/废弃 API

无变更/废弃 API。本特性为纯新增，不修改已有 UIContext 接口签名。

## 接口规格

### 接口定义

**UIContext.getId()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getId(): number` |
| 返回值 | `number` — 实例唯一 ID，有效实例 ≥ 0，构造器创建返回 -1 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.8 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 通过 window.getUIContext() 获取的 UIContext | 返回 ≥ 0 的 instanceId | AC-2.8 |
| 2 | 通过 new UIContext() 创建的实例 | 返回 -1 | AC-2.8 |

源码验证: jsUIContext.js:595-596

---

**UIContext.getWindowName()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getWindowName(): string \| undefined` |
| 返回值 | `string \| undefined` — 口名称字符串或 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.18 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 UIContext 且存在关联窗口 | 返回窗口名称字符串 | AC-2.18 |
| 2 | Window-Free 容器（无窗场景） | 返回 undefined | AC-2.18 |

源码验证: jsUIContext.js:938-941

---

**UIContext.getWindowId()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getWindowId(): number \| undefined` |
| 返回值 | `number \| undefined` — 窗口 ID 或 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.19 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 UIContext 且存在关联窗口 | 返回窗口 ID number | AC-2.19 |
| 2 | Window-Free 容器（无窗场景） | 返回 undefined | AC-2.19 |

源码验证: jsUIContext.js:944-947, @ohos.arkui.UIContext.ts:1205-1211

---

**UIContext.isAvailable()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `isAvailable(): boolean` |
| 返回值 | `boolean` — true 表示后端 Container 存活 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.10 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 对应后端 Container 存活 | 返回 true | AC-2.10 |
| 2 | 构造器创建（instanceId=-1） | 返回 false | AC-2.10 |
| 3 | Container 已销毁 | 返回 false | AC-2.10 |

源码验证: jsUIContext.js:1061-1062

---

**new UIContext()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor()` |
| 返回值 | `UIContext` — instanceId=-1 的未绑定实例 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.8 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 new UIContext() | 创建 instanceId=-1 的 UIContext，isAvailable()=false | AC-2.8 |

---

**UIContext.resolveUIContext()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static resolveUIContext(): ResolvedUIContext` |
| 返回值 | `ResolvedUIContext` — 包含 strategy 属性的 UIContext 子类 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.6 |

**参数约束**

无参数。策略由 C++ CurrentIdWithReason 决策链内部确定。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 存在调用域（CurrentId()≥0） | strategy=CALLING_SCOPE，instanceId=调用域 ID | AC-2.1 |
| 2 | 无调用域，0 容器 | strategy=UNDEFINED，instanceId=-1 | AC-2.6 |
| 3 | 无调用域，1 容器 | strategy=UNIQUE | AC-2.2 |
| 4 | 无调用域，多容器，RecentActiveId()≥0 | strategy=LAST_FOCUS | AC-2.3 |
| 5 | 无调用域，多容器，RecentForegroundId()≥0 | strategy=LAST_FOREGROUND | AC-2.4 |
| 6 | 无调用域，多容器，无焦点/前台 | strategy=MAX_INSTANCE_ID | AC-2.5 |

源码验证: js_scope_util.cpp:126-134, container_scope.cpp:403-425

---

**UIContext.getCallingScopeUIContext()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static getCallingScopeUIContext(): UIContext \| undefined` |
| 返回值 | `UIContext \| undefined` — 调用域 UIContext 或 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.7 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 存在调用域（CurrentId()≥0） | 返回对应 UIContext | AC-2.7 |
| 2 | 无调用域（CurrentId()\<0） | 返回 undefined | AC-2.7 |

源码验证: jsUIContext.js:429-435

---

**UIContext.getLastFocusedUIContext()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static getLastFocusedUIContext(): UIContext \| undefined` |
| 返回值 | `UIContext \| undefined` — 最近焦点 UIContext 或 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.16 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | RecentActiveId()≥0 且对应 Container 存活 | 返回对应 UIContext | AC-2.16 |
| 2 | RecentActiveId()\<0 或对应 Container 已销毁 | 返回 undefined | AC-2.16 |

源码验证: jsUIContext.js:437-443

---

**UIContext.getLastForegroundUIContext()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static getLastForegroundUIContext(): UIContext \| undefined` |
| 返回值 | `UIContext \| undefined` — 最近前台 UIContext 或 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.17 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | RecentForegroundId()≥0 且对应 Container 存活 | 返回对应 UIContext | AC-2.17 |
| 2 | RecentForegroundId()\<0 或对应 Container 已销毁 | 返回 undefined | AC-2.17 |

源码验证: jsUIContext.js:445-451

---

**UIContext.getAllUIContexts()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static getAllUIContexts(): Array\<UIContext\>` |
| 返回值 | `Array\<UIContext\>` — 所有存活实例对应 UIContext 数组 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.9 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | containerSet_ 有存活实例 | 返回包含所有存活实例 UIContext 的数组 | AC-2.9 |
| 2 | 无存活实例 | 返回空数组 | AC-2.9 |

源码验证: jsUIContext.js:453-462

---

**ResolveStrategy 枚举**

| 属性 | 值 |
|------|-----|
| 函数签名 | `const enum ResolveStrategy` |
| 返回值 | N/A |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.6 |

**参数约束**

枚举成员：CALLING_SCOPE=0, LAST_FOCUS=1, MAX_INSTANCE_ID=2, UNIQUE=3, LAST_FOREGROUND=4, UNDEFINED=5

源码验证: @ohos.arkui.UIContext.ts:726-733

---

**ResolvedUIContext 类**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class ResolvedUIContext extends UIContext` |
| 返回值 | N/A |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instanceId | number | 是 | 无 | 由 CurrentIdWithReason 决策链确定 |
| strategy | ResolveStrategy | 是 | UNDEFINED | 枚举值 0-5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | resolveUIContext() 返回结果 | strategy 字段记录解析策略，继承 UIContext 全部方法 | AC-2.1~AC-2.6 |

源码验证: jsUIContext.js:1133-1138, @ohos.arkui.UIContext.ts:718-724

---

**UIContext.createUIContextWithoutWindow(context)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static createUIContextWithoutWindow(context: UIAbilityContext \| ExtensionContext): UIContext \| undefined` |
| 返回值 | `UIContext \| undefined` — 无窗 UIContext 或 undefined |
| 开放范围 | Public (atomicservice only) |
| 错误码 | N/A |
| 关联 AC | AC-2.11 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| context | UIAbilityContext \| ExtensionContext | 是 | 无 | 若 runtime 或 ctx 为 nullptr 返回 undefined |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | g_WindowFreeContainer 为 null | 创建 AceContainer，instanceId∈[900000,999999]，PseudoEventCallback，0×0 | AC-2.11 |
| 2 | g_WindowFreeContainer 已存在 | 返回同一实例（幂等） | AC-2.11 |
| 3 | runtime/ctx 为 nullptr | 返回 undefined | AC-2.11 |

源码验证: jsUIContext.js:469-477, js_container_utils.cpp:24

---

**UIContext.destroyUIContextWithoutWindow()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static destroyUIContextWithoutWindow(): void` |
| 返回值 | `void` |
| 开放范围 | Public (atomicservice only) |
| 错误码 | N/A |
| 关联 AC | AC-2.12 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | g_WindowFreeContainer 存在 | DestroyContainer + RemoveAndCheck + g_WindowFreeContainer.Reset() | AC-2.12 |
| 2 | g_WindowFreeContainer 为 null | LOGW 并直接返回 | AC-2.12 |

源码验证: jsUIContext.js:479-484, window_free_container.cpp:229-238

---

**UIContext.runScopedTask(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `runScopedTask(callback: () => void): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.13 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | () => void | 是 | 无 | 若为 undefined/null，作用域仍设置/恢复但回调不执行 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | callback 为有效函数 | withInstanceId(instanceId) 设置作用域 → 执行 callback → restoreInstanceId 恢复 | AC-2.13 |
| 2 | callback 为 undefined | withInstanceId 设置作用域 → 跳过回调 → restoreInstanceId 恢复 | AC-2.13 |

源码验证: jsUIContext.js:721-726, jsUIContext.js:2036-2043

---

**UIContext.getHostContext()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getHostContext(): Context \| undefined` |
| 返回值 | `Context \| undefined` — 宿主上下文或 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.14 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 UIContext | 在 instanceId 作用域内返回 getContext() 对应 Context | AC-2.14 |
| 2 | instanceId=-1 或 Container 已销毁 | 返回 undefined | AC-2.14 |

源码验证: jsUIContext.js:808-812, @ohos.arkui.UIContext.ts:975-977

---

**UIContext.getSharedLocalStorage()**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getSharedLocalStorage(): LocalStorage \| undefined` |
| 返回值 | `LocalStorage \| undefined` — 共享 LocalStorage 或 undefined |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.15 |

**参数约束**

无参数。

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 UIContext | 在 instanceId 作用域内返回 NativeLocalStorage.GetShared() | AC-2.15 |
| 2 | instanceId=-1 或 Container 已销毁 | 返回 undefined | AC-2.15 |

源码验证: jsUIContext.js:814-818, @ohos.arkui.UIContext.ts:924-926

## 兼容性声明

- **已有 API 行为变更:** 否，本特性为纯新增 API，不修改已有 UIContext 接口签名
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（getId @since 10）；runScopedTask/getHostContext/getSharedLocalStorage/getWindowName/getWindowId/isAvailable @since 12；createUIContextWithoutWindow/destroyUIContextWithoutWindow @since 17；resolveUIContext 系列/构造器 @since 22
- **API 版本号策略:** @since 标注随版本递增，不同 API 的平台限定（crossplatform vs atomicservice only）与版本号不可混用

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 决策链不可跳步 | CurrentIdWithReason 严格按 SCOPE→UNDEFINED→SINGLETON→ACTIVE→FOREGROUND→DEFAULT 顺序执行 | AC-2.1~AC-2.6 |
| Window-Free 单例 | g_WindowFreeContainer 为进程级静态指针，同一进程内所有 atomicservice 共享同一实例 | AC-2.11 |
| 零窗口模型 | Window-Free 使用 RosenWindow(nullptr) + INVALID_WINDOW_ID，无窗口生命周期 | AC-2.11, AC-2.18, AC-2.19 |
| 单线程模型 | Window-Free 容器 usePlatformAsUIThread + useUIAsJSThread，UI 和 JS 在同一线程 | AC-2.11 |
| ContainerScope RAII | CurrentId 使用线程局部 currentId_，不可跨线程传递 | AC-2.7, AC-2.13 |
| 实例 ID 空间 | ContainerType × 100000 分域；WINDOW_FREE_CONTAINER ID ∈ [900000, 999999] | AC-2.8, AC-2.11 |
| isDynamicRender 排除 | Window-Free/DynamicComponent 不参与 UpdateRecentActive/UpdateRecentForeground | AC-2.16, AC-2.17 |
| destroyedUIContextCache_ 上限 | MAX_DESTROYED_CACHE_SIZE=10，溢出淘汰 destroyTime_ 最小条目 | AC-2.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | resolveUIContext ≤ 1ms（仅查全局注册表+原子变量读取） | 单元测试计时 | container_scope.cpp:403-425 |
| 性能 | getAllUIContexts 内存：返回数组大小=存活实例数，典型≤10 | 内存分析 | container_scope.h:86 |
| 性能 | Window-Free 创建 ≤ 50ms（无窗口初始化） | 集成测试计时 | window_free_container.cpp:176-227 |
| 内存 | destroyedUIContextCache_ ≤ 10条×UIContextCacheInfo ≈ 640字节 | 内存分析 | ace_engine.h:84-85 |
| 安全 | isAvailable() 对已销毁 Container 必须返回 false，不产生悬空引用 | NAPI 测试 | jsUIContext.js:1061-1062 |
| 可靠性 | Container 销毁同步：DestroyContainer 在 UI/JS 线程同步执行，不泄漏 | 集成测试 | window_free_container.cpp:229-238 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板 | 多窗口场景下 resolveUIContext 按 CALLING_SCOPE→ACTIVE→FOREGROUND→DEFAULT 正常工作 | LAST_FOCUS/LAST_FOREGROUND 按窗口生命周期触发 | NAPI 测试 | jsUIContext.js:429-451 |
| 穿戴设备 | 单实例场景 UNIQUE 策略优先 | 无多窗口冲突 | NAPI 测试 | container_scope.cpp:413-414 |
| 2in1 设备 | 多窗口+多实例典型场景 | 所有策略均需覆盖 | NAPI 测试 | container_scope.cpp:403-425 |
| 原子化服务 | createUIContextWithoutWindow/destroyUIContextWithoutWindow 仅此场景可用 | Window-Free 单例离屏，0×0 | NAPI 测试 | js_container_utils.cpp:24 |
| TV | crossplatform API 可用，Window-Free 不适用 | 单窗口为主 | NAPI 测试 | container_scope.cpp:413-414 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | runScopedTask/getHostContext/getSharedLocalStorage 不影响无障碍 | — |
| 大字体 | 否 | 身份查询与作用域调度不涉及字体缩放 | — |
| 深色模式 | 否 | 本特性不涉及颜色/主题 | — |
| 多窗口/分屏 | 是 | resolveUIContext 决策链与多窗口生命周期强关联 | AC-2.1~AC-2.6 |
| 多用户 | 否 | ContainerScope 不区分用户 | — |
| 版本升级 | 是 | 不同 API @since 版本差异需注意兼容性 | R-10 |
| 生态兼容 | 是 | resolveUIContext 为 crossplatform，Window-Free 仅 atomicservice | R-10 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 茎围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "ContainerScope::CurrentIdWithReason 决策链实现与 InstanceIdGenReason 映射"
  - repo: "openharmony/ace_engine"
    query: "Window-Free Container 单例创建与销毁流程"
  - repo: "openharmony/ace_engine"
    query: "runScopedTask withInstanceId RAII 作用域设置与恢复机制"
  - repo: "openharmony/ace_engine"
    query: "destroyedUIContextCache_ 缓存策略与 GetEnhancedContextBNotFoundMessage 错误增强"
```

关键文档:

- ContainerScope 头文件: frameworks/core/common/container_scope.h:29-86
- ContainerScope 实现: frameworks/core/common/container_scope.cpp:403-425
- AceEngine 头文件: frameworks/core/common/ace_engine.h:40-85
- UIContext JS 定义: frameworks/bridge/declarative_frontend/engine/jsUIContext.js
- UIContext ArkTS 定义: frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.UIContext.ts
- JSScopeUtil: frameworks/bridge/declarative_frontend/jsview/js_scope_util.cpp:126-134
- NAPI container_utils: interfaces/napi/kits/container_utils/js_container_utils.cpp
- Feat-01 UIContext 接口总纲: specs/04-common-capability/12-ui-context/01-ui-context-interface/Feat-01-uicontext-entry-architecture-instance-routing-spec.md
