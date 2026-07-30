# 特性规格
## 概述
| 字段 | 内容 |
|---|---|
| 特性名称 | 缓存与懒加载 |
| 特性编号 | Func-05-03-10-Feat-06 |
| 所属 Epic | WaterFlow/FlowItem 长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 11-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
## 本次变更范围（Delta）
| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | cachedCount | 动态默认、showCachedItems、范围释放 |
| ADDED | Predict/idle preload | deadline 拆分、lanes 恢复、异步下一帧 |
## 输入文档
- SDK：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/water_flow.d.ts:706-752`
- 实现：`layout/water_flow_layout_algorithm_base.cpp:129-220`、`layout/sliding_window/water_flow_layout_sw.cpp:46-149,824-860,951-974,1093-1125`
## 用户故事
### US-1: 配置缓存范围
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN未显式设置 cachedCount THEN初始为1，布局后按 ceil(pageCount×可见 Item 数) 增长且最大16 | 边界 |
| AC-1.2 | WHEN显式 count<0 或 undefined/reset THEN恢复默认策略 | 恢复 |
| AC-1.3 | WHEN使用 LazyForEach/Repeat virtualScroll THEN范围外节点可释放；普通静态子节点不承诺同等回收 | 边界 |
### US-2: 预加载和拆帧
| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN showCachedItems=true THEN同步创建缓存 Item；WHEN false THEN通过 predict/idle task 分批预载 | 正常 |
| AC-2.2 | WHEN preload 超过 deadline THEN剩余索引重新入队并在后续任务继续 | 边界 |
| AC-2.3 | WHEN SW 缓存测量结束 THEN恢复正式 lanes，缓存节点 Layout 后 inactive，正式布局再恢复范围 | 正常 |
| AC-2.4 | WHEN syncLoad=false 且无 delta/target THEN允许 Fill 超时设置 measureInNextFrame 并 PostAsyncLoadTask | 边界 |
| AC-2.5 | WHEN Sections itemsCount 与 LazyForEach/Repeat 实际数不一致 THEN布局数据无效并上报 | 异常 |
## 验收追溯
| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-2.5 | R-1-R-8 | TASK-05-03-10-F6 | cache/predict/deadline/lazy 参数化测试 | `water_flow_layout_algorithm_base.cpp:129-220` |
## 规则定义
| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 边界 | cachedCount 未设置 | 动态计算，最大16 | 初始1 | AC-1.1 |
| R-2 | 恢复 | count<0/reset | 默认策略 | 静态 undefined | AC-1.2 |
| R-3 | 边界 | virtual lazy source | 范围外可释放 | 普通节点不同 | AC-1.3 |
| R-4 | 行为 | show=true/false | 同步/异步 preload | 前后缓存范围 | AC-2.1 |
| R-5 | 恢复 | deadline 超时 | 剩余重新入队 | 后续 idle | AC-2.2 |
| R-6 | 行为 | SW cache update | 保存/恢复 lanes | cache item inactive | AC-2.3 |
| R-7 | 边界 | async Fill 超时 | 下一帧继续 measure | 仅安全状态 | AC-2.4 |
| R-8 | 异常 | Section 总数不符 | 数据无效并上报 | 停止有效布局 | AC-2.5 |
## 验证映射
| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.3 | count/visible/lazy 回收测试 | 动态默认、上限、释放 |
| VM-2 | AC-2.1-AC-2.5 | deadline/lanes/next-frame/Sections 测试 | 同异步、状态不污染 |
## API 变更分析
### 新增 API
| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `cachedCount(count,show?)` | Public | int、boolean | 属性链 | N/A | 配置缓存与显示 | 全部 AC |
### 变更/废弃 API
| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| cachedCount show 重载 | 历史扩展 | API14+ | 按版本使用 | AC-2.1 |
## 接口规格
### 接口定义
| 接口 | 参数约束 | 行为场景 | 关联 AC |
|---|---|---|---|
| cachedCount | 非负；默认动态且<=16 | LazyForEach/Repeat 缓存范围 | AC-1.1-AC-2.5 |
## 兼容性声明
- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** cachedCount API11；show 重载按 SDK 版本；静态 API23。
- **API 版本号策略:** 方法/重载级版本。
## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 缓存不污染窗口 | preload 后恢复 lanes/active range | AC-2.3 |
| 响应时限 | async Fill 可跨帧续作 | AC-2.2, AC-2.4 |
## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 自动缓存上限16屏幕可见节点倍数 | 大列表测试 | LayoutInfoBase |
| 内存 | virtual 范围外节点允许释放 | 节点计数测试 | SDK |
| 可靠性 | 超时任务可续作且状态恢复 | deadline 注入 | preload 实现 |
| 安全 | N/A | 审查 | 无权限 |
| 可测试性 | deadline/pageCount 可 Mock | Host 测试 | VM-1/2 |
## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机/平板/折叠屏 | 可见 Item 数改变自动 cachedCount | 上限仍16 | resize 测试 | LayoutInfoBase |
## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 内存压力 | 是 | virtual 范围外释放 | AC-1.3 |
| 多窗口 | 是 | 可见数变化重算默认缓存 | AC-1.1 |
| 生态兼容 | 是 | 仅 LazyForEach/Repeat virtualScroll 保证回收 | AC-1.3 |
## 行为场景（可选，Gherkin）
```gherkin
Scenario: 异步预载超时续作
  Given showCachedItems 为 false
  When predict task 达到 deadline
  Then 保存剩余索引并重新入队
  And 正式窗口 lanes 保持不变
```
## Spec 自审清单
- [x] 无占位符
- [x] 缓存/懒加载范围明确
- [x] AC/规则/VM 完整映射
## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "WaterFlow cachedCount preload lazy sliding window"
```
**关键文档：** WaterFlow cache/preload/SW 实现与 SDK。
