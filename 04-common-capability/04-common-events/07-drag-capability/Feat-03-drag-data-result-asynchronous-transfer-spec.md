# 特性规格

## 概览

| 字段 | 内容 |
|---|---|
| 特性名称 | 拖拽数据、结果与异步传输 |
| 特性编号 | Func-04-04-07-Feat-03 |
| 所属 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 优先级 | P1 |
| 目标版本 | 动态 ArkTS API 10/20；静态 ArkTS API 23/26.0.0；C API API 12/20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | `DragEvent` 数据、结果、落放操作与异步 `DataLoadParams` 合同 | 对既有动态/静态 ArkTS、C API、UDMF 与 Manager 落放路径的行为补录；不改变实现。 |

## 输入文档

- `specs/04-common-capability/04-common-events/07-drag-capability/design.md`
- `<OH_ROOT>/interface_sdk-js/api/@internal/component/ets/common.d.ts:10792,11550-11602,11787-11796`
- `<OH_ROOT>/interface_sdk-js/api/arkui/component/common.static.d.ets:6005-6012,6480-6518,6637-6645`
- `<OH_ROOT>/interface_sdk_c/arkui/ace_engine/native/drag_and_drop.h:237-345`
- `interfaces/native/event/drag_and_drop_impl.cpp:871-882`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_manager.cpp:1174-1180,1258-1268,1384-1387,1476-1533,1918-1920`

## 用户故事

### US-1: 在拖拽回调中传递和读取统一数据

作为拖拽源或落放目标开发者，我希望在已有的 `DragEvent` 中写入或读取 `UnifiedData`，以便在不依赖组件私有协议的情况下传输拖拽内容。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 动态 ArkTS 在 API 10 可用的 `DragEvent` 上调用 `setData` 或 `getData`，THEN 其数据合同为 `unifiedDataChannel.UnifiedData`。 | 正常 |
| AC-1.2 | WHEN 静态 ArkTS API 23 调用 `getData()`，THEN 返回 `UnifiedData \| undefined`；THEN 不将动态 ArkTS 的非空返回签名推断为静态合同。 | 边界 |
| AC-1.3 | WHEN C API 的数据/类型获取调用所给数组缓冲区不足，THEN 返回 `ARKUI_ERROR_CODE_BUFFER_SIZE_ERROR`，而不是写入超出调用方缓冲区的数据。 | 异常 |

### US-2: 声明落放结果和操作

作为落放目标开发者，我希望在事件处理期间表达结果、允许的落放操作和数据类型，以便系统反馈与后续落放逻辑使用同一事件上下文。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 动态 ArkTS API 10 调用 `setResult/getResult`，THEN 结果随当前 `DragEvent` 读写；静态 ArkTS 对应 API 从 API 23 提供。 | 正常 |
| AC-2.2 | WHEN C API API 12 在有效 `ArkUI_DragEvent` 上设置或读取 drop operation、result 或 type，THEN 按 `drag_and_drop.h` 声明的枚举/缓冲区合同返回对应状态。 | 正常 |
| AC-2.3 | WHEN 系统拖拽通知到达 Manager，THEN Manager 将通知携带的 result、behavior 和动画信息写回当前 `DragEvent`；DROP 分支再派发客户回调和内部 drop 处理。 | 正常 |

### US-3: 按数据加载策略完成异步数据获取

作为需要远端或延迟数据的落放目标开发者，我希望通过 `DataLoadParams` 选择数据加载策略，以便在落放期间按现有预取或后台请求路径取得数据。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 动态 ArkTS API 20、静态 ArkTS API 26.0.0 或 C API API 20 设置 `DataLoadParams`，THEN 事件标记为使用该加载参数；同一事件同时设置数据时，以最后一次调用为准。 | 正常 |
| AC-3.2 | WHEN C `OH_ArkUI_DragEvent_SetDataLoadParams` 的 event 或 dataLoadParams 为空，THEN 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`。 | 异常 |
| AC-3.3 | WHEN 落放目标禁用数据预取，THEN Manager 进入远端检查/后台请求路径；WHEN 未禁用，THEN 先走既有本地预取处理，再进入内部 onDrop 路径。 | 边界 |

## 验收追踪

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.2 | R-1 | Feat-03 | SDK 类型对照 | `common.d.ts:11550-11602`; `common.static.d.ets:6480-6518` |
| AC-1.3 | R-2 | Feat-03 | C API 单测 | `drag_and_drop.h:237-345` |
| AC-2.1~AC-2.3 | R-3 | Feat-03 | SDK/Manager Host 单测 | `common.d.ts:11550-11602`; `drag_drop_manager.cpp:1174-1180,1918-1920` |
| AC-3.1~AC-3.3 | R-4~R-6 | Feat-03 | SDK、C API、Manager Host 单测 | `common.d.ts:11787-11796`; `drag_and_drop_impl.cpp:871-882`; `drag_drop_manager.cpp:1258-1268,1476-1533` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 在 `DragEvent` 上调用 ArkTS `setData/getData` | 动态 API 10 使用 `UnifiedData`；静态 API 23 的 `getData()` 可返回 `undefined` | SDK 签名是公开合同，不以内部 C++ 表示合并动态和静态可空性 | AC-1.1、AC-1.2 |
| R-2 | 异常 | C 数据/类型读取的调用方数组小于所需元素数 | 返回 `ARKUI_ERROR_CODE_BUFFER_SIZE_ERROR` | 不写入越界内存；有效 event 和数组参数仍须满足 C header 条件 | AC-1.3 |
| R-3 | 行为 | 目标回调读写 result、drop operation 或 type，或 Manager 收到系统通知 | 结果/操作保存在当前事件并供 DROP 分支的客户回调和内部处理消费 | C API 12 与 ArkTS API 10/23 的入口和签名分别受各自 `@since` 约束 | AC-2.1、AC-2.2、AC-2.3 |
| R-4 | 行为 | 同一事件既设置 data 又设置 `DataLoadParams` | 最后一次设置生效；设置 `DataLoadParams` 后标记使用加载参数 | 动态 API 20、静态 API 26.0.0、C API 20 分别适用 | AC-3.1 |
| R-5 | 异常 | C `SetDataLoadParams` 的 event 或参数指针为空 | 返回 `ARKUI_ERROR_CODE_PARAM_INVALID`，不进入内部参数写入 | 空指针不等同于默认加载策略 | AC-3.2 |
| R-6 | 边界 | 落放时 `disableDataPrefetch` 为真或为假 | 为真时检查远端并在需要时后台请求；为假时保留本地预取路径，随后按既有顺序处理内部 onDrop | 该规则只描述 ArkUI 的数据请求分支，不定义 MSDP/UDMF 内部传输实现 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-3 | 动态/静态 SDK 类型对照 | `UnifiedData`、`undefined`、`setResult/getResult` 的版本与签名。 |
| VM-2 | R-2、R-5 | C API 单测 | 缓冲区不足和空指针的真实错误码。 |
| VM-3 | R-3、R-6 | DragDropManager Host 单测 | 系统通知结果写回、DROP 回调、预取与远端请求分支。 |
| VM-4 | R-4 | ArkTS/C API 单测 | 最后调用优先和 `useDataLoadParams` 状态。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `DragEvent.setData/getData/setResult/getResult` | Public ArkTS | `UnifiedData` 或 result | 数据或结果 | N/A | 读写当前事件的数据和结果；动态 API 10。 | AC-1.1、AC-2.1 |
| 静态 `DragEvent` 数据/结果 API | Public ArkTS | 静态 `UnifiedData`、result | `getData(): UnifiedData \| undefined` 等 | N/A | 静态 ArkTS API 23 的对应合同。 | AC-1.2、AC-2.1 |
| `DragEvent.setDataLoadParams` | Public ArkTS | `DataLoadParams` | 当前事件 | N/A | 动态 API 20、静态 API 26.0.0 的加载策略设置。 | AC-3.1 |
| C `ArkUI_DragEvent` data/result/drop-operation/type API | Public C API | event、值或数组缓冲区 | 错误码/输出参数 | `PARAM_INVALID`、`BUFFER_SIZE_ERROR` 等 | API 12 公开数据、结果、操作及类型访问。 | AC-1.3、AC-2.2 |
| `OH_ArkUI_DragEvent_SetDataLoadParams` | Public C API | event、`ArkUI_DataLoadParams*` | 错误码 | `PARAM_INVALID` | API 20 设置 C 异步数据加载参数。 | AC-3.1、AC-3.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| 数据读取可空性 | 变更 | 静态 ArkTS API 23 `getData()` 可为 `undefined`，动态 API 10 签名不同 | 按所选 ArkTS 前端的 SDK 声明处理空值，不跨前端推断 | AC-1.1、AC-1.2 |
| `DataLoadParams` | 变更 | 动态 API 20、静态 API 26.0.0、C API 20 才可用 | 低版本维持数据 API 的既有路径；不要调用未引入的加载参数 API | AC-3.1 |

## 接口规格

### 接口定义

**`DragEvent.setData/getData`**

| 属性 | 值 |
|---|---|
| 函数签名 | 动态 `setData(data: unifiedDataChannel.UnifiedData): void` / `getData(): unifiedDataChannel.UnifiedData`；静态 `getData(): UnifiedData \| undefined` |
| 返回值 | 数据设置无返回；读取返回当前事件数据，静态接口可为 `undefined` |
| 开放范围 | Public ArkTS |
| 错误码 | N/A |
| 关联 AC | AC-1.1、AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| data | `UnifiedData` | 是 | N/A | 必须在当前拖拽事件可写的回调上下文内使用；版本按动态 API 10 / 静态 API 23。 |

**`DragEvent.setDataLoadParams` / `OH_ArkUI_DragEvent_SetDataLoadParams`**

| 属性 | 值 |
|---|---|
| 函数签名 | ArkTS `setDataLoadParams(params: DataLoadParams): void`；C `OH_ArkUI_DragEvent_SetDataLoadParams(ArkUI_DragEvent*, ArkUI_DataLoadParams*)` |
| 返回值 | ArkTS 无返回；C 返回 `ArkUI_ErrorCode` |
| 开放范围 | Public ArkTS / Public C API |
| 错误码 | C 空 event 或空参数返回 `ARKUI_ERROR_CODE_PARAM_INVALID` |
| 关联 AC | AC-3.1、AC-3.2、AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| params / dataLoadParams | `DataLoadParams` / `ArkUI_DataLoadParams*` | 是 | N/A | 动态 API 20、静态 API 26.0.0、C API 20；与数据设置冲突时最后调用优先。 |
| event | `ArkUI_DragEvent*` | 是（C） | N/A | 为空立即返回 `PARAM_INVALID`。 |

**C 数据/结果/操作/类型访问组**

| 属性 | 值 |
|---|---|
| 函数签名 | `drag_and_drop.h` 中 API 12 的 `ArkUI_DragEvent` data、result、drop operation 与 type getter/setter 组 |
| 返回值 | `ArkUI_ErrorCode`、输出参数或类型数量，按声明的具体函数确定 |
| 开放范围 | Public C API |
| 错误码 | 参数非法或输出数组容量不足时按 header 返回，包括 `ARKUI_ERROR_CODE_BUFFER_SIZE_ERROR` |
| 关联 AC | AC-1.3、AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| typesArray / size | C 数组及容量 | 按具体 getter | N/A | 容量不足必须由调用方扩容后重试，不得假定函数可截断成功。 |
| event | `ArkUI_DragEvent*` | 是 | N/A | 必须是当前 C 拖拽回调提供的有效事件。 |

## 兼容性声明

- **已有 API 行为变更:** 否；本规格记录已实现的动态/静态 ArkTS 和 C API 差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；`UnifiedData`/UDMF 的具体内部格式不在本规格扩展。
- **最低支持版本:** 动态数据/结果 API 10；C 数据/结果/operation/type API 12；`DataLoadParams` 动态/C API 20、静态 API 26.0.0；静态数据/结果 API 23。
- **API 版本号策略:** 每个入口以 canonical SDK 的 `@since` 为准；静态 `getData()` 的 `undefined` 必须保留，不以动态签名覆盖。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 公共 API 合同优先 | ArkTS 以 `common.d.ts`/`common.static.d.ets`、C 以 `drag_and_drop.h` 为准；实现只作为行为证据。 | AC-1.1、AC-1.2、AC-2.1、AC-2.2 |
| 事件上下文边界 | 数据、结果和加载参数附着于当前 `DragEvent`，不得将一次回调的事件对象语义延伸为独立持久会话。 | AC-1.1、AC-2.1、AC-3.1 |
| 传输职责边界 | ArkUI 选择预取、远端检查/请求并派发落放；MSDP/UDMF 的内部传输会话不由本规格定义。 | AC-3.3 |
| C 失败可观测 | 空指针与缓冲区容量分别返回既有错误码，不能由 C adapter 静默修正。 | AC-1.3、AC-3.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 可靠性 | 缓冲区不足和空参数具有确定错误码，不产生可用的伪结果。 | C API 单测 | `drag_and_drop.h:237-345`; `drag_and_drop_impl.cpp:871-882` |
| 安全 | 远端数据路径先按既有权限/摘要检查再请求数据。 | Manager Host/集成测试 | `drag_drop_manager.cpp:1258-1268,1476-1533` |
| 可测试性 | 事件数据、结果和加载策略可由 SDK、C adapter 与 Manager 分层验证。 | 分层 Host 单测 | 本规格 VM-1~VM-4 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 无本 Feat 特有差异 | 使用相同的事件数据与加载策略合同。 | Host/设备集成测试 | `drag_drop_manager.cpp:1476-1533` |
| 平板 | 无本 Feat 特有差异 | 多窗口命中与坐标路由由 `03-04-02/Feat-06` 承接。 | 多窗口集成测试 | `pipeline_context.cpp:6248-6275` |
| 折叠屏 | 无本 Feat 特有差异 | 数据加载不因显示形态改变；显示器交接不在本 Feat 定义。 | 多显示器集成测试 | `03-04-02/Feat-06` |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|---|---|---|---|
| 多窗口/分屏 | 是 | 事件数据随当前 Manager 路由的会话消费，窗口交接由框架拖拽 Feat 承接。 | AC-3.3 |
| 多用户 | 是 | 数据访问仍受既有系统数据权限和摘要检查约束。 | AC-3.3 |
| 版本升级 | 是 | 必须按动态、静态和 C 的不同引入版本选择 API。 | AC-1.1、AC-1.2、AC-3.1 |
| 生态兼容 | 是 | 保留 UDMF `UnifiedData`、C 错误码与静态可空性差异。 | AC-1.1~AC-3.2 |

## 行为场景（Gherkin）

```gherkin
Feature: 拖拽数据与异步传输
  Scenario: 使用最后设置的数据加载语义
    Given 当前 DragEvent 已进入可写回调
    When 开发者先设置数据再设置 DataLoadParams
    Then 该事件使用 DataLoadParams

  Scenario: 目标禁用数据预取
    Given 当前落放目标的 disableDataPrefetch 为真
    When Manager 处理 DROP
    Then Manager 执行远端检查并在需要时发起后台请求
    And 再按既有路径处理内部 onDrop

  Scenario: C 调用传入空加载参数
    Given C 回调提供一个 DragEvent
    When 调用 OH_ArkUI_DragEvent_SetDataLoadParams 且 dataLoadParams 为空
    Then 返回 ARKUI_ERROR_CODE_PARAM_INVALID
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 覆盖动态/静态 ArkTS、C API、UDMF、异步预取/远端路径、错误码与版本差异。
- [x] 每个 AC 至少关联一条规则和一种验证方式。
- [x] 每条规则满足可复现、可观测、边界明确、关联 AC 和不冲突要求。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "DragEvent UnifiedData result DataLoadParams and DragDropManager prefetch remote request flow"
```
