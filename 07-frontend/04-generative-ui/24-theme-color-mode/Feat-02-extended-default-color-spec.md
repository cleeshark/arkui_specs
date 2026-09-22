# 特性规格

> Func-07-04-24-Feat-02 扩展组件默认深浅色：固化鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）下扩展组件的默认浅/深色硬编码值——公共阴影色（`ExtendedCommonTheme`）、文本字体/装饰线色（`ExtendedTextTheme`）、分割线色（`ExtendedDividerTheme`）、进度条按类型取色（`ExtendedProgressTheme`），以及 Grid/List 主题类的断点驱动成员；并固化扩展主题「组件直接栈构造、绕过 ThemeFactory」的消费方式。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 扩展组件默认深浅色 |
| 特性编号 | Func-07-04-24-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）；宿主集成 API Version ≥ 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性承接 Func-07-04-24 design.md（Feat-01 已建立基线），固化扩展组件默认深浅色 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/24-theme-color-mode/design.md` | Baselined |
| 公共主题（C++） | `genui/src/main/cpp/components/extended/ExtendedCommonTheme.cpp` | — |
| 文本主题（C++） | `genui/src/main/cpp/components/extended/ExtendedTextTheme.cpp` | — |
| 分割线主题（C++） | `genui/src/main/cpp/components/extended/ExtendedDividerTheme.cpp` | — |
| 进度条主题（C++） | `genui/src/main/cpp/components/extended/ExtendedProgressTheme.cpp` | — |
| Grid 主题（C++） | `genui/src/main/cpp/components/extended/ExtendedGridTheme.cpp` | — |
| List 主题（C++） | `genui/src/main/cpp/components/extended/ExtendedListTheme.cpp` | — |
| 组件基类（C++） | `genui/src/main/cpp/components/extended/ExtendedComponent.cpp` | — |
| 主题工厂（C++） | `genui/src/main/cpp/theme/ThemeFactory.cpp` | — |
| 扩展组件默认色（Docs） | `render_docs/concepts/extension-color-mode.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 公共阴影默认色

**作为** 生成式 UI 宿主开发者,
**我想要** 扩展组件在未显式设置阴影色时使用默认阴影色,
**以便** 深浅色模式下阴影表现一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 阴影色浅色默认值 THEN 为 `0xFF000000`（`ExtendedCommonTheme.cpp:23`） | 正常 |
| AC-1.2 | WHEN 阴影色深色默认值 THEN 为 `0xFF000000`（`ExtendedCommonTheme.cpp:24`） | 正常 |
| AC-1.3 | WHEN `context_.hasBrandColor` 为 true THEN `GetShadowColor()` 返回 `brandColor`（`ExtendedCommonTheme.cpp:49-51`） | 正常 |
| AC-1.4 | WHEN 无品牌色 THEN `GetShadowColor()` 按 `colorMode` 返回深/浅默认值（`ExtendedCommonTheme.cpp:52-53`） | 正常 |

### US-2: Text 默认字体与装饰线色

**作为** 生成式 UI 宿主开发者,
**我想要** 扩展 Text 组件在未显式设置颜色时使用默认深浅色,
**以便** 文本在深浅色模式下可读。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 字体色浅色默认值 THEN 为 `0xE5000000`（`ExtendedTextTheme.cpp:23`） | 正常 |
| AC-2.2 | WHEN 字体色深色默认值 THEN 为 `0x99FFFFFF`（`ExtendedTextTheme.cpp:24`） | 正常 |
| AC-2.3 | WHEN 无显式 fontColor THEN `GetDefaultFontColor()` 按 `colorMode` 返回深/浅值（`ExtendedTextTheme.cpp:48-52`） | 正常 |
| AC-2.4 | WHEN 装饰线色浅色默认值 THEN 为 `0xFF000000`（`ExtendedTextTheme.cpp:25`） | 正常 |
| AC-2.5 | WHEN 装饰线色深色默认值 THEN 复用深色字体色 `0x99FFFFFF`（`ExtendedTextTheme.cpp:54-58`） | 边界 |
| AC-2.6 | WHEN 组件渲染默认字体色 THEN 经 `GetDefaultFontColor()` 消费（`ExtendedTextComponent.cpp:656-657`、`:827-835`） | 正常 |

### US-3: Divider 默认颜色

**作为** 生成式 UI 宿主开发者,
**我想要** 扩展 Divider 组件在未显式设置颜色时使用默认分割线色,
**以便** 分割线在深浅色模式下适配。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 分割线浅色默认值 THEN 为 `0x33000000`（`ExtendedDividerTheme.cpp:23`） | 正常 |
| AC-3.2 | WHEN 分割线深色默认值 THEN 为 `0x33FFFFFF`（`ExtendedDividerTheme.cpp:24`） | 正常 |
| AC-3.3 | WHEN 无显式 color THEN `GetDefaultColor()` 按 `colorMode` 返回深/浅值（`ExtendedDividerTheme.cpp:47-51`） | 正常 |
| AC-3.4 | WHEN 组件渲染默认色 THEN 经 `GetDefaultColor()` 消费（`ExtendedDividerComponent.cpp:359-360`、`:495-496`） | 正常 |

### US-4: Progress 按类型默认颜色

**作为** 生成式 UI 宿主开发者,
**我想要** 扩展 Progress 组件按样式类型使用对应默认色,
**以便** 线性/月蚀/刻度环样式在深浅色下正确着色。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 线性进度浅色默认值 THEN 为 `0xFF0A59F7`（`ExtendedProgressTheme.cpp:23`） | 正常 |
| AC-4.2 | WHEN 线性进度深色默认值 THEN 为 `0xFF317AF7`（`ExtendedProgressTheme.cpp:24`） | 正常 |
| AC-4.3 | WHEN 月蚀浅色默认值 THEN 为 `0x19000000`；深色为 `0x19FFFFFF`（`ExtendedProgressTheme.cpp:25-26`） | 正常 |
| AC-4.4 | WHEN 刻度环浅色默认值 THEN 为 `0x99000000`；深色为 `0x99FFFFFF`（`ExtendedProgressTheme.cpp:27-28`） | 正常 |
| AC-4.5 | WHEN progressType 非 0/2/3 THEN 回落 `0xFFFF7DFF`（`ExtendedProgressTheme.cpp:29,71`） | 边界 |
| AC-4.6 | WHEN 类型常量 THEN `DEFAULT=0`/`ECLIPSE=2`/`SCALE_RING=3`（`ExtendedProgressTheme.cpp:31-33`） | 正常 |
| AC-4.7 | WHEN 组件在 `useDefaultColor_` 为 true 时 `OnConfigChange` THEN 重新解析默认色（`ExtendedProgressComponent.cpp:115-125`） | 正常 |
| AC-4.8 | WHEN 组件消费默认色 THEN 经 `GetDefaultColorByType(progressType_)`（`ExtendedProgressComponent.cpp:120-121`） | 正常 |

### US-5: Grid/List 主题断点成员

**作为** 生成式 UI 宿主开发者,
**我想要** 扩展 Grid/List 主题类按断点提供列模板/行数,
**以便** 一多部署的默认布局生效（断点语义归 07-04-23）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Grid 断点为 XS/SM THEN 列模板 `"1fr 1fr"`；MD → `"1fr 1fr 1fr"`；LG/XL → `"1fr 1fr 1fr 1fr 1fr"`（`ExtendedGridTheme.cpp:24-26,54-69`） | 正常 |
| AC-5.2 | WHEN List 断点为 XS/SM THEN 行数 1；MD → 2；LG/XL → 3（`ExtendedListTheme.cpp:24-26,54-69`） | 正常 |
| AC-5.3 | WHEN Grid 断点为未知值 THEN 回落两列模板（`ExtendedGridTheme.cpp:66-68`） | 边界 |
| AC-5.4 | WHEN 组件消费列模板/行数 THEN 经 `GetColumnsTemplate()`/`GetLanes()`（`ExtendedGridComponent.cpp:680-681`、`ExtendedListComponent.cpp:591-592`） | 正常 |

### US-6: 扩展主题构造与消费方式

**作为** 生成式 UI 宿主开发者,
**我想要** 理解扩展组件默认色的来源机制,
**以便** 主题变更时正确触发重渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 扩展组件读取默认色 THEN 直接以当前 `ThemeContext` 栈构造 `Extended*Theme`（如 `ExtendedTextComponent.cpp:656`） | 正常 |
| AC-6.2 | WHEN `ExtendedTextComponent::GetType()` THEN 返回 `"Text"`（`ExtendedTextComponent.cpp:249-251`） | 正常 |
| AC-6.3 | WHEN `ThemeFactory::CreateTheme` 收到扩展类型 THEN 注册表中仅 `"Grid"→ExtendedGridTheme`，Text/List/Divider/Progress/Common 未注册（`ThemeFactory.cpp:38-52`） | 边界 |
| AC-6.4 | WHEN `GetCommonTheme()` 缓存未命中 THEN 经 `Component::GetTheme()` 回退并 `dynamic_pointer_cast` 到 `ExtendedCommonTheme`（`ExtendedComponent.cpp:1234-1252`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-2 | C++ UT：`GetShadowColor` | `ExtendedCommonTheme.cpp:23-54` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 | R-2 | T-2 | C++ UT：`GetDefaultFontColor`/`GetDefaultDecorationColor` | `ExtendedTextTheme.cpp:23-58`、`ExtendedTextComponent.cpp:656-835` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-2 | C++ UT：`GetDefaultColor` | `ExtendedDividerTheme.cpp:23-51`、`ExtendedDividerComponent.cpp:359-496` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8 | R-4,R-5 | T-2 | C++ UT：`GetDefaultColorByType` | `ExtendedProgressTheme.cpp:23-72`、`ExtendedProgressComponent.cpp:115-125` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-6 | T-2 | C++ UT：`GetColumnsTemplate`/`GetLanes` | `ExtendedGridTheme.cpp:24-69`、`ExtendedListTheme.cpp:24-69` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-7 | T-2 | 静态比对：ThemeFactory vs 组件 GetType | `ThemeFactory.cpp:38-52`、`ExtendedTextComponent.cpp:249-251`、`ExtendedComponent.cpp:1234-1252` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 阴影色未显式设置 | 有 brandColor 用 brandColor，否则按 colorMode 用默认 `0xFF000000` | 深浅色默认值相同 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | Text 未显式设置 fontColor/decoration.color | 字体色 `0xE5000000`/`0x99FFFFFF`；装饰线色 `0xFF000000`/`0x99FFFFFF` | 深色装饰线复用深色字体色 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| R-3 | 行为 | Divider 未显式设置 color | 按 colorMode 用 `0x33000000`/`0x33FFFFFF` | 半透明黑/白 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | Progress 按 progressType 取默认色 | linear/eclipse/scalering 各自浅深默认值 | 类型常量 0/2/3 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |
| R-5 | 边界 | progressType 非法 | 回落 `0xFFFF7DFF` | 不区分深浅色 | AC-4.5 |
| R-6 | 行为 | Grid/List 按断点取列模板/行数 | XS/SM、MD、LG/XL 三档 | 未知断点回落最小档 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-7 | 行为 | 扩展组件读取默认色 | 组件直接栈构造 `Extended*Theme`，不经 ThemeFactory | ThemeFactory 仅注册 Grid | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 阴影色 | C++ UT | brandColor 优先 + 深浅同值 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 文本色 | C++ UT | 字体/装饰线浅深映射 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 分割线色 | C++ UT | 半透明浅深映射 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8 进度色 | C++ UT | 三类型 + 回落 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 Grid/List 断点 | C++ UT | 断点三档 + 回落 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 构造方式 | 静态比对 | ThemeFactory 注册表 vs 组件消费 |

## API 变更分析

> 存量补录，无新增/变更公开 API。扩展组件默认色由 C++ 内部 `Extended*Theme` 提供，不经 NAPI 暴露。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `Extended*Theme::GetDefault*`（内部 C++ 方法） | 既有 | 扩展组件默认色消费 | 不对外暴露 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

> 无 d.ts 公开契约变更。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ExtendedCommonTheme::GetShadowColor()`（内部 C++，`ExtendedCommonTheme.cpp:47`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `uint32_t GetShadowColor() const` |
| 返回值 | `uint32_t` — brandColor 或按 colorMode 的默认阴影色 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.3,AC-1.4 |

**`ExtendedTextTheme::GetDefaultFontColor()` / `GetDefaultDecorationColor()`（内部 C++，`ExtendedTextTheme.cpp:48,54`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `uint32_t GetDefaultFontColor() const` / `uint32_t GetDefaultDecorationColor() const` |
| 返回值 | `uint32_t` — 按 colorMode 的默认字体/装饰线色 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.3,AC-2.5 |

**`ExtendedProgressTheme::GetDefaultColorByType(progressType)`（内部 C++，`ExtendedProgressTheme.cpp:56`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `uint32_t GetDefaultColorByType(int32_t progressType) const` |
| 返回值 | `uint32_t` — 按 progressType 与 colorMode 的默认色；未知类型回落 `0xFFFF7DFF` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| progressType | int32_t | 是 | — | 取值 0（linear）/2（eclipse）/3（scale-ring）；其它值回落 |
| colorMode | ThemeMode（上下文成员） | 是（由 ThemeContext 提供） | LIGHT | 决定浅/深取值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 无品牌色 + LIGHT | GetShadowColor 返回 `0xFF000000` | AC-1.1,AC-1.4 |
| 2 | DARK 字体色 | GetDefaultFontColor 返回 `0x99FFFFFF` | AC-2.2,AC-2.3 |
| 3 | DARK 装饰线色 | GetDefaultDecorationColor 返回 `0x99FFFFFF` | AC-2.5 |
| 4 | progressType=0 + LIGHT | 返回 `0xFF0A59F7` | AC-4.1 |
| 5 | progressType=未知 + 任意模式 | 返回 `0xFFFF7DFF` | AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 宿主集成 API Version ≥ 20。
- **API 版本号策略:** 扩展组件默认色为 C++ 内部常量，无 `@since` 标注；深浅色跟随由 Feat-01 的 `updateThemeMode`/`updateAndCheckThemeMode` 统一驱动。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 硬编码默认色 | 扩展默认色固化在 `Extended*Theme.cpp` 常量，组件未显式设置时读取 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8 |
| 绕过 ThemeFactory | 扩展主题由组件栈构造，不经 `ThemeFactory`/`ThemeManager` 缓存 | AC-6.1,AC-6.3 |
| 深浅色切换传播 | 扩展组件经组件级 `OnConfigChange` 重渲染体现默认色切换 | AC-4.7 |
| 范围边界 | 其它扩展组件（Radio/Toggle/Button/Checkbox/TextInput/Select/TabContent 等）默认色内联于各组件 `.cpp/.h`，不在 `Extended*Theme` | design.md RISK-7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 未知 progressType 不抛异常，回落固定色 | C++ UT | `ExtendedProgressTheme.cpp:71` |
| 性能 | 默认色为编译期常量，无运行时分配 | C++ UT | `Extended*Theme.cpp` 常量 |
| 可测试性 | 取值方法为纯函数（依 colorMode/progressType/breakpoint） | C++ UT | `Extended*Theme.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | Grid/List 按断点（通常 SM）用 2 列/1 行 | 断点→模板/行数映射 | C++ UT | `ExtendedGridTheme.cpp:54-69`、`ExtendedListTheme.cpp:54-69` |
| 平板 | Grid/List 按断点（通常 MD/LG）用 3~5 列/2~3 行 | 同上 | C++ UT | 同上 |
| 折叠屏 | 断点随窗口宽度变化，触发 OnConfigChange 重解析 | 断点切换归 07-04-23 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 默认色与无障碍无关 | — |
| 大字体 | 否 | 不涉及（字号归其它接口） | — |
| 深色模式 | 是 | 本域核心：默认浅/深色映射 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7,AC-4.8 |
| 多窗口/分屏 | 否 | 多 Surface 主题独立 | design.md ADR-5 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API Version ≥ 20 | design.md |
| 生态兼容 | 是 | 鸿蒙扩展协议 `ohos.a2ui.extended.catalog` | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 扩展组件默认深浅色
  作为 生成式 UI 宿主开发者
  我想要 扩展组件在未显式设置颜色时使用默认深浅色
  以便 深浅色切换时组件自动适配

  Scenario: 深色模式文本默认字体色
    Given 当前 colorMode 为 DARK
    And Text 组件未设置 styles.fontColor
    When 组件解析默认字体色
    Then 返回 0x99FFFFFF

  Scenario: 品牌色优先于阴影默认色
    Given 当前 hasBrandColor 为 true 且 brandColor 为 0xFF123456
    When 组件解析阴影色
    Then 返回 0xFF123456

  Scenario Outline: 进度条按类型默认色
    Given 当前 colorMode 为 LIGHT
    When progressType 为 <type>
    Then 返回 <color>

    Examples:
      | type | color      |
      | 0    | 0xFF0A59F7 |
      | 2    | 0x19000000 |
      | 3    | 0x99000000 |
      | 99   | 0xFFFF7DFF |

  Scenario Outline: Grid 断点列模板
    Given 当前 breakpoint 为 <bp>
    When 组件解析列模板
    Then 返回 <template>

    Examples:
      | bp | template              |
      | XS | "1fr 1fr"             |
      | MD | "1fr 1fr 1fr"         |
      | XL | "1fr 1fr 1fr 1fr 1fr" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做扩展组件默认深浅色；其它扩展组件内联默认色不在此域）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedTextTheme ExtendedDividerTheme ExtendedProgressTheme 默认深浅色硬编码常量"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedCommonTheme GetShadowColor brandColor 优先 colorMode 默认"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedGridTheme GetColumnsTemplate ExtendedListTheme GetLanes 断点映射"
  - repo: "GenerativeUI/A2UIRender"
    query: "ThemeFactory 注册表 Extended*Theme 绕过 GetTheme 直接构造"
```

**关键文档：** `genui/src/main/cpp/components/extended/ExtendedCommonTheme.cpp`、`ExtendedTextTheme.cpp`、`ExtendedDividerTheme.cpp`、`ExtendedProgressTheme.cpp`、`ExtendedGridTheme.cpp`、`ExtendedListTheme.cpp`、`ExtendedComponent.cpp`、`genui/src/main/cpp/theme/ThemeFactory.cpp`
