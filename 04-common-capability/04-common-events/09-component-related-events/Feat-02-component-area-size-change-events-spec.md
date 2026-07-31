# 特性规格

> Func-04-04-09-Feat-02 组件区域与尺寸变化事件：固化 `onAreaChange`、`onSizeChange` 在 ArkTS Dynamic、ArkTS Static 与 Native Node 通道中的既有行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件区域与尺寸变化事件 |
| 特性编号 | Func-04-04-09-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | Dynamic API 8/12/26，Static API 23/26，Native API 12/20/21/26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 区域变化事件规格 | 补录区域快照、位置与父级偏移触发、回调数据、清理和生命周期边界 |
| ADDED | 区域变化节流规格 | 补录 `AreaChangeOptions`、间隔归一化、尾沿合并与首次触发差异 |
| ADDED | 尺寸变化事件规格 | 补录尺寸快照、同步回调、inactive 补偿、清理和去重行为 |
| ADDED | Native Node 规格 | 补录 Area/Size 事件数据、版本矩阵、注册通道和当前实现风险 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/09-component-related-events/design.md` | 增量合并 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts:22721-22764,25412-25438,27077-27116` | 已核查 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets:12835-12856,14196-14206,15123-15153` | 已核查 |
| 核心实现 | `frameworks/core/components_ng/base/frame_node.cpp:2350-2572,7200-7263` | 已核查 |
| 事件存储 | `frameworks/core/components_ng/event/event_hub.cpp:464-505,819-860,1260-1297` | 已核查 |
| Native API | `interfaces/native/native_node.h:10214-10278,10568-10576,14317-14408` | 已核查 |

> 本文档描述存量实现，不提出行为修正。SDK 声明与源码、Native 头文件与实现不一致处按兼容性风险记录。

## 用户故事

### US-1: 监听组件区域变化

**作为** ArkUI 应用开发者，

**我想要** 获得组件布局区域变化前后的尺寸与位置信息，

**以便** 根据组件在父节点和窗口中的几何变化更新业务状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 普通 `onAreaChange` 注册后第一次检测到非零实际区域 THEN 以零矩形和零父级偏移作为 oldValue，并以当前区域作为 newValue 触发回调 | 边界 |
| AC-1.2 | WHEN 安全区修正后的本地区域矩形或父级到窗口偏移任一发生变化 THEN `onAreaChange` 触发；父级移动可在子节点尺寸不变时触发子节点回调 | 正常 |
| AC-1.3 | WHEN 仅发生 translate、offset、markAnchor、scale、transform 等重绘属性变化且布局区域未变化 THEN `onAreaChange` 不触发 | 边界 |
| AC-1.4 | WHEN `onAreaChange` 回调执行 THEN oldValue/newValue 均包含 `width`、`height`、`position`、`globalPosition`，数值按当前密度从 px 转为 vp | 正常 |
| AC-1.5 | WHEN Dynamic 运行时创建 Area 对象 THEN 可同时出现未写入 SDK 的 `pos`/`globalPos` 兼容别名；公开契约仍仅包含 SDK 声明的四个字段 | 边界 |
| AC-1.6 | WHEN 对同一节点重复注册普通 area 回调 THEN 后注册回调覆盖原用户回调槽 | 正常 |
| AC-1.7 | WHEN Dynamic 在目标 API >= 11 时调用 `onAreaChange(undefined)` THEN 清除 area 用户回调；WHEN 目标 API < 11 或传入 null/非函数 THEN 保留旧回调 | 边界 |
| AC-1.8 | WHEN Static API 23 调用 `onAreaChange(undefined)` THEN 清除 area 用户回调 | 正常 |
| AC-1.9 | WHEN `position` 使用 `Position` 形式改变布局位置 THEN `onAreaChange` 可响应；WHEN 使用 `Edges` 或 `LocalizedEdges` 形式改变位置 THEN 不触发该事件 | 边界 |

### US-2: 控制区域变化回调间隔

**作为** ArkUI 应用开发者，

**我想要** 为频繁的区域变化设置期望回调间隔，

**以便** 在保持最新几何状态的同时降低回调频率。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 `onAreaChange(callback)` 且完全省略第二实参 THEN `expectedUpdateInterval` 为 0ms，每次有效区域变化均可触发 | 正常 |
| AC-2.2 | WHEN 调用存在第二实参的重载且第二实参为 `undefined`、null、空对象或非法类型 THEN Dynamic/桥接路径使用默认 1000ms | 边界 |
| AC-2.3 | WHEN interval 为 0 THEN 保持 0；WHEN 为正小数 THEN 截断为 int32；WHEN 为负值、NaN 或负无穷 THEN 回退 1000ms；WHEN 为正无穷或超过 int32 最大值 THEN 钳制为 `INT32_MAX` | 异常 |
| AC-2.4 | WHEN 区域变化发生且距上次执行不足 interval THEN 仅投递一个剩余间隔的延迟任务；WHEN 等待期间继续变化 THEN 不新增任务，执行时重新采样最新区域并合并中间变化 | 正常 |
| AC-2.5 | WHEN 使用 interval 形式注册 THEN 注册时预置当前 area 快照，注册动作本身不产生首次回调，后续实际变化才触发 | 边界 |
| AC-2.6 | WHEN interval 延迟任务已投递后清除用户回调 THEN 任务不被显式取消，但执行时不调用用户回调并清除 pending 状态 | 恢复 |
| AC-2.7 | WHEN area user callback 配置了正 interval 且节点同时存在 inner area callback THEN 当前实现仍可能在普通 `HandleOnAreaChange` 路径调用 user callback，形成节流旁路风险 | 边界 |

### US-3: 监听组件尺寸变化

**作为** ArkUI 应用开发者，

**我想要** 获得组件布局尺寸变化前后的宽高，

**以便** 在尺寸变化时同步调整依赖该尺寸的业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `RenderContext::GetPaintRectWithoutTransform()` 的宽或高发生变化 THEN `onSizeChange` 在几何同步阶段同步触发 | 正常 |
| AC-3.2 | WHEN 仅位置、父级窗口偏移或 transform 变化而宽高不变 THEN `onSizeChange` 不触发 | 边界 |
| AC-3.3 | WHEN `onSizeChange` 回调执行 THEN oldValue/newValue 仅表达旧宽高和新宽高，数值按当前密度从 px 转为 vp | 正常 |
| AC-3.4 | WHEN size 回调首次注册后同步到非零尺寸且旧快照为零矩形 THEN 以零尺寸作为 oldValue、当前尺寸作为 newValue 触发 | 边界 |
| AC-3.5 | WHEN 节点 active=false 时发生尺寸变化 THEN 不立即调用用户回调并设置补偿标志；WHEN 下一次 `SetActive(true)` THEN 立即触发一次补偿回调并清除标志 | 恢复 |
| AC-3.6 | WHEN 对同一节点重复注册 size 回调 THEN 后注册回调覆盖原用户回调槽，已有尺寸快照不因重注册自动清零 | 正常 |
| AC-3.7 | WHEN Dynamic 直接调用 `onSizeChange(undefined/null/非函数)` THEN 参数校验失败并保留旧回调；WHEN Modifier reset 或 Static 传入 undefined THEN 清除 size 回调 | 边界 |

### US-4: 跨离树和重挂载保持几何快照

**作为** ArkUI 框架维护者，

**我想要** 明确区域与尺寸事件在离树、重挂载和 inactive 状态中的行为，

**以便** 避免把缓存继承或补偿回调误判为重复事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN EventHub 与 PipelineContext 绑定 THEN area 节点加入 Pipeline 的 area change 集合；WHEN Context 分离 THEN 从集合移除 | 正常 |
| AC-4.2 | WHEN area 节点离树 THEN 用户回调和旧 area 快照均不清除；WHEN 重挂后再次检测 THEN 使用离树前快照与当前 area 比较 | 边界 |
| AC-4.3 | WHEN 普通 area 检测时节点 active=false THEN 不触发用户回调；WHEN重新 active 且后续 area 检测发现差异 THEN 按保留快照触发 | 边界 |
| AC-4.4 | WHEN size 事件进入几何同步流程 THEN 是否触发由尺寸变化和 active 状态共同决定，不以 visibility 或 `onMainTree_` 单独作为触发条件 | 边界 |

### US-5: 通过 Native Node 订阅区域和尺寸变化

**作为** Native UI 开发者，

**我想要** 通过 Native Node API 获得区域与尺寸变化数据，

**以便** 在 C API 场景使用与 ArkTS 对应的几何事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN API 12 泛型入口注册 `NODE_EVENT_ON_AREA_CHANGE` THEN 回调获得 12 个 f32，依次为旧/新 width、height、localX、localY、pageX、pageY，单位均为 vp | 正常 |
| AC-5.2 | WHEN API 20 注册 `NODE_ON_SIZE_CHANGE` THEN 回调实现提供 4 个 f32，依次为 oldWidth、oldHeight、newWidth、newHeight，单位均为 vp | 正常 |
| AC-5.3 | WHEN API 12 泛型入口对同一 eventType 重复注册 THEN 更新 targetId/userData 并继续使用单个底层用户槽；WHEN 注销 THEN 删除映射并调用对应 Reset | 正常 |
| AC-5.4 | WHEN API 21 CommonEvent 注册 Size THEN 使用独立 CommonEvent size 槽；WHEN使用该入口注册 Area THEN 返回不支持事件类型 | 异常 |
| AC-5.5 | WHEN API 26 调用 `OH_ArkUI_NativeModule_RegisterCommonAreaApproximateChangeEvent` THEN 按归一化后的 interval 使用 area 节流链路，targetId 固定为 0 | 正常 |
| AC-5.6 | WHEN API 12 泛型 `NODE_ON_SIZE_CHANGE` 被注销 THEN 当前实现错误调用 `ResetAreaChanged` 而未清除 size 用户槽；该行为作为实现风险记录 | 边界 |
| AC-5.7 | WHEN API 21/26 CommonEvent 对同一事件重复注册 THEN metadata 中 userData 更新，但 callback map 使用 `insert` 保留首次 callback；该行为与 API 26 头文件“新回调替换旧回调”说明冲突 | 边界 |

### US-6: 识别版本和旧管线边界

**作为** 跨版本应用和框架维护者，

**我想要** 明确各接口的开放版本和旧管线差异，

**以便** 不把新管线能力错误外推到不支持的运行环境。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN 使用 Dynamic ArkTS THEN普通 `onAreaChange` 自 API 8、`onSizeChange` 自 API 12、AreaChangeOptions 重载自 API 26 开放 | 正常 |
| AC-6.2 | WHEN 使用 Static ArkTS THEN普通 area/size 接口自 API 23 static、AreaChangeOptions 重载自 API 26 static 开放 | 正常 |
| AC-6.3 | WHEN 使用 Legacy Pipeline THEN area 注册忽略 minInterval 且 Disable 为空实现，size 注册为空实现 | 边界 |
| AC-6.4 | WHEN 使用 Native Node THEN area 泛型事件自 API 12、size 事件自 API 20、Size CommonEvent 自 API 21、Area interval 专用入口自 API 26 开放 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.9 | R-1~R-7 | 已有实现 | Host/Bridge 单测与源码审查 | `frame_node.cpp:2350-2409,7200-7263`; `event_hub.cpp:819-860`; `js_on_area_change_function.cpp:31-112`; `common.d.ts:22721-22746` |
| AC-2.1~AC-2.7 | R-8~R-14 | 已有实现 | Host 节流单测与源码审查 | `frame_node.cpp:2442-2496`; `view_abstract_test_six_ng.cpp:301-330`; `frame_node_test_ng_coverage.cpp:1079-1243` |
| AC-3.1~AC-3.7 | R-15~R-20 | 已有实现 | Host/Static 单测与源码审查 | `frame_node.cpp:2499-2572,6550-6600`; `event_hub.cpp:464-505`; `frame_node_test_ng_coverage_new.cpp:1492-1572` |
| AC-4.1~AC-4.4 | R-21~R-24 | 已有实现 | Pipeline/生命周期测试与源码审查 | `event_hub.cpp:37-57`; `pipeline_context.cpp:5688-5725`; `frame_node.cpp:2416-2429,2936-2946` |
| AC-5.1~AC-5.7 | R-25~R-31 | 已有实现 | C API 单测与源码审查 | `node_common_modifier.cpp:11056-11103,12536-12605,13698-13710`; `native_node_test.cpp:2759-2765,3054-3059,10312-10325` |
| AC-6.1~AC-6.4 | R-32~R-35 | 已有实现 | SDK/API 审查 | `common.d.ts:22721-22764,25412-25438`; `common.static.d.ets:12835-12856,14196-14206`; `native_node.h:10214-10278,10568-10576,14317-14408` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 普通 area 注册后进行区域检测 | 比较安全区修正后的 frame rect 与父级窗口偏移 | 任一项变化即满足 area 条件 | AC-1.1, AC-1.2 |
| R-2 | 边界 | 仅发生渲染属性变化，或 position 使用 Edges/LocalizedEdges 而未进入受支持的布局位置路径 | area 不触发 | translate/offset/markAnchor/scale/transform 不触发；position(Position) 可触发，Edges/LocalizedEdges 不触发 | AC-1.3, AC-1.9 |
| R-3 | 行为 | area 回调执行 | 输出 SDK 定义的 width/height/position/globalPosition，px 按 density 转 vp | Dynamic 额外别名不属于公开契约 | AC-1.4, AC-1.5 |
| R-4 | 行为 | 同一节点重复注册 area 用户回调 | 后注册覆盖旧单槽 | inner area callbacks 独立保存 | AC-1.6 |
| R-5 | 恢复 | Dynamic target API >= 11 且 area 参数为 undefined | Disable/Clear area 用户回调 | API 11 是清理门槛 | AC-1.7 |
| R-6 | 边界 | Dynamic target API < 11 的 undefined 或任意版本 null/非函数 | 忽略本次调用并保留旧回调 | 不隐式清理 | AC-1.7 |
| R-7 | 恢复 | Static API 23 area 参数为 undefined | 清除 area 用户回调 | API 26 options 重载的 event 不允许 undefined | AC-1.8 |
| R-8 | 行为 | 完全省略 AreaChangeOptions | interval=0ms | 与显式传第二实参不同 | AC-2.1 |
| R-9 | 边界 | 第二实参存在但为 undefined/null/空对象/非法类型 | 默认 interval=1000ms | Dynamic/Modifier/Static 新重载均需记录入口差异 | AC-2.2 |
| R-10 | 异常 | interval 为小数、负数、NaN、无穷或超 int32 | 0 保持；正小数截断；非法负值回退1000；正无穷/过大值钳制 INT32_MAX | Static `int` 类型减少浮点输入面 | AC-2.3 |
| R-11 | 行为 | area 变化距上次回调小于 interval | 只投递一个剩余间隔延迟任务，执行时采样最新 area | 尾沿合并，中间状态不逐次回调 | AC-2.4 |
| R-12 | 边界 | 使用 interval 形式注册 | 预置当前 area 快照，不因注册产生首次回调 | 普通注册使用零初始快照 | AC-2.5 |
| R-13 | 恢复 | pending 延迟任务期间清理 user callback | 任务执行时跳过用户回调并清 pending | 任务本身不显式取消 | AC-2.6 |
| R-14 | 边界 | 正 interval user callback 与 inner callback 并存 | 当前普通处理链仍可能调用 user callback | 作为节流旁路风险记录 | AC-2.7 |
| R-15 | 行为 | paint rect without transform 的 size 变化 | 在几何同步阶段同步触发 size 回调 | 仅比较宽高 | AC-3.1 |
| R-16 | 边界 | 仅位置、父偏移或 transform 变化 | size 不触发 | area 可能因位置/父偏移变化触发 | AC-3.2 |
| R-17 | 行为 | size 回调执行 | old/new 宽高 px 转 vp | SDK 类型为 SizeOptions | AC-3.3 |
| R-18 | 边界 | 首次 size 检测使用零快照 | 非零尺寸以零尺寸 oldValue 触发 | 重注册不自动重置缓存 | AC-3.4, AC-3.6 |
| R-19 | 恢复 | active=false 时发生 size 变化 | 不立即回调并设置补偿标志；active=true 时补偿并清标志 | 补偿由 SetActive 触发 | AC-3.5 |
| R-20 | 边界 | Dynamic direct 参数非法或 Modifier/Static reset | direct 保留旧回调；Modifier reset/Static undefined 清除 | 前端入口行为不同 | AC-3.7 |
| R-21 | 行为 | EventHub attach/detach PipelineContext | attach 注册 area 节点，detach 移除 area 节点 | 回调和快照不随 detach 清理 | AC-4.1, AC-4.2 |
| R-22 | 边界 | area 节点离树后重挂 | 用离树前快照与当前 area 比较 | 离树期间不检测 | AC-4.2 |
| R-23 | 边界 | 普通 area 检测时 active=false | 不触发回调 | interval 延迟路径存在独立门禁风险 | AC-4.3 |
| R-24 | 边界 | size 进入几何同步 | 由 size 差异和 active 决定是否触发/补偿 | visibility/onMainTree 不单独决定 | AC-4.4 |
| R-25 | 行为 | API 12 area 泛型事件派发 | 输出12项 old/new area vp 数据 | 顺序由 public native_node.h 声明 | AC-5.1 |
| R-26 | 行为 | API 20 size 事件派发 | 输出4项 old/new size vp 数据 | public enum 注释未声明 payload，属于实现事实 | AC-5.2 |
| R-27 | 行为 | API 12 泛型注册/注销 | 重复注册更新 targetId/userData；注销删除映射并 Reset | 同 eventType 单项映射 | AC-5.3 |
| R-28 | 异常 | API 21 CommonEvent 注册 Area 或 Size | Size 支持；Area 不在白名单并返回不支持 | CommonEvent targetId 固定为0 | AC-5.4 |
| R-29 | 行为 | API 26 area interval 专用入口注册 | 归一化 interval 后进入 SetOnAreaChangedWithInterval | 回调输出12项 area 数据 | AC-5.5 |
| R-30 | 边界 | API 12 泛型 Size 注销 | 当前 ResetOnSizeChange 实际调用 ResetAreaChanged | 记录实现风险，不提出修复 | AC-5.6 |
| R-31 | 边界 | API 21/26 CommonEvent 重复注册 | userData 更新，callback map 保留首次 callback | 与 API 26 公开替换说明冲突 | AC-5.7 |
| R-32 | 行为 | Dynamic ArkTS 使用 area/size | Area API8，Size API12，Area options API26 | SDK HEAD 与 ace_engine HEAD 为近邻版本 | AC-6.1 |
| R-33 | 行为 | Static ArkTS 使用 area/size | Area/Size API23 static，Area options API26 static | undefined 清理按 Static 声明 | AC-6.2 |
| R-34 | 边界 | Legacy Pipeline 调用 area/size | area 忽略 interval且 Disable 为空；size 为空实现 | 不承诺 NG 等价行为 | AC-6.3 |
| R-35 | 行为 | Native 使用 area/size | Area12、Size20、Size CommonEvent21、Area interval26 | 按入口分别记录支持矩阵 | AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.6, AC-1.9, R-1~R-4 | Host 单测 | area 首次触发、父级移动、position 三种形式、位置/尺寸去重、vp 数据和单槽覆盖 |
| VM-2 | AC-1.7, AC-1.8, R-5~R-7 | Bridge/Static 单测 | Dynamic API11 清理门槛与 Static undefined 清理 |
| VM-3 | AC-2.1~AC-2.5, R-8~R-12 | Bridge + 可控时钟单测 | 第二实参存在性、interval 归一化、尾沿合并和首次触发 |
| VM-4 | AC-2.6, AC-2.7, R-13, R-14 | 可控 TaskExecutor/inner callback 单测 | 清理竞态与 inner callback 节流旁路 |
| VM-5 | AC-3.1~AC-3.4, AC-3.6, R-15~R-18 | Host 单测 | size-only 去重、同步回调、vp 转换和快照继承 |
| VM-6 | AC-3.5, AC-4.4, R-19, R-24 | Host 生命周期单测 | inactive 补偿及 geometry sync 边界 |
| VM-7 | AC-4.1~AC-4.3, R-21~R-23 | Pipeline/生命周期单测 | area 集合注册、离树重挂和 active 门禁 |
| VM-8 | AC-5.1~AC-5.5, R-25~R-29 | C API 单测 | payload 顺序、单位、targetId/userData 和版本通道 |
| VM-9 | AC-5.6, AC-5.7, R-30, R-31 | C API 回归测试 | Size 注销误清 Area 与 CommonEvent 重复注册偏差 |
| VM-10 | AC-6.1~AC-6.4, R-32~R-35 | SDK/API/双管线审查 | Dynamic/Static/Native/Legacy 版本矩阵 |

## API 变更分析

> 本特性为已有 API 的规格补录，不引入新的 API 或 ABI 变更。下表记录纳入规格的现有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `onAreaChange(event: (oldValue: Area, newValue: Area) => void): T` | Public | area 回调 | `T` | N/A | 监听布局区域变化 | AC-1.1~AC-1.8 |
| `onAreaChange(event: AreaChangeCallback, options?: AreaChangeOptions): T` | Public | area 回调、期望间隔 | `T` | N/A | 监听并节流布局区域变化 | AC-2.1~AC-2.7 |
| `onSizeChange(event: SizeChangeCallback): T` | Public | size 回调 | `T` | N/A | 同步监听布局尺寸变化 | AC-3.1~AC-3.7 |
| `ArkUI_NativeNodeAPI_1::registerNodeEvent(...)` | Public C API | node、eventType、targetId、userData | `int32_t` | 0, 401, 106102, 106103 | 注册 Area/Size 泛型事件 | AC-5.1~AC-5.3 |
| `ArkUI_NativeNodeAPI_1::unregisterNodeEvent(...)` | Public C API | node、eventType | `void` | N/A | 注销 Area/Size 泛型事件 | AC-5.3, AC-5.6 |
| `OH_ArkUI_NativeModule_RegisterCommonEvent(...)` | Public C API | node、eventType、userData、callback | `int32_t` | 0, 401, 500, 106110 | API 21 CommonEvent；本特性支持 Size | AC-5.4, AC-5.7 |
| `OH_ArkUI_NativeModule_RegisterCommonAreaApproximateChangeEvent(...)` | Public C API | node、interval、userData、callback | `int32_t` | 0, 401 | API 26 Area interval 专用入口 | AC-5.5, AC-5.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | 本次仅补录规格，无接口变更或废弃 | — | — |

## 接口规格

### 接口定义

**ArkTS onAreaChange**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onAreaChange(event: (oldValue: Area, newValue: Area) => void): T`; `onAreaChange(event: AreaChangeCallback, options?: AreaChangeOptions): T` |
| 返回值 | `T` — 当前组件属性链对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.7, AC-4.1~AC-4.3, AC-6.1~AC-6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `AreaChangeCallback` | 是；Static旧重载可为 undefined | 无 | Dynamic 有效函数注册；API>=11 的 undefined 清理旧回调 |
| options | `AreaChangeOptions` | 否 | 完全省略时 interval=0ms | 第二实参存在但无有效 interval 时使用1000ms |
| expectedUpdateInterval | `int`/桥接数值 | 否 | 1000ms（options 字段） | 负/NaN/-Inf→1000；+Inf/过大→INT32_MAX；正小数截断 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 本地布局 area 或父级窗口偏移改变 | 见 Gherkin 场景“区域变化触发” | AC-1.1~AC-1.4 |
| 2 | 带 interval 的连续区域变化 | 见 Gherkin 场景“尾沿合并” | AC-2.1~AC-2.6 |
| 3 | 离树后重挂 | 见 Gherkin 场景“离树快照继承” | AC-4.1~AC-4.3 |

**ArkTS onSizeChange**

| 属性 | 值 |
|------|-----|
| 函数签名 | `onSizeChange(event: SizeChangeCallback): T`; Static: `onSizeChange(event: SizeChangeCallback | undefined): this` |
| 返回值 | 当前组件属性链对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.7, AC-4.4, AC-6.1~AC-6.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `(oldValue: SizeOptions, newValue: SizeOptions) => void` | Dynamic SDK 是；Static 可为 undefined | 无 | Dynamic direct 仅函数有效；Static undefined 清理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | paint rect 宽高改变且 active=true | 几何同步阶段立即传递 old/new vp 宽高 | AC-3.1~AC-3.4 |
| 2 | inactive 时尺寸改变 | 延迟到下次 active 补偿 | AC-3.5 |
| 3 | 仅位置或 transform 改变 | 不触发 | AC-3.2 |

**NativeNodeAPI_1 Area/Size 事件**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t registerNodeEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType, int32_t targetId, void* userData)`; `void unregisterNodeEvent(ArkUI_NodeHandle node, ArkUI_NodeEventType eventType)` |
| 返回值 | 注册返回错误码；注销无返回值 |
| 开放范围 | Public C API |
| 错误码 | 0, 401, 106102, 106103 |
| 关联 AC | AC-5.1~AC-5.3, AC-5.6, AC-6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| node | `ArkUI_NodeHandle` | 是 | 无 | 有效 CNode；主线程调用 |
| eventType | `ArkUI_NodeEventType` | 是 | 无 | Area 使用 `NODE_EVENT_ON_AREA_CHANGE`；Size 使用 `NODE_ON_SIZE_CHANGE` |
| targetId | `int32_t` | 是 | 无 | 原样写入 NodeEvent custom ID |
| userData | `void*` | 否 | nullptr | 原样传递，生命周期由调用方管理 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 注册 Area 并发生布局区域变化 | 返回12项 vp 数据 | AC-5.1 |
| 2 | 注册 Size 并发生尺寸变化 | 返回4项 vp 数据 | AC-5.2 |
| 3 | 泛型 Size 注销 | 当前实现误清 Area，作为风险验证 | AC-5.6 |

**NativeModule Common Size / Area Interval**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_NativeModule_RegisterCommonEvent(...)`; `OH_ArkUI_NativeModule_RegisterCommonAreaApproximateChangeEvent(...)` 及对应 Unregister |
| 返回值 | `int32_t` — 操作结果码 |
| 开放范围 | Public C API |
| 错误码 | 0, 401, 500（CommonEvent实现分支）, 106110 |
| 关联 AC | AC-5.4, AC-5.5, AC-5.7, AC-6.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| eventType | `ArkUI_NodeEventType` | CommonEvent 是 | 无 | 本特性 CommonEvent 白名单仅支持 Size，不支持 Area |
| expectedUpdateInterval | `float` | Area interval 是 | 无 | 使用与 ArkTS 类似的归一化规则 |
| callback | 函数指针 | 是 | 无 | 空回调返回401；重复注册当前不替换首次 callback |
| userData | `void*` | 否 | nullptr | 重复注册时更新；targetId 固定0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | API21 CommonEvent 注册 Size | 使用独立 size CommonEvent 槽 | AC-5.4 |
| 2 | API26 Area interval 注册 | 按间隔尾沿合并并输出12项 area 数据 | AC-5.5 |
| 3 | 相同事件重复注册 | 首次 callback 与最新 userData 组合，记录契约偏差 | AC-5.7 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次仅补录当前实现；需保留以下版本和实现差异：
  - Dynamic 普通 Area 自 API 8、Size 自 API 12、AreaChangeOptions 自 API 26；Static 普通 Area/Size 自 API 23 static、options 自 API 26 static。
  - 完全省略 options 为 0ms，但显式存在无效第二实参时回退1000ms。
  - Dynamic area 支持 API>=11 的 undefined 清理；Dynamic size direct 不支持 undefined 清理；Static 两个旧接口都允许 undefined。
  - Legacy area 忽略 interval且 Disable 为空，Legacy size 为空实现。
  - Native Area API12、Size API20、Size CommonEvent API21、Area interval API26。
  - Native Size public enum 注释未声明4项 payload，但实现稳定写入 old/new width/height。
  - API12 Size 注销误清 Area；API21/26 CommonEvent 重复注册不替换首次 callback，均作为现状风险。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic Area API 8；完整 Dynamic Area+Size 为 API12；完整 options/Static 能力到 API26。
- **API 版本号策略:** 按 canonical SDK 与 `native_node.h` 的 `@since` 标注；SDK HEAD 与 ace_engine HEAD 相差4天，属于近邻版本而非 manifest 锁定同提交，需后续复核。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 两套独立快照 | Area 使用 frame rect + parent offset；Size 使用 paint rect size，不得共用触发定义 | AC-1.1~AC-1.3, AC-3.1~AC-3.4 |
| 布局驱动 | 两事件描述布局/几何同步结果，不把纯 render transform 视为布局变化 | AC-1.3, AC-3.2 |
| 节流尾沿合并 | interval area 在单 pending 任务中合并中间变化，执行时读取最新状态 | AC-2.4, AC-2.6 |
| 单用户槽 | area/size 各一个用户回调槽，inner 和 JS FrameNode 回调属于独立通道 | AC-1.6, AC-3.6 |
| 生命周期缓存保留 | detach/重注册不自动清空几何快照，必须按继承语义验证 | AC-3.4~AC-3.6, AC-4.1~AC-4.4 |
| 实现即规格 | Size 注销误清 Area、节流旁路和 CommonEvent 替换偏差仅登记风险，不修改产品行为 | AC-2.7, AC-5.6, AC-5.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | interval>0 时同一 pending 窗口最多保留一个延迟任务，中间变化合并为最新值 | 可控时钟/TaskExecutor 单测 | `frame_node.cpp:2442-2496` |
| 功耗 | Area interval 可降低连续布局变化的用户回调频率；Size 不额外创建周期任务 | Host 性能测试/源码审查 | `frame_node.cpp:2442-2496,2546-2570` |
| 内存 | Area/Size 用户回调均为单槽；节点保存有限数量 rect/offset 快照和一个 pending 标志 | Host 单测/源码审查 | `frame_node.h:1856-1859`; `event_hub.h:344-351` |
| 安全 | Native API 校验 node、eventType 和主线程；NodeEvent 数据只在回调期间有效 | C API 错误路径测试 | `native_node.h:12931-12939,13080-13107` |
| 可靠性 | inactive size 通过补偿标志恢复；area 延迟任务清理 callback 后安全跳过 | 生命周期/竞态单测 | `frame_node.cpp:2442-2496,2936-2946` |
| 可测试性 | 核心分支已有覆盖；前端参数存在性、真实节流合并、Native payload/注销仍需补充 | 覆盖审查 | `frame_node_test_ng_coverage.cpp:1079-1243`; `native_node_test.cpp:10312-10325` |
| 自动化维测 | 通过 area/size eventType、targetId/userData、interval 和 active 状态定界 | 日志/断点 | Native event map 与 FrameNode 快照字段 |
| 定界定位 | Area 问题优先检查 rect/parent offset/Pipeline 集合；Size 问题检查 paint size/active/补偿标志 | 分层诊断 | `frame_node.cpp:2381-2572`; `pipeline_context.cpp:5688-5725` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | 坐标和尺寸统一按当前 density 转 vp | Host/XTS | 通用 FrameNode 与 Pipeline 实现 |
| 平板 | 无差异 | 同手机 | Host/XTS | 通用实现 |
| 折叠屏 | 无接口差异 | 折叠导致的真实布局区域/尺寸变化按本规格触发 | 多窗口/折叠场景测试 | 通用布局事件链 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变无障碍语义；仅观察几何结果 | — |
| 大字体 | 是 | 字体缩放引起真实布局 area/size 变化时可触发 | AC-1.2, AC-3.1 |
| 深色模式 | 否 | 单纯颜色变化不触发布局几何事件 | AC-1.3, AC-3.2 |
| 多窗口/分屏 | 是 | 窗口布局变化和父级偏移变化可触发 Area，尺寸变化可触发 Size | AC-1.2, AC-3.1 |
| 多用户 | 否 | 无用户数据持久化 | — |
| 版本升级 | 是 | API 8/11/12/20/21/23/26 和 Legacy 差异需保留 | AC-1.7, AC-6.1~AC-6.4 |
| 生态兼容 | 是 | Dynamic/Static/Native 参数、清理和支持矩阵不完全一致 | AC-2.1~AC-2.3, AC-5.1~AC-5.7 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 组件区域与尺寸变化事件
  作为 ArkUI 应用或 Native UI 开发者
  我想要监听组件布局区域和尺寸变化
  以便使用可预测的几何数据更新业务状态

  Scenario: 父级移动触发子节点区域变化
    Given 子节点尺寸和本地布局矩形保持不变
    And 子节点已注册 onAreaChange
    When 父级到窗口的偏移发生变化
    Then 子节点 onAreaChange 触发
    And newValue.globalPosition 反映新的窗口位置

  Scenario: 位置变化不触发尺寸事件
    Given 节点宽高保持不变
    And 节点已注册 onSizeChange
    When 节点仅发生 transform 或不改变宽高的位置变化
    Then onSizeChange 不触发

  Scenario: 区域节流采用尾沿合并
    Given area interval 为 1000ms
    When 1000ms 窗口内区域连续变化多次
    Then 最多保留一个 pending 延迟任务
    And 任务执行时回调使用最新区域

  Scenario Outline: interval 非法值归一化
    Given 使用 AreaChangeOptions 注册 area 回调
    When expectedUpdateInterval 为 <输入>
    Then 内部 interval 为 <结果>

    Examples:
      | 输入 | 结果 |
      | 0 | 0 |
      | -1 | 1000 |
      | NaN | 1000 |
      | +Infinity | INT32_MAX |

  Scenario: inactive 尺寸变化延迟补偿
    Given 节点 active=false 且已注册 onSizeChange
    When 节点尺寸发生变化
    Then 用户回调不立即执行
    When 节点随后 SetActive(true)
    Then 执行一次尺寸变化补偿回调

  Scenario: 泛型 Native Size 注销实现风险
    Given 同一节点同时注册 Area 和 Size 泛型事件
    When 注销 NODE_ON_SIZE_CHANGE
    Then 当前实现调用 ResetAreaChanged
    And 该行为作为兼容风险记录而非修复要求
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：仅覆盖 onAreaChange/onSizeChange，不包含可见区域监听、生命周期、焦点或绘制完成事件
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致，每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] ArkTS Public API 已与 canonical Dynamic/Static SDK 交叉核查
- [x] Native API 已与 `native_node.h`、NodeModel、NodeModifier 和真实 EventHub 链路交叉核查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode TriggerOnAreaChangeCallback onSizeChange interval lastFrameRect parent offset active compensate"
  - repo: "openharmony/arkui_ace_engine"
    query: "NODE_EVENT_ON_AREA_CHANGE NODE_ON_SIZE_CHANGE payload register unregister common area approximate"
  - repo: "openharmony/interface_sdk-js"
    query: "CommonMethod onAreaChange AreaChangeOptions onSizeChange API version static dynamic"
```

**关键文档：** `frameworks/core/components_ng/base/frame_node.cpp`; `frameworks/core/components_ng/event/event_hub.cpp`; `interfaces/native/native_node.h`
