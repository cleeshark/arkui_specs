# 特性规格

> Func-07-02-04-Feat-01 ObserveV2 核心机制：固化 ArkUI V2 状态管理共享的 `trackInternal` getter/setter 安装、`ObserveV2` 单例依赖收集（`addRef` 双向映射）、变更分发（`fireChange` ID 分段路由）、异步 dirty 调度（`updateDirty2Optimized`）、惰性集合代理（`autoProxyObject`）、依赖图 GC（`WeakRefPool` + `FinalizationRegistry`）行为规格。本特性是全部 V2 装饰器（`@ObservedV2`/`@Trace`/`@Local`/`@Param`/`@Provider`/`@Consumer`/`@Computed`/`@Monitor` 等）的运行时基础。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ObserveV2 核心机制 |
| 特性编号 | Func-07-02-04-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 12 起支持核心机制；UIUtils.applySync/flushUpdates/flushUIUpdates 同步刷新 API 22 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Draft |
| ObserveV2 单例 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts` | — |
| 惰性 Proxy | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_observed_proxy.ts` | — |
| WeakRefPool | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/weakref_pool.ts` | — |
| UIUtils | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts` | — |
| makeObserved | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_make_observed.ts` | — |
| 状态管理原理介绍 | `docs/zh-cn/application-dev/ui/state-management/arkts-state-management-introduce.md` | — |
| V1/V2 更新机制差异 | `docs/zh-cn/application-dev/ui/state-management/arkts-v1-v2-update-difference.md` | — |

---

## 用户故事

### US-1: trackInternal getter/setter 安装

**作为** 应用开发者,
**我想要** V2 装饰器（@Trace/@Local/@Provider 等）在原生数据上直接安装 getter/setter,
**以便** 属性读写被透明拦截，无需 V1 的属性包装对象开销。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `trackInternal`（`v2_change_observation.ts:1741-1780`）安装某属性 THEN 将原值移动到 `__ob_<prop>` 后备存储，在原属性装 getter 与 setter | 正常 |
| AC-1.2 | WHEN 读取被 track 的属性（getter 触发）THEN getter 调 `ObserveV2.addRef(target, attrName)` 记录依赖，并经 `autoProxyObject` 惰性包装集合类型 | 正常 |
| AC-1.3 | WHEN 赋值被 track 的属性（setter 触发）且新值与旧值严格 `!==` THEN setter 调 `ObserveV2.fireChange(target, attrName)` 触发变更分发 | 正常 |
| AC-1.4 | WHEN 赋值被 track 的属性且新值与旧值严格 `===` THEN setter 跳过 `fireChange`（值未变化） | 边界 |

### US-2: ObserveV2 addRef 双向依赖收集

**作为** 框架维护者,
**我想要** ObserveV2 单例在 getter 触发时记录双向依赖映射,
**以便** 变更分发时能精确查询依赖该属性的 id 列表，GC 时能反向清理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN getter 调 `ObserveV2.addRef`(423) THEN 记录到 `target[SYMBOL_REFS]`（属性 → 依赖它的 id 集合）与 `ObserveV2.id2targets_`（id → 它依赖的属性集合） | 正常 |
| AC-2.2 | WHEN 同一 id 多次读取同一属性 THEN 依赖去重，仅记录一次 | 边界 |
| AC-2.3 | WHEN `@ObservedV2` 类属性数 > 5 THEN 启用 ID_REFS 反向映射优化加速 `clearBinding` | 正常 |
| AC-2.4 | WHEN 非渲染上下文（无当前 id）读取属性 THEN `addRef` 不记录依赖（V2 渲染期保护） | 边界 |

### US-3: fireChange 变更分发与 ID 分段路由

**作为** 框架维护者,
**我想要** `fireChange` 按 ID 区间分发变更到不同子系统,
**以便** @Computed/@Monitor/PersistenceV2/elmtId 各自独立调度，互不干扰。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN setter 调 `ObserveV2.fireChange`(619) THEN 按 ID 区间分发：`ComputedV2.MIN_COMPUTED_ID=0x1000000000` 段 / Monitor ID 段 / `PersistenceV2.MIN_PERSISTENCE_ID` 段 / 普通 elmtId 段 | 正常 |
| AC-3.2 | WHEN fireChange 处理 @Computed ID 段 THEN 将变更累积到 `computedPropIdsChanged_`，由 `updateDirtyComputedProps`(998) 重算 | 正常 |
| AC-3.3 | WHEN fireChange 处理 @Monitor ID 段 THEN 将变更累积到 `monitorIdsChanged_`，由 `updateDirtyMonitors`(1042) 触发回调 | 正常 |
| AC-3.4 | WHEN fireChange 处理普通 elmtId 段 THEN 将变更累积到 `elmtIdsChanged_`，请求 VSync 重渲染 | 正常 |

### US-4: updateDirty2Optimized 异步调度

**作为** 应用开发者,
**我想要** 一个 microtask 内多次状态变更合并为一次 dirty 批次,
**以便** 避免冗余重渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN fireChange 累积变更后 THEN 经 `Promise.resolve().then()` 调度 `updateDirty`(794) | 正常 |
| AC-4.2 | WHEN `updateDirty` 执行 THEN 设置 `startDirty_=true` 防递归（调度期间的新变更不再触发新调度） | 正常 |
| AC-4.3 | WHEN `updateDirty` 调用 `updateDirty2Optimized`(807) THEN 按 containerId 分组，经 `ViewStackProcessor.scheduleUpdateOnNextVSync` 在 VSync 处理 | 正常 |
| AC-4.4 | WHEN `updateDirty2Optimized` 执行 THEN 顺序：先 `updateDirtyComputedProps`(998) 重算 @Computed → 再 `updateDirtyMonitors`(1042) 触发 @Monitor → 最后标脏 UI elmtId 请求 VSync | 正常 |
| AC-4.5 | WHEN VSync 周期到达 THEN `ViewV2.updateDirtyElements`(`v2_view.ts:762`) 按 elmtId 执行局部重渲染（最多迭代 3 次/VSync） | 正常 |
| AC-4.6 | WHEN 调用 `UIUtils.applySync`(104，API 22+) THEN 闭包内的状态变量修改同步刷新（不走异步调度） | 正常 |
| AC-4.7 | WHEN `applySync` 后需同步 UI 更新 THEN `updateDirty2`(908) 同步路径执行 | 正常 |

### US-5: autoProxyObject 惰性集合代理

**作为** 应用开发者,
**我想要** Array/Set/Map/Date 类型的 @Trace 属性首次读取时自动包装为可观察 Proxy,
**以便** 集合的 push/pop/set/add 等接口调用可被观察。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 首次读取 Array 类型 @Trace 属性 THEN `ObserveV2.autoProxyObject`(1444) 包装为 `ArrayProxyHandler`（`v2_observed_proxy.ts:110-250`） | 正常 |
| AC-5.2 | WHEN 首次读取 Object 类型 @Trace 属性 THEN 包装为 `ObjectProxyHandler`（`v2_observed_proxy.ts:19-108`） | 正常 |
| AC-5.3 | WHEN 首次读取 Map/Set 类型 @Trace 属性 THEN 包装为 `SetMapProxyHandler`（`v2_observed_proxy.ts:252-436`） | 正常 |
| AC-5.4 | WHEN 集合 Proxy 拦截操作 THEN 额外加 `OB_LENGTH` 依赖（length/size 变化可观察） | 正常 |
| AC-5.5 | WHEN 未读取的集合属性 THEN 不包装（惰性，避免未读取集合的代理开销） | 边界 |

### US-6: WeakRefPool 依赖图 GC

**作为** 框架维护者,
**我想要** 观察对象被 GC 时自动清理依赖图,
**以便** 避免内存泄漏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `@ObservedV2` 类实例构造 THEN `observedV2Internal` 调 `WeakRefPool.asyncRegisterToFinalizationRegistry`(68) 注册到 `FinalizationRegistry`(36) | 正常 |
| AC-6.2 | WHEN 观察对象被 GC THEN `FinalizationRegistry` 回调触发依赖图清理 | 正常 |
| AC-6.3 | WHEN `clearBinding` 执行（O(n) 操作）THEN 放入 `idleTasks_` 延迟到空闲时执行，避免阻塞渲染帧 | 正常 |
| AC-6.4 | WHEN `makeObserved`（`v2_make_observed.ts:16-46`，对外 API `UIUtils.makeObserved` line 39）包装普通对象 THEN 该对象同样注册到 `WeakRefPool` 参与 GC | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 trackInternal 安装 |
| AC-1.2 | US-1 | R-2 | 单元测试 getter addRef |
| AC-1.3 | US-1 | R-3 | 单元测试 setter fireChange |
| AC-1.4 | US-1 | R-3 | 单元测试 === 跳过 |
| AC-2.1 | US-2 | R-4 | 单元测试 双向映射 |
| AC-2.2 | US-2 | R-4 | 单元测试 依赖去重 |
| AC-2.3 | US-2 | R-5 | 代码审查 ID_REFS 优化 |
| AC-2.4 | US-2 | R-4 | 单元测试 非渲染期不记录 |
| AC-3.1 | US-3 | R-6 | 单元测试 ID 分段路由 |
| AC-3.2 | US-3 | R-6 | 单元测试 Computed 段 |
| AC-3.3 | US-3 | R-6 | 单元测试 Monitor 段 |
| AC-3.4 | US-3 | R-6 | 单元测试 elmtId 段 |
| AC-4.1 | US-4 | R-7 | 单元测试 Promise 调度 |
| AC-4.2 | US-4 | R-8 | 单元测试 startDirty_ 防递归 |
| AC-4.3 | US-4 | R-7 | 代码审查 updateDirty2Optimized |
| AC-4.4 | US-4 | R-9 | 单元测试 调度顺序 |
| AC-4.5 | US-4 | R-10 | 单元测试 updateDirtyElements |
| AC-4.6 | US-4 | R-11 | 单元测试 applySync |
| AC-4.7 | US-4 | R-11 | 单元测试 updateDirty2 同步 |
| AC-5.1 | US-5 | R-12 | 单元测试 ArrayProxyHandler |
| AC-5.2 | US-5 | R-12 | 单元测试 ObjectProxyHandler |
| AC-5.3 | US-5 | R-12 | 单元测试 SetMapProxyHandler |
| AC-5.4 | US-5 | R-12 | 单元测试 OB_LENGTH |
| AC-5.5 | US-5 | R-12 | 单元测试 惰性未读不包装 |
| AC-6.1 | US-6 | R-13 | 单元测试 FinalizationRegistry 注册 |
| AC-6.2 | US-6 | R-13 | 单元测试 GC 回调 |
| AC-6.3 | US-6 | R-14 | 代码审查 idleTasks_ |
| AC-6.4 | US-6 | R-13 | 单元测试 makeObserved GC |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `trackInternal`（`v2_change_observation.ts:1741-1780`）安装某属性 | 将原值移动到 `__ob_<prop>` 后备存储，在原属性装 getter 与 setter | trackInternal 是模块级 const，被 @Trace/@Local/@Provider 共用 | AC-1.1 |
| R-2 | 行为 | 读取被 track 的属性（getter） | getter 调 `ObserveV2.addRef`(423) 记录依赖，并经 `autoProxyObject`(1444) 惰性包装集合类型 | 集合类型首次读取才包装 | AC-1.2 |
| R-3 | 行为 | 赋值被 track 的属性（setter） | 严格 `!==` 比较通过后调 `ObserveV2.fireChange`(619) 触发变更分发；`===` 相等则跳过 | V2 用 `!==`（V1 用 `===` 反向判断） | AC-1.3, AC-1.4 |
| R-4 | 行为 | getter 调 `addRef` | 记录双向映射：`target[SYMBOL_REFS]`（属性 → id 集合）+ `ObserveV2.id2targets_`（id → 属性集合）；同一 id 重复读取去重；非渲染上下文不记录 | 双向映射支持 GC 反向清理 | AC-2.1, AC-2.2, AC-2.4 |
| R-5 | 行为 | `@ObservedV2` 类属性数 > 5 | 启用 ID_REFS 反向映射优化加速 `clearBinding` | observedV2Internal 构造时判定 | AC-2.3 |
| R-6 | 行为 | setter 调 `fireChange`(619) | 按 ID 区间分发：`ComputedV2.MIN_COMPUTED_ID=0x1000000000` 段 → `computedPropIdsChanged_`；Monitor ID 段 → `monitorIdsChanged_`；Persistence ID 段 → PersistenceV2；普通 elmtId 段 → `elmtIdsChanged_` | ID 分段独立调度 | AC-3.1~AC-3.4 |
| R-7 | 行为 | fireChange 累积变更 | 经 `Promise.resolve().then()` 调度 `updateDirty`(794)；`updateDirty2Optimized`(807) 按 containerId 分组，经 `ViewStackProcessor.scheduleUpdateOnNextVSync` 在 VSync 处理 | 异步合并同 microtask 内多次变更 | AC-4.1, AC-4.3 |
| R-8 | 行为 | `updateDirty` 执行 | 设置 `startDirty_=true`（`v2_change_observation.ts:129` 字段）防递归：调度期间的新变更不再触发新调度 | 防止 fireChange → updateDirty → fireChange 死循环 | AC-4.2 |
| R-9 | 行为 | `updateDirty2Optimized` 执行 | 顺序：先 `updateDirtyComputedProps`(998) 重算 @Computed → 再 `updateDirtyMonitors`(1042) 触发 @Monitor 回调 → 最后标脏 UI elmtId 请求 VSync | Computed 先于 Monitor 先于 UI | AC-4.4 |
| R-10 | 行为 | VSync 周期到达 | `ViewV2.updateDirtyElements`（`v2_view.ts:762`）按 elmtId 执行局部重渲染，最多迭代 3 次/VSync | 迭代上限防死循环 | AC-4.5 |
| R-11 | 行为 | 调用 `UIUtils.applySync`(104，API 22+) | 闭包内的状态变量修改同步刷新（@Computed/@Monitor/UI）；`applySync` 后用 `updateDirty2`(908) 同步路径；`flushUpdates`(108)/`flushUIUpdates`(112) 同步刷新调用前累积的变更 | applySync 用于 animateTo 等需同步场景；错误码 140001（@Computed 内调用）、140002（@Monitor 内调用 flushUpdates） | AC-4.6, AC-4.7 |
| R-12 | 行为 | 首次读取集合类型 @Trace 属性 | `autoProxyObject`(1444) 惰性包装：Array → `ArrayProxyHandler`(110-250)、Object → `ObjectProxyHandler`(19-108)、Map/Set → `SetMapProxyHandler`(252-436)；集合 Proxy 拦截操作时额外加 `OB_LENGTH` 依赖；未读取的集合不包装 | 惰性包装避免未读集合开销 | AC-5.1~AC-5.5 |
| R-13 | 行为 | 观察对象构造/GC | `@ObservedV2` 实例构造时 `observedV2Internal` 调 `WeakRefPool.asyncRegisterToFinalizationRegistry`(68) 注册到 `FinalizationRegistry`(36)；对象 GC 时回调清理依赖图；`makeObserved`（`v2_make_observed.ts:16-46`）包装的对象同样注册 | WeakRefPool 自动 GC 避免内存泄漏 | AC-6.1, AC-6.2, AC-6.4 |
| R-14 | 行为 | `clearBinding` 执行（O(n) 操作） | 放入 `idleTasks_` 延迟到空闲时执行，避免阻塞渲染帧 | O(n) 操作不阻塞渲染 | AC-6.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` trackInternal 安装 |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` getter addRef |
| VM-3 | AC-1.3 | 单元测试 | `v2_tests/` setter fireChange |
| VM-4 | AC-1.4 | 单元测试 | `v2_tests/` === 跳过 |
| VM-5 | AC-2.1 | 单元测试 | `v2_tests/` 双向映射 |
| VM-6 | AC-2.2 | 单元测试 | `v2_tests/` 依赖去重 |
| VM-7 | AC-2.3 | 代码审查 | `v2_decorated_variables.ts` ID_REFS 优化 |
| VM-8 | AC-2.4 | 单元测试 | `v2_tests/` 非渲染期不记录 |
| VM-9 | AC-3.1 | 单元测试 | `v2_tests/` ID 分段路由 |
| VM-10 | AC-3.2 | 单元测试 | `v2_tests/` Computed 段 |
| VM-11 | AC-3.3 | 单元测试 | `v2_tests/` Monitor 段 |
| VM-12 | AC-3.4 | 单元测试 | `v2_tests/` elmtId 段 |
| VM-13 | AC-4.1 | 单元测试 | `v2_tests/` Promise 调度 |
| VM-14 | AC-4.2 | 代码审查 | `v2_change_observation.ts:129` startDirty_ |
| VM-15 | AC-4.3 | 代码审查 | `v2_change_observation.ts:807` updateDirty2Optimized |
| VM-16 | AC-4.4 | 单元测试 | `v2_tests/` 调度顺序 |
| VM-17 | AC-4.5 | 单元测试 | `v2_tests/` updateDirtyElements |
| VM-18 | AC-4.6 | 单元测试 | `v2_tests/` applySync |
| VM-19 | AC-4.7 | 代码审查 | `v2_change_observation.ts:908` updateDirty2 |
| VM-20 | AC-5.1 | 单元测试 | `v2_tests/` ArrayProxyHandler |
| VM-21 | AC-5.2 | 单元测试 | `v2_tests/` ObjectProxyHandler |
| VM-22 | AC-5.3 | 单元测试 | `v2_tests/` SetMapProxyHandler |
| VM-23 | AC-5.4 | 单元测试 | `v2_tests/` OB_LENGTH |
| VM-24 | AC-5.5 | 单元测试 | `v2_tests/` 惰性未读不包装 |
| VM-25 | AC-6.1 | 单元测试 | `common_tests/` FinalizationRegistry 注册 |
| VM-26 | AC-6.2 | 单元测试 | `common_tests/` GC 回调 |
| VM-27 | AC-6.3 | 代码审查 | `v2_change_observation.ts` idleTasks_ |
| VM-28 | AC-6.4 | 单元测试 | `v2_tests/` makeObserved GC |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `ObserveV2` | `v2_change_observation.ts:52-1739` | 全局单例，依赖跟踪、变更分发、dirty 调度、惰性代理 |
| `trackInternal` | `v2_change_observation.ts:1741-1780` | 模块级 const，共享 getter/setter 安装（被 @Trace/@Local/@Provider 共用） |
| `addRef(target, attrName)` | `v2_change_observation.ts:423` | 记录双向依赖映射 |
| `fireChange(target, attrName)` | `v2_change_observation.ts:619` | 变更分发，按 ID 段路由 |
| `updateDirty()` | `v2_change_observation.ts:794-796` | 调度入口，设 startDirty_ 后调 updateDirty2Optimized/2 |
| `updateDirty2Optimized()` | `v2_change_observation.ts:807` | 异步按 VSync 更新（默认路径） |
| `updateDirty2()` | `v2_change_observation.ts:908` | 同步更新（applySync 后用） |
| `updateDirtyComputedProps()` | `v2_change_observation.ts:998` | @Computed 段重算 |
| `updateDirtyMonitors()` | `v2_change_observation.ts:1042` | @Monitor 段回调 |
| `autoProxyObject()` | `v2_change_observation.ts:1444` | 静态方法，惰性包装集合类型 |
| `applySync()`/`flushUpdates()`/`flushUIUpdates()` | `v2_change_observation.ts:1645/1698/1718` | 同步刷新逃生舱（API 22+） |
| `ObjectProxyHandler`/`ArrayProxyHandler`/`SetMapProxyHandler` | `v2_observed_proxy.ts:19-108/110-250/252-436` | 集合类型 Proxy 拦截 |
| `WeakRefPool` | `weakref_pool.ts:32-141` | 规范化 WeakRef + FinalizationRegistry GC |
| `RefInfo` | `v2_make_observed.ts:16-46` | makeObserved 内部实现 |
| `UIUtilsImpl` | `ui_utils.ts:16-134` | 对外 SDK API（makeObserved/getTarget/applySync 等） |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | ObserveV2 单例引入，trackInternal getter/setter 范式；异步 dirty 调度；惰性集合代理；WeakRefPool GC | V2 核心机制 | V1→V2 迁移见 Feat-06 |
| API 22 | `UIUtils.applySync`/`flushUpdates`/`flushUIUpdates` 同步刷新引入 | 解决 V2 异步调度与 animateTo 不兼容 | 在 animateTo 前用 applySync |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| getter/setter 范式 | V2 在原生数据上装 getter/setter，无属性包装对象；依赖与通知提取到全局 `ObserveV2` 单例 |
| 异步调度 | fireChange 不立即重渲染，经 `Promise.resolve().then()` 合并到 VSync；`applySync`(API 22+) 提供同步逃生舱 |
| ID 分段路由 | fireChange 按 Computed/Monitor/Persistence/elmtId 四段独立路由 |
| 双向依赖映射 | `target[SYMBOL_REFS]` + `ObserveV2.id2targets_` 双向；ID_REFS >5 属性优化 |
| 惰性集合代理 | Array/Set/Map/Date 首次读取才包装（autoProxyObject）；OB_LENGTH 依赖 |
| FinalizationRegistry GC | 观察对象 GC 时自动清理依赖图；clearBinding 延迟到 idleTasks_ |
| V1/V2 不直接混用 | V1 属性包装对象与 V2 getter/setter 范式不同；混用约束见 Feat-06 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 异步合并减少同 microtask 内多次变更的冗余重渲染；惰性代理避免未读集合开销；迭代上限 3 次/VSync 防死循环 |
| 可调试性 | `stateMgmt.setPropertyAccessTrace(true)` 输出详细 `addRef`/`fireChange` 日志；日志关键字：`ObserveV2.addRef 'X' for id N`、`fireChange 'X' dependent ids`、`updateDirty2Optimized() start/end`；元数据检查：`ObserveV2.IsObservedObjectV2(obj)`、`data[SYMBOL_REFS]`、`data.__ob_<prop>` |
| 可观测性 | `UIUtils.canBeObserved`(API 23+) 返回 `{ isObserved, reason, decoratorInfo }`；`hidumper -s WindowManagerService -a "-stateVariables -viewId=N"` |
| 内存 | WeakRefPool + FinalizationRegistry 自动 GC；clearBinding 延迟到 idleTasks_ 避免阻塞 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 全部 V2 装饰器 | @ObservedV2/@Trace/@Local/@Param/@Provider/@Consumer/@Computed/@Monitor（Feat-02~05）均依赖本特性的 trackInternal/ObserveV2 机制 |
| V2 自定义组件 | ViewV2 复用 ObserveV2 调度管线（Feat-06） |
| 跨域协同 | WeakRefPool GC、elmtId 同步与 07-02-14 协同；C++ CustomNode（isV2_=true）集成见 07-02-14 |
| V1 对比 | V1 用属性包装对象 + 同步通知（07-02-01）；V2 用 getter/setter + 异步调度；V1/V2 不应直接混用 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file 信息
- [x] 变更范围 Delta 明确标注为已有实现补录

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:52-1739` | `ObserveV2` 单例：依赖跟踪、变更分发、dirty 调度 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:1741-1780` | `trackInternal` 共享 getter/setter 安装 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:423` | `addRef` 依赖收集 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:619` | `fireChange` 变更分发 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:807` | `updateDirty2Optimized` 异步调度 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:908` | `updateDirty2` 同步路径 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:998/1042` | `updateDirtyComputedProps`/`updateDirtyMonitors` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:1444` | `autoProxyObject` 惰性代理 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:1645/1698/1718` | `applySync`/`flushUpdates`/`flushUIUpdates` 同步刷新 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_observed_proxy.ts:19-108` | `ObjectProxyHandler` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_observed_proxy.ts:110-250` | `ArrayProxyHandler` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_observed_proxy.ts:252-436` | `SetMapProxyHandler` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/weakref_pool.ts:32-141` | `WeakRefPool` + `FinalizationRegistry` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_make_observed.ts:16-46` | `RefInfo` makeObserved 内部实现 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:16-134` | `UIUtilsImpl` 对外 SDK API |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | ObserveV2、trackInternal、Proxy handler、调度管线回归测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | WeakRefPool、UIUtils 共享基础测试 |
