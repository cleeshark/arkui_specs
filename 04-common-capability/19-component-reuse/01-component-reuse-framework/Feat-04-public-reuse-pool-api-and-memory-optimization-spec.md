# 特性规格

> Func-04-19-01-Feat-04 公开复用池 API 与内存优化（@since26）：固化 `ReusePoolOwnership`（SHARED/PER_INSTANCE/OFF）+ `poolAccepts`、`UIUtils.getCustomComponentContext`→`CustomComponentContext.getReusePool`→`IReusePool`（`getReusableInfo`/`preRender`）/`IReusableInfo`（`count`/`maxCount` 默认 100 上限 200）、`ReusableMemOptStrategy`/`memoryOptimizationStrategy`；全局复用池 `__ReusePool__Internal`（**TS-only，无 C++ 类**）、preRender `setTimeout(5)` macrotask、maxCount **同步**强制、C++ mem-opt（`CleanCache`/`PostMemOptTask`/`FireClearParentReusePoolFunc`）、C-API/NDK/ANI 桥接（`ReuseImpl`/`RecycleImpl`）、DFX（hidump RecyclePool）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 公开复用池 API 与内存优化（@since26） |
| 特性编号 | Func-04-19-01-Feat-04 |
| 优先级 | P1 |
| 目标版本 | dynamic/static `@since26`（ReusePoolOwnership/poolAccepts/IReusePool/IReusableInfo/preRender/ReusableMemOptStrategy 全套） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01~03（引擎复用框架）；本特性聚焦 `@since26` 公开复用池 API 与内存优化。TS `@Reusable`/`@ReusableV2` 装饰器与旧 state-mgmt 池（RecyclePoolV2/`__ReusePool__Internal__` shared/perInstance ≤API23）由 07-03-03 承接；本特性覆盖其 `@since26` 公开所有权配置 + engine realization。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/19-component-reuse/01-component-reuse-framework/design.md` | Baselined |
| Static API（@Component/@Reusable 配置） | `interface/sdk-js/api/arkui/component/customComponent.static.d.ets` | — |
| Dynamic API（UIUtils/IReusePool） | `interface/sdk-js/api/@ohos.arkui.StateManagement.d.ts` | — |
| TS 全局复用池 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_globalreuse.ts` | — |
| TS 池 handle/preRender | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts`、`v2/v2_change_observation.ts`、`sdk/ui_utils.ts` | — |
| C++ mem-opt | `frameworks/core/components_ng/pattern/custom/custom_node.cpp` / `custom_node_base.cpp` | — |
| JS 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_view.cpp` | — |
| C-API/NDK/ANI | `frame_node_extender_accessor.cpp`、`custom_node_ani_modifier.cpp` | — |
| 旧 per-instance 池（memOpt 消费） | `state_mgmt/src/lib/partial_update/pu_recycle_manager.ts`、`v2/v2_recycle_pool.ts` | — |

> 需求基线详见 proposal.md。本特性含 `@since26` 公开 API（SDK 契约）+ framework-internal C++/TS backing。

---

## 用户故事

### US-1: 池所有权配置

**作为** 应用开发者,
**我想要** 用 `@Component.reusePool`/`poolAccepts` 配置复用池所有权,
**以便** 控制跨父共享 vs 按父隔离 vs 关闭。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 设 `@Component.reusePool`/`@ComponentV2.reusePool`（`customComponent.static.d.ets:190,221` `@since26`）为 `ReusePoolOwnership.SHARED`/`PER_INSTANCE`/`OFF`（默认 OFF，`:140-169`）THEN 配置池所有权 | 正常 |
| AC-1.2 | WHEN 设 `poolAccepts: string[]`（`:199,230` `@since26`）THEN 声明该池接受的组件类型列表；空则 `__ReusePool__Internal.create` 抛错（`puv2_globalreuse.ts:499-501`） | 异常 |
| AC-1.3 | WHEN `SHARED` THEN `__ReusePool__Internal.create`（`:487-520`）返回按 owner ctor+accepted ctors 缓存的共享池（`:503-517`） | 正常 |
| AC-1.4 | WHEN `PER_INSTANCE` THEN 每次创建新池（`:519`） | 正常 |
| AC-1.5 | WHEN `OFF`（默认）THEN 不配置全局池，沿用旧 per-instance 复用（07-03-03） | 边界 |

### US-2: 公开池 handle（IReusePool/IReusableInfo）

**作为** 应用开发者,
**我想要** 经 `getCustomComponentContext`→`getReusePool` 查询池信息,
**以便** 监控/控制复用池。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调 `UIUtils.getCustomComponentContext(target)`（`StateManagement.d.ts:660` `@since26`）THEN 仅 ViewPU/ViewV2 返回 `CustomComponentContext`（`ui_utils.ts:117-125`） | 正常 |
| AC-2.2 | WHEN `CustomComponentContext.getReusePool()`（`StateManagement.d.ts:1355` `@since26`）THEN 解析 `__reusePool__Internal ?? __getReusePoolInternal__Internal()`（`puv2_view_base.ts:959-968`）+`setCallerContext(this)` 返回 `IReusePool\|undefined` | 正常 |
| AC-2.3 | WHEN `__getReusePoolInternal__Internal()`（`:937-950`）THEN 沿祖先链匹配 `acceptsComponent(cls)` 解析池 | 正常 |
| AC-2.4 | WHEN `IReusePool.getReusableInfo(ctor,reuseId?)`（`StateManagement.d.ts:1391` `@since26`）THEN 返回 `IReusableInfo[]/IReusableInfo/undefined` | 正常 |
| AC-2.5 | WHEN `IReusableInfo.count`/`maxCount`（`:1434,1448`）THEN count 通常≤maxCount（默认 100、上限 200、负→0、>200→200，`:1425-1440`） | 边界 |

### US-3: preRender idle 预创建

**作为** 应用开发者,
**我想要** 用 `preRender(builder,times)` 预创建复用节点,
**以便** 提前填充池减少滚动卡顿。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调 `IReusePool.preRender(builder,times): Promise<void>`（`StateManagement.d.ts:1408` `@since26`）THEN `__beginPreRender__Internal`+循环 `times` 次 `builderFn()`+`__endPreRender__Internal`（`puv2_globalreuse.ts:402-434`） | 正常 |
| AC-3.2 | WHEN 预渲染子组件创建 THEN `queuePreRenderCreation`（`v2_change_observation.ts:253-292`）以 `setTimeout(5)` macrotask 延迟构建（`:281-291`），设 `__isPreRendered__Internal=true`+`__initialRenderForPreRender__Internal`+`pool.push` | 边界 |
| AC-3.3 | WHEN preRender Promise 解析 THEN `Promise.all(preRenderTasks_)` 完成后 resolve（`puv2_globalreuse.ts:427-433`） | 正常 |

### US-4: maxCount 强制与异步清理

**作为** 应用开发者,
**我想要** maxCount 限制池大小,
**以便** 控制内存。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `push(reuseId,node,cls)`（`puv2_globalreuse.ts:546-577`）且 `currentArr.length>=currentMax` THEN **同步** reject+`node.resetRecycleCustomNode()` 销毁（`:564-569`） | 正常 |
| AC-4.2 | WHEN `pruneMaxCount`（`:210-239`）THEN `<0`→0、`>200`→200；`pruneBucket_`（`:243-259`）同步淘汰超限（`arr.pop()?.resetRecycleCustomNode()`，`pruning_` Set 防重入） | 正常 |
| AC-4.3 | WHEN `maxCount` setter（`:321-323`）THEN 立即 `pruneMaxCount` | 正常 |
| AC-4.4 | WHEN `pop` 且 `currentMax==0` THEN reject pop（`:594-597`） | 边界 |
| AC-4.5 | WHEN `getEffectiveMaxCount`（`:533-538`）THEN 优先级：bucket-specific→component-wide→DEFAULT_MAX_COUNT(100) | 正常 |
| AC-4.6 | WHEN C++ mem-opt 异步清理 THEN `CustomNode::CleanCache`（`custom_node.cpp:474-494`）+`CleanCacheOnIdle`（`:496-516`）+`PostMemOptTask`（`:547-579`，1000ms poll）在内存/可见性事件时 drain（非为 maxCount 上限） | 边界 |

### US-5: ReusableMemOptStrategy

**作为** 应用开发者,
**我想要** 用 `memoryOptimizationStrategy` 启用自动缓存优化,
**以便** 后台/低内存回收池缓存。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设 `@Reusable.memoryOptimizationStrategy`/`@ReusableV2.memoryOptimizationStrategy`（`customComponent.static.d.ets:293,312` `@since26`）为 `ReusableMemOptStrategy.ENABLE_AUTO_CACHE_OPTIMIZATION`（`:240-257`）THEN 启用 mem-opt | 正常 |
| AC-5.2 | WHEN C++ `SetReusableMemOptStrategy`/`SetStaMemopt`（`custom_node_base.cpp:244-252,394-398`）THEN 存 `staReusableMemOptStrategy_` | 正常 |
| AC-5.3 | WHEN `CustomNode::OnAttachToMainTree`（`custom_node.cpp:56-58`）+`staReusableMemOptStrategy_==ENABLE_AUTO_CACHE_OPTIMIZATION` THEN `StartMemOpt` | 正常 |
| AC-5.4 | WHEN mem-opt 启用 + 父不可见/内存事件 THEN `PostMemOptTask` tick `FireClearParentReusePoolIfNeeded()`（`:569-576`）→`FireClearParentReusePoolFunc`→TS `__releaseRecyclePool__Internal` drain | 正常 |
| AC-5.5 | WHEN 旧 per-instance 池 THEN `pu_recycle_manager.ts:67`/`v2_recycle_pool.ts:66` 直接读 `__getReusableMemOptStrategy__Internal()==1` 加 `reuseIdForOptimize`+`scheduleCacheCleanTask` | 边界 |
| AC-5.6 | WHEN `__ReusePool__Internal`（全局池）THEN **不直接读** ReusableMemOptStrategy；仅经 C++ `FireClearParentReusePoolFunc` 间接影响 | 边界 |

### US-6: C-API/NDK/ANI 桥接与 DFX

**作为** 框架维护者,
**我想要** C-API/ANI 节点参与复用 + DFX 可 dump 池,
**以便** 命令式节点复用 + 调试。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN NDK `frame_node_extender_accessor::ReuseImpl/RecycleImpl`（`:1114-1133`）THEN 调 `UINode::OnReuse()`/`OnRecycle()` | 正常 |
| AC-6.2 | WHEN ANI `custom_node_ani_modifier::OnReuse/OnRecycle`（`:266-278`）THEN `reinterpret_cast<CustomNode*>`→`OnReuse/OnRecycle` | 正常 |
| AC-6.3 | WHEN hidump → `CustomNode::DumpInfo`（`custom_node.cpp:322`）THEN `FireOnDumpInfoFunc({"RecyclePool"})`→TS `onDumpInfo`（`puv2_view_base.ts:1294-1296`）→`__getRecycleDump_internal`（`pu_view.ts:419-428`）→`reusePool.getDumpInfo()`（`puv2_globalreuse.ts:610-618`）JSON dump `{reuseKey,className,nodeId[]}` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.5 | R-1,R-2 | T-4 | UT + SDK 比对 | `customComponent.static.d.ets:140-230`、`puv2_globalreuse.ts:487-520` |
| AC-2.1~2.5 | R-3 | T-4 | UT + SDK 比对 | `StateManagement.d.ts:660-1448`、`puv2_view_base.ts:937-990` |
| AC-3.1~3.3 | R-4,R-10 | T-4 | UT：preRender | `puv2_globalreuse.ts:402-434`、`v2_change_observation.ts:253-292` |
| AC-4.1~4.6 | R-5,R-6,R-11 | T-4 | UT：maxCount + C++ memOpt | `puv2_globalreuse.ts:546-577`、`custom_node.cpp:474-579` |
| AC-5.1~5.6 | R-7,R-8,R-12 | T-4 | UT + C++ memOpt | `custom_node_base.cpp:244-252`、`custom_node.cpp:56-58,569-576` |
| AC-6.1~6.3 | R-9,R-13 | T-4 | UT + hidump | `frame_node_extender_accessor.cpp:1114-1133`、`custom_node.cpp:322` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | reusePool 配置 | SHARED→缓存共享池；PER_INSTANCE→每实例新池；OFF（默认）→旧 per-instance | poolAccepts 空抛错 | AC-1.1~1.5 |
| R-2 | 行为 | poolAccepts | 声明接受组件类型；空→create 抛错 | @since26 | AC-1.2 |
| R-3 | 行为 | getReusePool | 解析 __reusePool__Internal/沿祖先 acceptsComponent+setCallerContext | ViewPU/ViewV2 only | AC-2.1~2.3 |
| R-4 | 行为 | preRender | beginPreRender+循环 builderFn+endPreRender；子 setTimeout(5) 延迟构建；Promise.all resolve | @since26 | AC-3.1~3.3 |
| R-5 | 行为 | push + maxCount | 同步 reject+destroy if >=currentMax | currentMax 优先级 bucket→component→100 | AC-4.1,AC-4.5 |
| R-6 | 行为 | pruneMaxCount | <0→0、>200→200；setter 立即 prune | pruning_ 防重入 | AC-4.2,AC-4.3 |
| R-7 | 行为 | ReusableMemOptStrategy | C++ SetStaMemopt+OnAttachToMainTree StartMemOpt | ENABLE_AUTO_CACHE_OPTIMIZATION | AC-5.1~5.3 |
| R-8 | 行为 | mem-opt drain | PostMemOptTask(1000ms) + 父不可见/内存→FireClearParentReusePoolIfNeeded→TS drain | 全局池不直接读 memOpt | AC-5.4,AC-5.6 |
| R-9 | 行为 | C-API/ANI | ReuseImpl/RecycleImpl/OnReuse/OnRecycle→UINode::OnReuse/OnRecycle | — | AC-6.1,AC-6.2 |
| R-10 | 边界 | preRender setTimeout | SDK "idle task" 实为 setTimeout(5) macrotask（非 queueIdleTask） | SDK-vs-source 差异 | AC-3.2 |
| R-11 | 边界 | maxCount 同步 | SDK "async clean" 实为同步 push reject；异步仅 memOpt drain | SDK-vs-source 差异 | AC-4.1,AC-4.6 |
| R-12 | 边界 | 全局池 TS-only | __ReusePool__Internal 无 C++ 类；C++ 仅 mem-opt/DFX/生命周期 | — | AC-5.6 |
| R-13 | 行为 | DFX | hidump→DumpInfo→FireOnDumpInfoFunc(RecyclePool)→TS getDumpInfo JSON | — | AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 所有权配置 | UT + SDK | SHARED/PER_INSTANCE/OFF、poolAccepts |
| VM-2 | AC-2.x 池 handle | UT + SDK | getCustomComponentContext/getReusePool/getReusableInfo |
| VM-3 | AC-3.x preRender | UT | setTimeout(5)、Promise.all |
| VM-4 | AC-4.x maxCount | UT | 同步 push reject、pruneMaxCount、memOpt async drain |
| VM-5 | AC-5.x memOpt | UT + C++ | C++ StartMemOpt/PostMemOptTask、旧池 scheduleCacheCleanTask |
| VM-6 | AC-6.x C-API/DFX | UT + hidump | ReuseImpl/RecycleImpl、getDumpInfo |

## API 变更分析

> 本特性含 `@since26` 公开 API（存量补录）。

### 新增 API

N/A（存量补录）。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `ReusePoolOwnership` + `@Component/@ComponentV2.reusePool`/`poolAccepts`（static `@since26`） | 既有 | 池所有权配置 | OFF 默认沿用旧池 | AC-1.1~1.2 |
| `UIUtils.getCustomComponentContext`/`CustomComponentContext.getReusePool`/`IReusePool`/`IReusableInfo`（dynamic `@since26`） | 既有 | 池 handle 查询 | ViewPU/ViewV2 only | AC-2.1~2.5 |
| `IReusePool.preRender`（dynamic `@since26`） | 既有 | idle 预创建 | setTimeout(5) macrotask | AC-3.1 |
| `ReusableMemOptStrategy` + `@Reusable/@ReusableV2.memoryOptimizationStrategy`（static `@since26`） | 既有 | 内存优化 | ENABLE_AUTO_CACHE_OPTIMIZATION | AC-5.1 |

> SDK：static `customComponent.static.d.ets:140-312`；dynamic `StateManagement.d.ts:660-1448`。

## 接口规格

### 接口定义

**ReusePoolOwnership（static，`customComponent.static.d.ets:140`）**

| 属性 | 值 |
|------|-----|
| 枚举 | `SHARED='shared'`/`PER_INSTANCE='perInstance'`/`OFF='off'`（默认） |
| 开放范围 | Public（`@since26`） |
| 关联 AC | AC-1.1 |

**IReusePool（dynamic，`StateManagement.d.ts:1367`）**

| 属性 | 值 |
|------|-----|
| 方法 | `getReusableInfo(ctor,reuseId?): IReusableInfo[]\|IReusableInfo\|undefined`；`preRender(builder,times): Promise<void>` |
| 开放范围 | Public（`@since26`） |
| 关联 AC | AC-2.4,AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| reusePool | ReusePoolOwnership | 否 | OFF | SHARED/PER_INSTANCE/OFF |
| poolAccepts | string[] | 否 | [] | 空则 create 抛错 |
| maxCount | number | 否 | 100 | <0→0、>200→200 |
| times（preRender） | number | 是 | — | 预创建次数 |
| memoryOptimizationStrategy | ReusableMemOptStrategy | 否 | DEFAULT | DEFAULT/ENABLE_AUTO_CACHE_OPTIMIZATION |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | reusePool=SHARED | 缓存共享池 | AC-1.3 |
| 2 | push 超 maxCount | 同步 reject+destroy | AC-4.1 |
| 3 | preRender | setTimeout(5) 延迟构建+Promise.all | AC-3.2,AC-3.3 |
| 4 | memOpt + 父不可见 | PostMemOptTask drain | AC-5.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为：全局复用池 `__ReusePool__Internal` 为 **TS-only**（无 C++ 类）；`preRender` 用 `setTimeout(5)` macrotask（**非** SDK 文档的 "idle task"/`queueIdleTask`）；`maxCount` **同步**强制（push reject，**非** SDK 文档的 "async clean"）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic/static `@since26`。
- **API 版本号策略:** 按 SDK `@since26` 标注。

> **SDK-vs-source 差异风险（必须可见，不静默消除）：**
> - **F-preRender**：SDK 文档称 preRender "idle task"（`StateManagement.d.ts:1400`），实现为 `setTimeout(5)` macrotask（`v2_change_observation.ts:281-291`），**非**框架 `queueIdleTask`（风险 RISK-F4-1）。
> - **F-maxCount**：SDK `IReusableInfo.count` 文档称 "count may exceed maxCount briefly because pool clean happens asynchronously"（`:1425-1426`），实现为 **同步** push reject（`puv2_globalreuse.ts:564-569`）；异步路径（`custom_node.cpp:496-516`）仅用于 mem-opt drain，**非**上限强制（风险 RISK-F4-2）。
> - **F-globalpool**：全局复用池 `__ReusePool__Internal` 为 **TS-only**（无 C++ 类），C++ 仅做 mem-opt/DFX/生命周期钩子（风险 RISK-F4-3）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 全局池 TS-only | __ReusePool__Internal 无 C++ 类 | AC-5.6 |
| preRender setTimeout(5) | 非 queueIdleTask | AC-3.2 |
| maxCount 同步强制 | push reject+destroy；异步仅 memOpt drain | AC-4.1,AC-4.6 |
| ReusableMemOptStrategy 间接 | 全局池不直接读；经 C++ FireClearParentReusePoolFunc | AC-5.6 |
| C-API/ANI 经 UINode virtual | ReuseImpl/RecycleImpl→OnReuse/OnRecycle | AC-6.1,AC-6.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 内存 | memOpt 后台/低内存 drain 池（PostMemOptTask 1000ms poll） | UT + 内存 dump | `custom_node.cpp:547-579` |
| 性能 | maxCount 同步强制避免池膨胀；preRender 预创建减少滚动卡顿 | UT + benchmark | `puv2_globalreuse.ts:564-569,402-434` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 是 | 内存压力易触发 memOpt drain | XTS | `custom_node.cpp:569-576` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 无直接关联 | — |
| 大字体 | 否 | 无直接关联 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 是 | 父不可见触发 memOpt drain | AC-5.4 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | `@since26` 全套公开 API | AC-1.1,AC-2.1,AC-3.1,AC-5.1 |
| 生态兼容 | 是 | dynamic/static `@since26` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 公开复用池 API 与内存优化（@since26）
  作为 应用开发者
  我想要 用 reusePool/preRender/maxCount/memOpt 配置控制复用池
  以便 跨父共享复用 + 内存可控

  Scenario Outline: 池所有权
    Given @Component.reusePool = <模式>
    When __ReusePool__Internal.create
    Then <池>

    Examples:
      | 模式 | 池 |
      | SHARED | 缓存共享池 |
      | PER_INSTANCE | 每实例新池 |
      | OFF | 旧 per-instance |

  Scenario: maxCount 同步强制
    Given 池已满（length>=maxCount）
    When push
    Then 同步 reject+resetRecycleCustomNode

  Scenario: preRender
    Given preRender(builder, 3)
    When 执行
    Then 3 次 builderFn + setTimeout(5) 延迟构建 + Promise.all resolve

  Scenario: memOpt drain
    Given memoryOptimizationStrategy=ENABLE_AUTO_CACHE_OPTIMIZATION + 父不可见
    When PostMemOptTask tick
    Then FireClearParentReusePoolIfNeeded→TS __releaseRecyclePool__Internal drain
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 做 @since26 公开池 API+memOpt；引擎框架见 Feat-01~03；TS @Reusable 见 07-03-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查
- [x] SDK-vs-source 差异（preRender/maxCount/全局池）在兼容性声明+风险表可见

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "__ReusePool__Internal create SHARED PER_INSTANCE OFF poolAccepts puv2_globalreuse"
  - repo: "openharmony/arkui_ace_engine"
    query: "preRender queuePreRenderCreation setTimeout(5) Promise.all puv2_globalreuse v2_change_observation"
  - repo: "openharmony/arkui_ace_engine"
    query: "maxCount push 同步 reject pruneMaxCount pruneBucket_ puv2_globalreuse"
  - repo: "openharmony/arkui_ace_engine"
    query: "CustomNode CleanCache PostMemOptTask FireClearParentReusePoolIfNeeded ReusableMemOptStrategy"
```

**关键文档：** `interface/sdk-js/api/arkui/component/customComponent.static.d.ets`、`interface/sdk-js/api/@ohos.arkui.StateManagement.d.ts`、`frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_globalreuse.ts`、`frameworks/core/components_ng/pattern/custom/custom_node.cpp`
