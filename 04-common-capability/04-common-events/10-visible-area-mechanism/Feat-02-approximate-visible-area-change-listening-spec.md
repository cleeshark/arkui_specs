# 特性规格

> Func-04-04-10-Feat-02 近似可见区域变化监听：固化 `onVisibleAreaApproximateChange` 在 ArkTS 与 Native Node 通道中的阈值、期望更新间隔、视口测量、节流调度和兼容性行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 近似可见区域变化监听 |
| 特性编号 | Func-04-04-10-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | UICommonEvent API 12，Dynamic API 18，Native API 17/21；Static/`measureFromViewport` 版本待同基线 SDK 复核 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkTS 近似监听规格 | 补录 options、ratios、callback、`expectedUpdateInterval`、`measureFromViewport` 和清理行为 |
| ADDED | 近似节流调度规格 | 补录 100 ms 下限、单在途任务、IDLE 调度、最终采样与生命周期归零 |
| ADDED | Native 近似监听规格 | 补录 API 17 generic 与 API 21 便捷注册/注销、payload、错误码和实现偏差 |
| MODIFIED | 共享可见区域设计 | 将 Feat-02 增量合并到 Func-04-04-10 的 `design.md` 对应章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/10-visible-area-mechanism/design.md` | 本次增量合并 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:24562-24574,29240-29272,29421-29432` | 已核查；来自本机可用 SDK checkout，未确认与目标 ace_engine 同基线 |
| Dynamic Bridge | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:12108-12162` | 已核查 |
| Modifier Bridge | `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:4046-4058,5888-5901,6299-6301` | 已核查 |
| Static/生成入口 | `frameworks/core/interfaces/native/implementation/common_method_modifier.cpp:7246-7283`；`frameworks/core/interfaces/native/implementation/ui_common_event_accessor.cpp:242-260` | 已核查 |
| 核心节流实现 | `frameworks/core/components_ng/base/view_abstract.cpp:11548-11591`；`frameworks/core/components_ng/base/frame_node.cpp:2837-2903` | 已核查 |
| Native API | `interfaces/native/native_type.h:3693-3807`；`interfaces/native/native_node.h:10538-10555,14348-14376` | 已核查 |
| Native 映射 | `interfaces/native/node/node_model.cpp:550-647,1779-1825`；`interfaces/native/node/node_utils.cpp:936-970` | 已核查 |

> 本文档描述存量实现，不提出行为修正。目标 checkout 缺少同基线 `interface_sdk-js`，因此无法从当前源码反推未在可用 canonical SDK 中出现的 Static 或 `measureFromViewport` 开放版本。

## 用户故事

### US-1: 通过 ArkTS 注册和清理近似监听

**作为** ArkUI 应用开发者，

**我想要** 使用 options 和回调注册近似可见区域监听，

**以便** 在降低计算频率的同时获得可见比例阈值通知。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN ArkTS 传入包含 ratios 的 options 和有效 callback THEN当前组件的近似监听槽保存 ratios、callback、period 和 `measureFromViewport` | 正常 |
| AC-1.2 | WHEN Legacy Dynamic 参数数量不是 2、options 不是对象、ratios 不是数组或 callback 不是函数 THEN本次调用被忽略且已有监听保持不变 | 异常 |
| AC-1.3 | WHEN canonical Dynamic API 18 调用的 event 为 `undefined` THEN SDK 契约要求重置；WHEN经当前 Legacy Dynamic Bridge 传入 `undefined` THEN Bridge 直接返回并保留旧监听 | 边界 |
| AC-1.4 | WHEN Modifier 路径的 `options.ratios` 或 event 为 `undefined` THEN执行近似监听 reset | 正常 |
| AC-1.5 | WHEN Legacy Dynamic 输入 N 个 ratios THEN当前实现先保留 N 个初始化为 0 的元素，再追加 N 个钳制值，最终向核心传入 2N 个阈值且前 N 项为 0 | 边界 |
| AC-1.6 | WHEN Common/Modifier 路径接收非数值或越界 ratio THEN按入口规则转换并钳制到 [0,1]；WHEN Static UICommonEvent 路径接收 ratios THEN入口层直接转换数组而不执行同样钳制 | 边界 |
| AC-1.7 | WHEN源码入口提供 `measureFromViewport` THEN该值进入近似回调配置；WHEN查阅当前可用 Dynamic canonical SDK THEN options 中未声明该字段，开放版本作为兼容风险记录 | 边界 |
| AC-1.8 | WHEN UICommonEvent event 缺失 THEN调用专用 Clear；WHEN生成 CommonMethod event 缺失 THEN当前实现调用 setter 注册空 callback 和空 ratios，而不是执行同一清理路径 | 边界 |

### US-2: 配置期望更新间隔

**作为** 关注性能和回调频率的开发者，

**我想要** 为近似监听配置期望更新间隔，

**以便** 控制可见比例计算与业务回调的节流粒度。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN ArkTS options 未提供数字类型 `expectedUpdateInterval` THEN Legacy/Modifier 默认使用 1000 ms | 正常 |
| AC-2.2 | WHEN Legacy Dynamic 输入负数 interval THEN恢复为 1000 ms；WHEN输入 0~99 ms THEN核心最终使用 100 ms | 边界 |
| AC-2.3 | WHEN Modifier 或 FrameNode 路径输入 interval=0 THEN JS truthiness 将其替换为 1000 ms；WHEN输入负数或 1~99 ms THEN核心最终使用 100 ms | 边界 |
| AC-2.4 | WHEN Native options setter 输入负数 THEN保存 1000 ms；WHEN输入 0~99 ms THEN保存 100 ms | 边界 |
| AC-2.5 | WHEN API 21 Native 便捷入口输入 float interval THEN下传到 int32 路径时截断；负数或截断后小于 100 的值由核心改为 100 ms | 边界 |
| AC-2.6 | WHEN interval=100 ms 或更大 THEN核心保存该整数 period；该值表示期望节流间隔，不承诺精确定时周期 | 正常 |

### US-3: 在节流任务中计算并派发阈值变化

**作为** ArkUI 应用开发者，

**我想要** 在期望间隔内合并频繁的几何变化，

**以便** 每个节流窗口只处理最终可见比例。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Pipeline 的 UI VSync area-change 阶段发现近似监听 THEN每个节点最多保持一个近似任务在途 | 正常 |
| AC-3.2 | WHEN距上次近似任务执行时间小于 period THEN投递延迟完整 period 的 UI IDLE 任务，而不是仅延迟剩余时间 | 边界 |
| AC-3.3 | WHEN任务执行前组件几何连续变化 THEN任务执行时重新读取当前可见矩形并使用最终比例判断阈值 | 正常 |
| AC-3.4 | WHEN `measureFromViewport=false` THEN使用普通 visibleRect/frameRect；WHEN为 true THEN使用 inner visibleRect/inner frameRect | 正常 |
| AC-3.5 | WHEN可见矩形或帧矩形为空 THEN比例为 0；WHEN均非空 THEN比例为裁剪后轴对齐矩形面积除以帧矩形面积并钳制到 [0,1] | 正常 |
| AC-3.6 | WHEN一次采样跨越乱序或重复 ratios 中的一个或多个阈值 THEN按输入顺序遍历、不排序不去重，并在遍历完成后只调用一次 callback | 边界 |
| AC-3.7 | WHEN currentRatio 与上次近似采样比例近似相等 THEN不执行阈值回调；WHEN监听刚注册且首次采样仍为 0 THEN即使 ratios 含 0 也不产生首次回调 | 边界 |
| AC-3.8 | WHEN阈值上穿或下穿 THEN回调分别携带 `isVisible=true` 或 false，并携带本次最终 currentRatio | 正常 |

### US-4: 处理重注册和生命周期归零

**作为** 需要动态调整曝光采样策略的开发者，

**我想要** 明确重注册、隐藏和销毁场景的状态延续，

**以便** 避免错误假设新的监听从空状态开始。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN同一节点重新注册近似监听 THEN替换近似 callback、ratios、period 和 measure 配置，但不重置历史采样比例、历史回调比例、上次触发时间或在途任务标志 | 边界 |
| AC-4.2 | WHEN旧近似任务已排队后发生重注册 THEN旧任务按原排队时点执行，并在执行时读取新的回调和阈值配置 | 边界 |
| AC-4.3 | WHEN用户精确、内部精确和近似监听同时存在 THEN EventHub 将三者保存在独立槽位 | 正常 |
| AC-4.4 | WHEN窗口后台、节点离主树、自身隐藏/inactive 或祖先隐藏/inactive THEN近似任务采样比例按 0 处理 | 正常 |
| AC-4.5 | WHEN detach 或销毁触发 `forceDisappear` 且历史近似采样比例非 0 THEN绕过 period 立即执行一次比例 0 的阈值判断 | 恢复 |
| AC-4.6 | WHEN `forceDisappear` 发生但近似任务从未执行、历史采样比例仍为 0 THEN即使节点实际曾可见也不补发归零回调 | 边界 |
| AC-4.7 | WHEN节点销毁且延迟任务尚未执行 THEN销毁路径清理三个槽和 Pipeline 登记，延迟任务通过弱引用升级失败后退出 | 恢复 |

### US-5: 通过 Native Node 使用近似监听

**作为** Native UI 开发者，

**我想要** 使用 generic 或 API 21 便捷接口订阅近似可见区域变化，

**以便** 在 C API 场景控制采样间隔并接收比例通知。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN API 17 使用 `ArkUI_VisibleAreaEventOptions` 配置 ratios/interval 并注册 `NODE_VISIBLE_AREA_APPROXIMATE_CHANGE_EVENT` THEN generic 链路建立近似监听 | 正常 |
| AC-5.2 | WHEN API 21 options 额外设置 `measureFromViewport` THEN generic 链路下传该值；WHEN使用 API 21 便捷注册函数 THEN因接口无该参数而使用默认 false | 边界 |
| AC-5.3 | WHEN新建 options 但未设置 ratios THEN generic 注册因 ratios 为空返回 401；WHEN未显式设置 measure THEN公开契约期望 false，但 Create 当前未初始化该字段 | 异常 |
| AC-5.4 | WHEN `SetRatios` 输入越界 float THEN每项钳制到 [0,1]；WHEN size<=0 THEN清空 ratios 后返回成功；WHEN value=null 且 size>0 THEN当前实现会解引用空指针，作为实现风险记录 | 异常 |
| AC-5.5 | WHEN Native 近似事件派发 THEN两条链路均输出 `data[0].i32=isVisible` 和 `data[1].f32=currentRatio` | 正常 |
| AC-5.6 | WHEN generic 事件派发 THEN调用方 targetId 写入 eventId、实际 FrameNode ID 写入 targetId 并透传 userData；WHEN便捷链路派发 THEN eventId 固定为 0，仍透传节点 ID 和 userData | 正常 |
| AC-5.7 | WHEN API 21 便捷接口重复注册或注销后重注册 THEN ratios/interval/userData 更新，但 callback map 保留首次 callback，最终使用新配置和旧 callback | 边界 |
| AC-5.8 | WHEN generic 或便捷注册在写入事件映射后因 options/ratios 校验失败 THEN返回错误但注册元数据可能残留 | 异常 |
| AC-5.9 | WHEN generic 注销近似事件 THEN删除事件映射，但公共 reset 表对该事件为空，核心近似监听可能继续存在且后续事件因 metadata 缺失被丢弃 | 恢复 |
| AC-5.10 | WHEN API 21 便捷注销成功 THEN清除 CommonEvent 元数据并显式清理核心近似监听 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.8 | R-1~R-7 | 已有实现 | SDK/Bridge/Static 源码审查与单测 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:12108-12162`；`frameworks/core/interfaces/native/implementation/ui_common_event_accessor.cpp:242-260` |
| AC-2.1~AC-2.6 | R-8~R-12 | 已有实现 | 前端/核心/Native 边界测试 | `frameworks/core/components_ng/base/view_abstract.cpp:11548-11591`；`interfaces/native/node/native_node_extented.cpp:1266-1278` |
| AC-3.1~AC-3.8 | R-13~R-19 | 已有实现 | FrameNode/Pipeline 可控时钟与几何单测 | `frameworks/core/components_ng/base/frame_node.cpp:2837-2903`；`frameworks/core/pipeline_ng/pipeline_context.cpp:1362-1374,5674-5685` |
| AC-4.1~AC-4.7 | R-20~R-25 | 已有实现 | 重注册/生命周期 Host 集成测试 | `frameworks/core/components_ng/base/frame_node.cpp:2605-2665,2866-2903,8615-8625` |
| AC-5.1~AC-5.10 | R-26~R-34 | 已有实现 | Native C API 端到端与失败注入测试 | `interfaces/native/node/node_model.cpp:550-647,1779-1825`；`interfaces/native/node/node_utils.cpp:936-970` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ArkTS options.ratios 和 callback 有效 | 保存近似槽的 ratios、callback、period、measure | 与用户精确槽独立 | AC-1.1 |
| R-2 | 异常 | Legacy 参数数量/类型非法 | 静默返回并保留旧近似监听 | 不按 SDK `undefined` 契约清理 | AC-1.2, AC-1.3 |
| R-3 | 恢复 | Modifier ratios 或 event 为 `undefined` | 执行 reset | 与 Legacy Dynamic 行为不同 | AC-1.4 |
| R-4 | 边界 | Legacy 输入 N 个 ratios | 形成 N 个前置 0 加 N 个钳制值 | 当前 vector 初始化与 push 行为 | AC-1.5 |
| R-5 | 边界 | ratios 经不同 ArkTS/Static 入口 | Common/Modifier 钳制；UICommonEvent 入口不做同样钳制 | SDK 契约范围仍为 [0,1] | AC-1.6 |
| R-6 | 边界 | 使用 `measureFromViewport` | 源码下传配置；可用 canonical SDK 未声明该字段 | 开放版本不得从源码推断 | AC-1.7 |
| R-7 | 恢复 | Static event 缺失 | UICommonEvent Clear；CommonMethod 空回调重注册 | 两条链路不可合并描述 | AC-1.8 |
| R-8 | 行为 | interval 缺失或非数字 | 默认 1000 ms | 入口默认值 | AC-2.1 |
| R-9 | 边界 | Legacy interval<0 或 0~99 | 负数为 1000；其余核心下限 100 | 0 最终为 100 | AC-2.2 |
| R-10 | 边界 | Modifier interval=0、<0 或 1~99 | 0 为 1000；负数和 1~99 核心为 100 | JS truthiness 差异 | AC-2.3 |
| R-11 | 边界 | Native options 或便捷入口输入低间隔 | options 负数为 1000；便捷负数为 100；0~99 为 100 | 便捷 float 先截断 | AC-2.4, AC-2.5 |
| R-12 | 行为 | period>=100 | 保存整数 period 作为期望节流值 | 不保证固定周期 | AC-2.6 |
| R-13 | 行为 | VSync area-change 检测近似槽 | 若无在途任务则投递一个 UI 任务 | 每节点最多一个任务在途 | AC-3.1 |
| R-14 | 边界 | 距上次执行小于 period | 延迟完整 period，PriorityType::IDLE | 非剩余时长 | AC-3.2 |
| R-15 | 行为 | 延迟任务开始执行 | 读取任务时最新几何与最新回调配置 | 尾沿采样 | AC-3.3 |
| R-16 | 行为 | 根据 measure 选择矩形 | false 选 normal，true 选 inner | 共享 Feat-01 可见矩形缓存 | AC-3.4, AC-3.5 |
| R-17 | 边界 | 比例跨越一个或多个阈值 | 原序遍历后回调一次最终 ratio | 不排序、不去重 | AC-3.6, AC-3.8 |
| R-18 | 边界 | currentRatio 与上次采样近似相等 | 不执行回调 | 首次 0 也被去重 | AC-3.7 |
| R-19 | 行为 | 比例上穿/下穿 | 分别回调 true/false 和最终 ratio | 0/1 使用端点分支 | AC-3.8 |
| R-20 | 边界 | 近似监听重注册 | 覆盖配置但保留历史和任务状态 | 旧任务读取新配置 | AC-4.1, AC-4.2 |
| R-21 | 行为 | 三类可见区域监听并存 | EventHub 使用三个独立槽 | Pipeline nodeId 共享 | AC-4.3 |
| R-22 | 行为 | 后台、离树、隐藏或 inactive | 任务采样 ratio=0 | 与精确监听共享失效判定 | AC-4.4 |
| R-23 | 恢复 | forceDisappear 且历史 ratio 非 0 | 绕过节流立即执行归零阈值判断 | detach/销毁路径 | AC-4.5 |
| R-24 | 边界 | forceDisappear 但历史仍为 0 | 不补发归零 callback | 在途任务未执行时可能发生 | AC-4.6 |
| R-25 | 恢复 | 节点销毁且任务在途 | 清理槽和 Pipeline；弱引用任务退出 | 不访问已销毁节点 | AC-4.7 |
| R-26 | 行为 | API 17 generic 配置 options 并注册事件 | 建立近似监听 | ratios 必须非空 | AC-5.1 |
| R-27 | 边界 | 配置视口测量或使用便捷 API | generic API 21 可下传；便捷 API 固定默认 false | 两条链路能力不等价 | AC-5.2 |
| R-28 | 异常 | options 缺 ratios 或未初始化 measure | 空 ratios 注册返回 401；measure 默认偏差登记风险 | Create 仅初始化 interval | AC-5.3 |
| R-29 | 异常 | SetRatios 越界、size<=0 或空 value | 越界钳制；非正 size 成功清空；正 size 空 value 存在崩溃风险 | 当前实现无 value/size 完整校验 | AC-5.4 |
| R-30 | 行为 | Native 事件派发 | data[0] 为方向，data[1] 为比例 | payload 无单位 | AC-5.5 |
| R-31 | 行为 | generic/便捷链路派发 | generic 保留自定义 eventId；便捷 eventId=0；均透传 nodeId/userData | ID 语义不同 | AC-5.6 |
| R-32 | 边界 | 便捷接口重复注册/注销后重注册 | 新配置和 userData 配合首次 callback | callback map 使用 insert | AC-5.7 |
| R-33 | 异常 | 写入映射后校验失败 | 返回错误但 metadata 可能残留 | 注册非原子 | AC-5.8 |
| R-34 | 恢复 | 注销 Native 近似事件 | generic 仅删映射且核心可能残留；便捷显式清核心监听 | 两种注销不等价 | AC-5.9, AC-5.10 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.8, R-1~R-7 | SDK/Bridge/Static 单测 | undefined、双倍 ratios、归一化、measure 和清理差异 |
| VM-2 | AC-2.1~AC-2.6, R-8~R-12 | 参数化边界测试 | 缺失、0、负数、1~99、100、float 截断 |
| VM-3 | AC-3.1~AC-3.8, R-13~R-19 | 可控时钟/VSync/几何 Host 单测 | 单在途任务、完整 period 延迟、尾沿采样和阈值回调 |
| VM-4 | AC-4.1~AC-4.7, R-20~R-25 | 生命周期集成测试 | 重注册继承、强制归零和销毁弱引用 |
| VM-5 | AC-5.1~AC-5.6, R-26~R-31 | Native C API 端到端测试 | 17/21 能力、options、payload 和 ID 语义 |
| VM-6 | AC-5.7~AC-5.10, R-32~R-34 | Native 重复注册/失败注入/注销测试 | 旧 callback、残留 metadata 和 generic 核心残留 |

## API 变更分析

> 本特性为已有 API 的规格补录，不引入新的 API 或 ABI 变更。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic `onVisibleAreaApproximateChange(options, event)` | Public | `VisibleAreaEventOptions`、callback/`undefined` | `T` | N/A | API 18 近似监听 | AC-1.1~AC-1.7 |
| `UICommonEvent.setOnVisibleAreaApproximateChange` | Public/Static Runtime | options、callback | `void` | N/A | API 12 UICommonEvent 入口 | AC-1.6~AC-1.8 |
| `ArkUI_VisibleAreaEventOptions_*` | Public C API | ratios、interval、API 21 measure | 指针、`int32_t` 或 `bool` | 0, 401, 106401 | API 17/21 options 配置 | AC-5.1~AC-5.4 |
| `NODE_VISIBLE_AREA_APPROXIMATE_CHANGE_EVENT` | Public C API | generic node event 注册 | `int32_t` / `void` | 0, 401, 106102, 106103；安全入口可为 106204 | API 17 generic 近似事件 | AC-5.1, AC-5.5~AC-5.9 |
| `OH_ArkUI_NativeModule_RegisterCommonVisibleAreaApproximateChangeEvent` / `Unregister...` | Public C API | node、ratios、size、float interval、userData、callback | `int32_t` | 0, 401, 500 | API 21 便捷注册/注销 | AC-5.2, AC-5.5~AC-5.10 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | 本次仅补录规格，无接口变更或废弃 | — | — |

## 接口规格

### 接口定义

**ArkTS 近似可见区域监听**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onVisibleAreaApproximateChange(options: VisibleAreaEventOptions, event: VisibleAreaChangeCallback | undefined): T` |
| 返回值 | `T` — 返回当前组件属性链对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options.ratios | `Array<number>` | 是 | 无 | SDK 范围 [0,1]；实际归一化因入口不同 |
| options.expectedUpdateInterval | `number` | 否 | 1000 ms | 核心下限 100 ms；0/负数存在入口差异 |
| options.measureFromViewport | `boolean` | 源码可选 | false | 可用 canonical Dynamic SDK 未声明，版本风险 |
| event | `(isVisible: boolean, currentRatio: number) => void` | SDK 可为 `undefined` | 无 | SDK 约定 undefined reset；Legacy Bridge 不执行该契约 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | interval=0 或负数经不同入口 | 见 Gherkin“跨入口间隔归一化” | AC-2.2~AC-2.5 |
| 2 | 多次几何变化发生在节流窗口 | 见 Gherkin“尾沿最终采样” | AC-3.1~AC-3.3 |
| 3 | 重注册时旧任务在途 | 见 Gherkin“重注册继承在途任务” | AC-4.1, AC-4.2 |

**Native generic 近似监听**

| 属性 | 值 |
|------|-----|
| 函数签名 | `registerNodeEvent(node, NODE_VISIBLE_AREA_APPROXIMATE_CHANGE_EVENT, targetId, userData)` / `unregisterNodeEvent(...)` |
| 返回值 | 注册返回错误码；注销无返回值 |
| 开放范围 | Public C API |
| 错误码 | 0, 401, 106102, 106103；安全入口可为 106204 |
| 关联 AC | AC-5.1~AC-5.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| options | `ArkUI_VisibleAreaEventOptions*` | 是 | 无 | ratios 必须非空；interval 最低 100；API 21 可配置 measure |
| targetId | `int32_t` | 是 | 调用方提供 | 派发时写入 eventId |
| userData | `void*` | 否 | `nullptr` | 原样透传 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | options 合法且注册成功 | 近似事件携带方向、比例、eventId/nodeId/userData | AC-5.1, AC-5.5, AC-5.6 |
| 2 | options 校验失败 | 见 Gherkin“Native 失败注册” | AC-5.8 |
| 3 | generic 注销 | 删除 metadata，当前 reset 表不清核心监听 | AC-5.9 |

**Native API 21 便捷近似监听**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_NativeModule_RegisterCommonVisibleAreaApproximateChangeEvent(node, ratios, size, expectedUpdateInterval, userData, callback)` |
| 返回值 | `int32_t` — 错误码 |
| 开放范围 | Public C API |
| 错误码 | 0, 401, 500 |
| 关联 AC | AC-5.2, AC-5.5~AC-5.10 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | `ArkUI_NodeHandle` | 是 | 无 | 有效节点，必须主线程调用 |
| ratios/size | `float*` / `int32_t` | 是 | 无 | size>0，每项 [0,1]；非法返回 401 |
| expectedUpdateInterval | `float` | 是 | 无 | 转 int32 后核心下限 100 ms |
| userData | `void*` | 否 | `nullptr` | 重复注册时 metadata 更新 |
| callback | function pointer | 是 | 无 | 当前 callback map 保留首次函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 首次合法注册 | 使用 measure=false 建立监听，eventId=0 | AC-5.2, AC-5.6 |
| 2 | 重复注册或注销后重注册 | 使用新配置/userData 与首次 callback | AC-5.7 |
| 3 | 注销成功 | 清 metadata 并显式清核心近似监听 | AC-5.10 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录现有行为和偏差。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** UICommonEvent API 12；Dynamic API 18；Native generic API 17；Native 便捷 API 21。
- **API 版本号策略:** 记录可由 canonical SDK/公开头文件证明的版本；Static 和 ArkTS `measureFromViewport` 不从源码反推 `@since`。

| 通道 | 0 interval | 负 interval | ratios 处理 | 清理/重注册 |
|------|------------|---------------|-------------|-------------|
| Legacy Dynamic | 核心变为 100 ms | Bridge 变为 1000 ms | 前置 N 个 0，再追加钳制值 | 非法/undefined 保留旧监听 |
| ArkTS Modifier/FrameNode | truthiness 变为 1000 ms | 核心变为 100 ms | Common Bridge 钳制 | undefined reset |
| Static UICommonEvent | 核心变为 100 ms | 核心变为 100 ms | 入口不做同样钳制 | event 缺失专用 Clear |
| Native options generic | setter 变为 100 ms | setter 变为 1000 ms | SetRatios 钳制 | generic 注销可能残留核心监听 |
| Native API 21 便捷 | 核心变为 100 ms | 核心变为 100 ms | 越界返回 401 | 重注册保留首次 callback |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 共享几何模型 | Feat-02 复用 Feat-01 normal/inner 可见矩形和面积比，不建立第二套裁剪算法 | AC-3.4, AC-3.5 |
| 独立近似槽 | period>0 的近似监听保存到 throttled slot，与用户/内部精确槽独立 | AC-4.3 |
| UI VSync 驱动 | 近似监听不建立固定周期定时器，由 area-change VSync 驱动并投递单个 UI IDLE 任务 | AC-3.1~AC-3.3 |
| SDK 契约优先 | 外部 ArkTS 契约以 canonical SDK 为准，源码缺失字段/清理偏差进入风险 | AC-1.3, AC-1.7 |
| 主线程约束 | Native 注册/注销接口必须在主线程调用 | AC-5.1, AC-5.10 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 核心 period 下限 100 ms，同一节点最多一个近似任务在途 | 可控时钟单测 | `frameworks/core/components_ng/base/view_abstract.cpp:11559-11569`；`frameworks/core/components_ng/base/frame_node.cpp:2888-2903` |
| 功耗 | 不建立独立轮询，只有 VSync area-change 触发采样任务 | Pipeline 集成测试 | `frameworks/core/pipeline_ng/pipeline_context.cpp:1362-1374,5674-5685` |
| 内存 | 每节点一个 throttled 配置槽和至多一个弱引用任务 | EventHub/任务状态单测 | `frameworks/core/components_ng/event/event_hub.cpp:1205-1219` |
| 安全 | 不新增权限或敏感数据；Native 空指针/size 校验缺口作为风险 | Native 失败注入 | `interfaces/native/node/native_node_extented.cpp:1252-1263` |
| 可靠性 | forceDisappear 可立即归零，节点销毁后弱引用任务退出 | 生命周期集成测试 | `frameworks/core/components_ng/base/frame_node.cpp:2866-2884,8615-8625` |
| 可测试性 | 时间、几何、VSync、任务队列和 Native receiver 可独立控制 | Host/C API 测试 | `test/unittest/core/base/frame_node_test_ng_coverage.cpp:2017-2118` |
| 自动化维测 | 近似回调复用可见区域 trace、缓存比例和触发原因 | Dump/trace 检查 | `frameworks/core/components_ng/base/frame_node.cpp:1103-1125,2820-2833` |
| 定界定位 | 区分前端归一化、核心 period 和 Native event map 三类问题 | 分层日志/源码证据 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:12108-12162` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 使用通用 FrameNode/Pipeline 节流实现 | Host/设备测试 | `frameworks/core/components_ng/base/frame_node.cpp:2837-2903` |
| 平板 | 无接口差异 | 多窗口几何和 onShow 状态参与最终采样 | 多窗口测试 | `frameworks/core/components_ng/base/frame_node.cpp:2605-2665` |
| 折叠屏 | 无接口差异 | 折叠导致多次几何变化时只采样任务执行时最终比例 | 折叠状态切换测试 | `frameworks/core/components_ng/base/frame_node.cpp:2837-2864` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不修改语义树或无障碍事件 | N/A |
| 大字体 | 间接 | 字体引起几何变化时按节流后的最终矩形采样 | AC-3.3 |
| 深色模式 | 否 | 不读取颜色或主题 | N/A |
| 多窗口/分屏 | 是 | 窗口 onShow、边界和 VSync 调度影响采样 | AC-3.4, AC-4.4 |
| 多用户 | 否 | 无持久化或用户数据隔离 | N/A |
| 版本升级 | 是 | 必须遵守 12/18/17/21 版本边界和未确认版本风险 | AC-1.7, AC-5.1, AC-5.2 |
| 生态兼容 | 是 | 0/负间隔、ratios、清理和 Native callback 差异可被应用观察 | AC-1.3~AC-2.5, AC-5.7~AC-5.10 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 近似可见区域变化监听
  作为 ArkUI 或 Native UI 开发者
  我想要按期望间隔合并可见区域变化
  以便降低频繁几何变化产生的回调压力

  Scenario Outline: 跨入口间隔归一化
    Given 使用 <entry> 注册近似监听
    When expectedUpdateInterval 为 <input>
    Then 核心或 options 保存的 period 为 <period>

    Examples:
      | entry | input | period |
      | Legacy Dynamic | -1 | 1000 |
      | Legacy Dynamic | 0 | 100 |
      | Modifier | 0 | 1000 |
      | Modifier | -1 | 100 |
      | Native options | -1 | 1000 |
      | Native convenience | -1 | 100 |

  Scenario: 尾沿最终采样
    Given period 为 500 ms
    And 一个近似任务已经在途
    When 组件在任务执行前连续发生多次几何变化
    Then 不再投递第二个近似任务
    And 任务执行时读取最后一次几何状态
    And 只按最终比例判断阈值

  Scenario: 重注册继承在途任务
    Given 旧近似监听已有一个延迟任务
    When 使用新 ratios 和 callback 重注册
    Then 不重置在途任务和历史比例
    And 旧任务在原排队时点读取新 ratios 和 callback

  Scenario: 生命周期强制归零
    Given 最近近似采样比例为 0.6
    And ratios 包含 0.5
    When 节点 detach 或销毁
    Then forceDisappear 绕过 period
    And 立即按 ratio 0 执行一次下穿判断

  Scenario: Native 失败注册
    Given Native event map 尚无近似事件
    When 注册入口先写 metadata 后发现 ratios 非法
    Then 返回参数错误
    And metadata 可能仍留在 event map

  Scenario: Native 两种注销差异
    Given generic 和 convenience 链路分别建立近似监听
    When 分别执行注销
    Then generic 链路删除 metadata 但可能保留核心监听
    And convenience 链路删除 metadata 并显式清理核心监听
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（仅近似监听，不重复定义 Feat-01 精确监听）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "approximate visible area throttled callback scheduling interval and lifecycle"
  - repo: "openharmony/arkui_ace_engine"
    query: "NativeNode approximate visible area generic and common event registration"
  - repo: "openharmony/interface_sdk-js"
    query: "onVisibleAreaApproximateChange VisibleAreaEventOptions API versions"
```

**关键文档：** `interfaces/native/native_node.h:10538-10555,14348-14376`；`interfaces/native/native_type.h:3693-3807`
