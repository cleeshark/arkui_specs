# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽预览覆盖层动画与视觉效果 |
| 特性编号 | Func-03-04-02-Feat-04 |
| 优先级 | P0 |
| 目标版本 | 存量实现；API 11/12/15/19 与动态/静态/C API 差异 |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 预览构建、窗口交接、动画和回收规格 | 不修改既有实现。 |

## 输入文档

- `specs/03-engine-framework/04-event-framework/02-drag-framework/design.md`
- `<OH_ROOT>/docs/zh-cn/application-dev/reference/apis-arkui/arkui-ts/ts-universal-attributes-drag-drop.md`

## 用户故事

### US-1: 构建和显示拖拽预览

作为开发者，我希望使用配置预览或系统回退预览，并在预览不可用时得到可恢复的失败结果。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 起拖需要预览，THEN 按多选 PixelMap、缓存/inspector、配置 PixelMap、自定义节点和文本/鼠标兜底的现有顺序解析。 | 正常 |
| AC-1.2 | WHEN 自定义节点快照最终无法生成缩略图，THEN 起拖失败并执行客户结束清理。 | 异常 |
| AC-1.3 | WHEN Item Overlay 输入为空 PixelMap、非 FrameNode 或缺 render/geometry，THEN 创建失败且不挂载 Overlay。 | 边界 |

### US-2: 窗口交接、动画和回收

作为框架维护者，我希望预览在 Overlay、子窗口和 MSDP 系统窗口之间正确交接。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 预览已解析，THEN 灰化、gather、缩放、角标、材质和尺寸变化效果写入系统拖拽数据。 | 正常 |
| AC-2.2 | WHEN 输入源或动画模式要求交接，THEN 三类预览承载按实现时机转移。 | 正常 |
| AC-2.3 | WHEN 默认动画启动/移动，THEN 使用现有 300ms/30ms spring；WHEN 禁用 ArkUI 动画，THEN 预览相关节点透明。 | 边界 |
| AC-2.4 | WHEN 默认、定制或 follow-hand-morph 落放结束，THEN 移除 Overlay 资源、隐藏对应窗口并完成 StopDrag。 | 恢复 |

## 验收追踪

| AC | 关联规则 | 关联Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.3 | R-1~R-3 | Feat-04 | Host preview/overlay 测试 | `gesture_event_hub_drag.cpp:786` |
| AC-2.1~AC-2.4 | R-4~R-7 | Feat-04 | Manager 动画/清理测试 | `drag_drop_manager.cpp:2845` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 起拖解析预览 | 按现有优先级选择预览源 | 低优先级只在高优先级不可用时使用 | AC-1.1 |
| R-2 | 异常 | 快照或最终缩略图缺失 | 不开始系统拖拽，执行客户结束清理 | 异步快照可重入起拖 | AC-1.2 |
| R-3 | 边界 | Item Overlay 输入无效 | 返回失败且不挂载节点 | FrameNode/render/geometry 是前置条件 | AC-1.3 |
| R-4 | 行为 | 预览成功 | 将视觉选项和 ShadowInfoCore 交 InteractionInterface | 系统窗口负责真实会话显示 | AC-2.1 |
| R-5 | 行为 | Overlay/子窗口/系统窗口交接 | 按触摸、鼠标和动画模式迁移 | 三种承载生命周期不等价 | AC-2.2 |
| R-6 | 边界 | 默认或禁用动画 | 默认 spring；禁用时预览/角标/gather 透明 | 不改变系统会话 | AC-2.3 |
| R-7 | 恢复 | 三类落放结束 | 清理 map/gather/filter/subwindow 并 StopDrag | 清理顺序随模式不同 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1~R-3 | Host 单元测试 | 优先级、快照失败、无效 Overlay |
| VM-2 | R-4~R-6 | Manager/Interaction mock | 选项、交接、动画 |
| VM-3 | R-7 | Host/集成测试 | 资源清理和窗口可见性 |

## API 变更分析

### 新增 API

存量补录：`dragPreview`、`dragPreviewOptions`、C `ArkUI_DragPreviewOption` 不新增签名。

### 变更/废弃 API

标注 API 11 预览/选项、API 12 交互选项、API 15 PreviewConfiguration、API 19 尺寸变化效果及静态/C API 差异。

## 接口规格

### 接口定义

| 接口 | 开放范围 | 参数约束 | 行为场景 |
|---|---|---|---|
| `dragPreview` | Public | CustomBuilder/DragItemInfo/string | 预览来源，AC-1.1 |
| `dragPreviewOptions` | Public | 模式、角标、效果和交互选项 | 视觉映射，AC-2.1 |
| `OH_ArkUI_SetNodeDragPreviewOption` | Public C | 有效 node 与 option | C 预览配置，AC-2.1 |

## 兼容性声明

- **已有 API 行为变更:** 否；补录动态/静态/C API 的不同 `@since`。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 以 SDK `@since` 为准。
- **API 版本号策略:** 标注 11/12/15/19 及静态/C API 差异。

## 架构约束

| 关键约束 | 约束说明 | 影响AC |
|---|---|---|
| 承载边界 | Overlay、子窗口、MSDP 系统窗口分别管理。 | AC-2.2 |
| 资源回收 | 任一路径必须移除预览资源并恢复窗口可见性。 | AC-1.2、AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 默认起拖 300ms、移动 30ms spring | 动画测试 | `drag_drop_manager.cpp:2676-2941` |
| 可靠性 | 快照失败和 StopDrag 失败无资源遗留 | Host/集成测试 | `gesture_event_hub_drag.cpp:1270-1310` |

## 多设备适配声明

触摸、鼠标和 scene-board 的窗口交接时机不同；系统窗口显示由 InteractionInterface 协作。

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 深色模式 | 是 | 材质和预览视觉由现有选项决定。 | AC-2.1 |
| 多窗口/分屏 | 是 | 子窗口和系统窗口交接需保持可见性一致。 | AC-2.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽预览生命周期
  Scenario: 预览快照失败
    Given 自定义预览节点无法生成缩略图
    When 起拖准备结束
    Then 不开始系统拖拽
    And 执行客户结束清理
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN。
- [x] 覆盖预览选择、窗口交接、动画和回收。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "drag preview source resolution, overlay/subwindow/system-window handoff and cleanup"
```
