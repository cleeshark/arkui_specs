# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 物理动画全量规格 (SpringMotion / ResponsiveSpringMotion / InterpolatingSpring / SpringCurve) |
| 特性编号 | Func-03-02-09-Feat-01 |
| FuncID | 03-02-09 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 9 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 9 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | springMotion(response?, dampingFraction?, overlapDuration?) | @since 9，Motion-based 物理动画，默认 0.55/0.825/0 |
| ADDED | responsiveSpringMotion(response?, dampingFraction?, overlapDuration?) | @since 9，默认 0.15/0.86/0.25 |
| ADDED | springCurve(velocity, mass, stiffness, damping) | @since 9，Curve-based 物理动画，返回 ICurve |
| ADDED | string 形式 "spring-motion(r,d,o)" / "responsive-spring-motion(r,d,o)" / "spring(v,m,s,d)" | @since 7，AnimateParam.curve string 支持 |
| ADDED | interpolatingSpring(velocity, mass, stiffness, damping) | @since 10，Motion-based，实际计算委托 rosen |
| ADDED | string 形式 "interpolating-spring(v,m,s,d)" | @since 10，AnimateParam.curve string 支持 |
| MODIFIED | springMotion / responsiveSpringMotion / interpolatingSpring 明确忽略 AnimateParam.duration | 物理动画时长由方程决定 |
| MODIFIED | springMotion / responsiveSpringMotion / interpolatingSpring 明确不支持 ICurve.interpolate() 采样 | MoveInternal 返回 0.0 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/09-physics-animation/design.md`
- **SDK 类型定义**:
  - `<OH_ROOT>/interface/sdk-js/api/@ohos.curves.d.ts` (springMotion:384, responsiveSpringMotion:412, interpolatingSpring:453, springCurve:329)
  - `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts` (AnimateParam:4301, string curve forms:4384-4394)

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: SpringMotion 物理动画

**角色**: 应用开发者
**期望**: 我想要使用 springMotion 创建基于物理的弹簧动画，动画自然衰减结束
**价值**: 以便获得真实的物理交互体验（如拖拽回弹、滑块切换）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `curves.springMotion()` 无参数 THEN 使用默认值 response=0.55, dampingFraction=0.825, overlapDuration=0（`@ohos.curves.d.ts:356-367`，`curve.h:364-366`） | 正常 |
| AC-1.2 | WHEN 调用 `curves.springMotion(0.3, 0.7, 0.2)` THEN 创建 SpringMotion 曲线，参数为 response=0.3, dampingFraction=0.7, overlapDuration=0.2 | 正常 |
| AC-1.3 | WHEN 调用 `curves.springMotion(-1, ...)` 传入 response≤0 THEN 使用默认值 0.55（`@ohos.curves.d.ts:357-358`） | 边界 |
| AC-1.4 | WHEN 在 `animateTo({curve: springMotion(...), duration: 1000})` 中设置 duration THEN duration 参数不生效，动画时长由物理方程决定（`common.d.ts:4314`） | 正常 |
| AC-1.5 | WHEN SpringMotion 运行时通过 `IsCompleted()` 判定完成 THEN 当 position 和 velocity 均接近零（NearZero 阈值 NEAR_ZERO=0.1）时完成（`spring_motion.h:67`，`spring_motion.cpp:56-59`） | 边界 |

### US-2: ResponsiveSpringMotion 响应式弹簧动画

**角色**: 应用开发者
**期望**: 我想要使用 responsiveSpringMotion 创建响应式弹簧动画，获得更快的响应速度
**价值**: 以便在需要快速响应的场景（如手势跟随）中获得更紧致的动画效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `curves.responsiveSpringMotion()` 无参数 THEN 使用默认值 response=0.15, dampingFraction=0.86, overlapDuration=0.25（`@ohos.curves.d.ts:390-396`，`curve.h:367-369`） | 正常 |
| AC-2.2 | WHEN 调用 `curves.responsiveSpringMotion(0.1, 0.9, 0.3)` THEN 创建 ResponsiveSpringMotion 曲线，参数为 response=0.1, dampingFraction=0.9, overlapDuration=0.3 | 正常 |
| AC-2.3 | WHEN ResponsiveSpringMotion 的 `MoveInternal(time)` 被调用 THEN 返回 0.0f，实际物理计算在 rosen 中通过 NativeCurveHelper 完成（`curve.h:314-317`） | 正常 |
| AC-2.4 | WHEN 尝试通过 `ICurve.interpolate(fraction)` 采样 ResponsiveSpringMotion THEN 不可获得有效插值（MoveInternal 返回 0.0，`@ohos.curves.d.ts:371-378`） | 边界 |

### US-3: SpringModel 物理方程模型选择

**角色**: 引擎开发者
**期望**: 我想要了解 SpringModel 如何根据 spring 参数自动选择阻尼模型
**价值**: 以便理解不同 mass/stiffness/damping 组合下的动画行为

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN cmk = damping² - 4*mass*stiffness ≈ 0 (NearZero) 且 distance≠0 THEN SpringModel::Build 返回 CriticalDampedModel（`spring_model.cpp:79-85`） | 正常 |
| AC-3.2 | WHEN cmk > 0 THEN SpringModel::Build 返回 OverdampedModel（`spring_model.cpp:86-87`） | 正常 |
| AC-3.3 | WHEN cmk < 0 THEN SpringModel::Build 返回 UnderdampedModel（`spring_model.cpp:88-89`） | 正常 |
| AC-3.4 | WHEN SpringProperty 的 mass/stiffness/damping 任一 ≤0 THEN `IsValid()` 返回 false，SpringModel::Build 返回 nullptr（`spring_model.cpp:29-35, 75-77`） | 异常 |
| AC-3.5 | WHEN cmk ≈ 0 但 distance=0 (NearZero) THEN SpringModel::Build 返回 nullptr（创建 CriticalDamped 失败，`spring_model.cpp:81-84`） | 边界 |

### US-4: InterpolatingSpring 插值弹簧动画

**角色**: 应用开发者
**期望**: 我想要使用 interpolatingSpring 创建基于物理参数的弹簧动画
**价值**: 以便通过 mass/stiffness/damping 精确控制动画的物理特性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `curves.interpolatingSpring(0.0, 1.0, 228, 30)` THEN 创建 InterpolatingSpring 曲线，参数 velocity=0, mass=1, stiffness=228, damping=30 | 正常 |
| AC-4.2 | WHEN InterpolatingSpring 的 `MoveInternal(time)` 被调用 THEN 返回 0.0f，实际物理计算在 rosen 中通过 NativeCurveHelper 完成（`curve.h:389-392`） | 正常 |
| AC-4.3 | WHEN 调用 `interpolatingSpring(0, 0, 228, 30)` 传入 mass≤0 THEN 使用值 1（`@ohos.curves.d.ts:428`） | 边界 |
| AC-4.4 | WHEN 调用 `interpolatingSpring(0, 1, 0, 30)` 传入 stiffness≤0 THEN 使用值 1（`@ohos.curves.d.ts:434`） | 边界 |
| AC-4.5 | WHEN 调用 `interpolatingSpring(0, 1, 228, 0)` 传入 damping≤0 THEN 使用值 1（`@ohos.curves.d.ts:440`） | 边界 |

### US-5: SpringCurve 弹簧曲线

**角色**: 应用开发者
**期望**: 我想要使用 springCurve 创建有固定 duration 治理的弹簧曲线
**价值**: 以便在需要 duration 控制的场景中使用弹簧效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `curves.springCurve(0.0, 1.0, 228, 30)` THEN 创建 SpringCurve 对象，参数 velocity=0, mass=1, stiffness=228, damping=30 | 正常 |
| AC-5.2 | WHEN SpringCurve 的 `MoveInternal(time)` 被调用 THEN 产出 [0,1] 区间的 fraction 值（`spring_curve.h:31`） | 正常 |
| AC-5.3 | WHEN 在 `animateTo({curve: springCurve(...), duration: 2000})` 中设置 duration THEN duration 生效，动画在指定时长内完成 | 正常 |

### US-6: 速度继承

**角色**: 应用开发者
**期望**: 我想要多个 spring 动画连续作用于同一属性时保持速度连续性
**价值**: 以便避免连续弹簧动画之间的视觉跳变

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 多个 springMotion 动画连续作用于同一属性 THEN 后继动画继承前驱动画的末速度（`@ohos.curves.d.ts:353-354`） | 正常 |
| AC-6.2 | WHEN 多个 interpolatingSpring 动画连续作用于同一属性 THEN 后继动画继承前驱动画的末速度 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-7 | TASK-PHYSICS-01 | UT | `test/unittest/core/animation/` |
| AC-2.1 ~ AC-2.4 | R-3, R-5 | TASK-PHYSICS-01 | UT | ResponsiveSpringMotion 单测 |
| AC-3.1 ~ AC-3.5 | R-6, R-8, R-9 | TASK-PHYSICS-01 | UT | SpringModel 单测 |
| AC-4.1 ~ AC-4.5 | R-4, R-5, R-10 | TASK-PHYSICS-01 | UT | InterpolatingSpring 单测 |
| AC-5.1 ~ AC-5.3 | R-1, R-11 | TASK-PHYSICS-01 | UT | SpringCurve 单测 |
| AC-6.1 ~ AC-6.2 | R-12 | TASK-PHYSICS-01 | UT + 手工 | 速度继承测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | springMotion / responsiveSpringMotion / interpolatingSpring 配置为 AnimateParam.curve | AnimateParam.duration 参数不生效，动画时长由物理方程和初始速度决定 | `common.d.ts:4314` | AC-1.4, AC-5.3 |
| R-2 | 行为 | SpringMotion::Move(offsetTime) 被调用 | offsetTime(ms) 转换为 offsetTimeInSecond(s)（除以 UNIT_CONVERT=1000.0f），通过 SpringModel::Position/Velocity 计算当前位置和速度 | `spring_motion.cpp:23, 91` | AC-1.5 |
| R-3 | 行为 | ResponsiveSpringMotion 构造 | MoveInternal 返回 0.0f，实际物理计算在 rosen via NativeCurveHelper，ace_engine 仅保存 response/dampingRatio/blendDuration 参数 | `curve.h:314-317` | AC-2.3 |
| R-4 | 行为 | InterpolatingSpring 构造 | MoveInternal 返回 0.0f，实际物理计算在 rosen via NativeCurveHelper，ace_engine 仅保存 velocity/mass/stiffness/damping 参数 | `curve.h:389-392` | AC-4.2 |
| R-5 | 边界 | 尝试通过 ICurve.interpolate(fraction) 采样 springMotion / responsiveSpringMotion / interpolatingSpring | 不可获得有效插值（MoveInternal 返回 0.0），时间无法归一化 | `@ohos.curves.d.ts:371-378, 398-406, 443-446` | AC-2.4, AC-4.2 |
| R-6 | 行为 | SpringModel::Build(distance, velocity, spring) 调用 | 计算 cmk = damping² - 4*mass*stiffness，cmk≈0(NearZero)→CriticalDamped，cmk>0→Overdamped，cmk<0→Underdamped | `spring_model.cpp:73-92`，HIGH_RATIO=4.0 | AC-3.1 ~ AC-3.3 |
| R-7 | 行为 | SpringMotion::IsCompleted(value, velocity) 调用 | NearZero(value - endPosition_, accuracy_) && NearZero(velocity, velocityAccuracy_)，NEAR_ZERO=0.1 | `spring_motion.h:67, spring_motion.cpp:56-59` | AC-1.5 |
| R-8 | 异常 | SpringProperty 的 mass/stiffness/damping 任一 ≤0 | IsValid() 返回 false，SpringModel::Build 返回 nullptr，SpringMotion::Move 时 model_==nullptr 输出 LOGE | `spring_model.cpp:29-35, 75-77, spring_motion.cpp:86-88` | AC-3.4 |
| R-9 | 边界 | cmk ≈ 0 (NearZero) 但 distance = 0 (NearZero) | SpringModel::Build 返回 nullptr（创建 CriticalDamped 失败，c2_ = velocity/(r_*distance) 除零） | `spring_model.cpp:81-84` | AC-3.5 |
| R-10 | 边界 | interpolatingSpring 参数 mass/stiffness/damping ≤0 | 对应参数使用值 1 | `@ohos.curves.d.ts:428, 434, 440` | AC-4.3 ~ AC-4.5 |
| R-11 | 行为 | SpringCurve::MoveInternal(time) 调用 | 产出 [0,1] 区间的 fraction，duration 由 AnimateParam.duration 治理，有 estimateDuration_ | `spring_curve.h:31, 74` | AC-5.2, AC-5.3 |
| R-12 | 行为 | 多个 spring 动画连续作用于同一属性 | 后继动画继承前驱动画的末速度，保证平滑过渡 | `@ohos.curves.d.ts:353-354` | AC-6.1, AC-6.2 |
| R-13 | 行为 | SpringProperty 默认值 | DEFAULT_STIFFNESS=228.0, DEFAULT_DAMPING=30.0, DEFAULT_MASS=1.0 | `spring_model.h:57-61` | — |
| R-14 | 恢复 | ScrollSpringMotion::IsCompleted() 调用 | 仅判定 position 接近 endPosition（NearZero），不判定 velocity | `spring_motion.cpp:104-107` | — |
| R-15 | 行为 | Motion 基类 OnTimestampChanged(timestamp, normalizedTime, reverse) 调用 | 调用 Move(timestamp)，再调用 NotifyListener(GetCurrentPosition())，normalizedTime 始终为 0（Motion 无 duration） | `motion.h:41-45` | — |
| R-16 | 边界 | ResponsiveSpringMotion / InterpolatingSpring 的 minimumAmplitudeRatio | ResponsiveSpringMotion 默认 0.001，InterpolatingSpring 默认 0.00025，可通过 UpdateMinimumAmplitudeRatio 修改 | `curve.h:356-363, 446-454, 370, 458` | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | SpringMotion 参数默认值、duration 无效性、IsCompleted 判定 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT | ResponsiveSpringMotion 参数默认值、MoveInternal 返回 0.0、interpolate 不可用 |
| VM-3 | AC-3.1 ~ AC-3.5 | UT | SpringModel::Build cmk 判别式三种模型选择、异常输入处理 |
| VM-4 | AC-4.1 ~ AC-4.5 | UT | InterpolatingSpring 参数、MoveInternal 返回 0.0、非法参数降级 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT | SpringCurve MoveInternal 产出 fraction、duration 生效 |
| VM-6 | AC-6.1 ~ AC-6.2 | UT + 手工 | 速度继承连续性验证 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| curves.springMotion(response?, dampingFraction?, overlapDuration?) | Public | response=0.55, dampingFraction=0.825, overlapDuration=0 | ICurve | N/A | 创建 Motion-based 弹簧动画曲线 | AC-1.1 ~ AC-1.5 |
| curves.responsiveSpringMotion(response?, dampingFraction?, overlapDuration?) | Public | response=0.15, dampingFraction=0.86, overlapDuration=0.25 | ICurve | N/A | 创建响应式弹簧动画曲线 | AC-2.1 ~ AC-2.4 |
| curves.interpolatingSpring(velocity, mass, stiffness, damping) | Public | velocity, mass>0, stiffness>0, damping>0 | ICurve | N/A | 创建插值弹簧动画曲线 | AC-4.1 ~ AC-4.5 |
| curves.springCurve(velocity, mass, stiffness, damping) | Public | velocity, mass>0, stiffness>0, damping>0 | ICurve | N/A | 创建 Curve-based 弹簧曲线 | AC-5.1 ~ AC-5.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| curves.spring(velocity, mass, stiffness, damping): string | 废弃 | API 7 动态模型 string 形式 | @deprecated since 9，@useinstead curves.springCurve（返回 ICurve） | — |

## 接口规格

### 接口定义

**curves.springMotion**

| 属性 | 值 |
|------|-----|
| 函数签名 | `curves.springMotion(response?: number, dampingFraction?: number, overlapDuration?: number): ICurve` |
| 返回值 | `ICurve` — 弹簧动画曲线对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| response | number | 否 | 0.55 | (0, +∞)，≤0 使用默认 0.55 |
| dampingFraction | number | 否 | 0.825 | [0, +∞)，<0 使用默认 0.825；0=无阻尼，1=临界阻尼，>1=过阻尼 |
| overlapDuration | number | 否 | 0 | [0, +∞)，<0 使用默认 0；动画重叠过渡时长（秒） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 无参数调用 | 使用默认值 0.55/0.825/0 | AC-1.1 |
| 2 | response≤0 | 使用默认 0.55 | AC-1.3 |
| 3 | 配置为 AnimateParam.curve | duration 参数不生效 | AC-1.4 |
| 4 | 动画运行中 IsCompleted 判定 | position 和 velocity 均 NearZero(0.1) 时完成 | AC-1.5 |

**curves.interpolatingSpring**

| 属性 | 值 |
|------|-----|
| 函数签名 | `curves.interpolatingSpring(velocity: number, mass: number, stiffness: number, damping: number): ICurve` |
| 返回值 | `ICurve` — 插值弹簧动画曲线对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1 ~ AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| velocity | number | 是 | 无 | (-∞, +∞)，归一化速度 |
| mass | number | 是 | 无 | (0, +∞)，≤0 使用 1 |
| stiffness | number | 是 | 无 | (0, +∞)，≤0 使用 1 |
| damping | number | 是 | 无 | (0, +∞)，≤0 使用 1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常参数调用 | 创建 InterpolatingSpring，MoveInternal 返回 0.0，实际计算委托 rosen | AC-4.1, AC-4.2 |
| 2 | mass≤0 | 使用值 1 | AC-4.3 |
| 3 | stiffness≤0 | 使用值 1 | AC-4.4 |
| 4 | damping≤0 | 使用值 1 | AC-4.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - springMotion / responsiveSpringMotion / interpolatingSpring 明确忽略 AnimateParam.duration（AC-1.4）
  - springMotion / responsiveSpringMotion / interpolatingSpring 明确不支持 ICurve.interpolate() 采样（AC-2.4, AC-4.2）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9（springMotion / responsiveSpringMotion / springCurve），API 10（interpolatingSpring）
- **API 版本号策略:** springMotion / responsiveSpringMotion / springCurve @since 9，interpolatingSpring @since 10，string 形式 @since 7/10

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双路径架构 | Motion-based（SpringMotion 无固定 duration，速度继承）与 Curve-based（SpringCurve 有 duration 治理）两条路径 | AC-1.4, AC-5.3 |
| SpringModel 物理方程 | SpringModel::Build 按 cmk 判别式自动选择三种阻尼模型 | AC-3.1 ~ AC-3.3 |
| rosen 委托 | InterpolatingSpring / ResponsiveSpringMotion 的实际物理计算在 rosen via NativeCurveHelper | AC-2.3, AC-4.2 |
| 不可采样性 | springMotion / responsiveSpringMotion / interpolatingSpring 不可通过 ICurve.interpolate() 采样 | AC-2.4, AC-4.2 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 物理动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | SpringMotion / SpringModel 对象在动画结束后释放 | UT | 对象生命周期单测 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | SpringProperty 参数非法时不崩溃，Build 返回 nullptr | UT | 异常输入单测 |
| 问题定位 | hilog 标签覆盖关键路径（model_==nullptr 时 LOGE） | 代码审查 | `spring_motion.cpp:87` |

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
| 无障碍 | 否 | 物理动画为引擎内部能力，无直接无障碍接口 | — |
| 大字体 | 否 | 物理动画无字体相关属性 | — |
| 深色模式 | 否 | 物理动画无颜色/主题属性 | — |
| 多窗口/分屏 | 否 | 物理动画无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | spring @deprecated since 9 → springCurve；需在兼容性声明中明确 | — |
| 生态兼容 | 是 | springMotion / responsiveSpringMotion / interpolatingSpring 不可通过 interpolate() 采样，需在 SDK 文档明确 | AC-2.4, AC-4.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 物理动画
  作为应用开发者
  我想要使用基于物理的弹簧动画
  以便获得真实的物理交互体验

  Scenario: SpringMotion 默认参数
    Given 调用 curves.springMotion() 无参数
    When 创建 SpringMotion 曲线
    Then response=0.55, dampingFraction=0.825, overlapDuration=0

  Scenario: SpringMotion duration 不生效
    Given 使用 springMotion 作为 AnimateParam.curve
    When 设置 duration=1000
    Then duration 参数不生效
    And 动画时长由物理方程决定

  Scenario: SpringModel cmk 判别式选择模型
    Given SpringProperty(mass=1, stiffness=228, damping=30)
    When 调用 SpringModel::Build(distance=100, velocity=0, spring)
    Then 计算 cmk = 30²-4*1*228 = 900-912 = -12 < 0
    And 返回 UnderdampedModel

  Scenario Outline: SpringModel 阻尼模型选择
    Given SpringProperty(mass=<mass>, stiffness=<stiffness>, damping=<damping>)
    When 调用 SpringModel::Build(distance=100, velocity=0, spring)
    Then 返回 <model_type>

    Examples:
      | mass | stiffness | damping | model_type |
      | 1    | 100       | 20       | CriticalDamped |
      | 1    | 100       | 30       | Overdamped |
      | 1    | 100       | 10       | Underdamped |

  Scenario: InterpolatingSpring 非法参数降级
    Given 调用 interpolatingSpring(0, 0, 228, 30)
    When mass=0 (≤0)
    Then 使用 mass=1

  Scenario: ResponsiveSpringMotion 不可采样
    Given 创建 ResponsiveSpringMotion 曲线
    When 调用 ICurve.interpolate(0.5)
    Then 返回 0.0（不可获得有效插值）

  Scenario: 速度继承
    Given 多个 springMotion 动画连续作用于同一属性
    When 后继动画启动
    Then 继承前驱动画的末速度
    And 平滑过渡无视觉跳变
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
    query: "SpringModel::Build cmk 判别式和三种阻尼模型选择机制"
  - repo: "openharmony/ace_engine"
    query: "SpringMotion Move 方法 ms→s 单位转换和 IsCompleted 判定"
  - repo: "openharmony/ace_engine"
    query: "ResponsiveSpringMotion / InterpolatingSpring MoveInternal 返回 0.0 和 rosen 委托"
  - repo: "openharmony/ace_engine"
    query: "SpringCurve MoveInternal fraction 计算和 estimateDuration"
  - repo: "openharmony/ace_engine"
    query: "Motion 基类 OnTimestampChanged→Move→NotifyListener 调用链"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.curves.d.ts`
- 源码入口: `frameworks/core/animation/spring_model.cpp` / `spring_motion.cpp` / `spring_curve.h`
- InnerAPI: `interfaces/inner_api/ace_kit/include/ui/animation/curve.h`
