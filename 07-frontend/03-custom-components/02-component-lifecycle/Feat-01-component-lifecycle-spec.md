# 特性规格

> Func-07-03-02-Feat-01 自定义组件生命周期：固化 V1 旧回调（`aboutToAppear`/`aboutToDisappear`/`onDidBuild`）与新生命周期状态机（`CustomComponentLifecycle` 5 态 FSM + `@ComponentInit`/`@ComponentAppear`/`@ComponentBuilt`/`@ComponentReuse`/`@ComponentRecycle`/`@ComponentDisappear`（API 23+）/`@ComponentActive`/`@ComponentInactive`（API 26+）装饰器）、新旧并存机制、`activeCount_` 引用计数、`transitionTable` 状态转移约束行为规格。`onPageShow`/`onPageHide` 是页面级（@Entry）生命周期，不属于本特性。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义组件生命周期 |
| 特性编号 | Func-07-03-02-Feat-01 |
| 优先级 | P1 |
| 目标版本 | aboutToAppear/aboutToDisappear API 7 起；onDidBuild API 9 起；新生命周期装饰器（@ComponentInit/@ComponentAppear/@ComponentBuilt/@ComponentReuse/@ComponentRecycle/@ComponentDisappear）API 23 起；@ComponentActive/@ComponentInactive API 26 起；activeCount_ API 18 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/03-custom-components/02-component-lifecycle/design.md` | Baselined |
| CustomComponentLifecycle | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/pu_lifecycle.ts` | — |
| PUV2ViewBase | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts` | — |
| ViewPU（生命周期触发） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | — |
| 新生命周期指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-new-lifecycle.md` | — |
| 自定义组件生命周期 | `docs/zh-cn/application-dev/ui/state-management/arkts-page-custom-components-lifecycle.md` | — |
| @ComponentV2 API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-custom-component-decorator-componentv2.md` | — |

---

## 用户故事

### US-1: V1 旧生命周期回调

**作为** 应用开发者,
**我想要** 用 `aboutToAppear`/`aboutToDisappear`/`onDidBuild` 监听自定义组件的关键阶段,
**以便** 在组件创建/销毁时初始化/释放资源。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 组件创建 THEN `aboutToAppear` 在 `build()` 前执行（初始化资源、设置初始状态） | 正常 |
| AC-1.2 | WHEN 组件销毁 THEN `aboutToDisappear` 在销毁前执行（释放资源、取消订阅） | 正常 |
| AC-1.3 | WHEN 组件 build 完成 THEN `onDidBuild`（API 9+）在 build 后执行（可在此访问子组件引用） | 正常 |
| AC-1.4 | WHEN `onPageShow`/`onPageHide`/`onBackPress` THEN 是页面级（@Entry）生命周期，不属于自定义组件 | 边界 |
| AC-1.5 | WHEN 组件未实现任何生命周期回调 THEN 正常工作（框架使用默认空实现） | 边界 |
| AC-1.6 | WHEN `aboutToAppear` 中修改状态变量 THEN 允许（build 尚未开始，无渲染期保护） | 正常 |
| AC-1.7 | WHEN `aboutToDisappear` 中修改状态变量 THEN 允许但无意义（组件即将销毁，UI 不再刷新） | 边界 |

### US-2: 新生命周期状态机（API 23+）

**作为** 应用开发者,
**我想要** 用 `@ComponentInit`/`@ComponentAppear`/`@ComponentBuilt` 等装饰器监听精细化的生命周期阶段,
**以便** 在复用/冻结等场景精确控制组件行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 新状态机（API 23+）THEN `CustomComponentLifecycle`（`pu_lifecycle.ts:56-263`）维护 5 态 FSM：INIT(0)→APPEARED(1)→BUILT(2)→RECYCLED(3)→DISAPPEARED(4) | 正常 |
| AC-2.2 | WHEN `@ComponentInit` 装饰 THEN 非状态机，在 `__customComponentExecuteInit__Internal` 构造期执行（与其他 @Component* 装饰器不同） | 正常 |
| AC-2.3 | WHEN 新生命周期装饰器触发 THEN `__componentX__Internal`（`pu_lifecycle.ts:277-399`）的 `executeInternalFunction`（装饰器方法）先于 `handleObserverFunction`（observer 回调）执行 | 正常 |
| AC-2.4 | WHEN 6 个生命周期装饰器 THEN `@ComponentInit`（构造期）/`@ComponentAppear`（APPEARED 态）/`@ComponentBuilt`（BUILT 态）/`@ComponentReuse`（复用时）/`@ComponentRecycle`（回收时）/`@ComponentDisappear`（DISAPPEARED 态） | 正常 |
| AC-2.5 | WHEN `@ComponentActive`/`@ComponentInactive`（API 26+）THEN 监听激活/非激活状态变化，不受状态机约束（独立于 5 态 FSM） | 正常 |
| AC-2.6 | WHEN 同一方法被多个 `@Component*` 装饰器装饰 THEN 不建议，仅最后定义的装饰器生效 | 边界 |

### US-3: 新旧并存与 Active/Inactive

**作为** 应用开发者,
**我想要** 新旧生命周期并存且不冲突,
**以便** 渐进迁移。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 新旧生命周期并存 THEN 不冲突，C++ 按序调用两套（旧 `FireOnAppear` 先，新 `FireTriggerLifecycleFunc` 后） | 正常 |
| AC-3.2 | WHEN `activeCount_`（`puv2_view_base.ts:104`，API 18+）变化 THEN `executeActiveOrInactiveLifecycleByNonFreezeCount`（line 701-722）处理非冻结组件的 active/inactive | 正常 |
| AC-3.3 | WHEN `@Styles`/`@Extend`/`@Require` THEN 是纯编译期特性，运行时无对应生命周期代码 | 边界 |
| AC-3.4 | WHEN 组件从 active 变 inactive THEN `@ComponentInactive`（API 26+）回调触发；从 inactive 变 active THEN `@ComponentActive` 回调触发 | 正常 |
| AC-3.5 | WHEN 非冻结组件的 `activeCount_` 从 0→1 THEN 触发 active；从 1→0 THEN 触发 inactive | 正常 |
| AC-3.6 | WHEN 冻结组件（`freezeWhenInactive=true`）THEN 不走 `executeActiveOrInactiveLifecycleByNonFreezeCount`，由冻结机制管理 | 边界 |

### US-4: 状态机转移约束

**作为** 框架维护者,
**我想要** 状态机转移受 `transitionTable` 约束,
**以便** 防止非法状态转移。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 状态机转移 THEN 受 `transitionTable`（`pu_lifecycle.ts:35-53`）约束；非法转移被拒绝 | 正常 |
| AC-4.2 | WHEN 合法转移路径 THEN INIT→APPEARED（组件出现）、APPEARED→BUILT（build 完成）、BUILT→RECYCLED（回收）、RECYCLED→APPEARED（复用重出现）、BUILT/APPEARED→DISAPPEARED（销毁） | 正常 |
| AC-4.3 | WHEN 组件 RECYCLED 后经 reuse 重新使用 THEN 可从 RECYCLED 回到 APPEARED（复用重出现路径） | 正常 |
| AC-4.4 | WHEN 组件 DISAPPEARED 后 THEN 彻底销毁，不可再转移 | 边界 |
| AC-4.5 | WHEN `LifeCycleEvent` 事件 THEN ON_APPEAR/ON_BUILD/ON_RECYCLE/ON_REUSE/ON_DISAPPEAR（`pu_lifecycle.ts:26-32`）对应状态转移 | 正常 |

### US-5: 生命周期边界与异常

**作为** 应用开发者,
**我想要** 了解生命周期的边界约束与异常处理,
**以便** 避免常见误用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `build()` 中修改状态变量 THEN `viewPropertyHasChanged` 检测到 `isRenderInProgress` 并输出错误日志 "State variable has changed during render!" | 异常 |
| AC-5.2 | WHEN `aboutToAppear` 中执行异步操作 THEN 不阻塞 build（aboutToAppear 同步执行完即进入 build） | 边界 |
| AC-5.3 | WHEN `onDidBuild` 中创建/修改子组件 THEN 允许（build 已完成） | 正常 |
| AC-5.4 | WHEN `aboutToReuse`（V1，参数模式）中修改状态变量 THEN 允许（复用重初始化阶段） | 正常 |
| AC-5.5 | WHEN `@Component*` 装饰器装饰非方法成员 THEN 编译报错（装饰器仅支持方法） | 异常 |
| AC-5.6 | WHEN 组件嵌套 THEN 子组件的生命周期在父组件 build 期间触发（父 aboutToAppear → 父 build → 子 aboutToAppear → 子 build → 子 onDidBuild → 父 onDidBuild） | 正常 |
| AC-5.7 | WHEN 多个 `@Component*` 装饰器装饰不同方法 THEN 各自独立触发（按状态机事件分发） | 正常 |
| AC-5.8 | WHEN `aboutToDisappear` 中访问已销毁的子组件 THEN 可能得到 undefined（子组件已先销毁） | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 aboutToAppear 时机 |
| AC-1.2 | US-1 | R-1 | 单元测试 aboutToDisappear 时机 |
| AC-1.3 | US-1 | R-1 | 单元测试 onDidBuild 时机 |
| AC-1.4 | US-1 | R-2 | 代码审查 页面级确认 |
| AC-1.5 | US-1 | R-3 | 单元测试 未实现回调 |
| AC-1.6 | US-1 | R-4 | 单元测试 aboutToAppear 修改状态 |
| AC-1.7 | US-1 | R-4 | 单元测试 aboutToDisappear 修改状态 |
| AC-2.1 | US-2 | R-5 | 单元测试 5 态 FSM |
| AC-2.2 | US-2 | R-5 | 单元测试 @ComponentInit 构造期 |
| AC-2.3 | US-2 | R-6 | 代码审查 executeInternalFunction |
| AC-2.4 | US-2 | R-5 | 单元测试 6 装饰器 |
| AC-2.5 | US-2 | R-7 | 单元测试 @ComponentActive/@Inactive |
| AC-2.6 | US-2 | R-8 | 单元测试 多装饰器同一方法 |
| AC-3.1 | US-3 | R-9 | 单元测试 新旧并存 |
| AC-3.2 | US-3 | R-10 | 代码审查 activeCount_ |
| AC-3.3 | US-3 | R-2 | 代码审查 编译期特性 |
| AC-3.4 | US-3 | R-7 | 单元测试 @ComponentActive/Inactive 触发 |
| AC-3.5 | US-3 | R-10 | 单元测试 activeCount_ 0→1/1→0 |
| AC-3.6 | US-3 | R-10 | 单元测试 冻结组件不走 NonFreezeCount |
| AC-4.1 | US-4 | R-11 | 单元测试 非法转移拒绝 |
| AC-4.2 | US-4 | R-11 | 单元测试 合法转移路径 |
| AC-4.3 | US-4 | R-11 | 单元测试 RECYCLED→APPEARED |
| AC-4.4 | US-4 | R-11 | 单元测试 DISAPPEARED 终态 |
| AC-4.5 | US-4 | R-11 | 代码审查 LifeCycleEvent |
| AC-5.1 | US-5 | R-12 | 单元测试 build 中修改抛错 |
| AC-5.2 | US-5 | R-4 | 单元测试 aboutToAppear 异步 |
| AC-5.3 | US-5 | R-4 | 单元测试 onDidBuild 创建子组件 |
| AC-5.4 | US-5 | R-4 | 单元测试 aboutToReuse 修改状态 |
| AC-5.5 | US-5 | R-8 | 编译期校验 |
| AC-5.6 | US-5 | R-1 | 单元测试 嵌套组件生命周期顺序 |
| AC-5.7 | US-5 | R-5 | 单元测试 多装饰器不同方法 |
| AC-5.8 | US-5 | R-1 | 单元测试 aboutToDisappear 访问子组件 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | V1 旧回调时机 | `aboutToAppear` 在 build 前执行；`aboutToDisappear` 在销毁前执行；`onDidBuild`（API 9+）在 build 后执行；嵌套组件时子组件生命周期在父 build 期间触发（父 aboutToAppear → 父 build → 子 aboutToAppear → 子 build → 子 onDidBuild → 父 onDidBuild）；`aboutToDisappear` 中访问已销毁子组件可能得 undefined（子先销毁） | 页面级 onPageShow/onPageHide 不属于自定义组件 | AC-1.1~AC-1.3, AC-5.6, AC-5.8 |
| R-2 | 边界 | 页面级 vs 组件级 | `onPageShow`/`onPageHide`/`onBackPress` 是页面级（@Entry）生命周期，不属于自定义组件；`@Styles`/`@Extend`/`@Require` 是纯编译期特性，运行时无生命周期代码 | — | AC-1.4, AC-3.3 |
| R-3 | 行为 | 组件未实现生命周期回调 | 框架使用默认空实现，组件正常工作 | — | AC-1.5 |
| R-4 | 行为 | 生命周期回调中的状态变量操作 | `aboutToAppear` 中修改状态变量允许（build 未开始，无渲染期保护）；`aboutToDisappear` 中修改允许但无意义（组件即将销毁，UI 不刷新）；`onDidBuild` 中创建/修改子组件允许（build 已完成）；`aboutToReuse` 中修改状态变量允许（复用重初始化）；`aboutToAppear` 异步操作不阻塞 build（同步执行完即进入 build） | — | AC-1.6, AC-1.7, AC-5.2~AC-5.4 |
| R-5 | 行为 | 新状态机（API 23+） | `CustomComponentLifecycle`（`pu_lifecycle.ts:56-263`）5 态 FSM（INIT→APPEARED→BUILT→RECYCLED→DISAPPEARED）；6 个装饰器：@ComponentInit（构造期，非状态机）/@ComponentAppear（APPEARED 态）/@ComponentBuilt（BUILT 态）/@ComponentReuse（复用）/@ComponentRecycle（回收）/@ComponentDisappear（DISAPPEARED 态）；多个装饰器装饰不同方法各自独立触发 | @Component* 6 个 API 23+ | AC-2.1~AC-2.4, AC-5.7 |
| R-6 | 行为 | 装饰器方法执行顺序 | `executeInternalFunction`（装饰器方法）先于 `handleObserverFunction`（observer 回调）执行；`__componentX__Internal`（line 277-399）实现分发 | — | AC-2.3 |
| R-7 | 行为 | @ComponentActive/@ComponentInactive（API 26+） | 监听激活/非激活状态变化，不受 5 态 FSM 约束（独立机制）；active→inactive 触发 @ComponentInactive；inactive→active 触发 @ComponentActive | API 26+ | AC-2.5, AC-3.4 |
| R-8 | 异常 | 装饰器误用 | 同一方法被多个 @Component* 装饰器装饰不建议，仅最后定义生效；装饰非方法成员编译报错 | — | AC-2.6, AC-5.5 |
| R-9 | 行为 | 新旧并存 | 不冲突，C++ 按序调用两套（旧 `FireOnAppear` 先，新 `FireTriggerLifecycleFunc` 后） | 渐进迁移 | AC-3.1 |
| R-10 | 行为 | Active/Inactive 引用计数 | `activeCount_`（`puv2_view_base.ts:104`，API 18+）；`executeActiveOrInactiveLifecycleByNonFreezeCount`（line 701-722）处理非冻结组件；0→1 触发 active，1→0 触发 inactive；冻结组件不走此路径（由冻结机制管理） | API 18+ | AC-3.2, AC-3.5~AC-3.6 |
| R-11 | 行为 | 状态机转移约束 | `transitionTable`（`pu_lifecycle.ts:35-53`）约束合法转移路径；INIT→APPEARED→BUILT→RECYCLED→APPEARED（复用）/→DISAPPEARED；非法转移被拒绝；DISAPPEARED 为终态不可再转移；`LifeCycleEvent`（line 26-32）对应转移事件 | — | AC-4.1~AC-4.5 |
| R-12 | 异常 | build 中修改状态变量 | `viewPropertyHasChanged` 检测到 `isRenderInProgress` 并输出错误日志 "State variable has changed during render!"；需将修改移到事件回调/生命周期/aboutToAppear 中 | 常见误用 | AC-5.1 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` aboutToAppear 时机 |
| VM-2 | AC-1.2 | 单元测试 | `v1_tests/` aboutToDisappear 时机 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` onDidBuild 时机 |
| VM-4 | AC-1.4 | 代码审查 | 页面级确认 |
| VM-5 | AC-1.5 | 单元测试 | `v1_tests/` 未实现回调 |
| VM-6 | AC-1.6 | 单元测试 | `v1_tests/` aboutToAppear 修改状态 |
| VM-7 | AC-1.7 | 单元测试 | `v1_tests/` aboutToDisappear 修改状态 |
| VM-8 | AC-2.1 | 单元测试 | `common_tests/` 5 态 FSM |
| VM-9 | AC-2.2 | 单元测试 | `v2_tests/` @ComponentInit 构造期 |
| VM-10 | AC-2.3 | 代码审查 | `pu_lifecycle.ts:277-399` executeInternalFunction |
| VM-11 | AC-2.4 | 单元测试 | `v2_tests/` 6 装饰器 |
| VM-12 | AC-2.5 | 单元测试 | `v2_tests/` @ComponentActive/@Inactive |
| VM-13 | AC-2.6 | 单元测试 | `v2_tests/` 多装饰器同一方法 |
| VM-14 | AC-3.1 | 单元测试 | `v2_tests/` 新旧并存 |
| VM-15 | AC-3.2 | 代码审查 | `puv2_view_base.ts:701-722` activeCount_ |
| VM-16 | AC-3.3 | 代码审查 | @Styles/@Extend/@Require 编译期 |
| VM-17 | AC-3.4 | 单元测试 | `v2_tests/` @ComponentActive/Inactive 触发 |
| VM-18 | AC-3.5 | 单元测试 | `v2_tests/` activeCount_ 0→1/1→0 |
| VM-19 | AC-3.6 | 单元测试 | `v2_tests/` 冻结组件不走 NonFreezeCount |
| VM-20 | AC-4.1 | 单元测试 | `common_tests/` 非法转移拒绝 |
| VM-21 | AC-4.2 | 单元测试 | `common_tests/` 合法转移路径 |
| VM-22 | AC-4.3 | 单元测试 | `common_tests/` RECYCLED→APPEARED |
| VM-23 | AC-4.4 | 单元测试 | `common_tests/` DISAPPEARED 终态 |
| VM-24 | AC-4.5 | 代码审查 | `pu_lifecycle.ts:26-32` LifeCycleEvent |
| VM-25 | AC-5.1 | 单元测试 | `v1_tests/` build 中修改抛错 |
| VM-26 | AC-5.2 | 单元测试 | `v1_tests/` aboutToAppear 异步 |
| VM-27 | AC-5.3 | 单元测试 | `v1_tests/` onDidBuild 创建子组件 |
| VM-28 | AC-5.4 | 单元测试 | `repeat_tests/` aboutToReuse 修改状态 |
| VM-29 | AC-5.5 | 编译期校验 | ArkTS 编译器 装饰非方法拒绝 |
| VM-30 | AC-5.6 | 单元测试 | `v1_tests/` 嵌套组件生命周期顺序 |
| VM-31 | AC-5.7 | 单元测试 | `v2_tests/` 多装饰器不同方法 |
| VM-32 | AC-5.8 | 单元测试 | `v1_tests/` aboutToDisappear 访问子组件 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `CustomComponentLifecycle` | `puv2_common/pu_lifecycle.ts:56-263` | 5 态 FSM 状态机 |
| `__CustomComponentLifecycleState__Internal` | `puv2_common/pu_lifecycle.ts:17-24` | 5 态枚举（INIT/APPEARED/BUILT/RECYCLED/DISAPPEARED） |
| `LifeCycleEvent` | `puv2_common/pu_lifecycle.ts:26-32` | 状态转移事件枚举 |
| `transitionTable` | `puv2_common/pu_lifecycle.ts:35-53` | 合法状态转移路径表 |
| `__componentX__Internal` | `puv2_common/pu_lifecycle.ts:277-399` | 新生命周期装饰器内部实现（8 个函数） |
| `CustomComponentLifecycleObserver` | `puv2_common/pu_lifecycle.ts:265-275` | observer 回调接口 |
| `activeCount_` | `puv2_common/puv2_view_base.ts:104` | API 18+ 引用计数 |
| `executeActiveOrInactiveLifecycleByNonFreezeCount` | `puv2_common/puv2_view_base.ts:701-722` | 非冻结组件 active/inactive |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | aboutToAppear/aboutToDisappear 引入 | V1 生命周期回调 | 无需迁移 |
| API 9 | onDidBuild 引入 | build 后回调 | 无需迁移 |
| API 18 | activeCount_ 引用计数引入 | 精确管理激活状态 | 无需迁移 |
| API 23 | 新生命周期装饰器（@ComponentInit/@ComponentAppear/@ComponentBuilt/@ComponentReuse/@ComponentRecycle/@ComponentDisappear）引入 | 精细化生命周期管理 | 无需迁移 |
| API 26 | @ComponentActive/@ComponentInactive 引入（不受状态机约束） | 激活/非激活监听 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 页面 vs 组件 | onPageShow/onPageHide/onBackPress 是页面级（@Entry），不属于自定义组件生命周期 |
| 新旧并存 | C++ 按序调用两套（旧先、新后），不冲突，支持渐进迁移 |
| @ComponentInit 特殊 | 非状态机，构造期执行（与其他 @Component* 差异） |
| executeInternalFunction 先于 observer | 装饰器方法先于 observer 回调执行 |
| transitionTable 约束 | 状态转移受合法路径表约束，非法转移被拒绝；DISAPPEARED 为终态 |
| build 中禁修改状态 | build 中修改状态变量抛错（isRenderInProgress 检测） |
| @ComponentActive/@Inactive 独立 | 不受 5 态 FSM 约束，API 26+ |
| 与状态管理交叉 | 状态变量在生命周期回调中的行为（如 aboutToAppear 修改允许、build 中抛错）详见 07-02 |
| 与冻结交叉 | freezeWhenInactive 影响生命周期回调触发（冻结期间延迟）详见 07-03-04 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 生命周期回调注册/触发无额外开销；回调直接在 Pattern/View 层触发 |
| 可调试性 | 所有回调包含 TAG_LOGI 日志输出；DFX trace 含组件名/状态转移信息 |
| 可观测性 | `hidumper -s WindowManagerService -a "-stateVariables -viewId=N"` 可查询组件状态；Inspector 显示生命周期状态 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 自定义组件体系 | 生命周期是自定义组件的核心机制，与组件化（07-03-01）、复用（07-03-03）、冻结（07-03-04）协同 |
| 状态管理 | 生命周期回调中的状态变量行为（aboutToAppear 修改/build 中抛错）与 07-02 状态管理交叉 |
| 组件复用 | aboutToReuse/aboutToRecycle 的触发时机与 07-03-03 复用机制协同 |
| 组件冻结 | activeCount_ 与 freezeWhenInactive 的协同见 07-03-04 |
| LazyForEach/Repeat | 缓存节点的生命周期状态影响复用/冻结行为 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 标准生命周期 | — | 单元测试 | — |
| 平板 | Split 模式下组件可能因分屏触发 active/inactive | activeCount_ 适配 | 单元测试 | — |
| 折叠屏 | 折叠/展开可能触发组件重建（DISAPPEARED→重新 INIT） | — | 单元测试 | — |
| 穿戴 | 小屏场景生命周期一致 | — | 单元测试 | — |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/pu_lifecycle.ts:17-24` | 5 态 FSM 枚举 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/pu_lifecycle.ts:26-53` | `LifeCycleEvent` + `transitionTable` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/pu_lifecycle.ts:56-263` | `CustomComponentLifecycle` 状态机 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/pu_lifecycle.ts:277-399` | `__componentX__Internal` 新装饰器实现（8 个） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts:104` | `activeCount_` 引用计数 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts:701-722` | `executeActiveOrInactiveLifecycleByNonFreezeCount` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:682-734` | `viewPropertyHasChanged` build 中修改检测 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | CustomComponentLifecycle FSM/transitionTable 测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | V1 生命周期回调测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | 新生命周期装饰器测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-custom-components-new-lifecycle.md` | 新生命周期指南（API 23+） |
| `docs/zh-cn/application-dev/ui/state-management/arkts-page-custom-components-lifecycle.md` | 自定义组件生命周期 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-custom-component-decorator-componentv2.md` | @ComponentV2 API 参考 |
