# 特性规格

> Func-07-02-01-Feat-01 V1 依赖收集与变更通知核心机制：固化 ArkUI 声明式前端 V1 状态管理共享的渲染期 elmtId 级依赖收集、状态变更精确通知、PU 渲染路径（API 9 起统一）、dirty 元素升序局部重渲染、elmtId 生命周期管理行为规格。本特性是 `@State`/`@Prop`/`@Link`/`@Provide`/`@Consume`/`@ObjectLink`/`@Watch`/`@Track` 全部 V1 组件级装饰器的运行时基础。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | V1 依赖收集与变更通知核心机制 |
| 特性编号 | Func-07-02-01-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持核心机制；Date 类型 API 10 起；Map/Set/联合类型 API 11 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| ObservedPropertyAbstractPU | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts` | — |
| ViewPU | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts` | — |
| UINodeRegisterProxy | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_uinode_registry_proxy.ts` | — |
| ConfigureStateMgmt | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_configure.ts` | — |
| PUV2ViewBase（markNeedUpdate） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts` | — |
| PipelineContext | `frameworks/core/pipeline_ng/pipeline_context.cpp` | — |
| 状态管理概述 | `docs/zh-cn/application-dev/ui/state-management/arkts-state-management-introduce.md` | — |

---

## 用户故事

### US-1: 渲染期 elmtId 级依赖收集

**作为** 应用开发者,
**我想要** 在 UI 渲染期读取状态变量时，框架自动记录「该 UI 元素（elmtId）依赖该状态变量」的映射关系,
**以便** 状态变量变化时仅精确重渲染读取过它的 UI 元素，而非整个组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 自定义组件执行 build/updateFunc 渲染且 `getRenderingElmtId()` 返回有效 elmtId THEN 读取任意 V1 状态变量的 `get()` 时，框架经 `recordPropertyDependentUpdate(elmtId)` 将该 elmtId 记录到该变量的 `PropertyDependencies` | 正常 |
| AC-1.2 | WHEN 同一 elmtId 在多次渲染中读取同一状态变量 THEN `PropertyDependencies` 中该 elmtId 仅记录一次（去重） | 边界 |
| AC-1.3 | WHEN 渲染完成后状态变量变更 THEN 框架查询 `PropertyDependencies` 获取依赖该变量的全部 elmtId 列表，仅对这些 elmtId 触发重渲染 | 正常 |
| AC-1.4 | WHEN 不在任何组件渲染期（非渲染上下文，`getRenderingElmtId()` 返回 `notRecordingDependencies` 即 -1）THEN 读取状态变量不记录依赖 | 边界 |
| AC-1.5 | WHEN elmtId 对应的 UI 元素被删除 THEN `UINodeRegisterProxy` 将该 elmtId 从所有 `PropertyDependencies` 中清除 | 正常 |
| AC-1.6 | WHEN 状态变量被 `@Track` 标记属性级追踪 THEN 依赖记录写入 `PropertyDependencies.trackedObjectPropertyDependencies_`（按属性名分组），而非 `propertyDependencies_` | 正常 |

### US-2: 状态变更精确通知与局部重渲染

**作为** 应用开发者,
**我想要** 修改状态变量时框架精确通知依赖该变量的 UI 元素重渲染,
**以便** UI 与状态自动保持一致，且只重渲染必要的部分。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN V1 状态变量经属性包装对象 `set()` 方法被赋新值（编译器将 `this.var = x` 编译为 `ObservedPropertyPU.set(x)`） THEN `ObservedPropertyAbstractPU.notifyPropertyHasChangedPU()` 被调用，查询 `PropertyDependencies` 获取依赖 elmtId 列表 | 正常 |
| AC-2.2 | WHEN 依赖 elmtId 列表非空 THEN 对每个 elmtId 调用所属 `ViewPU.viewPropertyHasChanged(elmtId, varName)`，将 elmtId 标记 dirty | 正常 |
| AC-2.3 | WHEN elmtId 被标记 dirty THEN `ViewPU.markNeedUpdate(elmtId)`（继承自 `PUV2ViewBase`，`puv2_view_base.ts:337-339`）将其加入下个 VSync 的更新队列 | 正常 |
| AC-2.4 | WHEN 状态变量新值与旧值严格相等（`===`）THEN 不触发 `notifyPropertyHasChangedPU`（值未变化） | 边界 |
| AC-2.5 | WHEN 依赖 elmtId 列表为空（无 UI 读取过该变量）THEN 不触发任何重渲染 | 边界 |
| AC-2.6 | WHEN PU 路径下 `notifyHasChanged`（基类遗留方法）被调用 THEN PU 覆盖该方法为空操作，使用 elmtId 级精确通知代替全量重渲染 | 正常 |

### US-3: PU 渲染路径（API 9 起统一）

**作为** 框架维护者,
**我想要** API 9 起统一使用 PU（Partial Update）渲染路径（API 9 前 FU 已废弃）,
**以便** 所有组件走 PU 获得 elmtId 级精确重渲染，无 PU/FU 开关。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN API 9+ THEN 所有组件统一走 PU（Partial Update）路径，使用 `ViewPU` 与 `ObservedPropertyAbstractPU`，无 PU/FU 开关 | 正常 |
| AC-3.2 | WHEN API 9 前 THEN 存在 FU（Full Update）历史路径（`full_update/`），API 9 后已废弃 | 边界 |
| AC-3.3 | WHEN PU 路径的 `ObservedPropertyAbstractPU.notifyHasChanged` 被调用 THEN 该方法被覆盖为空操作，通知逻辑由 `notifyPropertyHasChangedPU` 承担 | 正常 |

### US-4: dirty 元素升序更新

**作为** 应用开发者,
**我想要** 一个 VSync 周期内多次状态变更产生的多个 dirty elmtId 被合并并按树层级顺序重渲染,
**以便** 避免重复重渲染，且父组件重渲染先于子组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 一个 VSync 周期内多个状态变量变更产生多个 dirty elmtId THEN `ViewPU.updateDirtyElements()`（`pu_view.ts:1005-1043`）将其合并处理 | 正常 |
| AC-4.2 | WHEN dirty elmtId 集合中存在已删除的 elmtId THEN `updateDirtyElements` 先执行 purge 移除这些 elmtId | 正常 |
| AC-4.3 | WHEN 处理 dirty elmtId 列表 THEN 按升序排序，保证父 elmtId 先于子 elmtId 执行 `UpdateElement` | 正常 |
| AC-4.4 | WHEN 重渲染过程中产生新的 dirty elmtId（`dirtRetakenElementIds_`）THEN 合并到当前批次继续处理 | 正常 |
| AC-4.5 | WHEN dirty 集合为空 THEN `updateDirtyElements` 不执行任何重渲染 | 边界 |

### US-5: elmtId 生命周期与渲染期保护

**作为** 应用开发者,
**我想要** 框架在组件创建/删除时正确维护 elmtId 映射，并在渲染期阻止状态变量的非法修改,
**以便** 避免内存泄漏与渲染期不一致状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 自定义组件经 `observeComponentCreation2` 创建 THEN elmtId 被压入 `currentlyRenderedElmtIdStack_`，并注册到 `UINodeRegisterProxy.ElementIdToOwningViewPU_` 映射 | 正常 |
| AC-5.2 | WHEN 自定义组件被删除 THEN `aboutToBeDeletedInternal()`（`pu_view.ts:303-383`）清理其所有状态变量的订阅，并从 `UINodeRegisterProxy` 移除 elmtId 映射 | 正常 |
| AC-5.3 | WHEN 渲染进行中（`isRenderInProgress` 为 true）状态变量被修改 THEN `viewPropertyHasChanged` 检测到该状态并输出 "State variable has changed during render!" 错误日志 | 异常 |
| AC-5.4 | WHEN V1 状态变量被赋值为 `@ObservedV2` 装饰对象 THEN `checkIsSupportedValue` 拒绝该赋值，V1/V2 不应混用 | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 渲染期依赖记录 |
| AC-1.2 | US-1 | R-1 | 单元测试 依赖去重 |
| AC-1.3 | US-1 | R-3 | 单元测试 精确重渲染 |
| AC-1.4 | US-1 | R-2 | 单元测试 非渲染期不记录 |
| AC-1.5 | US-1 | R-8 | 单元测试 elmtId 删除清理 |
| AC-1.6 | US-1 | R-1 | 单元测试 @Track 属性级依赖 |
| AC-2.1 | US-2 | R-3 | 单元测试 notifyPropertyHasChangedPU |
| AC-2.2 | US-2 | R-4 | 单元测试 viewPropertyHasChanged |
| AC-2.3 | US-2 | R-4 | 代码审查 markNeedUpdate |
| AC-2.4 | US-2 | R-3 | 单元测试 值未变化不通知 |
| AC-2.5 | US-2 | R-3 | 单元测试 空依赖不重渲染 |
| AC-2.6 | US-2 | R-5 | 代码审查 PU 覆盖 notifyHasChanged |
| AC-3.1 | US-3 | R-5 | 代码审查 ViewStackProcessor 默认 PU |
| AC-3.2 | US-3 | R-6 | 代码审查 API 9 前 FU 历史 |
| AC-3.3 | US-3 | R-5 | 代码审查 PU notifyHasChanged 空操作 |
| AC-4.1 | US-4 | R-7 | 单元测试 dirty 合并 |
| AC-4.2 | US-4 | R-7 | 单元测试 purge 已删除 |
| AC-4.3 | US-4 | R-7 | 单元测试 升序更新 |
| AC-4.4 | US-4 | R-7 | 单元测试 dirtRetakenElementIds |
| AC-4.5 | US-4 | R-7 | 单元测试 空 dirty |
| AC-5.1 | US-5 | R-9 | 代码审查 observeComponentCreation2 |
| AC-5.2 | US-5 | R-9 | 代码审查 aboutToBeDeletedInternal |
| AC-5.3 | US-5 | R-10 | 单元测试 渲染期修改抛错 |
| AC-5.4 | US-5 | R-11 | 单元测试 V2 对象拒绝 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 渲染期读取状态变量 `get()` | `recordPropertyDependentUpdate(elmtId)` 将当前渲染 elmtId 记录到该变量的 `PropertyDependencies`（`pu_observed_property_abstract.ts` `PropertyDependencies` 类 line 646-773）；`@Track` 变量记录到 `trackedObjectPropertyDependencies_` 按属性名分组 | 同一 elmtId 重复读取去重 | AC-1.1, AC-1.2, AC-1.6 |
| R-2 | 边界 | 非渲染上下文读取状态变量 | `getRenderingElmtId()` 返回 `notRecordingDependencies`(-1)，不记录依赖 | 事件回调、生命周期回调、setTimeout 中读取不建立依赖 | AC-1.4 |
| R-3 | 行为 | 状态变量经属性包装对象 `set()` 赋新值 | `ObservedPropertyAbstractPU.notifyPropertyHasChangedPU()`（`pu_observed_property_abstract.ts:343-373`）查询 `PropertyDependencies` 获取依赖 elmtId 列表并通知；新值与旧值 `===` 相等则不通知；依赖列表为空则不触发重渲染 | 值未变化或无依赖时跳过 | AC-1.3, AC-2.1, AC-2.4, AC-2.5 |
| R-4 | 行为 | 依赖 elmtId 列表非空 | 对每个 elmtId 调用 `ViewPU.viewPropertyHasChanged(elmtId, varName)`（`pu_view.ts:682-734`），经 `markNeedUpdate(elmtId)`（`puv2_view_base.ts:337-339`）加入 VSync 更新队列；同时触发 `@Watch` 回调（见 Feat-06） | elmtId 所属 View 必须已注册到 `UINodeRegisterProxy` | AC-2.2, AC-2.3 |
| R-5 | 行为 | PU 路径属性变更 | PU 覆盖 `ObservedPropertyAbstract.notifyHasChanged` 为空操作，通知逻辑完全由 `notifyPropertyHasChangedPU` 承担；`ViewStackProcessor.UsesNewPipeline()` 为 true 时新组件走 PU（现代默认）；`ConfigureStateMgmt`（`state_mgmt_configure.ts:20-70`）负责 V1/V2 范式检测（`needsV2Observe`） | API 9 起统一 PU，FU 已废弃 | AC-2.6, AC-3.1, AC-3.3 |
| R-6 | 边界 | FU 历史路径（API 9 前） | API 9 前存在 FU（Full Update）历史路径，走 `ObservedPropertyAbstract.notifyHasChanged` 全量通知；API 9 后统一为 PU，FU 已废弃，无开关 | API 9+ 统一 PU | AC-3.2 |
| R-7 | 行为 | 一个 VSync 周期内产生多个 dirty elmtId | `ViewPU.updateDirtyElements()`（`pu_view.ts:1005-1043`）：先 purge 已删除 elmtId → 按 elmtId 升序排序（父先于子）→ 对每个 elmtId 执行 `UpdateElement` → 合并 `dirtRetakenElementIds_`；dirty 集合为空则跳过 | 父子顺序由 elmtId 升序保证 | AC-4.1~AC-4.5 |
| R-8 | 行为 | elmtId 对应 UI 元素被删除 | `UINodeRegisterProxy`（`pu_uinode_registry_proxy.ts`）将该 elmtId 从所有 `PropertyDependencies` 中清除，避免悬挂引用 | 删除流程与 07-02-01 Feat-09 elmtId 全链路同步协同 | AC-1.5 |
| R-9 | 行为 | 组件创建/删除 | 创建时 `observeComponentCreation2`（`pu_view.ts:1089-1179`）注册 elmtId→View 到 `UINodeRegisterProxy.ElementIdToOwningViewPU_`；删除时 `aboutToBeDeletedInternal()`（`pu_view.ts:303-383`）清理订阅与映射 | 删除顺序保证 appear/destroy 配对（本域 Feat-09） | AC-5.1, AC-5.2 |
| R-10 | 异常 | 渲染进行中（`isRenderInProgress`）状态变量被修改 | `viewPropertyHasChanged` 检测到该状态并输出 "State variable has changed during render!" 错误日志，引导开发者将修改移到事件回调/生命周期/`setTimeout` | 渲染期修改是常见误用 | AC-5.3 |
| R-11 | 异常 | V1 状态变量被赋值为 `@ObservedV2` 装饰对象 | `checkIsSupportedValue` 拒绝该赋值；V1/V2 不应混用，V1→V2 迁移见 07-02-04 | 跨域约束，V2 范式归 07-02-04 | AC-5.4 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` 渲染期依赖记录 |
| VM-2 | AC-1.2 | 单元测试 | `v1_tests/` 依赖去重 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` 精确重渲染 |
| VM-4 | AC-1.4 | 单元测试 | `v1_tests/` 非渲染期不记录依赖 |
| VM-5 | AC-1.5 | 单元测试 | `v1_tests/` elmtId 删除清理 |
| VM-6 | AC-1.6 | 单元测试 | `v1_tests/` @Track 属性级依赖 |
| VM-7 | AC-2.1 | 单元测试 | `v1_tests/` notifyPropertyHasChangedPU |
| VM-8 | AC-2.2 | 单元测试 | `v1_tests/` viewPropertyHasChanged |
| VM-9 | AC-2.3 | 代码审查 | `puv2_view_base.ts:337-339` markNeedUpdate |
| VM-10 | AC-2.4 | 单元测试 | `v1_tests/` 值未变化不通知 |
| VM-11 | AC-2.5 | 单元测试 | `v1_tests/` 空依赖不重渲染 |
| VM-12 | AC-2.6 | 代码审查 | `pu_observed_property_abstract.ts` PU 覆盖 notifyHasChanged |
| VM-13 | AC-3.1 | 代码审查 | `ViewStackProcessor` UsesNewPipeline 始终 true（API 9+ 统一 PU） |
| VM-14 | AC-3.2 | 代码审查 | API 9 前 FU 历史路径 |
| VM-15 | AC-3.3 | 代码审查 | `pu_observed_property_abstract.ts` PU notifyHasChanged 空操作 |

| VM-17 | AC-4.1 | 单元测试 | `v1_tests/` dirty 合并 |
| VM-18 | AC-4.2 | 单元测试 | `v1_tests/` purge 已删除 |
| VM-19 | AC-4.3 | 单元测试 | `v1_tests/` 升序更新 |
| VM-20 | AC-4.4 | 单元测试 | `v1_tests/` dirtRetakenElementIds |
| VM-21 | AC-4.5 | 单元测试 | `v1_tests/` 空 dirty |
| VM-22 | AC-5.1 | 代码审查 | `pu_view.ts:1089-1179` observeComponentCreation2 |
| VM-23 | AC-5.2 | 代码审查 | `pu_view.ts:303-383` aboutToBeDeletedInternal |
| VM-24 | AC-5.3 | 单元测试 | `v1_tests/` 渲染期修改抛错 |
| VM-25 | AC-5.4 | 单元测试 | `v1_tests/` V2 对象拒绝 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `ObservedPropertyAbstractPU<T>` | `pu_observed_property_abstract.ts:22-644` | PU 属性包装抽象基类，提供依赖收集、变更通知、冻结三态机 |
| `PropertyDependencies` | `pu_observed_property_abstract.ts:646-773` | 依赖映射：状态变量 → 依赖它的 elmtId 集合 |
| `recordPropertyDependentUpdate(elmtId)` | `pu_observed_property_abstract.ts` | 渲染期记录 elmtId 依赖 |
| `notifyPropertyHasChangedPU()` | `pu_observed_property_abstract.ts:343-373` | PU 主路径变更通知 |
| `getRenderingElmtId()` | `pu_observed_property_abstract.ts` | 返回当前渲染 elmtId，非渲染期返回 -1 |
| `DelayedNotifyChangesEnum` | `pu_observed_property_abstract.ts` | 冻结三态枚举（详见 Feat-06） |
| `checkIsSupportedValue` | `pu_observed_property_abstract.ts` | 拒绝 V2 对象作为 V1 状态变量 |
| `ViewPU` | `pu_view.ts:59-1667` | V1 视图抽象基类 |
| `viewPropertyHasChanged()` | `pu_view.ts:682-734` | 接收属性变更通知，标记 dirty + 触发 @Watch |
| `updateDirtyElements()` | `pu_view.ts:1005-1043` | dirty 元素升序局部重渲染 |
| `observeComponentCreation2()` | `pu_view.ts:1089-1179` | 组件创建观察，注册 elmtId→View |
| `aboutToBeDeletedInternal()` | `pu_view.ts:303-383` | 组件删除清理 |
| `markNeedUpdate(elmtId)` | `puv2_view_base.ts:337-339` | 将 elmtId 加入 VSync 更新队列（继承自 PUV2ViewBase） |
| `UINodeRegisterProxy` | `pu_uinode_registry_proxy.ts` | 全局 elmtId→`IView` 映射 |
| `ConfigureStateMgmt` | `state_mgmt_configure.ts:20-70` | V1/V2 范式检测（`needsV2Observe`）与特性开关 |
| `ObservedPropertyAbstract<T>` | `common/observed_property_abstract.ts` | 公共抽象基类，含 `createSync` 工厂（line 201）、遗留 `notifyHasChanged`（PU 覆盖为空） |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | FU（Full Update）历史路径；PU（Partial Update）引入 | 核心依赖收集与变更通知机制 | 无需迁移 |
| API 9 | PU 统一：API 9 起统一为 PU，FU 废弃，无开关 | 统一渲染路径 | 无需迁移 |
| API 10 | `PropertyDependencies` 扩展支持 `Date` 类型观测 | Date 类型状态变量可被依赖追踪 | 无需迁移 |
| API 11 | `PropertyDependencies` 扩展支持 `Map`/`Set`/联合类型观测 | Map/Set 类型状态变量可被依赖追踪 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 属性包装对象范式 | V1 每个状态变量编译为 `ObservedPropertyAbstractPU` 子类实例，包装真实值并提供 get/set 钩子；V2（07-02-04）改用 getter/setter + 全局 `ObserveV2` 单例，两套不应混用 |
| elmtId 级依赖粒度 | PU 的核心优势：依赖收集与变更通知均精确到 elmtId，而非整个组件；API 9 起统一 PU |
| 单向数据流 | 状态变量变更自上而下触发 UI 刷新；UI 不反向写状态变量；渲染期修改状态变量抛错（R-10） |
| V1/V2 共用 C++ 宿主 | V1/V2 在 C++ 侧共用同一 `CustomNode`（`core/components_ng/pattern/custom/custom_node.cpp`），仅靠 `isV2_` 区分；C++ 不参与 V1 观察逻辑 |
| VSync 合批 | 同一 VSync 周期内的多次状态变更合并为一次 `updateDirtyElements` 批次处理 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | elmtId 级精确重渲染避免全量重渲染开销；dirty 元素升序合并避免重复重渲染；`PropertyDependencies` 查询为 O(1) Map 查找 |
| 可调试性 | 日志关键字（统一走 `stateMgmtConsole`）：`ObservedPropertyPU`、`viewPropertyHasChanged`、`recordPropertyDependentUpdate`；Profiler dump：`stateMgmtDFX.enableProfiler = true` 输出每次变更的组件名/ID、装饰器类型、变量名、依赖 elmtId 列表 |
| 可观测性 | `PipelineContext::GetStateMgmtInfo(nodeIds, propertyName, jsonPath)` 上报给 `UiSessionManager`（2000ms 超时）；`hidumper -s WindowManagerService -a "-stateVariables -viewId=N"` 查询状态变量 |
| 内存 | 组件删除时 `aboutToBeDeletedInternal` 必须清理订阅与 elmtId 映射，避免悬挂引用；`UINodeRegisterProxy` 双流程同步清理（详见 07-02-01 Feat-09） |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 全部 V1 装饰器 | `@State`/`@Prop`/`@Link`/`@Provide`/`@Consume`/`@ObjectLink`/`@Watch`/`@Track`（Feat-02~06）均依赖本特性的依赖收集与变更通知机制 |
| 自定义组件机制 | `observeComponentCreation2`/`updateDirtyElements` 是 `@Component` 渲染管线核心（详见 07-02-01 Feat-06 / custom_component KB） |
| 跨域协同 | elmtId 全链路同步、`UINodeRegisterProxy` 清理流程与 07-02-01 Feat-09 协同；C++ `CustomNode`/`PipelineContext` 集成见 07-02-01 Feat-09 |
| V2 对比 | V2（07-02-04）采用 `ObserveV2` 单例 + getter/setter，无属性包装对象；V1/V2 不应混用 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts:22-644` | `ObservedPropertyAbstractPU` 抽象基类：依赖收集、变更通知、冻结三态机 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts:343-373` | `notifyPropertyHasChangedPU` PU 主路径变更通知 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts:646-773` | `PropertyDependencies` 依赖映射类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:59-1667` | `ViewPU` V1 视图抽象基类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:682-734` | `viewPropertyHasChanged` 属性变更处理 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:1005-1043` | `updateDirtyElements` dirty 元素升序重渲染 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:1089-1179` | `observeComponentCreation2` 组件创建观察 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_view.ts:303-383` | `aboutToBeDeletedInternal` 组件删除清理 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_uinode_registry_proxy.ts` | `UINodeRegisterProxy` elmtId→View 全局映射 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_configure.ts:20-70` | `ConfigureStateMgmt` V1/V2 范式检测 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_property_abstract.ts:201-203` | `ObservedPropertyAbstract.createSync` 工厂方法 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_base.ts:337-339` | `markNeedUpdate` elmtId 加入 VSync 队列（ViewPU 继承自此） |
| `frameworks/core/pipeline_ng/pipeline_context.cpp` | `RecordStateMgmtNode` dirty 计数、`GetStateMgmtInfo` 调试上报、`CallStateMgmtCleanUpIdleTaskFunc` |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | V1 装饰器、`ObservedPropertyPU` 依赖收集与通知回归测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | `SubscriberManager`、`ObservedObject`、PU/FU 基础类测试 |
