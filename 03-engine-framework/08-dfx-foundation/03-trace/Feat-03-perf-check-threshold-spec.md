# 特性规格

| 属性 | 值 |
|------|-----|
| 特性名称 | 性能检查与阈值监控 |
| 特性编号 | Func-03-08-03-Feat-03 |
| 所属 Epic | 无 |
| SIG 归属 | ArkUI SIG |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

---

## 概述

本特性定义 ArkUI ace_engine 框架内部对页面级和函数级性能指标进行阈值检查、违规数据采集与上报的完整机制。该机制由五个核心模块协同构成：

- **AcePerformanceCheck**（`ace_performance_check.h:39`）：性能检查入口，提供 `Start()`/`Stop()` 静态接口控制检查生命周期，维护 JSON 格式的性能信息。
- **AceScopedPerformanceCheck**（`ace_performance_check.h:57`）：RAII 作用域计时器，构造时记录起始时间戳（`GetSysTimestamp()`），析构时计算耗时（纳秒除以 `CONVERT_NANOSECONDS` = 1000000 转毫秒），超过 `FUNCTION_TIMEOUT`（150ms）时通过 `EventReport::ReportFunctionTimeout` 上报。
- **PerformanceCheckNode**（`performance_check_types.h:24`）：性能检查数据载体，包含 pageDepth、childrenSize、codeRow、codeCol、layoutTime、flexLayouts、foreachItems、nodeTag、pagePath 等字段。
- **AceChecker**（`ace_checker.h:24`）：HiChecker 集成层，检查 `RULE_CHECK_ARKUI_PERFORMANCE` 规则是否激活，持有 8 个可配置阈值，通过系统参数 `arkui.performancecheck.*` 初始化。
- **AcePerformanceMonitor**（`ace_performance_monitor.h`）：thread_local 帧级性能监控，按 6 种 MonitorTag 分类统计耗时，通过 `ACE_SCOPED_TRACE` 输出 trace。

此外，**AceTracker**（`ace_tracker.h:32`）提供 JSON 格式的计时追踪，**AceScoringLog**（`ace_scoring_log.h:29`）提供评分日志记录，分别受各自的运行时开关控制。

检查结果覆盖 5 个规则类别（故障码 9901–9905）：
- 9901：页面节点数 / 深度超限
- 9902：函数执行超时
- 9903：Vsync 超时 / 节点布局超时
- 9904：ForEach 条目数超限
- 9905：Flex 布局次数超限

---

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 为已有实现补录规格文档 | 覆盖 ace_performance_check.h/.cpp、performance_check_types.h、ace_performance_monitor.h/.cpp、ace_checker.h、ace_tracker.h/.cpp、ace_scoring_log.h/.cpp、adapter/ohos/osal/ace_checker.cpp |
| ADDED | 用户故事 5 个、验收标准 18 个、规则 10 条 | 完整追溯源码行号 |
| ADDED | context-references 表 | 16 条源码引用 |

---

## 输入文档

| 序号 | 文档 | 来源 | 关键内容 |
|------|------|------|----------|
| 1 | `ace_performance_check.h` | `frameworks/base/log/ace_performance_check.h` | AcePerformanceCheck 和 AceScopedPerformanceCheck 类声明、CodeInfo 结构体 |
| 2 | `ace_performance_check.cpp` | `frameworks/base/log/ace_performance_check.cpp` | Start/Stop、RecordPerformanceCheckData、5 个 Record 方法、SourceMap 解析、WebSocket 发送 |
| 3 | `performance_check_types.h` | `frameworks/base/log/performance_check_types.h` | PerformanceCheckNode 结构体、PerformanceCheckNodeMap 类型别名 |
| 4 | `ace_performance_monitor.h` | `frameworks/base/log/ace_performance_monitor.h` | MonitorTag 枚举、MonitorStatus 枚举、ScopedMonitor 类、ArkUIPerfMonitor 类、6 个耗时宏 |
| 5 | `ace_performance_monitor.cpp` | `frameworks/base/log/ace_performance_monitor.cpp` | thread_local 单例实现、FlushPerfMonitor、FlushPerfMonitorOutOfVsync、RecordTimeSlice 嵌套状态管理 |
| 6 | `ace_checker.h` | `frameworks/base/log/ace_checker.h` | AceChecker 类声明、8 个阈值 getter、IsPerformanceCheckEnabled/NotifyCaution/InitPerformanceParameters/SetPerformanceCheckStatus |
| 7 | `ace_checker.cpp` | `adapter/ohos/osal/ace_checker.cpp` | HiChecker 委托实现、8 个默认阈值常量、系统参数读取 |
| 8 | `ace_tracker.h` | `frameworks/base/log/ace_tracker.h` | ACE_FUNCTION_TRACK 宏、AceTracker 和 AceScopedTracker 类声明 |
| 9 | `ace_tracker.cpp` | `frameworks/base/log/ace_tracker.cpp` | JSON 计时 Start/Stop、AceScopedTracker 微秒级 RAII 实现 |
| 10 | `ace_scoring_log.h` | `frameworks/base/log/ace_scoring_log.h` | ACE_SCORING_EVENT/ACE_SCORING_COMPONENT 宏、AceScoringLog 类声明 |
| 11 | `ace_scoring_log.cpp` | `frameworks/base/log/ace_scoring_log.cpp` | Init() once_flag 初始化、isDebuggingEnabled_ 门控、GetSysTimestamp 计时 |

---

## 用户故事

### US-01：性能检查生命周期管理

**作为**性能优化工程师，**我希望**通过 `AcePerformanceCheck::Start()` 和 `Stop()` 控制性能检查的开始和结束，**以便**在需要时采集性能数据，采集完成后输出到 JSON 文件或通过 WebSocket 发送。

### US-02：页面级阈值违规检测

**作为**应用开发者，**我希望**框架自动检测页面节点数、页面深度、子节点数是否超过阈值，**以便**在开发阶段发现组件树过于复杂的问题。

### US-03：函数执行超时检测

**作为**框架开发者，**我希望**通过 RAII 作用域计时器自动测量关键函数执行时间并在超时时上报，**以便**定位卡顿根因而无需手动插桩。

### US-04：Vsync 超时与节点布局超时检测

**作为**渲染管线工程师，**我希望**在 Vsync 周期超过阈值时记录页面级和节点级布局耗时，**以便**识别布局性能瓶颈。

### US-05：ForEach 和 Flex 布局过量检测

**作为**组件开发者，**我希望**检测 ForEach 条目数和 Flex 布局次数是否超过阈值，**以便**避免列表过大或布局重算过多导致的性能问题。

### US-06：帧级性能监控

**作为**性能分析工程师，**我希望**通过 thread_local 的 ArkUIPerfMonitor 按组件创建/生命周期/更新/JS回调/静态API/其他六类统计每帧耗时，**以便**在 trace 中观察框架开销占比。

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-01 | R001 | TASK-01 | 代码审查 | 代码审查 |
| AC-02 | R001 | TASK-01 | 代码审查 | 代码审查 |
| AC-03 | R001 | TASK-01 | 代码审查 | 代码审查 |
| AC-04 | R002 | TASK-01 | 代码审查 | 代码审查 |
| AC-05 | R002 | TASK-01 | 代码审查 | 代码审查 |
| AC-06 | R004 | TASK-01 | 代码审查 | 代码审查 |
| AC-07 | R004 | TASK-01 | 代码审查 | 代码审查 |
| AC-08 | R006 | TASK-01 | 代码审查 | 代码审查 |
| AC-09 | R004 | TASK-01 | 代码审查 | 代码审查 |
| AC-10 | R007 | TASK-01 | 代码审查 | 代码审查 |
| AC-11 | R002 | TASK-01 | 代码审查 | 代码审查 |
| AC-12 | R009 | TASK-01 | 代码审查 | 代码审查 |
| AC-13 | R009 | TASK-01 | 代码审查 | 代码审查 |
| AC-14 | R009 | TASK-01 | 代码审查 | 代码审查 |
| AC-15 | R009 | TASK-01 | 代码审查 | 代码审查 |
| AC-16 | R008 | TASK-01 | 代码审查 | 代码审查 |
| AC-17 | R009 | TASK-01 | 代码审查 | 代码审查 |
| AC-18 | R003 | TASK-01 | 代码审查 | 代码审查 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | OHOS 平台调用 IsPerformanceCheckEnabled() | 检查 HiChecker::Contains(RULE_CHECK_ARKUI_PERFORMANCE) 并 OR 运算 isPerformanceCheckEnabled_ | 非 OHOS 平台仅返回 isPerformanceCheckEnabled_ | AC-1.1, AC-1.2 |
| R-2 | 行为 | IsPerformanceCheckEnabled() 返回 true 且 InitPerformanceParameters() 执行 | 8 个阈值取默认值：pageNodes=1000, pageDepth=30, nodeChildren=100, functionTimeout=15ms, vsyncTimeout=500ms, nodeTimeout=15ms, foreachItems=50, flexLayouts=8 | 默认值不可低于0 | AC-2.1 |
| R-3 | 行为 | IsPerformanceCheckEnabled() 返回 true | InitPerformanceParameters() 通过 GetIntParameter 读取系统参数 arkui.performancecheck.{故障码}.{参数名} | 参数不存在时使用默认值 | AC-2.2 |
| R-4 | 行为 | AceScopedPerformanceCheck 析构或 AceScopedTracker 析构 | 纳秒/微秒分别除以 1000000/1000 转为毫秒 | CONVERT_NANOSECONDS=1000000 | AC-3.1, AC-3.2 |
| R-5 | 边界 | CheckIsRuleContainsPage 检查规则去重 | WebSocket 模式检查 GetCheckMessge() 含 ruleType；非 WebSocket 模式遍历 JSON 数组检查 pagePath | 重复规则跳过不重复上报 | AC-4.1 |
| R-6 | 边界 | RecordVsyncTimeout 排除框架节点 | nodeTag 为 "page"/"ContainerModal"/"JsView" 的节点不纳入性能报告 | 仅排除3种框架内部节点标签 | AC-5.1 |
| R-7 | 行为 | ForEach 条目记录时按 codeRow 聚合 | 同一 codeRow 下 foreachItems 自增，items 值为 foreachItems+1（含自身） | foreachItems 从0开始 | AC-6.1 |
| R-8 | 边界 | SetRecordingStatus 处理 STATIC_API 标签 | RUNNING 时 push bkMonitorStatus_，IDLE 时 pop，实现嵌套耗时归属 | bkMonitorStatus_ 为栈结构 | AC-7.1 |
| R-9 | 边界 | GetAcePerformanceMonitorEnabled() 为 false | 所有 Monitor 操作时间戳为零、不累加耗时 | true 时才产生有效数据 | AC-7.2 |
| R-10 | 边界 | AceScoringLog isDebuggingEnabled_ 为 false | 构造函数和析构函数提前返回，不记录任何数据 | std::call_once 初始化，值为 IsScoringEnabled(procName_) | AC-7.3 |

---

## 验证映射

| VM编号 | 规则ID | 验证方法 | 验证位置 |
|--------|--------|----------|----------|
| VM-01 | R001 | 代码审查 `IsPerformanceCheckEnabled()` 的 HiChecker 调用和 OR 逻辑 | `ace_checker.cpp:52-55`（HICHECKER_EXISTS 分支）、`ace_checker.cpp:94-97`（非 HICHECKER 分支） |
| VM-02 | R002 | 代码审查匿名命名空间中的 8 个常量定义及其与静态成员的绑定 | `ace_checker.cpp:29-36`、`ace_checker.cpp:39-46` |
| VM-03 | R003 | 代码审查 `InitPerformanceParameters` 的 `system::GetIntParameter` 调用和参数命名 | `ace_checker.cpp:64-78` |
| VM-04 | R004 | 代码审查 `AceScopedPerformanceCheck` 析构和 `AceScopedTracker` 析构的时间单位转换 | `ace_performance_check.cpp:97`、`ace_tracker.cpp:51` |
| VM-05 | R005 | 代码审查 `CheckIsRuleContainsPage` 的 WebSocket 分支和 JSON 遍历逻辑 | `ace_performance_check.cpp:108-138` |
| VM-06 | R006 | 代码审查 `RecordVsyncTimeout` 中 nodeTag 过滤条件 | `ace_performance_check.cpp:319-320` |
| VM-07 | R007 | 代码审查 `RecordForEachItemsCount` 的 codeRow 聚合和 items+1 逻辑 | `ace_performance_check.cpp:220-228, 358` |
| VM-08 | R008 | 代码审查 `SetRecordingStatus` 的 STATIC_API 栈操作 | `ace_performance_monitor.cpp:110-128` |
| VM-09 | R009 | 代码审查 `GetTimePoint` 的开关检查和各 Record 方法的隐式依赖 | `ace_performance_monitor.cpp:29-34` |
| VM-10 | R010 | 代码审查 `AceScoringLog::Init` 的 call_once 和 isDebuggingEnabled_ 门控 | `ace_scoring_log.cpp:53-63`、`ace_scoring_log.cpp:34, 67` |

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

- **已有 API 行为变更:** 否 — 全部为框架内部 static 方法或 RAII 类，不暴露为公开 API
- **配置文件格式变更:** 否 — JSON 输出格式与 WebSocket 消息格式保持不变
- **数据存储格式变更:** 否 — 规则码 9901–9905 字段名、trace 标签名均保持不变
- **最低支持版本:** API 9
- **API 版本号策略:** 无 @since 标注（框架内部能力）

---

## 架构约束

| 约束ID | 约束描述 |
|--------|----------|
| C001 | `AcePerformanceCheck` 和 `AceScopedPerformanceCheck` 声明在 `frameworks/base/log/`，实现也在同一目录（`ace_performance_check.cpp`），不依赖 `adapter/` 层。 |
| C002 | `AceChecker` 头文件在 `frameworks/base/log/`，OHOS 实现在 `adapter/ohos/osal/ace_checker.cpp`，通过 `#ifdef HICHECKER_EXISTS` 区分有/无 HiChecker 的平台，无 HiChecker 时 `NotifyCaution` 和 `InitPerformanceParameters` 为空实现。 |
| C003 | `AcePerformanceCheck::Start()` 依赖 `AceChecker::IsPerformanceCheckEnabled()` 作为前置门控；`AceChecker::SetPerformanceCheckStatus()` 是 WebSocket 模式的唯一入口，设置 `isWebSocketCheckEnabled_ = true` 后调用 Start/Stop。 |
| C004 | `AceScopedPerformanceCheck::GetCurrentSourceMap()` 依赖 `Container::Current()` 获取容器实例，区分 Stage 模型（`IsUseStageModel()`）和 FA 模型加载不同的 sourceMap，API 12+ 使用不同的路径拼接策略。 |
| C005 | `ArkUIPerfMonitor` 为 `thread_local static` 单例（`ace_performance_monitor.cpp:51`），每个线程独立维护时间片数据，无法跨线程聚合。 |
| C006 | `AcePerformanceMonitor` 依赖 `SystemProperties::GetAcePerformanceMonitorEnabled()` 运行时开关，false 时所有时间戳为零（`steady_clock::now()` 不被调用），不影响执行路径性能。 |
| C007 | `AceTracker::trackInfo_` 为 static `unique_ptr<JsonValue>`，`AceScopedTracker` 在构造时检查 `trackInfo_` 非空才记录起始时间，析构时检查非空才写入耗时。 |
| C008 | `AceScoringLog` 的 `procName_` 和 `isDebuggingEnabled_` 为 static 成员，通过 `std::call_once` 保证只初始化一次，后续实例共享同一开关状态。 |

---

## 非功能性需求

| 需求ID | 类别 | 需求描述 | 指标/约束 |
|--------|------|----------|-----------|
| NFR-01 | 性能 | `AceScopedPerformanceCheck` 在性能检查未启用时（`performanceInfo_` 为 null）仅做时间戳比较，不执行 JSON 写入，析构开销可忽略 | markTime_ 比较 + 可选 records_.push_back |
| NFR-02 | 性能 | `GetTimePoint` 在 monitor 未启用时直接返回，不调用 `steady_clock::now()` | `ace_performance_monitor.cpp:29-34` |
| NFR-03 | 内存 | `AceScopedPerformanceCheck::records_` 为 `static vector<pair<int64_t, string>>`，在 `RecordFunctionTimeout` 处理后调用 `records_.clear()` 释放内存 | `ace_performance_check.cpp:299` |
| NFR-04 | 线程安全 | `ArkUIPerfMonitor` 为 thread_local，无需加锁；`AceScoringLog::Init` 使用 `std::call_once` 保证初始化线程安全 | `ace_performance_monitor.cpp:51`、`ace_scoring_log.cpp:55-56` |
| NFR-05 | 可配置性 | 8 个阈值均可通过系统参数动态覆盖，参数命名规则为 `arkui.performancecheck.{故障码}.{参数名}`，无需重新编译 | `ace_checker.cpp:64-78` |
| NFR-06 | 可观测性 | 帧级监控输出通过 `ACE_SCOPED_TRACE` 写入 HiTraceMeter，标签分别为 "ArkUIPerfMonitor" 和 "ArkUIOutOfVsyncPerfMonitor"，可在 trace 工具中直接查看 | `ace_performance_monitor.cpp:188, 208` |

---

## 多设备适配声明

无差异。

全部性能检查模块的接口定义在 `frameworks/base/log/` 层（平台无关），OHOS 实现在 `adapter/ohos/osal/`，非 OHOS 平台通过 `#ifdef HICHECKER_EXISTS` 提供空实现。不同设备形态（手机、平板、折叠屏、穿戴）使用相同的阈值默认值和系统参数命名，无需差异化适配。

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 框架启动 | 否 | 性能检查通过 HiChecker 规则或 WebSocket 命令按需激活，不在启动路径同步执行 | 无 |
| 渲染管线 | 是 | RecordPerformanceCheckData 在页面路由完成时调用，遍历 nodeMap 进行阈值比较；ArkUIPerfMonitor::FinishPerf 在帧结束时调用 FlushPerfMonitor 输出 trace | ace_performance_check.cpp:200-241, ace_performance_monitor.cpp:162-210 |
| 组件系统 | 是 | 各组件通过 AceScopedPerformanceCheck 测量函数耗时，通过 6 个 Monitor 宏标记关键路径 | ace_performance_check.cpp:88-106, ace_performance_monitor.h:41-46 |
| 前端桥接 | 是 | AceScopedPerformanceCheck::GetCurrentSourceMap 依赖前端 sourceMap 进行代码行号映射 | ace_performance_check.cpp:420-464 |
| 内存/功耗 | 否 | 性能检查未启用时仅做指针判空，monitor 未启用时不调用系统时钟 API | 无 |

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
- path: frameworks/base/log/ace_performance_check.h
  lines: 33-37
  description: CodeInfo 结构体（row, col, sources）
- path: frameworks/base/log/ace_performance_check.h
  lines: 39-55
  description: AcePerformanceCheck 类声明（Start/Stop、静态成员）
- path: frameworks/base/log/ace_performance_check.h
  lines: 57-92
  description: AceScopedPerformanceCheck 类声明（构造/析构、Record 方法）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 26-38
  description: 常量定义（FAULT_COMPONENT_LARGE="9901"、FUNCTION_TIMEOUT=150、CONVERT_NANOSECONDS=1000000 等）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 50-84
  description: Start() 和 Stop() 实现（JSON 创建、WebSocket/文件输出）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 88-106
  description: AceScopedPerformanceCheck 构造/析构（时间戳记录、超时上报）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 200-241
  description: RecordPerformanceCheckData（nodeMap 遍历、阈值比较、分类记录）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 243-278
  description: RecordPageNodeCountAndDepth（9901 规则、组件子节点记录）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 280-300
  description: RecordFunctionTimeout（9902 规则、records_ 清理）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 302-339
  description: RecordVsyncTimeout（9903 规则、节点排除）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 341-406
  description: RecordForEachItemsCount（9904）和 RecordFlexLayoutsCount（9905）
- path: frameworks/base/log/ace_performance_check.cpp
  lines: 420-464
  description: GetCurrentSourceMap（Stage/FA 模型 sourceMap 加载）
- path: frameworks/base/log/performance_check_types.h
  lines: 24-37
  description: PerformanceCheckNode 结构体（9 个字段）及 PerformanceCheckNodeMap 类型
- path: frameworks/base/log/ace_performance_monitor.h
  lines: 27-46
  description: MonitorTag 枚举（6 值）和 6 个耗时宏
- path: frameworks/base/log/ace_performance_monitor.h
  lines: 50-90
  description: ScopedMonitor 类和 ArkUIPerfMonitor 类（thread_local 单例）
- path: frameworks/base/log/ace_performance_monitor.cpp
  lines: 29-47
  description: GetTimePoint 开关门控、ScopedMonitor 构造/析构
- path: frameworks/base/log/ace_performance_monitor.cpp
  lines: 49-53
  description: ArkUIPerfMonitor::GetInstance thread_local 实现
- path: frameworks/base/log/ace_performance_monitor.cpp
  lines: 110-137
  description: SetRecordingStatus（STATIC_API 嵌套栈管理）
- path: frameworks/base/log/ace_performance_monitor.cpp
  lines: 162-210
  description: FlushPerfMonitor 和 FlushPerfMonitorOutOfVsync（trace 输出）
- path: frameworks/base/log/ace_checker.h
  lines: 24-96
  description: AceChecker 类完整声明（8 个阈值 getter、4 个功能方法）
- path: adapter/ohos/osal/ace_checker.cpp
  lines: 29-46
  description: 8 个默认阈值常量和静态成员初始化
- path: adapter/ohos/osal/ace_checker.cpp
  lines: 52-91
  description: HICHECKER_EXISTS 分支（HiChecker 委托、系统参数读取、SetPerformanceCheckStatus）
- path: frameworks/base/log/ace_tracker.h
  lines: 28-59
  description: ACE_FUNCTION_TRACK 宏、AceTracker 和 AceScopedTracker 类
- path: frameworks/base/log/ace_tracker.cpp
  lines: 24-53
  description: AceTracker Start/Stop 和 AceScopedTracker 微秒级 RAII
- path: frameworks/base/log/ace_scoring_log.h
  lines: 24-48
  description: ACE_SCORING_EVENT/ACE_SCORING_COMPONENT 宏、AceScoringLog 类
- path: frameworks/base/log/ace_scoring_log.cpp
  lines: 31-71
  description: Init() call_once 初始化、isDebuggingEnabled_ 门控、GetSysTimestamp 计时
```
