# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ScrollBar 核心构造与绑定 |
| 特性编号 | Func-05-03-03-Feat-01 |
| 优先级 | P1 |
| 目标版本 | API 8 ~ 11+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/03-scroll-bar/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll_bar.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll_bar/scroll_bar_pattern.cpp` |
| Model Source | `frameworks/core/components_ng/pattern/scroll_bar/scroll_bar_model_ng.cpp` |
| JSView Source | `frameworks/bridge/declarative_frontend/jsview/scroll_bar/js_scroll_bar.cpp` |
| Proxy Source | `frameworks/core/components_ng/pattern/scroll_bar/proxy/scroll_bar_proxy.h` |
| C-API Modifier | `frameworks/core/interfaces/native/node/node_scroll_bar_modifier.cpp` |
| Native Header | `interfaces/native/native_node.h` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 创建 ScrollBar 并绑定可滚动宿主

作为**应用开发者**，我想要**通过 `ScrollBar({scroller, direction, state})` 创建独立滚动条并与 Scroll/List/Grid/WaterFlow 的 Scroller 绑定**，以便**自定义滚动条位置与外观，独立于宿主内建滚动条**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 `ScrollBar({scroller: myScroller})` 且 myScroller 已与某 Scroll 绑定 THEN ScrollBar 创建成功，经 `ScrollBarProxy::RegisterScrollBar(pattern)` 登记本 ScrollBarPattern 与该 Scroll 宿主配对（`scroll_bar_model_ng.cpp:76-77`） | 正常 |
| AC-1.2 | WHEN options.scroller 为合法 JSScroller 且其 ScrollBarProxy 为空 THEN `ScrollBarModelNG::GetScrollBarProxy` 新建 `NG::ScrollBarProxy` 并回填 `jsScroller->SetScrollBarProxy(proxy)`（`scroll_bar_model_ng.cpp:36-44`、`js_scroll_bar.cpp:95-96`） | 正常 |
| AC-1.3 | WHEN 传入 options 对象但 scroller 字段缺失或非对象 THEN `proxyFlag=false`，ScrollBar 仍创建但不登记 Proxy，后续依赖 Proxy 的能力（如 `enableNestedScroll`）为 no-op | 边界 |
| AC-1.4 | WHEN 不传任何参数（`ScrollBar()`） THEN `info.Length()<=0`，`ScrollBarModel::Create(proxy,null,false,-1,-1)` 被调用，direction/state 均为 -1 走默认值 | 边界 |
| AC-1.5 | WHEN 同一 scroller 绑定多个 ScrollBar THEN 每个 ScrollBarPattern 均被同一 ScrollBarProxy 登记，宿主滚动时多 ScrollBar 同步更新 | 正常 |

### US-2: 配置滚动条方向

作为**应用开发者**，我想要**通过 `direction` 指定滚动条纵向或横向**，以便**匹配横向滚动容器**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `direction: ScrollBarDirection.Vertical`（0） THEN LayoutProperty `Axis` 写为 `Axis::VERTICAL`（`scroll_bar_model_ng.cpp:88`） | 正常 |
| AC-2.2 | WHEN 设置 `direction: ScrollBarDirection.Horizontal`（1） THEN LayoutProperty `Axis` 写为 `Axis::HORIZONTAL` | 正常 |
| AC-2.3 | WHEN direction 为 -1（未设置） THEN 越界钳位为 `Axis::VERTICAL`（`scroll_bar_model_ng.cpp:80-82`） | 边界 |
| AC-2.4 | WHEN direction 传入越界值（如 3、-2） THEN 仍钳位为 `Axis::VERTICAL`，组件不报错 | 边界 |

### US-3: 配置滚动条显示状态

作为**应用开发者**，我想要**通过 `state` 控制滚动条常显/常隐/自动**，以便**适配不同交互需求**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 `state: BarState.Auto`（1，缺省） THEN LayoutProperty `DisplayMode` 写为 `DisplayMode::AUTO`，`Visibility::VISIBLE` | 正常 |
| AC-3.2 | WHEN 设置 `state: BarState.On`（2） THEN `DisplayMode::ON`，`Visibility::VISIBLE` | 正常 |
| AC-3.3 | WHEN 设置 `state: BarState.Off`（0） THEN `DisplayMode::OFF`，`Visibility::INVISIBLE`（`scroll_bar_model_ng.cpp:90-91`） | 正常 |
| AC-3.4 | WHEN state 为 -1（未设置） THEN 越界钳位为 `DisplayMode::AUTO`（`scroll_bar_model_ng.cpp:84-86`） | 边界 |
| AC-3.5 | WHEN state 传入越界值（如 5） THEN 钳位为 `DisplayMode::AUTO`，组件不报错 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-1 | 单元测试：Create + RegisterScrollBar 调用断言 | `scroll_bar_model_ng.cpp:76` |
| AC-1.2 | R-2 | TASK-SKELETON-1 | 单元测试：空 Proxy 新建并回填 | `scroll_bar_model_ng.cpp:36-44` |
| AC-1.3 | R-3 | TASK-SKELETON-1 | 单元测试：scroller 缺失 proxyFlag=false | `js_scroll_bar.cpp:73-98` |
| AC-1.4 | R-4 | TASK-SKELETON-1 | 单元测试：无参 Create 默认值 | `js_scroll_bar.cpp:80-82` |
| AC-1.5 | R-1 | TASK-SKELETON-1 | 单元测试：多 ScrollBar 同 Proxy | `scroll_bar_proxy.h` |
| AC-2.1 | R-5 | TASK-SKELETON-2 | 单元测试：Vertical Axis | `scroll_bar_model_ng.cpp:88` |
| AC-2.2 | R-5 | TASK-SKELETON-2 | 单元测试：Horizontal Axis | `scroll_bar_model_ng.cpp:88` |
| AC-2.3 | R-6 | TASK-SKELETON-2 | 单元测试：-1 钳位 VERTICAL | `scroll_bar_model_ng.cpp:80-82` |
| AC-2.4 | R-6 | TASK-SKELETON-2 | 单元测试：越界钳位 | `scroll_bar_model_ng.cpp:80-82` |
| AC-3.1 | R-7 | TASK-SKELETON-2 | 单元测试：Auto 默认 | `scroll_bar_model_ng.cpp:84-91` |
| AC-3.2 | R-7 | TASK-SKELETON-2 | 单元测试：On | `scroll_bar_model_ng.cpp:84-91` |
| AC-3.3 | R-8 | TASK-SKELETON-2 | 单元测试：Off→INVISIBLE | `scroll_bar_model_ng.cpp:90-91` |
| AC-3.4 | R-8 | TASK-SKELETON-2 | 单元测试：-1 钳位 AUTO | `scroll_bar_model_ng.cpp:84-86` |
| AC-3.5 | R-8 | TASK-SKELETON-2 | 单元测试：越界钳位 AUTO | `scroll_bar_model_ng.cpp:84-86` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | options.scroller 为合法 JSScroller 且 Proxy 存在 | `ScrollBarProxy::RegisterScrollBar(pattern)` 登记本 Pattern，`pattern->SetScrollBarProxy(proxy)` | Proxy 必须非 null；宿主滚动经 Proxy 转发 | AC-1.1, AC-1.5 |
| R-2 | 行为 | options.scroller 合法但其 ScrollBarProxy 为空 | `GetScrollBarProxy` 新建 `NG::ScrollBarProxy` 并回填 jsScroller | 新建 Proxy 复用同一 jsScroller | AC-1.2 |
| R-3 | 边界 | options 为对象但 scroller 字段缺失/非对象 | `proxyFlag=false`，ScrollBar 仍创建，不登记 Proxy | 后续依赖 Proxy 的能力为 no-op | AC-1.3 |
| R-4 | 边界 | 调用不传参 `ScrollBar()` | `Create(proxy,null,false,-1,-1)`，direction/state=-1 走默认值 | info.Length()<=0 分支 | AC-1.4 |
| R-5 | 行为 | direction 取值 0 或 1 | 写 LayoutProperty `Axis` 为 VERTICAL/HORIZONTAL | 0=Vertical,1=Horizontal | AC-2.1, AC-2.2 |
| R-6 | 边界 | direction <0 或 >=3 | 钳位为 `Axis::VERTICAL`，组件不报错 | AXIS 向量大小=3 | AC-2.3, AC-2.4 |
| R-7 | 行为 | state 取值 0/1/2 | 写 DisplayMode 为 OFF/AUTO/ON，Visibility=VISIBLE（除 Off） | 0=Off,1=Auto,2=On | AC-3.1, AC-3.2 |
| R-8 | 边界 | state <0 或 >=3 或 ==Off | 越界钳位 `DisplayMode::AUTO`；state==Off 写 `Visibility::INVISIBLE` | DISPLAY_MODE 向量大小=3 | AC-3.3, AC-3.4, AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 Proxy 登记 | 单元测试 | RegisterScrollBar + SetScrollBarProxy 调用 |
| VM-2 | R-3/R-4 边界创建 | 单元测试 | scroller 缺失/无参 不崩溃且默认值正确 |
| VM-3 | R-5/R-6 方向 | 单元测试 | Axis 写入与越界钳位 |
| VM-4 | R-7/R-8 状态 | 单元测试 | DisplayMode + Visibility 写入与钳位 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `ScrollBar(value: ScrollBarOptions)` | Public | `{scroller: Scroller, direction?: ScrollBarDirection, state?: BarState}` | `ScrollBarAttribute` | 无 | 创建独立滚动条并经 Proxy 绑定可滚动宿主 | AC-1.1~1.4 |
| `ScrollBarOptions.scroller` | Public | `Scroller` | — | 无 | 绑定的可滚动宿主控制器（必填） | AC-1.1, AC-1.2 |
| `ScrollBarOptions.direction` | Public | `ScrollBarDirection`（Vertical=0/Horizontal=1） | — | 无 | 滚动条方向，缺省 Vertical | AC-2.1~2.4 |
| `ScrollBarOptions.state` | Public | `BarState`（Off=0/Auto=1/On=2） | — | 无 | 显示状态，缺省 Auto | AC-3.1~3.5 |
| `enum ScrollBarDirection` | Public | `Vertical \| Horizontal` | — | 无 | 方向枚举 | AC-2.x |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | ScrollBar 组件无废弃 API | — |

## 接口规格

### 接口定义

**ScrollBar(value: ScrollBarOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollBarInterface(value: ScrollBarOptions): ScrollBarAttribute` |
| 返回值 | `ScrollBarAttribute` — 滚动条属性链对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `ScrollBarOptions` | 是 | — | 对象；scroller 必填 |
| value.scroller | `Scroller` | 是 | — | 必须为已与可滚动宿主绑定的 JSScroller；缺失则 Proxy 不登记 |
| value.direction | `ScrollBarDirection` | 否 | Vertical(0) | 越界(<0 或 >=3)钳位为 Vertical |
| value.state | `BarState` | 否 | Auto(1) | 越界(<0 或 >=3)钳位为 Auto；Off→INVISIBLE |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | scroller 合法 + Proxy 非空 | 登记本 Pattern 到 Proxy，SetScrollBarProxy | AC-1.1 |
| 2 | scroller 合法 + Proxy 空 | 新建 NG::ScrollBarProxy 并回填 jsScroller | AC-1.2 |
| 3 | scroller 缺失 | proxyFlag=false，不登记 Proxy | AC-1.3 |
| 4 | 无参调用 | Create(proxy,null,false,-1,-1)，默认值 | AC-1.4 |
| 5 | direction=1 | Axis=HORIZONTAL | AC-2.2 |
| 6 | direction=-1/越界 | Axis 钳位 VERTICAL | AC-2.3, AC-2.4 |
| 7 | state=0(Off) | DisplayMode=OFF, Visibility=INVISIBLE | AC-3.3 |
| 8 | state 越界 | DisplayMode 钳位 AUTO | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 创建族自 API 8 起连续，crossplatform 10、FaAndStageModel+atomicservice 11 为能力层级再声明，行为无变化
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** 创建族标注 @since 8/10/11 三层；方向/状态越界钳位行为跨版本一致

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Proxy 前置依赖 | `enableNestedScroll` 等依赖宿主的能力在未登记 Proxy 时为 no-op | AC-1.3 |
| 与可滚动宿主解耦 | ScrollBar 经 Scroller/ScrollBarProxy 间接绑定，不直接持有宿主 | AC-1.1, AC-1.5 |
| 越界容错 | direction/state 越界一律钳位默认值，不抛错 | AC-2.3~2.4, AC-3.4~3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 创建单个 ScrollBar 在一帧内完成 Proxy 登记 | 单元测试/性能基准 | `scroll_bar_model_ng.cpp:46-93` |
| 内存 | ScrollBarPattern 不持有滚动内容，仅滑块状态 | 代码审查 | `scroll_bar_pattern.h:397-444` |
| 可测试性 | Create 路径可经 ModelNG 单测覆盖 | 单元测试 | TASK-SKELETON-1 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准 VERTICAL/AUTO | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |
| 穿戴(WATCH/WEARABLE) | Arc 形态 | `CreateArcScrollBar` 创建 `ARC_SCROLL_BAR_ETS_TAG` + `CreateArcScrollBarPattern` | 单元测试 | `scroll_bar_model_ng.cpp:55-60` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | ScrollBarAccessibilityProperty 提供滚动动作无障碍 | AC-1.x |
| 大字体 | 否 | 滑块尺寸不随字体变化 | — |
| 深色模式 | 是 | 颜色经主题；本 Feat 不涉及颜色（见 Feat-02） | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API≥12 启用 ScrollBarPaintMethod，之前走基类默认 | — |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（仅创建/方向/状态/Proxy 绑定，颜色与嵌套滚动在 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollBarPattern 如何经 ScrollBarProxy 与可滚动宿主配对，宿主滚动时如何转发偏移到 ScrollBar"
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollBar Create 路径方向/状态越界钳位为 VERTICAL/AUTO 的实现位置"
```

**关键文档:** `scroll_bar.d.ts`、`scroll_bar_model_ng.cpp`、`js_scroll_bar.cpp`、`design.md`
