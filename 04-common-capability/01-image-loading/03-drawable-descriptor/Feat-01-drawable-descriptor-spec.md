# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | DrawableDescriptor 能力 (TS + C API) |
| 特性编号 | Feat-01 |
| 所属 FuncID | 04-01-03 |
| 所属 Epic | 无，已有能力补录 |
| 优先级 | P0 |
| 目标版本 | API 10 到 API 26 |
| SIG 归属 | ArkUI |
| 状态 | Baselined |
| 复杂度 | 复杂 |

DrawableDescriptor 是 ArkUI drawable 资源的描述符抽象，覆盖资源/路径/base64 加载、PixelMap 获取、Layered 三层合成、Animated 帧动画、Picture/HDR 合成、ArkTS 到 Native 的桥接和 NDK C API 句柄管理。动态 SDK 定义 5 个类、4 个接口和 1 个枚举，静态 SDK 提供对应静态声明，C API 提供不透明句柄、动画配置和动画控制能力。SDK 声明是外部 API 契约，核心行为以 `frameworks/core/drawable/` 和桥接实现为证据。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 `Feat-01-drawable-descriptor-spec.md` | 将已有规格从粗略能力描述补齐为可追溯的 US/AC、规则、API、接口语义、兼容性和验证映射。 |
| MODIFIED | 标注 Dynamic/Static/C API 差异 | Dynamic SDK、Static SDK、C API 的 `@since`、返回值、错误码和 release 后行为存在差异，规格中显式记录。 |
| MODIFIED | 修正验证口径 | 已有 core/inner_api/NAPI 单测作为证据；未发现直接覆盖全部 `OH_ArkUI_DrawableDescriptor_*` C API 的单测，C API 行为以头文件和实现审查为主，并记录测试缺口。 |

## 输入文档

- 需求基线：已有实现能力补录，无独立 requirement.md。
- 设计文档：`arkui-specs/04-common-capability/01-image-loading/03-drawable-descriptor/design.md`
- SDK 声明文件：
  - Dynamic API: `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.d.ts:31`
  - Static API: `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.static.d.ets:27`
- TS/ArkTS 桥接实现：
  - Dynamic NAPI: `interfaces/inner_api/drawable_descriptor/js_drawable_descriptor.cpp:107`
  - Static ArkTS: `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/@ohos.arkui.drawableDescriptor.ets:55`
- C API：
  - Header: `interfaces/native/drawable_descriptor.h:46`
  - Implementation: `interfaces/native/node/drawable_descriptor.cpp:29`
  - NodeModel dispatch: `interfaces/native/node/node_model.cpp:1181`
  - NAPI bridge: `interfaces/native/node/native_node_napi.cpp:359`
  - ANI bridge: `interfaces/native/node/native_node_ani.cpp:343`
- Core implementation:
  - Base/type factory: `frameworks/core/drawable/drawable_descriptor.h:29`, `frameworks/core/drawable/drawable_descriptor.cpp:235`
  - Layered: `frameworks/core/drawable/layered_drawable_descriptor.cpp:156`
  - Animated: `frameworks/core/drawable/animated_drawable_descriptor.h:120`, `frameworks/core/drawable/animated_drawable_descriptor.cpp:32`
  - PixelMap: `frameworks/core/drawable/pixel_map_drawable_descriptor.cpp:29`
  - Picture: `frameworks/core/drawable/picture_drawable_descriptor.cpp:42`
  - Resource loader: `frameworks/core/drawable/drawable_descriptor_info.cpp:34`, `frameworks/core/drawable/drawable_descriptor_loader.cpp:44`
- 测试证据：
  - Core drawable tests: `test/unittest/frameworks/core/drawable/drawable_descriptor_test.cpp:164`
  - BlendMode boundary tests: `test/unittest/interfaces/drawable_descriptor_extended_test.cpp:417`

## 用户故事

### US-1: 基础 DrawableDescriptor 加载与生命周期

作为 ArkTS 调用者，我想要通过 DrawableDescriptor 获取 PixelMap、同步或异步加载尺寸并显式释放资源，以便在 Image 等组件中使用 drawable 资源并控制 native 内存生命周期。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Dynamic `DrawableDescriptor.getPixelMap()` 在对象未释放时被调用 THEN 返回 SDK 声明的 `image.PixelMap`，实现侧从 native descriptor 或 Layered descriptor 取 PixelMap。 | 正常 |
| AC-1.2 | WHEN Dynamic `loadSync()` 或 `load()` 在非 Layered descriptor 上调用 THEN 返回或 resolve `DrawableDescriptorLoadedResult`，结果只暴露 `imageWidth` 和 `imageHeight`。 | 正常 |
| AC-1.3 | WHEN Dynamic `loadSync()` 或 `load()` 资源加载失败 THEN 抛出或 reject `BusinessError 111001`。 | 异常 |
| AC-1.4 | WHEN Dynamic `release()` 第一次调用后再次调用 THEN 第二次调用直接返回且不崩溃；`isReleased()` 返回 `true`。 | 边界 |
| AC-1.5 | WHEN Dynamic 已释放对象继续调用 `getPixelMap()`、Layered getter、`loadSync()` 或 `load()` THEN 抛出 `BusinessError 111002`。 | 异常 |
| AC-1.6 | WHEN Static 已释放对象继续调用 `getPixelMap()`、`loadSync()` 或 `load()` THEN `getPixelMap()` 返回 `undefined`，`loadSync/load` 返回或 resolve `imageWidth=-1,imageHeight=-1`。 | 边界 |
| AC-1.7 | WHEN 调用 `invalidate()` 且 descriptor 类型不是 Picture 或未绑定组件 THEN 调用允许完成，不产生可见更新；Picture descriptor 已绑定回调时触发异步重载和回调。 | 正常 |

### US-2: LayeredDrawableDescriptor 分层合成

作为系统 UI 开发者，我想要读取 foreground/background/mask 三层并控制合成模式，以便生成自适应图标或组合图标 PixelMap。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 创建 Layered descriptor THEN `GetDrawableType()` 返回 `DrawableType::LAYERED`，Dynamic/Static SDK 暴露 `LayeredDrawableDescriptor extends DrawableDescriptor`。 | 正常 |
| AC-2.2 | WHEN `getForeground()`、`getBackground()`、`getMask()` 在对象未释放时调用 THEN 返回对应层 descriptor；Static API 允许返回 `undefined`。 | 正常 |
| AC-2.3 | WHEN 构造函数传入 foreground/background/mask THEN 三层从入参 PixelMap 建立；mask 未传时静态实现使用 native 创建逻辑，动态实现会尝试初始化默认 mask。 | 正常 |
| AC-2.4 | WHEN `setBlendMode(mode)` 传入 `CLEAR` 到 `LUMINOSITY` 范围内的值 THEN 设置 blendMode 并启用 foreground-over-background 合成顺序。 | 正常 |
| AC-2.5 | WHEN `setBlendMode(mode)` 传入范围外数值或 Static 传入 `undefined` THEN 本次调用不改变现有合成状态。 | 边界 |
| AC-2.6 | WHEN `getPixelMap()` 合成且 foreground 尺寸为 288x288 THEN 使用非自适应路径，输出 192x192；否则使用自适应路径，输出以 background 尺寸为准。 | 边界 |
| AC-2.7 | WHEN foreground/background/mask 数据不足以合成 THEN `getPixelMap()` 返回空结果，不抛出业务异常。 | 异常 |
| AC-2.8 | WHEN `LayeredDrawableDescriptor.getMaskClipPath()` 调用 THEN 返回系统内置 mask clip path 字符串。 | 正常 |

### US-3: PixelMap 与 Picture descriptor

作为 ArkTS 调用者，我想要直接包装 PixelMap、ResourceStr 或 Picture，以便不依赖 resource manager 产出的通用 descriptor。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `new PixelMapDrawableDescriptor(pixelMap)` 构造 THEN 直接保存并返回该 PixelMap；`loadSync()` 返回其宽高。 | 正常 |
| AC-3.2 | WHEN `new PixelMapDrawableDescriptor(resourceStr)` 使用 Resource、`file:` URI 或合法 base64 图像 URI THEN loader 按 RESOURCE/FILE/BASE64 类型加载并解码为 BGRA_8888 PixelMap。 | 正常 |
| AC-3.3 | WHEN PixelMap descriptor 无 PixelMap、无资源信息或资源读取/解码失败 THEN `loadSync()` 返回 loader error，Dynamic 桥接映射为 `BusinessError 111001`。 | 异常 |
| AC-3.4 | WHEN `new PictureDrawableDescriptor(picture)` 构造 THEN 保存 Picture；`loadSync()` 成功后缓存 main pixel 或 HDR 合成后的 PixelMap。 | 正常 |
| AC-3.5 | WHEN `setHdrComposition(config)` 中 `rect.width > 0` 且 `rect.height > 0` THEN Picture 加载时优先执行 HDR FOV 合成；合成失败回退到 main pixel。 | 边界 |
| AC-3.6 | WHEN Picture descriptor 调用 `getPixelMap()` 但尚未 `load/loadSync/invalidate` 生成缓存 THEN 返回空结果。 | 边界 |

### US-4: AnimatedDrawableDescriptor 动画数据与选项

作为 ArkTS 调用者，我想要用 PixelMap 数组或动画资源创建 Animated descriptor 并配置时长、播放次数、自动播放和停止帧，以便将同一动画资源绑定到 Image 组件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 构造 `AnimatedDrawableDescriptor(pixelMaps, options)` 且 PixelMap 数组非空 THEN 第一帧作为 `getPixelMap()` 返回值，帧数等于数组长度。 | 正常 |
| AC-4.2 | WHEN 构造 `AnimatedDrawableDescriptor(src, options)` 且 src 为 Resource、`file:` URI 或合法 base64 图像 URI THEN loader 从资源源读取原始数据并通过 ImageSource 解析帧信息。 | 正常 |
| AC-4.3 | WHEN `frameDurations` 非空 THEN 用户帧时长覆盖 `duration`，总时长等于帧时长求和。 | 正常 |
| AC-4.4 | WHEN `duration >= 0` 且未设置 `frameDurations` THEN 每帧时长按总时长和帧数平均分配；`duration < 0` 被忽略并使用默认规则。 | 边界 |
| AC-4.5 | WHEN 未设置 `duration/frameDurations` 且输入为 PixelMap 数组 THEN 总时长按每帧 1000ms 计算。 | 边界 |
| AC-4.6 | WHEN `iterations < -1` THEN 实现将播放次数恢复为默认值 1；`iterations=-1` 表示无限播放，`iterations=0` 表示不播放。 | 边界 |
| AC-4.7 | WHEN `autoPlay=false` 且组件进入可见状态 THEN 不自动 forward，并刷新第 0 帧；不可见时若动画正在运行则暂停。 | 正常 |
| AC-4.8 | WHEN `stopMode=LAST_FRAME` THEN stop 监听刷新最后一帧；否则刷新第 0 帧。 | 正常 |

### US-5: AnimationController 与 per-node 独立控制

作为开发者，我想要为绑定了 Animated descriptor 的组件获取动画控制器，以便每个组件独立 start/stop/pause/resume 并查询状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 只有一个组件绑定同一 Animated descriptor THEN `getAnimationController()` 不传 id 也返回该唯一 controller。 | 正常 |
| AC-5.2 | WHEN 同一 Animated descriptor 绑定多个组件 THEN 调用者必须传唯一组件 id；找不到 id 或未绑定 controller 时返回 `undefined`。 | 边界 |
| AC-5.3 | WHEN controller 调用 `start()` THEN native controller 先 finish 再 forward，状态进入运行路径。 | 正常 |
| AC-5.4 | WHEN controller 调用 `stop()`、`pause()` 或 `resume()` THEN 分别映射到 finish、pause、forward；`getStatus()` 返回 native control status。 | 正常 |
| AC-5.5 | WHEN 组件注销更新回调 THEN 对应 nodeId 的 animator、callback 和 imageSource 被移除，动画先暂停。 | 正常 |

### US-6: NDK C API 创建、配置与控制

作为 NDK 调用者，我想要通过 `ArkUI_DrawableDescriptor*` 创建静态或动画 descriptor，配置动画参数并创建控制器，以便在 Native UI 场景中复用 drawable 资源。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN `OH_ArkUI_DrawableDescriptor_CreateFromPixelMap(pixelMap)` 传入非空 PixelMap handle THEN 返回 descriptor；传入空指针返回 `nullptr`。 | 正常 |
| AC-6.2 | WHEN `OH_ArkUI_DrawableDescriptor_CreateFromAnimatedPixelMap(array, size)` 传入非空数组 THEN 返回 animated descriptor，数组中的空 PixelMap 元素被跳过，默认 duration=-1、iteration=1。 | 正常 |
| AC-6.3 | WHEN 调用 `OH_ArkUI_DrawableDescriptor_Dispose(descriptor)` THEN 空指针无操作；非空 descriptor 释放句柄并减少 newDrawableDescriptor 引用计数。 | 正常 |
| AC-6.4 | WHEN 静态/动画 PixelMap getter 在空 descriptor 上调用 THEN 静态 getter 返回 `nullptr`，动画数组 size getter 返回 0。 | 边界 |
| AC-6.5 | WHEN duration/iteration setter 在空 descriptor 或非动画 descriptor 上调用 THEN 调用无操作；getter 分别返回 -1 和 1。 | 边界 |
| AC-6.6 | WHEN `SetAnimationFrameDurations` 传入空 descriptor、非动画 descriptor、空 durations、size=0 或 size 与帧数不一致 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-6.7 | WHEN `SetAnimationAutoPlay(autoPlay)` 传入非 0 值 THEN native 侧按 `true` 处理；getter 需要非空输出指针。 | 边界 |
| AC-6.8 | WHEN `SetAnimationStopMode(mode)` 传入非 FIRST/LAST 范围值 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-6.9 | WHEN `CreateAnimationController` 传入非 animated descriptor、空 controller 输出指针或节点未绑定该 animated descriptor THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-6.10 | WHEN controller start/stop/pause/resume/status 传入空 controller 或底层 controller 为空 THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |

### US-7: ArkTS 到 Native Bridge

作为 NDK 调用者，我想要从 NAPI/ANI ArkTS 对象或资源对象提取 `ArkUI_DrawableDescriptor*`，以便 Native 层使用 ArkTS 已创建的 drawable 资源。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN `OH_ArkUI_GetDrawableDescriptorFromNapiValue` 传入可 unwrap 的非 Layered descriptor THEN 创建 native wrapper 并增加 core descriptor 引用计数。 | 正常 |
| AC-7.2 | WHEN `OH_ArkUI_GetDrawableDescriptorFromNapiValue` 传入 Layered descriptor THEN native wrapper 使用 Layered 合成后的 PixelMap 创建旧 `Napi::DrawableDescriptor` 包装。 | 正常 |
| AC-7.3 | WHEN NAPI unwrap 失败或对象已释放 THEN 返回 `ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-7.4 | WHEN Resource NAPI/ANI bridge 解析资源对象 THEN 将资源字段写入 `ArkUI_Resource`，供后续创建 descriptor 使用。 | 正常 |
| AC-7.5 | WHEN ANI bridge 读取 `nativeObj` 为 0 或对象为空 THEN 返回 `ERROR_CODE_PARAM_INVALID`；成功时增加 core descriptor 引用计数。 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-3 | TASK-SKELETON-1 | SDK/实现审查 + core UT | `@ohos.arkui.drawableDescriptor.d.ts:87`, `js_drawable_descriptor.cpp:496`, `drawable_descriptor_test.cpp:169` |
| AC-1.2 | R-4 | TASK-SKELETON-1 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:100`, `js_drawable_descriptor.cpp:613`, `js_drawable_descriptor.cpp:658` |
| AC-1.3 | R-5 | TASK-SKELETON-1 | SDK/实现审查 + core UT | `@ohos.arkui.drawableDescriptor.d.ts:104`, `pixel_map_drawable_descriptor.cpp:39`, `drawable_descriptor_test.cpp:341` |
| AC-1.4 | R-6 | TASK-SKELETON-1 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:129`, `js_drawable_descriptor.cpp:896` |
| AC-1.5 | R-6 | TASK-SKELETON-1 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:91`, `js_drawable_descriptor.cpp:107` |
| AC-1.6 | R-7 | TASK-SKELETON-1 | Static 实现审查 | `@ohos.arkui.drawableDescriptor.ets:65`, `@ohos.arkui.drawableDescriptor.ets:72` |
| AC-1.7 | R-8 | TASK-SKELETON-1 | Core UT + 实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:161`, `picture_drawable_descriptor.cpp:178`, `drawable_descriptor_test.cpp:1460` |
| AC-2.1 | R-2, R-9 | TASK-SKELETON-1 | SDK/UT | `drawable_descriptor.h:29`, `drawable_descriptor_test.cpp:357`, `drawable_descriptor_test.cpp:1685` |
| AC-2.2 | R-9 | TASK-SKELETON-1 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:208`, `@ohos.arkui.drawableDescriptor.static.d.ets:163`, `js_drawable_descriptor.cpp:375` |
| AC-2.3 | R-10 | TASK-SKELETON-1 | SDK/实现审查 + UT | `js_drawable_descriptor.cpp:1101`, `@ohos.arkui.drawableDescriptor.ets:183`, `drawable_descriptor_test.cpp:368` |
| AC-2.4 | R-11 | TASK-SKELETON-1 | Core UT | `layered_drawable_descriptor.cpp:307`, `drawable_descriptor_test.cpp:482` |
| AC-2.5 | R-11 | TASK-SKELETON-1 | Core/NAPI UT | `layered_drawable_descriptor.cpp:307`, `drawable_descriptor_test.cpp:495`, `drawable_descriptor_extended_test.cpp:422` |
| AC-2.6 | R-12 | TASK-SKELETON-1 | 实现审查 | `layered_drawable_descriptor.cpp:156`, `layered_drawable_descriptor.cpp:208`, `layered_drawable_descriptor.cpp:267` |
| AC-2.7 | R-13 | TASK-SKELETON-1 | Core UT | `layered_drawable_descriptor.cpp:258`, `drawable_descriptor_test.cpp:606` |
| AC-2.8 | R-14 | TASK-SKELETON-1 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:266`, `js_drawable_descriptor.cpp:445` |
| AC-3.1 | R-15 | TASK-SKELETON-1 | SDK/UT | `@ohos.arkui.drawableDescriptor.d.ts:280`, `pixel_map_drawable_descriptor.cpp:29`, `drawable_descriptor_test.cpp:297` |
| AC-3.2 | R-16 | TASK-SKELETON-1 | 实现审查 + loader UT | `drawable_descriptor_info.cpp:34`, `drawable_descriptor_loader.cpp:44`, `drawable_descriptor_test.cpp:1577` |
| AC-3.3 | R-5, R-16 | TASK-SKELETON-1 | Core UT | `pixel_map_drawable_descriptor.cpp:45`, `drawable_descriptor_test.cpp:341` |
| AC-3.4 | R-17 | TASK-SKELETON-1 | SDK/UT | `@ohos.arkui.drawableDescriptor.d.ts:596`, `picture_drawable_descriptor.cpp:142`, `drawable_descriptor_test.cpp:1322` |
| AC-3.5 | R-18 | TASK-SKELETON-1 | Core UT + 实现审查 | `picture_drawable_descriptor.cpp:60`, `picture_drawable_descriptor.cpp:127`, `drawable_descriptor_test.cpp:1434` |
| AC-3.6 | R-17 | TASK-SKELETON-1 | Core UT | `picture_drawable_descriptor.cpp:48`, `drawable_descriptor_test.cpp:1349` |
| AC-4.1 | R-19 | TASK-SKELETON-1 | SDK/UT | `@ohos.arkui.drawableDescriptor.d.ts:523`, `animated_drawable_descriptor.cpp:125`, `drawable_descriptor_test.cpp:660` |
| AC-4.2 | R-16, R-19 | TASK-SKELETON-1 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:536`, `animated_drawable_descriptor.cpp:32`, `drawable_descriptor_loader.cpp:44` |
| AC-4.3 | R-20 | TASK-SKELETON-1 | Core UT | `@ohos.arkui.drawableDescriptor.d.ts:396`, `animated_drawable_descriptor.cpp:201`, `drawable_descriptor_test.cpp:729` |
| AC-4.4 | R-20 | TASK-SKELETON-1 | Core UT | `animated_drawable_descriptor.cpp:184`, `animated_drawable_descriptor.cpp:211`, `drawable_descriptor_test.cpp:775` |
| AC-4.5 | R-20 | TASK-SKELETON-1 | Core UT | `animated_drawable_descriptor.cpp:170`, `drawable_descriptor_test.cpp:841` |
| AC-4.6 | R-21 | TASK-SKELETON-1 | SDK/UT | `@ohos.arkui.drawableDescriptor.d.ts:380`, `animated_drawable_descriptor.cpp:219`, `drawable_descriptor_test.cpp:891` |
| AC-4.7 | R-22 | TASK-SKELETON-1 | 实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:413`, `animated_drawable_descriptor.cpp:72` |
| AC-4.8 | R-23 | TASK-SKELETON-1 | SDK/UT + 实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:318`, `animated_drawable_descriptor.cpp:261`, `drawable_descriptor_test.cpp:647` |
| AC-5.1 | R-24 | TASK-SKELETON-1 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:552`, `animated_drawable_descriptor.cpp:95` |
| AC-5.2 | R-24 | TASK-SKELETON-1 | SDK/实现审查 + UT | `animated_drawable_descriptor.cpp:100`, `animated_drawable_descriptor.cpp:112`, `drawable_descriptor_test.cpp:915` |
| AC-5.3 | R-25 | TASK-SKELETON-1 | 实现审查 | `drawable_descriptor.cpp:181`, `node_model.cpp:1468` |
| AC-5.4 | R-25 | TASK-SKELETON-1 | 实现审查 | `drawable_descriptor.cpp:190`, `drawable_descriptor.cpp:198`, `drawable_descriptor.cpp:206`, `drawable_descriptor.cpp:214` |
| AC-5.5 | R-26 | TASK-SKELETON-1 | 实现审查 | `animated_drawable_descriptor.cpp:298` |
| AC-6.1 | R-27 | TASK-SKELETON-1 | Header/实现审查 | `drawable_descriptor.h:123`, `interfaces/native/node/drawable_descriptor.cpp:29` |
| AC-6.2 | R-27 | TASK-SKELETON-1 | Header/实现审查 | `drawable_descriptor.h:133`, `interfaces/native/node/drawable_descriptor.cpp:40` |
| AC-6.3 | R-28 | TASK-SKELETON-1 | Header/实现审查 | `drawable_descriptor.h:142`, `interfaces/native/node/drawable_descriptor.cpp:66` |
| AC-6.4 | R-29 | TASK-SKELETON-1 | 实现审查 | `interfaces/native/node/drawable_descriptor.cpp:75`, `interfaces/native/node/drawable_descriptor.cpp:88` |
| AC-6.5 | R-30 | TASK-SKELETON-1 | 实现审查 | `interfaces/native/node/drawable_descriptor.cpp:94`, `interfaces/native/node/drawable_descriptor.cpp:101` |
| AC-6.6 | R-31 | TASK-SKELETON-1 | 实现审查 | `interfaces/native/node/drawable_descriptor.cpp:122`, `node_model.cpp:1287` |
| AC-6.7 | R-32 | TASK-SKELETON-1 | 实现审查 | `interfaces/native/node/drawable_descriptor.cpp:146`, `node_model.cpp:1337` |
| AC-6.8 | R-33 | TASK-SKELETON-1 | 实现审查 | `interfaces/native/node/drawable_descriptor.cpp:168`, `node_model.cpp:1373` |
| AC-6.9 | R-34 | TASK-SKELETON-1 | 实现审查 | `interfaces/native/node/drawable_descriptor.cpp:191`, `node_model.cpp:1405` |
| AC-6.10 | R-35 | TASK-SKELETON-1 | 实现审查 | `interfaces/native/node/drawable_descriptor.cpp:209`, `node_model.cpp:1468` |
| AC-7.1 | R-36 | TASK-SKELETON-1 | 实现审查 | `native_node_napi.cpp:359` |
| AC-7.2 | R-36 | TASK-SKELETON-1 | 实现审查 | `native_node_napi.cpp:375` |
| AC-7.3 | R-37 | TASK-SKELETON-1 | 实现审查 | `native_node_napi.cpp:362` |
| AC-7.4 | R-38 | TASK-SKELETON-1 | 实现审查 | `native_node_napi.cpp:392`, `native_node_ani.cpp:363` |
| AC-7.5 | R-37, R-38 | TASK-SKELETON-1 | 实现审查 | `native_node_ani.cpp:343` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Dynamic `DrawableDescriptor.getPixelMap()` 调用，native 对象未释放。 | 返回 `image.PixelMap`；Layered 类型直接走 Layered descriptor `GetPixelMap()`，非 Layered 类型走 ArkUI drawable modifier。 | SDK 返回类型为非 optional；实际失败场景由 native 返回空 PixelMap 或错误传递。 | AC-1.1 |
| R-2 | 行为 | 创建任一 core descriptor 子类型。 | `DrawableType` 枚举固定为 BASE=0、LAYERED=1、ANIMATED=2、PIXELMAP=3、PICTURE=4。 | `OHOS_ACE_CreateDrawableDescriptorByType` 只允许创建到 PIXELMAP，type > PIXELMAP 返回空，不通过该工厂创建 Picture。 | AC-2.1 |
| R-3 | 行为 | 基类 core descriptor 默认方法被调用。 | `GetPixelMap()` 返回空，`GetOriginalWidth/Height()` 返回 -1，`LoadSync()` 返回宽高 0 且 errorCode 0，`Invalidate()` 无操作。 | 仅 core 默认行为；Dynamic SDK contract 仍以 SDK 声明为准。 | AC-1.1 |
| R-4 | 行为 | Dynamic `loadSync/load` 在非 Layered descriptor 上调用。 | `loadSync` 同步返回 `{imageWidth,imageHeight}`；`load` 创建 Promise 并在 async work 完成后 resolve 或 reject。 | Dynamic Layered `load()` 返回 `undefined`，Dynamic Layered `loadSync()` 走 last error 分支。 | AC-1.2 |
| R-5 | 异常 | 加载资源失败或 core `LoadSync()` 返回非 0 errorCode。 | Dynamic 桥接抛出或 reject `BusinessError 111001`；core PixelMap/Animated 返回 `ERROR_CODE_DRAWABLE_LOADER_ERROR`。 | SDK result 仅暴露宽高，内部 errorCode 不进入 `DrawableDescriptorLoadedResult`。 | AC-1.3, AC-3.3 |
| R-6 | 异常 | Dynamic descriptor 第一次 `release()` 后继续访问内部 native 数据。 | `release()` 设置 `_released=true` 并解绑 native wrap；后续 unwrap 为空的访问抛出 `BusinessError 111002`，重复 release 直接返回。 | 适用于 Dynamic SDK 标注 111002 的 API；C API `Dispose` 不等同于 TS release。 | AC-1.4, AC-1.5 |
| R-7 | 边界 | Static descriptor `_isReleased=true` 后调用 `getPixelMap/loadSync/load/invalidate`。 | `getPixelMap()` 返回 `undefined`；`loadSync/load` 返回或 resolve `imageWidth=-1,imageHeight=-1`；`invalidate()` 直接返回。 | Static SDK 未声明 111002；该行为与 Dynamic SDK 的 release 后错误码不同。 | AC-1.6 |
| R-8 | 行为 | `invalidate()` 被调用。 | 基类无操作；Picture descriptor 入队后台 invalidate 任务，加载 PixelMap 后缓存并通知 update callback。 | Picture invalidate 只保留一个最新 pending task；未绑定 callback 时只更新缓存或无可见效果。 | AC-1.7 |
| R-9 | 行为 | Layered getter 在对象未释放时调用。 | 返回 foreground/background/mask 对应 descriptor；Static API 允许返回 `undefined`；Dynamic release 后按 R-6 处理。 | Dynamic SDK getter 返回非 optional；Static getter 返回 optional。 | AC-2.1, AC-2.2 |
| R-10 | 行为 | Layered constructor 传入 0 到 3 个 descriptor。 | 已传入层转为 PixelMap 存储；缺失 background 时动态实现可复用 foreground；缺失 mask 时动态实现尝试初始化默认 mask。 | Static 构造直接把 `foreground?.getPixelMap()` 等传给 native 创建。 | AC-2.3 |
| R-11 | 边界 | `setBlendMode(mode)` 调用。 | mode 在 `RSBlendMode::CLEAR` 到 `RSBlendMode::LUMINOSITY` 范围内时设置 blendMode 并将 `foregroundOverBackground=true`；范围外或 Static `undefined` 时不改变。 | Dynamic 参数类型是 `drawing.BlendMode`；Static 参数类型是 `drawing.BlendMode 或 undefined`。 | AC-2.4, AC-2.5 |
| R-12 | 行为 | Layered `getPixelMap()` 触发合成。 | foreground 为 288x288 时走非自适应路径，输出 192x192；其他情况走自适应路径，输出使用 background 尺寸。 | 合成顺序受 `foregroundOverBackground` 控制；mask 使用 `DST_IN`。 | AC-2.6 |
| R-13 | 异常 | Layered 合成缺少 background 或层数据无法解码。 | 合成返回空 PixelMap，调用方按空结果处理。 | 不额外抛出 BusinessError。 | AC-2.7 |
| R-14 | 行为 | 调用 `LayeredDrawableDescriptor.getMaskClipPath()`。 | 返回内置自适应图标 mask clip path 字符串。 | 静态方法，无实例 release 状态依赖。 | AC-2.8 |
| R-15 | 行为 | PixelMap descriptor 持有已有 PixelMap。 | `getPixelMap()` 直接返回缓存；`loadSync()` 返回缓存 PixelMap 宽高。 | 构造入参为空时缓存为空，后续可通过资源/raw data 懒加载。 | AC-3.1 |
| R-16 | 行为 | ResourceStr 或资源对象输入被解析。 | 字符串 `file:` 头按 FILE，合法 `data:image/...;base64,` 按 BASE64，ResourceObject 按 RESOURCE；loader 分别从文件、base64 或 ResourceManager 读取字节。 | 空字符串、无逗号 base64 或不支持头返回 UNDEFINED，loader 返回空数据。 | AC-3.2, AC-3.3, AC-4.2 |
| R-17 | 行为 | Picture descriptor 加载或读取 PixelMap。 | `loadSync()` 从 Picture 获取 main pixel，若 HDR 配置有效先尝试 FOV 合成；成功后缓存 PixelMap，`getPixelMap()` 只返回缓存。 | 无 picture 或加载失败时返回 `{0,0,-1}`。 | AC-3.4, AC-3.6 |
| R-18 | 边界 | Picture HDR 配置被设置。 | `rect.width > 0` 且 `rect.height > 0` 才视为有效；有效时优先使用 LHDR gainmap 和 VPE 合成，失败则回退 main pixel。 | `x/y` 不参与有效性判断；VPE 调用串行化。 | AC-3.5 |
| R-19 | 行为 | Animated descriptor 使用 PixelMap 数组或动画资源构造。 | PixelMap 数组直接设置帧列表和帧数；资源输入在加载/注册回调时创建 ImageSource 并读取 frameCount 和 delay time。 | PixelMap 数组为空时帧数为 0，注册回调不创建 animator。 | AC-4.1, AC-4.2 |
| R-20 | 边界 | 计算 Animated frame durations 或 total duration。 | 非空 `frameDurations` 优先并将 totalDuration 设为求和；未设置时 `duration>=0` 均分到帧；PixelMap 数组默认每帧 1000ms；资源动图使用 ImageSource delay time。 | `duration<0` 被忽略；C API `SetFrameDurations` 要求数组长度等于帧数且 size 非 0。 | AC-4.3, AC-4.4, AC-4.5 |
| R-21 | 边界 | 设置 Animated iterations。 | `iterations<-1` 恢复为 1；`-1` 无限播放，`0` 不播放，正数为播放次数。 | C API 和 TS options 最终进入同一 core 字段。 | AC-4.6 |
| R-22 | 行为 | Animated descriptor 可见性控制进入 `ControllAnimation(nodeId, play)`。 | `play=true` 且 `autoPlay=false` 刷新第 0 帧；`play=true` 且 `autoPlay=true` forward；`play=false` 且状态 RUNNING 时 pause。 | 找不到 nodeId animator 时无操作。 | AC-4.7 |
| R-23 | 行为 | Animated stop 或 controller stop。 | stop listener 根据 `stopMode` 刷新首帧或末帧；`LAST_FRAME` 对应 fill mode FORWARDS，默认 FIRST_FRAME 对应 BACKWARDS。 | `AnimationStopMode` FIRST_FRAME=0、LAST_FRAME=1。 | AC-4.8 |
| R-24 | 边界 | 获取 AnimationController。 | 只有一个 animator 时直接返回该 controller；多个 animator 时按组件 id 或 nodeId 查找；找不到返回 `undefined` 或空指针。 | SDK 要求同一 descriptor 绑定多个 Image 时传唯一 id。 | AC-5.1, AC-5.2 |
| R-25 | 行为 | AnimationController 执行 start/stop/pause/resume/getStatus。 | start 映射 finish+forward；stop 映射 finish；pause 映射 pause；resume 映射 forward；status 读取 native control status。 | C API controller 操作遇到空 controller 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | AC-5.3, AC-5.4 |
| R-26 | 恢复 | Animated 组件解绑或注销更新回调。 | 对应 animator 先 pause，然后删除 callback、animator 和 imageSource。 | 不影响同一 descriptor 绑定的其他 nodeId。 | AC-5.5 |
| R-27 | 行为 | C API 创建 descriptor。 | 非空 PixelMap 创建静态 descriptor；非空 PixelMap 数组创建 animated descriptor，跳过数组内空元素并设置默认 duration=-1、iteration=1。 | 创建接口返回指针，创建失败返回 `nullptr`。 | AC-6.1, AC-6.2 |
| R-28 | 恢复 | C API dispose descriptor。 | 空指针无操作；非空且包含 newDrawableDescriptor 时减少引用计数后 delete wrapper。 | Dispose 后调用方不得继续使用旧指针。 | AC-6.3 |
| R-29 | 边界 | C API 静态/动画 PixelMap getter 接收空 descriptor。 | 静态 PixelMap getter 返回 `nullptr`，动画数组 getter 返回 `nullptr`，动画数组 size getter 返回 0。 | 这些 getter 不返回错误码。 | AC-6.4 |
| R-30 | 边界 | C API duration/iteration getter 或 setter 接收空 descriptor 或非动画 descriptor。 | setter 无操作；`GetAnimationDuration` 返回 -1，`GetAnimationIteration` 返回 1。 | 这些基础动画参数 API 不返回错误码。 | AC-6.5 |
| R-31 | 异常 | C API `Set/GetAnimationFrameDurations` 参数无效。 | 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 无效条件包括 descriptor 空、非 animated、durations 空、size 空、size=0、帧数为 0 或 size 与帧数不一致。 | AC-6.6 |
| R-32 | 边界 | C API `SetAnimationAutoPlay(autoPlay)`。 | `autoPlay != 0` 按 true 处理，`autoPlay == 0` 按 false 处理；getter 需要非空输出指针。 | descriptor 空、非 animated 或输出指针空返回参数错误。 | AC-6.7 |
| R-33 | 异常 | C API `Set/GetAnimationStopMode` 参数无效。 | mode 不在 FIRST_FRAME=0 和 LAST_FRAME=1 范围时返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | getter 输出指针为空也返回参数错误。 | AC-6.8 |
| R-34 | 异常 | C API 创建 AnimationController。 | 非 animated descriptor、空 controller 输出指针、未绑定对应 animated descriptor 的 node 均返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 实现直接读取 `node->uiNodeHandle`，调用方必须传入有效 node。 | AC-6.9 |
| R-35 | 异常 | C API controller 操作或状态查询参数无效。 | 空 controller、底层 controller 为空、status 输出为空时返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | Dispose controller 时空指针无操作。 | AC-6.10 |
| R-36 | 行为 | NAPI bridge 从 ArkTS descriptor 提取 native descriptor。 | 非 Layered descriptor 增加 core 引用计数并保存 `newDrawableDescriptor`；Layered descriptor 用合成 PixelMap 创建旧 Napi descriptor wrapper。 | 该 bridge 是 ArkTS 到 Native 单向提取，不把 Native 子类型反传 ArkTS。 | AC-7.1, AC-7.2 |
| R-37 | 异常 | NAPI/ANI bridge 输入对象无 native 对象。 | NAPI unwrap 为空或 ANI `nativeObj==0` 返回 `ERROR_CODE_PARAM_INVALID`。 | Dynamic release 后 unwrap 为空会进入该错误路径。 | AC-7.3, AC-7.5 |
| R-38 | 行为 | Resource NAPI/ANI bridge 输入资源对象。 | NAPI 使用 JS media parse API 生成 `ArkUI_Resource`；ANI 读取 bundle/module/id/type/param 后调用 static resource parse API。 | ANI parse API 缺失返回 `ERROR_CODE_INTERNAL_ERROR`。 | AC-7.4, AC-7.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1 到 AC-1.7 | SDK 声明审查 + Dynamic/Static 实现审查 + core UT | 基类默认行为、load 返回结构、Dynamic release 111002、Static release 后降级、Picture invalidate。 |
| VM-2 | AC-2.1 到 AC-2.8 | SDK 声明审查 + core UT + inner_api UT | Layered 类型、三层 getter、blendMode 有效/无效边界、合成路径、mask clip path。 |
| VM-3 | AC-3.1 到 AC-3.6 | SDK 声明审查 + core UT | PixelMap 直接包装、ResourceStr 解析、loader error、Picture/HDR 缓存和回退。 |
| VM-4 | AC-4.1 到 AC-4.8 | SDK 声明审查 + core UT | Animated 构造、frame duration 优先级、duration/iteration 边界、autoPlay、stopMode。 |
| VM-5 | AC-5.1 到 AC-5.5 | SDK 声明审查 + core/NodeModel 实现审查 | per-node controller、id 查找、controller 操作映射、注销清理。 |
| VM-6 | AC-6.1 到 AC-6.10 | C API header/implementation 审查 | 创建/销毁、默认返回、错误码、帧时长、autoPlay、stopMode、controller 参数错误。 |
| VM-7 | AC-7.1 到 AC-7.5 | NAPI/ANI bridge 实现审查 | ArkTS 到 Native wrapper 创建、Layered 特例、资源解析、引用计数、错误码。 |
| VM-8 | 全部 C API AC | 测试缺口审查 | `rg "OH_ArkUI_DrawableDescriptor_" test/unittest` 未发现直接 C API 调用用例；后续新增 C API 定向 UT 时按 AC-6 系列补齐。 |

## API 变更分析

本特性为已有实现补录，无产品代码新增或 API 新增。下表按当前 SDK 和 C API header 补齐既有 API 规格，作为后续 SDD 的基线。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `DrawableDescriptorLoadedResult` | System API | 无 | `imageWidth:number`, `imageHeight:number` | N/A | Dynamic API 21 起的加载结果；Static API 23 起为 `int` 字段。 | AC-1.2 |
| `DrawableDescriptor.constructor()` | System API | 无 | `DrawableDescriptor` | N/A | 创建基类 descriptor；Dynamic since 10，Static since 23。 | AC-1.1 |
| `DrawableDescriptor.getPixelMap()` | System API | 无 | Dynamic: `image.PixelMap`; Static: `image.PixelMap 或 undefined` | Dynamic: 111002 | 获取 descriptor 对应 PixelMap。 | AC-1.1, AC-1.5, AC-1.6 |
| `DrawableDescriptor.loadSync()` | System API | 无 | `DrawableDescriptorLoadedResult` | Dynamic: 111001, 111002; Static: 111001 | 同步加载图像并返回宽高。 | AC-1.2, AC-1.3, AC-1.6 |
| `DrawableDescriptor.load()` | System API | 无 | `Promise<DrawableDescriptorLoadedResult>` | Dynamic: 111001, 111002; Static: 111001 | 异步加载图像并返回宽高。 | AC-1.2, AC-1.3, AC-1.6 |
| `DrawableDescriptor.release()` | System API | 无 | `void` | N/A | API 26 起显式释放 descriptor native 资源；重复调用不崩溃。 | AC-1.4, AC-1.5, AC-1.6 |
| `DrawableDescriptor.isReleased()` | System API | 无 | `boolean` | N/A | API 26 起查询 release 状态。 | AC-1.4 |
| `DrawableDescriptor.invalidate()` | System API | 无 | `void` | N/A | API 26 起刷新 descriptor；当前仅 Picture 生效，未绑定组件时无操作。 | AC-1.7 |
| `LayeredDrawableDescriptor.constructor()` | System API | `foreground?`, `background?`, `mask?` | `LayeredDrawableDescriptor` | Dynamic: 111002 on released getters | 创建三层 descriptor。Dynamic class since 10，构造重载 since 12，crossplatform since 23；Static since 23。 | AC-2.1, AC-2.3 |
| `LayeredDrawableDescriptor.getForeground()` | System API | 无 | Dynamic: `DrawableDescriptor`; Static: `DrawableDescriptor 或 undefined` | Dynamic: 111002 | 获取前景层 descriptor。 | AC-2.2 |
| `LayeredDrawableDescriptor.getBackground()` | System API | 无 | Dynamic: `DrawableDescriptor`; Static: `DrawableDescriptor 或 undefined` | Dynamic: 111002 | 获取背景层 descriptor。 | AC-2.2 |
| `LayeredDrawableDescriptor.getMask()` | System API | 无 | Dynamic: `DrawableDescriptor`; Static: `DrawableDescriptor 或 undefined` | Dynamic: 111002 | 获取遮罩层 descriptor。 | AC-2.2 |
| `LayeredDrawableDescriptor.setBlendMode()` | System API | Dynamic: `drawing.BlendMode`; Static: `drawing.BlendMode 或 undefined` | `void` | N/A | 设置三层合成 blend mode，并改变绘制顺序。 | AC-2.4, AC-2.5 |
| `LayeredDrawableDescriptor.getMaskClipPath()` | System API | 无 | `string` | N/A | 返回内置自适应图标 mask clip path。 | AC-2.8 |
| `PixelMapDrawableDescriptor.constructor()` | System API | `image.PixelMap`; API 26 起支持 `ResourceStr` | `PixelMapDrawableDescriptor` | load 时可能 111001/111002 | 直接包装 PixelMap 或从 ResourceStr 加载 PixelMap。 | AC-3.1, AC-3.2 |
| `AnimationStopMode` | System API | N/A | `FIRST_FRAME=0`, `LAST_FRAME=1` | N/A | API 24 起定义动画停止帧。 | AC-4.8 |
| `AnimationOptions` | System API | `duration?`, `iterations?`, `frameDurations?`, `autoPlay?`, `stopMode?` | N/A | N/A | 配置 Animated descriptor 播放时长、次数、逐帧时长、自动播放和停止模式。 | AC-4.3 到 AC-4.8 |
| `AnimationController` | System API | 无 | `start/stop/pause/resume:void`, `getStatus():AnimationStatus` | N/A | 控制单个绑定组件的动画。 | AC-5.3, AC-5.4 |
| `AnimatedDrawableDescriptor.constructor()` | System API | `Array<image.PixelMap>` 或 `ResourceStr / Array<image.PixelMap>`, `options?` | `AnimatedDrawableDescriptor` | load 时可能 111001/111002 | 创建 PixelMap 序列或资源动图 descriptor。 | AC-4.1, AC-4.2 |
| `AnimatedDrawableDescriptor.getAnimationController()` | System API | `id?: string` | `AnimationController 或 undefined` | N/A | 获取与组件一一对应的动画控制器。 | AC-5.1, AC-5.2 |
| `HdrCompositionConfig` | System API | `rect: Rectangle` | N/A | N/A | API 26 起定义 Picture HDR 合成区域。 | AC-3.5 |
| `PictureDrawableDescriptor.constructor()` | System API | `image.Picture` | `PictureDrawableDescriptor` | load 时可能 111001/111002 | API 26 起包装 Picture。 | AC-3.4 |
| `PictureDrawableDescriptor.setHdrComposition()` | System API | `HdrCompositionConfig` | `void` | N/A | 设置 HDR FOV 合成配置。 | AC-3.5 |
| `OH_ArkUI_DrawableDescriptor_CreateFromPixelMap` | Public C API | `OH_PixelmapNativeHandle pixelMap` | `ArkUI_DrawableDescriptor*` | N/A | 从 PixelMap 创建 descriptor，空入参返回空。 | AC-6.1 |
| `OH_ArkUI_DrawableDescriptor_CreateFromAnimatedPixelMap` | Public C API | `OH_PixelmapNativeHandle* array`, `int32_t size` | `ArkUI_DrawableDescriptor*` | N/A | 从 PixelMap 数组创建 animated descriptor。 | AC-6.2 |
| `OH_ArkUI_DrawableDescriptor_Dispose` | Public C API | `ArkUI_DrawableDescriptor*` | `void` | N/A | 释放 C API wrapper。 | AC-6.3 |
| `OH_ArkUI_DrawableDescriptor_GetStaticPixelMap` | Public C API | `ArkUI_DrawableDescriptor*` | `OH_PixelmapNativeHandle` | N/A | 获取静态 PixelMap handle。 | AC-6.4 |
| `OH_ArkUI_DrawableDescriptor_GetAnimatedPixelMapArray` | Public C API | `ArkUI_DrawableDescriptor*` | `OH_PixelmapNativeHandle*` | N/A | 获取 animated PixelMap 数组。 | AC-6.4 |
| `OH_ArkUI_DrawableDescriptor_GetAnimatedPixelMapArraySize` | Public C API | `ArkUI_DrawableDescriptor*` | `int32_t` | N/A | 获取 animated PixelMap 数组长度。 | AC-6.4 |
| `OH_ArkUI_DrawableDescriptor_SetAnimationDuration` | Public C API | `ArkUI_DrawableDescriptor*`, `int32_t duration` | `void` | N/A | 设置 animated 总时长。 | AC-6.5 |
| `OH_ArkUI_DrawableDescriptor_GetAnimationDuration` | Public C API | `ArkUI_DrawableDescriptor*` | `int32_t` | N/A | 获取 animated 总时长；空或非 animated 返回 -1。 | AC-6.5 |
| `OH_ArkUI_DrawableDescriptor_SetAnimationIteration` | Public C API | `ArkUI_DrawableDescriptor*`, `int32_t iteration` | `void` | N/A | 设置 animated 播放次数。 | AC-6.5 |
| `OH_ArkUI_DrawableDescriptor_GetAnimationIteration` | Public C API | `ArkUI_DrawableDescriptor*` | `int32_t` | N/A | 获取 animated 播放次数；空或非 animated 返回 1。 | AC-6.5 |
| `OH_ArkUI_DrawableDescriptor_SetAnimationFrameDurations` | Public C API | `ArkUI_DrawableDescriptor*`, `uint32_t* durations`, `size_t size` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 设置逐帧时长。 | AC-6.6 |
| `OH_ArkUI_DrawableDescriptor_GetAnimationFrameDurations` | Public C API | `ArkUI_DrawableDescriptor*`, `uint32_t* durations`, `size_t* size` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 获取逐帧时长。 | AC-6.6 |
| `OH_ArkUI_DrawableDescriptor_SetAnimationAutoPlay` | Public C API | `ArkUI_DrawableDescriptor*`, `uint32_t autoPlay` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 设置自动播放。 | AC-6.7 |
| `OH_ArkUI_DrawableDescriptor_GetAnimationAutoPlay` | Public C API | `ArkUI_DrawableDescriptor*`, `uint32_t* autoPlay` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 获取自动播放。 | AC-6.7 |
| `OH_ArkUI_DrawableDescriptor_SetAnimationStopMode` | Public C API | `ArkUI_DrawableDescriptor*`, `DrawableDescriptor_AnimationStopMode` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 设置停止帧模式。 | AC-6.8 |
| `OH_ArkUI_DrawableDescriptor_GetAnimationStopMode` | Public C API | `const ArkUI_DrawableDescriptor*`, `DrawableDescriptor_AnimationStopMode*` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 获取停止帧模式。 | AC-6.8 |
| `OH_ArkUI_DrawableDescriptor_CreateAnimationController` | Public C API | `ArkUI_DrawableDescriptor*`, `ArkUI_NodeHandle`, `ArkUI_DrawableDescriptor_AnimationController**` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 为指定节点创建动画控制器。 | AC-6.9 |
| `OH_ArkUI_DrawableDescriptor_DisposeAnimationController` | Public C API | `ArkUI_DrawableDescriptor_AnimationController*` | `void` | N/A | 释放动画控制器。 | AC-6.10 |
| `OH_ArkUI_DrawableDescriptor_StartAnimation` | Public C API | `ArkUI_DrawableDescriptor_AnimationController*` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 启动动画。 | AC-6.10 |
| `OH_ArkUI_DrawableDescriptor_StopAnimation` | Public C API | `ArkUI_DrawableDescriptor_AnimationController*` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 停止动画。 | AC-6.10 |
| `OH_ArkUI_DrawableDescriptor_ResumeAnimation` | Public C API | `ArkUI_DrawableDescriptor_AnimationController*` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 恢复动画。 | AC-6.10 |
| `OH_ArkUI_DrawableDescriptor_PauseAnimation` | Public C API | `ArkUI_DrawableDescriptor_AnimationController*` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 暂停动画。 | AC-6.10 |
| `OH_ArkUI_DrawableDescriptor_GetAnimationStatus` | Public C API | `ArkUI_DrawableDescriptor_AnimationController*`, `DrawableDescriptor_AnimationStatus*` | `int32_t` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 获取动画状态。 | AC-6.10 |
| `OH_ArkUI_GetDrawableDescriptorFromNapiValue` | Public C API Bridge | `napi_env`, `napi_value`, `ArkUI_DrawableDescriptor**` | `int32_t` | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID` | 从 ArkTS NAPI descriptor 对象提取 native descriptor。 | AC-7.1 到 AC-7.3 |
| `OH_ArkUI_GetDrawableDescriptorFromResourceNapiValue` | Public C API Bridge | `napi_env`, `napi_value`, `ArkUI_DrawableDescriptor**` | `int32_t` | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID` | 从 NAPI Resource 对象创建 native resource wrapper。 | AC-7.4 |
| `OH_ArkUI_NativeModule_GetDrawableDescriptorFromAniValue` | Public C API Bridge | `ani_env*`, `ani_object`, `ArkUI_DrawableDescriptor**` | `int32_t` | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID` | 从 Static ArkTS ANI descriptor 对象提取 native descriptor。 | AC-7.5 |
| `OH_ArkUI_NativeModule_GetDrawableDescriptorFromResourceAniValue` | Public C API Bridge | `ani_env*`, `ani_object`, `ArkUI_DrawableDescriptor**` | `int32_t` | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_INTERNAL_ERROR` | 从 Static ArkTS Resource 对象创建 native resource wrapper。 | AC-7.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| N/A | N/A | 本次为已有能力规格补录，无产品 API 新增、变更或废弃。 | N/A | 全部 AC |

## 接口规格

### 接口定义

**DrawableDescriptor 基类方法**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(); getPixelMap(); loadSync(); load(); release(); isReleased(); invalidate()` |
| 返回值 | 见 API 变更分析中各方法返回值。 |
| 开放范围 | System API |
| 错误码 | Dynamic `getPixelMap/loadSync/load` 可抛 111002；`loadSync/load` 资源失败可抛或 reject 111001。 |
| 关联 AC | AC-1.1 到 AC-1.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| N/A | N/A | N/A | N/A | 基类方法均无显式入参。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 未释放对象调用 `getPixelMap()` | 返回 PixelMap 或 native 空结果。 | AC-1.1 |
| 2 | 未释放非 Layered 对象调用 `loadSync/load` | 返回或 resolve 宽高结果。 | AC-1.2 |
| 3 | 资源加载失败 | 抛出或 reject 111001。 | AC-1.3 |
| 4 | Dynamic release 后继续访问 | 抛出 111002，重复 release 不崩溃。 | AC-1.4, AC-1.5 |
| 5 | Static release 后继续访问 | 返回 `undefined` 或宽高 -1。 | AC-1.6 |
| 6 | `invalidate()` 在 Picture 上调用 | 后台刷新缓存并通知绑定回调。 | AC-1.7 |

**LayeredDrawableDescriptor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `constructor(foreground?, background?, mask?); getForeground(); getBackground(); getMask(); setBlendMode(mode); static getMaskClipPath()` |
| 返回值 | getter 返回 layer descriptor；Static getter 可返回 `undefined`；`getMaskClipPath()` 返回 `string`。 |
| 开放范围 | System API |
| 错误码 | Dynamic release 后 getter 可抛 111002；blendMode 无业务错误码。 |
| 关联 AC | AC-2.1 到 AC-2.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| `foreground` | `DrawableDescriptor` | 否 | `undefined` | 存在时取其 PixelMap 作为前景层。 |
| `background` | `DrawableDescriptor` | 否 | `undefined` | 存在时取其 PixelMap 作为背景层。 |
| `mask` | `DrawableDescriptor` | 否 | `undefined` | 存在时取其 PixelMap 作为遮罩层，缺省时可走默认 mask 初始化。 |
| `mode` | `drawing.BlendMode` 或 `undefined` | Dynamic 是，Static 否 | `undefined` | 有效范围为 Rosen `CLEAR` 到 `LUMINOSITY`；Static `undefined` 不调用 native set。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 构造后查询类型 | 类型为 LAYERED。 | AC-2.1 |
| 2 | getter 查询三层 | 返回对应 layer descriptor 或 optional 空。 | AC-2.2 |
| 3 | 合法 blendMode | 改变合成顺序并保存 mode。 | AC-2.4 |
| 4 | 非法 blendMode 或 `undefined` | 不改变已有 mode。 | AC-2.5 |
| 5 | foreground 为 288x288 | 非自适应合成，输出 192x192。 | AC-2.6 |
| 6 | 数据不足 | 返回空 PixelMap。 | AC-2.7 |

**PixelMapDrawableDescriptor 与 PictureDrawableDescriptor**

| 属性 | 值 |
|------|-----|
| 函数签名 | `new PixelMapDrawableDescriptor(src?); new PictureDrawableDescriptor(src); PictureDrawableDescriptor.setHdrComposition(config)` |
| 返回值 | descriptor 实例；`setHdrComposition` 返回 `void`。 |
| 开放范围 | System API |
| 错误码 | 加载失败通过基类 `load/loadSync` 映射为 111001；release 后按 Dynamic/Static 差异处理。 |
| 关联 AC | AC-3.1 到 AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| `src` | `image.PixelMap` | 否 | `undefined` | PixelMap descriptor 直接保存 PixelMap。 |
| `src` | `ResourceStr` | 否 | `undefined` | API 26 起支持 Resource、`file:` URI、合法 base64。 |
| `src` | `image.Picture` | 是 | 无 | Picture descriptor 必须有 Picture 才能成功加载。 |
| `config.rect` | `Rectangle` | 是 | 无 | `width>0` 且 `height>0` 时 HDR 配置有效。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | PixelMap 入参构造 | `getPixelMap/loadSync` 使用同一 PixelMap。 | AC-3.1 |
| 2 | ResourceStr 构造 | 通过 loader 读取并解码。 | AC-3.2 |
| 3 | loader 无数据 | 加载错误。 | AC-3.3 |
| 4 | Picture load 成功 | 缓存 main pixel 或 HDR 合成结果。 | AC-3.4 |
| 5 | HDR rect 无效 | 不执行 HDR FOV 合成。 | AC-3.5 |
| 6 | Picture 未加载先 `getPixelMap` | 返回空缓存。 | AC-3.6 |

**AnimatedDrawableDescriptor 与 AnimationController**

| 属性 | 值 |
|------|-----|
| 函数签名 | `new AnimatedDrawableDescriptor(pixelMaps, options?); new AnimatedDrawableDescriptor(src, options?); getAnimationController(id?)` |
| 返回值 | descriptor 实例；`getAnimationController` 返回 `AnimationController 或 undefined`。 |
| 开放范围 | System API |
| 错误码 | 加载失败通过基类 `load/loadSync` 映射；controller 获取失败返回 `undefined`。 |
| 关联 AC | AC-4.1 到 AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| `pixelMaps` | `Array<image.PixelMap>` | 是 | 无 | 非空数组才有帧；空数组帧数为 0。 |
| `src` | `ResourceStr` 或 `Array<image.PixelMap>` | 是 | 无 | Resource、`file:` URI、base64 或 PixelMap 数组。 |
| `options.duration` | `number/int` | 否 | PixelMap 数组每帧 1000ms，资源动图使用内嵌 delay | 取值范围 `[0,+∞)`；负数按默认规则。 |
| `options.iterations` | `number/int` | 否 | 1 | `-1` 无限，`0` 不播放，正数为次数，`<-1` 恢复为 1。 |
| `options.frameDurations` | `Array<number/int>` | 否 | 无 | 非空时覆盖 duration；C API 要求长度等于帧数。 |
| `options.autoPlay` | `boolean` | 否 | `true` | false 时可见状态不自动播放，只刷新首帧。 |
| `options.stopMode` | `AnimationStopMode` | 否 | `FIRST_FRAME` | 仅 FIRST_FRAME=0 或 LAST_FRAME=1 有效。 |
| `id` | `string` | 否 | 空字符串 | 多组件共享时必须传唯一组件 id。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | PixelMap 数组构造 | 第一帧作为 PixelMap，帧数等于数组长度。 | AC-4.1 |
| 2 | frameDurations 非空 | 覆盖 duration，求和为总时长。 | AC-4.3 |
| 3 | duration 非负且无 frameDurations | 均分到各帧。 | AC-4.4 |
| 4 | iterations 小于 -1 | 归一为 1。 | AC-4.6 |
| 5 | autoPlay false | 可见时刷新首帧，不 forward。 | AC-4.7 |
| 6 | stopMode LAST_FRAME | stop 后刷新最后一帧。 | AC-4.8 |
| 7 | 单组件绑定取 controller | id 可省略。 | AC-5.1 |
| 8 | 多组件绑定未传正确 id | 返回 `undefined`。 | AC-5.2 |
| 9 | controller 操作 | 映射到 native start/stop/pause/resume/status。 | AC-5.3, AC-5.4 |

**NDK DrawableDescriptor C API**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_DrawableDescriptor_*` descriptor 创建、访问、动画配置和 controller 操作函数。 |
| 返回值 | 创建函数返回指针；部分 getter 返回指针或 int；配置和控制函数返回 `int32_t`。 |
| 开放范围 | Public C API |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID`；部分 legacy getter 使用默认返回值而非错误码。 |
| 关联 AC | AC-6.1 到 AC-6.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| `pixelMap` | `OH_PixelmapNativeHandle` | 是 | 无 | 空指针创建失败并返回 `nullptr`。 |
| `array` | `OH_PixelmapNativeHandle*` | 是 | 无 | 空数组指针创建失败；数组内空元素被跳过。 |
| `size` | `int32_t` 或 `size_t` | 是 | 无 | 帧时长配置要求 size 非 0 且等于 frameCount。 |
| `drawableDescriptor` | `ArkUI_DrawableDescriptor*` | 是 | 无 | 对动画配置/控制必须包含 `newDrawableDescriptor`。 |
| `durations` | `uint32_t*` | 是 | 无 | setter/getter 均不能为 null。 |
| `autoPlay` | `uint32_t` | 是 | 1 | 非 0 为 true，0 为 false。 |
| `mode` | `DrawableDescriptor_AnimationStopMode` | 是 | FIRST_FRAME | 仅 0 或 1 有效。 |
| `node` | `ArkUI_NodeHandle` | 是 | 无 | 必须是有效节点且已绑定该 animated descriptor。 |
| `controller` | `ArkUI_DrawableDescriptor_AnimationController*` 或 `**` | 是 | 无 | 输出指针或控制器指针不能为空。 |
| `status` | `DrawableDescriptor_AnimationStatus*` | 是 | 无 | 查询状态时不能为空。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | PixelMap handle 非空 | 创建静态 descriptor。 | AC-6.1 |
| 2 | PixelMap 数组非空 | 创建 animated descriptor 并初始化默认动画参数。 | AC-6.2 |
| 3 | Dispose 空指针 | 无操作。 | AC-6.3 |
| 4 | 空 descriptor 调 getter | 返回空指针、0、-1 或 1。 | AC-6.4, AC-6.5 |
| 5 | 帧时长参数无效 | 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | AC-6.6 |
| 6 | autoPlay 非 0 | 写入 true。 | AC-6.7 |
| 7 | stopMode 越界 | 返回参数错误。 | AC-6.8 |
| 8 | node 未绑定动画 descriptor | 创建 controller 返回参数错误。 | AC-6.9 |
| 9 | controller 操作参数为空 | 返回参数错误。 | AC-6.10 |

**ArkTS 到 Native Bridge API**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_GetDrawableDescriptorFromNapiValue`, `OH_ArkUI_GetDrawableDescriptorFromResourceNapiValue`, `OH_ArkUI_NativeModule_GetDrawableDescriptorFromAniValue`, `OH_ArkUI_NativeModule_GetDrawableDescriptorFromResourceAniValue` |
| 返回值 | `int32_t` 错误码，并通过输出参数返回 `ArkUI_DrawableDescriptor*`。 |
| 开放范围 | Public C API Bridge |
| 错误码 | `ERROR_CODE_NO_ERROR`, `ERROR_CODE_PARAM_INVALID`, ANI resource parse 缺失时 `ERROR_CODE_INTERNAL_ERROR`。 |
| 关联 AC | AC-7.1 到 AC-7.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| `env` | `napi_env` 或 `ani_env*` | 是 | 无 | 必须匹配对应运行时。 |
| `value` | `napi_value` 或 `ani_object` | 是 | 无 | descriptor 对象必须可 unwrap 或具有非 0 `nativeObj`。 |
| `drawableDescriptor` | `ArkUI_DrawableDescriptor**` | 是 | 无 | 输出参数必须非空。 |
| resource fields | Resource object | 是 | 无 | Resource bridge 需要 bundle/module/id/type/param 或 JS media parse API。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | NAPI 非 Layered descriptor | 增加 core 引用计数并返回 wrapper。 | AC-7.1 |
| 2 | NAPI Layered descriptor | 以合成 PixelMap 创建 Napi descriptor wrapper。 | AC-7.2 |
| 3 | unwrap 失败或已释放 | 返回参数错误。 | AC-7.3 |
| 4 | Resource bridge | 生成 `ArkUI_Resource` wrapper。 | AC-7.4 |
| 5 | ANI `nativeObj==0` | 返回参数错误。 | AC-7.5 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次只补录规格，不修改产品代码。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic `DrawableDescriptor/LayeredDrawableDescriptor` 自 API 10；NDK C API 基础 descriptor 自 API 12；Static API 自 API 23。
- **API 版本号策略:** Dynamic SDK 以 `@since 10/12/21/23/24/26` 标注能力演进；Static SDK 以 `@since 23/24/26 static` 标注；C API 以 header `@since 12/22/24` 标注。
- **Dynamic/Static 返回值差异:** Dynamic `getPixelMap()` 和 Layered getter 返回非 optional 类型，Static 对应 getter 返回 `undefined` 能力；Dynamic release 后声明 111002，Static 实现返回 `undefined` 或宽高 -1。
- **Layered load 差异:** Dynamic `load()` 对 Layered 返回 `undefined`，`loadSync()` 对 Layered 不走 core LoadSync；SDK 对基类描述 load 能力时未逐类展开该差异。
- **Picture factory 差异:** Core `DrawableType` 包含 PICTURE=4，但 `OHOS_ACE_CreateDrawableDescriptorByType` 拒绝 type > PIXELMAP，C API create-by-type 路径不能创建 Picture。
- **C API 返回风格差异:** 部分 C API getter 用默认值表达无效对象，例如 duration=-1、iteration=1、array size=0；新增动画配置/控制接口返回标准错误码。
- **Previewer 兼容性:** Dynamic SDK 文件说明该模块可在真机预览效果，不支持 DevEco Studio Previewer。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 声明优先 | 外部 API 类型、错误码和版本以 `interface/sdk-js/api/` 与 `interfaces/native/` 头文件为契约。 | 全部 AC |
| 实现即规格 | 已有实现中 Dynamic/Static release 后行为不同，规格记录差异，不在本次修改实现。 | AC-1.5, AC-1.6 |
| core drawable 类型稳定 | `DrawableType` 数值已被测试固定，不能改变枚举顺序或含义。 | AC-2.1 |
| C API ABI 稳定 | `ArkUI_DrawableDescriptor` 和 controller 为不透明指针，公开 header 不暴露内部布局。 | AC-6.1 到 AC-6.10 |
| Animated per-node 状态隔离 | 一个 descriptor 可绑定多个 nodeId，每个 nodeId 独立 animator/callback/imageSource。 | AC-5.1 到 AC-5.5 |
| Picture invalidate 异步化 | Picture invalidate 通过后台任务重载 PixelMap，并且只保留一个最新 pending 任务。 | AC-1.7, AC-3.4 |
| 资源加载集中化 | ResourceStr 解析和加载必须经过 `DrawableDescriptorInfo` 与 `DrawableDescriptorLoader`，避免各子类重复解析。 | AC-3.2, AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无新增性能指标；本次不改变解码、合成或动画执行路径。 | 规格审查 | 仅文档变更。 |
| 功耗 | N/A，本特性无新增后台常驻任务；Picture invalidate 仍按既有按需后台任务执行。 | 实现审查 | `picture_drawable_descriptor.cpp:220` |
| 内存 | TS Dynamic 提供 `release()`，C API 提供 `Dispose`，Bridge 成功提取时增加引用计数并在释放时减少引用计数。 | 实现审查 | `js_drawable_descriptor.cpp:896`, `interfaces/native/node/drawable_descriptor.cpp:66`, `native_node_napi.cpp:386` |
| 安全 | ResourceStr 仅按 RESOURCE、`file:` URI、合法 base64 头解析；不识别输入返回空数据。 | 实现审查 | `drawable_descriptor_info.cpp:34`, `drawable_descriptor_loader.cpp:64` |
| 可靠性 | Dynamic release 重复调用不崩溃；Static release 后短路返回；C API 空指针多数返回空、默认值或参数错误。 | 实现审查 | `js_drawable_descriptor.cpp:908`, `@ohos.arkui.drawableDescriptor.ets:94`, `interfaces/native/node/drawable_descriptor.cpp:122` |
| 可测试性 | Core drawable 已有基类、PixelMap、Layered、Animated、Picture 和 loader 单测；C API direct wrapper 调用存在测试缺口。 | 单测审查 | `drawable_descriptor_test.cpp:164`, `drawable_descriptor_test.cpp:621`, `drawable_descriptor_test.cpp:1306` |
| 自动化维测 | 无新增自动化维测接口。 | N/A | 本次为规格补录。 |
| 定界定位 | load 失败通过 111001 或内部 errorCode，release 后 Dynamic 通过 111002，C API 通过参数错误码定界。 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:100`, `js_drawable_descriptor.cpp:107`, `drawable_descriptor.h:215` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无设备特有差异 | DrawableDescriptor 为资源描述和加载对象，行为由输入资源、API 版本和绑定组件状态决定。 | SDK/实现审查 | `@ohos.arkui.drawableDescriptor.d.ts:16` |
| 平板 | 无设备特有差异 | 同手机。 | SDK/实现审查 | `frameworks/core/drawable/` |
| 折叠屏 | 无设备特有差异 | 同手机；多窗口/可见性只影响 Animated auto pause/play，按组件可见状态处理。 | 实现审查 | `animated_drawable_descriptor.cpp:72`, `@ohos.arkui.drawableDescriptor.d.ts:552` |
| DevEco Studio Previewer | 有限制 | SDK 说明可在真机预览效果，不支持 DevEco Studio Previewer。 | SDK 审查 | `@ohos.arkui.drawableDescriptor.d.ts:20` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | DrawableDescriptor 本身不进入无障碍树；绑定 Image 的无障碍由组件处理。 | AC-1.1 |
| 大字体 | 否 | 不涉及文本布局或字体缩放。 | N/A |
| 深色模式 | 间接 | descriptor 不感知主题；资源选择由 ResourceManager 或资源对象决定。 | AC-3.2 |
| 多窗口/分屏 | 间接 | Animated 由组件可见状态控制播放/暂停，不直接读取窗口状态。 | AC-4.7 |
| 多用户 | 否 | 不直接处理用户数据隔离。 | N/A |
| 版本升级 | 是 | API 10 到 26 存在新增能力和 Dynamic/Static 差异，需要按兼容性声明验证。 | 全部 AC |
| 生态兼容 | 是 | C API 为 Public ABI，需要保持不透明句柄和错误码语义稳定。 | AC-6.1 到 AC-7.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DrawableDescriptor 加载和释放
  作为 ArkTS 调用者
  我想要获取 PixelMap 并显式释放 descriptor
  以便控制 drawable 资源生命周期

  Scenario: Dynamic release 后访问抛出 111002
    Given 一个 Dynamic DrawableDescriptor 已经成功创建
    When 调用 release() 后再次调用 getPixelMap()
    Then 抛出 BusinessError 111002
    And isReleased() 返回 true

  Scenario: Static release 后返回降级值
    Given 一个 Static DrawableDescriptor 已经成功创建
    When 调用 release() 后再次调用 loadSync()
    Then 返回 imageWidth=-1
    And 返回 imageHeight=-1

  Scenario Outline: Layered blendMode 边界
    Given 一个 LayeredDrawableDescriptor
    When 调用 setBlendMode(<mode>)
    Then 合成状态为 <result>

    Examples:
      | mode | result |
      | CLEAR | 更新 blendMode 并启用 foregroundOverBackground |
      | LUMINOSITY | 更新 blendMode 并启用 foregroundOverBackground |
      | LUMINOSITY+1 | 保持原状态 |

  Scenario: Animated frameDurations 覆盖 duration
    Given 一个 AnimatedDrawableDescriptor 有 3 帧
    When options.frameDurations 设置为 [100, 200, 300]
    Then 总时长为 600ms
    And options.duration 不再参与分帧

  Scenario: C API 创建未绑定 controller 失败
    Given 一个 animated ArkUI_DrawableDescriptor
    And 一个未绑定该 descriptor 的 ArkUI_NodeHandle
    When 调用 OH_ArkUI_DrawableDescriptor_CreateAnimationController
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID
```

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
    query: "DrawableDescriptor Dynamic Static SDK C API core drawable implementation release load layered animated picture"
  - repo: "OpenHarmony/interface/sdk-js"
    query: "@ohos.arkui.drawableDescriptor dynamic and static declarations"
```

**关键文档：**

- `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.d.ts`
- `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.static.d.ets`
- `interfaces/native/drawable_descriptor.h`
- `interfaces/native/native_node_napi.h`
- `interfaces/native/native_node_ani.h`
- `frameworks/core/drawable/`
