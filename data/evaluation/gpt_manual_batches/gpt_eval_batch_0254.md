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
{"candidate_id": "LLM06326", "doc_id": "NCT03126214_exc", "case_bucket": "or", "source_criterion": "Uncontrolled hypertension (defined as average SBP = 160 mmHg [2 readings taken at time of screening]). End stage renal disease (CrCl < 15 ml/min) Valvular Heart Disease including those with prosthetic valve, mitral stenosis (moderate to severe) or valve repair. Excess alcohol intake (males: = 28 units/week, females: = 21 units/week. One unit of alcohol = 8 oz beer, 1 oz hard liquor or 4 oz wine). Intracranial bleed at any point. History of \"Major Bleeding\" at any point (defined as overt bleeding at a critical site including intracranial, intraspinal, intraocular, pericardial, or retroperitoneal; or bleed requiring hospitalization). Foreshortened life-expectancy or severe comorbidities precluding study follow-up period Unable to read/understand English Severe cognitive impairment (defined as score = 5 on the Short Portable Mental Status Questionnaire)", "candidate_expression": "((2 readings) AND (< 15 ml/min) AND (= 160 mmHg) AND (= 21 units/week) AND (= 28 units/week) AND (= 5) AND (CrCl) AND (End stage renal disease) AND (Excess) AND (Foreshortened) AND (History) AND (Intracranial bleed) AND (Major Bleeding) AND (Severe) AND (Short Portable Mental Status Questionnaire) AND (Uncontrolled) AND (alcohol intake) AND (at any point) AND (at time of screening) AND (average SBP) AND (cognitive impairment) AND (critical site) AND (hospitalization) AND (hypertension) AND (screening) AND ((Valvular Heart Disease) OR (mitral stenosis) OR (prosthetic valve) OR (valve repair)) AND ((moderate) OR (severe)) AND ((females) OR (males)) AND ((intracranial) OR (intraocular) OR (intraspinal) OR (pericardial) OR (retroperitoneal)) AND ((bleed) OR (overt bleeding)) AND ((life-expectancy) OR (severe comorbidities)))"}
{"candidate_id": "LLM06327", "doc_id": "NCT02509091_inc", "case_bucket": "other", "source_criterion": "Age=18 years and =80 years; Patients with non-cystic fibrosis bronchiectasis diagnosed by high-resolution CT; Are sensitive to amikacin; Acute exacerbation of bronchiectasis; Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc; Willing to join in and sign the informed consent form.", "candidate_expression": "((Acute exacerbation of bronchiectasis) AND (Age =18 years and =80 years) AND (Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc) AND (Willing to join in and sign the informed consent form) AND (amikacin) AND (high-resolution CT) AND (non-cystic fibrosis bronchiectasis) AND (sensitive))"}
{"candidate_id": "LLM06328", "doc_id": "NCT02035800_inc", "case_bucket": "other", "source_criterion": "Patients aged of 18 and over, Satisfying the 1987 American College of Rheumatology (ACR) criteria for RA Receiving a prescription of Adalimumab 40 mg subcutaneous every two weeks.", "candidate_expression": "((Adalimumab 40 mg every two weeks subcutaneous) AND (RA 1987 American College of Rheumatology (ACR) criteria) AND (aged 18 and over))"}
{"candidate_id": "LLM06329", "doc_id": "NCT01088750_inc", "case_bucket": "other", "source_criterion": "Stage IA or IIA disease Not specified No prior therapy", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06330", "doc_id": "NCT01642875_exc", "case_bucket": "or", "source_criterion": "Metastatic tumor Locally unresectable tumor Previous gastric resection ASA IV-V Age under 18 years Preoperative complete parenteral or enteral feeding Immunosuppressive therapy before operation Severe malnutrition Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia", "candidate_expression": "((ASA IV-V) AND (Age under 18 years) AND (Immunosuppressive therapy before operation) AND (Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia) AND (complete enteral feeding) AND (complete parenteral feeding) AND (gastric resection Previous) AND (malnutrition Severe) AND (operation) AND (tumor) AND (tumor Metastatic Locally unresectable))"}
{"candidate_id": "LLM06331", "doc_id": "NCT02816164_exc", "case_bucket": "other", "source_criterion": "Contraindication to Filgrastim", "candidate_expression": "((Contraindication) AND (Filgrastim))"}
{"candidate_id": "LLM06332", "doc_id": "NCT02965443_exc", "case_bucket": "or", "source_criterion": "Use of any oral antidiabetic treatment except for metformin (i.e., sulphonylureas, DPP-IV inhibitors, thiazolidinediones, SGLT-2 inhibitors (Sodium dependent glucose transporter) or GLP-1 analogues (glucagone like peptide) within the last three months prior to Screening Repeated episodes of severe hypoglycaemia within the last six months prior to Screening History of diabetic ketoacidosis, precoma diabetica, or diabetic coma Treatment with any other investigational drug within the last three months before Screening Acute infections within the last four weeks prior to Screening Recurrent urogenital infections History of pancreatitis Anamnestic history of hypersensitivity to the study drugs or to drugs with similar chemical structures History of severe or multiple allergies Concomitant participation in other clinical trials Type 1 diabetes Cardiovascular disease Clinically relevant ventricular tachycardia or ventricular fibrillation, 3rd degree AV block or Torsades de Pointes or treatment with antiarrhythmic drugs. Percutaneous coronary intervention within the past 6 months. Any of the following within the past 6 months: myocardial infarction (MI), coronary artery bypass surgery; unstable angina; or stroke. Malignancy including leukemia and lymphoma within the last 5y. Liver disease such as cirrhosis or chronic active hepatitis. Significant renal dysfunction (see also exclusion criteria laboratory abnormalities). State after kidney transplantation Endocrine disease: Systolic blood pressure outside the range of 100-160 mmHg or diastolic blood pressure above 95 mmHg at Screening History of active substance abuse (including alcohol > 40g/day) within the past 2 years. Pregnancy or childbearing potential without adequate contraception Present therapy with systemic steroids Presence of psychiatric disorder or intake of anti-depressive or anti-psychotic agents with the exception of benzodiazepines and SSRIs/SNRI's (selective serotonin reuptake inhibitor) Potentially unreliable subjects, and those judged by the investigator to be unsuitable for the study. Contraindications for Magnetic resonance (MR) scanning such as persons with cardiac pacemaker and implants out of metal or claustrophobia", "candidate_expression": "((3rd degree AV block) AND (Acute infections within the last four weeks prior to Screening) AND (Cardiovascular disease) AND (Contraindications) AND (DPP-IV inhibitors) AND (Endocrine disease) AND (GLP-1 analogues) AND (Liver disease) AND (Magnetic resonance (MR) scanning) AND (Malignancy within the last 5y) AND (Percutaneous coronary intervention within the past 6 months) AND (Pregnancy) AND (SGLT-2 inhibitors) AND (SNRI's) AND (SSRIs) AND (State after kidney transplantation) AND (Systolic blood pressure outside the range of 100-160 mmHg) AND (Torsades de Pointes) AND (Treatment within the last three months before Screening) AND (Type 1 diabetes) AND (alcohol > 40g/day) AND (allergies History multiple) AND (anti-depressive agents) AND (anti-psychotic agents) AND (antiarrhythmic drugs) AND (benzodiazepines) AND (cardiac pacemaker) AND (childbearing potential) AND (chronic active hepatitis) AND (cirrhosis) AND (claustrophobia) AND (coronary artery bypass surgery) AND (diabetic coma) AND (diabetic ketoacidosis) AND (diastolic blood pressure above 95 mmHg) AND (drugs with similar chemical structures severe) AND (hypersensitivity Anamnestic history) AND (implants out of metal) AND (investigational drug) AND (kidney transplantation) AND (leukemia) AND (lymphoma) AND (myocardial infarction (MI)) AND (oral antidiabetic) AND (oral antidiabetic treatment) AND (pancreatitis History) AND (participation in other clinical trials Concomitant) AND (precoma diabetica) AND (psychiatric disorder) AND (renal dysfunction Significant) AND (severe hypoglycaemia Repeated within the last six months prior to Screening) AND (stroke) AND (study drugs) AND (substance abuse History active within the past 2 years) AND (sulphonylureas) AND (systemic steroids) AND (therapy Present) AND (thiazolidinediones) AND (treatment) AND (unreliable subjects) AND (unstable angina) AND (unsuitable for the study) AND (urogenital infections Recurrent) AND (ventricular fibrillation) AND (ventricular tachycardia) AND NOT (metformin) AND NOT (contraception adequate))"}
{"candidate_id": "LLM06333", "doc_id": "NCT02664558_inc", "case_bucket": "or", "source_criterion": "1. Male or female, 18-75 years old. 2. Has a diagnosis of WHO Group 1 PAH. 3. Right heart catheterization performed at Screening with results that are: 1. Mean pulmonary arterial pressure ≥25 mmHg (at rest) and 2. Pulmonary venous hypertension (measured as pulmonary capillary wedge pressure (PCWP) ≤15 mmHg. If PCWP is not available, then mean left atrial pressure or left ventricular end-diastolic pressure ≤15 mmHg in the absence of left atrial obstruction. and 3. Pulmonary vascular resistance (PVR) ≥300 dyn•s/cm5 (3.75 Wood units) 4. Has WHO/NYHA-FC of II or III. 5. Be on stable dose of at least one of the following PAH-specific therapies: endothelin receptor antagonist, an agent acting on the nitric oxide pathway (phosphodiesterase type 5 inhibitor or soluble guanylate cyclase stimulator), and/or a prostacyclin or prostacyclin analog. 6. Has a 6-minute walk distance that is ≥150 and ≤500 meters. 7. Have a ventilation-perfusion scan that rules out thromboembolic disease.", "candidate_expression": "((6-minute walk distance ≥150 and ≤500 meters) AND (Mean pulmonary arterial pressure ≥25 mmHg at rest) AND (PAH) AND (PAH-specific therapies stable dose at least one) AND (Pulmonary vascular resistance (PVR) ≥300 dyn•s/cm5 3.75 Wood units) AND (Pulmonary venous hypertension) AND (Right heart catheterization performed at Screening) AND (WHO Group 1) AND (WHO/NYHA-FC) AND (pulmonary capillary wedge pressure (PCWP) ≤15 mmHg) AND (ventilation-perfusion scan) AND (years old 18-75 years) AND NOT (left atrial obstruction) AND NOT (thromboembolic disease) AND ((Male) OR (female)) AND ((left ventricular end-diastolic pressure ≤15 mmHg) OR (mean left atrial pressure ≤15 mmHg)) AND ((II) OR (III)) AND ((agent acting on the nitric oxide pathway) OR (endothelin receptor antagonist) OR (prostacyclin analog)) AND ((phosphodiesterase type 5 inhibitor) OR (soluble guanylate cyclase stimulator)))"}
{"candidate_id": "LLM06334", "doc_id": "NCT02996916_exc", "case_bucket": "or", "source_criterion": "Secondary hypertension or malignant hypertension Diabetes mellitus History or evidence of a stroke Hepatic or hematologic abnormality Mild Cognitive Impairment or Dementia Serum potassium level = 5.5 mEq/L Serum creatinine level = 3.0 mg/dL Acute or chronic disease Allergy to any drugs Pregnancy", "candidate_expression": "((Allergy) AND (Diabetes mellitus) AND (Pregnancy) AND (Serum creatinine level = 3.0 mg/dL) AND (Serum potassium level = 5.5 mEq/L) AND (any drugs) AND (stroke) AND ((Secondary hypertension) OR (malignant hypertension)) AND ((Dementia) OR (Mild Cognitive Impairment)) AND ((Acute disease) OR (chronic disease)) AND ((History) OR (evidence)) AND ((Hepatic abnormality) OR (hematologic abnormality)))"}
{"candidate_id": "LLM06335", "doc_id": "NCT02691793_inc", "case_bucket": "or", "source_criterion": "Provision of fully informed consent prior to study specific procedures. Patients must be >= 19 years of age RET fusion positive or FGFR2 fusion/other FGFR mutation Refractory solid tumor and/or specific sensitivity to Sunitinib by Avatar scan that has progressed following standard therapy or that has not responded to standard therapy or for which there is no standard therapy. ECOG Performance status0-2 Have measurable or evaluated disease based on RECIST 1.1 as determined by investigator. Absolute neutrophil count >= 1.5 x 109/L, Hemoglobin >= 9g/dL, Platelets>=100 x 109/L Bilirubin <= 1.5 x upper limit of normal AST/ALT <= 2.5 X upper limit of normal(5.0 x upper limit of normal, for subject with liver metastases) Creatinine<= 1.5 X UNL Patients of child-bearing potential should be using adequate contraceptive measures should not be breast feeding and must have a negative pregnancy test prior to start of dosing Adequate heart function", "candidate_expression": "((0-2) AND (5.0 x upper limit of normal) AND (<= 1.5 X UNL) AND (<= 1.5 x upper limit of normal) AND (<= 2.5 X upper limit of normal() AND (>= 1.5 x 109/L) AND (>= 19 years) AND (>= 9g/dL,) AND (>=100 x 109/L) AND (ALT) AND (AST) AND (Absolute neutrophil count) AND (Adequate) AND (Adequate heart function) AND (Bilirubin) AND (Creatinine) AND (ECOG Performance status) AND (Hemoglobin) AND (Platelets) AND (Provision of fully informed consent prior to study specific procedures) AND (Refractory) AND (adequate contraceptive measures) AND (age) AND (breast feeding) AND (child-bearing potential) AND (heart function) AND (liver metastases) AND (negative) AND (not be) AND (positive) AND (pregnancy test) AND (prior to start of dosing) AND (sensitivity) AND (start of dosing) AND ((RET fusion) OR (Sunitinib) OR (solid tumor)) AND ((FGFR mutation) OR (FGFR2 fusion)))"}
{"candidate_id": "LLM06336", "doc_id": "NCT01116973_inc", "case_bucket": "or", "source_criterion": "Subject's ability to lay in a supine position with their hands at their sides during CVP measurements A consent form signed by the patient or patient's representative Subjects that are age 18-90 Subjects that have an indwelling CICC and are transitioning to a PICC for long-term IV access CICC placed in the internal jugular vein or subclavian vein position", "candidate_expression": "((18-90) AND (A consent form signed by the patient or patient's representative) AND (CICC placed) AND (CVP measurements) AND (PICC) AND (ability to lay in a supine position with their hands at their sides) AND (age) AND (during CVP measurements) AND (indwelling CICC) AND (transitioning to a PICC) AND ((in the internal jugular vein position) OR (in the subclavian vein position)))"}
{"candidate_id": "LLM06337", "doc_id": "NCT02604459_inc", "case_bucket": "other", "source_criterion": "Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board, Hip fracture surgery scheduled under general anesthesia Subject is 65 years or older on the day of surgery", "candidate_expression": "((Hip fracture surgery) AND (Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board,) AND (general anesthesia) AND (older 65 years or older) AND (surgery))"}
{"candidate_id": "LLM06338", "doc_id": "NCT02295202_inc", "case_bucket": "other", "source_criterion": "Metabolic Syndrome (ATP III) Moderate to severe OSA", "candidate_expression": "((ATP) AND (III) AND (Metabolic Syndrome) AND (Moderate to severe) AND (OSA))"}
{"candidate_id": "LLM06339", "doc_id": "NCT02092467_inc", "case_bucket": "or", "source_criterion": "Moderate to severe rheumatoid arthritis Taking methotrexate without adequate control of symptoms Have at least one cardiovascular risk factor (eg, current smoker, high blood pressure, high cholesterol levels, diabetes mellitus, history of heart attack, family history of coronary heart disease, extra-articular RA disease)", "candidate_expression": "((cardiovascular risk factor at least one) AND (methotrexate) AND (rheumatoid arthritis Moderate to severe) AND NOT (adequate control of symptoms) AND ((RA disease extra-articular) OR (coronary heart disease family history) OR (diabetes mellitus) OR (heart attack history) OR (high blood pressure) OR (high cholesterol levels) OR (smoker current)))"}
{"candidate_id": "LLM06340", "doc_id": "NCT03250507_exc", "case_bucket": "or", "source_criterion": "Patient with a chronic pain condition, major unexpected surgical complication, unexpected prolonged intubation, patient refusal, local anesthetic allergy, any contraindication to regional anesthesia, greater than 2 attempts by resident and greater than 1 attempt by staff anesthesiologist for TAP block.", "candidate_expression": "((anesthesiologist) AND (greater than 1) AND (greater than 2) AND (local anesthetic) AND (major) AND (prolonged) AND (regional anesthesia) AND (resident) AND (unexpected) AND ((TAP block) OR (allergy) OR (chronic pain condition) OR (contraindication) OR (intubation) OR (patient refusal) OR (unexpected surgical complication)))"}
{"candidate_id": "LLM06341", "doc_id": "NCT02109081_inc", "case_bucket": "other", "source_criterion": "patients = 70 years of age, undergoing a noncardiac surgical procedure under general anesthesia, with an anticipated duration of postoperative admission of at least 2 days.", "candidate_expression": "((= 70 years) AND (admission) AND (age) AND (anticipated) AND (at least 2 days) AND (duration of postoperative admission) AND (general anesthesia) AND (noncardiac surgical procedure) AND (postoperative))"}
{"candidate_id": "LLM06342", "doc_id": "NCT03413891_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for dental extraction and treated with edoxaban, apixaban, rivaroxaban or dabigatran Not having taken the direct oral anticoagulant on the day of the extraction Provision of signed and dated informed consent form Stated willingness to comply with all study procedures and availability for the duration of the study", "candidate_expression": "((Provision of signed and dated informed consent form) AND (Stated willingness to comply with all study procedures and availability for the duration of the study) AND (apixaban) AND (dabigatran) AND (dental extraction scheduled for) AND (edoxaban) AND (rivaroxaban) AND NOT (anticoagulant oral on the day of the extraction))"}
{"candidate_id": "LLM06343", "doc_id": "NCT01664507_inc", "case_bucket": "other", "source_criterion": "croup children between 6 month and 5 years old Westley croup score between 3 and 11", "candidate_expression": "((Westley croup score between 3 and 11) AND (children) AND (old between 6 month and 5 years))"}
{"candidate_id": "LLM06344", "doc_id": "NCT02721017_inc", "case_bucket": "other", "source_criterion": "scheduled for Nuss procedure for pectus excavatum correction at least 13 years old at the time of the procedure", "candidate_expression": "((Nuss procedure) AND (at least 13 years) AND (at the time of the procedure) AND (old) AND (pectus excavatum) AND (scheduled))"}
{"candidate_id": "LLM06345", "doc_id": "NCT03123562_exc", "case_bucket": "or", "source_criterion": "Epilepsy Hydrocephalus with ventricular drain Coagulation disorders Allergy to anesthetic agents Severe health conditions such as cancer, failure of heart, lung, liver or kidney Active infections", "candidate_expression": "((Active) AND (Allergy) AND (Coagulation disorders) AND (Epilepsy) AND (Hydrocephalus) AND (Severe health conditions) AND (anesthetic agents) AND (cancer) AND (failure of heart) AND (failure of kidney) AND (failure of liver) AND (failure of lung) AND (infections) AND (ventricular drain))"}
{"candidate_id": "LLM06346", "doc_id": "NCT02102243_inc", "case_bucket": "other", "source_criterion": "Normotensive controls Stage I (140-159/90-99 mmHg) untreated subjects with essential hypertension Patients with PA and stage I (140-159/90-99 mmHg) hypertension", "candidate_expression": "((PA) AND (controls Normotensive) AND (essential hypertension Stage I untreated) AND (hypertension stage I))"}
{"candidate_id": "LLM06347", "doc_id": "NCT03016741_inc", "case_bucket": "or", "source_criterion": "Have diagnosis of prostate cancer and have received treatment with GnRH agonist or antagonist therapy for at least 1 month prior to enrollment. Willing and able to complete survey questionnaires in English without assistance through the duration of the study. This stipulation is in place because not all of the proposed quality of life or cognitive tests are available or validated in other languages. Age = 18 years. Ability to understand and the willingness to sign a written informed consent document written in English that is approved by an institutional review board. Have either newly diagnosed metastatic hormone sensitive prostate cancer (mHSPC) or castration-resistant metastatic prostate cancer (mCRPC) and eligible to undergo treatment with abiraterone acetate (mHSPC or mCRPC) or enzalutamide (mCRPC) Patients may have received the following prior AR directed therapy prior to enrollment: bicalutamide, ketoconazole. Prior to enrollment, patients may have received treatment with abiraterone acetate or enzalutamide for no more than 14 days before completing baseline studies. Patients may have received chemotherapy for hormone-sensitive metastatic prostate cancer only, but it must not have lasted for more than 6 months. At least 12 months must have elapsed since completion of chemotherapy. Patients may have received prior definitive radiation therapy or surgery. At least 60 days must have elapsed since completion of definitive radiation therapy or surgery and patient must have only grade 2 or less adverse effects at the time of registration. Enrollment during palliative radiation of = 10 days, or radiation of = 10 days during the duration of the study is allowed. Patients must be able to take oral medication.", "candidate_expression": "((= 18 years) AND (Age) AND (At least 12 months must have elapsed since completion of chemotherapy) AND (At least 60 days must have elapsed since completion of definitive radiation therapy or surgery) AND (GnRH agonist) AND (GnRH antagonist) AND (abiraterone acetate) AND (adverse effects) AND (at the time of registration) AND (castration-resistant) AND (chemotherapy) AND (completion of chemotherapy) AND (completion of definitive radiation therapy or surgery) AND (definitive) AND (enzalutamide) AND (for at least 1 month) AND (grade 2 or less) AND (hormone sensitive) AND (hormone-sensitive) AND (lasted for more than 6 months) AND (mCRPC) AND (mHSPC) AND (metastatic) AND (not) AND (prior) AND (prior to enrollment) AND (prostate cancer) AND (radiation therapy) AND (surgery) AND (treatment))"}
{"candidate_id": "LLM06348", "doc_id": "NCT03500211_inc", "case_bucket": "or", "source_criterion": "Pregnant patients who require a scheduled or non-urgent cesarean birth Patient able to receive neuraxial analgesia Patient able to give verbal and written consent for both cesarean birth and study", "candidate_expression": "((Patient able to give verbal and written consent for both cesarean birth and study) AND (Pregnant) AND (cesarean birth) AND (neuraxial analgesia able to receive) AND ((non-urgent) OR (scheduled)))"}
{"candidate_id": "LLM06349", "doc_id": "NCT03216447_exc", "case_bucket": "or", "source_criterion": "Patient has previously received or is receiving an organ transplant other than a liver. Patient currently requires dialysis Recipient or donor is known to be seropositive for human immunodeficiency virus (HIV) Patient has received a liver transplant from a non-heart beating donor Patient who is HCV negative has received an HCV positive (HCV RNA by PCR or HCV antibody) donor liver Patient who is HbsAg negative has received an HbsAg positive (HBV DNA by PCR or HBV antibody) donor liver Patient has received a liver transplant from a decrease donor > 70 years of age Patient has a current malignancy or a history of malignancy (within the past 5 years), except hepatocellular carcinoma within UCSF Criteria and basal or non-metastatic squamous cell carcinoma of skin that has been treated successfully. Patient is hemodynamically unstable on POD 15", "candidate_expression": "((> 70 years) AND (HBV DNA) AND (HBV antibody) AND (HCV) AND (HCV RNA) AND (HCV antibody) AND (HIV) AND (HbsAg) AND (PCR) AND (POD 15) AND (Recipient) AND (UCSF Criteria) AND (age) AND (basal cell carcinoma of skin) AND (dialysis) AND (donor) AND (except) AND (heart beating) AND (hemodynamically unstable) AND (hepatocellular carcinoma) AND (history of malignancy) AND (human immunodeficiency virus) AND (liver) AND (liver transplant) AND (malignancy) AND (negative) AND (non) AND (non-metastatic) AND (organ transplant) AND (other than) AND (positive) AND (seropositive) AND (squamous cell carcinoma of skin) AND (treated successfully) AND (within the past 5 years))"}
{"candidate_id": "LLM06350", "doc_id": "NCT02886962_inc", "case_bucket": "or", "source_criterion": "Adult patients (= 18 years) Patient on hemodialysis treatment for at least 1 month Patient with a history of, or presenting a new episode of atrial fibrillation (either permanent or paroxysmal). Patient with a CHADS2VASC score =2 Patient with high risk of bleeding as defined by (1) HASBLED score =3 OR (2) HASBLED = CHADS2VASC score, OR (3) recent history of severe bleeding (type 3a, 3b, 3c), particularly cerebral or gastrointestinal, OR (4) prior recurrent (>2) history of falls. Patient capable of understanding information about the study and of giving his/her consent Patient informed of the preliminary medical exam results Patient with healthcare insurance Written consent signed", "candidate_expression": "((= 18) AND (=2) AND (=3) AND (>2) AND (Adult) AND (CHADS2VASC score) AND (HASBLED score) AND (Patient capable of understanding information about the study and of giving his/her consent) AND (Patient informed of the preliminary medical exam results) AND (Written consent signed) AND (at least 1 month) AND (atrial fibrillation) AND (cerebral) AND (falls) AND (gastrointestinal) AND (hemodialysis) AND (high) AND (new episode) AND (recurrent) AND (risk of bleeding) AND (severe bleeding) AND (type 3a, 3b, 3c) AND (years))"}
```
