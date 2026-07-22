# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍与DFX适配 |
| 特性编号 | Func-02-01-01-Feat-05 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P1 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`adapter/ohos/osal/` + `adapter/ohos/capability/` + `frameworks/base/log/` + `frameworks/base/perfmonitor/` + `frameworks/base/ressched/` + `frameworks/core/accessibility/` + `frameworks/core/common/`
- 设计文档：`02-cross-platform/01-platform-adapter/01-oh-platform-adapter/design.md`

## 用户故事

### US-1: Accessibility 平台桥接

作为一个 ACE 引擎开发者，我希望 JsAccessibilityManager 桥接 OHOS AccessibilitySystemAbilityClient，使 ACE 无障碍节点树能通过 OHOS 无障碍服务完成注册、查询、操作和事件分发。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN JsAccessibilityManager::InitializeCallback THEN 注册 AccessibilityElementOperator 到 OHOS AccessibilitySystemAbilityClient | 正常 |
| AC-1.2 | WHEN RegisterInteractionOperation(windowId) THEN 创建 JsInteractionOperation（AccessibilityElementOperator 子类）并注册到 OHOS 无障碍框架 | 正常 |
| AC-1.3 | WHEN DeregisterInteractionOperation THEN 从 OHOS 无障碍框架注销 InteractionOperation | 正常 |
| AC-1.4 | WHEN SearchElementInfoByAccessibilityId THEN 通过 OHOS AccessibilityElementOperator 查询元素信息 | 正常 |
| AC-1.5 | WHEN SearchElementInfosByText THEN 按文本搜索并返回 AccessibilityElementInfo 列表 | 正常 |
| AC-1.6 | WHEN FindFocusedElementInfo THEN 查找当前焦点元素信息 | 正常 |
| AC-1.7 | WHEN FocusMoveSearch THEN 通过 AccessibilityFocusStrategy 执行焦点移动搜索 | 正常 |
| AC-1.8 | WHEN ExecuteAction THEN 将 OHOS ActionType 映射到 ArkUI ActionClick/Focus/etc 并执行 | 正常 |
| AC-1.9 | WHEN SendAccessibilityAsyncEvent/SyncEvent THEN 发送 AccessibilityEventInfo 到 OHOS 无障碍服务 | 正常 |
| AC-1.10 | WHEN SubscribeToastObserver/StateObserver THEN 注册 AccessibilityConfig 和 AccessibilityState 观察者 | 正常 |
| AC-1.11 | WHEN IsScreenReaderEnabled THEN 查询 OHOS AccessibilitySystemAbilityClient 屏幕阅读器状态 | 正常 |
| AC-1.12 | WHEN RegisterInteractionOperationAsChildTree THEN 注册子树到 OHOS 无障碍框架（UIExtension 场景） | 正常 |
| AC-1.13 | WHEN WEB_SUPPORTED 宏定义 THEN WebInteractionOperation 提供 Web 无障碍操作桥接 | 边界 |

### US-2: FocusStrategy 焦点移动策略

作为一个 ACE 引擎开发者，我希望 AccessibilityFocusStrategy 和 FocusRulesCheckNode 适配器实现 OHOS 焦点移动规则，使无障碍焦点能在 NG 组件树中按规则遍历。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN FocusRulesCheckNode 包装 FrameNode THEN 提供 GetAceChildren/GetAceParent/IsAccessibiltyVisible 等统一接口 | 正常 |
| AC-2.2 | WHEN AccessibilityFocusStrategy::CanAccessibilityFocus THEN 根据焦点规则判断节点是否可聚焦 | 正常 |
| AC-2.3 | WHEN FindNextReadableNode THEN 按前向规则遍历查找下一个可读节点 | 正常 |
| AC-2.4 | WHEN FindPrevReadableNode THEN 按后向规则遍历查找上一个可读节点 | 正常 |
| AC-2.5 | WHEN FindForwardScrollAncestor/FindBackwardScrollAncestor THEN 查找滚动祖先支持滚动焦点 | 正常 |
| AC-2.6 | WHEN GetParentNodeStopByRootType THEN 检测根类型边界并提前停止遍历 | 正常 |
| AC-2.7 | WHEN FocusStrategyOsalNG THEN 提供 NG 管线特定的焦点移动 OSAL 实现（baseNode/rootNode 追踪） | 正常 |
| AC-2.8 | WHEN AceFocusMoveResult 返回 CHILDTREE/EMBED_TARGET THEN 焦点移动跨越子树或嵌入目标 | 边界 |

### US-3: VirtualAccessibilityNode 虚拟节点管理

作为一个 ACE 引擎开发者，我希望 VirtualAccessibilityNode 构建虚拟无障碍节点树，支持布局、命中测试和悬停事件分发。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN AddChild/RemoveChild THEN 构建虚拟节点树父子关系 | 正常 |
| AC-3.2 | WHEN SetRect/GetGlobalRect THEN 设置和计算虚拟节点布局边界 | 正常 |
| AC-3.3 | WHEN HitTest(point) THEN 从右到左遍历子节点返回最深层命中节点 | 正常 |
| AC-3.4 | WHEN OnAccessibilityHover THEN 分发悬停事件到虚拟节点树并更新 lastHovering_ | 正常 |
| AC-3.5 | WHEN CanAccessibilityFocus THEN 通过 AccessibilityFocusStrategy 判断虚拟节点是否可聚焦 | 正常 |
| AC-3.6 | WHEN CloneTree THEN 深拷贝虚拟节点树 | 正常 |

### US-4: DFX 日志与事件报告

作为一个 ACE 引擎开发者，我希望 LogWrapper 桥接 OHOS hilog，EventReport 桥接 OHOS HiSysEvent，FrameTraceAdapter 桥接 RS 渲染服务帧追踪。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN USE_HILOG 定义 THEN LogWrapper::PrintLog 桥接到 HILOG_IMPL 输出日志 | 正常 |
| AC-4.2 | WHEN IS_RELEASE_VERSION 定义 THEN SEC_PARAM/SEC_TAG_LOGI 掩码安全字段 | 正常 |
| AC-4.3 | WHEN STRIP_RELEASE_LOG 定义 THEN 编译期剥离 LOGD/LOGI/LOGW | 边界 |
| AC-4.4 | WHEN ACE_INSTANCE_LOG 定义 THEN 日志前缀附加实例 ID | 正常 |
| AC-4.5 | WHEN EventReport::SendAppStartException THEN 通过 HiSysEventWrite 报告 FAULT 事件 | 正常 |
| AC-4.6 | WHEN EventReport::ANRRawReport THEN 通过 HiSysEventWrite SECURITY 级别报告 ANR 事件 | 正常 |
| AC-4.7 | WHEN EventReport::JankFrameReport THEN 通过 HiSysEventWrite STATISTIC 级别报告帧抖动 | 正常 |
| AC-4.8 | WHEN EventReport::ReportAccessibilityFailEvent THEN 报告无障碍操作失败事件 | 正常 |
| AC-4.9 | WHEN EventReport 发送 11 类异常 THEN 每类映射到独立 HiSysEvent FAULT 参数 | 正常 |
| AC-4.10 | WHEN Resource_SCHEDULE_SERVICE_ENABLE 定义 THEN EventReport 通过 ResSchedClient 报告资源调度事件 | 边界 |

### US-5: Watchdog/ANR 检测

作为一个 ACE 引擎开发者，我希望 WatchDog + AnrThread + XcollieInterface 检测线程卡顿和 ANR，并通过 OHOS HiviewDFX 报告和弹窗处理。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN WatchDog::Register(instanceId) THEN 创建 JS+UI 双 ThreadWatcher | 正常 |
| AC-5.2 | WHEN ThreadWatcher::Check THEN 定期检测线程状态（3s/2s/1s 间隔） | 正常 |
| AC-5.3 | WHEN IsThreadStuck THEN 比较 loopTime_/threadTag_ 增长判断线程卡顿 | 正常 |
| AC-5.4 | WHEN 状态转换 NORMAL→WARNING→FREEZE THEN 依次执行 HiviewReport/RawReport/ShowDialog | 正常 |
| AC-5.5 | WHEN BuriedBomb/DefusingBomb THEN 入队/出队输入任务 ID 用于 ANR 检测 | 正常 |
| AC-5.6 | WHEN DetonatedBomb THEN 输入任务超过 5s 未处理则触发 ANR 弹窗 | 正常 |
| AC-5.7 | WHEN AnrThread::PostTaskToTaskRunner THEN 委托到 HiviewDFX::Watchdog::RunOneShotTask | 正常 |
| AC-5.8 | WHEN XcollieInterface::SetTimerCount THEN 委托到 HiviewDFX::XCollie 设置超时计数 | 正常 |
| AC-5.9 | WHEN OHOS_PLATFORM 定义 THEN GC 触发信号处理（SIG=60）初始化和 sigtimedwait 检测 | 边界 |

### US-6: Dump/Inspector/AceChecker

作为一个 ACE 引擎开发者，我希望 DumpLog 提供格式化树输出，LayoutInspector 桥接 IDE 和 RS 渲染服务进行布局检查，AceChecker 从系统参数加载性能阈值。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN DumpLog::Print(depth, className, childSize) THEN 格式化输出组件树层级信息 | 正常 |
| AC-6.2 | WHEN DumpLog::AddDesc(args) THEN 模板化累积描述字段 | 正常 |
| AC-6.3 | WHEN DumpLog::PrintJson THEN 输出 JSON 格式 dump | 正常 |
| AC-6.4 | WHEN DumpLog::OutPutByCompress THEN zlib 压缩大型 dump 输出 | 正常 |
| AC-6.5 | WHEN LayoutInspector::GetInspectorTreeJsonStr THEN 生成完整组件树 JSON 字符串 | 正常 |
| AC-6.6 | WHEN LayoutInspector::CreateLayoutInfo THEN 创建布局快照信息 | 正常 |
| AC-6.7 | WHEN LayoutInspector::GetSnapshotJson THEN 生成含 3D 捕获的快照 JSON | 正常 |
| AC-6.8 | WHEN LayoutInspector::RegisterConnectCallback THEN 注册 IDE 连接服务器回调 | 正常 |
| AC-6.9 | WHEN AceChecker::InitPerformanceParameters THEN 从 system::GetIntParameter 加载 5 组性能阈值（9901~9905） | 正常 |
| AC-6.10 | WHEN AceChecker::SetPerformanceCheckStatus THEN 启用/禁用性能检查 + WebSocket 通知 | 正常 |

### US-7: 性能监控与资源调度

作为一个 ACE 引擎开发者，我希望 PerfInterfaces 桥接 HiviewDFX PerfMonitorAdapter，ResSchedReport 通过 dlopen 加载 libressched_client.z.so 报告资源调度数据。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN PerfInterfaces::RecordInputEvent THEN 记录输入事件到 PerfMonitorAdapter | 正常 |
| AC-7.2 | WHEN PerfInterfaces::Start/End(sceneId) THEN 标记性能场景开始/结束 | 正常 |
| AC-7.3 | WHEN PerfInterfaces::SetFrameTime THEN 设置帧时间（vsyncTime/duration/jank） | 正常 |
| AC-7.4 | WHEN PerfInterfaces::ReportJankFrameApp THEN 报告帧抖动事件 | 正常 |
| AC-7.5 | WHEN ResSchedReport::ResSchedDataReport THEN 通过 dlsym("ReportData") 异步报告资源调度数据 | 正常 |
| AC-7.6 | WHEN ResSchedReport::ResScheSyncEventReport THEN 通过 dlsym("ReportSyncEvent") 同步报告事件 | 正常 |
| AC-7.7 | WHEN ResSchedReport::OnTouchEvent THEN 报告触摸子事件（down/up/move/cancel） | 正常 |
| AC-7.8 | WHEN ResSchedReport dlopen libressched_client.z.so THEN 动态加载资源调度客户端库 | 正常 |
| AC-7.9 | WHEN CROSS_PLATFORM 定义 THEN ResSchedReport 跳过 dlopen/dlsym（跨平台无 OHOS 资源调度） | 边界 |
| AC-7.10 | WHEN StatisticEventAdapter::ReportStatisticEvents THEN 通过 UIServiceMgrClientIdl 报告统计事件 | 正常 |
| AC-7.11 | WHEN ILongFrame::ReportStartEvent/ReportEndEvent THEN 通过 FFRT+ResSchedDataReport 检测长帧 | 正常 |

### US-8: 异常处理

作为一个 ACE 引擎开发者，我希望 ExceptionHandler 桥接 OHOS ApplicationDataManager 处理 JS 未捕获异常，无观察者时委托 AppMgrClient 自杀终止进程。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-8.1 | WHEN ExceptionHandler::HandleJsException THEN 将 JsErrorObject 转换为 AppExecFwk::ErrorObject 并通知 ApplicationDataManager | 正常 |
| AC-8.2 | WHEN ApplicationDataManager::NotifyUnhandledException THEN 通知异常观察者处理 | 正常 |
| AC-8.3 | WHEN 无异常观察者处理 THEN KillApplicationByUid 通过 AppMgrClient::KillApplicationSelf 终止进程 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.13 | R-1~13 | TASK-F05-01 | 单测+集成测试 | js_accessibility_manager.h |
| AC-2.1~2.8 | R-14~21 | TASK-F05-02 | 单测 | accessibility_focus_strategy.h |
| AC-3.1~3.6 | R-22~27 | TASK-F05-03 | 单测 | accessibility_hover_virtual_node_utils.h |
| AC-4.1~4.10 | R-28~37 | TASK-F05-04 | 单测+编译检查 | log_wrapper.h, event_report.h |
| AC-5.1~5.9 | R-38~46 | TASK-F05-05 | 单测+集成测试 | watch_dog.h, anr_thread.h, xcollieInterface.h |
| AC-6.1~6.10 | R-47~56 | TASK-F05-06 | 单测 | dump_log.h, layout_inspector.h, ace_checker.h |
| AC-7.1~7.11 | R-57~67 | TASK-F05-07 | 单测+集成测试 | perf_interfaces.h, ressched_report.h |
| AC-8.1~8.3 | R-68~70 | TASK-F05-08 | 集成测试 | exception_handler.h |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | InitializeCallback | 注册 AccessibilityElementOperator 到 AccessibilitySystemAbilityClient | windowId 必须有效 | AC-1.1 |
| R-2 | 行为 | RegisterInteractionOperation | 创建 JsInteractionOperation 并注册 | OHOS 无障碍框架为单例 | AC-1.2 |
| R-3 | 行为 | DeregisterInteractionOperation | 注销 InteractionOperation | 注销后不再接收查询请求 | AC-1.3 |
| R-4 | 行为 | SearchElementInfoByAccessibilityId | 按 ID 查询元素信息 | 支持 offset 分页 | AC-1.4 |
| R-5 | 行为 | SearchElementInfosByText | 按文本搜索元素 | 返回 AccessibilityElementInfo 列表 | AC-1.5 |
| R-6 | 行为 | FindFocusedElementInfo | 查找焦点元素 | 支持 INPUT/NODE 焦点类型 | AC-1.6 |
| R-7 | 行为 | FocusMoveSearch | AccessibilityFocusStrategy 焦点移动 | 6 种 AceFocusMoveResult | AC-1.7 |
| R-8 | 行为 | ExecuteAction | OHOS ActionType→ArkUI Action | 支持 10+ Action 类型映射 | AC-1.8 |
| R-9 | 行为 | SendAccessibilityAsyncEvent/SyncEvent | 发送 AccessibilityEventInfo 到 OHOS | 异步立即返回/同步等待响应 | AC-1.9 |
| R-10 | 行为 | SubscribeToastObserver/StateObserver | 注册配置/状态观察者 | AccessibilityConfig 和 AccessibilityStateObserver | AC-1.10 |
| R-11 | 行为 | IsScreenReaderEnabled | 查询屏幕阅读器状态 | AccessibilitySystemAbilityClient::IsScreenReaderEnabled | AC-1.11 |
| R-12 | 行为 | RegisterInteractionOperationAsChildTree | 子树注册（UIExtension） | 父子树 ID 关联 | AC-1.12 |
| R-13 | 边界 | WEB_SUPPORTED 宏定义 | WebInteractionOperation 提供 Web 无障碍操作 | 仅 Web 组件场景 | AC-1.13 |
| R-14 | 行为 | FocusRulesCheckNode 包装 FrameNode | 提供统一接口 | 继承 ReadableRulesNode | AC-2.1 |
| R-15 | 行为 | CanAccessibilityFocus | 判断节点是否可聚焦 | 使用 FocusRuleType 和 CheckSupportScrollAction | AC-2.2 |
| R-16 | 行为 | FindNextReadableNode | 前向焦点遍历 | 支持 SelfAndSameLevel→HigherLevel 逐级搜索 | AC-2.3 |
| R-17 | 行为 | FindPrevReadableNode | 后向焦点遍历 | 支持 ChildAndSelf 反向搜索 | AC-2.4 |
| R-18 | 行为 | FindForward/BackwardScrollAncestor | 查找滚动祖先 | 支持 FIND_FORWARD/BACKWARD/ANY | AC-2.5 |
| R-19 | 行为 | GetParentNodeStopByRootType | 根类型边界检测 | 遍历提前停止 | AC-2.6 |
| R-20 | 行为 | FocusStrategyOsalNG | NG 管线焦点移动 OSAL | baseNode/rootNode 追踪 | AC-2.7 |
| R-21 | 边界 | AceFocusMoveResult CHILDTREE/EMBED_TARGET | 焦点跨子树/嵌入目标 | UIExtension 场景 | AC-2.8 |
| R-22 | 行为 | AddChild/RemoveChild | 构建虚拟节点树 | parent_ 为 WeakPtr | AC-3.1 |
| R-23 | 行为 | SetRect/GetGlobalRect | 设置/计算布局边界 | RectT<int32_t> | AC-3.2 |
| R-24 | 行为 | HitTest | 从右到左遍历命中测试 | 返回最深层命中节点 | AC-3.3 |
| R-25 | 行为 | OnAccessibilityHover | 分发悬停事件 | 更新 lastHovering_ 状态 | AC-3.4 |
| R-26 | 行为 | CanAccessibilityFocus | 通过 FocusStrategy 判断 | 虚拟节点也可聚焦 | AC-3.5 |
| R-27 | 行为 | CloneTree | 深拷贝虚拟节点树 | 完整子树递归克隆 | AC-3.6 |
| R-28 | 行为 | USE_HILOG 定义 | LogWrapper 桥接 HILOG_IMPL | domain=0xD003900, 100+ tags | AC-4.1 |
| R-29 | 行为 | IS_RELEASE_VERSION 定义 | SEC_PARAM 掩码安全字段 | 输出 "secure_field" 替代真实值 | AC-4.2 |
| R-30 | 边界 | STRIP_RELEASE_LOG 定义 | 编译期剥离 LOGD/LOGI/LOGW | 仅保留 LOGE/LOGF | AC-4.3 |
| R-31 | 行为 | ACE_INSTANCE_LOG 定义 | 日志前缀附加实例 ID | 多实例场景区分来源 | AC-4.4 |
| R-32 | 行为 | SendAppStartException 等 11 类 | HiSysEventWrite FAULT 报告 | 每类独立参数 | AC-4.5 |
| R-33 | 行为 | ANRRawReport | HiSysEventWrite SECURITY 级别 | JS stacktrace 附加 | AC-4.6 |
| R-34 | 行为 | JankFrameReport | HiSysEventWrite STATISTIC 级别 | startTime+duration+jank 参数 | AC-4.7 |
| R-35 | 行为 | ReportAccessibilityFailEvent | 报告无障碍失败 | actionName 参数 | AC-4.8 |
| R-36 | 行为 | 11 类异常映射 | 每类独立 HiSysEvent 参数 | AppStart/PageRouter/Component/Render/Js/Animation/Event/Internal/Accessibility/Form/Vsync | AC-4.9 |
| R-37 | 边界 | RESOURCE_SCHEDULE_SERVICE_ENABLE | ResSchedClient 报告 | 条件编译控制 | AC-4.10 |
| R-38 | 行为 | WatchDog::Register | 创建 JS+UI 双 ThreadWatcher | instanceId 关联 | AC-5.1 |
| R-39 | 行为 | ThreadWatcher::Check | 定期检测（3s/2s/1s） | 通过 AnrThread 任务调度 | AC-5.2 |
| R-40 | 行为 | IsThreadStuck | loopTime_/threadTag_ 增长判断 | 前后周期比较 | AC-5.3 |
| R-41 | 行为 | NORMAL→WARNING→FREEZE | 依次 Hiview/Raw/Dialog | JS stacktrace 在 FREEZE 时采集 | AC-5.4 |
| R-42 | 行为 | BuriedBomb/DefusingBomb | 入队/出队输入任务 ID | queue<uint64_t> | AC-5.5 |
| R-43 | 行为 | DetonatedBomb | 输入 >5s 触发 ANR 弹窗 | ANR_DIALOG_BLOCK_TIME 冷却 | AC-5.6 |
| R-44 | 行为 | AnrThread::PostTaskToTaskRunner | HiviewDFX::Watchdog::RunOneShotTask | 委托到 OHOS watchdog 线程 | AC-5.7 |
| R-45 | 行为 | XcollieInterface::SetTimerCount | HiviewDFX::XCollie 超时计数 | name+timeLimit+countLimit | AC-5.8 |
| R-46 | 边界 | OHOS_PLATFORM GC 信号 | SIG=60 信号处理 | pthread_sigmask+sigtimedwait | AC-5.9 |
| R-47 | 行为 | DumpLog::Print(depth, className, childSize) | 格式化输出树信息 | depth 为缩进层级 | AC-6.1 |
| R-48 | 行为 | DumpLog::AddDesc(args) | 模板化累积描述 | 支持多参数变参模板 | AC-6.2 |
| R-49 | 行为 | DumpLog::PrintJson | JSON 格式 dump | MIN_JSON_LENGTH=4 阈值 | AC-6.3 |
| R-50 | 行为 | DumpLog::OutPutByCompress | zlib 压缩 | MAX_DUMP_LENGTH=100000 | AC-6.4 |
| R-51 | 行为 | LayoutInspector::GetInspectorTreeJsonStr | 生成组件树 JSON | containerId 关联 | AC-6.5 |
| R-52 | 行为 | LayoutInspector::CreateLayoutInfo | 创建布局快照 | 支持 container/winId 两种入口 | AC-6.6 |
| R-53 | 行为 | LayoutInspector::GetSnapshotJson | 快照含 3D 捕获 | RS ComponentSnapshot | AC-6.7 |
| R-54 | 行为 | LayoutInspector::RegisterConnectCallback | IDE 连接服务器 | ConnectServerManager | AC-6.8 |
| R-55 | 行为 | AceChecker::InitPerformanceParameters | 加载 5 组阈值 | system::GetIntParameter | AC-6.9 |
| R-56 | 行为 | AceChecker::SetPerformanceCheckStatus | 启用/禁用检查+WebSocket | IDE 命令控制 | AC-6.10 |
| R-57 | 行为 | PerfInterfaces::RecordInputEvent | 记录到 PerfMonitorAdapter | 支持 type+sourceType+coordinates | AC-7.1 |
| R-58 | 行为 | PerfInterfaces::Start/End(sceneId) | 标记性能场景 | commercial 版本独立 | AC-7.2 |
| R-59 | 行为 | PerfInterfaces::SetFrameTime | 设置帧时间 | vsyncTime+duration+jank 参数 | AC-7.3 |
| R-60 | 行为 | PerfInterfaces::ReportJankFrameApp | 报告帧抖动 | jankThreshold 参数 | AC-7.4 |
| R-61 | 行为 | ResSchedDataReport | dlsym("ReportData") 异步报告 | reportDataFunc_ 函数指针 | AC-7.5 |
| R-62 | 行为 | ResScheSyncEventReport | dlsym("ReportSyncEvent") 同步报告 | reportSyncEventFunc_ 函数指针 | AC-7.6 |
| R-63 | 行为 | ResSchedReport::OnTouchEvent | 报告触摸子事件 | 速率限制 IsPerSecRateLimit | AC-7.7 |
| R-64 | 行为 | dlopen libressched_client.z.so | 动态加载资源调度库 | dlsym 获取函数指针 | AC-7.8 |
| R-65 | 边界 | CROSS_PLATFORM 定义 | 跳过 dlopen/dlsym | 跨平台无 OHOS 资源调度 | AC-7.9 |
| R-66 | 行为 | StatisticEventAdapter::ReportStatisticEvents | UIServiceMgrClientIdl 报告 | UI_SERVICE_WITH_IDL 条件编译 | AC-7.10 |
| R-67 | 行为 | ILongFrame::ReportStartEvent/EndEvent | FFRT+ResSchedDataReport 长帧 | ffrt::task_handle 调度 | AC-7.11 |
| R-68 | 行为 | HandleJsException | JsErrorObject→ErrorObject+ApplicationDataManager | name/message/stack 三字段 | AC-8.1 |
| R-69 | 行为 | NotifyUnhandledException | 通知异常观察者 | ApplicationDataManager 单例 | AC-8.2 |
| R-70 | 边界 | 无异常观察者 | KillApplicationByUid 自杀 | AppMgrClient::KillApplicationSelf | AC-8.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.13 Accessibility 桥接 | 单测+集成测试 | 注册/注销、元素查询、操作映射、事件分发 |
| VM-2 | AC-2.1~2.8 FocusStrategy | 单测 | 焦点规则评估、前向/后向遍历、滚动祖先、根类型边界 |
| VM-3 | AC-3.1~3.6 VirtualNode | 单测 | 树构建、布局、命中测试、悬停事件、聚焦判断 |
| VM-4 | AC-4.1~4.10 DFX 日志与事件 | 单测+编译检查 | hilog 桥接、安全掩码、HiSysEvent 报告 |
| VM-5 | AC-5.1~5.9 Watchdog/ANR | 单测+集成测试 | 线程卡顿检测、状态转换、ANR 弹窗、GC 信号 |
| VM-6 | AC-6.1~6.10 Dump/Inspector/Checker | 单测 | 树输出、JSON dump、快照、阈值加载 |
| VM-7 | AC-7.1~7.11 性能监控与资源调度 | 单测+集成测试 | 输入记录、场景标记、dlopen 加载、帧抖动报告 |
| VM-8 | AC-8.1~8.3 异常处理 | 集成测试 | JS 异常转换、观察者通知、自杀回退 |

## API 变更分析

N/A，框架内部适配层，无 SDK API 变更。

## 接口规格

### 接口定义

**JsAccessibilityManager::InitializeCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void JsAccessibilityManager::InitializeCallback()` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**WatchDog::Register**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void WatchDog::Register(int32_t instanceId, WeakPtr<TaskExecutor> taskExecutor, bool useUIAsJSThread)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

**ExceptionHandler::HandleJsException**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ExceptionHandler::HandleJsException(const std::string& exceptionMsg, const JsErrorObject& errorInfo)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-8.1 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** InnerApi

## 架构约束

| 关键约束 | 束束说明 | 影响 AC |
|----------|----------|---------|
| WEB_SUPPORTED 宏 | WebInteractionOperation 仅在 Web 组件场景启用 | AC-1.13 |
| CROSS_PLATFORM 宏 | ResSchedReport 跳过 OHOS dlopen/dlsym | AC-7.9 |
| OHOS_PLATFORM 宏 | WatchDog GC 信号仅 OHOS/Android 启用 | AC-5.9 |
| IS_RELEASE_VERSION | LogWrapper 安全掩码仅发布版启用 | AC-4.2 |
| RESOURCE_SCHEDULE_SERVICE_ENABLE | EventReport 资源调度事件条件编译 | AC-4.10 |
| UI_SERVICE_WITH_IDL | StatisticEventAdapter 条件编译 | AC-7.10 |

## 非性能需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | Accessibility/FocusStrategy/WatchDog 可通过 Mock 测试 | 单测 | js_accessibility_manager.h, watch_dog.h |
| 性能 | Accessibility 搜索 ≤10ms | 单测计时 | js_accessibility_manager.cpp |
| 可靠性 | ANR 弹窗冷却 ≥ANR_DIALOG_BLOCK_TIME | 集成测试 | watch_dog.cpp |
| 安全 | SEC_PARAM 掩码安全字段 | 编译检查 | log_wrapper.h |

## 多设备适配声明

无差异。所有设备类型使用相同的无障碍和 DFX 适配代码。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本 Feat 直接桥接 OHOS 无障碍服务 | AC-1.1~1.13, AC-2.1~2.8, AC-3.1~3.6 |
| 大字体 | 间接 | Accessibility 搜索需考虑大字体布局变化 | AC-1.4~1.5 |
| 深色模式 | 间接 | AccessibilityHighContrast 通过 AccessibilityConfig 观察者 | AC-1.10 |
| 多窗口/分屏 | 是 | 子树注册和窗口 ID 关联 | AC-1.12 |
| 版本升级 | 是 | HiSysEvent 参数版本需随 OHOS 版本更新 | AC-4.5~4.9 |
| 生态兼容 | 是 | CROSS_PLATFORM 控制 ArkUI-X 跨平台 | AC-7.9 |

## 行为场景（可选，Gherkin）

> 本特性为 L2+（标准复杂度），使用 Gherkin 场景描述核心行为。

```gherkin
Feature: 无障碍与DFX适配
  作为 ACE 引擎开发者
  我想要 框架内部无障碍和 DFX 能力通过 OHOS 平台服务完成桥接
  以便 用户和开发者能通过 OHOS 无障碍和维测体系使用 ACE 引擎

  Scenario: Accessibility 注册并响应无障碍查询
    Given 一个 AceContainer 已初始化
    When JsAccessibilityManager::InitializeCallback 注册到 AccessibilitySystemAbilityClient
    And OHOS 无障碍服务发送 SearchElementInfoByAccessibilityId 请求
    Then JsInteractionOperation 查询 NG FrameNode 树
    And 返回 AccessibilityElementInfo 列表到 OHOS 无障碍服务

  Scenario: FocusStrategy 前向焦点移动
    Given 一个 NG FrameNode 树包含可聚焦节点 A→B→C
    When FocusMoveSearch 从节点 A 搜索下一个可聚焦节点
    Then AccessibilityFocusStrategy::FindNextReadableNode 查找节点 B
    And 返回 AceFocusMoveResult=FIND_SUCCESS

  Scenario: WatchDog 检测线程卡顿并弹窗
    Given WatchDog 已注册 JS ThreadWatcher(instanceId=1)
    And JS 线程 loopTime 连续 3 个周期无增长
    When ThreadWatcher::Check 检测到 IsThreadStuck=true
    Then 状态转换 NORMAL→WARNING→FREEZE
    And EventReport::ANRRawReport(FREEZE) 报告到 HiviewDFX
    And DetonatedBomb 检查输入超时 >5s 触发 ANR 弹窗

  Scenario: ExceptionHandler 处理 JS 未捕获异常
    Given JS 引擎抛出未捕获异常(name="TypeError", message="xxx", stack="...")
    When ExceptionHandler::HandleJsException 被调用
    Then ApplicationDataManager::NotifyUnhandledException 通知观察者
    And 若无观察者处理则 KillApplicationByUid 终止进程

  Scenario: ResSchedReport 动态加载资源调度库
    Given libressched_client.z.so 存在于系统路径
    When ResSchedReport 首次调用 ResSchedDataReport
    Then dlopen("libressched_client.z.so") 加载库
    And dlsym("ReportData") 获取函数指针
    And 通过函数指针异步报告资源调度数据
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "JsAccessibilityManager 与 OHOS AccessibilitySystemAbilityClient 的注册/查询/操作桥接机制"
  - repo: "openharmony/ace_engine"
    query: "AccessibilityFocusStrategy 焦点移动规则和 FocusRulesCheckNode 节点适配器层次"
  - repo: "openharmony/ace_engine"
    query: "WatchDog+AnrThread+XcollieInterface ANR 检测和 GC 信号处理流程"
  - repo: "openharmony/ace_engine"
    query: "LogWrapper hilog 桥接和 EventReport HiSysEvent 11 类异常映射"
  - repo: "openharmony/ace_engine"
    query: "PerfInterfaces PerfMonitorAdapter 桥接和 ResSchedReport dlopen/dlsym 资源调度客户端"
```

**关键文档：** ace_engine `adapter/ohos/osal/` + `adapter/ohos/capability/` + `frameworks/base/log/` + `frameworks/core/accessibility/` + `frameworks/core/common/`
