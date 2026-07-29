# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 拖拽 |
| 特性编号 | Func-05-03-05-Feat-06 |
| 优先级 | P2 |
| 目标版本 | API 7 ~ 8+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 onItemDragStart(@8)/onItemDragEnter/onItemDragMove/onItemDragLeave/onItemDrop/onItemMove，及弃用 onItemDelete。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md` |
| SDK Dynamic | `ets/dynamic/component/list.d.ts` |
| DragManager | `frameworks/core/components_ng/pattern/list/list_item_drag_manager.h/.cpp` |
| EventHub | `frameworks/core/components_ng/pattern/list/list_event_hub.h` |
| Pattern Source | `frameworks/core/components_ng/pattern/list/list_pattern.cpp` |
| C-API | `frameworks/core/interfaces/native/node/node_list_modifier.cpp` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 拖拽起止与移动

作为**应用开发者**，我想要**用 onItemDragStart/onItemDragEnter/Move/Leave/onItemDrop 接收拖拽事件**，以便**实现拖拽排序/跨列表拖拽**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 开始拖拽列表项 THEN `onItemDragStart(callback)`（@since 8/@23 rectify） 触发，返回拖拽内容 | 正常 |
| AC-1.2 | WHEN 拖拽进入列表 THEN `onItemDragEnter(event: ItemDragInfo, itemIndex)` 触发 | 正常 |
| AC-1.3 | WHEN 拖拽在列表内移动 THEN `onItemDragMove(event, itemIndex, insertIndex)` 触发 | 正常 |
| AC-1.4 | WHEN 拖拽离开列表 THEN `onItemDragLeave(event, itemIndex)` 触发 | 正常 |
| AC-1.5 | WHEN 拖拽放下 THEN `onItemDrop(event, itemIndex, insertIndex, isSuccess)` 触发 | 正常 |
| AC-1.6 | WHEN 拖拽到非法位置 THEN insertIndex 为 -1，isSuccess=false | 边界 |
| AC-1.7 | WHEN 未注册 onItemDragStart THEN 拖拽不产生内容 | 边界 |

### US-2: 拖拽排序

作为**应用开发者**，我想要**用 onItemMove 接受项内排序**，以便**列表内重排**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 列表内拖拽项排序 THEN `onItemMove(from, to): boolean`（@since 7） 触发，返回 true 表示接受排序 | 正常 |
| AC-2.2 | WHEN onItemMove 返回 false THEN 拒绝排序，项回原位 | 边界 |
| AC-2.3 | WHEN 使用 `onItemDelete(index): boolean`（@since 7 弃用 9） THEN 仍触发但建议迁移 onItemMove | 边界 |
| AC-2.4 | WHEN C-API 注册 SetOnItemMove/SetOnItemDragStart/Enter/Move/Leave/Drop THEN 事件经 node_list_modifier 触发 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-6 | 单元测试：onItemDragStart | `list.d.ts:2721` |
| AC-1.2 | R-2 | TASK-SKELETON-6 | 单元测试：onItemDragEnter | `list.d.ts:2750` |
| AC-1.3 | R-3 | TASK-SKELETON-6 | 单元测试：onItemDragMove | `list.d.ts:2779` |
| AC-1.4 | R-4 | TASK-SKELETON-6 | 单元测试：onItemDragLeave | `list.d.ts:2808` |
| AC-1.5 | R-5 | TASK-SKELETON-6 | 单元测试：onItemDrop | `list.d.ts:2839` |
| AC-1.6 | R-5 | TASK-SKELETON-6 | 单元测试：非法位置 | `list_item_drag_manager.cpp` |
| AC-1.7 | R-1 | TASK-SKELETON-6 | 单元测试：未注册 | `list_pattern.cpp` |
| AC-2.1 | R-6 | TASK-SKELETON-6 | 单元测试：onItemMove | `list.d.ts:2679` |
| AC-2.2 | R-6 | TASK-SKELETON-6 | 单元测试：返回 false | `list.d.ts:2679` |
| AC-2.3 | R-7 | TASK-SKELETON-6 | 单元测试：onItemDelete 弃用 | `list.d.ts:2650` |
| AC-2.4 | R-8 | TASK-SKELETON-6 | 单元测试：C-API | `node_list_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | onItemDragStart | 返回拖拽内容；未注册不产生内容 | @since 8/@23 | AC-1.1, AC-1.7 |
| R-2 | 行为 | onItemDragEnter | 拖入触发 itemIndex | — | AC-1.2 |
| R-3 | 行为 | onItemDragMove | 移动触发 insertIndex | — | AC-1.3 |
| R-4 | 行为 | onItemDragLeave | 离开触发 | — | AC-1.4 |
| R-5 | 行为 | onItemDrop | 放下触发 isSuccess；非法位置 insertIndex=-1,isSuccess=false | — | AC-1.5, AC-1.6 |
| R-6 | 行为 | onItemMove(from,to) | 返回 true 接受/false 拒绝 | @since 7 | AC-2.1, AC-2.2 |
| R-7 | 边界 | onItemDelete(弃用) | 仍触发，建议迁移 | 弃用 @since 9 | AC-2.3 |
| R-8 | 行为 | C-API SetOnItemMove/DragStart/Enter/Move/Leave/Drop | node_list_modifier 触发 | — | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5 拖拽起止移动 | 单元测试 | start/enter/move/leave/drop |
| VM-2 | R-6~R-7 排序与弃用 | 单元测试 | onItemMove/onItemDelete |
| VM-3 | R-8 C-API | 单元测试 | node modifier 事件 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `onItemDragStart(callback)` | Public（@since 8/@23） | `OnItemDragStartCallback` | `ListAttribute` | 无 | 拖拽开始 | AC-1.1 |
| `onItemDragEnter(event)` | Public（@since 8） | `(ItemDragInfo, itemIndex)=>void` | `ListAttribute` | 无 | 拖入 | AC-1.2 |
| `onItemDragMove(event)` | Public（@since 8） | `(ItemDragInfo, itemIndex, insertIndex)=>void` | `ListAttribute` | 无 | 移动 | AC-1.3 |
| `onItemDragLeave(event)` | Public（@since 8） | `(ItemDragInfo, itemIndex)=>void` | `ListAttribute` | 无 | 离开 | AC-1.4 |
| `onItemDrop(event)` | Public（@since 8） | `(ItemDragInfo, itemIndex, insertIndex, isSuccess)=>void` | `ListAttribute` | 无 | 放下 | AC-1.5 |
| `onItemMove(event)` | Public（@since 7） | `(from, to)=>boolean` | `ListAttribute` | 无 | 项内排序 | AC-2.1 |
| C-API `SetOnItemMove/SetOnItemDragStart/Enter/Move/Leave/Drop` | Public | 事件枚举 | — | 无 | NDK 拖拽 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `onItemDelete` | 废弃 since 9 | 项删除事件 | 迁移至 `onItemMove` | AC-2.3 |

## 接口规格

### 接口定义

**onItemMove(event)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ListAttribute::onItemMove(event: (from: number, to: number) => boolean): ListAttribute` |
| 返回值 | `ListAttribute` |
| 开放范围 | Public（@since 7） |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| from | `number` | 是 | — | 源索引 |
| to | `number` | 是 | — | 目标索引 |
| 返回 | `boolean` | — | — | true 接受/false 拒绝 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 列表内排序 | 触发 onItemMove | AC-2.1 |
| 2 | 返回 false | 拒绝回原位 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 是 — onItemDelete 弃用 9→onItemMove
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** onItemMove/onItemDelete @7；onItemDrag* @8；onItemDragStart rectify @23
- **API 版本号策略:** 各事件标注 @since；onItemDelete 弃用

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ListItemDragManager | 拖拽实现 | AC-1.x~2.x |
| onItemMove 返回值控制 | true/false 接受拒绝 | AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 拖拽排序单帧 | 单元测试 | `list_item_drag_manager.cpp` |
| 可测试性 | 拖拽事件可单测 | 单元测试 | TASK-SKELETON-6 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准拖拽 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 拖拽不影响无障碍 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | onItemDelete 弃用 9 | AC-2.3 |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（拖拽；滑动操作在 Feat-07）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ListItemDragManager 拖拽事件触发时序与 onItemMove 接受/拒绝控制"
```

**关键文档:** `list.d.ts`、`list_item_drag_manager.h/.cpp`、`list_event_hub.h`、`design.md`
