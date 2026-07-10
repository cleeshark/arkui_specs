# 特性规格

> Func-05-08-01-Feat-03 高级功能：固化 resizable、enableAnalyzer、analyzerConfig、ImageAIOptions、copyOption、draggable、syncLoad、matchTextDirection、supportSvg2、privacySensitive、enhancedImageQuality 十一个高级功能属性/配置的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 高级功能 (Advanced Features) |
| 特性编号 | Func-05-08-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 7 起支持，API 8/9/11/12/18/21/23/26 有增强 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 draggable | 动态 API 9 起提供，API 18 起跨平台；默认值 API 9 及以前 false、API 10 起/当前主题路径可为 true。 |
| MODIFIED | 补齐 analyzerConfig/ImageAIOptions | `analyzerConfig` 为 system API，构造态 `ImageAIOptions` 通过 napi_value 交给 ImageAnalyzerManager。 |
| MODIFIED | 补齐静态/NDK 覆盖 | 静态 API 23 覆盖高级属性；C API 覆盖 draggable/resizable/syncLoad/copyOption/enableAnalyzer 等。 |
| MODIFIED | 修正 enhancedImageQuality 默认值 | SDK 声明默认 Low，静态 reset 实现回退 NONE，动态 JSView 缺省/非法入参回退 LOW。 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `arkui-specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/image.d.ts` | 已核对：高级功能 API 声明 |
| Static SDK | `interface/sdk-js/api/arkui/component/image.static.d.ets` | 已核对：静态高级属性声明 |
| C API | `interfaces/native/native_node.h` | 已核对：高级属性 NDK 枚举 |

---

## 用户故事

### US-1: 设置图片可拉伸配置

**作为** 应用开发者,
**我想要** 通过 resizable 属性设置图片的九宫格切片或网格拉伸配置,
**以便** 实现图片在不同尺寸下的无损拉伸效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.resizable(value: ResizableOptions)` 传入 slice 配置 THEN 设置九宫格切片（ImageResizableSlice: left/right/top/bottom 四边距） | 正常 |
| AC-1.2 | WHEN 调用 resizable 传入 lattice 配置 THEN 设置网格拉伸（DrawingLattice 对象） | 正常 |
| AC-1.3 | WHEN resizable 设置后 THEN 存储在 RenderProperty 的 ImagePaintStyle 组中，触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-1.4 | WHEN 存在 resizable 切片配置 THEN 每次 layout wrapper 交换时重新计算拉伸区域，`image_pattern.cpp:1024-1052` | 正常 |
| AC-1.5 | WHEN 存在 resizable 切片或旋转（非 UP）THEN autoResize 被强制关闭，`image_pattern.cpp:880-893` | 正常 |
| AC-1.6 | WHEN resizable slice 值支持 Resource 类型 THEN 通过 ResourceUpdater 支持主题变更动态更新，`image_model_ng.cpp:649-694` | 正常 |
| AC-1.7 | WHEN resizable 配置有效 THEN SDK 声明 objectRepeat、antialiased、orientation 不生效；slice 上下或左右和超过源图尺寸时 resizable 不生效 | 边界 |
| AC-1.8 | WHEN C API 设置 `NODE_IMAGE_RESIZABLE` 且 `.object` 为 OH_Drawing_Lattice THEN lattice 模式从 API 24 起可通过 NDK 传入 | 正常 |

> ImageResizableSlice 定义：`frameworks/base/image/image_resizable_slice.h:36-63`

### US-2: 启用图片分析器

**作为** 应用开发者,
**我想要** 通过 enableAnalyzer 属性启用图片 AI 分析功能,
**以便** 让用户对图片内容进行智能识别和分析。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.enableAnalyzer(value: boolean)` THEN 启用或关闭图片分析器，默认 false | 正常 |
| AC-2.2 | WHEN enableAnalyzer 设置为 true THEN 创建 ImageAnalyzerManager 实例管理分析功能 | 正常 |
| AC-2.3 | WHEN enableAnalyzer 变更时 THEN 通过 Pattern 成员变量（isEnableAnalyzer_）管理，无 dirty flag 自动触发 | 正常 |
| AC-2.4 | WHEN analyzerConfig 配置 types THEN JSView 只接受 SUBJECT/TEXT 两类，其它数值被跳过 | 正常 |
| AC-2.5 | WHEN enableAnalyzer=false THEN SetImageAnalyzerConfig(const ImageAnalyzerConfig&) 直接返回，不创建配置效果 | 边界 |
| AC-2.6 | WHEN 构造参数传入 ImageAIOptions THEN Pattern 按需创建 ImageAnalyzerManager 并传入 options，不要求 enableAnalyzer 已开启 | 正常 |
| AC-2.7 | WHEN 图片为 SVG、GIF/多帧图、alt 占位图、objectRepeat 非 NoRepeat 或 obscured 开启 THEN SDK 声明不支持分析；实现侧 IsSupportImageAnalyzerFeature 要求非 SVG、frameCount<=1 且 Manager 支持 | 边界 |

> ImageAnalyzerConfig：`interfaces/inner_api/ace/ai/image_analyzer.h:105-109`；enable/analyzerConfig 实现：`frameworks/core/components_ng/pattern/image/image_pattern.cpp:2552-2607`；构造态 ImageAIOptions 解析：`frameworks/bridge/declarative_frontend/jsview/js_image.cpp:479-496`。

### US-3: 设置复制选项

**作为** 应用开发者,
**我想要** 通过 copyOption 属性设置图片是否可复制及复制范围,
**以便** 控制图片内容的复制行为（应用内/本地/分布式）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.copyOption(value: CopyOptions)` THEN 设置复制选项，默认 None | 正常 |
| AC-3.2 | WHEN copyOption 为 None(0) THEN 图片不可复制 | 正常 |
| AC-3.3 | WHEN copyOption 为 InApp(1) THEN 图片仅可在应用内复制 | 正常 |
| AC-3.4 | WHEN copyOption 为 Local(2) THEN 图片可在本设备内复制 | 正常 |
| AC-3.5 | WHEN copyOption 为 Distributed(3) THEN 图片支持跨设备分布式复制 | 正常 |
| AC-3.6 | WHEN 图片被隐私遮盖（obscured by placeholder）THEN 复制功能被禁用，`image_pattern.cpp:1490-1508` | 正常 |
| AC-3.7 | WHEN copyOption 变更时 THEN 通过 Pattern 成员变量（copyOption_）管理，无 dirty flag | 正常 |
| AC-3.8 | WHEN 图片为 SVG 或 AnimatedDrawableDescriptor THEN SDK 声明 copyOption 不生效 | 边界 |

> CopyOptions 枚举 4 个值（0-3），`constants.h:727-732`

### US-4: 设置同步加载

**作为** 应用开发者,
**我想要** 通过 syncLoad 属性控制图片加载的同步/异步模式,
**以便** 在需要立即显示图片时使用同步加载避免闪烁。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.syncLoad(value: boolean)` THEN 设置同步/异步加载模式，默认 false（异步） | 正常 |
| AC-4.2 | WHEN syncLoad 为 false THEN 图片在后台线程加载，UI 线程不阻塞 | 正常 |
| AC-4.3 | WHEN syncLoad 为 true THEN 图片在 UI 线程同步加载，PixelMap 通过 LoadPixelMapDrawableSync() 同步获取，`image_pattern.cpp:1256-1273` | 正常 |
| AC-4.4 | WHEN syncLoad 变更时 THEN 通过 Pattern 成员变量（syncLoad_）管理，传递给 ImageLoadingContext 构造函数 | 正常 |
| AC-4.5 | WHEN syncLoad 设置后对新加载生效 THEN 不影响已加载完成的图片 | 正常 |
| AC-4.6 | WHEN syncLoad=true 且主线程阻塞超过 6s THEN SDK 明确存在 AppFreeze 风险，规格仅记录风险不改变实现 | 边界 |

> `image_pattern.h:418`：`bool syncLoad_ = false`

### US-5: 匹配文本方向

**作为** 应用开发者,
**我想要** 通过 matchTextDirection 属性让图片在 RTL 布局中自动翻转,
**以便** 支持从右到左的语言环境下的图片显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.matchTextDirection(value: boolean)` THEN 设置是否匹配文本方向，默认 false | 正常 |
| AC-5.2 | WHEN matchTextDirection 为 true 且当前布局为 RTL（isRightToLeft=true）THEN 图片水平翻转（flipHorizontally=true），`image_paint_method.cpp:119-120` | 正常 |
| AC-5.3 | WHEN matchTextDirection 为 false THEN 即使在 RTL 布局中图片也不翻转 | 正常 |
| AC-5.4 | WHEN matchTextDirection 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-5.5 | WHEN 运行在静态版 API 23 或 NDK `NODE_IMAGE_MATCH_TEXT_DIRECTION` THEN 同样写入 RenderProperty 的 MatchTextDirection | 正常 |

> RenderProperty 存储：`image_render_property.h:74`

### US-6: 启用 SVG2 支持

**作为** 应用开发者,
**我想要** 通过 supportSvg2 属性启用 SVG2 规范支持,
**以便** 使用 SVG2 的新特性和元素。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.supportSvg2(value: boolean)` THEN 启用或关闭 SVG2 支持，默认 false | 正常 |
| AC-6.2 | WHEN supportSvg2 为 true THEN 传递给 ImageLoadingContext（loadingCtx_->SetSupportSvg2(true)），`image_pattern.cpp:1113` | 正常 |
| AC-6.3 | WHEN supportSvg2 变更时 THEN 通过 Pattern 成员变量（supportSvg2_）管理，无 dirty flag | 正常 |
| AC-6.4 | WHEN Image 组件创建完成后再动态修改 supportSvg2 THEN SDK 声明该值不能动态改变，需作为兼容约束记录 | 边界 |

> `image_pattern.h:444`：`bool supportSvg2_ = false`

### US-7: 设置隐私敏感标记

**作为** 应用开发者,
**我想要** 通过 privacySensitive 属性标记图片为隐私敏感内容,
**以便** 在安全显示模式下自动对图片应用模糊遮盖效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.privacySensitive(value: boolean)` THEN 设置隐私敏感标记 | 正常 |
| AC-7.2 | WHEN privacySensitive 为 true 且 isSensitive 为 true THEN 对图片应用模糊背景效果（radius=IMAGE_SENSITIVE_RADIUS, saturation=IMAGE_SENSITIVE_SATURATION, brightness=IMAGE_SENSITIVE_BRIGHTNESS），`image_pattern.cpp:2716-2738` | 正常 |
| AC-7.3 | WHEN privacySensitive 为 false THEN 不应用隐私遮盖效果 | 正常 |
| AC-7.4 | WHEN privacySensitive 属性 THEN 实际存储在 FrameNode 上（host->IsPrivacySensitive()），非 Image 专属属性 | 正常 |

> `image_pattern.cpp:926-931`：通过 host->IsPrivacySensitive() 读取

### US-8: 设置增强图像质量

**作为** 应用开发者,
**我想要** 通过 enhancedImageQuality 属性启用 AI 图像增强,
**以便** 通过 AI 算法提升图片的显示质量。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.enhancedImageQuality(value: ResolutionQuality)` THEN 设置 AI 图像增强级别，默认 NONE | 正常 |
| AC-8.2 | WHEN enhancedImageQuality 为 NONE(0) THEN 不启用 AI 增强（默认） | 正常 |
| AC-8.3 | WHEN enhancedImageQuality 为 LOW(1) THEN 启用低级别 AI 增强 | 正常 |
| AC-8.4 | WHEN enhancedImageQuality 为 NORMAL(2) THEN 启用中级别 AI 增强 | 正常 |
| AC-8.5 | WHEN enhancedImageQuality 为 HIGH(3) THEN 启用高级别 AI 增强 | 正常 |
| AC-8.6 | WHEN enhancedImageQuality 设置后 THEN 传递给 ImageLoadingContext（loadingCtx_->SetImageQuality()），影响解码质量选择，`image_pattern.cpp:862` | 正常 |
| AC-8.7 | WHEN JSView 未传参或传入非法枚举 THEN 动态实现回退 LOW；WHEN 静态版传入 undefined THEN 静态实现回退 NONE，形成范式差异 | 边界 |

> AIImageQuality 枚举 4 个值（0-3），`constants.h:374-379`。属性名在 API 层为 enhancedImageQuality/ResolutionQuality，内部实现为 AIImageQuality。动态实现默认/非法入参回退 LOW：`frameworks/bridge/declarative_frontend/jsview/js_image.cpp:1143-1155`；静态 reset 回退 NONE：`frameworks/core/components_ng/pattern/image/image_model_static.cpp:222-228`。

### US-9: 设置图片拖拽开关

**作为** 应用开发者,
**我想要** 通过 draggable 控制 Image 是否可拖拽,
**以便** 在默认拖拽、长按手势和自定义拖拽事件之间选择合适交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 调用 `.draggable(value: boolean)` THEN ImageModelNG 根据 value 初始化或移除拖拽事件，并写入 FrameNode 的 customer draggable 状态 | 正常 |
| AC-9.2 | WHEN 未显式设置 draggable THEN FrameNode 初始值来自 ImageTheme/PipelineContext 的 draggable 配置 | 正常 |
| AC-9.3 | WHEN 动态 JSView API 18+ 且未传参 THEN draggable 默认 true；API 18 前默认 false | 边界 |
| AC-9.4 | WHEN draggable=true THEN SDK 声明已绑定的 long press 手势不会生效；WHEN draggable=false THEN 不触发拖拽相关事件 | 正常 |
| AC-9.5 | WHEN NDK 使用 `NODE_IMAGE_DRAGGABLE` THEN 参数 `.value[0].i32` 控制是否可拖拽，并可获取当前值 | 正常 |

> SDK 声明：`interface/sdk-js/api/@internal/component/ets/image.d.ts:1290`、`interface/sdk-js/api/arkui/component/image.static.d.ets:827`。实现：`frameworks/core/components_ng/pattern/image/image_model_ng.cpp:524-539`, `image_model_ng.cpp:827-839`, `frameworks/bridge/declarative_frontend/jsview/js_image.cpp:1236-1243`，NDK 枚举：`interfaces/native/native_node.h:3401-3413`。

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.8 | R-4, R-12, R-18 | — | 代码审查 | `image_resizable_slice.h:36-63`, `native_node.h:3449-3468` |
| AC-2.1~2.7 | R-5, R-14, R-19 | — | 代码审查 | `image_analyzer.h:105-109`, `image_pattern.cpp:2552-2607` |
| AC-3.1~3.8 | R-6, R-13, R-20 | — | 代码审查 | `image_pattern.cpp:1490-1508` |
| AC-4.1~4.6 | R-7, R-21 | — | 代码审查 | `image_pattern.cpp:1256-1273` |
| AC-5.1~5.5 | R-8 | — | 代码审查 | `image_paint_method.cpp:119-120`, `native_node.h:3509-3521` |
| AC-6.1~6.4 | R-9, R-15 | — | 代码审查 | `image_model_ng.cpp:1334-1358`, `image_loading_context.h:169-172` |
| AC-7.1~7.4 | R-10 | — | 代码审查 | `image_pattern.cpp:2716-2738` |
| AC-8.1~8.7 | R-11, R-16 | — | 代码审查 | `image_pattern.cpp:840-890`, `js_image.cpp:1143-1155`, `image_model_static.cpp:222-228` |
| AC-9.1~9.5 | R-17 | — | 代码审查 | `image_model_ng.cpp:524-539`, `js_image.cpp:1236-1243`, `native_node.h:3401-3413` |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置高级功能属性 | 高级功能属性存储位置不统一：resizable/matchTextDirection 存 RenderProperty；enableAnalyzer/copyOption/syncLoad/supportSvg2/privacySensitive/enhancedImageQuality 存 Pattern/FrameNode 成员或通用属性 | 属性变更是否自动 dirty 取决于存储层 | AC-1.1~AC-9.5 |
| R-2 | 行为 | Pattern 成员变量变更 | Pattern 成员变量没有通用 dirty flag 机制，需要各 setter 或后续生命周期显式触发相关逻辑 | 例如 syncLoad 影响后续加载上下文 | AC-2.1~AC-8.7 |
| R-3 | 行为 | resizable slice/lattice 存在 | resizable 与 autoResize、objectRepeat、antialiased、orientation 存在互斥或不生效约束 | autoResize 显式设置优先级见 Feat-01 | AC-1.4~AC-1.7 |
| R-4 | 行为 | 调用 resizable(slice/lattice) | resizable 支持九宫格切片和 DrawingLattice 两种模式，存储在 RenderProperty | C API lattice API 24 起支持 | AC-1.1~AC-1.8 |
| R-5 | 行为 | enableAnalyzer=true | enableAnalyzer 通过 ImageAnalyzerManager 管理 AI 分析能力，启用时注册可见区域变化 | 需 SUPPORT_IMAGE_ANALYZER 宏和设备能力 | AC-2.1~AC-2.7 |
| R-6 | 行为 | copyOption 设置为 None/InApp/Local/Distributed | copyOption 控制 4 级复制权限，隐私遮盖时强制禁用 | SVG/AnimatedDrawableDescriptor 不适用 | AC-3.1~AC-3.8 |
| R-7 | 行为 | syncLoad=true | syncLoad 控制同步/异步加载模式，true 时同步获取 PixelMap 并阻塞 UI 线程 | 主线程阻塞超过 6s 有 AppFreeze 风险 | AC-4.1~AC-4.6 |
| R-8 | 行为 | matchTextDirection=true 且系统 RTL | PaintConfig 设置 flipHorizontally=true，实现水平翻转 | 默认 false | AC-5.1~AC-5.5 |
| R-9 | 行为 | supportSvg2=true | supportSvg2 传递给 ImageLoadingContext 的 ImageSourceInfo，控制增强 SVG 解析 | SDK 声明创建后不可动态改变 | AC-6.1~AC-6.4 |
| R-10 | 行为 | privacySensitive=true 且系统 isSensitive=true | privacySensitive 在 FrameNode 上存储，敏感模式下应用模糊遮盖效果 | 仅设置 privacySensitive 不足以生效 | AC-7.1~AC-7.4 |
| R-11 | 行为 | enhancedImageQuality 设置 | enhancedImageQuality（内部 AIImageQuality）传递给 ImageLoadingContext，影响解码质量选择 | SVG/PixelMap/DrawableDescriptorLoadedResult 等非解码类型不支持 | AC-8.1~AC-8.7 |
| R-12 | 异常 | resizable 切片配置存在 | resizable 存在时 autoResize 被强制关闭或按互斥约束不生效，不受默认值影响 | 用户显式 autoResize 仍需按实现测试 | AC-1.5, AC-1.7 |
| R-13 | 异常 | 图片被 obscured/隐私遮盖 | copyOption 被强制禁用，忽略用户设置 | 防止隐私泄露 | AC-3.6 |
| R-14 | 异常 | enableAnalyzer=false 时调用 analyzerConfig | const ImageAnalyzerConfig 路径直接返回；void* 路径要求 isEnableAnalyzer_ 为 true 才传给 manager | 不抛错 | AC-2.4~AC-2.5 |
| R-15 | 边界 | Image 创建后动态修改 supportSvg2 | SDK 声明不支持动态修改；实现 setter 可写 Pattern 成员，需标注为 SDK/实现兼容风险 | 不改实现 | AC-6.4 |
| R-16 | 边界 | enhancedImageQuality 缺省或非法 | 动态 JSView 回退 LOW；静态 undefined 回退 NONE | 范式差异 | AC-8.7 |
| R-17 | 行为 | draggable 设置或 reset | draggable 控制 GestureHub 拖拽事件初始化/移除，并写入 FrameNode customer draggable 状态 | 默认值由 API 版本和 ImageTheme/PipelineContext 共同影响 | AC-9.1~AC-9.5 |
| R-18 | 边界 | resizable slice 四边和超过源图尺寸 | SDK 声明 resizable 不生效 | 需渲染测试验证 | AC-1.7 |
| R-19 | 行为 | 构造态 ImageAIOptions 传入 | Pattern 按需创建 ImageAnalyzerManager 并传递 options | 不要求 enableAnalyzer 已开启 | AC-2.6 |
| R-20 | 边界 | copyOption 用于 SVG 或 AnimatedDrawableDescriptor | SDK 声明不生效，JSView 动画图路径直接返回 | 不抛错 | AC-3.8 |
| R-21 | 边界 | syncLoad=true 用于网络/大图 | 同步加载可能阻塞 UI，SDK 明确 AppFreeze 风险 | 规格记录风险，不改变行为 | AC-4.6 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.8 (resizable) | XTS + C API UT | slice/lattice 设置、NDK lattice 和互斥属性 |
| VM-2 | AC-2.1~2.7 (enableAnalyzer/analyzerConfig/ImageAIOptions) | XTS | 分析器启用、配置和不支持场景 |
| VM-3 | AC-3.1~3.8 (copyOption) | XTS | 4 级复制权限、SVG/动画不支持和隐私禁用 |
| VM-4 | AC-4.1~4.6 (syncLoad) | XTS + 性能风险验证 | 同步/异步加载行为和 UI 阻塞风险 |
| VM-5 | AC-5.1~5.5 (matchTextDirection) | XTS | RTL 布局下水平翻转和 NDK 覆盖 |
| VM-6 | AC-6.1~6.4 (supportSvg2) | XTS | SVG2 解析支持和创建后不可动态修改约束 |
| VM-7 | AC-7.1~7.4 (privacySensitive) | XTS | 隐私遮盖效果 |
| VM-8 | AC-8.1~8.7 (enhancedImageQuality) | XTS | AI 图像增强级别和动态/静态默认值差异 |
| VM-9 | AC-9.1~9.5 (draggable) | XTS + C API UT | 拖拽开关、默认值和手势互斥 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `resizable(value: ResizableOptions)` | Public | slice/lattice | ImageAttribute/this | N/A | 设置可拉伸配置 | AC-1.1~AC-1.8 |
| `enableAnalyzer(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 启用图片分析器 | AC-2.1~AC-2.7 |
| `analyzerConfig(config: ImageAnalyzerConfig)` | System | types | ImageAttribute/this | N/A | 设置 AI 分析类型 | AC-2.4~AC-2.5 |
| `Image(src, imageAIOptions?)` | Public | 图片源 + ImageAIOptions | ImageAttribute | N/A | 构造态设置 AI 分析选项 | AC-2.6 |
| `copyOption(value: CopyOptions)` | Public | None/InApp/Local/Distributed | ImageAttribute/this | N/A | 设置复制选项 | AC-3.1~AC-3.8 |
| `syncLoad(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 设置同步加载 | AC-4.1~AC-4.6 |
| `matchTextDirection(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 设置 RTL 水平翻转 | AC-5.1~AC-5.5 |
| `supportSvg2(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 启用增强 SVG 解析 | AC-6.1~AC-6.4 |
| `privacySensitive(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 设置隐私敏感标记 | AC-7.1~AC-7.4 |
| `enhancedImageQuality(value: ResolutionQuality)` | System | LOW/NORMAL/HIGH/NONE | ImageAttribute/this | N/A | 设置增强图像质量 | AC-8.1~AC-8.7 |
| `draggable(value: boolean)` | Public | boolean | ImageAttribute/this | N/A | 设置图片拖拽开关 | AC-9.1~AC-9.5 |
| `NODE_IMAGE_DRAGGABLE`/`NODE_IMAGE_RESIZABLE`/`NODE_IMAGE_SYNC_LOAD`/`NODE_IMAGE_MATCH_TEXT_DIRECTION`/`NODE_IMAGE_COPY_OPTION`/`NODE_IMAGE_ENABLE_ANALYZER`/`NODE_IMAGE_SUPPORT_SVG2` | Public C API | ArkUI_AttributeItem 数值、数组或对象 | ArkUI_AttributeItem | N/A | NDK 设置/重置/获取高级属性 | AC-1.1~AC-9.5 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**enableAnalyzer / analyzerConfig / ImageAIOptions**

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableAnalyzer(enable: boolean): ImageAttribute`; `analyzerConfig(config: ImageAnalyzerConfig): ImageAttribute`; `Image(src, imageAIOptions?: ImageAIOptions)` |
| 返回值 | `ImageAttribute` / `this` |
| 开放范围 | enableAnalyzer 为 Public；analyzerConfig 为 System；ImageAIOptions 构造为 Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enable | boolean | 是 | false | 关闭时释放/销毁分析覆盖层；开启时需要 SUPPORT_IMAGE_ANALYZER 和设备能力。 |
| config.types | ImageAnalyzerType[] | 否 | 全部支持（SDK 语义） | JSView 实现只接受 SUBJECT/TEXT，其它值跳过。 |
| imageAIOptions | ImageAIOptions | 否 | 未设置 | 构造态直接传给 ImageAnalyzerManager，不要求 enableAnalyzer 先开启。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enableAnalyzer(true) | 创建 ImageAnalyzerManager 并注册可见区域监听 | AC-2.1~AC-2.2 |
| 2 | analyzerConfig 在 enableAnalyzer=false 时调用 | const config 路径直接返回，void* 路径不传 manager | AC-2.5 |
| 3 | 构造时传 ImageAIOptions | Pattern 按需创建 manager 并转交 options | AC-2.6 |

**draggable(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `draggable(value: boolean): ImageAttribute` |
| 返回值 | `ImageAttribute` / `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-9.1~AC-9.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | API/Theme 默认 | true 初始化 DragDropEvent；false 移除拖拽事件并允许自定义长按手势生效。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | draggable(true) | GestureHub 初始化拖拽事件，FrameNode customer draggable=true | AC-9.1 |
| 2 | draggable(false) | GestureHub 移除拖拽事件，拖拽事件不触发 | AC-9.1, AC-9.4 |
| 3 | NDK NODE_IMAGE_DRAGGABLE | `.value[0].i32` 控制拖拽开关 | AC-9.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（matchTextDirection/fitOriginalSize 等基础高级属性），API 8 syncLoad，API 9 copyOption/draggable，API 11 enableAnalyzer/analyzerConfig/resizable，API 12 privacySensitive/enhancedImageQuality，API 21 supportSvg2，API 23 静态版属性，API 26 构造态 reloadKey/ImageAIOptions 重载
- **API 版本号策略:** Public/System 范围以 SDK `.d.ts/.d.ets` 为准；system API `analyzerConfig`/`enhancedImageQuality` 不按 Public 能力承诺；静态版从 API 23 起单独声明

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| Pattern 成员无 dirty flag | enableAnalyzer/copyOption/syncLoad/supportSvg2/enhancedImageQuality 存 Pattern 成员，变更不自动触发更新 | AC-2~4, AC-6, AC-8 |
| privacySensitive FrameNode 存储 | 实际存储在 FrameNode 级别，非 Image Pattern 独有 | AC-7 |
| resizable 与 autoResize 互斥 | 有 resizable 配置时 autoResize 被强制关闭 | AC-1.5 |
| Analyzer 宏与设备能力 | SUPPORT_IMAGE_ANALYZER 未开启或 Manager 判定不支持时，enableAnalyzer 不产生可见分析能力 | AC-2.1~AC-2.7 |
| draggable 使用通用拖拽框架 | ImageModelNG 通过 FrameNode/GestureHub 管理拖拽，不是 ImagePattern 专属属性 | AC-9.1~AC-9.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | syncLoad=true 阻塞 UI 线程，仅建议小图使用 | 代码审查 | `image_pattern.cpp:1256-1273` |
| 安全 | copyOption 隐私遮盖强制禁用复制，防止隐私泄露 | 代码审查 | `image_pattern.cpp:1490-1508` |
| 安全 | privacySensitive 模糊遮盖效果保护敏感图片 | 代码审查 | `image_pattern.cpp:2716-2738` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |
| 设备 AI 能力不支持 | enableAnalyzer 不产生分析覆盖层 | 取决于 ImageAnalyzerManager 和设备能力 | XTS/设备能力测试 | `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2602-2607` |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 高级功能不影响无障碍 | — |
| 大字体 | 否 | 高级功能不受大字体影响 | — |
| 深色模式 | 否 | 无特殊处理 | — |
| 多窗口/分屏 | 否 | 无特殊处理 | — |
| 多用户 | 是 | privacySensitive 需结合用户安全状态生效 | AC-7 |
| 版本升级 | 是 | draggable 默认值、supportSvg2、静态 API 和 enhancedImageQuality 范式默认值存在版本/范式差异 | AC-6.4, AC-8.7, AC-9.3 |
| 生态兼容 | 是 | enableAnalyzer 受设备能力、网络权限、图像类型和 objectRepeat/obscured 等外部状态影响 | AC-2.7 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 高级功能属性

  Scenario: resizable 与 autoResize 互斥
    Given 一个 Image 组件，autoResize 已设置
    When 设置 resizable slice 配置（left=10, top=10, right=10, bottom=10）
    Then autoResize 被强制关闭
    And 图片使用原始尺寸进行九宫格拉伸

  Scenario: syncLoad 同步加载
    Given 一个 Image 组件，syncLoad 设置为 true
    When 设置图片源
    Then 图片在 UI 线程同步加载
    And LoadPixelMapDrawableSync() 被调用
    And 加载完成前 UI 线程被阻塞

  Scenario: matchTextDirection RTL 翻转
    Given 一个 Image 组件，matchTextDirection 设置为 true
    And 当前布局为 RTL（isRightToLeft=true）
    When 触发渲染
    Then 图片水平翻转（flipHorizontally=true）

  Scenario: privacySensitive 隐私遮盖
    Given 一个 Image 组件，privacySensitive 设置为 true
    And isSensitive 状态为 true
    When 触发渲染
    Then 图片显示模糊遮盖效果
    And 模糊参数为 IMAGE_SENSITIVE_RADIUS/SATURATION/BRIGHTNESS

  Scenario: copyOption 隐私禁用
    Given 一个 Image 组件，copyOption 设置为 Local
    And 图片被隐私遮盖（obscured）
    When 用户尝试复制图片
    Then 复制功能被禁用

  Scenario: draggable 默认值和显式关闭
    Given 一个 API 18 及以上 Image 组件，未显式设置 draggable
    When 组件创建完成
    Then draggable 默认按 true/主题路径初始化拖拽事件
    When 调用 draggable(false)
    Then GestureHub 移除拖拽事件
    And 自定义长按手势可恢复生效

  Scenario: analyzerConfig 在未启用分析器时不生效
    Given 一个 Image 组件，enableAnalyzer 为 false
    When 调用 analyzerConfig({ types: [SUBJECT, TEXT] })
    Then Pattern 的 const config 路径直接返回
    And 不创建分析覆盖层
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（高级功能 11 个属性/配置，不含核心显示/颜色效果/事件）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Image advanced properties: resizable slice/lattice, syncLoad, copyOption, privacySensitive, AI image quality"
```

**关键文档：** `design.md`（同目录）
