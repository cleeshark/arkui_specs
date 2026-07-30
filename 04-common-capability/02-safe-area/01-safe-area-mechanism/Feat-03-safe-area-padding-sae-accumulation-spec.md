# 特性规格

> Func-04-02-01-Feat-03 组件级安全区内边距与 SAE 累积存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件级安全区内边距与 SAE 累积 |
| 特性编号 | Func-04-02-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`safeAreaPadding` 将组件级安全区表达为四边内边距，并通过 Safe Area Expansion（SAE）沿连续祖先向外累积；本特性覆盖 Padding、LengthMetrics、LocalizedPadding、Resource、undefined/reset、RTL、Stage 系统 padding、缓存和中断条件。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | safeAreaPadding 参数 | 物理边、本地化边、Resource 和 reset |
| ADDED | SAE 累积 | 祖先递归、Stage 输入、缓存与中断 |
| ADDED | 通道边界 | Dynamic/Static 有公开 API，C Node 当前未公开该属性 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets` | 已核对 |
| Parser | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 已核对 |
| Accumulation | `frameworks/core/components_ng/layout/layout_wrapper.cpp` | 已核对 |

## 用户故事

### US-1: 设置组件级安全区内边距

**作为** 应用开发者  
**我想要** 使用全部公开形式设置 safeAreaPadding  
**以便** 组件后代可识别自定义安全边界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 传入 Padding 的 top/right/bottom/left 合法长度 THEN 四边独立解析并保存为 safe-area padding | 正常 |
| AC-1.2 | WHEN 传入 LocalizedPadding 的 start/end THEN 按当前 LTR/RTL 映射到物理 left/right | 正常 |
| AC-1.3 | WHEN 传入 LengthMetrics 或 Resource THEN 按单位/资源上下文解析，资源变化后触发相应布局更新 | 正常 |
| AC-1.4 | WHEN 值为 undefined/reset、负数、NaN、Infinity 或资源解析失败 THEN 按当前入口清除/回退，不保存非法负 padding | 异常 |

### US-2: 沿连续祖先累积 SAE

**作为** 布局算法  
**我想要** 获取节点可扩展到的连续安全区  
**以便** ignoreLayoutSafeArea 使用准确边界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 当前节点及祖先 safeAreaPadding 连续且无中断 THEN SAE 向外递归累积各边范围 | 正常 |
| AC-2.2 | WHEN 祖先存在 margin、border、普通 padding 或到达 Stage 边界 THEN 按实现停止继续向外累积 | 边界 |
| AC-2.3 | WHEN 节点为 Stage 页面根 THEN 系统页级安全区作为该层 safe-area padding 参与计算 | 正常 |
| AC-2.4 | WHEN 几何、方向或 padding 改变 THEN 失效缓存被重算，START/END 使用新方向 | 边界 |

### US-3: 保持接口通道边界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Dynamic API 14 或 Static API 23 设置等价输入 THEN 形成等价 SafeAreaPaddingProperty | 正常 |
| AC-3.2 | WHEN 查询公开 C Node 属性集合 THEN 不把内部 CommonModifier::setSafeAreaPadding 误写为公开 C API | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Parser/Resource/RTL UT | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:4304-4380`; `interface/sdk-js/api/@internal/component/ets/common.d.ts:19938-19968` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | SAE LayoutWrapper UT | `frameworks/core/components_ng/layout/layout_wrapper.cpp:550-605` |
| AC-3.1~AC-3.2 | R-9~R-10 | 已有实现 | SDK/C API 审查 | `interface/sdk-js/api/arkui/component/common.static.d.ets:11625-11636` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 物理 Padding 合法 | 四边独立保存 | 未填边为既有默认 | AC-1.1 |
| R-2 | 行为 | Localized start/end | 按 LTR/RTL 映射 | 方向变化可重算 | AC-1.2 |
| R-3 | 行为 | LengthMetrics/Resource 合法 | 按单位和资源解析 | 资源更新触发布局 | AC-1.3 |
| R-4 | 异常 | undefined/非法长度/资源失败 | reset 或回退 | 不保存负/非有限值 | AC-1.4 |
| R-5 | 行为 | 连续 SAE 祖先 | 各边向外累积 | 仅连续范围 | AC-2.1 |
| R-6 | 边界 | margin/border/padding/Stage 中断 | 停止递归 | 已累积结果保留 | AC-2.2 |
| R-7 | 行为 | Stage 根 | 接入系统页级 safe area | 普通节点用自身 padding | AC-2.3 |
| R-8 | 恢复 | 几何/方向/padding 变化 | 使缓存失效并重算 | 使用最新方向 | AC-2.4 |
| R-9 | 行为 | Dynamic/Static 等价输入 | 形成等价属性 | SDK 类型为准 | AC-3.1 |
| R-10 | 边界 | 公共 C API 清单 | 标记 safeAreaPadding 未公开 | 内部 modifier 非公共 | AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | Parser/Resource/RTL UT | 全设置形式与非法值 |
| VM-2 | AC-2.1~AC-2.4 | SAE 祖先树 UT | 累积、中断、缓存 |
| VM-3 | AC-3.1~AC-3.2 | Dynamic/Static/C API 审查 | 通道边界 |

## API 变更分析

### 新增 API

N/A，`safeAreaPadding` 为 Dynamic API 14、Static API 23 已有能力。

### 变更/废弃 API

N/A；公开 C Node 未实现，不在文档中虚构。

## 接口规格

### 接口定义

**safeAreaPadding(paddingValue)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `safeAreaPadding(paddingValue: Padding | LengthMetrics | LocalizedPadding): T` |
| 返回值 | T — 当前组件 |
| 开放范围 | Public（ArkTS） |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| paddingValue | Padding/LengthMetrics/LocalizedPadding | 是 | 无 | 边值非负；支持 Resource 和 undefined reset |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 连续祖先均配置 | SAE 递归累积 | AC-2.1 |
| 2 | 中间存在 margin/border/padding | 在该层停止 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 是；Dynamic API 14，Localized/Static 能力按 SDK 版本演进。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 14。
- **API 版本号策略:** Dynamic API 14、Static API 23；C Node 未公开。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 独立属性 | safeAreaPadding 不等同普通 padding | AC-1.1 |
| 连续性 | margin/border/padding 会截断 SAE | AC-2.2 |
| 跨 Feat 消费 | 本 Feat 产出 SAE，ignoreLayoutSafeArea 消费 | AC-2.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 首次查询沿祖先链线性，缓存后复用 | Trace | `frameworks/core/components_ng/layout/layout_wrapper.cpp:576-605` |
| 功耗 | 无后台任务 | 审查 | VM-2 |
| 内存 | 每节点固定四边属性和缓存 | 内存审查 | VM-2 |
| 安全 | Resource 解析无权限数据 | 审查 | VM-1 |
| 可靠性 | 非法值和中断链不产生负范围 | 边界 UT | VM-1, VM-2 |
| 可测试性 | 祖先树与方向可参数化 | UT | VM-1~VM-3 |
| 自动化维测 | 属性和累计结果可 Dump | Inspector | AC-2.1 |
| 定界定位 | parser/property/layout wrapper 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 系统页级 top/bottom 常见 | Stage 输入参与 | 真机测试 | AC-2.3 |
| 平板 | 多窗口安全边界变化 | 缓存失效重算 | 多窗口测试 | AC-2.4 |
| 折叠屏 | RTL/姿态和 cutout 可变化 | 本地化边重新映射 | 折叠态测试 | AC-1.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 仅几何安全边界 | VM-1 |
| 大字体 | 是 | 普通 padding/布局变化可截断 SAE | AC-2.2 |
| 深色模式 | 否 | 不涉及颜色 | VM-1 |
| 多窗口/分屏 | 是 | 缓存和页级输入按窗口更新 | AC-2.4 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | API 14/23 边界需回归 | AC-3.1 |
| 生态兼容 | 是 | C API 边界不得虚构 | AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: SAE 累积
  Scenario: 普通 padding 截断累积
    Given 子节点和两层祖先均设置 safeAreaPadding
    And 中间祖先设置普通 padding
    When 子节点查询累计 SAE
    Then 累积在中间祖先停止且不包含更外层安全区
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 全形式、RTL、资源、累积、中断与缓存边界明确
- [x] C API 未开放边界明确
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "safeAreaPadding SAE accumulation localized padding Stage"
  - repo: "openharmony/interface_sdk-js"
    query: "CommonMethod safeAreaPadding API 14"
```

**关键文档：** `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md`
