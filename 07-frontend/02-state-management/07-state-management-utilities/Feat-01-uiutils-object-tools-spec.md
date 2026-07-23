# 特性规格

> Func-07-02-07-Feat-01 UIUtils 对象工具：固化 `UIUtils.getTarget`（还原代理对象，API 12+）、`makeObserved`（将普通对象变为 V2 可观察，API 12+）、`canBeObserved`（检测可观察性，API 23+）、`enableV2Compatibility`（V1→V2 桥接，API 19+）、`makeV1Observed`（V2→V1 桥接，API 19+）、`makeBinding`（构建 @Builder 参数，API 20+）行为规格与 `ObservedUtil` 检测能力。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIUtils 对象工具 |
| 特性编号 | Func-07-02-07-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | getTarget/makeObserved API 12 起；enableV2Compatibility/makeV1Observed API 19 起；makeBinding API 20 起；canBeObserved API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/07-state-management-utilities/design.md` | Draft |
| UIUtilsImpl | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts` | — |
| ObservedUtil | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/observed_util.ts` | — |
| RefInfo | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_make_observed.ts` | — |
| makeObserved 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-makeObserved.md` | — |
| getTarget 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-getTarget.md` | — |
| canBeObserved 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-canBeObserved.md` | — |

---

## 用户故事

### US-1: getTarget 还原代理对象

**作为** 应用开发者,
**我想要** 从状态管理框架的代理对象中获取原始对象,
**以便** 在序列化、`===` 比较、NAPI 接口等场景使用原始对象。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `UIUtils.getTarget<T>(source: T): T`(23，API 12+) THEN 返回状态管理框架代理前的原始对象 | 正常 |
| AC-1.2 | WHEN V1 装饰的 `@Observed` class 实例/`@State` 装饰的 class/Date/Map/Set/Array 经 getTarget THEN 返回代理前的原始对象 | 正常 |
| AC-1.3 | WHEN V2 `@Trace`/`@Local` 装饰的 Date/Map/Set/Array 经 getTarget THEN 返回代理前的原始对象；V2 不对类对象实例加代理 | 正常 |
| AC-1.4 | WHEN 修改 getTarget 返回的原始对象 THEN 不触发 UI 刷新（脱离了框架观察） | 边界 |
| AC-1.5 | WHEN getTarget 入参为非对象类型 THEN 编译报错 | 异常 |
| AC-1.6 | WHEN V2 `@Trace` 装饰的属性名有 `__ob_` 前缀 THEN getTarget 不剥离该前缀，可能影响 NAPI 接口（`napi_get_property_names`/`napi_delete_property`） | 边界 |

### US-2: makeObserved 创建可观察对象

**作为** 应用开发者,
**我想要** 用 `makeObserved` 将普通不可观察对象变为 V2 可观察对象（深度观察）,
**以便** 处理 `JSON.parse` 返回的 Object、未装饰的 class、`@Sendable` class 等场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `UIUtils.makeObserved<T>(source: T): T`(39，API 12+) THEN 将普通对象变为 V2 可观察对象（深度观察），内部委托 `RefInfo.get`(25) | 正常 |
| AC-2.2 | WHEN makeObserved 入参为未被 `@Observed`/`@ObservedV2` 装饰的 class/Array/Map/Set/Date/`collections.Array/Map/Set`/`JSON.parse` 返回的 Object/`@Sendable` class THEN 包装为可观察 | 正常 |
| AC-2.3 | WHEN makeObserved 入参为 `undefined`/`null` THEN 直接返回自身 | 边界 |
| AC-2.4 | WHEN makeObserved 入参为非 Object 类型 THEN 编译报错 | 异常 |
| AC-2.5 | WHEN makeObserved 入参已是 `@ObservedV2`/`@Observed` 装饰类实例或已被 makeObserved 包装 THEN 直接返回入参（防双重代理） | 边界 |
| AC-2.6 | WHEN makeObserved 与 V1 状态变量装饰器（如 `@State`）一起用 THEN 抛运行时异常 | 异常 |
| AC-2.7 | WHEN makeObserved 观察内置类型 THEN Array：`push/pop/shift/unshift/splice/copyWithin/fill/reverse/sort`；Map：`set/clear/delete`；Set：`add/clear/delete`；Date：`setFullYear/setMonth/...` 14 个 setter | 正常 |
| AC-2.8 | WHEN 对状态变量重新赋值为非 makeObserved 数据 THEN 失去观察能力 | 边界 |

### US-3: canBeObserved 检测可观察性

**作为** 应用开发者,
**我想要** 用 `canBeObserved`（API 23+）判断对象是否为可观察对象并获取关联的组件信息,
**以便** 调试状态变量装饰情况。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `UIUtils.canBeObserved<T>(source: T): ObservedResult`(19，API 23+) THEN 返回 `{ isObserved, reason, decoratorInfo }` | 正常 |
| AC-3.2 | WHEN `canBeObserved` 入参为 `undefined`/`null` THEN `isObserved=false`；非 Object 编译报错 | 边界 |
| AC-3.3 | WHEN 可观察对象经 canBeObserved THEN `reason` 描述装饰方式（V1 @Observed / V2 @ObservedV2+@Trace / makeObserved / enableV2Compatibility / built-in proxy） | 正常 |
| AC-3.4 | WHEN `decoratorInfo` 返回 THEN 含 `decoratorName`（@State/@Prop/@Link/@Trace/MakeObserved 等）、`owningComponentId`（V2 装饰器返回 -1） | 正常 |
| AC-3.5 | WHEN `ObservedUtil.canBeObserved` 检测顺序 THEN V2 → makeObserved → V2Proxy → V1 | 正常 |

### US-4: enableV2Compatibility V1→V2 桥接

**作为** 应用开发者,
**我想要** 用 `enableV2Compatibility`（API 19+）使 V1 状态变量能在 @ComponentV2 中观察,
**以便** V1→V2 复杂类型传递时实现混用观察。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `UIUtils.enableV2Compatibility<T>(source: T): T`(50，API 19+) THEN 数据源是 V1 状态数据时返回能在 @ComponentV2 中观察的数据 | 正常 |
| AC-4.2 | WHEN 数据源非 V1 状态数据 THEN 返回数据源本身 | 边界 |
| AC-4.3 | WHEN enableV2Compatibility 仅作用于 V1 状态变量（@Observed 实例或 @State/@Prop/@Link/@Provide/@Consume/@ObjectLink 装饰变量）THEN 支持；不支持 @ObservedV2/makeObserved 返回值/V2 built-in 类型 | 边界 |
| AC-4.4 | WHEN enableV2Compatibility 处理对象 THEN 递归遍历 class 属性、Array/Set/Map 子项直至遇到非 V1 状态变量 | 正常 |
| AC-4.5 | WHEN enableV2Compatibility 处理非 object 类型/undefined/null THEN 不支持 | 边界 |

### US-5: makeV1Observed V2→V1 桥接

**作为** 应用开发者,
**我想要** 用 `makeV1Observed`（API 19+）将不可观察对象包装成 V1 可观察对象,
**以便** V2→V1 传递复杂类型，返回值可初始化 @ObjectLink。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `UIUtils.makeV1Observed<T>(source: T): T`(45，API 19+) THEN 将不可观察对象包装成 V1 可观察对象，能力等同 @Observed，返回值可初始化 @ObjectLink | 正常 |
| AC-5.2 | WHEN makeV1Observed 入参为普通 class/Array/Map/Set/Date THEN 支持 | 正常 |
| AC-5.3 | WHEN makeV1Observed 入参为 collections 类型/`@Sendable` class/非 object/undefined/null/@ObservedV2/makeObserved 返回值/V2 built-in 类型 THEN 不支持，返回数据源本身 | 边界 |
| AC-5.4 | WHEN makeV1Observed 处理对象 THEN 不递归（区别于 enableV2Compatibility） | 边界 |

### US-6: makeBinding 构建 @Builder 参数

**作为** 应用开发者,
**我想要** 用 `makeBinding`（API 20+）构建 `@Builder` 函数中 `Binding<T>`/`MutableBinding<T>` 类型参数的实参,
**以便** 避免在 @Builder 内修改入参属性触发错误码 140109。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `UIUtils.makeBinding<T>(getter): Binding<T>`(57，API 20+) THEN 构建只读 Binding，写值报错 | 正常 |
| AC-6.2 | WHEN 调用 `UIUtils.makeBinding<T>(getter, setter): MutableBinding<T>`(58，API 20+) THEN 构建可变 MutableBinding，set value 调 setter | 正常 |
| AC-6.3 | WHEN MutableBinding 构造时未提供 setter THEN 触发 set 时运行时错误 | 异常 |
| AC-6.4 | WHEN `GetterCallback<T> = () => T` 与 `SetterCallback<T> = (newValue: T) => void` THEN 构建双向绑定参数 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 getTarget |
| AC-1.2 | US-1 | R-1 | 单元测试 V1 代理还原 |
| AC-1.3 | US-1 | R-1 | 单元测试 V2 代理还原 |
| AC-1.4 | US-1 | R-2 | 单元测试 不触发刷新 |
| AC-1.5 | US-1 | R-3 | 编译期校验 |
| AC-1.6 | US-1 | R-2 | 单元测试 __ob_ 前缀 |
| AC-2.1 | US-2 | R-4 | 单元测试 makeObserved |
| AC-2.2 | US-2 | R-4 | 单元测试 支持类型 |
| AC-2.3 | US-2 | R-4 | 单元测试 undefined/null |
| AC-2.4 | US-2 | R-3 | 编译期校验 |
| AC-2.5 | US-2 | R-4 | 单元测试 防双重代理 |
| AC-2.6 | US-2 | R-5 | 单元测试 V1 冲突 |
| AC-2.7 | US-2 | R-4 | 单元测试 内置类型观察 |
| AC-2.8 | US-2 | R-4 | 单元测试 重新赋值失效 |
| AC-3.1 | US-3 | R-6 | 单元测试 canBeObserved |
| AC-3.2 | US-3 | R-6 | 单元测试 undefined/null |
| AC-3.3 | US-3 | R-6 | 单元测试 reason |
| AC-3.4 | US-3 | R-6 | 单元测试 decoratorInfo |
| AC-3.5 | US-3 | R-6 | 代码审查 检测顺序 |
| AC-4.1 | US-4 | R-7 | 单元测试 enableV2Compatibility |
| AC-4.2 | US-4 | R-7 | 单元测试 非 V1 返回自身 |
| AC-4.3 | US-4 | R-7 | 单元测试 仅 V1 状态变量 |
| AC-4.4 | US-4 | R-7 | 单元测试 递归遍历 |
| AC-4.5 | US-4 | R-7 | 单元测试 非对象不支持 |
| AC-5.1 | US-5 | R-8 | 单元测试 makeV1Observed |
| AC-5.2 | US-5 | R-8 | 单元测试 支持类型 |
| AC-5.3 | US-5 | R-8 | 单元测试 不支持类型 |
| AC-5.4 | US-5 | R-8 | 单元测试 不递归 |
| AC-6.1 | US-6 | R-9 | 单元测试 makeBinding 只读 |
| AC-6.2 | US-6 | R-9 | 单元测试 makeBinding 可变 |
| AC-6.3 | US-6 | R-9 | 单元测试 无 setter 报错 |
| AC-6.4 | US-6 | R-9 | 单元测试 回调签名 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `UIUtils.getTarget`(23，API 12+) | 返回状态管理框架代理前的原始对象；V1 对 @Observed class/@State 装饰对象加代理；V2 对 @Trace/@Local 装饰的 Date/Map/Set/Array 加代理（不对类对象实例加代理） | 修改返回值不触发 UI 刷新 | AC-1.1~AC-1.3 |
| R-2 | 边界 | getTarget 返回值修改 / `__ob_` 前缀 | 修改 getTarget 返回值不触发 UI 刷新（脱离框架观察）；V2 @Trace 属性名有 `__ob_` 前缀，getTarget 不剥离，影响 NAPI 接口 | — | AC-1.4, AC-1.6 |
| R-3 | 异常 | getTarget/makeObserved 入参为非对象类型 | 编译报错 | 仅支持对象类型 | AC-1.5, AC-2.4 |
| R-4 | 行为 | 调用 `UIUtils.makeObserved`(39，API 12+) | 将普通对象变为 V2 可观察对象（深度观察），内部委托 `RefInfo.get`(25)；支持未装饰 class/Array/Map/Set/Date/collections/JSON.parse Object/@Sendable class；`undefined`/`null` 直接返回自身；已是 @ObservedV2/@Observed/makeObserved 包装则直接返回入参（防双重代理）；观察 Array `push/pop/shift/unshift/splice/copyWithin/fill/reverse/sort`、Map `set/clear/delete`、Set `add/clear/delete`、Date 14 个 setter | 对状态变量重新赋值为非 makeObserved 数据则失去观察能力 | AC-2.1~AC-2.5, AC-2.7, AC-2.8 |
| R-5 | 异常 | makeObserved 与 V1 状态变量装饰器一起用 | 抛运行时异常；makeObserved 走 V2 范式，不能用 V1 装饰器 | V1 场景用 makeV1Observed | AC-2.6 |
| R-6 | 行为 | 调用 `UIUtils.canBeObserved`(19，API 23+) / `ObservedUtil.canBeObserved`(121) | 返回 `ObservedResult { isObserved, reason, decoratorInfo }`；检测顺序 V2 → makeObserved → V2Proxy → V1；`undefined`/`null` 返回 `isObserved=false`；非 Object 编译报错；`reason` 描述装饰方式；`decoratorInfo` 含 `decoratorName` 与 `owningComponentId`（V2 装饰器返回 -1） | API 23+ | AC-3.1~AC-3.5 |
| R-7 | 行为 | 调用 `UIUtils.enableV2Compatibility`(50，API 19+) | 数据源是 V1 状态数据时返回能在 @ComponentV2 中观察的数据；非 V1 状态数据返回数据源本身；仅作用于 V1 状态变量（@Observed 实例或 @State/@Prop/@Link/@Provide/@Consume/@ObjectLink 装饰变量），不支持 @ObservedV2/makeObserved 返回值/V2 built-in 类型；递归遍历 class 属性、Array/Set/Map 子项直至遇到非 V1 状态变量；非 object/undefined/null 不支持 | API 19+；V1→V2 桥接 | AC-4.1~AC-4.5 |
| R-8 | 行为 | 调用 `UIUtils.makeV1Observed`(45，API 19+) | 将不可观察对象包装成 V1 可观察对象，能力等同 @Observed，返回值可初始化 @ObjectLink；支持普通 class/Array/Map/Set/Date；不支持 collections 类型/@Sendable class/非 object/undefined/null/@ObservedV2/makeObserved 返回值/V2 built-in 类型（返回数据源本身）；不递归（区别于 enableV2Compatibility） | API 19+；V2→V1 桥接 | AC-5.1~AC-5.4 |
| R-9 | 行为 | 调用 `UIUtils.makeBinding`(57-62，API 20+) | 构建只读 `Binding<T>`（`makeBinding(getter)`，写值报错）或可变 `MutableBinding<T>`（`makeBinding(getter, setter)`，set value 调 setter）；`GetterCallback<T> = () => T`、`SetterCallback<T> = (newValue: T) => void`；MutableBinding 构造时未提供 setter 则触发 set 时运行时错误；用于 @Builder 函数中 `Binding<T>`/`MutableBinding<T>` 类型参数，避免 140109 | API 20+ | AC-6.1~AC-6.4 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `common_tests/` getTarget |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` V1 代理还原 |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` V2 代理还原 |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` 不触发刷新 |
| VM-5 | AC-1.5 | 编译期校验 | ArkTS 编译器 非对象拒绝 |
| VM-6 | AC-1.6 | 单元测试 | `common_tests/` __ob_ 前缀 |
| VM-7 | AC-2.1 | 单元测试 | `v2_tests/` makeObserved |
| VM-8 | AC-2.2 | 单元测试 | `v2_tests/` 支持类型 |
| VM-9 | AC-2.3 | 单元测试 | `v2_tests/` undefined/null |
| VM-10 | AC-2.4 | 编译期校验 | ArkTS 编译器 非对象拒绝 |
| VM-11 | AC-2.5 | 单元测试 | `v2_tests/` 防双重代理 |
| VM-12 | AC-2.6 | 单元测试 | `v2_tests/` V1 冲突 |
| VM-13 | AC-2.7 | 单元测试 | `v2_tests/` 内置类型观察 |
| VM-14 | AC-2.8 | 单元测试 | `v2_tests/` 重新赋值失效 |
| VM-15 | AC-3.1 | 单元测试 | `common_tests/` canBeObserved |
| VM-16 | AC-3.2 | 单元测试 | `common_tests/` undefined/null |
| VM-17 | AC-3.3 | 单元测试 | `common_tests/` reason |
| VM-18 | AC-3.4 | 单元测试 | `common_tests/` decoratorInfo |
| VM-19 | AC-3.5 | 代码审查 | `observed_util.ts:121` 检测顺序 |
| VM-20 | AC-4.1 | 单元测试 | `v2_tests/` enableV2Compatibility |
| VM-21 | AC-4.2 | 单元测试 | `v2_tests/` 非 V1 返回自身 |
| VM-22 | AC-4.3 | 单元测试 | `v2_tests/` 仅 V1 状态变量 |
| VM-23 | AC-4.4 | 单元测试 | `v2_tests/` 递归遍历 |
| VM-24 | AC-4.5 | 单元测试 | `v2_tests/` 非对象不支持 |
| VM-25 | AC-5.1 | 单元测试 | `common_tests/` makeV1Observed |
| VM-26 | AC-5.2 | 单元测试 | `common_tests/` 支持类型 |
| VM-27 | AC-5.3 | 单元测试 | `common_tests/` 不支持类型 |
| VM-28 | AC-5.4 | 单元测试 | `common_tests/` 不递归 |
| VM-29 | AC-6.1 | 单元测试 | `v2_tests/` makeBinding 只读 |
| VM-30 | AC-6.2 | 单元测试 | `v2_tests/` makeBinding 可变 |
| VM-31 | AC-6.3 | 单元测试 | `v2_tests/` 无 setter 报错 |
| VM-32 | AC-6.4 | 单元测试 | `v2_tests/` 回调签名 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `UIUtilsImpl` | `sdk/ui_utils.ts:16-134` | 对外 UIUtils 工具类 |
| `getTarget` | `sdk/ui_utils.ts:23-37` | 还原代理对象（API 12+） |
| `makeObserved` | `sdk/ui_utils.ts:39-43` | 创建 V2 可观察对象（API 12+），委托 RefInfo.get |
| `canBeObserved` | `sdk/ui_utils.ts:19-21` | 检测可观察性（API 23+），委托 ObservedUtil |
| `enableV2Compatibility` | `sdk/ui_utils.ts:50-54` | V1→V2 桥接（API 19+） |
| `makeV1Observed` | `sdk/ui_utils.ts:45-48` | V2→V1 桥接（API 19+） |
| `makeBinding` | `sdk/ui_utils.ts:57-62` | 构建 @Builder 参数（API 20+） |
| `ObservedUtil` | `sdk/observed_util.ts:120-372` | 可观察检测工具 |
| `ObservedUtil.canBeObserved` | `sdk/observed_util.ts:121` | 检测顺序 V2→makeObserved→V2Proxy→V1 |
| `RefInfo` | `v2/v2_make_observed.ts:16-46` | makeObserved 内部实现 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | getTarget/makeObserved 引入 | 命令式对象工具 | 无需迁移 |
| API 19 | enableV2Compatibility/makeV1Observed 引入 | V1/V2 混用桥接 | V1→V2 传复杂类型调 enableV2Compatibility |
| API 20 | makeBinding 引入 | @Builder 参数构建 | 避免在 @Builder 内修改入参 |
| API 23 | canBeObserved 引入 | 可观察性检测 | 调试场景使用 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| UIUtils 是命令式工具 | UIUtils 与 V1/V2 装饰器（声明式）互补，服务运行时命令式场景 |
| makeObserved 走 V2 范式 | makeObserved 创建 V2 可观察对象，不能与 V1 装饰器一起用；V1 场景用 makeV1Observed |
| getTarget 不触发刷新 | 修改 getTarget 返回值脱离框架观察，不触发 UI 刷新 |
| V1/V2 桥接仅 V1 状态变量 | enableV2Compatibility 仅作用于 V1 状态变量，不支持 @ObservedV2/makeObserved 返回值 |
| makeBinding 服务 @Builder | 构建 Binding/MutableBinding 参数，避免 140109 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:16-134` | `UIUtilsImpl` 工具类 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:23-37` | `getTarget`（API 12+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:39-43` | `makeObserved`（API 12+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:19-21` | `canBeObserved`（API 23+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:45-54` | `makeV1Observed`/`enableV2Compatibility`（API 19+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:57-62` | `makeBinding`（API 20+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/observed_util.ts:120-372` | `ObservedUtil` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/observed_util.ts:121` | `ObservedUtil.canBeObserved` 检测顺序 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_make_observed.ts:16-46` | `RefInfo` makeObserved 内部实现 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | UIUtils/ObservedUtil 工具测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | makeObserved/enableV2Compatibility 测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-makeObserved.md` | makeObserved 指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-getTarget.md` | getTarget 指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-canBeObserved.md` | canBeObserved 指南 |
