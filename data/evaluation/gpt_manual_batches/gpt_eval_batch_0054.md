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
{"candidate_id": "LLM01326", "doc_id": "NCT03476850_exc", "case_bucket": "or", "source_criterion": "Chronic pain or narcotic usage during the preceding 30 days Infection at or near the intended needle insertion site Complex or altered abdominal wall anatomy Weight <45kg", "candidate_expression": "((Chronic pain) AND (Complex abdominal wall anatomy) AND (Infection intended needle insertion site) AND (Weight <45kg) AND (altered abdominal wall anatomy) AND (narcotic))"}
{"candidate_id": "LLM01327", "doc_id": "NCT02816762_inc", "case_bucket": "or", "source_criterion": "Subjects aged 18 to 80 years old Overweight or obesity (BMI =25 kg/m2) Previous diagnosis of type 2 diabetes, fulfilling at least one of the following criteria: 1) current treatment with oral antidiabetic drugs and/or insulin; 2) a fasting glucose value above 126 mg/dl on at least 2 occasions; 3) blood glucose level at 2 hours after an oral glucose tolerance test is equal to or more than 200 mg/dl; or 4) a glycated hemoglobin (HbA1c) level > 6.5 % Clinical diagnosis of diabetic nephropathy, with a urinary albumin/creatinine ratio >30 mg/g and an estimated glomerular filtration rate more than 20 ml/min per 1.73 m2. Treatment with stable doses of angiotensin-converting enzyme inhibitors, angiotensin II receptor blockers or anti-aldosterone agents in the last four weeks.", "candidate_expression": "((BMI =25 kg/m2) AND (Overweight) AND (aged 18 to 80 years old) AND (angiotensin II receptor blockers) AND (angiotensin-converting enzyme inhibitors) AND (anti-aldosterone agents) AND (blood glucose level at 2 hours after an oral glucose tolerance test equal to or more than 200 mg/dl) AND (diabetic nephropathy) AND (estimated glomerular filtration rate more than 20 ml/min per 1.73 m2) AND (fasting glucose above 126 mg/dl on at least 2 occasions) AND (glycated hemoglobin (HbA1c) level > 6.5 %) AND (insulin) AND (obesity) AND (oral antidiabetic drugs) AND (oral glucose tolerance test) AND (type 2 diabetes Previous) AND (urinary albumin/creatinine ratio >30 mg/g))"}
{"candidate_id": "LLM01328", "doc_id": "NCT02478515_inc", "case_bucket": "other", "source_criterion": "Signed informed consent form Macula edema secondary to BRVO BCVA of 77 to 20 letters assessed with the use of ETDRS charts CRT <U+2267>250µm", "candidate_expression": "((BCVA 77 to 20 letters) AND (BRVO) AND (CRT 250µm) AND (Macula edema) AND (Signed informed consent form))"}
{"candidate_id": "LLM01329", "doc_id": "NCT01228279_inc", "case_bucket": "other", "source_criterion": "Adult (age 18 years and older) Patients with end-stage renal disease(ESRD)/chronic kidney disease(CKD)stage 5", "candidate_expression": "((Adult) AND (CKD) AND (ESRD) AND (age 18 years and older) AND (chronic kidney disease stage 5) AND (end-stage renal disease))"}
{"candidate_id": "LLM01330", "doc_id": "NCT01009359_inc", "case_bucket": "or", "source_criterion": "Able to give fully informed consent in writing Males or females aged >/= 50 years No significant disease or drug use Absence of any sign of dementia/cognitive impairment in neuropsychological examinationsPatients for brain imaging: Patient and designee capable of giving fully informed consent in writing Patient fulfils DSM-IV and NINCDS-ADRA criteria for probable Alzheimers disease", "candidate_expression": "((Able to give fully informed consent in writing) AND (Alzheimers disease probable) AND (DSM-IV criteria fulfils) AND (NINCDS-ADRA criteria fulfils) AND (Patient and designee capable of giving fully informed consent in writing) AND (aged >/= 50 years) AND (cognitive impairment) AND (dementia) AND (neuropsychological examinations) AND (significant) AND ((sign of cognitive impairment) OR (sign of dementia)) AND ((Males) OR (females)) AND ((disease significant) OR (drug use)))"}
{"candidate_id": "LLM01331", "doc_id": "NCT02790593_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years Significant arterial disease (Ankle Brachial Pressure Index <0•9 or evidence on Arterial Duplex) Acute Deep Vein Thrombosis Patient unable or unwilling to have high compression (30mmHg minimum) Patients with dexterity insufficiency of hands Patients with peripheral neuropathy Leg ulcers of another underlying cause Leg ulcers of greater than 1 year duration Patients unable or unwilling to provide written, informed consent", "candidate_expression": "((<0•9) AND (Acute Deep Vein Thrombosis) AND (Age) AND (Leg ulcers) AND (Patient unable or unwilling to have high compression (30mmHg minimum)) AND (Patients unable or unwilling to provide written, informed consent) AND (Significant) AND (another) AND (arterial disease) AND (dexterity insufficiency of hands) AND (greater than 1 year duration) AND (less than 18 year) AND (peripheral neuropathy) AND (underlying cause) AND ((Ankle Brachial Pressure Index) OR (Arterial Duplex)))"}
{"candidate_id": "LLM01332", "doc_id": "NCT00094861_exc", "case_bucket": "or", "source_criterion": "Metastatic disease (M1)/stage 4 NSCLC Pleural or pericardial effusion greater than 100 ml in volume as documented by appropriate imaging (positron emission tomography [PET], computed tomography [CT] scan or ultrasound). If an effusion greater than 100 ml is documented by cytology to be free from malignancy and the investigator feels the patient is capable of receiving chemo/radiotherapy for their primary disease/ NSCLC, the investigator should discuss the patient with the study physician at Amgen. Effusions smaller than 100 ml would be acceptable, unless the investigator suspects that the effusion is malignant, in which case the effusions should be evaluated by cytology. Sponsor approval must be obtained before patient is randomized. Plan to remove the tumor surgically before completing the protocol chemo/radiotherapy course Shielding of any part of the esophagus during radiotherapy (including posterior spinal cord shielding) Prior chemotherapy, radiotherapy, or surgery for NSCLC Prior invasive malignancy during the past 3 years other than non-melanomatous skin cancer. Note: Patients with prior surgically-cured malignancies [eg, stage I breast cancer or prostate cancer, in-situ carcinoma of the cervix, etc] are not excluded; however, sponsor approval must be obtained before patient is randomized. Presence or history of dysphagia or conditions predisposing to dysphagia (eg, uncontrolled gastroesophageal reflux disease [GERD], dyspepsia, etc) History of pancreatitis Four weeks or less since completion of treatment using an investigational product/device in another clinical study or presence of any unresolved toxicity from previous treatment Previous treatment on this study or with a fibroblast growth factor Known to be sero-positive for human immunodeficiency virus (HIV), hepatitis C virus (HCV), or hepatitis B virus (HBV) Pregnant or breastfeeding women Known sensitivity to E. coli derived products Compromised ability of the patient to give written informed consent and/or to comply with study procedures Refusal to sign an informed consent form to participate in this study, and sign the hospital information release form, if applicable Unwilling or unable to complete the patient reported outcome (PRO) questionnaires Psychological, social, familial, or geographical reasons that would prevent regular follow-up", "candidate_expression": "(((M1)/stage 4) AND (CT) AND (Compromised ability) AND (GERD) AND (Metastatic disease NSCLC) AND (NSCLC) AND (PET) AND (Plan to remove the tumor surgically before completing the protocol chemo/radiotherapy course) AND (Shielding esophagus) AND (another clinical study) AND (fibroblast growth factor) AND (give written informed consent) AND (hepatitis B virus (HBV) sero-positive) AND (hepatitis C virus (HCV) sero-positive) AND (human immunodeficiency virus (HIV) sero-positive) AND (malignancy Prior invasive during the past 3 years) AND (pancreatitis History of) AND (posterior spinal cord shielding) AND (products E. coli derived) AND (radiotherapy) AND (sensitivity) AND (toxicity unresolved) AND (treatment) AND (treatment Previous) AND (treatment previous) AND (women) AND NOT (non-melanomatous skin cancer) AND NOT (surgically-cured malignancies) AND ((chemotherapy) OR (radiotherapy) OR (surgery)) AND ((Pleural effusion) OR (pericardial effusion)) AND ((conditions predisposing to dysphagia) OR (dysphagia)) AND ((dyspepsia) OR (gastroesophageal reflux disease uncontrolled)) AND ((investigational device) OR (investigational product)) AND ((sero-positive for hepatitis B virus (HBV)) OR (sero-positive for hepatitis C virus (HCV)) OR (sero-positive for human immunodeficiency virus (HIV))) AND ((Pregnant) OR (breastfeeding)) AND ((computed tomography scan) OR (positron emission tomography) OR (ultrasound)) AND ((sign an informed consent form Refusal to) OR (sign the hospital information release form Refusal to)))"}
{"candidate_id": "LLM01333", "doc_id": "NCT03337503_exc", "case_bucket": "or", "source_criterion": "Acute pain (less than 3 months in duration) Previous serious adverse event or hypersensitivity to cannabis or cannabinoids Inability to understand and comply with the instructions of the study Presence of significant cardiac disease (history of unstable ischemic heart disease, heart failure, severe and uncontrolled hypertension) that, in the opinion of the investigator, would put the patient at risk of a clinically significant arrhythmia or myocardial infarction Current substance use disorder according to the Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5) Life-time history of dependence on cannabis or diagnosis of cannabis use disorder (CUD) according to the DSM 5 Life-time history of DSM 5 schizophrenia, bipolar disorder, or previous psychosis with or intolerance to cannabinoids Current or history of suicidal ideation Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception Hepatic impairment (aspartate aminotransferase more than three times normal) or renal function impairment (serum creatinine level >133 µmol/L, Estimated Glomerular Filtration Rate (eGFR) <60) Cognitive impairment according to MiniCog The patient is currently using or has used cannabinoid based medications within 90 days of study entry and is unwilling to abstain for the duration of the study Positive urine drug screen for cannabinoids and other potential abuse substances (e.g. alcohol, cocaine, amphetamines and methamphetamines, unprescribed opioids) Participation in another clinical trial within 30 days of enrolment in our trial", "candidate_expression": "((<60) AND (>133 µmol/L) AND (Acute) AND (Cognitive impairment) AND (DSM 5) AND (Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5)) AND (MiniCog) AND (Participation in another clinical trial within 30 days of enrolment in our trial) AND (Positive) AND (Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception) AND (aspartate aminotransferase) AND (at risk of) AND (cannabinoid based medications) AND (cannabinoids) AND (cardiac disease) AND (clinically significant) AND (duration) AND (history) AND (less than 3 months) AND (more than three times normal) AND (pain) AND (serious) AND (severe) AND (significant) AND (substance use disorder) AND (suicidal ideation) AND (uncontrolled) AND (unprescribed) AND (urine drug screen) AND (within 90 days of study entry) AND ((adverse event) OR (hypersensitivity)) AND ((heart failure) OR (hypertension) OR (unstable ischemic heart disease)) AND ((arrhythmia) OR (myocardial infarction)) AND ((cannabis use disorder (CUD)) OR (dependence on cannabis)) AND ((bipolar disorder) OR (intolerance) OR (psychosis) OR (schizophrenia)) AND ((Current) OR (history)) AND ((Hepatic impairment) OR (renal function impairment)) AND ((Estimated Glomerular Filtration Rate (eGFR)) OR (serum creatinine level)) AND ((alcohol) OR (amphetamines) OR (cannabinoids) OR (cocaine) OR (methamphetamines) OR (opioids)) AND ((cannabinoids) OR (cannabis)))"}
{"candidate_id": "LLM01334", "doc_id": "NCT02510404_exc", "case_bucket": "or", "source_criterion": "1. Patients with other uncontrolled infections (see 2.3.2 for definitions) 2. Patients who received ATG, Campath, or other T cell immunosuppressive monoclonal antibodies in the last 28 days 3. Received donor lymphocyte infusion in last 28 days 4. Diagnosis of Omenn's syndrome or MHC class I deficiency 5. Active and uncontrolled malignancy 6. Pregnant or lactating 7. Unable to wean steroids to ≤0.5 mg/kg/day prednisone. 8. Patients with Grade 3 hyperbilirubinemia", "candidate_expression": "((ATG) AND (Active) AND (Campath) AND (Grade 3) AND (MHC class I deficiency) AND (Omenn's syndrome) AND (Pregnant) AND (T cell immunosuppressive monoclonal antibodies) AND (Unable) AND (donor lymphocyte infusion) AND (hyperbilirubinemia) AND (in last 28 days) AND (in the last 28 days) AND (lactating) AND (malignancy) AND (other uncontrolled infections) AND (prednisone) AND (steroids) AND (uncontrolled) AND (wean) AND (≤0.5 mg/kg/day))"}
{"candidate_id": "LLM01335", "doc_id": "NCT01866800_exc", "case_bucket": "or", "source_criterion": "History of acute coronary syndrome in the past 30 days. History of congesting heart failure with left ventricular ejection fraction <30% or exacerbation in the past 30 days. Current dialysis treatment. Known furosemide hypersensitivity. Contraindications to placement of a Foley catheter in the bladder.", "candidate_expression": "((Contraindications) AND (acute coronary syndrome in the past 30 days) AND (congesting heart failure) AND (dialysis treatment Current) AND (furosemide) AND (hypersensitivity) AND (placement of a Foley catheter bladder) AND ((exacerbation in the past 30 days) OR (left ventricular ejection fraction <30%)))"}
{"candidate_id": "LLM01336", "doc_id": "NCT03472508_inc", "case_bucket": "or", "source_criterion": "(1)= 45 years old; (2)A diagnosis or previous diagnosis of essential hypertension, including anyone currently taking antihypertensive drugs; or for those who have not taken antihypertensive drugs within the last 2 weeks, two consecutive examinations were conducted at least one day apart, and both sitting blood pressure (mean value of 3 measurements) met the following criteria: diastolic blood pressure (DBP) =90 mmHg or systolic blood pressure (SBP) =140 mmHg (the second blood pressure was measured at V1); (3)If a study participant is a woman of childbearing age, she agrees to use a reliable contraceptive method during the trial; (4)Voluntarily participates and has signed an informed consent form. (1)Completed MTHFR C677T gene polymorphism detection in run-in period or MTHFR C677T genotype already known in advance; (2)Exhibited good tolerance to enalapril and good overall medication compliance (>80%) in run-in period or previously exhibited good tolerance and adherence to ACEI drugs in previous medication history. (3)Voluntarily continues to participate in this study.", "candidate_expression": "((= 45 years) AND (=140 mmHg) AND (=90 mmHg) AND (>80%) AND (ACEI drugs) AND (MTHFR C677T) AND (Voluntarily) AND (Voluntarily participates) AND (agrees to use) AND (antihypertensive drugs) AND (childbearing age) AND (continues to participate in this study) AND (contraceptive method) AND (currently) AND (during the trial) AND (enalapril) AND (essential hypertension) AND (good) AND (good adherence to ACEI drugs) AND (good tolerance to ACEI drugs) AND (good tolerance to enalapril) AND (medication history) AND (not) AND (old) AND (overall medication compliance) AND (previously) AND (reliable) AND (signed an informed consent) AND (sitting blood pressure) AND (the trial) AND (two consecutive at least one day apart) AND (within the last 2 weeks) AND (woman) AND ((diastolic blood pressure (DBP)) OR (systolic blood pressure (SBP))) AND ((gene polymorphism detection) OR (genotype already known)) AND ((diagnosis) OR (previous)))"}
{"candidate_id": "LLM01337", "doc_id": "NCT03040024_exc", "case_bucket": "or", "source_criterion": "Emergency surgery Monitored Anesthesia Care (i.e., regional anesthesia alone without plans for general anesthesia) Surgery involving the eye, eyebrow, forehead, or frontal scalp near the sensor placement Poor health literacy Allergy, or have experienced any drug reaction to ketamine Pregnant or lactating Currently in active alcohol withdrawal", "candidate_expression": "((Allergy) AND (Emergency) AND (Emergency surgery) AND (Monitored Anesthesia Care) AND (Poor health literacy) AND (Pregnant) AND (Surgery eye eyebrow forehead frontal scalp) AND (alcohol withdrawal Currently active) AND (drug reaction) AND (ketamine) AND (lactating) AND (regional anesthesia alone) AND NOT (general anesthesia plans for))"}
{"candidate_id": "LLM01338", "doc_id": "NCT02970773_inc", "case_bucket": "other", "source_criterion": "Motor complete tetraplegia for at least 3 months Age from 18 to 74 years Body mass index (BMI) from 18 to 35kg/m2 Informed consent as documented by signature", "candidate_expression": "((Age) AND (BMI) AND (Body mass index) AND (at least 3 months) AND (complete) AND (from 18 to 35kg/m2) AND (from 18 to 74 years) AND (nformed consent as documented by signature) AND (tetraplegia))"}
{"candidate_id": "LLM01339", "doc_id": "NCT02787070_exc", "case_bucket": "other", "source_criterion": "General danger signs or symptoms of severe malaria Anaemia, defined as Hb <9g/dl G6PD deficiency (as determined by FST) Pregnant women as determined by Urine ß-HCG pregnancy test Known hypersensitivity to any of the drugs given", "candidate_expression": "((<9g/dl) AND (Anaemia) AND (G6PD deficiency) AND (Hb) AND (Pregnant women as determined by Urine ß-HCG pregnancy test) AND (drugs) AND (hypersensitivity) AND (malaria) AND (severe))"}
{"candidate_id": "LLM01340", "doc_id": "NCT02609425_inc", "case_bucket": "other", "source_criterion": "All patients with esophageal cancer who are deemed candidates for minimally invasive robot assisted Ivor Lewis esophagogastrectomy. Patients who provide written informed consent for the study.", "candidate_expression": "((Patients who provide written informed consent for the study.) AND (candidates) AND (esophageal cancer) AND (esophagogastrectomy minimally invasive robot assisted Ivor Lewis))"}
{"candidate_id": "LLM01341", "doc_id": "NCT02489045_inc", "case_bucket": "other", "source_criterion": "Be scheduled for trans-jugular liver biopsy the day of the ultrasound procedure. Be at least 21 years of age. Be medically stable. If a female of child-bearing potential, must have a negative pregnancy test. Be conscious and able to comply with study procedures. Have read and signed the IRB-approved Informed Consent form for participating in the study.", "candidate_expression": "((Have read and signed the IRB-approved Informed Consent form for participating in the study.) AND (age at least 21 years) AND (child-bearing potential) AND (female) AND (medically stable) AND (negative) AND (pregnancy test) AND (trans-jugular liver biopsy the day of the ultrasound procedure) AND (ultrasound procedure))"}
{"candidate_id": "LLM01342", "doc_id": "NCT03663387_exc", "case_bucket": "or", "source_criterion": "Uncontrolled hypertension or metabolic disease Neurodegenerative disorders (i.e. Parkinson disease. LBD, or FTD). Dementia or Mild cognitive impairment at baseline Long life major depression. Baseline scores =16 on the 17-item Hamilton Depression Scale at baseline. Long-life DSM-IV axis 1 disorders. Mental retardation. Substance abuse. Concurrent medication limiting validity of neuropsychological tests or imaging. Anti-depressants with anti-cholinergic properties Monoamine oxidase inhibitors (MAOi) Regular use of narcotic analgesics (>2 doses per week). Use of neuroleptics Use of anti-dementia medications (Aricept, Exelon, Razadyne) and memantine (Namenda)) or anti-Parkinsonian medications (Sinemet, amantadine, bromocriptine, pergolide, selegeline). Individuals taking over the counter memory enhancing or protecting medications (e.g. ginkgo biloba, vitamins) are not excluded. Implanted medical devices that are incompatible with MRI imaging. Radiation exposures exceeding annual Rad Worker limits. Heart failure stage D as defined by American Heart Association (7). Chronic kidney disease in stages = 4, as defined per National Kidney Foundation (8). Brain tumor and other neoplastic disorders outside the brain where disease itself or its treatment (radiation, chemotherapy) is likely to affect brain structure or function. Stroke when meeting criteria for total anterior, partial anterior or posterior circulation infarct according to the Oxford Community Stroke Project classification. Patients with clinically silent of lacunar strokes and transient ischemic attacks will not be excluded. Significant head trauma. Hydrocephalus. Hostility or refusal to cooperate", "candidate_expression": "((17-item Hamilton Depression Scale =16 at baseline) AND (Anti-depressants anti-cholinergic properties) AND (Aricept) AND (Baseline scores) AND (Brain tumor) AND (Chronic kidney disease) AND (Dementia) AND (Exelon) AND (FTD) AND (Heart failure) AND (Hostility) AND (Hydrocephalus) AND (LBD) AND (Long life major depression) AND (Long-life DSM-IV axis 1 disorders) AND (MRI imaging) AND (Mental retardation) AND (Mild cognitive impairment) AND (Monoamine oxidase inhibitors (MAOi)) AND (Namenda) AND (Neurodegenerative disorders) AND (Oxford Community Stroke Project classification) AND (Parkinson disease) AND (Radiation exposures exceeding annual Rad Worker limits) AND (Razadyne) AND (Sinemet) AND (Stroke total anterior partial anterior) AND (Substance abuse Concurrent) AND (amantadine) AND (anti-Parkinsonian medications) AND (anti-cholinergic) AND (anti-dementia medications) AND (bromocriptine) AND (chemotherapy likely to affect brain structure likely to affect brain function) AND (circulation infarct posterior) AND (cognitive impairment Mild) AND (ginkgo biloba) AND (head trauma Significant) AND (hypertension) AND (medical devices incompatible with MRI imaging) AND (medication limiting validity of neuropsychological tests limiting validity of imaging) AND (memantine) AND (metabolic disease) AND (narcotic analgesics Regular use >2 doses per week) AND (neoplastic disorders outside the brain) AND (neuroleptics) AND (over the counter memory enhancing medications) AND (over the counter memory protecting medications) AND (pergolide) AND (radiation) AND (refusal to cooperate) AND (selegeline) AND (stage D American Heart Association) AND (stages = 4 National Kidney Foundation) AND (vitamins))"}
{"candidate_id": "LLM01343", "doc_id": "NCT00061308_inc", "case_bucket": "or", "source_criterion": "Have had one prior platinum-based chemotherapy regimen for the treatment of primary disease. At least 4 weeks since last surgery or radiation therapy. Must have had a treatment-free interval of greater than 6 months following response to platinum. ECOG performance status of 0,1, or 2.", "candidate_expression": "((.) AND (0) AND (0,1) AND (At least 4 weeks since last surgery or radiation therapy) AND (ECOG performance status) AND (a treatment-free interval) AND (greater than 6 months following response to platinum) AND (last surgery) AND (platinum) AND (platinum-based chemotherapy regimen) AND (primary disease) AND (prior) AND (radiation therapy) AND (response to platinum))"}
{"candidate_id": "LLM01344", "doc_id": "NCT02555163_exc", "case_bucket": "other", "source_criterion": "Non papillary gross features of the tumor Anteriorly located tumor Patients criteria Poor performance status History of BCG sepsis History of bladder irradiation Contracted bladder", "candidate_expression": "((BCG) AND (Contracted bladder) AND (Non papillary gross features) AND (bladder irradiation History) AND (performance status Poor) AND (sepsis History) AND (tumor) AND (tumor Anteriorly located))"}
{"candidate_id": "LLM01345", "doc_id": "NCT02755701_exc", "case_bucket": "or", "source_criterion": "Child-Pugh score > 12 Having been diagnosed as HCC within the past 5 years Serum creatinine > 1.5mg/dl Serum bilirubin > 5.0mg/dl Presence of such complications as SBP, or hepatic encephalopathy(West Haven grade = 3) Patients who experienced organ failure by acute exacerbation of liver cirrhosis within the past 1 month Presence of serious cardiac or respiratory disease Contraindicated to either diuretics or BCAA Having commenced anti-viral treatment against hepatitis C, B within the past 1 month Pregnant or lactating women Chronic alcohol taker Woman patients who do not agree to the contraception from baseline to 12 month Unsuitable patients judged by investigator Patients participating in another clinical trial within 1 month", "candidate_expression": "((= 3) AND (> 1.5mg/dl) AND (> 12) AND (> 5.0mg/d) AND (BCAA) AND (Child-Pugh score) AND (Chronic) AND (Contraindicated) AND (HCC) AND (Patients participating in another clinical trial within 1 month) AND (Pregnant or lactating women) AND (SBP) AND (Serum bilirubin) AND (Serum creatinine) AND (West Haven grade) AND (Woman patients who do not agree to the contraception from baseline to 12 month) AND (acute exacerbation of liver cirrhosis) AND (alcohol taker) AND (anti-viral treatment) AND (cardiac disease) AND (complications) AND (diuretics) AND (hepatic encephalopathy) AND (hepatitis B) AND (hepatitis C) AND (organ failure) AND (past 1 month) AND (past 5 years) AND (respiratory disease) AND (serious))"}
{"candidate_id": "LLM01346", "doc_id": "NCT02431442_inc", "case_bucket": "or", "source_criterion": "Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures. Healthy obese male and female volunteers aged 18 to 55 years, inclusive. Heterozygous subjects may be 18 to 65 years inclusive. In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities. Body Mass Index of 30-40 kg/m2, inclusive. Heterozygous subjects may have a broader BMI range; to be eligible heterozygous subjects may have a BMI 27 -55 kg/ m2, inclusive. Stable body weight during the previous 6 months, based on Investigator judgment. Blood pressure <140/90 mmHg at Screening and D-1. Measurement may be repeated within 24 hours, based on Investigator judgment. Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1. Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD. Hormonal contraception must have started at least 3 months prior to screening. A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception. Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution. Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study. Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit. Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time. Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.", "candidate_expression": "((A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception.) AND (Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures.) AND (BMI 27 -55 kg/ m2, inclusive) AND (Blood pressure <140/90 mmHg at Screening and D-1) AND (Body Mass Index 30-40 kg/m2, inclusive) AND (Females) AND (Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1.) AND (Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD.) AND (Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study.) AND (Healthy) AND (Heterozygous) AND (Heterozygous 18 to 65 years inclusive) AND (Hormonal contraception at least 3 months prior to screening) AND (In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities.) AND (Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit.) AND (Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time.) AND (Measurement may be repeated within 24 hours, based on Investigator judgment.) AND (Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (aged 18 to 55 years, inclusive) AND (based on Investigator judgment) AND (body weight Stable during the previous 6 months) AND (childbearing potential) AND (female) AND (good general health) AND (heterozygous) AND (male) AND (obese) AND (serum pregnancy test negative at the Screening Visit and Day -1) AND NOT (pregnant))"}
{"candidate_id": "LLM01347", "doc_id": "NCT03126214_inc", "case_bucket": "or", "source_criterion": "Age = 65 years with one additional stroke risk factor (hypertension, diabetes, heart failure history of or left ventricular ejection fraction <0.40), previous stroke or transient ischemic attack). Atrial fibrillation and not on oral anticoagulation (OAC) therapy but eligible Atrial fibrillation on sub-optimal OAC", "candidate_expression": "((<0.40) AND (= 65 years) AND (Age) AND (Atrial fibrillation) AND (OAC) AND (history) AND (not) AND (one additional) AND (oral anticoagulation (OAC) therapy) AND (previous) AND (risk factor) AND (stroke) AND (sub-optimal) AND ((stroke) OR (transient ischemic attack)) AND ((diabetes) OR (heart failure) OR (hypertension) OR (left ventricular ejection fraction)))"}
{"candidate_id": "LLM01348", "doc_id": "NCT00305097_exc", "case_bucket": "or", "source_criterion": "Any condition/illness that may affect the study outcomes or would make participation potentially harmful such as pregnancy or breastfeeding, diabetes mellitus, heart disease, stroke, hypertension, malabsorption syndromes, GERD, a history of ulcer, according to a detailed medical history. Abnormal hepatic function (liver function test > twice the normal range), abnormal renal function (creatinine > 1.1 mg/dl), fasting plasma glucose in the diabetic range (>/= 126 mg/dl), or blood pressure > 140/90 mmHg. Present alcoholism or drug abuse or use of medications that could interfere with the treatment including bronchodilators, quinolone antibiotics, monoamine oxidase inhibitors, anxiolytics, ranitidine, corticosteroids, growth hormone, antihypertensives.", "candidate_expression": "((bronchodilators) AND (creatinine > 1.1 mg/dl >/= 126 mg/dl) AND (history of) AND (liver function test > twice the normal range) AND ((illness that may affect the study outcomes) OR (illness that would make participation potentially harmful)) AND ((blood pressure > 140/90 mmHg) OR (fasting plasma glucose in the diabetic range) OR (hepatic function Abnormal) OR (renal function abnormal)) AND ((alcoholism) OR (drug abuse) OR (medications that could interfere with the treatment)) AND ((antihypertensives) OR (anxiolytics) OR (corticosteroids) OR (growth hormone) OR (monoamine oxidase inhibitors) OR (quinolone antibiotics) OR (ranitidine)) AND ((GERD) OR (breastfeeding) OR (diabetes mellitus) OR (heart disease) OR (hypertension) OR (malabsorption syndromes) OR (pregnancy) OR (stroke) OR (ulcer)))"}
{"candidate_id": "LLM01349", "doc_id": "NCT01032109_inc", "case_bucket": "other", "source_criterion": "choroidal neovascularization caused by age-related macula degeneration no previous treatment a follow-up at least 12 months a baseline visual acuity ranging from a letter score of 0 to 70 on the Early Treatment Diabetic Retinopathy Study chart", "candidate_expression": "((Early Treatment Diabetic Retinopathy Study chart) AND (choroidal neovascularization) AND (follow-up at least 12 months) AND (macula degeneration age-related) AND (visual acuity baseline letter score of 0 to 70) AND NOT (treatment previous))"}
{"candidate_id": "LLM01350", "doc_id": "NCT03247738_exc", "case_bucket": "or", "source_criterion": "Inability to provide written informed consent Known history of prior intracranial bleeding On treatment with a P2Y12 receptor antagonist (ticlopidine, clopidogrel, prasugrel, ticagrelor) in the prior 10 days Known allergies to aspirin, ticagrelor or cangrelor On treatment with oral anticoagulant Treatment with glycoprotein IIb/IIIa inhibitors Fibrinolytics within 24 hours Active bleeding High risk of bleeding Known platelet count <80x106/mL Known hemoglobin <10 g/dL Intubated patients (prior to randomization) Known creatinine clearance <30 mL/minute or on hemodialysis. Known severe hepatic dysfunction Patients with sick sinus syndrome (SSS) or high degree AV block without pacemaker protection Current treatment with drugs interfering with CYP3A4 metabolism (to avoid interaction with ticagrelor): Ketoconazole, itraconazole, voriconazole, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, and telithromizycin. Pregnant or lactating females.", "candidate_expression": "((<10 g/dL) AND (<30 mL/minute) AND (<80x106/mL) AND (Active bleeding) AND (CYP3A4 metabolism) AND (Fibrinolytics) AND (High risk) AND (Inability to provide written informed consent) AND (Intubated) AND (P2Y12 receptor antagonist) AND (SSS) AND (allergies) AND (anticoagulant) AND (bleeding) AND (drugs) AND (females) AND (glycoprotein IIb/IIIa inhibitors) AND (hemoglobin) AND (hepatic dysfunction) AND (high degree) AND (interfering with) AND (intracranial bleeding) AND (oral) AND (pacemaker) AND (platelet count) AND (prior) AND (prior 10 days) AND (prior to randomization) AND (randomization) AND (severe) AND (ticagrelor) AND (within 24 hours) AND (without) AND ((aspirin) OR (cangrelor) OR (ticagrelor)) AND ((creatinine clearance) OR (hemodialysis)) AND ((AV block) OR (sick sinus syndrome)) AND ((Ketoconazole) OR (atazanavir) OR (clarithromycin) OR (indinavir) OR (itraconazole) OR (nefazodone) OR (nelfinavir) OR (ritonavir) OR (saquinavir) OR (telithromizycin) OR (voriconazole)) AND ((Pregnant) OR (lactating)) AND ((clopidogrel) OR (prasugrel) OR (ticagrelor) OR (ticlopidine)))"}
```
