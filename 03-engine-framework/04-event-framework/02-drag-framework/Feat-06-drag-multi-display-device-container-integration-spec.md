# 特性规格

## 概览

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽多显示设备与容器集成 |
| 特性编号 | Func-03-04-02-Feat-06 |
| 所属 Epic | 03-engine-framework / 04-event-framework / 02-drag-framework |
| 优先级 | P1 |
| 目标版本 | 存量实现补录 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 多显示坐标、容器、窗口和系统拖拽窗口交接的规格 | 补录现有实现；不改变 ArkTS、C API 或 MSDP 行为。 |

## 输入文档

- `specs/03-engine-framework/04-event-framework/02-drag-framework/design.md`
- `docs/common/interaction/Drag_Drop_Knowledge_Base_CN.md`
- `frameworks/core/event/pointer_event.h:72-162`
- `adapter/ohos/entrance/ace_view_ohos.cpp:376-425`
- `frameworks/core/pipeline_ng/pipeline_context.cpp:6248-6281`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_manager.cpp:277-303,322-339,832-910,1097-1171,2318-2358,2517-2562,2645-2656,2814-2819,3348-3354,3541-3564`

## 用户故事

### US-1: 保留跨显示位置上下文

作为拖拽目标开发者，我希望系统事件在跨窗口和显示器时保留窗口、显示器及全局显示坐标，以便命中和回调使用同一事件上下文。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN `AceViewOhos` 接收 MMI pull-in、move、out、up、cancel 或 throw 事件，THEN 它转换为 `DragPointerEvent` 并按对应 `DragEventAction` 转交回调。 | 正常 |
| AC-1.2 | WHEN `DragPointerEvent` 带有窗口坐标、显示器坐标、全局显示坐标和 `displayId`，THEN 管理器更新事件时保留这些字段并将它们提供给拖拽事件。 | 正常 |

### US-2: 在不同容器中维持目标和预览

作为多窗口应用开发者，我希望 SceneBoard、UIExtension 和子窗口的拖拽使用正确的根节点、容器和预览承载。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 拖拽源所在容器是 SceneBoard 窗口，THEN 项目拖拽预览挂载到源节点所属 `WindowScene`，并把该场景设为管理器根节点。 | 正常 |
| AC-2.2 | WHEN 当前容器是 UIExtension 或 SceneBoard，THEN 管理器不清空上一目标节点；WHEN 普通子容器重新进入，THEN 管理器恢复框架预览状态后再清空上一目标。 | 边界 |
| AC-2.3 | WHEN 当前子窗口未启用接收拖拽事件，THEN pull-out 不执行离窗处理，且起拖动画从主 Pipeline 取得 VSync 时间。 | 边界 |

### US-3: 在窗口边界交接系统拖拽窗口

作为系统拖拽集成方，我希望 ArkUI 预览与 MSDP 的系统拖拽窗口在离窗和边界条件下明确交接。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 拖拽离开当前窗口且需要子窗口承载预览或携带上下文菜单，THEN 管理器派发 Leave、清理摘要/附加信息，并调用交接流程使系统拖拽窗口可见。 | 正常 |
| AC-3.2 | WHEN UIExtension 或文件夹子窗口边界被命中，THEN ArkUI 停止起拖动画并交接到系统拖拽窗口。 | 边界 |
| AC-3.3 | WHEN 管理器交接系统拖拽窗口，THEN 它清理 ArkUI 子窗口预览、使菜单子窗口接收拖拽事件；MSDP 内部拖拽流程不属于 ArkUI 规格。 | 恢复 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | Feat-06 | Adapter/Pipeline 单元测试 | `ace_view_ohos.cpp:376-413`; `pipeline_context.cpp:6248-6275` |
| AC-1.2 | R-2 | Feat-06 | 事件字段断言 | `pointer_event.h:77-95,120-162`; `drag_drop_manager.cpp:2318-2358` |
| AC-2.1 | R-3 | Feat-06 | SceneBoard mock 测试 | `drag_drop_manager.cpp:322-339,742-773` |
| AC-2.2 | R-4 | Feat-06 | 容器分支测试 | `drag_drop_manager.cpp:1160-1171` |
| AC-2.3 | R-5 | Feat-06 | Host 子窗口测试 | `drag_drop_manager_test_ng_plus.cpp:785-876` |
| AC-3.1 | R-6 | Feat-06 | Manager 事件测试 | `drag_drop_manager.cpp:875-910` |
| AC-3.2, AC-3.3 | R-7 | Feat-06 | 边界/交接 mock 测试 | `drag_drop_manager.cpp:832-860,2645-2656,3541-3553` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | MMI 的 pointer action 是 pull move/up/in/out/cancel/throw | Adapter 映射为对应 `DragEventAction` 并调用已注册回调 | 未注册回调时由空检查返回 | AC-1.1 |
| R-2 | 行为 | `DragPointerEvent` 包含 `windowX/windowY`、`displayX/displayY`、`globalDisplayX/globalDisplayY` 和 `displayId` | `UpdateDragEvent` 写入对应 `DragEvent` 字段 | 位置字段由系统事件输入；ArkUI 不推算其他显示器的布局 | AC-1.2 |
| R-3 | 行为 | 当前容器为 SceneBoard 窗口 | 预览选择 `WindowScene` 作为挂载根，并记录该根用于拖拽 | 无有效 host、overlay 或 scene 时按空检查停止当前分支 | AC-2.1 |
| R-4 | 边界 | `ResetPreTargetFrameNode` 接收 UIExtension/SceneBoard 容器 ID，或接收普通子容器 ID | 前者保留上一目标；后者把 `isDragFwkShow_` 置为 true 后清空上一目标 | 子容器判定为 `instanceId > MIN_SUBCONTAINER_ID` | AC-2.2 |
| R-5 | 边界 | 当前容器 ID 不小于 `MIN_SUBCONTAINER_ID` 且菜单子窗口未接收拖拽事件 | 跳过 move-out；起拖动画取主 Pipeline 的 VSync | 子窗口不存在或接收事件时不跳过 | AC-2.3 |
| R-6 | 行为 | 收到离窗事件且存在上一目标 | 派发 Leave、清除摘要和附加信息；当缩放预览/聚合节点或上下文菜单需要时调用交接 | 不定义 MSDP 对可见系统拖拽窗口后的内部处理 | AC-3.1 |
| R-7 | 恢复 | 交接发生，或 UIExtension/文件夹子窗口边界被命中 | ArkUI 关闭起拖动画并清理子窗口预览；调用 `InteractionInterface::SetDragWindowVisible(true)`，菜单子窗口改为接收事件 | 系统拖拽会话由 MSDP 所有，ArkUI 仅通过 `InteractionInterface` 对接 | AC-3.2、AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-2 | Adapter 与事件对象单测 | action 映射、坐标和 `displayId` 保留 |
| VM-2 | R-3、R-4 | SceneBoard/UIExtension mock 测试 | 根节点和上一目标状态 |
| VM-3 | R-5 | `DoDragStartAnimationVsyncTime002` | 子窗口不接收事件时使用主 Pipeline VSync |
| VM-4 | R-6、R-7 | Manager/InteractionInterface mock 测试 | Leave、预览清理和系统窗口可见性交接 |

## API 变更分析

### 新增 API

无。本 Feat 仅补录内部事件与容器集成，不新增 ArkTS、C API、UIContext 或 DragController API。

### 变更/废弃 API

无。`DragPointerEvent` 的显示器字段是内部事件数据；公开接口的版本可用性不因本 Feat 改变。

## 接口规格

### 接口定义

| 接口 | 开放范围 | 参数约束 | 行为场景 |
|---|---|---|---|
| `PipelineContext::OnDragEvent(const DragPointerEvent&, DragEventAction, const RefPtr<FrameNode>&)` | InnerApi | 需存在 `DragDropManager`；`node` 可作为当前命中根 | 分发系统拖拽事件并在 MOVE 请求帧，AC-1.1 |
| `DragDropManager::TransDragWindowToDragFwk(int32_t)` | InnerApi | 只在尚未完成交接时执行；参数为窗口容器 ID | 使 MSDP 拖拽窗口可见并回收 ArkUI 子窗口预览，AC-3.1、AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文件为存量实现补录。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 不适用；没有本 Feat 独立的公开 API。
- **API 版本号策略:** 动态/静态 ArkTS、C API、UIContext 和 DragController 的既有 `@since` 不因内部多显示/容器交接改变；公开事件字段的契约以各 SDK 类型定义为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 系统事件入口 | MMI 事件必须经 `AceViewOhos` 和 `PipelineContext` 进入 Manager，不以 `DragDropProxy` 取代主系统事件链。 | AC-1.1 |
| 坐标保真 | 窗口、显示器、全局显示坐标及目标显示 ID 必须作为同一 `DragPointerEvent` 上下文传递。 | AC-1.2 |
| 容器归属 | 子窗口 overlay 通过父容器取得菜单子窗口；SceneBoard 使用 `WindowScene` 根。 | AC-2.1、AC-2.3 |
| MSDP 边界 | ArkUI 仅经 `InteractionInterface` 交接系统窗口；不定义 MSDP 内部会话行为。 | AC-3.1~AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | 未找到容器、Pipeline、overlay 或子窗口时提前返回，不继续访问空对象。 | Host/mock 覆盖 | `drag_drop_manager.cpp:280-303,3348-3354` |
| 可测试性 | 子窗口未接收事件时主 Pipeline VSync 路径可由 Host 单测验证。 | `DoDragStartAnimationVsyncTime002` | `drag_drop_manager_test_ng_plus.cpp:785-876` |
| 定界定位 | 使用窗口 ID、pointer event ID 和目标节点日志定位跨窗口目标切换。 | 日志审查 | `drag_drop_manager.cpp:789-809` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 单窗口或普通子窗口按事件中的窗口/显示器坐标处理。 | 不虚构跨显示 API。 | Manager mock | `pointer_event.h:77-95` |
| 平板/外接显示 | 使用系统输入提供的 `displayId` 与全局显示坐标；目标解析仍在当前容器内完成。 | 显示器拓扑由系统侧提供。 | Adapter/Manager 集成测试 | `ace_view_ohos.cpp:376-413`; `drag_drop_manager.cpp:2340-2358` |
| 折叠屏 | 折叠状态会影响文件夹子窗口边界路径；扩展状态不走该边界条件。 | 仅陈述现有 `FoldStatus::EXPAND` 分支。 | 边界 mock | `drag_drop_manager.cpp:3517-3539` |
| UIExtension/SceneBoard | 有专用根节点、目标复位和边界交接分支。 | 不与普通窗口分支混用。 | 容器 mock | `drag_drop_manager.cpp:742-773,1160-1171,3541-3564` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 否 | 本 Feat 未新增无障碍节点或语义。 | N/A |
| 大字体 | 否 | 未改变文本/布局属性。 | N/A |
| 深色模式 | 否 | 未新增颜色或主题决策。 | N/A |
| 多窗口/分屏 | 是 | SceneBoard、子窗口、UIExtension 和系统窗口交接属于本 Feat 范围。 | AC-2.1~AC-3.3 |
| 多用户 | 否 | 未在 ace_engine 中发现本 Feat 专用多用户分支。 | N/A |
| 版本升级 | 是 | 仅标注既有公开 API 版本不因本内部集成而改变。 | 兼容性声明 |
| 生态兼容 | 是 | 系统拖拽会话语义仍由 MSDP 负责，ArkUI 保持 `InteractionInterface` 边界。 | AC-3.3 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽多显示设备与容器集成
  作为多窗口和多显示设备上的 ArkUI 拖拽使用者
  我希望事件坐标、命中目标和预览窗口在容器变化时保持可追踪
  以便系统拖拽与 ArkUI 预览在正确边界交接

  Scenario: 子窗口未接收拖拽事件时的动画时钟
    Given 当前容器是菜单子窗口且 ReceiveDragEventEnabled 为 false
    When 管理器执行起拖动画
    Then 起拖 VSync 时间来自主 Pipeline
    And pull-out 事件不执行离窗处理

  Scenario: UIExtension 边界交接
    Given 当前容器是 UIExtension
    When 拖拽移动到当前窗口边界距离内
    Then ArkUI 停止起拖动画并交接系统拖拽窗口
    And ArkUI 子窗口预览被清理
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 明确排除 MSDP 内部拖拽会话和新增跨显示公开 API。
- [x] 每个 AC 至少关联一条规则和一种验证方式。
- [x] 规则表包含可复现触发条件、可观察结果、边界、AC 映射且无冲突。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "DragPointerEvent coordinates, SceneBoard/UIExtension/subwindow routing, and InteractionInterface drag-window handoff"
```
