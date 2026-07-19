# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 多实例管理全能力 |
| 特性编号 | Func-03-06-01-Feat-01 |
| 所属 Epic | 引擎框架层-多实例管理 |
| 优先级 | P0 |
| 目标版本 | API 10+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | L3（关键） |

## 本次变更范围（Delta）

> 已有实现补录（lineage: new-on-legacy），无代码变更。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 多实例管理全能力规格文档 | 补录已有框架内部多实例管理架构的规格文档，覆盖 7 个子能力 |

## 输入文档

| 文档类型 | 路径 |
|---------|------|
| 设计文档 | `specs/03-engine-framework/06-multi-instance-management/01-multi-instance-management/design.md` |
| 源码定位 | `frameworks/core/common/ace_engine.cpp`, `frameworks/core/common/container_scope.cpp`, `adapter/ohos/osal/system_properties.cpp` |

## 用户故事

### US-1: 实例生命周期管理

**As a** 框架开发者
**I want** 通过 AceEngine 单例管理多个独立 UI 容器实例的创建、注册和销毁
**So that** 同一进程中可以同时运行多个窗口/子窗口/对话框/卡片等独立 UI 实例

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-1.1 | **WHEN** 调用 `AceContainer::CreateContainer(instanceId, type, ...)` **THEN** 容器以指定 instanceId 注册到 `AceEngine::containerMap_`（`try_emplace` 不覆盖已存在的 key），同时插入 `ContainerScope::containerSet_` | 正常 |
| AC-1.2 | **WHEN** 调用 `Container::GenerateId<STAGE_CONTAINER>()` **THEN** 返回的 ID 范围为 100000–199999（`type * CONTAINER_ID_DIVIDE_SIZE`），且该 ID 不在 `AceEngine::GetContainer(id)` 中（碰撞检测通过） | 正常 |
| AC-1.3 | **WHEN** 同一类型连续调用 `GenerateId` 生成多个 ID **THEN** ID 在 100000 范围内递增（`atomic fetch_add % 100000`），不跳出到其他类型范围 | 正常 |
| AC-1.4 | **WHEN** 调用 `AceContainer::DestroyContainer(instanceId)` **THEN** 容器从 `containerMap_` 删除，其元数据（instanceId/createTime/destroyTime/windowId/windowName）缓存到 `destroyedUIContextCache_`，同时从 `containerSet_` 删除 | 正常 |
| AC-1.5 | **WHEN** `destroyedUIContextCache_` 已满（10 条）且有新容器被销毁 **THEN** 最早 `destroyTime_` 的缓存条目被淘汰（`std::min_element` 查找），新条目存入 | 边界 |
| AC-1.6 | **WHEN** 一个 instanceId 先被销毁（缓存）然后被重新创建（`AddContainer`）**THEN** 旧的缓存条目被清除，日志输出 "Re-adding instanceId that was previously destroyed" 警告 | 异常 |
| AC-1.7 | **WHEN** `AddContainer` 使用的 instanceId 已存在于 `containerMap_` 中 **THEN** `try_emplace` 不覆盖已有容器，旧容器保持不变 | 边界 |

### US-2: 实例 ID 解析与上下文作用域

**As a** 框架开发者
**I want** 通过 ContainerScope RAII 和多级 ID 解析策略在不同线程中正确解析当前实例
**So that** 多线程环境下每个线程能独立操作不同的 UI 实例

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-2.1 | **WHEN** 在某线程中构造 `ContainerScope scope(id)` **THEN** 该线程的 `thread_local currentId_` 被设为 `id`；析构时恢复为构造前的值（`restoreId_`） | 正常 |
| AC-2.2 | **WHEN** 调用 `ContainerScope::CurrentId()` **THEN** 返回当前线程的 `thread_local currentId_` 值（可能为 `INSTANCE_ID_UNDEFINED = -1`） | 正常 |
| AC-2.3 | **WHEN** 进程中无容器（`ContainerCount() == 0`）时调用 `SafelyId()` **THEN** 返回 `INSTANCE_ID_UNDEFINED (-1)` | 边界 |
| AC-2.4 | **WHEN** 进程中仅有 1 个容器时调用 `SafelyId()` **THEN** 返回该容器的 ID（`SingletonId()`），reason 为 `SINGLETON` | 正常 |
| AC-2.5 | **WHEN** 进程中有多个容器且 `RecentActiveId() >= 0` 时调用 `SafelyId()` **THEN** 返回 `RecentActiveId()` 的值，reason 为 `ACTIVE` | 正常 |
| AC-2.6 | **WHEN** 进程中有多个容器，`RecentActiveId() < 0` 但 `RecentForegroundId() >= 0` 时调用 `SafelyId()` **THEN** 返回 `RecentForegroundId()` 的值，reason 为 `FOREGROUND` | 边界 |
| AC-2.7 | **WHEN** 进程中有多个容器，且 `RecentActiveId()` 和 `RecentForegroundId()` 均 < 0 时调用 `SafelyId()` **THEN** 返回 `DefaultId()`（`containerSet_` 的最大值，`std::set::rbegin()`），reason 为 `DEFAULT` | 边界 |
| AC-2.8 | **WHEN** 调用 `CurrentIdWithReason()` 且 `CurrentId() >= 0` **THEN** 返回 `{CurrentId(), SCOPE}` | 正常 |
| AC-2.9 | **WHEN** 调用 `Container::GetByWindowId(windowId)` **THEN** 遍历 `containerMap_` 返回 `GetWindowId()` 匹配的容器，未找到返回 `nullptr` | 正常 |

### US-3: 线程级实例隔离

**As a** Dynamic Component / Form 渲染线程
**I want** 通过 `MarkIsolatedThread()` 在线程局部维护独立的实例集合
**So that** DC/Form 线程不会与主 UI 线程的实例上下文混淆

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-3.1 | **WHEN** 调用 `ContainerScope::MarkIsolatedThread()` **THEN** 当前线程的 `thread_local isIsolatedThread_` 设为 `true`，后续所有 ID 解析策略（DefaultId/SingletonId/RecentActiveId/RecentForegroundId/ContainerCount）返回线程局部值 | 正常 |
| AC-3.2 | **WHEN** 隔离线程调用 `AddLocal(id)` **THEN** `id` 插入线程局部 `localContainerSet_`，不影响全局 `containerSet_` | 正常 |
| AC-3.3 | **WHEN** 隔离线程调用 `RemoveLocal(id)` **THEN** `id` 从 `localContainerSet_` 删除；若 `localRecentActiveId_` 或 `localRecentForegroundId_` 等于 `id`，重置为 `DEFAULT_ID` | 正常 |
| AC-3.4 | **WHEN** UINode 在构造时快照的 `isIsolatedThread_` 与 `AttachContext` 时的当前线程隔离状态不匹配 **THEN** 输出 warning 日志（`ui_node.cpp:201-205`） | 异常 |
| AC-3.5 | **WHEN** UINode 的 `AdoptChild` 操作中父子节点的 `isIsolatedThread_` 不匹配 **THEN** 输出 error 日志（`ui_node.cpp:749-753`） | 异常 |
| AC-3.6 | **WHEN** DC 初始化（`UIContentImpl::Initialize`，`isDynamicRender_ == true`）**THEN** 依次调用 `UpdateLocalCurrent(instanceId)` → `MarkIsolatedThread()` → `AddLocal(instanceId)`（`ui_content_impl.cpp:1745-1752`） | 正常 |
| AC-3.7 | **WHEN** 调用 `ResetIsolatedThread()` **THEN** `isIsolatedThread_` 重置为 `false`，`localContainerSet_` 清空，`localRecentActiveId_` 和 `localRecentForegroundId_` 重置（测试清理用） | 恢复 |
| AC-3.8 | **WHEN** 调用 `ContainerScope::IsIsolatedThread()` **THEN** 返回当前线程的 `isIsolatedThread_` 标志；UINode 在构造时调用此方法快照隔离身份到 `isIsolatedThread_` 成员（`ui_node.cpp:94-97`），PipelineContext 同理（三个构造函数各一处：`pipeline_context.cpp:436,475,509`），该快照在对象整个生命周期内不可变 | 正常 |
| AC-3.9 | **WHEN** 隔离线程调用 `UpdateRecentActive(id)` 或 `UpdateRecentForeground(id)` **THEN** 执行**双写**：先写全局原子（`recentActiveId_.store(id)` / `recentForegroundId_.store(id)`），再写线程局部缓存（`localRecentActiveId_ = id` / `localRecentForegroundId_ = id`），保证非隔离线程可见性（`container_scope.cpp:622-638`） | 正常 |
| AC-3.10 | **WHEN** 隔离线程调用 `GetAllUIContextes()` **THEN** 仍返回全局 `containerSet_`（**不隔离**），与其他 5 个基础查询函数行为不同（`container_scope.cpp:447-450`） | 边界 |
| AC-3.11 | **WHEN** DC 销毁路径执行（`UIContentImpl` 析构）**THEN** 调用 `ContainerScope::RemoveLocal(instanceId_)` 从 `localContainerSet_` 移除 ID并重置匹配的线程局部缓存（`ui_content_impl.cpp:3141-3143`）；与 `RemoveAndCheck` 不同，`RemoveLocal` 不触达全局原子 | 正常 |

### US-4: RS 图形实例隔离

**As a** RS 渲染引擎
**I want** 当 `multiInstanceEnabled_` 为 true 时为每个容器实例创建独立的 RSUIContext
**So that** 多窗口/多实例场景下各实例的 RS 命令队列和渲染状态相互隔离

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-4.1 | **WHEN** `multiInstanceEnabled_ == true`（默认）且 `RosenRenderContext::InitContext()` 执行 **THEN** 通过 `GetRSUIContext(pipeline)` 获取每实例 RSUIContext，所有 RS 节点（RSRootNode/RSCanvasNode/RSSurfaceNode）使用该 context 创建（`rosen_render_context.cpp:631-665`） | 正常 |
| AC-4.2 | **WHEN** `multiInstanceEnabled_ == false` 且 `InitContext()` 执行 **THEN** 通过 `RSUIDirector::Create(nullptr)` 创建全局单例 RSUIDirector，所有实例共享 | 正常 |
| AC-4.3 | **WHEN** `multiInstanceEnabled_ == true` 且 `SetUITaskRunner` 被调用 **THEN** 参数为 `(callback, 0, true)` — instanceId=0 + useMultiInstance=true（`ui_content_impl.cpp:2683-2698`） | 正常 |
| AC-4.4 | **WHEN** `multiInstanceEnabled_ == false` 且 `SetUITaskRunner` 被调用 **THEN** 参数为 `(callback, instanceId)` — 传递实际 instanceId（`ui_content_impl.cpp:2683-2698`） | 正常 |
| AC-4.5 | **WHEN** `multiInstanceEnabled_ == true` 且 `FormScopedRSTransaction` 构造 **THEN** 通过 `rsUIContext->GetSyncTransactionHandler()` 获取每实例事务处理器；若当前无活动事务则 `OpenSyncTransaction()` 并标记 `needCloseSync_=true` | 正常 |
| AC-4.6 | **WHEN** `multiInstanceEnabled_ == false` 且 `FormScopedRSTransaction` 构造 **THEN** 使用全局 `RSSyncTransactionController::GetInstance()` 单例事务控制器 | 正常 |
| AC-4.7 | **WHEN** `multiInstanceEnabled_ == true` 且子窗口（`IsSubContainer() == true`）初始化 **THEN** 检查子窗口 RSUIContext 是否与父容器 RSUIContext 匹配；匹配则 `RegisterSubWindow(id_)` 并跳过标准初始化（`rosen_window.cpp:153-171`） | 正常 |
| AC-4.8 | **WHEN** 子窗口 RSUIContext 与父容器不匹配 **THEN** 走标准 Rosen 初始化路径（不调用 `RegisterSubWindow`） | 边界 |
| AC-4.9 | **WHEN** `multiInstanceEnabled_ == true` 且 RS 节点创建（`SetEffectLayer`/`InitContext`/`CreateHardwareSurface` 等）**THEN** `isSkipCheckInMultiInstance` 设为 `true`，绕过 RS 层跨实例验证（`rosen_render_context.cpp:746-752`） | 正常 |
| AC-4.10 | **WHEN** 系统参数 `persist.rosen.rsclientmultiinstance.enabled` 未设置 **THEN** `IsMultiInstanceEnabled()` 返回 `true`（默认 `"1" != "0"` 为 true）（`system_properties.cpp:335-338`） | 边界 |

### US-5: Form 多实例渲染

**As a** Form 渲染模块
**I want** 在多实例模式下为每个 Form 获取独立的 RSUIContext 并通过 IPC 传播多实例标志
**So that** 多个 Form 卡片在同一进程中渲染时各自的 RS 事务相互隔离

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-5.1 | **WHEN** `FormPattern` 创建 form bridge 且 `multiInstanceEnabled_ == true` **THEN** 调用 `GetRSUIContext()` 获取每实例 RSUIContext，传递给 `formManagerBridge_->SetRSUIContext(rsUIContext_)`（`form_pattern.cpp:1715-1719`） | 正常 |
| AC-5.2 | **WHEN** `FormPattern::GetRSUIContext()` 执行 **THEN** 从 pipeline 获取 RSUIDirector，再获取 RSUIContext（`form_pattern.cpp:3078-3096`） | 正常 |
| AC-5.3 | **WHEN** Form surface node 回调触发且 `multiInstanceEnabled_ == true` **THEN** 调用 `node->SetRSUIContext(rsUIContext_)` 将每实例 RSUIContext 设置到 form 的 RSSurfaceNode（`form_pattern.cpp:1881-1884`） | 正常 |
| AC-5.4 | **WHEN** `FormManagerDelegate::OnSurfaceCreate` 获取到 dispatcher **THEN** 调用 `formRendererDispatcher->SetMultiInstanceEnabled(SystemProperties::GetMultiInstanceEnabled())` 通过 IPC 传播标志（`form_manager_delegate.cpp:240`） | 正常 |
| AC-5.5 | **WHEN** `FormManagerDelegate::NotifySurfaceChange` 且 `multiInstanceEnabled_ == true` **THEN** 使用 `rsUIContext_->GetSyncTransactionHandler()` 获取每实例事务处理器（`form_manager_delegate.cpp:848`） | 正常 |
| AC-5.6 | **WHEN** `FormManagerDelegate::NotifySurfaceChange` 且 `multiInstanceEnabled_ == false` **THEN** 使用全局 `RSSyncTransactionController::GetInstance()`（`form_manager_delegate.cpp:850`） | 正常 |
| AC-5.7 | **WHEN** 调用 `FormManagerDelegate::SetMultiInstanceFlag(bool)` **THEN** 无效果（该方法在头文件声明但无实现 — 死声明，ADR-7） | 异常 |

### US-6: 容器级全局操作

**As a** 系统管理者
**I want** 对所有容器实例执行广播通知、全局 GC 和看门狗注册
**So that** 系统级操作能覆盖所有活跃实例

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-6.1 | **WHEN** 调用 `AceEngine::NotifyContainers(callback)` **THEN** 在 shared_lock 下拷贝 containerMap_，然后对每个容器设置 `ContainerScope scope(instanceId)` 后调用 callback（`ace_engine.cpp:244-257`） | 正常 |
| AC-6.2 | **WHEN** 调用 `AceEngine::NotifyContainersOrderly(callback)` **THEN** 将 containerMap_ 拷贝到 `std::map`（按 instanceId 升序），然后对每个容器设置 ContainerScope 后调用 callback（`ace_engine.cpp:259-274`） | 正常 |
| AC-6.3 | **WHEN** 调用 `TriggerGarbageCollection()` **THEN** 拷贝 containerMap_，对每个容器调用 `container->TriggerGarbageCollection()`，**不设置** ContainerScope（`ace_engine.cpp:213-242`）；额外调用 `ImageCache::Purge()` 和 `PurgeMallocCache()` | 正常 |
| AC-6.4 | **WHEN** 调用 `DumpJsHeap(isPrivate)` **THEN** 拷贝 containerMap_，对每个容器调用 `container->DumpHeapSnapshot(isPrivate)`，**不设置** ContainerScope（`ace_engine.cpp:276-286`） | 正常 |
| AC-6.5 | **WHEN** 调用 `ForceFullGC()` **THEN** 拷贝 containerMap_，对每个容器调用 `container->ForceFullGC()`，**不设置** ContainerScope（`ace_engine.cpp:300-310`） | 正常 |
| AC-6.6 | **WHEN** 容器创建时调用 `AceEngine::RegisterToWatchDog(instanceId, taskExecutor, useUIAsJSThread)` **THEN** 委托给 `watchDog_->Register` 注册该实例的线程健康监控（`ace_engine.cpp:189-193`） | 正常 |
| AC-6.7 | **WHEN** 调用 `GetEnhancedContextBNotFoundMessage(instanceId, reason)` 且 instanceId 在 `destroyedUIContextCache_` 中 **THEN** 返回包含 reason 描述和缓存元数据（createTime/destroyTime/windowId/windowName）的诊断字符串（`ace_engine.cpp:327-334`） | 正常 |

### US-7: 跨实例通信

**As a** UIExtension / Dynamic Component
**I want** 在不同容器实例间传递数据和共享管线上下文
**So that** 跨实例场景（如主机-扩展容器、全局模态 UIExtension）能正确通信

| AC 编号 | 验收标准 | 类型 |
|---------|---------|------|
| AC-7.1 | **WHEN** 调用 `ContainerHandler::SendDataToHost(data, reply)` **THEN** 同步调用 `OnReciveData(data, reply)` 并返回其结果（`container_handler.h:72-75`）；`HandlerData` 包含 `actionCode` 和 `params` map | 正常 |
| AC-7.2 | **WHEN** `PlatformContainerHandler::OnReciveData` 收到 `ACCESSIBILITY_GET_RECT` actionCode **THEN** 读取主机节点的 transform rect 并填充到 `HandlerReply`（`frameworks/core/components_ng/pattern/ui_extension/platform_container_handler.cpp:103-112`） | 正常 |
| AC-7.3 | **WHEN** `GlobalPipelineContextManager::RegisterSessionId(uecName, sessionId)` 被调用 **THEN** 将 `uecName → sessionId` 映射存入 `sessionIdMap_`；重复注册被拒绝（`global_pipeline_context_manager.cpp:166-174`） | 正常 |
| AC-7.4 | **WHEN** `GetUecNameBySessionId(sessionId)` 被调用 **THEN** 线性扫描 `sessionIdMap_` 反向查找对应的 `uecName`（`global_pipeline_context_manager.cpp:176-185`） | 正常 |
| AC-7.5 | **WHEN** `UIContent::GetUIContent(instanceId)` 被调用 **THEN** 通过 dlsym 加载 ACE 库的 `OHOS_ACE_GetUIContent` 符号，该符号查询 `AceEngine::GetContainer(instanceId)` 获取容器的 UIContent（`ui_content.cpp:153-168`, `ui_content_impl.cpp:492-498`） | 正常 |
| AC-7.6 | **WHEN** `GetUIContent(instanceId)` 查询的 instanceId 不存在 **THEN** `AceContainer::GetUIWindow(instanceId)` 返回 `nullptr`（`ace_container.cpp:1741-1746`），最终返回 `nullptr` | 异常 |
| AC-7.7 | **WHEN** NAPI `containerUtils.createContainerWithoutWindow(context)` 被调用 **THEN** 生成 `WINDOW_FREE_CONTAINER` 类型 ID，创建 AceContainer（无窗口），注册到 AceEngine，存入 `g_WindowFreeContainer` 单例指针（`window_free_container.cpp:176-227`） | 正常 |
| AC-7.8 | **WHEN** `g_WindowFreeContainer` 非空时再次调用 `createContainerWithoutWindow` **THEN** 不创建新容器（单例守卫，`window_free_container.cpp:178`） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1 | R-1, R-2 | TASK-1 | 单元测试 | `ace_engine.cpp:124-135`, `container_scope.cpp:650-654` |
| AC-1.2 | R-3 | TASK-1 | 单元测试 | `container.h:820-829`, `container_consts.h:37` |
| AC-1.3 | R-3 | TASK-1 | 单元测试 | `container.h:823` |
| AC-1.4 | R-4, R-5 | TASK-1 | 单元测试 | `ace_engine.cpp:137-164`, `container_scope.cpp:662-671` |
| AC-1.5 | R-5 | TASK-1 | 单元测试 | `ace_engine.cpp:83,150-159` |
| AC-1.6 | R-6 | TASK-1 | 单元测试 | `ace_engine.cpp:129-133` |
| AC-1.7 | R-1 | TASK-1 | 单元测试 | `ace_engine.cpp:134` (try_emplace) |
| AC-2.1 | R-7 | TASK-1 | 单元测试 | `container_scope.cpp:673-676,710-721` |
| AC-2.2 | R-8 | TASK-1 | 单元测试 | `container_scope.cpp:318-321` |
| AC-2.3 | R-9 | TASK-1 | 单元测试 | `container_scope.cpp:383-401` |
| AC-2.4 | R-9 | TASK-1 | 单元测试 | `container_scope.cpp:349-363` |
| AC-2.5 | R-9 | TASK-1 | 单元测试 | `container_scope.cpp:365-372,383-401` |
| AC-2.6 | R-9 | TASK-1 | 单元测试 | `container_scope.cpp:374-381,383-401` |
| AC-2.7 | R-9 | TASK-1 | 单元测试 | `container_scope.cpp:333-347,383-401` |
| AC-2.8 | R-10 | TASK-1 | 单元测试 | `container_scope.cpp:403-425` |
| AC-2.9 | R-11 | TASK-1 | 单元测试 | `container.cpp:178-187` |
| AC-3.1 | R-12 | TASK-1 | 单元测试 | `container_scope.cpp:466-476` |
| AC-3.2 | R-13 | TASK-1 | 单元测试 | `container_scope.cpp:479-482` |
| AC-3.3 | R-14 | TASK-1 | 单元测试 | `container_scope.cpp:486-495` |
| AC-3.4 | R-15 | TASK-1 | 手动验证 | `ui_node.cpp:201-205` |
| AC-3.5 | R-15 | TASK-1 | 手动验证 | `ui_node.cpp:749-753` |
| AC-3.6 | R-16 | TASK-1 | 手动验证 | `ui_content_impl.cpp:1745-1752` |
| AC-3.7 | R-17 | TASK-1 | 单元测试 | `container_scope.cpp:498-504` |
| AC-3.8 | R-41 | TASK-1 | 手动验证 | `container_scope.cpp:471-476`, `ui_node.cpp:94-97`, `pipeline_context.cpp:436,475,509` |
| AC-3.9 | R-42 | TASK-1 | 单元测试 | `container_scope.cpp:622-638` |
| AC-3.10 | R-43 | TASK-1 | 代码评审 | `container_scope.cpp:447-450` |
| AC-3.11 | R-14 | TASK-1 | 手动验证 | `container_scope.cpp:486-495`, `ui_content_impl.cpp:3141-3143` |
| AC-4.1 | R-18 | TASK-1 | 集成测试 | `rosen_render_context.cpp:631-665` |
| AC-4.2 | R-18 | TASK-1 | 集成测试 | `rosen_render_context.cpp:647` |
| AC-4.3 | R-19 | TASK-1 | 集成测试 | `ui_content_impl.cpp:2683-2698` |
| AC-4.4 | R-19 | TASK-1 | 集成测试 | `ui_content_impl.cpp:2683-2698` |
| AC-4.5 | R-20 | TASK-1 | 单元测试 | `form_scoped_rs_transaction.cpp:41-76` |
| AC-4.6 | R-20 | TASK-1 | 单元测试 | `form_scoped_rs_transaction.cpp:41-76` |
| AC-4.7 | R-21 | TASK-1 | 集成测试 | `rosen_window.cpp:153-171` |
| AC-4.8 | R-21 | TASK-1 | 集成测试 | `rosen_window.cpp:153-171` |
| AC-4.9 | R-22 | TASK-1 | 集成测试 | `rosen_render_context.cpp:746-752` |
| AC-4.10 | R-23 | TASK-1 | 单元测试 | `system_properties.cpp:335-338` |
| AC-5.1 | R-24 | TASK-1 | 集成测试 | `form_pattern.cpp:1715-1719` |
| AC-5.2 | R-25 | TASK-1 | 单元测试 | `form_pattern.cpp:3078-3096` |
| AC-5.3 | R-26 | TASK-1 | 集成测试 | `form_pattern.cpp:1881-1884` |
| AC-5.4 | R-27 | TASK-1 | 集成测试 | `form_manager_delegate.cpp:240` |
| AC-5.5 | R-28 | TASK-1 | 集成测试 | `form_manager_delegate.cpp:839-861` |
| AC-5.6 | R-28 | TASK-1 | 集成测试 | `form_manager_delegate.cpp:850` |
| AC-5.7 | R-29 | TASK-1 | 代码评审 | `form_manager_delegate.h:159`（无实现） |
| AC-6.1 | R-30 | TASK-1 | 单元测试 | `ace_engine.cpp:244-257` |
| AC-6.2 | R-31 | TASK-1 | 单元测试 | `ace_engine.cpp:259-274` |
| AC-6.3 | R-32 | TASK-1 | 单元测试 | `ace_engine.cpp:213-242` |
| AC-6.4 | R-32 | TASK-1 | 单元测试 | `ace_engine.cpp:276-286` |
| AC-6.5 | R-32 | TASK-1 | 单元测试 | `ace_engine.cpp:300-310` |
| AC-6.6 | R-33 | TASK-1 | 单元测试 | `ace_engine.cpp:189-193` |
| AC-6.7 | R-34 | TASK-1 | 单元测试 | `ace_engine.cpp:327-334` |
| AC-7.1 | R-35 | TASK-1 | 集成测试 | `container_handler.h:72-75` |
| AC-7.2 | R-36 | TASK-1 | 集成测试 | `frameworks/core/components_ng/pattern/ui_extension/platform_container_handler.cpp:103-112` |
| AC-7.3 | R-37 | TASK-1 | 单元测试 | `global_pipeline_context_manager.cpp:166-174` |
| AC-7.4 | R-38 | TASK-1 | 单元测试 | `global_pipeline_context_manager.cpp:176-185` |
| AC-7.5 | R-39 | TASK-1 | 集成测试 | `ui_content.cpp:153-168`, `ui_content_impl.cpp:492-498` |
| AC-7.6 | R-39 | TASK-1 | 单元测试 | `ace_container.cpp:1741-1746` |
| AC-7.7 | R-40 | TASK-1 | 集成测试 | `window_free_container.cpp:176-227` |
| AC-7.8 | R-40 | TASK-1 | 单元测试 | `window_free_container.cpp:178` |

## 规则定义

| 规则 ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联 AC |
|---------|------|---------|---------|-----------|---------|
| R-1 | 行为 | `AddContainer(instanceId, container)` 被调用 | 写锁 `try_emplace` 插入 containerMap_；若 instanceId 在 destroyedUIContextCache_ 中则清除旧缓存 | try_emplace 不覆盖已存在的 key | AC-1.1, AC-1.7 |
| R-2 | 行为 | 容器创建后 `ContainerScope::Add(instanceId)` 被调用 | 在 mutex_ 保护下插入全局 `containerSet_` | 与 containerMap_ 需手动保持同步 | AC-1.1 |
| R-3 | 行为 | `GenerateId<type>()` 被调用 | 计算 `type * 100000 + atomic_counter.fetch_add(1) % 100000`，循环直到 `IsIdAvailable(id)` 返回 true | 每类型独立 atomic 计数器；PLUGIN_SUBCONTAINER 委托 PluginManager | AC-1.2, AC-1.3 |
| R-4 | 行为 | `RemoveContainer(instanceId)` 被调用 | 写锁查找 containerMap_；提取元数据到 UIContextCacheInfo；缓存淘汰（max 10, LRU by destroyTime）；从 containerMap_ 删除 | 查找失败时日志告警并返回 | AC-1.4 |
| R-5 | 边界 | destroyedUIContextCache_ 达到 10 条上限 | 用 `std::min_element` 找到 destroyTime_ 最早的条目并删除，存入新条目 | `MAX_DESTROYED_CACHE_SIZE = 10` | AC-1.4, AC-1.5 |
| R-6 | 异常 | AddContainer 的 instanceId 在 destroyedUIContextCache_ 中 | 清除旧缓存条目，输出 "Re-adding instanceId that was previously destroyed" 警告日志 | 缓存条目在重新添加时被清除 | AC-1.6 |
| R-7 | 行为 | `ContainerScope(id)` 构造 | `restoreId_ = CurrentId()`；`UpdateCurrent(id)` 设置 thread_local currentId_ = id | 析构时 `UpdateCurrent(restoreId_)` 恢复 | AC-2.1 |
| R-8 | 行为 | `CurrentId()` 被调用 | 返回 thread_local `currentId_` 原始值 | 可能返回 INSTANCE_ID_UNDEFINED (-1) | AC-2.2 |
| R-9 | 行为 | `SafelyId()` 被调用 | 六级回退：ContainerCount==0→UNDEFINED；==1→SingletonId()；RecentActiveId()≥0→返回；RecentForegroundId()≥0→返回；DefaultId()→返回 | isolated thread 场景下所有查询自动切换为线程局部值 | AC-2.3 ~ AC-2.7 |
| R-10 | 行为 | `CurrentIdWithReason()` 被调用 | 返回 `{id, reason}` 对，reason 为 SCOPE/ACTIVE/DEFAULT/SINGLETON/FOREGROUND/UNDEFINED 之一 | reason 映射通过 ReasonToDescription() 提供人类可读描述 | AC-2.8 |
| R-11 | 行为 | `GetByWindowId(windowId)` 被调用 | 遍历 containerMap_ 返回 GetWindowId() 匹配的容器 | 未找到返回 nullptr | AC-2.9 |
| R-12 | 行为 | `MarkIsolatedThread()` 被调用 | 设置 thread_local `isIsolatedThread_ = true` | 后续所有查询函数返回线程局部值 | AC-3.1 |
| R-13 | 行为 | `AddLocal(id)` 被调用（隔离线程） | 插入 thread_local `localContainerSet_` | 不影响全局 containerSet_ | AC-3.2 |
| R-14 | 行为 | `RemoveLocal(id)` 被调用（隔离线程） | 从 localContainerSet_ 删除；若 localRecentActiveId_ 或 localRecentForegroundId_ 等于 id 则重置为 DEFAULT_ID | 不触达全局原子（与 RemoveAndCheck 不同，后者通过 UpdateRecentActive 写全局原子）；销毁路径调用点 `ui_content_impl.cpp:3141-3143` | AC-3.3, AC-3.11 |
| R-15 | 异常 | UINode/PipelineContext 跨域操作时 isIsolatedThread_ 快照不匹配 | UINode 7 个验证点（AttachContext/AdoptChild/DoAddChild/GetContext/GetAttachedContext/GetContextWithCheck×2，LOGW 或 LOGE）；PipelineContext 5 个验证点（AddDirtyPropertyNode/AddDirtyCustomNode/AddDirtyLayoutNode/AddDirtyRenderNode/AddDirtyFreezeNode，均 LOGW） | 快照在构造时通过 `ContainerScope::IsIsolatedThread()` 获取，不可变更；仅输出日志不阻断操作 | AC-3.4, AC-3.5 |
| R-16 | 行为 | DC 初始化（isDynamicRender_ == true） | 调用 UpdateLocalCurrent → MarkIsolatedThread → AddLocal | 仅 DC 场景触发 | AC-3.6 |
| R-17 | 恢复 | `ResetIsolatedThread()` 被调用 | isIsolatedThread_ = false；localContainerSet_.clear()；localRecent*_ 重置 | 测试清理用 | AC-3.7 |
| R-18 | 行为 | `InitContext()` 执行 | multiInstanceEnabled_: GetRSUIContext(pipeline) 创建每实例 RS 节点；!multiInstanceEnabled_: RSUIDirector::Create(nullptr) 全局单例 | 弱符号 multiInstanceEnabled_ 可被产品覆盖 | AC-4.1, AC-4.2 |
| R-19 | 行为 | `SetUITaskRunner` 被调用 | multiInstanceEnabled_: (cb, 0, true)；!multiInstanceEnabled_: (cb, instanceId) | 回调中包裹 ContainerScope scope(id) | AC-4.3, AC-4.4 |
| R-20 | 行为 | `FormScopedRSTransaction` 构造/析构 | multiInstanceEnabled_: GetSyncTransactionHandler() per-instance；!multiInstanceEnabled_: RSSyncTransactionController::GetInstance() global | RAII: 构造 Open, 析构 Close（仅当 needCloseSync_） | AC-4.5, AC-4.6 |
| R-21 | 行为 | 子窗口初始化且 multiInstanceEnabled_ | 检查子窗口 RSUIContext 与父容器 RSUIContext 是否匹配；匹配→RegisterSubWindow 并跳过标准初始化 | 不匹配→走标准 Rosen 初始化 | AC-4.7, AC-4.8 |
| R-22 | 行为 | RS 节点创建且 multiInstanceEnabled_ | `isSkipCheckInMultiInstance = true`，绕过 RS 层跨实例验证 | 适用于 SurfaceNode/HardwareSurface/HardwareTexture | AC-4.9 |
| R-23 | 边界 | 系统参数 persist.rosen.rsclientmultiinstance.enabled 未设置 | `IsMultiInstanceEnabled()` 返回 true（默认 "1" != "0" 为 true） | 弱符号 init + ReadSystemParametersCallOnce 重读 | AC-4.10 |
| R-24 | 行为 | FormPattern 创建 form bridge 且 multiInstanceEnabled_ | 调用 GetRSUIContext() 获取 per-instance context，传递给 formManagerBridge_ | — | AC-5.1 |
| R-25 | 行为 | `FormPattern::GetRSUIContext()` 执行 | pipeline→RSUIDirector→GetRSUIContext() | — | AC-5.2 |
| R-26 | 行为 | Form surface node 回调且 multiInstanceEnabled_ | `node->SetRSUIContext(rsUIContext_)` | — | AC-5.3 |
| R-27 | 行为 | FormManagerDelegate::OnSurfaceCreate 获取 dispatcher | IPC 推送 SetMultiInstanceEnabled(GetMultiInstanceEnabled()) | 跨进程 IPC 消息 SET_MULTI_INSTANCE_ENABLED | AC-5.4 |
| R-28 | 行为 | FormManagerDelegate::NotifySurfaceChange | multiInstanceEnabled_: rsUIContext_->GetSyncTransactionHandler()；!multiInstanceEnabled_: RSSyncTransactionController::GetInstance() | 事务传递给 DispatchSurfaceChangeEvent | AC-5.5, AC-5.6 |
| R-29 | 异常 | 调用 FormManagerDelegate::SetMultiInstanceFlag(bool) | 无效果（死声明，头文件声明但无 .cpp 实现） | 实际传播通过 SystemProperties + IPC | AC-5.7 |
| R-30 | 行为 | `NotifyContainers(callback)` 被调用 | shared_lock 拷贝 containerMap_（unordered_map），遍历时设置 ContainerScope scope(first) | 拷贝后无锁迭代，避免回调中死锁 | AC-6.1 |
| R-31 | 行为 | `NotifyContainersOrderly(callback)` 被调用 | 拷贝到 std::map（instanceId 升序），遍历时设置 ContainerScope | 有序遍历 | AC-6.2 |
| R-32 | 行为 | `TriggerGarbageCollection/DumpJsHeap/ForceFullGC` 被调用 | 拷贝 containerMap_，遍历调用每容器的 GC 方法，**不设置** ContainerScope | 额外调用 ImageCache::Purge()、PurgeMallocCache()（仅 GC） | AC-6.3 ~ AC-6.5 |
| R-33 | 行为 | `RegisterToWatchDog(instanceId, taskExecutor, useUIAsJSThread)` | 委托给 watchDog_->Register | 每实例独立注册 | AC-6.6 |
| R-34 | 行为 | `GetEnhancedContextBNotFoundMessage(instanceId, reason)` | 组合 ReasonToDescription(reason) + destroyedUIContextCache_ 中的缓存元数据 | 缓存未命中返回 "not found in destroyed cache" | AC-6.7 |
| R-35 | 行为 | `ContainerHandler::SendDataToHost(data, reply)` | 同步调用 OnReciveData(data, reply) 并返回结果 | HandlerData: actionCode + params map | AC-7.1 |
| R-36 | 行为 | `PlatformContainerHandler::OnReciveData` 收到 ACCESSIBILITY_GET_RECT | 读取主机节点 transform rect，填充 HandlerReply | 同步阻塞调用方 | AC-7.2 |
| R-37 | 行为 | `RegisterSessionId(uecName, sessionId)` | sessionIdMap_ try_emplace，重复拒绝 | uecName = bundle.module.ability | AC-7.3 |
| R-38 | 行为 | `GetUecNameBySessionId(sessionId)` | 线性扫描 sessionIdMap_ 反向查找 | O(n) 复杂度 | AC-7.4 |
| R-39 | 行为 | `UIContent::GetUIContent(instanceId)` | dlsym 加载 ACE 库 → OHOS_ACE_GetUIContent → AceEngine::GetContainer → window→GetUIContent | 跨库 dlsym 查找 | AC-7.5, AC-7.6 |
| R-40 | 行为 | NAPI `createContainerWithoutWindow(context)` | GenerateId\<WINDOW_FREE_CONTAINER\>() → 创建 AceContainer（无窗口）→ AddContainer → 存入 g_WindowFreeContainer 单例 | 单例守卫：已存在则不创建 | AC-7.7, AC-7.8 |
| R-41 | 行为 | `IsIsolatedThread()` 被调用 | 返回当前线程的 thread_local `isIsolatedThread_` 标志；UINode 在构造时快照此值到成员 `isIsolatedThread_`（`ui_node.cpp:94-97`），PipelineContext 同理（`pipeline_context.cpp:436,475,509`） | 快照后不可变更，用于跨域一致性验证 | AC-3.8 |
| R-42 | 行为 | 隔离线程调用 `UpdateRecentActive(id)` / `UpdateRecentForeground(id)` | 双写：先 `recentActiveId_.store(id)` / `recentForegroundId_.store(id)` 写全局原子，再写线程局部 `localRecentActiveId_` / `localRecentForegroundId_` | 保证非隔离线程的全局可见性 | AC-3.9 |
| R-43 | 边界 | 隔离线程调用 `GetAllUIContextes()` | 仍返回全局 `containerSet_`（不检查 `isIsolatedThread_`） | 与其他 5 个基础查询函数行为不同；调用方不应假设隔离线程返回局部集 | AC-3.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.7 | 单元测试 | 容器创建/销毁/缓存/重添加全流程；try_emplace 不覆盖 |
| VM-2 | AC-1.2, AC-1.3 | 单元测试 | ID 分区范围正确性；连续生成递增性 |
| VM-3 | AC-2.1 ~ AC-2.9 | 单元测试 | RAII 恢复；六级回退链各级别；CurrentIdWithReason reason 枚举 |
| VM-4 | AC-3.1 ~ AC-3.11 | 单元测试 + 手动验证 | 隔离标志切换查询源；IsIsolatedThread getter + UINode/PipelineContext 快照不可变；UpdateRecentActive/Foreground 双写；GetAllUIContextes 不隔离例外；RemoveLocal 销毁路径；7+5 跨域 mismatch 验证点；DC 初始化顺序 |
| VM-5 | AC-4.1 ~ AC-4.10 | 集成测试 | per-instance RSUIContext 隔离；子窗口匹配；默认开启验证 |
| VM-6 | AC-5.1 ~ AC-5.7 | 集成测试 | Form RSUIContext 获取/设置；IPC 传播；死声明无效果 |
| VM-7 | AC-6.1 ~ AC-6.7 | 单元测试 | 广播 ContainerScope 设置；GC 不设 scope；缓存诊断 |
| VM-8 | AC-7.1 ~ AC-7.8 | 集成测试 | 同步通信；dlsym 查找；单例守卫 |

## API 变更分析

无新增/变更/废弃公共 API。该功能为框架内部架构能力。

相关 InnerAPI 清单：

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---------|---------|---------|--------|-----------|---------|---------|
| `UIContent::GetUIContent(instanceId)` | InnerApi | int32_t instanceId | UIContent* | N/A | 按 instanceId 查找 UIContent | AC-7.5 |
| `UIContent::GetUIContentWindowID(instanceId)` | InnerApi | int32_t instanceId | int32_t windowId | N/A | 按 instanceId 查找窗口 ID | — |
| `FormRendererDispatcherInterface::SetMultiInstanceEnabled(bool)` | InnerApi | bool isMultiInstanceEnabled | void | N/A | IPC 传播多实例标志 | AC-5.4 |
| `containerUtils.createContainerWithoutWindow(context)` | 框架内部 NAPI | AbilityContext context | frontend context value | N/A | 创建无窗口容器 | AC-7.7 |
| `containerUtils.destroyContainerWithoutWindow()` | 框架内部 NAPI | 无 | void | N/A | 销毁无窗口容器 | — |

> **框架内部 NAPI 说明**：`containerUtils` 编译产出 `libcontainerutils.z.so`，但不在 `bundle.json` `inner_kits` 中、不在 SDK KB 公开 d.ts 映射表中。ace_engine 内无对应 d.ts 文件。NAPI 源码权威定义：`interfaces/napi/kits/container_utils/js_container_utils.cpp:88`（`nm_modname = "arkui.containerUtils"`）。唯一消费方为 `frameworks/bridge/declarative_frontend/engine/jsUIContext.js:469-484`，通过引擎内部 `globalThis.requireNapi('arkui.containerUtils')` 加载，包装为公开 API `UIContext.createUIContextWithoutWindow()` / `destroyUIContextWithoutWindow()`。应用不直接 import 此模块。

### 变更/废弃 API

无。

## 接口规格

无新增接口规格。该功能不涉及公共 API 变更。

## 兼容性声明

- **已有 API 行为变更:** 否。该功能为框架内部架构，不涉及 SDK API 行为变更。
- **配置文件格式变更:** 否。系统参数为 key-value 字符串格式。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 10+。
- **API 版本号策略:** N/A（无 SDK API）。

**兼容性风险：**

1. **双注册表一致性**（ADR-1）：`AceEngine::containerMap_` 和 `ContainerScope::containerSet_` 是两个独立数据结构，一致性依赖调用顺序。若调用顺序错误可能导致不同步。
2. **多实例 RS 隔离默认开启**（ADR-3）：`persist.rosen.rsclientmultiinstance.enabled` 默认 `"1"`（true）。依赖全局 RS 单例的旧代码可能需要适配。弱符号允许产品覆盖。
3. **SafelyId() 回退链不确定性**（ADR-4）：同一方法在不同上下文（容器数量/活跃状态/前台状态）可能返回不同实例的 ID。调用方需了解回退优先级。
4. **GC 操作无 ContainerScope**（ADR-6）：`TriggerGarbageCollection`/`DumpJsHeap`/`ForceFullGC` 回调中 `CurrentId()` 可能不正确。
5. **SetMultiInstanceFlag() 死声明**（ADR-7）：调用该方法无效果。
6. **枚举值 8 被跳过**：`ContainerType` 枚举中值 8 不存在（`container_consts.h:22-33`），依赖连续枚举值的代码可能出错。
7. **GetAllUIContexts() 无锁**（`container_scope.cpp:447-450`）：并发调用时可能读取到不一致的容器集合。
8. **静态 DC 路径未隔离**：`arkts_dynamic_uicontext_impl.cpp:489-491` 仅调 `UpdateLocalCurrent`，不调 `MarkIsolatedThread`/`AddLocal`，与动态 DC 路径（`ui_content_impl.cpp:1745-1752`）行为不对称。推测：静态前端 DC 可能运行在主 UI 线程故无需隔离，待确认。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|---------|
| shared_mutex 读写锁 | containerMap_ 使用 `std::shared_mutex` 保护：写操作（Add/Remove）用 unique_lock，读操作（Get/Has/NotifyContainers）用 shared_lock | AC-1.1, AC-1.4, AC-6.1 |
| thread_local 实例隔离 | `currentId_`、`isIsolatedThread_`、`localContainerSet_` 等为 thread_local 变量，每线程独立 | AC-2.1, AC-3.1 |
| 隔离状态快照不可变 | UINode/PipelineContext 在构造时通过 `ContainerScope::IsIsolatedThread()` 快照隔离身份，后续不可变更；跨域操作在 7 个 UINode 验证点 + 5 个 PipelineContext 验证点检测并输出 LOGW/LOGE | AC-3.4, AC-3.5, AC-3.8 |
| 弱符号覆盖 | `multiInstanceEnabled_` 及其 getter/setter 为 `ACE_WEAK_SYM`（`__attribute__((weak))`），允许产品级覆盖 | AC-4.10 |
| NotifyContainers 快照一致性 | 广播操作先拷贝 containerMap_ 再无锁迭代，避免回调中操作 map 导致死锁 | AC-6.1, AC-6.2 |
| 单例约束 | WindowFreeContainer 全局仅允许一个实例（`g_WindowFreeContainer` 静态守卫） | AC-7.8 |
| 跨库 dlsym 查找 | `UIContent::GetUIContent` 通过 dlsym 跨库查找 ACE 引擎符号 | AC-7.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | NotifyContainers 广播延迟 < 16ms（100 容器） | 性能测试 | 快照+无锁迭代避免锁争用 |
| 性能 | GenerateId CAS 循环在无碰撞时单次完成 | 代码评审 | `container.h:820-829`（通常一次成功） |
| 内存 | destroyedUIContextCache_ 最大 10 条 UIContextCacheInfo | 代码评审 | `ace_engine.cpp:83` |
| 安全 | 生产环境中 ContainerScope 正确隔离各实例上下文 | 代码评审 | thread_local + shared_mutex |
| 可靠性 | 双注册表不同步时不崩溃（最坏情况为查询失败返回 nullptr） | 代码评审 | GetContainer 返回 nullptr 安全处理 |
| 可测试性 | ContainerScope 状态可通过 CurrentId/CurrentIdWithReason 查询 | 单元测试 | `container_scope.cpp:318-425` |
| 自动化维测 | GetEnhancedContextBNotFoundMessage 提供诊断信息 | hilog 验证 | `ace_engine.cpp:327-334` |
| 定界定位 | ENABLE_CONTAINER_SCOPE_TRACKING 提供栈历史和不平衡检测 | 编译宏控制 | `container_scope.cpp:119-620` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|-----------|---------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | 多实例架构不依赖屏幕形态 | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 是 | ContainerHandler::SendDataToHost 用于 DC 场景的无障碍 rect 查询 | AC-7.2 |
| 大字体 | 否 | 多实例架构不依赖字体缩放 | — |
| 深色模式 | 否 | 多实例架构不依赖颜色模式 | — |
| 多窗口/分屏 | 是 | 多实例是多窗口/分屏的基础架构支撑 | AC-4.1, AC-4.7 |
| 多用户 | 否 | 系统参数为全局参数，不区分用户 | — |
| 版本升级 | 否 | 无持久化数据，无迁移需求 | — |
| 生态兼容 | 是 | 弱符号 multiInstanceEnabled_ 允许产品线自定义 RS 隔离策略 | AC-4.10 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 多实例管理全能力
  作为 框架开发者
  我想要 在同进程中管理多个独立 UI 容器实例
  以便 支持多窗口、子窗口、对话框、卡片等同进程共存场景

  Scenario: 创建 Stage 容器并注册到全局注册表
    Given 进程中无 ID 为 100001 的容器
    When 调用 AceContainer::CreateContainer(100001, STAGE, ...)
    Then AceEngine::containerMap_ 中存在 key=100001
    And ContainerScope::containerSet_ 中存在 100001
    And 当前线程 currentId_ 被设为 100001

  Scenario Outline: 容器 ID 分区生成
    Given GenerateId 被调用且之前未生成过该类型 ID
    When 调用 GenerateId<<type>>()
    Then 返回的 ID 范围为 <min> 到 <min>+99999

    Examples:
      | type | min |
      | STAGE_CONTAINER | 100000 |
      | FA_CONTAINER | 200000 |
      | DC_CONTAINER | 700000 |
      | WINDOW_FREE_CONTAINER | 900000 |

  Scenario: 销毁容器后缓存元数据用于诊断
    Given 容器 instanceId=100001 已存在
    When 调用 DestroyContainer(100001)
    Then containerMap_ 中 key=100001 被删除
    And destroyedUIContextCache_ 中存在 instanceId=100001 的条目
    And containerSet_ 中 100001 被删除

  Scenario: destroyedUIContextCache 淘汰最早条目
    Given destroyedUIContextCache_ 已有 10 条记录
    When 第 11 个容器被销毁
    Then destroyTime_ 最早的条目被删除
    And 新条目存入缓存

  Scenario Outline: SafelyId 多级回退
    Given 容器环境为 <scenario>
    When 调用 SafelyId()
    Then 返回 <expected_id>，reason 为 <reason>

    Examples:
      | scenario | expected_id | reason |
      | 无容器 | -1 | UNDEFINED |
      | 1个容器 | singleton_id | SINGLETON |
      | 多容器且有活跃 | active_id | ACTIVE |
      | 多容器无活跃有前台 | foreground_id | FOREGROUND |
      | 多容器无活跃无前台 | default_id | DEFAULT |

  Scenario: DC 线程隔离初始化
    Given UIContentImpl 初始化且 isDynamicRender_ = true
    When Initialize() 执行到 DC 分支
    Then UpdateLocalCurrent(instanceId) 被调用
    And MarkIsolatedThread() 被调用
    And AddLocal(instanceId) 被调用
    And 后续该线程的 DefaultId() 返回 localContainerSet_ 的值

  Scenario: IsIsolatedThread getter 与构造时快照不可变
    Given 线程已调用 MarkIsolatedThread()
    When UINode 在该线程上构造
    Then UINode::IsIsolatedThread() 返回 true（构造时快照）
    And 即使后续线程调用 ResetIsolatedThread()，该 UINode 的 IsIsolatedThread() 仍为 true

  Scenario: 隔离线程 UpdateRecentActive 双写
    Given 线程已调用 MarkIsolatedThread()
    When 调用 UpdateRecentActive(100001)
    Then 全局原子 recentActiveId_ 被设为 100001
    And 线程局部 localRecentActiveId_ 也被设为 100001
    And 非隔离线程调用 RecentActiveId() 返回 100001（全局原子可见）

  Scenario: GetAllUIContextes 不受隔离影响
    Given 线程已调用 MarkIsolatedThread()
    And localContainerSet_ 中有 ID 100001
    And 全局 containerSet_ 中有 ID 200001
    When 隔离线程调用 GetAllUIContextes()
    Then 返回全局 containerSet_（包含 200001）
    But 不返回 localContainerSet_（100001 不在返回值中）

  Scenario: DC 销毁路径 RemoveLocal
    Given DC 线程已隔离且 localContainerSet_ 中有 ID 100001
    And localRecentActiveId_ = 100001
    When UIContentImpl 析构调用 RemoveLocal(100001)
    Then 100001 从 localContainerSet_ 删除
    And localRecentActiveId_ 重置为 DEFAULT_ID
    But 全局原子 recentActiveId_ 不被修改（与 RemoveAndCheck 不同）

  Scenario: 多实例 RS 隔离（默认开启）
    Given 系统参数 persist.rosen.rsclientmultiinstance.enabled 未设置（默认 "1"）
    When RosenRenderContext::InitContext() 执行
    Then GetMultiInstanceEnabled() 返回 true
    And RS 节点使用 per-instance RSUIContext 创建
    And isSkipCheckInMultiInstance 被设为 true

  Scenario: 子窗口 RSUIContext 匹配检查
    Given multiInstanceEnabled_ = true
    And 子窗口容器（IsSubContainer = true）
    When RosenWindow::Init() 执行
    Then 检查子窗口 RSUIContext 是否与父容器匹配
    And 若匹配则 RegisterSubWindow(id_) 并跳过标准初始化

  Scenario: NotifyContainers 为每个容器设置 ContainerScope
    Given 进程中有容器 A(id=100001) 和 B(id=100002)
    When 调用 NotifyContainers(callback)
    Then callback 对 A 执行时 ContainerScope::CurrentId() == 100001
    And callback 对 B 执行时 ContainerScope::CurrentId() == 100002

  Scenario: GC 操作不设置 ContainerScope
    Given 进程中有容器 A(id=100001) 和 B(id=100002)
    And 当前线程 currentId_ 为 100001
    When 调用 TriggerGarbageCollection()
    Then 遍历所有容器调用 TriggerGarbageCollection()
    But 遍历过程中 currentId_ 保持为 100001（不为每个容器设置 scope）

  Scenario: SetMultiInstanceFlag 死声明
    Given FormManagerDelegate 实例
    When 调用 SetMultiInstanceFlag(true)
    Then 无任何效果（方法声明存在但无实现）
    And FormManagerDelegate::isMultiInstanceEnable_ 成员未被修改
    Note: 源码命名不一致 — FormManagerDelegate 为 isMultiInstanceEnable_（无 d），
    FormRendererDispatcherImpl 为 isMultiInstanceEnabled_（有 d）

  Scenario: WindowFreeContainer 单例守卫
    Given g_WindowFreeContainer 已非空（存在一个无窗口容器）
    When 再次调用 createContainerWithoutWindow(context)
    Then 不创建新容器
    And 返回已有的 frontend context
```

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
    query: "AceEngine singleton containerMap_ add remove container lifecycle management"
  - repo: "openharmony/arkui_ace_engine"
    query: "ContainerScope RAII thread_local currentId_ isolated thread MarkIsolatedThread"
  - repo: "openharmony/arkui_ace_engine"
    query: "Container GenerateId type partition CONTAINER_ID_DIVIDE_SIZE collision detection"
  - repo: "openharmony/arkui_ace_engine"
    query: "SafelyId CurrentIdWithReason fallback chain SingletonId RecentActiveId DefaultId"
  - repo: "openharmony/arkui_ace_engine"
    query: "multiInstanceEnabled RSUIContext per-instance RosenRenderContext FormScopedRSTransaction"
  - repo: "openharmony/arkui_ace_engine"
    query: "NotifyContainers NotifyContainersOrderly ContainerScope GC TriggerGarbageCollection"
  - repo: "openharmony/arkui_ace_engine"
    query: "FormManagerDelegate SetMultiInstanceFlag dead declaration form_renderer_dispatcher"
  - repo: "openharmony/arkui_ace_engine"
    query: "GlobalPipelineContextManager sessionId UIExtension ContainerHandler SendDataToHost"
```

**关键文档：** `specs/03-engine-framework/06-multi-instance-management/01-multi-instance-management/design.md`（DESIGN-Func-03-06-01）
