# 特性规格

> Func-04-02-01-Feat-02 渲染安全区扩展存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 渲染安全区扩展 |
| 特性编号 | Func-04-02-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

`expandSafeArea` 允许组件的渲染边界扩展到 SYSTEM、CUTOUT、KEYBOARD 非安全区；本特性覆盖类型/边枚举、默认与空数组、非法值、边界相交、固定尺寸、滚动祖先、位置优先级及 Dynamic/Static/C Node 通道。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | expandSafeArea 接口 | 补录类型、边、默认、reset 和非法值 |
| ADDED | 渲染几何规则 | 补录相交、固定尺寸、滚动容器与父子调整 |
| ADDED | 多通道和版本 | 补录 Dynamic API 10、C Node API 12、Static API 23 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/common.static.d.ets` | 已核对 |
| JS parser | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 已核对 |
| LayoutWrapper | `frameworks/core/components_ng/layout/layout_wrapper.cpp` | 已核对 |
| Native SDK | `interfaces/native/node_attributes/layout.h` | 已核对 |

## 用户故事

### US-1: 声明需要扩展的安全区

**作为** 应用开发者  
**我想要** 选择安全区类型和边  
**以便** 背景或内容延伸到系统非安全区域

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN expandSafeArea() 不传参数 THEN types 默认 SYSTEM/CUTOUT/KEYBOARD，edges 默认 TOP/BOTTOM/START/END | 正常 |
| AC-1.2 | WHEN types=[] 且 edges=[] THEN 形成 NONE 设置且当前节点不扩展 | 边界 |
| AC-1.3 | WHEN 数组含非法枚举或解析失败 THEN parser 按实现回退默认 ALL 掩码，不产生越界 bit | 异常 |
| AC-1.4 | WHEN expandSafeArea 使用 START/END THEN START 固定表示物理左边、END 固定表示物理右边，LTR/RTL 切换不重映射该扩展掩码 | 边界 |

### US-2: 按几何和父容器条件扩展

**作为** 布局渲染管线  
**我想要** 只在满足条件时修改 paint rect  
**以便** 不破坏组件布局尺寸

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 非 KEYBOARD 类型且组件边界与目标安全区相交 THEN paint rect 向所选边扩展 | 正常 |
| AC-2.2 | WHEN 组件固定宽高 THEN 保持布局尺寸，只有 TOP/START 等符合实现条件的边可调整绘制位置；aspectRatio 继续约束高度 | 边界 |
| AC-2.3 | WHEN 父容器可滚动 THEN 当前节点自身扩展被取消，但仍可处理具有 expandSafeArea 的子节点范围更新 | 边界 |
| AC-2.4 | WHEN position/offset 等先改变边界 THEN 先应用位置再判定 expandSafeArea 是否与非安全区相交 | 正常 |

### US-3: 使用多入口设置与重置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN Dynamic、Static 或公开 C Node 设置等价 types/edges THEN 节点保存等价 ExpandSafeAreaOpts | 正常 |
| AC-3.2 | WHEN C Node NODE_EXPAND_SAFE_AREA 收到非法 item THEN 返回既有参数错误/拒绝结果且不写非法状态 | 异常 |
| AC-3.3 | WHEN属性 reset/undefined THEN 清除或恢复当前入口的默认 ExpandSafeAreaOpts | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | Parser/方向矩阵测试 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:8996-9093,19606-19670`; `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:9978-10009`; `frameworks/core/components_ng/layout/layout_wrapper.cpp:639-658` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | LayoutWrapper UT | `frameworks/core/components_ng/layout/layout_wrapper.cpp:324-390,639-679` |
| AC-3.1~AC-3.3 | R-9~R-11 | 已有实现 | Static/CAPI UT | `interfaces/native/native_node.h:1888-1903`; `interfaces/native/node_attributes/layout.h:677-691` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 参数省略 | 使用全类型/全边默认 | Dynamic API 10 | AC-1.1 |
| R-2 | 边界 | 两数组为空 | 保存 NONE | 不扩展 | AC-1.2 |
| R-3 | 异常 | 非法枚举/解析失败 | 回退默认掩码 | 不保留非法 bit | AC-1.3 |
| R-4 | 边界 | START/END | 分别使用物理左/右边 | expand 不随 RTL 镜像；与 padding/ignore 语义不同 | AC-1.4 |
| R-5 | 行为 | 边界相交 | 扩展 paint rect | 非键盘需相交 | AC-2.1 |
| R-6 | 边界 | 固定尺寸/aspectRatio | 保持布局尺寸并按实现限制边扩展 | 不放大固定尺寸 | AC-2.2 |
| R-7 | 边界 | 可滚动父容器 | 取消自身扩展 | 子节点更新仍可执行 | AC-2.3 |
| R-8 | 行为 | 同时有 position/offset | 先定位后判定扩展 | 以新边界相交为准 | AC-2.4 |
| R-9 | 行为 | 多入口等价输入 | 保存等价 opts | SDK 枚举为准 | AC-3.1 |
| R-10 | 异常 | C Node item 非法 | 拒绝且不写状态 | 返回既有错误 | AC-3.2 |
| R-11 | 恢复 | reset/undefined | 清除或恢复默认 opts | 按入口语义 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.4 | Parser/枚举/方向矩阵测试 | 默认、空、非法及 expand START/END 的物理边固定语义 |
| VM-2 | AC-2.1~AC-2.4 | `expand_safe_area_test_ng.cpp` | 几何生效条件 |
| VM-3 | AC-3.1~AC-3.3 | Static/C Node UT | 通道等价与 reset |

## API 变更分析

### 新增 API

N/A，`expandSafeArea` 为 API 10 已有接口；C Node 属性为 API 12 已有能力。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**expandSafeArea(types?, edges?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `expandSafeArea(types?: Array<SafeAreaType>, edges?: Array<SafeAreaEdge>): T` |
| 返回值 | T — 当前组件 |
| 开放范围 | Public |
| 错误码 | ArkTS N/A；C Node 使用既有 attribute result |
| 关联 AC | AC-1.1~AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| types | SafeAreaType[] | 否 | SYSTEM/CUTOUT/KEYBOARD | 空数组表示 NONE；非法值回退 |
| edges | SafeAreaEdge[] | 否 | TOP/BOTTOM/START/END | START=物理左、END=物理右，不随 RTL 重映射 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 无参且边界相交 | 按全部默认类型和边扩展 | AC-1.1, AC-2.1 |
| 2 | 空数组或滚动父容器 | 不执行当前节点自身扩展 | AC-1.2, AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 是；Dynamic API 10、C Node API 12、Static API 23 分阶段开放。
- **配置文件格式变更:** 否；CUTOUT 仍受应用 metadata 影响。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 10。
- **API 版本号策略:** API 10/12/23/26 全量记录；公共枚举以 SDK 为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| Layout/Paint 分离 | expand 改绘制边界，不直接改变子组件布局 | AC-2.1 |
| 几何前置 | 位置和固定尺寸先影响相交判定 | AC-2.2, AC-2.4 |
| SDK 权威 | C/内部 bit 不得扩展公共枚举契约 | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每节点按固定边集合计算，无全树额外扫描 | Trace | `frameworks/core/components_ng/layout/layout_wrapper.cpp:639-679` |
| 功耗 | 随布局/渲染触发，无后台任务 | 审查 | VM-2 |
| 内存 | 每节点保存固定 opts | 内存审查 | VM-3 |
| 安全 | 系统区域内事件仍可能由系统优先拦截 | 集成测试 | SDK `common.d.ts:19634-19636` |
| 可靠性 | 空/非法输入和不相交场景安全无效果 | 边界 UT | VM-1, VM-2 |
| 可测试性 | paint rect 和 opts 可断言 | UT | VM-1~VM-3 |
| 自动化维测 | LayoutWrapper/RenderContext 可 Dump | Inspector | AC-2.1 |
| 定界定位 | parser→property→layout wrapper 分层 | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 状态栏/导航栏/键盘常见 | 按相交与类型扩展 | 真机测试 | AC-2.1 |
| 平板 | 多窗口和浮动导航常见 | 使用当前窗口 inset | 多窗口测试 | AC-3.1 |
| 折叠屏 | cutout 随姿态变化，expand START/END 保持物理边 | 重新执行相交判定但不做 RTL 镜像 | 折叠态测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 扩展不改变语义树 | AC-2.1 |
| 大字体 | 是 | 内容尺寸可能改变相交边界 | AC-2.4 |
| 深色模式 | 是 | 背景可延伸但颜色由组件决定 | AC-2.1 |
| 多窗口/分屏 | 是 | 窗口安全区独立 | AC-3.1 |
| 多用户 | 否 | 无用户状态 | VM-1 |
| 版本升级 | 是 | API 10/12/23 边界需回归 | 兼容性声明 |
| 生态兼容 | 是 | 固定尺寸和滚动限制保持 | AC-2.2, AC-2.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 渲染安全区扩展
  Scenario: 滚动父容器限制自身扩展
    Given 子组件设置 expandSafeArea 且父组件可滚动
    When 执行布局与绘制边界调整
    Then 当前子组件不进行自身扩展但其后代更新仍可处理
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 默认、空、非法、物理 START/END、固定尺寸和滚动边界明确
- [x] ArkTS/C Node 通道已核对
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "expandSafeArea LayoutWrapper scroll fixed size RTL"
  - repo: "openharmony/interface_sdk-js"
    query: "CommonMethod expandSafeArea SafeAreaType SafeAreaEdge"
```

**关键文档：** `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md`
