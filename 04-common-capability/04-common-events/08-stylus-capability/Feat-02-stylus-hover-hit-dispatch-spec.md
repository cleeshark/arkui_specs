# 特性规格

> Func-04-04-08-Feat-02 手写笔悬停命中与事件派发：固化 Pen Hover 事件识别、鼠标型命中测试、目标收集、进入/退出差分派发、Hover Move 传播及窗口移出清理行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手写笔悬停命中与事件派发 |
| 特性编号 | Func-04-04-08-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | ArkTS `onHover/onHoverMove` 现有能力；NDK Hover Move API 15、Hover Event API 17 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | L2（复杂） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Pen Hover 入口与命中测试 | 补录 PEN + LEVITATE 事件进入 UI Pipeline 后按 Mouse hit-test 收集目标的行为 |
| ADDED | 悬停状态差分 | 补录 last/current 目标链、进入/退出回调、传播停止边界 |
| ADDED | Hover Move 派发 | 补录按 event.id 保存移动目标及逐级传播行为 |
| ADDED | 窗口移出和按下清理 | 补录离开窗口以及带压力 Pen Down 时合成移出行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/08-stylus-capability/design.md` | 共享设计，增量合并 |
| 入口与 Pipeline | `adapter/ohos/entrance/ace_container.cpp:1350`、`frameworks/core/pipeline_ng/pipeline_context.cpp:5051` | 已核对 |
| 命中与派发 | `frameworks/core/common/event_manager_pen.cpp:27` | 已核对 |
| 目标收集 | `frameworks/core/components_ng/base/frame_node.cpp:4213`、`frameworks/core/components_ng/event/input_event_hub.cpp:74`、`input_event.cpp:176` | 已核对 |
| 回调构造 | `frameworks/core/event/mouse_event.cpp:69` | 已核对 |
| Public NDK 事件 | `interfaces/native/native_node.h:10525`、`:10555` | 已核对 |

> 目标仓库基线未纳入 canonical ArkTS SDK 声明。`onHover/onHoverMove` 的签名由仓内静态生成契约和 inner-api `.d.ets` 交叉验证，ArkTS `@since` 注释未经 canonical d.ts 验证。

## 用户故事

### US-1: 识别并路由手写笔悬停事件

**作为** ArkUI 应用开发者，  
**我想要** Pen Hover 事件进入独立悬停处理链，  
**以便** 在笔尖接触屏幕前获得组件交互反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN sourceTool 为 PEN 且 TouchType 为 LEVITATE_IN_WINDOW、LEVITATE_MOVE 或 LEVITATE_OUT_WINDOW THEN `IsPenHoverEvent()` 返回 true | 正常 |
| AC-1.2 | WHEN AceContainer 收到 Pen Hover 事件 THEN 调用 `PipelineContext::OnPenHoverEvent`，不进入普通 `OnTouchEvent` 路径 | 正常 |
| AC-1.3 | WHEN Pipeline 处理 Pen Hover THEN 将 hitTestType 设置为 MOUSE、inputEventType 设置为 TOUCH_SCREEN，并保持 sourceTool 和事件类型 | 正常 |
| AC-1.4 | WHEN sourceTool 不是 PEN 或 TouchType 不在三种 LEVITATE 类型中 THEN 不按 Pen Hover 链处理 | 边界 |

实现证据：`touch_event.cpp:509-515`、`ace_container.cpp:1350-1365`、`pipeline_context.cpp:5051-5077`。

### US-2: 收集悬停与移动目标

**作为** ArkUI 组件开发者，  
**我想要** 命中组件只在注册相应回调时加入目标链，  
**以便** 避免无回调节点参与派发。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN FrameNode 的 TouchTest 遇到 Pen Hover THEN 通过 `ProcessPenHoverTestHit` 收集 HoverEventTarget | 正常 |
| AC-2.2 | WHEN节点没有 inputEvents、userCallback 和 userJSFrameNodeCallback THEN 不创建或追加 Pen Hover 目标 | 边界 |
| AC-2.3 | WHEN节点注册 onHover THEN 创建/复用 penHoverEventTarget 并设置进入/退出 callback、坐标偏移、目标信息和附着节点 | 正常 |
| AC-2.4 | WHEN节点注册 onHoverMove THEN 创建/复用独立的 penHoverMoveEventTarget 并设置移动 callback | 正常 |
| AC-2.5 | WHEN TouchTestResult 包含非 HoverEventTarget 或没有对应 Pen callback 的目标 THEN UpdatePenHoverNode/MoveNode 忽略该目标 | 边界 |

实现证据：`frame_node.cpp:4213-4220`、`input_event_hub.cpp:74-93`、`input_event.cpp:176-259`、`event_manager_pen.cpp:41-75`。

### US-3: 派发悬停进入与退出

**作为** ArkUI 应用开发者，  
**我想要** 在笔尖进入或离开组件时收到一次状态变化回调，  
**以便** 更新组件悬停状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN LEVITATE_IN_WINDOW 到达 THEN 清空该事件身份的 last 链并将本次命中目标设为 current 链 | 正常 |
| AC-3.2 | WHEN LEVITATE_OUT_WINDOW 到达 THEN 将 current 链移入 last 链并清空 current 链 | 正常 |
| AC-3.3 | WHEN普通 LEVITATE_MOVE 改变命中链 THEN last=current 旧值，current=本次命中值 | 正常 |
| AC-3.4 | WHEN last 中目标不在 current 有效链 THEN 对该目标调用 `HandlePenHoverEvent(false, event)` | 正常 |
| AC-3.5 | WHEN current 中目标不在 last 有效链 THEN 调用 `HandlePenHoverEvent(true, event)` | 正常 |
| AC-3.6 | WHEN某一级 HoverInfo 调用 stopPropagation THEN 当前进入派发在该级停止，并保存 dispatch length 约束后续退出边界 | 边界 |
| AC-3.7 | WHEN回调执行期间覆盖自身 callback THEN 当前派发仍使用调用前复制的 callback 完成一次调用 | 恢复 |

实现证据：`event_manager_pen.cpp:41-65,78-135`、`mouse_event.cpp:69-103`。

### US-4: 派发悬停移动事件

**作为** ArkUI 应用开发者，  
**我想要** 在笔尖悬停移动时持续获得位置和姿态，  
**以便** 显示笔尖预览或预测落笔位置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN本次命中链包含 onHoverMove 目标 THEN以 event.id 为键保存完整 move 目标链 | 正常 |
| AC-4.2 | WHEN `DispatchPenHoverMoveEventNG` 找不到 event.id 对应目标链 THEN不触发回调并直接返回 | 边界 |
| AC-4.3 | WHEN目标链存在 THEN按链顺序调用 `HandlePenHoverMoveEvent` | 正常 |
| AC-4.4 | WHEN某一级 HoverInfo 设置 stopPropagation THEN移动派发在该级停止，后续目标不回调 | 边界 |
| AC-4.5 | WHEN构造 Pen HoverInfo THEN转换本地坐标并暴露时间、设备、sourceTool、tiltX/Y、rollAngle、窗口/屏幕/全局坐标和 targetDisplayId | 正常 |
| AC-4.6 | WHEN Pipeline 处理 LEVITATE_IN_WINDOW、LEVITATE_MOVE 或 LEVITATE_OUT_WINDOW THEN均执行 Hover Move 目标更新与派发；若目标链存在，进入/移出事件也可能触发 onHoverMove | 边界 |

实现证据：`event_manager_pen.cpp:66-75,137-149`、`mouse_event.cpp:105-139`。

### US-5: 处理窗口移出和公开事件接口

**作为** ArkUI 应用开发者，  
**我想要** 在笔尖离开窗口或落笔时关闭残留悬停状态，  
**以便** 避免组件保持错误的 hover 状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN sourceTool=PEN、TouchType=DOWN 且 force 不为 0 THEN `HandlePenHoverOut` 合成 PROXIMITY_OUT，使用空命中结果触发已有 current 目标退出 | 恢复 |
| AC-5.2 | WHEN任一条件不满足，包括 force=0 THEN `HandlePenHoverOut` 不执行清理 | 边界 |
| AC-5.3 | WHEN应用注册 ArkTS `onHover` THEN回调接收 isHover 和 HoverEvent；WHEN注册 `onHoverMove` THEN回调接收 HoverEvent | 正常 |
| AC-5.4 | WHEN Native 应用注册 NODE_ON_HOVER_MOVE THEN API 15+ 接收 ArkUI_UIInputEvent；WHEN注册 NODE_ON_HOVER_EVENT THEN API 17+ 接收进入/离开事件 | 正常 |
| AC-5.5 | WHEN Native Hover Move 事件被构造 THEN pressure 固定为 0，toolType、tiltX/Y、rollAngle 和坐标由 HoverInfo 写入 | 正常 |
| AC-5.6 | WHEN ArkTS onHover/onHoverMove 或 NDK NODE_ON_HOVER_EVENT 设置 stopPropagation THEN传播状态写回 HoverInfo；WHEN NDK NODE_ON_HOVER_MOVE 回调尝试停止传播 THEN当前转换路径不回写 stopPropagation，后续目标仍可继续派发 | 边界 |
| AC-5.7 | WHEN Pen Hover current 目标 vector 被清空 THEN对应 map key 仍保留，后续事件通过覆盖该 key 更新状态；通用 `ClearResults()` 不清理三张 Pen Hover map | 边界 |

实现证据：`pipeline_context.cpp:5080-5093`、`common.ets:9508-9532`、`native_node.h:10525-10572`、`node_common_modifier.cpp:13259-13404`、`ui_input_event.cpp:3134-3159`、`event_manager.cpp:2445-2452`。

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | Core/Pipeline 单测 | `touch_event.cpp:509`、`pipeline_context.cpp:5051` |
| AC-2.1~2.5 | R-5~R-8 | 已有实现 | InputEventHub 单测 | `input_event_hub_test_ng.cpp:1120`、`input_event.cpp:176` |
| AC-3.1~3.7 | R-9~R-14 | 已有实现 | EventManager 单测 | `event_manager_pen_test_ng.cpp:24-200` |
| AC-4.1~4.6 | R-15~R-18, R-23 | 已有实现 | EventManager/事件对象单测 | `event_manager_pen_test_ng.cpp:102`、`mouse_event.cpp:105` |
| AC-5.1~5.7 | R-19~R-22, R-24~R-25 | 已有实现 | Pipeline/NDK 集成测试 | `pipeline_context_test_ng_two.cpp:385`、`native_node.h:10525` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | sourceTool=PEN 且 type 为三种 LEVITATE 事件 | `IsPenHoverEvent()` 返回 true | `touch_event.cpp:509-515` | AC-1.1 |
| R-2 | 行为 | AceContainer 收到 Pen Hover | 路由到 OnPenHoverEvent | 不进入普通 OnTouchEvent | AC-1.2 |
| R-3 | 行为 | Pipeline 创建 TouchRestrict | hitTestType=MOUSE，inputEventType=TOUCH_SCREEN | 仍保留 Pen sourceTool | AC-1.3 |
| R-4 | 边界 | sourceTool 或 type 不匹配 | 不进入 Pen Hover 专用链 | 三种 LEVITATE 类型之外均不匹配 | AC-1.4 |
| R-5 | 行为 | FrameNode 执行 Pen Hover TouchTest | 调用 InputEventHub::ProcessPenHoverTestHit | `frame_node.cpp:4213-4220` | AC-2.1 |
| R-6 | 边界 | actuator 无任何回调 | 不追加目标 | inputEvents、userCallback、userJSFrameNodeCallback 全空 | AC-2.2 |
| R-7 | 行为 | 注册 onHover/onHoverMove | 分别创建或复用两个 HoverEventTarget | 两类目标独立保存 callback | AC-2.3, AC-2.4 |
| R-8 | 边界 | TouchTestResult 目标无 Pen callback | Update 阶段忽略 | 通过 IsPenHoverTarget/IsPenHoverMoveTarget 过滤 | AC-2.5 |
| R-9 | 行为 | LEVITATE_IN_WINDOW | last 清空，current=本次目标 | 以 GetEventIdentity 为键 | AC-3.1 |
| R-10 | 行为 | LEVITATE_OUT_WINDOW | last=旧 current，current 清空 | 触发退出差分 | AC-3.2 |
| R-11 | 行为 | 其他 Pen Hover move | last=旧 current，current=本次目标 | `event_manager_pen.cpp:58-63` | AC-3.3 |
| R-12 | 行为 | last/current 目标集合有差异 | 对离开目标发 false，对新目标发 true | 相同有效目标不重复进入 | AC-3.4, AC-3.5 |
| R-13 | 边界 | HandlePenHoverEvent 返回 false | 停止当前进入链并保存 dispatch length | 后续退出仅覆盖曾有效派发部分 | AC-3.6 |
| R-14 | 恢复 | callback 可能在回调中被替换 | 复制 callback 后再调用 | 本次调用不被覆盖动作中断 | AC-3.7 |
| R-15 | 行为 | UpdatePenHoverMoveNode | 以 event.id 保存 move 目标链 | 与 enter/exit 使用 GetEventIdentity 不同 | AC-4.1 |
| R-16 | 边界 | event.id 无目标链 | 直接返回 | 不创建空 map 项 | AC-4.2 |
| R-17 | 行为 | move 目标链存在 | 依次构造 HoverInfo 并回调 | 坐标通过附着 FrameNode Transform | AC-4.3, AC-4.5 |
| R-18 | 边界 | move callback 设置 stopPropagation | 在当前目标停止 | 后续 move 目标不回调 | AC-4.4 |
| R-19 | 恢复 | PEN DOWN 且 force!=0 | 合成 PROXIMITY_OUT 并用空命中链派发退出 | `pipeline_context.cpp:5080-5093` | AC-5.1 |
| R-20 | 边界 | 非 PEN、非 DOWN 或 force=0 | 不合成退出 | 三条件任一不满足即返回 | AC-5.2 |
| R-21 | 行为 | 注册公开 Hover API | ArkTS/NDK 回调接收 Hover 数据 | canonical ArkTS 版本未经 d.ts 验证 | AC-5.3, AC-5.4 |
| R-22 | 行为 | 构造 Native Hover Move | pressure=0，复制姿态与坐标 | `node_common_modifier.cpp:13348-13404` | AC-5.5 |
| R-23 | 边界 | Pipeline 处理任一 Pen LEVITATE 事件 | 始终在 enter/exit 派发后执行 move 派发 | 当前未按 LEVITATE_MOVE 过滤；`pipeline_context.cpp:5074-5076` | AC-4.6 |
| R-24 | 边界 | 回调尝试停止传播 | ArkTS 两类回调和 NDK Hover Event 可写回，NDK Hover Move 不写回 | SetStopPropagation 支持场景不含 S_NODE_ON_HOVER_MOVE；`ui_input_event.cpp:3134-3159` | AC-5.6 |
| R-25 | 边界 | current/last/move vector 被清空或通用 ClearResults 执行 | Pen Hover map key 和三张专用 map 仍可保留 | 生命周期依赖后续事件覆盖；`event_manager_pen.cpp:54-63`、`event_manager.cpp:2445-2452` | AC-5.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1~R-4 | Core/Pipeline 单测 | Pen Hover 判定与入口分流 |
| VM-2 | AC-2.1~2.5, R-5~R-8 | InputEventHub 单测 | Mouse hit-test、回调存在性过滤、双目标收集 |
| VM-3 | AC-3.1~3.7, R-9~R-14 | EventManager 单测 | last/current 差分、传播停止、dispatch length |
| VM-4 | AC-4.1~4.6, R-15~R-18, R-23 | EventManager 单测 | event.id 查找、move 顺序、IN/OUT move 派发、stopPropagation、HoverInfo 字段 |
| VM-5 | AC-5.1~5.7, R-19~R-22, R-24~R-25 | Pipeline/NDK 集成测试 | 落笔退出、API 版本、Native 数据转换、传播不对称、map 生命周期 |

## API 变更分析

> 本特性仅补录现有 API，不新增或修改公开接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `CommonMethod.onHover` | Public ArkTS | `(isHover: boolean, event: HoverEvent) => void` | `this` | N/A | 注册进入/退出悬停回调 | AC-3.4~3.7, AC-5.3 |
| `CommonMethod.onHoverMove` | Public ArkTS | `(event: HoverEvent) => void` | `this` | N/A | 注册悬停移动回调 | AC-4.1~4.5, AC-5.3 |
| `NODE_ON_HOVER_MOVE` | Public NDK | Node event listener | ArkUI_UIInputEvent callback | N/A | API 15+ Pen Hover Move 事件 | AC-5.4, AC-5.5 |
| `NODE_ON_HOVER_EVENT` | Public NDK | Node event listener | ArkUI_UIInputEvent callback | N/A | API 17+ Hover 进入/离开事件 | AC-5.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录现有能力 | 无迁移要求 | 全部 |

## 接口规格

### 接口定义

**ArkTS onHover / onHoverMove**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onHover(value: ((isHover: boolean, event: HoverEvent) => void) \| undefined): this` |
| 函数签名 | `onHoverMove(value: ((event: HoverEvent) => void) \| undefined): this` |
| 返回值 | `this`，用于链式调用 |
| 开放范围 | Public ArkTS |
| 错误码 | N/A |
| 关联 AC | AC-2.2~5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | callback/undefined | 否 | undefined | undefined 表示不注册或清除回调 |
| isHover | boolean | 回调参数 | 无 | true 表示进入，false 表示退出 |
| event | HoverEvent | 回调参数 | 无 | Pen Hover pressure 当前为 0；姿态字段见 Feat-01 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Pen 首次命中组件 | onHover(true, event) | AC-3.5 |
| 2 | Pen 离开组件或落笔清理 | onHover(false, event) | AC-3.4, AC-5.1 |
| 3 | Pen 在组件内悬停移动 | onHoverMove(event) | AC-4.3~4.5 |

**NDK Node Hover Events**

| 属性 | 值 |
|------|-----|
| 函数签名 | `NODE_ON_HOVER_MOVE = 29`、`NODE_ON_HOVER_EVENT = 27` |
| 返回值 | 通过 ArkUI_NodeEvent 回调交付 ArkUI_UIInputEvent |
| 开放范围 | Public NDK |
| 错误码 | 由节点事件注册接口定义 |
| 关联 AC | AC-5.4, AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | ArkUI_NodeHandle | 是 | 无 | 节点有效并注册相应事件 |
| eventType | ArkUI_NodeEventType | 是 | 无 | Hover Move API 15+；Hover Event API 17+ |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | API 15+ Pen Hover Move | 回调获得 tool/坐标/tilt/roll，pressure=0 | AC-5.4, AC-5.5 |
| 2 | API 17+ Hover Enter/Exit | 回调获得进入/离开状态 | AC-5.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；本规格记录现有 Pen Hover 专用派发链。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；last/current/move map 为进程内瞬态状态。
- **最低支持版本:** NDK Hover Move API 15；NDK Hover Event API 17；ArkTS 版本需 canonical SDK 复核。
- **API 版本号策略:** 以 `native_node.h` 的 `@since 15/17` 为准；ArkTS 仅记录仓内现有签名。
- **实现差异:** Pen Hover 命中测试使用 MOUSE hitTestType，但 inputEventType 仍为 TOUCH_SCREEN；enter/exit 状态按 event identity 保存，move 状态按 event.id 保存。
- **传播差异:** ArkTS onHover/onHoverMove 和 NDK Hover Event 可将 stopPropagation 写回，NDK Hover Move 当前不回写。
- **事件类型差异:** Hover Move 派发未限制为 LEVITATE_MOVE，IN/OUT 事件在存在 move 目标时也可能触发回调。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 专用入口分流 | 仅 PEN + LEVITATE 三类型进入 Pen Hover 链 | AC-1.1~1.4 |
| Mouse 型命中 | Pen Hover 复用组件 Mouse hit-test/response region，不复用普通 Touch 手势派发 | AC-1.3, AC-2.1 |
| 目标按回调过滤 | 只有注册 Pen onHover/onHoverMove callback 的 HoverEventTarget 进入对应链 | AC-2.2~2.5 |
| 差分与拦截一致性 | last/current 差分必须尊重上一轮传播停止长度，避免向从未收到 enter 的节点发送不匹配事件 | AC-3.4~3.6 |
| UI 线程执行 | PipelineContext::OnPenHoverEvent 明确在 UI 线程运行 | 全部 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每个 Pen Hover 事件只执行一次目标树命中和一次 enter/exit + move 派发 | 性能跟踪 | `pipeline_context.cpp:5074-5076` |
| 功耗 | 无轮询或定时器，事件驱动 | 源码审查 | Pipeline 仅在输入到达时执行 |
| 内存 | 每个活动事件身份保存 last/current 目标链，每个活动 event.id 保存 move 链 | 单测/内存检查 | `event_manager.h:570-572` |
| 安全 | 无新增权限；目标回调仅接收当前事件数据 | API 审查 | 无 IPC/持久化 |
| 可靠性 | 落笔时可合成退出，传播停止后退出链与有效 enter 链保持一致 | 场景测试 | AC-3.6, AC-5.1 |
| 可测试性 | EventManager map 和 HoverEventTarget 可构造验证 | 单元测试 | `event_manager_pen_test_ng.cpp` |
| 自动化维测 | 输入追踪日志记录 Pen Hover 类型、event id、finger id 和 inject 标记 | 日志测试 | `pipeline_context.cpp:5055-5063` |
| 定界定位 | enter/exit 与 move 分别使用独立 map，可按 identity/id 定位 | Dump/单测 | R-9~R-18 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 仅在硬件和输入服务产生 Pen LEVITATE 事件时可用 | 不支持悬停的设备不触发回调 | 真机测试 | IsPenHoverEvent 条件 |
| 平板 | 主要支持形态，完整命中与派发链 | 多层组件和 response region 均需验证 | 真机测试 | EventManager/InputEventHub |
| 折叠屏 | 窗口与坐标变化不改变目标差分规则 | 折叠前后重新命中，以当前节点树为准 | 折叠态测试 | 每事件重新 TouchTest |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | Pen Hover 与 Accessibility Hover 使用不同入口和目标链 | AC-1.2 |
| 大字体 | 否 | 不直接处理字体；布局改变会影响命中区域 | 组件布局变化 |
| 深色模式 | 否 | 不定义 Hover 视觉样式 | 无 |
| 多窗口/分屏 | 是 | 窗口移出和目标重新命中必须关闭旧 hover 状态 | AC-5.1, AC-5.2 |
| 多用户 | 否 | 无用户态差异 | 无 |
| 版本升级 | 是 | NDK API 15/17 有版本边界 | AC-5.4 |
| 生态兼容 | 是 | onHover 同时服务鼠标与 Pen；Pen 路径 pressure 固定为 0 | AC-5.3, AC-5.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 手写笔悬停命中与事件派发
  Scenario: Pen 首次进入组件
    Given 组件注册 onHover 和 onHoverMove
    And 输入事件 sourceTool 为 PEN 且 type 为 LEVITATE_IN_WINDOW
    When Pipeline 执行 PenHoverTest 和派发
    Then 组件收到 onHover(true)
    And 本次移动目标可收到 onHoverMove

  Scenario: Pen 从子节点移动到父节点区域
    Given last 目标链包含父节点和子节点
    And current 目标链只包含父节点
    When 派发 enter/exit 差分
    Then 子节点收到 onHover(false)
    And 父节点不重复收到 onHover(true)

  Scenario: Hover Move 停止传播
    Given 目标链包含内层和外层节点
    When 内层 onHoverMove 设置 stopPropagation
    Then 外层节点不收到本次 onHoverMove

  Scenario: Enter 事件沿 Move 链派发
    Given 当前命中节点注册 onHoverMove
    When Pipeline 收到 LEVITATE_IN_WINDOW
    Then Pipeline 在 onHover 进入派发后仍执行 onHoverMove 派发

  Scenario: Pen 落笔关闭悬停
    Given 当前节点保持 hover 状态
    When 收到 sourceTool=PEN、type=DOWN、force>0 的事件
    Then Pipeline 合成移出并向当前目标派发 onHover(false)
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 覆盖入口、命中、目标收集、差分、移动、传播停止和移出清理
- [x] 不展开手写服务、触控拦截和文本编辑命令
- [x] 每个 AC 与规则、验证方式和源码证据可追溯
- [x] 规则具备可复现条件、可观测结果和明确边界
- [x] ArkTS canonical SDK 缺失风险已显式记录

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Pen Hover 从 AceContainer 到 PipelineContext EventManager FrameNode InputEventHub HoverEventTarget 的命中和派发链"
  - repo: "openharmony/arkui_ace_engine"
    query: "lastPenHoverResultsMap curPenHoverResultsMap lastPenHoverDispatchLength 的 enter exit 差分和拦截语义"
  - repo: "openharmony/arkui_ace_engine"
    query: "onHover onHoverMove NODE_ON_HOVER_EVENT NODE_ON_HOVER_MOVE 的 ArkTS NDK 数据转换和版本"
```

**关键文档：** `frameworks/core/common/event_manager_pen.cpp`、`frameworks/core/pipeline_ng/pipeline_context.cpp`、`frameworks/core/components_ng/event/input_event.cpp`、`frameworks/core/event/mouse_event.cpp`。
