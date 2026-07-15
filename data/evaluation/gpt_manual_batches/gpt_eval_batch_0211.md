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
{"candidate_id": "LLM05251", "doc_id": "NCT02893228_exc", "case_bucket": "or", "source_criterion": "Patient refusal Allergy to local anaesthesia Severe coagulopathy Contralateral phrenic nerve palsy Local infection Moderate to severe pulmonary dysfunction (GOLD II, II, IV)", "candidate_expression": "((Allergy) AND (GOLD II, II, IV) AND (Local infection) AND (Patient refusal) AND (coagulopathy Severe) AND (local anaesthesia) AND (phrenic nerve palsy Contralateral) AND (pulmonary dysfunction) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM05252", "doc_id": "NCT02920177_exc", "case_bucket": "or", "source_criterion": "Established Osteoarthritis (Kellgren-Lawrence > 3) Minimum joint space > 2 mm as measured on AP radiograph Hip dysplasia (center edge angle < 20° on AP radiograph) Patients with clinically significant cardiovascular, renal, hepatic, endocrine disease, cancer or diabetes Patients with ongoing infection including HIV and Hepatitis Patient with history of osteomyelitis/septic arthritis Anticoagulation therapy Patients who are pregnant or breast feeding Patients with systemic, rheumatic or inflammatory disease of the knee or chondrocalcinosis, hemochromatosis, inflammatory arthritis, arthropathy of the knee associated with juxta-articular Paget's disease of the femur or tibia, hemophilic arthropathy, infectious arthritis, Charcot's knee joint, villonodular synovitis, and synovial chondromatosis Patients taking immunosuppressant medication Patients with abnormal hematology or serum chemistry lab results Patients receiving injection to treatment knee within 2 months of study enrollment BMI greater than 35 or less than 20", "candidate_expression": "((AP radiograph) AND (Anticoagulation therapy) AND (BMI) AND (Hip dysplasia) AND (Kellgren-Lawrence > 3) AND (Minimum joint space > 2 mm) AND (Osteoarthritis) AND (Paget's disease juxta-articular) AND (Patients who are pregnant or breast feeding) AND (arthropathy of the knee) AND (center edge angle < 20°) AND (immunosuppressant medication) AND (infection ongoing) AND (injection knee within 2 months of study enrollment) AND ((cancer) OR (cardiovascular disease) OR (diabetes) OR (endocrine disease) OR (hepatic disease) OR (renal disease)) AND ((HIV) OR (Hepatitis)) AND ((osteomyelitis) OR (septic arthritis)) AND ((Charcot's knee joint) OR (chondrocalcinosis) OR (hemochromatosis) OR (hemophilic arthropathy) OR (infectious arthritis) OR (inflammatory arthritis) OR (synovial chondromatosis) OR (villonodular synovitis)) AND ((femur) OR (tibia)) AND ((inflammatory disease) OR (rheumatic disease) OR (systemic disease)) AND ((hematology lab) OR (serum chemistry lab)) AND ((greater than 35) OR (less than 20)))"}
{"candidate_id": "LLM05253", "doc_id": "NCT03471117_exc", "case_bucket": "or", "source_criterion": "Allergy to Glitazones Myocardial infarction Heart failure Angina History of kidney stones Liver disease (abnormal liver enzymes) Anemia (hemoglobin <8 g/dl) Cancer with current treatment Previous organ transplantation Immunosuppressant therapy Human immunodeficiency virus infection Pregnancy or lactating Current tobacco use Dilantin and oral contraceptive usage due to potential drug interaction with glitazones Self-identified history of hypoglycemia", "candidate_expression": "((<8 g/dl) AND (Allergy) AND (Anemia) AND (Angina) AND (Cancer) AND (Current) AND (Dilantin) AND (Glitazones) AND (Heart failure) AND (History) AND (Human immunodeficiency virus infection) AND (Immunosuppressant therapy) AND (Liver disease) AND (Myocardial infarction) AND (Pregnancy) AND (Previous) AND (Self-identified) AND (abnormal) AND (current) AND (drug interaction) AND (glitazones) AND (hemoglobin) AND (history) AND (hypoglycemia) AND (kidney stones) AND (lactating) AND (liver enzymes) AND (oral contraceptive) AND (organ transplantation) AND (potential) AND (tobacco use) AND (treatment))"}
{"candidate_id": "LLM05254", "doc_id": "NCT02713087_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for supine-positioned elective craniotomy for supratentorial malignant and non-malignant brain tumors 3 cm or larger (measured as the largest diameter in any plane on MR images) ASA (American Society of Anesthesiologist) status 1-3 (27) Written informed consent from participating patients", "candidate_expression": "((ASA status 1-3 27) AND (American Society of Anesthesiologist status) AND (MR) AND (Written informed consent from participating patients) AND (brain tumors supratentorial 3 cm or larger malignant largest diameter in any plane) AND (supine-positioned elective craniotomy scheduled malignant))"}
{"candidate_id": "LLM05255", "doc_id": "NCT02810704_inc", "case_bucket": "or", "source_criterion": "Males and females 21 years of age or older; Undergoing elective primary, resurfacing arthroplasty, revision, or second stage re-implantation total hip replacement; Undergoing elective primary, revision, or second stage re-implantation total or uni compartmental knee replacement; Patient has necessary mental capacity to participate and is able to comply with study protocol requirements; Patient is willing and able to give informed consent; and Patient is willing to be randomized and participate.", "candidate_expression": "((21 years or older) AND (Males) AND (Patient has necessary mental capacity to participate and is able to comply with study protocol requirements) AND (Patient is willing and able to give informed consent) AND (Patient is willing to be randomized and participate) AND (age) AND (elective) AND (females) AND (knee replacement) AND (primary) AND (resurfacing arthroplasty) AND (revision) AND (second stage re-implantation) AND (second stage re-implantation total) AND (total hip replacement) AND (uni compartmental))"}
{"candidate_id": "LLM05256", "doc_id": "NCT02969876_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05257", "doc_id": "NCT03280017_exc", "case_bucket": "other", "source_criterion": "History of morphine allergy History of bupivacaine allergy Contraindication for ketamine infusion Contraindication for thoracic paravertebral block Anticipated postoperative positive pressure ventilation Body mass index more than 35 Any known psychiatric disorder", "candidate_expression": "((Anticipated) AND (Body mass index) AND (Contraindication) AND (History) AND (allergy) AND (bupivacaine) AND (ketamine) AND (ketamine infusion) AND (more than 35) AND (morphine) AND (paravertebral block) AND (positive pressure ventilation) AND (postoperative) AND (psychiatric disorder) AND (thoracic))"}
{"candidate_id": "LLM05258", "doc_id": "NCT01996436_inc", "case_bucket": "other", "source_criterion": "Adult patient, age 18-80 years old, with ruptured aneurysm(s) who experience cerebral vasospasm post operatively within 3-21 days.", "candidate_expression": "((Adult) AND (age 18-80 years old) AND (cerebral vasospasm post operatively within 3-21 days) AND (ruptured aneurysm))"}
{"candidate_id": "LLM05259", "doc_id": "NCT02731794_exc", "case_bucket": "other", "source_criterion": "myocardial infarction within the preceding 4 weeks severe valve disease requiring valve replacement cardiac reoperations", "candidate_expression": "((cardiac reoperations) AND (myocardial infarction) AND (requiring valve replacement) AND (severe) AND (the preceding 4 weeks) AND (valve disease) AND (valve replacement) AND (within the preceding 4 weeks))"}
{"candidate_id": "LLM05260", "doc_id": "NCT03195153_inc", "case_bucket": "or", "source_criterion": "diabetic patient; therapy with aspirin and insulin; patient well responders", "candidate_expression": "((aspirin) AND (diabetic) AND (insulin) AND (well responders))"}
{"candidate_id": "LLM05261", "doc_id": "NCT01497639_exc", "case_bucket": "other", "source_criterion": "previous brain surgery; cognitive impairment (< 120 points on the Mattis Dementia Rating Scale) moderate-to-severe depression (> 25 points on the Beck Depression Inventory) marked brain atrophy as detected by magnetic resonance imaging other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial", "candidate_expression": "((< 120 points) AND (> 25 points) AND (Beck Depression Inventory) AND (Mattis Dementia Rating Scale) AND (brain atrophy) AND (brain surgery) AND (cognitive impairment) AND (depression) AND (magnetic resonance imaging) AND (moderate-to-severe) AND (other medical or psychiatric coexisting disorders that could increase the surgical risk or interfere with completion of the trial) AND (previous))"}
{"candidate_id": "LLM05262", "doc_id": "NCT01116973_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent Subjects under 18 years of age Non-English speaking subjects Subjects that are unable to lay flat due to pulmonary complications, increased intracranial pressure (ICP), or unstable spinal cord injuries Subjects with known cardiac abnormalities (atrial septal defects or ventricular septal defects, severe tricuspid valve disease, severe pulmonary hypertension, Ejection fraction < 15%) Prisoners Subjects with known upper extremity deep vein thromboses (subclavian or distal) Subjects with non-functional CICC or PICC distal ports Subjects with femoral CICCs Pregnant women", "candidate_expression": "((< 15%) AND (Inability to obtain consent) AND (Pregnant) AND (Prisoners) AND (age) AND (cardiac abnormalities) AND (due to pulmonary complications) AND (femoral CICCs) AND (non-functional) AND (pulmonary complications) AND (severe) AND (under 18 years) AND (unstable) AND (upper extremity deep vein thromboses) AND (women) AND ((Ejection fraction) OR (atrial septal defects) OR (pulmonary hypertension) OR (tricuspid valve disease) OR (ventricular septal defects)) AND ((distal) OR (subclavian)) AND ((CICC distal ports) OR (PICC distal ports)) AND ((increased intracranial pressure (ICP)) OR (spinal cord injuries) OR (unable to lay flat)))"}
{"candidate_id": "LLM05263", "doc_id": "NCT00650312_exc", "case_bucket": "or", "source_criterion": "1. Institutionalized subjects will not be used. 2 Social Habits: 1. Use of any tobacco products. 2. Ingestion of any alcoholic, caffeine- or xanthine-containing food or beverage within the 48 hours prior to the initial dose of study medication. 3. Ingestion of any vitamins or herbal products within the 48 hours prior to the initial dose of the study medication. 4. Any recent, significant change in dietary or exercise habits. 5. Positive test for any drug included in the urine drug screen. 3. Medications: 1. Use of any medication within the 14 days prior to the initial dose of study medication. 2. Use of any medication known to alter hepatic enzyme activity within 28 days prior to the initial dose of study medication. 3. Use of hormonal contraceptives and hormonal replacement therapy within three months prior to the initial dose of study medication. 4. Diseases: a. History of any significant chronic disease and/or hepatitis. b. History of drug and/or alcohol abuse. c. Acute illness at the time of either the prestudy medical evaluation or dosing. d. Positive HIV, Hepatitis B, or Hepatitis C test. e. Renal disease or renal dysfunction (as suggested by serum creatinine levels greater than or equal to 1.5 mg/dL (for males) and greater than or equal to 1.4 mg/dL (for females) or abnormal creatinine clearance). 5. Abnormal and clinically significant laboratory test results: 1. Clinically significant deviation from the Guide for Clinically Relevant Abnormalities (see Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 2. Abnormal and clinically relevant ECG tracing. 6. Donation or loss of a significant volume of blood or plasma (> 450 mL) within 28 days prior to the initial dose of study medication. 7. Subjects who have received an investigational drug within 30 days prior to the initial dose of study medication. 8. Allergy or hypersensitivity to metformin hydrochloride. 9. History of difficulty in swallowing medication, or any gastrointestinal disorder which could affect the drug absorption.", "candidate_expression": "((Abnormal ECG tracing) AND (Abnormal and clinically significant laboratory test results:) AND (Allergy) AND (Clinically significant) AND (HIV test) AND (Hepatitis B test) AND (Hepatitis C test) AND (Renal disease) AND (abnormal creatinine clearance) AND (affect the drug absorption) AND (alcohol abuse History) AND (chronic disease significant) AND (clinically relevant) AND (difficulty in swallowing medication History) AND (drug abuse History) AND (females greater than or equal to 1.4 mg/dL) AND (gastrointestinal disorder affect the drug absorption) AND (hepatitis significant) AND (hormonal contraceptives within three months prior) AND (hormonal replacement therapy within three months prior) AND (hypersensitivity) AND (males greater than or equal to 1.5 mg/dL) AND (medication known to alter hepatic enzyme activity within 28 days prior) AND (medication within the 14 days prior) AND (metformin hydrochloride) AND (renal dysfunction) AND (serum creatinine levels) AND (significant) AND (tobacco products))"}
{"candidate_id": "LLM05264", "doc_id": "NCT02015923_inc", "case_bucket": "or", "source_criterion": "colorectal cancer above to 12 cm from the anal verge unresectable synchronous metastases no contraindications for chemotherapy absence of peritoneal carcinomatosis, central nervous system o bone metastasis. performance status ECOG = 2 (Eastern Cooperative Oncology Group) uncontrolled concomitant medical conditions that may compromise to chemotherapy significant symptomatic cardiac disease not pregnancy or breastfeeding", "candidate_expression": "((Eastern Cooperative Oncology Group) AND (cardiac disease significant symptomatic) AND (chemotherapy) AND (colorectal cancer above to 12 cm from the anal verge) AND (medical conditions that may compromise to chemotherapy uncontrolled concomitant) AND (metastases unresectable synchronous) AND NOT (contraindications) AND ((bone metastasis) OR (central nervous system metastasis) OR (peritoneal carcinomatosis)) AND ((ECOG = 2) OR (performance status)) AND ((breastfeeding) OR (pregnancy)))"}
{"candidate_id": "LLM05265", "doc_id": "NCT02371200_inc", "case_bucket": "or", "source_criterion": "1. Subject has a history of GTC seizures, either primary GTC or partial onset seizures with secondary generalization. 2. Is being admitted to a hospital for routine vEEG monitoring related to seizures. 3. Male or female between the ages of 2-99. 4. Has an upper arm circumference which is adequate for proper fit of the EMG monitor (at least 14cm). 5. If female and of childbearing potential, has a negative pregnancy test. 6. Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments. 7. Subject and/or Primary Caregiver must be competent to follow all study procedures. 8. Is able to read, speak, and understand English.", "candidate_expression": "((Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments.) AND (GTC seizures) AND (Male) AND (Subject and/or Primary Caregiver must be competent to follow all study procedures.) AND (adequate for proper fit of the EMG monitor) AND (admitted to a hospital) AND (at least 14cm) AND (between 2-99) AND (childbearing potential) AND (female) AND (history) AND (negative) AND (partial onset seizures) AND (pregnancy test) AND (primary GTC) AND (secondary generalization) AND (seizures) AND (the ages) AND (upper arm circumference) AND (vEEG monitoring))"}
{"candidate_id": "LLM05266", "doc_id": "NCT02901106_inc", "case_bucket": "or", "source_criterion": "patient 18 years old and more with multiple sclerosis according to the criteria of Mac Donald 2010 : relapsing-remitting (RR), secondary-progressive (SP) or primary-progressive (PP) for which treatment with dimethyl-fumarate has been prescribed followed at the Rothschild Foundation in the Neurology Department having given written consent to participation in the study", "candidate_expression": "((Rothschild Foundation in the Neurology Department) AND (criteria of Mac Donald 2010 RR SP) AND (dimethyl-fumarate PP) AND (having given written consent to participation in the study) AND (multiple sclerosis) AND (old and more 18 years) AND ((primary-progressive) OR (relapsing-remitting) OR (secondary-progressive)))"}
{"candidate_id": "LLM05267", "doc_id": "NCT03056391_inc", "case_bucket": "other", "source_criterion": "1. Patient age ≥ 12 years 2. Presence of P. knowlesi malaria, confirmed by positive blood smear with asexual forms of P. knowlesi. 3. Temperature >38C on admission or fever during the preceding 48 hours 4. Enrolled within 18 hours of commencing antimalarial treatment 5. Written informed consent from patient or attending relative able to and willing to give informed consent. Consent form and information sheets will be translated into Malay and copies provided to the patient.", "candidate_expression": "((Enrolled within 18 hours) AND (P. knowlesi malaria) AND (Temperature >38C) AND (Written informed consent from patient or attending relative able to and willing to give informed consent.) AND (age ≥ 12 years) AND (antimalarial treatment) AND (blood smear positive))"}
{"candidate_id": "LLM05268", "doc_id": "NCT00650312_exc", "case_bucket": "or", "source_criterion": "1. Institutionalized subjects will not be used. 2 Social Habits: 1. Use of any tobacco products. 2. Ingestion of any alcoholic, caffeine- or xanthine-containing food or beverage within the 48 hours prior to the initial dose of study medication. 3. Ingestion of any vitamins or herbal products within the 48 hours prior to the initial dose of the study medication. 4. Any recent, significant change in dietary or exercise habits. 5. Positive test for any drug included in the urine drug screen. 3. Medications: 1. Use of any medication within the 14 days prior to the initial dose of study medication. 2. Use of any medication known to alter hepatic enzyme activity within 28 days prior to the initial dose of study medication. 3. Use of hormonal contraceptives and hormonal replacement therapy within three months prior to the initial dose of study medication. 4. Diseases: a. History of any significant chronic disease and/or hepatitis. b. History of drug and/or alcohol abuse. c. Acute illness at the time of either the prestudy medical evaluation or dosing. d. Positive HIV, Hepatitis B, or Hepatitis C test. e. Renal disease or renal dysfunction (as suggested by serum creatinine levels greater than or equal to 1.5 mg/dL (for males) and greater than or equal to 1.4 mg/dL (for females) or abnormal creatinine clearance). 5. Abnormal and clinically significant laboratory test results: 1. Clinically significant deviation from the Guide for Clinically Relevant Abnormalities (see Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 2. Abnormal and clinically relevant ECG tracing. 6. Donation or loss of a significant volume of blood or plasma (> 450 mL) within 28 days prior to the initial dose of study medication. 7. Subjects who have received an investigational drug within 30 days prior to the initial dose of study medication. 8. Allergy or hypersensitivity to metformin hydrochloride. 9. History of difficulty in swallowing medication, or any gastrointestinal disorder which could affect the drug absorption.", "candidate_expression": "((Abnormal ECG tracing) AND (Abnormal and clinically significant laboratory test results:) AND (Clinically significant) AND (History) AND (Positive) AND (affect the drug absorption) AND (clinically relevant) AND (greater than or equal to 1.4 mg/dL) AND (greater than or equal to 1.5 mg/dL) AND (hormonal contraceptives) AND (hormonal replacement therapy) AND (medication) AND (medication known to alter hepatic enzyme activity) AND (metformin hydrochloride) AND (significant) AND (the initial dose of study medication) AND (tobacco products) AND (within 28 days prior) AND (within the 14 days prior) AND (within three months prior) AND ((chronic disease) OR (hepatitis)) AND ((alcohol abuse) OR (drug abuse)) AND ((HIV test) OR (Hepatitis B test) OR (Hepatitis C test)) AND ((Renal disease) OR (renal dysfunction)) AND ((females) OR (males)) AND ((abnormal creatinine clearance) OR (serum creatinine levels)) AND ((Allergy) OR (hypersensitivity)) AND ((difficulty in swallowing medication) OR (gastrointestinal disorder)))"}
{"candidate_id": "LLM05269", "doc_id": "NCT02121145_inc", "case_bucket": "or", "source_criterion": "Male or female subjects aged =18 to =65 years General good health as established by medical history and physical examination Written informed consent Females of childbearing potential must agree to use an efficacious hormonal or barrier method of birth control during the study. Abstinence is acceptable. Available for all visits scheduled in this study.", "candidate_expression": "((=18 to =65 years) AND (Abstinence) AND (Available for all visits) AND (Females) AND (General good health) AND (Male) AND (Written informed consent) AND (aged) AND (agree to use) AND (barrier method) AND (birth control) AND (childbearing potential) AND (during the study) AND (efficacious) AND (established by medical history) AND (female) AND (hormonal method) AND (physical examination) AND (scheduled in this study))"}
{"candidate_id": "LLM05270", "doc_id": "NCT02845427_exc", "case_bucket": "other", "source_criterion": "Revision cases Uncontrolled bleeding tendency (prothrombin conc. Less than 70%) History of deep venous thrombosis Sever liver impairment (liver failure) Sever renal impairment (S. creatinine more than 3)", "candidate_expression": "((Revision cases) AND (bleeding tendency Uncontrolled) AND (creatinine more than 3) AND (deep venous thrombosis History) AND (liver failure) AND (liver impairment Sever) AND (prothrombin Less than 70%) AND (renal impairment Sever))"}
{"candidate_id": "LLM05271", "doc_id": "NCT02267616_inc", "case_bucket": "other", "source_criterion": "Women age 18-45 Within 6 months of expiration or beyond the end of the FDA-approved duration of use of the levonorgestrel intrauterine device (LNG-IUD = 5 years) OR the etonogestrel-releasing subdermal implant (ENG implant = 3 years) Able to consent in English or Spanish. Not pregnant at the time of enrollment", "candidate_expression": "((18-45) AND (Able to consent in English or Spanish) AND (Not) AND (Women) AND (age) AND (at the time of enrollment) AND (pregnant))"}
{"candidate_id": "LLM05272", "doc_id": "NCT02707809_inc", "case_bucket": "other", "source_criterion": "kidney transplant recipient", "candidate_expression": "(kidney transplant)"}
{"candidate_id": "LLM05273", "doc_id": "NCT01735955_exc", "case_bucket": "or", "source_criterion": "Patient has been permanently discontinued from nilotinib treatment in the parent study due to unacceptable toxicity, non-compliance to study procedures, withdrawal of consent or any other reason Patient has participated in a Novartis sponsored combination trial where nilotinib was dispensed in combination with another study medication and patient is still receiving combination therapy Patients who are currently receiving treatment with any medications that have the potential to prolong the QT interval or inducing Torsade de Pointes and the treatment cannot be either safely discontinued at least one week prior to nilotinib treatment or switched to a different medication prior to start of nilotinib treatment and for the duration of the study Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hcG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception during the study and for 30 days after the final dose of nilotinib.", "candidate_expression": "((Novartis sponsored) AND (Pregnant) AND (Women) AND (any medications) AND (any other reason) AND (child-bearing potential) AND (consent) AND (contraception) AND (currently) AND (discontinued) AND (during the study) AND (for 30 days after the final dose of nilotinib) AND (have the potential to prolong the QT interval) AND (hcG laboratory test) AND (highly effective methods) AND (inducing Torsade de Pointes) AND (lactating) AND (nilotinib) AND (non-compliance) AND (nursing) AND (participated in a combination trial) AND (permanently) AND (physiologically capable of becoming pregnant) AND (positive) AND (study procedures) AND (the final dose of nilotinib) AND (treatment) AND (unacceptable toxicity) AND (unless) AND (withdrawal) AND (women))"}
{"candidate_id": "LLM05274", "doc_id": "NCT03216447_inc", "case_bucket": "other", "source_criterion": "Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure Patient is a primary liver transplant recipient Patient is 20 to 70 years of age Patient should be clearly conscious, fully understand and able to answer questionnaire", "candidate_expression": "((Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure) AND (Patient should be clearly conscious, fully understand and able to answer questionnaire) AND (age 20 to 70 years) AND (primary liver transplant) AND (recipient))"}
{"candidate_id": "LLM05275", "doc_id": "NCT02827526_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure (defined as a serum creatinine > 2.0 mg/dL.) American Society of Anesthesiologists Physical Status IV or V Pulmonary disease necessitating home oxygen therapy Allergy to methadone, hydromorphone, or ketamine Preoperative recent history of opioid or alcohol abuse Significant liver disease Inability to use a PCA device or speak the English language", "candidate_expression": "((> 2.0 mg/dL) AND (American Society of Anesthesiologists Physical Status) AND (IV or V) AND (Inability to speak the English language) AND (Inability to use) AND (PCA device) AND (Preoperative) AND (Pulmonary disease) AND (Significant) AND (alcohol abuse) AND (history) AND (home oxygen therapy) AND (hydromorphone) AND (ketamine) AND (liver disease) AND (methadone) AND (opioid abuse) AND (recent) AND (renal failure) AND (serum creatinine))"}
```
