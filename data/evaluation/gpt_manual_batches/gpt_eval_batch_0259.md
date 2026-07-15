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
{"candidate_id": "LLM06451", "doc_id": "NCT02902120_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age at the time of screening Have stable renal function for one month (30 days) prior to enrollment Have Chronic HCV infection prior to transplantation with documented HCV viremia = 1,000 IU/ml at screening and either documented HCV Ab positivity or HCV viremia = 1,000 IU/ml at least 6 months prior to enrollment. Documented genotype 1 HCV infection prior to enrollment and after their transplant in the post-transplantation cohort HCV disease staging within 12 months prior to enrollment by liver biopsy, transient elastography, or biochemical testing Be able to give informed consent and comply with study guidelines Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment. On the transplant waiting list followed by the University of Maryland's nephrology clinic or the Baltimore VA's nephrology clinic On chronic hemodialysis not yet on the transplant list and followed in the University's hemodialysis center or in the University's nephrology clinic Have chronic kidney disease with GFR <50", "candidate_expression": "((Be able to give informed consent and comply with study guidelines) AND (Chronic HCV infection prior to transplantation) AND (GFR <50) AND (HCV infection genotype 1 prior to enrollment after their transplant i) AND (HCV viremia = 1,000 IU/ml) AND (Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment.) AND (age At least 18 years) AND (chronic kidney disease) AND (disease staging HCV within 12 months prior to enrollment) AND (hemodialysis chronic) AND (renal function stable one month (30 days) prior to enrollment) AND ((HCV Ab positivity) OR (HCV viremia = 1,000 IU/ml)) AND ((biochemical testing) OR (liver biopsy) OR (transient elastography)))"}
{"candidate_id": "LLM06452", "doc_id": "NCT02200978_exc", "case_bucket": "or", "source_criterion": "Patients who have coma, convulsion or paralysis due to intracranial hemorrhage or central nervous system leukemia at diagnosis.", "candidate_expression": "((at diagnosis) AND (central nervous system) AND ((coma) OR (convulsion) OR (paralysis)) AND ((intracranial hemorrhage) OR (leukemia)))"}
{"candidate_id": "LLM06453", "doc_id": "NCT00391690_exc", "case_bucket": "or", "source_criterion": "Prior treatment with a bisphosphonate Abnormal renal function as evidenced by a calculated creatinine clearance < 30 ml/minute. Corrected (adjusted for serum albumin) serum calcium concentration < 8.0 mg/dl (2.00 mmol/L) or ≥ 12.0 mg/dl (3.00 mmol/L). Patients with clinically symptomatic brain metastases History of diseases with influence on bone metabolism such as Paget's disease and primary hyperparathyroidism Severe physical or psychological concomitant diseases that might impair compliance with the provisions of the study protocol or that might impair the assessment of drug or patient safety, e.g. clinically significant ascites, cardiac failure, NYHA III or IV, clinically relevant pathologic findings in ECG Known hypersensitivity to zoledronic acid or other bisphosphonates Use of other investigational drugs 30 days prior to the date of randomization Known history or present abuse of alcohol or drugs Subjects who, in the opinion of the investigator, are unlikely to cooperate fully during the study Current active dental problems including infection of the teeth or jawbone (maxilla or mandibular); dental or fixture trauma, or a current or prior diagnosis of osteonecrosis of the jaw (ONJ), of exposed bone in the mouth, or of slow healing after dental procedures. Recent (within 6 weeks) or planned dental or jaw surgery (e.g. extraction, implants) Other protocol defined inclusion/exclusion criteria may apply.", "candidate_expression": "((Corrected serum calcium concentration) AND (History) AND (NYHA III or IV) AND (bisphosphonate Prior) AND (brain metastases clinically symptomatic) AND (calculated creatinine clearance < 30 ml/minute) AND (dental problems Current) AND (hypersensitivity) AND (other investigational drugs 30 days prior to the date of randomization) AND (renal function Abnormal) AND (within 6 weeks) AND ((Paget's disease) OR (diseases with influence on bone metabolism) OR (primary hyperparathyroidism)) AND ((physical diseases) OR (psychological diseases)) AND ((ECG clinically relevant pathologic findings) OR (ascites clinically significant) OR (cardiac failure)) AND ((other bisphosphonates) OR (zoledronic acid)) AND ((history) OR (present)) AND ((abuse of alcohol) OR (abuse of drugs)) AND ((infection of the jawbone) OR (infection of the teeth)) AND ((infection of the mandibular) OR (infection of the maxilla)) AND ((dental trauma) OR (fixture trauma)) AND ((current) OR (prior)) AND ((exposed bone in the mouth) OR (osteonecrosis of the jaw (ONJ)) OR (slow healing after dental procedures)) AND ((Recent) OR (planned)) AND ((dental surgery) OR (jaw surgery)) AND ((extraction) OR (implants)) AND ((2.00 mmol/L) OR (3.00 mmol/L) OR (< 8.0 mg/dl) OR (≥ 12.0 mg/dl)))"}
{"candidate_id": "LLM06454", "doc_id": "NCT02456129_inc", "case_bucket": "or", "source_criterion": "Body mass index (BMI): 18 ≤ BMI ≤ 32 kg/m² Postmenopausal state revealed by: Medical history, if applicable (natural menopause at least 12 months prior to first study drug administration; or surgical menopause by bilateral ovariectomy at least 3 months prior to first study drug administration), in addition: in women < 65 years old, follicle stimulating hormone (FSH) > 40 IU/L", "candidate_expression": "((Body mass index (BMI) 18 ≤ BMI ≤ 32 kg/m²) AND (Postmenopausal state) AND (bilateral ovariectomy) AND (follicle stimulating hormone (FSH) > 40 IU/L) AND (women) AND (years old < 65 years) AND ((natural menopause at least 12 months prior to first study drug administration) OR (surgical menopause at least 3 months prior to first study drug administration)))"}
{"candidate_id": "LLM06455", "doc_id": "NCT00425789_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have known middle ear disease, chronic lung disease or claustrophobia", "candidate_expression": "((chronic lung disease) OR (claustrophobia) OR (middle ear disease))"}
{"candidate_id": "LLM06456", "doc_id": "NCT03413891_exc", "case_bucket": "other", "source_criterion": "Subjects with any condition that as judged by the Investigator would place the subject at increased risk of harm if he/she participated in the study. Pregnancy or lactation Known allergic reaction to tranexamic acid", "candidate_expression": "((Pregnancy or lactation) AND (allergic) AND (tranexamic acid))"}
{"candidate_id": "LLM06457", "doc_id": "NCT02715518_inc", "case_bucket": "or", "source_criterion": "Symptoms of ischaemia. New or presumed new significant ST-T wave changes Development of pathological Q waves on ECG. Imaging evidence of new or presumed new loss of viable myocardium or regional wall motion abnormality.", "candidate_expression": "((ECG) AND (Imaging) AND (New) AND (ST-T wave changes) AND (Symptoms) AND (evidence) AND (ischaemia) AND (loss of viable myocardium) AND (new) AND (pathological Q waves) AND (presumed new) AND (regional wall motion abnormality) AND (significant))"}
{"candidate_id": "LLM06458", "doc_id": "NCT02982577_exc", "case_bucket": "other", "source_criterion": "Sensitivity to pilocarpine Secondary Sjögren's syndrome; Type II diabetes mellitus; AIDS; pregnant or lactating women; Glaucoma; Uncontrolled asthma; Chronic obstructive pulmonary disease; Renal diseases; Severe cardiovascular diseases; Gastrointestinal disorders; Hepatic insufficiency.", "candidate_expression": "((AIDS) AND (Chronic obstructive pulmonary disease) AND (Gastrointestinal disorders) AND (Glaucoma) AND (Hepatic insufficiency) AND (Renal diseases) AND (Sensitivity) AND (Sjögren's syndrome Secondary) AND (Type II diabetes mellitus) AND (asthma Uncontrolled) AND (cardiovascular diseases Severe) AND (pilocarpine) AND (pregnant or lactating women))"}
{"candidate_id": "LLM06459", "doc_id": "NCT01032109_inc", "case_bucket": "other", "source_criterion": "choroidal neovascularization caused by age-related macula degeneration no previous treatment a follow-up at least 12 months a baseline visual acuity ranging from a letter score of 0 to 70 on the Early Treatment Diabetic Retinopathy Study chart", "candidate_expression": "((Early Treatment Diabetic Retinopathy Study chart) AND (age-related) AND (at least 12 months) AND (baseline) AND (choroidal neovascularization) AND (follow-up) AND (letter score of 0 to 70) AND (macula degeneration) AND (no) AND (previous) AND (treatment) AND (visual acuity))"}
{"candidate_id": "LLM06460", "doc_id": "NCT01846507_inc", "case_bucket": "or", "source_criterion": "1. Menstruating females 10-19 years of age 2. Non-smoker 3. Physician and patient have agreed to initiate Lysteda 4. Diagnosis of HMB based on the medical judgment of the principal or site investigator 5. Subjects must report menstrual periods occurring within 21-60 days from the start of one period to the start of the next menstrual period 6. Negative pregnancy test 7. Informed consent obtained and signed 8. Informed assent obtained and signed 9. Understanding of study procedures 10. Ability to comply with study procedures for the entire length of the study 11. Subjects should be either sexually inactive (abstinent) or agree to use a barrier method with spermicide in the event of sexual activity throughout the study period", "candidate_expression": "((Ability to comply with study procedures for the entire length of the study) AND (HMB) AND (Informed assent obtained and signed) AND (Informed consent obtained and signed) AND (Lysteda) AND (Menstruating) AND (Non-smoker) AND (Understanding of study procedures) AND (age 10-19 years) AND (barrier method with spermicide agree to use) AND (based on the medical judgment of the principal or site investigator) AND (females) AND (menstrual periods within 21-60 days from the start of one period the start of one period) AND (pregnancy test Negative) AND (sexually abstinent) AND (sexually inactive))"}
{"candidate_id": "LLM06461", "doc_id": "NCT02733159_exc", "case_bucket": "or", "source_criterion": "Untreated symptomatic brain or leptomeningeal metastatic disease. Medical or psychiatric conditions comprising informed consent. Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol. Radiotherapy within 4 weeks of trial entry. Active autoimmune disease that has required systemic treatment in past 2 years Chronic usage of steroids or other immunosuppressant medication. Previous history of pneumonitis. Any evidence of clinical autoimmunity.", "candidate_expression": "((Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol.) AND (Medical or psychiatric conditions comprising informed consent) AND (Radiotherapy within 4 weeks of trial entry) AND (autoimmune disease Active) AND (pneumonitis history) AND (systemic treatment in past 2 years) AND ((symptomatic brain metastatic disease) OR (symptomatic leptomeningeal metastatic disease Untreated Untreated)) AND ((immunosuppressant medication Chronic usage) OR (steroids Chronic usage)) AND ((Any evidence of clinical autoimmunity) OR (autoimmunity)) AND ((Medical conditions) OR (psychiatric conditions)))"}
{"candidate_id": "LLM06462", "doc_id": "NCT00625742_exc", "case_bucket": "or", "source_criterion": "1. Have dementia or delirium (as determined by the palliative care specialist) at study entry. 2. Are pregnant 3. Have been taking corticosteroids for longer than 48 hours. 4. Have pulmonary edema, ascites or pitting edema on clinical examination. 5. Are unable to walk. 6. Have a history of serious adverse gastrointestinal events (i.e., bleeding or perforation),history of a coagulopathy or current anti-coagulant use. 7. Have an ALT/AST>3x upper limit of normal. 8. Patients on methotrexate. 9. Patients taking melatonin receptor agonists (such as Rozerem® [ramelteon]).", "candidate_expression": "((ALT/AST >3x upper limit of normal) AND (Rozerem) AND (adverse gastrointestinal events history serious) AND (anti-coagulant current) AND (ascites) AND (bleeding) AND (coagulopathy history) AND (corticosteroids longer than 48 hours) AND (delirium) AND (dementia) AND (melatonin receptor agonists) AND (methotrexate) AND (perforation) AND (pitting edema) AND (pregnant) AND (pulmonary edema) AND (ramelteon) AND (unable to walk))"}
{"candidate_id": "LLM06463", "doc_id": "NCT02477280_inc", "case_bucket": "other", "source_criterion": "18 years old or older. ADHD is diagnosed according to Diagnostic and Statistical Manual of Mental Disorders, fifth edition (DSM-5 criteria). Substance Use Disorder is diagnosed according to DSM-5 criteria. Qb-score 1.3 or higher on at least one of the weighted summary parameters QbActivity, QbInattention or QbImpulsivity on the QbTest. Participants are given their written informed consent to participate in the study.", "candidate_expression": "((ADHD DSM-5) AND (Participants are given their written informed consent to participate in the study) AND (Qb-score 1.3 or higher) AND (Substance Use Disorder DSM-5) AND (old 18 years or older))"}
{"candidate_id": "LLM06464", "doc_id": "NCT03017053_inc", "case_bucket": "or", "source_criterion": "Ability to understand and the willingness to sign a written informed consent document Age= 18 and= 75 years Clinical/ Histological/ cytological/ Imaging examination proven Oral/Oropharynx Squamous-cell carcinoma (Tongue, buccal mucosa, mouth floor, hard palate, Molar area), the depth of invasion > 4mm in preoperative assessment In line with clinical stage I / II stage (T1-2 N0 M0; AJCC 2010) and receiving surgical resection KPS= 70 Normal bone marrow reserve function and normal liver, kidney function Expected survival period= 6 months", "candidate_expression": "((0) AND (1-2) AND (= 18 and= 75 years) AND (= 6 month) AND (= 70) AND (> 4mm) AND (Ability to understand and the willingness to sign a written informed consent document) AND (Age) AND (Expected survival period) AND (KPS) AND (M) AND (N) AND (Normal) AND (Squamous-cell carcinoma) AND (T) AND (bone marrow reserve function) AND (depth of invasion) AND (normal) AND (preoperative assessment) AND (surgical resection) AND ((Molar area) OR (Tongue) OR (buccal mucosa) OR (hard palate) OR (mouth floor)) AND ((Clinical examination) OR (Histological examination) OR (Imaging examination) OR (cytological examination)) AND ((clinical stage I) OR (clinical stage II)) AND ((kidney function) OR (liver function)) AND ((Oral) OR (Oropharynx)))"}
{"candidate_id": "LLM06465", "doc_id": "NCT02511574_inc", "case_bucket": "other", "source_criterion": "gestational age between 20 weeks and 23 weeks and 6 days singleton pregnancies", "candidate_expression": "((gestational age between 20 weeks and 23 weeks and 6 days) AND (singleton pregnancies))"}
{"candidate_id": "LLM06466", "doc_id": "NCT02691793_inc", "case_bucket": "or", "source_criterion": "Provision of fully informed consent prior to study specific procedures. Patients must be >= 19 years of age RET fusion positive or FGFR2 fusion/other FGFR mutation Refractory solid tumor and/or specific sensitivity to Sunitinib by Avatar scan that has progressed following standard therapy or that has not responded to standard therapy or for which there is no standard therapy. ECOG Performance status0-2 Have measurable or evaluated disease based on RECIST 1.1 as determined by investigator. Absolute neutrophil count >= 1.5 x 109/L, Hemoglobin >= 9g/dL, Platelets>=100 x 109/L Bilirubin <= 1.5 x upper limit of normal AST/ALT <= 2.5 X upper limit of normal(5.0 x upper limit of normal, for subject with liver metastases) Creatinine<= 1.5 X UNL Patients of child-bearing potential should be using adequate contraceptive measures should not be breast feeding and must have a negative pregnancy test prior to start of dosing Adequate heart function", "candidate_expression": "((ALT 5.0 x upper limit of normal) AND (ALT <= 2.5 X upper limit of normal() AND (AST 5.0 x upper limit of normal) AND (AST <= 2.5 X upper limit of normal() AND (Absolute neutrophil count >= 1.5 x 109/L) AND (Adequate heart function) AND (Bilirubin <= 1.5 x upper limit of normal) AND (Creatinine <= 1.5 X UNL) AND (ECOG Performance status 0-2) AND (Hemoglobin >= 9g/dL,) AND (Platelets >=100 x 109/L) AND (Provision of fully informed consent prior to study specific procedures) AND (RET fusion positive FGFR2 fusion FGFR mutation) AND (Sunitinib sensitivity) AND (adequate contraceptive measures) AND (age >= 19 years) AND (child-bearing potential) AND (heart function Adequate) AND (liver metastases) AND (pregnancy test negative prior to start of dosing) AND (solid tumor Refractory) AND NOT (breast feeding))"}
{"candidate_id": "LLM06467", "doc_id": "NCT03471117_inc", "case_bucket": "or", "source_criterion": "CKD patients classified as Stage 3 and 4 of National Kidney Foundation Classification with estimated glomerular filtration rate (GFR) between 15 and 59 mL/min/1.73 m2 according to the Modification of Diet in Renal Disease (MDRD) formula based on serum creatinine, age, gender, and race. Men and women 35 to 70 years of age", "candidate_expression": "((CKD) AND (National Kidney Foundation Classification) AND (age 35 to 70 years) AND (estimated glomerular filtration rate (GFR) between 15 and 59 mL/min/1.73 m2 Modification of Diet in Renal Disease (MDRD) formula) AND ((Stage 3) OR (Stage 4)) AND ((Men) OR (women)))"}
{"candidate_id": "LLM06468", "doc_id": "NCT03228238_inc", "case_bucket": "scope", "source_criterion": "Subject must be at least 30 years of age. Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure. Subject must have symptoms that are consistent with vasospastic angina with planned Coronary angiography and Provocation test.", "candidate_expression": "((Coronary angiography) AND (Provocation test) AND (Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure) AND (age at least 30 years) AND (symptoms) AND (vasospastic angina))"}
{"candidate_id": "LLM06469", "doc_id": "NCT02406885_exc", "case_bucket": "or", "source_criterion": "History of documented clotting/coagulation disorder History of cancer (within the last year) Any diagnosis requiring anti-coagulation History of hypersensitivity reaction to apixaban Active clinically significant bleeding Creatinine > 1.5 mg/dL Participants currently receiving any type of anticoagulation or blood thinning medications, including heparin, low molecular weight heparins, Plavix, aspirin, NSAIDS Combined P-glycoprotein and strong cytochrome P450 (CYP) 3A4 inhibitor Combined P-glycoprotein and moderate CYP 3A4 inhibitor Combined P-glycoprotein inducer and strong CYP 3A4 inducer Inducers of p-glycoprotein Strong inducers of CYP 3A4", "candidate_expression": "((> 1.5 mg/dL) AND (Active) AND (CYP 3A4 inducer) AND (CYP 3A4 inhibitor) AND (Creatinine) AND (Inducers of p-glycoprotein) AND (NSAIDS) AND (P-glycoprotein inducer) AND (P-glycoprotein inhibitor) AND (Plavix) AND (Strong) AND (anti-coagulation) AND (anticoagulation) AND (apixaban) AND (aspirin) AND (bleeding) AND (blood thinning medications) AND (cancer) AND (clotting disorder) AND (coagulation disorder) AND (cytochrome P450 3A4 inhibitor) AND (heparin) AND (hypersensitivity) AND (inducers of CYP 3A4) AND (last year) AND (low molecular weight heparins) AND (moderate) AND (significant) AND (strong))"}
{"candidate_id": "LLM06470", "doc_id": "NCT02055053_exc", "case_bucket": "other", "source_criterion": "Conversion from laparoscopic to open surgery History of Chronic pain or ongoing treatment for chronic pain Age less than 18 yrs Allergy to local anesthetics", "candidate_expression": "((Age less than 18 yrs) AND (Allergy) AND (Chronic pain History) AND (chronic pain) AND (local anesthetics) AND (treatment ongoing))"}
{"candidate_id": "LLM06471", "doc_id": "NCT02942303_inc", "case_bucket": "other", "source_criterion": "Consecutive 30 female patients presenting to our clinic for brow lifting with botulinum toxin will be randomized to receive one of the two injection techniques", "candidate_expression": "((30) AND (botulinum toxin) AND (brow lifting) AND (female))"}
{"candidate_id": "LLM06472", "doc_id": "NCT01314898_inc", "case_bucket": "or", "source_criterion": "Male and/or female healthy volunteers, age 18 to 55 years. Females must be of non-childbearing potential. Body Mass Index (BMI) of 17.5 to 30.5 kg/m2; and a total body weight >50 kg (110 lbs). Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.", "candidate_expression": "((17.5 to 30.5 kg/m2) AND (18 to 55 years) AND (>50 kg (110 lbs)) AND (Body Mass Index (BMI)) AND (Females) AND (Male) AND (Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.) AND (age) AND (childbearing potential) AND (female) AND (healthy) AND (non) AND (total body weight))"}
{"candidate_id": "LLM06473", "doc_id": "NCT02810704_inc", "case_bucket": "or", "source_criterion": "Males and females 21 years of age or older; Undergoing elective primary, resurfacing arthroplasty, revision, or second stage re-implantation total hip replacement; Undergoing elective primary, revision, or second stage re-implantation total or uni compartmental knee replacement; Patient has necessary mental capacity to participate and is able to comply with study protocol requirements; Patient is willing and able to give informed consent; and Patient is willing to be randomized and participate.", "candidate_expression": "((Patient has necessary mental capacity to participate and is able to comply with study protocol requirements) AND (Patient is willing and able to give informed consent) AND (Patient is willing to be randomized and participate) AND (age 21 years or older) AND (knee replacement elective) AND (total hip replacement elective) AND ((Males) OR (females)) AND ((primary) OR (revision) OR (second stage re-implantation total) OR (uni compartmental)) AND ((primary) OR (resurfacing arthroplasty) OR (revision) OR (second stage re-implantation)))"}
{"candidate_id": "LLM06474", "doc_id": "NCT03345589_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed with primary biliary cholangitis Treated with Ursodeoxycholic Acid in West China Hospital for at least 6 month and suboptimal response to Ursodeoxycholic Acid", "candidate_expression": "((Ursodeoxycholic Acid) AND (Ursodeoxycholic Acid for at least 6 month) AND (West China Hospital) AND (primary biliary cholangitis) AND (suboptimal response))"}
{"candidate_id": "LLM06475", "doc_id": "NCT02970773_exc", "case_bucket": "or", "source_criterion": "Any anti-coagulation therapy (apart from rivaroxaban for second objective) Hypersensitivity or allergy to factor Xa inhibitors Acute bacterial endocarditis Bleeding disorder Clinically relevant active bleeding Gastrointestinal ulcer or tumor Hepatic dysfunction with increased bleeding risk Renal failure / patients undergoing dialysis Pregnancy and breast feeding Gastrectomy, biliopancreatic diversion, resection or re-routing of small intestines Feeding tube Recent blood donation Abnormalities of laboratory values: alanine-aminotransferase (ALAT), aspartate-aminotransferase (ASAT), gamma-glutamyl transferase (gammaGT), alkalic phosphatase (AP), bilirubin, amylase, lipase, cystatin C, creatinine, white blood cell count, haemoglobin, platelet count, prothrombin time, aPTT, fibrinogen, thrombin time, factors II,V,VII and X Use of therapeutic or recreational drugs influencing plasmatic coagulation", "candidate_expression": "((ALAT) AND (AP) AND (ASAT) AND (Acute bacterial endocarditis) AND (Bleeding disorder) AND (Feeding tube) AND (Gastrectomy) AND (Gastrointestinal tumor) AND (Gastrointestinal ulcer) AND (Hepatic dysfunction) AND (Hypersensitivity) AND (Pregnancy and breast feeding) AND (Renal failure) AND (aPTT) AND (active bleeding) AND (alanine-aminotransferase) AND (alkalic phosphatase) AND (allergy) AND (amylase) AND (anti-coagulation therapy) AND (aspartate-aminotransferase) AND (biliopancreatic diversion) AND (bilirubin) AND (bleeding risk increased) AND (blood donation) AND (creatinine) AND (cystatin C) AND (dialysis) AND (factor Xa inhibitors) AND (factors II) AND (factors V) AND (factors VII) AND (factors X) AND (fibrinogen) AND (gamma-glutamyl transferase) AND (gammaGT) AND (haemoglobin) AND (lipase) AND (platelet count) AND (prothrombin time,) AND (re-routing) AND (resection) AND (thrombin time) AND (white blood cell count) AND NOT (rivaroxaban))"}
```
