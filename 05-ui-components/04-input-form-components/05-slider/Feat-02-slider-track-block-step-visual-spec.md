# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Slider 轨道、滑块与步点视觉 |
| 特性编号 | Func-05-04-05-Feat-02 |
| FuncID | 05-04-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+ / Static API 23+ / NDK API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出与 Feat-02 相关的历史能力范围。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `blockColor`, `trackColor`, `selectedColor`, `showSteps` | Dynamic API `@since 7`，基础轨道/滑块/步点视觉。 |
| ADDED | `SliderBlockType`, `SliderBlockStyle`, `blockBorderColor`, `blockBorderWidth`, `stepColor`, `trackBorderRadius`, `blockSize`, `blockStyle`, `stepSize` | Dynamic API `@since 10`，滑块外观、边框与步点尺寸。 |
| ADDED | `selectedBorderRadius` | Dynamic API `@since 12`，选中轨道圆角。 |
| ADDED | `selectedColor(ResourceColor \| LinearGradient)` | Dynamic API `@since 18`，选中轨道渐变。 |
| ADDED | `showSteps(value, options?)` | Dynamic API `@since 20`，步点无障碍文本映射；本文只覆盖步点显示与映射落点，无障碍语义归 Feat-04。 |
| ADDED | `blockColor(ResourceColor \| LinearGradient)` | Dynamic API `@since 21`，滑块渐变。 |
| ADDED | `trackColorMetrics(ColorMetricsLinearGradient)` | Dynamic API `@since 23`，ColorMetrics 轨道渐变。 |
| ADDED | NDK `NODE_SLIDER_BLOCK_COLOR/TRACK_COLOR/SELECTED_COLOR/SHOW_STEPS/BLOCK_STYLE/*_LINEAR_GRADIENT_COLOR` | 公开 NDK 视觉属性与渐变属性。 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-input-form-components/05-slider/design.md`
- **KB 路由**: `python3 docs/kb_search.py Slider` 未命中现有 KB 条目
- **SDK 类型定义**:
  - Dynamic: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/@internal/component/ets/slider.d.ts:386`
  - Static: `/home/sunfei/workspace/openHarmony/interface/sdk-js/api/arkui/component/slider.static.d.ets:279`
- **源码定位**:
  - `frameworks/core/components_ng/pattern/slider/slider_model_ng.cpp:92`
  - `frameworks/core/components_ng/pattern/slider/slider_paint_property.h:256`
  - `frameworks/core/components_ng/pattern/slider/slider_content_modifier.cpp:336`
  - `frameworks/core/components_ng/pattern/slider/slider_pattern.cpp:2406`
  - `frameworks/core/components_ng/pattern/slider/bridge/slider_static_modifier.cpp:64`
  - `interfaces/native/native_node.h:5998`
  - `interfaces/native/node/style_modifier.cpp:17977`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 配置轨道与滑块颜色

**角色**: 应用开发者  
**期望**: 我想设置 Slider 滑块、背景轨道和选中轨道的纯色或渐变色。  
**价值**: 以便 Slider 可与应用主题、品牌色和深浅色模式一致。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `blockColor(ResourceColor)` THEN 写入 `BlockColor`，清除 `BlockGradientColor`，并标记用户设置。 | 正常 |
| AC-1.2 | WHEN 调用 `blockColor(LinearGradient)` THEN 写入 `BlockGradientColor`，清除 `BlockColor`，并标记用户设置。 | 正常 |
| AC-1.3 | WHEN 调用 `trackColor(ResourceColor \| LinearGradient)` THEN 写入 `TrackBackgroundColor`，绘制时按渐变 stop 顺序绘制背景轨道。 | 正常 |
| AC-1.4 | WHEN 调用 `selectedColor(ResourceColor \| LinearGradient)` THEN 写入 `SelectColor` 或 `SelectGradientColor`，绘制选中轨道时按 reverse/direction 调整起止点。 | 正常 |
| AC-1.5 | WHEN 轨道或选中轨道渐变 stop 为空 THEN 绘制回退到当前 SliderTheme 的默认轨道色或选中色。 | 异常 |
| AC-1.6 | WHEN 调用 `trackColorMetrics(ColorMetricsLinearGradient)` 且 stop offset 小于 0 或大于 1 THEN offset 分别按 0 或 1 处理。 | 边界 |

### US-2: 配置滑块、轨道圆角和步点视觉

**角色**: 应用开发者  
**期望**: 我想设置滑块类型、滑块边框、轨道圆角、步点显示、步点颜色和步点尺寸。  
**价值**: 以便 Slider 支持默认圆形、图片、自定义形状和不同密度的步进视觉。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `showSteps(true)` 且 stepRatio 非 0 THEN 绘制步点；WHEN `showSteps(false)` 或 stepRatio 为 0 THEN 不绘制步点。 | 正常 |
| AC-2.2 | WHEN 设置 `stepSize` 大于轨道厚度 THEN 实际绘制步点直径不超过轨道厚度；WHEN `stepSize` 为 0 THEN 步点半径为 0。 | 边界 |
| AC-2.3 | WHEN 设置 `stepColor` THEN 步点 brush 使用该颜色绘制。 | 正常 |
| AC-2.4 | WHEN 设置 `trackBorderRadius` 或 `selectedBorderRadius` 为负值 THEN ArkTS/Static 路径校验后 reset 或使用默认值。 | 异常 |
| AC-2.5 | WHEN `blockStyle.type` 为 `DEFAULT` THEN 绘制圆形滑块，`blockColor` 与 `blockBorder*` 生效。 | 正常 |
| AC-2.6 | WHEN `blockStyle.type` 为 `IMAGE` 且 style 非 `NONE` THEN 创建 Image 子节点，按 `ImageFit::COVER` 显示；`blockColor` 和 `blockBorder*` 不产生填充/边框效果。 | 正常 |
| AC-2.7 | WHEN `blockStyle.type` 为 `SHAPE` 且 shape 为 Circle/Ellipse/Rect/Path THEN 按对应 BasicShape 绘制并使用 `blockColor`/`blockBorder*`。 | 正常 |

### US-3: 通过 NDK 配置 Slider 视觉属性

**角色**: NDK 开发者  
**期望**: 我想通过 `ArkUI_AttributeItem` 设置 Slider 的颜色、步点、滑块样式和渐变。  
**价值**: 以便 Native 组件树能与 ArkTS 组件树保持视觉一致。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 通过 `NODE_SLIDER_BLOCK_COLOR/TRACK_COLOR/SELECTED_COLOR` 设置 `.value[0].u32` THEN 返回 `ERROR_CODE_NO_ERROR` 并可 get/reset。 | 正常 |
| AC-3.2 | WHEN 通过 `NODE_SLIDER_SHOW_STEPS` 设置非 0/1 bool 值 THEN 返回 `ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-3.3 | WHEN 通过 `NODE_SLIDER_BLOCK_STYLE` 设置 IMAGE 但 `.string` 为空 THEN 返回 `ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-3.4 | WHEN 通过 `NODE_SLIDER_BLOCK_STYLE` 设置 SHAPE 且宽高或形状参数为负数 THEN 返回 `ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-3.5 | WHEN 通过 `NODE_SLIDER_*_LINEAR_GRADIENT_COLOR` 设置 stop 数量小于 1 或超过限制 THEN 返回 `ERROR_CODE_PARAM_INVALID`。 | 边界 |
| AC-3.6 | WHEN 通过 NDK 渐变属性设置 stop offset < 0 或 > 1 THEN offset clamp 到 0 或 1 后写入。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1, AC-1.2 | R-1, R-2 | TASK-SLIDER-02 | Core UT + Inspector | `slider_model_ng.cpp:92`, `slider_model_ng.cpp:98` |
| AC-1.3 ~ AC-1.5 | R-3, R-4 | TASK-SLIDER-02 | Core UT + 渲染截图 | `slider_content_modifier.cpp:336`, `slider_content_modifier.cpp:1334`, `slider_content_modifier.cpp:1368` |
| AC-1.6 | R-5 | TASK-SLIDER-02 | SDK/API UT | `slider.d.ts:740`, `style_modifier.cpp:20134` |
| AC-2.1 ~ AC-2.3 | R-6, R-7 | TASK-SLIDER-02 | Core UT + 渲染截图 | `slider_content_modifier.cpp:388`, `slider_content_modifier.cpp:476` |
| AC-2.4 | R-8 | TASK-SLIDER-02 | Core UT | `slider_model_ng.cpp:213`, `slider_model_static.cpp:117` |
| AC-2.5 ~ AC-2.7 | R-9, R-10, R-11 | TASK-SLIDER-02 | Core UT + Inspector | `slider_content_modifier.cpp:919`, `slider_pattern.cpp:2406` |
| AC-3.1 ~ AC-3.6 | R-12 ~ R-16 | TASK-SLIDER-02 | C API UT | `style_modifier.cpp:17977`, `style_modifier.cpp:20014` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `blockColor(ResourceColor)` | 更新 `BlockColor`，reset `BlockGradientColor`，`BlockColorSetByUser=true` | 默认滑块色来自 theme；IMAGE 类型无填充色效果 | AC-1.1 |
| R-2 | 行为 | `blockColor(LinearGradient)` | 更新 `BlockGradientColor`，reset `BlockColor`，`BlockColorSetByUser=true` | Dynamic 渐变重载 `@since 21`；Static `@since 23` | AC-1.2 |
| R-3 | 行为 | `trackColor` 或 `selectedColor` 设置纯色/渐变 | 背景轨道、选中轨道按渐变 stop 绘制 | `selectedColor` 渐变 Dynamic `@since 18`；track 渐变 Dynamic `@since 12` | AC-1.3, AC-1.4 |
| R-4 | 恢复 | 轨道或选中轨道渐变 stop 为空 | 使用 SliderTheme 默认轨道色或选中色构造纯色渐变 | 空数组/无效 stop 不绘制空轨道 | AC-1.5 |
| R-5 | 边界 | ColorMetrics 或 NDK 渐变 stop offset 超出 `[0,1]` | 小于 0 写入 0，大于 1 写入 1 | SDK 声明与 NDK 实现均执行 clamp | AC-1.6, AC-3.6 |
| R-6 | 行为 | `showSteps(true)` 且 stepRatio 非 0 | 在轨道起止点之间按 stepRatio 绘制步点 | `showSteps(false)` 或 stepRatio 为 0 不绘制 | AC-2.1 |
| R-7 | 边界 | `stepSize > trackThickness` | 绘制时将 stepSize 限制为 trackThickness | `stepSize=0` 时半径为 0 | AC-2.2, AC-2.3 |
| R-8 | 恢复 | `trackBorderRadius/selectedBorderRadius` 负值或 undefined | ArkTS/Static 路径通过 Length 校验 reset 或使用默认值 | SDK 声明负值使用默认值 | AC-2.4 |
| R-9 | 行为 | `blockStyle.type=DEFAULT` | 绘制圆形滑块，滑块颜色和边框生效 | 半径取 blockSize 宽高较小值的一半 | AC-2.5 |
| R-10 | 行为 | `blockStyle.type=IMAGE` 且 SliderStyle 非 NONE | 创建 Image FrameNode，设置 image source、`ImageFit::COVER`、autoResize | `SliderStyle.NONE` 不绘制 block | AC-2.6 |
| R-11 | 行为 | `blockStyle.type=SHAPE` 且 shape 存在 | 按 BasicShape 类型绘制 Circle/Ellipse/Rect/Path | shape 为空时不绘制自定义形状 | AC-2.7 |
| R-12 | 行为 | NDK 颜色属性 size > 0 | 写入 `.value[0].u32`，返回 `ERROR_CODE_NO_ERROR` | get 返回 `.value[0].u32` | AC-3.1 |
| R-13 | 异常 | NDK `NODE_SLIDER_SHOW_STEPS` 非 bool 或 size=0 | 返回 `ERROR_CODE_PARAM_INVALID` | bool 仅允许 0/1 | AC-3.2 |
| R-14 | 异常 | NDK IMAGE block style 缺少 string | 返回 `ERROR_CODE_PARAM_INVALID` | string 为图片资源路径 | AC-3.3 |
| R-15 | 异常 | NDK SHAPE 参数宽高或 shape 参数为负 | 返回 `ERROR_CODE_PARAM_INVALID` | PATH 宽高、RECT 圆角、Circle/Ellipse 尺寸均不可为负 | AC-3.4 |
| R-16 | 边界 | NDK 渐变 stop 数量 `<1` 或超过 `SLIDER_LINEAR_GRADIENT_LIMIT` | 返回 `ERROR_CODE_PARAM_INVALID` | 合法时写入 block/track/selected 对应渐变 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | Core UT + Inspector | 纯色/渐变互斥、theme 默认回退、reverse/direction 渐变方向。 |
| VM-2 | AC-1.6, AC-3.5, AC-3.6 | C API UT + SDK 对照 | ColorMetrics 与 NDK 渐变 stop 数量和 offset clamp。 |
| VM-3 | AC-2.1 ~ AC-2.4 | Core UT + 渲染截图 | showSteps、stepSize、stepColor、轨道/选中轨道圆角。 |
| VM-4 | AC-2.5 ~ AC-2.7 | Core UT + Inspector | DEFAULT/IMAGE/SHAPE 三类滑块绘制路径。 |
| VM-5 | AC-3.1 ~ AC-3.4 | C API UT | NDK 视觉属性错误码、get/reset 与 blockStyle 参数校验。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `SliderAttribute.blockColor(value)` | Public | `ResourceColor` / `LinearGradient` | `SliderAttribute/this` | N/A | 设置滑块纯色或渐变。 | AC-1.1, AC-1.2 |
| `SliderAttribute.trackColor(value)` | Public | `ResourceColor` / `LinearGradient` | `SliderAttribute/this` | N/A | 设置背景轨道颜色或渐变。 | AC-1.3, AC-1.5 |
| `SliderAttribute.selectedColor(value)` | Public | `ResourceColor` / `LinearGradient` | `SliderAttribute/this` | N/A | 设置选中轨道颜色或渐变。 | AC-1.4, AC-1.5 |
| `SliderAttribute.trackColorMetrics(color)` | Public | `ColorMetricsLinearGradient` | `SliderAttribute/this` | N/A | 使用 ColorMetrics 设置轨道渐变。 | AC-1.6 |
| `SliderAttribute.showSteps(value, options?)` | Public | boolean, `SliderShowStepOptions` | `SliderAttribute/this` | N/A | 控制步点显示，并可携带步点无障碍文本映射。 | AC-2.1 |
| `SliderAttribute.stepColor(value)` / `stepSize(value)` | Public | ResourceColor / Length | `SliderAttribute/this` | N/A | 设置步点颜色和直径。 | AC-2.2, AC-2.3 |
| `SliderAttribute.blockBorderColor/Width`, `trackBorderRadius`, `selectedBorderRadius` | Public | ResourceColor / Length / Dimension | `SliderAttribute/this` | N/A | 设置滑块边框和轨道圆角。 | AC-2.4, AC-2.5 |
| `SliderAttribute.blockStyle(value)` | Public | `SliderBlockStyle` | `SliderAttribute/this` | N/A | 设置滑块 DEFAULT/IMAGE/SHAPE 类型。 | AC-2.5 ~ AC-2.7 |
| `NODE_SLIDER_BLOCK_COLOR/TRACK_COLOR/SELECTED_COLOR/SHOW_STEPS/BLOCK_STYLE/*_LINEAR_GRADIENT_COLOR` | NDK/Public | `ArkUI_AttributeItem` | set 返回 `int32_t`，get 返回 `ArkUI_AttributeItem*` | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID` | Native 视觉属性设置、获取和重置。 | AC-3.1 ~ AC-3.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次为已有能力补录，不改变 API | N/A | N/A |

## 接口规格

### 接口定义

**颜色与渐变属性**

| 属性 | 值 |
|------|-----|
| 函数签名 | `blockColor(value: ResourceColor \| LinearGradient)`, `trackColor(value: ResourceColor \| LinearGradient)`, `selectedColor(value: ResourceColor \| LinearGradient)`, `trackColorMetrics(color: ColorMetricsLinearGradient)` |
| 返回值 | `SliderAttribute/this` — 当前 Slider 属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| blockColor | ResourceColor/LinearGradient | 是 | `$r('sys.color.ohos_id_color_foreground_contrary')` | IMAGE block type 无填充色效果；普通色与渐变互斥。 |
| trackColor | ResourceColor/LinearGradient | 是 | `$r('sys.color.ohos_id_color_component_normal')` | 空渐变回退 theme track bg color。 |
| selectedColor | ResourceColor/LinearGradient | 是 | `$r('sys.color.ohos_id_color_emphasize')` | 空渐变回退 theme selected color。 |
| trackColorMetrics | ColorMetricsLinearGradient | 是 | theme track bg color | offset 小于 0 使用 0，大于 1 使用 1。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 block 普通色 | 写入 BlockColor 并清除 BlockGradientColor | AC-1.1 |
| 2 | 设置 block 渐变色 | 写入 BlockGradientColor 并清除 BlockColor | AC-1.2 |
| 3 | track/selected 渐变为空 | 绘制回退 theme 默认色 | AC-1.5 |
| 4 | ColorMetrics offset 越界 | clamp 到 `[0,1]` | AC-1.6 |

**步点、圆角与滑块样式属性**

| 属性 | 值 |
|------|-----|
| 函数签名 | `showSteps(value: boolean, options?: SliderShowStepOptions)`, `stepColor(value: ResourceColor)`, `stepSize(value: Length)`, `blockStyle(value: SliderBlockStyle)` |
| 返回值 | `SliderAttribute/this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 ~ AC-2.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| showSteps | boolean | 是 | false | true 时绘制步点；options 仅在 true 且存在映射时写入。 |
| stepSize | Length | 是 | `4vp` | 绘制时不超过 trackThickness；0 表示不显示直径。 |
| stepColor | ResourceColor | 是 | theme step color | 写入 StepColor 并标记用户设置。 |
| blockStyle.type | SliderBlockType | 是 | DEFAULT | DEFAULT/IMAGE/SHAPE 分别走圆形、图片、自定义形状路径。 |
| blockStyle.image | ResourceStr | IMAGE 时需要 | N/A | 图片显示区域受 blockSize 约束，ImageFit 为 COVER。 |
| blockStyle.shape | Circle/Ellipse/Rect/Path | SHAPE 时需要 | N/A | shape 为空时不绘制自定义形状。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | showSteps=true 且 stepRatio 非 0 | 按 stepRatio 绘制步点 | AC-2.1 |
| 2 | stepSize 大于 trackThickness | 以 trackThickness 作为绘制上限 | AC-2.2 |
| 3 | blockStyle=IMAGE | 挂载 Image 子节点并使用 COVER | AC-2.6 |
| 4 | blockStyle=SHAPE | 按 BasicShape 绘制滑块 | AC-2.7 |

**NDK 视觉属性**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SetSlider*(ArkUI_NodeHandle node, const ArkUI_AttributeItem* item)` |
| 返回值 | `int32_t` — `ERROR_CODE_NO_ERROR` 或 `ERROR_CODE_PARAM_INVALID` |
| 开放范围 | NDK/Public |
| 错误码 | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID`, `ERROR_CODE_NATIVE_IMPL_TYPE_NOT_SUPPORTED` |
| 关联 AC | AC-3.1 ~ AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| `.value[0].u32` | color | 是 | N/A | 颜色属性 size 必须大于 0。 |
| `.value[0].i32` | bool/blockStyle | 是 | N/A | showSteps 必须为 0/1；blockStyle 必须在 DEFAULT~SHAPE。 |
| `.string` | image/path | 条件必填 | N/A | IMAGE 必须提供图片路径；PATH 使用 path command。 |
| `.object` | `ArkUI_ColorStop*` | 渐变必填 | N/A | `1 <= size <= SLIDER_LINEAR_GRADIENT_LIMIT`。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | NDK 颜色属性 size=0 | 返回参数错误 | AC-3.1 |
| 2 | NDK blockStyle IMAGE 无 string | 返回参数错误 | AC-3.3 |
| 3 | NDK 渐变 stop 数量非法 | 返回参数错误 | AC-3.5 |
| 4 | NDK 渐变 offset 越界 | clamp 后写入 | AC-3.6 |

## 兼容性声明

- **已有 API 行为变更:** 否，本次为已有实现规格补录。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7；Static API 23；NDK 颜色/步点/样式属性按 `native_node.h` 公开版本，线性渐变属性 `@since 21`。
- **API 版本号策略:** 以 `interface/sdk-js` 的 `@since` 和 `interfaces/native/native_node.h` 的 `@since` 为准；源码实现差异作为风险记录，不反推 SDK 契约。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | Dynamic/Static API 签名、版本、默认说明以 SDK 声明为准。 | AC-1.1 ~ AC-2.7 |
| PaintProperty 统一落点 | 颜色、渐变、步点、圆角、blockStyle 均保存到 `SliderPaintProperty`，触发 render。 | AC-1.1 ~ AC-2.7 |
| 图片滑块子节点 | IMAGE 类型由 Pattern 挂载 Image FrameNode，不能仅通过 PaintProperty 验证。 | AC-2.6 |
| NDK 错误码可观测 | NDK 非法入参必须返回 `ERROR_CODE_PARAM_INVALID`，不按 ArkTS reset 语义静默恢复。 | AC-3.2 ~ AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 视觉属性更新仅触发必要 render/measure，不新增阻塞 IO。 | Core UT + Trace | `slider_paint_property.h:256` |
| 功耗 | 步点和渐变绘制不引入后台任务。 | 代码评审 | `slider_content_modifier.cpp:476` |
| 内存 | IMAGE block 仅在 IMAGE 且非 NONE style 时挂载 Image 子节点，类型变化时移除。 | Core UT | `slider_pattern.cpp:2406` |
| 安全 | NDK 形状与渐变参数执行空指针、数量和负值校验。 | C API UT | `style_modifier.cpp:18074`, `style_modifier.cpp:20014` |
| 可靠性 | 空渐变回退 theme 默认色，避免空轨道绘制。 | Core UT | `slider_content_modifier.cpp:1334` |
| 可测试性 | 颜色、showSteps、blockStyle 均可通过 property/getter/Inspector 验证。 | UT + Inspector | `slider_model_ng.cpp:740` |
| 自动化维测 | 不新增日志、埋点或 DFX 事件。 | 代码评审 | N/A |
| 定界定位 | API 层、Model 层、Paint 层、NDK 层证据均可追溯。 | 文档自审 | 本规格验收追溯表 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无功能差异，默认尺寸由 theme 决定。 | 不硬编码像素，按 theme 取默认轨道/滑块/步点尺寸。 | UT + 组件测试 | `slider_model_ng.cpp:223` |
| 平板 | 无功能差异，布局尺寸随父约束变化。 | 渐变方向按 direction/reverse 计算。 | 组件测试 | `slider_content_modifier.cpp:336` |
| 折叠屏 | 无功能差异，窗口尺寸变化后按现有布局路径重新计算。 | 不新增折叠屏专用行为。 | 手工/组件测试 | `slider_pattern.cpp:1075` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | `showSteps(options)` 可携带步点无障碍文本映射；具体虚拟节点行为归 Feat-04。 | AC-2.1 |
| 大字体 | 间接适用 | 视觉属性本身不依赖字体；tip 文本归 Feat-04。 | N/A |
| 深色模式 | 是 | 未被用户设置的颜色在颜色配置更新时跟随 theme 更新。 | AC-1.5 |
| 多窗口/分屏 | 是 | 尺寸变化后按现有 layout/paint 路径重新计算，无额外状态。 | AC-2.1 |
| 多用户 | 否 | 不涉及用户态存储。 | N/A |
| 版本升级 | 是 | 需要保留 Dynamic 7/10/12/18/20/21/23 与 Static 23 的版本边界。 | API 变更分析 |
| 生态兼容 | 是 | NDK 公开属性与内部 modifier 范围不同，避免误把内部函数写为 C API。 | AC-3.1 ~ AC-3.6 |

## 行为场景（可选，Gherkin）

Feature: Slider 轨道、滑块与步点视觉
  作为 ArkUI 开发者
  我想配置 Slider 的颜色、滑块类型和步点
  以便在不同主题下得到可预测的视觉效果

  Scenario: blockColor 普通色覆盖渐变色
    Given Slider 已创建
    When 调用 blockColor(ResourceColor)
    Then SliderPaintProperty 保存 BlockColor
    And BlockGradientColor 被 reset

  Scenario: IMAGE 滑块挂载图片节点
    Given SliderStyle 不是 NONE
    When 调用 blockStyle({ type: IMAGE, image: src })
    Then Slider 挂载 Image FrameNode
    And ImageFit 为 COVER

  Scenario Outline: NDK 渐变 stop 越界
    Given NDK 调用 NODE_SLIDER_TRACK_LINEAR_GRADIENT_COLOR
    When stop offset 为 <offset>
    Then 写入 offset 为 <expected>

    Examples:
      | offset | expected |
      | -0.2 | 0 |
      | 1.5 | 1 |

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
    query: "Slider blockColor trackColor selectedColor showSteps blockStyle implementation"
  - repo: "OpenHarmony/interface/sdk-js"
    query: "SliderAttribute visual APIs dynamic static since"
```

**关键文档：** `slider.d.ts`, `slider.static.d.ets`, `native_node.h`, `slider_model_ng.cpp`, `slider_content_modifier.cpp`, `style_modifier.cpp`
