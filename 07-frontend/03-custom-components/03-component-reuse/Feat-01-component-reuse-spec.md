# 特性规格

> Func-07-03-03-Feat-01 自定义组件复用机制：固化 V1 `@Reusable`（`aboutToReuse(params)`/`aboutToRecycle`、`RecycleManager` + `BidirectionalMap`、reuseId）、V2 `@ReusableV2`（`aboutToReuse` 无参、`resetStateVarsOnReuse` 自动状态重置、`RecyclePoolV2` + `RecycledIdRegistry`）、全局复用池 `__ReusePool__Internal__`（shared/perInstance）、`reuseOrCreateNewComponent`、V1/V2 复用混用矩阵（错误码 140113）、Repeat template 限制行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自定义组件复用机制 |
| 特性编号 | Func-07-03-03-Feat-01 |
| 优先级 | P1 |
| 目标版本 | @Reusable API 10 起；@ReusableV2 API 18 起；全局复用池 API 10 起；错误码 140113 API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/03-custom-components/03-component-reuse/design.md` | Baselined |
| ViewPU（RecycleManager） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | — |
| ViewV2（RecyclePoolV2） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts` | — |
| 全局复用池 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_globalreuse.ts` | — |
| @Reusable 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-reusable.md` | — |
| @ReusableV2 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-reusableV2.md` | — |
| 全局复用指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-global-reuse-pool.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: V1 @Reusable

**作为** 应用开发者,
**我想要** 用 `@Reusable` 装饰 V1 自定义组件实现复用,
**以便** 组件出树时回收入池，需要同类型时从池中复用，避免频繁创建/销毁。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `@Reusable` 装饰 V1 组件 THEN 组件出树时 `aboutToRecycle` 回调触发，`RecycleManager` + `BidirectionalMap` 按父节点回收入池 | 正常 |
| AC-1.2 | WHEN `aboutToReuse(params)` 回调触发 THEN 接收新参数用于更新组件状态（与 V2 无参差异） | 正常 |
| AC-1.3 | WHEN `reuseId` 指定 THEN 池中按 reuseId 区分不同类型组件；相同 reuseId 可互换；默认用类名作为 reuseId | 正常 |
| AC-1.4 | WHEN V1 复用组件在池中 THEN 状态变量仍可能被引用，需 `freezeWhenInactive` 避免无效更新（详见 07-03-04） | 边界 |
| AC-1.5 | WHEN `aboutToRecycle` 中释放资源 THEN 允许（取消订阅、释放定时器等） | 正常 |
| AC-1.6 | WHEN 组件从池中被复用 THEN `aboutToReuse` 先于 build 执行（重初始化资源） | 正常 |
| AC-1.7 | WHEN 池中无匹配 reuseId 的组件 THEN 创建新组件（不从池中取不匹配类型） | 边界 |

### US-2: V2 @ReusableV2

**作为** 应用开发者,
**我想要** 用 `@ReusableV2`（API 18+）装饰 V2 组件实现自动状态重置的复用,
**以便** 复用组件状态干净，无需手动重置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `@ReusableV2`（API 18+）装饰 @ComponentV2 THEN `RecyclePoolV2` + `RecycledIdRegistry` 管理 V2 复用池 | 正常 |
| AC-2.2 | WHEN 组件回收 THEN `aboutToRecycle` 回调 + `freezeRecycledComponent`（`v2_view.ts:312`）冻结（activeCount_--） | 正常 |
| AC-2.3 | WHEN 组件复用 THEN `aboutToReuse` 回调（**无入参**，与 V1 `aboutToReuse(params)` 不同）+ `unfreezeReusedComponent`（`v2_view.ts:328`） | 正常 |
| AC-2.4 | WHEN 复用时 `resetStateVarsOnReuse`（`v2_view.ts:210`）THEN 按定义顺序重置状态变量：@Local/@Provider 用初始值；@Param/@Event 有外部用外部否则用初始值；@Consumer 有对应 @Provider 用其值否则用初始值；@Computed 用当前最新值重新计算；常量（含 readonly）不重置 | 正常 |
| AC-2.5 | WHEN 复用时 @Monitor 重置 THEN `resetMonitorsOnReuse`（`v2_view.ts:519`）在所有变量重置后触发；重置中的变化更新 IMonitorValue.before 但不触发回调 | 正常 |
| AC-2.6 | WHEN 回收/复用 THEN 递归调用所有子组件的对应 `aboutToRecycle`/`aboutToReuse` | 正常 |
| AC-2.7 | WHEN @Computed 推荐定义在所依赖变量之后 THEN 重置顺序正确（@Computed 用最新值重计算） | 边界 |

### US-3: 全局复用池

**作为** 应用开发者,
**我想要** 用全局复用池 `__ReusePool__Internal__` 跨父节点复用组件,
**以便** 提升复用效率（不同父节点下的同类型组件可共享复用池）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `__ReusePool__Internal__`（`puv2_globalreuse.ts`）THEN 支持 shared（跨父共享）/ perInstance（按父隔离）两种模式 | 正常 |
| AC-3.2 | WHEN `reuseOrCreateNewComponent`（`v2_view.ts:1075`）THEN 从池中查找匹配 reuseId 的组件；找到则复用，未找到则创建新组件 | 正常 |
| AC-3.3 | WHEN V2 复用组件不支持直接用于 Repeat 的 template THEN 可用在 template 内的 V2 自定义组件中 | 边界 |
| AC-3.4 | WHEN shared 模式 THEN 不同父节点下的同类型组件共享同一复用池 | 正常 |
| AC-3.5 | WHEN perInstance 模式 THEN 每个父节点有独立的复用池实例 | 正常 |
| AC-3.6 | WHEN 全局复用池 capacity 设置 THEN 控制池中最大缓存组件数 | 边界 |

### US-4: V1/V2 复用混用矩阵

**作为** 应用开发者,
**我想要** 了解 V1/V2 复用混用的完整规则,
**以便** 避免混用错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN V1 普通父 + V2 复用子 THEN 不支持（编译报错） | 异常 |
| AC-4.2 | WHEN V2 普通父 + V1 复用子 THEN 不支持（编译告警，子组件不创建） | 异常 |
| AC-4.3 | WHEN V1 复用父 + V2 普通子 THEN 支持 | 正常 |
| AC-4.4 | WHEN V2 复用父 + V2 普通子 THEN 支持 | 正常 |
| AC-4.5 | WHEN V1 复用父 + V1 复用子 THEN 支持 | 正常 |
| AC-4.6 | WHEN V2 复用父 + V1 复用子 THEN 不支持（编译报错） | 异常 |
| AC-4.7 | WHEN V1 复用父 + V2 复用子 需 API 18+ SDK THEN 否则 API 23+ 返回错误码 140113 | 异常 |
| AC-4.8 | WHEN V2 复用父 + V1 普通子 THEN 支持（需 SDK 18+） | 边界 |

### US-5: 复用边界与约束

**作为** 应用开发者,
**我想要** 了解复用的边界约束与最佳实践,
**以便** 正确使用复用避免性能陷阱。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 不建议嵌套滥用 @ReusableV2 THEN 文档已声明约束（嵌套复用增加复杂性） | 边界 |
| AC-5.2 | WHEN V2 复用组件回收期间冻结 THEN @Computed 不重新计算、@Monitor 回调不触发（冻结状态） | 边界 |
| AC-5.3 | WHEN V2 复用组件 aboutToReuse 中修改状态变量 THEN 允许（重初始化阶段，非渲染期） | 正常 |
| AC-5.4 | WHEN V1 aboutToReuse(params) 中接收的 params THEN 是父组件传递的新参数（用于更新组件） | 正常 |
| AC-5.5 | WHEN 组件复用后子组件的状态 THEN V1 需手动重置；V2 自动重置（resetStateVarsOnReuse） | 边界 |
| AC-5.6 | WHEN `recycleSelf()` 调用 THEN 组件主动回收入池（不等出树） | 正常 |
| AC-5.7 | WHEN 复用池为空且需要新组件 THEN 创建新组件并注册到池（下次可复用） | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 V1 回收入池 |
| AC-1.2 | US-1 | R-1 | 单元测试 aboutToReuse(params) |
| AC-1.3 | US-1 | R-2 | 单元测试 reuseId 匹配 |
| AC-1.4 | US-1 | R-3 | 单元测试 池中冻结 |
| AC-1.5 | US-1 | R-1 | 单元测试 aboutToRecycle 释放资源 |
| AC-1.6 | US-1 | R-1 | 单元测试 aboutToReuse 先于 build |
| AC-1.7 | US-1 | R-2 | 单元测试 无匹配创建新 |
| AC-2.1 | US-2 | R-4 | 单元测试 RecyclePoolV2 |
| AC-2.2 | US-2 | R-4 | 单元测试 回收冻结 |
| AC-2.3 | US-2 | R-4 | 单元测试 复用无参 |
| AC-2.4 | US-2 | R-5 | 单元测试 resetStateVarsOnReuse |
| AC-2.5 | US-2 | R-5 | 单元测试 resetMonitorsOnReuse |
| AC-2.6 | US-2 | R-6 | 单元测试 递归子组件 |
| AC-2.7 | US-2 | R-5 | 单元测试 @Computed 定义顺序 |
| AC-3.1 | US-3 | R-7 | 单元测试 shared/perInstance |
| AC-3.2 | US-3 | R-7 | 单元测试 reuseOrCreateNewComponent |
| AC-3.3 | US-3 | R-8 | 单元测试 Repeat template 限制 |
| AC-3.4 | US-3 | R-7 | 单元测试 shared 跨父 |
| AC-3.5 | US-3 | R-7 | 单元测试 perInstance 隔离 |
| AC-3.6 | US-3 | R-7 | 单元测试 capacity |
| AC-4.1~4.8 | US-4 | R-9 | 单元测试 混用矩阵 |
| AC-5.1 | US-5 | R-10 | 代码审查 嵌套约束 |
| AC-5.2 | US-5 | R-3 | 单元测试 回收冻结 |
| AC-5.3 | US-5 | R-5 | 单元测试 aboutToReuse 修改状态 |
| AC-5.4 | US-5 | R-1 | 单元测试 params 传递 |
| AC-5.5 | US-5 | R-5 | 单元测试 V1 手动 vs V2 自动 |
| AC-5.6 | US-5 | R-1 | 单元测试 recycleSelf |
| AC-5.7 | US-5 | R-7 | 单元测试 池空创建新 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | V1 @Reusable 回收/复用 | 组件出树 `aboutToRecycle` + `RecycleManager`/`BidirectionalMap` 回收入池；复用 `aboutToReuse(params)` 接收新参数先于 build；`recycleSelf()` 主动回收；池中需 freezeWhenInactive 避免无效更新 | API 10+ | AC-1.1~AC-1.7, AC-5.4~AC-5.6 |
| R-2 | 行为 | reuseId 匹配 | 池中按 reuseId 区分类型；相同 reuseId 可互换；默认类名；池中无匹配则创建新组件 | — | AC-1.3, AC-1.7 |
| R-3 | 边界 | 复用池中冻结 | V1 池中状态变量仍可能被引用需 freezeWhenInactive；V2 回收期间 `freezeRecycledComponent` 冻结 @Computed/@Monitor 不触发 | — | AC-1.4, AC-5.2 |
| R-4 | 行为 | V2 @ReusableV2（API 18+）回收/复用 | `RecyclePoolV2`/`RecycledIdRegistry` 管理池；回收 `aboutToRecycle` + `freezeRecycledComponent`(312) 冻结（activeCount_--）；复用 `aboutToReuse`（**无参**）+ `unfreezeReusedComponent`(328) | aboutToReuse 无参（V2 差异） | AC-2.1~AC-2.3 |
| R-5 | 行为 | V2 resetStateVarsOnReuse | `resetStateVarsOnReuse`(210) 按定义顺序重置 @Local/@Provider（初始值）→ @Param/@Event（有外部用外部否则初始值）→ @Consumer（有 @Provider 用其值否则初始值）→ @Computed（最新值重计算）→ @Monitor（所有变量重置后触发，重置中变化更新 before 不触发回调）；常量不重置；aboutToReuse 中修改状态变量允许 | @Computed 推荐定义在依赖变量之后 | AC-2.4~AC-2.7, AC-5.3, AC-5.5 |
| R-6 | 行为 | 递归子组件复用 | 回收/复用递归调用所有子组件的对应 `aboutToRecycle`/`aboutToReuse` | — | AC-2.6 |
| R-7 | 行为 | 全局复用池 | `__ReusePool__Internal__`（`puv2_globalreuse.ts`）支持 shared（跨父共享）/ perInstance（按父隔离）；`reuseOrCreateNewComponent`(1075) 从池查找或创建；capacity 控制最大缓存数；池空创建新并注册 | — | AC-3.1~AC-3.6, AC-5.7 |
| R-8 | 边界 | Repeat template 限制 | V2 复用组件不能直接用于 Repeat template（可用在 template 内的 V2 自定义组件中） | — | AC-3.3 |
| R-9 | 异常 | V1/V2 复用混用矩阵 | V1 普通+V2 复用=不支持（编译报错）；V2 普通+V1 复用=不支持（编译告警）；V1 复用+V2 复用=不支持（编译报错）；V1 复用+V2 普通+API 18+SDK=支持否则 140113；V2 复用+V1 普通+SDK 18+=支持 | 错误码 140113 API 23+ | AC-4.1~AC-4.8 |
| R-10 | 边界 | 嵌套约束 | 不建议嵌套滥用 @ReusableV2（增加复杂性） | — | AC-5.1 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `repeat_tests/` V1 回收入池 |
| VM-2 | AC-1.2 | 单元测试 | `repeat_tests/` aboutToReuse(params) |
| VM-3 | AC-1.3 | 单元测试 | `repeat_tests/` reuseId 匹配 |
| VM-4 | AC-1.4 | 单元测试 | `repeat_tests/` 池中冻结 |
| VM-5 | AC-1.5 | 单元测试 | `repeat_tests/` aboutToRecycle 释放 |
| VM-6 | AC-1.6 | 单元测试 | `repeat_tests/` aboutToReuse 先于 build |
| VM-7 | AC-1.7 | 单元测试 | `repeat_tests/` 无匹配创建新 |
| VM-8 | AC-2.1 | 单元测试 | `repeat_tests/` RecyclePoolV2 |
| VM-9 | AC-2.2 | 单元测试 | `repeat_tests/` 回收冻结 |
| VM-10 | AC-2.3 | 单元测试 | `repeat_tests/` 复用无参 |
| VM-11 | AC-2.4 | 代码审查 | `v2_view.ts:210` resetStateVarsOnReuse |
| VM-12 | AC-2.5 | 代码审查 | `v2_view.ts:519` resetMonitorsOnReuse |
| VM-13 | AC-2.6 | 单元测试 | `repeat_tests/` 递归子组件 |
| VM-14 | AC-2.7 | 单元测试 | `repeat_tests/` @Computed 定义顺序 |
| VM-15 | AC-3.1 | 单元测试 | `repeat_tests/` shared/perInstance |
| VM-16 | AC-3.2 | 单元测试 | `repeat_tests/` reuseOrCreateNewComponent |
| VM-17 | AC-3.3 | 单元测试 | `repeat_tests/` Repeat template 限制 |
| VM-18 | AC-3.4 | 单元测试 | `repeat_tests/` shared 跨父 |
| VM-19 | AC-3.5 | 单元测试 | `repeat_tests/` perInstance 隔离 |
| VM-20 | AC-3.6 | 单元测试 | `repeat_tests/` capacity |
| VM-21 | AC-4.1~4.8 | 单元测试 | `repeat_tests/` 混用矩阵 8 种组合 |
| VM-22 | AC-5.1 | 代码审查 | 嵌套约束 |
| VM-23 | AC-5.2 | 单元测试 | `repeat_tests/` 回收冻结 |
| VM-24 | AC-5.3 | 单元测试 | `repeat_tests/` aboutToReuse 修改状态 |
| VM-25 | AC-5.4 | 单元测试 | `repeat_tests/` params 传递 |
| VM-26 | AC-5.5 | 单元测试 | `repeat_tests/` V1 手动 vs V2 自动 |
| VM-27 | AC-5.6 | 单元测试 | `repeat_tests/` recycleSelf |
| VM-28 | AC-5.7 | 单元测试 | `repeat_tests/` 池空创建新 |

---

## 错误码规格

| 错误码 | 触发条件 | 错误信息 | 起始版本 |
|--------|----------|----------|----------|
| 140113 | @Reusable（V1）+ @ComponentV2（V2）混用且未用 API 18+ SDK 编译 | `Old toolchain detected. Please upgrade to the latest.` | API 23 起返回码 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `RecycleManager` + `BidirectionalMap` | `partial_update/pu_view.ts` | V1 按父节点的复用池 |
| `RecyclePoolV2` + `RecycledIdRegistry` | `v2/v2_recycle_pool.ts` | V2 复用池 |
| `__ReusePool__Internal__` | `puv2_common/puv2_globalreuse.ts` | 全局复用池（shared/perInstance） |
| `resetStateVarsOnReuse` | `v2/v2_view.ts:210` | V2 复用状态自动重置 |
| `resetMonitorsOnReuse` | `v2/v2_view.ts:519` | V2 复用 Monitor 重置 |
| `freezeRecycledComponent`/`unfreezeReusedComponent` | `v2/v2_view.ts:312/328` | V2 复用自动冻结/解冻 |
| `reuseOrCreateNewComponent` | `v2/v2_view.ts:1075` | V2 复用入口 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 10 | @Reusable + 全局复用池引入 | V1 复用机制 | 无需迁移 |
| API 18 | @ReusableV2 引入（aboutToReuse 无参 + 自动状态重置） | V2 复用机制 | 注意 aboutToReuse 无参 |
| API 23 | 错误码 140113 返回（@Reusable+@ComponentV2 混用需 API 18+ SDK） | 错误码规范化 | 处理新增错误码 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| V1 vs V2 复用差异 | V1 aboutToReuse(params) 手动传参 + 手动状态管理；V2 aboutToReuse 无参 + resetStateVarsOnReuse 自动重置 |
| V2 回收自动冻结 | freezeRecycledComponent 冻结（activeCount_--）；复用时 unfreezeReusedComponent 解冻 + resetStateVarsOnReuse 重置 |
| 全局复用池 | shared 跨父共享 / perInstance 按父隔离 |
| Repeat template 限制 | V2 复用组件不能直接用于 Repeat template（可用在 template 内的 V2 自定义组件中） |
| 混用矩阵 | V1/V2 复用组件混用有严格限制（8 种组合，部分不支持） |
| 递归子组件 | 回收/复用递归调用所有子组件 |
| 与冻结交叉 | 回收期间冻结行为详见 07-03-04 |
| 与状态管理交叉 | V2 resetStateVarsOnReuse 涉及的状态变量行为详见 07-02-04 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 复用避免频繁创建/销毁开销；V2 自动重置比 V1 手动重置更高效；全局复用池 shared 模式跨父共享提升复用率 |
| 可调试性 | `hidumper -s WindowManagerService -a "-RecyclePool"` 查询复用池状态；DFX trace 含回收/复用事件 |
| 内存 | 复用池缓存组件占用内存；capacity 控制最大缓存数；V1 池中组件需冻结避免无效更新 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 自定义组件体系 | 复用是自定义组件核心机制，与组件化（07-03-01）、生命周期（07-03-02）、冻结（07-03-04）协同 |
| 渲染控制 | LazyForEach/Repeat 触发复用；V2 复用组件不能直接用于 Repeat template（详见 07-05 渲染控制） |
| 状态管理 | V2 resetStateVarsOnReuse 涉及的状态变量重置行为与 07-02-04 交叉 |
| 组件冻结 | 回收期间冻结行为与 07-03-04 协同 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 标准复用 | — | 单元测试 | — |
| 平板 | Split 模式下复用池可能跨分屏共享 | shared 模式适配 | 单元测试 | — |
| 折叠屏 | 折叠/展开时组件重建可触发回收/复用 | — | 单元测试 | — |
| 穿戴 | 小屏列表场景复用频繁 | capacity 需合理设置 | 性能测试 | — |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | `RecycleManager` + `BidirectionalMap` V1 复用池 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts:210` | `resetStateVarsOnReuse` V2 状态重置 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts:312-340` | `freezeRecycledComponent`/`unfreezeReusedComponent` V2 复用冻结/解冻 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts:519` | `resetMonitorsOnReuse` V2 Monitor 重置 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_view.ts:1075` | `reuseOrCreateNewComponent` V2 复用入口 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_recycle_pool.ts` | `RecyclePoolV2` + `RecycledIdRegistry` V2 复用池 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_globalreuse.ts` | `__ReusePool__Internal__` 全局复用池（shared/perInstance） |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/repeat_tests/` | V1/V2 复用、混用矩阵、全局复用池回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-reusable.md` | @Reusable 指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-reusableV2.md` | @ReusableV2 指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-global-reuse-pool.md` | 全局复用指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | 错误码 140113 |
