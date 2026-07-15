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
{"candidate_id": "LLM01401", "doc_id": "NCT01490034_inc", "case_bucket": "or", "source_criterion": "Weight stable (<3 kg weight change within last 3 months) Constant habitual activity patterns (no deviation > 1x/wk at 30 min/session within last 3 months) Constant habitual diet patterns within last 3 months Willingness to eat a chocolate-flavored snack at test sessions and two week training period No allergies to any test foods Not planning to change use of medications known to influence appetite or metabolism Not diabetic No history of GI pathology Non-smoker for one year or more", "candidate_expression": "((<3 kg weight change) AND (Constant habitual activity patterns) AND (Constant habitual diet patterns) AND (GI pathology) AND (No) AND (Non) AND (Not) AND (Weight) AND (Willingness to eat a chocolate-flavored snack) AND (allergies) AND (at test sessions) AND (at two week training period) AND (diabetic) AND (for one year or more) AND (history) AND (medications known to influence appetite) AND (medications known to influence metabolism) AND (no deviation > 1x/wk at 30 min/session within last 3 months) AND (planning to change) AND (smoker) AND (stable) AND (test foods) AND (within last 3 months))"}
{"candidate_id": "LLM01402", "doc_id": "NCT03164096_inc", "case_bucket": "other", "source_criterion": "adult female partner aged 18 to 40 years. scheduled for elective cesarean section.", "candidate_expression": "((adult) AND (aged 18 to 40 years) AND (cesarean section scheduled for elective) AND (female) AND (female partner))"}
{"candidate_id": "LLM01403", "doc_id": "NCT00954850_inc", "case_bucket": "or", "source_criterion": "Adults (18 and older) with physiologically confirmed SA or mild-moderate asthma and followed by an asthma specialist for at least 6 months. Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma). Must have good compliance with medications Patients with asthma and COPD.", "candidate_expression": "((18 and older 18 and older) AND (Adults) AND (COPD) AND (Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma).) AND (SA mild moderate) AND (asthma) AND (followed by an asthma specialist for at least 6 months) AND (good compliance) AND (medications))"}
{"candidate_id": "LLM01404", "doc_id": "NCT02894268_exc", "case_bucket": "or", "source_criterion": "Bismuth compounds, acid inhibitor, or antibiotics during 4 weeks before the patient is enrolled Allergic to the medications Upper gastrointestinal surgery history Serious heart insufficiency, liver insufficiency, renal insufficiency and other serious medical problems Evidence of blood dyscrasia Pregnant and lactating women Can't express his complain correctly and can't cooperate with the researcher", "candidate_expression": "((Allergic) AND (Bismuth compounds) AND (Evidence) AND (Pregnant) AND (Serious) AND (Upper gastrointestinal surgery) AND (acid inhibitor) AND (antibiotics) AND (blood dyscrasia) AND (during 4 weeks before the patient is enrolled) AND (heart insufficiency) AND (history) AND (lactating) AND (liver insufficiency) AND (medications) AND (other) AND (renal insufficiency) AND (serious medical problems) AND (the patient is enrolled) AND (women))"}
{"candidate_id": "LLM01405", "doc_id": "NCT01720394_exc", "case_bucket": "other", "source_criterion": "fetal anomalies contra-indications for medical induction of labor placental pathologies St.p. surgery with opening the uterine cavity (incl. caesarean section) PROM multiple gestations < 37-0 weeks of gestation St.p. cervical tear", "candidate_expression": "((PROM) AND (St.p.) AND (caesarean section) AND (cervical tear) AND (contra-indications) AND (fetal anomalies) AND (gestation < 37-0 weeks) AND (medical induction of labor) AND (multiple gestations) AND (placental pathologies) AND (surgery with opening the uterine cavity))"}
{"candidate_id": "LLM01406", "doc_id": "NCT02200978_inc", "case_bucket": "other", "source_criterion": "Patients less than 16 years old with newly diagnosed PML-RARa positive acute promyelocytic leukemia.", "candidate_expression": "((PML-RARa) AND (acute promyelocytic leukemia) AND (less than 16 years) AND (old) AND (positive))"}
{"candidate_id": "LLM01407", "doc_id": "NCT02557386_inc", "case_bucket": "scope", "source_criterion": "Male sex ASA status I or II BMI between 20 and 34 kg/m2 Cruciate ligament of the knee reconstructive surgery No contraindications to general and regional anesthesia", "candidate_expression": "((ASA status) AND (BMI) AND (Cruciate ligament of the knee) AND (I or II) AND (Male) AND (No) AND (between 20 and 34 kg/m2) AND (contraindications) AND (general anesthesia) AND (reconstructive surgery) AND (regional anesthesia))"}
{"candidate_id": "LLM01408", "doc_id": "NCT00904202_inc", "case_bucket": "or", "source_criterion": "1. Had a diagnosis of PHN, DN, CRPS, carpal tunnel syndrome, HIV neuropathy, idiopathic sensory neuropathy, or other peripheral neuropathy (upon mutual agreement of the sponsor and investigator) 2. Patients with PHN must have had pain >3 months after rash healing 3. Patients with DN must have had Type I or II diabetes and painful distal symmetric sensorimotor polyneuropathy with or without dynamic allodynia of the lower extremities 4. Patients with CRPS must have met current IASP (International Association for the Study of Pain) diagnostic criteria 5. Patients with carpal tunnel syndrome must have had a diagnosis by combination clinical neurological examination (e.g., Phalen's and Tinel's signs), electrodiagnostic testing, and daily painful symptoms of at least 3 months' duration 6. Patients with HIV neuropathy must have had HIV, subjective symptoms of painful peripheral neuropathy, and daily painful symptoms of at least 3 months' duration 7. Patients with idiopathic sensory neuropathy must have had pain of at least 3 months' duration 8. Reached an average daily pain rating during the baseline week of pain ratings greater than 4 on the 0-to-10 numerical pain rating scale (Question 5 of the BPI) 9. Had never received an analgesic regimen that contained lidocaine or gabapentin", "candidate_expression": "((0-to-10 numerical pain rating scale) AND (>3 months) AND (CRPS) AND (DN) AND (HIV) AND (HIV neuropathy) AND (IASP (International Association for the Study of Pain) diagnostic criteria) AND (PHN) AND (Phalen's signs) AND (Tinel's signs) AND (Type I diabetes) AND (Type II diabetes) AND (after rash healing) AND (analgesic regimen) AND (at least 3 months' duration) AND (average) AND (baseline week) AND (carpal tunnel syndrome) AND (clinical neurological examination) AND (daily) AND (daily pain rating) AND (distal) AND (during the baseline week) AND (dynamic allodynia) AND (electrodiagnostic) AND (gabapentin) AND (greater than 4) AND (idiopathic) AND (idiopathic sensory neuropathy) AND (lidocaine) AND (met) AND (neuropathy) AND (pain) AND (painful) AND (painful symptoms) AND (peripheral neuropathy) AND (rash healing) AND (sensorimotor polyneuropathy) AND (sensory neuropathy) AND (subjective symptoms) AND (symmetric) AND (upon mutual agreement of the sponsor and investigator))"}
{"candidate_id": "LLM01409", "doc_id": "NCT03430284_inc", "case_bucket": "other", "source_criterion": "35-75 years old; diagnosed as type 2 diabetes according to the criteria of the World Health Organization in 1999.", "candidate_expression": "((old 35-75 years old) AND (type 2 diabetes criteria of the World Health Organization in 1999))"}
{"candidate_id": "LLM01410", "doc_id": "NCT03018171_exc", "case_bucket": "or", "source_criterion": "Suspect or certainty of fetal malformation, Presence of conditions such as preeclampsia, multiparity, preterm labor History of adverse reaction to a-2 adrenergic agonists Nicotine addiction Chronic use of opioid", "candidate_expression": "((Nicotine addiction) AND (a-2 adrenergic agonists) AND (adverse reaction) AND (fetal malformation Suspect certainty) AND (multiparity) AND (opioi Chronic use) AND (preeclampsia) AND (preterm labor))"}
{"candidate_id": "LLM01411", "doc_id": "NCT03250507_inc", "case_bucket": "other", "source_criterion": "Elective open abdominal hysterectomy with midline incision, age > 18 years, American Society of Anesthesiologist classification score (ASA classification) 1-3.", "candidate_expression": "((ASA classification) AND (American Society of Anesthesiologist classification score 1-3) AND (age > 18 years) AND (open abdominal hysterectomy Elective midline incision))"}
{"candidate_id": "LLM01412", "doc_id": "NCT03249272_inc", "case_bucket": "or", "source_criterion": "Men or women aged 18 years or older Patients presenting for CMR with the clinical diagnosis of hypertrophic cardiomyopathy based on left ventricular wall thickness of at least =15 mm in the absence of any other cardiac or systemic cause of hypertrophy Patients presenting for CMR with the clinical diagnosis of idiopathic dilated cardiomyopathy based upon left ventricular ejection fraction =40%, LV end-diastolic diameter =55 mm or left ventricular end-systolic diameter =45 mm, and the absence of coronary stenoses on angiography. Patients presenting for CMR evaluation of chest pain but without evidence of obstructive coronary artery disease either by coronary angiography or stress testing.", "candidate_expression": "((Men) AND (aged 18 years or older) AND (angiography) AND (chest pain) AND (hypertrophic cardiomyopathy) AND (idiopathic dilated cardiomyopathy) AND (left ventricular wall thickness at least =15 mm) AND (women) AND NOT (coronary stenoses) AND NOT (obstructive coronary artery disease) AND ((cardiac cause of hypertrophy) OR (systemic cause of hypertrophy)) AND ((LV end-diastolic diameter =55 mm) OR (left ventricular ejection fraction =40%) OR (left ventricular end-systolic diameter =45 mm)) AND ((coronary angiography) OR (stress testing)))"}
{"candidate_id": "LLM01413", "doc_id": "NCT02939872_exc", "case_bucket": "or", "source_criterion": "Contraindication to antiplatelet therapy Need to continue clopidogrel due to stroke, peripheral disease, significant carotid disease or recent acute coronary syndrome Major bleeding history or bleeding diathesis Pregnancy", "candidate_expression": "((Contraindication) AND (Major) AND (Need to) AND (Pregnancy) AND (acute coronary syndrome) AND (antiplatelet therapy) AND (bleeding) AND (bleeding diathesis) AND (carotid disease) AND (clopidogrel) AND (continue) AND (history) AND (peripheral disease) AND (recent) AND (significant) AND (stroke))"}
{"candidate_id": "LLM01414", "doc_id": "NCT01700790_exc", "case_bucket": "or", "source_criterion": "Non-compliance with DOTPlus. Alternatively DOT can be done by telephoning patient on a daily basis 5 times a week and having patient annotate taking drug in a log which would be reviewed by clinic staff History of being treated for tuberculosis in the prior 2 years unless there is DST, including PCR testing, showing sensitivity to rifamycin. Known hypersensitivity to rifampin or rifabutin. Liver enzymes greater than 2 times ULN. Bilirubin greater than 2 times ULN. Serum creatinine greater than 3 times ULN. Hemoglobin less than 7.0 gms even if receiving erythropoietin. Absolute neutrophil count less than 750 cells/mm3 even if receiving G-CSF. Fasting triglycerides greater than 400 mg/dL. Fasting cholesterol > 1.6 upper limits of normal. GI intolerance of tuberculosis medications requiring discontinuation of tuberculosis medications. Fasting glucose greater 150 mg/dL. Pregnant women. Use of one of the prohibited medications Any condition that the investigators feel could compromise the use of the current medication. Have a CD4 cell count of 50 cells/mm3or less Hepatitis B or C infection Alcohol or illicit drug use, which in the investigators opinion may affect participation in study.", "candidate_expression": "((Absolute neutrophil count less than 750 cells/mm3) AND (Alcohol use) AND (Any condition that the investigators feel could compromise the use of the current medication.) AND (Bilirubin greater than 2 times ULN) AND (CD4 cell count 50 cells/mm3or less) AND (DOTPlus) AND (DST) AND (Fasting cholesterol > 1.6 upper limits of normal) AND (Fasting glucose greater 150 mg/dL) AND (Fasting triglycerides greater than 400 mg/dL) AND (GI intolerance) AND (Hemoglobin less than 7.0 gms) AND (Hepatitis B) AND (Hepatitis C) AND (Liver enzymes greater than 2 times ULN) AND (Non-compliance) AND (PCR testing) AND (Pregnant) AND (Serum creatinine greater than 3 times ULN) AND (Use of one of the prohibited medications) AND (discontinuation) AND (hypersensitivity) AND (illicit drug use) AND (rifabutin) AND (rifampin) AND (rifamycin) AND (sensitivity) AND (treated in the prior 2 years) AND (tuberculosis) AND (tuberculosis medications) AND (women))"}
{"candidate_id": "LLM01415", "doc_id": "NCT02983214_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure, history of ventricular tachycardia, ventricular fibrillation or multifocal ventricular extrasystoles or QTc prolongation. Patients with atrial fibrillation taking any anticoagulant therapy or patients with a history of cardioembolic ischemic stroke or hemorrhagic stroke. Patients with a history (= 12 months) of acute coronary syndrome receiving dual antiplatelet therapy, or patients receiving monotherapy with aspirin. Patients with hepatic impairment (child-Pugh staging, calibration = 5) or renal impairment (creatinine clearance = 30ml / min), recent peptic ulcer, a history of hypersensitivity to cilostazol, cancer patients undergoing treatment.", "candidate_expression": "((Congestive heart failure) AND (QTc prolongation) AND (acute coronary syndrome) AND (anticoagulant therapy) AND (aspirin) AND (atrial fibrillation) AND (cancer) AND (child-Pugh staging calibration = 5) AND (cilostazol) AND (creatinine clearance = 30ml / min) AND (dual antiplatelet therapy) AND (hemorrhagic stroke = 12 months) AND (hepatic impairment) AND (hypersensitivity history of) AND (ischemic stroke cardioembolic) AND (monotherapy) AND (multifocal ventricular extrasystoles) AND (peptic ulcer recent) AND (renal impairment) AND (treatment) AND (ventricular fibrillation) AND (ventricular tachycardia history of))"}
{"candidate_id": "LLM01416", "doc_id": "NCT03124329_exc", "case_bucket": "or", "source_criterion": "Molar teeth Milller Class 4 recession defects Pregnancy (Self-reported) Smoking Uncontrolled local or systemic diseases that affects wound healing (diabetes, autoimmune or inflammatory disorders) Past history of systemic steroid use over 2 weeks within the last 2 years Poor oral hygiene on a non-compliant individual Ibuprofen Allergy/interlerance Anticoagulant therapy (e.g. Warfarin, Plavix, etc.), will not be automatic exclusion but patients will be required to have INR test performed and have values between 2.0 to 3. Physician consultation will be requested to determine whether anticoagulant therapy can be discontinued for 3 days prior to surgery. Objection to blood draw or application of blood products Students and staff from USC Ostrow school of Dentistry will not be recruited for this study", "candidate_expression": "((Anticoagulant therapy) AND (Class 4) AND (INR test) AND (Ibuprofen) AND (Milller) AND (Molar teeth) AND (Past history) AND (Poor oral hygiene) AND (Pregnancy) AND (Smoking) AND (Uncontrolled) AND (anticoagulant therapy) AND (between 2.0 to 3) AND (non-compliant) AND (over 2 weeks) AND (recession defects) AND (systemic steroid) AND (that affects wound healing) AND (within the last 2 years) AND ((autoimmune disorders) OR (diabetes) OR (inflammatory disorders)) AND ((Allergy) OR (interlerance)) AND ((Plavix) OR (Warfarin)) AND ((diseases local) OR (systemic diseases)))"}
{"candidate_id": "LLM01417", "doc_id": "NCT02339974_exc", "case_bucket": "or", "source_criterion": "Heart Team assessment of operability (the heart team considers the patient to be a good surgical candidate). Evidence of an acute myocardial infarction = 1 month (30 days) before the intended treatment [defined as: Q wave MI, or non-Q wave MI with total CK elevation of CK-MB = twice normal in the presence of MB elevation and/or troponin level elevation (WHO definition)]. Untreated, severe, left sided valvular heart disease including mitral regurgitation or stenosis, and aortic regurgitation or stenosis. Mean pulmonary artery pressures =40mmHG and PVR >4 woods units as assessed by right heart catheterization. Any therapeutic invasive cardiac procedure resulting in a permanent implant that is performed within 30 days of the index procedure. Examples of permanent implant would include any new heart valve. Implantation of a permanent pacemaker is excluded. Patients with planned concomitant surgical or transcatheter ablation for Atrial Fibrillation. Leukopenia (WBC < 3000 cell/mL), acute anemia (Hgb < 9 g/dL), Thrombocytopenia (Plt < 50,000 cell/mL). Hemodynamic or respiratory instability requiring inotropic support, mechanical ventilation or mechanical heart assistance within 30 days of screening evaluation. Need for emergency surgery for any reason. Left ventricular ejection fraction <40%. Echocardiographic evidence of intracardiac mass, thrombus or vegetation. Active upper GI bleeding within 3 months (90 days) prior to procedure. A known contraindication or hypersensitivity to all anticoagulation regimens, or inability to be anticoagulated for the study procedure. Recent CVA clinically confirmed (by neurologist) or neuroimaging confirmed stroke or transient ischemic attack (TIA) within 6 months (180 days) of the procedure. Estimated life expectancy < 1 year from conditions other than TR. Expectation that patient will not improve despite treatment of tricuspid regurgitation Currently participating in another investigational cardiac device study or any other clinical trial, including drugs or biologics. Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials. Active bacterial endocarditis within 6 months (180 days) of procedure. Patients with signs or symptoms of SVC syndrome, or hepatic cirrhosis not felt due to passive congestion from TR.", "candidate_expression": "((< 1 year) AND (< 3000 cell/mL) AND (< 50,000 cell/mL) AND (< 9 g/dL) AND (<40%) AND (= 1 month (30 days) before the intended treatment) AND (=40mmHG) AND (>4 woods units) AND (Active) AND (Atrial Fibrillation) AND (CVA) AND (Echocardiographic) AND (Estimated life expectancy) AND (Heart Team assessment of operability) AND (Hemodynamic instability) AND (Hgb) AND (Left ventricular ejection fraction) AND (Leukopenia) AND (Mean pulmonary artery pressures) AND (Need for) AND (PVR) AND (Plt) AND (SVC syndrome) AND (Thrombocytopenia) AND (Untreated) AND (WBC) AND (acute anemia) AND (acute myocardial infarction) AND (anticoagulated) AND (anticoagulation regimens) AND (aortic regurgitation) AND (aortic stenosis) AND (bacterial endocarditis) AND (cardiac procedure) AND (clinically confirmed (by neurologist)) AND (concomitant) AND (confirmed) AND (contraindication) AND (emergency surgery) AND (excluded) AND (for the study procedure) AND (heart team considers the patient to be a good surgical candidate) AND (heart valve) AND (hepatic cirrhosis) AND (hypersensitivity) AND (inability) AND (inotropic support) AND (intracardiac mass) AND (intracardiac thrombus) AND (intracardiac vegetation) AND (invasive) AND (left sided) AND (mechanical heart assistance) AND (mechanical ventilation) AND (mitral regurgitation) AND (mitral stenosis) AND (neuroimaging) AND (of procedure) AND (passive congestion from TR) AND (permanent implant) AND (permanent pacemaker) AND (planned) AND (procedure) AND (respiratory instability) AND (right heart catheterization) AND (screening evaluation) AND (severe) AND (stroke) AND (study procedure) AND (surgical ablation) AND (the index procedure) AND (the procedure) AND (therapeutic) AND (transcatheter ablation) AND (transient ischemic attack (TIA)) AND (upper GI bleeding) AND (valvular heart disease) AND (within 3 months (90 days) prior to procedure) AND (within 30 days of screening evaluation) AND (within 30 days of the index procedure) AND (within 6 months (180 days) of procedure) AND (within 6 months (180 days) of the procedure))"}
{"candidate_id": "LLM01418", "doc_id": "NCT02965027_inc", "case_bucket": "or", "source_criterion": "Male and female Active-duty SMs or Veterans aged 18 or older who are in good general health. History of blast and/or impact head trauma mTBI meeting Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria, which define mTBI as an injury to the head causing at least one of the following: alteration in consciousness (for up to 24 hours after the injury), loss of consciousness 0-30 minutes, and/or post-traumatic amnesia up to 1 day post-injury. If available, the Glasgow Coma Scale score must be 13-15, and head imaging findings (if imaging was performed) must be negative. Frequent HAs that started within 3months after a head injury. The HAs either 1) must last 4 or more hours a day and reach a moderate to severe intensity at any point during the headache, or 2) may be of any severity or duration if the participant takes a triptan or ergotamine. HAs meeting these criteria must have been present on average at least 8 days per 4-week period, starting within 30 days after head injury and occurring by self-report for at least 3 months prior to the Initial Screening Visit. The 4-week HA frequency/severity criteria must be confirmed during the Preliminary Screening Period. Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study. Participants must have English fluency sufficient to complete study measures.", "candidate_expression": "((0-30 minutes) AND (13-15) AND (18 or older) AND (Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria) AND (Frequent) AND (Glasgow Coma Scale) AND (HAs) AND (History of) AND (Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study.) AND (a head injury) AND (aged) AND (at least 3 months prior to the Initial Screening Visit) AND (at least 8 days per 4-week period) AND (blast) AND (findings) AND (for up to 24 hours after the injury) AND (good general health) AND (head imaging) AND (impact head trauma) AND (last 4 or more hours a day) AND (meeting) AND (moderate to severe intensity) AND (negative) AND (the Initial Screening Visit) AND (the injury) AND (up to 1 day post-injury) AND (within 30 days after head injury) AND (within 3months after a head injury) AND ((Male) OR (female)) AND ((alteration in consciousness) OR (loss of consciousness) OR (post-traumatic amnesia)) AND ((Active-duty SMs) OR (Veterans)) AND ((ergotamine) OR (triptan)))"}
{"candidate_id": "LLM01419", "doc_id": "NCT02003339_inc", "case_bucket": "or", "source_criterion": "Early, intermediate, advanced, non metastatic Hepatocellular Carcinoma. Indication for radioembolization validated after pluridisciplinary committee meeting. Isolated target on initial imagery (invasive hepatocellular carcinoma excluded) WHO (World Health organization) Performance status: 0, 1 or 2 If cirrhosis, Child A score with total bilirubin less than 30 micromoles per liter Creatinine clearance more or equal to 30 mL/min Patient informed and consent signature obtained", "candidate_expression": "((Child score A) AND (Creatinine clearance more or equal to 30 mL/min) AND (Hepatocellular Carcinoma metastatic) AND (Indication) AND (Patient informed and consent signature obtained) AND (WHO (World Health organization) Performance status 0, 1 or 2) AND (cirrhosis) AND (radioembolization Indication) AND (total bilirubin less than 30 micromoles per liter) AND ((Early) OR (advanced) OR (intermediate)))"}
{"candidate_id": "LLM01420", "doc_id": "NCT03187639_exc", "case_bucket": "or", "source_criterion": "Atrial fibrillation of new onset or when rate control has been difficult Known bigemini/trigeminy Prior CABG surgery Allergic to contrast Advanced renal impairment Significant valve disease (severe aortic stenosis or regurgitation; severe mitral regurgitation) Life expectancy <12 months Inclusion in another trial without prior agreement with CI", "candidate_expression": "((<12 months) AND (Advanced renal impairment) AND (Allergic) AND (Atrial fibrillation) AND (CABG surgery) AND (Inclusion in another trial without prior agreement with CI) AND (Life expectancy) AND (Prior) AND (aortic stenosis) AND (bigemini) AND (contrast) AND (mitral regurgitation) AND (new onset) AND (rate control has been difficult) AND (regurgitation) AND (severe) AND (trigeminy) AND (valve disease))"}
{"candidate_id": "LLM01421", "doc_id": "NCT02102243_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure or coronary artery disease Blood pressure averaging > 159/99 mmHg Serum creatinine > 1.5 mg/dL Diabetes mellitus or other systemic illness Left ventricular hypertrophy by echocardiography or ECG Pregnancy Hypersensitivity to spironolactone, chlorthalidone, amlodipine, human recombinant insulin or Definity Any history of substance abuse (other than tobacco) History of gouty arthritis Patients with right-to-left, bi-directional, or transient right-to-left cardiac shunts Hypersensitivity to perflutren, blood, blood products or albumin", "candidate_expression": "((Blood pressure > 159/99 mmHg) AND (Congestive heart failure) AND (Diabetes mellitus) AND (ECG) AND (Hypersensitivity) AND (Left ventricular hypertrophy) AND (Pregnancy) AND (Serum creatinine > 1.5 mg/dL) AND (albumin) AND (amlodipine) AND (blood) AND (blood products) AND (cardiac shunts transient right-to-left) AND (chlorthalidone) AND (coronary artery disease) AND (echocardiography) AND (gouty arthritis right-to-left, bi-directional) AND (human recombinant insulin) AND (perflutren) AND (spironolactone) AND (substance abuse) AND (systemic illness) AND NOT (tobacco))"}
{"candidate_id": "LLM01422", "doc_id": "NCT02396732_inc", "case_bucket": "or", "source_criterion": "Age 18 years or older Blunt or penetrating trauma Requires VTE thromboprophylaxis High-risk for VTE", "candidate_expression": "((Age 18 years or older) AND (Blunt trauma) AND (VTE) AND (VTE High-risk) AND (penetrating trauma) AND (thromboprophylaxis))"}
{"candidate_id": "LLM01423", "doc_id": "NCT00426751_inc", "case_bucket": "or", "source_criterion": "Women must be postmenopausal (i.e.12 months without menstrual period), or surgically sterile, i.e. women of child bearing potential are not allowed to be included into the study. In cases of doubt a pregnancy test should be performed. (NB -post menopausal women currently receiving hormone replacement are permissible) Acute myocardial infarction < 12 h defined as: 1. Angina or equivalent symptoms > 20 min and 2. ST elevation in 2 contiguous ECG leads (= 2 mm precordial lead, = 1 mm limb lead). This ECG recording serves as baseline ECG, i.e. ECG I. Planned primary percutaneous coronary intervention The subject has given written informed, dated consent to participate in the study", "candidate_expression": "((Acute myocardial infarction < 12 h) AND (Planned) AND (ST elevation) AND (Women) AND (child bearing potential) AND (contiguous ECG leads 2) AND (given written informed consent) AND (limb lead 1 mm) AND (postmenopausal) AND (precordial lead 2 mm) AND (pregnancy test doubt) AND (primary percutaneous coronary intervention) AND (surgically sterile) AND (women) AND NOT (menstrual period 12 months) AND ((Angina) OR (Angina symptoms)))"}
{"candidate_id": "LLM01424", "doc_id": "NCT01801072_exc", "case_bucket": "or", "source_criterion": "History of seizures within last 10 years History of epilepsy History of prior stroke Currently prescribed medication with anti-epileptic activity (keppra, dilantin, tegretol, lamictal, topamax, etc.) Brain tumor Pregnant or nursing woman Known levetiracetam allergy", "candidate_expression": "((Brain tumor) AND (Pregnant) AND (allergy) AND (anti-epileptic activity) AND (dilantin) AND (epilepsy) AND (keppra) AND (lamictal) AND (levetiracetam) AND (medication) AND (nursing) AND (prior) AND (seizures) AND (stroke) AND (tegretol) AND (topamax) AND (within last 10 years) AND (woman))"}
{"candidate_id": "LLM01425", "doc_id": "NCT03080493_inc", "case_bucket": "other", "source_criterion": "15 weeks 0 days gestational age - 23 weeks 5 days gestational age at time of dilator insertion Able to read and write in English Active cell phone with text messaging capability Ride home from dilator insertion clinic appointment", "candidate_expression": "((15 weeks 0 days - 23 weeks 5 days) AND (Able to read and write in English) AND (Active cell phone with text messaging capability) AND (Ride home) AND (at time of dilator insertion) AND (dilator insertion) AND (gestational age))"}
```
