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
{"candidate_id": "LLM03451", "doc_id": "NCT02283905_exc", "case_bucket": "other", "source_criterion": "The patient's data will be excluded if they die within 3 days of hospital admission.", "candidate_expression": "(die within 3 days of hospital admission)"}
{"candidate_id": "LLM03452", "doc_id": "NCT02970773_inc", "case_bucket": "other", "source_criterion": "Motor complete tetraplegia for at least 3 months Age from 18 to 74 years Body mass index (BMI) from 18 to 35kg/m2 Informed consent as documented by signature", "candidate_expression": "((Age from 18 to 74 years) AND (BMI) AND (Body mass index from 18 to 35kg/m2) AND (nformed consent as documented by signature) AND (tetraplegia complete at least 3 months))"}
{"candidate_id": "LLM03453", "doc_id": "NCT02277041_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((cesarean section) AND (gestation after 37 weeks) AND (singleton pregnancy))"}
{"candidate_id": "LLM03454", "doc_id": "NCT02196285_inc", "case_bucket": "other", "source_criterion": "Male Age between 18 and 49 years old; Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications); Willing to strictly follow the study protocol; Capacity for understanding and signing in the Informed Consent Form; To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion; Intellectual level which allows to filling in the diaries for registering of symptoms at home; Willing to undergo to serological testing to HIV, HBV and HCV; Being in good health, with no significant medical history; Physical examination at screening period without clinically significant changes; Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.", "candidate_expression": "((Age between 18 and 49 years old) AND (Being in good health, with no significant medical history;) AND (Capacity for understanding and signing in the Informed Consent Form;) AND (Intellectual level which allows to filling in the diaries for registering of symptoms at home;) AND (Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.) AND (Male) AND (Physical examination at screening period screening period) AND (Physical examination at screening period without clinically significant changes;) AND (To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion;) AND (Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications);) AND (Willing to strictly follow the study protocol;) AND (Willing to undergo to serological testing to HIV, HBV and HCV;) AND (good health) AND (serological testing to HBV) AND (serological testing to HCV) AND (serological testing to HIV))"}
{"candidate_id": "LLM03455", "doc_id": "NCT02779374_inc", "case_bucket": "scope", "source_criterion": "Women with POI: For the purpose of the research women is considered to have POI if she is aged less than 40 years and has amenorrhea of at least 4 month with FSH level above 25 IU/L (repeated twice >4 weeks apart).", "candidate_expression": "((>4 weeks apart) AND (FSH level) AND (POI) AND (Women) AND (above 25 IU/L) AND (aged) AND (amenorrhea) AND (at least 4 month) AND (less than 40 years) AND (repeated twice))"}
{"candidate_id": "LLM03456", "doc_id": "NCT02467686_inc", "case_bucket": "or", "source_criterion": "Menopausal women with breast cancer treated and using tamoxifen or aromatase inhibitor. With hot flashes and with or without active sexual life.", "candidate_expression": "((Menopausal) AND (breast cancer) AND (hot flashes) AND (treated) AND (women) AND ((with active sexual life) OR (without active sexual life)) AND ((aromatase inhibitor) OR (tamoxifen)))"}
{"candidate_id": "LLM03457", "doc_id": "NCT01891513_inc", "case_bucket": "or", "source_criterion": "Age 65 years and older Hypertension - untreated (Systolic Blood Pressure (SBP) ≥ 140 mm Hg or Diastolic Blood Pressure (DBP) ≥ 90 mm Hg) or treated Physical limitations evidenced by either: Score ≤ 10 on the Short Physical Performance Battery OR Walking speed < 1.2 m/sec during 400 m usual-paced test Sedentary lifestyle, defined as <150 min/wk of moderate physical activity as assessed by CHAMPS questionnaire Willingness to participate in all study procedures", "candidate_expression": "((400 m usual-paced test) AND (65 years and older) AND (< 1.2 m/sec) AND (<150 min/wk) AND (Age) AND (CHAMPS questionnaire) AND (Diastolic Blood Pressure (DBP)) AND (Hypertension) AND (Score ≤ 10) AND (Sedentary lifestyle) AND (Short Physical Performance Battery) AND (Systolic Blood Pressure (SBP)) AND (Walking speed) AND (moderate physical activity) AND (treated) AND (untreated) AND (≥ 140 mm Hg) AND (≥ 90 mm Hg))"}
{"candidate_id": "LLM03458", "doc_id": "NCT03193684_exc", "case_bucket": "or", "source_criterion": "eGFR <60 T2DM patients on insulin, GLP-1 RA or SGLT2 treatment Major organ disease type 1 diabetes", "candidate_expression": "((<60) AND (Major organ disease) AND (T2DM) AND (eGFR) AND (type 1 diabetes) AND ((GLP-1) OR (RA) OR (SGLT2) OR (insulin)))"}
{"candidate_id": "LLM03459", "doc_id": "NCT02462317_inc", "case_bucket": "or", "source_criterion": "First single stroke ischaemic or haemorrhagic responsible of an hemiplegia Stoke since less than 2 month A sufficient understood A spasticity : a Tardieu score upper or equal to 2 on at least one of the following muscle-triceps surae, flexors of fingers, of wrist and of elbow A free consent", "candidate_expression": "((A free consent) AND (Stoke since less than 2 month) AND (Tardieu score upper or equal to 2) AND (hemiplegia) AND (spasticity) AND (stroke First single) AND ((elbow) OR (flexors of fingers) OR (muscle-triceps surae) OR (wrist)) AND ((haemorrhagic) OR (ischaemic)))"}
{"candidate_id": "LLM03460", "doc_id": "NCT03338855_inc", "case_bucket": "or", "source_criterion": "Patients are able to provide signed and dated written informed consent prior to any study specific procedures. Women are post-menopausal (defined as at least 1 year post cessation of menses) and aged = 45 and = 70 years. Males are aged = 40 years and = 70 years. Patients should have suitable veins for cannulation or repeated venipuncture. Patients are diagnosed with T2DM for at least the last 6 months. Patients are on no other anti-diabetic drug treatment, or on stable maximum 3000 mg daily dose metformin treatment and/or on stable dose of a DPPIV inhibitor treatment for at least the last 3 months5. HbA1c levels =6.0% (=42 mmol/mol) and =9.0% (75 mmol/mol). Have a body mass index (BMI) = 35 kg/m2.", "candidate_expression": "((75 mmol/mol) AND (= 35 kg/m2) AND (= 40 years and = 70 years) AND (= 45 and = 70 years) AND (=42 mmol/mol) AND (=6.0%) AND (=9.0%) AND (HbA1c levels) AND (Patients are able to provide signed and dated written informed consent prior to any study specific procedures.) AND (T2DM) AND (aged) AND (as at least 1 year post cessation of menses) AND (body mass index (BMI)) AND (cessation of menses) AND (for at least the last 3 months) AND (for at least the last 6 months) AND (maximum 3000 mg daily dose) AND (no) AND (other) AND (post-menopausal) AND (stable) AND (stable dose) AND ((DPPIV inhibitor) OR (anti-diabetic drug treatment) OR (metformin)) AND ((Males) OR (Women)))"}
{"candidate_id": "LLM03461", "doc_id": "NCT02219880_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03462", "doc_id": "NCT03181984_exc", "case_bucket": "or", "source_criterion": "Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((Be judged not suitable to participate the study by the investigators) AND (Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application) AND (Scar diathesis) AND ((porphyrins) OR (porphyrins analogues)) AND ((Allergic constitution) OR (Allergy) OR (Photosensitivity) OR (Porphyria)))"}
{"candidate_id": "LLM03463", "doc_id": "NCT00676273_inc", "case_bucket": "other", "source_criterion": "Are at least 18 years of age Demonstrate a positive cough stress test during complex multi-channel urodynamic testing Demonstrate impact of stress urinary incontinence on quality of life questionnaire Are able to comprehend and sign a written informed consent Understand and are willing to comply with the study requirements, including agreeing to be available for the follow-up evaluations Are psychologically stable and suitable for interventions determined by the investigator Are ambulatory and able to use a toilet independently", "candidate_expression": "((Understand the study requirements) AND (able to comprehend a written informed consent) AND (able to sign a written informed consent) AND (able to use a toilet independently) AND (age) AND (ambulatory) AND (at least 18 years) AND (complex multi-channel urodynamic testing) AND (cough stress test) AND (determined by the investigator) AND (positive) AND (psychologically stable) AND (quality of life questionnaire) AND (stress urinary incontinence) AND (suitable for interventions) AND (willing to comply with the study requirements))"}
{"candidate_id": "LLM03464", "doc_id": "NCT02996916_inc", "case_bucket": "or", "source_criterion": "Written informed consent obtained Male and female subjects aged 20 years or older at informed consent Essential hypertension who had never received angiotensin II receptor antagonists and calcium channel blockers", "candidate_expression": "((Essential hypertension) AND (Male) AND (Written informed consent obtained) AND (aged 20 years or older at informed consent) AND (angiotensin II receptor antagonists) AND (calcium channel blockers) AND (female))"}
{"candidate_id": "LLM03465", "doc_id": "NCT02566226_inc", "case_bucket": "other", "source_criterion": "physical status I - III patients scheduled to undergo hip arthroplasty", "candidate_expression": "((I - III) AND (hip arthroplasty) AND (physical status) AND (scheduled to undergo))"}
{"candidate_id": "LLM03466", "doc_id": "NCT02426944_exc", "case_bucket": "or", "source_criterion": "thrombus in the LA or LAA; mechanical valve prosthesis; mitral stenosis; previous LAA ligation during cardiac surgery; life expectancy less than 2 years; comorbidities other than AF, which present an indication for anticoagulation; patent foramen ovale with atrial septal aneurysm mobile plaque in the aorta; symptomatic atherosclerosis of the carotid artery; pericardial effusion greater than 10 mm; clinically significant bleeding within the 30 days prior to the scheduled procedure; stroke or other cardioembolic event within the 30 days prior to the scheduled procedure; acute coronary syndrome within the 90 days prior to the scheduled procedure, gravidity, significant valvular disease, creatinine clearance less than 30 ml/min", "candidate_expression": "((LAA ligation) AND (acute coronary syndrome within the 90 days prior to the scheduled procedure) AND (anticoagulation) AND (atherosclerosis symptomatic of the carotid artery) AND (atrial septal aneurysm) AND (bleeding clinically significant within the 30 days prior to the scheduled procedure) AND (cardiac surgery) AND (comorbidities) AND (creatinine clearance less than 30 ml/min) AND (gravidity) AND (indication) AND (life expectancy less than 2 years) AND (mechanical valve prosthesis) AND (mitral stenosis) AND (mobile plaque in the aorta) AND (patent foramen ovale) AND (pericardial effusion greater than 10 mm) AND (thrombus) AND (valvular disease significant) AND NOT (AF) AND ((LA) OR (LAA)) AND ((cardioembolic event other) OR (stroke)))"}
{"candidate_id": "LLM03467", "doc_id": "NCT02370069_inc", "case_bucket": "or", "source_criterion": "Males and females of 18 years of age or older at the time of the vaccination Severe chronic kidney disease (Stage 4 and 5)", "candidate_expression": "((Males) AND (Stage 4 chronic kidney disease) AND (Stage 5 chronic kidney disease) AND (age 18 years or older at the time of the vaccination) AND (chronic kidney disease Severe) AND (females) AND (vaccination))"}
{"candidate_id": "LLM03468", "doc_id": "NCT02593409_exc", "case_bucket": "or", "source_criterion": "HIV infection at screening participation in previous or concurrent HIV vaccine trials lactating, pregnant or planning pregnancy renal function impairment (serum creatinine >1.5 mg/dl), Fanconi syndrome abnormal liver function tests (AST/ALT > 43 U/L), liver disease, viral hepatitis, hepatitis B virus (HBV) infection serum phosphorus <2.2mg/dl, osteoporosis known sensitivity to components of the Truvada® formulation any immunosuppressive treatment, such as systemic corticosteroids assumption of medication that interacts with Truvada® high likelihood of poor adherence to PREP and clinic attendance any condition that in the opinion of the attending physician could endanger the health of the participant or render her unsuitable to participate in the trial", "candidate_expression": "((<2.2mg/dl) AND (> 43 U/L) AND (>1.5 mg/dl) AND (ALT) AND (AST) AND (Fanconi syndrome) AND (HIV infection) AND (Truvada) AND (abnormal) AND (actating, pregnant or planning pregnancy) AND (hepatitis B virus (HBV) infection) AND (high likelihood of poor adherence to PREP and clinic attendanc) AND (immunosuppressive treatment) AND (liver disease) AND (liver function tests) AND (osteoporosis) AND (participation in previous or concurrent HIV vaccine trials) AND (renal function impairment) AND (sensitivity) AND (serum creatinine) AND (serum phosphorus) AND (systemic corticosteroids) AND (viral hepatitis))"}
{"candidate_id": "LLM03469", "doc_id": "NCT02871206_inc", "case_bucket": "other", "source_criterion": "Healthy children aged 6 months to 72 months", "candidate_expression": "((6 months to 72 months) AND (Healthy) AND (aged) AND (children))"}
{"candidate_id": "LLM03470", "doc_id": "NCT02323399_inc", "case_bucket": "or", "source_criterion": "Subject's age is between =12 and 16 years, inclusive Subject is scheduled for a procedure that requires general or neuraxial anesthesia Subjects must have normal or clinically acceptable physical exam Subjects with controlled diabetes prior to entry must have a mean systolic/diastolic office blood pressure =128/78 mmHg (sitting, after 5 minutes of rest) Females must have a urine or serum pregnancy test (Human Chorionic Gonadotropin) that is negative at Screening and Day 1 Subject's parent or legal guardian gives informed consent and subject gives assent.", "candidate_expression": "((Human Chorionic Gonadotropin at Screening Day 1) AND (Subject's parent or legal guardian gives informed consent and subject gives assent.) AND (age between =12 and 16 years) AND (diabetes controlled prior to entry) AND (general t) AND (mean diastolic blood pressure 78 mmHg) AND (mean systolic blood pressure 128 mmHg) AND (neuraxial anesthesia normal clinically acceptable) AND (physical exam) AND (procedure) AND (scheduled for a procedure) AND (serum pregnancy test) AND (urine pregnancy test))"}
{"candidate_id": "LLM03471", "doc_id": "NCT02765217_exc", "case_bucket": "or", "source_criterion": "Receiving antibiotic and/or probiotic, 8 weeks before the study Chronic gastrointestinal system disorders Congenital anomalies Chronic diseases Chemotherapy and radiotherapy Pregnancy", "candidate_expression": "((8 weeks before the study) AND (Chronic diseases) AND (Chronic gastrointestinal system disorders) AND (Congenital anomalies) AND (Pregnancy) AND (the study) AND ((antibiotic) OR (probiotic)) AND ((Chemotherapy) OR (radiotherapy)))"}
{"candidate_id": "LLM03472", "doc_id": "NCT02884115_exc", "case_bucket": "other", "source_criterion": "Human immunodeficiency virus (HIV)-infected Baseline serology showed a nonreactive RPR test follow-up is inadequate Allergic to penicillin Pregnant woman", "candidate_expression": "((Allergic) AND (Baseline) AND (Human immunodeficiency virus (HIV)-infected) AND (Pregnant) AND (RPR test) AND (follow-up is inadequate) AND (nonreactive) AND (penicillin) AND (serology) AND (woman))"}
{"candidate_id": "LLM03473", "doc_id": "NCT02621489_inc", "case_bucket": "or", "source_criterion": "Patients eligible for PCI with application of DES, due to ACS. Patients with known or newly diagnosed T2D (type 2 diabetes is diagnosed according to current WHO criteria or by the use of anti-diabetic drugs) Male and female subjects 18-80 years. HbA1c (accordingly to IFCC) 47 mmol/mol - 110 mmol/mol. Signed informed consent form.", "candidate_expression": "((ACS) AND (DES) AND (HbA1c 47 mmol/mol - 110 mmol/mol) AND (PCI) AND (Signed informed consent form) AND (T2D) AND (years 18-80) AND ((Male) OR (female)))"}
{"candidate_id": "LLM03474", "doc_id": "NCT03119766_exc", "case_bucket": "or", "source_criterion": "Organic diseases of the digestive system (gastro-oesophageal reflux disease (GERD), ulcer, chronic pancreatitis, cholelithiasis, fatty liver disease, hepatitis, cirrhosis of liver, etc.) . Diagnosis of other functional diseases of the digestive system, such as dyskinesia of cystic duct or gallbladder, irritable bowel syndrome, etc. Discontinuation of proton pump inhibitors, propulsives, antispasmodics, antacids, or bismuth preparations less than 7 days prior to randomization. H. Pylori eradication within 2 months before study entry. Intestinal infection within 2 months before study entry. Known history of/suspected malignant neoplasm of various sites. Prior diagnosis of a class IV cardiovascular disease (according to the New York Heart Association, 1964), hypothyroidism, diabetes mellitus, chronic kidney disease (С3-5), or disease of liver with portal hypertension and/or severe decompensation (Child-Pugh score > 6). Other severe coexisting morbidity which, in the investigator's opinion, can prevent the patient from participating in the study. Allergy/intolerance to any of the components of medications used in the treatment. Pregnancy, breast-feeding. Patients who, from investigator's point of view, will fail to comply with the observation requirements of the trial or with the dosing regimen of the investigational drugs. Planned hospitalization during the study period, for any diagnostic or treatment procedures. Drug addiction, alcohol use in the amount over 2 units of alcohol a day, mental diseases. Intake of medicines listed in the section 'Prohibited concomitant treatment' for 1 month prior to the enrollment in the trial. Participation in other clinical trials within 3 months to the enrollment in this study. Patient is related to the research staff of the clinical investigative site who are directly involved in the trial or is the immediate family member of the investigator. The immediate family members include husband/wife, parents, children or brothers (or sisters), regardless of whether they are natural or adopted. Patient works for OOO \"NPF \"MATERIA MEDICA HOLDING\" (i.e., is the company's employee, temporary contract worker or appointed official responsible for carrying out the research or their immediate family).", "candidate_expression": "((1 month prior to the enrollment in the trial) AND (3-5) AND (> 6) AND (Child-Pugh score) AND (Discontinuation) AND (H. Pylori eradication) AND (Intestinal infection) AND (New York Heart Association) AND (Organic diseases) AND (Participation in other clinical trials within 3 months to the enrollment in this study.) AND (Planned) AND (class IV) AND (coexisting) AND (components of medications used in the treatment) AND (digestive system) AND (disease of liver) AND (during the study period) AND (functional diseases) AND (hospitalization) AND (less than 7 days prior to randomization) AND (listed in the section 'Prohibited concomitant treatment') AND (malignant neoplasm) AND (medicines) AND (morbidity) AND (over 2 units of alcohol a day) AND (portal hypertension) AND (randomization) AND (responsible for carrying out the research or their immediate family) AND (study entry) AND (the enrollment in the trial) AND (various sites) AND (within 2 months before study entry) AND (works for OOO \"NPF \"MATERIA MEDICA HOLDING\") AND (С) AND ((dyskinesia of cystic duct) OR (dyskinesia of gallbladder) OR (irritable bowel syndrome)) AND ((antacids) OR (antispasmodics) OR (bismuth preparations) OR (propulsives) OR (proton pump inhibitors)) AND ((history of) OR (suspected)) AND ((cardiovascular disease) OR (chronic kidney disease) OR (diabetes mellitus) OR (hypothyroidism) OR (severe decompensation)) AND ((Allergy) OR (intolerance)) AND ((cholelithiasis) OR (chronic pancreatitis) OR (cirrhosis of liver) OR (fatty liver disease) OR (gastro-oesophageal reflux disease (GERD)) OR (hepatitis) OR (ulcer)) AND ((Pregnancy) OR (breast-feeding)) AND ((diagnostic procedures) OR (treatment procedures)) AND ((Drug addiction) OR (alcohol use) OR (mental diseases)) AND ((appointed official) OR (company's employee) OR (temporary contract worker)))"}
{"candidate_id": "LLM03475", "doc_id": "NCT01680081_exc", "case_bucket": "or", "source_criterion": "Contraindication of CT Known allergy to iodinated contrast media or history of contrast-induced nephropathy Decreased renal function: elevated serum creatinine(>1.5mg/dl) Contraindication to beta-blockers Severe arrhythmia: arterial fibrillation or uncontrolled tachyarrhythmia, or advanced atrioventricular block (second or third degree heart block) Contraindication of MRI Claustrophobia Metallic hazards Pacemaker implant eGFR<30 ml/min Unstable or uncooperative patients Limited life expectancy due to cancer or end-stage renal or liver disease Evidence of severe symptomatic heart failure (NYHA Class III or IV) Previous myocardial infarction, coronary artery intervention, coronary artery bypass surgery, or other cardiac surgery", "candidate_expression": "((Claustrophobia) AND (Contraindication) AND (Contraindication of CT) AND (Known allergy) AND (MRI) AND (Metallic hazards) AND (NYHA Class III or IV) AND (Pacemaker implant) AND (Unstable patients) AND (advanced atrioventricular block) AND (arrhythmia Severe) AND (arterial fibrillation) AND (beta-blockers) AND (cancer) AND (contrast-induced nephropathy) AND (coronary artery bypass surgery) AND (coronary artery intervention) AND (eGFR <30 ml/min) AND (end-stage renal disease) AND (heart failure severe symptomatic) AND (iodinated contrast media) AND (life expectancy Limited) AND (liver disease) AND (myocardial infarction) AND (other cardiac surgery) AND (renal function Decreased) AND (second degree heart block) AND (serum creatinine elevated >1.5mg/dl) AND (third degree heart block) AND (uncontrolled tachyarrhythmia) AND (uncooperative patients))"}
```
