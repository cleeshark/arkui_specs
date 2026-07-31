# 特性规格

> Func-04-04-11-Feat-04 多源缩放与旋转归一化：固化多指触控、触控板 Axis、Ctrl+滚轮和旋转 Axis 输入进入统一 Pinch/Rotation/GestureEvent 语义的存量行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 多源缩放与旋转归一化 |
| 特性编号 | Func-04-04-11-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic Pinch/Rotation API 7 起；Static API 23 起；Native Gesture API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 多源缩放归一化 | 补录触控双指、触控板 pinchAxisScale、Ctrl+鼠标滚轮到 PinchGesture 的既有路径 |
| ADDED | 多源旋转归一化 | 补录触控多指角度和 MMI rotate Axis 到 RotationGesture 的既有路径 |
| ADDED | 契约偏差记录 | SDK 文案称触控板双指旋转不能触发，而源码存在 rotate Axis 处理；差异显式列为版本风险 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/11-interaction-normalization/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/gesture.d.ts:1871-2080` | 已核验 |
| Static SDK | `interface/sdk-js/api/arkui/component/gesture.static.d.ets:1366-1488` | 已核验 |
| Native SDK | `interfaces/native/native_gesture.h:1051-1082` | 已核验 |
| Native getters | `interfaces/native/native_gesture.h:534-565` | 已核验 |
| Source locator | `frameworks/core/components_ng/gestures/recognizers/pinch_recognizer.cpp:95-157,303-328` | 已核验 |

> SDK 证据与目标 ace_engine 的精确版本基线未确认完全一致；可观察到的声明/实现差异按“SDK 契约优先、源码偏差入风险”处理。

## 用户故事

### US-1: 使用触控输入触发缩放和旋转

**作为** 触屏设备用户，
**我想要** 多指捏合和旋转触发统一 GestureEvent 回调，
**以便** 图像、画布和自定义组件实现缩放与旋转交互。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN PinchRecognizer 收到足够数量的 TouchEvent DOWN 且 recognizer 未失败 THEN 计算初始平均离差和中心点并进入 DETECTING | 正常 |
| AC-1.2 | WHEN触控移动使当前平均离差与初始离差之差达到 distance 阈值 THEN Pinch 被接受并按 Start/Update/End 生命周期回调 scale 和中心点 | 正常 |
| AC-1.3 | WHEN RotationRecognizer 收到足够触点并进入 DETECTING，且当前角度与初始角度差的绝对值超过 angle 阈值 THEN Rotation 被接受 | 正常 |
| AC-1.4 | WHEN rotation angle 参数 <=0 或 >360，或 pinch fingers/distance 不在公开约束范围 THEN 使用各 recognizer 的既有默认/归一化规则，不产生新的错误码 | 边界 |

### US-2: 使用 Axis 输入触发缩放

**作为** 使用触控板或鼠标的桌面设备用户，
**我想要** 触控板捏合和 Ctrl+滚轮复用 PinchGesture，
**以便** 不依赖触屏也能缩放内容。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Axis BEGIN 的 pinchAxisScale 约等于 1.0 且事件不是 rotation THEN PinchRecognizer 以 scale=1、事件位置为中心进入 DETECTING | 正常 |
| AC-2.2 | WHEN Axis BEGIN 按下 Ctrl 且 sourceTool 不是 TOUCHPAD THEN 即使没有显式 pinchAxisScale=1 也进入 Pinch DETECTING | 正常 |
| AC-2.3 | WHEN Axis UPDATE 的 pinchAxisScale 非 0 THEN scale 直接取该值；WHEN该值为 0 THEN根据水平/垂直轴符号按固定步长增减 scale | 正常 |
| AC-2.4 | WHEN fallback 轴更新使 scale <=0 THEN scale 被截断为 0，不输出负缩放值 | 边界 |
| AC-2.5 | WHEN AxisEvent 同时标记为 rotation 或 pinch 已结束 THEN Pinch Axis 更新被忽略，不与 Rotation 重复消费 | 边界 |

### US-3: 使用旋转 Axis 触发 RotationGesture

**作为** 支持旋转 Axis 的设备用户，
**我想要** 平台旋转输入进入 RotationGesture 生命周期，
**以便** 上层使用与触控旋转一致的回调接口。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN ConvertAxisEvent 接收 POINTER_ACTION_ROTATE_BEGIN/UPDATE/END THEN设置 isRotationEvent=true 并复制 rotateAxisAngle | 正常 |
| AC-3.2 | WHEN RotationRecognizer 收到 isRotationEvent=true 的 Axis BEGIN THEN 记录 initialAngle 并进入 DETECTING | 正常 |
| AC-3.3 | WHEN Axis UPDATE 的角度差超过阈值 THEN裁决接受；成功后后续 UPDATE 以归一化角度范围发送 onActionUpdate | 正常 |
| AC-3.4 | WHEN AxisEvent.isRotationEvent=false THEN RotationRecognizer 忽略该 Axis BEGIN/UPDATE，不误将滚动或 pinch 识别为旋转 | 边界 |
| AC-3.5 | WHEN Dynamic SDK 文案声明触控板双指旋转不能触发但当前源码接收 rotation Axis THEN 公开规格仍保留 SDK 限制，并将源码路径记录为版本偏差风险 | 边界 |

### US-4: 保留来源和多通道事件语义

**作为** ArkTS 或 Native 应用开发者，
**我想要** 在统一回调中读取 scale/angle、中心点和原始来源，
**以便** 对触控、触控板和鼠标进行必要的兼容处理。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN Pinch/Rotation 从 AxisEvent 生成 GestureEvent THEN 事件保留 inputEventType=AXIS、source/sourceTool/deviceId、轴字段和原始输入关联信息 | 正常 |
| AC-4.2 | WHEN ArkTS Dynamic/Static 使用 PinchGesture 或 RotationGesture THEN 公开回调类型统一为 GestureEvent，分别读取 scale/pinchCenterX/pinchCenterY 或 angle | 正常 |
| AC-4.3 | WHEN Native Gesture 回调收到 ArkUI_GestureEvent THEN可通过 OH_ArkUI_PinchGesture_GetScale/GetCenterX/GetCenterY 或 OH_ArkUI_RotationGesture_GetAngle 读取归一化结果 | 正常 |
| AC-4.4 | WHEN 输入不满足阈值、来源条件或事件类型条件 THEN recognizer 保持等待、拒绝或忽略，不把无效输入转换为成功手势 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现补录 | Pinch/Rotation Touch Host UT | `pinch_recognizer.cpp:101-131`；`rotation_recognizer.cpp:80-117` |
| AC-2.1~AC-2.5 | R-5~R-9 | 已有实现补录 | Pinch Axis Host UT | `pinch_recognizer.cpp:95-98,134-157,303-328`；`pinch_recognizer_test_ng.cpp:934-962` |
| AC-3.1~AC-3.5 | R-10~R-13 | 已有实现补录 | Convertor/Rotation Axis UT + SDK 审查 | `mmi_event_convertor.cpp:718-725`；`rotation_recognizer.cpp:120-137,270-297` |
| AC-4.1~AC-4.4 | R-14~R-17 | 已有实现补录 | ArkTS/NDK API 测试 | `native_gesture.h:534-565`；`gesture_impl.cpp:132-159` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Pinch 收集到至少 fingers 个有效触点 | 计算 initialDev 和 pinchCenter，进入 DETECTING | 已失败状态不进入 | AC-1.1 |
| R-2 | 行为 | 触控 Pinch 位移达到 distance 阈值 | 接受并输出 scale/center 生命周期回调 | 仅参与计算的触点按 recognizer 规则选择 | AC-1.2 |
| R-3 | 行为 | Rotation 角度差超过 angle | 接受并输出归一化 resultAngle | 使用绝对差做阈值判断 | AC-1.3 |
| R-4 | 边界 | fingers/distance/angle 超出公开范围 | 使用存量默认或归一化值 | 不新增异常或错误码 | AC-1.4 |
| R-5 | 行为 | 非 rotation Axis BEGIN 且 pinchAxisScale≈1 | scale=1、中心=事件位置并进入 DETECTING | recognizer 必须 READY | AC-2.1 |
| R-6 | 行为 | 非 TOUCHPAD Axis BEGIN 且 Ctrl 按下 | 作为 Ctrl+滚轮缩放入口进入 DETECTING | 左/右 Ctrl 均可 | AC-2.2 |
| R-7 | 行为 | Pinch Axis UPDATE | 非零 pinchAxisScale 直接赋值；否则按轴符号以固定步长更新 | 同时使用水平或垂直轴符号 | AC-2.3 |
| R-8 | 边界 | fallback scale 更新后 <=0 | 截断为 0 | 不允许负值 | AC-2.4 |
| R-9 | 边界 | rotation Axis 或 pinch end 后收到 Pinch 更新 | 忽略 | 防止交叉消费 | AC-2.5 |
| R-10 | 行为 | MMI rotate action 转换 | isRotationEvent=true，rotateAxisAngle 原值写入 AxisEvent | 仅 ROTATE_BEGIN..ROTATE_END 范围 | AC-3.1 |
| R-11 | 行为 | Rotation 收到合法 Axis BEGIN/UPDATE | BEGIN 记录初始角；UPDATE 按角度差裁决和回调 | 非 rotation event 直接返回 | AC-3.2~AC-3.4 |
| R-12 | 边界 | Dynamic SDK 与 Rotation Axis 源码能力不一致 | 对外声明以 SDK 限制为准，源码路径作为风险 | 不静默扩展公开支持范围 | AC-3.5 |
| R-13 | 异常 | Rotation Axis 不满足阈值或裁决被拒绝 | 不触发成功回调 | 保持当前实现状态机 | AC-3.3, AC-4.4 |
| R-14 | 行为 | Axis 手势生成 GestureEvent | 保留 AXIS 类型、来源、工具、deviceId 和轴数据 | Touch 路径保留 Touch 来源 | AC-4.1 |
| R-15 | 行为 | ArkTS Pinch/Rotation 回调 | 使用同一 GestureEvent 类型分别输出 scale/center 或 angle | Dynamic API 7+，Static API 23+ | AC-4.2 |
| R-16 | 行为 | Native getter 接收匹配的 GestureEvent | 返回 scale、center 或 angle | 接口错误处理按 native_gesture 实现 | AC-4.3 |
| R-17 | 异常 | 输入来源、动作或阈值不满足 | 等待、忽略或拒绝 | 不合成成功手势 | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.2, R-1~R-2 | Pinch Touch Host UT | 触点数、初始离差、中心和阈值接受 |
| VM-2 | AC-1.3~AC-1.4, R-3~R-4 | Rotation Touch 参数化 UT | 角度阈值与非法参数默认化 |
| VM-3 | AC-2.1~AC-2.2, R-5~R-6 | Pinch Axis BEGIN UT | pinchAxisScale=1 和 Ctrl+非触控板两条入口 |
| VM-4 | AC-2.3~AC-2.5, R-7~R-9 | Pinch Axis UPDATE UT | 直接 scale、步长增减、零截断和 rotation 排除 |
| VM-5 | AC-3.1~AC-3.4, R-10~R-11,R-13 | Convertor/Rotation Axis UT | rotate action、角度复制、阈值和非 rotation 忽略 |
| VM-6 | AC-3.5, R-12 | SDK-源码一致性审查 | SDK 限制与实现 Axis 路径同时可追溯 |
| VM-7 | AC-4.1~AC-4.2, R-14~R-15 | Dynamic/Static API 测试 | GestureEvent 来源与 scale/angle 字段 |
| VM-8 | AC-4.3~AC-4.4, R-16~R-17 | Native Gesture UT | 四个 getter 和无效手势不触发 |

## API 变更分析

> 本次仅补录存量行为，不产生产品 API 变更。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `PinchGesture` | Public | fingers、distance/handler options | GestureEvent 回调链 | N/A | 声明缩放手势 | AC-1.1~AC-2.5, AC-4.2 |
| `RotationGesture` | Public | fingers、angle/handler options | GestureEvent 回调链 | N/A | 声明旋转手势 | AC-1.3~AC-3.5, AC-4.2 |
| `ArkUI_NativeGestureAPI_1::createPinchGesture/createRotationGesture` | Public/NDK | fingers、distance/angle | recognizer 指针 | 参数由实现归一 | 创建 Native 缩放/旋转 recognizer | AC-4.3 |
| `OH_ArkUI_PinchGesture_GetScale/GetCenterX/GetCenterY` | Public/NDK | ArkUI_GestureEvent* | float | 非匹配事件按实现返回 | 读取缩放结果 | AC-4.3 |
| `OH_ArkUI_RotationGesture_GetAngle` | Public/NDK | ArkUI_GestureEvent* | float | 非匹配事件按实现返回 | 读取旋转结果 | AC-4.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录 | 无需迁移 | AC-1.1~AC-4.4 |

## 接口规格

### 接口定义

**PinchGesture**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `PinchGesture(value?: { fingers?: number; distance?: number } | PinchGestureHandlerOptions)`；Static: `PinchGesture.$_instantiate(..., value?: PinchGestureHandlerOptions)` |
| 返回值 | PinchGestureInterface/PinchGesture；回调接收 GestureEvent |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.5, AC-4.1~AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| fingers | number/int | 否 | 2 | 公开范围 2~5，越界使用默认值 |
| distance | number/double | 否 | 5vp | <=0 使用默认值；Axis pinchScale 路径使用设备提供的比例 |

**RotationGesture**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `RotationGesture(value?: { fingers?: number; angle?: number } | RotationGestureHandlerOptions)`；Static: `RotationGesture.$_instantiate(..., value?: RotationGestureHandlerOptions)` |
| 返回值 | RotationGestureInterface/RotationGesture；回调接收 GestureEvent |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.3~AC-1.4, AC-3.1~AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| fingers | number/int | 否 | 2 | 公开范围 2~5，越界使用默认值 |
| angle | number/double | 否 | 1deg | <=0 或 >360 使用默认值 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多指触控满足缩放/旋转阈值 | 通过 GestureEvent 输出 scale/center 或 angle | AC-1.1~AC-1.3 |
| 2 | TouchPad pinch 或 Ctrl+鼠标滚轮 Axis | 进入 Pinch 生命周期并保留 AXIS 来源 | AC-2.1~AC-2.5 |
| 3 | 平台 rotate Axis | 源码进入 Rotation 生命周期；公开支持范围受 SDK 契约限制 | AC-3.1~AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文档补录现有缩放/旋转归一化行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；scale/angle/center 仅在手势生命周期内存在。
- **最低支持版本:** Dynamic Pinch/Rotation API 7；Native Gesture API 12；Static API 23。
- **API 版本号策略:** 公开能力以 canonical SDK 和 native_gesture.h 为准；源码能力超出或不同于 SDK 文案时只记风险，不扩展契约。
- **跨输入差异:** 触控按多触点几何计算；TouchPad 可提供 pinchAxisScale；Ctrl+鼠标滚轮按固定步长转换；Rotation Axis 的公开支持存在版本偏差风险。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Axis 多语义载荷 | 同一 AxisEvent 可携带 scroll、pinch 和 rotate 字段，recognizer 必须按 isRotationEvent/axis 字段分流 | AC-2.5, AC-3.1, AC-3.4 |
| 统一回调不等于统一算法 | Touch 使用多点几何，Axis 使用比例或步长/角度值，但最终回调类型统一 | AC-1.1~AC-3.4 |
| SDK 契约优先 | 触控板旋转等声明/实现差异必须显式记录 | AC-3.5 |
| 来源可追溯 | GestureEvent/RawInputEvent 保留 source/sourceTool/deviceId 和 AXIS 类型 | AC-4.1~AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Axis UPDATE 使用常数时间比例/角度计算，不新增 IPC | 性能/源码审查 | `pinch_recognizer.cpp:303-328`；`rotation_recognizer.cpp:270-297` |
| 功耗 | 不新增轮询和后台任务 | 源码审查 | 同上 |
| 内存 | 复用 recognizer 的触点与最后 AxisEvent 状态，不新增持久数据 | Host UT | `pinch_recognizer.cpp:134-157` |
| 安全 | 不新增权限；Native getter 只读事件结果 | 安全审查 | `gesture_impl.cpp:132-159` |
| 可靠性 | scale 不低于 0，非 rotation 事件不进入 Rotation | 参数化 UT | `pinch_recognizer.cpp:317-327`；`rotation_recognizer.cpp:270-275` |
| 可测试性 | Touch、TouchPad pinch、Ctrl+wheel、rotate Axis 可独立构造 | Host UT | `pinch_recognizer_test_ng.cpp`、`rotation_recognizer_test_ng.cpp` |
| 自动化维测 | 事件保留轴值、来源和设备信息 | 字段断言 | `mmi_event_convertor.cpp:718-741` |
| 定界定位 | Convertor、Pinch、Rotation、SDK 声明可分层比较 | 一致性检查 | 本文 context-references |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 主要使用多指触控缩放/旋转 | 按触点几何和阈值识别 | 触控集成测试 | `pinch_recognizer.cpp:101-131` |
| 平板 | 可使用触控、触控板 pinch、鼠标 Ctrl+wheel | 不同算法汇聚到 GestureEvent；Rotation Axis 受契约风险约束 | 多输入集成测试 | `pinch_recognizer.cpp:134-157` |
| 折叠屏 | 窗口形态不改变手势规则 | 中心点和坐标以当前事件/节点几何为准 | 折叠/多窗口测试 | GestureEvent 坐标字段 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 本 Feat 不定义无障碍缩放动作到手势的映射 | 全部 |
| 大字体 | 否 | 不改变缩放/旋转阈值 | 全部 |
| 深色模式 | 否 | 不涉及视觉资源 | 全部 |
| 多窗口/分屏 | 是 | center 和坐标取当前窗口/事件值 | AC-1.2, AC-4.1 |
| 多用户 | 否 | 无持久化数据 | 全部 |
| 版本升级 | 是 | Dynamic 7、Native 12、Static 23 以及 SDK/源码基线差异需回归 | AC-3.5 |
| 生态兼容 | 是 | 应用不应假设所有设备都支持触控板旋转，也不应假设 Ctrl+wheel 与原生 pinch scale 完全一致 | AC-2.3, AC-3.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 多源缩放与旋转归一化
  作为 ArkUI 应用开发者
  我想要触控、触控板和鼠标输入驱动统一缩放与旋转回调
  以便复用内容变换逻辑

  Scenario: 触控板 pinch scale 触发缩放
    Given 组件注册 PinchGesture 且 recognizer 为 READY
    When Axis BEGIN 的 pinchAxisScale 约等于 1 并随后更新为 1.2
    Then Pinch 进入 DETECTING 并输出 scale 1.2
    And GestureEvent 的 inputEventType 为 AXIS

  Scenario: Ctrl 加鼠标滚轮触发缩放
    Given 组件注册 PinchGesture
    When 非 TOUCHPAD Axis BEGIN 携带 Ctrl 且 UPDATE 的 pinchAxisScale 为 0
    Then recognizer 进入 DETECTING
    And scale 按滚轮轴符号以固定步长变化且不低于 0

  Scenario: 旋转 Axis 被正确分流
    Given 平台发送 ROTATE_BEGIN 和 ROTATE_UPDATE
    When rotateAxisAngle 的差值超过 RotationGesture 阈值
    Then RotationGesture 被接受并发送 angle 更新
    And PinchRecognizer 不消费该 rotation Axis

  Scenario: SDK 与源码旋转能力偏差
    Given SDK 文案声明触控板双指旋转不能触发
    And 当前源码存在 rotation Axis 处理路径
    When 形成公开兼容性结论
    Then 以 SDK 限制作为对外契约
    And 将源码路径记录为待版本对齐风险
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：不含内容缩放渲染、组件私有变换、系统级无障碍缩放
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AxisEvent PinchRecognizer RotationRecognizer Ctrl wheel touchpad scale rotate 来源追踪"
  - repo: "openharmony/interface_sdk-js"
    query: "Dynamic Static PinchGesture RotationGesture GestureEvent scale angle trackpad 契约"
```

**关键文档：** `adapter/ohos/entrance/mmi_event_convertor.cpp:718-741`；`frameworks/core/components_ng/gestures/recognizers/pinch_recognizer.cpp:95-157,303-328`；`frameworks/core/components_ng/gestures/recognizers/rotation_recognizer.cpp:120-137,270-297`；`interfaces/native/native_gesture.h:534-565,1051-1082`。
