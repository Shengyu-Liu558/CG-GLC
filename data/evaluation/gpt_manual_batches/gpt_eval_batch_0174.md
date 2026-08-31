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
{"candidate_id": "LLM04326", "doc_id": "NCT02566928_exc", "case_bucket": "or", "source_criterion": "The patient is unwilling to provide informed consent acutely sick (for example, crying, wheezing, bleeding, screaming or shaken) unable to participate in a discussion about the study", "candidate_expression": "((The patient is unwilling to provide informed consent) AND (acutely sick) AND ((bleeding) OR (crying) OR (screaming) OR (shaken) OR (wheezing)))"}
{"candidate_id": "LLM04327", "doc_id": "NCT02743598_exc", "case_bucket": "or", "source_criterion": "Personal or family history of pancreatitis Medullary thyroid carcinoma (MTC) or Multiple Endocrine Neoplasia Syndrome Type 2 (MEN 2) Gastroparesis Allergy to liraglutide or any of the active ingredients in liraglutide or other GLP-1 analogue Weight loss drugs other than metformin Type 1 diabetes mellitus or diabetic ketoacidosis Known major cognitive deficit dementia, history of head trauma with loss of consciousness >30 min, history of stroke, current central nervous system (CNS) disorder such as seizures or opportunistic CNS infection Renal insufficiency defined as creatinine clearance < 60 mL/min Active opportunistic infections Pregnancy or breastfeeding Unstable cardiovascular disease with hospitalization within 1 year for acute coronary syndrome Decompensated heart failure Substance abuse Active alcohol or opioid substitution therapy Serious or unstable medical or psychological conditions that would compromise the subject's safety for successful participation", "candidate_expression": "((< 60 mL/min) AND (>30 min) AND (Active) AND (Allergy) AND (Decompensated heart failure) AND (Gastroparesis) AND (MEN 2) AND (MTC) AND (Pregnancy or breastfeeding) AND (Renal insufficiency) AND (Substance abuse) AND (Weight loss) AND (acute coronary syndrome) AND (cognitive deficit) AND (creatinine clearance) AND (hospitalization) AND (loss of consciousness) AND (metformin) AND (opportunistic infections) AND (other) AND (pancreatitis) AND (within 1 year) AND ((Type 1 diabetes mellitus) OR (diabetic ketoacidosis)) AND ((Medullary thyroid carcinoma) OR (Multiple Endocrine Neoplasia Syndrome Type 2)) AND ((central nervous system disorder) OR (dementia) OR (head trauma) OR (stroke)) AND ((opportunistic CNS infection) OR (seizures)) AND ((alcohol) OR (opioid substitution therapy)) AND ((GLP-1 analogue) OR (liraglutide)))"}
{"candidate_id": "LLM04328", "doc_id": "NCT03278548_inc", "case_bucket": "or", "source_criterion": "Patients undergoing elective abdominal surgery with an expected blood loss of = 500 ml ASA Physical Status II - III Signed written informed consent form Body weight = 140 kg Sepsis Burns Renal impairment (AKIN stage = 1) or acute and/or chronic renal replacement therapy Intracranial or cerebral haemorrhage Critically ill patients (typically admitted to the intensive care unit) Hyperhydration Pulmonary oedema Dehydration Hyperkalaemia Severe hypernatraemia Severe hyperchloraemia Severely impaired hepatic function Congestive heart failure Severe coagulopathy Organ transplant patients Metabolic alkalosis Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)", "candidate_expression": "((AKIN stage = 1) AND (ASA Physical Status II - III) AND (Body weight = 140 kg) AND (Burns) AND (Congestive heart failure) AND (Critically ill) AND (Dehydration) AND (Hyperhydration) AND (Hyperkalaemia) AND (Metabolic alkalosis) AND (Organ transplant) AND (Pulmonary oedema) AND (Sepsis) AND (Signed written informed consent form) AND (Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)) AND (abdominal surgery elective) AND (admitted typically) AND (coagulopathy Severe) AND (expected blood loss = 500 ml) AND (hyperchloraemia Severe) AND (hypernatraemia Severe) AND (impaired hepatic function Severely) AND (intensive care unit) AND ((Renal impairment) OR (renal replacement therapy)) AND ((acute) OR (chronic)) AND ((Intracranial haemorrhage) OR (cerebral haemorrhage)))"}
{"candidate_id": "LLM04329", "doc_id": "NCT00730301_inc", "case_bucket": "or", "source_criterion": "Patient diagnosed by HRCT Core Lab with eligible heterogeneous disease distribution and at least one complete oblique fissure. Age from 40 to 75 years BMI < 32 kg/m2 FEV1 < 40% of predicted value, FEV1/FVC < 70% TLC > 120% predicted, RV > 150% predicted. Stable with < 20 mg prednisone (or equivalent) qd PaCO2 < 50mm Hg PaO2 > 45 mm Hg on room air 6-min walk of > 50m (without rehabilitation) or > 100m (with rehabilitation) Nonsmoking for 4 months prior to initial interview and throughout screening The patient agrees to all protocol required follow-up intervals. The patient has no child bearing potential The patient is willing and able to complete protocol required baseline assessments and procedures", "candidate_expression": "((6-min walk) AND (< 20 mg qd) AND (< 32 kg/m2) AND (< 40% of predicted value) AND (< 50mm Hg) AND (< 70%) AND (> 100m) AND (> 120% predicted) AND (> 150% predicted) AND (> 45 mm Hg) AND (> 50m) AND (Age) AND (BMI) AND (FEV1) AND (FEV1/FVC) AND (HRCT Core Lab) AND (Nonsmoking) AND (PaCO2) AND (PaO2) AND (RV) AND (Stable) AND (TLC) AND (agrees to all protocol required follow-up intervals) AND (at least one) AND (baseline assessments) AND (baseline procedures) AND (child bearing potential) AND (complete oblique fissure) AND (follow-up intervals) AND (for 4 months prior to initial interview) AND (from 40 to 75 years) AND (heterogeneous disease distribution) AND (initial interview) AND (no) AND (on room air) AND (prednisone) AND (rehabilitation) AND (screening) AND (throughout screening) AND (willing and able to complete protocol) AND (without))"}
{"candidate_id": "LLM04330", "doc_id": "NCT00730301_exc", "case_bucket": "or", "source_criterion": "Prior endobronchial treatment for emphysema Pleural or interstitial disease that precludes surgery. Prior lung transplant, LVRS, median sternotomy, bullectomy or lobectomy. Clinically significant bronchiectasis Pulmonary nodule requiring surgery History of recurrent respiratory infections (> 3 hospitalization in the last year) Clinically significant (> 4 Tablespoons per day) sputum production Fever, elevated white cell count, or other evidence of active infection Dysrhythmia that might pose a risk during exercise or training Congestive heart failure within 6 mo and LVEF < 45% Evidence or history of Cor Pulmonale Resting bradycardia (< 50 beats/min), frequent multifocal PVCs, complex ventricular arrhythmia, sustained SVT History of exercise-related syncope MI within 6 mo and LVEF < 45% Evidence of systemic disease or neoplasia expected to compromise survival during 5-yr period Any disease or condition that interferes with completion of initial or follow-up assessments Patient is currently enrolled in another clinical trial Patient is unable to complete 3 minutes of unloaded peddling on cycle ergometer Alpha-1-Antitrypsin Deficiency", "candidate_expression": "((Alpha-1-Antitrypsin Deficiency) AND (Congestive heart failure within 6 mo) AND (Cor Pulmonale) AND (Dysrhythmia) AND (LVEF < 45%) AND (MI within 6 mo) AND (Pulmonary nodule) AND (bronchiectasis Clinically significant) AND (emphysema) AND (endobronchial treatment Prior) AND (enrolled in another clinical trial currently) AND (hospitalization > 3 in the last year) AND (pose a risk exercise training) AND (respiratory infections History recurrent) AND (sputum production Clinically significant > 4 Tablespoons per day) AND (surgery) AND (syncope History exercise-related) AND (unable to complete 3 minutes of unloaded peddling on cycle ergometer) AND NOT (surgery) AND ((LVRS) OR (bullectomy) OR (lobectomy) OR (lung transplant) OR (median sternotomy)) AND ((Fever) OR (active infection evidence) OR (white cell count elevated)) AND ((during exercise) OR (during training)) AND ((Pleural disease) OR (interstitial disease)) AND ((Evidence) OR (history)) AND ((Resting bradycardia < 50 beats/min) OR (complex ventricular arrhythmia) OR (multifocal PVCs frequent) OR (sustained SVT)) AND ((neoplasia) OR (systemic disease)) AND ((condition) OR (disease)))"}
{"candidate_id": "LLM04331", "doc_id": "NCT01391780_inc", "case_bucket": "or", "source_criterion": "presence of stress urinary or urgency incontinence", "candidate_expression": "((stress urinary incontinence) AND (urgency incontinence))"}
{"candidate_id": "LLM04332", "doc_id": "NCT02704234_inc", "case_bucket": "other", "source_criterion": "women previously diagnosed with generalized vulvodynia women previously diagnosed with localized vestibulodynia,", "candidate_expression": "((generalized vulvodynia) AND (localized vestibulodynia) AND (women))"}
{"candidate_id": "LLM04333", "doc_id": "NCT00730301_exc", "case_bucket": "or", "source_criterion": "Prior endobronchial treatment for emphysema Pleural or interstitial disease that precludes surgery. Prior lung transplant, LVRS, median sternotomy, bullectomy or lobectomy. Clinically significant bronchiectasis Pulmonary nodule requiring surgery History of recurrent respiratory infections (> 3 hospitalization in the last year) Clinically significant (> 4 Tablespoons per day) sputum production Fever, elevated white cell count, or other evidence of active infection Dysrhythmia that might pose a risk during exercise or training Congestive heart failure within 6 mo and LVEF < 45% Evidence or history of Cor Pulmonale Resting bradycardia (< 50 beats/min), frequent multifocal PVCs, complex ventricular arrhythmia, sustained SVT History of exercise-related syncope MI within 6 mo and LVEF < 45% Evidence of systemic disease or neoplasia expected to compromise survival during 5-yr period Any disease or condition that interferes with completion of initial or follow-up assessments Patient is currently enrolled in another clinical trial Patient is unable to complete 3 minutes of unloaded peddling on cycle ergometer Alpha-1-Antitrypsin Deficiency", "candidate_expression": "((3 minutes of unloaded peddling on cycle ergometer) AND (< 45%) AND (< 50 beats/min) AND (> 3 in the last year) AND (> 4 Tablespoons per day) AND (Alpha-1-Antitrypsin Deficiency) AND (Clinically significant) AND (Congestive heart failure) AND (Cor Pulmonale) AND (Dysrhythmia) AND (History) AND (LVEF) AND (MI) AND (Prior) AND (Pulmonary nodule) AND (bronchiectasis) AND (currently) AND (during 5-yr period) AND (elevated) AND (emphysema) AND (endobronchial treatment) AND (enrolled in another clinical trial) AND (evidence) AND (exercise) AND (exercise-related) AND (expected to compromise survival) AND (frequent) AND (hospitalization) AND (interferes with completion of initial or follow-up assessments) AND (pose a risk) AND (precludes) AND (precludes surgery) AND (recurrent) AND (respiratory infections) AND (sputum production) AND (surgery) AND (syncope) AND (training) AND (unable to complete) AND (within 6 mo) AND ((LVRS) OR (bullectomy) OR (lobectomy) OR (lung transplant) OR (median sternotomy)) AND ((Fever) OR (active infection) OR (white cell count)) AND ((during exercise) OR (during training)) AND ((Pleural disease) OR (interstitial disease)) AND ((Evidence) OR (history)) AND ((Resting bradycardia) OR (complex ventricular arrhythmia) OR (multifocal PVCs) OR (sustained SVT)) AND ((neoplasia) OR (systemic disease)) AND ((condition) OR (disease)))"}
{"candidate_id": "LLM04334", "doc_id": "NCT03122119_exc", "case_bucket": "or", "source_criterion": "Patients under the age of 18 (Subjects under the age of 18 will not be included in this study due to the continued growth and development of their joints and unstudied effects on children.) Over the age of 80 Multiple pain sources and multifactorial pain sources that complicated or confound diagnosing the SI joint as the primary and predominant pain generator that may contribute to low back pain (including but not limited to: lumbar diagnosis, lumbar radiculopathy, intra or extra-articular hip pathology to include acetabulum and femoral head, lumbo-sacral joint pathology, intervertebral disk disease, spondylolisthesis/spondylosis/spondylolysis of lumbar vertebra) Immunosuppressed/immune compromised Underlying comorbidities that contraindicate the procedure (including but not limited to polycythemia, coagulation disorder, or malignancy).", "candidate_expression": "((Underlying comorbidities contraindicate the procedure) AND (age 18 under) AND (age Over 80) AND (contraindicate) AND (lumbo-sacral joint pathology) AND (procedure) AND ((extra-articular hip pathology) OR (intra -articular hip pathology)) AND ((acetabulum pathology) OR (femoral head pathology) OR (intervertebral disk disease) OR (spondylolisthesis) OR (spondylolysis of lumbar vertebra) OR (spondylosis)) AND ((Immunosuppressed) OR (immune compromised)) AND ((coagulation disorder) OR (malignancy) OR (polycythemia)) AND ((Multiple pain sources) OR (multifactorial pain sources)) AND ((lumbar diagnosis) OR (lumbar radiculopathy)))"}
{"candidate_id": "LLM04335", "doc_id": "NCT03226080_exc", "case_bucket": "or", "source_criterion": "Inability to consent/refusal Allergy to any of the study medications Multiple traumatic injuries Contraindication to neuraxial or general anesthesia Pregnancy", "candidate_expression": "((Allergy) AND (Contraindication) AND (Multiple traumatic injuries) AND (Pregnancy) AND (study medications) AND ((Inability to consent) OR (refusal)) AND ((general anesthesia) OR (neuraxial anesthesia)))"}
{"candidate_id": "LLM04336", "doc_id": "NCT02546856_exc", "case_bucket": "or", "source_criterion": "Contraindications for BB. Living in a nursing home. Life expectancy < 6 months. Unable to self-care or mental disease without caregiver. Unable to weight Without phone Unable to go to clinic visit.", "candidate_expression": "((BB) AND (Contraindications) AND (Life expectancy < 6 months) AND (Living) AND (Unable) AND (Unable to self-care) AND (go to clinic visit Unable) AND (mental disease without caregiver) AND (nursing home) AND (weight) AND NOT (phone))"}
{"candidate_id": "LLM04337", "doc_id": "NCT01709981_inc", "case_bucket": "other", "source_criterion": "Patients must be more than 18 years of age and referred for coronary angiography", "candidate_expression": "((age) AND (coronary angiography) AND (more than 18 years) AND (referred for))"}
{"candidate_id": "LLM04338", "doc_id": "NCT02589691_exc", "case_bucket": "or", "source_criterion": "contra-indication to inhalational induction (full stomach) contra-indication to the use of rocuronium American Society of Anesthesiologists score (ASA) III or IV intracranial surgery parental refusal absence of affiliation to social security", "candidate_expression": "((American Society of Anesthesiologists score (ASA)) AND (III) AND (IV) AND (absence) AND (affiliation to social security) AND (contra-indication) AND (full stomach) AND (inhalational induction) AND (intracranial surgery) AND (parental refusal) AND (rocuronium))"}
{"candidate_id": "LLM04339", "doc_id": "NCT02478515_inc", "case_bucket": "other", "source_criterion": "Signed informed consent form Macula edema secondary to BRVO BCVA of 77 to 20 letters assessed with the use of ETDRS charts CRT <U+2267>250µm", "candidate_expression": "((250µm) AND (77 to 20 letters) AND (BCVA) AND (BRVO) AND (CRT) AND (Macula edema) AND (Signed informed consent form))"}
{"candidate_id": "LLM04340", "doc_id": "NCT03115151_inc", "case_bucket": "other", "source_criterion": "Adult subjects aged 18 years or older Scheduled for elective posterior lumbar spinal fusion surgery between 1 and 3 levels", "candidate_expression": "((Adult) AND (aged 18 years or older) AND (posterior lumbar spinal fusion surgery Scheduled for elective between 1 and 3 levels))"}
{"candidate_id": "LLM04341", "doc_id": "NCT02318446_exc", "case_bucket": "or", "source_criterion": "Pregnancy and lactation Patients with diabetes, Ischemic heart disease (IHD), stroke, malignancy and psychiatric diseases are excluded from study. The patients receiving vitamin supplements or who had clinical evidence for an acute illness, renal dysfunction, thyroid dysfunction, chronic inflammatory diseases, inborn errors of homocysteine, cobalamin or folate metabolism, or any other condition known to interfere with homocysteine metabolism will be excluded Patients who are already involved in any other trial. Patients not willing to fill consent/ assent form are also excluded from study.", "candidate_expression": "((Patients not willing to fill consent/ assent form are also excluded from study.) AND (acute illness) AND ((Pregnancy) OR (lactation)) AND ((chronic inflammatory diseases) OR (clinical evidence for an acute illness) OR (renal dysfunction) OR (thyroid dysfunction) OR (vitamin supplements)) AND ((condition known to interfere with homocysteine metabolism) OR (inborn errors of cobalamin metabolism) OR (inborn errors of folate metabolism) OR (inborn errors of homocysteine metabolism)) AND ((Ischemic heart disease (IHD)) OR (diabetes) OR (malignancy) OR (psychiatric diseases) OR (stroke)))"}
{"candidate_id": "LLM04342", "doc_id": "NCT02620904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04343", "doc_id": "NCT02997215_exc", "case_bucket": "or", "source_criterion": "Open surgery; Patients allergic to lidocaine or other local anesthetics; Drug abuser.", "candidate_expression": "((Drug abuser) AND (Open surgery) AND (allergic) AND (lidocaine) AND (local anesthetics other))"}
{"candidate_id": "LLM04344", "doc_id": "NCT02364648_inc", "case_bucket": "other", "source_criterion": "Stage 3 - 5 Chronic Kidney Disease", "candidate_expression": "((3 - 5) AND (Chronic Kidney Disease) AND (Stage))"}
{"candidate_id": "LLM04345", "doc_id": "NCT03228498_exc", "case_bucket": "or", "source_criterion": "1. Absence of objectionable cognitive impairment or presence of dementia of severe degree defined by CDR score > 2.0. 2. Unavailability of brain MRI (in case of absolute contraindications, the use of cranial CT is allowed). 3. Expected poor compliance with the study protocol. 4. Past diagnosis of major depression, schizophrenia, major anxiety syndrome, or manic- depressive illness. 5. Diagnosis of degenerative cognitive impairment based on clinical and/or neuroradiological findings (i.e., patients with prevailing memory impairment, or with medial temporal atrophy on brain MRI in absence of evident vascular abnormalities; i.e., Alzheimer disease as defined using the National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria, Parkinson disease, Huntington disease, frontotemporal dementia). 6. Diagnosis of cognitive impairment from other causes (i.e., vitamine B12 and folic acid deficiency, thyroid disorders, metabolic diseases, head trauma, tumor or infections of the central nervous system, normal pressure hydrocephalus). 7. Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status. 8. Clinically relevant cardiac or pulmonary insufficiency. 9. Relevant electrocardiograph abnormalities; bradycardia (50 bpm) or tachycardia (120 bpm) under resting conditions. 10. Myocardial infarction within the past 6 months. 11. Stroke still requiring neurological rehabilitation. 12. Severe/untreated blood pressure (systolic 180 mm Hg, diastolic 95 mm Hg). 13. Clinically relevant liver function impairment. 14. Insulin-dependent diabetes mellitus. 15. Idiopathic epilepsy and anti-epileptic treatment. 16. Severe anemia (Hb <10 mg/dL). 17. Severe gastrointestinal disease. 18. Cancer. 19. Known intolerance to study drugs. 20. Coexistent serious illnesses that would imply a drop-out before the end of the trial.", "candidate_expression": "((120 bpm) AND (180 mm Hg) AND (50 bpm) AND (95 mm Hg) AND (<10 mg/dL) AND (> 2.0) AND (Absence) AND (Alzheimer disease) AND (CDR score) AND (Cancer) AND (Clinically relevant) AND (Hb) AND (Huntington disease) AND (Idiopathic epilepsy) AND (Insulin-dependent diabetes mellitus) AND (Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status.) AND (Myocardial infarction) AND (National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria) AND (Parkinson disease) AND (Past diagnosis) AND (Relevant) AND (Severe) AND (Stroke) AND (Unavailability) AND (abnormalities) AND (absence) AND (absolute contraindications) AND (anemia) AND (anti-epileptic treatment) AND (blood pressure) AND (bradycardia) AND (brain MRI) AND (cardiac insufficiency) AND (clinical and/or neuroradiological findings) AND (cognitive impairment) AND (cranial CT) AND (degenerative cognitive impairment) AND (dementia) AND (diastolic) AND (electrocardiograph) AND (evident) AND (folic acid deficiency) AND (frontotemporal dementia) AND (gastrointestinal disease) AND (head trauma) AND (infections of the central nervous system) AND (intolerance) AND (liver function impairment) AND (major anxiety syndrome) AND (major depression) AND (manic- depressive illness) AND (medial temporal atrophy) AND (memory impairment) AND (metabolic diseases) AND (neurological rehabilitation) AND (normal pressure hydrocephalus) AND (objectionable) AND (other causes) AND (pulmonary insufficiency) AND (requiring) AND (schizophrenia) AND (severe degree) AND (study drugs) AND (systolic) AND (tachycardia) AND (thyroid disorders) AND (tumor of the central nervous system) AND (under resting conditions) AND (untreated) AND (vascular abnormalities) AND (vitamine B12 deficiency) AND (within the past 6 months))"}
{"candidate_id": "LLM04346", "doc_id": "NCT02946892_inc", "case_bucket": "or", "source_criterion": "Informed consent of parent(s) or legal guardian; informed consent or assent of subject as applicable. Male or female children between the ages of 10 and 35 years with congenital heart disease that has been palliated with a Fontan circulation. Ability of perform a maximal exercise test as defined by a respiratory exchange ratio (RER) greater than 1.0 at the time of maximal exercise", "candidate_expression": "((Ability of perform) AND (Fontan circulation) AND (ages between 10 and 35 years) AND (children) AND (congenital heart disease) AND (maximal exercise test) AND (respiratory exchange ratio (RER) greater than 1.0 at the time of maximal exercise) AND ((Informed consent of legal guardian) OR (Informed consent of parent) OR (informed assent of subject) OR (informed consent of subject)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04347", "doc_id": "NCT02396420_exc", "case_bucket": "or", "source_criterion": "History of prostate, bladder, or rectal cancer History of transurethral resection of the prostate (TURP), open prostate surgery, or radiofrequency or microwave therapies History of open bladder, rectosigmoid colon, or other pelvic surgery Patient is unwilling to discontinue alpha blockers 1 month after study treatment Patient is unwilling to discontinue 5-alph reductase inhibitors 1 month after study treatment Neurogenic bladder or other neurologic disorder impacting bladder function such as Parkinson's disease, multiple sclerosis, cerebral vascular accident or diabetes Any other confounding bladder or urethral pathology, including urethral stricture, bladder neck contracture, or bladder atonia Active prostatitis or urinary tract infection Cystolithiasis within the past 3 months Serum creatinine > 1.7mg/dL Inability to discontinue oral anticoagulant 2-5 days prior to study treatment Coagulation disturbances not normalized by medical treatment Iodinated contrast allergy that, in the opinion of the Investigator, cannot be adequately premedicated Gelatin allergy Known severe peripheral vascular disease or major iliac arterial occlusive disease Interest in future fertility Clinically significant cardiac arrhythmia or other cardiac disease (including congestive heart failure), uncontrolled diabetes mellitus, clinically significant respiratory disease, or known immunosuppression Other condition that the Investigator believes puts the patient at risk for a complication during the procedure", "candidate_expression": "((1 month after study treatment) AND (2-5 days prior to study treatment) AND (5-alph reductase inhibitors) AND (> 1.7mg/dL) AND (Active) AND (Coagulation disturbances) AND (Cystolithiasis) AND (Gelatin) AND (Interest in future fertility) AND (Iodinated contrast) AND (Other condition that the Investigator believes puts the patient at risk for a complication during the procedure) AND (Serum creatinine) AND (allergy) AND (alpha blockers) AND (clinically significant) AND (congestive heart failure) AND (major) AND (medical treatment) AND (neurologic disorder impacting bladder function) AND (normalized) AND (not) AND (open bladder surgery) AND (oral anticoagulant) AND (pelvic surgery) AND (rectosigmoid colon surgery) AND (severe) AND (study treatment) AND (uncontrolled) AND (within the past 3 months) AND ((Neurogenic bladder) OR (Parkinson's disease) OR (cerebral vascular accident) OR (diabetes) OR (multiple sclerosis)) AND ((bladder cancer) OR (prostate cancer) OR (rectal cancer)) AND ((bladder atonia) OR (bladder neck contracture) OR (urethral stricture)) AND ((bladder pathology) OR (urethral pathology)) AND ((prostatitis) OR (urinary tract infection)) AND ((iliac arterial occlusive disease) OR (peripheral vascular disease)) AND ((cardiac arrhythmia) OR (cardiac disease) OR (diabetes mellitus) OR (immunosuppression) OR (respiratory disease)) AND ((microwave therapies) OR (open prostate surgery) OR (radiofrequency) OR (transurethral resection of the prostate (TURP))))"}
{"candidate_id": "LLM04348", "doc_id": "NCT02762851_inc", "case_bucket": "other", "source_criterion": "Age = 18 years and NYHA (New York Heart Association) functional class II, III and IV", "candidate_expression": "((Age = 18 years) AND (NYHA (New York Heart Association) functional class II, III and IV))"}
{"candidate_id": "LLM04349", "doc_id": "NCT00379366_exc", "case_bucket": "other", "source_criterion": "contra-indications of radiotherapy angioplasty with stenting", "candidate_expression": "((angioplasty with stenting) AND (contra-indications) AND (radiotherapy))"}
{"candidate_id": "LLM04350", "doc_id": "NCT02464813_exc", "case_bucket": "or", "source_criterion": "Other spinal pathology or other associated medical condition Major neurologic developmental delay Need for anterior surgery or for vertebral column resection. Preoperative opioid use Inability to use PCA", "candidate_expression": "((Inability to use) AND (Major neurologic developmental delay) AND (Need for) AND (PCA) AND (Preoperative) AND (anterior surgery) AND (associated medical condition) AND (opioid) AND (spinal pathology) AND (vertebral column resection))"}
```
