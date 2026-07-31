# 特性规格

> Func-04-04-11-Feat-03 多源滑动与平移归一化：固化触控移动、鼠标滚轮和触控板 Axis 输入进入统一 Pan/Swipe/GestureEvent 语义的存量行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 多源滑动与平移归一化 |
| 特性编号 | Func-04-04-11-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic Pan API 7 起、Swipe API 8 起；Static API 23 起；Native Gesture API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 多源连续位移归一化 | 补录 TouchEvent 与 AxisEvent 到 Pan/Swipe 的统一识别生命周期 |
| ADDED | 鼠标与触控板差异 | 补录 Mouse Wheel 序列补齐、方向过滤、TouchPad 坐标变换和来源字段 |
| ADDED | 边界声明 | 明确不包含滚动容器摩擦、惯性、回弹、边缘效果和滚动生命周期 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/11-interaction-normalization/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/gesture.d.ts:1091,1700-1868` | 已核验 |
| Static SDK | `interface/sdk-js/api/arkui/component/gesture.static.d.ets:890,1271-1363` | 已核验 |
| Native SDK | `interfaces/native/native_gesture.h:1033-1049,1084-1098` | 已核验 |
| Input SDK | `interfaces/native/ui_input_event.h:437-471` | 已核验 |
| Source locator | `frameworks/core/components_ng/gestures/recognizers/gesture_recognizer.cpp:216-250` | 已核验 |

> 本 Feat 只规格化输入到手势事件的归一化。滚动容器物理效果和消费行为属于其他 FuncID，不在本规格内。

## 用户故事

### US-1: 让 Touch 和 Axis 共享手势生命周期

**作为** ArkUI 手势开发者，
**我想要** 触控移动、鼠标滚轮和触控板滑动进入一致的开始、更新、结束、取消语义，
**以便** 使用同一 Pan/Swipe 回调处理不同底层输入。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN NGGestureRecognizer 接收 AxisAction::BEGIN THEN 记录 deviceId/source/sourceTool、将 inputEventType 设为 AXIS，并调用对应 HandleTouchDownEvent | 正常 |
| AC-1.2 | WHEN AxisAction 为 UPDATE、END 或 CANCEL THEN 分别调用 HandleTouchMoveEvent、HandleTouchUpEvent 或 HandleTouchCancelEvent | 正常 |
| AC-1.3 | WHEN AxisAction 不属于 BEGIN/UPDATE/END/CANCEL THEN 按取消路径处理，不产生未定义状态 | 异常 |
| AC-1.4 | WHEN sourceTool 不在 recognizer 允许集合且 action 不是 CANCEL THEN 事件不进入识别；BEGIN 同时清理不支持事件记录 | 边界 |

### US-2: 将 Axis 位移归一化为 Pan

**作为** 使用 PanGesture 的应用开发者，
**我想要** 触控板滑动和鼠标滚轮产生可消费的平移增量与统一回调，
**以便** 业务无需直接解析平台 AxisEvent。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN PanRecognizer 收到非旋转 Axis BEGIN 且 fingers=AXIS_PAN_FINGERS、direction!=NONE THEN 进入 DETECTING 并初始化来源、触点和速度跟踪 | 正常 |
| AC-2.2 | WHEN Axis UPDATE 到达 THEN 将 horizontalAxis/verticalAxis 转为 delta，累加 averageDistance，并按阈值进入 ACCEPT/REJECT | 正常 |
| AC-2.3 | WHEN Pan 已成功且收到后续 Axis UPDATE THEN 首次发送 onActionStart，随后发送 onActionUpdate | 正常 |
| AC-2.4 | WHEN sourceTool=MOUSE THEN 按 PanDirection 清零不允许的轴；WHEN sourceTool=TOUCHPAD THEN 对起点和终点执行节点坐标变换后计算 delta | 边界 |
| AC-2.5 | WHEN Axis 事件构造 GestureEvent THEN 输出 sourceTool、verticalAxis、horizontalAxis、pressedCodes、pointerEventId、convertInfo 和 inputEventType=AXIS | 正常 |

### US-3: 将 Axis 位移归一化为 Swipe

**作为** 使用 SwipeGesture 的应用开发者，
**我想要** Axis 序列经过方向和速度规则后触发 Swipe 回调，
**以便** 鼠标滚轮或触控板滑动可复用滑动手势逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN SwipeRecognizer 在 DETECTING 状态接收 Axis UPDATE THEN 转换 offset、过滤鼠标禁用方向并累加 axisOffset | 正常 |
| AC-3.2 | WHEN 当前 Axis offset 为零 THEN 保持当前识别状态且不更新角度 | 边界 |
| AC-3.3 | WHEN Axis 方向角不满足 SwipeDirection THEN 识别被拒绝且不调用 onAction | 异常 |
| AC-3.4 | WHEN Axis END 且累计位移非零 THEN 执行 Axis 结束判定；WHEN累计位移两个方向均为零 THEN 直接拒绝 | 边界 |
| AC-3.5 | WHEN sourceTool=MOUSE 且 Axis END 进入判定 THEN resultSpeed 固定为 0 后按当前鼠标 Axis 规则完成裁决 | 边界 |

### US-4: 适配鼠标滚轮和触控板序列差异

**作为** 输入适配层维护者，
**我想要** 对不同设备产生的 Axis 序列进行最小兼容处理，
**以便** 上层 recognizer 总能观察到完整生命周期。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN MMI 鼠标滚轮首个事件被识别为 scroll begin THEN AceView 先发送零增量 BEGIN，再构造 UPDATE 发送真实轴值，使 START/END 序列补齐为 START/UPDATE/END | 恢复 |
| AC-4.2 | WHEN ConvertAxisEvent 接收 MMI PointerEvent THEN复制水平/垂直/pinch/rotate 值、action、sourceTool、deviceId、pressedKeys 和 axes 位图 | 正常 |
| AC-4.3 | WHEN Axis BEGIN/END 的某一轴近零 THEN ValidateAxes 从有效 axes 位图中移除该轴，避免将空轴声明为有效输入 | 边界 |
| AC-4.4 | WHEN Scrollable 消费 AxisEvent THEN 可依据 sourceTool 区分 MOUSE 与 TOUCHPAD；该消费端摩擦、惯性和回弹行为不属于本 Feat | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-3 | 已有实现补录 | GestureRecognizer Host UT | `gesture_recognizer.cpp:216-250` |
| AC-2.1~AC-2.5 | R-4~R-8 | 已有实现补录 | PanRecognizer Axis Host UT | `pan_recognizer.cpp:331-377,548-609,906-929`；`pan_recognizer_axis_base_test_ng.cpp:352-355` |
| AC-3.1~AC-3.5 | R-9~R-12 | 已有实现补录 | SwipeRecognizer Axis Host UT | `swipe_recognizer.cpp:221-250,317-353`；`swipe_recognizer_test_ng.cpp:799-842` |
| AC-4.1~AC-4.4 | R-13~R-16 | 已有实现补录 | Adapter/Event/Scrollable UT | `ace_view_ohos.cpp:498-513`；`mmi_event_convertor.cpp:692-752` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Axis BEGIN/UPDATE/END/CANCEL 进入 NGGestureRecognizer | 映射到 Down/Move/Up/Cancel 处理函数 | BEGIN 设置 inputEventType=AXIS | AC-1.1, AC-1.2 |
| R-2 | 异常 | Axis action 未知 | 调用取消处理 | 不保留半完成识别状态 | AC-1.3 |
| R-3 | 边界 | sourceTool 不被允许 | 非 CANCEL 事件被忽略；BEGIN 清理不支持记录 | CANCEL 仍允许清理状态 | AC-1.4 |
| R-4 | 行为 | 合法 Axis BEGIN 进入 PanRecognizer | 初始化来源、伪触点、速度跟踪并进入 DETECTING | rotation event、错误 fingers 或 NONE 方向不进入 | AC-2.1 |
| R-5 | 行为 | Axis UPDATE 进入 PanRecognizer | 转换 delta、累积距离、进行方向/阈值裁决 | Shift 和不同方向手势状态参与 ConvertToOffset | AC-2.2 |
| R-6 | 行为 | Pan 已成功接收 UPDATE | 保证 Start 至多一次，并持续发送 Update | recognizer 必须处于 enabled | AC-2.3 |
| R-7 | 边界 | MOUSE 或 TOUCHPAD Axis 更新 | MOUSE 清零禁用轴；TOUCHPAD 在节点变换空间计算增量 | 不把两者数值处理视为完全相同 | AC-2.4 |
| R-8 | 行为 | Pan 生成 Axis GestureEvent | 携带轴值、来源、按键、转换信息和 AXIS 类型 | Touch 路径从 lastTouchEvent 取字段 | AC-2.5 |
| R-9 | 行为 | Swipe 在 DETECTING 接收非零 Axis UPDATE | 转换并累积 offset，更新方向角 | 仅鼠标执行单轴方向清零 | AC-3.1 |
| R-10 | 边界 | Swipe Axis UPDATE 为零 | 不更新累计量和角度 | 不接受也不拒绝 | AC-3.2 |
| R-11 | 异常 | Swipe Axis 方向角不满足配置 | REJECT | 不触发 onAction | AC-3.3 |
| R-12 | 边界 | Swipe Axis END | 零累计位移拒绝；非零进入结束判定；MOUSE resultSpeed=0 | 触控速度算法不直接套用鼠标滚轮 | AC-3.4, AC-3.5 |
| R-13 | 恢复 | 鼠标滚轮首包同时承担 BEGIN 和增量 | 发送零 BEGIN 后将真实包改为 UPDATE | 保证 recognizer 看到至少一次 UPDATE | AC-4.1 |
| R-14 | 行为 | MMI PointerEvent 转 AxisEvent | 复制四类轴值、动作、来源、设备和按键字段 | GetPointerItem 失败时提前返回 | AC-4.2 |
| R-15 | 边界 | BEGIN/END 的轴值近零 | 从 axes 位图移除对应轴 | pinch 轴同样适用 | AC-4.3 |
| R-16 | 边界 | AxisEvent 进入 Scrollable | 消费端可区分 MOUSE/TOUCHPAD | 容器物理效果不在本规格 | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4, R-1~R-3 | GestureRecognizer 参数化 UT | 四阶段映射、未知 action 和不支持工具 |
| VM-2 | AC-2.1~AC-2.3, R-4~R-6 | PanRecognizer Axis UT | BEGIN 初始化、阈值裁决、Start/Update 顺序 |
| VM-3 | AC-2.4~AC-2.5, R-7~R-8 | PanRecognizer 坐标/事件字段 UT | MOUSE 单轴过滤、TOUCHPAD 变换、AXIS 字段 |
| VM-4 | AC-3.1~AC-3.3, R-9~R-11 | SwipeRecognizer Axis UT | 零增量、方向过滤和拒绝 |
| VM-5 | AC-3.4~AC-3.5, R-12 | SwipeRecognizer END UT | 零累计拒绝和鼠标速度分支 |
| VM-6 | AC-4.1, R-13 | AceView Adapter UT | 鼠标首包形成 BEGIN→UPDATE→END |
| VM-7 | AC-4.2~AC-4.3, R-14~R-15 | MMI Convertor UT | 字段复制和有效 axes 位图 |
| VM-8 | AC-4.4, R-16 | Scrollable 集成测试/边界审查 | 只验证来源传递，不验证物理效果 |

## API 变更分析

> 本次仅补录存量行为，不产生产品 API 变更。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `PanGesture` | Public | fingers、direction、distance/PanGestureOptions | GestureEvent 回调链 | N/A | 声明连续平移手势 | AC-1.1~AC-2.5 |
| `SwipeGesture` | Public | fingers、direction、speed | GestureEvent 回调 | N/A | 声明一次性滑动手势 | AC-1.1~AC-3.5 |
| `ArkUI_NativeGestureAPI_1::createPanGesture` | Public/NDK | fingersNum、direction mask、distance | recognizer 指针 | 参数由实现归一 | 创建 Native Pan recognizer | AC-2.1~AC-2.5 |
| `ArkUI_NativeGestureAPI_1::createSwipeGesture` | Public/NDK | fingersNum、direction mask、speed | recognizer 指针 | 参数由实现归一 | 创建 Native Swipe recognizer | AC-3.1~AC-3.5 |
| `OH_ArkUI_UIInputEvent_GetSourceType/GetToolType` | Public/NDK | UIInputEvent | int32_t | 参数错误返回约定值 | 查询原始输入来源 | AC-2.5, AC-4.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录 | 无需迁移 | AC-1.1~AC-4.4 |

## 接口规格

### 接口定义

**PanGesture**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `PanGesture(value?: { fingers?: number; direction?: PanDirection; distance?: number } | PanGestureOptions)`；Static: `PanGesture.$_instantiate(..., value?: PanGestureHandlerOptions | PanGestureOptions)` |
| 返回值 | PanGestureInterface/PanGesture；回调接收 GestureEvent |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| fingers | number/int | 否 | 1 | Touch 范围 1~10；Axis 路径要求内部 AXIS_PAN_FINGERS |
| direction | PanDirection | 否 | All | NONE 的 Axis BEGIN 直接拒绝 |
| distance | number/double | 否 | 普通来源 5vp、手写笔 8vp（Dynamic SDK） | 小于 0 使用默认值；实际坐标受组件变换影响 |

**SwipeGesture**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `SwipeGesture(value?: { fingers?: number; direction?: SwipeDirection; speed?: number })`；Static: `SwipeGesture.$_instantiate(..., value?: SwipeGestureHandlerOptions)` |
| 返回值 | SwipeGestureInterface/SwipeGesture；识别成功调用 onAction(GestureEvent) |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| fingers | number/int | 否 | 1 | SDK 范围 1~10 |
| direction | SwipeDirection | 否 | All | Axis 更新按方向角判定 |
| speed | number/double | 否 | 100vp/s | <=0 使用默认值；鼠标 Axis END 的实现 resultSpeed=0 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Touch 序列满足 Pan/Swipe 条件 | 按各 recognizer 原有阈值触发回调 | AC-1.1~AC-3.4 |
| 2 | Mouse Wheel/TouchPad Axis 序列到达 | 映射为统一生命周期并保留 AXIS 来源字段 | AC-1.1~AC-2.5 |
| 3 | 鼠标滚轮只产生首包与结束包 | Adapter 补齐 UPDATE 后进入 recognizer | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文档补录现有 Touch/Axis 归一化行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；Axis/Pan/Swipe 数据仅存在于事件分发期间。
- **最低支持版本:** Dynamic Pan API 7、Swipe API 8；Native Gesture API 12；Static API 23。
- **API 版本号策略:** Dynamic/Static 公开签名以 canonical SDK `@since` 为准，Native 以头文件为准。
- **来源差异:** MOUSE 与 TOUCHPAD 在方向过滤和坐标变换上保留差异；统一的是业务手势生命周期，不是底层数值算法完全相同。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Adapter 负责平台序列修复 | 鼠标 BEGIN/UPDATE 补齐发生在 AceView，不在 recognizer 内伪造 | AC-4.1 |
| Recognizer 统一生命周期 | Axis action 经 NGGestureRecognizer 映射到 Down/Move/Up/Cancel | AC-1.1~AC-1.3 |
| 来源差异可见 | Pan/Swipe 可按 sourceTool 采用不同方向或坐标处理 | AC-2.4, AC-3.5 |
| 功能域边界 | 不把 Scrollable 摩擦、惯性、回弹和滚动生命周期纳入本 Feat | AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每个 Axis UPDATE 仅执行现有位移转换、变换和 recognizer 裁决，不新增 IPC | 性能/源码审查 | `pan_recognizer.cpp:565-609` |
| 功耗 | 不新增轮询、定时唤醒或后台任务 | 源码审查 | 同上 |
| 内存 | AxisEvent 和 GestureEvent 为瞬态对象，累计状态受 recognizer 生命周期管理 | Host UT | `pan_recognizer.cpp:331-377` |
| 安全 | 不新增权限和跨进程数据 | 安全审查 | `gesture_recognizer.cpp:216-250` |
| 可靠性 | 未知 action 进入 Cancel，零位移 Swipe 被拒绝 | 参数化 UT | `gesture_recognizer.cpp:230-250`；`swipe_recognizer.cpp:239-244` |
| 可测试性 | Touch/Mouse/TouchPad 可独立构造并验证相同回调类型 | Host UT | `pan_recognizer_test_ng.cpp`、`swipe_recognizer_test_ng.cpp` |
| 自动化维测 | GestureEvent 保留 inputEventType、sourceTool、轴值和 pointerEventId | 字段断言 | `pan_recognizer.cpp:906-929` |
| 定界定位 | Adapter 序列、Convertor 字段、Recognizer 裁决分层可定位 | 源码追溯 | 本文 context-references |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 主要由触控拖动触发 | 走 TouchEvent Pan/Swipe 路径 | 触控集成测试 | Pan/Swipe Touch UT |
| 平板 | 可由触控、鼠标滚轮和触控板 Axis 触发 | Axis 统一生命周期但保留 sourceTool 差异 | 多输入集成测试 | `pan_recognizer.cpp:548-562` |
| 折叠屏 | 窗口/节点变换可能改变 TouchPad delta | 在当前节点变换空间计算增量 | 变换场景 UT | `pan_recognizer.cpp:556-562` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 本 Feat 不定义无障碍滚动动作映射 | 全部 |
| 大字体 | 否 | 不改变手势识别阈值 | 全部 |
| 深色模式 | 否 | 不涉及视觉资源 | 全部 |
| 多窗口/分屏 | 是 | TouchPad delta 在目标节点当前变换空间计算 | AC-2.4 |
| 多用户 | 否 | 无持久化数据 | 全部 |
| 版本升级 | 是 | Dynamic 7/8、Native 12、Static 23 的接口可用性需回归 | 接口规格 |
| 生态兼容 | 是 | 应用不得假设 Mouse Wheel 与 TouchPad 的 delta/速度完全一致 | AC-2.4, AC-3.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 多源滑动与平移归一化
  作为 ArkUI 应用开发者
  我想要触控、鼠标滚轮和触控板驱动同一 Pan/Swipe 语义
  以便复用连续位移业务逻辑

  Scenario: 触控板 Axis 触发 Pan 更新
    Given 组件注册合法 PanGesture 且方向不为 NONE
    When TOUCHPAD Axis BEGIN 和 UPDATE 到达
    Then recognizer 进入 DETECTING 或 SUCCEED
    And GestureEvent 的 inputEventType 为 AXIS 且包含轴值和 sourceTool

  Scenario: 鼠标滚轮首包被补齐
    Given MMI 鼠标滚轮首包同时表示开始和位移
    When AceView 处理该事件
    Then recognizer 先收到零增量 BEGIN
    And 随后收到携带真实轴值的 UPDATE

  Scenario: Swipe 方向不匹配
    Given SwipeGesture 仅允许水平方向
    When Axis 更新形成不符合方向阈值的角度
    Then recognizer 被拒绝
    And onAction 不被调用

  Scenario: Scrollable 物理效果保持域外
    Given AxisEvent 已归一化并进入 Scrollable
    When 容器执行惯性或回弹
    Then 本规格只验证 sourceTool 和 Axis 数据已正确传递
    And 不对惯性、摩擦或回弹结果作验收声明
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：不含滚动容器物理效果、拖拽业务、组件私有滚动行为
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AxisEvent PanRecognizer SwipeRecognizer Mouse Wheel TouchPad 生命周期与来源字段"
  - repo: "openharmony/interface_sdk-js"
    query: "Dynamic Static PanGesture SwipeGesture GestureEvent API 契约与版本"
```

**关键文档：** `adapter/ohos/entrance/ace_view_ohos.cpp:498-513`；`adapter/ohos/entrance/mmi_event_convertor.cpp:692-752`；`frameworks/core/components_ng/gestures/recognizers/gesture_recognizer.cpp:216-250`；`frameworks/core/components_ng/gestures/recognizers/pan_recognizer.cpp:331-377,548-609,906-929`；`frameworks/core/components_ng/gestures/recognizers/swipe_recognizer.cpp:221-250,317-353`。
