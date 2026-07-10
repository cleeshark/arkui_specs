# 特性规格

> Func-05-08-01-Feat-04 事件回调：固化 onComplete、onError、onFinish 三个 ArkTS 事件，以及 NDK `NODE_IMAGE_ON_COMPLETE`、`NODE_IMAGE_ON_ERROR`、`NODE_IMAGE_ON_SVG_PLAY_FINISH`、`NODE_IMAGE_ON_DOWNLOAD_PROGRESS` 四个节点事件的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件回调 (Event Callbacks) |
| 特性编号 | Func-05-08-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起支持，API 9/10/11/23 有事件字段或范式扩展 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐事件 API 版本与多范式入口 | 动态 ArkTS、静态 ArkTS 与 NDK 节点事件均已核对 SDK/C API 声明。 |
| MODIFIED | 修正 onFinish 语义 | SDK 合约限定为 SVG 动画播放完成；当前实现对非静态 CanvasImage 注册完成回调，作为 SDK/实现差异记录。 |
| MODIFIED | 补齐 NDK 下载进度事件 | `NODE_IMAGE_ON_DOWNLOAD_PROGRESS` 仅属于 NDK 节点事件，不是 ArkTS ImageAttribute 事件。 |
| MODIFIED | 补齐事件 payload 映射 | 明确 ArkTS `ImageCompleteEvent`/`ImageError` 字段，以及 NDK `ArkUI_NodeComponentEvent.data[]` 下标。 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `arkui-specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/image.d.ts` | 已核对：onComplete/onError/onFinish 声明和事件字段 |
| Static SDK | `interface/sdk-js/api/arkui/component/image.static.d.ets` | 已核对：静态 onComplete/onError/onFinish 声明 |
| C API | `interfaces/native/native_node.h` | 已核对：四个 Image 节点事件枚举与 payload |
| Source | `frameworks/core/components_ng/pattern/image/image_pattern.cpp` | 已核对：加载成功、失败、动画完成、下载进度回调链路 |

## 用户故事

### US-1: 监听图片加载完成

**作为** 应用开发者,
**我想要** 通过 onComplete 回调获取图片加载成功后的详细信息,
**以便** 根据图片实际尺寸、组件尺寸、内容区域和偏移量进行后续处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.onComplete(callback: ImageOnCompleteCallback)` THEN 回调注册到 ImageEventHub，并在成功事件中返回 `ImageCompleteEvent` | 正常 |
| AC-1.2 | WHEN 图片数据就绪并完成布局回调 THEN 触发 onComplete，`loadingStatus=0`，事件包含原图尺寸、组件尺寸、content 尺寸和 content offset | 正常 |
| AC-1.3 | WHEN 图片完整解码并生成 CanvasImage 成功 THEN 触发 onComplete，`loadingStatus=1`，事件 content 区域来自 `CalcImageContentPaintSize` | 正常 |
| AC-1.4 | WHEN onComplete 参数不是函数或回调未注册 THEN EventHub 不保存有效回调，加载流程继续执行 | 边界 |
| AC-1.5 | WHEN iOS 平台已存在 onComplete 回调后再次注册 THEN `ImageEventHub::SetOnComplete` 保留首次回调并直接返回 | 边界 |

> SDK 字段声明：动态 `interface/sdk-js/api/@internal/component/ets/image.d.ts:1388-1644`，静态 `interface/sdk-js/api/arkui/component/image.static.d.ets:855-865`。JS 事件转换：`frameworks/bridge/declarative_frontend/jsview/js_image.cpp:118-130`；事件数据结构：`frameworks/core/components/image/image_event.h:24-93`；触发点：`frameworks/core/components_ng/pattern/image/image_pattern.cpp:234-247`, `image_pattern.cpp:489-555`。

### US-2: 监听图片加载失败

**作为** 应用开发者,
**我想要** 通过 onError 回调获取图片加载失败信息,
**以便** 识别加载失败原因并进入替代图处理流程。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.onError(callback: ImageErrorCallback)` THEN 回调注册到 ImageEventHub，并在失败事件中返回 `ImageError` | 异常 |
| AC-2.2 | WHEN 主图加载或解码失败且 source 未来自 ResetImage THEN `OnImageLoadFail` 触发 onError | 异常 |
| AC-2.3 | WHEN onError 触发 THEN ArkTS event 包含 `componentWidth`、`componentHeight`、`message`、`error`，网络错误场景可包含 `downloadInfo` | 异常 |
| AC-2.4 | WHEN onError 触发且配置了 `AltError` THEN 先启动 altError 加载，再派发 onError 事件 | 异常 |
| AC-2.5 | WHEN 回调未注册 THEN EventHub 不执行外部回调，Image 失败处理和 alt/altError 流程仍按 Pattern 逻辑执行 | 边界 |
| AC-2.6 | WHEN 图片源类型为 AnimatedDrawableDescriptor THEN SDK 声明 onError 不触发 | 边界 |

> SDK 声明：`interface/sdk-js/api/@internal/component/ets/image.d.ts:1646-1667`，静态 `interface/sdk-js/api/arkui/component/image.static.d.ets:867-881`。JS 转换：`frameworks/bridge/declarative_frontend/jsview/js_image.cpp:133-160`；错误结构：`frameworks/base/image/image_defines.h:40-71`；触发点：`frameworks/core/components_ng/pattern/image/image_pattern.cpp:195-213`, `image_pattern.cpp:709-729`。

### US-3: 监听 SVG 动画播放完成

**作为** 应用开发者,
**我想要** 通过 onFinish 回调获知 SVG 动画播放完成,
**以便** 在有限循环 SVG 动画结束后执行后续逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.onFinish(event: () => void)` THEN 回调注册为 ImageEventHub 的 FinishEvent | 正常 |
| AC-3.2 | WHEN 已加载 SVG 图片的动画播放完成且不是无限循环 THEN SDK 合约要求触发 onFinish | 正常 |
| AC-3.3 | WHEN 图片源为静态图片 THEN `PrepareAnimation` 直接返回，不注册 CanvasImage 完成回调 | 边界 |
| AC-3.4 | WHEN CanvasImage 非静态 THEN 当前实现调用 `SetOnFinishCallback`，动画完成时由 CanvasImage 回调触发 EventHub | 正常 |
| AC-3.5 | WHEN 图片源类型为 AnimatedDrawableDescriptor THEN SDK 声明 onFinish 不触发 | 边界 |

> onFinish SDK 合约限定 SVG：动态 `interface/sdk-js/api/@internal/component/ets/image.d.ts:1669-1686`，静态 `interface/sdk-js/api/arkui/component/image.static.d.ets:883-899`，NDK `NODE_IMAGE_ON_SVG_PLAY_FINISH`：`interfaces/native/native_node.h:10521-10529`。当前实现对非静态 CanvasImage 注册完成回调：`frameworks/core/components_ng/pattern/image/image_pattern.cpp:259-280`，此差异列入风险表。

### US-4: 通过 NDK 监听 Image 节点事件

**作为** NDK 开发者,
**我想要** 通过 ArkUI NodeEvent 监听 Image 加载、失败、SVG 播放完成和下载进度,
**以便** 在 C API 场景下获得与组件事件对应的状态数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 注册 `NODE_IMAGE_ON_COMPLETE` THEN `ArkUI_NodeComponentEvent.data[0..8]` 依次返回 loadingStatus、原图宽高、组件宽高、内容偏移和内容宽高 | 正常 |
| AC-4.2 | WHEN 注册 `NODE_IMAGE_ON_ERROR` 且加载失败 THEN `data[0].i32` 返回错误码；当前 node modifier 固定填入 401 | 异常 |
| AC-4.3 | WHEN 注册 `NODE_IMAGE_ON_SVG_PLAY_FINISH` 且 SVG 动画完成 THEN 事件无 data 参数 | 正常 |
| AC-4.4 | WHEN 注册 `NODE_IMAGE_ON_DOWNLOAD_PROGRESS` 且网络图片下载进度回调存在 THEN `data[0].u32=dlNow`，`data[1].u32=dlTotal` | 正常 |
| AC-4.5 | WHEN 网络图片未开启下载进度回调 THEN ImageProvider 创建下载任务时 `hasProgressCallback=false`，不派发下载进度事件 | 边界 |

> NDK 事件声明：`interfaces/native/native_node.h:10508-10540`。node modifier 映射：`frameworks/core/interfaces/native/node/node_image_modifier.cpp:1660-1725`，错误固定码：`node_image_modifier.cpp:48`，事件 data 下标：`node_image_modifier.cpp:49-55`。下载进度链路：`frameworks/core/components_ng/pattern/image/image_model_ng.cpp:899-905`，`frameworks/core/components_ng/pattern/image/image_pattern.cpp:1158-1160`，`frameworks/core/components_ng/image_provider/image_provider.cpp:439-447`。

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1, R-2, R-3, R-10 | 无 | XTS + 代码审查 | `image.d.ts:1388-1644`, `js_image.cpp:118-130`, `image_pattern.cpp:234-247`, `image_pattern.cpp:489-555` |
| AC-2.1~2.6 | R-4, R-5, R-6 | 无 | XTS + 代码审查 | `image.d.ts:1646-1667`, `js_image.cpp:133-160`, `image_pattern.cpp:709-729` |
| AC-3.1~3.5 | R-7, R-8, R-11 | 无 | XTS + 代码审查 | `image.d.ts:1669-1686`, `image.static.d.ets:883-899`, `image_pattern.cpp:259-280` |
| AC-4.1~4.5 | R-9, R-12, R-13 | 无 | C API UT + 代码审查 | `native_node.h:10508-10540`, `node_image_modifier.cpp:1660-1725`, `image_provider.cpp:439-447` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 注册 onComplete 且图片数据就绪/解码成功 | ImagePattern 通过 ImageEventHub 触发 `LoadImageSuccessEvent`，`loadingStatus=0` 表示数据加载完成，`loadingStatus=1` 表示解码成功 | 成功回调后不再访问内部成员，避免外部回调导致节点销毁后继续使用 | AC-1.1~AC-1.3 |
| R-2 | 行为 | `loadingStatus=0` 的 onComplete 触发 | 事件尺寸来自 `loadingCtx_->GetImageSize()` 与 GeometryNode frame/content 信息 | 仅在 `onDataReadyComplete_` 通知路径触发 | AC-1.2 |
| R-3 | 行为 | `loadingStatus=1` 的 onComplete 触发 | 事件内容区域来自 `CalcImageContentPaintSize`，并包含 content offset | 触发前已移动 CanvasImage、设置绘制配置、清理 alt 数据 | AC-1.3 |
| R-4 | 异常 | 图片加载或解码失败 | Pattern 构造 `LoadImageFailEvent` 并触发 onError | ResetImage 来源失败不触发 Pattern 失败处理 | AC-2.1~AC-2.3 |
| R-5 | 恢复 | 失败时存在 `AltError` | Pattern 先调用 `LoadAltErrorImage` 启动错误图加载，再派发 onError | onError 不阻塞错误图加载流程 | AC-2.4~AC-2.5 |
| R-6 | 行为 | ArkTS onError 事件转换 | JS 事件包含 `componentWidth`、`componentHeight`、`message`、`error.code`、`error.message`，存在下载信息时补充 `downloadInfo` | `downloadInfo` 在无下载信息、无 engine 或 SceneBoard 窗口中不暴露 | AC-2.3 |
| R-7 | 行为 | 注册 onFinish 且 CanvasImage 完成动画 | EventHub 的 FinishEvent 被调用，无事件参数 | SDK 合约限定 SVG 动画完成 | AC-3.1~AC-3.4 |
| R-8 | 边界 | 图片为静态图片 | `PrepareAnimation` 判断 `image->IsStatic()` 后直接返回，不设置 redraw/finish 回调 | 静态 PNG/JPEG 不触发 onFinish | AC-3.3 |
| R-9 | 行为 | 注册 NDK Image 节点事件 | node modifier 将 C++ 事件转为 `ArkUINodeEvent`，通过 `SendArkUISyncEvent` 同步派发 | NDK payload 下标与 `native_node.h` 声明保持一致 | AC-4.1~AC-4.4 |
| R-10 | 边界 | iOS 平台重复注册 onComplete | `ImageEventHub::SetOnComplete` 在已有回调时直接返回 | 仅 iOS 平台有该保护 | AC-1.5 |
| R-11 | 边界 | onFinish 用于非 SVG 动画图片 | 当前实现对非静态 CanvasImage 都注册 finish 回调；SDK 只承诺 SVG，差异需作为兼容风险记录 | 不修改实现，仅文档显式标注 | AC-3.2~AC-3.4 |
| R-12 | 异常 | NDK onError 触发 | 当前 node modifier 固定返回 `LOAD_ERROR_CODE=401`，不透传 `ImageErrorInfo` 细分错误码 | 与 ArkTS `ImageError.error.code` 信息粒度不同 | AC-4.2 |
| R-13 | 边界 | 网络图片下载未携带进度回调 | `ImageProvider::CreateImageObject` 使用是否存在 progress callback 拼接 taskKey，并仅在 `hasProgressCallback=true` 时设置下载进度回调 | 非网络源或未开启下载能力不产生进度事件 | AC-4.4~AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.5 (onComplete) | XTS + 代码审查 | loadingStatus 0/1 两次触发、字段完整性、iOS 重复注册保护 |
| VM-2 | AC-2.1~2.6 (onError) | XTS + 代码审查 | 失败事件字段、BusinessError、downloadInfo、altError 触发顺序 |
| VM-3 | AC-3.1~3.5 (onFinish) | XTS + 代码审查 | SVG SDK 合约、静态图片不触发、当前非静态 CanvasImage 实现差异 |
| VM-4 | AC-4.1~4.5 (NDK events) | C API UT + 代码审查 | `ArkUI_NodeComponentEvent.data[]` 下标、401 错误码、下载进度 dlNow/dlTotal |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `onComplete(callback: ImageOnCompleteCallback)` | Public | 回调参数为 ImageCompleteEvent | ImageAttribute/this | N/A | 图片数据加载完成和解码成功回调 | AC-1.1~AC-1.5 |
| `onError(callback: ImageErrorCallback)` | Public | 回调参数为 ImageError | ImageAttribute/this | ImageErrorCode | 图片加载失败回调 | AC-2.1~AC-2.6 |
| `onFinish(event: () => void)` | Public | 无参回调 | ImageAttribute/this | N/A | SVG 动画播放完成回调 | AC-3.1~AC-3.5 |
| `NODE_IMAGE_ON_COMPLETE` | Public C API | ArkUI node event | ArkUI_NodeEvent | N/A | NDK 图片加载/解码成功事件 | AC-4.1 |
| `NODE_IMAGE_ON_ERROR` | Public C API | ArkUI node event | ArkUI_NodeEvent | 401, 103101（声明）；当前实现固定 401 | NDK 图片加载失败事件 | AC-4.2 |
| `NODE_IMAGE_ON_SVG_PLAY_FINISH` | Public C API | ArkUI node event | ArkUI_NodeEvent | N/A | NDK SVG 动画播放完成事件 | AC-4.3 |
| `NODE_IMAGE_ON_DOWNLOAD_PROGRESS` | Public C API | ArkUI node event | ArkUI_NodeEvent | N/A | NDK 网络图片下载进度事件 | AC-4.4~AC-4.5 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | N/A | 已有能力补录，无 API 变更/废弃 | N/A | N/A |

## 接口规格

### 接口定义

**onComplete(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onComplete(callback: ImageOnCompleteCallback): ImageAttribute` |
| 返回值 | `ImageAttribute`/`this`，支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | ImageOnCompleteCallback | 是 | 未注册 | 动态 JSView 仅在参数为函数时注册；静态 API 允许 undefined。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 数据加载完成且布局完成 | 触发 `loadingStatus=0` 的成功事件 | AC-1.2 |
| 2 | 解码和 CanvasImage 创建成功 | 触发 `loadingStatus=1` 的成功事件 | AC-1.3 |
| 3 | iOS 平台重复注册 | 保留首次注册回调 | AC-1.5 |

**onError(callback)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onError(callback: ImageErrorCallback): ImageAttribute` |
| 返回值 | `ImageAttribute`/`this`，支持链式调用 |
| 开放范围 | Public |
| 错误码 | ImageErrorCode |
| 关联 AC | AC-2.1~AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | ImageErrorCallback | 是 | 未注册 | 动态 JSView 仅在参数为函数时注册；AnimatedDrawableDescriptor 按 SDK 声明不触发。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 主图加载失败 | 触发 ImageError，包含组件尺寸和错误信息 | AC-2.2~AC-2.3 |
| 2 | 失败且存在 AltError | 先启动 AltError 加载，再派发 onError | AC-2.4 |
| 3 | 网络错误携带下载信息 | ArkTS event 可包含 downloadInfo | AC-2.3 |

**onFinish(event)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onFinish(event: () => void): ImageAttribute` |
| 返回值 | `ImageAttribute`/`this`，支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | VoidCallback | 是 | 未注册 | SDK 合约限定已加载 SVG 图片动画完成；无限循环 SVG 不触发。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有限循环 SVG 动画完成 | 触发无参回调 | AC-3.2 |
| 2 | 静态图片加载完成 | 不触发回调 | AC-3.3 |
| 3 | 当前实现遇到非静态 CanvasImage | 注册 finish 回调，作为 SDK/实现差异记录 | AC-3.4 |

**NDK Image Node Events**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_NodeEventType` 中 `NODE_IMAGE_ON_COMPLETE`/`NODE_IMAGE_ON_ERROR`/`NODE_IMAGE_ON_SVG_PLAY_FINISH`/`NODE_IMAGE_ON_DOWNLOAD_PROGRESS` |
| 返回值 | `ArkUI_NodeEvent`，通过节点事件回调返回 |
| 开放范围 | Public C API |
| 错误码 | `NODE_IMAGE_ON_ERROR` 当前实现固定 401 |
| 关联 AC | AC-4.1~AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| data | ArkUI_NodeComponentEvent.data | 否 | 空 | onComplete 使用 9 个 data 槽位；onError 使用 1 个；SVG finish 无参数；download progress 使用 2 个。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | NDK 成功事件 | 返回 loadingStatus、尺寸、偏移、内容尺寸 | AC-4.1 |
| 2 | NDK 失败事件 | `data[0].i32=401` | AC-4.2 |
| 3 | NDK 下载进度事件 | 返回 dlNow/dlTotal | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否，本文为已有实现补录；onFinish 的 SVG SDK 合约与非静态 CanvasImage 实现差异显式记录为风险。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** onFinish/onComplete 基础动态声明 API 7，onError API 9，静态 Image 事件 API 23，NDK 节点事件按 `native_node.h` 当前枚举。
- **API 版本号策略:** @since 与 SDK `.d.ts/.static.d.ets` 保持一致；NDK 事件 payload 以 `native_node.h` 注释为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| EventHub 注册 | ArkTS 三个事件均注册在 ImageEventHub，由 Pattern/CanvasImage 在对应生命周期触发 | AC-1.1, AC-2.1, AC-3.1 |
| 回调后状态访问约束 | `OnImageLoadSuccess` 明确在触发外部回调后避免继续访问内部成员 | AC-1.3 |
| NDK payload 固定下标 | C API 事件 data 下标由 `native_node.h` 与 node modifier 共同定义，不能随意重排 | AC-4.1~AC-4.4 |
| 下载进度依赖网络下载能力 | 只有网络源且启用 DownloadManager 路径，并存在 progress callback 时才注册下载进度回调 | AC-4.4~AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 事件回调不引入额外布局或渲染脏标记；仅在生命周期回调点派发 | 代码审查 | `image_pattern.cpp:234-247`, `image_pattern.cpp:489-555` |
| 功耗 | N/A，事件派发不改变图片解码或渲染策略 | 代码审查 | N/A |
| 内存 | 事件回调存储为 `std::function` 成员，未注册时为空 | 代码审查 | `image_event_hub.h:77-80`, `image_pattern.h:419` |
| 安全 | 错误事件中 URL/下载信息由已有 DownloadManager 包装逻辑处理 | 代码审查 | `js_image.cpp:143-160` |
| 可靠性 | onComplete 成功回调后不再继续访问内部状态，降低外部回调销毁节点风险 | 代码审查 | `image_pattern.cpp:542-555` |
| 可测试性 | ArkTS 事件可由 XTS 覆盖，NDK 事件可由 C API UT 覆盖 | XTS + C API UT | `native_node.h:10508-10540` |
| 自动化维测 | 事件注册上报组件事件名，支持会话维测记录 | 代码审查 | `js_image.cpp:281-307` |
| 定界定位 | ImageErrorCode 与 NDK 固定错误码可帮助区分 ArkTS 与 C API 信息粒度 | 代码审查 | `image_defines.h:40-71`, `node_image_modifier.cpp:1683-1695` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无设备专属差异 | 事件语义一致 | XTS/C API UT | `image_event_hub.h:36-75` |
| 平板 | 无设备专属差异 | 事件语义一致 | XTS/C API UT | `image_event_hub.h:36-75` |
| 折叠屏 | 无设备专属差异 | 事件语义一致；组件尺寸以当前 GeometryNode 为准 | XTS/C API UT | `image_pattern.cpp:234-247`, `image_pattern.cpp:548-551` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 事件回调不改变无障碍节点语义 | N/A |
| 大字体 | 否 | 事件字段为图片/组件尺寸，不受字体缩放影响 | N/A |
| 深色模式 | 否 | 事件回调不改变图片源或颜色模式 | N/A |
| 多窗口/分屏 | 是 | event 中 component/content 尺寸来自当前窗口布局后的 GeometryNode | AC-1.2~AC-1.3 |
| 多用户 | 否 | 无用户态存储差异 | N/A |
| 版本升级 | 是 | onError 从 API 9，静态事件从 API 23；onFinish SDK 合约需保持 SVG 语义 | AC-2.6, AC-3.2 |
| 生态兼容 | 是 | NDK onError 错误码粒度低于 ArkTS；onFinish SDK/实现范围存在差异 | AC-3.4, AC-4.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 事件回调

  Scenario: onComplete 两阶段触发
    Given 一个注册了 onComplete 的 Image 组件
    When 图片数据加载完成并完成布局回调
    Then onComplete 被触发且 loadingStatus 为 0
    And event 包含原图尺寸、组件尺寸、content 尺寸和 content offset
    When 图片解码并生成 CanvasImage 成功
    Then onComplete 再次触发且 loadingStatus 为 1
    And contentWidth/contentHeight 来自实际绘制区域

  Scenario: onError 触发并启动错误图加载
    Given 一个 Image 组件配置了 AltError
    And 注册了 onError 回调
    When 主图加载失败
    Then Pattern 启动 AltError 加载
    And onError 收到 componentWidth、componentHeight、message 和 error

  Scenario: onFinish SDK 合约
    Given 一个注册了 onFinish 的 Image 组件
    And 图片源为有限循环 SVG 动画
    When SVG 动画播放完成
    Then onFinish 被触发且无事件参数

  Scenario: NDK 下载进度事件
    Given 一个 NDK Image 节点注册了 NODE_IMAGE_ON_DOWNLOAD_PROGRESS
    And 图片源为网络图片且下载能力开启
    When 下载层回调 dlNow 和 dlTotal
    Then ArkUI_NodeComponentEvent.data[0].u32 等于 dlNow
    And ArkUI_NodeComponentEvent.data[1].u32 等于 dlTotal
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（ArkTS 3 个事件 + NDK 4 个节点事件，不含属性类规格）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Image event hub onComplete onError onFinish node image events payload"
  - repo: "openharmony/arkui_ace_engine"
    query: "Image NODE_IMAGE_ON_DOWNLOAD_PROGRESS ImageProvider progress callback"
```

**关键文档：** `design.md`（同目录）、`docs/kb/components/media/image.md`（Image 组件 KB）
