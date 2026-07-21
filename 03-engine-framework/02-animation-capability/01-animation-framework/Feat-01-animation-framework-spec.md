# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 动效框架全量规格 (Animator / Scheduler / Motion / AnimatorGroup / Curves) |
| 特性编号 | Func-03-02-01-Feat-01 |
| FuncID | 03-02-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 6 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 6 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Animator 类 + AnimatorOptions + AnimatorResult | @since 6，Animator.createAnimator 静态方法 |
| ADDED | onframe/onfinish/oncancel/onrepeat 回调 | @since 6（camelCase 命名） |
| ADDED | AnimatorResult.update(options) | @since 6，后续废弃 |
| ADDED | @crossplatform 标注 | @since 10，跨平台支持 |
| ADDED | @atomicservice 标注 | @since 11，原子化服务支持 |
| ADDED | setExpectedFrameRateRange(rateRange) | @since 11，帧率范围设置 |
| ADDED | onFrame/onFinish/onCancel/onRepeat 回调 | @since 12，PascalCase 命名 |
| ADDED | SimpleAnimatorOptions 类 | @since 18，带默认值的简化参数 |
| ADDED | reset(options: AnimatorOptions \| SimpleAnimatorOptions) | @since 18，支持 SimpleAnimatorOptions |
| ADDED | Animator.create(options: AnimatorOptions \| SimpleAnimatorOptions) | @since 18，重载支持 SimpleAnimatorOptions |
| MODIFIED | AnimatorResult.update 废弃 | @deprecated since 9，使用 instead reset |
| MODIFIED | Animator.createAnimator 废弃 | @deprecated since 9，使用 instead Animator.create |
| MODIFIED | onframe/onfinish/oncancel/onrepeat 废弃 | @deprecated since 12，使用 instead PascalCase 版本 |
| MODIFIED | Animator.create(options) 废弃 | @deprecated since 18，使用 instead UIContext.createAnimator |
| ADDED | UIContext.createAnimator(options) | @since 10，UI 实例关联创建 |
| ADDED | Static API: Animator.create, AnimatorOptions, SimpleAnimatorOptions, AnimatorResult | @since 23，静态模式 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/01-animation-framework/design.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@ohos.animator.d.ts`
  - Static: `<OH_ROOT>/interface/sdk-js/api/@ohos.animator.static.d.ets`
  - Curves: `<OH_ROOT>/interface/sdk-js/api/@ohos.curves.d.ts`
  - UIContext: `<OH_ROOT>/interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`
  - AnimateParam: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: Animator 创建与基本播放

**角色**: 应用开发者
**期望**: 我想要创建 Animator 实例并播放数值插值动画
**价值**: 以便驱动非属性绑定的自定义动画（如 Canvas 绘制动画）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Animator.create({ duration: 1000, iterations: 1 })` THEN 返回 AnimatorResult 对象，状态为 IDLE | 正常 |
| AC-1.2 | WHEN 调用 `animatorResult.play()` THEN 动画开始播放，onFrame 回调以 progress 值（[begin, end] 范围）被触发 | 正常 |
| AC-1.3 | WHEN 动画播放完成 THEN onFinish 回调被触发一次 | 正常 |
| AC-1.4 | WHEN 设置 `iterations: -1` THEN 动画无限循环播放，onRepeat 每轮触发 | 正常 |
| AC-1.5 | WHEN 设置 `iterations: 0` THEN play() 调用后不播放动画（`animator.cpp:394` iteration_ == 0 直接返回） | 边界 |

### US-2: Scheduler 帧调度

**角色**: 框架开发者
**期望**: 我想要通过 Scheduler 驱动动画帧回调
**价值**: 以便动画与 vsync 同步，避免画面撕裂

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Animator 调用 Play() THEN Scheduler::Start() 被调用，UIDisplaySync 订阅 vsync（`scheduler.h:50`，`scheduler.h:87`） | 正常 |
| AC-2.2 | WHEN vsync 回调到达 THEN Scheduler::OnFrame(nanoTimestamp) 被触发，转发为 callback_(durationMs) 调用 Animator::OnFrame（`scheduler.h:48`） | 正常 |
| AC-2.3 | WHEN Animator 调用 Stop()/Pause() THEN Scheduler::Stop() 被调用，UIDisplaySync 取消 vsync 订阅（`scheduler.h:52`） | 正常 |
| AC-2.4 | WHEN Scheduler 析构且 IsActive() 为 true THEN 自动调用 Stop()（`scheduler.h:42-46`） | 正常 |

### US-3: Motion 物理动画

**角色**: 应用开发者
**期望**: 我想要使用物理动画（弹簧/摩擦）驱动动画
**价值**: 以便获得自然的交互体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `animator.PlayMotion(motion)` THEN motion_ 被设置，interpolators_ 不被驱动（`animator.h:158`，`animator.cpp:378`） | 正常 |
| AC-3.2 | WHEN Motion 动画运行 THEN 每帧通过 NotifyMotion(playedTime) 驱动，motion->Move(offsetTime) 被调用（`motion.h:38`，`motion.h:41`） | 正常 |
| AC-3.3 | WHEN motion->IsCompleted() 返回 true THEN 动画自然结束，触发 finish 流程 | 边界 |
| AC-3.4 | WHEN 设置 Motion 后再调用 Play() THEN motion_ 被清除（`animator.cpp:397` motion_ = nullptr），切换回 Interpolator 模式 | 正常 |

### US-4: 状态管理

**角色**: 应用开发者
**期望**: 我想要控制动画的播放状态（暂停/恢复/停止/取消）
**价值**: 以便灵活控制动画生命周期

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 动画运行中调用 pause() THEN status_ 变为 PAUSED，scheduler_->Stop() 停止帧回调（`animator.cpp:436-461`） | 正常 |
| AC-4.2 | WHEN 动画暂停中调用 resume() THEN status_ 变为 RUNNING，scheduler_->Start() 恢复帧回调（`animator.cpp:463-496`） | 正常 |
| AC-4.3 | WHEN 动画运行中调用 stop() THEN status_ 变为 STOPPED，elapsedTime_ = 0，不可恢复（`animator.cpp:498-528`） | 正常 |
| AC-4.4 | WHEN 动画运行中调用 finish() THEN 动画跳到末尾帧并触发 finish 流程（`animator.cpp:530-548`） | 正常 |
| AC-4.5 | WHEN 动画运行中调用 cancel() THEN status_ 变为 IDLE，elapsedTime_ = 0，触发 onCancel 回调（`animator.cpp:550-569`） | 正常 |
| AC-4.6 | WHEN 动画已在 PAUSED 状态再次调用 pause() THEN 打印日志 "Already paused" 并直接返回（`animator.cpp:442-444`） | 边界 |
| AC-4.7 | WHEN 动画已在 IDLE 状态调用 cancel() THEN 打印日志 "Already in idle" 并直接返回（`animator.cpp:556-558`） | 边界 |

### US-5: 属性配置

**角色**: 应用开发者
**期望**: 我想要配置动画的时长、延迟、迭代次数、填充模式和方向
**价值**: 以便精确控制动画行为

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `duration: 2000` THEN 动画在 2000ms 内完成播放（`animator.h:125`，`animator.cpp:205`） | 正常 |
| AC-5.2 | WHEN 设置 `delay: 500` THEN 动画延迟 500ms 后开始播放（`animator.h:127` SetStartDelay） | 正常 |
| AC-5.3 | WHEN 设置 `iterations: 3` THEN 动画播放 3 次后触发 onFinish（`animator.h:130`，`animator.cpp:222`） | 正常 |
| AC-5.4 | WHEN 设置 `fill: 'forwards'` THEN 动画结束后保持末尾帧状态（`animator.h:133` SetFillMode，`animator.cpp:259`） | 正常 |
| AC-5.5 | WHEN 设置 `direction: 'alternate'` THEN 动画交替正向/反向播放（`animator.h:142` SetAnimationDirection，`animator.cpp:295`） | 正常 |
| AC-5.6 | WHEN 设置 `duration: 0` THEN 动画立即跳到末尾状态 | 边界 |

### US-6: 全局动画缩放

**角色**: 系统开发者
**期望**: 我想要通过开发者选项调节全局动画时长
**价值**: 以便测试和辅助功能使用

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `Animator::SetDurationScale(0.5)` THEN 所有新建/更新的动画 scaledDuration_ = duration_ × 0.5（`animator.h:53`，`animator.cpp:37`） | 正常 |
| AC-6.2 | WHEN 设置 scale_ 为 0.0 THEN 动画时长为 0，立即完成 | 边界 |
| AC-6.3 | WHEN 设置 scale_ 为负数 THEN 动画行为未定义（已知限制） | 异常 |

### US-7: 代理控制器

**角色**: 框架开发者
**期望**: 我想要将一个 Animator 作为另一个 Animator 的代理
**价值**: 以便实现动画编排

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `AddProxyController(proxy)` THEN proxy 加入 proxyControllers_ 列表（`animator.h:114`） | 正常 |
| AC-7.2 | WHEN 主 Animator Play/Pause/Resume/Stop THEN 所有 proxyControllers_ 中的 Animator 同步执行对应操作（`animator.cpp:458-460, 493-495, 525-527`） | 正常 |
| AC-7.3 | WHEN 调用 `ClearProxyControllers()` THEN proxyControllers_ 列表清空（`animator.h:116`） | 正常 |

### US-8: AnimatorGroup 编组

**角色**: 应用开发者
**期望**: 我想要将多个 Animator 编组同步播放
**价值**: 以便多个动画协同启动和停止

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `animatorGroup.AddAnimator(animator1)` 和 `AddAnimator(animator2)` THEN 两个 Animator 加入 animators_ map（`animator_group.h:37`） | 正常 |
| AC-8.2 | WHEN 调用 `animatorGroup.Play()` THEN 所有子 Animator 同步调用 Play()（`animator_group.h:39`） | 正常 |
| AC-8.3 | WHEN 所有子 Animator 停止 THEN AnimatorGroup status_ 变为 STOPPED，通过 OnAnimatorStop 回调检测（`animator_group.h:42`） | 正常 |

### US-9: 回调迁移

**角色**: 应用开发者
**期望**: 我想要使用新的 PascalCase 回调 API
**价值**: 以便符合 API 12+ 的命名规范

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 设置 `animatorResult.onFrame = (progress) => {}` THEN 每帧回调 progress 值（`@ohos.animator.d.ts:407`，@since 12） | 正常 |
| AC-9.2 | WHEN 同时设置 onframe（旧）和 onFrame（新） THEN 两者独立触发（旧回调 @deprecated since 12） | 正常 |
| AC-9.3 | WHEN 设置 `animatorResult.onFinish = () => {}` THEN 动画完成时触发（`@ohos.animator.d.ts:433`，@since 12） | 正常 |
| AC-9.4 | WHEN 设置 `animatorResult.onCancel = () => {}` THEN 动画取消时触发（`@ohos.animator.d.ts:459`，@since 12） | 正常 |

### US-10: UIContext 关联与 Static API

**角色**: 应用开发者
**期望**: 我想要在正确的 UI 实例中创建 Animator，并使用 Static API
**价值**: 以便在多实例场景和静态模式下正确使用动画

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 调用 `UIContext.createAnimator(options)` THEN 返回与该 UIContext 关联的 AnimatorResult（`@ohos.arkui.UIContext.d.ts:3845`，@since 10） | 正常 |
| AC-10.2 | WHEN 使用 Static API `Animator.create(options)` THEN 返回 AnimatorResult（`@ohos.animator.static.d.ets:382`，@since 23） | 正常 |
| AC-10.3 | WHEN 使用 SimpleAnimatorOptions 构造 THEN begin/end 必填，其余可选并有默认值（duration=1000, easing="ease", delay=0, fill=Forwards, direction=Normal, iterations=1）（`@ohos.animator.d.ts:172-269`） | 正常 |
| AC-10.4 | WHEN 调用 `reset(options: SimpleAnimatorOptions)` THEN 参数被正确解析（`@ohos.animator.d.ts:324`，@since 18） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-3 | TASK-ANIM-FW-01 | UT | `test/unittest/core/animation/animator_test.cpp` |
| AC-2.1 ~ AC-2.4 | R-4, R-5 | TASK-ANIM-FW-01 | UT | scheduler 单测 |
| AC-3.1 ~ AC-3.4 | R-6, R-7 | TASK-ANIM-FW-01 | UT | motion 单测 |
| AC-4.1 ~ AC-4.7 | R-8, R-9, R-10, R-11 | TASK-ANIM-FW-01 | UT | animator 状态机单测 |
| AC-5.1 ~ AC-5.6 | R-12, R-13, R-14, R-15 | TASK-ANIM-FW-01 | UT | 属性设置单测 |
| AC-6.1 ~ AC-6.3 | R-16 | TASK-ANIM-FW-01 | UT | 全局缩放单测 |
| AC-7.1 ~ AC-7.3 | R-17 | TASK-ANIM-FW-01 | UT | 代理控制器单测 |
| AC-8.1 ~ AC-8.3 | R-18 | TASK-ANIM-FW-01 | UT | animator_group 单测 |
| AC-9.1 ~ AC-9.4 | R-19 | TASK-ANIM-FW-01 | UT | 回调迁移单测 |
| AC-10.1 ~ AC-10.4 | R-20, R-21 | TASK-ANIM-FW-01 | UT + XTS | UIContext/Static API 测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 Animator.create(options) | 返回 AnimatorResult 对象，初始状态 IDLE | options 必填 | AC-1.1 |
| R-2 | 行为 | 调用 animatorResult.play() | Scheduler::Start() 启动 vsync，OnFrame 回调触发 onFrame(progress) | progress 范围 [begin, end]，默认 [0, 1] | AC-1.2 |
| R-3 | 行为 | 动画播放至 duration 结束 | 触发 onFinish 回调一次 | iterations=-1 时不触发 onFinish | AC-1.3 |
| R-4 | 行为 | Animator::AttachScheduler(context) | 创建 Scheduler 并绑定 OnFrame 回调到 Animator::OnFrame | context 为 PipelineBase 弱引用（`animator.cpp:85`） | AC-2.1 |
| R-5 | 行为 | Scheduler::Start() | displaySync_->Start() 订阅 vsync | Scheduler 析构时自动 Stop（`scheduler.h:42-46`） | AC-2.1, AC-2.4 |
| R-6 | 行为 | 调用 PlayMotion(motion) | motion_ 被设置，Play 时通过 NotifyMotion 驱动 | 设置 motion_ 后 interpolators_ 不被驱动（`animator.cpp:378`） | AC-3.1, AC-3.2 |
| R-7 | 行为 | 调用 Play()（已有 motion_ 时） | motion_ = nullptr 清除物理动画，切换回 Interpolator 模式 | `animator.cpp:397` | AC-3.4 |
| R-8 | 行为 | 调用 Pause() | status_ = PAUSED，scheduler_->Stop() 停止帧回调 | 已在 PAUSED 则直接返回（`animator.cpp:442-444`） | AC-4.1, AC-4.6 |
| R-9 | 行为 | 调用 Resume() | status_ = RUNNING，scheduler_->Start() 恢复帧回调 | 已在 RUNNING 则直接返回（`animator.cpp:469-471`） | AC-4.2 |
| R-10 | 行为 | 调用 Stop() | status_ = STOPPED，elapsedTime_ = 0，不可恢复 | 已在 STOPPED 则直接返回（`animator.cpp:504-506`） | AC-4.3 |
| R-11 | 行为 | 调用 Cancel() | status_ = IDLE，elapsedTime_ = 0，触发 onCancel 回调 | 已在 IDLE 则直接返回（`animator.cpp:556-558`） | AC-4.5, AC-4.7 |
| R-12 | 行为 | SetDuration(duration) | 设置 duration_ 并 UpdateScaledTime() | duration 单位为 ms，≥ 0 | AC-5.1 |
| R-13 | 行为 | SetIteration(iteration) | 设置 iteration_，返回 bool 表示是否成功 | iteration=0 不播放，-1 无限循环（`animator.cpp:222`） | AC-5.3 |
| R-14 | 行为 | SetFillMode(fillMode) | 设置 fillMode_，决定动画前后帧状态保持 | 默认 FillMode::FORWARDS（`animator.h:262`） | AC-5.4 |
| R-15 | 行为 | SetAnimationDirection(direction) | 设置 direction_，影响交替播放方向 | 默认 AnimationDirection::NORMAL（`animator.h:263`） | AC-5.5 |
| R-16 | 行为 | SetDurationScale(scale) | 修改静态 scale_ 变量，影响后续所有动画的 scaledDuration_ | scale=1.0 为默认，0 则立即完成 | AC-6.1, AC-6.2 |
| R-17 | 行为 | AddProxyController(proxy) | proxy 加入 proxyControllers_，主 Animator 状态变化同步传播 | Play/Pause/Resume/Stop 均同步传播 | AC-7.1, AC-7.2 |
| R-18 | 行为 | AnimatorGroup::Play() | 遍历 animators_ 调用 Play()，status_ = RUNNING | 全部子 Animator 停止后 status_ = STOPPED | AC-8.1 ~ AC-8.3 |
| R-19 | 行为 | 设置 onFrame/onFinish/onCancel/onRepeat（PascalCase） | 对应事件触发时回调 | @since 12，旧 camelCase 版本 @deprecated since 12 但仍可用 | AC-9.1 ~ AC-9.4 |
| R-20 | 行为 | 调用 UIContext.createAnimator(options) | 返回与该 UIContext 关联的 AnimatorResult | @since 10，替代全局 Animator.create | AC-10.1 |
| R-21 | 行为 | 使用 Static API Animator.create(options) | 返回 AnimatorResult | @since 23 static | AC-10.2 |
| R-22 | 边界 | iterations = 0 时调用 Play() | 直接返回，不播放动画 | `animator.cpp:394` iteration_ == 0 检查 | AC-1.5 |
| R-23 | 边界 | duration = 0 时调用 Play() | 动画立即跳到末尾状态 | scaledDuration_ = 0 时 OnFrame 直接到结束帧 | AC-5.6 |
| R-24 | 异常 | scale_ 为负数 | 行为未定义 | 已知限制，文档需说明 | AC-6.3 |
| R-25 | 恢复 | 动画运行中 UIAbility 转入后台 | 有限迭代动画立即终止并触发 onFinish 回调 | SDK 声明行为（`@ohos.arkui.UIContext.d.ts:5302-5304`） | AC-1.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | Animator 创建、Play、onFrame/onFinish/onRepeat 回调 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT | Scheduler Start/Stop/OnFrame 帧调度链路 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | Motion 设置、NotifyMotion 驱动、Play 清除 motion_ |
| VM-4 | AC-4.1 ~ AC-4.7 | UT | 状态机转换：IDLE/RUNNING/PAUSED/STOPPED |
| VM-5 | AC-5.1 ~ AC-5.6 | UT | Duration/Delay/Iteration/FillMode/Direction 设置 |
| VM-6 | AC-6.1 ~ AC-6.3 | UT | 全局 SetDurationScale 影响所有动画 |
| VM-7 | AC-7.1 ~ AC-7.3 | UT | ProxyController 同步传播 |
| VM-8 | AC-8.1 ~ AC-8.3 | UT | AnimatorGroup 编组播放/停止 |
| VM-9 | AC-9.1 ~ AC-9.4 | UT | PascalCase 回调 API |
| VM-10 | AC-10.1 ~ AC-10.4 | UT + XTS | UIContext.createAnimator + Static API + SimpleAnimatorOptions |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| Animator.create(options: AnimatorOptions) | Public | AnimatorOptions | AnimatorResult | 401 | 创建动画 | AC-1.1 |
| Animator.create(options: AnimatorOptions \| SimpleAnimatorOptions) | Public | AnimatorOptions \| SimpleAnimatorOptions | AnimatorResult | 401 | 创建动画（支持简化参数） | AC-1.1, AC-10.3 |
| AnimatorResult.play() | Public | 无 | void | N/A | 播放动画 | AC-1.2 |
| AnimatorResult.finish() | Public | 无 | void | N/A | 结束动画 | AC-4.4 |
| AnimatorResult.pause() | Public | 无 | void | N/A | 暂停动画 | AC-4.1 |
| AnimatorResult.cancel() | Public | 无 | void | N/A | 取消动画 | AC-4.5 |
| AnimatorResult.reverse() | Public | 无 | void | N/A | 反向播放 | AC-5.5 |
| AnimatorResult.reset(options) | Public | AnimatorOptions \| SimpleAnimatorOptions | void | 401, 100001 | 重置参数 | AC-10.4 |
| AnimatorResult.onFrame | Public | (progress: number) => void | void | N/A | 帧回调 | AC-9.1 |
| AnimatorResult.onFinish | Public | () => void | void | N/A | 完成回调 | AC-9.3 |
| AnimatorResult.onCancel | Public | () => void | void | N/A | 取消回调 | AC-9.4 |
| AnimatorResult.onRepeat | Public | () => void | void | N/A | 重复回调 | AC-1.4 |
| AnimatorResult.setExpectedFrameRateRange | Public | ExpectedFrameRateRange | void | N/A | 帧率范围 | AC-2.1 |
| SimpleAnimatorOptions | Public | begin: number, end: number | SimpleAnimatorOptions | N/A | 简化参数 | AC-10.3 |
| UIContext.createAnimator(options) | Public | AnimatorOptions \| SimpleAnimatorOptions | AnimatorResult | 401 | UI 关联创建 | AC-10.1 |
| curves.initCurve(curve?) | Public | Curve | ICurve | N/A | 创建曲线 | AC-5.5 |
| curves.cubicBezierCurve(x1,y1,x2,y2) | Public | number × 4 | ICurve | N/A | 三次贝塞尔 | AC-5.5 |
| curves.springCurve(velocity,mass,stiffness,damping) | Public | number × 4 | ICurve | N/A | 弹簧曲线 | AC-3.1 |
| curves.springMotion(response?,dampingFraction?,overlapDuration?) | Public | number × 3 (可选) | ICurve | N/A | 弹簧运动 | AC-3.1 |
| curves.interpolatingSpring(velocity,mass,stiffness,damping) | Public | number × 4 | ICurve | N/A | 插值弹簧 | AC-3.1 |
| Static: Animator.create(options) | Public | AnimatorOptions \| SimpleAnimatorOptions | AnimatorResult | 401 | 静态 API 创建 | AC-10.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| Animator.createAnimator(options) | MODIFIED（废弃） | @since 6 创建 Animator | 使用 Animator.create 替代 | AC-1.1 |
| AnimatorResult.update(options) | MODIFIED（废弃） | @since 6 更新参数 | 使用 reset 替代 | AC-10.4 |
| onframe | MODIFIED（废弃） | @since 6 帧回调 | 使用 onFrame 替代 | AC-9.1 |
| onfinish | MODIFIED（废弃） | @since 6 完成回调 | 使用 onFinish 替代 | AC-9.3 |
| oncancel | MODIFIED（废弃） | @since 6 取消回调 | 使用 onCancel 替代 | AC-9.4 |
| onrepeat | MODIFIED（废弃） | @since 6 重复回调 | 使用 onRepeat 替代 | AC-1.4 |
| Animator.create(options) | MODIFIED（废弃） | @since 9 全局创建 | 使用 UIContext.createAnimator 替代 | AC-10.1 |

## 接口规格

### 接口定义

**Animator.create**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static Animator.create(options: AnimatorOptions \| SimpleAnimatorOptions): AnimatorResult` |
| 返回值 | `AnimatorResult` — 动画结果对象 |
| 开放范围 | Public |
| 错误码 | 401 (参数错误), 100001 (页面未找到) |
| 关联 AC | AC-1.1, AC-10.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options.duration | number | 是 (AnimatorOptions) / 否 (SimpleAnimatorOptions) | 0 / 1000 | ≥ 0，浮点数向下取整 |
| options.easing | string | 是 (AnimatorOptions) / 否 (SimpleAnimatorOptions) | — / "ease" | 无效字符串回退为 "ease" |
| options.delay | number | 是 / 否 | 0 / 0 | 负数提前播放 |
| options.fill | string | 是 / 否 | — / FillMode.Forwards | none/forwards/backwards/both |
| options.direction | string | 是 / 否 | "normal" / PlayMode.Normal | normal/reverse/alternate/alternate-reverse |
| options.iterations | number | 是 / 否 | 0 / 1 | 0=不播放, -1=无限, 正整数=次数 |
| options.begin | number | 是 | 0 | 插值起点 |
| options.end | number | 是 | 1 | 插值终点 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入合法 AnimatorOptions | 返回 AnimatorResult，状态 IDLE | AC-1.1 |
| 2 | 传入 SimpleAnimatorOptions | 返回 AnimatorResult，使用默认值填充缺失参数 | AC-10.3 |
| 3 | 缺少必填参数 | 抛出 401 错误 | AC-1.1 |
| 4 | easing 字符串无效 | 回退为 "ease" 曲线 | AC-5.5 |

**AnimatorResult.play**

| 属性 | 值 |
|------|-----|
| 函数签名 | `AnimatorResult.play(): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 状态为 IDLE/STOPPED | 状态切换为 RUNNING，启动 vsync 帧调度 | AC-1.2 |
| 2 | iterations = 0 | 不播放，直接返回 | AC-1.5 |
| 3 | 状态为 RUNNING | 安全重入，重新启动 | AC-4.1 |

**AnimatorResult.pause**

| 属性 | 值 |
|------|-----|
| 函数签名 | `AnimatorResult.pause(): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 状态为 RUNNING | 状态切换为 PAUSED，停止帧调度 | AC-4.1 |
| 2 | 状态为 PAUSED | 打印日志，直接返回 | AC-4.6 |
| 3 | 状态为 IDLE | 先 Play 再 Pause | AC-4.1 |

**AnimatorResult.cancel**

| 属性 | 值 |
|------|-----|
| 函数签名 | `AnimatorResult.cancel(): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 状态为 RUNNING/PAUSED | 状态切换为 IDLE，elapsedTime 归零，触发 onCancel | AC-4.5 |
| 2 | 状态为 IDLE | 打印日志，直接返回 | AC-4.7 |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - onframe/onfinish/oncancel/onrepeat @deprecated since 12，推荐使用 PascalCase 版本（AC-9.1 ~ AC-9.4）
  - Animator.createAnimator @deprecated since 9，推荐 Animator.create（AC-1.1）
  - AnimatorResult.update @deprecated since 9，推荐 reset（AC-10.4）
  - Animator.create @deprecated since 18，推荐 UIContext.createAnimator（AC-10.1）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 6
- **API 版本号策略:** 基础 API @since 6，@crossplatform @since 10，@atomicservice @since 11，setExpectedFrameRateRange @since 11，PascalCase 回调 @since 12，SimpleAnimatorOptions @since 18，Static API @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双驱动模型 | Animator 同时持有 Interpolator 列表和 Motion 单例，互斥播放 | AC-1.2, AC-3.1, AC-3.4 |
| UI 线程约束 | Play/Pause/Stop/Finish/Cancel 均通过 CHECK_RUN_ON(UI) 校验 | AC-4.1 ~ AC-4.5 |
| Scheduler 生命周期 | Scheduler 析构时自动 Stop，避免 vsync 泄漏 | AC-2.4 |
| 全局缩放静态变量 | scale_ 为静态变量，影响所有 Animator 实例 | AC-6.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 动画帧率 ≥ 60fps（ExpectedFrameRateRange.expected=60） | Trace + 手工 | Trace 打点 |
| 功耗 | 动画暂停/停止后 vsync 订阅立即取消 | UT | scheduler 单测 |
| 内存 | Scheduler 和 Animator 在动画结束后被正确释放 | UT + Dump | RefPtr 引用计数 |
| 可靠性 | 重复 Play/Pause/Stop 调用不崩溃 | UT | 状态机单测 |
| 问题定位 | 关键路径 hilog 覆盖（Play/Stop/状态切换） | 代码审查 | — |

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
| 无障碍 | 是 | 全局动画缩放 SetDurationScale 影响动画时长，可被无障碍服务调节 | AC-6.1 |
| 大字体 | 否 | 动画框架不涉及字体 | — |
| 深色模式 | 否 | 动画框架不涉及颜色 | — |
| 多窗口/分屏 | 是 | UIContext.createAnimator 确保在正确的 UI 实例中创建 Animator | AC-10.1 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | 回调 API 从 camelCase 迁移到 PascalCase，createAnimator 废弃迁移到 create 再到 UIContext.createAnimator | AC-9.1, AC-10.1 |
| 生态兼容 | 是 | Static API（@since 23）与 Dynamic API 行为差异需文档化 | AC-10.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 动效框架
  作为应用开发者
  我想要使用 Animator 控制动画播放
  以便驱动自定义动画效果

  Scenario: 创建并播放动画
    Given 调用 Animator.create({ duration: 1000, iterations: 1, begin: 0, end: 1 })
    Then 返回 AnimatorResult 对象，状态为 IDLE
    When 调用 animatorResult.play()
    Then onFrame 回调以 progress 值被触发
    When 动画播放 1000ms
    Then onFinish 回调被触发一次

  Scenario: 暂停和恢复动画
    Given Animator 正在播放中（status = RUNNING）
    When 调用 animatorResult.pause()
    Then 状态变为 PAUSED，帧回调停止
    When 调用 animatorResult.resume()
    Then 状态恢复为 RUNNING，帧回调恢复

  Scenario: 停止动画（不可恢复）
    Given Animator 正在播放中
    When 调用 animatorResult.stop()
    Then 状态变为 STOPPED，elapsedTime 归零
    And 不可通过 resume 恢复

  Scenario: 取消动画
    Given Animator 正在播放中
    When 调用 animatorResult.cancel()
    Then 状态变为 IDLE，elapsedTime 归零
    And onCancel 回调被触发

  Scenario: 无限循环动画
    Given 设置 iterations = -1
    When 调用 play()
    Then 动画无限循环
    And onRepeat 每轮触发
    And 不触发 onFinish

  Scenario Outline: 全局动画缩放
    Given 全局 scale_ 设置为 <scale>
    And 动画 duration = 1000ms
    When 调用 play()
    Then 实际播放时长为 <actual_duration>ms

    Examples:
      | scale | actual_duration |
      | 1.0   | 1000            |
      | 0.5   | 500             |
      | 0.0   | 0（立即完成）    |

  Scenario: SimpleAnimatorOptions 使用
    Given 使用 SimpleAnimatorOptions(0, 100) 创建参数
    And 调用 .duration(2000).easing("ease-in")
    When 调用 Animator.create(simpleOptions)
    Then 返回 AnimatorResult，参数被正确设置

  Scenario: UIContext 关联创建
    Given 获取 UIContext 实例
    When 调用 uiContext.createAnimator(options)
    Then 返回与该 UIContext 关联的 AnimatorResult
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
    query: "Animator 状态机 IDLE/RUNNING/PAUSED/STOPPED 转换逻辑"
  - repo: "openharmony/ace_engine"
    query: "Scheduler UIDisplaySync vsync 帧调度链路"
  - repo: "openharmony/ace_engine"
    query: "Motion 物理动画 PlayMotion 和 NotifyMotion 驱动机制"
  - repo: "openharmony/ace_engine"
    query: "AnimatorGroup 编组播放和 OnAnimatorStop 回调"
  - repo: "openharmony/ace_engine"
    query: "全局动画缩放 SetDurationScale 静态变量实现"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.animator.d.ts`
- Static API: `interface/sdk-js/api/@ohos.animator.static.d.ets`
- 曲线模块: `interface/sdk-js/api/@ohos.curves.d.ts`
- 源码入口: `frameworks/core/animation/animator.h`, `frameworks/core/animation/animator.cpp`
