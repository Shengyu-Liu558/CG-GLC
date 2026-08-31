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
{"candidate_id": "LLM02151", "doc_id": "NCT02894268_inc", "case_bucket": "other", "source_criterion": "A positive 13 C-urea breath test Formal H.pylori treatment more than two times Age >18 years", "candidate_expression": "((13 C-urea breath test positive) AND (Age >18 years) AND (H.pylori treatment more than two times))"}
{"candidate_id": "LLM02152", "doc_id": "NCT03103204_exc", "case_bucket": "or", "source_criterion": "Systemic diseases (diabetes, renal diseases, rheumatic diseases, osteoporosis and cardiovascular diseases) Pregnant and lactating women HIV/ AIDS periodontal treatment in the last year (before baseline appointment) Medication: Immunosuppressive drugs, antibiotics in the past three months (before baseline appointment) ) orthodontic appliance", "candidate_expression": "((AIDS) AND (HIV) AND (Immunosuppressive drugs) AND (Pregnant) AND (Systemic diseases) AND (antibiotics) AND (baseline appointment) AND (lactating) AND (orthodontic appliance) AND (periodontal treatment in the last year before baseline appointment) AND (women))"}
{"candidate_id": "LLM02153", "doc_id": "NCT02267616_exc", "case_bucket": "other", "source_criterion": "Have history of female sterilization procedure Desire for conception in the next 12 months Not sexually active with a male partner", "candidate_expression": "((conception Desire in the next 12 months) AND (female sterilization procedure) AND NOT (sexually active male partner))"}
{"candidate_id": "LLM02154", "doc_id": "NCT00250640_exc", "case_bucket": "or", "source_criterion": "Any condition that prevents participation in the study, including pregnancy and other contraindications for Ventavis treatment (as listed in the current Ventavis Summary of Product Characteristics and patient package insert)", "candidate_expression": "((Ventavis Summary of Product Characteristics and patient package insert) AND (Ventavis treatment) AND (contraindications) AND (pregnancy))"}
{"candidate_id": "LLM02155", "doc_id": "NCT02884115_inc", "case_bucket": "other", "source_criterion": "Early Syphilis Cases Determined to Be Serofast at 6 Months after Initial Treatment", "candidate_expression": "((Early Syphilis Serofast) AND (Treatment Initial))"}
{"candidate_id": "LLM02156", "doc_id": "NCT02668978_inc", "case_bucket": "or", "source_criterion": "Patients over the age of 18 years who are able to give their informed consent Lobar and sublobar resections Open, video-assisted thoracoscopic or robotic surgeries Diagnostic or therapeutic procedures", "candidate_expression": "((able to give their informed consent) AND (over the age of 18 years) AND (video-assisted) AND ((Diagnostic procedures) OR (therapeutic procedures)) AND ((Lobar resections) OR (sublobar resections)) AND ((robotic surgeries) OR (thoracoscopic surgeries)))"}
{"candidate_id": "LLM02157", "doc_id": "NCT03187379_inc", "case_bucket": "other", "source_criterion": "bariatric surgery patients laparoscopic roux-en-y gastric bypass use of EEA stapler anastomosis", "candidate_expression": "((EEA stapler anastomosis) AND (bariatric surgery) AND (laparoscopic) AND (roux-en-y gastric bypass))"}
{"candidate_id": "LLM02158", "doc_id": "NCT02735902_inc", "case_bucket": "other", "source_criterion": "The patient or his/her representative must have given free and informed consent and signed the consent The patient must be insured or beneficiary of a health insurance plan The patient is available for 12 months of follow-up The patient underwent a successful transcutaneous implant procedure for an aortic valve within the past 24 hours The patient was receiving anti-vitamin K (AVK) treatment before percutaneous implantation of the aortic valve", "candidate_expression": "((AVK) AND (The patient is available for 12 months of follow-up) AND (The patient or his/her representative must have given free and informed consent and signed the consent) AND (anti-vitamin K) AND (aortic valve) AND (before percutaneous implantation of the aortic valve) AND (past 24 hours) AND (percutaneous implantation of the aortic valve) AND (transcutaneous implant procedure))"}
{"candidate_id": "LLM02159", "doc_id": "NCT03025620_inc", "case_bucket": "or", "source_criterion": "Elderly patients over 65 years old exhibiting clinical indices of cardiovascular disease Male or female Subjects who were hospitalized in the Geriatric Unit of the Emile Roux Hospital (AP-HP) MMSE (Mini Mental State Examination)score > or = 15 Supervision available for study medication Able to ingest oral diet", "candidate_expression": "((Able to ingest oral diet) AND (Elderly) AND (Geriatric Unit of the Emile Roux Hospital (AP-HP)) AND (MMSE (Mini Mental State Examination)) AND (Male) AND (female) AND (old) AND (over 65 years) AND (score > or = 15))"}
{"candidate_id": "LLM02160", "doc_id": "NCT03318874_inc", "case_bucket": "other", "source_criterion": "Meibomian Gland Dysfunction Eligible for heat treatment Ocular Surface Disease Index (OSDI) >12 Quality or expressibility score =20 years old: >1 or >20 years old: =1 Non-invasive tear film break-up time (NITBUT) <10 s in at least one eye Schirmer-1 test >5 mm after 5 min", "candidate_expression": "((Meibomian Gland Dysfunction) AND (Non-invasive tear film break-up time (NITBUT) <10 s eye) AND (OSDI) AND (Ocular Surface Disease Index >12) AND (Schirmer-1 test >5 mm after 5 min) AND (expressibility score) AND (heat treatment Eligible for) AND (score Quality))"}
{"candidate_id": "LLM02161", "doc_id": "NCT00806273_exc", "case_bucket": "other", "source_criterion": "ASA 3+ No current treatment plan at OHSU Severely carious teeth resulting in inability to isolate for procedure Unable to understand or sign consent form", "candidate_expression": "((ASA 3+) AND (No) AND (OHSU) AND (Severely) AND (Unable to understand or sign consent form) AND (carious teeth) AND (current) AND (inability to isolate for procedure) AND (treatment plan))"}
{"candidate_id": "LLM02162", "doc_id": "NCT02441179_exc", "case_bucket": "or", "source_criterion": "1. Orthopedic injuries that are unstable 2. Osteoporosis with high risk of pathological fracture 3. Cutaneous lesions and/or pressure ulcers 4. Joint contractures 5. Cardiopulmonary diseases 6. Body weight exceeding 150 Kg", "candidate_expression": "((Body weight exceeding 150 Kg) AND (Cardiopulmonary diseases) AND (Joint contractures) AND (Orthopedic injuries unstable) AND (Osteoporosis high risk of pathological fracture) AND (high risk of pathological fracture) AND ((Cutaneous lesions) OR (pressure ulcers)))"}
{"candidate_id": "LLM02163", "doc_id": "NCT03372304_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologists Classification I-III Normal cognitive function in order to sign written, informed consent and to understand trial protocol Agreement to the trial protocol, including the randomized manner", "candidate_expression": "((Agreement to the trial protocol, including the randomized manner) AND (American Society of Anesthesiologists Classification I-III) AND (ormal cognitive function in order to sign written, informed consent and to understand trial protoco))"}
{"candidate_id": "LLM02164", "doc_id": "NCT02733159_inc", "case_bucket": "other", "source_criterion": "Histologically confirmed PD-L1 status defined NSCLC. Biopsy must be within 70 days of first treatment with pembrolizumab. ECOG performance status 2. Life expectancy > 12 weeks. Uni-dimensionally measurable disease according to Response Evaluation Criteria in Solid Tumours (RECIST) v1.1 Computerised Tomography (CT) scan of chest and abdomen within 28 days of starting pembrolizumab. Adequate haematological function: Platelet count ≥100 x 109 /L. Neutrophils ≥1.5 x 109/L. Haemoglobin ≥ 9g/dL. Adequate hepatic function: Serum bilirubin ≤1.5 x upper limit of normal (ULN). Serum transaminases ≤2.5 x ULN. Adequate renal function: Creatinine clearance <1.5 times ULN concurrent with creatinine clearance >50 ml/min. Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.", "candidate_expression": "((2) AND (<1.5 times ULN) AND (>50 ml/min) AND (Adequate) AND (Biopsy) AND (Computerised Tomography (CT) scan of chest and abdomen) AND (Creatinine clearance) AND (ECOG performance status) AND (Haemoglobin) AND (Life expectancy) AND (NSCLC) AND (Neutrophils) AND (PD-L1 status) AND (Platelet count) AND (Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.) AND (Response Evaluation Criteria in Solid Tumours (RECIST) v1.1) AND (Serum bilirubin) AND (Serum transaminases) AND (Uni-dimensionally measurable) AND (concurrent) AND (creatinine clearance) AND (disease) AND (first treatment with pembrolizumab) AND (pembrolizumab) AND (renal function) AND (starting pembrolizumab) AND (within 28 days of starting pembrolizumab) AND (within 70 days of first treatment) AND (≤1.5 x upper limit of normal (ULN)) AND (≤2.5 x ULN) AND (≥ 9g/dL) AND (≥1.5 x 109/L) AND (≥100 x 109 /L))"}
{"candidate_id": "LLM02165", "doc_id": "NCT03018171_exc", "case_bucket": "or", "source_criterion": "Suspect or certainty of fetal malformation, Presence of conditions such as preeclampsia, multiparity, preterm labor History of adverse reaction to a-2 adrenergic agonists Nicotine addiction Chronic use of opioid", "candidate_expression": "((Chronic use) AND (Nicotine addiction) AND (a-2 adrenergic agonists) AND (adverse reaction) AND (fetal malformation) AND (opioi) AND ((Suspect) OR (certainty)) AND ((multiparity) OR (preeclampsia) OR (preterm labor)))"}
{"candidate_id": "LLM02166", "doc_id": "NCT02689817_exc", "case_bucket": "or", "source_criterion": "Existing sacral pressure ulcer, undergoing a cardiac procedure, or inability to provide informed consent.", "candidate_expression": "((cardiac procedure) AND (inability to provide informed consent) AND (sacral pressure ulcer))"}
{"candidate_id": "LLM02167", "doc_id": "NCT02416765_inc", "case_bucket": "or", "source_criterion": "1. Males and females ≥ 18 years old. 2. Clinical diagnosis of type 1 diabetes for at least one year. 3. The subject will have been on insulin pump therapy for at least 3 months and currently using a fast actin insulin analog (Lispro, Aspart or Guilisine). 4. Last (less than 3 months) HbA1c ≤ 10%. 5. Currently using carbohydrate counting as the meal insulin dose strategy.", "candidate_expression": "((Aspart) AND (Currently) AND (Guilisine) AND (HbA1c) AND (Last (less than 3 months)) AND (Lispro) AND (Males) AND (carbohydrate counting) AND (currently) AND (fast actin insulin analog) AND (females) AND (for at least 3 months) AND (for at least one year) AND (insulin pump therapy) AND (meal insulin dose strategy) AND (old) AND (type 1 diabetes) AND (≤ 10%) AND (≥ 18 years old))"}
{"candidate_id": "LLM02168", "doc_id": "NCT02222272_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02169", "doc_id": "NCT03083197_inc", "case_bucket": "or", "source_criterion": "Age = 15 years old Hospitalization with acute undifferentiated fever (temperature > 37.5 C, tympanic) =14 days or patients admitted to hospital with a history of fever = 14 days who subsequently develop fever within 24 hours of admission Clinically suspected scrub typhus: defined as acute undifferentiated fever with no clear focus of infection and negative malaria blood smear and/or negative malaria RDT. Patients may have one, none, or a combination of other clinical findings such as eschar, rash, lymphadenopathy, headache, myalgia, cough, nausea and abdominal discomfort. A positive scrub typhus RDT (Scrub Typhus IgM RDT, InBios International, Seattle, WA, USA) and/or positive PCR-based detection of O. tsutsugamushi DNA from the admission blood sample Written informed consent and/or, written informed assent as required Able to take oral medication", "candidate_expression": "((= 14 days) AND (= 15 years old) AND (=14 days) AND (> 37.5 C) AND (Able to take oral medication) AND (Age) AND (Hospitalization) AND (O. tsutsugamushi DNA) AND (Scrub Typhus IgM RDT) AND (acute undifferentiated fever) AND (admission) AND (admission blood sample) AND (admitted to hospital) AND (fever) AND (focus of infection) AND (history) AND (negative) AND (no clear) AND (oral medication) AND (positive) AND (scrub typhus) AND (temperature) AND (tympanic) AND (within 24 hours of admission) AND ((malaria RDT) OR (malaria blood smear)) AND ((a combination of) OR (none) OR (one)) AND ((abdominal discomfort) OR (cough) OR (eschar) OR (headache) OR (lymphadenopathy) OR (myalgia) OR (nausea) OR (rash)) AND ((PCR) OR (scrub typhus RDT)) AND ((Written informed consent) OR (written informed assent)))"}
{"candidate_id": "LLM02170", "doc_id": "NCT02964416_inc", "case_bucket": "or", "source_criterion": "Patients with craniotomy for supratentorial tumors under general anesthesia American Society of Anaesthesiologists (ASA) 2 and stable ASA 3 patients Elective surgery Patients with Glasgow Coma Scale (GCS) 15/15", "candidate_expression": "((ASA) AND (Elective surgery) AND (GCS) AND (Glasgow Coma Scale 15/15) AND (craniotomy) AND (general anesthesia) AND (supratentorial tumors) AND ((ASA stable 3) OR (American Society of Anaesthesiologists 2)))"}
{"candidate_id": "LLM02171", "doc_id": "NCT02897856_exc", "case_bucket": "or", "source_criterion": "Cardiac arrest Head trauma Drowning Congenital heart disease Inborn errors of metabolism Electrolyte imbalance (hypocalcaemia, hyponatremia and hypoglycemia) Hemodynamic instability Allergy to benzodiazepines Focal seizures with preserved level of consciousness", "candidate_expression": "((Allergy) AND (Cardiac arrest) AND (Congenital heart disease) AND (Drowning) AND (Electrolyte imbalance) AND (Focal seizures) AND (Head trauma) AND (Hemodynamic instability) AND (Inborn errors of metabolism) AND (benzodiazepines) AND (hypocalcaemia) AND (hypoglycemia) AND (hyponatremia) AND (preserved level of consciousness))"}
{"candidate_id": "LLM02172", "doc_id": "NCT02763007_exc", "case_bucket": "or", "source_criterion": "eGFR(Epidermal growth factor receptor) < 50mL/min AST(aspartate aminotransferase)/ALT(alanine aminotransaminase) >2.5 upper limit of normal Pregnant or lactating women Subject who the investigator deems inappropriate to participate in this study Patients with a history of bladder cancer or patients with active bladder cancer Patients with uninvestigated macroscopic hematuria Patients with cardiac failure or a history of cardiac failure (New York Heart Association [NYHA] Stages 3 to 4) Patients with genetic problems such as galactose intolerance, Lapp lactase deficiency or glucose-galactose malabsorption, since this study drug contains lactose", "candidate_expression": "((ALT) AND (AST) AND (Epidermal growth factor receptor) AND (NYHA) AND (New York Heart Association Stages 3 to 4) AND (Pregnant or lactating women) AND (alanine aminotransaminase) AND (aspartate aminotransferase) AND (eGFR < 50mL/min) AND (genetic problems) AND (macroscopic hematuria uninvestigated) AND ((bladder cancer) OR (bladder cancer active)) AND ((cardiac failure) OR (history of cardiac failure)) AND ((Lapp lactase deficiency) OR (galactose intolerance) OR (glucose-galactose malabsorption)))"}
{"candidate_id": "LLM02173", "doc_id": "NCT03044093_inc", "case_bucket": "other", "source_criterion": "healthy no allergy known to these drugs second trimester abortion", "candidate_expression": "((abortion) AND (allergy) AND (healthy) AND (no) AND (second trimester) AND (these drugs))"}
{"candidate_id": "LLM02174", "doc_id": "NCT03639519_inc", "case_bucket": "other", "source_criterion": "Elective Cardiac surgery American Society of Anesthesiologists physical status class I-III", "candidate_expression": "((American Society of Anesthesiologists physical status) AND (Elective Cardiac surgery) AND (class I-III))"}
{"candidate_id": "LLM02175", "doc_id": "NCT02563535_inc", "case_bucket": "other", "source_criterion": "age>18 years critical limb ischemia (Rutherford class 4-6) angiographic stenosis>50% or occlusion of at least one tibial vessel of at least 40mm for which an interventional treatment is scheduled", "candidate_expression": "((4-6) AND (>18 years) AND (>50%) AND (Rutherford class) AND (age) AND (angiographic stenosis) AND (at least 40mm) AND (at least one) AND (critical) AND (interventional treatment) AND (limb ischemia) AND (occlusion) AND (scheduled) AND (tibial vessel))"}
```
