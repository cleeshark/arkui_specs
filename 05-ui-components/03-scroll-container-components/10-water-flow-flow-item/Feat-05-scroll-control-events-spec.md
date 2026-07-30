# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | 滚动控制与事件 |
| 特性编号 | Func-05-03-10-Feat-05 |
| 所属 Epic | WaterFlow/FlowItem 长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 9-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | Scroller 控制 | scrollToIndex/edge/by/fling/page/查询 |
| ADDED | WaterFlow 事件 | index/reach/frame/will/did 与模式差异 |
## 输入文档
- SDK：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/scroll.d.ts:395-604`、`water_flow.d.ts:800-870`
- 实现：`frameworks/core/components_ng/pattern/waterflow/water_flow_pattern.cpp:354-547,708-830`
## 用户故事
### US-1: 控制滚动
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN调用 scrollToIndex 非动画 THEN设置 jumpIndex 并在 measure 对齐；WHEN smooth THEN测量目标后 AnimateTo | 正常 |
| AC-1.2 | WHEN调用 scrollEdge START/END THEN分别映射首 Item START/末 Item END，Footer 末端用无限 delta 对齐 | 正常 |
| AC-1.3 | WHEN SW 状态栏回顶动画估算未到顶 THEN额外 ScrollToIndex(0,false,START) 校准 | 恢复 |
| AC-1.4 | WHEN使用同一 Scroller 绑定多个滚动组件 THEN拒绝共享 | 异常 |
### US-2: 观察事件
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN首次布局 THEN onScrollIndex 报告当前 first/last；WHEN索引变化 THEN再次报告 | 正常 |
| AC-2.2 | WHEN交互、惯性或 fling 产生帧位移 THEN frameBegin 可改写；其他控制 API/回弹/滚动条拖动不触发 | 边界 |
| AC-2.3 | WHEN布局完成 THEN did/index/reach/stop 按公共生命周期顺序触发 | 正常 |
| AC-2.4 | WHEN静态事件传 undefined THEN注销回调；动态旧 onScroll API12 起废弃并由 onDidScroll 替代 | 恢复 |
## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-2.4 | R-1-R-8 | TASK-05-03-10-F5 | controller/模式/事件顺序测试 | `water_flow_pattern.cpp:354-547,708-830` |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | scrollToIndex | jump 或 target+AnimateTo | 默认 smooth=false START | AC-1.1 |
| R-2 | 行为 | scrollEdge | 映射首/末 Item | Footer 特殊 | AC-1.2 |
| R-3 | 恢复 | SW backToTop 未精确到顶 | 强制 index0 | 动画未 abort | AC-1.3 |
| R-4 | 异常 | Scroller 重复绑定 | 拒绝 | 独占 | AC-1.4 |
| R-5 | 行为 | 首布局/索引变化 | onScrollIndex | first/last | AC-2.1 |
| R-6 | 边界 | frameBegin 来源 | input/fling 是，其他否 | 可改写 offset | AC-2.2 |
| R-7 | 行为 | 布局后 | did/index/reach/stop | 使用实际布局状态 | AC-2.3 |
| R-8 | 恢复 | static undefined/旧 onScroll | 注销/迁移 didScroll | 版本分层 | AC-2.4 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.4 | 两模式 controller 测试 | jump/smooth/edge/backToTop |
| VM-2 | AC-2.1-AC-2.4 | 事件计数和顺序测试 | 初始化、来源、注销 |
## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| Scroller 控制/查询 | Public | index/offset/edge/velocity | void/bool/rect/index | N/A | 控制 WaterFlow | AC-1.1-AC-1.4 |
| WaterFlow 事件 | Public | callbacks | 属性链 | N/A | 观察滚动 | AC-2.1-AC-2.4 |
### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `onScroll` | API12 废弃 | 旧一维事件 | 使用 onDidScroll | AC-2.4 |
## 接口规格
### 接口定义
| 接口 | 参数约束 | 行为场景 | 关联 AC |
|---|---|---|---|
| scrollToIndex | index、smooth=false、align=START | 模式分别处理 jump/target | AC-1.1 |
| onScrollIndex/frame/will/did/reach | callback/静态 undefined | 初始化和布局后通知 | AC-2.1-AC-2.4 |
## 兼容性声明
- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** reach API9；frameBegin API10；index API11；will/did API12；滚动条 API18。
- **API 版本号策略:** 方法级版本。
## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 模式分派 | controller 共享入口，目标计算由 LayoutInfo 实现 | AC-1.1-AC-1.3 |
| 布局后事件 | 索引/Reach 使用最终 LayoutInfo | AC-2.1-AC-2.3 |
## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 远 smooth 会加载沿途 Item，测试需限制目标距离 | 性能测试 | SDK |
| 可靠性 | SW 回顶最终精确到 index0 | 回顶测试 | Pattern:798-818 |
| 安全 | N/A | 审查 | 无权限 |
| 可测试性 | 控制和事件均可观测 | VM-1/2 | 本文 |
## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机/平板/折叠屏 | 无控制语义差异 | 视口影响 align 结果 | resize 测试 | LayoutInfo |
## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 程序化滚动更新可见索引 | AC-1.1, AC-2.1 |
| 版本升级 | 是 | API9-21 事件演进 | AC-2.1-AC-2.4 |
| 生态兼容 | 是 | 头文件称 SW 不支持 scrollTo/animateTo 已陈旧 | AC-1.1 |
## 行为场景（可选，Gherkin）
```gherkin
Scenario: SW 精确回顶
  Given SW 远跳后 totalOffset 为估算值
  When 状态栏回顶动画停止但未到首项
  Then 非动画跳转到 index 0 START
```
## Spec 自审清单
- [x] 无占位符
- [x] 两模式控制差异明确
- [x] AC/规则/VM 完整映射
## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "WaterFlow scrollToIndex events backToTop"
```
**关键文档：** Scroller SDK 与 WaterFlowPattern。
