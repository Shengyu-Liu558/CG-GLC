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
{"candidate_id": "LLM07576", "doc_id": "NCT03034837_inc", "case_bucket": "other", "source_criterion": "generally healthy grade 1-2 school children with written parental consent with at least 1 sound and fully erupted permanent first molar", "candidate_expression": "((at least 1) AND (children) AND (fully erupted) AND (generally healthy) AND (grade 1-2 school) AND (permanent first molar) AND (sound) AND (with written parental consent))"}
{"candidate_id": "LLM07577", "doc_id": "NCT02224040_inc", "case_bucket": "or", "source_criterion": "Blood culture-proven typhoid fever (S. typhi or S. paratyphi) Signed informed consent to participate in the study.", "candidate_expression": "((Blood culture) AND (S. paratyphi) AND (S. typhi) AND (Signed informed consent to participate in the study.) AND (proven) AND (typhoid fever))"}
{"candidate_id": "LLM07578", "doc_id": "NCT03208465_inc", "case_bucket": "or", "source_criterion": "Men or women at least 19 years of age Type 2 diabetes mellitus Stable coronary artery disease Global myocardial perfusion reserve (MPR) index < 2.5 The patient or guardian agrees to the study protocol and the schedule of clinical and dynamic SPECT follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site.", "candidate_expression": "((Global myocardial perfusion reserve (MPR) index < 2.5) AND (Type 2 diabetes mellitus) AND (age at least 19 years) AND (coronary artery disease Stable) AND (informed, written consent) AND ((Men) OR (women)))"}
{"candidate_id": "LLM07579", "doc_id": "NCT02478346_inc", "case_bucket": "or", "source_criterion": "Adult patients (age = 18) Diagnosed by preoperative imaging modalities to have a brain tumor (including metastatic brain tumors) or vascular lesions (aneurysm, arteriovenous malformation or arteriovenous fistula) requiring surgical intervention. The patient is determined by a board certified neurosurgeon to have a tumor or vascular lesion that would take up fluorescein Patient or legally authorized representative provides written informed consent to enroll in this study", "candidate_expression": "((= 18) AND (Adult) AND (Patient or legally authorized representative provides written informed consent to enroll in this study) AND (age) AND (aneurysm) AND (arteriovenous fistula) AND (arteriovenous malformation) AND (brain tumor) AND (fluorescein) AND (imaging modalities) AND (metastatic brain tumors) AND (preoperative) AND (surgical intervention) AND (tumor) AND (vascular lesion) AND (vascular lesions) AND (would take up fluorescein))"}
{"candidate_id": "LLM07580", "doc_id": "NCT01799681_exc", "case_bucket": "or", "source_criterion": "any neurological conditions other than PD; significant musculoskeletal or cardiopulmonary diseases; other disorders that may affect balance or locomotion; taken any structured behavioral or exercise programs in the past 3 months or they are receiving regular physical rehabilitation at present; unstable condition on anti-parkinsonian medications; surgical interventions for PD; communication or cognitive deficits with mini-mental state examination, (MMSE) <24/30 (Folstein et al., 1975); a history of more than two falls in the previous 12 months.", "candidate_expression": "((<24/30) AND (PD) AND (anti-parkinsonian medications) AND (at present) AND (cardiopulmonary diseases) AND (cognitive deficits) AND (communication deficits) AND (disorders that may affect balance or locomotion) AND (falls) AND (history) AND (in the past 3 months) AND (in the previous 12 months) AND (mini-mental state examination, (MMSE)) AND (more than two) AND (musculoskeletal diseases) AND (neurological conditions) AND (other than) AND (regular physical rehabilitation) AND (significant) AND (structured behavioral programs) AND (structured exercise programs) AND (surgical interventions for PD) AND (unstable condition))"}
{"candidate_id": "LLM07581", "doc_id": "NCT03194074_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for laser laryngeal surgery under general anesthesia with either Propofol or desflurane based technique.", "candidate_expression": "((general anesthesia) AND (laser laryngeal surgery scheduled) AND ((Propofol) OR (desflurane)))"}
{"candidate_id": "LLM07582", "doc_id": "NCT02689089_inc", "case_bucket": "or", "source_criterion": "Males or non-pregnant, non-nursing females between the ages of 2-65 years LTBI diagnosis as per Canadian TB Standards using either the Tuberculin Skin Test (TST) or the Interferon Gamma Release Assay (IGRA) Children 2-5 years with negative TSTs who have been in close contact with a case of active TB disease recently Able and willing to provide fully informed consent or parent/guardian able to provide consent", "candidate_expression": "((2-5) AND (2-65 years) AND (Able and willing to provide fully informed consent or parent/guardian able to provide consent) AND (Children) AND (IGRA) AND (Interferon Gamma Release Assay) AND (LTBI) AND (Males) AND (TST) AND (TSTs) AND (Tuberculin Skin Test) AND (ages) AND (females) AND (negative) AND (non-pregnant, non-nursing) AND (years))"}
{"candidate_id": "LLM07583", "doc_id": "NCT02734173_exc", "case_bucket": "or", "source_criterion": "<18 years old Evidence of decompensated liver disease HOMA IR< 2.0 HIV seropositivity Chronic HBV/HIV infection Use of immune suppressing medications Active malignancy", "candidate_expression": "((< 2.0) AND (<18 years) AND (Active) AND (HIV) AND (HIV infection Chronic) AND (HOMA IR) AND (decompensated) AND (immune suppressing medications) AND (infection Chronic HBV) AND (liver disease) AND (malignancy) AND (old) AND (seropositivity))"}
{"candidate_id": "LLM07584", "doc_id": "NCT02827487_inc", "case_bucket": "or", "source_criterion": "Women with expected difficult IUD insertion like nulliparous women and women with previous cesarean section.", "candidate_expression": "((IUD insertion expected difficult) AND (Women) AND (cesarean section previous) AND (nulliparous) AND (women))"}
{"candidate_id": "LLM07585", "doc_id": "NCT02277041_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((cesarean section) AND (gestation after 37 weeks) AND (singleton pregnancy))"}
{"candidate_id": "LLM07586", "doc_id": "NCT02827487_inc", "case_bucket": "or", "source_criterion": "Women with expected difficult IUD insertion like nulliparous women and women with previous cesarean section.", "candidate_expression": "((IUD insertion expected difficult) AND (Women) AND (cesarean section previous) AND (nulliparous) AND (women))"}
{"candidate_id": "LLM07587", "doc_id": "NCT02687178_inc", "case_bucket": "or", "source_criterion": "Caucasian patients affected by uncomplicated, essential hypertension, not well controlled by concomitant administration of ACE-I or ARBs and diuretics at the maximum dosage.", "candidate_expression": "((Caucasian) AND (diuretics maximum dosage) AND (essential hypertension uncomplicated not well controlled) AND ((ACE-I maximum dosage) OR (ARBs maximum dosage)))"}
{"candidate_id": "LLM07588", "doc_id": "NCT02804126_inc", "case_bucket": "other", "source_criterion": "obtained consent singleton pregnancy subarachnoid anaesthesia", "candidate_expression": "((pregnancy singleton) AND (subarachnoid anaesthesia))"}
{"candidate_id": "LLM07589", "doc_id": "NCT01665417_exc", "case_bucket": "or", "source_criterion": "Prior chemotherapy Prior treatment with gefitinib, erlotinib, or other drugs that target EGFR Patients must not be receiving any other investigational agents Any evidence of interstitial lung disease", "candidate_expression": "((Patients must not be receiving any other investigational agents) AND (chemotherapy Prior) AND (drugs that target EGFR) AND (erlotinib) AND (gefitinib) AND (interstitial lung disease) AND (treatment Prior))"}
{"candidate_id": "LLM07590", "doc_id": "NCT03506009_exc", "case_bucket": "or", "source_criterion": "mRS=2; History of stroke within 3 months; History of intracranial hemorrhage; Suspected subarachnoid hemorrhage; Intracranial tumour, vascular malformation or arterial aneurysm; Major surgery within 1 month; Systolic pressure =180 mmHg or diastolic pressure =110 mmHg; Platelet count < 105/mm3; Heparin therapy or oral anticoagulation therapy within 48 hours; Abnormal APTT; Thrombin or Xa factor inhibitor; Severe disease with a life expectancy of less than 3 months; Blood glucose < 50 mg/dL (2.7mmol/L); Patients who have received any other investigational drug or device within 3 months; Pregnancy; Researchers consider patients inappropriate to participate in the registry.", "candidate_expression": "((APTT Abnormal) AND (Blood glucose < 50 mg/dL 2.7mmol/L) AND (Heparin) AND (Intracranial tumour) AND (Major surgery within 1 month) AND (Patients who have received any other investigational drug or device within 3 months;) AND (Platelet count < 105/mm3) AND (Pregnancy) AND (Systolic pressure =180 mmHg) AND (Thrombin) AND (Xa factor inhibitor) AND (arterial aneurysm) AND (diastolic pressure =110 mmHg) AND (disease Severe life expectancy) AND (intracranial hemorrhage) AND (mRS =2) AND (oral anticoagulation therapy) AND (stroke within 3 months) AND (subarachnoid hemorrhage) AND (therapy) AND (vascular malformation))"}
{"candidate_id": "LLM07591", "doc_id": "NCT01942915_inc", "case_bucket": "other", "source_criterion": "Patients with hepatocirrhosis: according to the standard of child- pugh, liver functions to achieve class A or B patients, Including C class patients but can achieve B class after treatment", "candidate_expression": "(hepatocirrhosis)"}
{"candidate_id": "LLM07592", "doc_id": "NCT02112734_exc", "case_bucket": "or", "source_criterion": "Infants who have already received postnatal vitamin D supplementation prematurity (<37 weeks)/low birthweight <2500 g poor health due to a current or past significant disease state or congenital abnormality.", "candidate_expression": "((Infants) AND (birthweight <2500 g) AND (poor health) AND (postnatal vitamin D supplementation) AND (vitamin D) AND ((congenital abnormality) OR (significant disease state)) AND ((low birthweight) OR (prematurity)) AND ((current) OR (past)))"}
{"candidate_id": "LLM07593", "doc_id": "NCT03212352_exc", "case_bucket": "or", "source_criterion": "Patient does not meet inclusion criteria, discovered after randomization Inability to give informed consent Known clotting disorder or use of anticoagulants Known risk factors for, or presence of, a cardiovascular disease Language barrier", "candidate_expression": "((Inability to give informed consent) AND (Patient does not meet inclusion criteria, discovered after randomization) AND (anticoagulants) AND (cardiovascular disease) AND (clotting disorder) AND (risk factors cardiovascular disease))"}
{"candidate_id": "LLM07594", "doc_id": "NCT02874092_exc", "case_bucket": "or", "source_criterion": "History of sensitivity to study medications or any of their excipients RA cohort: Previous intolerance to MTX Current treatment with antiplatelet therapy Absolute indication for anti-platelet therapy Need for chronic oral anticoagulant therapy Severe hepatic impairment (eg, ascites and/or clinical signs of coagulopathy) Renal failure (eGFR <30 or requiring dialysis) A known bleeding diathesis, hemostatic or coagulation disorder, or prior major bleeding Prior stroke Active pathological bleeding History of intracranial haemorrhage Life expectancy <12 months based on investigator's judgement Patients considered to be at risk of bradycardic events (e.g., known sick sinus syndrome or second or third degree atrioventricular [AV)] block) unless already treated with a permanent pacemaker Anemia (hematocrit < 27%) Platelet count < 100,000/ml Concomitant use of strong CYP 3A inhibitors or inducers History of thrombocytopenia or neutropenia Pregnant or nursing women, or females with a positive pregnancy test at screening Females of child bearing potential not using acceptable method of birth control prior to or during study Concern for inability of the patient to comply with study procedures and/or follow up (eg, alcohol or drug abuse)", "candidate_expression": "((Anemia) AND (Females) AND (Life expectancy <12 months) AND (MTX) AND (Platelet count < 100,000/ml) AND (RA) AND (Renal failure) AND (Severe hepatic impairment) AND (anti-platelet therapy Absolute indication for Need for) AND (antiplatelet therapy Current) AND (bradycardic events at risk of) AND (child bearing potential) AND (chronic oral anticoagulant therapy) AND (females) AND (hematocrit < 27%) AND (intolerance) AND (intracranial haemorrhage History) AND (pathological bleeding Active) AND (pregnancy test positive at screening) AND (sensitivity) AND (stroke Prior) AND (study medications) AND (women) AND NOT (permanent pacemaker) AND NOT (method of birth control acceptable) AND ((ascites) OR (coagulopathy clinical signs of)) AND ((dialysis requiring) OR (eGFR <30)) AND ((bleeding diathesis) OR (coagulation disorder) OR (hemostatic disorder) OR (major bleeding prior)) AND ((second degree atrioventricular [AV)] block) OR (sick sinus syndrome) OR (third degree atrioventricular [AV)] block)) AND ((strong CYP 3A inducers) OR (strong CYP 3A inhibitors)) AND ((neutropenia) OR (thrombocytopenia)) AND ((Pregnant) OR (nursing)) AND ((during study) OR (prior to study)) AND ((inability to comply with follow up) OR (inability to comply with study procedures)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM07595", "doc_id": "NCT02951832_inc", "case_bucket": "or", "source_criterion": "Women aged 20-49; Having a regular menstrual cycle of which the menstrual period is between day 3-7, and the period between day 25-35; Excluding internal and surgical disease (after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine).", "candidate_expression": "((Women) AND (aged 20-49) AND (internal disease) AND (menstrual period between day 3-7 between day 25-35) AND (regular menstrual cycle) AND (surgical disease))"}
{"candidate_id": "LLM07596", "doc_id": "NCT02579200_inc", "case_bucket": "or", "source_criterion": "Previous diagnoses of COPD and HF under optimized clinical treatment as judged by the accompanying physician Reduced left ventricular ejection fraction (<50%) Non-reversible airway obstruction (post-bronchodilator FEV1/FVC < 0.7 and FEV1 < 80 %) Respiratory muscle weakness (Pi,max < 70cmH2O) Persistent dyspnea on daily life (Baseline Dyspnea Index focal score <or= 8).", "candidate_expression": "((< 0.7) AND (< 70cmH2O) AND (< 80 %) AND (<50%) AND (<or= 8) AND (Baseline) AND (COPD) AND (Dyspnea Index focal score) AND (FEV1) AND (FEV1/FVC) AND (HF) AND (Non-reversible) AND (Persistent) AND (Pi,max) AND (Reduced) AND (Respiratory muscle weakness) AND (airway obstruction) AND (clinical treatment) AND (dyspnea on daily life) AND (left ventricular ejection fraction) AND (optimized) AND (post-bronchodilator))"}
{"candidate_id": "LLM07597", "doc_id": "NCT03104816_exc", "case_bucket": "or", "source_criterion": "Patients requiring surgery for neoplastic processes Allergy to acetaminophen Liver dysfunction and elevated Liver Function Tests (LFTs) Alcohol or drug dependency Mental retardation Less than 50 kg of weight regnant women Patients requiring long-acting opioid pain management (including fentanyl patch, oxycontin, etc) for over 3 weeks immediately prior to surgery", "candidate_expression": "((Allergy) AND (LFTs) AND (Less than 50 kg) AND (Liver Function Tests) AND (Liver dysfunction) AND (Mental retardation) AND (acetaminophen) AND (elevated) AND (for over 3 weeks) AND (immediately prior to surgery) AND (long-acting opioid) AND (neoplastic processes) AND (regnant) AND (requiring) AND (surgery) AND (weight) AND (women) AND ((Alcohol dependency) OR (drug dependency)) AND ((fentanyl patch) OR (oxycontin)))"}
{"candidate_id": "LLM07598", "doc_id": "NCT02650388_inc", "case_bucket": "or", "source_criterion": "Age = 75 years, Severe, symptomatic aortic stenosis, High risk for cardiac surgery (STS and logistic Euroscore ), According multidisciplinary (heart) team decision TAVI is preferable, Willing to participate", "candidate_expression": "((Age = 75 years) AND (Willing to participate) AND (aortic stenosis Severe symptomatic) AND (cardiac surgery High risk) AND ((STS) OR (logistic Euroscore)))"}
{"candidate_id": "LLM07599", "doc_id": "NCT03481894_inc", "case_bucket": "or", "source_criterion": "Male or female patients 2 to 16 years of age Patients who require at least 80% of their caloric intake as PN at study start, and in whom an indication for PN is expected for at least 5 days Patients who require a central venous line to receive PN or already have a central venous line in place for other reasons Written informed consent from legal representative(s)", "candidate_expression": "((2 to 16 years) AND (Male) AND (PN) AND (Written informed consent from legal representative(s)) AND (age) AND (at least 80% of caloric intake) AND (at study start) AND (central venous line) AND (expected) AND (female) AND (for at least 5 days) AND (indication) AND (other reasons))"}
{"candidate_id": "LLM07600", "doc_id": "NCT02979561_exc", "case_bucket": "or", "source_criterion": "Signs of hemodynamic instability (i.e. systolic blood pressure <100 mm Hg.St. or episode of systolic blood pressure fall for =40 mm Hg. / or heart rate > 110 lasting more than 15 min) or need for ventilatory support within 12 hours prior to randomisation. The indication for oral anticoagulation, associated with others disease. malignant neoplasm of any location Contraindications to warfarin or pradaxa according to Russian Instructions for medical use of these drugs Indications for concomitant treatment with antiplatelet agents Any stroke within 6 months before randomization Intracranial hemorrhage in anamnesis Active bleeding, bleeding diathesis. Clinically significant bleeding within the last 30 days. Trauma or extensive surgery within 1 month before randomization or surgery planned in the next 6 months after randomization. Intracranial pathology: tumor, arteriovenous fistula or aneurysm. Gastrointestinal bleeding in the previous 3 months. Gastric ulcer or duodenal ulcer with clinical manifestations or endoscopically identified acute ulcer without signs of scarring during previous 30 days. Uncontrolled hypertension (systolic blood pressure> 180 mm Hg. and / or diastolic blood pressure> 100 mm.hg in patients receiving antihypertensive drugs). Pregnancy, lactation. Life expectancy <6 months. Clinically significant liver disease. Creatinine clearance (estimated by Cockcroft-Gault) <30 ml / min. hemoglobin level <90 g/l), thrombocytopenia <100x10^9 / L. Patients who, in the opinion of the researcher, are not suitable for inclusion in the study, for example, due to the low likelihood of doctor's recommendations following. Long-term use of NSAIDs Current participation in another clinical study. Allergic to contrast substance or radioisotope drugs used in procedures to assess endpoints of the study, which according to researchers, may be a contraindication to the implementation of these research methods.", "candidate_expression": "((<100 mm Hg.St.) AND (<100x10^9 / L) AND (<30 ml / min) AND (<6 months) AND (<90 g/l) AND (=40 mm Hg) AND (> 100 mm.hg) AND (> 110) AND (> 180 mm Hg) AND (Active) AND (Allergic) AND (Clinically significant) AND (Cockcroft-Gault) AND (Contraindications) AND (Creatinine clearance) AND (Gastric ulcer) AND (Gastrointestinal bleeding) AND (Indications) AND (Intracranial hemorrhage) AND (Intracranial pathology) AND (Life expectancy) AND (Long-term use) AND (NSAIDs) AND (Pregnancy) AND (Russian Instructions for medical use) AND (Trauma) AND (Uncontrolled) AND (acute ulcer) AND (anamnesis) AND (aneurysm) AND (antihypertensive drugs) AND (antiplatelet agents) AND (arteriovenous fistula) AND (bleeding) AND (bleeding diathesis) AND (clinical manifestations) AND (concomitant) AND (contrast substance) AND (diastolic blood pressure) AND (duodenal ulcer) AND (during previous 30 days) AND (endoscopically) AND (endoscopically identified) AND (extensive surgery) AND (heart rate) AND (hemodynamic instability) AND (hemoglobin level) AND (hypertension) AND (in the next 6 months after randomization) AND (in the previous 3 months) AND (indication for) AND (lactation) AND (lasting more than 15 min) AND (liver disease) AND (malignant) AND (need for) AND (neoplasm) AND (oral anticoagulation) AND (planned) AND (pradaxa) AND (radioisotope drugs) AND (signs of scarring) AND (stroke) AND (surgery) AND (systolic blood pressure) AND (systolic blood pressure fall) AND (thrombocytopenia) AND (tumor) AND (ventilatory support) AND (warfarin) AND (within 1 month before randomization) AND (within 12 hours prior to randomisation) AND (within 6 months before randomization) AND (within the last 30 days) AND (without))"}
```
