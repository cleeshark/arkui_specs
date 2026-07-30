# 特性规格

> Func-04-04-01-Feat-03 历史采样与高级触点信息：固化 ArkTS 与 Native 的帧内历史点、压力、倾角、旋转角、接触面积、按压时间、操作手及其采样、索引、版本和异常规则。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 历史采样与高级触点信息 (History Sampling and Advanced Touch Information) |
| 特性编号 | Func-04-04-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 ArkTS API 9~26；静态 ArkTS API 23~26；Native API 12~26，API 9/10/12/15/17/20/23 存在能力边界 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkTS 历史采样规格 | 补录 `HistoricalPoint`、`getHistoricalPoints()`、帧内聚合、当前点重复和动态/静态返回差异 |
| ADDED | 高级触点属性规格 | 补录顶层及逐触点 pressure、tilt、roll、size、width/height、pressedTime 和 hand |
| ADDED | 重采样高级字段规格 | 补录仅坐标/时间参与插值、高级字段继承原始样本及插值拒绝条件 |
| ADDED | Native 高级触点访问规格 | 补录当前/索引/历史 getter、20×10 上限、数据来源差异、状态和实现偏差 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| 功能域设计 | `specs/04-common-capability/04-common-events/01-touch-events/design.md` | 与本 Spec 增量同步 |
| 动态 ArkTS SDK 契约 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:9361`、`:10840`、`:10917`、`:11037`；`enums.d.ts:716` | 已核验 |
| 静态 ArkTS SDK 契约 | `interface/sdk-js/api/arkui/component/common.static.d.ets:4573`、`:5414`、`:5490`、`:5582`；`enums.static.d.ets:549` | 已核验 |
| 平台输入转换 | `adapter/ohos/entrance/mmi_event_convertor.cpp:182`、`:319`、`:444` | 已核验 |
| 帧内聚合和重采样 | `frameworks/core/pipeline_ng/pipeline_context.cpp:183`、`:4898`；`frameworks/core/common/event_manager.cpp:2790`；`frameworks/core/event/resample_algo.cpp:144` | 已核验 |
| TouchEventInfo 历史构造 | `frameworks/core/components_ng/event/touch_event.cpp:109`、`:284` | 已核验 |
| ArkTS 转换实现 | `frameworks/bridge/declarative_frontend/engine/js_types.cpp:91`；`engine/functions/js_touch_function.cpp:28`；`frameworks/core/interfaces/native/implementation/touch_object_accessor.cpp:198` | 已核验 |
| Native SDK 与实现 | `interfaces/native/ui_input_event.h:741`、`:843`、`:1003`、`:1284`；`interfaces/native/event/ui_input_event.cpp:2200`、`:2475`、`:2828` | 已核验 |

## 用户故事

### US-1: 获取当前帧的历史触点

**作为** 需要高频轨迹的 ArkUI 开发者，
**我想要** 在触摸回调中读取当前帧内的历史采样，
**以便** 在不增加回调频率的情况下重建更细粒度的移动轨迹。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态 ArkTS API 10+ 在当前 `onTouch` 回调持有的 `TouchEvent` 上调用 `getHistoricalPoints()` THEN 返回该事件携带的 `Array<HistoricalPoint>` | 正常 |
| AC-1.2 | WHEN 静态 ArkTS API 23+ 调用 `getHistoricalPoints()` THEN 返回 `Array<HistoricalPoint>`；WHEN 内部运行环境无法提供事件指针 THEN 允许返回 `undefined` | 异常 |
| AC-1.3 | WHEN 同一帧缓存多个 MOVE 样本 THEN Pipeline 按 finger ID 聚合样本并通常只向该 ID 派发一个事件，历史列表保存聚合样本 | 正常 |
| AC-1.4 | WHEN 非插值事件的 history 非空 THEN 当前回调使用 `history.back()` 作为顶层和 changed point，同时 `getHistoricalPoints()` 遍历完整 history，因此历史末项允许与当前点重复 | 边界 |
| AC-1.5 | WHEN 插值成功产生独立重采样点 THEN 当前 changed point 使用重采样结果，history 保留原始样本，当前点不要求等于历史末项 | 边界 |
| AC-1.6 | WHEN `HistoricalPoint` 被返回 THEN 包含 `touchObject`、`size`、`force` 和 `timestamp`；timestamp 表示采样事件时间，动态 SDK 单位为 ns | 正常 |
| AC-1.7 | WHEN 运行在 wearable 构建且相邻 MOVE 样本 x/y 完全相同 THEN 该重复坐标样本不加入 history；非 wearable 构建按现有路径加入 | 边界 |

### US-2: 读取压力、角度、面积和操作手

**作为** 手写笔或精细触控应用开发者，
**我想要** 读取触摸强度、姿态、接触区域和操作手信息，
**以便** 调整笔迹、工具行为和交互反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN MMI PointerItem 被转换为 TouchPoint THEN pressure 转为 float，tiltX/tiltY、twist、width/height、downTime 和 tool 被复制，`size` 计算为 `max(width,height)/2.0` | 正常 |
| AC-2.2 | WHEN MMI blobId 小于 0 THEN hand 为 NONE=0；WHEN blobId 有效 THEN 仅保留 LEFT/RIGHT 位形成 InteractionHand | 边界 |
| AC-2.3 | WHEN 动态 ArkTS API 9+ 读取 BaseEvent pressure/tiltX/tiltY THEN pressure 默认 0、标称范围 `[0,1]` 且硬件允许大于 1，tilt 单位为 deg；API 17+ 可读取可选 rollAngle | 正常 |
| AC-2.4 | WHEN 动态 ArkTS API 15+ 读取 TouchObject 高级字段 THEN hand、pressedTime、pressure、width、height 为可选字段，其中 pressedTime 单位 ns、pressure 范围 `[0,65535)`、width/height 单位 vp | 正常 |
| AC-2.5 | WHEN 动态 ArkTS 比较 BaseEvent.pressure、TouchObject.pressure 和 HistoricalPoint.force THEN 不得假定三者量纲相同；顶层字段标称 `[0,1]`，后两者标称 `[0,65535)` | 边界 |
| AC-2.6 | WHEN 读取 HistoricalPoint.size THEN 该字段保持独立的单一接触面积量，不能推定为 width×height；常规 onTouch 历史构造未设置 size 时返回默认 0 | 边界 |
| AC-2.7 | WHEN 静态 ArkTS API 23+ 读取高级字段 THEN 使用静态声明的 double/long/int 类型；静态 SDK 未声明的动态单位、默认值和范围不得自动复制为静态契约 | 边界 |
| AC-2.8 | WHEN 解释 rollAngle THEN 动态和静态 SDK 的语义描述保持可见差异：动态描述为触控笔与设备表面夹角，静态描述为绕 Z 轴旋转角 | 边界 |

### US-3: 理解高级字段的采样和桥接来源

**作为** 需要跨入口一致性的框架或应用开发者，
**我想要** 知道高级字段何时参与重采样及各前端入口如何转换，
**以便** 避免将坐标采样时刻或 density 规则错误应用到无量纲数据。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN MOVE 重采样成功 THEN 只插值 x/y、screen/globalDisplay 坐标和 time；pressure、size、width/height、tilt、roll、pressedTime 和 hand 继承最接近目标时刻的原始 TouchEvent | 边界 |
| AC-3.2 | WHEN 样本少于 2 个、时间间隔不在 2~20 ms、轨迹反弹、预测超过 `min(delta/2,8 ms)` 或 targetDisplayId 不同 THEN 放弃对应插值并使用既有原始/降级结果 | 边界 |
| AC-3.3 | WHEN 标准动态 `onTouch` 路径创建 live TouchObject THEN 当前实现对 pressure 调用 density 换算；WHEN FrameNodeBridge 创建 TouchObject 或动态历史点 THEN pressure 使用原始 force | 边界 |
| AC-3.4 | WHEN 静态 TouchObject accessor 读取 pressure THEN 当前实现同样调用 density 换算；WHEN 静态 HistoricalPoint 转换 force THEN 使用原始 force | 边界 |
| AC-3.5 | WHEN pressure 被 density 换算的入口与原值入口处理同一 force THEN 输出允许不同；该源码偏差不改变 canonical SDK 的无量纲压力契约 | 边界 |
| AC-3.6 | WHEN 历史 TouchLocationInfo 被构造 THEN 复制 time、坐标、type、force、pressedTime、width/height、tilt、roll、tool 和 hand，但不复制 TouchEvent.size | 正常 |

### US-4: 通过 Native 读取当前高级触点信息

**作为** Native ArkUI 开发者，
**我想要** 读取当前触点的压力、姿态、面积、操作手和按压时间，
**以便** 在 C/C++ 业务中处理精细输入。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 12+ 对普通 `ON_TOUCH` 事件调用 pressure、tiltX/tiltY 或 touch-area getter 并传入任意有效 pointerIndex THEN 当前实现忽略该索引并读取 `touchPointes[touchPointSize-1]` | 边界 |
| AC-4.2 | WHEN API 15+ 调用 InteractionHand 无索引 getter THEN 读取 actionTouchPoint；WHEN 调用 InteractionHandByIndex 或 PressedTimeByIndex THEN 读取指定 `touchPointes[pointerIndex]` | 正常 |
| AC-4.3 | WHEN API 17+ 调用 RollAngle THEN ON_HOVER_MOVE 读取 actionTouchPoint，普通 ON_TOUCH 读取事件级 rollAngle，其他触摸子类型读取最后一个触点；该接口没有 ByIndex 版本 | 边界 |
| AC-4.4 | WHEN 高级 getter 的 touchPointSize 为 0、event 为空、事件类型不支持或索引越界 THEN 返回 0/0.0f 或参数错误；API 20+ 调用方通过 latest status 判断错误 | 异常 |
| AC-4.5 | WHEN Native 读取 pressure、tilt、roll、area、pressedTime 或 hand THEN 数值直接复制，不执行 VP/PX 坐标换算；pressedTime 头文件未声明具体时间单位 | 边界 |

### US-5: 通过 Native 读取历史多点数据

**作为** Native 多点输入开发者，
**我想要** 使用 historyIndex 和 pointerIndex 读取历史事件，
**以便** 重建帧内各触点的轨迹和高级属性。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN TouchEventInfo 的 historyPointerEvent 非空且数量等于 history THEN Native 构造历史数组；WHEN 两者为空或数量不等 THEN `historyEvents=nullptr` 且 `historySize=0` | 边界 |
| AC-5.2 | WHEN 历史样本超过 20 个或单个历史样本超过 10 个触点 THEN Native 仅保留从列表起始处开始的前 20 个历史事件和每事件前 10 个触点 | 边界 |
| AC-5.3 | WHEN API 12+ 使用有效 historyIndex 和 pointerIndex 调用历史 time/count/id/坐标/pressure/tilt/contact-area getter THEN 返回对应二维索引数据 | 正常 |
| AC-5.4 | WHEN Native 重建同一历史样本的多个触点 THEN 各触点 ID、pressure、tilt、hand 等来自各自 TouchPoint，但 local/window/display/globalDisplay 坐标均来自同一个 historyLocation | 边界 |
| AC-5.5 | WHEN Native 重建历史 contact area THEN width 和 height 均使用 `TouchPoint.size=max(rawWidth,rawHeight)/2.0`，不保留原始椭圆宽高 | 边界 |
| AC-5.6 | WHEN 调用公开历史 getter THEN 可读取 ID、坐标、pressure、tilt 和 contact area，但不能读取内部已保存的历史 rollAngle、pressedTime、toolType 或 hand | 边界 |
| AC-5.7 | WHEN `GetHistorySize` 面对 `historyEvents=nullptr` 或历史双索引越界 THEN 返回 0/0.0f 并将 latest status 置为 PARAM_INVALID；不支持事件类型置为 INPUT_EVENT_TYPE_NOT_SUPPORT | 异常 |
| AC-5.8 | WHEN historyPointerEvent 某个元素为空但两列表数量一致 THEN 该索引的构造被跳过，但最终 historySize 仍按原列表数量计算，该槽位保持默认数据 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1, R-2 | 已有实现 | SDK 声明检查 + ArkTS 运行时测试 | 动态 `common.d.ts:11037-11053`；静态 `common.static.d.ets:5582-5590`；`js_types.cpp:91-152` |
| AC-1.3~AC-1.5 | R-3~R-5 | 已有实现 | Pipeline/Actuator 参数化单测 | `pipeline_context.cpp:4898-4955`；`touch_event.cpp:109-130` |
| AC-1.6~AC-1.7 | R-6, R-7 | 已有实现 | SDK 字段检查 + wearable 构建测试 | `common.d.ts:10917-10980`；`pipeline_context.cpp:183-191` |
| AC-2.1~AC-2.2 | R-8, R-9 | 已有实现 | MMI 转换单测 | `mmi_event_convertor.cpp:182-232`；`touch_event.h:38-59` |
| AC-2.3~AC-2.5 | R-10~R-12 | 已有实现 | SDK 版本/范围检查 | `common.d.ts:9361-9419,10864-10875,10953-10966` |
| AC-2.6~AC-2.8 | R-13~R-15 | 已有实现 | SDK 双通道比对 + 历史输出测试 | `touch_event.cpp:284-331`；`common.static.d.ets:4573-4608,5414-5534` |
| AC-3.1~AC-3.2 | R-16, R-17 | 已有实现 | 重采样算法单测 | `event_manager.cpp:2790-2901`；`resample_algo.cpp:144-226` |
| AC-3.3~AC-3.5 | R-18~R-20 | 已有实现 | density 参数化前端测试 | `js_touch_function.cpp:51-55`；`arkts_native_frame_node_bridge.cpp:242-259`；`touch_object_accessor.cpp:210-217`；`js_types.cpp:128-145` |
| AC-3.6 | R-21 | 已有实现 | TouchEventInfo 字段检查 | `touch_event.cpp:284-331`；`touch_event.h:266-275` |
| AC-4.1~AC-4.3 | R-22~R-24 | 已有实现 | Native getter 多点单测 | `ui_input_event.cpp:2200-2445,3189-3207` |
| AC-4.4~AC-4.5 | R-25, R-26 | 已有实现 | Native 错误/单位检查 | `ui_input_event_impl.h:88-99`；`node_common_modifier.cpp:11240-11264` |
| AC-5.1~AC-5.2 | R-27, R-28 | 已有实现 | Native 历史构造边界单测 | `node_common_modifier.cpp:129-130,11287-11335` |
| AC-5.3~AC-5.6 | R-29~R-32 | 已有实现 | Native historyIndex+pointerIndex 单测 | `ui_input_event.cpp:2475-2942`；`node_common_modifier.cpp:10446-10487` |
| AC-5.7~AC-5.8 | R-33, R-34 | 已有实现 | Native 异常和空 raw event 单测 | `ui_input_event.cpp:61-74,2475-2500`；`node_common_modifier.cpp:11291-11335` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 动态 API 10+ 在当前 onTouch TouchEvent 调用 getHistoricalPoints | 返回 Array<HistoricalPoint> | API 仅在当前回调事件上下文有效 | AC-1.1 |
| R-2 | 异常 | 静态 API 23+ 调用 getHistoricalPoints | 正常返回数组；内部事件指针不可用时允许 undefined | 调用方必须检查 undefined | AC-1.2 |
| R-3 | 行为 | 同帧收到同 finger ID 的多个 MOVE | 按 ID 聚合 history，通常每 ID 派发一个事件 | 多指同帧仍可分别派发 | AC-1.3 |
| R-4 | 边界 | 非插值事件 history 非空 | history.back 同时成为当前点，完整 history 对外可见 | 历史末项允许与 changed point 重复 | AC-1.4 |
| R-5 | 边界 | 插值成功 | 当前点使用重采样结果，history 保存原始样本 | 当前点无需出现在 history | AC-1.5 |
| R-6 | 行为 | HistoricalPoint 转换 | 输出 touchObject、size、force、timestamp | 动态 timestamp 单位 ns | AC-1.6 |
| R-7 | 边界 | wearable 相邻样本坐标相同 | 不把重复 x/y 样本加入 history | 非 wearable 无此过滤 | AC-1.7 |
| R-8 | 行为 | MMI PointerItem 转换 | size=max(width,height)/2，复制 force/tilt/twist/width/height/downTime/tool | pressure 精度收窄为 float | AC-2.1 |
| R-9 | 边界 | 转换 operating hand | blobId<0 返回 NONE；否则仅保留 LEFT/RIGHT 位 | 枚举值 NONE/LEFT/RIGHT=0/1/2 | AC-2.2 |
| R-10 | 行为 | 动态读取 BaseEvent 高级字段 | pressure/tilt API 9，roll API 17，按 SDK 单位和默认值解释 | pressure 硬件允许超过 1 | AC-2.3 |
| R-11 | 行为 | 动态读取 TouchObject 高级字段 | API 15+ 提供可选 hand/pressedTime/pressure/width/height | pressure<65535，width/height 为 vp | AC-2.4 |
| R-12 | 边界 | 比较三种压力字段 | 分别遵循顶层与逐触点/历史 SDK 范围 | 不直接互换或归一化推断 | AC-2.5 |
| R-13 | 边界 | 读取 HistoricalPoint.size | 保持为独立字段；常规 onTouch 路径因未 SetSize 返回 0 | 不从 width/height 补算 | AC-2.6 |
| R-14 | 边界 | 静态读取高级字段 | 仅承诺静态 SDK 明示的类型/可选性 | 未声明的单位、默认值、范围不从动态复制 | AC-2.7 |
| R-15 | 边界 | 解释 rollAngle | 保留动态“与表面夹角”和静态“绕 Z 轴”描述差异 | 两通道均为可选字段 | AC-2.8 |
| R-16 | 边界 | MOVE 插值 | 只覆盖坐标和 time，高级字段继承最近原始样本 | 高级字段与坐标可能不同采样时刻 | AC-3.1 |
| R-17 | 边界 | 重采样前置条件不满足 | 使用原始/降级点，不强制插值 | 样本≥2、间隔2~20ms、预测≤min(delta/2,8ms)、同 display、非反弹 | AC-3.2 |
| R-18 | 边界 | 标准动态 live TouchObject 与 FrameNode/历史路径读取同一 force | 标准动态执行 density 换算，FrameNode/历史保持原值 | 作为源码偏差记录，不改 SDK 契约 | AC-3.3 |
| R-19 | 边界 | 静态 live TouchObject 与静态历史读取同一 force | live accessor 执行 density 换算，历史 force 保持原值 | 作为源码偏差记录 | AC-3.4 |
| R-20 | 边界 | density 不等于 1 且比较各入口 pressure | 允许产生不同数值 | 不能将 density 换算视为 SDK 量纲 | AC-3.5 |
| R-21 | 行为 | 构造历史 TouchLocationInfo | 复制除 size 外的已实现高级字段 | size 保持默认 0 | AC-3.6 |
| R-22 | 边界 | 普通 ON_TOUCH 调用 pressure/tilt/area getter | 忽略 pointerIndex，读取最后一个触点 | touchPointSize 必须大于 0 | AC-4.1 |
| R-23 | 行为 | 获取 hand 或 pressedTime | hand 无索引读 action point；ByIndex/PressedTime 按索引读数组项 | API 15+ | AC-4.2 |
| R-24 | 边界 | 获取 rollAngle | 按 subKind 读取 action/event/last point，且无 ByIndex | API 17+ | AC-4.3 |
| R-25 | 异常 | 高级 getter 参数/类型/索引非法 | 返回默认 0 或错误并记录 latest status | API 20+ 可区分合法零值 | AC-4.4 |
| R-26 | 边界 | Native 输出非坐标高级字段 | 直接复制数值，不执行 VP/PX 换算 | pressedTime 单位未在 C 头文件声明 | AC-4.5 |
| R-27 | 边界 | 构造 Native history | 仅当 historyPointerEvent 非空且与 history 等长时生成 | 否则 historySize=0 且 events=null | AC-5.1 |
| R-28 | 边界 | 历史超过容量 | 保留前20个事件、每事件前10点 | 上限20×10，超出直接截断 | AC-5.2 |
| R-29 | 行为 | historyIndex/pointerIndex 均有效 | 返回公开历史 time/count/id/坐标/pressure/tilt/area | 坐标 getter 按节点单位处理 | AC-5.3 |
| R-30 | 边界 | 重建历史多点坐标 | 每个 pointer 使用同一个 historyLocation 坐标，高级字段按各 TouchPoint | 同一历史样本内多 pointer 坐标相同 | AC-5.4 |
| R-31 | 边界 | 重建历史 contact area | width/height 均取 TouchPoint.size | size=max(rawWidth,rawHeight)/2 | AC-5.5 |
| R-32 | 边界 | 调用公开历史 getter | 不开放 roll/pressedTime/tool/hand 历史读取 | 内部保存不等于公开 API | AC-5.6 |
| R-33 | 异常 | history 为空、双索引越界或类型不支持 | 返回默认零值并设置 PARAM_INVALID/INPUT_EVENT_TYPE_NOT_SUPPORT | HistorySize=0 也需检查状态 | AC-5.7 |
| R-34 | 边界 | 等长 raw history 中某元素为空 | 跳过该槽构造，historySize 仍按列表总数 | 对应槽保持默认数据 | AC-5.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.7, R-1~R-7 | ArkTS/Pipeline 参数化测试 | 回调时机、返回类型、帧内聚合、当前点重复和 wearable 过滤 |
| VM-2 | AC-2.1~AC-2.8, R-8~R-15 | SDK 扫描 + MMI 转换单测 | 字段类型、版本、单位、范围、size、hand 和 roll 描述 |
| VM-3 | AC-3.1~AC-3.2, R-16~R-17 | 重采样算法单测 | 仅坐标/时间插值和所有拒绝边界 |
| VM-4 | AC-3.3~AC-3.6, R-18~R-21 | density/前端入口矩阵测试 | live/history、dynamic/static pressure 输出和 size 缺失 |
| VM-5 | AC-4.1~AC-4.5, R-22~R-26 | Native 当前高级 getter 单测 | index 忽略、hand/pressedTime、roll subKind 和错误状态 |
| VM-6 | AC-5.1~AC-5.3, R-27~R-29 | Native 历史容量/索引单测 | 构造门槛、20×10 截断和二维索引 |
| VM-7 | AC-5.4~AC-5.8, R-30~R-34 | Native 历史数据一致性测试 | 共享坐标、面积退化、未开放字段、状态和空 raw 槽 |

## API 变更分析

> 本文为已有能力补录，不修改公开 API；下表列出纳入基线的既有 API 和字段族。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `TouchEvent.getHistoricalPoints()` / `HistoricalPoint` | Public | 无 | 动态数组；静态数组或 undefined | N/A | 获取当前帧历史点 | AC-1.1~AC-1.6 |
| `BaseEvent.pressure/tiltX/tiltY/rollAngle` | Public | N/A | 属性 | N/A | 顶层压力和手写笔姿态 | AC-2.3, AC-2.5, AC-2.8 |
| `TouchObject.hand/pressedTime/pressure/width/height` | Public | N/A | 可选属性 | N/A | 逐触点高级信息 | AC-2.4~AC-2.7 |
| `InteractionHand` | Public | N/A | 枚举 0/1/2 | N/A | 表示 NONE/LEFT/RIGHT | AC-2.2 |
| Native pressure/tilt/touch-area getter | Public C API | event、pointerIndex | float | 默认 0 + latest status | 读取当前高级触点字段 | AC-4.1, AC-4.4, AC-4.5 |
| `OH_ArkUI_PointerEvent_GetRollAngle` | Public C API | event、输出指针 | int32_t 状态码 | 0、401、类型不支持 | 读取旋转角 | AC-4.3, AC-4.4 |
| Native InteractionHand/PressedTime getter | Public C API | event、可选 pointerIndex/输出指针 | 状态码或 int64_t | 0、401、类型不支持 | 读取操作手和按压时间 | AC-4.2, AC-4.5 |
| Native HistorySize/EventTime/PointerCount/PointerId/坐标 getter | Public C API | event、historyIndex、pointerIndex | 数量、时间、ID、坐标 | 默认零值 + latest status | 读取历史事件和触点 | AC-5.1~AC-5.4, AC-5.7 |
| Native HistoryPressure/Tilt/TouchArea getter | Public C API | event、pointerIndex、historyIndex | float | 默认 0 + latest status | 读取历史高级字段 | AC-5.3~AC-5.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `HistoricalPoint.touchObject` 高级字段 | 变更 | 动态 API 10~14 与 API 15+ | API 10~14 不依赖 hand/pressedTime/pressure/width/height；API 15+ 按可选字段处理 | AC-2.4, AC-2.7 |
| `BaseEvent.rollAngle` | 变更 | 动态 API 17+；静态 API 23+ | 使用符号字段并保留双通道语义描述差异 | AC-2.8 |
| Native HistoryGlobalDisplayX/Y | 变更 | API 20+ 全局显示坐标 | API 12~19 使用已有 local/window/display 历史坐标 | AC-5.3 |

## 接口规格

### 接口定义

**`TouchEvent.getHistoricalPoints` / `HistoricalPoint`**

| 属性 | 值 |
|------|-----|
| 函数签名 | 动态 `getHistoricalPoints(): Array<HistoricalPoint>`；静态 `getHistoricalPoints(): Array<HistoricalPoint> \| undefined` |
| 返回值 | 当前事件携带的帧内历史点 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.7、AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| this | `TouchEvent` | 是 | 无 | 仅在当前 onTouch 回调事件上下文调用 |
| 返回数组 | `HistoricalPoint[]` | N/A | 空数组 | 静态内部环境异常时允许 undefined |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多 MOVE 聚合、插值/非插值、wearable | 见 Gherkin 场景 1~3 | AC-1.1~AC-1.7 |

**ArkTS 高级字段**

| 属性 | 值 |
|------|-----|
| 函数签名 | `BaseEvent.pressure/tiltX/tiltY/rollAngle`；`TouchObject.hand/pressedTime/pressure/width/height` |
| 返回值 | number/double/long/int/InteractionHand 属性 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| BaseEvent.pressure | number/double | 是 | 动态 0 | 动态标称 `[0,1]`，硬件允许 >1 |
| TouchObject.pressure | 可选 number/double | 否 | 未提供 | 动态 `[0,65535)` |
| tiltX/tiltY/rollAngle | number/double | 见 SDK | 0/未提供 | 动态角度单位 deg；roll 双通道描述不同 |
| width/height | 可选 number/double | 否 | 未提供 | 动态单位 vp |
| pressedTime | 可选 number/long | 否 | 未提供 | 动态单位 ns |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 不同压力字段、density、重采样 | 见 Gherkin 场景 4~5 | AC-2.1~AC-3.6 |

**Native 当前高级 getter**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GetPressure/GetTiltX/GetTiltY/GetTouchAreaWidth/GetTouchAreaHeight/GetRollAngle/GetInteractionHand/GetPressedTimeByIndex` |
| 返回值 | float/double/int64_t 或状态码 |
| 开放范围 | Public C API |
| 错误码 | 默认零值；401、INPUT_EVENT_TYPE_NOT_SUPPORT；API 20+ latest status |
| 关联 AC | AC-4.1~AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 必须是 getter 支持的事件类型 |
| pointerIndex | `uint32_t` | 依 API | 无 | 契约为触点索引；部分当前实现忽略并读取最后一点 |
| rollAngle/hand | 输出指针 | 是 | 无 | 不得为空 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多点索引、不同 subKind、非法参数 | 见 Gherkin 场景 6 | AC-4.1~AC-4.5 |

**Native 历史 getter**

| 属性 | 值 |
|------|-----|
| 函数签名 | `GetHistorySize/EventTime/PointerCount/PointerId/X/Y/.../Pressure/Tilt/TouchArea` |
| 返回值 | 历史数量、时间、ID、坐标和高级字段 |
| 开放范围 | Public C API |
| 错误码 | 默认零值 + latest status |
| 关联 AC | AC-5.1~AC-5.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| historyIndex | `uint32_t` | 是 | 无 | `0 <= historyIndex < historySize <= 20` |
| pointerIndex | `uint32_t` | 按 getter | 无 | `0 <= pointerIndex < historyPointerCount <= 10` |
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 高级历史 getter 仅支持 C touch event |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效二维索引、容量截断、空 raw 历史 | 见 Gherkin 场景 7~8 | AC-5.1~AC-5.8 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文补录已有能力和源码偏差。历史 API 自动态 API 10 开放，高级 TouchObject 字段自 API 15 加入。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态高级 BaseEvent API 9；动态历史 API 10；Native API 12；静态 API 23。
- **API 版本号策略:** 逐字段保留 canonical SDK 的 `@since`、可选性、单位和范围；Native 按头文件/NDK 导出版本记录。

| API 版本 | 兼容性边界 | 证据 |
|----------|------------|------|
| API 9 | 动态 BaseEvent pressure、tiltX、tiltY | `common.d.ts:9361-9405` |
| API 10 | 动态 HistoricalPoint 和 getHistoricalPoints | `common.d.ts:10917-10980,11037-11053` |
| API 12 | Native 当前 pressure/tilt/area 和基础历史 getter | `ui_input_event.h:741-771,811-1066`；`libace.ndk.json:491-580` |
| API 15 | 动态 TouchObject hand/pressedTime/pressure/width/height；Native hand/pressedTime | `common.d.ts:10840-10901`；`ui_input_event.h:785-809,1284-1292` |
| API 17 | 动态和 Native rollAngle | `common.d.ts:9407-9419`；`ui_input_event.h:773-783` |
| API 20 | Native historical globalDisplay 和 latest status | `ui_input_event.h:969-1001,2150-2165` |
| API 23 | 静态 HistoricalPoint、getHistoricalPoints 和全部高级字段 | `common.static.d.ets:4573-4608,5414-5590` |

### 已知实现偏差

| 偏差 | SDK 契约 | 当前源码行为 | 处理方式 |
|------|----------|--------------|----------|
| 压力量纲/桥接 | pressure 为无量纲字段，顶层与逐触点范围不同 | 标准动态和静态 live TouchObject 对 force 做 density 换算；FrameNode/历史保留原值 | API 章节以 SDK 为准；测试和风险显式区分入口 |
| 历史末项 | SDK 描述最后点由 onTouch 返回，其余为历史点 | 非插值 history 包含当前 `history.back()`，历史末项可与 changed point 重复 | 固化源码行为并记录 SDK 偏差 |
| HistoricalPoint.size | SDK 定义独立 size 字段 | 常规 onTouch 历史路径未 SetSize，输出默认 0 | 不从 width/height 补造值 |
| Native pointerIndex | 头文件描述读取指定触点 | pressure/tilt/area 普通触摸实现读取最后一个触点 | 逐 getter 记录实际数据源 |
| Native 历史多点 | 每个 pointerIndex 应表示对应历史触点 | 同一历史样本所有 pointer 坐标复用 historyLocation，面积宽高均取 size | 作为实现风险和边界测试 |
| rollAngle 描述 | dynamic/static canonical SDK 应各自可解释 | 动态与静态文字定义不同 | 不静默合并语义 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | 外部字段的版本、类型、可选性、单位和范围以 canonical SDK 为准，源码偏差进入兼容风险 | AC-1.1~AC-2.8 |
| 帧内历史归属事件 | 历史点随单次 TouchEventInfo 传递，不作为跨回调持久缓存 | AC-1.1~AC-1.7 |
| 重采样字段白名单 | 仅坐标和时间参与线性插值，高级字段不补造插值值 | AC-3.1, AC-3.2 |
| Native 固定容量 | Native 回调数据保持 20×10 固定上限，不修改 ABI 数据结构 | AC-5.1~AC-5.3 |
| 当前实现即规格 | index 忽略、共享坐标、size=0 等行为仅记录风险，不在文档任务中修改源码 | AC-2.6、AC-4.1、AC-5.4~AC-5.8 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 同 finger ID 的帧内 MOVE 继续聚合后派发，不为每个历史点新增应用回调 | Pipeline 集成测试 | `pipeline_context.cpp:4779-4825,4898-4955` |
| 功耗 | 历史数据仅随输入/vsync 处理，不新增轮询或后台采样 | 架构审查 | `pipeline_context.cpp:1259,4798-4825` |
| 内存 | Native history 固定最多 20×10 点；ArkTS history 生命周期限于当前事件 | 容量边界测试 | `node_common_modifier.cpp:129-130,11287-11335` |
| 安全 | 不向 ArkTS/Native 转移 MMI PointerEvent 所有权；公开 getter 只读取事件包装数据 | 生命周期检查 | `touch_event.cpp:127-130`；`node_common_modifier.cpp:11381` |
| 可靠性 | 插值前验证样本数、时间间隔、方向和 display；失败时回退原始点 | 重采样算法单测 | `resample_algo.cpp:144-226`；`event_manager.cpp:2790-2806` |
| 可测试性 | pressure、角度、面积、历史双索引和 density 均可独立参数化 | Host/C API 单测 | `ui_input_event_test.cpp`；`touch_event_test_ng.cpp` |
| 自动化维测 | Native API 20+ 使用 latest status 定位空历史、越界和类型错误 | C API 状态单测 | `ui_input_event_impl.h:88-99`；`ui_input_event.h:2150-2165` |
| 定界定位 | MMI、Pipeline、Actuator、ArkTS、Native 各层保留独立 source evidence | 源码审查 | `mmi_event_convertor.cpp`、`pipeline_context.cpp`、`touch_event.cpp`、`ui_input_event.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 支持触摸历史、压力和多点；具体 pressure 上限受硬件影响 | 不把 pressure>1 判为非法硬件值 | 真机压力测试 | `common.d.ts:9361-9375` |
| 平板/手写笔设备 | tilt、roll、pressure 更常用；无对应硬件时默认 0/未提供 | 按 sourceTool 和字段可选性处理 | 手写笔集成测试 | `mmi_event_convertor.cpp:210-217` |
| 折叠屏/多屏 | targetDisplayId 不同的样本不进行跨屏重采样 | 切屏前后轨迹分段处理 | 多屏切换测试 | `event_manager.cpp:2790-2806` |
| Wearable | 相邻 MOVE 的 x/y 未变化时不加入 history | 不保证与手机获得相同数量的重复位置历史点 | wearable 构建测试 | `pipeline_context.cpp:183-191` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 本 Feat 不改变无障碍 HOVER 类型；姿态字段按输入源透传 | N/A |
| 大字体 | 否 | 历史采样和触点物理数据不依赖字体 | N/A |
| 深色模式 | 否 | 事件数据不依赖颜色模式 | N/A |
| 多窗口/分屏 | 是 | 节点 density/坐标单位和 targetDisplayId 影响历史坐标与重采样 | AC-3.2、AC-5.3~AC-5.5 |
| 多用户 | 否 | 历史数据不持久化，不跨用户存储 | N/A |
| 版本升级 | 是 | 动态 API 9/10/15/17、Native 12/15/17/20、静态 23 存在字段边界 | AC-1.1、AC-2.3~AC-2.8、AC-4.1~AC-5.7 |
| 生态兼容 | 是 | 压力换算、历史当前点重复、Native index 和历史多点偏差均可影响既有业务 | AC-1.4、AC-3.3~AC-3.5、AC-4.1、AC-5.4~AC-5.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 历史采样与高级触点信息
  作为 ArkUI 精细输入应用开发者
  我想要读取可追溯的历史点和高级触点属性
  以便正确重建帧内轨迹和手写笔状态

  Scenario: 非插值历史包含当前点
    Given 同一 finger ID 在一帧内缓存三个 MOVE 样本
    And 本帧未产生独立插值点
    When onTouch 回调读取 changedTouches 和 getHistoricalPoints
    Then changedTouches 使用 history.back
    And getHistoricalPoints 返回完整 history
    And 历史数组末项允许与 changedTouches 当前点相同

  Scenario: 插值点继承原始高级字段
    Given 两个有效 MOVE 样本满足重采样条件
    When 系统生成目标时刻的插值点
    Then 坐标和时间按算法插值
    And pressure、tilt、roll、area、pressedTime 和 hand 来自最近原始样本

  Scenario: Wearable 过滤重复位置
    Given wearable 构建连续收到 x/y 相同的 MOVE
    When Pipeline 聚合 history
    Then 重复位置样本不加入 history

  Scenario: 三种压力字段不可直接互换
    Given 同一输入 force 被转换为 BaseEvent、TouchObject 和 HistoricalPoint
    When 应用读取 pressure 和 force
    Then BaseEvent pressure 按顶层 SDK 范围解释
    And TouchObject pressure 与 HistoricalPoint force 按逐触点范围解释

  Scenario: 不同前端入口产生 pressure 偏差
    Given density 不等于 1
    When 标准动态或静态 live TouchObject 与 FrameNode/历史路径读取同一 force
    Then live TouchObject 路径可能返回 density 换算值
    And FrameNode/历史路径返回原始 force

  Scenario: Native 高级 getter 忽略 pointerIndex
    Given 普通 ON_TOUCH 事件包含三个 pressure 不同的触点
    When 使用有效 pointerIndex 0 调用 GetPressure
    Then 当前实现返回 touchPointes[2] 的 pressure
    And latest status 为 NO_ERROR

  Scenario: Native 历史容量截断
    Given 事件包含 21 个历史样本且每个样本有 11 个触点
    When Native 构造历史数组
    Then historySize 为 20
    And 每个 historyPointerCount 为 10
    And 保留列表起始处的样本和触点

  Scenario: Native 历史多点共享坐标
    Given 一个历史样本包含两个坐标不同的原始 TouchPoint
    When Native 按 pointerIndex 读取历史坐标和 pressure
    Then 两个 pointerIndex 返回相同的 historyLocation 坐标
    And pressure 分别来自各自 TouchPoint
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：基础多点/坐标由 Feat-02、事件构造注入由 Feat-04 承接
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致，每个 AC 至少关联一条规则
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突五项检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "TouchEvent history resample HistoricalPoint pressure tilt roll area hand pressedTime"
  - repo: "openharmony/interface_sdk-js"
    query: "HistoricalPoint getHistoricalPoints TouchObject pressure tilt roll InteractionHand dynamic static"
  - repo: "openharmony/arkui_ace_engine"
    query: "ArkUI PointerEvent HistoryPressure HistoryTilt TouchArea historyIndex pointerIndex"
```

**关键文档：** `specs/04-common-capability/04-common-events/01-touch-events/design.md`；`interface/sdk-js/api/@internal/component/ets/common.d.ts`；`interfaces/native/ui_input_event.h`
