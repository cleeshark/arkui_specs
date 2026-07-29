# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | SLIDING_WINDOW 布局算法 |
| 特性编号 | Func-05-03-10-Feat-04 |
| 所属 Epic | WaterFlow/FlowItem 长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 12-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |
本特性规定独立的 WaterFlowLayoutSW 窗口算法；Sections 在本模式下仍由 SW 消费，不切换 segmented 算法。
## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 窗口状态机 | Fill/clear/jump/target/估算 |
| ADDED | SW Sections | 分段 lane、margin、gap |
## 输入文档
- `frameworks/core/components_ng/pattern/waterflow/water_flow_pattern.cpp:213-227,884-890`
- `layout/sliding_window/water_flow_layout_sw.cpp:34-69,335-780`
- `layout/sliding_window/water_flow_layout_info_sw.cpp:109-123,345-394,657-696,895-965`
## 用户故事
### US-1: 维护滑动窗口
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN mode=SLIDING_WINDOW THEN无论是否有 Sections 均选择 WaterFlowLayoutSW | 正常 |
| AC-1.2 | WHEN普通滚动 THEN平移 lanes、向对应方向 Fill，并清除视口外稳定 Item | 正常 |
| AC-1.3 | WHEN跨 section Fill THEN按段内最短/最高 lane 放置并用相邻 margin 初始化新段 | 正常 |
### US-2: 跳转和估算
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN远距离非动画 jump THEN重置窗口并按 START/END/CENTER 方向双向填充 | 正常 |
| AC-2.2 | WHEN jump/数据更新后读取 totalOffset THEN允许返回估算值，回到顶部后校准 | 边界 |
| AC-2.3 | WHEN smooth target 不在窗口 THEN先测量到目标、跳过该轮 Layout，再计算动画目标 | 正常 |
| AC-2.4 | WHEN AUTO 目标已完整可见 THEN目标位移为0；其他 align 计入 contentStart/EndOffset | 边界 |
## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-2.4 | R-1-R-7 | TASK-05-03-10-F4 | SW/Sections/jump/target Host 测试 | `water_flow_layout_sw.cpp:34-780` |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | SW mode | WaterFlowLayoutSW | Sections 不改派发 | AC-1.1 |
| R-2 | 行为 | offset | 平移/Fill/clear | lanes 仅保留窗口 | AC-1.2 |
| R-3 | 行为 | Sections | 段内 lane 优先队列 | crossCount>=1 | AC-1.3 |
| R-4 | 行为 | jump | 重建窗口 | align 分支不同 | AC-2.1 |
| R-5 | 边界 | jump/update 后 | totalOffset 可估算 | 顶部校准 | AC-2.2 |
| R-6 | 行为 | smooth 远目标 | 预测目标后 AnimateTo | target measure 跳过 Layout | AC-2.3 |
| R-7 | 边界 | AUTO/START/END/CENTER | 计算窗口内目标 | AUTO 可0 | AC-2.4 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.3 | 窗口/Sections 测试 | Fill、clear、lane、margin |
| VM-2 | AC-2.1-AC-2.4 | jump/target/offset 测试 | align、估算、校准 |
## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `layoutMode=SLIDING_WINDOW` | Public | enum 1 | 属性链 | N/A | 选择 SW 算法 | 全部 AC |
### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| 无 | N/A | 存量算法补录 | N/A | 全部 |
## 接口规格
### 接口定义
| 接口 | 参数约束 | 行为场景 | 关联 AC |
|---|---|---|---|
| SLIDING_WINDOW | mode=1 | 窗口内布局、远跳估算 | 全部 AC |
## 兼容性声明
- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** layoutMode API12。
- **API 版本号策略:** SDK 方法级版本。
## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 算法隔离 | SW 不复用 TOP_DOWN LayoutInfo/算法 | AC-1.1 |
| 估算契约 | 远跳后 offset 不承诺立即精确 | AC-2.2 |
## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 稳定态仅保留窗口 lanes/item | 长列表测试 | SW Fill/Clear |
| 可靠性 | 顶部可校准估算偏差 | 回顶测试 | Pattern backToTop |
| 安全 | N/A | 审查 | 无权限 |
| 可测试性 | 窗口/lanes 可断言 | Host 测试 | VM-1/2 |
## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机/平板/折叠屏 | 窗口容量随视口变化 | 重建/Fill 当前窗口 | resize 测试 | SW |
## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 大数据 | 是 | 推荐 SW 降低历史 Item 布局 | AC-1.2 |
| 版本升级 | 是 | API12+ | AC-1.1 |
| 生态兼容 | 是 | currentOffset 存在估算语义 | AC-2.2 |
## 行为场景（可选，Gherkin）
```gherkin
Scenario: SW 与 Sections
  Given layoutMode 为 SLIDING_WINDOW 且配置 Sections
  When 创建布局算法
  Then 使用 WaterFlowLayoutSW
  And 不使用 WaterFlowSegmentedLayout
```
## Spec 自审清单
- [x] 无占位符
- [x] SW 与 TOP_DOWN 完全分离
- [x] AC/规则/VM 完整映射
## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "WaterFlow sliding window lanes jump target sections"
```
**关键文档：** WaterFlowLayoutSW 与 WaterFlowLayoutInfoSW。
