# 特性规格

> Func-05-08-01-Feat-05 基础内存与加载上下文生命周期：固化 Image 组件当前 ImageSourceInfo 值存储、ImageLoadingContext 持有与释放、CanvasImage 重用判定、alt/altError 清理和 DFX 配置传递行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 基础内存与加载上下文生命周期 (Base Memory and Loading Context Lifecycle) |
| 特性编号 | Func-05-08-01-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 ace_engine 已有实现 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 修正 Feat-05 定位 | 从未落地的“基础内存优化”草稿改为当前实现的内存持有与生命周期规格。 |
| MODIFIED | 固化 ImageSourceInfo 当前值语义 | LayoutProperty 与 ImageLoadingContext 当前均按值保存 ImageSourceInfo，ImageDfxConfig 也按值嵌入。 |
| MODIFIED | 固化加载上下文释放点 | OnUnloaded、OnLoadSuccess、ClearAltData、主图加载成功后的 alt 清理均按当前源码描述。 |
| MODIFIED | 固化 CanvasImage 重用判定 | MakeCanvasImageIfNeed 依据 autoResize/imageFit/sourceSize/firstLoad/sizeLevel 决定是否重建 CanvasImage。 |
| MODIFIED | 记录未实现优化风险 | shared_ptr 共享 ImageSourceInfo/ImageDfxConfig、alt 状态合并、bool bitmask 等优化未在当前源码中落地，仅作为开放问题。 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `arkui-specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |
| Source | `frameworks/core/image/image_source_info.h/.cpp` | 已核对：ImageSourceInfo 字段、pixmapBuffer、reloadKey、比较逻辑 |
| Source | `frameworks/core/components_ng/pattern/image/image_layout_property.h` | 已核对：ImageSourceInfo 属性项存储 |
| Source | `frameworks/core/components_ng/image_provider/image_loading_context.h/.cpp` | 已核对：加载上下文字段、状态回调、释放和重用逻辑 |
| Source | `frameworks/core/components_ng/pattern/image/image_pattern.h/.cpp` | 已核对：主图/alt/altError 上下文、DFX 配置和清理逻辑 |

## 用户故事

### US-1: 明确图片源对象的当前内存持有方式

**作为** ArkUI 组件维护者,
**我想要** 明确 ImageSourceInfo 在属性层和加载上下文中的存储方式,
**以便** 后续变更能识别值拷贝、比较和 reloadKey 语义的兼容边界。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ImageLayoutProperty 保存主图、alt、altError、altPlaceholder 源信息 THEN 当前实现使用 `ImageSourceInfo` 值类型属性项 | 正常 |
| AC-1.2 | WHEN ImageLoadingContext 创建 THEN 构造函数按值复制传入的 `ImageSourceInfo` 到 `src_`，并把 `ImageDfxConfig` 写入该副本 | 正常 |
| AC-1.3 | WHEN ImageSourceInfo 来自 PixelMap THEN 当前实现保存 `pixmap_` RefPtr，并缓存 `pixmapBuffer_ = pixmap->GetPixels()` 用于相等比较 | 正常 |
| AC-1.4 | WHEN 比较两个 ImageSourceInfo THEN 比较 localColorMode、SVG fillColor、buffer、reloadKey、pixmapBuffer/raw pixel map、src 和 resourceId | 正常 |
| AC-1.5 | WHEN 相同 src/resourceId 但 reloadKey 不同 THEN `IsReloadKeyChanged` 返回 true，触发上层重载判定 | 正常 |

> 证据：ImageSourceInfo 字段 `frameworks/core/image/image_source_info.h:146-174`；LayoutProperty 属性项 `frameworks/core/components_ng/pattern/image/image_layout_property.h:50-65`；LoadingContext 构造 `frameworks/core/components_ng/image_provider/image_loading_context.cpp:34-40` 与成员 `image_loading_context.h:204-230`；pixmapBuffer 写入 `frameworks/core/image/image_source_info.cpp:150-174`, `image_source_info.cpp:177-205`；比较逻辑 `image_source_info.cpp:260-289`。

### US-2: 管理 ImageLoadingContext 资源生命周期

**作为** Image 加载管线维护者,
**我想要** 明确 ImageLoadingContext 持有哪些对象并在何时释放,
**以便** 避免加载状态切换、卸载和失败恢复时出现资源悬挂或重复持有。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN ImageLoadingContext 处于运行期 THEN 持有 `ImageSourceInfo src_`、`ImageObject imageObj_`、`CanvasImage canvasImage_`、LoadNotifier、尺寸/rect、sourceSizePtr 和 progress callback | 正常 |
| AC-2.2 | WHEN 进入 OnUnloaded THEN 清空 `imageObj_`、`canvasImage_`、srcRect、dstRect、dstSize | 恢复 |
| AC-2.3 | WHEN StaticImageObject 加载成功 THEN OnLoadSuccess 在通知上层前调用 `imageObj_->ClearData()` 释放静态图原始数据 | 恢复 |
| AC-2.4 | WHEN OnLoadSuccess 通知上层 THEN 传入当前 `src_`，随后把待执行的 MakeCanvasImage task 投递到 UI 线程 | 正常 |
| AC-2.5 | WHEN OnLoadFail 触发 THEN 通过 LoadNotifier 回传 `src_`、errorMsg 和 ImageErrorInfo | 异常 |
| AC-2.6 | WHEN DownloadOnProgress 被触发且存在 progress callback THEN 回调 `dlNow` 和 `dlTotal`；不存在回调时不做额外处理 | 边界 |

> 证据：成员字段 `frameworks/core/components_ng/image_provider/image_loading_context.h:204-234`, `image_loading_context.h:254`；OnUnloaded/OnLoadSuccess/OnLoadFail `frameworks/core/components_ng/image_provider/image_loading_context.cpp:90-115`；下载进度 `image_loading_context.cpp:131-134`, `image_loading_context.cpp:169-173`。

### US-3: 控制 CanvasImage 重建与解码尺寸

**作为** Image 渲染维护者,
**我想要** 明确 MakeCanvasImageIfNeed 的重建条件,
**以便** 图片尺寸频繁变化时避免不必要的 CanvasImage 重建，同时保证切片/源尺寸变化可见。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN autoResize、imageFit、sourceSize 或 firstLoadImage 发生变化 THEN MakeCanvasImageIfNeed 判定需要重新 MakeCanvasImage | 正常 |
| AC-3.2 | WHEN dstSize 变化 THEN 使用 RoundUp 后的 sizeLevel 与已有 sizeLevel 比较，仅 sizeLevel 变化时触发重建 | 边界 |
| AC-3.3 | WHEN 不需要重建且存在有效 resizable slice/lattice THEN 更新 dstSize 并调用 ResizableCalcDstSize 同步 srcRect/dstRect | 正常 |
| AC-3.4 | WHEN 当前状态已在 MAKE_CANVAS_IMAGE THEN 缓存 pendingMakeCanvasImageTask，后续再执行；否则立即 MakeCanvasImage | 边界 |
| AC-3.5 | WHEN sourceSizePtr 为空或 width/height <= 0 THEN GetSourceSize 返回 nullopt，并使用图片原始尺寸路径 | 边界 |

> 证据：MakeCanvasImageIfNeed `frameworks/core/components_ng/image_provider/image_loading_context.cpp:330-360`；MakeCanvasImage 参数延迟更新 `image_loading_context.cpp:362-370`；sourceSize 边界 `image_loading_context.cpp:431-445`。

### US-4: 管理主图、alt 和 altError 图像状态

**作为** Image 组件维护者,
**我想要** 明确主图、alt 和 altError 的上下文与图像对象持有关系,
**以便** 加载成功、失败回退和主图恢复时正确释放替代图资源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN ImagePattern 运行期 THEN 主图持有 `loadingCtx_`、`image_`、src/dst rect；alt 和 altError 分别持有独立 LoadingContext、CanvasImage 和 rect 指针 | 正常 |
| AC-4.2 | WHEN 主图 OnImageLoadSuccess 成功 THEN `image_ = loadingCtx_->MoveCanvasImage()`，设置 DFX/绘制配置，并调用 `ClearAltData()` 清理 alt/altError 数据 | 恢复 |
| AC-4.3 | WHEN ClearAltData 执行 THEN altLoadingCtx、altImage、altDstRect、altSrcRect、altErrorCtx、altErrorImage、altErrorDstRect、altErrorSrcRect 全部释放或 reset | 恢复 |
| AC-4.4 | WHEN alt 图加载成功 THEN alt CanvasImage 从 altLoadingCtx 移出，保存 alt src/dst rect，并设置绘制配置和动画回调 | 正常 |
| AC-4.5 | WHEN altError 图加载成功 THEN altError CanvasImage 从 altErrorCtx 移出，保存 altError src/dst rect，并设置绘制配置和动画回调 | 正常 |
| AC-4.6 | WHEN OnImageLoadFail 发现 AltError 已配置 THEN 启动 altError 加载，再派发失败事件 | 异常 |

> 证据：Pattern 字段 `frameworks/core/components_ng/pattern/image/image_pattern.h:386-415`；主图成功清理 `frameworks/core/components_ng/pattern/image/image_pattern.cpp:489-525`；ClearAltData `image_pattern.cpp:411-422`；alt 成功 `image_pattern.cpp:1565-1598`；altError 成功 `image_pattern.cpp:3021-3098`；失败加载 altError `image_pattern.cpp:709-729`。

### US-5: 保持 DFX 配置与回调持有的当前语义

**作为** 维测和性能维护者,
**我想要** 明确 ImageDfxConfig 与回调成员当前是值或函数对象持有,
**以便** 后续内存优化不破坏日志、性能上报和下载进度事件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Pattern 创建主图加载上下文 THEN `imageDfxConfig_` 按值保存，并传入 ImageLoadingContext 写入 `src_` 的 ImageDfxConfig | 正常 |
| AC-5.2 | WHEN alt 或 altError 创建加载上下文 THEN `altImageDfxConfig_`/`altErrorImageDfxConfig_` 按值保存，并传入对应 LoadingContext | 正常 |
| AC-5.3 | WHEN CanvasImage 创建成功 THEN Pattern 把当前 ImageDfxConfig 设置到主图、alt 或 altError CanvasImage | 正常 |
| AC-5.4 | WHEN NDK 下载进度回调先设置到 Pattern THEN StartLoading 时把 `onProgressCallback_` 移入 loadingCtx | 正常 |
| AC-5.5 | WHEN 未设置下载进度回调 THEN Pattern 和 LoadingContext 中对应 function 为空，不产生下载进度通知 | 边界 |

> 证据：Pattern DFX 字段 `frameworks/core/components_ng/pattern/image/image_pattern.h:413-415`；主图加载上下文创建 `frameworks/core/components_ng/pattern/image/image_pattern.cpp:1148-1152`；alt 创建 `image_pattern.cpp:1184-1188`；altError 创建 `image_pattern.cpp:3029-3035`；CanvasImage DFX 设置 `image_pattern.cpp:515`, `image_pattern.cpp:1587`, `image_pattern.cpp:3092`；进度回调迁移 `image_pattern.cpp:1158-1160`, `image_pattern.cpp:2721-2724`。

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1, R-2, R-3, R-4 | 无 | 代码审查 + 单元测试 | `image_source_info.h:146-174`, `image_layout_property.h:50-65`, `image_source_info.cpp:260-289` |
| AC-2.1~2.6 | R-5, R-6, R-7, R-8 | 无 | 代码审查 + 单元测试 | `image_loading_context.h:204-234`, `image_loading_context.cpp:90-115`, `image_loading_context.cpp:169-173` |
| AC-3.1~3.5 | R-9, R-10, R-11 | 无 | 单元测试 | `image_loading_context.cpp:330-360`, `image_loading_context.cpp:431-445` |
| AC-4.1~4.6 | R-12, R-13, R-14, R-15 | 无 | 单元测试 + 代码审查 | `image_pattern.h:386-415`, `image_pattern.cpp:411-422`, `image_pattern.cpp:489-525` |
| AC-5.1~5.5 | R-16, R-17, R-18 | 无 | 代码审查 + C API UT | `image_pattern.cpp:1148-1160`, `image_pattern.cpp:1184-1188`, `image_pattern.cpp:3029-3035` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | LayoutProperty 保存图片源 | 主图、alt、altError、altPlaceholder 均以 `ImageSourceInfo` 值类型属性项保存 | 当前源码不是 shared_ptr 持有 | AC-1.1 |
| R-2 | 行为 | 创建 ImageLoadingContext | 构造函数复制 `ImageSourceInfo` 到 `src_`，并把 `ImageDfxConfig` 写入 `src_` | 后续 source 比对基于该副本 | AC-1.2, AC-5.1~AC-5.2 |
| R-3 | 行为 | PixelMap source 构造 | `pixmap_` 持有 PixelMap，`pixmapBuffer_` 缓存像素地址用于相等比较 | pixmapBuffer 当前仍存在，未移除 | AC-1.3~AC-1.4 |
| R-4 | 行为 | reloadKey 不同 | `operator==` 比较 reloadKey，`IsReloadKeyChanged` 在 src/resourceId 相同时识别 reloadKey 变化 | reloadKey 为空与非空参与比较 | AC-1.4~AC-1.5 |
| R-5 | 恢复 | LoadingContext 进入 Unloaded 状态 | 清空 ImageObject、CanvasImage 和 rect/size 缓存 | 不修改 `src_` 和 LoadNotifier | AC-2.2 |
| R-6 | 恢复 | StaticImageObject 加载成功 | 先清理静态图原始数据，再通知 onLoadSuccess | 仅 DynamicCast<StaticImageObject> 成功时执行 | AC-2.3~AC-2.4 |
| R-7 | 异常 | LoadingContext 加载失败 | 通过 notifier 回传 src、errorMsg、ImageErrorInfo | 上层 Pattern 决定是否派发 onError 和 altError | AC-2.5, AC-4.6 |
| R-8 | 边界 | 下载进度回调为空 | `DownloadOnProgress` 不触发外部回调 | 仅 function 存在时回调 | AC-2.6, AC-5.5 |
| R-9 | 行为 | MakeCanvasImageIfNeed 参数变化 | autoResize、imageFit、sourceSize、firstLoadImage 任一变化会触发重建 | dstSize 变化还需 sizeLevel 判断 | AC-3.1~AC-3.2 |
| R-10 | 边界 | 当前正在 MAKE_CANVAS_IMAGE | 保存 pendingMakeCanvasImageTask，待当前流程结束后执行 | 避免重入 MakeCanvasImage | AC-3.4 |
| R-11 | 边界 | sourceSize 为空或非正 | GetSourceSize 返回 nullopt，并记录 Invalid SourceSize 日志 | width/height 必须都 > 0 才作为有效 sourceSize | AC-3.5 |
| R-12 | 行为 | Pattern 持有图片状态 | 主图、alt、altError 使用三组 LoadingContext/CanvasImage/rect 字段持有 | 未合并为单独的 alt 状态对象 | AC-4.1 |
| R-13 | 恢复 | 主图加载成功 | 主图 CanvasImage 移出并配置后，调用 ClearAltData 释放 alt/altError 临时资源 | 保证主图恢复后替代图不继续持有 | AC-4.2~AC-4.3 |
| R-14 | 行为 | alt 或 altError 加载成功 | 从各自 LoadingContext 移出 CanvasImage、缓存 rect、设置 PaintConfig 和动画回调 | alt 与 altError 使用独立 DFX 配置 | AC-4.4~AC-4.5, AC-5.2~AC-5.3 |
| R-15 | 异常 | 主图加载失败且配置 AltError | Pattern 启动 AltError 加载并继续派发失败事件 | AltError 加载不吞掉主图失败事件 | AC-4.6 |
| R-16 | 行为 | DFX 配置流转 | Pattern、ImageSourceInfo、CanvasImage 当前按值传递或保存 ImageDfxConfig | 未实现 shared_ptr 共享 | AC-5.1~AC-5.3 |
| R-17 | 行为 | NDK 下载进度回调注册 | Pattern 先保存 `onProgressCallback_`，StartLoading 创建 loadingCtx 后移入 loadingCtx | 移动后 Pattern 成员不再持有该回调 | AC-5.4 |
| R-18 | 边界 | 未注册下载进度 | Pattern/LoadingContext 的 function 为空，ImageProvider 任务 `hasProgressCallback=false` | 不生成下载进度事件 | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5 (ImageSourceInfo 值语义) | 代码审查 + 单元测试 | LayoutProperty 值属性、pixmapBuffer 比较、reloadKey 变化判定 |
| VM-2 | AC-2.1~2.6 (LoadingContext 生命周期) | 单元测试 | OnUnloaded 清理、StaticImageObject ClearData、progress callback 空/非空 |
| VM-3 | AC-3.1~3.5 (CanvasImage 重建) | 单元测试 | autoResize/imageFit/sourceSize/sizeLevel/pending task 分支 |
| VM-4 | AC-4.1~4.6 (主图与 alt 状态) | 单元测试 + 代码审查 | ClearAltData、主图成功释放替代图、altError 失败链 |
| VM-5 | AC-5.1~5.5 (DFX 与回调持有) | 代码审查 + C API UT | DFX 值传递、CanvasImage 设置、下载进度回调迁移 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| N/A | N/A | N/A | N/A | N/A | 本特性为内部生命周期规格补录，无新增 ArkTS/C API | N/A |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | N/A | 当前实现不改变公开 API | N/A | N/A |

## 接口规格

### 接口定义

**ImageLoadingContext 生命周期接口（内部）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ImageLoadingContext(const ImageSourceInfo& src, LoadNotifier&& loadNotifier, bool syncLoad, bool isSceneBoardWindow, const ImageDfxConfig& imageDfxConfig)` |
| 返回值 | N/A，构造内部加载上下文 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2, AC-2.1~AC-2.6, AC-5.1~AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| src | const ImageSourceInfo& | 是 | N/A | 构造时复制到 `src_`；后续 notifier 使用该副本。 |
| loadNotifier | LoadNotifier&& | 是 | N/A | 包含 dataReady/loadSuccess/loadFail 等回调，移动保存。 |
| syncLoad | bool | 否 | false | API < 12 且 PixelMap source 时构造内可强制同步加载。 |
| isSceneBoardWindow | bool | 否 | false | 影响加载/解码路径的 SceneBoard 语义。 |
| imageDfxConfig | const ImageDfxConfig& | 是 | N/A | 写入 `src_` 的 ImageDfxConfig 值副本。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 构造 LoadingContext | 复制 src，保存 notifier，写入 DFX 配置 | AC-1.2, AC-5.1 |
| 2 | 状态进入 Unloaded | 清理 ImageObject/CanvasImage/rect/size | AC-2.2 |
| 3 | 下载进度回调触发 | 有 callback 时转发 dlNow/dlTotal，无 callback 时不处理 | AC-2.6 |

**MakeCanvasImageIfNeed（内部）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool MakeCanvasImageIfNeed(const SizeF& dstSize, bool autoResize, ImageFit imageFit, const std::optional<SizeF>& sourceSize, bool hasValidSlice)` |
| 返回值 | `bool`，表示是否触发 MakeCanvasImage |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| dstSize | SizeF | 是 | N/A | 非正或 sizeLevel 未变化可能不触发重建。 |
| autoResize | bool | 是 | N/A | 与上次值不同则触发重建。 |
| imageFit | ImageFit | 是 | COVER | 与上次值不同则触发重建。 |
| sourceSize | optional<SizeF> | 否 | nullopt | width/height 必须都 > 0 才有效。 |
| hasValidSlice | bool | 是 | false | 不重建时仍可触发 ResizableCalcDstSize 同步 rect。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 参数或 firstLoadImage 变化 | 返回 true 并执行或排队 MakeCanvasImage | AC-3.1, AC-3.4 |
| 2 | dstSize 变化但 sizeLevel 不变 | 不因尺寸变化重建 CanvasImage | AC-3.2 |
| 3 | sourceSize 非正 | 按 nullopt 处理 | AC-3.5 |

**ClearAltData（内部）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ImagePattern::ClearAltData()` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.2~AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| N/A | N/A | N/A | N/A | 无入参，操作 ImagePattern 当前 alt/altError 成员。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 主图加载成功 | 清空 alt 和 altError 上下文、图像与 rect | AC-4.2~AC-4.3 |
| 2 | alt/altError 未初始化 | reset/null 赋值保持幂等 | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否，本特性为当前内部生命周期补录，不改变 ArkTS/C API。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 跟随 Image 组件已有实现；无新增 SDK 版本。
- **API 版本号策略:** N/A；所有行为为内部实现规格，公开 API 版本见 Feat-01~Feat-04。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 当前实现即规格 | 不把未落地的 shared_ptr/bitmask 优化写入验收标准；仅记录开放问题 | AC-1.1~AC-5.5 |
| 值语义比较约束 | ImageSourceInfo 当前相等比较依赖 pixmapBuffer、raw pixel map、reloadKey 等字段 | AC-1.3~AC-1.5 |
| 回调源匹配约束 | Pattern 回调先比较当前 LayoutProperty source 与回调 source，避免过期加载结果污染当前节点 | AC-1.2, AC-2.5 |
| 主图优先清理约束 | 主图加载成功后必须清理 alt/altError 状态，避免替代图资源继续被 Pattern 持有 | AC-4.2~AC-4.3 |
| 状态机重入约束 | MAKE_CANVAS_IMAGE 状态下使用 pending task，避免重入创建 CanvasImage | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | MakeCanvasImageIfNeed 不因每次 dstSize 小幅变化都重建 CanvasImage，使用 sizeLevel 降低重建频率 | 单元测试 + 代码审查 | `image_loading_context.cpp:330-360` |
| 功耗 | N/A，本规格不改变解码线程或下载策略 | 代码审查 | N/A |
| 内存 | OnUnloaded、StaticImageObject ClearData、ClearAltData 明确释放临时持有对象 | 单元测试 + 代码审查 | `image_loading_context.cpp:90-108`, `image_pattern.cpp:411-422` |
| 安全 | N/A，不涉及外部权限或跨进程数据 | 代码审查 | N/A |
| 可靠性 | source 匹配检查防止旧加载回调影响新 source | 单元测试 + 代码审查 | `image_pattern.cpp:159-213` |
| 可测试性 | 可通过 ImagePattern/ImageLoadingContext 单元测试覆盖主要分支 | 单元测试 | `test/unittest/core/pattern/image/` |
| 自动化维测 | DFX 配置继续按值传递到 source 与 CanvasImage，维测日志字段保持可用 | 代码审查 | `image_pattern.cpp:1148-1152`, `image_pattern.cpp:515` |
| 定界定位 | reloadKey、source 比较和 DFX ToString 信息支持定位重复加载与过期回调 | 代码审查 | `image_source_info.cpp:286-289`, `image_pattern.cpp:2090` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无设备专属差异 | 内部生命周期一致 | 单元测试 | `image_loading_context.cpp:90-115` |
| 平板 | 无设备专属差异 | 内部生命周期一致 | 单元测试 | `image_loading_context.cpp:90-115` |
| 折叠屏 | 无设备专属差异 | dstSize/GeometryNode 变化可能触发 sizeLevel 判定，但规则一致 | 单元测试 | `image_loading_context.cpp:330-360` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 内部资源生命周期不改变无障碍语义 | N/A |
| 大字体 | 否 | 不涉及文本测量 | N/A |
| 深色模式 | 是 | ImageSourceInfo 比较包含 localColorMode，颜色模式变化会影响源相等性 | AC-1.4 |
| 多窗口/分屏 | 是 | dstSize 变化通过 MakeCanvasImageIfNeed 和 sizeLevel 处理 | AC-3.1~AC-3.4 |
| 多用户 | 否 | 不涉及用户态持久化 | N/A |
| 版本升级 | 是 | 现有值语义和 DFX 值拷贝是当前兼容基线，未来优化需保留行为 | AC-1.1~AC-5.5 |
| 生态兼容 | 是 | reloadKey、PixelMap 引用比较和 alt 清理顺序影响开发者可见刷新/回退行为 | AC-1.3~AC-1.5, AC-4.2~AC-4.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 基础内存与加载上下文生命周期

  Scenario: ImageLoadingContext 构造保存 source 副本
    Given 一个 ImageSourceInfo 和 ImageDfxConfig
    When 创建 ImageLoadingContext
    Then context 按值保存 ImageSourceInfo 到 src_
    And src_ 中写入 ImageDfxConfig 值副本

  Scenario: StaticImageObject 加载成功释放原始数据
    Given ImageLoadingContext 持有 StaticImageObject
    When OnLoadSuccess 执行
    Then StaticImageObject.ClearData 被调用
    And onLoadSuccess notifier 收到当前 src_

  Scenario: MakeCanvasImageIfNeed 避免重复重建
    Given ImageLoadingContext 已有 dstSize 和 sizeLevel
    When 新 dstSize 变化但 RoundUp 后 sizeLevel 未变化
    And autoResize、imageFit、sourceSize 都未变化
    Then 不重新 MakeCanvasImage

  Scenario: 主图成功后清理替代图状态
    Given ImagePattern 同时持有 altLoadingCtx 和 altErrorCtx
    When 主图 OnImageLoadSuccess 成功
    Then ClearAltData 清空 alt 和 altError 的 LoadingContext、CanvasImage 和 rect
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（内部生命周期补录，不包含未实现优化作为 AC）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ImageSourceInfo value storage pixmapBuffer reloadKey ImageLoadingContext lifecycle"
  - repo: "openharmony/arkui_ace_engine"
    query: "ImagePattern ClearAltData altLoadingCtx altErrorCtx ImageDfxConfig"
```

**关键文档：** `design.md`（同目录）、`docs/kb/components/media/image.md`（Image 组件 KB）
