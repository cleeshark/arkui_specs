# 特性规格

> Func-07-04-23-Feat-02 自适应单位：固化单位解析（`ParseDimension`：纯数字默认 vp、`vp`、`%`、keyword `matchParent`/`fill`/`wrapContent`/`fixAtIdealSize`；stroke width 额外 `px`）、密度采集（`resolveDisplayDensityPixels`：densityPixels 优先、否则 densityDPI/160）、fp→vp 换算（`resolveFpToVpScale` = `px2vp(fp2px(1))`，native `DisplayDensityUtils::ConvertFpToVp`）、字体缩放（`setFontSizeScale`→`SurfaceSlot`→`OnFontSizeScaleChanged`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 自适应单位 |
| 特性编号 | Func-07-04-23-Feat-02 |
| 优先级 | P0 |
| 目标版本 | OpenHarmony API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性承接 Feat-01 断点基线，固化单位/密度/字体缩放解析 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/23-multi-device-adaptation/design.md` | Baselined |
| 单位解析（C++） | `genui/src/main/cpp/styles/StyleApplyUtilsLayout.cpp` | — |
| 单位类型（C++） | `genui/src/main/cpp/styles/StyleTypes.h` | — |
| 密度工具（C++） | `genui/src/main/cpp/utils/DisplayDensityUtils.cpp`、`DisplayDensityUtils.h` | — |
| 密度采集（ArkTS） | `genui/src/main/ets/core/components/UIRendererComponentCore.ets` | — |
| 字体缩放（ArkTS/C++） | `genui/src/main/ets/interface/SurfaceController.ets`、`SurfaceControllerImpl.ets`、`cpp/RenderSlot.cpp`、`cpp/SurfaceSlot.cpp`、`cpp/SurfaceManager.cpp` | — |
| fontSize 应用（C++） | `genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp` | — |
| 概念参考（Docs） | `concepts/multi-device-adaptation.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 通用维度单位解析

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎解析 vp/%/关键词单位,
**以便** 同一尺寸 DSL 在不同密度设备上正确渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `ParseDimension` 收到 number（有限非负） THEN 解析为 VP 单位（`StyleApplyUtilsLayout.cpp:115-122`） | 正常 |
| AC-1.2 | WHEN `ParseDimension` 收到 `"16vp"` 后缀 THEN 解析为 VP 单位数值 16（`StyleApplyUtilsLayout.cpp:49-61,145-152`） | 正常 |
| AC-1.3 | WHEN `ParseDimension` 收到 `"50%"` 后缀 THEN 解析为 PERCENT 单位（`StyleApplyUtilsLayout.cpp:56-58`） | 正常 |
| AC-1.4 | WHEN `ParseDimension` 收到 `"matchParent"`/`"fill"` THEN 解析为 MATCH_PARENT（`StyleApplyUtilsLayout.cpp:34-37`） | 正常 |
| AC-1.5 | WHEN `ParseDimension` 收到 `"wrapContent"`/`"fixAtIdealSize"` THEN 分别解析为 WRAP_CONTENT/FIX_AT_IDEAL_SIZE（`StyleApplyUtilsLayout.cpp:38-45`） | 正常 |
| AC-1.6 | WHEN `ParseDimension` 收到无后缀纯数字字符串（如 `"16"`） THEN 后缀为空，解析为 VP（`StyleApplyUtilsLayout.cpp:52-54`） | 边界 |
| AC-1.7 | WHEN `ParseDimension` 收到负数/非有限数值 THEN 返回 false（`StyleApplyUtilsLayout.cpp:117-118,141-142`） | 异常 |
| AC-1.8 | WHEN `ParseDimension` 收到非法后缀（如 `"10rem"`/`"10fp"`） THEN `ParseDimensionUnitSuffix` 返回 false，整体返回 false（`StyleApplyUtilsLayout.cpp:49-61,146-149`） | 异常 |

### US-2: stroke width 专有 px 解析

**作为** 生成式 UI 宿主开发者,
**我想要** stroke width 支持 px 单位,
**以便** 精确指定边框/分割线像素宽度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ParseDividerStrokeWidth` 收到纯 number THEN 解析为 vp 数值（`StyleApplyUtilsLayout.cpp:95-103`） | 正常 |
| AC-2.2 | WHEN stroke width token 以 `px` 结尾 THEN 单位标记为 `"px"`（`StyleApplyUtilsLayout.cpp:77-79`） | 正常 |
| AC-2.3 | WHEN stroke width token 以 `%` 结尾 THEN 单位标记为 `"%"`（`StyleApplyUtilsLayout.cpp:74-76`） | 正常 |
| AC-2.4 | WHEN stroke width token 以 `vp` 结尾或默认 THEN 单位标记为 `"vp"`（`StyleApplyUtilsLayout.cpp:80-83`） | 正常 |
| AC-2.5 | WHEN stroke width 数值为负或无量纲非法 THEN 返回 false（`StyleApplyUtilsLayout.cpp:85,97-98`） | 异常 |
| AC-2.6 | WHEN `ExtendedDivider` 收到 `"…px"` 字面量 THEN 经 `px2vp` 换算为 vp（`ExtendedDivider.ets:130-132`） | 正常 |
| AC-2.7 | WHEN `ExtendedDivider` 收到 `"…fp"` 字面量 THEN 经 `px2vp(fp2px(value))` 换算（`ExtendedDivider.ets:133-135`） | 正常 |

### US-3: 密度采集与 px→vp 换算

**作为** 渲染引擎开发者,
**我想要** native 侧按 renderId 缓存显示密度,
**以便** px 单位精确换算为 vp。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `densityPixels` 有限且 >0 THEN `resolveDisplayDensityPixels` 返回 densityPixels（`UIRendererComponentCore.ets:71-72`） | 正常 |
| AC-3.2 | WHEN `densityPixels` 无效但 `densityDPI` 有效 THEN 返回 `densityDPI/160`（`UIRendererComponentCore.ets:74-77`） | 边界 |
| AC-3.3 | WHEN 两者均无效 THEN 返回 undefined（`UIRendererComponentCore.ets:74-75`） | 异常 |
| AC-3.4 | WHEN `dispatchDisplayDensityToNative` 收到非有限或 ≤0 的 densityPixels THEN 返回 false 不下发（`UIRendererComponentCore.ets:86-88`） | 异常 |
| AC-3.5 | WHEN `DisplayDensityUtils::SetDisplayDensity` 收到非法 renderId/densityPixels THEN 打 warn 并忽略（`DisplayDensityUtils.cpp:41-48`） | 异常 |
| AC-3.6 | WHEN `ConvertPxToVp` 且密度存在 THEN 返回 `px/densityPixels`（`DisplayDensityUtils.cpp:87`） | 正常 |
| AC-3.7 | WHEN `ConvertPxToVp` 且密度缺失 THEN 打 warn 并原样返回 px（`DisplayDensityUtils.cpp:81-86`） | 异常 |

### US-4: fp 换算与字体缩放

**作为** 生成式 UI 宿主开发者,
**我想要** fp 单位跟随系统字体缩放,
**以便** 大字体设置下文本正确缩放。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `resolveFpToVpScale` 计算 THEN 返回 `px2vp(fp2px(1))`（`UIRendererComponentCore.ets:298-308`） | 正常 |
| AC-4.2 | WHEN `oneFpPx`/`oneFpVp` 非有限或 ≤0 THEN 返回 0（`UIRendererComponentCore.ets:300-307`） | 边界 |
| AC-4.3 | WHEN `SetDisplayDensity` 收到合法 fpToVpScale THEN 缓存到 `fpToVpScale`（`DisplayDensityUtils.cpp:51-56`） | 正常 |
| AC-4.4 | WHEN `ConvertFpToVp` 且 fpToVpScale 存在 THEN 返回 `fp*fpToVpScale`（`DisplayDensityUtils.cpp:103`） | 正常 |
| AC-4.5 | WHEN `ConvertFpToVp` 且 fp 比例缺失 THEN 打 warn 并原样返回 fp（`DisplayDensityUtils.cpp:97-101`） | 异常 |
| AC-4.6 | WHEN `setFontSizeScale(scale)` 且 apiSupported THEN 经 NAPI 下发 `setFontSizeScale`（`SurfaceControllerImpl.ets:1123-1132`） | 正常 |
| AC-4.7 | WHEN `SurfaceManager::SetFontSizeScale` 收到 scale≤0 THEN 回落 1.0（`SurfaceManager.cpp:146`） | 边界 |
| AC-4.8 | WHEN `SurfaceSlot::SetFontSizeScale` 执行 THEN 对有 extended 组件触发 `OnFontSizeScaleChanged`（`SurfaceSlot.cpp:1609-1630`） | 正常 |

### US-5: fontSize 单位与文档一致性

**作为** 渲染引擎开发者,
**我想要** 明确 fontSize 的单位解析边界,
**以便** 分辨文档描述与实现差异。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN fontSize 样式为纯 number THEN `ParseNumber` 成功应用（`ExtendedStyleResolver.cpp:1016-1020`） | 正常 |
| AC-5.2 | WHEN fontSize 为 `"16fp"` 字符串 THEN `ParseNumber`（全量数字 token 校验）失败并打 `style=fontSize ignored`（`ExtendedStyleResolver.cpp:1020-1022` + `StyleApplyUtilsInternal.h:41-54`） | 异常 |
| AC-5.3 | WHEN `ParseDimension` 收到 `"16fp"` THEN 因后缀 `fp` 未在 `ParseDimensionUnitSuffix` 支持表内而返回 false（`StyleApplyUtilsLayout.cpp:49-61`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7,AC-1.8 | R-1,R-2,R-3 | T-2 | C++ UT：ParseDimension 单位/关键词 | `StyleApplyUtilsLayout.cpp:110-153` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-2.7 | R-4 | T-2 | C++ UT + ArkTS 单测：stroke width px | `StyleApplyUtilsLayout.cpp:63-108`、`ExtendedDivider.ets:126-136` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 | R-5,R-6 | T-2 | ArkTS 单测 + C++ UT：密度换算 | `UIRendererComponentCore.ets:67-91`、`DisplayDensityUtils.cpp:39-108` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8 | R-7,R-8 | T-2 | ArkTS 单测 + C++ UT：fp 换算与缩放 | `UIRendererComponentCore.ets:298-308`、`SurfaceSlot.cpp:1609-1630` |
| AC-5.1,AC-5.2,AC-5.3 | R-9 | T-2 | C++ UT：fontSize 单位边界 | `ExtendedStyleResolver.cpp:1016-1022` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | ParseDimension 收到数值/字符串 | 解析为 VP/PERCENT/keyword | 纯数字默认 vp | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| R-2 | 异常 | 负数/非有限数值 | 返回 false | — | AC-1.7 |
| R-3 | 异常 | 非法后缀（含 fp/rem） | 返回 false | 仅 vp/% 后缀合法 | AC-1.8,AC-5.3 |
| R-4 | 行为 | stroke width 单位 | 支持 vp/%/px | ArkTS 侧 px→px2vp、fp→px2vp(fp2px) | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-2.7 |
| R-5 | 边界 | densityPixels 无效 | 回落 densityDPI/160 | 均无效返回 undefined | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-6 | 异常 | 密度缺失时 ConvertPxToVp | 原样返回 px | 仅告警不崩溃 | AC-3.6,AC-3.7 |
| R-7 | 行为 | fp 换算 | `px2vp(fp2px(1))`，`fp*fpToVpScale` | 非法回落 0/原样返回 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-8 | 边界 | fontSizeScale≤0 | 回落 1.0 | — | AC-4.7 |
| R-9 | 异常 | fontSize `16fp` | ParseNumber 失败忽略 | 文档与实现分歧（RISK-2） | AC-5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7,AC-1.8 通用维度单位 | C++ UT | vp/%/keyword/负值/非法后缀 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-2.7 stroke width px | C++ UT + ArkTS 单测 | px/fp/vp/% token |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 密度换算 | ArkTS 单测 + C++ UT | densityPixels 回落与 px→vp |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8 fp 与字体缩放 | ArkTS 单测 + C++ UT | fpToVpScale + fontSizeScale |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 fontSize 单位边界 | C++ UT | 16fp 被忽略 |

## API 变更分析

> 存量补录，无新增 API。公开契约仅 `SurfaceController.setFontSizeScale` 现状覆盖。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceController.setFontSizeScale` | 既有 | 系统字体缩放 | 数值稳定 | AC-4.6 |
| `StyleDimensionUnit`（internal） | 既有 | 单位分类 | VP/PERCENT/MATCH_PARENT/WRAP_CONTENT/FIX_AT_IDEAL_SIZE/INVALID | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7,AC-1.8 |

> d.ts 位置：`genui/src/main/ets/interface/SurfaceController.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`StyleApplyUtils::ParseDimension(value, dimension)`（`StyleApplyUtilsLayout.cpp:110`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseDimension(const JsonValue& value, StyleDimension& dimension)` |
| 返回值 | `bool` — 解析成功与否 |
| 开放范围 | 内部（C++） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7,AC-1.8 |

**`DisplayDensityUtils::SetDisplayDensity(renderId, densityPixels, fpToVpScale)`（`DisplayDensityUtils.cpp:39`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void SetDisplayDensity(int32_t renderId, float densityPixels, float fpToVpScale = 0.0F)` |
| 返回值 | `void` |
| 开放范围 | 内部（C++） |
| 错误码 | N/A |
| 关联 AC | AC-3.5,AC-4.3 |

**`SurfaceController.setFontSizeScale(scale)`（`SurfaceController.ets:121`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setFontSizeScale(scale: number): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.6,AC-4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | JsonValue | 是 | — | number（非负有限）或 string（vp/%/keyword） |
| densityPixels | number | 是 | — | 有限且 >0 |
| fpToVpScale | number | 否 | 0.0F | 有限且 >0（否则忽略） |
| scale | number | 是 | 1.0（回落） | >0 生效 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 值 = 16 或 "16" | VP 数值 16 | AC-1.1,AC-1.6 |
| 2 | 值 = "50%" | PERCENT 50 | AC-1.3 |
| 3 | 值 = "matchParent" | MATCH_PARENT | AC-1.4 |
| 4 | 值 = "10fp" | 返回 false | AC-1.8,AC-5.3 |
| 5 | densityPixels 无效 | 回落 densityDPI/160 | AC-3.2 |
| 6 | scale≤0 | 回落 1.0 | AC-4.7 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** OpenHarmony API Version 20。
- **API 版本号策略:** `setFontSizeScale` 随扩展协议引入；密度/单位解析为 framework-internal 无独立版本策略。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 通用维度不含 px/fp | `ParseDimension` 仅 vp/%/keyword；px 仅 stroke width；fp 走换算通道 | AC-1.8,AC-5.3 |
| 密度单例按 renderId 缓存 | `DisplayDensityUtils` 进程级单例，map 索引 renderId | AC-3.5,AC-3.6,AC-3.7 |
| 字体缩放回落 | scale≤0 回落 1.0，避免负缩放 | AC-4.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法密度/单位不崩溃，降级原样返回或告警 | C++ UT | `DisplayDensityUtils.cpp:81-86,97-101` |
| 性能 | 密度按 renderId 缓存，避免重复查询 | ArkTS 单测 | `DisplayDensityUtils.cpp:56` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | densityPixels 取设备值，vp 缩放 | 无差异 | ohosTest | `UIRendererComponentCore.ets:286-292` |
| 平板 | 同上，密度不同 | 无差异 | ohosTest | 同上 |
| 折叠屏 | 动态密度变化 | px→vp 随密度换算 | ohosTest | `DisplayDensityUtils.cpp:78-92` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 单位解析不涉及 | — |
| 大字体 | 是 | `setFontSizeScale`+fp 换算跟随系统字体 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8 |
| 深色模式 | 否 | 颜色语义见 07-04-24 | — |
| 多窗口/分屏 | 是 | 密度随窗口/显示变化 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6,AC-3.7 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 20 起 | 兼容性 |
| 生态兼容 | 是 | 鸿蒙扩展协议单位语义 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 自适应单位
  作为 生成式 UI 宿主开发者
  我想要 单位按密度正确换算
  以便 跨设备物理尺寸一致

  Scenario: 密度回落
    Given displayResult.densityPixels 无效
    When 调用 resolveDisplayDensityPixels(densityPixels=0, densityDPI=320)
    Then 返回 2.0

  Scenario: fp 换算
    Given densityByRenderId_ 已缓存 fpToVpScale=1.4
    When 调用 ConvertFpToVp(renderId, 16)
    Then 返回 22.4

  Scenario Outline: 维度单位解析
    Given 调用 ParseDimension(<input>)
    Then 返回 <result> 且单位为 <unit>

    Examples:
      | input        | result | unit |
      | 16           | true   | VP   |
      | "50%"        | true   | PERCENT |
      | "matchParent"| true   | MATCH_PARENT |
      | "10fp"       | false  | -    |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做单位/密度/字体缩放；断点见 Feat-01，条件重渲染见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ParseDimension ParseDimensionUnitSuffix ParseKeywordDimension vp percent matchParent wrapContent"
  - repo: "GenerativeUI/A2UIRender"
    query: "ParseDividerStrokeWidth ParseStrokeWidthTokenInternal px vp percent"
  - repo: "GenerativeUI/A2UIRender"
    query: "DisplayDensityUtils SetDisplayDensity ConvertPxToVp ConvertFpToVp densityByRenderId"
  - repo: "GenerativeUI/A2UIRender"
    query: "resolveDisplayDensityPixels resolveFpToVpScale pushDisplayDensity dispatchDisplayDensityToNative"
  - repo: "GenerativeUI/A2UIRender"
    query: "setFontSizeScale SurfaceSlot OnFontSizeScaleChanged SurfaceManager"
```

**关键文档：** `genui/src/main/cpp/styles/StyleApplyUtilsLayout.cpp`、`genui/src/main/cpp/utils/DisplayDensityUtils.cpp`、`genui/src/main/ets/core/components/UIRendererComponentCore.ets`、`genui/src/main/cpp/SurfaceSlot.cpp`、`genui/src/main/cpp/components/extended/ExtendedStyleResolver.cpp`