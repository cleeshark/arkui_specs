# 特性规格

> Func-04-04-05-Feat-01 鼠标事件注册、命中与分发：固化 `onMouse` 从公开 API 注册、平台输入路由、NG 命中测试到响应链传播的存量行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 鼠标事件注册、命中与分发 |
| 特性编号 | Func-04-04-05-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 8–26.0.0、Node C-API 12–26.0.0、Static API 23–26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 存量鼠标事件行为规格 | 仅新增文档、设计基线和验证追溯，不修改产品源码、公开 API 或默认行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/05-mouse-events/design.md` | Baselined |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:21084` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:12104` | 已核对 |
| Native SDK | `interfaces/native/native_node.h:10121` | 已核对 |
| 主分发实现 | `frameworks/core/pipeline_ng/pipeline_context.cpp:5107` | 已核对 |

## 用户故事

### US-1: 注册和清除鼠标回调

**作为** ArkUI 应用或 NativeNode 开发者，
**我想要** 为组件注册、替换和清除鼠标回调，
**以便** 组件在生命周期内只执行当前有效的处理逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 在有效 FrameNode 上注册 `onMouse` 回调 THEN PRESS、RELEASE、MOVE、WINDOW_ENTER、WINDOW_LEAVE 或 CANCEL 到达该节点时调用该回调 | 正常 |
| AC-1.2 | WHEN 同一公开注册槽连续设置两个 `onMouse` 回调 THEN 第二个回调覆盖第一个回调，之后的鼠标事件不再调用第一个回调 | 边界 |
| AC-1.3 | WHEN Dynamic 目标 API >= 11 且 `.onMouse(undefined)` 到达 JS 桥接 THEN 当前用户鼠标回调被清除 | 正常 |
| AC-1.4 | WHEN Dynamic 目标 API < 11 且 `.onMouse(undefined)` 到达 JS 桥接 THEN 该参数被忽略，已注册回调保持不变 | 边界 |
| AC-1.5 | WHEN `UICommonEvent.setOnMouse(undefined)` 或 Static API 23+ `onMouse(undefined)` 被调用 THEN 目标节点的用户鼠标回调被清除 | 正常 |
| AC-1.6 | WHEN Node C-API 使用有效节点注册或注销 `NODE_ON_MOUSE` THEN 注册返回成功且注销后不再上报；WHEN 节点为空 THEN 注册返回参数错误 | 异常 |

### US-2: 将平台输入路由到正确的事件通道

**作为** ArkUI 输入框架维护者，
**我想要** 区分鼠标按键、滚轴、旋转和兼容转换输入，
**以便** 不同输入语义不会错误进入 `onMouse`。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN MMI PointerEvent 为轴起止、轴更新、旋转或带轴数据的 CANCEL THEN 事件进入 AxisEvent 通道而不进入普通鼠标分发 | 边界 |
| AC-2.2 | WHEN `LEFT_PRESS` 输入兼容转换开启且左键事件可转换为 TouchEvent THEN 事件进入触摸回调并在当次处理中不调用鼠标回调 | 边界 |
| AC-2.3 | WHEN 平台线程接收普通鼠标事件 THEN AceContainer 在 UI 线程中以 rootNode 或显式指定 FrameNode 调用 `PipelineContext::OnMouseEvent` | 正常 |
| AC-2.4 | WHEN 鼠标事件的 UI 任务执行完成 THEN 才通知 MMI 该输入已处理 | 正常 |

### US-3: 按动作类型确定分发时机

**作为** 交互组件开发者，
**我想要** 获得稳定的鼠标回调顺序和 MOVE 合帧行为，
**以便** 实现按键反馈、轨迹处理和穿透式交互。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 普通 MOVE 事件进入 NG Pipeline 且未开启 pass-through THEN 事件按目标节点入队、请求帧刷新，并在 VSync flush 阶段每个 pointer id 分发本帧最后的有效点 | 正常 |
| AC-3.2 | WHEN MOVE 事件处于全局鼠标 pass-through 模式或事件自身 `passThrough=true` THEN 该 MOVE 立即命中和分发，不等待 VSync 队列 | 边界 |
| AC-3.3 | WHEN PRESS、RELEASE、CANCEL、WINDOW_ENTER 或 WINDOW_LEAVE 进入 NG Pipeline THEN 事件在当次 UI 任务中立即命中和分发 | 正常 |
| AC-3.4 | WHEN RELEASE、CANCEL 或 WINDOW_LEAVE 到达前存在尚未分发的同 id MOVE THEN Pipeline 先补偿分发最后 MOVE，再处理终止动作 | 恢复 |

### US-4: 构建鼠标命中结果

**作为** ArkUI 组件框架维护者，
**我想要** 让鼠标命中复用组件通用响应区和坐标变换能力，
**以便** 鼠标与组件的可见区域、变换和 hitTestMode 保持一致。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN EventManager 对 NG FrameNode 执行鼠标命中 THEN 以 `hitTestType=MOUSE` 调用 `FrameNode::TouchTest` 并由 InputEventHub 收集 MouseEventTarget，不调用空实现 `FrameNode::MouseTest` | 正常 |
| AC-4.2 | WHEN 节点不活跃、EventHub 被禁用或坐标不在有效响应区 THEN 该节点不产生 MouseEventTarget | 边界 |
| AC-4.3 | WHEN 节点存在几何变换、responseRegion 或非默认 hitTestMode THEN 命中按 TouchTest 现有变换、子树逆序遍历和阻断规则生成响应链 | 正常 |
| AC-4.4 | WHEN TouchTest 的输入类型为 `MOUSE_BUTTON` THEN 不执行触摸事件专用的 `onTouchIntercept` 回调，鼠标截断由 hitTestMode、responseRegion 和 `stopPropagation` 控制 | 边界 |

### US-5: 按版本维护按压响应链和传播

**作为** 需要兼容多个 API 版本的应用开发者，
**我想要** 了解鼠标按压链和传播规则的版本边界，
**以便** 避免多按键或父子组件的回调顺序发生意外变化。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN action 不属于 PRESS、RELEASE、MOVE、WINDOW_ENTER、WINDOW_LEAVE、CANCEL THEN `DispatchMouseEventNG` 返回 false 且不调用鼠标目标 | 异常 |
| AC-5.2 | WHEN 回调设置 `stopPropagation=true` THEN 该结果同步写回 MouseInfo，EventManager 在当前响应链中停止调用后续目标 | 正常 |
| AC-5.3 | WHEN 回调未设置或设置 `stopPropagation=false` THEN EventManager 继续按响应链顺序调用剩余目标 | 正常 |
| AC-5.4 | WHEN 目标 API >= 12 且非 NONE 按键保持按下时到达 MOVE THEN 复用该 pointer id 已缓存的命中链；WHEN 目标 API < 12 THEN MOVE 重新执行 TouchTest | 边界 |
| AC-5.5 | WHEN 目标 API >= 13 且不同鼠标键分别 PRESS THEN 按 `(pointerId, button)` 独立保存和释放按压链；WHEN 目标 API < 13 THEN 仅左键使用单一按压链 | 边界 |
| AC-5.6 | WHEN 按键事件同时匹配按压时保存的目标链和当前命中链 THEN 先向按压链分发，再向当前链分发，已调用的目标不重复调用 | 正常 |

### US-6: 支持定向、注入和兼容分发

**作为** 窗口场景、动态组件或测试框架开发者，
**我想要** 将鼠标事件定向到指定节点或子容器，
**以便** 事件在正确的组件树和 ContainerScope 中分发。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN WindowScene 或 PostEvent 向有效指定 FrameNode 投递鼠标事件 THEN 以该节点为命中根复用 NG 主分发链 | 正常 |
| AC-6.2 | WHEN PostEvent 事件设置 pass-through THEN 分发后同步返回是否存在鼠标目标，且不污染其他指定节点的队列 | 正常 |
| AC-6.3 | WHEN DynamicComponent 将 PointerEvent 投递到子 UIContent THEN 切换到子 instance 的 ContainerScope 后再进入相同平台入口 | 正常 |
| AC-6.4 | WHEN 运行 legacy Pipeline THEN 每条鼠标事件执行 scale、`RenderNode::MouseDetect` 和立即分发，不使用 NG MOVE VSync 队列 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.6 | R-1~R-4 | 已有实现 | 单测/API 契约核对 | `view_abstract_test_ng_new.cpp:884`、`native_node_test.cpp:10291` |
| AC-2.1~AC-2.4 | R-5~R-7 | 已有实现 | 单测/源码追溯 | `ace_view_ohos.cpp:103`、`ace_container.cpp:1387` |
| AC-3.1~AC-3.4 | R-8~R-10 | 已有实现 | Pipeline 单测 | `pipeline_context_test_ng_eight.cpp:477`、`:754`、`:1689` |
| AC-4.1~AC-4.4 | R-11~R-13 | 已有实现 | 命中单测/源码追溯 | `input_event_hub_test_ng.cpp:250`、`frame_node_test_ng_coverage.cpp:3038` |
| AC-5.1~AC-5.6 | R-14~R-17 | 已有实现 | EventManager 单测 | `event_manager_test_ng_two_issuse.cpp:90`、`event_manager_test_ng_issuse.cpp:897` |
| AC-6.1~AC-6.4 | R-18~R-20 | 已有实现 | 定向分发单测/源码追溯 | `post_event_manager_test_ng.cpp:2933`、`event_manager_test_ng_new.cpp:673` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 有效节点第一次设置 `onMouse` | InputEventHub 存储用户回调并在命中时创建 MouseEventTarget | 用户公开回调为单槽 | AC-1.1 |
| R-2 | 边界 | 同一槽再次设置回调 | 新回调替换旧回调 | 内部 `AddOnMouseEvent` 列表不属于该公开单槽 | AC-1.2 |
| R-3 | 边界 | Dynamic `.onMouse(undefined)` | 目标 API >= 11 时清除，目标 API < 11 时忽略 | 非函数非 undefined 参数一律忽略 | AC-1.3, AC-1.4 |
| R-4 | 异常 | Node C-API 注册 `NODE_ON_MOUSE` | 有效节点返回 0，空节点返回参数错误，注销清除用户回调 | 不修改 C ABI | AC-1.5, AC-1.6 |
| R-5 | 边界 | MMI action 属于 Axis/Rotate 范围 | 进入 AxisEvent 而不进入 MouseEvent | 触摸板 CANCEL 和含 axis 的 CANCEL 也属于该分支 | AC-2.1 |
| R-6 | 边界 | `LEFT_PRESS` 兼容转换开启且左键 action 可转换 | 调用 TouchEvent 通道后结束本次鼠标处理 | 右键和不可转换 action 继续走 MouseEvent | AC-2.2 |
| R-7 | 行为 | 平台收到普通鼠标输入 | 通过 UI 线程任务调用 root 或指定节点 Pipeline 入口，任务后 MarkProcessed | 回调已在 UI 线程时直接执行 | AC-2.3, AC-2.4 |
| R-8 | 行为 | 普通 MOVE 且非 pass-through | 按 FrameNode 入队、RequestFrame，VSync 时每个 id 选末点分发 | 同帧其他点进入 history，字段规格属于 Feat-02 | AC-3.1 |
| R-9 | 边界 | MOVE 且全局或事件 pass-through | 立即命中和分发 | 不进入 MOVE 队列 | AC-3.2 |
| R-10 | 恢复 | 非 MOVE 终止动作到达前存在未分发 MOVE | 先补偿最后 MOVE，然后继续终止动作 | 仅处理相同 pointer id | AC-3.3, AC-3.4 |
| R-11 | 行为 | NG EventManager 执行鼠标命中 | 以 `MOUSE` hitTestType 调用 FrameNode::TouchTest 并收集 MouseEventTarget | `FrameNode::MouseTest` 不参与当前 NG 主链 | AC-4.1 |
| R-12 | 边界 | 节点无效、禁用或点位超出响应区 | 返回区域外且不收集鼠标目标 | 坐标变换后再判定响应区 | AC-4.2, AC-4.3 |
| R-13 | 边界 | inputEventType 为 `MOUSE_BUTTON` | 跳过 onTouchIntercept，保留 hitTestMode/responseRegion/stopPropagation 语义 | 不将滚轴 AxisEvent 归入本规则 | AC-4.4 |
| R-14 | 异常 | action 不在六种有效 MouseAction 内 | 返回 false，不分发 | HOVER/PULL 等由其他通道处理 | AC-5.1 |
| R-15 | 行为 | MouseEventTarget 回调完成 | 将 MouseInfo.stopPropagation 同步返回 EventManager，true 截断、false 继续 | 回调对象生命期仅限同步调用 | AC-5.2, AC-5.3 |
| R-16 | 边界 | 目标 API >= 12 的按键 MOVE | 复用 pointer id 缓存命中链 | API < 12 每次重新 TouchTest | AC-5.4 |
| R-17 | 边界 | 目标 API >= 13 的多按键事件 | 以 `(pointerId, button)` 管理按压链，先按压链后当前链并去重 | API < 13 仅左键单链 | AC-5.5, AC-5.6 |
| R-18 | 行为 | WindowScene/PostEvent 指定节点 | 以指定节点为根复用 NG 分发，pass-through 同步反馈命中结果 | 空或无效节点不分发 | AC-6.1, AC-6.2 |
| R-19 | 行为 | DynamicComponent 投递 PointerEvent | 切换子 instance ContainerScope 后进入平台鼠标入口 | 不在父 ContainerScope 直接调用子节点 | AC-6.3 |
| R-20 | 边界 | legacy Pipeline 收到鼠标事件 | 逐条 scale、MouseDetect、立即分发和 FlushMessages | 不使用 NG MOVE VSync 合帧 | AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.5, R-1~R-3 | Host UT | ViewAbstract/InputEventHub 注册、覆盖、清除和重新注册 |
| VM-2 | AC-1.6, R-4 | NativeNode UT | `NODE_ON_MOUSE` 合法节点成功、空节点报错、注销生效 |
| VM-3 | AC-2.1~AC-2.2, R-5~R-6 | Adapter UT/源码追溯 | Axis 分流和左键兼容转 Touch 时不进入 onMouse |
| VM-4 | AC-2.3~AC-2.4, R-7 | 集成测试 | UI 线程、root/指定节点和 MarkProcessed 顺序 |
| VM-5 | AC-3.1~AC-3.4, R-8~R-10 | Pipeline Host UT | MOVE 入队、pass-through 立即分发、终止动作补偿 |
| VM-6 | AC-4.1~AC-4.3, R-11~R-12 | EventManager/InputEventHub UT | TouchTest(MOUSE)、目标收集、无效节点不命中 |
| VM-7 | AC-4.4, R-13 | Host UT/源码追溯 | MOUSE_BUTTON 不触发 onTouchIntercept |
| VM-8 | AC-5.1, R-14 | EventManager 参数化 UT | 仅六种 MouseAction 可进入 NG 鼠标目标分发 |
| VM-9 | AC-5.2~AC-5.3, R-15 | EventManager UT + C-API UT | stopPropagation true/false 的调用计数和同步写回 |
| VM-10 | AC-5.4~AC-5.6, R-16~R-17 | 版本化 Host UT | API 12 命中缓存与 API 13 多键按压链 |
| VM-11 | AC-6.1~AC-6.3, R-18~R-19 | PostEvent/集成测试 | 指定节点隔离、穿透结果和子 ContainerScope |
| VM-12 | AC-6.4, R-20 | legacy Host UT | legacy 路径可分发且不使用 NG MOVE 队列 |

## API 变更分析

> 本次是存量能力补录，不新增或修改 API。下表为纳入规格的现有 ArkTS 与 C-API 契约。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `CommonMethod<T>.onMouse` | Public | `Callback<MouseEvent>`；Static 允许 `undefined` | 当前组件 | N/A | 设置或在支持的版本中清除鼠标回调 | AC-1.1~AC-1.5 |
| `UICommonEvent.setOnMouse` | Public | `Callback<MouseEvent> | undefined` | `void` | N/A | 为 FrameNode 事件对象设置或清除鼠标回调 | AC-1.5 |
| `ArkUI_NativeNodeAPI_1::registerNodeEvent` | Public/NDK | node、`NODE_ON_MOUSE`、targetId、userData | `int32_t` | 0/参数错误/不支持 | 注册 NativeNode 鼠标事件 | AC-1.6 |
| `ArkUI_NativeNodeAPI_1::unregisterNodeEvent` | Public/NDK | node、`NODE_ON_MOUSE` | `void` | N/A | 注销 NativeNode 鼠标事件 | AC-1.6 |
| `OH_ArkUI_PointerEvent_SetStopPropagation` | Public/NDK | inputEvent、bool | `int32_t` | 0/401 | 设置指针事件停止传播标志 | AC-5.2, AC-5.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 无产品 API 变更 | 继续使用现有接口 | AC-1.1~AC-6.4 |

## 接口规格

### 接口定义

**CommonMethod<T>.onMouse**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onMouse(event: (event: MouseEvent) => void): T`; Static: `onMouse(event: ((event: MouseEvent) => void) | undefined): this` |
| 返回值 | `T/this` — 当前组件，支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5、AC-5.1~AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | `(MouseEvent) => void` | Dynamic API 8 类型声明为是 | 无 | 非函数参数不注册；Dynamic 的 `undefined` 清除行为受目标 API 11 门控 |
| event | `((MouseEvent) => void) | undefined` | Static API 23+ 为否 | `undefined` | `undefined` 清除当前用户回调 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 注册合法回调 | 覆盖旧用户回调并参与命中分发 | AC-1.1, AC-1.2 |
| 2 | 支持清除的版本传入 `undefined` | 清除回调 | AC-1.3, AC-1.5 |
| 3 | 回调设置 `stopPropagation` | 当次同步传播链读取该值 | AC-5.2, AC-5.3 |

**ArkUI_NativeNodeAPI_1::registerNodeEvent / unregisterNodeEvent**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t registerNodeEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType, int32_t targetId, void* userData)` / `void unregisterNodeEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType)` |
| 返回值 | 注册返回 ArkUI 错误码；注销无返回值 |
| 开放范围 | Public/NDK |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR`、`ARKUI_ERROR_CODE_PARAM_INVALID`、`ARKUI_ERROR_CODE_ATTRIBUTE_OR_EVENT_NOT_SUPPORTED`、`ARKUI_ERROR_CODE_NOT_SUPPROTED_FOR_ARKTS_NODE` |
| 关联 AC | AC-1.6、AC-5.2、AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| node | `ArkUI_NodeHandle` | 是 | 无 | 必须是允许注册事件的有效 NativeNode |
| eventType | `ArkUI_NodeEventType` | 是 | 无 | 本特性只规定 `NODE_ON_MOUSE` |
| targetId | `int32_t` | 是 | 0 | 原样随 ArkUI_NodeEvent 返回 |
| userData | `void*` | 否 | `nullptr` | 回调期间由调用方管理生命周期 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效节点注册 `NODE_ON_MOUSE` | 同步返回成功，鼠标命中时产生 ArkUI_UIInputEvent | AC-1.6 |
| 2 | 空节点注册 | 返回参数错误 | AC-1.6 |
| 3 | C 回调设置 stopPropagation | 结果同步写回 MouseInfo 并截断后续目标 | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 是，存在已实现的版本边界：Dynamic API 11 开始支持 `undefined` 清除回调，API 12 开始复用按键 MOVE 命中链，API 13 开始按 pointer/button 管理多键按压链。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic API 8；Node C-API 12；Static API 23。
- **API 版本号策略:** 按 canonical SDK `@since` 和 `AceApplicationInfo` 的目标 API 分支同时标注；当声明版本与运行时目标版本不同时，以源码中的运行时分支规定行为。
- **legacy 兼容:** legacy Pipeline 保留立即分发，不承诺与 NG MOVE VSync 合帧时机一致。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 分层方向 | SDK/Frontend → ViewAbstract/InputEventHub → Pipeline/EventManager → MouseEventTarget，核心层不反向依赖前端 | AC-1.1~AC-6.4 |
| UI 线程 | PipelineContext 命中和分发在 UI 线程执行 | AC-2.3, AC-2.4 |
| 命中复用 | NG 必须复用 TouchTest 的 responseRegion、变换和 hitTestMode 管线 | AC-4.1~AC-4.4 |
| 同步传播 | stopPropagation 必须在回调返回后、调用下一目标前生效 | AC-5.2, AC-5.3 |
| Feat 边界 | MouseEvent 坐标、rawDelta、pressedButtons、history 和 eventHandleId 的字段规格属于 Feat-02 | AC-3.1, AC-6.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 非 pass-through MOVE 在单次 VSync 内每个 pointer id 最多对外分发一个主点 | Pipeline UT | `pipeline_context.cpp:5333` |
| 功耗 | 无额外定时器；MOVE 复用帧调度 | 代码评审 | `pipeline_context.cpp:5164` |
| 内存 | flush 后移出 MOVE 队列，RELEASE/CANCEL 后清理对应按压链 | Host UT | `event_manager.cpp:2088`、`pipeline_context.cpp:5321` |
| 安全 | ArkTS `onMouse` 无权限要求；NativeNode 指针必须为有效句柄 | API/Native UT | `native_node_test.cpp:10291` |
| 可靠性 | 无回调、无效 action、空节点时不崩溃且不分发 | Host UT | `event_manager_test_ng_two_issuse.cpp:149` |
| 可测试性 | 注册、命中、分发、传播、pass-through 和版本分支可通过 Host UT 观测 | Host UT | VM-1~VM-12 |
| 自动化维测 | 按下/释放记录 InputTracking 且分发带 trace | 日志/trace | `pipeline_context.cpp:5110` |
| 定界定位 | 平台接收和 Pipeline 消费均记录 touchEventId/action | 日志检查 | `ace_container.cpp:1391` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 连接鼠标或触控板时使用相同分发；无鼠标输入时不触发 | 输入能力取决于硬件和系统 MMI | 外接鼠标集成测试 | 平台 MMI 入口 |
| 平板 | 无框架行为差异 | 遵循同一 API 版本分支 | 集成测试 | 同上 |
| 折叠屏 | 折叠状态不改变注册和传播规则 | 坐标数据变化由 Feat-02 规定 | 多窗口/外接鼠标测试 | WindowScene 定向路径 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|------|------|---------|
| 无障碍 | 是 | 普通鼠标命中同时通知无障碍悬停管理，无障碍悬停的状态机不在本 Feat 展开 | AC-4.1 |
| 大字体 | 否 | 不改变鼠标事件注册和分发 | 无 |
| 深色模式 | 否 | 不改变事件行为 | 无 |
| 多窗口/分屏 | 是 | WindowScene 可以指定 FrameNode 为分发根 | AC-6.1 |
| 多用户 | 否 | 无持久化用户数据 | 无 |
| 版本升级 | 是 | API 11/12/13 存在明确行为分支 | AC-1.3~AC-1.5, AC-5.4~AC-5.5 |
| 生态兼容 | 是 | Dynamic、Static、Modifier 和 NativeNode 入口最终收敛到 InputEventHub | AC-1.1~AC-1.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 鼠标事件注册、命中与分发
  作为 ArkUI 交互组件开发者
  我想要使用稳定的鼠标响应链
  以便在多版本、多按键和多窗口场景中获得可预期回调

  Scenario: 普通 MOVE 在 VSync 时分发
    Given 节点已注册 onMouse 且未开启 pass-through
    When 同一 pointer id 在一帧内产生多个 MOVE
    Then Pipeline 在 VSync flush 阶段分发本帧主点
    And 同帧其他点仅作为历史数据传递给 Feat-02 定义的数据模型

  Scenario: 停止父级传播
    Given 子节点和父节点均已注册 onMouse
    When 子节点回调同步调用 stopPropagation
    Then 当次响应链不再调用后续目标

  Scenario Outline: API 版本化响应链
    Given 应用目标 API 为 <version>
    When 鼠标按键保持按下并产生 MOVE
    Then 命中策略为 <strategy>

    Examples:
      | version | strategy |
      | 11 | 每次 MOVE 重新命中 |
      | 12 | MOVE 复用 pointer id 缓存命中链 |
      | 13 | MOVE 复用命中链且按 pointerId/button 管理按压链 |

  Scenario: 兼容层将鼠标左键转为触摸
    Given LEFT_PRESS 兼容转换已开启
    When 左键按压事件可成功转换为 TouchEvent
    Then 调用触摸回调
    And 当次不调用 onMouse
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：事件注册、路由、分发时机、命中和传播属于本 Feat，MouseEvent 字段属于 Feat-02，悬停视觉属于 Feat-03
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC 和无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "onMouse registration reset InputEventHub MouseEventTarget"
  - repo: "openharmony/arkui_ace_engine"
    query: "PipelineContext OnMouseEvent VSync MouseTest DispatchMouseEventNG API 12 API 13"
  - repo: "openharmony/arkui_ace_engine"
    query: "NODE_ON_MOUSE stopPropagation post event dynamic component legacy pipeline"
```

**关键文档：** `specs/04-common-capability/04-common-events/05-mouse-events/design.md`
