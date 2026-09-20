# 特性规格

> Func-04-04-10-Feat-03 可见区域计算负载优化：利用 RSNode `GetIsOnTheTree()` 对已析出渲染树的节点做可见性运算剪枝，纯性能优化，对外行为与 Feat-01/02 等价。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 可见区域计算负载优化（离树节点剪枝） |
| 特性编号 | Func-04-04-10-Feat-03 |
| 所属 Epic | 无（存量能力优化） |
| 优先级 | P1 |
| 目标版本 | OpenHarmony-7.1-Release |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

> 存量特性（lineage: new-on-legacy）。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 对已析出渲染树的节点，跳过可见区域计算（祖先遍历与可见矩形裁切） | 纯性能优化，不改变两条监听接口的可观察行为 |
| MODIFIED | （无） | 无 API 签名/语义变更 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Requirement | `proposal.md` | Approved |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。

## 用户故事

### US-1: onVisibleAreaChange 离树时准确归零通知

**作为** 应用开发者，
**我想要** 组件被移出渲染树时 onVisibleAreaChange 仍给出准确的比例变化通知，
**以便** 在框架内部优化计算负载的同时，我的曝光/可见性业务逻辑不受影响。

**验收标准（AC, Acceptance Criteria）：**

| AC编号 | 验收标准 | 可观察表面 | 类型 |
|--------|----------|--------------|------|
| AC-1.1 | WHEN 注册了 onVisibleAreaChange 的组件被移出渲染树（动态改变组件或其祖先的 visibility 为 INVISIBLE/GONE，或条件渲染 false、列表项回收、导航离开）且离树前最近一次检测比例非 0 THEN 本 vsync 帧应用收到一次 isVisible=false、比例 0 的回调 | Public API（onVisibleAreaChange 回调） | 正常 |
| AC-1.2 | WHEN 注册了 onVisibleAreaChange 的组件被移出渲染树且离树前最近一次检测比例已为 0 THEN 离树后不产生任何回调通知 | Public API（onVisibleAreaChange 回调） | 边界 |
| AC-1.3 | WHEN 注册了 onVisibleAreaChange 的组件仍在渲染树 THEN 可见比例按「裁剪后轴对齐矩形面积 ÷ 组件矩形面积」计算并钳制到 [0,1]，仅当当前比例相对上次检测比例跨越任一已配置阈值时回调（上穿 isVisible=true、下穿 isVisible=false）；遮挡与透明度不改变比例、越界部分计为不可见、measureFromViewport 时改用 inner 矩形 | Public API（onVisibleAreaChange 回调） | 正常 |
| AC-1.4 | WHEN 组件从渲染树重新上树且当前比例跨越已配置阈值 THEN 产生上穿回调（isVisible=true、最终比例），不因剪枝残留状态而漏发或误发 | Public API（onVisibleAreaChange 回调） | 边界 |

### US-2: onVisibleAreaApproximateChange 离树时准确归零通知

**作为** 应用开发者，
**我想要** 组件被移出渲染树时 onVisibleAreaApproximateChange 的节流回调仍给出准确的比例通知，
**以便** 降低采样频率的同时保持曝光逻辑正确。

**验收标准（AC, Acceptance Criteria）：**

| AC编号 | 验收标准 | 可观察表面 | 类型 |
|--------|----------|--------------|------|
| AC-2.1 | WHEN 注册了 onVisibleAreaApproximateChange 的组件被移出渲染树（动态改变组件或其祖先的 visibility 为 INVISIBLE/GONE）且离树前已被通知可见 THEN 在期望更新间隔的节流采样时应用收到一次 isVisible=false、比例 0 的回调 | Public API（onVisibleAreaApproximateChange 回调） | 正常 |
| AC-2.2 | WHEN 注册了 onVisibleAreaApproximateChange 的组件离树后，节流最终采样比例与上次采样近似相等（均为 0）THEN 不产生新的近似回调 | Public API（onVisibleAreaApproximateChange 回调） | 边界 |
| AC-2.3 | WHEN 注册了 onVisibleAreaApproximateChange 的组件仍在渲染树 THEN 每个节流窗口合并频繁几何变化，仅在最终采样比例相对上次采样跨越阈值时回调一次并携带最终比例（上穿 true、下穿 false） | Public API（onVisibleAreaApproximateChange 回调） | 正常 |

### US-3: 离树组件不再拖累可见区域计算

**作为** 系统开发者（ArkUI），
**我想要** 页面存在大量离树但注册了可见区域监听的组件时，flushVsync 末尾的可见区域计算负载不随离树组件数量线性增长，
**以便** 降低热路径 CPU 占用与掉帧风险。

**验收标准（AC, Acceptance Criteria）：**

| AC编号 | 验收标准 | 可观察表面 | 类型 |
|--------|----------|--------------|------|
| AC-3.1 | WHEN 一批注册了可见区域监听（精确或近似）的组件被移出渲染树 THEN 应用不因可见区域计算出现掉帧/卡顿：flushVsync 可见区域阶段的逐帧耗时/计算计数不随离树组件数量线性增长 | 终端用户（应用流畅度，以 DFX 打点/benchmark 度量） | 正常 |
| AC-3.2 | WHEN 组件仍在渲染树 THEN 其可见区域计算与阈值判定结果不受剪枝影响（回调次数、比例与阈值判定保持不变） | Public API（onVisibleAreaChange / onVisibleAreaApproximateChange 回调） | 边界 |

## 验收追溯

| AC | 关联规则 | 可观察表面 |
|----|----------|--------------|
| AC-1.1 | R-1 | Public API（onVisibleAreaChange 回调） |
| AC-1.2 | R-2 | Public API（onVisibleAreaChange 回调） |
| AC-1.3 | R-3 | Public API（onVisibleAreaChange 回调） |
| AC-1.4 | R-4 | Public API（onVisibleAreaChange 回调） |
| AC-2.1 | R-5 | Public API（onVisibleAreaApproximateChange 回调） |
| AC-2.2 | R-6 | Public API（onVisibleAreaApproximateChange 回调） |
| AC-2.3 | R-7 | Public API（onVisibleAreaApproximateChange 回调） |
| AC-3.1 | R-8 | 终端用户（应用流畅度，以 DFX 打点/benchmark 度量） |
| AC-3.2 | R-9 | Public API（可见区域回调） |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 注册 onVisibleAreaChange 的组件被移出渲染树，且离树前最近检测比例非 0 | 本 vsync 帧回调 isVisible=false、比例 0 | 仅触发一次 | AC-1.1 |
| R-2 | 边界 | 注册 onVisibleAreaChange 的组件被移出渲染树，且离树前最近检测比例已为 0 | 不触发回调 | 无变化不通知 | AC-1.2 |
| R-3 | 行为 | 注册 onVisibleAreaChange 的组件仍在渲染树 | 比例=裁剪后轴对齐矩形面积÷组件矩形面积，钳制 [0,1]；仅阈值跨越时回调（上穿 true、下穿 false）；遮挡/透明度不计、越界计不可见、measureFromViewport 用 inner 矩形 | 比例边界 0 与 1 按端点处理 | AC-1.3 |
| R-4 | 边界 | 组件从渲染树重新上树且当前比例跨越已配置阈值 | 产生上穿回调（isVisible=true、最终比例） | 剪枝不得残留错误状态 | AC-1.4 |
| R-5 | 行为 | 注册 onVisibleAreaApproximateChange 的组件被移出渲染树，且离树前已被通知可见 | 期望更新间隔节流采样时回调 isVisible=false、比例 0 | 受 period 节流 | AC-2.1 |
| R-6 | 边界 | 注册 onVisibleAreaApproximateChange 的组件离树后，节流最终采样比例与上次采样近似相等（均为 0） | 不产生新的近似回调 | 无变化不通知 | AC-2.2 |
| R-7 | 行为 | 注册 onVisibleAreaApproximateChange 的组件仍在渲染树 | 每节流窗口合并几何变化，仅在最终采样比例相对上次采样跨越阈值时回调一次并携带最终比例 | 上穿 true、下穿 false | AC-2.3 |
| R-8 | 行为 | 一批注册了可见区域监听的组件被移出渲染树 | 这些组件不再进入可见区域计算，flushVsync 可见区域阶段耗时/计数不随离树组件数线性增长 | 性能（DFX/benchmark 验证） | AC-3.1 |
| R-9 | 边界 | 组件仍在渲染树 | 仍执行可见区域计算与阈值判定，回调结果不变 | 剪枝不误伤在树组件 | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 测试入口 | 验证方式 | Red 条件（实现前失败信号） | 通过标准 |
|------|------------|----------|----------|---------------------------|----------|
| VM-1 | R-1 / AC-1.1 | `test/unittest/core/base/frame_node_test_ng.cpp`（离树归零回调用例） | 单测 | N/A（等价性护栏：优化不改该可观察行为，实现前行为已正确；剪枝引入漏发归零回调时本用例转 Red） | 离树且离树前比例非 0 → 收到 isVisible=false、比例 0 的回调 |
| VM-2 | R-2 / AC-1.2 | `test/unittest/core/base/frame_node_test_ng.cpp` | 单测 | N/A（等价性护栏） | 离树前比例已为 0 → 无回调 |
| VM-3 | R-3 / AC-1.3 | `test/unittest/core/base/frame_node_test_ng.cpp`（在树比例/阈值用例） | 单测 | N/A（等价性护栏） | 比例计算与阈值跨越回调结果与基线一致 |
| VM-4 | R-4 / AC-1.4 | `test/unittest/core/base/frame_node_test_ng.cpp`（重新上树用例） | 单测 | N/A（等价性护栏） | 重新上树且跨越阈值 → 上穿回调正确 |
| VM-5 | R-5 / AC-2.1 | `test/unittest/core/base/frame_node_test_ng.cpp`（ThrottledVisible 离树用例） | 单测 | N/A（等价性护栏） | 节流采样时收到 isVisible=false、比例 0 |
| VM-6 | R-6 / AC-2.2 | `test/unittest/core/base/frame_node_test_ng.cpp` | 单测 | N/A（等价性护栏） | 最终采样比例与上次近似相等 → 无回调 |
| VM-7 | R-7 / AC-2.3 | `test/unittest/core/base/frame_node_test_ng.cpp`（节流取样用例） | 单测 | N/A（等价性护栏） | 节流窗口合并、阈值跨越回调一次 |
| VM-8 | R-8 / AC-3.1 | 可见区域阶段计算计数桩/DFX 打点 | 单测 + benchmark | 实现前：离树节点仍触发可见矩形计算与祖先遍历（桩计数 > 0），断言「跳过计算」的用例失败 | 离树节点计数为 0，且耗时/计数不随离树节点数线性增长 |
| VM-9 | R-9 / AC-3.2 | `test/unittest/core/base/frame_node_test_ng.cpp`（在树等价用例） | 单测 | N/A（等价性护栏） | 在树组件回调结果与阈值判定不变 |

## API 变更分析

N/A：本特性不新增、不变更、不废弃任何 Public/System/InnerAPI。`onVisibleAreaChange` 与 `onVisibleAreaApproximateChange` 均为既有 Public API，其签名与可观察语义保持不变。

### 新增 API

N/A：无新增 API。

### 变更/废弃 API

N/A：无变更、无废弃 API。

### API 与错误码事实

N/A：无 API 或错误码变更，不涉及新事实登记。两条监听接口的行为事实见存量 Feat-01 / Feat-02 规格（repos/sdd/arkui-specs/04-common-capability/04-common-events/10-visible-area-mechanism/）。

## 接口规格

> 本特性不改接口，仅在此声明受影响接口的可观察契约保持不变，作为剪枝优化的行为护栏。

| 接口 | 可观察契约（不变） | 关联 AC |
|------|--------------------|---------|
| onVisibleAreaChange | 离树归零（AC-1.1/1.2）、在树阈值跨越（AC-1.3）、重新上树恢复（AC-1.4） | US-1 |
| onVisibleAreaApproximateChange | 节流归零（AC-2.1/2.2）、节流阈值跨越（AC-2.3） | US-2 |

## 兼容性声明

- **已有 API 行为变更:** 否（两条监听接口回调次数、比例、时机均不变）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 与存量 onVisibleAreaChange / onVisibleAreaApproximateChange 一致
- **API 版本号策略:** 无新 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 剪枝判据语义等价 | 剪枝所依赖的「不在渲染树」判据必须与「该节点当前帧不可见（比例 0）」等价，不得因同帧 re-parent / transition-out / offscreen / MIXED 挂载策略产生误判（详见 design.md 专项验证） | AC-3.1 / AC-3.2 |
| 行为不漂移 | 剪枝只跳过计算，不改变比例口径、阈值穿越与回调派发语义 | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-2.1, AC-2.2, AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | flushVsync 可见区域阶段耗时/计算计数不随离树组件数量线性增长（对比基线有可量化下降） | DFX trace + benchmark | `evidence/checks/` |
| 可测试性 | 提供离树节点「跳过计算」的可观测计数（桩/DFX 打点）支撑 AC-3.1 | 单测 | `evidence/checks/` |

## 多设备适配声明

无差异：本特性为框架内部性能优化，各设备形态行为一致。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 不改变可见性语义 | — |
| 大字体 | 否 | 不改变布局/几何口径 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 行为一致 | — |
| 多用户 | 否 | 不涉及 | — |
| 版本升级 | 否 | 无 API 变更 | — |
| 生态兼容 | 否 | 回调语义不变 | — |

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "FrameNode::IsFrameDisappear / IsFrameAncestorDisappear / GetCacheVisibleRect / ThrottledVisibleTask 实现与调用链"
  - repo: "openharmony/arkui_ace_engine"
    query: "RenderContext::IsOnRenderTree 与 RSNode GetIsOnTheTree 语义、同帧 re-parent/transition-out 时序"
```

**关键文档：**
- proposal.md（本 change）
- repos/sdd/arkui-specs/04-common-capability/04-common-events/10-visible-area-mechanism/（Feat-01/02 存量规格与 design.md）
- docs/kb/issues/lifecycle/ispending-state-render-tree-diff.md
