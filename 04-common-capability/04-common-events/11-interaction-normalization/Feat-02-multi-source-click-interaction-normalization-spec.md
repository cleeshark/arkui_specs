# 特性规格

> Func-04-04-11-Feat-02 多源点击交互归一化：固化触控、鼠标、触控板、键盘和程序化/无障碍入口汇聚到统一点击回调的存量行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 多源点击交互归一化 |
| 特性编号 | Func-04-04-11-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic onClick API 7 起、距离阈值重载 API 12 起；Static API 23 起；NativeNode API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 多输入源点击归一化规格 | 补录触控、鼠标、触控板、键盘 SELECT/Enter/Space 和程序化/无障碍点击入口 |
| ADDED | 来源与兼容转换差异 | 补录 Mouse→Touch 兼容转换、键盘合成坐标和程序化事件默认来源行为 |
| ADDED | 多范式接口契约 | 补录 ArkTS Dynamic/Static、TapGesture 和 NativeNode 点击事件的既有接口 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/11-interaction-normalization/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:9835,21020-21057` | 已核验 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:4772-4781,12059-12093` | 已核验 |
| Gesture SDK | `interface/sdk-js/api/@internal/component/ets/gesture.d.ts:1091,1380-1488` | 已核验 |
| Native SDK | `interfaces/native/native_node.h:10321,10525` | 已核验 |
| Source locator | `frameworks/core/components_ng/event/gesture_event_hub.cpp:775-830` | 已核验 |

> 需求基线、不涉及项、受影响子系统与仓库详见 design.md，本文档不重复摘录。design.md 与本文档并行维护，互不依赖。

## 用户故事

### US-1: 通过指针输入触发统一点击

**作为** ArkUI 应用开发者，
**我想要** 触控、鼠标左键和触控板点击使用同一 onClick/TapGesture 语义，
**以便** 组件不需要为每种底层输入源编写独立点击逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 触控输入在组件响应区完成满足次数、手指数和移动阈值的 DOWN/UP 序列 THEN ClickRecognizer 接受手势并调用当前点击回调 | 正常 |
| AC-1.2 | WHEN 鼠标左键 PRESS/MOVE/RELEASE/CANCEL 进入兼容转换路径 THEN 事件被转换为 TouchEvent 并进入同一触摸命中与 ClickRecognizer 链 | 正常 |
| AC-1.3 | WHEN 鼠标事件经 Pipeline 的 Mouse→Touch 路径且动作是左键 PRESS/RELEASE/MOVE 或 CANCEL THEN 由 OnTouchEvent 进入同一点击识别链 | 正常 |
| AC-1.4 | WHEN ClickRecognizer 接收 SourceType::MOUSE 或 SourceType::TOUCH_PAD THEN 使用鼠标类多击超时参数；WHEN 来源为 TOUCH THEN 使用触控超时参数 | 边界 |
| AC-1.5 | WHEN 点击移动距离超过配置阈值、手指数不满足或抬起点不在有效区域 THEN 点击识别被拒绝且不调用 onClick | 异常 |

### US-2: 通过键盘触发组件点击

**作为** 键盘或遥控设备用户，
**我想要** SELECT、Enter 或 Space 触发与指针点击相同的组件回调，
**以便** 焦点导航场景保持统一交互结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 焦点按键解析得到 SELECT 且节点不是 TabStop THEN 意图被转换为 SPACE 并进入 FocusEventHandler::OnClick | 正常 |
| AC-2.2 | WHEN 焦点按键解析得到 SPACE 且焦点激活/版本门禁允许处理 THEN 调用 FocusHub 中与指针点击相同的 onClick 回调 | 正常 |
| AC-2.3 | WHEN 键盘触发点击 THEN GestureEvent 的输入类型为 KEYBOARD、来源设备和 deviceId 继承 KeyEvent，坐标取目标节点中心 | 正常 |
| AC-2.4 | WHEN 焦点未激活且目标 API >= 18，或主题不要求处理非激活焦点点击 THEN 不把该按键转换为点击 | 边界 |

### US-3: 通过程序化和无障碍入口触发点击

**作为** 自动化、无障碍或框架调用方，
**我想要** 在没有物理指针序列时执行组件的点击语义，
**以便** 辅助功能和程序化操作复用业务回调。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN GestureEventHub::ActClick 找到普通 ClickEventActuator THEN 构造目标区域和位置后同步调用其点击回调并返回 true | 正常 |
| AC-3.2 | WHEN 没有普通 ClickEventActuator 但存在无障碍 ClickRecognizer THEN 调用 TapAction、上报 Accessibility CLICK 并返回 true | 正常 |
| AC-3.3 | WHEN ActClick 找不到节点、几何信息或任何点击回调 THEN 返回 false 且不产生点击事件 | 异常 |
| AC-3.4 | WHEN 程序化点击构造 GestureEvent THEN 事件没有伪造物理 sourceTool、deviceId 或原始 PointerEvent；调用方不得将其等同于真实指针来源 | 边界 |

### US-4: 获取一致而可区分的点击事件数据

**作为** 需要分析输入来源的应用开发者，
**我想要** 所有来源调用相同回调，同时保留实现可提供的来源字段，
**以便** 通用逻辑与来源特化逻辑可以共存。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 指针点击被识别 THEN ClickEvent/GestureEvent 携带时间、屏幕/窗口/本地位置、source、sourceTool、deviceId 和目标信息 | 正常 |
| AC-4.2 | WHEN AceView 的 LEFT_PRESS 兼容转换开启 THEN TouchEvent.sourceType 被设置为 TOUCH，同时 convertInfo 记录 MOUSE→TOUCH；公开 source 可能体现转换后的触控来源 | 边界 |
| AC-4.3 | WHEN onClick 使用 distanceThreshold 且输入值 <= 0 THEN ClickRecognizer 将有效阈值退化为无限距离；SDK Static 文案将该值描述为转为默认值，二者差异作为风险记录 | 边界 |
| AC-4.4 | WHEN Dynamic/Static 或 NativeNode 注册点击回调 THEN 注册最终汇聚到 ViewAbstract/GestureEventHub 的统一点击执行链，不改变各通道公开签名 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现补录 | ClickRecognizer/Adapter Host UT | `click_recognizer.cpp:125-150,396-451`；`mmi_event_convertor.cpp:1309-1336` |
| AC-2.1~AC-2.4 | R-6~R-8 | 已有实现补录 | FocusEventHandler Host UT | `focus_event_handler.cpp:207-225,306-340` |
| AC-3.1~AC-3.4 | R-9~R-11 | 已有实现补录 | GestureEventHub Host UT/无障碍集成测试 | `gesture_event_hub.cpp:1115-1155` |
| AC-4.1~AC-4.4 | R-12~R-15 | 已有实现补录 | SDK 审查/NativeNode UT/源码审查 | `click_recognizer.cpp:580-637`；`node_common_modifier.cpp:12661-12739` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ClickEventActuator 收集有效点击目标 | 创建或复用 ClickRecognizer，设置统一回调并加入命中结果和响应链 | 没有任何点击回调时不创建目标 | AC-1.1 |
| R-2 | 行为 | LEFT_PRESS 兼容转换开启且鼠标左键 action 可转换 | MouseEvent 转为 TouchEvent 并结束当前 MouseEvent 通道处理 | 仅左键；不可转换 action 继续原通道 | AC-1.2 |
| R-3 | 行为 | Pipeline 收到左键 PRESS/RELEASE/MOVE 或 CANCEL | CreateTouchPoint 后调用 OnTouchEvent | 右键等不进入该触摸点击路径 | AC-1.3 |
| R-4 | 边界 | ClickRecognizer 初始化不同 SourceType | TOUCH 使用触控多击超时；MOUSE/TOUCH_PAD 使用鼠标多击超时 | 其他来源不改当前参数 | AC-1.4 |
| R-5 | 异常 | 移动阈值、手指数、点击次数或响应区条件不满足 | 拒绝识别，不调用点击回调 | distanceThreshold <= 0 的实现行为见 R-14 | AC-1.5 |
| R-6 | 行为 | 焦点意图为 SELECT 且节点非 TabStop | 将意图转为 SPACE 后尝试点击 | 保持 TabStop 的 SELECT 语义 | AC-2.1 |
| R-7 | 行为 | 焦点意图为 SPACE 且门禁允许 | 通过 FocusHub 保存的同一点击函数调用 onClick | 指针与键盘共享回调槽 | AC-2.2 |
| R-8 | 边界 | 键盘合成 GestureEvent | 输入类型固定 KEYBOARD，位置为节点中心，sourceTool 为 UNKNOWN | 不生成原始 PointerEvent | AC-2.3, AC-2.4 |
| R-9 | 行为 | ActClick 存在普通 ClickEventActuator | 构造目标区域并同步调用点击回调，返回 true | 几何节点必须存在 | AC-3.1 |
| R-10 | 行为 | ActClick 仅找到无障碍 ClickRecognizer | 调用 TapAction 并上报 Accessibility CLICK | 不重复调用普通 actuator | AC-3.2 |
| R-11 | 异常 | ActClick 缺少宿主、几何或回调 | 返回 false | 不创建虚假物理输入信息 | AC-3.3, AC-3.4 |
| R-12 | 行为 | 指针点击成功 | GestureEvent 复制来源设备、工具、deviceId、坐标、按键码和转换信息 | 可用字段取决于原始输入 | AC-4.1 |
| R-13 | 边界 | Mouse→Touch 兼容转换 | sourceType 变为 TOUCH，convertInfo 保存 MOUSE→TOUCH | ArkTS BaseEvent 未公开 convertInfo | AC-4.2 |
| R-14 | 边界 | ClickRecognizer 构造时 distanceThreshold 转换值 <= 0 | 内部阈值设为正无穷 | 与 Static SDK“转为默认值”文案存在偏差风险 | AC-4.3 |
| R-15 | 行为 | ArkTS/Static/NativeNode 设置点击回调 | 最终注册到 ViewAbstract/GestureEventHub 点击执行链 | 本特性不新增或修改 API | AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, R-1 | ClickEventActuator Host UT | 同一 ClickRecognizer 被加入触摸命中和响应链 |
| VM-2 | AC-1.2~AC-1.3, R-2~R-3 | Adapter/Pipeline UT | 左键转换后进入 TouchEvent 且不重复走 MouseEvent |
| VM-3 | AC-1.4~AC-1.5, R-4~R-5 | ClickRecognizer 参数化 UT | 来源超时、移动阈值、手指数和响应区拒绝 |
| VM-4 | AC-2.1~AC-2.4, R-6~R-8 | FocusEventHandler UT | SELECT/SPACE、焦点门禁、中心坐标和 KEYBOARD 类型 |
| VM-5 | AC-3.1~AC-3.4, R-9~R-11 | GestureEventHub/Accessibility UT | 普通 actuator 优先、无障碍回退和 false 返回 |
| VM-6 | AC-4.1~AC-4.2, R-12~R-13 | ArkTS 集成测试 | source/sourceTool/deviceId 与转换后来源 |
| VM-7 | AC-4.3, R-14 | SDK-源码一致性检查 | 非正阈值的声明与实现差异保持显式 |
| VM-8 | AC-4.4, R-15 | Dynamic/Static/NativeNode API 测试 | 多通道注册执行同一业务点击语义 |

## API 变更分析

> 本次仅补录存量行为，不产生产品 API 变更。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `CommonMethod<T>.onClick` | Public | `Callback<ClickEvent>`；可选 distanceThreshold | 当前组件 | N/A | 注册组件点击回调 | AC-1.1~AC-4.4 |
| `TapGesture` | Public | count、fingers、distanceThreshold | 手势对象 | N/A | 显式声明点击手势 | AC-1.1, AC-1.4, AC-1.5 |
| `NODE_ON_CLICK` / `NODE_ON_CLICK_EVENT` | Public/NDK | node、事件类型、userData | 注册结果/异步事件 | 参数错误/不支持 | NativeNode 点击注册与事件上报 | AC-4.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录 | 无需迁移 | AC-1.1~AC-4.4 |

## 接口规格

### 接口定义

**CommonMethod<T>.onClick**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onClick(event: (event: ClickEvent) => void): T`、`onClick(event: Callback<ClickEvent>, distanceThreshold: number): T`；Static: `onClick(event: Callback<ClickEvent> | undefined, distanceThreshold?: double): this` |
| 返回值 | `T/this` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `Callback<ClickEvent>` | 注册时是 | 无 | Static 允许 undefined 清除；回调由所有归一化入口复用 |
| distanceThreshold | number/double | 否 | SDK Static 声明 `(2^31-1)vp` | 实现转换值 <= 0 时使用无限距离，差异见风险 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 触控/鼠标/触控板满足点击条件 | 调用同一回调并附带可用来源字段 | AC-1.1~AC-1.4, AC-4.1 |
| 2 | 焦点键映射为 SPACE | 合成 KEYBOARD GestureEvent 后调用同一回调 | AC-2.1~AC-2.3 |
| 3 | ActClick 被程序化或无障碍调用 | 调用普通或无障碍点击链 | AC-3.1~AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文档补录多源点击既有行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；点击事件为瞬态对象。
- **最低支持版本:** Dynamic onClick API 7；distanceThreshold 重载 API 12；Static API 23；NativeNode API 12。
- **API 版本号策略:** 以 canonical SDK 的 dynamic/static `@since` 和 native_node.h 的公开枚举为准。
- **跨输入差异:** 键盘点击使用节点中心和 KEYBOARD 类型；程序化点击没有物理来源；兼容转换可能将公开 source 表现为 TOUCH。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 单一业务回调 | 指针和键盘入口通过 GestureEventHub/FocusHub 共享 onClick 函数 | AC-1.1~AC-2.3 |
| 输入适配前置 | Mouse→Touch 发生在 Adapter/Pipeline，ClickRecognizer 不负责平台鼠标动作转换 | AC-1.2, AC-1.3 |
| 来源如实呈现 | 仅输出当前事件模型实际持有的 source/sourceTool/deviceId，不反推物理来源 | AC-3.4, AC-4.1, AC-4.2 |
| SDK 契约优先 | 公开签名和版本以 SDK 为准，源码偏差进入风险表 | AC-4.3, AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次归一化不新增跨线程等待或 IPC | 调用链审查 | `click_event.cpp:35-60` |
| 功耗 | 不新增轮询或后台任务 | 源码审查 | 同上 |
| 内存 | 复用 ClickRecognizer 和现有 GestureEvent；不新增持久缓存 | Host UT/源码审查 | `gesture_event_hub.cpp:799-833` |
| 安全 | 程序化点击不伪造物理输入凭据 | 安全审查 | `gesture_event_hub.cpp:1115-1155` |
| 可靠性 | 无回调或无几何时返回 false，不崩溃 | Host UT | 同上 |
| 可测试性 | 各来源可通过独立事件构造验证同一回调计数 | Host UT/集成测试 | `focus_event_handler.cpp:306-340` |
| 自动化维测 | 保留事件类型、来源和转换信息用于定界 | 事件字段断言 | `click_recognizer.cpp:580-637` |
| 定界定位 | Adapter、Recognizer、FocusHub、Accessibility 分层证据可独立定位 | 源码追溯 | 本文 context-references |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 主要由触控触发 | 满足点击识别条件后调用统一回调 | 触控集成测试 | `click_recognizer.cpp:396-451` |
| 平板 | 可同时存在触控、鼠标、触控板和键盘 | 不同来源汇聚到同一回调并保留可用来源字段 | 多输入集成测试 | `ace_view_ohos.cpp:449-467` |
| 折叠屏 | 展开/折叠不改变点击归一化规则 | 坐标使用事件与节点几何的当前值 | 多窗口/折叠测试 | `click_recognizer.cpp:157-203` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | ActClick 可回退到无障碍 ClickRecognizer 并上报 CLICK | AC-3.2 |
| 大字体 | 否 | 不改变点击语义；尺寸变化由命中区域机制处理 | AC-1.1 |
| 深色模式 | 否 | 不涉及视觉资源 | 全部 |
| 多窗口/分屏 | 是 | 点击坐标按当前窗口和节点几何构造 | AC-2.3, AC-4.1 |
| 多用户 | 否 | 无持久化用户数据 | 全部 |
| 版本升级 | 是 | API 7/12/18/23 门禁和行为差异需回归 | AC-2.4, AC-4.3, AC-4.4 |
| 生态兼容 | 是 | Mouse→Touch 后公开来源可能为 TOUCH，应用不应仅凭 source 推断物理设备 | AC-4.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 多源点击交互归一化
  作为 ArkUI 应用开发者
  我想要不同底层输入触发同一点击语义
  以便复用组件业务逻辑

  Scenario: 鼠标左键兼容转换触发点击
    Given LEFT_PRESS 兼容转换已开启且组件注册 onClick
    When 鼠标左键在响应区完成 PRESS 和 RELEASE
    Then MouseEvent 被转换为 TouchEvent 并进入 ClickRecognizer
    And onClick 只被调用一次

  Scenario: 键盘 Space 触发点击
    Given 组件获得焦点且注册 onClick
    When FocusEventHandler 接收可处理的 Space/Select 按键
    Then 回调收到 inputEventType 为 KEYBOARD 的 GestureEvent
    And 事件位置为目标节点中心

  Scenario: 无障碍点击回退
    Given 组件没有普通 ClickEventActuator 但存在无障碍 ClickRecognizer
    When 框架调用 ActClick
    Then TapAction 被调用并上报 Accessibility CLICK

  Scenario: 程序化点击没有物理来源
    Given 组件存在普通点击回调
    When 框架直接调用 ActClick
    Then 点击业务回调被调用
    And 事件不伪造原始 PointerEvent 或物理 sourceTool
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：不扩展长按、悬停、滚动容器物理效果或组件私有点击语义
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ClickEventActuator ClickRecognizer GestureEventHub FocusEventHandler 多源点击归一化调用链"
  - repo: "openharmony/interface_sdk-js"
    query: "Dynamic Static onClick ClickEvent TapGesture source sourceTool deviceId 契约与版本"
```

**关键文档：** `frameworks/core/components_ng/event/click_event.cpp:35-60`；`frameworks/core/components_ng/event/gesture_event_hub.cpp:775-830,1115-1155`；`frameworks/core/components_ng/event/focus_event_handler.cpp:207-225,306-340`；`adapter/ohos/entrance/mmi_event_convertor.cpp:1309-1336`。
