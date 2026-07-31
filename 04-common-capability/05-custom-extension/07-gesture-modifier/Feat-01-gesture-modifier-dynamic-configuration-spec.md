# 特性规格

> Func-04-05-07-Feat-01 gestureModifier 动态手势配置：固化 `gestureModifier`、`GestureModifier`、`UIGestureEvent`、GestureHandler 家族及动态/静态前端的现有行为。本规格只记录已有实现，不修改产品代码。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | gestureModifier 动态手势配置 |
| 特性编号 | Func-04-05-07-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 12～23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Modifier 入口与应用生命周期 | 补录动态 API 12、静态 API 23 的 `gestureModifier` 与 `applyGesture` |
| ADDED | UIGestureEvent 手势管理 | 补录添加、并行添加、按 tag 删除、全量清理 |
| ADDED | Handler 与组合构建 | 补录六类 GestureHandler、GestureGroupHandler 及 API 12～23 演进 |
| ADDED | 兼容性和实现偏差 | 记录动态/静态差异、公开 Native 能力缺口与静态 peer hook 风险 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/05-custom-extension/07-gesture-modifier/design.md` | Baselined |
| Gesture Capability Context | `docs/kb/capabilities/gesture-capability.md` | Context |
| Dynamic Common SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | Source |
| Dynamic Gesture SDK | `interface/sdk-js/api/@internal/component/ets/gesture.d.ts` | Source |
| Static Common SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets` | Source |
| Static Gesture SDK | `interface/sdk-js/api/arkui/component/gesture.static.d.ets` | Source |

## 用户故事

### US-1: 动态配置和更新手势

**作为** 应用开发者，
**我想要** 通过自定义 GestureModifier 按状态构建组件手势，
**以便** 在不改变组件结构的情况下切换手势组合。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态前端调用 `gestureModifier(modifier)` 且 `applyGesture` 已实现 THEN 框架先清空该节点的 modifier 手势，再同步调用 `applyGesture(event)` 重建配置 | 正常 |
| AC-1.2 | WHEN 活动触摸序列尚未全部抬起时重新应用 modifier THEN 当前序列继续使用已收集的 recognizer，新配置从下一轮手势开始生效，清理过程不主动发送 Cancel | 边界 |
| AC-1.3 | WHEN 动态前端传入 `null` 或 `undefined` THEN 动态全局入口直接返回，既有 modifier 手势保持不变 | 边界 |
| AC-1.4 | WHEN 静态前端传入 `undefined` 且节点已有 UIGestureEvent THEN 清空 modifier 手势并释放该组件保存的 UIGestureEvent 引用 | 边界 |
| AC-1.5 | WHEN 在动态 `attributeModifier` 内调用 `gestureModifier` 或对动态自定义组件调用 THEN 该用法不属于 SDK 支持范围 | 异常 |

### US-2: 添加手势、优先级和 Mask

**作为** 应用开发者，
**我想要** 通过 UIGestureEvent 添加普通、高优先级或父子并行手势，
**以便** 控制手势竞争关系。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 `addGesture(handler)` 且省略 priority/mask THEN 使用 `GesturePriority.NORMAL` 和 `GestureMask.Normal` | 正常 |
| AC-2.2 | WHEN 调用 `addGesture(handler, GesturePriority.PRIORITY, mask)` THEN Handler 以高优先级配置进入 modifier 手势层级 | 正常 |
| AC-2.3 | WHEN 调用 `addParallelGesture(handler, mask)` THEN 内部以 Parallel priority 添加；公开 `GesturePriority` 枚举不新增 Parallel 成员 | 正常 |
| AC-2.4 | WHEN Handler 是 GestureGroupHandler THEN 组模式、子 Handler、组 tag 和 onCancel 被转换为组合 Gesture 并整体挂载 | 正常 |
| AC-2.5 | WHEN Handler 类型不属于六类基础 Handler 或 GestureGroupHandler THEN 前端分发不创建对应 Gesture | 异常 |

### US-3: 按 tag 移除和全量清理

**作为** 应用开发者，
**我想要** 增量移除特定手势或清空 modifier 手势，
**以便** 管理复杂条件分支中的手势集合。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 调用 `removeGestureByTag(tag)` THEN 删除全部同名顶层 modifier 手势，并递归删除任意嵌套 GestureGroup 中的同名子手势 | 正常 |
| AC-3.2 | WHEN tag 不存在 THEN 手势列表和 recognizer 层级保持不变，接口返回 void | 边界 |
| AC-3.3 | WHEN tag 为显式空字符串 THEN 只匹配通过 `tag("")` 设置了空 tag 的手势；未调用 tag 的 optional 空值不匹配 | 边界 |
| AC-3.4 | WHEN 调用 `clearGestures()` THEN 仅清空通过 Modifier 绑定的手势及其备份/层级，不清除其他声明式手势集合 | 正常 |
| AC-3.5 | WHEN tag 删除导致列表变化 THEN 标记需要重新收集并更新 modifier recognizer 层级 | 正常 |

### US-4: Handler 参数和版本演进

**作为** 应用开发者，
**我想要** 使用基础、组合 Handler 及其版本化参数，
**以便** 在不同 API 版本获得可预期的手势行为。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 12 创建 Tap/LongPress/Pan/Swipe/Pinch/Rotation/GestureGroup Handler THEN 可通过对应 Options 和回调构建手势 | 正常 |
| AC-4.2 | WHEN API 14 设置 `allowedTypes` THEN 只响应允许的 SourceTool；空数组转换为 0 位图并按当前实现等价于允许全部来源，CANCEL 仍放行 | 边界 |
| AC-4.3 | WHEN API 15 设置 `isFingerCountLimited=true` THEN recognizer 要求精确匹配手指数 | 正常 |
| AC-4.4 | WHEN API 18 使用连续手势 `onActionCancel(Callback<GestureEvent>)` THEN 回调可获得 GestureEvent；API 12 无事件重载继续兼容 | 正常 |
| AC-4.5 | WHEN API 19 使用动态 Pan `distanceMap` THEN 可按 SourceTool 配置距离；静态前端在 API 23 尚未开放该字段 | 边界 |
| AC-4.6 | WHEN API 22 设置 LongPress `allowableMovement` THEN 使用该移动阈值；非正值采用 SDK 定义的默认处理 | 边界 |
| AC-4.7 | WHEN API 23 设置 Tap `distanceThreshold` THEN 动态/静态 Handler 支持该字段；省略时默认 Infinity | 边界 |

### US-5: 多前端和 Native 边界

**作为** 框架维护者，
**我想要** 明确动态、静态和 Native 通道的能力边界，
**以便** 避免将内部接口误写成公开契约。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 对照动态与静态 SDK THEN 分别记录参数类型、默认值、单位和开放版本，不静默合并冲突声明 | 正常 |
| AC-5.2 | WHEN 使用公开 Native Gesture API THEN 可按 recognizer 添加/移除，但按 tag 删除、清空和 allowedTypes 的完整公开 C API 等价接口在 ace_engine 中未找到 | 边界 |
| AC-5.3 | WHEN 静态 CommonMethod 普通组件路径应用 gestureModifier THEN 使用已实现的 component hook 清空并重建 | 正常 |
| AC-5.4 | WHEN 静态生成 AttributeModifier 通过 peer hook 应用 gestureModifier THEN 当前实现抛出 `Not implemented`，不得描述为已支持 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1～AC-1.5 | R-1～R-5 | TASK-1 | SDK/前端单测与源码审查 | `common.d.ts:25203-25220,30502-30528`；`ArkComponent.ts:6652-6675`；`hooks/index.ets:182-201` |
| AC-2.1～AC-2.5 | R-6～R-9 | TASK-2 | Bridge/Node Modifier/组合手势测试 | `ArkComponent.ts:6479-6554`；`node_gesture_modifier.cpp:753-774` |
| AC-3.1～AC-3.5 | R-10～R-13 | TASK-3 | GestureEventHub 定向单测 | `gesture_event_hub.cpp:1421-1473`；`gesture_group.cpp:143-157` |
| AC-4.1～AC-4.7 | R-14～R-20 | TASK-4 | SDK 版本矩阵与 recognizer 测试 | `gesture.d.ts:2203-3102`；`gesture.static.d.ets:1522-2138` |
| AC-5.1～AC-5.4 | R-21～R-24 | TASK-5 | 多前端/Native 对照与风险测试 | `native_gesture.h:1153-1174`；`hooks/index.ets:178-201` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 有效 GestureModifier 被应用 | 先 clear modifier 手势，再同步执行 applyGesture 重建 | 不基于 modifier 对象 identity 做差量比较 | AC-1.1 |
| R-2 | 边界 | 活动触摸序列中重应用 | 当前序列继续使用已收集 recognizer；新层级供下一轮使用 | clear 本身不发送 Cancel | AC-1.2 |
| R-3 | 边界 | 动态参数为 null/undefined | 入口返回且保留旧手势 | 动态 SDK 签名本身不接受 undefined | AC-1.3 |
| R-4 | 边界 | 静态参数为 undefined | 清空并释放组件侧 UIGestureEvent | 仅静态签名公开 undefined | AC-1.4 |
| R-5 | 异常 | 动态自定义组件或 attributeModifier 内调用 | 属于 SDK 不支持范围 | 无公开错误码 | AC-1.5 |
| R-6 | 行为 | addGesture 省略可选参数 | priority=Normal、mask=Normal | 返回 void | AC-2.1 |
| R-7 | 行为 | priority=PRIORITY | 以 High/优先手势关系挂载 | GesturePriority 公开值只有 NORMAL/PRIORITY | AC-2.2 |
| R-8 | 行为 | addParallelGesture | 内部使用 Parallel priority 调用统一添加路径 | Parallel 不属于公开 GesturePriority 枚举 | AC-2.3 |
| R-9 | 异常 | 未知 Handler 类型 | 不创建/挂载 Gesture | switch/default 或类型判断直接跳过 | AC-2.4, AC-2.5 |
| R-10 | 行为 | tag 匹配一个或多个顶层/组内手势 | 删除全部命中项并递归组 | 遍历不在首个命中后停止 | AC-3.1 |
| R-11 | 边界 | tag 不存在 | no-op | 返回 void、无错误码 | AC-3.2 |
| R-12 | 边界 | tag="" | 仅匹配显式 optional value="" | 未设置 tag 的 optional 无值不匹配 | AC-3.3 |
| R-13 | 行为 | clear 或删除后列表变化 | 更新 modifierGestures、backup 和 recognizer hierarchy | 不影响普通 gestures_ 集合 | AC-3.4, AC-3.5 |
| R-14 | 行为 | API 12 使用 Handler 家族 | 支持六类基础 Handler 和 Group Handler | 参数遵循各 Handler Options | AC-4.1 |
| R-15 | 边界 | allowedTypes 为空数组 | 当前实现以 0 位图视为允许全部；非空时过滤来源 | Touch/Axis CANCEL 放行 | AC-4.2 |
| R-16 | 行为 | isFingerCountLimited=true | 要求精确手指数 | 动态 API 15、静态 API 23 | AC-4.3 |
| R-17 | 行为 | API 18 连续 Handler cancel | 支持携带 GestureEvent 的重载 | 静态 API 23 仅声明带事件形式 | AC-4.4 |
| R-18 | 边界 | 动态 API 19 Pan distanceMap | 按 SourceTool 选择距离 | 静态到 API 26 才开放，超出本规格目标版本 | AC-4.5 |
| R-19 | 边界 | LongPress allowableMovement≤0 | 使用 SDK/实现默认处理 | 动态 API 22 | AC-4.6 |
| R-20 | 边界 | Tap distanceThreshold 省略 | 使用 Infinity | 动态 API 23、静态 API 23 | AC-4.7 |
| R-21 | 边界 | 动态/静态声明冲突 | 分通道记录，不推导统一默认值 | Pan 单位、Pinch/Rotation fingers 等见兼容表 | AC-5.1 |
| R-22 | 边界 | 查询 Native 等价能力 | 仅记录公开 native_gesture.h 的 recognizer add/remove | tag 删除/clear/allowedTypes 公开等价接口未找到 | AC-5.2 |
| R-23 | 行为 | 静态普通组件 hook | clear 后 apply | component overload 已实现 | AC-5.3 |
| R-24 | 异常 | 静态 AttributeModifier peer hook | 抛出 Not implemented | 当前无对应单测证明可用 | AC-5.4 |

实现证据：`frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:6462-6675`、`frameworks/core/components_ng/event/gesture_event_hub.cpp:573-595,675-733,1421-1473`、`frameworks/core/components_ng/gestures/gesture_group.cpp:143-157`、`frameworks/core/components_ng/gestures/recognizers/gesture_recognizer.cpp:93-135,216-229`。

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1～AC-1.5, R-1～R-5 | 动态/静态前端单测 | clear/apply 顺序、null/undefined 差异、当前序列不 Cancel |
| VM-2 | AC-2.1～AC-2.5, R-6～R-9 | Bridge 与 Node Modifier 单测 | priority/mask 默认、Parallel 映射、Group 构建、未知类型 |
| VM-3 | AC-3.1～AC-3.5, R-10～R-13 | GestureEventHub/Group 单测 | 全部同 tag、嵌套递归、不存在/空 tag、层级重建 |
| VM-4 | AC-4.1～AC-4.7, R-14～R-20 | SDK API 检查和 recognizer 单测 | API 12/14/15/18/19/22/23 演进、SourceTool 过滤 |
| VM-5 | AC-5.1～AC-5.4, R-21～R-24 | SDK 差异审查、C API 编译检查、静态异常测试 | 不静默合并契约、Native 缺口、peer hook 抛错 |

## API 变更分析

> 本节为已有 API 补录，不代表本次提交新增产品接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `CommonMethod.gestureModifier` | Public | GestureModifier；静态支持 undefined | 当前组件 | N/A | 绑定/更新 Modifier 手势 | AC-1.1～AC-1.5 |
| `GestureModifier.applyGesture` | Public | UIGestureEvent | void | N/A | 构建本轮目标手势集合 | AC-1.1, AC-1.2 |
| `UIGestureEvent.addGesture` | Public | Handler、可选 priority/mask | void | N/A | 添加普通或高优先级手势 | AC-2.1, AC-2.2 |
| `UIGestureEvent.addParallelGesture` | Public | Handler、可选 mask | void | N/A | 添加父子并行手势 | AC-2.3 |
| `UIGestureEvent.removeGestureByTag` | Public | string tag | void | N/A | 删除所有同 tag Modifier 手势 | AC-3.1～AC-3.3 |
| `UIGestureEvent.clearGestures` | Public | 无 | void | N/A | 清空全部 Modifier 手势 | AC-3.4 |
| `GestureHandler`/六类 Handler | Public | 各 Handler Options/Callbacks | Handler | N/A | 创建基础手势描述对象 | AC-4.1～AC-4.7 |
| `GestureGroupHandler` | Public | mode、Handler 数组、onCancel | Handler | N/A | 创建组合 Handler | AC-2.4, AC-4.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `GestureHandler.allowedTypes` | 变更（API 14 增量） | 按输入来源过滤 | API 14+ 设置；空数组按当前实现等价允许全部 | AC-4.2 |
| `BaseHandlerOptions.isFingerCountLimited` | 变更（API 15 增量） | 多指精确匹配 | API 15+ 设置 | AC-4.3 |
| 连续 Handler `onActionCancel` | 变更（API 18 重载） | 取消事件数据 | 新代码优先使用带 GestureEvent 重载 | AC-4.4 |
| Pan `distanceMap` | 变更（API 19 增量） | 分 SourceTool 阈值 | 动态 API 19+；静态 API 26+ | AC-4.5 |
| LongPress `allowableMovement` | 变更（API 22 增量） | 长按移动阈值 | API 22+ 设置 | AC-4.6 |
| Tap `distanceThreshold` | 变更（API 23 增量） | 点击移动阈值 | API 23+ 设置 | AC-4.7 |

## 接口规格

### 接口定义

**gestureModifier / applyGesture**

| 属性 | 值 |
|------|-----|
| 函数签名 | `gestureModifier(modifier: GestureModifier): T`；static: `gestureModifier(modifier: GestureModifier \| undefined): this` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1～AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier | GestureModifier | 动态是；静态否 | 静态 undefined | 动态不支持自定义组件，不能在 attributeModifier 内调用 |

**UIGestureEvent 手势管理**

| 属性 | 值 |
|------|-----|
| 函数签名 | `addGesture(handler, priority?, mask?)` / `addParallelGesture(handler, mask?)` / `removeGestureByTag(tag)` / `clearGestures()` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1～AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| handler | GestureHandler | 是 | 无 | 六类基础 Handler 或 GestureGroupHandler |
| priority | GesturePriority | 否 | NORMAL | 公开值 NORMAL/PRIORITY |
| mask | GestureMask | 否 | Normal | Normal/IgnoreInternal |
| tag | string | 是 | 无 | 删除全部显式匹配项；不存在时 no-op |

详细行为由 Gherkin 场景 GM-1～GM-8 覆盖。

## 兼容性声明

- **已有 API 行为变更:** 否；本文补录当前行为。动态与静态存在以下声明/实现差异：
  - 动态 `gestureModifier` 不接受 undefined，静态接受；动态 null/undefined 实现入口不清理，静态 undefined 清理。
  - 动态连续 Handler 同时保留 API 12 无事件 cancel 和 API 18 带事件 cancel；静态 API 23 仅声明带事件形式。
  - 动态 Pan `distanceMap` 自 API 19；静态到 API 26 才开放。
  - 动态文档明确 gestureModifier 下 Pan `distance` 单位为 px；静态文档写 vp。
  - 动态 Pinch/Rotation fingers 默认 2、范围 2～5；静态 API 23 文档写默认 1。
  - 静态 PanDirection 公开显式组合枚举，动态通过基础位值组合。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；状态仅存于前端 UIGestureEvent 和 GestureEventHub 内存对象。
- **最低支持版本:** 动态 API 12；静态 API 23。
- **API 版本号策略:** 逐项保留 SDK `@since`；API 26 静态 distanceMap 仅作为超出目标范围的兼容性注记。
- **实现偏差:** 静态 AttributeModifier peer hook 当前抛出 `Not implemented`（`hooks/index.ets:178-180`）；不得作为可用能力验收。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | Public API 以 canonical dynamic/static SDK 为准，源码偏差进入风险表 | AC-4.1～AC-5.4 |
| Modifier 手势隔离 | clear/remove 只操作 GestureEventHub 的 modifierGestures，不清普通 gestures | AC-3.4 |
| 当前序列稳定 | 配置更新不得主动取消已收集 recognizer；下一轮使用新层级 | AC-1.2 |
| 层级单向调用 | SDK/前端 → Native bridge → node gesture modifier → GestureEventHub | AC-1.1～AC-3.5 |
| 公开/内部接口分离 | 内部 ArkUIGestureModifier 的 tag/clear 不得冒充 public native_gesture.h API | AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增固定数值指标；更新不进入每个 MOVE 的重复重建路径 | 调用链审查 | `ArkComponent.ts:6652-6675` |
| 功耗 | 无新增后台任务或轮询 | 源码审查 | 同步 apply 路径 |
| 内存 | 节点销毁回调移除动态前端 modifier map 条目 | 单测/源码审查 | `ArkComponent.ts:6469-6475` |
| 安全 | 无权限和跨进程输入；回调遵循 ArkUI Full SysCap | SDK 检查 | canonical SDK 声明 |
| 可靠性 | 活动序列更新不主动 Cancel；tag 不存在为 no-op | 场景测试 | GM-2、GM-6 |
| 可测试性 | 覆盖动态、静态、EventHub、Group、Recognizer 和 Native 声明层 | 分层单测 | VM-1～VM-5 |
| 自动化维测 | 无新增日志/事件埋点 | 源码审查 | 当前实现无专用日志协议 |
| 定界定位 | 通过节点、modifierGestures、modifierGestureHierarchy、tag 定位 | UT/调试检查 | `gesture_event_hub.h:558-562` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无组件级差异 | 通过 SourceTool 过滤 Finger/Pen/Mouse 等来源 | 输入源单测 | `gesture_recognizer_test_ng.cpp:1479-1635` |
| 平板 | 无组件级差异 | 同手机；可覆盖触控笔 distanceMap | 输入源单测 | `gesture.d.ts:2500-2666` |
| 折叠屏 | 无折叠状态专属逻辑 | 节点手势配置随组件实例维护 | 多窗口/布局回归 | GestureEventHub 节点存储 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Click/LongPress recognizer 仍沿用 GestureEventHub 无障碍回调装配 | GM-1 |
| 大字体 | 否 | 不涉及文本布局 |
| 深色模式 | 否 | 不涉及颜色和主题 |
| 多窗口/分屏 | 是 | 每个 FrameNode 独立保存 Modifier 手势，不共享跨窗口状态 | GM-1, GM-8 |
| 多用户 | 否 | 无持久化用户数据 |
| 版本升级 | 是 | 按 API 12～23 时间线兼容，静态 API 23 独立声明 | AC-4.1～AC-4.7 |
| 生态兼容 | 是 | 动态/静态差异和 Native 缺口必须显式记录 | AC-5.1～AC-5.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: gestureModifier 动态手势配置

  Scenario: GM-1 有效 Modifier 全量重建
    Given 节点已通过 gestureModifier 绑定一个 TapGestureHandler
    When 状态变化后再次应用包含 LongPressGestureHandler 的同一 Modifier
    Then 框架先清空 modifier 手势再执行 applyGesture
    And 下一轮触摸只收集新配置的 LongPress recognizer

  Scenario: GM-2 活动手势期间切换
    Given 当前触摸序列已经收集旧 recognizer 且手指尚未全部抬起
    When gestureModifier 应用新配置
    Then 当前 recognizer 不因 clear 主动收到 Cancel
    And 新配置从所有手指抬起后的下一轮生效

  Scenario: GM-3 动态与静态 undefined 差异
    Given 节点已经存在 Modifier 手势
    When 动态入口传入 undefined
    Then 旧手势保持
    When 静态入口传入 undefined
    Then Modifier 手势被清空

  Scenario: GM-4 添加 Parallel 手势
    Given 一个有效 TapGestureHandler
    When 调用 addParallelGesture(handler, GestureMask.Normal)
    Then 内部以 Parallel priority 挂载
    And 公开 GesturePriority 枚举仍只有 NORMAL 和 PRIORITY

  Scenario: GM-5 删除全部同名手势
    Given 顶层和嵌套 GestureGroup 中各有多个 tag 为 drag 的 Handler
    When 调用 removeGestureByTag("drag")
    Then 所有显式 tag 为 drag 的手势均被删除
    And recognizer 层级重新收集

  Scenario: GM-6 删除不存在 tag
    Given 节点有两个 tag 不为 missing 的 Modifier 手势
    When 调用 removeGestureByTag("missing")
    Then 两个手势均保留
    And 接口不抛出错误码

  Scenario: GM-7 空 allowedTypes
    Given Handler 调用 allowedTypes([])
    When Finger 或 Axis 输入到达
    Then 当前实现将 0 位图视为允许全部来源
    And CANCEL 事件不被来源过滤阻断

  Scenario: GM-8 静态 AttributeModifier peer 路径
    Given 静态生成的 CommonMethodModifier 通过 peer hook 应用 gestureModifier
    When hookGestureModifier(peer, value) 被调用
    Then 当前实现抛出 Not implemented
    And 该路径不计入支持能力
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（“快速”“稳定”“尽可能”等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "gestureModifier UIGestureEvent clear apply lifecycle GestureEventHub"
  - repo: "openharmony/arkui_ace_engine"
    query: "removeGestureByTag nested GestureGroup modifierGestures"
  - repo: "openharmony/interface_sdk-js"
    query: "GestureModifier GestureHandler API 12 23 dynamic static"
```

**关键文档：**

- `docs/kb/capabilities/gesture-capability.md`
- `interface/sdk-js/api/@internal/component/ets/common.d.ts:25203-25220,30440-30528`
- `interface/sdk-js/api/@internal/component/ets/gesture.d.ts:2203-3135`
- `interface/sdk-js/api/arkui/component/common.static.d.ets:14045-14054,16561-16626`
- `interface/sdk-js/api/arkui/component/gesture.static.d.ets:1522-2165`
- `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:6462-6675`
- `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/hooks/index.ets:178-201`
- `frameworks/core/components_ng/event/gesture_event_hub.cpp:573-595,675-733,1421-1473`
- `frameworks/core/components_ng/gestures/gesture_group.cpp:143-157`
- `interfaces/native/native_gesture.h:1153-1174`
