# 特性规格

> Func-07-04-05-Feat-01 Card 容器：固化 A2UI 标准协议 Card 组件的行为——以原生 `COLUMN` 节点渲染（`CardComponent.cpp:24`）、`CardTheme` 默认样式（圆角 8/阴影 OUTER_DEFAULT_LG/内边距 16/边框宽 1，背景与边框色按 `colorMode` 深/浅双语）、`child` 单子引用、可选 `width`/`height` 覆盖、主题上下文变化（深色模式）时重放默认样式。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Card 容器 |
| 特性编号 | Func-07-04-05-Feat-01 |
| 优先级 | P0 |
| 目标版本 | API Version 20；A2UI 标准协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-05 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/05-a2ui-standard-container-components/design.md` | Baselined |
| Card 类目（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UICard.ets` | — |
| Card 组件（C++） | `genui/src/main/cpp/components/A2UI/card/CardComponent.cpp/.h` | — |
| Card 主题（C++） | `genui/src/main/cpp/components/A2UI/card/CardTheme.cpp/.h` | — |
| 组件工厂（C++） | `genui/src/main/cpp/components/NativeComponentFactory.cpp`、`theme/ThemeFactory.cpp` | — |
| Card 文档（Docs） | `reference/standard-components/card.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Card 类目注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `component: "Card"` 描述符并注册 Card 组件,
**以便** 通过标准协议声明卡片容器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ArkTS 类目项声明类型为 `Card` THEN `A2UICard.type` 为 `"Card"` 且 `asCatalogItem()` 经 `CatalogItem.forComponent` 注册并 `markCategory(A2UI_STANDARD).markInnerNative(true)`（`A2UICard.ets:24-35`） | 正常 |
| AC-1.2 | WHEN `A2UICard.asCatalogItem()` 被调用 THEN schemaProvider 加载 `components/Card.json`（`A2UICard.ets:26-28`） | 正常 |
| AC-1.3 | WHEN native 组件工厂收到 `"Card"` THEN 创建 `CardComponent`（`NativeComponentFactory.cpp:39`）；theme 工厂创建 `CardTheme`（`ThemeFactory.cpp:41`） | 正常 |
| AC-1.4 | WHEN `CardComponent::GetType()` 被调用 THEN 返回 `"Card"`（`CardComponent.cpp:77-80`） | 正常 |

### US-2: Card 原生渲染节点

**作为** 生成式 UI 宿主开发者,
**我想要** Card 复用原生布局节点,
**以便** 获得与 Column 一致的布局语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `CardComponent` 构造 THEN 以 `ArkUINodeApiAdapter::CreateNode(A2UINodeType::COLUMN)` 创建原生节点（`CardComponent.cpp:24`） | 正常 |
| AC-2.2 | WHEN Card 描述符含 `child` THEN `CollectChildListDescriptor` 经 `ChildListParser::ParseChild` 解析单子（`CardComponent.cpp:46-49`） | 正常 |
| AC-2.3 | WHEN Card 描述符含 `width`/`height` THEN `ApplyPrivateAttributes` 调用 `SetWidth`/`SetHeight` 覆盖默认（`CardComponent.cpp:63-68`） | 正常 |
| AC-2.4 | WHEN Card 描述符含 `width`/`height` 之外的未知附加键 THEN `IsKnownAdditionalDescriptorKey` 仅认可 `width`/`height`（`CardComponent.cpp:71-75`） | 边界 |

### US-3: Card 默认主题样式

**作为** 生成式 UI 宿主开发者,
**我想要** Card 有一套稳定的默认视觉样式,
**以便** 无需在 DSL 中显式指定样式即呈现卡片外观。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `CardTheme` 初始化 THEN 默认圆角 `8.0F`（`CardTheme.cpp:26`）、阴影 `OUTER_DEFAULT_LG`（`:27`）、内边距 `16.0F`（`:28`）、边框宽 `1.0F`（`:29`） | 正常 |
| AC-3.2 | WHEN `ApplyThemeDefaults` 被调用 THEN 依次下发 `SetBorderRadius`/`SetBackgroundColor`/`SetShadow`/`SetPadding`/`SetBorderWidth`/`SetBorderColor`（`CardComponent.cpp:105-114`） | 正常 |
| AC-3.3 | WHEN `ApplyPrivateAttributes` 中 `GetTheme()` 返回 null THEN 打 `LOG_ERROR` 并直接返回、不下发任何样式（`CardComponent.cpp:53-60`） | 异常 |
| AC-3.4 | WHEN `ApplyThemeDefaults` 下发内边距 THEN `SetPadding(padding, padding, padding, padding)` 四边等值（`CardComponent.cpp:110`） | 边界 |

### US-4: Card 深色模式双语

**作为** 生成式 UI 宿主开发者,
**我想要** Card 背景与边框随深色模式自动切换,
**以便** 深色环境下具备合理对比度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `colorMode==LIGHT` THEN `ResolveBackgroundColor` 返回 `0xFFFFFFFF`、`ResolveBorderColor` 返回 `0xFFE0E0E0`（`CardTheme.cpp:92-98,100-106`） | 正常 |
| AC-4.2 | WHEN `colorMode==DARK`（非 LIGHT） THEN `ResolveBackgroundColor` 返回 `0xFF1A1A1A`、`ResolveBorderColor` 返回 `0xFF333333`（`CardTheme.cpp:92-98,100-106`） | 正常 |
| AC-4.3 | WHEN 主题上下文变化触发 `OnConfigChange` THEN `CardComponent` 重放 `ApplyThemeDefaults`（`CardComponent.cpp:116-128`） | 正常 |
| AC-4.4 | WHEN `ResolveShadowStyle` 被调用 THEN 恒定返回 `DEFAULT_CARD_SHADOW_STYLE`，不随 `colorMode`/`breakpoint` 变化（`CardTheme.cpp:108-111`） | 边界 |

### US-5: Card child 引用约束

**作为** 生成式 UI 宿主开发者,
**我想要** 明确 Card 的 child 约束,
**以便** 正确声明卡片内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Card 为原生标准协议节点 THEN `GetRequiredStructuralPropertyKeysForComponentType` 要求 `{"child"}`（`SurfaceSlotSchemaValidation.cpp:62`） | 正常 |
| AC-5.2 | WHEN child 传递多个 id 或不存在的 id THEN 不渲染卡片内容（`card.md:28`） | 边界 |
| AC-5.3 | WHEN 需显示多个元素 THEN 必须采用容器组件包含并传容器 id（`card.md:27`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-1 | ArkTS/静态比对：类目项 + 工厂注册 | `A2UICard.ets:24-35`、`NativeComponentFactory.cpp:39` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2,R-6 | T-1 | C++ UT：节点类型 + child/width/height | `CardComponent.cpp:24,46-75` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-1 | C++ UT：默认常量 + 下发序列 | `CardTheme.cpp:26-29`、`CardComponent.cpp:105-114` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-1 | C++ UT：colorMode 双语 + OnConfigChange | `CardTheme.cpp:92-111`、`CardComponent.cpp:116-128` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-1 | 静态比对 + 文档交叉 | `SurfaceSlotSchemaValidation.cpp:62`、`card.md:27-28` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor `component=="Card"` | 创建 CardComponent 并经 ArkTS 类目注册 | innerNative=true | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | Card 构造 | 原生 COLUMN 节点 | 复用 Column 布局语义 | AC-2.1 |
| R-3 | 行为 | ApplyThemeDefaults 调用 | 下发圆角/背景/阴影/内边距/边框宽/边框色 | 默认值见 `CardTheme.cpp:26-29` | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 边界 | colorMode 为 LIGHT/DARK | 背景与边框双语切换 | 阴影/圆角/内边距/边框宽不随 mode | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-5 | 边界 | child 缺失/多 id/不存在 id | 不渲染卡片内容 | child 必填单 id | AC-5.1,AC-5.2,AC-5.3 |
| R-6 | 边界 | width/height 存在 | 覆盖主题默认尺寸 | 仅 width/height 为附加白名单键 | AC-2.3,AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 类目/工厂 | 静态比对 | 类型、innerNative、工厂映射 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 渲染节点 | C++ UT | COLUMN 节点、child/width/height |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 默认样式 | C++ UT | 默认常量、下发序列、null theme |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 深色双语 | C++ UT | LIGHT/DARK 双语、OnConfigChange 重放 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 child 约束 | 静态比对 | schema 必填 + 文档约束 |

## API 变更分析

> 存量补录，无新增/变更公开 ArkTS/C-API。本节列出受影响组件协议。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Card` 组件协议（`component`/`child`/`width`/`height`） | 既有 | 标准容器声明 | 单 child id，多元素用容器包一层 | AC-5.1,AC-5.2,AC-5.3 |
| `CardComponent`（内部 native 类） | 既有 | native 渲染 | 不直接暴露给宿主 | AC-1.3,AC-2.1 |

> Schema 位置：`components/Card.json`（经 `A2UICard.ets:27` 加载）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`CardComponent::ApplyPrivateAttributes(descriptor)`（内部，`CardComponent.cpp:51`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ApplyPrivateAttributes(const JsonValue& descriptor)` |
| 返回值 | `void` |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（theme null 打 LOG_ERROR 后返回） |
| 关联 AC | AC-2.3,AC-3.3 |

**`CardComponent::ApplyThemeDefaults(styleMetrics)`（`CardComponent.cpp:105`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ApplyThemeDefaults(const CardTheme::StyleMetrics&)` |
| 返回值 | `void` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.2,AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| child | string | 是（schema `{"child"}`） | `""` | 单个已存在组件 id |
| width | number | 否 | 主题默认（无显式宽度） | 正值 |
| height | number | 否 | 主题默认 | 正值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | descriptor 含 child | 解析单子并渲染 | AC-2.2 |
| 2 | descriptor 含 width/height | SetWidth/SetHeight 覆盖 | AC-2.3 |
| 3 | theme 为 null | LOG_ERROR 并返回 | AC-3.3 |
| 4 | colorMode LIGHT/DARK | 背景/边框双语 | AC-4.1,AC-4.2 |
| 5 | 主题上下文变化 | 重放默认样式 | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API Version 20（`card.md:5`）。
- **API 版本号策略:** 组件协议经 JSON Schema 约束；无 `@since` 标注差异。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| innerNative 渲染 | Card 必须走 native 渲染（非 ArkTS 自定义组件） | AC-1.1 |
| 单 child | Card 仅支持单 child id | AC-5.1,AC-5.2,AC-5.3 |
| 主题兜底 | 样式由 CardTheme 默认值兜底 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | theme null 不崩溃、打 LOG_ERROR 降级 | C++ UT | `CardComponent.cpp:53-60` |
| 性能 | 主题经 `weak_ptr` 缓存避免重复动态转换 | C++ UT | `CardComponent.cpp:82-103` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 固定默认样式，不按 breakpoint 差异化 | ohosTest | `CardTheme.cpp:85-90` |
| 平板 | 无差异 | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异 | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 是 | 背景/边框双语（colorMode） | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version 20 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 标准组件协议 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Card 容器
  作为 生成式 UI 宿主开发者
  我想要 通过 Card 组件协议渲染卡片
  以便 获得统一的卡片外观与单子内容

  Scenario: 声明 Card 并渲染单子内容
    Given DSL 含 {"component":"Card","id":"c1","child":"t1"} 与 Text("t1")
    When 引擎处理 updateComponents
    Then 创建 CardComponent（COLUMN 节点）并渲染 child 内容

  Scenario: Card 默认样式下发
    Given Card 描述符未显式指定样式
    When CardComponent 应用私有属性
    Then 下发圆角 8/阴影 OUTER_DEFAULT_LG/内边距 16/边框宽 1

  Scenario Outline: 深色模式双语
    Given 主题 colorMode 为 <mode>
    When CardTheme 解析外观
    Then 背景色 <bg> 边框色 <border>

    Examples:
      | mode  | bg          | border      |
      | LIGHT | 0xFFFFFFFF  | 0xFFE0E0E0  |
      | DARK  | 0xFF1A1A1A  | 0xFF333333  |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Card 容器特有语义；通用属性/主题基础归其他功能域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CardComponent COLUMN 节点 CardTheme 默认样式 ApplyThemeDefaults OnConfigChange"
  - repo: "GenerativeUI/A2UIRender"
    query: "CardTheme DEFAULT_CARD_BORDER_RADIUS SHADOW_STYLE PADDING BORDER_WIDTH colorMode 双语"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeComponentFactory Card 注册 A2UICard asCatalogItem markInnerNative"
```

**关键文档：** `genui/src/main/cpp/components/A2UI/card/CardComponent.cpp`、`genui/src/main/cpp/components/A2UI/card/CardTheme.cpp`、`genui/src/main/ets/core/components/A2UI/A2UICard.ets`
