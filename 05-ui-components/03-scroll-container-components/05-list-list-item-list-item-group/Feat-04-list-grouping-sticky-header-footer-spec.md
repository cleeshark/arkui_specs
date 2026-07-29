# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 分组/粘性头尾/Header/Footer |
| 特性编号 | Func-05-03-05-Feat-04 |
| 优先级 | P1 |
| 目标版本 | API 9 ~ 26+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 ListItemGroup header/footer(CustomBuilder@9)/headerComponent/footerComponent(ComponentContent@13)/headerStyle/footerStyle(FLOATING@26) 与 ListAttribute.sticky(StickyStyle: None/Header/Footer/BOTH@20)。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md` |
| SDK Dynamic | `ets/dynamic/component/list_item_group.d.ts` + `list.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/list/list_item_group_pattern.h/.cpp` |
| LayoutProperty | `frameworks/core/components_ng/pattern/list/list_item_group_layout_property.h` + `list_item_group_layout_info.h` |
| Properties | `frameworks/core/components_ng/pattern/list/list_properties.h` |
| Model Source | `frameworks/core/components_ng/pattern/list/list_item_group_model_ng.cpp` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 分组头尾内容

作为**应用开发者**，我想要**用 header/footer 或 headerComponent/footerComponent 为分组设置头尾**，以便**分组展示标题/统计**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `ListItemGroup({header: CustomBuilder, footer: CustomBuilder})`（@since 9） THEN 头尾经 ShallowBuilder 延迟构建 | 正常 |
| AC-1.2 | WHEN 设置 `headerComponent: ComponentContent`/`footerComponent`（@since 13） THEN 经 ComponentContent 通道运行时内容 | 正常 |
| AC-1.3 | WHEN 不设 header/footer THEN 分组无头尾 | 边界 |
| AC-1.4 | WHEN 同时设 header 与 headerComponent THEN headerComponent 优先 | 边界 |
| AC-1.5 | WHEN 设置 `space`/`spaceWidth(@26)` THEN 分组内项间距生效 | 正常 |
| AC-1.6 | WHEN 设置 `style: ListItemGroupStyle.CARD`（@since 10） THEN 卡片样式 | 正常 |

### US-2: 粘性头尾

作为**应用开发者**，我想要**用 sticky 让分组头尾在滚动时吸附固定**，以便**始终可见分组标识**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `ListAttribute.sticky(StickyStyle.Header)`（@since 9） THEN header 吸附固定 | 正常 |
| AC-2.2 | WHEN 设置 `sticky(StickyStyle.Footer)` THEN footer 吸附固定 | 正常 |
| AC-2.3 | WHEN 设置 `sticky(StickyStyle.None)` THEN 不吸附 | 边界 |
| AC-2.4 | WHEN 设置 `sticky(StickyStyle.BOTH)`（@since 20） THEN header 与 footer 同时吸附 | 正常 |
| AC-2.5 | WHEN 使用 ListItemAttribute.sticky（@since 7 弃用 9） THEN 不生效，应迁移至 ListAttribute.sticky | 边界 |

### US-3: 浮动头尾样式

作为**应用开发者**，我想要**用 headerStyle/footerStyle FLOATING 让头尾浮动**，以便**特殊视觉**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `headerStyle: ListItemGroupHeaderFooterStyle.FLOATING`（@since 26） THEN header 浮动样式 | 正常 |
| AC-3.2 | WHEN 设置 `footerStyle: FLOATING`（@since 26） THEN footer 浮动样式 | 正常 |
| AC-3.3 | WHEN 设置 `headerStyle/footerStyle: NONE`（默认） THEN 标准样式 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-4 | 单元测试：header/footer builder | `list_item_group.d.ts:155,192` |
| AC-1.2 | R-2 | TASK-SKELETON-4 | 单元测试：ComponentContent | `list_item_group.d.ts:166,203` |
| AC-1.3 | R-1 | TASK-SKELETON-4 | 单元测试：无头尾 | `list_item_group_pattern.cpp` |
| AC-1.4 | R-3 | TASK-SKELETON-4 | 单元测试：优先级 | `list_item_group_model_ng.cpp` |
| AC-1.5 | R-4 | TASK-SKELETON-4 | 单元测试：space | `list_item_group.d.ts:229,250` |
| AC-1.6 | R-5 | TASK-SKELETON-4 | 单元测试：CARD | `list_item_group.d.ts:269` |
| AC-2.1 | R-6 | TASK-SKELETON-4 | 单元测试：sticky Header | `list.d.ts:2131` |
| AC-2.2 | R-6 | TASK-SKELETON-4 | 单元测试：sticky Footer | `list.d.ts:2131` |
| AC-2.3 | R-6 | TASK-SKELETON-4 | 单元测试：None | `list.d.ts:2131` |
| AC-2.4 | R-6 | TASK-SKELETON-4 | 单元测试：BOTH | `list.d.ts:342` BOTH@20 |
| AC-2.5 | R-7 | TASK-SKELETON-4 | 单元测试：ListItem.sticky 弃用 | `list_item.d.ts:811` |
| AC-3.1 | R-8 | TASK-SKELETON-4 | 单元测试：FLOATING header | `list_item_group.d.ts:279` |
| AC-3.2 | R-8 | TASK-SKELETON-4 | 单元测试：FLOATING footer | `list_item_group.d.ts:289` |
| AC-3.3 | R-8 | TASK-SKELETON-4 | 单元测试：NONE 默认 | `list_item_group.d.ts:82` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | header/footer(CustomBuilder) | ShallowBuilder 延迟构建头尾 | @since 9 | AC-1.1, AC-1.3 |
| R-2 | 行为 | headerComponent/footerComponent(ComponentContent) | 运行时内容通道 | @since 13 | AC-1.2 |
| R-3 | 边界 | 同时设 builder 与 ComponentContent | ComponentContent 优先 | — | AC-1.4 |
| R-4 | 行为 | space/spaceWidth | 分组内项间距 | spaceWidth @26 | AC-1.5 |
| R-5 | 行为 | style(CARD) | 卡片样式 | @since 10 | AC-1.6 |
| R-6 | 行为 | ListAttribute.sticky(StickyStyle) | 头尾吸附；None/Header/Footer/BOTH | BOTH @since 20 | AC-2.1~2.4 |
| R-7 | 边界 | ListItemAttribute.sticky(弃用) | 不生效，迁移至 List | 弃用 @since 9 | AC-2.5 |
| R-8 | 行为 | headerStyle/footerStyle(FLOATING/NONE) | 浮动/标准样式 | @since 26 | AC-3.1~3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5 头尾内容 | 单元测试 | builder/ComponentContent/优先/space/style |
| VM-2 | R-6~R-7 粘性 | 单元测试 | sticky 各值/ListItem 弃用 |
| VM-3 | R-8 浮动样式 | 单元测试 | FLOATING/NONE |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `ListItemGroupOptions.header/footer` | Public（@since 9） | `CustomBuilder` | — | 无 | 头尾 builder | AC-1.1 |
| `ListItemGroupOptions.headerComponent/footerComponent` | Public（@since 13） | `ComponentContent` | — | 无 | 头尾 ComponentContent | AC-1.2 |
| `ListItemGroupOptions.space/spaceWidth` | Public（@since 9/26） | `number\|string` / `Dimension` | — | 无 | 项间距 | AC-1.5 |
| `ListItemGroupOptions.style` | Public（@since 10） | `ListItemGroupStyle` | — | 无 | 卡片样式 | AC-1.6 |
| `ListItemGroupOptions.headerStyle/footerStyle` | Public（@since 26） | `ListItemGroupHeaderFooterStyle` | — | 无 | 浮动样式 | AC-3.1~3.3 |
| `ListAttribute.sticky(value)` | Public（@since 9） | `StickyStyle` | `ListAttribute` | 无 | 粘性头尾 | AC-2.1~2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ListItemAttribute.sticky` | 废弃 since 9 | ListItem 头尾吸附 | 迁移至 `ListAttribute#sticky` | AC-2.5 |

## 接口规格

### 接口定义

**ListAttribute.sticky(value: StickyStyle)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ListAttribute::sticky(value: StickyStyle): ListAttribute` |
| 返回值 | `ListAttribute` |
| 开放范围 | Public（@since 9；BOTH @20） |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `StickyStyle` | 是 | None | None/Header/Footer/BOTH(@20) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Header | header 吸附 | AC-2.1 |
| 2 | Footer | footer 吸附 | AC-2.2 |
| 3 | None | 不吸附 | AC-2.3 |
| 4 | BOTH | 双吸附 | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是 — ListItemAttribute.sticky 弃用 9→ListAttribute.sticky
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** header/footer/space/sticky @9；style @10；headerComponent/footerComponent @13；BOTH @20；headerStyle/footerStyle/spaceWidth @26
- **API 版本号策略:** 各属性标注 @since；ListItem.sticky 弃用

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| sticky 在 List 非 ListItem | 分组级语义 | AC-2.x |
| builder 与 ComponentContent 双通道 | 运行时内容支持 | AC-1.4 |
| ShallowBuilder 延迟构建 | 性能 | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | ShallowBuilder 延迟构建保帧 | 单元测试 | `list_item_group_pattern.cpp` |
| 可测试性 | 头尾/粘性可单测 | 单元测试 | TASK-SKELETON-4 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 头尾无障碍可达 | AC-1.x |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | ListItem.sticky 弃用 9；@10/13/20/26 门槛 | AC-2.5, AC-3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（分组/粘性；选择编辑在 Feat-05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ListItemGroupPattern header/footer ShallowBuilder 延迟构建与 ListAttribute.sticky 吸附渲染"
```

**关键文档:** `list_item_group.d.ts`、`list_item_group_pattern.h/.cpp`、`list_properties.h`、`design.md`
