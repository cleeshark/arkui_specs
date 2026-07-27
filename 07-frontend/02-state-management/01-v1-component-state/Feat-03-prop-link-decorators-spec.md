# 特性规格

> Func-07-02-01-Feat-03 @Prop/@Link 父子单向/双向同步：固化 `@Prop`（`SynchedPropertyOneWayPU`，父→子单向深拷贝）、`@Link`（`SynchedPropertyTwoWayPU`，父↔子双向写穿透）的同步语义、`@Prop` 的 `deepCopyObjectInternal` 环检测与 Sendable 降级、`@Link` 的 `changeNotificationIsOngoing_` 防循环、BuildNode 复用重连（`resetSource`/`resetFakeSource`）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Prop/@Link 父子单向/双向同步 |
| 特性编号 | Func-07-02-01-Feat-03 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持；@Link `$var` 语法 API 9 起；@Prop/Date 类型 API 10 起；@Prop/Map/Set/联合类型 API 11 起；@Link 数据源编译期校验与 Function ERROR API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| SynchedPropertyOneWayPU | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_one_way.ts` | — |
| SynchedPropertyTwoWayPU | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_two_way.ts` | — |
| @Prop 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-prop.md` | — |
| @Link 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-link.md` | — |
| @Prop API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-prop.md` | — |
| @Link API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-link.md` | — |

---

## 用户故事

### US-1: @Prop 父→子单向同步

**作为** 应用开发者,
**我想要** 用 `@Prop` 装饰子组件变量，建立父组件到子组件的单向同步（父变化同步给子，子修改不回写父）,
**以便** 子组件拥有独立副本，避免双向耦合。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 父组件数据源（@State/@Link/@Provide 等）变化 THEN 子组件 @Prop 被父组件数据源重置，本地所有修改被覆盖 | 正常 |
| AC-1.2 | WHEN 子组件修改 @Prop 变量 THEN 修改仅写入 `localCopyObservedObject_`，不反向同步给父组件 | 边界 |
| AC-1.3 | WHEN @Prop 允许本地初始化 THEN 无本地初始化时必须父组件传参；与 @Require 结合（API 11+）必须父组件构造传参 | 边界 |
| AC-1.4 | WHEN 应用进入后台无法触发刷新 THEN @Prop 无法从数据源更新（推荐用 @Link 代替） | 边界 |
| AC-1.5 | WHEN 数据源与 @Prop 变量类型不同 THEN 行为异常，类型需相同 | 异常 |

### US-2: @Prop 深拷贝机制

**作为** 应用开发者,
**我想要** 了解 @Prop 同步时执行深拷贝的机制与边界,
**以便** 正确处理复杂类型与性能。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN API 10+ @Prop 装饰 class/Object/Array 类型 THEN 每次父重渲染对子做 `deepCopyObjectInternal` 深拷贝 | 正常 |
| AC-2.2 | WHEN 深拷贝遇到循环引用 THEN `Map<Object,Object>` 环检测机制处理，避免无限递归 | 正常 |
| AC-2.3 | WHEN 深拷贝遇到 `__MATERIAL_REFERENCE__` 标记对象 THEN 跳过深拷贝，直接引用 | 正常 |
| AC-2.4 | WHEN 深拷贝遇到 `NativePointer` 或 `@Sendable` 对象 THEN 降级为浅拷贝，避免拷贝原生指针 | 边界 |
| AC-2.5 | WHEN 深拷贝复杂类型（如 NAPI PixelMap、RegExp）THEN 拷贝中丢失类型（深拷贝限制） | 边界 |
| AC-2.6 | WHEN 组件复用场景深嵌套数据 THEN 建议不超过 5 层（性能原因），否则用 @ObjectLink（Feat-05） | 边界 |

### US-3: @Link 父↔子双向同步

**作为** 应用开发者,
**我想要** 用 `@Link` 装饰子组件变量，建立父组件与子组件的双向同步（任一方变化同步另一方）,
**以便** 父子组件共享同一状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 父组件状态变量与子组件 @Link 绑定 THEN 双方共享相同值，任一方改变同步更新另一方 | 正常 |
| AC-3.2 | WHEN 子组件 @Link 包装类创建 THEN 将自身 this 指针注册给父组件 @State 包装类 | 正常 |
| AC-3.3 | WHEN 父组件 @State 变化 THEN 遍历更新所有依赖的系统组件和 @Link 包装类 | 正常 |
| AC-3.4 | WHEN 子组件 @Link 更新 THEN 调用父组件 @State 包装类 set 方法将数值同步回父组件；双方分别遍历依赖的系统组件更新 UI | 正常 |
| AC-3.5 | WHEN @Link 变量所属自定义组件生命周期结束 THEN @Link 变量与之共享生命周期 | 边界 |

### US-4: @Link 声明约束与防循环

**作为** 应用开发者,
**我想要** 了解 @Link 的声明约束（禁止本地初始化、必须父组件传参）与防循环机制,
**以便** 正确使用 @Link 避免常见错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN @Link 变量本地初始化（`@Link count: number = 10;`）THEN 编译期报错，禁止本地初始化 | 异常 |
| AC-4.2 | WHEN 父组件向 @Link 传参 THEN 必须用 `$var` 语法（`Child({ aLink: $aState })`）或 `Child({ aLink: this.aState })`（API 9+） | 正常 |
| AC-4.3 | WHEN API 23+ @Link 数据源非状态变量或类型不匹配 THEN 编译期报错；API 23 前为运行时错误 | 异常 |
| AC-4.4 | WHEN @Link 仅能被状态变量初始化 THEN 用常规变量初始化编译报错 | 异常 |
| AC-4.5 | WHEN @Link 双向同步触发源 set() 回声 THEN `changeNotificationIsOngoing_` 标志防止循环通知 | 正常 |
| AC-4.6 | WHEN @State 与 @Link 类型均为 `number[]` THEN 不支持将 @Link 定义为 `number` 并用 @State 数组每项创建子组件（需 @Prop 或 @Observed+@ObjectLink） | 边界 |
| AC-4.7 | WHEN @Link 装饰 `Function` 类型 THEN API 23 前运行时错误，API 23+ 编译期 ERROR | 异常 |

### US-5: BuildNode 复用重连

**作为** 框架维护者,
**我想要** 组件复用时 @Link/@Prop 正确重连数据源,
**以便** 复用组件的状态变量正确同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN BuildNode 脱离原父组件 THEN `resetSource`/`resetFakeSource` 断开与原数据源的连接 | 正常 |
| AC-5.2 | WHEN BuildNode 挂载到新父组件 THEN 经 `isSameType` 类型检查后重连到新数据源 | 正常 |
| AC-5.3 | WHEN `fakeSourceBackup_` 存在 THEN 复用重连时用于恢复 @Link/@Consume 的源引用 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Prop 单向同步 |
| AC-1.2 | US-1 | R-2 | 单元测试 @Prop 修改不回写 |
| AC-1.3 | US-1 | R-3 | 单元测试 @Prop 本地初始化约束 |
| AC-1.4 | US-1 | R-1 | 单元测试 后台不刷新 |
| AC-1.5 | US-1 | R-4 | 单元测试 类型匹配 |
| AC-2.1 | US-2 | R-5 | 单元测试 深拷贝 |
| AC-2.2 | US-2 | R-5 | 单元测试 环检测 |
| AC-2.3 | US-2 | R-5 | 单元测试 __MATERIAL_REFERENCE__ |
| AC-2.4 | US-2 | R-6 | 单元测试 Sendable 降级 |
| AC-2.5 | US-2 | R-6 | 单元测试 类型丢失 |
| AC-2.6 | US-2 | R-6 | 性能测试 深嵌套 |
| AC-3.1 | US-3 | R-7 | 单元测试 @Link 双向同步 |
| AC-3.2 | US-3 | R-7 | 代码审查 注册订阅 |
| AC-3.3 | US-3 | R-7 | 单元测试 父变化同步 |
| AC-3.4 | US-3 | R-7 | 单元测试 子变化同步 |
| AC-3.5 | US-3 | R-7 | 单元测试 生命周期 |
| AC-4.1 | US-4 | R-8 | 编译期校验 |
| AC-4.2 | US-4 | R-9 | 单元测试 $var 语法 |
| AC-4.3 | US-4 | R-10 | 编译期校验 |
| AC-4.4 | US-4 | R-10 | 编译期校验 |
| AC-4.5 | US-4 | R-11 | 单元测试 防循环 |
| AC-4.6 | US-4 | R-12 | 单元测试 数组项约束 |
| AC-4.7 | US-4 | R-13 | 编译期校验 |
| AC-5.1 | US-5 | R-14 | 单元测试 resetSource |
| AC-5.2 | US-5 | R-14 | 单元测试 重连 |
| AC-5.3 | US-5 | R-14 | 代码审查 fakeSourceBackup_ |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 父组件数据源变化 | 子组件 @Prop（`SynchedPropertyOneWayPU`，`pu_synced_property_one_way.ts:65-496`）被父组件数据源重置，本地所有修改被覆盖；单向同步 | 应用后台无法触发刷新，@Prop 无法从数据源更新 | AC-1.1, AC-1.4 |
| R-2 | 边界 | 子组件修改 @Prop 变量 | 修改仅写入 `localCopyObservedObject_`，不反向同步给父组件（设计行为） | @Prop 的 set() 仅写本地副本 | AC-1.2 |
| R-3 | 边界 | @Prop 本地初始化 | 允许本地初始化（非强制）；无本地初始化时必须父组件传参；与 @Require 结合（API 11+）必须父组件构造传参 | @Require 组合约束 | AC-1.3 |
| R-4 | 异常 | 数据源与 @Prop 变量类型不同 | 行为异常；数据源与 @Prop 变量类型需相同 | 类型一致是同步前提 | AC-1.5 |
| R-5 | 行为 | API 10+ @Prop 同步 class/Object/Array 类型 | `deepCopyObjectInternal` 执行深拷贝：`Map<Object,Object>` 环检测避免无限递归；`__MATERIAL_REFERENCE__` 标记对象跳过深拷贝直接引用；每次父重渲染重拷 | 基本类型/Map/Set/Date/Array 外类型在拷贝中丢失类型 | AC-2.1~AC-2.3 |
| R-6 | 边界 | 深拷贝遇到特殊对象 | `NativePointer`/`@Sendable` 降级浅拷贝避免拷贝原生指针；NAPI（PixelMap）、RegExp 等复杂类型拷贝中丢失类型；深嵌套建议不超过 5 层或用 @ObjectLink（Feat-05） | 性能与类型保真权衡 | AC-2.4~AC-2.6 |
| R-7 | 行为 | @Link 父↔子双向同步 | 子组件 @Link（`SynchedPropertyTwoWayPU`，`pu_synced_property_two_way.ts:23-292`）将自身 this 注册给父组件 @State；父变化遍历更新所有依赖系统组件和 @Link；子变化调用父 set 同步回父；双方分别遍历依赖系统组件更新 UI；@Link 与所属组件共享生命周期 | 双向同步共享同一值 | AC-3.1~AC-3.5 |
| R-8 | 异常 | @Link 本地初始化 | 编译期报错，禁止本地初始化（`@Link count: number = 10;` 非法） | @Link 必须父组件传参 | AC-4.1 |
| R-9 | 行为 | 父组件向 @Link 传参 | 必须用 `$var` 语法（`Child({ aLink: $aState })`）或 API 9+ 的 `Child({ aLink: this.aState })` | $var 语法为引用传递 | AC-4.2 |
| R-10 | 异常 | @Link 数据源非状态变量或类型不匹配 | API 23+：编译期报错；API 23 前：运行时错误；用常规变量初始化编译报错 | 数据源必须是状态变量 | AC-4.3, AC-4.4 |
| R-11 | 行为 | @Link 双向同步触发源 set() 回声 | `changeNotificationIsOngoing_` 标志防止循环通知：写穿透触发源 set 时，若通知正在进行则跳过回声 | 双向同步必须防止 set → notify → set 死循环 | AC-4.5 |
| R-12 | 边界 | @State 与 @Link 类型均为 `number[]` | 不支持将 @Link 定义为 `number` 并用 @State 数组每项创建子组件；需 @Prop 或 @Observed+@ObjectLink（Feat-05） | 数组项级同步用 @ObjectLink | AC-4.6 |
| R-13 | 异常 | @Link/@Prop 装饰 `Function` 类型 | API 23 前：运行时错误；API 23+：编译期 ERROR（错误码 140115 间接相关） | Function 类型不支持 | AC-4.7 |
| R-14 | 行为 | BuildNode 复用重连 | `resetSource`/`resetFakeSource` 断开原数据源；`isSameType` 类型检查后重连新数据源；`fakeSourceBackup_` 恢复 @Link/@Consume 源引用 | 复用重连三件套协同 @Consume 重连（Feat-04） | AC-5.1~AC-5.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @Prop 单向同步 |
| VM-2 | AC-1.2 | 单元测试 | `v1_tests/` @Prop 修改不回写 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` @Prop 本地初始化约束 |
| VM-4 | AC-1.4 | 单元测试 | `v1_tests/` 后台不刷新 |
| VM-5 | AC-1.5 | 单元测试 | `v1_tests/` 类型匹配 |
| VM-6 | AC-2.1 | 单元测试 | `v1_tests/` 深拷贝 |
| VM-7 | AC-2.2 | 单元测试 | `v1_tests/` 环检测 |
| VM-8 | AC-2.3 | 单元测试 | `v1_tests/` __MATERIAL_REFERENCE__ |
| VM-9 | AC-2.4 | 单元测试 | `v1_tests/` Sendable 降级 |
| VM-10 | AC-2.5 | 单元测试 | `v1_tests/` 类型丢失 |
| VM-11 | AC-2.6 | 性能测试 | `performance_tests/` 深嵌套 |
| VM-12 | AC-3.1 | 单元测试 | `v1_tests/` @Link 双向同步 |
| VM-13 | AC-3.2 | 代码审查 | `pu_synced_property_two_way.ts:23-292` 注册订阅 |
| VM-14 | AC-3.3 | 单元测试 | `v1_tests/` 父变化同步 |
| VM-15 | AC-3.4 | 单元测试 | `v1_tests/` 子变化同步 |
| VM-16 | AC-3.5 | 单元测试 | `v1_tests/` 生命周期 |
| VM-17 | AC-4.1 | 编译期校验 | ArkTS 编译器 禁止本地初始化 |
| VM-18 | AC-4.2 | 单元测试 | `v1_tests/` $var 语法 |
| VM-19 | AC-4.3 | 编译期校验 | ArkTS 编译器 API 23+ 数据源校验 |
| VM-20 | AC-4.4 | 编译期校验 | ArkTS 编译器 常规变量拒绝 |
| VM-21 | AC-4.5 | 单元测试 | `v1_tests/` 防循环 |
| VM-22 | AC-4.6 | 单元测试 | `v1_tests/` 数组项约束 |
| VM-23 | AC-4.7 | 编译期校验 | ArkTS 编译器 Function ERROR |
| VM-24 | AC-5.1 | 单元测试 | `v1_tests/` resetSource |
| VM-25 | AC-5.2 | 单元测试 | `v1_tests/` 重连 |
| VM-26 | AC-5.3 | 代码审查 | `pu_synced_property_two_way.ts` fakeSourceBackup_ |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `SynchedPropertyOneWayPU<C>` | `pu_synced_property_one_way.ts:65-496` | @Prop 主实现，父→子单向深拷贝同步 |
| `deepCopyObjectInternal` | `pu_synced_property_one_way.ts` | API 10+ 深拷贝，环检测 + `__MATERIAL_REFERENCE__` 跳过 |
| `SynchedPropertySimpleOneWayPU<T>` | `pu_synced_property_one_way.ts:499-501` | 简单类型变体 |
| `SynchedPropertyObjectOneWayPU<T>` | `pu_synced_property_one_way.ts:503-505` | Object 变体 |
| `SynchedPropertyTwoWayPU<C>` | `pu_synced_property_two_way.ts:23-292` | @Link/@Consume 主实现，父↔子双向写穿透 |
| `changeNotificationIsOngoing_` | `pu_synced_property_two_way.ts` | 防循环通知标志 |
| `resetSource`/`resetFakeSource`/`fakeSourceBackup_` | `pu_synced_property_two_way.ts` | BuildNode 复用重连 |
| `isSameType` | `pu_synced_property_two_way.ts` | 复用重连类型检查 |
| `SynchedPropertyObjectTwoWayPU<C>` | `pu_synced_property_two_way.ts:295-297` | Object 变体 |
| `SynchedPropertySimpleTwoWayPU<T>` | `pu_synced_property_two_way.ts:299-301` | 简单类型变体 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | @Prop/@Link 引入，父→子单向 / 父↔子双向同步 | 核心父子同步装饰器 | 无需迁移 |
| API 9 | @Link 新增 `Child({ aLink: this.aState })` 语法（除 `$var` 外） | @Link 传参方式扩展 | 可选用新语法 |
| API 10 | @Prop 新增 `Date` 类型；@Prop 深拷贝机制（`deepCopyObjectInternal` 环检测）引入 | 复杂类型深拷贝同步 | 无需迁移 |
| API 11 | @Prop/@Link 新增 `Map`/`Set`/联合类型；@Prop 配 @Require 必须父组件构造传参 | 更多类型支持 | 无需迁移 |
| API 23 | @Link 数据源非状态变量/类型不匹配从运行时错误变为编译期报错；@Prop/@Link 装饰 Function 类型从运行时错误变为编译期 ERROR | 编译期更强校验 | 修正数据源类型 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| @Prop 单向 | 父→子单向同步，子修改不回写；@Prop 拥有独立副本（深拷贝） |
| @Link 双向 | 父↔子双向同步，共享同一值；@Link 禁止本地初始化，必须父组件 `$var` 传参 |
| @Prop 深拷贝 | API 10+ 复杂类型执行 `deepCopyObjectInternal` 深拷贝；`NativePointer`/`@Sendable` 降级浅拷贝 |
| @Link 防循环 | `changeNotificationIsOngoing_` 标志防止双向同步死循环 |
| 复用重连 | BuildNode 复用时 `resetSource`/`resetFakeSource`/`isSameType`/`fakeSourceBackup_` 协同重连数据源 |
| 第一层观察边界 | @Prop/@Link 的 class/Object 仅观察整体赋值与第一层属性；嵌套需 @Observed+@ObjectLink（Feat-05） |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | @Prop 深拷贝（API 10+）有递归开销，深嵌套数据建议不超过 5 层或用 @ObjectLink；@Link 双向同步为引用传递，无拷贝开销 |
| 可调试性 | @Prop 断点：`constructor`/`reset`/`syncPeerHasChanged`/`resetLocalValue`/`deepCopyObjectInternal`；@Link 断点：`constructor`/`set`/`setObject`/`syncPeerHasChanged`/`resetSource`/`isSameType` |
| 可观测性 | `hidumper -s WindowManagerService -a "-stateVariables -viewId=N"` 查询 @Prop/@Link 同步状态 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 父子组件通信 | @Prop/@Link 是 ArkUI 父子组件状态同步的核心机制；@Prop 单向适合只读输入，@Link 双向适合共享编辑 |
| 跨层级同步基础 | @Link 经 `initializeConsume` 升级为 @Consume（Feat-04），支持祖先-后代双向同步 |
| 嵌套观测协同 | @Prop/@Link 装饰 @Observed class 时，ObservedObject Proxy 代理嵌套属性变化（Feat-05）；@ObjectLink 是嵌套对象的引用同步替代方案 |
| @Watch 监听基础 | @Prop/@Link 变量可叠加 @Watch 装饰器监听变化回调（Feat-06） |
| 组件复用协同 | BuildNode 复用时 @Prop/@Link 经重连三件套恢复同步（与 @Consume 重连三件套协同，Feat-04） |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_one_way.ts:65-496` | `SynchedPropertyOneWayPU` @Prop 主实现 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_one_way.ts` | `deepCopyObjectInternal` 深拷贝、环检测、`__MATERIAL_REFERENCE__` 跳过 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_two_way.ts:23-292` | `SynchedPropertyTwoWayPU` @Link/@Consume 主实现 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_two_way.ts` | `changeNotificationIsOngoing_` 防循环、`resetSource`/`resetFakeSource`/`fakeSourceBackup_`/`isSameType` 复用重连 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | @Prop/@Link 同步语义、深拷贝、复用重连回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-prop.md` | @Prop 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-link.md` | @Link 开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-prop.md` | @Prop API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-link.md` | @Link API 参考 |
