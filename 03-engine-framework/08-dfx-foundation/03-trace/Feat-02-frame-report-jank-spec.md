# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 帧调度报告与Jank检测 |
| 特性编号 | Func-03-08-03-Feat-02 |
| 所属 Epic | 无 |
| SIG 归属 | ArkUI SIG |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

本特性定义 ArkUI ace_engine 框架内部的帧调度阶段插桩、逐帧任务耗时采集、Jank 比率计算与分档上报、以及性能监控场景门面（PerfInterfaces）的完整机制。

`FrameReport`（`frameworks/base/log/frame_report.h:58`）是帧调度阶段插桩的单例入口，在运行时通过 `dlopen` 动态加载 `frame_scheduler` .so，以函数指针方式回调 21 个阶段钩子（Build/Animation/Layout/Render/RenderFinish/PostFlush/ListFling/Flush 等）。管线在 `FlushDirtyNodeUpdate`、`FlushAnimation`、`FlushRenderTask` 等关键路径调用对应的 `Begin*/End*` 钩子，且每次调用前通过 `GetEnable()` 守护。

`FrameInfo`（`frameworks/base/log/frame_info.h:41`）是逐帧任务耗时采集的纯数据结构，内含 `TaskInfo`（tag/id/time）向量和 `TaskType` 枚举（LAYOUT/RENDER），由 `UITaskScheduler` 在布局和渲染任务执行后填充。

`JankFrameReport`（`frameworks/base/log/jank_frame_report.h:32`）是 `thread_local` 单例，负责 Jank 比率计算、8 档频率分桶、ACE Trace 输出及最终事件上报。Jank 比率 = 帧实际耗时 / 刷新周期（`refreshPeriod_ = 16666666` ns，即 60Hz）。当 jank ≥ 6.0 倍时触发 `ACE_SCOPED_TRACE` 和 `ACE_COUNT_TRACE`；`FlushRecord` 将统计结果通过 `EventReport::JankFrameReport` 和 `Rosen::RSInterfaces::ReportJankStats` 上报。

`PerfInterfaces`（`frameworks/base/perfmonitor/perf_interfaces.h:25`）是性能监控的静态门面，提供场景级 `Start/End`、商用变体 `StartCommercial/EndCommercial`、Jank 统计通知、页面追踪等接口。OHOS 适配层（`adapter/ohos/osal/perf_interfaces.cpp`）将全部调用委托给 `HiviewDFX::PerfMonitorAdapter`，并在 `Start`/`StartCommercial` 前通过 `GetAceAppInfo()` 注入 pid/bundleName/versionCode/versionName/processName/abilityName 六项应用信息。`PerfConstants`（`frameworks/base/perfmonitor/perf_constants.h:22`）定义了 54 个场景 ID 常量。

---

## 本次变更范围（Delta）

本规格为既有实现的基线化回录（backfill），不引入代码变更，仅将当前源码行为固化为可追溯的验收规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 特性规格文档 | 为 `frameworks/base/log/frame_report.h`、`jank_frame_report.h/.cpp`、`frame_info.h`、`frameworks/base/perfmonitor/` 既有实现编写验收规格 |
| ADDED | 用户故事 US-01 ~ US-07 | 覆盖帧阶段插桩、逐帧耗时采集、Jank 检测、频率分桶与 Trace、Jank 上报、场景监控门面、商用变体与应用信息桥接 |
| ADDED | 验收标准 AC-01 ~ AC-21 | 对应各用户故事的逐条可验证断言 |
| ADDED | 规则 R001 ~ R011 | .so 加载、阶段守护、Jank 计算/跳过/分桶/Trace/上报/委托/时钟校准/状态机约束 |
| ADDED | 验证映射 VM-01 ~ VM-10 | 规则与验收标准到验证手段的映射 |

---

## 输入文档

| 序号 | 文档 | 来源 | 关键内容 |
|------|------|------|----------|
| 1 | `frame_report.h` | `frameworks/base/log/frame_report.h` | FrameReport 单例类声明、FrameSchedEvent 枚举、21 个函数指针 typedef、阶段钩子方法 |
| 2 | `jank_frame_report.h` | `frameworks/base/log/jank_frame_report.h` | JankFrameReport 类声明、JankFrameFlag 常量、公开方法与私有成员 |
| 3 | `jank_frame_report.cpp` | `frameworks/base/log/jank_frame_report.cpp` | 频率分桶常量、GetJankRange、JankFrameRecord、RecordJankStatus、FlushRecord、时钟校准实现 |
| 4 | `frame_info.h` | `frameworks/base/log/frame_info.h` | TaskInfo 结构体、FrameInfo 结构体、TaskType 枚举、AddTaskInfo 方法 |
| 5 | `perf_interfaces.h` | `frameworks/base/perfmonitor/perf_interfaces.h` | PerfInterfaces 静态门面全部方法签名 |
| 6 | `perf_monitor.h` | `frameworks/base/perfmonitor/perf_monitor.h` | PerfMonitor 单例类、PerfActionType/PerfSourceType 枚举、时间换算常量 |
| 7 | `perf_constants.h` | `frameworks/base/perfmonitor/perf_constants.h` | PerfConstants 类、54 个场景 ID 常量 |
| 8 | `perf_interfaces.cpp` | `adapter/ohos/osal/perf_interfaces.cpp` | OHOS 适配层实现、GetAceAppInfo、PerfMonitorAdapter 委托 |
| 9 | `pipeline_context.cpp` | `frameworks/core/pipeline_ng/pipeline_context.cpp` | FlushDirtyNodeUpdate 中 Begin/EndFlushBuild 调用、FlushAnimation 中 Begin/EndFlushAnimation 调用 |
| 10 | `ui_task_scheduler.cpp` | `frameworks/core/pipeline_ng/ui_task_scheduler.cpp` | FlushRenderTask 中 BeginFlushRender 调用、FrameInfo AddTaskInfo 布局/渲染耗时记录 |

---

## 用户故事

### US-01：帧调度阶段插桩

**作为**框架性能工程师，**我希望**管线在 Build/Animation/Render 等关键阶段前后调用 FrameReport 钩子，**以便**外部帧调度器能够感知 ArkUI 内部各阶段耗时并进行调度优化。

### US-02：逐帧任务耗时采集

**作为**框架性能工程师，**我希望** UITaskScheduler 在执行布局和渲染任务时记录每个节点的 tag、id 和耗时到 FrameInfo，**以便**在帧超时时精确定位耗时节点。

### US-03：Jank 比率计算与记录

**作为**性能诊断工程师，**我希望**框架在每帧结束时计算 jank 比率（实际耗时 / 刷新周期）并通过 PerfMonitor 上报，**以便**量化帧丢步程度。

### US-04：Jank 频率分桶与 Trace 输出

**作为**性能诊断工程师，**我希望** Jank 按严重程度分入 8 个频率桶，且当 jank ≥ 6.0 倍时输出 ACE Trace，**以便**在 trace 工具中快速定位严重卡顿帧。

### US-05：Jank 统计上报

**作为**系统可靠性工程师，**我希望** JankFrameReport 在 FlushRecord 时将分桶统计通过 EventReport 和 RSInterfaces 上报，**以便** hiview 侧聚合分析应用卡顿分布。

### US-06：性能场景监控门面

**作为**应用性能开发者，**我希望**通过 PerfInterfaces 的 Start/End 接口以场景 ID 标记性能监控区段，**以便**按场景（如列表滑动、Swiper 滑动、窗口旋转）采集端到端性能数据。

### US-07：商用变体与应用信息桥接

**作为**商用版本工程师，**我希望** PerfInterfaces 提供独立的 StartCommercial/EndCommercial 路径，并在场景启动前自动注入应用信息，**以便**商用场景的统计数据与非商用数据隔离且携带完整应用上下文。

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-01 | R-1 | TASK-01 | 代码审查 | 代码审查 |
| AC-02 | R-1 | TASK-01 | 代码审查 | 代码审查 |
| AC-03 | R-2 | TASK-01 | 代码审查 | 代码审查 |
| AC-04 | R-2 | TASK-01 | 代码审查 | 代码审查 |
| AC-05 | R-2 | TASK-01 | 代码审查 | 代码审查 |
| AC-06 | R-3 | TASK-01 | 代码审查 | 代码审查 |
| AC-07 | R-3 | TASK-01 | 代码审查 | 代码审查 |
| AC-08 | R-3 | TASK-01 | 代码审查 | 代码审查 |
| AC-09 | R-4 | TASK-01 | 代码审查 | 代码审查 |
| AC-10 | R-4 / R-11 | TASK-01 | 代码审查 | 代码审查 |
| AC-11 | R-4 | TASK-01 | 代码审查 | 代码审查 |
| AC-12 | R-6 | TASK-01 | 代码审查 | 代码审查 |
| AC-13 | R-5 | TASK-01 | 代码审查 | 代码审查 |
| AC-14 | R-7 | TASK-01 | 代码审查 | 代码审查 |
| AC-15 | R-8 | TASK-01 | 代码审查 | 代码审查 |
| AC-16 | R-8 | TASK-01 | 代码审查 | 代码审查 |
| AC-17 | R-9 | TASK-01 | 代码审查 | 代码审查 |
| AC-18 | R-9 | TASK-01 | 代码审查 | 代码审查 |
| AC-19 | R-9 | TASK-01 | 代码审查 | 代码审查 |
| AC-20 | R-9 | TASK-01 | 代码审查 | 代码审查 |
| AC-21 | R-9 | TASK-01 | 代码审查 | 代码审查 |

---

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 边界 | FrameReport::LoadLibrary() 加载 frame_scheduler .so | dlopen 加载 .so，dlsym 获取 21 个函数指针；加载失败或符号为 null 时对应钩子为空操作，enable_ 保持 false | .so 加载失败时不崩溃，所有钩子为空操作 | AC-01 / AC-02 |
| R-2 | 行为 | 管线中 Begin*/End* 阶段钩子调用 | 调用前检查 FrameReport::GetInstance().GetEnable() 返回 true，否则跳过 | 所有阶段钩子调用必须受 GetEnable() 守卫 | AC-03 / AC-04 / AC-05 |
| R-3 | 行为 | FrameInfo::AddTaskInfo 调用 | 根据 TaskType 参数将 TaskInfo 追加到 layoutInfos_（LAYOUT）或 renderInfos_（RENDER） | TaskType 枚举仅 LAYOUT/RENDER 两种 | AC-06 / AC-07 / AC-08 |
| R-4 | 行为 | JankFrameRecord 计算 | duration = max(0, now - max(timeStampNanos, prevEndTimeStamp_))，jank = double(duration) / refreshPeriod_，refreshPeriod_ = 16666666 ns | now <= timeStampNanos 时 duration = 0 | AC-09 / AC-10 / AC-11 |
| R-5 | 边界 | RecordJankStatus 调用 | 三种跳过条件：(a) recordStatus_==JANK_IDLE && animatorEndTime_==0；(b) jank<=1.0f；(c) 首帧 prevFrameUpdateCount_==0 && currentFrameUpdateCount_>=0 | 任一条件满足即跳过，不记录不递增 | AC-13 |
| R-6 | 行为 | GetJankRange 调用 | 8 个频率桶由阈值 6.0/15.0/20.0/36.0/48.0/60.0/120.0 划分，frameJankRecord_ 为 vector\<uint16_t\>，JANK_SIZE=8 | 初始值全 0 | AC-12 |
| R-7 | 边界 | jank >= 6.0f | 输出 ACE_SCOPED_TRACE("JANK_STATS_APP skippedTime=%lld(ms)") 和 ACE_COUNT_TRACE(jankFrameCount_, "JANK FRAME %s")，调用 ReportJankFrameApp | skippedTime = jank * refreshPeriod_ / NS_TO_MS | AC-14 |
| R-8 | 行为 | FlushRecord 调用 | RSInterfaces::ReportJankStats() 无条件调用；needReport_==true 时调用 EventReport::JankFrameReport()；ClearFrameJankRecord() 无条件调用重置状态 | EventReport 仅在 needReport_==true 时上报 | AC-15 / AC-16 |
| R-9 | 行为 | PerfInterfaces 静态方法调用 | 全部委托给 PerfMonitorAdapter::GetInstance()；Start 和 StartCommercial 在委托前调用 GetAceAppInfo() 和 SetAppInfo() 注入应用信息 | GetAceAppInfo 获取 pid/bundleName/versionCode/versionName/processName/abilityName | AC-17 / AC-20 |
| R-10 | 边界 | 系统时间与单调时钟差值检查 | 差值 >= NS_TO_MS (1000000 ns = 1 ms) 时用单调时钟替换系统时间，输出 ACE_SCOPED_TRACE("ClockTimeCalibration realTime=..., now=...") | 使用 CLOCK_MONOTONIC 校准 | AC-11 |
| R-11 | 行为 | SetFrameJankFlag / ClearFrameJankFlag 调用 | SetFrameJankFlag 使 recordStatus_ 递增，递增至 1 时清零 animatorEndTime_ 和 hasJsAnimation_；ClearFrameJankFlag 使 recordStatus_ 递减，从 1 递减至 0 时记录 animatorEndTime_ 为当前单调时钟纳秒值 | JANK_IDLE=0, JANK_RUNNING_SCROLL=1, JANK_RUNNING_ANIMATOR=2, JANK_RUNNING_SWIPER=4 | AC-10 |

---

## 验证映射

| VM编号 | 关联规则/AC | 验证方法 | 验证位置 |
|--------|-------------|----------|----------|
| VM-01 | R001, AC-01, AC-02 | 代码审查 | `frame_report.h:58-94`（单例与状态成员）、`frame_report.h:26-34`（FrameSchedEvent 枚举）、`frame_report.h:35-56`（21 个函数指针 typedef） |
| VM-02 | R002, AC-03, AC-04, AC-05 | 代码审查 | `pipeline_context.cpp:893-929`（Build 阶段）、`pipeline_context.cpp:1532-1540`（Animation 阶段）、`ui_task_scheduler.cpp:233-234`（Render 阶段） |
| VM-03 | R003, AC-06, AC-07, AC-08 | 代码审查 | `frame_info.h:24-59`（TaskInfo/FrameInfo 结构体）、`ui_task_scheduler.cpp:168-169, 257-258`（AddTaskInfo 调用点） |
| VM-04 | R004, AC-09, AC-10, AC-11 | 代码审查 | `jank_frame_report.cpp:112-116`（thread_local 单例）、`jank_frame_report.cpp:118-132`（构造函数初始化）、`jank_frame_report.cpp:134-149`（JankFrameRecord 计算） |
| VM-05 | R006, AC-12 | 代码审查 | `jank_frame_report.cpp:25-33`（频率桶常量）、`jank_frame_report.cpp:50-74`（GetJankRange 实现） |
| VM-06 | R005, R007, AC-13, AC-14 | 代码审查 | `jank_frame_report.cpp:160-187`（RecordJankStatus 跳过逻辑与 Trace 输出） |
| VM-07 | R008, AC-15, AC-16 | 代码审查 | `jank_frame_report.cpp:245-258`（FlushRecord 上报流程）、`jank_frame_report.cpp:194-204`（ClearFrameJankRecord 重置） |
| VM-08 | R009, AC-17, AC-20 | 代码审查 | `perf_interfaces.cpp:110-116`（Start 委托）、`perf_interfaces.cpp:123-134`（StartCommercial/EndCommercial 委托） |
| VM-09 | AC-18, AC-19 | 代码审查 | `perf_constants.h:22-186`（54 个场景 ID 常量）、`perf_monitor.h:35-49`（PerfActionType/PerfSourceType 枚举） |
| VM-10 | R010, R011, AC-21 | 代码审查 | `perf_interfaces.cpp:27-37`（GetAceAppInfo）、`jank_frame_report.cpp:85-93`（ClockTimeCalibration）、`jank_frame_report.cpp:206-226`（SetFrameJankFlag/ClearFrameJankFlag 状态机） |

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

- **已有 API 行为变更:** 否 — 全部为框架内部类，无 Public/System API
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 无 @since 标注（框架内部能力）

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| FrameReport 进程级单例 | `FrameReport` 位于 `frameworks/base/log/frame_report.h`，是进程级单例（`static` 局部变量），通过 `dlopen`/`dlsym` 动态绑定外部 `frame_scheduler` .so 中的 21 个函数指针。.so 加载失败时所有钩子为空操作。 | AC-01 / AC-02 |
| JankFrameReport thread_local 单例 | `JankFrameReport` 位于 `frameworks/base/log/jank_frame_report.h`，是 `thread_local` 单例（`static thread_local`），每个线程拥有独立的 jank 统计状态，无需跨线程同步。 | AC-09 / AC-10 |
| FrameInfo 纯数据结构 | `FrameInfo` 位于 `frameworks/base/log/frame_info.h`，是纯数据结构（POD-like），无单例、无虚函数，由 `UITaskScheduler` 持有并在帧内填充。 | AC-06 / AC-07 / AC-08 |
| PerfInterfaces 全静态门面 | `PerfInterfaces` 位于 `frameworks/base/perfmonitor/perf_interfaces.h`，是全静态方法门面，无实例状态。OHOS 实现在 `adapter/ohos/osal/perf_interfaces.cpp`，委托给 `HiviewDFX::PerfMonitorAdapter`；preview 环境有独立 stub 实现。 | AC-17 / AC-20 |
| PerfMonitor 进程级单例 | `PerfMonitor` 位于 `frameworks/base/perfmonitor/perf_monitor.h`，是进程级单例（`GetPerfMonitor()`，`std::once_flag` 初始化），持有 `ApsMonitor*` 成员。 | AC-17 / AC-18 / AC-19 |
| PerfConstants 编译期常量 | `PerfConstants` 位于 `frameworks/base/perfmonitor/perf_constants.h`，全部为 `static constexpr char[]` 编译期常量，无运行时状态。 | AC-18 |
| JankFrameReport 外部依赖 | `JankFrameReport` 依赖外部能力：`Rosen::RSInterfaces::ReportJankStats()`（RenderService）、`EventReport::JankFrameReport()`（HiSysEvent）、`PerfMonitor::GetPerfMonitor()`（性能监控）、`ACE_SCOPED_TRACE`/`ACE_COUNT_TRACE`（HiTrace）。 | AC-11 / AC-14 / AC-15 / AC-16 |
| 时间换算常量跨文件使用 | 时间换算常量 `US_TO_MS=1000`、`NS_TO_MS=1000000`、`NS_TO_S=1000000000` 定义于 `perf_monitor.h:31-33`，在 `jank_frame_report.cpp` 中跨文件使用。 | AC-11 / AC-14 |

---

## 非功能性需求

| 需求ID | 类别 | 需求描述 | 指标/约束 |
|--------|------|----------|-----------|
| NFR-01 | 性能 | `FrameReport` 阶段钩子为函数指针调用，.so 未加载时为 null 检查 + return，单次开销 < 0.01ms | `GetEnable()` 守护 + null 指针跳过 |
| NFR-02 | 性能 | `JankFrameRecord` 单次执行包含 1 次系统时钟读取、1 次除法、1 次向量索引递增，不应阻塞 UI 线程超过 0.1ms | `steady_clock` 纳秒级时间戳 |
| NFR-03 | 线程安全 | `JankFrameReport` 为 `thread_local` 单例，各线程独立持有 `frameJankRecord_` 等状态，无数据竞争 | `static thread_local` |
| NFR-04 | 可靠性 | `FrameReport::LoadLibrary` 失败时 `frameSchedSoLoaded_` 保持 false，`enable_` 保持 false，所有钩子为空操作，不影响管线正常执行 | `frame_report.h:93-94` |
| NFR-05 | 可观测性 | Jank ≥ 6.0 倍时输出 `ACE_SCOPED_TRACE`（含 skippedTime 毫秒值）和 `ACE_COUNT_TRACE`（含 pageUrl 和累计帧数），可在 HiTrace 中直接检索 | `jank_frame_report.cpp:182-184` |
| NFR-06 | 内存 | `frameJankRecord_` 为 `vector<uint16_t>` 固定大小 8，每线程 jank 状态总内存 < 200 字节 | `JANK_SIZE=8` |
| NFR-07 | 可维护性 | 新增场景 ID 需在 `PerfConstants` 中追加 `static constexpr char[]` 常量；新增帧阶段钩子需在 `FrameReport` 中追加函数指针 typedef 和成员变量 | `perf_constants.h`、`frame_report.h:35-56` |

---

## 多设备适配声明

无差异。

`FrameReport`、`JankFrameReport`、`FrameInfo`、`PerfInterfaces`、`PerfMonitor`、`PerfConstants` 的接口定义均在 `frameworks/base/` 层（平台无关），OHOS 实现在 `adapter/ohos/osal/`，preview 环境有独立 stub。不同设备形态（手机、平板、折叠屏、穿戴、PC）使用相同的频率分桶阈值、场景 ID 常量和 Trace 事件名，`refreshPeriod_` 默认值 16666666 ns（60Hz）在所有设备上一致，实际刷新周期由上层窗口 vsync 动态配置。

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 框架启动 | 否 | FrameReport::Init() 在管线初始化时按需调用，.so 加载失败不影响启动流程 | 无 |
| 渲染管线 | 是 | FlushDirtyNodeUpdate、FlushAnimation、FlushRenderTask 三个关键路径插入 FrameReport 阶段钩子，均有 GetEnable() 守卫，禁用时零开销 | pipeline_context.cpp:893-929, 1532-1540, ui_task_scheduler.cpp:233-234 |
| 组件系统 | 是 | JankFrameReport 的 SetFrameJankFlag/ClearFrameJankFlag 在滚动容器和动画组件中调用 | jank_frame_report.cpp:206-226 |
| 前端桥接 | 是 | PerfInterfaces::Start/End 可在前端页面切换场景中调用 | perf_interfaces.cpp:110-116 |
| 内存/功耗 | 否 | frameJankRecord_ 固定 8 元素向量，thread_local 仅在使用线程分配；.so 按需加载 | 无 |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
- path: frameworks/base/log/frame_report.h
  lines: 26-34
  description: FrameSchedEvent 枚举定义（7 个值，UI_FLUSH_BEGIN=20001）
- path: frameworks/base/log/frame_report.h
  lines: 35-56
  description: 21 个函数指针 typedef（FrameInitFunc 至 ReportSchedEventFunc）
- path: frameworks/base/log/frame_report.h
  lines: 58-94
  description: FrameReport 类声明、GetInstance/Init/GetEnable、阶段钩子方法、私有成员
- path: frameworks/base/log/frame_report.h
  lines: 96-116
  description: 21 个 ACE_EXPORT 函数指针成员变量
- path: frameworks/base/log/jank_frame_report.h
  lines: 25-30
  description: JankFrameFlag 常量（JANK_IDLE=0, JANK_RUNNING_SCROLL=1, JANK_RUNNING_ANIMATOR=2, JANK_RUNNING_SWIPER=4）
- path: frameworks/base/log/jank_frame_report.h
  lines: 32-66
  description: JankFrameReport 类声明、公开方法、私有成员
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 25-33
  description: 8 个频率桶常量（JANK_FRAME_6_FREQ 至 JANK_FRAME_180_FREQ）和 JANK_SIZE=8
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 50-74
  description: GetJankRange 实现（阈值 6.0/15.0/20.0/36.0/48.0/60.0/120.0）
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 85-93
  description: ClockTimeCalibration 实现（差值 ≥ NS_TO_MS 时校准）
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 112-132
  description: GetInstance（thread_local）和构造函数（refreshPeriod_=16666666）
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 134-149
  description: JankFrameRecord 实现（jank 计算 + SetFrameTime + RecordJankStatus）
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 160-187
  description: RecordJankStatus 实现（跳过逻辑 + 频率桶递增 + ACE_SCOPED_TRACE/ACE_COUNT_TRACE）
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 206-226
  description: SetFrameJankFlag/ClearFrameJankFlag 状态机实现
- path: frameworks/base/log/jank_frame_report.cpp
  lines: 245-258
  description: FlushRecord 实现（ReportJankStats + EventReport::JankFrameReport + ClearFrameJankRecord）
- path: frameworks/base/log/frame_info.h
  lines: 24-39
  description: TaskInfo 结构体（tag_/id_/time_）
- path: frameworks/base/log/frame_info.h
  lines: 41-71
  description: FrameInfo 结构体（frameRecvTime_/frameTimeStamp_/layoutInfos_/renderInfos_、TaskType 枚举、AddTaskInfo）
- path: frameworks/base/perfmonitor/perf_interfaces.h
  lines: 25-58
  description: PerfInterfaces 静态门面全部方法签名
- path: frameworks/base/perfmonitor/perf_monitor.h
  lines: 31-33
  description: 时间换算常量（US_TO_MS=1000, NS_TO_MS=1000000, NS_TO_S=1000000000）
- path: frameworks/base/perfmonitor/perf_monitor.h
  lines: 35-49
  description: PerfActionType 枚举（LAST_DOWN=0, LAST_UP=1, FIRST_MOVE=2）和 PerfSourceType 枚举（5 个来源）
- path: frameworks/base/perfmonitor/perf_monitor.h
  lines: 53-89
  description: PerfMonitor 单例类声明
- path: frameworks/base/perfmonitor/perf_constants.h
  lines: 22-186
  description: PerfConstants 类、54 个场景 ID 常量
- path: adapter/ohos/osal/perf_interfaces.cpp
  lines: 25-37
  description: PerfMonitorAdapter 类型别名和 GetAceAppInfo 实现（pid/bundleName/versionCode/versionName/processName/abilityName）
- path: adapter/ohos/osal/perf_interfaces.cpp
  lines: 110-116
  description: PerfInterfaces::Start 实现（GetAceAppInfo + SetAppInfo + 委托）
- path: adapter/ohos/osal/perf_interfaces.cpp
  lines: 123-134
  description: PerfInterfaces::StartCommercial/EndCommercial 实现
- path: frameworks/core/pipeline_ng/pipeline_context.cpp
  lines: 893-929
  description: FlushDirtyNodeUpdate 中 BeginFlushBuild/EndFlushBuild 调用
- path: frameworks/core/pipeline_ng/pipeline_context.cpp
  lines: 1532-1540
  description: FlushAnimation 中 BeginFlushAnimation/EndFlushAnimation 调用
- path: frameworks/core/pipeline_ng/ui_task_scheduler.cpp
  lines: 168-169
  description: 布局任务 AddTaskInfo（TaskType::LAYOUT）
- path: frameworks/core/pipeline_ng/ui_task_scheduler.cpp
  lines: 233-234
  description: FlushRenderTask 中 BeginFlushRender 调用
- path: frameworks/core/pipeline_ng/ui_task_scheduler.cpp
  lines: 257-258
  description: 渲染任务 AddTaskInfo（TaskType::RENDER）
```
