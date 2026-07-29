# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | 公共布局配置与 Item 约束 |
| 特性编号 | Func-05-03-10-Feat-02 |
| 所属 Epic | WaterFlow/FlowItem 长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 9-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 模板、gap、方向 | 补录公共轨道配置与 reset |
| ADDED | Item/Section 约束 | 补录交集、回调尺寸和 Sections 覆盖 |
## 输入文档
- SDK：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/water_flow.d.ts:44-148,527-653`
- 实现：`frameworks/core/components_ng/pattern/waterflow/layout/water_flow_layout_utils.cpp:36-148,197-223`、`water_flow_layout_property.cpp:147-159`
## 用户故事
### US-1: 配置轨道与方向
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN垂直/水平布局 THEN分别消费 columnsTemplate/rowsTemplate 与对应 gap | 正常 |
| AC-1.2 | WHEN模板非法或为空 THEN退化为单轨；WHEN gap<0 THEN归零 | 异常 |
| AC-1.3 | WHEN使用 ItemFillPolicy THEN替代字符串 columnsTemplate 并按宽度/density 生成列模板 | 正常 |
| AC-1.4 | WHEN方向为 reverse 或 RTL THEN主轴和交叉轴分别镜像 | 边界 |
### US-2: 合并 Item 与 Section 约束
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN itemConstraintSize 与 FlowItem constraintSize 同时设置 THEN min 取较大、max 取较小 | 正常 |
| AC-2.2 | WHEN Section 提供 crossCount/gap/margin THEN覆盖公共模板并使用段级配置，crossCount<=0 归一为1 | 边界 |
| AC-2.3 | WHEN Section size callback 返回负值/非数值 THEN主轴尺寸按0处理 | 异常 |
| AC-2.4 | WHEN Section 自定义主轴尺寸存在 THEN容器 Item 约束不再无条件覆盖该尺寸 | 边界 |
## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-2.4 | R-1-R-8 | TASK-05-03-10-F2 | SDK/Bridge/Layout 参数化测试 | `water_flow_layout_utils.cpp:36-148,197-223` |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | Column/Row | 消费对应模板和 gap | 默认 1fr/0 | AC-1.1 |
| R-2 | 恢复 | 模板非法/空 | 单轨填满交叉轴 | auto 转 1fr | AC-1.2 |
| R-3 | 恢复 | gap<0/undefined | 0/默认 | 静态支持 undefined | AC-1.2 |
| R-4 | 行为 | ItemFillPolicy | 替代 columnsTemplate | API22+ | AC-1.3 |
| R-5 | 边界 | reverse/RTL | 分层镜像物理位置 | start/end 保持逻辑语义 | AC-1.4 |
| R-6 | 行为 | 双重 constraint | 取约束交集 | min/max 独立 | AC-2.1 |
| R-7 | 边界 | Sections | crossCount>=1，段 gap/margin 优先 | 忽略公共模板 | AC-2.2 |
| R-8 | 异常 | size callback 非法 | 0 | 用户尺寸优先于公共 Item 约束 | AC-2.3-AC-2.4 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.4 | 轴向/模板/gap/RTL 测试 | fallback、fill policy、镜像 |
| VM-2 | AC-2.1-AC-2.4 | constraint/Sections 测试 | 交集、优先级、非法值 |
## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| templates/gaps/direction | Public | string/ItemFillPolicy/Length/FlexDirection | 属性链 | N/A | 配置轨道 | AC-1.1-AC-1.4 |
| itemConstraintSize/SectionOptions | Public | ConstraintSizeOptions/section | 属性链/boolean | N/A | 配置 Item/段 | AC-2.1-AC-2.4 |
### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| ItemFillPolicy | 历史新增 | API22 | 仅 columnsTemplate 支持 | AC-1.3 |
## 接口规格
### 接口定义
| 接口 | 参数约束 | 行为场景 | 关联 AC |
|---|---|---|---|
| templates/gaps | 非法模板单轨；负 gap=0 | 轴向选择对应属性 | AC-1.1-AC-1.3 |
| itemConstraintSize/SectionOptions | crossCount>=1；itemsCount 非负 | 公共/段/Item 约束按优先级合并 | AC-2.1-AC-2.4 |
## 兼容性声明
- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 基础属性 API9；ItemFillPolicy API22；静态 API23。
- **API 版本号策略:** 方法级版本。
## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| Sections 优先 | Sections 不消费公共 templates | AC-2.2 |
| 约束门控 | Section 用户主轴尺寸可绕过容器 Item 约束 | AC-2.4 |
## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 模板/段变化仅触发必要重排 | Layout 测试 | LayoutProperty |
| 可靠性 | 非法模板/gap/size 均有恢复 | 边界测试 | LayoutUtils |
| 安全 | 不涉及权限 | 审查 | N/A |
| 可测试性 | 每类配置可参数化 | VM-1/2 | 本文 |
## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机/平板/折叠屏 | 宽度/density 改变 fill policy 轨道数 | 每轮按当前约束解析 | 尺寸测试 | `water_flow_layout_property.cpp:147-159` |
## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| RTL | 是 | 交叉轴镜像 | AC-1.4 |
| 版本升级 | 是 | API22 fill policy | AC-1.3 |
| 生态兼容 | 是 | static undefined reset | AC-1.2 |
## 行为场景（可选，Gherkin）
```gherkin
Scenario: Sections 覆盖公共模板
  Given columnsTemplate 为 3fr 且 Section crossCount 为 2
  When 执行分段布局
  Then 该段使用 2 个等宽轨道
```
## Spec 自审清单
- [x] 无占位符
- [x] AC/规则/VM 完整映射
- [x] 版本和非法值明确
## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "WaterFlow template gap constraint SectionOptions"
```
**关键文档：** WaterFlow SDK、LayoutProperty 和 LayoutUtils。
