# 特性规格

> Func-07-02-05-Feat-02 @Computed/@Monitor/@SyncMonitor 计算与监听：固化 `@Computed`（`ComputedV2` 惰性求值 + 缓存，`MIN_COMPUTED_ID` 段，只读）、`@Monitor`（`MonitorV2` 路径遍历监听，IMonitor before/now/path，异步）、`@SyncMonitor`（同步变体，API 23+）、通配符 `.*`（API 26+）、`UIUtils.addMonitor`/`clearMonitor`（API 20+）行为规格与错误码。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | @Computed/@Monitor/@SyncMonitor 计算与监听 |
| 特性编号 | Func-07-02-05-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | @Computed/@Monitor API 12 起；UIUtils.addMonitor/clearMonitor API 20 起；@SyncMonitor API 23 起；applySync/flushUpdates/flushUIUpdates API 22 起；@Monitor 通配符 API 26 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Draft |
| ComputedV2 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_computed.ts` | — |
| MonitorV2 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_monitor.ts` | — |
| V2 装饰器定义 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts` | — |
| UIUtils | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts` | — |
| ObserveV2（调度） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts` | — |
| @Computed 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-computed.md` | — |
| @Monitor 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-monitor.md` | — |
| @SyncMonitor 开发指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-syncmonitor.md` | — |
| addMonitor/clearMonitor 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-addMonitor-clearMonitor.md` | — |
| applySync/flushUpdates 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-applySync-flushUpdates-flushUIUpdates.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: @Computed 只读计算属性

**作为** 应用开发者,
**我想要** 用 `@Computed` 装饰 getter 方法，实现惰性求值 + 缓存的计算属性,
**以便** 派生状态自动随依赖变化重新计算，避免冗余计算。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `@Computed` 装饰 getter 方法 THEN `Computed`（`v2_decorators.ts:366-374`）+ `ComputedV2`（`v2_computed.ts:31-161`，`MIN_COMPUTED_ID=0x1000000000`）在初始化时重定义属性 | 正常 |
| AC-1.2 | WHEN @Computed 初始化 THEN `InitRun`(59) 调 `observeObjectAccess`(105) 在 `startRecordDependencies` 下跑 getter 收集依赖，结果缓存到 `___comp_cached_<prop>` | 正常 |
| AC-1.3 | WHEN @Computed 依赖的状态变量变化 THEN `fireChange`(79) 仅结果 `===` 变化才通知（重新求值后缓存） | 正常 |
| AC-1.4 | WHEN @Computed 自定义 setter THEN 编译报错（只读，`InitRun` setter 抛错） | 异常 |
| AC-1.5 | WHEN 在 @Computed getter 内修改参与计算的属性 THEN 导致循环计算 → appfreeze；`startDirty_` 防递归但不防状态不一致 | 边界 |
| AC-1.6 | WHEN @Computed 用于 @ComponentV2 THEN 自定义组件创建时初始化并触发计算；用于 @ObservedV2 类 THEN 实例创建后**异步初始化**触发计算 | 正常 |
| AC-1.7 | WHEN @Computed 与双向绑定 `!!` 联用 THEN 编译报错 | 异常 |

### US-2: @Monitor 异步路径监听

**作为** 应用开发者,
**我想要** 用 `@Monitor` 监听 @Local/@Param/@Provider/@Consumer/@Computed/@Trace 变量的变化，获取 before/now/path,
**以便** 实现比 V1 @Watch 更精细的状态变化监听（路径感知 + 前后值）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `@Monitor` 装饰方法 THEN `Monitor`（`v2_decorators.ts:259-310`）+ `MonitorV2`（`v2_monitor.ts:189-574`）建立路径遍历监听 | 正常 |
| AC-2.2 | WHEN @Monitor 参数为点分路径 THEN `analysisProp`(520) 逐层 `addRef`，每层注册 MonitorV2 ID；路径不存在返回 `MONITOR_PATH_NOT_FOUND` | 正常 |
| AC-2.3 | WHEN @Monitor 回调触发 THEN 参数为 `IMonitor`（`v2_decorators.ts:337-348`）：`dirty: Array<string>`（变化路径数组）+ `value<T>(path?): IMonitorValue`（before/now/path） | 正常 |
| AC-2.4 | WHEN @Monitor 异步执行 THEN 事件处理程序结束后才执行；一次事件中多次变化**只触发一次**，使用初始值 vs 最终值做严格相等（`===`）判断 | 正常 |
| AC-2.5 | WHEN 单个 @Monitor 同时监听多个属性 THEN 共同变化只触发一次 | 边界 |
| AC-2.6 | WHEN @Monitor 监听整个数组 THEN 更改某项不被监听；无法监听 Array/Map/Date/Set 的 API 调用（除非 API 26+ 使用通配符） | 边界 |
| AC-2.7 | WHEN @Monitor 在非 @ObservedV2 类中使用 THEN 编译报错（仅在 @ComponentV2 与 @ObservedV2 中生效） | 异常 |

### US-3: @SyncMonitor 同步监听

**作为** 应用开发者,
**我想要** 用 `@SyncMonitor`（API 23+）实现同步立即执行的监听,
**以便** 在数据校验等需同步感知变化的场景使用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `@SyncMonitor`（API 23+）装饰方法 THEN `SyncMonitor`（`v2_decorators.ts:312-334`，`MIN_SYNC_MONITOR_OR_SYNC_API_ID` 段）在 fireChange 调用栈内**同步立即执行** | 正常 |
| AC-3.2 | WHEN 同一事件中每次属性变化 THEN @SyncMonitor 每次都触发回调（与 @Monitor 行为不同） | 正常 |
| AC-3.3 | WHEN @SyncMonitor 路径中使用通配符 `*`（一层模糊监听）THEN 触发；通配符路径的 before/now 返回 undefined | 正常 |
| AC-3.4 | WHEN 路径从可访问变为不可访问或反向 THEN @SyncMonitor 触发 | 正常 |
| AC-3.5 | WHEN 调用 Array API（如 splice、shift）一次性多元素变化 THEN @SyncMonitor 只触发一次回调；多次单独赋值会多次触发 | 边界 |
| AC-3.6 | WHEN @SyncMonitor 参数为 const 常量/enum/变量（非字符串字面量）THEN 编译报错 | 异常 |
| AC-3.7 | WHEN @SyncMonitor 内修改被监听属性 THEN 无限循环，不建议 | 边界 |
| AC-3.8 | WHEN @SyncMonitor 路径非法 THEN 返回错误码 130001 | 异常 |

### US-4: @Monitor 通配符（API 26+）

**作为** 应用开发者,
**我想要** 用 API 26+ 的通配符 `.*` 监听对象/数组的任意属性/元素变化,
**以便** 监听 Array/Map/Date/Set 的 API 调用等深层变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN API 26+ @Monitor 首参为 `MonitorDecoratorOptions`（含 `enableWildcard: boolean`，默认 true）THEN 支持通配符 | 正常 |
| AC-4.2 | WHEN 通配符路径 `obj.*` THEN 监听 obj 整体赋值或任意 @Trace 属性变化；通配符只能出现在路径末尾 | 正常 |
| AC-4.3 | WHEN 通配符路径 `arr.*` THEN 监听数组整体、任意元素、长度、API 调用 | 正常 |
| AC-4.4 | WHEN 通配符路径触发 THEN before/now 为 undefined | 边界 |
| AC-4.5 | WHEN 路径从可访问变为不可访问 THEN 默认（未用配置项）不触发；使用配置项（API 26+）触发 | 边界 |

### US-5: UIUtils.addMonitor/clearMonitor 动态监听

**作为** 应用开发者,
**我想要** 用 `UIUtils.addMonitor`/`clearMonitor`（API 20+）动态添加/取消监听,
**以便** 在运行时按需监听 @ComponentV2 与 @ObservedV2 实例的属性变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `UIUtils.addMonitor(target, path, monitorCallback, options?)`(64) THEN 动态添加监听；仅支持 @ComponentV2 与 @ObservedV2 实例 | 正常 |
| AC-5.2 | WHEN `MonitorOptions.isSynchronous=true` THEN 行为同 @SyncMonitor（同步立即执行） | 正常 |
| AC-5.3 | WHEN `MonitorOptions.enableWildcard=true`（API 26+）THEN 支持通配符 | 正常 |
| AC-5.4 | WHEN 调用 `UIUtils.clearMonitor(target, path, monitorCallback?)`(84) THEN 删除通过 addMonitor 添加的监听；不传 monitorCallback 时删除该 path 所有监听 | 正常 |
| AC-5.5 | WHEN addMonitor target 不是 @ComponentV2/@ObservedV2 实例 THEN 返回错误码 130000 | 异常 |
| AC-5.6 | WHEN addMonitor path 非法 THEN 返回错误码 130001 | 异常 |
| AC-5.7 | WHEN addMonitor monitorCallback 不是函数或是匿名函数 THEN 返回错误码 130002 | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 @Computed 重定义属性 |
| AC-1.2 | US-1 | R-1 | 单元测试 InitRun 依赖收集 |
| AC-1.3 | US-1 | R-2 | 单元测试 === 未变不通知 |
| AC-1.4 | US-1 | R-3 | 编译期校验 |
| AC-1.5 | US-1 | R-4 | 单元测试 循环计算 |
| AC-1.6 | US-1 | R-1 | 单元测试 同步/异步初始化 |
| AC-1.7 | US-1 | R-5 | 编译期校验 |
| AC-2.1 | US-2 | R-6 | 单元测试 @Monitor 路径监听 |
| AC-2.2 | US-2 | R-6 | 单元测试 analysisProp 逐层 |
| AC-2.3 | US-2 | R-7 | 单元测试 IMonitor 参数 |
| AC-2.4 | US-2 | R-8 | 单元测试 异步执行 |
| AC-2.5 | US-2 | R-8 | 单元测试 多属性合并 |
| AC-2.6 | US-2 | R-9 | 单元测试 数组项不监听 |
| AC-2.7 | US-2 | R-10 | 编译期校验 |
| AC-3.1 | US-3 | R-11 | 单元测试 @SyncMonitor 同步 |
| AC-3.2 | US-3 | R-11 | 单元测试 每次触发 |
| AC-3.3 | US-3 | R-12 | 单元测试 通配符 |
| AC-3.4 | US-3 | R-11 | 单元测试 路径可访问性 |
| AC-3.5 | US-3 | R-11 | 单元测试 Array API 合并 |
| AC-3.6 | US-3 | R-13 | 编译期校验 |
| AC-3.7 | US-3 | R-14 | 单元测试 无限循环 |
| AC-3.8 | US-3 | R-15 | 单元测试 错误码 130001 |
| AC-4.1 | US-4 | R-16 | 单元测试 enableWildcard |
| AC-4.2 | US-4 | R-16 | 单元测试 obj.* |
| AC-4.3 | US-4 | R-16 | 单元测试 arr.* |
| AC-4.4 | US-4 | R-16 | 单元测试 before/now undefined |
| AC-4.5 | US-4 | R-17 | 单元测试 路径可访问性 |
| AC-5.1 | US-5 | R-18 | 单元测试 addMonitor |
| AC-5.2 | US-5 | R-18 | 单元测试 isSynchronous |
| AC-5.3 | US-5 | R-18 | 单元测试 enableWildcard |
| AC-5.4 | US-5 | R-18 | 单元测试 clearMonitor |
| AC-5.5 | US-5 | R-19 | 单元测试 错误码 130000 |
| AC-5.6 | US-5 | R-19 | 单元测试 错误码 130001 |
| AC-5.7 | US-5 | R-19 | 单元测试 错误码 130002 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `@Computed` 装饰 getter 方法 | `Computed`（`v2_decorators.ts:366-374`）+ `ComputedV2`（`v2_computed.ts:31-161`，`MIN_COMPUTED_ID=0x1000000000`）`InitRun`(59) 重定义属性，`observeObjectAccess`(105) 在 `startRecordDependencies` 下跑 getter 收集依赖，结果缓存到 `___comp_cached_<prop>`；@ComponentV2 中创建时初始化，@ObservedV2 类中实例创建后异步初始化 | 仅能装饰 getter 访问器 | AC-1.1, AC-1.2, AC-1.6 |
| R-2 | 行为 | @Computed 依赖的状态变量变化 | `fireChange`(79) 仅结果 `===` 变化才通知（重新求值后缓存）；被动计算，只在依赖变化时重新计算一次 | 惰性求值 + 缓存 | AC-1.3 |
| R-3 | 异常 | @Computed 自定义 setter | 编译报错（只读，`InitRun` setter 抛错） | 计算属性只读 | AC-1.4 |
| R-4 | 边界 | 在 @Computed getter 内修改参与计算的属性 | 导致循环计算 → appfreeze；`startDirty_` 防递归但不防状态不一致；不应在 getter 中做额外赋值 | @Computed 应为纯函数 | AC-1.5 |
| R-5 | 异常 | @Computed 与双向绑定 `!!` 联用 | 编译报错 | — | AC-1.7 |
| R-6 | 行为 | `@Monitor` 装饰方法 | `Monitor`（`v2_decorators.ts:259-310`）+ `MonitorV2`（`v2_monitor.ts:189-574`）`analysisProp`(520) 点分路径逐层 `addRef`，每层注册 MonitorV2 ID；路径不存在返回 `MONITOR_PATH_NOT_FOUND` | 仅 @ComponentV2/@ObservedV2 中生效 | AC-2.1, AC-2.2 |
| R-7 | 行为 | @Monitor 回调触发 | 参数 `IMonitor`（`v2_decorators.ts:337-348`）：`dirty: Array<string>`（变化路径数组）+ `value<T>(path?): IMonitorValue`（before/now/path） | IMonitor 提供前后值 | AC-2.3 |
| R-8 | 行为 | @Monitor 异步执行 | 事件处理程序结束后才执行；一次事件中多次变化只触发一次，使用初始值 vs 最终值做严格相等（`===`）判断；单个 @Monitor 同时监听多个属性时共同变化只触发一次 | 与 @SyncMonitor 差异 | AC-2.4, AC-2.5 |
| R-9 | 边界 | @Monitor 监听整个数组/Map/Set/Date | 更改某项不被监听；无法监听 API 调用（除非 API 26+ 使用通配符）；深度监听嵌套类、多维数组、对象数组需深层属性 @Trace | 数组项/API 调用监听受限 | AC-2.6 |
| R-10 | 异常 | @Monitor 在非 @ObservedV2 类中使用 | 编译报错（仅在 @ComponentV2 与 @ObservedV2 中生效） | — | AC-2.7 |
| R-11 | 行为 | `@SyncMonitor`（API 23+）装饰方法 | `SyncMonitor`（`v2_decorators.ts:312-334`，`MIN_SYNC_MONITOR_OR_SYNC_API_ID` 段）在 fireChange 调用栈内同步立即执行；同一事件中每次属性变化都触发回调；调用 Array API 一次性多元素变化只触发一次，多次单独赋值会多次触发；路径从可访问变为不可访问或反向都触发 | 与 @Monitor 异步行为不同 | AC-3.1~AC-3.5 |
| R-12 | 行为 | @SyncMonitor 路径中使用通配符 `*` | 一层模糊监听；通配符路径的 before/now 返回 undefined | — | AC-3.3 |
| R-13 | 异常 | @SyncMonitor 参数为 const 常量/enum/变量（非字符串字面量） | 编译报错；参数仅支持字符串字面量 | — | AC-3.6 |
| R-14 | 边界 | @SyncMonitor 内修改被监听属性 | 无限循环，不建议 | — | AC-3.7 |
| R-15 | 异常 | @SyncMonitor 路径非法 | 返回错误码 130001（`The path is invalid.`） | API 23+ | AC-3.8 |
| R-16 | 行为 | API 26+ @Monitor 通配符 | 首参可为 `MonitorDecoratorOptions`（`enableWildcard: boolean`，默认 true）；`obj.*` 监听整体赋值或任意 @Trace 属性变化；`arr.*` 监听数组整体、任意元素、长度、API 调用；通配符只能出现在路径末尾；通配符路径的 before/now 为 undefined | API 26+ | AC-4.1~AC-4.4 |
| R-17 | 边界 | @Monitor 路径从可访问变为不可访问 | 默认（未用配置项）不触发；使用配置项（API 26+）触发 | API 26+ 配置项 | AC-4.5 |
| R-18 | 行为 | `UIUtils.addMonitor`/`clearMonitor`（API 20+） | `addMonitor`(64) 动态添加监听，仅支持 @ComponentV2 与 @ObservedV2 实例；`MonitorOptions.isSynchronous=true` 行为同 @SyncMonitor；`enableWildcard=true`（API 26+）支持通配符；`clearMonitor`(84) 删除监听，不传 monitorCallback 时删除该 path 所有监听 | API 20+ | AC-5.1~AC-5.4 |
| R-19 | 异常 | addMonitor/clearMonitor 非法参数 | target 不是 @ComponentV2/@ObservedV2 实例 → 错误码 130000；path 非法 → 130001；monitorCallback 不是函数或匿名函数 → 130002 | API 20+ | AC-5.5~AC-5.7 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` @Computed 重定义属性 |
| VM-2 | AC-1.2 | 代码审查 | `v2_computed.ts:59` InitRun |
| VM-3 | AC-1.3 | 单元测试 | `v2_tests/` === 未变不通知 |
| VM-4 | AC-1.4 | 编译期校验 | ArkTS 编译器 setter 拒绝 |
| VM-5 | AC-1.5 | 单元测试 | `v2_tests/` 循环计算 |
| VM-6 | AC-1.6 | 单元测试 | `v2_tests/` 同步/异步初始化 |
| VM-7 | AC-1.7 | 编译期校验 | ArkTS 编译器 !! 联用拒绝 |
| VM-8 | AC-2.1 | 单元测试 | `v2_tests/` @Monitor 路径监听 |
| VM-9 | AC-2.2 | 代码审查 | `v2_monitor.ts:520` analysisProp |
| VM-10 | AC-2.3 | 单元测试 | `v2_tests/` IMonitor 参数 |
| VM-11 | AC-2.4 | 单元测试 | `v2_tests/` 异步执行 |
| VM-12 | AC-2.5 | 单元测试 | `v2_tests/` 多属性合并 |
| VM-13 | AC-2.6 | 单元测试 | `v2_tests/` 数组项不监听 |
| VM-14 | AC-2.7 | 编译期校验 | ArkTS 编译器 非 @ObservedV2 拒绝 |
| VM-15 | AC-3.1 | 单元测试 | `v2_tests/` @SyncMonitor 同步 |
| VM-16 | AC-3.2 | 单元测试 | `v2_tests/` 每次触发 |
| VM-17 | AC-3.3 | 单元测试 | `v2_tests/` 通配符 |
| VM-18 | AC-3.4 | 单元测试 | `v2_tests/` 路径可访问性 |
| VM-19 | AC-3.5 | 单元测试 | `v2_tests/` Array API 合并 |
| VM-20 | AC-3.6 | 编译期校验 | ArkTS 编译器 非字面量拒绝 |
| VM-21 | AC-3.7 | 单元测试 | `v2_tests/` 无限循环 |
| VM-22 | AC-3.8 | 单元测试 | `v2_tests/` 错误码 130001 |
| VM-23 | AC-4.1 | 单元测试 | `v2_tests/` enableWildcard |
| VM-24 | AC-4.2 | 单元测试 | `v2_tests/` obj.* |
| VM-25 | AC-4.3 | 单元测试 | `v2_tests/` arr.* |
| VM-26 | AC-4.4 | 单元测试 | `v2_tests/` before/now undefined |
| VM-27 | AC-4.5 | 单元测试 | `v2_tests/` 路径可访问性 |
| VM-28 | AC-5.1 | 单元测试 | `v2_tests/` addMonitor |
| VM-29 | AC-5.2 | 单元测试 | `v2_tests/` isSynchronous |
| VM-30 | AC-5.3 | 单元测试 | `v2_tests/` enableWildcard |
| VM-31 | AC-5.4 | 单元测试 | `v2_tests/` clearMonitor |
| VM-32 | AC-5.5 | 单元测试 | `v2_tests/` 错误码 130000 |
| VM-33 | AC-5.6 | 单元测试 | `v2_tests/` 错误码 130001 |
| VM-34 | AC-5.7 | 单元测试 | `v2_tests/` 错误码 130002 |

---

## 错误码规格

| 错误码 | 触发条件 | 错误信息 | 起始版本 |
|--------|----------|----------|----------|
| 130000 | addMonitor/clearMonitor target 不是 @ObservedV2 class 或 @ComponentV2 实例 | 非法目标对象 | API 20 |
| 130001 | addMonitor/clearMonitor path 非法；@SyncMonitor 路径非法 | `The path is invalid.` | API 20（@SyncMonitor 自 API 23） |
| 130002 | addMonitor/clearMonitor monitorCallback 不是函数或匿名函数 | 非法回调方法 | API 20 |
| 140001 | 在 @Computed getter 内调用 applySync/flushUpdates/flushUIUpdates | 非法调用同步刷新 | API 22 |
| 140002 | 在 @Monitor 回调内调用 flushUpdates/flushUIUpdates | 非法调用同步刷新 | API 22 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `Computed` | `v2_decorators.ts:366-374` | @Computed 方法装饰器 |
| `ComputedV2` | `v2_computed.ts:31-161` | @Computed 实现：`InitRun`(59)/`observeObjectAccess`(105)/`fireChange`(79)，`MIN_COMPUTED_ID=0x1000000000` |
| `AsyncAddComputedV2` | `v2_computed.ts:167-189` | @Computed 微任务注册（@ObservedV2 类中异步初始化） |
| `Monitor`/`SyncMonitor` | `v2_decorators.ts:259-310/312-334` | @Monitor/@SyncMonitor 方法装饰器 |
| `IMonitor` | `v2_decorators.ts:337-348` | @Monitor 回调参数类型（dirty/value） |
| `MonitorV2`/`MonitorValueV2`/`MonitorPathHelper` | `v2_monitor.ts:189-574/59-188/26-57` | @Monitor/@SyncMonitor 实现：`analysisProp`(520) 路径遍历 |
| `AsyncAddMonitorV2` | `v2_monitor.ts:578-601` | @Monitor 微任务注册 |
| `UIUtilsImpl.addMonitor`/`clearMonitor` | `ui_utils.ts:64-82/84-97` | 动态添加/取消监听（API 20+） |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | @Computed/@Monitor 引入，计算属性 + 路径监听（IMonitor before/now/path） | V2 计算与监听 | V1 @Watch→@Monitor（参数从方法名变为路径，获取前后值） |
| API 20 | UIUtils.addMonitor/clearMonitor 动态监听引入（错误码 130000-130002） | 运行时动态监听 | 处理新增错误码 |
| API 22 | applySync/flushUpdates/flushUIUpdates 引入（错误码 140001/140002） | 同步刷新逃生舱 | 避免在 @Computed/@Monitor 内调用 |
| API 23 | @SyncMonitor 同步监听引入（错误码 130001 适用于 @SyncMonitor） | 同步立即执行监听 | 数据校验场景可用 |
| API 26 | @Monitor 通配符 `.*`（MonitorDecoratorOptions） | 监听 Array/Map/Set/Date API 调用 | 配置 enableWildcard |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| @Computed 只读 | @Computed 仅能装饰 getter，不支持 setter；应为纯函数；不能与 `!!` 联用 |
| @Computed ID 段 | `ComputedV2.MIN_COMPUTED_ID=0x1000000000` 独立 ID 段，fireChange 按段路由 |
| @Monitor 异步合并 | 一次事件中多次变化只触发一次（初始值 vs 最终值 `===` 判断）；与 @SyncMonitor 同步每次触发不同 |
| @SyncMonitor 同步立即 | @SyncMonitor 在 fireChange 调用栈内同步执行；每次属性变化都触发；API 23+ |
| 路径遍历依赖 @Trace | @Monitor/@SyncMonitor 深度监听嵌套类/多维数组需深层属性 @Trace；analysisProp 逐层 addRef |
| 仅 @ComponentV2/@ObservedV2 | @Computed/@Monitor/@SyncMonitor 仅在 @ComponentV2 与 @ObservedV2 中生效 |
| V1 对比 | V1 @Watch 仅变量名级监听无前后值；V2 @Monitor 路径感知 + IMonitor(before/now/path) |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | @Computed 惰性求值 + 缓存避免冗余计算；@Monitor 异步合并减少回调次数；@SyncMonitor 同步立即有开销，慎用 |
| 可调试性 | @Computed 断点：`ComputedV2.InitRun`/`fireChange`；@Monitor 断点：`MonitorV2.analysisProp`/`bindRun`；日志：`updateDirtyComputedProps N`、`updateDirtyMonitors: N` |
| 可观测性 | `UIUtils.canBeObserved`(API 23+) 返回 @Computed/@Monitor 装饰器信息 |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| V2 派生状态 | @Computed 是 V2 派生状态的核心机制；可初始化子组件 @Param |
| V2 变化监听 | @Monitor/@SyncMonitor + UIUtils.addMonitor 提供 V2 完整变化监听体系；@Monitor 可监听 @Computed |
| @ReusableV2 重置 | 复用时 @Computed 用当前最新值重新计算；@Monitor 在所有变量重置后触发（Feat-06） |
| V1 对比 | V1 无计算属性；V1 @Watch 仅变量名无前后值 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:259-310` | `Monitor` @Monitor 方法装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:312-334` | `SyncMonitor` @SyncMonitor 方法装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:337-348` | `IMonitor` 回调参数类型 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_decorators.ts:366-374` | `Computed` @Computed 方法装饰器 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_computed.ts:31-161` | `ComputedV2` @Computed 实现（InitRun/observeObjectAccess/fireChange） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_monitor.ts:26-57` | `MonitorPathHelper` 路径辅助 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_monitor.ts:59-188` | `MonitorValueV2` 监听值 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_monitor.ts:189-574` | `MonitorV2` @Monitor/@SyncMonitor 实现 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_monitor.ts:520` | `analysisProp` 路径遍历 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:64-82` | `UIUtilsImpl.addMonitor` 动态监听 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:84-97` | `UIUtilsImpl.clearMonitor` 取消监听 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:104-114` | `applySync`/`flushUpdates`/`flushUIUpdates` 同步刷新 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:998/1042` | `updateDirtyComputedProps`/`updateDirtyMonitors` 调度 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | @Computed/@Monitor/@SyncMonitor 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-computed.md` | @Computed 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-monitor.md` | @Monitor 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-syncmonitor.md` | @SyncMonitor 开发指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-addMonitor-clearMonitor.md` | addMonitor/clearMonitor 指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-applySync-flushUpdates-flushUIUpdates.md` | applySync/flushUpdates 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | 错误码 130000-130002/140001/140002 |
