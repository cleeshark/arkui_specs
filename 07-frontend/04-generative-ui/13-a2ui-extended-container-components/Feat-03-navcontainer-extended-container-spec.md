# 特性规格

> Func-07-04-13-Feat-03 NavContainer 扩展导航容器：固化鸿蒙扩展协议 `component: "NavContainer"` 的行为——NavContainer 为 C++ native 组件（`ExtendedComponentFactory.RegisterComponent("NavContainer")`，基于 `COLUMN` 节点），按 `currentIndex` 显示单个子页面（`RefreshChildVisibility` 仅目标子节点 `VISIBLE`、其余 `NONE`）；`currentIndex` 非负整数校验并裁剪到 `[0, len-1]`（非法回退 0 并派发 `INVALID_VALUE` 告警）；`navigate` 扩展函数（`NativeNavigateFunction`）解析 `componentId`/`targetComponentId`，定位 NavContainer 后按子组件 id 匹配索引切换当前页。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | NavContainer 扩展导航容器 |
| 特性编号 | Func-07-04-13-Feat-03 |
| 优先级 | P1 |
| 目标版本 | API Version 20；鸿蒙扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 与 Feat-01/Feat-02 并列，共享 Func-07-04-13 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/13-a2ui-extended-container-components/design.md` | Baselined |
| NavContainer 组件（C++） | `genui/src/main/cpp/components/extended/NavContainerComponent.cpp`、`.h` | — |
| navigate 路由函数（C++） | `genui/src/main/cpp/functions/extended/NativeNavigateFunction.cpp` | — |
| 组件工厂（C++） | `genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp` | — |
| 扩展 Catalog 聚合（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| navigate 函数（ArkTS） | `genui/src/main/ets/core/functions/extended/NavigateFunction.ets` | — |
| NavContainer 文档（Docs） | `reference/extended-components/nav-container.md` | 理解辅助 |
| 组件/函数 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/NavContainer.json`、`functions/navigate.json` | — |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: NavContainer 组件注册与节点创建

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `component: "NavContainer"` 并创建 native 组件,
**以便** 作为多子页面导航容器挂载。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `ExtendedComponentFactory.RegisterComponent("NavContainer", ...)` 执行 THEN 后续 `CreateComponent("NavContainer")` 返回 `NavContainerComponent`（`ExtendedComponentFactory.cpp:122,58-71`） | 正常 |
| AC-1.2 | WHEN 构造 `NavContainerComponent` THEN 创建 `A2UINodeType::COLUMN` 节点（`NavContainerComponent.cpp:51-53`） | 正常 |
| AC-1.3 | WHEN `GetType()` 被调用 THEN 返回 `"NavContainer"`（`NavContainerComponent.cpp:55-58`） | 正常 |
| AC-1.4 | WHEN 扩展 Catalog 聚合 THEN `EXTENDED_NATIVE_COMPONENT_NAMES` 含 `NavContainer` 且 schema 文件为 `NavContainer.json`（`A2UIExtendedComponents.ets:38,57`） | 正常 |

### US-2: children 子页面解析与 schema 校验

**作为** 生成式 UI 宿主开发者,
**我想要** NavContainer 解析静态子页面列表或动态模板,
**以便** 确定可导航的子页面集合。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ApplyPrivateAttributes` 且 descriptor 含 `children` 数组 THEN 记录 `hasDescriptorChildCount_` 与 `descriptorChildCount_`（`NavContainerComponent.cpp:66-72`） | 正常 |
| AC-2.2 | WHEN `CollectChildListDescriptor` 且 descriptor 含 `children` THEN `ChildListParser::ParseChildren` 解析（`NavContainerComponent.cpp:78-87`） | 正常 |
| AC-2.3 | WHEN `ValidateComponentDescriptorSchema` THEN `ValidateChildListSchema(..., ChildListEmptyArrayPolicy::ALLOW)` 校验，空数组不报错（`NavContainerComponent.cpp:89-94`） | 边界 |
| AC-2.4 | WHEN 子项增删改（OnAddChild/OnMoveChild/OnRemoveChild） THEN 各自调用 `RefreshChildVisibility`（`NavContainerComponent.cpp:117-134`） | 正常 |

### US-3: currentIndex 动态解析与范围裁剪

**作为** 生成式 UI 宿主开发者,
**我想要** `currentIndex` 被校验并裁剪到有效范围,
**以便** 非法/越界索引回退边界且可观测告警。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `currentIndex` 为非负整数字面量 THEN `ApplyCurrentIndexValue` 设为目标索引（`NavContainerComponent.cpp:175-198`） | 正常 |
| AC-3.2 | WHEN `currentIndex` 缺失（descriptor 无该键）且 `isApplyingCurrentIndexDescriptor_` THEN 回退 `NAV_CONTAINER_CURRENT_INDEX_FALLBACK=0`（`NavContainerComponent.cpp:169-172,33`） | 边界 |
| AC-3.3 | WHEN `currentIndex` 非有限/负数/非整数/超 int32 THEN 报 `INVALID_VALUE` 告警并回退 0（`NavContainerComponent.cpp:177-186`） | 异常 |
| AC-3.4 | WHEN `currentIndex >= childCount` THEN `ClampCurrentIndex` 裁剪到 `len-1` 并报越界告警（`NavContainerComponent.cpp:190-195`） | 边界 |
| AC-3.5 | WHEN `ClampCurrentIndex` 且 `childCount==0` 或 index<0 THEN 返回 0（`NavContainerComponent.cpp:35-47`） | 边界 |

### US-4: 子页面可见性切换

**作为** 生成式 UI 宿主开发者,
**我想要** 仅当前页可见、其余页隐藏,
**以便** 容器只显示被激活的子页面。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `RefreshChildVisibility` 执行 THEN 仅 `ResolveVisibleIndex` 对应子节点设 `VISIBLE`，其余 `NONE`（`NavContainerComponent.cpp:219-237`） | 正常 |
| AC-4.2 | WHEN children 为空 THEN `RefreshChildVisibility` 直接返回（`NavContainerComponent.cpp:222-224`） | 边界 |
| AC-4.3 | WHEN 某子节点为 null THEN 跳过并 `++index` 继续（`NavContainerComponent.cpp:229-232`） | 边界 |

### US-5: navigate 函数路由

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `navigate` 函数切换到指定子页面,
**以便** 按组件 id 而非索引进行导航。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `navigate` 函数被调用 THEN `NativeNavigateFunction::GetName()` 返回 `"navigate"`（`NativeNavigateFunction.cpp:57-60`） | 正常 |
| AC-5.2 | WHEN `ExecuteWithContext` 解析 `componentId`/`targetComponentId` 均非空 THEN 经 `FindSurfaceForContext` + `FindComponentById` 定位组件（`NativeNavigateFunction.cpp:72-85`） | 正常 |
| AC-5.3 | WHEN `componentId`/`targetComponentId` 任一为空或非 string THEN 返回 `FunctionResult(false)`（`NativeNavigateFunction.cpp:74-76,29-53`） | 异常 |
| AC-5.4 | WHEN 组件非 `NavContainerComponent`（`dynamic_pointer_cast` 失败） THEN 告警并返回 false（`NativeNavigateFunction.cpp:86-92`） | 异常 |
| AC-5.5 | WHEN `NavigateToTargetComponent(targetComponentId)` 执行 THEN 按子组件 id 匹配索引 → `SetCurrentIndex` → `RefreshChildVisibility`；目标不存在返回 false（`NavContainerComponent.cpp:141-165`） | 正常 |
| AC-5.6 | WHEN 目标组件 id 为空 THEN 直接返回 false（`NavContainerComponent.cpp:143-145`） | 边界 |

### US-6: 属性声明（currentIndex 动态支持）

**作为** 生成式 UI 宿主开发者,
**我想要** `currentIndex` 支持动态值/表达式/绑定,
**以便** 数据模型变化驱动页面切换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `GetPrivatePropertyDeclaration("currentIndex")` THEN 返回 `NUMBER` 类型、`allowDynamic=true`、`allowExpression=true`、`fallbackNumber=0` 的声明（`NavContainerComponent.cpp:96-107`） | 正常 |
| AC-6.2 | WHEN `ApplyPrivateAttributes` THEN 捕获 descriptor 的 currentIndex/childCount 后 `ApplySchemaProperty("currentIndex")` 再 `RefreshChildVisibility`（`NavContainerComponent.cpp:60-76`） | 正常 |
| AC-6.3 | WHEN 非 descriptor 属性更新（如数据模型绑定触发）THEN `ResolveCurrentIndexValidationChildCount` 用 `GetChildren().size()` 而非 descriptor 计数（`NavContainerComponent.cpp:211-217`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-3 | C++ 静态比对 + ArkTS 名表 | `ExtendedComponentFactory.cpp:122`、`NavContainerComponent.cpp:51-58`、`A2UIExtendedComponents.ets:38,57` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-3 | C++ UT：children 解析/校验 | `NavContainerComponent.cpp:60-94,117-134` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-3 | C++ UT：currentIndex 裁剪 | `NavContainerComponent.cpp:33-47,167-199` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-3 | C++ UT：可见性切换 | `NavContainerComponent.cpp:219-237` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 | R-5 | T-3 | C++ UT：navigate 路由 | `NativeNavigateFunction.cpp:57-96`、`NavContainerComponent.cpp:141-165` |
| AC-6.1,AC-6.2,AC-6.3 | R-6 | T-3 | C++ UT：属性声明 | `NavContainerComponent.cpp:96-115,211-217` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor `component=="NavContainer"` | 注册为 native COLUMN 节点组件 | 经 `ExtendedComponentFactory` | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 边界 | children 解析/校验 | 静态列表/模板解析；空数组 ALLOW | 子项增删改刷新可见性 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 边界 | currentIndex 校验 | 非法回退 0；越界裁剪到 `len-1` 并告警 | 非负整数；clamp 空子项回退 0 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | 子页面可见性 | 仅当前索引 VISIBLE，其余 NONE | 空子项直接返回 | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 行为 | navigate 路由 | 按 componentId/targetComponentId 定位并切换 | 目标/组件非法返回 false | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 |
| R-6 | 行为 | 属性声明 | currentIndex 动态/表达式/绑定支持 | fallback 0 | AC-6.1,AC-6.2,AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 注册/节点 | 静态比对 | RegisterComponent、COLUMN、GetType |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 children | C++ UT | 静态/模板/空数组、增删改 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 currentIndex | C++ UT | 非法回退、越界裁剪、告警 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 可见性 | C++ UT | VISIBLE/NONE 切换 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 navigate | C++ UT | 定位、dynamic_cast、目标匹配 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3 属性声明 | C++ UT | allowDynamic/allowExpression/fallback |

## API 变更分析

> 存量补录，无新增/变更公开 ArkTS/C-API。本节列出受影响组件协议与函数。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `NavContainer` 扩展组件协议（`children`/`currentIndex`） | 既有 | 多子页面导航容器 | 无 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3 |
| `navigate` 扩展函数（`call:"navigate"`，args `componentId`/`targetComponentId`，`returnType:"void"`） | 既有 | 子页面路由 | `interactionOnly` 函数，仅交互场景 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-5.6 |

> Schema 位置：`genui/src/main/resources/rawfile/schema/Extended/components/NavContainer.json`（required `["component"]`，properties `children`/`currentIndex`）与 `functions/navigate.json`（`interactionOnly:true`，args `componentId`/`targetComponentId`）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NavContainerComponent::NavigateToTargetComponent(targetComponentId)`（`NavContainerComponent.cpp:141`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool NavigateToTargetComponent(const std::string& targetComponentId)` |
| 返回值 | `bool` — 目标存在且切换成功返回 true；目标为空/不存在返回 false |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-5.5,AC-5.6 |

**`NativeNavigateFunction::ExecuteWithContext(resolvedArgs, context)`（`NativeNavigateFunction.cpp:69`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult ExecuteWithContext(const JsonValue& resolvedArgs, const DynamicResolveContext& context)` |
| 返回值 | `FunctionResult` — 成功 true，参数空/组件非 NavContainer/目标不存在 false |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| currentIndex | number/dynamic | 否 | 0 | 非负整数；越界裁剪 `[0, len-1]` |
| children | array/template | 否 | `[]` | 静态 id 列表或 `{componentId,path}` |
| componentId | string | 是 | — | 非空；须为 NavContainer 组件 id |
| targetComponentId | string | 是 | — | 非空；须为子页面组件 id |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | currentIndex 合法 | 显示对应子页面 | AC-3.1 |
| 2 | currentIndex 非法 | 回退 0 + 告警 | AC-3.2,AC-3.3 |
| 3 | currentIndex 越界 | 裁剪到 `len-1` + 告警 | AC-3.4 |
| 4 | navigate 目标存在 | 切换当前页 | AC-5.5 |
| 5 | navigate 组件非 NavContainer | 返回 false | AC-5.4 |
| 6 | navigate 目标不存在 | 返回 false | AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API Version 20；鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 组件协议与函数 schema 经 JSON Schema 约束；无 `@since` 标注差异。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| Native 组件 | NavContainer 走 C++（`COLUMN` 节点）而非 ArkTS | AC-1.1,AC-1.2 |
| 索引裁剪 | 非负整数 + 裁剪到 `[0, len-1]`，非法回退 0 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| 路由语义 | navigate 按子组件 id 匹配索引，非直接设索引 | AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 currentIndex/目标不存在不崩溃，返回 false 或回退 | C++ UT | `NavContainerComponent.cpp:167-199,141-165` |
| 性能 | 可见性切换仅遍历子节点一次 | C++ UT | `NavContainerComponent.cpp:219-237` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | native COLUMN 节点通用能力 | ohosTest | `NavContainerComponent.cpp:51-53` |
| 平板 | 无差异 | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异 | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | NavContainer 无专属无障碍属性 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version 20；扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | 鸿蒙扩展协议组件 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: NavContainer 扩展导航容器
  作为 生成式 UI 宿主开发者
  我想要 在多子页面间按索引或 navigate 函数切换
  以便 仅显示被激活的子页面

  Scenario: currentIndex 驱动页面切换
    Given NavContainer 含 3 个子页面且 currentIndex=1
    When 引擎应用属性
    Then 仅第 1 个子页面 VISIBLE，其余 NONE

  Scenario: navigate 函数路由
    Given NavContainer 含子页面 pageA/pageB
    When 调用 navigate(componentId="nav", targetComponentId="pageB")
    Then 当前页切换到 pageB

  Scenario Outline: currentIndex 越界处理
    Given NavContainer 含 3 个子页面且 currentIndex=<value>
    When 应用属性
    Then <expected>

    Examples:
      | value | expected |
      | -1 | 回退 0 |
      | 5 | 裁剪到 2 |
      | 2.5 | 回退 0 并告警 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（NavContainer 导航容器 + navigate 路由；导航栈语义不涉及）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NavContainerComponent ApplyCurrentIndexValue ClampCurrentIndex RefreshChildVisibility NavigateToTargetComponent"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeNavigateFunction ExecuteWithContext navigate componentId targetComponentId dynamic_pointer_cast"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedComponentFactory RegisterComponent NavContainer COLUMN A2UINodeType"
```

**关键文档：** `genui/src/main/cpp/components/extended/NavContainerComponent.cpp`、`genui/src/main/cpp/functions/extended/NativeNavigateFunction.cpp`、`genui/src/main/ets/core/functions/extended/NavigateFunction.ets`