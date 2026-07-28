# 特性规格

> Func-07-05-01-Feat-01 if/else 条件渲染语法：固化 `IfElseNode` 分支 diff（`SetBranchId` 经 `branchIdChanged_` 检测、`Clean`+`CollectCleanedChildren` 拆 removed/reserved、`branchId_` 初值 -1 故首分支必变更）、分支切换脏标记（`FlushUpdateAndMarkDirty` 仅 `PROPERTY_UPDATE_BY_CHILD_REQUEST` + `ChildrenUpdatedFrom(0)`，无 `MEASURE_SELF_AND_PARENT`）、`TryRetake` 跨分支状态保留（keyed by `(id,branchId_)`）、TS `ifElseBranchUpdateFunction` 分支选择 + JS 桥接（`If.branchId` 非 setBranchId、NG/legacy 管线）、**dynamic 纯语法无 callable** / **static `@since26` callable**（`If`/`ElseIf`/`Else`+`IfAttribute`）、C-API `ConditionScopeNode`（共用 `JS_IF_ELSE_ETS_TAG`、Arkoala 侧分支）行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | if/else 条件渲染语法 |
| 特性编号 | Func-07-05-01-Feat-01 |
| 优先级 | P1 |
| 目标版本 | dynamic：纯语法（无 callable，由 ArkTS 编译器转译为内部 `If.create`/`If.branchId`/`If.pop`）；static `@since26`（`If`/`ElseIf`/`Else`+`IfAttribute`）+ `@since26 staticonly`（style-builder/`debugLine`/`setIfOptions`/`applyAttributesFinish`） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。本特性为 Func-07-05-01（渲染控制语法）首个 Feat，作为该功能域 design.md 基线。ForEach 循环渲染（Feat-02）、共享语法节点框架（Feat-03）由后续 Feat 承接。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/05-render-control/01-render-control-syntax/design.md` | Baselined |
| Static API（SDK 契约，if 仅 static） | `interface/sdk-js/api/arkui/component/if.static.d.ets` | — |
| NG 分支节点 | `frameworks/core/components_ng/syntax/if_else_node.cpp` / `if_else_node.h` | — |
| NG Model 工厂 | `frameworks/core/components_ng/syntax/if_else_model_ng.cpp` / `if_else_model.h` | — |
| JS 桥接 | `frameworks/bridge/declarative_frontend/jsview/js_if_else.cpp` / `js_if_else.h` | — |
| legacy Model | `frameworks/bridge/declarative_frontend/jsview/models/if_else_model_impl.cpp` / `.h` | — |
| TS 分支选择 | `frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_buildnode_base.ts` | — |
| UINode 基类（disappearing/CollectCleanedChildren） | `frameworks/core/components_ng/base/ui_node.h` | — |
| C-API 条件节点 | `frameworks/core/components_ng/syntax/arkoala_condition_scope.cpp` / `arkoala_condition_scope.h` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: if/else 分支与 branchId diff

**作为** 应用开发者,
**我想要** 用 `if/else if/else` 条件渲染,条件变化时切换分支,
**以便** 按状态渲染不同子树。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ArkTS 编译器遇到 `if/else if/else` THEN 转译为内部序列 `If.create()`→`ifElseBranchUpdateFunction(<branchId>,()=>children)`→`If.branchId(<branchId>,...)`→`If.pop()`（注释 `if_else_node.cpp:36-65`），dynamic 无公开 callable | 正常 |
| AC-1.2 | WHEN `SetBranchId(value,removedElmtId,reservedElmtId)`（`if_else_node.cpp:66-79`）THEN `branchIdChanged_=(branchId_!=value)`（`:68`）；变更时 `Clean(false,true,branchId_)`（`:75`）+`CollectCleanedChildren(GetChildren(),removedElmtId,reservedElmtId,true)`（`:76`）拆分 removed/reserved，**之后**才 `branchId_=value`（`:77`） | 正常 |
| AC-1.3 | WHEN 首次渲染（`branchId_` 初值 -1，`if_else_node.h:66`）THEN 任何首分支 id 都判为"变更"（`-1 != branchId`），触发首次分支建立 | 边界 |
| AC-1.4 | WHEN 同一分支再次"切换"（value==branchId_）THEN `branchIdChanged_=false`，不 Clean、不重建 | 边界 |

### US-2: 分支切换脏标记

**作为** 应用开发者,
**我想要** 分支切换后父容器正确重测量,
**以便** 新分支子树正确布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `FlushUpdateAndMarkDirty()` 且 `branchIdChanged_` 为真 THEN 沿父链找到首个 `FrameNode` 祖先调 `ChildrenUpdatedFrom(0)`（`if_else_node.cpp:85-88`） | 正常 |
| AC-2.2 | WHEN 分支变更 THEN **仅** `MarkNeedFrameFlushDirty(PROPERTY_UPDATE_BY_CHILD_REQUEST)`（`:94`），**无** `PROPERTY_UPDATE_MEASURE_SELF_AND_PARENT`；`branchIdChanged_` 在此复位（`:96`） | 边界 |
| AC-2.3 | WHEN `FlushUpdateAndMarkDirty` 在 `If.pop()` 时执行 THEN（按编译器生成）完成分支建立/切换的脏标记 | 正常 |

### US-3: TryRetake 跨分支状态保留

**作为** 应用开发者,
**我想要** 分支切换时 disappearing 子节点能被复用,
**以便** 切回原分支时保留状态、减少重建。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `TryRetake(id)`（`if_else_node.cpp:99-112`）THEN 经 `GetDisappearingChildById(id,branchId_)`（`:101`，按**当前 branchId_** 查 disappearing 子）查找 | 正常 |
| AC-3.2 | WHEN 命中 disappearing 子 THEN `SetJSViewActive(true)`+`AddChild`（重新挂载）+`LayoutProperty::UpdateAllGeometryTransition(node)`（`:104-107`）+`CollectRetakenNodes`（`:108`） | 正常 |
| AC-3.3 | WHEN `CollectRetakenNodes(node)`（`:114-123`）THEN 记 `retakenElmtIds_`，递归子节点（遇 `JS_VIEW_ETS_TAG` 停止，`:117`） | 正常 |
| AC-3.4 | WHEN TS 经 `GetRetakenElmtIds`（`:124-130`）取回 THEN `splice` 转移并清空本地 `retakenElmtIds_`，partial-update 层据此标记这些 elmtId 非 dirty | 正常 |
| AC-3.5 | WHEN 同一子节点 id 在不同分支下 THEN 因查找键含 `branchId_`，跨分支不会误取（`ui_node.h:596`） | 边界 |

### US-4: TS 分支选择与 JS 桥接

**作为** 应用开发者,
**我想要** TS 按条件选活跃分支并驱动 C++ 切换,
**以便** 状态变化自动切换渲染分支。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `ifElseBranchUpdateFunction(branchId,branchfunc)`（`puv2_view_buildnode_base.ts:274-311`）THEN 读 `If.getBranchId()`，`branchId===oldBranchid` 则 no-op（`:275-277`） | 正常 |
| AC-4.2 | WHEN branchId 不同 THEN `If.branchId(branchId,removedChildElmtIds,reservedChildElmtIds)`（`:289`，**方法名 `branchId` 非 `setBranchId`**）切分支；reserved 子 `setPending(true)`（`:292`），removed 子从 `elmtId2Repeat_` 删除+`unregisterRemovedElmtsFromViewPUs`（`:295-300`），`purgeDeletedElmtIds`（`:304`），执行 `branchfunc()`（`:306`）+`ifElseBranchUpdateFunctionDirtyRetaken`（`:307`） | 正常 |
| AC-4.3 | WHEN JS 桥接 `JSIfElse::JSBind`（`js_if_else.cpp:43-55`）THEN 绑定 `"If"` 的 6 个静态方法：`create`/`pop`/`branchId`/`getBranchId`/`canRetake`/`getRetakenElmtIds` | 正常 |
| AC-4.4 | WHEN `IfElseModel::GetInstance()`（`js_if_else.cpp:24-38`）THEN `NG_BUILD` 或 `IsCurrentUseNewPipeline()` 返回 `IfElseModelNG`，否则 legacy `IfElseModelImpl` | 正常 |
| AC-4.5 | WHEN `IfElseModelNG`（`if_else_model_ng.cpp:23-66`）THEN `Create`→`GetOrCreateIfElseNode`+Push、`Pop`→`PopContainer`、`SetBranchId`→`node->SetBranchId`、`GetBranchId`（默认 -1）、`CanRetake`→`TryRetake`、`GetRetakenElmtIds` | 正常 |

### US-5: 静态范式 callable surface + C-API

**作为** 应用开发者（static `@since26` 范式）/ C-API,
**我想要** if/else 在静态范式有显式 callable、C-API 有条件节点,
**以便** 静态编译/C-API 路径支持条件渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN static 范式（`@since26`）THEN 暴露 `If(condition: boolean, content_: CustomBuilder): IfAttribute`（`if.static.d.ets:104-108`，`@ComponentBuilder`） | 正常 |
| AC-5.2 | WHEN static `IfAttribute`（`:32` `@since26`）THEN `ElseIf(condition,content_): this`（`:44`）、`Else(content_): void`（`:57`）链式分支 | 正常 |
| AC-5.3 | WHEN static style-builder 形态 THEN `If(style: CustomBuilderT<IfAttribute>, content_): IfAttribute`（`:121-124` `@since26 staticonly`），须首调 `setIfOptions(condition)`（`:82`）末调 `applyAttributesFinish()`（`:91`），另含 `debugLine`（`:71`） | 边界 |
| AC-5.4 | WHEN dynamic 范式 THEN **无公开 If callable**——纯语法，由编译器转译内部 `If.create/branchId/pop`（grep `interface/sdk-js` 仅 static 有 if 声明） | 边界 |
| AC-5.5 | WHEN C-API（Arkoala）路径 THEN `ConditionScopeNode`（`arkoala_condition_scope.h:27`，extends UINode）共用 `JS_IF_ELSE_ETS_TAG`（`:21`），`IsSyntaxNode()=true`（`:39`）；**不做 C++ 分支 diff**（分支由 Arkoala 侧先决），仅 `AddChild`+`UpdateAllGeometryTransition`（`:23-30`）+`FlushUpdateAndMarkDirty` 发 `NotifyChange(START_CHANGE_POSITION)`（`:37`）+`PROPERTY_UPDATE_BY_CHILD_REQUEST`（`:40`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1~1.4 | R-1,R-2,R-8 | T-1 | UT：`if_else_node` SetBranchId/branchIdChanged/Clean 顺序；编译产物 | `if_else_node.cpp:36-79,66` |
| AC-2.1~2.3 | R-3 | T-1 | UT：FlushUpdateAndMarkDirty + PROPERTY_UPDATE 标记 | `if_else_node.cpp:81-97` |
| AC-3.1~3.5 | R-4,R-9 | T-1 | UT：TryRetake/CollectRetakenNodes/GetRetakenElmtIds | `if_else_node.cpp:99-130`、`ui_node.h:596` |
| AC-4.1~4.5 | R-5,R-6,R-10 | T-1 | TS 单测 + UT：ifElseBranchUpdateFunction/IfElseModelNG | `puv2_view_buildnode_base.ts:274-311`、`if_else_model_ng.cpp:23-66` |
| AC-5.1~5.5 | R-7,R-11 | T-1 | UT + SDK 比对；C-API ConditionScopeNode | `if.static.d.ets:32-124`、`arkoala_condition_scope.cpp:21-41` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 编译器遇 if/else | 转译 If.create→ifElseBranchUpdateFunction→If.branchId→If.pop；dynamic 无 callable | — | AC-1.1 |
| R-2 | 行为 | SetBranchId 且 value≠branchId_ | branchIdChanged_=true；Clean+CollectCleanedChildren 拆 removed/reserved；之后 branchId_=value | 顺序固定 | AC-1.2 |
| R-3 | 行为 | FlushUpdateAndMarkDirty 且 branchIdChanged_ | ChildrenUpdatedFrom(0) + PROPERTY_UPDATE_BY_CHILD_REQUEST；复位 branchIdChanged_ | 无 MEASURE_SELF_AND_PARENT | AC-2.1,AC-2.2 |
| R-4 | 行为 | TryRetake(id) | 按 (id,branchId_) 查 disappearing 子，命中则 SetJSViewActive(true)+AddChild+UpdateAllGeometryTransition+CollectRetakenNodes | 跨分支不误取 | AC-3.1,AC-3.2,AC-3.5 |
| R-5 | 行为 | ifElseBranchUpdateFunction | branchId===getBranchId no-op；否则 If.branchId+reserved setPending+purge+branchfunc | — | AC-4.1,AC-4.2 |
| R-6 | 行为 | JS 桥接 | 绑定 create/pop/branchId/getBranchId/canRetake/getRetakenElmtIds；NG/legacy 按 IsCurrentUseNewPipeline | 方法名 branchId 非 setBranchId | AC-4.3,AC-4.4 |
| R-7 | 行为 | static @since26 | If/ElseIf/Else callable + IfAttribute；style-builder 须 setIfOptions+applyAttributesFinish | dynamic 无 callable | AC-5.1~5.4 |
| R-8 | 边界 | branchId_ 初值 -1 | 首分支必判变更 | — | AC-1.3 |
| R-9 | 行为 | GetRetakenElmtIds | splice 转移 retakenElmtIds_，partial-update 据此标非 dirty | 遇 JS_VIEW_ETS_TAG 停递归 | AC-3.3,AC-3.4 |
| R-10 | 行为 | IfElseModelNG | Create/Pop/SetBranchId/GetBranchId(默认-1)/CanRetake/GetRetakenElmtIds | — | AC-4.5 |
| R-11 | 边界 | C-API ConditionScopeNode | 共用 JS_IF_ELSE_ETS_TAG，不做 C++ 分支 diff（Arkoala 侧），仅 geometry transition+PROPERTY_UPDATE_BY_CHILD_REQUEST | IsSyntaxNode=true | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.x branchId diff | UT | branchIdChanged 检测、Clean+Collect 顺序、-1 初值 |
| VM-2 | AC-2.x 脏标记 | UT | 仅 PROPERTY_UPDATE_BY_CHILD_REQUEST、ChildrenUpdatedFrom |
| VM-3 | AC-3.x TryRetake | UT | (id,branchId_) 键、retakenElmtIds 收集/splice |
| VM-4 | AC-4.x TS/桥接 | TS 单测 + UT | ifElseBranchUpdateFunction、If.branchId、NG/legacy |
| VM-5 | AC-5.x static/C-API | UT + SDK 比对 | @since26 callable、ConditionScopeNode 共用 tag |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `If(condition,content_)` + `IfAttribute.ElseIf/Else`（static `@since26`） | 既有 | 静态范式条件渲染 | dynamic 无 callable | AC-5.1,AC-5.2 |
| `If(style,content_)` + `setIfOptions`/`applyAttributesFinish`/`debugLine`（static `@since26 staticonly`） | 既有 | 静态 style-builder 形态 | 须 setIfOptions+applyAttributesFinish | AC-5.3 |

> SDK：static `if.static.d.ets:32-124`。dynamic 无 if 公开声明。Kit：ArkUI；权限：无；SysCap：`SystemCapability.ArkUI.ArkUI.Full`。

## 接口规格

### 接口定义

**If（static，`if.static.d.ets:104`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `@ComponentBuilder If(condition: boolean, content_: CustomBuilder): IfAttribute`（+ style-builder 重载 `@since26 staticonly`） |
| 返回值 | `IfAttribute` |
| 开放范围 | Public（static `@since26`；dynamic 无 callable） |
| 错误码 | N/A |
| 关联 AC | AC-5.1,AC-5.3 |

**IfAttribute（static，`if.static.d.ets:32`）**

| 属性 | 值 |
|------|-----|
| 方法 | `ElseIf(condition: boolean, content_: CustomBuilder): this`（`:44`）；`Else(content_: CustomBuilder): void`（`:57`）；`debugLine(...)`/`setIfOptions(condition)`/`applyAttributesFinish()`（`@since26 staticonly`） |
| 开放范围 | Public（static `@since26`） |
| 关联 AC | AC-5.2,AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| condition | boolean | 是 | — | 条件表达式，状态变化触发重渲染 |
| content_ | CustomBuilder | 是 | — | 分支子树构建器 |
| branchId（内部） | number | — | -1（C++ branchId_） | 编译器生成，唯一标识分支 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 条件变化切换分支 | SetBranchId 检测变更+Clean+Collect removed/reserved | AC-1.2 |
| 2 | 分支切换 | ChildrenUpdatedFrom(0)+PROPERTY_UPDATE_BY_CHILD_REQUEST | AC-2.1,AC-2.2 |
| 3 | 切回原分支 | TryRetake 复用 disappearing 子 | AC-3.1,AC-3.2 |
| 4 | 同分支再切换 | no-op（branchId===getBranchId） | AC-4.1 |
| 5 | static style-builder | 须 setIfOptions+applyAttributesFinish | AC-5.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。注意：if/else 在 **dynamic 范式为纯语法、无公开 callable**；仅 **static `@since26`** 暴露 `If/ElseIf/Else` callable。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** dynamic 语法自 ArkUI 起；static `@since26`。
- **API 版本号策略:** 按 SDK `@since26`/`@since26 staticonly` 标注；dynamic 无 callable 故无 @since。

> **JS 方法名澄清风险（F-branchId）：** C++ 注释（`if_else_node.cpp:50`）写 `If.setBranchId`，但 JS 实际绑定名为 **`If.branchId`**（`js_if_else.cpp:49`、`puv2_view_buildnode_base.ts:289`）；下游勿按 setBranchId 调用（风险 RISK-1）。分支切换仅 `PROPERTY_UPDATE_BY_CHILD_REQUEST`（无 MEASURE_SELF_AND_PARENT），父重测量经 `ChildrenUpdatedFrom(0)` 间接（风险 RISK-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| branchId diff | value≠branchId_ 触发 Clean+Collect，顺序固定 | AC-1.2 |
| 仅 BY_CHILD_REQUEST 脏标记 | 分支切换无 MEASURE_SELF_AND_PARENT，经 ChildrenUpdatedFrom 间接重测量 | AC-2.2 |
| TryRetake keyed by branchId_ | 跨分支状态保留按 (id,branchId_) 查 | AC-3.1,AC-3.5 |
| dynamic 无 callable | 仅 static @since26 暴露 If/ElseIf/Else | AC-5.1,AC-5.4 |
| C-API 共用 tag 不做 C++ diff | ConditionScopeNode 共用 JS_IF_ELSE_ETS_TAG，分支由 Arkoala 侧 | AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 同分支再切换 no-op；切回原分支 TryRetake 复用减少重建 | UT | `puv2_view_buildnode_base.ts:277`、`if_else_node.cpp:99-112` |
| 可靠性 | branchId_=-1 首分支必建立；跨分支不误取 | UT | `if_else_node.h:66`、`ui_node.h:596` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 契约一致 | XTS | — |
| 平板 | 无差异 | 同上 | XTS | — |
| 折叠屏 | 无差异 | 同上 | XTS | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 分支切换 ConditionScopeNode 发 NotifyChange(START_CHANGE_POSITION) | AC-5.5 |
| 大字体 | 否 | 子树随父布局 | — |
| 深色模式 | 否 | 无直接关联 | — |
| 多窗口/分屏 | 否 | 无直接关联 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | dynamic 纯语法、static `@since26` callable | AC-5.1,AC-5.4 |
| 生态兼容 | 是 | static `@since26` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: if/else 条件渲染
  作为 应用开发者
  我想要 用 if/else 按条件渲染子树
  以便 状态变化切换分支

  Scenario: 首次渲染（branchId_=-1）
    Given IfElseNode 首次 SetBranchId(id=2)
    When branchId_(-1) != 2
    Then branchIdChanged_=true，Clean+Collect，建立分支

  Scenario Outline: 分支切换脏标记
    Given 分支由 <from> 切到 <to>
    When FlushUpdateAndMarkDirty
    Then <行为>

    Examples:
      | from | to | 行为 |
      | 1 | 2 | ChildrenUpdatedFrom(0)+PROPERTY_UPDATE_BY_CHILD_REQUEST |
      | 2 | 2 | no-op（branchIdChanged_=false） |

  Scenario: 切回原分支状态保留
    Given 分支 A 的子节点已 disappearing
    When 切回分支 A，TryRetake(id)
    Then 按 (id,branchId_) 命中，SetJSViewActive(true)+AddChild 复用

  Scenario: 静态范式 style-builder
    Given static @since26 用 If(style,content_)
    When 构建
    Then 须首调 setIfOptions(condition) 末调 applyAttributesFinish()
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 if/else；ForEach 见 Feat-02、共享框架见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "IfElseNode SetBranchId branchIdChanged Clean CollectCleanedChildren 分支 diff 顺序"
  - repo: "openharmony/arkui_ace_engine"
    query: "IfElseNode TryRetake GetDisappearingChildById branchId_ 跨分支状态保留"
  - repo: "openharmony/arkui_ace_engine"
    query: "ifElseBranchUpdateFunction If.branchId TS 分支选择 puv2_view_buildnode_base"
  - repo: "openharmony/arkui_ace_engine"
    query: "ConditionScopeNode arkoala_condition_scope JS_IF_ELSE_ETS_TAG C-API 分支"
```

**关键文档：** `interface/sdk-js/api/arkui/component/if.static.d.ets`、`frameworks/core/components_ng/syntax/if_else_node.cpp`、`frameworks/bridge/declarative_frontend/state_mgmt/src/lib/puv2_common/puv2_view_buildnode_base.ts`、`frameworks/core/components_ng/syntax/arkoala_condition_scope.cpp`
