# 架构设计

> ComponentUtils（04-11-01）功能域的架构设计文档，补录已有实现。本域聚焦按 id 查询组件几何信息（`getRectangleById`）；组件树 Inspector（03-07-02）与无感监听（04-11-02）为独立功能域，本文仅在边界处交叉引用。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-11-01 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | 待拆分（Feat-01 getRectangleById 几何查询为候选方向，本设计仅给出骨架） |
| 复杂度 | 一般 |
| 目标版本 | API 10 起（getRectangleById），ANI 静态路径随静态前端落地 |
| Owner | ArkUI SIG / 通用能力 |
| 状态 | Draft（design 补录；Feat 规格待补） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 开发者需要按组件 id 查询组件的几何信息（尺寸、本地/窗口/屏幕偏移、平移/缩放/旋转、4×4 transform 矩阵），用于自定义布局校验、对齐计算、自动化测试断言等 |
| 核心目标 | 经 `@ohos.arkui.componentUtils` 提供 `getRectangleById(id)`，返回 `ComponentInfo`（size/localOffset/windowOffset/screenOffset/translate/scale/rotate/transform[16]）；底层统一走 `NG::Inspector::GetRectangleById` |
| P0 AC | （骨架）`getRectangleById(id)` 命中节点并正确填充 `Rectangle`；动态渲染 host-parent 偏移、windowOffset、screenRect、transform 矩阵均准确；非法/空 id 行为符合 SDK 约定 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块/路径 | 当前职责 | 本 Feature 影响 |
|------|-----------|----------|-----------------|
| ace_engine | `interfaces/napi/kits/componentutils/js_component_utils.cpp` | NAPI 模块 `arkui.componentUtils`；`getRectangleById`、`getItemsInShapePath`（后者走防误触） | NAPI 桥接 |
| ace_engine | `interfaces/ets/ani/componentUtils/src/componentUtils.cpp` | ANI `getRectangleById` 绑定；`InitCachedClass`；调 `NG::Inspector::GetRectangleById` | ANI 桥接 |
| ace_engine | `interfaces/ets/ani/componentUtils/ets/@ohos.arkui.componentUtils.ets` | ArkTS 接口（Size/Offset/TranslateResult/ScaleResult/RotateResult/ComponentInfo）+ `*Inner` ctor | ANI ArkTS 层 |
| ace_engine | `frameworks/bridge/cj_frontend/interfaces/cj_ffi/cj_component_utils_ffi.cpp` | Cangjie FFI：`FFIOHOSAceFrameworkComponentUtilsGetById`，返回 `CComponentInfo`（malloc transform[16]） | CJ 桥接 |
| ace_engine | `frameworks/core/components_ng/base/inspector.h/.cpp` | `NG::Inspector::GetRectangleById`：经 `GetFrameNodeByKey` 取节点，填充 `Rectangle`（paintRect/windowOffset/screenRect/matrix4/scale/rotate/translate） | 核心实现 |
| ace_engine | `frameworks/bridge/common/utils/componentInfo.h` | `struct Rectangle` + `TranslateOption/ScaleOption/RotateOption`，三桥共用结果结构 | 共享结构 |
| ace_engine | `frameworks/bridge/js_frontend/frontend_delegate.cpp/.h` | `FrontendDelegate::GetRectangleById` → `NG::Inspector::GetRectangleById`（NAPI 间接） | 委托转发 |
| ace_engine | `frameworks/core/interfaces/native/implementation/global_scope_accessor.cpp` | `GetRectangleByIdImpl`（Arkoala 静态 accessor 表，当前为返回空的桩） | 静态前端（桩） |
| ace_engine | `interfaces/napi/kits/componentutils/js_mistouch_prevention.h` | `getItemsInShapePath` 后端 `MistouchPrevention`（非几何） | 仅边界标注 |
| sdk-js | `interface/sdk-js/api/@ohos.arkui.componentUtils.d.ts` | 动态 SDK 声明 | SDK 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| SDK d.ts/d.ets | `@ohos.arkui.componentUtils.d.ts` / `.ets` | 定义 getRectangleById 签名与 ComponentInfo 类型 | 存量分析 |
| NAPI 桥接 | `js_component_utils.cpp` | `JSGetRectangleById` → `delegate->GetRectangleById`；构造 napi 对象（size/localOffset/windowOffset/screenOffset/translate/scale/rotate/matrix4[16]） | 存量分析 |
| ANI 桥接 | `componentUtils.cpp` | `getRectangleById` native → `NG::Inspector::GetRectangleById`；构造 `ComponentInfoInner` | 存量分析 |
| CJ 桥接 | `cj_component_utils_ffi.cpp` | `FFIOHOSAceFrameworkComponentUtilsGetById` → `NG::Inspector::GetRectangleById`；返回 `CComponentInfo` | 存量分析 |
| 静态前端 accessor | `global_scope_accessor.cpp` | `GetRectangleByIdImpl`（桩，返回空 `Ark_ComponentInfo`） | 待实现 |
| Framework 核心 | `inspector.cpp` | `GetRectangleById`：`GetFrameNodeByKey(key, true)` → 填充 Rectangle（RenderContext transform/paintRect、GetOffsetRelativeToWindow、pipeline screenRect） | 存量分析 |

检查项：
- [x] 调用链每层覆盖（SDK → NAPI/ANI/CJ/静态 accessor → Framework 核心）
- [x] 与 03-07-02 Inspector、04-11-03 布局回调、04-11-02 observer 的边界已标注

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | componentUtils 经 Bridge → Framework 单向 | SDK → Bridge(NAPI/ANI/CJ) → `NG::Inspector::GetRectangleById` | 代码评审 |
| OH-ARCH-API-LEVEL | getRectangleById 为 Public API | @since 标注；V2 返回结构与 transform 矩阵随版本稳定 | API 评审/XTS |
| OH-ARCH-COMPONENT-BUILD | NAPI 模块 `arkui.componentUtils`；ANI `componentUtils_ani` + abc | 无新增 BUILD target | 构建验证 |
| OH-ARCH-ERROR-LOG | 非法 id 行为由 SDK 约定 | 空字符串不报错但无匹配（见单测 InspectorTestNg008） | 单测 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 组件树 Inspector | 不涉及 — 03-07-02 独立域；本域复用 `Inspector::GetRectangleById` 但只取几何子集 |
| 布局回调 | 不涉及 — 04-11-03 独立域 |
| 无感监听 | 不涉及 — 04-11-02 独立域 |
| FrameNode 对象方法 | 不涉及 — `getMeasuredSize/getGlobalPosition/getScaleBy` 等为 `FrameNode`/NDK 对象方法，非 componentUtils NAPI 导出 |
| getItemsInShapePath | 不涉及几何 — 该 API 走 `MistouchPrevention` 防误触 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|------------------|----------|------|
| ADR-1 | 几何后端：独立实现 vs 复用 Inspector | 复用 `NG::Inspector::GetRectangleById`，三桥（NAPI/ANI/CJ）共用 | A: 独立几何查询路径 | Inspector 已实现完整几何（paintRect/windowOffset/screenRect/transform），复用避免重复 | 骨架 |
| ADR-2 | 结果结构归属 | `frameworks/bridge/common/utils/componentInfo.h` 的 `Rectangle`，三桥共用 | A: 各桥独立定义 | 共用结构保证字段一致；CJ FFI 做 malloc 适配 | 兼容 |
| ADR-3 | 静态前端路径 | `global_scope_accessor.cpp` 的 `GetRectangleByIdImpl` 当前为桩（返回空） | A: 立即完整实现 | 静态前端（Arkoala）accessor 表待对齐；暂返回空，后续补 | 静态前端（已知缺口） |
| ADR-4 | NAPI 导出范围 | 仅 `getRectangleById` + `getItemsInShapePath`；其他几何 API（V2 等）归 FrameNode 体系 | A: 全量导出 | 历史/职责划分：componentUtils 为 id→几何入口，FrameNode 为节点对象方法 | API 矩阵 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| getRectangleById 几何查询 | 三桥统一经 `Inspector::GetRectangleById` 填充 Rectangle | 完整字段单位/坐标系（归 SDK/Feat） | 单测 |
| 共享结果结构 | `componentInfo.h` 的 Rectangle + Options | CJ malloc 细节 | 代码评审 |

### 骨架 Spec 拆分（候选）

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|------------|----|
| TASK-SKELETON-1 | Feat-01 getRectangleById 几何查询 | js_component_utils.cpp, componentUtils.cpp, cj_component_utils_ffi.cpp, inspector.cpp, componentInfo.h | AC-1.x（待 Feat 补齐） |

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| 静态前端 accessor 为桩 | 功能 | 中 — 静态范式 getRectangleById 暂返回空 | 标注已知缺口；后续补 `GetRectangleByIdImpl` | ArkUI SIG |
| `getItemsInShapePath` 易被误归几何 | 文档 | 低 | 本设计明确其属防误触 | ArkUI SIG |
| FrameNode 几何方法 vs componentUtils 易混淆 | 文档 | 低 | 边界标注区分 | ArkUI SIG |
| NAPI 模块无专属单测 | 质量 | 中 | 几何回归集中在 `inspector_test_ng.cpp`；建议补 NAPI 用例 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0 骨架 AC
- [x] 不涉及项已承接（Inspector/布局回调/observer/FrameNode 方法/getItemsInShapePath）
- [x] 涉及仓和模块职责清楚
- [x] 调用链层级分析完整
- [x] 适用架构规则已识别并形成设计结论
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner
- [ ] Feat 规格已补齐（本设计为 Draft，Feat 补齐后升 Baselined）

**结论:** Draft（design 已补录，Feat 规格待补）
