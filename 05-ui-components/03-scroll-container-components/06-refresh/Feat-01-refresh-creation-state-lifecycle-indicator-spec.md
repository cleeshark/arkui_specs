# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Refresh 创建、刷新状态生命周期与指示器内容 |
| 特性编号 | Func-05-03-06-Feat-01 |
| 优先级 | P1 |
| 目标版本 | API 8 ~ 12+ |
| 复杂度 | 复杂 |
| 状态 | Baselined |

## 本次变更范围（Delta）

> 全新特性规格（已有实现补录），无 Delta。本 Feat 覆盖创建、RefreshStatus 状态机与事件顺序、默认 LoadingProgress 与自定义 builder/refreshingContent/promptText 指示器。

## 输入文档

| 文档类型 | 路径 |
|----------|------|
| Design | `05-ui-components/03-scroll-container-components/06-refresh/design.md` |
| SDK Dynamic | `ets/dynamic/component/refresh.d.ts` |
| Pattern Source | `frameworks/core/components_ng/pattern/refresh/refresh_pattern.h` / `.cpp` |
| EventHub Source | `frameworks/core/components_ng/pattern/refresh/refresh_event_hub.h` |
| LayoutProperty | `frameworks/core/components_ng/pattern/refresh/refresh_layout_property.h` |
| Model Source | `frameworks/core/components_ng/pattern/refresh/refresh_model_ng.cpp` |
| Bridge Source | `frameworks/core/components_ng/pattern/refresh/bridge/arkts_native_refresh_bridge.cpp` |
| Component Rules | `frameworks/core/components_ng/pattern/refresh/CLAUDE.md` |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 创建 Refresh 容器并绑定刷新状态

作为**应用开发者**，我想要**通过 `Refresh({refreshing})` 创建下拉刷新容器并用 `$$` 双向绑定 refreshing 状态**，以便**在代码中控制刷新开始/结束**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 `Refresh({refreshing: this.isRefreshing})` THEN RefreshPattern 创建成功，RefreshLayoutProperty::IsRefreshing 写入初值（`refresh_model_ng.cpp`） | 正常 |
| AC-1.2 | WHEN refreshing 支持 `$$` 双向绑定且代码置 isRefreshing=true THEN 进入 REFRESH 状态，FireOnRefreshing 触发；置 false THEN 转 DONE 回 INACTIVE | 正常 |
| AC-1.3 | WHEN 不传 refreshing THEN 创建失败/报错（refreshing 为必填） | 异常 |
| AC-1.4 | WHEN Refresh 创建且 Axis 固定为 VERTICAL THEN `GetAxis()` 返回 `Axis::VERTICAL`（`refresh_pattern.h:90`），非纵向场景不适用 | 正常 |

### US-2: 刷新状态机与事件顺序

作为**应用开发者**，我想要**通过 onStateChange/onRefreshing 感知刷新状态变化**，以便**联动业务加载逻辑**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 子节点在顶部下拉进入 DRAG THEN onStateChange(RefreshStatus.Drag) 触发 | 正常 |
| AC-2.2 | WHEN 下拉越过 refreshOffset 阈值 THEN DRAG→OVER_DRAG，onStateChange(OverDrag) 触发；回落低于阈值 THEN 回 DRAG | 正常 |
| AC-2.3 | WHEN OVER_DRAG 状态释放 THEN 转 REFRESH；事件顺序为 UpdateRefreshStatus(REFRESH)→FireChangeEvent("true")→FireOnRefreshing()→FireOnStateChange(REFRESH)（CLAUDE.md） | 正常 |
| AC-2.4 | WHEN 未到阈值释放 THEN DRAG→INACTIVE，不触发 onRefreshing | 正常 |
| AC-2.5 | WHEN 刷新完成（refreshing=false）THEN REFRESH→DONE→FireChangeEvent("false")→FireOnStateChange(DONE)，动画完成后回 INACTIVE | 正常 |
| AC-2.6 | WHEN 新状态与旧状态相同 THEN UpdateRefreshStatus 早退，不重复触发事件 | 边界 |
| AC-2.7 | WHEN 状态机被要求跳转（如 DRAG 直接到 REFRESH）THEN 不允许跳转，必须经 OVER_DRAG（CLAUDE.md 禁止跳转） | 边界 |

### US-3: 默认指示器与自定义指示器内容

作为**应用开发者**，我想要**用 builder/refreshingContent 替换默认 LoadingProgress，并用 promptText 显示刷新提示文本**，以便**自定义刷新视觉**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 不设 builder/refreshingContent THEN 默认创建 LoadingProgress（progressChild_，`refresh_pattern.h:199`）+ 可选 Text（loadingTextNode_）堆叠于 Column | 正常 |
| AC-3.2 | WHEN 设置 builder(CustomBuilder) THEN AddCustomBuilderNode 先 RemoveChild(progressChild_/columnNode_)，再 AddChild(builder,0)，isCustomBuilderExist_=true（CLAUDE.md） | 正常 |
| AC-3.3 | WHEN 设置 refreshingContent(ComponentContent) THEN 同样替换默认指示器，经 ComponentContent 通道 | 正常 |
| AC-3.4 | WHEN builder 传 null/移除 THEN 恢复默认 LoadingProgress，isCustomBuilderExist_=false | 正常 |
| AC-3.5 | WHEN 同时存在 builder 与默认未清理 THEN 必须先删后加，禁止叠加显示（CLAUDE.md 反模式） | 异常 |
| AC-3.6 | WHEN 设置 promptText(ResourceStr) THEN loadingTextNode_ 显示该文本（@since 12，stagemodelonly） | 正常 |
| AC-3.7 | WHEN 切换深色模式 THEN OnColorConfigurationUpdate/OnColorModeChange 重算 LoadingProgress 颜色与主题尺寸（loadingProgressSizeTheme_=32vp） | 正常 |

### US-4: 键盘快捷触发刷新

作为**应用开发者（桌面/调试）**，我想要**用 F5 或 Ctrl+R 快捷键触发刷新**，以便**快速验证刷新逻辑**。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 焦点在 Refresh 且非刷新中按下 F5 THEN QuickStartFresh 直接进入 REFRESH | 正常 |
| AC-4.2 | WHEN 按下 Ctrl+R（Cmd+R）组合键且非刷新中 THEN 同上触发 | 正常 |
| AC-4.3 | WHEN 已在刷新中再按快捷键 THEN 不重复触发（CLAUDE.md 仅非刷新时） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-1 | 单元测试：Create + IsRefreshing 写入 | `refresh_model_ng.cpp` |
| AC-1.2 | R-2 | TASK-SKELETON-1 | 单元测试：$$ 双向绑定状态转换 | `refresh_pattern.cpp` |
| AC-1.3 | R-3 | TASK-SKELETON-1 | 单元测试：缺 refreshing 报错 | `refresh.d.ts:215` |
| AC-1.4 | R-4 | TASK-SKELETON-1 | 单元测试：Axis VERTICAL | `refresh_pattern.h:90` |
| AC-2.1 | R-5 | TASK-SKELETON-1 | 单元测试：DRAG onStateChange | `refresh_pattern.cpp` |
| AC-2.2 | R-5 | TASK-SKELETON-1 | 单元测试：阈值切换 | `refresh_pattern.cpp` |
| AC-2.3 | R-6 | TASK-SKELETON-1 | 单元测试：事件顺序断言 | CLAUDE.md |
| AC-2.4 | R-5 | TASK-SKELETON-1 | 单元测试：未到阈值不触发 | `refresh_pattern.cpp` |
| AC-2.5 | R-6 | TASK-SKELETON-1 | 单元测试：DONE 回 INACTIVE | `refresh_pattern.cpp` |
| AC-2.6 | R-7 | TASK-SKELETON-1 | 单元测试：同态早退 | `refresh_pattern.cpp` |
| AC-2.7 | R-8 | TASK-SKELETON-1 | 代码审查：禁止跳转 | CLAUDE.md |
| AC-3.1 | R-9 | TASK-SKELETON-2 | 单元测试：默认 LoadingProgress | `refresh_pattern.h:199` |
| AC-3.2 | R-10 | TASK-SKELETON-2 | 单元测试：builder 先删后加 | `refresh_pattern.cpp` AddCustomBuilderNode |
| AC-3.3 | R-10 | TASK-SKELETON-2 | 单元测试：refreshingContent 替换 | `refresh_model_ng.cpp` |
| AC-3.4 | R-11 | TASK-SKELETON-2 | 单元测试：null 恢复默认 | `refresh_pattern.cpp` |
| AC-3.5 | R-12 | TASK-SKELETON-2 | 代码审查：禁止叠加 | CLAUDE.md |
| AC-3.6 | R-13 | TASK-SKELETON-2 | 单元测试：promptText 文本节点 | `refresh_layout_property.h` LoadingText |
| AC-3.7 | R-14 | TASK-SKELETON-2 | 单元测试：深色模式重算 | `refresh_pattern.h:88,113` |
| AC-4.1 | R-15 | TASK-SKELETON-1 | 单元测试：F5 触发 | `refresh_pattern.cpp` OnKeyEvent |
| AC-4.2 | R-15 | TASK-SKELETON-1 | 单元测试：Ctrl+R | `refresh_pattern.cpp` |
| AC-4.3 | R-16 | TASK-SKELETON-1 | 单元测试：刷新中不重复 | CLAUDE.md |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `Refresh({refreshing})` 创建 | RefreshLayoutProperty::IsRefreshing 写入 refreshing 初值 | refreshing 必填 | AC-1.1 |
| R-2 | 行为 | refreshing `$$` 双向绑定，代码置 true/false | 进入/退出 REFRESH 并同步回写变量 | 双向绑定 | AC-1.2 |
| R-3 | 异常 | 不传 refreshing | 创建失败/报错 | refreshing 必填，无默认 | AC-1.3 |
| R-4 | 行为 | Refresh 创建 | Axis 固定 VERTICAL | `refresh_pattern.h:90` | AC-1.4 |
| R-5 | 行为 | 下拉/阈值切换 | onStateChange 触发对应状态 | INACTIVE→DRAG→OVER_DRAG | AC-2.1, AC-2.2, AC-2.4 |
| R-6 | 行为 | 释放达阈值/完成 | 事件顺序固定：状态→ChangeEvent→OnRefreshing→StateChange | REFRESH/DONE 两段 | AC-2.3, AC-2.5 |
| R-7 | 边界 | 新状态==旧状态 | UpdateRefreshStatus 早退，不重复触发 | 同态守卫 | AC-2.6 |
| R-8 | 边界 | 要求跳转 | 不允许跳过中间态 | 禁止 DRAG→REFRESH 直跳 | AC-2.7 |
| R-9 | 行为 | 不设自定义指示器 | 默认 LoadingProgress(progressChild_)+可选 Text | progressChild_ 非空 | AC-3.1 |
| R-10 | 行为 | 设置 builder/refreshingContent | 先 RemoveChild(progressChild_/columnNode_) 再 AddChild(builder,0) | isCustomBuilderExist_=true | AC-3.2, AC-3.3 |
| R-11 | 恢复 | builder 传 null | 恢复默认 LoadingProgress | isCustomBuilderExist_=false | AC-3.4 |
| R-12 | 异常 | 默认未清理即加 builder | 禁止叠加，必须先删后加 | CLAUDE.md 反模式 | AC-3.5 |
| R-13 | 行为 | 设置 promptText | loadingTextNode_ 显示文本（@since 12） | LoadingText 属性 | AC-3.6 |
| R-14 | 行为 | 深色模式切换 | OnColorConfigurationUpdate/OnColorModeChange 重算颜色与主题尺寸 | loadingProgressSizeTheme_=32vp | AC-3.7 |
| R-15 | 行为 | 焦点在 Refresh 且非刷新中按 F5/Ctrl+R | QuickStartFresh 进入 REFRESH | 仅 key press | AC-4.1, AC-4.2 |
| R-16 | 边界 | 已刷新中再按快捷键 | 不重复触发 | 仅非刷新时 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1~R-4 创建与绑定 | 单元测试 | IsRefreshing 写入与 Axis |
| VM-2 | R-5~R-8 状态机 | 单元测试 | 状态转换与事件顺序 |
| VM-3 | R-9~R-12 指示器 | 单元测试 | 先删后加与恢复默认 |
| VM-4 | R-13 promptText | 单元测试 | 文本节点 |
| VM-5 | R-14 深色模式 | 单元测试 | 颜色重算 |
| VM-6 | R-15/R-16 快捷键 | 单元测试 | F5/Ctrl+R 触发与守卫 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `Refresh(value)` | Public（@since 8/10/11） | `RefreshOptions` | `RefreshAttribute` | 无 | 创建下拉刷新容器 | AC-1.1~1.4 |
| `RefreshOptions.refreshing` | Public | `boolean`（支持 `$$`） | — | 无 | 刷新状态，必填 | AC-1.1, AC-1.2 |
| `RefreshOptions.builder` | Public（@since 10/11） | `CustomBuilder?` | — | 无 | 自定义拖拽指示器 | AC-3.2 |
| `RefreshOptions.refreshingContent` | Public（@since 12） | `ComponentContent?` | — | 无 | 自定义刷新内容 | AC-3.3 |
| `RefreshOptions.promptText` | Public（@since 12） | `ResourceStr?` | — | 无 | 刷新提示文本 | AC-3.6 |
| `enum RefreshStatus` | Public | Inactive/Drag/OverDrag/Refresh/Done | — | 无 | 状态枚举 | AC-2.x |
| `onStateChange(callback)` | Public | `(state: RefreshStatus)=>void` | `RefreshAttribute` | 无 | 状态变化回调 | AC-2.1~2.7 |
| `onRefreshing(callback)` | Public | `()=>void` | `RefreshAttribute` | 无 | 进入刷新回调 | AC-2.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 本 Feat 不含废弃（offset/friction 在 Feat-02） | — |

## 接口规格

### 接口定义

**Refresh(value: RefreshOptions)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefreshInterface(value: RefreshOptions): RefreshAttribute` |
| 返回值 | `RefreshAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | `RefreshOptions` | 是 | — | 对象 |
| value.refreshing | `boolean` | 是 | — | 支持 `$$` 双向绑定 |
| value.builder | `CustomBuilder` | 否 | 无（用默认 LoadingProgress） | 非空时替换默认 |
| value.refreshingContent | `ComponentContent` | 否 | 无 | @since 12，替换默认 |
| value.promptText | `ResourceStr` | 否 | 无 | @since 12，文本节点 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | refreshing 合法 | 创建 + IsRefreshing 写入 | AC-1.1 |
| 2 | refreshing `$$` 绑定 true/false | 状态转换同步回写 | AC-1.2 |
| 3 | 缺 refreshing | 报错 | AC-1.3 |
| 4 | 创建 | Axis=VERTICAL | AC-1.4 |
| 5 | 下拉进 DRAG | onStateChange(Drag) | AC-2.1 |
| 6 | 越阈值 | DRAG→OVER_DRAG | AC-2.2 |
| 7 | OVER_DRAG 释放 | REFRESH + 事件顺序 | AC-2.3 |
| 8 | 完成 | DONE→INACTIVE | AC-2.5 |
| 9 | 设 builder | 先删后加 | AC-3.2 |
| 10 | builder null | 恢复默认 | AC-3.4 |
| 11 | 设 promptText | 文本节点 | AC-3.6 |
| 12 | F5/Ctrl+R | QuickStartFresh | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 创建族自 API 8 连续；状态机/事件顺序/弹簧参数为不变量
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8（builder @10/11、refreshingContent/promptText @12）
- **API 版本号策略:** 创建族标注 @since 8/10/11；builder @10/11；refreshingContent/promptText @12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 状态机顺序不可变 | INACTIVE→DRAG→OVER_DRAG→REFRESH→DONE | AC-2.x |
| 事件顺序固定 | 状态→ChangeEvent→OnRefreshing→StateChange | AC-2.3, AC-2.5 |
| 自定义指示器先删后加 | 禁止叠加 | AC-3.2, AC-3.5 |
| 纵向固定 | Axis=VERTICAL | AC-1.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 拖拽回调保 60FPS，热路径无字符串操作 | 性能基准 | CLAUDE.md 性能约束 |
| 内存 | 动画控制器复用，Stop 旧动画再起新 | 代码审查 | CLAUDE.md |
| 可靠性 | 状态机同态早退避免重复事件 | 单元测试 | R-7 |
| 可测试性 | 状态机/事件可单测覆盖 | 单元测试 | TASK-SKELETON-1/2 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | — | 标准状态机 | 单元测试 | — |
| 平板 | — | 同手机 | 单元测试 | — |
| 折叠屏 | — | 同手机 | 单元测试 | — |
| 穿戴 | 键盘快捷键可能不适用 | F5/Ctrl+R 在无键盘设备不触发 | 代码审查 | `refresh_pattern.cpp` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | RefreshAccessibilityProperty 提供刷新动作 | AC-2.x |
| 大字体 | 是 | promptText/loadingText 随字体 | AC-3.6 |
| 深色模式 | 是 | OnColorConfigurationUpdate 重算指示器颜色 | AC-3.7 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | builder @10/11、refreshingContent/promptText @12 门槛 | AC-3.2, AC-3.3, AC-3.6 |
| 生态兼容 | 否 | 无差异 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（创建/状态机/事件/指示器；物理与手势在 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RefreshPattern UpdateRefreshStatus 状态机顺序与事件触发顺序实现"
  - repo: "openharmony/arkui_ace_engine"
    query: "Refresh AddCustomBuilderNode 先删默认 LoadingProgress 再加自定义 builder 的契约"
```

**关键文档:** `refresh.d.ts`、`refresh_pattern.h/.cpp`、`refresh_event_hub.h`、`CLAUDE.md`、`design.md`
