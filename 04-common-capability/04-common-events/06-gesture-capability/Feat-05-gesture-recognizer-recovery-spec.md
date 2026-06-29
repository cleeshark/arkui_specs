# 特性规格

> Draft。当前文档是 Func-04-04-06 / Feat-05 的长期规格草案，占位并承接 Stage 2。

## AC 摘要

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 新一轮首个 down 到达 THEN 恢复非 READY 非豁免残留状态 | 正常 |
| AC-1.2 | WHEN 识别器处于 READY 或已闭环 THEN 不触发额外恢复和业务回调 | 正常 |
| AC-2.1 | WHEN 双击识别器处于 pending THEN 豁免恢复 | 正常 |
| AC-2.2 | WHEN Swipe 识别器处于 pending THEN 豁免恢复 | 正常 |
| AC-3.1 | WHEN 恢复行为发生 THEN 可测可观测 | 正常 |

## 规则摘要

- 首 down 判定：上一轮无活动手指后的首个 `TouchType::DOWN`。
- 重复同 id down 走既有强清逻辑。
- 多指第二根及后续 down 不触发全局恢复。
- 非豁免 pending 视为未闭环并恢复。

## 验证摘要

- UT：`test/unittest/core/event`、`test/unittest/core/gestures`
- HostPreview：`examples/SpecTest/.../Feat-05-gesture-recognizer-recovery`

