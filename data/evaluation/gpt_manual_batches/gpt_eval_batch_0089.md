# GPT-5.5 Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT-5.5 评估指南

本指南用于让 GPT-5.5 对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT-5.5 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

## 评估角色

请作为独立评估者，逐条评价候选布尔表达式。每条样本只允许使用以下信息：

- 原始纳排标准文本。
- 一个候选布尔表达式。
- 本指南中的评分细则。

请不要推测候选表达式由哪种方法生成，不要使用任何隐藏参考答案，不要根据表达式长短直接加分或扣分。评价重点是候选表达式是否保留原文临床含义。

## 输入字段

每条候选通常包含：

- `candidate_id`：盲化候选编号。
- `doc_id`：原始纳排标准编译单元编号。
- `case_bucket`：样本类型，可能为 `or`、`scope` 或 `other`。
- `source_criterion`：原始纳排标准文本。
- `candidate_expression`：候选布尔表达式。

`candidate_id` 是唯一需要在输出中保留的样本键。不要输出方法名。

## 评分流程

对每条候选按以下顺序评估：

1. 阅读 `source_criterion`，识别关键临床条件、数值、时间、限定词、否定、并列关系和局部分组。
2. 阅读 `candidate_expression`，判断它是否表达了相同临床含义。
3. 分别给五个维度打 0、1、2 分。
4. 选择适用的 `error_flags`。
5. 写一句非常简短的 `brief_rationale`，说明主要扣分原因或为什么基本正确。

不同候选之间不要相互比较；每条候选都只与自己的原始文本比较。

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

## 错误标签

从以下标签中选择 1 个或多个：

- `missing_key_condition`：遗漏关键条件。
- `extra_condition`：新增原文不支持的条件。
- `wrong_or_logic`：析取条件遗漏或被错误表示为 AND。
- `wrong_and_logic`：必须同时满足的条件遗漏或被错误表示为 OR。
- `wrong_negation`：否定缺失、误加或作用范围错误。
- `wrong_scope_or_grouping`：分组、嵌套或共享修饰语作用范围错误。
- `predicate_fragmentation`：同一临床谓词被拆成混乱片段。
- `overly_verbose`：表达过度冗长并影响可用性。
- `empty_or_unusable`：空输出或不可用。
- `none`：无明显错误标签。

如果没有明显错误，`error_flags` 只能填写 `["none"]`。如果存在其他错误标签，不要同时填写 `none`。

## 输出格式

请严格输出 JSONL。每个候选只输出一行 JSON，不要输出 Markdown 表格，不要输出额外解释文字。

输出字段必须为：

- `candidate_id`
- `predicate_completeness`
- `logical_correctness`
- `grouping_correctness`
- `faithfulness`
- `downstream_usability`
- `total_score`
- `error_flags`
- `brief_rationale`

示例：

```json
{"candidate_id":"EXAMPLE_ID","predicate_completeness":2,"logical_correctness":2,"grouping_correctness":1,"faithfulness":2,"downstream_usability":1,"total_score":8,"error_flags":["wrong_scope_or_grouping"],"brief_rationale":"Main predicates and logic are preserved, but one local grouping is ambiguous."}
```

`total_score` 必须等于五个维度分数之和，范围为 0-10。

## 推荐投喂方式

全量评估约有 8000 个候选，不建议一次性输入。建议每批 20-50 个候选。

可用以下命令导出批次文件：

```powershell
python src/criteria_boolean/export_gpt_eval_batches.py --batch-size 25
```

批次文件位于：

```text
data/evaluation/gpt_manual_batches/
```

每批评估步骤：

1. 粘贴本评估指南。
2. 粘贴一批候选 JSONL。
3. 要求模型只输出同样数量的 JSONL 评分结果。
4. 检查输出行数是否与输入候选数一致。
5. 将输出追加保存到 `results/llm_eval/llm_judge_results.jsonl`。

全部批次保存后运行：

```powershell
python src/criteria_boolean/summarize_llm_judge.py
```

## 给 Codex 或 GPT-5.5 的输入模板

如果使用 Codex 直接读取本项目文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md 中的所有候选。

要求：
1. 只根据每条样本的 source_criterion 和 candidate_expression 评分。
2. 不要读取或使用 data/evaluation/llm_judge/llm_eval_key.csv。
3. 不要推测方法名。
4. 每个 candidate_id 输出一行 JSONL。
5. 输出字段必须包含 candidate_id、五个维度分数、total_score、error_flags、brief_rationale。
6. 不输出 Markdown 表格，不输出额外解释文字。
```

如果需要 Codex 直接写入结果文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md，
并把 JSONL 结果追加保存到 results/llm_eval/llm_judge_results.jsonl。

注意：
- 不要读取 data/evaluation/llm_judge/llm_eval_key.csv。
- 如果结果文件不存在，请创建它。
- 如果输出行数不是25行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM02201", "doc_id": "NCT02370069_inc", "case_bucket": "or", "source_criterion": "Males and females of 18 years of age or older at the time of the vaccination Severe chronic kidney disease (Stage 4 and 5)", "candidate_expression": "((18 years or older) AND (Severe) AND (age) AND (at the time of the vaccination) AND (chronic kidney disease) AND (vaccination) AND ((Males) OR (females)) AND ((Stage 4 chronic kidney disease) OR (Stage 5 chronic kidney disease)))"}
{"candidate_id": "LLM02202", "doc_id": "NCT03067740_inc", "case_bucket": "other", "source_criterion": "Patients are of American Society of Anesthesiologists (ASA) physical status I and II, aged 8-14 years old, of both gender, with suspected acute appendicitis scheduled for laparoscopic appendicectomy.", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists physical status I and II) AND (acute appendicitis suspected) AND (aged 8-14 years old) AND (both gender) AND (laparoscopic appendicectomy scheduled for))"}
{"candidate_id": "LLM02203", "doc_id": "NCT03146390_inc", "case_bucket": "other", "source_criterion": "Systemically healthy adults. Minimum of 24 permanent teeth. No gingivitis (Community Periodontal Index score = 0). No periodontitis (Community Periodontal Index score = 0). Absence of untreated caries.", "candidate_expression": "((Community Periodontal Index score = 0) AND (adults) AND (healthy Systemically) AND (permanent teeth Minimum of 24) AND NOT (periodontitis) AND NOT (caries untreated) AND NOT (gingivitis))"}
{"candidate_id": "LLM02204", "doc_id": "NCT01943812_inc", "case_bucket": "or", "source_criterion": "Endometrial thickness = 7 mm after stimulation 18-45 years IVF/ICSI fertilisation BMI > 18,5 <30 kg/m2 cycle length 25-34 days", "candidate_expression": "((BMI > 18,5 <30 kg/m2) AND (Endometrial thickness = 7 mm after stimulation) AND (cycle length 25-34 days) AND (stimulation stimulation) AND (years 18-45) AND ((ICSI fertilisation) OR (IVF fertilisation)))"}
{"candidate_id": "LLM02205", "doc_id": "NCT03168178_inc", "case_bucket": "other", "source_criterion": "Pregnant women between 34-42 weeks gestation Singleton fetus Admitted for labor management & develops a fever of 100.4 F or greater", "candidate_expression": "((Pregnant) AND (Singleton fetus) AND (fever 100.4 F or greater) AND (gestation between 34-42 weeks) AND (labor management Admitted for) AND (women))"}
{"candidate_id": "LLM02206", "doc_id": "NCT02550769_exc", "case_bucket": "other", "source_criterion": "Do not sign informed consent Pregnant patients Liver cirrhosis Undifferentiated adenocarcinoma. cT4 Metastatic disease (M1) chronic renal failure on dialysis ASA IV BMI <18 and> 35 kg / m2", "candidate_expression": "((<18 and> 35 kg / m2) AND (ASA) AND (BMI) AND (Do not sign informed consent) AND (IV) AND (Liver cirrhosis) AND (Metastatic disease (M1)) AND (Pregnant) AND (Undifferentiated) AND (adenocarcinoma) AND (cT4) AND (chronic renal failure) AND (dialysis))"}
{"candidate_id": "LLM02207", "doc_id": "NCT02312089_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Myoma) AND (Uterine abnormalities) AND (endometriosis Moderate severe) AND (uterine surgery))"}
{"candidate_id": "LLM02208", "doc_id": "NCT02894268_inc", "case_bucket": "other", "source_criterion": "A positive 13 C-urea breath test Formal H.pylori treatment more than two times Age >18 years", "candidate_expression": "((13 C-urea breath test positive) AND (Age >18 years) AND (H.pylori treatment more than two times))"}
{"candidate_id": "LLM02209", "doc_id": "NCT02631512_exc", "case_bucket": "or", "source_criterion": "Ulcers due to non-diabetic etiology. Uncontrolled diabetes defined as HbA1c above 70 mmol/mol and insufficient nutritional status. Ulcers older than 1 year. Any of gangrene, osteomyelitis, cellulitis, or Charcot osteoarthropathy.", "candidate_expression": "((HbA1c above 70 mmol/mol) AND (Ulcers non-diabetic) AND (Ulcers older than 1 year) AND (Uncontrolled diabetes) AND (insufficient nutritional status) AND ((Charcot osteoarthropathy) OR (cellulitis) OR (gangrene) OR (osteomyelitis)))"}
{"candidate_id": "LLM02210", "doc_id": "NCT02415257_inc", "case_bucket": "other", "source_criterion": "Vestibular schwannoma advised to surgical treatment No measurable remaining vestibular function", "candidate_expression": "((Vestibular schwannoma) AND (surgical treatment advised) AND NOT (remaining vestibular function))"}
{"candidate_id": "LLM02211", "doc_id": "NCT02242188_exc", "case_bucket": "or", "source_criterion": "preterm delivery (<37 weeks of gestation) birth weight < 2500 g multiple pregnancy major illness or congenital anomaly being <50% breastfed at the time of inclusion food allergy anaemia (Hb <105 g/L [10.5 g/dL]) at inclusion, lack of informed consent", "candidate_expression": "((Hb <105 g/L 10.5 g/dL) AND (anaemia at inclusion) AND (birth weight < 2500 g) AND (breastfed <50% at the time of inclusion) AND (congenital anomaly) AND (food allergy) AND (gestation <37 weeks) AND (lack of informed consent) AND (major illness) AND (multiple pregnancy) AND (preterm delivery))"}
{"candidate_id": "LLM02212", "doc_id": "NCT03264911_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to B-lactams concomitant disease which must be treated with antibiotics chronic disease-Immunocompromised Antibiotics within 72 h history of ARF,scarlet fever,impetigo,acute glomerulonephritis Family history of ARF Complicated pharyngitis", "candidate_expression": "((ARF) AND (Antibiotics) AND (B-lactams) AND (Complicated) AND (Family history) AND (Hypersensitivity) AND (Immunocompromised) AND (antibiotics) AND (concomitant) AND (disease) AND (history) AND (pharyngitis) AND (treated) AND (within 72 h) AND ((ARF) OR (acute glomerulonephritis) OR (impetigo) OR (scarlet fever)))"}
{"candidate_id": "LLM02213", "doc_id": "NCT02897856_exc", "case_bucket": "or", "source_criterion": "Cardiac arrest Head trauma Drowning Congenital heart disease Inborn errors of metabolism Electrolyte imbalance (hypocalcaemia, hyponatremia and hypoglycemia) Hemodynamic instability Allergy to benzodiazepines Focal seizures with preserved level of consciousness", "candidate_expression": "((Allergy) AND (Cardiac arrest) AND (Congenital heart disease) AND (Drowning) AND (Electrolyte imbalance) AND (Focal seizures) AND (Head trauma) AND (Hemodynamic instability) AND (Inborn errors of metabolism) AND (benzodiazepines) AND (preserved level of consciousness) AND ((hypocalcaemia) OR (hypoglycemia) OR (hyponatremia)))"}
{"candidate_id": "LLM02214", "doc_id": "NCT03476850_inc", "case_bucket": "other", "source_criterion": "Patients undergoing laparoscopic assisted donor nephrectomy Patients that have elected to have a nerve block 18 years of age or older Patients of ASA status I - III", "candidate_expression": "((ASA status I - III) AND (age 18 years or older) AND (laparoscopic assisted donor nephrectomy) AND (nerve block elected to have))"}
{"candidate_id": "LLM02215", "doc_id": "NCT03263481_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02216", "doc_id": "NCT03297944_inc", "case_bucket": "other", "source_criterion": "valid driver's license english-speaking and literate", "candidate_expression": "((english-speaking) AND (literate) AND (valid driver's license))"}
{"candidate_id": "LLM02217", "doc_id": "NCT02833116_inc", "case_bucket": "or", "source_criterion": "Unilateral leg pain secondary to lateral stenosis, disc protrusion or herniated disc. Age between 18 and 80 years. Moderate to severe pain (NVS>4). Right proficient oral and written language.", "candidate_expression": "((>4)) AND (Age) AND (Moderate) AND (NVS) AND (Right proficient oral and written language) AND (Unilateral leg pain) AND (between 18 and 80 years) AND (disc protrusion) AND (herniated disc) AND (lateral stenosis) AND (pain) AND (severe))"}
{"candidate_id": "LLM02218", "doc_id": "NCT03077204_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02219", "doc_id": "NCT00250640_exc", "case_bucket": "or", "source_criterion": "Any condition that prevents participation in the study, including pregnancy and other contraindications for Ventavis treatment (as listed in the current Ventavis Summary of Product Characteristics and patient package insert)", "candidate_expression": "((Ventavis treatment Ventavis Summary of Product Characteristics and patient package insert) AND (contraindications) AND (pregnancy))"}
{"candidate_id": "LLM02220", "doc_id": "NCT01793831_exc", "case_bucket": "or", "source_criterion": "Diagnosis as CD first time or first year. No history of using 5-ASA, biological or immunomodulatory therapy", "candidate_expression": "((5-ASA) AND (CD first time first year) AND (immunomodulatory therapy) AND (therapy biological))"}
{"candidate_id": "LLM02221", "doc_id": "NCT00886158_inc", "case_bucket": "other", "source_criterion": "Age from birth to 21 years All solid organ transplant recipients receiving their care at Seattle Children's Hospital Signed consent, and when age appropriate, signed assent", "candidate_expression": "((Age from birth to 21 years) AND (Seattle Children's Hospital) AND (Signed consent, and when age appropriate, signed assent) AND (solid organ transplant))"}
{"candidate_id": "LLM02222", "doc_id": "NCT01942109_exc", "case_bucket": "other", "source_criterion": "uncontrolled hypertension uncontrolled diabetes creatinine > 2,5 mg/dl potassium > 6 mg/dl acute coronary syndrome hypertrophic cardiomyopathy", "candidate_expression": "((acute coronary syndrome) AND (creatinine > 2,5 mg/dl) AND (diabetes uncontrolled) AND (hypertension uncontrolled) AND (hypertrophic cardiomyopathy) AND (potassium > 6 mg/dl))"}
{"candidate_id": "LLM02223", "doc_id": "NCT02590822_exc", "case_bucket": "or", "source_criterion": "• Diabetes duration >12 years Currently taking more than three glucose lowering therapies Weight-loss of >5kg in the preceding 6 months Stage 4 or 5 chronic kidney disease (eGFR< 30ml/min/1.73m2), Current therapy with Insulin, thiazolidinediones, steroids or atypical antipsychotic medication Untreated thyroid disease Known macrovascular disease including coronary artery disease, stroke/TIA or peripheral vascular disease Presence of arrhythmia (including atrial fibrillation, atrial flutter, or 2nd or 3rd degree atrioventricular block) Known heart failure Other clinically relevant heart disease Inability to exercise or undertake a MRP Absolute contraindication to CMR Cardiovascular symptoms (angina, limiting dyspnoea during normal physical activity) Inflammatory condition e.g. Connective tissue disorder, Rheumatoid arthritis", "candidate_expression": "((2nd degree atrioventricular block) AND (3rd degree atrioventricular block) AND (CMR) AND (Cardiovascular symptoms) AND (Connective tissue disorder,) AND (Diabetes >12 years) AND (Inflammatory) AND (Insulin) AND (MRP) AND (Rheumatoid arthritis) AND (TIA) AND (Weight-loss >5kg preceding 6 months) AND (angina) AND (arrhythmia) AND (atrial fibrillation) AND (atrial flutter) AND (atypical antipsychotic medication) AND (chronic kidney disease Stage 4 or 5) AND (contraindication) AND (coronary artery disease) AND (dyspnoea) AND (eGFR < 30ml/min/1.73m2) AND (exercise) AND (glucose lowering therapies more than three) AND (heart disease) AND (heart failure) AND (macrovascular disease) AND (peripheral vascular disease) AND (steroids) AND (stroke) AND (thiazolidinediones) AND (thyroid disease Untreated))"}
{"candidate_id": "LLM02224", "doc_id": "NCT02553226_exc", "case_bucket": "or", "source_criterion": "Unable to read and understand the Danish language or to give informed consent Cervical dilatation > 4 cm Non-cephalic presentation Multiple gestation Pathological fetal heart rate pattern (cardiotocogram, CTG) before Syntocinon® initiation Fetal weight estimation > 4500 g (clinical or ultrasonic) Subject declines participation Gestational age less than 37 completed weeks", "candidate_expression": "((> 4 cm) AND (> 4500 g) AND (CTG) AND (Cervical dilatation) AND (Fetal weight estimation) AND (Gestational age) AND (Multiple gestation) AND (Non-cephalic presentation) AND (Pathological fetal heart rate pattern) AND (Subject declines participation) AND (Syntocinon®) AND (Syntocinon® initiation) AND (Unable to give informed consent) AND (Unable to read) AND (Unable to understand the Danish language) AND (before Syntocinon® initiation) AND (cardiotocogram) AND (clinical) AND (less than 37 completed weeks) AND (ultrasonic))"}
{"candidate_id": "LLM02225", "doc_id": "NCT02529475_exc", "case_bucket": "or", "source_criterion": "Patients minors Patients on a legal protection regime type guardianship Respiratory pathologies, cardiovascular, renal, diabetes Claustrophobia Contraindications to exposure to a magnetic field Contraindications to injecting Dotarem ®", "candidate_expression": "((Claustrophobia) AND (Contraindications) AND (Dotarem) AND (Respiratory pathologies) AND (cardiovascular) AND (diabetes) AND (legal protection regime type guardianship) AND (magnetic field) AND (minors) AND (renal))"}
```
