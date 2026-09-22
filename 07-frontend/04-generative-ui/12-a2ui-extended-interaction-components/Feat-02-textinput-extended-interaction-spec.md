# 特性规格

> Func-07-04-12-Feat-02 TextInput 扩展交互组件：固化 A2UI 扩展协议交互组件 TextInput 的属性契约（`text`/`placeholder`/`enabled`/`maxLength`/`type`）、输入类型枚举、样式契约（占位色/取消按钮/光标色/选中高亮/下划线/字号/字重/对齐/自适应/换行）、文本变更事件（`onChange {value}`）与绑定回写语义。基准实现：`@arkui-genius/genui`（A2UIRender），原生 C++ 路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 扩展交互组件 |
| 特性编号 | Func-07-04-12-Feat-02 |
| 优先级 | P0 |
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
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（`components.TextInput`） | — |
| 原生组件（C++） | `genui/src/main/cpp/components/extended/ExtendedTextInputComponent.h/.cpp` | — |
| 文档参考 | `reference/extended-components/text-input.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 输入类型枚举契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `type` 控制键盘与校验行为，
**以便** 匹配数字/密码/邮箱等输入场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `type` 缺失 THEN 回落 `normal`（`CreateTypePropertyDeclaration.fallbackString="normal"`，`ExtendedTextInputComponent.cpp:496-509`） | 边界 |
| AC-1.2 | WHEN `type` 为 `number`/`phoneNumber`/`email`/`password`/`numberPassword`/`userName`/`newPassword`/`numberDecimal` THEN `ParseTextInputTypeToken` 映射到对应 `A2UITextInputType`（`ExtendedTextInputComponent.cpp:187-203`） | 正常 |
| AC-1.3 | WHEN `type` 为未识别 token THEN 回落 `A2UITextInputType::NORMAL`（`ExtendedTextInputComponent.cpp:201-202`） | 边界 |
| AC-1.4 | WHEN `type` 为 `screenLockPassword`/`oneTimeCode` THEN 实现映射对应枚举（`ExtendedTextInputComponent.cpp:195,199`），但 schema 未声明该值 | 异常 |
| AC-1.5 | WHEN `type` 为 `url` THEN 实现未识别回落 `NORMAL`，而 schema 声明其合法 | 异常 |

### US-2: 文本与占位属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `text`/`placeholder` 设置内容与提示，
**以便** 预填文本并显示占位提示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 描述符含 `text` 字符串 THEN `SetText` 写入输入框内容（`ExtendedTextInputComponent.cpp:408-409`） | 正常 |
| AC-2.2 | WHEN `text` 缺失 THEN `ResetTextPropertyIfMissing` 复位文本（`ExtendedTextInputComponent.cpp:410-411`） | 边界 |
| AC-2.3 | WHEN `placeholder` 字符串 THEN `SetPlaceholder` 写入占位提示（`CreatePlaceholderPropertyDeclaration`，`ExtendedTextInputComponent.cpp:461-469`） | 正常 |
| AC-2.4 | WHEN `text` 存在 path 绑定 THEN 变更时 `SyncTextToBoundDataModel` 回写数据模型（`ExtendedTextInputComponent.h:272-273`） | 正常 |

### US-3: maxLength 边界契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `maxLength` 限制输入长度，
**以便** 非法值回落安全上限。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `maxLength` 为 `[0, INT32_MAX]` 内数值 THEN `NormalizeMaxLength` 夹取为 int32（`ExtendedTextInputComponent.cpp:340-347`） | 正常 |
| AC-3.2 | WHEN `maxLength` 为负数或非有限值 THEN 回落 `DEFAULT_MAX_LENGTH`（int32 max）并告警（`ExtendedTextInputComponent.cpp:342-343,418-420`） | 边界 |
| AC-3.3 | WHEN `maxLength` 缺失 THEN 回落 `DEFAULT_MAX_LENGTH`（`CreateMaxLengthPropertyDeclaration.fallbackNumber`，`ExtendedTextInputComponent.cpp:481-494`） | 边界 |

### US-4: 交互状态与事件契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `enabled` 控制输入框交互并监听文本变化，
**以便** 禁用输入或响应输入变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `enabled=false` THEN `SetEnabled` 使输入框不可交互（`ExtendedTextInputComponent.cpp:471-479`） | 正常 |
| AC-4.2 | WHEN 用户输入导致文本变化 THEN `HandleInputValueChange` 更新内部态并派发 `onChange`（`ExtendedTextInputComponent.cpp:1425`） | 正常 |
| AC-4.3 | WHEN `onChange` 事件已注册 THEN `RegisterChangeEvent`/`UpdateChangeEventRegistration` 维护监听（`ExtendedTextInputComponent.h:230-232`） | 正常 |

### US-5: 样式契约与告警回落

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `styles` 控制占位色/取消按钮/下划线/字体等，
**以便** 非法样式告警并回落默认。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `styles.fontColor`/`placeholderColor`/`caretColor`/`selectedBackgroundColor` 非法 THEN `ValidateColorStyle` 告警回落（`ExtendedTextInputComponent.cpp:561-582`） | 异常 |
| AC-5.2 | WHEN `styles.showUnderline=true` 且 `type=normal` THEN 显示下划线；`showUnderline` 仅 normal 类型生效（schema `showUnderline` 描述） | 正常 |
| AC-5.3 | WHEN `styles.cancelButton.style` 为 `constant`/`invisible`/`input` 之一 THEN `ParseCancelButtonStyle` 映射对应枚举，否则回落 `INPUT`（`ExtendedTextInputComponent.cpp:230-266`） | 边界 |
| AC-5.4 | WHEN `styles.wordBreak` 为 `normal`/`breakAll`/`breakWord`/`hyphenation` THEN `ParseWordBreak` 映射，否则回落（`ExtendedTextInputComponent.cpp:205-228`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-2 | C++ UT（`GetInputTypeForTest`） | `ExtendedTextInputComponent.cpp:187-203,496-509` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-3,R-4 | T-2 | C++ UT | `ExtendedTextInputComponent.cpp:406-429` |
| AC-3.1,AC-3.2,AC-3.3 | R-5 | T-2 | C++ UT | `ExtendedTextInputComponent.cpp:340-347,481-494` |
| AC-4.1,AC-4.2,AC-4.3 | R-6 | T-2 | C++ UT + ohosTest | `ExtendedTextInputComponent.cpp:1425` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-7 | T-2 | C++ UT + 告警 | `ExtendedTextInputComponent.cpp:561-582` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `type` 为受支持 token | 映射 `A2UITextInputType` | 10 类受支持 token | AC-1.2 |
| R-2 | 边界 | `type` 未识别/缺失 | 回落 `NORMAL` | schema 含 `url` 但实现未识别 | AC-1.1,AC-1.3,AC-1.5 |
| R-3 | 行为 | `text`/`placeholder` 字符串 | 写入输入框内容/占位 | `text` 缺失复位 | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 行为 | `text` 有 path 绑定 | 变更回写数据模型 | 仅绑定存在时 | AC-2.4 |
| R-5 | 边界 | `maxLength` 负/非有限/缺失 | 回落 `DEFAULT_MAX_LENGTH` | 夹取 `[0,INT32_MAX]` | AC-3.1,AC-3.2,AC-3.3 |
| R-6 | 行为 | `enabled`/文本变化 | 交互态切换/派发 onChange | — | AC-4.1,AC-4.2,AC-4.3 |
| R-7 | 异常 | 样式非法 | 告警回落默认 | 不中断渲染 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 type 枚举 | C++ UT | 10 类 token + 未识别回落 + 分歧 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 text/placeholder | C++ UT | 预填/复位/绑定回写 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 maxLength | C++ UT | 夹取 + 负值回落 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 事件 | C++ UT + ohosTest | onChange 派发 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 样式 | C++ UT + 告警 | 颜色/下划线/取消按钮/换行 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 扩展协议组件 `TextInput`（`extended_catalog.json`） | 既有 | 文本输入渲染 | 描述符契约，无迁移 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`TextInput` 组件描述符（`components.TextInput`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 组件描述符（JSON object），`GetType()=="TextInput"`（`ExtendedTextInputComponent.cpp:401-404`） |
| 返回值 | 原生 `TEXT_INPUT` 节点 |
| 开放范围 | 扩展协议组件契约（非 ArkTS/C-API） |
| 错误码 | N/A（非法属性/样式经 `ReportExtendedSchemaWarning` 上报告警） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-3.1,AC-3.2,AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| text | string | 否 | `""` | 任一字符串 |
| placeholder | string | 否 | `""` | 任一字符串 |
| enabled | boolean | 否 | `true` | 缺失回落 true |
| maxLength | number | 否 | int32 max | `[0, INT32_MAX]` |
| type | string | 是 | `"normal"` | schema 枚举 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `type` 缺失 | 回落 normal | AC-1.1 |
| 2 | `type=url` | 实现回落 normal（分歧） | AC-1.5 |
| 3 | `maxLength=-1` | 回落 int32 max + 告警 | AC-3.2 |
| 4 | 文本变化 | 派发 onChange + 回写绑定 | AC-2.4,AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 1.0.0。
- **API 版本号策略:** `type` 枚举 schema（含 `url`）与实现（含 `screenLockPassword`/`oneTimeCode`）不一致，详见风险表 RISK-2。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生路径 | TextInput 走 C++ 原生组件（`ExtendedComponentFactory.cpp:117`） | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| 绑定回写 | `text` 绑定在输入变化时回写 | AC-2.4 |
| 告警不中断 | 非法样式/属性告警回落 | AC-3.2,AC-5.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，告警回落 | C++ UT | `ExtendedTextInputComponent.cpp:536-582` |
| 性能 | maxLength 归一 O(1) 夹取 | C++ UT | `ExtendedTextInputComponent.cpp:340-347` |

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
| 大字体 | 是 | `maxFontSize`/`minFontSize`/`fontScaleMode` | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| 深色模式 | 是 | 默认 fontColor/caretColor 按主题 | AC-5.1 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | `type` 枚举 schema/实现分歧 | AC-1.4,AC-1.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextInput 扩展交互组件
  作为 生成式 UI 宿主开发者
  我想要 文本输入支持类型/长度限制/变化监听
  以便 匹配多种输入场景

  Scenario: 输入类型映射
    Given TextInput 描述符 type="password"
    When 应用组件描述符
    Then 映射为 A2UITextInputType::PASSWORD

  Scenario Outline: 未识别 type 回落
    Given TextInput 描述符 type=<token>
    When 应用组件描述符
    Then 回落 A2UITextInputType::NORMAL

    Examples:
      | token |
      | "url" |
      | "unknown" |

  Scenario: 文本变化回写绑定
    Given TextInput 描述符 text={"path":"/form/name"}
    When 用户输入新值 "Alice"
    Then 派发 onChange{value:"Alice"} 并回写 /form/name
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做 TextInput 组件契约；`getSelectValue` 等取值函数归 07-04-16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTextInputComponent type 枚举 ParseTextInputTypeToken maxLength NormalizeMaxLength onChange 绑定回写"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTextInputComponent ValidateStylesSchema cancelButton showUnderline wordBreak 告警回落"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/components/extended/ExtendedTextInputComponent.cpp`、`reference/extended-components/text-input.md`