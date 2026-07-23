# 特性规格

> Func-07-02-05-Feat-01 @ObservedV2/@Trace 可观察数据模型：固化 `@ObservedV2`（类装饰器，`observedV2Internal` 5 步构造）、`@Trace`（属性装饰器，委托 `trackInternal` 安装 getter/setter）的声明约束、嵌套深度观测、继承链传递、内置类型 API 观测（Array/Date/Map/Set）、与 V1 `@Observed`/`@Track` 的范式差异行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @ObservedV2/@Trace 可观察数据模型 |
| 特性编号 | Func-07-02-05-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 12 起；ArkTS 卡片 API 12 起；原子化服务 API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Draft |
| V2 装饰器定义 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts` | — |
| observedV2Internal | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts` | — |
| trackInternal | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts` | — |
| @Type 实现 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/json_coder.ts` | — |
| @ObservedV2/@Trace 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-observedV2-and-trace.md` | — |
| @ObservedV2 API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-observedv2.md` | — |
| @Trace API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-trace.md` | — |

---

## 用户故事

### US-1: @ObservedV2 类装饰器

**作为** 应用开发者,
**我想要** 用 `@ObservedV2` 装饰 class，将其标记为可观察数据模型,
**以便** 配合 @Trace 实现属性级深度观测，无需 V1 的逐层 @Observed+@ObjectLink。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `@ObservedV2` 装饰 class THEN `observedV2Internal`（`v2_decorated_variables.ts:324-357`）执行 5 步构造：V1 `@Track` 冲突检查 → @Trace 计数 → ID_REFS（>5 属性）→ `AsyncAddComputedV2`/`AsyncAddMonitorV2` 微任务注册 → `WeakRefPool.asyncRegisterToFinalizationRegistry` | 正常 |
| AC-1.2 | WHEN @ObservedV2 装饰 class THEN 必须通过 `new` 实例化才具备观测能力；`JSON.parse` 反序列化得到的对象无观测能力（需配合 `UIUtils.makeObserved` 或三方库 `plainToInstance`） | 边界 |
| AC-1.3 | WHEN @ObservedV2 单独使用（无 @Trace）THEN 无实际观测能力，必须与 @Trace 配合 | 边界 |
| AC-1.4 | WHEN @ObservedV2 装饰 struct THEN 编译报错（不能装饰 struct） | 异常 |
| AC-1.5 | WHEN @ObservedV2 与 V1 @Observed/@Track 混用于同一 class THEN 编译报错（V1/V2 装饰器不能混用） | 异常 |

### US-2: @Trace 属性深度观测

**作为** 应用开发者,
**我想要** 用 `@Trace` 装饰 @ObservedV2 类的属性，使其变化可被观察,
**以便** 属性级精确追踪，嵌套对象的深层属性变化也能触发 UI 刷新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `@Trace` 装饰 @ObservedV2 类的属性 THEN `Trace`（`v2_decorators.ts:53`）委托 `trackInternal` 安装 getter/setter | 正常 |
| AC-2.2 | WHEN @Trace 属性变化（setter 触发，严格 `!==`）THEN 触发 `fireChange`，只通知关联 UI（属性级精确追踪） | 正常 |
| AC-2.3 | WHEN @Trace 装饰非 @ObservedV2 类的属性 THEN 缺 GC 清理、@Computed/@Monitor 构造、ID_REFS 优化，行为不完整 | 边界 |
| AC-2.4 | WHEN @Trace 装饰静态属性 THEN 静态属性也支持观测 | 正常 |
| AC-2.5 | WHEN @Trace 装饰 Function 类型属性 THEN 不支持观察（修改 Function 类型 UI 不刷新） | 边界 |

### US-3: 嵌套深度观测与继承

**作为** 应用开发者,
**我想要** 嵌套类对象每层 @ObservedV2+@Trace 实现深度观测，且继承链自动传递可观察性,
**以便** 复杂数据结构无需 V1 的逐层 @ObjectLink 拆解。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 嵌套类对象的属性变化 THEN 嵌套类需被 @ObservedV2 装饰 + 属性被 @Trace 才能触发刷新（每层 @ObservedV2+@Trace） | 正常 |
| AC-3.2 | WHEN 每层 @Trace getter 调用 THEN 调 `addRef` 逐层记录依赖 | 正常 |
| AC-3.3 | WHEN 父类被 @ObservedV2 装饰 THEN 子类自动继承可观察性 | 正常 |
| AC-3.4 | WHEN 继承自 @ObservedV2 的类与 V1 @State 混用 THEN 运行时报错（V1/V2 范式冲突） | 异常 |

### US-4: 内置类型 API 观测

**作为** 应用开发者,
**我想要** @Trace 装饰的 Array/Date/Map/Set 属性的接口调用可被观察,
**以便** 集合操作（push/set/add 等）触发 UI 刷新。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN @Trace Array 属性调用 `push`/`pop`/`shift`/`unshift`/`splice`/`copyWithin`/`fill`/`reverse`/`sort` THEN 可被观察（经 `ArrayProxyHandler`） | 正常 |
| AC-4.2 | WHEN @Trace Date 属性调用 `setFullYear`/`setMonth`/`setDate`/`setHours`/`setMinutes`/`setSeconds`/`setMilliseconds`/`setTime`/`setUTC*` THEN 可被观察（经 `autoProxyObject` 包装为 Date 代理） | 正常 |
| AC-4.3 | WHEN @Trace Map 属性调用 `set`/`clear`/`delete` THEN 可被观察（经 `SetMapProxyHandler`） | 正常 |
| AC-4.4 | WHEN @Trace Set 属性调用 `add`/`clear`/`delete` THEN 可被观察（经 `SetMapProxyHandler`） | 正常 |
| AC-4.5 | WHEN 集合 Proxy 拦截操作 THEN 额外加 `OB_LENGTH` 依赖（length/size 变化可观察） | 正常 |

### US-5: @Type 序列化类型标记

**作为** 应用开发者,
**我想要** 用 `@Type` 标记 @ObservedV2 类的嵌套对象属性类型,
**以便** PersistenceV2 序列化时保持原型链（详见 07-02-06）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `@Type` 装饰 @ObservedV2 类属性 THEN `__Type__`（`v2_data_coder/json_coder.ts:72`）注册到 `Meta` WeakMap（原型链继承） | 正常 |
| AC-5.2 | WHEN @Type 装饰非 @ObservedV2 类（@Observed class、自定义组件、@ComponentV2 struct）THEN 编译报错 | 异常 |
| AC-5.3 | WHEN @Type 参数为含参构造函数或 Native 类型（PixelMap/NativePointer/ArrayList）或简单类型或 collections.Set/Map THEN 不支持 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 5 步构造 |
| AC-1.2 | US-1 | R-2 | 单元测试 new vs JSON.parse |
| AC-1.3 | US-1 | R-1 | 单元测试 单独使用无效 |
| AC-1.4 | US-1 | R-3 | 编译期校验 |
| AC-1.5 | US-1 | R-4 | 编译期校验 |
| AC-2.1 | US-2 | R-5 | 单元测试 @Trace trackInternal |
| AC-2.2 | US-2 | R-5 | 单元测试 属性级精确追踪 |
| AC-2.3 | US-2 | R-6 | 单元测试 非 @ObservedV2 行为不完整 |
| AC-2.4 | US-2 | R-5 | 单元测试 静态属性 |
| AC-2.5 | US-2 | R-7 | 单元测试 Function 不观察 |
| AC-3.1 | US-3 | R-8 | 单元测试 嵌套每层 @ObservedV2+@Trace |
| AC-3.2 | US-3 | R-8 | 代码审查 addRef 逐层 |
| AC-3.3 | US-3 | R-9 | 单元测试 继承链 |
| AC-3.4 | US-3 | R-4 | 单元测试 与 @State 混用报错 |
| AC-4.1 | US-4 | R-10 | 单元测试 Array API |
| AC-4.2 | US-4 | R-10 | 单元测试 Date API |
| AC-4.3 | US-4 | R-10 | 单元测试 Map API |
| AC-4.4 | US-4 | R-10 | 单元测试 Set API |
| AC-4.5 | US-4 | R-10 | 单元测试 OB_LENGTH |
| AC-5.1 | US-5 | R-11 | 单元测试 @Type Meta 注册 |
| AC-5.2 | US-5 | R-12 | 编译期校验 |
| AC-5.3 | US-5 | R-12 | 单元测试 不支持类型 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `@ObservedV2` 装饰 class | `observedV2Internal`（`v2_decorated_variables.ts:324-357`）执行 5 步构造：V1 `@Track` 冲突检查 → @Trace 计数 → ID_REFS（>5 属性）→ `AsyncAddComputedV2`/`AsyncAddMonitorV2` 微任务注册 → `WeakRefPool.asyncRegisterToFinalizationRegistry`；单独使用（无 @Trace）无实际观测能力 | 必须与 @Trace 配合 | AC-1.1, AC-1.3 |
| R-2 | 边界 | @ObservedV2 class 实例化 | 必须通过 `new` 实例化才具备观测能力；`JSON.parse` 反序列化得到的对象无观测能力（需配合 `UIUtils.makeObserved` 或三方库 `plainToInstance`） | 反序列化场景需特殊处理 | AC-1.2 |
| R-3 | 异常 | @ObservedV2 装饰 struct | 编译报错（不能装饰 struct） | 仅 class | AC-1.4 |
| R-4 | 异常 | @ObservedV2 与 V1 @Observed/@Track 混用于同一 class | 编译报错（V1/V2 装饰器不能混用）；继承自 @ObservedV2 的类与 @State 混用运行时报错 | V1/V2 范式隔离 | AC-1.5, AC-3.4 |
| R-5 | 行为 | `@Trace` 装饰 @ObservedV2 类属性 | `Trace`（`v2_decorators.ts:53`）委托 `trackInternal`（`v2_change_observation.ts:1741-1780`）安装 getter/setter；属性变化（严格 `!==`）触发 `fireChange`，只通知关联 UI；静态属性也支持观测 | 属性级精确追踪 | AC-2.1, AC-2.2, AC-2.4 |
| R-6 | 边界 | @Trace 装饰非 @ObservedV2 类属性 | 缺 GC 清理（FinalizationRegistry 注册）、@Computed/@Monitor 构造、ID_REFS 优化，行为不完整 | 推荐仅在 @ObservedV2 类中使用 | AC-2.3 |
| R-7 | 边界 | @Trace 装饰 Function 类型属性 | 不支持观察（修改 Function 类型 UI 不刷新） | Function 不观察 | AC-2.5 |
| R-8 | 行为 | 嵌套类对象属性变化 | 嵌套类需被 @ObservedV2 装饰 + 属性被 @Trace 才能触发刷新；每层 @Trace getter 调 `addRef` 逐层记录依赖 | V2 无需 V1 的逐层 @ObjectLink | AC-3.1, AC-3.2 |
| R-9 | 行为 | 父类被 @ObservedV2 装饰 | 子类自动继承可观察性 | 继承链传递 | AC-3.3 |
| R-10 | 行为 | @Trace 内置类型 API 调用 | Array: `push`/`pop`/`shift`/`unshift`/`splice`/`copyWithin`/`fill`/`reverse`/`sort`；Date: `setFullYear`/`setMonth`/`setDate`/`setHours`/`setMinutes`/`setSeconds`/`setMilliseconds`/`setTime`/`setUTC*`；Map: `set`/`clear`/`delete`；Set: `add`/`clear`/`delete`；集合 Proxy 额外加 `OB_LENGTH` 依赖 | 经 autoProxyObject 惰性代理 | AC-4.1~AC-4.5 |
| R-11 | 行为 | `@Type` 装饰 @ObservedV2 类属性 | `__Type__`（`v2_data_coder/json_coder.ts:72`）注册到 `Meta` WeakMap（原型链继承），服务于 PersistenceV2 序列化保持原型链 | 详见 07-02-06 PersistenceV2 | AC-5.1 |
| R-12 | 异常 | @Type 装饰非 @ObservedV2 类 或 参数为不支持类型 | 编译报错（非 @ObservedV2 类）；不支持 collections.Set/Map、Native 类型（PixelMap/NativePointer/ArrayList）、简单类型、含参构造函数 | @Type 仅 @ObservedV2 类 | AC-5.2, AC-5.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` 5 步构造 |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` new vs JSON.parse |
| VM-3 | AC-1.3 | 单元测试 | `v2_tests/` 单独使用无效 |
| VM-4 | AC-1.4 | 编译期校验 | ArkTS 编译器 struct 拒绝 |
| VM-5 | AC-1.5 | 编译期校验 | ArkTS 编译器 V1/V2 混用拒绝 |
| VM-6 | AC-2.1 | 单元测试 | `v2_tests/` @Trace trackInternal |
| VM-7 | AC-2.2 | 单元测试 | `v2_tests/` 属性级精确追踪 |
| VM-8 | AC-2.3 | 单元测试 | `v2_tests/` 非 @ObservedV2 行为不完整 |
| VM-9 | AC-2.4 | 单元测试 | `v2_tests/` 静态属性 |
| VM-10 | AC-2.5 | 单元测试 | `v2_tests/` Function 不观察 |
| VM-11 | AC-3.1 | 单元测试 | `v2_tests/` 嵌套每层 @ObservedV2+@Trace |
| VM-12 | AC-3.2 | 代码审查 | `v2_change_observation.ts:423` addRef 逐层 |
| VM-13 | AC-3.3 | 单元测试 | `v2_tests/` 继承链 |
| VM-14 | AC-3.4 | 单元测试 | `v2_tests/` 与 @State 混用报错 |
| VM-15 | AC-4.1 | 单元测试 | `v2_tests/` Array API |
| VM-16 | AC-4.2 | 单元测试 | `v2_tests/` Date API |
| VM-17 | AC-4.3 | 单元测试 | `v2_tests/` Map API |
| VM-18 | AC-4.4 | 单元测试 | `v2_tests/` Set API |
| VM-19 | AC-4.5 | 单元测试 | `v2_tests/` OB_LENGTH |
| VM-20 | AC-5.1 | 单元测试 | `v2_tests/` @Type Meta 注册 |
| VM-21 | AC-5.2 | 编译期校验 | ArkTS 编译器 非 @ObservedV2 拒绝 |
| VM-22 | AC-5.3 | 单元测试 | `v2_tests/` 不支持类型 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `ObservedV2` | `v2_decorators.ts:39-43` | @ObservedV2 类装饰器工厂 |
| `Trace` | `v2_decorators.ts:53-56` | @Trace 属性装饰器，委托 trackInternal |
| `observedV2Internal` | `v2_decorated_variables.ts:324-357` | @ObservedV2 5 步构造实现 |
| `Trace_Internal` | `v2_decorated_variables.ts:309-311` | @Trace 内部，调 trackInternal |
| `trackInternal` | `v2_change_observation.ts:1741-1780` | 共享 getter/setter 安装（Feat-01） |
| `__Type__` | `v2_data_coder/json_coder.ts:72-83` | @Type 装饰器实现 |
| `Meta` | `v2_data_coder/json_coder.ts:31-70` | @Type 元信息 WeakMap（原型链继承） |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | @ObservedV2/@Trace/@Type 引入，getter/setter 范式替代 V1 @Observed/@Track 属性包装对象 | V2 可观察数据模型 | V1 @Observed+@ObjectLink 嵌套拆解迁移到 @ObservedV2+@Trace 每层装饰 |
| API 12 | 嵌套类深度观测无需 @ObjectLink 拆层 | 简化嵌套数据管理 | 直接 @ObservedV2+@Trace 装饰每层 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 必须配合使用 | @ObservedV2 单独使用无观测能力，必须与 @Trace 配合 |
| 必须 new 实例化 | @ObservedV2 class 必须通过 `new` 实例化；JSON.parse 反序列化需 makeObserved |
| V1/V2 范式隔离 | @ObservedV2 与 V1 @Observed/@Track 不能混用；继承链也不可跨范式 |
| 深度观测每层装饰 | 嵌套类对象的每层都需 @ObservedV2+@Trace（V2 无需 @ObjectLink 拆层） |
| 属性级精确追踪 | @Trace 仅标记属性变化触发通知，未标记属性不触发 |
| Function 不观察 | @Trace 装饰 Function 类型属性不触发 UI 刷新 |
| @Type 仅 @ObservedV2 | @Type 装饰器仅用于 @ObservedV2 类，服务于 PersistenceV2 序列化 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | getter/setter 范式无属性包装对象开销；ID_REFS（>5 属性）反向映射优化 clearBinding；惰性集合代理避免未读开销 |
| 可调试性 | `ObserveV2.IsObservedObjectV2(obj)` 检测；`data[ObserveV2.V2_DECO_META]` 装饰器元信息；`data.__ob_<prop>` 后备存储；`data[ObserveV2.SYMBOL_REFS]` 已注册依赖 |
| 可观测性 | `UIUtils.canBeObserved`(API 23+) 返回装饰器/组件依赖信息 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| V2 数据模型基础 | @ObservedV2+@Trace 是 V2 装饰器体系的可观察数据模型基础；@Local/@Param/@Provider 装饰的 @ObservedV2 实例属性变化均可观察 |
| PersistenceV2 协同 | @Type 标记服务于 PersistenceV2/AppStorageV2 序列化（07-02-06），保持原型链 |
| @Computed/@Monitor 基础 | @Computed 监听 @Trace 属性；@Monitor 路径遍历依赖 @Trace 逐层 addRef（Feat-04） |
| V1 对比 | V1 @Observed 仅一层观测需 @ObjectLink 拆层；V2 @ObservedV2+@Trace 每层装饰即可深度观测 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:39-43` | `ObservedV2` 类装饰器工厂 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:53-56` | `Trace` 属性装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:309-311` | `Trace_Internal` 调 trackInternal |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:324-357` | `observedV2Internal` 5 步构造 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:1741-1780` | `trackInternal` getter/setter 安装（Feat-01） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/json_coder.ts:31-70` | `Meta` @Type 元信息 WeakMap |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/json_coder.ts:72-83` | `__Type__` @Type 装饰器实现 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | @ObservedV2/@Trace/@Type 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-observedV2-and-trace.md` | @ObservedV2/@Trace 开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-observedv2.md` | @ObservedV2 API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-trace.md` | @Trace API 参考 |
