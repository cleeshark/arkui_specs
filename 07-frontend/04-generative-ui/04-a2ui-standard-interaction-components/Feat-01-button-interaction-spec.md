# 特性规格

> Func-07-04-04-Feat-01 Button 交互组件：固化 A2UI v0.9 标准 `Button` 组件的子节点（`child`）、点击响应（`action` 支持 `event`/`functionCall` 双形式）、样式变体（`variant`：default/primary/borderless，非法回退 default）与客户端校验（`checks` 失败即禁用）。基准实现：`@arkui-genius/genui`（A2UIRender），原生组件 `ButtonComponent`（`markInnerNative(true)`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Button 交互组件 |
| 特性编号 | Func-07-04-04-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9（API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-04 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/04-a2ui-standard-interaction-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIButton.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/components/A2UI/button/ButtonComponent.cpp`、`ButtonComponent.h` | — |
| 主题（C++） | `genui/src/main/cpp/components/A2UI/button/ButtonTheme.cpp/h` | — |
| 组件参考（Docs） | `reference/standard-components/button.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Button 组件以 `component="Button"` 注册为标准原生组件,
**以便** DSL 声明被引擎正确实例化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DSL 声明 `"component":"Button"` THEN 引擎经 `A2UIButton.asCatalogItem()` 注册，`type='Button'`（`A2UIButton.ets:25,31-36`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN 标记 `markCategory(A2UI_STANDARD)` 且 `markInnerNative(true)`（`A2UIButton.ets:34`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `SchemaResourceLoader.loadA2UISchema(version,'components/Button.json')` 命中 v0.9 schema（`A2UIButton.ets:27-29`） | 正常 |

### US-2: 子节点约束

**作为** 生成式 UI 宿主开发者,
**我想要** Button 子节点仅接受 Text/Icon 类型,
**以便** 其他类型子组件被忽略。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 添加子组件且其类型为 `Text` 或 `Icon` THEN `OnAddChild` 接受并缓存 `childComponent_` 且应用子节点视觉样式（`ButtonComponent.cpp:141-149`） | 正常 |
| AC-2.2 | WHEN 添加子组件且类型非 `Text`/`Icon`（或为 null） THEN `OnAddChild` 直接返回，不缓存（`ButtonComponent.cpp:143-145`） | 异常 |
| AC-2.3 | WHEN 移除子组件且为当前缓存子节点 THEN 重置 `childComponent_`，若为 `Text` 则 `ResetFontColor`（`ButtonComponent.cpp:151-165`） | 正常 |
| AC-2.4 | WHEN Icon 子节点应用样式 THEN 按钮尺寸取 `ButtonTheme::GetIconButtonSize()`，type 设 `CIRCLE`；Text 子节点则设 `CAPSULE` 并重置宽度（`ButtonComponent.cpp:229-242`） | 正常 |

### US-3: 样式变体

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `variant` 控制按钮样式,
**以便** 表达默认/主按钮/无边框三种样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `variant` 为 `"default"`/`"primary"`/`"borderless"` THEN `ResolveVariant` 原样返回（`ButtonComponent.cpp:43-45`） | 正常 |
| AC-3.2 | WHEN `variant` 为非法字符串 THEN `ResolveVariant` 回退 `"default"`（`ButtonComponent.cpp:46-47`） | 边界 |
| AC-3.3 | WHEN `SetVariant` 变更 THEN `variant_` 更新并 `SetBackgroundColor(theme->GetBackgroundColor(variant_))` + `ApplyChildVisualStyle`（`ButtonComponent.cpp:167-179`） | 正常 |
| AC-3.4 | WHEN `variant` 字段声明 THEN 类型 `ENUM_STRING`，`enumAllowed={default,primary,borderless}`，`enumFallback=default`，`fallbackString=default`（`ButtonComponent.cpp:60-71`） | 正常 |

### US-4: 点击响应（action）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `action` 定义点击响应（服务器事件或客户端函数）,
**以便** 点击按钮触发对应行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 描述符含 `action` 且 `actionInfo_` 有效 THEN 注册 `onClick` 回调执行 `DispatchAction`（`ButtonComponent.cpp:134-136`） | 正常 |
| AC-4.2 | WHEN action 类型为 `EVENT` THEN 解析事件上下文并 `ActionDispatchBridge::Dispatch` 上报（`ButtonComponent.cpp:307-314`） | 正常 |
| AC-4.3 | WHEN action 类型为 `FUNCTION_CALL` THEN `DispatchFunctionCallAction` 解析描述符，命中 `NativeActionRegistry` 则本地执行，否则经 `FunctionBridge::Invoke`（`ButtonComponent.cpp:317-355`） | 正常 |
| AC-4.4 | WHEN `functionCall` 解析失败 THEN 回退 raw args 并打 warn 日志（`ButtonComponent.cpp:333-336`） | 异常 |
| AC-4.5 | WHEN `action` 缺省（未设置） THEN 按钮点击无响应（`actionInfo_=null`，`DispatchAction` 直接返回，`ButtonComponent.cpp:298-301`） | 边界 |

### US-5: 客户端校验（checks）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `checks` 约束按钮可点状态,
**以便** 任一校验不通过时按钮禁用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 描述符含 `checks` THEN `ParseChecks` 解析规则并注册绑定路径（`ButtonComponent.cpp:256-265`） | 正常 |
| AC-5.2 | WHEN `ValidateChecks()` 返回 false THEN `SetEnabled(false)` 禁用按钮（`ButtonComponent.cpp:251-254,284-296`） | 正常 |
| AC-5.3 | WHEN 校验失败 THEN 打 `Button check failed` warn 日志并携带 message（`ButtonComponent.cpp:291-294`） | 异常 |
| AC-5.4 | WHEN 绑定路径数据更新且属性名以 `__checks_dep_` 前缀 THEN `RefreshEnabledState` 重新校验（`ButtonComponent.cpp:115-121,279-282`） | 正常 |
| AC-5.5 | WHEN `checks` 未设置 THEN `ValidateChecks` 恒 true，按钮保持可点（`ButtonComponent.cpp:284-288`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-1 | ArkTS 单测：目录注册与 schema 加载 | `A2UIButton.ets:25-36` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2,R-3 | T-1 | C++ UT：`OnAddChild`/`ApplyChildVisualStyle` | `ButtonComponent.cpp:141-244` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-4 | T-1 | C++ UT：`ResolveVariant`/`SetVariant` | `ButtonComponent.cpp:40-79,167-179` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-5,R-6 | T-1 | C++ UT：`DispatchAction` 分支 | `ButtonComponent.cpp:298-355` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-7,R-8 | T-1 | C++ UT：`ValidateChecks`/`RefreshEnabledState` | `ButtonComponent.cpp:251-296` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | DSL `component="Button"` | 注册为标准原生组件（A2UI_STANDARD + innerNative） | type 固定 Button | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | 添加 Text/Icon 子组件 | 缓存 childComponent_ 并应用视觉 | 仅 Text/Icon | AC-2.1,AC-2.4 |
| R-3 | 异常 | 添加非 Text/Icon 子组件 | 忽略，不缓存 | null 也忽略 | AC-2.2 |
| R-4 | 边界 | variant 非法 | 回退 default | 枚举 default/primary/borderless | AC-3.1,AC-3.2,AC-3.4 |
| R-5 | 行为 | action 为 event | 上报服务器事件 | 上下文经 EventContextResolver 解析 | AC-4.1,AC-4.2 |
| R-6 | 行为 | action 为 functionCall | 执行客户端函数 | NativeAction 优先，否则 FunctionBridge | AC-4.1,AC-4.3,AC-4.4 |
| R-7 | 异常 | checks 校验失败 | 禁用按钮（SetEnabled=false） | message 记录 warn 日志 | AC-5.2,AC-5.3 |
| R-8 | 边界 | checks 缺失 | 校验恒通过，按钮可点 | checksEngine 为空返回 true | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 | type、markInnerNative、schema 路径 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 子节点约束 | C++ UT | Text/Icon 接受、非法忽略、视觉样式 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 变体 | C++ UT | 枚举回退、SetVariant 副作用 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 action | C++ UT | event/functionCall 分支、null 直返 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 checks | C++ UT | 禁用刷新、缺省可点 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。Button 以 DSL 组件暴露。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Button`（DSL 组件） | 既有 | `component` 字段匹配 | 经 `CatalogItem.forComponent` 注册 | AC-1.1,AC-1.2,AC-1.3 |

> d.ts 位置：组件 schema `rawfile/schema/A2UI/v0.9/components/Button.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ButtonComponent`（原生，`component="Button"`）**

| 属性 | 值 |
|------|-----|
| 组件签名 | `ButtonComponent : public A2UIComponent`，`GetType()="Button"`（`ButtonComponent.h:34-38`、`ButtonComponent.cpp:110-113`） |
| 必填属性 | `action`（`GetComponentDirectRequiredPropertyKeys` 返回 `{"action"}`，`ButtonComponent.cpp:105-108`） |
| 开放范围 | DSL 标准组件（inner-native） |
| 错误码 | N/A（结构问题经 schema 告警 2001 上报） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| child | string(ComponentId) | 是 | "" | 仅引用 Text/Icon 组件 id |
| action | Action | 是 | {} | event 或 functionCall 之一 |
| variant | string | 否 | "default" | default/primary/borderless，非法回退 default |
| checks | CheckRule[] | 否 | [] | required/regex/length/numeric/email |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 声明 Button 并带合法 child/action | 实例化并注册 onClick | AC-1.1,AC-4.1 |
| 2 | action=event | 点击上报事件 | AC-4.2 |
| 3 | action=functionCall | 点击执行本地函数 | AC-4.3 |
| 4 | checks 失败 | 按钮禁用 | AC-5.2 |
| 5 | variant 非法 | 回退 default 样式 | AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本经 `SchemaResourceLoader.loadA2UISchema(version,...)` 加载。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生实现路径 | Button 标记 `markInnerNative(true)`，渲染在 C++ | AC-1.2 |
| 子节点白名单 | 仅 Text/Icon 可选为子节点 | AC-2.1,AC-2.2 |
| checks 失败即禁用 | 与 TextField/ChoicePicker 语义不同 | AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 variant/子节点不崩溃，统一回退或忽略 | C++ UT | `ButtonComponent.cpp:40-48,141-149` |
| 性能 | FunctionCall 解析失败回退 raw args 不阻塞 | C++ UT | `ButtonComponent.cpp:330-336` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 交互行为设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | Button 依赖底层 ArkUI 按钮无障碍语义 | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 字体由子 Text 组件承载 | — |
| 深色模式 | 是 | `OnConfigChange` 重设背景色（`ButtonComponent.cpp:378-386`） | AC-3.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 Button 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Button 交互组件
  作为 生成式 UI 宿主开发者
  我想要 Button 支持变体/点击/校验
  以便 表达可交互按钮

  Scenario: 主按钮点击上报服务器事件
    Given DSL 声明 Button 且 action 为 event（name="button.event"）
    When 用户点击按钮
    Then ActionDispatchBridge 上报该事件

  Scenario: 校验失败按钮禁用
    Given Button 声明 checks 且条件不满足
    When 引擎校验 checks
    Then 按钮 SetEnabled(false)

  Scenario Outline: 变体归一
    Given Button 声明 variant=<variant>
    When 应用变体
    Then 解析为 <resolved>
    Examples:
      | variant      | resolved   |
      | "primary"    | "primary"  |
      | "borderless" | "borderless" |
      | "weird"      | "default"  |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Button 组件行为；checks 函数归 07-04-07，action 链归 07-04-22）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ButtonComponent variant action checks DispatchAction ResolveVariant"
  - repo: "GenerativeUI/A2UIRender"
    query: "A2UIButton asCatalogItem markInnerNative schemaProvider"
  - repo: "GenerativeUI/Docs"
    query: "Button 组件 child variant action checks"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/A2UIButton.ets`、`genui/src/main/cpp/components/A2UI/button/ButtonComponent.cpp`、`reference/standard-components/button.md`