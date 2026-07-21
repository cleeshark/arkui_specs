# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 属性动画全量规格 (.animation 隐式属性动画 / PropertyAnimation / Animatable / AnimatableArithmetic) |
| 特性编号 | Func-03-02-02-Feat-01 |
| FuncID | 03-02-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `.animation(value: AnimateParam)` 属性 | @since 7，隐式属性动画入口 |
| ADDED | AnimateParam 接口 (duration/tempo/curve/delay/iterations/playMode/onFinish) | @since 7 |
| ADDED | FillMode 枚举 (None/Forwards/Backwards/Both) | @since 7 |
| ADDED | PlayMode 枚举 (Normal/Reverse/Alternate/AlternateReverse) | @since 7 |
| ADDED | curve 参数支持 ICurve 类型 | @since 9 |
| ADDED | @form 标注 | @since 9，卡片支持 |
| ADDED | @crossplatform 标注 | @since 10 |
| ADDED | @atomicservice 标注 | @since 11 |
| ADDED | finishCallbackType 字段 (REMOVED/LOGICALLY) | @since 11 |
| ADDED | expectedFrameRateRange 字段 | @since 11 |
| ADDED | duration 最大值从 API 26 起调整为 2000ms（卡片场景） | API 26 行为变更 |
| MODIFIED | 卡片动画最大时长限制 | API 26 前限 1000ms，API 26+ 限 2000ms |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/02-property-animation/design.md`
- **SDK 类型定义**:
  - Common: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`
  - Enums: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/enums.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 隐式属性动画基本使用

**角色**: 应用开发者
**期望**: 我想要通过 `.animation()` 属性为组件的属性变化添加动画效果
**价值**: 以便在属性变化时自动产生平滑过渡

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在属性设置前调用 `.animation({ duration: 1000, curve: Curve.EaseInOut })` THEN 后续属性变化通过 PropertyAnimation 插值器产生动画过渡 | 正常 |
| AC-1.2 | WHEN `.animation()` 后设置 `.width(200)` THEN 从当前宽度到 200vp 的变化通过 1000ms EaseInOut 曲线过渡（`property_animation.h:28`，`property_animation.cpp:55`） | 正常 |
| AC-1.3 | WHEN 动画完成 THEN onFinish 回调被触发一次 | 正常 |
| AC-1.4 | WHEN 组件首次构建时调用 `.animation()` THEN 不生成动画（`js_view_context.cpp:628-631` CheckTopNodeFirstBuilding 返回 true 时跳过） | 边界 |
| AC-1.5 | WHEN `.animation()` 参数为 null 或非对象 THEN 调用 closeAnimation 关闭动画（`js_view_context.cpp:648-651`） | 异常 |

### US-2: 可动画属性类型

**角色**: 应用开发者
**期望**: 我想要知道哪些组件属性可以通过 `.animation()` 产生动画
**价值**: 以便正确使用属性动画

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 对宽度设置 `.width()` 变化 THEN 产生 PROPERTY_WIDTH 类型动画（`animatable.h:28` PROPERTY_WIDTH） | 正常 |
| AC-2.2 | WHEN 对背景色 `.backgroundColor()` 变化 THEN 产生 PROPERTY_BG_COLOR 类型动画（`animatable.h:30`） | 正常 |
| AC-2.3 | WHEN 对透明度 `.opacity()` 变化 THEN 产生 PROPERTY_OPACITY 类型动画（`animatable.h:31`） | 正常 |
| AC-2.4 | WHEN 对外边距 `.margin()` 变化 THEN 产生 PROPERTY_MARGIN_LEFT/TOP/RIGHT/BOTTOM 类型动画（`animatable.h:32-35`） | 正常 |
| AC-2.5 | WHEN 对边框宽度/颜色/圆角变化 THEN 产生对应的 PROPERTY_BORDER_* 类型动画（`animatable.h:42-57`） | 正常 |

### US-3: 插值计算

**角色**: 框架开发者
**期望**: 我想要理解属性动画的插值计算机制
**价值**: 以便实现自定义可动画类型

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 动画帧回调到达 THEN PropertyAnimation::OnNormalizedTimestampChanged 被调用，normalized ∈ [0.0, 1.0]（`property_animation.cpp:55`） | 正常 |
| AC-3.2 | WHEN OnNormalizedTimestampChanged 被调用 THEN Calculate(keyTime) 计算关键时间点插值（`property_animation.cpp:81`），TriggerFrame 执行（`:101`） | 正常 |
| AC-3.3 | WHEN TriggerFrame 执行 THEN 调用 Next<T>(start, end, time) 模板，使用 AnimatableArithmetic 的 Plus/Minus/Multiply 运算（`property_animation.cpp:172`） | 正常 |
| AC-3.4 | WHEN 插值计算完成 THEN 通过 animateTo_ 回调通知属性更新（`property_animation.h:43-46` AddListener） | 正常 |

### US-4: 动画参数配置

**角色**: 应用开发者
**期望**: 我想要配置动画的时长、速度、曲线、延迟、迭代和播放模式
**价值**: 以便精确控制动画行为

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `duration: 2000` THEN 动画在 2000ms 内完成（`common.d.ts:4323`，default 1000） | 正常 |
| AC-4.2 | WHEN 设置 `tempo: 2.0` THEN 动画以 2 倍速播放（`common.d.ts:4343`，default 1.0） | 正常 |
| AC-4.3 | WHEN 设置 `curve: Curve.Linear` THEN 动画线性变化（`common.d.ts:4407`，default EaseInOut） | 正常 |
| AC-4.4 | WHEN 设置 `delay: 500` THEN 动画延迟 500ms 后开始（`common.d.ts:4430`，default 0） | 正常 |
| AC-4.5 | WHEN 设置 `iterations: 3` THEN 动画播放 3 次（`common.d.ts:4449`，default 1） | 正常 |
| AC-4.6 | WHEN 设置 `playMode: PlayMode.Alternate` THEN 动画交替正向/反向播放（`common.d.ts:4477`，default Normal） | 正常 |
| AC-4.7 | WHEN 设置 `tempo: 0` THEN 无动画效果（动画时长为 0）（`common.d.ts:4326`） | 边界 |

### US-5: 卡片动画限制

**角色**: 应用开发者
**期望**: 我想要在 ArkTS 卡片中使用属性动画
**价值**: 以便在卡片场景下实现动画效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 在 API 26 以下的卡片中设置 duration > 1000 THEN duration 被截断为 1000ms（`js_view_context.cpp:637-639`，FORM_MAX_DURATION） | 边界 |
| AC-5.2 | WHEN 在 API 26+ 的卡片中设置 duration > 2000 THEN duration 被截断为 2000ms（`js_view_context.cpp:637-639`，DEFAULT_DURATION） | 边界 |
| AC-5.3 | WHEN 卡片 finish 回调触发动画时已用时间 + 新动画时长超过限制 THEN 新动画时长被截断为剩余时间（`js_view_context.cpp:673-679`） | 边界 |

### US-6: 完成回调类型

**角色**: 应用开发者
**期望**: 我想要控制 onFinish 回调的触发时机
**价值**: 以便在动画逻辑结束和实际移除时执行不同逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 `finishCallbackType: FinishCallbackType.REMOVED` THEN onFinish 在动画被移除时触发（`common.d.ts:4227`，default REMOVED） | 正常 |
| AC-6.2 | WHEN 设置 `finishCallbackType: FinishCallbackType.LOGICALLY` THEN onFinish 在动画逻辑进入收尾状态时触发，可能仍有长尾动画（`common.d.ts:4239`） | 正常 |
| AC-6.3 | WHEN 未设置 finishCallbackType THEN 默认为 REMOVED（`common.d.ts:4498`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-3, R-4 | TASK-PROP-ANIM-01 | UT | `test/unittest/core/animation/property_animation_test.cpp` |
| AC-2.1 ~ AC-2.5 | R-5 | TASK-PROP-ANIM-01 | UT | animatable 属性类型单测 |
| AC-3.1 ~ AC-3.4 | R-6, R-7, R-8 | TASK-PROP-ANIM-01 | UT | 插值计算单测 |
| AC-4.1 ~ AC-4.7 | R-9, R-10, R-11 | TASK-PROP-ANIM-01 | UT | AnimateParam 参数单测 |
| AC-5.1 ~ AC-5.3 | R-12, R-13 | TASK-PROP-ANIM-01 | UT | 卡片动画限制单测 |
| AC-6.1 ~ AC-6.3 | R-14 | TASK-PROP-ANIM-01 | UT | finishCallbackType 单测 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `.animation(AnimateParam)` | ViewContextModelNG::openAnimation 设置 ImplicitAnimationOption | 首次构建时跳过（`js_view_context.cpp:628`） | AC-1.1, AC-1.4 |
| R-2 | 行为 | openAnimation 后设置属性 | 属性 setter 检测到 ImplicitAnimationOption，创建 PropertyAnimation 并加入 Animator | AnimatableType 枚举决定属性类型 | AC-1.2 |
| R-3 | 行为 | 动画播放完成 | onFinish 回调被触发一次 | iterations=-1 时不触发 | AC-1.3 |
| R-4 | 异常 | `.animation()` 参数为 null 或非对象 | 调用 closeAnimation 关闭动画 | `js_view_context.cpp:648-651` | AC-1.5 |
| R-5 | 行为 | 设置可动画属性 | 根据 AnimatableType 枚举创建对应类型 PropertyAnimation | 35 种属性类型（`animatable.h:27-66`） | AC-2.1 ~ AC-2.5 |
| R-6 | 行为 | Animator 帧回调 | OnNormalizedTimestampChanged(normalized, reverse) 被调用 | normalized ∈ [0.0, 1.0]（`property_animation.cpp:55`） | AC-3.1 |
| R-7 | 行为 | OnNormalizedTimestampChanged 调用 | Calculate(keyTime) 计算插值，TriggerFrame 执行 | `property_animation.cpp:81, 101` | AC-3.2 |
| R-8 | 行为 | TriggerFrame 执行 | 调用 Next<T> 模板，使用 AnimatableArithmetic Plus/Minus/Multiply 运算 | `property_animation.cpp:172` | AC-3.3 |
| R-9 | 行为 | 设置 duration | 动画在指定 ms 内完成 | default 1000，[0, +∞)，浮点向下取整 | AC-4.1 |
| R-10 | 行为 | 设置 tempo | 动画以 tempo 倍速播放 | default 1.0，[0, +∞)，0 表示无动画 | AC-4.2, AC-4.7 |
| R-11 | 行为 | 设置 curve | 动画按指定曲线变化 | default EaseInOut，支持 Curve/string/ICurve | AC-4.3 |
| R-12 | 边界 | 卡片场景 API < 26 且 duration > 1000 | duration 截断为 1000ms | `js_view_context.cpp:637` FORM_MAX_DURATION | AC-5.1 |
| R-13 | 边界 | 卡片场景 API >= 26 且 duration > 2000 | duration 截断为 2000ms | `js_view_context.cpp:639` DEFAULT_DURATION | AC-5.2 |
| R-14 | 行为 | 设置 finishCallbackType | REMOVED: 动画移除时触发；LOGICALLY: 逻辑收尾时触发 | default REMOVED（`common.d.ts:4498`） | AC-6.1 ~ AC-6.3 |
| R-15 | 边界 | tempo = 0 | 无动画效果 | 动画时长为 0 | AC-4.7 |
| R-16 | 边界 | duration = 0 | 立即跳到目标属性值 | 无过渡动画 | AC-4.1 |
| R-17 | 恢复 | UIAbility 转入后台 | 有限迭代动画立即终止并触发 onFinish | `common.d.ts:4481-4482` | AC-1.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | .animation() 隐式动画机制、首次构建跳过、null 参数处理 |
| VM-2 | AC-2.1 ~ AC-2.5 | UT | AnimatableType 属性类型映射 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | 插值计算链路：OnNormalizedTimestampChanged → Calculate → TriggerFrame → Next<T> |
| VM-4 | AC-4.1 ~ AC-4.7 | UT | AnimateParam 参数：duration/tempo/curve/delay/iterations/playMode |
| VM-5 | AC-5.1 ~ AC-5.3 | UT | 卡片动画时长限制（API 版本差异） |
| VM-6 | AC-6.1 ~ AC-6.3 | UT | finishCallbackType 行为差异 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| .animation(value: AnimateParam) | Public | AnimateParam | T (当前组件) | N/A | 设置隐式属性动画 | AC-1.1 |
| AnimateParam.duration | Public | number | — | N/A | 动画时长 | AC-4.1 |
| AnimateParam.tempo | Public | number | — | N/A | 播放速度 | AC-4.2 |
| AnimateParam.curve | Public | Curve\|string\|ICurve | — | N/A | 动画曲线 | AC-4.3 |
| AnimateParam.delay | Public | number | — | N/A | 延迟 | AC-4.4 |
| AnimateParam.iterations | Public | number | — | N/A | 迭代次数 | AC-4.5 |
| AnimateParam.playMode | Public | PlayMode | — | N/A | 播放模式 | AC-4.6 |
| AnimateParam.onFinish | Public | () => void | — | N/A | 完成回调 | AC-1.3 |
| AnimateParam.finishCallbackType | Public | FinishCallbackType | — | N/A | 完成回调类型 | AC-6.1 |
| AnimateParam.expectedFrameRateRange | Public | ExpectedFrameRateRange | — | N/A | 帧率范围 | AC-4.3 |
| FillMode 枚举 | Public | None/Forwards/Backwards/Both | — | N/A | 填充模式 | AC-4.6 |
| PlayMode 枚举 | Public | Normal/Reverse/Alternate/AlternateReverse | — | N/A | 播放模式 | AC-4.6 |
| FinishCallbackType 枚举 | Public | REMOVED/LOGICALLY | — | N/A | 完成回调类型 | AC-6.1 |
| ExpectedFrameRateRange 接口 | Public | {min, max, expected} | — | N/A | 帧率范围 | AC-4.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 卡片动画最大时长 (API 26 前) | MODIFIED | API 26 前限 1000ms | API 26+ 调整为 2000ms | AC-5.1, AC-5.2 |

## 接口规格

### 接口定义

**.animation(value: AnimateParam)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `animation(value: AnimateParam): T` |
| 返回值 | `T` — 当前组件（链式调用） |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | AnimateParam | 是 | — | 包含动画参数的对象 |
| value.duration | number | 否 | 1000 | [0, +∞)，浮点向下取整 |
| value.tempo | number | 否 | 1.0 | [0, +∞)，负数截断为 0 |
| value.curve | Curve\|string\|ICurve | 否 | Curve.EaseInOut | 无效字符串回退 EaseInOut |
| value.delay | number | 否 | 0 | (-∞, +∞) |
| value.iterations | number | 否 | 1 | [-1, +∞)，-1=无限，浮点向下取整 |
| value.playMode | PlayMode | 否 | Normal | Normal/Reverse/Alternate/AlternateReverse |
| value.onFinish | () => void | 否 | — | 完成回调 |
| value.finishCallbackType | FinishCallbackType | 否 | REMOVED | REMOVED/LOGICALLY |
| value.expectedFrameRateRange | ExpectedFrameRateRange | 否 | — | {min, max, expected} |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 组件非首次构建时调用 .animation() | 设置 ImplicitAnimationOption，后续属性变化产生动画 | AC-1.1 |
| 2 | 组件首次构建时调用 .animation() | 跳过，不生成动画 | AC-1.4 |
| 3 | 参数为 null 或非对象 | 调用 closeAnimation 关闭动画 | AC-1.5 |
| 4 | 卡片场景 duration 超限 | 截断为限制值 | AC-5.1, AC-5.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - 卡片动画最大时长从 API 26 起从 1000ms 调整为 2000ms（AC-5.1, AC-5.2）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 API @since 7，ICurve 支持 @since 9，@crossplatform @since 10，finishCallbackType/expectedFrameRateRange @since 11

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 隐式动画机制 | `.animation()` 在 ViewStackProcessor 上设置 ImplicitAnimationOption，后续属性设置检测后创建 PropertyAnimation | AC-1.1, AC-1.2 |
| 首次构建跳过 | CheckTopNodeFirstBuilding 为 true 时跳过动画生成 | AC-1.4 |
| UI 线程约束 | JSAnimation 和 Model 层操作在 UI 线程执行 | AC-1.1 |
| 卡片时长限制 | 卡片场景动画时长受 FORM_MAX_DURATION / DEFAULT_DURATION 限制 | AC-5.1, AC-5.2 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 属性动画帧率 ≥ 60fps | Trace + 手工 | Trace 打点 |
| 内存 | PropertyAnimation 在动画结束后被正确释放 | UT + Dump | RefPtr 引用计数 |
| 可靠性 | 重复 .animation() 调用不崩溃 | UT | Model 层单测 |
| 问题定位 | 关键路径 hilog 覆盖（openAnimation/closeAnimation） | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

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
| 无障碍 | 否 | 属性动画不直接涉及无障碍 | — |
| 大字体 | 否 | 属性动画不涉及字体 | — |
| 深色模式 | 是 | 颜色属性动画（PROPERTY_BG_COLOR 等）支持深色模式主题切换 | AC-2.2 |
| 多窗口/分屏 | 否 | 属性动画无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | 卡片动画时长限制在 API 26 前后有变化 | AC-5.1, AC-5.2 |
| 生态兼容 | 否 | 无特殊生态兼容问题 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 属性动画
  作为应用开发者
  我想要通过 .animation() 为属性变化添加动画
  以便实现平滑的视觉过渡

  Scenario: 基本属性动画
    Given 组件已渲染，宽度为 100vp
    When 调用 .animation({ duration: 1000, curve: Curve.EaseInOut })
    And 设置 .width(200)
    Then 宽度从 100vp 到 200vp 在 1000ms 内按 EaseInOut 曲线过渡
    And 动画完成后 onFinish 被触发

  Scenario: 首次构建不生成动画
    Given 组件首次构建
    When 在构建中调用 .animation({ duration: 1000 })
    Then 不生成动画，属性直接设置为最终值

  Scenario: null 参数关闭动画
    Given 组件已渲染
    When 调用 .animation(null)
    Then 隐式动画被关闭
    And 后续属性变化无动画

  Scenario Outline: 卡片动画时长限制
    Given 在 ArkTS 卡片中使用 .animation
    When 设置 duration = <duration>
    Then 实际动画时长为 <actual>

    Examples:
      | duration | api_version | actual |
      | 500      | API 25      | 500     |
      | 1500     | API 25      | 1000    |
      | 1500     | API 26      | 1500    |
      | 3000     | API 26      | 2000    |

  Scenario: tempo 为 0
    Given 设置 .animation({ duration: 1000, tempo: 0 })
    When 属性变化
    Then 无动画效果，属性立即跳到目标值

  Scenario: finishCallbackType
    Given 设置 .animation({ finishCallbackType: FinishCallbackType.LOGICALLY })
    When 动画逻辑进入收尾状态
    Then onFinish 被触发
    And 动画可能仍有长尾效果
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
  - repo: "openharmony/ace_engine"
    query: "PropertyAnimation 插值计算 SetStart/AddAnimatable/Calculate/TriggerFrame/Next 模板机制"
  - repo: "openharmony/ace_engine"
    query: "AnimatableType 枚举和 Animatable 基类 SetTimePoint/GetTimePoint"
  - repo: "openharmony/ace_engine"
    query: "ViewContextModelNG openAnimation/closeAnimation 隐式动画管理"
  - repo: "openharmony/ace_engine"
    query: "JSViewContext::JSAnimation .animation 属性解析和卡片时长限制"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 枚举定义: `interface/sdk-js/api/@internal/component/ets/enums.d.ts`
- 源码入口: `frameworks/core/animation/property_animation.h`, `frameworks/core/animation/property_animation.cpp`
