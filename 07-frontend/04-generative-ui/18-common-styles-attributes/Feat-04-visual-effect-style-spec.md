# 特性规格

> Func-07-04-18-Feat-04 视效样式：固化扩展协议通用样式中 `shadow`（阴影）的预设名/数字/对象三形态解析、子字段降级，以及 native-only 未文档化样式 `opacity`（不透明度）的解析与应用。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 视效样式 |
| 特性编号 | Func-07-04-18-Feat-04 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议 1.0.0（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 承继 Feat-01~03 基线，追加视效样式 `shadow` 与 `opacity` |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/18-common-styles-attributes/design.md` | Baselined |
| 契约（JSON Schema） | `specification/extended/1.0.0/extended_catalog.json` | — |
| 底层视效解析（C++） | `genui/src/main/cpp/styles/StyleApplyUtilsEffects.cpp` | — |
| 样式应用（C++） | `genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp` | — |
| 样式解析（C++） | `genui/src/main/cpp/styles/StyleParser.cpp` | — |
| ETS 回退应用（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedCommonStyleModifier.ets` | — |
| 文档参考（Docs） | `reference/extended-components/overview.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 阴影（shadow）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.shadow` 指定阴影效果,
**以便** 用预设名、数字或参数对象控制阴影。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `shadow` 为字符串预设名（如 `"outerDefaultMD"`） THEN `ParseShadowFromStringValue` 经 `SHADOW_STYLE_MAP` 映射为 STYLE 阴影，`SetNodeShadow` 落库（`StyleApplyUtilsEffects.cpp:72-78,132-152`、`ExtendedStyleResolver.cpp:2166-2169`） | 正常 |
| AC-1.2 | WHEN `shadow` 为 0~5 整数（数字或 `"0"`~`"5"` 数字串） THEN 映射对应 `A2UIShadowStyle` 预设（`StyleApplyUtilsEffects.cpp:90-103,115-152`） | 正常 |
| AC-1.3 | WHEN `shadow` 为对象且含 `radius`（必填）与可选 `offsetX/offsetY/color/fill/type` THEN `ParseShadowFromObjectValue` 解析为 CUSTOM 阴影，`SetNodeCustomShadow` 落库（`StyleApplyUtilsEffects.cpp:211-230`、`ExtendedStyleResolver.cpp:2172-2178`） | 正常 |
| AC-1.4 | WHEN `shadow` 对象 `radius` 为负/非法 THEN 仅 radius 按 0 降级；`offsetX/offsetY` 非法按 0；`type` 非法回退 `color`；`fill` 非 bool 回 false；`color` 非法用默认色（`StyleApplyUtilsEffects.cpp:154-209`、`overview.md:965`） | 边界 |
| AC-1.5 | WHEN `shadow` 为非法预设名（含大小写错误如 `"outerDefaultMD"`→正确、`"OuterDefaultMD"`→错误）、非 0~5 整数或对象无任何受支持字段 THEN 整体 reset 为无阴影并上报告警（`StyleApplyUtilsEffects.cpp:455-468`、`ExtendedStyleResolver.cpp:2135-2143`） | 异常 |

### US-2: 不透明度（opacity）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.opacity` 指定组件不透明度,
**以便** 控制组件整体透明度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `opacity` 为合法 number 或数字串 THEN `ApplyOpacityStyle` 经 `ParseNumber` 解析并 `SetNodeOpacity` 落库（`ExtendedStyleResolver.cpp:1240-1245`、`StyleApplyUtils.cpp:62-75`） | 正常 |
| AC-2.2 | WHEN `opacity` 非法 THEN 打 `LOG_WARN`（`style=opacity ignored`）且不应用，不强制 reset（`ExtendedStyleResolver.cpp:1246-1250`） | 异常 |
| AC-2.3 | WHEN `opacity` 未在 `extended_catalog.json`/`ExtendedCommonStyleModifier`/`overview.md` 声明 THEN 该样式仅 native C++ 路径识别（`StyleParser.cpp:41`、`StylePropertyName::OPACITY` `StyleTypes.h:61`），属未文档化样式（见 RISK-2） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-4 | C++ UT：`ParseShadow`/`ApplyShadow` | `StyleApplyUtilsEffects.cpp:455-468`、`ExtendedStyleResolver.cpp:2132-2179` |
| AC-2.1,AC-2.2,AC-2.3 | R-3 | T-4 | C++ UT：`ApplyOpacityStyle` | `ExtendedStyleResolver.cpp:1240-1251`、`StyleParser.cpp:41` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | shadow 为预设名/0~5 整数/含 radius 对象 | STYLE 或 CUSTOM 阴影落库 | radius 必填；预设名大小写敏感 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 边界 | shadow 子字段非法 | 仅该子字段按默认，其余字段仍生效 | radius 负数→0，type 非法→color | AC-1.4,AC-1.5 |
| R-3 | 异常 | opacity 非法或未声明 | 忽略 + LOG_WARN，不 reset | native-only，未进契约/ETS | AC-2.1,AC-2.2,AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 shadow | C++ UT | 三形态解析与子字段降级 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 opacity | C++ UT | number 解析与非法忽略 |

## API 变更分析

> 存量补录，无新增/变更 Public/C/System API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `styles.shadow` | 既有 | 阴影 | 预设名/数字/对象 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| `styles.opacity` | 既有（native-only） | 不透明度 | 未文档化，仅 native 路径 | AC-2.1,AC-2.2,AC-2.3 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json:691-741`（shadow；opacity 不在契约内）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`StyleApplyUtils::ParseShadow(value, shadow)`（`StyleApplyUtilsEffects.cpp:455`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseShadow(const JsonValue& value, StyleShadow& shadow)` |
| 返回值 | `bool` — 是否解析出 `shadow.valid=true` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

**`ExtendedStyleResolver::ApplyShadow(value, applier, issues, commonTheme)`（`ExtendedStyleResolver.cpp:2132`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static void ApplyShadow(const JsonValue&, ArkUINodeApiAdapter&, std::vector<DescriptorValidationIssue>&, std::shared_ptr<ExtendedCommonTheme>)` |
| 返回值 | `void` — 非法值经 `issues` 上报并 reset |
| 开放范围 | 内部 |
| 错误码 | `SCHEMA_ERROR_CODE_INVALID_VALUE` / `SCHEMA_ERROR_CODE_TYPE_MISMATCH` |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| shadow | string \| number \| object | 否 | 无阴影 | 预设名/0~5 整数/对象（radius 必填） |
| shadow.radius | number | 是（对象形态） | 0 | `[0,+∞)` |
| shadow.type | string \| number | 否 | color | `color`/`blur`（大小写敏感） |
| opacity | number \| string | 否 | — | number 或数字串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | shadow="outerDefaultMD" | STYLE 阴影落库 | AC-1.1 |
| 2 | shadow={radius:10,type:"blur"} | CUSTOM 阴影落库 | AC-1.3 |
| 3 | shadow={radius:-1} | radius 降级 0 | AC-1.4 |
| 4 | shadow="OuterDefaultMD" | reset 无阴影 | AC-1.5 |
| 5 | opacity=0.5 | SetNodeOpacity(0.5) | AC-2.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 契约随 `extended_catalog.json` 版本演进；`opacity` 为 native-only 未文档化样式（见 RISK-2）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 预设名大小写敏感 | 阴影预设名/type 均大小写敏感 | AC-1.5,AC-1.4 |
| 子字段独立降级 | shadow 对象子字段单独按默认，整体不 reset | AC-1.4 |
| opacity 未契约化 | opacity 仅 C++ 路径，ETS/契约不识别 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 shadow 不中断渲染，统一 reset + 告警 | C++ UT | `ExtendedStyleResolver.cpp:2135-2143` |
| 性能 | 预设名映射 O(1) | C++ UT | `StyleApplyUtilsEffects.cpp:72-78` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 视效语义设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 是 | `shadow` 未显式 color 时跟随主题 `ExtendedCommonTheme::GetShadowColor()` | AC-1.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 契约随扩展协议版本演进 | 概述「目标版本」 |
| 生态兼容 | 是 | CommonStyles 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 视效样式
  作为 生成式 UI 宿主开发者
  我想要 通过 styles 控制阴影与不透明度
  以便 实现立体层次与透明效果

  Scenario: 阴影子字段独立降级
    Given styles 为 {"shadow": {"radius": -1, "offsetX": 2, "color": "#000000"}}
    When 渲染引擎解析样式
    Then radius 降级 0，offsetX/color 仍生效

  Scenario Outline: 非法阴影降级
    Given styles 为 <styles>
    When 渲染引擎解析样式
    Then 阴影重置为无阴影并上报 schema warning

    Examples:
      | styles |
      | {"shadow": "OuterDefaultMD"} |
      | {"shadow": 99} |
      | {"shadow": {}} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 做视效 shadow/opacity；背景颜色归 Feat-03，显示裁切归 Feat-05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseShadow SHADOW_STYLE_MAP ParseShadowFromObjectValue 子字段降级"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedStyleResolver ApplyShadow ApplyOpacityStyle opacity native-only"
  - repo: "GenerativeUI/A2UIRender"
    query: "StylePropertyName OPACITY StyleParser propertyNameMap opacity"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/styles/StyleApplyUtilsEffects.cpp`、`genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp`、`reference/extended-components/overview.md`