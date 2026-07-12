# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Slider 创建、数值范围与布局样式 |
| 特性编号 | Func-05-04-05-Feat-01 |
| FuncID | 05-04-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+ / Static API 23+ / NDK API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出与 Feat-01 相关的历史能力范围。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `Slider(options?: SliderOptions)` | Dynamic API `@since 7`，value/min/max/step/style 基础参数。 |
| ADDED | `direction/reverse` | Dynamic API `@since 8`，横纵向与反向滑动。 |
| ADDED | `SliderStyle.NONE`, `SlideRange`, `SliderInteraction`, `minResponsiveDistance` | Dynamic API `@since 12`，本 Feat 覆盖 `SlideRange` 与 `minResponsiveDistance`。 |
| ADDED | Static `Slider` 与 `SliderOptions` | Static API `@since 23`。 |
| ADDED | `setSliderOptions(options?: SliderOptions)` | Static only `@since 26.0.0`。 |
| ADDED | NDK `NODE_SLIDER_VALUE/MIN_VALUE/MAX_VALUE/STEP/DIRECTION/REVERSE/STYLE/TRACK_THICKNESS` | `interfaces/native/native_node.h` 公开节点属性。 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-input-form-components/05-slider/design.md`
- **KB 路由**: `python3 docs/kb_search.py Slider` 未命中现有 KB 条目
- **SDK 类型定义**:
  - Dynamic: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/@internal/component/ets/slider.d.ts`
  - Static: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/arkui/component/slider.static.d.ets`
  - Modifier: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/arkui/SliderModifier.d.ts`
- **源码定位**:
  - `frameworks/core/components_ng/pattern/slider/bridge/arkts_native_slider_bridge.cpp`
  - `frameworks/core/components_ng/pattern/slider/slider_model_ng.cpp`
  - `frameworks/core/components_ng/pattern/slider/slider_pattern.cpp`
  - `interfaces/native/native_node.h`
  - `interfaces/native/node/style_modifier.cpp`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 创建 Slider 并获得确定的数值范围行为

**角色**: 应用开发者  
**期望**: 我想通过 `Slider(options)` 或 static `setSliderOptions(options)` 设置当前值、最小值、最大值、步长和有效滑动范围。  
**价值**: 以便音量、亮度、进度等连续值控制在非法输入下仍保持可预测。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Slider({ value: 20, min: 0, max: 100, step: 5 })` THEN Slider 保存 value=20、min=0、max=100、step=5，并按 value 计算当前进度。 | 正常 |
| AC-1.2 | WHEN 调用 `Slider({ min: 100, max: 0 })` THEN min/max 恢复为 0/100。 | 异常 |
| AC-1.3 | WHEN value 小于 min 或大于 max THEN value 被 clamp 到 min 或 max。 | 边界 |
| AC-1.4 | WHEN step <= 0 或 step > max-min THEN ArkTS 构造/Pattern 恢复 step=1。 | 异常 |
| AC-1.5 | WHEN static API 调用 `setSliderOptions(options)` THEN 依次写入 step/min/max/value/style/direction/reverse。 | 正常 |
| AC-1.6 | WHEN 设置 `slideRange({ from, to })` 且 `min <= from <= to <= max` THEN from/to 按 step 修正，value clamp 到修正后的 `[from,to]`。 | 边界 |
| AC-1.7 | WHEN `slideRange` 入参不是对象、from/to 均缺失、from/to 为 NaN 或不满足范围约束 THEN 有效滑动范围 reset。 | 异常 |
| AC-1.8 | WHEN 设置 `minResponsiveDistance(value)` 且 `0 <= value <= max-min` THEN 保存该响应距离；否则恢复为 0 或 reset。 | 边界 |

### US-2: 配置 Slider 布局方向与样式

**角色**: 应用开发者  
**期望**: 我想配置 Slider 的横纵方向、反向滑动、滑块/轨道样式、轨道厚度和滑块尺寸。  
**价值**: 以便 Slider 能适配水平、垂直和不同视觉密度布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 未设置 style/direction/reverse THEN 默认 style=OutSet、direction=Horizontal、reverse=false。 | 正常 |
| AC-2.2 | WHEN 设置 style/direction/reverse THEN LayoutProperty 与 PaintProperty 均更新对应值。 | 正常 |
| AC-2.3 | WHEN 设置 `trackThickness(value > 0)` THEN LayoutProperty 保存 thickness；WHEN value <= 0 THEN ArkTS 路径使用当前 style 的 theme 默认厚度。 | 边界 |
| AC-2.4 | WHEN 设置 `blockSize({ width, height })` 且宽高均 > 0 THEN LayoutProperty 保存 blockSize；WHEN 任一宽高 <= 0 THEN reset 到 theme 默认 blockSize。 | 边界 |
| AC-2.5 | WHEN style/direction/reverse 变化 THEN 触发 measure 与 render 相关更新；WHEN value/min/max/step/slideRange 变化 THEN 主要触发 render 更新。 | 正常 |

### US-3: 通过 NDK 公开属性设置 Slider 核心参数

**角色**: NDK 开发者  
**期望**: 我想通过 `ArkUI_AttributeItem` 设置 Slider 的核心数值和布局属性。  
**价值**: 以便 Native 场景能与 ArkTS 场景复用同一 Slider 组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 通过 `NODE_SLIDER_VALUE/MIN_VALUE/MAX_VALUE` 设置 `.value[0].f32` THEN 对应值委托到 Slider modifier 并可 get/reset。 | 正常 |
| AC-3.2 | WHEN 通过 `NODE_SLIDER_STEP` 设置 `.value[0].f32 < 0.01` THEN 返回 `ERROR_CODE_PARAM_INVALID`，不写入 step。 | 异常 |
| AC-3.3 | WHEN 通过 `NODE_SLIDER_DIRECTION` 设置非 `ArkUI_SliderDirection` 范围值 THEN 返回 `ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-3.4 | WHEN 通过 `NODE_SLIDER_REVERSE` 设置非 bool 值或通过 `NODE_SLIDER_STYLE` 设置非 `ArkUI_SliderStyle` 范围值 THEN 返回 `ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-3.5 | WHEN 通过 `NODE_SLIDER_TRACK_THICKNESS` 设置 `.value[0].f32 <= 0` THEN 返回 `ERROR_CODE_PARAM_INVALID`；设置正数时按 VP 单位写入 thickness。 | 边界 |
| AC-3.6 | WHEN 需要设置 blockSize/slideRange/minResponsiveDistance THEN `native_node.h` 无公开 NODE_SLIDER_* 属性枚举，只能作为内部/生成式 modifier 通道说明。 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-SLIDER-01 | UT | `test/unittest/core/pattern/slider/` |
| AC-1.2 | R-2 | TASK-SLIDER-01 | UT | `slider_pattern.cpp:1015` |
| AC-1.3 | R-3 | TASK-SLIDER-01 | UT | `slider_pattern.cpp:1029` |
| AC-1.4 | R-4, R-14 | TASK-SLIDER-01 | UT + C API UT | `arkts_native_slider_bridge.cpp:61`, `style_modifier.cpp:18233` |
| AC-1.5 | R-5 | TASK-SLIDER-01 | Static API UT | `arkts_native_slider_bridge.cpp:1325` |
| AC-1.6, AC-1.7 | R-6, R-7 | TASK-SLIDER-01 | UT | `slider_model_ng.cpp:696` |
| AC-1.8 | R-8 | TASK-SLIDER-01 | UT | `slider_model_ng.cpp:128` |
| AC-2.1 ~ AC-2.5 | R-9, R-10, R-11, R-12 | TASK-SLIDER-01 | UT + Inspector | `slider_layout_property.h:102`, `slider_paint_property.h:256` |
| AC-3.1 ~ AC-3.6 | R-13, R-14, R-15, R-16 | TASK-SLIDER-01 | C API UT | `interfaces/native/node/style_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `Slider(options)` 中 value/min/max/step 均为合法数值 | value/min/max/step 写入 SliderPaintProperty，并按 value 计算进度 | value 在 `[min,max]` 内；step 在 `(0,max-min]` 内 | AC-1.1 |
| R-2 | 恢复 | `min >= max` | min/max 恢复为 0/100 | 边界为 `min == max` | AC-1.2 |
| R-3 | 边界 | value < min 或 value > max | value clamp 到 min 或 max | 低于 min 取 min，高于 max 取 max | AC-1.3 |
| R-4 | 恢复 | ArkTS 构造或 Pattern 计算遇到 step <= 0 或 step > max-min | step 恢复为 1 | SDK 声明取值范围 `[0.01,max-min]`，实现对 `<=0` 和超范围恢复 | AC-1.4 |
| R-5 | 行为 | Static API 调用 `setSliderOptions(options)` | 按 step、min、max、value、style、direction、reverse 顺序写入 native modifier | 参数个数必须为 8 个 bridge 参数 | AC-1.5 |
| R-6 | 边界 | `slideRange({from,to})` 合法 | from 向下修正到 step 倍数或 min，to 向上修正到 step 倍数或 max，value clamp 到 `[from,to]` | `min <= from <= to <= max` 且 step > 0 | AC-1.6 |
| R-7 | 异常 | `slideRange` 入参非对象、from/to 均缺失、NaN 或范围不合法 | reset ValidSlideRange | from/to 无穷值分别按 min/max 处理，NaN 直接 reset | AC-1.7 |
| R-8 | 边界 | `minResponsiveDistance(value)` | `0 <= value <= max-min` 时保存；否则保存 0 或 reset | 单位与 min/max 一致 | AC-1.8 |
| R-9 | 行为 | style/direction/reverse 设置 | 同时更新 LayoutProperty 与 PaintProperty | style 默认 OutSet，direction 默认 Horizontal，reverse 默认 false | AC-2.1, AC-2.2 |
| R-10 | 行为 | `trackThickness(value > 0)` | 更新 LayoutProperty::Thickness | value 为 Length，dirty flag 为 measure | AC-2.3 |
| R-11 | 恢复 | `trackThickness(value <= 0)` | ArkTS 路径恢复当前 style 对应 theme 默认厚度 | OutSet/InSet/NONE 取不同 theme 默认值 | AC-2.3 |
| R-12 | 恢复 | `blockSize` width 或 height <= 0 | reset BlockSize，Inspector/布局使用 theme 默认 blockSize | OutSet/InSet 取不同 theme 默认值；NONE 下 blockSize 不生效 | AC-2.4 |
| R-13 | 行为 | NDK 公开 Slider 属性 set/get/reset | value/min/max/step 使用 f32；direction/style 使用 enum；reverse 使用 i32 bool；trackThickness 使用 f32 vp | 公开枚举见 `native_node.h` | AC-3.1 |
| R-14 | 异常 | NDK `NODE_SLIDER_STEP` value < 0.01 | 返回 `ERROR_CODE_PARAM_INVALID` | 与 ArkTS 恢复默认 1 的行为不同 | AC-3.2 |
| R-15 | 异常 | NDK direction/style/reverse 非法值 | 返回 `ERROR_CODE_PARAM_INVALID` | direction/style 必须在 NDK enum 范围；reverse 必须为 0/1 | AC-3.3, AC-3.4 |
| R-16 | 异常 | NDK `NODE_SLIDER_TRACK_THICKNESS` value <= 0 | 返回 `ERROR_CODE_PARAM_INVALID`；正数按 VP 写入 | get 时若 thickness <= 0 返回 nullptr | AC-3.5 |
| R-17 | 行为 | 查找 NDK 公开属性 | `native_node.h` 未暴露 blockSize/slideRange/minResponsiveDistance 的 NODE_SLIDER_* 枚举 | 内部 `ArkUISliderModifier` 函数不等同公开 C API | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | Core UT | 构造参数默认值、越界恢复、static `setSliderOptions` 写入顺序。 |
| VM-2 | AC-1.6, AC-1.7 | Core UT | `slideRange` from/to step 修正、NaN/无效范围 reset。 |
| VM-3 | AC-1.8 | Core UT | `minResponsiveDistance` 合法范围与 reset。 |
| VM-4 | AC-2.1 ~ AC-2.5 | Core UT + Inspector | Paint/LayoutProperty 分层与 dirty flag。 |
| VM-5 | AC-3.1 ~ AC-3.6 | C API UT | NDK 属性入参、错误码、get/reset 行为和公开属性边界。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Slider(options?: SliderOptions)` | Public | value/min/max/step/style/direction/reverse | `SliderAttribute` | N/A | 创建 Slider 并设置基础数值与布局样式。 | AC-1.1 ~ AC-2.2 |
| `SliderAttribute.setSliderOptions(options?: SliderOptions)` | Public/staticonly | Static SliderOptions | `this` | N/A | Static API 下更新 Slider 创建参数。 | AC-1.5 |
| `SliderAttribute.trackThickness(value: Length)` | Public | Length | `SliderAttribute/this` | N/A | 设置轨道厚度。 | AC-2.3 |
| `SliderAttribute.blockSize(value: SizeOptions)` | Public | width/height | `SliderAttribute/this` | N/A | 设置滑块尺寸。 | AC-2.4 |
| `SliderAttribute.slideRange(value: SlideRange)` | Public | from/to | `SliderAttribute/this` | N/A | 设置有效滑动范围。 | AC-1.6, AC-1.7 |
| `SliderAttribute.minResponsiveDistance(value: number)` | Public | number/double | `SliderAttribute/this` | N/A | 设置最小响应距离。 | AC-1.8 |
| `NODE_SLIDER_VALUE/MIN_VALUE/MAX_VALUE/STEP/DIRECTION/REVERSE/STYLE/TRACK_THICKNESS` | NDK/Public | `ArkUI_AttributeItem` | `int32_t` for set, `ArkUI_AttributeItem*` for get | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID` | Native 节点属性设置、获取和重置。 | AC-3.1 ~ AC-3.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录，不改变 API | N/A | N/A |

## 接口规格

### 接口定义

**Slider(options?: SliderOptions) / setSliderOptions(options?: SliderOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Slider(options?: SliderOptions): SliderAttribute`; `SliderAttribute.setSliderOptions(options?: SliderOptions): this` |
| 返回值 | `SliderAttribute/this` — 当前 Slider 属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number/double/Bindable | 否 | min | 小于 min 取 min，大于 max 取 max。 |
| min | number/double | 否 | 0 | 必须小于 max，否则 min/max 恢复为 0/100。 |
| max | number/double | 否 | 100 | 必须大于 min，否则 min/max 恢复为 0/100。 |
| step | number/double | 否 | 1 | ArkTS 路径非法时恢复为 1；SDK 声明范围 `[0.01,max-min]`。 |
| style | SliderStyle | 否 | OutSet | Dynamic OutSet/InSet @since 7，NONE @since 12；Static @since 23。 |
| direction | Axis | 否 | Horizontal | Dynamic @since 8；Static @since 23。 |
| reverse | boolean | 否 | false | Dynamic @since 8；Static @since 23。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | options 合法 | 写入属性并显示对应进度 | AC-1.1 |
| 2 | min >= max | min/max 恢复为 0/100 | AC-1.2 |
| 3 | value 超出范围 | clamp 到最近边界 | AC-1.3 |
| 4 | step 非法 | ArkTS 路径恢复为 1 | AC-1.4 |
| 5 | Static API 调用 `setSliderOptions` | 按 bridge 写入顺序更新所有选项 | AC-1.5 |

**slideRange(value: SlideRange)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SliderAttribute.slideRange(value: SlideRange): SliderAttribute` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.6, AC-1.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| from | number/double | 否 | min | 有效时需满足 `min <= from <= to`；按 step 向下修正。 |
| to | number/double | 否 | max | 有效时需满足 `from <= to <= max`；按 step 向上修正。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | from/to 合法 | 保存修正后的 ValidSlideRange 并 clamp value | AC-1.6 |
| 2 | 非对象、NaN、无 from/to 或范围非法 | reset ValidSlideRange | AC-1.7 |

**trackThickness / blockSize / minResponsiveDistance**

| 属性 | 值 |
|------|-----|
| 函数签名 | `trackThickness(value: Length)`, `blockSize(value: SizeOptions)`, `minResponsiveDistance(value: number)` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.8, AC-2.3, AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| trackThickness | Length | 是 | theme 默认值 | 正数有效；非正数恢复 theme 默认值。 |
| blockSize.width/height | Length | 是 | theme 默认值 | 宽高均正数有效；任一非正数 reset。 |
| minResponsiveDistance | number/double | 是 | 0 | `0 <= value <= max-min` 有效，否则恢复为 0/reset。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | trackThickness 为正数 | 更新 LayoutProperty::Thickness | AC-2.3 |
| 2 | blockSize 宽高为正数 | 更新 LayoutProperty::BlockSize | AC-2.4 |
| 3 | minResponsiveDistance 合法 | 更新 PaintProperty::MinResponsiveDistance | AC-1.8 |

**NDK NODE_SLIDER_* 属性**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SetSlider*(ArkUI_NodeHandle node, const ArkUI_AttributeItem* item)` |
| 返回值 | `int32_t` — `ERROR_CODE_NO_ERROR` 或 `ERROR_CODE_PARAM_INVALID` |
| 开放范围 | NDK/Public |
| 错误码 | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-3.1 ~ AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `.value[0].f32` | float | 是 | 属性默认值 | value/min/max/step/trackThickness 使用；step 必须 >= 0.01，trackThickness 必须 > 0。 |
| `.value[0].i32` | int32 | 是 | 属性默认值 | direction/style 枚举值必须合法，reverse 必须为 0/1。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 NDK 属性输入 | 委托 Slider modifier 并返回 `ERROR_CODE_NO_ERROR` | AC-3.1 |
| 2 | step < 0.01 | 返回 `ERROR_CODE_PARAM_INVALID` | AC-3.2 |
| 3 | direction/style/reverse 非法 | 返回 `ERROR_CODE_PARAM_INVALID` | AC-3.3, AC-3.4 |
| 4 | trackThickness <= 0 | 返回 `ERROR_CODE_PARAM_INVALID` | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次为存量能力补录，不修改实现。需记录既有差异：ArkTS 非法 step 恢复为 1，NDK `NODE_SLIDER_STEP` 对 `<0.01` 返回 `ERROR_CODE_PARAM_INVALID`。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic Slider `@since 7`；direction/reverse `@since 8`；SlideRange/SliderInteraction/minResponsiveDistance `@since 12`；Static Slider `@since 23`；static-only `setSliderOptions` `@since 26.0.0`；NDK Slider enum `@since 12`。
- **API 版本号策略:** 规格以 `interface/sdk-js` 的 `.d.ts/.d.ets` 和 `interfaces/native/native_node.h` 为 API 契约；源码差异进入风险/兼容性说明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | 外部 API 以 `interface/sdk-js` 声明为准，源码差异显式记录。 | AC-1.1 ~ AC-2.5 |
| 属性分层验证 | LayoutProperty 与 PaintProperty 的 dirty flag 不同，测试不能只看单一 property。 | AC-2.2 ~ AC-2.5 |
| NDK 公开边界 | 仅 `native_node.h` 的 NODE_SLIDER_* 视为公开 NDK 属性。 | AC-3.1 ~ AC-3.6 |
| 当前实现即规格 | 不修复 ArkTS/NDK 非法 step 差异，仅记录行为。 | AC-1.4, AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 属性设置不引入新增布局层级；layout 类属性触发 measure，paint 类属性触发 render。 | UT/Inspector | `slider_layout_property.h:102`, `slider_paint_property.h:256` |
| 功耗 | 无新增循环、定时器或后台任务。 | 代码审查 | 本次文档补录 |
| 内存 | `SliderValidRange` 使用 RefPtr 挂在 PaintProperty，无持久化存储。 | 代码审查 | `slider_model_ng.cpp:723` |
| 安全 | NDK 入参非法时返回参数错误，不越界访问枚举。 | C API UT | `style_modifier.cpp:689`, `style_modifier.cpp:18233` |
| 可靠性 | 非法 min/max/step/value/slideRange 均有恢复或 reset 路径。 | UT | `slider_pattern.cpp:1015`, `slider_model_ng.cpp:696` |
| 可测试性 | 已有 Slider core UT 与 C API modifier UT 可覆盖。 | UT/C API UT | `test/unittest/core/pattern/slider/`, `test/unittest/capi/modifiers/slider_modifier_test.cpp` |
| 自动化维测 | 可通过 Inspector JSON 验证 style、trackThickness、blockSize。 | Inspector 测试 | `slider_layout_property.h:47` |
| 定界定位 | Bridge/Model/Pattern/NDK 各层证据可定位到行号。 | 文档审查 | 本规格 context-references |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无 Feat-01 特有差异 | 按 theme 默认尺寸和 SDK 行为执行。 | UT/手工 | Slider UT |
| 平板 | 无 Feat-01 特有差异 | 同手机。 | UT/手工 | Slider UT |
| 折叠屏 | 无 Feat-01 特有差异 | 尺寸由父布局和 Slider direction/style 决定。 | 手工 | component_test Slider sample |
| 穿戴 | Feat-01 不覆盖数字表冠交互 | `digitalCrownSensitivity` 归 Feat-03。 | N/A | SDK `@since 12/23` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Feat-01 只覆盖数值范围基础；step 可访问文本、自定义内容归 Feat-04。 | AC-1.1 ~ AC-1.8 |
| 大字体 | 否 | Feat-01 不涉及文本布局；tip/custom content 归 Feat-04。 | N/A |
| 深色模式 | 是 | 默认 thickness/blockSize 依赖 SliderTheme，颜色主题归 Feat-02。 | AC-2.3, AC-2.4 |
| 多窗口/分屏 | 是 | Slider 尺寸由父布局约束和 direction/style 共同决定，无独立窗口状态。 | AC-2.1 ~ AC-2.5 |
| 多用户 | 否 | 无用户态存储。 | N/A |
| 版本升级 | 是 | 需记录 Dynamic/Static/NDK since 差异与 static-only API。 | 兼容性声明 |
| 生态兼容 | 是 | ArkTS 与 NDK 非法 step 行为不同，需显式说明。 | AC-1.4, AC-3.2 |

## 行为场景（可选，Gherkin）

Feature: Slider 创建、数值范围与布局样式
  作为 ArkUI 开发者
  我想要 Slider 对非法数值和布局参数给出确定行为
  以便在 ArkTS、Static ArkTS 和 NDK 场景中稳定使用 Slider

  Scenario Outline: 构造参数恢复
    Given Slider 使用 min <min> max <max> step <step> value <value>
    When 创建 Slider
    Then 生效 min 为 <effective_min>
    And 生效 max 为 <effective_max>
    And 生效 step 为 <effective_step>
    And 生效 value 为 <effective_value>

    Examples:
      | min | max | step | value | effective_min | effective_max | effective_step | effective_value |
      | 0 | 100 | 5 | 20 | 0 | 100 | 5 | 20 |
      | 100 | 0 | 5 | 20 | 0 | 100 | 5 | 20 |
      | 0 | 100 | -1 | 20 | 0 | 100 | 1 | 20 |
      | 0 | 100 | 5 | 120 | 0 | 100 | 5 | 100 |

  Scenario: slideRange 修正
    Given min=0 max=100 step=10 value=55
    When 设置 slideRange({ from: 23, to: 76 })
    Then from 修正为 20
    And to 修正为 80
    And value 保持 55

  Scenario: NDK 非法 step
    Given Native Slider 节点
    When 使用 NODE_SLIDER_STEP 设置 .value[0].f32 = 0
    Then 返回 ERROR_CODE_PARAM_INVALID

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
  - repo: "openharmony/arkui_ace_engine"
    query: "Slider SliderOptions value min max step style direction reverse implementation"
  - repo: "openharmony/arkui_ace_engine"
    query: "Slider slideRange SetValidSlideRange minResponsiveDistance trackThickness blockSize"
  - repo: "openharmony/arkui_ace_engine"
    query: "NODE_SLIDER_VALUE NODE_SLIDER_STEP style_modifier.cpp"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/slider.d.ts`
- `interface/sdk-js/api/arkui/component/slider.static.d.ets`
- `interfaces/native/native_node.h`
- `frameworks/core/components_ng/pattern/slider/slider_model_ng.cpp`
- `frameworks/core/components_ng/pattern/slider/slider_pattern.cpp`
