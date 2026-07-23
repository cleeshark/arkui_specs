# 特性规格

> Func-07-02-02-Feat-01 @Observed/@Track 数据对象观测与属性级追踪：固化 `@Observed`（类装饰器，实例经 `ObservedObject.createNewInternal` 包装为 ES6 Proxy，`SubscribableHandler` 系列拦截 Object/Array/Map/Set/Date 操作）、`@Track`（`TrackedObject`，属性级精确追踪，仅标记属性变化触发通知）行为规格。`@Observed` 与 `@ObjectLink`（组件内，Func-07-02-01-Feat-05）配合使用。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Observed/@Track 数据对象观测与属性级追踪 |
| 特性编号 | Func-07-02-02-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | @Observed API 7 起；@Track API 11 起；@Track 在 @ComponentV2 中不报错 API 19 起；非 @Track 属性 UI 使用错误码 140110 / Function ERROR API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Baselined |
| ObservedObject Proxy | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_object.ts` | — |
| TrackedObject | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_tracked_object.ts` | — |
| @Observed/@ObjectLink 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-observed-and-objectlink.md` | — |
| @Track 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-track.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: @Observed 类装饰器与 ES6 Proxy 代理

**作为** 应用开发者,
**我想要** 用 `@Observed` 装饰 class，使其实例的属性变化可被自动观察,
**以便** 嵌套对象的属性赋值（如 `this.obj.name = x`）触发 UI 刷新，无需手动通知。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `@Observed` 装饰 class THEN 每个 class 实例经 `ObservedObject.createNewInternal`（`observed_object.ts:912-935`）包装为 ES6 Proxy | 正常 |
| AC-1.2 | WHEN 包装 Object/class 实例 THEN 使用 `SubscribableHandler`（`observed_object.ts:119-363`）拦截属性 get/set | 正常 |
| AC-1.3 | WHEN 包装 Array THEN 使用 `SubscribableArrayHandler`（`observed_object.ts:664-875`）拦截数组操作 | 正常 |
| AC-1.4 | WHEN 包装 Map/Set THEN 使用 `SubscribableMapSetHandler`（`observed_object.ts:366-617`）拦截 Map/Set 操作 | 正常 |
| AC-1.5 | WHEN 包装 Date THEN 使用 `SubscribableDateHandler`（`observed_object.ts:619-662`）拦截 Date `set*` 接口 | 正常 |
| AC-1.6 | WHEN Proxy set trap 被触发且新值与旧值 `Reflect.get === newValue` THEN 跳过通知（值未变化） | 边界 |
| AC-1.7 | WHEN @Observed 装饰 class THEN 改变 class 原始原型链，与其他类装饰器装饰同一 class 可能冲突 | 边界 |

### US-2: @Track 属性级精确追踪

**作为** 应用开发者,
**我想要** 用 `@Track` 装饰 @Observed class 的属性，仅标记属性变化触发通知,
**以便** 避免冗余 UI 刷新，提升性能。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN @Observed class 中使用 @Track 装饰属性 THEN `TrackedObject`（`pu_tracked_object.ts:25-90`）仅对标记属性建立精确追踪 | 正常 |
| AC-2.2 | WHEN @Track 装饰属性变化 THEN 只触发该属性关联的 UI 更新（避免冗余刷新） | 正常 |
| AC-2.3 | WHEN class 对象是状态变量且无任何属性被标记 @Track THEN 行为与原先保持不变（无深度观测功能，整体级追踪） | 边界 |
| AC-2.4 | WHEN @Track 整对象赋值 THEN `notifyObjectValueAssignment` 按属性比较，fake props 触发 @Prop/@ObjectLink 源同步 | 正常 |
| AC-2.5 | WHEN @Track 装饰 Function 类型属性 THEN 不支持观察 Function 类型数据变化（修改不触发 UI 刷新） | 边界 |
| AC-2.6 | WHEN @Track 用于 @ComponentV2 的 UI（API 19+）THEN 不会引起运行时报错，但依旧不会刷新 | 边界 |

### US-3: @Track 边界与错误码

**作为** 应用开发者,
**我想要** 了解 @Track 的边界约束与错误码,
**以便** 避免 UI 中误用未标记属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN class 类中使用了 @Track 装饰器且未被 @Track 装饰的属性在 UI 中使用 THEN 运行时报错；API 23+ 返回错误码 140110 | 异常 |
| AC-3.2 | WHEN 未标记 @Track 的属性在非 UI 中使用（如事件回调函数、生命周期函数）THEN 允许使用，不报错 | 正常 |
| AC-3.3 | WHEN @Track 仅可用于 Stage 模型 THEN 非 Stage 模型不可用 | 边界 |
| AC-3.4 | WHEN @Track 不支持深度观测 THEN 嵌套对象的深层属性仍需每层 @Observed+@Track | 边界 |
| AC-3.5 | WHEN 混用包含 @Track 的 class 对象和不包含 @Track 的 class 对象 THEN 容易误用，不建议混用 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Observed 包装 |
| AC-1.2 | US-1 | R-2 | 单元测试 SubscribableHandler |
| AC-1.3 | US-1 | R-2 | 单元测试 SubscribableArrayHandler |
| AC-1.4 | US-1 | R-2 | 单元测试 SubscribableMapSetHandler |
| AC-1.5 | US-1 | R-2 | 单元测试 SubscribableDateHandler |
| AC-1.6 | US-1 | R-3 | 单元测试 值未变化跳过 |
| AC-1.7 | US-1 | R-4 | 代码审查 原型链改变 |
| AC-2.1 | US-2 | R-5 | 单元测试 @Track 精确追踪 |
| AC-2.2 | US-2 | R-5 | 单元测试 避免冗余刷新 |
| AC-2.3 | US-2 | R-6 | 单元测试 无 @Track 回退 |
| AC-2.4 | US-2 | R-7 | 单元测试 整对象赋值比较 |
| AC-2.5 | US-2 | R-8 | 单元测试 Function 不观察 |
| AC-2.6 | US-2 | R-9 | 单元测试 @ComponentV2 兼容 |
| AC-3.1 | US-3 | R-10 | 单元测试 非 @Track 属性错误码 140110 |
| AC-3.2 | US-3 | R-10 | 单元测试 非 UI 使用允许 |
| AC-3.3 | US-3 | R-11 | 编译期校验 |
| AC-3.4 | US-3 | R-12 | 单元测试 无深度观测 |
| AC-3.5 | US-3 | R-13 | 单元测试 混用约束 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `@Observed` 装饰 class | 每个 class 实例经 `ObservedObject.createNewInternal`（`observed_object.ts:912-935`）包装为 ES6 Proxy | — | AC-1.1 |
| R-2 | 行为 | 包装不同类型 ObservedObject | 按 Map/Set/Date/Array/Object 分发 handler：`SubscribableHandler`（119-363）、`SubscribableArrayHandler`（664-875）、`SubscribableMapSetHandler`（366-617）、`SubscribableDateHandler`（619-662） | handler 拦截对应操作 | AC-1.2~AC-1.5 |
| R-3 | 边界 | Proxy set trap 触发 | 新值与旧值 `Reflect.get === newValue` 则跳过通知 | 值未变化优化 | AC-1.6 |
| R-4 | 边界 | @Observed 装饰 class | 改变 class 原始原型链，与其他类装饰器装饰同一 class 可能冲突 | 文档已声明约束 | AC-1.7 |
| R-5 | 行为 | @Observed class 中使用 @Track 装饰属性 | `TrackedObject`（`pu_tracked_object.ts:25-90`）仅对标记属性建立精确追踪，仅标记属性变化触发通知，避免冗余刷新 | @Track 是属性装饰器 | AC-2.1, AC-2.2 |
| R-6 | 边界 | class 对象无任何属性被标记 @Track | 行为与原先保持不变（无深度观测功能，整体级追踪） | — | AC-2.3 |
| R-7 | 行为 | @Track 整对象赋值 | `notifyObjectValueAssignment` 按属性比较，fake props 触发 @Prop/@ObjectLink 源同步 | 按属性级比较避免冗余 | AC-2.4 |
| R-8 | 边界 | @Track 装饰 Function 类型属性 | 不支持观察 Function 类型数据变化 | Function 不观察 | AC-2.5 |
| R-9 | 边界 | @Track 用于 @ComponentV2 的 UI（API 19+） | 不会引起运行时报错，但依旧不会刷新 | V1/V2 跨域约束 | AC-2.6 |
| R-10 | 异常 | class 使用 @Track 后未标记属性在 UI 中使用 | 运行时报错；API 23+ 返回错误码 140110（`Illegal usage of not @Track'ed property on UI!`）；非 UI 中允许使用 | UI 中只能访问 @Track 属性 | AC-3.1, AC-3.2 |
| R-11 | 边界 | @Track 模型约束 | 仅可在 Stage 模型下使用 | 非 Stage 模型不可用 | AC-3.3 |
| R-12 | 边界 | @Track 深度观测 | @Track 没有深度观测功能；嵌套对象的深层属性仍需每层 @Observed+@Track | — | AC-3.4 |
| R-13 | 边界 | 混用包含 @Track 的 class 和不包含 @Track 的 class | 联合类型、类继承中易误用，不建议混用 | — | AC-3.5 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v1_tests/` @Observed 包装 |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` SubscribableHandler |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` SubscribableArrayHandler |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` SubscribableMapSetHandler |
| VM-5 | AC-1.5 | 单元测试 | `common_tests/` SubscribableDateHandler |
| VM-6 | AC-1.6 | 单元测试 | `v1_tests/` 值未变化跳过 |
| VM-7 | AC-1.7 | 代码审查 | `observed_object.ts` 原型链改变 |
| VM-8 | AC-2.1 | 单元测试 | `v1_tests/` @Track 精确追踪 |
| VM-9 | AC-2.2 | 单元测试 | `v1_tests/` 避免冗余刷新 |
| VM-10 | AC-2.3 | 单元测试 | `v1_tests/` 无 @Track 回退 |
| VM-11 | AC-2.4 | 单元测试 | `v1_tests/` 整对象赋值比较 |
| VM-12 | AC-2.5 | 单元测试 | `v1_tests/` Function 不观察 |
| VM-13 | AC-2.6 | 单元测试 | `v1_tests/` @ComponentV2 兼容 |
| VM-14 | AC-3.1 | 单元测试 | `v1_tests/` 非 @Track 属性错误码 140110 |
| VM-15 | AC-3.2 | 单元测试 | `v1_tests/` 非 UI 使用允许 |
| VM-16 | AC-3.3 | 编译期校验 | ArkTS 编译器 Stage 模型约束 |
| VM-17 | AC-3.4 | 单元测试 | `v1_tests/` 无深度观测 |
| VM-18 | AC-3.5 | 单元测试 | `v1_tests/` 混用约束 |

---

## 错误码规格

| 错误码 | 触发条件 | 错误信息 | 起始版本 |
|--------|----------|----------|----------|
| 140110 | class 使用 @Track 后，未 @Track 装饰的属性在 UI 中使用 | `Illegal usage of not @Track'ed property on UI!` | API 23 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `ObservedObject<T>` | `observed_object.ts:884-1229` | @Observed 类实例的 ES6 Proxy 包装 |
| `createNewInternal<T>()` | `observed_object.ts:912-935` | 内部工厂，按类型分发 handler |
| `SubscribableHandler` | `observed_object.ts:119-363` | Object/class 属性 get/set 拦截 |
| `SubscribableArrayHandler` | `observed_object.ts:664-875` | Array 操作拦截 |
| `SubscribableMapSetHandler` | `observed_object.ts:366-617` | Map/Set 操作拦截 |
| `SubscribableDateHandler` | `observed_object.ts:619-662` | Date `set*` 接口拦截 |
| `TrackedObject` | `pu_tracked_object.ts:25-90` | @Track 属性级精确追踪 |
| `notifyObjectValueAssignment` | `pu_tracked_object.ts` | 整对象赋值按属性比较 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | @Observed 引入，ES6 Proxy 嵌套对象代理 | 嵌套对象深度观测 | 无需迁移 |
| API 11 | @Track 引入（仅 Stage 模型） | 属性级精确追踪 | 无需迁移 |
| API 19 | @Track 在 @ComponentV2 UI 中不报错 | V1/V2 跨域兼容 | 无需迁移 |
| API 23 | 非 @Track 属性 UI 使用返回错误码 140110 | 错误码规范化 | 处理错误码 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| ES6 Proxy 代理 | @Observed class 实例经 Proxy 包装，5 类 handler 透明拦截 |
| @Track 属性级追踪 | @Track 后仅标记属性变化触发通知；未标记属性 UI 中读取报错（API 23 起错误码 140110） |
| @Track 无深度观测 | 嵌套对象的深层属性仍需每层 @Observed+@Track |
| 与 @ObjectLink 配合 | @Observed 创建可观察对象；@ObjectLink（组件内 Feat-05）在子组件接收共享引用 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_object.ts:884-1229` | `ObservedObject<T>` ES6 Proxy 包装类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_object.ts:912-935` | `createNewInternal` 内部工厂 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_object.ts:119-363` | `SubscribableHandler` Object/class 拦截 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_object.ts:664-875` | `SubscribableArrayHandler` Array 拦截 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_object.ts:366-617` | `SubscribableMapSetHandler` Map/Set 拦截 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/observed_object.ts:619-662` | `SubscribableDateHandler` Date 拦截 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_tracked_object.ts:25-90` | `TrackedObject` @Track 属性级追踪 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v1_tests/` | @Observed/@Track 行为回归测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | ObservedObject Proxy handler 测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-observed-and-objectlink.md` | @Observed/@ObjectLink 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-track.md` | @Track 开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-observed.md` | @Observed API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-track.md` | @Track API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | 错误码 140110 |
