# 特性规格

> Func-04-04-03-Feat-04 自定义输入事件构造与分发：固化 BuilderNode/ReactiveBuilderNode 的 touch/mouse/axis 自定义投递，以及 Native 指针事件克隆、空白构造、字段编辑、销毁和带竞争策略的节点注入能力。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义输入事件构造与分发 (Custom Input Event Construction and Dispatch) |
| 特性编号 | Func-04-04-03-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 ArkTS API 11~26；静态 ArkTS API 23~26；Native API 15~26，API 11/15/20/22/23/24/26 存在能力边界 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | BuilderNode 自定义输入分发规格 | 补录动态/静态 BuilderNode、ReactiveBuilderNode 的 `postTouchEvent()`、`postInputEvent()` 和策略投递 |
| ADDED | Native 输入事件构造规格 | 补录 API 15 触摸克隆和 API 24 touch/mouse/axis 克隆、空白创建、销毁及所有权 |
| ADDED | Native 字段编辑规格 | 补录通用、触摸当前点、逐触点 setter 的类型、范围、索引和错误规则 |
| ADDED | Native 节点注入规格 | 补录 API 15 普通投递、API 24 竞争策略、坐标来源、序列校验和错误码 |
| ADDED | 独立 PostEvent 生命周期 | 补录独立命中结果、FlushEnd、pass-through 动作记录及三事件族清理 |
| ADDED | handle 与 Referee 分组 | 补录 100000 隔离域、独立/竞争 Referee 选择和共享清理 |
| ADDED | 实现偏差和生命周期风险 | 补录动态 pressure 解析、返回语义、克隆字段缺失、history 生命周期和来源校验偏差 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| 功能域设计 | `specs/04-common-capability/04-common-events/03-event-dispatch-intercept/design.md` | 与本 Spec 增量同步 |
| BuilderNode 动态 SDK | `interface/sdk-js/api/arkui/BuilderNode.d.ts:415-455,550-636,758-798` | 已核验 |
| BuilderNode 静态 SDK | `interface/sdk-js/api/arkui/BuilderNode.static.d.ets:220-243,285-355,383-448` | 已核验 |
| 动态 BuilderNode 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_base_node.cpp:327-432,443-583,743-815` | 已核验 |
| 静态 BuilderNode 桥接 | `frameworks/core/interfaces/native/implementation/builder_node_ops_accessor.cpp:158-261` | 已核验 |
| 投递管理与分发 | `frameworks/core/components_ng/manager/post_event/post_event_manager.cpp:28-145,389-458,581-731`；`frameworks/core/common/event_manager.cpp:528-569,1219-1259` | 已核验 |
| Native 公共契约 | `interfaces/native/ui_input_event.h:1361-1984,2133-2148`；`interfaces/native/native_type.h:1389-1399,1540-1559` | 已核验 |
| Native 创建与 setter | `interfaces/native/event/ui_input_event.cpp:4148-5551,5640-5798` | 已核验 |
| Native 注入实现 | `interfaces/native/event/ui_input_event.cpp:5577-5637,5801-5825`；`frameworks/core/interfaces/native/node/node_common_modifier.cpp:9362-9572,9697-9809` | 已核验 |

## 用户故事

### US-1: 通过 BuilderNode 转发原始触摸事件

**作为** 使用命令式节点树的 ArkUI 开发者，
**我想要** 将已有 `TouchEvent` 从 BuilderNode 中间节点向其子树转发，
**以便** 复用目标子树的触摸测试和手势处理能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态 BuilderNode API 11+ 或 ReactiveBuilderNode API 22+ 调用 `postTouchEvent(event)` THEN 同步返回 boolean 投递结果 | 正常 |
| AC-1.2 | WHEN 静态 BuilderNode API 23+ 或 ReactiveBuilderNode 26.0.0+ 调用 `postTouchEvent(event)` THEN 同步返回 boolean 投递结果 | 正常 |
| AC-1.3 | WHEN 调用方准备 `postTouchEvent` 坐标 THEN 使用 px，并自行合并 BuilderNode 相对父节点偏移和仿射变换；WHEN 目标为 Webview THEN SDK 允许直接转发；WHEN 参数包含 UIExtensionComponent THEN SDK 声明不支持 | 边界 |
| AC-1.4 | WHEN 动态入口的 node/参数、changedTouches、PipelineContext 或 PostEventManager 无效，或节点已 dispose THEN 返回 false 而不抛出业务异常 | 异常 |
| AC-1.5 | WHEN 动态旧链在未清理的 action 序列中再次收到相同 finger ID 和 timestamp THEN 返回 false；WHEN ID 不同或序列已由 UP/CANCEL 清理 THEN 不因 timestamp 相同而自动拒绝；静态路径不执行该去重函数 | 边界 |
| AC-1.6 | WHEN 投递返回 true THEN 当前实现表示目标子树存在命中结果或事件序列可继续处理，不保证某个应用回调显式消费了事件 | 边界 |
| AC-1.7 | WHEN 动态 `postTouchEvent` 解析 pressure THEN 当前实现检查 pressure 字段却把 sourceTool 数值写入 force；WHEN 静态桥解析 pressure THEN 使用事件 pressure | 边界 |

### US-2: 使用通用输入转发和竞争策略

**作为** 需要控制原手势与目标手势关系的 ArkUI 开发者，
**我想要** 使用通用输入转发及竞争策略投递 touch、mouse 或 axis 事件，
**以便** 在独立识别和共同竞争之间选择手势裁决方式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 动态 API 20+ 调用 `postInputEvent()` 传入含 touches 的对象 THEN 按触摸事件处理；WHEN 静态通道调用无策略 `postInputEvent()` THEN 以静态 SDK 标注的 API 26 为版本边界 | 正常 |
| AC-2.2 | WHEN 使用 `postInputEvent` 转发触摸事件 THEN 坐标按目标组件窗口坐标和 px 提供，并补齐 touches 以及 DOWN/UP 等完整序列；UIExtensionComponent 不支持 | 边界 |
| AC-2.3 | WHEN 动态或静态 API 24+ 调用 `postInputEventWithStrategy(event, strategy?)` THEN strategy 省略或为 DEFAULT 时按不竞争处理，COMPETITION 时按竞争处理 | 正常 |
| AC-2.4 | WHEN strategy 为 DEFAULT THEN 当前实现设置 `isNewReferee=true` 并使用独立裁决器；WHEN 为 COMPETITION THEN 设置 `isNewReferee=false` 并复用正常/上级裁决器 | 正常 |
| AC-2.5 | WHEN 策略接口对同一事件进行多次转发 THEN SDK 允许重复调用；WHEN 同一目标节点正在策略投递中发生重入 THEN PostEventManager 返回 false | 边界 |
| AC-2.6 | WHEN 动态通用入口的对象含 touches THEN 识别为 touch；ELSE WHEN 含 scrollStep THEN 识别为 axis；ELSE 按 mouse 解析 | 边界 |
| AC-2.7 | WHEN node、事件对象、PipelineContext、PostEventManager、必需 touches/changedTouches 或具体事件字段无效 THEN BuilderNode 通用入口返回 false | 异常 |

### US-3: 创建、克隆和销毁 Native 指针事件

**作为** Native ArkUI 开发者，
**我想要** 从回调事件克隆或从空白创建可编辑事件，
**以便** 在保持明确所有权的前提下构造后续投递数据。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN API 15+ 调用 `CreateClonedEvent` 传入 touch/C touch event THEN 创建独立 wrapper、复制当前实现列出的触摸字段与触点并把输出标记为 user-created；WHEN 传入其他事件类型 THEN 数值返回 0 而 latest status 记录 INPUT_EVENT_TYPE_NOT_SUPPORT | 边界 |
| AC-3.2 | WHEN API 24+ 调用 `CreateClonedPointerEvent` THEN 仅支持 touch、mouse、axis；WHEN event/output/payload/FullImpl 或事件类型无效 THEN 返回 PARAM_INVALID | 异常 |
| AC-3.3 | WHEN API 24+ 调用 `CreatePointerEvent` 从空白创建 THEN 仅支持 TOUCH、MOUSE、AXIS；新建 touch payload 固定分配 10 个触点槽并将 touchPointSize 设为 10，wrapper 的 inputType 未在该路径显式设置 | 边界 |
| AC-3.4 | WHEN API 15/24 创建或克隆成功 THEN `isCreatedByUser=true`；WHEN setter、销毁或投递接收非 user-created callback event THEN 返回 NOT_CLONED_POINTER_EVENT | 异常 |
| AC-3.5 | WHEN 调用匹配版本的 Destroy API 销毁 user-created event THEN 释放 wrapper、payload、触点、raw pointer 和已分配按键数组；销毁后调用方不得再次使用该指针 | 正常 |
| AC-3.6 | WHEN API 15 克隆的 touchPointSize/historySize 大于 0 但对应数组为空 THEN 返回 PARAM_INVALID；WHEN API 24 克隆同类 malformed payload THEN 当前入口未执行等价的数组一致性检查 | 边界 |
| AC-3.7 | WHEN 克隆 ArkUITouchEvent THEN 当前复制函数未复制 rollAngle、pressedKeyCodes/keyCodesLength、preventDefault 和 interceptResult 等字段，并将克隆 history 指向函数内栈数组；不得把该实现描述为所有字段均具备独立长期副本 | 边界 |

### US-4: 编辑 Native 克隆事件字段

**作为** 需要构造完整多点触摸序列的 Native 开发者，
**我想要** 编辑事件级、当前变化点和指定触点字段，
**以便** 明确生成可被目标节点处理的触摸数据。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 24+ 对 user-created touch/mouse/axis event 调用通用 setter THEN 可设置 action、source、tool、eventTime、deviceId、targetDisplayId、changed window/screen/globalDisplay position、handleId 和 pressedKeys | 正常 |
| AC-4.2 | WHEN API 24+ 对 user-created touch event 调用当前变化点 setter THEN 可设置 pressure、changedFingerId、tilt、roll、touchArea 和 InteractionHand | 正常 |
| AC-4.3 | WHEN API 24+ 使用有效 pointerIndex THEN 可设置指定触点的 pressure、fingerId、window/screen/globalDisplay position、touchArea、InteractionHand 和 pressedTime | 正常 |
| AC-4.4 | WHEN pressure/area/time/device/display/finger/handle 为负数、tilt 超出 `[-90,90]`、hand 超出 NONE~RIGHT、pointerIndex 小于 0 或不小于 touchPointSize，或 hover-move 设置 pressure THEN 返回 PARAM_INVALID | 异常 |
| AC-4.5 | WHEN setter 的 event 为空 THEN 返回 PARAM_INVALID；WHEN 事件非 user-created THEN 返回 NOT_CLONED_POINTER_EVENT；WHEN 触摸专用 setter 接收 mouse/axis THEN 返回 INPUT_EVENT_TYPE_NOT_SUPPORT；部分三类通用 setter 对未知 eventTypeId 返回 PARAM_INVALID | 异常 |
| AC-4.6 | WHEN API 15 使用旧 setter THEN 仅开放 local position、local position by index、action、changed finger ID 和 finger ID by index，且旧 action/finger setter 不执行 API 24 的完整范围校验 | 边界 |
| AC-4.7 | WHEN API 24 `SetPressedKeys` 接收非空数组且 length>0 THEN 释放旧按键数组、复制新数组并更新长度；WHEN 数组为空或 length<=0 THEN 返回 PARAM_INVALID | 边界 |

### US-5: 向 Native 节点注入克隆事件

**作为** 需要将构造事件发送给指定节点子树的 Native 开发者，
**我想要** 投递克隆触摸事件并选择手势竞争策略，
**以便** 获取可诊断的命中、节点状态和序列结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN API 15+ 调用 `PostClonedEvent` 投递 user-created touch event THEN 使用 action/current/multipoint 数据构造 TouchEvent，并以 nodeX/nodeY 作为内部当前和逐触点 x/y | 正常 |
| AC-5.2 | WHEN API 24+ 调用 `PostClonedEventWithStrategy` THEN 支持 touch/mouse/axis；触摸路径以 windowX/windowY 作为内部 x/y，并按 strategy 选择裁决器 | 正常 |
| AC-5.3 | WHEN 遵循 SDK 调用策略投递 THEN event 必须来自 API 24 的 `CreateClonedPointerEvent` 或 `CreatePointerEvent`；当前实现只检查 `isCreatedByUser`，因此 API 15 克隆触摸事件也可到达投递路径 | 边界 |
| AC-5.4 | WHEN event 为空 THEN 返回 401；WHEN event 非 user-created THEN 返回 180003；WHEN node/FullImpl/FrameNode/Context/PostEventManager 状态异常 THEN 返回 180004；WHEN 投递未得到成功结果 THEN 返回 180005 | 异常 |
| AC-5.5 | WHEN 策略投递因同节点重入、eventHandleId 负数或溢出、重复 DOWN、无 DOWN 的 MOVE/UP/CANCEL、缺少 EventManager 或子树无命中而返回 false THEN 对外均可能表现为 180005 | 边界 |
| AC-5.6 | WHEN 目标节点有效但目标子树没有可响应命中项 THEN 返回 180005；WHEN 目标节点本身无法形成有效 FrameNode/Pipeline/PostEventManager THEN 返回 180004 | 异常 |
| AC-5.7 | WHEN Native strategy 等于 COMPETITION=1 THEN 进入竞争模式；WHEN 为 DEFAULT=0 或其他非 1 数值 THEN 当前实现均按 DEFAULT 处理而不返回枚举参数错误 | 边界 |
| AC-5.8 | WHEN 投递 DOWN 后再投递 MOVE 及 UP/CANCEL THEN 序列可继续并在结束时清理；WHEN 先投递 MOVE/UP/CANCEL 或在活动序列重复 DOWN THEN 按既有序列规则拒绝、上报或生成取消处理 | 边界 |

### US-6: 隔离 PostEvent 命中与 pass-through 生命周期

**作为** ArkUI 自定义输入投递方，
**我想要** 让后置事件使用可清理的独立命中和动作状态，
**以便** 自定义投递不覆盖正常平台输入的目标链。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN 旧 `PostEvent` 的触摸 DOWN 对指定 UINode 命中 THEN 结果写入 `postEventTouchTestResults_`，识别器标记为 PostEvent 并加入独立 `postEventRefereeNG_` scope | 正常 |
| AC-6.2 | WHEN 旧 PostEvent 目标链不存在 THEN `PostEventDispatchTouchEvent` 返回 false，不调用目标回调 | 异常 |
| AC-6.3 | WHEN 旧 PostEvent 收到 UP/CANCEL THEN 清理该 ID 的独立 scope 和命中结果；WHEN Flush 结束 THEN 仅通知独立结果链中的目标 | 恢复 |
| AC-6.4 | WHEN pass-through 投递 touch/mouse/axis THEN 写入目标节点 ID、设置 `passThrough=true`，并从指定 FrameNode 子树进入对应 Pipeline 入口 | 正常 |
| AC-6.5 | WHEN pass-through Touch MOVE 到达 THEN 在当前调用内执行 FlushEnd 和 Dispatch，不进入普通 VSync MOVE 队列 | 边界 |
| AC-6.6 | WHEN touch 为 MOVE、mouse 为普通 MOVE 或 axis 为 UPDATE THEN 不保存为序列起止动作；WHEN 收到各事件族结束动作 THEN 按目标节点和事件 ID 清理记录 | 边界 |

### US-7: 使用 eventHandleId 组织竞争 Referee

**作为** 需要多次转发同一输入的框架开发者，
**我想要** 使用 handle 隔离或继承手势裁决状态，
**以便** 多次投递之间具有可预测的竞争关系。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN WithStrategy 的 `eventHandleId=0` THEN 内部使用 `event.id+100000`；WHEN handle 大于0 THEN 使用 `handle+100000` 并令事件 ID 等于转换后的 handle | 正常 |
| AC-7.2 | WHEN handle 小于0或大于 `INT_MAX-100000` THEN 投递返回 false，不进入目标 Pipeline | 异常 |
| AC-7.3 | WHEN `isNewReferee=true` THEN 按 `eventHandleId/100000` 创建或复用独立 GestureReferee | 正常 |
| AC-7.4 | WHEN `isNewReferee=false` 且分组键为0或1 THEN 使用主 Referee；WHEN 分组键大于1 THEN 继承前一组 Referee | 正常 |
| AC-7.5 | WHEN 分组键大于1但前一组 Referee 不存在 THEN 当前实现取得空 Referee，后续命中/分发提前退出 | 异常 |
| AC-7.6 | WHEN 清理 touch、mouse、axis 目标或按下指针 THEN 删除所有映射到同一 Referee 的 handle 分组，而非只删除当前整数 handle | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1, R-2 | 已有实现 | 动态/静态 SDK 与桥接测试 | `BuilderNode.d.ts:415-455,758-798`；`BuilderNode.static.d.ets:220-243,383-448` |
| AC-1.3~AC-1.4 | R-3, R-4 | 已有实现 | 坐标/非法上下文参数化测试 | `BuilderNode.d.ts:417-455`；`js_base_node.cpp:327-432` |
| AC-1.5~AC-1.7 | R-5~R-7 | 已有实现 | 动静态差异与字段解析测试 | `post_event_manager.cpp:28-91,722-726`；`js_base_node.cpp:348-350` |
| AC-2.1~AC-2.3 | R-8~R-10 | 已有实现 | SDK 版本和入口分类测试 | `BuilderNode.d.ts:550-636`；`BuilderNode.static.d.ets:285-355` |
| AC-2.4~AC-2.7 | R-11~R-14 | 已有实现 | referee/重入/非法字段测试 | `js_base_node.cpp:443-583`；`post_event_manager.cpp:94-145`；`event_manager.cpp:612-631` |
| AC-3.1~AC-3.3 | R-15~R-17 | 已有实现 | Native 创建类型与默认容量测试 | `ui_input_event.cpp:5374-5491,5640-5678` |
| AC-3.4~AC-3.6 | R-18~R-20 | 已有实现 | 所有权、销毁和 malformed payload 测试 | `ui_input_event.cpp:5494-5551,5652-5658` |
| AC-3.7 | R-21 | 已有实现 | clone 字段/ASan 生命周期测试 | `arkoala_api.h:358-401`；`node_common_modifier.cpp:9697-9809` |
| AC-4.1~AC-4.3 | R-22~R-24 | 已有实现 | setter API 分组参数化测试 | `ui_input_event.cpp:4148-5127` |
| AC-4.4~AC-4.5 | R-25, R-26 | 已有实现 | 边界和错误码矩阵测试 | `ui_input_event.cpp:4148-5127` |
| AC-4.6~AC-4.7 | R-27, R-28 | 已有实现 | API 15/24 对照和数组替换测试 | `ui_input_event.cpp:4904-4969,5701-5798` |
| AC-5.1~AC-5.3 | R-29~R-31 | 已有实现 | 两代注入坐标/来源测试 | `ui_input_event.cpp:5577-5637,5801-5825`；`node_common_modifier.cpp:9458-9572` |
| AC-5.4~AC-5.6 | R-32~R-34 | 已有实现 | Native 错误码与命中测试 | `node_common_modifier.cpp:9362-9395`；`post_event_manager.cpp:94-145` |
| AC-5.7~AC-5.8 | R-35, R-36 | 已有实现 | 策略枚举和事件序列测试 | `ui_input_event.cpp:5596-5599`；`post_event_manager.cpp:389-458` |
| AC-6.1~AC-6.3 | R-37~R-39 | 已有实现 | 独立 PostEvent 目标链单测 | `event_manager.cpp:528-570,1014,1596-1648` |
| AC-6.4~AC-6.6 | R-40~R-42 | 已有实现 | 三事件族 pass-through 单测 | `post_event_manager.cpp:56-304,615-731` |
| AC-7.1~AC-7.6 | R-43~R-48 | 已有实现 | handle/referee 分组测试 | `event_manager.cpp:202-248,612-630`；`post_event_manager.cpp:94-294` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 动态 Builder/Reactive 调用 postTouchEvent | 同步投递并返回 boolean | Builder API 11；Reactive API 22 | AC-1.1 |
| R-2 | 行为 | 静态 Builder/Reactive 调用 postTouchEvent | 同步投递并返回 boolean | Builder API 23；Reactive 26.0.0 | AC-1.2 |
| R-3 | 边界 | 准备 postTouchEvent 坐标 | 使用 px 和父坐标/仿射合成；UIExtension 不支持 | Webview SDK 声明已内部转换 | AC-1.3 |
| R-4 | 异常 | node、参数、changedTouches 或上下文无效 | 返回 false | 不抛业务异常 | AC-1.4 |
| R-5 | 边界 | 动态活动序列出现同 id+timestamp | 拒绝重复；不同 id 或已清理序列不受此条件限制 | 静态路径不调用 CheckPointValidity | AC-1.5 |
| R-6 | 边界 | BuilderNode 返回 true | 表示命中/序列可处理 | 不保证用户回调显式消费 | AC-1.6 |
| R-7 | 边界 | 动态旧桥解析 pressure | force 实际取 sourceTool 数值；静态取 pressure | 作为源码偏差记录 | AC-1.7 |
| R-8 | 行为 | postInputEvent 对象含 touches | 按 touch 事件处理 | 动态 API 20；静态 API 26 | AC-2.1 |
| R-9 | 边界 | postInputEvent 转发 touch | 使用窗口坐标、px、完整 touches 与 DOWN/UP 序列 | UIExtension 不支持 | AC-2.2 |
| R-10 | 行为 | API 24 策略投递 | DEFAULT/省略为不竞争，COMPETITION 为竞争 | dynamic/static | AC-2.3 |
| R-11 | 行为 | DEFAULT 或 COMPETITION | 分别创建独立 referee 或复用正常 referee | isNewReferee=true/false | AC-2.4 |
| R-12 | 边界 | 同事件重复策略转发或同节点重入 | SDK允许重复；同节点执行中重入返回 false | targetNodes_ 防重入 | AC-2.5 |
| R-13 | 边界 | 动态通用对象分类 | touches→touch，scrollStep→axis，否则 mouse | 按属性存在性判断 | AC-2.6 |
| R-14 | 异常 | 通用入口必需条件缺失 | 返回 false | node/context/manager/字段均需有效 | AC-2.7 |
| R-15 | 边界 | API 15 克隆事件 | 仅 touch；不支持类型返回值0、状态180006 | 输出标记 user-created | AC-3.1 |
| R-16 | 异常 | API 24 克隆 | 仅 touch/mouse/axis；非法输入返回401 | clone output/payload/FullImpl 必须有效 | AC-3.2 |
| R-17 | 边界 | API 24 空白创建 touch | 分配10个触点槽，touchPointSize=10 | inputType 未在实现中显式写入 | AC-3.3 |
| R-18 | 异常 | 非 user-created 事件调用受限 API | 返回180003 | 所有权以 isCreatedByUser 判断 | AC-3.4 |
| R-19 | 行为 | 销毁 user-created event | 释放关联内存 | 销毁后禁止复用 | AC-3.5 |
| R-20 | 边界 | malformed touch payload 被克隆 | API15拒绝数组/size不一致；API24无等价前置校验 | 不承诺非法内存输入安全 | AC-3.6 |
| R-21 | 边界 | 克隆 touch payload | 当前字段复制不完整且 history 指针指向栈内数组 | 作为生命周期/完整性风险 | AC-3.7 |
| R-22 | 行为 | API24 调用通用 setter | 修改三类事件共享字段 | 具体 eventTypeId 必须支持 | AC-4.1 |
| R-23 | 行为 | API24 调用触摸当前点 setter | 修改 actionTouchPoint/事件级高级字段 | 仅 touch | AC-4.2 |
| R-24 | 行为 | API24 调用 ByIndex setter | 修改 touchPointes[pointerIndex] | `0<=index<touchPointSize` | AC-4.3 |
| R-25 | 异常 | 数值/枚举/索引越界 | 返回401 | tilt `[-90,90]`、area/pressure/time/ID非负 | AC-4.4 |
| R-26 | 异常 | null、所有权或事件类型错误 | 返回401/180003/180006或通用setter的401 | 逐 API 保留现有错误差异 | AC-4.5 |
| R-27 | 边界 | API15 使用旧 setter | 仅5个 setter，校验弱于API24 | 不把API24规则追溯应用到旧接口 | AC-4.6 |
| R-28 | 边界 | 替换 pressedKeys | length>0 时深拷贝并替换旧数组 | null或length<=0返回401 | AC-4.7 |
| R-29 | 行为 | API15投递克隆 touch | nodeX/nodeY 进入内部 x/y | 旧 PostEvent 链 | AC-5.1 |
| R-30 | 行为 | API24策略投递 | 支持touch/mouse/axis；touch使用windowX/windowY | 策略 Post*EventWithStrategy 链 | AC-5.2 |
| R-31 | 边界 | 策略接口校验创建来源 | SDK只允许API24创建器；实现只看user-created标记 | API15 clone 可达但不作为外部承诺 | AC-5.3 |
| R-32 | 异常 | 注入参数/所有权/节点状态/投递失败 | 返回401/180003/180004/180005 | 错误码不得互换 | AC-5.4 |
| R-33 | 边界 | 多种内部失败令策略投递返回false | 对外可能统一为180005 | 语义宽于“无组件命中” | AC-5.5 |
| R-34 | 异常 | 节点无效或子树无命中 | 前者180004，后者180005 | FrameNode/Context/Manager 为状态边界 | AC-5.6 |
| R-35 | 边界 | strategy数值映射 | 仅1视为COMPETITION，其余按DEFAULT | 非法枚举当前不返回401 | AC-5.7 |
| R-36 | 边界 | 注入触摸序列 | DOWN→MOVE→UP/CANCEL；非法顺序被拒绝/上报/取消 | 结束事件清理序列状态 | AC-5.8 |
| R-37 | 行为 | 旧 PostEvent DOWN 命中 | 写入独立结果并登记独立 Referee scope | 不覆盖普通 touchTestResults | AC-6.1 |
| R-38 | 异常 | 旧 PostEvent 无目标链 | 返回 false 且不调用目标 | 不伪造成功消费 | AC-6.2 |
| R-39 | 恢复 | 旧 PostEvent UP/CANCEL 或 FlushEnd | 清理独立状态并只通知独立目标 | 普通结果链不参与 | AC-6.3 |
| R-40 | 行为 | pass-through 投递三类输入 | 设置目标 ID/passThrough 并进入目标子树 Pipeline | touch/mouse/axis 分别转换 | AC-6.4 |
| R-41 | 边界 | pass-through Touch MOVE | 当前调用内 FlushEnd 和 Dispatch | 不等待普通 VSync | AC-6.5 |
| R-42 | 边界 | 连续动作或结束动作 | 连续动作不入起止记录，结束动作清理对应记录 | 按事件家族区分动作枚举 | AC-6.6 |
| R-43 | 行为 | handle 为0或正数 | 分别以 event.id 或 handle 加100000形成内部 ID | 转换后写回事件 ID | AC-7.1 |
| R-44 | 异常 | handle<0或handle>INT_MAX-100000 | 返回 false | 防止偏移溢出 | AC-7.2 |
| R-45 | 行为 | isNewReferee=true | 按十万分组创建/复用独立 Referee | DEFAULT 路径 | AC-7.3 |
| R-46 | 行为 | isNewReferee=false | 0/1组用主 Referee，更大组继承前组 | COMPETITION 路径 | AC-7.4 |
| R-47 | 异常 | 竞争组缺少前组 Referee | 后续命中/分发提前退出 | 不自动创建替代 Referee | AC-7.5 |
| R-48 | 边界 | 清理映射到同一 Referee 的状态 | 删除全部关联 handle 分组 | 不只删除当前 handle | AC-7.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.7, R-1~R-7 | 动态/静态 BuilderNode Host 测试 | 两套路径、timestamp、pressure 和 boolean 语义 |
| VM-2 | AC-2.1~AC-2.7, R-8~R-14 | 通用输入与 referee 集成测试 | 类型识别、窗口坐标、策略、重复和非法上下文 |
| VM-3 | AC-3.1~AC-3.6, R-15~R-20 | Native 创建/销毁 C API 测试 | API15/24、三类事件、10点默认、所有权和 malformed 输入 |
| VM-4 | AC-3.7, R-21 | 字段比对 + ASan/生命周期测试 | 未复制字段、history 栈指针和销毁覆盖 |
| VM-5 | AC-4.1~AC-4.3, R-22~R-24 | setter 分组参数化测试 | 通用、当前点、ByIndex 字段写入 |
| VM-6 | AC-4.4~AC-4.7, R-25~R-28 | 边界/错误码/版本矩阵 | 数值范围、类型、所有权、API15弱校验和按键数组 |
| VM-7 | AC-5.1~AC-5.4, R-29~R-32 | Native 两代注入集成测试 | node/window 坐标、来源限制、策略和错误码 |
| VM-8 | AC-5.5~AC-5.8, R-33~R-36 | PostEventManager/GestureReferee 测试 | 180005宽语义、节点状态、非法策略和事件序列 |
| VM-9 | AC-6.1~AC-6.6, R-37~R-42 | PostEvent/EventManager 集成测试 | 独立结果、FlushEnd、三事件族动作记录和即时 MOVE |
| VM-10 | AC-7.1~AC-7.6, R-43~R-48 | handle/referee 参数化测试 | 100000 偏移、溢出、主/独立/继承 Referee 和共享清理 |

## API 变更分析

> 本文为已有能力补录，不修改公开 API；下表列出纳入基线的既有 API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `BuilderNode/ReactiveBuilderNode.postTouchEvent` | Public | TouchEvent | boolean | N/A | 从中间节点向子树转发触摸事件 | AC-1.1~AC-1.7 |
| `BuilderNode/ReactiveBuilderNode.postInputEvent` | Public | InputEventType | boolean | N/A | 转发 touch/mouse/axis 输入 | AC-2.1~AC-2.2, AC-2.6~AC-2.7 |
| `BuilderNode/ReactiveBuilderNode.postInputEventWithStrategy` | Public | InputEventType、可选 CompetitionStrategy | boolean | N/A | 带手势竞争策略转发输入 | AC-2.3~AC-2.5 |
| API15 Native clone/destroy/set/post | Public C API | touch event、node、基础字段 | int32_t | 0、401、180003~180006 | 克隆、编辑、销毁和投递触摸事件 | AC-3.1、AC-3.4~AC-3.6、AC-4.6、AC-5.1 |
| API24 Native create/clone/destroy | Public C API | event/output/type | ArkUI_ErrorCode | 0、401、180003、180006 | 克隆或空白构造三类指针事件 | AC-3.2~AC-3.7 |
| `OH_ArkUI_ClonedEvent_Set*` | Public C API | event、字段值、可选 pointerIndex | ArkUI_ErrorCode | 0、401、180003、180006 | 编辑通用和触摸字段 | AC-4.1~AC-4.7 |
| `OH_ArkUI_PointerEvent_PostClonedEventWithStrategy` | Public C API | node、event、strategy | ArkUI_ErrorCode | 0、401、180003~180005 | 向节点注入并选择手势竞争 | AC-5.2~AC-5.8 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| API15 `CreateClonedEvent`/`DestroyClonedEvent`/旧 setter/`PostClonedEvent` | 变更 | API24 需要多事件类型、更多字段和竞争策略 | 新代码使用 API24 PointerEvent/ClonedEvent API；保留 API15 触摸兼容路径 | AC-3.1~AC-3.7、AC-4.6、AC-5.1~AC-5.3 |
| `postTouchEvent` → `postInputEvent`/`postInputEventWithStrategy` | 变更 | 需要窗口坐标、mouse/axis 或竞争控制 | 按坐标语义和版本选择入口，不直接互换 local/window 数据 | AC-2.1~AC-2.5 |

## 接口规格

### 接口定义

**BuilderNode/ReactiveBuilderNode 触摸投递**

| 属性 | 值 |
|------|-----|
| 函数签名 | `postTouchEvent(event: TouchEvent): boolean`；`postInputEvent(event: InputEventType): boolean`；`postInputEventWithStrategy(event: InputEventType, competitionStrategy?: CompetitionStrategy): boolean` |
| 返回值 | boolean — 是否命中/成功进入可处理投递路径 |
| 开放范围 | Public |
| 错误码 | N/A，失败返回 false |
| 关联 AC | AC-1.1~AC-2.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | TouchEvent/InputEventType | 是 | 无 | touch 必须提供有效 touches/changedTouches 和完整 DOWN/UP 序列 |
| 坐标 | number | 是 | 无 | postTouchEvent 使用目标局部/父转换语义；postInputEvent 使用窗口坐标；单位 px |
| competitionStrategy | CompetitionStrategy | 否 | DEFAULT | DEFAULT=0、COMPETITION=1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 动静态 postTouchEvent、通用投递、策略和异常 | 见 Gherkin 场景 1~3 | AC-1.1~AC-2.7 |

**Native 创建与销毁**

| 属性 | 值 |
|------|-----|
| 函数签名 | API15 `CreateClonedEvent/DestroyClonedEvent`；API24 `CreateClonedPointerEvent/CreatePointerEvent/DestroyClonedPointerEvent` |
| 返回值 | int32_t / ArkUI_ErrorCode |
| 开放范围 | Public C API |
| 错误码 | 0、401、180003、180006 |
| 关联 AC | AC-3.1~AC-3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event/clonedEvent | ArkUI_UIInputEvent*/** | 是 | 无 | 指针和 payload 必须有效；API24 clone 支持 touch/mouse/axis |
| type | ArkUI_UIInputEvent_Type | CreatePointerEvent 必填 | 无 | 仅 TOUCH/MOUSE/AXIS |
| destroy event | const ArkUI_UIInputEvent* | 是 | 无 | 必须为 user-created 且由对应创建族产生 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 克隆、空白创建、malformed、销毁 | 见 Gherkin 场景 4~5 | AC-3.1~AC-3.7 |

**Native 克隆事件 setter**

| 属性 | 值 |
|------|-----|
| 函数签名 | API15 `SetClonedEvent*`；API24 `OH_ArkUI_ClonedEvent_Set*` |
| 返回值 | int32_t / ArkUI_ErrorCode |
| 开放范围 | Public C API |
| 错误码 | 0、401、180003、180006 |
| 关联 AC | AC-4.1~AC-4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | const ArkUI_UIInputEvent* | 是 | 无 | 必须为 user-created |
| pointerIndex | int32_t | ByIndex 必填 | 无 | `0<=index<touchPointSize` |
| pressure/area/time/ID | float/int64/int32 | 按 API | 无 | 非负；hover-move 不接受 pressure |
| tiltX/tiltY | float | 是 | 无 | `[-90,90]` |
| hand | int32_t | 是 | 无 | NONE~RIGHT |
| pressedKeyCodes/length | int32_t*/int32_t | 是 | 无 | 数组非空且 length>0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 通用/当前点/ByIndex setter 和越界 | 见 Gherkin 场景 6 | AC-4.1~AC-4.7 |

**Native 克隆事件投递**

| 属性 | 值 |
|------|-----|
| 函数签名 | API15 `PostClonedEvent(node,event)`；API24 `PostClonedEventWithStrategy(node,event,strategy)` |
| 返回值 | int32_t / ArkUI_ErrorCode |
| 开放范围 | Public C API |
| 错误码 | 0、401、180003、180004、180005 |
| 关联 AC | AC-5.1~AC-7.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | ArkUI_NodeHandle | 是 | 无 | 必须可解析为具有 Context/PostEventManager 的 FrameNode |
| event | const ArkUI_UIInputEvent* | 是 | 无 | 必须为 user-created；SDK 对策略接口限定 API24 创建器 |
| strategy | ArkUI_CompetitionStrategy | API24 必填 | DEFAULT | 公开值 0/1；当前源码非1均按0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 普通/策略投递、命中、错误、独立状态和 handle/referee | 见 Gherkin 场景 7~10 | AC-5.1~AC-7.6 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文补录 API 11~26 已有能力和源码偏差。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；事件均为运行时临时对象。
- **最低支持版本:** 动态 BuilderNode API 11；Native clone/post API 15；静态 BuilderNode API 23。
- **API 版本号策略:** 按 canonical SDK/Native 头文件保留 API 11/15/20/22/23/24/26 边界。

| API 版本 | 兼容性边界 | 证据 |
|----------|------------|------|
| API 11 | 动态 BuilderNode `postTouchEvent` | `BuilderNode.d.ts:415-455` |
| API 15 | Native touch clone/destroy、5个旧 setter、普通 PostClonedEvent | `ui_input_event.h:1427-1522,2133-2148`；`libace.ndk.json:2998-3028` |
| API 20 | 动态 BuilderNode 通用 `postInputEvent` | `BuilderNode.d.ts:550-585` |
| API 22 | 动态 ReactiveBuilderNode `postTouchEvent` | `BuilderNode.d.ts:758-798` |
| API 23 | 静态 BuilderNode `postTouchEvent` | `BuilderNode.static.d.ets:220-243` |
| API 24 | 动静态策略投递；Native 三类创建/clone、完整 setter、策略注入 | `BuilderNode.d.ts:590-636`；`ui_input_event.h:1361-1425,1524-2131` |
| API 26 | 静态无策略 `postInputEvent` 和 ReactiveBuilderNode `postTouchEvent` | `BuilderNode.static.d.ets:285-355,383-448` |

### 已知实现偏差

| 偏差 | SDK 契约 | 当前源码行为 | 处理方式 |
|------|----------|--------------|----------|
| 动静态 timestamp | 同 timestamp 只调用一次 | 动态仅活动序列同 ID+timestamp 去重；静态路径不调用该校验 | 契约章节保留 SDK 文案，风险和测试拆分两条路径 |
| 动态 pressure | pressure 应来自事件 pressure | 动态旧桥从 sourceTool 读取 force | 显式记录，不在文档任务修改源码 |
| boolean consumed | true 描述为事件被响应组件消费 | 实现主要按命中结果或序列有效性返回 | 规格使用可观察的命中/可投递语义并记录偏差 |
| API24 空白 touch | 从空白创建事件 | 当前固定创建 10 个触点槽且未显式设置 wrapper inputType | 必填字段由调用方 setter 完整赋值，覆盖默认容量测试 |
| touch clone 完整性 | cloned event 语义上应形成可独立编辑副本 | 部分字段未复制，history 指向栈内数组 | 进入生命周期高风险，不承诺完整长期历史副本 |
| 策略来源 | 仅 API24 两个创建器的事件可投递 | 实现只检查 user-created，API15 clone 亦可达 | 对外遵循 SDK；源码宽松范围不作为承诺 |
| 180005 语义 | 无组件命中 | 还覆盖重入、handle/序列/manager 等 false 分支 | 错误码测试覆盖所有实际触发源 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | BuilderNode 版本、坐标、UIExtension 和 Native 创建来源以 canonical SDK 为准 | AC-1.1~AC-2.3、AC-5.3 |
| 所有权标记 | Native 可编辑/销毁/投递事件必须由创建 API 产生并带 user-created 标记 | AC-3.4~AC-4.7、AC-5.1~AC-5.4 |
| 坐标入口隔离 | postTouchEvent/API15 注入与 postInputEvent/API24 策略注入使用不同 local/window 来源 | AC-1.3、AC-2.2、AC-5.1~AC-5.2 |
| 事件序列完整 | 触摸注入必须维持 DOWN→MOVE→UP/CANCEL 的可识别序列 | AC-2.2、AC-5.5~AC-5.8 |
| 状态域隔离 | 旧 PostEvent 独立结果不得覆盖正常平台输入链；pass-through 状态按目标和事件族清理 | AC-6.1~AC-6.6 |
| handle 分组 | WithStrategy 使用十万偏移域选择独立或继承 Referee | AC-7.1~AC-7.6 |
| ABI 不变 | 固定 Native 结构、10点容量和既有错误码，不在文档补录中修改 | AC-3.3、AC-4.3、AC-5.4 |
| 实现偏差可见 | pressure、clone history、来源和错误码偏差进入风险，不能静默修正文档 | AC-1.5~AC-1.7、AC-3.7、AC-5.3~AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 投递复用目标节点子树既有 TouchTest/Pipeline，不新增后台循环；单次调用同步返回 | Pipeline 集成测试 | `post_event_manager.cpp:56-145` |
| 功耗 | 构造和注入仅由应用显式调用触发，不新增周期任务 | 架构审查 | `js_base_node.cpp:327-583`；`ui_input_event.cpp:5374-5825` |
| 内存 | API24 空白 touch 固定10点；创建成功必须由匹配 Destroy API 释放 | ASan/销毁压力测试 | `ui_input_event.cpp:5455-5463,5494-5551` |
| 安全 | callback-owned event 不允许被 setter/Destroy/Post 当作 user-created 事件处理 | C API 所有权测试 | `ui_input_event.cpp:4152-4157,5498-5502,5587-5589` |
| 可靠性 | 非法 node、字段、序列和命中失败返回 false/错误码，不修改产品依赖或持久状态 | 参数化异常测试 | `post_event_manager.cpp:389-458`；`node_common_modifier.cpp:9362-9395` |
| 可测试性 | 三种事件类型、两代 API、三类 setter、两种策略和五类错误码均可独立参数化 | Host/C API 单测 | `test/unittest/interfaces/ace_ui_input_event/`；`post_event_manager_test_ng.cpp` |
| 自动化维测 | 非法序列提交 POST_EVENT_ERROR；Native 返回 401/180003/180004/180005/180006 | 错误上报和状态测试 | `post_event_manager.cpp:403-437`；`native_type.h:1540-1559` |
| 定界定位 | Builder bridge、创建/setter、CommonModifier、PostEventManager、EventManager 分层保留 source evidence | 源码审查 | `js_base_node.cpp`、`ui_input_event.cpp`、`node_common_modifier.cpp`、`post_event_manager.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 标准触屏构造与注入；坐标按 px/local/window 入口区分 | 构造完整 DOWN/MOVE/UP 序列 | 真机触摸注入测试 | `BuilderNode.d.ts:417-455,573-575` |
| 平板/手写笔设备 | pressure、tilt、roll、area、hand 和 pressedTime setter 更常用 | 按触摸专用范围和工具类型提供字段 | 手写笔注入测试 | `ui_input_event.h:1832-1984` |
| 折叠屏/多屏 | targetDisplayId 和 globalDisplay 坐标可编辑 | displayId 非负，策略注入使用窗口坐标进入目标子树 | 多屏注入测试 | `ui_input_event.cpp:4459-4502,4722-4798` |
| Webview | SDK 声明已内部处理 postTouchEvent 坐标转换 | 不重复添加 Webview 内部转换 | Web 组件集成测试 | `BuilderNode.d.ts:431-435` |
| UIExtension | BuilderNode SDK 明确不支持 | 不把 false 映射为自定义错误码 | 负向测试 | `BuilderNode.d.ts:437-440` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 本 Feat 不构造或注入无障碍语义事件 | N/A |
| 大字体 | 否 | 事件坐标和字段不依赖字体缩放 | N/A |
| 深色模式 | 否 | 输入构造不依赖颜色模式 | N/A |
| 多窗口/分屏 | 是 | window/globalDisplay/targetDisplayId 和 px 转换影响命中 | AC-1.3、AC-2.2、AC-4.1~AC-4.3、AC-5.2 |
| 多用户 | 否 | 事件不持久化且不跨用户存储 | N/A |
| 版本升级 | 是 | API11/15/20/22/23/24/26 的入口、事件类型和校验能力不同 | AC-1.1~AC-3.7、AC-4.6、AC-5.1~AC-5.3 |
| 生态兼容 | 是 | timestamp、pressure、boolean、clone 和错误码偏差可能影响既有转发业务 | AC-1.5~AC-1.7、AC-3.7、AC-5.3~AC-5.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 自定义输入事件构造与分发
  作为 ArkUI 命令式节点与 Native 开发者
  我想要构造并向目标节点子树投递 touch、mouse 或 axis 事件
  以便复用既有命中测试和手势识别能力

  Scenario: 动态 postTouchEvent 拒绝活动序列的同 ID 同 timestamp
    Given 动态 BuilderNode 已投递 finger ID 1 的 DOWN 且尚未 UP/CANCEL
    When 再次以相同 timestamp 投递 finger ID 1
    Then 返回 false
    And 使用不同 finger ID 不因该 timestamp 自动失败

  Scenario: 动态 pressure 源码偏差
    Given TouchEvent pressure 与 sourceTool 数值不同
    When 动态 postTouchEvent 解析事件
    Then 当前内部 force 等于 sourceTool 数值
    And 静态入口使用 pressure 数值

  Scenario: DEFAULT 与 COMPETITION 选择不同裁决器
    Given 目标节点和完整触摸序列有效
    When 使用 DEFAULT 投递
    Then 注入手势使用独立 referee
    When 使用 COMPETITION 投递
    Then 注入手势复用正常或上级 referee

  Scenario: API24 从空白创建触摸事件
    Given 输出指针有效且 type 为 TOUCH
    When 调用 CreatePointerEvent
    Then 返回 NO_ERROR
    And touchPointSize 为 10
    And 调用方仍需设置完整动作、触点和坐标字段

  Scenario: 克隆触摸 history 生命周期风险
    Given 原事件包含 history、rollAngle 和 pressed keys
    When 当前实现调用 CreateClonedTouchEvent
    Then 部分事件级字段未复制
    And historyEvents 被设置为函数内临时数组地址

  Scenario: API24 setter 边界
    Given user-created touch event 包含 10 个触点槽
    When pointerIndex 为 10 或 tiltX 为 91
    Then 返回 PARAM_INVALID
    When pointerIndex 为 9 且 tiltX 为 90
    Then 对应 setter 返回 NO_ERROR

  Scenario: 两代 Native 注入使用不同坐标
    Given actionTouchPoint 的 nodeX 与 windowX 不同
    When API15 PostClonedEvent 投递
    Then 内部当前 x 使用 nodeX
    When API24 PostClonedEventWithStrategy 投递
    Then 内部当前 x 使用 windowX

  Scenario: 180005 覆盖多类投递失败
    Given node 和 user-created event 非空
    When 目标子树无命中或同节点重入或触摸序列非法
    Then 策略投递可能返回 180005

  Scenario: 旧 PostEvent 使用独立目标状态
    Given 普通平台触摸目标链已经存在
    When 旧 PostEvent DOWN 在指定 UINode 子树命中
    Then 目标写入 postEventTouchTestResults
    And 不覆盖普通 touchTestResults

  Scenario: pass-through MOVE 不等待 VSync
    Given 目标节点和 Touch MOVE 有效
    When 调用 postInputEvent 转发 MOVE
    Then 当前调用内执行 FlushEnd 和 Dispatch
    And 不进入普通 VSync MOVE 队列

  Scenario: handle 选择竞争 Referee
    Given eventHandleId 为 2 且策略为 COMPETITION
    When 执行 WithStrategy 投递
    Then 内部事件 ID 为 100002
    And 使用前一 handle 分组对应的 Referee
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：跨 Pipeline 拼链由 Feat-03 承接，本文覆盖自定义事件构造与投递
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致，每个 AC 至少关联一条规则
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突五项检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "BuilderNode postTouchEvent postInputEvent PostEventManager"
  - repo: "openharmony/arkui_ace_engine"
    query: "CreateClonedPointerEvent CreatePointerEvent ClonedEvent Set touch"
  - repo: "openharmony/arkui_ace_engine"
    query: "PostClonedEventWithStrategy CompetitionStrategy eventHandleId"
```

**关键文档：** `specs/04-common-capability/04-common-events/03-event-dispatch-intercept/design.md`；`interface/sdk-js/api/arkui/BuilderNode.d.ts`；`interfaces/native/ui_input_event.h`
