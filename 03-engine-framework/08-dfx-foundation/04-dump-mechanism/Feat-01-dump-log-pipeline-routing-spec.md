# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DumpLog核心引擎与Pipeline命令路由 |
| 特性编号 | Func-03-08-04-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 ArkUI ace_engine 的 dump 调试输出核心基础设施：DumpLog 单例格式化输出引擎（Print/AddDesc/Append/OutPut 系列）、大体量溢出文件落地（arkui.dump）与 zlib 压缩、AceContainer::Dump 入口重入保护与命令链分发、-basicinfo 基础环境信息、PipelineBase::Dump 一级命令路由（-memory/-jscrash/-hiviewreport/-frontend）、PipelineContext::OnDumpInfo 二级命令分发（30+ 命令）与常量信息输出、DumpPipelineInfo 帧任务信息、DumpRecorder 帧录制与差异比对。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DumpLog 单例格式化输出引擎规格 | dump_log.h:32-189, dump_log.cpp:37-218 定义 Print/AddDesc/Append/FormatDumpInfo/GetPrefix/PrintEndDumpInfoNG 等格式化输出接口 |
| ADDED | DumpLog 大体量溢出与压缩输出规格 | dump_log.cpp:122-151 OutPutBySize 溢出到 arkui.dump（MAX_DUMP_LENGTH=100000），dump_log.cpp:271-293 OutPutByCompress zlib 压缩 |
| ADDED | DumpFileBuf/DumpFile 流适配内部类规格 | dump_log.h:36-73 基于 FILE*/streambuf 的 C 文件流封装 |
| ADDED | AceContainer::Dump 入口分发与重入保护规格 | ace_container.cpp:2418-2591 Dump/DumpCommon/DumpInfo 命令链，isDumping_ 原子标志 |
| ADDED | -basicinfo 基础环境信息输出规格 | ace_container.cpp:2554-2588 输出 18 项环境信息 |
| ADDED | PipelineBase::Dump 一级命令路由规格 | pipeline_base.cpp:571-603 -memory/-jscrash/-hiviewreport/-frontend 命令分发 |
| ADDED | PipelineContext::OnDumpInfo 二级命令分发规格 | pipeline_context.cpp:4339-4593 常量信息输出 + 30+ 命令分发 |
| ADDED | DumpPipelineInfo 帧任务信息输出规格 | pipeline_context.cpp:4654-4678 输出刷新率/vsync/帧任务调度信息 |
| ADDED | DumpRecorder 帧录制与差异比对规格 | dump_recorder.h:25-64, dump_recorder.cpp:37-197 Start/Stop/Record/Diff/Compare 生命周期与 JSON 差异比对 |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/04-dump-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/base/log/dump_log.h`（189 行）—— DumpLog 单例声明、DumpFileBuf/DumpFile 内部类、模板方法
  - `frameworks/base/log/dump_log.cpp`（294 行）—— 格式化输出、溢出、压缩实现
  - `frameworks/base/log/dump_recorder.h`（66 行）—— DumpRecorder 帧录制单例声明
  - `frameworks/base/log/dump_recorder.cpp`（198 行）—— 录制/差异/输出实现
  - `adapter/ohos/entrance/ace_container.cpp:2418-2591` —— AceContainer::Dump 入口分发
  - `frameworks/core/pipeline/pipeline_base.cpp:571-603` —— PipelineBase::Dump 一级路由
  - `frameworks/core/pipeline_ng/pipeline_context.cpp:4339-4593` —— OnDumpInfo 二级分发
  - `frameworks/core/pipeline_ng/pipeline_context.cpp:4654-4678` —— DumpPipelineInfo

## 用户故事

### US-1: DumpLog 单例格式化输出引擎

- As a 框架调试信息消费者
- I want DumpLog 单例提供带缩进层级的树形格式化输出能力
- So that dump 结果以可读的树状结构展示组件树信息

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DumpLog::Print(depth, className, childSize) 被调用 THEN 先写 `depth + 1` 层 `"  "` 缩进，再写 `"|-> " + className + " childSize:" + childSize + "\n"`，随后为每条 description 写 `depth` 层缩进 + （childSize==0 时 `"      "`，否则 `"    | "`）+ desc 内容。来源：`dump_log.cpp:37-68` | 正常 |
| AC-1.2 | WHEN DumpLog::Print(depth, content) 被调用 THEN 写 `depth` 层 `" "` 单空格缩进后写 content + std::endl。Print(content) 内部转发为 Print(0, content)。来源：`dump_log.cpp:70-82` | 正常 |
| AC-1.3 | WHEN DumpLog::AddDesc(Args&&... args) 被调用 THEN 通过 BuildDesc 模板将多个参数用 `" "` 连接，末尾追加 `"\n"`，整体 push 到 description_ 向量。来源：`dump_log.h:147-166` | 正常 |
| AC-1.4 | WHEN DumpLog::Print(depth, className, childSize) 执行完毕 THEN 调用 ostream_->flush() 并执行 description_.clear() + shrink_to_fit() 释放描述缓冲区。来源：`dump_log.cpp:65-67` | 正常 |

### US-2: DumpLog 大体量溢出与压缩输出

- As a 调试工具开发者
- I want 当 dump 结果超过 MAX_DUMP_LENGTH 时自动溢出到文件，并支持 zlib 压缩输出
- So that 大型 UI 树的 dump 结果不会截断，且可通过压缩减少传输开销

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN DumpLog::OutPutBySize() 检测到 `result_.size() + 1 > MAX_DUMP_LENGTH(100000)` 或 `isUIExt_ == true` THEN 创建 `DataFileDirPath + "/arkui.dump"` 的 ofstream，调用 SetDumpFile 替换输出流，再写入 result_ 内容。来源：`dump_log.cpp:122-151` | 正常 |
| AC-2.2 | WHEN OutPutBySize() 中 ofstream 创建失败 THEN 将 result_ 替换为 `"Dump output failed,please try again"` 写入原 ostream_，CHECK_NULL_RETURN 返回 false。来源：`dump_log.cpp:134-142` | 异常 |
| AC-2.3 | WHEN DumpLog::OutPutByCompress() 被调用且定义了 OHOS_PLATFORM THEN 调用 CompressString(result_.c_str(), result_.size(), out_str, COMPRESS_VERSION=9)，CHUNK=16384，压缩成功则写入压缩数据，失败则写入原始数据。来源：`dump_log.cpp:271-293,28,30` | 正常 |

### US-3: AceContainer::Dump 入口分发与重入保护

- As a 系统调试工具（如 hidumper）
- I want AceContainer::Dump 作为入口，按命令链依次尝试各 dump 处理器
- So that 每条命令能被正确的处理器处理，且并发 dump 请求被安全拒绝

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN AceContainer::DumpCommon 执行时 THEN 首先调用 isDumping_.test_and_set()，若返回 true（已有 dump 运行中）则输出 LOGW 并返回 false。dump 结束后调用 isDumping_.clear()。来源：`ace_container.cpp:2430-2433,2457` | 边界 |
| AC-3.2 | WHEN AceContainer::DumpInfo(params) 被调用 THEN 按顺序尝试：aceView_->Dump(params) → OnDumpInfo(params) → DumpRSNodeByStringID(params) → DumpExistDarkRes(params) → pipelineContext_->Dump(params)，首个返回 true 的处理器终止链。来源：`ace_container.cpp:2472-2491` | 正常 |
| AC-3.3 | WHEN AceContainer::DumpCommon 中 DumpInfo 返回 false（result==false）THEN 调用 DumpLog::ShowDumpHelp(info) 追加帮助信息到输出。来源：`ace_container.cpp:2454-2456` | 异常 |

### US-4: AceContainer -basicinfo 基础环境信息输出

- As a 运维人员
- I want 通过 `-basicinfo` 命令获取当前容器的运行环境信息
- So that 快速诊断应用窗口配置、分辨率、颜色模式等基础状态

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN params[0] == "-basicinfo" THEN 输出 13 项无 pipelineContext_ 依赖的信息：InstanceId、FrontendType、NewPipeline、WindowName、WindowState、Language、RTL、ColorMode、DeviceOrientation、Resolution（width*height）、ApiVersion、ReleaseType、DeviceType。来源：`ace_container.cpp:2554-2587` | 正常 |
| AC-4.2 | WHEN pipelineContext_ 非空 THEN 额外输出 5 项依赖 pipeline 的信息：AppBgColor（ColorToString）、Density、ViewScale、DisplayWindowRect（ToString）、vsyncID（GetFrameCount）。来源：`ace_container.cpp:2577-2584` | 正常 |
| AC-4.3 | WHEN AceContainer::OnDumpInfo 处理 -basicinfo 并输出完毕 THEN 返回 true，终止命令链。来源：`ace_container.cpp:2588-2590` | 正常 |

### US-5: PipelineBase::Dump 一级命令路由

- As a 框架调试开发者
- I want PipelineBase::Dump 对 -memory/-jscrash/-hiviewreport/-frontend 命令直接处理，其余命令转发到 OnDumpInfo
- So that 引擎级调试命令在基类层处理，组件级命令由子类 PipelineContext 处理

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN params[0] == "-memory" THEN 在 ACE_DEBUG 构建下调用 MemoryMonitor::GetInstance().Dump()，随后调用 DumpUIExt()，返回 true。来源：`pipeline_base.cpp:577-582` | 正常 |
| AC-5.2 | WHEN params[0] == "-hiviewreport" 且 params.size() >= 3 THEN 打印 EventType/error type 并构造 EventInfo（eventType=params[1], errorType=StringToInt(params[2])），调用 EventReport::SendEvent。来源：`pipeline_base.cpp:590-594` | 正常 |
| AC-5.3 | WHEN params[0] 不匹配 -memory/-jscrash/-hiviewreport/-frontend THEN 调用 OnDumpInfo(params) 转发给子类处理。当 params 为空时返回 false。来源：`pipeline_base.cpp:573-575,602` | 正常 |

### US-6: PipelineContext::OnDumpInfo 命令分发与常量信息

- As a 框架调试开发者
- I want OnDumpInfo 在执行任何命令前始终输出引擎运行常量信息，并按 30+ 命令分发
- So that 每次 dump 都能附带引擎状态快照

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN PipelineContext::OnDumpInfo 被调用 THEN 无条件输出 5 项常量信息：LastRequestVsyncTime（依赖 window_）、transactionFlags（依赖 ENABLE_ROSEN_BACKEND + rsUIDirector）、last vsyncId（GetFrameCount）、finishCount（GetUnexecutedFinishCount）、UINodeCount（UINode::Count()）。来源：`pipeline_context.cpp:4347-4359` | 正常 |
| AC-6.2 | WHEN params[0] == "-default" THEN 若 params[1]=="-all" 则临时 SetDumpAllNodes(true) 并遍历 GetAllRoots() 之 DumpTree，结束后恢复原标志；否则对 rootNode_ 调用 DumpTree(depth)。最终调用 OutPutDefault()。来源：`pipeline_context.cpp:4449-4460` | 正常 |
| AC-6.3 | WHEN params[0] == "-element" THEN 调用 DumpElement(params, hasJson)；当 params[0] == "-inspector" THEN 调用 DumpInspector(params, hasJson)。hasJson 由 params.back()=="-json" 判定。来源：`pipeline_context.cpp:4341,4360-4361,4384-4385` | 正常 |
| AC-6.4 | WHEN params[0] == "-jsdump" THEN 取 params[1:] 作为 jsParams，若 params[1]=="-h" 则仅对 GetLastPage() 的 PagePattern 调用 FireDumpListener，否则遍历 stageNode 所有子页面 PagePattern 调用 FireDumpListener。来源：`pipeline_context.cpp:4393-4417` | 正常 |

### US-7: DumpPipelineInfo 帧任务信息输出

- As a 性能分析工程师
- I want 通过 `-pipeline` 命令获取刷新率、vsync 时间和帧任务调度详情
- So that 分析帧渲染管线中的布局和绘制任务执行情况

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN PipelineContext::DumpPipelineInfo 被调用且 window_ 非空 THEN 输出 DisplayRefreshRate（GetRefreshRate）、LastRequestVsyncTime（GetLastRequestVsyncTime）、NowTime（GetSysTimestamp）。来源：`pipeline_context.cpp:4656-4661` | 正常 |
| AC-7.2 | WHEN dumpFrameInfos_ 非空 THEN 为每条 FrameInfo 输出 Task 时间信息（GetTimeInfo）、LayoutTask 列表（layoutInfos_ 各项 ToString）和 RenderTask 列表（renderInfos_ 各项 ToString），以 `"==================================FrameTask=================================="` 分隔。来源：`pipeline_context.cpp:4662-4677` | 正常 |

### US-8: DumpRecorder 帧录制与差异比对

- As a UI 回归测试开发者
- I want 通过 `-start/-end` 命令录制 UI 树帧序列并自动执行差异比对
- So that 捕获 UI 树随时间的变化用于回归分析

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN OnDumpRecorderStart 以 params[1] 提供录制时长 THEN recordTime = min(inputTime, MAX_RECORD_SECOND=15)；inputTime<=0 时使用 DEFAULT_RECORD_SECOND=5。创建 dumpFunc lambda，每帧执行 DumpTreeJsonForDiff + DumpRecorder::Record。来源：`pipeline_context.cpp:4595-4621,149-151` | 正常 |
| AC-8.2 | WHEN DumpRecorder::Start(func) 被调用且 frameDumpFunc_ 已存在 THEN 先调用 Stop() 停止当前录制，再 Init() 初始化 recordTree_。来源：`dump_recorder.cpp:52-59` | 正常 |
| AC-8.3 | WHEN DumpRecorder::Record 第二次及之后被调用 THEN 在 BACKGROUND 线程异步执行 Diff(timestamp)，Diff 将当前帧与首帧进行 Compare 差异比对，结果追加到 recordTree_ 的 infos 数组。来源：`dump_recorder.cpp:80-130` | 正常 |
| AC-8.4 | WHEN DumpRecorder::Stop 被调用 THEN 在 BACKGROUND 线程执行 StopInner，将 recordTree_ 序列化输出到 `DataFileDirPath + "/arkui_dump.rec"` 文件并 Clear()。当累计 fileSize_ > MAX_FILE_SIZE(104857600) 时自动触发 Stop()。来源：`dump_recorder.cpp:61-78,126-128,27,191-197` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|---------|------|
| AC-1.1 | R-1 / R-2 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.2 | R-3 | TASK-01 | 代码评审 | 代码审查 |
| AC-1.3 | R-4 | TASK-01 | 代码评审 + 模板展开验证 | 代码审查 |
| AC-1.4 | R-1 | TASK-01 | 代码评审 | 代码审查 |
| AC-2.1 | R-5 / R-6 | TASK-01 | 代码评审 + 文件输出验证 | 代码审查 |
| AC-2.2 | R-6 | TASK-01 | 代码评审 | 代码审查 |
| AC-2.3 | R-7 / R-8 | TASK-01 | 代码评审 | 代码审查 |
| AC-3.1 | R-9 | TASK-01 | 代码评审 | 代码审查 |
| AC-3.2 | R-10 | TASK-01 | 代码评审 | 代码审查 |
| AC-3.3 | R-11 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.1 | R-12 | TASK-01 | 代码评审 + hidumper 输出验证 | 代码审查 |
| AC-4.2 | R-12 | TASK-01 | 代码评审 | 代码审查 |
| AC-4.3 | R-10 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.1 | R-13 | TASK-01 | 代码评审 + ACE_DEBUG 变体验证 | 代码审查 |
| AC-5.2 | R-14 | TASK-01 | 代码评审 | 代码审查 |
| AC-5.3 | R-15 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.1 | R-16 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.2 | R-17 / R-18 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.3 | R-19 | TASK-01 | 代码评审 | 代码审查 |
| AC-6.4 | R-20 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.1 | R-21 | TASK-01 | 代码评审 | 代码审查 |
| AC-7.2 | R-22 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.1 | R-23 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.2 | R-24 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.3 | R-25 | TASK-01 | 代码评审 | 代码审查 |
| AC-8.4 | R-26 / R-27 | TASK-01 | 代码评审 + 文件输出验证 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | DumpLog::Print(depth, className, childSize) 调用 | 写入缩进树形格式，flush 后清空 description_ | ostream_ 为 null 或 !good() 时直接返回。 | AC-1.1 / AC-1.4 |
| R-2 | 行为 | Print 树形格式输出 | 描述行前缀：childSize==0 用 `"      "`（6 空格），childSize>0 用 `"    | "` | 缩进单位为 2 字符 `"  "`。 | AC-1.1 |
| R-3 | 行为 | DumpLog::Print(depth, content) 调用 | 写 depth 层 `" "` 空格 + content + endl | Print(content) 等价于 Print(0, content)。 | AC-1.2 |
| R-4 | 行为 | AddDesc 模板调用 | 单参数版追加 `value + "\n"`；多参数版以 `" "` 连接各参数后追加 `"\n"` | 结果 push 到 description_ 向量，等待 Print/Append 消费。 | AC-1.3 |
| R-5 | 行为 | SetDumpAllNodes(true) / IsDumpAllNodes() | 设置/查询 isDumpAllNodes_ 标志，控制 DumpTree 是否包含不可见节点 | 默认 false，-default -all 时临时置 true。 | AC-6.2 |
| R-6 | 异常 | OutPutBySize 检测溢出 | result_.size()+1 > MAX_DUMP_LENGTH(100000) 或 isUIExt_==true 时溢出到 arkui.dump 文件 | ofstream 创建失败时输出错误提示并返回 false。 | AC-2.1 / AC-2.2 |
| R-7 | 行为 | OutPutByCompress 调用 | OHOS_PLATFORM 下用 CompressString(level=9, CHUNK=16384) zlib 压缩；非 OHOS_PLATFORM 或压缩失败时写原始数据 | CompressString 使用 deflateInit/deflate/deflateEnd。 | AC-2.3 |
| R-8 | 行为 | CompressString 内部 | 以 CHUNK=16384 为块循环 deflate 直到 Z_FINISH，成功返回 Z_OK | 返回 Z_STREAM_ERROR 时 OutPutByCompress 写原始数据。 | AC-2.3 |
| R-9 | 边界 | isDumping_ 重入保护 | test_and_set() 返回 true 时拒绝并发 dump | dump 完成后 clear()。 | AC-3.1 |
| R-10 | 行为 | AceContainer::DumpInfo 命令链 | 依次尝试 aceView_->Dump → OnDumpInfo → DumpRSNodeByStringID → DumpExistDarkRes → pipelineContext_->Dump | 首个 true 终止链；全部 false 则 DumpCommon 追加 ShowDumpHelp。 | AC-3.2 / AC-4.3 |
| R-11 | 行为 | DumpCommon 输出后处理 | 将 ostringstream 内容移入 info 向量，调用 DumpLog::Reset() | result==false 时追加 ShowDumpHelp。 | AC-3.3 |
| R-12 | 行为 | -basicinfo 输出 | 输出 13 项无依赖信息 + 5 项 pipelineContext_ 依赖信息（共 18 项） | pipelineContext_ 为空时仅输出 13 项。 | AC-4.1 / AC-4.2 |
| R-13 | 行为 | -memory 命令 | ACE_DEBUG 构建调用 MemoryMonitor::Dump()，然后 DumpUIExt() | 非 ACE_DEBUG 构建仅 DumpUIExt()。 | AC-5.1 |
| R-14 | 行为 | -hiviewreport 命令 | 需 params.size()>=3，构造 EventInfo 并 SendEvent | 参数不足时不匹配，继续路由。 | AC-5.2 |
| R-15 | 边界 | PipelineBase::Dump 空参数 | params.empty() 时返回 false | 非空但无匹配命令时转发 OnDumpInfo。 | AC-5.3 |
| R-16 | 行为 | OnDumpInfo 常量信息 | 无条件输出 LastRequestVsyncTime/transactionFlags/vsyncId/finishCount/UINodeCount | LastRequestVsyncTime 和 transactionFlags 依赖 window_ 和 ENABLE_ROSEN_BACKEND。 | AC-6.1 |
| R-17 | 行为 | -default 命令 | 无 -all 时 DumpTree(rootNode_, depth)；有 -all 时遍历 GetAllRoots 并临时 SetDumpAllNodes(true) | 最终调用 OutPutDefault()。 | AC-6.2 |
| R-18 | 行为 | DumpAllNodes 标志恢复 | -default -all 执行前保存 isAll，执行后恢复 | 保证临时标志不泄漏到后续 dump。 | AC-6.2 |
| R-19 | 行为 | -element/-inspector 命令 | 分别调用 DumpElement/DumpInspector，传入 hasJson 标志 | hasJson = (params.back()=="-json")。 | AC-6.3 |
| R-20 | 行为 | -jsdump 命令 | params[1]=="-h" 时单页面 FireDumpListener，否则遍历全部页面 | 依赖 stageManager_ 和 PagePattern。 | AC-6.4 |
| R-21 | 行为 | DumpPipelineInfo 窗口信息 | 输出 DisplayRefreshRate/LastRequestVsyncTime/NowTime | 依赖 window_ 非空。 | AC-7.1 |
| R-22 | 行为 | DumpPipelineInfo 帧任务 | 遍历 dumpFrameInfos_ 输出 LayoutTask/RenderTask | dumpFrameInfos_ 为空时仅输出窗口信息。 | AC-7.2 |
| R-23 | 行为 | -start 录制参数解析 | recordTime = min(inputTime, 15)；默认 5 秒 | recordTime 以 SECOND_TO_MILLISEC(1000) 转毫秒。 | AC-8.1 |
| R-24 | 行为 | DumpRecorder::Start | 若已有录制则先 Stop，然后 Init recordTree_ | Init 创建空 JSON 树并 PutRef("infos", array)。 | AC-8.2 |
| R-25 | 行为 | DumpRecorder::Record 后续帧 | 异步在 BACKGROUND 线程 Diff，与首帧 Compare 差异比对 | 首帧直接全量记录到 infos。 | AC-8.3 |
| R-26 | 行为 | DumpRecorder::Stop | BACKGROUND 线程 StopInner 输出 recordTree_ 到 arkui_dump.rec 并 Clear | frameDumpFunc_ 置 null。 | AC-8.4 |
| R-27 | 边界 | DumpRecorder 文件大小限制 | fileSize_ > MAX_FILE_SIZE(100*1024*1024) 时自动 Stop | MAX_FILE_SIZE = 104857600 字节。 | AC-8.4 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.4 / R-1..R-4 | 代码评审 | dump_log.h:105-166, dump_log.cpp:37-82（Print/AddDesc/Append 格式化输出） |
| VM-2 | AC-2.1..2.3 / R-6..R-8 | 代码评审 + 文件输出验证 | dump_log.cpp:122-151,271-293（OutPutBySize 溢出 / OutPutByCompress） |
| VM-3 | AC-3.1..3.3 / R-9..R-11 | 代码评审 | ace_container.cpp:2428-2459,2472-2491（DumpCommon 重入保护 / DumpInfo 命令链） |
| VM-4 | AC-4.1..4.3 / R-12 | 代码评审 + hidumper 输出验证 | ace_container.cpp:2552-2591（OnDumpInfo -basicinfo 18 项信息） |
| VM-5 | AC-5.1..5.3 / R-13..R-15 | 代码评审 + ACE_DEBUG 变体验证 | pipeline_base.cpp:571-603（PipelineBase::Dump 一级路由） |
| VM-6 | AC-6.1..6.4 / R-16..R-20 | 代码评审 | pipeline_context.cpp:4339-4593（OnDumpInfo 常量信息 + 命令分发） |
| VM-7 | AC-7.1..7.2 / R-21..R-22 | 代码评审 | pipeline_context.cpp:4654-4678（DumpPipelineInfo） |
| VM-8 | AC-8.1..8.4 / R-23..R-27 | 代码评审 + 文件输出验证 | dump_recorder.cpp:52-197, pipeline_context.cpp:4595-4621（录制生命周期与差异比对） |

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
|---------|---------|--------|
| DumpLog 单例 | Singleton<DumpLog>，通过 GetInstance() 访问，ACE_DISALLOW_MOVE 禁止移动语义 | AC-1.1 / AC-1.4 |
| 三层命令路由 | AceContainer::Dump→PipelineBase::Dump→PipelineContext::OnDumpInfo，严格自上而下，不允许反向依赖 | AC-3.1 / AC-3.2 / AC-5.1 / AC-6.1 |
| 命令链固定顺序 | DumpInfo 按 aceView→OnDumpInfo→DumpRSNodeByStringID→DumpExistDarkRes→pipelineContext_->Dump 执行，首个 true 终止链 | AC-3.2 |
| ostream_ 生命周期 | DumpLog::ostream_ 为 unique_ptr<std::ostream>，DumpCommon 使用 ostringstream，结束后必须 Reset() | AC-3.3 |
| DumpRecorder 异步执行 | Singleton 单例，Diff/StopInner 在 BACKGROUND 线程，避免阻塞 UI 线程 | AC-8.2 / AC-8.3 |
| 帧录制时长闭环 | TriggerFrameDumpFuncIfExist 在 vsync 中调用，frameDumpFunc_ 返回 false 则自动 Stop() | AC-8.1 / AC-8.4 |

## 非性能需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | OnDumpInfo 常量信息 O(1)；DumpTree O(n) | 代码评审 | 代码审查 |
| 内存安全 | description_ clear+shrink_to_fit；result_ clear+swap | 代码评审 | 代码审查 |
| 可观测 | 每次 dump 输出 5 项引擎运行态快照 | 代码评审 | 代码审查 |
| 并发安全 | isDumping_ atomic_flag；BACKGROUND 线程异步 | 代码评审 | 代码审查 |
| 鲁棒性 | 空 pointer 输出提示不崩溃 | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 框架内部 dump 调试，不涉及无障碍语义 | — |
| 大字体 | 否 | dump 输出不受字体缩放影响 | — |
| 深色模式 | 否 | dump 输出不含颜色模式语义 | — |
| 多窗口 | 是 | AceContainer::Dump 按 containerId 区分窗口 | OnDumpInfo |
| 多用户 | 否 | 框架内部能力，不涉及多用户 | — |
| 版本升级 | 否 | 全部为已有实现补录 | — |
| 生态兼容 | 否 | 无 Public/System API 变更 | — |

## Spec 自审清单

- [x] 所有 H2 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」中可被引用
- [x] 规则定义使用 R-N 编号，类型标签齐全（行为/边界/异常/恢复）
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 为框架内部接口
- [x] 兼容性声明覆盖编译配置/命令扩展/跨平台/输出文件四个维度
- [x] 无 TODO / TBD / 待定 占位符

## context-references

```yaml
references:
  - path: frameworks/base/log/dump_log.h
    lines: 32-34
    description: DumpLog 单例继承 Singleton + DECLARE_SINGLETON
  - path: frameworks/base/log/dump_log.h
    lines: 36-63
    description: DumpFileBuf streambuf 子类，fwrite/fclose 封装
  - path: frameworks/base/log/dump_log.h
    lines: 65-73
    description: DumpFile ostream 子类，持有 DumpFileBuf
  - path: frameworks/base/log/dump_log.h
    lines: 75-83
    description: SetDumpFile 重载 DumpFile* 与 unique_ptr<ostream>
  - path: frameworks/base/log/dump_log.h
    lines: 85-98
    description: SetUIExtFlag / SetDumpAllNodes / IsDumpAllNodes
  - path: frameworks/base/log/dump_log.h
    lines: 100-119
    description: GetDumpFile / Print 声明 / Append / Reset / PrintJson / PrintEndDumpInfoNG / GetPrefix / FormatDumpInfo / Append(string)
  - path: frameworks/base/log/dump_log.h
    lines: 121-166
    description: GetDepth/SetDepth + AddDesc 模板族 + BuildDesc 模板族
  - path: frameworks/base/log/dump_log.h
    lines: 168
    description: ShowDumpHelp 静态声明
  - path: frameworks/base/log/dump_log.h
    lines: 170-175
    description: MAX_DUMP_LENGTH=100000 / MIN_JSON_LENGTH=4 / CompressString / OutPutByCompress
  - path: frameworks/base/log/dump_log.h
    lines: 177-184
    description: description_ / ostream_ / result_ / isUIExt_ / isDumpAllNodes_ / depth_ 私有成员
  - path: frameworks/base/log/dump_log.cpp
    lines: 37-68
    description: Print(depth, className, childSize) 格式化输出实现
  - path: frameworks/base/log/dump_log.cpp
    lines: 70-82
    description: Print(content) / Print(depth, content) 实现
  - path: frameworks/base/log/dump_log.cpp
    lines: 89-96
    description: ShowDumpHelp -element/-render/-inspector/-frontend/-navigation 5 条帮助
  - path: frameworks/base/log/dump_log.cpp
    lines: 98-120
    description: Append(depth, className, childSize) 结果字符串积累
  - path: frameworks/base/log/dump_log.cpp
    lines: 122-151
    description: OutPutBySize 溢出到 arkui.dump, MAX_DUMP_LENGTH=100000
  - path: frameworks/base/log/dump_log.cpp
    lines: 153-166
    description: OutPutDefault 默认输出 + flush
  - path: frameworks/base/log/dump_log.cpp
    lines: 168-189
    description: PrintJson / PrintEndDumpInfoNG JSON 闭合括号
  - path: frameworks/base/log/dump_log.cpp
    lines: 191-218
    description: GetPrefix / FormatDumpInfo JSON 前缀与格式化
  - path: frameworks/base/log/dump_log.cpp
    lines: 220-268
    description: CompressString zlib deflate, CHUNK=16384, COMPRESS_VERSION=9
  - path: frameworks/base/log/dump_log.cpp
    lines: 271-293
    description: OutPutByCompress 压缩输出 + 失败 fallback
  - path: frameworks/base/log/dump_recorder.h
    lines: 25-64
    description: DumpRecorder 单例声明 Start/Stop/Record/Diff/Compare/CompareDumpParam/Output
  - path: frameworks/base/log/dump_recorder.cpp
    lines: 27-30
    description: MAX_FILE_SIZE=104857600 / REC_FILE_NAME="/arkui_dump.rec" / SKIP_COMPARE_PARAMS
  - path: frameworks/base/log/dump_recorder.cpp
    lines: 37-50
    description: Init/Clear recordTree_ JSON 树初始化
  - path: frameworks/base/log/dump_recorder.cpp
    lines: 52-78
    description: Start/Stop/StopInner 录制生命周期
  - path: frameworks/base/log/dump_recorder.cpp
    lines: 80-130
    description: Record/Diff 首帧全量 + 后续帧异步差异比对
  - path: frameworks/base/log/dump_recorder.cpp
    lines: 132-189
    description: CompareDumpParam/Compare JSON 节点递归比对
  - path: frameworks/base/log/dump_recorder.cpp
    lines: 191-197
    description: Output 输出到 arkui_dump.rec 文件
  - path: adapter/ohos/entrance/ace_container.cpp
    lines: 2418-2426
    description: Dump 入口 动态 UI 内容分发
  - path: adapter/ohos/entrance/ace_container.cpp
    lines: 2428-2459
    description: DumpCommon isDumping_ 保护 + ostringstream + bundleName/moduleName + DumpInfo + Reset
  - path: adapter/ohos/entrance/ace_container.cpp
    lines: 2472-2491
    description: DumpInfo 5 步命令链分发
  - path: adapter/ohos/entrance/ace_container.cpp
    lines: 2552-2591
    description: OnDumpInfo -basicinfo 18 项基础信息
  - path: frameworks/core/pipeline/pipeline_base.cpp
    lines: 571-603
    description: PipelineBase::Dump -memory/-jscrash/-hiviewreport/-frontend 路由 + OnDumpInfo 转发
  - path: frameworks/core/pipeline_ng/pipeline_context.cpp
    lines: 149-151
    description: MAX_RECORD_SECOND=15 / DEFAULT_RECORD_SECOND=5 / SECOND_TO_MILLISEC=1000
  - path: frameworks/core/pipeline_ng/pipeline_context.cpp
    lines: 4339-4359
    description: OnDumpInfo 常量信息 LastRequestVsyncTime/transactionFlags/vsyncId/finishCount/UINodeCount
  - path: frameworks/core/pipeline_ng/pipeline_context.cpp
    lines: 4360-4593
    description: OnDumpInfo 命令分发 30+ 命令分支
  - path: frameworks/core/pipeline_ng/pipeline_context.cpp
    lines: 4595-4621
    description: OnDumpRecorderStart 录制时长解析 + dumpFunc lambda
  - path: frameworks/core/pipeline_ng/pipeline_context.cpp
    lines: 4623-4630
    description: TriggerFrameDumpFuncIfExist 每帧驱动 + false 自动 Stop
  - path: frameworks/core/pipeline_ng/pipeline_context.cpp
    lines: 4654-4678
    description: DumpPipelineInfo 刷新率/vsync/帧任务
```
