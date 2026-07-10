# 特性规格

> Func-05-08-01-Feat-01 核心显示属性：固化 src/ImageContent/reloadKey、alt、objectFit、objectRepeat、renderMode、autoResize、sourceSize、orientation、fitOriginalSize、interpolation 十个核心显示属性及构造重载的行为规格。

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

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 Image 构造重载 | SDK 动态版包含 API 12 `ImageContent`/`ImageAIOptions` 和 API 26 `reloadKey` 重载；静态版 API 23/26 也有对应构造和 `setImageOptions`。 |
| MODIFIED | 补齐多范式 API 覆盖 | 对齐动态 ArkTS、静态 ArkTS、C API 的公开入口和版本差异。 |
| MODIFIED | 修正默认值来源 | `autoResize` 和 `interpolation` 默认值以 Pattern 初始化和 Reset 路径为准，保留 API 版本/SceneBoard 差异。 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `arkui-specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/image.d.ts` | 已核对：Image 构造、核心属性声明 |
| Static SDK | `interface/sdk-js/api/arkui/component/image.static.d.ets` | 已核对：静态 Image 构造、`setImageOptions`、核心属性声明 |
| C API | `interfaces/native/native_node.h` | 已核对：`NODE_IMAGE_SRC`、`NODE_IMAGE_OBJECT_FIT` 等属性枚举 |

---

## 用户故事

### US-1: 设置图片源

**作为** 应用开发者,
**我想要** 通过 src 属性设置 Image 组件显示的图片源,
**以便** 显示来自不同来源（本地文件、资源、网络、内存、Base64 等）的图片。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Image(src: PixelMap \| ResourceStr \| DrawableDescriptor)` 构造函数 THEN 根据 SrcType 自动识别图片来源类型（FILE/ASSET/NETWORK/MEMORY/BASE64/RESOURCE/PIXMAP 等 13 种） | 正常 |
| AC-1.2 | WHEN src 为 Resource 类型 THEN 从资源文件解析图片（SrcType=RESOURCE），包含 bundleName 和 moduleName | 正常 |
| AC-1.3 | WHEN src 为 PixelMap 类型 THEN 使用内存中的 PixelMap 直接渲染（SrcType=PIXMAP），无需额外解码 | 正常 |
| AC-1.4 | WHEN src 变更时 THEN 触发 PROPERTY_UPDATE_NORMAL，重新加载图片 | 正常 |
| AC-1.5 | WHEN src 为空字符串 THEN ImageSourceInfo 使用默认构造，不触发加载 | 异常 |
| AC-1.6 | WHEN 构造参数使用 `ImageContent.Empty` THEN 前端调用 ResetImage，写入带 `isFromReset=true` 的空 ImageSourceInfo 并清空图片与 alt 状态 | 正常 |
| AC-1.7 | WHEN 构造参数携带 `reloadKey` THEN reloadKey 写入 ImageSourceInfo，后续 `IsReloadKeyChanged` 可参与重载判定 | 正常 |
| AC-1.8 | WHEN PixelMap 对象内容变化但对象引用未变化 THEN Image 组件不会把像素内容变更识别为新的数据源变更 | 边界 |

> SrcType 枚举定义：`frameworks/core/components/common/layout/constants.h:459`（UNSUPPORTED=-1, FILE=0, ASSET=1, NETWORK=2, MEMORY=3, BASE64=4, INTERNAL=5, RESOURCE=6, DATA_ABILITY=7, DATA_ABILITY_DECODED=8, RESOURCE_ID=9, PIXMAP=10, ASTC=11, STREAM=12）

> 构造重载声明：动态版 `interface/sdk-js/api/@internal/component/ets/image.d.ts:549`, `image.d.ts:570`, `image.d.ts:585`, `image.d.ts:605`, `image.d.ts:619`；静态版 `interface/sdk-js/api/arkui/component/image.static.d.ets:1161`, `image.static.d.ets:1179`, `image.static.d.ets:1197`, `image.static.d.ets:1215`。reloadKey 解析：`frameworks/bridge/declarative_frontend/jsview/js_image.cpp:460-473`，Model 写入：`frameworks/core/components_ng/pattern/image/image_model_ng.cpp:105-109`, `image_model_ng.cpp:172-180`。

### US-2: 设置占位图和错误图

**作为** 应用开发者,
**我想要** 通过 alt 属性设置加载中占位图和加载失败错误图,
**以便** 在图片加载过程中或加载失败时显示替代内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.alt(value: string \\| Resource \\| PixelMap \\| ImageAlt)` THEN 设置占位图/错误图资源 |
| AC-2.2 | WHEN 使用 ImageAlt 对象 `{placeholder, error}` THEN placeholder 在主图加载中显示，error 在主图加载失败时显示 | 异常 |
| AC-2.3 | WHEN 主图加载失败且设置了 alt THEN 自动尝试加载 alt 图片作为替代 | 异常 |
| AC-2.4 | WHEN alt 图片也加载失败且设置了 altError THEN 尝试加载 altError 图片 | 异常 |
| AC-2.5 | WHEN alt 为网络 URL 且类型非 IMAGE_ALT_ERROR THEN 网络地址被拒绝（桥接层校验），不加载 | 正常 |
| AC-2.6 | WHEN alt 属性变更时 THEN 触发 PROPERTY_UPDATE_NORMAL | 正常 |
| AC-2.7 | WHEN 动态版 API 22 或静态版 API 23 使用 `ImageAlt` THEN placeholder 写入 `AltPlaceholder`，error 写入 `AltError`，普通 ResourceStr/PixelMap 写入 `Alt` | 正常 |

> 三级降级链：主图 → alt → altError → altPlaceholder/空白。`frameworks/core/components_ng/pattern/image/image_model_ng.cpp:1380-1437`、`frameworks/bridge/declarative_frontend/jsview/js_image.cpp:1390-1451`

### US-3: 设置图片缩放模式

**作为** 应用开发者,
**我想要** 通过 objectFit 属性设置图片在容器中的缩放和定位方式,
**以便** 控制图片的显示效果（填满、居中、裁剪等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.objectFit(value: ImageFit)` THEN 设置图片缩放模式，默认为 COVER | 正常 |
| AC-3.2 | WHEN objectFit 为 FILL(0) THEN 拉伸图片填满容器，不保持宽高比 | 正常 |
| AC-3.3 | WHEN objectFit 为 CONTAIN(1) THEN 保持宽高比完整显示图片，容器内居中，可能有留白 | 正常 |
| AC-3.4 | WHEN objectFit 为 COVER(2) THEN 保持宽高比填满容器，居中裁剪溢出部分（默认值） | 边界 |
| AC-3.5 | WHEN objectFit 为 FITWIDTH(3) THEN 宽度适配容器宽度，高度按比例缩放 | 正常 |
| AC-3.6 | WHEN objectFit 为 FITHEIGHT(4) THEN 高度适配容器高度，宽度按比例缩放 | 正常 |
| AC-3.7 | WHEN objectFit 为 NONE(5) THEN 图片使用原始尺寸，不缩放 | 正常 |
| AC-3.8 | WHEN objectFit 为 SCALE_DOWN(6) THEN 行为同 NONE，但不超过原始图片尺寸（取 min(原始, 容器)） | 边界 |
| AC-3.9 | WHEN objectFit 为 TOP_LEFT(7)~BOTTOM_END(15) THEN 按 9 宫格方位定位图片（TOP_LEFT/TOP/TOP_END/START/CENTER/END/BOTTOM_START/BOTTOM/BOTTOM_END） | 正常 |
| AC-3.10 | WHEN objectFit 为 MATRIX(17) THEN 使用 imageMatrix 变换矩阵定位图片 | 正常 |
| AC-3.11 | WHEN objectFit 变更时 THEN 同时触发 PROPERTY_UPDATE_LAYOUT（布局层）和 PROPERTY_UPDATE_RENDER（渲染层）双重更新 | 正常 |

> ImageFit 枚举 18 个值（0-17），`constants.h:324-343`。默认 COVER 在 `image_layout_property.cpp:87`

### US-4: 设置图片重复模式

**作为** 应用开发者,
**我想要** 通过 objectRepeat 属性设置图片在容器中的重复方式,
**以便** 实现平铺背景等效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.objectRepeat(value: ImageRepeat)` THEN 设置图片重复模式，默认为 NO_REPEAT | 正常 |
| AC-4.2 | WHEN objectRepeat 为 NO_REPEAT(0) THEN 图片不重复，仅显示一次 | 正常 |
| AC-4.3 | WHEN objectRepeat 为 REPEAT_X(1) THEN 图片在水平方向重复 | 正常 |
| AC-4.4 | WHEN objectRepeat 为 REPEAT_Y(2) THEN 图片在垂直方向重复 | 正常 |
| AC-4.5 | WHEN objectRepeat 为 REPEAT(3) THEN 图片在水平和垂直方向同时重复 | 正常 |
| AC-4.6 | WHEN objectRepeat 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-4.7 | WHEN objectRepeat 为 REPEAT 或 REPEAT_X THEN 水平方向图片尺寸不受容器宽度限制（repeatX=true），`image_pattern.cpp:388-389` | 正常 |
| AC-4.8 | WHEN objectRepeat 为 REPEAT 或 REPEAT_Y THEN 垂直方向图片尺寸不受容器高度限制（repeatY=true），`image_pattern.cpp:388-389` | 正常 |

> ImageRepeat 枚举 4 个值（0-3），`constants.h:317-322`

### US-5: 设置渲染模式

**作为** 应用开发者,
**我想要** 通过 renderMode 属性选择图片以原始模式或模板模式渲染,
**以便** SVG 图片可以使用主题颜色进行模板化渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.renderMode(value: ImageRenderMode)` THEN 设置渲染模式，默认为 ORIGINAL | 正常 |
| AC-5.2 | WHEN renderMode 为 ORIGINAL(0) THEN 图片以原始颜色渲染 | 正常 |
| AC-5.3 | WHEN renderMode 为 TEMPLATE(1) THEN 图片以模板模式渲染（SVG 可结合 fillColor 使用主题颜色） | 正常 |
| AC-5.4 | WHEN renderMode 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |

> ImageRenderMode 枚举 2 个值（0-1），`constants.h:399-402`

### US-6: 设置自动调整解码尺寸

**作为** 应用开发者,
**我想要** 通过 autoResize 属性控制图片是否自动调整解码尺寸以匹配组件尺寸,
**以便** 优化内存使用（开启时按组件尺寸解码，关闭时使用原始尺寸解码）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.autoResize(value: boolean)` THEN 设置是否自动调整解码尺寸 | 正常 |
| AC-6.2 | WHEN 未显式设置 autoResize 且 API < 11 THEN 默认值为 true（启用功率对齐优化） | 边界 |
| AC-6.3 | WHEN 未显式设置 autoResize 且 API >= 11 THEN 默认值为 false（不自动调整） | 边界 |
| AC-6.4 | WHEN 运行在 SceneBoard 窗口 THEN autoResize 默认值为 true（覆盖 API 版本判定），`image_pattern.cpp:2688-2690` | 正常 |
| AC-6.5 | WHEN autoResize 为 true 且存在 resizable 切片配置或图片有旋转（非 UP 方向） THEN autoResize 实际行为被强制关闭，`image_pattern.cpp:880-893` | 正常 |
| AC-6.6 | WHEN autoResize 变更时 THEN 触发 PROPERTY_UPDATE_LAYOUT | 正常 |
| AC-6.7 | WHEN autoResize 为 true 且非 resizable 且无旋转 THEN 使用 SystemProperties::GetImageAutoResizeEnabled() 系统属性决定最终行为 | 正常 |

> autoResize 默认值双重逻辑是已知兼容性风险，见 design.md ADR-3。`image_pattern.cpp:2679-2693`

### US-7: 设置解码目标尺寸

**作为** 应用开发者,
**我想要** 通过 sourceSize 属性指定图片解码的目标像素尺寸,
**以便** 控制解码后图片的实际像素分辨率。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.sourceSize(value: {width: number, height: number})` THEN 设置解码目标尺寸（单位 px） | 正常 |
| AC-7.2 | WHEN sourceSize 宽度或高度 < 0 THEN 桥接层拒绝设置（值校验），`arkts_native_image_bridge.cpp:693-700` | 边界 |
| AC-7.3 | WHEN 未设置 sourceSize THEN 默认为 SizeF(0, 0)，表示不限制解码尺寸 | 异常 |
| AC-7.4 | WHEN sourceSize 变更时 THEN 触发 PROPERTY_UPDATE_LAYOUT | 正常 |
| AC-7.5 | WHEN sourceSize 和 autoResize 同时设置 THEN sourceSize 优先级更高，作为显式指定的解码目标 | 正常 |

> 属性类型为 SizeF（非 ImageSourceSize 结构体），`image_layout_property.h:55`

### US-8: 设置图片旋转方向

**作为** 应用开发者,
**我想要** 通过 orientation 属性设置图片的旋转方向,
**以便** 手动或自动（EXIF）旋转图片显示方向。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.orientation(value: ImageRotateOrientation)` THEN 设置图片旋转方向，默认为 UP | 正常 |
| AC-8.2 | WHEN orientation 为 AUTO(0) THEN 使用图片 EXIF 信息中记录的旋转方向 | 正常 |
| AC-8.3 | WHEN orientation 为 UP(1) THEN 不旋转，使用原始方向（默认值） | 正常 |
| AC-8.4 | WHEN orientation 为 RIGHT(2)/DOWN(3)/LEFT(4) THEN 分别旋转 90°/180°/270° | 正常 |
| AC-8.5 | WHEN orientation 为 UP_MIRRORED(5)~LEFT_MIRRORED(8) THEN 应用镜像+旋转组合变换 | 正常 |
| AC-8.6 | WHEN 图片为多帧图片（GIF/WebP） THEN 强制使用 UP 方向，忽略用户设置，`image_pattern.cpp:680-701` | 正常 |
| AC-8.7 | WHEN orientation 变更时 THEN 触发 PROPERTY_UPDATE_MEASURE（需重新测量布局） | 正常 |
| AC-8.8 | WHEN orientation 入参为 undefined/null（SDK 语义）或桥接层解析失败 THEN JSView 路径回退为 UP，SDK 声明定义 undefined/null 语义为 AUTO，此差异需作为兼容风险记录 | 边界 |

> ImageRotateOrientation 枚举 9 个值（0-8），`constants.h:381-391`

### US-9: 适应原始图片尺寸

**作为** 应用开发者,
**我想要** 通过 fitOriginalSize 属性让 Image 组件尺寸自适应图片原始尺寸,
**以便** 在未设置显式宽高时按图片实际大小显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 `.fitOriginalSize(value: boolean)` THEN 设置是否适应原始尺寸，默认为 false | 正常 |
| AC-9.2 | WHEN fitOriginalSize 为 true 且未设置显式宽高（selfIdealSize.IsNull()） THEN 组件尺寸使用图片原始尺寸 | 异常 |
| AC-9.3 | WHEN fitOriginalSize 为 true 但已设置显式宽高 THEN 显式宽高优先，fitOriginalSize 不生效 | 异常 |
| AC-9.4 | WHEN fitOriginalSize 变更时 THEN 触发 PROPERTY_UPDATE_BY_CHILD_REQUEST（唯一使用此标志的 Image 属性） | 正常 |

> `image_layout_algorithm.cpp:49-104`

### US-10: 设置插值质量

**作为** 应用开发者,
**我想要** 通过 interpolation 属性设置图片缩放时的插值质量,
**以便** 在图片质量与性能之间做取舍。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `.interpolation(value: ImageInterpolation)` THEN 设置插值质量 | 正常 |
| AC-10.2 | WHEN interpolation 为 NONE(0) THEN 不使用插值（最快，质量最低） | 正常 |
| AC-10.3 | WHEN interpolation 为 LOW(1) THEN 使用低质量插值 | 正常 |
| AC-10.4 | WHEN interpolation 为 MEDIUM(2) THEN 使用中等质量插值 | 正常 |
| AC-10.5 | WHEN interpolation 为 HIGH(3) THEN 使用高质量插值（最慢，质量最高） | 正常 |
| AC-10.6 | WHEN 未显式设置 interpolation 且 API < 11（非 SceneBoard） THEN 默认为 NONE | 边界 |
| AC-10.7 | WHEN 未显式设置 interpolation 且 API >= 11（非 SceneBoard） THEN 默认为 LOW | 边界 |
| AC-10.8 | WHEN 运行在 SceneBoard 窗口 THEN interpolation 默认为 NONE | 正常 |
| AC-10.9 | WHEN interpolation 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |

> interpolation 默认值存在不一致（Pattern 成员初始值 LOW vs getter 默认 NONE），见 design.md 风险表。`image_pattern.h:382` vs `image_model_ng.cpp:977`

### US-11: 静态版 setImageOptions 与构造入口

**作为** 静态 ArkTS 开发者,
**我想要** 在 Image(style) 或静态构造中设置图片源、AI 选项和 reloadKey,
**以便** 使用静态范式完成与动态范式一致的图片源配置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-11.1 | WHEN 静态版调用 `Image(src, imageAIOptions?)` THEN 创建 ImageAttribute 并写入图片源和可选 AI 选项 | 正常 |
| AC-11.2 | WHEN 静态版调用 `Image(src, imageAIOptions?, reloadKey?)` 或 `Image(src, reloadKey?)` THEN reloadKey 作为可选字符串参与图片源重载判定 | 正常 |
| AC-11.3 | WHEN 静态版使用 `Image(style)` THEN 需要在属性设置开始调用 `setImageOptions`，结束调用 `applyAttributeFinish`，否则不满足 SDK 声明的构建约束 | 边界 |
| AC-11.4 | WHEN `setImageOptions` 参数 src 为 undefined THEN 静态接口允许构建空源 Image，后续属性仍可设置 | 边界 |

> 静态构造和 `setImageOptions` 声明：`interface/sdk-js/api/arkui/component/image.static.d.ets:515-550`, `image.static.d.ets:1161-1215`。静态 Model 的 reloadKey 写入：`frameworks/core/components_ng/pattern/image/image_model_static.cpp:170-177`。

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.8 | R-4, R-5, R-20, R-21 | — | 代码审查 | `image.d.ts:549`, `js_image.cpp:460-473`, `image_model_ng.cpp:105-109` |
| AC-2.1~2.7 | R-6, R-16, R-22 | — | 代码审查 | `image.d.ts:841`, `image.d.ts:875`, `js_image.cpp:1390-1451` |
| AC-3.1~3.11 | R-7, R-8 | — | 单元测试 | `image_layout_algorithm.cpp` |
| AC-4.1~4.8 | R-9 | — | 代码审查 | `image_pattern.cpp:388-389` |
| AC-5.1~5.4 | R-10 | — | 代码审查 | `image_render_property.h:65` |
| AC-6.1~6.7 | R-11, R-17 | — | 代码审查 | `image_pattern.cpp:2679-2693` |
| AC-7.1~7.5 | R-12 | — | 代码审查 | `image_layout_property.h:55` |
| AC-8.1~8.8 | R-13, R-18, R-23 | — | 代码审查 | `image.d.ts:1830`, `js_image.cpp:1158-1171`, `image_model_ng.cpp:1152-1166` |
| AC-9.1~9.4 | R-14 | — | 单元测试 | `image_layout_algorithm.cpp:49-104` |
| AC-10.1~10.9 | R-15, R-19 | — | 代码审查 | `image_pattern.h:382`, `image_pattern.cpp:2679-2693` |
| AC-11.1~11.4 | R-21 | — | 代码审查 | `image.static.d.ets:515-550`, `image.static.d.ets:1161-1215` |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 任一核心显示属性通过 ArkTS 或 C API 设置 | Image 组件属性分为三层存储：LayoutProperty（触发布局/加载）、RenderProperty（触发渲染）、Pattern 成员（需手动触发后续动作） | 属性层级见 design.md | AC-1.1~AC-11.4 |
| R-2 | 行为 | ImageSourceInfo 进入加载流程 | 图片加载管线（ImageLoadingContext）消费 ImageSourceInfo，管线行为变更会影响 Image 组件表现（跨功能域依赖 Func-04-01-01） | 加载管线另见 Func-04-01-01 | AC-1.1~AC-1.7 |
| R-3 | 行为 | 调用 `.objectFit(value)` | objectFit 同时写入 LayoutProperty 和 RenderProperty，因此同时影响布局计算和渲染绘制 | 默认值 COVER | AC-3.1~AC-3.11 |
| R-4 | 行为 | 调用 Image(src) 或 C API `NODE_IMAGE_SRC` | ImageSourceInfo 包装图片源信息并自动识别 SrcType，传递给 ImageLoadingContext 进行加载 | Base64 不支持 wildcard subtype，不支持 Base64 SVG | AC-1.1~AC-1.5 |
| R-5 | 行为 | src 或 reloadKey 发生变更 | src 存储在 LayoutProperty；reloadKey 存储在 ImageSourceInfo，更新后触发重新布局/加载判定 | reloadKey 为空字符串时置为 nullopt | AC-1.4, AC-1.7 |
| R-6 | 行为 | 主图加载失败且配置 alt/ImageAlt | alt 图片采用主图失败 -> alt -> altError -> altPlaceholder/空白降级链 | 网络 URL 仅允许 error 相关路径按实现进入；普通 alt 会被桥接/Model 过滤 | AC-2.1~AC-2.7 |
| R-7 | 行为 | 未显式设置 objectFit | objectFit 使用 COVER(2) 默认值，保持宽高比填满容器并居中裁剪溢出部分 | C API reset 也回到 COVER | AC-3.1~AC-3.4 |
| R-8 | 行为 | objectFit 为 TOP_LEFT(7) 到 BOTTOM_END(15) 或 MATRIX(17) | 9 宫格定位通过改变图片对齐位置实现，MATRIX 模式使用 imageMatrix 变换 | MATRIX 详见 Feat-02 | AC-3.9~AC-3.10 |
| R-9 | 行为 | objectRepeat 为 REPEAT_X/REPEAT_Y/REPEAT | objectRepeat 影响渲染绘制区域，REPEAT_X 水平方向平铺，REPEAT_Y 垂直方向平铺 | SVG 与 AnimatedDrawableDescriptor 不适用（SDK 声明） | AC-4.1~AC-4.8 |
| R-10 | 行为 | renderMode 为 TEMPLATE 且未被 colorFilter 覆盖 | TEMPLATE 模式以模板方式渲染非 SVG 图片；SDK 声明 renderMode 不适用于 SVG 且 colorFilter 设置后 renderMode 不生效 | 与 Feat-02 colorFilter 互斥 | AC-5.1~AC-5.4 |
| R-11 | 行为 | 未显式设置 autoResize | autoResize 默认值取决于 API 版本和 SceneBoard：API<11 为 true，API>=11 为 false，SceneBoard 强制 true | resizable 或旋转可能影响默认判定 | AC-6.1~AC-6.7 |
| R-12 | 行为 | 调用 sourceSize 且 width/height >= 0 | sourceSize 以 px 为单位指定解码目标尺寸；宽高 <=0 时 ImageLoadingContext 视为无效并回退使用图片尺寸 | SVG、PixelMap、AnimatedDrawableDescriptor 不适用（SDK 声明） | AC-7.1~AC-7.5 |
| R-13 | 行为 | 调用 orientation(AUTO/UP/RIGHT/DOWN/LEFT/镜像值) | orientation 写入 LayoutProperty 并同步 Pattern 的用户方向；AUTO 使用图片自身方向信息 | 默认 UP；undefined/null 的 SDK 与 JSView 差异见 R-23 | AC-8.1~AC-8.7 |
| R-14 | 行为 | fitOriginalSize=true 且未设置显式宽高 | 组件尺寸按图片原始尺寸计算；若设置显式宽高则显式尺寸优先 | 对 AnimatedDrawableDescriptor 不适用（SDK 声明） | AC-9.1~AC-9.4 |
| R-15 | 行为 | 未显式设置 interpolation | API<11 默认 NONE，API>=11 默认 LOW，SceneBoard 默认 NONE；reset 通过 Pattern 默认值写回 | undefined 在 SDK 声明中按 NONE 处理 | AC-10.1~AC-10.9 |
| R-16 | 异常 | alt 普通路径传入网络 URL | 桥接/Model 不把网络 URL 作为普通 loading placeholder 使用，避免加载在线占位图 | 不抛异常，以默认/空 alt 处理 | AC-2.5 |
| R-17 | 异常 | 未显式 autoResize 且存在 resizable 或非 UP 旋转 | Pattern 默认自动调整判定返回 false，不按组件尺寸重采样 | 用户显式设置 autoResize 时优先尊重显式值 | AC-6.4~AC-6.7 |
| R-18 | 异常 | 图片为多帧图片且设置 orientation | 多帧图片方向处理以实现侧实际解码/绘制为准，不按普通静态图完整套用用户方向 | 需用动画图测试验证 | AC-8.6 |
| R-19 | 异常 | 读取 interpolation 但 paintProperty 未存值 | Getter 返回 Pattern 的 interpolationDefault_，而不是字段 interpolation_ 的初始 LOW | 这是兼容风险，不改实现 | AC-10.6~AC-10.8 |
| R-20 | 边界 | 构造参数为 ImageContent.Empty 或 resetImage | 前端走 ResetImage，ImageSourceInfo 标记 `isFromReset=true`，Pattern 清空主图和 alt 状态 | 只在 ImageContent.Empty reset 语义下触发 | AC-1.6 |
| R-21 | 行为 | 静态版 Image 构造或 setImageOptions | 静态 API 允许 src 为 undefined，并通过 `setImageOptions`/静态构造设置 src、ImageAIOptions、reloadKey | 静态 API 从 API 23/26 提供 | AC-11.1~AC-11.4 |
| R-22 | 行为 | alt 使用 ImageAlt 对象 | placeholder 与 error 分别写入 AltPlaceholder 与 AltError，普通 alt 写入 Alt | 动态 API 22、静态 API 23 起声明 | AC-2.7 |
| R-23 | 边界 | orientation 入参为 undefined/null 或解析失败 | SDK 声明 undefined/null 为 AUTO；JSView 解析失败路径设置 UP，形成需记录的 SDK/实现差异 | 不修改实现，仅记录风险 | AC-8.8 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5 (src) | XTS + 代码审查 | 各 SrcType 正确识别和加载 |
| VM-2 | AC-2.1~2.7 (alt) | XTS | 降级链完整性、ImageAlt placeholder/error 拆分和网络 URL 拒绝 |
| VM-3 | AC-3.1~3.11 (objectFit) | 单元测试 | 18 种 ImageFit 的布局计算结果 |
| VM-4 | AC-4.1~4.8 (objectRepeat) | XTS | 4 种重复模式的绘制区域 |
| VM-5 | AC-5.1~5.4 (renderMode) | XTS | TEMPLATE 模式 SVG 渲染 |
| VM-6 | AC-6.1~6.7 (autoResize) | XTS + 代码审查 | API 版本默认值差异和强制关闭逻辑 |
| VM-7 | AC-7.1~7.5 (sourceSize) | XTS | 解码尺寸控制和边界校验 |
| VM-8 | AC-8.1~8.7 (orientation) | XTS | EXIF 自动识别和多帧图片豁免 |
| VM-9 | AC-9.1~9.4 (fitOriginalSize) | 单元测试 | 布局算法中原始尺寸适配逻辑 |
| VM-10 | AC-10.1~10.9 (interpolation) | XTS + 代码审查 | API 版本默认值和实际使用值 |
| VM-11 | AC-11.1~11.4 (static/setImageOptions) | 静态 ArkTS 编译测试 + 代码审查 | setImageOptions、undefined src 和 reloadKey 参数形态 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `Image(src)` / `Image(src, reloadKey?)` | Public | PixelMap/ResourceStr/DrawableDescriptor/ImageContent，可选 reloadKey | ImageAttribute | N/A | 设置图片源并支持 API 26 reloadKey | AC-1.1~1.8 |
| `Image(src, imageAIOptions?, reloadKey?)` | Public | 图片源、可选 ImageAIOptions、可选 reloadKey | ImageAttribute | N/A | 构造时绑定 AI 选项和重载键 | AC-1.7, AC-11.1~11.2 |
| `setImageOptions(src, imageAIOptions?, reloadKey?)` | Public staticonly | 静态版图片源、可选 AI 选项、可选 reloadKey | this | N/A | 静态 builder 形态设置图片源 | AC-11.1~11.4 |
| `alt(value)` | Public | string/Resource/PixelMap/ImageAlt/undefined | ImageAttribute/this | N/A | 设置占位图/错误图 | AC-2.1~2.7 |
| `objectFit(value: ImageFit)` | Public | ImageFit | ImageAttribute/this | N/A | 设置图片缩放模式（默认 COVER） | AC-3.1~3.11 |
| `objectRepeat(value: ImageRepeat)` | Public | ImageRepeat | ImageAttribute/this | N/A | 设置图片重复模式（默认 NO_REPEAT） | AC-4.1~4.8 |
| `renderMode(value: ImageRenderMode)` | Public | ImageRenderMode | ImageAttribute/this | N/A | 设置渲染模式（默认 ORIGINAL） | AC-5.1~5.4 |
| `autoResize(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 设置自动调整解码尺寸 | AC-6.1~6.7 |
| `sourceSize(value: ImageSourceSize)` | Public | width/height，px | ImageAttribute/this | N/A | 设置解码目标尺寸 | AC-7.1~7.5 |
| `orientation(value: ImageRotateOrientation)` | Public | ImageRotateOrientation | ImageAttribute/this | N/A | 设置图片旋转方向（默认 UP） | AC-8.1~8.8 |
| `fitOriginalSize(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 设置适应原始图片尺寸（默认 false） | AC-9.1~9.4 |
| `interpolation(value: ImageInterpolation)` | Public | ImageInterpolation | ImageAttribute/this | N/A | 设置插值质量 | AC-10.1~10.9 |
| `NODE_IMAGE_SRC`/`NODE_IMAGE_OBJECT_FIT`/`NODE_IMAGE_INTERPOLATION`/`NODE_IMAGE_OBJECT_REPEAT`/`NODE_IMAGE_AUTO_RESIZE`/`NODE_IMAGE_ALT`/`NODE_IMAGE_RENDER_MODE`/`NODE_IMAGE_FIT_ORIGINAL_SIZE`/`NODE_IMAGE_SOURCE_SIZE`/`NODE_IMAGE_ORIENTATION` | Public C API | ArkUI_AttributeItem 字符串或数值 | ArkUI_AttributeItem | N/A | NDK 设置/重置/获取核心 Image 属性 | AC-1.1~AC-10.9 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**Image(src, imageAIOptions?, reloadKey?) / setImageOptions(src, imageAIOptions?, reloadKey?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Image(src: PixelMap | ResourceStr | DrawableDescriptor | ImageContent, imageAIOptions?: ImageAIOptions, reloadKey?: string): ImageAttribute` |
| 返回值 | `ImageAttribute` / `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.8, AC-11.1~AC-11.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| src | PixelMap/ResourceStr/DrawableDescriptor/ImageContent/undefined(static) | 动态是；静态可 undefined | 空源 | Base64 需为 `data:image/subtype;base64,...`，不支持 wildcard subtype 和 Base64 SVG；AnimatedDrawableDescriptor 不触发若干属性/事件。 |
| imageAIOptions | ImageAIOptions | 否 | 未设置 | 传入对象时转为 napi_value 并交给 Pattern 的 ImageAnalyzerManager。 |
| reloadKey | string | 否 | nullopt | 仅非空字符串写入 ImageSourceInfo；空字符串按未设置处理。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 动态版 Image(src) 传入 Resource/PixelMap/string | Model 创建 ImageSourceInfo 并写入 LayoutProperty | AC-1.1~AC-1.4 |
| 2 | 动态版 Image(src, reloadKey) 或 Image(src, imageAIOptions, reloadKey) | JSView 解析第 2/3 个字符串参数作为 reloadKey | AC-1.7 |
| 3 | 静态版 Image(style) 使用 setImageOptions | setImageOptions 负责源配置，builder 结束后 applyAttributeFinish 生效 | AC-11.3 |

**alt(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `alt(value: ResourceStr | PixelMap | ImageAlt | undefined): ImageAttribute` |
| 返回值 | `ImageAttribute` / `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value/src | ResourceStr/PixelMap/ImageAlt | 是 | null | 普通占位图不支持在线图片；ImageAlt.placeholder/error 分别用于 loading 和 failed 状态。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | alt(ResourceStr/PixelMap) | 写入 Alt 并参与主图失败后的降级显示 | AC-2.1, AC-2.3 |
| 2 | alt(ImageAlt{placeholder,error}) | placeholder 写 AltPlaceholder，error 写 AltError | AC-2.2, AC-2.7 |
| 3 | alt 网络 URL | 普通 alt 路径不加载在线占位图 | AC-2.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 是 — autoResize 默认值在 API 11 发生变更（true → false）；interpolation 默认值在 API 11 发生变更（NONE → LOW）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（动态基础 Image），静态 Image API 23，reloadKey API 26
- **API 版本号策略:** @since 7 标注基础属性；API 11 影响 autoResize/interpolation 默认值；API 12 引入 ImageContent/ImageAIOptions 构造；API 14 引入 orientation；API 22 引入 ImageAlt；API 23 引入静态 Image；API 26 引入 reloadKey/setImageOptions 重载

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 属性三层存储 | src/alt/objectFit/autoResize/sourceSize/fitOriginalSize/orientation 存 LayoutProperty；objectRepeat/renderMode/interpolation 存 RenderProperty；变更触发不同的 dirty flag | AC-1~10 |
| objectFit 双写 | objectFit 同时写入 LayoutProperty 和 RenderProperty，触发 LAYOUT + RENDER 双重更新 | AC-3.11 |
| 跨功能域依赖 | 图片加载管线（Func-04-01-01）是 Image 组件的上游，管线行为变更可能影响 Image 表现 | AC-1.1~1.5 |
| fitOriginalSize 特殊更新标志 | 使用 PROPERTY_UPDATE_BY_CHILD_REQUEST，与其他属性的 MEASURE/LAYOUT/RENDER 不同 | AC-9.4 |
| reloadKey 不独立存储 | reloadKey 嵌入 ImageSourceInfo，而不是单独属性；变更通过 ImageSourceInfo 参与重载判定 | AC-1.7 |
| 静态 API 与动态 API 版本不同 | 静态 ImageAttribute 从 API 23 起声明，API 26 增加 setImageOptions/reloadKey；动态基础属性从 API 7 起分批演进 | AC-11.1~AC-11.4 |

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
| ArkTS Widget/Form | 字符串网络/文件源能力受 SDK 声明限制 | widgets 支持 GIF 仅播放一次，不支持 `http://` 或 `file://` 前缀字符串 | SDK 审查 | `interface/sdk-js/api/@internal/component/ets/image.d.ts:536-540` |

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
| 生态兼容 | 是 | objectFit 18 种枚举含非标准值（9 宫格定位），reloadKey/API 26 构造重载影响动态刷新语义 | AC-1.7, AC-3.9 |

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

  Scenario: reloadKey 触发图片源重载判定
    Given 一个 Image 组件，src 指向同一个资源 A
    And 初始 reloadKey 为 key-1
    When 使用相同 src 但 reloadKey 变为 key-2 重新构造 Image
    Then ImageSourceInfo 中 reloadKey 发生变化
    And 加载流程可按重载键变化重新评估图片源

  Scenario: 静态版 setImageOptions 配置空源
    Given 静态 ArkTS Image(style) builder
    When setImageOptions(undefined) 被调用
    Then 组件允许建立空源 Image 节点
    And 后续仍可设置 objectFit/autoResize 等属性
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
