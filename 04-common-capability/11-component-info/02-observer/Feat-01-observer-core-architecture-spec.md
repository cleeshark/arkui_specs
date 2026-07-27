# 特性规格

> Func-04-11-02-Feat-01 无感监听核心架构：固化 UIObserverHandler 单例 + HandleFunc 惰性注册 + NAPI/ANI 双桥接路径 + Context scope 分级 + NodeRenderStatusMonitor 独立架构的核心行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无感监听核心架构 (Observer Core Architecture) |
| 特性编号 | Func-04-11-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 11 起支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/11-component-info/02-observer/design.md` | Baselined |

---

## 用户故事

### US-1: HandleFunc 惰性注册与 Notify 分发

**作为** 框架开发者,
**我想要** 通过 UIObserverHandler 单例管理 HandleFunc 的惰性注册和 Notify 分发,
**以便** Observer 功能零启动开销且按需激活。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 首次调用 on(type) 注册监听器 THEN 对应类型的 HandleFunc 指针从 nullptr 设置为有效函数指针（NAPI 路径设置 func_ 指针，ANI 路径设置 funcForAni_ 指针） | 正常 |
| AC-1.2 | WHEN 再次调用 on(type) 注册同类型监听器 THEN HandleFunc 指针不再重复设置（NAPI 使用布尔标志 isXxxHandleFuncSetted_ 防重，ANI 使用 std::call_once 防重） | 正常 |
| AC-1.3 | WHEN off(type) 移除监听器 THEN HandleFunc 指针不被清除（仅移除 listener from map，HandleFunc 保持已设置状态） | 边界 |
| AC-1.4 | WHEN NAPI 路径首次注册 on(type) THEN UIObserverHandler 的 func_ 指针被设置为 `&UIObserver::Handle*StateChange` 形式的原始函数指针 | 正常 |
| AC-1.5 | WHEN ANI 路径首次注册 on(type) THEN UIObserverHandler 的 funcForAni_ 指针被设置为 `std::function` 包装的 Handle 函数 | 正常 |
| AC-1.6 | WHEN Component Pattern 调用 Notify* 方法 THEN UIObserverHandler 同时检查 func_ 和 funcForAni_ 双指针，分别调用 NAPI 和 ANI Handle 回调（双指针可独立存在，互不干扰） | 正常 |
| AC-1.7 | WHEN NAPI 路径和 ANI 路径同时注册同一 type THEN Notify* 方法触发双路径回调，NAPI 回调到 UIObserverListener::On*，ANI 回调到 ani_fn_object Call | 正常 |

### US-2: on/off/once/unsubscribe 生命周期管理

**作为** 应用开发者,
**我想要** 通过 on/off/once 三种模式注册和取消无感监听，且 on() 返回取消函数作为便捷替代,
**以便** 灵活管理监听器生命周期。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 on(type, callback) 注册监听器 THEN callback 存入 scoped listener map，后续 Notify 触发时调用 callback | 正常 |
| AC-2.2 | WHEN 调用 off(type, callback?) 去注册 THEN 若传入 callback 则仅移除匹配的 listener；若不传 callback 则移除该 scope 下该 type 的全部 listener | 正常 |
| AC-2.3 | WHEN 调用 once(type, callback) 注册一次性监听器 THEN 首次 Notify 触发后 callback 被自动移除（不再接收后续通知） | 正常 |
| AC-2.4 | WHEN on() 返回 UnsubscribeCallback THEN 调用该返回函数等效于调用 off(type, callback)，移除原注册的 listener | 正常 |
| AC-2.5 | WHEN 同 type + 同 scope 重复 on(callback_new) THEN 新 callback 替换旧 callback（旧 listener 被移除，新 listener 存入 map） | 边界 |
| AC-2.6 | WHEN off(type, callback) 传入不匹配的 callback THEN 静默无操作（不报错，不移除其他 listener） | 异常 |
| AC-2.7 | WHEN on(type, null) 或 on(type, undefined) THEN 抛出 401 ParameterError（callback 为必填参数） | 异常 |

### US-3: Context scope 分级机制

**作为** 应用开发者,
**我想要** 通过不同 context 参数控制监听范围（global/UIAbilityContext/UIContext/{id}/{navigationId}/{navigationUniqueId}),
**以便** 仅接收感兴趣范围的 UI 事件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN on(type) 不传 context/options 参数 THEN 监听器注册到 global scope（default instanceId = 0），接收所有同 instanceId 下的通知 | 正常 |
| AC-3.2 | WHEN on(type, UIAbilityContext, callback) THEN 监听器注册到 UIAbilityContext scope，仅接收该 UIAbility 实例的通知 | 正常 |
| AC-3.3 | WHEN on(type, UIContext, callback) THEN 监听器注册到 UIContext scope，仅接收该 UIContext 实例（instanceId）的通知 | 正常 |
| AC-3.4 | WHEN on(type, {id: string}, callback) THEN 监听器注册到 id scope，仅接收指定 id 组件的通知 | 正常 |
| AC-3.5 | WHEN on(type, {navigationId: ResourceStr}, callback) THEN 监听器注册到 navigationId scope，仅接收指定 Navigation 容器的通知 | 正常 |
| AC-3.6 | WHEN on(type, {navigationUniqueId: number}, callback) THEN 监听器注册到 navigationUniqueId scope，仅接收指定 Navigation 实例（uniqueId）的通知 | 正常 |
| AC-3.7 | WHEN on(type, context) 传入不合法 context 类型 THEN 抛出 401 ParameterError | 异常 |
| AC-3.8 | WHEN on(type, {navigationId: ''}) 传入空字符串 navigationId THEN 不报错但无匹配 Navigation 容器，callback 不会被触发（⚠️ 风险说明：空字符串静默无触发，开发者可能困惑） | 边界 |

### US-4: NAPI 桥接路径

**作为** JS 运行时开发者,
**我想要** 通过 NAPI 桥接路径注册和回调 observer 监听器,
**以便** 在 JS 运行时中使用 @ohos.arkui.observer API。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN NAPI 模块加载 THEN `napi_module_register` 注册模块名 `"arkui.observer"`，导出 on/off 函数和枚举属性 | 正常 |
| AC-4.2 | WHEN NAPI on(type) 调用 THEN ObserverProcess::ProcessRegister 按 type 字符串查找 registerProcessMap_ 分发到对应 Process*Register 方法 | 正常 |
| AC-4.3 | WHEN NAPI Notify 回调 THEN UIObserverListener::On* 方法构建 napi_value 参数对象并调用 JS callback（napi_call_function） | 正常 |
| AC-4.4 | WHEN NAPI 监听器存储 THEN UIObserver 静态类使用 static unordered_map 按 scope key 分区存储 listener | 正常 |
| AC-4.5 | WHEN NAPI context 解析 THEN IsUIAbilityContext(env, context) 检查 `abilityInfo.name` 属性判断 UIAbilityContext；GetUIContextInstanceId(env, context) 提取 `instanceId_` 属性判断 UIContext | 正常 |

### US-5: ANI 桥接路径

**作为** ArkTS-static 运行时开发者,
**我想要** 通过 ANI 桥接路径注册和回调 observer 监听器,
**以便** 在 ArkTS-static 运行时中使用 @ohos.arkui.observer API。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN ANI 创建 UIObserver 实例 THEN createUIObserver(instanceId) 返回 nativeObserverAddr 长整数，存储在 ArkTS 对象的 nativeObserverAddr 字段 | 正常 |
| AC-5.2 | WHEN ANI on(type) 调用 THEN UiObserver 实例方法 Register* 使用 ani_ref / ani_fn_object 注册 callback，std::call_once 设置 HandleFuncForAni | 正常 |
| AC-5.3 | WHEN ANI Notify 回调 THEN UiObserver Handle* 方法使用 FunctionalObject_Call 调用 ani_fn_object 回调到 ArkTS | 正常 |
| AC-5.4 | WHEN ANI 监听器存储 THEN UiObserver 实例成员 map（per instanceId）存储 listener，不使用 static 成员 | 正常 |
| AC-5.5 | WHEN ANI namespace 级别函数（如 onNavDestinationUpdate）THEN 使用 UiObserver::Register* static 方法，独立于实例方法 | 正常 |

### US-6: NodeRenderStatusMonitor 独立架构

**作为** 框架开发者,
**我想要** 通过 NodeRenderStatusMonitor 逐节点监听渲染可见性状态（ABOUT_TO_RENDER_IN/OUT）,
**以便** 开发者感知特定节点的可见性变化而不依赖全局广播。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 on('nodeRenderState', {uniqueId}, callback) THEN NodeRenderStatusMonitor 懒创建于 PipelineContext，注册该节点监听器 | 正常 |
| AC-6.2 | WHEN 注册 nodeRenderState 监听器超过 64 个 THEN 超限注册静默失败不报错（⚠️ 风险说明：开发者无感知超限） | 边界 |
| AC-6.3 | WHEN PipelineContext 驱动 WalkThroughAncestorForStateListener THEN 遍历注册节点的祖先链，检查 IsVisible()/IsActive()/IsOnMainTree() 三项条件 | 正常 |
| AC-6.4 | WHEN 注册节点的全部祖先满足 IsVisible()+IsActive()+IsOnMainTree() THEN 回调 ABOUT_TO_RENDER_IN | 正常 |
| AC-6.5 | WHEN 注册节点的任一祖先不满足上述条件 THEN 回调 ABOUT_TO_RENDER_OUT | 正常 |
| AC-6.6 | WHEN on('nodeRenderState', {uniqueId: 0}) 传入非法 uniqueId THEN 抛出 401 ParameterError | 异常 |

### US-7: 错误码与参数校验

**作为** 应用开发者,
**我想要** 在传入非法参数时收到明确的错误信息,
**以便** 快速定位和修正调用错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN on(type) 的 type 字符串不在 23 种法定值中 THEN 抛出 401 ParameterError | 异常 |
| AC-7.2 | WHEN on(type, callback) 的 callback 为 null/undefined THEN 抛出 401 ParameterError | 异常 |
| AC-7.3 | WHEN on(type, context) 的 context 类型不匹配（如传入 string 给要求 UIAbilityContext 的 type）THEN 抛出 401 ParameterError | 异常 |
| AC-7.4 | WHEN on(type, {navigationUniqueId: -1}) 传入负数 uniqueId THEN 抛出 401 ParameterError | 异常 |
| AC-7.5 | WHEN on(type, options) 的 options 字段缺失（如 {id} type 未传 id）THEN 抛出 401 ParameterError | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.7 | R-1~R-6 | 已有实现 | 单测/代码评审 | observer_handler.cpp:156-159, js_ui_observer.cpp:380-401 |
| AC-2.1~2.7 | R-7~R-12 | 已有实现 | XTS | ui_observer.cpp, observer.cpp |
| AC-3.1~3.8 | R-13~R-19 | 已有实现 | XTS | ui_observer.cpp static maps |
| AC-4.1~4.5 | R-20~R-23 | 已有实现 | 代码评审 | js_ui_observer.cpp:2011-2024 |
| AC-5.1~5.5 | R-24~R-27 | 已有实现 | 代码评审 | observer.cpp (ANI) |
| AC-6.1~6.6 | R-28~R-32 | 已有实现 | 单测 | node_render_status_monitor.cpp:27, 175-213 |
| AC-7.1~7.5 | R-33~R-36 | 已有实现 | XTS | js_ui_observer.cpp, observer.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 首次 on(type) 注册 | HandleFunc 指针从 nullptr 设置为有效函数指针 | NAPI 布尔标志 / ANI std::call_once 防重 | AC-1.1 |
| R-2 | 行为 | 再次 on(type) 注册同类型 | HandleFunc 指针不重复设置 | 布尔标志 / call_once 保证 | AC-1.2 |
| R-3 | 边界 | off(type) 移除监听器 | HandleFunc 指针不被清除，保持已设置状态 | 设计选择：惰性注册+永不清理 | AC-1.3 |
| R-4 | 行为 | NAPI 首次注册 | func_ 指针设置为 `&UIObserver::Handle*StateChange` 原始函数指针 | 原始函数指针类型 | AC-1.4 |
| R-5 | 行为 | ANI 首次注册 | funcForAni_ 指针设置为 `std::function` 包装的 Handle 函数 | std::function 类型 | AC-1.5 |
| R-6 | 行为 | Notify* 方法调用 | 检查 func_ 和 funcForAni_ 双指针，分别回调 NAPI 和 ANI | 双指针独立存在互不干扰 | AC-1.6, AC-1.7 |
| R-7 | 行为 | on(type, callback) | callback 存入 scoped listener map | — | AC-2.1 |
| R-8 | 行为 | off(type, callback?) | 传 callback 移除匹配 listener；不传移除该 scope 该 type 全部 | — | AC-2.2 |
| R-9 | 行为 | once(type, callback) | 首次触发后自动移除 | — | AC-2.3 |
| R-10 | 行为 | on() 返回值 | 返回 UnsubscribeCallback 函数 | 调用等效于 off | AC-2.4 |
| R-11 | 边界 | 同 type + 同 scope 重复 on | 新 callback 替换旧 callback | 旧 listener 移除 | AC-2.5 |
| R-12 | 异常 | off(type, mismatched callback) | 静默无操作 | 不报错 | AC-2.6 |
| R-13 | 行为 | 不传 context/options | 注册到 global scope（instanceId=0） | — | AC-3.1 |
| R-14 | 行为 | 传 UIAbilityContext | 注册到 UIAbilityContext scope | abilityInfo.name 为分区 key | AC-3.2 |
| R-15 | 行为 | 传 UIContext | 注册到 UIContext scope | instanceId_ 为分区 key | AC-3.3 |
| R-16 | 行为 | 传 {id: string} | 注册到 id scope | id 字符串为分区 key | AC-3.4 |
| R-17 | 行为 | 传 {navigationId} | 注册到 navigationId scope | navigationId 为分区 key | AC-3.5 |
| R-18 | 行为 | 传 {navigationUniqueId} | 注册到 navigationUniqueId scope | uniqueId 数字的字符串为分区 key | AC-3.6 |
| R-19 | 异常 | 不合法 context 类型 | 抛出 401 ParameterError | — | AC-3.7 |
| R-20 | 行为 | NAPI 模块加载 | 注册 `arkui.observer` 模块，导出 on/off + 枚举 | napi_module_register | AC-4.1 |
| R-21 | 行为 | NAPI on(type) | ObserverProcess::ProcessRegister 按 registerProcessMap_ 分发 | 23 种 type 字符串 | AC-4.2 |
| R-22 | 行为 | NAPI Notify 回调 | UIObserverListener::On* 构建 napi_value 参数对象并调用 | napi_call_function | AC-4.3 |
| R-23 | 行为 | NAPI 监听器存储 | UIObserver 静态 map 按 scope key 分区 | static unordered_map | AC-4.4 |
| R-24 | 行为 | ANI 创建实例 | createUIObserver(instanceId) 返回 nativeObserverAddr | per-instance | AC-5.1 |
| R-25 | 行为 | ANI on(type) | UiObserver Register* + std::call_once HandleFunc | ani_ref / ani_fn_object | AC-5.2 |
| R-26 | 行为 | ANI Notify 回调 | FunctionalObject_Call 回调到 ArkTS | ani_fn_object | AC-5.3 |
| R-27 | 行为 | ANI 监听器存储 | UiObserver 实例成员 map per instanceId | 非 static | AC-5.4 |
| R-28 | 行为 | nodeRenderState 注册 | PipelineContext 懒创建 NodeRenderStatusMonitor | 首次 on 触发 | AC-6.1 |
| R-29 | 边界 | 超过 64 节点注册 | 静默失败不报错 | ⚠️ 风险说明 | AC-6.2 |
| R-30 | 行为 | WalkThroughAncestorForStateListener | 遍历祖先链检查 IsVisible/IsActive/IsOnMainTree | 三项条件 | AC-6.3 |
| R-31 | 行为 | 全部祖先满足条件 | 回调 ABOUT_TO_RENDER_IN | — | AC-6.4 |
| R-32 | 行为 | 任一祖先不满足 | 回调 ABOUT_TO_RENDER_OUT | — | AC-6.5 |
| R-33 | 异常 | 非法 type 字符串 | 抛出 401 ParameterError | 23 种法定值 | AC-7.1 |
| R-34 | 异常 | callback 为 null/undefined | 抛出 401 ParameterError | — | AC-7.2 |
| R-35 | 异常 | context 类型不匹配 | 抛出 401 ParameterError | — | AC-7.3 |
| R-36 | 异常 | navigationUniqueId 为负数或 0 | 抛出 401 ParameterError | — | AC-7.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 HandleFunc 惰性设置 | 单测 | Mock on() 调用，验证 HandleFunc 指针变化 |
| VM-2 | AC-1.2 HandleFunc 不重复设置 | 单测 | 连续 on()，验证布尔标志 / call_once |
| VM-3 | AC-1.3 off 不清除 HandleFunc | 单测 | on → off → on，验证 HandleFunc 指针不变 |
| VM-4 | AC-1.6 双指针 Notify | 单测 | Mock 双路径注册，验证双回调触发 |
| VM-5 | AC-2.1~2.4 生命周期管理 | XTS | on/off/once/unsubscribe 四种模式全覆盖 |
| VM-6 | AC-2.5 重复 on 替换 | XTS | 同 scope 两次 on，验证仅新 callback 触发 |
| VM-7 | AC-3.1~3.6 scope 分级 | XTS | 各 scope 类型注册 + 限定触发 |
| VM-8 | AC-3.7 非法 context | XTS | 验证 401 错误码抛出 |
| VM-9 | AC-6.1 懒创建 Monitor | 单测 | 验证 PipelineContext 首次 on 时创建 Monitor |
| VM-10 | AC-6.2 64 节点限制 | 单测 | 注册 65 个节点，验证第 65 个静默失败 |
| VM-11 | AC-6.4~6.5 状态判定 | 单测 | 遍历祖先链逻辑验证 |
| VM-12 | AC-7.1~7.5 参数校验 | XTS | 各非法参数场景 401 错误码 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|----------|--------|-----------|----------|---------|
| uiObserver.on(type, callback) | Public | type: string, callback: Callback | UnsubscribeCallback | 401 | 注册全局 scope 监听器 | AC-2.1, AC-3.1 |
| uiObserver.on(type, context, callback) | Public | type: string, context: UIAbilityContext \| UIContext, callback: Callback | UnsubscribeCallback | 401 | 注册 context scope 监听器 | AC-2.1, AC-3.2~3.3 |
| uiObserver.on(type, options, callback) | Public | type: string, options: {id \| navigationId \| uniqueId}, callback: Callback | UnsubscribeCallback | 401 | 注册 options scope 监听器 | AC-2.1, AC-3.4~3.6 |
| uiObserver.off(type, callback?) | Public | type: string, callback?: Callback | void | — | 去注册监听器 | AC-2.2, AC-2.6 |
| uiObserver.once(type, callback) | Public | type: string, callback: Callback | UnsubscribeCallback | 401 | 一次性监听 | AC-2.3 |

### 变更/废弃 API

N/A，API 行为无变化（补录规格）。

## 接口规格

### 接口定义

**uiObserver.on(type, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `on(type: string, callback: Callback\<T\>): UnsubscribeCallback` |
| 返回值 | `UnsubscribeCallback` — 调用即去注册 |
| 开放范围 | Public |
| 错误码 | 401 (ParameterError) |
| 关联 AC | AC-2.1, AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | string | 是 | — | 23 种法定值，非法值抛 401 |
| callback | Callback\<T\> | 是 | — | null/undefined 抛 401 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | on('navDestinationUpdate', cb) | 注册 global scope 监听器，返回 UnsubscribeCallback | AC-2.1 |
| 2 | on('navDestinationUpdate', null) | 抛出 401 ParameterError | AC-7.2 |
| 3 | on('invalidType', cb) | 抛出 401 ParameterError | AC-7.1 |

---

**uiObserver.on(type, context, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `on(type: string, context: UIAbilityContext \| UIContext, callback: Callback\<T\>): UnsubscribeCallback` |
| 返回值 | `UnsubscribeCallback` — 调用即去注册 |
| 开放范围 | Public |
| 错误码 | 401 (ParameterError) |
| 关联 AC | AC-3.2, AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | string | 是 | — | 仅限支持 context scope 的 type 值 |
| context | UIAbilityContext \| UIContext | 是 | — | null/undefined 或类型不匹配抛 401 |
| callback | Callback\<T\> | 是 | — | null/undefined 抛 401 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | on('routerPageUpdate', UIAbilityContext, cb) | 注册 UIAbilityContext scope | AC-3.2 |
| 2 | on('routerPageUpdate', UIContext, cb) | 注册 UIContext scope | AC-3.3 |
| 3 | on('routerPageUpdate', string, cb) | 抛出 401（string 不是合法 context） | AC-7.3 |

---

**uiObserver.on(type, options, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `on(type: string, options: ObserverOptions \| {navigationId} \| {navigationUniqueId}, callback: Callback\<T\>): UnsubscribeCallback` |
| 返回值 | `UnsubscribeCallback` — 调用即去注册 |
| 开放范围 | Public |
| 错误码 | 401 (ParameterError) |
| 关联 AC | AC-3.4~3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | string | 是 | — | 仅限支持 options scope 的 type 值 |
| options | object | 是 | — | 必须包含对应 scope 字段（id/navigationId/navigationUniqueId），缺失抛 401 |
| callback | Callback\<T\> | 是 | — | null/undefined 抛 401 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | on('scrollEvent', {id: 'myScroll'}, cb) | 注册 id scope | AC-3.4 |
| 2 | on('navDestinationUpdate', {navigationId: 'nav1'}, cb) | 注册 navigationId scope | AC-3.5 |
| 3 | on('navDestinationUpdateByUniqueId', {navigationUniqueId: 123}, cb) | 注册 uniqueId scope | AC-3.6 |
| 4 | on('navDestinationUpdate', {navigationId: ''}, cb) | 不报错但无匹配，callback 不触发 | AC-3.8 |

---

**uiObserver.off(type, callback?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `off(type: string, callback?: Callback\<T\>): void` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | string | 是 | — | 23 种法定值 |
| callback | Callback\<T\> | 否 | — | 不传则移除该 scope 该 type 全部；不匹配静默无操作 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | off('navDestinationUpdate', cb) | 移除匹配的 listener | AC-2.2 |
| 2 | off('navDestinationUpdate') | 移除该 scope 该 type 全部 listener | AC-2.2 |
| 3 | off('navDestinationUpdate', mismatched) | 静默无操作 | AC-2.6 |

---

**uiObserver.once(type, callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `once(type: string, callback: Callback\<T\>): UnsubscribeCallback` |
| 返回值 | `UnsubscribeCallback` — 调用即去注册 |
| 开放范围 | Public |
| 错误码 | 401 (ParameterError) |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type | string | 是 | — | 23 种法定值 |
| callback | Callback\<T\> | 是 | — | null/undefined 抛 401；首次触发后自动移除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | once('navDestinationUpdate', cb) | 首次触发回调后自动移除 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（补录规格，无行为变更）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11
- **API 版本号策略:** @since 标注各枚举值和接口扩展版本

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UIObserverHandler 单例 | Meyer's singleton，进程唯一 | AC-1.1 |
| HandleFunc 惰性注册 | 首次 on() 设置，永不清理 | AC-1.1~1.3 |
| NAPI/ANI 双指针 | func_ 和 funcForAni_ 独立设置和调用 | AC-1.4~1.7 |
| NodeRenderStatusMonitor 64 限制 | 最多 64 节点，超限静默失败 | AC-6.2 |
| Context scope 分级 | 5 级 scope，各 type 按需支持 | AC-3.1~3.6 |
| JS 单线程模型 | on/off/Notify 均在 TaskThread | AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | HandleFunc 惰性注册，未使用 type 零开销 | 单测 | observer_handler.cpp |
| 内存 | UIObserver 静态 map + UiObserver 实例 map | 代码评审 | ui_observer.cpp |
| 可测试性 | 各 on() type 可独立 mock Notify 触发 | 单测/XTS | — |
| 自动化维测 | 401 错误码覆盖所有非法参数场景 | XTS | — |
| 定界定位 | Scoped map 按 key 分区，问题可按 scope 定位 | 代码评审 | — |

## 多设备适配声明

无差异 — Observer 功能在所有设备类型上行为一致。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Observer 不涉及无障碍 | — |
| 大字体 | 否 | Observer 不涉及大字体 | — |
| 深色模式 | 否 | Observer 不涉及深色模式 | — |
| 多窗口/分屏 | 是 | 每个 UIContext 有独立 instanceId，多窗口监听器天然分区 | 多 UIContext 注册 |
| 多用户 | 否 | Observer 不涉及多用户 | — |
| 版本升级 | 是 | 新 API 版本追加枚举值（如 NavDestinationState），旧值不变 | API 11→12→17 |
| 生态兼容 | 否 | Observer 无权限要求，无跨进程调用 | — |

## 行为场景（可选，Gherkin）

Feature: 无感监听核心架构
  作为 应用开发者
  我想要 通过 observer API 注册 scoped 监听器
  以便 按需接收 UI 生命周期和状态变化事件

  Scenario: 首次注册惰性设置 HandleFunc
    Given UIObserverHandler HandleFunc 指针为 nullptr
    When 调用 on('navDestinationUpdate', callback)
    Then handleNavigationChangeFunc_ 从 nullptr 变为有效函数指针
    And handleNavigationChangeFuncForAni_ 保持 nullptr（NAPI only）

  Scenario: 重复注册不重复设置 HandleFunc
    Given handleNavigationChangeFunc_ 已设置
    And isNavigationHandleFuncSetted_ = true
    When 再次调用 on('navDestinationUpdate', callback_new)
    Then handleNavigationChangeFunc_ 不变（不重复设置）
    And callback_new 替换旧 listener

  Scenario: off 不清除 HandleFunc
    Given on('navDestinationUpdate', cb) 已注册
    When 调用 off('navDestinationUpdate', cb)
    Then listener 从 map 移除
    And handleNavigationChangeFunc_ 仍为有效指针

  Scenario: NodeRenderState 超限静默失败
    Given 已注册 64 个 nodeRenderState 监听器
    When 调用 on('nodeRenderState', {uniqueId: 65}, cb)
    Then 注册静默失败（不报错）
    And callback 不会被触发

  Scenario Outline: 非法参数校验
    When 调用 on(<type>, <param>, <callback>)
    Then 抛出 401 ParameterError

    Examples:
      | type | param | callback |
      | invalidType | — | cb |
      | navDestinationUpdate | — | null |
      | routerPageUpdate | string | cb |
      | navDestinationUpdateByUniqueId | {uniqueId: -1} | cb |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "UIObserverHandler singleton HandleFunc lazy registration and Notify dispatch mechanism"
  - repo: "openharmony/arkui_ace_engine"
    query: "NAPI ObserverProcess on/off/once dispatch and UIObserver static listener storage"
  - repo: "openharmony/arkui_ace_engine"
    query: "ANI UiObserver per-instance registration and std::call_once HandleFunc setup"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeRenderStatusMonitor WalkThroughAncestorForStateListener and 64 node limit"
  - repo: "openharmony/interface_sdk-js"
    query: "@ohos.arkui.observer d.ts API surface and enum definitions"
```

**关键文档：** `/interface/sdk-js/api/@ohos.arkui.observer.d.ts`, `/ace_engine/frameworks/core/components_ng/base/observer_handler.h`, `/ace_engine/interfaces/napi/kits/observer/js_ui_observer.cpp`, `/ace_engine/interfaces/ets/ani/observer/src/observer.cpp`
