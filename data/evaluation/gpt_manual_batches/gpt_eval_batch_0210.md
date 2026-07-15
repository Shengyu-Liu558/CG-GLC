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
{"candidate_id": "LLM05226", "doc_id": "NCT02833116_exc", "case_bucket": "or", "source_criterion": "Patients with high intracranial pressure. Patients with Multiple Sclerosis. Patients with Guillain-Barré syndrome radiculopathy of vascular origin. Patients with previous lumbar surgery. Patients pregnant or lactating. Patients with allergy or intolerance to any of the drugs used. Patients with severe cognitive impairment. Patients with intrathecal injectio radiculalgia. Patients with poorly controlled major psychiatric pathology. Patients with type I diabetes or poorly controlled type II diabetes (Hb1Ac>8.5). Patients with glaucoma. Patients with caudal equine syndrome. Patients with pre-treatment with steroid injections/or local anesthetics. Patients with central canal stenosis. patients with chronic treatment with oral corticosteroids without stabilized pattern.", "candidate_expression": "((Guillain-Barré syndrome radiculopathy vascular) AND (Hb1Ac >8.5) AND (Multiple Sclerosis) AND (Patients pregnant or lactating) AND (caudal equine syndrome) AND (central canal stenosis) AND (cognitive impairment severe) AND (drugs) AND (glaucoma) AND (intracranial pressure high) AND (intrathecal injectio radiculalgia) AND (lumbar surgery.) AND (oral corticosteroids) AND (psychiatric pathology poorly controlled major) AND ((type I diabetes) OR (type II diabetes poorly controlled)) AND ((local anesthetics) OR (steroid injections)) AND ((allergy) OR (intolerance)))"}
{"candidate_id": "LLM05227", "doc_id": "NCT02942303_inc", "case_bucket": "other", "source_criterion": "Consecutive 30 female patients presenting to our clinic for brow lifting with botulinum toxin will be randomized to receive one of the two injection techniques", "candidate_expression": "((30) AND (botulinum toxin) AND (brow lifting) AND (female))"}
{"candidate_id": "LLM05228", "doc_id": "NCT01177891_inc", "case_bucket": "or", "source_criterion": "Patients of familial cases of POF : Female subjects between 16 and 40 years or women older than 40 years with a cessation of ovarian function before the age of 40 years with increased levels of FSH Primary or secondary amenorrhea for more than three months with LH and FSH> 30mUI/ml No cases of fragile X syndrome in the family or blepharophimosis syndrome At least two cases in the family Origin Caucasian Patient signing the consent form for at least the blood sample Patient with Social Security Population Index related topics : The presence of cycles until the age of 40 years with proven fertility, at least one child Amenorrhea and FSH> 30mUI/ml according to the criteria of the index subject Men of the family of index case Population control : Women of Caucasian origin Women who had regular cycles until at least age 40 and at least one child Lack of land autoimmune (no history of thyroid disease or diabetes type 1) Woman signing the consent form for at least the blood sample", "candidate_expression": "((> 30mUI/ml) AND (Amenorrhea) AND (At least two) AND (Caucasian) AND (Caucasian origin) AND (FSH) AND (Female) AND (LH) AND (No) AND (Patient signing the consent form for at least the blood sample) AND (Primary) AND (The presence of cycles until the age of 40 years with proven fertility, at least one child) AND (Woman signing the consent form for at least the blood sample) AND (Women) AND (age) AND (amenorrhea) AND (autoimmune) AND (before the age of 40 years) AND (between 16 and 40 years) AND (blepharophimosis syndrome) AND (cessation of ovarian function) AND (diabetes type 1) AND (for more than three months) AND (fragile X syndrome) AND (history) AND (in the family) AND (increased) AND (levels of FSH) AND (no) AND (older) AND (older than 40 years) AND (presence of cycles) AND (regular cycles) AND (secondary) AND (thyroid disease) AND (until at least age 40) AND (until the age of 40 years) AND (who had regular cycles until at least age 40) AND (women) AND (years))"}
{"candidate_id": "LLM05229", "doc_id": "NCT02621489_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes (autoantibody positive). Any history of receiving GLP-1 analogues or dipeptidyl peptidase inhibitors within 6 months Known severe heart failure, classified as NYHA 4. Active myocarditis; malfunctioning artificial heart valve. History of ventricular tachycardia within 3 months before study entry; second- or third-degree atrioventricular block. Supine systolic blood pressure <85 mm Hg or >200 mm Hg at screening. Primary renal impairment, creatinine clearance < 45 ml/min if treated with metformin. Uncorrected hypokalemia or hyperkalemia (potassium <3.5 mmol/l or >5.5 mmol/l). Significant anemia (Hb < 90 g/l) Severe gastrointestinal disease, including gastroparesis. As judged by the Investigator. Body mass index (BMI) > 45 kg/m2. Malignant neoplasm requiring chemotherapy, surgery, radiation or palliative therapy in the previous 5 years. Patients with intraepithelial squamous cell carcinoma of the skin treated with topical 5FU and subjects with basal cell skin cancer are allowed to enter the trial. Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant. Current drug and alcohol abuse. History of acute or chronic pancreatitis Subjects considered by the Investigator to be unsuitable for the study.", "candidate_expression": "((BMI) AND (Body mass index > 45 kg/m2) AND (Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant) AND (Hb < 90 g/l) AND (Malignant neoplasm previous 5 years.) AND (NYHA 4) AND (Primary renal impairment) AND (Type 1 diabetes) AND (anemia Significant) AND (autoantibody positive) AND (creatinine clearance < 45 ml/min) AND (gastrointestinal disease Severe) AND (gastroparesis) AND (heart failure severe) AND (metformin) AND (potassium) AND (systolic blood pressure Supine) AND (topical 5FU) AND ((Active myocarditis) OR (artificial heart valve malfunctioning)) AND ((second- degree atrioventricular block) OR (third-degree atrioventricular block) OR (ventricular tachycardia within 3 months)) AND ((<85 mm Hg) OR (>200 mm Hg)) AND ((hyperkalemia) OR (hypokalemia)) AND ((<3.5 mmol/l) OR (>5.5 mmol/l)) AND ((GLP-1 analogues) OR (dipeptidyl peptidase inhibitors)) AND ((chemotherapy) OR (palliative therapy) OR (radiation) OR (surgery)) AND ((basal cell skin cancer) OR (intraepithelial squamous cell carcinoma skin)) AND ((alcohol abuse) OR (drug abuse)) AND ((acute pancreatitis) OR (chronic pancreatitis)))"}
{"candidate_id": "LLM05230", "doc_id": "NCT00236340_inc", "case_bucket": "or", "source_criterion": "Pregnant women with abdomen discumfort and ultrasound diagnosis of polyhydramnios (AFI>25cm) Single or twin pregnancies", "candidate_expression": "((>25cm) AND (AFI) AND (Pregnant) AND (Single) AND (abdomen discumfort) AND (diagnosis) AND (polyhydramnios) AND (pregnancies) AND (twin) AND (ultrasound) AND (women))"}
{"candidate_id": "LLM05231", "doc_id": "NCT01943409_exc", "case_bucket": "other", "source_criterion": "• Patients without PN during their hospitalization", "candidate_expression": "((hospitalization) AND NOT (PN during their hospitalization))"}
{"candidate_id": "LLM05232", "doc_id": "NCT02698969_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-II age between 18-80 years old dNMB with rocuronium during ear nose and throat (ENT) surgery", "candidate_expression": "((ASA physical status) AND (I-II) AND (age) AND (between 18-80 years) AND (dNMB with rocuronium) AND (ear nose and throat (ENT) surgery))"}
{"candidate_id": "LLM05233", "doc_id": "NCT03539718_exc", "case_bucket": "other", "source_criterion": "Patients with intercurrent infections. Patients with sepsis. Patients receiving drugs affecting immune system like immunosuppressive drugs. Patients on antibiotics.", "candidate_expression": "((antibiotics) AND (drugs affecting immune system) AND (immunosuppressive drugs) AND (intercurrent infections) AND (sepsis))"}
{"candidate_id": "LLM05234", "doc_id": "NCT02596555_exc", "case_bucket": "or", "source_criterion": "Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond History of hypersensitivity to the investigational medicinal product or to any drug with similar chemical structure or to any excipient present in the pharmaceutical form of the investigational medicinal product Participation in another clinical trial during the present clinical trial or within the last three months Medical or psychological condition that would not permit completion of the trial or signing of informed consent Use of a fibrinolytic agent, surgical thrombectomy, interventional (catheter-directed) thrombus aspiration or lysis, or use of a cava filter to treat the index episode of PE Treatment with any therapeutically dosed anticoagulant for more than 48 hours prior to enrolment Need for long-term treatment with a low molecular weight heparin, vitamin K antagonists or NOAC, for an indication other than the index PE episode, or for antiplatelet agents except acetylsalicylic acid at a dosage =100 mg/day; Active bleeding or known significant bleeding risk (e.g., gastrointestinal ulcer, malignant neoplasms, injuries or recent surgeries of the brain, spinal cord or eyes, recent intracranial bleedings, known or suspected esophagus varices, aneurysms or intraspinal or intracranial vascular abnormalities) Artificial heart valves requiring treatment with an anticoagulant Renal insufficiency with estimated creatinine clearance <30 ml/min/1.73m2 Chronic liver disease with aminotransferase levels two times or more above the local upper limit of normal range Concomitant administration of strong inhibitors of P-glycoprotein like ketoconazole, cyclosporin, itraconazole or dronedarone Unwillingness or inability to adhere to treatment or to the follow-up visits Life expectancy less than 6 months", "candidate_expression": "((<30 ml/min/1.73m2) AND (=100 mg/day;) AND (Artificial heart valves) AND (Chronic liver disease) AND (Life expectancy) AND (Medical or psychological condition that would not permit completion of the trial or signing of informed consent) AND (PE) AND (PE episode) AND (Participation in another clinical trial during the present clinical trial or within the last three months) AND (Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation) AND (Renal insufficiency) AND (Unwillingness or inability to adhere to treatment or to the follow-up visits) AND (Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond) AND (acetylsalicylic acid) AND (aminotransferase) AND (anticoagulant) AND (antiplatelet agents) AND (enrolment) AND (estimated creatinine clearance) AND (except) AND (index) AND (inhibitors of P-glycoprotein) AND (less than 6 months) AND (long-term) AND (more than 48 hours prior to enrolment) AND (other) AND (significant) AND (therapeutically) AND (two times or more above the local upper limit of normal range) AND ((cava filter) OR (fibrinolytic agent) OR (surgical thrombectomy,) OR (thrombus aspiration) OR (thrombus lysis)) AND ((NOAC) OR (low molecular weight heparin) OR (vitamin K antagonists)) AND ((Active bleeding) OR (bleeding risk)) AND ((brain) OR (eyes) OR (spinal cord)) AND ((aneurysms) OR (esophagus varices) OR (gastrointestinal ulcer) OR (injuries) OR (intracranial bleedings) OR (malignant neoplasms) OR (surgeries) OR (vascular abnormalities))) AND ((intracranial) OR (intraspinal)) AND ((cyclosporin) OR (dronedarone) OR (itraconazole) OR (ketoconazole)))"}
{"candidate_id": "LLM05235", "doc_id": "NCT01700790_exc", "case_bucket": "or", "source_criterion": "Non-compliance with DOTPlus. Alternatively DOT can be done by telephoning patient on a daily basis 5 times a week and having patient annotate taking drug in a log which would be reviewed by clinic staff History of being treated for tuberculosis in the prior 2 years unless there is DST, including PCR testing, showing sensitivity to rifamycin. Known hypersensitivity to rifampin or rifabutin. Liver enzymes greater than 2 times ULN. Bilirubin greater than 2 times ULN. Serum creatinine greater than 3 times ULN. Hemoglobin less than 7.0 gms even if receiving erythropoietin. Absolute neutrophil count less than 750 cells/mm3 even if receiving G-CSF. Fasting triglycerides greater than 400 mg/dL. Fasting cholesterol > 1.6 upper limits of normal. GI intolerance of tuberculosis medications requiring discontinuation of tuberculosis medications. Fasting glucose greater 150 mg/dL. Pregnant women. Use of one of the prohibited medications Any condition that the investigators feel could compromise the use of the current medication. Have a CD4 cell count of 50 cells/mm3or less Hepatitis B or C infection Alcohol or illicit drug use, which in the investigators opinion may affect participation in study.", "candidate_expression": "((Absolute neutrophil count less than 750 cells/mm3) AND (Any condition that the investigators feel could compromise the use of the current medication.) AND (Bilirubin greater than 2 times ULN) AND (CD4 cell count 50 cells/mm3or less) AND (DOTPlus) AND (Fasting cholesterol > 1.6 upper limits of normal) AND (Fasting glucose greater 150 mg/dL) AND (Fasting triglycerides greater than 400 mg/dL) AND (GI intolerance) AND (Hemoglobin less than 7.0 gms) AND (Liver enzymes greater than 2 times ULN) AND (Non-compliance) AND (PCR testing) AND (Pregnant) AND (Serum creatinine greater than 3 times ULN) AND (Use of one of the prohibited medications) AND (discontinuation) AND (hypersensitivity) AND (rifamycin) AND (sensitivity) AND (tuberculosis) AND (tuberculosis medications) AND (women) AND ((DST) OR (treated in the prior 2 years)) AND ((rifabutin) OR (rifampin)) AND ((Hepatitis B) OR (Hepatitis C)) AND ((Alcohol use) OR (illicit drug use)))"}
{"candidate_id": "LLM05236", "doc_id": "NCT01314898_exc", "case_bucket": "or", "source_criterion": "Subjects with a supine BP >140 mm Hg systolic or >90 mm Hg diastolic or <100 mm Hg systolic or <60 mm Hg diastolic based on the average of the triplicate Serum potassium >=5.1 mmol/L or <3.5 mmol/L at screening, confirmed by a single repeat if deemed necessary. Estimated GFR <60 mL/min/1.73 m2 using the Cockcroft-Gault formula measurement of the individual parameters following at least 5 minutes of rest at Screening.", "candidate_expression": "((Estimated GFR <60 mL/min/1.73 m2 Cockcroft-Gault formula) AND (Serum potassium at screening >=5.1 mmol/L <3.5 mmol/L) AND (supine BP >140 mm Hg systolic >90 mm Hg diastolic <100 mm Hg systolic <60 mm Hg diastolic))"}
{"candidate_id": "LLM05237", "doc_id": "NCT03495557_inc", "case_bucket": "or", "source_criterion": "Age = 18 years Laparoscopic cholecystectomy Emergent/elective =2 risk factors: diabetes mellitus, age =70 years, BMI =30, fascial enlargement", "candidate_expression": "((= 18 years) AND (=2) AND (=30) AND (=70 years) AND (Age) AND (Laparoscopic) AND (cholecystectomy) AND (risk factors) AND ((BMI) OR (age) OR (diabetes mellitus) OR (fascial enlargement)) AND ((Emergent) OR (elective)))"}
{"candidate_id": "LLM05238", "doc_id": "NCT02535299_inc", "case_bucket": "or", "source_criterion": "Newly dignosised type 2 diabetes according to WHO criteria.glycated hemoglobin (HbA1c) was more than 10%; Seronegative for antibodies against insulin, islet cells and glutamic acid decarboxylase (GAD);", "candidate_expression": "((Newly dignosised) AND (Seronegative) AND (WHO criteria) AND (antibodies) AND (glutamic acid decarboxylase (GAD)) AND (glycated hemoglobin (HbA1c)) AND (insulin) AND (islet cells) AND (more than 10%) AND (type 2 diabetes))"}
{"candidate_id": "LLM05239", "doc_id": "NCT02282319_exc", "case_bucket": "other", "source_criterion": "micturition problems, neurological history or previous lower abdominal surgery with an abnormal micturition", "candidate_expression": "((lower abdominal surgery) AND (micturition) AND (micturition abnormal) AND (neurological history))"}
{"candidate_id": "LLM05240", "doc_id": "NCT02612181_exc", "case_bucket": "or", "source_criterion": "Age< 18 Pregnancy Bradycardia (HR<55bpm) Systolic Blood Pressure < 80 mmHg / Mean arterial pressure < 50 mmHg on maximal support Death imminent Unlikely to survive 90 days Acute liver failure Dementia High-grade block in the absence of a functioning pacemaker.", "candidate_expression": "((Acute liver failure) AND (Age < 18) AND (Bradycardia) AND (Death imminent) AND (Dementia) AND (HR <55bpm) AND (High-grade block) AND (Mean arterial pressure < 50 mmHg) AND (Pregnancy) AND (Systolic Blood Pressure < 80 mmHg) AND (support) AND NOT (pacemaker functioning))"}
{"candidate_id": "LLM05241", "doc_id": "NCT03231982_inc", "case_bucket": "other", "source_criterion": "Adult male and female aged 19 to 75 years Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.", "candidate_expression": "((Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.) AND (aged 19 to 75 years) AND (female) AND (male))"}
{"candidate_id": "LLM05242", "doc_id": "NCT02498483_inc", "case_bucket": "other", "source_criterion": "Apgar score at 5 minutes >7 birthweight greater than 2.4 kg Age of at least 10 hours At least one void.", "candidate_expression": "((>7) AND (Age) AND (Apgar score) AND (At least one) AND (at 5 minutes) AND (at least 10 hours) AND (birthweight) AND (greater than 2.4 kg) AND (void))"}
{"candidate_id": "LLM05243", "doc_id": "NCT03467750_exc", "case_bucket": "other", "source_criterion": "Known coagulation defect Patients on longstanding NSAID therapy Known renal impairment Patients may also be excluded at the discretion of the investigator", "candidate_expression": "((NSAID therapy longstanding) AND (coagulation defect) AND (renal impairment))"}
{"candidate_id": "LLM05244", "doc_id": "NCT01816997_inc", "case_bucket": "other", "source_criterion": "Age 35-70 years old Fasting blood glucose 100-125 mg/dL", "candidate_expression": "((Age 35-70 years old) AND (Fasting blood glucose 100-125 mg/dL))"}
{"candidate_id": "LLM05245", "doc_id": "NCT03177811_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((<0.7) AND (<40% predicted) AND (<92% at 750 m) AND (>20 cigarettes per day) AND (COPD) AND (COPD exacerbation) AND (Comorbidities) AND (hypoxemia) AND (in the last 2 months) AND (low altitude) AND (previous) AND (room air) AND (uncontrolled) AND (unstable) AND (very severe) AND ((coronary artery disease) OR (systemic arterial hypertension)) AND ((OSA) OR (cardiovascular disease) OR (pneumothorax) OR (stroke)) AND ((Internal disease) OR (heavy smoking) OR (neurologic disease) OR (psychiatric disease) OR (rheumatologic disease)) AND ((allergy) OR (renal failure)) AND ((acetazolamide) OR (sulfonamides)) AND ((FEV1) OR (FEV1/FVC) OR (oxygen saturation)))"}
{"candidate_id": "LLM05246", "doc_id": "NCT03241368_inc", "case_bucket": "or", "source_criterion": "Subject has provided informed consent. Subject is ≥ 18 years of age Subject is willing and able to comply with all aspects of treatment and evaluation schedule. Subject has known CD and a recent history (within last 2 years) of mucosal disease (diagnosis based on radiologic, endoscopic, or histological evidence).", "candidate_expression": "((age) AND (endoscopic evidence) AND (histological evidence) AND (mucosal disease) AND (radiologic evidence) AND (recent history) AND (within last 2 years) AND (≥ 18 years))"}
{"candidate_id": "LLM05247", "doc_id": "NCT02348918_exc", "case_bucket": "or", "source_criterion": "Active proliferative diabetic retinopathy (PDR) in the study eye such as NVE, NVD, vitreous hemorrhage, or neovascular glaucoma. Uncontrolled hypertension defined as systolic >180 mmHg or > 160 mmHg on 2 consecutive measurements or diastolic > 100 mmHg on optimal medical regimen Screening HgA1c blood test > 10.0 Focal laser photocoagulation or intravitreal/periocular steroids of any type in the study eye within the last 90 days prior to study enrollment. A history of intravitreal anti-VEGF injection of any type in the study eye within the last 45 days prior to study enrollment. History of rhegmatogenous retinal detachment, retinal tear(s), or traction retinal detachments in the study eye. Epiretinal membrane and/or vitreomacular traction in the study eye as determined by the central reading center. Previous pars plana vitrectomy in the study eye Any intraocular surgery in the study eye within the last 90 days prior to study enrollment. YAG laser treatment in the study eye in last 30 days prior to study enrollment. High myopia in the study eye, with a spherical equivalent of >8.00D at screening Other ocular pathologies that in the investigator's opinion would interfere with the subject's vision in the study eye. Chronic or recurrent uveitis. Ongoing ocular infection or inflammation in either eye. A history of cataract surgery complications/vitreous loss in the study eye. Congenital eye malformations in the study eye. A history of penetrating ocular trauma in the study eye. Mentally handicapped. Pregnant female, as determined for women less than 60 years old by a positive urine pregnancy test during the screening window. Nursing female. Currently participating in any other clinical research study. Contraindication to the study medication.", "candidate_expression": "((> 10.0) AND (> 100 mmHg) AND (> 160 mmHg) AND (>180 mmHg) AND (>8.00D) AND (Active proliferative diabetic retinopathy (PDR)) AND (Chronic) AND (Congenital eye malformations) AND (Contraindication) AND (Currently participating in any other clinical research study.) AND (Epiretinal membrane traction) AND (Focal laser photocoagulation) AND (HgA1c blood test) AND (High myopia) AND (History of) AND (Mentally handicapped) AND (NVD) AND (NVE) AND (Nursing) AND (Ongoing) AND (Other) AND (Pregnant) AND (Previous) AND (Screening) AND (Uncontrolled hypertension) AND (YAG laser treatment) AND (anti-VEGF injection) AND (at screening) AND (cataract surgery) AND (cataract surgery complications) AND (diastolic) AND (during the screening window) AND (female) AND (history of) AND (in either eye) AND (in last 30 days prior to study enrollment) AND (in the study eye) AND (intraocular surgery) AND (intravitreal) AND (intravitreal/periocular steroids) AND (less than 60 years) AND (neovascular glaucoma) AND (ocular infection) AND (ocular inflammation) AND (ocular pathologies) AND (old) AND (on 2 consecutive measurements) AND (on optimal medical regimen) AND (optimal medical regimen) AND (pars plana vitrectomy) AND (penetrating ocular trauma) AND (positive) AND (recurrent) AND (retinal tear(s)) AND (rhegmatogenous retinal detachment) AND (spherical equivalent) AND (study enrollment) AND (study medication) AND (systolic) AND (traction retinal detachments) AND (urine pregnancy test) AND (uveitis) AND (vitreomacular traction) AND (vitreous hemorrhage) AND (vitreous loss) AND (within the last 45 days prior to study enrollment) AND (within the last 90 days prior to study enrollment) AND (women) AND (would interfere with the subject's vision in the study eye))"}
{"candidate_id": "LLM05248", "doc_id": "NCT02964416_inc", "case_bucket": "or", "source_criterion": "Patients with craniotomy for supratentorial tumors under general anesthesia American Society of Anaesthesiologists (ASA) 2 and stable ASA 3 patients Elective surgery Patients with Glasgow Coma Scale (GCS) 15/15", "candidate_expression": "((15/15) AND (2) AND (3) AND (ASA) AND (Elective surgery) AND (GCS) AND (Glasgow Coma Scale) AND (craniotomy) AND (general anesthesia) AND (stable) AND (supratentorial tumors) AND ((ASA) OR (American Society of Anaesthesiologists)))"}
{"candidate_id": "LLM05249", "doc_id": "NCT02137538_inc", "case_bucket": "or", "source_criterion": "Current height less than 5th percentile AND/OR Predicted adult height (based on bone age) more than 10 cm below target height (mid parental height) Evidence of puberty: physical signs and serum luteinizing hormone > 0.3 IU/L and testosterone > 15 ng/dl", "candidate_expression": "((> 0.3 IU/L) AND (> 15 ng/dl) AND (Current) AND (Evidence of puberty) AND (Predicted adult height) AND (bone age) AND (height) AND (less than 5th percentile) AND (mid parental height) AND (more than 10 cm below target height) AND (physical signs) AND ((serum luteinizing hormone) OR (testosterone)))"}
{"candidate_id": "LLM05250", "doc_id": "NCT02965443_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetes Age 18 - 75 years Anti-GAD antibodies negative (Glutamic Acid Decarboxylase) C-peptide levels = 1.5 ng/mL Fasting blood glucose > 126 mg/dl HbA1c 8.0 - 10.5 % BMI 25.0 - 45.0 kg/m2 Previous therapy with BBIT (basal insulin and at least once daily bolus insulin)", "candidate_expression": "((Age 18 - 75 years) AND (Anti-GAD antibodies (Glutamic Acid Decarboxylase) negative) AND (BBIT) AND (BMI 25.0 - 45.0 kg/m2) AND (C-peptide levels = 1.5 ng/mL) AND (Fasting blood glucose > 126 mg/dl) AND (HbA1c 8.0 - 10.5 %) AND (Type 2 diabetes) AND (basal insulin and at least once daily bolus insulin) AND (therapy Previous))"}
```
