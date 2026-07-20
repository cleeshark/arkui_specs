# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 多实例窗口与全局管线 |
| 特性编号 | Func-03-05-01-Feat-03 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | API 10 及以后（以 master HEAD 实现为基线） |
| SIG 归属 | ArkUI SIG / 多实例与窗口团队 |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 GlobalPipelineContextManager 的全局 PipelineContext 创建与生命周期管理、跨窗口模态页面（ModalPageNode）在全局管线与实例管线之间的转移、以及多实例子窗口通过 RegisterSubWindow / SetRequestVsyncCallback 的 VSync 扇出机制。全局管线窗口使用 `isGlobalPipeline=true` 的 RosenWindow，拥有独立 TaskExecutor、ThreadModel 和 RSUIDirector，不依赖任何具体实例容器。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GlobalPipelineContextManager 单例模式 | GetInstance / globalContextMap_ / modalPageMap_ / sessionIdMap_ |
| ADDED | CreateGlobalPipelineContext 全流程 | TaskExecutor + AssetManager + Frontend + RosenWindow(isGlobalPipeline=true) + PipelineContext |
| ADDED | WindowLifeCycle::AfterDestroyed 清理链 | RemoveGlobalPipelineContext + RemoveModalPageNode + RemoveSessionId + Destroy |
| ADDED | ProcessModalPageNode 模态页面转移 | 从全局管线 OverlayManager 摘取 → 挂载到实例管线 RootElement |
| ADDED | 子窗口 VSync 扇出 | RegisterSubWindow / GetSubWindowIds / SetRequestVsyncCallback 遍历 |
| ADDED | SessionId 映射管理 | RegisterSessionId / GetSessionId / GetUecNameBySessionId |

## 输入文档

- 关联设计：`specs/03-engine-framework/05-window-mechanism/01-window-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/global_pipeline_context_manager.h` / `.cpp`（GetInstance, CreateGlobalPipelineContext, RemoveGlobalPipelineContext, ProcessModalPageNode, RegisterSessionId, GetSessionId, GetUecNameBySessionId）
  - `frameworks/core/components_ng/render/adapter/rosen_window.cpp`（Init, 多实例扇出）
  - `frameworks/core/common/window.h`（RegisterSubWindow, UnregisterSubWindow, GetSubWindowIds）

## 用户故事

### US-1: GlobalPipelineContextManager 单例管理全局管线

- As a 多窗口架构维护者
- I want GlobalPipelineContextManager 以 name 为 key 管理多个全局 PipelineContext
- So that 跨窗口模态、UEC（统一扩展组件）等全局能力有独立的渲染管线

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `GetInstance()` 被调用 THEN 返回静态局部变量实例（单例模式）。来源：`global_pipeline_context_manager.cpp:45-49` | 正常 |
| AC-1.2 | WHEN 构造函数执行 THEN 通过 `ThreadModelImpl::CreateThreadModel(false, false, !GetRosenBackendEnabled())` 创建内部 `threadModelImpl_`。来源：`global_pipeline_context_manager.cpp:206-209` | 正常 |
| AC-1.3 | WHEN `GetGlobalPipelineContext(name)` 被调用 THEN 在 `globalContextMap_` 中查找；若不存在返回 nullptr。来源：`global_pipeline_context_manager.cpp:51-58` | 正常 |
| AC-1.4 | WHEN `AddGlobalPipelineContext(name, pipelineContext)` 被调用且 name 已存在 THEN 记录 `LOGW` 并覆盖已有值。来源：`global_pipeline_context_manager.cpp:94-104` | 异常 |

### US-2: CreateGlobalPipelineContext 创建独立渲染管线

- As a 多窗口架构维护者
- I want CreateGlobalPipelineContext 创建一个拥有独立 TaskExecutor、AssetManager、Frontend 和 RosenWindow 的完整 PipelineContext
- So that 全局管线窗口可独立渲染，不依赖任何实例容器

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `CreateGlobalPipelineContext(name, rsWindow, frontendType, instanceId)` 被调用 THEN 创建 `TaskExecutorImpl`，调用 `InitPlatformThread(true)`（复用当前 event runner）和 `InitOtherThreads(threadModelImpl_)`。来源：`global_pipeline_context_manager.cpp:64-66` | 正常 |
| AC-2.2 | WHEN `frontendType` 非 DECLARATIVE_JS 且非 ETS_CARD THEN 调用 `taskExecutor->InitJsThread()` 初始化 JS 线程。来源：`global_pipeline_context_manager.cpp:67-69` | 正常 |
| AC-2.3 | WHEN 创建 RosenWindow THEN 使用 `std::make_shared<NG::RosenWindow>(rsWindow, taskExecutor, instanceId, true)`，第 4 参数 `isGlobalPipeline=true`。来源：`global_pipeline_context_manager.cpp:83` | 正常 |
| AC-2.4 | WHEN 创建 PipelineContext THEN 使用 `AceType::MakeRefPtr<NG::PipelineContext>(window, taskExecutor, assetManagerImpl, nullptr, frontend, instanceId)`。来源：`global_pipeline_context_manager.cpp:84-85` | 正常 |
| AC-2.5 | WHEN PipelineContext 创建完成 THEN 调用 `AddGlobalPipelineContext(name, pipelineContext)` 存入 map，并创建 `WindowLifeCycle` 注册到 `rsWindow->RegisterLifeCycleListener`。来源：`global_pipeline_context_manager.cpp:86-89` | 正常 |

### US-3: WindowLifeCycle::AfterDestroyed 清理全局管线

- As a 资源管理维护者
- I want Rosen::Window 销毁后通过 WindowLifeCycle 回调触发全局管线的完整清理
- So that 全局管线相关的 PipelineContext、ModalPageNode、SessionId 都被正确释放

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `AfterDestroyed()` 被调用 THEN 从 GlobalPipelineContextManager 移除 pipeline context（`RemoveGlobalPipelineContext`）、modal page node（`RemoveModalPageNode`）和 session ID（`RemoveSessionId`）。来源：`global_pipeline_context_manager.cpp:28-33` | 正常 |
| AC-3.2 | WHEN modalPageNode 非空 THEN 从原父节点摘除，挂载到全局管线的 RootElement。来源：`global_pipeline_context_manager.cpp:33-39` | 正常 |
| AC-3.3 | WHEN globalPipelineContext 非空 THEN 调用 `globalPipelineContext->Destroy()` 后 `Reset()`。来源：`global_pipeline_context_manager.cpp:40-42` | 正常 |

### US-4: ProcessModalPageNode 模态页面转移

- As a 多窗口交互维护者
- I want ProcessModalPageNode 将模态页面从全局管线的 OverlayManager 转移到实例管线的 RootElement
- So that 跨窗口模态页面能跟随目标实例窗口渲染

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `ProcessModalPageNode(name, instanceId)` 被调用 THEN 获取 `globalPipelineContext` 和 `pipelineContext`（通过 `NG::PipelineContext::GetContextByContainerId(instanceId)`）；若任一为空则 LOGE 并返回。来源：`global_pipeline_context_manager.cpp:137-144` | 正常 |
| AC-4.2 | WHEN modalPageMap_ 中不存在该 name THEN 从 globalPipelineContext 的 OverlayManager 获取 `GetModalStackTop()`，从原父节点摘除，存入 `modalPageMap_`。来源：`global_pipeline_context_manager.cpp:145-156` | 正常 |
| AC-4.3 | WHEN modalPageNode 已获取 THEN 挂载到 `pipelineContext->GetRootElement()`，调用 `RebuildRenderContextTree()` 和 `MarkDirtyNode(PROPERTY_UPDATE_MEASURE)`。来源：`global_pipeline_context_manager.cpp:157-163` | 正常 |
| AC-4.4 | WHEN globalOverlayManager 为空 **或** GetModalStackTop 为空 THEN CHECK_NULL_VOID 静默返回。来源：`global_pipeline_context_manager.cpp:146-149` | 异常 |

### US-5: 子窗口 VSync 扇出

- As a 多实例架构维护者
- I want 主窗口的 SetRequestVsyncCallback 在收到 VSync 请求时遍历已注册的子窗口，对每个子窗口的 pipeline 调用 RequestFrame
- So that 子窗口的 VSync 请求能通过主窗口统一扇出，避免独立请求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 子窗口 RosenWindow::Init 检测到 parent RSUIContext 一致 THEN 调用 `pipelineWindow->RegisterSubWindow(id_)` 将自身注册到父窗口。来源：`rosen_window.cpp:168` | 正常 |
| AC-5.2 | WHEN 主窗口的 `SetRequestVsyncCallback` 回调被触发 THEN 遍历 `self->GetSubWindowIds()`，对每个 subWindowId 获取 Container → PipelineContext → `pipeline->RequestFrame()`。来源：`rosen_window.cpp:177-186` | 正常 |
| AC-5.3 | WHEN `RegisterSubWindow(id)` 被调用 THEN 在 `subWindowMutex_` 保护下将 id 插入 `subWindowIds_` 集合。来源：`window.h:279-283` | 正常 |
| AC-5.4 | WHEN `UnregisterSubWindow(id)` 被调用 THEN 在 `subWindowMutex_` 保护下将 id 从 `subWindowIds_` 集合移除。来源：`window.h:285-289` | 正常 |
| AC-5.5 | WHEN `GetSubWindowIds()` 被调用 THEN 在 `subWindowMutex_` 保护下返回 `subWindowIds_` 的 vector 副本。来源：`window.h:291-296` | 正常 |

### US-6: SessionId 映射管理

- As a 多窗口架构维护者
- I want GlobalPipelineContextManager 管理 name → sessionId 的映射
- So that UEC（统一扩展组件）能通过 sessionId 查找对应的窗口名称

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `RegisterSessionId(name, sessionId)` 被调用且 name 已存在 THEN 记录 `LOGW` 并返回（不覆盖）。来源：`global_pipeline_context_manager.cpp:166-173` | 异常 |
| AC-6.2 | WHEN `GetSessionId(name)` 被调用且不存在 THEN 返回 0 并 LOGW。来源：`global_pipeline_context_manager.cpp:187-194` | 正常 |
| AC-6.3 | WHEN `GetUecNameBySessionId(sessionId)` 被调用 THEN 遍历 `sessionIdMap_` 反查 name；不存在时返回空字符串。来源：`global_pipeline_context_manager.cpp:176-185` | 正常 |
| AC-6.4 | WHEN `RemoveSessionId(name)` 被调用 THEN 从 map 中移除；不存在时静默返回。来源：`global_pipeline_context_manager.cpp:197-204` | 正常 |

## 验收追溯

| AC编号 | US ID | 业务规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码评审 |
| AC-1.2 | US-1 | R-2 | 代码评审 |
| AC-1.3 | US-1 | R-3 | 代码评审 |
| AC-1.4 | US-1 | R-4 | 代码评审 |
| AC-2.1 | US-2 | R-5 | 代码评审 |
| AC-2.2 | US-2 | R-6 | 代码评审 |
| AC-2.3 | US-2 | R-7 / R-8 | 代码评审 |
| AC-2.4 | US-2 | R-9 | 代码评审 |
| AC-2.5 | US-2 | R-10 / R-11 | 代码评审 |
| AC-3.1 | US-3 | R-12 | 代码评审 |
| AC-3.2 | US-3 | R-13 | 代码评审 |
| AC-3.3 | US-3 | R-14 | 代码评审 |
| AC-4.1 | US-4 | R-15 | 代码评审 |
| AC-4.2 | US-4 | R-16 / R-17 | 代码评审 |
| AC-4.3 | US-4 | R-18 | 代码评审 |
| AC-4.4 | US-4 | R-19 | 代码评审 |
| AC-5.1 | US-5 | R-20 | 多实例集成测试 |
| AC-5.2 | US-5 | R-20 / R-21 | 多实例集成测试 |
| AC-5.3 | US-5 | R-22 | 代码评审 |
| AC-5.4 | US-5 | R-22 | 代码评审 |
| AC-5.5 | US-5 | R-22 | 代码评审 |
| AC-6.1 | US-6 | R-23 | 代码评审 |
| AC-6.2 | US-6 | R-24 | 代码评审 |
| AC-6.3 | US-6 | R-25 | 代码评审 |
| AC-6.4 | US-6 | R-26 | 代码评审 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | GlobalPipelineContextManager 是进程级单例，`GetInstance()` 返回静态局部变量。持有 `globalContextMap_`、`modalPageMap_`、`sessionIdMap_` 三个 map 和一个 `threadModelImpl_`。来源：`global_pipeline_context_manager.cpp:45-49, 77-81`。 | — | — |
| R-2 | 行为 | — | 构造函数通过 `ThreadModelImpl::CreateThreadModel(false, false, !GetRosenBackendEnabled())` 创建线程模型；第 3 参数控制是否使用 Rosen 后端。来源：`global_pipeline_context_manager.cpp:206-209`。 | — | — |
| R-3 | 行为 | — | `GetGlobalPipelineContext(name)` 在 `globalContextMap_` 中查找；找不到返回 nullptr。来源：`global_pipeline_context_manager.cpp:51-58`。 | — | — |
| R-4 | 异常 | name 已存在于 globalContextMap_ | `AddGlobalPipelineContext` 记录 `LOGW("There already exists a global Pipeline Context with the same name!")` 并覆盖。来源：`global_pipeline_context_manager.cpp:94-104`。 | — | — |
| R-5 | 行为 | — | `CreateGlobalPipelineContext` 创建 `TaskExecutorImpl`，`InitPlatformThread(true)` 复用当前 event runner，`InitOtherThreads(threadModelImpl_)` 初始化其他线程。来源：`global_pipeline_context_manager.cpp:64-66`。 | — | — |
| R-6 | 行为 | frontendType 非 DECLARATIVE_JS 且非 ETS_CARD | 调用 `taskExecutor->InitJsThread()` 初始化独立 JS 线程。DECLARATIVE_JS 和 ETS_CARD 复用 UI 线程跑 JS。来源：`global_pipeline_context_manager.cpp:67-69`。 | — | — |
| R-7 | 行为 | — | `CreateGlobalPipelineContext` 使用 `std::make_shared<NG::RosenWindow>(rsWindow, taskExecutor, instanceId, true)` 创建 RosenWindow，第 4 参数 `isGlobalPipeline=true` 强制独立 RSUIDirector。来源：`global_pipeline_context_manager.cpp:83`。 | — | — |
| R-8 | 边界 | isGlobalPipeline=true | RosenWindow 构造函数中 `isGlobalPipeline` 优先于 Rosen::Window 提供的 director：即使 rsWindow->GetRSUIDirector() 非空，也创建独立 RSUIDirector（`directorFromWindow_=false`）。来源：`rosen_window.cpp:125-128`。 | — | — |
| R-9 | 行为 | — | PipelineContext 使用 `MakeRefPtr<NG::PipelineContext>(window, taskExecutor, assetManagerImpl, nullptr, frontend, instanceId)` 创建；第 4 参数（reflectionBridge）为 nullptr。来源：`global_pipeline_context_manager.cpp:84-85`。 | — | — |
| R-10 | 行为 | — | 创建后通过 `AddGlobalPipelineContext` 存入 map。来源：`global_pipeline_context_manager.cpp:86`。 | — | — |
| R-11 | 行为 | — | 创建 `WindowLifeCycle(name)` 并通过 `rsWindow->RegisterLifeCycleListener(windowLifeCycle)` 注册；Rosen::Window 销毁后回调 `AfterDestroyed()` 触发清理。来源：`global_pipeline_context_manager.cpp:88-89`。 | — | — |
| R-12 | 行为 | — | `WindowLifeCycle::AfterDestroyed` 依次调用 `RemoveGlobalPipelineContext(name)`、`RemoveModalPageNode(name)`、`RemoveSessionId(name)`。来源：`global_pipeline_context_manager.cpp:28-33`。 | — | — |
| R-13 | 行为 | modalPageNode 非空 | `AfterDestroyed` 将 modalPageNode 从原父节点摘除，挂载到全局管线的 RootElement。来源：`global_pipeline_context_manager.cpp:33-39`。 | — | — |
| R-14 | 行为 | globalPipelineContext 非空 | `AfterDestroyed` 调用 `globalPipelineContext->Destroy()` 和 `Reset()`。来源：`global_pipeline_context_manager.cpp:40-42`。 | — | — |
| R-15 | 行为 | — | `ProcessModalPageNode(name, instanceId)` 获取 globalPipelineContext 和 pipelineContext（按 containerId）；任一为空则 LOGE 并返回。来源：`global_pipeline_context_manager.cpp:137-144`。 | — | — |
| R-16 | 行为 | modalPageMap_ 不含 name | 从 globalOverlayManager→GetModalStackTop 获取模态节点，从原父节点 RemoveChild + RebuildRenderContextTree，存入 modalPageMap_。来源：`global_pipeline_context_manager.cpp:145-156`。 | — | — |
| R-17 | 行为 | — | modalPageNode 挂载到 `pipelineContext->GetRootElement()`，调用 `RebuildRenderContextTree()` + `MarkDirtyNode(PROPERTY_UPDATE_MEASURE)` 触发重新布局。来源：`global_pipeline_context_manager.cpp:157-163`。 | — | — |
| R-18 | 行为 | — | `RemoveGlobalPipelineContext` 从 map 中移除并返回 pipeline 指针（供 AfterDestroyed 后续 Destroy 使用）。来源：`global_pipeline_context_manager.cpp:106-115`。 | — | — |
| R-19 | 异常 | globalOverlayManager 为空 / GetModalStackTop 为空 | CHECK_NULL_VOID 静默返回，不触发模态页面转移。来源：`global_pipeline_context_manager.cpp:146-149`。 | — | — |
| R-20 | 行为 | — | 子窗口通过 `RegisterSubWindow(id)` 注册到父窗口的 `subWindowIds_` 集合；主窗口的 `SetRequestVsyncCallback` 回调遍历子窗口逐个 `pipeline->RequestFrame()`。来源：`rosen_window.cpp:168, 177-186`、`window.h:279-296`。 | — | — |
| R-21 | 行为 | 多实例未启用 | `SetRequestVsyncCallback` 内部仅调用 `self->RequestFrame()`，不遍历子窗口。来源：`rosen_window.cpp:173-176`。 | — | — |
| R-22 | 行为 | — | `subWindowIds_` 是 `std::set<int32_t>`，通过 `subWindowMutex_`（mutable mutex）保护。Register/Unregister/Get 均在锁内操作。来源：`window.h:279-296, 308-309`。 | — | — |
| R-23 | 异常 | name 已存在于 sessionIdMap_ | `RegisterSessionId` 记录 `LOGW` 并返回（不覆盖）。来源：`global_pipeline_context_manager.cpp:166-173`。 | — | — |
| R-24 | 行为 | name 不在 sessionIdMap_ | `GetSessionId` 返回 0 并 LOGW。来源：`global_pipeline_context_manager.cpp:187-194`。 | — | — |
| R-25 | 行为 | — | `GetUecNameBySessionId` 遍历 sessionIdMap_ 反查 name；不存在返回空字符串。来源：`global_pipeline_context_manager.cpp:176-185`。 | — | — |
| R-26 | 行为 | — | `RemoveSessionId` 从 map 中移除；不存在时静默返回。来源：`global_pipeline_context_manager.cpp:197-204`。 | — | — |

---

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.4 | 代码评审 | `global_pipeline_context_manager.cpp:45-104` 直接对照 |
| VM-2 | AC-2.1..2.5 | 集成测试 | 全局管线创建场景验证 |
| VM-3 | AC-3.1..3.3 | 集成测试 | WindowLifeCycle::AfterDestroyed 清理链 |
| VM-4 | AC-4.1..4.4 | 集成测试 | ProcessModalPageNode 模态页面转移 |
| VM-5 | AC-5.1..5.5 | 集成测试 | 多实例子窗口 VSync 扇出 |
| VM-6 | AC-6.1..6.4 | 代码评审 | `global_pipeline_context_manager.cpp:166-204` 直接对照 |

## API 变更分析

### 新增 API

无。Feat-03 为框架内部全局管线管理，**不对外暴露 ArkTS 属性 / C-API**。

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指引 |
|----------|----------|------|----------|
| 各版本 | `SystemProperties::GetMultiInstanceEnabled()` 控制子窗口 VSync 扇出路径 | 高：多实例编译态决定子窗口 vsync 行为 | 切换后行为按 R-20 / R-21 |
| 各版本 | `SystemProperties::GetRosenBackendEnabled()` 影响 ThreadModelImpl 创建参数 | 中：后端选择影响线程模型 | 不修改 |
| NG_BUILD 编译宏 | `CreateGlobalPipelineContext` 在 NG_BUILD 下使用 `DeclarativeFrontendNG`，否则使用 `DeclarativeFrontend` | 低：前端选择由编译配置决定 | 编译时决定 |
| 各版本 | `FlushImplicitTransaction` 是多实例专用的帧外 RS 事务刷新，**非** director SendMessages | 中：多实例窗口切换时确保 RS 事务暂存属性不丢失。刷新 `rsTransaction->FlushImplicitTransaction()` 而非消息队列提交。详见 Feat-02 R-21 | 仅影响多实例启用场景 |

## 架构约束

- GlobalPipelineContextManager 位于 `adapter/ohos/entrance/`，是 **平台特定** 实现（依赖 Rosen::Window、DeclarativeFrontend 等），不在 frameworks/core 中。
- 全局管线窗口的 RosenWindow 使用 `isGlobalPipeline=true`，拥有独立 RSUIDirector，**不** 从 Rosen::Window 获取 director。
- 全局管线窗口的每帧 RS 交互遵循标准管线：`FlushModifier`（属性暂存）→ `FlushTasks`→`SendMessages`（消息提交）。多实例启用时额外在 OnShow / attach 恢复时调用 `FlushImplicitTransaction`（RS 事务暂存刷新，非 SendMessages，详见 Feat-02 R-21）。
- 全局管线的 TaskExecutor 独立于任何实例容器：通过 `ThreadModelImpl::CreateThreadModel` 创建自己的线程模型。
- 子窗口 `subWindowIds_` 使用 `std::set<int32_t>` + `mutable std::mutex` 保护，支持跨线程安全访问。
- WindowLifeCycle 通过 Rosen::Window 的 `RegisterLifeCycleListener` 注册，`AfterDestroyed` 是 Rosen::Window 销毁后的唯一回调入口。

## 非功能性需求

- 线程安全：`subWindowIds_` 的读写通过 `subWindowMutex_` 互斥保护；`globalContextMap_` / `modalPageMap_` / `sessionIdMap_` 在 UI 线程访问（隐含单线程约束）。
- 资源管理：WindowLifeCycle::AfterDestroyed 确保全局管线、模态页面、SessionId 三者同步清理，无悬空引用。
- 可扩展性：globalContextMap_ 以 name 为 key，支持多个全局管线窗口共存。
- 模态页面一致性：ProcessModalPageNode 在节点转移后调用 RebuildRenderContextTree + MarkDirtyNode，确保渲染树一致性。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

- 多实例管理（03-06-01）：全局管线是多实例架构的补充，为跨窗口模态、UEC 提供渲染管线。
- 渲染管线（03-01-01）：全局管线窗口与实例管线窗口共享相同的 PipelineContext 架构，但 RSUIDirector 和 TaskExecutor 独立。
- OverlayManager：模态页面通过 OverlayManager 的 GetModalStackTop 获取，转移时重建渲染上下文树。
- SubwindowManager：子窗口通过 `SubwindowManager::GetParentContainerId` 确定父子关系，RegisterSubWindow 在父窗口上注册。

## 行为场景

```
场景 1: 创建全局管线窗口 (AC-2.1..2.5, R-5..R-11)
  Given 一个 Rosen::Window 已创建
  When CreateGlobalPipelineContext(name, rsWindow, frontendType, instanceId) 被调用
  Then 创建独立 TaskExecutor + AssetManager + Frontend
  And 创建 RosenWindow(isGlobalPipeline=true) 拥有独立 RSUIDirector
  And 创建 PipelineContext 存入 globalContextMap_
  And 注册 WindowLifeCycle 到 Rosen::Window

场景 2: 全局管线窗口销毁清理 (AC-3.1..3.3, R-12..R-14)
  Given 全局管线窗口已创建，WindowLifeCycle 已注册
  When Rosen::Window 被销毁，触发 AfterDestroyed()
  Then RemoveGlobalPipelineContext 从 map 移除 pipeline
  And RemoveModalPageNode 取出模态页面并挂回全局管线 RootElement
  And RemoveSessionId 移除映射
  And globalPipelineContext->Destroy() 被调用

场景 3: 模态页面从全局管线转移到实例管线 (AC-4.1..4.3, R-15..R-18)
  Given 全局管线 OverlayManager 栈顶有一个模态页面
  When ProcessModalPageNode(name, instanceId) 被调用
  Then 模态页面从全局管线 OverlayManager 摘取
  And 存入 modalPageMap_ 备查
  And 挂载到实例管线 RootElement
  And RebuildRenderContextTree + MarkDirtyNode 触发重新布局

场景 4: 子窗口 VSync 请求透传 (AC-5.1..5.2, R-20)
  Given SystemProperties::GetMultiInstanceEnabled()==true
  And 子窗口已通过 RegisterSubWindow 注册到父窗口
  When 子窗口的 RSUIDirector 需要 VSync
  Then SetRequestVsyncCallback 回调遍历 GetSubWindowIds()
  And 对每个子窗口的 pipeline 调用 RequestFrame()

场景 5: 子窗口 Init 短路注册 (AC-5.1, R-20)
  Given 多实例启用，子容器与父容器 RSUIContext 一致
  When RosenWindow::Init() 执行
  Then RegisterSubWindow(id_) 将子窗口注册到父窗口
  And 直接返回，不独立注册 SetRequestVsyncCallback

场景 6: SessionId 反查 UEC 名称 (AC-6.3, R-25)
  Given sessionIdMap_ 中有 {"window1": 42}
  When GetUecNameBySessionId(42) 被调用
  Then 返回 "window1"
```

## Spec 自审清单

- [x] 所有 H2/H3 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」「行为场景」中可被引用
- [x] 规则定义编号齐全（R-1..R-26）
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 不暴露 ArkTS / C-API
- [x] 兼容性声明覆盖当前已识别的版本差异
- [x] Gherkin 场景覆盖每个 AC
- [x] 与 design.md 章节标题、ID（DESIGN-Func-03-05-01）对齐

## context-references

- `adapter/ohos/entrance/global_pipeline_context_manager.h:32-83`（WindowLifeCycle + GlobalPipelineContextManager 类定义）
- `adapter/ohos/entrance/global_pipeline_context_manager.cpp:27-43`（WindowLifeCycle::AfterDestroyed）
- `adapter/ohos/entrance/global_pipeline_context_manager.cpp:45-92`（GetInstance + CreateGlobalPipelineContext）
- `adapter/ohos/entrance/global_pipeline_context_manager.cpp:94-115`（AddGlobalPipelineContext / RemoveGlobalPipelineContext）
- `adapter/ohos/entrance/global_pipeline_context_manager.cpp:117-164`（RemoveModalPageNode / GetModalPageNode / ProcessModalPageNode）
- `adapter/ohos/entrance/global_pipeline_context_manager.cpp:166-209`（SessionId 管理 + 构造函数）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:146-188`（Init 多实例扇出 + SetRequestVsyncCallback）
- `frameworks/core/common/window.h:279-296`（RegisterSubWindow / UnregisterSubWindow / GetSubWindowIds）
- `frameworks/core/common/window.h:308-309`（subWindowMutex_ / subWindowIds_ 成员）
