# 特性规格

> Func-04-03-03-Feat-02 背景设置：固化 backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition/backgroundBlurStyle/backdropBlur/backgroundEffect/backgroundBrightness/backgroundImageResizable/background(CustomBuilder) 的存量行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 背景设置 (Background Setting) |
| 特性编号 | Func-04-03-03-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 9/10/11/12/14/18/19 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 背景设置存量规格 | 补录 backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition/backgroundBlurStyle/backdropBlur/backgroundEffect/backgroundBrightness/backgroundImageResizable/background(CustomBuilder) 的 SDK/API/实现/Native 行为 |

> **已知重叠说明**：backgroundColor、backgroundImage、backgroundImageSize、backgroundImagePosition 与 Func-04-03-02 视效属性（Feat-01 图像效果）存在范围重叠。本规格按官方文档「基础属性 → 背景设置」分类覆盖这些 API，与 04-03-02 交叉引用而非互斥。详见 `specs/04-common-capability/03-common-attributes/02-visual-effect-attributes/Feat-01-image-effects-spec.md`。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md` | Draft |
| SDK dynamic | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核验 |
| ArkTS dynamic bridge | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 已核验 |
| Framework API | `frameworks/core/components_ng/base/view_abstract.cpp` | 已核验 |
| RenderContext | `frameworks/core/components_ng/render/render_context.h` | 已核验 |
| EffectOption/BlurStyleOption | `interfaces/inner_api/ace_kit/include/ui/properties/blur_style_option.h` | 已核验 |
| BrightnessOption | `interfaces/inner_api/ace_kit/include/ui/properties/brightness_option.h` | 已核验 |
| Native C API | `interfaces/native/native_node.h`, `frameworks/core/interfaces/native/node/node_common_modifier.cpp` | 已核验 |

> 需求基线、不涉及项、受影响子系统与仓库详见 design.md。本文档为存量特性补录，不提出代码修复。

---

## 用户故事

### US-1: 设置背景颜色（含 ColorMetrics 动态颜色）

**作为** 应用开发者,
**我想要** 通过 `.backgroundColor()` 设置组件背景颜色,
**以便** 为组件提供纯色或动态颜色背景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.backgroundColor(value: ResourceColor)` 且 value 可解析为 Color THEN 属性写入 RenderContext `BackgroundColor` 和 `PreBackgroundColor`，并标记 LayoutProperty `IsUserSetBackgroundColor=true` | 正常 |
| AC-1.2 | WHEN 调用 `.backgroundColor(value: ResourceColor)` 且 value 不可解析 THEN 写入 `Color::TRANSPARENT`（默认透明） | 异常 |
| AC-1.3 | WHEN 调用 `.backgroundColor(Color.TRANSPARENT)` THEN 组件背景透明（等效于未设置 backgroundColor） | 正常 |
| AC-1.4 | WHEN 调用 `.backgroundColor(undefined)`（API 18+） THEN 重置背景颜色为默认（透明） | 异常 |
| AC-1.5 | WHEN 调用 `.backgroundColor(ColorMetrics.colorWithSpace(...))`（API 18+，@since 20 实际生效） THEN ColorMetrics 解析为指定色域的颜色值写入 RenderContext | 正常 |
| AC-1.6 | WHEN Native C-API 设置 `NODE_BACKGROUND_COLOR` THEN `.value[0].u32` 以 0xARGB 格式写入背景色；若传入 bgColorRawPtr 且 ConfigChangePerform=true THEN 注册资源回调 | 正常 |

### US-2: 设置背景图片、大小和位置

**作为** 应用开发者,
**我想要** 通过 `.backgroundImage()`、`.backgroundImageSize()`、`.backgroundImagePosition()` 设置背景图片及其大小和位置,
**以便** 为组件提供图片背景并精确控制图片显示方式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.backgroundImage(src: ResourceStr, repeat?: ImageRepeat)` THEN src 写入 RenderContext `BackgroundImage`（ImageSourceInfo），repeat 写入 `BackgroundImageRepeat` | 正常 |
| AC-2.2 | WHEN 调用 `.backgroundImage(src: PixelMap)` THEN PixelMap 写入 ImageSourceInfo 作为背景图 | 正常 |
| AC-2.3 | WHEN 调用 `.backgroundImage(src: ResourceStr | PixelMap, options?: BackgroundImageOptions)`（API 18+） THEN options 中 `syncLoad` 写入 `BackgroundImageSyncMode`，`repeat` 写入 `BackgroundImageRepeat` | 正常 |
| AC-2.4 | WHEN 调用 `.backgroundImageSize(value: SizeOptions | ImageSize)` THEN 写入 RenderContext `BackgroundImageSize`；SizeOptions 指定宽高值，ImageSize 使用枚举值（Cover/Contain/Auto/None） | 正常 |
| AC-2.5 | WHEN 调用 `.backgroundImagePosition(value: Position | Alignment)` THEN 写入 RenderContext `BackgroundImagePosition`；Position 指定 x/y 坐标，Alignment 使用枚举值 | 正常 |
| AC-2.6 | WHEN Native C-API 设置 `NODE_BACKGROUND_IMAGE` THEN `.string` 为图片地址，`.value[0]?.i32` 为 ImageRepeat 枚举值 | 正常 |
| AC-2.7 | WHEN Native C-API 设置 `NODE_BACKGROUND_IMAGE_SIZE` THEN `.value[0].f32` 和 `.value[1].f32` 为宽高值（vp） | 正常 |
| AC-2.8 | WHEN Native C-API 设置 `NODE_BACKGROUND_IMAGE_POSITION` THEN `.value[0].f32` 和 `.value[1].f32` 为 x/y 坐标值 | 正常 |

### US-3: 设置背景模糊效果

**作为** 应用开发者,
**我想要** 通过 `.backgroundBlurStyle()`、`.backdropBlur()`、`.backgroundEffect()` 设置背景模糊效果,
**以便** 为组件添加材料模糊、自定义半径模糊或组合背景效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.backgroundBlurStyle(value: BlurStyle, options?: BackgroundBlurStyleOptions)` THEN BlurStyleOption 写入 RenderContext `BackBlurStyle`；BlurStyle 枚举（Thin/Regular/Thick/BACKGROUND_* 等）封装预定义模糊参数 | 正常 |
| AC-3.2 | WHEN 调用 `.backgroundBlurStyle(undefined)`（API 18+） THEN 背景模糊重置为默认（无模糊） | 异常 |
| AC-3.3 | WHEN 调用 `.backgroundBlurStyle(style, options, sysOptions)`（API 19+） THEN sysOptions 的 `disableSystemAdaptation` 控制系统自适应调整 | 正常 |
| AC-3.4 | WHEN 调用 `.backdropBlur(value: number, options?: BlurOptions)` THEN 写入 RenderContext `BackBlurRadius`（radius 为 Dimension）；同时清除已有的 `BackgroundEffect` 和 `BackBlurStyle`（互斥覆盖） | 正常 |
| AC-3.5 | WHEN 调用 `.backdropBlur(undefined)`（API 18+） THEN 背景模糊重置为默认 | 异常 |
| AC-3.6 | WHEN 调用 `.backgroundEffect(options: BackgroundEffectOptions)` THEN EffectOption 写入 RenderContext `BackgroundEffect`；同时清除已有的 `BackBlurRadius` 和 `BackBlurStyle`（互斥覆盖） | 正常 |
| AC-3.7 | WHEN 调用 `.backgroundEffect(undefined)`（API 18+） THEN 背景效果重置为默认（无效果） | 异常 |
| AC-3.8 | WHEN 调用 `.backgroundEffect(options, sysOptions)`（API 19+） THEN sysOptions 的 `disableSystemAdaptation` 控制系统自适应调整 | 正常 |
| AC-3.9 | WHEN 同时设置 `backgroundBlurStyle`、`backdropBlur`、`backgroundEffect` THEN 最后设置的生效，其余被清除为 nullopt（三者互斥） | 边界 |
| AC-3.10 | WHEN Native C-API 设置 `NODE_BACKGROUND_BLUR_STYLE` THEN `.value[0].i32` 为 ArkUI_BlurStyle 枚举值 | 正常 |
| AC-3.11 | WHEN Native C-API 设置 `NODE_BACKDROP_BLUR` THEN `.value[0].f32` 为模糊半径值 | 正常 |

### US-4: 设置背景亮度

**作为** 应用开发者,
**我想要** 通过 `.backgroundBrightness()` 设置背景亮度效果,
**以便** 控制组件背景的亮度增减。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.backgroundBrightness({rate, lightUpDegree})` THEN BrightnessOption 写入 RenderContext `BgDynamicBrightnessOption` | 正常 |
| AC-4.2 | WHEN 调用 `.backgroundBrightness(undefined)`（API 18+） THEN 背景亮度重置为默认（无亮度调整） | 异常 |
| AC-4.3 | WHEN rate = 0 THEN lightUpDegree 不生效，无亮度效果 | 边界 |
| AC-4.4 | WHEN lightUpDegree 超出 [-1.0, 1.0] 范围 THEN 内部 BrightnessOption 存储写入实际传入值（不做 Clamp），渲染层可能产生超出预期的视觉效果 | 边界 |

### US-5: 设置背景 CustomBuilder 覆盖

**作为** 应用开发者,
**我想要** 通过 `.background(CustomBuilder)` 设置自定义背景内容,
**以便** 使用声明式组件作为背景覆盖层。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.background(builder: CustomBuilder, options?: {align, ignoresLayoutSafeAreaEdges})` THEN builder 解析为 `BackgroundType::CUSTOM_BUILDER`，CustomBuilder 执行后将内容作为子节点挂载为背景层 | 正常 |
| AC-5.2 | WHEN 调用 `.background(color: ResourceColor, options?)` THEN 颜色写入 `CustomBackgroundColor`（而非 `BackgroundColor`），设置 `IsBuilderBackground=false` | 正常 |
| AC-5.3 | WHEN 同时设置 background(CustomBuilder)、backgroundColor、backgroundImage THEN 三者全部生效，background(CustomBuilder) 位于最上层 | 正常 |
| AC-5.4 | WHEN 调用 `.background(builder)` 且 builder 非 function/object THEN 解析失败，设置不生效 | 异常 |
| AC-5.5 | WHEN CustomBuilder 类型背景的 ignoresLayoutSafeAreaEdges 默认为 `LAYOUT_SAFE_AREA_EDGE_NONE`（不避让安全区）THEN 资源色背景默认为 `LAYOUT_SAFE_AREA_EDGE_ALL` | 边界 |
| AC-5.6 | WHEN Native C-API 设置 `setBackground` THEN 通过 `ArkUIBackgroundContent` 传入 color 和 `ArkUIBackgroundOptions` 传入 align/ignoresLayoutSafeAreaEdges | 正常 |

### US-6: 设置九宫格背景图片

**作为** 应用开发者,
**我想要** 通过 `.backgroundImageResizable()` 设置背景图片的九宫格切片,
**以便** 实现可拉伸的背景图片效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.backgroundImageResizable(value: ResizableOptions)` THEN ImageResizableSlice 写入 RenderContext `BackgroundImageResizableSlice` | 正常 |
| AC-6.2 | WHEN ResizableOptions 的 slice 各边值为正数 THEN 按指定切片拉伸 | 正常 |
| AC-6.3 | WHEN Native C-API 设置 `NODE_BACKGROUND_IMAGE_RESIZABLE_WITH_SLICE` THEN slice 四边值写入 `ImageResizableSlice` | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1, R-8 | 已有实现 | 单测/XTS | `frameworks/core/components_ng/base/view_abstract.cpp:745` |
| AC-2.1~2.8 | R-2 | 已有实现 | 单测/XTS | `frameworks/core/components_ng/base/view_abstract.cpp:838` |
| AC-3.1~3.11 | R-3, R-4 | 已有实现 | 单测/XTS | `frameworks/core/components_ng/base/view_abstract.cpp:1105, 5416` |
| AC-4.1~4.4 | R-7 | 已有实现 | 单测/XTS | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:6343` |
| AC-5.1~5.6 | R-5 | 已有实现 | 单测/XTS | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:13519` |
| AC-6.1~6.3 | R-6 | 已有实现 | 单测/XTS | `frameworks/core/components_ng/base/view_abstract.cpp:11306` |

---

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 backgroundColor | 颜色写入 RenderContext `BackgroundColor` + `PreBackgroundColor`，同时标记 LayoutProperty `IsUserSetBackgroundColor=true` | 默认值 `Color::TRANSPARENT` | AC-1.1, AC-1.2 |
| R-2 | 行为 | 调用 backgroundImage + backgroundImageSize + backgroundImagePosition | 三个属性分别写入 RenderContext Background Property Group（`BackgroundImage`、`BackgroundImageRepeat`、`BackgroundImageSyncMode`、`BackgroundImageSize`、`BackgroundImagePosition`），渲染时组合绘制 | Background Property Group 统一管理 | AC-2.1~2.5 |
| R-3 | 边界 | backdropBlur 与 backgroundBlurStyle 互斥 | 设置 backdropBlur 时清除已有 `BackgroundEffect` 和 `BackBlurStyle`；设置 backgroundBlurStyle 时不清除已有 backdropBlur（但后续 backdropBlur 会清除它） | 三者最后设置生效 | AC-3.9 |
| R-4 | 行为 | 调用 backgroundEffect | EffectOption 写入 RenderContext `BackgroundEffect`，同时清除已有 `BackBlurRadius` 和 `BackBlurStyle` | EffectOption 含 radius/saturation/brightness/color/adaptiveColor/blurOption/policy/inactiveColor | AC-3.6, AC-3.9 |
| R-5 | 边界 | background(CustomBuilder) vs backgroundColor/backgroundImage | CustomBuilder 类型背景作为子节点挂载，与 backgroundColor/backgroundImage 互不排斥，三者全部生效；background 层在最上层 | CustomBuilder 覆盖使用 `CustomBackgroundColor` 而非 `BackgroundColor` 存储 | AC-5.3, AC-5.5 |
| R-6 | 行为 | 调用 backgroundImageResizable | ImageResizableSlice 写入 RenderContext `BackgroundImageResizableSlice`；四边切片值支持 LPX 单位和 ConfigChange 资源回调 | — | AC-6.1, AC-6.2 |
| R-7 | 边界 | backgroundBrightness 参数范围 | rate > 0 时 lightUpDegree 才生效；lightUpDegree 推荐范围 [-1.0, 1.0] 但不做强制 Clamp；BrightnessOption 还支持 cubicCoeff/quadCoeff/saturation/posRGB/negRGB/fraction 等扩展参数（API 12+ internal） | rate=0 时无亮度效果 | AC-4.1, AC-4.3, AC-4.4 |
| R-8 | 行为 | backgroundColor 与 ColorMetrics（API 18+） | @since 20 dynamic 签名支持 `Optional<ResourceColor | ColorMetrics>`；ColorMetrics 通过 `colorWithSpace` 构造带色域的颜色值；@since 18 签名支持 `Optional<ResourceColor>` 用于重置（undefined → 透明） | — | AC-1.4, AC-1.5 |
| R-9 | 行为 | 多背景属性叠加优先级 | backgroundColor（底层色） → backgroundImage（中层图） → background(CustomBuilder)（最上层自定义内容）；模糊/亮度效果作用于背景层 | SDK 注释明确："They will all take effect, with background at the top layer" | AC-5.3 |
| R-10 | 行为 | 背景属性变更标记 | backgroundColor/backgroundImage 等属性变更触发 `PROPERTY_UPDATE_RENDER`，下一帧重绘；backgroundBrightness 变更触发 `ACE_UPDATE_RENDER_CONTEXT(BgDynamicBrightnessOption)` | — | AC-1.1, AC-3.6 |
| R-11 | 异常 | backgroundColor 不可解析 | 写入 `Color::TRANSPARENT` | — | AC-1.2 |
| R-12 | 异常 | background(CustomBuilder) builder 非 function/object | 解析失败，整条设置不生效，函数提前 return | — | AC-5.4 |
| R-13 | 异常 | backgroundBlurStyle/backdropBlur/backgroundEffect 传入 undefined（API 18+） | 对应效果重置为 nullopt（无模糊/无效果） | — | AC-3.2, AC-3.5, AC-3.7 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, AC-1.1 | 单测 | backgroundColor 写入 RenderContext 双属性 |
| VM-2 | R-2, AC-2.1 | 单测 | backgroundImage 组合属性写入 Background Property Group |
| VM-3 | R-3, R-4, AC-3.9 | 单测 | backdropBlur/backgroundBlurStyle/backgroundEffect 互斥清除逻辑 |
| VM-4 | R-5, AC-5.3 | 单测/集成 | background(CustomBuilder) 与 backgroundColor/backgroundImage 共存渲染层级 |
| VM-5 | R-6, AC-6.1 | 单测 | backgroundImageResizable slice 写入 |
| VM-6 | R-7, AC-4.3 | 单测 | backgroundBrightness rate=0 场景 |
| VM-7 | R-8, AC-1.5 | 单测 | ColorMetrics 动态颜色解析 |
| VM-8 | R-9 | 集成/XTS | 多背景属性叠加渲染优先级 |
| VM-9 | R-10 | 单测 | PROPERTY_UPDATE_RENDER 标记 |
| VM-10 | 全量 | XTS/集成 | 端到端背景渲染效果正确 |

---

## API 变更分析

N/A，已有能力补录，API 行为无变化。

### 新增 API

| API 签名 | 类型 | 功能 | d.ts 位置 | @since | 权限要求 |
|----------|------|------|-----------|--------|----------|
| `backgroundColor(value: ResourceColor): T` | Public | 背景颜色 | common.d.ts:20298 | 7 | - |
| `backgroundColor(color: Optional<ResourceColor>): T` | Public | 背景颜色（可重置） | common.d.ts:20312 | 18 | - |
| `backgroundColor(color: Optional<ResourceColor \| ColorMetrics>): T` | Public | 背景颜色（动态色域） | common.d.ts:20326 | 20 | - |
| `backgroundImage(src: ResourceStr \| PixelMap, repeat?: ImageRepeat): T` | Public | 背景图片 | common.d.ts:20428 | 7 | - |
| `backgroundImage(src: ResourceStr \| PixelMap, options?: BackgroundImageOptions): T` | Public | 背景图片（含同步加载/重复选项） | common.d.ts:20443 | 18 | - |
| `backgroundImageSize(value: SizeOptions \| ImageSize): T` | Public | 背景图片大小 | common.d.ts:20483 | 7 | - |
| `backgroundImagePosition(value: Position \| Alignment): T` | Public | 背景图片位置 | common.d.ts:20527 | 7 | - |
| `backgroundBlurStyle(value: BlurStyle, options?: BackgroundBlurStyleOptions): T` | Public | 背景模糊样式 | common.d.ts:20544 | 9 | - |
| `backgroundBlurStyle(style: Optional<BlurStyle>, options?: BackgroundBlurStyleOptions): T` | Public | 背景模糊样式（可重置） | common.d.ts:20565 | 18 | - |
| `backgroundBlurStyle(style: Optional<BlurStyle>, options?: BackgroundBlurStyleOptions, sysOptions?: SystemAdaptiveOptions): T` | Public | 背景模糊样式（系统自适应） | common.d.ts:20588 | 19 | - |
| `backdropBlur(value: number, options?: BlurOptions): T` | Public | 背景模糊半径 | common.d.ts:22396 | 7 | - |
| `backdropBlur(radius: Optional<number>, options?: BlurOptions): T` | Public | 背景模糊（可重置） | common.d.ts:22416 | 18 | - |
| `backdropBlur(radius: Optional<number>, options?: BlurOptions, sysOptions?: SystemAdaptiveOptions): T` | Public | 背景模糊（系统自适应） | common.d.ts:22439 | 19 | - |
| `backgroundEffect(options: BackgroundEffectOptions): T` | Public | 组合背景效果 | common.d.ts:20602 | 11 | - |
| `backgroundEffect(options: Optional<BackgroundEffectOptions>): T` | Public | 组合背景效果（可重置） | common.d.ts:20619 | 18 | - |
| `backgroundEffect(options: Optional<BackgroundEffectOptions>, sysOptions?: SystemAdaptiveOptions): T` | Public | 组合背景效果（系统自适应） | common.d.ts:20646 | 19 | - |
| `backgroundBrightness(params: BackgroundBrightnessOptions): T` | Public | 背景亮度 | common.d.ts:25469 | 12 | - |
| `backgroundBrightness(options: Optional<BackgroundBrightnessOptions>): T` | Public | 背景亮度（可重置） | common.d.ts:25484 | 18 | - |
| `backgroundImageResizable(value: ResizableOptions): T` | Public | 九宫格背景图片 | common.d.ts:20660 | 12 | - |
| `background(content: CustomBuilder \| ResourceColor, options?: BackgroundOptions): T` | Public | 自定义背景 | common.d.ts:20258 | 10/20 | - |

**C-API (NDK) 接口：**

| 属性枚举 | 值格式 | 功能 | @since |
|----------|--------|------|--------|
| `NODE_BACKGROUND_COLOR` | `.value[0].u32` (0xARGB) | 背景颜色 | 12 |
| `NODE_BACKGROUND_IMAGE` | `.string` (图片地址), `.value[0]?.i32` (ImageRepeat) | 背景图片 | 12 |
| `NODE_BACKGROUND_IMAGE_SIZE` | `.value[0].f32` (width vp), `.value[1].f32` (height vp) | 背景图片大小 | 12 |
| `NODE_BACKGROUND_IMAGE_SIZE_WITH_STYLE` | `.value[0].i32` (ArkUI_ImageSize) | 背景图片大小枚举 | 12 |
| `NODE_BACKGROUND_IMAGE_POSITION` | `.value[0].f32` (x), `.value[1].f32` (y) | 背景图片位置 | 12 |
| `NODE_BACKGROUND_BLUR_STYLE` | `.value[0].i32` (ArkUI_BlurStyle) | 背景模糊样式 | 12 |
| `NODE_BACKDROP_BLUR` | `.value[0].f32` (radius vp) | 背景模糊半径 | 12 |
| `NODE_BACKGROUND_IMAGE_RESIZABLE_WITH_SLICE` | slice 四边值 | 九宫格切片 | 12 |
| `setBackground` | `ArkUIBackgroundContent*` + `ArkUIBackgroundOptions*` | 设置背景（资源色+对齐） | 12 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `BackgroundEffectOptions` | `{radius, saturation?, brightness?, color?, adaptiveColor?, blurOptions?, policy?, inactiveColor?}` | common.d.ts:8496 |
| `BackgroundBrightnessOptions` | `{rate, lightUpDegree}` | common.d.ts:29902 |
| `BackgroundBlurStyleOptions` | extends BlurStyleOptions `{policy?, inactiveColor?}` | common.d.ts:8318 |
| `BlurStyle` | Thin/Regular/Thick/BACKGROUND_THIN/BACKGROUND_REGULAR/BACKGROUND_THICK/BACKGROUND_ULTRA_THICK/NONE/COMPONENT_* | common.d.ts:7954 |
| `SystemAdaptiveOptions` | `{disableSystemAdaptation?: boolean}` (default false) | common.d.ts:8395 |
| `BackgroundImageOptions` | `{syncLoad?, repeat?}` | common.d.ts:19582 |
| `BackgroundOptions` | `{align?, ignoresLayoutSafeAreaEdges?}` | common.d.ts:19619 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

---

## 接口规格

### 接口定义

**backgroundColor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `backgroundColor(value: ResourceColor): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceColor | 是 | — | Color \| ColorMetrics \| Resource \| number \| string；不可解析时写入 TRANSPARENT |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 为有效 Color | 写入 BackgroundColor + PreBackgroundColor，标记 IsUserSetBackgroundColor=true | AC-1.1 |
| 2 | value 不可解析 | 写入 Color::TRANSPARENT | AC-1.2 |
| 3 | value 为 undefined（API 18+） | 重置为默认（透明） | AC-1.4 |
| 4 | value 为 ColorMetrics（API 18+） | 解析为指定色域颜色 | AC-1.5 |

---

**backgroundEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `backgroundEffect(options: BackgroundEffectOptions): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.6, AC-3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options.radius | number | 是 | 0 | [0, +∞) |
| options.saturation | number | 否 | 1 | [0, +∞)，推荐 [0, 50] |
| options.brightness | number | 否 | 1 | [0, +∞)，推荐 [0, 2] |
| options.color | ResourceColor | 否 | Transparent | — |
| options.adaptiveColor | AdaptiveColor | 否 | DEFAULT | DEFAULT \| AVERAGE |
| options.blurOptions | BlurOptions | 否 | — | grayscale [0, 127] |
| options.policy | BlurStyleActivePolicy | 否 | ALWAYS_ACTIVE | API 14+ |
| options.inactiveColor | ResourceColor | 否 | Transparent | API 14+，须与 policy 配合 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | options 为有效 BackgroundEffectOptions | 写入 EffectOption 到 RenderContext，清除已有 BackBlurRadius + BackBlurStyle | AC-3.6 |
| 2 | options 为 undefined（API 18+） | 重置 BackgroundEffect 为 nullopt | AC-3.7 |
| 3 | options 含 sysOptions（API 19+） | disableSystemAdaptation 控制系统自适应调整 | AC-3.8 |

---

**background(CustomBuilder)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `background(content: CustomBuilder \| ResourceColor, options?: BackgroundOptions): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1, AC-5.2, AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | CustomBuilder \| ResourceColor | 是 | — | CustomBuilder 须为 function/object；ResourceColor 须可解析为 Color |
| options.align | Alignment | 否 | CENTER | 对齐方式 |
| options.ignoresLayoutSafeAreaEdges | LayoutSafeAreaEdge[] | 否 | CustomBuilder→NONE; ResourceColor→ALL | 安全区避让边 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | content 为 CustomBuilder | 解析为 BackgroundType::CUSTOM_BUILDER，内容挂载为子节点背景层 | AC-5.1 |
| 2 | content 为 ResourceColor | 写入 CustomBackgroundColor（非 BackgroundColor），IsBuilderBackground=false | AC-5.2 |
| 3 | background + backgroundColor + backgroundImage 同时设置 | 三者全部生效，background 最上层 | AC-5.3 |
| 4 | content 非 function/object | 解析失败，不生效 | AC-5.4 |

---

**backgroundImageResizable**

| 属性 | 值 |
|------|-----|
| 函数签名 | `backgroundImageResizable(value: ResizableOptions): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResizableOptions | 是 | — | slice 各边值支持 Dimension/LPX 单位 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 为有效 ResizableOptions | ImageResizableSlice 写入 RenderContext BackgroundImageResizableSlice | AC-6.1 |

---

**backgroundBlurStyle / backdropBlur 互斥规格**

| 属性 | 值 |
|------|-----|
| 函数签名 | `backgroundBlurStyle(value: BlurStyle, options?: BackgroundBlurStyleOptions): T` / `backdropBlur(value: number, options?: BlurOptions): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1, AC-3.4, AC-3.9 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 仅设置 backgroundBlurStyle | BlurStyleOption 写入 BackBlurStyle | AC-3.1 |
| 2 | 设置 backdropBlur | 写入 BackBlurRadius，清除 BackgroundEffect + BackBlurStyle | AC-3.4 |
| 3 | 设置 backgroundEffect | 写入 BackgroundEffect，清除 BackBlurRadius + BackBlurStyle | AC-3.6 |
| 4 | 三者先后设置 | 最后设置的生效，前两者被清除为 nullopt | AC-3.9 |

---

## 兼容性声明

- **已有 API 行为变更:** 否（已有能力补录）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 各 API 按 @since 标注版本号；API 9 新增 backgroundBlurStyle，API 10 新增 BACKGROUND_* BlurStyle 枚举和 background(CustomBuilder)，API 11 新增 backgroundEffect，API 12 新增 backgroundBrightness/backgroundImageResizable/COMPONENT_* BlurStyle 枚举，API 14 新增 policy/inactiveColor 参数，API 18 新增 Optional 重载和 ColorMetrics，API 19 新增 SystemAdaptiveOptions

---

## 架构约束

| 关键约束 | 设计结论 | 影响 AC |
|----------|----------|---------|
| RenderContext Property Group | 背景图片相关属性（BackgroundImage/BackgroundImageRepeat/BackgroundImageSyncMode/BackgroundImageSize/BackgroundImagePosition/BackgroundImageResizableSlice）归入 Background Property Group 统一管理 | AC-2.1~2.5 |
| 三模糊互斥 | backdropBlur/backgroundBlurStyle/backgroundEffect 三者互斥，最后设置清除前两者 | AC-3.9 |
| CustomBuilder 子节点挂载 | background(CustomBuilder) 通过 ViewAbstractModel::SetBackground 挂载为子节点，而非 RenderContext 属性存储 | AC-5.1 |
| CustomBackgroundColor vs BackgroundColor | background(ResourceColor) 使用 CustomBackgroundColor，backgroundColor 使用 BackgroundColor；两者共存时分别渲染 | AC-5.2 |
| PROPERTY_UPDATE_RENDER | 背景属性变更仅标记脏节点重绘，不触发重新布局 | AC-1.1 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | backgroundEffect 每帧实时渲染，高性能开销；静态场景建议使用 effectKit.blur 代替 | benchmark | SDK JSDoc 注释 |
| 内存 | backgroundImage 加载资源图片；backgroundImageResizable 增加切片信息 | hidumper | — |

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
| 无障碍 | 是 | backgroundColor 影响无障碍对比度检测 | 无障碍颜色对比度校验 |
| 大字体 | N/A | 背景属性不受大字体影响 | — |
| 深色模式 | 是 | backgroundColor 使用 ColorMetrics 时可指定色域；BlurStyle 按 ThemeColorMode 调整；背景色/模糊色/inactiveColor 在深色模式下视觉效果不同 | 深色模式背景色切换 |
| 多窗口/分屏 | 是 | 窗口尺寸变化时 backgroundImageSize(百分比) 需重绘；BlurStyleActivePolicy.FOLLOWS_WINDOW_ACTIVE_STATE 窗口失焦时模糊效果可能禁用 | 多窗口模糊策略 |
| 多用户 | N/A | 背景属性无用户态差异 | — |
| 版本升级 | 是 | API 9/10/11/12/14/18/19 各版本新增重载和参数需通过 @since 版本守护 | AC-3.2, AC-3.5, AC-1.4 |
| 生态兼容 | 是 | C-API (NDK) 提供等效接口 | 全部 C-API 属性 |

---

## 行为场景

```gherkin
Feature: 背景设置
  作为 应用开发者
  我想要 通过声明式 API 控制组件的背景颜色、图片、模糊效果和自定义内容
  以便 实现丰富的组件视觉背景

  # ─── backgroundColor 基础 ─────────────────────────

  Scenario: 设置背景颜色
    Given 一个 Column 容器
    When 设置 Column.backgroundColor('#FF0000')
    Then Column 背景色为红色 (0xFFFF0000)
    And RenderContext BackgroundColor = Color(0xFFFF0000)
    And LayoutProperty IsUserSetBackgroundColor = true

  Scenario: 设置透明背景色
    Given 一个 Column 容器已设置 backgroundColor('#FF0000')
    When 设置 Column.backgroundColor(Color.TRANSPARENT)
    Then Column 背景变为透明

  Scenario: backgroundColor 不可解析
    Given 一个 Column 容器
    When 设置 Column.backgroundColor(无效值)
    Then Column 背景色为 TRANSPARENT

  # ─── backgroundImage + size + position ───────────

  Scenario: 设置背景图片及大小
    Given 一个 Column 容器 200vp × 300vp
    When 设置 Column.backgroundImage('/res/bg.png').backgroundImageSize({width: 100, height: 150})
    Then 背景图片以 100vp × 150vp 尺寸渲染

  Scenario: 设置背景图片位置
    Given 一个 Column 容器
    When 设置 Column.backgroundImage('/res/bg.png').backgroundImagePosition({x: 20, y: 30})
    Then 背景图片从 (20vp, 30vp) 坐标开始绘制

  # ─── 三模糊互斥 ──────────────────────────────────

  Scenario: backdropBlur 清除已有 backgroundBlurStyle 和 backgroundEffect
    Given 一个 Column 容器已设置 backgroundBlurStyle(BlurStyle.Thin)
    And 已设置 backgroundEffect({radius: 20})
    When 设置 Column.backdropBlur(10)
    Then BackBlurRadius = Dimension(10)
    And BackBlurStyle = nullopt
    And BackgroundEffect = nullopt

  Scenario: backgroundEffect 清除已有 backdropBlur 和 backgroundBlurStyle
    Given 一个 Column 容器已设置 backdropBlur(10)
    And 已设置 backgroundBlurStyle(BlurStyle.Thin)
    When 设置 Column.backgroundEffect({radius: 20, saturation: 1.5})
    Then BackgroundEffect = EffectOption{radius:20, saturation:1.5}
    And BackBlurRadius = 重置为 Dimension()
    And BackBlurStyle = nullopt

  # ─── background(CustomBuilder) ──────────────────

  Scenario: background + backgroundColor + backgroundImage 共存
    Given 一个 Column 容器
    When 设置 Column.backgroundColor('#FF0000')
    And 设置 Column.backgroundImage('/res/bg.png')
    And 设置 Column.background(() => { this.TextComp.build() })
    Then 三者全部生效
    And backgroundColor 位于底层（纯色）
    And backgroundImage 位于中层（图片）
    And background(CustomBuilder) 位于最上层（自定义内容）

  Scenario: background(ResourceColor)
    Given 一个 Column 容器
    When 设置 Column.background('#00FF00', {align: Alignment.TopStart})
    Then CustomBackgroundColor = Color('#00FF00')
    And IsBuilderBackground = false
    And 背景对齐为 TopStart

  # ─── backgroundImageResizable ────────────────────

  Scenario: 设置九宫格背景图片切片
    Given 一个 Column 容器
    And 已设置 backgroundImage('/res/bg.png')
    When 设置 Column.backgroundImageResizable({slice: {top: 20, bottom: 20, left: 20, right: 20}})
    Then ImageResizableSlice 写入 RenderContext
    And 背景图片按九宫格方式拉伸

  # ─── backgroundBrightness ────────────────────────

  Scenario: 设置背景亮度
    Given 一个 Column 容器
    When 设置 Column.backgroundBrightness({rate: 0.5, lightUpDegree: 0.3})
    Then BrightnessOption{rate:0.5, lightUpDegree:0.3} 写入 BgDynamicBrightnessOption

  Scenario: rate=0 时亮度不生效
    Given 一个 Column 容器
    When 设置 Column.backgroundBrightness({rate: 0, lightUpDegree: 0.5})
    Then lightUpDegree 不生效，无亮度变化

  # ─── API 版本演进 ────────────────────────────────

  Scenario: backgroundBlurStyle undefined 重置（API 18+）
    Given 目标 API 版本 >= 18
    And 一个 Column 容器已设置 backgroundBlurStyle(BlurStyle.Thin)
    When 设置 Column.backgroundBlurStyle(undefined)
    Then 背景模糊重置为默认（无模糊）

  Scenario: SystemAdaptiveOptions 系统自适应（API 19+）
    Given 目标 API 版本 >= 19
    And 一个 Column 容器
    When 设置 Column.backgroundEffect({radius: 20}, {disableSystemAdaptation: true})
    Then 系统不对 backgroundEffect 做自适应调整
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（backgroundColor/backgroundImage/backgroundImageSize/backgroundImagePosition/backgroundBlurStyle/backdropBlur/backgroundEffect/backgroundBrightness/backgroundImageResizable/background(CustomBuilder)；不含 backgroundFilter/foregroundEffect/foregroundBlurStyle/opacity/blur/filter/shadow）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "CommonMethod backgroundColor backgroundImage backgroundImageSize backgroundImagePosition backgroundBlurStyle backdropBlur backgroundEffect backgroundBrightness backgroundImageResizable background CustomBuilder"
  - repo: "openharmony/ace_engine"
    query: "RenderContext Background Property Group BackBlurStyle BackBlurRadius BackgroundEffect BgDynamicBrightnessOption BackgroundImageResizableSlice"
  - repo: "openharmony/ace_engine"
    query: "BlurStyleOption EffectOption BrightnessOption ImageResizableSlice BackgroundImageSize BackgroundImagePosition"
```

**关键文档：**
- SDK dynamic API 定义：`interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 架构设计：`specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md`
- 视效属性重叠规格：`specs/04-common-capability/03-common-attributes/02-visual-effect-attributes/Feat-01-image-effects-spec.md`
