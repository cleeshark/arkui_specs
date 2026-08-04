# Function参考评价Pilot

本目录为NEXT-006的Function级参考评价Pilot，不修改任何正式Spec、Design或Registry。

`manifest.yaml`冻结12个Pilot Function、关联仓revision和输入指纹。每个Function只保留一份评价文件，完成一次评价并确认后即可提交入库，不设置专家团队、双评或仲裁流程。

静态Finding数量和Evidence Coverage只用于抽样分层，不能直接作为高、中、低质量结论。

## 冻结输入

每个Pilot Function记录：

- ace_engine、specs、ArkTS SDK和NDK SDK revision。
- Function目录、Feature数量和标准化复杂度。
- Registry条目、全部Feature Spec和共享Design内容指纹。
- 对应静态归档的Finding数量和Evidence Coverage。

校验命令：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator
```

只要Registry、任一Feature Spec或共享Design发生变化，`input_fingerprint`就会变化，原评价必须重新确认，不能继续作为同一参考输入。

查看单个Function参与指纹计算的文档和哈希：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator \
  --show-input 03-07-01
```

## 生成待评价文件

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator \
  --template 03-07-01 \
  --evaluator-id sunfei2021 \
  > specs/evaluation/reviews/03-07-01.yaml
```

模板会预填18个Rubric Criterion并标记为`NOT_VERIFIABLE`草稿。评价人必须逐项改为真实结论，不能把草稿直接当作质量结果。

确认前必须：

1. 阅读冻结的Function输入，对每个Criterion给出结论、理由和证据。
2. Critical/Major Finding至少提供一个带revision和content hash的证据。
3. 填写五维精确分、原始分、发布分、置信度和准入结论。
4. 将`semantic_complete`改为`true`。
5. 记录评价时间和一次确认，将状态改为`confirmed`。

校验单份评价：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator \
  --evaluation specs/evaluation/reviews/03-07-01.yaml
```

完整填写规则见`../reviews/README.md`。后续如需要增加复评，可在不改变当前单文件结构的前提下扩展版本；当前流程不启用该机制。
