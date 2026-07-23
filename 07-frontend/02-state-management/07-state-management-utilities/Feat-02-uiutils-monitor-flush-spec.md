# 特性规格

> Func-07-02-07-Feat-02 UIUtils 监听与同步刷新：固化 `UIUtils.addMonitor`/`clearMonitor`（动态监听，API 20+，错误码 130000-130002）、`applySync`（闭包同步刷新，API 22+）、`flushUpdates`（全量同步刷新，API 22+）、`flushUIUpdates`（仅 UI 节点同步标脏，API 22+）行为规格与错误码 140001/140002。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIUtils 监听与同步刷新 |
| 特性编号 | Func-07-02-07-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | addMonitor/clearMonitor API 20 起；applySync/flushUpdates/flushUIUpdates API 22 起；MonitorOptions.enableWildcard API 26 起 |
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
| ObserveV2（监听/刷新实现） | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts` | — |
| addMonitor/clearMonitor 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-addMonitor-clearMonitor.md` | — |
| applySync/flushUpdates 指南 | `docs/zh-cn/application-dev/ui/state-management/arkts-new-applySync-flushUpdates-flushUIUpdates.md` | — |
| 状态管理错误码 | `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | — |

---

## 用户故事

### US-1: addMonitor 动态监听

**作为** 应用开发者,
**我想要** 用 `UIUtils.addMonitor`（API 20+）运行时动态添加监听方法,
**以便** 在运行时按需监听 @ComponentV2 与 @ObservedV2 实例的属性变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `UIUtils.addMonitor(target, path, monitorCallback, options?)`(64，API 20+) THEN 动态添加监听，复用 @Monitor 路径遍历机制；回调参数为 `IMonitor`（before/now/path） | 正常 |
| AC-1.2 | WHEN target 为 @ComponentV2 或 @ObservedV2（且至少有一个 @Trace 装饰变量）实例 THEN 支持监听 | 正常 |
| AC-1.3 | WHEN `MonitorOptions.isSynchronous=true` THEN 行为同 @SyncMonitor（同步立即执行） | 正常 |
| AC-1.4 | WHEN `MonitorOptions.enableWildcard=true`（API 26+）THEN 支持通配符路径 | 正常 |
| AC-1.5 | WHEN 同一 path 注册多个不同名监听函数 THEN 支持；同名重复注册失败并打印错误日志 | 边界 |
| AC-1.6 | WHEN `isSynchronous` 在同一 path 多次设置 THEN 仅第一次有效，后续不可改 | 边界 |

### US-2: clearMonitor 取消监听

**作为** 应用开发者,
**我想要** 用 `UIUtils.clearMonitor`（API 20+）删除通过 addMonitor 添加的监听,
**以便** 避免内存泄漏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `UIUtils.clearMonitor(target, path, monitorCallback?)`(84，API 20+) THEN 删除通过 addMonitor 添加的监听 | 正常 |
| AC-2.2 | WHEN clearMonitor 不传 monitorCallback THEN 删除该 path 的所有 addMonitor 回调 | 正常 |
| AC-2.3 | WHEN clearMonitor 找不到对应回调 THEN 打印告警 | 边界 |
| AC-2.4 | WHEN clearMonitor 试图删除 `@Monitor` 装饰器声明的回调 THEN 不能删除（clearMonitor 仅管理 addMonitor 添加的监听） | 边界 |

### US-3: applySync 闭包同步刷新

**作为** 应用开发者,
**我想要** 用 `UIUtils.applySync`（API 22+）同步刷新闭包内的状态变量修改,
**以便** 解决 V2 异步调度与 `animateTo` 不兼容问题。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `UIUtils.applySync<T>(task: TaskCallback): T`(104，API 22+) THEN 同步刷新闭包内的状态变量修改（含 @Computed 计算、@Monitor 回调、UI 重新渲染） | 正常 |
| AC-3.2 | WHEN applySync 用于 animateTo 前的额外修改 THEN 确保修改先同步生效 | 正常 |
| AC-3.3 | WHEN applySync 内嵌套 applySync THEN 内层被跳过返回 undefined，打印警告 | 边界 |
| AC-3.4 | WHEN applySync 内调用 flushUpdates/flushUIUpdates THEN 被忽略，打印警告 | 边界 |

### US-4: flushUpdates/flushUIUpdates 全量同步刷新

**作为** 应用开发者,
**我想要** 用 `flushUpdates`/`flushUIUpdates`（API 22+）同步刷新调用前的所有状态变量修改,
**以便** 在非 @Computed/@Monitor 场景同步控制刷新粒度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `UIUtils.flushUpdates()`(108，API 22+) THEN 同步刷新调用前的所有状态变量修改（含 @Computed/@Monitor/UI 重渲染） | 正常 |
| AC-4.2 | WHEN 调用 `UIUtils.flushUIUpdates()`(112，API 22+) THEN 仅同步标脏对应 UI 节点，不执行 @Computed 计算与 @Monitor 回调 | 正常 |
| AC-4.3 | WHEN flushUIUpdates vs flushUpdates THEN 前者仅处理 `elmtIdsChanged_`，不处理 Computed/Monitor/Persistence；后者全量处理 | 边界 |

### US-5: 非法调用约束与错误码

**作为** 应用开发者,
**我想要** 明确 applySync/flushUpdates/flushUIUpdates 的非法调用场景与错误码,
**以便** 避免 @Computed/@Monitor 内误用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN addMonitor target 不是 @ComponentV2/@ObservedV2 实例 THEN 返回错误码 130000 | 异常 |
| AC-5.2 | WHEN addMonitor/clearMonitor path 非法（非 string 或非数组）THEN 返回错误码 130001 | 异常 |
| AC-5.3 | WHEN addMonitor/clearMonitor monitorCallback 不是函数或是匿名函数 THEN 返回错误码 130002 | 异常 |
| AC-5.4 | WHEN 在 @Computed getter 内调用 applySync/flushUpdates/flushUIUpdates THEN 返回错误码 140001 | 异常 |
| AC-5.5 | WHEN 在 @Monitor 回调内调用 flushUpdates/flushUIUpdates THEN 返回错误码 140002 | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 addMonitor |
| AC-1.2 | US-1 | R-1 | 单元测试 target 限制 |
| AC-1.3 | US-1 | R-1 | 单元测试 isSynchronous |
| AC-1.4 | US-1 | R-1 | 单元测试 enableWildcard |
| AC-1.5 | US-1 | R-1 | 单元测试 多监听函数 |
| AC-1.6 | US-1 | R-1 | 单元测试 isSynchronous 不可改 |
| AC-2.1 | US-2 | R-2 | 单元测试 clearMonitor |
| AC-2.2 | US-2 | R-2 | 单元测试 不传 callback |
| AC-2.3 | US-2 | R-2 | 单元测试 找不到告警 |
| AC-2.4 | US-2 | R-2 | 单元测试 不删除装饰器回调 |
| AC-3.1 | US-3 | R-3 | 单元测试 applySync |
| AC-3.2 | US-3 | R-3 | 单元测试 animateTo 协调 |
| AC-3.3 | US-3 | R-4 | 单元测试 嵌套跳过 |
| AC-3.4 | US-3 | R-4 | 单元测试 flush 被忽略 |
| AC-4.1 | US-4 | R-5 | 单元测试 flushUpdates |
| AC-4.2 | US-4 | R-6 | 单元测试 flushUIUpdates |
| AC-4.3 | US-4 | R-5 | 单元测试 差异 |
| AC-5.1 | US-5 | R-7 | 单元测试 错误码 130000 |
| AC-5.2 | US-5 | R-7 | 单元测试 错误码 130001 |
| AC-5.3 | US-5 | R-7 | 单元测试 错误码 130002 |
| AC-5.4 | US-5 | R-8 | 单元测试 错误码 140001 |
| AC-5.5 | US-5 | R-8 | 单元测试 错误码 140002 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `UIUtils.addMonitor(target, path, monitorCallback, options?)`(64，API 20+) | 动态添加监听，复用 @Monitor 路径遍历机制（`ObserveV2.AddMonitorPath`(1259)），回调参数 `IMonitor`（before/now/path）；target 仅支持 @ComponentV2/@ObservedV2（含 @Trace）实例；`MonitorOptions.isSynchronous=true` 行为同 @SyncMonitor；`enableWildcard=true`（API 26+）支持通配符；同一 path 可注册多个不同名监听函数，同名重复注册失败；`isSynchronous` 仅第一次有效，后续不可改；必须传非匿名 function（用 `monitorFunc.name` 作 key） | API 20+；enableWildcard API 26+ | AC-1.1~AC-1.6 |
| R-2 | 行为 | 调用 `UIUtils.clearMonitor(target, path, monitorCallback?)`(84，API 20+) | 删除通过 addMonitor 添加的监听；不传 monitorCallback 时删除该 path 所有回调；找不到对应回调打印告警；不能删除 `@Monitor` 装饰器声明的回调（clearMonitor 仅管理 addMonitor） | API 20+ | AC-2.1~AC-2.4 |
| R-3 | 行为 | 调用 `UIUtils.applySync<T>(task: TaskCallback): T`(104，API 22+) | 同步刷新闭包内的状态变量修改（含 @Computed 计算、@Monitor 回调、UI 重新渲染）；用于 animateTo 前的额外修改先同步生效；内部委托 `ObserveV2.applySync`(1645) | API 22+ | AC-3.1, AC-3.2 |
| R-4 | 边界 | applySync 嵌套与 flush 混用 | applySync 内嵌套 applySync 被跳过返回 undefined，打印警告；applySync 内调 flushUpdates/flushUIUpdates 被忽略，打印警告 | 嵌套限制 | AC-3.3, AC-3.4 |
| R-5 | 行为 | 调用 `UIUtils.flushUpdates()`(108，API 22+) | 同步刷新调用前的所有状态变量修改（含 @Computed/@Monitor/UI 重渲染）；内部委托 `ObserveV2.flushUpdates`(1698) | API 22+；全量同步 | AC-4.1, AC-4.3 |
| R-6 | 行为 | 调用 `UIUtils.flushUIUpdates()`(112，API 22+) | 仅同步标脏对应 UI 节点，不执行 @Computed 计算与 @Monitor 回调；内部委托 `ObserveV2.flushUIUpdates`(1718)；仅处理 `elmtIdsChanged_`，不处理 Computed/Monitor/Persistence | API 22+；仅 UI 节点 | AC-4.2, AC-4.3 |
| R-7 | 异常 | addMonitor/clearMonitor 非法参数 | target 不是 @ComponentV2/@ObservedV2（含 @Trace）实例 → 错误码 130000；path 不是 string 或数组 → 130001；monitorCallback 不是函数或匿名函数 → 130002 | API 20+ | AC-5.1~AC-5.3 |
| R-8 | 异常 | applySync/flushUpdates/flushUIUpdates 非法调用位置 | 在 @Computed getter 内调用 → 错误码 140001；在 @Monitor 回调内调用 flushUpdates/flushUIUpdates → 错误码 140002（applySync 不在 140002 列表中） | API 22+ | AC-5.4, AC-5.5 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `v2_tests/` addMonitor |
| VM-2 | AC-1.2 | 单元测试 | `v2_tests/` target 限制 |
| VM-3 | AC-1.3 | 单元测试 | `v2_tests/` isSynchronous |
| VM-4 | AC-1.4 | 单元测试 | `v2_tests/` enableWildcard |
| VM-5 | AC-1.5 | 单元测试 | `v2_tests/` 多监听函数 |
| VM-6 | AC-1.6 | 单元测试 | `v2_tests/` isSynchronous 不可改 |
| VM-7 | AC-2.1 | 单元测试 | `v2_tests/` clearMonitor |
| VM-8 | AC-2.2 | 单元测试 | `v2_tests/` 不传 callback |
| VM-9 | AC-2.3 | 单元测试 | `v2_tests/` 找不到告警 |
| VM-10 | AC-2.4 | 单元测试 | `v2_tests/` 不删除装饰器回调 |
| VM-11 | AC-3.1 | 单元测试 | `v2_tests/` applySync |
| VM-12 | AC-3.2 | 单元测试 | `v2_tests/` animateTo 协调 |
| VM-13 | AC-3.3 | 单元测试 | `v2_tests/` 嵌套跳过 |
| VM-14 | AC-3.4 | 单元测试 | `v2_tests/` flush 被忽略 |
| VM-15 | AC-4.1 | 单元测试 | `v2_tests/` flushUpdates |
| VM-16 | AC-4.2 | 单元测试 | `v2_tests/` flushUIUpdates |
| VM-17 | AC-4.3 | 单元测试 | `v2_tests/` 差异 |
| VM-18 | AC-5.1 | 单元测试 | `v2_tests/` 错误码 130000 |
| VM-19 | AC-5.2 | 单元测试 | `v2_tests/` 错误码 130001 |
| VM-20 | AC-5.3 | 单元测试 | `v2_tests/` 错误码 130002 |
| VM-21 | AC-5.4 | 单元测试 | `v2_tests/` 错误码 140001 |
| VM-22 | AC-5.5 | 单元测试 | `v2_tests/` 错误码 140002 |

---

## 错误码规格

| 错误码 | 触发条件 | 错误信息 | 起始版本 |
|--------|----------|----------|----------|
| 130000 | addMonitor/clearMonitor target 不是 @ComponentV2/@ObservedV2（含 @Trace）实例 | `The target is not a custom component instance or V2 class instance.` | API 20 |
| 130001 | addMonitor/clearMonitor path 不是 string 或数组 | `The path is invalid.` | API 20 |
| 130002 | addMonitor/clearMonitor monitorCallback 不是函数或匿名函数 | `addMonitor/clearMonitor failed because the monitorFunc is illegal` | API 20 |
| 140001 | applySync/flushUpdates/flushUIUpdates 在 @Computed getter 内调用 | `The function is not allowed to be called in @Computed.` | API 22 |
| 140002 | flushUpdates/flushUIUpdates 在 @Monitor 回调内调用 | `The function is not allowed to be called in @Monitor.` | API 22 |

---

## 核心类与机制清单

| 类/机制 | 定义位置 | 职责 |
|---------|----------|------|
| `UIUtilsImpl.addMonitor` | `sdk/ui_utils.ts:64-82` | 动态监听（API 20+） |
| `UIUtilsImpl.clearMonitor` | `sdk/ui_utils.ts:84-97` | 取消监听（API 20+） |
| `UIUtilsImpl.applySync` | `sdk/ui_utils.ts:104-106` | 闭包同步刷新（API 22+） |
| `UIUtilsImpl.flushUpdates` | `sdk/ui_utils.ts:108-110` | 全量同步刷新（API 22+） |
| `UIUtilsImpl.flushUIUpdates` | `sdk/ui_utils.ts:112-114` | 仅 UI 节点同步标脏（API 22+） |
| `ObserveV2.AddMonitorPath` | `v2/v2_change_observation.ts:1259` | 动态监听底层实现 |
| `ObserveV2.clearMonitorPath` | `v2/v2_change_observation.ts:1327` | 取消监听底层实现 |
| `ObserveV2.applySync` | `v2/v2_change_observation.ts:1645` | 同步刷新底层实现 |
| `ObserveV2.flushUpdates` | `v2/v2_change_observation.ts:1698` | 全量同步刷新底层实现 |
| `ObserveV2.flushUIUpdates` | `v2/v2_change_observation.ts:1718` | 仅 UI 节点同步底层实现 |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 20 | addMonitor/clearMonitor 引入（错误码 130000-130002） | 动态监听 | 处理新增错误码 |
| API 22 | applySync/flushUpdates/flushUIUpdates 引入（错误码 140001/140002） | 同步刷新逃生舱 | 避免在 @Computed/@Monitor 内调用 |
| API 26 | MonitorOptions.enableWildcard 支持 | 通配符监听 | 按需启用 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| addMonitor 复用 @Monitor 机制 | addMonitor/clearMonitor 复用 @Monitor 路径遍历 + IMonitor(before/now/path)；target 仅 @ComponentV2/@ObservedV2 |
| addMonitor 必须非匿名函数 | 用 `monitorFunc.name` 作 key，必须传非匿名 function |
| 三档同步刷新 | applySync 闭包同步（含 Computed/Monitor/UI）；flushUpdates 全量同步；flushUIUpdates 仅 UI 节点 |
| @Computed/@Monitor 内禁用 | applySync/flushUpdates/flushUIUpdates 在 @Computed 内调用抛 140001；flushUpdates/flushUIUpdates 在 @Monitor 内调用抛 140002 |
| applySync 嵌套限制 | applySync 内嵌套 applySync 被跳过；applySync 内调 flushUpdates/flushUIUpdates 被忽略 |

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
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:64-82` | `UIUtilsImpl.addMonitor`（API 20+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:84-97` | `UIUtilsImpl.clearMonitor`（API 20+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/sdk/ui_utils.ts:104-114` | `applySync`/`flushUpdates`/`flushUIUpdates`（API 22+） |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:1259` | `ObserveV2.AddMonitorPath` 底层实现 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:1327` | `ObserveV2.clearMonitorPath` 底层实现 |
| `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/v2/v2_change_observation.ts:1645/1698/1718` | `ObserveV2.applySync`/`flushUpdates`/`flushUIUpdates` 底层实现 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/v2_tests/` | addMonitor/clearMonitor/applySync/flushUpdates 行为回归测试 |
| `frameworks/bridge/declarative_frontend/state_mgmt/test/unittest/entry/src/main/common_tests/` | UIUtils 共享测试 |

### 开发者文档

| 文件 | 说明 |
|------|------|
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-addMonitor-clearMonitor.md` | addMonitor/clearMonitor 指南 |
| `docs/zh-cn/application-dev/ui/state-management/arkts-new-applySync-flushUpdates-flushUIUpdates.md` | applySync/flushUpdates 指南 |
| `docs/zh-cn/application-dev/reference/apis-arkui/errorcode-stateManagement.md` | 错误码 130000-130002/140001/140002 |
