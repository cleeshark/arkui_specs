# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ImageSpan 图片片段组件 |
| 特性编号 | Func-05-09-06-Feat-02 |
| 所属 Epic | Span 类组件规格补录 |
| 优先级 | P1 |
| 目标版本 | API 10（dynamic 基线）至 API 26（static 增强） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ImageSpan 创建与图像源规格 | 覆盖 `ImageSpan(value: ResourceStr \| PixelMap)` 构造，复用 JSImage::CreateImageSpan(isImageSpan=true)，dynamic @since 10 / static @since 23 |
| ADDED | ImageSpan 图像属性规格（verticalAlign/objectFit/colorFilter/alt/supportSvg2） | 覆盖图像对齐/缩放/滤镜/占位图/SVG2 支持 |
| ADDED | ImageSpan 装饰与事件规格（textBackgroundStyle/baselineOffset/onComplete/onError） | 覆盖背景/基线偏移（继承 BaseSpan）与图像加载完成/失败回调 |
| ADDED | ImageSpan 节点模型规格 | 覆盖 ImageSpanNode(FrameNode+ImagePattern) 复用 ImagePattern 的布局/绘制路径 |

## 输入文档

| 类型 | 路径 |
|------|------|
| 设计文档 | `05-ui-components/09-text-components/06-span-components/design.md`（详细设计 `### ImageSpan 图片片段（Feat-02）`） |
| SDK dynamic | `interface/sdk-js/api/@internal/component/ets/image_span.d.ts` |
| SDK static | `interface/sdk-js/api/arkui/component/imageSpan.static.d.ets` |
| Modifier dynamic | `interface/sdk-js/api/arkui/ImageSpanModifier.d.ts` |
| Modifier static | `interface/sdk-js/api/arkui/ImageSpanModifier.static.d.ets` |
| 节点实现 | `frameworks/core/components_ng/pattern/text/span_node.h:1461`（ImageSpanNode : FrameNode）、`:1433`（ImageSpanItem : PlaceholderSpanItem） |
| Model 实现 | `frameworks/core/components_ng/pattern/text/span/image_span_view.h:29`（ImageSpanView）、`image_span_view_static.h`（ImageSpanViewStatic） |
| Bridge 实现 | `frameworks/bridge/declarative_frontend/jsview/js_image.cpp:340`（JSImage::CreateImageSpan）、`:442`（CreateImage，isImageSpan=true）、`:463`（config.isImageSpan=true）、`:1183`（注册 createImageSpan） |
| ArkTS-native Bridge | `frameworks/core/components_ng/pattern/text/span/bridge/image_span/arkts_native_image_span_bridge.cpp`（ImageSpanBridge） |
| 样式定义 | `frameworks/core/components_ng/pattern/text/text_styles.h:137`（ImageSpanAttribute）、`:106`（ImageSpanSize）、`:195`（ImageSpanOptions : SpanOptionBase） |
| 布局/绘制 | `frameworks/core/components_ng/pattern/image/image_layout_algorithm.h`（ImageLayoutAlgorithm）、`pattern/image/image_paint_method.h`（ImagePaintMethod）、`render/paragraph.h:290`（Paragraph::AddPlaceholder）、`render/adapter/txt_paragraph.h:69`（TxtParagraph::AddPlaceholder） |
| C-API NDK | `interfaces/native/native_node.h:61`（ARKUI_NODE_IMAGE_SPAN）、`:3244`（NODE_IMAGE_SPAN_SRC）、`:3258`（NODE_IMAGE_SPAN_VERTICAL_ALIGNMENT）、`:3272`（NODE_IMAGE_SPAN_ALT）、`:3284`（NODE_IMAGE_SPAN_BASELINE_OFFSET）、`:3301`（NODE_IMAGE_SPAN_COLOR_FILTER）、`:3314`（NODE_IMAGE_SPAN_SUPPORT_SVG2） |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 插入图片片段

**作为** 应用开发者,
**我想要** 在 `Text` 组件下使用 `ImageSpan` 子组件声明一张行内图片,
**以便** 文本行内可混合文字与图片。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 开发者在 `Text` 下声明 `ImageSpan($r('app.media.icon'))` THEN 经 `JSImage::CreateImageSpan`（`js_image.cpp:340`）→ `CreateImage(info, isImageSpan=true)`（`:442`）→ `config.isImageSpan=true`（`:463`），构造 `ImageSpanNode`（FrameNode，复用 ImagePattern）并包装 `ImageSpanItem`（spanItemType=IMAGE），挂载为 Text 子节点 | 正常 |
| AC-1.2 | WHEN 传入 `ImageSpan(pixelMap)`（PixelMap 类型） THEN ImageSpan 以 PixelMap 作为图像源，无需资源解析 | 正常 |
| AC-1.3 | WHEN `ImageSpan` 未挂在 Text/RichEditor 下 THEN 无父级 Paragraph 占位符消费，图片不渲染 | 边界 |
| AC-1.4 | WHEN 父级 TextLayoutAlgorithm 消费含 ImageSpanItem 的列表 THEN 经 `Paragraph::AddPlaceholder`（`paragraph.h:290`，`TxtParagraph:69`）在段落中预留占位符槽位 | 正常 |

### US-2: 设置对齐与缩放

**作为** 应用开发者,
**我想要** 通过 verticalAlign/objectFit 设置图片片段在行内的垂直对齐与缩放模式,
**以便** 图片与文字基线/顶部/底部对齐，并按需裁剪/填充。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 调用 `.verticalAlign(ImageSpanAlignment.BASELINE)` THEN ImageSpanView::SetVerticalAlign 写入，图片底部与文字基线对齐 | 正常 |
| AC-2.2 | WHEN 调用 `.verticalAlign(ImageSpanAlignment.TOP)` 或 `BOTTOM` THEN 图片顶部/底部与行框对齐 | 正常 |
| AC-2.3 | WHEN 调用 `.objectFit(ImageFit.Cover)` THEN ImageSpanView::SetObjectFit 写入 ImageFit，图片按 Cover 模式裁剪填充占位符槽位 | 正常 |
| AC-2.4 | WHEN 未设置 objectFit THEN 默认按 ImageFit 默认值（Contain 或父级继承）处理 | 边界 |

### US-3: 设置滤镜、占位图与 SVG2 支持

**作为** 应用开发者,
**我想要** 通过 colorFilter/alt/supportSvg2 设置图片滤镜、加载失败占位图与 SVG 二代解析,
**以便** 图片可应用颜色变换、加载失败时显示替代图、SVG 资源用增强解析。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN 调用 `.colorFilter(filter)`（ColorFilter 或 DrawingColorFilter，API 14 dynamic / 23 static） THEN 图片应用颜色滤镜变换 | 正常 |
| AC-3.2 | WHEN 调用 `.alt(pixelMap)`（API 12 dynamic / 23 static） THEN 图片加载失败时显示该占位 PixelMap | 正常 |
| AC-3.3 | WHEN 调用 `.supportSvg2(true)`（API 22 dynamic / 24 static） THEN ImageSpan 启用 SVG 二代解析 | 正常 |
| AC-3.4 | WHEN `.supportSvg2(false)` 或未设置 THEN SVG 资源按默认解析路径处理 | 边界 |

### US-4: 监听加载完成与失败

**作为** 应用开发者,
**我想要** 通过 onComplete/onError 回调监听图片片段加载完成与失败,
**以便** 可在加载成功后获取尺寸、失败时降级处理。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN 图片加载成功 THEN `onComplete(callback)`（API 12 dynamic / 23 static）回调触发，result 含 width/height/componentWidth/componentHeight/loadingStatus/contentWidth/contentHeight/contentOffsetX/contentOffsetY | 正常 |
| AC-4.2 | WHEN 图片加载失败 THEN `onError(callback)`（API 12 dynamic / 23 static）回调触发，event 含失败原因 | 异常 |
| AC-4.3 | WHEN 未注册 onComplete/onError THEN 加载完成/失败静默处理，不崩溃 | 边界 |

### US-5: 设置背景与基线偏移

**作为** 应用开发者,
**我想要** 通过 textBackgroundStyle/baselineOffset 设置图片片段的背景与基线偏移,
**以便** 图片片段可呈现背景色圆角与垂直微调。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-5.1 | WHEN 调用 `.textBackgroundStyle({ color, radius })`（继承 BaseSpan，API 11 dynamic / 23 static） THEN BaseSpan TextBackgroundStyle 写入，图片背景绘制 | 正常 |
| AC-5.2 | WHEN 调用 `.baselineOffset(10)`（继承 BaseSpan，API 12 dynamic / 23 static） THEN BaseSpan baselineOffset 写入，图片相对基线偏移 10vp | 正常 |

### US-6: 通过 NDK C-API 创建 ImageSpan 并设属性

**作为** 应用开发者,
**我想要** 通过 `ARKUI_NODE_IMAGE_SPAN` 节点类型与 `NODE_IMAGE_SPAN_*` 属性枚举创建并配置 ImageSpan,
**以便** C-API 场景下可使用图片片段。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-6.1 | WHEN NDK 调用创建 `ARKUI_NODE_IMAGE_SPAN`（`native_node.h:61`）节点 THEN 经 `image_span_modifier.cpp` → ImageSpan 动态模块构造 ImageSpanNode | 正常 |
| AC-6.2 | WHEN NDK 设置 `NODE_IMAGE_SPAN_SRC`（`:3244`）属性 THEN 图片源被设置 | 正常 |
| AC-6.3 | WHEN NDK 设置 `NODE_IMAGE_SPAN_VERTICAL_ALIGNMENT`（`:3258`）/`NODE_IMAGE_SPAN_ALT`（`:3272`）/`NODE_IMAGE_SPAN_BASELINE_OFFSET`（`:3284`）/`NODE_IMAGE_SPAN_COLOR_FILTER`（`:3301`）/`NODE_IMAGE_SPAN_SUPPORT_SVG2`（`:3314`） THEN 对应属性被下发 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-02 | XTS + 节点校验 | js_image.cpp:340/442/463 |
| AC-1.4 | R-4 | TASK-02 | XTS 占位符校验 | paragraph.h:290 |
| AC-2.1 | R-5 | TASK-02 | XTS verticalAlign 用例 | image_span_view.h:32 |
| AC-2.3 | R-6 | TASK-02 | XTS objectFit 用例 | image_span_view.h:31 |
| AC-3.1 | R-7 | TASK-02 | XTS colorFilter 用例 | image_span.d.ts @since 14 |
| AC-3.2 | R-8 | TASK-02 | XTS alt 用例 | image_span.d.ts @since 12 |
| AC-3.3 | R-9 | TASK-02 | XTS supportSvg2 用例 | image_span.d.ts @since 22 |
| AC-4.1 | R-10 | TASK-02 | XTS onComplete 用例 | image_span_view.h:46 |
| AC-4.2 | R-11 | TASK-02 | XTS onError 用例 | image_span_view.h:47 |
| AC-6.2 | R-13 | TASK-02 | NDK 用例 | native_node.h:3244 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在 Text 下声明 `ImageSpan(value)` | 经 JSImage::CreateImageSpan → CreateImage(isImageSpan=true) 构造 ImageSpanNode（FrameNode+ImagePattern），包装 ImageSpanItem（IMAGE 类型） | value 为 ResourceStr 或 PixelMap | AC-1.1/1.2 |
| R-2 | 边界 | ImageSpan 未挂 Text/RichEditor | 无父级 Paragraph 占位符消费，不渲染 | ImageSpan 不可独立布局 | AC-1.3 |
| R-3 | 行为 | ImageSpanItem 被父级布局消费 | 经 ImageLayoutAlgorithm 测量图像内在尺寸，Paragraph::AddPlaceholder 预留占位符槽位 | 槽位尺寸由 ImageSpanSize/ImageSpanOptions 决定 | AC-1.4 |
| R-4 | 行为 | 占位符槽位由 ImagePaintMethod 绘制 | 图片在槽位内按 objectFit 模式绘制 | 槽位=0 时图片不显示 | AC-1.4 |
| R-5 | 行为 | 调用 `.verticalAlign(ImageSpanAlignment)` | ImageSpanView::SetVerticalAlign 写入，图片按 BASELINE/TOP/BOTTOM 对齐 | 默认 BASELINE | AC-2.1/2.2 |
| R-6 | 行为 | 调用 `.objectFit(ImageFit)` | ImageSpanView::SetObjectFit 写入，图片按 Cover/Contain/Fill 等模式缩放 | 默认按 ImageFit 默认值 | AC-2.3/2.4 |
| R-7 | 行为 | 调用 `.colorFilter(ColorFilter \| DrawingColorFilter)`（API 14 dynamic / 23 static） | 图片应用颜色滤镜 | 滤镜参数无效时原图 | AC-3.1 |
| R-8 | 行为 | 调用 `.alt(PixelMap)`（API 12 dynamic / 23 static） | 加载失败显示占位 PixelMap | alt 为 null 时无占位 | AC-3.2 |
| R-9 | 行为 | 调用 `.supportSvg2(boolean)`（API 22 dynamic / 24 static） | 启用/关闭 SVG 二代解析 | 默认 false | AC-3.3/3.4 |
| R-10 | 行为 | 注册 `.onComplete(callback)` 且图片加载成功（API 12 dynamic / 23 static） | 回调触发，result 含 width/height/componentWidth/componentHeight/loadingStatus/contentWidth/contentHeight/contentOffsetX/contentOffsetY | loadingStatus 反映加载阶段 | AC-4.1 |
| R-11 | 异常 | 注册 `.onError(callback)` 且图片加载失败（API 12 dynamic / 23 static） | 回调触发，event 含失败原因 | 未注册时静默不崩溃 | AC-4.2/4.3 |
| R-12 | 行为 | 调用 `.textBackgroundStyle({ color, radius })`（继承 BaseSpan） | BaseSpan TextBackgroundStyle 写入 | radius 可为 Dimension 或 BorderRadiuses | AC-5.1 |
| R-12a | 行为 | 调用 `.baselineOffset(LengthMetrics)`（继承 BaseSpan） | BaseSpan baselineOffset 写入 | 负值下移 | AC-5.2 |
| R-13 | 行为 | NDK 创建 `ARKUI_NODE_IMAGE_SPAN` 并设 `NODE_IMAGE_SPAN_*` 属性 | 经 image_span_modifier.cpp → 动态模块构造与属性下发 | 仅暴露 SRC/VERTICAL_ALIGNMENT/ALT/BASELINE_OFFSET/COLOR_FILTER/SUPPORT_SVG2 六属性枚举 | AC-6.1/6.2/6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ImageSpan 创建 | XTS：声明 ImageSpan 后检查 ImageSpanNode+ImagePattern | isImageSpan=true 路径 |
| VM-2 | AC-1.3 无父级不渲染 | 负向用例：ImageSpan 挂 Column 不显示 | 无 Paragraph 占位 |
| VM-3 | AC-1.4 占位符槽位 | XTS：检查 Paragraph AddPlaceholder 调用 | paragraph.h:290 |
| VM-4 | AC-2.1~2.4 verticalAlign/objectFit | XTS：逐对齐/缩放模式截图比对 | ImageSpanView Set 方法 |
| VM-5 | AC-3.1 colorFilter | XTS API14+：滤镜变换 | @since 14 |
| VM-6 | AC-3.2 alt | XTS API12+：加载失败占位图 | @since 12 |
| VM-7 | AC-3.3 supportSvg2 | XTS API22+：SVG 二代解析 | @since 22 |
| VM-8 | AC-4.1~4.3 onComplete/onError | XTS：加载成功/失败回调 | result 字段完整性 |
| VM-9 | AC-6.1~6.3 NDK C-API | NDK 用例：创建节点+设属性 | NODE_IMAGE_SPAN_* 枚举 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|--------|
| `ImageSpan(value: ResourceStr \| PixelMap)` dynamic @since 10 / static @since 23 | Public | 图像源 | ImageSpanAttribute | N/A | 创建图片片段 | AC-1.1/1.2 |
| `ImageSpanAttribute.verticalAlign(ImageSpanAlignment)` @since 10 | Public | 垂直对齐 | ImageSpanAttribute | N/A | 设对齐 | AC-2.1 |
| `ImageSpanAttribute.objectFit(ImageFit)` @since 10 | Public | 缩放模式 | ImageSpanAttribute | N/A | 设缩放 | AC-2.3 |
| `ImageSpanAttribute.colorFilter(ColorFilter \| DrawingColorFilter)` @since 14 dynamic / 23 static | Public | 颜色滤镜 | ImageSpanAttribute | N/A | 设滤镜 | AC-3.1 |
| `ImageSpanAttribute.alt(PixelMap)` @since 12 dynamic / 23 static | Public | 占位图 | ImageSpanAttribute | N/A | 设占位图 | AC-3.2 |
| `ImageSpanAttribute.supportSvg2(Optional<boolean>)` @since 22 dynamic / 24 static | Public | SVG2 开关 | ImageSpanAttribute | N/A | 设 SVG2 | AC-3.3 |
| `BaseSpan.textBackgroundStyle(TextBackgroundStyle)` @since 11 dynamic / 23 static（继承） | Public | 背景 | ImageSpanAttribute | N/A | 设背景 | AC-5.1 |
| `BaseSpan.baselineOffset(LengthMetrics)` @since 12 dynamic / 23 static（继承） | Public | 基线偏移 | ImageSpanAttribute | N/A | 设基线偏移 | AC-5.2 |
| `ImageSpanAttribute.onComplete(ImageCompleteCallback)` @since 12 dynamic / 23 static | Public | 完成回调 | ImageSpanAttribute | N/A | 注册完成 | AC-4.1 |
| `ImageSpanAttribute.onError(ImageErrorCallback)` @since 12 dynamic / 23 static | Public | 失败回调 | ImageSpanAttribute | N/A | 注册失败 | AC-4.2 |
| `class ImageSpanModifier extends ImageSpanAttribute implements AttributeModifier<ImageSpanAttribute>` @since 12 dynamic / 23 static | Public | — | ImageSpanModifier | N/A | 动态属性载体 | AC-6.1 |
| NDK `ARKUI_NODE_IMAGE_SPAN` + `NODE_IMAGE_SPAN_SRC`/`VERTICAL_ALIGNMENT`/`ALT`/`BASELINE_OFFSET`/`COLOR_FILTER`/`SUPPORT_SVG2` | Public | C-API | ArkUI_NodeHandle | N/A | NDK 创建/设属性 | AC-6.2/6.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ImageSpanAttribute.alt` crossplatform | 变更 | API 23 dynamic 增 @crossplatform 标记 | 跨平台场景需 API 23+ | AC-3.2 |
| `ImageSpanAttribute.colorFilter` | 变更 | API 14 dynamic / 23 static 新增 DrawingColorFilter 重载 | 旧 ColorFilter 兼容 | AC-3.1 |

## 接口规格

### 接口定义

**ImageSpan 构造**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ImageSpan(value: ResourceStr \| PixelMap): ImageSpanAttribute`（dynamic @since 10 / static @since 23，@ComponentBuilder） |
| 返回值 | `ImageSpanAttribute`（继承 BaseSpan<ImageSpanAttribute>） |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1/1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ResourceStr \| PixelMap | 是 | 无 | Resource 解析失败走 onError；PixelMap 直接使用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 在 Text 下声明 ImageSpan($r) | 构造 ImageSpanNode+ImagePattern，挂载为子节点 | AC-1.1 |
| 2 | 传入 PixelMap | 以 PixelMap 为图像源 | AC-1.2 |
| 3 | 未挂 Text/RichEditor | 不渲染 | AC-1.3 |

> verticalAlign/objectFit/colorFilter/alt/supportSvg2/onComplete/onError 接口规格结构同 Span Feat-01 范式，参数约束与行为场景见规则定义 R-5~R-11，为节省篇幅不逐条展开。

## 兼容性声明

- **已有 API 行为变更:** 是。`alt` API 23 增 crossplatform 标记；`colorFilter` API 14 dynamic / 23 static 新增 DrawingColorFilter 重载；`supportSvg2` API 22 dynamic / 24 static 新增。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10（dynamic）/ API 23（static）
- **API 版本号策略:** 逐 API 标注 `@since`；dynamic 与 static 双态分别标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ImageSpan 必须挂载于 Text/RichEditor | 复用父级 Paragraph 占位符机制 | AC-1.3 |
| ImageSpanNode 复用 ImagePattern | 不存在独立 ImageSpanPattern；布局经 ImageLayoutAlgorithm，绘制经 ImagePaintMethod | AC-1.1/1.4 |
| 通用事件仅 onClick/onHover（继承 BaseSpan） | onTouch/onKeyEvent/onGesture 不支持 | — |
| NDK 仅暴露六属性枚举 | objectFit/onComplete/onError/borderRadius 不经 NDK NODE_IMAGE_SPAN_* 暴露 | AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 图片片段加载与占位符槽位分配耗时 ≤ 同等 Image 组件 | 帧率/trace | ImageLayoutAlgorithm 复用 |
| 内存 | ImageSpanItem 复用 ImageSpanOptions，不重复持有图像数据 | 内存 profile | span_node.h:1433 |
| 可靠性 | 图像源解析失败走 onError 不崩溃 | 异常用例 | image_span_view.h:47 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | 图片自适应由 ImagePattern 处理 | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 图片片段经父级 Text 暴露无障碍语义 | 父级 Text accessibility |
| 大字体 | 否 | 图片不随字体缩放 | — |
| 深色模式 | 是 | colorFilter/textBackgroundStyle 支持主题资源 | ResourceColor |
| 多窗口/分屏 | 否 | 图片片段行为随父级 Text | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 10→26 多版本演进 | 兼容性声明 |
| 生态兼容 | 是 | dynamic/static 双态并存 | static @since 23 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ImageSpan 图片片段
  作为 ArkUI 应用开发者
  我想要 在 Text 中插入行内图片片段
  以便 文本行内混合图片

  Scenario: 在 Text 下创建 ImageSpan
    Given Text 组件已挂载
    When 开发者声明 ImageSpan($r('app.media.icon'))
    Then 经 JSImage::CreateImageSpan 构造 ImageSpanNode（FrameNode+ImagePattern）
    And ImageSpanItem（IMAGE 类型）挂载为子节点
    And 父级 Paragraph 经 AddPlaceholder 预留占位符槽位

  Scenario Outline: ImageSpan 对齐与缩放
    Given ImageSpan 已创建
    When 调用 <方法>(<参数>)
    Then ImageSpanView::Set<方法> 写入
    And 图片按 <效果> 绘制

    Examples:
      | 方法 | 参数 | 效果 |
      | verticalAlign | BASELINE | 图片底部对齐文字基线 |
      | objectFit | Cover | 图片裁剪填充槽位 |

  Scenario: 图片加载失败
    Given ImageSpan 已注册 onError(callback)
    When 图片源解析/解码失败
    Then onError 回调触发，event 含失败原因
    And 若注册了 alt 则显示占位图
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "JSImage::CreateImageSpan 如何复用 CreateImage(isImageSpan=true) 路径构造 ImageSpanNode"
  - repo: "openharmony/arkui_ace_engine"
    query: "ImageSpanView 静态方法如何下发 verticalAlign/objectFit/colorFilter/alt 到 ImagePattern"
  - repo: "openharmony/arkui_ace_engine"
    query: "Paragraph::AddPlaceholder 如何为 ImageSpanItem 预留占位符槽位并由 ImagePaintMethod 绘制"
  - repo: "openharmony/interface_sdk-js"
    query: "image_span.d.ts 与 imageSpan.static.d.ets 的 dynamic/static 差异与 @since 版本"
  - repo: "openharmony/arkui_ace_engine"
    query: "ImageSpanBridge ArkTS-native 属性注册与动态模块加载机制"
```

**关键文档：** design.md；SDK `image_span.d.ts`/`imageSpan.static.d.ets`；`ImageSpanModifier.d.ts`
