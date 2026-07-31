# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 无障碍子树注册与跨进程接入 |
| 特性编号 | Func-03-07-01-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 13 起 |
| SIG 归属 | SIG_ApplicationFramework |
| 状态 | Draft |
| 复杂度 | 复杂 |

> 框架内部能力补录：当前实现即契约。本 Feat 覆盖**无障碍子树（ChildTree）注册管理管道与跨进程组件（Form/UIExtension/Isolated/Web）的悬停转发**；元素字段填充在 Feat-01、悬停命中算法在 Feat-04、动作执行分发在 Feat-02、事件上报在 Feat-07。
>
> **术语**：本规格中"**跨进程组件**"指经 `AccessibilitySessionAdapter` 接入的系统级跨进程组件（Form/UIExtension/Isolated/Web）；"**应用自绘组件**"指经 NDK Accessibility Provider 接入的应用内 Native 自绘节点（XComponent/Custom），其 Provider 注册与分发见 **Feat-06**。子树注册管道（ChildTree）为二者共用的挂载机制，本 Feat 统一描述。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 子树注册与跨进程接入规格化 | 固化 SessionAdapter 子类矩阵（悬停转发）、ChildTree 注册/反注册/广播、子树 ID 编码、Web 独立路径 |

## 输入文档

- 设计文档：`03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/design.md`
- 源码定位：`frameworks/core/accessibility/accessibility_session_adapter.*`、`frameworks/core/accessibility/accessibility_manager.h`（ChildTreeCallback）、`adapter/ohos/osal/js_accessibility_manager.cpp`、各 pattern 的 `accessibility_session_adapter_*`/`*_accessibility_child_tree_callback.*`

## 用户故事

### US-1: 跨进程组件的悬停事件转发（SessionAdapter）

**作为** 跨进程组件,
**我想要** 宿主节点忽略自身、将悬停事件转发给子树,
**以便** 子进程参与触控浏览

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN 命中跨进程组件宿主 THEN `IgnoreHostNode()` 返回 true，宿主不消费悬停 | 正常 |
| AC-1.2 | WHEN 悬停事件需转发 THEN `TransferHoverEvent` 路由到对应 adapter 持有的委托（FormManagerDelegate/SessionWrapper/DynamicComponentRenderer/WebPattern/应用自绘组件 hover 管道） | 正常 |
| AC-1.3 | WHEN UIExtension/Isolated 系 adapter THEN `IgnoreTransformMouseEvent()` 返回 true（自行处理 mouse 事件） | 边界 |

### US-2: 子树（ChildTree）注册与管理

**作为** 框架,
**我想要** 管理跨进程/自绘子树的注册、反注册与 childTreeId/belongTreeId 关系,
**以便**  SA 按 (windowId, treeId) 路由查询/动作

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN 组件 attach 初始化无障碍 THEN 注册 `AccessibilityChildTreeCallback` 到父管理器（childTreeCallbackMap_） | 正常 |
| AC-2.2 | WHEN 父级注册成功 THEN `NotifyChildTreeOnRegister` 广播 OnRegister(windowId, treeId) 给所有已挂 callback | 正常 |
| AC-2.3 | WHEN SA 通知 SetChildTreeIdAndWinId THEN 普通路径经 childTreeCallbackMap_ 分发到子组件（SetChildTreeId + OnSetChildTree） | 正常 |
| AC-2.4 | WHEN 节点上报 ElementInfo THEN 设置 `SetChildTreeIdAndWinId(GetChildTreeId, GetChildWindowId)` 与 `SetBelongTreeId(treeId_)` | 正常 |
| AC-2.5 | WHEN 同 parent 三元组重复注册 THEN `NeedRegisterChildTree` 去重返回 false | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-5 | 单测 | accessibility_session_adapter.cpp:21 |
| AC-1.2 | R-1 | TASK-5 | 单测 | accessibility_session_adapter_*.cpp |
| AC-1.3 | R-1 | TASK-5 | 单测 | accessibility_session_adapter_ui_extension.h:35 |
| AC-2.1 | R-2 | TASK-5 | 单测 | js_accessibility_manager.cpp:9086 |
| AC-2.2 | R-2 | TASK-5 | 单测 | js_accessibility_manager.cpp:9136 |
| AC-2.3 | R-2 | TASK-5 | 单测 | js_accessibility_manager.cpp:9161 |
| AC-2.4 | R-2 | TASK-5 | 单测 | js_accessibility_manager.cpp:1669 |
| AC-2.5 | R-2 | TASK-5 | 单测 | js_accessibility_manager.cpp:9235 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 跨进程组件宿主命中悬停 | SessionAdapter 子类（Form/UIExtension/Isolated/XComponent/Web/Custom）`IgnoreHostNode()` 全 true；`TransferHoverEvent` 路由到各自委托 | 仅 UIExtension/Isolated 系 `IgnoreTransformMouseEvent`=true。XComponent/Custom 的 hover 命中算法见 Feat-04，其 Provider 分发见 Feat-06 | AC-1.1, AC-1.2, AC-1.3 |
| R-2 | 行为 | 子树注册/管理 | `RegisterAccessibilityChildTreeCallback` 存入 childTreeCallbackMap_；注册成功广播 OnRegister；SetChildTreeIdAndWinId 分发；节点上报 SetChildTreeIdAndWinId/SetBelongTreeId | NeedRegisterChildTree 按 parent 三元组去重。应用自绘组件（XComponent/Custom）经此管道以 `JS_THIRD_PROVIDER` operatorType 挂载，详见 Feat-06 | AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.x（SessionAdapter） | 单测：各 adapter TransferHoverEvent/Ignore* | 6 类矩阵、IgnoreTransformMouseEvent 差异 |
| VM-2 | AC-2.x（ChildTree） | 单测：注册/反注册/广播/上报 | childTreeCallbackMap、去重 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| 无 | — | — | — | — | 子树注册/悬停转发均为框架内部接口，无独立公开 API | — |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

## 接口规格

> L1：子树注册/悬停转发为框架内部行为，无新增 Public 接口规格需展开。

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13
- **API 版本号策略:** 无独立公开 API

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| SessionAdapter 仅承载悬停转发 | 查询/动作分发不经 SessionAdapter，走 ChildTree/Provider 注册管道（应用自绘组件 Provider 见 Feat-06） | AC-1.x, AC-2.x |
| ChildTree 为共享挂载管道 | 跨进程组件与应用自绘组件均经此管道注册子树 | AC-2.x |
| Web 路径独立 | Web 不走 Provider 体系，独立 RegisterWebInteractionOperationAsChildTree + UpdateWebAccessibilityElementInfo | 见设计 R-7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 各类 SessionAdapter 与 ChildTree 注册可独立单测 | 单测 | 各 pattern accessibility_session_adapter_* |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 本特性即子树注册与跨进程接入 | 全部 |
| 多窗口/分屏 | 是 | 跨进程子树、childTreeId/windowId 编码 | AC-2.x |
| 生态兼容 | 是 | 跨进程组件接入 | AC-1.x |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（子树注册 + 跨进程悬停转发；不含字段填充 Feat-01、悬停命中 Feat-04、动作执行 Feat-02、应用自绘组件 Provider 分发 Feat-06、事件上报 Feat-07）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilitySessionAdapter 子类矩阵 Form/UIExtension/Isolated/XComponent/Web/Custom"
  - repo: "openharmony/arkui_ace_engine"
    query: "AccessibilityChildTreeCallback 注册反注册与 childTreeId/belongTreeId 管理"
```

**关键文档：** design.md（同目录）、Feat-06（应用自绘组件 NDK Provider 接入）
