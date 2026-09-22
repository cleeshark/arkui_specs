# 特性规格

> Func-07-04-01-Feat-05 流式渐进渲染：固化 JSONL 流式传输下边接收边渲染的渐进式语义——每条完整 JSON 消息独立 `handleMessage` 处理、`updateComponents`/`updateDataModel` 可多次增量发送、跨批次关系索引复用未变节点、首帧延迟依赖组件邻接表增量而非全量重建。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 流式渐进渲染 |
| 特性编号 | Func-07-04-01-Feat-05 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-05 承接 design.md 流式渲染语义（依托 Feat-03/Feat-04 增量能力） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/01-protocol-core-message-model/design.md` | Baselined |
| 控制器实现 | `genui/src/main/ets/core/base/SurfaceControllerImpl.ets` | — |
| Surface 槽位 | `genui/src/main/cpp/SurfaceSlot.cpp` / `SurfaceSlot.h` | — |
| 术语/概念（Docs） | `glossary.md`、`introduction/what-is-genui.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 逐条消息处理

**作为** 生成式 UI 宿主开发者,
**我想要** 流式响应逐条转发给引擎,
**以便** 边接收边渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 每条完整 JSON 消息（JSONL 一行）传入 `handleMessage` THEN 独立解析处理（`SurfaceControllerImpl.ets:683`） | 正常 |
| AC-1.2 | WHEN 多条 `updateComponents` 依次发送 THEN 每条独立增量更新（不要求一次性全量） | 正常 |
| AC-1.3 | WHEN 处理完成后 THEN `CrossLanguageAttributeBridge.flushPending` 冲刷跨语言属性（`SurfaceControllerImpl.ets:873`） | 正常 |

### US-2: 增量更新复用未变节点

**作为** 生成式 UI 宿主开发者,
**我想要** 后续批次只更新变化节点,
**以便** 减少重渲染开销。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 后续 `updateComponents` 含既有 id THEN 复用节点更新属性（`SurfaceSlot.h:176-177`） | 正常 |
| AC-2.2 | WHEN 后续 `updateComponents` 含新 id THEN 仅新建新节点（`SurfaceSlot.h:176`） | 正常 |
| AC-2.3 | WHEN 跨批次关系经 `parentsRelations_`/`descriptorsById_` 保留 THEN 已构建子树不重建（`SurfaceSlot.h:207-208`） | 正常 |

### US-3: 数据模型流式更新

**作为** 生成式 UI 宿主开发者,
**我想要** 数据模型增量更新后即时刷新绑定,
**以便** 流式数据变化即时反映到 UI。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 流式 `updateDataModel` 逐条到达 THEN 逐条 `ProcessUpdate` 并 `NotifyPathUpdate`（`DataModel.h:72,82`） | 正常 |
| AC-3.2 | WHEN 同一 path 多次更新 THEN 最后一次值生效（幂等覆盖） | 正常 |

### US-4: 首帧与边界

**作为** 生成式 UI 宿主开发者,
**我想要** 首帧尽早渲染,
**以便** 用户感知延迟低。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 首条 `createSurface`+`updateComponents` 到达 THEN 即可构建 root 渲染（不等待后续批次） | 正常 |
| AC-4.2 | WHEN 组件引用尚未到达的子 id THEN 延迟挂载（待后续批次补齐），不阻塞当前渲染 | 边界 |
| AC-4.3 | WHEN 流式消息中间出现非法消息 THEN 该条报错不影响后续合法消息继续处理 | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-5 | ohosTest：多消息流式 | `SurfaceControllerImpl.ets:683,873` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-5 | C++ UT：跨批次复用 | `SurfaceSlot.h:176-208` |
| AC-3.1,AC-3.2 | R-3 | T-5 | C++ UT：流式数据 | `DataModel.h:72,82` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-5 | ohosTest：首帧/延迟挂载 | `SurfaceSlot.h:133-142` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 每条完整 JSON 消息 | 独立 handleMessage 处理 | JSONL 逐行 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | 增量组件批次 | 复用既有 id、新建新 id | 跨批次索引保留 | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 行为 | 流式数据更新 | 逐条 ProcessUpdate+通知 | 同 path 幂等覆盖 | AC-3.1,AC-3.2 |
| R-4 | 边界 | 首帧/延迟子节点 | 尽早渲染 + 延迟挂载缺省子 | 非法消息隔离 | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 逐条处理 | ohosTest | JSONL 逐行 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 节点复用 | UT | 跨批次 |
| VM-3 | AC-3.1,AC-3.2 数据流式 | UT | 幂等覆盖 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 首帧 | ohosTest | 首帧/延迟挂载 |

## API 变更分析

> 存量补录，无新增/变更 API。流式语义由 `handleMessage` 复用现有接口实现。

### 新增 API

N/A。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`SurfaceController.handleMessage(dsl)`（流式复用）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `handleMessage(dsl: string): void` |
| 返回值 | `void` |
| 开放范围 | Public（ArkTS） |
| 错误码 | 见 Feat-01/Feat-02 |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 多条 updateComponents | 逐条增量更新 | AC-1.2 |
| 2 | 既有 id | 复用更新 | AC-2.1 |
| 3 | 首帧 | 尽早渲染 | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 无新增 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| JSONL 逐行 | 每条完整 JSON 独立处理 | AC-1.1,AC-1.2,AC-1.3 |
| 邻接表增量 | 跨批次索引复用 | AC-2.1,AC-2.2,AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 首帧延迟低（增量而非全量） | ohosTest | `SurfaceSlot.h:176-177` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | — | ohosTest | — |
| 平板 | 无差异 | — | ohosTest | — |
| 折叠屏 | 无差异 | — | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | — | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | 多 Surface 见 Feat-06 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 是 | JSONL 流式为 A2UI 惯例 | AC-1.1,AC-1.2,AC-1.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 流式渐进渲染
  作为 生成式 UI 宿主开发者
  我想要 流式消息边接收边渲染
  以便 首帧延迟低

  Scenario: 多批次增量渲染
    Given 已处理 createSurface + 首条 updateComponents（root+title）
    When 收到第二条 updateComponents（新增 btn）
    Then 复用 title 节点、新建 btn 节点，不重建 root
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（流式语义依托 Feat-03/04 增量能力）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "handleMessage 流式 JSONL 逐条处理 增量更新"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceSlot 跨批次复用 parentsRelations_ descriptorsById_"
```

**关键文档：** `genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/cpp/SurfaceSlot.cpp`