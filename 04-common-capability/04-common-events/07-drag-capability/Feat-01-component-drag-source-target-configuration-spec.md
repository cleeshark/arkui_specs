# 特性规格

## 概览

| 字段 | 内容 |
|---|---|
| 特性名称 | 组件拖拽源与目标配置 |
| 特性编号 | Func-04-04-07-Feat-01 |
| 所属 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 优先级 | P1 |
| 目标版本 | 存量实现；动态 ArkTS API 10/11/15，静态 ArkTS API 23，C API API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 公共组件拖拽源、落放目标、预览及预览选项契约 | 补录已有 ArkTS/C API、内部存储和桥接行为。 |

## 输入文档

- `specs/04-common-capability/04-common-events/07-drag-capability/design.md`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts:18102-18327,22585-22699`
- `D:/arkui/gitCode/ArkUI/interface_sdk-js/api/arkui/component/common.static.d.ets:11144-11149,13204-13237`
- `D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:605-775`
- `interfaces/native/drag_and_drop.h:628-793`
- `interfaces/native/event/drag_and_drop_impl.cpp:458-459,551-659`
- `frameworks/core/components_ng/base/frame_node.h:901-975`
- `frameworks/core/components_ng/base/frame_node.cpp:8855-8859,9126-9129`
- `frameworks/core/components_ng/event/drag_event.cpp:1291-1298,1395-1416,2121-2133`

## 用户故事

### US-1: 配置拖拽源与落放目标

作为 ArkTS 或 C API 开发者，我希望启用组件拖拽并声明目标可接受的数据类型，以便框架可按组件配置参与拖拽交互。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 动态 ArkTS 调用 `draggable(boolean)` 或静态 ArkTS 调用 `draggable(boolean | undefined)`，THEN 组件保存对应可拖拽配置。 | 正常 |
| AC-1.2 | WHEN 调用 `allowDrop` 或 C API 的允许/禁止落放类型接口，THEN 新设置替换该节点现有的允许落放类型配置。 | 正常 |
| AC-1.3 | WHEN C API 接收空节点、空类型数组或无效选项对象，THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`，不调用节点 Modifier。 | 异常 |

### US-2: 配置拖拽预览来源

作为拖拽源开发者，我希望以 Builder、`DragItemInfo`、资源字符串或 C PixelMap 配置预览，以便在起拖时取得既定预览。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 动态 ArkTS 调用 API 11 的 `dragPreview(value)` 或 API 15 的 `dragPreview(preview, config?)`，THEN 按 SDK 签名保存预览来源和可选 lifting 配置。 | 正常 |
| AC-2.2 | WHEN 静态 ArkTS 调用 API 23 的 `dragPreview(preview | undefined, config?)`，THEN `undefined` 作为静态契约允许值传入。 | 边界 |
| AC-2.3 | WHEN C API 的 `OH_ArkUI_SetNodeDragPreview` 接收空 `preview`，THEN 调用 reset；WHEN 它接收有效 PixelMap，THEN 交给 DragAdapter 设置预览。 | 恢复 |
| AC-2.4 | WHEN 起拖解析节点预览，THEN 依次使用 inspectorId 对应 PixelMap、直接 PixelMap 和组件缩略图兜底。 | 正常 |

### US-3: 配置预览与交互选项

作为拖拽源开发者，我希望通过 ArkTS `dragPreviewOptions` 或 C `ArkUI_DragPreviewOption` 配置预览模式、徽标与默认视觉选项。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 动态 ArkTS 调用 API 11 的 `dragPreviewOptions(value, options?)` 或静态 ArkTS 调用 API 23 对应方法，THEN 节点保存预览选项及交互选项。 | 正常 |
| AC-3.2 | WHEN C 调用创建后的预览选项 setter，再调用 `OH_ArkUI_SetNodeDragPreviewOption`，THEN 实现将其转换为内部 preview/interaction options 并传给 CommonModifier。 | 正常 |
| AC-3.3 | WHEN C 选项对象或节点为空，THEN 选项 setter/节点设置函数返回 `ARKUI_ERROR_CODE_PARAM_INVALID`；WHEN 调用 Dispose，THEN 仅释放该选项对象。 | 异常 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | Feat-01 | SDK 签名/FrameNode 单测 | `common.d.ts:22603`; `common.static.d.ets:13215`; `frame_node.cpp:9126-9129` |
| AC-1.2, AC-1.3 | R-2 | Feat-01 | C API 单测 | `drag_and_drop.h:628-677`; `drag_and_drop_impl.cpp:611-659` |
| AC-2.1, AC-2.2 | R-3 | Feat-01 | 动态/静态 SDK 对照 | `common.d.ts:22645-22679`; `common.static.d.ets:13226` |
| AC-2.3 | R-4 | Feat-01 | C API mock | `drag_and_drop_impl.cpp:596-610` |
| AC-2.4 | R-5 | Feat-01 | 预览来源单测 | `drag_event.cpp:2121-2133` |
| AC-3.1 | R-6 | Feat-01 | SDK/FrameNode 单测 | `common.d.ts:22699`; `common.static.d.ets:13237`; `frame_node.cpp:8855-8859` |
| AC-3.2, AC-3.3 | R-7 | Feat-01 | C API 单测 | `drag_and_drop.h:695-775`; `drag_and_drop_impl.cpp:551-593` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | ArkTS 或 C API 为有效节点设置 draggable | 节点保存可拖拽状态，C 路径调用 CommonModifier | 动态 ArkTS 参数为 `boolean`；静态 ArkTS 额外接受 `undefined` | AC-1.1 |
| R-2 | 行为 | 调用 `allowDrop`、SetAllowed、Disallow 或 AllowAll | 新类型集合或允许策略覆盖先前节点设置 | C 路径的 node/typesArray 不可为空，否则参数非法 | AC-1.2、AC-1.3 |
| R-3 | 行为 | ArkTS 调用 `dragPreview` | 按对应 SDK 版本保存 Builder、`DragItemInfo` 或字符串预览及可选 config | 动态 API 11 基础重载；动态 API 15 增加 config；静态 API 23 支持 `undefined` | AC-2.1、AC-2.2 |
| R-4 | 恢复 | C 节点预览参数为 null 或有效 PixelMap | null 调用 reset；有效 PixelMap 经 DragAdapter 设置 | null node 或缺少 FullImpl 返回参数非法 | AC-2.3 |
| R-5 | 行为 | 起拖解析已配置的节点预览 | 先 inspectorId，再直接 PixelMap，最后调用渲染上下文缩略图 | 本规则不定义预览动画、效果和渲染细节 | AC-2.4 |
| R-6 | 行为 | ArkTS 设置 `dragPreviewOptions`/交互 options | 节点的拖拽相关配置保存选项 | 动态 API 11；静态 API 23；`onItemDragStart` 模式不支持属于 SDK 契约 | AC-3.1 |
| R-7 | 异常 | C 选项 setter/节点设置收到无效 option 或 node | 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`；有效选项转换后交给 CommonModifier | 仅 `Dispose` 释放选项对象；不隐式释放节点或 PixelMap | AC-3.2、AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-2 | 动态/静态 SDK 对照与 C API 单测 | 签名、版本、替换性和非法参数 |
| VM-2 | R-3、R-4、R-5 | Preview mock/FrameNode 单测 | 重载、null reset 与来源优先级 |
| VM-3 | R-6、R-7 | C API 选项对象单测 | setter 转换、错误码和 Dispose |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `CommonMethod.allowDrop` | Public ArkTS | 动态：`Array<UniformDataType> \| null \| Array<string>`；静态额外允许 `undefined` | 当前组件 | N/A | 声明可落放数据类型 | AC-1.2 |
| `CommonMethod.draggable` | Public ArkTS | 动态 `boolean`；静态 `boolean \| undefined` | 当前组件 | N/A | 启用或禁用组件拖拽 | AC-1.1 |
| `CommonMethod.dragPreview` | Public ArkTS | `CustomBuilder \| DragItemInfo \| string`；动态 API 15 可选 config | 当前组件 | N/A | 声明预览来源 | AC-2.1、AC-2.2 |
| `CommonMethod.dragPreviewOptions` | Public ArkTS | `DragPreviewOptions` 和可选 `DragInteractionOptions` | 当前组件 | N/A | 声明预览/交互选项 | AC-3.1 |
| `OH_ArkUI_*Node*Drop*`、`OH_ArkUI_SetNodeDraggable` | Public C API | node、类型数组或 enabled | `int32_t` | `NO_ERROR`、`PARAM_INVALID` | 节点源/目标配置 | AC-1.1~AC-1.3 |
| `OH_ArkUI_SetNodeDragPreview`、`ArkUI_DragPreviewOption` API 组 | Public C API | node、PixelMap 或 option | `int32_t`/option 指针 | `NO_ERROR`、`PARAM_INVALID` | 节点预览和预览选项配置 | AC-2.3、AC-3.2、AC-3.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `dragPreview` | 变更 | 动态 ArkTS API 15 增加 `PreviewConfiguration` 重载 | API 11-14 使用单参数重载；API 15+ 可传 config | AC-2.1 |
| `draggable`/`allowDrop`/预览 API | 变更 | 动态与静态 ArkTS 的可用版本及 `undefined` 接受范围不同 | 以目标 SDK `.d.ts`/`.d.ets` 签名为准，不从内部实现推断 | AC-1.1、AC-1.2、AC-2.2、AC-3.1 |
| C 预览选项 API | 变更 | 与 ArkTS 预览模型并列但参数结构不同 | 使用 `ArkUI_DragPreviewOption` 生命周期 API；不将 ArkTS Builder 推断为 C 支持 | AC-3.2、AC-3.3 |

## 接口规格

### 接口定义

| 接口组 | 开放范围 | 参数约束 | 行为场景 |
|---|---|---|---|
| `allowDrop` / `draggable` | Public ArkTS | 以动态/静态 SDK 各自签名为准 | 源端启用和目标端数据类型声明，AC-1.1、AC-1.2 |
| `dragPreview` / `dragPreviewOptions` | Public ArkTS | Preview 值、选项和可选交互项必须符合对应 SDK 类型 | 预览来源和选项声明，AC-2.1、AC-2.2、AC-3.1 |
| `OH_ArkUI_SetNodeAllowedDropDataTypes`、`OH_ArkUI_DisallowNodeAnyDropDataTypes`、`OH_ArkUI_AllowNodeAllDropDataTypes` | Public C API | node 与类型数组遵循头文件约束 | 覆盖节点允许落放类型，AC-1.2、AC-1.3 |
| `OH_ArkUI_SetNodeDraggable`、`OH_ArkUI_SetNodeDragPreview` | Public C API | 有效 node；预览可为 null 以 reset | 配置节点拖拽与 PixelMap 预览，AC-1.1、AC-2.3 |
| `OH_ArkUI_CreateDragPreviewOption`、Dispose、Scale/Shadow/Radius/Badge/Animation setters、`OH_ArkUI_SetNodeDragPreviewOption` | Public C API | setter/节点设置要求非空 option；Dispose 仅处理 option | 配置和绑定 C 预览选项，AC-3.2、AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文件补录现有行为，但 SDK 已存在动态 API 10/11/15、静态 API 23 和 C API 12 的可用性差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态 `draggable`/`allowDrop` 为 API 10；动态预览/选项为 API 11；动态预览 config 为 API 15；静态配置为 API 23；C 节点配置为 API 12。
- **API 版本号策略:** SDK 类型定义为公开契约；静态 `undefined` 接受范围与动态签名差异必须显式记录；未在 `CommonModifier*.d.ts` 中发现这四项公共 Modifier 声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| SDK 优先 | ArkTS 签名与 `@since` 以 interface_sdk-js 为准，不从 C++/桥接推断。 | AC-1.1、AC-2.1、AC-2.2、AC-3.1 |
| C 参数检查 | C 导出函数先检查 FullImpl、node、option 或类型数组，再调用 Modifier/Adapter。 | AC-1.3、AC-2.3、AC-3.3 |
| 状态分层 | 可拖拽、允许类型、预览信息和预览选项在 FrameNode/拖拽相关配置中分层保存。 | AC-1.1、AC-1.2、AC-3.1 |
| 预览边界 | 本 Feat 只定义预览配置与来源优先级；动画、视觉效果和系统窗口交接由 Feat-04 承接。 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | 无效 C 指针返回参数非法，不进入 Modifier/Adapter 调用。 | C API 单测 | `drag_and_drop_impl.cpp:551-659` |
| 性能 | Builder 预览要求离线渲染，SDK 标注其可能增加开销与延迟。 | SDK 文档审查 | `common.d.ts:22614-22618` |
| 可测试性 | 存储、reset 和预览来源优先级可用 FrameNode/PixelMap mock 观察。 | Host 单测 | `frame_node.cpp:8855-8859`; `drag_event.cpp:2121-2133` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 使用同一节点配置与预览来源优先级。 | 无组件专用差异。 | Host/UI 集成测试 | `drag_event.cpp:2121-2133` |
| 平板 | 使用同一 ArkTS/C 配置契约。 | 多窗口交接不在本 Feat。 | API 集成测试 | SDK 定义同上 |
| 折叠屏 | 使用同一 ArkTS/C 配置契约。 | 折叠状态窗口边界由 Feat-06 承接。 | API 集成测试 | `Feat-06` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 否 | 未新增无障碍语义。 | N/A |
| 大字体 | 否 | 未改变文本或字体配置。 | N/A |
| 深色模式 | 否 | 预览样式渲染不在本 Feat。 | N/A |
| 多窗口/分屏 | 是 | 配置可在多窗口使用，窗口/容器交接由 Feat-06 定义。 | AC-2.4 |
| 版本升级 | 是 | 动态、静态和 C API `@since` 必须分别声明。 | AC-1.1、AC-2.1、AC-3.1 |
| 生态兼容 | 是 | ArkTS Builder 与 C PixelMap 不可互相推断支持范围。 | AC-2.1、AC-2.3 |

## 行为场景（Gherkin）

```gherkin
Feature: 组件拖拽源与目标配置
  Scenario: C PixelMap 预览重置
    Given 一个有效的 ArkUI 节点已设置拖拽预览
    When 调用 OH_ArkUI_SetNodeDragPreview 并传入 null preview
    Then CommonModifier 的 resetDragPreview 路径被调用

  Scenario: 静态 ArkTS 预览配置
    Given 使用 API 23 静态 ArkTS
    When 调用 dragPreview(undefined, config)
    Then 调用满足静态 SDK 签名并由组件保存配置
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 覆盖动态/静态 ArkTS、C API、内部 Modifier 调用和版本差异。
- [x] 每个 AC 至少关联一条规则和一种验证方式。
- [x] 规则表包含可复现触发条件、可观察结果、边界、AC 映射且无冲突。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "Common drag configuration storage, C drag_and_drop API adaptation, and preview source priority"
  - repo: "OpenHarmony/interface_sdk-js"
    query: "CommonMethod draggable allowDrop dragPreview dragPreviewOptions dynamic and static contracts"
```
