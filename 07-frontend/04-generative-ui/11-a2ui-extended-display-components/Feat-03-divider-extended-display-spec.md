# 特性规格

> Func-07-04-11-Feat-03 Divider 扩展组件：固化 A2UI 扩展展示组件 Divider 的契约——分割线方向 `styles.vertical`、厚度 `styles.strokeWidth`（含 vp/px/% 单位）与主题模式颜色 `styles.color`。基准实现：`@arkui-genius/genui`（A2UIRender，生产 ArkTS Custom 组件 `ExtendedDivider`，另有 `#ifdef TDD_BUILD` 的 C++ 镜像 `ExtendedDividerComponent`/`ExtendedDividerTheme`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Divider 扩展组件 |
| 特性编号 | Func-07-04-11-Feat-03 |
| 优先级 | P1 |
| 目标版本 | A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog` + 起始 API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 沿用 07-04-11 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/11-a2ui-extended-display-components/design.md` | Baselined |
| 组件实现（ArkTS，生产） | `genui/src/main/ets/core/components/extended/ExtendedDivider.ets` | — |
| 组件实现（C++，TDD 镜像） | `genui/src/main/cpp/components/extended/ExtendedDividerComponent.cpp` | — |
| 主题映射（C++，TDD 镜像） | `genui/src/main/cpp/components/extended/ExtendedDividerTheme.cpp` | — |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 协议 Schema | `genui/src/main/resources/rawfile/schema/Extended/components/ExtendedDivider.json` | — |
| 文档参考 | `render_docs/reference/extended-components/divider.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 分割线厚度（strokeWidth）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.strokeWidth` 声明分割线厚度（支持单位）,
**以便** 精确控制分割线的视觉粗细。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `styles.strokeWidth` 为数字（如 `2`） THEN 按 vp 处理（生产解析 `resolveStrokeWidthLiteral`，`ExtendedDivider.ets:143-145`；C++ `ParseDividerStrokeWidth`，`StyleApplyUtilsLayout.cpp:95-102`） | 正常 |
| AC-1.2 | WHEN `styles.strokeWidth` 为带单位字符串（如 `"2vp"`/`"1px"`/`"20%"`） THEN 解析对应数值与单位（`resolveStrokeWidthString`，`ExtendedDivider.ets:105-137`；C++ `ParseStrokeWidthTokenInternal` 经 `ParseDividerStrokeWidth`，`StyleApplyUtilsLayout.cpp:90-108`） | 正常 |
| AC-1.3 | WHEN `styles.strokeWidth` 缺省 THEN 生产 ArkTS 回落默认 `'0.29vp'`（`DEFAULT_STROKE_WIDTH`，`ExtendedDivider.ets:40,228`）；schema/C++ 镜像声明 `"1px"`（`ExtendedDivider.json:37`、`ExtendedDividerComponent.cpp:32,286`） | 边界 |
| AC-1.4 | WHEN `styles.strokeWidth` 非法（负数/非有限/非法单位/非 string 非 number 对象） THEN 回落默认并上报 `TYPE_MISMATCH`/`INVALID_VALUE`（`resolveStrokeWidth`，`ExtendedDivider.ets:209-229`；C++ `ApplyStrokeWidthPrivateValue`，`ExtendedDividerComponent.cpp:376-400`） | 异常 |
| AC-1.5 | WHEN `strokeWidth` 单位为 `%` 且为厚度方向 THEN C++ 镜像按百分比维度设置（`ApplyThickness`，`ExtendedDividerComponent.cpp:447-461`） | 边界 |
| AC-1.6 | WHEN `strokeWidth` 单位为 `px` THEN C++ 镜像经密度换算 `ConvertPxToVp`（`ExtendedDividerComponent.cpp:455-458`） | 边界 |

### US-2: 分割线方向（vertical）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `styles.vertical` 声明分割线方向,
**以便** 在水平/垂直内容块之间渲染合适方向的分割线。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `styles.vertical` 为 `false` THEN 渲染水平分割线（`Divider().vertical(false)`，`ExtendedDivider.ets:321-325`） | 正常 |
| AC-2.2 | WHEN `styles.vertical` 为 `true` THEN 渲染垂直分割线（`Divider().vertical(true)`，`ExtendedDivider.ets:321-325`） | 正常 |
| AC-2.3 | WHEN `styles.vertical` 缺省或非法 THEN 回落默认 `false`（`resolveVertical`，`ExtendedDivider.ets:231-251`；`DEFAULT_VERTICAL`，`ExtendedDividerComponent.cpp:33`） | 边界 |

### US-3: 主题模式颜色（color）

**作为** 生成式 UI 宿主开发者,
**我想要** Divider 颜色随深色/浅色模式切换,
**以便** 分割线在两种主题下均清晰可见。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `styles.color` 为合法十六进制颜色 THEN 应用该颜色（`resolveColor`，`ExtendedDivider.ets:253-272`；C++ `SetColor`，`ExtendedDividerComponent.cpp:339-350`） | 正常 |
| AC-3.2 | WHEN `styles.color` 缺省或非法且 `ThemeMode==DARK` THEN 回落 `0x33FFFFFF`（`resolveDividerColorByThemeMode`，`CustomDivider.ets:36-41`；`ExtendedDividerTheme.cpp:24,49-51`） | 边界 |
| AC-3.3 | WHEN `styles.color` 缺省或非法且非 DARK（浅色/未定义） THEN 回落 `0x33000000`（`CustomDivider.ets:36-41`、`ExtendedDividerTheme.cpp:23,49-51`） | 边界 |
| AC-3.4 | WHEN 显式设置合法颜色后主题切换 THEN 颜色不随主题改变（`OnConfigChange` 中 `useDefaultColor_` 仅默认色时刷新，`ExtendedDividerComponent.cpp:490-498`） | 边界 |

### US-4: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** Divider 扩展组件以 `component:"Divider"` 注册为扩展目录 Custom 组件,
**以便** DSL 中的扩展 Divider 组件被正确路由到 ArkTS Custom 渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 目录注册 THEN `createExtendedDividerDefinition()` 以 `type='Divider'` 加载 `schema/Extended/components/ExtendedDivider.json`（`ExtendedDivider.ets:418-426`） | 正常 |
| AC-4.2 | WHEN 目录项 THEN Divider 不在 `EXTENDED_NATIVE_COMPONENT_NAMES`，故走 Custom 定义（`A2UIExtendedComponents.ets:28-45,168-183`） | 正常 |
| AC-4.3 | WHEN TDD 构建 THEN C++ `ExtendedDividerComponent` 经 `#ifdef TDD_BUILD` 注册（`ExtendedComponentFactory.cpp:118-120`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2,R-3 | T-3 | ArkTS 单测（`resolveStrokeWidth`）+ C++ UT（TDD 镜像） | `ExtendedDivider.ets:105-229`、`ExtendedDividerComponent.cpp:315-332,447-461` |
| AC-2.1,AC-2.2,AC-2.3 | R-4,R-5 | T-3 | ArkTS 单测 | `ExtendedDivider.ets:231-251,321-325` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-6,R-7 | T-3 | ArkTS 单测 + C++ UT（TDD 镜像） | `CustomDivider.ets:36-41`、`ExtendedDividerTheme.cpp:47-51` |
| AC-4.1,AC-4.2,AC-4.3 | R-8 | T-3 | 静态比对 | `ExtendedDivider.ets:418-426`、`A2UIExtendedComponents.ets:28-45`、`ExtendedComponentFactory.cpp:118-120` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `styles.strokeWidth` 数字/带单位字符串 | 解析为数值 + 单位（vp/px/%） | 数字按 vp；px 经密度换算 | AC-1.1,AC-1.2,AC-1.5,AC-1.6 |
| R-2 | 边界 | `styles.strokeWidth` 缺省 | 回落默认（生产 ArkTS `0.29vp`；schema/C++ 镜像 `1px`） | 三处默认值不一致（RISK-1） | AC-1.3 |
| R-3 | 异常 | `styles.strokeWidth` 非法 | 回落默认 + `TYPE_MISMATCH`/`INVALID_VALUE` 告警 | 非负数、有限值 | AC-1.4 |
| R-4 | 行为 | `styles.vertical` true/false | 渲染对应方向分割线 | 布尔映射 | AC-2.1,AC-2.2 |
| R-5 | 边界 | `styles.vertical` 缺省/非法 | 回落 `false`（水平） | 默认 false | AC-2.3 |
| R-6 | 行为 | `styles.color` 合法 hex | 应用该颜色（`useDefaultColor_=false`） | 十六进制 | AC-3.1 |
| R-7 | 边界 | `styles.color` 缺省/非法 | 回落 `0x33FFFFFF`（DARK）/`0x33000000`（浅色） | 随 ThemeMode 分流 | AC-3.2,AC-3.3 |
| R-8 | 行为 | 目录注册/类型 | 类型 `"Divider"`，Custom 组件（生产）+ TDD C++ 镜像 | 不在 native 名列表 | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 strokeWidth | ArkTS 单测 + C++ UT | 单位解析、px→vp、%比例、非法回落 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 vertical | ArkTS 单测 | 方向映射、缺省/非法回落 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 主题颜色 | ArkTS/C++ 单测 | DARK/浅色常量、显式色不随主题 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 目录 | 静态比对 | Custom 定义、TDD 工厂注册 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `createExtendedDividerDefinition()` | 既有 | Divider 扩展目录注册 | 不直接暴露给宿主 | AC-4.1 |
| `CatalogItem`（`A2UIExtendedComponents.allA2UIExtendedComponents()` 内 Divider 项） | 既有 | 扩展目录 Custom 项 | 不直接暴露给宿主 | AC-4.2 |

> d.ts 位置：`genui/src/main/ets/core/components/extended/ExtendedDivider.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**Divider 扩展组件特有样式（descriptor 属性契约，非函数 API）**

| 属性 | 值 |
|------|-----|
| 属性声明 | 生产 ArkTS `resolveExtendedDividerStyles`（`ExtendedDivider.ets:274-301`）；TDD C++ `ExtendedDividerComponent::GetPrivatePropertyDeclaration`（`ExtendedDividerComponent.cpp:276-313`） |
| 必填属性 | 无（`ExtendedDivider.json:15-17` 仅 required `component`） |
| 开放范围 | 协议 DSL（无 Public/System API） |
| 错误码 | 非法 strokeWidth/vertical/color 走 schema warning（`TYPE_MISMATCH`/`INVALID_VALUE`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| styles.strokeWidth | string\|number | 否 | 生产 `0.29vp`（schema/C++ `1px`） | 非负有限；单位 vp/px/% |
| styles.vertical | ExtendedDynamicBoolean | 否 | `false` | true/false，非法回落 false |
| styles.color | ExtendedDynamicString | 否 | `0x33000000`/`0x33FFFFFF` | 十六进制；随 ThemeMode 分流 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `styles.strokeWidth:"2vp"` | 厚度 2vp | AC-1.2 |
| 2 | `styles.strokeWidth:2` | 厚度 2（vp） | AC-1.1 |
| 3 | `styles.strokeWidth` 缺省 | 生产回落 `0.29vp` | AC-1.3 |
| 4 | `styles.vertical:true` | 垂直分割线 | AC-2.2 |
| 5 | `styles.vertical` 缺省/非法 | 水平分割线 | AC-2.3 |
| 6 | DARK 主题且 color 缺省 | 颜色 `0x33FFFFFF` | AC-3.2 |
| 7 | 浅色主题且 color 缺省 | 颜色 `0x33000000` | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 catalog `ohos.a2ui.extended.catalog`，起始 API Version 20。
- **API 版本号策略:** 协议 schema 版本由 `SchemaResourceLoader.loadSchema('schema/Extended/components/ExtendedDivider.json')` 声明（`ExtendedDivider.ets:419-421`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| Custom 组件路径 | 生产走 ArkTS `ExtendedDivider`（`Divider()` 链式属性），无 C++ 生产实现 | AC-4.1,AC-4.2 |
| 双实现并存 | C++ `ExtendedDividerComponent` 仅 `#ifdef TDD_BUILD` 镜像，供 UT 覆盖，生产不编译 | AC-4.3 |
| strokeWidth 单位换算 | px 经密度换算、% 按厚度方向维度设置 | AC-1.5,AC-1.6 |
| 主题颜色双端 | 生产 ArkTS 用 `resolveDividerColorByThemeMode`；C++ 镜像用 `ExtendedDividerTheme`，常量需双端同步 | AC-3.2,AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 strokeWidth/vertical/color 不抛异常，统一回落默认 | ArkTS 单测 + C++ UT | `ExtendedDivider.ets:209-272`、`ExtendedDividerComponent.cpp:376-415` |
| 可测试性 | `resolveExtendedDividerStyles` 纯函数可单测；C++ 镜像暴露 TDD 接口 | ArkTS/C++ 单测 | `ExtendedDivider.ets:274-301` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 分割线颜色/方向/厚度与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityLabel`/`accessibilityDescription` 透传（`ExtendedDivider.ets:332-333`） | AC-2.1,AC-2.2,AC-2.3 |
| 大字体 | 否 | 分割线无文本，不涉及 | — |
| 深色模式 | 是 | 分割线颜色按 `ThemeMode` 分流 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 catalog 绑定 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 扩展协议 Divider 语义对齐 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Divider 扩展组件
  作为 生成式 UI 宿主开发者
  我想要 通过 styles.strokeWidth/vertical/color 声明分割线
  以便 渲染引擎正确显示分割线

  Scenario: 方向解析
    Given DSL 组件为 {"component":"Divider","id":"d1","styles":{"vertical":true}}
    When 解析分割线样式
    Then 渲染垂直分割线（vertical=true）

  Scenario Outline: 方向回落
    Given DSL 组件为 {"component":"Divider","id":"d1","styles":{"vertical":<vertical>}}
    When 解析分割线样式
    Then 方向为 <direction>

    Examples:
      | vertical | direction |
      | true     | vertical  |
      | "bad"    | horizontal|
      | (缺省)   | horizontal|
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Divider 扩展特有样式 strokeWidth/vertical/color；通用属性归通用样式域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedDivider resolveExtendedDividerStyles resolveStrokeWidth resolveVertical resolveColor"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedDividerComponent SetStrokeWidth ParseDividerStrokeWidth ApplyThickness ConvertPxToVp"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedDividerTheme GetDefaultColor DIVIDER_LIGHT_COLOR DIVIDER_DARK_COLOR resolveDividerColorByThemeMode"
```

**关键文档：** `genui/src/main/ets/core/components/extended/ExtendedDivider.ets`、`genui/src/main/cpp/components/extended/ExtendedDividerComponent.cpp`、`genui/src/main/cpp/components/extended/ExtendedDividerTheme.cpp`、`genui/src/main/resources/rawfile/schema/Extended/components/ExtendedDivider.json`