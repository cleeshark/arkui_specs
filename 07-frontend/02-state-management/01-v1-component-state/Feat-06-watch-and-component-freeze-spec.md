# 特性规格

> Func-07-02-01-Feat-06 @Watch 变更回调与组件冻结：固化 `@Watch`（变量变化回调，`ViewPU.declareWatch`/`watchedProps`/`delayedWatchedProps_` 双触发路径）、组件冻结三态机（`DelayedNotifyChangesEnum`：`do_not_delay`/`delay_none_pending`/`delay_notification_pending`）、`freezeWhenInactive` 配置与继承、冻结触发场景（router/TabContent/LazyForEach/Navigation/组件复用/混用）、冻结期状态变更暂存与激活时 `performDelayedUpdate` 回放行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Watch 变更回调与组件冻结 |
| 特性编号 | Func-07-02-01-Feat-06 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | @Watch API 7 起；组件冻结（`freezeWhenInactive`）API 11 起；混用场景改进（父解冻只解冻子屏上节点）API 18 起；BuilderNode `inheritFreezeOptions` API 20 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| ViewPU（@Watch 注册） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | — |
| ObservedPropertyAbstractPU（冻结三态机） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts` | — |
| PUV2ViewBase（freezeWhenInactive 继承） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts` | — |
| @Watch 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-watch.md` | — |
| 组件冻结开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-freeze.md` | — |

---

## 用户故事

### US-1: @Watch 变量变化回调

**作为** 应用开发者,
**我想要** 用 `@Watch` 监听状态变量的变化并执行自定义回调,
**以便** 在变量变化时执行副作用逻辑（如联动其他变量、记录日志）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在状态变量上叠加 `@Watch('onChange')` THEN `ViewPU.declareWatch`（`pu_view.ts:844-846`）将变量名 → 回调方法名映射注册到 `watchedProps` | 正常 |
| AC-1.2 | WHEN 被监听的状态变量真正变化（严格相等 `===` 为 false）THEN 框架触发 @Watch 回调，参数为被 watch 的属性名 | 正常 |
| AC-1.3 | WHEN @Watch 方法执行 THEN 在自定义组件的属性变更之后同步执行 | 正常 |
| AC-1.4 | WHEN 状态变量第一次初始化 THEN @Watch 方法不会被调用（初始化不算状态变量改变） | 边界 |
| AC-1.5 | WHEN @Watch 仅能监听可以观察到的变化 THEN 无法观察的变化（如嵌套对象第二层属性，未用 @Observed）不触发 @Watch | 边界 |
| AC-1.6 | WHEN 多个状态变量绑定同一个 @Watch 回调方法 THEN 通过 `changedPropertyName` 参数区分被 watch 的属性 | 正常 |

### US-2: @Watch 双触发路径与触发时机

**作为** 应用开发者,
**我想要** 了解 @Watch 在不同装饰器路径下的触发时机,
**以便** 正确预期回调执行时间。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN @State/@Prop/@Link/@ObjectLink 等变量变化 THEN 经 `viewPropertyHasChanged`（`pu_view.ts:682-734`）路径标记 dirty 后触发 @Watch | 正常 |
| AC-2.2 | WHEN @Provide 变量变化 THEN 经 `__notifyDecoratedWatch__Internal` 路径触发 @Watch（含冻结延迟处理） | 正常 |
| AC-2.3 | WHEN @Link 状态更新 THEN 同步执行，状态变化立刻触发 @Watch | 正常 |
| AC-2.4 | WHEN @ObjectLink/@Prop 的更新 THEN 依赖父组件同步，触发时间略晚于 @Link | 边界 |
| AC-2.5 | WHEN 在 @Watch 方法里改变其他状态变量 THEN 引起状态变更和 @Watch 执行（注意避免无限循环） | 边界 |

### US-3: @Watch 声明约束

**作为** 应用开发者,
**我想要** 了解 @Watch 的声明约束,
**以便** 正确使用 @Watch 避免编译错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN @Watch 参数非 string 类型 THEN 编译期报错，参数必须是常量字符串（带引号） | 异常 |
| AC-3.2 | WHEN @Watch 参数引用的方法未声明 THEN 编译期报错，参数必须是 `(string) => void` 自定义成员函数的方法引用 | 异常 |
| AC-3.3 | WHEN @Watch 监听常规变量（非状态变量装饰器装饰）THEN 编译期报错，常规变量不能被 @Watch 装饰 | 异常 |
| AC-3.4 | WHEN @Watch 回调函数签名 THEN 为 `(changedPropertyName?: string) => void`，`changedPropertyName` 是被 watch 的属性名 | 正常 |
| AC-3.5 | WHEN @Watch 与其他装饰器组合 THEN 可与所有 V1 状态变量装饰器（@State/@Prop/@Link/@Provide/@Consume/@ObjectLink/@StorageLink 等）组合；装饰器顺序不影响实际功能 | 正常 |

### US-4: 组件冻结配置与触发场景

**作为** 应用开发者,
**我想要** 用 `@Component({ freezeWhenInactive: true })` 配置组件冻结，使非激活组件不响应状态变更,
**以便** 提升不可见组件的性能，避免无效刷新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `@Component({ freezeWhenInactive: true })` 配置激活 THEN 组件进入 inactive 状态时，状态变量变化不触发 UI 刷新和 @Watch 回调 | 正常 |
| AC-4.2 | WHEN 子组件未设置 `freezeWhenInactive` THEN 继承父组件的冻结配置（`puv2_view_base.ts`） | 正常 |
| AC-4.3 | WHEN 页面路由（router）非栈顶不可见页面 THEN 该页面自定义组件为 inactive | 正常 |
| AC-4.4 | WHEN TabContent 非当前显示 THEN 该 TabContent 中的自定义组件为 inactive | 正常 |
| AC-4.5 | WHEN LazyForEach 缓存节点中的组件 THEN 为 inactive（屏上节点为 active） | 正常 |
| AC-4.6 | WHEN Navigation 未显示的 NavDestination 中的自定义组件 THEN 为 inactive | 正常 |
| AC-4.7 | WHEN 组件复用进入复用池的组件 THEN 为 inactive；从复用池上树的节点为 active | 正常 |
| AC-4.8 | WHEN 组件 active/inactive 状态 THEN 不等同于其可见性；冻结仅适用于 router/TabContent/LazyForEach/Navigation/组件复用/混用 6 类场景 | 边界 |

### US-5: 冻结状态变更暂存与回放

**作为** 应用开发者,
**我想要** 冻结期间的状态变更被暂存，组件重新激活时回放,
**以便** 状态不丢失，激活后 UI 与状态一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 组件 active 时 `DelayedNotifyChangesEnum` 为 `do_not_delay`(0) THEN 状态变更立即通知 | 正常 |
| AC-5.2 | WHEN 组件进入 inactive（`setActiveInternal(false)`，`pu_view.ts:483-522`）THEN `delayedNotification_` 切换为 `delay_none_pending`(1)，暂无待处理变更 | 正常 |
| AC-5.3 | WHEN 组件 inactive 时状态变量变更 THEN `delayedNotification_` 切换为 `delay_notification_pending`(2)，暂存待处理 elmtId | 正常 |
| AC-5.4 | WHEN 组件继续 inactive 且继续变更 THEN 累积暂存更多 elmtId | 正常 |
| AC-5.5 | WHEN 组件由 inactive 变为 active（`setActiveInternal(true)`）THEN `performDelayedUpdate` 统一回放暂存的 elmtId，重新刷新冻结期间的状态变量，@Watch 回调被再次调用 | 正常 |
| AC-5.6 | WHEN API 17 及以下父组件解冻 THEN 解冻子组件所有节点 | 边界 |
| AC-5.7 | WHEN API 18+ 父组件解冻 THEN 只解冻子组件的屏上节点（混用场景改进） | 边界 |
| AC-5.8 | WHEN 页面生命周期 `OnPageShow` THEN 当前 Page 根节点设为 active（灭屏亮屏也会触发，影响 LazyForEach） | 正常 |

### US-6: 冻结与组件复用混用例外

**作为** 应用开发者,
**我想要** 了解冻结与组件复用混用时的特殊行为,
**以便** 正确预期 @Watch 回调触发。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 组件复用与冻结混用，子组件从复用池被复用（上树）THEN 重新标记为 active，但不会触发 @Watch 回调 | 边界 |
| AC-6.2 | WHEN 复用时执行脏节点刷新 THEN 包括冻结期间延迟刷新的变量绑定的系统组件，并清空脏节点列表 | 正常 |
| AC-6.3 | WHEN 解冻时判断冻结期间无变量改变 THEN 不触发 @Watch（复用已清空脏节点列表） | 边界 |
| AC-6.4 | WHEN `aboutToReuse` 中改值 THEN 解冻时同样不触发 @Watch | 边界 |
| AC-6.5 | WHEN API 20+ BuilderNode 配置 `inheritFreezeOptions: true` THEN BuilderNode 继承父组件冻结能力（API 20 前 BuilderNode 无法继承冻结） | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Watch 注册 |
| AC-1.2 | US-1 | R-2 | 单元测试 变化触发回调 |
| AC-1.3 | US-1 | R-2 | 单元测试 同步执行 |
| AC-1.4 | US-1 | R-3 | 单元测试 初始化不触发 |
| AC-1.5 | US-1 | R-4 | 单元测试 仅观察到的变化 |
| AC-1.6 | US-1 | R-1 | 单元测试 多变量共享回调 |
| AC-2.1 | US-2 | R-5 | 单元测试 viewPropertyHasChanged 路径 |
| AC-2.2 | US-2 | R-5 | 单元测试 __notifyDecoratedWatch__Internal 路径 |
| AC-2.3 | US-2 | R-6 | 单元测试 @Link 同步触发 |
| AC-2.4 | US-2 | R-6 | 单元测试 @ObjectLink/@Prop 延迟 |
| AC-2.5 | US-2 | R-7 | 单元测试 链式触发 |
| AC-3.1 | US-3 | R-8 | 编译期校验 |
| AC-3.2 | US-3 | R-8 | 编译期校验 |
| AC-3.3 | US-3 | R-9 | 编译期校验 |
| AC-3.4 | US-3 | R-1 | 单元测试 回调签名 |
| AC-3.5 | US-3 | R-10 | 单元测试 装饰器组合 |
| AC-4.1 | US-4 | R-11 | 单元测试 freezeWhenInactive |
| AC-4.2 | US-4 | R-12 | 单元测试 配置继承 |
| AC-4.3 | US-4 | R-13 | 单元测试 router 场景 |
| AC-4.4 | US-4 | R-13 | 单元测试 TabContent 场景 |
| AC-4.5 | US-4 | R-13 | 单元测试 LazyForEach 场景 |
| AC-4.6 | US-4 | R-13 | 单元测试 Navigation 场景 |
| AC-4.7 | US-4 | R-13 | 单元测试 组件复用场景 |
| AC-4.8 | US-4 | R-13 | 单元测试 active≠可见性 |
| AC-5.1 | US-5 | R-14 | 单元测试 do_not_delay |
| AC-5.2 | US-5 | R-14 | 单元测试 delay_none_pending |
| AC-5.3 | US-5 | R-14 | 单元测试 delay_notification_pending |
| AC-5.4 | US-5 | R-14 | 单元测试 累积暂存 |
| AC-5.5 | US-5 | R-15 | 单元测试 performDelayedUpdate 回放 |
| AC-5.6 | US-5 | R-16 | 单元测试 API 17 全节点解冻 |
| AC-5.7 | US-5 | R-16 | 单元测试 API 18 屏上节点解冻 |
| AC-5.8 | US-5 | R-17 | 单元测试 OnPageShow |
| AC-6.1 | US-6 | R-18 | 单元测试 复用上树不触发 @Watch |
| AC-6.2 | US-6 | R-18 | 单元测试 复用脏节点刷新 |
| AC-6.3 | US-6 | R-18 | 单元测试 解冻无变量不触发 |
| AC-6.4 | US-6 | R-18 | 单元测试 aboutToReuse 改值 |
| AC-6.5 | US-6 | R-19 | 单元测试 BuilderNode 继承冻结 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在状态变量上叠加 `@Watch('onChange')` | `ViewPU.declareWatch`（`pu_view.ts:844-846`）将变量名 → 回调方法名映射注册到 `watchedProps`；回调签名为 `(changedPropertyName?: string) => void`；多个状态变量可绑定同一回调，通过 `changedPropertyName` 区分 | 参数必须是 string 方法名 | AC-1.1, AC-1.6, AC-3.4 |
| R-2 | 行为 | 被监听的状态变量真正变化 | 框架使用严格相等（`===`）判断；`===` 为 false（即不相等）时触发 @Watch 回调；@Watch 方法在自定义组件属性变更之后**同步执行**；触发时间是变量真正变化、被赋值的时间 | — | AC-1.2, AC-1.3 |
| R-3 | 边界 | 状态变量第一次初始化 | @Watch 方法不会被调用（初始化不算状态变量改变） | — | AC-1.4 |
| R-4 | 边界 | @Watch 仅能监听到可以观察到的变化 | 无法观察的变化（如嵌套对象第二层属性未用 @Observed）不触发 @Watch | 观察边界与装饰器一致 | AC-1.5 |
| R-5 | 行为 | @Watch 双触发路径 | @State/@Prop/@Link/@ObjectLink 经 `viewPropertyHasChanged`（`pu_view.ts:682-734`）路径标记 dirty 后触发；@Provide 经 `__notifyDecoratedWatch__Internal` 路径触发（含冻结延迟处理） | 双路径覆盖不同装饰器 | AC-2.1, AC-2.2 |
| R-6 | 行为 | 不同装饰器的 @Watch 触发时机 | @Link 状态更新是同步的，状态变化立刻触发 @Watch；@ObjectLink/@Prop 的更新依赖父组件同步，触发时间略晚 | 触发时机差异 | AC-2.3, AC-2.4 |
| R-7 | 边界 | 在 @Watch 方法里改变其他状态变量 | 引起状态变更和 @Watch 执行；注意避免无限循环（直接或间接修改同一状态变量） | 避免循环 | AC-2.5 |
| R-8 | 异常 | @Watch 参数非 string 类型或方法未声明 | 编译期报错；参数必须是常量字符串，且为 `(string) => void` 自定义成员函数的方法引用 | — | AC-3.1, AC-3.2 |
| R-9 | 异常 | @Watch 监听常规变量（非状态变量） | 编译期报错，常规变量不能被 @Watch 装饰 | 仅状态变量可监听 | AC-3.3 |
| R-10 | 行为 | @Watch 与其他装饰器组合 | 可与所有 V1 状态变量装饰器（@State/@Prop/@Link/@Provide/@Consume/@ObjectLink/@StorageLink 等）组合；装饰器顺序不影响实际功能 | — | AC-3.5 |
| R-11 | 行为 | `@Component({ freezeWhenInactive: true })` 配置激活 | 组件进入 inactive 状态时，状态变量变化不触发 UI 刷新和 @Watch 回调，变化被暂存 | API 11+ | AC-4.1 |
| R-12 | 行为 | 子组件未设置 `freezeWhenInactive` | 继承父组件的冻结配置（`puv2_view_base.ts`） | 子继承父 | AC-4.2 |
| R-13 | 行为 | 组件冻结触发场景 | 6 类场景：页面路由（router）非栈顶不可见页面、TabContent 非当前显示、LazyForEach 缓存节点、Navigation 未显示的 NavDestination、组件复用进入复用池、混用场景（API 18+ 仅 LazyForEach 屏上节点为 active）；组件 active/inactive 不等同于其可见性 | 仅 6 类场景适用 | AC-4.3~AC-4.8 |
| R-14 | 行为 | `DelayedNotifyChangesEnum` 三态机 | `do_not_delay`(0)：组件 active，立即通知；`delay_none_pending`(1)：组件 inactive，暂无待处理（`setActiveInternal(false)`，`pu_view.ts:483-522`）；`delay_notification_pending`(2)：组件 inactive 且有暂存，继续变更累积 | 三态切换 | AC-5.1~AC-5.4 |
| R-15 | 行为 | 组件由 inactive 变为 active | `performDelayedUpdate` 统一回放暂存的 elmtId，重新刷新冻结期间的状态变量，@Watch 注册的方法被再次调用 | 激活时回放 | AC-5.5 |
| R-16 | 边界 | 父组件解冻时子组件解冻范围 | API 17 及以下：解冻子组件所有节点；API 18+：只解冻子组件的屏上节点（混用场景改进） | 版本差异 | AC-5.6, AC-5.7 |
| R-17 | 行为 | 页面生命周期 `OnPageShow` | 当前 Page 根节点设为 active（灭屏亮屏也会触发，影响 LazyForEach） | — | AC-5.8 |
| R-18 | 边界 | 组件冻结与组件复用混用 | 子组件从复用池被复用（上树）后重新标记为 active，但**不会触发 @Watch 回调**：复用时执行脏节点刷新（包括冻结期间延迟刷新的变量绑定的系统组件）并清空脏节点列表；解冻时判断冻结期间无变量改变，不触发 @Watch；即使 `aboutToReuse` 中改值，解冻时同样不触发 @Watch | 复用执行逻辑早于组件解冻 | AC-6.1~AC-6.4 |
| R-19 | 行为 | API 20+ BuilderNode `inheritFreezeOptions: true` | BuilderNode 继承父组件冻结能力；API 20 前 BuilderNode 无法继承冻结（BuilderNode 子组件无法被冻结，即使父组件开启冻结） | API 20+ | AC-6.5 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @Watch 注册 |
| VM-2 | AC-1.2 | 单元测试 | `v1_tests/` 变化触发回调 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` 同步执行 |
| VM-4 | AC-1.4 | 单元测试 | `v1_tests/` 初始化不触发 |
| VM-5 | AC-1.5 | 单元测试 | `v1_tests/` 仅观察到的变化 |
| VM-6 | AC-1.6 | 单元测试 | `v1_tests/` 多变量共享回调 |
| VM-7 | AC-2.1 | 单元测试 | `v1_tests/` viewPropertyHasChanged 路径 |
| VM-8 | AC-2.2 | 单元测试 | `v1_tests/` __notifyDecoratedWatch__Internal 路径 |
| VM-9 | AC-2.3 | 单元测试 | `v1_tests/` @Link 同步触发 |
| VM-10 | AC-2.4 | 单元测试 | `v1_tests/` @ObjectLink/@Prop 延迟 |
| VM-11 | AC-2.5 | 单元测试 | `v1_tests/` 链式触发 |
| VM-12 | AC-3.1 | 编译期校验 | ArkTS 编译器 参数类型校验 |
| VM-13 | AC-3.2 | 编译期校验 | ArkTS 编译器 方法存在校验 |
| VM-14 | AC-3.3 | 编译期校验 | ArkTS 编译器 常规变量拒绝 |
| VM-15 | AC-3.4 | 单元测试 | `v1_tests/` 回调签名 |
| VM-16 | AC-3.5 | 单元测试 | `v1_tests/` 装饰器组合 |
| VM-17 | AC-4.1 | 单元测试 | `v1_tests/` freezeWhenInactive |
| VM-18 | AC-4.2 | 代码审查 | `puv2_view_base.ts` 配置继承 |
| VM-19 | AC-4.3 | 单元测试 | `v1_tests/` router 场景 |
| VM-20 | AC-4.4 | 单元测试 | `v1_tests/` TabContent 场景 |
| VM-21 | AC-4.5 | 单元测试 | `v1_tests/` LazyForEach 场景 |
| VM-22 | AC-4.6 | 单元测试 | `v1_tests/` Navigation 场景 |
| VM-23 | AC-4.7 | 单元测试 | `repeat_tests/` 组件复用场景 |
| VM-24 | AC-4.8 | 单元测试 | `v1_tests/` active≠可见性 |
| VM-25 | AC-5.1 | 单元测试 | `v1_tests/` do_not_delay |
| VM-26 | AC-5.2 | 代码审查 | `pu_view.ts:483-522` setActiveInternal |
| VM-27 | AC-5.3 | 单元测试 | `v1_tests/` delay_notification_pending |
| VM-28 | AC-5.4 | 单元测试 | `v1_tests/` 累积暂存 |
| VM-29 | AC-5.5 | 单元测试 | `v1_tests/` performDelayedUpdate 回放 |
| VM-30 | AC-5.6 | 单元测试 | `v1_tests/` API 17 全节点解冻 |
| VM-31 | AC-5.7 | 单元测试 | `v1_tests/` API 18 屏上节点解冻 |
| VM-32 | AC-5.8 | 单元测试 | `v1_tests/` OnPageShow |
| VM-33 | AC-6.1 | 单元测试 | `repeat_tests/` 复用上树不触发 @Watch |
| VM-34 | AC-6.2 | 单元测试 | `repeat_tests/` 复用脏节点刷新 |
| VM-35 | AC-6.3 | 单元测试 | `repeat_tests/` 解冻无变量不触发 |
| VM-36 | AC-6.4 | 单元测试 | `repeat_tests/` aboutToReuse 改值 |
| VM-37 | AC-6.5 | 单元测试 | `v1_tests/` BuilderNode 继承冻结 |

---

## 枚举规格

### DelayedNotifyChangesEnum（组件冻结三态机）

| 常量 | 值 | 说明 | 来源 |
|------|-----|------|------|
| do_not_delay | 0 | 组件激活，状态变更立即通知 | `pu_observed_property_abstract.ts` |
| delay_none_pending | 1 | 组件冻结，暂无待处理变更 | `pu_observed_property_abstract.ts` |
| delay_notification_pending | 2 | 组件冻结且有暂存变更，激活时 `performDelayedUpdate` 统一回放 | `pu_observed_property_abstract.ts` |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `declareWatch()` | `pu_view.ts:844-846` | @Watch 注册变量名→回调方法名映射 |
| `watchedProps` | `pu_view.ts` | @Watch 映射表 |
| `delayedWatchedProps_` | `pu_view.ts` | 冻结期间延迟的 @Watch 集合 |
| `viewPropertyHasChanged()` | `pu_view.ts:682-734` | @Watch 主触发路径（@State/@Prop/@Link/@ObjectLink） |
| `__notifyDecoratedWatch__Internal` | `pu_view.ts` | @Watch @Provide 触发路径（含冻结延迟） |
| `setActiveInternal()` | `pu_view.ts:483-522` | 组件 active/inactive 切换，驱动冻结三态机 |
| `performDelayedUpdate()` | `pu_view.ts` | 激活时回放暂存的 dirty elmtId 与延迟 @Watch |
| `DelayedNotifyChangesEnum` | `pu_observed_property_abstract.ts` | 冻结三态枚举 |
| `enableDelayedNotification()`/`moveElmtIdsForDelayedUpdate()` | `pu_observed_property_abstract.ts` | 启用/处理延迟通知 |
| `freezeWhenInactive` 继承 | `puv2_view_base.ts` | 子组件未设置则继承父组件冻结配置 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | @Watch 引入，状态变量变化回调 | 变量级监听 | 无需迁移 |
| API 11 | 组件冻结（`freezeWhenInactive`）引入 | 非激活组件不响应状态变更 | 按需开启冻结 |
| API 18 | 混用场景改进：父组件解冻时只解冻子组件屏上节点 | 混用场景性能优化 | 行为变化，注意混用场景 |
| API 20 | BuilderNode `inheritFreezeOptions: true` 支持 BuilderNode 继承冻结 | BuilderNode 子组件可被冻结 | 配置 `inheritFreezeOptions` |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 严格相等判断 | @Watch 使用 `===` 判断数值有无更新；`===` 为 false 才触发回调 |
| 同步执行 | @Watch 方法在自定义组件属性变更之后同步执行；回调应仅执行快速运算 |
| 双触发路径 | @State/@Prop/@Link/@ObjectLink 经 `viewPropertyHasChanged`；@Provide 经 `__notifyDecoratedWatch__Internal` |
| 冻结三态机 | 每个 `ObservedPropertyAbstractPU` 维护 `delayedNotification_`，非激活组件暂存变更，激活时回放 |
| 配置继承 | `freezeWhenInactive` 子组件未设置则继承父组件（`PUV2ViewBase`） |
| 冻结≠可见性 | 组件 active/inactive 不等同于可见性；冻结仅适用于 router/TabContent/LazyForEach/Navigation/组件复用/混用 6 类场景 |
| 复用混用例外 | 组件复用上树后不触发 @Watch（复用执行逻辑早于组件解冻） |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 组件冻结避免不可见组件的无效刷新；@Watch 回调应仅执行快速运算，不建议 async/await |
| 可调试性 | 日志关键字：`calling @Watch function`、`calling delayed @Watch function`、`delays @Watch function while component is frozen`；DFX trace：`ViewPU.viewPropertyHasChanged / <Component> / <var> / <depCount>` |
| 可观测性 | `hidumper -s WindowManagerService -a "-inactiveComponents"` 查询非激活组件；`-dirtyElementIds` 查询 dirty 元素 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 全部 V1 状态变量 | @Watch 可叠加在所有 V1 状态变量装饰器（@State/@Prop/@Link/@Provide/@Consume/@ObjectLink/@StorageLink 等）上 |
| 组件冻结性能优化 | `freezeWhenInactive` 是 ArkUI 不可见组件性能优化的核心机制；6 类触发场景覆盖主要 UI 容器 |
| 自定义组件生命周期 | 冻结与组件复用、LazyForEach、Navigation 等场景的 active/inactive 状态机协同（详见 KB custom_component） |
| V2 对比 | V2 冻结采用实时 `isViewActive()` 检查（无三态枚举）；V2 复用自动冻结与 Monitor 重置（归 07-02-04） |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:844-846` | `declareWatch` @Watch 注册 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:682-734` | `viewPropertyHasChanged` @Watch 主触发路径 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:483-522` | `setActiveInternal` 组件 active/inactive 切换 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | `__notifyDecoratedWatch__Internal` @Provide 触发路径、`performDelayedUpdate` 激活时回放、`delayedWatchedProps_` 延迟集合 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts` | `DelayedNotifyChangesEnum` 三态枚举、`enableDelayedNotification`/`moveElmtIdsForDelayedUpdate` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts` | `freezeWhenInactive` 配置继承 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | @Watch 回调、组件冻结行为回归测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/repeat_tests/` | 组件复用与冻结混用场景测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-watch.md` | @Watch 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-freeze.md` | 自定义组件冻结功能开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-watch.md` | @Watch API 参考 |
