# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Menu/MenuItem 组件创建与属性 |
| 特性编号 | Func-05-06-01-Feat-02 |
| FuncID | 05-06-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 9 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Menu 组件 (MenuInterface/MenuAttribute) | @since 9，必须配合 bindMenu/bindContextMenu 使用 |
| ADDED | MenuItem 组件 (MenuItemInterface/MenuItemAttribute/MenuItemOptions) | @since 9 |
| ADDED | MenuAttribute.fontSize/fontColor/font/radius 属性 | @since 9-10 |
| ADDED | MenuAttribute.menuItemDivider/menuItemGroupDivider 属性 | @since 12 |
| ADDED | MenuAttribute.subMenuExpandingMode (SubMenuExpandingMode) 属性 | @since 12，SIDE_EXPAND/EMBEDDED_EXPAND/STACK_EXPAND |
| ADDED | MenuItemOptions.symbolStartIcon/symbolEndIcon 属性 | @since 12 |
| ADDED | MenuAttribute.subMenuExpandSymbol 属性 | @since 20 |
| ADDED | MenuItemAttribute.subMenuBuilder 属性 | @since 26 |
| MODIFIED | MenuAttribute.fontSize 废弃 | @deprecated since 10，@useinstead font |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/design.md`
- **KB 路由**: `docs/kb/components/overlay/menu.md`
- **SDK 类型定义**:
  - Dynamic (Menu): `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/menu.d.ts`
  - Dynamic (MenuItem): `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/menu_item.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: Menu 组件创建与属性

**角色**: 应用开发者
**期望**: 我想要创建 Menu 组件并设置字体、圆角、分隔线等属性
**价值**: 以便自定义菜单的视觉样式

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Menu()` 创建菜单容器 THEN 返回 MenuAttribute 对象，菜单作为 MenuItem/MenuItemGroup 的容器（`menu.d.ts:70`，`MenuModelNG::Create()` at `menu_model_ng.cpp:257`） | 正常 |
| AC-1.2 | WHEN 设置 `font(value: Font)` THEN 菜单内所有文本使用指定字号/字重/字体族/样式，默认值 { size: 16, family: 'HarmonyOS Sans', weight: FontWeight.Medium, style: FontStyle.Normal }（`menu.d.ts:153`，`MenuModelNG::SetFontWeight/SetFontStyle` at `menu_model_ng.cpp:315,320`） | 正常 |
| AC-1.3 | WHEN 设置 `radius(value: Dimension \| BorderRadiuses)` THEN 菜单圆角为指定值，默认 2-in-1 设备 8vp、其他设备 20vp（`menu.d.ts:183`，`MenuModelNG::SetBorderRadius` at `menu_model_ng.cpp:341`）；API 12+ 当水平两最大圆角之和超过菜单宽度时回退默认圆角 | 正常 |
| AC-1.4 | WHEN 设置 `menuItemDivider(options: DividerStyleOptions \| undefined)` (API 12+) THEN 菜单项之间显示分隔线，strokeWidth/color/startMargin/endMargin/mode 可配置（`menu.d.ts:201`，`MenuPattern::UpdateMenuItemDivider` at `menu_pattern.cpp:427`） | 正常 |
| AC-1.5 | WHEN menuItemDivider 的 startMargin + endMargin 超过组件宽度 THEN 两者均设为 0（`menu.d.ts:187-188` 注释） | 边界 |
| AC-1.6 | WHEN 设置 `subMenuExpandingMode(mode: SubMenuExpandingMode)` (API 12+) THEN 子菜单按指定模式展开，默认 SIDE_EXPAND（`menu.d.ts:232`，`MenuModelNG::SetExpandingMode` at `menu_model_ng.cpp:432`） | 正常 |
| AC-1.7 | WHEN 设置 `subMenuExpandSymbol(symbol: SymbolGlyphModifier)` (API 20+) THEN 子菜单展开符号按模式显示：SIDE 不显示、EMBEDDED 默认 chevron_down 旋转 180°、STACK 默认 chevron_forward 旋转 90°（`menu.d.ts:249`，`MenuModelNG::SetExpandSymbol` at `menu_model_ng.cpp:442`） | 正常 |
| AC-1.8 | WHEN 使用 `fontSize(value: Length)` THEN 废弃 API，应使用 `font(value: Font)` 替代（`menu.d.ts:140`，@deprecated since 10） | 边界 |

### US-2: MenuItem 组件创建与交互

**角色**: 应用开发者
**期望**: 我想要创建 MenuItem 并设置图标、文本、选中状态和子菜单
**价值**: 以便构建菜单项内容和交互逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `MenuItem(value?: MenuItemOptions)` THEN 创建菜单项，支持 startIcon/content/endIcon/labelInfo/builder 参数（`menu_item.d.ts:140`） | 正常 |
| AC-2.2 | WHEN 调用 `MenuItem(value: CustomBuilder)` THEN 使用 CustomBuilder 构建菜单项内容（`menu_item.d.ts:140`） | 正常 |
| AC-2.3 | WHEN 设置 `selected(value: boolean)` THEN 菜单项选中状态改变，默认 false；API 10+ 支持 `$$` 双向绑定，API 18+ 支持 `!!` 双向绑定（`menu_item.d.ts:172`） | 正常 |
| AC-2.4 | WHEN 设置 `selectIcon(value: boolean \| ResourceStr \| SymbolGlyphModifier)` THEN 选中时显示对应图标：true=默认勾选图标，ResourceStr=自定义图标，SymbolGlyphModifier=HMSymbol 图标，默认 false（`menu_item.d.ts:196`） | 正常 |
| AC-2.5 | WHEN 菜单项被手动选中/取消选中 THEN 触发 `onChange(callback: (selected: boolean) => void)` 回调（`menu_item.d.ts:210`，`MenuItemPattern::OnClick` at `menu_item_pattern.cpp:1432` 调用 `onChange(IsSelected())` at `menu_item_pattern.cpp:1460`） | 正常 |
| AC-2.6 | WHEN 点击 MenuItem 且有 builder/subMenuBuilder THEN 触发 ShowSubMenu（`menu_item_pattern.cpp:1481`，`ShowSubMenu(ShowSubMenuType::CLICK)`） | 正常 |
| AC-2.7 | WHEN 设置 `contentFont/contentFontColor/labelFont/labelFontColor` THEN 菜单项内容和标签使用指定字体样式，contentFontColor 默认 '#E5000000'，labelFontColor 默认 '#99000000'（`menu_item.d.ts:223,236,249,262`） | 正常 |
| AC-2.8 | WHEN 设置 MenuItemOptions.symbolStartIcon/symbolEndIcon THEN 对应位置显示 Symbol 图标，且设置后 startIcon/endIcon 不显示（`menu_item.d.ts:54,89`） | 正常 |
| AC-2.9 | WHEN 调用 `subMenuBuilder(builder: CustomBuilder)` (API 26+) THEN 为自定义菜单项创建子菜单（`menu_item.d.ts:275`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-MENU-01 | UT | `menu_model_ng.cpp:257` |
| AC-1.2 | R-1 | TASK-MENU-01 | UT | `menu_model_ng.cpp:315,320` |
| AC-1.3 | R-2, R-6 | TASK-MENU-01 | UT | `menu_model_ng.cpp:341` |
| AC-1.4 | R-3 | TASK-MENU-01 | UT | `menu_pattern.cpp:427` |
| AC-1.5 | R-6 | TASK-MENU-01 | UT | `menu.d.ts:187-188` |
| AC-1.6 | R-4 | TASK-MENU-01 | UT | `menu_model_ng.cpp:432` |
| AC-1.7 | R-5 | TASK-MENU-01 | UT | `menu_model_ng.cpp:442` |
| AC-1.8 | R-7 | TASK-MENU-01 | 手工 | `menu.d.ts:140` |
| AC-2.1 | R-8 | TASK-MENU-01 | UT | `menu_item.d.ts:140` |
| AC-2.2 | R-8 | TASK-MENU-01 | UT | `menu_item.d.ts:140` |
| AC-2.3 | R-8 | TASK-MENU-01 | UT | `menu_item.d.ts:172` |
| AC-2.4 | R-8 | TASK-MENU-01 | UT | `menu_item.d.ts:196` |
| AC-2.5 | R-8 | TASK-MENU-01 | UT | `menu_item_pattern.cpp:1460` |
| AC-2.6 | R-9 | TASK-MENU-01 | UT | `menu_item_pattern.cpp:1481` |
| AC-2.7 | R-8 | TASK-MENU-01 | UT | `menu_item.d.ts:223,236,249,262` |
| AC-2.8 | R-8 | TASK-MENU-01 | UT | `menu_item.d.ts:54,89` |
| AC-2.9 | R-9 | TASK-MENU-01 | UT | `menu_item.d.ts:275` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 Menu() 创建菜单容器 | 返回 MenuAttribute，API < 11 设置最小宽度 64vp (MIN_MENU_WIDTH) | 必须配合 bindMenu/bindContextMenu 使用 | AC-1.1, AC-1.2 |
| R-2 | 行为 | 设置 radius(value) | 菜单圆角为指定值 | Dimension 非法回退默认圆角；BorderRadiuses 非法无圆角；2-in-1 默认 8vp，其他 20vp | AC-1.3 |
| R-3 | 行为 | 设置 menuItemDivider(options) (API 12+) | 菜单项间显示分隔线 | startMargin + endMargin 超过组件宽度时均设为 0 | AC-1.4 |
| R-4 | 行为 | 设置 subMenuExpandingMode(mode) (API 12+) | 子菜单按指定模式展开 | 默认 SIDE_EXPAND，枚举值 0/1/2 | AC-1.6 |
| R-5 | 行为 | 设置 subMenuExpandSymbol(symbol) (API 20+) | 子菜单展开符号按模式显示 | SIDE 不显示，EMBEDDED chevron_down 旋转 180°，STACK chevron_forward 旋转 90° | AC-1.7 |
| R-6 | 边界 | menuItemDivider 的 startMargin + endMargin 超过组件宽度 | 两者均设为 0 | — | AC-1.5 |
| R-7 | 恢复 | 使用废弃 API fontSize(value: Length) | 废弃 API，仍可调用但应迁移到 font(value: Font) | @deprecated since 10 | AC-1.8 |
| R-8 | 行为 | 调用 MenuItem(value) 创建菜单项 | 支持 MenuItemOptions 或 CustomBuilder；selected 默认 false；selectIcon 默认 false | selected 支持 $$ (API 10+) 和 !! (API 18+) 双向绑定 | AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5, AC-2.7, AC-2.8 |
| R-9 | 行为 | 点击 MenuItem 且有 builder/subMenuBuilder | 触发 ShowSubMenu(ShowSubMenuType::CLICK) | 无 builder 时关闭菜单 | AC-2.6, AC-2.9 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.8 | UT | Menu 组件创建和属性设置（font/radius/divider/expandingMode/expandSymbol） |
| VM-2 | AC-2.1 ~ AC-2.9 | UT | MenuItem 创建、selected/selectIcon/onChange/subMenuBuilder |

## API 变更分析

> 涉及 API 变更时必填。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Menu() | Public | 无参数 | MenuAttribute | 无 | 创建菜单容器 | AC-1.1 |
| MenuAttribute.font(value) | Public | value: Font | MenuAttribute | 无 | 设置菜单文本字体 | AC-1.2 |
| MenuAttribute.fontColor(value) | Public | value: ResourceColor | MenuAttribute | 无 | 设置菜单文本颜色 | AC-1.2 |
| MenuAttribute.radius(value) | Public | value: Dimension \| BorderRadiuses | MenuAttribute | 无 | 设置菜单圆角 | AC-1.3 |
| MenuAttribute.menuItemDivider(options) | Public | options: DividerStyleOptions \| undefined | MenuAttribute | 无 | 设置菜单项分隔线 | AC-1.4 |
| MenuAttribute.menuItemGroupDivider(options) | Public | options: DividerStyleOptions \| undefined | MenuAttribute | 无 | 设置分组分隔线 | AC-1.4 |
| MenuAttribute.subMenuExpandingMode(mode) | Public | mode: SubMenuExpandingMode | MenuAttribute | 无 | 设置子菜单展开模式 | AC-1.6 |
| MenuAttribute.subMenuExpandSymbol(symbol) | Public | symbol: SymbolGlyphModifier | MenuAttribute | 无 | 设置子菜单展开符号 | AC-1.7 |
| MenuItem(value?) | Public | value?: MenuItemOptions \| CustomBuilder | MenuItemAttribute | 无 | 创建菜单项 | AC-2.1 |
| MenuItemAttribute.selected(value) | Public | value: boolean | MenuItemAttribute | 无 | 设置选中状态 | AC-2.3 |
| MenuItemAttribute.selectIcon(value) | Public | value: boolean \| ResourceStr \| SymbolGlyphModifier | MenuItemAttribute | 无 | 设置选中图标 | AC-2.4 |
| MenuItemAttribute.onChange(callback) | Public | callback: (selected: boolean) => void | MenuItemAttribute | 无 | 选中状态变化回调 | AC-2.5 |
| MenuItemAttribute.subMenuBuilder(builder) | Public | builder: CustomBuilder | MenuItemAttribute | 无 | 创建子菜单 | AC-2.9 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| MenuAttribute.fontSize(value: Length) | 废弃 | 设置菜单文本字号 | @deprecated since 10，使用 font(value: Font) 替代 | AC-1.8 |

> API 签名、d.ts 位置、权限要求等实现细节见 design.md "API 签名、Kit 与权限" 章节。

## 接口规格

### 接口定义

**Menu**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Menu(): MenuAttribute` |
| 返回值 | `MenuAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| — | 无参数 | — | — | 必须配合 bindMenu/bindContextMenu 使用；API < 11 最小宽度 64vp |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 调用 Menu() 创建菜单 | 返回 MenuAttribute，作为 MenuItem/MenuItemGroup 容器 | AC-1.1 |
| 2 | Menu 单独使用（无 bindMenu/bindContextMenu） | 不显示菜单 | AC-1.1 |

---

**MenuItem**

| 属性 | 值 |
|------|-----|
| 函数签名 | `MenuItem(value?: MenuItemOptions \| CustomBuilder): MenuItemAttribute` |
| 返回值 | `MenuItemAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | MenuItemOptions \| CustomBuilder | 否 | — | MenuItemOptions: startIcon/content/endIcon/labelInfo/builder/symbolStartIcon/symbolEndIcon；symbolStartIcon 设置后 startIcon 不显示 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 创建 MenuItem(MenuItemOptions) | 创建菜单项，显示 startIcon/content/endIcon/labelInfo | AC-2.1 |
| 2 | 创建 MenuItem(CustomBuilder) | 使用 CustomBuilder 构建内容 | AC-2.2 |
| 3 | 点击有 builder 的 MenuItem | 触发 ShowSubMenu(CLICK) | AC-2.6 |
| 4 | selected 状态手动变化 | 触发 onChange 回调 | AC-2.5 |

## 兼容性声明

- **已有 API 行为变更:** 是，MenuAttribute.fontSize 废弃（@deprecated since 10）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9（Menu/MenuItem 组件）
- **API 版本号策略:** 各 API 按 @since 标注版本引入，通过 Container::LessThanAPIVersion/GreatOrEqualAPIVersion 条件分支实现兼容

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 绑定接口与内容组件分离 | bindMenu/bindContextMenu 在 CommonMethod 上，Menu/MenuItem 作为内容走组件化 Bridge 路径 | AC-1.1, AC-2.1 |
| 调用链自上而下 | SDK → JS Bridge → ViewAbstract → OverlayManager → Bridge → Model → View → Pattern → Layout → Paint | 全部 AC |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 内存 | 单个菜单节点树内存占用 ≤ 500KB | 内存分析 | — |
| 可测试性 | UT 覆盖 MenuPattern/MenuItemPattern | UT | `test/unittest/core/pattern/menu/` |
| 自动化维测 | 支持 DumpLog 状态导出 | hilog | MenuWrapperPattern Dump |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 圆角 20vp | Menu radius 默认值 | 手工 | `common.d.ts:17115` |
| 平板 | 圆角 20vp | Menu radius 默认值 | 手工 | `common.d.ts:17115` |
| 2-in-1 | 圆角 8vp | Menu radius 默认值 | 手工 | `common.d.ts:17115` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Menu/MenuItem 各自实现 AccessibilityProperty，支持 ActionSelect/ActionClick | AC-2.5 (onChange 无障碍上报) |
| 大字体 | 是 | Menu font 属性支持字号定制，大字体下菜单布局自适应 | AC-1.2 |
| 深色模式 | 是 | 颜色属性使用 ResourceColor，通过 MenuThemeWrapper 适配 Token 主题 | AC-1.2, AC-1.3 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 9~26 多版本兼容，废弃 API 保持可用 | AC-1.8 |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "MenuModelNG Create and font/radius/divider property setting"
  - repo: "openharmony/arkui_ace_engine"
    query: "MenuItemPattern OnClick/onChange selected state and ShowSubMenu trigger"
  - repo: "openharmony/arkui_ace_engine"
    query: "MenuItemOptions symbolStartIcon/symbolEndIcon and contentFont/labelFont property"
```

**关键文档：**
- 设计文档: `specs/05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/design.md`
- KB 路由: `docs/kb/components/overlay/menu.md`
- SDK (Menu): `interface/sdk-js/api/@internal/component/ets/menu.d.ts`
- SDK (MenuItem): `interface/sdk-js/api/@internal/component/ets/menu_item.d.ts`
