# 特性规格

> Func-05-08-01-Feat-02 颜色与效果：固化 fillColor、colorFilter、dynamicRangeMode、hdrBrightness、imageMatrix、edgeAntialiasing、antialiased、contentTransition 八个颜色效果属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 颜色与效果 (Color and Effects) |
| 特性编号 | Func-05-08-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 9 起支持，API 12 有增强 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |

---

## 用户故事

### US-1: 设置 SVG 填充颜色

**作为** 应用开发者,
**我想要** 通过 fillColor 属性设置 SVG 图片的填充颜色,
**以便** 动态改变 SVG 图标的颜色以适配主题或状态。

**验收标准：**

- **AC-1.1:** WHEN 调用 `.fillColor(value: ResourceColor)` THEN 设置 SVG 填充颜色
- **AC-1.2:** WHEN fillColor 设置后 THEN 同时更新 SvgFillColor 渲染属性和 ForegroundColor 渲染上下文，`image_model_ng.cpp:447-451`
- **AC-1.3:** WHEN fillColor 变更时 THEN 触发 PROPERTY_UPDATE_RENDER
- **AC-1.4:** WHEN fillColor 应用到 SVG THEN 通过 svgCanvas->SetFillColor() 生效，`image_content_modifier.cpp:86-103`
- **AC-1.5:** WHEN fillColor 变更且图片为 HDR 内容 THEN 同步更新 HDR headroom，`image_content_modifier.cpp:67-84`

### US-2: 设置颜色滤镜

**作为** 应用开发者,
**我想要** 通过 colorFilter 属性设置颜色滤镜矩阵或 DrawingColorFilter,
**以便** 对图片应用自定义颜色变换效果。

**验收标准：**

- **AC-2.1:** WHEN 调用 `.colorFilter(value: ColorFilter)` 传入 4x5 矩阵数组 THEN 设置颜色滤镜矩阵（20 个 float 元素的 identity 矩阵为默认）
- **AC-2.2:** WHEN 调用 colorFilter 传入 DrawingColorFilter 对象 THEN 设置 Drawing 渲染滤镜
- **AC-2.3:** WHEN 设置 ColorFilter 矩阵 THEN 自动重置 DrawingColorFilter（互斥），`image_model_ng.cpp:497-501`
- **AC-2.4:** WHEN 设置 DrawingColorFilter THEN 自动重置 ColorFilter 矩阵（互斥），`image_model_ng.cpp:503-507`
- **AC-2.5:** WHEN 未设置 colorFilter THEN 使用默认 identity 矩阵 `{1,0,0,0,0, 0,1,0,0,0, 0,0,1,0,0, 0,0,0,1,0}`，`image_model_ng.cpp:40`
- **AC-2.6:** WHEN colorFilter 变更时 THEN 触发 PROPERTY_UPDATE_RENDER
- **AC-2.7:** WHEN colorFilter 应用到 SVG 且 API >= 12 THEN 通过 svgCanvas 应用颜色滤镜，`image_content_modifier.cpp:96-101`

> ColorFilter 双类型（矩阵 vs DrawingColorFilter）互斥设计，见 design.md ADR 部分。

### US-3: 设置动态范围模式

**作为** 应用开发者,
**我想要** 通过 dynamicRangeMode 属性控制 HDR 图片的渲染方式,
**以便** 在支持 HDR 的设备上获得更好的视觉效果。

**验收标准：**

- **AC-3.1:** WHEN 调用 `.dynamicRangeMode(value: DynamicRangeMode)` THEN 设置动态范围模式，默认为 STANDARD
- **AC-3.2:** WHEN dynamicRangeMode 为 HIGH(0) THEN 使用 HDR 渲染（需要设备支持）
- **AC-3.3:** WHEN dynamicRangeMode 为 CONSTRAINT(1) THEN 使用受限 HDR 渲染
- **AC-3.4:** WHEN dynamicRangeMode 为 STANDARD(2) THEN 使用标准 SDR 渲染（默认值）
- **AC-3.5:** WHEN dynamicRangeMode 变更时 THEN 触发 PROPERTY_UPDATE_RENDER
- **AC-3.6:** WHEN 同时设置了 hdrBrightness 且图片为 HDR PixelMap THEN dynamicRangeMode 被强制为 HIGH，`image_paint_method.cpp:134-138`

> DynamicRangeMode 枚举 3 个值，`constants.h:368-372`

### US-4: 设置 HDR 亮度

**作为** 应用开发者,
**我想要** 通过 hdrBrightness 属性调整 HDR 图片的亮度,
**以便** 在 HDR 显示模式下精细控制图片亮度表现。

**验收标准：**

- **AC-4.1:** WHEN 调用 `.hdrBrightness(value: number)` THEN 设置 HDR 亮度值，默认为 1.0
- **AC-4.2:** WHEN hdrBrightness 设置且图片为 HDR PixelMap THEN 设置 renderContext 的 ImageHDRBrightness 并启用 ImageHDRPresent，`image_paint_method.cpp:134-138`
- **AC-4.3:** WHEN hdrBrightness 设置且图片为 HDR THEN 强制 dynamicRangeMode 为 HIGH
- **AC-4.4:** WHEN hdrBrightness 变更时 THEN 触发 PROPERTY_UPDATE_RENDER

> DEFAULT_HDR_BRIGHTNESS = 1.0f，`image_render_property.h:32`

### US-5: 设置变换矩阵

**作为** 应用开发者,
**我想要** 通过 imageMatrix 属性设置图片的变换矩阵,
**以便** 对图片应用自定义的仿射或透视变换。

**验收标准：**

- **AC-5.1:** WHEN 调用 `.imageMatrix(value: Matrix4Transit)` THEN 设置变换矩阵
- **AC-5.2:** WHEN imageMatrix 仅在 objectFit 为 MATRIX(17) 时生效，`image_paint_method.cpp:142-156`
- **AC-5.3:** WHEN objectFit 非 MATRIX 且设置了 imageMatrix THEN imageMatrix 被忽略
- **AC-5.4:** WHEN 未设置 imageMatrix 且 objectFit 为 MATRIX THEN 使用 identity 矩阵作为默认值
- **AC-5.5:** WHEN imageMatrix 变更时 THEN 触发 PROPERTY_UPDATE_RENDER

> imageMatrix 存储在 RenderProperty 但不在 ImagePaintStyle 组内，独立存储，`image_render_property.h:87`

### US-6: 设置边缘抗锯齿

**作为** 应用开发者,
**我想要** 通过 edgeAntialiasing 属性设置图片边缘抗锯齿强度,
**以便** 改善图片边缘的渲染质量。

**验收标准：**

- **AC-6.1:** WHEN 调用 `.edgeAntialiasing(value: number)` THEN 设置边缘抗锯齿值（float 类型内部存储为 SmoothEdge）
- **AC-6.2:** WHEN 未显式设置 THEN 默认为 0.0f（无抗锯齿），`image_paint_method.cpp:113`
- **AC-6.3:** WHEN 图片为 SVG THEN 同时应用 smoothEdge 到 svgCanvas，`image_content_modifier.cpp:94`
- **AC-6.4:** WHEN SVG 场景下 smoothEdge 值 THEN 取 max(theme默认值, renderProp值)，`image_pattern.cpp:895-900`
- **AC-6.5:** WHEN edgeAntialiasing 变更时 THEN 触发 PROPERTY_UPDATE_RENDER

### US-7: 设置抗锯齿

**作为** 应用开发者,
**我想要** 通过 antialiased 属性开启或关闭图片渲染的抗锯齿,
**以便** 控制图片缩放时的边缘平滑处理。

**验收标准：**

- **AC-7.1:** WHEN 调用 `.antialiased(value: boolean)` THEN 设置抗锯齿开关，默认为 false
- **AC-7.2:** WHEN antialiased 为 true THEN 图片渲染时启用抗锯齿
- **AC-7.3:** WHEN antialiased 变更时 THEN 触发 PROPERTY_UPDATE_RENDER

> `image_paint_method.cpp:118`：`config.antiAlias_ = renderProps->GetAntiAliasValue(false)`

### US-8: 设置内容过渡效果

**作为** 应用开发者,
**我想要** 通过 contentTransition 属性设置图片源切换时的过渡动画,
**以便** 在更换图片时提供平滑的视觉效果。

**验收标准：**

- **AC-8.1:** WHEN 调用 `.contentTransition(value: ContentTransitionEffect)` THEN 设置内容过渡类型
- **AC-8.2:** WHEN contentTransition 为 IDENTITY(0) THEN 无过渡效果（默认）
- **AC-8.3:** WHEN contentTransition 为 OPACITY(1) THEN 图片切换时使用透明度淡入淡出过渡
- **AC-8.4:** WHEN 图片源变更且 contentTransition 非 IDENTITY THEN ImagePaintMethod 根据源变更判断是否需要过渡动画，`image_paint_method.cpp:159-180`
- **AC-8.5:** WHEN 图片为 SVG 或动画图片 THEN 跳过内容过渡动画
- **AC-8.6:** WHEN contentTransition 变更时 THEN 触发 PROPERTY_UPDATE_RENDER

> ContentTransitionType 枚举 2 个值（IDENTITY=0, OPACITY=1），`constants.h:977-980`

---

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.5 | FR-1 | — | 代码审查 | `image_model_ng.cpp:447-451` |
| AC-2.1~2.7 | FR-2, EX-1 | — | 代码审查 | `image_model_ng.cpp:497-507` |
| AC-3.1~3.6 | FR-3, EX-2 | — | 代码审查 | `image_paint_method.cpp:134-138` |
| AC-4.1~4.4 | FR-4 | — | 代码审查 | `image_render_property.h:32` |
| AC-5.1~5.5 | FR-5, EX-3 | — | 代码审查 | `image_paint_method.cpp:142-156` |
| AC-6.1~6.5 | FR-6 | — | 代码审查 | `image_content_modifier.cpp:94` |
| AC-7.1~7.3 | FR-7 | — | 代码审查 | `image_paint_method.cpp:118` |
| AC-8.1~8.6 | FR-8 | — | 代码审查 | `image_paint_method.cpp:159-180` |

## 业务规则

| 规则 ID | 规则描述 |
|---------|----------|
| BR-1 | 颜色与效果属性均存储在 RenderProperty 中（触发 PROPERTY_UPDATE_RENDER），不触发布局重测 |
| BR-2 | fillColor 同时更新 SvgFillColor 和 ForegroundColor 两个目标，确保 SVG 和通用渲染管道颜色一致 |
| BR-3 | colorFilter 的两种类型（矩阵 vs DrawingColorFilter）互斥，设置一种自动重置另一种 |

## 功能规则

| 规则 ID | 规则描述 |
|---------|----------|
| FR-1 | fillColor 设置 SVG 填充颜色，通过 svgCanvas->SetFillColor() 应用到 SVG 渲染，同时同步 HDR headroom |
| FR-2 | colorFilter 支持两种互斥类型：4x5 矩阵数组（ColorFilter）和 DrawingColorFilter 对象；默认为 identity 矩阵 |
| FR-3 | dynamicRangeMode 控制HDR渲染模式，STANDARD(2) 为默认；被 hdrBrightness + HDR PixelMap 强制覆盖为 HIGH |
| FR-4 | hdrBrightness 默认 1.0，仅对 HDR PixelMap 生效，同时强制 dynamicRangeMode 为 HIGH |
| FR-5 | imageMatrix 仅在 objectFit=MATRIX(17) 时生效，未设置时使用 identity 矩阵 |
| FR-6 | edgeAntialiasing 内部存储为 SmoothEdge（float），SVG 场景取 max(theme默认值, 用户设置值) |
| FR-7 | antialiased 控制图片渲染抗锯齿，默认 false |
| FR-8 | contentTransition 支持透明度淡入淡出（OPACITY），SVG 和动画图片跳过过渡 |

## 异常/豁免规则

| 规则 ID | 规则描述 |
|---------|----------|
| EX-1 | colorFilter 矩阵和 DrawingColorFilter 互斥，后设置的覆盖先设置的 |
| EX-2 | dynamicRangeMode 可被 hdrBrightness 强制覆盖为 HIGH，不受用户设置值影响 |
| EX-3 | imageMatrix 在 objectFit 非 MATRIX 时被忽略，不产生渲染效果 |

## 恢复契约

| 契约 ID | 契约描述 |
|---------|----------|
| RC-1 | fillColor/colorFilter/dynamicRangeMode/hdrBrightness/imageMatrix/edgeAntialiasing/antialiased/contentTransition 变更时仅触发 RENDER，不重新加载图片 |
| RC-2 | colorFilter 互斥重置可通过重新设置被覆盖的类型来恢复 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5 (fillColor) | XTS | SVG 颜色填充和 HDR headroom 同步 |
| VM-2 | AC-2.1~2.7 (colorFilter) | XTS | 矩阵/DrawingColorFilter 互斥和默认 identity |
| VM-3 | AC-3.1~3.6 (dynamicRangeMode) | XTS | HDR 模式和 hdrBrightness 强制覆盖 |
| VM-4 | AC-4.1~4.4 (hdrBrightness) | XTS | HDR 亮度设置和强制 HIGH 模式 |
| VM-5 | AC-5.1~5.5 (imageMatrix) | XTS | MATRIX 模式生效和非 MATRIX 忽略 |
| VM-6 | AC-6.1~6.5 (edgeAntialiasing) | XTS | SVG 场景 max 取值逻辑 |
| VM-7 | AC-7.1~7.3 (antialiased) | XTS | 抗锯齿开关 |
| VM-8 | AC-8.1~8.6 (contentTransition) | XTS | OPACITY 过渡和 SVG/动画豁免 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `fillColor(value: ResourceColor)` | Public | 设置 SVG 填充颜色 | AC-1.1~1.5 |
| `colorFilter(value: ColorFilter)` | Public | 设置颜色滤镜矩阵（4x5 矩阵或 DrawingColorFilter） | AC-2.1~2.7 |
| `dynamicRangeMode(value: DynamicRangeMode)` | Public | 设置动态范围模式（默认 STANDARD） | AC-3.1~3.6 |
| `hdrBrightness(value: number)` | Public | 设置 HDR 亮度（默认 1.0） | AC-4.1~4.4 |
| `imageMatrix(value: Matrix4Transit)` | Public | 设置变换矩阵（仅 MATRIX 模式生效） | AC-5.1~5.5 |
| `edgeAntialiasing(value: number)` | Public | 设置边缘抗锯齿强度 | AC-6.1~6.5 |
| `antialiased(value: boolean)` | Public | 设置抗锯齿开关（默认 false） | AC-7.1~7.3 |
| `contentTransition(value: ContentTransitionEffect)` | Public | 设置内容过渡效果（默认 IDENTITY） | AC-8.1~8.6 |

### 变更/废弃 API

无。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** colorFilter 的 SVG 应用仅在 API >= 12 生效，`image_content_modifier.cpp:96-101`

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| RenderProperty 统一存储 | 8 个属性均存储在 ImageRenderProperty 的 ImagePaintStyle 组内（imageMatrix 除外），仅触发 RENDER | AC-1~8 |
| imageMatrix 独立存储 | imageMatrix 在 RenderProperty 但不在 ImagePaintStyle 组内，独立管理 | AC-5 |
| colorFilter 双类型互斥 | 矩阵和 DrawingColorFilter 通过桥接层互斥管理 | AC-2.3~2.4 |
| HDR 联动 | hdrBrightness 和 dynamicRangeMode 存在强制覆盖关系 | AC-3.6, AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 颜色效果仅触发 RENDER 不触发 MEASURE，最小化更新范围 | 代码审查 | PROPERTY_UPDATE_RENDER 标志 |
| 内存 | colorFilter 矩阵为 20 float（80 字节），DrawingColorFilter 为 RefPtr 智能指针 | 代码审查 | `image_render_property.h:40-41` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 颜色效果不影响无障碍 | — |
| 大字体 | 否 | 颜色效果不受大字体影响 | — |
| 深色模式 | 是 | fillColor 可用于适配深色主题 SVG 颜色 | AC-1 |
| 多窗口/分屏 | 否 | 无特殊处理 | — |
| 多用户 | 否 | 无特殊处理 | — |
| 版本升级 | 是 | colorFilter SVG 应用仅 API >= 12 | AC-2.7 |
| 生态兼容 | 否 | 无特殊兼容性问题 | — |

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
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（颜色与效果 8 个属性，不含核心显示/高级/事件）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Image render property ImagePaintStyle group and content modifier SVG color filter application"
```

**关键文档：** `design.md`（同目录）
