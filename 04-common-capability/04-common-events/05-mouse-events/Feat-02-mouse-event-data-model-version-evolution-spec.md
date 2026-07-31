# 特性规格

> Func-04-04-05-Feat-02 鼠标事件数据模型与版本演进：固化 `MouseEvent` 从 MMI 输入、核心数据对象、Dynamic/Static ArkTS、BuilderNode 定向投递到 Node C-API/克隆事件的字段语义、坐标体系和版本边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 鼠标事件数据模型与版本演进 |
| 特性编号 | Func-04-04-05-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 8–26.0.0、Node C-API 12–26.0.0、Static API 23–26.0.0、BuilderNode/克隆事件 API 20–26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 存量 `MouseEvent` 数据模型规格 | 覆盖字段、枚举、坐标、历史点、BuilderNode、Node C-API、克隆/回投和版本兼容 |
| ADDED | SDK 与源码偏差记录 | 仅记录当前实现风险，不修改产品源码、公开 API、ABI、错误码或默认行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/05-mouse-events/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:10154`、`enums.d.ts:760` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:4976`、`enums.static.d.ets:586` | 已核对 |
| BuilderNode SDK | `interface/sdk-js/api/arkui/BuilderNode.d.ts:540`、`BuilderNode.static.d.ets:297` | 已核对 |
| Native SDK | `interfaces/native/ui_input_event.h:234`、`:843`、`:1127`、`:1294`、`:1361` | 已核对 |
| 核心数据实现 | `frameworks/core/event/mouse_event.h:36`、`mouse_event.cpp:199` | 已核对 |
| 平台转换实现 | `adapter/ohos/entrance/mmi_event_convertor.cpp:537` | 已核对 |

## 用户故事

### US-1: 按 API 版本获得稳定的数据字段

**作为** 同时维护多个 API 版本的 ArkUI 应用开发者，
**我想要** 明确每个鼠标字段和枚举动作的开放版本，
**以便** 不访问当前运行版本尚未提供或已经废弃的数据。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Dynamic API 8+ 接收 `MouseEvent` THEN `button`、`action`、`x`、`y`、`screenX`、`screenY` 和 `stopPropagation` 可用 | 正常 |
| AC-1.2 | WHEN Dynamic API 10+ 接收 `MouseEvent` THEN `displayX/Y` 与 `windowX/Y` 可用；WHEN 使用 `screenX/Y` THEN 其按照 API 10 废弃契约等价指向窗口坐标语义 | 边界 |
| AC-1.3 | WHEN Dynamic API 15+ 接收 `MouseEvent` THEN `rawDeltaX/Y` 与 `pressedButtons` 可用 | 正常 |
| AC-1.4 | WHEN Dynamic API 18+ 使用动作枚举 THEN `CANCEL=13` 可用；WHEN Dynamic API 23+ THEN `ENTER_WINDOW=4`、`LEAVE_WINDOW=5` 可用 | 边界 |
| AC-1.5 | WHEN Dynamic API 20+ 接收 `MouseEvent` THEN `globalDisplayX/Y` 可用；WHEN API 24+ THEN `eventHandleId` 可用；WHEN API 26+ THEN `getCurrentLocalPosition()` 与 `getHistoricalPoints()` 可用 | 正常 |
| AC-1.6 | WHEN Static API 23+ 接收 `MouseEvent` THEN基础字段、`rawDeltaX/Y` 和 `pressedButtons` 按 Static 基线提供；WHEN API 24+ THEN `eventHandleId` 声明可用；WHEN API 26+ THEN `globalDisplayX/Y`、实时局部坐标和历史点声明可用 | 正常 |

### US-2: 区分四类坐标与实时局部位置

**作为** 需要在组件、窗口、屏幕和全局显示之间换算位置的开发者，
**我想要** 获得语义明确的坐标字段，
**以便** 在节点发生变换或窗口移动后仍能选择正确的坐标来源。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 平台 PointerEvent 转换为 MouseEvent THEN `x/y` 保存窗口输入位置，`screenX/Y` 保存当前显示坐标，`globalDisplayX/Y` 保存全局显示坐标 | 正常 |
| AC-2.2 | WHEN MouseEventTarget 为目标节点构造 MouseInfo THEN `x/y` 经目标节点变换形成回调时的局部坐标快照，`windowX/Y`、`displayX/Y`、`globalDisplayX/Y` 分别来自全局、屏幕和全局显示位置 | 正常 |
| AC-2.3 | WHEN ArkTS 读取坐标字段 THEN px 内部值按当前 density 转换为 vp；WHEN Node C-API 节点启用 PX 单位 THEN 按 px 打包，否则按 density 转为 vp | 边界 |
| AC-2.4 | WHEN 节点在事件产生后发生位移、缩放或其他几何变换且调用 `getCurrentLocalPosition()` THEN 返回值基于节点当前变换重新计算，不要求等于事件快照 `x/y` | 正常 |
| AC-2.5 | WHEN 实时位置 getter、事件 peer 或运行环境无效 THEN Dynamic 返回 `undefined`，Static accessor 使用零坐标错误值或 Static 声明规定的可选结果 | 异常 |

### US-3: 获得动作、按键和原始移动量

**作为** 实现多按键交互或高精度鼠标轨迹的开发者，
**我想要** 区分当前动作、触发按键、同时按下按键和硬件移动量，
**以便** 不混用不同通道的数值表示。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 通过 Dynamic、Static 或 Node C-API 读取 `MouseButton`/`MouseAction` THEN 按各自公开枚举语义解释，不以跨通道裸整数相等作为兼容条件 | 边界 |
| AC-3.2 | WHEN `rawDeltaX/Y` 在 Dynamic API 15–25 返回 THEN 其语义为硬件原始移动量除以系统显示缩放比；WHEN Dynamic API 26+ 返回 THEN 其为未按物理像素或逻辑像素换算的硬件原始移动数据 | 边界 |
| AC-3.3 | WHEN MMI PointerEvent 提供 raw dx/dy THEN 当前实现将其写入 MouseEvent，并由 MouseInfo、Dynamic/Static 回调和 Node C-API 继续传递 | 正常 |
| AC-3.4 | WHEN MMI PointerEvent 提供 pressed set THEN `pressedButtonsArray` 按集合逐项生成并作为 ArkTS `pressedButtons` 数据源 | 正常 |
| AC-3.5 | WHEN 当前 MMI 转换计算标量 `pressedButtons` THEN 因其从 0 开始使用按位与，该标量保持 0；该现状不改变独立数组的内容 | 边界 |
| AC-3.6 | WHEN Node C-API 获取单一 `button` THEN 内部位值被转换为公开连续枚举；WHEN 获取 `pressedButtons` 数组 THEN 当前实现原样返回内部位值，调用方不得假定其与单一 button getter 的数值域一致 | 边界 |

### US-4: 获取同帧历史移动点

**作为** 绘制和轨迹分析应用开发者，
**我想要** 获取当前帧内被合并的鼠标移动点，
**以便** 在降低回调频率的同时保留轨迹细节。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 同一 FrameNode、同一 pointer id 在一次 VSync 前积累多个普通 MOVE THEN 最后有效点作为主 MouseEvent 分发，同帧其余样本按时间顺序进入 `history` | 正常 |
| AC-4.2 | WHEN 终止动作到达前存在尚未分发的同 id MOVE THEN 补偿事件以最后 MOVE 为主点，并携带收集到的历史样本后再处理终止动作 | 恢复 |
| AC-4.3 | WHEN MouseEventTarget 转换历史点 THEN 每一点包含局部、窗口、屏幕、全局显示坐标和时间戳，局部坐标按目标节点完成变换 | 正常 |
| AC-4.4 | WHEN Dynamic API 26+ 在有效 onMouse 回调中调用 `getHistoricalPoints()` THEN 返回 `MouseHistoricalPoint[]`；WHEN没有历史点 THEN 返回空数组 | 正常 |
| AC-4.5 | WHEN Static API 26+ 调用历史点访问器 THEN 返回对应数组；WHEN peer/运行环境无效 THEN 按 Static 契约返回 `undefined`/空 optional | 异常 |
| AC-4.6 | WHEN Node C-API 读取鼠标历史点 THEN `pointerIndex` 仅允许 0，历史坐标和时间通过 API 12+ 通用 PointerEvent getter 获取，全局显示历史坐标从 API 20+ 获取；Node 打包最多保留 20 点 | 边界 |

### US-5: 使用 BuilderNode 构造和定向投递鼠标事件

**作为** BuilderNode、动态内容或事件转发框架开发者，
**我想要** 构造完整 MouseEvent 并携带唯一 handle 定向投递，
**以便** 目标子树可以维持一条完整的鼠标事件序列。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN Dynamic BuilderNode 接收输入对象 THEN 含 `touches` 数组时按 TouchEvent 处理，含数值 `scrollStep` 时按 AxisEvent 处理，其余对象按 MouseEvent 解析 | 边界 |
| AC-5.2 | WHEN MouseEvent 对象被 BuilderNode 解析 THEN source、sourceTool、timestamp、deviceId、targetDisplayId、四类坐标、button、action、rawDelta、pressedButtons 和 eventHandleId 被写入核心 MouseEvent | 正常 |
| AC-5.3 | WHEN Dynamic API 20+ 调用 `postInputEvent` THEN MouseEvent 以 pass-through 方式投递目标节点；WHEN API 24+ 调用 `postInputEventWithStrategy` THEN competitionStrategy 仅接受 0/1，缺省或非法值按 0 处理 | 正常 |
| AC-5.4 | WHEN策略投递的 `eventHandleId=0` THEN实现使用 `event.id+100000`；WHEN `eventHandleId>0` THEN增加 100000 后作为 MouseEvent.id；WHEN值为负数或大于 `INT_MAX-100000` THEN投递返回 false | 边界 |
| AC-5.5 | WHEN相同目标和 id 在未 RELEASE/CANCEL 前再次投递 PRESS 且 handle 已进入 pass-through 分段 THEN系统先生成 CANCEL 清理旧序列，再接受新 PRESS | 恢复 |
| AC-5.6 | WHEN Static SDK API 24+ 读写 `eventHandleId` THEN公开契约要求该字段可用；WHEN经过当前 checked-in `MouseEventAccessor` THEN getter 返回空 optional 且 setter 无操作，该偏差记录为风险 | 异常 |

### US-6: 通过 Node C-API 读取、克隆和回投数据

**作为** NativeNode/NDK 开发者，
**我想要** 读取 MouseEvent、构造或克隆事件并投递到指定节点，
**以便** Native 交互和测试工具可以复用 ArkUI 输入管线。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN `NODE_ON_MOUSE` 产生 ArkUI_UIInputEvent THEN Node modifier 同步打包动作、按键、坐标、rawDelta、pressedButtons、历史点、eventHandleId 和底层 PointerEvent | 正常 |
| AC-6.2 | WHEN C getter 接收空事件、错误类型、空输出缓冲区或不足长度 THEN 返回对应参数错误、不支持或缓冲区不足错误码，不修改公开 ABI | 异常 |
| AC-6.3 | WHEN API 24+ 使用 `CreateClonedPointerEvent` 克隆鼠标事件 THEN action、button、坐标、rawDelta、pressedButtons、handle 和 raw PointerEvent 被复制；当前 clone 不复制 history 和 pressedKeyCodes | 边界 |
| AC-6.4 | WHEN API 24+ 对用户创建/克隆的 mouse event 调用 `SetMouseButton`、`SetRawDeltaX/Y`、`SetPressedButtons` 或 `SetHandleId` THEN合法参数写入事件；WHEN事件并非用户创建/克隆、类型不支持或值越界 THEN返回相应错误码 | 正常 |
| AC-6.5 | WHEN当前 `SetPressedButtons` 以新 length 写入数组 THEN数组内容被替换但 `pressedButtonsLength` 保持旧值；WHEN元素非法 THEN指针清空但旧长度仍保留，该现状记录为高风险 | 边界 |
| AC-6.6 | WHEN `PostClonedEventWithStrategy` 回投鼠标事件 THEN其重建 MouseEvent 并走 pass-through/post-event 管线，但内部 `isInjected` 保持默认 false | 边界 |
| AC-6.7 | WHEN使用旧 `OH_ArkUI_PointerEvent_CreateClonedEvent` THEN当前实现仅处理 TouchEvent，不按新 API 24 鼠标克隆能力解释 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.6 | R-1~R-4 | 已有实现 | canonical SDK 核对 | `common.d.ts:10154`、`common.static.d.ets:4976` |
| AC-2.1~AC-2.5 | R-5~R-7 | 已有实现 | 源码追溯/Accessor UT | `mmi_event_convertor.cpp:559`、`mouse_event.cpp:199`、`mouse_event_accessor_test.cpp:171` |
| AC-3.1~AC-3.6 | R-8~R-11 | 已有实现 | SDK/Adapter/C-API UT | `enums.d.ts:760`、`mmi_event_convertor.cpp:602`、`ui_input_event_test_two.cpp:1038` |
| AC-4.1~AC-4.6 | R-12~R-15 | 已有实现 | Pipeline/Native UT | `pipeline_context_test_ng_eight.cpp:754`、`ui_input_event.cpp:2475` |
| AC-5.1~AC-5.6 | R-16~R-19 | 已有实现 | BuilderNode/PostEvent UT | `js_base_node.cpp:435`、`post_event_manager_test_ng.cpp:3276` |
| AC-6.1~AC-6.7 | R-20~R-24 | 已有实现 | C-API UT/源码追溯 | `node_common_modifier.cpp:13377`、`oh_arkui_pointerevent_tdd_test.cpp:971` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Dynamic API 8/10/15/20/24/26 分别达到字段开放点 | 仅在对应版本及以后暴露该组字段 | API 18/23 还分别增加 CANCEL 和窗口动作 | AC-1.1~AC-1.5 |
| R-2 | 边界 | Dynamic API 10+ 读取 `screenX/Y` | 字段仍存在但标记废弃，迁移到 `windowX/Y` | Static 不声明 `screenX/Y` | AC-1.2 |
| R-3 | 行为 | Static API 23/24/26 达到开放点 | 基础数据、handle、全局显示/实时位置/历史点依版本提供 | Static 与 Dynamic 起始版本不对齐 | AC-1.6 |
| R-4 | 边界 | 使用继承自 BaseEvent 的 target、timestamp、source、pressure、tool、device/display 等字段 | 按 BaseEvent 对应版本提供 | Axis 字段不将 AxisEvent 纳入本 Feat | AC-1.1, AC-1.6 |
| R-5 | 行为 | MMI PointerEvent 转换 | 写入窗口、显示、全局显示、raw delta、动作、按键、设备和时间数据 | 缺少 PointerItem 时返回，不生成完整事件 | AC-2.1 |
| R-6 | 行为 | MouseEventTarget 构造 MouseInfo | 目标节点变换生成局部快照，保留其他坐标系 | ArkTS 转 vp；Native 根据 UsePXUnit 选择 px/vp | AC-2.2, AC-2.3 |
| R-7 | 边界 | 调用 `getCurrentLocalPosition()` | 有 getter 时使用当前节点变换重新计算，否则退回事件局部快照 | 无效对象按通道返回 undefined/零值 | AC-2.4, AC-2.5 |
| R-8 | 边界 | 跨 Dynamic/Static/C-API 传递按键或动作 | 以名称语义转换，不承诺裸整数一致 | Static Hover 与 ENTER_WINDOW 同值 4 | AC-3.1 |
| R-9 | 边界 | Dynamic API 15–25 与 26+ 读取 rawDelta | 15–25 为原始量除显示缩放比；26+ 为硬件原始量 | Static SDK 未记载该切换 | AC-3.2, AC-3.3 |
| R-10 | 行为 | MMI pressed set 非空 | 逐项生成 `pressedButtonsArray` 并传给 MouseInfo | 列表顺序来自 `std::set` 遍历 | AC-3.4 |
| R-11 | 边界 | 当前实现计算 pressedButtons 标量或 Node C 列表 | 标量保持 0；C 列表原样暴露内部位值 | 单一 button getter 有显式转换 | AC-3.5, AC-3.6 |
| R-12 | 行为 | 同帧相同 id 有多个普通 MOVE | 主事件取最后有效点，其他点进入 history | pass-through MOVE 不进入该队列 | AC-4.1 |
| R-13 | 恢复 | 终止动作前存在未处理 MOVE | 补偿分发携带 history 的最后 MOVE | 仅收集相同 pointer id | AC-4.2 |
| R-14 | 行为 | ArkTS 访问 MouseEvent history | 输出九个字段：四类坐标各 x/y 加 timestamp | Dynamic 有效对象无历史返回空数组 | AC-4.3~AC-4.5 |
| R-15 | 边界 | Node C-API 读取鼠标 history | pointerIndex 必须为 0，最多打包 20 点 | 基础 history getter API 12，全局显示 history API 20 | AC-4.6 |
| R-16 | 边界 | BuilderNode 判断 InputEventType | touches→Touch、scrollStep→Axis、其余→Mouse | 缺少 Mouse 必需字段时使用 MouseEvent 默认值 | AC-5.1, AC-5.2 |
| R-17 | 行为 | BuilderNode 投递 MouseEvent | 设置 passThrough/postEventNodeId 后重入目标节点 Pipeline | 普通接口 Dynamic API 20，策略接口 API 24 | AC-5.3 |
| R-18 | 边界 | 策略投递处理 handle | 0 使用 id+100000；正值加 100000；越界返回 false | 最大合法输入为 `INT_MAX-100000` | AC-5.4 |
| R-19 | 恢复 | 同 handle 序列发生重复 PRESS | 生成 CANCEL 清理旧序列后继续 | Static handle accessor 当前为空实现并列为偏差 | AC-5.5, AC-5.6 |
| R-20 | 行为 | NODE_ON_MOUSE 同步回调 | ArkUIMouseEvent 指针在回调期间提供字段和 history | pressedButtons/history 指针生命周期限同步回调 | AC-6.1 |
| R-21 | 异常 | C getter/setter 参数无效 | 返回参数错误、不支持、非克隆或缓冲区不足错误码 | 不改变 ABI 和结构体布局 | AC-6.2, AC-6.4 |
| R-22 | 边界 | 克隆 MouseEvent | 复制 action/button/坐标/rawDelta/buttons/handle/raw pointer，不复制 history/pressedKeys | 旧 CreateClonedEvent 仅支持 Touch | AC-6.3, AC-6.7 |
| R-23 | 边界 | `SetPressedButtons` 改变数组长度或遇到非法元素 | 当前实现不更新/清零旧 length | getter/回投可能按陈旧长度读取 | AC-6.5 |
| R-24 | 边界 | PostCloned mouse 回投 | 走 pass-through/post-event，`isInjected` 保持 false | cloned/post 与平台 injected 不是同一标志 | AC-6.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.6, R-1~R-4 | SDK 静态检查 | `@since`、`@deprecated`、Dynamic/Static 字段矩阵 |
| VM-2 | AC-2.1~AC-2.3, R-5~R-6 | Adapter/MouseEvent Host UT | 四类坐标从 MMI 到 MouseInfo 的值和单位 |
| VM-3 | AC-2.4~AC-2.5, R-7 | Dynamic/Static Accessor UT | 节点变换后实时位置与快照差异、无效 peer 返回 |
| VM-4 | AC-3.1, R-8 | SDK + Converter 参数化 UT | 各通道枚举名称与数值映射 |
| VM-5 | AC-3.2~AC-3.3, R-9 | API 版本化集成测试 | API 25/26 rawDelta 缩放语义边界 |
| VM-6 | AC-3.4~AC-3.6, R-10~R-11 | MMI/Node C-API UT | pressed set、标量 0、列表值域与单 button 转换差异 |
| VM-7 | AC-4.1~AC-4.3, R-12~R-14 | Pipeline/MouseEvent Host UT | 主点选择、历史顺序、坐标变换和时间戳 |
| VM-8 | AC-4.4~AC-4.6, R-14~R-15 | Dynamic/Static/Native UT | 空历史、无效 peer、pointerIndex=0 和 20 点上限 |
| VM-9 | AC-5.1~AC-5.3, R-16~R-17 | BuilderNode 集成测试 | InputEventType 判别、字段解析、pass-through 投递 |
| VM-10 | AC-5.4~AC-5.5, R-18~R-19 | PostEventManager Host UT | handle=0、正值、负值、溢出、重复 PRESS/CANCEL |
| VM-11 | AC-5.6, R-19 | Static Accessor UT | SDK 声明与空 getter/setter 偏差可见 |
| VM-12 | AC-6.1~AC-6.2, R-20~R-21 | NativeNode/C-API UT | 同步结构体生命周期、错误码、缓冲区长度 |
| VM-13 | AC-6.3~AC-6.7, R-22~R-24 | C-API clone→mutate→post 集成测试 | history/keys 保真、length、isInjected 和旧 API 边界 |

## API 变更分析

> 本次是存量能力补录，不新增产品 API。下表按版本列出纳入规格的现有契约。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `MouseEvent` | Public | 事件字段/方法 | 事件对象 | N/A | Dynamic API 8、Static API 23 起的鼠标数据模型 | AC-1.1~AC-3.6 |
| `MouseEvent.getCurrentLocalPosition` | Public | 无 | `Coordinate2D`；异常通道可为 undefined/零值 | N/A | API 26 获取基于节点当前位置的局部坐标 | AC-2.4, AC-2.5 |
| `MouseEvent.getHistoricalPoints` | Public | 无 | `MouseHistoricalPoint[]`；Static 可为 undefined | N/A | API 26 获取同帧历史点 | AC-4.1~AC-4.5 |
| `BuilderNode.postInputEvent` | Public | `InputEventType` | `boolean` | N/A | Dynamic API 20、Static API 26 定向投递输入事件 | AC-5.1~AC-5.3 |
| `BuilderNode.postInputEventWithStrategy` | Public | event、可选 competitionStrategy | `boolean` | N/A | API 24 携竞争策略和 eventHandleId 投递 | AC-5.3~AC-5.6 |
| `OH_ArkUI_MouseEvent_GetMouseButton/GetMouseAction` | Public/NDK | `ArkUI_UIInputEvent*` | `int32_t` | 返回值 + last error | API 12 读取单一按键和动作 | AC-3.1, AC-3.6, AC-6.1 |
| `OH_ArkUI_MouseEvent_GetRawDeltaX/Y/GetPressedButtons` | Public/NDK | event、buttons buffer、length | float/int32_t | 0、参数错误、缓冲区不足 | API 15 读取 raw delta 与按键集合 | AC-3.2~AC-3.6, AC-6.2 |
| `OH_ArkUI_PointerEvent_GetHistory*` | Public/NDK | event、pointerIndex、historyIndex | size/time/coordinate | 默认值 + last error | API 12/20 读取历史点 | AC-4.6 |
| `OH_ArkUI_PointerEvent_CreateClonedPointerEvent/CreatePointerEvent` | Public/NDK | event/type、输出指针 | ArkUI_ErrorCode | 0、参数错误 | API 24 克隆或新建 Mouse/Touch/Axis 事件 | AC-6.3~AC-6.7 |
| `OH_ArkUI_ClonedEvent_SetMouseButton/SetRawDeltaX/Y/SetPressedButtons/SetHandleId` | Public/NDK | cloned event 与字段值 | ArkUI_ErrorCode | 0、参数错误、非克隆、不支持 | API 24 修改克隆/新建鼠标事件 | AC-6.4, AC-6.5 |
| `OH_ArkUI_PointerEvent_PostClonedEventWithStrategy` | Public/NDK | node、event、strategy | ArkUI_ErrorCode | 0、参数错误、非克隆、组件异常、无命中 | API 24 定向回投克隆事件 | AC-6.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `MouseEvent.screenX/screenY` | 废弃 | Dynamic API 10+ 窗口坐标读取 | 使用 `windowX/windowY` | AC-1.2 |
| `MouseEvent.rawDeltaX/rawDeltaY` | 变更 | Dynamic API 26 原始移动量 | 不再按屏幕 density 推导物理或逻辑像素；按硬件原始量处理 | AC-3.2, AC-3.3 |

## 接口规格

### 接口定义

**MouseEvent**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `interface MouseEvent extends BaseEvent`; Static: `interface MouseEvent extends BaseEvent` |
| 返回值 | N/A — 事件回调数据对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `button` | `MouseButton` | 是 | 通道定义的 None/默认值 | 以枚举名称解释，不跨通道持久化裸整数 |
| `action` | `MouseAction` | 是 | 通道定义的 unknown/none | Dynamic CANCEL 自 API 18，窗口动作自 API 23 |
| `x/y` | number/double | 是 | 0 | 组件局部坐标，ArkTS 单位 vp |
| `displayX/Y` | number/double | 依版本 | 0 | 当前显示坐标；Dynamic API 10+ |
| `windowX/Y` | number/double | 依版本 | 0 | 当前应用窗口坐标；Dynamic API 10+ |
| `globalDisplayX/Y` | optional number/double | 否 | undefined/0 | Dynamic API 20+，Static API 26+ |
| `rawDeltaX/Y` | optional number/double | 否 | undefined/0 | Dynamic API 15+；API 26 改变语义 |
| `pressedButtons` | optional `MouseButton[]` | 否 | 空数组/undefined | Dynamic API 15+，Static API 23+ |
| `eventHandleId` | optional number/int | 否 | 0/undefined | API 24；必须在重复策略投递时保持唯一 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 读取版本内已开放字段 | 返回对应坐标、动作或设备数据 | AC-1.1~AC-1.6 |
| 2 | 节点变换后读取实时局部位置 | 返回重新计算的位置 | AC-2.4 |
| 3 | API 25/26 读取 rawDelta | 分别遵循缩放前后语义 | AC-3.2 |
| 4 | 同帧多个 MOVE | 主点携带历史点访问器 | AC-4.1~AC-4.5 |

**BuilderNode.postInputEventWithStrategy**

| 属性 | 值 |
|------|-----|
| 函数签名 | `postInputEventWithStrategy(event: InputEventType, competitionStrategy?: CompetitionStrategy): boolean` |
| 返回值 | `boolean` — 投递/命中结果 |
| 开放范围 | Public |
| 错误码 | N/A；失败返回 false |
| 关联 AC | AC-5.1~AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | `TouchEvent | MouseEvent | AxisEvent` | 是 | 无 | MouseEvent 需提供正确窗口 px 坐标和完整动作序列 |
| competitionStrategy | `CompetitionStrategy` | 否 | 0 | 运行时仅接受 0/1，其他值按 0 |
| event.eventHandleId | `number/int` | 否 | 0 | 范围 `[0, INT_MAX-100000]`，每次转发需唯一 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | event 不是 Touch/Axis 特征对象 | 按 MouseEvent 解析并投递 | AC-5.1, AC-5.2 |
| 2 | 合法 handle | 增加 100000 后作为分发 id | AC-5.4 |
| 3 | 负数、溢出或递归目标 | 返回 false | AC-5.4 |
| 4 | 重复 PRESS | 生成 CANCEL 清理旧序列 | AC-5.5 |

**Node C-API MouseEvent 与克隆接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_MouseEvent_Get*`、`OH_ArkUI_PointerEvent_CreateClonedPointerEvent`、`OH_ArkUI_ClonedEvent_Set*`、`OH_ArkUI_PointerEvent_PostClonedEventWithStrategy` |
| 返回值 | 字段值或 `ArkUI_ErrorCode` |
| 开放范围 | Public/NDK |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR`、`PARAM_INVALID`、`BUFFER_SIZE_NOT_ENOUGH`、`NOT_CLONED_POINTER_EVENT`、`INPUT_EVENT_TYPE_NOT_SUPPORT`、PostCloned 专用错误 |
| 关联 AC | AC-3.6、AC-4.6、AC-6.1~AC-6.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | `ArkUI_UIInputEvent*` | 是 | 无 | getter 要求 C_MOUSE_EVENT_ID；setter/post 要求 isCreatedByUser |
| pressedButtons | `int32_t*` | 是 | 无 | getter 需要足够缓冲区；setter length 必须 > 0，元素范围 0..5 |
| historyIndex | `uint32_t` | 是 | 0 | 必须小于 historySize |
| pointerIndex | `uint32_t` | 是 | 0 | Mouse history 仅允许 0 |
| node | `ArkUI_NodeHandle` | 是 | 无 | PostCloned 要求有效目标节点 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 NODE_ON_MOUSE 回调 | 可同步读取打包字段和历史点 | AC-6.1 |
| 2 | 缓冲区不足 | 返回 BUFFER_SIZE_NOT_ENOUGH | AC-6.2 |
| 3 | 克隆后修改并回投 | 走 Mouse post-event 管线 | AC-6.3, AC-6.4, AC-6.6 |
| 4 | 修改 pressedButtons 长度 | 保留当前陈旧 length 行为并记录风险 | AC-6.5 |

## 兼容性声明

- **已有 API 行为变更:** 是。Dynamic API 10 废弃 `screenX/Y`；API 15 增加 rawDelta/pressedButtons；API 18 增加 CANCEL；API 20 增加 globalDisplay；API 23 增加窗口动作和 Static 基线；API 24 增加 handle/策略投递/新克隆接口；API 26 增加实时位置与 ArkTS 历史点，并改变 Dynamic rawDelta 语义。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；但 Dynamic、Static、内部 C++ 与 Node C-API 的鼠标枚举数值域不同，禁止跨通道直接持久化裸整数。
- **最低支持版本:** Dynamic API 8；Node C-API 12；BuilderNode Dynamic API 20；Static API 23；策略投递和新克隆 API 24。
- **API 版本号策略:** 外部契约以 canonical SDK `@since/@deprecated` 为准；源码偏差单列风险，不静默覆盖 SDK 契约。
- **历史点兼容:** ArkTS `MouseEvent.getHistoricalPoints` 自 API 26 开放；Node C-API 的通用 history getter 自 API 12 已声明支持鼠标，全局显示历史坐标自 API 20。
- **rawDelta 兼容:** API 15–25 与 API 26+ 不承诺相同数值尺度；Static SDK 当前未记录 API 26 切换说明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 契约优先级 | 外部 API 以 SDK 声明为契约，源码不一致进入风险表 | AC-1.1~AC-1.6, AC-5.6 |
| 数据分层 | MMI 数据只在 adapter 转换，core 使用 MouseEvent/MouseInfo，前端和 C-API只做通道适配 | AC-2.1~AC-6.7 |
| 坐标单位 | core 使用 px，ArkTS 输出 vp，Node C-API 按 UsePXUnit 选择 px/vp | AC-2.2~AC-2.4, AC-4.3 |
| 同步生命周期 | MouseInfo、ArkUIMouseEvent 指针、pressedButtons/history 临时数组只在同步回调期间有效 | AC-4.6, AC-6.1 |
| Feat 边界 | 注册、命中、传播属于 Feat-01；hover/hoverEffect 属于 Feat-03；本 Feat 负责字段和定向数据传输 | AC-1.1~AC-6.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 普通 MOVE 每帧每 pointer id 仅分发一个主点，其他样本通过 history 批量交付 | Pipeline Host UT | `pipeline_context.cpp:5333` |
| 功耗 | 不增加额外定时器，history 复用 VSync MOVE 队列 | 代码评审 | `pipeline_context.cpp:5319` |
| 内存 | Node C-API 单次回调最多打包 20 个鼠标历史点 | Native UT/边界测试 | `node_common_modifier.cpp:130,10846` |
| 安全 | 克隆接口必须校验 event、isCreatedByUser、事件类型和数组元素范围 | C-API UT | `ui_input_event.cpp:5246` |
| 可靠性 | eventHandleId 负数和加 100000 后溢出的输入必须拒绝 | PostEventManager UT | `post_event_manager.cpp:192` |
| 可测试性 | 每个 API 版本边界、坐标通道、历史点和克隆错误码有独立 VM | 规格追溯检查 | VM-1~VM-13 |
| 自动化维测 | PostEvent 错误继续使用 GeneralInteractionErrorReporter/InputTracking | 日志与 UT | `post_event_manager.cpp:529` |
| 定界定位 | SDK/源码偏差在风险表保留 file:line，不以文档任务修改源码 | 文档审查 | 本 Spec 风险条目 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 外接鼠标可产生 MouseEvent；历史点数量由设备报告频率决定 | 不保证每帧存在多个历史点 | 真机/空历史测试 | `common.d.ts:10405` |
| 平板 | 与手机字段和版本契约一致，通常更常见外接鼠标/触控板 | 触控板轴数据仍归 AxisEvent，不归本 Feat | 真机/输入路由测试 | `ace_view_ohos.cpp:103` |
| 折叠屏 | 折叠或窗口位置变化影响 display/globalDisplay 坐标值 | 坐标语义不变；多窗口移动后用正确坐标系 | 折叠/多窗口集成测试 | `mmi_event_convertor.cpp:569` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变无障碍悬停状态机；鼠标数据仅沿现有分发链交付 | Feat-03/无障碍功能域 |
| 大字体 | 否 | 不涉及字体布局 | N/A |
| 深色模式 | 否 | 不涉及颜色和主题 | N/A |
| 多窗口/分屏 | 是 | window、display、globalDisplay 必须保持不同坐标语义 | AC-2.1~AC-2.4 |
| 多用户 | 否 | 不持久化用户级数据 | N/A |
| 版本升级 | 是 | 升级到 API 26 后 rawDelta 数值尺度和新增方法需要兼容验证 | AC-1.5, AC-3.2 |
| 生态兼容 | 是 | Dynamic/Static/C 枚举裸整数不可直接互认；克隆接口存在保真边界 | AC-3.1, AC-6.3~AC-6.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 鼠标事件数据模型与版本演进
  作为 ArkUI 应用、BuilderNode 或 NativeNode 开发者
  我想要按 API 版本获得语义稳定的 MouseEvent 数据
  以便在不同前端和投递通道之间正确处理坐标、按键、历史点和事件序列

  Scenario Outline: API 版本字段开放
    Given 应用运行在 <通道> 的 <版本>
    When onMouse 回调读取 <字段>
    Then 字段可用性应为 <结果>

    Examples:
      | 通道 | 版本 | 字段 | 结果 |
      | Dynamic | API 8 | x/y | 可用 |
      | Dynamic | API 14 | rawDeltaX/Y | 不在公开契约内 |
      | Dynamic | API 15 | rawDeltaX/Y | 可用 |
      | Static | API 23 | globalDisplayX/Y | 不在公开契约内 |
      | Static | API 26 | globalDisplayX/Y | 可用 |

  Scenario: 节点变换后的实时局部坐标
    Given MouseEvent 已记录局部快照 x/y
    And 目标节点在回调期间发生几何变换
    When 调用 getCurrentLocalPosition
    Then 返回基于节点当前变换重新计算的坐标
    And 原始 x/y 快照不被修改

  Scenario Outline: rawDelta API 26 语义边界
    Given 鼠标硬件报告原始移动量 D 且显示缩放比为 S
    When Dynamic <版本> 读取 rawDelta
    Then 期望语义为 <结果>

    Examples:
      | 版本 | 结果 |
      | API 25 | D/S |
      | API 26 | D |

  Scenario: 同帧鼠标历史点
    Given 同一节点同一 pointer id 在一次 VSync 前收到三个普通 MOVE
    When Pipeline flush 鼠标队列
    Then 最后一个点作为主 MouseEvent
    And 前序样本按时间顺序由 getHistoricalPoints 返回

  Scenario: BuilderNode eventHandleId 分段
    Given MouseEvent eventHandleId 为 11
    When 调用 postInputEventWithStrategy
    Then 内部分发 id 为 100011
    And 相同序列使用 RELEASE 或 CANCEL 清理状态

  Scenario: Node C-API pressedButtons 值域
    Given 内部 pressedButtonsArray 包含 Middle 位值 4
    When 通过 OH_ArkUI_MouseEvent_GetPressedButtons 读取
    Then 当前实现返回数值 4
    And 不将其等同于单一 button getter 的公开 Middle 数值 3

  Scenario: 克隆事件保真边界
    Given 原始 mouse event 包含 history、pressedKeys 和 pressedButtons
    When 通过 CreateClonedPointerEvent 克隆并回投
    Then action、button、坐标、rawDelta、buttons 和 handle 被复制
    And 当前实现不复制 history 和 pressedKeys
    And 回投 MouseEvent 的 isInjected 保持 false
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（“快速”“稳定”“尽可能”等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "MouseEvent MouseInfo MMI conversion coordinates rawDelta pressedButtons history eventHandleId"
  - repo: "openharmony/arkui_ace_engine"
    query: "BuilderNode postInputEventWithStrategy cloned mouse event Node C API"
  - repo: "openharmony/interface_sdk-js"
    query: "Dynamic Static MouseEvent MouseHistoricalPoint API since deprecated"
```

**关键文档：** `specs/04-common-capability/04-common-events/05-mouse-events/design.md`、`interface/sdk-js/api/@internal/component/ets/common.d.ts`、`interface/sdk-js/api/arkui/component/common.static.d.ets`、`interfaces/native/ui_input_event.h`
