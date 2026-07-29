# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | 组件创建、Footer 与 FlowItem |
| 特性编号 | Func-05-03-10-Feat-01 |
| 所属 Epic | WaterFlow/FlowItem 长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 9-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
本特性规定 WaterFlow/FlowItem 创建、Scroller 绑定、Footer、Sections 和布局模式初始化。
## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 创建与子项规格 | 补录 WaterFlow、FlowItem 和单子节点约束 |
| ADDED | Footer/Sections 规格 | 补录 footerContent 优先级与互斥 |
## 输入文档
- SDK：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/water_flow.d.ts:263-398,492-505`、`flow_item.d.ts:22-100`
- 实现：`frameworks/core/components_ng/pattern/waterflow/water_flow_pattern.cpp:190-231,861-890`
- Bridge：`frameworks/core/components_ng/pattern/waterflow/bridge/waterflow/arkts_native_water_flow_bridge.cpp:467-492,690-700`
## 用户故事
### US-1: 创建容器和子项
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN API9+ 创建 WaterFlow 和 FlowItem THEN FlowItem 作为 WaterFlow 子项参与布局且最多承载一个子组件 | 正常 |
| AC-1.2 | WHEN同一 Scroller 已绑定其他滚动组件 THEN不得再次绑定 WaterFlow | 异常 |
### US-2: 配置 Footer、Sections 和模式
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN footer 与 API18+ footerContent 同时设置 THEN使用 footerContent | 边界 |
| AC-2.2 | WHEN设置 Sections THEN忽略独立 footer，最后一个 section 可承担 footer | 边界 |
| AC-2.3 | WHEN layoutMode 缺省或非法 THEN恢复 ALWAYS_TOP_DOWN；WHEN为 SLIDING_WINDOW THEN创建 SW LayoutInfo | 恢复 |
| AC-2.4 | WHEN运行时切换 layoutMode THEN重建对应 LayoutInfo、清初始化状态并重新布局 | 正常 |
## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-2.4 | R-1-R-6 | TASK-05-03-10-F1 | SDK/Bridge/Pattern 与创建测试 | `water_flow_pattern.cpp:213-227,861-890` |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 创建 FlowItem | 建立 WaterFlowItem FrameNode | 仅一个子组件 | AC-1.1 |
| R-2 | 异常 | Scroller 已绑定 | 拒绝重复绑定 | 滚动控制器独占 | AC-1.2 |
| R-3 | 行为 | footerContent 存在 | 覆盖 footer builder | API18+ | AC-2.1 |
| R-4 | 边界 | Sections 存在 | 不单独设置 footer | 尾 section 可替代 | AC-2.2 |
| R-5 | 恢复 | mode 缺省/越界 | TOP_DOWN | 枚举 0..1 | AC-2.3 |
| R-6 | 行为 | mode 改变 | 重建 LayoutInfo 并重排 | 两算法状态不复用 | AC-2.4 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.2 | 动静态创建测试 | 子节点和 Scroller 独占 |
| VM-2 | AC-2.1-AC-2.4 | Footer/Sections/mode 参数化测试 | 优先级、reset、状态重建 |
## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `WaterFlow(options?)`/`FlowItem()` | Public | WaterFlowOptions/无 | 属性对象 | N/A | 创建容器/子项 | AC-1.1-AC-2.4 |
### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `footerContent` | 历史新增 | API18 | 优先使用 ComponentContent | AC-2.1 |
| `layoutMode` | 历史新增 | API12 | 缺省 TOP_DOWN | AC-2.3 |
## 接口规格
### 接口定义
| 接口 | 参数约束 | 行为场景 | 关联 AC |
|---|---|---|---|
| WaterFlow | options 可省略；sections/footer/mode 按优先级 | 创建后先确定 mode，再确定内容入口 | AC-1.1-AC-2.4 |
| FlowItem | 无选项；单子节点 | 作为虚拟化和布局单元 | AC-1.1 |
## 兼容性声明
- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 动态 API9；layoutMode API12；footerContent API18；静态 API23。
- **API 版本号策略:** 按方法级 `@since`。
## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 模式隔离 | TOP_DOWN/SW 使用不同 LayoutInfo | AC-2.3-AC-2.4 |
| 内容优先级 | Sections > footerContent > footer | AC-2.1-AC-2.2 |
## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 模式切换只重建 WaterFlow 布局状态 | Host 测试 | `water_flow_pattern.cpp:884-890` |
| 可靠性 | 非法 mode 可恢复 TOP_DOWN | Bridge 测试 | `arkts_native_water_flow_bridge.cpp:690-700` |
| 安全 | 不涉及敏感数据 | 审查 | N/A |
| 可测试性 | 创建入口均可独立构造 | 单测 | VM-1/2 |
## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机/平板/折叠屏 | 无创建语义差异 | 尺寸差异由布局 Feat 承接 | 创建测试 | SDK |
## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | FlowItem 保持节点语义 | AC-1.1 |
| 版本升级 | 是 | API9/12/18/23 分层 | AC-2.1-AC-2.3 |
| 生态兼容 | 是 | static Sections generated 路径受条件编译保护 | AC-2.2 |
## 行为场景（可选，Gherkin）
```gherkin
Scenario: Sections 覆盖 Footer
  Given 同时提供 sections、footerContent 和 footer
  When 创建 WaterFlow
  Then 使用 sections
  And 不创建独立 footer
```
## Spec 自审清单
- [x] 无占位符
- [x] AC 可测试且与规则/VM 对应
- [x] 范围、版本和风险明确
## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "WaterFlow create footer FlowItem sections layoutMode"
```
**关键文档：** WaterFlow/FlowItem SDK 与 Pattern/Bridge 创建实现。
