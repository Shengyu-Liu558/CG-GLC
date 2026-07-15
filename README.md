# 临床试验纳排标准布尔逻辑表示方法研究

本项目是论文《临床试验纳排标准布尔逻辑表示方法研究》的代码、数据、评估材料和结果整理版。研究目标是将 CHIA 临床试验纳排标准中的图结构标注转换为 Boolean AST 和布尔逻辑表达式，并评估本文方法 CG-GLC 在临床纳排标准逻辑表示任务中的表现。

## 目录结构

```text
.
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   │   ├── chia_with_scope.zip
│   │   └── chia_with_scope/
│   ├── processed/
│   │   ├── source_criteria.jsonl
│   │   ├── source_stats.json
│   │   └── boolean_outputs/
│   └── evaluation/
│       ├── llm_judge/
│       └── gpt_manual_batches/
├── docs/
│   ├── gpt_manual_evaluation_guide.md
│   └── human_eval_scoring_guide.md
├── results/
│   ├── llm_eval/
│   └── human_eval/
├── scripts/
└── src/
    └── criteria_boolean/
```

说明文档保留了三份：本 README、`docs/gpt_manual_evaluation_guide.md`、`docs/human_eval_scoring_guide.md`。`data/evaluation/gpt_manual_batches/` 下的 `.md` 文件是自动生成的 GPT 分批评估 prompt，不属于人工编写的项目说明文档。

隐藏目录如 `.git/`、`.agents/` 属于本地工作环境，不是论文投稿材料本体。正式打包补充材料时可以排除隐藏工作目录。

## 数据说明

原始数据位于：

```text
data/raw/chia_with_scope.zip
data/raw/chia_with_scope/
```

该数据为 CHIA brat 格式标注。brat 标注通常由同名 `.txt` 和 `.ann` 文件组成：

```text
NCT*_inc.txt
NCT*_inc.ann
NCT*_exc.txt
NCT*_exc.ann
```

其中 `.txt` 保存原始临床试验入组或排除标准文本，`.ann` 保存实体、关系、事件和属性标注。

结构化后的输入数据位于：

```text
data/processed/source_criteria.jsonl
data/processed/source_stats.json
```

当前数据规模：

```text
source_criteria.jsonl: 2000 条
```

`source_criteria.jsonl` 每条记录对应一个入组或排除标准编译单元，主要字段包括：

- `doc_id`
- `trial_id`
- `section`
- `text`
- `entities`
- `relations`
- `events`
- `attributes`
- `source`

## 方法输出

4 个方法的布尔表达式输出位于：

```text
data/processed/boolean_outputs/
```

当前文件如下：

```text
flat.jsonl
or_direct.jsonl
constraint.jsonl
cgglc.jsonl
generation_summary.json
```

每个方法均包含 2000 条输出。方法含义如下：

- `flat.jsonl`：Flat 基线，将候选谓词尽量扁平连接。
- `or_direct.jsonl`：OR-direct 基线，直接使用 CHIA OR 事件形成析取结构。
- `constraint.jsonl`：Constraint 基线，保留修饰约束和语义附着，但不进行完整 OR/grouping 恢复。
- `cgglc.jsonl`：本文方法 CG-GLC，综合修饰合并、OR 结构恢复和 scope 辅助分组。

方法输出中的主要字段包括：

- `doc_id`
- `trial_id`
- `section`
- `text`
- `mode`
- `boolean_expression`
- `boolean_ast`
- 结构统计字段，如 `num_entities`、`num_relations`、`num_scope_groups`、`num_or_events`

## GPT 盲评材料

GPT 盲评输入位于：

```text
data/evaluation/llm_judge/
```

主要文件：

- `llm_eval_items.jsonl`：盲化后的 GPT 评估项。每条包含原始纳排标准文本和一个候选布尔表达式。
- `llm_eval_key.csv`：`candidate_id` 到真实方法名的映射表，只能用于评估结束后的解盲汇总，不能提供给 GPT。
- `llm_eval_manifest.json`：记录方法列表、样本规模、随机种子和生成方式。

当前 GPT 评估规模：

```text
2000 条 source criteria × 4 种方法 = 8000 条 GPT 评估项
```

自动导出的 GPT 分批 prompt 位于：

```text
data/evaluation/gpt_manual_batches/
```

当前共有 320 个批次文件，每批 25 条。它们用于手动提交 GPT 评分，不是新的实验数据。

GPT 评分结果位于：

```text
results/llm_eval/llm_judge_results.jsonl
results/llm_eval/llm_judge_per_item.csv
results/llm_eval/llm_judge_summary_by_method.csv
results/llm_eval/llm_judge_paired_vs_cgglc.csv
```

文件作用：

- `llm_judge_results.jsonl`：GPT 原始/最终评分记录，按 `candidate_id` 保存。
- `llm_judge_per_item.csv`：解盲后的逐条明细，包含 `doc_id`、`method_key`、`method_label`、评分和错误标签。
- `llm_judge_summary_by_method.csv`：4 个方法的总体均分。
- `llm_judge_paired_vs_cgglc.csv`：CG-GLC 与各基线的配对比较。

## 人工评估材料

人工评估只抽样 CG-GLC 输出，用于检查本文方法的绝对质量。人工评估文件位于：

```text
results/human_eval/
```

当前只保留 3 个文件：

```text
cgglc_human_eval_1.csv
cgglc_human_eval_2.csv
cgglc_human_eval_summary.csv
```

其中：

- `cgglc_human_eval_1.csv`：评审 1 的 50 条评分。
- `cgglc_human_eval_2.csv`：评审 2 的 50 条评分。
- `cgglc_human_eval_summary.csv`：两名评审评分汇总，包括维度均分、总分均分、完全一致率和平均绝对差异。

50 条人工样本采用分层随机抽样，覆盖 OR、scope 和普通样本。人工评分与 GPT 使用相同的 5 个维度，每个维度 0-2 分，总分 0-10。

## GPT 与人工一致性

GPT-human 一致性分析位于：

```text
results/llm_eval/gpt_human_agreement_summary.csv
```

该文件由 `src/criteria_boolean/compare_gpt_human_eval.py` 生成。比较范围只限于 50 条同时具备人工评分和 GPT 评分的 CG-GLC 样本。它不使用全部 8000 条 GPT 评分直接与 50 条人工评分比较。

该文件包含：

- 两名人工评审之间的一致性。
- GPT 评分与两名人工平均分之间的一致性。
- OR、scope、other 三类样本上的 GPT-human 总分比较。

## 评分维度

GPT 和人工评估均使用同一套 5 维 rubric：

1. `predicate_completeness`：关键实体、数值、时间、限定词、否定等是否形成完整谓词。
2. `logical_correctness`：AND、OR、NOT 是否保留原文逻辑。
3. `grouping_correctness`：并列项、共享修饰语、局部分组和层级结构是否合理。
4. `faithfulness`：候选表达式是否忠实于原文，是否新增或遗漏重要临床条件。
5. `downstream_usability`：是否适合作为队列查询或患者筛选的中间表示。

GPT 输出额外包含：

- `error_flags`：主要错误类型标签。
- `brief_rationale`：简短评分理由。

详细评分规则见：

```text
docs/gpt_manual_evaluation_guide.md
docs/human_eval_scoring_guide.md
```

## 复现命令

安装依赖：

```powershell
pip install -r requirements.txt
```

从原始 CHIA brat 标注生成结构化输入：

```powershell
python src/criteria_boolean/prepare_chia_jsonl.py
```

生成 4 个方法的布尔表达式：

```powershell
python src/criteria_boolean/compile_boolean.py
```

也可以一次运行数据准备和表达式生成：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_generation.ps1
```

生成 GPT 评估输入、GPT 分批 prompt 和两份人工评估表：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/prepare_evaluation_materials.ps1
```

汇总 GPT 评分：

```powershell
python src/criteria_boolean/summarize_llm_judge.py
```

汇总双人工评分：

```powershell
python src/criteria_boolean/summarize_human_eval.py
```

计算 GPT 与人工评分一致性：

```powershell
python src/criteria_boolean/compare_gpt_human_eval.py
```

## 代码入口

```text
src/criteria_boolean/prepare_chia_jsonl.py
src/criteria_boolean/compile_boolean.py
src/criteria_boolean/prepare_llm_eval_dataset.py
src/criteria_boolean/export_gpt_eval_batches.py
src/criteria_boolean/generate_human_eval_sample.py
src/criteria_boolean/summarize_llm_judge.py
src/criteria_boolean/summarize_human_eval.py
src/criteria_boolean/compare_gpt_human_eval.py
```

常用流程脚本：

```text
scripts/run_generation.ps1
scripts/prepare_evaluation_materials.ps1
```

