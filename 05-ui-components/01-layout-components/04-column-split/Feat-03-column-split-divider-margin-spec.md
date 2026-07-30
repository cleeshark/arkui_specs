# 特性规格

> Func-05-01-04-Feat-03 ColumnSplit 分隔线边距存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ColumnSplit 分隔线边距 |
| 特性编号 | Func-05-01-04-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

`divider` 以 startMargin/endMargin 定义水平分隔线与上下子项之间的距离，并参与测量、绘制及拖拽有效空间计算；本特性同时记录 Dynamic/Static 输入校验差异、`childrenDragPos_` 为空时的首轮布局偏差及 legacy 空实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | divider 参数规格 | 补录 start/end margin 解析、默认值和非法值 |
| ADDED | 资源与单位规格 | 补录 Resource 重载、LPX 和资源刷新 |
| ADDED | legacy 风险 | 记录旧 Model 的 SetDivider 空实现 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/04-column-split/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/column_split.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/columnSplit.static.d.ets` | 已核对 |
| Model | `frameworks/core/components_ng/pattern/linear_split/linear_split_model_ng.cpp` | 已核对 |
| Legacy Model | `frameworks/core/components_ng/pattern/linear_split/linear_split_model_impl.cpp` | 已核对 |

## 用户故事

### US-1: 配置分隔线两侧间距

**作为** 应用开发者  
**我想要** 为水平分隔线配置 start/end margin  
**以便** 控制分隔线与上下内容的视觉及交互距离

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN divider 接收合法 startMargin/endMargin THEN 两个值写入 LayoutProperty 并触发重新测量 | 正常 |
| AC-1.2 | WHEN 任一 margin 缺失 THEN 缺失边使用 0vp，已提供边保持解析结果 | 边界 |
| AC-1.3 | WHEN divider 为 null 或 undefined/reset THEN 两侧 margin 恢复 0vp | 边界 |
| AC-1.4 | WHEN Dynamic 输入为任意 Number（含负值、NaN、Infinity）THEN 当前 ParseJsDimensionVp 不做范围/有限性检查并下发解析结果；WHEN Static/CAPI 输入负 Dimension THEN 当前路径保留该负值；仅解析失败或空 optional 走 0vp/default | 异常 |
| AC-1.5 | WHEN API>=10 布局开始时 childrenDragPos_ 为空且 startMargin>0 THEN index>0 子项当前实现累计两次 startMargin；WHEN childrenDragPos_ 已初始化 THEN 后续布局只累计一次 | 异常 |
| AC-1.6 | WHEN API>=10 为最后一个有效子项计算 ColumnSplitChildConstrain THEN 当前 `index == visibleChildCount_` 的 end-only 分支不可达，末项进入 start+end margin 约束分支 | 异常 |

### US-2: 保持资源、单位和实现通道兼容

**作为** 框架维护者  
**我想要** 各入口对同一间距形成可追溯行为  
**以便** 资源变化和版本升级不产生静默差异

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN margin 使用 Resource THEN 资源重载后重新解析并标记 Measure | 正常 |
| AC-2.2 | WHEN margin 使用 LPX THEN 按当前 Pipeline 比例转换为像素参与布局 | 正常 |
| AC-2.3 | WHEN Dynamic、Static 或 Modifier 设置相同值 THEN NG 路径得到等价 ColumnSplitDivider | 正常 |
| AC-2.4 | WHEN 应用运行于 legacy pipeline THEN SDK 声明的 divider 进入空 SetDivider 实现；该差异作为兼容风险保留 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.6 | R-1~R-4, R-9~R-10 | 已有实现 | Modifier/Layout 边界测试 | `frameworks/core/components_ng/pattern/linear_split/bridge/arkts_native_column_split_bridge.cpp:97-117`; `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_algorithm.cpp:410-493` |
| AC-2.1~AC-2.3 | R-5~R-7 | 已有实现 | Resource/LPX/CAPI UT | `test/unittest/core/pattern/linear_split/linear_split_lpx_test_ng.cpp:57-80`; `test/unittest/capi/modifiers/column_split_modifier_test.cpp:77-155` |
| AC-2.4 | R-8 | 已有实现 | 代码审查 | `frameworks/core/components_ng/pattern/linear_split/linear_split_model_impl.cpp:58-60` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 两侧值合法 | 写入 divider 并标记 Measure | start/end 独立 | AC-1.1 |
| R-2 | 边界 | 一侧缺失 | 缺失侧取 0vp | 不覆盖合法侧 | AC-1.2 |
| R-3 | 恢复 | null/undefined/reset | 两侧恢复 0vp | 与默认一致 | AC-1.3 |
| R-4 | 异常 | 负值/NaN/Infinity/解析失败 | Dynamic 对 Number 缺少范围/有限性校验；Static/CAPI 保留负值；解析失败/空 optional 才走默认 | 与 SDK 的非法值默认契约存在偏差 | AC-1.4 |
| R-5 | 行为 | Resource 有效且变化 | 重载并触发测量 | 节点仍有效 | AC-2.1 |
| R-6 | 行为 | 单位为 LPX | 使用 Pipeline 比例转换 | 无 Pipeline 时安全回退 | AC-2.2 |
| R-7 | 行为 | NG 多入口等值设置 | 形成等价 LayoutProperty | 类型转换以 SDK 为准 | AC-2.3 |
| R-8 | 边界 | legacy pipeline | SetDivider 不写入属性 | 显式记录风险 | AC-2.4 |
| R-9 | 异常 | childrenDragPos_ 为空且 startMargin>0 | index>0 首轮累计两次 startMargin | 属性变化清空数组后可再次触发；后续布局一次 | AC-1.5 |
| R-10 | 异常 | 最后一个有效子项约束 | 进入 start+end 分支 | end-only 判断使用 `index == visibleChildCount_`，对合法索引不可达 | AC-1.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.6 | Dynamic/Static/CAPI 与两轮布局对照 | 负值/非有限输入、reset、childrenDragPos 空/非空 offset 差及末项约束分支 |
| VM-2 | AC-2.1~AC-2.2 | Resource/LPX UT | 重载和单位转换 |
| VM-3 | AC-2.3~AC-2.4 | 多入口对比/legacy 审查 | NG 等价与偏差 |

## API 变更分析

### 新增 API

N/A，`divider` 为 API 10 起已有接口。

### 变更/废弃 API

N/A；legacy 空实现作为风险，不改变 SDK 声明。

## 接口规格

### 接口定义

**divider(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `divider(value: ColumnSplitDividerStyle | null): ColumnSplitAttribute` |
| 返回值 | ColumnSplitAttribute — 当前属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4, AC-1.5~AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ColumnSplitDividerStyle/null | 是 | null | null/reset 将两侧设为 0vp |
| startMargin | Dimension | 否 | 0vp | SDK 非法值使用默认值；当前 Dynamic 未校验 Number 的范围/有限性，Static/CAPI 接受负 Dimension；可为 Resource/LPX |
| endMargin | Dimension | 否 | 0vp | SDK 非法值使用默认值；当前 Dynamic 未校验 Number 的范围/有限性，Static/CAPI 接受负 Dimension；可为 Resource/LPX |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 两侧合法 | 参与布局和拖拽有效空间 | AC-1.1 |
| 2 | null/解析失败 | 重置或回退 0vp | AC-1.3, AC-1.4 |
| 3 | childrenDragPos 为空且 startMargin>0 | index>0 当前实现累计两次 startMargin | AC-1.5 |
| 4 | 最后一个有效子项 | 当前进入 start+end margin 约束而非 end-only 分支 | AC-1.6 |

## 兼容性声明

- **已有 API 行为变更:** 是；NG 实现有效，legacy `SetDivider` 当前为空实现；Dynamic/Static 对负值和非有限值的校验未统一且偏离 SDK 非法值默认契约。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 10。
- **API 版本号策略:** Dynamic API 10，Static API 23，Builder API 26；存量偏差不修改。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| Measure 脏标记 | divider 修改必须触发 PROPERTY_UPDATE_MEASURE | AC-1.1 |
| 资源生命周期 | Resource 重载回调随节点有效期管理 | AC-2.1 |
| 契约优先级 | Public API 以 SDK 为准，source 偏差进入风险 | AC-2.4 |
| 已知布局偏差 | childrenDragPos 为空时 startMargin 对 index>0 累计两次 | AC-1.5 |
| 末项约束偏差 | end-only 分支不可达，最后一项使用 start+end margin | AC-1.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 设置或资源更新仅触发一次 Measure dirty | Trace | `frameworks/core/components_ng/pattern/linear_split/linear_split_layout_property.h:68-69` |
| 功耗 | 无后台任务 | 代码审查 | VM-1 |
| 内存 | 仅保存两侧 Dimension 与资源回调 | 内存审查 | VM-2 |
| 安全 | Resource 解析不涉及权限 | API 审查 | VM-2 |
| 可靠性 | 负值/非有限输入可能进入像素换算；首轮 startMargin 存在双累计，需以风险用例锁定 | 边界测试 | VM-1, VM-2 |
| 可测试性 | LayoutProperty 可直接读取 | 单元测试 | VM-1 |
| 自动化维测 | Inspector 可观察 divider 值 | Inspector | AC-1.1 |
| 定界定位 | SDK/bridge/model/property 分层证据明确 | 审查 | VM-3 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | vp/resource 为主 | 统一转 px | 单位矩阵 | AC-2.1 |
| 平板 | 可使用更大间距 | 有效值按 Dimension 转换；非法输入存在通道偏差 | 尺寸 UT | AC-1.1, AC-1.4 |
| 折叠屏 | 密度/资源变化可重载 | 重新测量 | 折叠态测试 | AC-2.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 仅改变几何间距 | AC-1.1 |
| 大字体 | 是 | 内容最小高度与间距共同约束 | AC-1.1 |
| 深色模式 | 否 | 不涉及颜色 | VM-1 |
| 多窗口/分屏 | 是 | 重新测量有效空间 | AC-1.1 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | legacy/NG 偏差需回归 | AC-2.4 |
| 生态兼容 | 是 | SDK 默认值保持 0vp | AC-1.3 |

## 行为场景（可选，Gherkin）

本 Feat 为标准复杂度，接口规格行为场景已覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] Resource、LPX、null、输入校验偏差、首轮双 startMargin、末项约束和 legacy 风险明确
- [x] AC、规则、VM 一致
- [x] 未修改存量偏差

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ColumnSplit divider margin resource LPX legacy SetDivider"
  - repo: "openharmony/interface_sdk-js"
    query: "ColumnSplitDividerStyle startMargin endMargin"
```

**关键文档：** `05-ui-components/01-layout-components/04-column-split/design.md`
