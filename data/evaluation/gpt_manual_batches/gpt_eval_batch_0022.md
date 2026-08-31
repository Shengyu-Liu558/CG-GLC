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
{"candidate_id": "LLM00526", "doc_id": "NCT03624881_inc", "case_bucket": "or", "source_criterion": "Symptomatic paroxysmal AF who had at least one AF episode electrocardiographically documented within one (1) year prior to enrollment. Documentation may include electrocardiogram (ECG); Transtelephonic monitoring (TTM), Holter monitor or telemetry strip Failed at least one antiarrhythmic drug (AAD) (Class I or III antiarrhythmic drugs) as evidenced by recurrent symptomatic AF, or intolerable to the AAD Age 18 years or older Signed Patient Informed Consent Form (ICF) Able and willing to comply with all pre-, post-, and follow-up testing and requirements", "candidate_expression": "((18 years or older) AND (AAD) AND (AF episode) AND (Age) AND (Signed Patient Informed Consent Form (ICF)) AND (Symptomatic) AND (antiarrhythmic drug (AAD)) AND (at least one) AND (electrocardiographically documented) AND (enrollment) AND (paroxysmal AF) AND (within one (1) year prior to enrollment) AND ((Holter monitor) OR (Transtelephonic monitoring (TTM)) OR (electrocardiogram (ECG)) OR (electrocardiographically) OR (telemetry strip)) AND ((Class I antiarrhythmic drugs) OR (III antiarrhythmic drugs)) AND ((intolerable) OR (recurrent symptomatic AF)))"}
{"candidate_id": "LLM00527", "doc_id": "NCT03209687_exc", "case_bucket": "or", "source_criterion": "Females who have high response (estradiol at time of ovulation trigger is > 5000 pg/ml or more than 15 oocytes are retrieved)", "candidate_expression": "((> 5000 pg/ml) AND (Females) AND (at time of ovulation trigger) AND (high response) AND (more than 15) AND (ovulation trigger) AND ((estradiol) OR (oocytes retrieved)))"}
{"candidate_id": "LLM00528", "doc_id": "NCT02601157_exc", "case_bucket": "or", "source_criterion": "1. High risk profiles for ischemic adverse events such as A. ST-segment elevation myocardial infarction (STEMI) B. Patients with cardiogenic shock or concomitant severe decompensated heart failure C. Myocardial infarction or stent thrombosis in spite of the maintenance of antiplatelet therapy D. Restenosis in stented segments or previous sites of balloon angioplasty 2. Patients who cannot follow allocated DAPT schedule due to the planned surgery or elective procedure within 3 months after the stenting 3. Recent history of major surgery or evident events of gastrointestinal bleeding within 1 month from the procedure 4. Patients on anticoagulation therapy with warfarin or other anticoagulants 5. Life expectancy less than 1 year (such as malignancies or other chronic systemic diseases) 6. Pregnant women 7. Past history of allergy or other contraindications for the following medications/materials: aspirin, clopidogrel, heparin, cobalt chromium, sirolimus", "candidate_expression": "((High risk profiles) AND (Life expectancy less than 1 year) AND (Pregnant) AND (allergy) AND (anticoagulation therapy) AND (antiplatelet therapy) AND (cannot follow allocated DAPT schedule) AND (contraindications other) AND (ischemic adverse events) AND (women) AND ((Myocardial infarction) OR (stent thrombosis)) AND ((Restenosis) OR (ST-segment elevation myocardial infarction (STEMI)) OR (cardiogenic shock) OR (heart failure severe decompensated)) AND ((procedure elective) OR (surgery)) AND ((events of gastrointestinal bleeding) OR (major surgery)) AND ((anticoagulants other) OR (warfarin)) AND ((chronic systemic diseases other) OR (malignancies)) AND ((aspirin) OR (clopidogrel) OR (cobalt chromium) OR (heparin) OR (sirolimus)))"}
{"candidate_id": "LLM00529", "doc_id": "NCT03004209_inc", "case_bucket": "or", "source_criterion": "Clinically diagnosed autoimmune encephalitis Ineffective 1st line treatment (e.g. steroid IV, IVIg) and 2nd line treatment (e.g. Rituximab or cyclophosphamide)", "candidate_expression": "((1st line treatment Ineffective) AND (2nd line treatment Ineffective) AND (autoimmune encephalitis Clinically diagnosed) AND ((IVIg) OR (steroid IV)) AND ((Rituximab) OR (cyclophosphamide)))"}
{"candidate_id": "LLM00530", "doc_id": "NCT01932996_inc", "case_bucket": "other", "source_criterion": "Currently Homeless Smoked at least 100 cigarettes in lifetime AUDIT score of > or equal to 5, < or equal to 26 Aged 18 years or older Willing to attend study sessions and follow other study protocol", "candidate_expression": "((18 years or older) AND (AUDIT) AND (Aged) AND (Homeless) AND (Smoked) AND (Willing to attend study sessions and follow other study protocol) AND (at least 100 cigarettes) AND (score of > or equal to 5, < or equal to 26))"}
{"candidate_id": "LLM00531", "doc_id": "NCT02954029_inc", "case_bucket": "or", "source_criterion": "age 18 years or older patients undergoing invasive procedures via the radial or femoral arteries", "candidate_expression": "((age 18 years or older) AND (invasive procedures undergoing) AND ((femoral arteries) OR (radial arteries)))"}
{"candidate_id": "LLM00532", "doc_id": "NCT02396732_exc", "case_bucket": "or", "source_criterion": "Presence of VTE upon admission Pregnant or nursing Inability to give informed consent by patient or healthcare proxy Contraindication to enoxaparin Contraindication to aspirin Epidural or subdural hematoma Presence, or removal within the last 12 hours, of an epidural or spinal catheter, or recent (within the last 12 hours) epidural or spinal anesthesia/procedures", "candidate_expression": "((Contraindication) AND (Epidural hematoma) AND (Inability to give informed consent) AND (Inability to give informed consent by patient or healthcare proxy) AND (Pregnant) AND (Presence of a spinal catheter within the last 12 hours) AND (Presence of an epidural) AND (VTE upon admission) AND (aspirin) AND (enoxaparin) AND (epidural anesthesia) AND (nursing) AND (removal of a spinal catheter) AND (removal of an epidural) AND (spinal anesthesia) AND (subdural hematoma))"}
{"candidate_id": "LLM00533", "doc_id": "NCT03350659_exc", "case_bucket": "or", "source_criterion": "Drug-induced hypotension, if necessary, evaluate patient after discontinuing the causative drug for one month Heart failure or Chronic renal failure Severe supine hypertension (Systolic Blood Pressure >180 or Diastolic Blood Pressure>110mmHg) Pregnant women, breast-feeding Unable to perform questionnaire", "candidate_expression": "((>110mmHg) AND (>180) AND (Chronic renal failure) AND (Diastolic Blood Pressure) AND (Drug-induced) AND (Heart failure) AND (Pregnant) AND (Severe) AND (Systolic Blood Pressure) AND (Unable to perform questionnaire) AND (breast-feeding) AND (hypotension) AND (supine hypertension) AND (women))"}
{"candidate_id": "LLM00534", "doc_id": "NCT01720394_inc", "case_bucket": "or", "source_criterion": "medical indication for induction of labor 18 years of age signed informed consent cephalic presentation no PROM 37+0 - 42+0 weeks of gestation Bishop-Score = 6 no contra-indication for medical induction of labor no clinical signs of infection", "candidate_expression": "((Bishop-Score = 6) AND (age 18 years) AND (cephalic presentation) AND (induction of labor) AND (medical indication) AND (medical induction of labor) AND (signed informed consent) AND (weeks of gestation) AND NOT (contra-indication) AND NOT (infection clinical signs of) AND NOT (PROM) AND ((37+0) OR (42+0)))"}
{"candidate_id": "LLM00535", "doc_id": "NCT03297125_exc", "case_bucket": "or", "source_criterion": "Optune compliance < 75%; they would be excluded from the final analyses. History of craniectomy or significant skull defect (contraindication to Optune). Active implantable medical device (i.e. DBS, spinal cord stimulator, pacemaker, defibrillator, vagus nerve stimulator, programmable shunt). Karnofsky Performance Status (KPS) < 60.", "candidate_expression": "((< 60) AND (< 75%) AND (Active) AND (DBS) AND (KPS) AND (Karnofsky Performance Status) AND (Optune) AND (Optune compliance) AND (contraindication) AND (craniectomy) AND (defibrillator) AND (implantable medical device) AND (pacemaker) AND (programmable shunt) AND (significant) AND (skull defect) AND (spinal cord stimulator) AND (vagus nerve stimulator))"}
{"candidate_id": "LLM00536", "doc_id": "NCT02908919_exc", "case_bucket": "or", "source_criterion": "ileus known or suspected bowel obstruction active bowel inflammation pregnancy any presence of serious medical conditions ( esp. cardiac, renal, liver diseases) history of prior colonic or rectal surgery inability to obtain valid data from", "candidate_expression": "((active) AND (bowel inflammation) AND (bowel obstruction) AND (cardiac diseases) AND (colonic surgery) AND (history of) AND (ileus) AND (known) AND (liver diseases) AND (pregnancy) AND (prior) AND (rectal surgery) AND (renal diseases) AND (serious medical conditions) AND (suspected))"}
{"candidate_id": "LLM00537", "doc_id": "NCT01942109_inc", "case_bucket": "other", "source_criterion": "heart failure NYHA II-IV previous treatment with diuretics age>18 years", "candidate_expression": "((NYHA II-IV) AND (age >18 years) AND (diuretics) AND (heart failure) AND (treatment previous))"}
{"candidate_id": "LLM00538", "doc_id": "NCT03033745_inc", "case_bucket": "or", "source_criterion": "Male or female on stable dose of IgPro20 (Hizentra) therapy. Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening. Subjects with PID, eg, with a diagnosis of common variable immunodeficiency or X-linked agammaglobulinemia, as defined by the Pan American Group for Immune Deficiency and the European Society of Immune Deficiencies. With infusion parameters as specified below: Experience with pump-assisted infusions of IgPro20 at the tolerated flow rate of 25 mL/h per injection site for at least 1 month prior to Day 1. Total weekly IgPro20 dose of = 50 mL (= 10 g). Experience with pump-assisted infusions of IgPro20 at tolerated volumes of 25 mL/injection site for at least 1 month prior to Day 1. Experience with frequent (2-7 times per week) infusions of IgPro20 at the tolerated flow rate of approximately 0.5 mL/min (equivalent of 25-30 mL/h) per injection site for at least 1 month prior to Day 1. The dose (volume) per injection site should not exceed 25 mL.", "candidate_expression": "((European Society of Immune Deficiencies) AND (Hizentra) AND (IgPro20 frequent 2-7 times per week per injection site flow rate of approximately 0.5 mL/min for at least 1 month prior to Day 1 exceed 25 mL. 25-30 mL/h) AND (IgPro20 pump-assisted infusions flow rate of 25 mL/h per injection site for at least 1 month prior to Day 1) AND (IgPro20 pump-assisted infusions volumes of 25 mL/injection site for at least 1 month prior to Day 1) AND (IgPro20 stable dose) AND (IgPro20 weekly = 50 mL = 10 g) AND (Male) AND (PID) AND (Pan American Group for Immune Deficiency) AND (Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening) AND (X-linked agammaglobulinemia) AND (common variable immunodeficiency) AND (female))"}
{"candidate_id": "LLM00539", "doc_id": "NCT01929434_exc", "case_bucket": "or", "source_criterion": "Intracranial infection. Severe respiratory and circulatory system diseases. Hematologic malignancies. Positive serological tests such as AIDS, hepatitis B virus, hepatitis C virus and syphilis （antigen or antibody）. Tumors. Genetic and metabolic diseases.", "candidate_expression": "((AIDS) AND (Genetic diseases) AND (Hematologic malignancies) AND (Intracranial infection) AND (Severe) AND (Tumors) AND (circulatory system disease) AND (hepatitis B virus) AND (hepatitis C virus) AND (metabolic diseases) AND (respiratory system disease) AND (syphilis))"}
{"candidate_id": "LLM00540", "doc_id": "NCT03431831_inc", "case_bucket": "or", "source_criterion": "Overweight/Obese Adult patients (age 19 years -65) eligible based on WALI screening tool", "candidate_expression": "((19 years -65) AND (Adult) AND (WALI screening tool) AND (age) AND (eligible) AND ((Obese) OR (Overweight)))"}
{"candidate_id": "LLM00541", "doc_id": "NCT02053246_inc", "case_bucket": "other", "source_criterion": "Adults (= 18 years of age) with World Health Organization Group 2 Pulmonary Hypertension (Mean pulmonary artery pressure = 25 mmHg and pulmonary capillary wedge pressure = 15 mmHg) New York Heart Association class II-IV symptoms Left ventricular ejection fraction (LVEF) = 45%", "candidate_expression": "(((Mean pulmonary artery pressure) AND (= 15 mmHg) AND (= 18 years) AND (= 25 mmHg) AND (= 45%) AND (Adults) AND (Left ventricular ejection fraction (LVEF)) AND (New York Heart Association) AND (Pulmonary Hypertension) AND (World Health Organization Group 2) AND (age) AND (class II-IV) AND (pulmonary capillary wedge pressure) AND (symptoms))"}
{"candidate_id": "LLM00542", "doc_id": "NCT02527512_exc", "case_bucket": "or", "source_criterion": "Documented renal failure documented allergy to iodine or shellfish previous spine fusion surgery undergoing elective posterior spine single-level instrumentation surgery undergoing anterior spine multi-level instrumentation surgery current antibiotic use.", "candidate_expression": "((allergy) AND (antibiotic use current) AND (iodine) AND (multi-level instrumentation surgery undergoing anterior spine) AND (renal failure) AND (shellfish) AND (single-level instrumentation surgery undergoing elective posterior spine) AND (spine fusion surgery previous))"}
{"candidate_id": "LLM00543", "doc_id": "NCT02269137_exc", "case_bucket": "or", "source_criterion": "hypoglycemia SE;psychogenic SE;any other pseudo-SE", "candidate_expression": "((hypoglycemia SE) AND (pseudo-SE) AND (psychogenic SE))"}
{"candidate_id": "LLM00544", "doc_id": "NCT01116882_inc", "case_bucket": "or", "source_criterion": "1. Subject is at least 18 years old. 2. Subject requires single- or multi-vessel percutaneous coronary intervention (PCI) of de novo or restenotic target lesion (including in-stent restenotic lesions). 3. Subject's lesion(s) is (are) amenable to stent treatment with currently available FDA-approved bare metal or drug eluting stents. 4. Subject is an acceptable candidate for elective, urgent or emergency coronary artery bypass graft (CABG). 5. Subject has clinical evidence of ischemic heart disease in terms of a positive functional study, or documented symptoms. 6. Documented stable angina pectoris [Canadian Cardiovascular Society Classification (CCS) 1, 2, 3, or 4], unstable angina pectoris with documented ischemia (Braunwald Class IB-C, IIB-C, or IIIB-C), non-ST segment elevation myocardial infarction, or documented silent ischemia. 7. Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm. 8. Subject and the treating physician agree that the subject will comply with all follow-up evaluations. 9. Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site. 10. The target lesion(s) is (are) de novo or restenotic (including in-stent restenotic) native coronary artery lesion(s) with greater than 50 and less than 100% stenosis (visual estimate), or the target lesion is an acute (less than 1 month) total occlusion as evidenced by clinical symptoms. 11. Target lesions(s) is (are) located in an infarct (if not treated with primary PCI) or non-infarct-related artery with a 70% or greater stenosis (by visual estimate) more than 72 hours following the ST segment elevation myocardial infarction (STEMI). Lesions treated with PCI more than 72 hours following STEMI would be subject to the same protocol inclusion/exclusion criteria listed above and below with the exception that a target lesion of 70% or greater stenosis may be treated with or without symptoms or abnormal stress test).", "candidate_expression": "((1, 2, 3, or 4) AND (70% or greater) AND (Braunwald Class) AND (Canadian Cardiovascular Society Classification (CCS)) AND (IB-C, IIB-C, or IIIB-C) AND (SOS hospital) AND (ST segment elevation myocardial infarction (STEMI)) AND (Subject and the treating physician agree that the subject will comply with all follow-up evaluations.) AND (Subject has been informed of the nature of the study and agrees to its provisions and has provided written informed consent as approved by the Institutional Review Board/Ethics Committee of the respective clinical site.) AND (Subject is willing and able to undergo percutaneous intervention at SOS hospital, if randomized to SOS study arm.) AND (Target lesions) AND (able) AND (acute) AND (amenable to stent treatment) AND (at least 18 years) AND (bare metal stents) AND (clinical evidence) AND (clinical symptoms) AND (coronary artery bypass graft (CABG)) AND (coronary artery lesion) AND (de novo) AND (documented) AND (drug eluting stents) AND (elective) AND (emergency) AND (functional study) AND (greater than 50 and less than 100%) AND (in an infarct -related artery) AND (in-stent) AND (in-stent restenotic) AND (in-stent restenotic lesions) AND (infarct) AND (ischemia) AND (ischemic heart disease) AND (less than 1 month) AND (more than 72 hours following the ST segment elevation myocardial infarction (STEMI)) AND (multi-vessel) AND (non-ST segment elevation myocardial infarction) AND (non-infarct-related artery) AND (not) AND (old) AND (percutaneous coronary intervention (PCI)) AND (percutaneous intervention) AND (positive) AND (primary PCI) AND (restenotic) AND (silent) AND (silent ischemia) AND (single- vessel) AND (stable) AND (stable angina pectoris) AND (stenosis) AND (target lesion) AND (the ST segment elevation myocardial infarction (STEMI)) AND (total occlusion) AND (unstable) AND (unstable angina pectoris) AND (urgent) AND (willing))"}
{"candidate_id": "LLM00545", "doc_id": "NCT02607748_inc", "case_bucket": "or", "source_criterion": "Acute Coronary Syndrome group: 40 patients with type 1 myocardial infarction within 21 days prior to the imaging visit and invasive coronary angiography with angiographic evidence of at least a 50% stenosis in one or more coronary arteries. Only patients undergoing PCI will be included in the study. Stable Ischemic Heart Disease group: 40 patients who have undergone invasive coronary angiography within 21 days prior to the imaging visit, with history of typical angina prior to the angiogram, but no prior myocardial infarction or coronary revascularization. have no prior CAD associated event (no prior myocardial infarction, acute coronary syndrome, coronary angiogram, or PCI), have CAC between 10 to <1000, and match to patients in the ACS group by gender, age by decile, and CAC category (using CAC categories of 10 to <100, 100 to <400, 400 to <1000).", "candidate_expression": "((Acute Coronary Syndrome) AND (CAC) AND (CAD) AND (between 10 to <1000) AND (no) AND ((PCI) OR (acute coronary syndrome) OR (coronary angiogram) OR (myocardial infarction)))"}
{"candidate_id": "LLM00546", "doc_id": "NCT01803438_exc", "case_bucket": "or", "source_criterion": "Subject has documented typical atrial flutter. Subject has any history of successful or unsuccessful treatment of AF with class I or III antiarrhythmic or sotalol with the intention to prevent an AF recurrence. Patients pretreated with above AAD at maximum 48 hours with the intention to convert an AF episode are allowed. Subject had any previous left atrial ablation. Subject had any previous cardiac surgery, e.g. prosthetic valves. Subject has permanent pacemaker or defibrillator implant. Subject has 2° type II, 3° degree AV-block or left/right bundle branch block pattern. Subject has unstable angina pectoris. Subject has history of previous myocardial infarction or percutaneous intervention during the last three months. Subject has symptomatic carotid stenosis. Subject has chronic obstructive pulmonary disease with detected pulmonary hypertension or any other evidence of significant lung disease. Subject has any contraindication for oral anticoagulation. Subject has any history of previous transient ischemic attack or stroke. Subject has known intra-cardiac thrombus formation. Subject has any significant congenital heart defect corrected or not (except for patent foramen ovale that is allowed). Subject has evidence of congestive heart failure (NYHA class II, III or IV) in sinus rhythm. Subject has hypertrophic cardiomyopathy. Subject has abnormal long or short QT interval, signs of Brugada syndrome, known inheriting ion channel disease on the family, arrhythmogenic right ventricular dysplasia. Subject has sarcoidosis. Subject has pulmonary vein stent. Subject has myxoma. Exclusion criteria based on laboratory abnormalities Subject has thrombocytosis (platelet count > 600,000 / µl) or thrombocytopenia (platelet count <100,000 / µl). Subject has any untreated or uncontrolled hyperthyroidism or hypothyroidism. Subject has renal dysfunction with glomerular filtration rate < 60 ml / min. Subject has known cryoglobulinaemia. General exclusion criteria Subject has a reversible causes for AF like hyperthyroidism and alcoholism. Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled. Subject is a breastfeeding woman. Subject has an active systemic infection. Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators. Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state. Legal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up. Subject has a life expectancy of = 1 year. Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager.", "candidate_expression": "((2° type II AV-block) AND (3° degree AV-block) AND (< 60 ml / min) AND (<100,000 / µl) AND (= 1 year) AND (> 600,000 / µl) AND (AF) AND (Brugada syndrome) AND (II) AND (III) AND (IV) AND (NYHA class) AND (QT interval) AND (Subject is a breastfeeding woman) AND (Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled) AND (Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager) AND (Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators) AND (Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state) AND (abnormal) AND (active) AND (alcoholism) AND (antiarrhythmic) AND (arrhythmogenic) AND (atrial ablation) AND (atrial flutter) AND (cardiac surgery) AND (carotid stenosis) AND (chronic obstructive pulmonary disease) AND (class I) AND (class III) AND (congenital heart defect) AND (congestive heart failure) AND (contraindication) AND (cryoglobulinaemia) AND (defibrillator implant) AND (egal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up) AND (except) AND (glomerular filtration rate) AND (hyperthyroidism) AND (hypertrophic cardiomyopathy) AND (hypothyroidism) AND (inheriting ion channel disease) AND (inheriting ion channel disease on the family) AND (intra-cardiac thrombus) AND (last three months) AND (left) AND (left bundle branch block) AND (life expectancy) AND (long) AND (lung disease) AND (myocardial infarction) AND (myxoma) AND (oral anticoagulation) AND (patent foramen ovale) AND (percutaneous intervention) AND (permanent pacemaker) AND (platelet count) AND (prosthetic valves) AND (pulmonary hypertension) AND (pulmonary vein stent) AND (renal dysfunction) AND (right bundle branch block) AND (right ventricular dysplasia) AND (sarcoidosis) AND (short) AND (significant) AND (sinus rhythm) AND (sotalol) AND (stroke) AND (symptomatic) AND (systemic infection) AND (thrombocytopenia) AND (thrombocytosis) AND (transient ischemic attack) AND (uncontrolled) AND (unstable angina pectoris) AND (untreated))"}
{"candidate_id": "LLM00547", "doc_id": "NCT03004209_exc", "case_bucket": "or", "source_criterion": "Hemoglobin > 12g/dL Hematochrit >36% Thrombocytosis > 750K AST or ALT > 120 HIV (+) Allergic reaction upon erythropoietin Uncontrolled hypertension mRS before the autoimmune encephalitis > 3 Breast feeding or pregnancy History of ischemic stroke or pulmonary thrombosis Refuse to be enrolled", "candidate_expression": "((Allergic) AND (HIV (+)) AND (Hematochrit >36%) AND (Hemoglobin > 12g/dL) AND (Refuse to be enrolled) AND (Thrombocytosis > 750K) AND (Uncontrolled hypertension) AND (autoimmune encephalitis) AND (erythropoietin) AND (mRS before the autoimmune encephalitis > 3) AND ((Breast feeding) OR (pregnancy)) AND ((ischemic stroke) OR (pulmonary thrombosis)) AND ((ALT) OR (AST)))"}
{"candidate_id": "LLM00548", "doc_id": "NCT03461679_inc", "case_bucket": "other", "source_criterion": "Patients undergoing total knee arthroplasty under spinal anaesthesia 45y or older ASA 1-3 BMI 18-35", "candidate_expression": "((1-3) AND (18-35) AND (45 or older) AND (ASA) AND (BMI) AND (spinal anaesthesia) AND (total knee arthroplasty) AND (y))"}
{"candidate_id": "LLM00549", "doc_id": "NCT01857167_exc", "case_bucket": "or", "source_criterion": "1. Deny to sign the informed consent; 2. type 1 diabetes; 3. Family history of hypertriglyceridemia or fasting triglyceride>4.56 mmol/L; 4. Have severe liver disease, kidney disease or cancer; 5. Participating in the other clinical trial within 30 days; 6. Other diseases or conditions, for which the doctor of the patients do not agree his or her participating.", "candidate_expression": "((>4.56 mmol/L) AND (Deny to sign the informed consent;) AND (Family history) AND (for which the doctor of the patients do not agree his or her participating) AND (for which the doctor of the patients do not agree his or her participating.) AND (severe) AND (type 1 diabetes) AND ((cancer) OR (kidney disease) OR (liver disease)) AND ((Other conditions) OR (Other diseases)) AND ((fasting triglyceride) OR (hypertriglyceridemia)))"}
{"candidate_id": "LLM00550", "doc_id": "NCT02894645_exc", "case_bucket": "or", "source_criterion": "Age less than one year or age greater than/equals to 18 years Previous treatment with cytotoxic agents or high-dose steroids Mixed phenotype acute leukemia (MPAL) ALL as secondary malignancy Abnormal renal or liver function Doubtful compliance or unable to afford full course of therapy", "candidate_expression": "((ALL) AND (Abnormal liver function) AND (Abnormal renal function) AND (Age less than one year) AND (Doubtful compliance) AND (MPAL) AND (Mixed phenotype acute leukemia) AND (age greater than/equals to 18 years) AND (cytotoxic agents) AND (high-dose steroids) AND (malignancy secondary) AND (treatment Previous) AND (unable to afford full course of therapy))"}
```
