# 特性规格

> Func-05-08-01-Feat-02 颜色与效果：固化 fillColor、colorFilter、dynamicRangeMode、hdrBrightness、imageMatrix、edgeAntialiasing、antialiased、contentTransition、pointLight 九个颜色效果属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 颜色与效果 (Color and Effects) |
| 特性编号 | Func-05-08-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起支持，API 12/15/19/20/21/23/26 有增强 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 fillColor 重载 | API 15 增加 ColorContent reset 形态，API 20 增加 ColorMetrics/P3 色域输入。 |
| MODIFIED | 补齐 colorFilter(ResourceColor) | API 26 支持 ResourceColor，并转换为 DrawingColorFilter + SRC_ATOP blend。 |
| MODIFIED | 补齐 pointLight | 动态/静态 SDK 暴露 system API `pointLight`，实现落到通用 RenderContext 点光源属性。 |
| MODIFIED | 补齐 NDK/静态覆盖 | C API 覆盖 dynamicRangeMode、hdrBrightness、contentTransition、antialiased；静态版 API 23 起覆盖全部本特性属性。 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `arkui-specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/image.d.ts` | 已核对：颜色与效果属性声明 |
| Static SDK | `interface/sdk-js/api/arkui/component/image.static.d.ets` | 已核对：静态颜色与效果属性声明 |
| C API | `interfaces/native/native_node.h` | 已核对：Image 颜色/效果相关 NDK 属性枚举 |

---

## 用户故事

### US-1: 设置 SVG 填充颜色

**作为** 应用开发者,
**我想要** 通过 fillColor 属性设置 SVG 图片的填充颜色,
**以便** 动态改变 SVG 图标的颜色以适配主题或状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.fillColor(value: ResourceColor)` THEN 设置 SVG 填充颜色 | 正常 |
| AC-1.2 | WHEN fillColor 设置后 THEN 同时更新 SvgFillColor 渲染属性和 ForegroundColor 渲染上下文，`image_model_ng.cpp:447-451` | 正常 |
| AC-1.3 | WHEN fillColor 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-1.4 | WHEN fillColor 应用到 SVG THEN 通过 svgCanvas->SetFillColor() 生效，`image_content_modifier.cpp:86-103` | 正常 |
| AC-1.5 | WHEN fillColor 变更且图片为 HDR 内容 THEN 同步更新 HDR headroom，`image_content_modifier.cpp:67-84` | 正常 |
| AC-1.6 | WHEN API 15+ 传入 ColorContent THEN fillColor 走 reset/无用户色路径，用于取消用户设置的填充色 | 边界 |
| AC-1.7 | WHEN API 20+ 传入 ColorMetrics THEN fillColor 支持 P3 高色域颜色输入，最终仍写入 SvgFillColor/ForegroundColor | 正常 |
| AC-1.8 | WHEN API 21+ 且 supportSvg2=true THEN fillColor 是否覆盖 SVG 元素取决于源 SVG 的 fill 属性；fill='none' 时不生效 | 边界 |

### US-2: 设置颜色滤镜

**作为** 应用开发者,
**我想要** 通过 colorFilter 属性设置颜色滤镜矩阵或 DrawingColorFilter,
**以便** 对图片应用自定义颜色变换效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.colorFilter(value: ColorFilter)` 传入 4x5 矩阵数组 THEN 设置颜色滤镜矩阵（20 个 float 元素的 identity 矩阵为默认） | 正常 |
| AC-2.2 | WHEN 调用 colorFilter 传入 DrawingColorFilter 对象 THEN 设置 Drawing 渲染滤镜 | 正常 |
| AC-2.3 | WHEN 设置 ColorFilter 矩阵 THEN 自动重置 DrawingColorFilter（互斥），`image_model_ng.cpp:497-501` | 正常 |
| AC-2.4 | WHEN 设置 DrawingColorFilter THEN 自动重置 ColorFilter 矩阵（互斥），`image_model_ng.cpp:503-507` | 正常 |
| AC-2.5 | WHEN 未设置 colorFilter THEN 使用默认 identity 矩阵 `{1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,1,0}`，`image_model_ng.cpp:40` | 异常 |
| AC-2.6 | WHEN colorFilter 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-2.7 | WHEN colorFilter 应用到 SVG 且 API >= 12 THEN 通过 svgCanvas 应用颜色滤镜，`image_content_modifier.cpp:96-101` | 边界 |
| AC-2.8 | WHEN API 26+ colorFilter 传入 ResourceColor THEN 解析为颜色并创建 `BlendMode::SRC_ATOP` 的 DrawingColorFilter；解析失败时重置为默认矩阵 | 正常 |
| AC-2.9 | WHEN supportSvg2=true 且 API 21+ THEN SVG colorFilter 作用到整个 SVG 源；API 12~20 仅按旧 SVG/stroke 规则生效 | 边界 |

> ColorFilter 双类型（矩阵 vs DrawingColorFilter）互斥设计，见 design.md ADR 部分。

### US-3: 设置动态范围模式

**作为** 应用开发者,
**我想要** 通过 dynamicRangeMode 属性控制 HDR 图片的渲染方式,
**以便** 在支持 HDR 的设备上获得更好的视觉效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.dynamicRangeMode(value: DynamicRangeMode)` THEN 设置动态范围模式，默认为 STANDARD | 正常 |
| AC-3.2 | WHEN dynamicRangeMode 为 HIGH(0) THEN 使用 HDR 渲染（需要设备支持） | 正常 |
| AC-3.3 | WHEN dynamicRangeMode 为 CONSTRAINT(1) THEN 使用受限 HDR 渲染 | 正常 |
| AC-3.4 | WHEN dynamicRangeMode 为 STANDARD(2) THEN 使用标准 SDR 渲染（默认值） | 正常 |
| AC-3.5 | WHEN dynamicRangeMode 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-3.6 | WHEN 同时设置了 hdrBrightness 且图片为 HDR PixelMap THEN dynamicRangeMode 被强制为 HIGH，`image_paint_method.cpp:134-138` | 正常 |

> DynamicRangeMode 枚举 3 个值，`constants.h:368-372`

### US-4: 设置 HDR 亮度

**作为** 应用开发者,
**我想要** 通过 hdrBrightness 属性调整 HDR 图片的亮度,
**以便** 在 HDR 显示模式下精细控制图片亮度表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.hdrBrightness(value: number)` THEN 设置 HDR 亮度值，默认为 1.0，SDK 有效范围 [0.0, 1.0] | 正常 |
| AC-4.2 | WHEN hdrBrightness 设置且图片为 HDR PixelMap THEN 设置 renderContext 的 ImageHDRBrightness 并启用 ImageHDRPresent，`image_paint_method.cpp:134-138` | 正常 |
| AC-4.3 | WHEN hdrBrightness 设置且图片为 HDR THEN 强制 dynamicRangeMode 为 HIGH | 正常 |
| AC-4.4 | WHEN hdrBrightness 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-4.5 | WHEN hdrBrightness < 0.0 或 > 1.0 THEN JSView/C API 均按默认 1.0 写入 | 边界 |

> DEFAULT_HDR_BRIGHTNESS = 1.0f，`image_render_property.h:32`

### US-5: 设置变换矩阵

**作为** 应用开发者,
**我想要** 通过 imageMatrix 属性设置图片的变换矩阵,
**以便** 对图片应用自定义的仿射或透视变换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.imageMatrix(value: Matrix4Transit)` THEN 设置变换矩阵 | 正常 |
| AC-5.2 | WHEN imageMatrix 仅在 objectFit 为 MATRIX(17) 时生效，`image_paint_method.cpp:142-156` | 正常 |
| AC-5.3 | WHEN objectFit 非 MATRIX 且设置了 imageMatrix THEN imageMatrix 被忽略 | 正常 |
| AC-5.4 | WHEN 未设置 imageMatrix 且 objectFit 为 MATRIX THEN 使用 identity 矩阵作为默认值 | 异常 |
| AC-5.5 | WHEN imageMatrix 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-5.6 | WHEN 同时设置 resizable 或 objectRepeat THEN SDK 声明 imageMatrix 不生效；实现侧仅在 paint 配置中要求 objectFit=MATRIX 后读取矩阵，resizable/objectRepeat 的互斥需作为兼容约束测试 | 边界 |

> imageMatrix 存储在 RenderProperty 但不在 ImagePaintStyle 组内，独立存储，`image_render_property.h:87`

### US-6: 设置边缘抗锯齿

**作为** 应用开发者,
**我想要** 通过 edgeAntialiasing 属性设置图片边缘抗锯齿强度,
**以便** 改善图片边缘的渲染质量。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 system API `.edgeAntialiasing(value: number)` THEN 设置 SVG 边缘抗锯齿值（float 类型内部存储为 SmoothEdge） | 正常 |
| AC-6.2 | WHEN 未显式设置 THEN 默认为 0.0f（无抗锯齿），`image_paint_method.cpp:113` | 正常 |
| AC-6.3 | WHEN 图片为 SVG THEN 同时应用 smoothEdge 到 svgCanvas，`image_content_modifier.cpp:94` | 正常 |
| AC-6.4 | WHEN SVG 场景下 smoothEdge 值 THEN 取 max(theme默认值, renderProp值)，`image_pattern.cpp:895-900` | 边界 |
| AC-6.5 | WHEN edgeAntialiasing 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-6.6 | WHEN 静态实现传入值超出 (0.333, 1.333] THEN Converter Validator 对可选值做范围校验；动态 JSView 路径仍按解析值写入，需作为版本/范式差异记录 | 边界 |

### US-7: 设置抗锯齿

**作为** 应用开发者,
**我想要** 通过 antialiased 属性开启或关闭图片渲染的抗锯齿,
**以便** 控制图片缩放时的边缘平滑处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.antialiased(value: boolean)` THEN 设置抗锯齿开关，默认为 false | 正常 |
| AC-7.2 | WHEN antialiased 为 true THEN 图片渲染时启用抗锯齿 | 正常 |
| AC-7.3 | WHEN antialiased 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-7.4 | WHEN antialiased 与 resizable 同时设置 THEN SDK 声明 antialiased 不生效，渲染配置仍需以 resizable 场景为准 | 边界 |

> `image_paint_method.cpp:118`：`config.antiAlias_ = renderProps->GetAntiAliasValue(false)`

### US-8: 设置内容过渡效果

**作为** 应用开发者,
**我想要** 通过 contentTransition 属性设置图片源切换时的过渡动画,
**以便** 在更换图片时提供平滑的视觉效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.contentTransition(value: ContentTransitionEffect)` THEN 设置内容过渡类型 | 正常 |
| AC-8.2 | WHEN contentTransition 为 IDENTITY(0) THEN 无过渡效果（默认） | 正常 |
| AC-8.3 | WHEN contentTransition 为 OPACITY(1) THEN 图片切换时使用透明度淡入淡出过渡 | 正常 |
| AC-8.4 | WHEN 图片源变更且 contentTransition 非 IDENTITY THEN ImagePaintMethod 根据源变更判断是否需要过渡动画，`image_paint_method.cpp:159-180` | 正常 |
| AC-8.5 | WHEN 图片为 SVG 或动画图片 THEN 跳过内容过渡动画 | 正常 |
| AC-8.6 | WHEN contentTransition 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |

> ContentTransitionType 枚举 2 个值（IDENTITY=0, OPACITY=1），`constants.h:977-980`

### US-9: 设置点光源效果

**作为** 系统应用开发者,
**我想要** 通过 pointLight 设置 Image 的点光源、照亮边框和 bloom 效果,
**以便** 在支持点光源编译能力的场景下获得统一的空间光效。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 system API `.pointLight(value: PointLightStyle)` THEN 实现把 lightSource 映射到通用 RenderContext 的 LightPosition/LightIntensity/LightColor | 正常 |
| AC-9.2 | WHEN pointLight 中 illuminationType 存在 THEN 实现通过 ViewAbstractModelStatic 写入 LightIlluminated/IlluminatedBorderWidth | 正常 |
| AC-9.3 | WHEN pointLight 中 bloom 存在 THEN 实现写入 RenderContext Bloom，并通过 shadow 参数表达 bloom 半径和颜色 | 正常 |
| AC-9.4 | WHEN POINT_LIGHT_ENABLE 未开启 THEN pointLight 相关实现被宏裁剪，调用不产生 Image 专属属性变更 | 边界 |
| AC-9.5 | WHEN NDK 通用 pointLight C API 使用在 Image 节点上 THEN 走 `node_common_modifier` 通用点光源接口；`native_node.h` 没有 `NODE_IMAGE_POINT_LIGHT` 专属枚举 | 正常 |

> pointLight SDK 声明：动态 `interface/sdk-js/api/@internal/component/ets/image.d.ts:1302`，静态 `interface/sdk-js/api/arkui/component/image.static.d.ets:839`。静态实现：`frameworks/core/interfaces/native/implementation/image_modifier.cpp:422-455`；通用 NDK 实现：`frameworks/core/interfaces/native/node/node_common_modifier.cpp:6113-6245`；RenderContext 属性：`frameworks/core/components_ng/render/render_context.h:686-693`。

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.8 | R-2, R-4, R-16 | — | 代码审查 | `image.d.ts:942`, `image.d.ts:966`, `image.d.ts:992`, `image_model_ng.cpp:462-466` |
| AC-2.1~2.9 | R-3, R-5, R-12, R-17 | — | 代码审查 | `image.d.ts:1236`, `image.d.ts:1255`, `arkts_native_image_bridge.cpp:953-992` |
| AC-3.1~3.6 | R-6, R-13 | — | 代码审查 | `image_paint_method.cpp:134-138` |
| AC-4.1~4.5 | R-7, R-18 | — | 代码审查 | `image.d.ts:1137`, `js_image.cpp:1131-1140`, `node_image_modifier.cpp:963-970` |
| AC-5.1~5.6 | R-8, R-14 | — | 代码审查 | `image_paint_method.cpp:142-156` |
| AC-6.1~6.6 | R-9, R-19 | — | 代码审查 | `image_content_modifier.cpp:94`, `image_modifier.cpp:458-466` |
| AC-7.1~7.4 | R-10, R-20 | — | 代码审查 | `image_paint_method.cpp:118`, `image_model_ng.cpp:1481-1497` |
| AC-8.1~8.6 | R-11 | — | 代码审查 | `image_paint_method.cpp:159-180` |
| AC-9.1~9.5 | R-21 | — | 代码审查 | `image_modifier.cpp:422-455`, `node_common_modifier.cpp:6113-6245` |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用颜色与效果属性 setter | 除 pointLight 外，本特性属性主要存储在 ImageRenderProperty/RenderContext 中，触发 PROPERTY_UPDATE_RENDER，不触发布局重测 | pointLight 是通用 RenderContext 点光源属性 | AC-1.1~AC-9.5 |
| R-2 | 行为 | 调用 fillColor(ResourceColor/ColorContent/ColorMetrics) | fillColor 同时更新 SvgFillColor 和 ForegroundColor，SVG 绘制时通过 SetFillColor 应用 | ColorContent 可表达 reset，ColorMetrics 支持 P3 输入 | AC-1.1~AC-1.8 |
| R-3 | 行为 | 调用 colorFilter 矩阵、DrawingColorFilter 或 ResourceColor | colorFilter 的矩阵、DrawingColorFilter/ResourceColor blend 互斥，设置一种会重置另一种 | 默认矩阵为 identity | AC-2.1~AC-2.9 |
| R-4 | 行为 | SVG Canvas 更新颜色配置 | fillColor 通过 svgCanvas->SetFillColor() 应用到 SVG 渲染，同时同步 HDR headroom | API 21 + supportSvg2 时受源 SVG fill 属性影响 | AC-1.4~AC-1.8 |
| R-5 | 行为 | colorFilter 应用到 SVG | API 12 起 SVG 路径可应用 colorFilter；API 21 + supportSvg2 时作用到整个 SVG 源 | API 11 及以前 SVG 不可用 | AC-2.7, AC-2.9 |
| R-6 | 行为 | 设置 dynamicRangeMode | dynamicRangeMode 控制 HDR 渲染模式，STANDARD 为默认；hdrBrightness + HDR PixelMap 会强制 dynamicMode=HIGH | 设备行为差异见多设备适配 | AC-3.1~AC-3.6 |
| R-7 | 行为 | 设置 hdrBrightness 且图片为 HDR PixelMap | hdrBrightness 默认 1.0，仅对 HDR PixelMap 生效，同时强制 dynamicRangeMode 为 HIGH | 取值范围 [0.0, 1.0] | AC-4.1~AC-4.5 |
| R-8 | 行为 | objectFit=MATRIX 且设置 imageMatrix | imageMatrix 仅在 objectFit=MATRIX 时写入 PaintConfig，未设置时使用 identity 矩阵 | resizable/objectRepeat 互斥按 SDK 声明纳入测试 | AC-5.1~AC-5.6 |
| R-9 | 行为 | system API edgeAntialiasing 设置 SVG smoothEdge | edgeAntialiasing 内部存储为 SmoothEdge，SVG 绘制时传给 svgCanvas | SDK 范围 (0.333, 1.333]，默认 0.0 | AC-6.1~AC-6.6 |
| R-10 | 行为 | antialiased=true/false | antialiased 控制 pixel map 图片边缘抗锯齿，默认 false | 与 resizable 同时设置时 SDK 声明不生效 | AC-7.1~AC-7.4 |
| R-11 | 行为 | contentTransition=OPACITY 且图片源变化 | contentTransition 支持透明度过渡；动态图片资源、SVG 动画和多帧图跳过过渡 | undefined/null 按 IDENTITY | AC-8.1~AC-8.6 |
| R-12 | 异常 | 先后设置 colorFilter 矩阵和 DrawingColorFilter/ResourceColor | 后设置的滤镜类型覆盖先设置的滤镜类型 | 不抛错，按最后一次有效设置生效 | AC-2.3~AC-2.8 |
| R-13 | 异常 | hdrBrightness 设置且 dynamicRangeMode 也设置 | 渲染阶段 dynamicRangeMode 被 hdrBrightness + HDR PixelMap 强制覆盖为 HIGH | 仅 HDR PixelMap 场景 | AC-3.6, AC-4.3 |
| R-14 | 异常 | objectFit 非 MATRIX 且设置 imageMatrix | imageMatrix 保存在 RenderProperty 但不会写入 PaintConfig 的有效矩阵 | 可通过渲染结果观察 | AC-5.2~AC-5.5 |
| R-15 | 恢复 | contentTransition 参数为 undefined/null 或非法类型 | Bridge/Model 将 contentTransition 重置为 IDENTITY，后续图片源变化不执行过渡 | 默认 IDENTITY | AC-8.1~AC-8.6 |
| R-16 | 边界 | fillColor 传入无效 ResourceColor | API 11+ 路径使用主题默认颜色，API 11 前资源重载失败路径可能直接返回 | 当前实现不抛异常 | AC-1.1~AC-1.7 |
| R-17 | 行为 | API 26+ colorFilter 传入 ResourceColor | ResourceColor 被转换为 DrawingColorFilter，BlendMode 为 SRC_ATOP | 解析失败重置默认矩阵 | AC-2.8 |
| R-18 | 边界 | hdrBrightness 超出 [0.0, 1.0] | JSView 与 C API 均回退为 DEFAULT_HDR_BRIGHTNESS=1.0 | 包含小于 0 和大于 1 | AC-4.5 |
| R-19 | 边界 | 静态 edgeAntialiasing 超出 (0.333, 1.333] | Converter Validator 对可选值做范围校验；动态路径未见同等范围钳制 | 范式差异需测试覆盖 | AC-6.6 |
| R-20 | 边界 | antialiased 与 resizable 同时配置 | SDK 声明 antialiased 不生效，渲染配置以 resizable 切片/网格路径为约束 | 不抛异常 | AC-7.4 |
| R-21 | 行为 | pointLight 在 POINT_LIGHT_ENABLE 开启时设置 | 实现把 PointLightStyle 映射到通用 RenderContext 点光源、照亮和 bloom 属性 | 未开启宏时相关实现为空 | AC-9.1~AC-9.5 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5 (fillColor) | XTS | SVG 颜色填充和 HDR headroom 同步 |
| VM-2 | AC-2.1~2.9 (colorFilter) | XTS | 矩阵/DrawingColorFilter/ResourceColor 互斥和默认 identity |
| VM-3 | AC-3.1~3.6 (dynamicRangeMode) | XTS | HDR 模式和 hdrBrightness 强制覆盖 |
| VM-4 | AC-4.1~4.5 (hdrBrightness) | XTS | HDR 亮度设置、边界值和强制 HIGH 模式 |
| VM-5 | AC-5.1~5.6 (imageMatrix) | XTS | MATRIX 模式生效、非 MATRIX 忽略和互斥属性 |
| VM-6 | AC-6.1~6.6 (edgeAntialiasing) | XTS | SVG 场景 max 取值逻辑和静态范围校验 |
| VM-7 | AC-7.1~7.4 (antialiased) | XTS | 抗锯齿开关及 resizable 互斥 |
| VM-8 | AC-8.1~8.6 (contentTransition) | XTS | OPACITY 过渡和 SVG/动画豁免 |
| VM-9 | AC-9.1~9.5 (pointLight) | 系统 API 测试 + 代码审查 | POINT_LIGHT_ENABLE 宏开启/关闭下 RenderContext 点光源属性 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `fillColor(value: ResourceColor | ColorContent | ColorMetrics)` | Public | 资源色、reset 色内容、P3 ColorMetrics | ImageAttribute/this | N/A | 设置 SVG 填充颜色 | AC-1.1~AC-1.8 |
| `colorFilter(value: ColorFilter | DrawingColorFilter | ResourceColor)` | Public | 4x5 矩阵、DrawingColorFilter、API 26 ResourceColor | ImageAttribute/this | N/A | 设置颜色滤镜 | AC-2.1~AC-2.9 |
| `dynamicRangeMode(value: DynamicRangeMode)` | Public | HIGH/CONSTRAINT/STANDARD | ImageAttribute/this | N/A | 设置动态范围模式 | AC-3.1~AC-3.6 |
| `hdrBrightness(value: number)` | Public | [0.0, 1.0] | ImageAttribute/this | N/A | 设置 HDR 亮度 | AC-4.1~AC-4.5 |
| `imageMatrix(value: Matrix4Transit)` | Public | Matrix4Transit | ImageAttribute/this | N/A | 设置变换矩阵（仅 MATRIX 模式生效） | AC-5.1~AC-5.6 |
| `edgeAntialiasing(value: number)` | System | (0.333, 1.333]，默认 0.0 | ImageAttribute/this | N/A | 设置 SVG 边缘抗锯齿强度 | AC-6.1~AC-6.6 |
| `antialiased(value: Optional<boolean>)` | Public | boolean/undefined | ImageAttribute/this | N/A | 设置 pixel map 图片边缘抗锯齿 | AC-7.1~AC-7.4 |
| `contentTransition(value: ContentTransitionEffect)` | Public | IDENTITY/OPACITY | ImageAttribute/this | N/A | 设置内容过渡效果 | AC-8.1~AC-8.6 |
| `pointLight(value: PointLightStyle)` | System | lightSource/illuminationType/bloom | ImageAttribute/this | N/A | 设置通用点光源效果 | AC-9.1~AC-9.5 |
| `NODE_IMAGE_COLOR_FILTER`/`NODE_IMAGE_FILL_COLOR`/`NODE_IMAGE_DYNAMIC_RANGE_MODE`/`NODE_IMAGE_HDR_BRIGHTNESS`/`NODE_IMAGE_IMAGE_MATRIX`/`NODE_IMAGE_CONTENT_TRANSITION`/`NODE_IMAGE_ANTIALIASED` | Public C API | ArkUI_AttributeItem 数组、对象或数值 | ArkUI_AttributeItem | N/A | NDK Image 颜色/效果属性 | AC-1.1~AC-8.6 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**colorFilter(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `colorFilter(value: ColorFilter | DrawingColorFilter | ResourceColor): ImageAttribute` |
| 返回值 | `ImageAttribute` / `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ColorFilter/DrawingColorFilter/ResourceColor | 是 | identity 矩阵 | ColorFilter 矩阵为 20 个 float；DrawingColorFilter 与矩阵互斥；ResourceColor API 26 起转换为 SRC_ATOP blend。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 20 个 float 的矩阵数组 | 写入 ColorFilter 并重置 DrawingColorFilter | AC-2.1, AC-2.3 |
| 2 | 传入 DrawingColorFilter | 写入 DrawingColorFilter 并重置矩阵 ColorFilter | AC-2.2, AC-2.4 |
| 3 | API 26+ 传入 ResourceColor | 创建 SRC_ATOP DrawingColorFilter | AC-2.8 |

**pointLight(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pointLight(value: PointLightStyle): ImageAttribute` |
| 返回值 | `ImageAttribute` / `this` |
| 开放范围 | System |
| 错误码 | N/A |
| 关联 AC | AC-9.1~AC-9.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | PointLightStyle | 是 | 清空点光源 | 仅 POINT_LIGHT_ENABLE 宏开启时生效；lightSource、illuminationType、bloom 可分别映射到通用 RenderContext 属性。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value.lightSource 存在 | 设置 LightPosition、LightIntensity、LightColor | AC-9.1 |
| 2 | value 为空或未提供 lightSource | 清空点光源位置、强度、颜色 | AC-9.1 |
| 3 | POINT_LIGHT_ENABLE 未开启 | 实现宏裁剪，调用不改变 Image 专属属性 | AC-9.4 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（fillColor/imageMatrix/objectFit 关联能力），API 9 colorFilter/copy 相关能力，静态 Image API 23
- **API 版本号策略:** fillColor API 15 支持 ColorContent、API 20 支持 ColorMetrics、API 21 与 supportSvg2 交互；colorFilter API 12 支持 DrawingColorFilter，API 21 supportSvg2 SVG 全源生效，API 26 支持 ResourceColor；dynamicRangeMode API 12、hdrBrightness API 19、contentTransition API 21、antialiased API 23、静态属性 API 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| RenderProperty 统一存储 | 8 个属性均存储在 ImageRenderProperty 的 ImagePaintStyle 组内（imageMatrix 除外），仅触发 RENDER | AC-1~8 |
| imageMatrix 独立存储 | imageMatrix 在 RenderProperty 但不在 ImagePaintStyle 组内，独立管理 | AC-5 |
| colorFilter 双类型互斥 | 矩阵和 DrawingColorFilter 通过桥接层互斥管理 | AC-2.3~2.4 |
| HDR 联动 | hdrBrightness 和 dynamicRangeMode 存在强制覆盖关系 | AC-3.6, AC-4.3 |
| pointLight 通用属性 | pointLight 不走 ImageRenderProperty，而是写入通用 RenderContext 点光源属性；C API 也走 common modifier | AC-9.1~AC-9.5 |
| SDK/实现互斥约束 | imageMatrix、antialiased 与 resizable/objectRepeat 的互斥主要来自 SDK 声明，需测试验证实现侧实际绘制 | AC-5.6, AC-7.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 颜色效果仅触发 RENDER 不触发 MEASURE，最小化更新范围 | 代码审查 | PROPERTY_UPDATE_RENDER 标志 |
| 内存 | colorFilter 矩阵为 20 float（80 字节），DrawingColorFilter 为 RefPtr 智能指针 | 代码审查 | `image_render_property.h:40-41` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |
| 非手机/PC/2-in-1/平板设备 | dynamicRangeMode SDK 声明不生效 | 动态范围模式仅在 SDK 指定设备类型上生效 | SDK 审查 | `interface/sdk-js/api/@internal/component/ets/image.d.ts:1104-1117` |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 颜色效果不影响无障碍 | — |
| 大字体 | 否 | 颜色效果不受大字体影响 | — |
| 深色模式 | 是 | fillColor 可用于适配深色主题 SVG 颜色 | AC-1 |
| 多窗口/分屏 | 否 | 无特殊处理 | — |
| 多用户 | 否 | 无特殊处理 | — |
| 版本升级 | 是 | colorFilter SVG 应用仅 API >= 12 | AC-2.7 |
| 生态兼容 | 是 | API 21 supportSvg2 改变 fillColor/colorFilter 对 SVG 的作用范围；API 26 colorFilter(ResourceColor) 改走 SRC_ATOP blend | AC-1.8, AC-2.8~AC-2.9 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 颜色与效果属性

  Scenario: colorFilter 矩阵和 DrawingColorFilter 互斥
    Given 一个 Image 组件已设置 ColorFilter 矩阵
    When 调用 colorFilter 设置 DrawingColorFilter 对象
    Then ColorFilter 矩阵被自动重置为空
    And DrawingColorFilter 生效

  Scenario: hdrBrightness 强制 dynamicRangeMode 为 HIGH
    Given 一个 Image 组件，dynamicRangeMode 设置为 STANDARD
    And 设置了 hdrBrightness 为 1.5
    And 图片源为 HDR PixelMap
    When 触发渲染
    Then dynamicRangeMode 被强制覆盖为 HIGH
    And renderContext 启用 ImageHDRPresent

  Scenario: imageMatrix 仅在 MATRIX 模式生效
    Given 一个 Image 组件，objectFit 设置为 COVER
    And imageMatrix 设置了缩放变换矩阵
    When 触发渲染
    Then imageMatrix 被忽略，使用 COVER 的布局计算结果

  Scenario: contentTransition OPACITY 淡入淡出
    Given 一个 Image 组件，contentTransition 设置为 OPACITY
    When 图片源从 A 变更为 B
    Then 图片 B 以透明度淡入效果显示
    And 图片 A 以透明度淡出效果消失

  Scenario: API 26 colorFilter ResourceColor
    Given 一个 Image 组件，运行在 API 26
    When 调用 colorFilter(Color.Red)
    Then 桥接层创建 SRC_ATOP DrawingColorFilter
    And 原 ColorFilter 矩阵被重置

  Scenario: pointLight 宏开启
    Given POINT_LIGHT_ENABLE 已开启
    When 调用 pointLight 设置 lightSource 和 bloom
    Then RenderContext 写入 LightPosition/LightIntensity/LightColor
    And Bloom 和 shadow 参数同步更新
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（颜色与效果 9 个属性，不含核心显示/高级/事件）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Image render property ImagePaintStyle group and content modifier SVG color filter application"
```

**关键文档：** `design.md`（同目录）
