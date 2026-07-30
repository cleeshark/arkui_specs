# 特性规格

> Func-07-02-06-Feat-01 AppStorageV2 内存全局存储：固化 `AppStorageV2`（`AppStorageV2Impl extends StorageHelper`，`sdk/v2_persistence.ts:167-277`，单例）的 `connect`/`remove`/`keys`（API 12+）、typeKey 机制、仅 class 类型约束、`@Trace` 属性自动刷新、与 AppStorage 数据隔离行为规格与错误码 140103/140104/140107/140116。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | AppStorageV2 内存全局存储 |
| 特性编号 | Func-07-02-06-Feat-01 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P1 |
| 目标版本 | connect/remove/keys API 12 起；错误码 140103 由运行时报错改为返回码 API 23 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/04-v2-component-state/design.md` | Draft |
| AppStorageV2Impl | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts` | — |
| AppStorageV2 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-appstoragev2.md` | — |
| StateManagement 模块 | `docs/zh-cn/application-dev/reference/apis-arkui/js-apis-stateManagement.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: connect 连接与 typeKey 机制

**作为** 应用开发者,
**我想要** 用 `AppStorageV2.connect` 连接或创建全局存储的 class 实例,
**以便** 跨组件树共享 V2 状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `AppStorageV2.connect<T>(type, keyOrDefaultCreator?, defaultCreator?)`(185-217，API 12+) THEN 返回内存中 class 实例；首次 connect 必须 defaultCreator | 正常 |
| AC-1.2 | WHEN 未指定 key THEN 使用 `type` 的 name 作为 typeKey | 正常 |
| AC-1.3 | WHEN 同一 typeKey connect 不同类型 THEN 导致应用异常；key 建议字母/数字/下划线，长度 ≤ 255 | 边界 |
| AC-1.4 | WHEN 第一次 connect 某 key 未提供 defaultCreator THEN 返回 undefined 导致应用异常 | 异常 |
| AC-1.5 | WHEN 数据已存后再 connect THEN 可省略 defaultCreator | 边界 |
| AC-1.6 | WHEN connect 仅支持 class 类型 THEN 非 class 类型（基本类型/Native 类型）不支持；API 23+ 返回错误码 140103 | 异常 |

### US-2: @Trace 属性自动刷新

**作为** 应用开发者,
**我想要** connect 返回的 class 实例的 @Trace 属性变化自动触发 UI 刷新,
**以便** V2 范式的响应式存储。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN connect 返回的实例 `@Trace` 属性变化 THEN 触发 UI 刷新（经 ObserveV2 依赖图） | 正常 |
| AC-2.2 | WHEN 非 `@Trace` 属性变化 THEN 已同步回 AppStorageV2 但不刷新 UI | 边界 |
| AC-2.3 | WHEN AppStorageV2 实例需配合 `@ObservedV2`/`@Trace` + `@ComponentV2`/`@Local`/`@Param` 使用 THEN V2 范式联动 | 正常 |

### US-3: remove/keys 与进程级共享

**作为** 应用开发者,
**我想要** 用 `remove`/`keys` 管理 AppStorageV2 存储,
**以便** 清理与查询全局状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `AppStorageV2.remove<T>(keyOrType)`(219-232，API 12+) THEN 删除指定 key；**不影响**组件中已创建的数据副本 | 正常 |
| AC-3.2 | WHEN remove 删除不存在的 key THEN 会报警告 | 边界 |
| AC-3.3 | WHEN remove 后再 connect 同名 key THEN 得到新对象，父子组件之间失去同步 | 边界 |
| AC-3.4 | WHEN `AppStorageV2.keys()`(234-236，API 12+) THEN 返回所有 key，顺序无序 | 正常 |
| AC-3.5 | WHEN AppStorageV2 在应用 UI 启动时创建，主线程内多 UIAbility 共享 THEN 进程级共享 | 边界 |
| AC-3.6 | WHEN AppStorageV2 与 AppStorage THEN 数据互不共享 | 边界 |
| AC-3.7 | WHEN AppStorageV2 不支持 UIContext 隔离 THEN 全局扁平 Map；需 `@Env`/`@CustomEnv` 按 instanceId 隔离 | 边界 |

### US-4: 错误码

**作为** 应用开发者,
**我想要** 明确 connect/remove 的错误码,
**以便** 排查问题。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN connect type 非 `TypeConstructorWithArgs<T>` THEN API 23+ 返回错误码 140103 | 异常 |
| AC-4.2 | WHEN 首次 connect defaultCreator 不是 `StorageDefaultCreator<T>` THEN 错误码 140104 | 异常 |
| AC-4.3 | WHEN type 类型与 defaultCreator 返回类型不一致 THEN 错误码 140107（仅日志上报） | 异常 |
| AC-4.4 | WHEN remove key 不是 string 或 `TypeConstructorWithArgs<T>` THEN 错误码 140116 | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 connect |
| AC-1.2 | US-1 | R-1 | 单元测试 typeKey |
| AC-1.3 | US-1 | R-1 | 单元测试 key 规范 |
| AC-1.4 | US-1 | R-2 | 单元测试 缺 defaultCreator |
| AC-1.5 | US-1 | R-1 | 单元测试 可省略 |
| AC-1.6 | US-1 | R-3 | 单元测试 仅 class |
| AC-2.1 | US-2 | R-4 | 单元测试 @Trace 刷新 |
| AC-2.2 | US-2 | R-4 | 单元测试 非 @Trace 不刷新 |
| AC-2.3 | US-2 | R-4 | 单元测试 V2 联动 |
| AC-3.1 | US-3 | R-5 | 单元测试 remove |
| AC-3.2 | US-3 | R-5 | 单元测试 不存在警告 |
| AC-3.3 | US-3 | R-5 | 单元测试 remove 后新对象 |
| AC-3.4 | US-3 | R-5 | 单元测试 keys |
| AC-3.5 | US-3 | R-6 | 单元测试 进程级共享 |
| AC-3.6 | US-3 | R-6 | 单元测试 与 AppStorage 隔离 |
| AC-3.7 | US-3 | R-6 | 单元测试 不支持 UIContext 隔离 |
| AC-4.1 | US-4 | R-3 | 单元测试 错误码 140103 |
| AC-4.2 | US-4 | R-2 | 单元测试 错误码 140104 |
| AC-4.3 | US-4 | R-7 | 单元测试 错误码 140107 |
| AC-4.4 | US-4 | R-5 | 单元测试 错误码 140116 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `connect<T>(type, keyOrDefaultCreator?, defaultCreator?)`(185-217，API 12+) | 返回内存中 class 实例；首次 connect 必须 defaultCreator（否则返回 undefined）；未指定 key 用 type 的 name 作 typeKey；同一 typeKey connect 不同类型导致异常；数据已存后可省略 defaultCreator；key 建议字母/数字/下划线，长度 ≤ 255 | 仅 class 类型 | AC-1.1~AC-1.5 |
| R-2 | 异常 | 首次 connect 缺 defaultCreator 或 defaultCreator 类型错误 | 首次 connect 缺 defaultCreator 返回 undefined 导致应用异常；defaultCreator 不是 `StorageDefaultCreator<T>` 返回错误码 140104 | — | AC-1.4, AC-4.2 |
| R-3 | 异常 | connect type 非 class 类型 | 非 class 类型（基本类型/Native 类型）不支持；API 23+ 返回错误码 140103（`Not supported type!`） | 仅 class 类型 | AC-1.6, AC-4.1 |
| R-4 | 行为 | connect 返回实例的 @Trace 属性变化 | `@Trace` 属性变化触发 UI 刷新（经 ObserveV2 依赖图自动追踪）；非 @Trace 属性变化已同步回 AppStorageV2 但不刷新 UI；需配合 @ObservedV2/@Trace + @ComponentV2/@Local/@Param | V2 范式联动 | AC-2.1~AC-2.3 |
| R-5 | 行为 | `remove<T>(keyOrType)`(219-232，API 12+) / `keys()`(234-236) | `remove` 删除指定 key，**不影响**组件中已创建的数据副本；删除不存在 key 报警告；remove 后再 connect 得到新对象失去同步；`keys` 返回所有 key 顺序无序；remove key 不是 string/TypeConstructor 返回 140116 | — | AC-3.1~AC-3.4, AC-4.4 |
| R-6 | 边界 | AppStorageV2 共享范围 | 应用 UI 启动时创建，主线程内多 UIAbility 共享；与 AppStorage 数据互不共享；不支持 UIContext 隔离（全局扁平 Map），需 @Env/@CustomEnv 按 instanceId 隔离 | — | AC-3.5~AC-3.7 |
| R-7 | 异常 | type 类型与 defaultCreator 返回类型不一致 | 错误码 140107（`The type of target mismatches the type of source.`，仅日志上报不抛异常） | — | AC-4.3 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` connect |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` typeKey |
| VM-3 | AC-1.3 | 单元测试 | `v2_tests/` key 规范 |
| VM-4 | AC-1.4 | 单元测试 | `v2_tests/` 缺 defaultCreator |
| VM-5 | AC-1.5 | 单元测试 | `v2_tests/` 可省略 |
| VM-6 | AC-1.6 | 单元测试 | `v2_tests/` 仅 class |
| VM-7 | AC-2.1 | 单元测试 | `v2_tests/` @Trace 刷新 |
| VM-8 | AC-2.2 | 单元测试 | `v2_tests/` 非 @Trace 不刷新 |
| VM-9 | AC-2.3 | 单元测试 | `v2_tests/` V2 联动 |
| VM-10 | AC-3.1 | 单元测试 | `v2_tests/` remove |
| VM-11 | AC-3.2 | 单元测试 | `v2_tests/` 不存在警告 |
| VM-12 | AC-3.3 | 单元测试 | `v2_tests/` remove 后新对象 |
| VM-13 | AC-3.4 | 单元测试 | `v2_tests/` keys |
| VM-14 | AC-3.5 | 单元测试 | `v2_tests/` 进程级共享 |
| VM-15 | AC-3.6 | 单元测试 | `v2_tests/` 与 AppStorage 隔离 |
| VM-16 | AC-3.7 | 单元测试 | `v2_tests/` 不支持 UIContext 隔离 |
| VM-17 | AC-4.1 | 单元测试 | `v2_tests/` 错误码 140103 |
| VM-18 | AC-4.2 | 单元测试 | `v2_tests/` 错误码 140104 |
| VM-19 | AC-4.3 | 单元测试 | `v2_tests/` 错误码 140107 |
| VM-20 | AC-4.4 | 单元测试 | `v2_tests/` 错误码 140116 |

---

## 错误码规格

| 错误码 | 触发条件 | 错误信息 | 起始版本 |
|--------|----------|----------|----------|
| 140103 | connect type 非 `TypeConstructorWithArgs<T>` | `Not supported type!` | API 23 起返回码 |
| 140104 | 首次 connect defaultCreator 不是 `StorageDefaultCreator<T>` | `The default creator should be function when first connect.` | API 12 |
| 140107 | type 类型与 defaultCreator 返回类型不一致 | `The type of target mismatches the type of source.` | API 12（仅日志） |
| 140116 | remove key 不是 string 或 `TypeConstructorWithArgs<T>` | `The key is invalid` | API 12 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `AppStorageV2Impl extends StorageHelper` | `sdk/v2_persistence.ts:167-277` | V2 全局存储单例 |
| `instance()` | `sdk/v2_persistence.ts:177-183` | 单例获取 |
| `connect<T>` | `sdk/v2_persistence.ts:185-217` | 连接/创建 class 实例 |
| `remove<T>` | `sdk/v2_persistence.ts:219-232` | 删除 key |
| `keys()` | `sdk/v2_persistence.ts:234-236` | 查询所有 key |
| `StorageHelper` | `sdk/v2_persistence.ts:70-165` | 基类（key 校验 `isKeyValid`） |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 12 | AppStorageV2.connect/remove/keys 引入 | V2 全局存储 | V1 AppStorage→AppStorageV2 |
| API 23 | connect type 非 class 从运行时报错改为返回错误码 140103 | 错误码规范化 | 处理新增错误码 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 仅 class 类型 | connect 仅支持 class 类型；基本类型/Native 类型不支持 |
| typeKey 机制 | 未指定 key 用 type 的 name；同一 typeKey 不同类型冲突 |
| @Trace 自动刷新 | @Trace 属性变化触发 UI 刷新；非 @Trace 不刷新 |
| 与 AppStorage 隔离 | AppStorageV2 与 AppStorage 数据互不共享 |
| 不支持 UIContext 隔离 | 全局扁平 Map；需 @Env/@CustomEnv 按 instanceId 隔离 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:167-277` | `AppStorageV2Impl` V2 全局存储 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:185-217` | `connect` 连接/创建 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:219-232` | `remove` |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/v2_persistence.ts:70-165` | `StorageHelper` 基类 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | AppStorageV2 行为回归测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-appstoragev2.md` | AppStorageV2 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/js-apis-stateManagement.md` | StateManagement 模块 |
| `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | 错误码 140103/140104/140107/140116 |
