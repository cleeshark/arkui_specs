# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 滚动可观测性与控制器 |
| 特性编号 | Func-05-03-05-Feat-03 |
| 优先级 | P1 |
| 目标版本 | API 7 ~ 19+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 ListScroller 控制器（getItemRectInGroup/scrollToItemInGroup/closeAllSwipeActions/getVisibleListContentInfo + 继承 Scroller）、滚动事件（onScroll 弃用/onScrollIndex/onScrollVisibleContentChange/onReachStart/onReachEnd/onScrollStart/onScrollStop/onScrollFrameBegin）、UIListEvent 程序化接口。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md` |
| SDK Dynamic | `ets/dynamic/component/list.d.ts` |
| Controller | `frameworks/core/components_ng/pattern/list/list_position_controller.h/.cpp` |
| PositionMap | `frameworks/core/components_ng/pattern/list/list_position_map.h` |
| EventHub | `frameworks/core/components_ng/pattern/list/list_event_hub.h` |
| Pattern Source | `frameworks/core/components_ng/pattern/list/list_pattern.cpp` |
| C-API | `frameworks/core/interfaces/native/implementation/ui_list_event_accessor.cpp` + `list_scroller_accessor.cpp` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 列表控制器查询

作为**应用开发者**，我想要**用 ListScroller 查询子项矩形与可见内容信息**，以便**驱动联动与定位**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `getItemRectInGroup(index, indexInGroup)`（@since 11） THEN 返回分组内子项 RectResult | 正常 |
| AC-1.2 | WHEN 调用 `scrollToItemInGroup(index, indexInGroup, smooth?, align?)`（@since 11） THEN 滚动到分组内子项 | 正常 |
| AC-1.3 | WHEN 调用 `getVisibleListContentInfo(x, y)`（@since 14） THEN 返回 VisibleListContentInfo（index/itemGroupArea/itemIndexInGroup） | 正常 |
| AC-1.4 | WHEN index/indexInGroup 越界 THEN 返回默认/空结果 | 边界 |
| AC-1.5 | WHEN 调用继承的 scrollTo/scrollEdge/currentOffset/scrollToIndex/getItemRect THEN 经 ScrollableController 复用 | 正常 |

### US-2: 关闭所有滑动操作

作为**应用开发者**，我想要**用 closeAllSwipeActions 程序化关闭所有 ListItem 滑动**，以便**退出编辑态**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 `closeAllSwipeActions(options?: CloseSwipeActionOptions)`（@since 11，ListScroller 方法） THEN 所有展开的 ListItem 滑动收起（见 Feat-07） | 正常 |
| AC-2.2 | WHEN options.onFinish 设置 THEN 收起完成后回调 | 正常 |
| AC-2.3 | WHEN 无展开项 THEN 立即回调 onFinish | 边界 |

### US-3: 滚动事件

作为**应用开发者**，我想要**用滚动事件感知列表滚动状态**，以便**联动加载/标记**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `onScroll(scrollOffset, scrollState)`（@since 7，弃用 12） THEN 触发但建议迁移 onDidScroll | 边界 |
| AC-3.2 | WHEN 设置 `onScrollIndex(start, end, center?)`（center @since 19） THEN 可见索引变化触发 | 正常 |
| AC-3.3 | WHEN 设置 `onScrollVisibleContentChange(start, end)`（@since 12） THEN 可见内容变化触发 | 正常 |
| AC-3.4 | WHEN 设置 `onReachStart/onReachEnd`（@since 7） THEN 到首尾触发 | 正常 |
| AC-3.5 | WHEN 设置 `onScrollStart`（@since 9） THEN 滚动开始触发 | 正常 |
| AC-3.6 | WHEN 设置 `onScrollStop`（@since 7） THEN 滚动停止触发 | 正常 |
| AC-3.7 | WHEN 设置 `onScrollFrameBegin`（@since 9/@20） THEN 帧前触发 | 正常 |

### US-4: 程序化事件接口

作为**应用开发者**，我想要**用 UIListEvent 程序化绑定事件**，以便**动态切换回调**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 调用 `UIListEvent.setOnWillScroll/setOnDidScroll`（@since 19） THEN 程序化绑定滚动事件 | 正常 |
| AC-4.2 | WHEN 调用 `UIListEvent.setOnScrollIndex/setOnScrollVisibleContentChange` THEN 程序化绑定 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-3 | 单元测试：getItemRectInGroup | `list.d.ts:915` |
| AC-1.2 | R-2 | TASK-SKELETON-3 | 单元测试：scrollToItemInGroup | `list.d.ts:958` |
| AC-1.3 | R-3 | TASK-SKELETON-3 | 单元测试：getVisibleListContentInfo | `list.d.ts:1016` |
| AC-1.4 | R-4 | TASK-SKELETON-3 | 单元测试：越界 | `list_position_controller.cpp` |
| AC-1.5 | R-5 | TASK-SKELETON-3 | 单元测试：继承方法 | `list_position_controller.h:22` |
| AC-2.1 | R-6 | TASK-SKELETON-3 | 单元测试：closeAllSwipeActions | `list.d.ts:992` |
| AC-2.2 | R-6 | TASK-SKELETON-3 | 单元测试：onFinish | `list.d.ts:735` CloseSwipeActionOptions |
| AC-2.3 | R-6 | TASK-SKELETON-3 | 单元测试：无展开 | `list_pattern.cpp` |
| AC-3.1 | R-7 | TASK-SKELETON-3 | 单元测试：onScroll 弃用 | `list.d.ts:2433` |
| AC-3.2 | R-8 | TASK-SKELETON-3 | 单元测试：onScrollIndex | `list.d.ts:2473` |
| AC-3.3 | R-9 | TASK-SKELETON-3 | 单元测试：onScrollVisibleContentChange | `list.d.ts:2485` |
| AC-3.4 | R-10 | TASK-SKELETON-3 | 单元测试：onReachStart/End | `list.d.ts:2525,2565` |
| AC-3.5 | R-11 | TASK-SKELETON-3 | 单元测试：onScrollStart | `list.d.ts:2598` |
| AC-3.6 | R-12 | TASK-SKELETON-3 | 单元测试：onScrollStop | `list.d.ts:2639` |
| AC-3.7 | R-13 | TASK-SKELETON-3 | 单元测试：onScrollFrameBegin | `list.d.ts:2887` |
| AC-4.1 | R-14 | TASK-SKELETON-3 | 单元测试：UIListEvent will/did | `list.d.ts:668` |
| AC-4.2 | R-14 | TASK-SKELETON-3 | 单元测试：UIListEvent index | `list.d.ts:668` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | getItemRectInGroup | 返回分组内子项 RectResult | @since 11 | AC-1.1 |
| R-2 | 行为 | scrollToItemInGroup | 滚到分组内子项 | @since 11 | AC-1.2 |
| R-3 | 行为 | getVisibleListContentInfo | 返回可见内容信息 | @since 14 | AC-1.3 |
| R-4 | 边界 | index 越界 | 默认/空结果 | — | AC-1.4 |
| R-5 | 行为 | 继承 Scroller 方法 | 经 ScrollableController 复用 | — | AC-1.5 |
| R-6 | 行为 | closeAllSwipeActions(options?) | 收起所有 ListItem 滑动；onFinish 回调 | @since 11；CloseSwipeActionOptions 类型见 Feat-07 | AC-2.1~2.3 |
| R-7 | 边界 | onScroll(弃用) | 触发但建议迁移 | @since 7，弃用 12 | AC-3.1 |
| R-8 | 行为 | onScrollIndex(start,end,center?) | 可见索引变化 | center @since 19 | AC-3.2 |
| R-9 | 行为 | onScrollVisibleContentChange | 可见内容变化 | @since 12 | AC-3.3 |
| R-10 | 行为 | onReachStart/onReachEnd | 到首尾 | @since 7 | AC-3.4 |
| R-11 | 行为 | onScrollStart | 滚动开始 | @since 9 | AC-3.5 |
| R-12 | 行为 | onScrollStop | 滚动停止 | @since 7 | AC-3.6 |
| R-13 | 行为 | onScrollFrameBegin | 帧前触发 | @since 9/@20 | AC-3.7 |
| R-14 | 行为 | UIListEvent.setOnWillScroll/setOnDidScroll/setOnScrollIndex/setOnScrollVisibleContentChange | 程序化绑定 | @since 19 | AC-4.1, AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5 控制器查询 | 单元测试 | rect/group/visible/越界/继承 |
| VM-2 | R-6 closeAllSwipeActions | 单元测试 | 收起与 onFinish |
| VM-3 | R-7~R-13 滚动事件 | 单元测试 | 弃用/index/visible/reach/start/stop/frame |
| VM-4 | R-14 UIListEvent | 单元测试 | 程序化绑定 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `ListScroller.getItemRectInGroup(index, indexInGroup)` | Public（@since 11） | `number, number` | `RectResult` | 无 | 分组内子项矩形 | AC-1.1 |
| `ListScroller.scrollToItemInGroup(index, indexInGroup, smooth?, align?)` | Public（@since 11） | `number, number, boolean?, ScrollAlign?` | `void` | 无 | 滚到分组内子项 | AC-1.2 |
| `ListScroller.getVisibleListContentInfo(x, y)` | Public（@since 14） | `number, number` | `VisibleListContentInfo` | 无 | 可见内容信息 | AC-1.3 |
| `ListScroller.closeAllSwipeActions(options?)` | Public（@since 11） | `CloseSwipeActionOptions?` | `void` | 无 | 关闭所有滑动 | AC-2.1 |
| `onScrollIndex/onScrollVisibleContentChange/onReachStart/onReachEnd/onScrollStart/onScrollStop/onScrollFrameBegin` | Public | 各回调 | `ListAttribute` | 无 | 滚动事件 | AC-3.x |
| `UIListEvent.setOnWillScroll/setOnDidScroll/setOnScrollIndex/setOnScrollVisibleContentChange` | Public（@since 19） | 程序化回调 | — | 无 | 程序化事件 | AC-4.1, AC-4.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `onScroll` | 废弃 since 12 | 滚动通知 | 迁移至 `onDidScroll` | AC-3.1 |

## 接口规格

### 接口定义

**ListScroller.getItemRectInGroup(index, indexInGroup)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ListScroller::getItemRectInGroup(index: number, indexInGroup: number): RectResult` |
| 返回值 | `RectResult` |
| 开放范围 | Public（@since 11） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| index | `number` | 是 | — | 分组索引 |
| indexInGroup | `number` | 是 | — | 组内子项索引；越界返回默认 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 index | 返回 RectResult | AC-1.1 |
| 2 | 越界 | 默认/空 | AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 是 — onScroll 弃用 12→onDidScroll
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** onScroll/onReachStart/End/onScrollStop @7；onScrollStart/onScrollFrameBegin @9；getItemRectInGroup/scrollToItemInGroup/closeAllSwipeActions @11；onScrollVisibleContentChange @12；getVisibleListContentInfo @14；onScrollIndex center/UIListEvent @19
- **API 版本号策略:** 各方法标注 @since；onScroll 弃用 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 控制器经 ListPositionController: ScrollableController | 抽象复用 | AC-1.x |
| closeAllSwipeActions 跨 Feat | 方法在本 Feat，类型 CloseSwipeActionOptions 在 Feat-07 | AC-2.1~2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 控制器查询 O(1) | 单元测试 | `list_position_map.h` |
| 可测试性 | 控制器/事件可单测 | 单元测试 | TASK-SKELETON-3 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 滚动动作无障碍 | AC-1.x |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | onScroll 弃用 12；@7~19 门槛 | AC-3.1, AC-3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（控制器/事件；滑动操作在 Feat-07）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ListPositionController getItemRectInGroup/scrollToItemInGroup/getVisibleListContentInfo 与 ListPositionMap 实现"
```

**关键文档:** `list.d.ts`、`list_position_controller.h/.cpp`、`list_position_map.h`、`list_event_hub.h`、`design.md`
