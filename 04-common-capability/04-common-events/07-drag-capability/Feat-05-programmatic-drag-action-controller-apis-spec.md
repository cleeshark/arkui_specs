# 特性规格

## 概览

| 字段 | 内容 |
|---|---|
| 特性名称 | 程序化 DragAction 与 DragController API |
| 特性编号 | Func-04-04-07-Feat-05 |
| 所属 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 优先级 | P1 |
| 目标版本 | 动态 ArkTS API 11/18；静态 ArkTS API 23/26.0.0；C API API 12/20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | UIContext DragController、ArkTS/C DragAction、监听、数据/预览配置和系统起拖边界 | 对既有程序化起拖实现补录，不改变 API 或产品行为。 |

## 输入文档

- `specs/04-common-capability/04-common-events/07-drag-capability/design.md`
- `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.dragController.d.ts:125-174,437-522`
- `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.dragController.static.d.ets:110-151,180-264`
- `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.UIContext.d.ts:3474-3569,5560-5569`
- `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.UIContext.static.d.ets:2647-2710,4032-4038`
- `<OH_ROOT>/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:785-950`
- `interfaces/native/event/drag_and_drop_impl.cpp:169-419`
- `frameworks/core/interfaces/native/node/drag_adapter_impl.cpp:66-119`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_func_wrapper.cpp:360-366`

## 用户故事

### US-1: 从当前 UIContext 发起程序化拖拽

作为 ArkTS 开发者，我希望从当前 `UIContext` 获取 `DragController` 后创建或直接执行 DragAction，以便不依赖手势触发系统拖拽。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 动态 ArkTS API 11 调用 `UIContext.getDragController()`，THEN 返回当前 UIContext 对应的 `DragController`，可调用 `executeDrag` 或 `createDragAction`。 | 正常 |
| AC-1.2 | WHEN 使用 API 18 及以上的动态 ArkTS，THEN 旧全局 `executeDrag/createDragAction` 被标为 deprecated，迁移目标为 `UIContext.DragController`。 | 兼容 |
| AC-1.3 | WHEN 静态 ArkTS API 23 创建 Action 或调用 `startDrag`，THEN 其 SDK 合同允许 `customArray`/custom 为 `undefined`，且 `startDrag()` 返回 `Promise<void> \| null`。 | 边界 |

### US-2: 管理 Action 的配置与生命周期

作为程序化拖拽源开发者，我希望配置 pointer、预览、触点、数据和加载参数，并正确管理每次拖拽的 Action 生命周期。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN C API API 12 在有效 Action 上设置 pointer、PixelMap、触点、数据或 PreviewOption，THEN 将配置写入 Action；WHEN pointer 不在 0–9，THEN 设为 -1 并返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 边界 |
| AC-2.2 | WHEN C API API 20 设置 `DataLoadParams`，THEN Action 使用加载参数；WHEN 与 `SetData` 冲突，THEN 最后调用生效。 | 正常 |
| AC-2.3 | WHEN 一个 ArkTS DragAction 的生命周期结束，THEN 该对象上注册的回调失效；WHEN 下一次起拖，THEN 开发者使用新创建的 Action 替换旧对象。 | 边界 |

### US-3: 监听状态并进入系统拖拽会话

作为需要跟踪程序化拖拽结果的开发者，我希望通过 Action 状态监听得到可用结果，同时了解 ArkUI 与 MSDP 的职责边界。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 动态 ArkTS 对 Action 注册 `on/off('statusChange')`，或静态 ArkTS 注册 `onStatusChange/offStatusChange`，THEN 按各自 SDK 签名接收/取消状态监听。 | 正常 |
| AC-3.2 | WHEN C 状态监听回调被调用，THEN `ArkUI_DragAndDropInfo*` 仅在回调期间使用；WHEN 读取失败信息，THEN status 为 `ARKUI_DRAG_STATUS_UNKNOWN` 或 event 为 null。 | 异常 |
| AC-3.3 | WHEN C Action 通过 adapter 起拖失败，THEN adapter 以 `DRAG_CANCEL` 和 `ENDED` 通知已注册 listener；WHEN 起拖成功，THEN 最终系统会话经 `InteractionInterface::GetInstance()->StartDrag` 发起。 | 恢复 |
| AC-3.4 | WHEN 当前 UIContext 已在拖拽，THEN 不能创建或执行第二个程序化拖拽，现有 NAPI 路径以内部处理失败拒绝。 | 异常 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.3 | R-1、R-2 | Feat-05 | SDK 类型对照 | `UIContext.d.ts:3474-3569,5560-5569`; `UIContext.static.d.ets:2647-2710` |
| AC-2.1~AC-2.3 | R-3、R-4 | Feat-05 | C/ArkTS Host 单测 | `drag_and_drop.h:785-895`; `drag_and_drop_impl.cpp:169-339` |
| AC-3.1~AC-3.4 | R-5~R-7 | Feat-05 | C adapter/NAPI/Interaction mock | `drag_adapter_impl.cpp:66-119`; `drag_drop_func_wrapper.cpp:360-366`; `js_drag_controller.cpp:2085-2179` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 从 UIContext 获取 Controller 并调用 `executeDrag/createDragAction` | 动态 API 11 使用当前 UIContext 的 Controller；静态 API 23 使用静态签名 | API 18 起动态全局 API 仅为 deprecated 兼容入口 | AC-1.1、AC-1.2、AC-1.3 |
| R-2 | 边界 | 调用 ArkTS `DragAction.startDrag` 或状态监听 | 动态返回 `Promise<void>` 且以 `on/off('statusChange')` 注册；静态返回 `Promise<void> \| null` 且以 `onStatusChange/offStatusChange` 注册 | 不以一种前端的返回值或方法名覆盖另一种合同 | AC-1.3、AC-3.1 |
| R-3 | 边界 | C Action 设置 pointer、PixelMap、数据、加载参数或 PreviewOption | 有效输入保存到 Action；pointer 范围为 0–9，越界写 -1 并返回 `PARAM_INVALID`；`DataLoadParams` 与 data 最后调用优先 | PixelMap 数组元素不可为空且 size 不可为负 | AC-2.1、AC-2.2 |
| R-4 | 恢复 | ArkTS Action 生命周期结束后再次起拖 | 旧对象的回调失效；用新 Action 替换旧对象 | 同一时刻未完成的 Action 阻止创建新的 Action | AC-2.3、AC-3.4 |
| R-5 | 行为 | 注册/注销 Action status listener | 动态/静态 ArkTS 按各自方法名处理；C adapter 保存或清空 listener/userData | C `DragAndDropInfo` 是回调瞬时对象，不得保留 | AC-3.1、AC-3.2 |
| R-6 | 恢复 | C adapter 无法启动 Action | 构造 `DRAG_CANCEL`，以 `ENDED` 回调状态 listener | 只在存在 listener 时对外通知 | AC-3.3 |
| R-7 | 行为 | Action 完成转换并进入实际系统起拖 | C API 经 `DragAdapterAPI` 转换；最终由 `DragDropFuncWrapper` 调用 `InteractionInterface::GetInstance()->StartDrag` | ArkUI 只负责 Action 组装和会话对接，不定义 MSDP 内部流程 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-2 | 动态/静态 SDK 对照 | 迁移、`undefined`、返回值与监听方法名差异。 |
| VM-2 | R-3 | C API 单测 | 0–9 pointer、无效 PixelMap/Action、数据与加载参数覆盖。 |
| VM-3 | R-4、R-5 | ArkTS/C 生命周期测试 | 单会话限制、回调失效、listener 瞬时对象。 |
| VM-4 | R-6、R-7 | DragAdapter/Interaction mock | 失败 cancel/ended 回调和 `StartDrag` 对接。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `UIContext.getDragController`、`DragController.executeDrag/createDragAction` | Public ArkTS | preview/drag item、`DragInfo` | Promise、回调或 Action | BusinessError 401/100001 | 从当前 UIContext 程序化起拖。 | AC-1.1、AC-1.3、AC-3.4 |
| `DragAction.startDrag/on/off` 与静态 `onStatusChange/offStatusChange` | Public ArkTS | Action、status callback | Promise 或 null | BusinessError 100001 | 启动和监听 Action。 | AC-1.3、AC-3.1 |
| C `CreateDragAction*`、setter、listener、`OH_ArkUI_StartDrag` | Public C API | node/context、Action、预览/数据/回调 | Action 指针、错误码 | `PARAM_INVALID` | API 12 C 程序化起拖。 | AC-2.1、AC-3.2、AC-3.3 |
| `OH_ArkUI_DragAction_SetDataLoadParams` | Public C API | Action、UDMF load params | `ArkUI_ErrorCode` | `PARAM_INVALID` | API 20 异步数据加载配置。 | AC-2.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| 全局 `dragController.executeDrag/createDragAction` | 废弃 | 动态 API 18 起 | 使用 `UIContext.getDragController()` 返回的实例方法。 | AC-1.2 |
| `DragAction` 动态/静态合同 | 变更 | 返回值和状态监听方法不同 | 按前端 SDK 单独调用，不混用 `on/off` 与 `onStatusChange/offStatusChange`。 | AC-1.3、AC-3.1 |
| `DataLoadParams` | 变更 | C API 20 增加 | 低版本使用既有 `SetData`；可用版本按最后调用优先处理。 | AC-2.2 |

## 接口规格

### 接口定义

**`UIContext.getDragController` / `DragController.createDragAction`**

| 属性 | 值 |
|---|---|
| 函数签名 | 动态 `getDragController(): DragController`、`createDragAction(customArray, dragInfo): DragAction`；静态 API 23 的 customArray 可为 `undefined` |
| 返回值 | 当前 UIContext 的 Controller 或新的 Action |
| 开放范围 | Public ArkTS |
| 错误码 | ArkTS 参数/内部失败为 BusinessError 401/100001 |
| 关联 AC | AC-1.1、AC-1.2、AC-1.3、AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| customArray | `Array<CustomBuilder \| DragItemInfo>` | 动态是；静态可为 undefined | N/A | Builder 仅用于当前拖拽预览；已有 Action 未结束时不能创建新 Action。 |
| dragInfo | `DragInfo` | 是 | N/A | 包含 pointer、数据、预览/触点等公开字段，版本以 SDK 为准。 |

**C `ArkUI_DragAction` 配置、监听与起拖组**

| 属性 | 值 |
|---|---|
| 函数签名 | `OH_ArkUI_CreateDragActionWithNode/Context`、setter、`Register/UnregisterStatusListener`、`OH_ArkUI_StartDrag` |
| 返回值 | Create 返回 Action/null；setter/Start 返回 `int32_t` |
| 开放范围 | Public C API |
| 错误码 | 无效 Action/node/context/option/数据或数组返回 `ARKUI_ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-2.1、AC-2.2、AC-3.2、AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| pointer | `int32_t` | 否 | 0 | 仅 0–9；越界设置内部 -1 并返回 `PARAM_INVALID`。 |
| pixelmapArray/size | PixelMap 数组、`int32_t` | 需要预览时 | N/A | 数组元素不能为 null，size 不能小于 0。 |
| listener | C function pointer | 注册时 | N/A | `ArkUI_DragAndDropInfo*` 仅回调期间有效。 |

## 兼容性声明

- **已有 API 行为变更:** 否；本规格显式记录动态 API 11/18、静态 API 23 和 C API 12/20 的既有差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；Action 配置仅在既有 Action 生命周期内保存。
- **最低支持版本:** 动态 UIContext Controller/Action API 11，动态全局兼容 API 10/11（API 18 废弃），静态 API 23，C Action API 12，C `DataLoadParams` API 20。
- **API 版本号策略:** 以各 canonical SDK 的 `@since`/deprecated 标记为准，静态 `null` 返回和 `undefined` 参数必须单独声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 当前 UIContext 归属 | Controller/Action 必须绑定创建时的 UIContext 或 node 所在实例。 | AC-1.1、AC-2.1 |
| 单会话 | NAPI 路径检测到正在拖拽时拒绝第二次创建/执行。 | AC-2.3、AC-3.4 |
| Action 生命周期 | 结束后的 Action 回调失效，C callback info 不可跨回调保存。 | AC-2.3、AC-3.2 |
| MSDP 边界 | Action 转换后由 `InteractionInterface` 发起系统会话；ArkUI 不定义其内部结果处理。 | AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | 同时只允许一个程序化拖拽；失败 Action 以 cancel/ended 回收可观察状态。 | NAPI/adapter Host 测试 | `js_drag_controller.cpp:2085-2179`; `drag_adapter_impl.cpp:92-100` |
| 性能 | SDK 提示限制预览数量以保持拖拽性能。 | SDK 对照/性能测试 | `UIContext.d.ts:3535-3545` |
| 可测试性 | Action 参数、listener、启动失败和 Interaction 调用均有独立桥接层。 | C/Host mock | `drag_and_drop_impl.cpp:169-419`; `drag_adapter_impl.cpp:66-119` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 无本 Feat 特有 API 差异 | pointer ID 合同和当前 UIContext 归属一致。 | Host/设备集成测试 | `drag_and_drop.h:805-815` |
| 平板 | 无本 Feat 特有 API 差异 | 系统窗口/显示器交接由 `03-04-02/Feat-06` 承接。 | 多窗口集成测试 | `drag_drop_func_wrapper.cpp:360-366` |
| 折叠屏 | 无本 Feat 特有 API 差异 | Action 到 InteractionInterface 的对接不因形态改变。 | 多显示器集成测试 | `drag_drop_func_wrapper.cpp:360-366` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 多窗口/分屏 | 是 | Controller 绑定 UIContext；系统会话窗口路由由框架拖拽能力承接。 | AC-1.1、AC-3.3 |
| 版本升级 | 是 | 旧全局 API 的 deprecated 和动态/静态差异必须保留。 | AC-1.2、AC-1.3、AC-3.1 |
| 生态兼容 | 是 | C API 以 PixelMap/UDMF/回调表达 Action，不能推断 Builder 等价支持。 | AC-2.1、AC-2.2、AC-3.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 程序化 DragAction 与 DragController
  Scenario: 拒绝第二个程序化拖拽
    Given 当前 UIContext 已处于 dragging 状态
    When 调用 createDragAction 或 executeDrag
    Then NAPI 路径以内部处理失败拒绝调用

  Scenario: C Action 启动失败
    Given C Action 已注册 status listener
    When adapter 无法启动系统拖拽
    Then listener 接收 DRAG_CANCEL
    And 状态为 ENDED

  Scenario: C 指针 ID 越界
    Given 已创建有效 C DragAction
    When SetPointerId 传入 10
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID
    And Action 内部 pointer ID 为 -1
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 覆盖动态/静态 ArkTS、C API、生命周期、监听、数据/预览配置、错误边界和 MSDP 对接。
- [x] 每个 AC 至少关联一条规则和一种验证方式。
- [x] 每条规则满足可复现、可观测、边界明确、关联 AC 和不冲突要求。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "UIContext DragController DragAction C DragAdapter status listener and InteractionInterface StartDrag"
```
