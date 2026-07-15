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
{"candidate_id": "LLM00176", "doc_id": "NCT02415257_exc", "case_bucket": "other", "source_criterion": "impaired decision making neurofibromatosis signs for central dysfunction remaining vestibular function Patients are advised not to participate in the gentamicin arm if hearing is better than 30 deciBel (dB) in pure tone average (500, 1000, 2000, 3-4000 Hz) and speech discrimination better than 70% the neurosurgeon aim at hearing preservation surgery and do not want to risk gentamicin associated hearing loss", "candidate_expression": "((500, 1000, 2000, 3-4000 Hz) AND (better than 30 deciBel (dB)) AND (better than 70%) AND (central dysfunction) AND (hearing) AND (impaired decision making) AND (neurofibromatosis) AND (pure tone average) AND (remaining vestibular function) AND (signs) AND (speech discrimination))"}
{"candidate_id": "LLM00177", "doc_id": "NCT03231982_exc", "case_bucket": "or", "source_criterion": "The difference in blood pressure between the selected arm versus non-selected arm is = 20 mmHg for siSBP and = 10 mmHg for siDBP at Visit 1 (screening). Blood pressure taken at screening and randomization is = 180 mmHg for siSBP or = 110 mmHg for siDBP. Diagnosed with secondary hypertension or suspected of secondary hypertension [e.g., renovascular disease, adrenal medullary and cortical hyperfunction, coarctation of the aorta, hyperaldosteronism, unilateral or bilateral renal artery stenosis, Cushing's syndrome, pheochromocytoma, polycystic kidney disease, etc.] Patients with symptomatic orthostatic hypertension (the difference in the blood pressures between measured at supine position and measured at standing position is = 20 mmHg for siSBP and = 10 mmHg for siDBP) Diagnosis of type 1 diabetes mellitus (DM) or uncontrolled DM (patients on insulin therapy or with HbA1c > 9%) Patients with severe cardiac conditions: heart failure (NYHA Class 3 or 4), history of ischemic cardiac disease (unstable angina, myocardial infarction), peripheral vascular diseases, percutaneous transluminal angioplasty or coronary artery bypass graft within recent 6 months. Patients with clinically significant ventricular tachycardia, atrial fibrillation, atrial flutter or other clinically significant arrhythmia at the discretion of the investigator Patients with hypertrophic occlusive myocardiopathy, severe occlusive coronary artery disease, aortic stenosis, hemodynamically significant aortic valve or mitral valve stenosis History of cardiogenic shock Presence of severe cerebrovascular disorders (diagnosis of stroke, cerebral infarction or cerebral hemorrhage within recent 6 months) History or current evidence of wasting, autoimmune (such as rheumatoid arthritis and systemic lupus erythematosus) or connective tissue diseases Known diagnosis of moderate or malignant retinopathy (including retinal hemorrhage, visual disturbance and retinal microaneurysm within 6 months) Patients with surgical or medical intestinal diseases or having received surgeries that could interfere with drug absorption distribution, metabolism and elimination History of malignancy including leukemia and lymphoma within recent 5 years except for localized basal cell carcinoma of the skin) Patients with any inflammatory diseases requiring chronic anti-inflammatory therapy Renal failure on dialysis AST or ALT >2 x upper limit of normal (ULN) Serum creatinine > 1.5 x ULN Serum potassium < 3.5 mmol/L or >5.5 mmol/L Needs for co-administration of non-study antihypertensive agents or contraindicated medications during the study History of hypersensitivity to ARBs or dihydropyridines History of angioedema to treatment with ACE inhibitors or ARBs Pregnant or lactating women and female volunteers of childbearing potential (except for women who are surgically sterile) who are not willing to use an adequate method of contraception (oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening. History of drug or alcohol abuse within recent 1 year Patients having received any other investigational product within recent 12 weeks Conditions which render a subject ineligible for the study at the discretion of the investigator", "candidate_expression": "(((oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening.) AND (< 3.5 mmol/L) AND (= 10 mmHg) AND (= 110 mmHg) AND (= 180 mmHg) AND (= 20 mmHg) AND (> 1.5 x ULN) AND (> 9%) AND (>2 x upper limit of normal (ULN)) AND (>5.5 mmol/L) AND (ACE inhibitors) AND (ALT) AND (ARBs) AND (AST) AND (Blood pressure) AND (Class 3 or 4) AND (Cushing's syndrome) AND (DM) AND (HbA1c) AND (History) AND (History of) AND (NYHA) AND (Pregnant) AND (Renal failure) AND (Serum creatinine) AND (Serum potassium) AND (adequate method of contraception) AND (adrenal medullary hyperfunction) AND (alcohol abuse) AND (angioedema) AND (anti-inflammatory therapy) AND (antihypertensive agents) AND (aortic stenosis) AND (aortic valve stenosis) AND (arrhythmia) AND (at Visit 1) AND (at randomization) AND (at screening) AND (atrial fibrillation) AND (atrial flutter) AND (autoimmune diseases) AND (bilateral) AND (cardiac conditions) AND (cardiogenic shock) AND (cerebral hemorrhage) AND (cerebral infarction) AND (cerebrovascular disorders) AND (childbearing potential) AND (chronic) AND (clinically significant) AND (co-administration during the study) AND (coarctation of the aorta) AND (connective tissue diseases) AND (contraindicated medications) AND (coronary artery bypass graft) AND (cortical hyperfunction) AND (could interfere with drug absorption distribution) AND (could interfere with drug elimination) AND (could interfere with drug metabolism) AND (current) AND (dialysis) AND (difference in blood pressure) AND (difference in the blood pressures) AND (dihydropyridines) AND (drug abuse) AND (except for) AND (female) AND (heart failure) AND (hemodynamically significant) AND (history) AND (hyperaldosteronism) AND (hypersensitivity) AND (hypertension) AND (hypertrophic occlusive myocardiopathy) AND (inflammatory diseases) AND (insulin therapy) AND (intestinal diseases) AND (ischemic cardiac disease) AND (lactating) AND (leukemia) AND (localized basal cell carcinoma of the skin) AND (lymphoma) AND (malignancy) AND (malignant) AND (measured at supine position and measured at standing position) AND (medical) AND (mitral valve stenosis) AND (moderate) AND (myocardial infarction) AND (non-study) AND (not) AND (occlusive coronary artery disease) AND (orthostatic hypertension) AND (other investigational product) AND (percutaneous transluminal angioplasty) AND (peripheral vascular diseases) AND (pheochromocytoma) AND (polycystic kidney disease) AND (renal artery stenosis) AND (renovascular disease) AND (retinal hemorrhage) AND (retinal microaneurysm) AND (retinopathy) AND (rheumatoid arthritis) AND (secondary) AND (selected arm versus non-selected arm) AND (severe) AND (siDBP) AND (siSBP) AND (stroke) AND (surgeries) AND (surgical) AND (suspected) AND (symptomatic) AND (systemic lupus erythematosus) AND (treatment) AND (type 1 diabetes mellitus (DM)) AND (uncontrolled) AND (unilateral) AND (unstable angina) AND (ventricular tachycardia) AND (visual disturbance) AND (wasting) AND (willing to) AND (within 6 months) AND (within recent 1 year) AND (within recent 12 weeks) AND (within recent 5 years) AND (within recent 6 months) AND (women))"}
{"candidate_id": "LLM00178", "doc_id": "NCT02256943_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((Alcohol abuse) AND (CYP3A inducers) AND (CYP3A inhibitors) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Healthy) AND (Heart disease) AND (Male) AND (Metabolic Equivalents >7) AND (Neurological disease) AND (Obstructive uropathy) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction Suspicion tested sites) AND (tested drugs) AND (treatment Ongoing))"}
{"candidate_id": "LLM00179", "doc_id": "NCT03493919_inc", "case_bucket": "or", "source_criterion": "Subjects who, in the opinion of the investigator, can and will comply with the requirements of the protocol. Written informed consent obtained from the subject prior to performing any study specific procedure. A male or female between, and including, 18 and 50 years of age at the time of the first study visit. Healthy subjects as established by medical history and clinical examination before entering into the study. Healthy subjects with no medical conditions that, in the opinion of the investigator, prevents the subject from participating in the study. Subjects must weigh at least 110 pounds (50 kg), but not to present obesity (BMI < 32kg/m2). Female subjects of non-childbearing potential may be enrolled in the study. Non-childbearing potential is defined as pre-menarche, current bilateral tubal ligation or occlusion, hysterectomy, bilateral ovariectomy or post-menopause. has practiced adequate contraception for 30 days prior to vaccination, and has a negative pregnancy test on the day of vaccination and has agreed to continue adequate contraception during the entire treatment period and for 1 month, after completion of the vaccination series.", "candidate_expression": "((BMI < 32kg/m2) AND (Female) AND (Healthy medical history before entering into the study) AND (Written informed consent prior to performing any study specific procedure) AND (adequate contraception continue during the entire treatment period for 1 month, after completion of the vaccination series) AND (age 18 and 50 years at the time of the first study visit) AND (bilateral ovariectomy) AND (bilateral tubal ligation) AND (bilateral tubal occlusion) AND (clinical examination) AND (comply with the requirements of the protocol) AND (contraception adequate 30 days prior to vaccination) AND (female) AND (hysterectomy) AND (male) AND (post-menopause) AND (pre-menarche) AND (pregnancy test negative on the day of vaccination) AND (study specific procedure) AND (weigh at least 110 pounds at least 50 kg) AND NOT (obesity) AND NOT (childbearing potential))"}
{"candidate_id": "LLM00180", "doc_id": "NCT02664558_inc", "case_bucket": "or", "source_criterion": "1. Male or female, 18-75 years old. 2. Has a diagnosis of WHO Group 1 PAH. 3. Right heart catheterization performed at Screening with results that are: 1. Mean pulmonary arterial pressure ≥25 mmHg (at rest) and 2. Pulmonary venous hypertension (measured as pulmonary capillary wedge pressure (PCWP) ≤15 mmHg. If PCWP is not available, then mean left atrial pressure or left ventricular end-diastolic pressure ≤15 mmHg in the absence of left atrial obstruction. and 3. Pulmonary vascular resistance (PVR) ≥300 dyn•s/cm5 (3.75 Wood units) 4. Has WHO/NYHA-FC of II or III. 5. Be on stable dose of at least one of the following PAH-specific therapies: endothelin receptor antagonist, an agent acting on the nitric oxide pathway (phosphodiesterase type 5 inhibitor or soluble guanylate cyclase stimulator), and/or a prostacyclin or prostacyclin analog. 6. Has a 6-minute walk distance that is ≥150 and ≤500 meters. 7. Have a ventilation-perfusion scan that rules out thromboembolic disease.", "candidate_expression": "((6-minute walk distance ≥150 and ≤500 meters) AND (Male) AND (Mean pulmonary arterial pressure ≥25 mmHg at rest) AND (PAH) AND (PAH-specific therapies stable dose at least one) AND (Pulmonary vascular resistance (PVR) ≥300 dyn•s/cm5 3.75 Wood units) AND (Pulmonary venous hypertension) AND (Right heart catheterization performed at Screening) AND (WHO Group 1) AND (WHO/NYHA-FC II III) AND (agent acting on the nitric oxide pathway) AND (endothelin receptor antagonist) AND (female) AND (left ventricular end-diastolic pressure ≤15 mmHg) AND (mean left atrial pressure ≤15 mmHg) AND (phosphodiesterase type 5 inhibitor) AND (prostacyclin analog) AND (pulmonary capillary wedge pressure (PCWP) ≤15 mmHg) AND (soluble guanylate cyclase stimulator) AND (ventilation-perfusion scan) AND (years old 18-75 years) AND NOT (left atrial obstruction) AND NOT (thromboembolic disease))"}
{"candidate_id": "LLM00181", "doc_id": "NCT02867618_inc", "case_bucket": "or", "source_criterion": "Phase I: Patients must have histologically confirmed R/R NHL or HL (defined by WHO criteria). Patients with chronic lymphocytic leukemia (CLL) and small lymphocytic lymphoma (SLL) are eligible. In addition, patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL and HL will be eligible if there is no available standard therapy. Phase II: Patients must have histologically confirmed R/R NHL (as defined by WHO criteria). Patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL will be eligible if there is no available standard therapy. Must have received front line chemotherapy. No upper limit for the number of prior therapies Evaluable Disease in the Phase I, and measurable disease in the Phase II Age > 18 years ECOG performance status < 2 Patients must have adequate organ and marrow function Adequate Contraception Ability to understand and the willingness to sign a written informed consent document", "candidate_expression": "((< 2) AND (> 18 years) AND (Ability to understand and the willingness to sign a written informed consent document) AND (Adequate) AND (Age) AND (Contraception) AND (DLBCL) AND (Disease) AND (ECOG performance status) AND (Evaluable) AND (HL) AND (NHL) AND (R/R) AND (WHO criteria) AND (adequate) AND (at least 2) AND (chemotherapy) AND (chronic lymphocytic leukemia (CLL)) AND (confirmed) AND (diffuse large B cell lymphomas (DLBCL)) AND (front line) AND (histologically) AND (in the Phase I) AND (in the Phase II) AND (marrow function) AND (measurable) AND (no) AND (organ function) AND (other than) AND (prior) AND (small lymphocytic lymphoma (SLL)) AND (standard therapy) AND (therapies))"}
{"candidate_id": "LLM00182", "doc_id": "NCT03221231_inc", "case_bucket": "other", "source_criterion": "Current DSM-IV diagnosis of cannabis dependence, >1 week detoxified and abstinent; Able to provide written informed consent and to comply with study procedures. Dutch speaking (Dutch as primary language).", "candidate_expression": "((abstinent) AND (cannabis dependence DSM-IV) AND (detoxified))"}
{"candidate_id": "LLM00183", "doc_id": "NCT02106624_inc", "case_bucket": "or", "source_criterion": "need mechanical ventilation for more than 2 days mean blood pressure more than 60mmHg predicted ICU stay more than 7 days tolerance of parenteral or enteral nutrition", "candidate_expression": "((ICU) AND (mean blood pressure more than 60mmHg) AND (mechanical ventilation need for more than 2 days) AND (predicted ICU stay more than 7 days) AND (tolerance) AND ((enteral nutrition) OR (parenteral nutrition)))"}
{"candidate_id": "LLM00184", "doc_id": "NCT03537924_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((40-75 yrs) AND (Healthy) AND (Kyrgyz ethnicity) AND (Written informed consent.) AND (age) AND (any disease) AND (living at <800m) AND (living at low altitude) AND (medication) AND (men) AND (need of) AND (without) AND (women))"}
{"candidate_id": "LLM00185", "doc_id": "NCT03472846_inc", "case_bucket": "other", "source_criterion": "Postmenopausal women Age 60-80 years T-score according to DXA: <-2.5 indication for osteoporosis therapy according to international guidelines", "candidate_expression": "((60-80 years) AND (<-2.5) AND (Age) AND (DXA) AND (Postmenopausal) AND (T-score) AND (according to DXA) AND (indication for) AND (international guidelines) AND (osteoporosis) AND (osteoporosis therapy) AND (women))"}
{"candidate_id": "LLM00186", "doc_id": "NCT02443844_exc", "case_bucket": "other", "source_criterion": "Patients who have previous prostate surgery Patients who have muscle invasive bladder cancer", "candidate_expression": "((bladder cancer muscle invasive) AND (prostate surgery previous))"}
{"candidate_id": "LLM00187", "doc_id": "NCT02469610_inc", "case_bucket": "other", "source_criterion": "Thoracoscopic surgery candidate. Over 18 years old. No known allergy to Bupivacaine. Patient is able to read understand and singe an inform consent.", "candidate_expression": "((Bupivacaine) AND (Thoracoscopic surgery candidate) AND (able to read) AND (old Over 18 years old) AND (singe) AND (understand) AND NOT (allergy))"}
{"candidate_id": "LLM00188", "doc_id": "NCT02851303_exc", "case_bucket": "other", "source_criterion": "Born prior to 34 weeks Neonatal intensive care unit admission Serious medical comorbidities Primary substance exposure in-utero was buprenorphine, or was not opioids", "candidate_expression": "((Born prior to 34 weeks) AND (Neonatal intensive care unit) AND (medical comorbidities Serious) AND (substance exposure in-utero buprenorphine) AND NOT (opioids))"}
{"candidate_id": "LLM00189", "doc_id": "NCT02632318_inc", "case_bucket": "or", "source_criterion": "History of falls or dizziness at exit from bed in the morning (at least two incidents in the past year) At least 20/200 corrected visual acuity Stable health Normal hearing", "candidate_expression": "((At least 20/200) AND (Normal hearing) AND (Stable health) AND (at exit from bed in the morning) AND (at least two) AND (corrected visual acuity) AND (in the past year) AND (incidents) AND ((dizziness) OR (falls)))"}
{"candidate_id": "LLM00190", "doc_id": "NCT03015818_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Pregnancy Concurrent antibiotherapy Certain infectious endocarditis Concurrent anti-inflammatory therapy, including corticosteroid therapy", "candidate_expression": "((Certain) AND (Concurrent) AND (Inability to give informed consent) AND (Pregnancy) AND (anti-inflammatory) AND (anti-inflammatory therapy) AND (antibiotherapy) AND (corticosteroid) AND (corticosteroid therapy) AND (infectious endocarditis))"}
{"candidate_id": "LLM00191", "doc_id": "NCT02167022_inc", "case_bucket": "other", "source_criterion": "1. Age: 12 to 36 months of age (The diagnosis of CP is often uncertain under the age of 12 months. The cutoff at 36 months is to have a population of young children when the brain is most \"plastic\" and most susceptible to reorganization). 2. Diagnosis: Diagnosis of spastic CP confirmed by a pediatric neurologist or pediatric rehabilitation specialist. 3. Etiology: The insult to the central nervous system that caused the motor dysfunction must have occurred during gestation or within one year after birth independent of gestational age. 4. Disease severity level: Gross Motor Function Classification System (GMFCS) levels I, II and III.", "candidate_expression": "((12 to 36 months of age) AND (Age) AND (Gross Motor Function Classification System (GMFCS)) AND (levels I, II and III) AND (one year after birth) AND (spastic CP))"}
{"candidate_id": "LLM00192", "doc_id": "NCT03122119_inc", "case_bucket": "other", "source_criterion": "Diagnosis of sacroiliitis Age 18 to 80 years old Chronic low back pain SI joint pathology is the predominant source of pain Positive Fortin Finger Test (PMT) Joint anatomy is identifiable using ultrasonography Patient has no other comorbidities that contraindicate the procedure Patient has attempted physical therapy and corticosteroid injections with local anesthetic -Previous injections of lidocaine and corticosteroid provided at least minor immediate relief Patient must not have had a corticosteroid injection in the SI joint within the last three months Patient must consent to the procedure", "candidate_expression": "((18 to 80 years) AND (Age) AND (Chronic low back pain) AND (Fortin Finger Test (PMT)) AND (Positive) AND (SI joint) AND (SI joint pathology) AND (comorbidities that contraindicate the procedure) AND (consent to the procedure) AND (corticosteroid injection) AND (corticosteroid injections) AND (no) AND (not) AND (ocal anesthetic) AND (other) AND (physical therapy) AND (sacroiliitis) AND (within the last three months))"}
{"candidate_id": "LLM00193", "doc_id": "NCT02548013_exc", "case_bucket": "other", "source_criterion": "1. Patient with equivocal diagnosis of rupture of membranes 2. advanced labor 3. intrauterine infection 4. vaginal bleeding or 5. non reassuring fetal heart rate.", "candidate_expression": "((advanced labor) AND (fetal heart rate non reassuring) AND (intrauterine infection) AND (non reassuring) AND (vaginal bleeding) AND NOT (rupture of membranes))"}
{"candidate_id": "LLM00194", "doc_id": "NCT03530124_inc", "case_bucket": "other", "source_criterion": "=32 weeks gestational age at birth =6 weeks postnatal age at randomization Remains hospitalized after birth (has never been discharged home) Treating clinician deems infant eligible to receive 2-month vaccines English- or Spanish-speaking parent(s)/legally authorized representative(s) (LAR(s)) Not planned for discharge within 60 hours of study entry The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process", "candidate_expression": "((2-month vaccines eligible) AND (Not) AND (The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process) AND (discharge planned within 60 hours of study entry study entry) AND (gestational age at birth =32 weeks) AND (hospitalized after birth) AND (postnatal age =6 weeks at randomization))"}
{"candidate_id": "LLM00195", "doc_id": "NCT00527826_exc", "case_bucket": "or", "source_criterion": "Known other respiratory disorders or signs for other respiratory disorders (e.g. asthma, lung cancer, sarcoidosis, tuberculosis, lung fibrosis, cystic fibrosis, bronchoectasis). Known history of significant inflammatory disease, other than COPD (e.g. rheumatoid arthritis and systemic lupus erythematosus). Known to be severely alpha-1-antitrypsin deficient (PI SZ or ZZ) Having undergone lung surgery (e.g. lung resection including lung volume reduction surgery, lung transplant) or subjects scheduled for surgery. Concurrent medication from Visit 1 and for the duration of the study with any of the prohibited medications: monoamine oxidase inhibitors and tricyclic antidepressants, and ritonavir (a highly potent cytochrome P450 3A4 inhibitor). Subjects receiving chronic or prophylactic antibiotic therapy. Serious, uncontrolled disease (including serious psychological disorders) likely to interfere with the study or impact on subject safety. Have, in the opinion of the investigator, evidence of alcohol, drug or solvent abuse. History of depression. History or presence of clinically significant drug sensitivity or clinically significant allergic reaction to corticosteroids or salmeterol. Moderate or severe COPD exacerbation (requiring corticosteroids or increased dosage of corticosteroids and/or antibiotics or hospitalization) within the 4 weeks prior to Visit 1 Lower respiratory tract infection within the 4 weeks prior to Visit 1 . Pregnant or lactating female and female of childbearing potential. Subject is a participating investigator, sub-investigator, study coordinator, or other employee of a participating investigator, or is an immediate family member of the before mentioned. Subject is an employee of GlaxoSmithKline (GSK). Subject participated in an investigational drug study within 30 days prior to Visit 1", "candidate_expression": "((COPD) AND (COPD exacerbation) AND (History of) AND (Lower respiratory tract infection) AND (Visit 1) AND (alpha-1-antitrypsin deficient) AND (corticosteroids) AND (cytochrome P450 3A4 inhibitor) AND (depression) AND (female) AND (increased dosage) AND (inflammatory disease) AND (lung resection) AND (medication from Visit 1) AND (other than) AND (participated in an investigational drug study) AND (psychological disorders) AND (scheduled) AND (severely) AND (significant) AND (uncontrolled disease) AND (within 30 days prior to Visit 1) AND (within the 4 weeks prior to Visit 1) AND ((respiratory disorders) OR (signs for respiratory disorders)) AND ((rheumatoid arthritis) OR (systemic lupus erythematosus)) AND ((lung surgery) OR (surgery)) AND ((lung transplant) OR (lung volume reduction surgery)) AND ((monoamine oxidase inhibitors) OR (ritonavir) OR (tricyclic antidepressants)) AND ((asthma) OR (bronchoectasis) OR (cystic fibrosis) OR (lung cancer) OR (lung fibrosis) OR (sarcoidosis) OR (tuberculosis)) AND ((chronic antibiotic therapy) OR (prophylactic antibiotic therapy)) AND ((alcohol abuse) OR (drug abuse) OR (solvent abuse)) AND ((allergic reaction) OR (drug sensitivity)) AND ((corticosteroids) OR (salmeterol)) AND ((Moderate) OR (severe)) AND ((antibiotics) OR (corticosteroids) OR (hospitalization)) AND ((Pregnant) OR (childbearing potential) OR (lactating)))"}
{"candidate_id": "LLM00196", "doc_id": "NCT03344042_exc", "case_bucket": "scope", "source_criterion": "no consent known allergy to administered opioid contraindications to epidural analgesia coagulopathies including platelet count of less than 100,000 spine surgery in past", "candidate_expression": "((allergy) AND (coagulopathies) AND (contraindications) AND (epidural analgesia) AND (no consent) AND (opioid) AND (platelet count less than 100,000) AND (spine surgery in past))"}
{"candidate_id": "LLM00197", "doc_id": "NCT02984475_inc", "case_bucket": "scope", "source_criterion": "Diagnosed with Beta-Thalassemia Major and receiving regular blood transfusion and on iron chelating therapy. Weight: equal to or over 35 kg. Normal renal function.", "candidate_expression": "((Beta-Thalassemia Major) AND (Normal) AND (Weight) AND (blood transfusion) AND (equal to or over 35 kg) AND (iron chelating therapy) AND (regular) AND (renal function))"}
{"candidate_id": "LLM00198", "doc_id": "NCT01440296_inc", "case_bucket": "or", "source_criterion": "male and female patients over the age of 18 years. written informed consent (approved by the Institutional Review Board [IRB]/Independent Ethics Committee [IEC]) obtained prior to any study specific procedures. patient with mild to severe carotid artery disease", "candidate_expression": "((age over 18 years) AND (carotid artery disease mild severe) AND (female) AND (male))"}
{"candidate_id": "LLM00199", "doc_id": "NCT02208739_exc", "case_bucket": "or", "source_criterion": "Patients who had history of systemic antibiotic usage over the previous 4 months Patients who were pregnant Patients who had received non-surgical periodontal treatment within the past 6 months Patients who had received surgical periodontal treatment within the past 12 months Patients who were smokers Patients with a history of stroke or an acute cardiovascular event over the previous 12 months.", "candidate_expression": "((history) AND (non-surgical periodontal treatment) AND (over the previous 12 months) AND (over the previous 4 months) AND (pregnant) AND (smokers) AND (surgical periodontal treatment) AND (systemic antibiotic) AND (within the past 12 months) AND (within the past 6 months) AND ((acute cardiovascular event) OR (stroke)))"}
{"candidate_id": "LLM00200", "doc_id": "NCT03333655_exc", "case_bucket": "or", "source_criterion": "Participants taking CPI combination therapies with chemotherapy are not permitted. Pregnant, lactating, or intending to become pregnant during the study.", "candidate_expression": "((CPI combination therapies) AND (Pregnant) AND (chemotherapy) AND (during the study) AND (intending to become) AND (lactating) AND (pregnant))"}
```
