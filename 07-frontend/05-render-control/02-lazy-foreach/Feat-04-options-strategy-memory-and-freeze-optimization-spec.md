# 特性规格

> Func-07-05-02-Feat-04 选项策略与内存/冻结优化：固化 `LazyForEachOptions`（`@since26`：customComponentFreezeMode/releaseStrategy/memoryOptimizationStrategy，默认 AUTO/BATCH/DEFAULT）及三枚举、`ParseOptions` 解析（number/string 双形式）、`releaseStrategy`（BATCH 同步释放 vs PROGRESSIVE 空闲分批释放）、`memoryOptimizationStrategy`（ENABLE_AUTO_CACHE_OPTIMIZATION 注册窗口/内存回调：hide 同步清/show 延迟恢复/LOW·CRITICAL 异步清/2s 防抖/maxCacheCount=2）、`customComponentFreezeMode`（AUTO 门控全局 metadata 标志、DISABLED/ENABLED 硬覆盖）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 选项策略与内存/冻结优化 |
| 特性编号 | Func-07-05-02-Feat-04 |
| 优先级 | P2 |
| 目标版本 | dynamic `@since26`（LazyForEachOptions + 三枚举）；static `@since26`（同套）+ `@since26 staticonly`（`setLazyForEachOptions` 重载） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01~03 的核心/数据侧能力；本特性聚焦 `@since26` 引入的选项策略与内存/冻结优化。拖拽排序 onMove（Feat-05）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/02-lazy-foreach/design.md` | Baselined |
| Dynamic API | `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts` | — |
| Static API | `interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets` | — |
| JS 桥接（ParseOptions/Parse*Strategy） | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach.cpp` | — |
| JS 执行器（options 结构） | `frameworks/bridge/declarative_frontend/jsview/js_lazy_foreach_actuator.h` | — |
| NG Builder（枚举/默认值/释放/清缓存） | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` / `.h` | — |
| NG 节点（窗口/内存回调/冻结） | `frameworks/core/components_ng/syntax/lazy_for_each_node.cpp` / `.h` | — |
| 全局标志 | `frameworks/core/components_ng/syntax/lazy_for_each_utils.h` / `.cpp` | — |
| metadata 读取 | `adapter/ohos/entrance/ui_content_impl.cpp` | — |

> 需求基线详见 proposal.md。design.md 与本文档增量合并，互不依赖。

---

## 用户故事

### US-1: LazyForEachOptions 与解析

**作为** 应用开发者,
**我想要** 通过第四参 `options` 配置 LazyForEach 的释放策略/冻结模式/内存优化,
**以便** 在 `@since26` 精细控制长列表的内存与冻结行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 在 `@since26` 传入第四参 `options: LazyForEachOptions`（dynamic `lazy_for_each.d.ts:1035-1040`/static `lazyForEach.static.d.ets:786-791`）THEN `ParseOptions`（`js_lazy_foreach.cpp:258-277`）读取 `customComponentFreezeMode`/`releaseStrategy`/`memoryOptimizationStrategy` 三属性并 `actuator->SetOptions`（`:355-356`） | 正常 |
| AC-1.2 | WHEN `options` 非 object（或第四参缺省）THEN `ParseOptions` 返回默认构造 `LazyForEachOptions`（`:262-264`），即 customComponentFreezeMode=AUTO、releaseStrategy=BATCH、memOptStrategy=DEFAULT | 边界 |
| AC-1.3 | WHEN 枚举值以 number 或 string 形式传入 THEN `ParseLazyForEachReleaseStrategy`/`ParseLazyForEachCustomComponentFreezeMode`/`ParseLazyForEachMemOptStrategy`（`:177-256`）均接受双形式（如 `1` 或 `"PROGRESSIVE"`），无法识别时回退默认（BATCH/AUTO/DEFAULT） | 边界 |
| AC-1.4 | WHEN static 范式 THEN 额外暴露 `LazyForEachAttribute.setLazyForEachOptions(ds,itemGen,keyGen?,options?)` 四参重载（`lazyForEach.static.d.ets:716-719`，`@since26 staticonly`），dynamic 无此方法 | 边界 |

### US-2: releaseStrategy（BATCH / PROGRESSIVE）

**作为** 应用开发者,
**我想要** 选择离屏节点释放节奏（批量 vs 逐个分批）,
**以便** 在帧预算与释放完整性间取舍。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `releaseStrategy=BATCH`（默认）THEN `PreBuild` 仅 `ProcessOffscreenNodesNotInExpiring`（`lazy_for_each_builder.cpp:812-815,829-832`）同步 detach 不在 `expiringItem_` 的离屏节点（`:843-851`） | 正常 |
| AC-2.2 | WHEN `releaseStrategy=PROGRESSIVE` THEN 额外 `CollectNodesForDelayedRelease`（`:853-861`）把不在 `expiringItem_` 的节点入 `removingNodeList_`，由 `RemovingExpiringItem`（`:1282-1302`）在帧间按 deadline 分批释放（测每节点耗时，`deadline-endTimeStamp>averageTime` 续释） | 正常 |
| AC-2.3 | WHEN `removingNodeList_` 非空 THEN `PostIdleTask` 内 `RemovingExpiringItem(deadline)`（`lazy_for_each_node.cpp:164`），未释放完则 `PostIdleTask(RELEASE_NODE)` 重投（`:165-167`） | 正常 |

### US-3: memoryOptimizationStrategy（ENABLE_AUTO_CACHE_OPTIMIZATION）

**作为** 应用开发者,
**我想要** 启用自动缓存优化，让框架按窗口可见性与内存压力回收/恢复缓存,
**以便** 后台/低内存时降低内存占用，回到前台恢复流畅。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `memoryOptimizationStrategy=ENABLE_AUTO_CACHE_OPTIMIZATION` THEN 节点创建时 `GetOrCreateLazyForEachNode`（`lazy_for_each_node.cpp:54-58`）注册 `WindowStateChangedCallback`+`MemoryLevelChangedCallback`+`PostMemOptTask`；析构时对称解注册（`:72-77`） | 正常 |
| AC-3.2 | WHEN `memoryOptimizationStrategy=DEFAULT`（缺省）THEN 不注册上述回调，沿用标准缓存行为 | 边界 |
| AC-3.3 | WHEN 窗口 hide THEN `OnWindowHide`→`CleanCache(true)`（`:855-858`）**同步**清缓存 | 正常 |
| AC-3.4 | WHEN 窗口 show THEN `OnWindowShow`→`ScheduleRestoreCacheTask`+`PostMemOptTask`（`:849-853`）**延迟恢复** | 正常 |
| AC-3.5 | WHEN 内存 level=LOW(1)/CRITICAL(2) THEN `OnNotifyMemoryLevel`→`CleanCache(false)`（`:860-865`）**异步**清 | 正常 |
| AC-3.6 | WHEN 内存 level=HIGH(0)/MODERATE THEN 不触发清缓存（仅 LOW/CRITICAL） | 边界 |
| AC-3.7 | WHEN 调度 clean/restore task THEN `TryExecuteScheduledCacheTask`（`:924-940`）须等 `CACHE_TASK_DELAY_TIME=2s`（`:30`）防抖；clean 另要求无近期 active range 变化，restore 另要求 `CheckParentFrameNodeVisibility()` 为真，否则清标志 | 边界 |
| AC-3.8 | WHEN 内存压力清缓存 THEN builder `CleanCache` 置 `reduceCache_=true`，`CheckCacheIndex` 经 `ReduceCacheCount` 把缓存范围上限压到 `maxCacheCount=2`（`:1467-1474`，前/后向 idle range 均压）；`RestoreCache` 置 `reduceCache_=false` 恢复全范围（`:1462-1465`） | 正常 |
| AC-3.9 | WHEN 启用策略且有周期 poll THEN `PostMemOptTask`（`:986-1013`）每 1000ms 检查 pipeline onShow 与父可见性变化，按可见性 schedule clean/restore（`:1002-1006`） | 正常 |

### US-4: customComponentFreezeMode（AUTO / DISABLED / ENABLED）

**作为** 应用开发者,
**我想要** 控制离屏缓存自定义组件是否冻结状态更新,
**以便** 离屏项不消耗无效更新，或按需保持活跃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 缓存离屏节点构建（`isCache=true`）THEN `GetFrameChildByIndex` 无条件 `SetJSViewActive(false,...)`（`lazy_for_each_node.cpp:437,439`）去活，与选项无关 | 正常 |
| AC-4.2 | WHEN `customComponentFreezeMode=AUTO`（默认）THEN 离屏子节点 `GetFrameChildByIndex(0,needBuild,isFreeze)` 的 `isFreeze` 取进程全局 `LazyForEachUtils::GetEnableCustomComponentFreeze()`（`:441-447`，该全局由 app metadata `enableCustomComponentFreeze=="true"` 设置，`ui_content_impl.cpp:2266-2270`） | 正常 |
| AC-4.3 | WHEN `customComponentFreezeMode=DISABLED` THEN 强制 `enableCustomComponentFreeze=false`，覆盖全局标志 | 正常 |
| AC-4.4 | WHEN `customComponentFreezeMode=ENABLED` THEN 强制 `enableCustomComponentFreeze=true`，覆盖全局标志 | 正常 |
| AC-4.5 | WHEN 应用设全局 `enableRepeatAnimation` metadata THEN 仅影响进程全局 `LazyForEachUtils::enableRepeatAnimation_`（`ui_content_impl.cpp:2271-2274`），**`LazyForEachOptions` 不暴露该字段**，无实例级覆盖 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2 | T-4 | UT：`lazy_for_each_model_test_ng` options 解析；SDK 比对 | `js_lazy_foreach.cpp:177-277`、`lazy_for_each.d.ts:226-264` |
| AC-2.1~2.3 | R-3 | T-4 | UT：`lazy_for_each_builder_syntax_test_ng(_advanced)` BATCH/PROGRESSIVE | `lazy_for_each_builder.cpp:812-861,1282-1302` |
| AC-3.1~3.9 | R-4,R-5,R-6 | T-4 | UT：`lazy_for_each_syntax_test_ng(_2)` 窗口/内存回调 + `lazy_for_each_utils_test_ng` | `lazy_for_each_node.cpp:54-58,849-1013`、`lazy_for_each_builder.cpp:1442-1494` |
| AC-4.1~4.5 | R-7,R-8 | T-4 | UT：冻结模式 + 全局标志 | `lazy_for_each_node.cpp:421-450`、`lazy_for_each_utils.h`、`ui_content_impl.cpp:2266-2274` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `@since26` 传 options 对象 | ParseOptions 读三属性并 SetOptions | 非 object→默认 AUTO/BATCH/DEFAULT | AC-1.1,AC-1.2 |
| R-2 | 边界 | 枚举值 number/string | 双形式接受，无法识别回退默认 | BATCH/AUTO/DEFAULT | AC-1.3 |
| R-3 | 行为 | releaseStrategy | BATCH 同步 ProcessOffscreenNodesNotInExpiring；PROGRESSIVE 额外 CollectNodesForDelayedRelease→RemovingExpiringItem 分批 | PROGRESSIVE 帧 deadline 分批 | AC-2.1~2.3 |
| R-4 | 行为 | memOptStrategy=ENABLE_AUTO_CACHE_OPTIMIZATION | 节点创建注册窗口/内存回调+PostMemOptTask，析构对称解注册 | DEFAULT 不注册 | AC-3.1,AC-3.2 |
| R-5 | 行为 | 窗口/内存事件 | hide→CleanCache(true)同步；show→ScheduleRestoreCacheTask延迟；LOW/CRITICAL→CleanCache(false)异步 | 仅 LOW/CRITICAL 触发清 | AC-3.3~3.6 |
| R-6 | 边界 | clean/restore 调度 | 须等 2s 防抖；clean 要求无近期 active range 变化；restore 要求父可见 | CACHE_TASK_DELAY_TIME=2s | AC-3.7 |
| R-7 | 行为 | 内存压力清缓存 | reduceCache_=true，ReduceCacheCount 压到 maxCacheCount=2；RestoreCache 恢复 | reduceCache_ 门控 CheckCacheIndex | AC-3.8 |
| R-8 | 行为 | customComponentFreezeMode | AUTO 取全局标志；DISABLED/ENABLED 硬覆盖；SetJSViewActive(false) 无条件 | 全局标志由 metadata 设置；enableRepeatAnimation 不暴露 | AC-4.1~4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x options 解析 | `lazy_for_each_model_test_ng` + SDK 比对 | 三属性、number/string 双形式、默认值、static setLazyForEachOptions |
| VM-2 | AC-2.x releaseStrategy | `lazy_for_each_builder_syntax_test_ng(_advanced)` | BATCH 同步 vs PROGRESSIVE 分批、RemovingExpiringItem deadline |
| VM-3 | AC-3.x memOpt | `lazy_for_each_syntax_test_ng(_2)` + `lazy_for_each_utils_test_ng` | 窗口/内存回调、2s 防抖、maxCacheCount=2 |
| VM-4 | AC-4.x freeze | UT + metadata 注入 | AUTO 门控全局、DISABLED/ENABLED 覆盖、enableRepeatAnimation 仅全局 |
| VM-5 | 兼容性 | XTS + d.ts/d.ets 比对 | `@since26`/`@since26 staticonly` |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `LazyForEach(...,options?: LazyForEachOptions)`（dynamic/static `@since26`） | 既有版本扩展 | options 第四参 | 三选项见 Feat-04 | AC-1.1 |
| `LazyForEachOptions` + `LazyForEachReleaseStrategy`/`LazyForEachCustomComponentFreezeMode`/`LazyForEachMemOptStrategy`（`@since26`） | 既有 | 选项与枚举 | — | AC-1.1~1.3 |
| `LazyForEachAttribute.setLazyForEachOptions(...,options?)`（static `@since26 staticonly`） | 既有 | static 范式选项设置 | dynamic 无 | AC-1.4 |

> SDK：dynamic `lazy_for_each.d.ts:30-264,1035-1040`；static `lazyForEach.static.d.ets:35-227,716-719,786-791`。

## 接口规格

### 接口定义

**LazyForEachOptions（`lazy_for_each.d.ts:226`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `interface LazyForEachOptions { customComponentFreezeMode?: LazyForEachCustomComponentFreezeMode; releaseStrategy?: LazyForEachReleaseStrategy; memoryOptimizationStrategy?: LazyForEachMemOptStrategy; }` |
| 返回值 | — |
| 开放范围 | Public（`@since26`） |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| customComponentFreezeMode | enum | 否 | AUTO(0) | AUTO/DISABLED(1)/ENABLED(2)；number 或 string |
| releaseStrategy | enum | 否 | BATCH(0) | BATCH(0)/PROGRESSIVE(1) |
| memoryOptimizationStrategy | enum | 否 | DEFAULT(0) | DEFAULT(0)/ENABLE_AUTO_CACHE_OPTIMIZATION(1<<0) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | releaseStrategy=PROGRESSIVE | CollectNodesForDelayedRelease→RemovingExpiringItem 分批释放 | AC-2.2 |
| 2 | 窗口 hide（memOpt 启用） | CleanCache(true) 同步清 | AC-3.3 |
| 3 | 内存 CRITICAL | CleanCache(false) 异步清 + reduceCache 压到 2 | AC-3.5,AC-3.8 |
| 4 | customComponentFreezeMode=ENABLED | 离屏子 isFreeze=true 覆盖全局 | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。options 全部为 `@since26` 新增，低版本无该第四参。
- **配置文件格式变更:** 否（仅 app metadata `enableCustomComponentFreeze`/`enableRepeatAnimation` 既有读取）。
- **数据存储格式变更:** 否。
- **最低支持版本:** `@since26`（dynamic/static）。
- **API 版本号策略:** 按 SDK `@since26`/`@since26 staticonly` 标注。

> **全局 vs 实例标志风险：** `customComponentFreezeMode` 实例选项**不替换**而是**门控**进程全局 `LazyForEachUtils::enableCustomComponentFreeze_`（metadata 驱动）；AUTO 用全局、DISABLED/ENABLED 硬覆盖（风险 RISK-F4-1）。`enableRepeatAnimation_` 仅全局、不暴露实例选项（风险 RISK-F4-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| options 解析双形式 | 枚举值 number/string 均接受，无法识别回退默认 | AC-1.3 |
| 内存优化回调需启用 | 仅 ENABLE_AUTO_CACHE_OPTIMIZATION 注册窗口/内存回调 | AC-3.1,AC-3.2 |
| 缓存回收防抖 | clean/restore 须 2s 防抖 + 可见性/active-range 前置 | AC-3.7 |
| 冻结门控全局 | 实例选项门控而非替换全局 metadata 标志 | AC-4.2~4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 内存 | ENABLE_AUTO_CACHE_OPTIMIZATION 后台/低内存回收缓存，maxCacheCount=2 | UT + 内存 dump | `lazy_for_each_node.cpp:849-965`、`lazy_for_each_builder.cpp:1467-1474` |
| 性能 | PROGRESSIVE 分批释放不阻塞当前帧 | UT + benchmark | `lazy_for_each_builder.cpp:1282-1302` |
| 功耗 | freeze 离屏自定义组件减少无效状态更新 | UT | `lazy_for_each_node.cpp:441-447` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 选项一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 是 | 内存压力更易触发 ReduceCacheCount | XTS | `lazy_for_each_builder.cpp:1467-1474` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 无直接关联 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 是 | 窗口 hide/show 触发 CleanCache/RestoreCache（memOpt 启用时） | AC-3.3,AC-3.4 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | options 全部 `@since26` | AC-1.1 |
| 生态兼容 | 是 | dynamic/static `@since26` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 选项策略与内存/冻结优化
  作为 应用开发者
  我想要 通过 options 控制释放/冻结/内存优化
  以便 长列表内存与活跃度可控

  Scenario Outline: releaseStrategy 释放节奏
    Given releaseStrategy = <策略>
    When PreBuild 到达 deadline
    Then <行为>

    Examples:
      | 策略 | 行为 |
      | BATCH | 同步 ProcessOffscreenNodesNotInExpiring 释放 |
      | PROGRESSIVE | 额外 CollectNodesForDelayedRelease，帧间 RemovingExpiringItem 分批 |

  Scenario: 内存压力回收
    Given memoryOptimizationStrategy = ENABLE_AUTO_CACHE_OPTIMIZATION
    When 系统内存 level = CRITICAL
    Then CleanCache(false) 异步清，缓存范围压到 maxCacheCount=2
    And 窗口 show 后经 2s 防抖 RestoreCache 恢复

  Scenario Outline: customComponentFreezeMode
    Given customComponentFreezeMode = <模式>
    When 构建离屏缓存子节点
    Then <冻结>

    Examples:
      | 模式 | 冻结 |
      | AUTO | 取全局 metadata 标志 |
      | DISABLED | 强制不冻结（覆盖全局） |
      | ENABLED | 强制冻结（覆盖全局） |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 做 `@since26` options 三策略；onMove 见 Feat-05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachBuilder PreBuild releaseStrategy BATCH vs PROGRESSIVE CollectNodesForDelayedRelease"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachNode ENABLE_AUTO_CACHE_OPTIMIZATION OnWindowHide/OnWindowShow/OnNotifyMemoryLevel CleanCache/RestoreCache"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachNode GetFrameChildByIndex customComponentFreezeMode AUTO 门控 LazyForEachUtils 全局标志"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts`、`interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets`、`frameworks/core/components_ng/syntax/lazy_for_each_node.cpp`、`frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp`、`frameworks/core/components_ng/syntax/lazy_for_each_utils.h`
