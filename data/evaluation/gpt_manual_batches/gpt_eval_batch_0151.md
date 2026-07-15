# GPT Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT 评估指南

本指南用于让大模型对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

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

## 给 Codex 或 GPT 的输入模板

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
- 如果输出行数不是 25 行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM03751", "doc_id": "NCT00886158_inc", "case_bucket": "other", "source_criterion": "Age from birth to 21 years All solid organ transplant recipients receiving their care at Seattle Children's Hospital Signed consent, and when age appropriate, signed assent", "candidate_expression": "((Age) AND (Seattle Children's Hospital) AND (Signed consent, and when age appropriate, signed assent) AND (from birth to 21 years) AND (solid organ transplant))"}
{"candidate_id": "LLM03752", "doc_id": "NCT02607748_exc", "case_bucket": "or", "source_criterion": "Age < 18 years Creatinine > 1.5 mg/dL History of severe allergy to Iodine contrast agents Pregnancy Active atrial fibrillation Multiple premature ventricular or atrial contractions Ejection fraction <35% Class III congestive heart failure", "candidate_expression": "((< 18 years) AND (<35%) AND (> 1.5 mg/dL) AND (Age) AND (Class III) AND (Creatinine) AND (Ejection fraction) AND (Iodine contrast agents) AND (Pregnancy) AND (allergy) AND (atrial fibrillation) AND (congestive heart failure) AND ((Multiple premature atrial contractions) OR (Multiple premature ventricular contractions)))"}
{"candidate_id": "LLM03753", "doc_id": "NCT03100513_inc", "case_bucket": "other", "source_criterion": "Adult Patients with Overt Hepatic Encephalopathy.", "candidate_expression": "((Adult) AND (Overt Hepatic Encephalopathy))"}
{"candidate_id": "LLM03754", "doc_id": "NCT02303171_inc", "case_bucket": "other", "source_criterion": "Pregnant women with APS diagnosed according to the revised classification criteria for APS in 2006 in Sydney, Australia Early pregnancy body weight is 50-90 Kg", "candidate_expression": "((APS revised classification criteria for APS in 2006 in Sydney, Australia) AND (Pregnant) AND (body weight Early pregnancy 50-90 Kg) AND (women))"}
{"candidate_id": "LLM03755", "doc_id": "NCT03335904_exc", "case_bucket": "other", "source_criterion": "history of hypertension known impaired renal function liver disease heart failure myocardial infarction coronary artery disease smoked within the past year apnea hypopnea index > 5 events per hour", "candidate_expression": "((> 5 events per hour) AND (apnea hypopnea index) AND (coronary artery disease) AND (heart failure) AND (history) AND (hypertension) AND (impaired renal function) AND (liver disease) AND (myocardial infarction) AND (smoked) AND (within the past year))"}
{"candidate_id": "LLM03756", "doc_id": "NCT01604187_inc", "case_bucket": "other", "source_criterion": "ASA I-III Colonoscopy Written informed consent from participating subject", "candidate_expression": "((ASA) AND (Colonoscopy) AND (I-III) AND (Written informed consent from participating subject))"}
{"candidate_id": "LLM03757", "doc_id": "NCT01850147_exc", "case_bucket": "or", "source_criterion": "Pre-existing hemoptysis of a severity > grade 3 by NCI CTCAE criteria within 4 weeks prior to study entry Uncontrolled hypertension CHF, angina or arrhythmias LVEF < 1 UNL Existing a second malignancy within 5 years Infected with HIV", "candidate_expression": "((< 1 UNL) AND (> grade 3) AND (CHF) AND (HIV) AND (LVEF) AND (NCI CTCAE criteria) AND (Uncontrolled) AND (angina) AND (arrhythmias) AND (hemoptysis) AND (hypertension) AND (second malignancy) AND (severity) AND (study entry) AND (within 4 weeks prior to study entry) AND (within 5 years))"}
{"candidate_id": "LLM03758", "doc_id": "NCT02673359_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Congenital uterine malformation. Multifetal pregnancy. Known major fetal structural or chromosomal abnormality. Known allergy or contraindication (relative or absolute) to progesterone therapy. Presence of contraindication to cervical cerclage. Medical conditions complicating pregnancy. Vaginal bleeding.", "candidate_expression": "((Age < 20 > 35 years) AND (Congenital uterine malformation) AND (Medical conditions complicating pregnancy) AND (Multifetal pregnancy) AND (Vaginal bleeding) AND (allergy) AND (cervical cerclage) AND (chromosomal abnormality) AND (contraindication) AND (contraindication relative absolute) AND (fetal structural) AND (progesterone therapy))"}
{"candidate_id": "LLM03759", "doc_id": "NCT03124329_exc", "case_bucket": "or", "source_criterion": "Molar teeth Milller Class 4 recession defects Pregnancy (Self-reported) Smoking Uncontrolled local or systemic diseases that affects wound healing (diabetes, autoimmune or inflammatory disorders) Past history of systemic steroid use over 2 weeks within the last 2 years Poor oral hygiene on a non-compliant individual Ibuprofen Allergy/interlerance Anticoagulant therapy (e.g. Warfarin, Plavix, etc.), will not be automatic exclusion but patients will be required to have INR test performed and have values between 2.0 to 3. Physician consultation will be requested to determine whether anticoagulant therapy can be discontinued for 3 days prior to surgery. Objection to blood draw or application of blood products Students and staff from USC Ostrow school of Dentistry will not be recruited for this study", "candidate_expression": "((Anticoagulant therapy) AND (INR test between 2.0 to 3) AND (Ibuprofen) AND (Milller Class 4) AND (Molar teeth) AND (Poor oral hygiene) AND (Pregnancy) AND (Smoking) AND (anticoagulant therapy) AND (non-compliant) AND (recession defects) AND (systemic steroid Past history over 2 weeks within the last 2 years) AND ((autoimmune disorders) OR (diabetes) OR (inflammatory disorders)) AND ((Allergy) OR (interlerance)) AND ((Plavix) OR (Warfarin)) AND ((diseases local) OR (systemic diseases)))"}
{"candidate_id": "LLM03760", "doc_id": "NCT02156999_exc", "case_bucket": "or", "source_criterion": "Kidney, parathyroid, congenital bone metabolic disease", "candidate_expression": "((disease) AND ((Kidney) OR (bone) OR (congenital) OR (metabolic) OR (parathyroid)))"}
{"candidate_id": "LLM03761", "doc_id": "NCT03373669_inc", "case_bucket": "other", "source_criterion": "Age =1 year, stratified into different age groups Living in the Waya Clinic Catchment Area Good health condition, without clinically significant medical history (by participant or guardian, in case of minor) Not pregnant for female subjects. Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening. Signed informed consent", "candidate_expression": "((=1 year) AND (Age) AND (Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening.) AND (Good health condition) AND (Living) AND (Not) AND (Signed informed consent) AND (Waya Clinic Catchment Area) AND (clinically significant) AND (female) AND (medical history) AND (pregnant) AND (without))"}
{"candidate_id": "LLM03762", "doc_id": "NCT01908465_inc", "case_bucket": "or", "source_criterion": "Irritable Bowel Syndrome (IBS) (ROME III criteria): subtype with diarrhea or mixed form age 18-65 years", "candidate_expression": "((Irritable Bowel Syndrome (IBS) ROME III criteria) AND (age 18-65 years) AND (diarrhea mixed form))"}
{"candidate_id": "LLM03763", "doc_id": "NCT02876484_inc", "case_bucket": "or", "source_criterion": "Uncomplicated RYGB performed minimum 3 months prior to the study. Fasting plasma glucose < 7,0 mM, HbA1c < 48 mmol/mol 3 months after RYGB", "candidate_expression": "((3 months after RYGB) AND (< 48 mmol/mol) AND (< 7,0 mM) AND (RYGB) AND (Uncomplicated) AND (minimum 3 months prior to the study) AND (the study) AND ((Fasting plasma glucose) OR (HbA1c)))"}
{"candidate_id": "LLM03764", "doc_id": "NCT00250640_inc", "case_bucket": "or", "source_criterion": "The treating physician has chosen Ventavis as a suitable long-term treatment for the patient Patient with primary pulmonary hypertension (i.e. Idiopathic Pulmonary Arterial Hypertension or Familial Pulmonary Arterial Hypertension) and classified as NYHA functional class III (NYHA = New York Heart Association) No prior treatment with Ventavis or other active treatments for primary pulmonary hypertension within 6 weeks of date of study inclusion (unless otherwise advised by Bayer Schering Pharma)", "candidate_expression": "((NYHA functional class III) AND (Ventavis long-term) AND (primary pulmonary hypertension) AND ((Familial Pulmonary Arterial Hypertension) OR (Idiopathic Pulmonary Arterial Hypertension)) AND ((treatment with Ventavis) OR (treatments for primary pulmonary hypertension)))"}
{"candidate_id": "LLM03765", "doc_id": "NCT02464865_inc", "case_bucket": "other", "source_criterion": "obese : weight for height > median + 3 standard deviations simple obesity", "candidate_expression": "((> median + 3 standard deviations) AND (obese) AND (simple obesity) AND (weight for height))"}
{"candidate_id": "LLM03766", "doc_id": "NCT01794793_inc", "case_bucket": "other", "source_criterion": "Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives Patient is currently benefiting from the treatment with pasireotide, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness", "candidate_expression": "((Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives) AND (Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures) AND (Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness))"}
{"candidate_id": "LLM03767", "doc_id": "NCT01669369_inc", "case_bucket": "or", "source_criterion": "histologically diagnosed primary classical osteosarcoma in extremities staging IIB MRI showing no skip lesion receive standard neo-adjuvant chemotherapy, adjuvant chemotherapy,and standard surgical treatment", "candidate_expression": "((MRI skip lesion staging IIB) AND (adjuvant chemotherapy) AND (classical osteosarcoma primary in extremities) AND (histologically) AND (standard neo-adjuvant chemotherapy) AND (standard surgical treatment))"}
{"candidate_id": "LLM03768", "doc_id": "NCT02742233_exc", "case_bucket": "or", "source_criterion": "Uncontrolled diabetes Ulcer infection Non-diabetic ulcers Orthopedic or neuromuscular pathologic conditions", "candidate_expression": "((Non-diabetic) AND (Orthopedic pathologic conditions) AND (Ulcer infection) AND (Uncontrolled) AND (diabetes) AND (neuromuscular pathologic conditions) AND (ulcers))"}
{"candidate_id": "LLM03769", "doc_id": "NCT02490839_inc", "case_bucket": "other", "source_criterion": "Participants having H. pylori related chronic gastritis with/without peptic ulcers who are aged greater than 20 years old and are willing to received eradication therapy.", "candidate_expression": "((aged greater than 20 years old) AND (chronic gastritis H. pylori related) AND (eradication therapy willing to received) AND (peptic ulcers))"}
{"candidate_id": "LLM03770", "doc_id": "NCT02299063_inc", "case_bucket": "other", "source_criterion": "aged between 3 - 36 months having primary corrective heart surgery", "candidate_expression": "((aged between 3 - 36 months) AND (corrective heart surgery primary))"}
{"candidate_id": "LLM03771", "doc_id": "NCT02443844_inc", "case_bucket": "other", "source_criterion": "Patients who have non muscle invasive bladder cancer male patients patients between 40-80 years old", "candidate_expression": "((male) AND (non muscle invasive bladder cancer) AND (old between 40-80 years))"}
{"candidate_id": "LLM03772", "doc_id": "NCT03619707_inc", "case_bucket": "or", "source_criterion": "Normal uterine cavity Normal Hormonal investigation: TSH,PRL,FBS Frozen embryo transfer cycles: at least 2 embryos Primary or secondary infertility: tubal occlusion, male factor, unexplained, endometriosis, ovarian factors… Body mass index (BMI) =18 to =30 kg/m2", "candidate_expression": "((=18 to =30 kg/m2) AND (BMI) AND (Body mass index) AND (FBS) AND (Frozen embryo transfer cycles) AND (Hormonal investigation) AND (Normal) AND (PRL) AND (TSH) AND (at least 2) AND (embryos) AND (uterine cavity) AND ((Primary infertility) OR (secondary infertility)) AND ((endometriosis) OR (male factor) OR (ovarian factors) OR (tubal occlusion) OR (unexplained factors)))"}
{"candidate_id": "LLM03773", "doc_id": "NCT03318874_inc", "case_bucket": "other", "source_criterion": "Meibomian Gland Dysfunction Eligible for heat treatment Ocular Surface Disease Index (OSDI) >12 Quality or expressibility score =20 years old: >1 or >20 years old: =1 Non-invasive tear film break-up time (NITBUT) <10 s in at least one eye Schirmer-1 test >5 mm after 5 min", "candidate_expression": "((<10 s) AND (>12) AND (>5 mm) AND (Eligible for) AND (Meibomian Gland Dysfunction) AND (Non-invasive tear film break-up time (NITBUT)) AND (OSDI) AND (Ocular Surface Disease Index) AND (Schirmer-1 test) AND (after 5 min) AND (at least one) AND (expressibility score) AND (eye) AND (heat treatment) AND (score Quality))"}
{"candidate_id": "LLM03774", "doc_id": "NCT00586898_exc", "case_bucket": "or", "source_criterion": "Clinically significant cardiac disease (New York Heart Association Class III/IV),or severe debilitating puhnonary disease. Uncontrolled serious active infection. Anticipated survival of less than 3 months. Active CNS or epiduraltumor Inability or unwillingness to comply with the treatment protocol, follow-up, or research tests.", "candidate_expression": "((Anticipated survival less than 3 months) AND (New York Heart Association Class III/IV) AND (cardiac disease significant) AND (debilitating puhnonary disease severe) AND (infection Uncontrolled serious) AND ((CNS tumor) OR (epiduraltumor)) AND ((Inability) OR (unwillingness)) AND ((comply with the treatment protocol) OR (follow-up) OR (research tests)))"}
{"candidate_id": "LLM03775", "doc_id": "NCT02844907_exc", "case_bucket": "or", "source_criterion": "Rheumatoid arthritis Diabetes or immediate family history of diabetes Coronary artery disease Congestive heart failure Pulmonary disorders, including COPD and asthma Malabsorptive GI disease, such as celiac disease, or gastric bypass Significant hepatic disease Renal insufficiency (eGFR < 60 mL/kg/min) Anemia (hematocrit < 34%) as measured at screening visit Pregnant females Consumption of daily medications that alter glucose metabolism of GI function (glucocorticoids, psychotropics, narcotics, metoclopramide) Consumption or injection of insulin Apparent sensitivity to any of the study peptides as determined by the skin test Diagnosis or h/o PTSD, depression, substance use, mental health problems, sleep disorders, HPA disruption and/or TBI", "candidate_expression": "((< 34%) AND (< 60 mL/kg/min) AND (Anemia) AND (COPD) AND (Congestive heart failure) AND (Coronary artery disease) AND (Diabetes) AND (HPA disruption) AND (Malabsorptive GI disease) AND (PTSD) AND (Pregnant) AND (Pulmonary disorders) AND (Renal insufficiency) AND (Rheumatoid arthritis) AND (Significant) AND (TBI) AND (asthma) AND (celiac disease) AND (daily) AND (depression) AND (diabetes) AND (eGFR) AND (females) AND (gastric bypass) AND (glucocorticoids) AND (hematocrit) AND (hepatic disease) AND (immediate family history) AND (injection) AND (insulin) AND (medications) AND (mental health problems) AND (metoclopramide) AND (narcotics) AND (psychotropics) AND (screening visit) AND (sensitivity) AND (skin test) AND (sleep disorders) AND (study peptides) AND (substance use) AND (that alter glucose metabolism of GI function))"}
```
