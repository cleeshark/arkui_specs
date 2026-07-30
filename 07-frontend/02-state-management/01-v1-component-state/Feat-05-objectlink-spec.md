# 特性规格

> Func-07-02-01-Feat-05 @ObjectLink 嵌套对象共享引用：固化 `@ObjectLink`（`SynchedPropertyNestedObjectPU`，无 `source_` 直接订阅 ObservedObject，共享引用双向同步）的声明约束、类型约束（API 7/11/19 演进）、只读语义、与 `@Observed` 的配合行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @ObjectLink 嵌套对象共享引用 |
| 特性编号 | Func-07-02-01-Feat-05 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | @ObjectLink API 7 起；Map/Set 继承类与联合类型 API 11 起；接收复杂类型（无 @Observed 限制）API 19 起；Function ERROR API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Baselined |
| SynchedPropertyNestedObjectPU | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_object_nested.ts` | — |
| @Observed/@ObjectLink 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-observed-and-objectlink.md` | — |
| @ObjectLink API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-objectlink.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: @ObjectLink 嵌套对象共享引用

**作为** 应用开发者,
**我想要** 用 `@ObjectLink` 在子组件接收 @Observed class 实例的共享引用（不拷贝）,
**以便** 父子组件双向同步嵌套对象的属性变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 子组件声明 `@ObjectLink obj: ClassA` THEN 创建 `SynchedPropertyNestedObjectPU<ClassA>`（`pu_synced_property_object_nested.ts:23-167`），无 `source_` 字段，直接经 `addOwningProperty` 订阅 ObservedObject | 正常 |
| AC-1.2 | WHEN @ObjectLink 变量是只读的 THEN 不能被整体赋值（运行时报错 `Cannot set property when setter is undefined`）；但其属性可被改变 | 边界 |
| AC-1.3 | WHEN ObservedObject 属性变化 THEN 遍历依赖该 ObservedObject 的所有 @ObjectLink 包装类通知更新 | 正常 |
| AC-1.4 | WHEN @ObjectLink 装饰变量 THEN 相当于指向数据源的指针，与源对象双向同步 | 正常 |
| AC-1.5 | WHEN @ObjectLink 推荐为每个数组/对象设计单独的自定义组件渲染 THEN 可观察 `Object.keys()` 返回的所有属性变化、数组项替换、class 属性变化 | 正常 |
| AC-1.6 | WHEN @ObjectLink 创建源依赖 THEN `createSourceDependency` 读 fake tracked prop 建立父重渲染依赖 | 正常 |

### US-2: @ObjectLink 类型约束与 API 19+ 扩展

**作为** 应用开发者,
**我想要** 了解 @ObjectLink 的类型约束与各 API 版本的扩展,
**以便** 正确使用 @ObjectLink 接收不同类型。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN @ObjectLink 本地初始化 THEN 编译期报错，禁止本地初始化，仅能通过构造参数从父组件传入 | 异常 |
| AC-2.2 | WHEN API 19 前 @ObjectLink 类型未显式由 @Observed 装饰 THEN 编译报错 | 异常 |
| AC-2.3 | WHEN API 19+ @ObjectLink 接收复杂类型（class、object、built-in）THEN 可被初始化，无 @Observed 限制；但观察嵌套类型仍需 @Observed 或 `makeV1Observed` 返回值 | 正常 |
| AC-2.4 | WHEN API 19+ @ObjectLink 接收未 @Observed 装饰的 class 或非 makeV1Observed 返回值 THEN 运行时告警日志 | 边界 |
| AC-2.5 | WHEN @ObjectLink 支持继承 Date/Array 的 class 实例 THEN 可观察整体赋值及对应接口调用 | 正常 |
| AC-2.6 | WHEN API 11+ @ObjectLink 支持继承 Map/Set 的 class 实例及 @Observed 类与 undefined/null 的联合类型 THEN 可被装饰 | 正常 |
| AC-2.7 | WHEN @ObjectLink 类型为简单类型（string/number/boolean 等）THEN 编译报错，不支持简单类型（需用 @Prop） | 异常 |
| AC-2.8 | WHEN API 19+ @ObjectLink 接收 @State 传递的 built-in 类型（Array/Map/Set/Date）和普通 class 对象 THEN 可观察其 API 调用和第一层变化，无需额外 @Observed | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @ObjectLink 订阅 |
| AC-1.2 | US-1 | R-2 | 单元测试 只读约束 |
| AC-1.3 | US-1 | R-1 | 单元测试 属性变化通知 |
| AC-1.4 | US-1 | R-1 | 单元测试 双向同步 |
| AC-1.5 | US-1 | R-3 | 单元测试 观察粒度 |
| AC-1.6 | US-1 | R-1 | 代码审查 createSourceDependency |
| AC-2.1 | US-2 | R-4 | 编译期校验 |
| AC-2.2 | US-2 | R-5 | 编译期校验 |
| AC-2.3 | US-2 | R-6 | 单元测试 API 19 复杂类型 |
| AC-2.4 | US-2 | R-6 | 单元测试 告警日志 |
| AC-2.5 | US-2 | R-7 | 单元测试 Date/Array 继承 |
| AC-2.6 | US-2 | R-8 | 单元测试 Map/Set/联合类型 |
| AC-2.7 | US-2 | R-9 | 编译期校验 |
| AC-2.8 | US-2 | R-6 | 单元测试 built-in 类型观察 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 子组件声明 `@ObjectLink obj: ClassA` | 创建 `SynchedPropertyNestedObjectPU<ClassA>`（`pu_synced_property_object_nested.ts:23-167`），无 `source_` 字段，直接经 `addOwningProperty` 订阅 ObservedObject；ObservedObject 属性变化遍历所有 @ObjectLink 通知；@ObjectLink 相当于指向数据源的指针，与源对象双向同步；`createSourceDependency` 读 fake tracked prop 建立父重渲染依赖 | 共享引用，不拷贝 | AC-1.1, AC-1.3~AC-1.6 |
| R-2 | 边界 | @ObjectLink 变量整体赋值 | 不能被整体赋值（运行时报错 `Cannot set property when setter is undefined`）；但其属性可被改变；整体替换需在父组件进行 | 只读引用，属性可改 | AC-1.2 |
| R-3 | 行为 | @ObjectLink 观察粒度 | 可观察 `Object.keys()` 返回的所有属性变化、数组项替换、class 属性变化；推荐为每个数组/对象设计单独的自定义组件渲染 | — | AC-1.5 |
| R-4 | 异常 | @ObjectLink 本地初始化 | 编译期报错，禁止本地初始化，仅能通过构造参数从父组件传入 | — | AC-2.1 |
| R-5 | 异常 | API 19 前 @ObjectLink 类型未由 @Observed 装饰 | 编译报错 | API 19 前必须 @Observed | AC-2.2 |
| R-6 | 行为 | API 19+ @ObjectLink 接收复杂类型 | 可接收 class、object、built-in（Array/Map/Set/Date）和普通 class 对象，无 @Observed 限制；可观察其 API 调用和第一层变化，无需额外 @Observed；接收未 @Observed 装饰的 class 或非 makeV1Observed 返回值时运行时告警 | 观察嵌套类型仍需 @Observed 或 makeV1Observed | AC-2.3, AC-2.4, AC-2.8 |
| R-7 | 行为 | @ObjectLink 支持继承 Date/Array 的 class 实例 | 可观察整体赋值及对应 `set*`/数组接口调用 | — | AC-2.5 |
| R-8 | 行为 | API 11+ @ObjectLink 支持继承 Map/Set 的 class 实例及联合类型 | 支持 @Observed 类与 undefined/null 的联合类型（如 `ClassA \| ClassB`、`ClassA \| undefined`） | API 11+ | AC-2.6 |
| R-9 | 异常 | @ObjectLink 类型为简单类型 | 编译报错，不支持简单类型；需用 @Prop | 必须复杂类型 | AC-2.7 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @ObjectLink 订阅 |
| VM-2 | AC-1.2 | 单元测试 | `v1_tests/` 只读约束 |
| VM-3 | AC-1.3 | 单元测试 | `v1_tests/` 属性变化通知 |
| VM-4 | AC-1.4 | 单元测试 | `v1_tests/` 双向同步 |
| VM-5 | AC-1.5 | 单元测试 | `v1_tests/` 观察粒度 |
| VM-6 | AC-1.6 | 代码审查 | `pu_synced_property_object_nested.ts` createSourceDependency |
| VM-7 | AC-2.1 | 编译期校验 | ArkTS 编译器 禁止本地初始化 |
| VM-8 | AC-2.2 | 编译期校验 | ArkTS 编译器 API 19 前 @Observed 必需 |
| VM-9 | AC-2.3 | 单元测试 | `v1_tests/` API 19 复杂类型 |
| VM-10 | AC-2.4 | 单元测试 | `v1_tests/` 告警日志 |
| VM-11 | AC-2.5 | 单元测试 | `v1_tests/` Date/Array 继承 |
| VM-12 | AC-2.6 | 单元测试 | `v1_tests/` Map/Set/联合类型 |
| VM-13 | AC-2.7 | 编译期校验 | ArkTS 编译器 简单类型拒绝 |
| VM-14 | AC-2.8 | 单元测试 | `v1_tests/` built-in 类型观察 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `SynchedPropertyNestedObjectPU<C>` | `pu_synced_property_object_nested.ts:23-167` | @ObjectLink 主实现，无 source_ 直接订阅 |
| `setValueInternal(newValue)` | `pu_synced_property_object_nested.ts:122-166` | @ObjectLink 值变更内部逻辑 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | @ObjectLink 引入，嵌套对象共享引用双向同步 | 嵌套对象深度观测 | 无需迁移 |
| API 11 | 支持继承 Map/Set 的 class 实例及联合类型 | 更多类型 | 无需迁移 |
| API 19 | 可接收复杂类型（无 @Observed 限制） | @ObjectLink 类型放宽 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 共享引用 vs 深拷贝 | @ObjectLink 共享引用（双向同步，不拷贝）；@Prop 深拷贝（单向同步）；嵌套场景优先 @ObjectLink |
| 只读引用 | @ObjectLink 变量不能整体赋值（运行时报错），但属性可改；整体替换需在父组件进行 |
| 必须父组件传入 | @ObjectLink 禁止本地初始化，仅能通过构造参数从父组件传入 |
| 依赖 @Observed | @ObjectLink 接收的对象需 @Observed 装饰（API 19 前必需，API 19+ 可接收非 @Observed 但告警） |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_object_nested.ts:23-167` | `SynchedPropertyNestedObjectPU` @ObjectLink 主实现 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_synced_property_object_nested.ts:122-166` | `setValueInternal` @ObjectLink 值变更 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | @ObjectLink 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-observed-and-objectlink.md` | @Observed/@ObjectLink 开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-objectlink.md` | @ObjectLink API 参考 |
