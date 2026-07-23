# 特性规格

> Func-07-02-01-Feat-07 SubscribableAbstract 自定义可观察类型：固化 `SubscribableAbstract`（`sdk/subscribable_abstract.ts:67-183`，V1 SDK 抽象基类）的继承约束、`notifyPropertyHasChanged` 通知机制、`addOwningProperty`/`removeOwningProperty` 订阅管理、与 `@State` 装饰器的联动（`setValueInternal` 5 分支之一）、三通知路径（PU TrackedObject / FU 单一 / PU 多个）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SubscribableAbstract 自定义可观察类型 |
| 特性编号 | Func-07-02-01-Feat-07 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 7 起支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 低 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| SubscribableAbstract | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/subscribable_abstract.ts` | — |
| 状态管理概述 | `docs/zh-cn/application-dev/ui/state-management/arkts-state-management-overview.md` | — |

---

## 用户故事

### US-1: 继承 SubscribableAbstract 创建自定义可观察类型

**作为** 应用开发者,
**我想要** 继承 `SubscribableAbstract` 实现自定义可观察类型（如封装外部数据源、数据库游标、传感器数据等）,
**以便** 非 `@Observed` 装饰的复杂对象也能参与 V1 状态管理的依赖收集与 UI 刷新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 应用 `extends SubscribableAbstract`（`subscribable_abstract.ts:67-183`）创建自定义可观察类型 THEN 子类构造器必须调 `super()` 让基类初始化订阅管理 | 正常 |
| AC-1.2 | WHEN 子类管理自身属性 get/set THEN 子类需自行管理属性读写逻辑（基类不提供属性存储） | 正常 |
| AC-1.3 | WHEN 子类可覆盖 `addOwningProperty`/`removeOwningProperty` THEN 添加自定义逻辑（如首个订阅者时连接外部资源，最后一个退订时释放），但 `removeOwningProperty` 必须调 `super` | 正常 |
| AC-1.4 | WHEN SubscribableAbstract 是 V1 SDK 抽象基类 THEN V2 不使用（V2 用 makeObserved 创建可观察对象，归 07-02-03） | 边界 |

### US-2: notifyPropertyHasChanged 通知机制

**作为** 应用开发者,
**我想要** 在子类属性变化时调 `notifyPropertyHasChanged` 通知框架,
**以便** 框架能触发依赖该属性的 UI 重渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 子类属性变化 THEN 子类必须调 `notifyPropertyHasChanged(propName, newValue)`(90) 通知框架 | 正常 |
| AC-2.2 | WHEN `notifyPropertyHasChanged` 执行 THEN 按 PU/FU 路径分三通知路径：PU TrackedObject / FU 单一 / PU 多个（`SubscribableAbstract` 被 @State 持有时按 @State 所在路径） | 正常 |
| AC-2.3 | WHEN 通知仅给参与 UI 的属性 THEN 不参与 UI 的属性无需通知（避免冗余刷新） | 边界 |
| AC-2.4 | WHEN 子类未调 `notifyPropertyHasChanged` THEN 框架无法感知属性变化，UI 不刷新 | 边界 |

### US-3: 与 @State 装饰器联动

**作为** 应用开发者,
**我想要** 用 `@State` 装饰 SubscribableAbstract 子类实例,
**以便** 自定义可观察对象接入 V1 组件状态变量体系。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `@State var: MySubscribable` 装饰 SubscribableAbstract 子类实例 THEN `ObservedPropertyPU.setValueInternal`（`pu_observed_property.ts:90-132`）走 `SubscribableAbstract` 分支，订阅其通知 | 正常 |
| AC-3.2 | WHEN SubscribableAbstract 实例 `notifyPropertyHasChanged` 触发 THEN `@State` 包装类收到通知，经 `notifyPropertyHasChangedPU` 触发依赖 elmtId 重渲染 | 正常 |
| AC-3.3 | WHEN SubscribableAbstract 与 @Observed 区别 THEN 前者需手动调 `notifyPropertyHasChanged`；后者经 ES6 Proxy 自动拦截属性 set（Feat-05） | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 继承 + super |
| AC-1.2 | US-1 | R-1 | 单元测试 自管属性 |
| AC-1.3 | US-1 | R-2 | 单元测试 覆盖订阅管理 |
| AC-1.4 | US-1 | R-1 | 代码审查 V1 专属 |
| AC-2.1 | US-2 | R-3 | 单元测试 notifyPropertyHasChanged |
| AC-2.2 | US-2 | R-3 | 代码审查 三通知路径 |
| AC-2.3 | US-2 | R-3 | 单元测试 仅 UI 属性 |
| AC-2.4 | US-2 | R-3 | 单元测试 未调不刷新 |
| AC-3.1 | US-3 | R-4 | 单元测试 @State 联动 |
| AC-3.2 | US-3 | R-4 | 单元测试 通知触发重渲染 |
| AC-3.3 | US-3 | R-5 | 单元测试 vs @Observed |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `extends SubscribableAbstract`(67-183) 创建自定义可观察类型 | 子类构造器必须调 `super()` 初始化订阅管理；子类自行管理属性 get/set（基类不提供属性存储）；可覆盖 `addOwningProperty`/`removeOwningProperty` 添加自定义逻辑（首个订阅者连接外部资源，最后退订释放），`removeOwningProperty` 必须调 `super`；V1 SDK 抽象基类，V2 不使用（V2 用 makeObserved） | V1 专属 | AC-1.1~AC-1.4 |
| R-2 | 行为 | 子类覆盖订阅管理 | `addOwningProperty` 可覆盖（如连接外部资源）；`removeOwningProperty`/`removeOwningPropertyById` 可覆盖但必须调 `super`（如释放外部资源） | 退订必须调 super 避免悬挂 | AC-1.3 |
| R-3 | 行为 | 子类属性变化调 `notifyPropertyHasChanged(propName, newValue)`(90) | 按 PU/FU 路径分三通知路径（PU TrackedObject / FU 单一 / PU 多个）；仅参与 UI 的属性需通知；未调则框架无法感知，UI 不刷新 | 子类负责通知 | AC-2.1~AC-2.4 |
| R-4 | 行为 | `@State` 装饰 SubscribableAbstract 子类实例 | `ObservedPropertyPU.setValueInternal`(`pu_observed_property.ts:90-132`) 走 `SubscribableAbstract` 分支订阅；实例 `notifyPropertyHasChanged` 触发后 `@State` 包装类经 `notifyPropertyHasChangedPU` 触发依赖 elmtId 重渲染 | @State setValueInternal 5 分支之一（Feat-02 R-5） | AC-3.1, AC-3.2 |
| R-5 | 边界 | SubscribableAbstract 与 @Observed 区别 | 前者需手动调 `notifyPropertyHasChanged`；后者经 ES6 Proxy 自动拦截属性 set（Feat-05）；前者适合封装外部数据源，后者适合普通 class | — | AC-3.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `common_tests/` 继承 + super |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` 自管属性 |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` 覆盖订阅管理 |
| VM-4 | AC-1.4 | 代码审查 | `subscribable_abstract.ts:67-183` V1 专属 |
| VM-5 | AC-2.1 | 单元测试 | `common_tests/` notifyPropertyHasChanged |
| VM-6 | AC-2.2 | 代码审查 | `subscribable_abstract.ts:90` 三通知路径 |
| VM-7 | AC-2.3 | 单元测试 | `common_tests/` 仅 UI 属性 |
| VM-8 | AC-2.4 | 单元测试 | `common_tests/` 未调不刷新 |
| VM-9 | AC-3.1 | 单元测试 | `v1_tests/` @State 联动 |
| VM-10 | AC-3.2 | 单元测试 | `v1_tests/` 通知触发重渲染 |
| VM-11 | AC-3.3 | 单元测试 | `v1_tests/` vs @Observed |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `SubscribableAbstract` | `sdk/subscribable_abstract.ts:67-183` | V1 SDK 抽象基类，供应用实现自定义可观察类型 |
| `notifyPropertyHasChanged` | `sdk/subscribable_abstract.ts:90` | 子类属性变化时通知框架 |
| `addOwningProperty`/`removeOwningProperty` | `sdk/subscribable_abstract.ts` | 订阅管理（子类可覆盖） |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | SubscribableAbstract 引入 | V1 SDK 自定义可观察类型 | 无需迁移；V2 场景用 makeObserved（07-02-03） |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| V1 SDK 抽象基类 | SubscribableAbstract 是 V1 专属；V2 用 makeObserved 创建可观察对象（07-02-03） |
| 手动通知 | 子类必须手动调 `notifyPropertyHasChanged`（区别于 @Observed 的 ES6 Proxy 自动拦截） |
| 子类构造器调 super | 必须调 `super()` 初始化订阅管理 |
| 退订调 super | `removeOwningProperty` 覆盖时必须调 `super` 避免悬挂引用 |
| @State 联动 | SubscribableAbstract 是 @State setValueInternal 5 分支之一（Feat-02 R-5） |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file 信息
- [x] 变更范围 Delta 明确标注为已有实现补录

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/subscribable_abstract.ts:67-183` | `SubscribableAbstract` V1 SDK 抽象基类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/subscribable_abstract.ts:90` | `notifyPropertyHasChanged` 通知方法 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property.ts:90-132` | `ObservedPropertyPU.setValueInternal` @State 联动 5 分支之一 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | SubscribableAbstract 行为回归测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | @State 联动测试 |
