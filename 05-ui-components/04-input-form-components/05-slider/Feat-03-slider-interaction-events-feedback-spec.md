# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Slider 交互模式、事件与反馈 |
| 特性编号 | Func-05-04-05-Feat-03 |
| FuncID | 05-04-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+ / Static API 23+ / NDK API 18+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出与 Feat-03 相关的历史能力范围。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `onChange(callback)` | Dynamic API `@since 7`，拖动或点击触发，回调 value 与 `SliderChangeMode`。 |
| ADDED | `SliderInteraction`, `sliderInteractionMode(value)` | Dynamic API `@since 12`，控制点击、滑动、抬手点击更新模式。 |
| ADDED | `digitalCrownSensitivity(sensitivity)` | Dynamic API `@since 18`，仅在 `SUPPORT_DIGITAL_CROWN` 编译能力下生效，SDK 声明不能在 `attributeModifier` 内调用。 |
| ADDED | `enableHapticFeedback(enabled)` | Dynamic API `@since 18`，默认 true，SDK 声明需要 `ohos.permission.VIBRATE`。 |
| ADDED | Static `onChange`, `sliderInteractionMode`, `digitalCrownSensitivity`, `enableHapticFeedback` | Static API `@since 23`。 |
| ADDED | NDK `NODE_SLIDER_ENABLE_HAPTIC_FEEDBACK` 与 `NODE_SLIDER_EVENT_ON_CHANGE` | NDK 震感属性 `@since 18`，事件返回 value + mode。 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-input-form-components/05-slider/design.md`
- **KB 路由**: `python3 docs/kb_search.py Slider` 未命中现有 KB 条目
- **SDK 类型定义**:
  - Dynamic: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/@internal/component/ets/slider.d.ts:1042`
  - Static: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/arkui/component/slider.static.d.ets:695`
- **源码定位**:
  - `frameworks/core/components_ng/pattern/slider/slider_pattern.cpp:1346`
  - `frameworks/core/components_ng/pattern/slider/slider_event_hub.h:24`
  - `frameworks/core/components_ng/pattern/slider/slider_model_ng.cpp:651`
  - `frameworks/core/components_ng/pattern/slider/bridge/slider_dynamic_modifier.cpp:1050`
  - `frameworks/core/interfaces/native/node/node_slider_modifier.cpp:66`
  - `interfaces/native/native_node.h:11104`
  - `interfaces/native/node/style_modifier.cpp:18357`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 控制 Slider 的点击与拖动交互

**角色**: 应用开发者  
**期望**: 我想配置 Slider 对点击、拖动和抬手点击的响应方式。  
**价值**: 以便 Slider 能满足精细调节、防误触和只允许拖动等交互场景。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 未设置 `sliderInteractionMode` THEN 默认按 `SLIDE_AND_CLICK` 处理点击与滑动。 | 正常 |
| AC-1.2 | WHEN `sliderInteractionMode=SLIDE_AND_CLICK` 且触点不在滑块热区 THEN touch down 立即按触点位置更新 value。 | 正常 |
| AC-1.3 | WHEN `sliderInteractionMode=SLIDE_ONLY` 且触点不在滑块热区 THEN 不允许本次拖动更新 value。 | 正常 |
| AC-1.4 | WHEN `sliderInteractionMode=SLIDE_AND_CLICK_UP` THEN touch down 只记录位置，若 touch up 与 down 距离小于阈值才在抬手时按位置更新 value 并触发 Click。 | 正常 |
| AC-1.5 | WHEN ArkTS 设置的 interaction mode 非法 THEN Dynamic JSView 路径 reset 为默认值；Static undefined 也 reset。 | 异常 |

### US-2: 接收 Slider 值变化事件

**角色**: 应用开发者和 NDK 开发者  
**期望**: 我想在 Slider 开始、移动、结束和点击时接收变化事件。  
**价值**: 以便同步应用状态、执行业务逻辑和记录用户操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 用户 touch down 开始交互 THEN `onChange` 触发 mode=Begin。 | 正常 |
| AC-2.2 | WHEN 用户拖动或滚轮/轴事件改变 value THEN `onChange` 触发 mode=Moving。 | 正常 |
| AC-2.3 | WHEN 用户点击且最终 value 变化 THEN `onChange` 触发 mode=Click；WHEN Moving/Click 的 value 与上次事件 value 相等 THEN 不触发重复事件。 | 边界 |
| AC-2.4 | WHEN 用户交互结束 THEN `onChange` 触发 mode=End。 | 正常 |
| AC-2.5 | WHEN value 因异常恢复被 clamp THEN render 后补发 End 事件。 | 恢复 |
| AC-2.6 | WHEN NDK 注册 `NODE_SLIDER_EVENT_ON_CHANGE` THEN 事件数据 `data[0].f32` 为当前 value，`data[1].i32` 为 mode。 | 正常 |

### US-3: 使用震感与数字表冠反馈

**角色**: 应用开发者  
**期望**: 我想控制 Slider 的震感反馈，并在支持数字表冠的设备上设置表冠灵敏度。  
**价值**: 以便穿戴等输入设备具备可感知且可配置的交互反馈。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 未设置 `enableHapticFeedback` THEN 默认允许震感。 | 正常 |
| AC-3.2 | WHEN `enableHapticFeedback(false)` THEN Slider 值变化时不触发震感。 | 正常 |
| AC-3.3 | WHEN `enableHapticFeedback(true)`、`showSteps=true` 且 value 实际变化 THEN 调用震感反馈。 | 正常 |
| AC-3.4 | WHEN `showSteps=false` 或 value 未变化 THEN 即使 enableHapticFeedback 为 true 也不触发步点震感。 | 边界 |
| AC-3.5 | WHEN 设置 `digitalCrownSensitivity(LOW/MEDIUM/HIGH)` 且编译开启 `SUPPORT_DIGITAL_CROWN` THEN 按灵敏度换算表冠旋转像素并触发 Begin/Moving/End。 | 正常 |
| AC-3.6 | WHEN `digitalCrownSensitivity` 入参非法或在不支持 attributeModifier 的路径调用 THEN reset 或拒绝该调用；未开启 `SUPPORT_DIGITAL_CROWN` 时不产生表冠行为。 | 异常 |
| AC-3.7 | WHEN NDK 设置 `NODE_SLIDER_ENABLE_HAPTIC_FEEDBACK` 为非 bool THEN reset 震感属性并返回 `ERROR_CODE_PARAM_INVALID`。 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1 ~ R-5 | TASK-SLIDER-03 | Core UT + 手工交互 | `slider_pattern.cpp:1346`, `arkts_native_slider_bridge.cpp:1160` |
| AC-2.1 ~ AC-2.5 | R-6 ~ R-10 | TASK-SLIDER-03 | Core UT | `slider_pattern.cpp:1367`, `slider_pattern.cpp:2133` |
| AC-2.6 | R-11 | TASK-SLIDER-03 | C API UT | `native_node.h:11104`, `slider_dynamic_modifier.cpp:1050` |
| AC-3.1 ~ AC-3.4 | R-12 ~ R-14 | TASK-SLIDER-03 | Core UT + 权限场景验证 | `slider_model_ng.cpp:1091`, `slider_pattern.cpp:506`, `slider_pattern.cpp:1624` |
| AC-3.5, AC-3.6 | R-15, R-16 | TASK-SLIDER-03 | 穿戴设备/编译开关验证 | `slider_pattern.h:192`, `slider_pattern.cpp:2194` |
| AC-3.7 | R-17 | TASK-SLIDER-03 | C API UT | `style_modifier.cpp:18357` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 未设置 interaction mode | 使用 `SLIDE_AND_CLICK` | 默认值来自 PaintProperty/Pattern 默认 | AC-1.1 |
| R-2 | 行为 | `SLIDE_AND_CLICK` touch down 且不在滑块热区 | 立即按本地坐标更新 value | IMAGE 或 NONE 特定热区判断可能使点击转为不可拖动区域 | AC-1.2 |
| R-3 | 行为 | `SLIDE_ONLY` touch down | 只有命中滑块热区才允许拖动更新 | mouse/touch 分别使用不同热区计算 | AC-1.3 |
| R-4 | 行为 | `SLIDE_AND_CLICK_UP` touch down/up | down 记录位置，up 距离小于阈值时更新并发 Click | 阈值来自 `PAN_MOVE_DISTANCE` | AC-1.4 |
| R-5 | 恢复 | interaction mode 非 number、越界或 undefined | reset `SliderInteractionMode` | 合法范围为 `SLIDE_AND_CLICK` 到 `SLIDE_AND_CLICK_UP` | AC-1.5 |
| R-6 | 行为 | touch down 开始交互 | 触发 Begin | Begin 不执行 value 去重 | AC-2.1 |
| R-7 | 行为 | pan/axis/crown update | 更新 value 后触发 Moving | Moving 若 value 未变则不回调 | AC-2.2, AC-2.3 |
| R-8 | 边界 | Click 或 Moving 事件 value 等于 EventHub 记录值 | 不触发重复 `onChange` | Begin/End 不受该去重条件限制 | AC-2.3 |
| R-9 | 行为 | 交互结束 | 触发 End，清理 pressed/bubble/axis 状态 | axis 结束也发 End | AC-2.4 |
| R-10 | 恢复 | Pattern 发现 value 越界并 clamp | render 后通过 after-render task 补发 End | 用于异常值恢复通知 | AC-2.5 |
| R-11 | 行为 | NDK onChange 事件注册 | 发送 `ON_SLIDER_CHANGE`，数据为 value 与 mode | `event_converter.cpp` 映射 NODE 与 ON 枚举 | AC-2.6 |
| R-12 | 行为 | 未设置 haptic | `GetEnableHapticFeedback` 返回 true | SDK 默认值 true | AC-3.1 |
| R-13 | 行为 | `enableHapticFeedback(false)` | Pattern 标记不触发震感 | 同时写入 PaintProperty | AC-3.2 |
| R-14 | 边界 | value 变化时调用 `PlayHapticFeedback` | 仅当 `isEnableHaptic_` true 且 `showSteps` true 时启动震感 | `showSteps=false` 或 value 未变不震动 | AC-3.3, AC-3.4 |
| R-15 | 行为 | 表冠 UPDATE/END 事件 | UPDATE 首次发 Begin，后续发 Moving；END 发 End | 仅 `SUPPORT_DIGITAL_CROWN` 编译开启 | AC-3.5 |
| R-16 | 异常 | 表冠灵敏度非法或 attributeModifier 路径调用 | Dynamic bridge reset 或抛拒绝调用；无编译开关时无行为 | SDK 声明不能在 `attributeModifier` 内调用 | AC-3.6 |
| R-17 | 异常 | NDK haptic 属性 size=0 或非 bool | reset enableHapticFeedback 并返回 `ERROR_CODE_PARAM_INVALID` | bool 仅允许 0/1 | AC-3.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | Core UT + 手工交互 | 三种 interaction mode 的 down/move/up 差异。 |
| VM-2 | AC-2.1 ~ AC-2.5 | Core UT | Begin/Moving/Click/End 时序、value 去重和恢复事件。 |
| VM-3 | AC-2.6 | C API UT | `NODE_SLIDER_EVENT_ON_CHANGE` 的 value/mode 数据格式。 |
| VM-4 | AC-3.1 ~ AC-3.4 | Core UT + 设备验证 | haptic 默认值、关闭、showSteps 门槛和 value 变化门槛。 |
| VM-5 | AC-3.5, AC-3.6 | 穿戴设备/编译开关验证 | 数字表冠灵敏度、事件时序和 unsupported path。 |
| VM-6 | AC-3.7 | C API UT | NDK haptic 非法 bool 错误码和 reset。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `SliderAttribute.sliderInteractionMode(value)` | Public | `SliderInteraction` | `SliderAttribute/this` | N/A | 设置点击/滑动交互模式。 | AC-1.1 ~ AC-1.5 |
| `SliderAttribute.onChange(callback)` | Public | `(value, mode) => void` | `SliderAttribute/this` | N/A | 监听 Slider 值变化事件。 | AC-2.1 ~ AC-2.5 |
| `SliderAttribute.digitalCrownSensitivity(sensitivity)` | Public | `CrownSensitivity` | `SliderAttribute/this` | N/A | 设置数字表冠灵敏度。 | AC-3.5, AC-3.6 |
| `SliderAttribute.enableHapticFeedback(enabled)` | Public | boolean | `SliderAttribute/this` | N/A | 设置是否启用震感反馈。 | AC-3.1 ~ AC-3.4 |
| `NODE_SLIDER_ENABLE_HAPTIC_FEEDBACK` | NDK/Public | `.value[0].i32` bool | `int32_t` for set, `ArkUI_AttributeItem*` for get | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID`, `ERROR_CODE_INTERNAL_ERROR` | Native 震感属性设置、获取和重置。 | AC-3.7 |
| `NODE_SLIDER_EVENT_ON_CHANGE` | NDK/Public | 注册节点事件 | `ArkUI_NodeEvent` | N/A | Native Slider 变化事件，返回 value 与 mode。 | AC-2.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录，不改变 API | N/A | N/A |

## 接口规格

### 接口定义

**sliderInteractionMode(value: SliderInteraction)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SliderAttribute.sliderInteractionMode(value: SliderInteraction): SliderAttribute` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | SliderInteraction | 是 | `SLIDE_AND_CLICK` | 合法值为 `SLIDE_AND_CLICK`、`SLIDE_ONLY`、`SLIDE_AND_CLICK_UP`。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SLIDE_AND_CLICK | 点击轨道可立即更新，拖动滑块可移动 | AC-1.2 |
| 2 | SLIDE_ONLY | 非滑块热区 touch down 不更新 | AC-1.3 |
| 3 | SLIDE_AND_CLICK_UP | 抬手点击才更新 | AC-1.4 |
| 4 | 非法值 | reset 默认交互模式 | AC-1.5 |

**onChange(callback) / NODE_SLIDER_EVENT_ON_CHANGE**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SliderAttribute.onChange(callback: (value: number, mode: SliderChangeMode) => void): SliderAttribute`; `NODE_SLIDER_EVENT_ON_CHANGE` |
| 返回值 | ArkTS 返回 `SliderAttribute/this`；NDK 回调返回 `ArkUI_NodeEvent` |
| 开放范围 | Public / NDK Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 ~ AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| callback | function | ArkTS 是；Static 可 undefined | N/A | 回调参数为当前 value 和 mode。 |
| mode | SliderChangeMode/i32 | 系统生成 | N/A | Begin=0、Moving=1、End=2、Click=3。 |
| NDK data[0] | f32 | 系统生成 | N/A | 当前 Slider value。 |
| NDK data[1] | i32 | 系统生成 | N/A | 事件模式。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | touch down | 发 Begin | AC-2.1 |
| 2 | value 变化中 | 发 Moving | AC-2.2 |
| 3 | 点击导致 value 变化 | 发 Click | AC-2.3 |
| 4 | 交互结束 | 发 End | AC-2.4 |
| 5 | NDK 事件注册 | `ArkUI_NodeComponentEvent.data[0/1]` 返回 value/mode | AC-2.6 |

**enableHapticFeedback / digitalCrownSensitivity**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableHapticFeedback(enabled: boolean): SliderAttribute`; `digitalCrownSensitivity(sensitivity: Optional<CrownSensitivity>): SliderAttribute` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public |
| 错误码 | NDK haptic set 可返回 `ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-3.1 ~ AC-3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| enabled | boolean | 是 | true | 开启震感需按 SDK 声明配置 `ohos.permission.VIBRATE`。 |
| sensitivity | CrownSensitivity | 否 | MEDIUM | 仅支持 LOW/MEDIUM/HIGH；不能在 `attributeModifier` 内调用。 |
| NDK haptic | i32 bool | 是 | true | 非 0/1 返回 `ERROR_CODE_PARAM_INVALID` 并 reset。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enabled=false | 不触发震感 | AC-3.2 |
| 2 | enabled=true、showSteps=true、value 改变 | 触发 Slider 步点震感 | AC-3.3 |
| 3 | 表冠 UPDATE/END | 触发 Begin/Moving/End | AC-3.5 |
| 4 | NDK haptic 非 bool | reset 并返回参数错误 | AC-3.7 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次为已有实现规格补录。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** `onChange` Dynamic API 7；`sliderInteractionMode` Dynamic API 12；`digitalCrownSensitivity` 和 `enableHapticFeedback` Dynamic API 18；Static API 23；NDK haptic API 18。
- **API 版本号策略:** 以 SDK `@since` 和 NDK `native_node.h` 为准；数字表冠行为受 `SUPPORT_DIGITAL_CROWN` 编译开关约束。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 事件统一进入 EventHub | ArkTS、Static、NDK 事件最终写入 `SliderEventHub::SetOnChange`。 | AC-2.1 ~ AC-2.6 |
| Pattern 决定交互时序 | touch/pan/axis/crown 时序由 `SliderPattern` 统一控制。 | AC-1.1 ~ AC-2.5 |
| Haptic 受权限和状态双重约束 | SDK 要求 VIBRATE 权限，实现还要求 enable=true、showSteps=true、value 变化。 | AC-3.1 ~ AC-3.4 |
| Crown 编译开关 | 数字表冠代码在 `SUPPORT_DIGITAL_CROWN` 宏下编译。 | AC-3.5, AC-3.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Moving 事件对相同 value 去重，避免重复回调。 | Core UT | `slider_pattern.cpp:2133` |
| 功耗 | 震感只在 showSteps 且 value 改变时触发。 | Core UT + 设备验证 | `slider_pattern.cpp:1624` |
| 内存 | 事件回调存储在 EventHub，属性 reset 不新增持久资源。 | 代码评审 | `slider_event_hub.h:32` |
| 安全 | 震感权限由应用配置承担，规格明确 SDK 权限要求。 | 权限场景验证 | `slider.d.ts:1268` |
| 可靠性 | 异常 value 恢复后补发 End，避免状态不同步。 | Core UT | `slider_pattern.cpp:1038` |
| 可测试性 | 交互模式、事件 mode、NDK data 均可观测。 | UT + C API UT | `native_node.h:11104` |
| 自动化维测 | 不新增日志、埋点或 DFX 事件。 | 代码评审 | N/A |
| 定界定位 | Bridge、Pattern、EventHub、NDK 事件链路均有明确证据。 | 文档自审 | 本规格验收追溯表 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 支持 touch/mouse/axis 通用交互；无数字表冠。 | 验证点击、拖动、滚轮事件。 | 组件测试 | `slider_pattern.cpp:1467` |
| 平板 | 与手机一致，布局尺寸变化不改变事件语义。 | 验证多窗口下事件时序。 | 组件测试 | `slider_pattern.cpp:1193` |
| 折叠屏 | 与手机一致，旋转场景会跳过部分旧手势事件。 | API 12+ 旋转后验证跳过状态恢复。 | 手工/组件测试 | `slider_pattern.cpp:1193` |
| 穿戴 | 支持数字表冠时按 crownSensitivity 处理。 | 仅 `SUPPORT_DIGITAL_CROWN` 开启时验证。 | 设备验证 | `slider_pattern.h:192` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 值变化会发送无障碍 value 事件；步点虚拟节点归 Feat-04。 | AC-2.1 ~ AC-2.5 |
| 大字体 | 否 | 本 Feat 不涉及文本布局。 | N/A |
| 深色模式 | 否 | 交互时序不依赖颜色模式。 | N/A |
| 多窗口/分屏 | 是 | 窗口尺寸变化可能影响手势跳过状态，但不改变 mode 枚举。 | AC-1.1 ~ AC-2.5 |
| 多用户 | 否 | 不涉及用户态存储。 | N/A |
| 版本升级 | 是 | 需要保留 Dynamic 7/12/18、Static 23、NDK 18 的版本边界。 | API 变更分析 |
| 生态兼容 | 是 | NDK 事件数据格式需保持 value/mode 顺序。 | AC-2.6 |

## 行为场景（可选，Gherkin）

Feature: Slider 交互模式、事件与反馈
  作为 ArkUI 开发者
  我想配置 Slider 的交互和反馈
  以便得到可预测的事件和触感行为

  Scenario: SLIDE_ONLY 不响应轨道点击
    Given Slider 设置 sliderInteractionMode 为 SLIDE_ONLY
    When 用户在滑块热区外 touch down
    Then 本次交互不更新 value

  Scenario: Moving 事件去重
    Given Slider 已注册 onChange
    When 连续 Moving 计算出的 value 与上次事件 value 相同
    Then 不触发重复 onChange

  Scenario: 步点震感触发
    Given enableHapticFeedback 为 true
    And showSteps 为 true
    When 用户拖动导致 value 变化
    Then Slider 触发震感反馈

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/foundation/arkui/ace_engine"
    query: "Slider sliderInteractionMode onChange haptic digital crown implementation"
  - repo: "OpenHarmony/interface/sdk-js"
    query: "Slider onChange sliderInteractionMode enableHapticFeedback digitalCrownSensitivity since"
```

**关键文档：** `slider.d.ts`, `slider.static.d.ets`, `native_node.h`, `slider_pattern.cpp`, `slider_event_hub.h`, `node_slider_modifier.cpp`
