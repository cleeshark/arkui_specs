# 特性规格
## 概述
| 字段 | 内容 |
|------|------|
| 特性名称 | ImageAnimator 播放控制与可见性联动 |
| 特性编号 | Func-05-08-02-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+；`monitorInvisibleArea` Dynamic API 17+；Static API 23+；NDK API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 补录播放状态和动画参数规格 | 覆盖 `state`、`duration`、`reverse`、`fillMode`、`iterations`。 |
| ADDED | 补录 `monitorInvisibleArea` 可见性联动 | 覆盖 visible area callback 注册、暂停/恢复、native setter 差异。 |
| ADDED | 补录 `preDecode` 和 form render 特殊行为 | `preDecode` 为 deprecated 且无实现；form 下 duration/iteration 受限。 |

## 输入文档
- 设计文档: `arkui-specs/05-ui-components/08-image-components/02-image-animator/design.md`
- 动态 SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/@internal/component/ets/image_animator.d.ts:199`
- 静态 SDK: `/srv/workspace/openharmony_master_default_20260709175431_huawei_a631ac547/code/interface/sdk-js/api/arkui/component/imageAnimator.static.d.ets:134`
- NDK API: `interfaces/native/node_attributes/image_animator.h:47`；`interfaces/native/native_node.h:9232`
- 核心实现: `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:275`；`frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:647`
- 动态 bridge: `frameworks/core/components_ng/pattern/image_animator/bridge/arkts_native_image_animator_bridge.cpp:148`
- 动态 modifier: `frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_dynamic_modifier.cpp:71`
- 静态 modifier: `frameworks/core/components_ng/pattern/image_animator/bridge/image_animator_static_modifier.cpp:131`
- Native node: `interfaces/native/node/style_modifier.cpp:19219`
- 测试参考: `test/unittest/capi/modifiers/image_animator_modifier_test.cpp:226`；`test/unittest/interfaces/native_node_test.cpp:6766`

## 用户故事
### US-1: 开发者控制动画播放状态
As a ArkUI 开发者, I want 设置 ImageAnimator 的播放状态、方向和结束填充模式, So that 帧动画可以按 Initial/Running/Paused/Stopped 与正反向播放语义运行。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `state(AnimationStatus.Initial)`, THEN Pattern 调用 cancel 路径、重置 form 标志、显示指定索引并设置 running index。 | 正常 |
| AC-1.2 | WHEN 设置 `state(AnimationStatus.Paused)`, THEN Pattern 调用 pause 路径并在需要时显示暂停索引。 | 正常 |
| AC-1.3 | WHEN 设置 `state(AnimationStatus.Stopped)`, THEN Pattern 调用 finish 路径并在需要时显示停止索引。 | 正常 |
| AC-1.4 | WHEN 状态为 Running 且 `reverse=false`, THEN animator 调用 Forward；WHEN `reverse=true`, THEN animator 调用 Backward。 | 正常 |
| AC-1.5 | WHEN 动态 ArkTS state 越界或非 number, THEN bridge/modifier 将 state 降级或 reset 为 Initial；WHEN native node state 越界, THEN setter 返回参数错误。 | 异常 |

### US-2: 开发者配置播放时长和循环次数
As a ArkUI 开发者, I want 配置 duration、逐帧 duration 和 iterations, So that 动画时长和重复次数符合 SDK 与实现的边界规则。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 任一有效帧存在正 duration, THEN 全局 `duration(value)` 不生效，animator duration 使用逐帧 duration 总和。 | 边界 |
| AC-2.2 | WHEN 所有帧 duration 均为 0, THEN animator 使用全局 duration，默认值为 1000ms。 | 正常 |
| AC-2.3 | WHEN dynamic duration 小于 0, THEN bridge/modifier 使用默认 1000ms；WHEN static duration 小于 0, THEN validator 使 optional 失效并走默认值。 | 异常 |
| AC-2.4 | WHEN animator 正在 Running 或 Paused 且 duration 改变, THEN 新 duration 在下一次 repeat 内部监听时生效。 | 边界 |
| AC-2.5 | WHEN iterations 为 -1, THEN 表示无限循环；WHEN iterations 小于 -1, THEN 降级为默认 1；WHEN是浮点动态输入, THEN bridge 以 Int32Value 取整。 | 边界 |

### US-3: 组件随可见性和 form 场景调整播放
As a ArkUI 运行时, I want ImageAnimator 在不可见时可自动暂停并在 form 中限制播放, So that 不可见或卡片场景下减少无效播放。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `monitorInvisibleArea=true` 且组件不可见, THEN 如果用户 state 仍为 Running，内部 animator 暂停。 | 正常 |
| AC-3.2 | WHEN `monitorInvisibleArea=true` 且组件重新可见, THEN 如果用户 state 仍为 Running 且 animator 当前不是 Running，按 `reverse` 恢复 Forward 或 Backward。 | 正常 |
| AC-3.3 | WHEN `monitorInvisibleArea=false`, THEN visible area callback 仍更新内部 visible 标志，但不调用暂停/恢复逻辑。 | 正常 |
| AC-3.4 | WHEN 通过 native `NODE_IMAGE_ANIMATOR_IMAGES` 设置帧数组, THEN native style modifier 在设置 images 后额外开启 auto monitor invisible area。 | 边界 |
| AC-3.5 | WHEN 在 form render 场景, THEN duration 被限制为不超过 1000ms，iterations 被强制为 1，剩余时间小于等于 0 时结束播放。 | 边界 |
| AC-3.6 | WHEN 调用 `preDecode(value)`, THEN 当前 NG Pattern 不产生可观测行为。 | 正常 |

## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:275` |
| AC-1.2 | R-2 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:284` |
| AC-1.3 | R-3 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:289` |
| AC-1.4 | R-4 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:303` |
| AC-1.5 | R-5, R-6 | TASK-05-08-02-02 | bridge/native 源码审查 + native UT | `arkts_native_image_animator_bridge.cpp:148`; `interfaces/native/node/style_modifier.cpp:19219`; `test/unittest/interfaces/native_node_test.cpp:6766` |
| AC-2.1 | R-7 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:49` |
| AC-2.2 | R-8 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:35` |
| AC-2.3 | R-9 | TASK-05-08-02-02 | bridge/static 源码审查 | `arkts_native_image_animator_bridge.cpp:186`; `image_animator_static_modifier.cpp:138` |
| AC-2.4 | R-10 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:688` |
| AC-2.5 | R-11 | TASK-05-08-02-02 | 源码审查 + CAPI modifier UT | `image_animator_dynamic_modifier.cpp:214`; `test/unittest/capi/modifiers/image_animator_modifier_test.cpp:249` |
| AC-3.1 | R-12 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.h:108` |
| AC-3.2 | R-13 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.h:115` |
| AC-3.3 | R-14 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:393` |
| AC-3.4 | R-15 | TASK-05-08-02-02 | Native node 源码审查 | `interfaces/native/node/style_modifier.cpp:19183` |
| AC-3.5 | R-16 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:647` |
| AC-3.6 | R-17 | TASK-05-08-02-02 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.h:96` |

## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | Pattern `status_ == IDLE` | animator cancel，重置 form 标志，显示 index，设置 running index。 | Initial 对应内部 IDLE。 | AC-1.1 |
| R-2 | 行为 | Pattern `status_ == PAUSED` | animator pause，重置 form 标志，在 `showingIndexByStoppedOrPaused_` 为 true 时显示 index。 | 不主动改变用户保存的 `status_`。 | AC-1.2 |
| R-3 | 行为 | Pattern `status_ == STOPPED` | animator finish，重置 form 标志，在需要时显示 index。 | `onFinish` 由 stop listener 触发，详见 Feat-03。 | AC-1.3 |
| R-4 | 行为 | Running 路径且未因可见性或 form 结束返回 | `reverse=true` 调 Backward，否则调 Forward。 | 起始索引在 OnModifyDone 中按 reverse 调整。 | AC-1.4 |
| R-5 | 异常 | 动态 state 非 number 或越界 | 非 number reset；越界降级 Initial。 | 合法值为 0 至 3。 | AC-1.5 |
| R-6 | 异常 | native node state size 为 0 或值不在 0 至 3 | 返回 `ERROR_CODE_PARAM_INVALID`。 | 与动态降级策略不同。 | AC-1.5 |
| R-7 | 边界 | `durationTotal_ > 0` | PictureInfo 只为 duration 非 0 的帧生成权重，animator duration 设置为 `durationTotal_`。 | 负逐帧 duration 已在 SetImages 阶段归零。 | AC-2.1 |
| R-8 | 行为 | `durationTotal_ == 0` | 每帧等分 `NORMALIZED_DURATION_MAX`，animator duration 使用全局 duration。 | Pattern 构造默认 duration 1000ms。 | AC-2.2 |
| R-9 | 异常 | duration 输入小于 0 | 动态 bridge/modifier 降级 1000；静态 validator 非负校验后交给默认值。 | native node style setter 对 size 校验，负值由 modifier 降级。 | AC-2.3 |
| R-10 | 边界 | animator 当前 Running 或 Paused 且 duration 变化 | 移除旧 inner repeat listener，新增 listener 在下一次 repeat 设置 finalDuration。 | IDLE/STOPPED 时立即设置。 | AC-2.4 |
| R-11 | 边界 | iterations 输入 | `-1` 保留为无限循环；`< -1` 降级 1；reset 为 1。 | form render 下 Pattern 强制为 1。 | AC-2.5 |
| R-12 | 行为 | `monitorInvisibleArea=true` 且 visible=false | 如果用户 state 为 Running，则内部 animator Pause。 | 只暂停内部 animator，不修改 `status_`。 | AC-3.1 |
| R-13 | 行为 | `monitorInvisibleArea=true` 且 visible=true | 如果用户 state 为 Running 且内部 animator 不在 Running，则按 reverse 恢复。 | reverse=true 调 Backward。 | AC-3.2 |
| R-14 | 行为 | visible area callback 触发 | 始终更新 `visible_`；仅 `isAutoMonitorInvisibleArea_` 为 true 时调用 pause/resume。 | 注册 ratio list 为 `{0.0}`。 | AC-3.3 |
| R-15 | 边界 | native `NODE_IMAGE_ANIMATOR_IMAGES` 设置成功 | 调用 `setImageAnimatorSrc` 后额外调用 `setAutoMonitorInvisibleArea(..., true)`。 | 与 ArkTS 默认 false 不同。 | AC-3.4 |
| R-16 | 边界 | form render 场景 | duration 被限制到不超过 1000ms，iteration 强制 1，剩余时间耗尽后不再继续运行。 | `IsFormRender()` 来源于 PipelineBase 当前上下文。 | AC-3.5 |
| R-17 | 行为 | 调用 `preDecode(value)` | NG Pattern `SetPreDecode` 为空实现，无缓存数量或播放行为变化。 | SDK 标注 deprecated since 9。 | AC-3.6 |

## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1 至 AC-1.5 | Pattern、bridge、native node 源码审查 | 状态机分支、合法值和异常处理。 |
| VM-2 | AC-2.1 至 AC-2.5 | Pattern、modifier 源码审查 + CAPI modifier UT | duration 优先级、运行中延迟生效、iterations 边界。 |
| VM-3 | AC-3.1 至 AC-3.4 | Pattern/native node 源码审查 | 可见性联动、native setter 额外开启 auto monitor。 |
| VM-4 | AC-3.5 | Pattern 源码审查 | form duration cap、iteration 强制和结束标志。 |
| VM-5 | AC-3.6 | SDK + Pattern 源码审查 | `preDecode` 废弃且无实现。 |

## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|--------|
| `state(value: AnimationStatus)` | Public | `AnimationStatus` | `ImageAnimatorAttribute` / `this` | N/A | 设置播放状态。 | AC-1.1 至 AC-1.5 |
| `duration(value: number)` | Public | `number` / static `int | undefined` | `ImageAnimatorAttribute` / `this` | N/A | 设置全局播放时长。 | AC-2.1 至 AC-2.4 |
| `reverse(value: boolean)` | Public | `boolean` | `ImageAnimatorAttribute` / `this` | N/A | 设置播放方向。 | AC-1.4 |
| `fillMode(value: FillMode)` | Public | `FillMode` | `ImageAnimatorAttribute` / `this` | N/A | 设置动画前后状态保持策略。 | AC-1.3 |
| `iterations(value: number)` | Public | `number` / static `int | undefined` | `ImageAnimatorAttribute` / `this` | N/A | 设置播放次数，`-1` 为无限循环。 | AC-2.5 |
| `monitorInvisibleArea(value: boolean)` | Public | `boolean` / static `boolean | undefined` | `ImageAnimatorAttribute` / `this` | N/A | 启用或关闭按可见性自动暂停/恢复。 | AC-3.1 至 AC-3.4 |
| `preDecode(value: number)` | Public deprecated | `number` | `ImageAnimatorAttribute` | N/A | API 9 起废弃，当前 NG 实现无可观测效果。 | AC-3.6 |
| `NODE_IMAGE_ANIMATOR_STATE/DURATION/REVERSE/FILL_MODE/ITERATION` | Public NDK | `ArkUI_AttributeItem.value[0].i32` | `ArkUI_ErrorCode` | `ARKUI_ERROR_CODE_NO_ERROR`, `ARKUI_ERROR_CODE_PARAM_INVALID` | NDK 播放控制属性。 | AC-1.5, AC-2.3, AC-2.5 |

### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|--------|
| `preDecode(value: number)` | 废弃 | API 7-8 可见，API 9 起 deprecated，当前 NG Pattern 不执行预解码参数。 | 不依赖该接口控制缓存；缓存策略按 Feat-01 的 50ms 规则。 | AC-3.6 |

## 接口规格
### 接口定义
**state**

| 属性 | 值 |
|------|-----|
| 函数签名 | `state(value: AnimationStatus): ImageAnimatorAttribute`; static `state(value: AnimationStatus | undefined): this`; NDK `NODE_IMAGE_ANIMATOR_STATE` |
| 返回值 | ArkTS 返回属性对象；NDK 返回错误码 |
| 开放范围 | Public / Public NDK |
| 错误码 | NDK 可返回 `ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-1.1 至 AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | `AnimationStatus` / `int32` | ArkTS 是；static 否；NDK 是 | Initial | 合法值 0 Initial、1 Running、2 Paused、3 Stopped。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | state Initial | cancel/reset/show index。 | AC-1.1 |
| 2 | state Running | 按 reverse Forward/Backward。 | AC-1.4 |
| 3 | dynamic 越界 | 降级 Initial。 | AC-1.5 |
| 4 | native 越界 | 返回参数错误。 | AC-1.5 |

**duration**

| 属性 | 值 |
|------|-----|
| 函数签名 | `duration(value: number): ImageAnimatorAttribute`; static `duration(value: int | undefined): this`; NDK `NODE_IMAGE_ANIMATOR_DURATION` |
| 返回值 | ArkTS 返回属性对象；NDK 返回错误码 |
| 开放范围 | Public / Public NDK |
| 错误码 | NDK size 为 0 返回 `ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-2.1 至 AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `value` | `number` / `int32` | ArkTS 是；static 否；NDK 是 | 1000ms | 小于 0 在动态/modifier/static validator 路径降级到默认。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 存在正逐帧 duration | 全局 duration 不生效，使用逐帧总和。 | AC-2.1 |
| 2 | Running/Paused 时修改 duration | 下一次 repeat 生效。 | AC-2.4 |
| 3 | form render 下 duration 超过 1000 | 限制为 1000。 | AC-3.5 |

**reverse/fillMode/iterations/monitorInvisibleArea/preDecode**

| 属性 | 值 |
|------|-----|
| 函数签名 | `reverse(boolean)`, `fillMode(FillMode)`, `iterations(number)`, `monitorInvisibleArea(boolean)`, `preDecode(number)` |
| 返回值 | ArkTS 返回属性对象；NDK 对应属性返回错误码 |
| 开放范围 | Public / Public NDK，`preDecode` 为 dynamic only deprecated |
| 错误码 | NDK reverse/fillMode 越界返回参数错误；iteration size 为 0 返回参数错误 |
| 关联 AC | AC-1.4, AC-2.5, AC-3.1 至 AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| `reverse` | boolean | 是 | false | dynamic 非 bool reset false；native 仅 0/1。 |
| `fillMode` | FillMode | 是 | Forwards | dynamic 越界 Forwards；native 合法值 0 至 3。 |
| `iterations` | number/int | 是 | 1 | `-1` 无限循环，`< -1` 默认 1。 |
| `monitorInvisibleArea` | boolean | 否 | false | true 时才依据 visible area 暂停/恢复。 |
| `preDecode` | number | 是 | 0 | API 9 起废弃，当前实现无动作。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | reverse true 且 Running | 调用 Backward。 | AC-1.4 |
| 2 | iterations 小于 -1 | 降级为 1。 | AC-2.5 |
| 3 | invisible 且 monitor true | 内部 animator pause。 | AC-3.1 |
| 4 | visible 且 monitor true | 按 reverse 恢复运行。 | AC-3.2 |
| 5 | 调用 preDecode | 无可观测效果。 | AC-3.6 |

## 兼容性声明
- **已有 API 行为变更:** 否。本 Feat 仅记录已有实现。动态 API 的非法值通常 reset/降级，native node 对部分非法值返回错误码，两者均按现状保留。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 7；`monitorInvisibleArea` Dynamic API 17；Static API 23；NDK API 12。
- **API 版本号策略:** 以 SDK `@since` 标注为准；`preDecode` 记录 API 9 deprecated。

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 状态由 `status_` 保存 | `status_` 是用户设置的目标状态，可见性暂停不改变该字段。 | AC-3.1, AC-3.2 |
| duration 优先级 | 逐帧 duration 总和优先于全局 duration。 | AC-2.1 |
| form render 限制 | form 场景限制 duration 和 iteration。 | AC-3.5 |
| `preDecode` 无实现 | 缓存策略不读取 `preDecode` 参数。 | AC-3.6 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不可见且开启 monitor 时暂停内部 animator。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.h:108` |
| 功耗 | 可见性暂停减少不可见播放；form duration 最大 1000ms。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:647` |
| 内存 | 播放控制不新增内存结构；缓存由 Feat-01 约束。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.h:227` |
| 安全 | native node 非法枚举返回参数错误。 | Native UT | `test/unittest/interfaces/native_node_test.cpp:6766` |
| 可靠性 | Running/Paused 中修改 duration 延迟到下一轮，避免当前周期中途跳变。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:704` |
| 可测试性 | CAPI modifier UT 覆盖 iterations 默认、有效和非法值。 | 单测审查 | `test/unittest/capi/modifiers/image_animator_modifier_test.cpp:226` |
| 自动化维测 | inspector 输出 state、duration、reverse、fillMode、iterations、monitorInvisibleArea。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:478` |
| 定界定位 | 状态运行入口集中在 `RunAnimatorByStatus`，duration 入口集中在 `SetDuration`。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:275` |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 播放状态和 duration 按通用实现。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:275` |
| 平板 | 无差异 | 播放状态和 duration 按通用实现。 | 源码审查 | 同上 |
| 折叠屏 | 可见性可能受窗口区域变化触发 | visible area callback 统一处理，不定义折叠屏专有分支。 | 源码审查 | `frameworks/core/components_ng/pattern/image_animator/image_animator_pattern.cpp:393` |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 播放控制不新增无障碍语义。 | N/A |
| 大字体 | 否 | 不涉及文本。 | N/A |
| 深色模式 | 否 | 播放控制不改变图片资源颜色策略。 | N/A |
| 多窗口/分屏 | 是 | visible area 可能因窗口变化触发 pause/resume。 | AC-3.1, AC-3.2 |
| 多用户 | 否 | 不涉及用户数据。 | N/A |
| 版本升级 | 是 | `monitorInvisibleArea` API 17+，static API 23+，preDecode deprecated since 9。 | AC-3.1, AC-3.6 |
| 生态兼容 | 是 | 动态与 native 非法值处理策略不同，需在测试和文档中分范式验证。 | AC-1.5 |

## 行为场景（可选，Gherkin）
Feature: ImageAnimator playback control
  作为 ArkUI 开发者
  我想要控制动画状态、时长和可见性联动
  以便 动画按预期开始、暂停、停止和恢复

  Scenario: visible area pauses and resumes running animation
    Given ImageAnimator state is Running
    And monitorInvisibleArea is true
    When visible area callback reports invisible
    Then the internal animator is paused
    When visible area callback reports visible
    Then the internal animator resumes in the configured direction

  Scenario: frame duration overrides global duration
    Given at least one frame has positive duration
    When ImageAnimator builds picture animation
    Then the animator duration equals the sum of positive frame durations

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
    query: "ImageAnimator state duration reverse fillMode iterations monitorInvisibleArea form preDecode implementation"
```

**关键文档:** `docs/pattern/image_animator/Image_Animator_Knowledge_Base.md`
