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
{"candidate_id": "LLM06751", "doc_id": "NCT02548013_inc", "case_bucket": "other", "source_criterion": "1. PPROM with gestational age between 27 to 34 weeks 2. Cephalic presentation 3. Clear amniotic fluid 4. Oral temperature > 38 C 5. Near distance from the hospital (the patient can reach hospital within one hour ) 6. Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home . 7. Maternal and fetal condition remain stable after hospitalization for 72 hours", "candidate_expression": "((> 38 C) AND (Cephalic presentation) AND (Clear amniotic fluid) AND (Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home .) AND (Maternal condition) AND (Near distance from the hospital (the patient can reach hospital within one hour )) AND (Oral temperature) AND (PPROM) AND (after hospitalization for 72 hours) AND (between 27 to 34 weeks) AND (fetal condition) AND (gestational age) AND (hospitalization) AND (stable))"}
{"candidate_id": "LLM06752", "doc_id": "NCT02535299_inc", "case_bucket": "or", "source_criterion": "Newly dignosised type 2 diabetes according to WHO criteria.glycated hemoglobin (HbA1c) was more than 10%; Seronegative for antibodies against insulin, islet cells and glutamic acid decarboxylase (GAD);", "candidate_expression": "((glycated hemoglobin (HbA1c) more than 10%) AND (type 2 diabetes Newly dignosised WHO criteria) AND NOT (antibodies insulin islet cells glutamic acid decarboxylase (GAD)))"}
{"candidate_id": "LLM06753", "doc_id": "NCT01908465_exc", "case_bucket": "or", "source_criterion": "IBS subtype with constipation medication: antidepressants or H1-receptor antagonists pregnancy, breast feeding co-morbidity: severe kidney- and/or liver disease or other gastrointestinal diseases", "candidate_expression": "((H1-receptor antagonists) AND (IBS subtype) AND (antidepressants) AND (breast feeding) AND (constipation) AND (gastrointestinal diseases) AND (kidney disease) AND (liver disease) AND (pregnancy) AND (severe))"}
{"candidate_id": "LLM06754", "doc_id": "NCT02714725_inc", "case_bucket": "or", "source_criterion": "Adult patients aged (>18), males and females, undergoing elective coronary artery bypass graft (CABG) surgery with cardiopulmonary bypass (CPB).", "candidate_expression": "((>18) AND (CABG) AND (CPB) AND (aged) AND (cardiopulmonary bypass) AND (elective) AND (females) AND (males) AND (surgery coronary artery bypass graft))"}
{"candidate_id": "LLM06755", "doc_id": "NCT02965443_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetes Age 18 - 75 years Anti-GAD antibodies negative (Glutamic Acid Decarboxylase) C-peptide levels = 1.5 ng/mL Fasting blood glucose > 126 mg/dl HbA1c 8.0 - 10.5 % BMI 25.0 - 45.0 kg/m2 Previous therapy with BBIT (basal insulin and at least once daily bolus insulin)", "candidate_expression": "((18 - 75 years) AND (25.0 - 45.0 kg/m2) AND (8.0 - 10.5 %) AND (= 1.5 ng/mL) AND (> 126 mg/dl) AND (Age) AND (Anti-GAD antibodies (Glutamic Acid Decarboxylase)) AND (BBIT) AND (BMI) AND (C-peptide levels) AND (Fasting blood glucose) AND (HbA1c) AND (Previous) AND (Type 2 diabetes) AND (basal insulin and at least once daily bolus insulin) AND (negative) AND (therapy))"}
{"candidate_id": "LLM06756", "doc_id": "NCT02918409_inc", "case_bucket": "or", "source_criterion": "Male or female = 18 years of age at Visit 1. Sweat chloride equal or greater than 60 mEq/L by quantitative pilocarpine iontophoresis test. Two well-characterized mutations in the cystic fibrosis transmembrane conductance regulator (CFTR) gene Abnormal nasal potential difference (NPD) as measured by a change in NPD in response to a low chloride solution and isoproterenol of less than -5 mV. Documentation of the presence of an acute pulmonary exacerbation, based on CF Foundation guidelines, as diagnosed by a faculty member of the Denver Adult CF Program. Respiratory culture(s) demonstrating evidence of Pseudomonas aeruginosa or Achromobacter species airway infection. Subject is able to produce sputum, undergo phlebotomy, and provide written consent. The subject's treating physician has determined that they should receive either tobramycin or colistin intravenously as one of the designated agents for their APE treatment. Subjects who are able to receive either tobramycin or colistin as part of their antibiotic regimen will be randomized into one of three arms. If a treating physician deems that a subject cannot receive tobramycin due to vestibular toxicity, ototoxicity or bacterial resistance, the subject will be randomized to either standard or PK-adjusted colistin.", "candidate_expression": "((CF Foundation guidelines) AND (CFTR) AND (Male) AND (NPD) AND (Respiratory culture(s) Pseudomonas aeruginosa) AND (Subject is able to produce sputum, undergo phlebotomy, and provide written consent.) AND (Sweat chloride equal or greater than 60 mEq/L) AND (The subject's treating physician has determined that they should receive either tobramycin or colistin intravenously as one of the designated agents for their APE treatment. Subjects who are able to receive either tobramycin or colistin as part of their antibiotic regimen will be randomized into one of three arms. If a treating physician deems that a subject cannot receive tobramycin due to vestibular toxicity, ototoxicity or bacterial resistance, the subject will be randomized to either standard or PK-adjusted colistin) AND (acute pulmonary exacerbation) AND (age = 18 years at Visit 1.) AND (airway infection Achromobacter species) AND (cystic fibrosis transmembrane conductance regulator gene) AND (female) AND (mutations Two) AND (nasal potential difference Abnormal less than -5 mV) AND (quantitative pilocarpine iontophoresis test))"}
{"candidate_id": "LLM06757", "doc_id": "NCT01822262_inc", "case_bucket": "other", "source_criterion": "Clinical diagnosis of calculous cholecystitis.", "candidate_expression": "(calculous cholecystitis Clinical diagnosis)"}
{"candidate_id": "LLM06758", "doc_id": "NCT03360214_inc", "case_bucket": "or", "source_criterion": "Subjects must be female Subjects must be 18 years or older Subjects must be undergoing unilateral or bilateral mastectomy with tissue expander reconstruction", "candidate_expression": "((18 years or older) AND (female) AND (mastectomy) AND (older) AND (tissue expander reconstruction) AND (undergoing) AND ((bilateral) OR (unilateral)))"}
{"candidate_id": "LLM06759", "doc_id": "NCT03017053_inc", "case_bucket": "or", "source_criterion": "Ability to understand and the willingness to sign a written informed consent document Age= 18 and= 75 years Clinical/ Histological/ cytological/ Imaging examination proven Oral/Oropharynx Squamous-cell carcinoma (Tongue, buccal mucosa, mouth floor, hard palate, Molar area), the depth of invasion > 4mm in preoperative assessment In line with clinical stage I / II stage (T1-2 N0 M0; AJCC 2010) and receiving surgical resection KPS= 70 Normal bone marrow reserve function and normal liver, kidney function Expected survival period= 6 months", "candidate_expression": "((Ability to understand and the willingness to sign a written informed consent document) AND (Age = 18 and= 75 years) AND (Expected survival period = 6 month) AND (KPS = 70) AND (M 0) AND (N 0) AND (Squamous-cell carcinoma) AND (T 1-2) AND (bone marrow reserve function Normal) AND (depth of invasion > 4mm) AND (preoperative assessment) AND (surgical resection) AND ((Molar area) OR (Tongue) OR (buccal mucosa) OR (hard palate) OR (mouth floor)) AND ((Clinical examination) OR (Histological examination) OR (Imaging examination) OR (cytological examination)) AND ((clinical stage I) OR (clinical stage II)) AND ((kidney function normal) OR (liver function normal)) AND ((Oral) OR (Oropharynx)))"}
{"candidate_id": "LLM06760", "doc_id": "NCT02807857_inc", "case_bucket": "other", "source_criterion": "Willing and able to provide written informed consent and accept study procedures and time schedule. Age = 18 years. Patients suffering from chronic heart failure (the heart failure diagnosis must have been made or confirmed by a cardiologist and/or hospital physician at any time in the patient's medical history). Patients with reduced ejection fraction (= 40%) as confirmed at any time point in the patient's medical history.", "candidate_expression": "((= 18 years) AND (= 40%) AND (Age) AND (Willing and able to provide written informed consent and accept study procedures and time schedule.) AND (chronic heart failure) AND (ejection fraction))"}
{"candidate_id": "LLM06761", "doc_id": "NCT03407625_exc", "case_bucket": "other", "source_criterion": "latex allergy non-reassuring fetal status HIV active herpes outbreak Prior uterine scar Contraindication to prostaglandins according to current Parkland protocol Contraindication to vaginal delivery", "candidate_expression": "((Contraindication) AND (HIV) AND (Parkland protocol) AND (active) AND (allergy) AND (fetal status) AND (herpes) AND (latex) AND (non-reassuring) AND (prostaglandins) AND (uterine scar) AND (vaginal delivery))"}
{"candidate_id": "LLM06762", "doc_id": "NCT03223909_inc", "case_bucket": "or", "source_criterion": ">18 to < 90 years old Both sexes Mild to moderate tear film dysfunction clinical diagnose TBUT > 5 sec. and < 10 sec. Schirmer: > 4 mm and < 14 mm OSDI < 30 points Corneal staining < grade III on the Oxford scale Availability to go to each revision when indicated.", "candidate_expression": "((< 30 points) AND (< grade III) AND (> 4 mm and < 14 mm) AND (> 5 sec. and < 10 sec) AND (>18 to < 90 years) AND (Availability to go to each revision when indicated.) AND (Both sexes) AND (Corneal staining) AND (OSDI) AND (Oxford scale) AND (Schirmer) AND (TBUT) AND (old) AND (tear film dysfunction) AND ((Mild) OR (moderate)))"}
{"candidate_id": "LLM06763", "doc_id": "NCT02765035_exc", "case_bucket": "or", "source_criterion": "Person is under 18 years of age. Person who weighs more than 136kg. Person who weighs less than 50kg. Person who is pregnant. Person has a history of chronic skin breakdown on the residual limb. Person has conditions that would prevent participation and pose increased risk (e.g. unstable cardiovascular conditions that preclude physical activity such as walking). Person falls = once a week due to the reasons that could not be corrected by the new prosthesis (for ex. problems with vestibular system). Person is using under arm axillary crutches or walker. Person in an emergency, life threatening situation. Person is unwilling/unable to follow instructions. Person who is not available to follow the entire study protocol. Person who is participating in another study or intends to participate in another study during this study duration. Person who cannot personally provide their consent. Person who is not wearing prosthesis 8hours/day on average. Person who has a score on 10m walk test less than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person who walks on average less than 1km per day. Person who is not able to walk on level ground in a step over step manner.", "candidate_expression": "((0.8m/s)) AND (10m walk test) AND (8hours/day) AND (Person is unwilling/unable to follow instruction) AND (Person who cannot personally provide their consent) AND (Person who is not available to follow the entire study protocol) AND (Person who is participating in another study or intends to participate in another study during this study duration.) AND (age) AND (chronic) AND (ess than 1km per day) AND (falls) AND (less than 3km/h) AND (less than 50kg) AND (more than 136kg) AND (not) AND (once a week) AND (pregnant) AND (prosthesis) AND (residual limb) AND (skin breakdown) AND (under 18 years) AND (walks) AND (weighs) AND ((under arm axillary crutches) OR (walker)) AND ((emergency situation) OR (life threatening situation)))"}
{"candidate_id": "LLM06764", "doc_id": "NCT03360214_exc", "case_bucket": "or", "source_criterion": "Allergy to narcotic medications Intake of any chronic opioids or pain medications preoperatively", "candidate_expression": "((Allergy) AND (any) AND (chronic) AND (narcotic medications) AND (opioids) AND (pain medications) AND (preoperatively))"}
{"candidate_id": "LLM06765", "doc_id": "NCT01175044_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo revision total knee arthroplasty", "candidate_expression": "(revision total knee arthroplasty)"}
{"candidate_id": "LLM06766", "doc_id": "NCT03467750_exc", "case_bucket": "other", "source_criterion": "Known coagulation defect Patients on longstanding NSAID therapy Known renal impairment Patients may also be excluded at the discretion of the investigator", "candidate_expression": "((NSAID therapy) AND (coagulation defect) AND (longstanding) AND (renal impairment))"}
{"candidate_id": "LLM06767", "doc_id": "NCT01313676_inc", "case_bucket": "or", "source_criterion": "Type of subject: outpatient. Informed consent: Subjects must give their signed and dated written informed consent to participate. Gender: Male or female. Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception. Age: >=40 and <=80 years of age at Screening (Visit 1). Tobacco use: Subjects with a current or prior history of >=10 pack-years of cigarette smoking at screening (Visit 1). Previous smokers are defined as those who have stopped smoking for at least 6 months prior to Visit 1. Airflow Obstruction: Subjects with a measured post-albuterol/salbutamol forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio of <=0.70 at Screening (Visit 1). Subjects with a measured post-albuterol/salbutamol FEV1 >=50 and <=70% of predicted normal values calculated using NHANES III reference equations [Hankinson, 1999; Hankinson, 2010] at Screening (Visit 1). Post-bronchodilator spirometry will be performed approximately 15 minutes after the subject has self-administered 4 inhalations (i.e., total 400mcg) of albuterol/salbutamol via a metered dose inhaler (MDI )with a valved-holding chamber. The FEV1/FVC ratio and FEV1 percent predicted values will be calculated. Symptoms of COPD: Subjects must score 2 or higher on the modified Medical Research Council Dyspnea scale (Visit 1) Cardiovascular disease: For patients >= 40 years of age: any one of the following: Established (i.e. by clinical signs or imaging studies) coronary artery disease (CAD) Established (i.e. by clinical signs or imaging studies) peripheral vascular disease (PVD) Previous stroke Previous MI Diabetes mellitus with target organ disease OR For patients >=60 years of age: any 2 of the following: Being treated for hypercholesterolemia Being treated for hypertension Being treated for diabetes mellitus Being treated for peripheral vascular disease", "candidate_expression": "((Age >=40 and <=80 years at Screening) AND (Diabetes mellitus) AND (FEV1 post-albuterol/salbutamol >=50 and <=70% of predicted normal values at Screening) AND (Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception.) AND (Informed consent: Subjects must give their signed and dated written informed consent to participate.) AND (MI Previous) AND (Male) AND (Previous smokers) AND (Symptoms of COPD) AND (age >= 40 years) AND (age >=40 and <=80 years at Screening current) AND (age >=60 years) AND (albuterol) AND (bronchodilator) AND (cigarette smoking history >=10 pack-years at screening prior) AND (clinical signs) AND (coronary artery disease (CAD) Established) AND (diabetes mellitus) AND (female) AND (forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio post-albuterol/salbutamol <=0.70 at Screening) AND (hypercholesterolemia) AND (hypertension) AND (imaging studies) AND (inhalations self-administered 4 400mcg) AND (metered dose inhaler (MDI ) with a valved-holding chamber) AND (modified Medical Research Council Dyspnea scale score 2 or higher) AND (outpatient) AND (peripheral vascular disease) AND (peripheral vascular disease (PVD) Established) AND (salbutamol) AND (spirometry Post-bronchodilator approximately 15 minutes after) AND (stopped smoking for at least 6 months prior to Visit 1) AND (stroke Previous) AND (target organ disease) AND (treated for diabetes mellitus) AND (treated for hypercholesterolemia) AND (treated for hypertension) AND (treated for peripheral vascular disease))"}
{"candidate_id": "LLM06768", "doc_id": "NCT00785213_exc", "case_bucket": "or", "source_criterion": "Recent participation (within 28 days) in other research studies Recent significant blood donation or plasma donation Pregnant or lactating Test positive at screening for human immunodeficiency virus (HIV), hepatitis B surface antigen (HbsAg), or hepatitis C virus (HCV) Recent (2-year) history or evidence of alcoholism or drug abuse History or presence of significant cardiovascular, pulmonary, hepatic, gallbladder or biliary tract, renal, hematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease Subjects who have used any drugs or substances known to inhibit or induce cytochrome (CYP) P450 enzymes and/or P-glycoprotein (P-gp) within 28 days prior to the first dose and throughout the study Drug allergies to quinine sulfate or rosiglitazone", "candidate_expression": "((2-year) AND (History or presence of significant cardiovascular, pulmonary, hepatic, gallbladder or biliary tract, renal, hematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease) AND (Recent) AND (Recent participation (within 28 days) in other research studies) AND (allergies) AND (at screening) AND (drugs known to induce P-glycoprotein (P-gp)) AND (drugs known to inhibit P-glycoprotein (P-gp)) AND (positive) AND (significant) AND (throughout the study) AND (within 28 days) AND (within 28 days prior to the first dose) AND ((hepatitis B surface antigen (HbsAg)) OR (hepatitis C virus (HCV)) OR (human immunodeficiency virus (HIV))) AND ((alcoholism) OR (drug abuse)) AND ((evidence) OR (history)) AND ((drugs known to induce cytochrome (CYP) P450 enzymes) OR (drugs known to inhibit cytochrome (CYP) P450 enzymes)) AND ((quinine sulfate) OR (rosiglitazone)) AND ((blood donation) OR (plasma donation)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM06769", "doc_id": "NCT03639545_inc", "case_bucket": "other", "source_criterion": "diabetes mellitus type 1", "candidate_expression": "(diabetes mellitus type 1)"}
{"candidate_id": "LLM06770", "doc_id": "NCT02590315_inc", "case_bucket": "other", "source_criterion": "Asymptomatic women 45-68 years, residents in the Piedmont Region, attending the regional breast cancer screening program", "candidate_expression": "((Piedmont Region) AND (regional breast cancer screening program) AND (women 45-68 years Asymptomatic))"}
{"candidate_id": "LLM06771", "doc_id": "NCT02251249_exc", "case_bucket": "or", "source_criterion": "Allergy or contraindication to paracetamol, Prasugrel or Ticagrelor Paracetamol ingestion in the previous 48 hours Patient treated with drugs supposed to alter gastric emptying times (calcium antagonists, Alimentary tract treatments, opioid analgesics, tricyclic antidepressants, antibiotics). Conditions or pathologies supposed to alter gastric emptying times (Thyroid dysfunction, chronic renal failure, Parkinson's disease, scleroderma, amyloidosis, any gastrointestinal disease, any not cured malignancy, and any advanced psychiatric or neurological disease). Presence of vomiting Cardiogenic shock, ventricular arrhythmia or resuscitated cardiac arrest Hepatic insufficiency Severe respiratory disease Pregnant or breastfeeding women", "candidate_expression": "((Hepatic insufficiency) AND (Paracetamol in the previous 48 hours) AND (drugs supposed to alter gastric emptying times) AND (respiratory disease Severe) AND (vomiting) AND (women) AND ((Allergy) OR (contraindication)) AND ((Alimentary tract treatments) OR (antibiotics) OR (calcium antagonists) OR (opioid analgesics) OR (tricyclic antidepressants)) AND ((Parkinson's disease) OR (Thyroid dysfunction) OR (amyloidosis) OR (chronic renal failure) OR (gastrointestinal disease) OR (malignancy) OR (scleroderma)) AND ((neurological disease) OR (psychiatric disease)) AND ((Cardiogenic shock) OR (cardiac arrest resuscitated) OR (ventricular arrhythmia)) AND ((Pregnant) OR (breastfeeding)) AND ((Conditions supposed to alter gastric emptying times) OR (pathologies supposed to alter gastric emptying times)) AND ((Prasugrel) OR (Ticagrelor) OR (paracetamol)))"}
{"candidate_id": "LLM06772", "doc_id": "NCT00250640_exc", "case_bucket": "or", "source_criterion": "Any condition that prevents participation in the study, including pregnancy and other contraindications for Ventavis treatment (as listed in the current Ventavis Summary of Product Characteristics and patient package insert)", "candidate_expression": "((Ventavis treatment Ventavis Summary of Product Characteristics and patient package insert) AND ((contraindications) OR (pregnancy)))"}
{"candidate_id": "LLM06773", "doc_id": "NCT02762851_inc", "case_bucket": "other", "source_criterion": "Age = 18 years and NYHA (New York Heart Association) functional class II, III and IV", "candidate_expression": "((= 18 years) AND (Age) AND (II, III and IV) AND (NYHA (New York Heart Association) functional class))"}
{"candidate_id": "LLM06774", "doc_id": "NCT02195024_exc", "case_bucket": "or", "source_criterion": "Pacing threshold(s) (at 0.4 or 0.5 ms) and/or sensing amplitude(s) and/or impedance(s) are not measurable Meet one or more of the contraindications for MRI including Psychiatric disorders, anxiety, claustrophobia Cardiac disorders that represent a contraindication to MRI Cardiac surgery already scheduled in the next three months Have other medical implants that may interact with MRI, e.g. abandoned implantable cardioverter defibrillator (ICD) leads or pacemaker leads other than MRI conditional, lead extensions, other active medical devices, non-MRI compatible devices, mechanical valve Have other metallic artifacts/components in body that may interact with MRI Subjects for whom a single dose of 1.0 milligram (mg) dexamethasone acetate may be contraindicated Subjects who require a legally authorized representative to obtain consent Subjects who are immediate candidates for an ICD Subjects with medical conditions that preclude the testing required by the protocol or limit study participation Subjects who are enrolled or intend to participate in another clinical trial (of an investigational drug or device, new indication for an approved drug or device, or requirement of additional testing beyond standard clinical practice) during this clinical study Being pregnant Have a life expectancy of less than three months Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)", "candidate_expression": "((Cardiac disorders) AND (Cardiac surgery) AND (ICD) AND (MRI) AND (MRI conditional) AND (Pacing threshold) AND (Psychiatric disorders) AND (Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)) AND (abandoned implantable cardioverter defibrillator (ICD) leads) AND (active medical devices) AND (anxiety) AND (at 0.4 or 0.5 ms) AND (candidates for) AND (claustrophobia) AND (contraindicated) AND (contraindication) AND (contraindications) AND (dexamethasone acetate) AND (dose of 1.0 milligram (mg)) AND (immediate) AND (impedance) AND (in the next three months) AND (interact) AND (interact with MRI) AND (lead extensions) AND (less than three months) AND (life expectancy) AND (limit study participation) AND (mechanical valve) AND (medical conditions) AND (medical implants) AND (metallic artifacts) AND (metallic components) AND (non-MRI compatible devices) AND (not measurable) AND (one or more) AND (other) AND (other than) AND (pacemaker leads) AND (preclude) AND (pregnant) AND (scheduled) AND (sensing amplitude) AND (single) AND (testing required by the protoco) AND (three months))"}
{"candidate_id": "LLM06775", "doc_id": "NCT01909934_exc", "case_bucket": "or", "source_criterion": "Previous treatment with brentuximab vedotin. Previously received an allogeneic transplant. Patients with current diagnosis of primary cutaneous ALCL (patients whose ALCL has transformed to sALCL are eligible). Known cerebral/meningeal disease including signs or symptoms of progressive multifocal leukoencephalopathy (PML) Female patients who are lactating and breastfeeding or pregnant Known human immunodeficiency virus (HIV) positive Known hepatitis B surface antigen-positive, or known or suspected active hepatitis C infection", "candidate_expression": "((Female patients who are lactating and breastfeeding or pregnant) AND (HIV) AND (PML) AND (active) AND (allogeneic transplant) AND (brentuximab) AND (cerebral disease) AND (hepatitis B surface antigen) AND (hepatitis C infection) AND (human immunodeficiency virus) AND (meningeal disease) AND (positive) AND (primary cutaneous ALCL) AND (progressive multifocal leukoencephalopathy) AND (sALCL))"}
```
