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
{"candidate_id": "LLM03226", "doc_id": "NCT01757717_inc", "case_bucket": "other", "source_criterion": "Patients must have histologic proof of a malignancy suitable for radiation therapy. Patients must have received prior external beam radiation therapy to the region proposed for HDR brachytherapy treatment; evaluation of doses previously delivered to spinal cord/cauda equine, pelvis, and other critical structures (bowel, kidneys, rectum) will be taken into consideration. If repeat irradiation would exceed any normal tissue constraint set by MSKCC Radiation Oncology Department dose constraint criteria, the patient will potentially be eligible. If the total prior radiation dose to the cord or pelvis exceeds 100 Gy BED equivalent, the patient will be potentially eligible, where a total of 100 BED Gy equivalent is determined by the biological equivalent dose (BED) calculation; BED = nd(1 + d/α/β), where n = number of fractions and d = dose per fraction; α/β is the constant for spinal cord late effect and equals 2. [Rades 2005, Nieder 2005, Sahgal 2012] KPS ≥ 60 Age ≥ 18 years old", "candidate_expression": "((Age ≥ 18 years old) AND (HDR brachytherapy) AND (KPS ≥ 60) AND (MSKCC Radiation Oncology Department dose constraint criteria exceed any normal tissue constraint) AND (external beam radiation therapy prior to the region proposed for HDR brachytherapy treatment) AND (histologic proof) AND (malignancy suitable for radiation therapy) AND (radiation therapy) AND (repeat irradiation) AND (suitable for radiation therapy))"}
{"candidate_id": "LLM03227", "doc_id": "NCT02876484_inc", "case_bucket": "or", "source_criterion": "Uncomplicated RYGB performed minimum 3 months prior to the study. Fasting plasma glucose < 7,0 mM, HbA1c < 48 mmol/mol 3 months after RYGB", "candidate_expression": "((Fasting plasma glucose < 7,0 mM) AND (HbA1c < 48 mmol/mol 3 months after RYGB) AND (RYGB) AND (RYGB Uncomplicated minimum 3 months prior to the study))"}
{"candidate_id": "LLM03228", "doc_id": "NCT02589353_exc", "case_bucket": "or", "source_criterion": "adults 61 years old and above smokers pregnant women taking any prescription pain/ insulin medication has a history of taste or smell loss or other oral disorders (e.g., burning mouth syndrome) has current oral lesions, canker sores, or piercings has a history of food allergy", "candidate_expression": "((adults) AND (burning mouth syndrome) AND (food allergy history) AND (old and above 61 years) AND (oral disorders other) AND (pregnant) AND (smokers) AND (women) AND ((smell loss) OR (taste loss)) AND ((canker sores) OR (oral lesions) OR (piercings)) AND ((prescription insulin medication) OR (prescription pain medication)))"}
{"candidate_id": "LLM03229", "doc_id": "NCT01978028_inc", "case_bucket": "or", "source_criterion": "Patients with chronic heart failure of New York Heart Association Class II or III, a left ventricular ejection fraction of = 40% for patients in NYHA class II or = 45% for patients in NYHA class III, a hemoglobin level at the screening visit between 9.5-13.5 g/dl, and iron deficiency, which is defined as serum ferritin level < 100µg/l or between 100 and 299 µg/l, when transferring saturation is < 20%. Age =18 years Obtained informed consent Stable pharmacological therapy during the last 4 weeks (with the exception of diuretics)", "candidate_expression": "((< 20%) AND (= 40%) AND (= 45%) AND (=18 years) AND (Age) AND (Class II or III) AND (NYHA) AND (New York Heart Association) AND (Obtained informed consent) AND (Stable) AND (at the screening visit) AND (between 9.5-13.5 g/dl) AND (chronic heart failure) AND (class II) AND (class III) AND (diuretics) AND (during the last 4 weeks) AND (hemoglobin level) AND (iron deficiency) AND (last 4 weeks) AND (left ventricular ejection fraction) AND (pharmacological therapy) AND (serum ferritin level) AND (the screening visit) AND (transferring saturation) AND (with the exception of) AND ((< 100µg/l) OR (between 100 and 299 µg/l)))"}
{"candidate_id": "LLM03230", "doc_id": "NCT03352869_exc", "case_bucket": "or", "source_criterion": "Except for serious complications (cardiovascular events and recent significant liver, kidney or lung disease within 3 months) high blood pressure (>160/100mmHg) active infection secondary diabetes pregnancy alcohol abuse allergic to GLP-1 receptor agonist", "candidate_expression": "((GLP-1 receptor agonist) AND (active infection) AND (alcohol abuse) AND (allergic) AND (blood pressure >160/100mmHg) AND (cardiovascular events) AND (diabetes secondary) AND (high blood pressure) AND (pregnancy) AND (serious complications) AND ((disease kidney) OR (disease liver) OR (lung disease)))"}
{"candidate_id": "LLM03231", "doc_id": "NCT02340169_exc", "case_bucket": "or", "source_criterion": "Has other dermatological conditions that may interfere with clinical assessments Allergy or sensitivity to corticosteroids or any drug hypersensitivity or intolerance that would compromise patient safety or study results History of an adverse reaction to Cortrosyn™ or similar test reagents Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation", "candidate_expression": "((Allergy) AND (Chronic infectious disease, system or organ disorder or other medical condition that would place patient at undue risk by study participation) AND (Cortrosyn) AND (Has other dermatological conditions that may interfere with clinical assessments) AND (adverse reaction) AND (corticosteroids) AND (hat would compromise patient safety or study results) AND (sensitivity) AND (test reagents similar) AND ((Cortrosyn) OR (similar test reagents)) AND ((drug hypersensitivity) OR (drug intolerance)))"}
{"candidate_id": "LLM03232", "doc_id": "NCT02555163_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed at the out-patient cystoscopy with papillary bladder tumour will be legible for inclusion", "candidate_expression": "((cystoscopy) AND (out-patient) AND (papillary bladder tumour))"}
{"candidate_id": "LLM03233", "doc_id": "NCT01214096_inc", "case_bucket": "or", "source_criterion": "1. Age: 18-75 years old, no limitation in gender; 2. Left ventricular ejection fraction (LVEF) ≤ 40% (ECHO); 3. Patients with chronic heart failure (NYHA class II or III); 4. In the past one month, the clinical condition (including history, clinical symptoms and signs) was relatively stable; 5. Patients on standard treatment of chronic heart failure at the target dose or maximum tolerance dose for over 1 month ,or unchanged dose in last 1 month; 6. Understand and sign the informed consent form;", "candidate_expression": "((Age 18-75 years) AND (ECHO) AND (Left ventricular ejection fraction (LVEF) ≤ 40%) AND (NYHA class II or III) AND (Understand and sign the informed consent form;) AND (chronic heart failure) AND (clinical signs) AND (clinical symptoms) AND (history) AND (maximum tolerance dose) AND (target dose) AND (treatment of chronic heart failure) AND (unchanged dose in last 1 month))"}
{"candidate_id": "LLM03234", "doc_id": "NCT03519568_inc", "case_bucket": "or", "source_criterion": "aged = 6 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures the subjects have completed the basic immunization of 2 needle recombinant hepatitis B vaccine, there is no inoculation history of EV71 vaccine, and no history of EV71 infection the last vaccination intervals = 14 days temperature = 37<U+2103> aged = 6 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days temperature = 37<U+2103> aged = 8 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days and the last attenuated live vaccine intervals=28days temperature = 37<U+2103> aged = 8 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days and the last attenuated live vaccine intervals = 28 days temperature = 37<U+2103>", "candidate_expression": "((2) AND (= 14 days) AND (= 28 days) AND (= 37<U+2103>) AND (= 6 months) AND (= 8 months) AND (=28days) AND (EV71 infection) AND (EV71 vaccine) AND (aged) AND (history) AND (inoculation) AND (last attenuated live vaccine intervals) AND (last vaccination intervals) AND (needle recombinant hepatitis B vaccine) AND (no) AND (sign the informed consent form) AND (temperature) AND (the legal guardians participate in all the planned follow-up and be able to comply with all research procedures))"}
{"candidate_id": "LLM03235", "doc_id": "NCT01032109_inc", "case_bucket": "other", "source_criterion": "choroidal neovascularization caused by age-related macula degeneration no previous treatment a follow-up at least 12 months a baseline visual acuity ranging from a letter score of 0 to 70 on the Early Treatment Diabetic Retinopathy Study chart", "candidate_expression": "((Early Treatment Diabetic Retinopathy Study chart) AND (age-related) AND (at least 12 months) AND (baseline) AND (choroidal neovascularization) AND (follow-up) AND (letter score of 0 to 70) AND (macula degeneration) AND (no) AND (previous) AND (treatment) AND (visual acuity))"}
{"candidate_id": "LLM03236", "doc_id": "NCT01857167_inc", "case_bucket": "or", "source_criterion": "1. Fasting glucose > 7.0 or have diabetes medication; 2. Male, 35-80 years; female, postmenopausal to 80 years; 3. Agree to participant in the trial.", "candidate_expression": "((35-80 years 35-80 years) AND (Agree to participant in the trial.) AND (Male 35-80 years) AND (diabetes) AND (female) AND (postmenopausal) AND (to 80 years) AND ((Fasting glucose > 7.0) OR (diabetes medication)))"}
{"candidate_id": "LLM03237", "doc_id": "NCT03347513_exc", "case_bucket": "or", "source_criterion": "Severe Iron deficiency anemia (hemoglobin < 8.0 g/dL). Parasitic worm infection e.g. schistosomiasis, and hook worm by stool analysis. Any cases giving clinical symptoms of gastritis e.g. nausea, vomiting, dull aching pain or soreness in the epigastrium. Cases with history of gastric ulcer diagnosed by upper endoscopy. Cases complaining of hematemesis.", "candidate_expression": "((Iron deficiency anemia Severe) AND (Parasitic worm infection) AND (gastric ulcer history) AND (gastritis clinical symptoms) AND (hematemesis) AND (hemoglobin < 8.0 g/dL) AND (stool analysis) AND (upper endoscopy) AND ((dull aching pain) OR (nausea) OR (soreness in the epigastrium) OR (vomiting)) AND ((hook worm) OR (schistosomiasis)))"}
{"candidate_id": "LLM03238", "doc_id": "NCT03008005_inc", "case_bucket": "other", "source_criterion": "Able to give informed consent Right-handed Age between 18-50 years old, Physically and neurologically healthy [confirmed by a comprehensive medical history] Current PTSD diagnosis", "candidate_expression": "((Able to give informed consent) AND (Age between 18-50 years old) AND (PTSD Current) AND (Right-handed) AND (comprehensive medical history) AND (healthy Physically) AND (neurologically healthy))"}
{"candidate_id": "LLM03239", "doc_id": "NCT02175186_exc", "case_bucket": "or", "source_criterion": "Pregnant or breast feeding History of Stomach or esophagus surgery Peptic ulcer or reflux esophagitis Zollinger-Ellison syndrome or primary esophageal motility disorders Malignant tumor Bleeding tendency or coagulopathy Contraindication of ALBIS Long term use of aspirin or P2Y12 receptor antagonist within 1month Patients who tool medicine such as PPI, APA,H2blocker, Muscarine receptor antagonist, anti-gastic agent, antacid, anticaogulant, Bisphosphonate agents, Cytotoxic drug, NSAID, adrenal cortex hormone agents (topical treatment is allowed) Terminal patient", "candidate_expression": "((ALBIS) AND (Contraindication) AND (Malignant tumor) AND (Pregnant or breast feeding) AND (patient Terminal) AND NOT (topical treatment) AND ((P2Y12 receptor antagonist) OR (aspirin)) AND ((APA) OR (Bisphosphonate agents) OR (Cytotoxic drug) OR (H2blocker) OR (Muscarine receptor antagonist) OR (NSAID) OR (PPI) OR (adrenal cortex hormone agents) OR (antacid) OR (anti-gastic agent) OR (anticaogulant)) AND ((Stomach surgery) OR (esophagus surgery)) AND ((Peptic ulcer) OR (reflux esophagitis)) AND ((Zollinger-Ellison syndrome) OR (primary esophageal motility disorders)) AND ((Bleeding tendency) OR (coagulopathy)))"}
{"candidate_id": "LLM03240", "doc_id": "NCT02630628_inc", "case_bucket": "or", "source_criterion": "Biopsy-proven LN Class III/IV±V (ISN/RPS 2003), with biopsy performed within 12 weeks of randomization. Positive anti-dsDNA. Active LN with proteinuria (urine protein/creatinine ratio >1.0 or 24-hr urine protein >1.0 g at baseline), with or without hematuria. Both 'incident' (i.e. new) patients and 'flare' patients can be included.", "candidate_expression": "((24-hr urine protein) AND (>1.0) AND (>1.0 g) AND (Active) AND (Class III/IV±V) AND (LN) AND (Positive) AND (anti-dsDNA) AND (biopsy) AND (hematuria) AND (proteinuria) AND (urine protein/creatinine ratio) AND (within 12 weeks))"}
{"candidate_id": "LLM03241", "doc_id": "NCT02882113_exc", "case_bucket": "or", "source_criterion": "Patients who have Tacrolimus trough level resulted as 2 ng/mg at the baseline. Patients who are on steroid therapy due to positive result of acute rejection test before the baseline. Patients who have received a transplant besides liver. Patients who are allergic to IP or macrolide compounds. Patients who are on cyclosporine, bosentan, or potassium sparing diuretic. Patients with genetic diseases such as galactose intolerance, Lapp lactase deficiency, or glucose-galactose malabsorption. Pregnant or lactating women. Patients not willing to adhere to study procedures/treatments.", "candidate_expression": "((2 ng/mg) AND (IP) AND (Lapp lactase deficiency) AND (Patients not willing to adhere to study procedures/treatments) AND (Pregnant or lactating women) AND (Tacrolimus) AND (acute rejection test) AND (allergic) AND (bosentan) AND (cyclosporine) AND (galactose intolerance) AND (genetic diseases) AND (glucose-galactose malabsorption) AND (liver) AND (macrolide) AND (positive) AND (potassium sparing diuretic) AND (steroid) AND (transplant))"}
{"candidate_id": "LLM03242", "doc_id": "NCT00343668_exc", "case_bucket": "or", "source_criterion": "Other tumor type than adenocarcinoma Central nervous system (CNS) metastases or prior radiation for CNS metastases Gastric outlet obstruction or intestinal obstruction Evidence of gastrointestinal bleeding The patient has bony lesions as the sole evaluable disease. Past or concurrent history of neoplasm other than stomach cancer, except for curatively treated non-melanoma skin cancer or in situ carcinoma of the cervix uteri Pregnant or lactating women, women of childbearing potential not employing adequate contraception Other serious illness or medical conditions Unstable cardiac disease despite treatment, myocardial infarction within 6 months prior to study entry History of significant neurologic or psychiatric disorders including dementia or seizures Active uncontrolled infection Other serious underlying medical conditions which could impair the ability of the patient to participate in the study Concomitant administration of any other experimental drug under investigation, or concomitant chemotherapy, hormonal therapy, or immunotherapy concomitant drug medication; The following drugs cause drug interaction with S-1. i. Warfarin, phenprocoumon: increase bleeding tendency ii. Increase blood concentration of phenytoin iii. sorivudine: inhibit DPD -> increase toxicity according to fluoropyrimidine iv. allopurinol : decrease activity of S-1", "candidate_expression": "((CNS metastases) AND (Central nervous system (CNS) metastases) AND (Evidence of) AND (Gastric outlet obstruction) AND (History) AND (Pregnant) AND (Unstable cardiac disease) AND (Warfarin) AND (ability of the patient to participate) AND (allopurinol) AND (bleeding tendency increase) AND (blood concentration of phenytoin Increase) AND (bony lesions the sole) AND (chemotherapy) AND (childbearing potential) AND (dementia) AND (drug) AND (experimental drug Concomitant) AND (fluoropyrimidine) AND (gastrointestinal bleeding) AND (history of) AND (hormonal therapy) AND (immunotherapy) AND (in situ carcinoma of the cervix uteri) AND (infection Active uncontrolled) AND (intestinal obstruction) AND (lactating) AND (medical conditions) AND (medication) AND (myocardial infarction within 6 months prior to study entry) AND (neoplasm) AND (neurologic disorders) AND (non-melanoma skin cancer) AND (phenprocoumon) AND (psychiatric disorders) AND (radiation) AND (seizures) AND (serious illness) AND (serious medical conditions) AND (sorivudine) AND (treatment) AND (tumor) AND (women) AND NOT (adenocarcinoma) AND NOT (stomach cancer) AND NOT (treated curatively) AND NOT (contraception))"}
{"candidate_id": "LLM03243", "doc_id": "NCT02862314_inc", "case_bucket": "other", "source_criterion": "aged 18 or older, have undergone oro-tracheal intubation for a coma (Glasgow Coma Score below or equal to 8), with mechanical ventilation initiated in the first 48 hours following hospital admission", "candidate_expression": "((18 or older) AND (Glasgow Coma Score) AND (aged) AND (below or equal to 8)) AND (coma) AND (first 48 hours following hospital admission) AND (hospital admission) AND (mechanical ventilation) AND (oro-tracheal intubation))"}
{"candidate_id": "LLM03244", "doc_id": "NCT03228654_inc", "case_bucket": "or", "source_criterion": "uterine size <12 weeks. presence of benign cause for the hysterectomy e.g. fibroid uterus, perimenopausal beeding not responding to medical treatment or complex endometrial hyperplasia without atypia. Absence of significant scarring in the pelvis from previous surgeries.", "candidate_expression": "((benign cause) AND (complex endometrial hyperplasia) AND (fibroid uterus) AND (hysterectomy) AND (medical treatment) AND (perimenopausal beeding responding to medical treatment) AND (surgeries previous) AND (uterine size <12 weeks) AND NOT (atypia) AND NOT (significant scarring pelvis from previous surgeries))"}
{"candidate_id": "LLM03245", "doc_id": "NCT03445949_exc", "case_bucket": "or", "source_criterion": "indications to dual antiplatelet therapy other than atrial fibrillation or left atrial appendage occlusion at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. coronary artery disease) indications to anticoagulation at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. pulmonary embolism) known allergy to clopidogrel or acetylsalicylic acid precluding its administration as specified by the protocol any known inborn or acquired coagulation disorders poor tolerance of or technical difficulties with performing transesophageal echocardiography peridevice leak >5mm on transesophageal echocardiography study preceding enrollment left atrial thrombus on transesophageal echocardiography study performed after successful left atrial appendage closure but before enrollment life expectancy of less than 18months participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months chronic kidney disease stage IV and V women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women", "candidate_expression": "((allergy) AND (anticoagulation at the time of enrollment predicted appearance) AND (chronic kidney disease) AND (coagulation disorders) AND (coronary artery disease within the duration of the trial) AND (dual antiplatelet therapy at the time of enrollment) AND (indications) AND (left atrial appendage closure successful before enrollment enrollment) AND (left atrial thrombus) AND (life expectancy less than 18months) AND (participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months) AND (peridevice leak >5mm) AND (predicted appearance) AND (pulmonary embolism within the duration of the trial) AND (transesophageal echocardiography) AND (transesophageal echocardiography after successful left atrial appendage closure) AND (transesophageal echocardiography study) AND (women) AND (women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women) AND ((acetylsalicylic acid) OR (clopidogrel)) AND ((poor tolerance) OR (technical difficulties)) AND ((atrial fibrillation) OR (left atrial appendage occlusion)) AND ((stage IV) OR (stage V)) AND ((breast feeding) OR (pregnant)))"}
{"candidate_id": "LLM03246", "doc_id": "NCT02560766_inc", "case_bucket": "or", "source_criterion": "Male and female adolescent patients, aged 13 to 17 years, diagnosed with RLS based on the IRLSSG consensus criteria (Allen RP 2014) (Appendix 2). Total RLS severity score of 15 or greater on the IRLS rating scale at Visit 1 (screening) and at Visit 2 (baseline) (Appendix 8). RLS symptoms for at least 4 of 7 consecutive evenings/nights during the screening period. Body weight greater than 33.4 kg and a healthy weight using age-based body mass index (BMI) range 5th-85th percentile at screening and baseline. Appendix 3 contains BMI-for-age charts that can be consulted. Estimated creatinine clearance of at least 60 mL/min (using the Cockcroft-Gault equation) at screening only. Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed.", "candidate_expression": "((13 to 17 years) AND (15 or greater) AND (5th-85th percentile) AND (BMI) AND (Body weight) AND (Estimated creatinine clearance) AND (IRLSSG consensus criteria) AND (RLS) AND (RLS symptoms) AND (Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed) AND (Total RLS severity score) AND (adolescent) AND (aged) AND (at least 4 of 7 consecutive evenings/nights) AND (at least 60 mL/min) AND (body mass index) AND (greater than 33.4 kg) AND ((Male) OR (female)))"}
{"candidate_id": "LLM03247", "doc_id": "NCT02701881_exc", "case_bucket": "or", "source_criterion": "Acute critical limb ischemia Severe critical limb ischemia (Rutherford category 6) Major bleeding history within prior 2 months Known hypersensitivity or contraindication to any of the following medications: heparin, aspirin, clopidogrel or contrast agents Age > 85 years Severe hepatic dysfunction (> 3 times normal reference values) Significant renal dysfunction (Serum creatinine > 2.0 mg/dl Significant leucopenia, neutropenia, thrombocytopenia, anemia, or known bleeding diathesis LVEF <40% or clinically overt congestive heart failure Pregnant women or women with potential childbearing Life expectancy <1 year due to comorbidity Previous bypass surgery or stenting of the superficial femoral artery Untreated inflow disease of the ipsilateral pelvic arteries (more than 50%stenosis or or occlusion Popliteal artery stenosis >50% at P2 or P3 segment", "candidate_expression": "((Age > 85 years) AND (Life expectancy <1 year) AND (Major bleeding history within prior 2 months) AND (Popliteal artery stenosis >50% P2 or P3 segment) AND (Rutherford category 6) AND (Serum creatinine > 2.0 mg/dl) AND (comorbidity) AND (hepatic dysfunction Severe) AND (inflow disease Untreated ipsilateral pelvic arteries) AND (limb ischemia) AND (limb ischemia Acute critical Severe critical) AND (renal dysfunction Significant) AND (stenosis) AND ((contraindication) OR (hypersensitivity)) AND ((aspirin) OR (clopidogrel) OR (contrast agents) OR (heparin)) AND ((anemia) OR (bleeding diathesis) OR (leucopenia) OR (neutropenia) OR (thrombocytopenia)) AND ((LVEF <40%) OR (congestive heart failure clinically overt)) AND ((Pregnant) OR (potential childbearing)) AND ((women)) AND ((bypass surgery Previous) OR (stenting of the superficial femoral artery Previous)) AND ((more than 50%) OR (occlusion)))"}
{"candidate_id": "LLM03248", "doc_id": "NCT03402945_inc", "case_bucket": "other", "source_criterion": "≥18 years of age undergoing open-heart surgery (sternotomy, including minimally-invasive sternotomies)", "candidate_expression": "((age) AND (minimally-invasive sternotomies) AND (open-heart surgery) AND (sternotomy) AND (undergoing) AND (≥18 years))"}
{"candidate_id": "LLM03249", "doc_id": "NCT02301039_inc", "case_bucket": "or", "source_criterion": "Age ≥ 18 years (Age ≥ 12 years for patients with bone sarcomas). Histologically confirmed diagnosis of unresectable, recurrent, and/or metastatic high grade soft-tissue or bone sarcoma of one of the following subtypes: soft tissue sarcomas (leiomyosarcoma, poorly differentiated/de-differentiated liposarcoma, high grade pleomorphic undifferentiated sarcoma/MFH and synovial sarcoma), and bone sarcomas (Ewing sarcoma, osteosarcoma, and chondrosarcoma [de-differentiated or mesenchymal]). ECOG Performance Status of 0 or 1. At least one site of measurable disease on CT/MRI scans as defined by RECIST 1.1. Baseline imaging must be performed within 30 days of dosing. At least one site of accessible disease for pre- and post-treatment core biopsies for at least 20 patients per arm on the expansion cohorts. Patients may have received 1-3 prior systemic therapies in the metastatic setting. Adequate organ function within 14 days of dosing Must be willing to provide and have available archival tissue for PD-L1 testing. Written, voluntary informed consent. Fertile men and women of childbearing potential must agree to use an effective method of birth control from providing signed consent and for 120 days after last study drug administration. Women of childbearing potential include pre-menopausal women and women within the first 2 years of the onset of menopause. Women of childbearing potential must have a negative pregnancy test ≤ 72 hours prior to Day 1 of study. Effective methods of birth control include: surgically sterile, barrier device (condom, diaphragm), contraceptive coil, intrauterine device (IUD), and abstinence. Life expectancy of >12 weeks. Patients with central nervous system disease are eligible for enrollment if they have received prior radiotherapy or surgery to sites of CNS metastatic disease and are without evidence of clinical progression for at least 4 weeks prior to screening, have no evidence of new or enlarging brain metastases, and are off steroids for at least 7 days before first dose of pembrolizumab.", "candidate_expression": "((0 or 1) AND (1-3) AND (>12 weeks) AND (Adequate organ function) AND (Age) AND (Baseline) AND (CNS metastatic disease) AND (CT scans) AND (Day 1) AND (ECOG Performance Status) AND (Ewing sarcoma) AND (Histologically) AND (Life expectancy) AND (MFH) AND (MRI scans) AND (Women) AND (Written, voluntary informed consent.) AND (abstinence) AND (barrier device) AND (birth control) AND (bone sarcoma) AND (bone sarcomas) AND (brain metastases) AND (central nervous system disease) AND (childbearing potential) AND (chondrosarcoma) AND (clinical progression) AND (condom) AND (confirmed) AND (contraceptive coil) AND (de-differentiated) AND (diaphragm) AND (dosing) AND (enlarging) AND (first dose of pembrolizumab) AND (for 120 days after last study drug administration) AND (for at least 4 weeks prior to screening) AND (for at least 7 days before first dose of pembrolizumab) AND (from providing signed consent) AND (high grade) AND (imaging) AND (intrauterine device (IUD)) AND (last study drug administration) AND (leiomyosarcoma) AND (liposarcoma) AND (measurable disease) AND (men) AND (mesenchymal) AND (metastatic) AND (metastatic setting) AND (negative) AND (new) AND (no) AND (off) AND (osteosarcoma) AND (pembrolizumab) AND (pleomorphic) AND (poorly differentiated) AND (pre-menopausal) AND (pregnancy test) AND (prior) AND (providing signed consent) AND (radiotherapy) AND (recurrent) AND (sarcoma) AND (screening) AND (soft tissue sarcomas) AND (soft-tissue sarcoma) AND (steroids) AND (surgery) AND (surgically sterile) AND (synovial sarcoma) AND (systemic therapies) AND (the onset of menopause) AND (undifferentiated) AND (unresectable) AND (within 14 days of dosing) AND (within 30 days of dosing) AND (within the first 2 years of the onset of menopause) AND (without) AND (women) AND (≤ 72 hours prior to Day 1) AND (≥ 12 years) AND (≥ 18 years))"}
{"candidate_id": "LLM03250", "doc_id": "NCT02634541_exc", "case_bucket": "or", "source_criterion": "Psoriasis or psoriasis arthropathy Inflammatory bowel disease Unwillingness to participate in the study with additional imaging protocols Expected life-span less than <1 year Diabetes (to improve the PET imaging quality) Probable noncompliance Pregnancy Age <18 years or >75 years Contraindication for adalimumab Methotrexate used within the previous 6 months A biologic medicine used within the previous 6 months", "candidate_expression": "((Age <18 years >75 years) AND (Contraindication) AND (Diabetes) AND (Expected life-span less than <1 year) AND (Inflammatory bowel disease) AND (Methotrexate within the previous 6 months) AND (PET imaging quality) AND (Pregnancy) AND (Psoriasis) AND (Unwillingness to participate in the study with additional imaging protocols) AND (adalimumab) AND (biologic medicine within the previous 6 months) AND (noncompliance Probable) AND (psoriasis arthropathy))"}
```
