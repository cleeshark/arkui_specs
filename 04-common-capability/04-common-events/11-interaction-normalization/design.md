# 架构设计

> 确认目标仓和模块的架构约束、关键设计决策、Spec 拆分方向。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-04-11 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 按键意图归一化（KeyIntention / IntentionCode），Feat-02 多源点击交互归一化，Feat-03 多源滑动与平移归一化，Feat-04 多源缩放与旋转归一化 |
| 复杂度 | 复杂 |
| 目标版本 | 按键意图：ArkTS 动态 API 10、NDK API 14、静态 API 23 起；点击/手势：Dynamic API 7/8、Native API 12、Static API 23 起 |
| Owner | ArkUI SIG |
| 状态 | Baselined（已有实现补录） |

## 需求基线

> 本功能域没有独立 proposal.md。以下基线来自已确认的存量能力补录范围和 Func-04-04-11-Feat-01 规格。

| 项 | 补充说明（如需） |
|----|------------------|
| 全链路覆盖 | 覆盖 MMI 输入接入、KeyEvent 数据模型、ArkTS 动态/静态、NDK、焦点与菜单消费、Preview 差异 |
| 公开枚举契约 | ArkTS 以 interface_sdk-js 的 14 值 IntentionCode 为权威；NDK 使用范围更大的 ArkUI_KeyIntension |
| 行为保持 | 当前实现即规格，不修改物理键映射、焦点优先级或 Preview 行为 |
| 版本兼容 | 分别声明 ArkTS 动态 API 10、NDK API 14、ArkTS 静态 API 23 |
| 风险呈现 | 通道枚举差异与 Preview UNKNOWN 行为必须显式记录，不做静默统一 |
| 多源点击（Feat-02） | 触控、鼠标、触控板、键盘 SELECT/Enter/Space 和程序化/无障碍入口汇聚到统一点击回调，同时保留可用来源差异 |
| 连续位移（Feat-03） | Touch 与 Axis 统一为 Pan/Swipe 生命周期；鼠标滚轮与触控板保留方向、坐标和速度差异；不承接滚动容器物理效果 |
| 缩放旋转（Feat-04） | 多指触控、TouchPad pinch、Ctrl+滚轮与 rotate Axis 进入 Pinch/Rotation；SDK 与源码支持范围不一致时以 SDK 为契约并显式记风险 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 补充架构说明 |
|------|--------------|
| interface_sdk-js | IntentionCode、KeyEvent.intentionCode 及按键回调入口的公开契约源 |
| arkui_ace_engine / adapter | 将 MMI KeyEvent 转换为 ACE KeyEvent；OHOS 与 Preview 路径存在差异 |
| arkui_ace_engine / frameworks/core/event | KeyIntention 枚举、KeyEvent 和 KeyEventInfo 瞬态数据模型 |
| arkui_ace_engine / frameworks/core/common、components_ng/event | 非指针事件分发、焦点意图解析和组件行为消费 |
| arkui_ace_engine / frameworks/bridge | 将 KeyEventInfo.intentionCode 暴露给 ArkTS 回调 |
| arkui_ace_engine / interfaces/native | ArkUI_KeyIntension 与 NDK getter 的公开声明和参数校验 |
| interface_sdk-js（Feat-02~04） | ClickEvent、GestureEvent、onClick、Tap/Pan/Swipe/Pinch/Rotation 的 Dynamic/Static 公开契约 |
| arkui_ace_engine / adapter/ohos/entrance（Feat-02~04） | Mouse→Touch 兼容转换、Mouse Wheel 序列补齐以及 scroll/pinch/rotate Axis 字段转换 |
| arkui_ace_engine / frameworks/core/components_ng/gestures（Feat-02~04） | Click、Pan、Swipe、Pinch、Rotation recognizer 的多输入源识别和统一 GestureEvent 构造 |
| arkui_ace_engine / frameworks/core/components_ng/event（Feat-02） | ClickEventActuator、GestureEventHub、FocusEventHandler 和程序化/无障碍点击入口 |
| arkui_ace_engine / interfaces/native（Feat-02~04） | NativeNode 点击事件、Native Gesture recognizer 与手势结果 getter |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| SDK 契约层 | interface_sdk-js/api/@ohos.multimodalInput.intentionCode.d.ts、common.d.ts、common.static.d.ets | 定义 ArkTS 14 值 IntentionCode、KeyEvent.intentionCode 与动态/静态事件入口 | 存量补录，无代码修改 |
| 输入源层 | MMI::KeyEvent | 生成物理按键对应的 GetKeyIntention() 结果 | 外部上游，不修改 |
| 平台适配层 | adapter/ohos/entrance/mmi_event_convertor.cpp | 将 MMI 意图码直接写入 ACE KeyEvent.keyIntention | 存量补录，无代码修改 |
| 预览适配层 | adapter/preview/entrance/event_dispatcher.cpp | 转换 Preview 按键字段；当前未写入 keyIntention | 存量差异记录，无代码修改 |
| 事件模型层 | frameworks/core/event/key_event.h、event_constants.h | 定义 KeyIntention、默认 UNKNOWN、KeyEventInfo 复制语义 | 存量补录，无代码修改 |
| 分发层 | frameworks/core/common/event_manager.cpp | 将 KEY 类型 NonPointerEvent 交给按键事件处理链 | 存量补录，无代码修改 |
| 框架消费层 | components_ng/event/focus_event_handler.cpp、base/view_abstract_model_ng.cpp | 解析焦点意图和上下文菜单触发条件 | 存量补录，无代码修改 |
| ArkTS 桥接层 | arkts_native_frame_node_bridge.cpp、node_common_modifier.cpp | 将 GetKeyIntention() 写入 ArkTS/节点事件对象的 intentionCode | 存量补录，无代码修改 |
| NDK 层 | interfaces/native/native_key_event.h、event/key_event_impl.cpp | 声明 ArkUI_KeyIntension，校验并返回 NDK 事件意图码 | 存量补录，无代码修改 |
| 点击 SDK 层 | interface_sdk-js/api/@internal/component/ets/common.d.ts、arkui/component/common.static.d.ets | 定义 ClickEvent、onClick 和来源字段 | （Feat-02）存量补录，无代码修改 |
| 指针适配层 | adapter/ohos/entrance/ace_view_ohos.cpp、mmi_event_convertor.cpp | Mouse→Touch、Mouse Wheel 补包和 Axis 字段转换 | （Feat-02~04）存量补录，无代码修改 |
| 点击汇聚层 | components_ng/event/click_event.cpp、gesture_event_hub.cpp、focus_event_handler.cpp | 汇聚指针、键盘、程序化和无障碍点击入口 | （Feat-02）存量补录，无代码修改 |
| 手势生命周期层 | components_ng/gestures/recognizers/gesture_recognizer.cpp | 将 Axis BEGIN/UPDATE/END/CANCEL 映射为 recognizer 生命周期 | （Feat-03~04）存量补录，无代码修改 |
| 位移识别层 | pan_recognizer.cpp、swipe_recognizer.cpp | 将 Touch/Axis 位移归一化为 Pan/Swipe GestureEvent | （Feat-03）存量补录，无代码修改 |
| 变换识别层 | pinch_recognizer.cpp、rotation_recognizer.cpp | 将多指触控、pinch/Ctrl+wheel/rotate Axis 归一化为 scale/angle | （Feat-04）存量补录，无代码修改 |
| 手势 Native 层 | interfaces/native/native_gesture.h、node/gesture_impl.cpp | 创建 Native recognizer 并读取 Pan/Swipe/Pinch/Rotation 结果 | （Feat-03~04）存量补录，无代码修改 |

调用链证据：OHOS 适配写入见 adapter/ohos/entrance/mmi_event_convertor.cpp:867-875；事件默认值与复制见 frameworks/core/event/key_event.h:153-162,190-204；非指针事件分发见 frameworks/core/common/event_manager.cpp:3111-3123；ArkTS 输出见 frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_frame_node_bridge.cpp:1465-1483；NDK 输出见 interfaces/native/event/key_event_impl.cpp:145-167。

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 涉及输入适配、事件模型、分发、消费和 API 暴露 | 保持 MMI→Adapter→KeyEvent→EventManager/FocusHub→Bridge/NDK 的单向数据流 | 架构评审/依赖检查 |
| OH-ARCH-SUBSYSTEM | ArkUI 依赖 MMI 产生意图码 | ACE 只消费 MMI 公开事件，不反向调用或维护生产映射 | 代码评审 |
| OH-ARCH-API-LEVEL | 动态、NDK、静态接口版本不同 | 以 canonical SDK 和 native_key_event.h 的 @since 为准 | API 评审/XTS |
| OH-ARCH-COMPONENT-BUILD | 本次不新增源码或目标 | BUILD.gn、bundle.json 均无变化 | 生成与构建检查 |
| OH-ARCH-ERROR-LOG | NDK getter 接收外部指针 | 空指针和错误 eventTypeId 返回 -1 并记录参数错误 | NDK 单测 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 新增功能实现 | 不涉及；当前实现即规格，不修改产品源码 |
| 安全与权限 | 不新增权限；NDK 仅读取事件内标量值，并执行空指针与类型校验 |
| IPC/跨进程 | ACE 内部路径不新增 IPC；MMI 事件到达后的处理为现有同步数据传递 |
| 数据持久化 | 不涉及；KeyIntention 仅存在于瞬态 KeyEvent/KeyEventInfo |
| 构建与部件 | 不涉及；不修改 BUILD.gn、bundle.json 或部件依赖 |
| UI 渲染与布局 | 不涉及；意图码影响事件消费，不改变布局、绘制和资源 |
| 物理键映射算法 | 不在 ACE 生产路径定义；由 MMI GetKeyIntention() 提供结果 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|-----------------|----------|------|
| ADR-1 | ACE 是否重新计算按键意图 | OHOS 路径直接透传 MMI GetKeyIntention() | 方案A：在 ACE 维护完整物理键映射；方案B：仅对部分按键覆盖 MMI 结果 | 当前实现仅做枚举转换，避免两套映射漂移；证据为 mmi_event_convertor.cpp:867-875 | AC-1.1；物理键映射问题需向上游 MMI 定界 |
| ADR-2 | 无意图时的统一表示 | 使用 INTENTION_UNKNOWN=-1 作为 KeyEvent 默认值和降级值 | 方案A：使用 0；方案B：字段可选；方案C：抛出事件错误 | 内部枚举与 ArkTS/NDK 均已有 -1 未知值，默认构造安全；证据为 key_event.h:153-162 | AC-1.2、AC-4.4 |
| ADR-3 | ArkTS 与 NDK 枚举范围如何处理 | 分通道记录真实公开集合，不强制做并集或交集 | 方案A：ArkTS 静默接受全部内部值；方案B：NDK 缩减到 ArkTS 14 值；方案C：文档只写公共交集 | SDK 是 ArkTS 契约权威，而 NDK 头文件已公开扩展值；静默统一会误导调用方 | AC-1.3、AC-2.3 |
| ADR-4 | 焦点解析中原始 KeyCode 与意图码的优先级 | 保持原始 KeyCode 优先，意图码仅回退 SELECT/ESCAPE/HOME | 方案A：意图码始终优先；方案B：只使用原始 KeyCode；方案C：合并后冲突时报错 | 当前行为兼容方向键、Tab、Enter、Space 等历史焦点规则；证据为 focus_event_handler.cpp:28-80 | AC-3.1~AC-3.3 |
| ADR-5 | 菜单按键兼容方式 | action=DOWN 且 KEY_MENU 或 INTENTION_MENU 任一命中即触发 | 方案A：仅 KEY_MENU；方案B：仅 INTENTION_MENU；方案C：所有 action 均触发 | 双入口兼容未归一化与已归一化设备，DOWN 门禁避免抬键重复触发；证据为 view_abstract_model_ng.cpp:1158-1181 | AC-3.4 |
| ADR-6 | Preview 缺失意图码的处理 | 记录为环境差异并沿用默认 UNKNOWN | 方案A：在 Preview 新增映射；方案B：从 KeyCode 推断部分值；方案C：隐藏 intentionCode 字段 | 当前任务是存量规格补录，不能提出行为修复；默认 UNKNOWN 可安全降级 | AC-4.4 |
| ADR-F2-1 | 多输入源是否各自维护点击回调 | 通过 GestureEventHub/FocusHub 复用同一 onClick 函数 | 为 Touch、Mouse、Keyboard、Accessibility 各建回调槽 | 当前实现把用户回调同时注册到指针 actuator 和 FocusHub，程序化入口也调用该链；避免业务重复 | Feat-02 AC-1.1~AC-3.4 |
| ADR-F2-2 | Mouse→Touch 后如何表达来源 | 保留当前转换后的 sourceType，并在内部 convertInfo 记录 MOUSE→TOUCH | 强制对外还原 MOUSE；丢弃转换信息 | 实现明确设置 sourceType=TOUCH，ArkTS 未公开 convertInfo；不能伪造不同于当前模型的来源 | Feat-02 AC-4.1~AC-4.2 |
| ADR-F2-3 | 键盘和程序化点击如何构造位置 | 键盘取节点中心并标记 KEYBOARD；程序化点击只填可确定的目标/几何，不伪造物理输入 | 沿用上一次指针位置；统一填零坐标和 TOUCH 来源 | 当前实现可观测且避免把非物理入口误报为真实设备 | Feat-02 AC-2.3、AC-3.4 |
| ADR-F3-1 | Axis 如何进入现有 recognizer | 在 NGGestureRecognizer 将四阶段 Axis action 映射到 Down/Move/Up/Cancel | 为 Axis 新建独立手势状态机 | 复用 Pan/Swipe 状态机和回调模型，同时保留 inputEventType=AXIS | Feat-03 AC-1.1~AC-1.3 |
| ADR-F3-2 | 鼠标滚轮缺少 UPDATE 如何兼容 | Adapter 发送零 BEGIN 后将真实首包改为 UPDATE | recognizer 接受无 UPDATE 序列；在结束时推导位移 | 当前补包保证连续手势至少观察一次更新且不污染 recognizer 通用逻辑 | Feat-03 AC-4.1 |
| ADR-F3-3 | Mouse 与 TouchPad 位移是否完全统一 | 只统一生命周期和 GestureEvent，保留 Mouse 单轴过滤与 TouchPad 坐标变换 | 强制使用相同 delta 算法 | 设备数据语义不同，当前实现已按 sourceTool 分支处理 | Feat-03 AC-2.4、AC-3.5 |
| ADR-F4-1 | Pinch 的 Axis 来源如何合流 | 显式 pinchAxisScale 直接使用；Ctrl+非 TouchPad 滚轮按轴符号步进 | 仅支持多指 Touch；把所有滚轮都视为缩放 | 当前实现同时支持设备原生比例和桌面 Ctrl+wheel 惯例 | Feat-04 AC-2.1~AC-2.4 |
| ADR-F4-2 | Pinch 与 Rotation Axis 如何避免交叉消费 | 以 isRotationEvent 分流，Rotation 只消费 rotate Axis，Pinch 忽略 rotation Axis | 让两个 recognizer 同时竞争同一 Axis | 当前字段和 early-return 规则可避免同一输入被双重解释 | Feat-04 AC-2.5、AC-3.1~AC-3.4 |
| ADR-F4-3 | SDK 声明与 Rotation Axis 源码不一致时如何定契约 | 对外以 SDK 限制为准，源码路径作为版本基线风险 | 直接按源码扩展公开支持；忽略源码路径 | canonical SDK 是外部契约，且当前 SDK 明示触控板双指旋转不能触发 | Feat-04 AC-3.5 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| SDK 契约 | 固化 ArkTS 14 值、字段形态和版本 | 修改 SDK 声明 | canonical SDK 审查 |
| 输入与事件模型 | 固化 MMI 透传和 UNKNOWN 默认值 | 在 ACE 新增映射算法 | 适配层/结构体单测 |
| 事件暴露 | 固化 ArkTS 与 NDK 输出行为 | 新增事件入口 | API/XTS、NDK 单测 |
| 框架消费 | 固化焦点与菜单优先级 | 扩展到所有组件私有按键逻辑 | Focus/Menu 单测 |
| 环境兼容 | 固化 OHOS 与 Preview 差异 | 修改 Preview 实现 | Preview 集成测试 |

### 骨架 Spec 拆分

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|------------|-----|
| TASK-SKELETON-1 | MMI 输入、KeyEvent 默认值与 ArkTS 暴露 | Feat-01-key-intention-normalization-spec.md | AC-1.1~AC-1.4 |
| TASK-SKELETON-2 | NDK getter 与枚举范围 | Feat-01-key-intention-normalization-spec.md | AC-2.1~AC-2.3 |
| TASK-SKELETON-3 | 焦点和上下文菜单消费规则 | Feat-01-key-intention-normalization-spec.md | AC-3.1~AC-3.4 |
| TASK-SKELETON-4 | 版本和 Preview 兼容性 | Feat-01-key-intention-normalization-spec.md | AC-4.1~AC-4.4 |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|------------|------|
| TASK-1 | Feat-01 按键意图归一化完整行为规格 | Feat-01-key-intention-normalization-spec.md | 本 Design |
| TASK-2 | Feat-02 多源点击交互归一化完整行为规格 | Feat-02-multi-source-click-interaction-normalization-spec.md | 本 Design |
| TASK-3 | Feat-03 多源滑动与平移归一化完整行为规格 | Feat-03-multi-source-slide-pan-normalization-spec.md | 本 Design |
| TASK-4 | Feat-04 多源缩放与旋转归一化完整行为规格 | Feat-04-multi-source-scale-rotation-normalization-spec.md | 本 Design |

## API 签名、Kit 与权限

### 新增 API

> 本次不新增代码；下表记录存量公开签名。

| API 签名 | 类型 | Kit | d.ts 位置 | 权限要求 | SysCap |
|----------|------|-----|------------|----------|--------|
| export enum IntentionCode | Public | InputKit | api/@ohos.multimodalInput.intentionCode.d.ts:21-171 | 无 | SystemCapability.MultimodalInput.Input.Core |
| KeyEvent.intentionCode: IntentionCode | Public | ArkUI | api/@internal/component/ets/common.d.ts:12794-12805；api/arkui/component/common.static.d.ets:6801-6810 | 无 | SystemCapability.ArkUI.ArkUI.Full |
| onKeyEvent(event: Callback<KeyEvent, boolean>): T | Public | ArkUI | api/@internal/component/ets/common.d.ts:21157-21181 | 无 | SystemCapability.ArkUI.ArkUI.Full |
| onKeyPreIme(event: Callback<KeyEvent, boolean>): T | Public | ArkUI | api/@internal/component/ets/common.d.ts:21199-21214 | 无 | SystemCapability.ArkUI.ArkUI.Full |
| onKeyEventDispatch(event: Callback<KeyEvent, boolean>): T | Public | ArkUI | api/@internal/component/ets/common.d.ts:21216-21232 | 无 | SystemCapability.ArkUI.ArkUI.Full |
| ArkUI_KeyIntension OH_ArkUI_KeyEvent_GetKeyIntensionCode(const ArkUI_UIInputEvent* event) | Public | ArkUI NDK | interfaces/native/native_key_event.h:530-537 | 无 | N/A |
| CommonMethod<T>.onClick(Callback<ClickEvent>[, distanceThreshold]) | Public | ArkUI | api/@internal/component/ets/common.d.ts:21020-21057；api/arkui/component/common.static.d.ets:12059-12093 | 无 | SystemCapability.ArkUI.ArkUI.Full |
| PanGesture / SwipeGesture | Public | ArkUI | api/@internal/component/ets/gesture.d.ts:1700-1868；api/arkui/component/gesture.static.d.ets:1271-1363 | 无 | SystemCapability.ArkUI.ArkUI.Full |
| PinchGesture / RotationGesture | Public | ArkUI | api/@internal/component/ets/gesture.d.ts:1871-2080；api/arkui/component/gesture.static.d.ets:1366-1488 | 无 | SystemCapability.ArkUI.ArkUI.Full |
| ArkUI_NativeGestureAPI_1::createPanGesture/createSwipeGesture/createPinchGesture/createRotationGesture | Public | ArkUI NDK | interfaces/native/native_gesture.h:1033-1098 | 无 | N/A |
| OH_ArkUI_PanGesture_Get* / OH_ArkUI_SwipeGesture_Get* / OH_ArkUI_PinchGesture_Get* / OH_ArkUI_RotationGesture_GetAngle | Public | ArkUI NDK | interfaces/native/native_gesture.h:463-565 | 无 | N/A |

### 变更/废弃 API

| 原有 API | 变更类型 | 新 API | 迁移说明 |
|----------|----------|--------|----------|
| 无 | 无 | 无 | 本次为存量能力补录 |

## 构建系统影响

### BUILD.gn 变更

无变更。本文档不修改产品源码，现有 adapter、ace_core、bridge 和 native interface 构建目标已覆盖相关实现。

### bundle.json 变更

无变更。不新增部件、不修改依赖关系。

## 可选设计扩展

### 架构图

```mermaid
graph TB
    MMI["MMI KeyEvent<br/>GetKeyIntention()"]
    OHOS["OHOS Adapter<br/>ConvertKeyEvent"]
    PREVIEW["Preview Adapter<br/>未写入 keyIntention"]
    MODEL["ACE KeyEvent / KeyEventInfo<br/>默认 UNKNOWN=-1"]
    DISPATCH["EventManager / FocusHub<br/>按键分发"]
    FOCUS["FocusEvent<br/>KeyCode 优先 + 意图回退"]
    MENU["Context Menu<br/>KEY_MENU 或 INTENTION_MENU"]
    ARKTS["ArkTS Bridge<br/>KeyEvent.intentionCode"]
    NDK["NDK<br/>GetKeyIntensionCode"]

    MMI --> OHOS --> MODEL
    PREVIEW --> MODEL
    MODEL --> DISPATCH
    DISPATCH --> FOCUS
    DISPATCH --> MENU
    MODEL --> ARKTS
    MODEL --> NDK
```

架构证据：adapter/ohos/entrance/mmi_event_convertor.cpp:867-875；adapter/preview/entrance/event_dispatcher.cpp:110-126；frameworks/core/event/key_event.h:153-162,190-204；frameworks/core/common/event_manager.cpp:3111-3123。

#### 多源点击归一化架构图（Feat-02）

```mermaid
graph TB
    TOUCH["Touch DOWN/UP"] --> CLICK["ClickRecognizer"]
    MOUSE["Mouse Left"] --> CONVERT["Mouse→Touch Adapter/Pipeline"] --> CLICK
    PAD["TouchPad Click"] --> CLICK
    KEY["SELECT / Enter / Space"] --> FOCUS["FocusEventHandler"]
    A11Y["Programmatic / Accessibility"] --> ACT["GestureEventHub::ActClick"]
    CLICK --> HUB["GestureEventHub common click"]
    FOCUS --> HUB
    ACT --> HUB
    HUB --> CALLBACK["onClick / Tap callback"]
```

#### 多源滑动与平移归一化架构图（Feat-03）

```mermaid
graph TB
    TOUCH["Touch Move"] --> LIFE["Recognizer lifecycle"]
    WHEEL["Mouse Wheel"] --> FIX["BEGIN/UPDATE 序列补齐"] --> AXIS["AxisEvent"]
    PAD["TouchPad Axis"] --> AXIS
    AXIS --> LIFE
    LIFE --> PAN["PanRecognizer"]
    LIFE --> SWIPE["SwipeRecognizer"]
    PAN --> EVENT["GestureEvent<br/>sourceTool + axis + AXIS"]
    SWIPE --> EVENT
```

#### 多源缩放与旋转归一化架构图（Feat-04）

```mermaid
graph TB
    MULTI["Multi-touch geometry"] --> PINCH["PinchRecognizer"]
    MULTI --> ROTATE["RotationRecognizer"]
    PADPINCH["TouchPad pinchAxisScale"] --> AXIS["AxisEvent"]
    CTRL["Ctrl + Mouse Wheel"] --> AXIS
    PADROTATE["Rotate Axis"] --> AXIS
    AXIS --> SPLIT{"isRotationEvent?"}
    SPLIT -->|否| PINCH
    SPLIT -->|是| ROTATE
    PINCH --> SCALE["GestureEvent scale / center"]
    ROTATE --> ANGLE["GestureEvent angle"]
```

### 数据流/控制流

| 步骤 | 调用方 | 被调用方 | 数据/接口 | 说明 |
|------|--------|----------|-----------|------|
| 1 | MMI | OHOS Adapter | MMI::KeyEvent::GetKeyIntention() | 上游生成归一化结果 |
| 2 | OHOS Adapter | ACE KeyEvent | KeyIntention | static_cast 后直接写入 |
| 3 | EventManager | 按键处理链 | NonPointerEvent / KeyEvent | KEY 事件进入 OnKeyEvent |
| 4 | KeyEvent | KeyEventInfo/NodeEvent | keyIntention/intentionCode | 复制为事件回调字段 |
| 5 | FocusEvent/Menu | 组件行为 | KeyCode + KeyIntention | 按优先级解析焦点或菜单 |
| 6 | NDK getter | Native 应用 | ArkUI_KeyIntension | 校验 event 后返回值 |

### 时序设计

```mermaid
sequenceDiagram
    participant MMI
    participant Adapter as OHOS Adapter
    participant Event as ACE KeyEvent
    participant Manager as EventManager
    participant Consumer as Focus/Menu
    participant API as ArkTS/NDK

    MMI->>Adapter: KeyEvent + GetKeyIntention()
    Adapter->>Event: 写入 keyIntention
    Event->>Manager: NonPointerEvent(KEY)
    Manager->>Consumer: 分发 KeyEvent
    Consumer->>Consumer: KeyCode 优先或意图回退
    Event->>API: 输出 intentionCode
```

### 数据模型设计

**ArkTS 契约**

interface_sdk-js/api/@ohos.multimodalInput.intentionCode.d.ts:21-171 定义 IntentionCode；api/@internal/component/ets/common.d.ts:12794-12805 定义 KeyEvent.intentionCode。

**框架模型**

frameworks/core/components_ng/event/event_constants.h:163-195 定义内部 KeyIntention；frameworks/core/event/key_event.h:153-162 定义 KeyEvent.keyIntention 默认值；同文件 190-204 将其复制到 KeyEventInfo。

| 数据 | 存储位置 | 生命周期 | 持久化 |
|------|----------|----------|--------|
| KeyIntention | KeyEvent.keyIntention | 单次事件分发 | 否 |
| KeyIntention | KeyEventInfo.keyIntention_ | 单次回调对象 | 否 |
| intentionCode | ArkUIKeyEvent/NodeEvent | 单次 Native 回调 | 否 |

#### 多源交互事件数据模型（Feat-02~04）

| 数据 | 关键字段 | 来源 | 生命周期 |
|------|----------|------|----------|
| TouchEvent | sourceType、sourceTool、deviceId、convertInfo、坐标 | 触控或 Mouse→Touch | 单次指针分发 |
| AxisEvent | horizontalAxis、verticalAxis、pinchAxisScale、rotateAxisAngle、isRotationEvent、pressedCodes | Mouse Wheel/TouchPad/MMI rotate | 单次 Axis 分发 |
| GestureEvent | inputEventType、sourceDevice、sourceTool、deviceId、axis、scale、angle、center | Click/Pan/Swipe/Pinch/Rotation recognizer | 单次手势回调 |
| Recognizer 状态 | READY/DETECTING/SUCCEED/FAIL、累计位移/比例/角度 | 手势识别器 | 单次手势序列 |

```cpp
// 语义摘要，字段以真实事件类型定义为准。
AxisEvent { horizontalAxis, verticalAxis, pinchAxisScale, rotateAxisAngle, isRotationEvent, sourceTool };
GestureEvent { inputEventType, sourceDevice, sourceTool, deviceId, scale, angle, axisHorizontal, axisVertical };
```

### 算法与状态机

本特性在 ACE 生产路径没有独立归一化状态机。核心决策流程如下：

```mermaid
graph TD
    START["收到 KeyEvent"] --> PRE{"isPreIme 或非 DOWN?"}
    PRE -->|是| NONE["FocusIntension::NONE"]
    PRE -->|否| RAW{"原始 KeyCode 命中?"}
    RAW -->|是| RAW_RESULT["返回原始按键焦点意图"]
    RAW -->|否| COUNT{"pressedCodes 满足单键/Shift+Tab?"}
    COUNT -->|否| NONE
    COUNT -->|是| INTENT{"意图为 SELECT / ESCAPE / HOME?"}
    INTENT -->|是| INTENT_RESULT["返回对应焦点意图"]
    INTENT -->|否| NONE
```

实现见 frameworks/core/components_ng/event/focus_event_handler.cpp:28-80。

### 测试性设计

| 测试层级 | 测试目标 | Mock 策略 | 验证方式 |
|----------|----------|-----------|----------|
| Adapter 单测 | MMI 意图值写入 KeyEvent | 构造 MMI::KeyEvent | 检查 keyIntention |
| Event model 单测 | 默认 UNKNOWN 与 KeyEventInfo 复制 | 构造 KeyEvent | 比较枚举值 |
| Focus 单测 | KeyCode 优先和 SELECT/ESCAPE/HOME 回退 | 构造 KeyEvent | FocusIntension 断言 |
| Menu 单测 | KEY_MENU/INTENTION_MENU + DOWN 门禁 | 构造 FocusHub 事件 | 菜单回调断言 |
| NDK Level0 | 有效值与非法输入 | 构造 ArkUI_UIInputEvent | 返回值和错误状态 |
| Preview 集成 | 未写入意图时的 UNKNOWN 降级 | Preview KeyEvent | ArkTS 回调字段断言 |
| 多源 Click（Feat-02） | Touch/Mouse/TouchPad/Keyboard/ActClick 调用同一业务回调 | 构造各类输入或直接调用 ActClick | 回调计数、inputEventType、来源和中心坐标 |
| Pan/Swipe Axis（Feat-03） | 四阶段映射、鼠标补包、方向过滤和 Axis 字段 | 构造 AxisEvent 与 sourceTool | Start/Update/End、delta、sourceTool、inputEventType |
| Pinch/Rotation Axis（Feat-04） | pinchScale、Ctrl+wheel、rotateAxis 和分流 | 构造 AxisEvent/pressedCodes | scale、angle、零截断、isRotationEvent 排除 |
| SDK 一致性（Feat-04） | 触控板旋转声明与源码路径差异 | 对比 canonical SDK 和 recognizer | 风险条目持续存在直至版本基线对齐 |

已有 NDK 证据：test/unittest/interfaces/ace_key_event/oh_arkui_keyevent_getkeyintensioncode_test.cpp:24-79；焦点证据：test/unittest/core/event/focus_event_handler_test_ng.cpp:180-194；菜单证据：test/unittest/core/base/view_abstract_model_test_ng.cpp:1023-1033。

### 异常传播时序图

```mermaid
sequenceDiagram
    participant App as Native App
    participant Getter as NDK Getter
    participant Status as ArkUI Error Status

    App->>Getter: event=null / inputEvent=null / wrong eventTypeId
    Getter->>Status: ARKUI_ERROR_CODE_PARAM_INVALID
    Getter-->>App: ArkUI_KeyIntension(-1)
```

| 异常场景 | 处理 | 恢复 |
|----------|------|------|
| event 为空 | 返回 -1 并记录参数错误 | 调用方停止读取该事件 |
| inputEvent 为空 | 返回 -1 并记录参数错误 | 调用方停止读取该事件 |
| eventTypeId 非按键事件 | 返回 -1 并记录参数错误 | 调用方改用匹配事件类型的 getter |
| Preview 无意图字段 | 保留 UNKNOWN | 应用按未知意图降级 |

实现见 interfaces/native/event/key_event_impl.cpp:145-167。

### 资源所有权矩阵

| 资源 | 创建方 | 持有方 | 销毁触发 | 实际释放 | 异常回收 |
|------|--------|--------|----------|----------|----------|
| MMI::KeyEvent shared_ptr | MMI/Adapter | KeyEvent.rawKeyEvent | 事件分发结束且引用归零 | shared_ptr | 自动引用计数 |
| KeyEvent | 输入分发路径 | 栈/事件队列 | 单次事件处理结束 | 自动对象 | 默认析构 |
| KeyEventInfo | 回调包装层 | 回调执行上下文 | 回调对象释放 | 框架事件对象 | 空指针检查 |

本特性不新增资源所有权关系。

### 接口参数规约

| 接口 | 参数 | 类型 | 合法范围 | 非法处理 | 边界说明 |
|------|------|------|----------|----------|----------|
| KeyEvent.intentionCode | 事件字段 | IntentionCode | ArkTS 14 个公开值 | 无值时 UNKNOWN=-1 | dynamic API 10+，static API 23+ |
| OH_ArkUI_KeyEvent_GetKeyIntensionCode | event | const ArkUI_UIInputEvent* | C_KEY_EVENT_ID 且 inputEvent 非空 | 返回 -1 + PARAM_INVALID | NDK API 14+ |

### 线程与并发模型

| 操作 | 发起线程 | 回调线程 | 跨进程边界 | 线程安全 | 重入约束 |
|------|----------|----------|------------|----------|----------|
| 平台 KeyEvent 转换 | 现有输入事件线程 | N/A | MMI 边界已在上游完成 | 事件对象单次写入 | 不新增重入 |
| EventManager 分发 | UI 事件处理线程 | UI 事件处理线程 | 无新增 | KeyEvent 按值/只读传递 | 回调消费规则沿用现状 |
| NDK getter | 调用线程 | 同步返回 | 无 | 只读 event 内容 | 调用期间 event 必须有效 |

本次不引入异步任务、锁、共享缓存或新的并发状态。

## 详细设计

### MMI 输入接入与默认值

OHOS ConvertKeyEvent 对非空 MMI::KeyEvent 调用 GetKeyIntention()，static_cast 为 KeyIntention 后直接写入 event.keyIntention，见 adapter/ohos/entrance/mmi_event_convertor.cpp:867-875。KeyEvent 构造时 keyIntention 默认初始化为 INTENTION_UNKNOWN，见 frameworks/core/event/key_event.h:153-162。因此生产路径以 MMI 为语义权威，缺失写入的路径安全降级为 -1。

### ArkTS 动态与静态契约

IntentionCode 模块声明其用途是把原始键盘事件映射为归一化交互意图，动态 API 10 起、静态 API 23 起，见 interface_sdk-js/api/@ohos.multimodalInput.intentionCode.d.ts:21-31。公开枚举包含 14 值，见同文件 31-171。动态 KeyEvent.intentionCode 是非可选字段且默认 UNKNOWN，见 api/@internal/component/ets/common.d.ts:12794-12805；静态字段见 api/arkui/component/common.static.d.ets:6801-6810。

动态 onKeyEvent、onKeyPreIme、onKeyEventDispatch 分别见 api/@internal/component/ets/common.d.ts:21157-21232；静态三个入口统一自 API 23 提供，见 api/arkui/component/common.static.d.ets:12166-12205。桥接层从 KeyEventInfo.GetKeyIntention() 构造 intentionCode 属性，见 frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_frame_node_bridge.cpp:1465-1483。

### NDK 意图码读取

ArkUI_KeyIntension 与 getter 自 API 14 公开，见 interfaces/native/native_key_event.h:425-537。实现先检查 event、eventTypeId 和 inputEvent；有效事件返回 intentionCode，非法事件返回 -1 并设置参数错误，见 interfaces/native/event/key_event_impl.cpp:145-167。NDK Level0 测试覆盖空 event、空 inputEvent、有效扩展值和错误事件类型，见 test/unittest/interfaces/ace_key_event/oh_arkui_keyevent_getkeyintensioncode_test.cpp:24-79。

### 焦点意图解析

FocusEvent::GetFocusIntension 首先拒绝 PreIME 和非 DOWN 事件；随后按原始方向键、Tab、Home、End、Enter、Space 等规则解析；只有原始规则未命中时才调用 GetFocusIntensionFromKey，且仅识别 SELECT、ESCAPE、HOME，见 frameworks/core/components_ng/event/focus_event_handler.cpp:28-80。该顺序保证存量焦点键行为不被归一化意图覆盖。

### 上下文菜单消费

RegisterContextMenuKeyEvent 仅处理 DOWN；原始 KEY_MENU 或 INTENTION_MENU 任一命中即打开已绑定菜单，见 frameworks/core/components_ng/base/view_abstract_model_ng.cpp:1158-1181。该设计同时兼容能产生物理 Menu KeyCode 的设备和只提供归一化 Menu 意图的设备。

### Preview 兼容路径

Preview ConvertKeyEvent 复制 code、key、action、pressedCodes、时间戳、metaKey、deviceId、sourceType 和锁键状态，但没有写入 keyIntention，见 adapter/preview/entrance/event_dispatcher.cpp:110-126。由于 KeyEvent 默认值为 UNKNOWN，Preview 当前对意图码统一表现为 -1。本设计仅记录这一存量差异，不改变实现。

### 多源点击交互归一化

ClickEventActuator 在存在用户或框架点击回调时创建统一 ClickRecognizer，并将 recognizer 同时加入触摸命中结果和响应链，见 frameworks/core/components_ng/event/click_event.cpp:35-60。GestureEventHub::SetUserOnClick 将同一点击函数写入 common click 和 FocusHub，见 frameworks/core/components_ng/event/gesture_event_hub.cpp:815-833；因此指针和键盘最终调用相同业务回调。

鼠标左键可在 AceView 输入兼容路径转换为 TouchEvent，转换后 sourceType 为 TOUCH，convertInfo 记录 MOUSE→TOUCH，见 adapter/ohos/entrance/mmi_event_convertor.cpp:1309-1336；Pipeline 也能将左键 PRESS/RELEASE/MOVE/CANCEL 转为触摸分发，见 frameworks/core/pipeline_ng/pipeline_context.cpp:5175-5186。ClickRecognizer 针对 TOUCH 与 MOUSE/TOUCH_PAD 使用不同多击超时，见 click_recognizer.cpp:140-150，并在成功回调中复制来源、工具、设备、输入类型和转换信息，见同文件 580-637。

焦点链把可处理的 SELECT 转为 SPACE 后调用 OnClick；合成 GestureEvent 使用节点中心、KEYBOARD 输入类型和 KeyEvent 的 source/deviceId，见 frameworks/core/components_ng/event/focus_event_handler.cpp:207-225,306-340。GestureEventHub::ActClick 则为程序化/无障碍入口构造目标区域，优先调用普通 actuator，缺失时回退到无障碍 ClickRecognizer 并上报 CLICK，见 gesture_event_hub.cpp:1115-1155。

### 多源滑动与平移归一化

NGGestureRecognizer 将 Axis BEGIN/UPDATE/END/CANCEL 分别映射到 Down/Move/Up/Cancel，并在 BEGIN 记录 source、tool、deviceId 与 inputEventType=AXIS，见 frameworks/core/components_ng/gestures/recognizers/gesture_recognizer.cpp:216-250。AceView 对鼠标滚轮首包先发送零增量 BEGIN，再把真实首包转换为 UPDATE，从而补齐连续手势生命周期，见 adapter/ohos/entrance/ace_view_ohos.cpp:498-513。

PanRecognizer 的 Axis BEGIN 校验 fingers 与 direction 后初始化伪触点和速度跟踪；UPDATE 将轴值转换为 delta 并触发 Start/Update。MOUSE 按方向清零禁用轴，TOUCHPAD 在节点变换空间计算 delta，见 pan_recognizer.cpp:331-377,548-609。生成 GestureEvent 时保留轴值、sourceTool、pressedCodes、pointerEventId、convertInfo 和 AXIS 类型，见同文件 906-929。

SwipeRecognizer 在 Axis UPDATE 中累计非零 offset 并校验方向角；Axis END 对零累计位移直接拒绝，MOUSE 路径将 resultSpeed 设为 0 后完成裁决，见 swipe_recognizer.cpp:221-250,317-353。本设计只定义输入到 Pan/Swipe/GestureEvent 的归一化，不定义 Scrollable 的摩擦、惯性、回弹和边缘效果。

### 多源缩放与旋转归一化

PinchRecognizer 同时支持多点 Touch 和 Axis。Axis BEGIN 在 pinchAxisScale 约等于 1，或 Ctrl 按下且来源工具不是 TOUCHPAD 时进入 DETECTING；UPDATE 优先直接采用非零 pinchAxisScale，否则按滚轮轴符号以固定步长更新，并把非正结果截断为 0，见 frameworks/core/components_ng/gestures/recognizers/pinch_recognizer.cpp:95-157,303-328。rotation Axis 和已结束 pinch 被提前排除，避免重复消费。

ConvertAxisEvent 从 MMI 复制 scroll、pinch、rotate 四类字段，并通过 rotate action 设置 isRotationEvent，见 adapter/ohos/entrance/mmi_event_convertor.cpp:718-741。RotationRecognizer 只处理 isRotationEvent=true 的 Axis BEGIN/UPDATE，记录 initialAngle，超过阈值后输出归一化角度，见 rotation_recognizer.cpp:120-137,270-297。

Dynamic SDK 的 RotationGesture 文案说明触控板双指旋转不能触发，见 interface/sdk-js/api/@internal/component/ets/gesture.d.ts:1987-1996；当前源码仍存在 rotation Axis 路径。由于 SDK 是外部契约，本设计不据此扩展公开支持范围，只记录目标 ace_engine 与 SDK 版本基线可能未完全对齐的风险。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| ArkTS 14 值与 NDK 扩展枚举范围不同 | API | 中 | 在 spec/API 表中分别列出真实公开范围，禁止静默合并 | ArkUI SIG |
| 内部 KeyIntention 比 ArkTS 和 NDK 均包含更多值 | API | 中 | 内部值仅作为实现模型记录，不推导为未声明的公开 API | ArkUI SIG |
| Preview 未写入 keyIntention | 测试 | 中 | 记录为环境兼容差异，Preview 用例断言 UNKNOWN | ArkUI SIG |
| 物理键到意图的映射由 MMI 提供 | 架构 | 中 | ACE 侧仅验证透传；映射正确性由 MMI 契约和测试负责 | MMI / ArkUI SIG |
| Public C API 保留 KeyIntension 的历史拼写 | API | 低 | 文档和代码严格使用既有符号，不做重命名 | ArkUI SIG |
| Mouse→Touch 后公开 source 可能表现为 TOUCH（Feat-02） | 兼容 | 中 | 规格明确转换后来源与内部 convertInfo 的信息边界，应用不得仅凭 source 反推物理设备 | ArkUI SIG |
| onClick 非正 distanceThreshold 的 SDK 文案与实现策略不同（Feat-02） | API | 中 | SDK 作为公开参数契约，源码无限阈值行为作为偏差记录并配置一致性测试 | ArkUI SIG |
| Mouse Wheel 与 TouchPad 的 delta/速度算法不同（Feat-03） | 兼容 | 中 | 只承诺统一生命周期和事件类型，不承诺数值完全等价 | ArkUI SIG |
| 鼠标滚轮依赖 Adapter 补齐 UPDATE（Feat-03） | 适配 | 中 | Adapter UT 固化 BEGIN→UPDATE→END，避免平台序列变化破坏 recognizer | ArkUI SIG / MMI |
| Dynamic SDK 限制触控板双指旋转，但源码存在 rotate Axis 路径（Feat-04） | API | 高 | 对外以 SDK 为准；在版本基线对齐前保留风险和交叉测试，不静默宣称支持 | ArkUI SIG / SDK SIG |
| Ctrl+滚轮 scale 为固定步长而原生 pinch 使用设备比例（Feat-04） | 兼容 | 中 | 规格只统一 PinchGesture 回调，不承诺两类来源的 scale 曲线一致 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0/P1 AC
- [x] 不涉及项已承接，N/A 和展开项都有结论
- [x] 涉及仓和模块职责清楚
- [x] 调用链层级分析完整，每层覆盖到位
- [x] 适用架构规则已识别并形成设计结论
- [x] 分层和子系统边界合规
- [x] API 变更有签名、权限、错误码和兼容性说明
- [x] BUILD.gn/bundle.json 影响明确
- [x] 设计输出和后续 Task 拆分明确
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner

**结论:** 通过（已有实现补录）。
