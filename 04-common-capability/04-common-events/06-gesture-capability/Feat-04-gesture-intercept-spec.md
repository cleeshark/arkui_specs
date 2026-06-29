# 特性规格

> Func-04-04-06-Feat-04 手势拦截：固化触摸/手势拦截机制的行为规格，覆盖 Hit Test 层（hitTestBehavior/onTouchIntercept/onChildTouchTest）、手势收集层（onGestureCollectIntercept）、手势识别层（preventBegin/TouchRestrict）、事件响应层（monopolizeEvents/ResponseCtrl）、原始事件层（onTouch）。仅 NG 框架。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手势拦截 (Gesture Intercept) |
| 特性编号 | Func-04-04-06-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8（hitTestBehavior/onTouch），API 11（onTouchIntercept），API 12（monopolizeEvents/onGestureCollectIntercept/onChildTouchTest） |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/06-gesture-capability/design.md` | Baselined |
| Feat-01 基础手势 | `specs/04-common-capability/04-common-events/06-gesture-capability/Feat-01-basic-gestures-spec.md` | Baselined |
| Feat-03 手势判定 | `specs/04-common-capability/04-common-events/06-gesture-capability/Feat-03-gesture-referee-spec.md` | Baselined |

---

## 用户故事

### US-1: hitTestBehavior 控制触摸测试行为

**作为** 应用开发者,
**我想要** 通过 `.hitTestBehavior(mode)` 控制组件及其子组件是否参与触摸测试,
**以便** 精确控制哪些组件可以接收触摸事件。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-1.1 | WHEN 设置 `HitTestMode.Default` THEN 自身和子组件参与触摸测试，但屏蔽被标记的节点 |
| AC-1.2 | WHEN 设置 `HitTestMode.Block` THEN 自身响应触摸，阻止子组件和被标记节点参与 |
| AC-1.3 | WHEN 设置 `HitTestMode.Transparent` THEN 自身和子组件参与触摸测试，不屏蔽被标记节点 |
| AC-1.4 | WHEN 设置 `HitTestMode.None` THEN 自身不响应触摸事件，子组件正常响应 |
| AC-1.5 | WHEN 设置 `HitTestMode.BlockHierarchy` THEN 阻止所有低优先级兄弟节点和父节点接收触摸 |
| AC-1.6 | WHEN 设置 `HitTestMode.BlockDescendants` THEN 自身和所有后代节点均不响应触摸事件 |
| AC-1.7 | WHEN 设置 `HitTestMode.TransparentSelf` THEN 根据触摸事件是否被消费动态决定自身透明性 |

### US-2: onTouchIntercept 动态拦截触摸

**作为** 应用开发者,
**我想要** 通过 `.onTouchIntercept(callback)` 在触摸测试阶段动态决定组件的命中测试模式,
**以便** 根据触摸事件信息（如手指数量、位置）动态决定是否拦截触摸。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-2.1 | WHEN 设置 `onTouchIntercept` 回调 THEN 在每次触摸测试时调用回调，传入 TouchEventInfo |
| AC-2.2 | WHEN 回调返回 `HitTestMode.None` THEN 组件不接收该触摸事件 |
| AC-2.3 | WHEN 回调返回 `HitTestMode.Block` THEN 组件拦截触摸，子组件不接收 |
| AC-2.4 | WHEN 未设置 `onTouchIntercept` THEN 使用静态 `hitTestBehavior` 值 |
| AC-2.5 | WHEN 回调返回值与静态 `hitTestBehavior` 冲突 THEN `onTouchIntercept` 返回值优先 |

### US-3: onGestureCollectIntercept 手势收集拦截

**作为** 应用开发者,
**我想要** 通过 `.onGestureCollectIntercept(callback)` 在手势收集阶段拦截手势传递,
**以便** 控制手势在组件层级中的传播方向。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-3.1 | WHEN 回调返回 `GestureCollectIntervention.CONTINUE` THEN 不做干预，手势正常收集 |
| AC-3.2 | WHEN 回调返回 `GestureCollectIntervention.DISCARD_LOWER` THEN 阻止手势向祖先组件冒泡 |
| AC-3.3 | WHEN 回调返回 `GestureCollectIntervention.DISCARD_HIGHER` THEN 丢弃所有已收集的目标 |
| AC-3.4 | WHEN 回调返回 `GestureCollectIntervention.DISCARD_SELF` THEN 丢弃自身但保留子组件的手势 |
| AC-3.5 | WHEN 回调返回 `GestureCollectIntervention.DISCARD_LOWER_PRIORITY_SIBLINGS` THEN 阻止低优先级的兄弟节点 |

### US-4: onChildTouchTest 子组件触摸控制

**作为** 应用开发者,
**我想要** 通过 `.onChildTouchTest(callback)` 控制子组件的触摸分发,
**以便** 父组件可以根据触摸信息决定哪些子组件接收触摸。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-4.1 | WHEN 设置 `onChildTouchTest` 回调 THEN 在子组件触摸测试时调用，传入子组件的 TouchTestInfo 数组 |
| AC-4.2 | WHEN 回调返回 TouchResult THEN 根据返回值决定子组件的触摸分发 |

### US-5: monopolizeEvents 首节点独占

**作为** 应用开发者,
**我想要** 通过 `.monopolizeEvents(true)` 确保只有第一个响应触摸的组件继续接收后续事件,
**以便** 避免多个组件同时响应同一触摸序列。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-5.1 | WHEN 设置 `monopolizeEvents(true)` THEN 第一个成功响应触摸事件的组件（通过 ResponseCtrl 记录）独占后续事件 |
| AC-5.2 | WHEN 首节点已确定后其他节点尝试响应 THEN `ResponseCtrl::ShouldResponse()` 返回 false，阻止其他节点 |
| AC-5.3 | WHEN 设置 `monopolizeEvents(false)`（默认）THEN 所有命中组件均可响应触摸事件 |

### US-6: preventBegin 阻止手势开始

**作为** 手势框架,
**我想要** 通过 `preventBegin_` 标志阻止识别器开始手势识别,
**以便** 在特定条件下禁用某个手势识别器。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-6.1 | WHEN 识别器的 `preventBegin_==true` THEN `HandleEvent()` 检查到 IsPreventBegin() 返回 true 后直接返回，不处理触摸事件 |
| AC-6.2 | WHEN `preventBegin_` 从 true 变为 false THEN 识别器恢复正常的触摸事件处理 |

### US-7: TouchRestrict 触摸类型限制

**作为** 手势框架,
**我想要** 通过 TouchRestrict 位标志限制可识别的手势类型,
**以便** 根据触摸输入源类型过滤不需要的手势。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-7.1 | WHEN TouchRestrict 包含 CLICK 位 THEN 点击类手势（ClickRecognizer）被限制 |
| AC-7.2 | WHEN TouchRestrict 包含 LONG_PRESS 位 THEN 长按手势被限制 |
| AC-7.3 | WHEN TouchRestrict 包含方向标志（SWIPE_LEFT/RIGHT/UP/DOWN）THEN 对应方向的滑动手势被限制 |

### US-8: onTouch 原始触摸事件

**作为** 应用开发者,
**我想要** 通过 `.onTouch(callback)` 直接处理原始触摸事件,
**以便** 在手势识别之前消费或响应触摸。

| AC ID | WHEN/THEN |
|-------|-----------|
| AC-8.1 | WHEN 设置 `onTouch` 回调 THEN 在触摸事件到达手势识别器之前触发回调 |
| AC-8.2 | WHEN onTouch 回调中消费了事件 THEN 后续手势识别可能受到影响 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.7 | R-1, R-9~R-15 | 已有实现 | 单测/XTS | `test/unittest/core/event/` |
| AC-2.1~2.5 | R-2, R-16~R-20 | 已有实现 | 单测/XTS | 同上 |
| AC-3.1~3.5 | R-3, R-21~R-25 | 已有实现 | 单测 | 同上 |
| AC-4.1~4.2 | R-4, R-26~R-27 | 已有实现 | 单测 | 同上 |
| AC-5.1~5.3 | R-5, R-28~R-30 | 已有实现 | 单测 | 同上 |
| AC-6.1~6.2 | R-6, R-31~R-32 | 已有实现 | 单测 | 同上 |
| AC-7.1~7.3 | R-7, R-33~R-35 | 已有实现 | 单测 | 同上 |
| AC-8.1~8.2 | R-8, R-36~R-37 | 已有实现 | 单测 | 同上 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 静态设置，在触摸测试阶段生效 | hitTestBehavior 有 7 种模式，每种决定组件自身和后代是否参与触摸测试及是否屏蔽其他节点 | — | AC-1.1~1.7 |
| R-2 | 行为 | 回调在触摸测试时动态调用 | onTouchIntercept 回调返回值优先于静态 hitTestBehavior | — | AC-2.1~2.5 |
| R-3 | 行为 | 回调在手势层级构建后、事件分发前执行 | onGestureCollectIntercept 有 5 种干预策略，在手势收集阶段执行 | — | AC-3.1~3.5 |
| R-4 | 行为 | 回调在子组件触摸测试时执行 | onChildTouchTest 允许父组件根据触摸信息控制子组件分发 | — | AC-4.1~4.2 |
| R-5 | 行为 | 仅当 monopolizeEvents=true 时 ResponseCtrl 生效 | monopolizeEvents 通过 ResponseCtrl 实现首节点独占，独占范围为一个触摸序列 | — | AC-5.1~5.3 |
| R-6 | 行为 | 识别器内部标志 | preventBegin 阻止识别器处理触摸事件，但不清除已设置的回调 | — | AC-6.1~6.2 |
| R-7 | 行为 | 从父组件传递到子组件 | TouchRestrict 使用位标志组合，可同时限制多种手势类型 | — | AC-7.1~7.3 |
| R-8 | 行为 | 回调在事件分发管线早期 | onTouch 回调在手势识别器之前执行，可消费原始触摸事件 | — | AC-8.1~8.2 |
| R-9 | 行为 | 触摸测试阶段 | HitTestMode.Default 下自身和子组件参与触摸测试 | FrameNode | AC-1.1 |
| R-10 | 行为 | 触摸测试阶段 | HitTestMode.Block 阻止子组件参与，仅自身响应 | FrameNode | AC-1.2 |
| R-11 | 行为 | 触摸测试阶段 | HitTestMode.Transparent 允许穿透到被标记节点 | FrameNode | AC-1.3 |
| R-12 | 行为 | 触摸测试阶段 | HitTestMode.None 自身不响应但子组件正常 | FrameNode | AC-1.4 |
| R-13 | 行为 | 触摸测试阶段 | HitTestMode.BlockHierarchy 阻止低优先级兄弟和父节点 | FrameNode | AC-1.5 |
| R-14 | 行为 | 触摸测试阶段 | HitTestMode.BlockDescendants 阻止自身和所有后代 | FrameNode | AC-1.6 |
| R-15 | 行为 | 触摸测试阶段 | HitTestMode.TransparentSelf 根据事件消费状态动态决定 | FrameNode | AC-1.7 |
| R-16 | 行为 | 触摸测试阶段 | onTouchIntercept 回调在 ProcessTouchTestHit 时调用 | GestureEventHub | AC-2.1 |
| R-17 | 行为 | 回调返回 | 回调返回 HitTestMode.None 时组件不接收该触摸 | GestureEventHub | AC-2.2 |
| R-18 | 行为 | 回调返回 | 回调返回 HitTestMode.Block 时组件拦截触摸 | GestureEventHub | AC-2.3 |
| R-19 | 行为 | 无回调 | 未设置回调时使用静态 hitTestBehavior 值 | GestureEventHub | AC-2.4 |
| R-20 | 行为 | 两者同时设置 | onTouchIntercept 返回值优先于静态 hitTestBehavior | GestureEventHub | AC-2.5 |
| R-21 | 行为 | 回调返回 CONTINUE | GestureCollectIntervention.CONTINUE 不干预手势收集 | GestureEventHub | AC-3.1 |
| R-22 | 行为 | 回调返回 | DISCARD_LOWER 阻止手势向祖先冒泡 | GestureEventHub | AC-3.2 |
| R-23 | 行为 | 回调返回 | DISCARD_HIGHER 丢弃所有已收集目标 | GestureEventHub | AC-3.3 |
| R-24 | 行为 | 回调返回 | DISCARD_SELF 丢弃自身保留子组件 | GestureEventHub | AC-3.4 |
| R-25 | 行为 | 回调返回 | DISCARD_LOWER_PRIORITY_SIBLINGS 阻止低优先级兄弟 | GestureEventHub | AC-3.5 |
| R-26 | 行为 | 触摸测试 | onChildTouchTest 在子组件触摸测试时调用 | GestureEventHub | AC-4.1 |
| R-27 | 行为 | 回调返回 | 回调返回 TouchResult 决定子组件分发策略 | GestureEventHub | AC-4.2 |
| R-28 | 行为 | 手势 AboutToAccept | monopolizeEvents=true 时 ResponseCtrl 记录首个响应节点 | ResponseCtrl | AC-5.1 |
| R-29 | 行为 | 手势响应阶段 | ShouldResponse() 检查当前节点是否为首节点，非首节点返回 false | ResponseCtrl | AC-5.2 |
| R-30 | 行为 | 默认行为 | monopolizeEvents=false 时所有命中组件均可响应 | ResponseCtrl | AC-5.3 |
| R-31 | 行为 | 触摸事件到达 | preventBegin_=true 时 HandleEvent 直接返回 true | NGGestureRecognizer | AC-6.1 |
| R-32 | 行为 | 标志变更 | preventBegin_ 变为 false 后恢复正常处理 | NGGestureRecognizer | AC-6.2 |
| R-33 | 行为 | 触摸测试 | TouchRestrict CLICK 位阻止 ClickRecognizer | TouchRestrict | AC-7.1 |
| R-34 | 行为 | 触摸测试 | TouchRestrict LONG_PRESS 位阻止 LongPressRecognizer | TouchRestrict | AC-7.2 |
| R-35 | 行为 | 触摸测试 | TouchRestrict 方向位阻止对应方向的 SwipeRecognizer | TouchRestrict | AC-7.3 |
| R-36 | 行为 | 触摸事件到达 | onTouch 回调在触摸事件分发早期触发 | TouchEvent | AC-8.1 |
| R-37 | 行为 | 回调中消费 | onTouch 回调消费事件后影响后续手势识别 | TouchEvent | AC-8.2 |
| R-38 | 异常 | 无回调 | onTouchIntercept 回调未设置 | 使用静态 hitTestBehavior | AC-2.4 |
| R-39 | 异常 | 未开启独占 | monopolizeEvents=false（默认） | 所有命中组件均可响应 | AC-5.3 |
| R-40 | 异常 | 未阻止 | preventBegin_=false（默认） | 正常处理触摸事件 | AC-6.2 |
| R-41 | 异常 | 无限制 | TouchRestrict=NONE | 所有手势类型均可识别 | AC-7.1~7.3 |
| R-42 | 恢复 | hitTestBehavior 从 Block 恢复为 Default | 后续触摸测试中子组件重新参与 | 子组件恢复响应 | — |
| R-43 | 恢复 | monopolizeEvents 独占节点在触摸序列结束后 | ResponseCtrl 重置首节点记录 | 下一触摸序列可重新选择首节点 | — |
| R-44 | 恢复 | preventBegin 从 true 变为 false | 识别器恢复正常处理 | 后续触摸事件正常处理 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-9~R-15, AC-1.1~1.7 | 单测/XTS | hitTestBehavior 7 种模式正确 |
| VM-2 | R-16~R-20, AC-2.1~2.5 | 单测 | onTouchIntercept 动态返回值生效 |
| VM-3 | R-21~R-25, AC-3.1~3.5 | 单测 | onGestureCollectIntercept 5 种干预策略 |
| VM-4 | R-26~R-27, AC-4.1~4.2 | 单测 | onChildTouchTest 子组件分发控制 |
| VM-5 | R-28~R-30, AC-5.1~5.3 | 单测 | monopolizeEvents 首节点独占 |
| VM-6 | R-31~R-32, AC-6.1~6.2 | 单测 | preventBegin 阻止和恢复 |
| VM-7 | R-33~R-35, AC-7.1~7.3 | 单测 | TouchRestrict 位标志过滤 |
| VM-8 | R-36~R-37, AC-8.1~8.2 | 单测 | onTouch 原始事件消费 |
| VM-9 | 全量 | XTS/集成 | 端到端拦截场景正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能描述 | @since | 关联 AC |
|----------|------|----------|--------|---------|
| `hitTestBehavior(value: HitTestMode): T` | Public | 设置触摸测试行为模式 | 8 | AC-1.1~1.7 |
| `onTouchIntercept(callback: (event: TouchEvent) => HitTestMode): T` | Public | 动态拦截触摸回调 | 11 | AC-2.1~2.5 |
| `onGestureCollectIntercept(callback: GestureCollectInterceptCallback): T` | Public | 手势收集阶段拦截 | 12 | AC-3.1~3.5 |
| `onChildTouchTest(callback: (value: Array\<TouchTestInfo\>) => TouchResult): T` | Public | 子组件触摸测试控制 | 12 | AC-4.1~4.2 |
| `monopolizeEvents(monopolize: boolean): T` | Public | 首节点独占事件 | 12 | AC-5.1~5.3 |
| `onTouch(event: (event: TouchEvent) => void): T` | Public | 原始触摸事件回调 | 7 | AC-8.1~8.2 |

**关联枚举类型：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `HitTestMode` | `{ Default, Block, Transparent, None, BlockHierarchy, BlockDescendants, TransparentSelf }` | `common.d.ts` |
| `GestureCollectIntervention` | `{ CONTINUE, DISCARD_LOWER, DISCARD_HIGHER, DISCARD_SELF, DISCARD_LOWER_PRIORITY_SIBLINGS }` | `common.d.ts` |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

---

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7（onTouch），API 8（hitTestBehavior），API 11（onTouchIntercept），API 12（monopolizeEvents/onGestureCollectIntercept/onChildTouchTest）
- **API 版本号策略:** 各 API 按 @since 标注版本，新增 API 为新增重载

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 拦截分层执行 | Hit Test → 手势收集 → 手势识别 → 事件响应，各层有序执行 | 全部 |
| onTouchIntercept 优先于静态 hitTestBehavior | 动态回调覆盖静态配置 | AC-2.5 |
| ResponseCtrl 每触摸序列独立 | 首节点记录在触摸序列结束时重置 | AC-5.1~5.3 |
| TouchRestrict 从父向子传递 | 父组件的限制传递到子组件的手势识别器 | AC-7.1~7.3 |

> 架构规则适用性及设计方案见 design.md。

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | onTouchIntercept 回调执行 < 100μs | benchmark | — |
| 安全 | N/A — 无权限要求 | — | — |
| 可靠性 | hitTestBehavior 变更在下一帧生效 | 单测 | — |

---

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
| 无障碍 | 是 | HitTestMode.None 可能影响无障碍焦点 | hitTestBehavior 设为 None 的组件 |
| 大字体 | N/A | 拦截机制与字体无关 | — |
| 深色模式 | N/A | 拦截机制与颜色无关 | — |
| 多窗口/分屏 | 是 | 分屏后各窗口独立触摸测试 | 多窗口下拦截行为正确 |
| 版本升级 | 是 | 各 API @since 版本不同，需注意版本兼容 | API 12 新增 API 较多 |

---

## 行为场景（可选，Gherkin）

```gherkin
Feature: 手势拦截
  作为 应用开发者
  我想要 通过多种拦截机制控制触摸和手势的分发
  以便 精确控制组件的触摸响应行为

  # ─── hitTestBehavior ─────────────────────────────

  Scenario: Block 阻止子组件
    Given 一个 Stack 容器设置 hitTestBehavior(Block)
    And 子组件绑定了 TapGesture
    When 用户点击子组件区域
    Then Stack 自身响应触摸
    And 子组件不接收触摸事件

  Scenario: None 自身不响应
    Given 一个组件设置 hitTestBehavior(None)
    And 子组件绑定了 TapGesture
    When 用户点击组件区域
    Then 组件自身不响应触摸
    And 子组件正常接收触摸并识别手势

  Scenario: Transparent 允许穿透
    Given 上层组件设置 hitTestBehavior(Transparent)
    And 下层被标记的组件绑定了 TapGesture
    When 用户点击重叠区域
    Then 下层被标记的组件接收触摸事件

  Scenario: BlockDescendants 阻止所有后代
    Given 一个容器设置 hitTestBehavior(BlockDescendants)
    And 多层嵌套的子组件绑定了手势
    When 用户点击任意子组件区域
    Then 容器和所有子组件均不响应

  # ─── onTouchIntercept ────────────────────────────

  Scenario: 动态拦截-单指穿透多指拦截
    Given 一个组件设置了 onTouchIntercept
    And 回调逻辑：单指返回 Transparent，多指返回 Block
    When 用户单指触摸
    Then 回调返回 Transparent，触摸穿透到下层
    When 用户双指触摸
    Then 回调返回 Block，组件拦截触摸

  Scenario: onTouchIntercept 优先于静态值
    Given 组件静态 hitTestBehavior=None
    And 设置了 onTouchIntercept 返回 Block
    When 用户触摸
    Then 使用回调返回的 Block（优先于静态 None）

  # ─── onGestureCollectIntercept ───────────────────

  Scenario: DISCARD_LOWER 阻止冒泡
    Given 子组件设置了 onGestureCollectIntercept 返回 DISCARD_LOWER
    And 父组件绑定了 TapGesture
    When 子组件的手势收集完成
    Then 手势不向父组件冒泡
    And 父组件的 TapGesture 不触发

  Scenario: DISCARD_SELF 丢弃自身
    Given 组件设置了 onGestureCollectIntercept 返回 DISCARD_SELF
    And 组件绑定了 TapGesture
    When 手势收集时回调返回 DISCARD_SELF
    Then 组件自身的手势被丢弃
    And 子组件的手势保留

  # ─── monopolizeEvents ────────────────────────────

  Scenario: 首节点独占
    Given 两个重叠组件均设置 monopolizeEvents(true)
    And 均绑定了 TapGesture
    When 用户点击重叠区域
    Then 第一个响应的组件独占后续事件
    And 另一个组件的手势被阻止

  # ─── preventBegin ────────────────────────────────

  Scenario: 阻止手势开始
    Given 一个识别器设置 preventBegin_=true
    When 触摸事件到达识别器
    Then HandleEvent 直接返回 true
    And 识别器不处理触摸事件

  # ─── TouchRestrict ──────────────────────────────

  Scenario: 限制点击手势
    Given 父组件传递 TouchRestrict 包含 CLICK 位
    And 子组件绑定了 TapGesture
    When 用户点击子组件
    Then ClickRecognizer 被限制，不识别点击手势
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（5 层 9 种拦截机制；不含手势仲裁逻辑（Feat-03）、手势识别算法（Feat-01））
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "HitTestMode hitTestBehavior onTouchIntercept ProcessTouchTestHit"
  - repo: "openharmony/ace_engine"
    query: "onGestureCollectIntercept GestureCollectIntervention DISCARD"
  - repo: "openharmony/ace_engine"
    query: "monopolizeEvents ResponseCtrl ShouldResponse TrySetFirstResponse"
  - repo: "openharmony/ace_engine"
    query: "preventBegin IsPreventBegin TouchRestrict onChildTouchTest"
```

**关键文档：**
- SDK API 类型定义：`interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 架构设计：`specs/04-common-capability/04-common-events/06-gesture-capability/design.md`
