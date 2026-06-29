# 特性规格

> Func-05-08-01-Feat-01 核心显示属性：固化 src、alt、objectFit、objectRepeat、renderMode、autoResize、sourceSize、orientation、fitOriginalSize、interpolation 十个核心显示属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 核心显示属性 (Core Display Properties) |
| 特性编号 | Func-05-08-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 9/11 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |

---

## 用户故事

### US-1: 设置图片源

**作为** 应用开发者,
**我想要** 通过 src 属性设置 Image 组件显示的图片源,
**以便** 显示来自不同来源（本地文件、资源、网络、内存、Base64 等）的图片。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-1.1 | WHEN 调用 `Image(src: string \\| Resource \\| PixelMap \\| DrawableDescriptor)` 构造函数 THEN 根据 SrcType 自动识别图片来源类型（FILE/ASSET/NETWORK/MEMORY/BASE64/RESOURCE/PIXMAP 等 13 种） |
| AC-1.2 | WHEN src 为 Resource 类型 THEN 从资源文件解析图片（SrcType=RESOURCE），包含 bundleName 和 moduleName |
| AC-1.3 | WHEN src 为 PixelMap 类型 THEN 使用内存中的 PixelMap 直接渲染（SrcType=PIXMAP），无需额外解码 |
| AC-1.4 | WHEN src 变更时 THEN 触发 PROPERTY_UPDATE_NORMAL，重新加载图片 |
| AC-1.5 | WHEN src 为空字符串 THEN ImageSourceInfo 使用默认构造，不触发加载 |

> SrcType 枚举定义：`frameworks/core/components/common/layout/constants.h:459`（UNSUPPORTED=-1, FILE=0, ASSET=1, NETWORK=2, MEMORY=3, BASE64=4, INTERNAL=5, RESOURCE=6, DATA_ABILITY=7, DATA_ABILITY_DECODED=8, RESOURCE_ID=9, PIXMAP=10, ASTC=11, STREAM=12）

### US-2: 设置占位图和错误图

**作为** 应用开发者,
**我想要** 通过 alt 属性设置加载中占位图和加载失败错误图,
**以便** 在图片加载过程中或加载失败时显示替代内容。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-2.1 | WHEN 调用 `.alt(value: string \\| Resource \\| PixelMap \\| ImageAlt)` THEN 设置占位图/错误图资源 |
| AC-2.2 | WHEN 使用 ImageAlt 对象 `{placeholder, error}` THEN placeholder 在主图加载中显示，error 在主图加载失败时显示 |
| AC-2.3 | WHEN 主图加载失败且设置了 alt THEN 自动尝试加载 alt 图片作为替代 |
| AC-2.4 | WHEN alt 图片也加载失败且设置了 altError THEN 尝试加载 altError 图片 |
| AC-2.5 | WHEN alt 为网络 URL 且类型非 IMAGE_ALT_ERROR THEN 网络地址被拒绝（桥接层校验），不加载 |
| AC-2.6 | WHEN alt 属性变更时 THEN 触发 PROPERTY_UPDATE_NORMAL |

> 三级降级链：主图 → alt → altError → altPlaceholder/空白。`image_pattern.cpp:704-720`

### US-3: 设置图片缩放模式

**作为** 应用开发者,
**我想要** 通过 objectFit 属性设置图片在容器中的缩放和定位方式,
**以便** 控制图片的显示效果（填满、居中、裁剪等）。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-3.1 | WHEN 调用 `.objectFit(value: ImageFit)` THEN 设置图片缩放模式，默认为 COVER |
| AC-3.2 | WHEN objectFit 为 FILL(0) THEN 拉伸图片填满容器，不保持宽高比 |
| AC-3.3 | WHEN objectFit 为 CONTAIN(1) THEN 保持宽高比完整显示图片，容器内居中，可能有留白 |
| AC-3.4 | WHEN objectFit 为 COVER(2) THEN 保持宽高比填满容器，居中裁剪溢出部分（默认值） |
| AC-3.5 | WHEN objectFit 为 FITWIDTH(3) THEN 宽度适配容器宽度，高度按比例缩放 |
| AC-3.6 | WHEN objectFit 为 FITHEIGHT(4) THEN 高度适配容器高度，宽度按比例缩放 |
| AC-3.7 | WHEN objectFit 为 NONE(5) THEN 图片使用原始尺寸，不缩放 |
| AC-3.8 | WHEN objectFit 为 SCALE_DOWN(6) THEN 行为同 NONE，但不超过原始图片尺寸（取 min(原始, 容器)） |
| AC-3.9 | WHEN objectFit 为 TOP_LEFT(7)~BOTTOM_END(15) THEN 按 9 宫格方位定位图片（TOP_LEFT/TOP/TOP_END/START/CENTER/END/BOTTOM_START/BOTTOM/BOTTOM_END） |
| AC-3.10 | WHEN objectFit 为 MATRIX(17) THEN 使用 imageMatrix 变换矩阵定位图片 |
| AC-3.11 | WHEN objectFit 变更时 THEN 同时触发 PROPERTY_UPDATE_LAYOUT（布局层）和 PROPERTY_UPDATE_RENDER（渲染层）双重更新 |

> ImageFit 枚举 18 个值（0-17），`constants.h:324-343`。默认 COVER 在 `image_layout_property.cpp:87`

### US-4: 设置图片重复模式

**作为** 应用开发者,
**我想要** 通过 objectRepeat 属性设置图片在容器中的重复方式,
**以便** 实现平铺背景等效果。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-4.1 | WHEN 调用 `.objectRepeat(value: ImageRepeat)` THEN 设置图片重复模式，默认为 NO_REPEAT |
| AC-4.2 | WHEN objectRepeat 为 NO_REPEAT(0) THEN 图片不重复，仅显示一次 |
| AC-4.3 | WHEN objectRepeat 为 REPEAT_X(1) THEN 图片在水平方向重复 |
| AC-4.4 | WHEN objectRepeat 为 REPEAT_Y(2) THEN 图片在垂直方向重复 |
| AC-4.5 | WHEN objectRepeat 为 REPEAT(3) THEN 图片在水平和垂直方向同时重复 |
| AC-4.6 | WHEN objectRepeat 变更时 THEN 触发 PROPERTY_UPDATE_RENDER |
| AC-4.7 | WHEN objectRepeat 为 REPEAT 或 REPEAT_X THEN 水平方向图片尺寸不受容器宽度限制（repeatX=true），`image_pattern.cpp:388-389` |
| AC-4.8 | WHEN objectRepeat 为 REPEAT 或 REPEAT_Y THEN 垂直方向图片尺寸不受容器高度限制（repeatY=true），`image_pattern.cpp:388-389` |

> ImageRepeat 枚举 4 个值（0-3），`constants.h:317-322`

### US-5: 设置渲染模式

**作为** 应用开发者,
**我想要** 通过 renderMode 属性选择图片以原始模式或模板模式渲染,
**以便** SVG 图片可以使用主题颜色进行模板化渲染。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-5.1 | WHEN 调用 `.renderMode(value: ImageRenderMode)` THEN 设置渲染模式，默认为 ORIGINAL |
| AC-5.2 | WHEN renderMode 为 ORIGINAL(0) THEN 图片以原始颜色渲染 |
| AC-5.3 | WHEN renderMode 为 TEMPLATE(1) THEN 图片以模板模式渲染（SVG 可结合 fillColor 使用主题颜色） |
| AC-5.4 | WHEN renderMode 变更时 THEN 触发 PROPERTY_UPDATE_RENDER |

> ImageRenderMode 枚举 2 个值（0-1），`constants.h:399-402`

### US-6: 设置自动调整解码尺寸

**作为** 应用开发者,
**我想要** 通过 autoResize 属性控制图片是否自动调整解码尺寸以匹配组件尺寸,
**以便** 优化内存使用（开启时按组件尺寸解码，关闭时使用原始尺寸解码）。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-6.1 | WHEN 调用 `.autoResize(value: boolean)` THEN 设置是否自动调整解码尺寸 |
| AC-6.2 | WHEN 未显式设置 autoResize 且 API < 11 THEN 默认值为 true（启用功率对齐优化） |
| AC-6.3 | WHEN 未显式设置 autoResize 且 API >= 11 THEN 默认值为 false（不自动调整） |
| AC-6.4 | WHEN 运行在 SceneBoard 窗口 THEN autoResize 默认值为 true（覆盖 API 版本判定），`image_pattern.cpp:2688-2690` |
| AC-6.5 | WHEN autoResize 为 true 且存在 resizable 切片配置或图片有旋转（非 UP 方向） THEN autoResize 实际行为被强制关闭，`image_pattern.cpp:880-893` |
| AC-6.6 | WHEN autoResize 变更时 THEN 触发 PROPERTY_UPDATE_LAYOUT |
| AC-6.7 | WHEN autoResize 为 true 且非 resizable 且无旋转 THEN 使用 SystemProperties::GetImageAutoResizeEnabled() 系统属性决定最终行为 |

> autoResize 默认值双重逻辑是已知兼容性风险，见 design.md ADR-3。`image_pattern.cpp:2679-2693`

### US-7: 设置解码目标尺寸

**作为** 应用开发者,
**我想要** 通过 sourceSize 属性指定图片解码的目标像素尺寸,
**以便** 控制解码后图片的实际像素分辨率。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-7.1 | WHEN 调用 `.sourceSize(value: {width: number, height: number})` THEN 设置解码目标尺寸（单位 px） |
| AC-7.2 | WHEN sourceSize 宽度或高度 < 0 THEN 桥接层拒绝设置（值校验），`arkts_native_image_bridge.cpp:693-700` |
| AC-7.3 | WHEN 未设置 sourceSize THEN 默认为 SizeF(0, 0)，表示不限制解码尺寸 |
| AC-7.4 | WHEN sourceSize 变更时 THEN 触发 PROPERTY_UPDATE_LAYOUT |
| AC-7.5 | WHEN sourceSize 和 autoResize 同时设置 THEN sourceSize 优先级更高，作为显式指定的解码目标 |

> 属性类型为 SizeF（非 ImageSourceSize 结构体），`image_layout_property.h:55`

### US-8: 设置图片旋转方向

**作为** 应用开发者,
**我想要** 通过 orientation 属性设置图片的旋转方向,
**以便** 手动或自动（EXIF）旋转图片显示方向。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-8.1 | WHEN 调用 `.orientation(value: ImageRotateOrientation)` THEN 设置图片旋转方向，默认为 UP |
| AC-8.2 | WHEN orientation 为 AUTO(0) THEN 使用图片 EXIF 信息中记录的旋转方向 |
| AC-8.3 | WHEN orientation 为 UP(1) THEN 不旋转，使用原始方向（默认值） |
| AC-8.4 | WHEN orientation 为 RIGHT(2)/DOWN(3)/LEFT(4) THEN 分别旋转 90°/180°/270° |
| AC-8.5 | WHEN orientation 为 UP_MIRRORED(5)~LEFT_MIRRORED(8) THEN 应用镜像+旋转组合变换 |
| AC-8.6 | WHEN 图片为多帧图片（GIF/WebP） THEN 强制使用 UP 方向，忽略用户设置，`image_pattern.cpp:680-701` |
| AC-8.7 | WHEN orientation 变更时 THEN 触发 PROPERTY_UPDATE_MEASURE（需重新测量布局） |

> ImageRotateOrientation 枚举 9 个值（0-8），`constants.h:381-391`

### US-9: 适应原始图片尺寸

**作为** 应用开发者,
**我想要** 通过 fitOriginalSize 属性让 Image 组件尺寸自适应图片原始尺寸,
**以便** 在未设置显式宽高时按图片实际大小显示。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-9.1 | WHEN 调用 `.fitOriginalSize(value: boolean)` THEN 设置是否适应原始尺寸，默认为 false |
| AC-9.2 | WHEN fitOriginalSize 为 true 且未设置显式宽高（selfIdealSize.IsNull()） THEN 组件尺寸使用图片原始尺寸 |
| AC-9.3 | WHEN fitOriginalSize 为 true 但已设置显式宽高 THEN 显式宽高优先，fitOriginalSize 不生效 |
| AC-9.4 | WHEN fitOriginalSize 变更时 THEN 触发 PROPERTY_UPDATE_BY_CHILD_REQUEST（唯一使用此标志的 Image 属性） |

> `image_layout_algorithm.cpp:49-104`

### US-10: 设置插值质量

**作为** 应用开发者,
**我想要** 通过 interpolation 属性设置图片缩放时的插值质量,
**以便** 在图片质量与性能之间做取舍。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-10.1 | WHEN 调用 `.interpolation(value: ImageInterpolation)` THEN 设置插值质量 |
| AC-10.2 | WHEN interpolation 为 NONE(0) THEN 不使用插值（最快，质量最低） |
| AC-10.3 | WHEN interpolation 为 LOW(1) THEN 使用低质量插值 |
| AC-10.4 | WHEN interpolation 为 MEDIUM(2) THEN 使用中等质量插值 |
| AC-10.5 | WHEN interpolation 为 HIGH(3) THEN 使用高质量插值（最慢，质量最高） |
| AC-10.6 | WHEN 未显式设置 interpolation 且 API < 11（非 SceneBoard） THEN 默认为 NONE |
| AC-10.7 | WHEN 未显式设置 interpolation 且 API >= 11（非 SceneBoard） THEN 默认为 LOW |
| AC-10.8 | WHEN 运行在 SceneBoard 窗口 THEN interpolation 默认为 NONE |
| AC-10.9 | WHEN interpolation 变更时 THEN 触发 PROPERTY_UPDATE_RENDER |

> interpolation 默认值存在不一致（Pattern 成员初始值 LOW vs getter 默认 NONE），见 design.md 风险表。`image_pattern.h:382` vs `image_model_ng.cpp:977`

---

## 验收追溯

| AC ID | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 | R-4 | — | 代码审查 | `constants.h:459` |
| AC-1.2 | R-4 | — | 代码审查 | `image_source_info.h:35` |
| AC-1.3 | R-4 | — | 代码审查 | `image_model_ng.cpp:159` |
| AC-1.4 | R-5 | — | 代码审查 | `image_layout_property.h:51` |
| AC-2.1~2.6 | R-6, R-16 | — | 代码审查 | `image_pattern.cpp:704-720` |
| AC-3.1~3.11 | R-7, R-8 | — | 单元测试 | `image_layout_algorithm.cpp` |
| AC-4.1~4.8 | R-9 | — | 代码审查 | `image_pattern.cpp:388-389` |
| AC-5.1~5.4 | R-10 | — | 代码审查 | `image_render_property.h:65` |
| AC-6.1~6.7 | R-11, R-17 | — | 代码审查 | `image_pattern.cpp:2679-2693` |
| AC-7.1~7.5 | R-12 | — | 代码审查 | `image_layout_property.h:55` |
| AC-8.1~8.7 | R-13, R-18 | — | 代码审查 | `image_pattern.cpp:680-701` |
| AC-9.1~9.4 | R-14 | — | 单元测试 | `image_layout_algorithm.cpp:49-104` |
| AC-10.1~10.9 | R-15, R-19 | — | 代码审查 | `image_pattern.h:382`, `image_pattern.cpp:2679-2693` |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | Image 组件属性分为三层存储：LayoutProperty（触发 MEASURE/LAYOUT）、RenderProperty（触发 RENDER）、Pattern 成员（无 dirty flag），属性变更的影响范围由存储层决定 | — | — |
| R-2 | 行为 | — | 图片加载管线（ImageLoadingContext）是 Image 组件的上游依赖，管线行为变更可能影响 Image 组件表现（跨功能域依赖，Func-04-01-01） | — | — |
| R-3 | 行为 | — | objectFit 同时影响布局计算和渲染绘制，因此同时写入 LayoutProperty 和 RenderProperty，触发双重更新 | — | — |
| R-4 | 行为 | — | Image(src) 构造函数通过 ImageSourceInfo 包装图片源信息，自动识别 SrcType（13 种类型），传递给 ImageLoadingContext 进行加载 | — | — |
| R-5 | 行为 | — | src 属性存储在 LayoutProperty 中，变更触发 PROPERTY_UPDATE_NORMAL，重新触发加载流程 | — | — |
| R-6 | 行为 | — | alt 图片采用三级降级链：主图失败 → alt → altError → altPlaceholder/空白，网络 URL 仅允许用于 error 类型 | — | — |
| R-7 | 行为 | — | objectFit COVER(2) 为默认值，保持宽高比填满容器，居中裁剪溢出部分 | — | — |
| R-8 | 行为 | — | objectFit 18 种枚举值中，9 宫格定位（TOP_LEFT=7 到 BOTTOM_END=15）通过改变图片在容器中的对齐位置实现定位 | — | — |
| R-9 | 行为 | — | objectRepeat 影响渲染层绘制逻辑：REPEAT_X 使水平方向平铺不受容器宽度限制，REPEAT_Y 使垂直方向平铺不受容器高度限制 | — | — |
| R-10 | 行为 | — | renderMode TEMPLATE(1) 模式下 SVG 图片可结合 fillColor 实现主题化渲染 | — | — |
| R-11 | 行为 | — | autoResize 默认值取决于 API 版本和运行环境：API<11 为 true，API>=11 为 false，SceneBoard 强制 true；resizable 切片或旋转会强制关闭 autoResize | — | — |
| R-12 | 行为 | — | sourceSize 以 px 为单位指定解码目标尺寸，桥接层校验 width/height >= 0，为 0 表示不限制 | — | — |
| R-13 | 行为 | — | orientation AUTO(0) 使用 EXIF 方向，多帧图片强制 UP(1) 忽略用户设置 | — | — |
| R-14 | 行为 | — | fitOriginalSize 为 true 且无显式宽高时，组件尺寸使用图片原始像素尺寸 | — | — |
| R-15 | 行为 | — | interpolation 默认值存在 API 版本差异（API<11=NONE，API>=11=LOW），SceneBoard 统一为 NONE | — | — |
| R-16 | 异常 | — | alt 图片不接受网络 URL（error 类型除外），桥接层静默拒绝不抛异常 | — | — |
| R-17 | 异常 | — | autoResize 在 resizable 切片配置存在或图片有旋转时被强制关闭，不受用户设置值影响 | — | — |
| R-18 | 异常 | — | 多帧图片（GIF/WebP）的 orientation 被强制为 UP，不应用用户设置的旋转方向 | — | — |
| R-19 | 异常 | — | interpolation Pattern 成员初始值（LOW）与 getter 默认值（NONE）不一致，实际渲染使用 interpolationDefault_（取决于 API 版本） | — | — |
| R-20 | 恢复 | — | — | — | — |
| R-21 | 恢复 | — | — | — | — |
| R-22 | 恢复 | — | — | — | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5 (src) | XTS + 代码审查 | 各 SrcType 正确识别和加载 |
| VM-2 | AC-2.1~2.6 (alt) | XTS | 降级链完整性和网络 URL 拒绝 |
| VM-3 | AC-3.1~3.11 (objectFit) | 单元测试 | 18 种 ImageFit 的布局计算结果 |
| VM-4 | AC-4.1~4.8 (objectRepeat) | XTS | 4 种重复模式的绘制区域 |
| VM-5 | AC-5.1~5.4 (renderMode) | XTS | TEMPLATE 模式 SVG 渲染 |
| VM-6 | AC-6.1~6.7 (autoResize) | XTS + 代码审查 | API 版本默认值差异和强制关闭逻辑 |
| VM-7 | AC-7.1~7.5 (sourceSize) | XTS | 解码尺寸控制和边界校验 |
| VM-8 | AC-8.1~8.7 (orientation) | XTS | EXIF 自动识别和多帧图片豁免 |
| VM-9 | AC-9.1~9.4 (fitOriginalSize) | 单元测试 | 布局算法中原始尺寸适配逻辑 |
| VM-10 | AC-10.1~10.9 (interpolation) | XTS + 代码审查 | API 版本默认值和实际使用值 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `Image(src)` 构造函数 | Public | 设置图片源（支持 string/Resource/PixelMap/DrawableDescriptor） | AC-1.1~1.3 |
| `alt(value)` | Public | 设置占位图/错误图 | AC-2.1~2.6 |
| `objectFit(value: ImageFit)` | Public | 设置图片缩放模式（默认 COVER） | AC-3.1~3.11 |
| `objectRepeat(value: ImageRepeat)` | Public | 设置图片重复模式（默认 NO_REPEAT） | AC-4.1~4.8 |
| `renderMode(value: ImageRenderMode)` | Public | 设置渲染模式（默认 ORIGINAL） | AC-5.1~5.4 |
| `autoResize(value: boolean)` | Public | 设置自动调整解码尺寸 | AC-6.1~6.7 |
| `sourceSize(value: {width, height})` | Public | 设置解码目标尺寸（px） | AC-7.1~7.5 |
| `orientation(value: ImageRotateOrientation)` | Public | 设置图片旋转方向（默认 UP） | AC-8.1~8.7 |
| `fitOriginalSize(value: boolean)` | Public | 设置适应原始图片尺寸（默认 false） | AC-9.1~9.4 |
| `interpolation(value: ImageInterpolation)` | Public | 设置插值质量 | AC-10.1~10.9 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 是 — autoResize 默认值在 API 11 发生变更（true → false）；interpolation 默认值在 API 11 发生变更（NONE → LOW）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** @since 7 标注基础属性，API 9/11 行为变更已在源码中通过 GreatOrEqualTargetAPIVersion(VERSION_ELEVEN) 守卫

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 属性三层存储 | src/alt/objectFit/autoResize/sourceSize/fitOriginalSize/orientation 存 LayoutProperty；objectRepeat/renderMode/interpolation 存 RenderProperty；变更触发不同的 dirty flag | AC-1~10 |
| objectFit 双写 | objectFit 同时写入 LayoutProperty 和 RenderProperty，触发 LAYOUT + RENDER 双重更新 | AC-3.11 |
| 跨功能域依赖 | 图片加载管线（Func-04-01-01）是 Image 组件的上游，管线行为变更可能影响 Image 表现 | AC-1.1~1.5 |
| fitOriginalSize 特殊更新标志 | 使用 PROPERTY_UPDATE_BY_CHILD_REQUEST，与其他属性的 MEASURE/LAYOUT/RENDER 不同 | AC-9.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | autoResize 功率对齐减少内存占用 | 代码审查 | `image_pattern.cpp:880-893` |
| 内存 | sourceSize 和 autoResize 共同控制解码尺寸，避免过大图片占用内存 | 代码审查 | `image_model_ng.cpp:440` |
| 安全 | alt 不接受网络 URL（error 除外），防止网络图片作为占位图 | 代码审查 | `arkts_native_image_bridge.cpp:791` |

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
| 无障碍 | 是 | Image 组件的 alt 可作为无障碍描述的一部分 | 桥接层处理 |
| 大字体 | 否 | 图片尺寸不受大字体影响 | — |
| 深色模式 | 部分 | renderMode TEMPLATE 可配合深色主题色 | AC-5.3 |
| 多窗口/分屏 | 否 | 无特殊处理 | — |
| 多用户 | 否 | 无特殊处理 | — |
| 版本升级 | 是 | autoResize/interpolation 默认值在 API 11 变更 | AC-6.2~6.4, AC-10.6~10.8 |
| 生态兼容 | 是 | objectFit 18 种枚举含非标准值（9 宫格定位），开发者需注意 | AC-3.9 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 核心显示属性

  Scenario: 设置 objectFit 为 COVER（默认值）
    Given 一个 Image 组件，未显式设置 objectFit
    And 图片原始尺寸为 200x100，容器尺寸为 100x100
    When 触发布局计算
    Then 图片保持宽高比缩放至 200x200（填满容器宽度）
    And 居中裁剪，上下各裁掉 50px

  Scenario: 设置 objectFit 为 CONTAIN
    Given 一个 Image 组件，objectFit 设置为 CONTAIN
    And 图片原始尺寸为 200x100，容器尺寸为 100x100
    When 触发布局计算
    Then 图片保持宽高比缩放至 100x50（适配容器宽度）
    And 居中显示，上下各有 25px 留白

  Scenario: autoResize API 版本默认值差异
    Given 一个 Image 组件，未显式设置 autoResize
    When 运行环境 API 版本 < 11 且非 SceneBoard
    Then autoResizeDefault_ 为 true（启用功率对齐优化）
    When 运行环境 API 版本 >= 11 且非 SceneBoard
    Then autoResizeDefault_ 为 false（不自动调整）

  Scenario: orientation AUTO 使用 EXIF 方向
    Given 一个 Image 组件，orientation 设置为 AUTO
    And 图片 EXIF 信息记录旋转方向为 RIGHT（90° CW）
    When 图片加载完成
    Then 图片按 90° 顺时针旋转显示

  Scenario: alt 三级降级链
    Given 一个 Image 组件，src 指向不存在的资源
    And alt 设置了占位图 A
    And altError 设置了错误图 E
    When 主图加载失败
    Then 尝试加载占位图 A
    When 占位图 A 也加载失败
    Then 尝试加载错误图 E
    When 错误图 E 也加载失败
    Then 显示空白或 altPlaceholder
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（核心显示属性 10 个，不含颜色效果/高级/事件）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Image component LayoutProperty/RenderProperty three-layer property storage and objectFit layout algorithm"
  - repo: "openharmony/arkui_ace_engine"
    query: "ImageLoadingContext state machine and image loading pipeline (Func-04-01-01)"
```

**关键文档：** `design.md`（同目录）、`specs/04-common-capability/01-image-loading/01-image-loading-mechanism/design.md`（图片加载管线）
