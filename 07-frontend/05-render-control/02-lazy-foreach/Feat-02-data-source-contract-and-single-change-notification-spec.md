# 特性规格

> Func-07-05-02-Feat-02 数据源契约与单条变更通知：固化 `IDataSource`（totalCount/getData/registerDataChangeListener/unregisterDataChangeListener，注册期不校验、调用期静默降级）、监听器注册生命周期（NG `LazyForEachNode` 自为 `V2::DataChangeListener` 无条件注册 / C-API NodeAdapter API≥26 门控 / legacy `DefaultDataChangeListener`）、`DataChangeListener` 单条 API（onDataReloaded/Add/Delete/Move/Change 与 `@since7` 弃用别名 onDataAdded/Moved/Deleted/Changed 等价零差异、`@since26.1` `onDataReloaded(reuseImmediately)`）、单条 API 与 onDatasetChange 互斥守卫、reuseImmediately key 后缀立即回收机制行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 数据源契约与单条变更通知 |
| 特性编号 | Func-07-05-02-Feat-02 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since7`（IDataSource/单条 API）/ `@since8`（onDataAdd/Move/Delete/Change 现行名）/ `@since12`（onDatasetChange 互斥）/ `@since26.1`（onDataReloaded(reuseImmediately)）；static `@since23`（IDataSource/单条 API，无弃用形式） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性承接 Feat-01（核心语法与按需渲染）的数据侧契约；批量数据集变更 `onDatasetChange`（Feat-03）、选项策略与内存优化（Feat-04）、拖拽排序 onMove（Feat-05）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/02-lazy-foreach/design.md` | Baselined |
| Dynamic API（SDK 契约） | `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts` | — |
| Static API（SDK 契约） | `interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets` | — |
| JS 执行器（dataSource 持有/方法提取） | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach_actuator.h` | — |
| JS 变更监听代理 | `frameworks/bridge/declarative_frontend/jsview/js_data_change_listener.h` | — |
| JS 桥接绑定 | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach.cpp` | — |
| NG Builder（listener 虚函数/getData 调用） | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach_builder.h` | — |
| legacy 组件（DefaultDataChangeListener） | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach_component.h` | — |
| NG 语法节点（OnData* 单条处理/注册生命周期） | `frameworks/core/components_ng/syntax/lazy_for_each_node.cpp` / `.h` | — |
| NG 缓存引擎（OnDataReloaded/reuseImmediately/ReleaseExpiringNode） | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` / `.h` | — |
| 数据源契约 C++ 接口（V2::DataChangeListener/Operation） | `frameworks/core/components_v2/foreach/lazy_foreach_component.h` | — |
| C-API NodeAdapter 注册调用方 | `frameworks/core/interfaces/native/node/node_adapter_impl.cpp` | — |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md。design.md 与本文档并行产出/增量合并，互不依赖。

---

## 用户故事

### US-1: IDataSource 数据源契约

**作为** 应用开发者,
**我想要** 实现 `IDataSource` 的四个方法（totalCount/getData/register/unregister）作为 LazyForEach 的数据供给,
**以便** 框架按需查询总数与数据项，并在数据变化时接收通知。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 应用提供实现四方法的 `IDataSource` 对象 THEN `JSLazyForEachActuator::SetDataSourceObj`（`js_lazy_foreach_actuator.h:157-164`）经 `GetFunctionFromObject` 提取 `totalCount`/`getData`/`registerDataChangeListener`/`unregisterDataChangeListener` 四个 function 引用 | 正常 |
| AC-1.2 | WHEN 框架需要数据项总数 THEN 经 `OnGetTotalCount`（`js_lazy_foreach_builder.h:42-45`）→`GetTotalIndexCount` 调用 `totalCountFunc_->Call(dataSourceObj_)`（`js_lazy_foreach_actuator.h:90`），结果作为 `FrameCount()` 用于按需生成 bounds check（`lazy_for_each_node.h:67-70`） | 正常 |
| AC-1.3 | WHEN 框架按需构建 index 对应子项 THEN `OnGetChildByIndex(New)` 内 `CallJSFunction(getDataFunc_, dataSourceObj_, index)`（`js_lazy_foreach_builder.h:143,200`）取数据项并交 `itemGenerator` 构建子树 | 正常 |
| AC-1.4 | WHEN `IDataSource` 缺失 `totalCount`（非 function）THEN `GetFunctionFromObject` 返回空 `JSRef`（`js_lazy_foreach_actuator.h:195-202`），`GetTotalIndexCount` 命中 `if (totalCountFunc_.IsEmpty()) return 0`（`:85-87`），即 totalCount 视为 0、不生成任何子项，**不报错** | 异常 |
| AC-1.5 | WHEN `IDataSource` 缺失 `getData` THEN `OnGetChildByIndex(New)` 命中 `if (getDataFunc_.IsEmpty()) return info`（`js_lazy_foreach_builder.h:138-140,195-197`），返回空 info、不构建子树，**不报错** | 异常 |
| AC-1.6 | WHEN `IDataSource` 缺失 `registerDataChangeListener`/`unregisterDataChangeListener` THEN `RegisterListener`/析构直接 return（`js_lazy_foreach_actuator.h:112-114,74`），监听器不注册/不解注册，**不报错** | 异常 |
| AC-1.7 | WHEN 单条 API 入参 index 为负数 THEN `ConvertFromJSCallbackInfo` 将其 clamp 到 0（`js_data_change_listener.h:62-75`） | 边界 |

### US-2: 监听器注册与生命周期

**作为** 应用开发者,
**我想要** 在 `registerDataChangeListener` 中拿到监听器对象、用它通知数据变化，并在组件销毁时自动解注册,
**以便** 数据变化能驱动 LazyForEach 增量更新且无内存泄漏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 首次 `registerDataChangeListener` 被调用 THEN 创建内部类 `__ohos_ace_inner_JSDataChangeListener__` 的 JS 代理（`js_lazy_foreach.cpp:66`、`js_lazy_foreach_actuator.h:116`），把 C++ 监听器 `AddListener` 入 `listeners_`（`:122`），再以该代理为参回调应用的 `registerDataChangeListener`（`:126-127`） | 正常 |
| AC-2.2 | WHEN 应用持有该代理 THEN 其暴露的方法名为 `onDataReloaded`/`onDataAdd`/`onDataDelete`/`onDataMove`/`onDataChange`（及弃用别名）等（`js_lazy_foreach.cpp:68-88`），调用即经 `NotifyAll` 遍历 `listeners_` 派发到所有注册的 C++ 监听器（`js_data_change_listener.h:326-368`） | 正常 |
| AC-2.3 | WHEN NG 路径构造节点 THEN `LazyForEachNode` 自身继承 `V2::DataChangeListener`（`lazy_for_each_node.h:45`），`RegisterBuilderListener`（`:173-179`，`isRegisterListener_` 守卫）调用 `builder_->RegisterDataChangeListener(Claim(this))` 把自己注册为监听器 | 正常 |
| AC-2.4 | WHEN dynamic ArkTS 路径经 `GetOrCreateLazyForEachNode` 构造 THEN **无条件** `RegisterBuilderListener()`（`lazy_for_each_node.cpp:52`，仅新建分支） | 正常 |
| AC-2.5 | WHEN C-API NodeAdapter 路径经 `CreateLazyForEachNode` 构造（唯一调用方 `node_adapter_impl.cpp:473`）THEN **仅 API≥26** 时 `RegisterBuilderListener()`（`lazy_for_each_node.cpp:92-94`）；API<26 须应用侧显式触发注册 | 边界 |
| AC-2.6 | WHEN `LazyForEachNode` 析构（`OnDelete` `:62-70` / 析构函数 `:72-84`）THEN 若 `isRegisterListener_` 则 `builder_->UnregisterDataChangeListener(this)` 并复位标志（`:65,:80`），监听器随节点销毁解注册 | 正常 |
| AC-2.7 | WHEN legacy 组件树路径 THEN `JSLazyForEachComponent::ExpandChildren` 创建 `DefaultDataChangeListener`（`js_lazy_foreach_component.h:179-187`），其每个 `OnData*` 覆写仅调用 `parentView_->MarkNeedUpdate()`（`:30-89`）；NG 路径不使用该默认监听器 | 正常 |
| AC-2.8 | WHEN 多个监听器注册 THEN `JSDataChangeListener::listeners_`（`std::set<WeakPtr<V2::DataChangeListener>>`，`js_data_change_listener.h:370`）支持多监听器（`AddListener`/`RemoveListener` `:36-44`），但实践中每 builder 仅注册一个（NG 为 `LazyForEachNode`，legacy 为 `DefaultDataChangeListener`） | 边界 |

### US-3: 单条数据变更通知

**作为** 应用开发者,
**我想要** 通过监听器对象的 `onDataReloaded`/`onDataAdd`/`onDataDelete`/`onDataMove`/`onDataChange` 通知单条数据变化,
**以便** 框架增量更新对应子节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `onDataReloaded()` THEN 派发 `LazyForEachNode::OnDataReloaded(false)`（`lazy_for_each_node.cpp:173-194`）→`builder_->OnDataReloaded(false)`（`:182`），全量重载；若 `FrameCount()==0` 额外 `PostIdleTask(ON_DATA_RELOADED)`（`:184`） | 正常 |
| AC-3.2 | WHEN 调用 `onDataAdd(index)` THEN 派发 `OnDataAdded(index)`（`lazy_for_each_node.cpp:196-211`）→`builder_->OnDataAdded(index)`（`:202`） | 正常 |
| AC-3.3 | WHEN 调用 `onDataDelete(index)` THEN 派发 `OnDataDeleted(index)`（`lazy_for_each_node.cpp:230-261`）→`builder_->OnDataDeleted(index)`（`:236`），返回节点加入 disappearing children 或 detach，重复/越界项交 `ProcessOffscreenNode(node, true)`（`:243`） | 正常 |
| AC-3.4 | WHEN 调用 `onDataChange(index)` THEN 派发 `OnDataChanged(index)`（`lazy_for_each_node.cpp:293-307`）→`builder_->OnDataChanged(index)`（`:298`） | 正常 |
| AC-3.5 | WHEN 调用 `onDataMove(from,to)` THEN 派发 `OnDataMoved(from,to)`（`lazy_for_each_node.cpp:356-370`）→`builder_->OnDataMoved(from,to)`（`:360`） | 正常 |
| AC-3.6 | WHEN 任一单条 API 触发 THEN handler 置 `builder_->SetUseNewInterface(false)` 走 legacy 差分路径，并以 `MarkNeedSyncRenderTree(true)`（受 `needMarkParent_` 门控，`lazy_for_each_node.cpp:414-419`）+`MarkNeedFrameFlushDirty(PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT)` 收尾（`:209-210,:259-260,:305-306,:368-369,:192-193`） | 正常 |
| AC-3.7 | WHEN 调用弃用名 `onDataAdded`/`onDataMoved`/`onDataDeleted`/`onDataChanged`（`@since7`，`@since8` 弃用）THEN 与现行名 `onDataAdd`/`onDataMove`/`onDataDelete`/`onDataChange` **别名到同一处理器**（`js_lazy_foreach.cpp:71-72,74-75,77-78,80-81`），**零行为差异、无运行时弃用告警**，弃用信号仅存在于 SDK JSDoc `@deprecated since 8 / @useinstead`（`lazy_for_each.d.ts:671-672,708-709,746-747,781-782`） | 正常 |
| AC-3.8 | WHEN 同一 `JSDataChangeListener` 实例已触发过任一单条 API 后再调用 `onDatasetChange`（或反之）THEN 粘性 per-instance JS 守卫 `UseAnotherInterface` 抛 `ERROR_CODE_PARAM_INVALID`「onDatasetChange cannot be used with other interface」并 no-op（`js_data_change_listener.h:316-324`）；该守卫**仅作用于 JS 桥接**，C++ 直接调用 `V2::DataChangeListener` 方法不受约束 | 异常 |

### US-4: reuseImmediately 立即回收

**作为** 应用开发者,
**我想要** 在 `onDataReloaded(true)`（`@since26.1`）时把离屏节点立即交给父自定义组件复用池,
**以便** 大规模重载场景下离屏节点被父 CustomNode 复用而非被 LazyForEach 自身缓存。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `onDataReloaded(reuseImmediately: boolean)`（`@since26.1` dynamic）THEN JS 布尔经 `NotifyAll(&V2::DataChangeListener::OnDataReloaded, reuseImmediately)`（`js_data_change_listener.h:84-88`）传入 `LazyForEachBuilder::OnDataReloaded(bool)`（`lazy_for_each_builder.cpp:66-98`） | 正常 |
| AC-4.2 | WHEN `reuseImmediately == false` THEN `CHECK_EQUAL_VOID(reuseImmediately, false)` 提前 return（`lazy_for_each_builder.cpp:81`），走普通重载路径（仅把 `cachedItems_` 移入 `expiringItem_`、置 needTransition） | 边界 |
| AC-4.3 | WHEN `reuseImmediately == true` THEN 对每个 expiring 节点 `TryRecordRecyclableNodeRecursively`（`lazy_for_each_builder.cpp:84-88,1597-1613`）查找 `RECYCLE_VIEW_ETS_TAG` 子且其直接子为 `CustomNode`，按 CustomNode 的 reuseId 记入 `recyclableNodeSet_` | 正常 |
| AC-4.4 | WHEN 记录可回收节点后 THEN 给 `expiringItem_` **所有 key 追加 `"__MarkedByReuseImmediately__Internal"` 后缀**（`lazy_for_each_builder.cpp:91-95`），使 LazyForEach 级 key 匹配复用无法命中这些节点，从而绕过 LazyForEach 自身复用 | 正常 |
| AC-4.5 | WHEN 后缀化完成 THEN `EnableParentCustomNodeReleaseExpiringNode(reuseIds)`（`:96-97`）把候选 reuseId 经 `LazyForEachNode::EnableParentCustomNodeReleaseExpiringNode`（`lazy_for_each_node.cpp:1051-1058`，一次性 `isParentCustomNodeReleaseExpiringNodeEnabled_` 守卫）注册父 CustomNode 为释放方 | 正常 |
| AC-4.6 | WHEN 父 CustomNode 请求释放某 reuseId THEN `LazyForEachNode::ReleaseExpiringNode`（`lazy_for_each_node.cpp:1070-1073`）转发 `builder_->ReleaseExpiringNode(reuseId)`（`lazy_for_each_builder.cpp:1533-1575`），按 key 累计释放直到 `releasedCount >= MIN_RELEASE_COUNT=5`（`:1535,1545-1546`）或桶空；每节点 `NotifyDataDeleted`+`ProcessOffscreenNode(true)`+`NotifyItemDeleted`+detach+erase | 正常 |
| AC-4.7 | WHEN 预构建完成 THEN `PostIdleTask` 内 `DisableParentCustomNodeReleaseExpiringNode()`（`lazy_for_each_node.cpp:161`）关闭父 CustomNode 释放授权 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.7 | R-1,R-2,R-8 | T-2 | UT：`lazy_for_each_syntax_test_ng` 注入缺方法 dataSource；Mock `mock_lazy_foreach_actuator.h` | `js_lazy_foreach_actuator.h:85-202`、`js_lazy_foreach_builder.h:138-200` |
| AC-2.1~2.8 | R-3,R-4,R-5,R-9 | T-2 | UT：`lazy_for_each_model_test_ng` 注册/解注册；legacy `DefaultDataChangeListener` 路径 | `lazy_for_each_node.cpp:37-96,62-84`、`js_lazy_foreach_component.h:30-187` |
| AC-3.1~3.8 | R-6,R-7,R-10 | T-2 | UT：`lazy_for_each_builder_syntax_test_ng(_2/_advanced)` 单条 OnData* + 互斥守卫 | `js_lazy_foreach.cpp:64-91`、`lazy_for_each_node.cpp:173-370`、`js_data_change_listener.h:316-324` |
| AC-4.1~4.7 | R-11,R-12,R-13 | T-2 | UT：`lazy_for_each_builder_syntax_test_ng(_advanced)` reuseImmediately 后缀 + ReleaseExpiringNode 批量释放 | `lazy_for_each_builder.cpp:66-98,1533-1613` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 应用提供实现四方法的 IDataSource | `SetDataSourceObj` 提取四 function 引用 | 注册期不校验类型 | AC-1.1 |
| R-2 | 行为 | 框架查询总数/数据项 | `totalCount()`→FrameCount bounds check；`getData(index)`→itemGenerator | — | AC-1.2,AC-1.3 |
| R-3 | 行为 | 首次 registerDataChangeListener | 创建 JS 代理、AddListener 入 `listeners_`、回调应用 register | 代理内部类 `__ohos_ace_inner_JSDataChangeListener__` | AC-2.1,AC-2.2 |
| R-4 | 行为 | NG 节点构造 | `LazyForEachNode`（IS-A DataChangeListener）`RegisterBuilderListener` 注册自身 | `isRegisterListener_` 守卫防重 | AC-2.3 |
| R-5 | 边界 | ArkTS vs C-API 注册时机 | `GetOrCreateLazyForEachNode` 无条件注册；`CreateLazyForEachNode`（NodeAdapter）仅 API≥26 注册 | C-API 唯一调用方 `node_adapter_impl.cpp:473` | AC-2.4,AC-2.5 |
| R-6 | 行为 | 调用单条 onData* API | 派发到 builder 对应 OnData* op；置 SetUseNewInterface(false)+MEASURE_SELF_AND_PARENT+MarkNeedSyncRenderTree | MarkNeedSyncRenderTree 受 needMarkParent_ 门控 | AC-3.1~3.6 |
| R-7 | 行为 | 调用弃用名单条 API | 与现行名别名到同一处理器，零行为差异、无运行时告警 | 弃用信号仅 JSDoc @deprecated since 8 | AC-3.7 |
| R-8 | 异常 | IDataSource 缺失某方法 | 调用期静默降级（totalCount→0/getData→空/不注册监听），不报错 | 缺失在注册期不被发现 | AC-1.4~1.6 |
| R-9 | 行为 | 节点销毁 | OnDelete/析构解注册监听器并复位标志 | 监听器随节点生命周期 | AC-2.6 |
| R-10 | 异常 | 单条 API 与 onDatasetChange 混用 | 粘性 per-instance JS 守卫抛 ERROR_CODE_PARAM_INVALID 并 no-op | 仅 JS 桥接约束，C++ 直接调用不受限 | AC-3.8 |
| R-11 | 行为 | onDataReloaded(true)（@since26.1） | 记录 RECYCLE_VIEW/CustomNode 可回收节点 + expiring key 加 `__MarkedByReuseImmediately__Internal` 后缀绕过 LazyForEach 复用 | false 时走普通重载 | AC-4.1~4.4 |
| R-12 | 行为 | 父 CustomNode 请求释放 reuseId | `ReleaseExpiringNode` 按 key 累计释放至 `releasedCount>=5` 或桶空 | MIN_RELEASE_COUNT=5 | AC-4.5,AC-4.6 |
| R-13 | 恢复 | 预构建完成 | `DisableParentCustomNodeReleaseExpiringNode` 关闭父 CustomNode 释放授权 | 一次性启用/关闭 | AC-4.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x IDataSource 契约 | `lazy_for_each_syntax_test_ng` + `mock_lazy_foreach_actuator.h` | 四方法提取、totalCount/getData 调用、缺方法静默降级 |
| VM-2 | AC-2.x 监听器生命周期 | `lazy_for_each_model_test_ng` | 代理创建/注册/解注册、ArkTS 无条件 vs C-API API26 门控、legacy 默认监听 |
| VM-3 | AC-3.x 单条通知 | `lazy_for_each_builder_syntax_test_ng(_2/_advanced)` | 五单条 op 派发、弃用别名等价、互斥守卫 ERROR_CODE_PARAM_INVALID |
| VM-4 | AC-4.x reuseImmediately | `lazy_for_each_builder_syntax_test_ng(_advanced)` | key 后缀化、绕过 LazyForEach 复用、MIN_RELEASE_COUNT=5 批量释放 |
| VM-5 | 兼容性/版本矩阵 | XTS（dynamic/static 双范式）+ d.ts/d.ets 比对 | `@since7/8/12/23/26.1` 边界、static 无弃用形式 |

## API 变更分析

> 存量补录，无新增/变更 API。下列为本特性覆盖的既有 API 清单（声明层视图）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `IDataSource.{totalCount,getData,registerDataChangeListener,unregisterDataChangeListener}`（dynamic `@since7`） | 既有 | 数据供给契约 | 实现详见 Feat-02 US-1 | AC-1.1~1.6 |
| `DataChangeListener.onDataAdded/onDataMoved/onDataDeleted/onDataChanged`（dynamic `@since7`） | 废弃（`@since8` 弃用） | 与现行名别名等价，无运行时差异 | `@useinstead onDataAdd/onDataMove/onDataDelete/onDataChange` | AC-3.7 |
| `DataChangeListener.onDataAdd/onDataMove/onDataDelete/onDataChange`（dynamic `@since8`） | 既有 | 现行单条变更名 | — | AC-3.2~3.5 |
| `DataChangeListener.onDataReloaded(reuseImmediately)`（dynamic `@since26.1`） | 既有版本扩展 | 新增布尔重载 | false 走普通重载、true 触发立即回收 | AC-4.1 |
| `IDataSource<T>`/`DataChangeListener`（static `@since23`） | 既有 | static 范式契约，**无弃用形式** | onDataChange（非 onChange） | AC-1.1,AC-3.4 |

> SDK 契约交叉核对：dynamic `lazy_for_each.d.ts:689-948`；static `lazyForEach.static.d.ets:553-664`。

## 接口规格

### 接口定义

**IDataSource（dynamic，`lazy_for_each.d.ts:898`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `interface IDataSource { totalCount(): number; getData(index: number): any; registerDataChangeListener(listener: DataChangeListener): void; unregisterDataChangeListener(listener: DataChangeListener): void; }` |
| 返回值 | 见各方法 |
| 开放范围 | Public（`@since7`，`@FaAndStageModel`、crossplatform `@since10`、atomicservice `@since11`） |
| 错误码 | N/A（缺方法静默降级，不抛错误码） |
| 关联 AC | AC-1.1~1.6 |

**DataChangeListener 单条方法（dynamic，`lazy_for_each.d.ts:701,718,735,749,774,796,814,834,851,865`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onDataReloaded(): void` / `onDataReloaded(reuseImmediately: boolean): void`(`@since26.1`) / `onDataAdd(index): void` / `onDataMove(from,to): void` / `onDataDelete(index): void` / `onDataChange(index): void`（及弃用别名 onDataAdded/Moved/Deleted/Changed） |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | 与 onDatasetChange 混用→`ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-3.1~3.8,AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| totalCount | `() => number` | 是 | — | 缺失→返回 0（静默） |
| getData | `(index) => any` | 是 | — | 缺失→不构建子项（静默） |
| registerDataChangeListener | `(listener) => void` | 是 | — | 缺失→监听器不注册（静默） |
| unregisterDataChangeListener | `(listener) => void` | 是 | — | 缺失→析构跳过（静默） |
| onDataReloaded.reuseImmediately | boolean | 否 | false | `@since26.1`；true 触发立即回收 |
| onData*(index/from,to) | number | 是 | — | 负数 clamp 到 0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 缺 totalCount 的 dataSource | totalCount 视为 0，不生成子项，不报错 | AC-1.4 |
| 2 | 调用 onDataAdded（弃用） | 与 onDataAdd 等价，无运行时告警 | AC-3.7 |
| 3 | 单条 API 后调 onDatasetChange | 抛 ERROR_CODE_PARAM_INVALID 并 no-op | AC-3.8 |
| 4 | onDataReloaded(true) | expiring key 加后缀绕过 LazyForEach 复用，交父 CustomNode | AC-4.3,AC-4.4 |
| 5 | 父 CustomNode ReleaseExpiringNode | 按 key 释放至 ≥5 个或桶空 | AC-4.6 |
| 6 | C-API NodeAdapter API<26 构造 | 不自动注册监听器，须显式触发 | AC-2.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意既有行为：弃用单条 API（`@since7`，`@since8` 弃用）与现行名完全别名等价、**无运行时弃用告警**，仅 SDK JSDoc 标注；`onDataReloaded(reuseImmediately)` 为 `@since26.1` 新增重载。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since7`；static `@since23`。
- **API 版本号策略:** 按 SDK `@since` 标注（见概述「目标版本」）。

> **IDataSource 注册不校验风险（F1）：** `IDataSource` 四方法在 `SetDataSourceObj` 注册期**不校验**类型/存在性（`js_lazy_foreach_actuator.h:157-164,195-202`），缺失方法在**调用期静默降级**（totalCount→0、getData→空、不注册监听），**不抛错误码**。应用提供残缺 dataSource 不会得到任何错误反馈，仅表现为空列表/无更新（风险 RISK-F2-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 监听器=节点自身（NG） | NG 路径 `LazyForEachNode` 继承 `V2::DataChangeListener` 并注册自身；legacy 用 `DefaultDataChangeListener` | AC-2.3,AC-2.7 |
| 注册时机双路径 | ArkTS 无条件注册；C-API NodeAdapter API≥26 门控 | AC-2.4,AC-2.5 |
| 单条/批量互斥（JS 守卫） | 单条 API 与 onDatasetChange 在同一 JS 代理实例上互斥，C++ 直接调用不受限 | AC-3.8 |
| reuseImmediately 后缀隔离 | true 时 expiring key 加后缀，绕过 LazyForEach 级复用，交父 CustomNode | AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 残缺 dataSource 不崩溃（静默降级） | UT 异常用例 | `js_lazy_foreach_actuator.h:85-87,138-140` |
| 内存 | 监听器随节点销毁解注册，无泄漏 | UT 生命周期 | `lazy_for_each_node.cpp:62-84` |
| 性能 | reuseImmediately 大规模重载离屏节点交父池复用，避免 LazyForEach 缓存堆积 | UT + benchmark | `lazy_for_each_builder.cpp:66-98,1533-1575` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 数据源契约与无障碍无直接关联 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 弃用别名等价、`@since26.1` reuseImmediately、C-API API26 注册门控差异 | AC-2.5,AC-3.7,AC-4.1 |
| 生态兼容 | 是 | crossplatform `@since10`、atomicservice `@since11`（dynamic） | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: IDataSource 契约与单条变更通知
  作为 应用开发者
  我想要 实现 IDataSource 并用监听器通知单条数据变化
  以便 LazyForEach 增量更新且无内存泄漏

  Scenario: 残缺 dataSource 静默降级
    Given dataSource 未实现 totalCount
    When 框架查询总数
    Then 返回 0 且不生成任何子项，不抛错误

  Scenario: 弃用与现行单条 API 等价
    Given 一个已注册的监听器
    When 调用 onDataAdded(3)（弃用）
    Then 行为与 onDataAdd(3) 完全一致，无运行时告警

  Scenario Outline: 单条与批量互斥
    Given 同一监听器实例已调用过 <先调>
    When 再调用 <后调>
    Then 抛 ERROR_CODE_PARAM_INVALID 且 no-op

    Examples:
      | 先调 | 后调 |
      | onDataAdd | onDatasetChange |
      | onDatasetChange | onDataAdd |

  Scenario: reuseImmediately 立即回收
    Given expiringItem_ 中存在 CustomNode 子节点
    When 调用 onDataReloaded(true)
    Then expiring key 追加 __MarkedByReuseImmediately__Internal 后缀，绕过 LazyForEach 复用
    And 父 CustomNode 经 ReleaseExpiringNode 按 reuseId 批量释放（每批≥5）
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做 IDataSource 契约/监听器生命周期/单条通知/reuseImmediately；批量 onDatasetChange 详见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "JSLazyForEachActuator::SetDataSourceObj 提取四方法与缺失静默降级"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachNode RegisterBuilderListener 注册时机 ArkTS vs C-API API26"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachBuilder::OnDataReloaded(reuseImmediately) key 后缀 __MarkedByReuseImmediately__Internal"
  - repo: "openharmony/arkui_ace_engine"
    query: "JSDataChangeListener UseAnotherInterface 单条与 onDatasetChange 互斥守卫"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts`、`interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets`、`frameworks/bridge/declarative_frontend/jsview/js_data_change_listener.h`、`frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp`、`docs/syntax/LazyForEach_Knowledge_Base.md`
