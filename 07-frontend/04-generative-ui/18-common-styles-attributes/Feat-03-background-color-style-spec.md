# 特性规格

> Func-07-04-18-Feat-03 背景与颜色样式：固化扩展协议通用样式中 `backgroundColor`（颜色）与 `backgroundImage`/`backgroundImageSizeWithStyle`/`linearGradient`（背景）四项属性的解析、应用与非法值降级。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 背景与颜色样式 |
| 特性编号 | Func-07-04-18-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议 1.0.0（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 承继 Feat-01/02 基线，追加背景与颜色四项通用样式 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/18-common-styles-attributes/design.md` | Baselined |
| 契约（JSON Schema） | `specification/extended/1.0.0/extended_catalog.json` | — |
| 底层视效解析（C++） | `genui/src/main/cpp/styles/StyleApplyUtilsEffects.cpp` | — |
| 样式应用（C++） | `genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp` | — |
| ETS 回退应用（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedCommonStyleModifier.ets` | — |
| 文档参考（Docs） | `reference/extended-components/overview.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 背景色（backgroundColor）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.backgroundColor` 指定组件背景色,
**以便** 用 hex 颜色设置背景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `backgroundColor` 为 `#RRGGBB`/`#AARRGGBB` THEN `ParseColor` 成功，`SetBackgroundColor` 落库（`StyleApplyUtils.cpp:40-60`、`ExtendedStyleResolver.cpp:962-965`） | 正常 |
| AC-1.2 | WHEN `backgroundColor` 为 `#RGB`/命名色/`rgb()`/缺 `#` THEN 解析失败，`Reset` 为默认透明并上报告警（`ExtendedStyleResolver.cpp:966-981`、`overview.md:959`） | 异常 |
| AC-1.3 | WHEN `backgroundColor` 显式 `null` THEN 上报 `TYPE_MISMATCH`，其余非法值上报 `INVALID_VALUE`（`ExtendedStyleResolver.cpp:971-979`） | 异常 |

### US-2: 背景图（backgroundImage）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.backgroundImage` 指定背景图片 URL,
**以便** 加载背景图。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `backgroundImage` 为非空字符串（trim 后） THEN `ParseBackgroundImage` 成功，`SetNodeBackgroundImage` 落库（`StyleApplyUtilsEffects.cpp:545-555`、`ExtendedStyleResolver.cpp:1511-1515`） | 正常 |
| AC-2.2 | WHEN `backgroundImage` 为空串或纯空白 THEN `ApplyBackgroundImage` 走 reset 分支，清除背景图（`ExtendedStyleResolver.cpp:1502-1508`） | 边界 |
| AC-2.3 | WHEN `backgroundImage` 为非 string 类型 THEN 上报 `TYPE_MISMATCH` 并 reset（`ExtendedStyleResolver.cpp:1474-1489`） | 异常 |

### US-3: 背景图尺寸（backgroundImageSizeWithStyle）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.backgroundImageSizeWithStyle` 指定背景图尺寸,
**以便** 用枚举或 {width,height} 控制填充方式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `backgroundImageSizeWithStyle` 为字符串枚举 `cover`/`contain`/`auto` THEN `ParseBackgroundImageSize` 映射 IMAGE_SIZE，native `SetNodeBackgroundImageSizeWithStyle` 落库（`StyleApplyUtilsEffects.cpp:470-483,58-60`） | 正常 |
| AC-3.2 | WHEN `backgroundImageSizeWithStyle` 为 `fill` THEN 分发到 ETS 侧（native C 枚举不含 FILL）（`ExtendedStyleResolver.cpp:2208-2221`） | 边界 |
| AC-3.3 | WHEN `backgroundImageSizeWithStyle` 为对象 `{width,height}` THEN 仅 vp/% 且 ≥0、有限，`SetNodeBackgroundImageSize` 落库；缺一维按 0 由渲染层按原图宽高比推导（`StyleApplyUtilsEffects.cpp:485-507`、`overview.md:961`） | 正常 |
| AC-3.4 | WHEN `backgroundImageSizeWithStyle` 为非法枚举/负值/NaN/非法对象 THEN reset 为默认 auto 并上报告警（`ExtendedStyleResolver.cpp:2260-2273`、`StyleApplyUtilsEffects.cpp:473-479`） | 异常 |

### US-4: 线性渐变（linearGradient）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.linearGradient` 指定线性渐变填充,
**以便** 用角度/方向 + 颜色 stop 控制渐变。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `linearGradient` 为含 `colors` 数组的对象且每项为 `[color, position]` 对 THEN `ParseLinearGradient` 成功，`SetNodeLinearGradient` 落库（`StyleApplyUtilsEffects.cpp:510-533`、`ExtendedStyleResolver.cpp:2342-2344`） | 正常 |
| AC-4.2 | WHEN `linearGradient` 的 `angle`/`direction`/`repeating` 合法 THEN 按角度（`ParseAngleToken` 支持 deg/rad/grad/turn）或方向枚举解析（`StyleApplyUtilsEffects.cpp:264-299,368-390`） | 正常 |
| AC-4.3 | WHEN `linearGradient` stop 越界或非单调递减 THEN `ClampStop` 限制在 `[0,1]` 且强制单调不减（`StyleApplyUtilsEffects.cpp:340-349,443-449`） | 边界 |
| AC-4.4 | WHEN `linearGradient` 的 `colors` 缺失/非数组/空数组或整体非 object THEN 整体 reset 为无渐变并上报告警（`StyleApplyUtilsEffects.cpp:518-524`、`ExtendedStyleResolver.cpp:2333-2337`） | 异常 |
| AC-4.5 | WHEN `linearGradient` 单个 color-stop 项非法（颜色非 hex） THEN 跳过该项，其余项仍生效（`StyleApplyUtilsEffects.cpp:432-441`、`overview.md:962`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-3 | C++ UT：`ParseColor`/`ApplyColorStyles` | `StyleApplyUtils.cpp:40-60`、`ExtendedStyleResolver.cpp:959-1003` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-3 | C++ UT：`ParseBackgroundImage`/`ApplyBackgroundImage` | `StyleApplyUtilsEffects.cpp:545-555`、`ExtendedStyleResolver.cpp:1467-1516` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-3 | C++ UT：`ParseBackgroundImageSize`/`ApplyBackgroundImageSize` | `StyleApplyUtilsEffects.cpp:470-508`、`ExtendedStyleResolver.cpp:2252-2275` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-4 | T-3 | C++ UT：`ParseLinearGradient`/`ApplyLinearGradient` | `StyleApplyUtilsEffects.cpp:510-533`、`ExtendedStyleResolver.cpp:2329-2345` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 异常 | backgroundColor 非法 hex/null | reset 透明 + 告警；null 归 TYPE_MISMATCH | 仅 6/8 hex | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 边界 | backgroundImage 空串/非 string | 空串 reset；非 string 上报 reset | trim 后透传 | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 边界 | backgroundImageSize 枚举/对象/非法 | 枚举（cover/contain/auto native，fill ETS）；对象 vp/%≥0；非法 reset auto | 缺一维按 0 推导 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 边界 | linearGradient colors/stops/字段非法 | 缺 colors 整体 reset；stop 钳制 [0,1] 单调；单色项跳过 | 角度支持 deg/rad/grad/turn | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 backgroundColor | C++ UT | hex 校验与 reset |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 backgroundImage | C++ UT | 空串/非 string |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 backgroundImageSize | C++ UT | 枚举/对象/非法 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 linearGradient | C++ UT | stop 钳制与单色项跳过 |

## API 变更分析

> 存量补录，无新增/变更 Public/C/System API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `styles.backgroundColor` | 既有 | 背景色 | hex | AC-1.1,AC-1.2,AC-1.3 |
| `styles.backgroundImage` | 既有 | 背景图 | 字符串 URL | AC-2.1,AC-2.2,AC-2.3 |
| `styles.backgroundImageSizeWithStyle` | 既有 | 背景图尺寸 | 枚举/对象 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| `styles.linearGradient` | 既有 | 线性渐变 | 对象 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json:229-286,404-416,571-583,742-784`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`StyleApplyUtils::ParseColor(value, color)`（`StyleApplyUtils.cpp:31`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseColor(const JsonValue& value, uint32_t& color)` |
| 返回值 | `bool` — 是否解析为合法 hex |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`StyleApplyUtils::ParseLinearGradient(value, gradient)`（`StyleApplyUtilsEffects.cpp:510`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseLinearGradient(const JsonValue& value, StyleLinearGradient& gradient)` |
| 返回值 | `bool` — colors 非空且 colors/stops 长度一致 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| backgroundColor | string | 否 | 透明 | `#RRGGBB`/`#AARRGGBB` |
| backgroundImage | string | 否 | 无背景图 | 非空字符串 |
| backgroundImageSizeWithStyle | string \| object | 否 | auto | 枚举 cover/contain/auto/fill；对象 {width,height} |
| linearGradient.colors | array | 是 | [] | 每项 `[color, position]`，color 为 hex |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | backgroundColor="#F0F0F0" | 背景落库 #FFF0F0F0 | AC-1.1 |
| 2 | backgroundColor="red" | reset 透明 + 告警 | AC-1.2 |
| 3 | backgroundImage="http://x/i.png" | 背景图落库 | AC-2.1 |
| 4 | backgroundImageSizeWithStyle="fill" | 分发 ETS | AC-3.2 |
| 5 | linearGradient stop=[1.5] | 钳制为 1.0 | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议 1.0.0。
- **API 版本号策略:** 契约随 `extended_catalog.json` 版本演进；`backgroundImageSizeWithStyle` 大小写变体键（`backgroundimageSizeWithStyle` 等）为内部兼容别名（见 RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 颜色单一形态 | 背景/边框色仅 6/8 hex | AC-1.1,AC-1.2,AC-1.3 |
| FILL 走 ETS | native C 枚举无 FILL，需跨语言桥分发 | AC-3.2 |
| 渐变 stop 单调 | stop 钳制 [0,1] 且非递减 | AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法背景/渐变不中断渲染，统一 reset + 告警 | C++ UT | `ExtendedStyleResolver.cpp:2294-2314` |
| 性能 | 颜色解析常数次字符比较 | C++ UT | `StyleApplyUtils.cpp:40-60` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 背景/颜色语义设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 是 | 未显式设置时 backgroundColor 跟随组件/主题默认（TextInput/Button 等见组件域） | AC-1.1,AC-1.2,AC-1.3 |
| 多窗口/分屏 | 是 | 百分比尺寸随父容器内容区重算 | AC-3.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 契约随扩展协议版本演进 | 概述「目标版本」 |
| 生态兼容 | 是 | CommonStyles 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 背景与颜色样式
  作为 生成式 UI 宿主开发者
  我想要 通过 styles 控制背景色、背景图与线性渐变
  以便 实现丰富的视觉填充

  Scenario: 线性渐变 stop 钳制
    Given linearGradient colors 为 [["#FF0000",0],["#0000FF",1.5]]
    When 渲染引擎解析样式
    Then 第二个 stop 钳制为 1.0

  Scenario Outline: 非法背景/渐变降级
    Given styles 为 <styles>
    When 渲染引擎解析样式
    Then 指定属性重置为默认并上报 schema warning

    Examples:
      | styles |
      | {"backgroundColor": "blue"} |
      | {"backgroundImageSizeWithStyle": "stretch"} |
      | {"linearGradient": {"colors": []}} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做背景与颜色；间距边框归 Feat-02，视效归 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseColor NormalizeHexColor backgroundColor backgroundImage"
  - repo: "GenerativeUI/A2UIRender"
    query: "StyleApplyUtils ParseBackgroundImageSize ParseLinearGradient ClampStop gradient stops"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedStyleResolver ApplyColorStyles ApplyBackgroundImage ApplyLinearGradient fill ETS dispatch"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/styles/StyleApplyUtilsEffects.cpp`、`genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp`、`reference/extended-components/overview.md`