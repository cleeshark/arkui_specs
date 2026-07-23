# 特性规格

> Func-07-02-03-Feat-01 LocalStorage 页面级存储：固化 `LocalStorage`（页面级多实例存储，`sdk/local_storage.ts:29-540`）的创建与注入、`@LocalStorageLink`/`@LocalStorageProp` 装饰器（双向/单向同步）、`link`/`prop`/`setAndLink`/`setAndProp`/`ref`/`setAndRef` 方法、CRUD（`has`/`get`/`set`/`setOrCreate`/`delete`/`keys`/`size`/`clear`）、`__createSync` 工厂、订阅者保护、跨页面共享行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | LocalStorage 页面级存储 |
| 特性编号 | Func-07-02-03-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | LocalStorage/@LocalStorageLink/@LocalStorageProp API 9 起；ref/setAndRef API 12 起；Map/Set/Date/null/undefined/联合类型 API 12 起；Function 编译期 ERROR API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| LocalStorage | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/local_storage.ts` | — |
| LocalStorage 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-localstorage.md` | — |
| 应用状态管理概述 | `docs/zh-cn/application-dev/ui/state-management/arkts-application-state-management-overview.md` | — |
| V1 应用级变量 API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | — |
| @LocalStorageLink API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-localstoragelink.md` | — |
| @LocalStorageProp API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-localstorageprop.md` | — |

---

## 用户故事

### US-1: LocalStorage 创建与注入

**作为** 应用开发者,
**我想要** 创建 LocalStorage 实例并通过 `@Entry(storage)` 注入组件树,
**以便** 在页面/组件树内共享状态，子组件自动继承同一实例。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `new LocalStorage(initializingProperties)` 创建实例 THEN `constructor`(69-84) 初始化 `storage_: Map<string, ObservedPropertyAbstract>` | 正常 |
| AC-1.2 | WHEN 通过 `@Entry(storage)` 注入到组件树根节点 THEN 子组件自动继承同一 LocalStorage 实例 | 正常 |
| AC-1.3 | WHEN 自定义组件（非根，API 12+）通过构造参数第 2 位接收 LocalStorage 实例 THEN 子组件可接收；若组件定义了其它成员属性，首参需传 `{}` | 边界 |
| AC-1.4 | WHEN `initializingProperties` 为 undefined THEN 默认空对象，不报错 | 边界 |
| AC-1.5 | WHEN LocalStorage 创建后命名属性的类型 THEN 不可更改，后续 `set` 必须用同类型值 | 边界 |

### US-2: @LocalStorageLink/@LocalStorageProp 装饰器

**作为** 应用开发者,
**我想要** 用 `@LocalStorageLink`/`@LocalStorageProp` 建立组件变量与 LocalStorage 的双向/单向同步,
**以便** 跨组件共享 LocalStorage 状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `@LocalStorageLink('key') var: T`（API 9+）装饰组件变量 THEN 经 `__createSync`(524-540) 创建 `SynchedPropertyTwoWayPU`（双向同步） | 正常 |
| AC-2.2 | WHEN `@LocalStorageProp('key') var: T`（API 9+）装饰组件变量 THEN 经 `__createSync` 创建 `SynchedPropertyOneWayPU`（单向同步） | 正常 |
| AC-2.3 | WHEN 装饰变量初始化时 LocalStorage 中无对应 key THEN 用本地初始值在 LocalStorage 中创建该属性 | 正常 |
| AC-2.4 | WHEN LocalStorage 中已存在 key THEN 装饰变量的本地初始值被 LocalStorage 值覆盖 | 正常 |
| AC-2.5 | WHEN 装饰变量不能从父节点初始化 THEN 禁止（但可用于初始化子节点的 @State/@Link/@Prop/@Provide） | 边界 |
| AC-2.6 | WHEN API 12+ THEN @LocalStorageLink/@LocalStorageProp 支持 Map/Set/Date/null/undefined/联合类型 | 正常 |
| AC-2.7 | WHEN API 23+ 装饰 Function 类型变量 THEN 编译期 ERROR | 异常 |
| AC-2.8 | WHEN 装饰器参数 key 非字符串常量 THEN 编译期报错 | 异常 |

### US-3: link/prop 双向/单向同步

**作为** 应用开发者,
**我想要** 用 `link`/`prop`/`setAndLink`/`setAndProp` 方法获取 `SubscribedAbstractProperty` 句柄,
**以便** 在非装饰器场景命令式建立同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `link<T>(propName)`(293-310) THEN 返回 `SubscribedAbstractProperty<T>`（双向同步），本地修改同步回 LocalStorage | 正常 |
| AC-3.2 | WHEN `prop<S>(propName)`(351-369) THEN 返回 `SubscribedAbstractProperty<S>`（单向同步），本地修改不回写 | 正常 |
| AC-3.3 | WHEN `setAndLink<T>(propName, defaultValue)`(326-335) THEN 若 key 不存在用 defaultValue 创建后 link | 正常 |
| AC-3.4 | WHEN `setAndProp<S>(propName, defaultValue)`(383-392) THEN 若 key 不存在用 defaultValue 创建后 prop | 正常 |
| AC-3.5 | WHEN `ref<T>(propName)`(235-237，API 12+) THEN 返回 `AbstractProperty<T>`（双向，框架自动管理释放，无需手动 aboutToBeDeleted） | 正常 |
| AC-3.6 | WHEN `setAndRef<T>(propName, defaultValue)`(250-255，API 12+) THEN 若 key 不存在用 defaultValue 创建后 ref | 正常 |

### US-4: CRUD 与订阅者保护

**作为** 应用开发者,
**我想要** 用 `has`/`get`/`set`/`setOrCreate`/`delete`/`keys`/`size`/`clear` 管理 LocalStorage 属性,
**以便** 命令式操作存储。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `has(propName)`(123-125) THEN 返回 boolean | 正常 |
| AC-4.2 | WHEN `get<T>(propName)`(161-164) THEN 返回值或 undefined | 正常 |
| AC-4.3 | WHEN `set<T>(propName, newValue)`(177-193) THEN 仅 key 已存在时生效返回 true，否则 false；同值不触发 UI 刷新 | 正常 |
| AC-4.4 | WHEN `setOrCreate<T>(propName, newValue)`(207-225) THEN 不存在则创建 | 正常 |
| AC-4.5 | WHEN `delete(propName)`(414-443) THEN **仅当属性无订阅者时**返回 true，否则 false | 边界 |
| AC-4.6 | WHEN `clear()`(454-483) THEN **仅当所有属性无订阅者时**返回 true | 边界 |
| AC-4.7 | WHEN 订阅者包括 @LocalStorageLink/@LocalStorageProp 变量、link/prop 返回的 SubscribedAbstractProperty 实例 THEN 需调 `aboutToBeDeleted` 释放 | 边界 |
| AC-4.8 | WHEN `keys()`(135-137)/`size()`(148-150) THEN 返回所有 key / key 数量 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 创建 |
| AC-1.2 | US-1 | R-1 | 单元测试 @Entry 注入 |
| AC-1.3 | US-1 | R-1 | 单元测试 子组件接收 |
| AC-1.4 | US-1 | R-1 | 单元测试 undefined |
| AC-1.5 | US-1 | R-2 | 单元测试 类型不可改 |
| AC-2.1 | US-2 | R-3 | 单元测试 @LocalStorageLink |
| AC-2.2 | US-2 | R-3 | 单元测试 @LocalStorageProp |
| AC-2.3 | US-2 | R-3 | 单元测试 无 key 用初始值创建 |
| AC-2.4 | US-2 | R-3 | 单元测试 有 key 覆盖 |
| AC-2.5 | US-2 | R-4 | 单元测试 不能从父初始化 |
| AC-2.6 | US-2 | R-3 | 单元测试 Map/Set/Date |
| AC-2.7 | US-2 | R-5 | 编译期校验 |
| AC-2.8 | US-2 | R-5 | 编译期校验 |
| AC-3.1 | US-3 | R-6 | 单元测试 link |
| AC-3.2 | US-3 | R-6 | 单元测试 prop |
| AC-3.3 | US-3 | R-6 | 单元测试 setAndLink |
| AC-3.4 | US-3 | R-6 | 单元测试 setAndProp |
| AC-3.5 | US-3 | R-7 | 单元测试 ref |
| AC-3.6 | US-3 | R-7 | 单元测试 setAndRef |
| AC-4.1 | US-4 | R-8 | 单元测试 has |
| AC-4.2 | US-4 | R-8 | 单元测试 get |
| AC-4.3 | US-4 | R-8 | 单元测试 set |
| AC-4.4 | US-4 | R-8 | 单元测试 setOrCreate |
| AC-4.5 | US-4 | R-9 | 单元测试 delete 订阅者保护 |
| AC-4.6 | US-4 | R-9 | 单元测试 clear 订阅者保护 |
| AC-4.7 | US-4 | R-9 | 单元测试 aboutToBeDeleted |
| AC-4.8 | US-4 | R-8 | 单元测试 keys/size |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建 LocalStorage 并注入 | `new LocalStorage(initializingProperties)`(69-84) 初始化 `storage_: Map`；通过 `@Entry(storage)` 注入组件树根节点，子组件自动继承；自定义组件（API 12+）可通过构造参数第 2 位接收；`initializingProperties` 为 undefined 默认空对象 | LocalStorage 是页面级可多实例存储 | AC-1.1~AC-1.4 |
| R-2 | 边界 | LocalStorage 属性类型 | 创建后命名属性的类型不可更改，后续 `set` 必须用同类型值 | 类型固定 | AC-1.5 |
| R-3 | 行为 | @LocalStorageLink/@LocalStorageProp 装饰（API 9+） | 经 `__createSync`(524-540) 创建 `SynchedPropertyTwoWayPU`（@LocalStorageLink 双向）/ `SynchedPropertyOneWayPU`（@LocalStorageProp 单向）；初始化时 LocalStorage 无 key 则用本地初始值创建，有 key 则覆盖本地；API 12+ 支持 Map/Set/Date/null/undefined/联合类型 | 不能从父节点初始化；key 必须为字符串常量 | AC-2.1~AC-2.6, AC-2.8 |
| R-4 | 边界 | 装饰变量初始化约束 | 不能从父节点初始化（禁止），但可用于初始化子节点的 @State/@Link/@Prop/@Provide | — | AC-2.5 |
| R-5 | 异常 | 装饰 Function 类型（API 23+）或 key 非字符串 | API 23+ Function 类型编译期 ERROR；key 非字符串常量编译期报错 | Function 不支持 | AC-2.7, AC-2.8 |
| R-6 | 行为 | link/prop/setAndLink/setAndProp | `link<T>`(293-310) 返回 `SubscribedAbstractProperty<T>`（双向，本地修改同步回 LocalStorage）；`prop<S>`(351-369) 返回单向（不回写）；`setAndLink`(326-335)/`setAndProp`(383-392) 若 key 不存在用 defaultValue 创建 | `addNewPropertyInternal`(266-277) 按 PU/FU 分支创建属性 | AC-3.1~AC-3.4 |
| R-7 | 行为 | ref/setAndRef（API 12+） | `ref<T>`(235-237) 返回 `AbstractProperty<T>`（双向，框架自动管理释放，无需手动 aboutToBeDeleted）；`setAndRef`(250-255) 若 key 不存在用 defaultValue 创建后 ref | API 12+；自动释放 | AC-3.5, AC-3.6 |
| R-8 | 行为 | CRUD（has/get/set/setOrCreate/keys/size） | `has`(123-125) 返回 boolean；`get`(161-164) 返回值或 undefined；`set`(177-193) 仅 key 已存在时生效返回 true，同值不触发 UI 刷新；`setOrCreate`(207-225) 不存在则创建；`keys`(135-137)/`size`(148-150) 返回 key 列表/数量 | `set` 仅 key 已存在时生效 | AC-4.1~AC-4.4, AC-4.8 |
| R-9 | 边界 | delete/clear 订阅者保护 | `delete`(414-443) 仅当属性无订阅者时返回 true，否则 false；`clear`(454-483) 仅当所有属性无订阅者时返回 true；订阅者包括 @LocalStorageLink/@LocalStorageProp 变量、link/prop 返回的 SubscribedAbstractProperty 实例，需调 `aboutToBeDeleted` 释放 | 订阅者保护避免悬挂引用 | AC-4.5~AC-4.7 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `common_tests/` 创建 |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` @Entry 注入 |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` 子组件接收 |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` undefined |
| VM-5 | AC-1.5 | 单元测试 | `common_tests/` 类型不可改 |
| VM-6 | AC-2.1 | 单元测试 | `common_tests/` @LocalStorageLink |
| VM-7 | AC-2.2 | 单元测试 | `common_tests/` @LocalStorageProp |
| VM-8 | AC-2.3 | 单元测试 | `common_tests/` 无 key 用初始值 |
| VM-9 | AC-2.4 | 单元测试 | `common_tests/` 有 key 覆盖 |
| VM-10 | AC-2.5 | 单元测试 | `common_tests/` 不能从父初始化 |
| VM-11 | AC-2.6 | 单元测试 | `common_tests/` Map/Set/Date |
| VM-12 | AC-2.7 | 编译期校验 | ArkTS 编译器 Function ERROR |
| VM-13 | AC-2.8 | 编译期校验 | ArkTS 编译器 key 类型 |
| VM-14 | AC-3.1 | 单元测试 | `common_tests/` link |
| VM-15 | AC-3.2 | 单元测试 | `common_tests/` prop |
| VM-16 | AC-3.3 | 单元测试 | `common_tests/` setAndLink |
| VM-17 | AC-3.4 | 单元测试 | `common_tests/` setAndProp |
| VM-18 | AC-3.5 | 单元测试 | `common_tests/` ref |
| VM-19 | AC-3.6 | 单元测试 | `common_tests/` setAndRef |
| VM-20 | AC-4.1 | 单元测试 | `common_tests/` has |
| VM-21 | AC-4.2 | 单元测试 | `common_tests/` get |
| VM-22 | AC-4.3 | 单元测试 | `common_tests/` set |
| VM-23 | AC-4.4 | 单元测试 | `common_tests/` setOrCreate |
| VM-24 | AC-4.5 | 单元测试 | `common_tests/` delete 订阅者保护 |
| VM-25 | AC-4.6 | 单元测试 | `common_tests/` clear 订阅者保护 |
| VM-26 | AC-4.7 | 单元测试 | `common_tests/` aboutToBeDeleted |
| VM-27 | AC-4.8 | 单元测试 | `common_tests/` keys/size |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `LocalStorage` | `sdk/local_storage.ts:29-540` | 页面级存储（extends NativeStorage） |
| `constructor` | `sdk/local_storage.ts:69-84` | 初始化 storage_ Map |
| `link`/`setAndLink` | `sdk/local_storage.ts:293-310/326-335` | 双向同步 |
| `prop`/`setAndProp` | `sdk/local_storage.ts:351-369/383-392` | 单向同步 |
| `ref`/`setAndRef` | `sdk/local_storage.ts:235-237/250-255` | 双向自动释放（API 12+） |
| `has`/`get`/`set`/`setOrCreate` | `sdk/local_storage.ts:123-225` | CRUD |
| `delete`/`clear` | `sdk/local_storage.ts:414-443/454-483` | 订阅者保护删除 |
| `keys`/`size` | `sdk/local_storage.ts:135-137/148-150` | 查询 |
| `__createSync` | `sdk/local_storage.ts:524-540` | @LocalStorageLink/@LocalStorageProp 编译产物工厂 |
| `addNewPropertyInternal` | `sdk/local_storage.ts:266-277` | PU/FU 属性创建分支 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 9 | LocalStorage 与 @LocalStorageLink/@LocalStorageProp 引入 | 页面级存储 | 无需迁移 |
| API 10 | `getShared()` 引入（API 18 废弃） | 跨页面共享 | 改用 UIContext.getSharedLocalStorage |
| API 12 | ref/setAndRef 引入（自动释放）；Map/Set/Date/null/undefined/联合类型 | 更多类型+自动管理 | 无需迁移 |
| API 23 | Function 类型编译期 ERROR | 类型校验加强 | 移除 Function 类型 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 页面级多实例 | LocalStorage 是页面级可多实例存储；AppStorage 继承 LocalStorage 并增加单例（Feat-08） |
| 订阅者保护 | delete/clear 仅在无订阅者时成功；需 aboutToBeDeleted 释放 SubscribedAbstractProperty 句柄 |
| 类型不可改 | 创建后命名属性的类型不可更改 |
| @LocalStorageLink/@LocalStorageProp 不能从父初始化 | 但可用于初始化子节点的 @State/@Link/@Prop/@Provide |
| PU/FU 分支 | `addNewPropertyInternal` 按 `ViewStackProcessor.UsesNewPipeline()` 决定 PU/FU 属性类型 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/local_storage.ts:29-540` | `LocalStorage` 页面级存储 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/local_storage.ts:69-84` | `constructor` 初始化 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/local_storage.ts:293-392` | `link`/`prop`/`setAndLink`/`setAndProp` 同步方法 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/local_storage.ts:235-255` | `ref`/`setAndRef` 自动释放（API 12+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/local_storage.ts:414-483` | `delete`/`clear` 订阅者保护 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/local_storage.ts:524-540` | `__createSync` 装饰器工厂 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | LocalStorage 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-localstorage.md` | LocalStorage 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | V1 应用级变量 API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-localstoragelink.md` | @LocalStorageLink API |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-localstorageprop.md` | @LocalStorageProp API |
