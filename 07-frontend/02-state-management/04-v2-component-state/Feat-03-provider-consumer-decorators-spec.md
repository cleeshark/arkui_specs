# 特性规格

> Func-07-02-04-Feat-03 @Provider/@Consumer V2 跨层同步：固化 `@Provider`（祖先提供，必须本地初始化，`trackInternal` + `ProviderConsumerUtilV2`）、`@Consumer`（后代消费，弱引用配对 `connectConsumer2Provider`，找不到 @Provider 用本地默认值 `defineConsumerWithoutProvider`）、alias 唯一匹配、@Provider 重名默认开启重载、Provider GC 抛错、跨 BuilderNode 配对（API 23+）行为规格与 V1 @Provide/@Consume 的范式差异。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Provider/@Consumer V2 跨层同步 |
| 特性编号 | Func-07-02-04-Feat-03 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | API 12 起；跨 BuilderNode 配对（`enableProvideConsumeCrossing`）API 23 起 |
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
| ProviderConsumerUtilV2 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts` | — |
| WeakRefPool | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/weakref_pool.ts` | — |
| @Provider/@Consumer 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-provider-and-consumer.md` | — |
| @Provider API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-provider.md` | — |
| @Consumer API 参考 | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-consumer.md` | — |

---

## 用户故事

### US-1: @Provider 祖先提供

**作为** 应用开发者,
**我想要** 用 `@Provider` 在 @ComponentV2 祖先组件声明状态变量并向后代暴露,
**以便** 后代 @Consumer 无需逐层传递即可获取该状态（V2 的 @Provide）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 @ComponentV2 中声明 `@Provider('alias') var: T = init` THEN `Provider`（`v2_decorators.ts:175-185`）委托 `trackInternal` 安装 getter/setter，并经 `ProviderConsumerUtilV2` 注册到祖先 | 正常 |
| AC-1.2 | WHEN @Provider 别名参数省略 THEN 默认 aliasName 为属性名 | 正常 |
| AC-1.3 | WHEN @Provider 必须本地初始化 THEN 禁止外部传入初始化（`Child({ provider: this.x })` 编译报错） | 异常 |
| AC-1.4 | WHEN @Provider 变量变化 THEN 通知所有配对的 @Consumer 双向同步 | 正常 |
| AC-1.5 | WHEN @Provider 装饰 class 属性 或 在 @Component 中使用 THEN 编译报错 | 异常 |

### US-2: @Consumer 后代消费与弱引用配对

**作为** 应用开发者,
**我想要** 用 `@Consumer` 在后代 @ComponentV2 声明变量，向上查找最近的同 alias @Provider 并建立双向同步,
**以便** 跨层级共享状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 在 @ComponentV2 中声明 `@Consumer('alias') var: T = init` THEN `Consumer`（`v2_decorators.ts:204-236`）+ `ProviderConsumerUtilV2.findProvider`(125) 向上查找最近的同 alias @Provider | 正常 |
| AC-2.2 | WHEN 匹配到 @Provider THEN `connectConsumer2Provider`(239) 重定义 @Consumer 的 getter/setter 读写 Provider view，建立双向同步 | 正常 |
| AC-2.3 | WHEN alias 是唯一匹配 key THEN 不像 V1 同时匹配 alias 和属性名，仅 alias 一致才绑定 | 正常 |
| AC-2.4 | WHEN @Consumer 必须本地初始化 THEN 编译期强制本地初始化 | 异常 |
| AC-2.5 | WHEN @Consumer 找不到对应 @Provider THEN 使用本地初始值 `defineConsumerWithoutProvider`(280)，不抛错 | 正常 |
| AC-2.6 | WHEN @Consumer 支持 function 类型 THEN V1 @Consume 不支持，V2 支持 | 边界 |

### US-3: 别名机制与重载

**作为** 应用开发者,
**我想要** @Provider 可在组件树重名，@Consumer 向上查找最近的,
**以便** 灵活组织跨层级状态（V2 默认开启重载，V1 默认关闭需 allowOverride）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 同一组件树存在多个同 alias @Provider THEN V2 默认开启重载，@Consumer 向上查找最近的 @Provider | 正常 |
| AC-3.2 | WHEN @Provider/@Consumer 别名省略 THEN 默认 aliasName 为属性名 | 正常 |
| AC-3.3 | WHEN @Provider/@Consumer 参数 alias 非 string 类型 THEN 编译报错 | 异常 |

### US-4: Provider GC 与默认值兜底

**作为** 应用开发者,
**我想要** @Provider 被销毁后 @Consumer 优雅降级,
**以便** 避免悬挂引用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN @Provider 所在组件被 GC THEN `WeakRefPool` 回调清理；@Consumer 访问时 `weakView.deref()` 为 undefined 抛 `MISSING_PROVIDE_DEFAULT_VALUE_FOR_CONSUME_CONSUMER` | 异常 |
| AC-4.2 | WHEN @Consumer 设置了本地初始值且 @Provider 被销毁 THEN 使用本地默认值兜底（defineConsumerWithoutProvider） | 正常 |
| AC-4.3 | WHEN @Consumer 未设置本地初始值且 @Provider 被销毁 THEN 抛错（建议 @Consumer 始终设置本地初始值） | 异常 |

### US-5: 跨 BuilderNode 配对（API 23+）

**作为** 应用开发者,
**我想要** API 23+ @Provider/@Consumer 支持跨 BuilderNode 配对,
**以便** 在更灵活的组件树结构中使用跨层级同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN API 23+ 配置 `enableProvideConsumeCrossing: true` THEN @Provider/@Consumer 支持跨 BuilderNode 双向同步 | 正常 |
| AC-5.2 | WHEN BuilderNode 内 @Consumer 跨 BuilderNode 配对 THEN 需设置本地默认值；上树后向上查找 @Provider 建立双向同步 | 正常 |
| AC-5.3 | WHEN 跨 BuilderNode 配对类型不一致 THEN 运行时错误（包括类实例构造函数不同的判断） | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Provider 注册 |
| AC-1.2 | US-1 | R-2 | 单元测试 默认 alias |
| AC-1.3 | US-1 | R-3 | 编译期校验 |
| AC-1.4 | US-1 | R-1 | 单元测试 @Provider 变化通知 |
| AC-1.5 | US-1 | R-4 | 编译期校验 |
| AC-2.1 | US-2 | R-5 | 单元测试 @Consumer 查找 |
| AC-2.2 | US-2 | R-5 | 单元测试 connectConsumer2Provider |
| AC-2.3 | US-2 | R-2 | 单元测试 alias 唯一匹配 |
| AC-2.4 | US-2 | R-3 | 编译期校验 |
| AC-2.5 | US-2 | R-6 | 单元测试 默认值兜底 |
| AC-2.6 | US-2 | R-7 | 单元测试 function 支持 |
| AC-3.1 | US-3 | R-8 | 单元测试 重载 |
| AC-3.2 | US-3 | R-2 | 单元测试 默认 alias |
| AC-3.3 | US-3 | R-9 | 编译期校验 |
| AC-4.1 | US-4 | R-10 | 单元测试 Provider GC 抛错 |
| AC-4.2 | US-4 | R-6 | 单元测试 默认值兜底 |
| AC-4.3 | US-4 | R-10 | 单元测试 未设默认值抛错 |
| AC-5.1 | US-5 | R-11 | 单元测试 跨 BuilderNode |
| AC-5.2 | US-5 | R-11 | 单元测试 上树查找 |
| AC-5.3 | US-5 | R-12 | 单元测试 类型不一致错误 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 在 @ComponentV2 中声明 `@Provider('alias') var: T = init` | `Provider`（`v2_decorators.ts:175-185`）委托 `trackInternal` 安装 getter/setter，并经 `ProviderConsumerUtilV2` 注册到祖先；@Provider 变量变化通知所有配对的 @Consumer 双向同步 | V2 的 @Provide | AC-1.1, AC-1.4 |
| R-2 | 行为 | @Provider/@Consumer 别名 | 别名参数省略时默认 aliasName 为属性名；alias 是唯一匹配 key（不像 V1 同时匹配 alias 和属性名） | — | AC-1.2, AC-2.3, AC-3.2 |
| R-3 | 异常 | @Provider/@Consumer 初始化约束 | @Provider 必须本地初始化，禁止外部传入（编译报错）；@Consumer 必须本地初始化（编译期强制） | 与 V1 @Provide（允许父组件初始化）差异 | AC-1.3, AC-2.4 |
| R-4 | 异常 | @Provider 装饰 class 属性 或 在 @Component 中使用 | 编译报错；@Provider 仅 @ComponentV2 成员变量 | — | AC-1.5 |
| R-5 | 行为 | 在 @ComponentV2 中声明 `@Consumer('alias') var: T = init` | `Consumer`（`v2_decorators.ts:204-236`）+ `ProviderConsumerUtilV2.findProvider`(125) 向上查找最近的同 alias @Provider；`connectConsumer2Provider`(239) 重定义 @Consumer 的 getter/setter 读写 Provider view，建立双向同步 | 弱引用配对 | AC-2.1, AC-2.2 |
| R-6 | 行为 | @Consumer 找不到对应 @Provider 或 @Provider 被销毁 | 使用本地初始值 `defineConsumerWithoutProvider`(280) 兜底，不抛错（前提是设置了本地初始值） | 建议始终设本地初始值 | AC-2.5, AC-4.2 |
| R-7 | 行为 | @Consumer 支持 function 类型 | V1 @Consume 不支持 function；V2 @Consumer 支持 | — | AC-2.6 |
| R-8 | 行为 | 同一组件树存在多个同 alias @Provider | V2 默认开启重载，@Consumer 向上查找最近的 @Provider；V1 默认关闭需 `allowOverride` | V2 重载默认开启 | AC-3.1 |
| R-9 | 异常 | @Provider/@Consumer 参数 alias 非 string 类型 | 编译报错；alias 必须 string | — | AC-3.3 |
| R-10 | 异常 | @Provider 所在组件被 GC | `WeakRefPool` 回调清理；@Consumer 访问时 `weakView.deref()` 为 undefined 抛 `MISSING_PROVIDE_DEFAULT_VALUE_FOR_CONSUME_CONSUMER`；未设置本地初始值时抛错，设置了则用本地默认值兜底 | 弱引用避免 Provider 长期持有 Consumer | AC-4.1, AC-4.3 |
| R-11 | 行为 | API 23+ 跨 BuilderNode 配对 | 配置 `enableProvideConsumeCrossing: true`；BuilderNode 内 @Consumer 需设默认值；上树后向上查找 @Provider 建立双向同步 | API 23+ | AC-5.1, AC-5.2 |
| R-12 | 异常 | 跨 BuilderNode 配对类型不一致 | 运行时错误（包括类实例构造函数不同的判断）；类型必须严格一致 | — | AC-5.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` @Provider 注册 |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` 默认 alias |
| VM-3 | AC-1.3 | 编译期校验 | ArkTS 编译器 外部传入拒绝 |
| VM-4 | AC-1.4 | 单元测试 | `v2_tests/` @Provider 变化通知 |
| VM-5 | AC-1.5 | 编译期校验 | ArkTS 编译器 class 属性/@Component 拒绝 |
| VM-6 | AC-2.1 | 单元测试 | `v2_tests/` @Consumer 查找 |
| VM-7 | AC-2.2 | 代码审查 | `v2_decorated_variables.ts:239` connectConsumer2Provider |
| VM-8 | AC-2.3 | 单元测试 | `v2_tests/` alias 唯一匹配 |
| VM-9 | AC-2.4 | 编译期校验 | ArkTS 编译器 @Consumer 必须本地初始化 |
| VM-10 | AC-2.5 | 单元测试 | `v2_tests/` 默认值兜底 |
| VM-11 | AC-2.6 | 单元测试 | `v2_tests/` function 支持 |
| VM-12 | AC-3.1 | 单元测试 | `v2_tests/` 重载 |
| VM-13 | AC-3.2 | 单元测试 | `v2_tests/` 默认 alias |
| VM-14 | AC-3.3 | 编译期校验 | ArkTS 编译器 alias 类型校验 |
| VM-15 | AC-4.1 | 单元测试 | `v2_tests/` Provider GC 抛错 |
| VM-16 | AC-4.2 | 单元测试 | `v2_tests/` 默认值兜底 |
| VM-17 | AC-4.3 | 单元测试 | `v2_tests/` 未设默认值抛错 |
| VM-18 | AC-5.1 | 单元测试 | `v2_tests/` 跨 BuilderNode |
| VM-19 | AC-5.2 | 单元测试 | `v2_tests/` 上树查找 |
| VM-20 | AC-5.3 | 单元测试 | `v2_tests/` 类型不一致错误 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `Provider` | `v2_decorators.ts:175-185` | @Provider 装饰器，委托 trackInternal + ProviderConsumerUtilV2 |
| `Consumer` | `v2_decorators.ts:204-236` | @Consumer 装饰器 |
| `ProviderConsumerUtilV2` | `v2_decorated_variables.ts:88-305` | @Provider/@Consumer 配对核心 |
| `findProvider` | `v2_decorated_variables.ts:125` | 向上查找最近的同 alias @Provider |
| `findProviderInBuildNode` | `v2_decorated_variables.ts:170` | 跨 BuilderNode 查找 |
| `connectConsumer2Provider` | `v2_decorated_variables.ts:239` | 弱引用配对，重定义 getter/setter |
| `defineConsumerWithoutProvider` | `v2_decorated_variables.ts:280` | 找不到 @Provider 时本地默认值兜底 |
| `WeakRefPool` | `weakref_pool.ts:32-141` | 规范化 WeakRef + FinalizationRegistry GC |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | @Provider/@Consumer 引入，弱引用配对范式 | V2 跨层级同步 | V1 @Provide/@Consume→@Provider/@Consumer；alias 仅匹配 alias（不再匹配属性名）；@Consumer 必须本地初始化 |
| API 12 | @Provider 重载默认开启（V1 默认关闭需 allowOverride） | 重名 @Provider 行为变化 | 移除 allowOverride，默认即重载 |
| API 12 | @Consumer 支持 function 类型（V1 不支持） | function 可跨层传递 | 无需迁移 |
| API 23 | 跨 BuilderNode 配对（`enableProvideConsumeCrossing`） | 跨树配对 | 配置 `enableProvideConsumeCrossing` |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| alias 唯一匹配 | V2 @Provider/@Consumer 仅匹配 alias（不像 V1 同时匹配 alias 和属性名） |
| 必须本地初始化 | @Provider 与 @Consumer 都必须本地初始化；@Provider 禁止外部传入；@Consumer 找不到 @Provider 时用本地默认值兜底 |
| 重载默认开启 | V2 @Provider 重名默认开启重载（V1 默认关闭需 allowOverride） |
| 弱引用配对 | `connectConsumer2Provider` 重定义 getter/setter；Provider GC 后 @Consumer 访问抛错（除非有本地默认值） |
| function 支持 | V2 @Provider/@Consumer 支持 function 类型（V1 不支持） |
| @ComponentV2 限定 | @Provider/@Consumer 仅在 @ComponentV2 成员变量中可用 |
| V1/V2 范式隔离 | V1 递归祖先链查找（findProvidePU__）；V2 弱引用直接配对 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 弱引用配对避免 Provider 长期持有 Consumer；`WeakRefPool` 自动 GC 避免内存泄漏 |
| 可调试性 | 断点建议：`ProviderConsumerUtilV2.findProvider`、`connectConsumer2Provider`；@Provider GC 排查：`WeakRefPool.asyncRegisterToFinalizationRegistry` |
| 可观测性 | `UIUtils.canBeObserved`(API 23+) 返回 @Provider/@Consumer 装饰器信息 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| V2 跨层级同步 | @Provider/@Consumer 是 V2 跨层级状态共享的核心机制；弱引用 + 重载默认开启 |
| @ReusableV2 重置 | 复用时 @Provider 用初始值，@Consumer 有对应 @Provider 用其值否则用初始值（Feat-06） |
| 跨域协同 | WeakRefPool GC 与 07-02-14 协同 |
| V1 对比 | V1 @Provide/@Consume 递归祖先链查找 + 允许父组件初始化 + 不支持 function；V2 弱引用配对 + 必须本地初始化 + 支持 function + 重载默认开启 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:175-185` | `Provider` @Provider 装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:204-236` | `Consumer` @Consumer 装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:88-305` | `ProviderConsumerUtilV2` 配对核心 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:125` | `findProvider` 向上查找 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:170` | `findProviderInBuildNode` 跨 BuilderNode 查找 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:239` | `connectConsumer2Provider` 弱引用配对 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorated_variables.ts:280` | `defineConsumerWithoutProvider` 默认值兜底 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/weakref_pool.ts:32-141` | `WeakRefPool` + FinalizationRegistry GC |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | @Provider/@Consumer 配对、弱引用、GC、跨 BuilderNode 回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-provider-and-consumer.md` | @Provider/@Consumer 开发指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-provider.md` | @Provider API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-consumer.md` | @Consumer API 参考 |
