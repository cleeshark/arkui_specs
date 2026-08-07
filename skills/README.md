# ArkUI Spec Evaluation Skills

本目录保存与 `specs/` 质量评价体系配套、可随仓库版本化的 Skill 源文件。

当前 Skill：

- `ohos-design-arkui-spec-evaluator/`：以完整 Function 为最小单元，基于静态扫描、证据包和冻结 Rubric v0.3 生成语义评价结果。

目录约束：

- Skill 只读取正式 Spec、Design、Registry、源码、SDK、测试和静态评价产物。
- Skill 不自动修改正式 Spec、Design、Registry 或 `evaluation/reviews/` 中的人工确认基线。
- 确定性检查继续由 `tools/spec_eval/` 实现，Skill 不重复实现同类规则。
- Skill 输出必须先通过仓内协议校验，才能进入后续评分聚合或人工确认流程。

当前目录是仓内 Skill 源码，不会自动安装到用户级 Skill 目录。需要试运行时，应向 Agent 明确提供 `SKILL.md` 路径，或在确认版本稳定后再安装到用户级 Skill 根目录。
