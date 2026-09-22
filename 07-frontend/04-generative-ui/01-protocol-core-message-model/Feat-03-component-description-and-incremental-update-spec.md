# 特性规格

> Func-07-04-01-Feat-03 组件描述与增量更新：固化 `updateComponents` 扁平邻接表（`components[]`，每项 `id`+`component`+`children`）描述组件树、`SurfaceSlot` 跨批次增量更新（`allComponents_`/`descriptorsById_`/`parentsRelations_` 索引）、root 组件判定与重建、模板子组件延迟展开。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件描述与增量更新 |
| 特性编号 | Func-07-04-01-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-03 承接 design.md 组件增量更新章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/01-protocol-core-message-model/design.md` | Baselined |
| Surface 槽位 | `genui/src/main/cpp/SurfaceSlot.cpp` / `SurfaceSlot.h` | — |
| 消息解析 | `genui/src/main/ets/core/base/A2UIMessage.ets` | — |
| 消息格式参考（Docs） | `reference/messages.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件描述格式

**作为** 生成式 UI 宿主开发者,
**我想要** 用扁平邻接表描述组件树,
**以便** 支持流式增量更新的组件定义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `updateComponents.components` 为对象数组 THEN 消息体校验通过（`A2UIMessage.ets:126-131`） | 正常 |
| AC-1.2 | WHEN 组件项含 `id`、`component`（类型名）与可选 `children`（子 id 数组） THEN 参与组件树构建（`messages.md:55-67`） | 正常 |
| AC-1.3 | WHEN `components` 非数组 THEN 消息体校验失败（`A2UIMessage.ets:127-130`） | 异常 |

### US-2: 组件节点创建与更新

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎按组件 id 增量创建/更新节点,
**以便** 相同 id 复用在节点，避免全量重建。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `UpdateComponents` 处理组件数组 THEN `PrepareDescriptorById` 缓存邻接表描述符到 `descriptorsById_`（`SurfaceSlot.h:162`） | 正常 |
| AC-2.2 | WHEN 组件 id 已存在 THEN `GetOrCreateComponentNode` 复用既有节点（isNewNode=false），更新属性而非重建（`SurfaceSlot.h:176-177`） | 正常 |
| AC-2.3 | WHEN 组件 id 首次出现 THEN `GetOrCreateComponentNode` 新建节点（isNewNode=true）并 `RegisterComponentIfNeeded`（`SurfaceSlot.h:176-178`） | 正常 |

### US-3: root 组件与树构建

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别根组件并构建整树,
**以便** 从根节点触发渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 组件集合含被 `children` 引用但自身不是任何节点子项的节点 THEN 判定为 root 候选并构建 root（`SurfaceSlot::BuildRootFromComponents`，`SurfaceSlot.h:133-135`） | 正常 |
| AC-3.2 | WHEN `BuildComponentTree` 按深度排序（`BuildNodeDepthComparator`）构建 TH含 自底向上挂载子节点（`SurfaceSlot.h:180`） | 正常 |
| AC-3.3 | WHEN 组件引用不存在的子 id THEN 延迟挂载（模板/流式场景，待后续批次补齐） | 边界 |

### US-4: 增量更新与关系索引

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎维护父子关系索引,
**以便** 跨批次增量更新时不丢失既有关系。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 组件更新 THEN `parentsRelations_`（childId→parentId）跨批次维护父子关系（`SurfaceSlot.h:207`） | 正常 |
| AC-4.2 | WHEN 子节点被移除 THEN `RemoveOldChildren` 清理父节点旧子集（`SurfaceSlot.h:183`） | 正常 |
| AC-4.3 | WHEN 更新所有组件后 THEN `UpdateComponentsArray` 重新构建 root 并刷新渲染 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-3 | ArkTS 单测 + C++ UT | `A2UIMessage.ets:126-131` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-3 | C++ UT：GetOrCreateComponentNode | `SurfaceSlot.h:176-178` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-3 | C++ UT：BuildRootFromComponents | `SurfaceSlot.h:133-135` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-3 | C++ UT：关系索引 | `SurfaceSlot.h:207` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | updateComponents 消息 | components 数组，每项 id+component(+children) | 非数组拒绝 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | 组件 id 命中 | 复用节点更新属性；未命中新建 | isNewNode 标志 | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 行为 | 组件集合解析 | 识别 root 并按深度构建树 | 根为无父引用节点 | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 行为 | 组件更新 | 维护 parentsRelations_ 跨批次索引 | 正确处理移除 | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 描述格式 | 单测+UT | 邻接表结构 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 节点复用 | UT | id 命中复用 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 root 构建 | UT | 根识别+深度排序 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 增量索引 | UT | 跨批次关系 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`SurfaceSlot::UpdateComponents(messageBody)`（`SurfaceSlot.h:66`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool UpdateComponents(const JsonValue& messageBody)` |
| 返回值 | `bool` — 是否成功 |
| 开放范围 | 内部（C++ framework-internal） |
| 错误码 | N/A（bool 返回；失败经 native errorCode 上传） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| messageBody | JsonValue | 是 | — | 含 `components` 数组 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 组件 id 已存在 | 复用更新 | AC-2.2 |
| 2 | 组件 id 新出现 | 新建注册 | AC-2.3 |
| 3 | 含根节点 | 构建 root 树 | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 无新增 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 扁平邻接表 | 组件以 components 数组描述，children 引用 id | AC-1.1,AC-1.2,AC-1.3 |
| 跨批次索引 | parentsRelations_/descriptorsById_ 增量维护 | AC-4.1,AC-4.2,AC-4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 相同 id 复用节点避免重建 | C++ UT | `SurfaceSlot.h:176-177` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | — | ohosTest | — |
| 平板 | 无差异 | — | ohosTest | — |
| 折叠屏 | 无差异 | — | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 组件语义归 07-04-02~24 | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 是 | A2UI v0.9 邻接表兼容 | AC-1.1,AC-1.2,AC-1.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 组件描述与增量更新
  作为 生成式 UI 宿主开发者
  我想要 用扁平邻接表描述并增量更新组件树
  以便 支持流式渲染

  Scenario: 组件复用更新
    Given Surface 已存在组件 id="title"
    When 再次收到 updateComponents 含 id="title" 的新属性
    Then 复用节点更新属性而非重建

  Scenario: root 识别构建
    Given components 含 root(Column)+children[title,btn]
    When UpdateComponents
    Then 识别 root 并按深度构建子树
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（组件语义归 07-04-02~24）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceSlot UpdateComponents descriptorsById_ parentsRelations_ allComponents_ 增量更新"
  - repo: "GenerativeUI/A2UIRender"
    query: "BuildRootFromComponents root 识别 BuildComponentTree 深度排序"
```

**关键文档：** `genui/src/main/cpp/SurfaceSlot.cpp`、`genui/src/main/cpp/SurfaceSlot.h`、`genui/src/main/ets/core/base/A2UIMessage.ets`