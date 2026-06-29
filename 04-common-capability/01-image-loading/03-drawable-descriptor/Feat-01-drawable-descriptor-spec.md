# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | DrawableDescriptor 能力 (TS + C API) |
| 特性编号 | Feat-01 |
| 所属 FuncID | 04-01-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10 ~ 26 |
| SIG 归属 | ArkUI |
| 状态 | Baselined |
| 复杂度 | 标准 |

DrawableDescriptor 是 ArkUI 中用于表示 drawable 资源描述符的抽象层次，提供从资源管理系统加载、获取 PixelMap、控制动画播放的能力。本特性覆盖 5 个 TS 类（DrawableDescriptor / LayeredDrawableDescriptor / PixelMapDrawableDescriptor / AnimatedDrawableDescriptor / PictureDrawableDescriptor）、C API（20+ 函数）、以及 ArkTS↔Native 跨前端 Bridge。

## 本次变更范围（Delta）

> 存量特性补录（lineage: new），无 Delta。

## 输入文档

- 需求基线：本特性为已有实现能力补录，无独立 requirement.md
- 设计文档：[design.md](design.md)
- SDK 声明文件（权威来源）：
  - Dynamic API: `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.d.ts`
  - Static API: `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.static.d.ets`
- C API 头文件: `interfaces/native/drawable_descriptor.h`
- C API Bridge: `interfaces/native/native_node_napi.h`, `interfaces/native/native_node_ani.h`
- 核心实现: `frameworks/core/drawable/`

## 用户故事

### US-1: 基础 DrawableDescriptor 使用

作为应用开发者，我想要通过资源 ID 创建 DrawableDescriptor 并获取其 PixelMap，以便将 drawable 资源渲染到 Image 组件中。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 通过资源管理系统获取 DrawableDescriptor 后 THEN 调用 `getPixelMap()` 返回有效的 `image.PixelMap` 对象 | 正常 |
| AC-1.2 | WHEN 调用 `loadSync()` THEN 同步返回 `DrawableDescriptorLoadedResult`，包含 `imageWidth` 和 `imageHeight` | 正常 |
| AC-1.3 | WHEN 调用 `load()` THEN 异步返回 `Promise<DrawableDescriptorLoadedResult>` | 正常 |
| AC-1.4 | WHEN 调用 `release()` 后 THEN 后续任何方法调用抛出 BusinessError 111002 | 正常 |
| AC-1.5 | WHEN 调用 `isReleased()` THEN 已释放返回 `true`，未释放返回 `false` | 正常 |
| AC-1.6 | WHEN DrawableDescriptor 已绑定到组件且调用 `invalidate()` THEN 触发组件重绘 | 异常 |

### US-2: LayeredDrawableDescriptor 多层合成

作为应用开发者，我想要使用 LayeredDrawableDescriptor 获取前景、背景、遮罩三层独立的 DrawableDescriptor，以便实现分层图标效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 通过资源 ID 创建 `LayeredDrawableDescriptor` 后 THEN `GetDrawableType()` 返回 `DrawableType::LAYERED` | 正常 |
| AC-2.2 | WHEN 调用 `getForeground()` THEN 返回前景层的 `DrawableDescriptor` 对象 | 正常 |
| AC-2.3 | WHEN 调用 `getBackground()` THEN 返回背景层的 `DrawableDescriptor` 对象 | 正常 |
| AC-2.4 | WHEN 调用 `getMask()` THEN 按优先级 maskPath → defaultMask(name) 返回遮罩层 `DrawableDescriptor`；均失败返回 `nullptr` | 异常 |
| AC-2.5 | WHEN 调用 `getMaskClipPath()` (静态方法) THEN 返回自适应图标遮罩的 clip path 字符串 | 正常 |
| AC-2.6 | WHEN 调用 `setBlendMode(mode)` THEN 设置合成混合模式，且 `foregroundOverBackground` 自动设为 `true` | 正常 |
| AC-2.7 | WHEN 通过 `constructor(foreground, background, mask)` 构造 THEN 三层独立设置，不依赖资源管理系统 | 正常 |
| AC-2.8 | WHEN 调用 `getPixelMap()` THEN 合成前景/背景/遮罩三层为单张 PixelMap（288x288 前景走非自适应路径，否则走自适应缩放路径） | 正常 |

### US-3: AnimatedDrawableDescriptor 帧动画

作为应用开发者，我想要使用 AnimatedDrawableDescriptor 播放 PixelMap 帧动画，并控制播放状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 通过 `new AnimatedDrawableDescriptor(pixelMaps, options)` 构造 THEN 传入的 PixelMap 数组作为动画帧 | 正常 |
| AC-3.2 | WHEN 通过 `new AnimatedDrawableDescriptor(src, options)` 构造（ResourceStr 路径） THEN 从资源路径加载动画帧 | 正常 |
| AC-3.3 | WHEN 设置 `AnimationOptions.duration` THEN `totalDuration_` 被设置；不设置时由帧时长数组自动计算 | 异常 |
| AC-3.4 | WHEN 设置 `AnimationOptions.iterations` THEN 控制动画播放次数（默认 1） | 正常 |
| AC-3.5 | WHEN 设置 `AnimationOptions.autoPlay = false` THEN 动画不会自动播放 | 正常 |
| AC-3.6 | WHEN 设置 `AnimationOptions.stopMode = LAST_FRAME` THEN 停止时停在最后一帧，否则停在首帧 | 正常 |
| AC-3.7 | WHEN 调用 `getAnimationController(id)` THEN 返回该组件 ID 对应的 `AnimationController` 对象；不传 id 时使用默认 controller | 异常 |
| AC-3.8 | WHEN 通过 AnimationController 调用 `start()` / `stop()` / `pause()` / `resume()` THEN 动画进入对应播放状态 | 正常 |
| AC-3.9 | WHEN 通过 AnimationController 调用 `getStatus()` THEN 返回当前动画状态（INITIAL / RUNNING / PAUSED / STOPPED） | 正常 |
| AC-3.10 | WHEN 同一个 AnimatedDrawableDescriptor 被多个组件共享 THEN 每个组件通过 `nodeId` 持有独立的 `ControlledAnimator`，互不影响 | 正常 |

### US-4: PixelMapDrawableDescriptor

作为应用开发者，我想要直接传入 PixelMap 或 ResourceStr 来创建 DrawableDescriptor，无需通过资源管理系统。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 通过 `new PixelMapDrawableDescriptor(pixelMap)` 构造 THEN 直接包装传入的 PixelMap | 正常 |
| AC-4.2 | WHEN 通过 `new PixelMapDrawableDescriptor(resourceStr)` 构造 THEN 从 ResourceStr 路径加载 PixelMap | 正常 |

### US-5: PictureDrawableDescriptor

作为应用开发者，我想要使用 PictureDrawableDescriptor 处理 Picture 类型的 drawable 资源，并支持 HDR 合成。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 通过 `new PictureDrawableDescriptor(picture)` 构造 THEN 包装传入的 `image.Picture` 对象 | 正常 |
| AC-5.2 | WHEN 调用 `setHdrComposition(config)` THEN 设置 HDR 合成区域（rect: x/y/width/height） | 正常 |
| AC-5.3 | WHEN 调用 `getPixelMap()` 且已设置 HDR 配置 THEN 执行 HDR 合成并返回合成后的 PixelMap | 正常 |

### US-6: C API 使用

作为 NDK 开发者，我想要通过 C API 创建、配置和控制 DrawableDescriptor。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `OH_ArkUI_DrawableDescriptor_CreateFromPixelMap(pixelMap)` THEN 返回 `ArkUI_DrawableDescriptor*`，包装单个 PixelMap | 正常 |
| AC-6.2 | WHEN 调用 `OH_ArkUI_DrawableDescriptor_CreateFromAnimatedPixelMap(array, size)` THEN 返回包装 PixelMap 数组的 `ArkUI_DrawableDescriptor*` | 正常 |
| AC-6.3 | WHEN 调用 `OH_ArkUI_DrawableDescriptor_Dispose(descriptor)` THEN 释放内存，后续任何访问行为未定义 | 正常 |
| AC-6.4 | WHEN 调用 `OH_ArkUI_DrawableDescriptor_GetStaticPixelMap` THEN 返回首个 PixelMap | 正常 |
| AC-6.5 | WHEN 调用 `OH_ArkUI_DrawableDescriptor_GetAnimatedPixelMapArray` / `GetAnimatedPixelMapArraySize` THEN 返回动画 PixelMap 数组及其大小 | 正常 |
| AC-6.6 | WHEN 调用 `SetAnimationDuration` / `GetAnimationDuration` THEN 设置/获取总播放时长（毫秒） | 正常 |
| AC-6.7 | WHEN 调用 `SetAnimationIteration` / `GetAnimationIteration` THEN 设置/获取播放次数 | 正常 |
| AC-6.8 | WHEN 调用 `SetAnimationFrameDurations(durations, size)` THEN 设置逐帧时长数组；参数无效返回 `ARKUI_ERROR_CODE_PARAM_INVALID` | 异常 |
| AC-6.9 | WHEN 调用 `SetAnimationAutoPlay(autoPlay)` THEN 设置是否自动播放；默认值为 1（自动播放） | 正常 |
| AC-6.10 | WHEN 调用 `SetAnimationStopMode(mode)` THEN 设置停止模式（FIRST_FRAME=0 / LAST_FRAME=1） | 正常 |
| AC-6.11 | WHEN 调用 `CreateAnimationController` THEN 为指定 node 创建动画控制器 | 正常 |
| AC-6.12 | WHEN 调用 `StartAnimation` / `StopAnimation` / `PauseAnimation` / `ResumeAnimation` THEN 控制动画播放，无效参数返回 `ARKUI_ERROR_CODE_PARAM_INVALID` | 异常 |
| AC-6.13 | WHEN 调用 `GetAnimationStatus` THEN 返回 `DrawableDescriptor_AnimationStatus` 枚举值 | 正常 |

### US-7: 跨前端 Bridge

作为 NDK 开发者，我想要将 ArkTS 侧已创建的 DrawableDescriptor 映射到 Native 侧的 `ArkUI_DrawableDescriptor`，以便在 Native 层使用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `OH_ArkUI_GetDrawableDescriptorFromNapiValue(env, napi_value, &descriptor)` (NAPI 通道) THEN 从 NAPI 值提取并返回 `ArkUI_DrawableDescriptor*` | 正常 |
| AC-7.2 | WHEN 调用 `OH_ArkUI_GetDrawableDescriptorFromResourceNapiValue(env, napi_value, &descriptor)` (NAPI 通道) THEN 从 NAPI Resource 值解析并返回 `ArkUI_DrawableDescriptor*` | 正常 |
| AC-7.3 | WHEN 调用 `OH_ArkUI_NativeModule_GetDrawableDescriptorFromAniValue(env, ani_object, &descriptor)` (ANI 通道) THEN 从 ANI 对象提取并返回 `ArkUI_DrawableDescriptor*` | 正常 |
| AC-7.4 | WHEN 调用 `OH_ArkUI_NativeModule_GetDrawableDescriptorFromResourceAniValue(env, ani_resource, &descriptor)` (ANI 通道) THEN 从 ANI Resource 对象解析并返回 `ArkUI_DrawableDescriptor*` | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 | R-5 | TASK-SKELETON-1 | C API unittest + XTS | 已有测试覆盖 |
| AC-1.2 | R-6 | TASK-SKELETON-1 | C API unittest | 已有测试覆盖 |
| AC-1.3 | R-7 | TASK-SKELETON-1 | C API unittest | 已有测试覆盖 |
| AC-1.4 | R-23, R-29 | TASK-SKELETON-1 | C API unittest | 已有测试覆盖 |
| AC-1.5 | R-23 | TASK-SKELETON-1 | C API unittest | 已有测试覆盖 |
| AC-1.6 | R-22 | TASK-SKELETON-1 | SpecTest | 已有测试覆盖 |
| AC-2.1 ~ AC-2.8 | R-1, R-8~R-12 | TASK-SKELETON-1 | C API unittest + XTS | 已有测试覆盖 |
| AC-3.1 ~ AC-3.10 | R-2, R-13~R-19 | TASK-SKELETON-1 | C API unittest + XTS | 已有测试覆盖 |
| AC-4.1 ~ AC-4.2 | R-20 | TASK-SKELETON-1 | C API unittest | 已有测试覆盖 |
| AC-5.1 ~ AC-5.3 | R-21 | TASK-SKELETON-1 | C API unittest | 已有测试覆盖 |
| AC-6.1 ~ AC-6.13 | R-3 | TASK-SKELETON-1 | C API unittest (capi_all_modifiers_test) | 已有测试覆盖 |
| AC-7.1 ~ AC-7.4 | R-4 | TASK-SKELETON-1 | XTS | 已有测试覆盖 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | DrawableDescriptor 类型层级 DrawableDescriptor (BASE) ├── LayeredDrawableDescriptor (LAYERED) ├── AnimatedDrawableDescriptor (ANIMATED) ├── PixelMapDrawableDescriptor (PIXELMAP) └── PictureDrawableDescriptor (PICTURE) 每个子类型必须通过 `getDrawableType()` 返回正确的 `DrawableType` 枚举值。类型一旦创建不可更改。 | — | — |
| R-2 | 行为 | — | 动画生命周期 动画状态机: `INITIAL → RUNNING ⇄ PAUSED → STOPPED`。STOPPED 后根据 `AnimationStopMode` 回到 FIRST_FRAME 或停留在 LAST_FRAME。`start()` 从 INITIAL/STOPPED 进入 RUNNING；`pause()` 从 RUNNING 进入 PAUSED（保持当前帧）；`resume()` 从 PAUSED 回到 RUNNING。 | — | — |
| R-3 | 行为 | — | C API 错误码约定 所有返回 `int32_t` 的 C API 函数使用统一错误码：`ARKUI_ERROR_CODE_NO_ERROR` (0) 表示成功，`ARKUI_ERROR_CODE_PARAM_INVALID` 表示参数无效（如 null 指针、越界值）。 | — | — |
| R-4 | 行为 | — | DrawableDescriptor 跨前端传递方向 Bridge API 方向仅为 ArkTS→Native。Native 侧不可创建新的 DrawableDescriptor 子类型（仅可通过 C API 从 PixelMap 创建基础包装）。Native 侧获取到的 `ArkUI_DrawableDescriptor*` 生命周期由调用方管理。 | — | — |
| R-5 | 行为 | — | getPixelMap() — 基础类 `DrawableDescriptor::getPixelMap()` 返回缓存的 PixelMap（如有），否则从内部 buffer 解码创建 PixelMap（通过 `Media::ImageSource::CreatePixelMap`，格式 BGRA_8888），并缓存结果。返回 `nullptr` 表示失败。 | — | — |
| R-6 | 行为 | — | loadSync() 同步加载图像并返回 `DrawableDescriptorLoadedResult{imageWidth_, imageHeight_, errorCode}`。`AnimatedDrawableDescriptor` 从 `ImageSource` 创建帧参数并构建 `ControlledAnimator`。 | — | — |
| R-7 | 行为 | — | load() — 异步加载 通过 `LoadCallback` 异步回调返回加载结果。实现层在加载完成后调用 `callback(loadResult)`。 | — | — |
| R-8 | 行为 | — | LayeredDrawableDescriptor::getForeground() 返回前景层 `DrawableDescriptor`。优先返回已设置的 `foreground_`，否则通过 `GetPixelMapFromJsonBuf(false)` 从 JSON buffer 解码前景数据。 | — | — |
| R-9 | 行为 | — | LayeredDrawableDescriptor::getBackground() 同 getForeground() 逻辑，处理背景层。 | — | — |
| R-10 | 行为 | — | LayeredDrawableDescriptor::getMask() 遮罩获取优先级：已设置的 `mask_` > `GetMaskByPath()` (文件路径) > `GetDefaultMask()` (资源名 `ohos_icon_mask`)。 | — | — |
| R-11 | 行为 | — | setBlendMode(mode) 设置合成混合模式。mode 取值必须在 `BlendMode::CLEAR` ~ `BlendMode::LUMINOSITY` 范围内。设置 blendMode ≥ 0 时自动将 `foregroundOverBackground_` 设为 `true`。 | — | — |
| R-12 | 行为 | — | LayeredDrawableDescriptor::getPixelMap() — 合成逻辑 合成分为两条路径： - **非自适应路径**：foreground 尺寸 = 288x288，固定输出 192x192 - **自适应路径**：foreground 尺寸 ≠ 288x288，按背景比例缩放合成 合成顺序：background(SRC) → foregroundOverBackground? 前景 blend → mask(DST_IN) → !foregroundOverBackground? 前景(SRC_ATOP) | — | — |
| R-13 | 行为 | — | AnimatedDrawableDescriptor 构造 支持两种构造方式： - `constructor(pixelMaps, options?)`: 直接传入 PixelMap 数组 - `constructor(src, options?)`: 从 ResourceStr 或 PixelMap 数组加载，通过 `DrawableDescriptorInfo` 解析 src 类型（RESOURCE/BASE64/FILE） | — | — |
| R-14 | 行为 | — | AnimationOptions `AnimationOptions` 包含：`duration`（单次播放时长 ms）、`iterations`（播放次数，默认 1）、`frameDurations`（逐帧时长数组 ms）、`autoPlay`（默认 true）、`stopMode`（默认 FIRST_FRAME）。 | — | — |
| R-15 | 行为 | — | 总时长计算 若设置 `totalDuration_`（≥ 0），直接使用；否则由 `userDurations_`（如设置）或 `selfDurations_`（自动计算）累加得出。 | — | — |
| R-16 | 行为 | — | getAnimationController(id?) 返回与组件 ID 关联的 `AnimationController`。每个 `nodeId` 独立维护 `ControlledAnimator`。Controller 提供 `start/stop/pause/resume/getStatus` 五类操作。 | — | — |
| R-17 | 行为 | — | ControlledAnimator per-node 模型 `animators_` 为 `unordered_map<int32_t, RefPtr<ControlledAnimator>>`，每个 nodeId 对应独立 animator。`RegisterUpdateCallback(nodeId, callback)` 注册帧更新回调，`UnRegisterUpdateCallback(nodeId)` 注销。 | — | — |
| R-18 | 行为 | — | C API 从 PixelMap 创建 `OH_ArkUI_DrawableDescriptor_CreateFromPixelMap` 创建内部为 PixelMap 的 DrawableDescriptor。`CreateFromAnimatedPixelMap` 创建包含 PixelMap 数组的动画描述符。 | — | — |
| R-19 | 行为 | — | C API 动画控制 `CreateAnimationController` 返回 `ArkUI_DrawableDescriptor_AnimationController**`，绑定到指定 `ArkUI_NodeHandle`。所有动画控制函数通过 controller 操作。 | — | — |
| R-20 | 行为 | — | PixelMapDrawableDescriptor 直接包装 `RefPtr<PixelMap>`，`getPixelMap()` 直接返回。支持 raw data 设置用于后续解码。 | — | — |
| R-21 | 行为 | — | PictureDrawableDescriptor 包装 `RefPtr<Picture>`，支持 `setHdrComposition(config)` 设置 HDR 合成区域。`getPixelMap()` 执行合成（如已配置 HDR）。 | — | — |
| R-22 | 行为 | — | invalidate() 触发该 DrawableDescriptor 所绑定组件的重绘。适用于内容更新后需要刷新显示的场景。未绑定到任何组件时调用无效果。 | — | — |
| R-23 | 异常 | — | release() 后访问 调用 `release()` 后，后续任何方法调用（`getPixelMap()`、`loadSync()`、`load()` 等）抛出 `BusinessError 111002`（"The native memory referenced by the drawableDescriptor has been released"）。 | — | — |
| R-24 | 异常 | — | Resource 加载失败 资源加载失败时，`loadSync()` 抛出 `BusinessError 111001`（"resource loading failed"）。`load()` 返回 rejected Promise。 | — | — |
| R-25 | 异常 | — | getForeground/getBackground/getMask 失败 当对应层的数据不可用时（buffer 为空、JSON 解析失败、资源未找到），返回 `nullptr`。不会抛出异常。 | — | — |
| R-26 | 异常 | — | C API null 参数 所有 C API 函数在接收到 null 指针参数时返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | — | — |
| R-27 | 异常 | — | blendMode 非法值 `setBlendMode(mode)` 中 mode 超出 `[CLEAR, LUMINOSITY]` 范围时，调用被忽略，不报错。 | — | — |
| R-28 | 异常 | — | 动画已释放后操作 AnimationController 对应的 DrawableDescriptor 已 release 后，controller 操作行为未定义（上层业务应保证生命周期）。 | — | — |
| R-29 | 恢复 | — | release() 后的状态恢复 一旦调用 `release()`，DrawableDescriptor 进入"已释放"状态，不可逆。`isReleased()` 返回 `true`。要重新使用需创建新的 DrawableDescriptor 实例。 | — | — |
| R-30 | 恢复 | — | 动画 stop 后的恢复 Stop → Start: 动画从首帧（FIRST_FRAME mode）或末帧（LAST_FRAME mode）重新开始播放。 Pause → Resume: 动画从暂停帧继续播放。 | — | — |
| R-31 | 恢复 | — | PixelMap 缓存失效后的自动重建 `getPixelMap()` 在内部 PixelMap 为 null 时自动尝试从原始 buffer 重新解码。对于 AnimatedDrawableDescriptor，`GetPixelMap()` 从当前帧索引获取对应帧。 | — | — |
| R-32 | 恢复 | — | Layered 合成失败回退 `CreatePixelMap()` 中 `GetLayeredIconParm` 返回 false（缺少必需的 foreground/background/mask）时，`getPixelMap()` 返回 nullptr。调用方检查返回值即可。 | — | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | US-1 全 AC | C API unittest + XTS | getPixelMap 正确性、loadSync/load 返回值、release 后异常 |
| VM-2 | US-2 全 AC | C API unittest + XTS | 三层分离获取、合成输出正确性、blendMode 设置 |
| VM-3 | US-3 全 AC | C API unittest + XTS + SpecTest | 帧动画播放、AnimationController 状态机、per-node 独立性 |
| VM-4 | US-4 全 AC | C API unittest | PixelMap 封装正确性、ResourceStr 加载 |
| VM-5 | US-5 全 AC | C API unittest | Picture 封装、HDR 合成 |
| VM-6 | US-6 全 AC | C API unittest (capi_all_modifiers_test) | C API 创建/销毁、动画配置、错误码 |
| VM-7 | US-7 全 AC | XTS | NAPI/ANI bridge 双向映射正确性 |

## API 变更分析

### 新增 API

**TS 动态 API (`@ohos.arkui.drawableDescriptor.d.ts`)：**

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `class DrawableDescriptor` | System | drawable 资源描述符基类，提供 getPixelMap/loadSync/load/release/isReleased/invalidate | AC-1.1~AC-1.6 |
| `class LayeredDrawableDescriptor extends DrawableDescriptor` | System | 分层描述符，提供 getForeground/getBackground/getMask/getMaskClipPath/setBlendMode | AC-2.1~AC-2.8 |
| `class PixelMapDrawableDescriptor extends DrawableDescriptor` | System | PixelMap 直接封装描述符 | AC-4.1~AC-4.2 |
| `class AnimatedDrawableDescriptor extends DrawableDescriptor` | System | 帧动画描述符，提供 getAnimationController | AC-3.1~AC-3.10 |
| `class PictureDrawableDescriptor extends DrawableDescriptor` | System | Picture 类型描述符，提供 setHdrComposition | AC-5.1~AC-5.3 |
| `interface AnimationOptions` | System | 动画配置选项（duration/iterations/frameDurations/autoPlay/stopMode） | AC-3.3~AC-3.6 |
| `interface AnimationController` | System | 动画控制器接口（start/stop/pause/resume/getStatus） | AC-3.7~AC-3.9 |
| `enum AnimationStopMode` | System | 动画停止模式（FIRST_FRAME/LAST_FRAME） | AC-3.6 |
| `interface DrawableDescriptorLoadedResult` | System | 加载结果接口（imageWidth/imageHeight） | AC-1.2~AC-1.3 |
| `interface HdrCompositionConfig` | System | HDR 合成配置 | AC-5.2 |

**TS 静态 API (`@ohos.arkui.drawableDescriptor.static.d.ets`)：** 同动态 API，签名差异详见兼容性声明。

**C API (`interfaces/native/drawable_descriptor.h`)：**

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `OH_ArkUI_DrawableDescriptor_CreateFromPixelMap` | Public | 从 PixelMap 创建描述符 | AC-6.1 |
| `OH_ArkUI_DrawableDescriptor_CreateFromAnimatedPixelMap` | Public | 从 PixelMap 数组创建动画描述符 | AC-6.2 |
| `OH_ArkUI_DrawableDescriptor_Dispose` | Public | 释放描述符 | AC-6.3 |
| `OH_ArkUI_DrawableDescriptor_GetStaticPixelMap` | Public | 获取静态 PixelMap | AC-6.4 |
| `OH_ArkUI_DrawableDescriptor_GetAnimatedPixelMapArray` | Public | 获取动画 PixelMap 数组 | AC-6.5 |
| `OH_ArkUI_DrawableDescriptor_GetAnimatedPixelMapArraySize` | Public | 获取动画 PixelMap 数组大小 | AC-6.5 |
| `OH_ArkUI_DrawableDescriptor_Set/GetAnimationDuration` | Public | 设置/获取总播放时长 | AC-6.6 |
| `OH_ArkUI_DrawableDescriptor_Set/GetAnimationIteration` | Public | 设置/获取播放次数 | AC-6.7 |
| `OH_ArkUI_DrawableDescriptor_Set/GetAnimationFrameDurations` | Public | 设置/获取逐帧时长 | AC-6.8 |
| `OH_ArkUI_DrawableDescriptor_Set/GetAnimationAutoPlay` | Public | 设置/获取自动播放 | AC-6.9 |
| `OH_ArkUI_DrawableDescriptor_Set/GetAnimationStopMode` | Public | 设置/获取停止模式 | AC-6.10 |
| `OH_ArkUI_DrawableDescriptor_CreateAnimationController` | Public | 创建动画控制器 | AC-6.11 |
| `OH_ArkUI_DrawableDescriptor_DisposeAnimationController` | Public | 释放动画控制器 | AC-6.11 |
| `OH_ArkUI_DrawableDescriptor_StartAnimation` | Public | 开始动画 | AC-6.12 |
| `OH_ArkUI_DrawableDescriptor_StopAnimation` | Public | 停止动画 | AC-6.12 |
| `OH_ArkUI_DrawableDescriptor_PauseAnimation` | Public | 暂停动画 | AC-6.12 |
| `OH_ArkUI_DrawableDescriptor_ResumeAnimation` | Public | 恢复动画 | AC-6.12 |
| `OH_ArkUI_DrawableDescriptor_GetAnimationStatus` | Public | 获取动画状态 | AC-6.13 |

**Bridge API：**

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `OH_ArkUI_GetDrawableDescriptorFromNapiValue` (native_node_napi.h) | Public | NAPI 通道：从 napi_value 获取描述符 | AC-7.1 |
| `OH_ArkUI_GetDrawableDescriptorFromResourceNapiValue` (native_node_napi.h) | Public | NAPI 通道：从 Resource napi_value 获取描述符 | AC-7.2 |
| `OH_ArkUI_NativeModule_GetDrawableDescriptorFromAniValue` (native_node_ani.h) | Public | ANI 通道：从 ani_object 获取描述符 | AC-7.3 |
| `OH_ArkUI_NativeModule_GetDrawableDescriptorFromResourceAniValue` (native_node_ani.h) | Public | ANI 通道：从 Resource ani_object 获取描述符 | AC-7.4 |

### 变更/废弃 API

无。本特性为已有实现补录。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否——本特性为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10 (dynamic), API 23 (static)
- **API 版本号策略:** 仅记录最新行为。关键版本节点：
  - API 10: DrawableDescriptor, LayeredDrawableDescriptor 基础能力
  - API 12: PixelMapDrawableDescriptor, AnimatedDrawableDescriptor, C API 基础函数
  - API 21: loadSync/load, AnimationController, frameDurations, autoPlay
  - API 22: C API 动画控制（CreateAnimationController, Start/Stop/Pause/Resume）
  - API 23: Static API 全面支持, setBlendMode, LayeredDrawableDescriptor 构造函数参数
  - API 24: AnimationStopMode 枚举
  - API 26: release/isReleased/invalidate, PictureDrawableDescriptor, HdrCompositionConfig
- **Dynamic vs Static API 差异：**
  - Static API 的 `getPixelMap()` 返回 `image.PixelMap | undefined`（而非裸 `image.PixelMap`）
  - Static API 的 `setBlendMode(mode?)` 参数允许 `undefined`
  - 这些差异属于动态/静态语言特性差异，语义等价

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 新旧双架构共存 | `interfaces/inner_api/` (Napi::DrawableDescriptor) 为旧 NAPI 桥接层，`frameworks/core/drawable/` (Ace::DrawableDescriptor) 为新核心实现。TS 侧通过 `JsDrawableDescriptor` 同时访问两者 | AC-1.*, AC-2.* |
| C API 不支持 DrawableType 查询 | C API 不暴露 `DrawableType` 枚举。Native 侧无法区分 BASE/LAYERED/ANIMATED 等子类型 | AC-6.* |
| C API Bridge 单向传递 | Bridge 仅支持 ArkTS→Native 方向。Native 侧不能通过 C API 创建子类型描述符 | AC-7.* |
| Animation per-node 隔离 | 同一 AnimatedDrawableDescriptor 多组件共享时，每个 nodeId 独立 animator，动画状态不共享 | AC-3.10 |

> 架构规则适用性及设计方案见 [design.md](design.md)。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单帧 PixelMap 解码 < 50ms (192x192 BGRA) | benchmark | N/A（存量补录，已有实现） |
| 内存 | DrawableDescriptor 基础内存 < 1KB（不含 PixelMap 数据） | 代码分析 | `frameworks/core/drawable/drawable_descriptor.h` 仅含 ImageSize (8 bytes) + vtable |
| 安全 | 资源路径不暴露到日志（`HILOGD` 不输出密钥/路径） | 代码审查 | 已有实现遵循此规则 |
| 可靠性 | 资源加载失败时返回 null/errorCode，不崩溃 | C API unittest | 异常规则 R-24, R-26 覆盖 |
| 问题定位 | `HILOGE` 记录所有失败路径 | 代码审查 | 如 `interfaces/inner_api/drawable_descriptor/drawable_descriptor.cpp:286` |

> N/A 判定：本特性为已有实现补录，性能基准、内存压测等需真实设备环境验证，不在补录范围。

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
| 无障碍 | 否 | DrawableDescriptor 是数据对象，不直接涉及无障碍 | N/A |
| 大字体 | 否 | 不涉及文本渲染 | N/A |
| 深色模式 | 否 | 资源选择由资源管理系统决定，DrawableDescriptor 不感知主题 | N/A |
| 多窗口/分屏 | 否 | DrawableDescriptor 不感知窗口状态 | N/A |
| 多用户 | 否 | 不涉及用户数据隔离 | N/A |
| 版本升级 | 是 | API 版本差异见兼容性声明 | Dynamic vs Static API 差异 |
| 生态兼容 | 是 | C API 和 TS API 均须保持 ABI/API 兼容 | C API @since 12 起不兼容变更需走废弃流程 |

## 行为场景（Gherkin）

```gherkin
Feature: DrawableDescriptor 资源加载与 PixelMap 获取
  作为 应用开发者
  我想要 从资源系统加载 drawable 并获取其 PixelMap
  以便 将图像渲染到 Image 组件中

  Scenario: 获取静态图片 PixelMap
    Given 已通过资源管理系统创建一个有效的 DrawableDescriptor
    When 调用 getPixelMap()
    Then 返回非空的 image.PixelMap 对象
    And 再次调用 getPixelMap() 返回缓存的同一 PixelMap

  Scenario: 同步加载图片
    Given 已创建一个 DrawableDescriptor
    When 调用 loadSync()
    Then 返回 DrawableDescriptorLoadedResult { imageWidth > 0, imageHeight > 0 }
    And errorCode 为 0

  Scenario: 异步加载图片
    Given 已创建一个 DrawableDescriptor
    When 调用 load() 并 await
    Then Promise resolve 为 DrawableDescriptorLoadedResult { imageWidth > 0, imageHeight > 0 }

  Scenario: release 后访问抛出异常
    Given 已创建一个 DrawableDescriptor 并调用 release()
    When 调用 getPixelMap()
    Then 抛出 BusinessError 111002

Feature: LayeredDrawableDescriptor 多层图像合成
  作为 应用开发者
  我想要 使用分层描述符合成前景/背景/遮罩
  以便 实现分层图标效果

  Scenario: 获取三层描述符
    Given 已通过资源 JSON 创建 LayeredDrawableDescriptor
    When 依次调用 getForeground(), getBackground(), getMask()
    Then 每层返回有效的 DrawableDescriptor

  Scenario: 合成 PixelMap（自适应路径）
    Given 创建的 LayeredDrawableDescriptor 的 foreground 尺寸为 192x192
    When 调用 getPixelMap()
    Then 返回按自适应缩放合成的 PixelMap

  Scenario: 设置 blendMode 影响合成顺序
    Given 创建的 LayeredDrawableDescriptor
    When 调用 setBlendMode(DST_OVER)
    Then foregroundOverBackground 自动设为 true
    And getPixelMap() 将前景合成到背景之上

Feature: AnimatedDrawableDescriptor 帧动画控制
  作为 应用开发者
  我想要 通过 AnimationController 控制帧动画播放
  以便 实现可控的动画效果

  Scenario: 自动播放动画
    Given 通过 PixelMap 数组创建 AnimatedDrawableDescriptor（autoPlay 默认 true）
    When 描述符绑定到组件后
    Then 动画自动开始播放

  Scenario: 手动控制动画
    Given 创建 AnimatedDrawableDescriptor(autoPlay=false) 并绑定组件
    When 通过 getAnimationController() 获取 controller 并调用 start()
    Then 动画从首帧开始播放
    And getStatus() 返回 RUNNING

  Scenario: 暂停和恢复
    Given 动画正在播放 (status=RUNNING)
    When 调用 controller.pause()
    Then 动画停在当前帧, getStatus() 返回 PAUSED
    When 调用 controller.resume()
    Then 动画从当前帧继续播放, getStatus() 返回 RUNNING

  Scenario: 多组件共享独立动画状态
    Given 同一个 AnimatedDrawableDescriptor 绑定到组件 A 和组件 B
    When 组件 A 的 controller.pause()
    Then 组件 A 的动画暂停, 组件 B 的动画继续播放

Feature: C API DrawableDescriptor
  作为 NDK 开发者
  我想要 通过 C API 创建和配置 DrawableDescriptor
  以便 在 Native 层使用 drawable 资源

  Scenario: 从 PixelMap 创建
    Given 持有一个有效的 OH_PixelmapNativeHandle
    When 调用 OH_ArkUI_DrawableDescriptor_CreateFromPixelMap(pixelMap)
    Then 返回非空 ArkUI_DrawableDescriptor*

  Scenario: 设置动画参数
    Given 通过 CreateFromAnimatedPixelMap 创建 ArkUI_DrawableDescriptor
    When 调用 SetAnimationDuration(1000) 和 SetAnimationIteration(3)
    Then GetAnimationDuration 返回 1000, GetAnimationIteration 返回 3

  Scenario: 动画控制
    Given 已创建 AnimationController
    When 调用 StartAnimation → PauseAnimation → ResumeAnimation → StopAnimation
    Then 各步骤动画状态依次为 RUNNING → PAUSED → RUNNING → STOPPED
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（5个TS类 + C API 20+函数 + Bridge，不涉及内部 Loader/Info 实现细节）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致
- [x] API 签名已与 SDK `.d.ts` / `.static.d.ets` 权威文件交叉核验（`interface/sdk-js/api/@ohos.arkui.drawableDescriptor.d.ts` 及 `.static.d.ets`）
- [x] C API 签名已与 `interfaces/native/drawable_descriptor.h` 交叉核验
- [x] 关键设计发现（新旧双架构、Layered 合成双路径、per-node 动画、内存释放模型、双 Bridge、资源加载三路径）已体现于架构约束和规则中

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/foundation/arkui/ace_engine"
    query: "DrawableDescriptor TS API 与 C API 的双向映射关系和全量 API 列表"
  - repo: "OpenHarmony/foundation/arkui/ace_engine"
    query: "frameworks/core/drawable/ 下新旧架构共存的原因和迁移计划"
```

**关键源文件：**
- SDK Dynamic API: `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.d.ts`
- SDK Static API: `interface/sdk-js/api/@ohos.arkui.drawableDescriptor.static.d.ets`
- C API Header: `interfaces/native/drawable_descriptor.h`
- Bridge NAPI: `interfaces/native/native_node_napi.h`
- Bridge ANI: `interfaces/native/native_node_ani.h`
- NAPI Bridge impl: `interfaces/inner_api/drawable_descriptor/js_drawable_descriptor.h`
- Old inner API: `interfaces/inner_api/drawable_descriptor/drawable_descriptor.h`
- Core base: `frameworks/core/drawable/drawable_descriptor.h`
- Core animated: `frameworks/core/drawable/animated_drawable_descriptor.h`
- Core layered: `frameworks/core/drawable/layered_drawable_descriptor.h`
- Core pixelmap: `frameworks/core/drawable/pixel_map_drawable_descriptor.h`
- Core picture: `frameworks/core/drawable/picture_drawable_descriptor.h`
- Core loader: `frameworks/core/drawable/drawable_descriptor_loader.h`
- Core info: `frameworks/core/drawable/drawable_descriptor_info.h`
