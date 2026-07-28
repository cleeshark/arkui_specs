# 特性规格

> Func-04-06-06-Feat-01 NodeAdapter ArkTS 前端规格：固化公开 `NodeAdapter` class（动态 `@ohos.arkui.node`/`FrameNode.d.ts` `@since 12 dynamic`，`isDisposed()` 除外 `@since 20 dynamic`；静态 `FrameNode.static.d.ets` `@since 23 static` 作变体）、19 成员（constructor/dispose/isDisposed/`totalNodeCount` get-set/`reloadAllItems`/`reloadItem`/`removeItem`/`insertItem`/`moveItem`/`getAllAvailableItems`/6 生命周期回调/`static attachNodeAdapter`/`detachNodeAdapter`）、TS 运行时 `node_adapter.ts`、JSI 桥 `NodeAdapterBridge`、C++ `UINodeAdapter` 包装、`needUpdateEvent_=true`（ON_UPDATE_NODE 路由 onUpdateChild）、构造时绑定 trampoline、负参静默忽略、TS 侧 attach 预校验 + 容器白名单行为规格。复用 LazyForEach 管线（07-05-02）；C-API/NDK 公开层为独立 Feat（后续补录）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | NodeAdapter ArkTS 前端规格 |
| 特性编号 | Func-04-06-06-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 动态 `@since 12 dynamic`（`isDisposed()` `@since 20 dynamic`）；静态 `@since 23 static`（变体） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-04-06-06（NodeAdapter）以 **TS 侧为基线**的首个 Feat：聚焦公开 `NodeAdapter` class 的 ArkTS 行为、TS 运行时（`node_adapter.ts`）、TS↔native 桥接（JSI `NodeAdapterBridge` + C++ `UINodeAdapter` 包装）。NodeAdapter 复用 LazyForEach 管线（LazyForEachNode/LazyForEachBuilder/DataChangeListener，07-05-02），不重新实现懒渲染；底层 `NativeLazyForEachBuilder`/`ArkUINodeAdapterAPI` vtable 与 C-API/NDK 路径共享，C-API 公开层（19 个 `OH_ArkUI_NodeAdapter_*`）为独立 Feat，后续按 5B 增量补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/06-custom-node/06-node-adapter/design.md` | Baselined |
| SDK 声明（动态） | `interface/sdk-js/api/arkui/FrameNode.d.ts`（L3410-3681） | — |
| SDK 声明（静态） | `interface/sdk-js/api/arkui/FrameNode.static.d.ets`（L3616-3821） | — |
| SDK re-export | `interface/sdk-js/api/@ohos.arkui.node.d.ts`、`@ohos.arkui.node.static.d.ets`、`kits/@kit.ArkUI.d.ts` | — |
| TS 运行时 | `frameworks/bridge/declarative_frontend/ark_node/src/node_adapter.ts`（220L） | — |
| TS 消费者（宿主反引用） | `frameworks/bridge/declarative_frontend/ark_node/src/frame_node.ts`（L110, L227-229） | — |
| TS native-module 声明 | `frameworks/bridge/declarative_frontend/ark_node/types/index.d.ts`（L469-483） | — |
| JSI 桥注册 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_api_impl_bridge.cpp`（L601-630） | — |
| JSI 桥实现 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_node_adapter_bridge.{h,cpp}` | — |
| C++ 包装 UINodeAdapter | `frameworks/core/interfaces/native/node/node_adapter_impl.h`（L178-237）/ `.cpp` | — |
| 共享 vtable | `frameworks/core/interfaces/arkoala/arkoala_api.h`（L10518-10559） | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 构造与回调绑定

**作为** ArkTS 开发者,
**我想要** 创建 `NodeAdapter` 并在子类中覆写生命周期回调,
**以便** 引擎按需经回调获取/复用/释放子 FrameNode。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调 `new NodeAdapter()` THEN `createAdapter()` 返回 `NativeStrongRef`，`nativePtr_=nativeRef_.getNativeHandle()`（即 C++ `UINodeAdapter*`），`_isDisposed=false`（`node_adapter.ts:36-47`） | 正常 |
| AC-1.2 | WHEN 构造时执行 `setCallbacks` THEN `onAttachToNodePtr`/`onDetachFromNodePtr`（attach/detach trampoline）**无条件**注册（`node_adapter.ts:39-45`） | 正常 |
| AC-1.3 | WHEN 子类以**方法覆写**（原型链）提供 `onGetChildId/onCreateChild/onDisposeChild/onUpdateChild` 且构造时 `this.onXxx!==undefined` THEN 对应 trampoline 注册（`onGetChildId` 直传用户函数；create/dispose/update 注册 `onCreateNewNodePtr/onDisposeNodePtr/onUpdateNodePtr`）（`node_adapter.ts:41-44`） | 正常 |
| AC-1.4 | WHEN 构造**之后**才赋值实例字段回调（如 `adapter.onCreateChild=...` 或子类实例箭头函数字段）THEN 该回调**未注册**（`setCallbacks` 已执行），引擎取节点时不触发该回调（`node_adapter.ts:36-45`） | 异常 |
| AC-1.5 | WHEN `UINodeAdapter` 构造 THEN 自动 `SetReceiver(lambda)`（单一 C event-receiver）+ `SetNeedUpdateEvent(true)`（`node_adapter_impl.cpp` UINodeAdapter ctor）——receiver 不由 `setCallbacks` 注册 | 边界 |

### US-2: 生命周期（dispose/isDisposed）

**作为** ArkTS 开发者,
**我想要** 显式释放 NodeAdapter 并查询其有效性,
**以便** 避免资源泄漏与 dispose 后误用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调 `dispose()` THEN 依次：`_isDisposed=true`→（`nativePtr_` 存在时）`fireArkUIObjectLifecycleCallback(WeakRef(this),'NodeAdapter',getNodeType()||'NodeAdapter',nativePtr_)`→宿主非空时 `NodeAdapter.detachNodeAdapter(hostNode)`→`nativeRef_.dispose()`→`nativePtr_=null`（`node_adapter.ts:53-65`） | 正常 |
| AC-2.2 | WHEN 调 `isDisposed()` THEN 返回 `_isDisposed && (nativePtr_===undefined || nativePtr_===null)`（`node_adapter.ts:67-69`）；动态版 `@since 20 dynamic`（`FrameNode.d.ts:3680`） | 正常 |
| AC-2.3 | WHEN 已 dispose（`nativePtr_=null`）后调用 mutator/`getAllAvailableItems`/attach 等以 null `nativePtr_` 传入 native THEN 行为未定义，SDK 文档示「可能 crash 或返回默认值」（`FrameNode.d.ts` isDisposed 文档；`node_adapter.ts:64` 置空） | 异常 |
| AC-2.4 | WHEN `getNodeType()` THEN 返回 `nodeAdapter.getNodeType(nativePtr_)`，`dispose` 时作 `getNodeType()||'NodeAdapter'` 回退（`node_adapter.ts:49-51,57`） | 正常 |

### US-3: 计数与查询

**作为** ArkTS 开发者,
**我想要** 设置总节点数并查询当前已实例化子节点,
**以便** 驱动懒渲染并观察缓存状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `totalNodeCount = count`（count≥0） THEN `setTotalNodeCount(nativePtr_,count)` + 缓存 `count_=count`（`node_adapter.ts:71-77`） | 正常 |
| AC-3.2 | WHEN `totalNodeCount = count`（count<0） THEN 直接 `return`，不调 native、不更新缓存（`node_adapter.ts:72-74`） | 边界 |
| AC-3.3 | WHEN `totalNodeCount`（getter） THEN 返回缓存 `count_`（`node_adapter.ts:79-81`） | 正常 |
| AC-3.4 | WHEN `getAllAvailableItems()` THEN `getAllItems(nativePtr_)`→`Array<NodeInfo>`，逐项按 `nodeId` 经 `FrameNodeFinalizationRegisterProxy.ElementIdToOwningFrameNode_.has(nodeId)` 过滤→`deref()` push FrameNode，返回当前已实例化子节点（含预加载）（`node_adapter.ts:115-128`） | 正常 |
| AC-3.5 | WHEN `getAllAvailableItems()` 中某 NodeInfo 的 `nodeId` 在 `ElementIdToOwningFrameNode_` 不存在或 `deref()` 为 undefined THEN 该项被跳过，结果数组可能少于 native 实际持有（`node_adapter.ts:118-125`） | 边界 |

### US-4: 数据变更通知

**作为** ArkTS 开发者,
**我想要** 经 reload/remove/insert/move 通知数据变更,
**以便** 触发懒渲染 diff 更新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `reloadAllItems()` THEN `notifyItemReloaded(nativePtr_)`（`node_adapter.ts:83-85`） | 正常 |
| AC-4.2 | WHEN `reloadItem(start,count)`（start≥0 且 count≥0） THEN `notifyItemChanged(nativePtr_,start,count)`（`node_adapter.ts:87-92`） | 正常 |
| AC-4.3 | WHEN `reloadItem/removeItem/insertItem(start,count)` 任一 <0 THEN 直接 `return`（`node_adapter.ts:88,95,102`） | 边界 |
| AC-4.4 | WHEN `removeItem(start,count)` THEN `notifyItemRemoved`（`node_adapter.ts:94-99`）；`insertItem(start,count)` THEN `notifyItemInserted`（`node_adapter.ts:101-106`） | 正常 |
| AC-4.5 | WHEN `moveItem(from,to)`（from≥0 且 to≥0） THEN `notifyItemMoved(nativePtr_,from,to)`（`node_adapter.ts:108-113`） | 正常 |
| AC-4.6 | WHEN `moveItem(from,to)` 任一 <0 THEN 直接 `return`（`node_adapter.ts:109`） | 边界 |

### US-5: 6 生命周期回调与事件分发

**作为** ArkTS 开发者,
**我想要** 在回调中创建/复用/释放子 FrameNode 并生成唯一 id,
**以便** 引擎管理懒渲染节点生命周期。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 引擎取新节点（cache miss）触发 `onCreateNewNodePtr(index)` THEN user `onCreateChild(index)`→FrameNode，去重 push `nodeRefs_`，返 `node.getNodePtr()`；无回调返 `null`（`node_adapter.ts:159-168`） | 正常 |
| AC-5.2 | WHEN 节点复用（cache hit，`needUpdateEvent_=true`）触发 `ON_UPDATE_NODE`→`onUpdateNodePtr(id,node)` THEN 反查 FrameNode，user `onUpdateChild(id,frameNode)`（`node_adapter.ts:184-192`）——TS 路径独有，raw C-API 不触发 | 边界 |
| AC-5.3 | WHEN 节点将被回收触发 `onDisposeNodePtr(id,node)` THEN 反查 FrameNode，user `onDisposeChild(id,frameNode)`，从 `nodeRefs_` 移除（`node_adapter.ts:170-182`） | 正常 |
| AC-5.4 | WHEN `onGetChildId(index)` 被引擎调用（经直传函数） THEN 返回 user 自定义 id，须保证跨 index 唯一（`FrameNode.d.ts:3587`；`node_adapter.ts:41`） | 正常 |
| AC-5.5 | WHEN attach 成功触发 `onAttachToNodePtr(target)` THEN 按 `target.nodeId` 反查 FrameNode（`deref()` undefined 则 return），`frameNode.setAdapterRef(this)`+`attachedNodeRef_=WeakRef(frameNode)`，再触发 user `onAttachToNode(frameNode)`（`node_adapter.ts:130-143`） | 正常 |
| AC-5.6 | WHEN detach 触发 `onDetachFromNodePtr()` THEN user `onDetachFromNode()`→清宿主 `setAdapterRef(undefined)`→`nodeRefs_.splice(0,length)` 清空（`node_adapter.ts:145-157`） | 正常 |

### US-6: 宿主绑定（static attach/detach）

**作为** ArkTS 开发者,
**我想要** 将 NodeAdapter 静态绑定到宿主 FrameNode 容器,
**以便** 启动懒渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `NodeAdapter.attachNodeAdapter(adapter,node)` 且 `node==null/undefined` THEN 返回 false（`node_adapter.ts:194-197`） | 异常 |
| AC-6.2 | WHEN `!node.isModifiable()` THEN 返回 false（`node_adapter.ts:198-200`） | 异常 |
| AC-6.3 | WHEN node 为 `TypedFrameNode` 且 `attribute_.allowChildCount()` 定义且 `<=1` THEN 返回 false（`node_adapter.ts:201-210`） | 异常 |
| AC-6.4 | WHEN 通过预校验 THEN 返回 `nodeAdapter.attachNodeAdapter(adapter.nativePtr_,node.getNodePtr())`（native `attachHostNode` 结果）（`node_adapter.ts:211`）；每个节点仅可绑定一个 NodeAdapter，已绑定再绑返回 false（`FrameNode.d.ts` attach 文档） | 正常 |
| AC-6.5 | WHEN 可绑定容器为 Column/Row/Stack/GridRow/Flex/Swiper/RelativeContainer/List/ListItemGroup/WaterFlow/Grid（11 个白名单） THEN 允许 attach；其余容器 native 侧失败返回 false（`FrameNode.d.ts` attach 文档 L3652） | 边界 |
| AC-6.6 | WHEN `NodeAdapter.detachNodeAdapter(node)`（node 非空） THEN `nodeAdapter.detachNodeAdapter(node.getNodePtr())`，native `detachHostNode`+`markDirty(MEASURE_SELF_AND_PARENT)`（`node_adapter.ts:214-219`）；node 为 null 直接 return | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.5 | R-1,R-2,R-9 | T-1 | TS UT（Mock getUINativeModule().nodeAdapter） | `node_adapter.ts:36-47`；`node_adapter_impl.cpp` UINodeAdapter ctor |
| AC-2.1~2.4 | R-3,R-10,R-11 | T-1 | TS UT | `node_adapter.ts:49-69`；`FrameNode.d.ts:3680` |
| AC-3.1~3.5 | R-4,R-5,R-12 | T-1 | TS UT | `node_adapter.ts:71-81,115-128` |
| AC-4.1~4.6 | R-6,R-7 | T-1 | TS UT | `node_adapter.ts:83-113` |
| AC-5.1~5.6 | R-8,R-9,R-13,R-14 | T-1 | TS UT | `node_adapter.ts:130-192`；`node_adapter_impl.cpp` OnEventReceived |
| AC-6.1~6.6 | R-15,R-16,R-17 | T-1 | TS UT + XTS（真实容器） | `node_adapter.ts:194-219`；`FrameNode.d.ts:3652-3664` |

## 规则定义

> 统一规则表，类型标签：行为/边界/异常/恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `new NodeAdapter()` | `createAdapter()`→`nativePtr_=UINodeAdapter*`；`_isDisposed=false` | `nativePtr_` 非 raw handle | AC-1.1 |
| R-2 | 行为 | 构造 `setCallbacks` | attach/detach trampoline 无条件注册；getId/create/dispose/update 仅构造时 `!==undefined` 注册 | 子类方法覆写生效，构造后赋值不生效 | AC-1.2,AC-1.3,AC-1.4 |
| R-3 | 行为 | `dispose()` | `_isDisposed=true`→fire 生命周期回调→detach 宿主→`nativeRef_.dispose()`→`nativePtr_=null` | 顺序固定；先解绑宿主 | AC-2.1 |
| R-4 | 行为 | `totalNodeCount` setter（count≥0） | `setTotalNodeCount`+缓存 `count_` | count∈[0,+∞) | AC-3.1 |
| R-5 | 边界 | `totalNodeCount` setter（count<0） | 静默 return，不调 native、不更新缓存 | 负数忽略 | AC-3.2 |
| R-6 | 行为 | `reloadAllItems()`/`reloadItem`/`removeItem`/`insertItem`/`moveItem`（参数≥0） | 转发 `notifyItem*` | start/count/from/to∈[0,+∞) | AC-4.1,AC-4.2,AC-4.4,AC-4.5 |
| R-7 | 边界 | 上述 mutator 任一参数 <0 | 静默 return，无异常/无错误码 | 类级 NOTE「Negative input parameters are ignored」 | AC-4.3,AC-4.6 |
| R-8 | 行为 | 引擎 cache miss | `onCreateChild(index)`→FrameNode，push `nodeRefs_`，返 `node.getNodePtr()` | 无回调返 null | AC-5.1 |
| R-9 | 边界 | cache hit（`needUpdateEvent_=true`） | `ON_UPDATE_NODE`→`onUpdateChild`（TS 路径独有） | raw C-API 不触发 | AC-1.5,AC-5.2 |
| R-10 | 行为 | `isDisposed()` | 返 `_isDisposed && nativePtr_==null` | 动态 `@since 20 dynamic` | AC-2.2 |
| R-11 | 异常 | dispose 后调用其他 API（nativePtr_ 为 null） | 行为未定义，可能 crash/默认值 | 用 `isDisposed()` 前置校验 | AC-2.3 |
| R-12 | 行为 | `getAllAvailableItems()` | 返回 `getAllItems` 中 nodeId 可反查的 FrameNode（含预加载） | 不可反查项被跳过 | AC-3.4,AC-3.5 |
| R-13 | 行为 | 节点回收 | `onDisposeChild(id,node)`+从 `nodeRefs_` 移除 | FrameNode deref undefined 时跳过 | AC-5.3 |
| R-14 | 行为 | `onGetChildId(index)` | 返 user 自定义 id，须跨 index 唯一 | id 冲突由用户负责 | AC-5.4 |
| R-15 | 异常 | `attachNodeAdapter` node null/`!isModifiable()`/`allowChildCount()<=1` | 返回 false（TS 预校验，未达 native） | TypedFrameNode 才查 allowChildCount | AC-6.1,AC-6.2,AC-6.3 |
| R-16 | 行为 | attach 通过预校验 | 返回 native `attachHostNode` 结果（true/false） | 每节点仅绑一个 adapter | AC-6.4 |
| R-17 | 边界 | attach 宿主为白名单 11 容器 | 允许；非白名单 native 失败返 false | Column/Row/Stack/GridRow/Flex/Swiper/RelativeContainer/List/ListItemGroup/WaterFlow/Grid | AC-6.5,AC-6.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | 构造与回调绑定（US-1） | TS UT（Mock nodeAdapter 模块） | createAdapter 返回值、setCallbacks 8 参数、trampoline 注册条件 |
| VM-2 | dispose/isDisposed（US-2） | TS UT | dispose 调用顺序、nativePtr_ 置空、isDisposed 双条件 |
| VM-3 | 计数与查询（US-3） | TS UT | count<0 守卫、getAllAvailableItems 反查过滤 |
| VM-4 | 数据变更（US-4） | TS UT | 负参 return、notifyItem* 转发 |
| VM-5 | 回调与事件流（US-5） | TS UT + XTS | onCreate/onUpdate（needUpdateEvent）/onDispose/nodeRefs_ 维护 |
| VM-6 | attach/detach（US-6） | TS UT + XTS（真实容器） | 预校验三源 false、容器白名单、detach markDirty |

## API 变更分析

> 存量补录，无新增/变更/废弃。API 已与 `interface/sdk-js/api/` 权威 `.d.ts`/`.static.d.ets` 交叉核对。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---------|---------|---------|--------|----------|---------|--------|
| `constructor()` | Public | 无 | `NodeAdapter` | 无 | 创建 adapter，建 native handle + 绑定回调（`FrameNode.d.ts:3435`） | AC-1.1~1.4 |
| `dispose(): void` | Public | 无 | void | 无 | 释放 adapter，先解绑宿主（`FrameNode.d.ts:3447`） | AC-2.1 |
| `isDisposed(): boolean` | Public | 无 | boolean | 无 | 是否已释放（动态 `@since 20 dynamic`，`FrameNode.d.ts:3680`） | AC-2.2,AC-2.3 |
| `set/get totalNodeCount` | Public | `count: number` | `number` | 无 | 总节点数（`FrameNode.d.ts:3459,3471`） | AC-3.1~3.3 |
| `reloadAllItems(): void` | Public | 无 | void | 无 | 全量重载（`FrameNode.d.ts:3483`） | AC-4.1 |
| `reloadItem(start,count)` | Public | `start,count: number` | void | 无 | 范围重载（`FrameNode.d.ts:3496`） | AC-4.2,AC-4.3 |
| `removeItem(start,count)` | Public | `start,count: number` | void | 无 | 范围删除（`FrameNode.d.ts:3509`） | AC-4.3,AC-4.4 |
| `insertItem(start,count)` | Public | `start,count: number` | void | 无 | 范围插入（`FrameNode.d.ts:3522`） | AC-4.3,AC-4.4 |
| `moveItem(from,to)` | Public | `from,to: number` | void | 无 | 移动（`FrameNode.d.ts:3535`） | AC-4.5,AC-4.6 |
| `getAllAvailableItems()` | Public | 无 | `Array<FrameNode>` | 无 | 当前已实例化子节点（`FrameNode.d.ts:3550`） | AC-3.4,AC-3.5 |
| `onAttachToNode?(target)` | Public | `target: FrameNode` | void | 无 | 绑定回调（可选，`FrameNode.d.ts:3562`） | AC-5.5 |
| `onDetachFromNode?()` | Public | 无 | void | 无 | 解绑回调（可选，`FrameNode.d.ts:3573`） | AC-5.6 |
| `onGetChildId?(index)` | Public | `index: number` | `number` | 无 | 自定义 id（可选，`FrameNode.d.ts:3587`） | AC-5.4 |
| `onCreateChild?(index)` | Public | `index: number` | `FrameNode` | 无 | 创建子节点（可选，`FrameNode.d.ts:3603`） | AC-5.1 |
| `onDisposeChild?(id,node)` | Public | `id: number,node: FrameNode` | void | 无 | 回收子节点（可选，`FrameNode.d.ts:3617`） | AC-5.3 |
| `onUpdateChild?(id,node)` | Public | `id: number,node: FrameNode` | void | 无 | 复用子节点（可选，`FrameNode.d.ts:3631`） | AC-5.2 |
| `static attachNodeAdapter(adapter,node)` | Public | `adapter: NodeAdapter,node: FrameNode` | `boolean` | 无 | 绑定宿主（`FrameNode.d.ts:3652`） | AC-6.1~6.5 |
| `static detachNodeAdapter(node)` | Public | `node: FrameNode` | void | 无 | 解绑宿主（`FrameNode.d.ts:3664`） | AC-6.6 |

### 变更/废弃 API

无。

> SDK 权威声明：动态 `interface/sdk-js/api/arkui/FrameNode.d.ts`（L3410-3681）；静态 `interface/sdk-js/api/arkui/FrameNode.static.d.ets`（L3616-3821）。源码与 SDK 一致，无偏差。

## 接口规格

### 接口定义

**NodeAdapter（动态版，`@since 12 dynamic`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `declare class NodeAdapter`（`FrameNode.d.ts:3424`），含 19 成员 |
| 返回值 | 见各方法 |
| 开放范围 | Public |
| 错误码 | 无（TS 侧负参静默忽略；native no-listener 错误码 106104 属 C-API 路径） |
| 关联 AC | AC-1.1~6.6 |

**参数约束（动态版核心 API）**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `totalNodeCount.count` | number | 是 | — | `[0,+∞)`；<0 静默忽略 |
| `reloadItem.start`/`.count` | number | 是 | — | `[0,+∞)`；任一 <0 静默忽略 |
| `removeItem.start`/`.count` | number | 是 | — | 同上 |
| `insertItem.start`/`.count` | number | 是 | — | 同上 |
| `moveItem.from`/`.to` | number | 是 | — | `[0,+∞)`；任一 <0 静默忽略 |
| `onGetChildId.index` | number | 是 | — | `[0,+∞)`；返回 id 须跨 index 唯一 |
| `onCreateChild.index` | number | 是 | — | `[0,+∞)`；返回 FrameNode 须为用户创建 |
| `attachNodeAdapter.adapter` | NodeAdapter | 是 | — | 非 null |
| `attachNodeAdapter.node` | FrameNode | 是 | — | 非 null、`isModifiable()`、白名单容器、未绑定 |

**行为场景（动态版）**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `new NodeAdapter()` 后子类方法覆写 6 回调 | 构造时绑定 trampoline，引擎按需触发回调 | AC-1.1~1.3 |
| 2 | 构造后 `adapter.onCreateChild=fn` 赋值 | 回调未注册，不触发 | AC-1.4 |
| 3 | `dispose()` | 解绑宿主 + 释放 native + nativePtr_ 置空 | AC-2.1 |
| 4 | dispose 后调 mutator | 行为未定义，可能 crash | AC-2.3 |
| 5 | `reloadItem(-1,2)` | 静默 return，无错误 | AC-4.3 |
| 6 | `attachNodeAdapter` 到非白名单容器 | TS 通过预校验但 native 失败返 false | AC-6.5 |
| 7 | cache hit 复用节点 | `onUpdateChild` 触发（TS 独有） | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态 `@since 12 dynamic`；静态 `@since 23 static`。
- **API 版本号策略:** 动态版成员 `@since 12 dynamic`，`isDisposed()` 为 `@since 20 dynamic`（后增，API<20 动态版无此 API）；静态版全部 `@since 23 static`。

**动态版 vs 静态版差异（静态版作兼容性变体）**

| 维度 | 动态版（`FrameNode.d.ts`） | 静态版（`FrameNode.static.d.ets`） |
|------|--------------------------|----------------------------------|
| since | `@since 12 dynamic`（`isDisposed` @since 20） | `@since 23 static`（全部，含 isDisposed） |
| 数值类型 | `number` | `int` |
| 回调可空性 | 6 回调可选（`?`） | 6 回调必填（无 `?`） |
| `@crossplatform`/`@atomicservice` | 有 | 无（仅 `@syscap`+`@stagemodelonly`） |
| re-export | `@ohos.arkui.node`（`@ohos.arkui.node.d.ts:128`） | `@ohos.arkui.node.static`（`@ohos.arkui.node.static.d.ets:69`） |

> 静态版（@since 23）运行时位于 `frameworks/bridge/arkts_frontend/`（arkoala 生成路径），本 Feat 未深入探查其运行时实现（RISK-7）；行为差异以上述 SDK 声明差异为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 单一 class 无 Controller | 公开仅 `NodeAdapter`，无 `NodeAdapterController`/无公开 `UINodeAdapter`/`NodeInfo`（内部） | AC-1.1 |
| 回调构造时绑定 | 4 个可选回调（getId/create/dispose/update）须构造时已定义 | AC-1.2~1.4 |
| 复用 LazyForEach 管线 | 经 UINodeAdapter→NativeLazyForEachBuilder 接入 07-05-02 管线 | AC-5.1~5.3 |
| `needUpdateEvent_=true` | TS 路径触发 ON_UPDATE_NODE→onUpdateChild | AC-5.2 |
| TS 预校验在 native 前 | attach 三源 false 在 JS 侧判定 | AC-6.1~6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 懒渲染按需实例化，首屏仅创建可见+预加载节点（cachedCount） | XTS 帧率/内存 | `FrameNode.d.ts:3550` getAllAvailableItems 文档 |
| 内存 | `nodeRefs_` 强引用已创建子节点防 GC；detach 时清空 | 内存测试 | `node_adapter.ts:24,156,163,178` |
| 安全 | Public 无权限；用户回调内创建的 FrameNode 受容器子组件约束（如 WaterFlow 仅 FlowItem） | 代码评审 | `FrameNode.d.ts:3603` onCreateChild 文档 |
| 可靠性 | dispose 顺序保证先解绑宿主；`isDisposed()` 提供 dispose 后前置校验 | UT | `node_adapter.ts:53-69` |
| 可测试性 | TS 行为可经 Mock `getUINativeModule().nodeAdapter` 单测 | TS UT | `node_adapter.ts` 全篇 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机/平板/折叠屏 | 无差异（`@crossplatform`） | 子节点布局随父容器 | XTS | `FrameNode.d.ts` 类级 `@crossplatform` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 否（透传） | 子节点无障碍由各自 FrameNode 承担 | — |
| 大字体 | 否（透传） | 随子节点/父容器 | — |
| 深色模式 | 否（透传） | 随子节点 | — |
| 多窗口/分屏 | 否 | NodeAdapter 行为与窗口无关 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | `isDisposed()` 动态 `@since 20`；静态版 `@since 23` | 兼容性声明 |
| 生态兼容 | 是 | 跨范式：动态（Declarative Frontend）/静态（ArkTS Frontend）/C-API（后续 Feat）共用 vtable | design.md ADR-1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: NodeAdapter ArkTS 前端
  作为 ArkTS 开发者
  我想要 用 NodeAdapter 实现懒渲染列表
  以便 高效渲染大量 FrameNode

  Scenario: 子类方法覆写回调正常触发
    Given 一个继承 NodeAdapter 的子类 MyAdapter，覆写 onCreateChild/onGetChildId/onDisposeChild/onUpdateChild 方法
    When 调用 new MyAdapter()
    Then setCallbacks 在构造时绑定 4 个 trampoline
    And 引擎取节点时 onCreateChild/onGetChildId 正常触发

  Scenario: 构造后赋值回调不生效
    Given const adapter = new NodeAdapter()
    When 构造后执行 adapter.onCreateChild = (index) => node
    Then onCreateChild 未注册（setCallbacks 已执行）
    And 引擎取节点时不触发该回调

  Scenario Outline: 负数入参静默忽略
    When 调用 <method>(<args>)
    Then 直接 return，无异常、无错误码、不调 native
    Examples:
      | method | args |
      | totalNodeCount setter | -1 |
      | reloadItem | -1, 2 |
      | removeItem | 0, -1 |
      | moveItem | -1, 0 |

  Scenario: dispose 顺序与有效性
    Given 已 attach 宿主的 NodeAdapter
    When 调用 dispose()
    Then 依次 _isDisposed=true、fire 生命周期回调、detach 宿主、nativeRef_.dispose()、nativePtr_=null
    And isDisposed() 返回 true

  Scenario: attach 到非白名单容器
    Given 一个非白名单容器 FrameNode
    When 调用 NodeAdapter.attachNodeAdapter(adapter, node)
    Then 通过 TS 预校验但 native attachHostNode 返回 false

  Scenario: 复用节点触发 onUpdateChild（TS 独有）
    Given 已绑定 NodeAdapter 且某缓存节点 key 命中
    When 引擎复用该节点
    Then 因 needUpdateEvent_=true 触发 ON_UPDATE_NODE
    And onUpdateChild(id, node) 被调用
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（TS 侧；C-API 公开层、LazyForEach 管线为复用/后续 Feat）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeAdapter ArkTS 前端运行时 node_adapter.ts 的回调注册时机与 native trampoline 事件分发"
  - repo: "openharmony/arkui_ace_engine"
    query: "NodeAdapterBridge JSI 桥 createAdapter/setCallbacks/attachHostNode 的 JS↔C marshalling"
  - repo: "openharmony/arkui_ace_engine"
    query: "UINodeAdapter C++ 包装 needUpdateEvent 与 ON_UPDATE_NODE 事件路由"
  - repo: "openharmony/interface_sdk-js"
    query: "NodeAdapter 公开 class 在 FrameNode.d.ts / FrameNode.static.d.ets 的动态/静态声明差异"
```

**关键文档：** `interface/sdk-js/api/arkui/FrameNode.d.ts`（L3410-3681）、`interface/sdk-js/api/arkui/FrameNode.static.d.ets`（L3616-3821）、`frameworks/bridge/declarative_frontend/ark_node/src/node_adapter.ts`
