# 特性规格

> Func-04-04-10-Feat-01 精确可见区域变化监听：固化 `onVisibleAreaChange` 在 ArkTS Dynamic、ArkTS Static 与 Native Node 通道中的既有阈值监听、可见比例计算、生命周期归零和兼容性行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 精确可见区域变化监听 |
| 特性编号 | Func-04-04-10-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 9/13/22，Static API 23/26，Native API 12/17/21 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ArkTS 精确可见区域监听规格 | 补录 Dynamic/Static 的阈值、回调、`measureFromViewport`、注册与清理行为 |
| ADDED | 可见比例和阈值触发规格 | 补录裁剪矩形面积比、端点、跨多阈值、首次检测和去重行为 |
| ADDED | 生命周期与调度规格 | 补录后台、离树、隐藏、销毁归零以及 UI VSync area-change 阶段调度 |
| ADDED | Native Node 精确监听规格 | 补录 API 12/17/21 支持矩阵、options、payload、错误码和已知实现偏差 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/10-visible-area-mechanism/design.md` | 本次生成 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:24494-24563` | 已核查；来源 SDK checkout 与当前 ace_engine 提交非同一仓 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:13706-13734` | 已核查；Static 两参/三参分别按 API 23/26 记录 |
| Dynamic Bridge | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:12060-12105` | 已核查 |
| Modifier Bridge | `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:4032-4042,5874-5887` | 已核查 |
| 核心计算与触发 | `frameworks/core/components_ng/base/frame_node.cpp:2605-2833,7555-7642` | 已核查 |
| 回调存储与清理 | `frameworks/core/components_ng/event/event_hub.cpp:1205-1257`；`frameworks/core/components_ng/base/view_abstract.cpp:11533-11621` | 已核查 |
| Pipeline 调度 | `frameworks/core/pipeline_ng/pipeline_context.cpp:1325-1380,5638-5686,6087-6110` | 已核查 |
| Native API | `interfaces/native/native_node.h:1904-1932,10214-10345,12931-13107`；`interfaces/native/native_type.h:3693-3807` | 已核查 |

> 本文档描述存量实现，不提出行为修正。SDK 声明、前端桥接和 Native 实现不一致处按兼容性或实现风险记录。

## 用户故事

### US-1: 注册精确可见区域监听

**作为** ArkUI 应用开发者，

**我想要** 使用一个或多个可见比例阈值注册组件监听，

**以便** 在组件可见比例跨越指定阈值时获得当前方向和比例。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN ArkTS 传入 ratios 数组和有效回调 THEN 当前组件的用户精确监听槽保存 ratios 和回调，重复注册覆盖旧槽而不形成监听列表 | 正常 |
| AC-1.2 | WHEN Dynamic Bridge 接收 ratio <= 0 或 ratio >= 1 THEN 分别按 0 或 1 下传；WHEN ratio 位于开区间 (0,1) THEN 保留解析值 | 边界 |
| AC-1.3 | WHEN ratios 包含乱序值或重复值 THEN 核心层按原数组逐项判断，不排序、不去重 | 边界 |
| AC-1.4 | WHEN Dynamic 直调参数个数不是 2~3、ratios 不是数组或 event 不是函数 THEN 本次调用被忽略且已有监听保持不变 | 异常 |
| AC-1.5 | WHEN Modifier/Static 路径将 ratios 或 event 设为 `undefined` THEN 执行 reset；WHEN Static 仅 event 为 `undefined` THEN 清理监听；WHEN Static 仅 ratios 为 `undefined` 且 event 有效 THEN 当前生成链路可形成空阈值监听 | 边界 |
| AC-1.6 | WHEN 使用 Dynamic 第三参数或 Static API 26 第三参数 THEN `measureFromViewport` 的布尔值随回调配置保存；WHEN 未提供 THEN 默认为 false | 正常 |
| AC-1.7 | WHEN ArkTS 传入空 ratios 数组和有效回调 THEN 监听配置可建立，但阈值遍历没有命中项，因此不产生用户阈值回调 | 边界 |

### US-2: 按既有口径计算可见比例

**作为** 跨组件布局开发者，

**我想要** 明确可见比例的几何计算和裁剪边界，

**以便** 正确解释嵌套、越界和 clip 场景中的回调结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN visibleRect 和 frameRect 均非空 THEN currentRatio 等于 `visibleRect.width * visibleRect.height / (frameRect.width * frameRect.height)` 并钳制到 [0,1] | 正常 |
| AC-2.2 | WHEN 任一参与计算的矩形为空 THEN currentRatio 为 0 | 边界 |
| AC-2.3 | WHEN `measureFromViewport=false` THEN可见矩形逐级受祖先 paint rect 约束，超出祖先范围的部分计为不可见 | 正常 |
| AC-2.4 | WHEN `measureFromViewport=true` THEN使用 inner visible/frame rect；未显式 clip 的普通祖先不裁剪越界部分，但显式 `clip(true)`、窗口边界和根节点仍执行裁剪 | 正常 |
| AC-2.5 | WHEN组件被兄弟节点遮挡或设置透明度而几何裁剪矩形不变 THEN精确监听比例不因遮挡或透明度单独变化 | 边界 |

### US-3: 在阈值穿越时获得单次回调

**作为** ArkUI 应用开发者，

**我想要** 在实际比例跨越阈值时获得去重后的通知，

**以便** 避免同一帧重复执行可见性业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN currentRatio 从阈值下方跨到阈值上方 THEN回调 `isVisible=true` 和最终 currentRatio；WHEN从上方跨到下方 THEN回调 `isVisible=false` 和最终 currentRatio | 正常 |
| AC-3.2 | WHEN一次比例变化跨越 ratios 中多个阈值 THEN遍历全部阈值后只调用一次回调，并携带最终比例 | 边界 |
| AC-3.3 | WHEN ratios 包含 0 且 currentRatio 到达 0 THEN按不可见端点处理；WHEN ratios 包含 1 且 currentRatio 到达 1 THEN按可见端点处理 | 边界 |
| AC-3.4 | WHEN监听刚注册但尚未发生 Pipeline area-change 检测 THEN不在注册调用栈同步触发首次回调 | 正常 |
| AC-3.5 | WHEN本轮 currentRatio 与上次检测比例近似相等 THEN不重复执行用户精确回调 | 边界 |
| AC-3.6 | WHEN同一节点重新注册精确监听 THEN替换 ratios 和 callback，但不重置节点已保存的最近检测比例与最近回调比例 | 边界 |
| AC-3.7 | WHEN新节点首次进入 area-change 检测且 currentRatio 大于某个正阈值 THEN相对初始历史比例 0 产生一次上穿回调；WHEN首次比例仍为 0 THEN不产生首次回调 | 边界 |

### US-4: 感知生命周期归零和调度时机

**作为** 需要跟踪页面曝光状态的开发者，

**我想要** 在组件失去参与可见区域计算的条件时得到一致的归零行为，

**以便** 正确结束已开始的可见状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN窗口进入后台、节点离开主树、节点自身隐藏或 inactive、或任一祖先隐藏/inactive THEN该节点按 currentRatio=0 处理 | 正常 |
| AC-4.2 | WHEN归零前最近检测比例非 0 且 ratios 跨越条件成立 THEN触发一次归零回调；WHEN最近检测比例已为 0 THEN不重复回调 | 边界 |
| AC-4.3 | WHEN节点正常参与 Pipeline 帧刷新 THEN精确监听在 UI VSync 的 area-change 阶段统一计算和派发，不在注册栈同步执行 | 正常 |
| AC-4.4 | WHEN FrameNode 销毁且仍有任一可见区域回调 THEN先强制执行比例 0 检测，再清理用户精确、内部精确和近似回调 | 恢复 |
| AC-4.5 | WHEN仅重注册用户精确监听 THEN用户精确、内部精确和近似监听仍分别保存在独立槽位 | 正常 |
| AC-4.6 | WHEN Modifier/Native reset 进入 `ViewAbstract::ResetVisibleChange` THEN清理用户精确槽并无条件从 Pipeline 可见区域节点集合移除该节点；若内部精确或近似槽仍存在，其后续调度可能受影响 | 边界 |

### US-5: 通过 Native Node 使用精确监听

**作为** Native UI 开发者，

**我想要** 使用 Native Node API 配置阈值并订阅精确可见区域事件，

**以便** 在 C API 场景获得与核心计算一致的回调。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN API 12 调用 `setAttribute(NODE_VISIBLE_AREA_CHANGE_RATIO)` 后以 `NODE_EVENT_ON_VISIBLE_AREA_CHANGE` 注册事件 THEN底层建立精确监听 | 正常 |
| AC-5.2 | WHEN使用 API 17 `ArkUI_VisibleAreaEventOptions` 设置 ratios THEN每个输入值被钳制到 [0,1]；WHEN使用直接 attribute value 路径传入越界值或空数组 THEN返回 401 | 边界 |
| AC-5.3 | WHEN API 21 将 options 放入 `NODE_VISIBLE_AREA_CHANGE_RATIO.object` THENoptions.ratios 覆盖 `value[]`，`measureFromViewport` 被下传，而 `expectedUpdateInterval` 对精确监听始终忽略 | 正常 |
| AC-5.4 | WHEN Native 精确事件派发 THEN `data[0].i32` 为方向标志、`data[1].f32` 为当前无单位比例，并保留注册时的 targetId 和 userData | 正常 |
| AC-5.5 | WHEN同一节点和 eventType 重复成功注册 THEN eventMap 更新 targetId/userData，底层用户精确槽覆盖为当前包装回调 | 边界 |
| AC-5.6 | WHEN eventMap 元数据更新后 ratios/options 校验失败 THEN注册返回错误，但旧底层回调可能继续存在并在后续派发中使用新的 targetId/userData | 异常 |
| AC-5.7 | WHEN创建 options 后未显式设置 `measureFromViewport` 就用于精确监听 THEN公开契约期望默认 false，但当前 Create 实现未初始化该字段，结果作为实现风险记录 | 异常 |
| AC-5.8 | WHEN主线程安全检查失败 THEN安全注册入口可返回 106204；WHEN参数、动态实现或 BuilderNode 条件不满足 THEN按公开错误码返回 401、106102 或 106103 | 异常 |
| AC-5.9 | WHEN注销 `NODE_EVENT_ON_VISIBLE_AREA_CHANGE` THEN删除 eventMap 元数据并清理底层用户精确槽，后续不再由该注册接收事件 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.7 | R-1~R-5, R-28 | 已有实现 | SDK/Bridge/Modifier 单测与源码审查 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:12060-12105`；`frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:4032-4042,5874-5887` |
| AC-2.1~AC-2.5 | R-6~R-9 | 已有实现 | FrameNode Host 单测与源码审查 | `frameworks/core/components_ng/base/frame_node.cpp:2732-2779,7555-7642`；`test/unittest/core/base/frame_node_test_ng_v3.cpp:481-517` |
| AC-3.1~AC-3.7 | R-10~R-14, R-29 | 已有实现 | FrameNode/EventHub Host 单测 | `frameworks/core/components_ng/base/frame_node.cpp:2742-2833`；`frameworks/core/components_ng/base/frame_node.h:1889-1895`；`test/unittest/core/base/frame_node_test_ng.cpp:1622-1779` |
| AC-4.1~AC-4.6 | R-15~R-19 | 已有实现 | Pipeline/生命周期 Host 单测 | `frameworks/core/components_ng/base/frame_node.cpp:2605-2710,8509-8527,8619-8643`；`test/unittest/core/pipeline/pipeline_context_test_ng.cpp:211-243` |
| AC-5.1~AC-5.9 | R-20~R-27 | 已有实现 | C API 单测与源码审查 | `test/unittest/interfaces/native_node_test.cpp:2551-2555,5532-5588,15283-15287,15544-15558`；`interfaces/native/node/node_model.cpp:550-648` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ArkTS 以有效 ratios 和 callback 注册 | 保存单个用户精确回调槽，后注册覆盖前注册 | 不形成监听列表 | AC-1.1 |
| R-2 | 边界 | Dynamic ratio <= 0、>= 1 或位于 (0,1) | 分别下传 0、1 或原解析值 | Bridge 不排序、不去重 | AC-1.2, AC-1.3 |
| R-3 | 异常 | Dynamic 参数个数不在 [2,3]、ratios 非数组或 callback 非函数 | 静默返回且保留旧槽 | `null`、`undefined` 和其他非函数均属于该分支 | AC-1.4 |
| R-4 | 边界 | Modifier/Static 输入 `undefined` | 按生成桥接的 set/reset 规则清理或形成空阈值配置 | Static 两参声明和生成实现存在组合差异 | AC-1.5 |
| R-5 | 行为 | 提供或省略 `measureFromViewport` | 布尔值写入用户回调配置；省略时为 false | Dynamic/Static 开放版本不同 | AC-1.6 |
| R-6 | 行为 | 两个矩形均非空 | 计算轴对齐矩形面积比并钳制到 [0,1] | 不读取遮挡关系或透明度 | AC-2.1, AC-2.5 |
| R-7 | 边界 | visibleRect 或 frameRect 为空 | 比例为 0 | 避免除零 | AC-2.2 |
| R-8 | 行为 | `measureFromViewport=false` | 使用逐祖先约束的 visibleRect/frameRect | 祖先 paint rect 参与裁剪 | AC-2.3 |
| R-9 | 行为 | `measureFromViewport=true` | 使用 inner visible/frame rect，仅显式 clip、窗口边界和根节点裁剪 | paint rect 为空时仍归零 | AC-2.4 |
| R-10 | 行为 | 比例由阈值一侧跨到另一侧 | 上穿回调 true，下穿回调 false，携带最终比例 | 阈值比较使用近似比较工具 | AC-3.1 |
| R-11 | 边界 | 一次变化跨越多个或重复阈值 | 完成遍历后只调用一次 callback | 最后命中的方向值用于回调 | AC-3.2 |
| R-12 | 边界 | 当前比例命中 0 或 1 阈值 | 0 对应 false，1 对应 true | 仅 ratios 含相应端点时生效 | AC-3.3 |
| R-13 | 行为 | 刚注册但尚未进入 area-change flush | 不同步回调；由后续 VSync 检测驱动 | 注册仅设置槽并加入节点集合 | AC-3.4, AC-4.3 |
| R-14 | 边界 | currentRatio 与最近检测值近似相等，或重新注册 | 相同比例不回调；重注册不清空历史比例 | 新阈值相对旧历史比例继续判断 | AC-3.5, AC-3.6 |
| R-15 | 行为 | 后台、离树、自身/祖先隐藏或 inactive | 将当前比例作为 0 处理 | 各原因使用统一归零出口 | AC-4.1 |
| R-16 | 边界 | 强制归零时最近比例已为 0 或非 0 | 已为 0 不重复回调；非 0 时按阈值规则处理 | 是否实际回调仍取决于 ratios | AC-4.2 |
| R-17 | 恢复 | FrameNode 销毁且存在任一可见区域回调 | 强制归零后清理三个槽并移出 Pipeline 集合 | 销毁路径不保留回调 | AC-4.4 |
| R-18 | 行为 | 用户精确、内部精确、近似监听分别注册 | EventHub 使用三个独立配置槽 | 各槽有独立 ratios、callback 和历史比例 | AC-4.5 |
| R-19 | 边界 | 调用 `ResetVisibleChange` 且其他槽仍有效 | 用户精确槽被清理，Pipeline 节点仍被无条件移除 | 作为现有实现风险，不在本规格修复 | AC-4.6 |
| R-20 | 行为 | API 12 配置 ratio attribute 并注册精确事件 | 建立 Native 到 ViewAbstract 的精确回调链路 | 必须为受支持 Native 节点 | AC-5.1 |
| R-21 | 边界 | Native options 或直接 attribute 设置 ratios | options 钳制；直接路径越界/空数组返回 401 | 两条入口的非法值处理不同 | AC-5.2 |
| R-22 | 行为 | API 21 attribute.object 携带 options | 采用 options.ratios 和 `measureFromViewport`，忽略 interval | 精确监听不节流 | AC-5.3 |
| R-23 | 行为 | Native 精确回调派发 | data[0] 写方向，data[1] 写比例，事件携带 targetId/userData | payload 无尺寸单位 | AC-5.4 |
| R-24 | 边界 | Native 同 eventType 成功重注册 | 更新元数据并覆盖底层单槽 | 不形成多回调 | AC-5.5 |
| R-25 | 异常 | Native 在元数据更新后校验失败 | 返回错误且存在新元数据配旧回调的非原子状态 | 作为实现风险登记 | AC-5.6 |
| R-26 | 异常 | options 未初始化字段或调用线程/参数非法 | 默认字段偏差作为风险；入口返回对应错误码 | 安全入口额外可能返回 106204 | AC-5.7, AC-5.8 |
| R-27 | 恢复 | 注销 Native 精确事件 | 删除 eventMap 项并 Reset 用户精确监听 | 注销后该订阅不再派发 | AC-5.9 |
| R-28 | 边界 | ArkTS ratios 数组长度为 0 | 保存空阈值配置，后续遍历不命中且不回调 | 不自动补充 0 阈值 | AC-1.7 |
| R-29 | 边界 | 首次帧检测相对初始历史比例 0 | currentRatio 上穿正阈值时回调 true；currentRatio 仍为 0 时被相同比例去重 | 注册调用栈仍不同步回调 | AC-3.4, AC-3.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.7, R-1~R-5, R-28 | SDK 审查 + Bridge/Modifier 单测 | API 版本、参数校验、覆盖、空数组、清理和第三参数 |
| VM-2 | AC-2.1~AC-2.5, R-6~R-9 | FrameNode Host 单测 | 面积比、空矩形、祖先裁剪与视口测量 |
| VM-3 | AC-3.1~AC-3.7, R-10~R-14, R-29 | 阈值参数化 Host 单测 | 上下穿、乱序/重复阈值、0/1、跨多阈值、首次检测和历史比例 |
| VM-4 | AC-4.1~AC-4.4, R-15~R-17 | Pipeline/FrameNode 集成测试 | 后台、离树、隐藏、inactive、销毁归零和 VSync 调度 |
| VM-5 | AC-4.5, AC-4.6, R-18, R-19 | EventHub/ViewAbstract 回归测试 | 三槽独立性与 reset 移除 Pipeline 节点风险 |
| VM-6 | AC-5.1~AC-5.5, R-20~R-24 | Native C API 端到端测试 | 12/17/21 矩阵、payload、targetId/userData 和覆盖 |
| VM-7 | AC-5.6~AC-5.9, R-25~R-27 | Native 失败注入/注销测试 | 非原子失败、默认字段、线程错误和注销 |

## API 变更分析

> 本特性为已有 API 的规格补录，不引入新的 API 或 ABI 变更。下表记录纳入规格的存量接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| Dynamic `onVisibleAreaChange(ratios, event)` | Public | `Array<number>`、可见变化回调 | `T` | N/A | API 9 两参精确监听 | AC-1.1~AC-1.5 |
| Dynamic `onVisibleAreaChange(ratios, event, measureFromViewport)` | Public | ratios、回调、视口测量开关 | `T` | N/A | API 22 三参精确监听 | AC-1.6, AC-2.4 |
| Static `onVisibleAreaChange(ratios, event)` | Public | ratios/回调可为 `undefined` | `this` | N/A | API 23 Static 精确监听 | AC-1.5 |
| Static `onVisibleAreaChange(ratios, event, measureFromViewport)` | Public | ratios、回调、布尔开关 | `this` | N/A | API 26 Static 视口测量 | AC-1.6, AC-2.4 |
| `ArkUI_NativeNodeAPI_1::registerNodeEvent` / `unregisterNodeEvent` | Public C API | node、eventType、targetId、userData | `int32_t` / `void` | 0, 401, 106102, 106103；安全入口可为 106204 | API 12 注册/注销精确事件 | AC-5.1, AC-5.4~AC-5.9 |
| `NODE_VISIBLE_AREA_CHANGE_RATIO` | Public C API | `ArkUI_AttributeItem.value[]` 或 `object` options | `int32_t` | 0, 401 | API 12 ratio attribute；API 21 扩展 options | AC-5.1~AC-5.3 |
| `OH_ArkUI_VisibleAreaEventOptions_*` | Public C API | options 生命周期、ratios、interval、measure 开关 | 指针、`int32_t` 或 `bool` | 0, 401, 106401 | API 17/21 options 配置与读取 | AC-5.2, AC-5.3, AC-5.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | 本次仅补录规格，无接口变更或废弃 | — | — |

## 接口规格

### 接口定义

**ArkTS `onVisibleAreaChange`**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic: `onVisibleAreaChange(ratios: Array<number>, event: VisibleAreaChangeCallback, measureFromViewport?: boolean): T`；Static: 对应两参/三参 `this` 接口 |
| 返回值 | `T` / `this` — 返回当前组件属性链对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| ratios | `Array<number>` | Dynamic 是；Static 可为 `undefined` | 无 | 每项契约范围 [0,1]；Bridge 将端点外值压到 0/1；保留顺序和重复项 |
| event | `(isVisible: boolean, currentRatio: number) => void` | Dynamic 是；Static 可为 `undefined` | 无 | Dynamic 直调只接受函数；Modifier/Static 的 `undefined` 可触发 reset |
| measureFromViewport | `boolean` | 否 | false | Dynamic API 22、Static API 26 起；仅改变祖先越界裁剪口径 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 比例上穿或下穿一个/多个阈值 | 见 Gherkin“跨越多个阈值” | AC-3.1, AC-3.2 |
| 2 | 切换 `measureFromViewport` | 见 Gherkin“祖先越界区域计算” | AC-2.3, AC-2.4 |
| 3 | 节点离树或窗口后台 | 见 Gherkin“生命周期归零” | AC-4.1, AC-4.2 |

**NativeNode 精确可见区域事件**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t registerNodeEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType, int32_t targetId, void* userData)`；`void unregisterNodeEvent(...)` |
| 返回值 | 注册返回错误码；注销无返回值 |
| 开放范围 | Public C API |
| 错误码 | 0, 401, 106102, 106103；安全入口另有 106204 |
| 关联 AC | AC-5.1~AC-5.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | `ArkUI_NodeHandle` | 是 | 无 | 有效且支持 Native event 的节点；API 必须在主线程调用 |
| eventType | `ArkUI_NodeEventType` | 是 | 无 | 本特性固定为 `NODE_EVENT_ON_VISIBLE_AREA_CHANGE` |
| targetId | `int32_t` | 是 | 由调用方提供 | 原样写入派发事件 |
| userData | `void*` | 否 | `nullptr` | 原样写入派发事件；未预设 ratio attribute 时实现还会尝试将其解释为 `ArkUI_AttributeItem*` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | ratio attribute 有效且注册成功 | 建立单槽监听并派发方向、比例、targetId/userData | AC-5.1, AC-5.4 |
| 2 | options 与 `value[]` 同时存在 | 使用 options.ratios/measure，忽略 `value[]` 和 interval | AC-5.3 |
| 3 | 校验失败或注销 | 见 Gherkin“Native 失败注册和注销” | AC-5.6, AC-5.9 |

**`ArkUI_VisibleAreaEventOptions`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Create/Dispose/SetRatios/GetRatios/SetMeasureFromViewport/GetMeasureFromViewport` |
| 返回值 | options 指针、错误码或配置值 |
| 开放范围 | Public C API |
| 错误码 | 0, 401；GetRatios 缓冲区不足为 106401 |
| 关联 AC | AC-5.2, AC-5.3, AC-5.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| ratios value/size | `float*` / `int32_t` | 是 | 无 | SetRatios 将每项钳制到 [0,1] |
| expectedUpdateInterval | `int32_t` | 否 | 1000 ms | 精确监听忽略该字段 |
| measureFromViewport | `bool` | 否 | 契约为 false | 当前 Create 未初始化字段，使用前应显式设置以规避实现风险 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SetRatios 输入 -0.2、0.5、1.2 | options 保存 0、0.5、1 | AC-5.2 |
| 2 | options 用于精确 ratio attribute | ratio 和 measure 生效，interval 不生效 | AC-5.3 |
| 3 | 未 SetMeasure 即注册 | 契约期望 false，当前实现结果未定义并登记风险 | AC-5.7 |

## 兼容性声明

- **已有 API 行为变更:** 否；本次仅补录现有行为和偏差。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** ArkTS Dynamic API 9；API 13 统一 `VisibleAreaChangeCallback` 类型；Native 精确事件 API 12；Static API 23。
- **API 版本号策略:** 保留 Dynamic 9/13/22、Static 23/26、Native 12/17/21 的分阶段能力，不向低版本外推。

| 通道/版本 | 能力 | 兼容性说明 |
|-----------|------|------------|
| Dynamic API 9 | 两参 ratios + callback | 不包含 `measureFromViewport` |
| Dynamic API 13 | 统一 `VisibleAreaChangeCallback` 类型 | 回调语义保持方向布尔值和当前实际比例 |
| Dynamic API 22 | 三参接口 | 第三参默认为 false |
| Static API 23 | 两参接口 | ratios/event 可为 `undefined` |
| Static API 26 | 三参接口 | 增加 `measureFromViewport` |
| Native API 12 | ratio attribute + 精确事件注册 | 直接 ratios 越界返回 401 |
| Native API 17 | options ratios/lifecycle API | SetRatios 钳制越界值 |
| Native API 21 | ratio attribute 接受 options，开放 measure set/get | 精确监听忽略 options interval |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 分层单向调用 | SDK/Bridge/Native API 仅经 ViewAbstract、EventHub、FrameNode 和 Pipeline 建立回调，不跨层直接计算比例 | AC-1.1, AC-4.3, AC-5.1 |
| 几何口径固定 | 精确比例只使用裁剪后的轴对齐矩形面积，不引入遮挡或透明度判断 | AC-2.1~AC-2.5 |
| 单槽和历史状态 | 用户精确监听为单槽，重注册不重置 FrameNode 历史比例 | AC-1.1, AC-3.6 |
| SDK 契约优先 | 外部接口以匹配版本 SDK 声明为契约，源码偏差单独登记风险 | AC-1.5, AC-5.7 |
| 主线程约束 | Native Node 注册接口必须在主线程调用 | AC-5.8 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 同一节点同一 VSync、同一用户精确槽最多执行一次最终回调 | 阈值跨越 Host 单测 | `frameworks/core/components_ng/base/frame_node.cpp:2783-2833` |
| 功耗 | 不建立独立轮询；复用 Pipeline area-change VSync 阶段 | Pipeline 源码审查 | `frameworks/core/pipeline_ng/pipeline_context.cpp:1325-1380,5674-5686` |
| 内存 | 每节点三个可见区域配置槽，不随重复注册线性增长 | EventHub 单测 | `frameworks/core/components_ng/event/event_hub.cpp:1205-1257` |
| 安全 | 不访问敏感信息、不新增权限；Native 参数经节点、线程和范围校验 | C API 失败测试 | `interfaces/native/node/node_model.cpp:535-587`；`interfaces/native/node/node_model_safely.cpp:289-299` |
| 可靠性 | 后台、离树、隐藏和销毁路径有统一归零或清理行为 | 生命周期集成测试 | `frameworks/core/components_ng/base/frame_node.cpp:2605-2710,8619-8643` |
| 可测试性 | ratios、裁剪、生命周期和 Native payload 均可通过可控几何/时钟验证 | Host/C API 单测 | `test/unittest/core/base/frame_node_test_ng.cpp:782-831,1622-1779` |
| 自动化维测 | 回调路径带 ACE trace 和触发原因 | 日志/trace 检查 | `frameworks/core/components_ng/base/frame_node.cpp:2746-2752,2819-2831` |
| 定界定位 | 区分 SELF_INVISIBLE、IS_NOT_ON_MAINTREE、BACKGROUND、ANCESTOR_INVISIBLE 等原因 | Dump/日志检查 | `frameworks/core/components_ng/base/frame_node.cpp:2605-2631` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 使用通用 FrameNode 几何和 Pipeline 调度 | Host/设备测试 | `frameworks/core/components_ng/base/frame_node.cpp:2605-2833` |
| 平板 | 无差异 | 多窗口状态变化仍按窗口 onShow 和几何裁剪处理 | 多窗口测试 | `frameworks/core/components_ng/base/frame_node.cpp:2608-2625` |
| 折叠屏 | 无接口差异 | 折叠导致布局/窗口几何改变时按最终裁剪矩形重新计算 | 折叠状态切换测试 | `frameworks/core/pipeline_ng/pipeline_context.cpp:1325-1380` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变语义树或无障碍事件 | N/A |
| 大字体 | 间接 | 字体导致组件几何变化时按新矩形计算，不新增字体规则 | AC-2.1 |
| 深色模式 | 否 | 不读取颜色或主题 | N/A |
| 多窗口/分屏 | 是 | 窗口可见状态和边界参与归零与裁剪 | AC-2.4, AC-4.1 |
| 多用户 | 否 | 无持久化或用户态数据 | N/A |
| 版本升级 | 是 | 必须遵守 9/22、23/26、12/17/21 版本矩阵 | AC-1.6, AC-5.1~AC-5.3 |
| 生态兼容 | 是 | SDK、Modifier、Native 的参数清理和默认值偏差需保持可见 | AC-1.5, AC-5.7 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 精确可见区域变化监听
  作为 ArkUI 应用或 Native UI 开发者
  我想要在比例跨越阈值时获得精确通知
  以便管理曝光、加载和资源状态

  Scenario: 跨越多个阈值只回调一次
    Given ratios 为 [0.2, 0.5, 0.8, 0.5]
    And 最近回调比例为 0.1
    When 当前可见比例变为 0.9
    Then 回调执行一次
    And isVisible 为 true
    And currentRatio 为 0.9

  Scenario Outline: 端点阈值
    Given ratios 包含 <threshold>
    When 当前可见比例到达 <ratio>
    Then isVisible 为 <visible>

    Examples:
      | threshold | ratio | visible |
      | 0 | 0 | false |
      | 1 | 1 | true |

  Scenario: 祖先越界区域计算
    Given 子组件有一部分超出未设置 clip 的普通父组件
    When measureFromViewport 为 false
    Then 超出父组件的部分计为不可见
    When measureFromViewport 为 true
    Then 超出普通父组件的部分可计入可见面积
    And 显式 clip、窗口边界和根节点仍执行裁剪

  Scenario: 生命周期归零
    Given 组件最近可见比例为 0.6
    And ratios 包含 0.5
    When 窗口进入后台或组件离开主树
    Then 组件按比例 0 处理
    And 回调 isVisible 为 false
    And currentRatio 为 0

  Scenario: Native options 覆盖 attribute values
    Given NODE_VISIBLE_AREA_CHANGE_RATIO.value 为 [0.2]
    And options.ratios 为 [0.7]
    And options.measureFromViewport 为 true
    When 注册 NODE_EVENT_ON_VISIBLE_AREA_CHANGE
    Then 使用阈值 0.7
    And measureFromViewport 为 true
    And options.expectedUpdateInterval 不影响精确监听

  Scenario: Native 失败注册和注销
    Given 节点已有一个成功的精确监听
    When 使用非法 ratios 和新的 targetId/userData 重复注册
    Then 注册返回参数错误
    And 当前实现可能保留旧底层回调但使用新元数据
    When 注销精确事件
    Then 元数据和用户精确槽被清理
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（仅精确监听，不包含 Feat-02 近似监听）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode exact visible area ratio calculation, threshold crossing and lifecycle reset"
  - repo: "openharmony/arkui_ace_engine"
    query: "NativeNode visible area event options registration payload and error handling"
  - repo: "openharmony/interface_sdk-js"
    query: "CommonAttribute onVisibleAreaChange Dynamic and Static API version signatures"
```

**关键文档：** `interfaces/native/native_node.h:1904-1932,10331-10345,13080-13107`；`interfaces/native/native_type.h:3693-3807`
