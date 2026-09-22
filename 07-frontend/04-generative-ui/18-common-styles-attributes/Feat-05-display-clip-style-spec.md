# 特性规格

> Func-07-04-18-Feat-05 显示与裁切：固化扩展协议通用样式中 `visibility`（可见性）与 `clip`（裁切）两项属性的解析、应用与非法值降级。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 显示与裁切 |
| 特性编号 | Func-07-04-18-Feat-05 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议 1.0.0（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 承继 Feat-01~04 基线，追加显示与裁切两项通用样式 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/18-common-styles-attributes/design.md` | Baselined |
| 契约（JSON Schema） | `specification/extended/1.0.0/extended_catalog.json` | — |
| 底层可见性解析（C++） | `genui/src/main/cpp/styles/StyleApplyUtilsText.cpp` | — |
| 底层裁切解析（C++） | `genui/src/main/cpp/styles/StyleApplyUtilsEffects.cpp` | — |
| 样式应用（C++） | `genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp` | — |
| ETS 回退应用（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedCommonStyleModifier.ets` | — |
| 文档参考（Docs） | `reference/extended-components/overview.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 可见性（visibility）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.visibility` 控制组件可见性,
**以便** 在 visible/hidden/none 三态间切换。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `visibility` 为 `"visible"` THEN `ParseVisibility` 映射 `A2UIVisibility::VISIBLE`，`SetNodeVisibility` 落库（`StyleApplyUtilsText.cpp:229-239`、`ExtendedStyleResolver.cpp:1258-1259`） | 正常 |
| AC-1.2 | WHEN `visibility` 为 `"hidden"`/`"none"` THEN 分别映射 `HIDDEN`/`NONE`（`StyleApplyUtilsText.cpp:235-237`、`A2UIArkUITypes.h:158-162`） | 正常 |
| AC-1.3 | WHEN `visibility` 为非 string、未知值或大小写错误（如 `"Visible"`） THEN 解析失败，`Reset` 为默认 `visible` 并上报告警（`ExtendedStyleResolver.cpp:1260-1272`、`overview.md:966`） | 异常 |

### US-2: 裁切（clip）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.clip` 控制子内容是否裁剪到组件边界,
**以便** 配合 borderRadius 实现圆角裁切。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `clip` 为 `true`/`false` THEN `ParseClip` 成功，`SetNodeClip` 落库（`StyleApplyUtilsEffects.cpp:557-564`、`ExtendedStyleResolver.cpp:1352-1357`） | 正常 |
| AC-2.2 | WHEN `clip` 为非 bool（数字/字符串/对象，如 `1`/`"true"`） THEN 解析失败，`Reset` 为默认 `false` 并上报 `TYPE_MISMATCH`，**不做强转**（`ExtendedStyleResolver.cpp:1361-1374`、`overview.md:967`） | 异常 |
| AC-2.3 | WHEN `clip` 未显式设置 THEN 保持默认 `false`（不裁剪），不产生告警（`extended_catalog.json:557`、`overview.md:943`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-5 | C++ UT：`ParseVisibility`/`ApplyVisibilityStyle` | `StyleApplyUtilsText.cpp:229-239`、`ExtendedStyleResolver.cpp:1253-1273` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-5 | C++ UT：`ParseClip`/`ApplyClipStyle` | `StyleApplyUtilsEffects.cpp:557-564`、`ExtendedStyleResolver.cpp:1344-1375` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 异常 | visibility 三态合法/非法 | 合法映射；非法 reset visible + 告警 | 大小写敏感 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 异常 | clip 布尔/非布尔 | 布尔落库；非布尔 reset false，无强转 | 默认 false | AC-2.1,AC-2.2,AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 visibility | C++ UT | 三态映射与非法 reset |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 clip | C++ UT | 布尔仅接受，无强转 |

## API 变更分析

> 存量补录，无新增/变更 Public/C/System API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `styles.visibility` | 既有 | 可见性 | visible/hidden/none | AC-1.1,AC-1.2,AC-1.3 |
| `styles.clip` | 既有 | 裁切 | boolean | AC-2.1,AC-2.2,AC-2.3 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json:536-569`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`StyleApplyUtils::ParseVisibility(value, visibility)`（`StyleApplyUtilsText.cpp:229`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseVisibility(const JsonValue& value, A2UIVisibility& visibility)` |
| 返回值 | `bool` — 是否映射成功 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`StyleApplyUtils::ParseClip(value, clip)`（`StyleApplyUtilsEffects.cpp:557`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseClip(const JsonValue& value, bool& clip)` |
| 返回值 | `bool` — 是否 boolean 类型 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| visibility | string | 否 | visible | 仅 visible/hidden/none（大小写敏感） |
| clip | boolean | 否 | false | 仅 boolean，无强转 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | visibility="hidden" | 隐藏但占位 | AC-1.2 |
| 2 | visibility="Visible" | reset visible + 告警 | AC-1.3 |
| 3 | clip=true | 裁切子内容 | AC-2.1 |
| 4 | clip="true" | reset false + TYPE_MISMATCH | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 契约随 `extended_catalog.json` 版本演进。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 可见性三态语义 | visible/hidden/none 分别对应显示/隐藏占位/隐藏不占位 | AC-1.1,AC-1.2,AC-1.3 |
| clip 无强转 | 数字 `1`/字符串 `"true"` 均不识别为布尔 | AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 visibility/clip 不中断渲染，统一 reset + 告警 | C++ UT | `ExtendedStyleResolver.cpp:1260-1272,1361-1374` |
| 性能 | 枚举/布尔解析 O(1) | C++ UT | `StyleApplyUtilsText.cpp:229-239` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 显示/裁切语义设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `visibility:none` 语义下组件不参与无障碍树；hidden 保留布局 | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 契约随扩展协议版本演进 | 概述「目标版本」 |
| 生态兼容 | 是 | CommonStyles 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 显示与裁切
  作为 生成式 UI 宿主开发者
  我想要 通过 styles 控制组件可见性与内容裁切
  以便 实现显隐与圆角裁切

  Scenario: clip 无布尔强转
    Given styles 为 {"clip": "true"}
    When 渲染引擎解析样式
    Then clip 重置为 false 并上报 TYPE_MISMATCH

  Scenario Outline: 非法可见性降级
    Given styles 为 <styles>
    When 渲染引擎解析样式
    Then visibility 重置为 visible 并上报 schema warning

    Examples:
      | styles |
      | {"visibility": "Visible"} |
      | {"visibility": "collapse"} |
      | {"visibility": 0} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-05 做显示与裁切；视效归 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseVisibility A2UIVisibility visible hidden none"
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseClip ExtendedStyleResolver ApplyClipStyle boolean"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedStyleResolver ApplyVisibilityStyle reset 大小写敏感"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/styles/StyleApplyUtilsText.cpp`、`genui/src/main/cpp/styles/StyleApplyUtilsEffects.cpp`、`genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp`、`reference/extended-components/overview.md`