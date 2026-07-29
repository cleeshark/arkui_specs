# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | List 选择与编辑模式 |
| 特性编号 | Func-05-03-05-Feat-05 |
| 优先级 | P2 |
| 目标版本 | API 7 ~ 26+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 ListItem selectable/selected/onSelect、List multiSelectable/editModeOptions(@23)/enableEditMode(@26)/onEditModeChange(@26)，及弃用 editMode/ListItem.sticky/ListItem.editable + Sticky/EditMode 枚举。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md` |
| SDK Dynamic | `ets/dynamic/component/list.d.ts` + `list_item.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/list/list_pattern.cpp` + `list_item_pattern.cpp` |
| BasePattern | `frameworks/core/components_ng/pattern/scrollable/selectable_container_pattern.h` |
| EventHub | `frameworks/core/components_ng/pattern/list/list_item_event_hub.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 单项选择

作为**应用开发者**，我想要**用 selectable/selected/onSelect 支持单项选择**，以便**点击高亮选中项**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `ListItemAttribute.selectable(true)`（@since 8） THEN 该项可被选中 | 正常 |
| AC-1.2 | WHEN 设置 `ListItemAttribute.selected(boolean)`（@since 10） THEN 控制选中态 | 正常 |
| AC-1.3 | WHEN 点击可选项 THEN `onSelect(isSelected: boolean)` 触发（@since 8） | 正常 |
| AC-1.4 | WHEN selectable=false THEN 不可选中，onSelect 不触发 | 边界 |

### US-2: 多选与编辑模式

作为**应用开发者**，我想要**用 multiSelectable/enableEditMode 支持多选与编辑**，以便**批量操作**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `ListAttribute.multiSelectable(true)`（@since 8） THEN 启用多选 | 正常 |
| AC-2.2 | WHEN 设置 `ListAttribute.enableEditMode(boolean)`（@since 26） THEN 进入/退出编辑模式 | 正常 |
| AC-2.3 | WHEN 设置 `ListAttribute.editModeOptions(EditModeOptions?)`（@since 23） THEN 编辑模式配置 | 正常 |
| AC-2.4 | WHEN 编辑模式状态变化 THEN `onEditModeChange(callback)`（@since 26） 触发 | 正常 |
| AC-2.5 | WHEN 使用 `editMode(boolean)`（@since 7 弃用 9） THEN 仍生效但建议迁移 enableEditMode | 边界 |
| AC-2.6 | WHEN 使用 `ListItemAttribute.editable(boolean|EditMode)`（@since 7 弃用 9） THEN 不生效，迁移至 List | 边界 |

### US-3: 弃用枚举

作为**应用开发者**，我想要**了解弃用枚举迁移**，以便**避免使用废弃 API**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 使用 `enum Sticky`（@since 7 弃用 9） THEN 迁移至 `StickyStyle` | 边界 |
| AC-3.2 | WHEN 使用 `enum EditMode`（@since 7 弃用 9） THEN 迁移至 `EditModeOptions` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-5 | 单元测试：selectable | `list_item.d.ts:862` |
| AC-1.2 | R-2 | TASK-SKELETON-5 | 单元测试：selected | `list_item.d.ts:888` |
| AC-1.3 | R-3 | TASK-SKELETON-5 | 单元测试：onSelect | `list_item.d.ts:957` |
| AC-1.4 | R-1 | TASK-SKELETON-5 | 单元测试：selectable false | `list_item.d.ts:862` |
| AC-2.1 | R-4 | TASK-SKELETON-5 | 单元测试：multiSelectable | `list.d.ts:1963` |
| AC-2.2 | R-5 | TASK-SKELETON-5 | 单元测试：enableEditMode | `list.d.ts:2348` |
| AC-2.3 | R-6 | TASK-SKELETON-5 | 单元测试：editModeOptions | `list.d.ts:2334` |
| AC-2.4 | R-7 | TASK-SKELETON-5 | 单元测试：onEditModeChange | `list.d.ts:2361` |
| AC-2.5 | R-8 | TASK-SKELETON-5 | 单元测试：editMode 弃用 | `list.d.ts:1921` |
| AC-2.6 | R-8 | TASK-SKELETON-5 | 单元测试：editable 弃用 | `list_item.d.ts:822` |
| AC-3.1 | R-9 | TASK-SKELETON-5 | 单元测试：Sticky 弃用 | `list_item.d.ts:29` |
| AC-3.2 | R-9 | TASK-SKELETON-5 | 单元测试：EditMode 弃用 | `list_item.d.ts:67` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | selectable(true/false) | 可选/不可选；false 不触发 onSelect | @since 8 | AC-1.1, AC-1.4 |
| R-2 | 行为 | selected(boolean) | 控制选中态 | @since 10 | AC-1.2 |
| R-3 | 行为 | 点击可选项 | onSelect(isSelected) 触发 | @since 8 | AC-1.3 |
| R-4 | 行为 | multiSelectable(true) | 启用多选 | @since 8 | AC-2.1 |
| R-5 | 行为 | enableEditMode(boolean) | 进入/退出编辑模式 | @since 26 | AC-2.2 |
| R-6 | 行为 | editModeOptions(EditModeOptions) | 编辑模式配置 | @since 23 | AC-2.3 |
| R-7 | 行为 | onEditModeChange(callback) | 编辑模式变化回调 | @since 26 | AC-2.4 |
| R-8 | 边界 | editMode/ListItem.editable(弃用) | 不生效/迁移 | 弃用 @since 9 | AC-2.5, AC-2.6 |
| R-9 | 边界 | enum Sticky/EditMode(弃用) | 迁移至 StickyStyle/EditModeOptions | 弃用 @since 9 | AC-3.1, AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-3 单项选择 | 单元测试 | selectable/selected/onSelect |
| VM-2 | R-4~R-7 多选编辑 | 单元测试 | multiSelectable/enableEditMode/options/change |
| VM-3 | R-8~R-9 弃用 | 单元测试 | editMode/editable/Sticky/EditMode |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `ListItemAttribute.selectable(value)` | Public（@since 8） | `boolean` | `ListItemAttribute` | 无 | 可选 | AC-1.1 |
| `ListItemAttribute.selected(value)` | Public（@since 10） | `boolean` | `ListItemAttribute` | 无 | 选中态 | AC-1.2 |
| `ListItemAttribute.onSelect(event)` | Public（@since 8） | `(isSelected: boolean)=>void` | `ListItemAttribute` | 无 | 选中回调 | AC-1.3 |
| `ListAttribute.multiSelectable(value)` | Public（@since 8） | `boolean` | `ListAttribute` | 无 | 多选 | AC-2.1 |
| `ListAttribute.enableEditMode(enabled)` | Public（@since 26） | `boolean\|undefined` | `ListAttribute` | 无 | 编辑模式 | AC-2.2 |
| `ListAttribute.editModeOptions(options?)` | Public（@since 23） | `EditModeOptions?` | `ListAttribute` | 无 | 编辑配置 | AC-2.3 |
| `ListAttribute.onEditModeChange(callback)` | Public（@since 26） | `Callback<boolean>\|undefined` | `ListAttribute` | 无 | 编辑变化 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ListAttribute.editMode` | 废弃 since 9 | 编辑模式 | 迁移至 `enableEditMode`(@26) | AC-2.5 |
| `ListItemAttribute.editable` | 废弃 since 9 | 项编辑 | 迁移至 `ListAttribute#enableEditMode` | AC-2.6 |
| `enum Sticky` | 废弃 since 9 | ListItem 吸附 | 迁移至 `StickyStyle` | AC-3.1 |
| `enum EditMode` | 废弃 since 9 | 编辑枚举 | 迁移至 `EditModeOptions` | AC-3.2 |

## 接口规格

### 接口定义

**enableEditMode(enabled)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ListAttribute::enableEditMode(enabled: boolean\|undefined): ListAttribute` |
| 返回值 | `ListAttribute` |
| 开放范围 | Public（@since 26） |
| 错误码 | N/A |
| 关联 AC | AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enabled | `boolean\|undefined` | 是 | — | 进入/退出编辑；undefined 重置 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | true | 进入编辑模式 | AC-2.2 |
| 2 | false | 退出 | AC-2.2 |
| 3 | 变化 | onEditModeChange 触发 | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是 — editMode/ListItem.editable/Sticky/EditMode 弃用 9
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** selectable/multiSelectable/onSelect @8；selected @10；editModeOptions @23；enableEditMode/onEditModeChange @26
- **API 版本号策略:** 各属性标注 @since；弃用迁移

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 选择基类 SelectableContainerPattern | ListPattern 继承 | AC-1.x~2.x |
| 编辑模式上移至 List | ListItem.editable 弃用 | AC-2.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 选择状态切换单帧 | 单元测试 | `selectable_container_pattern.h` |
| 可测试性 | 选择/编辑可单测 | 单元测试 | TASK-SKELETON-5 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 选中态无障碍 | AC-1.x |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | editMode 等弃用 9；@23/26 门槛 | AC-2.5~2.6, AC-3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（选择编辑；拖拽在 Feat-06）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SelectableContainerPattern 选择基类与 enableEditMode/onEditModeChange 编辑模式状态"
```

**关键文档:** `list.d.ts`、`list_item.d.ts`、`selectable_container_pattern.h`、`design.md`
