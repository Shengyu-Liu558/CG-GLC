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
{"candidate_id": "LLM04276", "doc_id": "NCT02426034_exc", "case_bucket": "or", "source_criterion": "Subjects with poor-controlled arterial hypertension (systolic blood pressure> 140 mmHg and diastolic blood pressure > 90 mm Hg) despite standard medical management; Coronary heart disease greater than ClassII; II-level arrhythmia (including QT interval prolongation, for man = 450 ms, for woman = 470 ms) together with Class II cardiac dysfunction; Factors that could have an effect on oral medication (such as inability to swallow, chronic diarrhea and intestinal obstruction); Subjects with high gastrointestinal bleeding risk, including the following conditions: local active ulcer lesions with positive fecal occult blood test (++); history of black stool, or vomiting blood in the past 3 months;unresected primary lesion in stomach with positive fecal occult blood test (+), ulcerated gastric carcinoma with massive alimentary tract bleeding risk judged by PIs based on gastric endoscopy result; Abnormal Coagulation (INR>1.5<U+3001>APTT>1.5 UNL), with tendency of bleed; Associated with CNS (central nervous system) metastases; Pregnant or lactating women; Other conditions regimented at investigators' discretion.", "candidate_expression": "((Abnormal Coagulation) AND (Pregnant or lactating women) AND (QT interval prolongation) AND (arrhythmia II-level) AND (cardiac dysfunction Class II) AND (diastolic blood pressure > 90 mm Hg) AND (fecal occult blood test positive +) AND (fecal occult blood test positive ++) AND (gastrointestinal bleeding risk high) AND (metastases CNS) AND (systolic blood pressure > 140 mmHg Subjects) AND (tendency of bleed) AND ((chronic diarrhea) OR (inability to swallow) OR (intestinal obstruction)) AND ((black stool) OR (vomiting blood)) AND ((primary lesion stomach) OR (ulcer lesions active) OR (ulcerated gastric carcinoma bleeding risk)) AND ((APTT >1.5 UNL) OR (INR >1.5)) AND ((Coronary heart disease greater than ClassII) OR (arterial hypertension poor-controlled)))"}
{"candidate_id": "LLM04277", "doc_id": "NCT02821819_exc", "case_bucket": "other", "source_criterion": "PCOS patients Allergy to gonadotrophins Concomitant participation in other trial", "candidate_expression": "((Allergy) AND (Concomitant participation in other trial) AND (PCOS) AND (gonadotrophins))"}
{"candidate_id": "LLM04278", "doc_id": "NCT00962364_inc", "case_bucket": "or", "source_criterion": "acute myocardial infarction or ischemic cardiomyopathy with or without previous myocardial infarction or dilated cardiomyopathy due to valvular heart disease, hypertensive heart disease, history of myocarditis (no active myocardial infection present)", "candidate_expression": "((active) AND (acute myocardial infarction) AND (dilated cardiomyopathy) AND (history) AND (hypertensive heart disease) AND (ischemic cardiomyopathy) AND (myocardial infarction) AND (myocardial infection) AND (myocarditis) AND (no) AND (previous) AND (valvular heart disease))"}
{"candidate_id": "LLM04279", "doc_id": "NCT03103204_inc", "case_bucket": "or", "source_criterion": "Moderate to advanced generalized chronic periodontitis Body mass index: > 18.5 kg/m2 Minimum of 12 natural teeth Smokers, non-smokers or former-smokers", "candidate_expression": "((Body mass index > 18.5 kg/m2) AND (generalized chronic periodontitis Moderate to advanced) AND (natural teeth Minimum of 12) AND ((Smokers) OR (former-smokers) OR (non-smokers)))"}
{"candidate_id": "LLM04280", "doc_id": "NCT03369379_exc", "case_bucket": "or", "source_criterion": "Those subjects with previous use of vitamin D. Known subjects with renal, liver, calcium metabolism disorders, malabsorption disorders, known neoplasms. Subjects with serum calcium levels equal to or greater than 10.2 mg / dl.", "candidate_expression": "((calcium metabolism disorders) AND (disorders liver) AND (disorders renal) AND (equal to or greater than 10.2 mg / dl) AND (malabsorption disorders) AND (neoplasms) AND (previous use) AND (serum calcium levels) AND (vitamin D))"}
{"candidate_id": "LLM04281", "doc_id": "NCT03532620_exc", "case_bucket": "or", "source_criterion": "Past history of hypersensitivity to the study drug; Diagnosed diabetes; Severe liver disease (including ALT or AST=2.5-fold the normal upper limit), biliary obstruction; Ongoing treatment with cyclosporine within 2 weeks; Renal dysfunction, including endogenous creatinine clearance male<120ml/min, female<105ml/min, serum creatinine=2mg/dl (186umol/L), Renal function progressive decline, GFR<30ml•min-1•1.73m-2; Diagnosed or past history of ASCVD (including ACS, SCAD, revascularization, ICM, ischemic stroke, TIA, PASD, etc. SBP=180mmHg, or DBP=110mmHg; Ongoing treatment with Beta blockers, Diuretic; Secondary hypertension, including SAS, PA, RAS, pheochromocytoma, Cushing's syndrome, aorta diseases, drug induced hypertension; Ongoing treatment with statins, fibrates, and/or cation exchange resins within 2 weeks; Pancreatic disease; History of gastrectomy, short bowel syndrome; Ongoing hormone replacement therapy; Diagnosed or suspected malignant tumor; Familial hypercholesterolemia; Any diseases may limit the efficacy or safety of the study; Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation; IFG impaired fast glucose, FPG fasting plasma glucose, IGT impaired glucose tolerance, OGTT oral glucose tolerance test, PG plasma glucose, HbA1C hemoglobin A1C, LDL-C low-density lipoprotein cholesterol, TG triglycerides, SBP systolic blood pressure, DBP diastolic blood pressure, ALT alanine aminotransferase, AST aspartate aminotransferase, GFR glomerular filtration rate, ASCVD arteriosclerotic cardiovascular disease, ACS acute coronary syndrome, SCAD stable coronary artery disease, ICM ischemic cardiomyopathy, TIA transient ischemic attack, PASD peripheral atherosclerotic disease, SAS sleep apnea syndrome, PA primary aldosteronism, RAS renal arterial stenosis", "candidate_expression": "((186umol/L) AND (<105ml/min) AND (<120ml/min) AND (<30ml•min-1•1.73m-2) AND (=110mmHg) AND (=180mmHg) AND (=2.5-fold the normal upper limit) AND (=2mg/dl) AND (ACS) AND (ALT) AND (ASCVD) AND (AST) AND (Beta blockers) AND (Cushing's syndrome) AND (DBP) AND (Diagnosed) AND (Diuretic) AND (Familial hypercholesterolemia) AND (GFR) AND (History) AND (ICM) AND (Ongoing) AND (PA) AND (PASD) AND (Pancreatic disease) AND (Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation) AND (RAS) AND (Renal dysfunction) AND (Renal function) AND (SAS) AND (SBP) AND (SCAD) AND (Secondary hypertension) AND (Severe) AND (TIA) AND (aorta diseases) AND (biliary obstruction) AND (cation exchange resins) AND (cyclosporine) AND (diabetes) AND (drug induced) AND (endogenous creatinine clearance) AND (female) AND (fibrates) AND (gastrectomy) AND (hormone replacement therapy) AND (hypersensitivity) AND (hypertension) AND (ischemic stroke) AND (liver disease) AND (male) AND (malignant tumor) AND (pheochromocytoma) AND (progressive decline) AND (revascularization) AND (serum creatinine) AND (short bowel syndrome) AND (statins) AND (study drug) AND (suspected) AND (treatment) AND (within 2 weeks))"}
{"candidate_id": "LLM04282", "doc_id": "NCT02579200_exc", "case_bucket": "or", "source_criterion": "Inability to perform exercise tests Diagnosed psychiatric or cognitive disorders Progressive neurological or neuromuscular disorders having a major impact on exercise capacity", "candidate_expression": "((Inability to perform) AND (exercise tests) AND (impact on exercise capacity) AND ((cognitive disorders) OR (psychiatric disorders)) AND ((disorders Progressive neurological) OR (neuromuscular disorders Progressive)))"}
{"candidate_id": "LLM04283", "doc_id": "NCT02969187_inc", "case_bucket": "or", "source_criterion": "Fulfills NIH criteria for bariatric surgery Planned operation of laparoscopic Roux-en Y gastric bypass (LRYGB) or laparoscopic sleeve gastrectomy (LSG) as primary bariatric procedure", "candidate_expression": "((NIH criteria Fulfills) AND (bariatric surgery) AND ((laparoscopic Roux-en Y gastric bypass (LRYGB)) OR (laparoscopic sleeve gastrectomy (LSG))))"}
{"candidate_id": "LLM04284", "doc_id": "NCT02277041_exc", "case_bucket": "or", "source_criterion": "women undergoing caesarean section at less than 37 weeks of gestation. Hypertension with pregnancy. Cardiac and coronary diseases with pregnancy", "candidate_expression": "((Hypertension) AND (caesarean section) AND (gestation) AND (less than 37 weeks) AND (pregnancy) AND (undergoing) AND (women) AND ((Cardiac diseases) OR (coronary diseases)))"}
{"candidate_id": "LLM04285", "doc_id": "NCT01579604_inc", "case_bucket": "or", "source_criterion": "Cervical spine injury with functional loss in the upper extremity Greater than 4 months out from C-spine injury Stable motor recovery Medically stable International Classification for Surgery of the Hand in Tetraplegia of 0-5 at 6 months Grade 0 finger/thumb extension at 6 months Subjects fluent in English or when not fluent, an appropriate translator is present", "candidate_expression": "((0-5) AND (C-spine injury) AND (Cervical spine injury) AND (Grade 0) AND (Greater than 4 month) AND (International Classification for Surgery of the Hand in Tetraplegia) AND (Medically) AND (Stable) AND (Subjects fluent in English or when not fluent, an appropriate translator is present) AND (at 6 months) AND (extension) AND (functional loss) AND (motor recovery) AND (stable) AND (upper extremity) AND ((finger) OR (thumb)))"}
{"candidate_id": "LLM04286", "doc_id": "NCT03195153_exc", "case_bucket": "other", "source_criterion": "not diabetic patient; patients in dual antiplatelet therapy; patient with severe renal failure; patient poor responders", "candidate_expression": "((diabetic) AND (dual antiplatelet therapy) AND (not) AND (poor responders) AND (renal failure) AND (severe))"}
{"candidate_id": "LLM04287", "doc_id": "NCT03256864_exc", "case_bucket": "or", "source_criterion": "Patients who are recipients of multiple solid organ or islet cell tissue transplants, or have previously received an organ or tissue transplant. Patients who have a combined liver-kidney transplant. History of malignancy of any organ system (other than localized basal cell carcinoma of the skin), treated or untreated, within the past 5 years, regardless of whether there is evidence of local recurrence or metastases. Existence of any surgical, medical or mental conditions, other than the current transplantation, which, in the opinion of the investigator, might interfere with the objectives of the study. Pregnant or nursing (lactating) women.", "candidate_expression": "((History) AND (Pregnant) AND (any organ system) AND (combined liver-kidney transplant) AND (current) AND (lactating) AND (localized basal cell carcinoma of the skin) AND (malignancy) AND (might interfere with the objectives of the study) AND (multiple) AND (nursing) AND (other than) AND (previously) AND (transplantation) AND (within the past 5 years) AND (women) AND ((treated) OR (untreated)) AND ((medical conditions) OR (mental conditions) OR (surgical conditions)) AND ((islet cell tissue transplants) OR (solid organ transplants)) AND ((organ transplant) OR (tissue transplant)))"}
{"candidate_id": "LLM04288", "doc_id": "NCT02754583_exc", "case_bucket": "other", "source_criterion": "School districts that are too difficult to reach (more than a 3-hour walk from the farthest place reachable by a four-wheel drive vehicle) School districts in the 2 urban regions of the study area Refusal of village chief All residents residing near to the well sites that are randomly selected for this study. Refusal of participant [or parent/guardian]", "candidate_expression": "((Refusal of participant [or parent/guardian]) AND (School districts in the 2 urban regions of the study area) AND (School districts that are too difficult to reach) AND (more than a 3-hour) AND (near to the well sites) AND (residing) AND (walk from the farthest place reachable by a four-wheel drive vehicle))"}
{"candidate_id": "LLM04289", "doc_id": "NCT02992028_exc", "case_bucket": "or", "source_criterion": "age <45 or >80 allergies to medications used in the study history of renal diseases, a coagulation abnormality, a hepatic disease, or drug abuse definite radiographic evidence of osteoarthritis of the glenohumeral joint inflammatory arthritis including rheumatoid arthritis a history of acute trauma systemic conditions associated with chronic pain a history of infection an inability to understand the questionnaires", "candidate_expression": "((<45 or >80) AND (acute trauma) AND (age) AND (allergies) AND (associated with chronic pain) AND (chronic pain) AND (coagulation abnormality) AND (definite) AND (drug abuse) AND (glenohumeral joint) AND (hepatic disease) AND (history) AND (inability to understand the questionnaires) AND (infection) AND (inflammatory arthritis) AND (medications) AND (osteoarthritis) AND (radiographic) AND (radiographic evidence) AND (renal diseases) AND (rheumatoid arthritis) AND (systemic conditions) AND (used in the study))"}
{"candidate_id": "LLM04290", "doc_id": "NCT02632760_exc", "case_bucket": "or", "source_criterion": "Pregnancy Known hypersensitivity to study drug (ferric carboxymaltose or equivalent) or its excipients Known or suspected haemoglobinopathy/thalassaemia Bone marrow disease Haemochromatosis Renal dialysis Erythropoietin or IV iron in the previous 4 weeks", "candidate_expression": "((Bone marrow disease) AND (Erythropoietin) AND (Haemochromatosis) AND (IV iron) AND (Known) AND (Pregnancy) AND (Renal dialysis) AND (ferric carboxymaltose) AND (haemoglobinopathy) AND (hypersensitivity) AND (in the previous 4 weeks) AND (study drug) AND (suspected) AND (thalassaemia))"}
{"candidate_id": "LLM04291", "doc_id": "NCT01084993_exc", "case_bucket": "or", "source_criterion": "Intolerance or allergy to ASA, clopidogrel or ticlopidine precluding treatment for 12 months Concurrent participation in other investigational study Femoral sheath (artery)", "candidate_expression": "((Concurrent participation in other investigational study) AND (Femoral sheath (artery)) AND NOT (treatment for 12 months) AND ((Intolerance) OR (allergy)) AND ((ASA) OR (clopidogrel) OR (ticlopidine)))"}
{"candidate_id": "LLM04292", "doc_id": "NCT00182520_exc", "case_bucket": "or", "source_criterion": "Any other primary DSM-IV diagnosis; DSM-IV criteria for body dysmorphic disorder, bipolar affective disorder, schizophrenia, psychotic disorder, current alcohol/substance abuse. A previous adequate trial of topiramate Comorbid major depressive disorder diagnosis which predates OCD diagnosis Cognitive behavioural therapy or additional psychotherapy in past four months Allergy or hypersensitivity to topiramate BMI < 20 History of kidney stones", "candidate_expression": "((BMI < 20) AND (DSM-IV criteria) AND (diagnosis primary DSM-IV) AND (kidney stones History of) AND (major depressive disorder Comorbid predates OCD diagnosis) AND (topiramate in past four months) AND (topiramate previous) AND ((alcohol abuse) OR (bipolar affective disorder) OR (body dysmorphic disorder) OR (psychotic disorder,) OR (schizophrenia) OR (substance abuse)) AND ((Cognitive behavioural therapy) OR (psychotherapy additional)) AND ((Allergy) OR (hypersensitivity)))"}
{"candidate_id": "LLM04293", "doc_id": "NCT01932996_inc", "case_bucket": "other", "source_criterion": "Currently Homeless Smoked at least 100 cigarettes in lifetime AUDIT score of > or equal to 5, < or equal to 26 Aged 18 years or older Willing to attend study sessions and follow other study protocol", "candidate_expression": "((AUDIT score of > or equal to 5, < or equal to 26) AND (Aged 18 years or older) AND (Homeless) AND (Smoked at least 100 cigarettes) AND (Willing to attend study sessions and follow other study protocol))"}
{"candidate_id": "LLM04294", "doc_id": "NCT03328052_inc", "case_bucket": "or", "source_criterion": "Patients with a clinical diagnosis of depression who in the judgement of their physician require medication management may be eligible for enrollment. A score of 10 or more on the PHQ-9 instrument will be required for enrollment. Some practices utilize the PHQ-2 and PHQ-9 are part of routine screening for depression. If the tests are performed routinely, they do not need to be repeated for study eligibility, and may be performed prior to informed consent for this study. If, however, the PHQ-9 is not routinely performed, informed consent must be performed prior to administration. Patients with a score below 10 will be considered screen failures and will not be enrolled or offered the MYnd testing. Patients with non-psychotic comorbid conditions may be included. Patients must be either medication treatment naïve for behavioral illnesses or have no active medication treatments for at least 1 month prior to enrollment. Prohibited medications at the time of enrollment will include stimulants, benzodiazepines and THC. Prior therapy with these agents is permitted with a washout of >30 days. Patients must have private medical insurance coverage through Horizon Blue Cross Blue Shield. This is limited to insured commercial members, including HMO, and excluding, for the avoidance of doubt, members of self-insured customers or Medicare or Medicaid programs.", "candidate_expression": "((PHQ-9 score of 10 or more) AND (behavioral illnesses) AND (depression) AND (medication) AND (non-psychotic conditions) AND NOT (medication active for at least 1 month prior to enrollment) AND NOT (medication) AND ((THC) OR (benzodiazepines) OR (stimulants)))"}
{"candidate_id": "LLM04295", "doc_id": "NCT00396734_inc", "case_bucket": "scope", "source_criterion": "Methadone-maintained cocaine-dependent patients use between 1g to 2g a day; 1 to 3 times a week", "candidate_expression": "((1 to 3 times a week) AND (1g to 2g a day) AND (Methadone) AND (Methadone-maintained) AND (cocaine-dependent))"}
{"candidate_id": "LLM04296", "doc_id": "NCT03420638_exc", "case_bucket": "or", "source_criterion": "Presence of severe systemic disease Presence of coagulation disorders Current or previous history of analgesic dependence Allergy to any of the drugs used in the study Women pregnant or lactating, or women planning to become pregnant Presence of hearing loss Presence of cardiovascular comorbidities Presence of hepatic comorbidities Presence of kidney comorbidities Presence of cognitive disabilities", "candidate_expression": "((Allergy) AND (Women) AND (analgesic) AND (analgesic dependence) AND (cardiovascular comorbidities) AND (coagulation disorders) AND (cognitive disabilities) AND (drugs used in the study) AND (hearing loss) AND (hepatic comorbidities) AND (history) AND (kidney comorbidities) AND (planning to become) AND (severe) AND (systemic disease) AND (women) AND ((lactating) OR (pregnant)) AND ((Current) OR (previous)))"}
{"candidate_id": "LLM04297", "doc_id": "NCT00500500_exc", "case_bucket": "or", "source_criterion": "patient already treated by medicines which could interfere with the study low level of vitamin B12 and folate which are considered as clinically relevant clinically relevant pathologies (eg: pulmonary illness, cardiovascular illness; evolutive cancer, neurological illness, blood illness….)", "candidate_expression": "((folate level of) AND (level of vitamin B12) AND (low) AND ((blood illness) OR (cardiovascular illness) OR (evolutive cancer) OR (neurological illness) OR (pulmonary illness)))"}
{"candidate_id": "LLM04298", "doc_id": "NCT02589691_inc", "case_bucket": "other", "source_criterion": "age <2 years indication of general anesthesia with tracheal intubation inhalational induction scheduled written informed consent of both parents", "candidate_expression": "((age <2 years) AND (general anesthesia indication) AND (inhalational induction scheduled) AND (tracheal intubation) AND (written informed consent of both parents))"}
{"candidate_id": "LLM04299", "doc_id": "NCT02985710_exc", "case_bucket": "or", "source_criterion": "Subjects with cognitive, psychiatric, or other problems that preclude informed consent. Patients with history of glucose intolerance or diabetes. Patient on chemotherapy People with any open or bleeding wounds at any sensor plate contact surface location People with any type of implantable device People with missing hand(s) and/or leg(s) Pregnant women or women who are uncertain about a possible pregnancy Patients sensitive to chemicals used to induce sweating Patients with heat intolerance Patients with bleeding disorders Patients on current anticoagulant therapy Patients with keloids on the intended biopsy site People with hypersensitivity to local amide-type anesthetics", "candidate_expression": "((Pregnant) AND (anticoagulant therapy) AND (at any sensor plate contact surface location) AND (bleeding disorders) AND (bleeding wounds) AND (chemotherapy) AND (cognitive problems) AND (current) AND (diabetes) AND (glucose intolerance) AND (heat intolerance) AND (history) AND (hypersensitivity) AND (implantable device) AND (keloids) AND (local amide-type anesthetics) AND (missing hand) AND (missing leg) AND (on the intended biopsy site) AND (open wounds) AND (other problems that preclude informed consent) AND (possible pregnancy) AND (psychiatric problems) AND (sensitive to chemicals used to induce sweating))"}
{"candidate_id": "LLM04300", "doc_id": "NCT01346436_exc", "case_bucket": "other", "source_criterion": "Age <18 years old Patient unable to communicate or to understand the study Patient refusing to participate to the study contraindication to laparoscopy", "candidate_expression": "((<18 years old) AND (Age) AND (Patient refusing to participate to the study) AND (Patient unable to communicate or to understand the study) AND (contraindication) AND (laparoscopy))"}
```
