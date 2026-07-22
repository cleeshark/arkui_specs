# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 共享元素动画 (Shared Transition) 全量规格 |
| 特性编号 | Func-03-02-06-Feat-01 |
| FuncID | 03-02-06 |
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
| ADDED | sharedTransition(id, options?) 属性方法 | @since 7，common.d.ts:22889 |
| ADDED | sharedTransitionOptions 接口（duration/curve/delay/motionPath/zIndex/type） | @since 7，common.d.ts:4638 |
| ADDED | SharedTransitionEffectType 枚举（Static / Exchange） | @since 7，enums.d.ts:2790 |
| ADDED | MotionPathOptions 接口（path/from/to/rotatable） | @since 7，common.d.ts:4553 |
| MODIFIED | sharedTransitionOptions 跨平台支持 | @since 10，@crossplatform |
| MODIFIED | sharedTransitionOptions 原子化服务支持 | @since 11，@atomicservice |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/06-shared-transition/design.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`
  - Enum: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/enums.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础共享元素过渡

**角色**: 应用开发者
**期望**: 我想要在页面导航时让共享元素在两个页面间平滑过渡
**价值**: 以便提供连贯的视觉导航体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在源页面和目标页面对同一元素设置 `sharedTransition("shareId")` THEN 页面导航时 SharedOverlayManager::StartSharedTransition 匹配两端 shareId 并创建 SharedTransitionEffect（`shared_overlay_manager.h:36`） | 正常 |
| AC-1.2 | WHEN 设置 `sharedTransitionOptions.type = SharedTransitionEffectType.Static` THEN 仅创建 opacity 动画（`shared_transition_effect.cpp:268-282`），passenger 为 src_（离开方向）或 dest_（进入方向） | 正常 |
| AC-1.3 | WHEN 设置 `sharedTransitionOptions.type = SharedTransitionEffectType.Exchange`（默认）THEN 同时创建 translate + size + opacity 三维度动画（`shared_transition_effect.cpp:100-118`） | 正常 |
| AC-1.4 | WHEN shareId 为空字符串 THEN 不对该组件应用过渡动画（`shared_transition_effect.cpp:90-98`，Allow() 返回 false） | 边界 |
| AC-1.5 | WHEN 源页面和目标页面的 shareId 不匹配 THEN 该 shareId 不产生 Effect，CheckAndPrepareTransition 过滤掉 | 异常 |

### US-2: MotionPath 路径动画集成

**角色**: 应用开发者
**期望**: 我想要 Exchange 类型的共享元素沿自定义 SVG 路径移动
**价值**: 以便实现弧线等非直线过渡效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `sharedTransitionOptions.motionPath` 设置有效 SVG path 且 type=Exchange THEN Exchange 的 translate 动画使用 MotionPathEvaluator 替代默认 Evaluator（`shared_transition_effect.cpp:135-138`） | 正常 |
| AC-2.2 | WHEN `sharedTransitionOptions.motionPath.rotatable = true` THEN 额外创建 rotate 动画，旋转角度由 MotionPathEvaluator::CreateRotateEvaluator 计算（`shared_transition_effect.cpp:139-152`） | 正常 |
| AC-2.3 | WHEN `sharedTransitionOptions.motionPath` 未设置或 path 为空 THEN Exchange translate 使用默认直线 DimensionOffset 插值 | 正常 |
| AC-2.4 | WHEN type=Static 且设置 motionPath THEN motionPath 不生效（SDK 文档注明仅 Exchange 生效，`common.d.ts:4625`） | 边界 |

### US-3: 动画参数控制

**角色**: 应用开发者
**期望**: 我想要控制共享元素动画的时长、曲线、延迟和层级
**价值**: 以便精细调整动画效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `sharedTransitionOptions.duration = 500` THEN Animator 的 duration 设为 500ms（`shared_transition_effect.cpp:80`，ApplyAnimation → controller_->SetDuration） | 正常 |
| AC-3.2 | WHEN 未设置 duration THEN 使用默认值 1000ms（`shared_transition_option.h:28`，duration = 0 → SDK 默认 1000） | 正常 |
| AC-3.3 | WHEN 设置 `sharedTransitionOptions.delay = 200` THEN Animator 的 StartDelay 设为 200ms（`shared_transition_effect.cpp:81`，controller_->SetStartDelay） | 正常 |
| AC-3.4 | WHEN 设置 `sharedTransitionOptions.curve = Curve.EaseIn` THEN CurveAnimation 使用该曲线插值（`shared_transition_effect.cpp:61`） | 正常 |
| AC-3.5 | WHEN 未设置 curve THEN 使用默认 Curve.Linear（`common.d.ts:4664`） | 正常 |
| AC-3.6 | WHEN 设置 `sharedTransitionOptions.zIndex = 10` THEN passenger 在 overlay 中的 zIndex 为 10（`shared_transition_effect.h:59-62`，GetZIndex → option_->zIndex） | 正常 |

### US-4: 回退动画

**角色**: 终端用户
**期望**: 我想要在动画期间按下返回键时正确终止动画
**价值**: 以便避免动画卡死或状态不一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 共享过渡动画运行中按下返回键 THEN SharedOverlayManager::OnBackPressed → StopSharedTransition，对所有 effect 调用 StopPlayingEffect（`shared_overlay_manager.h:38`，`shared_transition_effect.h:63-69`） | 正常 |
| AC-4.2 | WHEN StopPlayingEffect 调用时 controller_ 正在运行 THEN controller_->Finish() 使动画跳到终点 | 正常 |
| AC-4.3 | WHEN StopPlayingEffect 调用时 controller_ 未运行 THEN 不执行 Finish（`shared_transition_effect.h:65`，IsRunning() 检查） | 边界 |
| AC-4.4 | WHEN 回退动画完成后 THEN GetOffShuttle 恢复 passenger 到原位置，移除 holder 节点（`shared_overlay_manager.h:48`） | 正常 |

### US-5: Passenger 节点管理

**角色**: 框架开发者
**期望**: 我想要了解 Passenger 节点在动画期间如何被管理
**价值**: 以便理解 overlay 机制和布局一致性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN AboardShuttle 执行 THEN PassengerAboard 将 passenger 从原父节点摘除，创建 passengerHolder_ 节点占位（`shared_overlay_manager.h:47-49`，`shared_transition_effect.h:103-106`） | 正常 |
| AC-5.2 | WHEN passenger 被移入 overlay THEN passengerHolder_ 保持原位置和布局约束（initialPosition_ / initialMargin_ / initialFrameOffset_ / initialZIndex_，`shared_transition_effect.h:142-145`） | 正常 |
| AC-5.3 | WHEN 动画完成 GetOffShuttle 执行 THEN PerformFinishCallback 清理 finishCallbacks_ 列表（`shared_transition_effect.cpp:44-52`），passenger 恢复到 holder 位置 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-3 | TASK-SHARED-TRANSITION-01 | UT | shared_overlay_manager 单测 |
| AC-2.1 ~ AC-2.4 | R-4, R-5 | TASK-SHARED-TRANSITION-01 | UT + 手工 | MotionPath 集成测试 |
| AC-3.1 ~ AC-3.6 | R-6, R-7 | TASK-SHARED-TRANSITION-01 | UT | 参数传递测试 |
| AC-4.1 ~ AC-4.4 | R-8, R-9 | TASK-SHARED-TRANSITION-01 | UT | 回退动画测试 |
| AC-5.1 ~ AC-5.3 | R-10, R-11 | TASK-SHARED-TRANSITION-01 | UT | Passenger 管理测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 两页面元素设置相同 shareId 且 type=Exchange | SharedOverlayManager 创建 SharedTransitionExchange，CreateAnimation 创建 translate+size+opacity 三维度 | shareId 非空，src 和 dest 节点有效 | AC-1.1, AC-1.3 |
| R-2 | 行为 | type=Static | 创建 SharedTransitionStatic，仅 CreateOpacityAnimation；passenger = src_.Invalid() ? dest_ : src_ | — | AC-1.2 |
| R-3 | 边界 | shareId 为空字符串 | Allow() 返回 false，CheckAndPrepareTransition 过滤掉该 Effect | `shared_transition_effect.cpp:90-98, 261-266` | AC-1.4 |
| R-4 | 行为 | Exchange + motionPathOption.IsValid() | CreateTranslateAnimation 创建 MotionPathEvaluator(option, Offset(0,0), diff)，调用 CreateDimensionOffsetEvaluator() | `shared_transition_effect.cpp:135-138` | AC-2.1 |
| R-5 | 行为 | Exchange + motionPathOption.GetRotate() = true | 额外创建 CurveAnimation<float>，使用 CreateRotateEvaluator()，listener 调用 UpdateTransformRotate | `shared_transition_effect.cpp:139-152` | AC-2.2 |
| R-6 | 行为 | ApplyAnimation 调用 | controller_->SetDuration(option_->duration) + SetStartDelay(option_->delay) | duration 默认 1000，delay 默认 0 | AC-3.1, AC-3.3 |
| R-7 | 行为 | CreateOpacityAnimation 创建 | 使用 option_->curve 创建 CurveAnimation<float>，listener 调用 UpdateOpacity | curve 默认 Curve.Linear | AC-3.4, AC-3.5 |
| R-8 | 恢复 | 动画运行中 OnBackPressed | StopSharedTransition → 遍历 effects，StopPlayingEffect → controller_->Finish() | IsRunning() 为 true 时才 Finish | AC-4.1, AC-4.2 |
| R-9 | 边界 | StopPlayingEffect 调用时 controller_ 未运行 | 不执行 Finish，直接返回 | `shared_transition_effect.h:65` | AC-4.3 |
| R-10 | 行为 | AboardShuttle 执行 | PassengerAboard 摘除 passenger，创建 passengerHolder_ 占位，passenger 挂到 sharedManager_ overlay | holder 保持 initialPosition/Margin/FrameOffset/ZIndex | AC-5.1, AC-5.2 |
| R-11 | 恢复 | 动画完成 | PerformFinishCallback 遍历 finishCallbacks_ 列表逐个调用后清空；GetOffShuttle 恢复 passenger | `shared_transition_effect.cpp:44-52` | AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | shareId 匹配、Exchange/Static 类型分发、空 shareId 跳过 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT + 手工 | MotionPath Evaluator 集成、rotate 动画、Static 忽略 motionPath |
| VM-3 | AC-3.1 ~ AC-3.6 | UT | duration/delay/curve/zIndex 参数传递 |
| VM-4 | AC-4.1 ~ AC-4.4 | UT | 回退动画 Finish + GetOffShuttle |
| VM-5 | AC-5.1 ~ AC-5.3 | UT | Passenger holder 创建与恢复 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| sharedTransition(id, options?) | Public | id: string, options?: sharedTransitionOptions | T | N/A | 设置共享元素过渡 | AC-1.1 |
| sharedTransitionOptions | Public | duration/curve/delay/motionPath/zIndex/type | — | N/A | 过渡参数配置 | AC-3.1 ~ AC-3.6 |
| SharedTransitionEffectType | Public | Static / Exchange | — | N/A | 过渡效果类型枚举 | AC-1.2, AC-1.3 |
| MotionPathOptions | Public | path/from/to/rotatable | — | N/A | 路径动画配置 | AC-2.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| sharedTransitionOptions | MODIFIED | @crossplatform since 10 | 新增跨平台支持，行为兼容 | AC-1.1 |
| sharedTransitionOptions | MODIFIED | @atomicservice since 11 | 新增原子化服务支持，行为兼容 | AC-1.1 |

> 截至当前版本，sharedTransition 未发现任何 @deprecated 标注的 API。

## 接口规格

### 接口定义

**sharedTransition**

| 属性 | 值 |
|------|-----|
| 函数签名 | `sharedTransition(id: string, options?: sharedTransitionOptions): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | string | 是 | — | 空字符串 → 无过渡；非空 → 匹配同 id 的另一页面元素 |
| options | sharedTransitionOptions | 否 | 默认值见下表 | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 两页面相同 id，type=Exchange | 创建 Exchange Effect，translate+size+opacity | AC-1.1, AC-1.3 |
| 2 | 两页面相同 id，type=Static | 创建 Static Effect，仅 opacity | AC-1.2 |
| 3 | id 为空字符串 | Allow() 返回 false，跳过过渡 | AC-1.4 |
| 4 | 两页面无匹配 id | 不产生 Effect | AC-1.5 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 API @since 7，@crossplatform @since 10，@atomicservice @since 11

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ShareId 匹配 | 通过 shareId 跨页面匹配元素，空 id 不产生过渡 | AC-1.1, AC-1.4 |
| Overlay 机制 | Passenger 在动画期间移入 SharedOverlayManager 的 overlay 层，holder 占位 | AC-5.1, AC-5.2 |
| Exchange 三维度 | translate / size / opacity 各自独立判断 NearEqual 跳过 | AC-1.3 |
| MotionPath 仅 Exchange | Static 类型忽略 motionPath 设置 | AC-2.4 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 共享过渡动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | 动画结束后 holder 节点销毁，passenger 恢复 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | 回退动画不导致状态不一致 | UT | 回退动画测试 |
| 问题定位 | TAG_LOGD ACE_ANIMATION 标签覆盖关键路径 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 共享过渡为视觉效果，不影响无障碍属性 | — |
| 大字体 | 否 | 共享过渡不涉及字体 | — |
| 深色模式 | 否 | 共享过渡不涉及颜色属性 | — |
| 多窗口/分屏 | 是 | SharedOverlayManager 绑定页面根节点，每个窗口独立管理 | AC-1.1 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | @since 7/10/11 版本策略 | AC-1.1 |
| 生态兼容 | 否 | 无 C API | — |

## 行为场景（Gherkin）

```gherkin
Feature: 共享元素动画
  作为应用开发者
  我想要在页面导航时实现共享元素过渡动画
  以便提供连贯的视觉导航体验

  Scenario: Exchange 类型基础过渡
    Given 源页面和目标页面各有一个元素设置了 sharedTransition("myId")
    When 页面导航触发
    Then SharedOverlayManager 匹配 shareId 并创建 SharedTransitionExchange
    And 依次创建 translate + size + opacity 三维度动画
    And Animator 驱动动画播放

  Scenario: Static 类型过渡
    Given 元素设置了 sharedTransition("myId", { type: SharedTransitionEffectType.Static })
    When 页面导航触发
    Then 创建 SharedTransitionStatic
    And 仅创建 opacity 动画（淡入或淡出）

  Scenario: 空 shareId 跳过过渡
    Given 元素设置了 sharedTransition("")
    When 页面导航触发
    Then Allow() 返回 false
    And 不对该元素应用过渡动画

  Scenario: Exchange + MotionPath 路径动画
    Given 元素设置了 sharedTransition("myId", { motionPath: { path: "Mstart.x start.y L100 200 Lend.x end.y" } })
    When Exchange 动画创建
    Then translate 使用 MotionPathEvaluator 计算偏移
    And 元素沿 SVG 路径移动

  Scenario: Exchange + MotionPath + rotatable
    Given 元素设置了 sharedTransition("myId", { motionPath: { path: "...", rotatable: true } })
    When Exchange 动画创建
    Then 额外创建 rotate 动画
    And 旋转角度由路径切线方向计算

  Scenario: 回退动画
    Given 共享过渡动画正在运行
    When 用户按下返回键
    Then StopSharedTransition 被调用
    And 所有 effect 的 StopPlayingEffect 调用 controller_->Finish()
    And Passenger 恢复到原位置

  Scenario Outline: 动画参数设置
    Given 元素设置了 sharedTransition("myId", { duration: <duration>, delay: <delay> })
    When 动画启动
    Then Animator duration = <duration> ms
    And Animator startDelay = <delay> ms

    Examples:
      | duration | delay |
      | 500      | 0     |
      | 1000     | 200   |
      | 2000     | 500   |
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
    query: "SharedOverlayManager StartSharedTransition 流程和 Passenger holder 机制"
  - repo: "openharmony/ace_engine"
    query: "SharedTransitionExchange CreateTranslateAnimation 中 MotionPathEvaluator 集成"
  - repo: "openharmony/ace_engine"
    query: "SharedTransitionStatic CreateOpacityAnimation 淡入淡出逻辑"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 源码入口: `frameworks/core/components_ng/manager/shared_overlay/shared_overlay_manager.h`
- Effect 实现: `frameworks/core/components_ng/manager/shared_overlay/shared_transition_effect.h/.cpp`
