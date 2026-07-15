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
{"candidate_id": "LLM05976", "doc_id": "NCT03561753_exc", "case_bucket": "or", "source_criterion": "Tuberculosis resistant to any of the study drugs (isoniazid, rifampin, EMB, PZA, CFZ, Pto) Unable to take oral medications. History of allergy or intolerance to any of the study drugs Serum aminotransferase (AST or ALT) 3x upper limit of normal or higher Pregnant or nursing females, or plan to become pregnant or nurse during the study period Males planning to conceive a child during the study or within 6 months of cessation of treatment. Any treatment directed against active tuberculosis within 6 months preceding initiation of study drugs. Suspected or documented tuberculosis involving the central nervous system and/or bones and/or joints, and/or miliary tuberculosis and/or pericardial tuberculosis. HIV infected HBV infected or HCV infected (these increase the risk of TB-drug induced hepatotoxicity) Weight less than 40.0 kg. Known allergy or intolerance to any of the study medications. Individuals will be excluded from enrollment if, at the time of enrollment, their M. tuberculosis isolate is already known to be resistant to any of the study drugs. QTcF > 500 msec Other medical conditions, that, in the investigator's judgment, make study participation not in the individual's best interest. Current or planned incarceration or other involuntary detention Having participated in other clinical studies with dosing of investigational agents within 8 weeks prior to trial start or currently enrolled in an investigational study that includes treatment with medicinal agents. Subjects who are participating in observational studies or who are in a follow up period of a trial that included drug therapy may be considered for inclusion.", "candidate_expression": "((3x upper limit of normal or higher) AND (> 500 msec) AND (ALT) AND (AST) AND (CFZ) AND (Current) AND (EMB) AND (HBV infected) AND (HCV infected) AND (HIV infected) AND (History) AND (M. tuberculosis isolate) AND (Males) AND (PZA) AND (Pregnant) AND (Pto) AND (QTcF) AND (Serum aminotransferase) AND (Suspected) AND (Tuberculosis) AND (Unable to take oral medications) AND (Weight) AND (active) AND (allergy) AND (become pregnant) AND (bones) AND (central nervous system) AND (cessation of treatment) AND (conceive a child) AND (currently) AND (documented) AND (during the study) AND (during the study period) AND (enrolled in an investigational study) AND (females) AND (incarceration) AND (intolerance) AND (investigational agents) AND (involuntary detention) AND (isoniazid) AND (joints) AND (less than 40.0 kg) AND (medicinal agents) AND (miliary tuberculosis) AND (nurse) AND (nursing) AND (participated in other clinical studies) AND (pericardial tuberculosis) AND (plan to) AND (planned) AND (planning to) AND (resistant to) AND (resistant to any of the study drugs) AND (rifampin) AND (study drugs) AND (study medications) AND (the study) AND (treatment) AND (trial start) AND (tuberculosis) AND (within 6 months of cessation of treatment) AND (within 6 months preceding initiation of study drugs) AND (within 8 weeks prior to trial start))"}
{"candidate_id": "LLM05977", "doc_id": "NCT02531724_inc", "case_bucket": "other", "source_criterion": "Patients in the cardiothoracic intensive care after cardiac surgery with cardiopulmonary bypass Acute kidney injury, defined as increase in S-creatinine 50% or 27 mol/L Normal S-creatinine before surgery", "candidate_expression": "((Acute kidney injury) AND (S-creatinine Normal before surgery) AND (cardiac surgery) AND (cardiopulmonary bypass) AND (cardiothoracic intensive care after cardiac surgery with cardiopulmonary bypass) AND (increase in S-creatinine 50% or 27 mol/L) AND (surgery))"}
{"candidate_id": "LLM05978", "doc_id": "NCT02483715_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((PPIs) AND (antibiotics) AND (bismuth salts) AND (bleeding serious during the course of the ulcer) AND (gastric surgery previous) AND (hypersensitivity history of) AND (illness serious concomitant) AND (malignant tumor any kind) AND (nursing) AND (pregnant) AND (test drugs) AND (woman))"}
{"candidate_id": "LLM05979", "doc_id": "NCT02590822_inc", "case_bucket": "or", "source_criterion": "Capacity to provide informed consent before any trial-related activities Established T2DM (=3months) HbA1c = 9% if on triple therapy or = 10% on diet & exercise or monotherapy or dual therapy Current glucose lowering therapy either mono, dual or triple of any combination of metformin, sulphonylurea, DPP-IV inhibitor, GLP-1 therapy or an SGLT2 +/- diet and exercise Poorly managed diet controlled diabetes (with HbA1c > 6.5% , not currently taking any glucose lowering therapy, meeting BMI inclusion range) Body mass index > 30Kg/m2 or > 27.5 Kg/m2 (South Asian), Diagnosis of T2DM before the age of 60 years of age Age =18 and = 65 years", "candidate_expression": "((=18 and = 65 years) AND (=3months) AND (> 6.5%) AND (Age) AND (Body mass index) AND (Capacity to provide informed consent before any trial-related activities) AND (HbA1c) AND (T2DM) AND (age) AND (before 60 years of age) AND (diabetes) AND (glucose lowering therapy) AND (not) AND ((DPP-IV inhibitor,) OR (GLP-1 therapy) OR (SGLT2) OR (diet) OR (exercise) OR (metformin) OR (sulphonylurea)) AND ((> 27.5 Kg/m2) OR (> 30Kg/m2)) AND ((= 10%) OR (= 9%)))"}
{"candidate_id": "LLM05980", "doc_id": "NCT03070847_inc", "case_bucket": "other", "source_criterion": "age > 18 y.o. American Society of Anesthesiologists Physical Status Classification (ASA) 1-2 signed informed consent form after reading the information about the study and talking with one of the investigators", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists Physical Status Classification 1-2) AND (age > 18 y.o) AND (signed informed consent form after reading the information about the study and talking with one of the investigators))"}
{"candidate_id": "LLM05981", "doc_id": "NCT01720394_exc", "case_bucket": "other", "source_criterion": "fetal anomalies contra-indications for medical induction of labor placental pathologies St.p. surgery with opening the uterine cavity (incl. caesarean section) PROM multiple gestations < 37-0 weeks of gestation St.p. cervical tear", "candidate_expression": "((< 37-0 weeks) AND (PROM) AND (St.p.) AND (caesarean section) AND (cervical tear) AND (contra-indications) AND (fetal anomalies) AND (gestation) AND (medical induction of labor) AND (multiple gestations) AND (placental pathologies) AND (surgery with opening the uterine cavity))"}
{"candidate_id": "LLM05982", "doc_id": "NCT00396734_inc", "case_bucket": "scope", "source_criterion": "Methadone-maintained cocaine-dependent patients use between 1g to 2g a day; 1 to 3 times a week", "candidate_expression": "((Methadone) AND (cocaine-dependent Methadone-maintained 1g to 2g a day 1 to 3 times a week))"}
{"candidate_id": "LLM05983", "doc_id": "NCT02360631_inc", "case_bucket": "other", "source_criterion": "Self-identified African American Smokes = 1 cigarette per day (cpd) Smoke on = 25 days of the past 30 days Functioning telephone Interested in quitting smoking Interested in taking 3 months of varenicline Willing to complete all study visits", "candidate_expression": "((= 1 cigarette per day) AND (= 25 days of the past 30 days) AND (African American) AND (Interested) AND (Interested in quitting smoking) AND (Interested in taking 3 months of varenicline) AND (Smoke) AND (Smokes) AND (Willing to complete all study visits) AND (quitting smoking))"}
{"candidate_id": "LLM05984", "doc_id": "NCT00586898_exc", "case_bucket": "or", "source_criterion": "Clinically significant cardiac disease (New York Heart Association Class III/IV),or severe debilitating puhnonary disease. Uncontrolled serious active infection. Anticipated survival of less than 3 months. Active CNS or epiduraltumor Inability or unwillingness to comply with the treatment protocol, follow-up, or research tests.", "candidate_expression": "((Anticipated survival) AND (Class III/IV) AND (New York Heart Association) AND (Uncontrolled serious) AND (cardiac disease) AND (debilitating puhnonary disease) AND (infection) AND (less than 3 months) AND (severe) AND (significant) AND ((CNS tumor) OR (epiduraltumor)) AND ((Inability) OR (unwillingness)) AND ((comply with the treatment protocol) OR (follow-up) OR (research tests)))"}
{"candidate_id": "LLM05985", "doc_id": "NCT02951520_inc", "case_bucket": "other", "source_criterion": "Adult patients scheduled for arthroscopic knee ligament reconstruction", "candidate_expression": "((Adult) AND (arthroscopic knee ligament reconstruction) AND (scheduled))"}
{"candidate_id": "LLM05986", "doc_id": "NCT02499185_inc", "case_bucket": "other", "source_criterion": "= 18 years High risk patients: General Surgery AKI Risk Index Class III, IV or V Major abdominal surgery", "candidate_expression": "((= 18 years = 18 years) AND (General Surgery AKI Risk Index Class III, IV or V) AND (High risk) AND (Major abdominal surgery))"}
{"candidate_id": "LLM05987", "doc_id": "NCT01803438_exc", "case_bucket": "or", "source_criterion": "Subject has documented typical atrial flutter. Subject has any history of successful or unsuccessful treatment of AF with class I or III antiarrhythmic or sotalol with the intention to prevent an AF recurrence. Patients pretreated with above AAD at maximum 48 hours with the intention to convert an AF episode are allowed. Subject had any previous left atrial ablation. Subject had any previous cardiac surgery, e.g. prosthetic valves. Subject has permanent pacemaker or defibrillator implant. Subject has 2° type II, 3° degree AV-block or left/right bundle branch block pattern. Subject has unstable angina pectoris. Subject has history of previous myocardial infarction or percutaneous intervention during the last three months. Subject has symptomatic carotid stenosis. Subject has chronic obstructive pulmonary disease with detected pulmonary hypertension or any other evidence of significant lung disease. Subject has any contraindication for oral anticoagulation. Subject has any history of previous transient ischemic attack or stroke. Subject has known intra-cardiac thrombus formation. Subject has any significant congenital heart defect corrected or not (except for patent foramen ovale that is allowed). Subject has evidence of congestive heart failure (NYHA class II, III or IV) in sinus rhythm. Subject has hypertrophic cardiomyopathy. Subject has abnormal long or short QT interval, signs of Brugada syndrome, known inheriting ion channel disease on the family, arrhythmogenic right ventricular dysplasia. Subject has sarcoidosis. Subject has pulmonary vein stent. Subject has myxoma. Exclusion criteria based on laboratory abnormalities Subject has thrombocytosis (platelet count > 600,000 / µl) or thrombocytopenia (platelet count <100,000 / µl). Subject has any untreated or uncontrolled hyperthyroidism or hypothyroidism. Subject has renal dysfunction with glomerular filtration rate < 60 ml / min. Subject has known cryoglobulinaemia. General exclusion criteria Subject has a reversible causes for AF like hyperthyroidism and alcoholism. Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled. Subject is a breastfeeding woman. Subject has an active systemic infection. Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators. Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state. Legal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up. Subject has a life expectancy of = 1 year. Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager.", "candidate_expression": "((2° type II AV-block) AND (3° degree AV-block) AND (AF class I class III) AND (Brugada syndrome) AND (NYHA class II III IV) AND (QT interval short) AND (Subject is a breastfeeding woman) AND (Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled) AND (Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager) AND (Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators) AND (Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state) AND (alcoholism) AND (antiarrhythmic) AND (atrial ablation left) AND (atrial flutter) AND (cardiac surgery) AND (carotid stenosis symptomatic) AND (chronic obstructive pulmonary disease) AND (congenital heart defect significant) AND (congestive heart failure) AND (contraindication) AND (cryoglobulinaemia) AND (defibrillator implant) AND (egal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up) AND (glomerular filtration rate < 60 ml / min) AND (hyperthyroidism) AND (hyperthyroidism uncontrolled) AND (hypertrophic cardiomyopathy long) AND (hypothyroidism) AND (inheriting ion channel disease) AND (inheriting ion channel disease on the family) AND (intra-cardiac thrombus) AND (left bundle branch block) AND (life expectancy = 1 year) AND (lung disease significant) AND (myocardial infarction) AND (myxoma) AND (oral anticoagulation) AND (percutaneous intervention) AND (permanent pacemaker) AND (platelet count <100,000 / µl untreated) AND (platelet count > 600,000 / µl) AND (prosthetic valves) AND (pulmonary hypertension) AND (pulmonary vein stent) AND (renal dysfunction) AND (right bundle branch block) AND (right ventricular dysplasia arrhythmogenic) AND (sarcoidosis) AND (sinus rhythm) AND (sotalol) AND (stroke) AND (systemic infection active) AND (thrombocytopenia) AND (thrombocytosis) AND (transient ischemic attack) AND (unstable angina pectoris) AND NOT (patent foramen ovale))"}
{"candidate_id": "LLM05988", "doc_id": "NCT01799681_inc", "case_bucket": "other", "source_criterion": "diagnosed with PD by a neurologist (Fahn and Elton, 1987); aged 30 to 85 years; at modified Hoehn and Yahr (H&Y) stage 1.5 to 3 (Hoehn and Yahr ,1967; Goetz et al., 2004); able and willing to give written consent for participation in the study; living at home in the community; able to walk independently for 30 metres with or without an assistive device.", "candidate_expression": "((30 to 85 years) AND (PD) AND (able and willing to give written consent for participation in the study;) AND (able to walk independently with or without an assistive device) AND (aged) AND (by a neurologist) AND (for 30 metres) AND (living at home in the community) AND (modified Hoehn and Yahr (H&Y)) AND (stage 1.5 to 3))"}
{"candidate_id": "LLM05989", "doc_id": "NCT03263481_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05990", "doc_id": "NCT01743755_inc", "case_bucket": "or", "source_criterion": "18 years or older Chest radiograph showing new opacities. Cough Production of sputum Temp >38,0 °C or <36,0 °C Audible abnormalities by chest examination compatible with pneumonia Leukocytosis (>10.000 cells/mm3), leftward shift (>10%) or leucopenia (<4000 cells/mm3) C-reactive protein > 15 mg/l (three fold higher than the upper limit of normal)", "candidate_expression": "((18 or older) AND (<36,0 °C) AND (<4000 cells/mm3) AND (> 15 mg/l) AND (>10.000 cells/mm3) AND (>38,0 °C) AND (Audible abnormalities) AND (C-reactive protein) AND (Chest radiograph) AND (Cough) AND (Leukocytosis) AND (Temp) AND (chest examination) AND (leftward shift >10%) AND (leucopenia) AND (new) AND (opacities) AND (pneumonia) AND (sputum) AND (three fold higher than the upper limit of normal) AND (years))"}
{"candidate_id": "LLM05991", "doc_id": "NCT01890759_inc", "case_bucket": "or", "source_criterion": "Male and female subjects aged 9 to 17 months on the day of inclusion Informed consent form has been signed and dated by the parent(s) or other legally acceptable representative(s) (if applicable) Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.", "candidate_expression": "((9 to 17 months) AND (Male) AND (Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.) AND (aged) AND (female) AND (on the day of inclusion) AND (the day of inclusion))"}
{"candidate_id": "LLM05992", "doc_id": "NCT02942303_inc", "case_bucket": "other", "source_criterion": "Consecutive 30 female patients presenting to our clinic for brow lifting with botulinum toxin will be randomized to receive one of the two injection techniques", "candidate_expression": "((botulinum toxin) AND (brow lifting) AND (female 30))"}
{"candidate_id": "LLM05993", "doc_id": "NCT02318446_inc", "case_bucket": "other", "source_criterion": "Diagnosed epileptic patients of either sex with age between 10-19 yrs (<19yrs), coming to the medicine Out Patient /In Patient Departments and undergoing AED therapy for more than 6 months. Epileptics with high homocysteine levels i.e. > 10.9 µmol/L (Normal homocysteine levels are 4.3-9.9 µmol/L for male and 3.3-7.2 µmol/L for female adolescent and a high homocysteine concentration is deaned as at least 11.4 µmol/L for male and at least 10.4 µmol/L for female. Gender mean of high homocysteine concentration is 10.9 µmol/L) [5]", "candidate_expression": "((<19yrs) AND (> 10.9 µmol/L) AND (AED therapy) AND (In Patient Departments) AND (Out Patient Departments) AND (age) AND (between 10-19 yrs) AND (epileptic) AND (for more than 6 months) AND (high) AND (homocysteine levels))"}
{"candidate_id": "LLM05994", "doc_id": "NCT02957877_exc", "case_bucket": "or", "source_criterion": "History of intolerance to LMWHs during HD Receiving warfarin or other oral anticoagulant Pregnant patients", "candidate_expression": "((HD) AND (LMWHs during HD) AND (Pregnant) AND (intolerance) AND ((oral anticoagulant other) OR (warfarin)))"}
{"candidate_id": "LLM05995", "doc_id": "NCT02845427_inc", "case_bucket": "other", "source_criterion": "Primary total hip arthroplasty (THA)", "candidate_expression": "((Primary) AND (THA) AND (total hip arthroplasty))"}
{"candidate_id": "LLM05996", "doc_id": "NCT03350659_exc", "case_bucket": "or", "source_criterion": "Drug-induced hypotension, if necessary, evaluate patient after discontinuing the causative drug for one month Heart failure or Chronic renal failure Severe supine hypertension (Systolic Blood Pressure >180 or Diastolic Blood Pressure>110mmHg) Pregnant women, breast-feeding Unable to perform questionnaire", "candidate_expression": "((Unable to perform questionnaire) AND (hypotension Drug-induced) AND (supine hypertension Severe) AND (women) AND ((Pregnant) OR (breast-feeding)) AND ((Chronic renal failure) OR (Heart failure)) AND ((Diastolic Blood Pressure >110mmHg) OR (Systolic Blood Pressure >180)))"}
{"candidate_id": "LLM05997", "doc_id": "NCT02321202_exc", "case_bucket": "or", "source_criterion": "Contraindication for hepatectomy, including gastrointestinal hemorrhage, severe hemorrhagic disorders, explicit acute nonspecific infectious lesion, overt ascites, Child-Pugh Score C, indocyanine green retention rate at 15min (ICGR15)＞30%(12), serum hepatitis B virus (HBV)-DNA＞126 copies/ml and serum alanine aminotransferase (ALT) ＞ 2×ULN, serum triglycerides＞2.0 mmol/L, circulatory shock, stroke, acute myocardial infarction, renal failure, coma of unknown cause Pregnancy Age of＜18y or＞75y Performed intraoperative ablation Unresectable tumor during operation Allergic reactions against fish or egg proteins", "candidate_expression": "((Age) AND (Allergic reactions) AND (C) AND (Child-Pugh Score) AND (Contraindication for hepatectomy) AND (Pregnancy) AND (Unresectable tumor) AND (acute) AND (acute myocardial infarction) AND (ascites) AND (circulatory shock) AND (coma) AND (egg proteins) AND (fish proteins) AND (gastrointestinal hemorrhage) AND (hemorrhagic disorders) AND (hepatectomy) AND (indocyanine green retention rate at 15min (ICGR15)) AND (infectious lesion) AND (intraoperative ablation) AND (nonspecific) AND (overt) AND (renal failure) AND (serum alanine aminotransferase (ALT)) AND (serum hepatitis B virus (HBV)-DNA) AND (serum triglycerides) AND (severe) AND (stroke) AND (unknown cause) AND (＜18y or＞75y) AND (＞ 2×ULN) AND (＞126 copies/ml) AND (＞2.0 mmol/L) AND (＞30%))"}
{"candidate_id": "LLM05998", "doc_id": "NCT02068365_inc", "case_bucket": "or", "source_criterion": "Male & female patients >= 18 and < 70 years of age Positive HBeAg before starting NA treatment Treated by a single NA (lamivudine, adefovir, entecavir or tenofovir) for 6 months to 5 years Developed HBeAg seroconversion (HBeAg negative and ant-HBe negative) with undetectable HBV DNA by PCR based assay on NA treatment. Negative urine or serum pregnancy test (for women of childbearing potential) documented within the 24-hour period prior to the first dose of test drug. Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion", "candidate_expression": "((>= 18 and < 70 years) AND (Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion) AND (HBV DNA) AND (HBeAg) AND (NA) AND (Negative) AND (PCR based assay) AND (Positive) AND (Treated) AND (age) AND (before starting NA treatment) AND (childbearing potential) AND (for 6 months to 5 years) AND (single) AND (starting NA treatment) AND (the first dose of test drug) AND (treatment) AND (undetectable) AND (within the 24-hour period prior to the first dose of test drug) AND (women) AND ((Male) OR (female)) AND ((adefovir) OR (entecavir) OR (lamivudine) OR (tenofovir)) AND ((HBeAg) OR (seroconversion)) AND ((HBeAg) OR (negative)) AND ((ant-HBe) OR (negative)) AND ((serum pregnancy test) OR (urine pregnancy test)))"}
{"candidate_id": "LLM05999", "doc_id": "NCT00426751_inc", "case_bucket": "or", "source_criterion": "Women must be postmenopausal (i.e.12 months without menstrual period), or surgically sterile, i.e. women of child bearing potential are not allowed to be included into the study. In cases of doubt a pregnancy test should be performed. (NB -post menopausal women currently receiving hormone replacement are permissible) Acute myocardial infarction < 12 h defined as: 1. Angina or equivalent symptoms > 20 min and 2. ST elevation in 2 contiguous ECG leads (= 2 mm precordial lead, = 1 mm limb lead). This ECG recording serves as baseline ECG, i.e. ECG I. Planned primary percutaneous coronary intervention The subject has given written informed, dated consent to participate in the study", "candidate_expression": "((1 mm) AND (12 months) AND (2) AND (2 mm) AND (< 12 h) AND (> 20 min) AND (Acute myocardial infarction) AND (Angina) AND (Angina symptoms) AND (Planned) AND (ST elevation) AND (Women) AND (child bearing potential) AND (contiguous ECG leads) AND (doubt) AND (given written informed consent) AND (limb lead) AND (menstrual period) AND (not) AND (postmenopausal) AND (precordial lead) AND (pregnancy test) AND (primary percutaneous coronary intervention) AND (surgically sterile) AND (without) AND (women))"}
{"candidate_id": "LLM06000", "doc_id": "NCT01313676_exc", "case_bucket": "or", "source_criterion": "Pregnancy: Women who are pregnant or lactating. Asthma: Subjects with a current diagnosis of asthma. (Subjects with a prior history of asthma are eligible if they also have a current diagnosis of COPD). alpha 1-antitrypsin deficiency: Subjects with known alpha-1 antitrypsin deficiency as the underlying cause of COPD. Other respiratory disorders: Subjects with active tuberculosis, lung cancer, bronchiectasis, sarcoidosis, pulmonary fibrosis, pulmonary hypertension, interstitial lung diseases or other active pulmonary diseases. Lung resection or transplantation: Subjects with lung volume reduction surgery within the 12 months prior to Screening or having had a lung transplant. A moderate/severe COPD exacerbation that has not resolved at least 14 days prior to Visit 1 and at least 30 days following the last dose of oral corticosteroids (if applicable). Current severe heart failure (New York Heart Association class IV). Subjects will also be excluded if they have a known ejection fraction of <30% or if they have an implantable cardioverter defibrillator (ICD). Other diseases/abnormalities: Any life-threatening condition with life expectancy <3 years, other than vascular disease or COPD, that might prevent the subject from completing the study. End stage chronic renal disease: Subjects will be excluded if on renal replacement therapy (hemodialysis or peritoneal). Drug/food allergy: Subjects with a history of hypersensitivity to any of the study medications (e.g. beta-agonists, corticosteroid) or components of the inhalation powder (e.g. lactose, magnesium stearate). In addition, patients with a history of severe milk protein allergy that, in the opinion of the study physician, contraindicates the subject's participation will also be excluded. Drug/alcohol abuse: Subjects with a known or suspected history of alcohol or drug abuse within the last 2 years. Oxygen therapy: Subjects receiving treatment with long-term oxygen therapy (LTOT) or nocturnal oxygen therapy required for greater than 12 hours a day. Oxygen prn use (i.e. <=12 hours per day) is not exclusionary. Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures. Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study. Additional medication: Use of the following medications within the following time intervals prior to Visit 1 or during the study (unless otherwise specified): Medication No use within the following time intervals prior to Screening or thereafter at any time during the study (unless otherwise specified) Inhaled Long acting beta-agonists (LABA) 48 hours ICS/LABA combination products 48 hours Inhaled corticosteroids 48 hours Tiotropium 1 week Systemic, Oral, parenteral, intra-articular corticosteroids 30 days (oral and systemic corticosteroids may be used to treat COPD exacerbations during the study) Cytochrome P450 3A4 strong inhibitors including but not limited to antiretrovirals (protease inhibitors) (e.g.Indinavir, Nelfinavir, Ritonavir, Saquinavir); Imidazole and Triazole anti-fungals (e.g. Ketaconazole, Itraconazole); Clarithromycin, Telithromycin, Amiodarone, and Nefazodone 6 weeks Grapefruit is allowed up to Visit 1, then limited to no more than one glass of grapefruit juice (250 mL/ 8 ounces) or one grapefruit per day Any other investigational drug 30 days or 5 half lives whichever is longer.", "candidate_expression": "((1 week) AND (30 days) AND (48 hours) AND (6 weeks) AND (<3 years) AND (<30%) AND (Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study.) AND (Asthma) AND (COPD) AND (COPD exacerbation) AND (COPD exacerbations) AND (End stage chronic renal disease) AND (Grapefruit) AND (Imidazole anti-fungals) AND (New York Heart Association) AND (No) AND (Other respiratory disorders) AND (Pregnancy: Women who are pregnant or lactating.) AND (Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures.) AND (Screening) AND (Triazole anti-fungals) AND (alpha 1-antitrypsin deficiency) AND (alpha-1 antitrypsin deficiency) AND (asthma) AND (at least 14 days prior to Visit 1) AND (at least 30 days following the last dose of oral corticosteroids) AND (class IV) AND (current) AND (during the study) AND (greater than 12 hours a day) AND (heart failure) AND (history) AND (hypersensitivity) AND (in the opinion of the study physician, contraindicates the subject's participation will also be excluded) AND (investigational drug) AND (life expectancy) AND (life-threatening condition) AND (lung transplant) AND (lung volume reduction surgery) AND (milk protein allergy) AND (not) AND (other than) AND (prior) AND (protease inhibitors) AND (renal replacement therapy) AND (resolved) AND (severe) AND (that might prevent the subject from completing the study) AND (the last dose of oral corticosteroids) AND (the study) AND (treat COPD exacerbations) AND (within the 12 months prior to Screening) AND (within the last 2 years) AND ((Oral) OR (Systemic) OR (intra-articular) OR (parenteral)) AND ((oral) OR (systemic)) AND ((Cytochrome P450 3A4 strong inhibitors) OR (ICS/LABA combination products) OR (Inhaled Long acting beta-agonists (LABA)) OR (Inhaled corticosteroids) OR (Tiotropium) OR (corticosteroids)) AND ((Itraconazole) OR (Ketaconazole)) AND ((Amiodarone) OR (Clarithromycin) OR (Nefazodone) OR (Telithromycin) OR (antiretrovirals)) AND ((30 days) OR (5 half lives)) AND ((Indinavir) OR (Nelfinavir) OR (Ritonavir) OR (Saquinavir)) AND ((active pulmonary diseases) OR (bronchiectasis) OR (interstitial lung diseases) OR (lung cancer) OR (pulmonary fibrosis) OR (pulmonary hypertension) OR (sarcoidosis) OR (tuberculosis)) AND ((Lung resection) OR (transplantation)) AND ((having had a lung transplant) OR (with lung volume reduction surgery)) AND ((moderate) OR (severe)) AND ((ejection fraction) OR (implantable cardioverter defibrillator (ICD))) AND ((COPD) OR (vascular disease)) AND ((hemodialysis) OR (peritoneal)) AND ((Drug allergy) OR (food allergy)) AND ((beta-agonists) OR (corticosteroid)) AND ((components of the inhalation powder) OR (study medications)) AND ((lactose) OR (magnesium stearate)) AND ((Drug abuse) OR (alcohol abuse)) AND ((alcohol abuse) OR (drug abuse)) AND ((long-term oxygen therapy (LTOT)) OR (nocturnal oxygen therapy)) AND ((Screening) OR (any time during the study)))"}
```
