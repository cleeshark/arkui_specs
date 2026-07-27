# 特性规格

> Func-07-02-03-Feat-03 PersistentStorage 磁盘持久化：固化 `PersistentStorage`（`implements IMultiPropertiesChangeSubscriber`，`sdk/persistent_storage.ts:158-482`）的 `persistProp` 决策链（先 AppStorage.link；不在则查磁盘→读或默认→setAndLink）、Map/Set/Date 序列化（`MapInfo`/`SetInfo`/`DateInfo` + `replacer`）、`IStorage` 后端（`write()` 写所有属性）、嵌套对象手动 `notifyHasChanged`、module 级存储路径行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | PersistentStorage 磁盘持久化 |
| 特性编号 | Func-07-02-03-Feat-03 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | 大写 API（`PersistProp`/`DeleteProp`/`PersistProps`/`Keys`）API 7 起 API 10 废弃；小写 API 10 起；Map/Set/Date/null/undefined/联合类型 API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| PersistentStorage | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/persistent_storage.ts` | — |
| IStorage 接口 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/i_storage.ts` | — |
| PersistentStorage 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-persiststorage.md` | — |
| V1 应用级变量 API | `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | — |

---

## 用户故事

### US-1: persistProp 决策链

**作为** 应用开发者,
**我想要** 用 `persistProp` 建立磁盘持久化,
**以便** 应用退出再启动后恢复状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `persistProp<T>(key, defaultValue)`(216-218，API 10+) THEN 触发 `persistProp1`(358-392) 决策链 | 正常 |
| AC-1.2 | WHEN PersistentStorage 文件中存在 key THEN 在 AppStorage 中创建对应 key，用磁盘值初始化 | 正常 |
| AC-1.3 | WHEN 文件中无 key 但 AppStorage 已有 THEN 将该属性持久化，用 AppStorage 当前值覆盖磁盘值 | 正常 |
| AC-1.4 | WHEN 文件与 AppStorage 都无 THEN 在 AppStorage 中用 defaultValue 创建并持久化 | 正常 |
| AC-1.5 | WHEN persistProp 必须在 UI 实例初始化成功后调用 THEN 即在 `windowStage.loadContent` 回调后；否则持久化失败 | 边界 |
| AC-1.6 | WHEN persistProp 在访问 AppStorage 同名 key 之后调用 THEN 用 AppStorage 值覆盖磁盘值（推荐先 persistProp 后访问 AppStorage） | 边界 |

### US-2: 持久化方向与 IStorage 后端

**作为** 应用开发者,
**我想要** 了解持久化方向（AppStorage ⇄ 磁盘）与 IStorage 后端语义,
**以便** 正确配置持久化后端。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN UI/业务逻辑访问持久化数据 THEN 不直接访问 PersistentStorage，所有读写经 AppStorage | 正常 |
| AC-2.2 | WHEN AppStorage 中已持久化 key 变化 THEN 自动同步写回磁盘 | 正常 |
| AC-2.3 | WHEN `IStorage.write()` THEN 写所有属性（不支持增量更新） | 边界 |
| AC-2.4 | WHEN `configureBackend(storage)`(173-175) THEN 配置 IStorage 后端（内部启动钩子） | 正常 |

### US-3: Map/Set/Date 序列化

**作为** 应用开发者,
**我想要** 了解 Map/Set/Date 类型的持久化序列化机制,
**以便** 正确持久化复杂类型。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN API 12+ 持久化 Map THEN 观察 `set`/`clear`/`delete` + 整体赋值；经 `MapInfo`(35-75) 序列化 | 正常 |
| AC-3.2 | WHEN API 12+ 持久化 Set THEN 观察 `add`/`clear`/`delete` + 整体赋值；经 `SetInfo`(83-112) 序列化 | 正常 |
| AC-3.3 | WHEN API 12+ 持久化 Date THEN 观察 14 个 setter + 整体赋值；经 `DateInfo`(120-148) 序列化 | 正常 |
| AC-3.4 | WHEN 序列化 THEN `replacer` 检测 NewVersion/CompatibleVersion 标记 | 正常 |
| AC-3.5 | WHEN 持久化文件存储对象 THEN 不存储对象的方法（只存可被 JSON.stringify/parse 重构的数据） | 边界 |

### US-4: 嵌套对象与 deleteProp

**作为** 应用开发者,
**我想要** 了解嵌套对象持久化限制与 deleteProp,
**以便** 避免持久化失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 持久化嵌套对象（对象数组、属性为对象的对象）THEN 框架无法检测嵌套变化并写回；需手动 `notifyHasChanged('data')`(315-320) | 边界 |
| AC-4.2 | WHEN 调用 `deleteProp(key)`(235-237，API 10+) THEN 删除持久化 key | 正常 |
| AC-4.3 | WHEN 调用 `persistProps(props)`(257-262，API 10+) THEN 批量持久化 | 正常 |
| AC-4.4 | WHEN module 级存储路径 THEN 哪个 module 调用 persistProp 就存到哪个 module 的持久化文件；多 module 同 key 数据归属最先使用 PersistentStorage 的 module | 边界 |
| AC-4.5 | WHEN 持久化建议数据 < 2kb 且写盘在 UI 线程同步执行 THEN 频繁变化或大型数据集影响 UI 性能，建议改用 relationalStore | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 persistProp |
| AC-1.2 | US-1 | R-1 | 单元测试 磁盘有 key |
| AC-1.3 | US-1 | R-1 | 单元测试 AppStorage 有 key |
| AC-1.4 | US-1 | R-1 | 单元测试 都无 key |
| AC-1.5 | US-1 | R-2 | 单元测试 UI 初始化约束 |
| AC-1.6 | US-1 | R-1 | 单元测试 顺序陷阱 |
| AC-2.1 | US-2 | R-3 | 单元测试 经 AppStorage |
| AC-2.2 | US-2 | R-3 | 单元测试 自动写回 |
| AC-2.3 | US-2 | R-4 | 代码审查 write 写所有 |
| AC-2.4 | US-2 | R-4 | 代码审查 configureBackend |
| AC-3.1 | US-3 | R-5 | 单元测试 Map 序列化 |
| AC-3.2 | US-3 | R-5 | 单元测试 Set 序列化 |
| AC-3.3 | US-3 | R-5 | 单元测试 Date 序列化 |
| AC-3.4 | US-3 | R-5 | 代码审查 replacer |
| AC-3.5 | US-3 | R-5 | 单元测试 不存储方法 |
| AC-4.1 | US-4 | R-6 | 单元测试 嵌套手动通知 |
| AC-4.2 | US-4 | R-7 | 单元测试 deleteProp |
| AC-4.3 | US-4 | R-7 | 单元测试 persistProps |
| AC-4.4 | US-4 | R-2 | 单元测试 module 级路径 |
| AC-4.5 | US-4 | R-2 | 代码审查 性能约束 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `persistProp<T>(key, defaultValue)`(216-218，API 10+) | 触发 `persistProp1`(358-392) 决策链：①文件有 key → AppStorage 创建用磁盘值；②文件无 AppStorage 有 → 持久化用 AppStorage 值覆盖磁盘；③都无 → AppStorage 用 defaultValue 创建并持久化；若在访问 AppStorage 同名 key 之后调用会用 AppStorage 值覆盖磁盘值 | 推荐先 persistProp 后访问 AppStorage | AC-1.1~AC-1.4, AC-1.6 |
| R-2 | 边界 | persistProp 调用时机与路径 | 必须在 UI 实例初始化成功后调用（`windowStage.loadContent` 回调后）；module 级存储路径（哪个 module 调用存哪个 module 文件）；建议数据 < 2kb（写盘在 UI 线程同步执行） | 频繁变化或大型数据用 relationalStore | AC-1.5, AC-4.4, AC-4.5 |
| R-3 | 行为 | 持久化方向 | UI/业务逻辑不直接访问 PersistentStorage，所有读写经 AppStorage；AppStorage 已持久化 key 变化自动同步写回磁盘；双向同步链 `AppStorage ⇄ PersistentStorage(磁盘)` | — | AC-2.1, AC-2.2 |
| R-4 | 行为 | `IStorage` 后端 | `configureBackend(storage)`(173-175) 配置后端；`write()` 写所有属性（不支持增量更新）；`writeToPersistentStorage`(423-433)/`readFromPersistentStorage`(437-452) 读写实现 | — | AC-2.3, AC-2.4 |
| R-5 | 行为 | Map/Set/Date 序列化（API 12+） | Map 经 `MapInfo`(35-75) 观察 `set`/`clear`/`delete`；Set 经 `SetInfo`(83-112) 观察 `add`/`clear`/`delete`；Date 经 `DateInfo`(120-148) 观察 14 个 setter；`replacer` 检测 NewVersion/CompatibleVersion；持久化文件不存储对象方法（只存可被 JSON 重构的数据） | API 12+ | AC-3.1~AC-3.5 |
| R-6 | 边界 | 嵌套对象持久化 | 框架无法检测嵌套对象（对象数组、属性为对象的对象）变化并写回；需手动 `notifyHasChanged('data')`(315-320) | 不支持嵌套对象自动持久化 | AC-4.1 |
| R-7 | 行为 | deleteProp/persistProps | `deleteProp(key)`(235-237，API 10+) 删除持久化 key；`persistProps(props)`(257-262，API 10+) 批量持久化 | — | AC-4.2, AC-4.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `common_tests/` persistProp |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` 磁盘有 key |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` AppStorage 有 key |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` 都无 key |
| VM-5 | AC-1.5 | 单元测试 | `common_tests/` UI 初始化约束 |
| VM-6 | AC-1.6 | 单元测试 | `common_tests/` 顺序陷阱 |
| VM-7 | AC-2.1 | 单元测试 | `common_tests/` 经 AppStorage |
| VM-8 | AC-2.2 | 单元测试 | `common_tests/` 自动写回 |
| VM-9 | AC-2.3 | 代码审查 | `i_storage.ts` write 写所有 |
| VM-10 | AC-2.4 | 代码审查 | `persistent_storage.ts:173-175` configureBackend |
| VM-11 | AC-3.1 | 单元测试 | `common_tests/` Map 序列化 |
| VM-12 | AC-3.2 | 单元测试 | `common_tests/` Set 序列化 |
| VM-13 | AC-3.3 | 单元测试 | `common_tests/` Date 序列化 |
| VM-14 | AC-3.4 | 代码审查 | `persistent_storage.ts` replacer |
| VM-15 | AC-3.5 | 单元测试 | `common_tests/` 不存储方法 |
| VM-16 | AC-4.1 | 单元测试 | `common_tests/` 嵌套手动通知 |
| VM-17 | AC-4.2 | 单元测试 | `common_tests/` deleteProp |
| VM-18 | AC-4.3 | 单元测试 | `common_tests/` persistProps |
| VM-19 | AC-4.4 | 单元测试 | `common_tests/` module 级路径 |
| VM-20 | AC-4.5 | 代码审查 | 性能约束 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `PersistentStorage` | `sdk/persistent_storage.ts:158-482` | 磁盘持久化（implements IMultiPropertiesChangeSubscriber） |
| `persistProp`/`persistProp1` | `sdk/persistent_storage.ts:216-218/358-392` | 持久化决策链 |
| `MapInfo`/`SetInfo`/`DateInfo` | `sdk/persistent_storage.ts:35-75/83-112/120-148` | Map/Set/Date 序列化辅助 |
| `writeToPersistentStorage`/`readFromPersistentStorage` | `sdk/persistent_storage.ts:423-433/437-452` | 读写磁盘 |
| `notifyHasChanged` | `sdk/persistent_storage.ts:315-320` | 嵌套对象手动通知 |
| `configureBackend` | `sdk/persistent_storage.ts:173-175` | 配置 IStorage 后端 |
| `deleteProp`/`persistProps`/`keys` | `sdk/persistent_storage.ts:235-292` | 删除/批量/查询 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | 大写 API（PersistProp/DeleteProp/PersistProps/Keys）引入 | 磁盘持久化 | 无需迁移 |
| API 10 | 小写 API 引入（大写废弃） | API 风格统一 | 改用小写 API |
| API 12 | Map/Set/Date/null/undefined/联合类型；defaultValue 可 null/undefined | 更多类型 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 经 AppStorage 中转 | UI/业务逻辑不直接访问 PersistentStorage，所有读写经 AppStorage |
| IStorage 不支持增量 | `write()` 写所有属性；后端不支持增量更新 |
| 嵌套对象需手动通知 | 嵌套对象变化需手动 `notifyHasChanged`；不支持自动嵌套持久化 |
| module 级存储路径 | 多 module 同 key 数据归属最先使用 PersistentStorage 的 module |
| 必须在 UI 初始化后 | persistProp 必须在 `windowStage.loadContent` 回调后调用 |
| 性能约束 | 建议 < 2kb；写盘在 UI 线程同步；频繁变化或大型数据用 relationalStore |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/persistent_storage.ts:158-482` | `PersistentStorage` 磁盘持久化 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/persistent_storage.ts:358-392` | `persistProp1` 决策链 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/persistent_storage.ts:35-148` | `MapInfo`/`SetInfo`/`DateInfo` 序列化辅助 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/persistent_storage.ts:423-452` | `writeToPersistentStorage`/`readFromPersistentStorage` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/persistent_storage.ts:315-320` | `notifyHasChanged` 嵌套手动通知 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/persistent_storage.ts:173-175` | `configureBackend` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/i_storage.ts` | `IStorage` 接口 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | PersistentStorage 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-persiststorage.md` | PersistentStorage 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-state-management.md` | V1 应用级变量 API 参考 |
