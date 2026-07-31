# 特性规格

> Func-04-09-01-Feat-05 默认焦点、FocusView 与焦点恢复：固化默认节点标记、FocusView 根 Scope、视图栈切换以及页面、弹窗和窗口恢复行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 默认焦点、FocusView 与焦点恢复 |
| 特性编号 | Func-04-09-01-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 当前 NG 实现；UIExtensionWindow 恢复包含 Target API 26 分支 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义 `defaultFocus`、`groupDefaultFocus` 的节点标记与搜索边界，FocusView 的合法性、Entry View 和 ViewRoot Scope 模型，FocusView show/hide/close 栈管理，以及首次显示、历史叶节点、根 Scope、modal、窗口重新获焦和 `autoFocusTransfer` 组合下的焦点恢复顺序。

本特性不重复定义普通焦点请求事务、PRIOR/PREVIOUS 域优先节点或按键遍历算法；它们分别由 Feat-02、Feat-04、Feat-03 承接。焦点激活状态和焦点框绘制归 Feat-06。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 默认与组默认焦点 | 补录属性入口、深度优先搜索、FocusView 边界和 tabIndex 首次进入行为 |
| ADDED | FocusView 根模型 | 补录合法性、Entry View、首个 Scope 路径、指定根 Scope 和根焦点标志 |
| ADDED | View 栈生命周期 | 补录 show、hide、close、modal 拦截、子 View 清理和栈重排 |
| ADDED | 首次与历史恢复 | 补录 default、ViewRoot、历史叶节点、InheritFocus 和 PREVIOUS 接入顺序 |
| ADDED | 窗口与运行时恢复 | 补录 WindowFocus、DynamicRender、UIExtensionWindow 和 Target API 26 差异 |
| ADDED | 自动转移开关 | 补录 `autoFocusTransfer=false` 对失焦、关闭和恢复根 Scope 的影响 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/design.md` | Baselined |
| 请求事务规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-02-focus-request-clear-switch-transaction-spec.md` | Baselined |
| 导航规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-03-focus-navigation-traversal-algorithm-spec.md` | Baselined |
| 域与优先级规格 | `specs/04-common-capability/09-focus-framework/01-focus-mechanism/Feat-04-focus-scope-group-priority-spec.md` | Baselined |
| FocusView 模型 | `frameworks/core/components_ng/manager/focus/focus_view.h:28-119`、`focus_view.cpp:23-428` | 已核验 |
| FocusManager View 栈 | `frameworks/core/components_ng/manager/focus/focus_manager.cpp:55-228,572-623,743-777` | 已核验 |
| FocusHub 默认与 View 接入 | `frameworks/core/components_ng/event/focus_hub.cpp:595-621,2300-2357,2732-2769,3386-3423` | 已核验 |
| Pipeline Flush | `frameworks/core/pipeline_ng/pipeline_context.cpp:1885-1908` | 已核验 |
| 属性入口 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:13345-13363`、`frameworks/core/components_ng/base/view_abstract.cpp:8794-8839` | 已核验 |

## 用户故事

### US-1: 配置默认焦点

**作为** 页面或组件开发者，  
**我想要** 标记普通默认节点和组默认节点，  
**以便** 首次显示或首次 Tab 进入时得到确定的焦点目标。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `defaultFocus` 或 `groupDefaultFocus` 入参是 boolean THEN写入 FocusHub 对应标记；WHEN动态前端入参非 boolean THEN忽略本次设置 | 正常 |
| AC-1.2 | WHEN搜索 DEFAULT 或 GROUP_DEFAULT THEN按焦点树深度优先返回首个同时具有对应标记且 `IsFocusable()` 为 true 的节点 | 正常 |
| AC-1.3 | WHEN递归遇到合法 Entry FocusView THEN不进入其子树搜索外层 View 的默认节点 | 边界 |
| AC-1.4 | WHEN tabIndex 首次进入 SCOPE 且尚未使用过组默认节点 THEN优先请求首个 GROUP_DEFAULT；成功后记录该 Scope 已使用组默认 | 正常 |
| AC-1.5 | WHEN GROUP_DEFAULT 不可 whole-path 聚焦或请求失败 THEN本次 tabIndex 请求失败；不会在该分支自动回退普通目标 | 边界 |

### US-2: 建立 FocusView 与 ViewRoot Scope

**作为** 页面、导航目的地或弹层容器，  
**我想要** 将自身接入统一 FocusView 模型，  
**以便** 视图切换和焦点恢复拥有明确边界。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN FocusView 提供显式 rootScopeSpecified THEN直接使用该 Scope；否则按 `GetRouteOfFirstScope()` 从 View Hub 查找首个 Scope | 正常 |
| AC-2.2 | WHEN路径索引失效 THEN退回 FocusView 自身 Hub；WHEN得到的目标不是 SCOPE 或等于 Screen Hub THEN改用其父 FocusHub | 边界 |
| AC-2.3 | WHEN ViewRoot 不是 FocusView 自身 Hub THEN将 FocusView Hub 的 dependence 设置为 AUTO | 正常 |
| AC-2.4 | WHEN设置 ViewRoot 已聚焦标志 THEN同时把 ViewRoot dependence 切换为 SELF；取消标志时切回 AUTO | 正常 |
| AC-2.5 | WHEN Navbar、NavDestination 或 Menu 的 whole-path 自身不可聚焦 THEN `FocusViewShow` 拒绝入栈 | 边界 |

### US-3: 管理 FocusView show/hide/close

**作为** FocusManager，  
**我想要** 维护当前 View、普通 View 栈和 modal View 栈，  
**以便** 页面与弹层切换不会恢复到错误视图。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN show 的 FocusView 无父 FocusHub THEN不入栈；WHEN与当前 View 相同或当前 View 是其子 View THEN保持现状 | 边界 |
| AC-3.2 | WHEN有效 modal View 存在且新 View 不是该 modal 的子 View THEN拦截 show，不替换当前 View | 边界 |
| AC-3.3 | WHEN普通 show 成功 THEN去重后追加到 View 栈尾、状态置 SHOW、更新 lastFocusView；非步进 show 还沿 View 历史链设置 PREVIOUS | 正常 |
| AC-3.4 | WHEN hide 的 View 被当前 modal 覆盖或包含当前 modal THEN忽略；否则在自动转移开启时失焦，并在命中当前 View/其子 View 时清空 lastFocusView | 边界 |
| AC-3.5 | WHEN close 且自动转移关闭、同时并非 detach-from-tree THEN直接返回；其他 close 失焦并移除自身及子 View、modal 条目和域注册 | 恢复 |
| AC-3.6 | WHEN close 后栈为空 THEN lastFocusView 置空并上报栈空错误；WHEN栈顶变化 THEN更新 lastFocusView并检查新栈顶可聚焦性 | 异常 |

### US-4: 首次显示与历史恢复

**作为** FocusView，  
**我想要** 在首次进入和再次显示时按稳定顺序恢复焦点，  
**以便** 默认目标不覆盖用户历史。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN View Hub 不是可聚焦 SCOPE、ViewRoot 不存在、modal 栈有效或 FocusManager 不存在 THEN `RequestDefaultFocus` 返回 false | 边界 |
| AC-4.2 | WHEN View 从未成功显示且 ViewRoot 尚无聚焦子节点、且 DEFAULT whole-path 可聚焦 THEN先请求 DEFAULT，并把 ViewRoot 标记为非根聚焦 | 正常 |
| AC-4.3 | WHEN自动转移关闭且默认请求未成功 THEN调用 `RearrangeViewStack`；SHOW 状态下当前 View 未聚焦时从栈移除，CLOSE 状态下把当前 ViewRoot 设为焦点 | 恢复 |
| AC-4.4 | WHEN自动转移开启、无可用首次默认且 ViewRoot 标记为根聚焦并且历史属于 ViewRoot 路径 THEN请求 ViewRoot，保留其历史供后续扩展 | 正常 |
| AC-4.5 | WHEN不走 ViewRoot 分支 THEN取 View Hub 的焦点叶；View Hub 已 current 时执行 InheritFocus，否则以 VIEW_SWITCH 原因请求历史叶节点 | 正常 |
| AC-4.6 | WHEN任一路径成功 THEN清除 `neverShown`；首次 default 只执行一次，后续优先恢复历史而不是重新覆盖 | 正常 |

### US-5: 窗口与运行时恢复

**作为** 窗口焦点管理器，  
**我想要** 在窗口重新获焦和特殊容器中恢复当前 View，  
**以便** 焦点状态与运行时模式保持一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN窗口失焦通知到达 THEN `FocusManager::WindowFocus(false)` 不主动恢复；WHEN重新获焦 THEN建立 WINDOW_FOCUS 事务并尝试当前 View | 正常 |
| AC-5.2 | WHEN当前 View 曾聚焦但 View Hub 当前未聚焦 THEN自动转移关闭时请求 ViewRoot，开启时请求历史焦点叶 | 正常 |
| AC-5.3 | WHEN当前 View 无可恢复 Hub或未进入上述分支 THEN DynamicRender 强制取消根聚焦标志后请求默认焦点 | 正常 |
| AC-5.4 | WHEN UIExtensionWindow Target API 小于 26 THEN无条件取消根聚焦标志后请求默认焦点 | 兼容 |
| AC-5.5 | WHEN UIExtensionWindow Target API 大于等于 26 THEN仅在 focus active 时取消根聚焦标志；inactive 时保留根标志再执行默认/历史恢复 | 兼容 |
| AC-5.6 | WHEN窗口恢复后根 FocusHub 仍未 current THEN临时设 dependence=SELF 请求根焦点，再恢复原 dependence，并请求下一帧 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-3 | TASK-SKELETON-F5-1 | 属性/焦点树/tabIndex UT | `js_view_abstract.cpp:13345-13363`、`focus_hub.cpp:2300-2357` |
| AC-2.1~2.5 | R-4~R-6 | TASK-SKELETON-F5-2 | FocusView 路径 UT | `focus_view.cpp:23-46,158-251` |
| AC-3.1~3.6 | R-7~R-10 | TASK-SKELETON-F5-3 | FocusManager 栈 UT | `focus_manager.cpp:76-228` |
| AC-4.1~4.6 | R-11~R-14 | TASK-SKELETON-F5-4 | 首次/历史恢复 UT | `focus_view.cpp:285-359`、`focus_manager.cpp:123-145` |
| AC-5.1~5.6 | R-15~R-17 | TASK-SKELETON-F5-5 | Window/Container/API 版本 UT | `focus_manager.cpp:579-623,754-777`、`pipeline_context.cpp:1885-1908` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | API | 设置 default/groupDefault | boolean 写标记，动态前端非法类型忽略 | 不建立唯一性约束 | AC-1.1 |
| R-2 | 行为 | 搜索默认节点 | DFS 返回首个标记且自身可聚焦节点 | 合法 Entry FocusView 截断外层搜索 | AC-1.2, AC-1.3 |
| R-3 | 行为 | 首次 tabIndex 进入 Scope | GROUP_DEFAULT 优先且仅在未使用时执行 | 不可聚焦或请求失败直接失败 | AC-1.4, AC-1.5 |
| R-4 | 行为 | 获取 ViewRoot | 显式根优先，否则按路径查找 | 非 Scope/Screen 根回退父 Hub | AC-2.1, AC-2.2 |
| R-5 | 状态 | 根聚焦标志变化 | SELF/AUTO 与标志同步切换 | 根解析可改变 View Hub dependence | AC-2.3, AC-2.4 |
| R-6 | 边界 | 特定 FocusView show | Navbar/NavDestination/Menu 先做 whole-path 准入 | 其他 FocusView 由各 Pattern 合法性决定 | AC-2.5 |
| R-7 | 栈 | show | 去重追加并更新 last View | modal、父链和重复 View 可拦截 | AC-3.1~3.3 |
| R-8 | 栈 | hide | 可选失焦并清当前 View 引用 | modal 覆盖时忽略 | AC-3.4 |
| R-9 | 栈 | close | 按开关/detach 决定是否关闭，递归移除子 View | 同时清域注册 | AC-3.5 |
| R-10 | 异常 | close 后栈变化 | 更新/清空 last View并报告异常状态 | 不自动制造新 View | AC-3.6 |
| R-11 | 准入 | 请求 View 默认焦点 | 要求合法可聚焦 SCOPE、ViewRoot、Manager 且无 modal | modal 栈有效时拒绝 | AC-4.1 |
| R-12 | 首次 | neverShown 且根无子焦点 | DEFAULT 优先 | whole-path 不可聚焦则继续恢复链 | AC-4.2, AC-4.6 |
| R-13 | 恢复 | 根标志和历史有效 | ViewRoot 优先 | 成功后保留历史用于扩展 | AC-4.4 |
| R-14 | 恢复 | 普通历史路径 | InheritFocus 或请求焦点叶 | autoFocusTransfer=false 改走栈重排 | AC-4.3, AC-4.5 |
| R-15 | 窗口 | WindowFocus(true) | 合并为窗口事务并恢复当前 View | false 不恢复 | AC-5.1, AC-5.2 |
| R-16 | 运行时 | DynamicRender/UIExtensionWindow | 调整根标志后请求默认/历史 | API 26 仅 UIExtensionWindow+inactive 保留标志 | AC-5.3~5.5 |
| R-17 | 恢复 | 根 Hub 未 current | 临时 SELF 请求根并恢复 dependence | 最后 RequestFrame | AC-5.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | R-1~R-3 | 属性与树搜索 UT | true/false/非法类型、DFS 顺序、Entry View 截断、组默认一次性 |
| VM-2 | R-4~R-6 | FocusView 根模型 UT | 显式根、路径越界、Screen、合法性与 dependence |
| VM-3 | R-7~R-10 | View 栈状态机 UT | 父子 View、modal、重复 show、hide、close、detach、空栈 |
| VM-4 | R-11~R-14 | 恢复顺序 UT | 首次 default、已有根子焦点、根历史、叶历史、自动转移开关 |
| VM-5 | R-15~R-17 | 窗口恢复 UT | WindowFocus false/true、DynamicRender、UIExtensionWindow API 25/26、active/inactive |
| VM-6 | AC-3.3, AC-4.4~4.5 | PRIOR/PREVIOUS 联合 UT | step show 不写 PREVIOUS，普通 show 和历史恢复接入 Feat-04 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| N/A | N/A | N/A | N/A | N/A | 已有能力补录，不新增 API | AC-1.1~5.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|---------|
| N/A | N/A | 无 API 变更或废弃 | 无需迁移 | AC-1.1~5.6 |

## 接口规格

### 接口定义

当前检出不含 canonical SDK 类型目录；以下签名依据仓内动态类型与实现核验，未经 canonical d.ts/d.ets 验证。

| API | 签名 | 入参 | 行为 | 关联 AC |
|-----|------|------|------|---------|
| defaultFocus | `defaultFocus(value: boolean): T` | boolean | 设置普通默认焦点标记；非法动态参数忽略 | AC-1.1~1.3 |
| groupDefaultFocus | `groupDefaultFocus(value: boolean): T` | boolean | 设置首次 Tab 进入 Scope 的组默认标记 | AC-1.1, AC-1.4~1.5 |

FocusView、FocusManager、ViewRoot 和窗口恢复方法均为 Inner C++ 实现，不构成 SDK 稳定性承诺。

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录当前实现。
- **数据与配置格式:** 无持久化格式变更，View 栈和历史仅存在于 Pipeline 运行期。
- **Target API:** UIExtensionWindow 在 Target API 26 起，inactive 状态不再强制把 ViewRoot 标记切为非根聚焦。
- **自动转移:** `autoFocusTransfer=false` 会保留部分旧焦点并以 ViewRoot/栈重排恢复，不能假设 show/hide/close 总会主动迁移焦点。
- **默认唯一性:** 实现按树序取首个命中，不校验同一 View 内只存在一个 default 或 groupDefault。
- **SDK 核验:** canonical `interface/sdk-js/api/` 未随当前检出提供。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| View 边界隔离 | 外层默认搜索不得穿越合法 Entry FocusView | AC-1.3 |
| 弱引用栈 | FocusManager 以 WeakPtr 保存 View 和历史，不延长页面/弹层生命周期 | AC-3.1~3.6 |
| 单一当前 View | lastFocusView 与栈尾共同定义恢复入口，modal 可覆盖普通栈 | AC-3.2~3.6 |
| 首次不覆盖历史 | default 仅在 neverShown 且根无焦点子节点时优先 | AC-4.2~4.6 |
| 根标志联动 | isViewRootScopeFocused 必须与 ViewRoot dependence SELF/AUTO 同步 | AC-2.4, AC-4.4 |

## 非功能性需求

| 维度 | 要求 | 验证 |
|------|------|------|
| 性能 | 默认节点搜索只遍历当前 FocusView 边界内焦点树；View 栈操作保持线性列表复杂度 | 性能审查/大栈 UT |
| 可靠性 | WeakPtr 失效、路径索引错误、ViewRoot 缺失和空栈均安全收敛 | VM-2, VM-3 |
| 可观测性 | View show/hide/close、默认请求和窗口恢复继续使用 ACE_FOCUS 日志及交互错误报告 | 日志审查 |
| 安全 | 不处理敏感数据、权限、IPC 或持久化 | 架构审查 |

## 多设备适配声明

- 键盘、遥控器和手柄的导航入口由 Feat-03 定义；本特性只定义导航进入 View 后的恢复目标。
- DynamicRender 与 UIExtensionWindow 使用专门恢复分支；普通窗口不应套用其根标志规则。
- 不新增设备形态、分辨率或输入法相关配置。

## 全局特性影响

| 影响面 | 结论 |
|--------|------|
| 页面/导航 | Page、Navigation、NavDestination 通过 FocusView 栈共享恢复规则 |
| 弹层/modal | Dialog、Menu、Bubble、Sheet 等合法 FocusView 可拦截或覆盖普通 View |
| 焦点域 | 普通 show 可通过 Feat-04 PREVIOUS 更新历史；close 清理域注册 |
| 焦点激活 | API 26 UIExtensionWindow 恢复读取 focus active，状态定义归 Feat-06 |
| 无障碍 | 焦点切换最终仍由 Feat-02 事务触发既有可访问性事件 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 默认焦点与 FocusView 恢复

  Scenario: 首次显示使用默认焦点
    Given FocusView 从未成功显示且 ViewRoot 没有聚焦子节点
    And View 内存在 whole-path 可聚焦的 defaultFocus 节点
    When Pipeline 刷新当前 FocusView
    Then 默认节点先于历史叶节点获得请求
    And 后续再次显示不以默认节点覆盖新历史

  Scenario: modal 拦截普通 View 切换
    Given modal FocusView 栈顶有效
    And 新 View 不是该 modal 的子 View
    When 新 View 调用 FocusViewShow
    Then 当前 lastFocusView 和普通恢复目标保持不变

  Scenario Outline: UIExtensionWindow API 26 恢复根标志
    Given 当前容器是 UIExtensionWindow
    And Target API 为 <api>
    And focus active 为 <active>
    When 窗口恢复并请求默认焦点
    Then ViewRoot 根聚焦标志按 <reset> 处理

    Examples:
      | api | active | reset |
      | 25  | false  | 取消 |
      | 26  | true   | 取消 |
      | 26  | false  | 保留 |
```

## Spec 自审清单

- [x] 状态、优先级、目标版本和复杂度完整
- [x] Delta 表头与类型符合仓库规则
- [x] 默认焦点、FocusView、modal、自动转移、窗口恢复和 API 26 分支均有 AC
- [x] 每组 AC 均映射到源码证据和 VM
- [x] 未把 Inner C++ 行为承诺为 Public SDK
- [x] 未修改产品源码、构建文件或测试代码
- [x] 无“待定”“TBD”“TODO”等占位符

## context-references

- `frameworks/core/components_ng/manager/focus/focus_view.h`
- `frameworks/core/components_ng/manager/focus/focus_view.cpp`
- `frameworks/core/components_ng/manager/focus/focus_manager.h`
- `frameworks/core/components_ng/manager/focus/focus_manager.cpp`
- `frameworks/core/components_ng/event/focus_hub.h`
- `frameworks/core/components_ng/event/focus_hub.cpp`
- `frameworks/core/pipeline_ng/pipeline_context.cpp`
- `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp`
- `frameworks/core/components_ng/base/view_abstract.cpp`
- `frameworks/bridge/declarative_frontend/ark_component/types/index.d.ts`
- `test/unittest/core/manager/focus_manager_test_ng.cpp`
- `test/unittest/core/event/focus_core/focus_request_test.cpp`
