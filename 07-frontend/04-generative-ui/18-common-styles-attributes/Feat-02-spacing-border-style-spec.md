# 特性规格

> Func-07-04-18-Feat-02 间距与边框样式：固化扩展协议通用样式中 `padding`/`margin`（间距）与 `borderWidth`/`borderColor`/`borderRadius`（边框）五项属性的边角解析、四边语义、简写展开与非法值降级。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 间距与边框样式 |
| 特性编号 | Func-07-04-18-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议 1.0.0（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 承继 Feat-01 基线，追加间距与边框五项通用样式 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/18-common-styles-attributes/design.md` | Baselined |
| 契约（JSON Schema） | `specification/extended/1.0.0/extended_catalog.json` | — |
| 底层边距解析（C++） | `genui/src/main/cpp/styles/StyleApplyUtilsLayout.cpp` | — |
| 样式应用（C++） | `genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp` | — |
| ETS 回退应用（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedCommonStyleModifier.ets` | — |
| 文档参考（Docs） | `reference/extended-components/overview.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 间距（padding/margin）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.padding`/`styles.margin` 指定内外间距,
**以便** 用统一值、四边或简写字符串控制间距。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `padding` 为数字（如 `10`） THEN `ParseEdge` 解析为四边统一 VP（`ApplyEdgeValue`），`ApplyPaddingStyles` 落库（`StyleApplyUtilsLayout.cpp:155-170`、`StyleApplyUtilsInternal.h:130-136`） | 正常 |
| AC-1.2 | WHEN `padding` 为对象 `{top,right,bottom,left}` 或 `{all,vertical,horizontal}` THEN 按边/按组展开四边（`StyleApplyUtilsLayout.cpp:189-234`） | 正常 |
| AC-1.3 | WHEN `padding` 为简写字符串（1~4 段，如 `"1 2 3 4"`） THEN `ParseEdgeShorthand` 按 CSS 顺序展开（`StyleApplyUtilsLayout.cpp:236-278`） | 正常 |
| AC-1.4 | WHEN `padding`/`margin` 对象缺某边或某边非法 THEN 仅该边按 0，其余合法边仍生效（`ExtendedStyleResolver.cpp:1043-1159`、`overview.md:955`） | 边界 |
| AC-1.5 | WHEN `padding`/`margin` 包含百分比与绝对边混用（非零边） THEN `DispatchMixedEdgeStyle` 经跨语言桥分发 ETS 按边应用，每边保留原单位（`ExtendedStyleResolver.cpp:1089-1096`） | 正常 |
| AC-1.6 | WHEN `padding`/`margin` 裸值为负数、非有限或坏段 THEN 整体重置并上报告警（`ExtendedStyleResolver.cpp:1069-1075,1127-1133`） | 异常 |

### US-2: 边框宽度（borderWidth）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.borderWidth` 指定边框宽度,
**以便** 用 vp/百分比控制边框粗细。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `borderWidth` 为数字或 vp 字符串（如 `"2vp"`） THEN `ApplyBorderWidthStyle` 落库 `SetNodeBorderWidth`（`ExtendedStyleResolver.cpp:1215-1222,1198-1199`） | 正常 |
| AC-2.2 | WHEN `borderWidth` 为百分比字符串（如 `"10%"`） THEN 走 `SetBorderWidthPercent(number/100)`（`ExtendedStyleResolver.cpp:1193-1196`） | 正常 |
| AC-2.3 | WHEN `borderWidth` 单位非 vp/% 或转换失败 THEN `ResetInvalidBorderWidth` 重置默认并上报（`ExtendedStyleResolver.cpp:1161-1200`） | 异常 |
| AC-2.4 | WHEN `borderWidth` 显式 `null` 或类型不符 THEN 上报 `TYPE_MISMATCH` 并 reset（`ExtendedStyleResolver.cpp:1224-1236`） | 异常 |

### US-3: 边框颜色（borderColor）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.borderColor` 指定边框颜色,
**以便** 用 hex 颜色控制边框。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `borderColor` 为 `#RRGGBB`/`#AARRGGBB` THEN `ParseColor` 成功，`SetNodeBorderColor` 落库（`StyleApplyUtils.cpp:40-60`、`ExtendedStyleResolver.cpp:984-986`） | 正常 |
| AC-3.2 | WHEN `borderColor` 为 `#RGB`/命名色/`rgb()`/缺 `#` THEN 解析失败，`Reset` 为默认黑并上报告警（`ExtendedStyleResolver.cpp:987-1001`、`overview.md:958`） | 异常 |

### US-4: 圆角（borderRadius）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.borderRadius` 指定圆角,
**以便** 用统一值或逐角控制圆角。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `borderRadius` 为数字或字符串 THEN `ParseRadius` 解析为四角统一（`ApplyRadiusValue`），`ApplyRadius` 落库（`StyleApplyUtilsLayout.cpp:172-187`、`ExtendedStyleResolver.cpp:2093-2130`） | 正常 |
| AC-4.2 | WHEN `borderRadius` 为对象 `{topLeft,topRight,bottomLeft,bottomRight}` 或 `{all}` THEN 按角展开（`StyleApplyUtilsLayout.cpp:280-312`） | 正常 |
| AC-4.3 | WHEN `borderRadius` 四角百分比与绝对混用 THEN `DispatchMixedRadius` 分发 ETS（Button 例外），否则 `ResetUnsupportedMixedRadius`（`ExtendedStyleResolver.cpp:2059-2090`） | 边界 |
| AC-4.4 | WHEN `borderRadius` 缺某角或某角非法 THEN 仅该角按 0，其余合法角仍生效（`ExtendedStyleResolver.cpp:2014-2056`、`overview.md:956`） | 边界 |
| AC-4.5 | WHEN `borderRadius` 全部非法或转换失败 THEN 整体 reset 并上报告警（`ExtendedStyleResolver.cpp:2099-2106`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2 | T-2 | C++ UT：`ParseEdge`/`ApplyPaddingStyles`/`ApplyMarginStyles` | `StyleApplyUtilsLayout.cpp:155-278`、`ExtendedStyleResolver.cpp:1043-1159` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-3 | T-2 | C++ UT：`ApplyBorderWidthStyle` | `ExtendedStyleResolver.cpp:1161-1238` |
| AC-3.1,AC-3.2 | R-4 | T-2 | C++ UT：`ParseColor` | `StyleApplyUtils.cpp:40-60` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-5 | T-2 | C++ UT：`ParseRadius`/`ApplyRadius` | `StyleApplyUtilsLayout.cpp:172-325`、`ExtendedStyleResolver.cpp:2093-2130` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 间距为数字/对象/1~4 段简写 | 四边统一或按边/按组展开 | 简写按 top/right/bottom/left 顺序 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 边界 | 间距对象缺边/某边非法/百分比混用 | 缺边按 0；混用经跨语言桥按边分发 | 已设置边全部非法才整体重置 | AC-1.4,AC-1.5,AC-1.6 |
| R-3 | 异常 | borderWidth 单位非 vp/% 或类型不符 | reset 默认并上报告警 | 仅 vp/% 单位 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-4 | 异常 | borderColor 非 6/8 hex | reset 黑色并上报告警 | `#RGB`/命名色/rgb() 拒绝 | AC-3.1,AC-3.2 |
| R-5 | 边界 | borderRadius 圆角缺角/混用/全非法 | 缺角按 0；混用分发 ETS；全非法整体 reset | Button 混用不走 ETS 分发 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 间距 | C++ UT | 四边/简写/混用/缺边降级 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 borderWidth | C++ UT | vp/% 与非法单位 |
| VM-3 | AC-3.1,AC-3.2 borderColor | C++ UT | hex 校验 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 borderRadius | C++ UT | 逐角/混用/全非法 |

## API 变更分析

> 存量补录，无新增/变更 Public/C/System API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `styles.padding` | 既有 | 内边距 | number/object/简写 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| `styles.margin` | 既有 | 外边距 | number/object/简写 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| `styles.borderWidth` | 既有 | 边框宽度 | vp/% | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| `styles.borderColor` | 既有 | 边框颜色 | hex | AC-3.1,AC-3.2 |
| `styles.borderRadius` | 既有 | 圆角 | number/object | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json:418-616`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`StyleApplyUtils::ParseEdge(value, edge)`（`StyleApplyUtilsLayout.cpp:155`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseEdge(const JsonValue& value, StyleEdge& edge)` |
| 返回值 | `bool` — 解析成功与否 |
| 开放范围 | 内部 |
| 错误码 | N/A（返回 false，调用方 reset） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |

**`ExtendedStyleResolver::ApplyPaddingStyles/ApplyMarginStyles`（`ExtendedStyleResolver.cpp:1043/1102`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static void ApplyPaddingStyles(...); static void ApplyMarginStyles(...)` |
| 返回值 | `void` — 非法值经 `issues` 上报并 reset |
| 开放范围 | 内部 |
| 错误码 | `SCHEMA_ERROR_CODE_TYPE_MISMATCH` / `SCHEMA_ERROR_CODE_INVALID_VALUE` |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |

**`ExtendedStyleResolver::ApplyRadius(value, applier, dispatchContext, issues)`（`ExtendedStyleResolver.cpp:2093`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static void ApplyRadius(const JsonValue&, ArkUINodeApiAdapter&, std::optional<ConstraintDispatchContext>, std::vector<DescriptorValidationIssue>&)` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | `SCHEMA_ERROR_CODE_TYPE_MISMATCH` / `SCHEMA_ERROR_CODE_INVALID_VALUE` |
| 关联 AC | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| padding/margin | number \| string \| object | 否 | 0 | number∈[0,+∞)；对象边 `top/right/bottom/left` |
| borderWidth | number \| string | 否 | 0 | 仅 vp/% 单位 |
| borderColor | string | 否 | 黑 #000000 | `#RRGGBB`/`#AARRGGBB` |
| borderRadius | number \| string \| object | 否 | 0 | 角 `topLeft/topRight/bottomLeft/bottomRight` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | padding=10 | 四边 10vp | AC-1.1 |
| 2 | padding={top:8,bottom:8} | 上下 8，左右 0 | AC-1.2,AC-1.4 |
| 3 | margin="1 2 3 4" | 上1/右2/下3/左4 | AC-1.3 |
| 4 | borderWidth="2vp" | 2vp 边框 | AC-2.1 |
| 5 | borderColor="#FF0000" | 红色边框（#FFFF0000） | AC-3.1 |
| 6 | borderRadius 全非法 | 整体 reset | AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 契约随 `extended_catalog.json` 版本演进；间距/圆角对象 `all`/`vertical`/`horizontal` 为扩展别名。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 边角四语义 | 缺边按 0，单边非法仅该边降级 | AC-1.4,AC-4.4 |
| 混用单位分发 | 百分比与绝对混用走跨语言桥，非 zero 边保留原单位 | AC-1.5,AC-4.3 |
| 颜色单一形态 | 边框/背景色仅 6/8 hex | AC-3.1,AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法间距/边框不中断渲染，统一 reset + 告警 | C++ UT | `ExtendedStyleResolver.cpp:1161-1200` |
| 性能 | 边角解析为常数次字面比较 | C++ UT | `StyleApplyUtilsInternal.h` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 间距/边框语义设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 默认色接受显式 hex；主题默认另域 | — |
| 多窗口/分屏 | 是 | 百分比边距随父容器内容区重算 | AC-2.2 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 契约随扩展协议版本演进 | 概述「目标版本」 |
| 生态兼容 | 是 | CommonStyles 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 间距与边框样式
  作为 生成式 UI 宿主开发者
  我想要 通过 styles 控制内外间距与边框
  以便 实现视觉留白与描边

  Scenario: 简写四边展开
    Given styles 为 {"margin": "1 2 3 4"}
    When 渲染引擎解析样式
    Then 上1/右2/下3/左4 按 CSS 顺序应用

  Scenario Outline: 非法间距/边框降级
    Given styles 为 <styles>
    When 渲染引擎解析样式
    Then 指定属性重置为默认并上报 schema warning

    Examples:
      | styles |
      | {"padding": -5} |
      | {"borderWidth": "2px"} |
      | {"borderColor": "red"} |
      | {"borderRadius": {"topLeft": "abc"}} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做间距边框；尺寸布局归 Feat-01，背景颜色归 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseEdge ParseEdgeShorthand ParseRadius 四边语义 简写展开"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedStyleResolver ApplyPaddingStyles ApplyMarginStyles ApplyBorderWidthStyle ApplyRadius 混用分发"
  - repo: "GenerativeUI/A2UIRender"
    query: "borderColor ParseColor hex NormalizeHexColor AARRGGBB"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/styles/StyleApplyUtilsLayout.cpp`、`genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp`、`reference/extended-components/overview.md`