# 特性规格

> Func-05-14-01-Feat-05 Shape Path 命令绘制存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Shape Path 命令绘制 |
| 特性编号 | Func-05-14-01-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

Path 通过 SVG 风格 `commands` 字符串/Resource 定义几何，并结合可选宽高完成测量和绘制。本特性覆盖命令更新、支持命令、空/非法字符串、资源刷新、边界盒与多范式入口。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Path 创建与尺寸 | options、width/height 与测量 |
| ADDED | commands | SVG path 解析、Resource、reset 与非法命令 |
| ADDED | 多版本入口 | Dynamic/Static/Modifier/Builder |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/01-shape/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/path.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/path.static.d.ets` | 已核对 |
| Model | `frameworks/core/components_ng/pattern/shape/path_model_ng.cpp` | 已核对 |
| Layout | `frameworks/core/components_ng/pattern/shape/path_layout_algorithm.cpp` | 已核对 |
| Painter | `frameworks/core/components_ng/pattern/shape/path_painter.cpp` | 已核对 |

## 用户故事

### US-1: 从 SVG 命令构建路径

**作为** 图形应用开发者  
**我想要** 使用 commands 构建复杂路径  
**以便** 绘制直线、曲线、圆弧和闭合轮廓

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN commands 为合法 ResourceStr 且包含支持的绝对/相对路径命令 THEN parser 构建对应路径并由 PathPainter 绘制 | 正常 |
| AC-1.2 | WHEN命令形成闭合子路径 THEN fill 作用于闭合区域且 stroke 沿路径轮廓绘制 | 正常 |
| AC-1.3 | WHEN commands 为空、undefined/reset THEN 清除当前路径命令并产生空几何/无路径绘制 | 边界 |
| AC-1.4 | WHEN字符串含无法解析命令、参数数量错误、NaN/Infinity 或 Resource 失败 THEN 安全拒绝非法片段/路径，不崩溃或越界 | 异常 |

### US-2: 测量和更新 Path

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN options 提供合法 width/height THEN Path 布局使用显式边界；未提供时按命令边界和约束确定 | 正常 |
| AC-2.2 | WHEN命令坐标越出显式边界 THEN 绘制仍遵守当前组件 clip/布局边界规则，不自动扩展 API 契约 | 边界 |
| AC-2.3 | WHEN commands Resource 或构造参数更新 THEN Model 更新 PaintProperty 并标记 Measure/Paint | 正常 |
| AC-2.4 | WHEN Dynamic、Static、Modifier 或 Builder 设置等价命令 THEN NG PathModel 得到等价字符串/Resource 结果 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Path parser/painter UT | `frameworks/core/components_ng/pattern/shape/path_model_ng.cpp:20-78`; `frameworks/core/components_ng/pattern/shape/path_painter.cpp:20-36` |
| AC-2.1~AC-2.3 | R-5~R-7 | 已有实现 | Path layout/resource UT | `frameworks/core/components_ng/pattern/shape/path_layout_algorithm.cpp:20-88`; `frameworks/core/components_ng/pattern/shape/path_pattern.cpp:20-55` |
| AC-2.4 | R-8 | 已有实现 | Dynamic/Static modifier UT | `frameworks/core/components_ng/pattern/shape/bridge/path_dynamic_modifier.cpp:20-132`; `frameworks/core/components_ng/pattern/shape/bridge/path_static_modifier.cpp:20-98` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | commands 合法 | 构建并绘制路径 | 支持 SDK/底层命令集 | AC-1.1 |
| R-2 | 行为 | 子路径闭合 | fill 闭合区域、stroke 轮廓 | 样式由 Feat-02 | AC-1.2 |
| R-3 | 恢复 | 空/undefined/reset | 清除路径命令 | 空几何 | AC-1.3 |
| R-4 | 异常 | 命令/参数/数值非法 | 拒绝非法路径且安全退出 | 不越界 | AC-1.4 |
| R-5 | 行为 | 显式/隐式尺寸 | 使用显式或命令边界 | 受父约束 | AC-2.1 |
| R-6 | 边界 | 命令越出边界 | 遵守当前 clip/布局 | 不扩展接口 | AC-2.2 |
| R-7 | 行为 | Resource/参数更新 | 更新属性并标脏 | 使用最新命令 | AC-2.3 |
| R-8 | 行为 | 多入口等价命令 | 形成等价 NG 属性 | SDK 为准 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | Path command/Fuzz UT | 命令、闭合、空和非法值 |
| VM-2 | AC-2.1~AC-2.3 | Layout/Resource UT | 边界与更新 |
| VM-3 | AC-2.4 | 多入口对照 UT | Dynamic/Static/Builder |

## API 变更分析

### 新增 API

N/A，Path/commands 为已有 API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**Path(options?) / commands(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Path(options?: PathOptions): PathAttribute`; `commands(value: ResourceStr): PathAttribute` |
| 返回值 | PathAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| width/height | Length | 否 | 命令边界/约束 | 非负有限 |
| commands | ResourceStr | 是 | 空 | 可解析 SVG path 字符串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法闭合命令 | 绘制填充与描边 | AC-1.1, AC-1.2 |
| 2 | 非法或空命令 | 安全空路径 | AC-1.3, AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 是；Options/Resource/Static/Builder 按 API 18/20/23/26 演进。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 7。
- **API 版本号策略:** API 7/18/20/23/26 全量记录。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 命令解析 | commands 由 Path 模型/绘制链解析 | AC-1.1 |
| 几何/样式分离 | Path 几何在本 Feat，通用样式在 Feat-02 | AC-1.2 |
| Resource 更新 | 命令资源变化需重新解析并标脏 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 解析/绘制复杂度随命令数增长 | 性能测试 | VM-1 |
| 功耗 | 无后台任务 | 审查 | VM-1 |
| 内存 | 路径对象随节点释放 | 生命周期 UT | VM-1 |
| 安全 | 非法命令不越界或执行代码 | Fuzz | AC-1.4 |
| 可靠性 | 空/失败资源得到安全空路径 | 边界 UT | VM-1 |
| 可测试性 | path bounds/像素可断言 | UT/截图 | VM-1~VM-3 |
| 自动化维测 | commands/边界可 Dump | Inspector | AC-2.3 |
| 定界定位 | SDK→bridge→model→parser/painter | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 小尺寸路径精度敏感 | density 解析一致 | 像素测试 | AC-2.1 |
| 平板 | 复杂路径常见 | 命令数性能回归 | 性能测试 | AC-1.1 |
| 折叠屏 | 尺寸变化 | 显式/隐式边界重算 | 折叠态测试 | AC-2.1 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Path 不自动产生语义 | AC-1.1 |
| 大字体 | 否 | 不涉及文本 | VM-1 |
| 深色模式 | 是 | 样式资源可变 | AC-1.2 |
| 多窗口/分屏 | 是 | 边界重算 | AC-2.1 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | Resource/Static/Builder 需回归 | AC-2.4 |
| 生态兼容 | 是 | 非法命令安全行为保持 | AC-1.4 |

## 行为场景（可选，Gherkin）

本 Feat 为标准复杂度，接口规格行为场景已覆盖。

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 命令、Resource、尺寸、空值和非法输入明确
- [x] AC、规则、VM 一致
- [x] 未扩展未声明命令契约

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Path commands SVG parser PathPainter"
  - repo: "openharmony/interface_sdk-js"
    query: "PathOptions commands ResourceStr"
```

**关键文档：** `05-ui-components/14-drawing-components/01-shape/design.md`
