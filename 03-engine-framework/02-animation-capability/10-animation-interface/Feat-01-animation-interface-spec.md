# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 动画接口全量规格 (animateTo / animateToImmediately / keyframeAnimateTo / .animation() / UIContext 动画接口) |
| 特性编号 | Func-03-02-10-Feat-01 |
| FuncID | 03-02-10 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | animateTo(value: AnimateParam, event: () => void) | @since 7，显式动画入口 |
| ADDED | .animation(value: AnimateParam) 属性 | @since 7，声明式动画属性 |
| ADDED | AnimateParam 接口 (duration/tempo/curve/delay/iterations/playMode/onFinish) | @since 7，统一参数模型 |
| ADDED | PlayMode 枚举 (Normal/Reverse/Alternate/AlternateReverse) | @since 7 |
| ADDED | FillMode 枚举 (None/Forwards/Backwards/Both) | @since 7 |
| ADDED | curves.Curve 枚举 (Linear/Ease/EaseIn/EaseOut/EaseInOut/...) | @since 7 |
| ADDED | curves.init/steps/cubicBezier/spring (返回 string) | @since 7，@deprecated since 9 |
| ADDED | curves.initCurve/stepsCurve/cubicBezierCurve/springCurve (返回 ICurve) | @since 9 |
| ADDED | ICurve 接口 (interpolate(fraction)) | @since 9 |
| ADDED | finishCallbackType: FinishCallbackType | @since 11，REMOVED/LOGICALLY |
| ADDED | keyframeAnimateTo (UIContext) | @since 11 |
| ADDED | curves.customCurve (返回 ICurve) | @since 10 |
| ADDED | curves.interpolatingSpring (返回 ICurve) | @since 10 |
| ADDED | animateToImmediately | @since 12 |
| ADDED | expectedFrameRateRange | @since 11 |
| ADDED | UIContext.animateTo / UIContext.animateToImmediately | @since 18 |
| MODIFIED | duration 上限：API<26 为 1000ms，API≥26 为 2000ms | API 26 行为变更 |
| MODIFIED | animateTo @deprecated since 18 → UIContext.animateTo | 迁移到 UIContext |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/10-animation-interface/design.md`
- **SDK 类型定义**:
  - `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts` (AnimateParam:4301, animateTo:7082, animateToImmediately:7095, FinishCallbackType:4216, .animation():21450)
  - `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/enums.d.ts` (FillMode:1149, PlayMode:1215)
  - `<OH_ROOT>/interface/sdk-js/api/@ohos.curves.d.ts` (Curve:39, ICurve:171, initCurve:197, stepsCurve:226, cubicBezierCurve:277, customCurve:245)

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: animateTo 显式动画

**角色**: 应用开发者
**期望**: 我想要使用 animateTo 在闭包中声明状态变化并自动插入过渡动画
**价值**: 以便以命令式方式精确控制动画时机和参数

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `animateTo({duration: 1000, curve: Curve.EaseInOut}, () => { this.width = 200 })` THEN 在闭包执行期间捕获 width 属性变化，插入 1000ms EaseInOut 过渡动画 | 正常 |
| AC-1.2 | WHEN 在 API 18+ 调用全局 `animateTo` THEN 标记为 @deprecated since 18，建议使用 `UIContext.animateTo`（`common.d.ts:7079-7080`） | 正常 |
| AC-1.3 | WHEN 设置 `duration` 超过上限 THEN API<26 钳为 1000ms，API≥26 钳为 2000ms（`common.d.ts:4307-4309`） | 边界 |
| AC-1.4 | WHEN 设置 `tempo=0` THEN 无动画；设置 `tempo=+∞` THEN 当前帧完成并立即执行完成回调（`common.d.ts:4326-4329`） | 边界 |
| AC-1.5 | WHEN 设置 `iterations=-1` THEN 动画无限循环（`animation_constants.h:26`，ANIMATION_REPEAT_INFINITE=-1） | 边界 |
| AC-1.6 | WHEN 设置 `finishCallbackType=FinishCallbackType.LOGICALLY` THEN 动画逻辑进入衰减态时触发 onFinish 回调（`common.d.ts:4229-4239`） | 正常 |

### US-2: animateToImmediately 立即动画

**角色**: 应用开发者
**期望**: 我想要使用 animateToImmediately 立即交付显式动画
**价值**: 以便在需要立即生效的场景中跳过延迟

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `animateToImmediately({duration: 1000, curve: Curve.Linear}, () => { this.width = 200 })` THEN 立即交付动画，不等待当前帧结束（`common.d.ts:7084-7095`） | 正常 |
| AC-2.2 | WHEN 在 API 18+ 调用全局 `animateToImmediately` THEN 建议使用 `UIContext.animateToImmediately` | 正常 |

### US-3: keyframeAnimateTo 关键帧动画

**角色**: 应用开发者
**期望**: 我想要使用 keyframeAnimateTo 创建关键帧动画
**价值**: 以便定义多关键点的复杂动画路径

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `UIContext.keyframeAnimateTo({iterations, keyframeOptions}, keyframes)` THEN 按关键帧定义的路径执行动画（@since 11） | 正常 |

### US-4: .animation() 声明式动画属性

**角色**: 应用开发者
**期望**: 我想要使用 .animation() 属性声明组件的动画参数
**价值**: 以便以声明式方式为属性变化绑定动画

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 在组件上设置 `.animation({duration: 300, curve: Curve.EaseInOut})` THEN 组件属性变化时自动插入 300ms EaseInOut 动画（`common.d.ts:21442-21450`） | 正常 |
| AC-4.2 | WHEN 在 `attributeModifier` 中调用 `.animation()` THEN 不可使用（已知限制） | 异常 |

### US-5: 曲线类型与解析

**角色**: 应用开发者
**期望**: 我想要通过多种形式（枚举/字符串/ICurve对象）指定动画曲线
**价值**: 以便在不同场景下选择最合适的曲线表达方式

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `curve: Curve.EaseInOut` THEN 使用预定义的三阶贝塞尔曲线 (0.42, 0.0, 0.58, 1.0)（`@ohos.curves.d.ts:77-85`） | 正常 |
| AC-5.2 | WHEN 设置 `curve: "cubic-bezier(0.42, 0.0, 0.58, 1.0)"` THEN 解析为 CubicCurve，P1=(0.42,0.0), P2=(0.58,1.0)，MoveInternal 解 Bx(m)=time 返回 By(m)，cubicErrorBound_=0.001（`cubic_curve.h:30-74`） | 正常 |
| AC-5.3 | WHEN 使用 `curves.init()` (返回 string) THEN @deprecated since 9，建议使用 `curves.initCurve()` (返回 ICurve)（`@ohos.curves.d.ts:206-210`） | 正常 |
| AC-5.4 | WHEN 设置 `curve: "linear"` THEN 使用 LinearCurve，MoveInternal 返回 time（`curve.h:130-161`） | 正常 |
| AC-5.5 | WHEN 设置 `curve: "steps(3, start)"` THEN 使用 StepsCurve，3 阶跃，step-position=start（`curve.h:213-278`） | 正常 |
| AC-5.6 | WHEN 使用 `curves.customCurve((fraction) => fraction * 2)` THEN 创建自定义曲线，MoveInternal 调用回调函数（`curve.h:280-302`，`@ohos.curves.d.ts:245`） | 正常 |

### US-6: 求值管线

**角色**: 引擎开发者
**期望**: 我想要了解动画属性值的求值管线
**价值**: 以便理解曲线插值如何映射到实际属性值

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN CurveAnimation<T>::Calculate(time, curve) 被调用 THEN 执行 `evaluator_->Evaluate(begin_, end_, curve->Move(time))` 得到 currentValue（`curve_animation.h:100-111`） | 正常 |
| AC-6.2 | WHEN 属性类型为 Color THEN 使用 LinearEvaluator<Color> 特化，在 gamma 线性空间插值（GAMMA_FACTOR=2.2）（`evaluator.h:48-74`） | 正常 |
| AC-6.3 | WHEN normalizedTime=0.0 THEN currentValue=begin；WHEN normalizedTime=1.0 THEN currentValue=end（`curve_animation.h:102-109`） | 边界 |
| AC-6.4 | WHEN normalizedTime 超出 [0,1] THEN 输出 LOGE 并返回，不更新（`curve_animation.h:115-118`） | 异常 |

### US-7: AnimationInterface 来源标记

**角色**: 引擎开发者
**期望**: 我想要通过 AnimationInterface 枚举追踪动画来源
**价值**: 以便在 metrics/tracing 中区分不同动画接口的性能数据

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 通过 animateTo 创建动画 THEN AnimationOption.animationInterface_ = ANIMATE_TO，GetAnimationInterfaceString() 返回 "animateTo"（`animation_option.h:31-40, 182-186`） | 正常 |
| AC-7.2 | WHEN 未设置 AnimationInterface THEN 默认为 UNKNOWN，GetAnimationInterfaceString() 返回 "unknown"（`animation_constants.h:99`，`animation_option.h:233`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.6 | R-1, R-2, R-3, R-4, R-5, R-6 | TASK-ANIM-IFACE-01 | UT + 手工 | `test/unittest/core/animation/` |
| AC-2.1 ~ AC-2.2 | R-7 | TASK-ANIM-IFACE-01 | UT + 手工 | animateToImmediately 单测 |
| AC-3.1 | R-8 | TASK-ANIM-IFACE-01 | 手工 | keyframeAnimateTo 集成测试 |
| AC-4.1 ~ AC-4.2 | R-9, R-10 | TASK-ANIM-IFACE-01 | UT | .animation() 属性单测 |
| AC-5.1 ~ AC-5.6 | R-11, R-12, R-13, R-14, R-15 | TASK-ANIM-IFACE-01 | UT | 曲线解析单测 |
| AC-6.1 ~ AC-6.4 | R-16, R-17, R-18, R-19 | TASK-ANIM-IFACE-01 | UT | CurveAnimation 求值单测 |
| AC-7.1 ~ AC-7.2 | R-20, R-21 | TASK-ANIM-IFACE-01 | UT | AnimationInterface 单测 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | animateTo(AnimateParam, event) 调用 | 在 event 闭包执行期间捕获属性变化，按 AnimateParam 参数插入过渡动画 | `common.d.ts:7082` | AC-1.1 |
| R-2 | 行为 | animateTo 设置 duration 超过上限 | API<26 钳为 1000ms，API≥26 钳为 2000ms，浮点值取整 | `common.d.ts:4307-4309` | AC-1.3 |
| R-3 | 边界 | animateTo 设置 tempo=0 | 无动画 | `common.d.ts:4326` | AC-1.4 |
| R-4 | 边界 | animateTo 设置 tempo=+∞ | 当前帧完成并立即执行完成回调 | `common.d.ts:4328-4329` | AC-1.4 |
| R-5 | 边界 | animateTo 设置 iterations=-1 | 无限循环（ANIMATION_REPEAT_INFINITE=-1） | `animation_constants.h:26` | AC-1.5 |
| R-6 | 行为 | animateTo 设置 finishCallbackType=LOGICALLY | 动画逻辑进入衰减态时触发 onFinish 回调 | `common.d.ts:4229-4239` | AC-1.6 |
| R-7 | 行为 | animateToImmediately(AnimateParam, event) 调用 | 立即交付显式动画，不等待当前帧结束 | `common.d.ts:7084-7095` | AC-2.1 |
| R-8 | 行为 | UIContext.keyframeAnimateTo 调用 | 按关键帧定义的路径执行动画 | @since 11 | AC-3.1 |
| R-9 | 行为 | .animation(AnimateParam) 属性设置 | 组件属性变化时自动插入动画 | `common.d.ts:21442-21450` | AC-4.1 |
| R-10 | 异常 | .animation() 在 attributeModifier 中调用 | 不可使用（已知限制） | — | AC-4.2 |
| R-11 | 行为 | AnimateParam.curve 设置为 Curve 枚举 | 使用预定义曲线（如 EaseInOut = cubic-bezier(0.42,0.0,0.58,1.0)） | `@ohos.curves.d.ts:77-85` | AC-5.1 |
| R-12 | 行为 | AnimateParam.curve 设置为 string "cubic-bezier(x1,y1,x2,y2)" | 解析为 CubicCurve，MoveInternal 解 Bx(m)=time 求 m 返回 By(m)，cubicErrorBound_=0.001 | `cubic_curve.h:30-74` | AC-5.2 |
| R-13 | 行为 | 使用 curves.init/steps/cubicBezier/spring (返回 string) | @deprecated since 9，建议使用 ICurve 版本 | `@ohos.curves.d.ts:206-210, 256-260, 289-294, 345-350` | AC-5.3 |
| R-14 | 行为 | AnimateParam.curve 设置为 "linear" | 使用 LinearCurve，MoveInternal 返回 time | `curve.h:130-161` | AC-5.4 |
| R-15 | 行为 | AnimateParam.curve 设置为 "steps(count, position)" | 使用 StepsCurve，count 阶跃，position=start/end | `curve.h:213-278` | AC-5.5 |
| R-16 | 行为 | CurveAnimation<T>::Calculate(time, curve) 调用 | evaluator_->Evaluate(begin_, end_, curve->Move(time)) 得到 currentValue，NotifyListener(currentValue) | `curve_animation.h:100-111, 120` | AC-6.1 |
| R-17 | 行为 | 属性类型为 Color 时求值 | LinearEvaluator<Color> 特化，ARGB→gamma 线性空间插值→gamma 空间，GAMMA_FACTOR=2.2 | `evaluator.h:48-74, 77` | AC-6.2 |
| R-18 | 边界 | normalizedTime=0.0 | currentValue=begin；normalizedTime=1.0，currentValue=end | `curve_animation.h:102-109` | AC-6.3 |
| R-19 | 异常 | normalizedTime 超出 [0,1] | 输出 LOGE，不更新 currentValue | `curve_animation.h:115-118` | AC-6.4 |
| R-20 | 行为 | animateTo 创建动画时 AnimationOption.animationInterface_ | 设置为 ANIMATE_TO，GetAnimationInterfaceString() 返回 "animateTo" | `animation_option.h:31-40, 182-186` | AC-7.1 |
| R-21 | 行为 | 未设置 AnimationInterface | 默认 UNKNOWN，GetAnimationInterfaceString() 返回 "unknown" | `animation_constants.h:99, animation_option.h:233` | AC-7.2 |
| R-22 | 边界 | AnimationOption::IsValid() 判定 | duration>0 || allowRunningAsynchronously | `animation_option.h:137-140` | — |
| R-23 | 边界 | AnimationOption::SetIteration(iteration) | iteration<0 且 ≠-1 时忽略 | `animation_option.h:76-82` | — |
| R-24 | 边界 | AnimationOption::SetTempo(tempo) | tempo<0 时忽略 | `animation_option.h:89-95` | — |
| R-25 | 行为 | CubicCurve::MoveInternal(time) | 解 Bx(m)=3m(1-m)²*x0_+3m²*x1_+m³=time 求 m（二分法），返回 By(m)=3m(1-m)²*y0_+3m²*y1_+m³ | `cubic_curve.h:64-67` | — |
| R-26 | 行为 | Interpolator::OnTimestampChanged(timestamp, normalizedTime, reverse) | 调用 OnNormalizedTimestampChanged(normalizedTime, reverse) | `interpolator.h:47-51` | — |
| R-27 | 行为 | Curves 静态工厂单例 | EASE/LINEAR/FAST_OUT_SLOW_IN 等为 static const RefPtr 单例 | `curves.h:30-48` | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.6 | UT + 手工 | animateTo 参数解析、duration 上限、tempo 边界、iterations 无限循环、finishCallbackType |
| VM-2 | AC-2.1 ~ AC-2.2 | UT + 手工 | animateToImmediately 立即交付、@deprecated 迁移 |
| VM-3 | AC-3.1 | 手工 | keyframeAnimateTo 关键帧动画 |
| VM-4 | AC-4.1 ~ AC-4.2 | UT | .animation() 属性声明、attributeModifier 限制 |
| VM-5 | AC-5.1 ~ AC-5.6 | UT | Curve 枚举/string/ICurve 三种形式解析、CubicCurve 求解、string→ICurve 废弃迁移 |
| VM-6 | AC-6.1 ~ AC-6.4 | UT | CurveAnimation 求值管线、Color gamma 插值、边界值处理 |
| VM-7 | AC-7.1 ~ AC-7.2 | UT | AnimationInterface 枚举标记和字符串映射 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| animateTo(value: AnimateParam, event: () => void) | Public | AnimateParam + event 闭包 | void | N/A | 显式动画入口 | AC-1.1 |
| animateToImmediately(value: AnimateParam, event: () => void) | Public | AnimateParam + event 闭包 | void | N/A | 立即显式动画 | AC-2.1 |
| animation(value: AnimateParam) | Public | AnimateParam | T | N/A | 声明式动画属性 | AC-4.1 |
| UIContext.animateTo(value: AnimateParam, event: () => void) | Public | AnimateParam + event 闭包 | void | N/A | UIContext 绑定的显式动画 | AC-1.2 |
| UIContext.animateToImmediately(value: AnimateParam, event: () => void) | Public | AnimateParam + event 闭包 | void | N/A | UIContext 绑定的立即动画 | AC-2.2 |
| UIContext.keyframeAnimateTo(iterations, keyframeOptions, keyframes) | Public | 关键帧参数 | void | N/A | 关键帧动画 | AC-3.1 |
| curves.initCurve(curve?: Curve): ICurve | Public | Curve 枚举 | ICurve | N/A | 创建插值曲线 | AC-5.3 |
| curves.stepsCurve(count: number, end: boolean): ICurve | Public | count, end | ICurve | N/A | 创建阶跃曲线 | AC-5.5 |
| curves.cubicBezierCurve(x1, y1, x2, y2): ICurve | Public | x1,y1,x2,y2 | ICurve | N/A | 创建三阶贝塞尔曲线 | AC-5.2 |
| curves.customCurve(interpolate: (fraction: number) => number): ICurve | Public | 自定义回调 | ICurve | N/A | 创建自定义曲线 | AC-5.6 |
| curves.springCurve(velocity, mass, stiffness, damping): ICurve | Public | velocity,mass,stiffness,damping | ICurve | N/A | 创建弹簧曲线 | AC-5.3 |
| AnimateParam 接口 | Public | duration/tempo/curve/delay/iterations/playMode/onFinish/finishCallbackType/expectedFrameRateRange | — | N/A | 统一动画参数 | AC-1.1 |
| FinishCallbackType 枚举 (REMOVED/LOGICALLY) | Public | — | — | N/A | 完成回调类型 | AC-1.6 |
| PlayMode 枚举 (Normal/Reverse/Alternate/AlternateReverse) | Public | — | — | N/A | 播放模式 | AC-1.1 |
| FillMode 枚举 (None/Forwards/Backwards/Both) | Public | — | — | N/A | 填充模式 | AC-1.1 |
| ICurve 接口 (interpolate(fraction): number) | Public | fraction∈[0,1] | number | N/A | 可采样曲线接口 | AC-5.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| animateTo (全局函数) | 废弃 | API 7~17 显式动画 | @deprecated since 18，@useinstead UIContext.animateTo | AC-1.2 |
| curves.init (返回 string) | 废弃 | API 7~8 初始化曲线 | @deprecated since 9，@useinstead curves.initCurve | AC-5.3 |
| curves.steps (返回 string) | 废弃 | API 7~8 阶跃曲线 | @deprecated since 9，@useinstead curves.stepsCurve | AC-5.3 |
| curves.cubicBezier (返回 string) | 废弃 | API 7~8 贝塞尔曲线 | @deprecated since 9，@useinstead curves.cubicBezierCurve | AC-5.3 |
| curves.spring (返回 string) | 废弃 | API 7~8 弹簧曲线 | @deprecated since 9，@useinstead curves.springCurve | AC-5.3 |
| duration 上限 | MODIFIED | API 26 前后 duration 上限变更 | API<26 钳为 1000ms，API≥26 钳为 2000ms | AC-1.3 |

## 接口规格

### 接口定义

**animateTo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `declare function animateTo(value: AnimateParam, event: () => void): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | AnimateParam | 是 | — | 含 duration/tempo/curve/delay/iterations/playMode/onFinish/finishCallbackType |
| event | () => void | 是 | — | 闭包内属性变化触发动画 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 闭包内属性变化插入动画 | AC-1.1 |
| 2 | duration 超上限 | 钳为 1000ms(API<26) 或 2000ms(API≥26) | AC-1.3 |
| 3 | tempo=0 | 无动画 | AC-1.4 |
| 4 | tempo=+∞ | 当前帧完成 | AC-1.4 |
| 5 | iterations=-1 | 无限循环 | AC-1.5 |
| 6 | finishCallbackType=LOGICALLY | 逻辑衰减态即回调 | AC-1.6 |
| 7 | API 18+ 调用 | 标记 @deprecated，建议 UIContext.animateTo | AC-1.2 |

**curves.cubicBezierCurve**

| 属性 | 值 |
|------|-----|
| 函数签名 | `function cubicBezierCurve(x1: number, y1: number, x2: number, y2: number): ICurve` |
| 返回值 | `ICurve` — 三阶贝塞尔曲线对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| x1 | number | 是 | 无 | [0, 1]，<0→0，>1→1 |
| y1 | number | 是 | 无 | (-∞, +∞) |
| x2 | number | 是 | 无 | [0, 1]，<0→0，>1→1 |
| y2 | number | 是 | 无 | (-∞, +∞) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 创建 CubicCurve，MoveInternal 解 Bx(m)=time 返回 By(m) | AC-5.2 |
| 2 | x1<0 | 钳为 0 | AC-5.2 |
| 3 | x1>1 | 钳为 1 | AC-5.2 |

**curves.customCurve**

| 属性 | 值 |
|------|-----|
| 函数签名 | `function customCurve(interpolate: (fraction: number) => number): ICurve` |
| 返回值 | `ICurve` — 自定义曲线对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| interpolate | (fraction: number) => number | 是 | 无 | fraction∈[0,1]，返回∈[0,1] |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 创建 CustomCurve，MoveInternal 调用 interpolate 回调 | AC-5.6 |
| 2 | 回调为 null | MoveInternal 返回 1.0 | AC-5.6 |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - animateTo @deprecated since 18 → UIContext.animateTo（AC-1.2）
  - curves.init/steps/cubicBezier/spring @deprecated since 9 → ICurve 版本（AC-5.3）
  - duration 上限 API 26 变更：1000ms → 2000ms（AC-1.3）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（animateTo / .animation() / AnimateParam / PlayMode / FillMode / Curve 枚举）
- **API 版本号策略:** animateTo @since 7 @deprecated 18, animateToImmediately @since 12, keyframeAnimateTo @since 11, UIContext.animateTo @since 18, ICurve @since 9, customCurve @since 10, finishCallbackType @since 11, expectedFrameRateRange @since 11

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 统一参数模型 | animateTo / animateToImmediately / keyframeAnimateTo / .animation() 均使用 AnimateParam → AnimationOption | AC-1.1, AC-2.1, AC-3.1, AC-4.1 |
| 三类型曲线解析 | AnimateParam.curve 支持 Curve \| string \| ICurve → RefPtr<Curve> | AC-5.1 ~ AC-5.3 |
| 求值管线 | CurveAnimation<T>::Calculate → evaluator_->Evaluate(begin, end, curve->Move(time)) → NotifyListener | AC-6.1, AC-6.2 |
| Scheduler 驱动 | Interpolator::OnTimestampChanged → OnNormalizedTimestampChanged，由 Scheduler vsync 驱动 | AC-6.1 |
| AnimationInterface 标记 | AnimationOption 通过 AnimationInterface 枚举标记动画来源 | AC-7.1, AC-7.2 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | CurveAnimation / AnimationOption 对象在动画结束后释放 | UT | 对象生命周期单测 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | AnimateParam 参数非法时不崩溃（duration<0 钳为 0，tempo<0 钳为 0） | UT | 异常输入单测 |
| 问题定位 | hilog 标签覆盖关键路径（normalized 超范围 LOGE，curve 为空 LOGW） | 代码审查 | `curve_animation.h:116, 35-36` |
| 自动化维测 | AnimationInterface 枚举标记动画来源，支持 metrics/tracing 追踪 | 代码审查 | `animation_option.h:182-186` |

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
| 无障碍 | 否 | 动画接口为引擎内部能力，无直接无障碍接口 | — |
| 大字体 | 否 | 动画接口无字体相关属性 | — |
| 深色模式 | 否 | 动画接口无颜色/主题属性（Color 插值在 gamma 线性空间，与主题无关） | — |
| 多窗口/分屏 | 否 | 动画接口无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | animateTo @deprecated since 18 → UIContext.animateTo；string 曲线工厂 @deprecated since 9 → ICurve；duration 上限 API 26 变更 | AC-1.2, AC-5.3, AC-1.3 |
| 生态兼容 | 是 | .animation() 不可在 attributeModifier 中调用，需在 SDK 文档明确 | AC-4.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 动画接口
  作为应用开发者
  我想要使用 animateTo / .animation() 等接口创建动画
  以便以命令式或声明式方式控制 UI 过渡效果

  Scenario: animateTo 基本调用
    Given 组件 width=100
    When 调用 animateTo({duration: 1000, curve: Curve.EaseInOut}, () => { width = 200 })
    Then 在 1000ms 内以 EaseInOut 曲线从 100 过渡到 200

  Scenario: duration 超上限钳位
    Given 调用 animateTo({duration: 5000, curve: Curve.Linear}, event)
    When 运行在 API < 26
    Then duration 钳为 1000ms
    When 运行在 API >= 26
    Then duration 钳为 2000ms

  Scenario: tempo 边界值
    Given 调用 animateTo({duration: 1000, tempo: <tempo>, curve: Curve.Linear}, event)
    When tempo = 0
    Then 无动画，属性直接跳变
    When tempo = +∞
    Then 当前帧完成，立即执行 onFinish

  Scenario: iterations 无限循环
    Given 调用 animateTo({duration: 1000, iterations: -1, curve: Curve.Linear}, event)
    When 动画运行
    Then 无限循环播放

  Scenario: finishCallbackType LOGICALLY
    Given 调用 animateTo({duration: 1000, curve: springMotion(), finishCallbackType: FinishCallbackType.LOGICALLY}, event)
    When 动画逻辑进入衰减态
    Then onFinish 回调触发（可能仍有长尾状态）

  Scenario: 曲线 string 形式解析
    Given 设置 AnimateParam.curve = "cubic-bezier(0.42, 0.0, 0.58, 1.0)"
    When 解析曲线
    Then 创建 CubicCurve，P1=(0.42, 0.0), P2=(0.58, 1.0)
    And MoveInternal 解 Bx(m)=time 返回 By(m)

  Scenario: string 曲线工厂废弃迁移
    Given 使用 curves.init() (返回 string)
    When API >= 9
    Then 标记 @deprecated
    And 建议使用 curves.initCurve() (返回 ICurve)

  Scenario: Color gamma 插值
    Given 属性类型为 Color，begin=Red, end=Blue
    When curve->Move(time) 返回 fraction=0.5
    Then LinearEvaluator<Color> 在 gamma 线性空间插值
    And GAMMA_FACTOR=2.2

  Scenario: normalized 超范围
    Given CurveAnimation OnNormalizedTimestampChanged 被调用
    When normalized < 0 或 normalized > 1
    Then 输出 LOGE
    And 不更新 currentValue

  Scenario: AnimationInterface 来源标记
    Given 通过 animateTo 创建动画
    When AnimationOption 构造
    Then animationInterface_ = ANIMATE_TO
    And GetAnimationInterfaceString() 返回 "animateTo"

  Scenario Outline: PlayMode 行为
    Given 调用 animateTo({duration: 1000, iterations: <iterations>, playMode: <mode>}, event)
    When 动画播放
    Then <behavior>

    Examples:
      | mode | iterations | behavior |
      | Normal | 1 | 单次正向播放 |
      | Alternate | 3 | 正→反→正 |
      | Reverse | 1 | 反向播放（跳到终态再播放） |
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
    query: "AnimationOption 统一参数模型和 AnimationInterface 枚举标记"
  - repo: "openharmony/ace_engine"
    query: "CurveAnimation<T> Calculate 求值管线和 Evaluator 模式"
  - repo: "openharmony/ace_engine"
    query: "CubicCurve MoveInternal 贝塞尔求解算法 cubicErrorBound"
  - repo: "openharmony/ace_engine"
    query: "Curves 静态工厂单例 EASE LINEAR FAST_OUT_SLOW_IN"
  - repo: "openharmony/ace_engine"
    query: "Interpolator OnTimestampChanged OnNormalizedTimestampChanged RunAsync"
  - repo: "openharmony/ace_engine"
    query: "LinearEvaluator<Color> gamma 线性空间插值 GAMMA_FACTOR=2.2"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts` / `enums.d.ts` / `@ohos.curves.d.ts`
- 源码入口: `frameworks/core/animation/curve_animation.h` / `evaluator.h` / `interpolator.h`
- InnerAPI: `interfaces/inner_api/ace_kit/include/ui/animation/animation_option.h` / `curve.h` / `cubic_curve.h`
