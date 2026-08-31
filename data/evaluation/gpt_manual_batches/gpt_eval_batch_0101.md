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
{"candidate_id": "LLM02501", "doc_id": "NCT02637076_inc", "case_bucket": "or", "source_criterion": "current diagnosis of narcolepsy with cataplexy OR healthy control", "candidate_expression": "((cataplexy) AND ((healthy) OR (narcolepsy)))"}
{"candidate_id": "LLM02502", "doc_id": "NCT02992028_exc", "case_bucket": "or", "source_criterion": "age <45 or >80 allergies to medications used in the study history of renal diseases, a coagulation abnormality, a hepatic disease, or drug abuse definite radiographic evidence of osteoarthritis of the glenohumeral joint inflammatory arthritis including rheumatoid arthritis a history of acute trauma systemic conditions associated with chronic pain a history of infection an inability to understand the questionnaires", "candidate_expression": "((acute trauma) AND (age <45 or >80) AND (allergies) AND (chronic pain) AND (coagulation abnormality) AND (drug abuse) AND (hepatic disease) AND (history) AND (inability to understand the questionnaires) AND (infection history) AND (inflammatory arthritis) AND (medications used in the study) AND (osteoarthritis radiographic evidence glenohumeral joint) AND (radiographic) AND (renal diseases) AND (rheumatoid arthritis) AND (systemic conditions associated with chronic pain))"}
{"candidate_id": "LLM02503", "doc_id": "NCT02689089_exc", "case_bucket": "or", "source_criterion": "Suspected or confirmed active TB disease Known allergies to any of the study medications by participant self-report have a positive pregnancy test at screening, or are not willing to use a reliable method of barrier contraception during the study, or are breastfeeding hormonal contraception HIV infected participants who are on anti-retroviral drugs other drugs that interact with 3HP (see Table 1) Known contact with an INH or rifampin resistant case Weight < 10 kg Evidence of possible liver damage defined by an aspartate transaminase (AST) level that is more than 3x the upper limit of normal in an asymptomatic patient Porphyria reported by patient Inability to adhere to protocol. Patients may be excluded from the study for other reasons, at the investigator's discretion with detailed documentation.", "candidate_expression": "((< 10 kg) AND (AST) AND (HIV infected) AND (INH) AND (Inability to adhere to protocol) AND (Porphyria) AND (Weight) AND (active TB) AND (allergies) AND (anti-retroviral drugs) AND (are breastfeeding) AND (are not willing to use a reliable method of barrier contraception during the study) AND (aspartate transaminase) AND (have a positive pregnancy test at screening) AND (hormonal contraception) AND (liver damage) AND (more than 3x the upper limit of normal) AND (resistant) AND (rifampin))"}
{"candidate_id": "LLM02504", "doc_id": "NCT01501201_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetes mellitus with HbA1c > 7.5 % Body mass index > 35 and < 50 kg/m2 Candidate for Gastric By-Pass Treatment with GLP1 (glucagon-like peptide) analogue or insulin", "candidate_expression": "((> 35 and < 50 kg/m2) AND (> 7.5 %) AND (Body mass index) AND (Candidate) AND (GLP1 (glucagon-like peptide) analogue) AND (Gastric By-Pass) AND (HbA1c) AND (Treatment) AND (Type 2 diabetes mellitus) AND (insulin))"}
{"candidate_id": "LLM02505", "doc_id": "NCT02851303_inc", "case_bucket": "or", "source_criterion": "Born at University of New Mexico Hospital Greater than 34 weeks gestation Primary in-utero drug exposure was opioids other than buprenorphine Maternal or infant urine drug screen positive for methadone and/or opioids on admission", "candidate_expression": "((Born) AND (Greater than 34 weeks) AND (University of New Mexico Hospital) AND (buprenorphine) AND (drug exposure) AND (gestation) AND (in-utero) AND (opioids) AND (other) AND (positive) AND (urine drug screen) AND ((Maternal) OR (infant)) AND ((methadone) OR (opioids)))"}
{"candidate_id": "LLM02506", "doc_id": "NCT01349413_inc", "case_bucket": "other", "source_criterion": "Patients with functional dyspepsia that fulfill Rome III criteria with inadequate relief of dyspeptic symptoms Age >18 Provision of written consent", "candidate_expression": "((Age >18) AND (Provision of written consent) AND (dyspeptic symptoms inadequate relief) AND (functional dyspepsia Rome III criteria))"}
{"candidate_id": "LLM02507", "doc_id": "NCT02607163_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02508", "doc_id": "NCT00461136_exc", "case_bucket": "or", "source_criterion": "Severe Hypertension Grade 3 WHO classification (Mean Sitting Diastolic Blood Pressure (MSDBP) 110 mmHg and/or Mean Sitting Systolic Blood Pressure MSSBP 180 mmHg) Acetylsalicyclic acid (ASA) treatment >1g/day or regular use of Non steroidal anti-inflammatory drug (NSAIDs) Kidney disease not caused by diabetes or hypertension Serum potassium < 3.5 or > 5.1 mEq/L GFR < 40 ml/min/1.73m2 as measured by the MDRD formula Serum albumin < 2.0mg/dL History of hypertensive encephalopathy or cerebrovascular accident at any time prior to Visit1. Current diagnosis of heart failure (New York Heart Association (NYHA) Class II-IV) History of myocardial infarction, unstable angina pectoris, coronary bypass surgery, or any percutaneous coronary intervention (PCI) during the 6 months prior to Visit 1 Second or third degree heart block without a pacemaker Concurrent potentially life threatening arrhythmia or symptomatic arrhythmia Clinically significant valvular heart disease Type 1 diabetes mellitus Uncontrolled Type II diabetes mellitus (Hemaglobin subtype A1C (HbA1C) >11 %) History of malignancy including leukemia and lymphoma (but not basal cell skin carcinoma) within the past five years Participation in any clinical investigation within 4 weeks prior to dosing or longer if required by local regulation. Donation or loss of 400 mL or more of blood within 8 weeks prior to dosing. Significant illness within the two weeks prior to dosing. Any surgical or medical condition which might significantly alter the absorption, distribution, metabolism, or excretion of study drugs including, but not limited to, any of the following: History of major gastrointestinal tract surgery such as gastrectomy, gastroenterostomy, or bowel resection -Currently active or previously active inflammatory bowel disease during the 12 months prior to Visit 1 Currently active gastritis, duodenal or gastric ulcers, or gastrointestinal/rectal bleeding during the 3 months prior to Visit 1. Any history of pancreatic injury, pancreatitis or evidence of impaired pancreatic function/injury as indicated by abnormal lipase or amylase Evidence of hepatic disease, a history of hepatic encephalopathy, a history of esophageal varices, or a history of portocaval shunt Current treatment with cholestyramine or cholestipol resins History of immunocompromise, including a positive HIV test result. History of a positive Hepatitis B surface antigen (HBsAg) or Hepatitis C test result. History of drug or alcohol abuse within the 12 months prior to dosing. Persons directly involved in the execution of this protocol. Any condition that in the opinion of the investigator or the Novartis medical monitor would jeopardize the evaluation of efficacy or safety History of noncompliance to medical regimens or unwillingness to comply with the study protocol Known or suspected contraindications to the study medications, including history of allergy to Angiotensin converting enzyme (ACE) inhibitors and/or to thiazide diuretics or other sulfonamide derived drug Any surgical or medical condition, which in the opinion of the investigator, may place the patient at higher risk from his/her participation in the study, or is likely to prevent the patient from complying with the requirements of the study or completing the study Use of any prescription drug or over-the-counter (OTC) medication which is prohibited by the protocol. Patients who previously participated in any Aliskiren study. Pregnant or nursing woman. Other protocol-defined inclusion/exclusion criteria may apply", "candidate_expression": "((110 mmHg) AND (180 mmHg) AND (3) AND (400 mL or more) AND (< 2.0mg/dL) AND (< 40 ml/min/1.73m2) AND (>11 %) AND (>1g/day) AND (Aliskiren) AND (Aliskiren study) AND (Current) AND (Currently active) AND (GFR) AND (Grade WHO classification) AND (Hemaglobin subtype A1C (HbA1C)) AND (History) AND (History of) AND (II-IV) AND (MDRD formula) AND (New York Heart Association (NYHA) Class) AND (Other) AND (Serum albumin) AND (Serum potassium) AND (Severe Hypertension) AND (Significant illness) AND (Type 1 diabetes mellitus) AND (Type II diabetes mellitus) AND (Uncontrolled) AND (abnormal) AND (allergy) AND (alter the absorption, distribution, metabolism, or excretion of study drugs) AND (any clinical investigation) AND (any time prior) AND (basal cell skin carcinoma) AND (complying with the requirements of the study) AND (condition) AND (contraindications) AND (dosing) AND (duodenal) AND (during the 12 months prior) AND (during the 3 months prior) AND (during the 6 months prior) AND (esophageal varices) AND (gastric ulcers) AND (gastritis) AND (heart failure) AND (hepatic encephalopathy) AND (history of) AND (impaired) AND (inflammatory bowel disease) AND (likely to prevent the patient from) AND (major gastrointestinal tract surgery) AND (malignancy) AND (other) AND (pacemaker) AND (place the patient at higher risk from his/her participation in the study) AND (portocaval shunt) AND (positive) AND (potentially life threatening) AND (prevent) AND (previously) AND (prohibited by the protocol) AND (protocol-defined) AND (study medications) AND (symptomatic) AND (unwillingness to) AND (valvular heart disease) AND (within 4 weeks prior to dosing) AND (within 8 weeks prior) AND (within the 12 months prior) AND (within the past five years) AND (within the two weeks prior) AND (without) AND (woman) AND ((cholestipol resins) OR (cholestyramine)) AND ((HIV test) OR (immunocompromise)) AND ((Hepatitis B surface antigen (HBsAg) test) OR (Hepatitis C test)) AND ((Kidney disease) OR (diabetes) OR (hypertension)) AND ((alcohol abuse) OR (drug abuse)) AND ((Angiotensin converting enzyme (ACE) inhibitors) OR (sulfonamide derived drug) OR (thiazide diuretics)) AND ((Pregnant) OR (nursing)) AND ((that would jeopardize safety) OR (that would jeopardize the evaluation of efficacy)) AND ((comply with the study protocol) OR (noncompliance to medical regimens)) AND ((over-the-counter (OTC) medication) OR (prescription drug)) AND ((< 3.5) OR (> 5.1 mEq/L)) AND ((cerebrovascular accident) OR (hypertensive encephalopathy)) AND ((coronary bypass surgery) OR (myocardial infarction) OR (percutaneous coronary intervention (PCI)) OR (unstable angina pectoris)) AND ((Mean Sitting Diastolic Blood Pressure (MSDBP)) OR (Mean Sitting Systolic Blood Pressure MSSBP)) AND ((Second degree heart block) OR (third degree heart block)) AND ((arrhythmia)) AND ((leukemia) OR (lymphoma)) AND ((Donation of blood) OR (loss of blood)) AND ((medical condition) OR (surgical condition)) AND ((bowel resection) OR (gastrectomy) OR (gastroenterostomy)) AND ((Currently active) OR (previously active)) AND ((gastrointestinal bleeding) OR (rectal bleeding)) AND ((Acetylsalicyclic acid (ASA) treatment) OR (Non steroidal anti-inflammatory drug (NSAIDs))) AND ((pancreatic function) OR (pancreatic injury) OR (pancreatitis)) AND ((amylase) OR (lipase)) AND ((hepatic disease) OR (history)))"}
{"candidate_id": "LLM02509", "doc_id": "NCT03012984_exc", "case_bucket": "or", "source_criterion": "Preoperative history of schizophrenia, epilepsy, parkinsonism or myasthenia gravis; Preoperative radio- or chemotherapy; Inability to communicate in the preoperative period because of coma, profound dementia or language barrier; Preoperative obstructive sleep apnea (previously diagnosed as obstructive sleep apnea, or a STOP-Bang score >= 3); Brain trauma or neurosurgery; Preoperative left ventricular ejection fraction < 30%, sick sinus syndrome, severe sinus bradycardia (< 50 beats per minute), or second-degree or above atrioventricular block without pacemaker; Severe hepatic dysfunction (Child-Pugh class C) or severe renal dysfunction (requirement of renal replacement therapy before surgery); ASA classification >= IV.", "candidate_expression": "((ASA classification >= IV) AND (Child-Pugh class C) AND (Inability to communicate preoperative period) AND (hepatic dysfunction Severe) AND (obstructive sleep apnea Preoperative) AND (renal dysfunction severe) AND (renal replacement therapy before surgery) AND (surgery) AND NOT (pacemaker) AND ((coma) OR (dementia profound) OR (language barrier)) AND ((epilepsy) OR (myasthenia gravis) OR (parkinsonism) OR (schizophrenia)) AND ((STOP-Bang score >= 3) OR (obstructive sleep apnea)) AND ((Brain trauma) OR (neurosurgery)) AND ((atrioventricular block second-degree or above) OR (left ventricular ejection fraction Preoperative < 30%) OR (sick sinus syndrome) OR (sinus bradycardia severe < 50 beats per minute)) AND ((chemotherapy) OR (therapy radio)))"}
{"candidate_id": "LLM02510", "doc_id": "NCT02713087_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for supine-positioned elective craniotomy for supratentorial malignant and non-malignant brain tumors 3 cm or larger (measured as the largest diameter in any plane on MR images) ASA (American Society of Anesthesiologist) status 1-3 (27) Written informed consent from participating patients", "candidate_expression": "((ASA status 1-3 27) AND (American Society of Anesthesiologist status) AND (MR) AND (Written informed consent from participating patients) AND (brain tumors supratentorial 3 cm or larger largest diameter in any plane) AND (supine-positioned elective craniotomy scheduled) AND ((malignant) OR NOT (malignant)))"}
{"candidate_id": "LLM02511", "doc_id": "NCT03082573_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02512", "doc_id": "NCT02590822_exc", "case_bucket": "or", "source_criterion": "• Diabetes duration >12 years Currently taking more than three glucose lowering therapies Weight-loss of >5kg in the preceding 6 months Stage 4 or 5 chronic kidney disease (eGFR< 30ml/min/1.73m2), Current therapy with Insulin, thiazolidinediones, steroids or atypical antipsychotic medication Untreated thyroid disease Known macrovascular disease including coronary artery disease, stroke/TIA or peripheral vascular disease Presence of arrhythmia (including atrial fibrillation, atrial flutter, or 2nd or 3rd degree atrioventricular block) Known heart failure Other clinically relevant heart disease Inability to exercise or undertake a MRP Absolute contraindication to CMR Cardiovascular symptoms (angina, limiting dyspnoea during normal physical activity) Inflammatory condition e.g. Connective tissue disorder, Rheumatoid arthritis", "candidate_expression": "((2nd degree atrioventricular block) AND (3rd degree atrioventricular block) AND (< 30ml/min/1.73m2) AND (>12 years) AND (>5kg) AND (CMR) AND (Cardiovascular symptoms) AND (Connective tissue disorder,) AND (Diabetes) AND (Inability) AND (Inflammatory) AND (Insulin) AND (MRP) AND (Rheumatoid arthritis) AND (Stage 4 or 5) AND (TIA) AND (Untreated) AND (Weight-loss) AND (angina) AND (arrhythmia) AND (atrial fibrillation) AND (atrial flutter) AND (atypical antipsychotic medication) AND (chronic kidney disease) AND (contraindication) AND (coronary artery disease) AND (dyspnoea) AND (eGFR) AND (exercise) AND (glucose lowering therapies) AND (heart disease) AND (heart failure) AND (macrovascular disease) AND (more than three) AND (peripheral vascular disease) AND (preceding 6 months) AND (steroids) AND (stroke) AND (thiazolidinediones) AND (thyroid disease))"}
{"candidate_id": "LLM02513", "doc_id": "NCT02432404_exc", "case_bucket": "or", "source_criterion": "Current pregnancy Desire/intent to become pregnant over the course of the study Women who are less than 6 weeks postpartum Contraindications to hormonal contraceptive use per package insert, including history of deep vein thrombosis, smoking in women older than 35 years Current IUD Unable to comprehend consent material because of language barrier or psychological difficulty", "candidate_expression": "((Contraindications to hormonal contraceptive) AND (Desire/intent to become pregnant over the course of the study) AND (IUD) AND (Unable to comprehend consent material because of language barrier or psychological difficulty) AND (Women less than 6 weeks postpartum) AND (hormonal contraceptive) AND (pregnancy) AND (pregnant) AND ((deep vein thrombosis) OR (women smoking older than 35 years)))"}
{"candidate_id": "LLM02514", "doc_id": "NCT03373669_inc", "case_bucket": "other", "source_criterion": "Age =1 year, stratified into different age groups Living in the Waya Clinic Catchment Area Good health condition, without clinically significant medical history (by participant or guardian, in case of minor) Not pregnant for female subjects. Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening. Signed informed consent", "candidate_expression": "((Age =1 year) AND (Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening.) AND (Good health condition) AND (Living) AND (Signed informed consent) AND (Waya Clinic Catchment Area) AND (female) AND NOT (pregnant) AND NOT (medical history clinically significant))"}
{"candidate_id": "LLM02515", "doc_id": "NCT02580630_inc", "case_bucket": "or", "source_criterion": "Midsubstance pain in the achilles tendon Symptoms for at least 3 months Ultrasound scanning at the first visit shows thickness of the achilles tendon above 7 mm or 20% thicker than the contralateral. Patient can read and understand danish", "candidate_expression": "((Midsubstance pain) AND (Symptoms) AND (Ultrasound scanning) AND (achilles tendon) AND (at the first visit) AND (for at least 3 months) AND (thickness of the achilles tendon) AND ((20% thicker than the contralateral) OR (above 7 mm)))"}
{"candidate_id": "LLM02516", "doc_id": "NCT02456532_exc", "case_bucket": "or", "source_criterion": "acute or unstable medical disease, current or past history of psychiatric disease, alcoholism or drug abuse, and other primary sleep disorders", "candidate_expression": "((alcoholism) AND (drug abuse) AND (medical disease acute unstable) AND (primary sleep disorders) AND (psychiatric disease))"}
{"candidate_id": "LLM02517", "doc_id": "NCT02270970_inc", "case_bucket": "or", "source_criterion": "Patients who meet 1987 ACR criteria for SLE with 1996 modifications SLEDAI >/= 6 at screening visit Positive ANA OR anti-dsDNA within one year of screening In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease", "candidate_expression": "((1987 ACR criteria with 1996 modifications) AND (>/= 6) AND (ANA) AND (In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease) AND (Positive) AND (SLE) AND (SLEDAI) AND (anti-dsDNA) AND (at screening visit) AND (screening) AND (screening visit) AND (within one year of screening))"}
{"candidate_id": "LLM02518", "doc_id": "NCT02637453_exc", "case_bucket": "or", "source_criterion": "With acute diseases, such as acute phase after myocardial infarction (within 3 months), within 3 months after acute heart failure or new cerebral infarction; In the list of heart transplantation; Expected survival less than 1 year; With other hemorrhagic diseases and anticoagulant therapy is not allowed; Thrombosis in left atrium; Heart failure, New York Heart Association(NYHA) III/IV or eject fraction(EF)<40%; Patients with uncontrolled cancer; Significant hepatic or renal impairment (and/or alanine transaminase(ALT) or Aspartate transaminase(AST) >2 times upper limit of normal, creatinine clearance rate(CCr)<50%); Previous catheter radiofrequency ablation for AF or cardiac surgery; Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.", "candidate_expression": "((<40%) AND (<50%) AND (>2 times upper limit of normal) AND (AF) AND (Aspartate transaminase(AST)) AND (Expected survival) AND (Heart failure) AND (III/IV) AND (In the list) AND (New York Heart Association(NYHA)) AND (Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.) AND (Significant) AND (Thrombosis) AND (acute diseases) AND (acute heart failure) AND (acute phase) AND (alanine transaminase(ALT)) AND (anticoagulant therapy) AND (cancer) AND (cardiac surgery) AND (catheter radiofrequency ablation) AND (cerebral infarction) AND (creatinine clearance rate(CCr)) AND (eject fraction(EF)) AND (heart transplantation) AND (hemorrhagic diseases) AND (hepatic impairment) AND (left atrium) AND (less than 1 year) AND (myocardial infarction) AND (not allowed) AND (other) AND (renal impairment) AND (uncontrolled) AND (within 3 months))"}
{"candidate_id": "LLM02519", "doc_id": "NCT00425789_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have known middle ear disease, chronic lung disease or claustrophobia", "candidate_expression": "((chronic lung disease) OR (claustrophobia) OR (middle ear disease))"}
{"candidate_id": "LLM02520", "doc_id": "NCT02905890_exc", "case_bucket": "or", "source_criterion": "Currently pregnant or using a reliable contraception (e.g. injectables, intrauterine devices, implant, oral contraceptive pills) Desiring pregnancy in the next year History of tubal ligation or hysterectomy Contraindication to progestin-only contraceptives Unable to comprehend consent material because of language barrier or psychological difficulty", "candidate_expression": "((Currently pregnant or using a reliable contraception (e.g. injectables, intrauterine devices, implant, oral contraceptive pills)) AND (Desiring pregnancy in the next year) AND (Unable to comprehend consent material because of language barrier or psychological difficulty) AND (contraceptives) AND (only) AND (progestin) AND ((hysterectomy) OR (tubal ligation)))"}
{"candidate_id": "LLM02521", "doc_id": "NCT01175044_exc", "case_bucket": "other", "source_criterion": "Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance). Age = 17. Allergy to povidone iodine. Any condition requiring antibiotics 14 days prior to arriving for surgery. Patients with chronic immunosuppression (such as HIV/AIDS). Unable to adhere to follow up schedule and treatment. Patients scheduled to undergo revision total knee arthroplasty for infectious reasons.", "candidate_expression": "((Age = 17) AND (Allergy) AND (HIV/AIDS) AND (Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance).) AND (Unable to adhere to follow up schedule and treatment.) AND (antibiotics 14 days prior to arriving for surgery) AND (immunosuppression chronic) AND (infectious reasons) AND (povidone iodine) AND (revision total knee arthroplasty) AND (surgery))"}
{"candidate_id": "LLM02522", "doc_id": "NCT03350815_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02523", "doc_id": "NCT03280017_exc", "case_bucket": "other", "source_criterion": "History of morphine allergy History of bupivacaine allergy Contraindication for ketamine infusion Contraindication for thoracic paravertebral block Anticipated postoperative positive pressure ventilation Body mass index more than 35 Any known psychiatric disorder", "candidate_expression": "((Body mass index more than 35) AND (Contraindication) AND (allergy History) AND (bupivacaine) AND (ketamine) AND (ketamine infusion) AND (morphine) AND (paravertebral block thoracic) AND (positive pressure ventilation postoperative) AND (psychiatric disorder))"}
{"candidate_id": "LLM02524", "doc_id": "NCT03187379_inc", "case_bucket": "other", "source_criterion": "bariatric surgery patients laparoscopic roux-en-y gastric bypass use of EEA stapler anastomosis", "candidate_expression": "((EEA stapler anastomosis) AND (bariatric surgery) AND (roux-en-y gastric bypass laparoscopic))"}
{"candidate_id": "LLM02525", "doc_id": "NCT03159507_exc", "case_bucket": "or", "source_criterion": "Allergy known to fish Pregnant women who breast-feed or test positive for pregnancy", "candidate_expression": "((Allergy) AND (fish) AND (women) AND ((Pregnant) OR (breast-feed) OR (test for pregnancy positive)))"}
```
