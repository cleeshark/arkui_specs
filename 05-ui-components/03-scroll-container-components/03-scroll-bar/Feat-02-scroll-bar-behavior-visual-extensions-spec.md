# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ScrollBar 行为与视觉扩展 |
| 特性编号 | Func-05-03-03-Feat-02 |
| 优先级 | P2 |
| 目标版本 | API 14 ~ 20+ |
| 复杂度 | 标准 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖在 Feat-01 创建基线之上的两个后增属性：`enableNestedScroll`（@since 14）与 `scrollBarColor`（@since 20）。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/03-scroll-bar/design.md` |
| SDK Dynamic | `ets/dynamic/component/scroll_bar.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/scroll_bar/scroll_bar_pattern.h` |
| Model Source | `frameworks/core/components_ng/pattern/scroll_bar/scroll_bar_model_ng.cpp` |
| PaintProperty | `frameworks/core/components_ng/pattern/scroll_bar/scroll_bar_paint_property.h` |
| JSView Source | `frameworks/bridge/declarative_frontend/jsview/scroll_bar/js_scroll_bar.cpp` |
| C-API Modifier | `frameworks/core/interfaces/native/node/node_scroll_bar_modifier.cpp` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 启用滚动条嵌套滚动

作为**应用开发者**，我想要**通过 `enableNestedScroll` 让 ScrollBar 拖动联动父级可滚动容器**，以便**在嵌套滚动场景下统一滚动分发**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `enableNestedScroll(true)` 且已绑定合法宿主（Proxy 非空）且旧值为 false THEN `SetNestedScroll`→宿主 `SearchAndSetParentNestedScroll(node)` 被调用（`scroll_bar_model_ng.cpp:133-134`） | 正常 |
| AC-1.2 | WHEN 设置 `enableNestedScroll(false)` 且旧值为 true THEN `UnSetNestedScroll`→宿主 `SearchAndUnsetParentNestedScroll(node)` 被调用（`scroll_bar_model_ng.cpp:136-137`） | 正常 |
| AC-1.3 | WHEN 未绑定 scroller（Proxy 为空）THEN `SetEnableNestedScroll` 经 `CHECK_NULL_VOID(scrollBarProxy)` 提前返回，`enableNestedSorll_` 不更新且不崩溃（`scroll_bar_model_ng.cpp:125-126`） | 边界 |
| AC-1.4 | WHEN 设置的值与旧值相同 THEN 不触发 Set/UnSetNestedScroll（`scroll_bar_model_ng.cpp:133,136` 的 `!= enableNested` 守卫） | 边界 |
| AC-1.5 | WHEN `enableNestedScroll` 入参非布尔（缺参或类型错误）THEN 默认置为 false（`js_scroll_bar.cpp:116-118`） | 异常 |
| AC-1.6 | WHEN 宿主节点不在主树（`frameNode->IsOnMainTree()` 为 false）THEN `SetNestedScroll`/`UnSetNestedScroll` 不执行 `SearchAndSetParentNestedScroll`（`scroll_bar_model_ng.cpp:105-107`） | 边界 |

### US-2: 自定义滚动条颜色

作为**应用开发者**，我想要**通过 `scrollBarColor(color)` 设置滚动条颜色（支持渐变与 alpha）**，以便**匹配应用视觉风格**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `scrollBarColor(ColorMetrics)` 且解析成功 THEN `ScrollBarPaintProperty::ScrollBarColor` 写为该 Color（`scroll_bar_model_ng.cpp:163-166`） | 正常 |
| AC-2.2 | WHEN ColorMetrics 解析失败（非法颜色）THEN 调用 `ResetScrollBarColor`（`js_scroll_bar.cpp:128-130`） | 异常 |
| AC-2.3 | WHEN 调用 `scrollBarColor(undefined)` 或 reset THEN `ResetScrollBarColor` 取 `ScrollBarTheme::GetForegroundColor()` 回写 `ScrollBar::SetForegroundColor`（`scroll_bar_model_ng.cpp:179-193`） | 正常 |
| AC-2.4 | WHEN 传入资源对象 THEN `HandleSetScrollBarColor` 注册 `AddResObj("ScrollBar.SetScrollBarColor", ...)`，配置变更时经 `ParseResColor` 重解析并重写或 reset（`scroll_bar_model_ng.cpp:209-227`） | 正常 |
| AC-2.5 | WHEN 资源解析成功 THEN `SetScrollBarColor(frameNode, result)`；失败 THEN `ResetScrollBarColor(frameNode)`（`scroll_bar_model_ng.cpp:220-224`） | 正常 |
| AC-2.6 | WHEN 切换深色模式 THEN `OnColorConfigurationUpdate`/`OnColorModeChange` 触发颜色重算（`scroll_bar_pattern.h:321-322`） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-3 | 单元测试：true 触发 SearchAndSetParentNestedScroll | `scroll_bar_model_ng.cpp:133-134` |
| AC-1.2 | R-2 | TASK-SKELETON-3 | 单元测试：false 触发 SearchAndUnsetParentNestedScroll | `scroll_bar_model_ng.cpp:136-137` |
| AC-1.3 | R-3 | TASK-SKELETON-3 | 单元测试：Proxy null 提前返回不崩溃 | `scroll_bar_model_ng.cpp:125-126` |
| AC-1.4 | R-4 | TASK-SKELETON-3 | 单元测试：同值不触发 | `scroll_bar_model_ng.cpp:133,136` |
| AC-1.5 | R-5 | TASK-SKELETON-3 | 单元测试：非布尔默认 false | `js_scroll_bar.cpp:116-118` |
| AC-1.6 | R-6 | TASK-SKELETON-3 | 单元测试：非主树不执行 | `scroll_bar_model_ng.cpp:105-107` |
| AC-2.1 | R-7 | TASK-SKELETON-4 | 单元测试：PaintProperty 写入 | `scroll_bar_model_ng.cpp:163-166` |
| AC-2.2 | R-8 | TASK-SKELETON-4 | 单元测试：解析失败 reset | `js_scroll_bar.cpp:128-130` |
| AC-2.3 | R-9 | TASK-SKELETON-4 | 单元测试：reset 回退主题前景色 | `scroll_bar_model_ng.cpp:179-193` |
| AC-2.4 | R-10 | TASK-SKELETON-4 | 单元测试：资源对象注册与回调 | `scroll_bar_model_ng.cpp:209-227` |
| AC-2.5 | R-10 | TASK-SKELETON-4 | 单元测试：资源重解析分支 | `scroll_bar_model_ng.cpp:220-224` |
| AC-2.6 | R-11 | TASK-SKELETON-4 | 单元测试：深色模式重算 | `scroll_bar_pattern.h:321-322` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `enableNestedScroll(true)` 且 Proxy 非空且旧值=false | 写 `enableNestedSorll_=true`，调 `SetNestedScroll`→宿主 `SearchAndSetParentNestedScroll` | 依赖宿主在主树 | AC-1.1 |
| R-2 | 行为 | `enableNestedScroll(false)` 且旧值=true | 写 `enableNestedSorll_=false`，调 `UnSetNestedScroll`→宿主 `SearchAndUnsetParentNestedScroll` | 同上 | AC-1.2 |
| R-3 | 边界 | 未绑定 scroller（Proxy 为空） | `CHECK_NULL_VOID(scrollBarProxy)` 提前返回，不更新状态 | 不崩溃 | AC-1.3 |
| R-4 | 边界 | 新值==旧值 | 不触发 Set/UnSetNestedScroll | `!= enableNested` 守卫 | AC-1.4 |
| R-5 | 异常 | 入参非布尔或缺参 | 默认置 false 并调用 `SetEnableNestedScroll(false)` | args.Length()<1 或非 Boolean | AC-1.5 |
| R-6 | 边界 | 宿主节点 `IsOnMainTree()`=false | `SetNestedScroll`/`UnSetNestedScroll` 不执行 Search | 仅在主树时搜索父级 | AC-1.6 |
| R-7 | 行为 | `scrollBarColor(ColorMetrics)` 解析成功 | 写 `ScrollBarPaintProperty::ScrollBarColor` | PROPERTY_UPDATE_RENDER | AC-2.1 |
| R-8 | 异常 | ColorMetrics 解析失败 | 调 `ResetScrollBarColor` | 解析失败兜底 | AC-2.2 |
| R-9 | 恢复 | `scrollBarColor(undefined)`/reset | 取 `ScrollBarTheme::GetForegroundColor()` 回写 `ScrollBar::SetForegroundColor` | 主题回退 | AC-2.3 |
| R-10 | 行为 | 传入资源对象 | `HandleSetScrollBarColor` 注册 `AddResObj`，配置变更时 `ParseResColor` 重解析 | 成功→Set，失败→Reset | AC-2.4, AC-2.5 |
| R-11 | 行为 | 深色模式切换 | `OnColorConfigurationUpdate`/`OnColorModeChange` 触发颜色重算 | 主题色随模式更新 | AC-2.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 嵌套滚动开关 | 单元测试 | SearchAndSet/Unset 调用与守卫 |
| VM-2 | R-3/R-4/R-6 边界 | 单元测试 | Proxy null/同值/非主树 不触发 |
| VM-3 | R-5 异常入参 | 单元测试 | 非布尔默认 false |
| VM-4 | R-7/R-8 颜色写入 | 单元测试 | PaintProperty 写入与解析失败 reset |
| VM-5 | R-9 主题回退 | 单元测试 | GetForegroundColor 回写 |
| VM-6 | R-10 资源对象 | 单元测试 | AddResObj 注册与回调重解析 |
| VM-7 | R-11 深色模式 | 单元测试 | OnColorConfigurationUpdate 触发 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `enableNestedScroll(enabled)` | Public（@since 14, stagemodelonly+crossplatform+atomicservice） | `Optional<boolean>` | `ScrollBarAttribute` | 无 | 启用/关闭滚动条嵌套滚动，委派所绑定宿主 | AC-1.1~1.6 |
| `scrollBarColor(color)` | Public（@since 20, stagemodelonly+crossplatform+atomicservice） | `Optional<ColorMetrics>` | `ScrollBarAttribute` | 无 | 设置滚动条颜色（支持渐变/alpha），reset 回退主题 | AC-2.1~2.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无废弃 | — |

## 接口规格

### 接口定义

**enableNestedScroll(enabled: Optional<boolean>)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollBarAttribute::enableNestedScroll(enabled: Optional<boolean>): ScrollBarAttribute` |
| 返回值 | `ScrollBarAttribute` — 链式返回 |
| 开放范围 | Public（@since 14） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enabled | `Optional<boolean>` | 是 | 非布尔时按 false | 缺参/非 Boolean → false；依赖 Proxy 非空 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | true+Proxy 非空+旧 false | SearchAndSetParentNestedScroll | AC-1.1 |
| 2 | false+旧 true | SearchAndUnsetParentNestedScroll | AC-1.2 |
| 3 | Proxy 空 | 提前返回，不更新 | AC-1.3 |
| 4 | 新==旧 | 不触发 | AC-1.4 |
| 5 | 非布尔 | 默认 false | AC-1.5 |
| 6 | 非主树 | 不执行 Search | AC-1.6 |

### 接口定义

**scrollBarColor(color: Optional<ColorMetrics>)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ScrollBarAttribute::scrollBarColor(color: Optional<ColorMetrics>): ScrollBarAttribute` |
| 返回值 | `ScrollBarAttribute` |
| 开放范围 | Public（@since 20） |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| color | `Optional<ColorMetrics>` | 是 | reset 时回退主题前景色 | 经 `ParseColorMetricsToColor` 解析；支持资源对象 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | ColorMetrics 解析成功 | 写 PaintProperty ScrollBarColor | AC-2.1 |
| 2 | 解析失败 | ResetScrollBarColor | AC-2.2 |
| 3 | undefined/reset | 主题 GetForegroundColor 回写 | AC-2.3 |
| 4 | 资源对象 | AddResObj 注册回调 | AC-2.4 |
| 5 | 配置变更重解析 | 成功 Set/失败 Reset | AC-2.5 |
| 6 | 深色模式切换 | OnColorConfigurationUpdate 重算 | AC-2.6 |

## 兼容性声明

- **已有 API 行为变更:** 否 — `enableNestedScroll`（@since 14）与 `scrollBarColor`（@since 20）均为新增，不改既有创建族行为
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** enableNestedScroll API 14；scrollBarColor API 20
- **API 版本号策略:** 两属性均 stagemodelonly+crossplatform+atomicservice；签名差异风险：可滚动容器的 `scrollBarColor` 接 `Color|string|number|Resource`，本组件接 `ColorMetrics`

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 嵌套委派宿主 | enableNestedScroll 不在 ScrollBar 内实现嵌套，作用于所绑定宿主 | AC-1.1~1.6 |
| 颜色两层存储 | 写 PaintProperty；reset/主题回退走 ScrollBar 内建 foreground | AC-2.1~2.3 |
| 资源热重载 | 颜色资源对象经 AddResObj 在配置变更时重解析 | AC-2.4~2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 颜色设置触发 PROPERTY_UPDATE_RENDER 单帧内完成 | 单元测试 | `scroll_bar_model_ng.cpp:163-166` |
| 内存 | 资源对象经 pattern 持有，模式切换释放 | 代码审查 | `scroll_bar_model_ng.cpp:214-226` |
| 可测试性 | 嵌套开关与颜色均可经 ModelNG 单测 | 单元测试 | TASK-SKELETON-3/4 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准行为 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 颜色/嵌套不影响无障碍动作 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 是 | scrollBarColor reset 回退主题，模式切换重算 | AC-2.3, AC-2.6 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | enableNestedScroll @14、scrollBarColor @20 版本门槛 | AC-1.x, AC-2.x |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（仅 enableNestedScroll/scrollBarColor，创建在 Feat-01）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollBar enableNestedScroll 如何经 ScrollBarProxy 取宿主并调用 SearchAndSetParentNestedScroll"
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollBar scrollBarColor 的 ColorMetrics 解析、资源对象热重载与主题 GetForegroundColor 回退路径"
```

**关键文档:** `scroll_bar.d.ts`、`scroll_bar_model_ng.cpp`、`js_scroll_bar.cpp`、`scroll_bar_pattern.h`、`design.md`
