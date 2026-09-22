# 特性规格

> Func-07-04-18-Feat-01 尺寸与布局样式：固化扩展协议通用样式中 `width`/`height`/`constraintSize`/`aspectRatio`/`flexShrink`/`layoutWeight` 六项尺寸与布局属性的解析、应用与非法值降级。基准实现：`@arkui-genius/genui`（A2UIRender），契约声明于 `extended_catalog.json` `CommonStyles`。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 尺寸与布局样式 |
| 特性编号 | Func-07-04-18-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议 1.0.0（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-18 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/18-common-styles-attributes/design.md` | Baselined |
| 契约（JSON Schema） | `specification/extended/1.0.0/extended_catalog.json` | — |
| 底层尺寸解析（C++） | `genui/src/main/cpp/styles/StyleApplyUtilsLayout.cpp` | — |
| 样式应用（C++） | `genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp` | — |
| ETS 回退应用（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedCommonStyleModifier.ets` | — |
| 文档参考（Docs） | `reference/extended-components/overview.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 尺寸（width/height）解析与应用

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.width`/`styles.height` 指定组件宽高,
**以便** 用 vp/百分比/关键字控制组件尺寸。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `width` 为数字（如 `200`） THEN `StyleApplyUtils::ParseDimension` 解析为 `VP` 单位、值 200，`ApplyDimension` 经 `ApplyAbsoluteDimension` 落库（`StyleApplyUtilsLayout.cpp:115-121`、`ExtendedStyleResolver.cpp:1941-1943`） | 正常 |
| AC-1.2 | WHEN `width` 为带 vp 后缀字符串（如 `"40vp"`） THEN 解析为 VP 值 40（`StyleApplyUtilsLayout.cpp:49-60`） | 正常 |
| AC-1.3 | WHEN `width` 为百分比字符串（如 `"50%"`） THEN 解析为 PERCENT，`ApplyDimension` 走 `ApplyPercentDimension`（`StyleApplyUtilsLayout.cpp:56-58`、`ExtendedStyleResolver.cpp:1937-1940`） | 正常 |
| AC-1.4 | WHEN `width` 为关键字 `matchParent`/`fill`/`wrapContent`/`fixAtIdealSize` THEN `ParseKeywordDimension` 映射 MATCH_PARENT/WRAP_CONTENT/FIX_AT_IDEAL_SIZE（`StyleApplyUtilsLayout.cpp:32-47`） | 正常 |
| AC-1.5 | WHEN `width` 为负数、NaN/Infinity 或未知单位（如 `"100px"`、`"MatchParent"`） THEN 解析失败，`HandleInvalidDimensionInput` 重置为默认并上报告警（`StyleApplyUtilsLayout.cpp:117-118,141-148`、`ExtendedStyleResolver.cpp:1819-1841`） | 异常 |
| AC-1.6 | WHEN `height` 语义与 `width` 一致 THEN `ApplyDimension(..., isWidth=false)` 走相同分派（`ExtendedStyleResolver.cpp:1900-1907`） | 正常 |

### US-2: 约束尺寸（constraintSize）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.constraintSize` 限制组件最小/最大宽高,
**以便** 在约束区间内布局组件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `constraintSize` 为含 `minWidth/maxWidth/minHeight/maxHeight` 的对象 THEN `ApplyConstraintSizeStyle` 落库 `SetNodeConstraintSize`（`ExtendedStyleResolver.cpp:1425-1429`） | 正常 |
| AC-2.2 | WHEN `constraintSize` 各字段含百分比字符串 THEN `result.percentJson` 非空，走 native `SetPercentConstraintSize` 或跨语言桥分发 ETS（`ExtendedStyleResolver.cpp:1425-1459`） | 正常 |
| AC-2.3 | WHEN `constraintSize` 为非 object 或字段全部非法 THEN `ParseConstraintSizeStyle` 失败，`ReportInvalidConstraintSize` + `Reset`（`ExtendedStyleResolver.cpp:1463-1464`） | 异常 |
| AC-2.4 | WHEN `constraintSize` 对象缺省字段 THEN 缺省 minWidth/minHeight=0、maxWidth/maxHeight=不限，仅按缺省值处理该字段（`overview.md:954`） | 边界 |
| AC-2.5 | WHEN `constraintSize` 单个子字段类型不符/越界/单位不支持 THEN 仅该字段按缺省值（min→0、max→不限）降级，其余合法字段仍生效，并按子字段路径上报告警（`overview.md:954`） | 异常 |

### US-3: 宽高比（aspectRatio）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.aspectRatio` 指定组件宽高比,
**以便** 由一侧推导另一侧尺寸。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `aspectRatio` 为有限正数（如 `1.5`） THEN `ApplyAspectRatio` 落库 `SetNodeAspectRatio`（`ExtendedStyleResolver.cpp:929-932`） | 正常 |
| AC-3.2 | WHEN `aspectRatio` 为 0、负数或非有限值 THEN 上报 `SCHEMA_ERROR_CODE_INVALID_VALUE` 并回落 `DEFAULT_ASPECT_RATIO`（`ExtendedStyleResolver.cpp:937-944`） | 异常 |
| AC-3.3 | WHEN `aspectRatio` 非 number 类型 THEN 上报 `SCHEMA_ERROR_CODE_TYPE_MISMATCH` 并回落 `DEFAULT_ASPECT_RATIO`（`ExtendedStyleResolver.cpp:946-955`） | 异常 |

### US-4: 弹性收缩（flexShrink）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.flexShrink` 控制父容器空间不足时的收缩比例,
**以便** 实现弹性布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `flexShrink` 为 `[0,+∞)` 有限值 THEN `ParseFlexShrink` 成功，`SetNodeFlexShrink` 落库（`StyleApplyUtilsEffects.cpp:535-543`、`ExtendedStyleResolver.cpp:1315-1321`） | 正常 |
| AC-4.2 | WHEN `flexShrink` 为负数或非法类型 THEN 上报告警并 `Reset`（父组件为 Column/Row 时回 0，Flex 时回 1）（`ExtendedStyleResolver.cpp:1324-1341`、`ExtendedStyleResolver.cpp:1591-1602`） | 异常 |
| AC-4.3 | WHEN `flexShrink` 未设置且父组件为 Column/Row THEN `UpdateFlexShrinkStyleState` 标记 `PARENT_DEFAULT`，默认收缩比例 0（`ExtendedComponent.cpp:994-1014`） | 边界 |

### US-5: 弹性权重（layoutWeight）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.layoutWeight` 在 Row/Column 内按比例分配剩余空间,
**以便** 实现等比例布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `layoutWeight` 为非负有限数且 >0 THEN `ApplyLayoutWeightStyle` 以截断后的 uint32 落库（如 `2.6`→2）（`ExtendedStyleResolver.cpp:1384-1388`） | 正常 |
| AC-5.2 | WHEN `layoutWeight` 为 0、负数或非有限值 THEN 不应用（保持默认 0），仅 `>0` 时落库（`ExtendedStyleResolver.cpp:1385-1389`） | 边界 |
| AC-5.3 | WHEN `layoutWeight` 为非 number 类型（布尔/对象/"2vp"） THEN 上报 `TYPE_MISMATCH` 并 `Reset` 为默认（`ExtendedStyleResolver.cpp:1396-1406`） | 异常 |
| AC-5.4 | WHEN `layoutWeight` 小数部分被截断 THEN 仅非负整数部分生效（`overview.md:963`、`ExtendedStyleResolver.cpp:1387`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2 | T-1 | C++ UT：`ParseDimension`/`ApplyDimension` 尺寸分派 | `StyleApplyUtilsLayout.cpp:110-153`、`ExtendedStyleResolver.cpp:1910-1951` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-3 | T-1 | C++ UT：`ApplyConstraintSizeStyle` 约束与降级 | `ExtendedStyleResolver.cpp:1409-1465` |
| AC-3.1,AC-3.2,AC-3.3 | R-4 | T-1 | C++ UT：`ApplyAspectRatio` 回落默认 | `ExtendedStyleResolver.cpp:916-957` |
| AC-4.1,AC-4.2,AC-4.3 | R-5 | T-1 | C++ UT：`ParseFlexShrink`/`UpdateFlexShrinkStyleState` | `StyleApplyUtilsEffects.cpp:535-543`、`ExtendedComponent.cpp:994-1014` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-6 | T-1 | C++ UT：`ApplyLayoutWeightStyle` 截断与降级 | `ExtendedStyleResolver.cpp:1377-1407` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 尺寸为数字或 vp/ 百分比字符串 | 按 VP/PERCENT 单位落库 | 数字默认 VP；仅 vp/% 后缀 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 异常 | 尺寸为负数/NaN/Infinity/未知单位/非法关键字 | 解析失败，重置默认并上报告警 | 关键字大小写敏感；不认 px | AC-1.5,AC-1.6 |
| R-3 | 边界 | constraintSize 字段缺省或单个字段非法 | 缺省 min→0/max→不限；单字段非法仅该字段降级 | min>max 不校验，直接透传 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-4 | 异常 | aspectRatio 非有限正数或非 number | 回落 `DEFAULT_ASPECT_RATIO` | 区分 INVALID_VALUE/TYPE_MISMATCH | AC-3.1,AC-3.2,AC-3.3 |
| R-5 | 边界 | flexShrink 越界或父容器为 Column/Row/Flex | 越界 reset；父容器决定默认 0/1 | Column/Row→0，Flex→1 | AC-4.1,AC-4.2,AC-4.3 |
| R-6 | 边界 | layoutWeight 小数/负数/非 number | 小数截断、负数不应用、非 number reset | 仅非负整数有效 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 尺寸解析 | C++ UT | vp/% 与关键字、非法单位重置 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 constraintSize | C++ UT + 文档比对 | 缺省与单字段降级 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 aspectRatio | C++ UT | 非法值回落默认 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 flexShrink | C++ UT | 父容器相关默认 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 layoutWeight | C++ UT | 截断与降级 |

## API 变更分析

> 存量补录，无新增/变更 Public/C/System API。通用样式经 DSL `styles` 对象承载。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `styles.width`/`styles.height` | 既有 | 组件尺寸 | vp/% / 关键字枚举 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| `styles.constraintSize` | 既有 | 尺寸约束 | 四字段对象 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| `styles.aspectRatio` | 既有 | 宽高比 | 有限正数 | AC-3.1,AC-3.2,AC-3.3 |
| `styles.flexShrink` | 既有 | 弹性收缩 | `[0,+∞)` | AC-4.1,AC-4.2,AC-4.3 |
| `styles.layoutWeight` | 既有 | 弹性权重 | 非负整数（截断） | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json:287-403,675-689`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`StyleApplyUtils::ParseDimension(value, dimension)`（`StyleApplyUtilsLayout.cpp:110`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseDimension(const JsonValue& value, StyleDimension& dimension)` |
| 返回值 | `bool` — 解析成功与否 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（返回 false，调用方 reset） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |

**`ExtendedStyleResolver::ApplyDimension(value, applier, isWidth, issues, dispatchContext)`（`ExtendedStyleResolver.cpp:1910`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static void ApplyDimension(const JsonValue&, ArkUINodeApiAdapter&, bool isWidth, std::vector<DescriptorValidationIssue>&, std::optional<ConstraintDispatchContext>)` |
| 返回值 | `void` — 非法值经 `issues` 上报告警并 reset |
| 开放范围 | 内部 |
| 错误码 | `SCHEMA_ERROR_CODE_TYPE_MISMATCH` / `SCHEMA_ERROR_CODE_INVALID_VALUE` |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number \| string | 否 | 组件原生默认尺寸 | number∈[0,+∞)；string 匹配 `N(vp\|%)?` 或关键字 |
| isWidth | bool | 是 | — | true→width，false→height |
| constraintSize | object | 否 | 无约束 | 四字段均可选，缺省 min=0/max=不限 |
| aspectRatio | number | 否 | 1.0 | 有限正数 |
| flexShrink | number | 否 | 父容器相关 | `[0,+∞)` 有限 |
| layoutWeight | number | 否 | 0 | 非负，小数截断 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | width=200 | VP 落库 | AC-1.1 |
| 2 | height="40vp" | VP 落库 | AC-1.6 |
| 3 | width="50%" | PERCENT 落库 | AC-1.3 |
| 4 | width="100px" | 解析失败，reset + 告警 | AC-1.5 |
| 5 | constraintSize 字段全非法 | 整体 reset | AC-2.3 |
| 6 | aspectRatio=-1 | 回落默认 | AC-3.2 |
| 7 | layoutWeight=2.6 | 截断为 2 | AC-5.1,AC-5.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 契约随 `extended_catalog.json` 版本演进；尺寸关键字别名 `fill` 为 `matchParent` 同义（见 RISK-4）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 单位集固定 | 通用尺寸仅 vp/%，px 非通用单位 | AC-1.5 |
| 尺寸分派顺序 | Match/LayoutPolicy→百分比→绝对，`constraintSize` 优先于 `aspectRatio` | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3 |
| 双路径一致 | C++/ETS 非法值降级需对齐（layoutWeight 存在差异见 RISK-3） | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法尺寸不中断渲染，统一 reset + 告警 | C++ UT | `ExtendedStyleResolver.cpp:1819-1841` |
| 性能 | 数字尺寸 static float→f 解析 O(1) | C++ UT | `StyleApplyUtilsInternal.h:41-54` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 尺寸语义设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 断点主题走表达式变量（`$__widthBreakpoint`） | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 尺寸样式不涉及 | — |
| 大字体 | 否 | 不涉及字体 | — |
| 深色模式 | 否 | 颜色归 Feat-03；断点表达式另域 | — |
| 多窗口/分屏 | 是 | 百分比/`matchParent` 随父容器内容区重算 | AC-1.3,AC-1.4 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 契约随扩展协议版本演进 | 概述「目标版本」 |
| 生态兼容 | 是 | 扩展协议 CommonStyles 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 尺寸与布局样式
  作为 生成式 UI 宿主开发者
  我想要 通过 styles 控制组件的宽高、约束、宽高比与弹性
  以便 实现灵活布局

  Scenario: 固定宽度落库
    Given DSL styles 为 {"width": 200}
    When 渲染引擎解析样式
    Then 组件宽度按 200vp 应用

  Scenario Outline: 非法尺寸降级
    Given styles 为 <styles>
    When 渲染引擎解析样式
    Then 指定属性重置为默认并上报 schema warning

    Examples:
      | styles |
      | {"width": -10} |
      | {"width": "100px"} |
      | {"width": "MatchParent"} |
      | {"aspectRatio": 0} |
      | {"layoutWeight": "2vp"} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做尺寸布局；间距边框/背景颜色/视效/显示裁切归 Feat-02~05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseDimension ParseKeywordDimension 尺寸单位 vp % matchParent"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedStyleResolver ApplyDimension ApplyConstraintSizeStyle ApplyAspectRatio ParseFlexShrink layoutWeight"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedStyleResolver ApplyLayoutWeight 截断 flexShrink reset parent"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/styles/StyleApplyUtilsLayout.cpp`、`genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp`、`reference/extended-components/overview.md`