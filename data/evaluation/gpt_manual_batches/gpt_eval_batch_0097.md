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
{"candidate_id": "LLM02401", "doc_id": "NCT03212352_exc", "case_bucket": "or", "source_criterion": "Patient does not meet inclusion criteria, discovered after randomization Inability to give informed consent Known clotting disorder or use of anticoagulants Known risk factors for, or presence of, a cardiovascular disease Language barrier", "candidate_expression": "((Inability to give informed consent) AND (Patient does not meet inclusion criteria, discovered after randomization) AND (anticoagulants) AND (clotting disorder) AND ((cardiovascular disease) OR (risk factors cardiovascular disease)))"}
{"candidate_id": "LLM02402", "doc_id": "NCT02431559_inc", "case_bucket": "or", "source_criterion": "1. Subjects must have recurrent or persistent platinum-resistant epithelial ovarian, fallopian tube, or primary peritoneal carcinoma with measureable disease (as defined by RECIST 1.1.) after first or second line platinum-based chemotherapy, for which treatment with PLD is indicated. Platinum-based therapy is defined as treatment with carboplatin, cisplatin or another organoplatinum compound. Platinum-resistant is defined as having a platinum-free interval (PFI) of < 12 months after first- or second-line platinum-based chemotherapy, or having disease progression while receiving second-line platinum-based chemotherapy. Subjects are allowed to have received, but are not required to have received: one additional cytotoxic regimen and/or PARP inhibitor for management of recurrent or persistent disease. biologic therapy (e.g., bevacizumab) as part of their primary treatment regimen or part of their treatment for management of recurrent or persistent disease. 2. Histologic documentation of the original primary tumor. 3. Documented radiographic disease progression < 12 months after the last dose of first- or second-line platinum-based chemotherapy. 4. Subjects in Phase 2 must have disease amenable to biopsy and must be willing to undergo pre- and post-treatment tumor biopsies. Optional for Phase 1. Note: archival tissue will be requested for all subjects preferably from primary tumor site prior to cancer treatment; however, archival tissue is not a requirement for study entry. 5. ECOG performance status of 0 or 1. 6. Laboratory parameters for vital functions should be in the normal range. Laboratory abnormalities that are not clinically significant are generally permitted, except for the following laboratory parameters, which must be within the ranges specified, regardless of clinical significance: Hemoglobin: ≥ 9 g/dL Neutrophil count: ≥ 1.5 x 109/L Platelet count: ≥ 100,000/mm3 Serum creatinine, ≤ 1.5x Institutional Upper Limit of Normal (ULN), or Creatinine Clearance ≥ 50 mL/min (by Cockcroft-Gault formula) Serum bilirubin: ≤ 1.2 mg/dL AST/ALT: ≤ 2.5 x ULN Alkaline phosphatase: ≤ 2.5 x ULN 7. Age ≥18 years. 8. Able and willing to give valid written informed consent. 9. Body weight > 30 kg", "candidate_expression": "((0 or 1) AND (< 12 months after first- or second-line platinum-based chemotherapy) AND (< 12 months after the last dose of first- or second-line platinum-based chemotherapy) AND (> 30 kg) AND (AST/ALT) AND (Able and willing to give valid written informed consent.) AND (Age) AND (Alkaline phosphatase) AND (Body weight) AND (Cockcroft-Gault formula) AND (Creatinine Clearance) AND (ECOG performance status) AND (Hemoglobin) AND (Histologic) AND (Laboratory parameters for vital functions) AND (Neutrophil count) AND (PARP inhibitor) AND (PLD) AND (Platelet count) AND (Platinum-based therapy) AND (Platinum-resistant) AND (Serum bilirubin) AND (Serum creatinine) AND (after first line platinum-based chemotherapy) AND (after second line platinum-based chemotherapy) AND (another organoplatinum compound) AND (bevacizumab) AND (biologic therapy) AND (carboplatin) AND (carcinoma epithelial ovarian) AND (carcinoma fallopian tube) AND (cisplatin) AND (cytotoxic regimen) AND (disease) AND (disease amenable to biopsy) AND (disease progression) AND (documentation) AND (first line platinum-based chemotherapy) AND (first- or second-line platinum-based chemotherapy) AND (indicated) AND (measureable disease) AND (normal range) AND (one additional) AND (original primary tumor) AND (persistent) AND (platinum-free interval (PFI)) AND (platinum-resistant) AND (primary peritoneal carcinoma) AND (primary treatment regimen) AND (radiographic) AND (recurrent) AND (second line platinum-based chemotherapy) AND (second-line platinum-based chemotherapy) AND (the last dose of first- or second-line platinum-based chemotherapy) AND (treatment) AND (treatment with PLD) AND (willing to undergo pre- and post-treatment tumor biopsies) AND (≤ 1.2 mg/dL) AND (≤ 1.5x Institutional Upper Limit of Normal (ULN)) AND (≤ 2.5 x ULN) AND (≥ 1.5 x 109/L) AND (≥ 100,000/mm3) AND (≥ 50 mL/min) AND (≥ 9 g/dL) AND (≥18 years))"}
{"candidate_id": "LLM02403", "doc_id": "NCT02515773_inc", "case_bucket": "or", "source_criterion": "Inpatient or outpatient age 8-19 years inclusive; participants must live with a parent, guardian, or caregiver; Fluent in English; Diagnosed or told by a clinician that they have any of the following bipolar spectrum disorders (BSD): bipolar I, bipolar II, unspecified bipolar and related disorders, Disruptive Mood Dysregulation Disorder (DMDD), cyclothymic disorder, other specified bipolar and related disorders, as well as mood disorder not otherwise specified (if diagnosed in the past as per DSM-IV); Body mass index >85%ile for age and sex by standard growth charts; Received a new or ongoing prescription for at least one SGA (i.e., olanzapine, clozapine, risperidone, quetiapine, aripiprazole, ziprasidone, iloperidone, lurasidone, paliperidone, brexpiprazole or cariprazine) that is not prescribed as a PRN medication;", "candidate_expression": "((BSD) AND (Body mass index >85%ile) AND (DMDD) AND (SGA at least one) AND (age 8-19 years) AND (bipolar spectrum disorders) AND ((Inpatient) OR (outpatient)) AND ((Disruptive Mood Dysregulation Disorder) OR (bipolar I) OR (bipolar II) OR (cyclothymic disorder) OR (mood disorder not otherwise specified) OR (other specified bipolar and related disorders) OR (unspecified bipolar and related disorders)) AND ((aripiprazole) OR (brexpiprazole) OR (cariprazine) OR (clozapine) OR (iloperidone) OR (lurasidone) OR (olanzapine) OR (paliperidone) OR (quetiapine) OR (risperidone) OR (ziprasidone)))"}
{"candidate_id": "LLM02404", "doc_id": "NCT01440296_inc", "case_bucket": "or", "source_criterion": "male and female patients over the age of 18 years. written informed consent (approved by the Institutional Review Board [IRB]/Independent Ethics Committee [IEC]) obtained prior to any study specific procedures. patient with mild to severe carotid artery disease", "candidate_expression": "((age over 18 years) AND (carotid artery disease) AND ((female) OR (male)) AND ((mild) OR (severe)))"}
{"candidate_id": "LLM02405", "doc_id": "NCT02541955_inc", "case_bucket": "other", "source_criterion": "Patient must meet 1987 ACR criteria Age > 18 years of age Baseline DAS28/Erythrocyte Sedimentation Rate (ESR) >=3.2 Stable concomitant Disease Modifying Anti-Rheumatic Drugs (DMARDs) Stable prednisone <10mg or equivalent Power Doppler score of >=10", "candidate_expression": "((1987 ACR criteria) AND (<10mg) AND (> 18 years of age) AND (>=10) AND (>=3.2) AND (Age) AND (Baseline) AND (DAS28/Erythrocyte Sedimentation Rate (ESR)) AND (Disease Modifying Anti-Rheumatic Drugs (DMARDs)) AND (Power Doppler score) AND (Stable) AND (concomitant) AND (prednisone))"}
{"candidate_id": "LLM02406", "doc_id": "NCT02673359_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Congenital uterine malformation. Multifetal pregnancy. Known major fetal structural or chromosomal abnormality. Known allergy or contraindication (relative or absolute) to progesterone therapy. Presence of contraindication to cervical cerclage. Medical conditions complicating pregnancy. Vaginal bleeding.", "candidate_expression": "((Age) AND (Congenital uterine malformation) AND (Medical conditions complicating pregnancy) AND (Multifetal pregnancy) AND (Vaginal bleeding) AND (cervical cerclage) AND (contraindication) AND (progesterone therapy) AND ((allergy) OR (contraindication)) AND ((absolute) OR (relative)) AND ((< 20) OR (> 35 years)) AND ((chromosomal abnormality) OR (fetal structural)))"}
{"candidate_id": "LLM02407", "doc_id": "NCT03225469_inc", "case_bucket": "other", "source_criterion": "1. Individuals scheduled for undergoing colonoscopy at the Endoscopy Center of Wuxi people's Hospital in China 2. Greater than the age of 18 3. Individuals living with other family members 4. Outpatients", "candidate_expression": "((Endoscopy Center of Wuxi people's Hospital in China) AND (Greater than 18) AND (Outpatients) AND (age) AND (colonoscopy))"}
{"candidate_id": "LLM02408", "doc_id": "NCT02990403_exc", "case_bucket": "or", "source_criterion": "having experienced severe allergies, trauma history and/or operation history within 3 months. with a history of mental illness and/or family history of mental illness limb disabled. taking medicine within one month. suffering major events or having mood swings. having internal and surgical disease(after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine) chromosome aberrations in anyone of the couple. patients who have drugs contraindications", "candidate_expression": "((allergies severe) AND (blood routine) AND (chromosome aberrations anyone of the couple anyone of the couple) AND (contraindications) AND (drugs) AND (electrocardiogram) AND (hepatic function) AND (internal disease) AND (major events) AND (medicine within one month) AND (mental illness family history limb disabled) AND (mental illness history limb disabled) AND (mood swings) AND (operation history) AND (physical examination) AND (renal function) AND (surgical) AND (surgical disease) AND (trauma history) AND (urine routine))"}
{"candidate_id": "LLM02409", "doc_id": "NCT02986659_inc", "case_bucket": "or", "source_criterion": "Age 65 - 79 History of coronary artery disease (MI/heart attack, stroke, heart failure, or peripheral artery disease) Cancer, with no active treatment in the last year MCI (MoCA >18<26 -inclusive of 1 point if <12 years of education Group 2 Decline physical function (walking speed < 1 m/s) Group 3 (Either or both) Abdominal obesity (>88cm women, >102cm men) AND hypertension (treated or resting blood pressure >140/90 Abdominal obesity (>88cm women, >102cm men) AND hyperlipidemia (treated or fasting total cholesterol >240 English literacy Willing to provide informed consent", "candidate_expression": "((65 - 79) AND (< 1 m/s) AND (>102cm) AND (>140/90) AND (>18<26) AND (>240) AND (>88cm) AND (Abdominal) AND (Abdominal obesity) AND (Age) AND (Cancer) AND (Decline physical function) AND (English literacy) AND (History) AND (MCI) AND (MI) AND (MoCA) AND (Willing to) AND (active treatment) AND (coronary artery disease) AND (fasting total cholesterol) AND (heart attack) AND (heart failure) AND (hyperlipidemia) AND (hypertension) AND (in the last year) AND (men) AND (no) AND (peripheral artery disease) AND (provide informed consent) AND (resting blood pressure) AND (stroke) AND (treated) AND (walking speed) AND (women))"}
{"candidate_id": "LLM02410", "doc_id": "NCT03472495_exc", "case_bucket": "or", "source_criterion": "Limited English proficiency (LEP) Pregnant Prisoners Wolff Parkinson White syndrome Administration of electrical or chemical cardioversion before screening Administration of other antiarrhythmics for acute heart rate control (excluding adenosine) History of allergy or idiosyncratic reaction to diltiazem Unable to take oral medications Heart rate <60 beats/min", "candidate_expression": "((Heart rate <60 beats/min) AND (LEP) AND (Limited English proficiency) AND (Pregnant) AND (Prisoners) AND (Unable to take) AND (Wolff Parkinson White syndrome) AND (allergy) AND (antiarrhythmics) AND (chemical cardioversion) AND (diltiazem) AND (electrical cardioversion) AND (heart rate control acute) AND (idiosyncratic reaction) AND (oral medications) AND NOT (adenosine))"}
{"candidate_id": "LLM02411", "doc_id": "NCT03140488_exc", "case_bucket": "or", "source_criterion": "Non-reassuring fetal assessment at the time of recruitment Previous cervical ripening agents (cytotec, cervidil, cervical Foley Balloon) <18 years of age Prisoners Any patients contraindicated for vaginal delivery Multiple gestations History of previous cesarean delivery Patients with history of significant cardiac disease Fetal demise Estimated fetal weight greater than 4500 grams in diabetic and 5000 grams in non-diabetic mother Ruptured membranes Spontaneous labor (latent or active phase) Augmentation of labor (latent or active phase)", "candidate_expression": "((5000 grams) AND (<18 years) AND (Augmentation of labor) AND (Estimated fetal weight) AND (Fetal demise) AND (History) AND (Multiple gestations) AND (Non-reassuring) AND (Previous) AND (Prisoners) AND (Ruptured membranes) AND (Spontaneous labor) AND (age) AND (at the time of recruitment) AND (cardiac disease) AND (cervical ripening agents) AND (cesarean delivery) AND (contraindicated) AND (diabetic) AND (fetal assessment) AND (greater than 4500 grams) AND (history) AND (non-) AND (previous) AND (significant) AND (vaginal delivery) AND ((active phase) OR (latent phase)) AND ((cervical Foley Balloon) OR (cervidil) OR (cytotec)))"}
{"candidate_id": "LLM02412", "doc_id": "NCT02974660_inc", "case_bucket": "other", "source_criterion": "patients who underwent successful TAVI with any approved TAVI device via transfemoral access with use of any of the approved vascular closure devices provided written informed consent", "candidate_expression": "((TAVI device) AND (TAVI successful) AND (provided written informed consent) AND (transfemoral access) AND (vascular closure devices))"}
{"candidate_id": "LLM02413", "doc_id": "NCT02368743_exc", "case_bucket": "or", "source_criterion": "Patient included in an interventional study assessing treatment for active proctitis or distal proctosigmoiditis. Patient with left sided, colitis or pancolitis. Patient with severe proctitis (MAYO score ≥ 11 at inclusion). Patient previously treated with biologics. Patient treated with immunosuppressive within 1 month before study inclusion. Patient treated with corticosteroids within 2 weeks before study inclusion.", "candidate_expression": "((MAYO score) AND (at inclusion) AND (biologics) AND (corticosteroids) AND (immunosuppressive) AND (left sided) AND (previously) AND (proctitis) AND (severe) AND (study inclusion) AND (treated) AND (treatment) AND (within 1 month before study inclusion) AND (within 2 weeks before study inclusion) AND (≥ 11) AND ((active proctitis) OR (distal proctosigmoiditis)) AND ((colitis) OR (pancolitis)))"}
{"candidate_id": "LLM02414", "doc_id": "NCT03354572_exc", "case_bucket": "or", "source_criterion": "Pregnancy or lactating Allergy to NAC History of chronic pain Use of opioids or neuropathic analgesics Use of NAC prior to trial (< 1 month of planned surgery) Alcoholism Diabetes Mellitus (insulin therapy) Asthma or Chronic Obstructive pulmonary Disease Known renal function disorders (MDRD <ô0) Known liver failure (bilirubin >1.Sx upper limit of normal) No written lC by patient", "candidate_expression": "((Alcoholism) AND (Allergy) AND (Asthma) AND (Chronic Obstructive pulmonary Disease) AND (Diabetes Mellitus) AND (MDRD <ô0) AND (NAC) AND (NAC prior to trial) AND (No written lC by patient) AND (Pregnancy) AND (bilirubin >1.Sx upper limit of normal) AND (chronic pain History) AND (insulin) AND (lactating) AND (liver failure) AND (neuropathic analgesics) AND (opioids) AND (renal function disorders) AND (surgery < 1 month planned))"}
{"candidate_id": "LLM02415", "doc_id": "NCT02877485_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 NOSE score greater than 55 Nasal septal deviation on exam", "candidate_expression": "((Age) AND (NOSE score) AND (Nasal septal deviation) AND (greater than 18) AND (greater than 55))"}
{"candidate_id": "LLM02416", "doc_id": "NCT01373684_exc", "case_bucket": "or", "source_criterion": "Treatment with any investigational drug within 30 days of entry to this protocol Current treatment with Telbivudine Severe hepatitis activity as documented by ALT>10 x ULN History of decompensated cirrhosis (defined as jaundice in the presence of cirrhosis, ascites, bleeding gastric or esophageal varices or encephalopathy) Pre-existent neutropenia (neutrophils <1,500/mm3) or thrombocytopenia (platelets < 90,000/mm3) Co-infection with hepatitis C virus, hepatitis D virus or human immunodeficiency virus (HIV) Other acquired or inherited causes of liver disease: alcoholic liver disease, obesity induced liver disease, drug related liver disease, auto-immune hepatitis, hemochromatosis, Wilson's disease or alpha-1 antitrypsin deficiency Alpha fetoprotein > 50 ng/ml Hyper- or hypothyroidism (subjects requiring medication to maintain TSH levels in the normal range are eligible if all other inclusion/exclusion criteria are met) Immune suppressive treatment within the previous 6 months Contra-indications for alfa-interferon therapy like suspected hypersensitivity to interferon or Peginterferon or any known pre-existing medical condition that could interfere with the patient's participation in and completion of the study. Pregnancy, breast-feeding Other significant medical illness that might interfere with this study: significant pulmonary dysfunction in the previous 6 months, malignancy other than skin basocellular carcinoma in previous 5 years, immunodeficiency syndromes (e.g. HIV positivity, auto-immune diseases, organ transplants other than cornea and hair transplant) Any medical condition requiring, or likely to require chronic systemic administration of steroids, during the course of the study Substance abuse, such as alcohol (>80 g/day), I.V. drugs and inhaled drugs in the past 2 years. Any other condition which in the opinion of the investigator would make the patient unsuitable for enrollment, or could interfere with the patient participating in and completing the study", "candidate_expression": "((< 90,000/mm3) AND (<1,500/mm3) AND (> 50 ng/ml) AND (>10 x ULN) AND (>80 g/day) AND (ALT) AND (Alpha fetoprotein) AND (Co-infection) AND (Contra-indications) AND (HIV) AND (Immune suppressive treatment) AND (Pre-existent) AND (Pregnancy, breast-feeding) AND (Severe) AND (Substance abuse) AND (Telbivudine) AND (Treatment with any investigational drug within 30 days of entry to this protocol) AND (alfa-interferon therapy) AND (ascites) AND (chronic) AND (cirrhosis) AND (course of the study) AND (decompensated) AND (during the course of the study) AND (hepatitis) AND (hypersensitivity) AND (in previous 5 years) AND (in the past 2 years.) AND (in the previous 6 months) AND (jaundice) AND (liver disease) AND (malignancy) AND (medical illness) AND (medication) AND (neutrophils) AND (organ transplants) AND (other than) AND (platelets) AND (significant) AND (skin basocellular carcinoma) AND (systemic steroids) AND (within the previous 6 months) AND ((bleeding gastric) OR (encephalopathy) OR (esophageal varices)) AND ((neutropenia) OR (thrombocytopenia)) AND ((hepatitis C virus) OR (hepatitis D virus) OR (human immunodeficiency virus)) AND ((acquired) OR (inherited)) AND ((Wilson's disease) OR (alcoholic liver disease) OR (alpha-1 antitrypsin deficiency) OR (auto-immune hepatitis) OR (drug related liver disease) OR (hemochromatosis) OR (obesity induced liver disease)) AND ((Hyper thyroidism) OR (hypothyroidism)) AND ((Peginterferon) OR (interferon)) AND ((immunodeficiency syndromes) OR (pulmonary dysfunction)) AND ((HIV positivity) OR (auto-immune diseases)) AND ((cornea transplant) OR (hair transplant)) AND ((I.V. drugs) OR (alcohol) OR (inhaled drugs)))"}
{"candidate_id": "LLM02417", "doc_id": "NCT03103204_exc", "case_bucket": "or", "source_criterion": "Systemic diseases (diabetes, renal diseases, rheumatic diseases, osteoporosis and cardiovascular diseases) Pregnant and lactating women HIV/ AIDS periodontal treatment in the last year (before baseline appointment) Medication: Immunosuppressive drugs, antibiotics in the past three months (before baseline appointment) ) orthodontic appliance", "candidate_expression": "((AIDS) AND (HIV) AND (Immunosuppressive drugs) AND (Pregnant) AND (Systemic diseases) AND (antibiotics) AND (baseline appointment) AND (before baseline appointment) AND (in the last year) AND (in the past three months) AND (lactating) AND (orthodontic appliance) AND (periodontal treatment) AND (women))"}
{"candidate_id": "LLM02418", "doc_id": "NCT03036462_inc", "case_bucket": "other", "source_criterion": "Patients aged at least 18 years Patients with chronic heart failure present for at least 12 months Confirmed presence of iron deficiency Serum haemoglobin of 9.5 to 14.0 g/dL", "candidate_expression": "((Serum haemoglobin 9.5 to 14.0 g/dL) AND (aged at least 18 years) AND (chronic heart failure for at least 12 months) AND (iron) AND (iron deficiency))"}
{"candidate_id": "LLM02419", "doc_id": "NCT02003339_inc", "case_bucket": "or", "source_criterion": "Early, intermediate, advanced, non metastatic Hepatocellular Carcinoma. Indication for radioembolization validated after pluridisciplinary committee meeting. Isolated target on initial imagery (invasive hepatocellular carcinoma excluded) WHO (World Health organization) Performance status: 0, 1 or 2 If cirrhosis, Child A score with total bilirubin less than 30 micromoles per liter Creatinine clearance more or equal to 30 mL/min Patient informed and consent signature obtained", "candidate_expression": "((Child score A) AND (Creatinine clearance more or equal to 30 mL/min) AND (Hepatocellular Carcinoma metastatic Early intermediate advanced) AND (Indication) AND (Patient informed and consent signature obtained) AND (WHO (World Health organization) Performance status 0, 1 or 2) AND (cirrhosis) AND (radioembolization Indication) AND (total bilirubin less than 30 micromoles per liter))"}
{"candidate_id": "LLM02420", "doc_id": "NCT03154931_inc", "case_bucket": "other", "source_criterion": "Clinical Administered PTSD Scale 5 Monthly version Criteria A and >30 points", "candidate_expression": "(Clinical Administered PTSD Scale Criteria A >30 points)"}
{"candidate_id": "LLM02421", "doc_id": "NCT02455921_exc", "case_bucket": "other", "source_criterion": "Parents refusal Cognitive impairment Difficulty in communication due to language issues Psychiatric disorder Severe systematic disorder Known allergy to any drug used", "candidate_expression": "((Cognitive impairment) AND (Difficulty in communication) AND (Known allergy) AND (Parents refusal) AND (Psychiatric disorder) AND (Severe systematic disorder) AND (any drug used) AND (language issues))"}
{"candidate_id": "LLM02422", "doc_id": "NCT02042287_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02423", "doc_id": "NCT01768195_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with B-cell lymphoma HBsAg positive at baseline treated with rituximab-based immunochemotherapy life expectancy of more than 3 months", "candidate_expression": "((B-cell lymphoma) AND (HBsAg positive at baseline) AND (immunochemotherapy rituximab-based) AND (life expectancy more than 3 months) AND (rituximab) AND NOT (treatment))"}
{"candidate_id": "LLM02424", "doc_id": "NCT03026088_exc", "case_bucket": "or", "source_criterion": "Acute coronary syndrome (ACS) within 3 months. Under beta-blocker treatment for the last 2 weeks. Under other medicine treatment which may affect heart rate, like Non-dihydropyridine calcium channel blockers (NDHP-CCBs) or ivabradine for the last 2 weeks; Under Digoxin treatment [more than (>) 0.125 milligram (mg)]. Uncontrolled Diabetes [hemoglobin A1c, (HbA1c) >7.5%]. Severe or uncontrolled hypertension [resting Systolic Blood Pressure (SBP) >180 millimeters of mercury (mmHg), or resting Diastolic Blood Pressure (DBP) >110mmHg at screening period]. Severe hypotension [resting SBP less than (<) 90mmHg, or resting DBP<50mmHg]. Resting heart rate <60 beat per minute (bpm). Any contradiction to Bisoprolol according to label, including: Acute heart failure or during episodes of heart failure decompensation requiring intravenous inotropic therapy. Cardiogenic shock. Atrioventricular block of second or third degree (without a pacemaker). Sick sinus syndrome. Sinoatrial block. Slowed heart rate, causing symptoms (symptomatic bradycardia), Decreased blood pressure, causing symptoms (symptomatic hypotension), Severe bronchial asthma or severe chronic obstructive pulmonary disease. Sever forms of peripheral arterial occlusive disease and Raynaud's syndrome. Untreated phaeochromocytoma. Metabolic acidosis. Hypersensitivity to bisoprolol or to any of the excipients. Severe Arrhythmia including atrial fibrillation, atrial flutter, ventricular fibrillation, ventricular flutter or ventricular tachycardia. Significant valvular heart disease, congenital heart disease, pulmonary heart disease or perinatal heart disease. Acute pulmonary edema. Severe hepatic dysfunction, defined as: Serum Alanine Aminotransferase (ALT) > triple the upper limit of the normal range; and/or Serum Aspartate Aminotransferase (AST) > triple the upper limit of the normal value range and/or Severe renal dysfunction, defined as: Serum creatinine > twice the upper limit of the normal range Chronic Kidney Disease (glomerular filtration rate <45 Milliliter per minute). Hyperthyroidism or hypothyroidism. Severe infectious disease, example (eg) Human Immunodeficiency Virus positive or active tuberculosis. Severe autoimmune disease, e.g. lupus erythematosus, multiple sclerosis. Severe respiratory, digestive, hematological disease (including Anemia of Hb < 100 gram per litre) or tumor. Known to be hypersensitivity to Bisoprolol, or any of the excipient. Substance or alcohol abuse. Received heart transplantation or pacemaker implantation; revascularization treatment within 3 months; or plan to receive above treatment in 6 months. Currently undertaking other treatment that may affect the safety and/or efficacy evaluation, e.g. beta receptors agonists, et cetera. No legal ability or legal ability is limited. Subjects unlikely to cooperate in the study or with inability or unwillingness to give informed consent. Child-bearing period women without effective contraceptive measures, pregnancy and lactation. Participation in another clinical trial within the past 90 days. Other significant condition that in the Investigator's opinion would exclude the subject from the trial.", "candidate_expression": "((ACS) AND (ALT) AND (AST) AND (Acute coronary syndrome within 3 months) AND (Acute pulmonary edema) AND (Anemia) AND (Arrhythmia Severe) AND (Bisoprolol) AND (Cardiogenic shock) AND (Child-bearing period women without effective contraceptive measures, pregnancy and lactation) AND (Chronic Kidney Disease) AND (DBP) AND (Diabetes Uncontrolled) AND (Digoxin more than 0.125 milligram > 0.125 mg) AND (Hb < 100 gram per litre) AND (HbA1c) AND (Hypersensitivity) AND (Metabolic acidosis) AND (NDHP-CCBs) AND (No legal ability or legal ability is limited) AND (Other significant condition that in the Investigator's opinion would exclude the subject from the trial) AND (SBP >180 mmHg) AND (Serum creatinine > twice the upper limit of the normal range) AND (Sick sinus syndrome) AND (Sinoatrial block) AND (autoimmune disease Severe) AND (beta receptors agonists) AND (beta-blocker for the last 2 weeks) AND (blood pressure Decreased) AND (bradycardia symptomatic) AND (contradiction) AND (glomerular filtration rate <45 Milliliter per minute) AND (heart rate Resting <60 beat per minute <60 bpm) AND (heart rate Slowed) AND (hemoglobin A1c >7.5%) AND (hepatic dysfunction Severe) AND (hypersensitivity) AND (hypertension) AND (hypotension Severe) AND (hypotension symptomatic) AND (infectious disease Severe) AND (intravenous inotropic therapy) AND (phaeochromocytoma Untreated) AND (renal dysfunction Severe) AND (symptoms) AND (tumor) AND (ubjects unlikely to cooperate in the study or with inability or unwillingness to give informed consent) AND NOT (pacemaker) AND ((Serum Alanine Aminotransferase > triple the upper limit of the normal range) OR (Serum Aspartate Aminotransferase > triple the upper limit of the normal value range)) AND ((Hyperthyroidism) OR (hypothyroidism)) AND ((Human Immunodeficiency Virus positive) OR (tuberculosis active)) AND ((lupus erythematosus) OR (multiple sclerosis)) AND ((digestive disease) OR (hematological disease) OR (respiratory disease)) AND ((Bisoprolol) OR (excipient any)) AND ((Substance abuse) OR (alcohol abuse)) AND ((heart transplantation) OR (pacemaker implantation) OR (revascularization)) AND ((heart transplantation) OR (pacemaker implantation)) AND ((Severe) OR (uncontrolled)) AND ((Diastolic Blood Pressure resting >110mmHg) OR (Systolic Blood Pressure resting >180 millimeters of mercury)) AND ((DBP resting <50mmHg) OR (SBP resting less than 90mmHg)) AND ((Acute heart failure) OR (heart failure decompensation)) AND ((Atrioventricular block of second degree) OR (Atrioventricular block of third degree)) AND ((Non-dihydropyridine calcium channel blockers) OR (ivabradine)) AND ((bronchial asthma Severe) OR (chronic obstructive pulmonary disease severe)) AND ((Raynaud's syndrome) OR (peripheral arterial occlusive disease)) AND ((bisoprolol) OR (excipients any)) AND ((atrial fibrillation) OR (atrial flutter) OR (ventricular fibrillation) OR (ventricular flutter) OR (ventricular tachycardia)) AND ((congenital heart disease) OR (perinatal heart disease) OR (pulmonary heart disease) OR (valvular heart disease)))"}
{"candidate_id": "LLM02425", "doc_id": "NCT02788045_inc", "case_bucket": "scope", "source_criterion": "Are negative for human immunodeficiency virus (HIV) infection at screening Is healthy on the basis of physical examination, medical history, electrocardiogram (ECG), and vital signs measurement performed at screening Are willing/able to adhere to the prohibitions and restrictions specified in the protocol and study procedures Female participants of childbearing potential must have a negative serum pregnancy test (beta human chorionic gonadotropin [beta hCG]) at the Screening visit, and a negative urine pregnancy test pre-dose on Day 1 Are assessed by the clinic staff as being at low risk for HIV infection", "candidate_expression": "((Are willing/able to adhere to the prohibitions and restrictions specified in the protocol and study procedures) AND (Female) AND (HIV infection) AND (beta human chorionic gonadotropin [beta hCG]) AND (childbearing potential) AND (electrocardiogram (ECG)) AND (healthy) AND (low risk) AND (medical history) AND (physical examination) AND (serum pregnancy test) AND (urine pregnancy test negative pre-dose on Day 1) AND (vital signs measurement) AND NOT (human immunodeficiency virus (HIV) at screening))"}
```
