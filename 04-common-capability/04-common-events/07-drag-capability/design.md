# 架构设计

> 确认 ArkUI 公共拖拽能力的接口分层、配置存储、预览边界和后续 Spec 拆分；本设计基于现有实现补录，不改变产品行为。

## 设计元数据

| 字段 | 内容 |
|---|---|
| Design ID | DESIGN-Func-04-04-07 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 目标 Feature | Feat-01 组件拖拽源与目标配置，Feat-02 组件拖拽生命周期与事件契约，Feat-03 拖拽数据、结果与异步传输，Feat-04 拖拽预览与交互呈现，Feat-05 程序化 DragAction 与 DragController API，Feat-06 落放完成、反馈与延迟结束，Feat-07 弹簧加载与悬停检测 |
| 复杂度 | 关键 |
| 目标版本 | 动态 ArkTS API 10/11/15；静态 ArkTS API 23；C API API 12 |
| Owner | ArkUI SIG |
| 状态 | Baselined（已有实现补录） |

## 需求基线

| 项 | 补充说明 |
|---|---|
| SDK 是公开契约 | ArkTS 签名、可空性和 `@since` 必须以 interface_sdk-js 类型定义为准；内部实现只能作为行为证据。 |
| 双通道公开接口 | 动态/静态 ArkTS 与 C API 是并列接口面，允许参数形态和版本不得静默合并。 |
| 真实拖拽边界 | 组件配置由 ArkUI 存储和消费；真实系统拖拽会话仍经 `InteractionInterface` 由 MSDP 侧管理。 |
| 生命周期派发边界 | （Feat-02）系统 MMI 事件经 `PipelineContext` 和 Manager 派发目标端生命周期；源端真实结束仅以 `GetDragCallback` 为准。 |
| 数据与异步传输边界 | （Feat-03）ArkUI 在当前 `DragEvent` 读写数据、结果和加载参数，并选择本地预取或远端请求路径；UDMF/MSDP 的内部传输会话不由 ArkUI 规格重定义。 |
| 预览呈现边界 | （Feat-04）ArkUI 选择预览来源、应用 Preview/Interaction options，并用 Overlay 呈现多选和动画；不将渲染动画等同于 MSDP 拖拽会话。 |
| 程序化起拖边界 | （Feat-05）ArkUI 构造/校验 UIContext 或 C Action、管理状态监听并调用 InteractionInterface；真实系统会话和外部传输仍由 MSDP 协作。 |
| 延迟完成边界 | （Feat-06）ArkUI 仅在 onDrop 阶段保存 pending ID、结果/操作/动画反馈并调用 stop callback；不能把手势结束或预览动画作为系统拖拽最终完成。 |
| 悬停检测边界 | （Feat-07）ArkUI 仅对当前命中目标提供计时、状态和回调；真实系统拖拽会话仍经 `InteractionInterface` 与 MSDP 协作，且 `drag_and_drop.h` 未提供 SpringLoading C API。 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 补充架构说明 |
|---|---|
| `interface_sdk-js` | 动态/静态 `CommonMethod`、预览及交互选项的公开 ArkTS 契约。 |
| `interface_sdk_c` | `drag_and_drop.h` 的 NDK 公开声明与 API 12 版本信息。 |
| `arkui_ace_engine` | C API 实现、CommonModifier/DragAdapter、FrameNode 存储和起拖预览解析。 |
| `docs` | ArkTS/C API 参考文档和版本说明。 |
| UDMF / MSDP 协作边界 | （Feat-03）`UnifiedData` 是公开数据合同；Manager 仅执行摘要/权限、预取与远端请求协作。 |
| Overlay/Animation | （Feat-04）预览 ImageNode、Gather Node、drag-node-copy 的创建、挂载与动画由 `DragEventActuator`、`DragAnimationHelper` 和 OverlayManager 协作。 |
| `drag_controller` / native adapter | （Feat-05）动态 NAPI、静态 ANI、C adapter 和 `DragDropFuncWrapper` 分别桥接程序化 Action 到系统起拖。 |
| GlobalController / pending feedback | （Feat-06）`DragDropFuncWrapper` 与 `DragDropGlobalController` 管理延迟结束 ID、最终反馈和待执行跟手形变动画。 |
| SpringLoading detector / state machine | （Feat-07）`DragDropManager` 驱动 detector；IDLE/BEGIN/UPDATE/END/CANCEL 状态机在 UI 任务上完成稳定停留计时、回调与中断。 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|---|---|---|---|
| ArkTS API 层 | `common.d.ts`、`common.static.d.ets` | 声明 `draggable`、`allowDrop`、`dragPreview` 和 `dragPreviewOptions` 的签名与版本。 | 存量公开契约补录 |
| C API 层 | `drag_and_drop.h` | 声明节点源/目标、PixelMap 预览和选项对象 API。 | 存量公开契约补录 |
| C 适配层 | `drag_and_drop_impl.cpp` | 校验参数，调用 CommonModifier 或 DragAdapter，并转换 C 预览选项。 | 存量适配补录 |
| Modifier/Adapter 层 | CommonModifier、DragAdapter | 将 C 接口设置转换为节点配置。 | 存量内部桥接补录 |
| 节点状态层 | `FrameNode`、`DragDropRelatedConfigurations` | 分别保存 draggable、allowDrop、预览信息和预览选项。 | 存量状态存储补录 |
| 起拖消费层 | `DragEventActuator`、`GestureEventHub` | 按 inspectorId、PixelMap、缩略图优先级解析预览。 | 存量预览消费补录 |
| 系统交互层 | `InteractionInterface` | 消费配置后的起拖数据并进入 MSDP 系统拖拽。 | 已有子系统边界 |
| 事件派发层 | `PipelineContext`、`DragDropManager`、EventHub | （Feat-02）分发系统拖拽事件，按命中目标派发 enter/move/leave/drop。 | 存量生命周期补录 |
| C 事件读取层 | `ArkUI_NodeEvent`、`ArkUI_DragEvent` | （Feat-02）从 C 回调事件提取拖拽事件和预拖拽状态。 | 存量 C 事件补录 |
| 数据合同层 | `DragEvent`、`UnifiedData`、`DataLoadParams` | （Feat-03）按动态/静态 ArkTS 与 C API 的各自版本合同读写数据、结果与加载策略。 | 存量数据接口补录 |
| 落放数据处理层 | `DragDropManager` | （Feat-03）在 DROP 前后选择本地预取、远端检查/后台请求，并写回系统通知的结果、行为和动画。 | 存量异步处理补录 |
| 预览解析层 | `DragEventActuator`、`GestureEventHub` | （Feat-04）按 inspectorId PixelMap、直接 PixelMap、缩略图回退，并将选项应用给预览节点。 | 存量预览消费补录 |
| Overlay 动画层 | `DragAnimationHelper`、OverlayManager | （Feat-04）创建/挂载多选 Gather Node，控制 drag-node-copy 和预览的起拖动画。 | 存量呈现补录 |
| Controller 桥接层 | `js_drag_controller.cpp`、ANI DragController | （Feat-05）解析 ArkTS 参数、限制单会话、创建/启动 Action 并映射回调。 | 存量程序化桥接补录 |
| C Action 适配层 | `drag_and_drop_impl.cpp`、`drag_adapter_impl.cpp` | （Feat-05）保存 C Action 配置/监听，转换为内部 Action 并在失败时回调 cancel/ended。 | 存量 C Action 补录 |
| 系统起拖层 | `DragDropFuncWrapper`、`InteractionInterface` | （Feat-05）将内部 Action 转为系统 DragData 后发起 MSDP StartDrag。 | 存量子系统对接补录 |
| 落放反馈层 | `DragEvent`、`DragDropManager` | （Feat-06）写入结果、behavior 与自定义落放动画状态，并消费默认动画开关。 | 存量落放反馈补录 |
| pending 完成层 | `DragDropFuncWrapper`、`DragDropGlobalController` | （Feat-06）申请/校验 ID、保存结果和完成 stop callback。 | 存量延迟完成补录 |
| 悬停检测 API 层 | `common.d.ts`、`common.static.d.ets`、`dragController*.d.ts` | （Feat-07）声明绑定回调、时序配置、状态、上下文与 BEGIN-only 控制 API。 | 存量公开契约补录 |
| 悬停状态层 | `DragDropRelatedConfigurations`、SpringLoading StateMachine | （Feat-07）节点保存绑定配置；状态机调度 IDLE→BEGIN→UPDATE/END 或 CANCEL。 | 存量状态机补录 |
| 命中/中断层 | `DragDropManager`、SpringLoadingDetector | （Feat-07）ENTER/MOVE 驱动目标检测；LEAVE/drag end、快速移动或目标改变中断周期。 | 存量交互补录 |

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---|---|---|---|
| OH-ARCH-LAYERING | 存在 SDK/C API → Adapter/Modifier → 节点状态 → 起拖消费链路 | 公开接口不直接操作 Preview/Manager 内部状态；配置经适配层进入节点。 | 调用链审查 |
| OH-ARCH-SUBSYSTEM | ArkUI 与 MSDP 协作 | 本域只定义配置和 ArkUI 消费边界，不定义 MSDP 内部会话。 | Mock/集成测试 |
| OH-ARCH-API-LEVEL | 动态、静态和 C API 有版本与可空性差异 | SDK 定义优先，差异在 Spec 与风险中显式保留。 | SDK 对照 |
| OH-ARCH-ERROR-LOG | C API 暴露错误码 | 无效 node/option/typesArray 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`，不得继续调用内部实现。 | C API 单测 |

## 不涉及项承接

| 维度 | 设计结论 |
|---|---|
| 组件拖拽生命周期事件与回调 | 由 Feat-02 承接。 |
| 数据传输、结果和异步读取 | 由 Feat-03 承接。 |
| 预览渲染、动画和视觉交互 | 由 Feat-04 承接；本 Feat 仅定义预览配置与来源优先级。 |
| 程序化 DragAction/DragController | 由 Feat-05 承接。 |
| 落放结束、反馈和延迟完成 | 由 Feat-06 承接。 |
| 弹簧加载/悬停检测 | 由 Feat-07 承接。 |

## 关键设计决策

| 决策ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---|---|---|---|---|---|
| ADR-1 | 哪一份定义是 ArkTS 公共签名的权威？ | 以动态/静态 SDK 类型定义分别作为契约。 | 从 C++ bridge 推断；强行统一动态静态签名。 | 内部表示和动态/静态可空性、版本可不同。 | Feat-01 AC-1.1、AC-2.1、AC-2.2、AC-3.1 |
| ADR-2 | C API 如何进入节点配置？ | 先参数校验，再经 CommonModifier 或 DragAdapter 设置/复位。 | C API 直接修改 FrameNode；忽略无效参数。 | 保留已有适配层和 `PARAM_INVALID` 错误边界。 | Feat-01 AC-1.3、AC-2.3、AC-3.2、AC-3.3 |
| ADR-3 | 预览从何处取得？ | inspectorId PixelMap 优先于直接 PixelMap，二者缺失时使用组件缩略图。 | 总使用快照；总优先回调返回值。 | 这是现有节点预览解析顺序；视觉渲染细节留给 Feat-04。 | Feat-01 AC-2.4 |
| ADR-4 | 配置应存储在哪一层？ | 将 draggable、allowDrop、预览信息和预览选项分层存储在 FrameNode/拖拽相关配置。 | 合并为一个无类型 map；在起拖时重新解析 API。 | 保持当前存储位置和配置更新语义。 | Feat-01 AC-1.1、AC-1.2、AC-3.1 |
| ADR-F2-1 | 谁负责系统拖拽生命周期主派发？ | `PipelineContext::OnDragEvent` 将 MMI 事件交给 DragDropManager。 | DragDropProxy 主派发；EventHub 直接接收 MMI。 | Proxy 只模拟起拖后的路径，不能取代系统事件链。 | Feat-02 AC-2.1、AC-2.2 |
| ADR-F2-2 | 什么代表真实源端结束？ | 仅以 MSDP `GetDragCallback` 回到 UI 线程后的 onDragEnd 为准。 | 手势 actionEndTask；预览动画结束。 | 系统会话结束与手势任务不是同一边界。 | Feat-02 AC-1.3 |
| ADR-F2-3 | 动态/静态/C 生命周期差异如何表达？ | 保留回调 `@since`、静态 undefined 和 C PreDragStatus 不对称。 | 统一成一份推测签名；扩展 C 枚举。 | SDK/C ABI 是既有契约，规格不得改写。 | Feat-02 AC-1.1、AC-1.2、AC-3.2 |
| ADR-F3-1 | 数据和结果的公开合同由谁定义？ | 动态/静态 ArkTS 分别以 canonical SDK 类型、C 以 `drag_and_drop.h` 为准。 | 从 C++ 内部对象推断统一签名。 | 静态 `getData(): UnifiedData \| undefined` 与动态 API 存在既有差异。 | Feat-03 AC-1.1、AC-1.2、AC-2.1、AC-2.2 |
| ADR-F3-2 | 数据与 `DataLoadParams` 同时设置时如何决策？ | 保留最后一次设置优先，并记录 `useDataLoadParams`。 | 合并两种设置或总是优先数据。 | 这是 API 20 已实现的可观测状态选择。 | Feat-03 AC-3.1 |
| ADR-F3-3 | 谁负责异步数据传输？ | ArkUI Manager 负责预取、远端检查/请求与内部 drop 协作；不定义 UDMF/MSDP 内部会话。 | 将完整传输和权限语义归入 ArkUI。 | 保持子系统职责边界且不虚构系统侧行为。 | Feat-03 AC-3.3 |
| ADR-F4-1 | 预览来源如何选择？ | 保留 inspectorId PixelMap → PixelMap → 组件缩略图的实现顺序。 | 总是优先缩略图；把 ArkTS Builder 与 C PixelMap 视为同一内部来源。 | 既有起拖实现已按该顺序短路消费，且 C/ArkTS 的可表达性不同。 | Feat-04 AC-1.1、AC-1.3、AC-2.1 |
| ADR-F4-2 | 动态/静态/C 的预览选项怎样共存？ | 以各自 SDK 版本和签名记录，内部 C adapter 转换为 Preview/Interaction options。 | 强制统一 `undefined`、重载或 Builder 支持。 | 动态 API 11/12/15、静态 API 23、C API 12 存在公开差异。 | Feat-04 AC-1.1、AC-1.2、AC-1.4、AC-2.2 |
| ADR-F4-3 | 多选预览由谁呈现？ | OverlayManager 通过 Gather Node 挂载；SceneBoard 使用 WindowScene，其他容器使用 RootNode。 | 在普通预览 ImageNode 中内联多选元素。 | 保持现有 Overlay 生命周期及窗口容器边界。 | Feat-04 AC-3.2、AC-3.3 |
| ADR-F5-1 | 程序化起拖使用什么 ArkTS 入口？ | 动态 API 18 起迁移到当前 UIContext 的 DragController；静态使用 API 23 Controller。 | 继续以全局 API 作为主路径。 | 全局 API 已标 deprecated，且 Controller 必须绑定当前 UIContext。 | Feat-05 AC-1.1、AC-1.2、AC-1.3 |
| ADR-F5-2 | Action 是否可跨会话复用？ | 生命周期结束后用新 Action 替换旧对象，旧回调失效。 | 重复调用旧 Action；让多个 Action 并发。 | SDK 与 NAPI 均保留单会话和回调生命周期边界。 | Feat-05 AC-2.3、AC-3.4 |
| ADR-F5-3 | C 起拖失败如何对外表达？ | adapter 对注册 listener 回调 `DRAG_CANCEL` 与 `ENDED`；最终系统起拖经 InteractionInterface。 | 静默返回；由 ArkUI 伪造 MSDP 成功。 | 保持现有 C callback 恢复路径及 ArkUI/MSDP 分层。 | Feat-05 AC-3.2、AC-3.3 |
| ADR-F6-1 | 落放 behavior 是否控制实际数据处理？ | 仅作为 COPY/MOVE 意图和徽标/源端反馈。 | 由 behavior 直接驱动 UDMF 数据处理。 | SDK 明确 behavior 不负责真实数据处理。 | Feat-06 AC-1.1 |
| ADR-F6-2 | 延迟结束如何保证属于当前落放？ | 仅在 onDrop 阶段分配 request ID，所有通知验证该 ID，完成后复位状态。 | 全局无 ID 通知；跨阶段完成。 | 保持现有 GlobalController 会话隔离和错误码行为。 | Feat-06 AC-2.1、AC-2.2、AC-2.3 |
| ADR-F6-3 | “中断”跟手形变动画的含义是什么？ | 消费并立即执行待执行回调，返回是否存在回调。 | 丢弃回调或保证存在动画。 | 这是现有 GlobalController 的可观测实现。 | Feat-06 AC-3.1、AC-3.2 |
| ADR-F7-1 | SpringLoading 是否是独立系统拖拽会话？ | 否；它是当前命中目标的 ArkUI 计时/回调状态机。 | 将 END/CANCEL 视为 MSDP 会话结束。 | 保持 ArkUI 与 InteractionInterface/MSDP 的职责边界。 | Feat-07 AC-2.1~AC-2.4 |
| ADR-F7-2 | 动态重配置作用域？ | 仅 BEGIN 中更新当前检测周期，不覆盖节点绑定配置。 | 任意状态持久化改写绑定配置。 | 公开 SDK 与 state machine 都保留此生命周期边界。 | Feat-07 AC-3.1、AC-3.2 |
| ADR-F7-3 | abort 是否应补发 CANCEL？ | 否；应用自行清理，规格保留 SDK 明示的无 CANCEL 合同。 | 合成 CANCEL 或将 abort 定义为系统拖拽结束。 | 避免与既有公开合同冲突。 | Feat-07 AC-3.3 |
| ADR-F7-4 | 是否补 C API？ | 不补；canonical `drag_and_drop.h` 未发现 SpringLoading 声明。 | 从内部状态机推断 NDK ABI。 | 防止对外虚构 C 接口。 | Feat-07 AC-3.4 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|---|---|---|---|
| 组件源/目标配置 | 定义 ArkTS/C API 如何写入 draggable 与 allowDrop。 | 生命周期事件和数据协商。 | SDK/C API 单测 |
| 预览配置与来源 | 定义 Preview API、C 选项对象和起拖前来源优先级。 | 预览渲染、动画和窗口交接。 | FrameNode/PixelMap mock |
| 版本兼容 | 保留动态、静态、C API 的版本/可空性差异。 | 修改既有 ABI 或 SDK。 | SDK 对照 |

### 骨架 Spec 拆分

| Task ID | 目标 | 受影响文件 | AC |
|---|---|---|---|
| TASK-SKELETON-1 | 基线化组件拖拽源/目标和预览配置接口 | `common.d.ts`、`common.static.d.ets`、`drag_and_drop.h`、`drag_and_drop_impl.cpp`、`frame_node.*` | AC-1.1~AC-3.3 |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---|---|---|---|
| Feat-01 | 组件拖拽源与目标配置 | SDK common、`drag_and_drop.h`、FrameNode、C adapter | 基线任务 |
| Feat-02 | 组件拖拽生命周期与事件契约 | EventHub、DragEvent、ArkTS/C 事件桥接 | Feat-01 |
| Feat-03 | 数据、结果与异步传输 | UDMF、DragEvent、C API | Feat-02 |
| Feat-04 | 预览与交互呈现 | Preview options、overlay、animation | Feat-01 |
| Feat-05 | 程序化 DragAction/DragController | UIContext、DragAction、C API | Feat-01 |
| Feat-06 | 落放完成、反馈与延迟结束 | Drop result、pending completion、InteractionInterface | Feat-02、Feat-03 |
| Feat-07 | 弹簧加载与悬停检测 | SpringLoading、CommonMethod | Feat-02 |

## API 签名、Kit 与权限

### 新增 API

| API签名 | 类型 | Kit | d.ts 位置 | 权限要求 | SysCap |
|---|---|---|---|---|---|
| `allowDrop(value)` / `draggable(value)` | Public | ArkUI | `@internal/component/ets/common.d.ts:22589-22603`; `common.static.d.ets:13204-13215` | 无额外权限 | `SystemCapability.ArkUI.ArkUI.Full` |
| `dragPreview(value[, config])` / `dragPreviewOptions(value[, options])` | Public | ArkUI | `common.d.ts:22645-22699`; `common.static.d.ets:13226-13237` | 无额外权限 | `SystemCapability.ArkUI.ArkUI.Full` |
| `OH_ArkUI_SetNode*Drop*`、`OH_ArkUI_SetNodeDraggable` | Public C API | ArkUI Native | `drag_and_drop.h:605-677` | 无额外权限 | ArkUI Native |
| `OH_ArkUI_SetNodeDragPreview`、`ArkUI_DragPreviewOption` API 组 | Public C API | ArkUI Native | `drag_and_drop.h:667-775` | 无额外权限 | ArkUI Native |
| `DragEvent.setData/getData/setResult/getResult`（Feat-03） | Public ArkTS | ArkUI | `common.d.ts:11550-11602`; `common.static.d.ets:6480-6518` | 无额外权限 | `SystemCapability.ArkUI.ArkUI.Full` |
| `DragEvent.setDataLoadParams`（Feat-03） | Public ArkTS | ArkUI | `common.d.ts:11787-11796`; `common.static.d.ets:6637-6645` | 无额外权限 | `SystemCapability.ArkUI.ArkUI.Full` |
| C `ArkUI_DragEvent` data/result/drop-operation/type 与 `SetDataLoadParams`（Feat-03） | Public C API | ArkUI Native | `drag_and_drop.h:237-345` | 无额外权限 | ArkUI Native |
| `dragPreview` / `dragPreviewOptions`（Feat-04） | Public ArkTS | ArkUI | `common.d.ts:22645-22699`; `common.static.d.ets:13226-13237` | 无额外权限 | `SystemCapability.ArkUI.ArkUI.Full` |
| `DragPreviewMode` / `DragPreviewOptions`（Feat-04） | Public ArkTS | ArkUI | `common.d.ts:17886-18325`; `common.static.d.ets:11015-11159` | 无额外权限 | `SystemCapability.ArkUI.ArkUI.Full` |
| C `SetNodeDragPreview` 与 `ArkUI_DragPreviewOption` 组（Feat-04） | Public C API | ArkUI Native | `drag_and_drop.h:667-775` | 无额外权限 | ArkUI Native |
| `UIContext.getDragController`、`DragController.executeDrag/createDragAction`（Feat-05） | Public ArkTS | ArkUI | `@ohos.arkui.UIContext.d.ts:3474-3569,5560-5569`; static: `2647-2710,4032-4038` | 无额外权限 | `SystemCapability.ArkUI.ArkUI.Full` |
| `DragAction.startDrag`、状态监听（Feat-05） | Public ArkTS | ArkUI | `@ohos.arkui.dragController.d.ts:125-174`…2072 tokens truncated…。 |

### 数据模型设计

```typescript
type DragConfiguration = {
  draggable: boolean | undefined;
  allowDrop: Array<UniformDataType> | Array<string> | null | undefined;
  preview: CustomBuilder | DragItemInfo | string | undefined;
  previewOptions: DragPreviewOptions | undefined;
};
```

```cpp
// Existing storage boundary (conceptual mapping)
FrameNode: draggable_, allowDrop_, dragPreviewInfo_;
DragDropRelatedConfigurations: DragPreviewOption;
```

| 数据 | 存储位置 | 更新入口 | 消费方 |
|---|---|---|---|
| draggable/allowDrop | `FrameNode` | ArkTS bridge 或 CommonModifier | 事件/命中逻辑 |
| preview info | `FrameNode` | ArkTS/C DragAdapter | DragEventActuator |
| preview option | `DragDropRelatedConfigurations` | ArkTS/C options | 预览创建与动画 |

#### 数据、结果与加载参数模型（Feat-03）

```typescript
type DragEventTransferState = {
  data: UnifiedData | undefined;
  result: DragResult | undefined;
  dropOperation: DragBehavior | undefined;
  dataLoadParams: DataLoadParams | undefined;
  useDataLoadParams: boolean;
};
```

该模型描述既有事件上下文的概念映射：动态/静态 ArkTS 与 C API 的返回签名、枚举和可空性仍以各自 SDK/头文件为准；`useDataLoadParams` 由 C adapter 在有效参数时设置，证据为 `interfaces/native/event/drag_and_drop_impl.cpp:871-882`。

#### 预览呈现模型（Feat-04）

```typescript
type DragPreviewPresentation = {
  source: 'inspectorIdPixelMap' | 'pixelMap' | 'thumbnail';
  options: DragPreviewOptions;
  interaction: DragInteractionOptions | undefined;
  isMultiSelection: boolean;
  defaultAnimationBeforeLifting: boolean;
};
```

内部存储为 `FrameNode` 的 preview info 和 `DragDropRelatedConfigurations::DragPreviewOption`；预览来源解析见 `frameworks/core/components_ng/event/drag_event.cpp:2121-2133`，选项对象在 `frameworks/core/components_ng/manager/drag_drop/drag_drop_related_configuration.cpp:42-74` 管理。

#### 程序化 Action 模型（Feat-05）

```typescript
type ProgrammaticDragAction = {
  instanceId: number;
  pointerId: number;
  pixelMaps: PixelMap[];
  data: UnifiedData | undefined;
  dataLoadParams: DataLoadParams | undefined;
  statusListener: ((info: DragAndDropInfo) => void) | undefined;
};
```

该模型是 C/ArkTS Action 的概念映射；实际公开签名、可空性和对象释放规则以 SDK/C header 为准。C adapter 的字段转换和启动路径见 `frameworks/core/interfaces/native/node/drag_adapter_impl.cpp:45-101`。

#### 延迟落放完成模型（Feat-06）

```typescript
type DeferredDropCompletion = {
  requestId: number;
  result: DragResult;
  behavior: DragBehavior;
  disableDefaultDropAnimation: boolean;
  isOnDropPhase: boolean;
  stopCallback: (() => void) | undefined;
};
```

该模型是 `DragDropGlobalController` 既有状态的概念映射；ID 匹配和完成后的回调/复位实现见 `frameworks/core/components_ng/manager/drag_drop/drag_drop_global_controller.cpp:224-294`。

#### 弹簧加载数据模型（Feat-07）

```typescript
interface DragSpringLoadingConfiguration {
  stillTimeLimit?: number | int
  updateInterval?: number | int
  updateNotifyCount?: number | int
  updateToFinishInterval?: number | int
}
class SpringLoadingContext {
  state: BEGIN | UPDATE | END | CANCEL
  currentNotifySequence: number | int
  dragInfos?: { dataSummary?: Summary, extraInfos?: string }
  currentConfig?: DragSpringLoadingConfiguration
  abort(): void
  updateConfiguration(config: DragSpringLoadingConfiguration): void
}
```

### 测试性设计

| 测试层级 | 测试目标 | Mock 策略 | 验证方式 |
|---|---|---|---|
| SDK 对照 | 动态/静态签名和 @since | 读取 canonical d.ts/d.ets | API 表审查 |
| C API 单元 | 参数非法、reset、option 转换 | Mock FullImpl/Modifier/DragAdapter | 断言错误码和调用 |
| Host 单元 | FrameNode 配置与预览优先级 | Mock PixelMap/RenderContext | 断言保存值和来源 |
| Overlay/动画 Host | 多选挂载、默认效果和动画开关 | Mock OverlayManager/SceneBoard | 断言 WindowScene/RootNode 与动画路径 |
| Controller/Action Host | 单会话、Action 生命周期、状态监听和失败回调 | Mock NAPI/ANI、DragAdapter/Interaction | 断言拒绝、cancel/ended、StartDrag 调用 |
| Pending completion Host | onDrop phase、ID、2 秒等待与 stop callback | Mock GlobalController/DragAdapter | 断言结果、错误码、完成和状态复位 |
| SpringLoading Host | 停留、更新次数、END/CANCEL、abort 与动态配置 | Mock FrameNode/EventHub/TaskExecutor | 断言状态序列、序号、延迟和回调上下文 |

### 接口参数规约

| 接口 | 参数 | 类型 | 合法范围 | 非法处理 | 边界说明 |
|---|---|---|---|---|---|
| `draggable` | value | 动态 boolean；静态 boolean/undefined | SDK 签名允许范围 | ArkTS 类型检查 | 动态/静态不可空性不同 |
| `allowDrop` | value | 类型数组/null/静态 undefined | SDK 签名允许范围 | ArkTS 类型检查 | C typesArray 不可为空 |
| `OH_ArkUI_SetNodeDragPreview` | preview | PixelMap 指针/空 | 有效 PixelMap 或 null reset | 无效 node 返回 PARAM_INVALID | null preview 是 reset，不是错误 |
| PreviewOption setters | option | 非空 option 指针 | Create 返回的对象 | 空 option 返回 PARAM_INVALID | Dispose 仅释放 option |
| `onDragSpringLoading` | callback/configuration | 动态 callback/null；静态 callback/null/undefined | 动态 API 20；静态 API 26.0.0 | ArkTS 类型检查 | 四项配置默认 500ms/100ms/3/100ms；动态无效值回退 |

## 详细设计

### 组件源与目标配置

动态 ArkTS 的 `allowDrop`、`draggable` 从 API 10 可用；静态 ArkTS 对应 API 从 API 23 可用且签名接受 `undefined`。C API 的允许类型、禁止全部类型、允许全部类型及 draggable 从 API 12 暴露。C 实现先校验 FullImpl/node/typesArray，再把设置交给 CommonModifier。证据：`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts:22585-22603`，`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/arkui/component/common.static.d.ets:13204-13215`，`interfaces/native/drag_and_drop.h:628-677`，`interfaces/native/event/drag_and_drop_impl.cpp:458-459,611-659`。

### 预览配置、选项与来源优先级

动态 `dragPreview`/`dragPreviewOptions` 从 API 11 可用，`dragPreview(preview, config?)` 从 API 15 增加可选 config；静态对应 API 从 API 23 可用。C API 用 API 12 的 `ArkUI_DragPreviewOption` 生命周期和 setter 组构建选项，再转换为内部 preview/interaction options。起拖解析预览时按 inspectorId PixelMap、直接 PixelMap、组件缩略图顺序选择。证据：`common.d.ts:22645-22699`，`common.static.d.ets:13226-13237`，`interfaces/native/drag_and_drop.h:667-775`，`interfaces/native/event/drag_and_drop_impl.cpp:551-610`，`frameworks/core/components_ng/event/drag_event.cpp:2121-2133`。

### 生命周期派发与真实结束边界

`PipelineContext::OnDragEvent` 将系统 MMI 拖拽事件交给 `DragDropManager`。相同目标派发 Move；目标变化时派发 Leave 后 Enter，嵌套父子目标仅在 strict reporting 时对父目标 Leave。目标端 enter/move/leave 的 SDK 契约以绑定 onDrop 为前提。源端真实 onDragEnd 来自 `InteractionInterface::GetDragCallback` 进入 UI 任务，手势 `actionEndTask` 不定义系统拖拽结束。C API 仅从 NodeEvent 提取可表达的 DragEvent/PreDragStatus；数据和最终结果接口分别由 Feat-03/Feat-06 承接。证据：`frameworks/core/pipeline_ng/pipeline_context.cpp:6248-6275`，`frameworks/core/components_ng/manager/drag_drop/drag_drop_manager.cpp:1072-1085,1949-1974,3189-3201`，`frameworks/core/components_ng/event/gesture_event_hub_drag.cpp:1289,1642-1697`，`interfaces/native/drag_and_drop.h:195-211`。

### 数据、结果与异步传输

动态 ArkTS 在 API 10 提供 `setData/getData/setResult/getResult`，静态 ArkTS 对应接口从 API 23 提供，且静态 `getData()` 的公开返回值为 `UnifiedData | undefined`。`DataLoadParams` 的动态入口从 API 20、静态入口从 API 26.0.0、C 入口从 API 20 提供；数据与加载参数都写入同一事件时，以最后一次调用为准。C API API 12 覆盖数据、结果、drop operation 与 type，数组容量不足返回 `ARKUI_ERROR_CODE_BUFFER_SIZE_ERROR`；`SetDataLoadParams` 的 event 或参数为空则返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。Manager 在落放过程中先处理摘要/权限和预取选择：禁用预取时检查远端并按既有逻辑后台请求，否则走本地预取；之后处理内部 onDrop。系统通知携带的结果、行为和动画写回当前 `DragEvent`，DROP 分支再派发客户回调与内部 drop。证据：`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts:10792,11550-11602,11787-11796`，`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/arkui/component/common.static.d.ets:6005-6012,6480-6518,6637-6645`，`D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:237-345`，`interfaces/native/event/drag_and_drop_impl.cpp:871-882`，`frameworks/core/components_ng/manager/drag_drop/drag_drop_manager.cpp:1174-1180,1258-1268,1384-1387,1476-1533,1918-1920`。

### 预览、交互与 Overlay 呈现

动态 ArkTS 的 `dragPreview`/`dragPreviewOptions` 从 API 11 可用，API 15 为 `dragPreview` 增加 `PreviewConfiguration`；动态 mode 从 API 12 支持数组，且 `AUTO` 与其他模式同时设置时 `AUTO` 优先。静态 ArkTS 在 API 23 提供对应 API，并接受 `undefined`。C API API 12 用 PixelMap 和 `ArkUI_DragPreviewOption` 表达缩放、默认阴影/圆角、徽标和起拖前动画；adapter 在有效 node/option 时映射到 CommonModifier，空 PixelMap 重置预览，其他空参数返回 `PARAM_INVALID`。起拖时依次选择 inspectorId PixelMap、直接 PixelMap、缩略图；随后应用默认 opacity、阴影和圆角。多选时 OverlayManager 创建 Gather Node，SceneBoard 挂到 WindowScene，普通窗口挂到 RootNode；`defaultAnimationBeforeLifting` 控制 drag-node-copy 的 Overlay 动画路径。证据：`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts:17886-18018,18102-18325,22645-22699`，`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/arkui/component/common.static.d.ets:11015-11159,13226-13237`，`D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:667-775`，`interfaces/native/event/drag_and_drop_impl.cpp:540-588`，`frameworks/core/components_ng/event/drag_event.cpp:1344-1416,2121-2133`，`frameworks/core/components_ng/manager/drag_drop/utils/drag_animation_helper.cpp:610-672,771-848`。

### 程序化 DragAction 与 DragController

动态 ArkTS 通过 API 11 的 `UIContext.getDragController()` 获得当前上下文 Controller；旧全局 `executeDrag/createDragAction` 在 API 18 废弃。静态 ArkTS 从 API 23 提供 Controller/Action，但 `startDrag()` 返回 `Promise<void> | null`，状态监听使用 `onStatusChange/offStatusChange`，与动态 `on/off('statusChange')` 不同。一个 Action 的生命周期结束后其回调无效，NAPI 路径禁止在已有拖拽时创建或执行第二个 Action。C API API 12 可由 node/context 创建 Action，设置 pointer、PixelMap、触点、UDMF 数据、PreviewOption 和 listener；pointer 只接受 0–9。C adapter 负责转换 Action；启动失败时用 `DRAG_CANCEL` 和 `ENDED` 回调 listener。最终系统起拖由 `DragDropFuncWrapper::StartDragAction` 调用 `InteractionInterface::GetInstance()->StartDrag`，ArkUI 不定义 MSDP 内部会话。证据：`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@ohos.arkui.dragController.d.ts:125-174,437-522`，`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@ohos.arkui.dragController.static.d.ets:110-151`，`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@ohos.arkui.UIContext.d.ts:3474-3569,5560-5569`，`D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:785-950`，`interfaces/native/event/drag_and_drop_impl.cpp:169-419`，`frameworks/core/interfaces/native/node/drag_adapter_impl.cpp:66-119`，`frameworks/core/components_ng/manager/drag_drop/drag_drop_func_wrapper.cpp:360-366`。

### 落放完成、反馈与延迟结束

ArkTS `DragResult` 与 `DragBehavior` 从 API 10 表达落放结果和 copy/move 意图；behavior 只影响徽标和源端反馈，并不决定实际数据处理。动态 custom drop animation 必须在 onDrop 中且先设置 `useCustomDropAnimation`，静态 API 23 提供对应合同。C API 12 可在当前 event 禁用默认动画；C API 19 的 pending 仅能在 onDrop 阶段申请，GlobalController 保存递增 request ID 并只接受匹配 ID 的 result、operation 与完成通知，完成时调用保存的 stop callback 后复位。C API 24 才增加 pending 后默认动画开关通知；在错误阶段或 ID 不匹配时，adapter 返回 `DRAG_DROP_OPERATION_NOT_ALLOWED`。UIContext API 26.0.0 的跟手中断不是丢弃动画，而是消费并执行待执行回调。证据：`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@internal/component/ets/common.d.ts:10670-10675,11504,11676-11684`，`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/arkui/component/common.static.d.ets:6439-6449,6566-6572`，`D:/arkui/gitCode/ArkUI/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:225,952-1033`，`interfaces/native/event/drag_and_drop_impl.cpp:925-1005`，`frameworks/core/components_ng/manager/drag_drop/drag_drop_func_wrapper.cpp:404-444`，`frameworks/core/components_ng/manager/drag_drop/drag_drop_global_controller.cpp:224-340`。

### 弹簧加载与悬停检测

`onDragSpringLoading` 是通用目标端能力，不包含普通鼠标 hover、无障碍 hover 或具体 Text/TextField 组件行为。DragDropManager 在 ENTER/MOVE 时把当前命中 FrameNode、坐标、时间戳和 extraInfo 交给 detector；目标变化会复位并从新目标开始。IDLE 根据节点 `DragDropRelatedConfigurations` 的 `stillTimeLimit` 延迟进入 BEGIN；BEGIN 获取配置、构建带 summary/extraInfos 的 context，随后根据 `updateNotifyCount` 调度 UPDATE 或 END。UPDATE 到达次数上限后等待 `updateToFinishInterval` 再进入 END。LEAVE、drag end、目标改变或速度阈值会使未进入 END 的周期转 CANCEL 并复位。`abort()` 的公开合同是不触发 CANCEL；`updateConfiguration()` 仅 BEGIN 有效且只覆盖当前周期。动态 ArkTS 为 API 20，静态 ArkTS 为 API 26.0.0，C header 未提供等价 API。证据：`frameworks/core/components_ng/manager/drag_drop/drag_drop_manager.cpp:1291-1295,1934-1943,3610-3624`，`frameworks/core/components_ng/manager/drag_drop/drag_drop_spring_loading/drag_drop_spring_loading_detector.cpp:48-149`，`drag_drop_spring_loading_state_idle.cpp:22-40`，`drag_drop_spring_loading_state_begin.cpp:22-70`，`drag_drop_spring_loading_state_update.cpp:22-68`，`D:/arkui/gitCode/ArkUI/interface_sdk-js/api/@ohos.arkui.dragController.d.ts:569-812`。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|---|---|---|---|---|
| 动态/静态 ArkTS 的 @since 和 undefined 接受范围不同 | API | 中 | 每个 Spec 以 SDK 类型定义列出版本差异，不从内部实现统一语义。 | ArkUI API owner |
| C API 与 ArkTS 预览可表达能力不同 | API | 中 | 记录 C 仅以 PixelMap/option 对象表达；不捏造 Builder 等价路径。 | ArkUI Native owner |
| `CommonModifier*.d.ts` 未发现四项公共 Modifier 声明 | API | 低 | 规格只记录 C 实现的内部 Modifier 调用，后续如发现 SDK 声明再补录。 | ArkUI API owner |
| Builder 预览可能增加离线渲染开销和延迟 | 性能 | 中 | 在接口约束中保留 SDK 提示，使用 PixelMap 路径进行性能验证。 | Drag framework owner |
| C PreDragStatus 与动态 ArkTS 状态值不对称 | API | 中 | Feat-02 记录差异；不通过规格推断或修改 C ABI。 | ArkUI Native owner |
| 动态/静态 ArkTS `getData()` 的可空性和引入版本不同 | API | 中 | Feat-03 以各自 canonical SDK 记录，禁止以实现或另一前端签名静默合并。 | ArkUI API owner |
| `DataLoadParams` 与直接数据设置的最后调用优先容易被调用方忽略 | 行为 | 中 | 在 Feat-03 合同和测试中同时覆盖两种设置顺序。 | Drag framework owner |
| 远端检查/后台请求依赖 UDMF/MSDP 协作，ArkUI 无法单独定义完整系统会话 | 子系统 | 中 | 仅记录 Manager 可观察分支和权限/摘要前置，不虚构外部模块行为。 | Drag framework owner |
| 动态、静态与 C 的 preview 签名、可空性和引入版本不同 | API | 中 | Feat-04 逐项以 canonical SDK/头文件记录，禁止静默合并。 | ArkUI API owner |
| `AUTO` 与其他 DragPreviewMode 并存时其他模式不生效 | 行为 | 中 | 在 API 规约和用例中明确 `AUTO` 优先。 | Drag framework owner |
| 多选 Gather Node 的窗口挂载依赖 SceneBoard 容器 | 多窗口 | 中 | 用 Overlay Host/SceneBoard 测试验证 WindowScene 与 RootNode 两条路径。 | Drag framework owner |
| 动态/静态 Action 的可空性、返回值和状态监听方法名不同 | API | 中 | Feat-05 逐项以各自 canonical SDK 声明，禁止跨前端合并。 | ArkUI API owner |
| 旧 Action 生命周期结束后 callback 失效，且并发起拖被拒绝 | 生命周期 | 中 | 在 Action 管理和 Host 用例中覆盖替换对象、单会话和失败返回。 | Drag framework owner |
| C callback info 只在 listener 回调期间有效 | C ABI | 中 | 在接口规约和 C 单测中禁止保留指针，失败读取使用既有 UNKNOWN/null。 | ArkUI Native owner |
| pending ID 与 onDrop 阶段不匹配导致通知不生效/返回操作不允许 | 生命周期 | 中 | Feat-06 测试必须覆盖正确 ID、错误 ID 和非 onDrop 三种路径。 | Drag framework owner |
| header 的“不生效”描述与实现返回 `DRAG_DROP_OPERATION_NOT_ALLOWED` 需要同时可见 | API | 中 | 规格保留两者：外部语义为不接受通知，实现错误码为 operation-not-allowed。 | ArkUI Native owner |
| 跟手“中断”会执行而非丢弃待执行动画回调 | 行为 | 中 | API 文档和测试以 GlobalController 的消费执行行为为准。 | Drag framework owner |
| 动态/静态 SpringLoading API 的最低版本和 callback 可空性不同 | API | 中 | Feat-07 分别保留动态 API 20 与静态 API 26.0.0 的 canonical SDK 合同。 | ArkUI API owner |
| abort 不发送 CANCEL，应用若忽略自行清理可能遗留视觉状态 | 生命周期 | 中 | Feat-07 明确 UI 清理责任并以单测覆盖无额外 CANCEL。 | Drag framework owner |
| SpringLoading 未提供 C API | API/ABI | 中 | 规格明确 header 缺失；不由内部状态机推断 NDK 合同。 | ArkUI Native owner |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0/P1 AC。
- [x] 不涉及项已承接，N/A 和展开项均有结论。
- [x] 涉及仓和模块职责清晰。
- [x] 调用链层级分析完整，每层覆盖到位。
- [x] 适用架构规则已识别并形成设计结论。
- [x] 分层和子系统边界合规。
- [x] API 变更有签名、权限、错误码和兼容性说明。
- [x] BUILD.gn/bundle.json 影响明确。
- [x] 设计输出和后续 Task 拆分明确。
- [x] 关键设计决策有理由和影响说明。
- [x] 风险和开放问题有 Owner。

**结论:** 通过（已有实现补录）
