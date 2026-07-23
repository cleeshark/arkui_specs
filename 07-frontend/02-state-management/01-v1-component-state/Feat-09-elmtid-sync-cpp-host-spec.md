# 特性规格

> Func-07-02-01-Feat-09 elmtId 全链路同步与 C++ 宿主集成：固化 `ElementRegister`（全局 elmtId 分配/回收/移除集）、`UINodeRegisterProxy`（elmtId→View 映射、双流程同步）、`moveDeletedElmtIds`（C++→TS 全链路同步）、`OnIdle`（空闲清理与强制回收阈值）、`stateMgmt.abc` 字节码载入、`CustomNode`/`CustomNodeBase`（C++ 宿主节点，V1/V2 共用 `isV2_`）、`ViewFunctions`（约 40 回调 C++ 分发）、`JSLocalStorage`/`JSPersistent`/`JSEnvironment` C++ 绑定行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | elmtId 全链路同步与 C++ 宿主集成 |
| 特性编号 | Func-07-02-01-Feat-09 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 7 起支持核心机制 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| UINodeRegisterProxy | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_uinode_registry_proxy.ts` | — |
| ElementRegister | `frameworks/core/pipeline/base/element_register.h` | — |
| CustomNode | `frameworks/core/components_ng/pattern/custom/custom_node.cpp/.h` | — |
| PipelineContext | `frameworks/core/pipeline_ng/pipeline_context.cpp` | — |
| JSLocalStorage | `frameworks/bridge/declarative_frontend/jsview/js_local_storage.cpp/.h` | — |
| Frontend 接口 | `frameworks/core/common/frontend.h` | — |

---

## 用户故事

### US-1: ElementRegister elmtId 分配与移除集

**作为** 框架维护者,
**我想要** `ElementRegister` 全局分配/回收 elmtId 并跟踪移除集,
**以便** 组件创建/删除时 elmtId 全局唯一且可同步清理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 组件创建需要新 elmtId THEN `ElementRegister.MakeUniqueId` 分配全局唯一 elmtId | 正常 |
| AC-1.2 | WHEN 组件删除 THEN `ElementRegister.RemoveItem(elmtId)` 将 elmtId 加入移除集（用于 TS 侧同步清理） | 正常 |
| AC-1.3 | WHEN 组件复用重注册 THEN `ElementRegister.RemoveItemSilently(elmtId)` 跳过移除集（用于复用场景重注册） | 边界 |

### US-2: UINodeRegisterProxy 双流程同步

**作为** 框架维护者,
**我想要** `UINodeRegisterProxy` 维护 elmtId→View 映射并通过双流程同步已删除 elmtId,
**以便** 避免悬挂引用与内存泄漏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 组件创建 THEN elmtId→View 注册到 `UINodeRegisterProxy.ElementIdToOwningViewPU_`（`pu_uinode_registry_proxy.ts`） | 正常 |
| AC-2.2 | WHEN 流程 A（延迟）THEN 下次重渲染 `purgeDeletedElmtIds` 时清理已删除 elmtId 的依赖 | 正常 |
| AC-2.3 | WHEN 流程 B（即时）THEN `aboutToBeDeleted` + `PipelineContext::OnIdle` 经 `uiNodeCleanUpIdleTask` 即时清理 | 正常 |
| AC-2.4 | WHEN 双流程协同 THEN A 兜底延迟清理，B 即时清理，确保无悬挂引用 | 正常 |

### US-3: moveDeletedElmtIds 全链路同步

**作为** 框架维护者,
**我想要** C++ 侧删除的 elmtId 经 `moveDeletedElmtIds` 全链路同步到 TS 侧,
**以便** TS 侧 `UINodeRegisterProxy` 与 `PropertyDependencies` 清理对应依赖。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN C++ `ElementRegister::RemoveItem` 将 elmtId 加入移除集 THEN 移除集累积待同步的 elmtId | 正常 |
| AC-3.2 | WHEN 移除集同步到 TS THEN `moveDeletedElmtIds` 将已删除 elmtId 列表传给 TS | 正常 |
| AC-3.3 | WHEN TS 收到已删除 elmtId 列表 THEN `unregisterElmtIdsFromIViews` 注销对应 View，清理 `PropertyDependencies` 中的依赖 | 正常 |

### US-4: OnIdle 空闲清理与强制回收

**作为** 框架维护者,
**我想要** `PipelineContext::OnIdle` 在空闲时执行清理，并有强制回收阈值防 OOM,
**以便** 避免状态管理清理任务堆积导致内存溢出。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 管线空闲 THEN `OnIdle` 执行 `CallStateMgmtCleanUpIdleTaskFunc`（经 `frontend.h` 虚函数反向调用 TS `uiNodeCleanUpIdleTask`） | 正常 |
| AC-4.2 | WHEN 组件未正常注销（JS 忘记调 `aboutToBeDeleted`）THEN `MAX_FRAME_COUNT_WITHOUT_JS_UNREGISTRATION=100` 帧后强制回收，防 OOM | 边界 |
| AC-4.3 | WHEN `PipelineContext::GetStateMgmtInfo(nodeIds, propertyName, jsonPath)` THEN 上报给 `UiSessionManager`（2000ms 超时），用于 Inspector 查询 | 正常 |
| AC-4.4 | WHEN `PipelineContext::RecordStateMgmtNode` THEN 记录 dirty node 计数用于性能监控 | 正常 |

### US-5: stateMgmt.abc 字节码载入与 CustomNode 宿主

**作为** 框架维护者,
**我想要** `stateMgmt.abc` 在引擎初始化时载入，`CustomNode` 作为 `@Component`/`@ComponentV2` 的 C++ 宿主节点,
**以便** TS 状态管理运行时与 C++ 渲染管线对接。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 引擎初始化 THEN `_binary_stateMgmt_abc_start` 载入 `stateMgmt.abc` 字节码（编译自 `stateMgmt` TS 库） | 正常 |
| AC-5.2 | WHEN `@Component`/`@ComponentV2` 组件创建 THEN C++ 侧创建 `CustomNode`（继承 `UINode` + `CustomNodeBase`）作为宿主节点 | 正常 |
| AC-5.3 | WHEN V1 组件 THEN `CustomNode` 的 `isV2_=false`；V2 组件 `isV2_=true`（V1/V2 共用同一 C++ 宿主） | 正常 |
| AC-5.4 | WHEN `CustomNodeBase` 持有约 20 个 `std::function` 回调 THEN 这些回调连接到 TS 侧的 `ViewPU`/`ViewV2` 方法 | 正常 |
| AC-5.5 | WHEN `CustomNode` 析构 THEN appear/destroy 回调配对（确保生命周期完整） | 边界 |
| AC-5.6 | WHEN `CustomNodePattern`/`CustomNodeLayoutAlgorithm` THEN 处理自定义组件的布局与渲染 | 正常 |

### US-6: ViewFunctions 生命周期 C++ 分发

**作为** 框架维护者,
**我想要** `ViewFunctions`（约 40 个 `JSWeak<JSFunc>`）将 C++ 侧的生命周期/渲染回调分发到 TS 侧,
**以便** C++ 宿主与 TS 视图实现双向通信。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `JSViewPartialUpdate::JSBind`（"NativeViewPartialUpdate"）THEN 绑定 TS 视图到 C++ 宿主 | 正常 |
| AC-6.2 | WHEN 渲染 THEN `ViewFunctions.ExecuteRender`/`ExecuteRerender` 分发到 TS 侧 build/rerender | 正常 |
| AC-6.3 | WHEN 生命周期 THEN `ExecuteAboutToBeDeleted`/`ExecuteRecycle`/`ExecuteAboutToReuse`/`ExecuteSetActive` 分发 | 正常 |
| AC-6.4 | WHEN Inspector dump THEN `ExecuteOnDumpInfo` 分发到 TS 侧 `onDumpInspector` | 正常 |
| AC-6.5 | WHEN `ViewPartialUpdateModelNG::CreateNode` THEN 创建 CustomNode 并关联 ViewFunctions | 正常 |

### US-7: C++ 存储/环境绑定

**作为** 框架维护者,
**我想要** `JSLocalStorage`/`JSPersistent`/`JSEnvironment` C++ 绑定将存储与环境对象注入 TS,
**以便** V1 存储（Feat-07~10）与环境在 C++ 侧有对应实现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `JSLocalStorage::JSBind` THEN `storages_` thread_local 按 containerId 多实例隔离 LocalStorage | 正常 |
| AC-7.2 | WHEN `JSPersistent::JSBind`（"Storage"）THEN 绑定到 `StorageProxy` 提供 PersistentStorage 后端 | 正常 |
| AC-7.3 | WHEN `JSEnvironment::JSBind`（"EnvironmentSetting"）THEN 注入 `EnvironmentSetting`（colorMode/fontScale/languageCode 等 getter） | 正常 |
| AC-7.4 | WHEN `JSStateMgmtProfiler`/`JSStateMgmtHistogram` THEN C++ 侧注入性能采集对象 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 MakeUniqueId |
| AC-1.2 | US-1 | R-1 | 代码审查 RemoveItem 移除集 |
| AC-1.3 | US-1 | R-1 | 代码审查 RemoveItemSilently |
| AC-2.1 | US-2 | R-2 | 单元测试 elmtId→View 注册 |
| AC-2.2 | US-2 | R-2 | 单元测试 流程 A 延迟 |
| AC-2.3 | US-2 | R-2 | 单元测试 流程 B 即时 |
| AC-2.4 | US-2 | R-2 | 单元测试 双流程协同 |
| AC-3.1 | US-3 | R-3 | 代码审查 C++ 移除集 |
| AC-3.2 | US-3 | R-3 | 单元测试 moveDeletedElmtIds |
| AC-3.3 | US-3 | R-3 | 单元测试 unregisterElmtIdsFromIViews |
| AC-4.1 | US-4 | R-4 | 代码审查 OnIdle |
| AC-4.2 | US-4 | R-4 | 单元测试 强制回收阈值 |
| AC-4.3 | US-4 | R-4 | 代码审查 GetStateMgmtInfo |
| AC-4.4 | US-4 | R-4 | 代码审查 RecordStateMgmtNode |
| AC-5.1 | US-5 | R-5 | 代码审查 stateMgmt.abc 载入 |
| AC-5.2 | US-5 | R-6 | 单元测试 CustomNode 创建 |
| AC-5.3 | US-5 | R-6 | 单元测试 isV2_ 区分 |
| AC-5.4 | US-5 | R-6 | 代码审查 CustomNodeBase 回调 |
| AC-5.5 | US-5 | R-6 | 单元测试 appear/destroy 配对 |
| AC-5.6 | US-5 | R-6 | 代码审查 Pattern/LayoutAlgorithm |
| AC-6.1 | US-6 | R-7 | 代码审查 JSBind |
| AC-6.2 | US-6 | R-7 | 单元测试 ExecuteRender/Rerender |
| AC-6.3 | US-6 | R-7 | 单元测试 生命周期分发 |
| AC-6.4 | US-6 | R-7 | 单元测试 ExecuteOnDumpInfo |
| AC-6.5 | US-6 | R-7 | 代码审查 CreateNode |
| AC-7.1 | US-7 | R-8 | 单元测试 JSLocalStorage 多实例 |
| AC-7.2 | US-7 | R-8 | 代码审查 JSPersistent |
| AC-7.3 | US-7 | R-8 | 代码审查 JSEnvironment |
| AC-7.4 | US-7 | R-8 | 代码审查 Profiler 注入 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | elmtId 分配/删除 | `ElementRegister.MakeUniqueId` 分配全局唯一 elmtId；`RemoveItem(elmtId)` 加入移除集（用于 TS 同步清理）；`RemoveItemSilently(elmtId)` 跳过移除集（用于复用重注册） | 移除集是全链路同步的基础 | AC-1.1~AC-1.3 |
| R-2 | 行为 | `UINodeRegisterProxy`（`pu_uinode_registry_proxy.ts`）elmtId→View 映射与同步 | 组件创建时注册到 `ElementIdToOwningViewPU_`；双流程同步已删除 elmtId：流程 A 延迟（下次重渲染 `purgeDeletedElmtIds`）、流程 B 即时（`aboutToBeDeleted` + `PipelineContext::OnIdle` 经 `uiNodeCleanUpIdleTask`）；双流程协同确保无悬挂引用 | 双流程兜底 | AC-2.1~AC-2.4 |
| R-3 | 行为 | `moveDeletedElmtIds` 全链路同步 | C++ `ElementRegister::RemoveItem` 加入移除集 → `moveDeletedElmtIds` 将已删除 elmtId 列表传给 TS → `unregisterElmtIdsFromIViews` 注销对应 View，清理 `PropertyDependencies` 中的依赖 | C++→TS 全链路 | AC-3.1~AC-3.3 |
| R-4 | 行为 | `PipelineContext::OnIdle` 空闲清理 | `OnIdle` 执行 `CallStateMgmtCleanUpIdleTaskFunc`（经 `frontend.h` 虚函数反向调用 TS `uiNodeCleanUpIdleTask`）；`MAX_FRAME_COUNT_WITHOUT_JS_UNREGISTRATION=100` 帧后强制回收未正常注销的组件防 OOM；`GetStateMgmtInfo(nodeIds, propertyName, jsonPath)` 上报 `UiSessionManager`（2000ms 超时）用于 Inspector；`RecordStateMgmtNode` 记录 dirty node 计数 | 强制回收防 OOM | AC-4.1~AC-4.4 |
| R-5 | 行为 | `stateMgmt.abc` 字节码载入 | 引擎初始化时 `_binary_stateMgmt_abc_start` 载入 `stateMgmt.abc`（编译自 stateMgmt TS 库 debug/release/profile 三种构建产物） | TS 库编译为单一 abc | AC-5.1 |
| R-6 | 行为 | `CustomNode`/`CustomNodeBase` 宿主节点 | `@Component`/`@ComponentV2` 组件创建时 C++ 创建 `CustomNode`（继承 UINode + CustomNodeBase）作为宿主；`isV2_` 区分 V1/V2（共用同一宿主）；`CustomNodeBase` 持有约 20 个 `std::function` 回调连接 TS 侧 `ViewPU`/`ViewV2`；析构时 appear/destroy 配对；`CustomNodePattern`/`CustomNodeLayoutAlgorithm` 处理布局渲染；`reusableMemOptStrategy_` 管理复用内存 | V1/V2 共用 C++ 宿主 | AC-5.2~AC-5.6 |
| R-7 | 行为 | `ViewFunctions` 生命周期 C++ 分发 | `JSViewPartialUpdate::JSBind`（"NativeViewPartialUpdate"）绑定 TS 视图到 C++；约 40 个 `JSWeak<JSFunc>`：`ExecuteRender`/`ExecuteRerender`（渲染）、`ExecuteAboutToBeDeleted`/`ExecuteRecycle`/`ExecuteAboutToReuse`/`ExecuteSetActive`（生命周期）、`ExecuteOnDumpInfo`（Inspector dump）；`ViewPartialUpdateModelNG::CreateNode` 创建 CustomNode 并关联 ViewFunctions | C++→TS 双向通信 | AC-6.1~AC-6.5 |
| R-8 | 行为 | C++ 存储/环境绑定 | `JSLocalStorage::JSBind`（`storages_` thread_local 按 containerId 多实例隔离 LocalStorage）；`JSPersistent::JSBind`（"Storage"→`StorageProxy`）；`JSEnvironment::JSBind`（"EnvironmentSetting" 注入 colorMode/fontScale/languageCode 等 getter）；`JSStateMgmtProfiler`/`JSStateMgmtHistogram` 注入性能采集对象 | 服务 V1 存储（Feat-07~10） | AC-7.1~AC-7.4 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 代码审查 | `element_register.h` MakeUniqueId |
| VM-2 | AC-1.2 | 代码审查 | `element_register.h` RemoveItem 移除集 |
| VM-3 | AC-1.3 | 代码审查 | `element_register.h` RemoveItemSilently |
| VM-4 | AC-2.1 | 单元测试 | `common_tests/` elmtId→View 注册 |
| VM-5 | AC-2.2 | 单元测试 | `common_tests/` 流程 A 延迟 |
| VM-6 | AC-2.3 | 单元测试 | `common_tests/` 流程 B 即时 |
| VM-7 | AC-2.4 | 单元测试 | `common_tests/` 双流程协同 |
| VM-8 | AC-3.1 | 代码审查 | `element_register.h` C++ 移除集 |
| VM-9 | AC-3.2 | 单元测试 | `common_tests/` moveDeletedElmtIds |
| VM-10 | AC-3.3 | 单元测试 | `common_tests/` unregisterElmtIdsFromIViews |
| VM-11 | AC-4.1 | 代码审查 | `pipeline_context.cpp` OnIdle |
| VM-12 | AC-4.2 | 单元测试 | `common_tests/` 强制回收阈值 |
| VM-13 | AC-4.3 | 代码审查 | `pipeline_context.cpp` GetStateMgmtInfo |
| VM-14 | AC-4.4 | 代码审查 | `pipeline_context.cpp` RecordStateMgmtNode |
| VM-15 | AC-5.1 | 代码审查 | `stateMgmt.abc` 载入 |
| VM-16 | AC-5.2 | 单元测试 | `test/unittest/core/pattern/custom/` CustomNode 创建 |
| VM-17 | AC-5.3 | 单元测试 | `test/unittest/core/pattern/custom/` isV2_ 区分 |
| VM-18 | AC-5.4 | 代码审查 | `custom_node_base.h` 回调 |
| VM-19 | AC-5.5 | 单元测试 | `test/unittest/core/pattern/custom/` appear/destroy 配对 |
| VM-20 | AC-5.6 | 代码审查 | `custom_node_pattern.h`/`custom_node_layout_algorithm.h` |
| VM-21 | AC-6.1 | 代码审查 | `js_view.h` JSBind |
| VM-22 | AC-6.2 | 单元测试 | `test/unittest/core/pattern/custom/` ExecuteRender |
| VM-23 | AC-6.3 | 单元测试 | `test/unittest/core/pattern/custom/` 生命周期分发 |
| VM-24 | AC-6.4 | 单元测试 | `test/unittest/core/pattern/custom/` ExecuteOnDumpInfo |
| VM-25 | AC-6.5 | 代码审查 | `view_partial_update_model_ng.cpp` CreateNode |
| VM-26 | AC-7.1 | 单元测试 | `test/unittest/core/` JSLocalStorage 多实例 |
| VM-27 | AC-7.2 | 代码审查 | `js_persistent.cpp` JSPersistent |
| VM-28 | AC-7.3 | 代码审查 | `js_environment.cpp` JSEnvironment |
| VM-29 | AC-7.4 | 代码审查 | `js_state_mgmt_profiler.*` Profiler 注入 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `ElementRegister`/`ElementRegisterImpl` | `frameworks/core/pipeline/base/element_register.h` | 全局 elmtId 分配/回收/移除集 |
| `UINodeRegisterProxy` | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_uinode_registry_proxy.ts` | elmtId→View 映射、双流程同步 |
| `moveDeletedElmtIds` | TS 侧入口 | 接收 C++ 已删除 elmtId 列表 |
| `unregisterElmtIdsFromIViews` | TS 侧 | 注销 View，清理 PropertyDependencies |
| `PipelineContext` | `frameworks/core/pipeline_ng/pipeline_context.cpp` | `OnIdle`/`RecordStateMgmtNode`/`GetStateMgmtInfo`/`CallStateMgmtCleanUpIdleTaskFunc` |
| `Frontend` | `frameworks/core/common/frontend.h` | C++→TS 反向调用虚函数 |
| `CustomNode`/`CustomNodeBase` | `frameworks/core/components_ng/pattern/custom/custom_node.cpp/.h` | C++ 宿主节点（V1/V2 共用 isV2_） |
| `ViewFunctions` | `frameworks/bridge/declarative_frontend/jsview/js_view_functions.h` | 约 40 回调 C++ 分发 |
| `JSViewPartialUpdate` | `frameworks/bridge/declarative_frontend/jsview/js_view.h` | "NativeViewPartialUpdate" 绑定 |
| `JSLocalStorage` | `frameworks/bridge/declarative_frontend/jsview/js_local_storage.cpp/.h` | LocalStorage C++ 绑定（thread_local 多实例） |
| `JSPersistent` | `frameworks/bridge/declarative_frontend/jsview/js_persistent.cpp/.h` | PersistentStorage C++ 绑定 |
| `JSEnvironment` | `frameworks/bridge/declarative_frontend/jsview/js_environment.cpp/.h` | Environment C++ 绑定 |
| `JSStateMgmtProfiler`/`JSStateMgmtHistogram` | `frameworks/bridge/declarative_frontend/jsview/js_state_mgmt_profiler.*` | 性能采集 C++ 注入 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | ElementRegister/UINodeRegisterProxy/CustomNode/ViewFunctions 引入 | elmtId 同步与 C++ 宿主基础 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| V1/V2 共用 C++ 宿主 | CustomNode/ViewFunctions 经 `isV2_` 区分 V1/V2；C++ 不参与观察逻辑（V1 属性包装对象、V2 getter/setter 均为纯 TS） |
| elmtId 全链路同步 | C++ RemoveItem → 移除集 → moveDeletedElmtIds → TS unregisterElmtIdsFromIViews；双流程（延迟+即时）兜底 |
| 强制回收阈值 | `MAX_FRAME_COUNT_WITHOUT_JS_UNREGISTRATION=100` 帧后强制回收未正常注销组件防 OOM |
| stateMgmt.abc 单一字节码 | V1/V2 共用同一 `stateMgmt.abc`（debug/release/profile 三种构建产物） |
| thread_local 多实例 | JSLocalStorage 按 containerId 隔离 LocalStorage 实例 |
| 归属 | elmtId 同步与 C++ 宿主归 V1（07-02-01）；动态/静态前端互操作（InteropStorage/ViewInterop/BuilderViewV2）归 07-02-05 |

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
| `frameworks/core/pipeline/base/element_register.h` | `ElementRegister` 全局 elmtId 分配/回收/移除集 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_uinode_registry_proxy.ts` | `UINodeRegisterProxy` elmtId→View 映射、双流程同步 |
| `frameworks/core/pipeline_ng/pipeline_context.cpp` | `PipelineContext` OnIdle/RecordStateMgmtNode/GetStateMgmtInfo/CallStateMgmtCleanUpIdleTaskFunc |
| `frameworks/core/common/frontend.h` | `Frontend` C++→TS 反向调用虚函数 |
| `frameworks/core/components_ng/pattern/custom/custom_node.cpp/.h` | `CustomNode`/`CustomNodeBase` C++ 宿主节点 |
| `frameworks/core/components_ng/pattern/custom/custom_node_pattern.cpp/.h` | `CustomNodePattern` |
| `frameworks/core/components_ng/pattern/custom/custom_node_layout_algorithm.cpp/.h` | `CustomNodeLayoutAlgorithm` |
| `frameworks/bridge/declarative_frontend/jsview/js_view.h` | `JSViewPartialUpdate::JSBind` 绑定 |
| `frameworks/bridge/declarative_frontend/jsview/js_view_functions.h` | `ViewFunctions` 约 40 回调 |
| `frameworks/bridge/declarative_frontend/jsview/js_local_storage.cpp/.h` | `JSLocalStorage` C++ 绑定（thread_local） |
| `frameworks/bridge/declarative_frontend/jsview/js_persistent.cpp/.h` | `JSPersistent` C++ 绑定 |
| `frameworks/bridge/declarative_frontend/jsview/js_environment.cpp/.h` | `JSEnvironment` C++ 绑定 |
| `frameworks/bridge/declarative_frontend/jsview/js_state_mgmt_profiler.*` | `JSStateMgmtProfiler`/`JSStateMgmtHistogram` 性能采集 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | UINodeRegisterProxy/moveDeletedElmtIds 行为回归 |
| `test/unittest/core/pattern/custom/` | CustomNode/ViewFunctions C++ 宿主测试 |
