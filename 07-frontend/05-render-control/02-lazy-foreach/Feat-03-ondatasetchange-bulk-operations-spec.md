# 特性规格

> Func-07-05-02-Feat-03 批量数据集变更 onDatasetChange：固化 `onDatasetChange(dataOperations)`（`@since12` dynamic / `@since23` static，stage-model-only）入口与单条 API 互斥守卫（per-instance sticky 双向、`ERROR_CODE_PARAM_INVALID`）、`DataOperation` 联合与 `DataOperationType`（ADD/DELETE/CHANGE/MOVE/EXCHANGE/RELOAD）六类型语义、同回调规则（RELOAD 短路、same-index-first 静默丢弃、越界 index 静默无效、ADD keys>count 抛错）、index 修复归一化（CollectIndexChangedCount/RepairDatasetItems/RepairMoveOrExchange）、RELOAD op 的 `reuseImmediately`（`@since26.1` dynamic-only，static 缺失）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 批量数据集变更 onDatasetChange |
| 特性编号 | Func-07-05-02-Feat-03 |
| 优先级 | P1 |
| 目标版本 | dynamic `@since12`（onDatasetChange/DataOperationType/6 Data*Operation/MoveIndex/ExchangeIndex/ExchangeKey）；`@since26.1`（DataReloadOperation.reuseImmediately，dynamic-only）；static `@since23`（同套类型，无 reuseImmediately） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-02 单条变更通知；本特性聚焦批量 `onDatasetChange` 与其互斥/短路/修复规则。选项策略与内存优化（Feat-04）、拖拽排序 onMove（Feat-05）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/02-lazy-foreach/design.md` | Baselined |
| Dynamic API（SDK 契约） | `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts` | — |
| Static API（SDK 契约） | `interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets` | — |
| JS 变更监听代理（onDatasetChange 入口/解析/互斥） | `frameworks/bridge/declarative_frontend/jsview/js_data_change_listener.h` | — |
| NG 语法节点（OnDatasetChange/ParseOperations） | `frameworks/core/components_ng/syntax/lazy_for_each_node.cpp` / `.h` | — |
| NG 缓存引擎（OnDatasetChange/ClassifyOperation/Operate*/Repair*） | `frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp` / `.h` | — |
| 数据源契约 C++ 接口（V2::Operation） | `frameworks/core/components_v2/foreach/lazy_foreach_component.h` | — |

> 需求基线详见 proposal.md。design.md 与本文档增量合并，互不依赖。

---

## 用户故事

### US-1: onDatasetChange 入口与互斥

**作为** 应用开发者,
**我想要** 用一次 `onDatasetChange(ops)` 通知多条批量数据变更,
**以便** 用单次回调表达增删改移换/重载组合，减少多次单条通知的开销。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `onDatasetChange(dataOperations)`（`@since12` dynamic，stage-model-only）THEN `JSDataChangeListener::OnDatasetChange`（`js_data_change_listener.h:166-175`）置 `useNewInterface=true`，校验入参为单个数组（`args.Length()==1 && IsArray`），否则静默 no-op（`:173-175`） | 正常 |
| AC-1.2 | WHEN 入参为数组 THEN 遍历元素，仅 object 元素经 `TransferJSInfoType` 转 `V2::Operation` 入 `DataOperations` 列表（`:176-183`），非 object 元素静默跳过（`:179`） | 边界 |
| AC-1.3 | WHEN 同一 `JSDataChangeListener` 实例已用过单条 API（`useOldInterface=true`）后再调 `onDatasetChange`（或反之）THEN 粘性守卫 `UseAnotherInterface` 抛 `ERROR_CODE_PARAM_INVALID`「onDatasetChange cannot be used with other interface」并 no-op（`:168-171,316-324`）；不同 LazyForEach 实例监听器独立、互不影响 | 异常 |
| AC-1.4 | WHEN 任一 `onDatasetChange` 触发 THEN 经 `NotifyAll`（`:336-351`）派发到 `LazyForEachNode::OnDatasetChange`（`lazy_for_each_node.cpp:372-412`），置 `builder_->SetUseNewInterface(true)`（`:377`），收尾 `MarkNeedSyncRenderTree(true)`+`MarkNeedFrameFlushDirty(PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT)`（`:410-411`） | 正常 |

### US-2: 六种 DataOperation 类型语义

**作为** 应用开发者,
**我想要** 用 ADD/DELETE/CHANGE/MOVE/EXCHANGE/RELOAD 六种操作类型表达批量变更,
**以便** 精确描述数据集的结构性变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN op `type=ADD`（`DataAddOperation`，`lazy_for_each.d.ts:275-323`）THEN `ClassifyOperation` 派发 `OperateAdd`（`lazy_for_each_builder.cpp:533,571-592`）；字段 `index`（必填）、`count?`（默认 1）、`key?: string\|Array<string>` | 正常 |
| AC-2.2 | WHEN op `type=DELETE`（`DataDeleteOperation`，`:334-371`）THEN 派发 `OperateDelete`（`:536,594-618`）；批量删除占用 `index..index+count-1`，每 index 独立冲突检查（`:606-614`） | 正常 |
| AC-2.3 | WHEN op `type=CHANGE`（`DataChangeOperation`，`:382-416`）THEN 派发 `OperateChange`（`:539,620-647`），对应 index 节点置 null 强制重建（`RepairDatasetItems` `:467-468`） | 正常 |
| AC-2.4 | WHEN op `type=MOVE`（`DataMoveOperation`，`index: MoveIndex{from,to}`，`:529-563`）THEN 派发 `OperateMove`（`:542,649-690`），from/to 两端各自 first-wins 冲突检查（`:658-689`） | 正常 |
| AC-2.5 | WHEN op `type=EXCHANGE`（`DataExchangeOperation`，`index: ExchangeIndex{start,end}`、`key?: ExchangeKey{start,end}`，`:574-608`）THEN 派发 `OperateExchange`（`:545,692-741`），start/end 两端各自 first-wins（`:701-740`） | 正常 |
| AC-2.6 | WHEN op `type=RELOAD`（`DataReloadOperation`，`:621-651`）THEN 派发 `OperateReload(expiringTemp, operation.reuseImmediately)`（`:548-549,756-763`），把 expiringTemp 移回 `expiringItem_`、清 `operationList_`、调 `OnDataReloaded(reuseImmediately)`（`:762`） | 正常 |

### US-3: 同回调规则（短路 / 同 index / 越界 / keys 计数）

**作为** 应用开发者,
**我想要** 了解同一次 `onDatasetChange` 内多 op 的优先与冲突规则,
**以便** 正确构造操作序列、避免无效操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 同一次回调中含任意 RELOAD op THEN `OnDatasetChange` 遇 RELOAD 立即 `return`（`lazy_for_each_builder.cpp:424-427`），**该回调内其余所有 op 失效**；框架调 `keyGenerator` 做 key 比较（SDK `lazy_for_each.d.ts:611-613`） | 边界 |
| AC-3.2 | WHEN 同一次回调中多个 op 命中同一 index THEN 以 `operationList_`（`map<index,OperationInfo>`，`lazy_for_each_builder.h:354`）first-wins，后续命中该 index 的 op 调 `ThrowRepeatOperationError` 仅 `TAG_LOGE(ACE_LAZY_FOREACH,"Repeat Operation for index")` 静默丢弃，**不抛异常**（`lazy_for_each_builder.cpp:577-591,765-768`） | 异常 |
| AC-3.3 | WHEN op 的 index 越界 THEN `ValidateIndex` 判定无效：ADD 允许 `index == totalCount`（追加），其余要求 `0 <= index < totalCount`；越界 op 输出 `"<type>(<index>) Operation is out of range"` 错误日志并跳过，**不抛异常**（`:555-569`；SDK `lazy_for_each.d.ts:679-681`） | 异常 |
| AC-3.4 | WHEN ADD op 的 `key` 数量 > `count` THEN 置 `allocateMoreKeys=true`，回调末尾抛 `ERROR_CODE_PARAM_INVALID`「The number of key is more than count for ADD operation」（`js_data_change_listener.h:184-187,274-277`） | 异常 |
| AC-3.5 | WHEN op 类型字符串非法（非六种之一）THEN `ClassifyOperation` 的 `operationTypeMap[operation.type]` 未命中默认分支，该 op 不产生 Operate* 调用（`lazy_for_each_builder.cpp:532`） | 边界 |

### US-4: index 修复归一化与 RELOAD 的 reuseImmediately

**作为** 应用开发者,
**我想要** 多 op 叠加后 index 自动归一化，并可在 RELOAD 时触发立即回收,
**以便** 批量操作后缓存节点落位正确、大规模重载离屏节点交父复用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 非 RELOAD op 全部分类入 `operationList_` 后 THEN `CollectIndexChangedCount`（`lazy_for_each_builder.cpp:514-527`）按 ADD +count/DEL -count/MOVE from -1·to +1 累积 `changeCount`，并回填 gap index 构造 `indexChangedMap`（cumulative delta） | 正常 |
| AC-4.2 | WHEN 累积 delta 构造完成 THEN `RepairDatasetItems`（`:441-486`）对每个缓存/离屏节点按 `index+changedIndex` 重定位；`isDeleting` 入 nodeList 移除、`isChanged` 置 null 重建、`extraKey` 插入新 key 槽、`moveIn\|isExchange` 走 `RepairMoveOrExchange`（`:488-512`） | 正常 |
| AC-4.3 | WHEN MOVE/EXCHANGE 修复 THEN `RepairMoveOrExchange` 按 `fromDiffTo`（`OperateMove:679 = coupleIndex.first-second`）决定位移方向；Exchange 与 null 节点交换时既有子入 nodeList 删除（`:491-511`） | 边界 |
| AC-4.4 | WHEN RELOAD op 携带 `reuseImmediately`（dynamic `@since26.1`，`DataReloadOperation.reuseImmediately`，`lazy_for_each.d.ts:650`）THEN `TransferReuseImmediately`（`js_data_change_listener.h:223-225,306-314`）解析为 `Operation.reuseImmediately`，经 `OperateReload`→`OnDataReloaded(reuseImmediately)`（`:549,762`）走 Feat-02 的 key 后缀立即回收机制 | 正常 |
| AC-4.5 | WHEN static 范式使用 RELOAD THEN `DataReloadOperation`（`lazyForEach.static.d.ets:518-528`）**仅含 `type`，无 `reuseImmediately` 字段**（该字段 dynamic-only `@since26.1`）——dynamic/static 差异 | 边界 |
| AC-4.6 | WHEN OnDatasetChange 完成 THEN `ParseOperations`（`lazy_for_each_node.cpp:799-835`）按 op 类型发 `NotifyChangeWithCount(...,END_CHANGE_POSITION)` 无障碍/父通知（不修改子节点），RELOAD 取 `max(GetHistoryTotalCount, FrameCount)` 作 endChangePos（`:827-830`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2,R-8 | T-3 | UT：`lazy_for_each_builder_syntax_test_ng(_advanced)` onDatasetChange 入口/互斥 | `js_data_change_listener.h:166-351`、`lazy_for_each_node.cpp:372-412` |
| AC-2.1~2.6 | R-3 | T-3 | UT：六 op 类型 ClassifyOperation/Operate* 派发 | `lazy_for_each_builder.cpp:529-763`、SDK `:275-651` |
| AC-3.1~3.5 | R-4,R-5,R-6,R-9 | T-3 | UT：RELOAD 短路/same-index/越界/keys>count | `lazy_for_each_builder.cpp:424-427,555-591,765-768`、`js_data_change_listener.h:184-187` |
| AC-4.1~4.6 | R-7,R-10,R-11 | T-3 | UT：CollectIndexChangedCount/RepairDatasetItems + reuseImmediately dataset 路径 | `lazy_for_each_builder.cpp:441-527`、`js_data_change_listener.h:306-314` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 onDatasetChange(单数组) | 解析 object 元素为 Operation 列表，NotifyAll 派发，置 SetUseNewInterface(true)+MEASURE_SELF_AND_PARENT | 非单数组静默 no-op；非 object 跳过 | AC-1.1,AC-1.2,AC-1.4 |
| R-2 | 异常 | 同实例单条与 onDatasetChange 混用 | 粘性守卫抛 ERROR_CODE_PARAM_INVALID 并 no-op | 双向、per-instance、跨实例独立 | AC-1.3 |
| R-3 | 行为 | op type∈{ADD,DELETE,CHANGE,MOVE,EXCHANGE,RELOAD} | ClassifyOperation 派发对应 Operate* | 非法 type 不派发 | AC-2.1~2.6,AC-3.5 |
| R-4 | 边界 | 同回调含 RELOAD | 遇 RELOAD 立即 return，其余 op 失效 | RELOAD 触发 keyGenerator 比较 | AC-3.1 |
| R-5 | 异常 | 多 op 命中同 index | operationList_ first-wins，后续 ThrowRepeatOperationError 静默丢弃 | 仅 TAG_LOGE，不抛异常 | AC-3.2 |
| R-6 | 异常 | op index 越界 | ValidateIndex 判定无效+错误日志跳过 | ADD 允许 index==totalCount | AC-3.3 |
| R-7 | 行为 | 非 RELOAD op 全分类后 | CollectIndexChangedCount 累积 delta + RepairDatasetItems 重定位 | gap 回填 | AC-4.1,AC-4.2,AC-4.3 |
| R-8 | 异常 | ADD key 数量>count | 抛 ERROR_CODE_PARAM_INVALID | allocateMoreKeys 标志 | AC-3.4 |
| R-9 | 边界 | RELOAD op reuseImmediately（dynamic @since26.1） | 经 OperateReload→OnDataReloaded(reuseImmediately) 走 Feat-02 后缀机制 | static 缺该字段 | AC-4.4,AC-4.5 |
| R-10 | 行为 | OnDatasetChange 完成 | ParseOperations 发 END_CHANGE_POSITION 通知（不改子节点） | RELOAD endPos=max(history,frame) | AC-4.6 |
| R-11 | 边界 | static 范式 RELOAD | DataReloadOperation 仅 type，无 reuseImmediately | dynamic-only @since26.1 差异 | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x 入口/互斥 | `lazy_for_each_builder_syntax_test_ng(_advanced)` | 单数组校验、per-instance 互斥、ERROR_CODE_PARAM_INVALID |
| VM-2 | AC-2.x 六 op 类型 | UT + SDK d.ts 比对 | ClassifyOperation→Operate* 派发、字段约束 |
| VM-3 | AC-3.x 同回调规则 | UT | RELOAD 短路、same-index-first 静默、越界静默、keys>count 抛错 |
| VM-4 | AC-4.x 修复/reuseImmediately | UT | CollectIndexChangedCount/RepairDatasetItems、dataset RELOAD reuseImmediately 路径、static 缺字段 |
| VM-5 | 兼容性/版本矩阵 | XTS + d.ts/d.ets 比对 | `@since12`/`@since23`/`@since26.1` dynamic-only reuseImmediately |

## API 变更分析

> 存量补录，无新增/变更 API。下列为本特性覆盖的既有 API 清单。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `DataChangeListener.onDatasetChange(dataOperations)`（dynamic `@since12`/static `@since23`） | 既有 | 批量变更入口，stage-model-only | 与单条 API 互斥 | AC-1.1~1.4 |
| `DataOperationType`（ADD/DELETE/EXCHANGE/MOVE/CHANGE/RELOAD） | 既有 | op 类型枚举 | — | AC-2.1~2.6 |
| `DataAddOperation`/`DataDeleteOperation`/`DataChangeOperation`/`DataMoveOperation`/`DataExchangeOperation`/`DataReloadOperation` + `MoveIndex`/`ExchangeIndex`/`ExchangeKey` | 既有 | op 结构 | — | AC-2.1~2.6 |
| `DataReloadOperation.reuseImmediately`（dynamic `@since26.1`） | 既有版本扩展 | RELOAD 立即回收 | static 缺该字段；复用 Feat-02 机制 | AC-4.4,AC-4.5 |

> SDK 契约：dynamic `lazy_for_each.d.ts:64-131,275-671,867-886`；static `lazyForEach.static.d.ets:61-544,613`。

## 接口规格

### 接口定义

**onDatasetChange（dynamic，`lazy_for_each.d.ts:886`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onDatasetChange(dataOperations: DataOperation[]): void` |
| 返回值 | void |
| 开放范围 | Public（`@since12`，stage-model-only） |
| 错误码 | 混用单条→`ERROR_CODE_PARAM_INVALID`；ADD keys>count→`ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-1.1~1.4,AC-3.4 |

**DataOperation 联合（`lazy_for_each.d.ts:670`）**

```
DataOperation = DataAddOperation | DataDeleteOperation | DataChangeOperation
              | DataMoveOperation | DataExchangeOperation | DataReloadOperation
```

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| dataOperations | `DataOperation[]` | 是 | — | 单数组；非 object 元素跳过；含 RELOAD 则其余失效 |
| DataAddOperation.index/count/key | number/number/string\|string[] | index 必填 | count=1 | key 数量≤count，否则抛错 |
| DataDeleteOperation.index/count | number/number | index 必填 | count=1 | 越界（index≥totalCount）静默无效 |
| DataMoveOperation.index | MoveIndex{from,to} | 是 | — | from/to 各自 first-wins |
| DataExchangeOperation.index/key | ExchangeIndex/ExchangeKey | index 必填 | — | start/end 各自 first-wins |
| DataReloadOperation.reuseImmediately | boolean | 否 | false | dynamic `@since26.1`，static 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 单条后调 onDatasetChange | 抛 ERROR_CODE_PARAM_INVALID 并 no-op | AC-1.3 |
| 2 | 回调含 RELOAD | 其余 op 全失效，走 keyGenerator 比较 | AC-3.1 |
| 3 | 两 op 命中同 index | 首个生效，后续静默丢弃（Repeat Operation 日志） | AC-3.2 |
| 4 | op index 越界 | 该 op 静默无效 + 错误日志 | AC-3.3 |
| 5 | ADD key 数>count | 抛 ERROR_CODE_PARAM_INVALID | AC-3.4 |
| 6 | RELOAD reuseImmediately=true | 经 OperateReload→OnDataReloaded(true) 走 Feat-02 后缀回收 | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。既有行为：onDatasetChange 与单条 API 在同实例互斥（双向 sticky）；RELOAD 短路；same-index/越界静默处理；ADD keys>count 抛错。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since12`；static `@since23`。
- **API 版本号策略:** 按 SDK `@since` 标注；`DataReloadOperation.reuseImmediately` 为 **dynamic-only `@since26.1`**，static `DataReloadOperation`（`lazyForEach.static.d.ets:518-528`）无此字段（dynamic/static 差异，风险 RISK-F3-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 互斥 per-instance | onDatasetChange 与单条 API 在同一 JSDataChangeListener 实例上互斥；跨实例独立 | AC-1.3 |
| RELOAD 短路 | 同回调含 RELOAD 则其余 op 全失效 | AC-3.1 |
| first-wins 同 index | operationList_ 按 index first-wins，后续静默丢弃 | AC-3.2 |
| index 归一化 | 多 op 叠加经 CollectIndexChangedCount/RepairDatasetItems 重定位 | AC-4.1~4.3 |
| dynamic-only reuseImmediately | RELOAD 立即回收仅 dynamic `@since26.1` | AC-4.4,AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 批量 onDatasetChange 单次回调优于多次单条通知 | UT + benchmark | `lazy_for_each_builder.cpp:405-486` |
| 可靠性 | 越界/同 index/非法 type 不崩溃（静默或抛 JS 异常） | UT 异常用例 | `lazy_for_each_builder.cpp:555-591,765-768` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | ParseOperations 发 END_CHANGE_POSITION 通知父/无障碍 | AC-4.6 |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | `@since12`/`@since23`/`@since26.1` dynamic-only reuseImmediately | AC-4.4,AC-4.5 |
| 生态兼容 | 是 | stage-model-only（dynamic）；static `@since23` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: onDatasetChange 批量变更与同回调规则
  作为 应用开发者
  我想要 用单次 onDatasetChange 表达批量数据变更
  以便 减少多次单条通知开销且语义精确

  Scenario: RELOAD 短路
    Given 一次 onDatasetChange 含 [ADD, RELOAD, DELETE]
    When 框架处理该回调
    Then 仅 RELOAD 生效，ADD/DELETE 失效，框架调 keyGenerator 比较

  Scenario Outline: 同 index 与越界处理
    Given 一次 onDatasetChange
    When 含 <操作>
    Then <结果>

    Examples:
      | 操作 | 结果 |
      | 两个 ADD 命中 index=3 | 首个生效，第二个静默丢弃（Repeat Operation 日志） |
      | DELETE index=99（越界） | 该 op 静默无效 + out of range 错误日志 |
      | ADD index=count（追加） | 允许，追加到末尾 |

  Scenario: 互斥守卫
    Given 同一监听器实例已调用 onDataAdd
    When 再调用 onDatasetChange
    Then 抛 ERROR_CODE_PARAM_INVALID 并 no-op

  Scenario: ADD keys 多于 count
    Given ADD op count=1 但 key=[a,b]
    When 框架解析
    Then 抛 ERROR_CODE_PARAM_INVALID「The number of key is more than count for ADD operation」
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做 onDatasetChange 批量变更及规则；单条通知见 Feat-02；reuseImmediately 机制本体见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachBuilder::OnDatasetChange RELOAD 短路与 ClassifyOperation Operate* 派发"
  - repo: "openharmony/arkui_ace_engine"
    query: "LazyForEachBuilder operationList_ same-index first-wins ThrowRepeatOperationError"
  - repo: "openharmony/arkui_ace_engine"
    query: "CollectIndexChangedCount RepairDatasetItems RepairMoveOrExchange index 归一化"
  - repo: "openharmony/arkui_ace_engine"
    query: "DataReloadOperation reuseImmediately TransferReuseImmediately OperateReload 链路"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/lazy_for_each.d.ts`、`interface/sdk-js/api/arkui/component/lazyForEach.static.d.ets`、`frameworks/core/components_ng/syntax/lazy_for_each_builder.cpp`、`frameworks/bridge/declarative_frontend/jsview/js_data_change_listener.h`
