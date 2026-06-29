# 特性规格

> Func-04-04-06-Feat-01 基础手势：固化 Tap/LongPress/Pan/Pinch/Rotation/Swipe 六种基本手势类型和 gesture/priorityGesture/parallelGesture 挂载 API + GestureMask 的行为规格。仅 NG 框架。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 基础手势 (Basic Gestures) |
| 特性编号 | Func-04-04-06-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7（Tap/Pan），API 8（LongPress/Pinch/Rotation/Swipe） |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/06-gesture-capability/design.md` | Baselined |

---

## 用户故事

### US-1: 点击手势（TapGesture）

**作为** 应用开发者,
**我想要** 通过 TapGesture 为组件绑定点击/多击/多指点击手势,
**以便** 响应用户的点击交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `TapGesture({count: 1, fingers: 1})` THEN 单指单击即可触发 onAction 回调 | 正常 |
| AC-1.2 | WHEN 创建 `TapGesture({count: N})` THEN 需在 MULTI_TAP_TIMEOUT(300ms) 间隔内完成 N 次点击才触发 onAction | 边界 |
| AC-1.3 | WHEN 创建 `TapGesture({fingers: N})` THEN 需有 N 个手指同时按下才触发；若 isLimitFingerCount=false（默认），则 ≥N 指也可触发 | 正常 |
| AC-1.4 | WHEN 多指按下时各手指间隔超过 MULTI_FINGER_TIMEOUT(300ms) THEN 识别失败 | 异常 |
| AC-1.5 | WHEN 按下后手指移动超过 distanceThreshold THEN 识别失败（distanceThreshold 默认为 infinity，即不限移动距离） | 异常 |
| AC-1.6 | WHEN 多击时两次点击的焦距（两触点中心距离）超过 MAX_THRESHOLD_MANYTAP(60vp) THEN 识别失败 | 异常 |
| AC-1.7 | WHEN 点击次数未达 count 且超过 MULTI_TAP_TIMEOUT(300ms) THEN 识别失败（tappedCount 重置） | 异常 |

### US-2: 长按手势（LongPressGesture）

**作为** 应用开发者,
**我想要** 通过 LongPressGesture 为组件绑定长按手势,
**以便** 响应用户的长按交互（可配置持续时间和是否重复触发）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 创建 `LongPressGesture({duration: D})` THEN 手指按下后持续 D 毫秒不抬起即触发 onAction（默认 500ms） | 正常 |
| AC-2.2 | WHEN 创建 `LongPressGesture({repeat: true})` THEN 首次触发后每隔 duration 毫秒重复触发 onAction | 正常 |
| AC-2.3 | WHEN 创建 `LongPressGesture({repeat: false})`（默认）THEN 仅触发一次 onAction | 正常 |
| AC-2.4 | WHEN 长按过程中手指移动超过 allowableMovement(默认 15px) THEN 识别失败，触发 onActionCancel | 异常 |
| AC-2.5 | WHEN 手指抬起 THEN 触发 onActionEnd 回调 | 正常 |
| AC-2.6 | WHEN 创建 `LongPressGesture({fingers: N})` THEN 需 N 指同时按下；若 isLimitFingerCount=false（默认），则 ≥N 指也可触发 | 正常 |
| AC-2.7 | WHEN 长按成功后手指移动不超过 allowableMovement THEN 保持识别状态，不触发取消 | 边界 |

### US-3: 拖动手势（PanGesture）

**作为** 应用开发者,
**我想要** 通过 PanGesture 为组件绑定拖动手势,
**以便** 响应用户的拖动交互并获取实时位移数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 创建 `PanGesture({distance: D})` THEN 手指移动距离超过 D(vp) 后触发 onActionStart，随后持续触发 onActionUpdate | 边界 |
| AC-3.2 | WHEN 创建 `PanGesture({direction: PanDirection.Horizontal})` THEN 仅水平方向（角度偏差 ≤45°）的拖动才触发 | 正常 |
| AC-3.3 | WHEN 创建 `PanGesture({direction: PanDirection.Vertical})` THEN 仅垂直方向（角度偏差 ≤45°）的拖动才触发 | 正常 |
| AC-3.4 | WHEN 创建 `PanGesture({direction: PanDirection.All})`（默认）THEN 所有方向均可触发 | 正常 |
| AC-3.5 | WHEN 手指抬起 THEN 触发 onActionEnd 回调 | 正常 |
| AC-3.6 | WHEN 拖动方向与指定方向夹角 >45° THEN 该方向位移不计入触发距离 | 正常 |
| AC-3.7 | WHEN 创建 `PanGesture({fingers: N})` THEN 需 N 指同时按下；若 isLimitFingerCount=false（默认），则 ≥N 指也可触发 | 正常 |
| AC-3.8 | WHEN 手指按下后未移动即抬起 THEN 不触发任何回调（未达 distance 阈值） | 正常 |
| AC-3.9 | WHEN onActionUpdate 回调中 THEN GestureEvent.offsetX/offsetY 提供相对于初始触点的累计位移 | 正常 |

### US-4: 捏合手势（PinchGesture）

**作为** 应用开发者,
**我想要** 通过 PinchGesture 为组件绑定捏合手势,
**以便** 响应用户的双指/多指缩放交互并获取缩放比例。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 创建 `PinchGesture({distance: D})` THEN 双指间距离变化超过 D(vp) 后触发 onActionStart | 边界 |
| AC-4.2 | WHEN 捏合过程中 THEN GestureEvent.scale 提供当前缩放比例（= currentDev / initialDev） | 正常 |
| AC-4.3 | WHEN 缩放比例计算基于所有活跃手指到焦点的平均偏差比 THEN 焦点为所有活跃手指的平均 X/Y 坐标 | 正常 |
| AC-4.4 | WHEN 手指抬起剩余手指数 < fingers THEN 触发 onActionEnd | 边界 |
| AC-4.5 | WHEN 创建 `PinchGesture({fingers: N})` THEN 需 ≥N 指（或精确 =N 指，取决于 isLimitFingerCount）才触发 | 正常 |
| AC-4.6 | WHEN onActionUpdate THEN GestureEvent 提供缩放中心点（捏合焦点坐标） | 正常 |

### US-5: 旋转手势（RotationGesture）

**作为** 应用开发者,
**我想要** 通过 RotationGesture 为组件绑定旋转手势,
**以便** 响应用户的双指/多指旋转交互并获取旋转角度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 创建 `RotationGesture({angle: A})` THEN 双指旋转累计角度超过 A 度后触发 onActionStart | 边界 |
| AC-5.2 | WHEN 旋转过程中 THEN GestureEvent.angle 提供当前累计旋转角度（度数） | 正常 |
| AC-5.3 | WHEN 角度计算取前两个活跃手指的连线角度变化 THEN 通过 atan2 计算向量角度并累计差值 | 正常 |
| AC-5.4 | WHEN 角度跨越 ±180° 边界 THEN 归一化正确累加（不会因角度跳变导致计算错误） | 异常 |
| AC-5.5 | WHEN 手指抬起剩余手指数 < fingers THEN 触发 onActionEnd | 边界 |
| AC-5.6 | WHEN 创建 `RotationGesture({fingers: N})` THEN 需 ≥N 指（或精确 =N 指，取决于 isLimitFingerCount）才触发 | 正常 |

### US-6: 滑动手势（SwipeGesture）

**作为** 应用开发者,
**我想要** 通过 SwipeGesture 为组件绑定滑动手势,
**以便** 响应用户的快速滑动交互并获取滑动速度和方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 创建 `SwipeGesture({speed: S})` THEN 手指抬起时计算速度 ≥ S(vp/s) 才触发 onAction | 正常 |
| AC-6.2 | WHEN 创建 `SwipeGesture({direction: SwipeDirection.Horizontal})` THEN 仅水平滑动（角度与水平线夹角 ≤45°）才触发 | 正常 |
| AC-6.3 | WHEN 创建 `SwipeGesture({direction: SwipeDirection.Vertical})` THEN 仅垂直滑动才触发 | 正常 |
| AC-6.4 | WHEN 创建 `SwipeGesture({direction: SwipeDirection.All})`（默认）THEN 所有方向均可触发 | 正常 |
| AC-6.5 | WHEN 滑动过程中角度变化超过 45° THEN 识别失败（CheckAngle 判定非直线滑动） | 异常 |
| AC-6.6 | WHEN 滑动手指移动总距离 < SWIPE_MOVE_LIMITED(3.0) THEN 识别失败（非有效滑动） | 异常 |
| AC-6.7 | WHEN 识别成功 THEN GestureEvent 提供滑动速度和方向信息 | 正常 |
| AC-6.8 | WHEN 创建 `SwipeGesture({fingers: N})` THEN 需 ≥N 指（或精确 =N 指，取决于 isLimitFingerCount）才触发 | 正常 |
| AC-6.9 | WHEN 滑动速度计算 = 总位移 / 持续时间 THEN duration 为首个 TouchDown 到最后一个 TouchUp 的时间差 | 正常 |

### US-7: 手势挂载 API

**作为** 应用开发者,
**我想要** 通过 gesture/priorityGesture/parallelGesture 将手势绑定到组件,
**以便** 控制手势的优先级和并行关系。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.gesture(gesture)` THEN 以 Low 优先级挂载手势，子组件手势优先于父组件的 gesture() | 正常 |
| AC-7.2 | WHEN 调用 `.priorityGesture(gesture)` THEN 以 High 优先级挂载手势，父组件手势优先于子组件的 gesture() | 正常 |
| AC-7.3 | WHEN 调用 `.parallelGesture(gesture)` THEN 以 Parallel 优先级挂载手势，父子组件手势可同时识别 | 正常 |
| AC-7.4 | WHEN 调用 `.gesture(gesture, GestureMask.IgnoreInternal)` THEN 子组件的内置手势被抑制，但子组件通过 gesture() 添加的自定义手势不受影响 | 正常 |
| AC-7.5 | WHEN 调用 `.gesture(gesture, GestureMask.Normal)`（默认）THEN 子组件手势正常处理 | 正常 |
| AC-7.6 | WHEN 同一组件多次调用 gesture() THEN 后调用的手势追加到组件的手势层级中（不替换） | 正常 |

### US-8: 手指数控制（isLimitFingerCount）

**作为** 应用开发者,
**我想要** 通过 isLimitFingerCount 控制多指手势的手指匹配策略,
**以便** 灵活控制手势触发条件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN isLimitFingerCount=false（默认）且 fingers=2 THEN 2 指、3 指、4 指等 ≥2 指触摸均可触发 | 正常 |
| AC-8.2 | WHEN isLimitFingerCount=true 且 fingers=2 THEN 仅精确 2 指触摸触发，3 指触摸不触发 | 正常 |
| AC-8.3 | WHEN 触摸过程中手指数量从 2 增加到 3 THEN isLimitFingerCount=false 时保持识别；isLimitFingerCount=true 时识别失败 | 异常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.7 | R-1, R-2, R-6~R-10, R-39~R-41 | 已有实现 | 单测/XTS | `test/unittest/core/gestures/` |
| AC-2.1~2.7 | R-1, R-2, R-11~R-15, R-42~R-43 | 已有实现 | 单测/XTS | 同上 |
| AC-3.1~3.9 | R-1, R-2, R-16~R-20 | 已有实现 | 单测/XTS | 同上 |
| AC-4.1~4.6 | R-1, R-2, R-21~R-23 | 已有实现 | 单测/XTS | 同上 |
| AC-5.1~5.6 | R-1, R-2, R-24~R-26 | 已有实现 | 单测/XTS | 同上 |
| AC-6.1~6.9 | R-1, R-2, R-27~R-31, R-44 | 已有实现 | 单测/XTS | 同上 |
| AC-7.1~7.6 | R-3, R-4, R-32~R-36 | 已有实现 | 单测/集成 | `test/unittest/core/event/` |
| AC-8.1~8.3 | R-5, R-37~R-38 | 已有实现 | 单测 | `test/unittest/core/gestures/` |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 适用于所有手势类型 | 6 种手势分为两类回调模式：离散手势（Tap/Swipe）仅触发 onAction；连续手势（LongPress/Pan/Pinch/Rotation）有完整生命周期 onActionStart/Update/End + onActionCancel | — | AC-1.1~6.9 |
| R-2 | 行为 | fingers 参数有效范围 1~10 | 多指手势（除单指 Tap 外）均继承 MultiFingersRecognizer，受 fingers 和 isLimitFingerCount 控制 | — | AC-1.3, AC-2.6, AC-3.7, AC-4.5, AC-5.6, AC-6.8 |
| R-3 | 行为 | 父子组件同时绑定手势时适用 | 手势优先级分三级：Low（gesture）、High（priorityGesture）、Parallel（parallelGesture），影响父子组件手势竞争结果 | — | AC-7.1~7.3 |
| R-4 | 行为 | 需配合 priorityGesture 使用效果最显著 | GestureMask.IgnoreInternal 仅抑制子组件的内置手势（如 List 的滚动、Button 的点击），不影响子组件通过 gesture() 添加的用户自定义手势 | — | AC-7.4 |
| R-5 | 行为 | 适用于所有支持 fingers 参数的手势 | isLimitFingerCount 默认 false 表示 fingers 为最低要求（≥即可）；true 表示必须精确匹配 | — | AC-8.1~8.3 |
| R-6 | 行为 | 创建 TapGesture 实例 | TapGesture 创建 ClickRecognizer（非 TapRecognizer），保持历史命名兼容 | Gesture→Recognizer 映射 | AC-1.1 |
| R-7 | 行为 | 多指按下 | ClickRecognizer 在 TouchDown 时追踪手指，若未达 fingers_ 则启动 fingerDeadlineTimer_(300ms) | ClickRecognizer | AC-1.4 |
| R-8 | 行为 | 手指抬起 | ClickRecognizer 在 TouchUp 时 tappedCount_++，若 tappedCount_==count_ 则 ACCEPT，否则启动 tapDeadlineTimer_(300ms) | ClickRecognizer | AC-1.2, AC-1.7 |
| R-9 | 行为 | TouchMove | ClickRecognizer 检查移动距离：若超过 distanceThreshold_（默认 infinity）或单次点击超过 MAX_THRESHOLD(20vp) 则 REJECT | ClickRecognizer | AC-1.5 |
| R-10 | 行为 | TouchUp 计算焦距 | 多击时两次点击的触点中心距离超过 MAX_THRESHOLD_MANYTAP(60vp) 则 REJECT | ClickRecognizer | AC-1.6 |
| R-11 | 行为 | 手指按下 | LongPressRecognizer 在 TouchDown 后启动 deadlineTimer_(duration 毫秒)，超时后触发 onAction | LongPressRecognizer | AC-2.1 |
| R-12 | 行为 | 超时触发后 | LongPressRecognizer repeat_=true 时，首次触发后每隔 duration_ 毫秒重复触发 onAction | LongPressRecognizer | AC-2.2 |
| R-13 | 行为 | TouchMove | LongPressRecognizer 在 MOVE 时检查手指移动是否超过 allowableMovement_(默认 15px)，超过则 REJECT | LongPressRecognizer | AC-2.4 |
| R-14 | 行为 | 手指抬起 | LongPressRecognizer 在 TouchUp 时触发 onActionEnd | LongPressRecognizer | AC-2.5 |
| R-15 | 行为 | 移动超限或外部取消 | LongPressRecognizer 取消时触发 onActionCancel | LongPressRecognizer | AC-2.4 |
| R-16 | 行为 | TouchMove | PanRecognizer 通过 IsPanGestureAccept 进行方向判定：计算 atan2(dy, dx) 角度与指定方向的偏差 | PanRecognizer | AC-3.2~3.4, AC-3.6 |
| R-17 | 行为 | 距离达标 | PanRecognizer 在移动距离超过 distance_(默认 5.0vp) 后 ACCEPT，触发 onActionStart | PanRecognizer | AC-3.1 |
| R-18 | 行为 | 识别成功后 TouchMove | PanRecognizer 持续 MOVE 时触发 onActionUpdate，提供 offsetX/offsetY | PanRecognizer | AC-3.9 |
| R-19 | 行为 | 手指抬起 | PanRecognizer 在 TouchUp 时触发 onActionEnd | PanRecognizer | AC-3.5 |
| R-20 | 行为 | TouchUp（距离不足） | PanRecognizer 未达 distance 即抬起时不触发任何回调 | PanRecognizer | AC-3.8 |
| R-21 | 行为 | TouchMove | PinchRecognizer 通过 ComputeAverageDeviation 计算缩放比例：scale_ = currentDev_ / initialDev_ | PinchRecognizer | AC-4.2, AC-4.3 |
| R-22 | 行为 | 计算焦点 | PinchRecognizer 焦点为所有活跃手指的平均 X/Y 坐标 | PinchRecognizer | AC-4.3 |
| R-23 | 行为 | currentDev_-initialDev_ | PinchRecognizer 在 | ≥ distance_ 时 ACCEPT | 距离变化达标 |
| R-24 | 行为 | TouchMove | RotationRecognizer 取前两个活跃手指通过 atan2 计算连线角度，累计角度变化 | RotationRecognizer | AC-5.2, AC-5.3 |
| R-25 | 行为 | 角度计算 | RotationRecognizer 将角度归一化到 [-180°, 180°] 范围，跨边界时正确累加 | RotationRecognizer | AC-5.4 |
| R-26 | 行为 | cumulativeAngle_ | RotationRecognizer 在 | ≥ angle_ 时 ACCEPT | 累计角度达标 |
| R-27 | 行为 | TouchMove | SwipeGestureRecognizer 通过 CheckAngle 检查滑动过程中角度变化不超过 45° | SwipeRecognizer | AC-6.5 |
| R-28 | 行为 | 手指抬起 | SwipeGestureRecognizer 在 TouchUp 时计算速度 = 总位移 / 持续时间 | SwipeRecognizer | AC-6.9 |
| R-29 | 行为 | 速度和方向判定 | SwipeGestureRecognizer 速度 ≥ speed_(默认 300vp/s) 且方向匹配时 ACCEPT | SwipeRecognizer | AC-6.1 |
| R-30 | 行为 | θ\ | SwipeGestureRecognizer 方向判定：HORIZONTAL 为 \ | ≤ 45°，VERTICAL 为 \ | \ |
| R-31 | 行为 | 位移不足 | SwipeGestureRecognizer 总位移 < SWIPE_MOVE_LIMITED(3.0) 时 REJECT | SwipeRecognizer | AC-6.6 |
| R-32 | 行为 | 调用 .gesture() | gesture() 通过 GestureEventHub::AddGesture 以 GesturePriority::Low 挂载 | GestureEventHub | AC-7.1 |
| R-33 | 行为 | 调用 .priorityGesture() | priorityGesture() 通过 AddGesture 以 GesturePriority::High 挂载 | GestureEventHub | AC-7.2 |
| R-34 | 行为 | 调用 .parallelGesture() | parallelGesture() 通过 AddGesture 以 GesturePriority::Parallel 挂载 | GestureEventHub | AC-7.3 |
| R-35 | 行为 | 未指定 mask | GestureMask.Normal 为默认值，父子手势按正常优先级竞争 | GestureEventHub | AC-7.5 |
| R-36 | 行为 | 指定 mask=IgnoreInternal | GestureMask.IgnoreInternal 仅抑制子组件内置手势，不影响用户通过 gesture() 添加的自定义手势 | GestureEventHub | AC-7.4 |
| R-37 | 行为 | 默认行为 | isLimitFingerCount=false 时 fingers 为最低要求，activeFingers.size() >= fingers 即满足 | MultiFingersRecognizer | AC-8.1 |
| R-38 | 行为 | 显式设置 | isLimitFingerCount=true 时 activeFingers.size() 必须 == fingers，多一个都不触发 | MultiFingersRecognizer | AC-8.2, AC-8.3 |
| R-39 | 异常 | 各手指按下间隔 > MULTI_FINGER_TIMEOUT(300ms) | 多指按下超时 | 识别失败（REJECT） | AC-1.4 |
| R-40 | 异常 | 两次点击间隔 > MULTI_TAP_TIMEOUT(300ms) | 多击超时 | tappedCount 重置，识别失败 | AC-1.7 |
| R-41 | 异常 | 两次点击触点中心距离 > MAX_THRESHOLD_MANYTAP(60vp) | 多击焦距过大 | 识别失败 | AC-1.6 |
| R-42 | 异常 | 长按过程中手指移动 > allowableMovement(15px) | 长按移动超限 | 触发 onActionCancel，识别失败 | AC-2.4 |
| R-43 | 异常 | duration 未达前手指抬起 | 长按手指抬起 | 识别失败，不触发 onAction | — |
| R-44 | 异常 | 滑动过程中角度变化 >45° | 滑动非直线 | CheckAngle 失败，识别失败 | AC-6.5 |
| R-45 | 异常 | 触摸手指数 > fingers 且 isLimitFingerCount=true | 手指数超限（isLimitFingerCount=true） | 识别失败 | AC-8.2 |
| R-46 | 异常 | 开发者回调中抛出异常 | 手势回调异常 | UI 线程可能阻塞，框架不捕获回调异常 | — |
| R-47 | 恢复 | 识别失败（REJECT/FAIL） | RefereeState 重置为 READY，等待下一轮触摸事件序列 | 识别器恢复到初始状态，可接受新的触摸序列 | — |
| R-48 | 恢复 | 识别成功后（SUCCEED） | 手指全部抬起后 RefereeState 重置为 READY | 识别器恢复到初始状态 | — |
| R-49 | 恢复 | TouchCancel 事件 | 立即触发 onActionCancel（连续手势），状态重置为 READY | 回调通知开发者手势被取消 | — |
| R-50 | 恢复 | 组件销毁 | GestureEventHub 析构时清理所有手势识别器 | 识别器被释放，不会触发任何回调 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-6~R-10, AC-1.1~1.7 | 单测 | ClickRecognizer 单击/多击/多指/超时/移动超限 |
| VM-2 | R-11~R-15, AC-2.1~2.7 | 单测 | LongPressRecognizer 持续时间/重复/移动超限/生命周期 |
| VM-3 | R-16~R-20, AC-3.1~3.9 | 单测 | PanRecognizer 方向过滤/距离阈值/位移计算 |
| VM-4 | R-21~R-23, AC-4.1~4.6 | 单测 | PinchRecognizer scale 计算/焦点/距离判定 |
| VM-5 | R-24~R-26, AC-5.1~5.6 | 单测 | RotationRecognizer 角度计算/归一化/累计 |
| VM-6 | R-27~R-31, AC-6.1~6.9 | 单测 | SwipeRecognizer 速度/方向/直线判定 |
| VM-7 | R-32~R-36, AC-7.1~7.6 | 集成测试 | GestureEventHub 优先级和 GestureMask |
| VM-8 | R-37~R-38, AC-8.1~8.3 | 单测 | isLimitFingerCount 最低要求 vs 精确匹配 |
| VM-9 | 全量 | XTS/集成 | 端到手势交互正确 |
| VM-10 | R-1 | 集成测试 | 离散 vs 连续手势回调模式差异 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `TapGesture(value?: {count?: number; fingers?: number})` | Public | 创建点击手势 | AC-1.1~1.7 |
| `LongPressGesture(value?: {fingers?: number; repeat?: boolean; duration?: number})` | Public | 创建长按手势 | AC-2.1~2.7 |
| `PanGesture(value?: {fingers?: number; direction?: PanDirection; distance?: number})` | Public | 创建拖动手势 | AC-3.1~3.9 |
| `PinchGesture(value?: {fingers?: number; distance?: number})` | Public | 创建捏合手势 | AC-4.1~4.6 |
| `RotationGesture(value?: {fingers?: number; angle?: number})` | Public | 创建旋转手势 | AC-5.1~5.6 |
| `SwipeGesture(value?: {fingers?: number; direction?: SwipeDirection; speed?: number})` | Public | 创建滑动手势 | AC-6.1~6.9 |
| `gesture(gesture: GestureType, mask?: GestureMask): T` | Public | 挂载普通优先级手势 | AC-7.1, AC-7.4~7.6 |
| `priorityGesture(gesture: GestureType, mask?: GestureMask): T` | Public | 挂载高优先级手势 | AC-7.2 |
| `parallelGesture(gesture: GestureType, mask?: GestureMask): T` | Public | 挂载并行手势 | AC-7.3 |

**C-API (NDK)：**

| API | 参数 | 功能 | 关联 AC |
|-----|------|------|---------|
| `ArkUI_NodeHandle createTapGesture(countNum, fingersNum)` | 点击次数, 手指数 | 创建点击手势 | AC-1.1~1.7 |
| `ArkUI_NodeHandle createLongPressGesture(fingersNum, repeatResult, durationNum)` | 手指数, 是否重复, 持续时间 | 创建长按手势 | AC-2.1~2.7 |
| `ArkUI_NodeHandle createPanGesture(fingersNum, directions, distanceNum)` | 手指数, 方向掩码, 距离 | 创建平移手势 | AC-3.1~3.9 |
| `ArkUI_NodeHandle createPinchGesture(fingersNum, distanceNum)` | 手指数, 距离 | 创建捏合手势 | AC-4.1~4.6 |
| `ArkUI_NodeHandle createRotationGesture(fingersNum, angleNum)` | 手指数, 角度 | 创建旋转手势 | AC-5.1~5.6 |
| `ArkUI_NodeHandle createSwipeGesture(fingersNum, directions, speedNum)` | 手指数, 方向, 速度 | 创建滑动手势 | AC-6.1~6.9 |
| `addGestureToNode(node, recognizer, priority, mask)` | 节点, 识别器, 优先级, 掩码 | 挂载手势到节点 | AC-7.1~7.6 |

**关联枚举类型：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `GestureMask` | `{ Normal, IgnoreInternal }` | `common.d.ts` |
| `PanDirection` | `{ All, Horizontal, Vertical, Left, Right, Up, Down, None }` | `common.d.ts` |
| `SwipeDirection` | `{ None, Horizontal, Vertical, All }` | `common.d.ts` |
| `GesturePriority` | `{ Low, High, Parallel }` | `gesture_info.h` |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

---

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 12**: TapGesture 新增 distanceThreshold 参数（新增可选参数，不影响旧调用）
  - 各手势 @since 版本不同：Tap/Pan @since 7，LongPress/Pinch/Rotation/Swipe @since 8
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** @since 7/8 为基础版本，后续新增参数通过可选参数扩展

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| RefereeState 统一状态机 | 所有识别器共享 READY→DETECTING→PENDING/SUCCEED/FAIL 状态转换 | 全部 |
| UI 线程同步执行 | 手势识别和回调在 UI 线程同步执行，回调不可阻塞 | 全部 |
| 单向依赖 | API 层 → Gesture 层 → Recognizer 层 → EventHub 层，不可反向调用 | 全部 |
| Gesture→Recognizer 映射 | TapGesture→ClickRecognizer（历史命名），其他 5 种 1:1 同名映射 | AC-1.1 |
| 多指手势共享 MultiFingersRecognizer | Pan/Pinch/Rotation/Swipe/LongPress 共享多指基础能力（fingers/isLimitFingerCount/activeFingers） | AC-2.6, AC-3.7, AC-4.5, AC-5.6, AC-6.8 |

> 架构规则适用性及设计方案见 design.md。

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次触摸事件分发到识别器判定 < 1ms | benchmark | — |
| 内存 | 每个手势识别器对象 < 512 字节 | hidumper | — |
| 安全 | N/A — 手势 API 无权限要求 | — | — |
| 可靠性 | 状态机异常后可 Reset 到 READY | 单测 | R-47~R-50 |
| 问题定位 | GestureEvent 包含 source/device/toolType 可追溯触摸来源 | 日志 | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 手势本身无语义，但 onClick（TapGesture）与无障碍 click action 关联 | TapGesture 触发时需同步无障碍事件 |
| 大字体 | N/A | 手势参数不涉及字体大小 | — |
| 深色模式 | N/A | 手势参数不涉及颜色 | — |
| 多窗口/分屏 | 是 | 分屏后触摸事件坐标映射到对应窗口，手势识别不受影响 | 多窗口下触摸坐标正确 |
| 多用户 | N/A | 手势无用户态差异 | — |
| 版本升级 | 是 | 各手势 @since 版本不同（7 vs 8），API 12 新增 distanceThreshold 参数 | TapGesture distanceThreshold |
| 生态兼容 | 是 | C-API (NDK) 提供等效接口，行为应与 ArkTS 一致 | 全部 C-API 手势 |

---

## 行为场景（可选，Gherkin）

```gherkin
Feature: 基础手势
  作为 应用开发者
  我想要 通过声明式 API 为组件绑定点击/长按/拖动/捏合/旋转/滑动手势
  以便 响应用户的多指触摸交互

  # ─── TapGesture ──────────────────────────────────

  Scenario: 单指单击
    Given 一个 Text 组件绑定了 TapGesture({count:1, fingers:1})
    When 用户单指按下并抬起
    Then 触发 onAction 回调

  Scenario: 双击
    Given 一个 Text 组件绑定了 TapGesture({count:2})
    When 用户在 300ms 内连续点击 2 次
    Then 触发 onAction 回调

  Scenario: 双击超时
    Given 一个 Text 组件绑定了 TapGesture({count:2})
    When 用户第 1 次点击后等待 >300ms 再第 2 次点击
    Then 不触发 onAction（tappedCount 重置）

  Scenario: 多指按下超时
    Given 一个 Text 组件绑定了 TapGesture({fingers:2})
    When 用户第 1 指按下后等待 >300ms 再按第 2 指
    Then 识别失败

  Scenario: 双击焦距过大
    Given 一个 Text 组件绑定了 TapGesture({count:2})
    When 用户两次点击位置相距 70vp
    Then 识别失败（超过 MAX_THRESHOLD_MANYTAP 60vp）

  # ─── LongPressGesture ────────────────────────────

  Scenario: 长按触发
    Given 一个 Text 组件绑定了 LongPressGesture({duration:500})
    When 用户按下并保持 500ms 不抬起
    Then 触发 onAction 回调

  Scenario: 长按重复触发
    Given 一个 Text 组件绑定了 LongPressGesture({duration:500, repeat:true})
    When 用户按下并保持
    Then 首次在 500ms 时触发 onAction
    And 之后每隔 500ms 再次触发 onAction

  Scenario: 长按移动超限取消
    Given 一个 Text 组件绑定了 LongPressGesture({duration:500})
    When 用户按下后移动超过 15px
    Then 触发 onActionCancel

  # ─── PanGesture ──────────────────────────────────

  Scenario: 拖动触发
    Given 一个 Column 组件绑定了 PanGesture({distance:5})
    When 用户按下并移动超过 5vp
    Then 触发 onActionStart
    And 持续移动时触发 onActionUpdate（提供 offsetX/offsetY）
    And 抬起时触发 onActionEnd

  Scenario: 水平拖动方向限制
    Given 一个 Column 组件绑定了 PanGesture({direction: Horizontal})
    When 用户以 30° 角拖动（接近水平）
    Then 触发识别（角度偏差 ≤45°）

  Scenario: 水平拖动方向限制-超出角度
    Given 一个 Column 组件绑定了 PanGesture({direction: Horizontal})
    When 用户以 60° 角拖动（接近垂直）
    Then 识别失败（角度偏差 >45°）

  Scenario: 拖动距离不足
    Given 一个 Column 组件绑定了 PanGesture({distance:5})
    When 用户移动 3vp 后抬起
    Then 不触发任何回调

  # ─── PinchGesture ────────────────────────────────

  Scenario: 双指捏合
    Given 一个 Image 组件绑定了 PinchGesture({distance:5})
    When 用户双指按下并向内/向外移动，距离变化超过 5vp
    Then 触发 onActionStart
    And onActionUpdate 中 GestureEvent.scale 提供缩放比例

  Scenario: 捏合焦点计算
    Given 一个 Image 组件绑定了 PinchGesture
    When 用户两指分别位于 (100,100) 和 (200,200)
    Then 焦点为 (150, 150)
    And scale = currentDev / initialDev

  # ─── RotationGesture ────────────────────────────

  Scenario: 双指旋转
    Given 一个 Image 组件绑定了 RotationGesture({angle:1})
    When 用户双指旋转累计角度超过 1°
    Then 触发 onActionStart
    And onActionUpdate 中 GestureEvent.angle 提供累计旋转角度

  Scenario: 旋转角度跨 ±180° 边界
    Given 一个 Image 组件绑定了 RotationGesture
    When 两指连线角度从 170° 变化到 -170°（实际旋转 20°）
    Then 累计角度正确增加 20°（不因归一化跳变出错）

  # ─── SwipeGesture ───────────────────────────────

  Scenario: 快速滑动
    Given 一个 Column 组件绑定了 SwipeGesture({speed:300})
    When 用户快速滑动，抬起时速度 ≥300vp/s
    Then 触发 onAction（提供速度和方向信息）

  Scenario: 滑动速度不足
    Given 一个 Column 组件绑定了 SwipeGesture({speed:300})
    When 用户缓慢滑动，抬起时速度 <300vp/s
    Then 不触发 onAction

  Scenario: 滑动方向限制
    Given 一个 Column 组件绑定了 SwipeGesture({direction: Horizontal})
    When 用户垂直方向快速滑动
    Then 不触发 onAction（方向不匹配）

  Scenario Outline: isLimitFingerCount 手指匹配
    Given 一个组件绑定了 PanGesture({fingers:2}) 且 isLimitFingerCount=<模式>
    When 用户使用 <触摸手指数> 指触摸并拖动
    Then <预期结果>

    Examples:
      | 模式 | 触摸手指数 | 预期结果 |
      | false | 2 | 触发（≥2 指满足最低要求） |
      | false | 3 | 触发（≥2 指满足最低要求） |
      | true | 2 | 触发（精确匹配） |
      | true | 3 | 不触发（超过精确匹配） |

  # ─── 手势挂载 ────────────────────────────────────

  Scenario: gesture 普通优先级
    Given 父组件绑定了 .gesture(TapGesture())
    And 子组件绑定了 .gesture(TapGesture())
    When 用户点击子组件区域
    Then 子组件手势优先触发（Low vs Low 时子优先）

  Scenario: priorityGesture 高优先级
    Given 父组件绑定了 .priorityGesture(TapGesture())
    And 子组件绑定了 .gesture(TapGesture())
    When 用户点击子组件区域
    Then 父组件手势优先触发（High > Low）

  Scenario: parallelGesture 并行
    Given 父组件绑定了 .parallelGesture(TapGesture())
    And 子组件绑定了 .gesture(TapGesture())
    When 用户点击子组件区域
    Then 父子手势同时触发

  Scenario: GestureMask.IgnoreInternal
    Given 父组件绑定了 .priorityGesture(TapGesture(), GestureMask.IgnoreInternal)
    And 子组件为 List（内置滚动手势）
    When 用户在子组件上点击
    Then 父组件 TapGesture 触发
    And 子组件的内置滚动手势被抑制

  Scenario: GestureMask.IgnoreInternal 不影响自定义手势
    Given 父组件绑定了 .priorityGesture(TapGesture(), GestureMask.IgnoreInternal)
    And 子组件通过 .gesture(TapGesture()) 绑定了自定义手势
    When 用户在子组件上点击
    Then 子组件自定义手势仍可正常识别
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（6 种基本手势 + 3 种挂载 API + GestureMask + isLimitFingerCount；不含 GestureGroup、GestureReferee）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "TapGesture ClickRecognizer tappedCount multi-tap threshold implementation"
  - repo: "openharmony/ace_engine"
    query: "LongPressRecognizer deadlineTimer repeat allowableMovement duration"
  - repo: "openharmony/ace_engine"
    query: "PanRecognizer IsPanGestureAccept direction angle distance threshold"
  - repo: "openharmony/ace_engine"
    query: "PinchRecognizer ComputeAverageDeviation scale calculation"
  - repo: "openharmony/ace_engine"
    query: "RotationRecognizer ComputeAngle cumulativeAngle normalization"
  - repo: "openharmony/ace_engine"
    query: "SwipeRecognizer CheckAngle speed resultSpeed direction"
  - repo: "openharmony/ace_engine"
    query: "GestureEventHub AddGesture GestureMask GesturePriority"
  - repo: "openharmony/ace_engine"
    query: "MultiFingersRecognizer isLimitFingerCount activeFingers"
```

**关键文档：**
- SDK API 类型定义：`interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 架构设计：`specs/04-common-capability/04-common-events/06-gesture-capability/design.md`
