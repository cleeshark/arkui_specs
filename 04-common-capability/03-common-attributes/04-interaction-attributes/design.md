# 架构设计

> 通用交互属性把鼠标光标、悬浮效果、触摸热区、触摸控制、事件独占和禁用控制分派到 NG 事件 Hub 和 UIContext；本文为已有实现补录的共享基线。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-03-04 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01、Feat-02、Feat-03 |
| 复杂度 | 标准 |
| 目标版本 | API 7 起，持续扩展至 API 24/26 |
| Owner | ArkUI SIG |
| 状态 | Baselined（已有实现补录） |

## 需求基线

| 项 | 补充说明 |
|----|----------|
| 通用交互属性 | 本 FuncID 按检视范围补录鼠标光标、悬浮效果、触摸热区、触摸控制、事件独占和禁用控制。 |
| 可用性 | `enabled` 必须同步事件处理与焦点可用性。 |
| 兼容性 | 动态、静态 ArkTS 的声明和 API 版本以 SDK 为准，规格显式保留差异。 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 补充架构说明 |
|------|----------------|
| ace_engine | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp` 提供动态 ArkTS 桥接（悬浮回调、无障碍悬浮透明回调）。 |
| ace_engine | `frameworks/core/components_ng/base/view_abstract.cpp` 统一写入 GestureEventHub、EventHub；`UIContext.cursorControl` 提供鼠标光标控制。 |
| interface_sdk-js | `common.d.ts` 与 `common.static.d.ets` 是外部 API 契约（含光标、悬浮、热区、触摸控制和禁用）。 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| SDK | `common.d.ts:6616-6655,18892-19015,20146-20281,22281-22430,24522-24534` | 动态 API 与 since 声明 | 无修改（规格补录） |
| SDK | `common.static.d.ets:3256-3273,11592-11625,12072-12165` | 静态 API 声明 | 无修改（规格补录） |
| 动态桥 | `arkts_native_common_bridge.cpp:5262-5273,8932-9313` | 解析 ArkTS 回调并调用 ViewAbstract | 无修改（规格补录） |
| 通用属性 | `view_abstract.cpp:3199-3267,3220-3229,3557-3583,9850-9861,9900-9909` | 将光标、悬浮、热区、触摸控制和 enabled 分派到 Hub | 无修改（规格补录） |
| 事件/手势 | `gesture_event_hub.cpp:781-1352,1254-1256,1780-1813`、`event_hub.cpp:1083-1089` | 保存悬浮回调、触摸/独占状态和可用状态 | 无修改（规格补录） |

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 交互 API 跨 SDK、桥接和 NG Hub | 仅由桥接向 ViewAbstract 下行，不从 Hub 反向依赖前端 | 代码审查 |
| OH-ARCH-API-LEVEL | 公共 API 存在动态/静态及 since 差异 | 以 `common*.d.ts` 为契约，源实现差异写入风险 | SDK 对照 |
| OH-ARCH-ERROR-LOG | 回调和配置为可选 | 无回调时清除或不注册，空 Hub 早返回 | 单测/代码审查 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 命中测试与手势仲裁 | 由 `04-04-06` 覆盖；本域不重复定义。 |
| 键盘与外设输入 | 由相邻输入事件功能域承接；本 FuncID 不再以键盘与外设回调作为 Feat 拆分项。 |
| 拖拽、弹窗、模态 | 分别由 `04-04-07`、`04-03-05`、`04-03-06` 覆盖。 |
| 构建与部件 | 无变更，使用现有 ace_engine source set。 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|------------------|----------|------|
| ADR-1 | 交互属性拆分 | Feat-01 覆盖鼠标光标和悬浮效果，Feat-02 覆盖热区、触摸控制与事件独占，Feat-03 覆盖禁用控制 | 按键盘/外设回调拆分 | 对齐检视确认的通用交互属性范围 | 全部 Feat |
| ADR-2 | enabled 的作用面 | 同时设置 EventHub 和 FocusHub | 仅禁用点击；仅禁用焦点 | `ViewAbstract::SetEnabled` 已同步两者 | Feat-03 |
| ADR-3 | 前端契约冲突 | 动态/静态 API 分表声明 | 将两者抽象为同一签名 | SDK 声明实际存在重载与可空返回差异 | 全部 Feat |
| ADR-4 | 规格边界 | 引用相邻域、不复制命中/拖拽语义 | 合并所有交互 API | 保持 FuncID 职责单一 | 全部 Feat |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| 鼠标光标与悬浮效果 | 光标控制、悬浮回调和效果配置 | 命中测试算法 | SDK/源码审查 |
| 触摸热区、控制与独占 | responseRegion、touchable、monopolizeEvents | 手势识别器内部算法 | SDK/源码审查 |
| 禁用控制与反馈 | enabled 同步事件/焦点和点击反馈 | 组件绘制实现 | SDK/源码审查 |

### 骨架 Spec 拆分

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|--------------|----|
| TASK-SKELETON-1 | 鼠标光标和悬浮效果 | `common.d.ts`、`view_abstract.cpp` | Feat-01 AC |
| TASK-SKELETON-2 | 触摸热区、触摸控制和事件独占 | `common.d.ts`、`view_abstract.cpp` | Feat-02 AC |
| TASK-SKELETON-3 | 禁用控制和点击反馈 | `common.d.ts`、`event_hub.cpp` | Feat-03 AC |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|--------------|------|
| TASK-1 | 鼠标光标与悬浮效果规格 | Feat-01 | 无 |
| TASK-2 | 触摸热区、触摸控制与事件独占规格 | Feat-02 | ADR-1 |
| TASK-3 | 禁用控制与点击反馈规格 | Feat-03 | ADR-2 |

## API 签名、Kit 与权限

### 新增 API

| API 签名 | 类型 | Kit | d.ts 位置 | 权限要求 | SysCap |
|----------|------|-----|-----------|----------|--------|
| `UIContext.cursorControl.setCursor/restoreDefault` | Public | ArkUI | `common.d.ts:6616-6655`; `common.static.d.ets:3256-3273` | 无 | ArkUI |
| `CommonMethod.onHover/onHoverMove/hoverEffect` | Public | ArkUI | `common.d.ts:20146-20281` | 无 | ArkUI |
| `CommonMethod.onAccessibilityHover/onAccessibilityHoverTransparent` | Public | ArkUI | `common.d.ts:20226-20254` | 无 | ArkUI |
| `CommonMethod.responseRegion/responseRegionList` | Public | ArkUI | `common.d.ts:18892-18940`; `common.static.d.ets:11592-11625` | 无 | ArkUI |
| `CommonMethod.touchable/monopolizeEvents` | Public | ArkUI | `common.d.ts:18998-19015,24522-24534` | 无 | ArkUI |
| `CommonMethod.enabled/clickEffect/enableClickSoundEffect` | Public | ArkUI | `common.d.ts:22281-22430` | 无 | ArkUI |

### 变更/废弃 API

| 原有 API | 变更类型 | 新 API | 迁移说明 |
|----------|----------|--------|----------|
| `CommonMethod.touchable` | SDK 建议替代 | `hitTestBehavior` | SDK 注释建议使用 `hitTestBehavior` 替代；本规格仍记录现有实现路径。 |
| `onHoverMove` | 版本扩展 | API 15 才可用 | 低版本使用 `onHover` 的进入/离开通知。 |
| `onAccessibilityHoverTransparent` | 版本扩展 | API 20 才可用 | 低版本使用 `onAccessibilityHover`。 |

## 构建系统影响

### BUILD.gn 变更

无变更，均为既有实现补录。

### bundle.json 变更

无变更。

## 可选设计扩展

### 架构图

```mermaid
graph TB
    SDK["CommonMethod / UIContext 动态/静态 SDK"] --> Bridge["ArkTS / JS Bridge"]
    Bridge --> View["ViewAbstract / ViewAbstractModelNG"]
    View --> Gesture["GestureEventHub\n悬浮回调、触摸控制、事件独占"]
    View --> UIContext["UIContext.cursorControl\n鼠标光标控制"]
    View --> Event["EventHub\nenabled 禁用控制"]
```

### 数据流/控制流

| 步骤 | 调用方 | 被调用方 | 数据/接口 | 说明 |
|------|--------|----------|-----------|------|
| 1 | ArkTS | CommonBridge | 回调或配置值 | 解析 API 参数。 |
| 2 | Bridge | ViewAbstract / UIContext | `SetOn*` / `SetResponseRegion` / `SetTouchable` / `SetEnabled` / `cursorControl.setCursor` | 分派到对应 Hub 或 UIContext。 |
| 3 | ViewAbstract | GestureEventHub/EventHub | 回调、布尔值、区域值 | Hub 保存供后续系统事件分发。 |

### 数据模型设计

```typescript
type HoverConfig = { onHover?: Callback<HoverEvent>; hoverEffect?: HoverEffect }
type TouchConfig = { responseRegion?: Rectangle | Array<Rectangle>; touchable?: boolean; monopolizeEvents?: boolean }
type DisableConfig = { enabled?: boolean; clickEffect?: ClickEffect; enableClickSoundEffect?: boolean }
```

### 测试性设计

| 测试层级 | 测试目标 | Mock 策略 | 验证方式 |
|----------|----------|-----------|----------|
| SDK 对照 | 光标控制、悬浮/热区/触摸控制/禁用的重载和 since 差异 | 不适用 | 声明审查 |
| 单元测试 | Hub 保存、UIContext 光标绑定及 enabled 同步 | FrameNode/Hub/UIContext mock | 既有 `view_abstract_*` 测试 |

## 详细设计

### 鼠标光标控制（Feat-01）

`UIContext.cursorControl.setCursor/restoreDefault` 与当前 `UIContext` 绑定，光标控制不跨 UIContext 生效；SDK 声明见 `common.d.ts:6616-6655`、`common.static.d.ets:3256-3273`。

### 悬浮回调与悬浮效果（Feat-01）

`ViewAbstract::SetOnHover` 将回调交给 GestureEventHub；动态桥在 `arkts_native_common_bridge.cpp:8932-9313` 建立 ArkTS 包装回调。`hoverEffect` 和无障碍悬浮回调（`onAccessibilityHover`、`onAccessibilityHoverTransparent`）也经既有事件路径配置。

### 触摸热区、触摸控制与事件独占（Feat-02）

`ViewAbstract::SetResponseRegion/SetResponseRegionList` 配置触摸响应热区，`SetTouchable`/`SetMonopolizeEvents` 将触摸控制与事件独占标志写入 GestureEventHub；命中测试与手势裁决不在本 Feat 定义，见 `gesture_event_hub.cpp:1254-1256,1780-1813`。

### 禁用控制与点击反馈（Feat-03）

`SetEnabled` 先写 EventHub 再写 FocusHub，见 `view_abstract.cpp:3255-3267`；点击反馈和声音由通用桥及 FrameNode 路径处理。禁用状态同时作用于事件与焦点路径。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| 动态/静态签名不对称 | API | 中 | 各 Feat 逐 API 标注而不推断统一语义 | ArkUI SIG |
| 相邻域重复覆盖 | 架构 | 中 | 规格采用边界引用 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0/P1 AC
- [x] 不涉及项已有结论
- [x] 涉及仓和模块职责清晰
- [x] 调用链层级分析完整
- [x] 适用架构规则已形成结论
- [x] 分层和子系统边界合规
- [x] API 签名、权限与兼容性已声明
- [x] BUILD.gn/bundle.json 影响明确
- [x] 后续 Task 拆分明确
- [x] 关键设计决策有理由和影响
- [x] 风险有 Owner

**结论:** 通过（已有实现补录）
