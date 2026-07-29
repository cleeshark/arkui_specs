# 特性规格

## 概览

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽预览与交互呈现 |
| 特性编号 | Func-04-04-07-Feat-04 |
| 所属 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 优先级 | P1 |
| 目标版本 | 动态 ArkTS API 11/12/15；静态 ArkTS API 23；C API API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 预览来源、`dragPreview`/`dragPreviewOptions`、C PreviewOption、Overlay、多选与动画呈现合同 | 对已有 ArkTS/C API 和渲染实现补录，不改变产品行为。 |

## 输入文档

- `specs/04-common-capability/04-common-events/07-drag-capability/design.md`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts:17886-18018,18102-18325,22645-22699`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/arkui/component/common.static.d.ets:11015-11159,13226-13237`
- `D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:141-144,667-775`
- `interfaces/native/event/drag_and_drop_impl.cpp:540-588`
- `frameworks/core/components_ng/event/drag_event.cpp:1232-1297,1344-1416,2121-2133`
- `frameworks/core/components_ng/manager/drag_drop/utils/drag_animation_helper.cpp:610-672,771-848,989-1027`

## 用户故事

### US-1: 配置确定的预览来源与外观

作为拖拽源开发者，我希望配置预览内容和样式，以便拖拽开始时呈现可预期的浮动预览。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 动态 ArkTS API 11 设置 `dragPreview`，THEN 可传 `CustomBuilder`、`DragItemInfo` 或 string；WHEN 使用 API 15 重载，THEN 可附加 `PreviewConfiguration`。 | 正常 |
| AC-1.2 | WHEN 静态 ArkTS API 23 设置 `dragPreview` 或 `dragPreviewOptions`，THEN `preview`/`value` 允许 `undefined`，不得用动态签名覆盖其可空合同。 | 边界 |
| AC-1.3 | WHEN 起拖解析预览，THEN 依次使用 inspectorId PixelMap、直接 PixelMap、组件缩略图；前一来源有效时不继续使用后一来源。 | 正常 |
| AC-1.4 | WHEN 配置 `DragPreviewOptions.mode` 时 `AUTO` 与其他枚举同时出现，THEN `AUTO` 优先，其他模式被忽略。 | 边界 |

### US-2: 配置 C 预览选项与可观察错误边界

作为 C API 开发者，我希望通过 PixelMap 和 PreviewOption 设置缩放、默认视觉效果、徽标和起拖前动画，以便获得与 ArkTS 对应的既有预览能力。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN C API API 12 传入有效 node 和 PixelMap，THEN `OH_ArkUI_SetNodeDragPreview` 设置预览；WHEN preview 为 null，THEN 重置节点预览且返回成功。 | 正常 |
| AC-2.2 | WHEN API 12 以有效 `ArkUI_DragPreviewOption` 设置 scale、shadow、radius、badge 或起拖前动画，THEN adapter 转换为节点 Preview/Interaction options。 | 正常 |
| AC-2.3 | WHEN C 的 node、option 或 PreviewOption setter 的 option 为空，THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |

### US-3: 呈现默认效果、多选 Overlay 与动画

作为用户，我希望在单选和多选拖拽中看到与当前选项一致的阴影、圆角、徽标和动画，而不会把多选 Overlay 当作普通单选预览。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 预览属性被应用，THEN 默认 opacity 被写入；默认 shadow 按开关设置；默认 radius 在开关开启或启用多选时设置。 | 正常 |
| AC-3.2 | WHEN 启用多选预览，THEN 创建 Gather Node；WHEN 为 SceneBoard 窗口，THEN 挂载到 WindowScene，否则挂载到 RootNode。 | 正常 |
| AC-3.3 | WHEN 默认起拖前动画未启用，THEN 不执行 drag-node-copy 动画；WHEN 启用，THEN 使用既有 Overlay 动画路径显示/隐藏副本。 | 边界 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.2 | R-1 | Feat-04 | SDK 类型对照 | `common.d.ts:22645-22699`; `common.static.d.ets:13226-13237` |
| AC-1.3~AC-1.4 | R-2、R-3 | Feat-04 | Host 单测 | `drag_event.cpp:2121-2133`; `common.d.ts:18107-18120` |
| AC-2.1~AC-2.3 | R-4 | Feat-04 | C API 单测 | `drag_and_drop.h:667-775`; `drag_and_drop_impl.cpp:540-588` |
| AC-3.1~AC-3.3 | R-5~R-7 | Feat-04 | Preview/Overlay Host 单测 | `drag_event.cpp:1402-1416`; `drag_animation_helper.cpp:610-672,771-848` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 调用 `dragPreview` 或 `dragPreviewOptions` | 动态 API 11 提供基础预览/选项，API 15 提供 config 重载；静态 API 23 的参数可为 `undefined` | `CustomBuilder` 需离线渲染，SDK 已提示其可能增加开销和延迟 | AC-1.1、AC-1.2 |
| R-2 | 行为 | 起拖时 `FrameNode` 存在 inspectorId、PixelMap 或缩略图 | 按 inspectorId PixelMap → PixelMap → 缩略图顺序选择，命中即停止 | 此顺序是内部消费行为；公开 ArkTS 签名仍以 SDK 为准 | AC-1.3 |
| R-3 | 边界 | `mode` 同时含 `AUTO` 和其他 `DragPreviewMode` | `AUTO` 生效，其他模式被忽略 | 动态 mode 在 API 11 为单值、API 12 起可为数组；静态 API 23 直接定义单值或数组 | AC-1.4 |
| R-4 | 异常 | C 设置 PixelMap/PreviewOption，且 node、option 或 setter 参数无效 | 有效输入经 CommonModifier/DragAdapter 写入；无效输入返回 `PARAM_INVALID` | null PixelMap 是重置预览的有效输入，不等同于无效 node | AC-2.1、AC-2.2、AC-2.3 |
| R-5 | 行为 | 应用节点预览选项 | 始终写默认 opacity；shadow 由 `isDefaultShadowEnabled` 决定；radius 由默认 radius 或多选决定 | 应用后的渲染属性保存在既有 `DragPreviewOption`，不新增持久格式 | AC-3.1 |
| R-6 | 行为 | 多选已启用且请求 Gather Node | 创建/复用 Gather Node；SceneBoard 挂 WindowScene，其他窗口挂 RootNode | 未启用多选直接不创建 Gather Node | AC-3.2 |
| R-7 | 边界 | 处理 drag-node-copy 的显示/隐藏 | `defaultAnimationBeforeLifting` 为 false 时不执行对应动画；为 true 时走 Overlay 动画 | 本规则只定义 ArkUI 呈现路径，不等同于系统拖拽会话结束 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-3 | 动态/静态 SDK 对照 | 引入版本、`undefined`、重载和 `AUTO` 优先级。 |
| VM-2 | R-2、R-5 | Preview Host 单测 | 来源选择、默认 opacity/shadow/radius。 |
| VM-3 | R-4 | C API 单测 | reset 成功与 `PARAM_INVALID` 错误边界。 |
| VM-4 | R-6、R-7 | Overlay/动画 Host 单测 | 多选挂载位置和动画开关。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `dragPreview` | Public ArkTS | Builder、`DragItemInfo`、string；API 15 可带 config | 当前组件 | N/A | 设置拖拽预览。 | AC-1.1、AC-1.2 |
| `dragPreviewOptions` | Public ArkTS | `DragPreviewOptions`、可选 `DragInteractionOptions` | 当前组件 | N/A | 设置模式、徽标和交互呈现。 | AC-1.2、AC-1.4 |
| `OH_ArkUI_SetNodeDragPreview` | Public C API | node、`OH_PixelmapNative*` | `int32_t` | `PARAM_INVALID` | 设置或重置节点 PixelMap 预览。 | AC-2.1、AC-2.3 |
| `ArkUI_DragPreviewOption` Create/Dispose/setter/SetNode 组 | Public C API | option、枚举/布尔值/徽标数 | `int32_t` 或 void | `PARAM_INVALID` | API 12 配置缩放、视觉效果、徽标和起拖动画。 | AC-2.2、AC-2.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| 动态 `dragPreview` | 变更 | API 15 增加 `PreviewConfiguration` 重载 | API 11-14 使用基础重载；按动态 SDK 版本选择。 | AC-1.1 |
| `DragPreviewOptions.mode` | 变更 | 动态 API 11 单模式，API 12 起支持数组 | 同时含 `AUTO` 时不要期待其他 mode 生效。 | AC-1.4 |
| 静态预览 API | 变更 | API 23 参数接受 `undefined` | 静态代码按可空合同处理，不回推至动态 API。 | AC-1.2 |

## 接口规格

### 接口定义

**`dragPreview` / `dragPreviewOptions`**

| 属性 | 值 |
|---|---|
| 函数签名 | 动态 `dragPreview(value: CustomBuilder \| DragItemInfo \| string): T`、API 15 `dragPreview(preview, config?): T`、`dragPreviewOptions(value, options?): T`；静态 API 23 的对应参数允许 `undefined` |
| 返回值 | 当前组件对象 |
| 开放范围 | Public ArkTS |
| 错误码 | N/A |
| 关联 AC | AC-1.1、AC-1.2、AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| preview/value | Builder、`DragItemInfo`、string 或静态 `undefined` | 动态是；静态可选 | N/A | API 版本决定可用签名；Builder 适用 SDK 的离线渲染提示。 |
| mode | `DragPreviewMode` 或数组 | 否 | `AUTO` | `AUTO` 与其他值并存时仅 `AUTO` 生效。 |
| options | `DragInteractionOptions` | 否 | 空 | 动态从 API 12 文档化交互参数；静态契约以 API 23 声明为准。 |

**`OH_ArkUI_SetNodeDragPreview` / PreviewOption 组**

| 属性 | 值 |
|---|---|
| 函数签名 | `OH_ArkUI_SetNodeDragPreview(node, preview)`；`OH_ArkUI_CreateDragPreviewOption`、`Dispose`、scale/shadow/radius/badge/animation setters 与 `OH_ArkUI_SetNodeDragPreviewOption` |
| 返回值 | setter/节点设置返回 `int32_t`；Create 返回 option；Dispose 无返回 |
| 开放范围 | Public C API |
| 错误码 | 无效 node/option 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`；null preview 执行 reset 并返回成功 |
| 关联 AC | AC-2.1、AC-2.2、AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| node | `ArkUI_NodeHandle` | 是 | N/A | FullImpl 和 node 必须有效。 |
| preview | `OH_PixelmapNative*` | 是 | N/A | null 表示 reset；非 null 必须能转换为内部 PixelMap。 |
| option | `ArkUI_DragPreviewOption*` | 是（setter/SetNode） | N/A | 必须来自 Create 且未 Dispose；为空返回 `PARAM_INVALID`。 |

## 兼容性声明

- **已有 API 行为变更:** 否；补录动态 API 11/12/15、静态 API 23 与 C API 12 的既有差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；预览选项仍存于既有 `DragDropRelatedConfigurations`。
- **最低支持版本:** 动态基础预览/选项 API 11，动态交互 options 和 mode 数组 API 12，动态 config 重载 API 15，静态 API 23，C API 12。
- **API 版本号策略:** 每个入口以 canonical SDK `@since` 为准；静态 `undefined` 与动态重载不得静默合并。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| SDK 优先 | ArkTS/C 的公开签名和版本分别以 SDK type definition/C header 为准。 | AC-1.1、AC-1.2、AC-2.1 |
| 预览消费顺序 | 起拖实现固定按 inspectorId、PixelMap、缩略图回退，不允许规格调换顺序。 | AC-1.3 |
| Overlay 边界 | Gather Node 与 drag-node-copy 均由 Overlay/动画辅助层呈现；不定义系统 MSDP 会话。 | AC-3.2、AC-3.3 |
| C 错误边界 | 无效参数可观察为 `PARAM_INVALID`，但 null PixelMap 的 reset 是有效语义。 | AC-2.1、AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | Builder 预览可能产生离线渲染开销和延迟，按 SDK 提示验证。 | 性能/Host 测试 | `common.d.ts:22614-22617` |
| 可靠性 | 参数非法不进入 adapter 写入；多选未启用不创建 Gather Node。 | C/Host 单测 | `drag_and_drop_impl.cpp:540-588`; `drag_animation_helper.cpp:620-627` |
| 可测试性 | 来源选择、默认效果、挂载位置和动画开关均有独立可观察状态。 | Preview/Overlay Host 单测 | `drag_event.cpp:1402-1416,2121-2133` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 无本 Feat 特有 API 差异 | 使用同一预览来源和效果合同。 | Host/设备集成测试 | `drag_event.cpp:2121-2133` |
| 平板 | 无本 Feat 特有 API 差异 | 多窗口挂载按 Overlay 容器处理。 | 多窗口集成测试 | `drag_animation_helper.cpp:659-672` |
| 折叠屏 | 无本 Feat 特有 API 差异 | SceneBoard 挂载规则不随设备形态改变。 | SceneBoard 集成测试 | `drag_animation_helper.cpp:667-672` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 深色模式 | 是 | 预览视觉由已有 image/render context 与选项消费，本 Feat 不另行定义主题变换。 | AC-3.1 |
| 多窗口/分屏 | 是 | 多选 Gather Node 按 SceneBoard/RootNode 选择挂载位置。 | AC-3.2 |
| 版本升级 | 是 | 动态 11/12/15、静态 23、C 12 的差异须显式保留。 | AC-1.1、AC-1.2、AC-1.4 |
| 生态兼容 | 是 | C 仅以 PixelMap 和 PreviewOption 表达，不能假定支持 ArkTS Builder。 | AC-2.1、AC-2.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽预览与交互呈现
  Scenario: 选择预览来源
    Given FrameNode 同时保存 inspectorId PixelMap 和直接 PixelMap
    When 起拖解析预览
    Then 使用 inspectorId PixelMap
    And 不读取直接 PixelMap 或组件缩略图

  Scenario: SceneBoard 多选预览
    Given 已启用多选且当前容器是 SceneBoard 窗口
    When 创建 Gather Node
    Then 将其挂载到 WindowScene

  Scenario: C 重置预览
    Given C API 接收到有效 node
    When OH_ArkUI_SetNodeDragPreview 的 preview 为 null
    Then 重置节点预览
    And 返回成功
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 覆盖动态/静态 ArkTS、C API、预览来源、视觉效果、Overlay、多选和动画。
- [x] 每个 AC 至少关联一条规则和一种验证方式。
- [x] 每条规则满足可复现、可观测、边界明确、关联 AC 和不冲突要求。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "Drag preview source selection options Overlay gather node and animation implementation"
```
