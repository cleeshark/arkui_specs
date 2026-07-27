# 特性规格

> Func-07-02-01-Feat-02 @State 组件私有状态：固化 `@State` 装饰器的声明约束、`ObservedPropertyPU` 的 `setValueInternal` 5 分支自动包装、允许的变量类型矩阵（API 7/10/11/23 演进）、观察粒度（基本类型/对象第一层/数组/Date/Map/Set）、必须本地初始化与父组件初始值语义行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @State 组件私有状态 |
| 特性编号 | Func-07-02-01-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持；Date 类型 API 10 起；Map/Set/undefined/null/Length/ResourceStr/ResourceColor/联合类型 API 11 起；Function 类型编译期 ERROR API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| ObservedPropertyPU | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property.ts` | — |
| @State 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-state.md` | — |
| @State API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-state.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: @State 变量声明与初始化

**作为** 应用开发者,
**我想要** 用 `@State` 装饰器声明组件私有状态变量并必须本地初始化,
**以便** 该变量成为组件内部可观察状态，赋值时自动触发依赖该变量的 UI 重渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 `@Component` 中声明 `@State count: number = 10` THEN 框架编译期为该变量创建 `ObservedPropertyPU<number>` 实例包装初始值 10 | 正常 |
| AC-1.2 | WHEN `@State` 变量未本地初始化（如 `@State count: number;`）THEN 编译期报错，要求必须本地初始化 | 异常 |
| AC-1.3 | WHEN 父组件构造时传入非 `undefined` 值（`Child({ count: this.parentVar })`）THEN 父组件值覆盖 @State 本地初始值，仅作初始值使用 | 正常 |
| AC-1.4 | WHEN 父组件构造时传入 `undefined` THEN @State 保留本地默认初始值 | 边界 |
| AC-1.5 | WHEN 父组件外部变量后续变化 THEN 该变化不同步至子组件 @State（父组件外部变量仅作初始值） | 边界 |

### US-2: @State 值类型自动包装

**作为** 应用开发者,
**我想要** 框架根据赋值类型自动选择合适的包装策略,
**以便** 简单类型、`@Observed` 对象、`SubscribableAbstract` 等不同类型都能正确观察。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN @State 被赋值为简单类型（number/string/boolean）THEN `setValueInternal`（`pu_observed_property.ts:90-132`）走简单类型分支，直接存储值并触发 `notifyPropertyHasChangedPU` | 正常 |
| AC-2.2 | WHEN @State 被赋值为已 `@Observed` 装饰的 class 实例 THEN `setValueInternal` 走 ObservedObject 分支，将该属性注册为该 ObservedObject 的订阅者 | 正常 |
| AC-2.3 | WHEN @State 被赋值为普通对象（未 @Observed）THEN `setValueInternal` 走普通对象分支，按需包装 | 正常 |
| AC-2.4 | WHEN @State 被赋值为 `SubscribableAbstract` 子类实例 THEN `setValueInternal` 走 `SubscribableAbstract` 分支，订阅其通知 | 正常 |
| AC-2.5 | WHEN Interop 模式启用且值为静态代理对象 THEN `setValueInternal` 走 Interop 分支（本域 Feat-09） | 正常 |

### US-3: @State 类型支持矩阵

**作为** 应用开发者,
**我想要** 明确 @State 支持的变量类型与各 API 版本的演进,
**以便** 正确使用类型并了解版本约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN API 7+ THEN @State 支持 `object`/`class`/`string`/`number`/`boolean`/`enum` 及这些类型的数组 | 正常 |
| AC-3.2 | WHEN API 10+ THEN @State 额外支持 `Date` 类型 | 正常 |
| AC-3.3 | WHEN API 11+ THEN @State 额外支持 `Map`/`Set`/`undefined`/`null`/`Length`/`ResourceStr`/`ResourceColor` 及这些类型的联合类型 | 正常 |
| AC-3.4 | WHEN API 23 前 @State 装饰 `Function` 类型变量 THEN 运行时错误 | 异常 |
| AC-3.5 | WHEN API 23+ @State 装饰 `Function` 类型变量 THEN 编译期 ERROR | 异常 |

### US-4: @State 观察粒度

**作为** 应用开发者,
**我想要** 了解 @State 对不同类型的观察粒度（哪些操作可被观察）,
**以便** 正确触发 UI 刷新，避免无法观察的深层修改。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `boolean`/`string`/`number` 类型 @State 被赋新值 THEN 框架观察到变化并触发依赖 UI 刷新 | 正常 |
| AC-4.2 | WHEN `class`/`Object` 类型 @State 被整体赋值，或其第一层属性（`Object.keys()` 返回的属性）被赋值 THEN 可被观察；嵌套对象第二层及更深的属性赋值无法观察 | 边界 |
| AC-4.3 | WHEN `Array` 类型 @State 被整体赋值、数组项赋值，或调用 `push`/`pop`/`shift`/`unshift`/`splice`/`copyWithin`/`fill`/`reverse`/`sort` THEN 可被观察；数组项的嵌套属性赋值无法观察 | 正常 |
| AC-4.4 | WHEN `Date` 类型 @State 被整体赋值或调用 `setFullYear`/`setMonth`/`setDate`/`setHours`/`setMinutes`/`setSeconds`/`setMilliseconds`/`setTime`/`setUTC*` THEN 可被观察 | 正常 |
| AC-4.5 | WHEN `Map` 类型 @State 被整体赋值或调用 `set`/`clear`/`delete` THEN 可被观察 | 正常 |
| AC-4.6 | WHEN `Set` 类型 @State 被整体赋值或调用 `add`/`clear`/`delete` THEN 可被观察 | 正常 |
| AC-4.7 | WHEN 需要观察 `class`/`Object` 的嵌套属性（第二层及更深）THEN 必须使用 `@Observed`+`@ObjectLink`（见 Feat-05），@State 仅观察第一层 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @State 创建包装 |
| AC-1.2 | US-1 | R-2 | 编译期校验 |
| AC-1.3 | US-1 | R-3 | 单元测试 父组件初始值覆盖 |
| AC-1.4 | US-1 | R-3 | 单元测试 undefined 保留默认值 |
| AC-1.5 | US-1 | R-4 | 单元测试 父后续变化不同步 |
| AC-2.1 | US-2 | R-5 | 单元测试 简单类型分支 |
| AC-2.2 | US-2 | R-5 | 单元测试 ObservedObject 分支 |
| AC-2.3 | US-2 | R-5 | 单元测试 普通对象分支 |
| AC-2.4 | US-2 | R-5 | 单元测试 SubscribableAbstract 分支 |
| AC-2.5 | US-2 | R-5 | 代码审查 Interop 分支 |
| AC-3.1 | US-3 | R-6 | 单元测试 API 7 类型 |
| AC-3.2 | US-3 | R-6 | 单元测试 Date 类型 |
| AC-3.3 | US-3 | R-6 | 单元测试 Map/Set/联合类型 |
| AC-3.4 | US-3 | R-7 | 单元测试 Function 运行时错误 |
| AC-3.5 | US-3 | R-7 | 编译期校验 |
| AC-4.1 | US-4 | R-8 | 单元测试 简单类型观察 |
| AC-4.2 | US-4 | R-9 | 单元测试 对象第一层观察 |
| AC-4.3 | US-4 | R-10 | 单元测试 数组观察 |
| AC-4.4 | US-4 | R-11 | 单元测试 Date 观察 |
| AC-4.5 | US-4 | R-12 | 单元测试 Map 观察 |
| AC-4.6 | US-4 | R-13 | 单元测试 Set 观察 |
| AC-4.7 | US-4 | R-9 | 单元测试 嵌套属性需 @Observed |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在 `@Component` 中声明 `@State var: T = init` | 编译期为该变量创建 `ObservedPropertyPU<T>`（`pu_observed_property.ts:27-193`）实例包装初始值，注册到所属 `ViewPU` | 变量生命周期与所属自定义组件相同 | AC-1.1 |
| R-2 | 异常 | `@State` 变量未本地初始化 | 编译期报错，要求必须本地初始化（`@State count: number;` 非法） | — | AC-1.2 |
| R-3 | 行为 | 父组件构造时传入值 | 传入非 `undefined` 值覆盖 @State 本地初始值（仅作初始值）；传入 `undefined` 保留本地默认值；父组件外部变量后续变化不同步至 @State | 父组件传入仅作初始值，无持续同步 | AC-1.3, AC-1.4 |
| R-4 | 边界 | 父组件外部变量在子组件 @State 初始化后变化 | 该变化不同步至子组件 @State；@State 不与父组件任何类型变量同步 | 需要同步用 @Prop/@Link（Feat-03） | AC-1.5 |
| R-5 | 行为 | @State 被赋新值 | `ObservedPropertyPU.setValueInternal()`（`pu_observed_property.ts:90-132`）按值类型 5 分支自动包装：Interop（静态代理）/ 简单类型 / `SubscribableAbstract` / 已 ObservedObject / 普通对象；包装后调用 `notifyPropertyHasChangedPU` | Interop 分支本域 Feat-09 | AC-2.1~AC-2.5 |
| R-6 | 行为 | @State 装饰变量 | 允许类型：API 7 `object`/`class`/`string`/`number`/`boolean`/`enum` 及数组；API 10 +`Date`；API 11 +`Map`/`Set`/`undefined`/`null`/`Length`/`ResourceStr`/`ResourceColor` 及联合类型 | 类型矩阵随 API 版本扩展 | AC-3.1~AC-3.3 |
| R-7 | 异常 | @State 装饰 `Function` 类型变量 | API 23 前：运行时错误；API 23+：编译期 ERROR（错误码 140115 间接相关） | Function 类型不支持 | AC-3.4, AC-3.5 |
| R-8 | 行为 | `boolean`/`string`/`number` 类型 @State 被赋新值 | 框架观察到变化（`===` 不等）并触发依赖 UI 刷新 | 新值与旧值严格相等则不触发 | AC-4.1 |
| R-9 | 行为 | `class`/`Object` 类型 @State | 可观察整体赋值与第一层属性（`Object.keys()` 返回）赋值；嵌套对象第二层及更深属性赋值无法观察（需 @Observed+@ObjectLink，Feat-05） | 第一层为观察边界 | AC-4.2, AC-4.7 |
| R-10 | 行为 | `Array` 类型 @State | 可观察整体赋值、数组项赋值，以及 `push`/`pop`/`shift`/`unshift`/`splice`/`copyWithin`/`fill`/`reverse`/`sort` 接口调用；数组项嵌套属性赋值无法观察 | — | AC-4.3 |
| R-11 | 行为 | `Date` 类型 @State | 可观察整体赋值，以及 `setFullYear`/`setMonth`/`setDate`/`setHours`/`setMinutes`/`setSeconds`/`setMilliseconds`/`setTime`/`setUTC*` 接口调用 | API 10+ | AC-4.4 |
| R-12 | 行为 | `Map` 类型 @State | 可观察整体赋值，以及 `set`/`clear`/`delete` 接口调用 | API 11+ | AC-4.5 |
| R-13 | 行为 | `Set` 类型 @State | 可观察整体赋值，以及 `add`/`clear`/`delete` 接口调用 | API 11+ | AC-4.6 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @State 创建包装 |
| VM-2 | AC-1.2 | 编译期校验 | ArkTS 编译器 未初始化报错 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` 父组件初始值覆盖 |
| VM-4 | AC-1.4 | 单元测试 | `v1_tests/` undefined 保留默认值 |
| VM-5 | AC-1.5 | 单元测试 | `v1_tests/` 父后续变化不同步 |
| VM-6 | AC-2.1 | 单元测试 | `v1_tests/` 简单类型分支 |
| VM-7 | AC-2.2 | 单元测试 | `v1_tests/` ObservedObject 分支 |
| VM-8 | AC-2.3 | 单元测试 | `v1_tests/` 普通对象分支 |
| VM-9 | AC-2.4 | 单元测试 | `v1_tests/` SubscribableAbstract 分支 |
| VM-10 | AC-2.5 | 代码审查 | `pu_observed_property.ts:90-132` Interop 分支 |
| VM-11 | AC-3.1 | 单元测试 | `v1_tests/` API 7 类型 |
| VM-12 | AC-3.2 | 单元测试 | `v1_tests/` Date 类型 |
| VM-13 | AC-3.3 | 单元测试 | `v1_tests/` Map/Set/联合类型 |
| VM-14 | AC-3.4 | 单元测试 | `v1_tests/` Function 运行时错误 |
| VM-15 | AC-3.5 | 编译期校验 | ArkTS 编译器 API 23+ ERROR |
| VM-16 | AC-4.1 | 单元测试 | `v1_tests/` 简单类型观察 |
| VM-17 | AC-4.2 | 单元测试 | `v1_tests/` 对象第一层观察 |
| VM-18 | AC-4.3 | 单元测试 | `v1_tests/` 数组观察 |
| VM-19 | AC-4.4 | 单元测试 | `v1_tests/` Date 观察 |
| VM-20 | AC-4.5 | 单元测试 | `v1_tests/` Map 观察 |
| VM-21 | AC-4.6 | 单元测试 | `v1_tests/` Set 观察 |
| VM-22 | AC-4.7 | 单元测试 | `v1_tests/` 嵌套属性需 @Observed |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `ObservedPropertyPU<T>` | `pu_observed_property.ts:27-193` | @State 主实现类 |
| `setValueInternal(newValue)` | `pu_observed_property.ts:90-132` | 5 分支自动包装（Interop/简单/SubscribableAbstract/ObservedObject/普通对象） |
| `ObservedPropertyObjectPU<T>` | `pu_observed_property.ts:196-198` | Object 变体（空子类透传） |
| `ObservedPropertySimplePU<T>` | `pu_observed_property.ts:200-202` | 简单类型变体（空子类透传） |
| `aboutToBeDeleted()` | `pu_observed_property.ts:39-43` | 组件删除时清理订阅 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | @State 引入，支持 `object`/`class`/`string`/`number`/`boolean`/`enum` 及数组 | 核心状态变量装饰器 | 无需迁移 |
| API 9 | 卡片能力支持 | @State 可在卡片中使用 | 无需迁移 |
| API 10 | 新增 `Date` 类型支持 | Date 状态变量可观察 `set*`/`setUTC*` 接口 | 无需迁移 |
| API 11 | 新增 `Map`/`Set`/`undefined`/`null`/`Length`/`ResourceStr`/`ResourceColor` 及联合类型 | 更多类型可观察 | 无需迁移 |
| API 23 | `Function` 类型从运行时错误改为编译期 ERROR | 装饰 Function 类型在编译期即被拒绝 | 移除 Function 类型状态变量 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 必须本地初始化 | `@State` 变量必须本地初始化，编译期强制；未初始化编译报错 |
| 不同步父组件 | @State 不与父组件任何类型变量持续同步；父组件传入仅作初始值，后续变化不同步；需要同步用 @Prop/@Link（Feat-03） |
| 第一层观察边界 | `class`/`Object` 仅观察整体赋值与第一层属性；嵌套对象第二层及更深属性赋值无法观察（需 @Observed+@ObjectLink，Feat-05） |
| 依赖收集与变更通知 | @State 复用 Feat-01 的 `ObservedPropertyAbstractPU` 基类机制：渲染期 `recordPropertyDependentUpdate` 收集依赖，`notifyPropertyHasChangedPU` 触发通知 |
| 值严格相等优化 | 新值与旧值 `===` 相等时不触发通知，避免冗余刷新 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 简单类型赋值为直接存储 + Map 查找通知；对象赋值按值类型分支包装，ObservedObject 分支有订阅注册开销 |
| 可调试性 | 断点建议：`ObservedPropertyPU.set()` → `setValueInternal()` → `notifyPropertyHasChangedPU()` → `ViewPU.viewPropertyHasChanged()`；`this.dumpStateVars()` 输出所有状态变量值 |
| 可观测性 | `hidumper -s WindowManagerService -a "-stateVariables -viewId=N"` 查询 @State 变量值与依赖 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 父子同步基础 | @State 是 @Prop/@Link 的父端数据源（Feat-03）；@State 整体赋值或第一层属性变化触发子组件 @Prop 重拷贝 / @Link 双向同步 |
| 跨层级同步基础 | @State 经 `addProvidedVar` 升级为 @Provide（Feat-04），向后代组件暴露同步入口 |
| 嵌套观测基础 | @State 装饰 @Observed class 实例时，ObservedObject Proxy 代理嵌套属性变化（Feat-05） |
| @Watch 监听基础 | @State 变量可叠加 @Watch 装饰器监听变化回调（Feat-06） |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property.ts:27-193` | `ObservedPropertyPU<T>` @State 主实现类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property.ts:90-132` | `setValueInternal` 5 分支自动包装 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property.ts:196-202` | `ObservedPropertyObjectPU`/`ObservedPropertySimplePU` 变体 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_observed_property_abstract.ts:22-644` | `ObservedPropertyAbstractPU` 基类（依赖收集、变更通知，详见 Feat-01） |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | @State 装饰器行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-state.md` | @State 开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-state.md` | @State API 参考 |
