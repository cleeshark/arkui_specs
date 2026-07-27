# 特性规格

> Func-04-02-01-Feat-04 布局安全区忽略与多阶段调度存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 布局安全区忽略与多阶段调度 |
| 特性编号 | Func-04-02-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`ignoreLayoutSafeArea` 使组件布局延伸到页级和组件级连续安全区。本特性覆盖 LayoutSafeAreaType/Edge、默认/非法/空值、START/END RTL、matchParent 尺寸语义、滚动轴过滤、SAE、延迟 Measure/Layout 调度，以及与 expandSafeArea 的顺序。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ignoreLayoutSafeArea API | 补录类型、边、默认、reset 与版本 |
| ADDED | 布局扩展规则 | 补录位置/尺寸、滚动轴、SAE 与 RTL |
| ADDED | 多阶段调度 | 补录 delayed bundle、反向刷新和 expand 优先级 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets` | 已核对 |
| Parser | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 已核对 |
| LayoutProperty | `frameworks/core/components_ng/layout/layout_property.cpp` | 已核对 |
| Scheduler | `frameworks/core/pipeline_ng/ui_task_scheduler.cpp` | 已核对 |

## 用户故事

### US-1: 选择布局安全区类型和边

**作为** 应用开发者  
**我想要** 指定布局要忽略的安全区边  
**以便** 组件扩展到连续页级或组件级安全区

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN ignoreLayoutSafeArea() 省略参数 THEN types 默认 SYSTEM，edges 默认 ALL | 正常 |
| AC-1.2 | WHEN edges 含 START/END/VERTICAL/HORIZONTAL/ALL THEN 展开为当前方向对应的物理边集合 | 正常 |
| AC-1.3 | WHEN 参数为 undefined/reset 或含非法枚举 THEN 按 parser 的默认/清除路径处理，不保存未定义 bit | 异常 |
| AC-1.4 | WHEN SDK 公共 LayoutSafeAreaType 被使用 THEN 只公开 SYSTEM；内部 KEYBOARD/ALL 不提升为公共契约 | 边界 |

### US-2: 调整位置、尺寸和滚动轴

**作为** 布局算法  
**我想要** 按布局策略消费累计安全区  
**以便** 扩展后几何保持一致

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 节点非 matchParent THEN忽略所选边主要改变位置；WHEN 对应轴为 matchParent THEN 同时改变位置和尺寸 | 正常 |
| AC-2.2 | WHEN START/END 且布局方向变化 THEN raw edges 保留，物理边重新映射并触发 Measure/Layout | 正常 |
| AC-2.3 | WHEN 节点位于 List/Grid/WaterFlow/Swiper/Tabs 等滚动场景 THEN 滚动方向不考虑滚动组件及其外层安全区 | 边界 |
| AC-2.4 | WHEN SAE 被 margin/border/padding 截断 THEN 只扩展到可检测的连续范围 | 边界 |

### US-3: 通过多阶段 Pipeline 完成布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 首轮 Measure 发现扩展约束依赖未决祖先几何 THEN 节点进入 IgnoreLayoutSafeAreaBundle 并延迟自身布局 | 边界 |
| AC-3.2 | WHEN scheduler 处理 bundle THEN 按反向依赖刷新约束并完成延迟 Measure/Layout | 正常 |
| AC-3.3 | WHEN 同时设置 ignoreLayoutSafeArea 与 expandSafeArea THEN 先完成布局安全区忽略，再基于新几何执行渲染扩展 | 正常 |
| AC-3.4 | WHEN Dynamic、Static 或 C Node 设置等价有效公开值 THEN 形成等价 raw opts；C Node 的 edge=0 表示 NONE，size>2 的额外 item 被忽略 | 正常 |
| AC-3.5 | WHEN C Node item 为 null 或 size=0 THEN 返回 PARAM_INVALID 且不写入；WHEN 非空 item 的 type!=1 THEN type 回退 SYSTEM；WHEN 第二项缺失或 edge 不在 0..15 THEN edge 回退 ALL，随后仍写入并返回 NO_ERROR | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | SDK/parser UT | `interface/sdk-js/api/@internal/component/ets/common.d.ts:9104-9205,19672-19706`; `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10011-10043` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | LayoutProperty/scroll UT | `frameworks/core/components_ng/layout/layout_property.cpp:2264-2293`; `frameworks/core/components_ng/layout/layout_wrapper.cpp:550-605` |
| AC-3.1~AC-3.5 | R-9~R-13 | 已有实现 | Scheduling/CAPI 边界测试 | `frameworks/core/pipeline_ng/ui_task_scheduler.cpp:195-227`; `interfaces/native/node/style_modifier.cpp:20272-20287`; `interfaces/native/node_attributes/layout.h:693-723` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 参数省略 | SYSTEM+ALL | Dynamic API 20 | AC-1.1 |
| R-2 | 行为 | 组合 edge | 展开为物理边集合 | START/END RTL 镜像 | AC-1.2 |
| R-3 | 异常 | undefined/reset/非法值 | 默认、清除或拒绝 | 不保留非法 bit | AC-1.3 |
| R-4 | 边界 | 公共 type 查询 | 仅 SYSTEM | 内部 KEYBOARD/ALL 非 Public | AC-1.4 |
| R-5 | 行为 | 非 matchParent/matchParent | 分别改变位置/位置+尺寸 | 按对应轴判断 | AC-2.1 |
| R-6 | 行为 | 方向变化 | raw edge 重映射并标脏 | 使用最新 RTL | AC-2.2 |
| R-7 | 边界 | 滚动方向 | 排除滚动组件外层范围 | 非滚动轴正常计算 | AC-2.3 |
| R-8 | 边界 | SAE 链中断 | 停在最后连续边界 | 不跨 margin/border/padding | AC-2.4 |
| R-9 | 恢复 | 约束依赖未决 | 延迟并登记 bundle | 不提交未决几何 | AC-3.1 |
| R-10 | 行为 | scheduler 消费 bundle | 反向刷新后完成布局 | 保持依赖序 | AC-3.2 |
| R-11 | 行为 | 同时 ignore+expand | ignore 先，expand 后 | 新几何作为基准 | AC-3.3 |
| R-12 | 行为 | 多入口/有效 C item | 等价保存 raw opts；edge=0 保持 NONE，额外 item 忽略 | SDK 公共枚举为准 | AC-3.4 |
| R-13 | 异常 | C item 为空、size=0 或字段越界 | 空/零长度返回 PARAM_INVALID；非空非法 type/edge 分别回退 SYSTEM/ALL 后写入并返回 NO_ERROR | C API 为逐字段默认策略，不是统一拒绝 | AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | Parser/SDK 枚举 UT | 默认、组合边、内部差异 |
| VM-2 | AC-2.1~AC-2.4 | `ignore_layout_safe_area_scheduling_test_ng.cpp` | matchParent、RTL、滚动、SAE |
| VM-3 | AC-3.1~AC-3.3 | Pipeline bundle UT | 延迟和优先级 |
| VM-4 | AC-3.4~AC-3.5 | Static/C Node 边界测试 | 通道等价、NONE/额外 item、空 item 错误与非空非法字段默认写入 |

## API 变更分析

### 新增 API

N/A，`ignoreLayoutSafeArea` 为 Dynamic API 20、Static/C Node API 23 已有能力。

### 变更/废弃 API

N/A；内部额外枚举不作为 API 变更。

## 接口规格

### 接口定义

**ignoreLayoutSafeArea(types?, edges?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ignoreLayoutSafeArea(types?: Array<LayoutSafeAreaType>, edges?: Array<LayoutSafeAreaEdge>): T` |
| 返回值 | T — 当前组件 |
| 开放范围 | Public |
| 错误码 | ArkTS N/A；C Node 使用既有 attribute result |
| 关联 AC | AC-1.1~AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| types | LayoutSafeAreaType[] | 否 | SYSTEM | Public 只声明 SYSTEM |
| edges | LayoutSafeAreaEdge[] | 否 | ALL | TOP/BOTTOM 自 API 12；组合边自 API 20 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | matchParent + ALL | 位置和尺寸扩展到连续 SAE | AC-2.1, AC-2.4 |
| 2 | 同时 expand | ignore 完成后再扩 paint rect | AC-3.3 |
| 3 | C item 非空但 type/edge 越界 | 分别回退 SYSTEM/ALL，写入并返回 NO_ERROR | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 是；LayoutSafeAreaEdge TOP/BOTTOM 自 API 12，组合边与 ignoreLayoutSafeArea 自 API 20，Static/C Node 自 API 23。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 20（公开 ignoreLayoutSafeArea）。
- **API 版本号策略:** API 12/20/23 全量记录；内部类型不扩展公共契约。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| raw edge 保留 | START/END 在 LayoutProperty 阶段按方向映射 | AC-2.2 |
| 多阶段调度 | 未决约束必须进入 scheduler bundle | AC-3.1 |
| 优先级 | ignoreLayoutSafeArea 先于 expandSafeArea | AC-3.3 |
| SDK 权威 | Public type 仅 SYSTEM | AC-1.4 |
| C 入口错误策略 | 仅 null/size=0 拒绝；非空非法字段按默认值写入 | AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 仅有依赖未决节点进入附加调度 | Trace | `frameworks/core/pipeline_ng/ui_task_scheduler.cpp:195-227` |
| 功耗 | 无后台任务 | 审查 | VM-3 |
| 内存 | bundle 生命周期限于当前 Pipeline 帧 | 生命周期 UT | VM-3 |
| 安全 | 不涉及权限或用户数据 | API 审查 | VM-1 |
| 可靠性 | 循环/失效节点不提交未决几何 | 调度 UT | VM-3 |
| 可测试性 | 方向、滚动轴和依赖树可参数化 | UT | VM-1~VM-4 |
| 自动化维测 | scheduler bundle 和 opts 可 Dump | Trace | AC-3.2 |
| 定界定位 | parser/property/wrapper/scheduler 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 状态栏和键盘场景多 | 按连续 SAE 扩展 | 真机测试 | AC-2.4 |
| 平板 | 滚动/多窗口复杂 | 滚动轴过滤 | 多窗口测试 | AC-2.3 |
| 折叠屏 | RTL/姿态/根尺寸变化 | raw edge 重映射和重测 | 折叠态测试 | AC-2.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 几何改变但语义树不变 | AC-2.1 |
| 大字体 | 是 | layout policy 和 SAE 可重算 | AC-2.1 |
| 深色模式 | 否 | 不涉及颜色 | VM-1 |
| 多窗口/分屏 | 是 | 每个窗口独立调度 | AC-3.2 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | API 20/23 和内部枚举差异需回归 | AC-1.4 |
| 生态兼容 | 是 | ignore/expand 顺序固定 | AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 布局安全区忽略
  Scenario: ignore 与 expand 同时设置
    Given 组件设置 ignoreLayoutSafeArea 和 expandSafeArea
    When Pipeline 完成多阶段测量布局
    Then 先扩展布局几何再基于新边界扩展绘制区域
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 全边形式、RTL、matchParent、滚动和调度明确
- [x] SDK/内部枚举偏差显式记录
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ignoreLayoutSafeArea scheduling matchParent RTL SAE"
  - repo: "openharmony/interface_sdk-js"
    query: "LayoutSafeAreaType LayoutSafeAreaEdge ignoreLayoutSafeArea"
```

**关键文档：** `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md`
