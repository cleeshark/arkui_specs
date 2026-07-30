# 特性规格

> Func-04-24-01-Feat-01 像素取整策略与布局渲染传播存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 像素取整策略与布局渲染传播 |
| 特性编号 | Func-04-24-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | Dynamic API 11+；UIContext API 18+；Static/C API 23/21+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 组件策略 | 补录四边 PixelRoundPolicy 与 component `pixelRound` |
| ADDED | 页面模式 | 补录 UIContext PixelRoundMode 与 Pipeline 存储 |
| ADDED | 几何传播 | 补录 LayoutWrapper、GeometryNode 和 Rosen 取整路径 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/24-layout-common-capability/01-pixel-rounding/design.md` | 已核对 |
| Dynamic SDK | `interface_sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Static SDK | `interface_sdk-js/api/arkui/component/common.static.d.ets` | 已核对 |
| UIContext SDK | `interface_sdk-js/api/@ohos.arkui.UIContext.d.ts` | 已核对 |
| Native API | `interfaces/native/node_attributes/layout.h` | 已核对 |

## 用户故事

### US-1: 为组件边界设置舍入策略

**作为** ArkUI 应用开发者
**我想要** 分别指定组件四个边缘的像素取整策略
**以便** 在浮点布局下控制边界落到像素网格的方式

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Dynamic/Static `pixelRound` 接收 Policy THEN start/top/end/bottom 策略写入当前组件的布局属性路径 | 正常 |
| AC-1.2 | WHEN Policy 未设置某个方向 THEN 该方向按默认最近整像素路径处理 | 边界 |
| AC-1.3 | WHEN Native 调用创建、set/get 四边 Policy 并最终 dispose THEN C API 对象按 `layout.h` 契约完成读写与释放 | 正常 |

### US-2: 选择页面级取整模式

**作为** 页面开发者
**我想要** 经 UIContext 设置或读取 PixelRoundMode
**以便** 当前 Pipeline 使用可预测的取整阶段

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `setPixelRoundMode(mode)` 接收 SDK 枚举 THEN 当前 Pipeline 保存该模式 | 正常 |
| AC-2.2 | WHEN 未显式设置模式或读取不存在的 Pipeline THEN 使用/返回 `PIXEL_ROUND_ON_LAYOUT_FINISH` 默认模式 | 恢复 |
| AC-2.3 | WHEN JS bridge 接收非数值或越界模式 THEN 保持既有忽略路径，不写入非法枚举 | 异常 |

### US-3: 将取整几何传播到绘制

**作为** 框架开发者
**我想要** 让取整后的 GeometryNode 矩形参与 paint rect
**以便** 布局和 Rosen 绘制使用一致的像素边界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Layout/Render 消费组件 Policy 与页面 Mode THEN Rosen 分别处理 left/top/right/bottom 并写入 PixelGridRound offset/size | 正常 |
| AC-3.2 | WHEN LayoutWrapper 更新 paint rect THEN 使用 PixelGridRoundRect 与 frame rect 的差值，而非忽略取整几何 | 正常 |
| AC-3.3 | WHEN 二合一设备与 force-floor 组合触发 THEN 保留当前实现的误差修正分支 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-3 | 已有实现 | SDK/C API/Modifier UT | `common.d.ts:25313-25322`; `layout.h:905-997` |
| AC-2.1~AC-2.3 | R-4~R-6 | 已有实现 | UIContext/JS bridge UT | `js_view_abstract.cpp:14065-14089`; `pipeline_base.h:1092-1099` |
| AC-3.1~AC-3.3 | R-7~R-9 | 已有实现 | Layout/Rosen UT | `layout_wrapper.cpp:314,383`; `rosen_render_context.cpp:4319-4468` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置 PixelRoundPolicy | 将四边策略写入组件属性路径 | 策略作用于组件边界 | AC-1.1 |
| R-2 | 边界 | 某方向未设置 | 使用该方向默认最近整像素逻辑 | 不用其他方向值替代 | AC-1.2 |
| R-3 | 恢复 | Native Policy 生命周期结束 | 由调用方 dispose Policy 对象 | 仅使用公开 C API | AC-1.3 |
| R-4 | 行为 | 合法 UIContext mode | Pipeline 保存模式 | 当前 UI 实例作用域 | AC-2.1 |
| R-5 | 恢复 | 未设置/无 Pipeline | 使用默认 ON_LAYOUT_FINISH | 默认值可观察 | AC-2.2 |
| R-6 | 异常 | 非数值或越界 mode | JS bridge 不写入非法值 | 保留现有忽略语义 | AC-2.3 |
| R-7 | 行为 | Render 接收几何和策略 | 按四边 round/ceil/floor 写回取整 offset/size | right/bottom 使用绝对边界 | AC-3.1 |
| R-8 | 行为 | LayoutWrapper 更新 paint rect | 叠加取整 rect 与 frame rect 的差值 | safe area 调整后仍使用该差值 | AC-3.2 |
| R-9 | 边界 | 二合一 + force-floor | 走当前误差补偿分支 | 不推广为全部设备规则 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | SDK/Modifier/C API UT | 四边策略与对象生命周期 |
| VM-2 | AC-2.1~AC-2.3 | UIContext/JS bridge UT | 默认值、合法和非法枚举 |
| VM-3 | AC-3.1~AC-3.3 | pixel_round/RenderContext UT | offset、size、paint rect、设备分支 |

## API 变更分析

### 新增 API

N/A；本次仅登记已有 Public API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**组件 `pixelRound`**

| 属性 | 值 |
|------|-----|
| 函数签名 | `pixelRound(value: PixelRoundPolicy)` |
| 返回值 | Dynamic 返回属性对象；Static 返回 `this` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.3 |

**UIContext 页面模式**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setPixelRoundMode(mode)` / `getPixelRoundMode()` |
| 返回值 | set 为 void；get 为 PixelRoundMode |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| Policy 四边 | PixelRoundCalcPolicy | 否 | NO_FORCE_ROUND | start/top/end/bottom 可分别指定 |
| mode | PixelRoundMode | 是 | ON_LAYOUT_FINISH | 必须为 SDK 枚举 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|----------|
| 1 | 设置单一边缘 force floor | 仅该边缘按强制 floor 计算 | AC-1.1 |
| 2 | 不设置 mode | Pipeline 使用默认模式 | AC-2.2 |
| 3 | 取整后更新 LayoutWrapper | paint rect 使用取整几何 | AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** Dynamic component API 11；UIContext API 18；Static API 23；C API 21。
- **API 版本号策略:** Dynamic、Static、UIContext 和 C API 按各自 `@since` 记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 策略/模式分离 | Policy 是组件属性；Mode 是 Pipeline 页面设置 | AC-1.1, AC-2.1 |
| 几何一致性 | paint rect 必须使用 PixelGridRound 与 frame 的差值 | AC-3.2 |
| SDK 权威 | 对外签名和版本以 SDK/C API 头文件为准 | AC-1.1, AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 取整只在既有布局/渲染流程传播，不增加后台任务 | Trace | Layout/Rosen 路径 |
| 可靠性 | 非法 mode 不污染 Pipeline 枚举 | JS bridge UT | `js_view_abstract.cpp:14065-14089` |
| 可测试性 | 四边策略、模式和 paint rect 均可独立断言 | UT | pixel_round 测试 |
| 定界定位 | API/属性/Layout/Render 分层可追踪 | 代码审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 默认四边计算 | 不设置 force-floor 特例 | Render UT | Rosen |
| 平板 | 同一策略与模式 | 几何按当前 scale 传播 | Render UT | Rosen |
| 二合一 | force-floor 有误差补偿分支 | 仅该设备路径适用 | 参数化 UT | `rosen_render_context.cpp:4408-4468` |

## 全局特性影响

| 特性 | 是否适用 | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变语义树 | VM-1 |
| 大字体 | 是 | 字体导致的浮点几何仍经取整传播 | AC-3.2 |
| 深色模式 | 否 | 无颜色语义 | VM-1 |
| 多窗口/分屏 | 是 | 每个 Pipeline 保有自己的 mode | AC-2.1 |
| 版本升级 | 是 | 通道 since 不同 | VM-1, VM-2 |
| 生态兼容 | 是 | 保留 C API Policy 对象边界 | AC-1.3 |

## 行为场景（可选，Gherkin）

Feature: 像素取整几何传播
  作为 ArkUI 应用开发者
  我想要设置组件策略和页面模式
  以便绘制使用可预测的像素边界

  Scenario: 四边策略进入绘制矩形
    Given 一个具有浮点 frame rect 的组件
    When 设置 PixelRoundPolicy 并完成布局
    Then GeometryNode 保存取整后的 offset 和 size
    And paint rect 使用该取整几何

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 组件策略、页面模式、Native Policy 和渲染传播边界明确
- [x] 未将二合一设备分支泛化为通用算法
- [x] AC、规则与 VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "pixelRound PixelRoundPolicy PixelRoundMode LayoutWrapper RosenRenderContext"
```

**关键文档：** `docs/kb/capabilities/pixel-rounding.md`
