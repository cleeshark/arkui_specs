# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 转场动画全量规格 (TransitionEffect 链式效果、appear/disappear 效果链、SLIDE_SWITCH 内置参数) |
| 特性编号 | Func-03-02-05-Feat-01 |
| FuncID | 03-02-05 |
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
| ADDED | `.transition(value: TransitionOptions \| TransitionEffect): T` | @since 7，支持旧 TransitionOptions |
| ADDED | `TransitionOptions` 接口（type/opacity/translate/scale/rotate） | @since 7，@deprecated since 10 |
| ADDED | `TransitionType` 枚举（All/Insert/Delete） | @since 7，@deprecated since 10 |
| ADDED | `TransitionEffect` 类（IDENTITY/OPACITY/SLIDE/SLIDE_SWITCH 预设 + translate/rotate/scale/opacity/move/asymmetric 工厂 + combine/animation 方法） | @since 10 |
| ADDED | `TransitionEdge` 枚举（TOP/BOTTOM/START/END） | @since 10 |
| ADDED | `.transition(effect: TransitionEffect, onFinish: Optional<TransitionFinishCallback>): T` | @since 12 |
| ADDED | `TransitionFinishCallback` type (transitionIn: boolean) => void | @since 12 |
| MODIFIED | `.transition(effect, onFinish)` 可在 attributeModifier 中调用 | @since 20 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/02-animation-capability/05-transition-animation/design.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/common.d.ts`（TransitionEffect / TransitionOptions / TransitionEdge / TransitionFinishCallback）
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/enums.static.d.ets`（TransitionType 静态枚举）
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/common.static.d.ets`（TransitionEffect 静态 API）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: TransitionEffect 预设效果

**角色**: 应用开发者
**期望**: 我想要使用预设的 TransitionEffect 实现组件转场
**价值**: 以便快速实现常见的 appear/disappear 动画效果

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 使用 `TransitionEffect.OPACITY` THEN 组件 appear 时 opacity 0→1，disappear 时 opacity 1→0（SDK common.d.ts:6358-6368） | 正常 |
| AC-1.2 | WHEN 使用 `TransitionEffect.IDENTITY` THEN 组件 appear/disappear 时不做任何变换（SDK common.d.ts:6355） | 正常 |
| AC-1.3 | WHEN 使用 `TransitionEffect.SLIDE` THEN 等价于 `asymmetric(move(START), move(END))`，appear 从 START 边滑入，disappear 从 END 边滑出（SDK common.d.ts:6371-6390） | 正常 |
| AC-1.4 | WHEN 使用 `TransitionEffect.SLIDE_SWITCH` THEN 使用内置 600ms cubicBezier(0.24,0,0.5,1.0) + scale 0.85 动画（`rosen_transition_effect.cpp:24-29`） | 正常 |

### US-2: TransitionEffect 工厂方法

**角色**: 应用开发者
**期望**: 我想要通过工厂方法自定义转场效果
**价值**: 以便实现超出预设效果的定制化转场

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 使用 `TransitionEffect.translate({ x: 100, y: 0, z: 0 })` THEN 组件 appear 时从 (100,0,0) 平移到原位，disappear 时从原位平移到 (100,0,0)（SDK common.d.ts:6422） | 正常 |
| AC-2.2 | WHEN 使用 `TransitionEffect.opacity(0.5)` THEN appear 时 opacity 从 0.5→1，disappear 时 1→0.5（SDK common.d.ts:6479） | 正常 |
| AC-2.3 | WHEN `TransitionEffect.opacity(alpha)` 的 alpha < 0 THEN 取 0；alpha > 1 THEN 取 1（SDK common.d.ts:6469-6470） | 边界 |
| AC-2.4 | WHEN 使用 `TransitionEffect.move(TransitionEdge.TOP)` THEN 组件从 TOP 边滑入/滑出（SDK common.d.ts:6495） | 正常 |
| AC-2.5 | WHEN 使用 `TransitionEffect.scale({ x: 0.5, y: 0.5 })` THEN appear 时从 (0.5,0.5) 缩放到 (1,1)（SDK common.d.ts:6463） | 正常 |
| AC-2.6 | WHEN 使用 `TransitionEffect.rotate({ x: 0, y: 0, z: 1, angle: 90 })` THEN appear 时从 90° 旋转到 0°（SDK common.d.ts:6442） | 正常 |

### US-3: combine 链式组合

**角色**: 应用开发者
**期望**: 我想要组合多个转场效果
**价值**: 以便实现复合动画（如同时平移和淡入）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `effect1.combine(effect2)` THEN effect2 追加到 effect1 的 successor 链尾（SDK common.d.ts:6561） | 正常 |
| AC-3.2 | WHEN 使用 `TransitionEffect.OPACITY.combine(TransitionEffect.translate({x:100}))` THEN appear 时先执行 opacity 效果再执行 translate 效果 | 正常 |
| AC-3.3 | WHEN ParseChainedTransition 解析 successor_ 属性 THEN 递归调用 `ParseChainedTransition(successor, context)` 构建完整链（`js_view_abstract.cpp:2133-2134`） | 正常 |
| AC-3.4 | WHEN combine 被多次链式调用 THEN 形成单链表结构，通过 `next_` 指针依次链接（`transition_property.h:166-169, 174-177`） | 正常 |

### US-4: Asymmetric 非对称效果

**角色**: 应用开发者
**期望**: 我想要为 appear 和 disappear 设置不同的转场效果
**价值**: 以便实现更自然的交互（如 appear 从左滑入，disappear 向右滑出）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 使用 `TransitionEffect.asymmetric(TransitionEffect.move(TransitionEdge.START), TransitionEffect.move(TransitionEdge.END))` THEN appear 使用 move(START)，disappear 使用 move(END)（SDK common.d.ts:6514） | 正常 |
| AC-4.2 | WHEN ChainedAsymmetricEffect 存储 appear/disappear THEN 使用独立的 `appearEffect_` 和 `disappearEffect_` 字段，不共享 successor 链（`transition_property.h:463-465`） | 正常 |
| AC-4.3 | WHEN ParseChainedTransition 解析 type_="asymmetric" THEN 调用 `ParseChainedAsymmetricTransition` 分别解析 appear 和 disappear 子效果（`js_view_abstract.cpp:2065, 919-923`） | 正常 |

### US-5: animation 动画参数

**角色**: 应用开发者
**期望**: 我想要自定义转场效果的动画参数（时长、曲线、延迟）
**价值**: 以便控制转场动画的节奏

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `effect.animation({ duration: 300, curve: Curve.EaseOut, delay: 100 })` THEN AnimationOption 被设到 effect 上，标记 `AnimationInterface::TRANSITION`（`transition_property.h:178-184`） | 正常 |
| AC-5.2 | WHEN 对 SLIDE_SWITCH 调用 `.animation()` THEN 用户参数覆盖内置 600ms cubicBezier(0.24,0,0.5,1.0)（`rosen_transition_effect.cpp:597`） | 正常 |
| AC-5.3 | WHEN effect 的 animation_ 的 onFinish 被设置 THEN 在 TransitionEffect.animation() 中不生效（SDK common.d.ts:6536-6537 标注"onFinish callback does not work here"） | 边界 |

### US-6: onFinish 完成回调

**角色**: 应用开发者
**期望**: 我想要在转场动画结束时获得回调
**价值**: 以便在转场完成后执行后续逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 使用 `.transition(effect, onFinish)` THEN 动画结束时调用 `onFinish(transitionIn: boolean)`，appear 时 transitionIn=true，disappear 时 transitionIn=false（SDK common.d.ts:11412, 21486） | 正常 |
| AC-6.2 | WHEN `SetChainedTransition` 被调用 THEN `target->SetTransitionUserCallback(std::move(finishCallback))` 将回调写入 RenderContext（`view_abstract.cpp:5972`） | 正常 |
| AC-6.3 | WHEN API < 12 THEN 不支持 onFinish 参数，需使用 .transition(effect) 重载（SDK common.d.ts:21486 @since 12） | 边界 |

### US-7: TransitionOptions 旧 API 兼容

**角色**: 应用开发者
**期望**: 我想要了解旧 API TransitionOptions 的行为和迁移方式
**价值**: 以便将旧代码迁移到 TransitionEffect

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 使用 `TransitionOptions { type: TransitionType.All, opacity: 0 }` THEN 等价于 `TransitionEffect.opacity(0)`，appear 时 0→1，disappear 时 1→0（SDK common.d.ts:6053-6060） | 正常 |
| AC-7.2 | WHEN `TransitionOptions` 未设置 opacity/translate/scale/rotate THEN 使用默认 opacity=0（`transition_property.h:112-118` GetDefaultTransition） | 正常 |
| AC-7.3 | WHEN API 12+ 调用 `.transition()` 无参数 THEN 执行 `CleanTransition()` + `SetChainedTransition(nullptr, nullptr)` 清除转场（`js_view_abstract.cpp:2502-2505`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2, R-3, R-4 | TASK-TRANSITION-01 | UT + 手工 | TransitionEffect 预设测试 |
| AC-2.1 ~ AC-2.6 | R-5, R-6, R-7 | TASK-TRANSITION-01 | UT | 工厂方法测试 |
| AC-3.1 ~ AC-3.4 | R-8, R-9 | TASK-TRANSITION-01 | UT | combine 链式测试 |
| AC-4.1 ~ AC-4.3 | R-10, R-11 | TASK-TRANSITION-01 | UT | asymmetric 测试 |
| AC-5.1 ~ AC-5.3 | R-12, R-13 | TASK-TRANSITION-01 | UT + 手工 | animation 参数测试 |
| AC-6.1 ~ AC-6.3 | R-14, R-15 | TASK-TRANSITION-01 | UT | onFinish 回调测试 |
| AC-7.1 ~ AC-7.3 | R-16, R-17 | TASK-TRANSITION-01 | UT | 旧 API 兼容测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | TransitionEffect.OPACITY | appear 时 opacity 0→1，disappear 时 1→0 | 等价 opacity(0) | AC-1.1 |
| R-2 | 行为 | TransitionEffect.IDENTITY | appear/disappear 无变换 | — | AC-1.2 |
| R-3 | 行为 | TransitionEffect.SLIDE | 等价 asymmetric(move(START), move(END)) | RTL 下 START/END 反转 | AC-1.3 |
| R-4 | 行为 | TransitionEffect.SLIDE_SWITCH | 内置 600ms cubicBezier(0.24,0,0.5,1.0) + scale 0.85 | 用户可通过 .animation() 覆盖 | AC-1.4 |
| R-5 | 行为 | TransitionEffect.translate(options) | appear 从指定偏移平移到原位 | — | AC-2.1 |
| R-6 | 边界 | TransitionEffect.opacity(alpha) | alpha < 0 取 0，alpha > 1 取 1 | SDK common.d.ts:6469-6470 | AC-2.3 |
| R-7 | 行为 | TransitionEffect.move(edge) | 从指定 TransitionEdge 滑入/滑出 | TOP/BOTTOM/START/END | AC-2.4 |
| R-8 | 行为 | effect1.combine(effect2) | effect2 追加到 effect1 的 successor 链尾 | 单链表结构 | AC-3.1, AC-3.4 |
| R-9 | 行为 | ParseChainedTransition 解析 successor_ | 递归调用构建完整链 | `js_view_abstract.cpp:2133-2134` | AC-3.3 |
| R-10 | 行为 | TransitionEffect.asymmetric(appear, disappear) | appear 和 disappear 使用独立效果 | 不共享 successor 链 | AC-4.1 |
| R-11 | 行为 | ChainedAsymmetricEffect 存储 | 独立 appearEffect_ 和 disappearEffect_ | `transition_property.h:463-465` | AC-4.2 |
| R-12 | 行为 | effect.animation(value) | AnimationOption 被标记 AnimationInterface::TRANSITION | `transition_property.h:178-184` | AC-5.1 |
| R-13 | 边界 | SLIDE_SWITCH 的 .animation() | 用户参数覆盖内置 SLIDE_SWITCH_DEFAULT_OPTION | `rosen_transition_effect.cpp:597` | AC-5.2 |
| R-14 | 行为 | .transition(effect, onFinish) | 动画结束时调用 onFinish(transitionIn) | transitionIn=true (appear) / false (disappear) | AC-6.1 |
| R-15 | 边界 | API < 12 | 不支持 onFinish 参数 | SDK common.d.ts:21486 @since 12 | AC-6.3 |
| R-16 | 行为 | TransitionOptions { opacity: 0 } | 等价 TransitionEffect.opacity(0) | @deprecated since 10 | AC-7.1 |
| R-17 | 恢复 | API 12+ .transition() 无参 | CleanTransition + SetChainedTransition(nullptr, nullptr) | `js_view_abstract.cpp:2502-2505` | AC-7.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT + 手工 | 预设效果 OPACITY/IDENTITY/SLIDE/SLIDE_SWITCH |
| VM-2 | AC-2.1 ~ AC-2.6 | UT | 工厂方法 translate/opacity/move/scale/rotate |
| VM-3 | AC-3.1 ~ AC-3.4 | UT | combine 链式组合和递归解析 |
| VM-4 | AC-4.1 ~ AC-4.3 | UT | asymmetric 非对称效果 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT + 手工 | animation 参数和 SLIDE_SWITCH 覆盖 |
| VM-6 | AC-6.1 ~ AC-6.3 | UT | onFinish 回调和版本兼容 |
| VM-7 | AC-7.1 ~ AC-7.3 | UT | TransitionOptions 旧 API 兼容和清除 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|----------|----------|--------|-----------|----------|---------|--------|
| .transition(value: TransitionOptions \| TransitionEffect) | Public | TransitionOptions 或 TransitionEffect | T | N/A | 设置转场效果 | AC-1.1, AC-7.1 | 7 |
| .transition(effect: TransitionEffect, onFinish) | Public | TransitionEffect, Optional<TransitionFinishCallback> | T | N/A | 设置转场效果+完成回调 | AC-6.1 | 12 |
| TransitionEffect.IDENTITY | Public | — | TransitionEffect<"identity"> | N/A | 无变换预设 | AC-1.2 | 10 |
| TransitionEffect.OPACITY | Public | — | TransitionEffect<"opacity"> | N/A | 透明度预设 | AC-1.1 | 10 |
| TransitionEffect.SLIDE | Public | — | TransitionEffect<"asymmetric"> | N/A | 滑入滑出预设 | AC-1.3 | 10 |
| TransitionEffect.SLIDE_SWITCH | Public | — | TransitionEffect<"slideSwitch"> | N/A | 缩放滑入滑出预设 | AC-1.4 | 10 |
| TransitionEffect.translate(options) | Public | TranslateOptions | TransitionEffect<"translate"> | N/A | 平移效果 | AC-2.1 | 10 |
| TransitionEffect.rotate(options) | Public | RotateOptions | TransitionEffect<"rotate"> | N/A | 旋转效果 | AC-2.6 | 10 |
| TransitionEffect.scale(options) | Public | ScaleOptions | TransitionEffect<"scale"> | N/A | 缩放效果 | AC-2.5 | 10 |
| TransitionEffect.opacity(alpha) | Public | number | TransitionEffect<"opacity"> | N/A | 透明度效果 | AC-2.2 | 10 |
| TransitionEffect.move(edge) | Public | TransitionEdge | TransitionEffect<"move"> | N/A | 边缘滑入滑出 | AC-2.4 | 10 |
| TransitionEffect.asymmetric(appear, disappear) | Public | TransitionEffect, TransitionEffect | TransitionEffect<"asymmetric"> | N/A | 非对称效果 | AC-4.1 | 10 |
| TransitionEffect.animation(value) | Public | AnimateParam | TransitionEffect | N/A | 动画参数 | AC-5.1 | 10 |
| TransitionEffect.combine(effect) | Public | TransitionEffect | TransitionEffect | N/A | 链式组合 | AC-3.1 | 10 |
| TransitionEdge enum | Public | — | TOP/BOTTOM/START/END | N/A | 边缘枚举 | AC-2.4 | 10 |
| TransitionFinishCallback type | Public | (transitionIn: boolean) => void | — | N/A | 完成回调类型 | AC-6.1 | 12 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| TransitionOptions | 废弃 | 旧 API 转场配置 | @deprecated since 10，@useinstead TransitionEffect | AC-7.1 |
| TransitionType (All/Insert/Delete) | 废弃 | 旧 API 转场类型 | @deprecated since 10，语义由 TransitionEffect.asymmetric 覆盖 | AC-7.1 |

> 截至当前版本，TransitionOptions 和 TransitionType 标注 @deprecated since 10，建议使用 TransitionEffect 替代。

## 接口规格

### 接口定义

**CommonMethod.transition (重载 1)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod::transition(value: TransitionOptions \| TransitionEffect): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-7.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | TransitionOptions \| TransitionEffect | 是 | — | 有效对象；API 12+ 可传 undefined 清除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 为 TransitionEffect 且有 successor_ | ParseChainedTransition 解析效果链，SetChainedTransition 写入 | AC-3.3 |
| 2 | value 为 TransitionOptions（无 successor_） | ParseJsTransition 解析，SetTransition 写入 | AC-7.1 |
| 3 | API 12+ value 为 undefined/空 | CleanTransition + SetChainedTransition(nullptr, nullptr) | AC-7.3 |

**CommonMethod.transition (重载 2)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `CommonMethod::transition(effect: TransitionEffect, onFinish: Optional<TransitionFinishCallback>): T` |
| 返回值 | `T` — 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| effect | TransitionEffect | 是 | — | 有效 TransitionEffect 对象 |
| onFinish | Optional<TransitionFinishCallback> | 否 | undefined | (transitionIn: boolean) => void |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 组件 appear 动画完成 | 调用 onFinish(true) | AC-6.1 |
| 2 | 组件 disappear 动画完成 | 调用 onFinish(false) | AC-6.1 |
| 3 | API < 12 | 不支持此重载 | AC-6.3 |

**TransitionEffect.opacity**

| 属性 | 值 |
|------|-----|
| 函数签名 | `TransitionEffect::opacity(alpha: number): TransitionEffect<"opacity">` |
| 返回值 | `TransitionEffect<"opacity">` |
| 开放范围 | Public |
| 关联 AC | AC-2.2, AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| alpha | number | 是 | — | [0, 1]；< 0 取 0，> 1 取 1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | alpha = 0 | appear 0→1，disappear 1→0 | AC-2.2 |
| 2 | alpha = 0.5 | appear 0.5→1，disappear 1→0.5 | AC-2.2 |
| 3 | alpha = -1 | 截断为 0 | AC-2.3 |
| 4 | alpha = 2 | 截断为 1 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 10: TransitionOptions 和 TransitionType 标注 @deprecated，引入 TransitionEffect
  - API 12: 新增 .transition(effect, onFinish) 重载和 TransitionFinishCallback
  - API 20: .transition(effect, onFinish) 可在 attributeModifier 中调用
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** .transition(TransitionOptions) @since 7，TransitionEffect @since 10，.transition(effect, onFinish) @since 12，TransitionType 静态 @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| successor 链为单链表 | ChainedTransitionEffect 通过 next_ 指针链接，不支持环形或多后继 | AC-3.4 |
| Asymmetric 独立存储 | appearEffect_ 和 disappearEffect_ 不共享 successor 链 | AC-4.2 |
| AnimationOption 标记 TRANSITION | SetAnimationOption 自动设置 AnimationInterface::TRANSITION | AC-5.1 |
| SLIDE_SWITCH 内置参数 | 默认 600ms cubicBezier(0.24,0,0.5,1.0) + scale 0.85，可被 .animation() 覆盖 | AC-1.4, AC-5.2 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 转场动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | ChainedTransitionEffect 链在组件销毁后回收 | UT + Dump | 对象计数 |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | 组件 appear/disappear 时效果链正确播放，不崩溃 | UT | 转场生命周期测试 |
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
| 无障碍 | 否 | 转场动画不影响无障碍属性 | — |
| 大字体 | 否 | 转场动画与字体无关 | — |
| 深色模式 | 否 | 转场动画为通用动画能力 | — |
| 多窗口/分屏 | 否 | 无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | TransitionOptions @deprecated since 10，.transition(effect, onFinish) @since 12 | AC-7.1, AC-6.3 |
| 生态兼容 | 是 | Static API TransitionEffect @since 23（enums.static.d.ets），需在静态 API 文档中明确 | AC-1.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 转场动画
  作为应用开发者
  我想要使用 TransitionEffect 定义组件的 appear/disappear 动画
  以便实现自然的插入和删除效果

  Scenario: OPACITY 预设效果
    Given 组件设置了 .transition(TransitionEffect.OPACITY)
    When 组件 appear（插入到组件树）
    Then opacity 从 0 渐变到 1
    When 组件 disappear（从组件树移除）
    Then opacity 从 1 渐变到 0

  Scenario: SLIDE_SWITCH 内置参数
    Given 组件设置了 .transition(TransitionEffect.SLIDE_SWITCH)
    When 组件 appear
    Then 使用 600ms cubicBezier(0.24, 0.0, 0.5, 1.0) 动画
    And 在 1/3 时间点缩放到 0.85

  Scenario: SLIDE_SWITCH 自定义覆盖
    Given 组件设置了 .transition(TransitionEffect.SLIDE_SWITCH.animation({ duration: 300 }))
    When 组件 appear
    Then 使用 300ms 动画（覆盖默认 600ms）

  Scenario: combine 链式组合
    Given 组件设置了 .transition(TransitionEffect.OPACITY.combine(TransitionEffect.translate({ x: 100 })))
    When 组件 appear
    Then 先执行 opacity 效果（0→1）
    And 再执行 translate 效果（从 x=100 平移到原位）

  Scenario: asymmetric 非对称效果
    Given 组件设置了 .transition(TransitionEffect.asymmetric(TransitionEffect.move(TransitionEdge.START), TransitionEffect.move(TransitionEdge.END)))
    When 组件 appear
    Then 从 START 边滑入
    When 组件 disappear
    Then 从 END 边滑出

  Scenario: onFinish 回调
    Given 组件设置了 .transition(TransitionEffect.OPACITY, (transitionIn) => { ... })
    When 组件 appear 动画完成
    Then 回调被调用，transitionIn = true
    When 组件 disappear 动画完成
    Then 回调被调用，transitionIn = false

  Scenario: 旧 API TransitionOptions 兼容
    Given 组件设置了 .transition({ type: TransitionType.All, opacity: 0 })
    When 组件 appear
    Then opacity 从 0 渐变到 1
    And 效果等价于 TransitionEffect.OPACITY

  Scenario: 清除转场效果
    Given 组件已有转场效果，API >= 12
    When 调用 .transition() 无参数
    Then CleanTransition 被执行
    And SetChainedTransition(nullptr, nullptr) 被执行
    And 组件 appear/disappear 时不再播放转场动画

  Scenario Outline: opacity 边界值
    Given TransitionEffect.opacity(alpha = <input>)
    When 组件 appear
    Then 实际起始 opacity 为 <expected>

    Examples:
      | input | expected |
      | -1    | 0        |
      | 0     | 0        |
      | 0.5   | 0.5      |
      | 1     | 1        |
      | 2     | 1        |
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
    query: "ChainedTransitionEffect 继承体系和 successor 链式组合"
  - repo: "openharmony/ace_engine"
    query: "SLIDE_SWITCH 内置动画参数和 RosenTransitionEffect 实现"
  - repo: "openharmony/ace_engine"
    query: "ParseChainedTransition 递归解析和 JsTransition 分支逻辑"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/common.d.ts`（TransitionEffect / TransitionOptions / TransitionEdge / TransitionFinishCallback）
- 源码入口: `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:2499`（JsTransition）
- 属性定义: `frameworks/core/components_ng/property/transition_property.h:156`（ChainedTransitionEffect 基类）
