# 特性规格

> Func-07-05-02-Feat-01 LazyForEach 核心语法与按需渲染：固化 `LazyForEach()` 构造的全部重载（dynamic `@since7` / static `@since23` / options `@since26` / style-builder `@since26 staticonly`）、NG/legacy/Arkoala 三条派发路径、`itemGenerator` 与按需子节点生成（`GetFrameChildByIndex` / `BuildAllChildren`、三级缓存 `cachedItems_`→`expiringItem_`→build）、`keyGenerator` key 契约（默认 key=`viewId-index`、`viewId-` 前缀注入、非 string/number 回退、重复 key 静默丢弃）、虚拟滚动引擎（cachedCount/active range/recycle/idle pre-build）、`LazyForEachAttribute` 返回值与静态属性面行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | LazyForEach 核心语法与按需渲染 |
| 特性编号 | Func-07-05-02-Feat-01 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since7`（三参）/ `@since12`（`LazyForEachAttribute` 返回值）/ `@since26`（options 四参）；static `@since23`（三参）/ `@since26`（options 四参）/ `@since26 staticonly`（style-builder）；crossplatform `@since10`、atomicservice `@since11`（dynamic） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-07-05-02（LazyForEach）的首个 Feat，作为该功能域 design.md 基线。数据源契约/单条变更通知（Feat-02）、批量 onDatasetChange（Feat-03）、选项策略与内存/冻结优化（Feat-04）、拖拽排序 onMove（Feat-05）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/02-lazy-foreach/design.md` | Baselined |
| Dynamic API（SDK 契约） | `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts` | — |
| Static API（SDK 契约） | `interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets` | — |
| JS 桥接入口 | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach.cpp` | — |
| JS 执行器/Builder | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach_builder.h` | — |
| NG 语法节点 | `frameworks/core/components_ng/syntax/lazy_for_each_node.cpp` / `.h` | — |
| NG 缓存/差分引擎 | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` / `.h` | — |
| NG Model 工厂 | `frameworks/core/components_ng/syntax/lazy_for_each_model_ng.h` | — |
| 布局侧 Lazy Wrapper | `frameworks/core/components_ng/syntax/lazy_layout_wrapper_builder.cpp` / `.h` | — |
| Arkoala 静态节点 | `frameworks/core/components_ng/syntax/arkoala_lazy_node.cpp` / `.h` | — |
| ANI 静态构造入口 | `frameworks/core/interfaces/native/ani/lazy_for_each_node_ani_modifier.h` | — |
| C-API NodeAdapter 构造 | `frameworks/core/interfaces/native/node/node_adapter_impl.cpp` | — |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: LazyForEach 构造与返回值

**作为** 应用开发者,
**我想要** 用 `LazyForEach(dataSource, itemGenerator, keyGenerator?)` 声明按需渲染的循环列表,
**以便** 仅构建可见及预缓存区内的子节点，支撑长列表/网格等大数据量场景的性能。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 dynamic 范式（`@since7`）调用 `LazyForEach(dataSource, itemGenerator, keyGenerator?)` THEN 经 `JSLazyForEach::Create`（`js_lazy_foreach.cpp:306-365`）解析参数并构造；自 `@since12` 起返回值类型为 `LazyForEachAttribute`（`lazy_for_each.d.ts:961,1007-1019`） | 正常 |
| AC-1.2 | WHEN 在 dynamic 范式（`@since26`）传入第四参 `options: LazyForEachOptions` THEN 走 `ParseOptions`（`js_lazy_foreach.cpp:258-277`）解析 `customComponentFreezeMode`/`releaseStrategy`/`memoryOptimizationStrategy` 并 `actuator->SetOptions`（选项语义详见 Feat-04） | 正常 |
| AC-1.3 | WHEN 在 static 范式（`@since23`）调用三参 `LazyForEach<T>(dataSource, itemGenerator, keyGenerator?)` THEN 经 ANI 静态入口 `ConstructLazyForEachNode`（`lazy_for_each_node_ani_modifier.h:24-31`）创建 `ArkoalaLazyNode`（`arkoala_lazy_node.cpp:25-26`），返回 `LazyForEachAttribute`（`lazyForEach.static.d.ets:756-769`） | 正常 |
| AC-1.4 | WHEN 在 static 范式（`@since26`）传入第四参 `options` THEN 走 `setLazyForEachOptions(...)` 四参重载（`lazyForEach.static.d.ets:716-719`） | 正常 |
| AC-1.5 | WHEN 在 static 范式（`@since26 staticonly`）使用 style-builder 形态 `LazyForEach(style: CustomBuilderT<LazyForEachAttribute>)` THEN 该重载为 staticonly，dynamic 无对应形态（`lazyForEach.static.d.ets:804`） | 边界 |
| AC-1.6 | WHEN dynamic 实例构造时 THEN 由 `LazyForEachModel::GetInstance()` 经 `Container::IsCurrentUseNewPipeline()` 选择 NG（`LazyForEachModelNG`+`JSLazyForEachBuilder`）或 legacy（`LazyForEachModelImpl`+`JSLazyForEachComponent`）路径（`js_lazy_foreach.cpp:45-59`）；`NG_BUILD` 编译时 legacy 分支被裁剪 | 正常 |
| AC-1.7 | WHEN Arkoala 静态节点构造 THEN 不经 `LazyForEachModelNG::Create`，而是独立路径 `ConstructLazyForEachNode`→`ArkoalaLazyNode`→`RegisterArkoalaLazyNode`，ops 由 `lazy_for_each_ops_accessor.cpp` 驱动 | 正常 |
| AC-1.8 | WHEN 取 `LazyForEachAttribute` 静态接口（`@since23`，extends `DynamicNode`）THEN 仅 `@since26 staticonly` 暴露 `debugLine`/`setLazyForEachOptions`（2 重载）/`applyAttributesFinish`（`lazyForEach.static.d.ets:667-729`）；dynamic 侧 `LazyForEachAttribute` 为空类（`@since12`），仅作拖拽排序属性承载（`lazy_for_each.d.ts:961`） | 边界 |
| AC-1.9 | WHEN `ParseAndVerifyParams`（`js_lazy_foreach.cpp:138-175`）校验参数 THEN `dataSource` 必须为 object、`itemGenerator` 必须为 function、`keyGenerator` 为 function 或 undefined，否则按非法参数处理不进入构造 | 异常 |

### US-2: itemGenerator 与按需子节点生成

**作为** 应用开发者,
**我想要** 仅在父容器请求某个 index 时由 `itemGenerator` 生成对应子节点,
**以便** 避免一次性构建全量数据项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 父容器（List/Grid/Swiper 等）按 index 请求子节点 THEN `LazyForEachNode::GetFrameChildByIndex`（`lazy_for_each_node.cpp:421-474`）经 bounds check 后派发 `builder_->GetChildByIndex(index, needBuild, isCache)` | 正常 |
| AC-2.2 | WHEN 请求 `index >= totalCount` THEN `CHECK_EQUAL_RETURN(index >= FrameCount(), true, nullptr)` 直接返回 `nullptr`，不触发构建（`lazy_for_each_node.cpp:427`） | 边界 |
| AC-2.3 | WHEN `GetChildByIndex`（`lazy_for_each_builder.cpp:25-64`）查找节点 THEN 按 `cachedItems_`（L1 活跃）→`expiringItem_`（L2 离屏池）→`OnGetChildByIndex`/`OnGetChildByIndexNew` 实构建的三级顺序命中即返回 | 正常 |
| AC-2.4 | WHEN `isCache=true` 读 THEN 命中 `expiringItem_` 时返回副本但不提升（不回迁 L1）；WHEN `isCache=false` 读 THEN 命中 `expiringItem_` 时把节点提升回 `cachedItems_` 并擦除 expiring 条目（`lazy_for_each_builder.cpp:33-42`） | 边界 |
| AC-2.5 | WHEN LazyForEachNode 出现在非滚动容器的 frame-child 枚举中 THEN 触发 `BuildAllChildren`（`lazy_for_each_node.cpp:116-130`）对 `[0, FrameCount)` 全量 `GetFrameChildByIndex` 后回填 `children_`（全量构建回退路径，调用方 `frame_node.cpp:357-364`） | 正常 |
| AC-2.6 | WHEN 父容器为 Swiper（host tag == `SWIPER_ETS_TAG`）THEN `AdjustLayoutWrapperTree` 置 `lazySwiper_` 标志（`lazy_for_each_node.cpp:109-110`），`LazyLayoutWrapperBuilder::OnGetOrCreateWrapperByIndex` 走虚拟索引转换（`lazy_layout_wrapper_builder.cpp:52-59`）而非全量构建 | 正常 |
| AC-2.7 | WHEN `itemGenerator(item, index)` 回调执行 THEN 通过 `JSLazyForEachBuilder::OnGetChildByIndex(New)`（`js_lazy_foreach_builder.h:133,189`）在 ViewStackProcessor 上 `PushKey`/`PopKey` 驱动子树构建，回调返回 `void` | 正常 |

### US-3: keyGenerator 与 key 契约

**作为** 应用开发者,
**我想要** 通过 `keyGenerator` 为每个数据项提供稳定唯一 key,
**以便** 框架按 key 复用/定位子节点，避免渲染错位与重复构建。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 省略 `keyGenerator` THEN 默认 key 生成函数返回 `viewId + "-" + index`（即仅按序号生成，与数据内容无关）（`js_lazy_foreach.cpp:333-334`；SDK 契约 `lazy_for_each.d.ts:1001-1003`） | 正常 |
| AC-3.2 | WHEN 提供用户 `keyGenerator` THEN 其返回值恒被注入 `viewId + "-"` 前缀（即最终 key = `viewId + "-" + <用户返回>`），保证同一 LazyForEach 实例内命名空间隔离（`js_lazy_foreach.cpp:335-342`） | 正常 |
| AC-3.3 | WHEN 用户 `keyGenerator` 返回非 string/number（如 undefined/object）THEN 回退为 `std::to_string(index)` 并仍加 `viewId + "-"` 前缀（`js_lazy_foreach.cpp:335-342`） | 异常 |
| AC-3.4 | WHEN 同一 LazyForEach 内出现重复 key（用户 keyGenerator 返回值碰撞）THEN `expiringItem_`/cache 的 `try_emplace` 插入失败，输出 `Use repeat key for index: <index>` 告警（`AceLogTag::ACE_LAZY_FOREACH`）并将重复节点交 `ProcessOffscreenNode` 丢弃，**不抛异常、不中断渲染**（`lazy_for_each_builder.cpp:919-923,947-951,1008-1022`） | 异常 |
| AC-3.5 | WHEN 数据项内容未变化 THEN 其 key 必须保持不变（一致性约束，SDK `lazy_for_each.d.ts:996-1006`）；违反将导致缓存命中错乱 | 边界 |
| AC-3.6 | WHEN 采用默认 index-based key 且数据源发生重排/交换/删除（非末尾追加）THEN 因 key 仅随序号变化，框架无法识别内容迁移，可能导致子节点状态/渲染错位；需提供内容型 `keyGenerator` 才能正确复用（风险项，详见兼容性声明） | 边界 |

### US-4: 虚拟滚动引擎（cachedCount / active range / recycle / idle pre-build）

**作为** 应用开发者,
**我想要** LazyForEach 仅保留可视区及预缓存区内的活跃节点，离屏节点回收入池、帧间空闲预构建后续节点,
**以便** 平衡滚动流畅度与内存占用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 父容器设置 cachedCount THEN 经 `ForEachBaseNode::OnSetCacheCount` 覆写（`lazy_for_each_node.h:133-139`）转发 `builder_->SetCacheCount(cacheCount)`；默认 `cacheCount_ = 0`（`lazy_for_each_builder.h:367`） | 正常 |
| AC-4.2 | WHEN `cachedCount = 0` THEN **不等于"不缓存"**：仍会预构建可视窗口本身，预构建范围 `range = cacheCount_ - showCached`（前向/后向分别 `cacheCount_ - endShowCached_` / `cacheCount_ - startShowCached_`）（`lazy_for_each_builder.cpp:1031-1072` `CheckCacheIndex`） | 边界 |
| AC-4.3 | WHEN `DoSetActiveChildRange`（`lazy_for_each_node.cpp:519-548`）下发活跃区间 THEN `SetActiveChildRange`（`lazy_for_each_builder.cpp:927-977`）将越界节点 `SetActive(false)` 并**移入 `expiringItem_` 二级离屏池**（非销毁），重复 key 越界项交 `ProcessOffscreenNode(node, true)` 释放 | 正常 |
| AC-4.4 | WHEN 越界节点后再次进入活跃区且 `isCache=false` 读 THEN 从 `expiringItem_` 提升回 `cachedItems_` 并 `SetActive(true)`（`lazy_for_each_builder.cpp:963-974`） | 正常 |
| AC-4.5 | WHEN 触发 `PostIdleTask(taskSource)`（`lazy_for_each_node.cpp:132-171`）THEN 以帧间 predict task（`AddPredictTask`）方式在 deadline 内执行 `builder_->PreBuild` + `RemovingExpiringItem`；任务源枚举 `LazyForEachIdleTaskSource`（`lazy_for_each_node.h:33-43`：POST_IDLE_TASK/ON_DATA_RELOADED/GET_FRAME_CHILD/RECYCLE_ITEMS/REMOVE_CHILD_IN_RENDER_TREE/SET_ACTIVE_RANGE/RESTORE_CACHE/MEMORY_OPTIMIZE/RELEASE_NODE） | 正常 |
| AC-4.6 | WHEN `PreBuildByIndex` 在 `deadline` 前未完成 THEN 返回未完成并记录 `preBuildingIndex_`，下一次 `PostIdleTask` 经 `ProcessPreBuildingIndex` 从该 index 续建（`lazy_for_each_builder.cpp:1074-1118,1362-1372`） | 边界 |
| AC-4.7 | WHEN 任一数据变更（`OnDataReloaded`/`OnDataAdded`/`OnDataDeleted`/`OnDataChanged`/`OnDataMoved`/`OnDataBulk*`/`OnDatasetChange`/`MoveData`/`TryTriggleAdditionalLayout`）触发 THEN 统一置 `PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT` 并前置 `MarkNeedSyncRenderTree(true)`（`lazy_for_each_node.cpp:193,210,227,260,290,306,337,353,369,411,592,697`） | 正常 |
| AC-4.8 | WHEN 父容器布局 THEN `AdjustLayoutWrapperTree` 把 `LazyLayoutWrapperBuilder` 安装到**父容器** wrapper（`lazy_for_each_node.cpp:104-114`）；`OnGetOrCreateWrapperByIndexLegacy` 强制对现有 `[startIndex_, endIndex_]` 窗口做 ±1 有序步进访问，越序访问返回 `nullptr`+LOGE（`lazy_layout_wrapper_builder.cpp:94-139`） | 边界 |
| AC-4.9 | WHEN `RecycleItems(from,to)`（`lazy_for_each_node.cpp:490-503`）/`DoRemoveChildInRenderTree`（`:505-517`）THEN 越界节点记入 `outOfBoundaryNodes_` 并 `PostIdleTask(RECYCLE_ITEMS)`，builder 侧 `RecycleItemsOutOfBoundary`→`RecycleChildByIndex`（`lazy_for_each_builder.cpp:770-787,868-874`）回收 `RecycleDummyNode` 占位项；`RemoveAllChild` 将全部缓存节点移入 `expiringItem_`（`:907-925`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.9 | R-1,R-2,R-9 | T-1 | UT：`lazy_for_each_model_test_ng` / `lazy_for_each_syntax_test_ng` 构造与参数校验 | `js_lazy_foreach.cpp:306-365`、`lazyForEach.static.d.ets:756-804` |
| AC-2.1~2.7 | R-3,R-4,R-5 | T-2 | UT：`lazy_for_each_builder_syntax_test_ng` GetChildByIndex/BuildAllChildren；Mock `mock_lazy_foreach_builder.h` | `lazy_for_each_node.cpp:421-474`、`lazy_for_each_builder.cpp:25-64` |
| AC-3.1~3.6 | R-6,R-7,R-8,R-10 | T-3 | UT：`lazy_for_each_builder_syntax_test_ng(_advanced)` 默认 key/前缀/冲突；XTS 渲染错位用例 | `js_lazy_foreach.cpp:333-342`、`lazy_for_each_builder.cpp:919-1022` |
| AC-4.1~4.9 | R-11,R-12,R-13,R-14,R-15 | T-4 | UT：`lazy_for_each_syntax_test_ng(_2)`、`lazy_for_each_builder_syntax_test_ng(_advanced)` cachedCount/active range/pre-build；benchmark 帧率 | `lazy_for_each_node.cpp:116-171,490-548`、`lazy_for_each_builder.cpp:789-1118` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | dynamic `@since7` 调用三参 `LazyForEach` | 经 `JSLazyForEach::Create` 构造，`@since12` 起返回 `LazyForEachAttribute` | `dataSource` 非 object / `itemGenerator` 非 function 不构造 | AC-1.1,AC-1.9 |
| R-2 | 行为 | static 范式构造 | 经 ANI `ConstructLazyForEachNode`→`ArkoalaLazyNode`；options 四参/style-builder 为 `@since26`/`@since26 staticonly` | style-builder 仅 staticonly，dynamic 无 | AC-1.3,AC-1.4,AC-1.5 |
| R-3 | 行为 | 父容器按 index 请求子节点 | `GetFrameChildByIndex`→`GetChildByIndex` 三级缓存查找后实构建 | — | AC-2.1,AC-2.3 |
| R-4 | 边界 | `index >= totalCount` | 返回 `nullptr`，不构建 | index 为 uint32 比较 | AC-2.2 |
| R-5 | 行为 | `isCache=true/false` 读 `expiringItem_` | cache 读返回副本不提升；非 cache 读提升回 `cachedItems_` 并擦除 expiring | — | AC-2.4 |
| R-6 | 行为 | 省略 `keyGenerator` | 默认 key=`viewId + "-" + index` | key 与数据内容无关 | AC-3.1 |
| R-7 | 行为 | 提供用户 `keyGenerator` | 返回值注入 `viewId + "-"` 前缀 | 非 string/number 回退 index（仍加前缀） | AC-3.2,AC-3.3 |
| R-8 | 异常 | 同一 LazyForEach 内 key 重复 | `try_emplace` 失败→`Use repeat key` 告警→`ProcessOffscreenNode` 丢弃，不抛异常 | 日志 tag `ACE_LAZY_FOREACH` | AC-3.4 |
| R-9 | 行为 | 实例构造管线选择 | `IsCurrentUseNewPipeline()` 选 NG/legacy；`NG_BUILD` 裁剪 legacy | — | AC-1.6,AC-1.7 |
| R-10 | 边界 | 默认 index-key 下数据源重排/交换/删除 | 无法识别内容迁移，可能渲染错位 | 需内容型 keyGenerator 规避 | AC-3.5,AC-3.6 |
| R-11 | 边界 | `cachedCount = 0` | 仍预构建可视窗口；范围 `cacheCount_ - showCached` | 内存压力下 `ReduceCacheCount` 上限 `maxCacheCount=2` | AC-4.1,AC-4.2 |
| R-12 | 行为 | 节点移出活跃区间 | `SetActive(false)`+移入 `expiringItem_` 二级池（非销毁） | 重复 key 越界项交 `ProcessOffscreenNode(true)` 释放 | AC-4.3,AC-4.4 |
| R-13 | 行为 | 帧间空闲 | `PostIdleTask` 以 deadline 型 `AddPredictTask` 预构建 + 渐进释放 `RemovingExpiringItem` | 任务源 `LazyForEachIdleTaskSource` | AC-4.5 |
| R-14 | 边界 | `PreBuild` 超 deadline | 记录 `preBuildingIndex_`，下次续建 | `PreBuildByIndex` 顶部 deadline 校验 | AC-4.6 |
| R-15 | 行为 | 任一数据变更 | 统一 `PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT` + `MarkNeedSyncRenderTree(true)` | 自测量+父测量+渲染树重同步 | AC-4.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 构造/重载/派发 | `lazy_for_each_model_test_ng`、`lazy_for_each_syntax_test_ng` | NG/legacy/Arkoala 三路径、参数校验、返回值类型随版本 |
| VM-2 | AC-2.x 按需生成 | `lazy_for_each_builder_syntax_test_ng` + `mock_lazy_foreach_builder.h` | 三级缓存命中顺序、nullptr 边界、BuildAllChildren/Swiper 分支 |
| VM-3 | AC-3.x key 契约 | `lazy_for_each_builder_syntax_test_ng(_advanced)` | 默认 key 串、前缀注入、非 string/number 回退、重复 key 告警丢弃 |
| VM-4 | AC-4.x 虚拟滚动 | `lazy_for_each_syntax_test_ng(_2)`、`lazy_for_each_builder_syntax_test_ng(_advanced)`、benchmark | cachedCount=0 仍缓存、越界入池/提升回、pre-build deadline 续建、PROPERTY_UPDATE 标记 |
| VM-5 | 兼容性/版本矩阵 | XTS（dynamic/static 双范式）+ d.ts/d.ets 比对 | `@since7/12/23/26` 行为边界、C-API 与 ArkTS 监听器注册差异 |

## API 变更分析

> 本特性为存量补录，无新增/变更 API。下列为本特性覆盖的既有 API 清单（声明层视图），签名/d.ts 位置/权限等实现细节见 design.md。

### 新增 API

N/A，API 行为无新增。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `LazyForEach(dataSource,itemGenerator,keyGenerator?)`（dynamic） | 既有 | `@since7` 基本构造，`@since12` 返回值改为 `LazyForEachAttribute` | — | AC-1.1 |
| `LazyForEach(...,options?)`（dynamic `@since26`） | 既有（版本扩展） | 新增 options 第四参 | 选项语义见 Feat-04 | AC-1.2 |
| `LazyForEach<T>(...)`（static `@since23`） | 既有 | static 范式入口 | — | AC-1.3 |
| `LazyForEach(style)`（static `@since26 staticonly`） | 既有（版本扩展） | style-builder 仅静态 | dynamic 无对应形态 | AC-1.5 |
| `LazyForEachAttribute` 静态方法（`debugLine`/`setLazyForEachOptions`/`applyAttributesFinish`） | 既有（`@since26 staticonly`） | 仅静态范式暴露 | dynamic `LazyForEachAttribute` 为空类 | AC-1.8 |

> SDK 契约交叉核对：dynamic `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts`；static `interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets`。

## 接口规格

### 接口定义

**LazyForEach（dynamic，`lazy_for_each.d.ts:1015,1035`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `LazyForEach(dataSource: IDataSource, itemGenerator: (item: any, index: number) => void, keyGenerator?: (item: any, index: number) => string, options?: LazyForEachOptions): LazyForEachAttribute` |
| 返回值 | `LazyForEachAttribute` — `@since12` 起；`@since7-11` 返回 `LazyForEachInterface` |
| 开放范围 | Public（`@FaAndStageModel`、crossplatform `@since10`、atomicservice `@since11`、`@noninterop`） |
| 错误码 | N/A（参数非法由 `ParseAndVerifyParams` 拦截，不抛错误码） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.9 |

**LazyForEach（static，`lazyForEach.static.d.ets:768,787,804`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `LazyForEach<T = Any>(dataSource: IDataSource<T>, itemGenerator: ItemGeneratorFunc<T>, keyGenerator?: KeyGeneratorFunc<T>, options?: LazyForEachOptions): LazyForEachAttribute`（含 style-builder `@since26 staticonly` 重载） |
| 返回值 | `LazyForEachAttribute`（`@since23`） |
| 开放范围 | Public（`@noninterop`） |
| 错误码 | N/A |
| 关联 AC | AC-1.3,AC-1.4,AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| dataSource | `IDataSource`/`IDataSource<T>` | 是 | — | 必须实现 totalCount/getData/register/unregister（契约详见 Feat-02）；非 object 不构造 |
| itemGenerator | `(item,index)=>void`/`ItemGeneratorFunc<T>` | 是 | — | 必须为 function；回调内通过 ViewStack 驱动子树构建 |
| keyGenerator | `(item,index)=>string`/`KeyGeneratorFunc<T>` | 否 | `viewId + "-" + index` | 非 string/number 返回回退 index；重复 key 静默丢弃（R-8） |
| options | `LazyForEachOptions` | 否 | — | `@since26`；customComponentFreezeMode/releaseStrategy/memoryOptimizationStrategy（详见 Feat-04） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | dynamic `@since7` 三参调用 | 经 `JSLazyForEach::Create` 构造 NG 或 legacy 节点 | AC-1.1,AC-1.6 |
| 2 | static `@since26 staticonly` style-builder 调用 | 经 ANI 创建 `ArkoalaLazyNode`，返回 `LazyForEachAttribute` | AC-1.3,AC-1.5,AC-1.7 |
| 3 | `keyGenerator` 省略 | 默认 key=`viewId-index` | AC-3.1 |
| 4 | 用户 `keyGenerator` 返回 object（非 string/number） | 回退 index 并加 `viewId-` 前缀 | AC-3.3 |
| 5 | 同实例 key 重复 | `Use repeat key` 告警 + `ProcessOffscreenNode` 丢弃，不中断 | AC-3.4 |
| 6 | `index >= totalCount` 请求 | 返回 `nullptr`，不构建 | AC-2.2 |
| 7 | `cachedCount=0` | 仍预构建可视窗口 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为差异：`LazyForEachAttribute` 返回值在 dynamic 侧 `@since7-11` 为 `LazyForEachInterface`、`@since12` 起为 `LazyForEachAttribute`；静态属性面方法（`debugLine`/`setLazyForEachOptions`/`applyAttributesFinish`）为 `@since26 staticonly`，dynamic 侧无。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since7`；static `@since23`。
- **API 版本号策略:** 按 SDK `.d.ts`/`.static.d.ets` 的 `@since` 标注，逐能力标注版本矩阵（见概述「目标版本」）。

> **版本/变体边界风险（F4）：** 自动注册数据变更监听器的 `Container::GreatOrEqualAPIVersion(PlatformVersion::VERSION_TWENTY_SIX)` 门控（`lazy_for_each_node.cpp:86-96`）**仅作用于 C-API/NodeAdapter 路径**（唯一调用方 `node_adapter_impl.cpp:473` 的 `CreateLazyForEachNode`）；dynamic ArkTS 路径 `GetOrCreateLazyForEachNode`（`lazy_for_each_node.cpp:37-60`，line 52）**无条件**注册监听器，无版本门。该 ArkTS 与 C-API 的注册时机差异是下游兼容性需关注的点。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 三级缓存模型 | `cachedItems_`（L1 活跃）→`expiringItem_`（L2 离屏池）→实构建，决定按需生成与回收语义 | AC-2.3,AC-4.3,AC-4.4 |
| 父容器驱动 cachedCount | cachedCount 由父容器（List/Grid/Swiper Pattern）经 `OnSetCacheCount` 下发，LazyForEach 自身默认 0 | AC-4.1 |
| 有序 ±1 布局访问 | `LazyLayoutWrapperBuilder` 强制对活跃窗口 ±1 步进访问，越序返回 nullptr，父容器布局算法须遵守 | AC-4.8 |
| 数据变更测量标记 | 任一数据变更统一 `PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT`，父容器必然重测量 | AC-4.7 |
| key 命名空间隔离 | 所有 key（含用户生成）恒带 `viewId-` 前缀，跨实例天然隔离 | AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 长列表滚动帧率不劣于基线（按需构建+预构建保障） | `test/benchmark` 帧率基准 + XTS | `lazy_for_each_node.cpp:132-171`（predict task） |
| 内存 | 离屏节点入 `expiringItem_` 池而非销毁，内存压力下渐进释放（`maxCacheCount=2`） | UT + 内存 dump | `lazy_for_each_builder.cpp:1282-1302,1467-1474` |
| 可靠性 | 重复 key/越界 index 不崩溃（静默丢弃/nullptr） | UT 异常用例 | `lazy_for_each_builder.cpp:919-1022`、`lazy_for_each_node.cpp:427` |
| 可测试性 | 暴露 `mock_lazy_foreach_actuator.h`/`mock_lazy_foreach_builder.h` 供 UT 注入 | UT | `test/unittest/core/syntax/` |

> 功耗/安全/自动化维测/定界定位：适用项见 proposal.md 不涉及项确认；本特性无独立指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | cachedCount/active range 行为一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上；内存压力下 `ReduceCacheCount` 触发 | XTS | `lazy_for_each_builder.cpp:1467-1474` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 子节点按需生成，离屏节点 `SetActive(false)` 不进入无障碍树活跃集 | AC-4.3 |
| 大字体 | 否 | 无独立处理，随父容器布局重测量 | — |
| 深色模式 | 是 | `NotifyColorModeChange`（`lazy_for_each_node.cpp:98`）下发子节点主题 scope | — |
| 多窗口/分屏 | 是 | 窗口 hide/show 触发 cache clean/restore（内存优化详见 Feat-04） | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 见兼容性声明版本矩阵与 C-API/ArkTS 监听器注册差异（F4） | AC-1.6,兼容性声明 |
| 生态兼容 | 是 | crossplatform `@since10`、atomicservice `@since11`（dynamic） | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: LazyForEach 按需渲染与 key 契约
  作为 应用开发者
  我想要 仅构建可见区子节点并按 key 复用
  以便 长列表滚动流畅且内存可控

  Scenario: 省略 keyGenerator 使用默认序号 key
    Given LazyForEach 未提供 keyGenerator
    When 框架为 index=3 生成 key
    Then key 等于 "<viewId>-3"（与数据内容无关）

  Scenario: 用户 keyGenerator 返回值被注入前缀
    Given 用户提供 keyGenerator 返回 "item-007"
    When 框架生成最终 key
    Then 最终 key 等于 "<viewId>-item-007"

  Scenario Outline: 越界与重复 key 处理
    Given 一个 LazyForEach 实例
    When <触发>
    Then <预期>

    Examples:
      | 触发 | 预期 |
      | 请求 index >= totalCount | 返回 nullptr，不构建 |
      | 同实例出现重复 key | 输出 "Use repeat key" 告警并丢弃重复项，不中断渲染 |
      | cachedCount 设为 0 | 仍预构建可视窗口 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做构造/按需生成/key 契约/虚拟滚动；数据通知/批量变更/选项优化/onMove 分别由 Feat-02~05 承接）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachNode::GetFrameChildByIndex 三级缓存命中顺序与越界 nullptr 处理"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachBuilder key 重复 try_emplace 冲突检测与 ProcessOffscreenNode 丢弃"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEach PostIdleTask deadline 预构建与 preBuildingIndex_ 续建"
  - repo: "openharmony/arkui_ace_engine"
    query: "ArkoalaLazyNode 静态构造入口与 LazyForEachModelNG::Create 路径差异"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts`、`interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets`、`frameworks/core/components_ng/syntax/lazy_for_each_node.cpp`、`frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp`、`docs/syntax/LazyForEach_Knowledge_Base.md`
