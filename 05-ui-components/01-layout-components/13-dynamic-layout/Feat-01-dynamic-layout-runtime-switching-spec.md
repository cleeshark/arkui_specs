# 特性规格

> Func-05-01-13-Feat-01 DynamicLayout 容器创建与运行时算法切换：补录稳定节点创建/复用、算法类型到 Pattern 的映射、同类型参数更新、异类型 ReplacePattern、子组件状态保持和非法算法 Stack 回退。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DynamicLayout 容器创建与运行时算法切换 |
| 特性编号 | Func-05-01-13-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

DynamicLayout 接收一个 `LayoutAlgorithm` 对象并在运行时映射到 Row、Column、Stack、Grid 或 Custom Pattern。`DynamicLayoutNode` 在算法切换时保持 node id 和子树；只有类型变化时替换 Pattern，同类型参数变化只更新属性并标记 Measure。无效算法按 SDK 回退为 Center 对齐的 Stack。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | DynamicLayout 创建与稳定节点规格 | 覆盖 API 24 Dynamic/Static 构造和子组件支持 |
| ADDED | 运行时算法切换规格 | 覆盖五种类型、同类型更新、异类型 Pattern 替换和状态保持 |
| ADDED | 无效算法与生命周期恢复规格 | 覆盖 Stack Center 回退、节点复用、销毁和旧回调隔离 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/13-dynamic-layout/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.static.d.ets` | 已核对 |
| Model/Node | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp`、`frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_node.cpp` | 已核对 |
| Dynamic bridge | `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp` | 已核对 |

> LazyDynamicLayout 与 NDK 明确不在本 Feat；即使共享相邻模块也不得注册为本功能域能力。

## 用户故事

### US-1: 创建可切换算法的容器

**作为** ArkUI 应用开发者  
**我想要** 用一个容器承载可变布局策略  
**以便** 无需条件重建子树即可响应界面模式变化

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API 24 调用 `DynamicLayout(algorithm)` THEN 创建/复用 tag 为 DynamicLayout 的 FrameNode，并允许内容 builder 构建多个子组件 | 正常 |
| AC-1.2 | WHEN algorithm 为 Row、Column、Stack、Grid 或 CustomLayoutAlgorithm THEN Model 选择对应 Pattern/Property/Algorithm 生产路径 | 正常 |
| AC-1.3 | WHEN DynamicLayout 支持的通用属性或事件被设置 THEN 由其 CommonMethod 能力正常处理，不因当前 preset 类型丢失外层节点属性 | 正常 |
| AC-1.4 | WHEN 容器没有子组件 THEN 当前算法仍产生合法非负容器几何，不访问不存在的 child | 边界 |

### US-2: 在运行时切换布局算法并保持子组件状态

**作为** 响应式界面开发者  
**我想要** 通过更新 LayoutAlgorithm 对象切换布局  
**以便** 保持输入、滚动或自定义子组件状态

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 算法类型从一种公开类型切换为另一种 THEN `DynamicLayoutNode` 保持同一 node id 和现有子节点，替换为新类型 Pattern 并标记重新测量 | 正常 |
| AC-2.2 | WHEN 同一算法类型仅 options/`@Trace` 字段改变 THEN 不替换 Pattern，只更新对应 Property/params 并触发下一次 Measure/Layout | 正常 |
| AC-2.3 | WHEN 切换完成 THEN 子节点声明身份、应用状态和相对 UI 树归属保持，几何按新算法重新计算 | 正常 |
| AC-2.4 | WHEN 短时间连续 Row→Grid→Custom→Stack 切换 THEN 最终节点只使用最新有效类型，旧 Pattern/callback 不得覆盖最新几何 | 边界 |
| AC-2.5 | WHEN 切换发生在当前布局阶段之外的状态更新 THEN 由后续 Pipeline 执行，不同步重入正在运行的 Measure/Layout | 边界 |

### US-3: 对无效算法安全回退

**作为** 使用动态数据选择算法的开发者  
**我想要** 非法输入仍得到确定布局  
**以便** 页面不会因算法对象异常而空白或崩溃

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN algorithm 为无法识别的对象、undefined/null 或解析失败 THEN Bridge/Model 选择 DEFAULT_LAYOUT，子组件按 Center 对齐的 Stack 叠放 | 异常 |
| AC-3.2 | WHEN 有效算法运行后更新为无效算法 THEN 容器切换到默认 Stack，而不是静默沿用上一个算法 | 异常 |
| AC-3.3 | WHEN 旧 Pattern、VM 或 callback 在切换/销毁后失效 THEN 迟到访问安全退出，不持有已销毁节点或脚本上下文 | 异常 |
| AC-3.4 | WHEN DynamicLayout 节点被移除后以新 node id 创建 THEN 新节点按新输入初始化，不继承已销毁节点的算法私有状态 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Model/Node 创建 UT | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_node.cpp:21-39`; `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:92-114,156-199`; `test/unittest/core/pattern/dynamiclayout/dynamic_layout_model_test_ng.cpp:69-220` |
| AC-2.1~AC-2.5 | R-5~R-9 | 已有实现 | ReplacePattern/状态保持 UT | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:116-199`; `test/unittest/core/pattern/dynamiclayout/frame_node_test_dynamic_layout.cpp:61-162` |
| AC-3.1~AC-3.4 | R-10~R-13 | 已有实现 | 非法对象/销毁/重建 UT | `frameworks/core/components_ng/pattern/dynamiclayout/bridge/arkts_native_dynamic_layout_bridge.cpp:446-467,510-531`; `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:92-114` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | DynamicLayout 创建 | GetOrCreate 稳定 DynamicLayoutNode | API 24 | AC-1.1 |
| R-2 | 行为 | 五种公开算法对象 | 映射到 Row/Column/Stack/Grid/Custom Pattern | 不含 LazyDynamicLayout | AC-1.2 |
| R-3 | 行为 | 通用属性/事件 | 作用于稳定外层 FrameNode | 不依赖当前 Pattern 类型 | AC-1.3 |
| R-4 | 边界 | 无 child | 当前算法输出合法空容器几何 | 不迭代空 child | AC-1.4 |
| R-5 | 行为 | algorithm type 改变 | ReplacePattern、保留 node/children、标记 Measure | 新 Pattern 以新 params 初始化 | AC-2.1 |
| R-6 | 行为 | 同 type 参数改变 | 更新现有 Pattern/Property，不 ReplacePattern | 必须触发布局更新 | AC-2.2 |
| R-7 | 行为 | 切换布局完成 | 子组件状态/身份保持，Geometry 按新算法更新 | 不重建应用子树 | AC-2.3 |
| R-8 | 边界 | 连续多次切换 | 最终类型和参数以最后有效输入为准 | 旧状态不得回写 | AC-2.4 |
| R-9 | 边界 | 布局中收到状态更新 | 下一 Pipeline 周期处理 | 禁止当前算法重入 ReplacePattern | AC-2.5 |
| R-10 | 异常 | algorithm 解析失败 | 使用 Stack Center 默认布局 | 不抛异常/不空布局 | AC-3.1 |
| R-11 | 恢复 | 有效算法变无效 | 显式切换默认 Stack | 不沿用旧算法 | AC-3.2 |
| R-12 | 异常 | 旧 Pattern/VM/callback 失效 | 弱上下文校验失败后退出 | 不延长生命周期 | AC-3.3 |
| R-13 | 边界 | 节点销毁后新建 | 按新 node id 和当前输入初始化 | 不继承私有状态 | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | Model/Node UT | 稳定节点、五种类型、通用属性和空 child |
| VM-2 | R-5~R-7, AC-2.1~AC-2.3 | ReplacePattern + 子状态 UT | node id/child identity、Pattern 类型、dirty 和 Geometry |
| VM-3 | R-8~R-9, AC-2.4~AC-2.5 | 快速切换/管线时序 UT | last-write wins、无重入 |
| VM-4 | R-10~R-13, AC-3.1~AC-3.4 | fuzz/销毁/重建 UT | Stack Center 回退、旧回调隔离和干净新节点 |

## API 变更分析

> 本文档补录 API 24 已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `DynamicLayout(algorithm: LayoutAlgorithm)` | Public Dynamic | 五类 LayoutAlgorithm | `DynamicLayoutAttribute` | N/A | 创建可运行时切换算法的容器 | AC-1.1~AC-3.4 |
| Static `DynamicLayout(algorithm, content_?)` | Public Static | LayoutAlgorithm + content builder | `DynamicLayoutAttribute` | N/A | Static 构造同等容器 | AC-1.1~AC-3.4 |
| `LayoutAlgorithm` | Public type | marker interface | N/A | N/A | 五类算法对象的共同输入类型 | AC-1.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | API 24 首次提供，本轮仅存量补录 | 无需迁移 | AC-1.1~AC-3.4 |

## 接口规格

### 接口定义

**DynamicLayout(algorithm)**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic `(algorithm: LayoutAlgorithm): DynamicLayoutAttribute`；Static `(algorithm: LayoutAlgorithm, content_?: CustomBuilder): DynamicLayoutAttribute` |
| 返回值 | DynamicLayoutAttribute |
| 开放范围 | Public、Stage、crossplatform/form/atomicservice，API 24 |
| 错误码 | N/A；无效 algorithm 回退 Stack Center |
| 关联 AC | AC-1.1~AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| algorithm | LayoutAlgorithm | 是 | 无效时 StackLayoutAlgorithm Center | 公开实现为 Row/Column/Stack/Grid/Custom |
| content_ | CustomBuilder | Static 可选 | 无 child | 构建 DynamicLayout 子组件 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 首次有效算法 | 创建稳定节点并安装对应 Pattern | AC-1.1, AC-1.2 |
| 2 | 同类型字段变化 | 更新属性、节点与 Pattern 保持 | AC-2.2 |
| 3 | 异类型变化 | ReplacePattern，子节点状态保持 | AC-2.1, AC-2.3 |
| 4 | 无效算法 | Stack Center 回退 | AC-3.1, AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否；Dynamic/Static 均为 API 24。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否；节点/算法状态不持久化。
- **最低支持版本:** API 24。
- **API 版本号策略:** DynamicLayout 和五类 LayoutAlgorithm 统一遵循 SDK API 24；不向下模拟。

| 表面 | 版本 | 证据 |
|------|------|------|
| Dynamic | API 24 | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts:22-110` |
| Static | API 24 | `interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.static.d.ets:27-64` |
| 五类 LayoutAlgorithm | API 24 | `interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts:24-688` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 节点身份稳定 | 算法切换不得重建 DynamicLayoutNode 或应用子树 | AC-2.1~AC-2.4 |
| Pattern 按类型负责 | 不建立一个越权实现全部布局逻辑的万能算法 | AC-1.2, AC-2.1 |
| 默认回退确定 | 任何无法识别算法均为 Stack Center | AC-3.1, AC-3.2 |
| Pipeline 更新 | 参数/类型变化通过 Measure dirty 在后续管线生效 | AC-2.1, AC-2.2, AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 同类型更新不替换 Pattern；异类型切换不重建子树 | Trace/切换基准 | `frameworks/core/components_ng/pattern/dynamiclayout/dynamic_layout_model_ng.cpp:116-199` |
| 功耗 | 只有状态/算法变化触发重新布局，无后台任务 | 帧计数 | VM-2, VM-3 |
| 内存 | ReplacePattern 释放旧 Pattern，稳定节点只持有当前实现 | 泄漏/生命周期 UT | AC-2.1, AC-3.3 |
| 安全 | 无权限/敏感数据；非法对象安全回退 | fuzz/代码审查 | AC-3.1 |
| 可靠性 | 连续切换、空 child、销毁和旧回调不得崩溃 | 压力 UT | AC-1.4, AC-2.4, AC-3.3 |
| 可测试性 | node id、Pattern type、child identity 和 dirty 可直接断言 | NG UT | VM-1~VM-4 |
| 自动化维测 | 可 dump 当前算法类型、node id 和 Pattern | Inspector/trace | Node/Pattern |
| 定界定位 | 区分 Bridge 识别、Model 映射、Node 替换和具体 Algorithm | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无专有差异 | 按窗口约束执行当前算法 | 多尺寸切换测试 | AC-2.1~AC-2.3 |
| 平板 | 无专有差异 | 适合运行时 Row/Grid 切换，但语义不变 | 大窗口测试 | AC-2.4 |
| 折叠屏 | 折叠/展开可驱动应用切换算法 | DynamicLayout 自身只执行最新算法并保留状态 | 姿态切换测试 | AC-2.1~AC-2.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 切换不重建子组件身份，几何/遍历规则随具体算法 | AC-2.3 |
| 大字体 | 是 | 字体变化触发当前算法重新测量 | AC-2.2 |
| 深色模式 | 否 | 不涉及颜色 | N/A |
| 多窗口/分屏 | 是 | 应用可随窗口模式切换算法，节点状态保持 | AC-2.1~AC-2.4 |
| 多用户 | 否 | 无持久用户状态 | N/A |
| 版本升级 | 是 | API 24 之前接口不可见 | AC-1.1 |
| 生态兼容 | 是 | 无效算法 Stack Center 回退和状态保持是关键契约 | AC-2.3, AC-3.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DynamicLayout 运行时算法切换
  Scenario: Row 切换 Grid 保持子组件
    Given DynamicLayout 使用 RowLayoutAlgorithm
    And 子组件已有输入状态
    When algorithm 更新为 GridLayoutAlgorithm
    Then DynamicLayoutNode id 不变
    And 子组件身份与输入状态不变
    And 当前 Pattern 变为 Grid 对应类型并重新布局

  Scenario: 同类型只更新参数
    Given 当前为 RowLayoutAlgorithm
    When space 发生变化
    Then 不替换 Pattern
    And 下一次 Measure 使用新 space

  Scenario: 无效算法回退
    Given algorithm 无法识别
    When 创建或更新 DynamicLayout
    Then 子项按 Center Stack 叠放
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖容器创建、算法切换、状态保持和默认回退
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] LazyDynamicLayout 与 NDK 明确排除

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DynamicLayoutNode ReplacePattern SetParams DEFAULT_LAYOUT preserve children state"
  - repo: "openharmony/interface_sdk-js"
    query: "DynamicLayout LayoutAlgorithm runtime switch child state invalid StackLayoutAlgorithm API 24"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@ohos.arkui.components.ArkDynamicLayout.d.ts`
- LayoutAlgorithm SDK：`interface/sdk-js/api/arkui/LayoutAlgorithm.d.ts`
- 架构设计：`05-ui-components/01-layout-components/13-dynamic-layout/design.md`
