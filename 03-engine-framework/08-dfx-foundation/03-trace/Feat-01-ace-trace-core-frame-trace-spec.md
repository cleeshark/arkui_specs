# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ACE Trace核心框架与FrameTrace适配 |
| 特性编号 | Func-03-08-03-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 ArkUI ace_engine 性能 Trace 框架的核心基础设施：三层 Scoped Trace 宏（通用/Commercial/条件 Flag）、11 个域特定条件 Trace 宏、Begin/End 与函数级 Trace 宏、RAII 类族（AceScopedTrace / AceScopedTraceCommercial / AceScopedTraceFlag / AceAsyncScopedTrace / ResTracer / ContainerTracer / UINodeTracer）、OHOS HiTraceMeter 适配后端、FrameTraceAdapter 抽象与 FFRT Quick/Slow 任务路由、BackgroundTaskExecutor 集成、TraceId 跨线程传播。不涉及帧调度报告与 Jank 检测（Feat-02）、性能检查与阈值监控（Feat-03）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 三层 Scoped Trace 宏规格 | ace_trace.h:29-31 定义 ACE_SCOPED_TRACE / ACE_SCOPED_TRACE_COMMERCIAL / ACE_SCOPED_TRACE_FLAG 三个通用宏，展开为对应 RAII 临时对象 |
| ADDED | 11 个域特定条件 Trace 宏规格 | ace_trace.h:32-52 定义 ACE_SVG / ACE_TEXT / ACE_SYNTAX / ACE_ACCESS / ACE_LAYOUT / ACE_IMAGE / ACE_MEASURE / ACE_SAFE_AREA / ACE_VSYNC_MODE / ACE_EVENT / ACE_REUSE_DETECTION 共 11 个 SCOPED TRACE 宏，各自受 SystemProperties::Get*TraceEnabled() 运行时开关控制 |
| ADDED | Begin/End 与函数级 Trace 宏规格 | ace_trace.h:60-99 定义 ACE_LAYOUT_TRACE_BEGIN/END、ACE_BUILD_TRACE_BEGIN/END、ACE_BENCH_MARK_TRACE、CHECK_NULL_VOID_LAYOUT_TRACE_END、ACE_FUNCTION_TRACE / ACE_FUNCTION_TRACE_COMMERCIAL、ACE_COUNT_TRACE、ACE_UINODE_TRACE、ACE_CONTAINER_TRACE |
| ADDED | RAII Trace 类族规格 | ace_trace.h:121-216 定义 AceScopedTrace / AceScopedTraceCommercial / AceScopedTraceFlag / AceAsyncScopedTrace / ResTracer / ContainerTracer / UINodeTracer 共 7 个 RAII 类，构造调 Begin、析构调 End |
| ADDED | 通用 Trace 函数与格式化规格 | ace_trace.h:101-119 声明 AceTraceBegin / AceTraceEnd / AceAsyncTraceBegin / AceAsyncTraceEnd / AceCountTrace / AceSetResTraceId 等 13 个 ACE_EXPORT 自由函数；ace_trace.cpp:30-69 实现 vsnprintf_s 格式化包装（MAX_STRING_SIZE=512） |
| ADDED | OHOS HiTraceMeter 适配后端规格 | adapter/ohos/osal/ace_trace.cpp:23-106 将 ACE Trace 函数桥接到 HiTraceMeter（StartTrace/FinishTrace/StartAsyncTrace/CountTrace），Commercial 路径使用 HITRACE_LEVEL_COMMERCIAL + ACE_TRACE_COMMERCIAL 标签组合 |
| ADDED | FrameTraceAdapter 抽象与平台实现规格 | frame_trace_adapter.h:23-39 定义 QuickExecute / SlowExecute / EnableFrameTrace / IsEnabled / SetFrameTraceLimit 接口；OHOS 实现（frame_trace_adapter_impl.cpp）经 FRAME_TRACE_ENABLE 编译守卫路由到 FFRT；Fake 实现全 no-op；Preview 实现返回 null |
| ADDED | BackgroundTaskExecutor FrameTrace 集成规格 | background_task_executor.cpp:50-64 构造函数检查 FrameTrace 启用状态，启用时跳过线程池创建；PostTask:93-103 按优先级路由到 SlowExecute（LOW）/ QuickExecute（其他） |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/03-trace/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/base/log/ace_trace.h`（226 行）—— 中央头文件，宏定义/RAII 类/自由函数声明
  - `frameworks/base/log/ace_trace.cpp`（183 行）—— 跨平台 RAII 与格式化实现
  - `adapter/ohos/osal/ace_trace.cpp`（106 行）—— OHOS HiTraceMeter 后端适配
  - `frameworks/base/thread/frame_trace_adapter.h`（41 行）—— FrameTraceAdapter 抽象接口
  - `adapter/ohos/osal/frame_trace_adapter_impl.cpp`（79 行）—— OHOS FFRT 实现
  - `adapter/ohos/osal/frame_trace_adapter_fake_impl.cpp`（44 行）—— Fake 实现（no-op）
  - `adapter/preview/osal/frame_trace_adapter_impl.cpp`（23 行）—— Preview 实现（null）
  - `frameworks/base/thread/background_task_executor.cpp`（235 行）—— FrameTrace 集成点
  - `frameworks/base/log/trace_id.h`（34 行）—— TraceId 抽象
  - `adapter/ohos/osal/trace_id_impl.cpp`（49 行）—— HiTraceChain 适配

## 用户故事

### US-1: 通用 Scoped Trace 宏与 AceScopedTrace RAII

- As a 框架开发者
- I want ACE_SCOPED_TRACE(fmt,...) 在作用域入口自动开始 trace、出口自动结束
- So that 无需手动配对 Begin/End，编译器保证 trace 段始终闭合

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ACE_SCOPED_TRACE(fmt,...) 被使用 THEN 展开为 `AceScopedTrace aceScopedTrace(fmt, ##__VA_ARGS__)`，创建 RAII 临时对象。来源：`ace_trace.h:29` | 正常 |
| AC-1.2 | WHEN AceScopedTrace 构造函数执行 THEN 通过 va_list 调用 AceTraceBeginWithArgv(fmt, args)，返回值存入 strValid_；若格式化失败则 strValid_=false。来源：`ace_trace.cpp:71-77` | 正常 |
| AC-1.3 | WHEN AceScopedTrace 析构函数执行 THEN 仅当 strValid_==true 时调用 AceTraceEnd()，避免格式化失败时产生未配对的 End。来源：`ace_trace.cpp:79-84` | 正常 |
| AC-1.4 | WHEN AceTraceBeginWithArgv(format, args) 被调用 THEN 使用 vsnprintf_s 格式化为最大 512 字节字符串（MAX_STRING_SIZE），格式化失败返回 false，成功后调用 AceTraceBegin(name)。来源：`ace_trace.cpp:27,30-38` | 正常 |
| AC-1.5 | WHEN AceScopedTrace 被拷贝或移动 THEN 编译失败，因 ACE_DISALLOW_COPY_AND_MOVE 宏删除了拷贝构造/赋值和移动构造/赋值。来源：`ace_trace.h:126` | 边界 |

### US-2: 域特定条件 Trace 宏与 AceScopedTraceFlag

- As a 性能调优工程师
- I want 11 个域特定 trace 宏各自受独立运行时开关控制，关闭时零开销
- So that 可以按需只开启关注的子域 trace，不影响其他路径的性能

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN ACE_SVG_SCOPED_TRACE(fmt,...) 被使用 THEN 展开为 `AceScopedTraceFlag aceScopedTraceFlag(SystemProperties::GetSvgTraceEnabled(), fmt, ##__VA_ARGS__)`，flag 参数来自 GetSvgTraceEnabled()。来源：`ace_trace.h:32-33` | 正常 |
| AC-2.2 | WHEN 11 个域特定宏被使用 THEN 各自映射到 SystemProperties 开关函数：SVG→GetSvgTraceEnabled(:33)、TEXT→GetTextTraceEnabled(:35)、SYNTAX→GetSyntaxTraceEnabled(:37)、ACCESS→GetAccessTraceEnabled(:39)、LAYOUT→GetLayoutTraceEnabled(:41)、IMAGE→GetDebugEnabled(:43)、MEASURE→GetMeasureDebugTraceEnabled(:45)、SAFE_AREA→GetSafeAreaDebugTraceEnabled(:47)、VSYNC_MODE→GetVsyncModeTraceEnabled(:49)、EVENT→GetTraceInputEventEnabled(:51)、REUSE_DETECTION→GetDynamicDetectionTraceEnabled(:53)。来源：`ace_trace.h:32-53` | 正常 |
| AC-2.3 | WHEN AceScopedTraceFlag 构造时 flag==false THEN 不调用 AceTraceBeginWithArgv，flagTraceEnabled_ 保持初始值 false，构造函数直接返回。来源：`ace_trace.cpp:101-109` | 边界 |
| AC-2.4 | WHEN AceScopedTraceFlag 构造时 flag==true THEN 调用 AceTraceBeginWithArgv 并将返回值存入 flagTraceEnabled_；析构时仅当 flagTraceEnabled_==true 才调用 AceTraceEnd()。来源：`ace_trace.cpp:101-116` | 正常 |

### US-3: Commercial Trace 分级

- As a 商用版本 DFX 工程师
- I want Commercial 级别 trace 使用独立的 HITRACE_LEVEL_COMMERCIAL 标签输出
- So that 商用版本 trace 数据与开发版 trace 数据在 HiTraceMeter 中可分级过滤

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN ACE_SCOPED_TRACE_COMMERCIAL(fmt,...) 被使用 THEN 展开为 `AceScopedTraceCommercial aceScopedTrace(fmt, ##__VA_ARGS__)`。来源：`ace_trace.h:30` | 正常 |
| AC-3.2 | WHEN AceScopedTraceCommercial 构造 THEN 调用 AceTraceBeginWithArgvCommercial，该函数使用 vsnprintf_s 格式化后调用 AceTraceBeginCommercial(name)。来源：`ace_trace.cpp:40-48,86-92` | 正常 |
| AC-3.3 | WHEN AceTraceBeginCommercial(name) 在 OHOS 平台执行 THEN 调用 StartTraceEx(HITRACE_LEVEL_COMMERCIAL, ACE_TRACE_COMMERCIAL, name)，其中 ACE_TRACE_COMMERCIAL = HITRACE_TAG_ACE | HITRACE_TAG_COMMERCIAL。来源：`adapter/ohos/osal/ace_trace.cpp:25,41-44` | 正常 |
| AC-3.4 | WHEN AceTraceEndCommercial() 在 OHOS 平台执行 THEN 调用 FinishTraceEx(HITRACE_LEVEL_COMMERCIAL, ACE_TRACE_COMMERCIAL)，标签与 Begin 一致。来源：`adapter/ohos/osal/ace_trace.cpp:46-49` | 正常 |
| AC-3.5 | WHEN AceAsyncTraceBeginCommercial 被调用且 isAnimationTrace==true THEN 使用 ANIMATION_TRACE_COMMERCIAL（HITRACE_TAG_ANIMATION | HITRACE_TAG_COMMERCIAL）标签；isAnimationTrace==false 时使用 ACE_TRACE_COMMERCIAL 标签。来源：`adapter/ohos/osal/ace_trace.cpp:26,73-82` | 正常 |

### US-4: Begin/End 宏与函数级 Trace

- As a 框架开发者
- I want 使用 ACE_FUNCTION_TRACE() 自动以当前函数名为 trace 标签，以及 ACE_LAYOUT_TRACE_BEGIN/END 手动配对控制 layout 域 trace
- So that 函数级耗时和特定阶段的 layout trace 可被灵活标记

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN ACE_FUNCTION_TRACE() 被使用 THEN 展开为 ACE_SCOPED_TRACE(__func__)，即以当前函数名为标签创建 AceScopedTrace。来源：`ace_trace.h:93` | 正常 |
| AC-4.2 | WHEN ACE_FUNCTION_TRACE_COMMERCIAL() 被使用 THEN 展开为 ACE_SCOPED_TRACE_COMMERCIAL(__func__)，以函数名为标签创建 Commercial 级别 trace。来源：`ace_trace.h:94` | 正常 |
| AC-4.3 | WHEN ACE_LAYOUT_TRACE_BEGIN(fmt,...) 被使用 THEN 仅当 SystemProperties::GetLayoutTraceEnabled() 返回 true 时调用 AceTraceBeginWithArgs(fmt,...)；ACE_LAYOUT_TRACE_END() 同理仅当开关开启时调用 AceTraceEnd()。来源：`ace_trace.h:60-67` | 正常 |
| AC-4.4 | WHEN ACE_BUILD_TRACE_BEGIN/END 被使用 THEN 仅当 SystemProperties::GetBuildTraceEnabled() 返回 true 时调用 AceTraceBeginWithArgs / AceTraceEnd。来源：`ace_trace.h:74-81` | 正常 |
| AC-4.5 | WHEN CHECK_NULL_VOID_LAYOUT_TRACE_END(ptr) 被使用且 ptr 为空 THEN 若 GetLayoutTraceEnabled() 为 true 则先调用 AceTraceEnd() 再 return；ptr 非空时继续执行。来源：`ace_trace.h:83-91` | 边界 |
| AC-4.6 | WHEN ACE_BENCH_MARK_TRACE(fmt,...) 被使用 THEN 仅当 SystemProperties::GetEventBenchMarkEnabled() 返回 true 时展开为 ACE_SCOPED_TRACE(fmt,...)。来源：`ace_trace.h:68-71` | 正常 |

### US-5: OHOS HiTraceMeter 适配后端

- As a 系统集成工程师
- I want ACE Trace 的所有同步/异步/计数 trace 调用统一桥接到 HiTraceMeter，使用 HITRACE_TAG_ACE 标签
- So that 所有 ArkUI trace 可通过系统级 trace 抓取工具统一采集

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN AceTraceBegin(name) 在 OHOS 平台执行 THEN 对 name 做 CHECK_NULL_VOID 空指针检查，通过后调用 StartTrace(HITRACE_TAG_ACE, nameStr)。来源：`adapter/ohos/osal/ace_trace.cpp:29-34` | 正常 |
| AC-5.2 | WHEN AceTraceEnd() 在 OHOS 平台执行 THEN 调用 FinishTrace(HITRACE_TAG_ACE)，无参数。来源：`adapter/ohos/osal/ace_trace.cpp:36-39` | 正常 |
| AC-5.3 | WHEN AceAsyncTraceBegin(taskId, name, isAnimationTrace) 被调用 THEN isAnimationTrace==true 时使用 StartAsyncTrace(HITRACE_TAG_ANIMATION,...)，否则使用 StartAsyncTrace(HITRACE_TAG_ACE,...)；AceAsyncTraceEnd 对应使用 FinishAsyncTrace。来源：`adapter/ohos/osal/ace_trace.cpp:51-71` | 正常 |
| AC-5.4 | WHEN AceCountTrace(key, count) 被调用 THEN 对 key 做 CHECK_NULL_VOID，通过后调用 CountTrace(HITRACE_TAG_ACE, keyStr, count)。来源：`adapter/ohos/osal/ace_trace.cpp:95-100` | 正常 |
| AC-5.5 | WHEN AceSetResTraceId(traceType, traceId, pOldTraceType, pOldTraceId) 在 OHOS 平台执行 THEN 委托给外部 C 函数 setResTraceId(traceType, traceId, pOldTraceType, pOldTraceId)。来源：`adapter/ohos/osal/ace_trace.cpp:22,102-105` | 正常 |
| AC-5.6 | WHEN AceTraceBegin/AceAsyncTraceBegin/AceCountTrace 接收到 nullptr 参数 THEN CHECK_NULL_VOID 宏直接 return，不调用 HiTraceMeter API，不产生崩溃。来源：`adapter/ohos/osal/ace_trace.cpp:31,53,64,75,87,97` | 异常 |

### US-6: FrameTraceAdapter 抽象与 Quick/Slow 任务路由

- As a 帧调度优化工程师
- I want FrameTraceAdapter 提供 Quick/Slow 两级任务执行路由，将高优先级任务标记为 QUICK_TRACE、低优先级标记为 SLOW_TRACE
- So that FFRT 帧感知调度器能区分关键路径与非关键路径进行调度优化

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN FrameTraceAdapter::QuickExecute(func) 在 OHOS 平台被调用 THEN 若 AccessFrameTrace() 返回 true（FRAME_TRACE_ENABLE 已定义），调用 FRAME_TRACE::TraceAndExecute(std::move(func), FRAME_TRACE::TraceType::QUICK_TRACE)。来源：`frame_trace_adapter_impl.cpp:26-40` | 正常 |
| AC-6.2 | WHEN FrameTraceAdapter::SlowExecute(func) 在 OHOS 平台被调用 THEN 若 AccessFrameTrace() 返回 true，调用 FRAME_TRACE::TraceAndExecute(std::move(func), FRAME_TRACE::TraceType::SLOW_TRACE)。来源：`frame_trace_adapter_impl.cpp:42-47` | 正常 |
| AC-6.3 | WHEN FRAME_TRACE_ENABLE 未定义 THEN AccessFrameTrace() 返回 false，QuickExecute 和 SlowExecute 均为空操作不执行 func。来源：`frame_trace_adapter_impl.cpp:26-33,35-47` | 边界 |
| AC-6.4 | WHEN FrameTraceAdapter::SetFrameTraceLimit() 被调用 THEN 读取系统参数 "ffrt.interval.limit"，若为 false 则调用 OHOS::system::SetParameter("ffrt.interval.limit", "true")。来源：`frame_trace_adapter_impl.cpp:24,71-78` | 正常 |
| AC-6.5 | WHEN FrameTraceAdapter::GetInstance() 在 Preview 平台被调用 THEN 返回 nullptr，Preview 不支持 FrameTrace。来源：`adapter/preview/osal/frame_trace_adapter_impl.cpp:19-22` | 边界 |
| AC-6.6 | WHEN FrameTraceAdapter::GetInstance() 在 OHOS 但 FRAME_TRACE_ENABLE 未定义时被调用 THEN 返回 FrameTraceAdapterFakeImpl 静态实例，其 QuickExecute/SlowExecute 为 no-op、IsEnabled 返回 false。来源：`frame_trace_adapter_fake_impl.cpp:19-43` | 边界 |

### US-7: BackgroundTaskExecutor FrameTrace 集成

- As a 后台任务调度开发者
- I want BackgroundTaskExecutor 在 FrameTrace 启用时跳过自有线程池创建，改为通过 Quick/Slow 路由任务
- So that 后台任务纳入帧感知调度体系，避免与 UI 线程竞争

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN BackgroundTaskExecutor 构造函数执行 THEN 获取 FrameTraceAdapter::GetInstance()，若非 null 且 IsEnabled()==true 则直接 return 不创建线程池；否则创建最多 MAX_BACKGROUND_THREADS(8) 个后台线程。来源：`background_task_executor.cpp:28,50-65` | 正常 |
| AC-7.2 | WHEN PostTask(task, priority) 被调用且 FrameTrace 已启用 THEN BgTaskPriority::LOW 路由到 ft->SlowExecute(std::move(task))，其他优先级路由到 ft->QuickExecute(std::move(task))，返回 true 不进入本地任务队列。来源：`background_task_executor.cpp:93-104` | 正常 |
| AC-7.3 | WHEN PostTask(task, priority) 被调用且 FrameTrace 未启用 THEN LOW 优先级进入 lowPriorityTasks_ 队列，其他进入 tasks_ 队列，通过 condition_.notify_one() 唤醒后台线程。来源：`background_task_executor.cpp:105-114` | 正常 |
| AC-7.4 | WHEN PostTask 接收到空 task THEN 直接返回 false，不进入任何执行路径。来源：`background_task_executor.cpp:85-87` | 异常 |

### US-8: 资源追踪 ResTracer / ContainerTracer / UINodeTracer

- As a DFX 可观测性工程师
- I want ResTracer 在 RAII 作用域内设置资源 trace ID（UINode 或 Container 类型），析构时恢复原值
- So that trace 工具能关联 trace 段所属的 UI 节点或容器上下文

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN ResTracer 构造函数 ResTracer(caller, traceType, traceId) 执行 THEN 调用 AceSetResTraceId(traceType, traceId, &traceType_, &traceId_)，将当前 traceType 和 traceId 设置为新值，原值保存到成员变量。来源：`ace_trace.cpp:155-158` | 正常 |
| AC-8.2 | WHEN ResTracer 析构函数执行 THEN 调用 AceSetResTraceId(traceType_, traceId_, &traceType, &traceId)，将保存的原值恢复回去。来源：`ace_trace.cpp:160-165` | 正常 |
| AC-8.3 | WHEN ResTraceType 枚举被使用 THEN 包含两个值：UINode 和 Container。来源：`ace_trace.h:165-168` | 正常 |
| AC-8.4 | WHEN ACE_CONTAINER_TRACE(container...) 被使用 THEN 展开为 `ContainerTracer ACE_UNIQUE_VAR { __PRETTY_FUNCTION__, container }`，创建 ContainerTracer RAII 对象。来源：`ace_trace.h:99` | 正常 |
| AC-8.5 | WHEN ContainerTracer(caller) 无参容器构造 THEN 委托给 ContainerTracer(caller, Container::CurrentId()) 获取当前容器 ID。来源：`ace_trace.cpp:171-173` | 正常 |
| AC-8.6 | WHEN ContainerTracer(caller, const Container* container) 构造且 container 为 null THEN 使用 INSTANCE_ID_UNDEFINED 作为容器 ID。来源：`ace_trace.cpp:167-169` | 异常 |

### US-9: AceAsyncScopedTrace 与 TraceId 跨线程传播

- As a 异步任务开发者
- I want AceAsyncScopedTrace 自动管理异步 trace taskId，TraceId 能在跨线程场景传播 HiTraceChain ID
- So that 跨线程的异步操作能被正确关联到同一 trace 链

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN AceAsyncScopedTrace 构造函数执行 THEN taskId_ = id_++（std::atomic 自增），随后调用 AceAsyncTraceBeginWithArgv(taskId_, fmt, args) 开始异步 trace。来源：`ace_trace.cpp:137-146` | 正常 |
| AC-9.2 | WHEN AceAsyncScopedTrace 析构函数执行 THEN 仅当 name_ 非空时调用 AceAsyncTraceEnd(taskId_, name_.c_str())，确保 Begin/End 配对。来源：`ace_trace.cpp:148-153` | 正常 |
| AC-9.3 | WHEN AceAsyncScopedTrace::id_ 静态成员初始化 THEN 初始值为 0（std::atomic<int32_t>），在 ace_trace.cpp:137 处定义。来源：`ace_trace.cpp:137` | 边界 |
| AC-9.4 | WHEN TraceId::CreateTraceId() 被调用 THEN 返回 std::make_shared<TraceIdImpl>()，OHOS 平台 TraceIdImpl 构造时通过 HiTraceChain::GetId() 获取当前链路 ID。来源：`trace_id.h:27`, `trace_id_impl.cpp:22-24,44-47` | 正常 |
| AC-9.5 | WHEN TraceIdImpl::SetTraceId() 被调用且 traceId_ 有效 THEN 调用 HiTraceChain::SetId(*(traceId_.get())) 恢复保存的链路 ID。来源：`trace_id_impl.cpp:28-33` | 正常 |
| AC-9.6 | WHEN TraceIdImpl::ClearTraceId() 被调用 THEN 调用 HiTraceChain::ClearId() 清除当前线程链路 ID。来源：`trace_id_impl.cpp:35-38` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-1.2 | R-2 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.3 | R-3 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.4 | R-4 | TASK-01 | 单元测试 | 代码审查 |
| AC-1.5 | R-5 | TASK-01 | 编译验证 | 代码审查 |
| AC-2.1 | R-6 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-2.2 | R-6 / R-7 | TASK-01 | 代码评审 | 代码审查 |
| AC-2.3 | R-8 | TASK-01 | 单元测试 | 代码审查 |
| AC-2.4 | R-8 | TASK-01 | 单元测试 | 代码审查 |
| AC-3.1 | R-9 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-3.2 | R-9 | TASK-01 | 代码评审 | 代码审查 |
| AC-3.3 | R-10 | TASK-01 | 代码评审 + HiTraceMeter 输出验证 | 代码审查 |
| AC-3.4 | R-10 | TASK-01 | 代码评审 | 代码审查 |
| AC-3.5 | R-10 / R-11 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.1 | R-12 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-4.2 | R-12 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-4.3 | R-13 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.4 | R-13 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.5 | R-14 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.6 | R-15 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.1 | R-16 | TASK-01 | 代码评审 + trace 抓取验证 | 代码审查 |
| AC-5.2 | R-16 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.3 | R-16 / R-17 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.4 | R-16 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.5 | R-18 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.6 | R-19 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.1 | R-20 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.2 | R-20 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.3 | R-21 | TASK-01 | 编译变体验证 | 代码审查 |
| AC-6.4 | R-22 | TASK-01 | 代码评审 + 系统参数验证 | 代码审查 |
| AC-6.5 | R-23 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.6 | R-24 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.1 | R-25 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.2 | R-26 | TASK-01 | 单元测试 | 代码审查 |
| AC-7.3 | R-27 | TASK-01 | 单元测试 | 代码审查 |
| AC-7.4 | R-19 | TASK-01 | 单元测试 | 代码审查 |
| AC-8.1 | R-28 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.2 | R-28 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.3 | R-29 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.4 | R-30 | TASK-01 | 宏展开验证 | 代码审查 |
| AC-8.5 | R-31 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.6 | R-19 | TASK-01 | 代码评审 | 代码审查 |
| AC-9.1 | R-32 | TASK-01 | 单元测试 | 代码审查 |
| AC-9.2 | R-32 | TASK-01 | 单元测试 | 代码审查 |
| AC-9.3 | R-33 | TASK-01 | 代码评审 | 代码审查 |
| AC-9.4 | R-34 | TASK-01 | 代码评审 | 代码审查 |
| AC-9.5 | R-34 | TASK-01 | 代码评审 | 代码审查 |
| AC-9.6 | R-34 | TASK-01 | 代码评审 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ACE_SCOPED_TRACE 宏使用 | 展开为 AceScopedTrace 局部变量，变量名固定为 aceScopedTrace。 | 同一作用域内不可重复使用同名宏。 | AC-1.1 |
| R-2 | 行为 | AceScopedTrace 构造 | 通过 va_list 调用 AceTraceBeginWithArgv 格式化 trace 名称，结果存入 strValid_。 | 格式化缓冲区上限 MAX_STRING_SIZE=512 字节。 | AC-1.2 |
| R-3 | 行为 | AceScopedTrace 析构 | 仅当 strValid_==true 时调用 AceTraceEnd()。 | RAII 保证作用域结束时必定执行。 | AC-1.3 |
| R-4 | 行为 | AceTraceBeginWithArgv 调用 | 使用 vsnprintf_s 格式化，成功后调用 AceTraceBegin；失败返回 false。 | vsnprintf_s 失败时 name 缓冲区为零初始化。 | AC-1.4 |
| R-5 | 边界 | AceScopedTrace 拷贝/移动 | ACE_DISALLOW_COPY_AND_MOVE 禁止拷贝构造、拷贝赋值、移动构造、移动赋值。 | 编译期检查，违反则编译失败。 | AC-1.5 |
| R-6 | 行为 | 11 个域特定条件 trace 宏使用 | 每个宏展开为 AceScopedTraceFlag，第一参数为对应的 SystemProperties::Get*TraceEnabled() 返回值。 | 域特定宏共 11 个：SVG/TEXT/SYNTAX/ACCESS/LAYOUT/IMAGE/MEASURE/SAFE_AREA/VSYNC_MODE/EVENT/REUSE_DETECTION。 | AC-2.1 / AC-2.2 |
| R-7 | 行为 | 域特定 trace 开关读取 | 12 个系统属性参数控制开关，读取自 persist.ace.trace.* 系统属性。 | 大部分开关需要 developerModeOn_ 为 true。 | AC-2.2 |
| R-8 | 行为 | AceScopedTraceFlag 构造 | flag==true 时调用 AceTraceBeginWithArgv 并保存结果到 flagTraceEnabled_；flag==false 时跳过。 | flagTraceEnabled_ 初始值为 false。 | AC-2.3 / AC-2.4 |
| R-9 | 行为 | ACE_SCOPED_TRACE_COMMERCIAL 宏使用 | 展开为 AceScopedTraceCommercial，经 AceTraceBeginWithArgvCommercial 走 Commercial 路径。 | 变量名固定为 aceScopedTrace。 | AC-3.1 / AC-3.2 |
| R-10 | 行为 | Commercial trace OHOS 适配 | AceTraceBeginCommercial 调用 StartTraceEx(HITRACE_LEVEL_COMMERCIAL, ACE_TRACE_COMMERCIAL, name)；End 调用 FinishTraceEx 对应参数。 | ACE_TRACE_COMMERCIAL = HITRACE_TAG_ACE | HITRACE_TAG_COMMERCIAL（:25）。 | AC-3.3 / AC-3.4 / AC-3.5 |
| R-11 | 行为 | Commercial 异步 trace 动画标签 | AceAsyncTraceBeginCommercial isAnimationTrace==true 时使用 ANIMATION_TRACE_COMMERCIAL（HITRACE_TAG_ANIMATION | HITRACE_TAG_COMMERCIAL）。 | 非 animation 时使用 ACE_TRACE_COMMERCIAL。 | AC-3.5 |
| R-12 | 行为 | ACE_FUNCTION_TRACE / ACE_FUNCTION_TRACE_COMMERCIAL 使用 | 分别展开为 ACE_SCOPED_TRACE(__func__) / ACE_SCOPED_TRACE_COMMERCIAL(__func__)，以当前函数名为标签。 | __func__ 为 C99 预定义标识符。 | AC-4.1 / AC-4.2 |
| R-13 | 行为 | ACE_LAYOUT_TRACE_BEGIN/END / ACE_BUILD_TRACE_BEGIN/END 使用 | 分别受 GetLayoutTraceEnabled() / GetBuildTraceEnabled() 控制，开关关闭时为空操作。 | Begin 和 End 各自独立检查开关。 | AC-4.3 / AC-4.4 |
| R-14 | 边界 | CHECK_NULL_VOID_LAYOUT_TRACE_END(ptr) 使用 | ptr 为空时若 layout trace 开启则先 End 再 return；ptr 非空时正常继续。 | 使用 do-while(0) 包装确保宏安全。 | AC-4.5 |
| R-15 | 行为 | ACE_BENCH_MARK_TRACE 使用 | 受 SystemProperties::GetEventBenchMarkEnabled() 控制，开启时展开为 ACE_SCOPED_TRACE。 | 用于基准测试场景。 | AC-4.6 |
| R-16 | 行为 | ACE Trace 函数 OHOS HiTraceMeter 桥接 | AceTraceBegin→StartTrace(HITRACE_TAG_ACE)、AceTraceEnd→FinishTrace(HITRACE_TAG_ACE)、AceCountTrace→CountTrace(HITRACE_TAG_ACE)。 | 所有同步 trace 统一使用 HITRACE_TAG_ACE。 | AC-5.1 / AC-5.2 / AC-5.4 |
| R-17 | 行为 | 异步 trace OHOS 适配 | AceAsyncTraceBegin/End 根据 isAnimationTrace 选择 HITRACE_TAG_ANIMATION 或 HITRACE_TAG_ACE。 | 默认 isAnimationTrace=false。 | AC-5.3 |
| R-18 | 行为 | AceSetResTraceId OHOS 适配 | 委托给 extern "C" void setResTraceId() 外部 C 函数实现。 | 函数声明在 ace_trace.cpp:22。 | AC-5.5 |
| R-19 | 异常 | ACE Trace 函数空指针参数 | AceTraceBegin/AceAsyncTraceBegin/AceCountTrace 等对 name/key 参数执行 CHECK_NULL_VOID，空指针时直接返回不调用 HiTraceMeter。 | 不产生崩溃，静默忽略。 | AC-5.6 / AC-7.4 / AC-8.6 |
| R-20 | 行为 | FrameTraceAdapter Quick/Slow 路由 | QuickExecute→TraceAndExecute(func, QUICK_TRACE)，SlowExecute→TraceAndExecute(func, SLOW_TRACE)，均受 AccessFrameTrace() 守卫。 | AccessFrameTrace() 检查 FRAME_TRACE_ENABLE 编译宏。 | AC-6.1 / AC-6.2 |
| R-21 | 边界 | FRAME_TRACE_ENABLE 未定义 | AccessFrameTrace() 返回 false，QuickExecute/SlowExecute 为空操作不执行 func。 | func 不会被调用。 | AC-6.3 |
| R-22 | 行为 | SetFrameTraceLimit 系统参数设置 | 读取 "ffrt.interval.limit" 参数，为 false 时设置为 "true"。 | INTERVAL_LIMIT 常量为 "ffrt.interval.limit"。 | AC-6.4 |
| R-23 | 边界 | Preview 平台 FrameTrace | FrameTraceAdapter::GetInstance() 返回 nullptr，所有 FrameTrace 功能禁用。 | Preview 无 FFRT 支持。 | AC-6.5 |
| R-24 | 边界 | OHOS Fake 实现 FrameTrace | GetInstance() 返回 FrameTraceAdapterFakeImpl，QuickExecute/SlowExecute 为 no-op，IsEnabled 返回 false。 | FRAME_TRACE_ENABLE 未定义时使用 Fake 实现。 | AC-6.6 |
| R-25 | 行为 | BackgroundTaskExecutor 构造 FrameTrace 检查 | FrameTrace 启用时跳过线程池创建直接 return；否则创建最多 8 个后台线程。 | MAX_BACKGROUND_THREADS=8。 | AC-7.1 |
| R-26 | 行为 | PostTask FrameTrace 启用时路由 | LOW 优先级→SlowExecute，其他→QuickExecute，不进入本地队列。 | 两个 PostTask 重载（&&和const&）行为一致。 | AC-7.2 |
| R-27 | 行为 | PostTask FrameTrace 未启用时路由 | LOW→lowPriorityTasks_ 队列，其他→tasks_ 队列，notify_one 唤醒。 | 本地线程池模式。 | AC-7.3 |
| R-28 | 行为 | ResTracer 构造/析构资源 ID 管理 | 构造时设置新 traceType/traceId 并保存旧值；析构时恢复旧值。 | AceSetResTraceId 的 4 参数语义：newType, newId, *oldType, *oldId。 | AC-8.1 / AC-8.2 |
| R-29 | 行为 | ResTraceType 枚举 | 定义两个值 UINode 和 Container，用于区分资源追踪类型。 | uint32_t 底层类型。 | AC-8.3 |
| R-30 | 行为 | ACE_UINODE_TRACE / ACE_CONTAINER_TRACE 宏使用 | 分别展开为 UINodeTracer / ContainerTracer RAII 对象，使用 __PRETTY_FUNCTION__ 作为 caller 参数。 | 使用 ACE_UNIQUE_VAR 避免变量名冲突。 | AC-8.4 |
| R-31 | 行为 | ContainerTracer 无参构造 | 委托给 ContainerTracer(caller, Container::CurrentId()) 获取当前容器 ID。 | INSTANCE_ID_UNDEFINED 为无效容器 ID。 | AC-8.5 |
| R-32 | 行为 | AceAsyncScopedTrace 生命周期 | 构造时 taskId_=id_++（atomic 自增）并开始异步 trace；析构时 name_ 非空则结束异步 trace。 | id_ 为 static std::atomic<int32_t>。 | AC-9.1 / AC-9.2 |
| R-33 | 边界 | AceAsyncScopedTrace::id_ 初始化 | 静态成员 id_ 初始值为 0。 | 在 ace_trace.cpp:137 处定义。 | AC-9.3 |
| R-34 | 行为 | TraceId / TraceIdImpl 跨线程传播 | CreateTraceId 返回 TraceIdImpl（HiTraceChain::GetId）；SetTraceId 恢复链路 ID；ClearTraceId 清除链路 ID。 | SetTraceId 检查 traceId_ 有效性和 IsValid()。 | AC-9.4 / AC-9.5 / AC-9.6 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.5 / R-1..R-5 | 宏展开验证 + 代码评审 + 编译验证 | ace_trace.h:29, ace_trace.cpp:27-84 |
| VM-2 | AC-2.1..2.4 / R-6..R-8 | 宏展开验证 + 单元测试 | ace_trace.h:32-53, ace_trace.cpp:101-116 |
| VM-3 | AC-3.1..3.5 / R-9..R-11 | 宏展开验证 + 代码评审 + HiTraceMeter 输出验证 | ace_trace.h:30, ace_trace.cpp:40-48,86-92, adapter/ohos/osal/ace_trace.cpp:25-26,41-93 |
| VM-4 | AC-4.1..4.6 / R-12..R-15 | 宏展开验证 + 代码评审 | ace_trace.h:60-99 |
| VM-5 | AC-5.1..5.6 / R-16..R-19 | 代码评审 + trace 抓取验证 | adapter/ohos/osal/ace_trace.cpp:23-106 |
| VM-6 | AC-6.1..6.6 / R-20..R-24 | 代码评审 + 编译变体验证 + 系统参数验证 | frame_trace_adapter.h:23-39, frame_trace_adapter_impl.cpp:24-78, frame_trace_adapter_fake_impl.cpp:19-43, adapter/preview/osal/frame_trace_adapter_impl.cpp:19-22 |
| VM-7 | AC-7.1..7.4 / R-25..R-27 / R-19 | 代码评审 + 单元测试 | background_task_executor.cpp:28,50-65,83-115 |
| VM-8 | AC-8.1..8.6 / R-28..R-31 / R-19 | 代码评审 + 宏展开验证 | ace_trace.h:99,165-216, ace_trace.cpp:155-183 |
| VM-9 | AC-9.1..9.6 / R-32..R-34 | 单元测试 + 代码评审 | ace_trace.h:152-163, ace_trace.cpp:118-153,137, trace_id.h:23-30, trace_id_impl.cpp:22-47 |
| VM-10 | AC-2.2 / R-7 | 系统属性验证 + 代码评审 | adapter/ohos/osal/system_properties.cpp:142-215 |

## API 变更分析

### 新增 API

N/A，无新增 Public/System/InnerApi。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

无新增接口规格。

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 无 @since 标注（框架内部能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 四层调用链单向依赖 | 宏 → RAII → 适配函数 → HiTraceMeter 四层调用链严格自上而下，不允许反向依赖 | AC-1.1 |
| 框架必须使用 RAII trace 宏 | 框架内所有同步 trace 输出必须使用 ACE_SCOPED_TRACE / ACE_FUNCTION_TRACE / ACE_SCOPED_TRACE_FLAG 等宏，禁止直接手动配对 | AC-2.1 |
| Commercial trace 级别分离 | 必须使用 ACE_SCOPED_TRACE_COMMERCIAL / ACE_FUNCTION_TRACE_COMMERCIAL 宏，HITRACE_LEVEL_COMMERCIAL + ACE_TRACE_COMMERCIAL 标签 | AC-3.1 |
| FrameTraceAdapter 抽象基类 | 平台通过继承实现 QuickExecute/SlowExecute；GetInstance() 各平台独立实现，Preview 返回 null | AC-5.1 |
| BackgroundTaskExecutor 单向依赖 | BackgroundTaskExecutor 依赖 FrameTraceAdapter，FrameTraceAdapter 不反向依赖 | AC-5.2 |
| MAX_STRING_SIZE=512 缓冲区上限 | trace 名称格式化缓冲区上限，超出截断，所有 vsnprintf_s 共享此限制 | AC-6.1 |
| AceAsyncScopedTrace::id_ 全局原子计数器 | 从 0 开始递增，不回收，用于异步 trace 唯一标识 | AC-7.1 |

## 非功能性需求

- 性能：ACE_SCOPED_TRACE 宏在作用域入口/出口各产生一次 HiTraceMeter API 调用，RAII 对象构造/析构开销为 va_list 格式化 + 一次函数调用；域特定 trace 宏（AceScopedTraceFlag）在开关关闭时仅构造一个 bool 成员的 RAII 对象，开销接近零。
- 性能：FrameTrace 启用时 BackgroundTaskExecutor 不创建线程池（省去最多 8 个线程的资源开销），改为通过 FFRT 调度；PostTask 路由判断为一次 IsEnabled() 调用 + switch 分支。
- 可观测：所有同步 trace 使用 HITRACE_TAG_ACE 标签，异步 trace 可选 HITRACE_TAG_ANIMATION，Commercial trace 使用 HITRACE_TAG_ACE | HITRACE_TAG_COMMERCIAL 组合标签，支持 HiTraceMeter 分级过滤。
- 可观测：12 个域特定 trace 开关可通过 persist.ace.trace.* 系统属性运行时动态控制，无需重新编译。
- 鲁棒性：所有接受 const char* 参数的 ACE Trace 函数对空指针执行 CHECK_NULL_VOID 静默忽略，不产生崩溃。
- 鲁棒性：FrameTrace 在 Preview 平台返回 null adapter，在 OHOS 无 FRAME_TRACE_ENABLE 时使用 Fake 实现，保证跨平台不崩溃。
- 线程安全：AceAsyncScopedTrace::id_ 为 std::atomic<int32_t>，保证多线程异步 trace taskId 唯一性；其他 RAII trace 对象为栈局部对象，天然线程安全。

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 其他 Public/System API | 否 | 不改变任何 Public/System API 契约 | 无 |
| 框架管线 Trace 打点 | 是 | 所有使用 ACE_SCOPED_TRACE 等宏的模块隐式依赖本 Feat | pipeline_context.cpp:892 FlushBuild、pipeline_context.cpp:1170 FlushVsync、ui_task_scheduler.cpp:134/241、frame_node.cpp:3024/3059 |
| BackgroundTaskExecutor | 是 | FrameTrace 启用时后台任务经 FFRT 调度，未启用时经自有线程池调度 | background_task_executor.cpp:50-64, 93-104 |
| 增域 trace 开关扩展 | 是 | 新增域需在 SystemProperties 添加开关和 persist.ace.trace.* 属性 | ace_trace.h:32-53, adapter/ohos/osal/system_properties.cpp:142-215 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
- path: frameworks/base/log/ace_trace.h
  lines: 29-31
  description: ACE_SCOPED_TRACE / ACE_SCOPED_TRACE_COMMERCIAL / ACE_SCOPED_TRACE_FLAG 三个通用 Scoped 宏
- path: frameworks/base/log/ace_trace.h
  lines: 32-53
  description: 11 个域特定条件 trace 宏（SVG/TEXT/SYNTAX/ACCESS/LAYOUT/IMAGE/MEASURE/SAFE_AREA/VSYNC_MODE/EVENT/REUSE_DETECTION）
- path: frameworks/base/log/ace_trace.h
  lines: 54-58
  description: ACE_DEBUG_SCOPED_TRACE 条件编译宏
- path: frameworks/base/log/ace_trace.h
  lines: 60-67
  description: ACE_LAYOUT_TRACE_BEGIN / ACE_LAYOUT_TRACE_END 宏
- path: frameworks/base/log/ace_trace.h
  lines: 68-71
  description: ACE_BENCH_MARK_TRACE 宏
- path: frameworks/base/log/ace_trace.h
  lines: 74-81
  description: ACE_BUILD_TRACE_BEGIN / ACE_BUILD_TRACE_END 宏
- path: frameworks/base/log/ace_trace.h
  lines: 83-91
  description: CHECK_NULL_VOID_LAYOUT_TRACE_END 宏
- path: frameworks/base/log/ace_trace.h
  lines: 93-99
  description: ACE_FUNCTION_TRACE / ACE_FUNCTION_TRACE_COMMERCIAL / ACE_COUNT_TRACE / ACE_UINODE_TRACE / ACE_CONTAINER_TRACE 宏
- path: frameworks/base/log/ace_trace.h
  lines: 101-119
  description: 13 个 ACE_EXPORT / ACE_FORCE_EXPORT 自由函数声明
- path: frameworks/base/log/ace_trace.h
  lines: 121-129
  description: AceScopedTrace 类声明
- path: frameworks/base/log/ace_trace.h
  lines: 131-139
  description: AceScopedTraceCommercial 类声明
- path: frameworks/base/log/ace_trace.h
  lines: 141-150
  description: AceScopedTraceFlag 类声明
- path: frameworks/base/log/ace_trace.h
  lines: 152-163
  description: AceAsyncScopedTrace 类声明，含 static std::atomic id_
- path: frameworks/base/log/ace_trace.h
  lines: 165-168
  description: ResTraceType 枚举（UINode, Container）
- path: frameworks/base/log/ace_trace.h
  lines: 170-180
  description: ResTracer 类声明
- path: frameworks/base/log/ace_trace.h
  lines: 182-197
  description: ContainerTracer 类声明，多构造函数重载
- path: frameworks/base/log/ace_trace.h
  lines: 199-216
  description: UINodeTracer 类声明，多构造函数重载
- path: frameworks/base/log/ace_trace.h
  lines: 218-222
  description: ACE_UNITTEST 条件下的 mock 函数声明
- path: frameworks/base/log/ace_trace.cpp
  lines: 27
  description: MAX_STRING_SIZE=512 常量
- path: frameworks/base/log/ace_trace.cpp
  lines: 30-38
  description: AceTraceBeginWithArgv 实现（vsnprintf_s + AceTraceBegin）
- path: frameworks/base/log/ace_trace.cpp
  lines: 40-48
  description: AceTraceBeginWithArgvCommercial 实现
- path: frameworks/base/log/ace_trace.cpp
  lines: 50-57
  description: AceTraceBeginWithArgs 可变参数包装
- path: frameworks/base/log/ace_trace.cpp
  lines: 59-69
  description: AceCountTraceWidthArgs 实现
- path: frameworks/base/log/ace_trace.cpp
  lines: 71-84
  description: AceScopedTrace 构造/析构实现
- path: frameworks/base/log/ace_trace.cpp
  lines: 86-99
  description: AceScopedTraceCommercial 构造/析构实现
- path: frameworks/base/log/ace_trace.cpp
  lines: 101-116
  description: AceScopedTraceFlag 构造/析构实现，flag 门控
- path: frameworks/base/log/ace_trace.cpp
  lines: 118-153
  description: AceAsyncScopedTrace 实现，含 id_ 初始化:137
- path: frameworks/base/log/ace_trace.cpp
  lines: 155-165
  description: ResTracer 构造/析构实现
- path: frameworks/base/log/ace_trace.cpp
  lines: 167-173
  description: ContainerTracer 构造实现
- path: frameworks/base/log/ace_trace.cpp
  lines: 175-183
  description: UINodeTracer 构造实现
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 22
  description: extern "C" setResTraceId 声明
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 25-26
  description: ACE_TRACE_COMMERCIAL / ANIMATION_TRACE_COMMERCIAL 常量定义
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 29-39
  description: AceTraceBegin → StartTrace / AceTraceEnd → FinishTrace
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 41-49
  description: AceTraceBeginCommercial / AceTraceEndCommercial 实现
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 51-71
  description: AceAsyncTraceBegin / AceAsyncTraceEnd 实现，isAnimationTrace 分支
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 73-93
  description: AceAsyncTraceBeginCommercial / AceAsyncTraceEndCommercial 实现
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 95-100
  description: AceCountTrace → CountTrace 实现
- path: adapter/ohos/osal/ace_trace.cpp
  lines: 102-105
  description: AceSetResTraceId → setResTraceId 委托
- path: frameworks/base/thread/frame_trace_adapter.h
  lines: 23-39
  description: FrameTraceAdapter 抽象接口声明
- path: adapter/ohos/osal/frame_trace_adapter_impl.cpp
  lines: 24
  description: INTERVAL_LIMIT = "ffrt.interval.limit" 常量
- path: adapter/ohos/osal/frame_trace_adapter_impl.cpp
  lines: 26-33
  description: AccessFrameTrace：FRAME_TRACE_ENABLE 编译守卫
- path: adapter/ohos/osal/frame_trace_adapter_impl.cpp
  lines: 35-47
  description: QuickExecute / SlowExecute → TraceAndExecute
- path: adapter/ohos/osal/frame_trace_adapter_impl.cpp
  lines: 49-55
  description: EnableFrameTrace 实现
- path: adapter/ohos/osal/frame_trace_adapter_impl.cpp
  lines: 57-61
  description: GetInstance 返回 FrameTraceAdapterImpl
- path: adapter/ohos/osal/frame_trace_adapter_impl.cpp
  lines: 63-69
  description: IsEnabled 实现
- path: adapter/ohos/osal/frame_trace_adapter_impl.cpp
  lines: 71-78
  description: SetFrameTraceLimit 系统参数设置
- path: adapter/ohos/osal/frame_trace_adapter_fake_impl.cpp
  lines: 19-43
  description: Fake 实现（全部 no-op / return false）
- path: adapter/preview/osal/frame_trace_adapter_impl.cpp
  lines: 19-22
  description: Preview 实现（GetInstance 返回 nullptr）
- path: frameworks/base/thread/background_task_executor.cpp
  lines: 28
  description: MAX_BACKGROUND_THREADS=8 常量
- path: frameworks/base/thread/background_task_executor.cpp
  lines: 50-65
  description: 构造函数 FrameTrace 启用检查
- path: frameworks/base/thread/background_task_executor.cpp
  lines: 83-115
  description: PostTask(&&) FrameTrace 路由
- path: frameworks/base/thread/background_task_executor.cpp
  lines: 117-149
  description: PostTask(const&) FrameTrace 路由
- path: frameworks/base/log/trace_id.h
  lines: 23-30
  description: TraceId 抽象基类声明
- path: adapter/ohos/osal/trace_id_impl.cpp
  lines: 22-42
  description: TraceIdImpl 实现（HiTraceChain::GetId/SetId/ClearId）
- path: adapter/ohos/osal/trace_id_impl.cpp
  lines: 44-47
  description: TraceId::CreateTraceId 工厂方法
- path: adapter/ohos/osal/system_properties.cpp
  lines: 142-215
  description: 12 个 trace 开关系统属性读取函数
```
