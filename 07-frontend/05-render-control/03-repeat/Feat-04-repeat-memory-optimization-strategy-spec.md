# 特性规格

> Func-07-05-03-Feat-04 Repeat 内存优化策略：固化 `VirtualScrollOptions.memoryOptimizationStrategy`+`RepeatMemOptStrategy`（DEFAULT/ENABLE_AUTO_CACHE_OPTIMIZATION，`@since26`，**仅 v2**）选项解析、节点创建注册窗口/内存回调、窗口 hide 同步清/show 延迟恢复/内存 LOW·CRITICAL 异步清、2s 防抖（`CACHE_TASK_DELAY_TIME`）+1s `PostMemOptTask` 轮询、`CleanCache`/`PurgeAll`/`RestoreCache`/`RemovingExpiringItem`（`pendingRemoveRids_` deadline 分批）、无 `maxCacheCount` 硬下限（仅 LazyForEach 有）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Repeat 内存优化策略 |
| 特性编号 | Func-07-05-03-Feat-04 |
| 优先级 | P2 |
| 目标版本 | dynamic `@since26`（`VirtualScrollOptions.memoryOptimizationStrategy`+`RepeatMemOptStrategy`）；static `@since26`（同套）；仅 v2（`RepeatVirtualScroll2Node`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01~03；本特性聚焦 `@since26` 内存优化策略（仅 v2 虚拟滚动）。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/03-repeat/design.md` | Baselined |
| Dynamic API | `interface/sdk-js/api/@internal/component/ets/repeat.d.ts` | — |
| Static API | `interface/sdk-js/api/arkui/component/repeat.static.d.ets` | — |
| TS 选项解析 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_repeat.ts` / `pu_repeat_virtual_scroll_2_impl.ts` | — |
| v2 节点（memOpt 注册/回调/防抖/清恢复） | `frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_node.cpp` / `.h` | — |
| v2 Model（removeNodes） | `frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_model_ng.cpp` | — |
| v2 缓存（RestoreL2CacheByIndex） | `frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_caches.cpp` | — |
| 对照（LazyForEach maxCacheCount） | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` | — |

> 需求基线详见 proposal.md。design.md 与本文档增量合并，互不依赖。

---

## 用户故事

### US-1: memoryOptimizationStrategy 选项解析

**作为** 应用开发者,
**我想要** 用 `virtualScroll({memoryOptimizationStrategy})` 启用自动缓存优化,
**以便** 后台/低内存时框架自动回收缓存、回前台恢复。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `VirtualScrollOptions.memoryOptimizationStrategy` 提供（dynamic `repeat.d.ts:230`/static `:185` `@since26`）THEN `parseMemoryOptimizationStrategy`（`pu_repeat.ts:326-341`）解析，存 `config.memOptStrategy`（`:163,338`） | 正常 |
| AC-1.2 | WHEN 值非 DEFAULT/ENABLE_AUTO_CACHE_OPTIMIZATION THEN 警告并强制 `DEFAULT`（`pu_repeat.ts:326-341`） | 异常 |
| AC-1.3 | WHEN v2 创建 THEN `memOptStrategy_` 默认 DEFAULT（`repeat_virtual_scroll_2_node.h:355`），ctor 从 int32 转 enum（`repeat_virtual_scroll_2_node.cpp:83`）；`RepeatMemOptStrategy` 枚举 DEFAULT=0/ENABLE_AUTO_CACHE_OPTIMIZATION=1<<0（`:95-98`） | 正常 |
| AC-1.4 | WHEN v2 `RepeatVirtualScroll2Native.create(arrLen,totalCount,memOptStrategy_,handlers)` THEN memOpt 作第 3 参传入（`pu_repeat_virtual_scroll_2_impl.ts:495,532`） | 正常 |

### US-2: 节点创建注册回调

**作为** 应用开发者,
**我想要** 启用策略后框架自动注册窗口/内存监听,
**以便** 无需手动触发即可响应可见性与内存压力。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `GetOrCreateRepeatNode` 新建 v2 且 `memOptStrategy_==ENABLE_AUTO_CACHE_OPTIMIZATION` THEN 注册 `WindowStateChangedCallback`+`MemoryLevelChangedCallback`+`PostMemOptTask()`（`repeat_virtual_scroll_2_node.cpp:65-69`） | 正常 |
| AC-2.2 | WHEN `memOptStrategy_==DEFAULT` THEN 不注册上述回调，沿用标准缓存行为 | 边界 |
| AC-2.3 | WHEN v2 节点析构 THEN 对称解注册（仅启用时，`:88-94`） | 正常 |
| AC-2.4 | WHEN 注册 THEN `RegisterWindowStateChangedCallback`→`context->AddWindowStateChangedCallback(GetId())`（`:1060-1065`）；`RegisterMemoryLevelChangedCallback`→`context->AddNodesToNotifyMemoryLevel(GetId())`（`:1074-1079`） | 正常 |

### US-3: 窗口/内存触发与防抖

**作为** 应用开发者,
**我想要** 窗口 hide 同步清、show 延迟恢复、内存压力异步清,
**以便** 后台省内存、回前台恢复流畅、避免抖动。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 窗口 hide THEN `OnWindowHide`→`CleanCache(true)` 同步清（`repeat_virtual_scroll_2_node.cpp:1048-1051`） | 正常 |
| AC-3.2 | WHEN 窗口 show THEN `OnWindowShow`→`ScheduleRestoreCacheTask()`+`PostMemOptTask()`（`:1042-1046`）延迟恢复 | 正常 |
| AC-3.3 | WHEN 内存 level=LOW(1)/CRITICAL(2) THEN `OnNotifyMemoryLevel`→`CleanCache(false)` 异步清（`:1053-1058`，常量 `:34-35`） | 正常 |
| AC-3.4 | WHEN 内存 level=HIGH(0)/正常 THEN 不触发清（仅 LOW/CRITICAL） | 边界 |
| AC-3.5 | WHEN 调度 clean/restore THEN `TryExecuteScheduledCacheTask`（`:1117-1133`）须等 `CACHE_TASK_DELAY_TIME=2s`（`:33`）且距 `setActiveRangeTime_`≥2s（clean）；restore 另要求 `CheckParentFrameNodeVisibility()` 为真否则清标志 | 边界 |
| AC-3.6 | WHEN `PostMemOptTask` 周期 poll THEN `PostDelayedTask(UI,1000ms)`（`:1197-1224,1204`），每 tick 比较 `CheckParentFrameNodeVisibility()` 与缓存可见性，变化则 schedule restore/clean，再 `TryExecuteScheduledCacheTask`，递归重投 | 正常 |

### US-4: CleanCache / PurgeAll / RestoreCache / RemovingExpiringItem

**作为** 应用开发者,
**我想要** 清缓存保留 per-ttype 恢复预算、分批释放不阻塞帧,
**以便** 内存回收彻底且恢复高效。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `CleanCache(syncClean)`（`:1135-1155`）THEN `restoringCache_=false`+`PurgeAll()`；syncClean=true 同步排空 `pendingRemoveRids_`（`DisableRecycle`+`RemoveNode` 每 rid）；false 则 `PostIdleTask()`；复位 clean/restore 标志 | 正常 |
| AC-4.2 | WHEN `PurgeAll`（`:691-702`）THEN 次级 VSP push this+`onPurgeAll_()`；TS `onPurgeAll`（`pu_repeat_virtual_scroll_2_impl.ts:1783-1816`）按 per-ttype `cachedCount` 预算保留项（记 `template4RestoreCache_`），其余 `removeNodes(spareRidArray,indexesArray)`——**不盲删，保留恢复预算** | 正常 |
| AC-4.3 | WHEN `StartRestoreCache`/`RestoreCache(deadline,...)`（`:1157-1185`）THEN 排空 `cleanedCacheIndexes_`，经 `caches_.RestoreL2CacheByIndex(*it,deadline)`（调 TS `onGetRid4Index(...,true)` 离屏构建，`repeat_virtual_scroll_2_caches.cpp:70-114`），超时/非 long-predict 重投 | 正常 |
| AC-4.4 | WHEN `RemovingExpiringItem(deadline)`（`:712-744`）THEN 在 deadline 内排空 `pendingRemoveRids_`（测每节点耗时，`deadline-endTimeStamp>averageTime` 续释），`DisableRecycle`+`RemoveNode` 每 rid；未排空则 `PostIdleTask` 重投（`:800-802`） | 正常 |
| AC-4.5 | WHEN `pendingRemoveRids_` 入队 THEN `AddPendingRemoveNodes`（`:704-710`）为 `removeNodes` model 调用入口（`repeat_virtual_scroll_2_model_ng.cpp:53-60`） | 正常 |
| AC-4.6 | WHEN 内存压力回收 THEN Repeat v2 **无 `maxCacheCount` 硬下限**（仅 LazyForEach 有 `maxCacheCount=2`，`lazy_for_each_builder.cpp:1472`）；回收量仅由用户 `TemplateOptions.cachedCount` per-ttype 预算约束（`onPurgeAll` 保留逻辑） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2 | T-4 | UT + SDK 比对 | `repeat.d.ts:30-230`、`pu_repeat.ts:326-341`、`repeat_virtual_scroll_2_node.h:95-98` |
| AC-2.1~2.4 | R-3 | T-4 | UT：节点创建注册/解注册 | `repeat_virtual_scroll_2_node.cpp:65-94,1060-1079` |
| AC-3.1~3.6 | R-4,R-5,R-6 | T-4 | UT：窗口/内存回调 + 防抖 + poll | `repeat_virtual_scroll_2_node.cpp:1042-1224` |
| AC-4.1~4.6 | R-7,R-8,R-9 | T-4 | UT：CleanCache/PurgeAll/RestoreCache/RemovingExpiringItem | `repeat_virtual_scroll_2_node.cpp:691-1185`、`pu_repeat_virtual_scroll_2_impl.ts:1783-1816` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | memoryOptimizationStrategy 提供 | parseMemoryOptimizationStrategy 解析存 config.memOptStrategy | 非法值强制 DEFAULT | AC-1.1,AC-1.2 |
| R-2 | 边界 | memOpt 仅 v2 | v2 ctor int→enum；v1（已废弃）无 memOpt | RepeatMemOptStrategy DEFAULT=0/ENABLE_AUTO_CACHE_OPTIMIZATION=1<<0 | AC-1.3 |
| R-3 | 行为 | v2 新建+ENABLE_AUTO_CACHE_OPTIMIZATION | 注册窗口/内存回调+PostMemOptTask；析构对称解注册 | DEFAULT 不注册 | AC-2.1~2.4 |
| R-4 | 行为 | 窗口/内存事件 | hide→CleanCache(true)同步；show→ScheduleRestoreCacheTask；LOW/CRITICAL→CleanCache(false)异步 | 仅 LOW(1)/CRITICAL(2) 触发清 | AC-3.1~3.4 |
| R-5 | 边界 | clean/restore 调度 | 须 2s 防抖（cacheTaskPostTime_+setActiveRangeTime_）；restore 要求父可见 | CACHE_TASK_DELAY_TIME=2s | AC-3.5 |
| R-6 | 行为 | PostMemOptTask poll | 1000ms 自重投；可见性变化 schedule clean/restore | — | AC-3.6 |
| R-7 | 行为 | CleanCache | PurgeAll + sync 排空/async PostIdleTask | 复位标志 | AC-4.1 |
| R-8 | 行为 | PurgeAll | onPurgeAll 按 per-ttype cachedCount 预算保留，余 removeNodes | 不盲删，保留恢复预算 | AC-4.2 |
| R-9 | 边界 | 内存压力回收量 | 无 maxCacheCount 硬下限；仅用户 TemplateOptions.cachedCount 约束 | LazyForEach 有 maxCacheCount=2，Repeat v2 无 | AC-4.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 选项解析 | UT + SDK 比对 | RepeatMemOptStrategy 枚举、非法值强制 DEFAULT、@since26 |
| VM-2 | AC-2.x 注册 | UT | ENABLE 才注册、析构解注册 |
| VM-3 | AC-3.x 触发/防抖 | UT | hide 同步/show 延迟/LOW·CRITICAL 异步、2s 防抖、1s poll |
| VM-4 | AC-4.x 清/恢复 | UT + 内存 dump | PurgeAll per-ttype 预算保留、RemovingExpiringItem 分批、无 maxCacheCount |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `VirtualScrollOptions.memoryOptimizationStrategy`（dynamic/static `@since26`） | 既有版本扩展 | v2 自动缓存优化 | DEFAULT/ENABLE_AUTO_CACHE_OPTIMIZATION | AC-1.1 |
| `RepeatMemOptStrategy` 枚举（`@since26`） | 既有 | 策略枚举 | 仅 v2 生效 | AC-1.3 |

> SDK：dynamic `repeat.d.ts:30-53,230`；static `repeat.static.d.ets:185,343-362`。

## 接口规格

### 接口定义

**VirtualScrollOptions.memoryOptimizationStrategy（`repeat.d.ts:230`）**

| 属性 | 值 |
|------|-----|
| 字段签名 | `memoryOptimizationStrategy?: RepeatMemOptStrategy` |
| 类型 | `RepeatMemOptStrategy`（DEFAULT=0 / ENABLE_AUTO_CACHE_OPTIMIZATION=1<<0） |
| 开放范围 | Public（`@since26`，仅 v2） |
| 错误码 | N/A（非法值强制 DEFAULT） |
| 关联 AC | AC-1.1,AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| memoryOptimizationStrategy | RepeatMemOptStrategy | 否 | DEFAULT | 仅 ENABLE_AUTO_CACHE_OPTIMIZATION 启用回调；非法值强制 DEFAULT |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | ENABLE + 窗口 hide | CleanCache(true) 同步清 | AC-3.1 |
| 2 | ENABLE + 内存 CRITICAL | CleanCache(false) 异步清 | AC-3.3 |
| 3 | PurgeAll | 按 per-ttype cachedCount 预算保留，余 removeNodes | AC-4.2 |
| 4 | ENABLE + 窗口 show | 经 2s 防抖 RestoreCache | AC-3.2,AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。memoryOptimizationStrategy 为 `@since26` 新增、仅 v2 生效；v1（已废弃）无此能力。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic/static `@since26`。
- **API 版本号策略:** 按 SDK `@since26` 标注；仅 v2（`RepeatVirtualScroll2Node`）。

> **无 maxCacheCount 硬下限风险（F-mem）：** Repeat v2 内存回收**无** LazyForEach 的 `maxCacheCount=2` 硬下限（`lazy_for_each_builder.cpp:1472`），回收量仅由用户 `TemplateOptions.cachedCount` per-ttype 预算约束（`onPurgeAll` 保留逻辑）；用户未设 cachedCount 时回收后保留项取决于默认预算（风险 RISK-F4-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| memOpt 仅 v2 | v1（已废弃）无 memOpt；v2 新建+ENABLE 才注册回调 | AC-2.1,AC-2.2 |
| 2s 防抖+1s poll | clean/restore 须 2s 防抖；PostMemOptTask 1s 自重投 | AC-3.5,AC-3.6 |
| PurgeAll 保留预算 | 按 per-ttype cachedCount 保留恢复项，不盲删 | AC-4.2 |
| 无 maxCacheCount 硬下限 | 仅 LazyForEach 有；Repeat v2 由用户 cachedCount 约束 | AC-4.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 内存 | ENABLE 后台/低内存回收缓存， RemovingExpiringItem 分批不阻塞帧 | UT + 内存 dump | `repeat_virtual_scroll_2_node.cpp:712-744,1135-1155` |
| 功耗 | 后台 PurgeAll 减少离屏节点活跃开销 | UT | `repeat_virtual_scroll_2_node.cpp:691-702` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 是 | 内存压力更易触发 CleanCache | XTS | `repeat_virtual_scroll_2_node.cpp:1053-1058` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 无直接关联 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 是 | 窗口 hide/show 触发 CleanCache/RestoreCache（ENABLE 时） | AC-3.1,AC-3.2 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | memoryOptimizationStrategy `@since26`、仅 v2 | AC-1.1 |
| 生态兼容 | 是 | dynamic/static `@since26` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Repeat 内存优化策略
  作为 应用开发者
  我想要 用 memoryOptimizationStrategy 自动回收/恢复缓存
  以便 后台省内存、回前台恢复流畅

  Scenario: 内存压力回收
    Given memoryOptimizationStrategy = ENABLE_AUTO_CACHE_OPTIMIZATION（v2）
    When 系统内存 level = CRITICAL
    Then CleanCache(false) 异步清，PurgeAll 按 per-ttype cachedCount 预算保留
    And 窗口 show 后经 2s 防抖 RestoreCache

  Scenario Outline: 触发条件
    Given ENABLE 策略
    When <事件>
    Then <行为>

    Examples:
      | 事件 | 行为 |
      | 窗口 hide | CleanCache(true) 同步 |
      | 内存 LOW | CleanCache(false) 异步 |
      | 内存 HIGH | 不清 |
      | 窗口 show | ScheduleRestoreCacheTask（2s 防抖） |

  Scenario: 无 maxCacheCount 硬下限
    Given Repeat v2 内存压力回收
    When PurgeAll
    Then 回收量仅由 TemplateOptions.cachedCount per-ttype 预算约束（无 LazyForEach 的 maxCacheCount=2）
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 做 @since26 v2 内存优化；虚拟滚动基础见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScroll2Node GetOrCreateRepeatNode ENABLE_AUTO_CACHE_OPTIMIZATION 注册窗口/内存回调"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScroll2Node CleanCache PurgeAll RestoreCache TryExecuteScheduledCacheTask 2s 防抖"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScroll2Node RemovingExpiringItem pendingRemoveRids deadline 分批 与 LazyForEach maxCacheCount 对比"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/repeat.d.ts`、`frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_node.cpp`、`frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_repeat_virtual_scroll_2_impl.ts`
