# 特性规格

> `ComponentUtils.getRectangleById` 的实例路由、几何查询、兼容和前端行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组件几何信息查询 |
| 特性编号 | Func-04-11-01-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 10+；API 18+ 推荐 UIContext |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `UIContext.getComponentUtils().getRectangleById(id)` 与历史 `componentUtils.getRectangleById(id)` 的行为规格 | 补录 API 10 起已有实现，包括实例路由、返回字段和异常语义 |
| ADDED | 尺寸、三类坐标、平移、缩放、旋转和 4×4 变换矩阵规则 | 覆盖 `ComponentInfo` 的 8 个必填字段 |
| MODIFIED | 历史模块级入口的版本状态 | API 18 起标记废弃，迁移到 `UIContext.ComponentUtils#getRectangleById`，运行时能力未删除 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/11-component-info/01-component-utils/design.md` | Baselined |
| Canonical SDK | `interface/sdk-js/api/@ohos.arkui.componentUtils.d.ts` | 已核对 |
| Canonical SDK | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` | 已核对 |
| NAPI 实现 | `interfaces/napi/kits/componentutils/js_component_utils.cpp` | 已实现 |
| ANI 实现 | `interfaces/ets/ani/componentUtils/src/componentUtils.cpp` | 已实现 |
| 查询核心 | `frameworks/core/components_ng/base/inspector.cpp` | 已实现 |
| 单元测试 | `test/unittest/core/base/inspector_test_ng.cpp` | 已有底层覆盖 |

## 用户故事

### US-1: 实例绑定入口与版本迁移

**作为** 多窗口或多实例应用开发者，  
**我想要** 从当前 `UIContext` 获取绑定实例的 `ComponentUtils` 并查询组件，  
**以便** 查询始终落到调用方所属的 UI 执行上下文。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 同一 `UIContext` 连续调用 `getComponentUtils()` THEN 返回同一个绑定该 `instanceId` 的 `ComponentUtils` 对象 | 正常 |
| AC-1.2 | WHEN 通过 `UIContext.getComponentUtils().getRectangleById(id)` 查询 THEN 调用在目标 `UIContext` 的实例作用域内同步执行并返回 `ComponentInfo` | 正常 |
| AC-1.3 | WHEN API 10 至 API 17 应用调用模块级 `componentUtils.getRectangleById(id)` THEN 按既有公开签名同步返回 `ComponentInfo` | 正常 |
| AC-1.4 | WHEN API 18 及以上应用仍调用模块级入口 THEN 接口保持可调用但编译期显示废弃信息，迁移目标为 `UIContext.ComponentUtils#getRectangleById` | 边界 |
| AC-1.5 | WHEN 当前容器无法取得有效 UI 执行上下文或前端代理 THEN 调用抛出错误码 `100001`，而不是返回部分结果 | 异常 |

### US-2: 节点查找与几何坐标

**作为** 应用开发者，  
**我想要** 通过组件 `id` 获取绘制区域尺寸及本地、窗口、屏幕坐标，  
**以便** 实现定位、联动和调试能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `id` 匹配当前 Pipeline 的主节点树组件 THEN 以 px 返回 frame size、localOffset、windowOffset 和 screenOffset | 正常 |
| AC-2.2 | WHEN `id` 匹配 Inspector 离屏节点集合中的组件 THEN 离屏节点参与查询并返回其当前几何信息 | 正常 |
| AC-2.3 | WHEN `id` 不存在 THEN 不抛 `100001`，返回零尺寸/偏移/变换分解和单位 transform 矩阵 | 异常 |
| AC-2.4 | WHEN 被查询节点运行于 dynamic component 容器 THEN `windowOffset` 等于节点窗口相对偏移加宿主父级窗口偏移 | 边界 |
| AC-2.5 | WHEN 生成 `screenOffset` THEN x/y 分别等于 `windowOffset` 加当前窗口矩形的 x/y 偏移 | 正常 |
| AC-2.6 | WHEN 节点存在但 RenderContext 或 PipelineContext 不可用 THEN 已写入字段保持当前值，未写入字段保持默认值，查询不伪造后续几何数据 | 异常 |

### US-3: 变换分解与单位换算

**作为** 应用开发者，  
**我想要** 同时获得组件的平移、缩放、旋转中心和变换矩阵，  
**以便** 在组件经过视觉变换后仍能复现其几何状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 节点未显式设置 transform scale THEN 返回 scale.x=1、scale.y=1、scale.z=1 | 边界 |
| AC-3.2 | WHEN transform center 未显式设置 THEN 以未变换绘制矩形宽高的 50% 作为 centerX/centerY，并转换为 vp | 边界 |
| AC-3.3 | WHEN transform center 使用 PX 或 PERCENT THEN PX 直接换算为 vp；PERCENT 按未变换绘制矩形对应轴尺寸换算后再转为 vp | 正常 |
| AC-3.4 | WHEN translate.x/y 使用 PERCENT 且未变换绘制矩形有效 THEN 分别按矩形宽/高换算；其他单位和 translate.z 直接转换为 vp | 正常 |
| AC-3.5 | WHEN 组件具有旋转变换 THEN rotate 返回 x/y/z 轴、angle 及与 scale 共用的 centerX/centerY | 正常 |
| AC-3.6 | WHEN 返回 transform THEN 公开契约为固定 16 个 number 的列优先四阶矩阵 | 正常 |

### US-4: 多前端返回一致性与已知偏差

**作为** ArkTS 动态、ArkTS 静态和 CJ 运行时维护者，  
**我想要** 明确各前端对同一内部 `Rectangle` 的封装行为，  
**以便** 兼容性验证能够发现而不是掩盖通道差异。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN NAPI 返回 `ComponentInfo` THEN 对象包含 size、localOffset、windowOffset、screenOffset、translate、scale、rotate、transform 8 个必填字段 | 正常 |
| AC-4.2 | WHEN NAPI 封装 transform THEN 虽使用行列交换式中间下标，最终数组索引 0 至 15 与内部矩阵同序 | 正常 |
| AC-4.3 | WHEN ANI 封装 transform THEN 当前实现创建 16 元素集合，索引 1 至 15 从内部矩阵复制，索引 0 保持默认值 0 | 边界 |
| AC-4.4 | WHEN CJ FFI 封装 transform THEN 分配 16 个 `float` 并按内部矩阵索引 0 至 15 直接复制 | 正常 |
| AC-4.5 | WHEN 对多前端执行一致性验证 THEN 将 ANI 索引 0 默认值和 CJ float 精度记录为偏差，不在规格补录中推导源码修复 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.2 | R-1~R-3 | 已有实现 | JS/ANI 集成测试、代码评审 | `jsUIContext.js:599-604,1352-1369`; `UIContextImpl.ets:267-279` |
| AC-1.3~AC-1.4 | R-4 | 已有实现 | SDK API 检查 | `@ohos.arkui.componentUtils.d.ts:826-847` |
| AC-1.5 | R-5 | 已有实现 | NAPI 异常注入 | `js_component_utils.cpp:45-67` |
| AC-2.1~AC-2.2 | R-6~R-7 | 已有实现 | Inspector UT | `inspector.cpp:636-660,690-705` |
| AC-2.3, AC-2.6 | R-8~R-9 | 已有实现 | Inspector UT | `inspector_test_ng.cpp:494-519,1479-1515` |
| AC-2.4~AC-2.5 | R-10~R-11 | 已有实现 | Inspector UT、桥接 UT | `inspector.cpp:706-714`; `inspector_test_ng.cpp:1264-1317` |
| AC-3.1~AC-3.5 | R-12~R-15 | 已有实现 | Inspector UT | `inspector.cpp:723-770`; `inspector_test_ng.cpp:1319-1417` |
| AC-3.6 | R-16 | 已有实现 | SDK 类型检查 | `@ohos.arkui.componentUtils.d.ts:786-824` |
| AC-4.1~AC-4.5 | R-17~R-20 | 已有实现 | XTS、跨前端评审 | `ComponentUtils.test.ets:48-203`; NAPI/ANI/CJ 封装源码 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 同一 UIContext 首次调用 `getComponentUtils()` | 创建并缓存绑定当前 instanceId 的 ComponentUtils | 每个 UIContext 独立缓存 | AC-1.1 |
| R-2 | 行为 | 同一 UIContext 再次调用 `getComponentUtils()` | 返回已缓存对象 | 不重复创建 | AC-1.1 |
| R-3 | 恢复 | UIContext 入口执行查询，无论正常返回或抛异常 | 动态前端恢复调用前 instanceId | `withInstanceId` 使用 `finally` 恢复 | AC-1.2 |
| R-4 | 边界 | target API ≥18 使用模块级入口 | 接口仍存在但标记 deprecated，指向 UIContext 入口 | 不视为运行时删除 | AC-1.3, AC-1.4 |
| R-5 | 异常 | 无法获取有效 FrontendDelegate | 抛 `100001` | 仅 UI 执行上下文错误使用该错误码 | AC-1.5 |
| R-6 | 行为 | 使用 inspectorId 查找节点 | 先遍历离屏节点集合，再遍历根节点树 | 默认不跳过离屏节点 | AC-2.1, AC-2.2 |
| R-7 | 行为 | 找到有效 FrameNode 和 RenderContext | 填充 frame size、localOffset、windowOffset | localOffset 来自含变换 PaintRect 偏移 | AC-2.1 |
| R-8 | 异常 | inspectorId 未命中任何节点 | 提前返回，Rectangle 保持默认初始化 | 不抛 `100001` | AC-2.3 |
| R-9 | 恢复 | RenderContext/PipelineContext 缺失 | 停止后续字段计算 | 已写字段不回滚，未写字段为默认值 | AC-2.6 |
| R-10 | 边界 | dynamic render 且 UIContentType 为 DYNAMIC_COMPONENT | windowOffset 增加 hostParentOffsetToWindow | 其他容器不增加 | AC-2.4 |
| R-11 | 行为 | 封装 screenOffset | screenOffset = windowOffset + currentWindowRect.offset | x/y 分别计算 | AC-2.5 |
| R-12 | 边界 | 未设置 scale | x/y 使用 1，z 固定为 1 | 找到有效节点后成立 | AC-3.1 |
| R-13 | 边界 | 未设置 transform center | 使用 50%/50% | PaintRect 无效时 center 保持 0 | AC-3.2 |
| R-14 | 行为 | center 为 PX/PERCENT | 按单位转换为 vp | PERCENT 依赖有效 PaintRect 宽高 | AC-3.3 |
| R-15 | 行为 | translate 为 PERCENT/其他单位 | x/y 百分比按宽高换算，其他值直接转 vp | z 不使用矩形尺寸 | AC-3.4, AC-3.5 |
| R-16 | 行为 | 公开返回 transform | 固定 16 个 number，语义为列优先四阶矩阵 | 数组长度必须等于 16 | AC-3.6 |
| R-17 | 行为 | NAPI 封装 Rectangle | 创建 8 字段对象 | 所有字段必填 | AC-4.1 |
| R-18 | 行为 | NAPI 封装 matrix4 | 两阶段索引映射后最终保持内部 0~15 顺序 | 固定 16 元素 | AC-4.2 |
| R-19 | 边界 | ANI/CJ 封装 matrix4 | ANI 复制索引 1~15；CJ 复制索引 0~15 | ANI 索引 0 为默认 0 | AC-4.3, AC-4.4 |
| R-20 | 异常 | 多前端矩阵结果不一致 | 验证结果标记兼容性偏差 | 规格补录不改变既有实现 | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.2, R-1~R-3 | UIContext 集成测试 | 对象缓存、instanceId 路由与异常后恢复 |
| VM-2 | AC-1.3~AC-1.4, R-4 | SDK API 扫描 | API 10/11/12/18 标签和迁移指引 |
| VM-3 | AC-1.5, R-5 | NAPI 故障注入 | Delegate 缺失时抛 `100001` |
| VM-4 | AC-2.1~AC-2.3, R-6~R-8 | Inspector UT | 主树、离屏节点、未知 ID |
| VM-5 | AC-2.4~AC-2.6, R-9~R-11 | Inspector UT | 动态组件、屏幕坐标、空上下文 |
| VM-6 | AC-3.1~AC-3.5, R-12~R-15 | Inspector UT | 默认 scale、PX/PERCENT center、translate 换算 |
| VM-7 | AC-3.6, R-16 | SDK 类型/XTS | 16 元素列优先矩阵契约 |
| VM-8 | AC-4.1~AC-4.5, R-17~R-20 | 现有 NAPI XTS + ANI/CJ 对比 | 字段完整性、矩阵索引与精度偏差 |

## API 变更分析

### 新增 API

> 以下为历史已新增 API 的规格补录，不代表本次文档变更新增产品接口。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `UIContext.getComponentUtils()` | Public | 无 | `ComponentUtils` | 无 | 获取绑定当前 UIContext 的组件查询对象 | AC-1.1 |
| `ComponentUtils.getRectangleById(id: string)` | Public | 必填组件 id | `componentUtils.ComponentInfo` | `100001` | 查询组件几何与变换信息 | AC-1.2, AC-1.5, AC-2.1~AC-3.6 |

**C-API（NDK）通道：** 未发现与该公开能力等价的 ArkUI NDK C-API；CJ FFI 为独立语言桥接，不登记为 NDK Public API。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `componentUtils.getRectangleById(id: string)` | 废弃 | API 18 及以上继续使用模块级入口的应用 | 改为从目标窗口/页面的 `UIContext` 获取 `ComponentUtils` 后调用同名方法 | AC-1.3, AC-1.4 |

## 接口规格

### 接口定义

**UIContext.getComponentUtils**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getComponentUtils(): ComponentUtils` |
| 返回值 | `ComponentUtils` — 与当前 UIContext 实例绑定的查询对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

无参数。

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 同一 UIContext 重复调用 | 返回同一缓存对象 | AC-1.1 |
| 2 | 不同 UIContext 分别调用 | 返回绑定各自 instanceId 的对象 | AC-1.2 |

**ComponentUtils.getRectangleById**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getRectangleById(id: string): componentUtils.ComponentInfo` |
| 返回值 | `ComponentInfo` — 8 个必填几何与变换字段 |
| 开放范围 | Public |
| 错误码 | `100001`：UI execution context not found |
| 关联 AC | AC-1.2~AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| id | string | 是 | 无 | 作为 inspector id 搜索键；仅当主树和离屏节点均未命中时返回默认值 |

**返回字段:** `size` 和三类 offset 使用 px；`translate` 与变换中心按实现换算为 vp；`scale`、`rotate` 表示变换分解；`transform` 为固定 16 个 number 的列优先四阶矩阵。8 个字段均必填。

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效 id 和执行上下文 | 返回完整 ComponentInfo | AC-2.1, AC-3.1~AC-3.6 |
| 2 | id 未命中 | 返回默认初始化 ComponentInfo | AC-2.3 |
| 3 | 执行上下文缺失 | 抛出 `100001` | AC-1.5 |
| 4 | dynamic component | windowOffset 叠加宿主偏移 | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是。API 18 起模块级 `componentUtils.getRectangleById` 仅增加废弃标记和迁移指引，运行时行为未删除；推荐使用绑定 UIContext 的实例入口。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 10；Atomic Service 自 API 11 支持；`ComponentInfo` 相关类型自 API 12 标注跨平台。
- **API 版本号策略:** API 10 为基础能力，API 11 增加 `@atomicservice`，API 12 完善类型的 `@crossplatform` 标记，API 18 废弃模块级入口。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 实例作用域 | UIContext 入口必须在绑定 instanceId 的作用域内同步调用并恢复原作用域 | AC-1.1, AC-1.2 |
| 当前 Pipeline 查询 | 节点查找依赖当前 PipelineContext，不跨窗口或跨进程搜索 | AC-1.5, AC-2.1~AC-2.3 |
| 只读查询 | 查询不得修改 FrameNode、GeometryNode 或 RenderContext 状态 | AC-2.1~AC-3.6 |
| 坐标单位一致 | 百分比先按未变换绘制矩形换算，再输出 vp | AC-3.2~AC-3.4 |
| 偏差可见 | 多前端封装差异必须在验证结果中显式呈现 | AC-4.2~AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次查询为同步操作；现有公开契约不承诺固定时延，离屏节点数量增长不得改变返回语义 | 性能回归、节点规模分档测试 | `inspector.cpp:636-660` |
| 安全 | 仅查询当前 UI 执行上下文中的公开组件几何，不新增权限和跨进程访问 | 权限审查 | SDK 无权限声明 |
| 可靠性 | 未命中 id 与上下文缺失必须使用不同可观测结果 | 异常注入 | AC-1.5, AC-2.3 |
| 可测试性 | AC 映射到 Inspector UT、NAPI XTS、SDK 检查或跨前端对比 | 追溯审查 | VM-1~VM-8 |
| 定界定位 | 上下文缺失保留错误码 `100001`；节点未命中保留日志和默认值 | 日志/错误码检查 | `js_component_utils.cpp:58-67`; `inspector.cpp:692-695` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无设备类型差异 | size/offset 为 px，translate/center 按实现转 vp | 集成测试 | AC-2.5, AC-3.3 |
| 平板 | 无设备类型差异 | 多窗口下必须绑定目标 UIContext | 分屏/自由窗口测试 | AC-1.2, AC-2.5 |
| 折叠屏 | 无设备类型差异 | 窗口矩形变化后返回当前 screenOffset | 折叠状态切换测试 | AC-2.5 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 仅查询几何，不修改语义树 | — |
| 大字体 | 间接适用 | 大字体引发布局变化时 size/offset 返回最新布局结果 | AC-2.1 |
| 深色模式 | 否 | 与颜色和主题无关 | — |
| 多窗口/分屏 | 是 | 必须通过正确 UIContext 绑定目标实例，screenOffset 受窗口矩形影响 | AC-1.2, AC-2.5 |
| 多用户 | 否 | 不访问用户数据 | — |
| 版本升级 | 是 | API 18 入口迁移不得改变返回类型和错误码 | AC-1.4 |
| 生态兼容 | 是 | ANI 矩阵索引 0 与 CJ float 精度差异需持续监测 | AC-4.2~AC-4.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ComponentUtils 组件几何信息查询
  作为 应用开发者
  我想要 在正确的 UIContext 中查询组件几何与变换信息
  以便 实现可靠的定位、联动和调试能力

  Scenario: 从 UIContext 查询有效组件
    Given 当前 UIContext 对应的组件树中存在 inspector id 为 "target" 的节点
    When 调用 uiContext.getComponentUtils().getRectangleById("target")
    Then 返回包含 8 个必填字段的 ComponentInfo
    And 查询执行后恢复调用前的实例作用域

  Scenario: 查询不存在的组件 id
    Given 当前 UI 执行上下文有效
    And 当前主树及离屏节点集合均不存在 inspector id 为 "missing" 的节点
    When 调用 getRectangleById("missing")
    Then 不抛出错误码 100001
    And 返回默认初始化的 ComponentInfo

  Scenario: UI 执行上下文缺失
    Given 当前容器无法取得 FrontendDelegate
    When 调用 getRectangleById("target")
    Then 抛出错误码 100001

  Scenario: 百分比平移换算
    Given 未变换绘制矩形宽为 200vp 高为 100vp
    When translate 设置为 x=50% y=20%
    Then translate.x 为 100vp
    And translate.y 为 20vp
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 不包含 `getItemsInShapePath`）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 每条规则满足可复现、可观测、边界明确、关联 AC、无冲突要求
- [x] 公开 API 已与 canonical SDK 类型定义交叉核对
- [x] 多前端实现偏差已记录为风险，没有推导源码修复方案

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ComponentUtils getRectangleById 的 UIContext/NAPI/ANI/CJ 路由、Inspector 节点查找、坐标与变换换算实现"
  - repo: "openharmony/interface_sdk-js"
    query: "componentUtils.ComponentInfo、ComponentUtils.getRectangleById 与 UIContext.getComponentUtils 的 API 10-18 契约"
```

**关键文档：** `interface/sdk-js/api/@ohos.arkui.componentUtils.d.ts`、`interface/sdk-js/api/@ohos.arkui.UIContext.d.ts`、`frameworks/core/components_ng/base/inspector.cpp`。
