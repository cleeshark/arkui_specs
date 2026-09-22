# 特性规格

> Func-07-04-12-Feat-04 Toggle 扩展交互组件：固化 A2UI 扩展协议交互组件 Toggle 的属性契约（`label`/`isOn`/`enabled`）、样式契约（选中色/未选中色/滑块色）、开关变化事件（`onChange {isOn}`）、非布尔表达式 `isOn` 推断与绑定回写语义。基准实现：`@arkui-genius/genui`（A2UIRender），原生 C++ 路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Toggle 扩展交互组件 |
| 特性编号 | Func-07-04-12-Feat-04 |
| 优先级 | P1 |
| 目标版本 | A2UI 扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 存量特性（lineage: new-on-legacy） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/12-a2ui-extended-interaction-components/design.md` | Baselined |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（`components.Toggle`） | — |
| 原生组件（C++） | `genui/src/main/cpp/components/extended/ExtendedToggleComponent.h/.cpp` | — |
| 文档参考 | `reference/extended-components/toggle.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 开关状态属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `isOn` 控制开关状态，
**以便** 正确呈现开/关态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `isOn=true` THEN `SetIsOn(true)` 调用 `SetNodeToggleValue` 置开（`ExtendedToggleComponent.cpp:388-395`） | 正常 |
| AC-1.2 | WHEN `isOn` 缺失 THEN 回落 `false`（`fallbackBool=false`，`ExtendedToggleComponent.cpp:182-190`） | 边界 |
| AC-1.3 | WHEN `isOn` 为表达式解析为非布尔 number THEN `值!=0` 为 true（`ApplyNonBoolExpressionIsOn`，`ExtendedToggleComponent.cpp:161-162`） | 边界 |
| AC-1.4 | WHEN `isOn` 表达式解析为 string THEN 非空且非 `"false"`/`"0"` 为 true（`ExtendedToggleComponent.cpp:163-165`） | 边界 |
| AC-1.5 | WHEN `isOn` 属性被移除 THEN `OnPropertyRemoved` 复位 false（`ExtendedToggleComponent.cpp:277-279`） | 边界 |

### US-2: 交互状态与标签契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `enabled`/`label` 控制交互态与标签，
**以便** 禁用开关或显示说明文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `enabled=false` THEN `SetEnabled(false)` 使开关不可交互（`ExtendedToggleComponent.cpp:397-404`） | 正常 |
| AC-2.2 | WHEN `label` 字符串 THEN `SetLabel` 写入 `textNode_` 文本（`ExtendedToggleComponent.cpp:433-440`） | 正常 |
| AC-2.3 | WHEN `label` 缺失或移除 THEN 回落/复位 `""`（`ExtendedToggleComponent.cpp:180,286-288`） | 边界 |

### US-3: 开关变化事件与绑定回写

**作为** 生成式 UI 宿主开发者，
**我想要** 监听开关变化，
**以便** 通过 `onChange` 处理并回写绑定状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 用户切换开关且 `isOn` 变化 THEN `HandleToggleChange` 派发 `onChange`，负载 `{isOn:boolean}`（`ExtendedToggleComponent.cpp:357-366,43-52`） | 正常 |
| AC-3.2 | WHEN `isOn` 无变化 THEN `HandleToggleChange` 直接返回不派发（`ExtendedToggleComponent.cpp:359-361`） | 边界 |
| AC-3.3 | WHEN `isOn` 存在 path 绑定 THEN `SyncIsOnToBoundDataModel` 回写数据模型（`ExtendedToggleComponent.cpp:453-481`） | 正常 |
| AC-3.4 | THEN 监听始终注册（`UpdateChangeEventRegistration` `shouldRegister=true`），即使无绑定（`ExtendedToggleComponent.cpp:368-386`） | 正常 |

### US-4: 样式契约与告警回落

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `styles` 控制开关颜色，
**以便** 非法样式告警回落主题默认。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `styles.selectedColor`/`unSelectedColor`/`switchPointColor` 合法 THEN 应用对应颜色（`ExtendedToggleComponent.cpp:245-255`） | 正常 |
| AC-4.2 | WHEN 颜色非法/无法解析 THEN 告警并回落主题默认色（`ValidateStylesSchema`，`ExtendedToggleComponent.cpp:211-238`） | 异常 |
| AC-4.3 | WHEN 主题切换且无覆盖 THEN 重设默认选中色 light `0xFF007DFF`/dark `0xFF006CDE`（`ExtendedToggleComponent.cpp:257-268,36-37`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-4 | C++ UT（`GetIsOnForTest`） | `ExtendedToggleComponent.cpp:142-167,388-395` |
| AC-2.1,AC-2.2,AC-2.3 | R-3 | T-4 | C++ UT | `ExtendedToggleComponent.cpp:397-440` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-4,R-5 | T-4 | C++ UT + ohosTest | `ExtendedToggleComponent.cpp:357-386` |
| AC-4.1,AC-4.2,AC-4.3 | R-6 | T-4 | C++ UT + 告警 | `ExtendedToggleComponent.cpp:245-268` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `isOn` 布尔设置 | `SetNodeToggleValue` 置开关 | 默认 false | AC-1.1,AC-1.2 |
| R-2 | 边界 | `isOn` 非布尔表达式 | number!=0/非空非"false"非"0"string 判 true | 表达式解析路径 | AC-1.3,AC-1.4,AC-1.5 |
| R-3 | 行为 | `enabled`/`label` 设置 | 交互态切换/标签呈现 | 移除复位 | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 行为 | 开关状态变化 | 派发 onChange `{isOn}` + 回写绑定 | 无变化不派发 | AC-3.1,AC-3.2,AC-3.3 |
| R-5 | 行为 | 监听注册 | 始终注册（getToggleValue 场景） | `shouldRegister=true` | AC-3.4 |
| R-6 | 异常 | 颜色样式非法 | 告警回落主题默认 | 不中断渲染 | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 isOn | C++ UT | 布尔/非布尔表达式推断/移除复位 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 交互态 | C++ UT | enabled/label 契约 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 事件 | C++ UT + ohosTest | onChange 负载 + 绑定回写 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 样式 | C++ UT + 告警 | 三色默认值 + 主题切换 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 扩展协议组件 `Toggle`（`extended_catalog.json`） | 既有 | 开关切换渲染 | 描述符契约，无迁移 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`Toggle` 组件描述符（`components.Toggle`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 组件描述符（JSON object），`GetType()=="Toggle"`（`ExtendedToggleComponent.cpp:129-132`） |
| 返回值 | 复合 `ROW` 节点（内挂 `TOGGLE`+`TEXT`） |
| 开放范围 | 扩展协议组件契约（非 ArkTS/C-API） |
| 错误码 | N/A（非法样式经 `ReportExtendedSchemaWarning` 上报告警） |
| 关联 AC | AC-1.1,AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| label | string | 否 | `""` | 任一字符串 |
| isOn | boolean | 否 | `false` | 缺失回落 false |
| enabled | boolean | 否 | `true` | 缺失回落 true |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 用户切换开关 | 派发 onChange{isOn} + 回写绑定 | AC-3.1,AC-3.3 |
| 2 | isOn 非布尔表达式 | 推断 boolean | AC-1.3,AC-1.4 |
| 3 | 颜色非法 | 告警回落主题默认 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 1.0.0。
- **API 版本号策略:** `isOn` 支持表达式/绑定（扩展协议独有）；`onChange` 负载键 `{isOn}`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生路径 | Toggle 走 C++ 原生组件（`ExtendedComponentFactory.cpp:115`） | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3 |
| 复合节点 | ROW 内含 TOGGLE+TEXT 两子节点 | AC-2.2 |
| 绑定回写 | isOn 绑定在变化时回写 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，告警回落 | C++ UT | `ExtendedToggleComponent.cpp:211-238` |
| 性能 | 事件负载构造 O(1) | C++ UT | `ExtendedToggleComponent.cpp:43-52` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 组件契约设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 通用 `accessibility.label/description` | 概述「组件公共结构」 |
| 大字体 | 否 | 无文字字号配置 | — |
| 深色模式 | 是 | 三色按主题切换 | AC-4.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | `isOn` 表达式推断扩展行为 | AC-1.3,AC-1.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Toggle 扩展交互组件
  作为 生成式 UI 宿主开发者
  我想要 开关支持状态/标签/颜色与变化监听
  以便 提供二元开关交互

  Scenario: 用户切换开关
    Given Toggle 描述符 isOn=false
    When 用户切换到开
    Then 派发 onChange{isOn:true}

  Scenario Outline: 非布尔 isOn 推断
    Given Toggle 描述符 isOn=<expr>
    When 应用组件描述符
    Then isOn 推断为 <expected>

    Examples:
      | expr | expected |
      | 1 | true |
      | 0 | false |
      | "yes" | true |
      | "0" | false |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 做 Toggle 组件契约；`getToggleValue` 归 07-04-16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedToggleComponent isOn 非布尔表达式推断 onChange 绑定回写 SyncIsOnToBoundDataModel"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedToggleComponent selectedColor unSelectedColor switchPointColor 主题默认色"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/components/extended/ExtendedToggleComponent.cpp`、`reference/extended-components/toggle.md`