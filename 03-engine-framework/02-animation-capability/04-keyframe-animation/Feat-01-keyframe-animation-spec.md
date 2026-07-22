# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 关键帧动画全量规格 (keyframeAnimateTo 隐式作用域、KeyframeAnimation 链式组装、逐帧曲线) |
| 特性编号 | Func-03-02-04-Feat-01 |
| FuncID | 03-02-04 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 11 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 11 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `UIContext.keyframeAnimateTo(param, keyframes)` | @since 11，动态 API |
| ADDED | `KeyframeAnimateParam` 接口（delay/iterations/onFinish） | @since 11 |
| ADDED | `KeyframeState` 接口（duration/curve/event） | @since 11 |
| MODIFIED | `KeyframeAnimateParam.expectedFrameRateRange` 新增 | @since 19，ExpectedFrameRateRange |
| MODIFIED | Form 场景 duration 限制 FORM_MAX_DURATION | @since 26，API 26+ 使用 FORM_MAX_DURATION |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/04-keyframe-animation/design.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`（keyframeAnimateTo）
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`（KeyframeAnimateParam / KeyframeState）
  - Static: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.static.d.ets`（静态 keyframeAnimateTo）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础关键帧动画

**角色**: 应用开发者
**期望**: 我想要通过 keyframeAnimateTo 定义多个关键帧状态，每个状态指定时长和曲线
**价值**: 以便实现复杂的多阶段动画，每个阶段使用不同的插值曲线

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `keyframeAnimateTo({ delay: 0, iterations: 1 }, [{ duration: 1000, curve: Curve.EaseIn, event: () => { ... } }])` THEN 打开隐式动画作用域，执行唯一关键帧的 event 闭包，1000ms 后触发 onFinish | 正常 |
| AC-1.2 | WHEN 调用 keyframeAnimateTo 传入多个 KeyframeState THEN 各帧按数组顺序串行执行，每帧执行完毕后进入下一帧 | 正常 |
| AC-1.3 | WHEN `info.Length() < 2` 或 `info[0]` 非对象或 `info[1]` 非数组 THEN 直接 return，不触发任何动画（`js_view_context.cpp:878-886`） | 异常 |
| AC-1.4 | WHEN `info[1]` 为空数组 THEN 直接 return，不触发任何动画（`js_view_context.cpp:888-890`） | 异常 |

### US-2: 逐帧曲线与总时长

**角色**: 应用开发者
**期望**: 我想要为每个关键帧指定独立的动画曲线
**价值**: 以便在不同阶段使用不同的加速/减速曲线

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN KeyframeState.curve 未设置 THEN 该帧使用默认曲线 Curve.EaseInOut（SDK common.d.ts:30045-30052） | 正常 |
| AC-2.2 | WHEN 设置多个 KeyframeState 的 duration THEN 总时长 = Σ 各帧 duration（`js_view_context.cpp:906-908`） | 正常 |
| AC-2.3 | WHEN overallAnimationOption.SetCurve 被调用 THEN 强制设为 Curves::EASE_IN_OUT，用户不可覆盖（`js_view_context.cpp:911`） | 边界 |

### US-3: 弹簧曲线排除

**角色**: 应用开发者
**期望**: 我想要了解哪些曲线不支持关键帧动画
**价值**: 以便避免在不支持的场景下使用弹簧曲线

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN KeyframeState.curve 为 springMotion THEN 降级为 EASE_IN_OUT，不报错（`js_view_context.cpp:430` ParseCurve exceptSpring=true） | 异常 |
| AC-3.2 | WHEN KeyframeState.curve 为 responsiveSpringMotion THEN 降级为 EASE_IN_OUT | 异常 |
| AC-3.3 | WHEN KeyframeState.curve 为 interpolatingSpring THEN 降级为 EASE_IN_OUT，SDK 文档 common.d.ts:30040-30043 明确标注不支持 | 异常 |

### US-4: KeyframeAnimation 模板行为

**角色**: 框架开发者
**期望**: 我想要了解 KeyframeAnimation<T> 的内部插值算法
**价值**: 以便正确实现自定义类型的动画

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN KeyframeAnimation::Calculate 的 keyTime < 0 THEN currentValue_ = 首帧 keyValue（`keyframe_animation.h:148-150`） | 边界 |
| AC-4.2 | WHEN keyTime > 1.0 或 keyframeNum_ == 1 THEN currentValue_ = 末帧 keyValue（`keyframe_animation.h:151-154`） | 边界 |
| AC-4.3 | WHEN keyTime 在 [0, 1] 区间 THEN 使用 `evaluator_->Evaluate(begin, end, curve->Move(intervalKeyTime))` 插值，curve 为当前帧 curve 或 fallback EASE（`keyframe_animation.h:164-174`） | 正常 |
| AC-4.4 | WHEN RunAsync 被调用 THEN `scheduler->OpenImplicitAnimation(option, Curves::EASE, finishCallback)` 打开隐式作用域，逐帧 `AddKeyFrame(fraction, curve, callback)`（`keyframe_animation.h:111, 120-133`） | 正常 |

### US-5: Color 插值特化

**角色**: 应用开发者
**期望**: 我想要在关键帧动画中实现颜色平滑过渡
**价值**: 以便颜色动画不会有中间色偏暗的问题

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 关键帧动画的目标属性为 Color 类型 THEN 使用 LinearEvaluator<Color> 特化（`evaluator.h:48-105`） | 正常 |
| AC-5.2 | WHEN Color 插值 THEN 先将 ARGB 转 gamma 空间（GAMMA_FACTOR=2.2），线性插值后回 gamma 空间（`evaluator.h:53-73`） | 正常 |
| AC-5.3 | WHEN 关键帧动画的目标属性为 BorderStyle THEN fraction ≥ 0.5 取 end，否则 begin（`evaluator.h:110-116`） | 正常 |

### US-6: expectedFrameRateRange 与 onFinish

**角色**: 应用开发者
**期望**: 我想要控制关键帧动画的帧率和完成回调
**价值**: 以便在功耗敏感场景降低帧率，在动画完成时执行后续逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN KeyframeAnimateParam.expectedFrameRateRange 设置 {min: 30, max: 120, expected: 60} THEN 解析为 FrameRateRange 传入 overallAnimationOption（`js_view_context.cpp:389-398`） | 正常 |
| AC-6.2 | WHEN 动画完成或被打断（UIAbility 后台 / 转场动画禁用）THEN 触发 onFinish 回调（SDK common.d.ts:29967-29969） | 正常 |
| AC-6.3 | WHEN KeyframeAnimateParam.expectedFrameRateRange 未设置 THEN 默认 {min:0, max:0, expected:0}，跟随应用帧率（SDK common.d.ts:29990） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.2 | R-1, R-3 | TASK-KEYFRAME-01 | UT | js_view_context 单测 |
| AC-1.3 ~ AC-1.4 | R-2 | TASK-KEYFRAME-01 | UT | 参数校验单测 |
| AC-2.1 ~ AC-2.3 | R-3, R-4, R-5 | TASK-KEYFRAME-01 | UT | 逐帧曲线和总时长单测 |
| AC-3.1 ~ AC-3.3 | R-6 | TASK-KEYFRAME-01 | UT | 弹簧曲线降级单测 |
| AC-4.1 ~ AC-4.4 | R-7, R-8, R-9 | TASK-KEYFRAME-01 | UT | KeyframeAnimation 模板单测 |
| AC-5.1 ~ AC-5.3 | R-10, R-11 | TASK-KEYFRAME-01 | UT | Evaluator 特化单测 |
| AC-6.1 ~ AC-6.3 | R-12, R-13 | TASK-KEYFRAME-01 | UT + 手工 | expectedFrameRateRange + onFinish |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 keyframeAnimateTo(param, keyframes) | 解析 overallParam 和 keyframes，累加总时长，强制 EASE_IN_OUT，启动隐式作用域 | keyframes 必须非空数组 | AC-1.1, AC-1.2 |
| R-2 | 异常 | info.Length() < 2 或 info[0] 非对象或 info[1] 非数组或空数组 | 直接 return，不触发动画 | `js_view_context.cpp:878-890` | AC-1.3, AC-1.4 |
| R-3 | 行为 | KeyframeState.curve 未设置 | 使用默认曲线 Curve.EaseInOut | SDK common.d.ts:30045 | AC-2.1 |
| R-4 | 行为 | 多帧 keyframeAnimateTo | 总时长 = Σ keyframe.duration，逐帧串行执行 | `js_view_context.cpp:906-908` | AC-2.2 |
| R-5 | 边界 | overallAnimationOption.SetCurve | 强制设为 Curves::EASE_IN_OUT，用户不可覆盖 | `js_view_context.cpp:911` | AC-2.3 |
| R-6 | 异常 | KeyframeState.curve 为 springMotion/responsiveSpringMotion/interpolatingSpring | 降级为 EASE_IN_OUT（ParseCurve exceptSpring=true） | `js_view_context.cpp:430` | AC-3.1, AC-3.2, AC-3.3 |
| R-7 | 边界 | KeyframeAnimation::Calculate keyTime < 0 | currentValue_ = 首帧 keyValue | `keyframe_animation.h:148-150` | AC-4.1 |
| R-8 | 边界 | keyTime > 1.0 或 keyframeNum_ == 1 | currentValue_ = 末帧 keyValue | `keyframe_animation.h:151-154` | AC-4.2 |
| R-9 | 行为 | keyTime 在 [0,1] 区间 | evaluator_->Evaluate(begin, end, curve->Move(intervalKeyTime))，curve 为帧 curve 或 fallback EASE | `keyframe_animation.h:164-174` | AC-4.3 |
| R-10 | 行为 | Color 类型关键帧动画 | 使用 LinearEvaluator<Color> gamma 空间特化 | GAMMA_FACTOR=2.2 | AC-5.1, AC-5.2 |
| R-11 | 行为 | BorderStyle 类型关键帧动画 | fraction ≥ 0.5 取 end，否则 begin | `evaluator.h:110-116` | AC-5.3 |
| R-12 | 行为 | expectedFrameRateRange 设置 | 解析为 FrameRateRange，SetFrameRateRange 到 option | min/max/expected ≥ 0 | AC-6.1 |
| R-13 | 恢复 | UIAbility 后台或转场动画禁用 | 有限次数动画立即停止，触发 onFinish | SDK common.d.ts:29967-29969 | AC-6.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.2 | UT | keyframeAnimateTo 多帧串行执行 |
| VM-2 | AC-1.3 ~ AC-1.4 | UT | 参数非法时安全退出 |
| VM-3 | AC-2.1 ~ AC-2.3 | UT | 逐帧曲线默认值和总时长累加 |
| VM-4 | AC-3.1 ~ AC-3.3 | UT | 弹簧曲线降级为 EASE_IN_OUT |
| VM-5 | AC-4.1 ~ AC-4.4 | UT | KeyframeAnimation Calculate 边界和 RunAsync 流程 |
| VM-6 | AC-5.1 ~ AC-5.3 | UT | Color gamma 插值和 BorderStyle 阶跃 |
| VM-7 | AC-6.1 ~ AC-6.3 | UT + 手工 | expectedFrameRateRange 解析和 onFinish 回调 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| UIContext.keyframeAnimateTo(param, keyframes) | Public | KeyframeAnimateParam, Array<KeyframeState> | void | N/A | 生成关键帧动画 | AC-1.1 |
| KeyframeAnimateParam.delay | Public | number | — | N/A | 整体延迟，默认 0 | AC-1.1 |
| KeyframeAnimateParam.iterations | Public | number | — | N/A | 播放次数，−1 无限 | AC-1.1 |
| KeyframeAnimateParam.onFinish | Public | () => void | — | N/A | 完成回调 | AC-6.2 |
| KeyframeAnimateParam.expectedFrameRateRange | Public | ExpectedFrameRateRange | — | N/A | 期望帧率，@since 19 | AC-6.1 |
| KeyframeState.duration | Public | number | — | N/A | 单帧时长 [0,+∞) | AC-2.2 |
| KeyframeState.curve | Public | Curve/string/ICurve | — | N/A | 单帧曲线，默认 EaseInOut | AC-2.1 |
| KeyframeState.event | Public | () => void | — | N/A | 关键帧状态闭包 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| KeyframeAnimateParam.expectedFrameRateRange | MODIFIED | 新增字段 | API 19+ 可选字段，向前兼容 | AC-6.1 |

> 截至当前版本，keyframeAnimateTo 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

**UIContext.keyframeAnimateTo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIContext::keyframeAnimateTo(param: KeyframeAnimateParam, keyframes: Array<KeyframeState>): void` |
| 返回值 | `void` — 无返回 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| param | KeyframeAnimateParam | 是 | — | delay=0, iterations=1, expectedFrameRateRange={0,0,0} |
| keyframes | Array<KeyframeState> | 是 | — | 非空数组，空数组时直接 return |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | param 和 keyframes 均合法 | 打开隐式作用域，逐帧注册 AddDurationKeyFrame，关闭隐式作用域 | AC-1.1 |
| 2 | keyframes 为空数组 | 直接 return，不触发动画 | AC-1.4 |
| 3 | KeyframeState.curve 为弹簧曲线 | 降级为 EASE_IN_OUT | AC-3.1 |

**KeyframeState**

| 属性 | 值 |
|------|-----|
| 类型 | interface |
| 开放范围 | Public |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| duration | number | 是 | — | [0, +∞) ms，< 0 取 0，浮点向下取整 |
| curve | Curve/string/ICurve | 否 | Curve.EaseInOut | 弹簧曲线降级为 EASE_IN_OUT |
| event | () => void | 是 | — | 非函数时跳过该帧 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | duration = 0 | 该帧瞬时执行 event 闭包 | AC-2.2 |
| 2 | curve 未设置 | 使用 EaseInOut | AC-2.1 |
| 3 | curve 为 springMotion | 降级为 EASE_IN_OUT | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 19+: KeyframeAnimateParam 新增 expectedFrameRateRange 可选字段，向前兼容
  - API 26+: Form 场景 duration 受 FORM_MAX_DURATION 限制
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11
- **API 版本号策略:** 基础 API @since 11，expectedFrameRateRange @since 19，Form duration 限制 @since 26

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 整体 curve 强制 EASE_IN_OUT | overallAnimationOption.SetCurve 硬编码，用户不可覆盖 | AC-2.3 |
| 弹簧曲线排除 | ParseCurve exceptSpring=true 降级弹簧曲线为 EASE_IN_OUT | AC-3.1 ~ AC-3.3 |
| 逐帧串行执行 | 各帧按数组顺序串行，不支持并行关键帧 | AC-1.2 |
| Color gamma 插值 | Color 类型使用 LinearEvaluator<Color> 特化，GAMMA_FACTOR=2.2 | AC-5.1, AC-5.2 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 关键帧动画帧率 ≥ 60fps（无 expectedFrameRateRange 限制时） | 手工 + Trace | Trace 打点 |
| 功耗 | expectedFrameRateRange 可降低帧率至 30fps | 手工 | 帧率监控 |
| 内存 | KeyframeAnimation<T> 在动画结束后被 Scheduler 回收 | UT + Dump | 对象计数 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | UIAbility 后台时动画停止并触发 onFinish，不崩溃 | UT | 生命周期测试 |
| 问题定位 | hilog 标签 ACE_ANIMATION 覆盖关键路径 | 代码审查 | — |

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
| 无障碍 | 否 | 关键帧动画不影响无障碍属性 | — |
| 大字体 | 否 | 关键帧动画与字体无关 | — |
| 深色模式 | 否 | 关键帧动画为通用动画能力，颜色值由使用方决定 | — |
| 多窗口/分屏 | 否 | 无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 19 新增 expectedFrameRateRange，API 26 Form duration 限制 | AC-6.1 |
| 生态兼容 | 否 | 无 C API / NDK 对应接口 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 关键帧动画
  作为应用开发者
  我想要使用 keyframeAnimateTo 定义多阶段关键帧动画
  以便实现复杂的串行动画效果

  Scenario: 基本多帧动画
    Given 应用调用 keyframeAnimateTo 传入 3 个 KeyframeState
    When 动画开始执行
    Then 总时长 = duration_1 + duration_2 + duration_3
    And 各帧按数组顺序串行执行
    And 每帧使用各自的 curve 进行插值
    And 所有帧完成后触发 onFinish

  Scenario: 弹簧曲线降级
    Given KeyframeState.curve 设置为 springMotion
    When ParseKeyframes 解析该帧
    Then curve 降级为 EASE_IN_OUT
    And 不报错

  Scenario: 空数组安全退出
    Given keyframeAnimateTo 第二参数为空数组
    When 调用 keyframeAnimateTo
    Then 直接 return
    And 不触发任何动画

  Scenario: Color 类型 gamma 插值
    Given 关键帧动画的目标属性为 Color，从 Red 到 Blue
    When Calculate 在 keyTime=0.5 时执行
    Then 使用 LinearEvaluator<Color> 在 gamma 空间线性插值
    And GAMMA_FACTOR=2.2

  Scenario: expectedFrameRateRange 设置
    Given KeyframeAnimateParam.expectedFrameRateRange = {min:30, max:120, expected:60}
    When 调用 keyframeAnimateTo
    Then overallAnimationOption 携带 FrameRateRange
    And 系统按帧率范围调度渲染管线
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
    query: "KeyframeAnimation<T> 模板的 AddKeyframe/Calculate/RunAsync 实现"
  - repo: "openharmony/ace_engine"
    query: "keyframeAnimateTo 隐式作用域和 AddDurationKeyFrame 链式组装"
  - repo: "openharmony/ace_engine"
    query: "LinearEvaluator<Color> gamma 空间插值算法"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`（keyframeAnimateTo）
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`（KeyframeAnimateParam / KeyframeState）
- 源码入口: `frameworks/bridge/declarative_frontend/jsview/js_view_context.cpp:870`（JSKeyframeAnimateTo）
