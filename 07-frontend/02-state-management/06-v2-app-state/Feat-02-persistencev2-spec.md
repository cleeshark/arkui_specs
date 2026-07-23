# 特性规格

> Func-07-02-06-Feat-02 PersistenceV2 磁盘持久化与 @Type/DataCoder：固化 `PersistenceV2`（`PersistenceV2Impl extends StorageHelper`，`sdk/v2_persistence.ts:279-913`，`MIN_PERSISTENCE_ID=0x1020000000000`）的 `connect`（module 级，API 12+）/`globalConnect`（应用级，API 18+，EL1-EL5 加密级别）/集合类型重载（API 23+）、`@Type` 序列化类型标记、`DataCoder` 编解码（保持原型链）、`ObserveV2` 依赖图自动追踪 `@Trace` 变化、错误码 140103-140109/140116 行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | PersistenceV2 磁盘持久化与 @Type/DataCoder |
| 特性编号 | Func-07-02-06-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | connect/remove/keys/save/notifyOnError API 12 起；globalConnect API 18 起；集合类型重载（`ConnectOptionsCollections`）API 23 起；错误码 140105/140106 由 crash 改为返回码 API 23 起；PersistenceErrorCallback.oldValue API 26 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Draft |
| PersistenceV2Impl | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts` | — |
| DataCoder/JSONCoder | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/` | — |
| @Type 实现 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/json_coder.ts` | — |
| PersistenceV2 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-persistencev2.md` | — |
| StateManagement 模块 | `docs/zh-cn/application-dev/reference/apis-arkui/js-apis-stateManagement.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: connect module 级持久化

**作为** 应用开发者,
**我想要** 用 `PersistenceV2.connect`（API 12+）建立 module 级磁盘持久化,
**以便** 应用退出再启动后恢复 V2 状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `PersistenceV2.connect<T>(type, keyOrDefaultCreator?, defaultCreator?)`(341-394，API 12+) THEN 返回内存中 class 实例并写入设备磁盘；继承自 AppStorageV2 的 connect 行为 | 正常 |
| AC-1.2 | WHEN connect 存储**路径为 module 级** THEN 哪个 module 调用存到哪个 module 的持久化文件 | 正常 |
| AC-1.3 | WHEN `@Trace` 属性变化 THEN 触发**整个关联对象的自动持久化**（经 ObserveV2 依赖图 `startRecordDependencies`/`stopRecordDependencies` → `onChangeObserved` → `writeAllChangedToFile`(762-793)） | 正常 |
| AC-1.4 | WHEN 非 `@Trace` 属性变化 THEN 不触发自动持久化，需手动调 `save` | 边界 |
| AC-1.5 | WHEN connect defaultCreator 仅首次（内存+磁盘都不存在）调用 THEN 后续 connect 可省略 | 边界 |
| AC-1.6 | WHEN 应用退出再启动 THEN 恢复选定结果（经 `getValueFromDisk`(689-740) `DataCoder.parse` 反序列化） | 正常 |

### US-2: globalConnect 应用级持久化（API 18+）

**作为** 应用开发者,
**我想要** 用 `PersistenceV2.globalConnect`（API 18+）建立应用级磁盘持久化,
**以便** 跨 module 共享持久化数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `globalConnect<T>(type: ConnectOptions<T>)`(401-461，API 18+) THEN 存储**路径为应用级** | 正常 |
| AC-2.2 | WHEN `ConnectOptions.areaMode` THEN 支持 EL1-EL5（数值 0-4），不传默认 EL2 | 正常 |
| AC-2.3 | WHEN EL5 加密 THEN 需在 module.json 配置 `ohos.permission.PROTECT_SCREEN_LOCK_DATA` | 边界 |
| AC-2.4 | WHEN 同一 key 不同加密级别 THEN 以**第一次** globalConnect 的加密级别为准 | 边界 |
| AC-2.5 | WHEN connect 与 globalConnect 混用相同 key THEN crash；API 23+ 返回错误码 140105 | 异常 |
| AC-2.6 | WHEN areaMode 不在 EL1-EL5（0-4）THEN crash；API 23+ 返回错误码 140106 | 异常 |

### US-3: 集合类型重载（API 23+）

**作为** 应用开发者,
**我想要** API 23+ 持久化集合类型（Array/Map/Set/collections）与循环引用对象,
**以便** 持久化复杂数据结构。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN API 23+ `globalConnect<T extends CollectionType<S>>` 集合类型重载 THEN 支持顶层 Array/Map/Set/Date/collections.Array/Map/Set | 正常 |
| AC-3.2 | WHEN 持久化 `Array<ClassA>` THEN 必须同时提供 `defaultCreator` 和 `defaultSubCreator`（`ConnectOptionsCollections`，API 23+） | 正常 |
| AC-3.3 | WHEN API 23+ THEN 支持 `@Sendable` 装饰类对象持久化（成员属性须为 string/number/boolean） | 正常 |
| AC-3.4 | WHEN API 23+ THEN 支持循环引用对象；解除单个 key ≤ 8k 限制（读写仍在 UI 线程同步） | 正常 |
| AC-3.5 | WHEN 持久化 `Array<ClassA>` 必须用 `UIUtils.makeObserved` 包装返回值 THEN 否则 JSON 对象无观察力，自动持久化失败 | 边界 |
| AC-3.6 | WHEN 不支持多层嵌套集合（如 `Array<Array<ClassA>>`）THEN 限制 | 边界 |
| AC-3.7 | WHEN globalConnect 持久化复杂类型缺 `@Type` THEN 错误码 140108（仅日志上报） | 异常 |

### US-4: @Type 序列化类型标记

**作为** 应用开发者,
**我想要** 用 `@Type` 标记持久化类的嵌套对象属性类型,
**以便** DataCoder 反序列化时保持原型链。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `@Type(type)` 装饰 @ObservedV2 类属性 THEN `__Type__`（`json_coder.ts:72`）注册到 `Meta`(31-70) WeakMap（原型链继承） | 正常 |
| AC-4.2 | WHEN 持久化类中自定义 class 属性必须用 `@Type` 装饰 THEN 属性值必须严格为 `@Type` 指定类的实例 | 正常 |
| AC-4.3 | WHEN 被持久化的 class 属性 THEN 必须要有初值 | 边界 |
| AC-4.4 | WHEN 被 connect/globalConnect 的类中使用 `@Computed` THEN 不允许（只读属性导致反序列化失败） | 异常 |
| AC-4.5 | WHEN @Type 仅支持自定义 class 类型 THEN 传入其它类型持久化失败 | 边界 |

### US-5: DataCoder 序列化与自动追踪

**作为** 应用开发者,
**我想要** 了解 DataCoder 的保持原型链序列化机制,
**以便** 理解持久化数据的恢复行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `DataCoder.stringify`(33-51) THEN 序列化对象到 JSON2 格式（`FORMAT_TAG='JSON2'`），保持 `@Type`/`@Trace` 元信息 | 正常 |
| AC-5.2 | WHEN `DataCoder.parse`(54-58) THEN 反序列化 JSON2 字符串到对象 | 正常 |
| AC-5.3 | WHEN `DataCoder.restoreTo`(63-) THEN 将解析数据恢复到**已有 @ObservedV2 实例**（区别于 JSON.parse 创建新对象） | 正常 |
| AC-5.4 | WHEN PersistenceV2 自动持久化经 ObserveV2 依赖图 THEN `@Trace` change → `fireChange` → Persistence ID 段路由 → `onChangeObserved`(566-568) → `writeAllChangedToFile`(762-793) | 正常 |
| AC-5.5 | WHEN PersistenceV2 不支持的类型 THEN WeakSet/WeakMap/Boolean/Number/String/Symbol/BigInt/RegExp/Function/Promise/ArrayBuffer | 边界 |

### US-6: remove/save/keys/notifyOnError

**作为** 应用开发者,
**我想要** 用 remove/save/keys/notifyOnError 管理 PersistenceV2,
**以便** 清理、手动持久化、查询、错误回调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `remove<T>(keyOrType)`(493-515，API 12+) THEN 委托 `disconnectValue`(581-594) 断开并删除 | 正常 |
| AC-6.2 | WHEN `save<T>(keyOrType)`(517-560，API 12+) THEN 手动持久化当前内存中处于 connect 状态的 key；否则无意义 | 正常 |
| AC-6.3 | WHEN `keys()`(463-491，API 12+) THEN 同时返回 module 级和应用级存储路径中的所有 key | 正常 |
| AC-6.4 | WHEN `notifyOnError(callback: PersistenceErrorCallback)`(562-564，API 12+) THEN 注册序列化/反序列化失败回调，`reason` 取值 `'quota' \| 'serialization' \| 'unknown'` | 正常 |
| AC-6.5 | WHEN `PersistenceErrorCallback.oldValue` THEN API 26+ 起提供旧值 | 边界 |
| AC-6.6 | WHEN remove/save key 不是 string 或 `TypeConstructorWithArgs<T>` THEN 错误码 140116 | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 connect |
| AC-1.2 | US-1 | R-1 | 单元测试 module 级 |
| AC-1.3 | US-1 | R-2 | 单元测试 @Trace 自动持久化 |
| AC-1.4 | US-1 | R-2 | 单元测试 非 @Trace 手动 save |
| AC-1.5 | US-1 | R-1 | 单元测试 defaultCreator 仅首次 |
| AC-1.6 | US-1 | R-1 | 单元测试 重启恢复 |
| AC-2.1 | US-2 | R-3 | 单元测试 globalConnect 应用级 |
| AC-2.2 | US-2 | R-3 | 单元测试 areaMode |
| AC-2.3 | US-2 | R-3 | 单元测试 EL5 权限 |
| AC-2.4 | US-2 | R-3 | 单元测试 加密级别优先 |
| AC-2.5 | US-2 | R-4 | 单元测试 混用 key |
| AC-2.6 | US-2 | R-5 | 单元测试 areaMode 越界 |
| AC-3.1 | US-3 | R-6 | 单元测试 集合类型 |
| AC-3.2 | US-3 | R-6 | 单元测试 defaultSubCreator |
| AC-3.3 | US-3 | R-6 | 单元测试 @Sendable |
| AC-3.4 | US-3 | R-6 | 单元测试 循环引用 |
| AC-3.5 | US-3 | R-6 | 单元测试 makeObserved 包装 |
| AC-3.6 | US-3 | R-6 | 单元测试 不支持多层嵌套 |
| AC-3.7 | US-3 | R-7 | 单元测试 错误码 140108 |
| AC-4.1 | US-4 | R-8 | 单元测试 @Type 注册 |
| AC-4.2 | US-4 | R-8 | 单元测试 严格实例 |
| AC-4.3 | US-4 | R-8 | 单元测试 必须初值 |
| AC-4.4 | US-4 | R-9 | 单元测试 @Computed 禁止 |
| AC-4.5 | US-4 | R-8 | 单元测试 仅 class |
| AC-5.1 | US-5 | R-10 | 单元测试 stringify |
| AC-5.2 | US-5 | R-10 | 单元测试 parse |
| AC-5.3 | US-5 | R-10 | 单元测试 restoreTo |
| AC-5.4 | US-5 | R-2 | 代码审查 自动追踪链 |
| AC-5.5 | US-5 | R-11 | 单元测试 不支持类型 |
| AC-6.1 | US-6 | R-12 | 单元测试 remove |
| AC-6.2 | US-6 | R-12 | 单元测试 save |
| AC-6.3 | US-6 | R-12 | 单元测试 keys |
| AC-6.4 | US-6 | R-12 | 单元测试 notifyOnError |
| AC-6.5 | US-6 | R-12 | 单元测试 oldValue |
| AC-6.6 | US-6 | R-12 | 单元测试 错误码 140116 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `connect<T>(type, keyOrDefaultCreator?, defaultCreator?)`(341-394，API 12+) | 返回内存中 class 实例并写入设备磁盘；存储路径为 module 级；defaultCreator 仅首次（内存+磁盘都不存在）调用；应用退出再启动恢复（`getValueFromDisk`(689-740) `DataCoder.parse` 反序列化） | 继承 AppStorageV2.connect 行为 | AC-1.1, AC-1.2, AC-1.5, AC-1.6 |
| R-2 | 行为 | `@Trace` 属性变化 → 自动持久化 | 经 ObserveV2 依赖图 `startRecordDependencies`/`stopRecordDependencies` 注册 → `@Trace` change → `fireChange` → Persistence ID 段（`MIN_PERSISTENCE_ID=0x1020000000000`）路由 → `onChangeObserved`(566-568) → `writeAllChangedToFile`(762-793)；非 @Trace 属性变化不触发，需手动 `save` | ObserveV2 依赖图自动追踪 | AC-1.3, AC-1.4, AC-5.4 |
| R-3 | 行为 | `globalConnect<T>(type: ConnectOptions<T>)`(401-461，API 18+) | 存储**路径为应用级**；`ConnectOptions.areaMode` 支持 EL1-EL5（数值 0-4），默认 EL2；EL5 需 `ohos.permission.PROTECT_SCREEN_LOCK_DATA`；同一 key 不同加密级别以第一次为准 | API 18+；应用级存储 | AC-2.1~AC-2.4 |
| R-4 | 异常 | connect 与 globalConnect 混用相同 key | crash；API 23+ 返回错误码 140105（`Duplicate key used when connect`） | API 23+ 由 crash 改为返回码 | AC-2.5 |
| R-5 | 异常 | areaMode 不在 EL1-EL5（0-4） | crash；API 23+ 返回错误码 140106（`AreaMode Value Error!`） | API 23+ 由 crash 改为返回码 | AC-2.6 |
| R-6 | 行为 | API 23+ 集合类型重载 `globalConnect<T extends CollectionType<S>>` | 支持顶层 Array/Map/Set/Date/collections.Array/Map/Set；持久化 `Array<ClassA>` 必须同时提供 `defaultCreator` 和 `defaultSubCreator`（`ConnectOptionsCollections`）；支持 @Sendable（成员属性须为 string/number/boolean）；支持循环引用；解除单 key ≤ 8k 限制（读写仍在 UI 线程同步）；持久化 `Array<ClassA>` 必须用 `UIUtils.makeObserved` 包装返回值；不支持多层嵌套集合（如 `Array<Array<ClassA>>`）；缺 `@Type` 返回 140108（仅日志） | API 23+；Map/collections.Map K 只能是 string\|number | AC-3.1~AC-3.7 |
| R-7 | 异常 | globalConnect 持久化复杂类型缺 `@Type` | 错误码 140108（`Miss @Type.`，仅日志上报，不抛运行时异常） | — | AC-3.7 |
| R-8 | 行为 | `@Type(type)` 装饰 @ObservedV2 类属性 | `__Type__`（`json_coder.ts:72`）注册到 `Meta`(31-70) WeakMap（原型链继承）；持久化类中自定义 class 属性必须用 @Type 装饰；属性值必须严格为 @Type 指定类的实例；被持久化的 class 属性必须要有初值；@Type 仅支持自定义 class 类型，传入其它类型持久化失败 | 仅 @ObservedV2 类属性 | AC-4.1~AC-4.3, AC-4.5 |
| R-9 | 异常 | 被 connect/globalConnect 的类中使用 `@Computed` | 不允许（只读属性导致反序列化失败） | — | AC-4.4 |
| R-10 | 行为 | `DataCoder` 序列化 | `stringify`(33-51) 序列化到 JSON2 格式（`FORMAT_TAG='JSON2'`），保持 @Type/@Trace 元信息；`parse`(54-58) 反序列化 JSON2 字符串；`restoreTo`(63-) 将解析数据恢复到已有 @ObservedV2 实例（区别于 JSON.parse 创建新对象） | DataCoder 保持原型链 | AC-5.1~AC-5.3 |
| R-11 | 边界 | PersistenceV2 不支持的类型 | WeakSet/WeakMap/Boolean/Number/String/Symbol/BigInt/RegExp/Function/Promise/ArrayBuffer 不支持 | — | AC-5.5 |
| R-12 | 行为 | `remove`/`save`/`keys`/`notifyOnError` | `remove<T>(keyOrType)`(493-515) 委托 `disconnectValue`(581-594) 断开并删除；`save<T>(keyOrType)`(517-560) 手动持久化当前 connect 状态的 key；`keys()`(463-491) 同时返回 module 级和应用级 key；`notifyOnError(callback)`(562-564) 注册序列化/反序列化失败回调（reason: quota/serialization/unknown，oldValue API 26+）；remove/save key 不是 string/TypeConstructor 返回 140116 | — | AC-6.1~AC-6.6 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` connect |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` module 级 |
| VM-3 | AC-1.3 | 代码审查 | `v2_persistence.ts:566-568` 自动持久化链 |
| VM-4 | AC-1.4 | 单元测试 | `v2_tests/` 非 @Trace 手动 save |
| VM-5 | AC-1.5 | 单元测试 | `v2_tests/` defaultCreator 仅首次 |
| VM-6 | AC-1.6 | 单元测试 | `v2_tests/` 重启恢复 |
| VM-7 | AC-2.1 | 单元测试 | `v2_tests/` globalConnect 应用级 |
| VM-8 | AC-2.2 | 单元测试 | `v2_tests/` areaMode |
| VM-9 | AC-2.3 | 单元测试 | `v2_tests/` EL5 权限 |
| VM-10 | AC-2.4 | 单元测试 | `v2_tests/` 加密级别优先 |
| VM-11 | AC-2.5 | 单元测试 | `v2_tests/` 混用 key |
| VM-12 | AC-2.6 | 单元测试 | `v2_tests/` areaMode 越界 |
| VM-13 | AC-3.1 | 单元测试 | `v2_tests/` 集合类型 |
| VM-14 | AC-3.2 | 单元测试 | `v2_tests/` defaultSubCreator |
| VM-15 | AC-3.3 | 单元测试 | `v2_tests/` @Sendable |
| VM-16 | AC-3.4 | 单元测试 | `v2_tests/` 循环引用 |
| VM-17 | AC-3.5 | 单元测试 | `v2_tests/` makeObserved 包装 |
| VM-18 | AC-3.6 | 单元测试 | `v2_tests/` 不支持多层嵌套 |
| VM-19 | AC-3.7 | 单元测试 | `v2_tests/` 错误码 140108 |
| VM-20 | AC-4.1 | 单元测试 | `v2_tests/` @Type 注册 |
| VM-21 | AC-4.2 | 单元测试 | `v2_tests/` 严格实例 |
| VM-22 | AC-4.3 | 单元测试 | `v2_tests/` 必须初值 |
| VM-23 | AC-4.4 | 单元测试 | `v2_tests/` @Computed 禁止 |
| VM-24 | AC-4.5 | 单元测试 | `v2_tests/` 仅 class |
| VM-25 | AC-5.1 | 单元测试 | `v2_tests/` stringify |
| VM-26 | AC-5.2 | 单元测试 | `v2_tests/` parse |
| VM-27 | AC-5.3 | 单元测试 | `v2_tests/` restoreTo |
| VM-28 | AC-5.4 | 代码审查 | `v2_persistence.ts:762-793` writeAllChangedToFile |
| VM-29 | AC-5.5 | 单元测试 | `v2_tests/` 不支持类型 |
| VM-30 | AC-6.1 | 单元测试 | `v2_tests/` remove |
| VM-31 | AC-6.2 | 单元测试 | `v2_tests/` save |
| VM-32 | AC-6.3 | 单元测试 | `v2_tests/` keys |
| VM-33 | AC-6.4 | 单元测试 | `v2_tests/` notifyOnError |
| VM-34 | AC-6.5 | 单元测试 | `v2_tests/` oldValue |
| VM-35 | AC-6.6 | 单元测试 | `v2_tests/` 错误码 140116 |

---

## 错误码规格

| 错误码 | 触发条件 | 错误信息 | 起始版本 |
|--------|----------|----------|----------|
| 140103 | connect/globalConnect type 非 `TypeConstructorWithArgs<T>` | `Not supported type!` | API 23 起返回码 |
| 140104 | 首次 connect/globalConnect defaultCreator 不是 `StorageDefaultCreator<T>` | `The default creator should be function when first connect.` | API 12 |
| 140105 | connect 和 globalConnect 使用相同 key | `Duplicate key used when connect` | API 23 起返回码（此前 crash） |
| 140106 | globalConnect areaMode 不在 EL1-EL5（0-4） | `AreaMode Value Error! value range can only in EL1-EL5` | API 23 起返回码（此前 crash） |
| 140107 | type 类型与 defaultCreator 返回类型不一致；持久化前后类型不一致 | `The type of target mismatches the type of source.` | API 12（仅日志） |
| 140108 | globalConnect 持久化复杂类型缺 `@Type` | `Miss @Type.` | API 18（仅日志） |
| 140116 | remove/save key 不是 string 或 `TypeConstructorWithArgs<T>` | `The key is invalid` | API 12 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `PersistenceV2Impl extends StorageHelper` | `sdk/v2_persistence.ts:279-913` | V2 磁盘持久化单例 |
| `MIN_PERSISTENCE_ID` | `sdk/v2_persistence.ts:280` | `0x1020000000000` 持久化 ID 段起点 |
| `connect<T>` | `sdk/v2_persistence.ts:341-394` | module 级持久化（API 12+） |
| `globalConnect<T>` | `sdk/v2_persistence.ts:401-461` | 应用级持久化（API 18+） |
| `remove`/`save`/`keys`/`notifyOnError` | `sdk/v2_persistence.ts:493-564` | 管理 API |
| `onChangeObserved`/`writeAllChangedToFile` | `sdk/v2_persistence.ts:566-568/762-793` | ObserveV2 自动持久化回调 |
| `getValueFromDisk`/`setValueToDisk` | `sdk/v2_persistence.ts:689-760` | 磁盘读写 |
| `DataCoder` | `v2/v2_data_coder/data_coder.ts:21-380` | JSON2 序列化（保持原型链） |
| `JSONCoder`/`Meta`/`__Type__` | `v2/v2_data_coder/json_coder.ts:138-493/31-70/72` | @Type 元信息 + 传统编解码 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | PersistenceV2.connect/remove/keys/save/notifyOnError + @Type + DataCoder 引入 | V2 磁盘持久化 | V1 PersistentStorage→PersistenceV2（官方推荐） |
| API 18 | globalConnect（应用级，EL1-EL5）引入 | 跨 module 持久化 | 替代 V1 persistProp |
| API 23 | 集合类型重载；@Sendable/循环引用；解除 8k 限制；140105/140106 由 crash 改为返回码 | 集合+健壮性 | 处理新增错误码 |
| API 26 | PersistenceErrorCallback.oldValue | 错误回传旧值 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| module 级 vs 应用级 | connect 存 module 级路径；globalConnect 存应用级路径；不建议混用，同 key crash/140105 |
| ObserveV2 自动追踪 | @Trace 属性变化经 ObserveV2 依赖图自动持久化；非 @Trace 需手动 save |
| DataCoder 保持原型链 | `restoreTo` 恢复到已有 @ObservedV2 实例（区别于 JSON.parse）；嵌套对象缺 @Type 报 140108 |
| @Type 仅 @ObservedV2 | @Type 装饰器仅用于 @ObservedV2 类，服务于 PersistenceV2 序列化 |
| @Computed 禁止 | 被 connect/globalConnect 的类中不允许 @Computed（只读属性导致反序列化失败） |
| EL1-EL5 加密级别 | globalConnect 支持 EL1-EL5（0-4），默认 EL2，EL5 需权限 |
| 不支持类型清单 | WeakSet/WeakMap/Boolean/Number/String/Symbol/BigInt/RegExp/Function/Promise/ArrayBuffer |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:279-913` | `PersistenceV2Impl` V2 磁盘持久化 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:341-394` | `connect` module 级 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:401-461` | `globalConnect` 应用级（API 18+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:493-564` | `remove`/`save`/`keys`/`notifyOnError` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:566-568/762-793` | `onChangeObserved`/`writeAllChangedToFile` 自动持久化 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:689-760` | `getValueFromDisk`/`setValueToDisk` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/data_coder.ts:21-380` | `DataCoder` JSON2 序列化 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/json_coder.ts:31-83` | `Meta`/`__Type__` @Type 元信息 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_data_coder/json_coder.ts:138-493` | `JSONCoder` 传统编解码 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | PersistenceV2/DataCoder/@Type 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-persistencev2.md` | PersistenceV2 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/js-apis-stateManagement.md` | StateManagement 模块 |
| `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | 错误码 140103-140109/140116 |
