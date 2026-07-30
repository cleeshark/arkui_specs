# 特性规格

> Func-07-02-01-Feat-08 状态管理调试与渲染基础设施：固化 `stateMgmtConsole`/`stateMgmtTrace`/`errorReport`（日志门面，`limitLog` 20s 去重）、`stateMgmtDFX`/`DumpInfo`/`getStateMgmtInfo`（Inspector 查询，2000ms 超时，`getElementName` ID 区间映射）、`stateMgmtProfiler`（性能采集，C++ 注入）、`UpdateFuncRecord`/`UpdateFuncsByElmtId`（update-function 记录，If/Else `isPending`/`isChanged`）行为规格。这些是 V1/V2 共享的调试、诊断与渲染记录基础设施，归 V1 域统一管理。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 状态管理调试与渲染基础设施 |
| 特性编号 | Func-07-02-01-Feat-08 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P2 |
| 目标版本 | API 7 起（核心机制）；`stateMgmt.setPropertyAccessTrace` V2 属性访问追踪 API 12 起 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/02-state-management/01-v1-component-state/design.md` | Draft |
| stateMgmtConsole | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_console_trace.ts` | — |
| stateMgmtDFX | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_dfx.ts` | — |
| stateMgmtProfiler | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_profiler.ts` | — |
| UpdateFuncRecord | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_updatefunc.ts` | — |
| 状态管理原理介绍 | `docs/zh-cn/application-dev/ui/state-management/arkts-state-management-introduce.md` | — |

---

## 用户故事

### US-1: stateMgmtConsole 日志门面与 limitLog 去重

**作为** 框架维护者,
**我想要** 统一的日志门面控制状态管理子系统输出，并通过 `limitLog` 20s 去重窗口避免日志洪泛,
**以便** 排查问题时不被重复日志淹没。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 状态管理子系统输出日志 THEN 统一走 `stateMgmtConsole`(28)/`stateMgmtTrace`(128)/`errorReport`，TAG 为 `LogTag.STATE_MGMT = 0` | 正常 |
| AC-1.2 | WHEN `frequentApplicationError(msg)`(85) 调用 THEN 经 `limitLog`(64) 20s 去重窗口处理，相同 msg 20s 内只输出一次 | 正常 |
| AC-1.3 | WHEN `applicationError(msg)` 调用 THEN 每次都输出（无去重） | 正常 |
| AC-1.4 | WHEN `errorLogFrequency.size` 超过 `MAX_LOG_TYPES=3000`(35) THEN 跳过去重直接输出避免内存溢出 | 边界 |

### US-2: stateMgmtDFX 信息收集与 Inspector 查询

**作为** 应用开发者,
**我想要** 通过 `hidumper`/Inspector 查询状态管理内部信息,
**以便** 调试状态变量与依赖关系。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `getStateMgmtInfo(nodeIds, propertyName, jsonPath)` 调用 THEN 上报给 `UiSessionManager`，2000ms 超时 | 正常 |
| AC-2.2 | WHEN `getElementName(elmtId)`(194) 调用 THEN 按 ID 区间映射到 @Computed/@Monitor/PersistenceV2 名 | 正常 |
| AC-2.3 | WHEN `findViewById(id)` 查询 THEN 经 `SubscriberManager` 查找 View | 正常 |
| AC-2.4 | WHEN `DumpInfo`(338) 输出 THEN 包含组件名/ID、装饰器类型、变量名、依赖 elmtId 列表 | 正常 |

### US-3: stateMgmtProfiler 性能采集

**作为** 框架维护者,
**我想要** 通过 `stateMgmtProfiler` 采集每次变更的详细信息,
**以便** 性能分析与瓶颈定位。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `stateMgmtDFX.enableProfiler = true` THEN 每次变更输出组件名/ID、装饰器类型、变量名、依赖 elmtId 列表、sync peer 信息 | 正常 |
| AC-3.2 | WHEN `stateMgmtProfiler`(16) 实例 THEN 由 C++ 初始化时注入（`stateMgmtProfiler.init(instance)`）；未注入时为桩 | 正常 |
| AC-3.3 | WHEN V2 `stateMgmt.setPropertyAccessTrace(true)` THEN 输出详细 `addRef`/`fireChange` 日志（API 12+） | 正常 |

### US-4: UpdateFuncRecord update-function 记录

**作为** 框架维护者,
**我想要** 每 elmtId 的更新函数经 `UpdateFuncRecord`/`UpdateFuncsByElmtId` 记录管理,
**以便** dirty 元素重渲染时按 elmtId 查找对应更新函数。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 组件创建时 `observeComponentCreation2` 注册 THEN 每 elmtId 的更新函数经 `UpdateFuncRecord`(51) 记录到 `UpdateFuncsByElmtId` | 正常 |
| AC-4.2 | WHEN `UpdateFuncRecord` 持有 `updateFunc`/`classObject_`/`node` THEN 提供 `getUpdateFunc`/`getClassObject`/`getPopFunc` 访问 | 正常 |
| AC-4.3 | WHEN If/Else 分支切换 THEN `isPending_`(55)/`isChanged_`(56) 暂存变更状态 | 正常 |
| AC-4.4 | WHEN dirty 元素重渲染 THEN `updateDirtyElements` 按 elmtId 从 `UpdateFuncsByElmtId` 查找 `UpdateFuncRecord` 执行更新 | 正常 |
| AC-4.5 | WHEN `UpdateFuncRecord` 是 V1/V2 共享（`puv2_common/`）THEN `ViewPU` 与 `ViewV2` 都使用 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 统一日志门面 |
| AC-1.2 | US-1 | R-2 | 单元测试 limitLog 去重 |
| AC-1.3 | US-1 | R-2 | 单元测试 applicationError |
| AC-1.4 | US-1 | R-2 | 单元测试 MAX_LOG_TYPES |
| AC-2.1 | US-2 | R-3 | 单元测试 getStateMgmtInfo |
| AC-2.2 | US-2 | R-3 | 代码审查 getElementName 映射 |
| AC-2.3 | US-2 | R-3 | 单元测试 findViewById |
| AC-2.4 | US-2 | R-3 | 单元测试 DumpInfo |
| AC-3.1 | US-3 | R-4 | 单元测试 enableProfiler |
| AC-3.2 | US-3 | R-4 | 代码审查 C++ 注入 |
| AC-3.3 | US-3 | R-4 | 单元测试 setPropertyAccessTrace |
| AC-4.1 | US-4 | R-5 | 单元测试 UpdateFuncRecord 注册 |
| AC-4.2 | US-4 | R-5 | 单元测试 访问方法 |
| AC-4.3 | US-4 | R-5 | 单元测试 isPending/isChanged |
| AC-4.4 | US-4 | R-5 | 单元测试 dirty 查找 |
| AC-4.5 | US-4 | R-5 | 代码审查 V1/V2 共享 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 状态管理子系统日志输出 | 统一走 `stateMgmtConsole`(28)/`stateMgmtTrace`(128)/`errorReport`，TAG `LogTag.STATE_MGMT = 0` | — | AC-1.1 |
| R-2 | 行为 | `frequentApplicationError`(85)/`applicationError` 调用 | `frequentApplicationError` 经 `limitLog`(64) 20s 去重窗口处理，相同 msg 20s 内只输出一次；`applicationError` 每次输出（无去重）；`errorLogFrequency.size` 超过 `MAX_LOG_TYPES=3000`(35) 跳过去重直接输出避免内存溢出 | limitLog 防洪泛 | AC-1.2~AC-1.4 |
| R-3 | 行为 | `getStateMgmtInfo`/`getElementName`/`findViewById` 查询 | `getStateMgmtInfo(nodeIds, propertyName, jsonPath)` 上报给 `UiSessionManager`（2000ms 超时）；`getElementName(elmtId)`(194) 按 ID 区间映射到 @Computed/@Monitor/PersistenceV2 名；`findViewById(id)` 经 `SubscriberManager` 查找 View；`DumpInfo`(338) 包含组件名/ID、装饰器类型、变量名、依赖 elmtId 列表 | DFX 信息收集 | AC-2.1~AC-2.4 |
| R-4 | 行为 | `stateMgmtProfiler`(16)/`stateMgmtDFX.enableProfiler`/`setPropertyAccessTrace` | `enableProfiler = true` 时每次变更输出组件名/ID、装饰器类型、变量名、依赖 elmtId、sync peer；`stateMgmtProfiler` 实例由 C++ 初始化注入（未注入时为桩）；V2 `setPropertyAccessTrace(true)`（API 12+）输出详细 `addRef`/`fireChange` 日志 | 性能采集 | AC-3.1~AC-3.3 |
| R-5 | 行为 | `UpdateFuncRecord`(51)/`UpdateFuncsByElmtId` 管理 | 组件创建时每 elmtId 的更新函数经 `UpdateFuncRecord` 记录到 `UpdateFuncsByElmtId`；持有 `updateFunc`/`classObject_`/`node`，提供 `getUpdateFunc`/`getClassObject`/`getPopFunc`；If/Else 分支切换时 `isPending_`(55)/`isChanged_`(56) 暂存；dirty 重渲染时按 elmtId 查找执行；V1/V2 共享（`puv2_common/`，`ViewPU`/`ViewV2` 都用） | V1/V2 共享渲染基础设施 | AC-4.1~AC-4.5 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 代码审查 | `state_mgmt_console_trace.ts:28` 统一日志门面 |
| VM-2 | AC-1.2 | 单元测试 | `common_tests/` limitLog 去重 |
| VM-3 | AC-1.3 | 单元测试 | `common_tests/` applicationError |
| VM-4 | AC-1.4 | 单元测试 | `common_tests/` MAX_LOG_TYPES |
| VM-5 | AC-2.1 | 单元测试 | `common_tests/` getStateMgmtInfo |
| VM-6 | AC-2.2 | 代码审查 | `state_mgmt_dfx.ts:194` getElementName |
| VM-7 | AC-2.3 | 单元测试 | `common_tests/` findViewById |
| VM-8 | AC-2.4 | 单元测试 | `common_tests/` DumpInfo |
| VM-9 | AC-3.1 | 单元测试 | `common_tests/` enableProfiler |
| VM-10 | AC-3.2 | 代码审查 | `state_mgmt_profiler.ts:16` C++ 注入 |
| VM-11 | AC-3.3 | 单元测试 | `v2_tests/` setPropertyAccessTrace |
| VM-12 | AC-4.1 | 单元测试 | `common_tests/` UpdateFuncRecord 注册 |
| VM-13 | AC-4.2 | 单元测试 | `common_tests/` 访问方法 |
| VM-14 | AC-4.3 | 单元测试 | `common_tests/` isPending/isChanged |
| VM-15 | AC-4.4 | 单元测试 | `common_tests/` dirty 查找 |
| VM-16 | AC-4.5 | 代码审查 | `puv2_updatefunc.ts:51` V1/V2 共享 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `stateMgmtConsole` | `common/state_mgmt_console_trace.ts:28` | 日志门面 |
| `stateMgmtTrace` | `common/state_mgmt_console_trace.ts:128` | Trace 门面 |
| `limitLog` | `common/state_mgmt_console_trace.ts:64` | 20s 去重窗口 |
| `frequentApplicationError` | `common/state_mgmt_console_trace.ts:85` | 去重错误输出 |
| `MAX_LOG_TYPES` | `common/state_mgmt_console_trace.ts:35` | 3000 上限 |
| `stateMgmtDFX` | `common/state_mgmt_dfx.ts:15` | DFX 信息收集 |
| `getElementName` | `common/state_mgmt_dfx.ts:194` | elmtId→名称映射 |
| `DumpInfo` | `common/state_mgmt_dfx.ts:338` | dump 信息结构 |
| `stateMgmtProfiler` | `common/state_mgmt_profiler.ts:16` | 性能采集 |
| `UpdateFuncRecord` | `puv2_common/puv2_updatefunc.ts:51` | update-function 记录 |
| `UpdateFuncsByElmtId` | `puv2_common/puv2_updatefunc.ts` | elmtId→UpdateFuncRecord 映射 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | stateMgmtConsole/stateMgmtDFX/stateMgmtProfiler/UpdateFuncRecord 引入 | 调试/渲染基础设施 | 无需迁移 |
| API 12 | `setPropertyAccessTrace` V2 属性访问追踪引入 | V2 调试 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| V1/V2 共享 | stateMgmtConsole/stateMgmtDFX/stateMgmtProfiler/UpdateFuncRecord 服务整个状态管理子系统（V1+V2），归 V1 域统一管理 |
| 日志统一门面 | 所有日志走 stateMgmtConsole（TAG STATE_MGMT），limitLog 20s 去重 |
| Inspector 2000ms 超时 | getStateMgmtInfo 上报 UiSessionManager 有 2000ms 超时 |
| UpdateFuncRecord 共享 | 位于 puv2_common/，ViewPU（V1）与 ViewV2（V2）共享 |
| Profiler C++ 注入 | stateMgmtProfiler 实例由 C++ 初始化注入，未注入时为桩 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_console_trace.ts:28-149` | `stateMgmtConsole`/`stateMgmtTrace` 日志门面 + `limitLog` 去重 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_dfx.ts:15-396` | `stateMgmtDFX`/`DumpInfo` DFX 信息收集 + `getElementName` ID 映射 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/common/state_mgmt_profiler.ts:16-33` | `stateMgmtProfiler` 性能采集 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_updatefunc.ts:51-160` | `UpdateFuncRecord`/`UpdateFuncsByElmtId` update-function 记录 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | 日志/DFX/Profiler/UpdateFuncRecord 行为回归测试 |
