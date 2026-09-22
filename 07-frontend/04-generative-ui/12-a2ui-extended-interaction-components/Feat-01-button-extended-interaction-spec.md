# 特性规格

> Func-07-04-12-Feat-01 Button 扩展交互组件：固化 A2UI 扩展协议（`ohos.a2ui.extended.catalog`）交互组件 Button 的属性契约（`label` 必填 + `text` 别名、`enabled`、`action`）、样式契约（字体颜色/字号/字重/自适应字号/字号缩放/背景色）、点击行为（`action` 优先于 `onClick`）与默认值/告警回落语义。基准实现：`@arkui-genius/genui`（A2UIRender），原生 C++ 路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Button 扩展交互组件 |
| 特性编号 | Func-07-04-12-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-12 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/12-a2ui-extended-interaction-components/design.md` | Baselined |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（`components.Button`） | — |
| 原生组件（C++） | `genui/src/main/cpp/components/extended/ExtendedButtonComponent.h/.cpp` | — |
| 目录注册（C++） | `genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp` | — |
| 文档参考 | `reference/extended-components/button.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 文本标签属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `label`（及别名 `text`）设置按钮文案，
**以便** 正确呈现按钮可读文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 描述符含 `label` 字符串 THEN `SetLabel` 写入 `labelValue_` 并调用 `SetNodeButtonLabel`（`ExtendedButtonComponent.cpp:547-551`） | 正常 |
| AC-1.2 | WHEN 描述符含 `text` 且不含 `label` THEN `ApplyPrivateAttributes` 按 `text` 处理（等价 `label`）（`ExtendedButtonComponent.cpp:145-149`） | 正常 |
| AC-1.3 | WHEN `label` 缺失 THEN `label` 属性 `fallbackString=""`，按钮文案为空（`ExtendedButtonComponent.cpp:181-187`） | 边界 |
| AC-1.4 | WHEN `label` 属性被移除 THEN `OnPropertyRemoved` 复位为 `""`（`ExtendedButtonComponent.cpp:533-535`） | 异常 |

### US-2: 可交互状态属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `enabled` 控制按钮可交互性，
**以便** 禁用态按钮不可点击且视觉区分。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `enabled=true` 或缺失 THEN 按钮可交互（`enabled_` 默认 true，`ExtendedButtonComponent.h:151`） | 正常 |
| AC-2.2 | WHEN `enabled=false` THEN `SetEnabled(false)` 调用 `SetNodeEnabled` 使按钮不可交互（`ExtendedButtonComponent.cpp:566-570`） | 正常 |
| AC-2.3 | WHEN `enabled` 属性被移除 THEN `OnPropertyRemoved` 复位为 true（`ExtendedButtonComponent.cpp:537-539`） | 边界 |

### US-3: 点击行为与 action 优先级

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `action` 或 `onClick` 处理点击，
**以便** `action` 优先于 `onClick`，只有无有效 action 时回退到 `onClick`。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 描述符含合法 `action` THEN `SetAction` 经 `ActionParser::Parse` 生成有效 `actionInfo_`（`ExtendedButtonComponent.cpp:713-721`） | 正常 |
| AC-3.2 | WHEN `actionInfo_` 有效 THEN 点击经 `DispatchActionInfo("action", ...)` 分发，不触达 `onClick`（`ExtendedButtonComponent.cpp:511-512`） | 正常 |
| AC-3.3 | WHEN 无 `action` 且含 `onClick` 事件 THEN 点击经 `DispatchEvent("onClick", ...)` 分发（`ExtendedButtonComponent.cpp:513-514`） | 正常 |
| AC-3.4 | WHEN 既无 action 也无 onClick THEN 清除点击监听 `RegisterOnClickWithContext(nullptr)`（`ExtendedButtonComponent.cpp:517-522`） | 边界 |
| AC-3.5 | WHEN `action` 属性被移除 THEN `OnPropertyRemoved` 调用 `ClearAction`（`ExtendedButtonComponent.cpp:541-543`） | 边界 |

### US-4: 样式契约与告警回落

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `styles` 控制字体与背景样式，
**以便** 非法样式触发 schema 告警并回落默认值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `styles.fontSize` 为正数 THEN `SetFontSize` 应用该字号（`ExtendedButtonComponent.cpp:377-389`） | 正常 |
| AC-4.2 | WHEN `styles.fontSize` 缺失或非法 THEN 回落 `DEFAULT_BUTTON_FONT_SIZE=16.0F`（`ExtendedButtonComponent.cpp:38,383-385`） | 异常 |
| AC-4.3 | WHEN `styles.fontWeight` 非法（非 100~900 步进 100 或非法字符串） THEN 回落 `DEFAULT_BUTTON_FONT_WEIGHT=W500`（`ExtendedButtonComponent.cpp:391-404`） | 异常 |
| AC-4.4 | WHEN `styles.fontColor` 无法解析 THEN 回落主题默认文字色（light `0xFF0A59F7`/dark `0xFF5291FF`）（`ExtendedButtonComponent.cpp:469-481,70-73`） | 异常 |
| AC-4.5 | WHEN 传入非法样式 THEN `ValidateComponentSpecificStylesSchema` 经 `ReportExtendedSchemaWarning` 上报告警（`ExtendedButtonComponent.cpp:220-234,247`） | 异常 |
| AC-4.6 | WHEN 主题模式切换 THEN `OnConfigChange` 无覆盖时重设默认文字/背景色（`ExtendedButtonComponent.cpp:498-506`） | 边界 |

### US-5: 必填属性声明

**作为** 生成式 UI 宿主开发者，
**我想要** 引擎声明必需的组件属性，
**以便** 缺失必填属性时按 schema 被拒绝。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | THEN `GetComponentDirectRequiredPropertyKeys` 返回 `{"label"}`（`ExtendedButtonComponent.cpp:215-218`），与 schema `required:["component","label"]` 一致 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-1 | C++ UT（TDD_BUILD `GetLabelForTest`） | `ExtendedButtonComponent.cpp:143-156,547-551` |
| AC-2.1,AC-2.2,AC-2.3 | R-3 | T-1 | C++ UT | `ExtendedButtonComponent.cpp:566-570` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-4,R-5 | T-1 | C++ UT + 点击分发 | `ExtendedButtonComponent.cpp:508-529,713-726` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 | R-6,R-7 | T-1 | C++ UT + 告警 | `ExtendedButtonComponent.cpp:377-506` |
| AC-5.1 | R-8 | T-1 | 静态比对 schema | `ExtendedButtonComponent.cpp:215-218` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 描述符含 `label`/`text` 字符串 | 写入 `labelValue_` 经 `SetNodeButtonLabel` 呈现 | `text` 为 `label` 别名，仅无 `label` 时生效 | AC-1.1,AC-1.2 |
| R-2 | 边界 | `label` 缺失或移除 | 回落/复位为 `""` | fallbackString="" | AC-1.3,AC-1.4 |
| R-3 | 行为 | `enabled` 布尔设置 | `SetNodeEnabled` 控制交互态 | 默认 true，移除复位 true | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 行为 | `action` 合法 | 点击分发 `action`（`DispatchActionInfo`） | action 优先于 onClick | AC-3.1,AC-3.2,AC-3.5 |
| R-5 | 边界 | 无 action 有 onClick / 两者皆无 | 分发 onClick / 清除监听 | 回退语义 | AC-3.3,AC-3.4 |
| R-6 | 异常 | 样式非法（fontSize/fontWeight/fontColor/字缩放宽幅） | 告警并回落默认值 | 不中断渲染 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-7 | 行为 | 主题切换 | 无用户覆盖时重设主题默认色 | `hasFontColor_`/`hasBackgroundColor_` 门控 | AC-4.6 |
| R-8 | 行为 | 组件实例化 | 必填键声明 `{label}` 与 schema 一致 | — | AC-5.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 标签契约 | C++ UT | label/text 别名、缺失/移除复位 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 交互态 | C++ UT | enabled 默认/显式/复位 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 点击 | C++ UT | action > onClick 优先级 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 样式 | C++ UT + 告警 | 默认值回落、主题切换 |
| VM-5 | AC-5.1 必填 | 静态比对 | schema required 与 `GetComponentDirectRequiredPropertyKeys` |

## API 变更分析

> 存量补录，无新增/变更 API。组件由 JSON 描述符驱动。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 扩展协议组件 `Button`（`extended_catalog.json`） | 既有 | 交互按钮渲染 | 描述符契约，无迁移 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`Button` 组件描述符（`components.Button`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 组件描述符（JSON object），`GetType()=="Button"`（`ExtendedButtonComponent.cpp:138-141`） |
| 返回值 | 原生 `BUTTON` 节点（`ArkUINodeApiAdapter::CreateNode(A2UINodeType::BUTTON)`） |
| 开放范围 | 扩展协议组件契约（非 ArkTS/C-API） |
| 错误码 | N/A（非法属性/样式经 `ReportExtendedSchemaWarning` 上报告警） |
| 关联 AC | AC-1.1,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| label | string | 是 | `""` | 任一字符串；`text` 为别名 |
| enabled | boolean | 否 | `true` | 缺失回落 true |
| action | object | 否 | — | `{event:{name,context?}}` 或 `{functionCall:{call,args?}}` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 含合法 `label` | 呈现按钮文案 | AC-1.1 |
| 2 | 含 `action` | 点击分发 action | AC-3.2 |
| 3 | 样式非法 | 告警 + 回落默认 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 1.0.0。
- **API 版本号策略:** schema 由 `extended_catalog.json` 声明；`label`/`text` 别名、`action` 属性为扩展协议独有（标准 A2UI v0.9 Button 无 `action`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| action > onClick | `action` 优先，onClick 仅在无有效 action 时触发 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 原生路径 | Button 走 C++ 原生组件（`ExtendedComponentFactory.cpp:108`） | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| 告警不中断 | 非法样式告警回落，不拒绝消息 | AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，统一告警回落 | C++ UT | `ExtendedButtonComponent.cpp:236-258` |
| 性能 | 点击分发直连 action/onClick 无中间层 | C++ UT | `ExtendedButtonComponent.cpp:508-529` |

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
| 大字体 | 是 | `fontScaleMode`/`minFontScale`/`maxFontScale` | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| 深色模式 | 是 | 默认文字/背景色按主题切换 | AC-4.6 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | `action` 为扩展协议独有属性 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Button 扩展交互组件
  作为 生成式 UI 宿主开发者
  我想要 按钮支持文本、启停、action 优先点击
  以便 正确呈现并分发交互

  Scenario: 合法点击分发 action
    Given Button 描述符含 action={"functionCall":{"call":"submit"}}
    When 用户点击按钮
    Then 经 DispatchActionInfo("action") 分发，不触达 onClick

  Scenario: 无 action 回退 onClick
    Given Button 描述符含 onClick=[{...}] 且无 action
    When 用户点击按钮
    Then 经 DispatchEvent("onClick") 分发

  Scenario Outline: 非法样式告警回落
    Given Button 描述符 styles=<style>
    When 应用组件描述符
    Then 上报 schema 告警并回落默认 <fallback>

    Examples:
      | style | fallback |
      | {"fontSize":-1} | fontSize=16.0F |
      | {"fontWeight":"heavy"} | fontWeight=W500 |
      | {"fontColor":"not-a-color"} | 主题默认文字色 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 Button 组件契约；取值函数归 07-04-16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedButtonComponent label text 别名 enabled action 优先级 onClick ActionParser"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedButtonComponent ValidateStylesSchema ReportExtendedSchemaWarning 默认值回落 主题切换"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/components/extended/ExtendedButtonComponent.cpp`、`reference/extended-components/button.md`