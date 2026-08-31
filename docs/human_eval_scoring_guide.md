# 人工评估指南

本指南用于人工评估四种图到逻辑编译方法生成的布尔逻辑表达式质量。当前人工评估采用配对设计：沿用同一批 50 条纳排标准编译单元，分别评价 Flat、OR-direct、Constraint 和 CG-GLC 的候选表达式，用于直接检验人工判断下 CG-GLC 是否仍优于对照方法。

## 评估文件

每种方法默认生成两份完全相同的人工评估表，供两名评审者独立填写：

```text
results/human_eval/flat_human_eval_1.csv
results/human_eval/flat_human_eval_2.csv
results/human_eval/or_direct_human_eval_1.csv
results/human_eval/or_direct_human_eval_2.csv
results/human_eval/constraint_human_eval_1.csv
results/human_eval/constraint_human_eval_2.csv
results/human_eval/cgglc_human_eval_1.csv
results/human_eval/cgglc_human_eval_2.csv
```

若需要基于已有 CG-GLC 人工评估样本生成对照方法模板，运行：

```powershell
python src/criteria_boolean/generate_human_eval_sample.py --methods flat or_direct constraint --reference-csv results/human_eval/cgglc_human_eval_1.csv --skip-existing
```

上述命令不会重新抽样，而是复用 `cgglc_human_eval_1.csv` 中的 50 个 `doc_id`、`sample_id` 和 `case_bucket`，为其它方法生成一一配对的候选表达式。评审 1 填写所有 `_1.csv` 文件，评审 2 填写所有 `_2.csv` 文件，两人独立评分，不需要互相讨论。

每条样本包含：

- `sample_id`：人工评估样本编号。
- `doc_id`：原始纳排标准编译单元编号。
- `case_bucket`：样本类型，可能为 `or`、`scope` 或 `other`。
- `source_criterion`：原始纳排标准文本。
- `candidate_expression`：对应方法生成的布尔表达式。
- 五个评分字段：见下方评分维度。
- `reviewer_notes`：评审备注，可记录主要错误或不确定点。

评分时只根据 `source_criterion` 和 `candidate_expression` 判断，不需要查看方法内部过程，也不需要查看 GPT 评分结果。

## 抽样设置

当前项目沿用已完成 CG-GLC 人工评估的 50 条样本，覆盖 OR、scope 和普通标准。样本分布为：OR 结构样本 25 条、scope 相关样本 15 条、其它样本 10 条。生成对照方法模板时，三种对照方法使用完全相同的 50 条 `doc_id` 和样本顺序，保证后续可以进行配对比较。

`case_bucket` 的含义：

- `or`：原始 CHIA 标注中包含 CHIA OR事件线索，重点考察候选表达式是否保留析取逻辑。
- `scope`：原始 CHIA 标注中包含 `Has_scope` 关系，重点考察修饰成分、数值、时间窗或条件范围是否归属正确。
- `other`：未归入上述两类的普通样本，用于检查整体基础质量。

## 评分维度

每个维度均为 0、1、2 分。

### 1. predicate_completeness

评价关键临床谓词是否完整。

- 2：疾病、药物、检查、数值、时间、限定词、否定等关键信息基本完整，并整合为清晰谓词。
- 1：主要谓词存在，但部分数值、时间、限定词、修饰语或谓词归属缺失或碎片化。
- 0：关键谓词大量缺失、严重碎片化、空输出或不可理解。

### 2. logical_correctness

评价 AND、OR、NOT 是否保留原文逻辑。

- 2：合取、析取和否定关系基本正确。
- 1：主体逻辑部分正确，但至少一个重要 AND、OR 或 NOT 关系错误或模糊。
- 0：布尔逻辑显著改变原文含义。

### 3. grouping_correctness

评价并列项、共享修饰语、局部分组和层级结构。

- 2：替代项、共享修饰语、局部条件组和嵌套结构清晰。
- 1：部分分组正确，但替代项归属或共享修饰语作用范围有错误。
- 0：分组缺失或严重误导。

### 4. faithfulness

评价候选表达式是否忠实于原文。

- 2：没有临床重要的新增条件或遗漏。
- 1：总体忠实，但存在需要人工修正的重要细节。
- 0：新增原文不支持的条件、遗漏核心条件或与原文矛盾。

### 5. downstream_usability

评价是否可作为队列查询或患者筛选的中间表示。

- 2：基本可用于后续查询生成或患者筛选，只需少量人工修正。
- 1：部分可用，但需要明显人工修复。
- 0：难以下游使用。

## 填写规则

所有评分字段只填写整数 `0`、`1` 或 `2`。如果难以判断，优先根据临床含义受影响程度评分：

- 不影响核心临床含义的轻微措辞问题，一般不降到 0 分。
- 遗漏关键疾病、药物、检查、数值、时间窗或否定信息时，应明显扣分。
- OR 被错误改成 AND，或 NOT 作用范围错误时，应在 `logical_correctness` 和 `grouping_correctness` 中扣分。
- 候选表达式新增原文没有支持的临床条件时，应在 `faithfulness` 中扣分。

备注字段建议简短记录关键问题，例如：

```text
misses time window
OR alternatives represented as AND
negation scope unclear
unsupported medication condition
```

## 汇总

四种方法均完成评分后，运行：

```text
python src/criteria_boolean/compare_human_methods.py
```

该脚本生成：

```text
results/human_eval/human_eval_per_item_200.csv
results/human_eval/human_eval_summary_by_method.csv
results/human_eval/human_eval_paired_vs_cgglc.csv
results/human_eval/human_eval_reviewer_agreement.csv
results/human_eval/gpt_human_eval_200.csv
results/human_eval/gpt_human_agreement_200.csv
```

其中 `human_eval_per_item_200.csv` 为 50 个纳排标准单元 × 4 种方法的人工评分明细；`human_eval_summary_by_method.csv` 用于报告四种方法的人工评分均值；`human_eval_paired_vs_cgglc.csv` 用于报告 CG-GLC 相对三种对照方法的配对总分差、胜/平/负数量，以及剔除平分样本后的单侧精确符号检验 P 值；`human_eval_reviewer_agreement.csv` 用于报告两名评审者之间的一致性；`gpt_human_eval_200.csv` 从全量 GPT 盲评结果中抽取同一批 200 条候选表达式；`gpt_human_agreement_200.csv` 用于报告 GPT 评分与人工均分的一致性。
