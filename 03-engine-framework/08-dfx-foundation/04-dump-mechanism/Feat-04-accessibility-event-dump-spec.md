# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 可访问性Dump与事件Dump |
| 特性编号 | Func-03-08-04-Feat-04 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 ArkUI ace_engine 中可访问性（Accessibility）Dump 与事件（Event）Dump 两类 hidumper 调试能力。可访问性侧覆盖 DumpMode 模式分发（23 种模式）、DumpInfoArgument 参数结构、AccessibilityHidumper 静态参数解析、JsAccessibilityManager NG 无障碍树 Dump（文本/JSON/简化三模式）、第三方无障碍 Dump。事件侧覆盖 EventManager 事件树 Dump（含 count 限制）、触摸点历史 Dump、事件快照数据结构（FrameNodeSnapshot / TouchPointSnapshot / AxisSnapshot / SmartGestureExecutionSnapshot / EventTree / EventTreeRecord / EventTouchInfo / EventTouchInfoRecord）。不涉及 Trace 基础设施（Feat-01）、帧调度 Jank 报告（Feat-02）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | AccessibilityHidumper 参数解析规格 | accessibility_hidumper.h:37-60 定义 DumpMode 枚举（23 种模式）；:62-91 定义 DumpInfoArgument 参数结构；:99-115 定义 AccessibilityHidumper 静态方法 DumpProcessInjectActionParameters / DumpProcessExecuteActionParameters / DumpProcessCustomActionParameters |
| ADDED | OSAL 无障碍 Dump 辅助规格 | accessibility_hidumper_osal.h:67-77 定义 AccessibilityManagerHidumper，提供 ConvertAccessibilityAction / ConvertActionTypeToString / DumpCustomActionTest |
| ADDED | NG 无障碍树 Dump 规格定义 | js_accessibility_manager.h:584 声明 OnDumpInfoNG；:823-832 声明 DumpTreeNG 系列（useWindowId 重载 / 递归重载 / SafeArea / CommonInfo / Simplify / AccessibilityNode）；:965 声明 DumpTreeNodeInfoInJson；:587 声明 DumpTree |
| ADDED | NG 无障碍树 Dump 实现规格 | js_accessibility_manager.cpp:5036 OnDumpInfoNG 参数校验与分发；:5055 ChooseDumpEvent switch on DumpMode；:4834 DumpTreeNG(useWindowId) 入口；:5666 DumpTreeNodeInfoNG 节点信息；:5706 DumpTreeNodeSafeAreaInfoNg 安全区域；:5780 DumpTreeNodeCommonInfoNg 通用属性；:5827 DumpTreeNodeSimplifyInfoNG 简化模式；:5835 DumpTreeAccessibilityNodeNG 虚拟节点；:5859 DumpTreeNG(递归)；:5914 DumpTree 入口（NG 与 legacy 分发）；:10211 DumpTreeNodeInfoInJson JSON 格式 |
| ADDED | 第三方无障碍 Dump 规格 | js_third_accessibility_hover_ng.cpp:361 -simplify 标志解析；:403 DumpTreeNodeInfoForThird 第三方节点信息；:438 DumpTreeForThird 第三方树递归；:461 IsDumpTreeForThird 判定 |
| ADDED | EventManager 事件 Dump 规格定义 | event_manager.h:286-299 声明 DumpEvent / DumpEventWithCount / DoDumpTouchInfo / DumpTouchInfo / AddDumpTouchInfo；:436-442 声明 IsUseDumpTouchInfo / SetIsUseDumpTouchInfo |
| ADDED | EventManager 事件 Dump 实现规格 | event_manager.cpp:2523 DumpEvent 事件树 Dump（文本/JSON）；:3115 DumpEventWithCount 含 count 限制；:3151 DoDumpTouchInfo 触摸点历史输出；:3169 DumpTouchInfo 命令分发（-b/-d/-e/-c）；:1141 AddDumpTouchInfo 触摸事件记录 |
| ADDED | 事件 Dump 数据结构规格 | event_dump.h:34-49 FrameNodeSnapshot；:51-64 TouchPointSnapshot；:66-78 AxisSnapshot；:80-91 SmartGestureExecutionSnapshot；:93-106 EventTree；:108-145 EventTreeRecord（Dump 文本+JSON）；:147-152 EventTouchInfo；:154-162 EventTouchInfoRecord |

## 输入文档

- 关联设计：`specs/03-engine-framework/08-dfx-foundation/04-dump-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/core/accessibility/hidumper/accessibility_hidumper.h`（118 行）—— DumpMode 枚举 / DumpInfoArgument 结构 / AccessibilityHidumper 静态参数解析
  - `adapter/ohos/osal/accessibility/accessibility_hidumper_osal.h`（79 行）—— OSAL 辅助：动作转换与自定义动作测试
  - `adapter/ohos/osal/js_accessibility_manager.h`（1106 行）—— NG 无障碍 Dump 方法声明
  - `adapter/ohos/osal/js_accessibility_manager.cpp`（11585 行）—— NG 无障碍 Dump 方法实现
  - `adapter/ohos/osal/js_third_accessibility_hover_ng.cpp`（687 行）—— 第三方无障碍 Dump
  - `frameworks/core/common/event_manager.h`（640 行）—— EventManager 事件 Dump 声明
  - `frameworks/core/common/event_manager.cpp`（3522 行）—— EventManager 事件 Dump 实现
  - `frameworks/core/common/event_dump.h`（164 行）—— 事件 Dump 数据结构

## 用户故事

### US-1: AccessibilityHidumper 参数解析与 DumpMode 模式分发

- As a 可访问性调试开发者
- I want hidumper 命令经 DumpInfoArgument 结构解析后，按 DumpMode 枚举分发到对应的 dump 处理逻辑
- So that 一条 hidumper 入口可支持 23 种不同的无障碍调试模式

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DumpMode 枚举被引用 THEN 包含 23 个值：TREE / NODE / HANDLE_EVENT / HOVER_TEST / EVENT_TEST / INJECT_ACTION_TEST / EMBED_SEARCH_TEST / EMBED_HOVER_TEST / SPECIFIC_SEARCH_TEST / SET_CHECKLIST_TEST / GET_CHECKLIST_TEST / EXECUTE_ACTION_TEST / WEB_ACC_DUMP / CUSTOM_ACTION_TEST / SET_COMPONENT_TYPE_TEST / CLEAR_COMPONENT_TYPE_TEST / SET_CUSTOM_PROPERTY / GET_CUSTOM_PROPERTY / ADD_VIRTUAL_NODE / REMOVE_VIRTUAL_NODE / GET_VIRTUAL_NODE / PERFORM_VIRTUAL_NODE_ACTION_TEST。来源：`accessibility_hidumper.h:37-60` | 正常 |
| AC-1.2 | WHEN DumpInfoArgument 结构默认构造 THEN useWindowId=false、mode=DumpMode::TREE、isDumpSimplify=false、verbose=false、rootId=-1、pointX=0、pointY=0、nodeId=-1、action=0、eventId=-1、virtualNodeId=-1、containerId=-1、webAccId=-1、focusMoveRule=-1、webAccFun="tree"。来源：`accessibility_hidumper.h:62-91` | 正常 |
| AC-1.3 | WHEN AccessibilityHidumper::DumpProcessInjectActionParameters(params, nodeId, result, actionType) 被调用 THEN 从 params 向量解析注入动作参数，成功返回 true 并填充 nodeId / result / actionType 输出参数。来源：`accessibility_hidumper.h:101-105` | 正常 |
| AC-1.4 | WHEN AccessibilityHidumper::DumpProcessCustomActionParameters(params, nodeId, actionName, listActions) 被调用 THEN 从 params 解析自定义动作参数，填充 nodeId / actionName / listActions。来源：`accessibility_hidumper.h:110-114` | 正常 |

### US-2: NG 无障碍树 Dump 入口与模式分发

- As a 可访问性测试工程师
- I want OnDumpInfoNG 作为 NG 无障碍 Dump 统一入口，校验参数后经 ChooseDumpEvent 按 DumpMode 分发
- So that 所有 NG 无障碍 dump 命令通过单一入口进入，参数校验集中处理

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN OnDumpInfoNG(params, windowId, hasJson) 被调用 THEN 先调用 CheckDumpInfoParams 校验参数，校验失败输出 "Error: invalid arguments!" 并 return；再调用 GetDumpInfoArgument 解析参数结构；最后调用 ChooseDumpEvent 分发。来源：`js_accessibility_manager.cpp:5036-5053` | 正常 |
| AC-2.2 | WHEN ChooseDumpEvent 中 argument.mode==TREE THEN 设置 isUseJson_=hasJson，调用 DumpTreeNG(useWindowId, windowId, rootId, isDumpSimplify)。来源：`js_accessibility_manager.cpp:5058-5062` | 正常 |
| AC-2.3 | WHEN ChooseDumpEvent 中 argument.mode 为 HOVER_TEST THEN 调用 DumpHoverTestNG(windowId, rootId, pointX, pointY, verbose)；为 INJECT_ACTION_TEST 调用 DumpInjectActionTest；为 CUSTOM_ACTION_TEST 调用 DumpCustomActionTest；为 WEB_ACC_DUMP（WEB_SUPPORTED 编译守卫下）调用 ChooseWebDumpEvent。来源：`js_accessibility_manager.cpp:5069-5100` | 正常 |
| AC-2.4 | WHEN ChooseDumpEvent 中 argument.mode 不匹配任何 case THEN 输出 "Error: invalid arguments!"。来源：`js_accessibility_manager.cpp:5110-5112` | 边界 |

### US-3: NG 无障碍树递归 Dump 与节点信息输出

- As a 可访问性调试开发者
- I want DumpTreeNG 以递归方式遍历 NG 无障碍树，每个节点输出 ID / compid / text / 坐标 / 尺寸 / 可见性 / 可点击性等属性
- So that 可以完整查看应用 UI 树的无障碍语义结构

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN DumpTreeNG(useWindowId, windowId, rootId, isDumpSimplify) 被调用且 useWindowId==false 且 rootId==-1 THEN 回退到 DumpTree(0, 0) 走旧路径。来源：`js_accessibility_manager.cpp:4836-4839` | 边界 |
| AC-3.2 | WHEN DumpTreeNG(useWindowId, windowId, rootId, isDumpSimplify) 被调用且 pipeline 不存在 THEN 输出 "Error: pipeline is not found!" 并 return。来源：`js_accessibility_manager.cpp:4842-4846` | 异常 |
| AC-3.3 | WHEN DumpTreeNodeInfoNG(node, depth, commonProperty, childSize) 输出节点信息 THEN 通过 AddDesc 输出 ID / compid / text / accessibilityText / accessibilityGroup / accessibilityLevel / accessibilityCustomRole / top / left / width / height / visible / debugLine / clickable / longclickable / checkable / scrollable / checked / hint / childTree 共 18 个属性。来源：`js_accessibility_manager.cpp:5666-5704` | 正常 |
| AC-3.4 | WHEN DumpTreeNG(递归) 中 isDumpSimplify==true THEN 调用 DumpTreeNodeSimplifyInfoNG（DumpTreeNodeCommonInfoNg + DumpTreeNodeSafeAreaInfoNg）；isDumpSimplify==false 且 isUseJson_==false 调用 DumpTreeNodeInfoNG；isUseJson_==true 调用 DumpTreeNodeInfoInJson。来源：`js_accessibility_manager.cpp:5880-5886` | 正常 |
| AC-3.5 | WHEN DumpTreeNG(递归) 遍历到存在 AccessibilityVirtualNode 的节点 THEN 调用 DumpTreeAccessibilityNodeNG 输出虚拟节点子树，且 hasVirtualNode=true 时跳过常规子节点递归。来源：`js_accessibility_manager.cpp:5887-5911` | 正常 |

### US-4: 第三方无障碍 Dump

- As a 第三方无障碍服务开发者
- I want 对第三方 Provider 提供的无障碍节点进行树 Dump，使用与主树一致的输出格式
- So that 可以在调试中查看跨进程无障碍树的节点信息

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN GetDumpInfoArgument 解析第三方 Dump 参数 THEN 通过 params[0].compare("-simplify")==0 设置 isDumpSimplify 标志。来源：`js_third_accessibility_hover_ng.cpp:361` | 正常 |
| AC-4.2 | WHEN DumpTreeNodeInfoForThird(info, depth) 被调用 THEN 从 AccessibilityElementInfo 输出 ID / compid / text / accessibilityText / accessibilityGroup / accessibilityLevel / top / left / width / height / visible / clickable / longclickable / checkable / scrollable / checked / hint 共 17 个属性，并以 Print(depth, componentType, childCount) 结束。来源：`js_third_accessibility_hover_ng.cpp:403-436` | 正常 |
| AC-4.3 | WHEN DumpTreeForThird(elementId, jsThirdProviderOperator, depth) 被调用 THEN 通过 FindAccessibilityNodeInfosByIdFromProvider 获取节点信息，输出后递归子节点（childrenIds.rbegin 到 rend 倒序遍历）。来源：`js_third_accessibility_hover_ng.cpp:438-459` | 正常 |
| AC-4.4 | WHEN IsDumpTreeForThird(inputRootId, jsThirdProviderOperator) 被调用 THEN 将 inputRootId 拆分为 splitElementId 和 splitTreeId，splitTreeId 等于 jsThirdProviderOperator->GetBelongTreeId() 时返回 true。来源：`js_third_accessibility_hover_ng.cpp:461-474` | 正常 |

### US-5: 事件树 Dump（含 count 限制）

- As a 事件系统调试工程师
- I want 通过 hidumper 调用 EventManager::DumpEvent 或 DumpEventWithCount，输出事件树（触摸点、命中测试树、手势树）的快照
- So that 可以诊断事件分发链路、命中测试结果和手势识别竞争状态

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN DumpEvent(type, hasJson) 被调用且 hasJson==true THEN 获取 EventTreeRecord，调用 eventTree.Dump(children, 0) 生成 JSON，包装为 {"DumpEvent": children} 后通过 DumpLog::PrintJson 输出。来源：`event_manager.cpp:2523-2538` | 正常 |
| AC-5.2 | WHEN DumpEvent(type, hasJson) 被调用且 hasJson==false THEN 调用 eventTree.Dump(dumpList, 0, DUMP_START_NUMBER) 生成文本列表，逐条通过 DumpLog::Print(depth, content) 输出。来源：`event_manager.cpp:2532-2538` | 正常 |
| AC-5.3 | WHEN DumpEventWithCount(params, type, hasJson) 被调用且 params.size()>=COUNT_PARAM_SIZE 且 params[1]=="-n" THEN 读取 params[2] 作为 size，若 size 在 [MIN_DUMP_SIZE, MAX_DUMP_SIZE] 范围内则调用 eventTree.Dump(..., MAX_DUMP_SIZE-size) 输出最近 size 条记录。来源：`event_manager.cpp:3123-3146` | 正常 |
| AC-5.4 | WHEN DumpEventWithCount 中 size 不在 [MIN_DUMP_SIZE, MAX_DUMP_SIZE] 范围内 THEN 回退到 DumpEvent(type, hasJson) 全量输出。来源：`event_manager.cpp:3129-3132` | 边界 |

### US-6: 触摸点历史 Dump

- As a 触摸事件调试工程师
- I want 通过 hidumper 控制 EventManager 触摸点历史记录的开启 / dump / 关闭 / 计数，在运行时抓取触摸事件的时间戳信息
- So that 可以分析触摸事件从创建到派发的时延

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN DumpTouchInfo(params, hasJson) 中 params[1]=="-b" THEN 调用 SetIsUseDumpTouchInfo(true) 开启记录，并 ClearDumpDeque 清空历史队列。来源：`event_manager.cpp:3173-3176` | 正常 |
| AC-6.2 | WHEN DumpTouchInfo(params, hasJson) 中 params[1]=="-d" THEN 调用 DoDumpTouchInfo(hasJson) 输出触摸历史并清空队列。来源：`event_manager.cpp:3177-3179` | 正常 |
| AC-6.3 | WHEN DumpTouchInfo(params, hasJson) 中 params[1]=="-e" THEN 调用 SetIsUseDumpTouchInfo(false) 关闭记录，并 ClearDumpDeque 清空历史队列。来源：`event_manager.cpp:3180-3183` | 正常 |
| AC-6.4 | WHEN DumpTouchInfo(params, hasJson) 中 params[1]=="-c" THEN 输出 eventTouchInfo_.touchHistory_.size() 即当前历史记录条数。来源：`event_manager.cpp:3184-3186` | 正常 |
| AC-6.5 | WHEN AddDumpTouchInfo(event) 被调用且 event.sourceTool 为 MOUSE 或 TOUCHPAD 或 convertInfo.first 为 MOUSE THEN CHECK_NULL_VOID 直接 return 不记录该事件。来源：`event_manager.cpp:1144-1145` | 边界 |

### US-7: 事件 Dump 数据结构与 EventTouchInfoRecord

- As a 事件可观测性开发者
- I want EventTreeRecord / EventTouchInfoRecord 等数据结构提供 Dump 接口，支持文本和 JSON 双模式输出
- So that 事件快照数据可通过 hidumper 以文本或 JSON 格式呈现

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN FrameNodeSnapshot 结构被填充 THEN 包含 nodeId / parentNodeId / tag / comId / monopolizeEvents / isHit / hitTestMode / responseRegionList / active / strategy / id 共 11 个字段，并提供 Dump(list, depth) 文本与 Dump(json) JSON 两个重载。来源：`event_dump.h:34-49` | 正常 |
| AC-7.2 | WHEN TouchPointSnapshot 结构被填充 THEN 包含 id / point / screenPoint / type / timestamp / isInjected / downFingerIds 共 7 个字段，由 TouchEvent 构造，提供 Dump(list, depth) 与 Dump(json) 两个重载。来源：`event_dump.h:51-64` | 正常 |
| AC-7.3 | WHEN EventTree 结构被使用 THEN 包含 axis / touchPoints / hitTestTree / gestureTree / gestureMap / smartGestureExecutions / touchDownCount / axisUpdateCount / downFingerIds_ / updateAxisIds_ 共 10 个成员。来源：`event_dump.h:93-106` | 正常 |
| AC-7.4 | WHEN EventTreeRecord::Dump(dumpList, depth, startNumber) 被调用 THEN 遍历 eventTreeList 中的 EventTree，从 startNumber 指定的起始序号开始输出文本格式快照；Dump(json, depth, startNumber) 同理输出 JSON 格式。来源：`event_dump.h:130-132` | 正常 |
| AC-7.5 | WHEN EventTouchInfoRecord::DumpAndClear(dumpList) 被调用 THEN 将 touchHistory_ 队列中的 EventTouchInfo 输出到 dumpList 并清空队列；DumpAndClear(json) 同理输出 JSON。来源：`event_dump.h:157-158` | 正常 |
| AC-7.6 | WHEN EventTouchInfoRecord::isUseDumpTouchInfo_ 为 false THEN AddTouchPoint 不被调用（由 EventManager::IsUseDumpTouchInfo 门控）；dequeMaxCnt_ 控制历史队列最大容量。来源：`event_dump.h:159-161` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|---------|------|
| AC-1.1 | R-1 | TASK-04 | 代码评审 | 代码审查 |
| AC-1.2 | R-2 | TASK-04 | 代码评审 | 代码审查 |
| AC-1.3 | R-3 | TASK-04 | 单元测试 | 代码审查 |
| AC-1.4 | R-3 | TASK-04 | 单元测试 | 代码审查 |
| AC-2.1 | R-4 | TASK-04 | 单元测试 | 代码审查 |
| AC-2.2 | R-5 | TASK-04 | 代码评审 | 代码审查 |
| AC-2.3 | R-5 | TASK-04 | 代码评审 | 代码审查 |
| AC-2.4 | R-6 | TASK-04 | 代码评审 | 代码审查 |
| AC-3.1 | R-7 | TASK-04 | 代码评审 | 代码审查 |
| AC-3.2 | R-8 | TASK-04 | 单元测试 | 代码审查 |
| AC-3.3 | R-9 | TASK-04 | 代码评审 | 代码审查 |
| AC-3.4 | R-10 | TASK-04 | 代码评审 | 代码审查 |
| AC-3.5 | R-11 | TASK-04 | 代码评审 | 代码审查 |
| AC-4.1 | R-12 | TASK-04 | 代码评审 | 代码审查 |
| AC-4.2 | R-13 | TASK-04 | 代码评审 | 代码审查 |
| AC-4.3 | R-14 | TASK-04 | 代码评审 | 代码审查 |
| AC-4.4 | R-15 | TASK-04 | 单元测试 | 代码审查 |
| AC-5.1 | R-16 | TASK-04 | 代码评审 | 代码审查 |
| AC-5.2 | R-16 | TASK-04 | 代码评审 | 代码审查 |
| AC-5.3 | R-17 | TASK-04 | 单元测试 | 代码审查 |
| AC-5.4 | R-18 | TASK-04 | 代码评审 | 代码审查 |
| AC-6.1 | R-19 | TASK-04 | 单元测试 | 代码审查 |
| AC-6.2 | R-20 | TASK-04 | 单元测试 | 代码审查 |
| AC-6.3 | R-19 | TASK-04 | 单元测试 | 代码审查 |
| AC-6.4 | R-21 | TASK-04 | 单元测试 | 代码审查 |
| AC-6.5 | R-22 | TASK-04 | 代码评审 | 代码审查 |
| AC-7.1 | R-23 | TASK-04 | 代码评审 | 代码审查 |
| AC-7.2 | R-23 | TASK-04 | 代码评审 | 代码审查 |
| AC-7.3 | R-24 | TASK-04 | 代码评审 | 代码审查 |
| AC-7.4 | R-25 | TASK-04 | 单元测试 | 代码审查 |
| AC-7.5 | R-26 | TASK-04 | 单元测试 | 代码审查 |
| AC-7.6 | R-27 | TASK-04 | 代码评审 | 代码审查 |

## 规则定义

> 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | DumpMode 枚举引用 | 枚举定义 23 种无障碍 dump 模式，覆盖树/节点/事件/悬停/动作注入/Web/自定义属性/虚拟节点等场景。 | 枚举值为隐式序号 0-22。 | AC-1.1 |
| R-2 | 行为 | DumpInfoArgument 默认构造 | 所有字段使用默认值初始化，mode 默认 TREE，nodeId/rootId/webAccId 默认 -1 表示未指定。 | 自定义属性字段 customEnabled 默认 true，其余布尔默认 false。 | AC-1.2 |
| R-3 | 行为 | AccessibilityHidumper 静态参数解析 | DumpProcessInjectActionParameters / DumpProcessExecuteActionParameters / DumpProcessCustomActionParameters 从 params 向量解析对应参数并填充输出引用。 | 解析失败返回 false。 | AC-1.3 / AC-1.4 |
| R-4 | 行为 | OnDumpInfoNG 入口调用 | 先 CheckDumpInfoParams 校验，再 GetDumpInfoArgument 解析，再 ChooseDumpEvent 分发。三步顺序执行。 | CheckDumpInfoParams 失败输出 "Error: invalid arguments!" 并 return。 | AC-2.1 |
| R-5 | 行为 | ChooseDumpEvent 模式分发 | switch on argument.mode 将 23 种 DumpMode 分发到对应的 dump 处理方法。 | TREE→DumpTreeNG、NODE→DumpPropertyNG、HANDLE_EVENT→DumpHandleEvent、HOVER_TEST→DumpHoverTestNG 等。 | AC-2.2 / AC-2.3 |
| R-6 | 边界 | ChooseDumpEvent default 分支 | 不匹配任何 DumpMode case 时输出 "Error: invalid arguments!"。 | default 分支兜底所有未知模式。 | AC-2.4 |
| R-7 | 边界 | DumpTreeNG 无 windowId 回退 | useWindowId==false 且 rootId==-1 时回退到 DumpTree(0,0) 兼容旧入口。 | 仅在未指定窗口和根节点时触发。 | AC-3.1 |
| R-8 | 异常 | DumpTreeNG pipeline 不存在 | GetPipelineByWindowId 返回 null 时输出 "Error: pipeline is not found!"。 | pipeline 可能在窗口未注册时为 null。 | AC-3.2 |
| R-9 | 行为 | DumpTreeNodeInfoNG 节点属性输出 | 对每个节点输出 18 个属性：ID/compid/text/accessibilityText/accessibilityGroup/accessibilityLevel/accessibilityCustomRole/top/left/width/height/visible/debugLine/clickable/longclickable/checkable/scrollable/checked/hint/childTree。 | accessibilityProperty 为 null 时部分属性跳过。 | AC-3.3 |
| R-10 | 行为 | DumpTreeNG 三模式选择 | isDumpSimplify→SimplifyInfoNG，isUseJson_→InJson，否则→InfoNG。 | 三模式互斥，simplify 优先级最高。 | AC-3.4 |
| R-11 | 行为 | DumpTreeNG 虚拟节点遍历 | 存在 AccessibilityVirtualNode 时调用 DumpTreeAccessibilityNodeNG 输出虚拟子树，hasVirtualNode=true 时跳过常规子节点。 | 虚拟节点优先于常规子节点输出。 | AC-3.5 |
| R-12 | 行为 | 第三方 Dump simplify 标志 | params[0]=="-simplify" 时设置 isDumpSimplify=true。 | simplify 标志为第三方 Dump 首参数。 | AC-4.1 |
| R-13 | 行为 | DumpTreeNodeInfoForThird 属性输出 | 从 AccessibilityElementInfo 输出 17 个属性，字段与主树 DumpTreeNodeInfoNG 对齐。 | 第三方节点信息来自跨进程 AccessibilityElementInfo。 | AC-4.2 |
| R-14 | 行为 | DumpTreeForThird 递归遍历 | 通过 FindAccessibilityNodeInfosByIdFromProvider 获取节点，倒序遍历子节点递归。 | 获取失败或 infos 为空时直接 return。 | AC-4.3 |
| R-15 | 行为 | IsDumpTreeForThird 判定 | 拆分 inputRootId 得到 splitTreeId，与 jsThirdProviderOperator->GetBelongTreeId() 比较判定。 | 树 ID 匹配才走第三方 Dump 路径。 | AC-4.4 |
| R-16 | 行为 | DumpEvent 事件树输出 | hasJson==true 输出 JSON（{"DumpEvent": children}），hasJson==false 输出文本列表（DumpLog::Print(depth, content)）。 | 两种模式共享同一个 EventTreeRecord。 | AC-5.1 / AC-5.2 |
| R-17 | 行为 | DumpEventWithCount count 限制 | params[1]=="-n" 时读取 params[2] 作为 size，调用 Dump(..., MAX_DUMP_SIZE-size) 输出最近 size 条。 | size 必须在 [MIN_DUMP_SIZE, MAX_DUMP_SIZE] 范围内。 | AC-5.3 |
| R-18 | 边界 | DumpEventWithCount size 越界 | size 超出范围时回退到全量 DumpEvent。 | COUNT_PARAM_SIZE 为参数门槛。 | AC-5.4 |
| R-19 | 行为 | DumpTouchInfo 开启/关闭 | -b 开启记录（SetIsUseDumpTouchInfo(true) + ClearDumpDeque），-e 关闭记录（SetIsUseDumpTouchInfo(false) + ClearDumpDeque）。 | 开启和关闭都会清空历史队列。 | AC-6.1 / AC-6.3 |
| R-20 | 行为 | DumpTouchInfo dump | -d 调用 DoDumpTouchInfo(hasJson) 输出触摸历史并清空队列。 | DumpAndClear 语义：输出后自动清空。 | AC-6.2 |
| R-21 | 行为 | DumpTouchInfo 计数 | -c 输出 eventTouchInfo_.touchHistory_.size() 当前记录条数。 | 仅输出数量不输出内容。 | AC-6.4 |
| R-22 | 边界 | AddDumpTouchInfo 鼠标事件过滤 | event.sourceTool 为 MOUSE / TOUCHPAD 或 convertInfo.first 为 MOUSE 时不记录。 | CHECK_NULL_VOID 语义：条件满足则 return。 | AC-6.5 |
| R-23 | 行为 | 事件快照结构字段定义 | FrameNodeSnapshot 含 11 字段、TouchPointSnapshot 含 7 字段，各自提供 Dump 文本和 JSON 重载。 | AxisSnapshot 含 6 字段，SmartGestureExecutionSnapshot 含 7 字段。 | AC-7.1 / AC-7.2 |
| R-24 | 行为 | EventTree 结构 | 包含 axis/touchPoints/hitTestTree/gestureTree/gestureMap/smartGestureExecutions 六类子树以及 touchDownCount/axisUpdateCount/downFingerIds_/updateAxisIds_ 四个统计字段。 | gestureTree 按 finger 分组。 | AC-7.3 |
| R-25 | 行为 | EventTreeRecord::Dump 输出 | 遍历 eventTreeList，支持 depth 限制和 startNumber 起始序号，文本和 JSON 双模式。 | startNumber 用于 count 限制场景的偏移。 | AC-7.4 |
| R-26 | 行为 | EventTouchInfoRecord::DumpAndClear | 将 touchHistory_ 队列输出后清空，支持文本和 JSON 双模式。 | 输出后队列变为空。 | AC-7.5 |
| R-27 | 边界 | EventTouchInfoRecord 门控 | isUseDumpTouchInfo_ 为 false 时不记录触摸点；dequeMaxCnt_ 控制最大容量。 | 由 EventManager::IsUseDumpTouchInfo 门控 AddTouchPoint。 | AC-7.6 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.4 / R-1..R-3 | 代码评审 + 单元测试 | accessibility_hidumper.h:37-115 |
| VM-2 | AC-2.1..2.4 / R-4..R-6 | 单元测试 + 代码评审 | js_accessibility_manager.cpp:5036-5114 |
| VM-3 | AC-3.1..3.5 / R-7..R-11 | 代码评审 + 单元测试 | js_accessibility_manager.cpp:4834-4854,5666-5912 |
| VM-4 | AC-4.1..4.4 / R-12..R-15 | 代码评审 + 单元测试 | js_third_accessibility_hover_ng.cpp:356-474 |
| VM-5 | AC-5.1..5.4 / R-16..R-18 | 代码评审 + 单元测试 | event_manager.cpp:2523-2538,3115-3147 |
| VM-6 | AC-6.1..6.5 / R-19..R-22 | 单元测试 + 代码评审 | event_manager.cpp:1141-1158,3151-3186, event_manager.h:436-442 |
| VM-7 | AC-7.1..7.6 / R-23..R-27 | 代码评审 + 单元测试 | event_dump.h:34-162 |
| VM-8 | AC-3.5 / R-11 | 代码评审 | js_accessibility_manager.cpp:5887-5911 |
| VM-9 | AC-1.1 / R-1 | 代码评审 | accessibility_hidumper.h:37-60 |

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
| 可访问性 Dump 调用链自上而下 | hidumper→OnDumpInfoNG→GetDumpInfoArgument→ChooseDumpEvent→具体 Dump 方法，不允许反向调用 | AC-2.1 |
| AccessibilityHidumper 纯参数解析 | 不持有状态，不直接操作 FrameNode；具体节点操作由 JsAccessibilityManager 实现 | AC-1.3 / AC-1.4 |
| 第三方 Dump 独立输出方法 | DumpTreeNodeInfoForThird vs DumpTreeNodeInfoNG，不共享节点遍历逻辑 | AC-4.2 / AC-4.3 |
| 事件树 Dump 与触摸历史两条独立路径 | DumpEvent 输出 EventTreeRecord 快照；DumpTouchInfo 输出 EventTouchInfoRecord 历史 | AC-5.1 / AC-6.2 |
| isUseDumpTouchInfo_ 默认 false | 必须通过 -b 命令显式开启，避免正常运行性能开销 | AC-6.1 / AC-7.6 |
| DumpLog 统一写入 | 所有 Dump 输出通过 DumpLog::GetInstance()，Dump 方法不直接写标准输出 | AC-3.3 / AC-5.1 |

## 非性能需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | DumpInfoArgument 栈上局部结构无堆分配；ChooseDumpEvent O(1) switch | 代码评审 | 代码审查 |
| 性能 | AddDumpTouchInfo isUseDumpTouchInfo_==false 时仅一次检查即 return | 代码评审 | 代码审查 |
| 性能 | touchHistory_ deque dequeMaxCnt_ 限制容量，超出丢弃旧记录 | 代码评审 | 代码审查 |
| 可观测 | 23 种 DumpMode + 文本/JSON 双格式 + 触摸历史 | 代码评审 | 代码审查 |
| 鲁棒性 | CheckDumpInfoParams 校验失败输出错误信息不崩溃；pipeline null 检查 | 代码评审 | 代码审查 |
| 鲁棒性 | AddDumpTouchInfo 对鼠标/触摸板事件 CHECK_NULL_VOID 过滤 | 代码评审 | 代码审查 |
| 线程安全 | DumpTouchInfo/DoDumpTouchInfo/AddDumpTouchInfo CHECK_RUN_ON(UI) | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 可访问性 Dump 直接输出无障碍树和节点属性 | DumpTreeNG / DumpTreeNodeInfoNG |
| 大字体 | 否 | Dump 输出不受字体缩放影响 | — |
| 深色模式 | 否 | Dump 输出不含颜色模式语义 | — |
| 多窗口 | 是 | OnDumpInfoNG 按 windowId 区分窗口 | DumpTreeNG(useWindowId) |
| 多用户 | 否 | 框架内部能力，不涉及多用户 | — |
| 版本升级 | 否 | 全部为已有实现补录 | — |
| 生态兼容 | 否 | 无 Public/System API 变更 | — |

## Spec 自审清单

- [x] 所有 H2 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」中可被引用
- [x] 规则定义使用 R-N 编号，类型标签齐全（行为/边界/异常）
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 为框架内部接口
- [x] 兼容性声明覆盖 DumpMode / NG-Legacy / Web / 三方 / 输出格式五个维度
- [x] 无 TODO / TBD / 待定 占位符

## context-references

```yaml
references:
  - path: frameworks/core/accessibility/hidumper/accessibility_hidumper.h
    lines: 37-60
    description: DumpMode 枚举：23 种无障碍 dump 模式
  - path: frameworks/core/accessibility/hidumper/accessibility_hidumper.h
    lines: 62-91
    description: DumpInfoArgument 参数结构：useWindowId / mode / isDumpSimplify / verbose / rootId / pointX / pointY / nodeId / action / eventId / virtualNodeId / containerId / 自定义属性 / webAccId / focusMoveRule / webAccFun
  - path: frameworks/core/accessibility/hidumper/accessibility_hidumper.h
    lines: 93-97
    description: ExecuteActionArgument 结构：elementId / actionType / actionArguments
  - path: frameworks/core/accessibility/hidumper/accessibility_hidumper.h
    lines: 99-115
    description: AccessibilityHidumper 类：DumpProcessInjectActionParameters / DumpProcessExecuteActionParameters / DumpProcessCustomActionParameters
  - path: adapter/ohos/osal/accessibility/accessibility_hidumper_osal.h
    lines: 67-77
    description: AccessibilityManagerHidumper：ConvertAccessibilityAction / ConvertActionTypeToString / DumpCustomActionTest
  - path: adapter/ohos/osal/js_accessibility_manager.h
    lines: 584
    description: OnDumpInfoNG 声明
  - path: adapter/ohos/osal/js_accessibility_manager.h
    lines: 587
    description: DumpTree 声明
  - path: adapter/ohos/osal/js_accessibility_manager.h
    lines: 823-832
    description: DumpTreeNG 系列声明：useWindowId 重载 / 递归重载 / SafeArea / CommonInfo / Simplify / AccessibilityNode
  - path: adapter/ohos/osal/js_accessibility_manager.h
    lines: 965
    description: DumpTreeNodeInfoInJson 声明
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 4834-4855
    description: DumpTreeNG(useWindowId) 入口实现
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5036-5053
    description: OnDumpInfoNG 实现：CheckDumpInfoParams → GetDumpInfoArgument → ChooseDumpEvent
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5055-5114
    description: ChooseDumpEvent 实现：switch on DumpMode 分发 23 种模式
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5666-5704
    description: DumpTreeNodeInfoNG 实现：18 属性输出
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5706-5718
    description: DumpTreeNodeSafeAreaInfoNg 实现：SafeAreaExpandOpts / SafeAreaInsets / selfAdjust
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5780-5825
    description: DumpTreeNodeCommonInfoNg 实现：BackgroundColor / PaintRectWithoutTransform / 坐标 / Padding / Margin / Border / LayoutRect
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5827-5833
    description: DumpTreeNodeSimplifyInfoNG 实现：CommonInfoNg + SafeAreaInfoNg
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5835-5857
    description: DumpTreeAccessibilityNodeNG 实现：虚拟节点递归
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5859-5912
    description: DumpTreeNG(递归) 实现：节点查找 / 子节点遍历 / 虚拟节点 / Extension 组件 / 三模式输出
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 5914-5943
    description: DumpTree 实现：NG 与 legacy 分发 + subPipeline 遍历
  - path: adapter/ohos/osal/js_accessibility_manager.cpp
    lines: 10211-10220
    description: DumpTreeNodeInfoInJson 实现：CreateNodeInfoJson + FormatDumpInfo + PrintJson
  - path: adapter/ohos/osal/js_third_accessibility_hover_ng.cpp
    lines: 356-401
    description: GetDumpInfoArgument 第三方参数解析：-simplify / -w / --root / --hover-test / -v / -json
  - path: adapter/ohos/osal/js_third_accessibility_hover_ng.cpp
    lines: 403-436
    description: DumpTreeNodeInfoForThird 实现：17 属性输出
  - path: adapter/ohos/osal/js_third_accessibility_hover_ng.cpp
    lines: 438-459
    description: DumpTreeForThird 实现：FindAccessibilityNodeInfosByIdFromProvider + 倒序递归
  - path: adapter/ohos/osal/js_third_accessibility_hover_ng.cpp
    lines: 461-474
    description: IsDumpTreeForThird 实现：splitTreeId 匹配判定
  - path: frameworks/core/common/event_manager.h
    lines: 286-288
    description: DumpEvent / DumpEventWithCount 声明
  - path: frameworks/core/common/event_manager.h
    lines: 295-299
    description: DoDumpTouchInfo / DumpTouchInfo / AddDumpTouchInfo 声明
  - path: frameworks/core/common/event_manager.h
    lines: 436-442
    description: IsUseDumpTouchInfo / SetIsUseDumpTouchInfo 声明
  - path: frameworks/core/common/event_manager.cpp
    lines: 1141-1158
    description: AddDumpTouchInfo 实现：MOUSE/TOUCHPAD 过滤 + history 遍历 + AddTouchPoint
  - path: frameworks/core/common/event_manager.cpp
    lines: 2523-2538
    description: DumpEvent 实现：EventTreeRecord.Dump 文本/JSON 双模式
  - path: frameworks/core/common/event_manager.cpp
    lines: 3115-3147
    description: DumpEventWithCount 实现：-n count 限制 + 范围校验
  - path: frameworks/core/common/event_manager.cpp
    lines: 3151-3167
    description: DoDumpTouchInfo 实现：EventTouchInfoRecord.DumpAndClear 文本/JSON
  - path: frameworks/core/common/event_manager.cpp
    lines: 3169-3188
    description: DumpTouchInfo 实现：-b/-d/-e/-c 命令分发
  - path: frameworks/core/common/event_dump.h
    lines: 34-49
    description: FrameNodeSnapshot：nodeId / parentNodeId / tag / comId / monopolizeEvents / isHit / hitTestMode / responseRegionList / active / strategy / id
  - path: frameworks/core/common/event_dump.h
    lines: 51-64
    description: TouchPointSnapshot：id / point / screenPoint / type / timestamp / isInjected / downFingerIds
  - path: frameworks/core/common/event_dump.h
    lines: 66-78
    description: AxisSnapshot：id / point / screenPoint / action / timestamp / isInjected
  - path: frameworks/core/common/event_dump.h
    lines: 80-91
    description: SmartGestureExecutionSnapshot：trigger / hasMonitor / defaultProposalType / defaultProposalNodeId / resolvedProposalType / resolvedProposalNodeId / executeResult
  - path: frameworks/core/common/event_dump.h
    lines: 93-106
    description: EventTree：axis / touchPoints / hitTestTree / gestureTree / gestureMap / smartGestureExecutions / touchDownCount / axisUpdateCount / downFingerIds_ / updateAxisIds_
  - path: frameworks/core/common/event_dump.h
    lines: 108-145
    description: EventTreeRecord：AddAxis / AddTouchPoint / AddFrameNodeSnapshot / UpdateFrameNodeSnapshot / AddGestureSnapshot / AddSmartGestureExecution / AddGestureProcedure / Dump 文本+JSON / BuildTouchPoints / BuildAxis / BuildSmartGestureExecutions / BuildGestureTree / BuildHitTestTree / MountToParent
  - path: frameworks/core/common/event_dump.h
    lines: 147-152
    description: EventTouchInfo：pointerID / creatTime / processTime / dispatchTime
  - path: frameworks/core/common/event_dump.h
    lines: 154-162
    description: EventTouchInfoRecord：AddTouchPoint / ClearDumpDeque / DumpAndClear 文本+JSON / touchHistory_ / dequeMaxCnt_ / isUseDumpTouchInfo_
```
