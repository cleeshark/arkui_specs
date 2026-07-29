# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 嵌套滚动与内容边界 |
| 特性编号 | Func-05-03-01-Feat-03 |
| 所属 Epic | 滚动公共能力长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 10-26 已有能力补录 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性规定 `List`、`Grid`、`Scroll`、`WaterFlow` 共享的嵌套滚动模式、父子位移与惯性分配、越界协同、递归起止生命周期，以及 `contentStartOffset` / `contentEndOffset` 内容边界行为。规格覆盖 ArkTS 动态/静态、generated Modifier 与 Public NativeNode C API 的现有差异。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 嵌套模式长期规格 | 补录 SELF_ONLY、SELF_FIRST、PARENT_FIRST、PARALLEL 的双向配置和分配顺序 |
| ADDED | 嵌套惯性与越界规格 | 补录剩余位移、速度传播、边缘效果和递归生命周期 |
| ADDED | 内容边界长期规格 | 补录数值/Resource/reset、主轴边界、方向和定位接口联动 |
| ADDED | 通道与版本兼容 | 补录 List 特有版本、静态 undefined、Public C 校验和组件降级差异 |

## 输入文档

- SDK 动态接口：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/common.d.ts:18555-18594,29083-29149`、`list.d.ts:1217-1291,1557-1566`、`grid.d.ts:1013-1028`、`scroll.d.ts:1375-1392`
- SDK 静态接口：`/home/leslie/repo/interface_sdk-js/api/arkui/component/common.static.d.ets:10702-10720,15399-15449`、`list.static.d.ets:858-884`
- 嵌套核心：`frameworks/core/components_ng/pattern/scrollable/nestable_scroll_container.cpp:22-96`、`scrollable_pattern.cpp:2723-3223,4793-4820`
- 内容边界：`frameworks/core/components_ng/pattern/scrollable/scrollable_layout_property.h:39-57`、`scrollable_model_ng.cpp:744-849`
- 布局算法：`frameworks/core/components_ng/pattern/scroll/scroll_layout_algorithm.cpp:121-124,259-290,392-425`、List/Grid/WaterFlow 对应 `CalcContentOffset`
- Public C API：`interfaces/native/native_node.h:7616-7640`、`interfaces/native/node/style_modifier.cpp:7652-7707,7969-8004`
- 共享设计：`05-ui-components/03-scroll-container-components/01-scroll-common-capability/design.md`

## 用户故事

### US-1: 配置嵌套滚动模式

作为 ArkUI 应用开发者，我希望分别配置向前和向后的父子响应顺序，以便组合多个同轴滚动容器。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN `scrollForward` 和 `scrollBackward` 分别设置 SELF_ONLY、SELF_FIRST、PARENT_FIRST 或 PARALLEL THEN 每个方向按其独立模式分配位移 | 正常 |
| AC-1.2 | WHEN options 缺字段、非法枚举、非对象或执行 reset THEN 对应入口恢复双 SELF_ONLY；Public C 非法枚举返回 401 | 异常 |
| AC-1.3 | WHEN 父节点不是同主轴 NestableScrollContainer THEN 不建立嵌套父链并按 SELF_ONLY 路径处理 | 边界 |
| AC-1.4 | WHEN Scroll 开启 scrollSnap 或 enablePaging 且当前方向配置 PARENT_FIRST THEN手势位移不走 PARENT_FIRST 分支，按自身路径处理 | 边界 |
| AC-1.5 | WHEN Grid 内容不足一屏且 edgeEffect.alwaysEnabled=false THEN自身手势和 nestedScroll 不触发，存在父手势时由父容器响应 | 边界 |
| AC-1.6 | WHEN父链候选为 Refresh THEN target API 12、当前模式是否需要父节点和 isSearchRefresh 状态共同决定是否接入该父节点 | 边界 |
| AC-1.7 | WHEN组件启用 reverse THEN物理拖动增量和结束速度先取反，再以负值选择 forward、正值选择 backward 模式 | 边界 |

### US-2: 分配父子位移与越界

作为嵌套容器开发者，我希望位移和越界量按模式稳定分配，以便父子滚动不会丢失剩余量或重复消费。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN SELF_ONLY 在正常内容区接收位移 THEN仅自身执行 scrollFrameBegin 和边界计算，未消费量作为 remain 返回调用方 | 正常 |
| AC-2.2 | WHEN SELF_FIRST 接收位移 THEN自身先消费可滚动量，再将越界量和 frameBegin 剩余量交给父容器 | 正常 |
| AC-2.3 | WHEN PARENT_FIRST 接收位移 THEN父容器先消费，父剩余量再由自身处理；父完全消费时自身不移动 | 正常 |
| AC-2.4 | WHEN PARALLEL 接收位移 THEN父子基于同一初始位移并行响应，越界剩余量仍按父是否到边界和子边缘效果裁决 | 正常 |
| AC-2.5 | WHEN自身已处于越界回弹区且收到反向恢复位移 THEN先恢复自身越界量，再把未消费量递归交给父容器 | 边界 |
| AC-2.6 | WHEN边缘效果为 NONE/FADE/SPRING 或仅指定 START/END THEN越界消费、回弹和 remain 结果按当前 effectEdge 分支执行 | 边界 |
| AC-2.7 | WHEN已处于越界区且存在父容器 THEN边界恢复预处理先于四模式分派，剩余量可通过 CHILD_CHECK_OVER_SCROLL 交父，即使当前模式为 SELF_ONLY | 边界 |

### US-3: 传播惯性与递归生命周期

作为使用嵌套滚动的开发者，我希望拖动开始、惯性和停止状态沿父链一致传播，以便事件和动画生命周期可预测。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN子容器开始嵌套滚动且当前模式需要父容器 THEN start 生命周期递归传播到同轴父链并停止父节点仍在运行的滚动动画 | 正常 |
| AC-3.2 | WHEN子容器产生非手势 CHILD_SCROLL 位移 THEN按 vsync 时间差计算 nested velocity；WHEN时间差异常 THEN使用默认帧间隔 | 正常 |
| AC-3.3 | WHEN nested velocity 超过有效时间窗口未更新 THEN读取时清零，不把过期速度作为惯性初速度 | 边界 |
| AC-3.4 | WHEN自身可继续 fling THEN自身启动惯性；WHEN到边界且模式需要父容器 THEN按模式、父边界和边缘效果把速度交给父链 | 正常 |
| AC-3.5 | WHEN祖先已经处于越界且启动回弹 THEN祖先回到边界后可将剩余速度交还原子容器继续 fling | 边界 |
| AC-3.6 | WHEN滚动结束、模式切换中断父链或回弹完成 THEN end 生命周期按 NeedParent 或 nestedInterrupt 状态递归传播且每层清理嵌套状态 | 恢复 |

### US-4: 配置内容起止边界

作为滚动容器开发者，我希望在内容首尾保留逻辑滚动空间，以便内容、滚动条和定位接口共享一致边界。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-4.1 | WHEN设置非负 contentStartOffset/contentEndOffset THEN以 vp 接收、转换为 px 并参与测量、滚动范围和滚动条边距 | 正常 |
| AC-4.2 | WHEN数值为负、Resource 非数值或解析失败 THEN布局生效值为 0；Resource 配置更新失败时回调也写回 0 | 异常 |
| AC-4.3 | WHEN start+end 大于或等于主轴可视长度 THEN两端布局生效值同时归零 | 边界 |
| AC-4.4 | WHEN Scroll 使用 Axis::FREE 或 List 使用 ScrollSnapAlign.CENTER THEN两端偏移不生效并归零 | 边界 |
| AC-4.5 | WHEN水平 RTL 或 reverse 布局 THEN start/end 保持逻辑滚动边界语义，最终物理位置由布局算法镜像 | 正常 |
| AC-4.6 | WHEN scrollToIndex 使用 START/END/AUTO THEN定位结果分别对齐内容起点、终点或最近可见边界，并计入内容偏移 | 正常 |
| AC-4.7 | WHEN静态接口传 undefined、Bridge 解析失败或 Native reset THEN恢复默认 0；动态公共 API 不声明 undefined | 恢复 |
| AC-4.8 | WHEN Public C 传负 f32 THEN setter 返回 0 且 Getter 可暂时读到原值，但布局生效值截断为 0 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-1.7 | R-1-R-6, R-29-R-30 | TASK-05-03-01-F3 | SDK 审查、嵌套 Host 测试、C API 测试 | `scrollable_pattern.cpp:2975-3014`；`style_modifier.cpp:7652-7707` |
| AC-2.1-AC-2.7 | R-7-R-13, R-31 | TASK-05-03-01-F3 | 四模式父子位移与 edge effect 参数化测试 | `scrollable_pattern.cpp:2723-2940` |
| AC-3.1-AC-3.6 | R-14-R-19 | TASK-05-03-01-F3 | 惯性、vsync、递归开始/结束 Host 测试 | `scrollable_pattern.cpp:3017-3223,4793-4820` |
| AC-4.1-AC-4.8 | R-20-R-28 | TASK-05-03-01-F3 | 四组件布局、Resource、RTL/reverse、C API 测试 | `scrollable_model_ng.cpp:744-849`；四组件 `CalcContentOffset` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 两个方向均传入 0..3 枚举 | 分别保存 forward/backward 模式 | 两字段均必填 | AC-1.1 |
| R-2 | 恢复 | reset/undefined/非法 JS 参数 | 恢复 SELF_ONLY/SELF_ONLY | 动态 SDK 不声明 undefined | AC-1.2 |
| R-3 | 异常 | Public C 任一枚举不在 0..3 | 返回 401 且不设置 | 必须提供两个参数 | AC-1.2 |
| R-4 | 边界 | 搜索祖先时轴向不同 | 跳过该祖先继续搜索 | 最终无同轴父节点则无嵌套 | AC-1.3 |
| R-5 | 边界 | Scroll snap/paging + PARENT_FIRST | 不进入父优先位移分支 | SDK 静态声明未复述 | AC-1.4 |
| R-6 | 边界 | Grid 短内容且 alwaysEnabled=false | 子手势不启动，父手势可接管 | Grid 专属公开说明 | AC-1.5 |
| R-7 | 行为 | SELF_ONLY | 自身消费并返回剩余量 | 不主动请求父容器 | AC-2.1 |
| R-8 | 行为 | SELF_FIRST | 自身先消费，再给父剩余/越界量 | CHILD_OVER_SCROLL 时父仍优先处理越界 | AC-2.2 |
| R-9 | 行为 | PARENT_FIRST | 父先消费，剩余再给自身 | snap 时不适用 | AC-2.3 |
| R-10 | 行为 | PARALLEL | 父子基于同一初始 offset 响应 | remain 取决于双方边界 | AC-2.4 |
| R-11 | 恢复 | 自身已越界且收到回边位移 | 先恢复自身，再递归未消费量 | CHILD_CHECK_OVER_SCROLL 保留 remain | AC-2.5 |
| R-12 | 边界 | effectEdge=START/END/ALL | 仅允许对应侧或两侧越界效果 | Public 枚举仅公开 START/END | AC-2.6 |
| R-13 | 边界 | effect=NONE/FADE/SPRING | 无效果、淡出或弹性路径分别消费速度/位移 | 结合 alwaysEnabled 与边界状态 | AC-2.6 |
| R-14 | 行为 | nested start 且 NeedParent=true | start 递归到父链 | 仅同轴父链 | AC-3.1 |
| R-15 | 行为 | CHILD_SCROLL/CHILD_OVER_SCROLL 位移 | 计算 nested velocity | GESTURE 不更新该速度 | AC-3.2 |
| R-16 | 边界 | vsync 差值不在有效区间 | 使用默认帧间隔计算 | 防止异常速度 | AC-3.2 |
| R-17 | 恢复 | 速度时间戳超过 MAX_VSYNC_DIFF_TIME | nested velocity 清零 | 过期速度不传播 | AC-3.3 |
| R-18 | 行为 | fling 到边界且 NeedParent=true | 按模式与 edge effect 把速度交给父/祖先 | 祖先越界回弹可优先 | AC-3.4, AC-3.5 |
| R-19 | 恢复 | end/interrupt/spring 完成 | 递归 OnScrollEnd 并清除 nested 状态 | scrollTo over 动画抑制父传播 | AC-3.6 |
| R-20 | 行为 | offset>=0 | vp 转 px 后参与测量与滚动范围 | Property dirty flag 为 MEASURE | AC-4.1 |
| R-21 | 异常 | offset<0 | Property 可存原值，布局值 max(px,0) | Getter 与布局可观测值暂时不同 | AC-4.2, AC-4.8 |
| R-22 | 恢复 | Resource 解析/配置更新失败 | 写回 0 | 回调不保留旧值 | AC-4.2 |
| R-23 | 边界 | start+end>=主轴可视长度 | 两端同时归零 | 等于长度也触发 | AC-4.3 |
| R-24 | 边界 | Axis::FREE 或 List CENTER snap | 两端归零 | 不参与对应布局 | AC-4.4 |
| R-25 | 行为 | 水平 RTL/reverse | 逻辑 start/end 经布局镜像到物理边 | 不固定等于 top/left | AC-4.5 |
| R-26 | 行为 | scrollToIndex START/END/AUTO | 计入 offset 对齐指定或最近边界 | 组件公开版本不同 | AC-4.6 |
| R-27 | 恢复 | 静态 undefined/Bridge reset/Native reset | 恢复 0 | NG reset 写 0；静态 Model 可清 optional | AC-4.7 |
| R-28 | 边界 | Public C 负 f32 | setter 返回成功、布局截断为 0 | C API 不支持 Resource | AC-4.8 |
| R-29 | 边界 | 父候选为 Refresh | 按 target API 12 与 isSearchRefresh 决定跳过或接入 | NeedParent 配置会更新搜索策略 | AC-1.6 |
| R-30 | 边界 | reverse=true | 增量/速度先取反，再按符号选择 forward/backward | forward/backward 不是固定物理方向 | AC-1.7 |
| R-31 | 边界 | 已越界且存在父节点 | 先恢复自身，并把剩余量以 CHILD_CHECK_OVER_SCROLL 交父 | 发生在 NeedParent/四模式判断之前 | AC-2.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.7 | Scroll/List/Grid/WaterFlow nested Host 与 Public C 参数化测试 | 四模式、双方向、非法枚举、snap/paging、短内容、Refresh、reverse |
| VM-2 | AC-2.1-AC-2.7 | 父子 offset/remain/edge effect 测试 | 消费顺序、并行、越界恢复、SELF_ONLY 预处理、effectEdge |
| VM-3 | AC-3.1-AC-3.6 | fling、recursive lifecycle、vsync 速度测试 | 速度超时、祖先 spring、interrupt、end 次数 |
| VM-4 | AC-4.1-AC-4.5 | 四组件布局算法测试 | 非负截断、总和阈值、FREE/CENTER、RTL/reverse |
| VM-5 | AC-4.6-AC-4.8 | scrollToIndex、Resource 更新、NativeNode C 测试 | 对齐、undefined/reset、负值 getter/布局差异 |

## API 变更分析

### 新增 API

本次不新增接口，以下为补录的现有公开能力。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `nestedScroll` | Public | NestedScrollOptions/静态 undefined | 组件属性链 | N/A | 配置前后向嵌套模式 | AC-1.1-AC-3.6 |
| `contentStartOffset` | Public | number/Resource/静态 undefined | 组件属性链 | N/A | 配置逻辑内容首端边界 | AC-4.1-AC-4.8 |
| `contentEndOffset` | Public | number/Resource/静态 undefined | 组件属性链 | N/A | 配置逻辑内容尾端边界 | AC-4.1-AC-4.8 |
| `NODE_SCROLL_NESTED_SCROLL` | Public C API | 两个 ArkUI_ScrollNestedMode | 0/401 | 0、401、106102 | 设置、获取、重置嵌套模式 | AC-1.1-AC-1.3 |
| `NODE_SCROLL_CONTENT_*_OFFSET` | Public C API | f32，vp | 0/401 | 0、401、106102 | 设置、获取、重置内容边界 | AC-4.1-AC-4.8 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `nestedScroll` | 历史公共化 | 四组件动态 API10，公共动态 API11，静态 API23 | 按组件实际开放版本使用 | AC-1.1 |
| List `contentStart/EndOffset(number)` | 历史新增 | API11 | 低版本不使用 | AC-4.1 |
| List `contentStart/EndOffset(number|Resource)` | 历史扩展 | 动态 API22、静态 API23 | Resource 失败按 0 | AC-4.2 |
| 公共 `contentStart/EndOffset` | 历史新增 | 动态 API22、静态 API26 | 非 List 组件按公共版本使用 | AC-4.1, AC-4.7 |
| Native content offset | 历史新增 | API15，f32/vp | 不支持 Resource | AC-4.8 |

## 接口规格

### 接口定义

**nestedScroll**

| 属性 | 值 |
|---|---|
| 函数签名 | `nestedScroll(value: NestedScrollOptions): T`；静态 `nestedScroll(value: NestedScrollOptions | undefined): this` |
| 返回值 | 当前组件属性对象 |
| 开放范围 | Public |
| 错误码 | ArkTS N/A；Public C API 为 0/401/106102 |
| 关联 AC | AC-1.1-AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| scrollForward | NestedScrollMode | 是 | SELF_ONLY | 0..3 |
| scrollBackward | NestedScrollMode | 是 | SELF_ONLY | 0..3 |
| value | NestedScrollOptions/undefined | 动态是、静态否 | 双 SELF_ONLY | 静态 undefined 恢复 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 四模式与两个方向组合 | 按 Gherkin 场景执行父子分配 | AC-1.1-AC-2.6 |
| 2 | fling、回弹和中断 | 按 Gherkin 场景传播生命周期 | AC-3.1-AC-3.6 |

**contentStartOffset / contentEndOffset**

| 属性 | 值 |
|---|---|
| 函数签名 | `contentStartOffset(offset: number | Resource): T`；`contentEndOffset(offset: number | Resource): T`；静态允许 undefined |
| 返回值 | 当前组件属性对象 |
| 开放范围 | Public |
| 错误码 | ArkTS N/A；Public C API 为 0/401/106102 |
| 关联 AC | AC-4.1-AC-4.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| offset | number/double | 是 | 0vp | 布局生效值不小于 0 |
| offset | Resource | 是 | 0vp | 解析为数值；失败写 0 |
| offset | undefined | 仅静态 | 0vp | 恢复默认 |
| Native value | f32 | 是 | 0vp | 不校验负数，不支持 Resource |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 两端非负且总和小于主轴 | 参与布局、范围、滚动条与定位 | AC-4.1, AC-4.6 |
| 2 | 负值/资源失败/总和达到主轴 | 按 Gherkin 场景归零 | AC-4.2-AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次补录当前实现和历史差异。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** nestedScroll 动态组件级 API10；List number 内容偏移 API11；Native 内容偏移 API15；公共动态/Resource API22；静态 List API23；静态公共内容偏移 API26。
- **API 版本号策略:** 同时记录组件级、公共方法级和静态范式的实际 `@since`。
- **通道差异:** 动态接口通常不接受 undefined；静态接口支持 reset；Public C 内容偏移只支持 f32 且不拒绝负值。
- **组件差异:** Scroll snap/paging、Grid 短内容、List CENTER snap、Scroll Axis::FREE 均有专属降级规则。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 同轴父链 | 只连接 Axis 相同的 NestableScrollContainer；Refresh 接入受 API 和搜索状态控制 | AC-1.3, AC-1.6 |
| 模式分配 | 每个模式必须明确父子收到的 offset/remain/overOffset；PARALLEL 的父子各收到完整初始位移 | AC-2.1-AC-2.7 |
| 生命周期递归 | start/end/velocity 必须使用同一父链和中断状态 | AC-3.1-AC-3.6 |
| 测量属性 | 内容偏移存于 LayoutProperty 并触发 MEASURE | AC-4.1-AC-4.4 |
| 逻辑方向 | start/end 为逻辑滚动边界，由 RTL/reverse 映射到物理边 | AC-4.5 |
| 契约分层 | SDK 契约和 Source/C API 偏差必须分通道记录 | AC-1.2, AC-4.7-AC-4.8 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 每帧嵌套分配沿祖先链线性传播，不新增全树遍历 | Host 深层嵌套测试 | `nestable_scroll_container.cpp:22-47` |
| 功耗 | 无位移、无有效速度时不启动额外惯性 | 动画状态断言 | `scrollable_pattern.cpp:2975-3042` |
| 内存 | 仅维护弱父引用、模式和少量速度状态 | 源码审查 | `nestable_scroll_container.h:181-192` |
| 安全 | 不涉及敏感数据和权限 | 接口审查 | UI 数值与枚举 |
| 可靠性 | 位移守恒、过期速度归零、非法 offset 可恢复 | 参数化边界测试 | `scrollable_pattern.cpp:4793-4820` |
| 可测试性 | 四模式、四组件、双方向、三通道均映射 VM | VM-1 至 VM-5 | 本文 |
| 自动化维测 | Dump 输出 forward/backward 模式和父链状态 | Dump 审查 | `scrollable_pattern.cpp:337-339,4456-4461` |
| 定界定位 | 日志包含 offset、source、state、velocity、node id/tag | Trace 审查 | `scrollable_pattern.cpp:2999-3005,3028-3032` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 触摸拖动和惯性进入标准嵌套链 | 同轴父链与边缘效果共同决定 | Host/集成测试 | 嵌套核心实现 |
| 平板/PC | 触控板轴事件开始时父容器可能未收到 TouchDown，start 时主动停止父动画 | 保证新一轮嵌套无旧动画竞争 | 触控板测试 | `scrollable_pattern.cpp:3190-3200` |
| 折叠屏 | 尺寸变化可能使 start+end 达到新主轴长度并同时归零 | 每轮 measure 使用当前主轴尺寸 | 尺寸变化测试 | 四组件 CalcContentOffset |
| 穿戴设备 | 轴向和表冠输入不改变嵌套模式语义 | 仍按同轴父链处理 | 输入联动测试 | 公共 ScrollablePattern |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 无障碍滚动仍需沿当前容器边界和父链产生一致 reachEdge | AC-2.1-AC-3.6 |
| 大字体 | 间接 | 内容尺寸变化可改变短内容和两端和阈值 | AC-1.5, AC-4.3 |
| 深色模式 | 否 | 不涉及颜色 |
| 多窗口/分屏 | 是 | 主轴尺寸变化会重新计算内容边界 | AC-4.3 |
| 多用户 | 否 | 无用户状态 |
| 版本升级 | 是 | API10-26 存在组件与范式版本矩阵 | AC-1.1, AC-4.1-AC-4.7 |
| 生态兼容 | 是 | 动静态、generated 与 Public C 参数/reset 语义不同 | AC-1.2, AC-4.7-AC-4.8 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 嵌套滚动与内容边界
  作为 ArkUI 滚动容器开发者
  我想要稳定的父子分配和逻辑内容边界
  以便组合滚动时位移、惯性和定位结果可预测

  Scenario Outline: 四种嵌套模式分配位移
    Given 子容器与父容器主轴相同且均可滚动
    When 子容器沿 <direction> 方向以 <mode> 模式接收位移
    Then 位移按 <order> 顺序消费
    And 验证父子各自接收的 offset 与返回 remain

    Examples:
      | mode | direction | order |
      | SELF_ONLY | forward | 仅子容器 |
      | SELF_FIRST | backward | 子容器后父容器 |
      | PARENT_FIRST | forward | 父容器后子容器 |
      | PARALLEL | backward | 父子并行 |

  Scenario: 内容边界总和达到视口
    Given 主轴可视长度为 100vp
    When contentStartOffset=40vp 且 contentEndOffset=60vp
    Then 两端布局生效值均为 0
    And 滚动范围不增加 100vp

  Scenario: Public C 设置负内容偏移
    Given 一个支持 ScrollableLayoutProperty 的 NativeNode
    When NODE_SCROLL_CONTENT_START_OFFSET 设置为 -1vp
    Then setter 返回成功
    And 属性 Getter 可返回 -1
    And 布局生效值为 0
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollablePattern nested scroll parent self parallel velocity recursive lifecycle"
  - repo: "openharmony/arkui_ace_engine"
    query: "contentStartOffset contentEndOffset layout Resource RTL reverse"
  - repo: "openharmony/interface_sdk-js"
    query: "NestedScrollOptions contentStartOffset contentEndOffset API version"
```

**关键文档：** ArkUI Scroll、List、Grid、WaterFlow SDK 类型定义；`scrollable_pattern`、`nestable_scroll_container` 与四组件布局算法。
