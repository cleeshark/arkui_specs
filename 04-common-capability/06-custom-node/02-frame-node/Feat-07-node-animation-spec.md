# 特性规格

> Func-04-06-02-Feat-07 FrameNode 节点动画：固化 createAnimation、cancelAnimations、getNodePropertyValue 共 3 个公开 API 与 AnimationPropertyType 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | FrameNode 节点动画 |
| 特性编号 | Func-04-06-02-Feat-07 |
| 所属 Epic | 自定义节点能力 / FrameNode |
| 优先级 | P1 |
| 目标版本 | API 20（dynamic 起始）；静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准（L1+） |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | createAnimation/cancelAnimations/getNodePropertyValue | API 20；静态 @since 23 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/06-custom-node/02-frame-node/design.md` | Baselined |
| SDK 动态/静态 | `interface/sdk-js/api/arkui/FrameNode.d.ts` / `FrameNode.static.d.ets` | — |

## 用户故事

### US-1: 创建属性动画
**作为** 应用开发者，**我想要** 为节点的旋转/平移/缩放/透明度创建动画。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-1.1 | WHEN `createAnimation(property, startValue, endValue, param)` 参数有效 THEN SetAnimationPropertyValue(baseline 无动画)+OpenImplicitAnimation+设 endValue+CloseImplicitAnimation，返回是否生成动画 | 正常 |
| AC-1.2 | WHEN property=ROTATION(0) THEN 3 值[rotX,rotY,rotZ]，RS 侧 SetRotationX/Y 取负（角度方向差异）、SetRotation(value[2]) | 正常 |
| AC-1.3 | WHEN property=OPACITY(3) THEN AdjustPropertyValue 将 start/end 各值 clamp 至 [0,1]；RSAlphaModifier SetAlpha+MarkNeedDrawNode(<1.0) | 正常 |
| AC-1.4 | WHEN endValue 与当前值相同 THEN 未生成动画，返回 false，onFinish 不触发 | 边界 |
| AC-1.5 | WHEN startValue 提供 THEN 先无动画设为基线（ExecuteWithoutAnimation） | 正常 |

### US-2: 取消属性动画
**作为** 应用开发者，**我想要** 取消正在进行的属性动画。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-2.1 | WHEN `cancelAnimations(properties)` 且 properties 非空有效 THEN 开 duration=0 LINEAR 隐式动画，逐属性 CancelPropertyAnimation，SyncRSProperty，返回 true | 正常 |
| AC-2.2 | WHEN properties 为空数组 THEN 返回 true（无需取消） | 边界 |
| AC-2.3 | WHEN 任一元素非法（非数字/超范围）THEN 返回 false（整调用中止） | 异常 |
| AC-2.4 | WHEN 取消 ROTATION THEN 同时取消 X/Y/Z；TRANSLATION 取消 TRANSLATE；SCALE 取消 SCALE；OPACITY 取消 ALPHA | 正常 |

### US-3: 读取属性当前值
**作为** 应用开发者，**我想要** 读取动画属性的当前（staging）值。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-3.1 | WHEN `getNodePropertyValue(ROTATION)` THEN 返回 [-angleX,-angleY,angleZ]（3 值，默认 0.0，X/Y 取负） | 正常 |
| AC-3.2 | WHEN `getNodePropertyValue(TRANSLATION)`/`(SCALE)` THEN 返回 [x,y]（SCALE 默认 1.0,1.0） | 正常 |
| AC-3.3 | WHEN `getNodePropertyValue(OPACITY)` THEN 返回 [opacity]（默认 1.0） | 正常 |
| AC-3.4 | WHEN 节点 null/无 rsNode/property 非法 THEN 返回空数组 [] | 边界 |
| AC-3.5 | WHEN 动画进行中 THEN 返回 staging 值（可能与已提交值不同） | 边界 |

### US-4: 不可改节点动画限制
**作为** 应用开发者，**我想要** 了解不可改节点的动画限制。

| AC 编号 | 验收标准 | 类型 |
|---------|----------|------|
| AC-4.1 | WHEN ImmutableFrameNode.createAnimation THEN warn "can't create animation on unmodifiable frameNode" 并返回 false（不抛 100021） | 边界 |
| AC-4.2 | WHEN ImmutableFrameNode.cancelAnimations THEN warn 并返回 false | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|----------|----------|------|
| AC-1.1..1.5 | R-1,R-2,R-3,R-4,R-5 | 单测 | view_abstract.cpp:12169; bridge:2871; rosen_render_context.cpp:8819 |
| AC-2.1..2.4 | R-6,R-7,R-8,R-9 | 单测 | view_abstract.cpp:12210; rosen_render_context.cpp:8870 |
| AC-3.1..3.5 | R-10,R-11,R-12,R-13 | 单测 | view_abstract.cpp:12244; rosen_render_context.cpp:8908 |
| AC-4.1..4.2 | R-14 | 单测 | frame_node.ts:1164,1168 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | createAnimation 有效参数 | 按 param 创建属性动画；返回是否生成动画 | 返 boolean | AC-1.1 |
| R-2 | 行为 | property=ROTATION(0) | 3 值[rotX,rotY,rotZ]（X/Y 方向与底层渲染相反） | size 须==3 | AC-1.2 |
| R-3 | 行为 | property=OPACITY(3) | clamp start/end 至 [0,1] | size 须==1 | AC-1.3 |
| R-4 | 边界 | endValue==当前值 | 未生成动画，返回 false，onFinish 不触发 | — | AC-1.4 |
| R-5 | 行为 | 提供 startValue | 先无动画设置 start 为基线 | — | AC-1.5 |
| R-6 | 行为 | cancelAnimations 非空有效 | 立即取消指定属性动画；返回 true | — | AC-2.1,2.4 |
| R-7 | 边界 | properties 空数组 | 返回 true（无需取消） | — | AC-2.2 |
| R-8 | 异常 | 任一元素非法 | 整调用中止返回 false | 非数字/超范围 | AC-2.3 |
| R-9 | 行为 | 各属性取消映射 | ROTATION→X/Y/Z；TRANSLATION→TRANSLATE；SCALE→SCALE；OPACITY→ALPHA | — | AC-2.4 |
| R-10 | 行为 | getNodePropertyValue(ROTATION) | 返回 [-angleX,-angleY,angleZ]（X/Y 取负，默认 0） | 返回 staging 值 | AC-3.1 |
| R-11 | 行为 | getNodePropertyValue(TRANSLATION/SCALE) | 返回 [x,y]（SCALE 默认 1.0,1.0） | size 须==2 | AC-3.2 |
| R-12 | 行为 | getNodePropertyValue(OPACITY) | 返回 [opacity]（默认 1.0） | size 须==1 | AC-3.3 |
| R-13 | 边界 | null/无渲染节点/非法 | 返回空数组 [] | — | AC-3.4,3.5 |
| R-14 | 边界 | ImmutableFrameNode create/cancel | warn 并返回 false（不抛 100021） | 100021 仅树操作 | AC-4.1,4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1..R-5 createAnimation | 单测 | 四属性映射、OPACITY clamp、end==当前返 false |
| VM-2 | R-6..R-9 cancelAnimations | 单测 | 空 true、非法 false、取消映射 |
| VM-3 | R-10..R-13 getNodePropertyValue | 单测 | ROTATION 取负、默认值、staging |
| VM-4 | R-14 Immutable 限制 | 单测 | warn+false 非 100021 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| createAnimation(property, startValue, endValue, param) | Public | property: AnimationPropertyType; startValue?: number[]; endValue: number[]; param: AnimateParam | boolean | — | 创建属性动画 | AC-1 |
| cancelAnimations(properties) | Public | properties: AnimationPropertyType[] | boolean | — | 取消动画 | AC-2 |
| getNodePropertyValue(property) | Public | property: AnimationPropertyType | number[] | — | 读属性当前值 | AC-3 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**createAnimation**

| 属性 | 值 |
|------|-----|
| 函数签名 | `createAnimation(property: AnimationPropertyType, startValue: number[]\|undefined, endValue: number[], param: AnimateParam): boolean` (@since 20 dyn/23 static) |
| 返回值 | boolean（是否生成动画） |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| property | AnimationPropertyType | 是 | — | ROTATION=0/TRANSLATION=1/SCALE=2/OPACITY=3；超范围返 false |
| startValue | number[]\|undefined | 否 | undefined | 须匹配属性 size（OPACITY clamp [0,1]）；undefined 允许 |
| endValue | number[] | 是 | — | 须匹配属性 size；OPACITY clamp |
| param | AnimateParam | 是 | — | duration/easing/iterations/playMode/onFinish |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 有效参数+end≠当前 | 生成动画返 true | AC-1.1 |
| 2 | ROTATION | 3 值，X/Y 取负 | AC-1.2 |
| 3 | OPACITY | clamp [0,1] | AC-1.3 |
| 4 | end==当前 | 返 false，onFinish 不触发 | AC-1.4 |
| 5 | 提供 start | 先无动画设基线 | AC-1.5 |

**cancelAnimations**

| 属性 | 值 |
|------|-----|
| 函数签名 | `cancelAnimations(properties: AnimationPropertyType[]): boolean` (@since 20 dyn/23 static) |
| 返回值 | boolean |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| properties | AnimationPropertyType[] | 是 | — | 空→true；任一非法→false |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 非空有效 | duration=0 逐属性 Cancel+Sync，返 true | AC-2.1,2.4 |
| 2 | 空数组 | 返 true | AC-2.2 |
| 3 | 任一非法 | 整调用中止返 false | AC-2.3 |

**getNodePropertyValue**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getNodePropertyValue(property: AnimationPropertyType): number[]` (@since 20 dyn/23 static) |
| 返回值 | number[] |
| 开放范围 | Public |
| 错误码 | — |
| 关联 AC | AC-3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | ROTATION | [-angleX,-angleY,angleZ]（默认 0） | AC-3.1 |
| 2 | TRANSLATION/SCALE | [x,y]（SCALE 默认 1） | AC-3.2 |
| 3 | OPACITY | [opacity]（默认 1） | AC-3.3 |
| 4 | null/非法 | 返 [] | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 20（dynamic）；静态 @since 23。
- **API 版本号策略:** 全部 @since 20 dyn / 23 static。

**风险项:**

| 风险 | 说明 | 来源 |
|------|------|------|
| ROTATION X/Y 取负 | arkui 与 RS 角度方向相反，getNodePropertyValue 返 [-angleX,-angleY,angleZ] | rosen_render_context.cpp:8819,8908 |
| ImmutableFrameNode 动画返 false 非 100021 | 与树操作不同，仅 warn+false | frame_node.ts:1164,1168 |
| getNodePropertyValue 返 staging 值 | 动画进行中可能与已提交值不同 | rosen_render_context.cpp:8908 GetAnimatablePropertyStagingValue |
| size 不匹配静默跳过 | RS 侧 if(value.size()==_PARAM_SIZE) 守卫，size 错误静默不应用 | rosen_render_context.cpp:8819 |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| AnimationPropertyType 映射 | ROTATION(3)/TRANSLATION(2)/SCALE(2)/OPACITY(1) 各有固定 size | AC-1.2,3 |
| OPACITY clamp | start/end 值 clamp 至 [0,1] | AC-1.3 |
| 取消映射 | 各属性对应 RS modifier 取消 | AC-2.4 |
| Immutable 限制 | 不可改节点动画返 false（非 100021） | AC-4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | createAnimation 触发隐式动画+RequestFrame | 单测 | view_abstract.cpp:12169 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | 全部 API 20/23 演进 | AC-1,2,3 |

## 行为场景

```gherkin
Feature: FrameNode 节点动画
  Scenario: createAnimation end==当前值
    Given 节点 opacity 当前为 1.0
    When 调用 createAnimation(OPACITY, undefined, [1.0], param)
    Then 返回 false，onFinish 不触发

  Scenario Outline: getNodePropertyValue 各属性
    When 调用 node.getNodePropertyValue(<property>)
    Then 返回 <期望>

    Examples:
      | property | 期望 |
      | ROTATION | [-angleX,-angleY,angleZ] |
      | SCALE | [x,y]（默认 1.0,1.0） |
      | OPACITY | [opacity]（默认 1.0） |
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC WHEN/THEN 可独立测试
- [x] 范围边界明确（节点动画；不含生命周期 Feat-08）
- [x] 无语义模糊
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ViewAbstract::CreatePropertyAnimation 隐式动画+SetAnimationPropertyValue+CloseImplicitAnimation"
  - repo: "openharmony/arkui_ace_engine"
    query: "RosenRenderContext SetAnimationPropertyValue/CancelPropertyAnimation/GetRenderNodePropertyValue AnimationPropertyType→RS modifier 映射"
  - repo: "openharmony/arkui_ace_engine"
    query: "AnimationPropertyType ROTATION/TRANSLATION/SCALE/OPACITY 与 PARAM_SIZE 常量"
```
