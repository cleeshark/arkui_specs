# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Scroll 缩放与二维自由滚动 |
| 特性编号 | Func-05-03-07-Feat-07 |
| 优先级 | P2 |
| 目标版本 | API 20 ~ 26+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖 maxZoomScale/minZoomScale/zoomScale(支持 `!!` 双向绑定)/enableBouncesZoom/onDidZoom/onZoomStart/onZoomStop、ScrollDirection.FREE 二维自由滚动及 C-API。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/07-scroll/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll.d.ts` |
| ZoomController | `frameworks/core/components_ng/pattern/scroll/zoom_controller.h/.cpp` |
| FreeScrollController | `frameworks/core/components_ng/pattern/scroll/free_scroll_controller.h/.cpp` |
| ScrollBar2D | `frameworks/core/components_ng/pattern/scroll/inner/scroll_bar_2d.h/.cpp` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll/scroll_pattern.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 缩放范围与捏合缩放

作为**应用开发者**，我想要**用 maxZoomScale/minZoomScale/zoomScale 控制缩放范围与当前缩放**，以便**支持内容缩放查看**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `maxZoomScale(scale)`（@since 20） THEN 最大缩放比生效（ZoomController） | 正常 |
| AC-1.2 | WHEN 设置 `minZoomScale(scale)`（@since 20） THEN 最小缩放比生效 | 正常 |
| AC-1.3 | WHEN 设置 `zoomScale(scale)`（@since 20，支持 `!!` 双向绑定） THEN 当前缩放比更新，双向回写 | 正常 |
| AC-1.4 | WHEN 捏合手势 THEN ZoomController::ProcessZoomScale/UpdatePinchGesture 处理（`scroll_pattern.cpp`） | 正常 |
| AC-1.5 | WHEN 设置 `enableBouncesZoom(enable)`（@since 20） THEN 越界缩放回弹 | 正常 |
| AC-1.6 | WHEN zoomScale 超过 maxZoomScale THEN 钳位到 maxZoomScale | 边界 |
| AC-1.7 | WHEN zoomScale 低于 minZoomScale THEN 钳位到 minZoomScale | 边界 |

### US-2: 缩放事件

作为**应用开发者**，我想要**用 onDidZoom/onZoomStart/onZoomStop 感知缩放阶段**，以便**联动 UI**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 缩放中 THEN `onDidZoom(scale)` 触发（@since 20，ScrollOnDidZoomCallback） | 正常 |
| AC-2.2 | WHEN 缩放将开始 THEN `onZoomStart` 触发（@since 20） | 正常 |
| AC-2.3 | WHEN 缩放已停止 THEN `onZoomStop` 触发（@since 20） | 正常 |

### US-3: 二维自由滚动

作为**应用开发者**，我想要**用 scrollable(FREE) 启用二维自由滚动**，以便**大面积内容漫游**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `scrollable(ScrollDirection.FREE)`（@since 20） THEN 启用 FreeScrollController，偏移为 2D（X+Y） | 正常 |
| AC-3.2 | WHEN FREE 模式 CreateLayoutAlgorithm THEN 用 freeScroll_ 2D offset 构造（`scroll_pattern.h:69-72`） | 正常 |
| AC-3.3 | WHEN FREE 模式 THEN Get2DScrollBar 返回 ScrollBar2D，显示二维滚动条 | 正常 |
| AC-3.4 | WHEN FreeScrollBy/Page/ToEdge/To 调用 THEN 2D 偏移更新（`scroll_pattern.cpp`） | 正常 |
| AC-3.5 | WHEN GetFreeScrollOffset 查询 THEN 返回 2D 偏移 | 正常 |
| AC-3.6 | WHEN C-API `NODE_SCROLL_MAX_ZOOM_SCALE/MIN_ZOOM_SCALE/ZOOM_SCALE/ENABLE_BOUNCES_ZOOM` THEN 经 node_modifier 写 ZoomController | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-7 | 单元测试：maxZoomScale | `scroll.d.ts:1390` |
| AC-1.2 | R-1 | TASK-SKELETON-7 | 单元测试：minZoomScale | `scroll.d.ts:1404` |
| AC-1.3 | R-2 | TASK-SKELETON-7 | 单元测试：zoomScale 双向 | `scroll.d.ts:1419` |
| AC-1.4 | R-3 | TASK-SKELETON-7 | 单元测试：捏合 | `zoom_controller.cpp` |
| AC-1.5 | R-4 | TASK-SKELETON-7 | 单元测试：bounces | `scroll.d.ts:1432` |
| AC-1.6 | R-5 | TASK-SKELETON-7 | 单元测试：上界钳位 | `zoom_controller.cpp` |
| AC-1.7 | R-5 | TASK-SKELETON-7 | 单元测试：下界钳位 | `zoom_controller.cpp` |
| AC-2.1 | R-6 | TASK-SKELETON-7 | 单元测试：onDidZoom | `scroll.d.ts:1675` |
| AC-2.2 | R-6 | TASK-SKELETON-7 | 单元测试：onZoomStart | `scroll.d.ts:1687` |
| AC-2.3 | R-6 | TASK-SKELETON-7 | 单元测试：onZoomStop | `scroll.d.ts:1699` |
| AC-3.1 | R-7 | TASK-SKELETON-7 | 单元测试：FREE 启用 | `scroll.d.ts:133` |
| AC-3.2 | R-8 | TASK-SKELETON-7 | 单元测试：2D 算法 | `scroll_pattern.h:69-72` |
| AC-3.3 | R-9 | TASK-SKELETON-7 | 单元测试：2D 滚动条 | `inner/scroll_bar_2d.h` |
| AC-3.4 | R-10 | TASK-SKELETON-7 | 单元测试：2D 偏移方法 | `scroll_pattern.cpp` FreeScrollBy |
| AC-3.5 | R-10 | TASK-SKELETON-7 | 单元测试：GetFreeScrollOffset | `scroll_pattern.cpp` |
| AC-3.6 | R-11 | TASK-SKELETON-7 | 单元测试：C-API | `node_scroll_modifier.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | maxZoomScale/minZoomScale | 缩放范围生效 | @since 20 | AC-1.1, AC-1.2 |
| R-2 | 行为 | zoomScale(scale) | 当前缩放更新，支持 `!!` 双向回写 | @since 20 | AC-1.3 |
| R-3 | 行为 | 捏合手势 | ProcessZoomScale/UpdatePinchGesture | ZoomController | AC-1.4 |
| R-4 | 行为 | enableBouncesZoom | 越界缩放回弹 | @since 20 | AC-1.5 |
| R-5 | 边界 | zoomScale 超 max/min | 钳位到上下界 | — | AC-1.6, AC-1.7 |
| R-6 | 行为 | onDidZoom/onZoomStart/onZoomStop | 缩放阶段回调 | @since 20 | AC-2.1~2.3 |
| R-7 | 行为 | scrollable(FREE) | 启用 FreeScrollController 2D | @since 20 | AC-3.1 |
| R-8 | 行为 | FREE CreateLayoutAlgorithm | 用 freeScroll_ 2D offset | `scroll_pattern.h:69-72` | AC-3.2 |
| R-9 | 行为 | FREE 模式 | Get2DScrollBar 返回 ScrollBar2D | inner/scroll_bar_2d | AC-3.3 |
| R-10 | 行为 | FreeScrollBy/Page/ToEdge/To | 2D 偏移更新 | `scroll_pattern.cpp` | AC-3.4, AC-3.5 |
| R-11 | 行为 | C-API NODE_SCROLL_MAX/MIN/ZOOM_SCALE/ENABLE_BOUNCES_ZOOM | node_modifier 写 ZoomController | — | AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-5 缩放范围 | 单元测试 | max/min/zoom/bounces/钳位 |
| VM-2 | R-6 缩放事件 | 单元测试 | did/start/stop |
| VM-3 | R-7~R-11 自由滚动与 C-API | 单元测试 | FREE/2D/2D滚动条/C-API |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `maxZoomScale(scale)` | Public（@since 20） | `number` | `ScrollAttribute` | 无 | 最大缩放比 | AC-1.1 |
| `minZoomScale(scale)` | Public（@since 20） | `number` | `ScrollAttribute` | 无 | 最小缩放比 | AC-1.2 |
| `zoomScale(scale)` | Public（@since 20，支持 `!!`） | `number` | `ScrollAttribute` | 无 | 当前缩放比双向 | AC-1.3 |
| `enableBouncesZoom(enable)` | Public（@since 20） | `boolean` | `ScrollAttribute` | 无 | 越界回弹 | AC-1.5 |
| `onDidZoom(event)` | Public（@since 20） | `ScrollOnDidZoomCallback` | `ScrollAttribute` | 无 | 缩放回调 | AC-2.1 |
| `onZoomStart/onZoomStop(event)` | Public（@since 20） | `VoidCallback` | `ScrollAttribute` | 无 | 缩放起停 | AC-2.2, AC-2.3 |
| `ScrollDirection.FREE` | Public（@since 20） | 枚举值 4 | — | 无 | 2D 自由滚动 | AC-3.1 |
| C-API `NODE_SCROLL_MAX_ZOOM_SCALE/MIN_ZOOM_SCALE/ZOOM_SCALE/ENABLE_BOUNCES_ZOOM` | Public | 属性枚举 | — | 无 | NDK 缩放 | AC-3.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `ScrollDirection.Free`（小写） | 废弃 since 9 | 旧小写 Free | 迁移至 `FREE`（@since 20） | AC-3.1 |

## 接口规格

### 接口定义

**zoomScale(scale: number)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollAttribute::zoomScale(scale: number): ScrollAttribute` |
| 返回值 | `ScrollAttribute` |
| 开放范围 | Public（@since 20，支持 `!!` 双向绑定） |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| scale | `number` | 是 | — | 钳位到 [minZoomScale, maxZoomScale]；支持 `!!` 回写 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 scale | ZoomController 更新 | AC-1.3 |
| 2 | 超 max | 钳位 max | AC-1.6 |
| 3 | 低于 min | 钳位 min | AC-1.7 |
| 4 | 捏合手势 | ProcessZoomScale | AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（FREE 弃用迁移见 Feat-01）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 全量 @since 20
- **API 版本号策略:** 缩放族与 FREE 均 @since 20

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ZoomController 与 FreeScrollController 分离 | 关注点分离 | AC-1.x, AC-3.x |
| FREE 启用 ScrollBar2D 与 2D 算法 | 二维专属 | AC-3.2, AC-3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 缩放/2D 滚动单帧 | 单元测试 | `zoom_controller.cpp` |
| 内存 | 2D 滚动条与自由控制器轻量 | 代码审查 | `free_scroll_controller.h` |
| 可测试性 | 缩放/FREE 可单测 | 单元测试 | TASK-SKELETON-7 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准捏合 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 无差异 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 无差异 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 缩放族与 FREE @since 20 | AC-1.x~3.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（缩放/FREE；分页在 Feat-06）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ZoomController ProcessZoomScale/UpdatePinchGesture 与 FreeScrollController 2D 偏移及 ScrollBar2D"
```

**关键文档:** `scroll.d.ts`、`zoom_controller.h/.cpp`、`free_scroll_controller.h/.cpp`、`inner/scroll_bar_2d.h`、`design.md`
