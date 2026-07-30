# 特性规格

> Func-04-04-01-Feat-02 触摸事件与多点数据模型：固化动态/静态 ArkTS 与 Native C API 的触摸类型、基础元数据、多点列表、触点标识、坐标系统、版本差异和异常边界。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 触摸事件与多点数据模型 (Touch Event and Multi-pointer Data Model) |
| 特性编号 | Func-04-04-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 ArkTS API 7~26；静态 ArkTS API 23~26；Native API 12~26，API 7/8/9/10/12/15/20/21/23/26 存在能力边界 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 触摸类型与基础元数据规格 | 补录 `TouchType`、事件时间、来源、输入工具、设备 ID 和目标屏幕 ID 的动态/静态版本契约 |
| ADDED | 多点触摸数据模型规格 | 补录 `touches`、`changedTouches`、触点 ID、重采样、非活动触点类型和空数组边界 |
| ADDED | 坐标系统规格 | 补录局部、窗口、屏幕、全局显示坐标，废弃 `screenX/screenY` 和实时局部坐标 |
| ADDED | Native 触摸访问规格 | 补录当前变化点、`ByIndex`、最多 10 点、长度单位、状态查询和错误返回行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| 功能域设计 | `specs/04-common-capability/04-common-events/01-touch-events/design.md` | 与本 Spec 增量同步 |
| 动态 ArkTS SDK 契约 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:9252`、`:10668`、`:10983`；`@internal/component/ets/enums.d.ts:620` | 已核验 |
| 静态 ArkTS SDK 契约 | `interface/sdk-js/api/arkui/component/common.static.d.ets:4520`、`:5333`、`:5536`；`enums.static.d.ets:467` | 已核验 |
| 平台输入转换 | `adapter/ohos/entrance/mmi_event_convertor.cpp:182`、`:235`、`:444` | 已核验 |
| NG 触摸事件实现 | `frameworks/core/components_ng/event/touch_event.cpp:109`、`:154`、`:191`、`:234` | 已核验 |
| ArkTS 事件对象转换 | `frameworks/bridge/declarative_frontend/engine/functions/js_touch_function.cpp:28`；`engine/jsi/nativeModule/arkts_native_frame_node_bridge.cpp:235` | 已核验 |
| Native SDK 与实现 | `interfaces/native/ui_input_event.h:437`、`:482`、`:549`、`:831`、`:2150`；`interfaces/native/event/ui_input_event.cpp:719`、`:818`、`:889` | 已核验 |

## 用户故事

### US-1: 识别触摸类型和基础来源

**作为** ArkUI 应用开发者，
**我想要** 从触摸事件读取稳定的类型、时间和输入来源信息，
**以便** 根据触摸生命周期、设备和输入工具执行不同交互逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 动态 ArkTS API 7+ 接收普通触摸事件 THEN `TouchType.Down/Up/Move/Cancel` 分别使用枚举值 0/1/2/3 | 正常 |
| AC-1.2 | WHEN 动态 ArkTS API 20+ 或静态 ArkTS API 23+ 接收无障碍悬停触摸事件 THEN `HOVER_ENTER/HOVER_MOVE/HOVER_EXIT/HOVER_CANCEL` 分别使用固定值 9/10/11/12 | 正常 |
| AC-1.3 | WHEN 动态 ArkTS 读取 `TouchEvent` 继承的基础字段 THEN `target/timestamp/source` 自 API 8、`sourceTool` 自 API 9、`deviceId` 自 API 12、`targetDisplayId` 自 API 15 按各自版本开放 | 边界 |
| AC-1.4 | WHEN 静态 ArkTS API 23+ 接收 `TouchEvent` THEN `type`、基础元数据、`touches` 和 `changedTouches` 使用静态类型契约提供 | 正常 |
| AC-1.5 | WHEN 输入来自触摸屏、鼠标、触控板或手写笔 THEN 顶层事件保留转换层提供的 `source`、`sourceTool`、`deviceId` 和 `targetDisplayId`，不根据回调类型改写来源 | 正常 |
| AC-1.6 | WHEN 应用跨动态和静态 ArkTS 直接比较 `SourceTool.MOUSE/TOUCHPAD/JOYSTICK` 数值 THEN 不得假定两套 canonical SDK 声明的数值相同，动态声明推导为 3/4/5，静态声明为 7/9/10 | 边界 |

### US-2: 处理多点触摸列表和触点标识

**作为** 多点交互开发者，
**我想要** 区分全部触点、变化触点及其稳定 ID，
**以便** 正确维护每个手指的状态而不混淆采样点或数组索引。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 非事件注入场景产生触摸事件 THEN `changedTouches` 使用按屏幕刷新率重采样的变化点，`touches` 使用设备上报频率的触点数据，两者坐标允许不同 | 边界 |
| AC-2.2 | WHEN 常规 `TouchEventActuator` 路径触发一次回调 THEN `changedTouches` 添加当前变化触点，`touches` 遍历当前 `lastPoint.pointers` 快照生成全部列表 | 正常 |
| AC-2.3 | WHEN 多点事件包含当前变化触点和其他触点 THEN 当前触点使用本次事件类型，其他触点在 `touches` 中统一标记为 `TouchType.Move` | 边界 |
| AC-2.4 | WHEN 上游 pointer 快照仍包含已抬起或取消的点 THEN `TouchEventActuator` 不根据 `isPressed` 二次过滤，`touches` 是否包含该点由上游快照决定 | 边界 |
| AC-2.5 | WHEN 应用读取 `TouchObject.id` THEN 返回输入触点的对外 finger ID；手写笔或鼠标内部 ID 转换不应直接作为公开触点 ID 暴露 | 正常 |
| AC-2.6 | WHEN SDK 事件路径提供空 `touches` 或空 `changedTouches` THEN 应用必须允许空数组且在索引访问前检查长度 | 边界 |
| AC-2.7 | WHEN 非插值 MOVE 事件带有历史批次 THEN 顶层基础元数据、变化点和全部触点以 `history.back()` 作为当前采样点，历史列表仍由原始 `point.history` 保存 | 边界 |

### US-3: 使用正确的坐标系统

**作为** 需要定位触点的应用开发者，
**我想要** 明确局部、窗口、屏幕和全局显示坐标的含义与版本，
**以便** 在组件变换、多窗口和多屏设备上使用正确位置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN ArkTS 读取 `x/y` THEN 返回事件生成时相对于事件响应组件的局部坐标快照，动态 API 7+ 和静态 API 23+ 以 vp 表达 | 正常 |
| AC-3.2 | WHEN ArkTS 读取 `windowX/windowY`、`displayX/displayY` 和 `globalDisplayX/globalDisplayY` THEN 分别映射内部窗口全局坐标、当前应用屏幕坐标和全局显示坐标，并按当前 density 转换为 vp | 正常 |
| AC-3.3 | WHEN 动态 ArkTS API 7~9 读取 `screenX/screenY` THEN 返回与窗口坐标相同的历史字段；WHEN API 10+ 编译新代码 THEN 该字段保持兼容但已废弃，应改用 `windowX/windowY` | 边界 |
| AC-3.4 | WHEN 静态 ArkTS API 23+ 使用 `TouchObject` THEN 不提供 `screenX/screenY`，只提供 `x/y`、`windowX/windowY`、`displayX/displayY`，API 26 增加全局显示和实时局部坐标 | 边界 |
| AC-3.5 | WHEN API 26+ 调用 `getCurrentLocalPosition()` 或 Native `GetCurrentLocalX/Y` THEN 使用保存的窗口坐标和节点当前变换重新计算局部坐标；节点已失效时回退到事件生成时的局部坐标 | 正常 |
| AC-3.6 | WHEN 节点变换在事件生成后、实时局部坐标查询前发生变化 THEN `x/y` 快照与 current-local 结果允许不同 | 边界 |
| AC-3.7 | WHEN Native 节点长度单位为 VP THEN Native 坐标按 density 转为 vp；WHEN 长度单位配置为 PX THEN Native 坐标保持 px | 边界 |

### US-4: 通过 Native C API 读取当前点和多点数据

**作为** Native ArkUI 开发者，
**我想要** 通过当前点和 `ByIndex` 接口读取触摸数据并识别错误，
**以便** 在 C/C++ 业务中安全处理多点事件。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN API 12+ 从输入事件类别的 `ArkUI_NodeEvent` 调用 `OH_ArkUI_NodeEvent_GetInputEvent` THEN 返回可供触摸 getter 使用的 `ArkUI_UIInputEvent`；非输入事件类别返回空指针 | 异常 |
| AC-4.2 | WHEN Native 调用无索引的触摸坐标或 pointer ID getter THEN 读取 `changedTouches.front()` 转换得到的 `actionTouchPoint`；该值不保证等于 `ByIndex(0)` | 正常 |
| AC-4.3 | WHEN Native 调用 `GetPointerCount` 和 `ByIndex` getter THEN 读取 `touchPointes[]` 中的全量触点；有效索引范围为 `[0, pointerCount-1]` | 正常 |
| AC-4.4 | WHEN ArkTS 触摸列表超过 10 个触点并转换为 Native 事件 THEN Native `touchPointes[]` 和 `touchPointSize` 仅暴露前 10 个触点 | 边界 |
| AC-4.5 | WHEN API 15+ 调用 `OH_ArkUI_PointerEvent_GetChangedPointerId(event, &pointerIndex)` THEN 输出参数写入变化触点的 finger ID，而不是 `touchPointes[]` 数组索引 | 边界 |
| AC-4.6 | WHEN Native 数值 getter 接收空事件、不支持的事件类型或越界索引 THEN 返回 `0` 或 `0.0f` 默认值；API 20+ 调用方通过 `OH_ArkUI_UIInputEvent_GetLatestStatus()` 区分有效零值与错误 | 异常 |
| AC-4.7 | WHEN `GetPointerCount` 接收未识别事件类型 THEN 返回 0，且当前实现可能保持 `NO_ERROR` 状态，调用方不得统一把 `pointerCount == 0` 解释为参数错误 | 边界 |
| AC-4.8 | WHEN API 12+ 读取触摸 action THEN Native `ARKUI_UIINPUTEVENT_ACTION_CANCEL/DOWN/MOVE/UP` 分别使用 0/1/2/3，与 ArkTS `TouchType` 数值顺序不同 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1, R-2 | 已有实现 | SDK 声明检查 + 枚举单测 | `interface/sdk-js/api/@internal/component/ets/enums.d.ts:620-714`；`enums.static.d.ets:467-547` |
| AC-1.3~AC-1.4 | R-3, R-4 | 已有实现 | SDK 版本注解检查 | `common.d.ts:9252-9297,9421-9481,10983-11025`；`common.static.d.ets:4520-4644,5536-5572` |
| AC-1.5~AC-1.6 | R-5, R-6 | 已有实现 | 转换层单测 + SDK 双通道比对 | `mmi_event_convertor.cpp:182-232,444-470`；动态 `common.d.ts:7595-7666`；静态 `common.static.d.ets:3353-3409` |
| AC-2.1~AC-2.4 | R-7~R-10 | 已有实现 | 多点事件单测 + 源码审查 | `common.d.ts:10983-11025`；`touch_event.cpp:109-126,234-281`；`mmi_event_convertor.cpp:209,235-249` |
| AC-2.5~AC-2.7 | R-11~R-13 | 已有实现 | ID/批量 MOVE 参数化单测 | `frameworks/core/event/touch_event.cpp:34-45,414-425`；`components_ng/event/touch_event.cpp:113-130,193,248` |
| AC-3.1~AC-3.4 | R-14~R-17 | 已有实现 | ArkTS 坐标集成测试 + SDK 检查 | `js_touch_function.cpp:28-50`；`common.d.ts:10668-10838`；`common.static.d.ets:5333-5413` |
| AC-3.5~AC-3.7 | R-18~R-20 | 已有实现 | 节点变换/单位参数化单测 | `touch_event.cpp:194-210,249-260`；`ui_input_event.cpp:1071-1084,1255-1268`；`node_common_modifier.cpp:10300-10310,11240-11255` |
| AC-4.1~AC-4.5 | R-21~R-25 | 已有实现 | Native C API 单测 | `event_converter.cpp:1360-1370`；`node_common_modifier.cpp:11267-11280,11370-11375`；`ui_input_event.cpp:2453-2467` |
| AC-4.6~AC-4.8 | R-26~R-28 | 已有实现 | Native 异常和枚举单测 | `ui_input_event.cpp:173-227,719-763,889-929`；`ui_input_event_impl.h:88-99` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ArkTS 接收普通触摸生命周期事件 | 使用 Down=0、Up=1、Move=2、Cancel=3 | 动态 API 7+；静态 API 23+ | AC-1.1 |
| R-2 | 行为 | 无障碍模式产生悬停触摸事件 | 使用 HOVER_ENTER=9、HOVER_MOVE=10、HOVER_EXIT=11、HOVER_CANCEL=12 | 动态 API 20+；静态 API 23+；4~8 不分配给本组枚举 | AC-1.2 |
| R-3 | 边界 | 动态 ArkTS 读取基础事件字段 | 按字段 `@since` 提供 target/timestamp/source、sourceTool、deviceId、targetDisplayId | 边界依次为 API 8、9、12、15 | AC-1.3 |
| R-4 | 行为 | 静态 ArkTS API 23+ 读取触摸事件 | 提供强类型 TouchEvent、TouchObject 和 BaseEvent 字段 | 静态接口不回填 API 7~22 的动态历史签名 | AC-1.4 |
| R-5 | 行为 | 输入转换层形成 TouchEvent | 将 deviceId、targetDisplayId、sourceType 和 sourceTool 复制到顶层事件信息 | 回调路径不得将 Mouse/Pen 改写为 TouchScreen/Finger | AC-1.5 |
| R-6 | 边界 | 应用跨动态和静态 SDK 比较 SourceTool 后三项 | 按各通道声明解释枚举值，并记录契约偏差 | 动态自动递增为 3/4/5；静态显式为 7/9/10 | AC-1.6 |
| R-7 | 行为 | 非注入触摸事件形成 ArkTS 数据 | changedTouches 使用屏幕刷新率重采样数据，touches 使用设备上报数据 | 两数组同一触点坐标不保证相等 | AC-2.1 |
| R-8 | 行为 | 常规 TouchEventActuator 触发回调 | 添加 1 个 changedTouch，并遍历 lastPoint.pointers 构造 touches | SDK 契约仍允许其他路径提供空数组 | AC-2.2, AC-2.6 |
| R-9 | 边界 | 多点快照含当前触点和其他触点 | 当前 originalId 匹配点使用事件类型，其余点使用 Move | 匹配基于 originalId，不基于数组位置 | AC-2.3 |
| R-10 | 边界 | 上游 pointer 快照包含 isPressed=false 的点 | Actuator 不二次过滤，按快照生成 touches | UP/CANCEL 时列表成员取决于输入层快照 | AC-2.4 |
| R-11 | 行为 | ArkTS 暴露 TouchObject.id | 使用 GetOriginalReCovertId 形成对外 finger ID | TouchPadIdChanged 开关影响 Pen/Mouse 内部 ID 恢复路径 | AC-2.5 |
| R-12 | 边界 | touches 或 changedTouches 长度为 0 | 返回空数组，调用方先检查长度再索引 | 不保证列表至少含一个元素 | AC-2.6 |
| R-13 | 边界 | 非插值事件 history 非空 | 使用 history.back() 形成本次顶层事件和触点列表 | history 列表仍保留原 point.history；历史点详细字段由 Feat-03 承接 | AC-2.7 |
| R-14 | 行为 | ArkTS 读取 x/y | 返回事件生成时节点局部坐标并换算为 vp | 坐标范围允许负值和超出组件边界 | AC-3.1 |
| R-15 | 行为 | ArkTS 读取 window/display/globalDisplay 坐标 | 分别从 globalLocation、screenLocation、globalDisplayLocation 取值并按 density 转 vp | globalDisplay 动态 API 20+；静态 API 26+ | AC-3.2 |
| R-16 | 边界 | 动态代码读取 screenX/screenY | 返回与 windowX/windowY 相同的 globalLocation 值 | API 7 开放、API 10 废弃；新代码使用 windowX/windowY | AC-3.3 |
| R-17 | 边界 | 静态 ArkTS 读取 TouchObject | 不暴露 screenX/screenY，使用静态声明的现代坐标字段 | 静态 API 23+；实时/全局显示扩展为 API 26 | AC-3.4 |
| R-18 | 行为 | API 26+ 查询 current-local | 用窗口坐标和节点当前变换重算；节点失效时返回保存的 local 坐标 | 结果以查询时节点变换为准 | AC-3.5 |
| R-19 | 边界 | 事件生成后节点变换发生变化 | x/y 快照不变化，current-local 可变化 | 两者不同不是精度错误 | AC-3.6 |
| R-20 | 边界 | Native 包装事件具有节点长度单位 | VP 单位除以 density；PX 单位保留原值 | 不得无条件把 Native 返回值解释为 vp | AC-3.7 |
| R-21 | 异常 | NodeEvent 不是输入事件类别 | GetInputEvent 返回 null | 有效输入事件类别返回 ArkUI_UIInputEvent | AC-4.1 |
| R-22 | 行为 | Native 调用无索引 getter | 读取 actionTouchPoint/changedPointerId | 当前变化点不保证等于 touchPointes[0] | AC-4.2 |
| R-23 | 行为 | Native 调用 PointerCount 或 ByIndex | 从 touchPointes[index] 读取全量触点 | index 必须满足 0≤index<pointerCount | AC-4.3 |
| R-24 | 边界 | 输入快照超过 10 个触点 | Native 转换在第 10 点停止并令 pointerCount=10 | 上限常量为 10 | AC-4.4 |
| R-25 | 边界 | API 15+ 获取 changed pointer | 输出变化触点 finger ID | 形参名 pointerIndex 不表示数组索引 | AC-4.5 |
| R-26 | 异常 | Native getter 接收 null、不支持类型或越界索引 | 返回 0/0.0f；API 20+ latest status 返回 PARAM_INVALID 或 INPUT_EVENT_TYPE_NOT_SUPPORT | 合法坐标 0 需结合状态判断 | AC-4.6 |
| R-27 | 边界 | GetPointerCount 接收未识别类型 | 返回 0，当前实现可能不写错误状态 | 0 也可表示有效空列表 | AC-4.7 |
| R-28 | 边界 | 比较 Native action 与 ArkTS TouchType | 分别使用 Native CANCEL/DOWN/MOVE/UP=0/1/2/3 和 ArkTS Down/Up/Move/Cancel=0/1/2/3 | 不得跨枚举按整数直接转换 | AC-4.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4, R-1~R-4 | SDK API 扫描 | 动态/静态类型、字段和 `@since` 完整性 |
| VM-2 | AC-1.5~AC-1.6, R-5~R-6 | 输入转换单测 + SDK 契约比对 | 来源元数据保留、SourceTool 数值偏差可见 |
| VM-3 | AC-2.1~AC-2.4, R-7~R-10 | NG 多点事件参数化单测 | 重采样差异、changed/touches 构造和非当前点 Move |
| VM-4 | AC-2.5~AC-2.7, R-11~R-13 | ID 恢复和批量 MOVE 单测 | 对外 ID、空数组、history.back 当前点选择 |
| VM-5 | AC-3.1~AC-3.4, R-14~R-17 | ArkTS 集成测试 | 坐标映射、density、screen 字段废弃和静态缺省 |
| VM-6 | AC-3.5~AC-3.7, R-18~R-20 | 节点变换/单位测试 | snapshot 与 current-local 差异、VP/PX 返回单位 |
| VM-7 | AC-4.1~AC-4.5, R-21~R-25 | Native C API 单测 | 当前点与 ByIndex 隔离、10 点上限、changed ID 语义 |
| VM-8 | AC-4.6~AC-4.8, R-26~R-28 | Native 异常单测 | 默认零值、latest status、PointerCount 特例和枚举顺序 |

## API 变更分析

> 本文为已有能力补录，不修改公开 API；下表列出纳入基线的既有 API 和字段族。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `TouchType` | Public | N/A | 枚举 | N/A | 动态 API 7 提供普通触摸类型，API 20 增加 HOVER 类型；静态 API 23 提供完整集合 | AC-1.1, AC-1.2 |
| `TouchEvent.type/touches/changedTouches` | Public | N/A | 属性 | N/A | 提供事件类型、全部触点和变化触点 | AC-1.4, AC-2.1~AC-2.7 |
| `TouchObject.id/x/y/windowX/windowY/displayX/displayY` | Public | N/A | 属性 | N/A | 提供触点 ID 和基本坐标 | AC-2.5, AC-3.1~AC-3.4 |
| `TouchObject.globalDisplayX/globalDisplayY/getCurrentLocalPosition()` | Public | N/A | 属性/Coordinate2D | N/A | 提供全局显示坐标和实时局部坐标 | AC-3.2, AC-3.5, AC-3.6 |
| `BaseEvent.source/sourceTool/deviceId/targetDisplayId/timestamp` | Public | N/A | 属性 | N/A | 提供基础输入来源和时间元数据 | AC-1.3~AC-1.6 |
| `OH_ArkUI_NodeEvent_GetInputEvent` | Public C API | nodeEvent | `ArkUI_UIInputEvent*` | null 表示不适用 | 从 Native Node 输入事件提取统一输入事件 | AC-4.1 |
| `OH_ArkUI_PointerEvent_GetPointerCount/GetPointerId` 及坐标 getter | Public C API | event | 数量、ID、坐标 | 默认 0/0.0f；API 20+ 查询 latest status | 读取当前变化触点 | AC-4.2, AC-4.6~AC-4.8 |
| `OH_ArkUI_PointerEvent_*ByIndex` | Public C API | event、pointerIndex | ID、坐标 | 默认 0/0.0f；越界状态错误 | 按数组索引读取全量触点 | AC-4.3, AC-4.4, AC-4.6 |
| `OH_ArkUI_PointerEvent_GetChangedPointerId` | Public C API | event、输出指针 | int32_t 状态码 | 0、401、类型不支持 | API 15+ 输出变化触点 ID | AC-4.5 |
| `OH_ArkUI_PointerEvent_GetCurrentLocalX/Y` 及 `ByIndex` | Public C API | event、可选 pointerIndex | float | 默认 0.0f + latest status | API 26+ 按当前节点变换重算局部坐标 | AC-3.5, AC-3.6 |
| `OH_ArkUI_UIInputEvent_GetLatestStatus` | Public C API | 无 | int32_t | 返回最近一次 getter 状态 | API 20+ 消除默认零值歧义 | AC-4.6, AC-4.7 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `TouchObject.screenX/screenY` | 废弃 | 动态 ArkTS API 10+ 的窗口坐标读取 | 使用 `windowX/windowY`；静态 ArkTS 不提供该字段 | AC-3.3, AC-3.4 |
| `TouchType.HOVER_*` | 变更 | 动态 ArkTS API 20+ 无障碍触摸类型 | 按固定值 9~12 处理，不假定枚举连续 | AC-1.2 |
| `SourceType.KEY/JOYSTICK` | 变更 | 动态 API 22、Native API 21 的来源扩展 | 使用符号枚举，不按旧最大值过滤 | AC-1.5 |

## 接口规格

### 接口定义

**`TouchEvent` / `TouchObject`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `interface TouchEvent extends BaseEvent { type; touches; changedTouches; }`；`interface TouchObject { type; id; coordinates; }` |
| 返回值 | 属性对象 — 当前事件与触点数据 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| touches | `TouchObject[]` | 是 | 空数组 | 允许为空；成员来自当前 pointer 快照 |
| changedTouches | `TouchObject[]` | 是 | 空数组 | 允许为空；常规 Actuator 路径为当前变化点，且可采用重采样坐标 |
| id | 动态 `number` / 静态 `int` | 是 | 无 | 表示 finger ID，不表示数组索引 |
| coordinates | `number` / `double` | 依版本 | 无 | ArkTS 坐标单位为 vp；`screenX/Y` 仅动态历史兼容 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多点、重采样、非当前点、空数组 | 见 Gherkin 场景 1~3 | AC-2.1~AC-2.7 |
| 2 | 窗口/屏幕/局部/实时局部坐标 | 见 Gherkin 场景 4~5 | AC-3.1~AC-3.7 |

**Native 当前点 getter**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_PointerEvent_GetPointerId/GetX/GetY/GetWindowX/GetWindowY/GetDisplayX/GetDisplayY(...)` |
| 返回值 | `int32_t` 或 `float` — 当前变化触点 ID/坐标 |
| 开放范围 | Public C API |
| 错误码 | 返回值为默认 0/0.0f；API 20+ 通过 latest status 获取错误 |
| 关联 AC | AC-3.7、AC-4.2、AC-4.6~AC-4.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 必须是支持的触摸输入事件 |
| lengthMetricUnit | 节点配置 | 否 | VP | VP 时换算，PX 时保持原值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效变化触点或参数错误 | 见 Gherkin 场景 6~7 | AC-4.2, AC-4.6~AC-4.8 |

**Native `ByIndex` getter 与状态接口**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_PointerEvent_GetPointerIdByIndex/GetXByIndex/...`；`OH_ArkUI_UIInputEvent_GetLatestStatus()` |
| 返回值 | ID/坐标/最近状态 |
| 开放范围 | Public C API |
| 错误码 | `ARKUI_ERROR_CODE_NO_ERROR`、`ARKUI_ERROR_CODE_PARAM_INVALID`、`ARKUI_ERROR_INPUT_EVENT_TYPE_NOT_SUPPORT` |
| 关联 AC | AC-4.3~AC-4.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 必须是支持的输入事件 |
| pointerIndex | `uint32_t` | 是 | 无 | `0 <= pointerIndex < pointerCount`，Native pointerCount 最大为 10 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效索引、越界索引或超过 10 点 | 见 Gherkin 场景 6~7 | AC-4.3~AC-4.7 |

## 兼容性声明

- **已有 API 行为变更:** 否；本文补录已有实现。动态 `screenX/screenY` 自 API 10 废弃但保持兼容，API 20/26 增加坐标和触摸类型能力。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态 ArkTS API 7；Native API 12；静态 ArkTS API 23。
- **API 版本号策略:** 逐字段保留 canonical SDK 的 `@since`、`@deprecated` 和 dynamic/static 标注；Native 按头文件 `since` 版本记录。

| API 版本 | 兼容性边界 | 证据 |
|----------|------------|------|
| API 7 | 动态 TouchType、TouchEvent、TouchObject、x/y、screenX/screenY | `common.d.ts:10668-10838,10983-11035`；`enums.d.ts:620-669` |
| API 8 | target/timestamp/source 加入 BaseEvent | `common.d.ts:9252-9297` |
| API 9 | sourceTool 加入 | `common.d.ts:9421-9430` |
| API 10 | display/window 坐标加入；screenX/screenY 废弃 | `common.d.ts:10730-10810` |
| API 12 | deviceId 和 Native 基础 getter 开放 | `common.d.ts:9453-9466`；`ui_input_event.h:437-687` |
| API 15 | targetDisplayId、Native changedPointerId 开放 | `common.d.ts:9468-9481`；`ui_input_event.h:831-841,1331-1338` |
| API 20 | HOVER 类型、globalDisplay 坐标、Native latest status/global display getter | `enums.d.ts:671-713`；`common.d.ts:10698-10728`；`ui_input_event.h:689-739,2150-2165` |
| API 21/22 | Native API 21、动态 API 22 增加 KEY/JOYSTICK SourceType | `ui_input_event.h:168-192`；`common.d.ts:7532-7592` |
| API 23 | 静态 ArkTS TouchEvent/TouchObject/TouchType 开放 | `common.static.d.ets:5333-5572`；`enums.static.d.ets:467-547` |
| API 26 | 动态/静态实时局部坐标和静态 globalDisplay；Native current-local getter | `common.d.ts:10903-10914`；`common.static.d.ets:5460-5488`；`ui_input_event.h:549-595` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SDK 契约优先 | 动态/静态字段、类型和版本以 canonical SDK 为外部契约，SourceTool 差异必须显式保留为风险 | AC-1.1~AC-1.6 |
| 输入快照不重构 | Actuator 按输入层提供的 pointers/history 生成列表，不额外推断活动触点 | AC-2.1~AC-2.7 |
| 坐标层级单向转换 | MMI 原始坐标经 TouchEvent、TouchLocationInfo 转换后再由 ArkTS/Native 桥接暴露 | AC-3.1~AC-3.7 |
| 当前点与列表隔离 | Native actionTouchPoint 和 touchPointes[] 保持独立，调用方不得用一个接口族推断另一个接口族 | AC-4.2~AC-4.5 |
| 现有错误语义保持 | 默认零值、latest status 和 PointerCount 特例按当前实现记录，不在规格补录中修改 | AC-4.6, AC-4.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | MOVE 批次继续使用 vsync 合并和历史末点作为当前采样，不新增同步 I/O | Pipeline/事件单测 | `pipeline_context.cpp:4026-4072,4798-4825`；`touch_event.cpp:113-130` |
| 功耗 | 不新增轮询、传感器订阅或后台任务 | 架构审查 | 触摸事件仅由输入回调驱动 |
| 内存 | Native 单事件触点数组上限为 10；ArkTS 列表生命周期限于事件对象 | 边界单测 | `ui_input_event.cpp:31-34`；`node_common_modifier.cpp:11267-11280` |
| 安全 | 不暴露原始平台对象所有权；Native getter 对空指针和类型错误返回默认值并记录状态 | C API 异常单测 | `ui_input_event_impl.h:88-99`；`ui_input_event.cpp:889-929` |
| 可靠性 | CANCEL、空数组、越界索引和节点失效均有可观察降级结果 | 参数化单测 | `enums.d.ts:659-669`；`node_common_modifier.cpp:10300-10310` |
| 可测试性 | 每个坐标系统、类型、版本和索引边界均可通过构造输入事件独立验证 | Host/C API 单测 | `test/unittest/interfaces/ui_input_event_test.cpp:241-267,894-955` |
| 自动化维测 | API 20+ Native getter 可通过 latest status 定位最近一次失败 | C API 状态单测 | `ui_input_event.h:2150-2165` |
| 定界定位 | ArkTS 契约差异、输入快照、Actuator 构造和 Native 转换分别保留层级证据 | 源码审查 | `common.d.ts`、`mmi_event_convertor.cpp`、`touch_event.cpp`、`ui_input_event.cpp` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 基础触摸和多点模型无额外差异 | 按 TouchType、列表和坐标通用规则执行 | 触摸屏集成测试 | `mmi_event_convertor.cpp:182-251` |
| 平板 | 多点数量由设备上报决定，Native 仍最多暴露 10 点 | 验证 1 点、2 点和 10 点边界 | 多点参数化测试 | `node_common_modifier.cpp:11267-11280` |
| 折叠屏 | 折叠切屏时仍按压可能产生 Cancel；屏幕/全局显示坐标随目标显示变化 | 验证 Cancel 和 targetDisplayId | 折叠状态集成测试 | `enums.d.ts:659-669`；`touch_event.cpp:187` |
| 桌面/二合一 | 鼠标左键可进入触摸管线但保留 Mouse 来源；触控板/鼠标 SourceTool 契约需按通道解释 | 验证 source/sourceTool 和单 pointer | 鼠标/触控板集成测试 | `pipeline_context.cpp:5175-5186`；`mouse_event.cpp:440-496` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | API 20+ TouchType 增加 HOVER_ENTER/MOVE/EXIT/CANCEL 9~12 | AC-1.2 |
| 大字体 | 否 | 触摸数据模型不依赖字体尺寸 | N/A |
| 深色模式 | 否 | 事件类型、坐标和来源不依赖颜色模式 | N/A |
| 多窗口/分屏 | 是 | window、display、globalDisplay 坐标含义不同，必须按目标坐标系统选择 | AC-3.2~AC-3.6 |
| 多用户 | 否 | 事件对象不持久化用户数据 | N/A |
| 版本升级 | 是 | 动态 API 7~26、静态 API 23~26 和 Native API 12~26 存在逐字段边界 | AC-1.2~AC-1.4、AC-3.3~AC-3.5 |
| 生态兼容 | 是 | screen 字段废弃、SourceTool 双通道数值差异和 Native 默认零值需显式处理 | AC-1.6、AC-3.3、AC-4.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 触摸事件与多点数据模型
  作为 ArkUI 多输入应用开发者
  我想要读取一致且可追溯的触摸类型、多点和坐标数据
  以便在 ArkTS 与 Native 通道正确维护触点状态

  Scenario: 重采样变化点与设备触点快照不同
    Given 非事件注入场景产生带重采样的 MOVE 事件
    When 回调同时读取 changedTouches 和 touches
    Then changedTouches 返回屏幕刷新率采样的变化点
    And touches 返回设备上报频率的触点快照
    And 同一触点在两个数组中的坐标允许不同

  Scenario: 多点列表标记当前变化触点
    Given 输入快照包含两个 originalId 不同的触点
    When 第二个触点产生 Up 事件
    Then changedTouches 的当前触点类型为 Up
    And touches 中 originalId 匹配的触点类型为 Up
    And touches 中其他触点类型为 Move

  Scenario: 触摸数组为空
    Given SDK 事件路径提供空 touches 或 changedTouches
    When 应用读取数组
    Then 返回长度为 0 的数组
    And 应用不得在未检查长度时访问索引 0

  Scenario: 动态历史窗口坐标迁移
    Given 动态 ArkTS 应用读取同一个 TouchObject
    When 同时读取 screenX 和 windowX
    Then 两者均来自窗口 globalLocation
    And API 10 起 screenX 标记为废弃

  Scenario: 局部坐标快照与实时坐标不同
    Given 触摸事件生成后节点发生位移或变换
    When API 26 查询 x 和 getCurrentLocalPosition
    Then x 保持事件生成时快照
    And getCurrentLocalPosition 按节点当前变换重新计算

  Scenario: Native 当前点与 ByIndex 列表独立
    Given 变化触点不是 touchPointes 数组的第 0 项
    When 分别调用无索引 getter 和 ByIndex(0)
    Then 无索引 getter 返回 actionTouchPoint
    And ByIndex(0) 返回 touchPointes[0]

  Scenario: Native 越界返回默认零值
    Given pointerCount 为 2
    When 调用 ByIndex(2) 坐标 getter
    Then getter 返回 0.0
    And API 20+ GetLatestStatus 返回 PARAM_INVALID
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：高级触点信息由 Feat-03、事件构造注入由 Feat-04 承接
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致，每个 AC 至少关联一条规则
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突五项检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "TouchEventActuator TouchEventInfo TouchLocationInfo touches changedTouches multi pointer coordinates"
  - repo: "openharmony/interface_sdk-js"
    query: "TouchEvent TouchObject TouchType SourceTool dynamic static since deprecated"
  - repo: "openharmony/arkui_ace_engine"
    query: "ArkUI_UIInputEvent PointerEvent ByIndex GetLatestStatus CurrentLocal"
```

**关键文档：** `specs/04-common-capability/04-common-events/01-touch-events/design.md`；`interface/sdk-js/api/@internal/component/ets/common.d.ts`；`interfaces/native/ui_input_event.h`
