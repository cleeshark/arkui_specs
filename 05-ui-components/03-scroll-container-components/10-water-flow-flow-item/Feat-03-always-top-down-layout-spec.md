# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | ALWAYS_TOP_DOWN 布局算法 |
| 特性编号 | Func-05-03-10-Feat-03 |
| 所属 Epic | WaterFlow/FlowItem 长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 9-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |
本特性分别规定 TOP_DOWN 普通算法与 Sections/系统开关触发的 segmented 算法。
## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 普通 TOP_DOWN | 最短轨放置、增量测量、Footer |
| ADDED | Segmented TOP_DOWN | Section 轨道、边界、size callback、计数校验 |
## 输入文档
- 派发：`frameworks/core/components_ng/pattern/waterflow/water_flow_pattern.cpp:190-231`
- 普通：`layout/top_down/water_flow_layout_algorithm.cpp:57-203,269-505,626-667`
- 分段：`layout/top_down/water_flow_segmented_layout.cpp:37-121,243-579,627-720`
## 用户故事
### US-1: 使用普通 TOP_DOWN
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN无 Sections 且系统分段开关关闭 THEN选择 WaterFlowLayoutAlgorithm | 正常 |
| AC-1.2 | WHEN放置 Item THEN优先空轨，否则选择当前末端最短轨，相等取较小轨道下标 | 正常 |
| AC-1.3 | WHEN目标未缓存 THEN顺序测量至目标；WHEN Item 尺寸变化 THEN从该 Item 后清缓存并重排 | 边界 |
| AC-1.4 | WHEN到达 Item 尾部且存在 Footer THEN将 Footer 放在最高轨末端并在 reverse 下镜像 | 正常 |
### US-2: 使用 Segmented TOP_DOWN
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN存在 Sections 或系统开关开启 THEN选择 WaterFlowSegmentedLayout | 正常 |
| AC-2.2 | WHEN跨 section THEN下一段起点取前序 Item 最大末端并叠加相邻 margin，连续空段跳过 | 正常 |
| AC-2.3 | WHEN size callback 可用且远距离 jump THEN可用回调尺寸建立中间 itemInfo 而不创建全部节点 | 正常 |
| AC-2.4 | WHEN section itemsCount 总和与真实 FlowItem 数不一致 THEN停止有效测量并上报一次错误 | 异常 |
| AC-2.5 | WHEN未到尾部 THEN总长按已记录平均尺寸估算；WHEN普通算法到尾部 THEN返回精确 maxHeight | 边界 |
## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-2.5 | R-1-R-9 | TASK-05-03-10-F3 | 普通/segmented/Sections 参数化布局测试 | `water_flow_pattern.cpp:213-231` |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | TOP_DOWN 无分段条件 | 普通算法 | 共享 WaterFlowLayoutInfo | AC-1.1 |
| R-2 | 行为 | 新 Item | 最短轨优先 | tie 取低 lane | AC-1.2 |
| R-3 | 恢复 | 尺寸变化 | 清后续缓存重排 | 已缓存目标可直算 | AC-1.3 |
| R-4 | 行为 | 尾部+Footer | 放最高轨末端 | Footer 非 FlowItem 索引 | AC-1.4 |
| R-5 | 行为 | Sections/系统开关 | segmented | TOP_DOWN 内第二实现 | AC-2.1 |
| R-6 | 行为 | 段切换 | 最大末端+margin | 跳过空段 | AC-2.2 |
| R-7 | 行为 | callback 远 jump | 用尺寸预建 itemInfo | 真实测量可回填 | AC-2.3 |
| R-8 | 异常 | item 总数不一致 | 停止并上报 | 一次错误事件 | AC-2.4 |
| R-9 | 边界 | 未到/已到尾部 | 估算/精确总长 | segmented 可估算 | AC-2.5 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.4 | 普通算法 Host 测试 | lane、cache、Footer、reverse |
| VM-2 | AC-2.1-AC-2.5 | segmented/Sections 测试 | margin、空段、callback、计数、估算 |
## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `layoutMode=ALWAYS_TOP_DOWN` | Public | enum 0 | 属性链 | N/A | 选择 TOP_DOWN 家族 | AC-1.1, AC-2.1 |
| `WaterFlowSections` | Public | SectionOptions 列表 | boolean/values | N/A | 驱动 segmented | AC-2.1-AC-2.4 |
### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| 无 | N/A | 存量算法补录 | N/A | 全部 |
## 接口规格
### 接口定义
| 接口 | 参数约束 | 行为场景 | 关联 AC |
|---|---|---|---|
| ALWAYS_TOP_DOWN | Sections 决定普通/segmented | 从起点保存完整已布局位置 | 全部 AC |
## 兼容性声明
- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** WaterFlow API9；layoutMode API12。
- **API 版本号策略:** 现有算法补录。
## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 双实现 | 普通与 segmented 不得混为一套流程 | AC-1.1, AC-2.1 |
| 完整位置缓存 | TOP_DOWN 保存从起点测得的位置 | AC-1.3, AC-2.5 |
## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 普通仅填充视口/扩展区；callback jump 可跳过中间节点创建 | 性能测试 | 算法实现 |
| 可靠性 | 计数不一致停止布局并上报 | 异常测试 | segmented:37-62 |
| 安全 | N/A | 审查 | 无权限 |
| 可测试性 | lane/itemInfo 可直接断言 | Host 测试 | VM-1/2 |
## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机/平板/折叠屏 | 轨道数随交叉轴变化 | 变化后重置布局缓存 | resize 测试 | 普通算法 |
## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| RTL/reverse | 是 | 主轴与交叉轴分层镜像 | AC-1.4, AC-2.2 |
| 版本升级 | 是 | layoutMode API12 | AC-1.1 |
| 生态兼容 | 是 | Sections+Footer 计数存在风险 | AC-2.4 |
## 行为场景（可选，Gherkin）
```gherkin
Scenario: TOP_DOWN 派发
  Given layoutMode 为 ALWAYS_TOP_DOWN
  When Sections 存在
  Then 使用 WaterFlowSegmentedLayout
  When Sections 不存在且系统分段开关关闭
  Then 使用 WaterFlowLayoutAlgorithm
```
## Spec 自审清单
- [x] 无占位符
- [x] 两个 TOP_DOWN 实现分别规定
- [x] AC/规则/VM 完整映射
## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "WaterFlow top down segmented shortest lane sections footer"
```
**关键文档：** WaterFlow TOP_DOWN 普通与 segmented 算法。
