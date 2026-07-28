# 特性规格

> Func-07-05-03-Feat-03 Repeat 模板化渲染与复用：固化 `.template(type,itemBuilder,TemplateOptions?)`/`.templateId(typedFunc)`（`@since12` dynamic / `@since23` static）、`TemplateOptions.cachedCount`（per-ttype 池上限）、`TemplateTypedFunc<T>`、ttype 决策（`templateId` 装 item→ttype 映射、未知 ttype 回退 `each`）、v2 TS 侧 per-ttype 簿记（C++ 仅 flat RID→CacheItem）、`SetCreateByTemplate`→`SetAllowReusableV2Descendant` 禁用模板内 `@ReusableV2` 复用行为规格。**v1 原生 per-ttype 节点池已废弃（见 US-3/R-5）。**

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Repeat 模板化渲染与复用 |
| 特性编号 | Func-07-05-03-Feat-03 |
| 优先级 | P2 |
| 目标版本 | dynamic `@since12`（template/templateId/TemplateOptions/TemplateTypedFunc）；static `@since23`（同套） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。承接 Feat-01（核心语法）/Feat-02（虚拟滚动）；本特性聚焦多模板渲染与 per-ttype 复用。内存优化（Feat-04）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/03-repeat/design.md` | Baselined |
| Dynamic API | `interface/sdk-js/api/@internal/component/ets/repeat.d.ts` | — |
| Static API | `interface/sdk-js/api/arkui/component/repeat.static.d.ets` | — |
| TS 模板逻辑 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_repeat.ts` | — |
| TS v1/v2 ttype 决策 | `pu_repeat_virtual_scroll_2_impl.ts`（v2；v1 `pu_repeat_virtual_scroll_impl.ts` 已废弃） | — |
| v1 JS 桥接（templateCachedCountMap，已废弃） | `frameworks/bridge/declarative_frontend/jsview/js_repeat_virtual_scroll.cpp` | **已废弃** |
| v1/v2 Model（SetCreateByTemplate） | `repeat_virtual_scroll_model_ng.cpp`（v1，已废弃）/ `repeat_virtual_scroll_2_model_ng.cpp`（v2） | — |
| v1 缓存（per-ttype 池，已废弃） | `frameworks/core/components_ng/syntax/repeat_virtual_scroll_caches.h` / `.cpp` | **已废弃** |
| UINode 复用标志 | `frameworks/core/components_ng/base/ui_node.h` / `.cpp`、`view_partial_update_model_ng.cpp` | — |

> 需求基线详见 proposal.md。design.md 与本文档增量合并，互不依赖。

---

## 用户故事

### US-1: template / templateId 注册

**作为** 应用开发者,
**我想要** 用 `.template(type,itemBuilder,options)` 注册多套模板、`.templateId(typedFunc)` 指定 item→模板映射,
**以便** 异构数据项用不同模板渲染并按类型复用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 链式 `.template(ttype,itemBuilder,templateOptions?)`（dynamic `repeat.d.ts:397`/static `:262` `@since12/23`）THEN `config.itemGenFuncs[ttype]=itemBuilder`+`config.templateOptions[ttype]=normTemplateOptions(options)`（`pu_repeat.ts:267-273`）；多次 `.template()` 累积不同 ttype 键 | 正常 |
| AC-1.2 | WHEN 链式 `.templateId(typedFunc)`（dynamic `:414`/static `:273` `@since12/23`）THEN `config.ttypeGenFunc=typedFunc`（`pu_repeat.ts:261-264`），存 item→ttype 映射函数（per-item 调用） | 正常 |
| AC-1.3 | WHEN `.each(itemGenFunc)` THEN 注册到保留 ttype `''`（`RepeatEachFuncTtype`，`pu_repeat.ts:173,207-211`）；`templateId` 返回无匹配时回落 `each`（`repeat.d.ts:342` 文档） | 正常 |
| AC-1.4 | WHEN `TemplateOptions.cachedCount` 提供（dynamic `:276`/static `:204` `@since12/23`）THEN 经 `normTemplateOptions` 校验 `Number.isInteger && >=0`，产 `{cachedCount:max(0,n),cachedCountSpecified:true}`（`pu_repeat.ts:314-324`）；范围 `[0,+∞)`，默认=显示区+预加载区数且不递减（SDK `:263-268`） | 正常 |

### US-2: ttype 决策与回退

**作为** 应用开发者,
**我想要** 每项按 ttypeGenFunc 选模板，未知 ttype 安全回退,
**以便** 数据驱动多模板且不因未知类型崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ttypeGenFunc===undefined` THEN v2 `computeTtype(item,index)` 返回 `''`（`pu_repeat_virtual_scroll_2_impl.ts:878-899`） | 正常 |
| AC-2.2 | WHEN 用户 ttypeGenFunc 返回的 ttype 不在 `itemGenFuncs` THEN 日志 "No template found for ttype" 并回退 `''`（v2 `:878-899`） | 异常 |
| AC-2.3 | WHEN 用户 ttypeGenFunc 抛异常 THEN try/catch 捕获并回退 `''`（v2） | 异常 |
| AC-2.4 | WHEN v2 `onGetRid4Index` 处理 item THEN `computeTtype(item,index,monitorAccess)` 决定 ttype（`pu_repeat_virtual_scroll_2_impl.ts:988`），rebuild 路径同（`:711`） | 正常 |

### US-3: v1 原生 per-ttype 节点池（已废弃）

> **v1 已废弃：** `RepeatVirtualScrollNode`（v1）整体已废弃，其 per-ttype 节点池（`node4key4ttype_`/`cacheCountL24ttype_`/`ttype4index_`/`templateCachedCountMap`/`GetL2KeyToUpdate`/per-ttype `Purge`）随之废弃，源码保留但不演进。本 US 不再展开 AC（详见 Feat-02 废弃声明与 R-5）。模板 per-ttype 复用以 v2 TS 侧簿记（US-4）为准。

### US-4: v2 TS 侧 per-ttype 簿记 + SetCreateByTemplate

**作为** 应用开发者（API≥16/master 路径）,
**我想要** v2 ttype 簿记在 TS、模板内 @ReusableV2 复用被禁用,
**以便** Repeat ttype 池为唯一复用路径，避免与 @ReusableV2 冲突。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN v2 模板信息 THEN `templateOptions_`/`itemGenFuncs_` 全在 TS 侧（`pu_repeat_virtual_scroll_2_impl.ts:306,488,1026-1032`），ttype 按 RID 经 `RIDMeta.ttype_` 跟踪（`:1170,1049`） | 正常 |
| AC-4.2 | WHEN v2 C++ 缓存 THEN 仅 flat `cacheItem4Rid_`（RID→CacheItem），**无** `node4key4ttype_`/`cacheCountL24ttype_`/`ttype4index_`（grep 确认 v2 C++ 无 per-ttype 结构） | 边界 |
| AC-4.3 | WHEN v2 spare-RID 匹配 THEN 按 ttype 在 TS `canUpdate`/`canUpdateTryMatch`（`:1043-1066,1070-1090`）完成 | 正常 |
| AC-4.4 | WHEN v2 创建模板子节点（`isTemplate=true`，ttype≠`''`）THEN `RepeatVirtualScroll2Native.setCreateByTemplate(true)`（`pu_repeat_virtual_scroll_2_impl.ts:1152-1154`）→`SetCreateByTemplate(true)`→`SetAllowReusableV2Descendant(false)`（`repeat_virtual_scroll_2_model_ng.cpp:136-142`） | 正常 |
| AC-4.5 | WHEN `SetAllowReusableV2Descendant(false)` THEN `AllowReusableV2Descendant`（`view_partial_update_model_ng.cpp:125-147`）沿父链遇 RepeatVirtualScroll(2)Node 时返回该标志——禁用模板内 `@ReusableV2` 按 reuseId 复用，Repeat ttype 池为唯一复用路径（`ui_node.h:1001-1008`） | 正常 |
| AC-4.6 | WHEN 子节点由 `.each()`（ttype=`''`，`isTemplate=false`）创建 THEN `SetAllowReusableV2Descendant(true)`（默认），允许 `@ReusableV2` 复用 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2 | T-3 | UT + SDK 比对 | `repeat.d.ts:260-414`、`pu_repeat.ts:173-324` |
| AC-2.1~2.4 | R-3,R-4 | T-3 | TS 单测 | `pu_repeat_virtual_scroll_2_impl.ts:878-999`（v1 文件已废弃） |
| AC-3.x（v1，已废弃） | R-5 | T-3 | v1 per-ttype 池已废弃，不再验证（详见 US-3） | v1 文件已废弃 |
| AC-4.1~4.6 | R-6,R-7,R-8 | T-3 | UT：v2 TS 簿记 + SetCreateByTemplate | `repeat_virtual_scroll_2_model_ng.cpp:136-142`、`view_partial_update_model_ng.cpp:125-147` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `.template(ttype,itemBuilder,options)` | 注册 itemGenFuncs[ttype]+templateOptions[ttype] | 多次累积；ttype 任意字符串 | AC-1.1 |
| R-2 | 行为 | `.templateId(typedFunc)` | 装 item→ttype 映射；TemplateOptions.cachedCount per-ttype 上限 `[0,+∞)` | 默认=显示+预加载，不递减 | AC-1.2,AC-1.4 |
| R-3 | 行为 | `.each()` | 注册保留 ttype `''`；templateId 无匹配回落 each | each 仍 mandatory | AC-1.3 |
| R-4 | 异常 | ttypeGenFunc 返回未知 ttype 或抛错 | 日志+回退 `''` | try/catch 捕获 | AC-2.2,AC-2.3 |
| R-5 | 行为 | ~~v1 per-ttype 池~~（已废弃） | ~~node4key4ttype_ 分池、cacheCountL24ttype_ 各上限、ttype 匹配复用~~ | v1 整体已废弃，详见 Feat-02 废弃声明 | AC-3.x（已废弃） |
| R-6 | 边界 | v2 per-ttype 簿记位置 | TS 侧（templateOptions_/itemGenFuncs_/RIDMeta.ttype_），C++ 仅 flat RID→CacheItem | v2 C++ 无 per-ttype 结构 | AC-4.1,AC-4.2 |
| R-7 | 行为 | v2 模板子节点创建 | setCreateByTemplate(true)→SetAllowReusableV2Descendant(false) | ttype≠'' | AC-4.4 |
| R-8 | 行为 | AllowReusableV2Descendant=false | 禁用模板内 @ReusableV2 reuseId 复用，Repeat ttype 池唯一 | each 子节点允许 | AC-4.5,AC-4.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x template 注册 | UT + SDK 比对 | ttype 键、TemplateOptions.cachedCount 校验、@since12/23 |
| VM-2 | AC-2.x ttype 决策 | TS 单测 | undefined→''、未知→回退、抛错→回退 |
| VM-3 | AC-3.x v1 池（已废弃） | — | v1 per-ttype 池已废弃，不再验证 |
| VM-4 | AC-4.x v2 簿记+SetCreateByTemplate | UT | TS 簿记、setCreateByTemplate、AllowReusableV2Descendant |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `.template(type,itemBuilder,templateOptions?)`（dynamic `@since12`/static `@since23`） | 既有 | 多模板注册 | — | AC-1.1 |
| `.templateId(typedFunc)`（`@since12/23`） | 既有 | item→ttype 映射 | — | AC-1.2 |
| `TemplateOptions.cachedCount` / `TemplateTypedFunc<T>`（`@since12/23`） | 既有 | per-ttype 上限/映射类型 | — | AC-1.4 |

> SDK：dynamic `repeat.d.ts:260-414`；static `repeat.static.d.ets:195-273`。

## 接口规格

### 接口定义

**.template / .templateId（dynamic，`repeat.d.ts:397,414`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `template(type: string, itemBuilder: RepeatItemBuilder<T>, templateOptions?: TemplateOptions): RepeatAttribute<T>`；`templateId(typedFunc: TemplateTypedFunc<T>): RepeatAttribute<T>` |
| 返回值 | `RepeatAttribute<T>`（链式） |
| 开放范围 | Public（`@since12`） |
| 错误码 | N/A（未知 ttype 回退 each，不抛错） |
| 关联 AC | AC-1.1,AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| type（ttype） | string | 是 | — | 任意字符串；`''` 为 each 保留 |
| itemBuilder | RepeatItemBuilder<T> | 是 | — | @Builder（static） |
| templateOptions.cachedCount | number/int | 否 | 显示+预加载 | `[0,+∞)`，不递减 |
| typedFunc | (item,index)=>string | 是 | — | 返回 ttype；未知/抛错回退 `''` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `.template('a',...)` 多次 | 累积不同 ttype 构建器 | AC-1.1 |
| 2 | ttypeGenFunc 返回未知 ttype | 日志+回退 each（`''`） | AC-2.2 |
| 3 | v2 模板子节点 | setCreateByTemplate(true) 禁用 @ReusableV2 | AC-4.4,AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意：v1 per-ttype 池（C++ `node4key4ttype_`）**已废弃**，v2 per-ttype 簿记在 TS（C++ 仅 flat RID→CacheItem）；模板内 `@ReusableV2` 复用被 `SetAllowReusableV2Descendant(false)` 禁用。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic `@since12`；static `@since23`。
- **API 版本号策略:** 按 SDK `@since12/23` 标注。

> **@ReusableV2 互斥风险（F-tpl）：** 模板（ttype≠`''`）子节点经 `SetAllowReusableV2Descendant(false)` 禁用 `@ReusableV2` reuseId 复用，Repeat ttype 池为唯一复用路径；`.each()` 子节点（ttype=`''`）仍允许 `@ReusableV2`（风险 RISK-F3-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| ttype 任意字符串 | `''` 为 each 保留；templateId 装 item→ttype 映射 | AC-1.1,AC-1.3 |
| v1 per-ttype 池在 C++（已废弃） | ~~`node4key4ttype_`/`cacheCountL24ttype_` 原生分池~~ | AC-3.x（已废弃） |
| v2 per-ttype 簿记在 TS | C++ v2 仅 flat RID→CacheItem，ttype 在 TS | AC-4.1,AC-4.2 |
| 模板禁用 @ReusableV2 | SetAllowReusableV2Descendant(false)，ttype 池唯一复用 | AC-4.4,AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | v2 per-ttype 复用降低异构项重建开销 | UT + benchmark | `pu_repeat_virtual_scroll_2_impl.ts:1043-1090`（v1 池已废弃） |
| 可靠性 | 未知 ttype/抛错安全回退 each | UT 异常 | `pu_repeat_virtual_scroll_2_impl.ts:878-899` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 子节点随父容器 | — |
| 大字体 | 否 | 无独立处理 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | template/templateId `@since12`、static `@since23`；v1 per-ttype 池已废弃、v2 TS 簿记为准 | AC-1.1,AC-4.1 |
| 生态兼容 | 是 | dynamic `@since12`、static `@since23` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Repeat 模板化渲染与复用
  作为 应用开发者
  我想要 用 .template/.templateId 多模板渲染并按 ttype 复用
  以便 异构数据项高效渲染

  Scenario Outline: ttype 决策
    Given ttypeGenFunc 对某 item 返回 <返回>
    When computeTtype
    Then <结果>

    Examples:
      | 返回 | 结果 |
      | undefined | 回退 each（''） |
      | 'card'（已注册） | 用 card 模板 |
      | 'unknown'（未注册） | 日志+回退 each |

  Scenario: v2 模板禁用 @ReusableV2
    Given v2 路径，ttype='card'
    When 创建模板子节点
    Then setCreateByTemplate(true)→SetAllowReusableV2Descendant(false)，@ReusableV2 reuseId 复用被禁用
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做模板渲染与 per-ttype 复用；内存优化见 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "pu_repeat template/templateId ttype 注册与 RepeatEachFuncTtype 保留 ttype"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScrollCaches node4key4ttype cacheCountL24ttype v1 per-ttype 池"
  - repo: "openharmony/arkui_ace_engine"
    query: "RepeatVirtualScroll2ModelNG SetCreateByTemplate SetAllowReusableV2Descendant 禁用 @ReusableV2"
```

**关键文档：** `interface/sdk-js/api/@internal/component/ets/repeat.d.ts`、`frameworks/bridge/declarative_frontend/state_mgmt/src/lib/partial_update/pu_repeat.ts`、`frameworks/core/components_ng/syntax/repeat_virtual_scroll_caches.h`、`frameworks/core/components_ng/syntax/repeat_virtual_scroll_2_model_ng.cpp`
