# 特性规格

> Func-07-02-03-Feat-02 AppStorage 全局存储与存储装饰器：固化 `AppStorage`（应用级全局单例，`extends LocalStorage`，`sdk/app_storage.ts:27-514`）的静态 API、`@StorageLink`/`@StorageProp` 装饰器（双向/单向同步）、进程级共享语义、与 LocalStorage/PersistentStorage/Environment 的协同行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | AppStorage 全局存储与存储装饰器 |
| 特性编号 | Func-07-02-03-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | @StorageLink/@StorageProp/AppStorage 大写 API 7 起；AppStorage 小写 API 10 起（大写 API 10 废弃）；ref/setAndRef API 12 起；Map/Set/Date API 12 起；Function 编译期 ERROR API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| AppStorage | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/app_storage.ts` | — |
| AppStorage 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-appstorage.md` | — |
| 应用状态管理概述 | `docs/zh-cn/application-dev/ui/state-management/arkts-application-state-management-overview.md` | — |
| V1 应用级变量 API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | — |
| @StorageLink API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-storagelink.md` | — |
| @StorageProp API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-storageprop.md` | — |

---

## 用户故事

### US-1: AppStorage 单例与静态 API

**作为** 应用开发者,
**我想要** 用 AppStorage 的静态 API 管理应用级全局状态,
**以便** 在主线程内跨 UIAbility 共享状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 应用启动 THEN 框架创建 AppStorage 单例（`AppStorage extends LocalStorage`，`app_storage.ts:27-514`），运行期常驻内存 | 正常 |
| AC-1.2 | WHEN 主线程内多个 UIAbility 实例 THEN 共享同一 AppStorage；UIExtensionAbility 是独立进程，不共享主进程 AppStorage | 边界 |
| AC-1.3 | WHEN AppStorage 与 AppStorageV2 THEN 数据互不共享 | 边界 |
| AC-1.4 | WHEN `AppStorage.setOrCreate<T>(key, newValue)`(281-283，API 10+) THEN 不存在则创建 | 正常 |
| AC-1.5 | WHEN `AppStorage.set<T>(key, newValue)`(254-256，API 10+) THEN 仅 key 已存在时生效返回 true，否则 false | 正常 |
| AC-1.6 | WHEN `AppStorage.has`(202-204)/`get`(227-229)/`delete`(317-319)/`keys`(340-342)/`size`(364-366)/`clear`(388-390)（API 10+ 小写）THEN 语义同 LocalStorage 对应非静态方法 | 正常 |

### US-2: @StorageLink/@StorageProp 装饰器

**作为** 应用开发者,
**我想要** 用 `@StorageLink`/`@StorageProp` 建立组件变量与 AppStorage 的双向/单向同步,
**以便** 跨组件树共享全局状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `@StorageLink('key') var: T`（API 7+）装饰组件变量 THEN 经 `__createSync`(483-486) 创建双向同步（`SynchedPropertyTwoWayPU`） | 正常 |
| AC-2.2 | WHEN `@StorageProp('key') var: T`（API 7+）装饰组件变量 THEN 经 `__createSync` 创建单向同步（`SynchedPropertyOneWayPU`） | 正常 |
| AC-2.3 | WHEN 装饰变量初始化时 AppStorage 中已存在 key THEN 本地初始值被 AppStorage 值覆盖；不存在则用本地初始值在 AppStorage 创建 | 正常 |
| AC-2.4 | WHEN 装饰变量不能从父节点初始化 THEN 禁止（但可用于初始化子节点 @State/@Link/@Prop/@Provide） | 边界 |
| AC-2.5 | WHEN API 12+ THEN @StorageLink/@StorageProp 支持 Map/Set/Date/null/undefined/联合类型 | 正常 |
| AC-2.6 | WHEN API 23+ 装饰 Function 类型变量 THEN 编译期 ERROR | 异常 |

### US-3: link/prop/ref 静态方法

**作为** 应用开发者,
**我想要** 用 AppStorage 静态 `link`/`prop`/`ref` 方法获取 `SubscribedAbstractProperty`/`AbstractProperty` 句柄,
**以便** 在非装饰器场景命令式建立同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `AppStorage.link<T>(key)`(91-93，API 10+) THEN 返回 `SubscribedAbstractProperty<T>`（双向） | 正常 |
| AC-3.2 | WHEN `AppStorage.prop<T>(key)`(147-149，API 10+) THEN 返回 `SubscribedAbstractProperty<T>`（单向） | 正常 |
| AC-3.3 | WHEN `AppStorage.setAndLink<T>`(120-122)/`setAndProp<S>`(176-178)（API 10+）THEN 若 key 不存在用 defaultValue 创建后 link/prop | 正常 |
| AC-3.4 | WHEN `AppStorage.ref<T>`(54-56，API 12+) THEN 返回 `AbstractProperty<T>`（双向自动释放） | 正常 |

### US-4: 同值优化与 delete 订阅者保护

**作为** 应用开发者,
**我想要** 了解 set/setOrCreate 的同值优化与 delete 的订阅者保护,
**以便** 避免冗余刷新与悬挂引用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `set`/`setOrCreate` 新值与旧值相等 THEN 不会通知 @StorageLink/@StorageProp 更新 | 边界 |
| AC-4.2 | WHEN `delete(key)`(317-319) THEN 仅当该 key 无订阅者时成功；订阅者包括 @StorageLink/@StorageProp 装饰的变量以及 link/prop 返回的 SubscribedAbstractProperty 实例 | 边界 |
| AC-4.3 | WHEN 清除订阅者 THEN 删除所在自定义组件 / 调用 `SubscribedAbstractProperty.aboutToBeDeleted()`(414-416) | 边界 |
| AC-4.4 | WHEN @StorageProp 本地修改后 AppStorage 端 `setOrCreate` 同值 THEN 不同步回 @StorageProp（副本不一致陷阱） | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 单例创建 |
| AC-1.2 | US-1 | R-1 | 单元测试 多 UIAbility 共享 |
| AC-1.3 | US-1 | R-2 | 单元测试 与 V2 互不共享 |
| AC-1.4 | US-1 | R-3 | 单元测试 setOrCreate |
| AC-1.5 | US-1 | R-3 | 单元测试 set |
| AC-1.6 | US-1 | R-3 | 单元测试 CRUD |
| AC-2.1 | US-2 | R-4 | 单元测试 @StorageLink |
| AC-2.2 | US-2 | R-4 | 单元测试 @StorageProp |
| AC-2.3 | US-2 | R-4 | 单元测试 初始值 |
| AC-2.4 | US-2 | R-5 | 单元测试 不能从父初始化 |
| AC-2.5 | US-2 | R-4 | 单元测试 Map/Set/Date |
| AC-2.6 | US-2 | R-6 | 编译期校验 |
| AC-3.1 | US-3 | R-7 | 单元测试 link |
| AC-3.2 | US-3 | R-7 | 单元测试 prop |
| AC-3.3 | US-3 | R-7 | 单元测试 setAndLink/setAndProp |
| AC-3.4 | US-3 | R-7 | 单元测试 ref |
| AC-4.1 | US-4 | R-3 | 单元测试 同值优化 |
| AC-4.2 | US-4 | R-8 | 单元测试 delete 订阅者保护 |
| AC-4.3 | US-4 | R-8 | 单元测试 aboutToBeDeleted |
| AC-4.4 | US-4 | R-5 | 单元测试 副本不一致陷阱 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | AppStorage 单例创建 | 应用启动时框架创建 AppStorage 单例（`extends LocalStorage`，`app_storage.ts:27-514`），运行期常驻内存；主线程内多个 UIAbility 共享；UIExtensionAbility 独立进程不共享；与 AppStorageV2 数据互不共享 | AppStorage 是"特殊的单例 LocalStorage 对象"，所有 API 均为静态方法 | AC-1.1~AC-1.3 |
| R-2 | 边界 | AppStorage 与 AppStorageV2 隔离 | 数据互不共享；AppStorage 是 V1 范式，AppStorageV2 是 V2 范式（Feat-07 of 07-02-02） | — | AC-1.3 |
| R-3 | 行为 | AppStorage 静态 CRUD（小写 API 10+） | `setOrCreate`(281-283) 不存在则创建；`set`(254-256) 仅 key 已存在时生效返回 true，同值不触发刷新；`has`(202-204)/`get`(227-229)/`delete`(317-319)/`keys`(340-342)/`size`(364-366)/`clear`(388-390) 语义同 LocalStorage | 大写 API（7→10 废弃）为别名 | AC-1.4~AC-1.6, AC-4.1 |
| R-4 | 行为 | @StorageLink/@StorageProp 装饰（API 7+） | 经 `__createSync`(483-486) 创建 `SynchedPropertyTwoWayPU`（@StorageLink 双向）/ `SynchedPropertyOneWayPU`（@StorageProp 单向）；初始化时 AppStorage 有 key 则覆盖本地，无则用本地创建；API 12+ 支持 Map/Set/Date/null/undefined/联合类型 | key 必须为字符串字面量 | AC-2.1~AC-2.3, AC-2.5 |
| R-5 | 边界 | 装饰变量初始化约束 | 不能从父节点初始化（禁止）；@StorageProp 本地修改后 AppStorage 端 setOrCreate 同值不同步回 @StorageProp（副本不一致陷阱） | 不支持组件外访问 | AC-2.4, AC-4.4 |
| R-6 | 异常 | 装饰 Function 类型（API 23+） | API 23+ Function 类型编译期 ERROR | Function 不支持 | AC-2.6 |
| R-7 | 行为 | AppStorage 静态 link/prop/setAndLink/setAndProp/ref | `link<T>`(91-93)/`setAndLink`(120-122)（API 10+）双向；`prop<T>`(147-149)/`setAndProp`(176-178)（API 10+）单向；`ref<T>`(54-56)（API 12+）双向自动释放 | 静态方法委托到内部单例 LocalStorage | AC-3.1~AC-3.4 |
| R-8 | 边界 | delete 订阅者保护 | `delete`(317-319) 仅当 key 无订阅者时成功；订阅者包括 @StorageLink/@StorageProp 装饰变量、link/prop 返回的 SubscribedAbstractProperty；需 `aboutToBeDeleted`(414-416) 释放 | 订阅者保护避免悬挂引用 | AC-4.2, AC-4.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 代码审查 | `app_storage.ts:27-514` 单例创建 |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` 多 UIAbility 共享 |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` 与 V2 互不共享 |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` setOrCreate |
| VM-5 | AC-1.5 | 单元测试 | `common_tests/` set |
| VM-6 | AC-1.6 | 单元测试 | `common_tests/` CRUD |
| VM-7 | AC-2.1 | 单元测试 | `common_tests/` @StorageLink |
| VM-8 | AC-2.2 | 单元测试 | `common_tests/` @StorageProp |
| VM-9 | AC-2.3 | 单元测试 | `common_tests/` 初始值 |
| VM-10 | AC-2.4 | 单元测试 | `common_tests/` 不能从父初始化 |
| VM-11 | AC-2.5 | 单元测试 | `common_tests/` Map/Set/Date |
| VM-12 | AC-2.6 | 编译期校验 | ArkTS 编译器 Function ERROR |
| VM-13 | AC-3.1 | 单元测试 | `common_tests/` link |
| VM-14 | AC-3.2 | 单元测试 | `common_tests/` prop |
| VM-15 | AC-3.3 | 单元测试 | `common_tests/` setAndLink/setAndProp |
| VM-16 | AC-3.4 | 单元测试 | `common_tests/` ref |
| VM-17 | AC-4.1 | 单元测试 | `common_tests/` 同值优化 |
| VM-18 | AC-4.2 | 单元测试 | `common_tests/` delete 订阅者保护 |
| VM-19 | AC-4.3 | 单元测试 | `common_tests/` aboutToBeDeleted |
| VM-20 | AC-4.4 | 单元测试 | `common_tests/` 副本不一致陷阱 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `AppStorage` | `sdk/app_storage.ts:27-514` | 应用级全局单例（extends LocalStorage） |
| `createSingleton` | `sdk/app_storage.ts:35-42` | 单例创建 |
| `setOrCreate`/`set` | `sdk/app_storage.ts:281-283/254-256` | 静态 CRUD |
| `link`/`prop`/`setAndLink`/`setAndProp` | `sdk/app_storage.ts:91-178` | 静态同步方法 |
| `ref`/`setAndRef` | `sdk/app_storage.ts:54-73` | 静态自动释放（API 12+） |
| `__createSync` | `sdk/app_storage.ts:483-486` | @StorageLink/@StorageProp 工厂 |
| `instance_` | `sdk/app_storage.ts:491` | 静态私有单例字段 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | AppStorage 大写静态 API + @StorageLink/@StorageProp 引入 | 全局存储 | 无需迁移 |
| API 10 | 小写静态 API 引入（大写废弃） | API 风格统一 | 改用小写 API |
| API 12 | ref/setAndRef 引入；Map/Set/Date/null/undefined/联合类型 | 自动释放+更多类型 | 无需迁移 |
| API 23 | Function 类型编译期 ERROR | 类型校验加强 | 移除 Function 类型 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 全局单例 | AppStorage 是应用启动时框架创建的单例，主线程内多 UIAbility 共享；UIExtensionAbility 不共享 |
| 继承 LocalStorage | AppStorage extends LocalStorage，所有 API 为静态方法委托到内部单例 |
| 订阅者保护 | delete/clear 仅在无订阅者时成功 |
| 同值优化 | set/setOrCreate 同值不触发刷新 |
| 与 V2 隔离 | AppStorage 与 AppStorageV2 数据互不共享 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/app_storage.ts:27-514` | `AppStorage` 全局单例 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/app_storage.ts:35-42` | `createSingleton` 单例创建 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/app_storage.ts:254-390` | 静态 CRUD（set/setOrCreate/has/get/delete/keys/size/clear） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/app_storage.ts:91-178` | 静态 link/prop/setAndLink/setAndProp |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/app_storage.ts:54-73` | 静态 ref/setAndRef（API 12+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/app_storage.ts:483-486` | `__createSync` @StorageLink/@StorageProp 工厂 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | AppStorage 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-appstorage.md` | AppStorage 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | V1 应用级变量 API 参考 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-storagelink.md` | @StorageLink API |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management-storageprop.md` | @StorageProp API |
