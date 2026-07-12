# 特性规格
## 概述
| 字段 | 内容 |
|------|------|
| 特性名称 | ImageAnimator 帧数据与显示缓存 |
| 特性编号 | Func-05-08-02-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+；PixelMap API 12+；Static API 23+；NDK API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 补录 `ImageFrameInfo` 与 `images` 规格 | 覆盖动态、静态和 NDK frame info。 |
| ADDED | 补录内部 Image 子节点显示规则 | 覆盖 source 更新、fixedSize 布局、自适应尺寸。 |
| ADDED | 补录缓存队列与加载成功切换规则 | 覆盖缓存数量、cache swap、theme/config 更新。 |

## 输入文档
- 设计文档: `arkui-specs/05-ui-components/08-image-components/02-image-animator/design.md`
- 动态 SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/@internal/component/ets/image_animator.d.ts:61`
- 静态 SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/arkui/component/imageAnimator.static.d.ets:36`
- NDK API: `interfaces/native/node_attributes/image_animator.h:84`
- 核心实现: `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.h:67`；`frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:70`
- Model 实现: `frameworks/core/components_ng/pattern/image_animator/image_animator_model_ng.cpp:71`；`frameworks/core/components_ng/pattern/image_animator/image_animator_model_static.cpp:31`
- Static modifier: `frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_static_modifier.cpp:67`
- Native node: `interfaces/native/node/style_modifier.cpp:810`
- 测试参考: `test/unittest/core/pattern/image_animator/image_animator_pattern_test_ng.cpp:198`；`test/unittest/capi/modifiers/image_animator_modifier_test.cpp:96`

## 用户故事
### US-1: 开发者配置帧数据
As a ArkUI 开发者, I want 通过 `images` 配置多帧图片源、尺寸、位置和单帧时长, So that ImageAnimator 可以按帧序列播放并正确解析 string、Resource、PixelMap 和 NDK frame info。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态 ArkTS 调用 `images(value: Array<ImageFrameInfo>)`, THEN `value` 中每帧应按 SDK 声明包含 `src`、可选 `width/height/top/left/duration`，并返回 `ImageAnimatorAttribute`。 | 正常 |
| AC-1.2 | WHEN 动态 API 版本为 7-8、9-11、12+ 时, THEN `src` 类型分别按 string、string/Resource、string/Resource/PixelMap 的 SDK 版本边界解释。 | 边界 |
| AC-1.3 | WHEN 静态 ArkTS API 23+ 调用 `images(value: Array<ImageFrameInfo> | undefined)`, THEN undefined 走默认空数组，非 undefined 转换为 `ImageProperties`。 | 正常 |
| AC-1.4 | WHEN NDK 调用 `OH_ArkUI_ImageAnimatorFrameInfo_CreateFromString(nullptr)` 或 `CreateFromDrawableDescriptor(nullptr)`, THEN 返回 null；WHEN 对 null frame info 调 getter, THEN 返回 0。 | 异常 |
| AC-1.5 | WHEN 任一帧 duration 小于 0, THEN Pattern 在保存帧列表时将该帧 duration 归零，不计入逐帧总时长。 | 边界 |
| AC-1.6 | WHEN `images` 为空或 length 小于等于 0, THEN Pattern 无可播放帧，`OnModifyDone` 在 size <= 0 时返回，不生成缓存或启动播放。 | 边界 |

### US-2: 组件显示当前帧并应用尺寸规则
As a ArkUI 渲染框架, I want ImageAnimator 使用内部 Image 节点显示当前帧, So that 复用 Image 的加载、资源解析和布局能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN ModelNG 设置非空 `images`, THEN 如果 ImageAnimator 无子节点，应创建内部 Image FrameNode，并将 ImagePattern 标记为 ImageAnimator 场景。 | 正常 |
| AC-2.2 | WHEN `fixedSize=true`, THEN 当前帧 Image 清空 margin 和用户自定义尺寸，measure type 为 MATCH_PARENT，并忽略帧 width/height/top/left。 | 正常 |
| AC-2.3 | WHEN `fixedSize=false`, THEN 当前帧 Image 使用帧 left/top 作为 margin，使用 width/height 作为用户尺寸，measure type 为 MATCH_CONTENT。 | 正常 |
| AC-2.4 | WHEN 组件自身没有显式 self ideal size 且帧 width/height 存在非百分比值, THEN ImageAnimator 以所有帧中最大非百分比 width/height 作为自身用户尺寸。 | 正常 |
| AC-2.5 | WHEN 当前帧 src 是 PixelMap, THEN Pattern 使用 PixelMap 构造 `ImageSourceInfo`; WHEN 当前帧 src 是 string/resource, THEN 使用 src、bundleName、moduleName 构造 `ImageSourceInfo` 并更新本地颜色模式。 | 正常 |

### US-3: 组件预加载并切换缓存帧
As a ArkUI 运行时, I want ImageAnimator 根据帧显示时间维护有限缓存, So that 播放时减少等待且控制内存占用。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `images.size() > 0`, THEN `GenerateCachedImages` 根据平均帧显示时间生成 1 或 2 个缓存 Image，且缓存数量不超过 `images.size() - 1`。 | 正常 |
| AC-3.2 | WHEN 平均帧显示时间大于等于 50ms, THEN 缓存 1 帧；WHEN 小于 50ms, THEN 缓存 2 帧。 | 边界 |
| AC-3.3 | WHEN 目标帧对应缓存 Image 已加载, THEN `SetShowingIndex` 用缓存节点替换当前显示节点，并把旧显示节点放回缓存队列。 | 正常 |
| AC-3.4 | WHEN 缓存 Image 加载完成且 loadingStatus 等于 1, THEN 缓存项标记为 loaded；其他 loadingStatus 不改变缓存状态。 | 边界 |
| AC-3.5 | WHEN theme scope 或颜色配置更新, THEN 缓存 Image 触发对应 ImagePattern 更新并将缓存 loaded 状态置 false。 | 恢复 |

## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1, R-2 | TASK-05-08-02-01 | SDK 审查 + static modifier UT | `/interface/sdk-js/api/@internal/component/ets/image_animator.d.ts:181`; `test/unittest/capi/modifiers/image_animator_modifier_test.cpp:110` |
| AC-1.2 | R-3 | TASK-05-08-02-01 | SDK 审查 | `/interface/sdk-js/api/@internal/component/ets/image_animator.d.ts:63` |
| AC-1.3 | R-4 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_static_modifier.cpp:120` |
| AC-1.4 | R-5 | TASK-05-08-02-01 | NDK 源码审查 | `interfaces/native/node/frame_information.cpp:23` |
| AC-1.5 | R-6 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.h:75` |
| AC-1.6 | R-7 | TASK-05-08-02-01 | 源码审查 + Pattern UT | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:332`; `test/unittest/core/pattern/image_animator/image_animator_pattern_test_ng.cpp:198` |
| AC-2.1 | R-8 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_model_ng.cpp:26` |
| AC-2.2 | R-9 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:148` |
| AC-2.3 | R-10 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:136` |
| AC-2.4 | R-11 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:526` |
| AC-2.5 | R-12 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:125` |
| AC-3.1 | R-13 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:235` |
| AC-3.2 | R-14 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:238` |
| AC-3.3 | R-15 | TASK-05-08-02-01 | Pattern UT | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:98`; `test/unittest/core/pattern/image_animator/image_animator_pattern_test_ng.cpp:225` |
| AC-3.4 | R-16 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:582` |
| AC-3.5 | R-17 | TASK-05-08-02-01 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:735` |

## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用动态 `images(value)` | SDK 返回 `ImageAnimatorAttribute`，帧信息包含路径、尺寸、位置、duration。 | SDK 声明动态更新不支持。 | AC-1.1 |
| R-2 | 行为 | static modifier `SetImagesImpl` 收到有效 `Opt_Array_ImageFrameInfo` | 转换为 `std::vector<ImageProperties>` 并调用 `ImageAnimatorModelNG::SetImages`。 | value 不可转换时设置空数组。 | AC-1.1, AC-1.3 |
| R-3 | 边界 | `src` 在不同 API 版本下声明 | API 7-8 仅 string；API 9-11 string/Resource；API 12+ string/Resource/PixelMap。 | 静态 API 23+ 直接声明 string/Resource/PixelMap。 | AC-1.2 |
| R-4 | 行为 | 静态 `images(undefined)` 或 converter 返回空 optional | Model 设置空 `std::vector<ImageProperties>`。 | 空数组不会创建可播放帧。 | AC-1.3, AC-1.6 |
| R-5 | 异常 | NDK frame info create 入参为 null 或 getter 入参为 null | create 返回 null；getter 返回 0；setter/Dispose 对 null 无动作。 | 调用方仍负责 dispose 非 null 对象。 | AC-1.4 |
| R-6 | 边界 | 帧 duration 小于 0 | `SetImages` 将该 duration 改为 0。 | 只有 src 或 PixelMap 存在且 duration > 0 的帧进入 `durationTotal_`。 | AC-1.5 |
| R-7 | 边界 | `images_.size() <= 0` | `OnModifyDone` 返回，不生成缓存，不运行 animator。 | 日志不改变可观测 UI。 | AC-1.6 |
| R-8 | 行为 | ModelNG 设置非空帧数组且 host 无子节点 | 创建 Image FrameNode，设置 `ImagePattern::SetImageAnimator(true)`，子 Image MATCH_PARENT，host alignment TOP_LEFT。 | 普通 `Create()` 本身不立即创建子 Image。 | AC-2.1 |
| R-9 | 行为 | `fixedSize=true` 切换当前帧 | 清零 margin、清理用户尺寸、设置 MATCH_PARENT，并控制 animated image 播放。 | SDK 规定 frame width/height/top/left 无效。 | AC-2.2 |
| R-10 | 行为 | `fixedSize=false` 切换当前帧 | 将 left/top 写入 margin，将 width/height 写入 user defined ideal size，设置 MATCH_CONTENT。 | 帧尺寸不匹配组件尺寸时不拉伸。 | AC-2.3 |
| R-11 | 行为 | host 无显式 self ideal size | 遍历帧列表，取非百分比 width/height 最大值更新自身用户尺寸。 | 百分比维度不参与最大值计算。 | AC-2.4 |
| R-12 | 行为 | 更新当前帧 source | PixelMap 路径用 PixelMap 构造 `ImageSourceInfo`；string/resource 路径用 src、bundleName、moduleName 并更新 local color mode。 | cache path 使用相同 source 比较逻辑。 | AC-2.5 |
| R-13 | 行为 | 生成缓存 | 创建 1 或 2 个内部 Image 缓存节点，并注册加载成功事件。 | `cacheImageNum <= images.size() - 1`。 | AC-3.1 |
| R-14 | 边界 | 平均帧显示时间与 50ms 比较 | `>= 50ms` 缓存 1 帧，`< 50ms` 缓存 2 帧。 | 平均值来自当前 animator duration 除以帧数。 | AC-3.2 |
| R-15 | 行为 | 目标帧缓存存在且 `isLoaded=true` | 用缓存节点替换当前显示节点，重建 render context tree，将旧节点作为 loaded 缓存项入队。 | 缓存未加载时直接更新当前 Image 并等待。 | AC-3.3 |
| R-16 | 边界 | 内部 Image onComplete 回调 | 仅 loadingStatus 等于 1 时标记缓存 loaded 并可能触发当前帧刷新。 | 其他状态直接返回。 | AC-3.4 |
| R-17 | 恢复 | Theme scope 或颜色配置更新 | 缓存 Image 调用 ImagePattern 更新并将 `isLoaded=false`，当前显示 Image 同步更新。 | 防止复用旧主题/旧颜色模式缓存。 | AC-3.5 |

## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, AC-1.3 | SDK + static modifier 源码审查 | API 声明、版本边界、converter 行为。 |
| VM-2 | AC-1.4 | NDK frame info 源码审查 | null create/getter/setter/dispose 行为。 |
| VM-3 | AC-1.5, AC-1.6 | Pattern 源码审查 | duration 归零、空帧早返回。 |
| VM-4 | AC-2.1 至 AC-2.5 | Pattern/Model 源码审查 + Pattern UT | 子 Image 创建、source 更新、fixedSize 布局、自适应尺寸。 |
| VM-5 | AC-3.1 至 AC-3.5 | Pattern 源码审查 + Pattern UT | 缓存数量、缓存替换、load success、theme/config 恢复。 |

## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|--------|
| `ImageFrameInfo` | Public | `src`, `width?`, `height?`, `top?`, `left?`, `duration?` | N/A | N/A | 描述 ImageAnimator 单帧图片源、尺寸、位置和时长。 | AC-1.1, AC-1.2 |
| `ImageAnimatorAttribute.images` | Public | 动态 `Array<ImageFrameInfo>`；静态 `Array<ImageFrameInfo> | undefined` | `ImageAnimatorAttribute` / `this` | N/A | 设置帧数组；SDK 声明动态更新不支持。 | AC-1.1, AC-1.3 |
| `OH_ArkUI_ImageAnimatorFrameInfo_*` | Public NDK | char* src、drawable descriptor、width/height/top/left/duration | frame info 指针或 int32 getter | N/A | 创建和维护 native frame info 对象。 | AC-1.4 |
| `NODE_IMAGE_ANIMATOR_IMAGES` | Public NDK | `ArkUI_AttributeItem.object` 为 `ArkUI_ImageAnimatorFrameInfo**`，`size` 为帧数 | `ArkUI_ErrorCode` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | 设置 native ImageAnimator 帧数组。 | AC-1.4, AC-2.1 |

### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|--------|
| N/A | N/A | 本 Feat 补录已有 API，不新增或废弃 API。 | N/A | N/A |

## 接口规格
### 接口定义
**ImageAnimatorAttribute.images**

| 属性 | 值 |
|------|-----|
| 函数签名 | `images(value: Array<ImageFrameInfo>): ImageAnimatorAttribute`；static `images(value: Array<ImageFrameInfo> | undefined): this` |
| 返回值 | `ImageAnimatorAttribute` / `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | `Array<ImageFrameInfo>` / `Array<ImageFrameInfo> | undefined` | 动态是；静态否 | `[]` | SDK 声明动态更新不支持；静态 undefined 转为空数组。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入非空 frame array | Model 初始化内部 Image 子节点并保存帧列表。 | AC-2.1 |
| 2 | 传入空数组或 static undefined | Pattern 无可播放帧，后续 OnModifyDone 返回。 | AC-1.6 |
| 3 | 帧中包含负 duration | 保存前归零，且不计入逐帧总时长。 | AC-1.5 |

**ImageFrameInfo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `interface ImageFrameInfo { src: string | Resource | PixelMap; width?: number | string; height?: number | string; top?: number | string; left?: number | string; duration?: number; }` |
| 返回值 | N/A |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `src` | `string | Resource | PixelMap` | 是 | 无 | 动态 API 7-8 string，9-11 string/Resource，12+ string/Resource/PixelMap；静态 API 23+ string/Resource/PixelMap。 |
| `width/height/top/left` | `number | string` | 否 | `0vp` | fixedSize=false 时参与子 Image 布局；fixedSize=true 时无效。 |
| `duration` | `number` / static `int` | 否 | `0` | 负数由 Pattern 归零；正数参与逐帧总时长。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `src` 是 PixelMap | Pattern 使用 PixelMap `ImageSourceInfo`。 | AC-2.5 |
| 2 | `src` 是 Resource | Converter/bridge 保存 src、bundleName、moduleName。 | AC-2.5 |
| 3 | 所有帧 duration 都为 0 | 全局 duration 等分到每帧。 | AC-1.5 |

**OH_ArkUI_ImageAnimatorFrameInfo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_ImageAnimatorFrameInfo_CreateFromString`, `CreateFromDrawableDescriptor`, `Dispose`, `Set/GetWidth`, `Set/GetHeight`, `Set/GetTop`, `Set/GetLeft`, `Set/GetDuration` |
| 返回值 | frame info 指针或 `int32_t` getter |
| 开放范围 | Public NDK |
| 错误码 | N/A |
| 关联 AC | AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `src` | `char*` | 是 | 无 | null 时 create 返回 null。 |
| `drawable` | `ArkUI_DrawableDescriptor*` | 是 | 无 | null 时 create 返回 null。 |
| `imageInfo` | `ArkUI_ImageAnimatorFrameInfo*` | 是 | 无 | setter/dispose null 无动作；getter null 返回 0。 |
| `width/height/top/left` | `int32_t` | 是 | 0 | 单位 px，未设置 getter 返回 0。 |
| `duration` | `int32_t` | 是 | 0 | 单位 ms，未设置 getter 返回 0。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `CreateFromString` src 非 null | 返回 frame info，src 保存调用方传入字符串。 | AC-1.4 |
| 2 | getter 入参 null | 返回 0。 | AC-1.4 |
| 3 | `NODE_IMAGE_ANIMATOR_IMAGES` 接收 frame info 数组 | native style modifier 解析 drawable/src、尺寸和 duration 后转发到 modifier。 | AC-2.1 |

## 兼容性声明
- **已有 API 行为变更:** 否。本 Feat 补录已有行为；SDK 声明 `images` 动态更新不支持，源码存在替换帧数组实现，不作为新承诺。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7；NDK API 12；Static API 23。
- **API 版本号策略:** 以 SDK `@since` 和 NDK header `@since` 为准；`src` 类型扩展按 API 7/9/12/23 边界记录。

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 内部 Image 节点 | ImageAnimator 自身不直接绘制图片，必须通过内部 Image 子节点承接 source 和布局。 | AC-2.1, AC-2.5 |
| 缓存数量受 duration 和帧数约束 | 缓存数量只由平均帧显示时间和帧数决定，不由 `preDecode` 决定。 | AC-3.1, AC-3.2 |
| SDK 版本为契约 | `src` 支持类型以 SDK 声明为准，源码转换行为只补充实现细节。 | AC-1.2 |
| Native frame info 生命周期 | NDK create/dispose 由调用方管理，组件只消费 frame info 指针数组。 | AC-1.4 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 平均帧显示时间小于 50ms 时缓存 2 帧，否则缓存 1 帧。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:238` |
| 功耗 | 无新增功耗策略；缓存数量受限于最多 2 帧且不超过帧数减 1。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:239` |
| 内存 | SDK 提示大数组会增加内存；实现仅缓存有限 Image 节点。 | SDK + 源码审查 | `/interface/sdk-js/api/@internal/component/ets/image_animator.d.ts:181`; `image_animator_pattern.cpp:235` |
| 安全 | NDK null 入参返回 null/0 或错误码，不解引用 null。 | NDK 源码审查 | `interfaces/native/node/frame_information.cpp:23` |
| 可靠性 | theme/config 更新时缓存标记未加载，避免复用旧缓存。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:735` |
| 可测试性 | 已有 Pattern UT 和 CAPI modifier UT 覆盖核心路径。 | 单测审查 | `test/unittest/core/pattern/image_animator/image_animator_pattern_test_ng.cpp:198` |
| 自动化维测 | inspector 输出包含 images、duration、state 等属性。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:478` |
| 定界定位 | source、cache、duration 和 layout 更新均有集中入口。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:70` |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 按通用 ArkUI ImageAnimator 行为执行。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:332` |
| 平板 | 无差异 | 按通用 ArkUI ImageAnimator 行为执行。 | 源码审查 | 同上 |
| 折叠屏 | 无差异 | 尺寸变化后由布局和 Image source 更新链路重新计算。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:526` |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | ImageAnimator native node 和 accessibility role 存在，但本 Feat 不新增无障碍语义。 | `frameworks/core/interfaces/native/generated/interface/arkoala_api_generated.h:3851` |
| 大字体 | 否 | 本 Feat 不涉及文本。 | N/A |
| 深色模式 | 是 | string/resource source 更新时同步 local color mode，颜色配置更新会刷新缓存 Image。 | AC-2.5, AC-3.5 |
| 多窗口/分屏 | 是 | 通过布局约束和 visible area 机制间接受影响，本 Feat 只覆盖帧尺寸和缓存。 | AC-2.4 |
| 多用户 | 否 | 不涉及用户数据隔离。 | N/A |
| 版本升级 | 是 | `src` 类型和 static API 版本边界需保留兼容说明。 | AC-1.2 |
| 生态兼容 | 是 | SDK 声明 dynamic update 不支持，不能在规格中承诺动态帧更新。 | AC-1.1 |

## 行为场景（可选，Gherkin）
Feature: ImageAnimator frame data and cache
  作为 ArkUI 开发者
  我想要设置图片帧数组并由组件缓存后续帧
  以便 图片动画按当前实现稳定播放

  Scenario: fixedSize true ignores frame position and size
    Given ImageAnimator has one frame with width, height, top and left
    When fixedSize is true and the frame is displayed
    Then the internal Image uses MATCH_PARENT
    And frame margin and user defined size are cleared

  Scenario: cache count follows average frame time
    Given ImageAnimator has multiple frames
    When average frame time is below 50ms
    Then two cache Image nodes are prepared unless the frame count allows fewer

## Spec 自审清单
- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references
```yaml
context-queries:
  - repo: "OpenHarmony/foundation_arkui_ace_engine"
    query: "ImageAnimator ImageFrameInfo images cache fixedSize current implementation"
```

**关键文档:** `docs/pattern/image_animator/Image_Animator_Knowledge_Base.md`
