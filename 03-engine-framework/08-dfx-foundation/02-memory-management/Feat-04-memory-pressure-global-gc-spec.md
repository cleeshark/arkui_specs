# 特性规格

> Func-03-08-02-Feat-04 系统内存压力监听与全局 GC：固化系统内存压力信号从 `UIContentImpl` 到 PipelineContext 节点级分发、Declarative 前端 JS 线程路由、以及 `AceEngine::TriggerGarbageCollection` 多线程 GC 的完整行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 系统内存压力监听与全局 GC (Memory Pressure Dispatch & Global GC) |
| 特性编号 | Func-03-08-02-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录内存压力信号分发链路 + 全局 GC 管线已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 内存压力信号分发规格 | 补录 `UIContentImpl::NotifyMemoryLevel` → PipelineContext 节点级分发的完整链路 |
| ADDED | 节点注册/反注册规格 | 补录 `AddNodesToNotifyMemoryLevel` / `RemoveNodesToNotifyMemoryLevel` 注册生命周期 |
| ADDED | 消费端响应规格 | 补录 LazyForEachNode / RepeatVirtualScroll2Node / ArkoalaLazyNode 在 LOW/CRITICAL 级别清理缓存的行为 |
| ADDED | Declarative 前端路由规格 | 补录 `DeclarativeFrontend::OnMemoryLevel` → JS 线程 `onMemoryLevel` 回调的分发路径 |
| ADDED | 全局 GC 管线规格 | 补录 `AceEngine::TriggerGarbageCollection` 的 PLATFORM/GPU/IO 线程 PurgeMallocCache + 容器 GC + ImageCache::Purge + 后台线程 purge 链路 |
| ADDED | 后台线程 purge 规格 | 补录 `BackgroundTaskExecutor::TriggerGarbageCollection` 位掩码多线程 purge 机制 |
| ADDED | 容器级 GC 规格 | 补录 `AceContainer::TriggerGarbageCollection` 按线程分发 PurgeMallocCache + JS 前端 GC |
| ADDED | WatchDog GC 触发规格 | 补录 WatchDog 在 ANR 恢复时触发全局 GC 的行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/03-engine-framework/08-dfx-foundation/02-memory-management/design.md` | Baselined |

---

## 用户故事

### US-1: 系统内存压力信号分发至 PipelineContext

**作为** 系统开发者,
**我想要** 在系统发出内存压力信号时将 level 值传递到对应窗口的 PipelineContext,
**以便** 驱动框架内部的缓存清理和 GC 机制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `UIContentImpl::NotifyMemoryLevel(level)` 被调用 THEN 通过 `Platform::AceContainer::GetContainer(instanceId_)` 获取容器并校验非空 | 行为 |
| AC-1.2 | WHEN 容器获取成功 THEN 获取 `pipelineContext` 并校验非空后调用 `pipelineContext->NotifyMemoryLevel(level)` | 行为 |
| AC-1.3 | WHEN NotifyMemoryLevel 执行 THEN 在 `ContainerScope scope(instanceId_)` 作用域内分发到 PipelineContext | 行为 |
| AC-1.4 | WHEN 容器或 pipelineContext 为空 THEN 直接返回不执行分发 | 异常 |

### US-2: 节点级内存压力通知与失效节点自动清理

**作为** 系统开发者,
**我想要** PipelineContext 维护已注册节点列表并在内存压力时逐节点通知,
**以便** 各消费节点能根据自身策略执行缓存释放。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `AddNodesToNotifyMemoryLevel(nodeId)` 调用 THEN 将 `nodeId` 追加到 `nodesToNotifyMemoryLevel_` 列表尾部 | 行为 |
| AC-2.2 | WHEN `RemoveNodesToNotifyMemoryLevel(nodeId)` 调用 THEN 从 `nodesToNotifyMemoryLevel_` 移除所有匹配 `nodeId` 的条目 | 行为 |
| AC-2.3 | WHEN `PipelineContext::NotifyMemoryLevel` 执行 THEN 遍历 `nodesToNotifyMemoryLevel_`，对每个 nodeId 通过 `ElementRegister::GetInstance()->GetUINodeById()` 获取节点 | 行为 |
| AC-2.4 | WHEN 获取到的节点为空 THEN 从列表中 `erase` 该条目并继续遍历 | 异常 |
| AC-2.5 | WHEN 获取到的节点非空 THEN 调用 `node->OnNotifyMemoryLevel(level)` | 行为 |
| AC-2.6 | WHEN 遍历结束且 `window_` 非空 THEN 调用 `window_->FlushTasks()` 刷新待执行任务 | 行为 |

### US-3: 懒加载列表节点在内存压力下清理缓存

**作为** 应用开发者,
**我想要** LazyForEachNode / RepeatVirtualScroll2Node / ArkoalaLazyNode 在收到 LOW 或 CRITICAL 级别信号时自动清理缓存,
**以便** 释放离屏缓存项占用的内存。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN LazyForEachNode::OnNotifyMemoryLevel(level) 且 level 为 `MEMORY_LEVEL_LOW` 或 `MEMORY_LEVEL_CRITICAL` THEN 调用 `CleanCache(false)` 异步清理 | 行为 |
| AC-3.2 | WHEN RepeatVirtualScroll2Node::OnNotifyMemoryLevel(level) 且 level 为 LOW 或 CRITICAL THEN 调用 `CleanCache(false)` | 行为 |
| AC-3.3 | WHEN ArkoalaLazyNode::OnNotifyMemoryLevel(level) 且 level 为 LOW 或 CRITICAL THEN 调用 `CleanCache(false)` | 行为 |
| AC-3.4 | WHEN level 既非 LOW 也非 CRITICAL THEN 不触发缓存清理 | 边界 |

### US-4: Declarative 前端 JS 线程内存级别路由

**作为** 应用开发者,
**我想要** 内存级别信号路由到 Declarative 前端 JS 线程的 `onMemoryLevel` 回调,
**以便** 应用侧业务逻辑能感知系统内存压力。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `DeclarativeFrontend::OnMemoryLevel(level)` 调用 THEN 转发到 `delegate_->OnMemoryLevel(level)` | 行为 |
| AC-4.2 | WHEN `FrontendDelegateDeclarative::OnMemoryLevel(level)` 调用 THEN 将 `onMemoryLevel(level)` 投递到 JS 线程，任务名为 `"ArkUIMemoryLevel"` | 行为 |
| AC-4.3 | WHEN `onMemoryLevel_` 回调未设置 THEN 在 JS 线程任务中不执行回调 | 异常 |

### US-5: 全局 GC 多线程 PurgeMallocCache

**作为** 系统开发者,
**我想要** `AceEngine::TriggerGarbageCollection` 在多个关键线程上执行 `PurgeMallocCache` 并清理全局缓存,
**以便** 全面释放框架持有的内存资源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `AceEngine::TriggerGarbageCollection` 调用 THEN 在共享锁下拷贝 `containerMap_`，若为空则直接返回 | 行为 |
| AC-5.2 | WHEN 拷贝成功 THEN 从首个容器获取 TaskExecutor，向 PLATFORM 线程投递 `PurgeMallocCache()` 任务 | 行为 |
| AC-5.3 | WHEN 定义了 `OHOS_PLATFORM` 且 `ENABLE_NATIVE_VIEW` THEN 额外向 GPU 和 IO 线程投递 `PurgeMallocCache()` | 行为 |
| AC-5.4 | WHEN 容器遍历 THEN 对每个 container 调用 `container->TriggerGarbageCollection()` | 行为 |
| AC-5.5 | WHEN 容器遍历结束 THEN 调用 `ImageCache::Purge()` 清理图形资源缓存 | 行为 |
| AC-5.6 | WHEN ImageCache::Purge 完成 THEN 调用 `BackgroundTaskExecutor::GetInstance().TriggerGarbageCollection()` 触发后台线程 purge | 行为 |
| AC-5.7 | WHEN 后台线程 purge 触发完成 THEN 在调用线程同步执行 `PurgeMallocCache()` | 行为 |

### US-6: 后台线程位掩码多线程 purge

**作为** 系统开发者,
**我想要** BackgroundTaskExecutor 通过位掩码机制并行通知所有后台线程执行 purge,
**以便** 释放各后台线程的 malloc 缓存。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `BackgroundTaskExecutor::TriggerGarbageCollection` 调用 THEN 设置 `purgeFlags_ = PURGE_FLAG_MASK`（即 `(1 << MAX_BACKGROUND_THREADS) - 1 = 255`）并 `condition_.notify_all()` | 行为 |
| AC-6.2 | WHEN 后台线程在空闲（tasks_ 和 lowPriorityTasks_ 均空）时被唤醒 THEN 检查 `(purgeFlags_ & purgeFlag) == purgeFlag`，其中 `purgeFlag = 1u << (threadNo - 1)` | 行为 |
| AC-6.3 | WHEN purgeFlag 匹配成功 THEN 解锁后执行 `PurgeMallocCache()`，再重新加锁清除 `purgeFlags_ &= ~purgeFlag` | 行为 |
| AC-6.4 | WHEN tasks_ 或 lowPriorityTasks_ 非空 THEN 优先处理任务，不执行 purge | 边界 |

### US-7: 容器级 GC 按线程分发

**作为** 系统开发者,
**我想要** AceContainer::TriggerGarbageCollection 将 PurgeMallocCache 分发到各工作线程并在 JS 线程触发前端 GC,
**以便** 确保每个线程的内存缓存都被清理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `AceContainer::TriggerGarbageCollection` 执行 THEN 在 `ContainerScope scope(instanceId_)` 作用域内分发 | 行为 |
| AC-7.2 | WHEN 未定义 `OHOS_PLATFORM` 或未定义 `ENABLE_NATIVE_VIEW` THEN 向 GPU 和 IO 线程投递 `PurgeMallocCache()` | 行为 |
| AC-7.3 | WHEN 容器 GC 执行 THEN 向 UI 线程投递 `PurgeMallocCache()` | 行为 |
| AC-7.4 | WHEN 容器 GC 执行 THEN 向 JS 线程投递任务：升级 `frontend_` 弱引用后调用 `sp->TriggerGarbageCollection()` + `PurgeMallocCache()` | 行为 |
| AC-7.5 | WHEN JS 线程上 `frontend_` 弱引用升级失败 THEN 不调用前端 GC，但仍执行 `PurgeMallocCache()` | 异常 |

### US-8: WatchDog ANR 恢复触发全局 GC

**作为** 系统开发者,
**我想要** WatchDog 在检测到 GC 信号时自动触发全局 GC,
**以便** 在 ANR 恢复过程中主动释放内存资源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN WatchDog 检测到 `SIGNAL_FOR_GC` THEN 调用 `AceEngine::Get().TriggerGarbageCollection()` | 行为 |
| AC-8.2 | WHEN GC 信号处理后 THEN 继续以 `GC_CHECK_PERIOD` 周期重新检查 GC 信号 | 恢复 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1, R-2 | TASK-04 | 单测 | `adapter/ohos/entrance/ui_content_impl.cpp:4847-4857` |
| AC-2.1~2.6 | R-3, R-4, R-5, R-6 | TASK-04 | 单测 | `frameworks/core/pipeline_ng/pipeline_context.cpp:6250-6275` |
| AC-3.1~3.4 | R-7, R-8, R-9 | TASK-04 | 单测 | `lazy_for_each_node.cpp:860-864`; `repeat_virtual_scroll_2_node.cpp:1053-1057`; `arkoala_lazy_node.cpp:722-726` |
| AC-4.1~4.3 | R-10, R-11 | TASK-04 | 单测 | `declarative_frontend.cpp:1163-1167`; `frontend_delegate_declarative.cpp:662-671` |
| AC-5.1~5.7 | R-12, R-13, R-14, R-15 | TASK-04 | 单测 | `frameworks/core/common/ace_engine.cpp:213-242` |
| AC-6.1~6.4 | R-16, R-17 | TASK-04 | 单测 | `background_task_executor.cpp:28-29, 196-209, 228-233` |
| AC-7.1~7.5 | R-18, R-19 | TASK-04 | 单测 | `adapter/ohos/entrance/ace_container.cpp:2602-2620` |
| AC-8.1~8.2 | R-20 | TASK-04 | 单测 | `frameworks/core/common/watch_dog.cpp:62-70` |

---

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | UIContentImpl::NotifyMemoryLevel(level) | 获取 container → pipelineContext，在 `ContainerScope` 内调用 `pipelineContext->NotifyMemoryLevel(level)` | `ui_content_impl.cpp:4851-4856` | AC-1.1~1.3 |
| R-2 | 异常 | container 或 pipelineContext 为空 | CHECK_NULL_VOID 短路返回 | `ui_content_impl.cpp:4852, 4854` | AC-1.4 |
| R-3 | 行为 | AddNodesToNotifyMemoryLevel(nodeId) | `nodesToNotifyMemoryLevel_.emplace_back(nodeId)` | `pipeline_context.cpp:6252`; `pipeline_context.h:1473` | AC-2.1 |
| R-4 | 行为 | RemoveNodesToNotifyMemoryLevel(nodeId) | `nodesToNotifyMemoryLevel_.remove(nodeId)` 移除所有匹配项 | `pipeline_context.cpp:6257` | AC-2.2 |
| R-5 | 行为 | PipelineContext::NotifyMemoryLevel 遍历 | 对每个 nodeId 调用 `ElementRegister::GetUINodeById` 获取节点，非空调用 `OnNotifyMemoryLevel(level)` | `pipeline_context.cpp:6262-6270` | AC-2.3, AC-2.5 |
| R-6 | 异常 | GetUINodeById 返回空 | `erase` 该条目；遍历后调用 `window_->FlushTasks()` | `pipeline_context.cpp:6265-6266, 6272-6274` | AC-2.4, AC-2.6 |
| R-7 | 行为 | LazyForEachNode::OnNotifyMemoryLevel | level 为 LOW 或 CRITICAL 时调用 `CleanCache(false)` | `lazy_for_each_node.cpp:860-864` | AC-3.1 |
| R-8 | 行为 | RepeatVirtualScroll2Node::OnNotifyMemoryLevel | level 为 LOW 或 CRITICAL 时调用 `CleanCache(false)` | `repeat_virtual_scroll_2_node.cpp:1053-1057` | AC-3.2 |
| R-9 | 行为 | ArkoalaLazyNode::OnNotifyMemoryLevel | level 为 LOW 或 CRITICAL 时调用 `CleanCache(false)` | `arkoala_lazy_node.cpp:722-726` | AC-3.3 |
| R-10 | 行为 | DeclarativeFrontend::OnMemoryLevel | 转发到 `delegate_->OnMemoryLevel(level)` | `declarative_frontend.cpp:1163-1167` | AC-4.1 |
| R-11 | 行为 | FrontendDelegateDeclarative::OnMemoryLevel | 将 `onMemoryLevel(level)` 投递到 JS 线程，任务名 `"ArkUIMemoryLevel"`；回调未设置则不执行 | `frontend_delegate_declarative.cpp:662-671` | AC-4.2, AC-4.3 |
| R-12 | 行为 | AceEngine::TriggerGarbageCollection | 共享锁拷贝 containerMap_；空则返回；PLATFORM 线程投递 PurgeMallocCache | `ace_engine.cpp:215-226` | AC-5.1, AC-5.2 |
| R-13 | 行为 | OHOS_PLATFORM && ENABLE_NATIVE_VIEW | 额外向 GPU（`ace_engine.cpp:229-230`）和 IO（`:231-232`）线程投递 PurgeMallocCache | `ace_engine.cpp:227-233` | AC-5.3 |
| R-14 | 行为 | 容器遍历 | 对每个 container 调用 `TriggerGarbageCollection()` | `ace_engine.cpp:235-237` | AC-5.4 |
| R-15 | 行为 | 容器遍历后 | 调用 `ImageCache::Purge()`（`:239`）→ `BackgroundTaskExecutor::TriggerGarbageCollection()`（`:240`）→ `PurgeMallocCache()`（`:241`） | `ace_engine.cpp:239-241` | AC-5.5~5.7 |
| R-16 | 行为 | BackgroundTaskExecutor::TriggerGarbageCollection | `purgeFlags_ = PURGE_FLAG_MASK`（255）+ `notify_all()` | `background_task_executor.cpp:228-233`; `:29` | AC-6.1 |
| R-17 | 边界 | 后台线程空闲时检查 purgeFlag | 匹配则解锁执行 PurgeMallocCache → 清除位；有任务则优先处理任务不 purge | `background_task_executor.cpp:196-209` | AC-6.2~6.4 |
| R-18 | 行为 | AceContainer::TriggerGarbageCollection | ContainerScope 内分发；非 native-view 时投递 GPU + IO 的 PurgeMallocCache | `ace_container.cpp:2602-2609` | AC-7.1, AC-7.2 |
| R-19 | 行为 | 容器 GC 线程分发 | UI 线程 PurgeMallocCache（`:2610`）；JS 线程升级 frontend_ 后调 `TriggerGarbageCollection()` + PurgeMallocCache（`:2611-2619`） | `ace_container.cpp:2610-2619` | AC-7.3~7.5 |
| R-20 | 恢复 | WatchDog 检测 SIGNAL_FOR_GC | 调用 `AceEngine::Get().TriggerGarbageCollection()`；之后以 `GC_CHECK_PERIOD` 重新检查 | `watch_dog.cpp:62-70` | AC-8.1, AC-8.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, R-2, AC-1.1~1.4 | 单测 | UIContentImpl → container → pipelineContext 分发链路 + 空值守护 |
| VM-2 | R-3, R-4, AC-2.1~2.2 | 单测 | AddNodesToNotifyMemoryLevel / RemoveNodesToNotifyMemoryLevel 列表操作 |
| VM-3 | R-5, R-6, AC-2.3~2.6 | 单测 | NotifyMemoryLevel 遍历 + 失效节点 erase + FlushTasks |
| VM-4 | R-7~R-9, AC-3.1~3.4 | 单测 | 三种懒加载节点 LOW/CRITICAL → CleanCache(false) |
| VM-5 | R-10, R-11, AC-4.1~4.3 | 单测 | DeclarativeFrontend → FrontendDelegateDeclarative JS 线程路由 |
| VM-6 | R-12~R-15, AC-5.1~5.7 | 单测 | AceEngine::TriggerGarbageCollection 全链路 |
| VM-7 | R-16, R-17, AC-6.1~6.4 | 单测 | BackgroundTaskExecutor 位掩码 purge 机制 |
| VM-8 | R-18, R-19, AC-7.1~7.5 | 单测 | AceContainer 线程分发 + 前端弱引用升级 |
| VM-9 | R-20, AC-8.1~8.2 | 单测 | WatchDog SIGNAL_FOR_GC → TriggerGarbageCollection |
| VM-10 | 全量 | 集成/hidumper | 内存压力场景下多线程 purge 可观测 |

---

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

---

## 接口规格

### 接口定义

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 无
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9+
- **ABI 影响:** 无（内存压力分发与 GC 均通过内部虚函数和 TaskExecutor 投递实现，不跨模块导出）

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| PipelineBase 虚函数默认空实现 | `PipelineBase::NotifyMemoryLevel`（`pipeline_base.h:1121`）为 `virtual void NotifyMemoryLevel(int32_t) {}`，PipelineContext 覆写提供节点级分发 | AC-1.2, AC-2.3 |
| 节点列表使用 list<int32_t> | `nodesToNotifyMemoryLevel_`（`pipeline_context.h:1473`）存储 nodeId 而非节点指针，遍历时通过 ElementRegister 解引用，避免悬挂指针 | AC-2.1~2.5 |
| GPU/IO 线程共享 | 定义 `OHOS_PLATFORM && ENABLE_NATIVE_VIEW` 时 GPU/IO 线程共享，AceEngine 直接 purge；否则由 AceContainer 分别 purge | AC-5.3, AC-7.2 |
| 后台线程位掩码 | `PURGE_FLAG_MASK = (1 << 8) - 1 = 255`，每线程对应 1 bit，最多支持 8 个后台线程 | AC-6.1 |
| Frontend::OnMemoryLevel 纯虚函数 | `frontend.h:297` 声明为 `virtual void OnMemoryLevel(int32_t) = 0`，所有前端必须实现 | AC-4.1 |
| ContainerMap 共享锁拷贝 | `AceEngine::TriggerGarbageCollection` 先在 `shared_lock` 下拷贝 containerMap_ 再操作，避免长时间持锁 | AC-5.1 |
| ImageCache::Purge 为静态方法 | `image_cache.h:99` 声明 `static void Purge()`，实现于 `drawing_image.cpp:405` 调用 `SkGraphics::PurgeResourceCache()` | AC-5.5 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | NotifyMemoryLevel 遍历为 O(已注册节点数)；失效节点在遍历时一并清理，无额外扫描 | benchmark / trace | `pipeline_context.cpp:6262-6271` |
| 内存 | 全局 GC 释放 PLATFORM/GPU/IO/UI/JS/BACKGROUND 线程 malloc 缓存 + ImageCache 图形资源缓存 + 各容器前端 GC | hidumper | `ace_engine.cpp:225-241` |
| 稳定性 | containerMap_ 使用 `shared_mutex` 共享锁保护；后台线程 purge 使用 `mutex` + `condition_variable` 协调，无数据竞争 | 单测 / TSan | `ace_engine.cpp:217`; `background_task_executor.cpp:197, 230` |
| 并发 | 后台线程 purge 位掩码确保每线程仅 purge 一次（位清除后不再重复） | 单测 | `background_task_executor.cpp:200-208` |

---

## 多设备适配声明

无差异

> 本特性为框架内部内存管理管线，在各设备形态（手机 / 平板 / 折叠屏）上行为一致。GPU/IO 线程 purge 策略由编译宏 `OHOS_PLATFORM` + `ENABLE_NATIVE_VIEW` 决定，与设备形态无关。

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | N/A | 内存压力分发与 GC 不影响无障碍语义 | — |
| 大字体 | N/A | GC 管线与字体缩放无关 | — |
| 深色模式 | N/A | GC 管线与颜色无关 | — |
| 多窗口/分屏 | 是 | 每个窗口的 UIContentImpl 独立接收内存压力信号；AceEngine::TriggerGarbageCollection 遍历所有 container 逐个执行 GC | AC-1.1, AC-5.4 |
| 多用户 | N/A | 内存压力分发无用户态差异 | — |
| 版本升级 | N/A | 本特性自 API 9 起存在，无版本守护分支 | — |
| SceneBoard | 是 | SceneBoard 窗口同样参与全局 GC（containerMap_ 遍历不区分窗口类型） | AC-5.4 |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（UIContentImpl::NotifyMemoryLevel → PipelineContext 节点分发 → Declarative 前端路由 → AceEngine::TriggerGarbageCollection 全局 GC → BackgroundTaskExecutor 位掩码 purge → AceContainer 线程分发 → WatchDog GC 触发；不含 MemoryManager 回收管线、ImageCache 多级缓存 LRU 策略、SharedImageManager 驱逐策略）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致
- [x] 所有数值来自真实源码（PURGE_FLAG_MASK=255、MAX_BACKGROUND_THREADS=8、行号引用均可追溯）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "UIContentImpl NotifyMemoryLevel PipelineContext container dispatch"
  - repo: "openharmony/ace_engine"
    query: "PipelineContext NotifyMemoryLevel nodesToNotifyMemoryLevel AddNodesToNotifyMemoryLevel RemoveNodesToNotifyMemoryLevel"
  - repo: "openharmony/ace_engine"
    query: "LazyForEachNode RepeatVirtualScroll2Node ArkoalaLazyNode OnNotifyMemoryLevel CleanCache"
  - repo: "openharmony/ace_engine"
    query: "DeclarativeFrontend OnMemoryLevel FrontendDelegateDeclarative onMemoryLevel ArkUIMemoryLevel"
  - repo: "openharmony/ace_engine"
    query: "AceEngine TriggerGarbageCollection containerMap PurgeMallocCache ImageCache Purge BackgroundTaskExecutor"
  - repo: "openharmony/ace_engine"
    query: "BackgroundTaskExecutor TriggerGarbageCollection purgeFlags PURGE_FLAG_MASK ThreadLoop"
  - repo: "openharmony/ace_engine"
    query: "AceContainer TriggerGarbageCollection DumpHeapSnapshot frontend GPU IO UI JS thread"
  - repo: "openharmony/ace_engine"
    query: "WatchDog SIGNAL_FOR_GC TriggerGarbageCollection CheckGcSignal"
```

**关键文档：**
- `adapter/ohos/entrance/ui_content_impl.cpp:4847` — UIContentImpl::NotifyMemoryLevel 入口
- `frameworks/core/pipeline_ng/pipeline_context.cpp:6250-6275` — 节点注册/反注册/分发实现
- `frameworks/core/pipeline_ng/pipeline_context.h:1473` — nodesToNotifyMemoryLevel_ 列表声明
- `frameworks/core/pipeline/pipeline_base.h:1121` — PipelineBase::NotifyMemoryLevel 虚函数默认实现
- `frameworks/core/components_ng/syntax/lazy_for_each_node.cpp:860` — LazyForEachNode::OnNotifyMemoryLevel
- `frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_node.cpp:1053` — RepeatVirtualScroll2Node::OnNotifyMemoryLevel
- `frameworks/core/components_ng/syntax/arkoala_lazy_node.cpp:722` — ArkoalaLazyNode::OnNotifyMemoryLevel
- `frameworks/core/components_ng/pattern/image/image_pattern.cpp:1663` — ImagePattern::OnNotifyMemoryLevel（占位实现）
- `frameworks/core/components_ng/pattern/web/web_pattern.h:1219,1644` — WebPattern override + isMemoryLevelEnable_
- `frameworks/core/components_ng/pattern/swiper/swiper_pattern.h:1290` — SwiperPattern override
- `frameworks/core/components_ng/pattern/custom/custom_node.h:263,266-267` — CustomNode override + register/unregister
- `frameworks/core/common/frontend.h:297` — Frontend::OnMemoryLevel 纯虚函数
- `frameworks/bridge/declarative_frontend/declarative_frontend.cpp:1163` — DeclarativeFrontend::OnMemoryLevel
- `frameworks/bridge/declarative_frontend/frontend_delegate_declarative.cpp:662` — FrontendDelegateDeclarative::OnMemoryLevel
- `frameworks/core/common/ace_engine.cpp:213-242` — AceEngine::TriggerGarbageCollection 全局 GC
- `frameworks/base/thread/background_task_executor.cpp:28-29,196-209,228-233` — 后台线程位掩码 purge
- `adapter/ohos/entrance/ace_container.cpp:2602-2620` — AceContainer::TriggerGarbageCollection
- `adapter/ohos/entrance/ace_container.cpp:2622-2631` — AceContainer::DumpHeapSnapshot
- `frameworks/core/common/watch_dog.cpp:62-70` — WatchDog GC 信号处理
- `frameworks/core/image/image_cache.h:49,99,107,116,120` — ImageCache 类定义与缓存参数
- `frameworks/core/image/image_cache.cpp:226-253` — ImageCache::Clear
- `frameworks/core/components_ng/render/adapter/drawing_image.cpp:405` — ImageCache::Purge (SkGraphics::PurgeResourceCache)
- `frameworks/core/pipeline/pipeline_base.h:1731` — PipelineBase::imageCache_ 持有
- `frameworks/base/resource/shared_image_manager.h:43,49,68` — SharedImageManager 类定义与阈值
- `frameworks/core/components_ng/image_provider/image_decoder.h:69` — weakPixelMapCache_ 弱引用缓存
- 架构设计：`specs/03-engine-framework/08-dfx-foundation/02-memory-management/design.md`
