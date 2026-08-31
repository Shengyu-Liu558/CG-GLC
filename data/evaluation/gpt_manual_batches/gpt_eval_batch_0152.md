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
{"candidate_id": "LLM03776", "doc_id": "NCT02939872_inc", "case_bucket": "or", "source_criterion": "Age 19 and more On dual or triple antiplatelet therapy and between 12months and 14months from Bioresorbable Vascular Scaffold implantation No history of death, serious myocardial infarction, stroke, repeat revascularization, or major bleeding", "candidate_expression": "((19 and more) AND (Age) AND (Bioresorbable Vascular Scaffold) AND (Bioresorbable Vascular Scaffold implantation) AND (No) AND (between 12months and 14months from Bioresorbable Vascular Scaffold implantation) AND (bleeding) AND (death) AND (dual antiplatelet therapy) AND (history) AND (implantation) AND (major) AND (myocardial infarction) AND (repeat) AND (revascularization) AND (serious) AND (stroke) AND (triple antiplatelet therapy))"}
{"candidate_id": "LLM03777", "doc_id": "NCT02219880_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03778", "doc_id": "NCT03177837_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((Comorbidities) AND (FEV1 <40% predicted) AND (FEV1/FVC <0.7) AND (cigarettes per day >20) AND (disease) AND (hypoxemia low altitude) AND (oxygen saturation room air <92% 750 m) AND (smoking heavy) AND ((COPD exacerbation) OR (COPD very severe)) AND ((OSA) OR (cardiovascular disease uncontrolled) OR (coronary artery disease) OR (pneumothorax in the last 2 months) OR (stroke previous) OR (systemic arterial hypertension unstable)) AND ((Internal) OR (neurologic) OR (psychiatric) OR (rheumatologic)) AND ((allergy) OR (renal failure)) AND ((acetazolamide) OR (other) OR (sulfonamides)))"}
{"candidate_id": "LLM03779", "doc_id": "NCT02222272_inc", "case_bucket": "or", "source_criterion": "All adult patients with chronic myeloid leukaemia in any phase (chronic, accelerated or blastic) who undergo allogeneic stem cell transplantation between 01/01/2010 and 30/09/2013 and have been previously treated with Nilotinib or Dasatinib, regardless of their response to these drugs.", "candidate_expression": "((Dasatinib) AND (Nilotinib) AND (accelerated) AND (adult) AND (allogeneic stem cell transplantation) AND (any phase) AND (between 01/01/2010 and 30/09/2013) AND (blastic) AND (chronic) AND (chronic myeloid leukaemia) AND (previously))"}
{"candidate_id": "LLM03780", "doc_id": "NCT03231982_exc", "case_bucket": "or", "source_criterion": "The difference in blood pressure between the selected arm versus non-selected arm is = 20 mmHg for siSBP and = 10 mmHg for siDBP at Visit 1 (screening). Blood pressure taken at screening and randomization is = 180 mmHg for siSBP or = 110 mmHg for siDBP. Diagnosed with secondary hypertension or suspected of secondary hypertension [e.g., renovascular disease, adrenal medullary and cortical hyperfunction, coarctation of the aorta, hyperaldosteronism, unilateral or bilateral renal artery stenosis, Cushing's syndrome, pheochromocytoma, polycystic kidney disease, etc.] Patients with symptomatic orthostatic hypertension (the difference in the blood pressures between measured at supine position and measured at standing position is = 20 mmHg for siSBP and = 10 mmHg for siDBP) Diagnosis of type 1 diabetes mellitus (DM) or uncontrolled DM (patients on insulin therapy or with HbA1c > 9%) Patients with severe cardiac conditions: heart failure (NYHA Class 3 or 4), history of ischemic cardiac disease (unstable angina, myocardial infarction), peripheral vascular diseases, percutaneous transluminal angioplasty or coronary artery bypass graft within recent 6 months. Patients with clinically significant ventricular tachycardia, atrial fibrillation, atrial flutter or other clinically significant arrhythmia at the discretion of the investigator Patients with hypertrophic occlusive myocardiopathy, severe occlusive coronary artery disease, aortic stenosis, hemodynamically significant aortic valve or mitral valve stenosis History of cardiogenic shock Presence of severe cerebrovascular disorders (diagnosis of stroke, cerebral infarction or cerebral hemorrhage within recent 6 months) History or current evidence of wasting, autoimmune (such as rheumatoid arthritis and systemic lupus erythematosus) or connective tissue diseases Known diagnosis of moderate or malignant retinopathy (including retinal hemorrhage, visual disturbance and retinal microaneurysm within 6 months) Patients with surgical or medical intestinal diseases or having received surgeries that could interfere with drug absorption distribution, metabolism and elimination History of malignancy including leukemia and lymphoma within recent 5 years except for localized basal cell carcinoma of the skin) Patients with any inflammatory diseases requiring chronic anti-inflammatory therapy Renal failure on dialysis AST or ALT >2 x upper limit of normal (ULN) Serum creatinine > 1.5 x ULN Serum potassium < 3.5 mmol/L or >5.5 mmol/L Needs for co-administration of non-study antihypertensive agents or contraindicated medications during the study History of hypersensitivity to ARBs or dihydropyridines History of angioedema to treatment with ACE inhibitors or ARBs Pregnant or lactating women and female volunteers of childbearing potential (except for women who are surgically sterile) who are not willing to use an adequate method of contraception (oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening. History of drug or alcohol abuse within recent 1 year Patients having received any other investigational product within recent 12 weeks Conditions which render a subject ineligible for the study at the discretion of the investigator", "candidate_expression": "(((oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening.) AND (Blood pressure at randomization at screening) AND (NYHA Class 3 or 4) AND (Renal failure) AND (Serum creatinine > 1.5 x ULN) AND (Serum potassium) AND (adequate method of contraception willing to) AND (angioedema History of) AND (anti-inflammatory therapy) AND (anti-inflammatory therapy chronic) AND (arrhythmia clinically significant) AND (cardiac conditions severe) AND (cardiogenic shock History) AND (cerebrovascular disorders severe) AND (childbearing potential) AND (dialysis) AND (difference in blood pressure selected arm versus non-selected arm at Visit 1) AND (difference in the blood pressures measured at supine position and measured at standing position) AND (hypersensitivity History of) AND (inflammatory diseases) AND (malignancy History of within recent 5 years) AND (orthostatic hypertension symptomatic) AND (other investigational product within recent 12 weeks) AND (retinopathy) AND (siDBP = 10 mmHg) AND (siSBP = 20 mmHg) AND (treatment) AND NOT (localized basal cell carcinoma of the skin) AND ((malignant) OR (moderate)) AND ((retinal hemorrhage) OR (retinal microaneurysm) OR (visual disturbance)) AND ((intestinal diseases) OR (surgeries)) AND ((medical) OR (surgical)) AND ((could interfere with drug absorption distribution) OR (could interfere with drug elimination) OR (could interfere with drug metabolism)) AND ((leukemia) OR (lymphoma)) AND ((siDBP = 110 mmHg) OR (siSBP = 180 mmHg)) AND ((ALT) OR (AST)) AND ((< 3.5 mmol/L) OR (>5.5 mmol/L)) AND ((antihypertensive agents co-administration during the study non-study) OR (contraindicated medications co-administration during the study)) AND ((ARBs) OR (dihydropyridines)) AND ((ACE inhibitors) OR (ARBs)) AND ((hypertension secondary) OR (hypertension suspected secondary)) AND ((Pregnant) OR (lactating)) AND ((female) OR (women)) AND ((alcohol abuse) OR (drug abuse)) AND ((bilateral) OR (unilateral)) AND ((Cushing's syndrome) OR (adrenal medullary hyperfunction) OR (coarctation of the aorta) OR (cortical hyperfunction) OR (hyperaldosteronism) OR (pheochromocytoma) OR (polycystic kidney disease) OR (renal artery stenosis) OR (renovascular disease)) AND ((DM uncontrolled) OR (type 1 diabetes mellitus (DM))) AND ((HbA1c > 9%) OR (insulin therapy)) AND ((heart failure) OR (ischemic cardiac disease history)) AND ((myocardial infarction) OR (peripheral vascular diseases) OR (unstable angina)) AND ((coronary artery bypass graft) OR (percutaneous transluminal angioplasty)) AND ((atrial fibrillation) OR (atrial flutter) OR (ventricular tachycardia)) AND ((aortic stenosis) OR (hypertrophic occlusive myocardiopathy) OR (occlusive coronary artery disease severe)) AND ((aortic valve stenosis) OR (mitral valve stenosis)) AND ((cerebral hemorrhage) OR (cerebral infarction) OR (stroke)) AND ((History) OR (current)) AND ((autoimmune diseases) OR (connective tissue diseases) OR (wasting)) AND ((rheumatoid arthritis) OR (systemic lupus erythematosus)))"}
{"candidate_id": "LLM03781", "doc_id": "NCT02647788_exc", "case_bucket": "or", "source_criterion": "ASA> 3; Coagulopathy; Renal disease, Liver disease, History of recent gastro-intestinal bleeding Pregnancy. Diagnosis of chronic pain currently taking opioid pain medication or with a history of drug abuse. Patients with a self-described allergy to ASA, acetaminophen, NSAIDS and codeine. All patients receiving a brachial plexus block for anesthesia and/or analgesia", "candidate_expression": "((> 3) AND (ASA) AND (Coagulopathy) AND (Liver disease) AND (NSAIDS) AND (Pregnancy) AND (Renal disease) AND (acetaminophen) AND (allergy) AND (brachial plexus block) AND (chronic pain) AND (codeine) AND (drug abuse) AND (gastro-intestinal bleeding) AND (history of) AND (opioid pain medication) AND (recent))"}
{"candidate_id": "LLM03782", "doc_id": "NCT02312960_exc", "case_bucket": "other", "source_criterion": "Not applicable to this follow up study", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03783", "doc_id": "NCT02314559_inc", "case_bucket": "other", "source_criterion": "All patients subjected to deep sedation in ambulant care, having a colonoscopy ASA 1-3", "candidate_expression": "((ASA 1-3) AND (ambulant) AND (colonoscopy) AND (deep sedation))"}
{"candidate_id": "LLM03784", "doc_id": "NCT02535299_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes mellitus,presence of autoimmune diabetes indicated by antibodies to insulin, islet cells, and GAD; Gestational diabetes; patients with heart, liver, or renal function impairment;presence of severe infections or cerebrovascular disease;", "candidate_expression": "((Gestational diabetes) AND (Type 1 diabetes mellitus) AND (antibodies) AND (autoimmune diabetes) AND ((heart function impairment) OR (liver function impairment) OR (renal function impairment)) AND ((cerebrovascular disease) OR (infections)) AND ((GAD) OR (insulin) OR (islet cells)))"}
{"candidate_id": "LLM03785", "doc_id": "NCT02944292_inc", "case_bucket": "other", "source_criterion": "Age 18 years or older Mechanical ventilation IAP between 12 and 20 mmHg in at least two consecutive measurements within 1-12 h Spontaneous breathing activity of at least 6 breaths/minute RASS score between 0 and -4 Physician-led sedation (if sedated; as opposed to nurse-led protocol)", "candidate_expression": "((18 years or older) AND (Age) AND (IAP) AND (Mechanical ventilation) AND (Physician-led) AND (RASS score) AND (Spontaneous breathing activity) AND (as opposed to) AND (at least 6 breaths/minute) AND (at least two consecutive measurements) AND (between 0 and -4) AND (between 12 and 20 mmHg) AND (nurse-led protocol) AND (sedation) AND (within 1-12 h))"}
{"candidate_id": "LLM03786", "doc_id": "NCT02637076_exc", "case_bucket": "or", "source_criterion": "use of any sedative hypnotics, tranquilizers, anticonvulsants, antihistamines (except non-sedating), benzodiazepines, clonidine or any medication known to affect dopamine at start of baseline period significant unstable or uncontrolled medical/psychiatric disease significant history of head trauma/surgery or seizure disorder radiation exposure exceeding 20mSv in last 12 months pregnancy substance abuse/dependence (including alcohol) have sleep apnea, or are shift workers on a sodium-restricted diet has ever taken Xyrem / sodium oxybate / GHB at any time claustrophobia metal implants / objects in the body that may interfere with MRI succinic semialdehyde dehydrogenase deficiency", "candidate_expression": "((MRI) AND (alcohol) AND (at start of baseline period) AND (claustrophobia) AND (ever) AND (exceeding 20mSv) AND (except) AND (history) AND (in last 12 months) AND (may interfere with) AND (non-sedating) AND (pregnancy) AND (radiation exposure) AND (significant) AND (sodium-restricted diet) AND (succinic semialdehyde dehydrogenase deficiency) AND ((uncontrolled) OR (unstable)) AND ((medical disease) OR (psychiatric disease)) AND ((head surgery) OR (head trauma) OR (seizure disorder)) AND ((substance abuse) OR (substance dependence)) AND ((anticonvulsants) OR (antihistamines) OR (benzodiazepines) OR (clonidine) OR (medication known to affect dopamine) OR (sedative hypnotics) OR (tranquilizers)) AND ((shift workers) OR (sleep apnea)) AND ((GHB) OR (Xyrem) OR (sodium oxybate)) AND ((metal implants) OR (metal objects)))"}
{"candidate_id": "LLM03787", "doc_id": "NCT03323047_exc", "case_bucket": "or", "source_criterion": "Patients Level III or greater on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) Patients with chronic conditions that would limit our ability to develop the study according to objectives, such as neurodevelopmental conditions preventing patients from understanding the Oucher tool Hepatic or renal disease cardiac disease active infection diabetes mellitus sickle cell disease known coagulation disorders pre- operative treatment with anti-emetics, steroids, or analgesics Acetaminophen allergy or already receiving acetaminophen within 24 h of surgery Complicating health factors precluding the use of opioids or acetaminophen any other factors which would interfere with pain assessment and management Patients weighing more than 30 kg that would exceed maximum dexamethasone dose Patients who live without a home telephone patient living without parental supervision.", "candidate_expression": "((Acetaminophen) AND (American Society of Anesthesiologists (ASA) physical status Level III or greater) AND (Complicating health factors) AND (cardiac disease) AND (chronic conditions limit our ability to develop the study according to objectives) AND (coagulation disorders) AND (diabetes mellitus) AND (infection active) AND (interfere) AND (neurodevelopmental conditions) AND (other factors) AND (precluding) AND (preventing understanding the Oucher tool) AND (sickle cell disease) AND (treatment pre- operative) AND (weighing more than 30 kg) AND ((Hepatic disease) OR (renal disease)) AND ((analgesics) OR (anti-emetics) OR (steroids)) AND ((acetaminophen within 24 h of surgery) OR (allergy)) AND ((acetaminophen) OR (opioids)) AND ((management) OR (pain assessment)))"}
{"candidate_id": "LLM03788", "doc_id": "NCT03350659_exc", "case_bucket": "or", "source_criterion": "Drug-induced hypotension, if necessary, evaluate patient after discontinuing the causative drug for one month Heart failure or Chronic renal failure Severe supine hypertension (Systolic Blood Pressure >180 or Diastolic Blood Pressure>110mmHg) Pregnant women, breast-feeding Unable to perform questionnaire", "candidate_expression": "((Chronic renal failure) AND (Diastolic Blood Pressure >110mmHg) AND (Heart failure) AND (Pregnant) AND (Systolic Blood Pressure >180) AND (Unable to perform questionnaire) AND (breast-feeding) AND (hypotension Drug-induced) AND (supine hypertension Severe) AND (women))"}
{"candidate_id": "LLM03789", "doc_id": "NCT02565277_inc", "case_bucket": "other", "source_criterion": "Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) Age 18 years or older Undergoing major cardiac surgery using cardiopulmonary bypass", "candidate_expression": "((Age 18 years or older) AND (Subjects who the investigator believes can and will comply with the requirements of the protocol (i.e. return for follow-up visits, and able to converse with study personnel) AND (cardiopulmonary bypass) AND (major cardiac surgery))"}
{"candidate_id": "LLM03790", "doc_id": "NCT03620526_inc", "case_bucket": "or", "source_criterion": "presence of typical HF symptoms and signs LV ejection fraction = 50 elevated levels of NT-proBNP (at least >125 pg/ml) echocardiographic structural (a left atrial volume index > 34 mL/m2 or a left ventricular mass index =115 g/m2 for males and =95 g/m2 for females) or functional alterations (E/e'=13 and a mean e' septal and lateral wall < 9 cm/s).", "candidate_expression": "((E/e' =13) AND (HF signs) AND (HF symptoms) AND (LV ejection fraction = 50) AND (NT-proBNP elevated at least >125 pg/ml) AND (echocardiographic structural) AND (females) AND (functional alterations) AND (left atrial volume inde > 34 mL/m2) AND (left ventricular mass index =115 g/m2) AND (left ventricular mass index =95 g/m2) AND (males) AND (mean e' septal and lateral wall < 9 cm/s))"}
{"candidate_id": "LLM03791", "doc_id": "NCT02754583_inc", "case_bucket": "other", "source_criterion": "Community in a school district that is within the study area Area within each school district that is in need of a well", "candidate_expression": "((school district that is in need of a well) AND (school district that is within the study area))"}
{"candidate_id": "LLM03792", "doc_id": "NCT02162433_inc", "case_bucket": "or", "source_criterion": "Patients between 3 to 16 years of age undergoing adenotonsillectomy, with or without myringotomy or myringoplasty ASA 1 & 2", "candidate_expression": "((1 & 2) AND (ASA) AND (adenotonsillectomy) AND (age) AND (between 3 to 16 years) AND (undergoing) AND ((myringoplasty) OR (myringotomy)))"}
{"candidate_id": "LLM03793", "doc_id": "NCT02983214_inc", "case_bucket": "other", "source_criterion": "Patients aged =50 years with DM2 and symptomatic PAD diagnosed clinically (according to Fontaine criteria, stage IIa or IIb and III) and by measuring the <U+0391><U+0392><U+0399>.", "candidate_expression": "((=50 years) AND (DM2) AND (Fontaine criteria) AND (PAD) AND (aged) AND (stage IIa or IIb and III) AND (symptomatic))"}
{"candidate_id": "LLM03794", "doc_id": "NCT03016741_inc", "case_bucket": "or", "source_criterion": "Have diagnosis of prostate cancer and have received treatment with GnRH agonist or antagonist therapy for at least 1 month prior to enrollment. Willing and able to complete survey questionnaires in English without assistance through the duration of the study. This stipulation is in place because not all of the proposed quality of life or cognitive tests are available or validated in other languages. Age = 18 years. Ability to understand and the willingness to sign a written informed consent document written in English that is approved by an institutional review board. Have either newly diagnosed metastatic hormone sensitive prostate cancer (mHSPC) or castration-resistant metastatic prostate cancer (mCRPC) and eligible to undergo treatment with abiraterone acetate (mHSPC or mCRPC) or enzalutamide (mCRPC) Patients may have received the following prior AR directed therapy prior to enrollment: bicalutamide, ketoconazole. Prior to enrollment, patients may have received treatment with abiraterone acetate or enzalutamide for no more than 14 days before completing baseline studies. Patients may have received chemotherapy for hormone-sensitive metastatic prostate cancer only, but it must not have lasted for more than 6 months. At least 12 months must have elapsed since completion of chemotherapy. Patients may have received prior definitive radiation therapy or surgery. At least 60 days must have elapsed since completion of definitive radiation therapy or surgery and patient must have only grade 2 or less adverse effects at the time of registration. Enrollment during palliative radiation of = 10 days, or radiation of = 10 days during the duration of the study is allowed. Patients must be able to take oral medication.", "candidate_expression": "((= 18 years) AND (Age) AND (At least 12 months must have elapsed since completion of chemotherapy) AND (At least 60 days must have elapsed since completion of definitive radiation therapy or surgery) AND (abiraterone acetate) AND (adverse effects) AND (at the time of registration) AND (castration-resistant) AND (chemotherapy) AND (completion of chemotherapy) AND (completion of definitive radiation therapy or surgery) AND (definitive) AND (enzalutamide) AND (for at least 1 month) AND (grade 2 or less) AND (hormone sensitive) AND (hormone-sensitive) AND (lasted for more than 6 months) AND (mCRPC) AND (mHSPC) AND (metastatic) AND (not) AND (prior) AND (prior to enrollment) AND (prostate cancer) AND (treatment) AND ((GnRH agonist) OR (GnRH antagonist)) AND ((mCRPC) OR (mHSPC)) AND ((radiation therapy) OR (surgery)))"}
{"candidate_id": "LLM03795", "doc_id": "NCT03335436_inc", "case_bucket": "other", "source_criterion": "singleton, term pregnancy currently on buprenorphine maintenance therapy scheduled for elective CD under spinal anesthesia", "candidate_expression": "((CD scheduled for elective) AND (buprenorphine) AND (buprenorphine maintenance therapy currently) AND (pregnancy singleton term) AND (spinal anesthesia))"}
{"candidate_id": "LLM03796", "doc_id": "NCT03171987_exc", "case_bucket": "or", "source_criterion": "Known or suspected serious spinal pathology and spinal implants Lumbar spinal surgery within the preceding six months Serious comorbidities preventing prescription of paracetamol Alternative treatment for low back pain in previous two weeks Chronic neurological lesion Chronic musculoskeletal lesion Active cancer Pregnancy Use of pain medication (except paracetamol) within 3 days Treatment site has active skin lesion or inflammation Known allergy to skin patch", "candidate_expression": "((Chronic musculoskeletal lesion) AND (Chronic neurological lesion) AND (Lumbar spinal surgery within the preceding six months) AND (Pregnancy) AND (allergy) AND (cancer Active) AND (comorbidities Serious) AND (low back pain in previous two weeks) AND (pain medication within 3 days) AND (paracetamol) AND (preventing) AND (skin patch) AND (treatment Alternative) AND NOT (paracetamol) AND ((spinal implants) OR (spinal pathology serious)) AND ((inflammation) OR (skin lesion)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM03797", "doc_id": "NCT02145026_exc", "case_bucket": "or", "source_criterion": "Contraindications and/or known hypersensitivity to the active substance and/or any of the excipients of epoetin beta treatment Poorly controlled hypertension as assessed by the investigator History of Acute Myeloid Leukemia (AML) or high risk for AML Administration of another investigational drug within 1 month before screening or planned during the study period Previously documented evidence of Pure Red Cell Aplasia (PRCA)", "candidate_expression": "((AML) AND (Administration of another investigational drug within 1 month before screening or planned during the study period) AND (PRCA) AND (Pure Red Cell Aplasia) AND (epoetin beta treatment) AND (hypertension Poorly controlled) AND ((Contraindications) OR (hypersensitivity)) AND ((Acute Myeloid Leukemia) OR (risk for AML high)))"}
{"candidate_id": "LLM03798", "doc_id": "NCT03046108_inc", "case_bucket": "other", "source_criterion": "Clinical suspicion of Morton neuroma confirmed in ultrasound scan Symptoms present more than six months The thickness of the nerve must be at least 2 mm in short axis and at least 5 mm in the longitudinal axis.", "candidate_expression": "((Morton neuroma Clinical suspicion) AND (Symptoms more than six months) AND (thickness of the nerve in short axis at least 2 mm) AND (thickness of the nerve in the longitudinal axis at least 5 mm) AND (ultrasound scan))"}
{"candidate_id": "LLM03799", "doc_id": "NCT02386800_inc", "case_bucket": "other", "source_criterion": "Patient is currently enrolled in a Novartis OGD or GMA-sponsored or Incyte-sponsored clinical study (where Incyte can delegate the sponsorship to a preferred CRO, if applicable) that is approved to enroll into this rollover study, is receiving ruxolitinib and has fulfilled all of the requirements of the parent protocol. Patient is currently benefiting from the treatment with ruxolitinib, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Patient currently has no evidence of progressive disease, as determined by the investigator, following previous treatment with ruxolitinib Written informed consent obtained prior to enrolling in roll-over study and receiving study medication. If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness.", "candidate_expression": "((Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures) AND (Patient is currently enrolled in a Novartis OGD or GMA-sponsored or Incyte-sponsored clinical study (where Incyte can delegate the sponsorship to a preferred CRO, if applicable) that is approved to enroll into this rollover study, is receiving ruxolitinib and has fulfilled all of the requirements of the parent protocol.) AND (Written informed consent obtained prior to enrolling in roll-over study and receiving study medication. If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness) AND (progressive disease) AND (ruxolitinib))"}
{"candidate_id": "LLM03800", "doc_id": "NCT01911650_inc", "case_bucket": "or", "source_criterion": "1. age 18-65 years, inclusive 2. diagnosis of moderate to severe AT, confirmed by Dr. Wilson using clinical symptoms and exam findings consistent with chronic AT (>6 month duration) - which includes pain while palpating the intratendinous swelling part of the Achilles tendon and relief of pain when tendon placed under tension - and pre-procedure US 3. self-reported AT-related pain for at least 6 months and VAS (Visual Analog Scale) pain >5 (0-10 scale) 4. self-reported failure of eccentric exercise protocol (at least 75% completion) 5. self-reported failure of at least 2 of the 3 most common treatments for AT (NSAIDS, rest/ice or taping) 6. patient considered surgery but decided to wait and/or refused surgery -", "candidate_expression": "((0-10 scale) AND (18-65 years, inclusive) AND (>5) AND (>6 month duration) AND (AT) AND (AT-related pain) AND (VAS (Visual Analog Scale) pain) AND (age) AND (at least 75%) AND (chronic AT) AND (failure of at least 2 of the 3 most common treatments for AT) AND (failure of eccentric exercise protocol) AND (for at least 6 months) AND (moderate to severe) AND (pain while palpating the intratendinous swelling part of the Achilles tendon) AND (relief of pain when tendon placed under tension) AND (self-reported) AND (surgery) AND ((NSAIDS) OR (ice) OR (rest) OR (taping)))"}
```
