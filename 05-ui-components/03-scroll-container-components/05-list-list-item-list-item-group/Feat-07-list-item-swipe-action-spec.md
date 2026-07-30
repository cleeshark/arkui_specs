# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ListItem 滑动操作 |
| 特性编号 | Func-05-03-05-Feat-07 |
| 优先级 | P1 |
| 目标版本 | API 9 ~ 26+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 ListItem swipeAction(SwipeActionOptions)、SwipeActionItem、SwipeEdgeEffect/SwipeActionState/ListItemSwipeActionDirection、ListItemSwipeActionManager(expand/collapse)、ListScroller.closeAllSwipeActions 选项类型 CloseSwipeActionOptions、ListBackPressBehavior.closeSwipeAction 联动，及 ListItemPattern 滑动状态机。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md` |
| SDK Dynamic | `ets/dynamic/component/list_item.d.ts` + `list.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/list/list_item_pattern.h/.cpp` |
| LayoutProperty | `frameworks/core/components_ng/pattern/list/list_item_layout_property.h` |
| EventHub | `frameworks/core/components_ng/pattern/list/list_item_event_hub.h` |
| C-API | `frameworks/core/interfaces/native/implementation/list_item_swipe_action_manager_accessor.cpp` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 配置滑动操作

作为**应用开发者**，我想要**用 swipeAction 配置 ListItem 左右滑动按钮**，以便**显示快捷操作**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `ListItemAttribute.swipeAction({start, end, edgeEffect, onOffsetChange})`（@since 9） THEN 滑动操作生效 | 正常 |
| AC-1.2 | WHEN 设置 SwipeActionOptions.start(SwipeActionItem[]) THEN 起始方向显示操作按钮 | 正常 |
| AC-1.3 | WHEN 设置 SwipeActionOptions.end THEN 末方向显示操作按钮 | 正常 |
| AC-1.4 | WHEN 设置 edgeEffect=SwipeEdgeEffect.Spring THEN 滑出回弹；None 无回弹 | 正常 |
| AC-1.5 | WHEN 设置 onOffsetChange(callback)（@since 11） THEN 滑动偏移实时回调 | 正常 |
| AC-1.6 | WHEN 不设 start/end THEN 该方向无滑动操作 | 边界 |

### US-2: 操作项与区域事件

作为**应用开发者**，我想要**用 SwipeActionItem 配置操作按钮与区域事件**，以便**触发操作/进入区域**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 SwipeActionItem.builder(CustomBuilder)（@since 10/11） THEN 自定义操作按钮 | 正常 |
| AC-2.2 | WHEN 设置 SwipeActionItem.builderComponent(ComponentContent)（@since 18） THEN 运行时内容按钮 | 正常 |
| AC-2.3 | WHEN 设置 SwipeActionItem.actionAreaDistance THEN 进入操作区域距离阈值生效 | 正常 |
| AC-2.4 | WHEN 进入操作区域 THEN onAction/onEnterActionArea 触发 | 正常 |
| AC-2.5 | WHEN 离开操作区域 THEN onExitActionArea 触发 | 正常 |
| AC-2.6 | WHEN 滑动状态变化 THEN onStateChange(SwipeActionState: COLLAPSED/EXPANDED/ACTIONING)（@since 11） 触发 | 正常 |

### US-3: 程序化控制滑动

作为**应用开发者**，我想要**用 ListItemSwipeActionManager 程序化展开/收起滑动**，以便**联动外部控制**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 `ListItemSwipeActionManager.expand(node, direction)`（@since 21） THEN 展开指定方向滑动 | 正常 |
| AC-3.2 | WHEN 调用 `ListItemSwipeActionManager.collapse(node)`（@since 21） THEN 收起滑动 | 正常 |
| AC-3.3 | WHEN 调用 `ListScroller.closeAllSwipeActions(options?)`（方法见 Feat-03，@since 11） THEN 收起所有项滑动，CloseSwipeActionOptions.onFinish 回调 | 正常 |
| AC-3.4 | WHEN 设置 `ListAttribute.backPressBehavior({closeSwipeAction: true})`（@since 26） THEN 系统返回键收起滑动（行为定义在 Feat-02） | 正常 |
| AC-3.5 | WHEN 滑动方向设置 ListItemSwipeActionDirection.START/END（@since 21） THEN 方向控制 | 正常 |
| AC-3.6 | WHEN 无展开滑动调用 collapse THEN 无操作 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-7 | 单元测试：swipeAction | `list_item.d.ts:917` |
| AC-1.2 | R-2 | TASK-SKELETON-7 | 单元测试：start | `list_item.d.ts:491` |
| AC-1.3 | R-2 | TASK-SKELETON-7 | 单元测试：end | `list_item.d.ts:491` |
| AC-1.4 | R-3 | TASK-SKELETON-7 | 单元测试：edgeEffect | `list_item.d.ts:121` |
| AC-1.5 | R-4 | TASK-SKELETON-7 | 单元测试：onOffsetChange | `list_item.d.ts:491` |
| AC-1.6 | R-2 | TASK-SKELETON-7 | 单元测试：无 start/end | `list_item_pattern.cpp` |
| AC-2.1 | R-5 | TASK-SKELETON-7 | 单元测试：builder | `list_item.d.ts:333` |
| AC-2.2 | R-5 | TASK-SKELETON-7 | 单元测试：builderComponent | `list_item.d.ts:333` |
| AC-2.3 | R-6 | TASK-SKELETON-7 | 单元测试：actionAreaDistance | `list_item.d.ts:333` |
| AC-2.4 | R-6 | TASK-SKELETON-7 | 单元测试：onAction/onEnter | `list_item.d.ts:333` |
| AC-2.5 | R-6 | TASK-SKELETON-7 | 单元测试：onExitActionArea | `list_item.d.ts:333` |
| AC-2.6 | R-7 | TASK-SKELETON-7 | 单元测试：onStateChange | `list_item.d.ts:188` |
| AC-3.1 | R-8 | TASK-SKELETON-7 | 单元测试：expand | `list_item.d.ts:299` |
| AC-3.2 | R-8 | TASK-SKELETON-7 | 单元测试：collapse | `list_item.d.ts:313` |
| AC-3.3 | R-9 | TASK-SKELETON-7 | 单元测试：closeAllSwipeActions | `list.d.ts:992` + `list.d.ts:735` CloseSwipeActionOptions |
| AC-3.4 | R-10 | TASK-SKELETON-7 | 单元测试：backPress closeSwipe | `list.d.ts:814` |
| AC-3.5 | R-11 | TASK-SKELETON-7 | 单元测试：方向 START/END | `list_item.d.ts:251` |
| AC-3.6 | R-8 | TASK-SKELETON-7 | 单元测试：无展开 collapse | `list_item_pattern.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | swipeAction(SwipeActionOptions) | 滑动操作生效；状态机 SWIPER_START/END/ACTION | @since 9 | AC-1.1 |
| R-2 | 行为 | start/end(SwipeActionItem[]) | 方向操作按钮；不设则该方向无 | — | AC-1.2, AC-1.3, AC-1.6 |
| R-3 | 行为 | edgeEffect(Spring/None) | 滑出回弹/无回弹 | SwipeEdgeEffect | AC-1.4 |
| R-4 | 行为 | onOffsetChange | 偏移实时回调 | @since 11 | AC-1.5 |
| R-5 | 行为 | builder/builderComponent | 自定义/运行时内容按钮 | builder @10/11；builderComponent @18 | AC-2.1, AC-2.2 |
| R-6 | 行为 | actionAreaDistance/onAction/onEnterActionArea/onExitActionArea | 区域距离与进出触发 | — | AC-2.3~2.5 |
| R-7 | 行为 | onStateChange(SwipeActionState) | 状态变化回调 COLLAPSED/EXPANDED/ACTIONING | @since 11 | AC-2.6 |
| R-8 | 行为 | ListItemSwipeActionManager.expand/collapse | 程序化展开/收起；无展开 collapse 无操作 | @since 21 | AC-3.1, AC-3.2, AC-3.6 |
| R-9 | 行为 | ListScroller.closeAllSwipeActions(CloseSwipeActionOptions?) | 收起所有项；onFinish 回调 | 方法在 Feat-03；类型在本 Feat；@since 11 | AC-3.3 |
| R-10 | 行为 | backPressBehavior.closeSwipeAction | 返回键收起滑动（行为 Feat-02） | @since 26 | AC-3.4 |
| R-11 | 行为 | ListItemSwipeActionDirection.START/END | 方向控制 | @since 21 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-4 滑动配置 | 单元测试 | swipeAction/start/end/edgeEffect/onOffset |
| VM-2 | R-5~R-7 操作项与事件 | 单元测试 | builder/区域/状态 |
| VM-3 | R-8~R-11 程序化控制 | 单元测试 | manager/closeAll/backPress/方向 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `ListItemAttribute.swipeAction(value)` | Public（@since 9） | `SwipeActionOptions` | `ListItemAttribute` | 无 | 滑动操作 | AC-1.1 |
| `SwipeActionOptions.start/end/edgeEffect/onOffsetChange` | Public（@since 9/11） | `SwipeActionItem[]?` / `SwipeEdgeEffect?` / `callback?` | — | 无 | 滑动配置 | AC-1.2~1.5 |
| `SwipeActionItem.builder/builderComponent/actionAreaDistance/onAction/onEnterActionArea/onExitActionArea/onStateChange` | Public（@since 10/11/18） | 各类型 | — | 无 | 操作项 | AC-2.1~2.6 |
| `enum SwipeEdgeEffect/SwipeActionState` | Public（@since 9/11） | Spring/None / COLLAPSED/EXPANDED/ACTIONING | — | 无 | 枚举 | AC-1.4, AC-2.6 |
| `enum ListItemSwipeActionDirection` | Public（@since 21） | START/END | — | 无 | 方向枚举 | AC-3.5 |
| `class ListItemSwipeActionManager.expand/collapse` | Public（@since 21） | `(FrameNode, direction)` / `(FrameNode)` | `void` | 无 | 程序化控制 | AC-3.1, AC-3.2 |
| `interface CloseSwipeActionOptions.onFinish?` | Public（@since 11） | `()=>void?` | — | 无 | 收起完成回调（供 ListScroller.closeAllSwipeActions） | AC-3.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无废弃 | — |

## 接口规格

### 接口定义

**swipeAction(value: SwipeActionOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ListItemAttribute::swipeAction(value: SwipeActionOptions): ListItemAttribute` |
| 返回值 | `ListItemAttribute` |
| 开放范围 | Public（@since 9） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.start | `SwipeActionItem[]` | 否 | — | 起始方向操作 |
| value.end | `SwipeActionItem[]` | 否 | — | 末方向操作 |
| value.edgeEffect | `SwipeEdgeEffect` | 否 | Spring | Spring/None |
| value.onOffsetChange | `callback` | 否 | — | @since 11 偏移回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | start/end 设置 | 方向操作按钮 | AC-1.2, AC-1.3 |
| 2 | 不设 | 该方向无 | AC-1.6 |
| 3 | edgeEffect Spring | 回弹 | AC-1.4 |
| 4 | onOffsetChange | 偏移回调 | AC-1.5 |

### 接口定义

**ListItemSwipeActionManager.expand(node, direction)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static ListItemSwipeActionManager::expand(node: FrameNode, direction: ListItemSwipeActionDirection): void` |
| 返回值 | `void` |
| 开放范围 | Public（@since 21） |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| node | `FrameNode` | 是 | — | ListItem 节点 |
| direction | `ListItemSwipeActionDirection` | 是 | — | START/END |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** swipeAction/SwipeEdgeEffect @9；SwipeActionItem/onStateChange/builder @10/11；onOffsetChange @11；builderComponent @18；ListItemSwipeActionManager/ListItemSwipeActionDirection @21；backPressBehavior.closeSwipeAction @26
- **API 版本号策略:** 各属性标注 @since；CloseSwipeActionOptions 类型跨 Feat（方法在 Feat-03）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ListItemPattern 滑动状态机 | SWIPER_START/END/ACTION | AC-1.1~1.6 |
| builder 先删后加契约 | 替换默认 | AC-2.1 |
| CloseSwipeActionOptions 跨 Feat | 类型本 Feat，方法 Feat-03 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 滑动状态机单帧 | 单元测试 | `list_item_pattern.cpp` |
| 内存 | 操作项 builder 按需构建 | 代码审查 | `list_item_pattern.cpp` |
| 可测试性 | 滑动可单测 | 单元测试 | TASK-SKELETON-7 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准滑动 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 滑动操作无障碍可达 | AC-1.x |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | @9~21/26 门槛；ListItemSwipeActionManager @21 | AC-3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（滑动操作；控制器其他方法在 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ListItemPattern 滑动状态机 SWIPER_START/END/ACTION 与 ListItemSwipeActionManager expand/collapse 实现"
```

**关键文档:** `list_item.d.ts`、`list_item_pattern.h/.cpp`、`list_item_event_hub.h`、`design.md`
