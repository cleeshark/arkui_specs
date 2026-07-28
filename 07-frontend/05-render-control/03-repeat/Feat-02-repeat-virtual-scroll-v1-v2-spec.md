# 特性规格

> Func-07-05-03-Feat-02 Repeat 虚拟滚动（v2；v1 已废弃）：固化 `virtualScroll(VirtualScrollOptions)`（totalCount `@since12`/reusable `@since18`/onLazyLoading·onTotalCount `@since19`/disableVirtualScroll static-only `@since23`）与 **v2 RepeatVirtualScroll2Node（RID 缓存，master 动态路径）** 的按需生成/活跃区间/cachedCount/recycle/pre-build、sync-load、API18 FreezeSpareNode 门控行为规格。

> **⚠️ 废弃声明（v1）：** `RepeatVirtualScrollNode`（v1，key+ttype 缓存，原 API≤15 兼容实现）**已废弃**。v1 源码（`repeat_virtual_scroll_node.*`/`repeat_virtual_scroll_caches.*`/`repeat_virtual_scroll_model*`/`js_repeat_virtual_scroll.cpp`/`pu_repeat_virtual_scroll_impl.ts`）当前仍保留于代码库并被部分生产 Pattern 引用，但**不再演进**，master 动态路径经 `pu_repeat.ts:291` **始终实例化 v2**（`__RepeatVirtualScroll2Impl`）。本规格不再展开 v1 的详细行为（AC/规则/数据模型），仅保留此废弃声明与兼容性/风险条目（RISK-F2-3）。v1 的历史行为详见代码与历史规格版本。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Repeat 虚拟滚动（v2；v1 已废弃） |
| 特性编号 | Func-07-05-03-Feat-02 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since12`（virtualScroll/totalCount）/ `@since18`（reusable）/ `@since19`（onLazyLoading/onTotalCount）；static `@since23`（含 disableVirtualScroll static-only）；v2=master 动态路径（memoryOptimizationStrategy `@since26` 见 Feat-04）；v1 已废弃（代码保留不演进） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01（核心语法与非虚拟渲染）；本特性聚焦虚拟滚动（v2）。模板化渲染（Feat-03）、内存优化（Feat-04）由后续 Feat 承接。**v1 已废弃，详见顶部废弃声明。**

> **关键澄清：** master 动态路径经 `pu_repeat.ts:291` **始终实例化 v2**（`__RepeatVirtualScroll2Impl`）；v1 为历史 API≤15 兼容实现，经独立前端桥接（`js_view_register_impl.cpp:498-499` 双注册 `RepeatVirtualScrollNative`/`RepeatVirtualScroll2Native`）保留，现已废弃、不再演进。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/03-repeat/design.md` | Baselined |
| Dynamic API | `interface/sdk-js/api/@internal/component/ets/repeat.d.ts` | — |
| Static API | `interface/sdk-js/api/arkui/component/repeat.static.d.ets` | — |
| TS 路由/驱动（v2） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_repeat.ts`（:291 路由）、`pu_repeat_virtual_scroll_2_impl.ts`（v2） | — |
| 桥接注册 | `frameworks/bridge/declarative_frontend/engine/jsi/js_view_register_impl.cpp` | — |
| v2 JS/Model/Node/Cache | `js_repeat_virtual_scroll_2.cpp`、`repeat_virtual_scroll_2_model_ng.cpp`、`repeat_virtual_scroll_2_node.cpp/.h`、`repeat_virtual_scroll_2_caches.cpp/.h` | — |
| v1（已废弃，仅留存） | `repeat_virtual_scroll_node.*`、`repeat_virtual_scroll_caches.*`、`repeat_virtual_scroll_model*`、`js_repeat_virtual_scroll.cpp`、`pu_repeat_virtual_scroll_impl.ts` | **已废弃** |

> 需求基线详见 proposal.md。design.md 与本文档增量合并，互不依赖。

---

## 用户故事

### US-1: virtualScroll 与 VirtualScrollOptions

**作为** 应用开发者,
**我想要** 用 `.virtualScroll(options)` 开启虚拟滚动并提供 totalCount/reusable/onLazyLoading 等,
**以便** 大数据量场景按需构建+回收子节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 链式调用 `.virtualScroll(options?)`（dynamic `@since12` `repeat.d.ts:378`/static `:249` `@since23`）THEN 开启虚拟滚动路径；`pu_repeat.ts:280-293` 检测 `isVirtualScroll` 并实例化 `__RepeatVirtualScroll2Impl`（master 动态路径**始终 v2**，`:291`） | 正常 |
| AC-1.2 | WHEN `VirtualScrollOptions.totalCount` 提供 THEN 用其作总长度（dynamic `repeat.d.ts:136` `@since12`/static `:138` `@since23`，number/int） | 正常 |
| AC-1.3 | WHEN `VirtualScrollOptions.reusable` 提供（`@since18`，默认 true）THEN 控制节点复用；`reusable=false` 时各模板 cachedCount 强制 0（v2 `pu_repeat_virtual_scroll_2_impl.ts:516-519`） | 正常 |
| AC-1.4 | WHEN `VirtualScrollOptions.onLazyLoading(index)` 注册（`@since19` dynamic `:183`/static `:157`）THEN 滚动到该 index 触发懒加载回调 | 正常 |
| AC-1.5 | WHEN `VirtualScrollOptions.onTotalCount()` 注册（`@since19` dynamic `:219`/static `:166`）THEN 框架调用获取总长度（动态总数场景） | 正常 |
| AC-1.6 | WHEN static 范式设 `VirtualScrollOptions.disableVirtualScroll=true`（static-only `repeat.static.d.ets:176` `@since23`，默认 false）THEN 禁用虚拟滚动；**dynamic 无此字段** | 边界 |

### US-2: v2 虚拟滚动（RID 缓存，master 动态路径）

**作为** 应用开发者（master 路径）,
**我想要** v2 按 RID 缓存、TS 侧决定新建/复用,
**以便** 更灵活的复用匹配与内存控制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN v2 `GetFrameChild(index,needBuild)`（`repeat_virtual_scroll_2_caches.cpp:50-68`）THEN `ConvertFromToIndex`（drag 映射 `:54`）→`GetL1CacheItem4Index`（`:55`）命中返回 `UNCHANGED_NODE`；`!needBuild` 返回 `NO_NODE`；否则 `CallOnGetRid4Index`（`:64`） | 正常 |
| AC-2.2 | WHEN v2 `CallOnGetRid4Index`（`caches.cpp:273-308`）THEN 调 TS `onGetRid4Index_(index,IsImplicitAnimationOpen(),false)`（`:283`）；`CREATED_NEW_NODE`→`GetNewRid4Index`（`:310-329`，设 `l1Rid4Index_[index]=rid`+`cacheItem4Rid_[rid]=MakeCacheItem(isL1=true)`）；`UPDATED_NODE`→`GetUpdatedRid4Index`（`:331-355`，复用既有 RID） | 正常 |
| AC-2.3 | WHEN v2 缓存结构 THEN `cacheItem4Rid_`（RID→CacheItem{node_,isL1_,isActive_,isOnRenderTree_}，`caches.h:316`）、`l1Rid4Index_`（index→RID，`:313`）、`moveFromTo_`（drag，`:329`）；`RIDType=uint32_t`/`IndexType=int32_t`（`:115-116`） | 正常 |
| AC-2.4 | WHEN v2 `SetInvalid(rid)`（`caches.cpp:170-174`）THEN 仅 `DropFromL1ByRid`（L1→L2，保留节点于 `cacheItem4Rid_`，标记 not-L1）——**不删除** | 正常 |
| AC-2.5 | WHEN v2 `RemoveNode(rid)`（`caches.cpp:153-163`）THEN `DropFromL1ByRid`+`cacheItem4Rid_.erase(rid)`——**完全删除** | 正常 |
| AC-2.6 | WHEN v2 TS 决定复用匹配 THEN ttype/key 匹配在 **TS 侧**（`canUpdateTryMatch`，`pu_repeat_virtual_scroll_2_impl.ts:30-37`），C++ 仅存 RID→node+L1 成员标志 | 正常 |
| AC-2.7 | WHEN v2 TS 驱动回调 THEN 注册 `{onGetRid4Index,onRecycleItems,onActiveRange,onMoveFromTo,onPurge,onPurgeAll,onUpdateDirty}`（`pu_repeat_virtual_scroll_2_impl.ts:532-540`，`RepeatVirtualScroll2Native.create(arrLen,totalCount,memOptStrategy,handlers)`） | 正常 |

### US-3: 活跃区间 / cachedCount / recycle / pre-build（v2）

**作为** 应用开发者,
**我想要** 父容器驱动活跃区间、cachedCount 控制预缓存、离屏节点回收,
**以便** 滚动流畅且内存可控。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 父容器调 `DoSetActiveChildRange(start,end,cacheStart,cacheEnd,showCache)` THEN v2（`repeat_virtual_scroll_2_node.cpp:105-153`）规范化区间；`showCache=true` 把 cache 折入活跃窗口（`:108-114`） | 正常 |
| AC-3.2 | WHEN `reusable=false` THEN v2 置 `allowUpdate_=config.reusable`（`:491`）+强制模板 cachedCount=0（`:516-519`） | 边界 |
| AC-3.3 | WHEN TemplateOptions.cachedCount 提供（dynamic `repeat.d.ts:276`/static `:204` `@since12/23`）THEN v2 TS 侧 `templateOptions_`，`onPurge` 经 `availableCachedCount`（`:1749-1752`）/`getCachedCountByType`（`:1027-1029`）约束 | 正常 |
| AC-3.4 | WHEN v2 模板 cachedCount 未指定 THEN `onActiveRange` 提升 `cachedCount=max(numberOfActiveItems,cachedCount)`（`pu_repeat_virtual_scroll_2_impl.ts:1462-1469`）——动态 cachedCount | 边界 |
| AC-3.5 | WHEN 离屏回收 THEN v2 `RecycleItems`（`:648-669`）记 `prevRecycleFrom_/To_`，L1→L2 在 `RebuildL1+ProcessActiveL2Nodes`，TS 侧经 `onRecycleItems`/`SetInvalid`（`caches.cpp:170-174`） | 正常 |
| AC-3.6 | WHEN 帧间预构建 THEN v2 `PostIdleTask`（`:769-809`）→`GetChildren()`→（`!CheckIsSyncLoad()` 则重投 `:788-790`）→`RestoreCache(deadline)`（`:792`）→`Purge()`（`:794`）→[API≥18]`FreezeSpareNode()`（`:795-797`）→`RemovingExpiringItem(deadline)`（`:800`） | 正常 |
| AC-3.7 | WHEN 数据/rerender 变更 THEN v2 `RequestContainerReLayout`（`:448-451`）`MarkNeedSyncRenderTree(true)`+`MarkNeedFrameFlushDirty(PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT|BY_CHILD_REQUEST)`（+`ChildrenUpdatedFrom`） | 正常 |
| AC-3.8 | WHEN 仅活跃区间变更（无数据变更）THEN v2 `RequestSyncTree()`（`:140,358`） | 边界 |

### US-4: sync-load（v2）与 API18 FreezeSpareNode

**作为** 应用开发者,
**我想要** v2 同步加载保证布局期子树就绪、API≥18 离屏 spare 节点冻结,
**以便** 布局稳定且离屏节点不消耗无效活跃观察。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN v2 sync-load 默认开启（`enableSyncLoad_=true`/`isSyncLoad_=true`，`caches.h:338-339`）THEN `CheckIsSyncLoad()`（`caches.cpp:603-606`）返回 true，`PostIdleTask` 继续 restore/purge | 正常 |
| AC-4.2 | WHEN sync-load 关闭（async）THEN `PostIdleTask`（`node.cpp:788`）`!CheckIsSyncLoad()` 重投延迟；`ProcessSyncLoadTempChildren`（`caches.cpp:576-592`，仅 async 模式 `:579`）从 `syncLoadCache_` 为可见窗口补齐 temp 子节点 | 边界 |
| AC-4.3 | WHEN L1 变更 THEN `UpdateL1Rid4Index`（`node.cpp:423`）后 `OrganizeSyncLoadCache`（`caches.cpp:594-601`，仅 `enableSyncLoad_==true` `:596`）从当前 L1 重建 `syncLoadCache_`（index→WeakPtr）——同步快照刷新 | 正常 |
| AC-4.4 | WHEN API≥18 且预构建完成 THEN `PostIdleTask` 内 `node->FreezeSpareNode()`（`node.cpp:795`，`GreatOrEqualAPITargetVersion(VERSION_EIGHTEEN)` 门控）；`FreezeSpareNode`（`:811-824`）对非 L1（spare/L2）CacheItem 调 `SetJSViewActive(false)` 冻结 JS-view 生命周期 | 正常 |
| AC-4.5 | WHEN API<18 THEN 不调 `FreezeSpareNode`，spare 节点不以此方式冻结 | 边界 |
| AC-4.6 | WHEN 容器 toggle sync-load THEN 经基类 `ForEachBaseNode::SetEnableSyncLoad/SetIsSyncLoad`（`for_each_base_node.h:97-98` 虚 no-op）→ v2 覆写（`node.cpp:1021-1029`）转发 `caches_` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.6 | R-1,R-2,R-9 | T-2 | UT + SDK 比对 | `repeat.d.ts:102-230`、`pu_repeat.ts:280-293` |
| AC-2.1~2.7 | R-3,R-4,R-5 | T-2 | UT：v2 caches GetFrameChild/CallOnGetRid4Index/SetInvalid/RemoveNode | `repeat_virtual_scroll_2_caches.cpp:50-355` |
| AC-3.1~3.8 | R-6,R-7,R-8 | T-2 | UT：DoSetActiveChildRange/RecycleItems/PostIdleTask/PROPERTY_UPDATE | `repeat_virtual_scroll_2_node.cpp:105-153,448-451,648-809` |
| AC-4.1~4.6 | R-10,R-11 | T-2 | UT：sync-load + API18 FreezeSpareNode | `repeat_virtual_scroll_2_caches.cpp:563-606`、`repeat_virtual_scroll_2_node.cpp:795-824` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `.virtualScroll(options?)` | 开启虚拟滚动；master 动态路径始终 v2（`pu_repeat.ts:291`） | v1 已废弃（见废弃声明） | AC-1.1 |
| R-2 | 行为 | VirtualScrollOptions 字段 | totalCount/reusable/onLazyLoading/onTotalCount 各 @since；disableVirtualScroll static-only | reusable 默认 true | AC-1.2~1.6 |
| R-3 | 行为 | v2 GetFrameChild | L1 命中 UNCHANGED；!needBuild NO_NODE；否则 CallOnGetRid4Index | drag 经 ConvertFromToIndex | AC-2.1 |
| R-4 | 行为 | v2 CallOnGetRid4Index | TS 返回 CREATED_NEW_NODE/UPDATED_NODE；C++ 存 RID→CacheItem+L1 标志 | ttype 匹配在 TS 侧 | AC-2.2,AC-2.6 |
| R-5 | 边界 | v2 SetInvalid vs RemoveNode | SetInvalid=L1→L2 保留；RemoveNode=完全删除 | — | AC-2.4,AC-2.5 |
| R-6 | 行为 | DoSetActiveChildRange | 规范化区间；showCache 折入；reusable=false 强制 cachedCount=0 | — | AC-3.1,AC-3.2 |
| R-7 | 行为 | TemplateOptions.cachedCount | v2 TS 约束；未指定则动态 max | — | AC-3.3,AC-3.4 |
| R-8 | 行为 | 数据/rerender 变更 | MEASURE_SELF_AND_PARENT\|BY_CHILD_REQUEST+MarkNeedSyncRenderTree(true)；仅区间变更用 RequestSyncTree | — | AC-3.7,AC-3.8 |
| R-9 | 边界 | disableVirtualScroll | static-only @since23，dynamic 无 | 默认 false | AC-1.6 |
| R-10 | 行为 | v2 sync-load 默认开 | OrganizeSyncLoadCache 刷新快照；async 经 ProcessSyncLoadTempChildren 补齐 | enableSyncLoad_/isSyncLoad_ 默认 true | AC-4.1~4.3 |
| R-11 | 行为 | API≥18 FreezeSpareNode | 预构建后冻结非 L1 spare 节点 JSViewActive | API18 门控 | AC-4.4,AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x virtualScroll/options | UT + SDK 比对 | 字段 @since、disableVirtualScroll static-only、master 始终 v2 |
| VM-2 | AC-2.x v2 RID 缓存 | UT | CallOnGetRid4Index CREATED/UPDATED、SetInvalid vs RemoveNode |
| VM-3 | AC-3.x 区间/recycle/pre-build | UT + benchmark | DoSetActiveChildRange、reusable=false、PROPERTY_UPDATE |
| VM-4 | AC-4.x sync-load/FreezeSpareNode | UT + API18 注入 | sync-load 默认开、API18 spare 冻结 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `.virtualScroll(VirtualScrollOptions?)`（dynamic `@since12`/static `@since23`） | 既有 | 开启虚拟滚动 | — | AC-1.1 |
| `VirtualScrollOptions.totalCount`（`@since12`） | 既有 | 总长度 | — | AC-1.2 |
| `VirtualScrollOptions.reusable`（`@since18`，默认 true） | 既有 | 复用开关 | false 强制 cachedCount=0 | AC-1.3 |
| `VirtualScrollOptions.onLazyLoading`/`onTotalCount`（`@since19`） | 既有 | 懒加载/动态总数 | — | AC-1.4,AC-1.5 |
| `VirtualScrollOptions.disableVirtualScroll`（static-only `@since23`） | 既有 | 禁用虚拟滚动 | dynamic 无 | AC-1.6 |

> SDK：dynamic `repeat.d.ts:102-230,378`；static `repeat.static.d.ets:129-185,249`。

## 接口规格

### 接口定义

**virtualScroll（dynamic，`repeat.d.ts:378`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `virtualScroll(virtualScrollOptions?: VirtualScrollOptions): RepeatAttribute<T>` |
| 返回值 | `RepeatAttribute<T>`（链式） |
| 开放范围 | Public（`@since12`） |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| totalCount | number/int | 否 | — | 总长度；与 onTotalCount 互斥场景 |
| reusable | boolean | 否 | true | false 强制 cachedCount=0（`@since18`） |
| onLazyLoading | (index)=>void | 否 | — | `@since19` |
| onTotalCount | ()=>number | 否 | — | `@since19`，动态总数 |
| disableVirtualScroll | boolean | 否 | false | **static-only** `@since23` |
| memoryOptimizationStrategy | RepeatMemOptStrategy | 否 | DEFAULT | `@since26`，详见 Feat-04 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.virtualScroll()` | master 动态路径实例化 v2 | AC-1.1 |
| 2 | reusable=false | 各模板 cachedCount 强制 0 | AC-1.3 |
| 3 | v2 CallOnGetRid4Index | TS 决定 CREATED_NEW_NODE/UPDATED_NODE | AC-2.2 |
| 4 | API≥18 预构建后 | FreezeSpareNode 冻结非 L1 spare | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为：master 动态路径**始终 v2**（`pu_repeat.ts:291`）；`disableVirtualScroll` 为 static-only。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since12`（virtualScroll/totalCount）；static `@since23`。
- **API 版本号策略:** 按 SDK `@since12/18/19/23` 标注。

> **v1 废弃风险（RISK-F2-3）：** v1（`RepeatVirtualScrollNode`，key+ttype 缓存，原 API≤15 兼容实现）**已废弃**——源码仍保留于代码库并被部分生产 Pattern（如 `list_pattern.cpp`/`swiper_pattern.cpp`）引用，但不再演进，master 动态路径始终 v2。下游勿基于 v1 做新开发；v1 残留引用待后续代码清理移除。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| master 动态路径始终 v2 | `pu_repeat.ts:291` 实例化 v2；v1 已废弃 | AC-1.1 |
| v2 RID 缓存 | `cacheItem4Rid_`+`l1Rid4Index_`，复用匹配在 TS 侧 | AC-2.2,AC-2.6 |
| cachedCount 双源 | TemplateOptions.cachedCount（TS 约束）+ 容器 cachedCount | AC-3.3 |
| PROPERTY_UPDATE 统一 | MEASURE_SELF_AND_PARENT\|BY_CHILD_REQUEST | AC-3.7 |
| sync-load 默认开 | v2 `enableSyncLoad_/isSyncLoad_` 默认 true | AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 虚拟滚动仅构建活跃+预缓存区，滚动帧率不劣于基线 | benchmark | `repeat_virtual_scroll_2_node.cpp` PostIdleTask |
| 内存 | 离屏节点 L1→L2，RID 上限 Purge | UT + 内存 dump | `repeat_virtual_scroll_2_caches.cpp:153-174` |
| 可靠性 | reusable=false/越界 index 不崩溃 | UT 异常 | `repeat_virtual_scroll_2_node.cpp:105-153` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 仅活跃 L1 节点入无障碍树，spare（API≥18）冻结 | AC-4.4 |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 是 | 窗口 hide/show 触发缓存回收/恢复（memOpt 启用，Feat-04） | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | reusable `@since18`、onLazyLoading/onTotalCount `@since19`、static `@since23` disableVirtualScroll、API18 FreezeSpareNode；v1 已废弃 | AC-1.3~1.6,AC-4.4 |
| 生态兼容 | 是 | dynamic `@since12`、static `@since23` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Repeat 虚拟滚动（v2；v1 已废弃）
  作为 应用开发者
  我想要 用 .virtualScroll 按需构建+回收子节点
  以便 大数据量滚动流畅且内存可控

  Scenario: master 动态路径始终 v2
    Given 动态范式调用 .virtualScroll()
    When pu_repeat.ts 路由
    Then 实例化 __RepeatVirtualScroll2Impl（v2），不经运行时 API 版本门控

  Scenario Outline: v2 RID 操作
    Given v2 路径
    When <操作>
    Then <结果>

    Examples:
      | 操作 | 结果 |
      | SetInvalid(rid) | L1→L2 保留节点 |
      | RemoveNode(rid) | 完全删除节点 |
      | CallOnGetRid4Index 返回 UPDATED_NODE | 复用既有 RID |

  Scenario: API18 spare 冻结
    Given API≥18 且 memOpt 预构建完成
    When FreezeSpareNode
    Then 非 L1 spare 节点 SetJSViewActive(false)
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做虚拟滚动 v2；v1 已废弃仅留声明；模板见 Feat-03、内存优化见 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "pu_repeat.ts virtualScroll 路由始终 v2 __RepeatVirtualScroll2Impl"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScroll2Caches cacheItem4Rid l1Rid4Index CallOnGetRid4Index SetInvalid RemoveNode"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScroll2Node FreezeSpareNode API18 门控 sync-load OrganizeSyncLoadCache"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScrollNode v1 已废弃 代码保留 master 始终 v2"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/repeat.d.ts`、`frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_node.cpp`、`frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_caches.cpp`、`docs/syntax/RepeatVirtualScroll_Knowledge_Base.md`
