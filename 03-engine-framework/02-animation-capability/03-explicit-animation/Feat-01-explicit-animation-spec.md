# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 显式动画全量规格 (animateTo / animateToImmediately / AnimationUtils / Animation<T> / AddKeyFrame) |
| 特性编号 | Func-03-02-03-Feat-01 |
| FuncID | 03-02-03 |
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
| ADDED | `animateTo(value: AnimateParam, event: () => void): void` | @since 7，全局显式动画函数 |
| ADDED | @crossplatform 标注 | @since 10，跨平台支持 |
| ADDED | `UIContext.animateTo(value, event)` | @since 10，UI 实例关联版本 |
| ADDED | @form 标注 | @since 9，卡片支持 |
| ADDED | @atomicservice 标注 | @since 11 |
| ADDED | `animateToImmediately(value: AnimateParam, event: () => void): void` | @since 12，立即执行版本 |
| ADDED | `UIContext.animateToImmediately(param, processor)` | @since 12，UI 关联立即执行版本 |
| MODIFIED | `animateTo` (全局) 废弃 | @deprecated since 18，使用 instead UIContext.animateTo |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/03-explicit-animation/design.md`
- **SDK 类型定义**:
  - Common: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`
  - UIContext: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基本显式动画

**角色**: 应用开发者
**期望**: 我想要通过 animateTo 函数显式地为状态变化添加动画
**价值**: 以便在状态变化时自动产生平滑过渡

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `animateTo({ duration: 1000, curve: Curve.EaseInOut }, () => { this.width = 200 })` THEN 宽度从当前值到 200vp 在 1000ms 内按 EaseInOut 曲线过渡 | 正常 |
| AC-1.2 | WHEN animateTo 闭包执行前 THEN OpenImplicitAnimation 被调用（`animation_utils.h:58`，`rosen_animation_utils.cpp:123`），Rosen RSNode 开启隐式动画作用域 | 正常 |
| AC-1.3 | WHEN animateTo 闭包执行后 THEN CloseImplicitAnimation 被调用（`animation_utils.h:63`，`rosen_animation_utils.cpp:138`），收集所有插值器创建 Animator | 正常 |
| AC-1.4 | WHEN 动画完成 THEN onFinish 回调被触发 | 正常 |
| AC-1.5 | WHEN animateTo 参数不足 2 个（info.Length() < 2）THEN 直接返回不执行动画（`js_view_context.cpp:744-746`） | 异常 |
| AC-1.6 | WHEN info[0] 不是对象 THEN 直接返回不执行动画（`js_view_context.cpp:747-748`） | 异常 |

### US-2: 立即执行动画

**角色**: 应用开发者
**期望**: 我想要动画立即开始而不等待 vsync 对齐
**价值**: 以便在需要即时视觉反馈的场景中获得更好体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `animateToImmediately(value, event)` THEN 动画立即开始，不等 vsync 对齐（`common.d.ts:7095`，@since 12） | 正常 |
| AC-2.2 | WHEN JSAnimateToImmediately 被调用 THEN 传递 immediately=true 到 AnimateToInner（`js_view_context.cpp:699-702`） | 正常 |
| AC-2.3 | WHEN 调用 `UIContext.animateToImmediately(param, processor)` THEN 在指定 UIContext 中立即执行动画（`@ohos.arkui.UIContext.d.ts:5592`） | 正常 |

### US-3: AnimationUtils 隐式动画管理

**角色**: 框架开发者
**期望**: 我想要理解 AnimationUtils 的隐式动画作用域管理机制
**价值**: 以便正确使用显式动画接口

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `AnimationUtils::OpenImplicitAnimation(option, curve, finishCallback)` THEN Rosen RSNode::OpenImplicitAnimation 被调用，开启隐式动画作用域（`rosen_animation_utils.cpp:123-131`） | 正常 |
| AC-3.2 | WHEN 调用 `AnimationUtils::CloseImplicitAnimation()` THEN Rosen RSNode::CloseImplicitAnimation 被调用，收集插值器创建 Animator（`rosen_animation_utils.cpp:138-148`） | 正常 |
| AC-3.3 | WHEN 调用 `AnimationUtils::Animate(option, callback, finishCallback, repeatCallback)` THEN Open + callback + Close 一体化执行（`rosen_animation_utils.cpp:191-205`） | 正常 |
| AC-3.4 | WHEN 调用 `AnimationUtils::IsImplicitAnimationOpen()` THEN 返回当前是否有活跃的隐式动画作用域（`rosen_animation_utils.cpp:179-183`） | 正常 |

### US-4: 关键帧动画

**角色**: 应用开发者
**期望**: 我想要通过关键帧精确控制动画的每个阶段
**价值**: 以便实现多阶段复杂动画

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `AnimationUtils::AddKeyFrame(0.0, curve1, callback1)` 和 `AddKeyFrame(0.5, curve2, callback2)` 和 `AddKeyFrame(1.0, curve3, callback3)` THEN 动画按 3 个关键帧分段执行，每段使用独立曲线（`animation_utils.h:82-84`） | 正常 |
| AC-4.2 | WHEN 调用 `AnimationUtils::AddDurationKeyFrame(duration, curve, callback)` THEN 按 duration（ms）添加关键帧（`animation_utils.h:89-91`） | 正常 |
| AC-4.3 | WHEN 关键帧 fraction 超出 [0.0, 1.0] 范围 THEN 行为未定义 | 边界 |

### US-5: UIContext 关联

**角色**: 应用开发者
**期望**: 我想要在正确的 UI 实例中执行显式动画
**价值**: 以便在多实例场景下避免动画混淆

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `UIContext.animateTo(value, event)` THEN 在指定 UIContext 中执行动画（`@ohos.arkui.UIContext.d.ts:5319`，@since 10） | 正常 |
| AC-5.2 | WHEN 全局 animateTo 在非正确线程调用 THEN 尝试 localContainerId 回退，若失败则打印警告日志（`js_view_context.cpp:720-733`） | 异常 |
| AC-5.3 | WHEN 找不到 current context THEN 打印警告日志并返回，建议使用 uiContext.animateTo（`js_view_context.cpp:736-742`） | 异常 |

### US-6: Animation<T> 与动画控制

**角色**: 框架开发者
**期望**: 我想要理解 Animation<T> 模板和动画控制 API
**价值**: 以便实现自定义动画和精确控制

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 使用 `AnimationUtils::StartAnimation(option, callback, finishCallback, repeatCallback)` THEN 返回 Animation 对象引用（`animation_utils.h:103-108`） | 正常 |
| AC-6.2 | WHEN 调用 `AnimationUtils::StopAnimation(animation)` THEN 停止指定动画（`animation_utils.h:110`） | 正常 |
| AC-6.3 | WHEN 调用 `AnimationUtils::PauseAnimation(animation)` 和 `ResumeAnimation(animation)` THEN 动画暂停和恢复（`animation_utils.h:113-114`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.6 | R-1, R-2, R-3, R-4 | TASK-EXPL-ANIM-01 | UT | `test/unittest/core/animation/` animateTo 单测 |
| AC-2.1 ~ AC-2.3 | R-5, R-6 | TASK-EXPL-ANIM-01 | UT | animateToImmediately 单测 |
| AC-3.1 ~ AC-3.4 | R-7, R-8, R-9 | TASK-EXPL-ANIM-01 | UT | AnimationUtils 单测 |
| AC-4.1 ~ AC-4.3 | R-10, R-11 | TASK-EXPL-ANIM-01 | UT | AddKeyFrame 单测 |
| AC-5.1 ~ AC-5.3 | R-12, R-13 | TASK-EXPL-ANIM-01 | UT + XTS | UIContext.animateTo 测试 |
| AC-6.1 ~ AC-6.3 | R-14 | TASK-EXPL-ANIM-01 | UT | StartAnimation/StopAnimation 单测 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 animateTo(value, event) | OpenImplicitAnimation → 执行闭包 → CloseImplicitAnimation | 闭包内属性变化自动注册插值器 | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 行为 | OpenImplicitAnimation 调用 | 委托 RSNode::OpenImplicitAnimation 开启隐式动画作用域 | `rosen_animation_utils.cpp:123-131` | AC-1.2, AC-3.1 |
| R-3 | 行为 | CloseImplicitAnimation 调用 | 委托 RSNode::CloseImplicitAnimation 收集插值器创建 Animator | `rosen_animation_utils.cpp:138-148` | AC-1.3, AC-3.2 |
| R-4 | 异常 | animateTo 参数不足 2 个或 info[0] 非对象 | 直接返回，不执行动画 | `js_view_context.cpp:744-748` | AC-1.5, AC-1.6 |
| R-5 | 行为 | 调用 animateToImmediately(value, event) | 动画立即开始，不等 vsync 对齐 | @since 12（`common.d.ts:7095`） | AC-2.1 |
| R-6 | 行为 | JSAnimateToImmediately 调用 | 传递 immediately=true 到 AnimateToInner | `js_view_context.cpp:699-702` | AC-2.2 |
| R-7 | 行为 | 调用 AnimationUtils::Animate(option, callback, finishCallback, repeatCallback) | Open + callback + Close 一体化执行 | `rosen_animation_utils.cpp:191-205` | AC-3.3 |
| R-8 | 行为 | 调用 IsImplicitAnimationOpen() | 返回当前是否有活跃隐式动画作用域 | `rosen_animation_utils.cpp:179-183` | AC-3.4 |
| R-9 | 行为 | 调用 ExecuteWithoutAnimation(callback) | 在无动画作用域中执行回调 | `animation_utils.h:118-119` | AC-3.4 |
| R-10 | 行为 | 调用 AddKeyFrame(fraction, curve, callback) | 按 fraction ∈ [0.0, 1.0] 添加关键帧 | 每帧可指定独立曲线 | AC-4.1 |
| R-11 | 行为 | 调用 AddDurationKeyFrame(duration, curve, callback) | 按 duration（ms）添加关键帧 | `animation_utils.h:89-91` | AC-4.2 |
| R-12 | 行为 | 调用 UIContext.animateTo(value, event) | 在指定 UIContext 中执行动画 | @since 10（`@ohos.arkui.UIContext.d.ts:5319`） | AC-5.1 |
| R-13 | 异常 | 全局 animateTo 在非正确线程调用 | 尝试 localContainerId 回退，失败则打印警告日志 | `js_view_context.cpp:720-733` | AC-5.2 |
| R-14 | 行为 | 调用 StartAnimation(option, callback, finishCallback, repeatCallback) | 返回 Animation 对象引用，可通过 StopAnimation/PauseAnimation/ResumeAnimation 控制 | `animation_utils.h:103-114` | AC-6.1 ~ AC-6.3 |
| R-15 | 边界 | 关键帧 fraction 超出 [0.0, 1.0] | 行为未定义 | 已知限制 | AC-4.3 |
| R-16 | 恢复 | UIAbility 转入后台 | 有限迭代动画立即终止并触发 onFinish | `@ohos.arkui.UIContext.d.ts:5302-5304` | AC-1.4 |
| R-17 | 边界 | 在 aboutToAppear 中调用 animateTo | 动画可能不生效（组件未创建，无初始值） | 文档说明限制 | AC-1.1 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.6 | UT | animateTo 闭包动画机制、参数校验 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT | animateToImmediately 立即执行 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | AnimationUtils Open/Close/Animate/IsOpen |
| VM-4 | AC-4.1 ~ AC-4.3 | UT | AddKeyFrame / AddDurationKeyFrame |
| VM-5 | AC-5.1 ~ AC-5.3 | UT + XTS | UIContext.animateTo、线程检查 |
| VM-6 | AC-6.1 ~ AC-6.3 | UT | StartAnimation/StopAnimation/PauseAnimation/ResumeAnimation |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| animateTo(value, event) | Public | AnimateParam, () => void | void | N/A | 显式动画 | AC-1.1 |
| animateToImmediately(value, event) | Public | AnimateParam, () => void | void | N/A | 立即显式动画 | AC-2.1 |
| UIContext.animateTo(value, event) | Public | AnimateParam, () => void | void | N/A | UI 关联显式动画 | AC-5.1 |
| UIContext.animateToImmediately(param, processor) | Public | AnimateParam, Callback<void> | void | N/A | UI 关联立即动画 | AC-2.3 |
| AnimationUtils::Animate | InnerApi | AnimationOption, PropertyCallback, FinishCallback, RepeatCallback | void | N/A | 一体化动画 | AC-3.3 |
| AnimationUtils::AddKeyFrame | InnerApi | float, RefPtr<Curve>, PropertyCallback | void | N/A | 添加关键帧 | AC-4.1 |
| AnimationUtils::AddDurationKeyFrame | InnerApi | int32_t, RefPtr<Curve>, PropertyCallback | void | N/A | 按时长关键帧 | AC-4.2 |
| AnimationUtils::StartAnimation | InnerApi | AnimationOption, PropertyCallback, FinishCallback, RepeatCallback | shared_ptr<Animation> | N/A | 启动动画 | AC-6.1 |
| AnimationUtils::StopAnimation | InnerApi | shared_ptr<Animation> | void | N/A | 停止动画 | AC-6.2 |
| AnimationUtils::PauseAnimation | InnerApi | shared_ptr<Animation> | void | N/A | 暂停动画 | AC-6.3 |
| AnimationUtils::ResumeAnimation | InnerApi | shared_ptr<Animation> | void | N/A | 恢复动画 | AC-6.3 |
| AnimationUtils::ReverseAnimation | InnerApi | shared_ptr<Animation> | void | N/A | 反向动画 | AC-6.2 |
| AnimationUtils::ExecuteWithoutAnimation | InnerApi | PropertyCallback | void | N/A | 无动画执行 | AC-3.4 |
| AnimationUtils::OpenImplicitAnimation | InnerApi | AnimationOption, RefPtr<Curve>, FinishCallback | void | N/A | 开启隐式动画 | AC-1.2 |
| AnimationUtils::CloseImplicitAnimation | InnerApi | 无 | bool | N/A | 关闭隐式动画 | AC-1.3 |
| AnimationUtils::IsImplicitAnimationOpen | InnerApi | 无 | bool | N/A | 查询隐式动画状态 | AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| animateTo (全局函数) | MODIFIED（废弃） | @since 7 全局显式动画 | 使用 UIContext.animateTo 替代 (@since 10) | AC-5.1 |

## 接口规格

### 接口定义

**animateTo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `animateTo(value: AnimateParam, event: () => void): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | AnimateParam | 是 | — | 动画参数（duration/curve/delay 等） |
| event | () => void | 是 | — | 闭包函数，内含属性变化 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入合法 AnimateParam 和闭包 | Open → 闭包 → Close，动画自动产生 | AC-1.1 |
| 2 | 参数不足 2 个 | 直接返回 | AC-1.5 |
| 3 | info[0] 非对象 | 直接返回 | AC-1.6 |
| 4 | 在 aboutToAppear 中调用 | 可能不生效（组件未创建） | AC-1.1 |

**animateToImmediately**

| 属性 | 值 |
|------|-----|
| 函数签名 | `animateToImmediately(value: AnimateParam, event: () => void): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 animateToImmediately | 动画立即开始，不等 vsync | AC-2.1 |
| 2 | 通过 UIContext 调用 | 在指定 UI 实例中立即执行 | AC-2.3 |

**UIContext.animateTo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `UIContext.animateTo(value: AnimateParam, event: () => void): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 通过 UIContext 调用 animateTo | 在正确 UI 实例中执行动画 | AC-5.1 |
| 2 | UIAbility 转入后台 | 有限迭代动画立即终止，触发 onFinish | AC-1.4 |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - 全局 animateTo @deprecated since 18，推荐 UIContext.animateTo（AC-5.1）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 全局 animateTo @since 7 @deprecated 18，UIContext.animateTo @since 10，animateToImmediately @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Open-Close 作用域 | animateTo 通过 Open/Close 隐式动画作用域捕获闭包内属性变化 | AC-1.1, AC-1.2, AC-1.3 |
| Rosen RSNode 委托 | AnimationUtils 静态方法委托 Rosen RSNode 管理隐式动画 | AC-3.1, AC-3.2 |
| 线程检查 | AnimateToInner 检查运行线程，非正确线程尝试回退 | AC-5.2 |
| UIContext 关联 | 推荐使用 UIContext 版本确保正确 UI 实例 | AC-5.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 显式动画帧率 ≥ 60fps | Trace + 手工 | Trace 打点 |
| 内存 | Animation 对象在动画结束后被正确释放 | UT + Dump | shared_ptr 引用计数 |
| 可靠性 | 重复 animateTo 调用不崩溃 | UT | AnimateToInner 单测 |
| 问题定位 | 关键路径 hilog 覆盖（线程检查、参数解析） | 代码审查 | — |

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
| 无障碍 | 否 | 显式动画不直接涉及无障碍 | — |
| 大字体 | 否 | 显式动画不涉及字体 | — |
| 深色模式 | 否 | 显式动画框架不涉及颜色 | — |
| 多窗口/分屏 | 是 | UIContext.animateTo 确保在正确 UI 实例执行 | AC-5.1 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | 全局 animateTo @deprecated since 18，迁移到 UIContext.animateTo | AC-5.1 |
| 生态兼容 | 是 | State Management V2 与 animateTo 可能产生意外结果，需文档说明 | AC-1.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 显式动画
  作为应用开发者
  我想要通过 animateTo 显式地为状态变化添加动画
  以便实现复杂的动画效果

  Scenario: 基本 animateTo
    Given 组件已渲染，宽度为 100vp
    When 调用 animateTo({ duration: 1000, curve: Curve.EaseInOut }, () => { this.width = 200 })
    Then 宽度从 100vp 到 200vp 在 1000ms 内按 EaseInOut 曲线过渡
    And 动画完成后 onFinish 被触发

  Scenario: animateToImmediately 立即执行
    Given 组件已渲染
    When 调用 animateToImmediately({ duration: 300 }, () => { this.opacity = 0 })
    Then 动画立即开始，不等 vsync 对齐
    And 透明度从 1 到 0 在 300ms 内过渡

  Scenario: UIContext 关联 animateTo
    Given 获取 UIContext 实例
    When 调用 uiContext.animateTo({ duration: 500 }, () => { this.scale = 1.5 })
    Then 在指定 UI 实例中执行动画

  Scenario: 参数不足
    When 调用 animateTo({ duration: 1000 })
    Then 直接返回，不执行动画

  Scenario: 关键帧动画
    Given 调用 animateTo({ duration: 3000 })
    When 在闭包内使用 AddKeyFrame(0.0, curve1, callback1)
    And 使用 AddKeyFrame(0.5, curve2, callback2)
    And 使用 AddKeyFrame(1.0, curve3, callback3)
    Then 动画按 3 个关键帧分段执行
    And 每段使用独立曲线

  Scenario Outline: animateTo 与 animateToImmediately 差异
    Given 组件已渲染
    When 调用 <function>({ duration: 1000 }, () => { this.width = 200 })
    Then 动画<timing>开始

    Examples:
      | function              | timing     |
      | animateTo             | 等 vsync 后 |
      | animateToImmediately  | 立即       |

  Scenario: 非正确线程调用
    Given 全局 animateTo 在非 UI 线程调用
    When 线程检查失败
    Then 尝试 localContainerId 回退
    And 回退失败则打印警告日志

  Scenario: 动画控制
    Given 使用 StartAnimation 启动动画并获取 Animation 引用
    When 调用 PauseAnimation(animation)
    Then 动画暂停
    When 调用 ResumeAnimation(animation)
    Then 动画恢复
    When 调用 StopAnimation(animation)
    Then 动画停止
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
    query: "animateTo 闭包动画 Open-Close 作用域机制和 AnimateToInner 实现"
  - repo: "openharmony/ace_engine"
    query: "animateToImmediately 与 animateTo 的差异和 immediately 参数处理"
  - repo: "openharmony/ace_engine"
    query: "AnimationUtils OpenImplicitAnimation/CloseImplicitAnimation/Animate 委托 Rosen RSNode 实现"
  - repo: "openharmony/ace_engine"
    query: "AddKeyFrame 关键帧动画和 Animation<T> 模板"
  - repo: "openharmony/ace_engine"
    query: "UIContext.animateTo 线程检查和多实例关联"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- UIContext API: `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`
- 源码入口: `frameworks/core/components_ng/render/animation_utils.h`, `frameworks/core/components_ng/render/adapter/rosen_animation_utils.cpp`
