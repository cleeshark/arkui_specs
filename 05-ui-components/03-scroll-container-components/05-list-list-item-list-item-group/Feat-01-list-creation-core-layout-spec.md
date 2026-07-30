# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 创建与核心布局（含懒加载/缓存） |
| 特性编号 | Func-05-03-05-Feat-01 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ 26+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 List/ListItem/ListItemGroup 创建、listDirection/lanes/alignListItem/divider/childrenMainSize/cachedCount/syncLoad/supportEmptyBranchInLazyLoading 及布局类偏移 contentStartOffset/contentEndOffset/stackFromEnd/maintainVisibleContentPosition。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md` |
| SDK Dynamic | `ets/dynamic/component/list.d.ts` + `list_item.d.ts` + `list_item_group.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/list/list_pattern.h/.cpp` |
| LayoutAlgorithm | `frameworks/core/components_ng/pattern/list/list_layout_algorithm.h/.cpp` |
| LayoutProperty | `frameworks/core/components_ng/pattern/list/list_layout_property.h` + `list_properties.h` + `list_divider_arithmetic.h` + `list_children_main_size.h` |
| Model Source | `frameworks/core/components_ng/pattern/list/list_model_ng.cpp` + `list_item_model_ng.cpp` + `list_item_group_model_ng.cpp` |
| JSView Source | `frameworks/bridge/declarative_frontend/jsview/js_list.cpp` + `js_list_item.cpp` + `js_list_item_group.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 创建 List 与子组件

作为**应用开发者**，我想要**通过 `List(options)` 创建列表并嵌套 ListItem/ListItemGroup**，以便**展示可滚动列表内容**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 `List({initialIndex, space, scroller})` THEN ListPattern 创建，默认 `SetEdgeEffect(EdgeEffect::SPRING,false)`（`list_pattern.h:62`） | 正常 |
| AC-1.2 | WHEN 传入 `ListItem(value?: ListItemOptions)`（@since 10） THEN ListItemPattern 创建 | 正常 |
| AC-1.3 | WHEN 传入 `ListItem(string)`（@since 7 弃用 10） THEN 仍生效但建议 options 形式 | 边界 |
| AC-1.4 | WHEN 传入 `ListItemGroup({header, footer, space, style})`（@since 9） THEN ListItemGroupPattern 创建 | 正常 |
| AC-1.5 | WHEN ListOptions.initialIndex 设置 THEN 初始索引生效 | 正常 |
| AC-1.6 | WHEN ListOptions.space/spaceWidth(@26) 设置 THEN 项间距生效 | 正常 |

### US-2: 方向、多列与对齐

作为**应用开发者**，我想要**用 listDirection/lanes/alignListItem 配置方向与多列**，以便**适配横向与多列布局**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `listDirection(Axis.Vertical)`（默认，@since 7） THEN 纵向布局 | 正常 |
| AC-2.2 | WHEN 设置 `listDirection(Axis.Horizontal)` THEN 横向布局 | 正常 |
| AC-2.3 | WHEN 设置 `lanes(number)`（@since 9） THEN 多列均分，切 ListLanesLayoutAlgorithm | 正常 |
| AC-2.4 | WHEN 设置 `lanes(LengthConstrain, gutter?)`（gutter @since 10） THEN 约束多列+列间距 | 正常 |
| AC-2.5 | WHEN 设置 `lanes(number, ItemFillPolicy)`（@since 22） THEN 按填充策略分布 | 正常 |
| AC-2.6 | WHEN 设置 `alignListItem(ListItemAlign.Start/Center/End)`（@since 9） THEN 交叉轴对齐 | 正常 |
| AC-2.7 | WHEN lanes=1 THEN 单列，用 ListLayoutAlgorithm | 边界 |

### US-3: 分隔线与主轴尺寸

作为**应用开发者**，我想要**用 divider/childrenMainSize 配置分隔线与主轴尺寸预测**，以便**精确布局**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `divider({strokeWidth, color?, startMargin?, endMargin?})`（ListDividerOptions @since 18 rectify） THEN 分隔线绘制 | 正常 |
| AC-3.2 | WHEN divider 设 null THEN 无分隔线 | 边界 |
| AC-3.3 | WHEN 设置 `childrenMainSize(ChildrenMainSize)`（@since 12） THEN 精确预测量减少跳变 | 正常 |
| AC-3.4 | WHEN ListItemGroup 设置 divider THEN 分组内分隔线 | 正常 |
| AC-3.5 | WHEN ListItemGroup 设置 childrenMainSize THEN 分组主轴尺寸预测 | 正常 |

### US-4: 懒加载与缓存

作为**应用开发者**，我想要**用 cachedCount/syncLoad/supportEmptyBranchInLazyLoading 优化性能**，以便**流畅长列表**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 设置 `cachedCount(number)`（@since 7） THEN 预加载窗口生效 | 正常 |
| AC-4.2 | WHEN 设置 `cachedCount(count, show)`（@since 14） THEN 预加载并控制是否显示 | 正常 |
| AC-4.3 | WHEN 设置 `cachedCount(count\|CacheCountInfo, show)`（@since 22） THEN CacheCountInfo 控制正反向缓存 | 正常 |
| AC-4.4 | WHEN 设置 `syncLoad(enable)`（@since 20） THEN 启用分帧加载 | 正常 |
| AC-4.5 | WHEN 设置 `supportEmptyBranchInLazyLoading(supported)`（@since 23） THEN 空分支懒加载容错 | 正常 |
| AC-4.6 | WHEN 不设 cachedCount THEN 默认缓存窗口 | 边界 |

### US-5: 布局类偏移

作为**应用开发者**，我想要**用 contentStartOffset/contentEndOffset/stackFromEnd/maintainVisibleContentPosition 控制内容区与可见性**，以便**安全区避让与数据变更稳定**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 设置 `contentStartOffset(value)`（@since 11/22 Resource） THEN 内容区起始偏移生效 | 正常 |
| AC-5.2 | WHEN 设置 `contentEndOffset(value)`（@since 11/22 Resource） THEN 内容区结束偏移生效 | 正常 |
| AC-5.3 | WHEN 设置 `stackFromEnd(enabled)`（@since 19） THEN 从底部开始布局 | 正常 |
| AC-5.4 | WHEN 设置 `maintainVisibleContentPosition(enabled)`（@since 12） THEN 上方插入/删除数据时保持可见内容位置不变 | 正常 |
| AC-5.5 | WHEN 不设 maintainVisibleContentPosition THEN 数据变更可能引起可见位置跳变 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-1 | 单元测试：Create + SPRING | `list_pattern.h:62` |
| AC-1.2 | R-2 | TASK-SKELETON-1 | 单元测试：ListItem 创建 | `list_item.d.ts:749` |
| AC-1.3 | R-3 | TASK-SKELETON-1 | 单元测试：string 弃用 | `list_item.d.ts:770` |
| AC-1.4 | R-4 | TASK-SKELETON-1 | 单元测试：ListItemGroup 创建 | `list_item_group.d.ts:345` |
| AC-1.5 | R-5 | TASK-SKELETON-1 | 单元测试：initialIndex | `list.d.ts:1086` |
| AC-1.6 | R-5 | TASK-SKELETON-1 | 单元测试：space | `list.d.ts:1141` |
| AC-2.1 | R-6 | TASK-SKELETON-1 | 单元测试：Vertical | `list.d.ts:1693` |
| AC-2.2 | R-6 | TASK-SKELETON-1 | 单元测试：Horizontal | `list.d.ts:1693` |
| AC-2.3 | R-7 | TASK-SKELETON-1 | 单元测试：lanes 多列 | `list.d.ts:1604` |
| AC-2.4 | R-7 | TASK-SKELETON-1 | 单元测试：gutter | `list.d.ts:1620` |
| AC-2.5 | R-7 | TASK-SKELETON-1 | 单元测试：ItemFillPolicy | `list.d.ts:1620` |
| AC-2.6 | R-8 | TASK-SKELETON-1 | 单元测试：alignListItem | `list.d.ts:1653` |
| AC-2.7 | R-7 | TASK-SKELETON-1 | 单元测试：lanes=1 | `list_layout_algorithm.h` |
| AC-3.1 | R-9 | TASK-SKELETON-1 | 单元测试：divider | `list.d.ts:1910` |
| AC-3.2 | R-9 | TASK-SKELETON-1 | 单元测试：divider null | `list.d.ts:1910` |
| AC-3.3 | R-10 | TASK-SKELETON-1 | 单元测试：childrenMainSize | `list.d.ts:2237` |
| AC-3.4 | R-9 | TASK-SKELETON-1 | 单元测试：组 divider | `list_item_group.d.ts:427` |
| AC-3.5 | R-10 | TASK-SKELETON-1 | 单元测试：组 childrenMainSize | `list_item_group.d.ts:439` |
| AC-4.1 | R-11 | TASK-SKELETON-1 | 单元测试：cachedCount 1-arg | `list.d.ts:2005` |
| AC-4.2 | R-11 | TASK-SKELETON-1 | 单元测试：cachedCount 2-arg | `list.d.ts:2021` |
| AC-4.3 | R-11 | TASK-SKELETON-1 | 单元测试：CacheCountInfo | `list.d.ts:2039` |
| AC-4.4 | R-12 | TASK-SKELETON-1 | 单元测试：syncLoad | `list.d.ts:2308` |
| AC-4.5 | R-13 | TASK-SKELETON-1 | 单元测试：supportEmpty | `list.d.ts:2377` |
| AC-4.6 | R-11 | TASK-SKELETON-1 | 单元测试：默认缓存 | `list_pattern.cpp` |
| AC-5.1 | R-14 | TASK-SKELETON-1 | 单元测试：contentStartOffset | `list.d.ts:1806` |
| AC-5.2 | R-14 | TASK-SKELETON-1 | 单元测试：contentEndOffset | `list.d.ts:1843` |
| AC-5.3 | R-15 | TASK-SKELETON-1 | 单元测试：stackFromEnd | `list.d.ts:2283` |
| AC-5.4 | R-16 | TASK-SKELETON-1 | 单元测试：maintainVisible | `list.d.ts:2261` |
| AC-5.5 | R-16 | TASK-SKELETON-1 | 单元测试：默认跳变 | `list_pattern.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | List(options) 创建 | ListPattern 创建，默认 SPRING | `list_pattern.h:62` | AC-1.1 |
| R-2 | 行为 | ListItem(ListItemOptions) 创建 | ListItemPattern 创建 | @since 10 | AC-1.2 |
| R-3 | 边界 | ListItem(string) | 弃用 @10 仍生效 | 建议 options | AC-1.3 |
| R-4 | 行为 | ListItemGroup(options) 创建 | ListItemGroupPattern 创建 | @since 9 | AC-1.4 |
| R-5 | 行为 | ListOptions.initialIndex/space/spaceWidth | 索引/间距生效 | spaceWidth @26 | AC-1.5, AC-1.6 |
| R-6 | 行为 | listDirection(Axis) | 方向布局 | 默认 Vertical | AC-2.1, AC-2.2 |
| R-7 | 行为 | lanes(number/LengthConstrain, gutter?, ItemFillPolicy?) | 多列均分+列间距+填充 | gutter @10；ItemFillPolicy @22 | AC-2.3~2.5, AC-2.7 |
| R-8 | 行为 | alignListItem(ListItemAlign) | 交叉轴对齐 | @since 9 | AC-2.6 |
| R-9 | 行为 | divider(ListDividerOptions/null) | 分隔线绘制；null 无 | @since 18 rectify | AC-3.1, AC-3.2, AC-3.4 |
| R-10 | 行为 | childrenMainSize(ChildrenMainSize) | 精确预测量 | @since 12 | AC-3.3, AC-3.5 |
| R-11 | 行为 | cachedCount(number/(count,show)/(count\|CacheCountInfo,show)) | 预加载窗口 | @since 7/14/22 | AC-4.1~4.3, AC-4.6 |
| R-12 | 行为 | syncLoad(enable) | 分帧加载 | @since 20 | AC-4.4 |
| R-13 | 行为 | supportEmptyBranchInLazyLoading(supported) | 空分支容错 | @since 23 | AC-4.5 |
| R-14 | 行为 | contentStartOffset/contentEndOffset | 内容区起止偏移 | @since 11/22 | AC-5.1, AC-5.2 |
| R-15 | 行为 | stackFromEnd(enabled) | 从底布局 | @since 19 | AC-5.3 |
| R-16 | 行为 | maintainVisibleContentPosition(enabled) | 数据变更保持可见位置 | @since 12 | AC-5.4, AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5 创建 | 单元测试 | 三组件创建与默认 SPRING |
| VM-2 | R-6~R-8 方向多列 | 单元测试 | direction/lanes/align |
| VM-3 | R-9~R-10 分隔与尺寸 | 单元测试 | divider/childrenMainSize |
| VM-4 | R-11~R-13 懒加载 | 单元测试 | cachedCount/syncLoad/supportEmpty |
| VM-5 | R-14~R-16 布局偏移 | 单元测试 | offsets/stackFromEnd/maintainVisible |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `List(options?)` | Public（@since 7） | `ListOptions?` | `ListAttribute` | 无 | 创建列表 | AC-1.1 |
| `ListItem(options?)` | Public（@since 10） | `ListItemOptions?` | `ListItemAttribute` | 无 | 创建列表项 | AC-1.2 |
| `ListItemGroup(options?)` | Public（@since 9） | `ListItemGroupOptions?` | `ListItemGroupAttribute` | 无 | 创建列表组 | AC-1.4 |
| `listDirection/lanes/alignListItem/divider/childrenMainSize/syncLoad/cachedCount/supportEmptyBranchInLazyLoading/contentStartOffset/contentEndOffset/stackFromEnd/maintainVisibleContentPosition` | Public | 各类型 | `ListAttribute` | 无 | 布局属性 | AC-2.x~5.x |
| C-API `NODE_LIST_*` divider/lanes 等 | Public | 属性枚举 | — | 无 | NDK 通道 | AC-3.x |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ListItemInterface(string)` | 废弃 since 10 | 字符串形式 | 迁移至 `ListItem(ListItemOptions)` | AC-1.3 |

## 接口规格

### 接口定义

**lanes(value, gutter?, ItemFillPolicy?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ListAttribute::lanes(value: number\|LengthConstrain, gutter?: Dimension): ListAttribute` |
| 返回值 | `ListAttribute` |
| 开放范围 | Public（@since 9；gutter @10；ItemFillPolicy @22） |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `number\|LengthConstrain` | 是 | 1 | lanes>1 切 ListLanesLayoutAlgorithm |
| gutter | `Dimension` | 否 | 0 | 列间距 |
| ItemFillPolicy | — | 否 | — | @since 22 填充策略 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | lanes>1 | 多列均分 | AC-2.3 |
| 2 | gutter 设置 | 列间距 | AC-2.4 |
| 3 | ItemFillPolicy | 填充策略 | AC-2.5 |
| 4 | lanes=1 | 单列 | AC-2.7 |

## 兼容性声明

- **已有 API 行为变更:** 否（ListItem(string) 弃用 10）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** List/ListItem(string)/ListItemGroup @7/9；ListItem(options) @10；childrenMainSize/contentStartOffset/End/maintainVisible @11/12；cachedCount 2-arg @14；syncLoad/supportEmpty @20/23；ItemFillPolicy/CacheCountInfo/Resource @22；stackFromEnd @19；spaceWidth @26
- **API 版本号策略:** 各属性标注 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 默认 edgeEffect SPRING | `list_pattern.h:62` | AC-1.1 |
| lanes>1 切 ListLanesLayoutAlgorithm | 多列专用 | AC-2.3 |
| childrenMainSize 精确预测量 | 减少跳变 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 懒加载/分帧保帧；cachedCount 控制内存 | 性能基准 | `list_layout_algorithm.cpp` |
| 内存 | cachedCount 限制预加载窗口 | 代码审查 | `list_pattern.cpp` |
| 可测试性 | 布局属性可单测 | 单元测试 | TASK-SKELETON-1 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
| 平板 | — | 多列常见 | 单元测试 | — |
| 折叠屏 | — | 多列适配 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | ListAccessibilityProperty | AC-1.x |
| 大字体 | 否 | 几何不随字体 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | @7~26 多轮门槛 | AC-2.x~5.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（创建/布局/懒加载；滚动运动学在 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ListPattern 默认 SPRING 与 ListLanesLayoutAlgorithm 多列布局及 childrenMainSize 精确预测量"
```

**关键文档:** `list.d.ts`、`list_pattern.h`、`list_layout_algorithm.h`、`design.md`
