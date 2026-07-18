# 特性规格

> Func-05-01-08-Feat-03 RelativeContainer 辅助线、屏障与 RTL：补录 guideline、physical/localized barrier、ID 过滤、极值计算、资源更新和 RTL 镜像。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | RelativeContainer 辅助线、屏障与 RTL |
| 特性编号 | Func-05-01-08-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 12–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

RelativeContainer 在 API 12 增加 guideline 和 barrier 虚拟锚点。Guideline 由唯一 ID、方向和 start/end 位置定义；Barrier 由唯一 ID、方向及一组 referencedId 定义，并取引用节点边界的极值。LocalizedBarrierDirection 用 START/END 支持 RTL。公开声明见 `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:45-421`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Guideline 规格 | 覆盖 ID、方向、start/end、默认值、auto/百分比限制、资源更新 |
| ADDED | Barrier 规格 | 覆盖 physical/localized 方向、referencedId、极值、缺失/GONE 引用 |
| ADDED | 虚拟锚点过滤与依赖 | 覆盖空/重复 ID、barrier-to-barrier 和错误轴使用 |
| ADDED | RTL 规格 | 覆盖 START/END 归一化和最终子项水平镜像 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/08-relative-container/design.md` | 已补录 |
| Relative SDK | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts` | 已核对 |
| Model/Property | `frameworks/core/components_ng/pattern/relative_container/relative_container_model_ng.cpp`、`relative_container_layout_property.h` | 已核对 |
| ArkTS Bridge | `frameworks/core/components_ng/pattern/relative_container/bridge/arkts_native_relative_container_bridge.cpp` | 已核对 |
| Dynamic modifier | `frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp` | 已核对 |
| Layout algorithm | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp` | 已核对 |

> Public Native option 生命周期归 Feat-05；本文只定义布局语义。

## 用户故事

### US-1: 定义并使用 guideline

**作为** 相对布局开发者  
**我想要** 在容器指定固定或资源化辅助线  
**以便** 多个子项共享同一位置锚点

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN guideLine 数组含唯一非空 id、合法 direction 和 position THEN 将每项转换为虚拟锚点并参与 alignRules | 正常 |
| AC-1.2 | WHEN direction 缺失/非法 THEN 使用 Axis.Vertical；垂直 guideline 只为水平定位提供有效坐标，水平 guideline 只为垂直定位提供有效坐标 | 异常 |
| AC-1.3 | WHEN position 同时给 start/end THEN 仅 start 生效；WHEN 两者缺失或非法 THEN 使用 start=0 | 边界 |
| AC-1.4 | WHEN 容器对应轴为 auto THEN 该轴 guideline 必须使用非百分比 start；使用 end 或百分比 start 时算法不能从未定容器尺寸得到有效自适应位置 | 边界 |
| AC-1.5 | WHEN guideline position 使用 ResourceObject 且配置变化 THEN 重新解析位置并标记容器 Measure | 边界 |

### US-2: 用 barrier 聚合多个引用节点

**作为** 构建动态内容的开发者  
**我想要** 用屏障跟随一组组件的最外侧边界  
**以便** 后续组件避开其中最宽或最高的可见内容

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN direction=LEFT/START 或 TOP THEN barrier 坐标取有效引用 rect 的 minLeft/minTop | 正常 |
| AC-2.2 | WHEN direction=RIGHT/END 或 BOTTOM THEN barrier 坐标取有效引用 rect 的 maxRight/maxBottom | 正常 |
| AC-2.3 | WHEN referencedId 指向缺失节点、guideline 或 GONE 子项 THEN 该引用不进入有效 barrier rect；其他合法引用仍可决定坐标 | 边界 |
| AC-2.4 | WHEN barrier 引用另一 barrier THEN 依赖图先计算被引用 barrier，再计算当前 barrier | 正常 |
| AC-2.5 | WHEN barrier direction 缺失/非法 THEN physical API 使用 LEFT 默认；错误轴把 barrier 当 anchor 时该轴值为 0 | 异常 |

### US-3: 过滤非法虚拟锚点标识

**作为** 布局引擎维护者  
**我想要** 对空 ID、重复 ID 和与子项冲突的 ID 确定性处理  
**以便** 避免同名锚点覆盖产生随机布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN guideline/barrier id 为空 THEN 该虚拟锚点不加入有效 map | 异常 |
| AC-3.2 | WHEN id 与已有 child/guideline/barrier 重复 THEN 后续同名虚拟锚点被跳过，已有锚点不被覆盖 | 异常 |
| AC-3.3 | WHEN guideLine/barrier 属性 reset 或传入无效非数组 THEN 容器清空对应列表并在下一次 Measure 不再暴露这些虚拟锚点 | 边界 |

### US-4: 在 RTL 中使用 localized barrier

**作为** 双向语言页面开发者  
**我想要** 用 START/END 定义逻辑屏障  
**以便** LTR/RTL 自动镜像而无需维护两套配置

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN localizedDirection=START/END THEN 先归一化为逻辑水平边界；TOP/BOTTOM 不受文本方向影响 | 正常 |
| AC-4.2 | WHEN 容器为 RTL THEN 算法在所有锚点偏移计算后，以容器宽度、子项宽度和 padding 镜像每个子项 x offset | 正常 |
| AC-4.3 | WHEN 使用 physical LEFT/RIGHT barrier THEN 保持物理方向定义，不把 SDK 物理枚举重写为 START/END | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.5 | R-1~R-5 | 已有实现 | Guideline API/Layout/Resource UT | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:45-145`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:198-302` |
| AC-2.1~AC-2.5 | R-6~R-10 | 已有实现 | Barrier extrema/dependency UT | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:147-364`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:303-408` |
| AC-3.1~AC-3.3 | R-11~R-13 | 已有实现 | duplicate/reset UT | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:244-302`；`frameworks/core/components_ng/pattern/relative_container/bridge/arkts_native_relative_container_bridge.cpp:195-262` |
| AC-4.1~AC-4.3 | R-14~R-16 | 已有实现 | LTR/RTL localized/physical UT | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:205-262,317-364`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:2244-2278` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 |合法 GuideLineStyle 进入 Measure |按 direction 和 position 计算虚拟 offset 并注册 id | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:198-302` | AC-1.1 |
| R-2 | 异常 |guideline direction 缺失/非法或用在错误轴 |默认 Vertical；错误轴的 anchor 坐标按 0 处理 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:101-119` | AC-1.2 |
| R-3 | 边界 |position 同时有 start/end 或两者皆无 |start 优先；皆无时 start=0 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:121-144`；`frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp:50-83` | AC-1.3 |
| R-4 | 边界 |容器轴为 auto 且 guideline 使用 end/百分比 |该配置不满足 SDK 自适应约束；算法无法用未定轴尺寸稳定求值 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:121-144`；`frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:198-241` | AC-1.4 |
| R-5 | 恢复 |guideline Resource 配置变化 |Model 重新设置位置资源并标记 Measure | `frameworks/core/components_ng/pattern/relative_container/relative_container_model_ng.cpp:34-67`；`frameworks/core/components_ng/pattern/relative_container/bridge/relative_container_dynamic_modifier.cpp:50-83` | AC-1.5 |
| R-6 | 行为 |LEFT/START 或 TOP barrier 有有效引用 |分别写 minLeft 或 minTop | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:348-408` | AC-2.1 |
| R-7 | 行为 |RIGHT/END 或 BOTTOM barrier 有有效引用 |分别写 maxRight 或 maxBottom | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:348-408` | AC-2.2 |
| R-8 | 边界 |引用缺失、guideline 或 GONE child |跳过该 referencedId，不阻断其余有效引用 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:348-392,1517-1528` | AC-2.3 |
| R-9 | 行为 |barrier 引用 barrier |被引用 barrier 进入依赖图并先完成 offset | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:1377-1385,1512-1534` | AC-2.4 |
| R-10 | 异常 |physical barrier direction 缺失/非法或用在错误轴 |公开默认 LEFT；错误轴 anchor 值为 0 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:264-315` | AC-2.5 |
| R-11 | 异常 |虚拟锚点 id 为空 |CalcGuideline/CalcBarrier 跳过 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:244-302` | AC-3.1 |
| R-12 | 异常 |虚拟锚点 id 已在 child/guide/barrier map |跳过重复项，不覆盖已有记录 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:244-302` | AC-3.2 |
| R-13 | 恢复 |bridge 输入不是数组或执行 reset |设置空 vector/reset Property，下一 Measure 清除虚拟锚点 | `frameworks/core/components_ng/pattern/relative_container/bridge/arkts_native_relative_container_bridge.cpp:195-262,289-423` | AC-3.3 |
| R-14 | 行为 |localizedDirection 为 START/END |算法映射到水平逻辑边界，TOP/BOTTOM 原样 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:2244-2253` | AC-4.1 |
| R-15 | 行为 |容器 layoutDirection=RTL |对 renderList 子项执行 `newX=containerWidth-nodeWidth-oldX-paddingWidth` | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:2255-2278` | AC-4.2 |
| R-16 | 边界 |使用 physical LEFT/RIGHT BarrierStyle |保持物理枚举，不等同 localized START/END | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:147-203,205-262` | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-5, AC-1.1~AC-1.5 | Guideline 参数化 UT |Horizontal/Vertical、start/end/none/both、auto、Resource |
| VM-2 | R-6~R-10, AC-2.1~AC-2.5 | Barrier rect UT |四方向、多个引用、缺失/GONE、barrier chain、错误轴 |
| VM-3 | R-11~R-13, AC-3.1~AC-3.3 | ID/reset UT |空、child 冲突、guide/barrier 重复、非数组、reset |
| VM-4 | R-14~R-16, AC-4.1~AC-4.3 | 2×方向×LTR/RTL UT |physical 与 localized 区分、最终 x 镜像 |

## API 变更分析

> 本次只补录 API 12 已有接口。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `guideLine(Array<GuideLineStyle>)` | Public |id/direction/start或end | RelativeContainerAttribute | N/A |设置辅助线 | AC-1.1~AC-1.5 |
| `barrier(Array<BarrierStyle>)` | Public |id/physical direction/referencedId | RelativeContainerAttribute | N/A |设置物理屏障 | AC-2.1~AC-3.3 |
| `barrier(Array<LocalizedBarrierStyle>)` | Public |id/localized direction/referencedId | RelativeContainerAttribute | N/A |设置 RTL 屏障 | AC-2.1~AC-4.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| physical barrier 水平方向 | 变更 |需要自动适配 RTL |改用 LocalizedBarrierStyle START/END overload | AC-4.1~AC-4.3 |

## 接口规格

### 接口定义

**guideLine(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `guideLine(value: Array<GuideLineStyle>): RelativeContainerAttribute` |
| 返回值 | RelativeContainerAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.5, AC-3.1~AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| id | string |是 |无 |非空、容器内唯一且不与 child 同名 |
| direction | Axis |是 |非法回退 Vertical |Horizontal/Vertical |
| position | GuideLinePosition |是 |start=0 |start/end 二选一；同时给出 start 优先 |

**barrier(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `barrier(value: Array<BarrierStyle \| LocalizedBarrierStyle>): RelativeContainerAttribute` |
| 返回值 | RelativeContainerAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| id | string |是 |无 |非空、唯一 |
| direction/localizedDirection |枚举 |是 |physical 非法回退 LEFT |LEFT/RIGHT/TOP/BOTTOM 或 START/END/TOP/BOTTOM |
| referencedId | Array<string> |是 |空数组 |只有有效、非 GONE 引用影响极值 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 |guideline start/end/auto/Resource |按优先级求坐标并响应更新 | AC-1.1~AC-1.5 |
| 2 |barrier 多引用/缺失/GONE/嵌套 |求有效 rect 极值或依赖排序 | AC-2.1~AC-2.5 |
| 3 |localized + RTL |归一化并镜像子项 x | AC-4.1~AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；guideLine/barrier/localized overload 均为 API 12 存量能力。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 12。
- **API 版本号策略:** 对外仅按 `@since 12 dynamic`；内部 runtime gate 不扩大 API 11 表面。

| API | 版本 | 证据 |
|-----|------|------|
| GuideLinePosition/Style | API 12 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:45-145` |
| BarrierStyle/Direction | API 12 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:147-315` |
| LocalizedBarrierStyle/Direction | API 12 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:205-364` |
| guideLine/barrier attributes | API 12 | `interface/sdk-js/api/@internal/component/ets/relative_container.d.ts:378-421` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
|虚拟锚点唯一性 |guide/barrier ID 不得覆盖 child 或已有虚拟锚点 | AC-3.1, AC-3.2 |
|轴语义 |Vertical guideline/LEFT-RIGHT barrier 服务水平定位；另一轴值为 0 | AC-1.2, AC-2.5 |
|依赖前置 |barrier 必须在全部有效引用完成后求极值 | AC-2.1~AC-2.4 |
|RTL 单点处理 |localized 归一化后由最终 AdjustOffsetRtl 镜像 | AC-4.1, AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 |每个 barrier 对 referencedId 线性扫描；不新增后台处理 |Trace/benchmark | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_algorithm.cpp:348-408` |
| 功耗 |只在 Measure 计算；资源变化事件驱动 |代码审查 | AC-1.5 |
| 内存 |guideline/barrier vector 随 Property；虚拟 offset 随算法 |内存基线 | `frameworks/core/components_ng/pattern/relative_container/relative_container_layout_property.h:25-51` |
| 安全 |ID 是布局标识，不涉及权限/敏感数据 |API 审查 | VM-3 |
| 可靠性 |空/重复 ID、缺失/GONE 引用、非法数组安全跳过/清空 |异常 UT/fuzz | AC-2.3, AC-3.1~AC-3.3 |
| 可测试性 |固定引用 rect 可精确断言四方向极值 |Layout UT | VM-2 |
| 自动化维测 |拓扑 Dump 可观察 barrier 依赖顺序 |Dump | Feat-02 VM-3 |
| 定界定位 |区分 Bridge、Property、virtual anchor、RTL 四层 |设计审查 | `05-ui-components/01-layout-components/08-relative-container/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 |无算法差异 |固定/百分比 guideline 受内容区宽高影响 |手机尺寸 UT | AC-1.1, AC-1.4 |
| 平板 |无算法差异 |较大引用 rect 改变 barrier 极值 |平板尺寸 UT | AC-2.1, AC-2.2 |
| 折叠屏 |尺寸/RTL 可动态变化 |重测后重新计算虚拟锚点和镜像 |折叠/展开集成测试 | AC-1.5, AC-4.2 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 |虚拟锚点不进入语义树，只改变子项视觉位置 | AC-1.1, AC-2.1 |
| 大字体 | 是 |引用节点尺寸变化会更新 barrier 极值 | AC-2.1, AC-2.2 |
| 深色模式 | 否 |不涉及颜色 |
| 多窗口/分屏 | 是 |内容区变化需重算 guideline/barrier | AC-1.4, AC-4.2 |
| 多用户 | 否 |无用户状态 |
| 版本升级 | 是 |API 12 表面与 localized 迁移需验证 | AC-4.1~AC-4.3 |
| 生态兼容 | 是 |start 优先、极值/GONE 和唯一 ID 行为必须保留 | AC-1.3, AC-2.3, AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: RelativeContainer 辅助线、屏障与 RTL
  Scenario: guideline 同时设置 start 和 end
    Given垂直 guideline 的 start 为 20vp 且 end 为 40vp
    When RelativeContainer 计算 guideline
    Then其水平坐标使用 start 20vp
    And end 40vp 不参与定位

  Scenario: RIGHT barrier 忽略 GONE 引用
    Given barrier 引用 A、B、C
    And A 右边为 50vp、B 为 GONE、C 右边为 120vp
    When计算 RIGHT barrier
    Then barrier 坐标为 120vp
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN，可独立测试
- [x]物理/localized、guide/barrier 与 Native 生命周期边界明确
- [x] API 12 对外版本未被内部 gate 扩大
- [x]每个 AC 与规则、VM 双向追溯
- [x]包含 start/end、auto、空/重复 ID、GONE 和 RTL 边界

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "RelativeContainer guideline barrier localized RTL extrema duplicate id"
  - repo: "openharmony/interface_sdk-js"
    query: "GuideLineStyle BarrierStyle LocalizedBarrierStyle API 12"
```

**关键文档：**

- Relative SDK：`interface/sdk-js/api/@internal/component/ets/relative_container.d.ts`
- 共享设计：`05-ui-components/01-layout-components/08-relative-container/design.md`
