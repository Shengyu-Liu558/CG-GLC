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
{"candidate_id": "LLM06351", "doc_id": "NCT02653131_exc", "case_bucket": "other", "source_criterion": "HPN < 12 months metabolically unstable cancer as the reason for intestinal failure", "candidate_expression": "((HPN < 12 months) AND (cancer) AND (intestinal failure) AND (metabolically unstable))"}
{"candidate_id": "LLM06352", "doc_id": "NCT02698969_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-II age between 18-80 years old dNMB with rocuronium during ear nose and throat (ENT) surgery", "candidate_expression": "((ASA physical status) AND (I-II) AND (age) AND (between 18-80 years) AND (dNMB with rocuronium) AND (ear nose and throat (ENT) surgery))"}
{"candidate_id": "LLM06353", "doc_id": "NCT02997215_exc", "case_bucket": "or", "source_criterion": "Open surgery; Patients allergic to lidocaine or other local anesthetics; Drug abuser.", "candidate_expression": "((Drug abuser) AND (Open surgery) AND (allergic) AND ((lidocaine) OR (local anesthetics other)))"}
{"candidate_id": "LLM06354", "doc_id": "NCT02705222_exc", "case_bucket": "or", "source_criterion": "Age < 45 or > 55 years. Blood disorders or coagulopathy. Diagnosed or suspected local gynecologic lesion (polyp, adenomyosis, myoma, malignancy or cervical pathology). Use intrauterine contraceptive device. Pregnancy related conditions.", "candidate_expression": "((Age < 45 or > 55 years) AND (Blood disorders) AND (Pregnancy) AND (adenomyosis) AND (cervical pathology) AND (coagulopathy Diagnosed suspected) AND (conditions Pregnancy related) AND (intrauterine contraceptive device) AND (local gynecologic lesion) AND (malignancy) AND (myoma) AND (polyp))"}
{"candidate_id": "LLM06355", "doc_id": "NCT01531257_inc", "case_bucket": "or", "source_criterion": "1. Male and female recipients of all races, ≥18 years of age. 2. Patients undergoing primary or subsequent deceased-donor or living donor kidney transplantation. 3. Subject and/or guardian must be able to provide informed consent. 4. Subject and/or guardian must be able to comply with the study protocol.", "candidate_expression": "((Male) AND (Subject and/or guardian must be able to comply with the study protocol.) AND (Subject and/or guardian must be able to provide informed consent.) AND (age) AND (deceased-donor kidney transplantation) AND (female) AND (living donor kidney transplantation) AND (primary) AND (subsequent) AND (≥18 years))"}
{"candidate_id": "LLM06356", "doc_id": "NCT03260881_exc", "case_bucket": "or", "source_criterion": "Patients with a personal or family history of medullary thyroid carcinoma or patients with Multiple Endocrine Neoplasia syndrome type 2 Patients with a prior serious hypersensitivity reaction to liraglutide Other contra-indications to liraglutide in accordance with risks and safety information included in the latest updated prescribing information Type 1 diabetes, as defined by ADA criteria Current use of other GLP-1A, dipeptidyl peptidase 4 (DPP4) or Sodium Glucose transporters 2 (SGLT2) inhibitors, thiazolidinediones (TZDs), pramlintide and fixed prandial insulin. Patients with unstable CAD, assessed by the Cardiology team and defined as new onset angina, rest angina, rapidly increasing or crescendo angina History of diabetic ketoacidosis, pancreas or beta-cell transplantation, or diabetes secondary to pancreatitis or pancreatectomy; acute or chronic infective diseases, cancer or chemotherapy, history of pulmonary, renal or liver diseases, and drug abuse Patients with chronic and acute inflammatory conditions such as sepsis, rheumatoid arthritis, ectopic dermatitis, asthma, ulcerative colitis. Current use of systemic corticosteroids in the 3 months prior this study. Pregnant or breast-feeding women Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)", "candidate_expression": "((ADA criteria) AND (Current) AND (Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)) AND (GLP-1A) AND (History) AND (Multiple Endocrine Neoplasia syndrome type 2) AND (Other) AND (Pregnant) AND (Sodium Glucose transporters 2 (SGLT2) inhibitors) AND (Type 1 diabetes) AND (acute) AND (asthma) AND (beta-cell transplantation) AND (breast-feeding women) AND (cancer) AND (chemotherapy) AND (chronic) AND (contra-indications) AND (crescendo angina) AND (diabetes) AND (diabetic ketoacidosis) AND (dipeptidyl peptidase 4 (DPP4) inhibitors) AND (drug abuse) AND (ectopic dermatitis) AND (family history) AND (hypersensitivity reaction) AND (in the 3 months prior this study) AND (infective diseases) AND (inflammatory conditions) AND (liraglutide) AND (liver diseases) AND (medullary thyroid carcinoma) AND (new onset angina) AND (other) AND (pancreas transplantation) AND (pancreatectomy) AND (pancreatitis) AND (personal history) AND (pramlintide) AND (prandial insulin) AND (prior) AND (pulmonary diseases) AND (rapidly increasing angina) AND (renal diseases) AND (rest angina) AND (rheumatoid arthritis) AND (secondary to) AND (sepsis) AND (serious) AND (systemic corticosteroids) AND (thiazolidinediones (TZDs)) AND (ulcerative colitis) AND (unstable CAD))"}
{"candidate_id": "LLM06357", "doc_id": "NCT03190304_inc", "case_bucket": "or", "source_criterion": "Symptomatic patients with heart failure (men and women) aged >18 years, Functional class II, III or IV by the New York Heart Association (NYHA) Left ventricular ejection fraction <35% Ischemic and nonischemic etiology Type B natriuretic peptide (BNP) >150 pg/ml (or pro-BNP [N-terminal-proBNP] = 600 pg / ml) or if the patient was hospitalized for cardiac decompensation within the preceding 12 months, BNP >100 pg/ml (or N-terminal-proBNP = 400 pg / ml)", "candidate_expression": "((BNP >100 pg/ml) AND (Ischemic etiology) AND (Left ventricular ejection fraction <35%) AND (N-terminal-proBNP = 400 pg / ml) AND (New York Heart Association (NYHA) Functional class II, III or IV) AND (Symptomatic) AND (Type B natriuretic peptide (BNP) >150 pg/ml) AND (aged >18 years) AND (cardiac decompensation) AND (heart failure) AND (hospitalized within the preceding 12 months) AND (men) AND (nonischemic etiology) AND (pro-BNP [N-terminal-proBNP] = 600 pg / ml) AND (women))"}
{"candidate_id": "LLM06358", "doc_id": "NCT02671318_exc", "case_bucket": "or", "source_criterion": "Re-transplant; Patients with any panel reactive antibody (PRA) equal to or above 50%, class I or class II; Acute rejection episode in the last 30 days, or episode > 2A in the Banff criteria; GFR (MDRD) < 40 ml/min; Proteinuria > 0,5 g/l; Hemoglobin < 10 g/l and/or leucocytes < 4000 cels/mm3 and/or platelets < 150.000 cels/mm3; Triglycerides > 500 mg/dl with or without use of fibrate; Cholesterol total > 300 mg/dl with or without use of statin; Hepatic abnormalities; Significant periphery edema; Pulmonary abnormalities or breast x-ray abnormalities; Hyper sensibility to sirolimus formula;", "candidate_expression": "((Acute rejection episode last 30 days class II) AND (Banff criteria > 2A) AND (Cholesterol total > 300 mg/dl) AND (GFR < 40 ml/min) AND (Hemoglobin < 10 g/l) AND (Hepatic abnormalities) AND (Hyper sensibility) AND (PRA equal to or above 50% class I) AND (Proteinuria > 0,5 g/l) AND (Pulmonary abnormalities) AND (Re-transplant) AND (Triglycerides > 500 mg/dl) AND (breast x-ray abnormalities) AND (fibrate) AND (leucocytes < 4000 cels/mm3) AND (panel reactive antibody) AND (periphery edema Significant) AND (platelets < 150.000 cels/mm3) AND (sirolimus) AND (statin))"}
{"candidate_id": "LLM06359", "doc_id": "NCT03340740_inc", "case_bucket": "other", "source_criterion": "History of allergic rhinitis Wheezing", "candidate_expression": "((Wheezing) AND (allergic rhinitis))"}
{"candidate_id": "LLM06360", "doc_id": "NCT02282319_inc", "case_bucket": "other", "source_criterion": "ASA (American Society of Anesthesiologists) class 1 & 2, undergoing day-case knee arthroscopy", "candidate_expression": "((ASA class 1 & 2) AND (knee arthroscopy))"}
{"candidate_id": "LLM06361", "doc_id": "NCT02167022_exc", "case_bucket": "other", "source_criterion": "1. Diagnosis: Diagnosis of CP secondary to neuronal migration. 2. Co-morbidities: Medical conditions that may prevent the administration of rehabilitation therapies at the intensity required by the study, or that may compromise the study ability to maintain blindness, or that have a co-morbidity not typically associated with CP (i.e. cancer, cystic fibrosis). 3. Co-interventions: Anticipated pharmacological intervention or procedure or participation in other studies that may interfere with this study.", "candidate_expression": "((CP secondary to neuronal migration) AND (Co-interventions: Anticipated pharmacological intervention or procedure or participation in other studies that may interfere with this study.))"}
{"candidate_id": "LLM06362", "doc_id": "NCT03484091_inc", "case_bucket": "other", "source_criterion": "Symptomatic primary knee osteoarthritis with failed conservative treatment at least 3 months Kellgren-Lawrence grade I-III Gave informed consent Can do questionnaires", "candidate_expression": "((Can do questionnaires) AND (Gave informed consent) AND (I-III) AND (Kellgren-Lawrence grade) AND (Symptomatic) AND (at least 3 months) AND (conservative treatment) AND (failed) AND (knee) AND (osteoarthritis) AND (primary))"}
{"candidate_id": "LLM06363", "doc_id": "NCT03477851_exc", "case_bucket": "or", "source_criterion": "No consent Spinal anesthesia or sciatic nerve block contraindicated Known intolerance to tramadol or other contraindications for the drug", "candidate_expression": "((No consent) AND (contraindicated) AND (contraindications other) AND (intolerance) AND (the drug) AND (tramadol) AND NOT (consent) AND ((Spinal anesthesia) OR (sciatic nerve block)))"}
{"candidate_id": "LLM06364", "doc_id": "NCT02560389_exc", "case_bucket": "or", "source_criterion": "Claustrophobia, or the inability to lie still in a confined space Major medical disorders (e.g., HIV, cancer) Magnetic metallic implants (such as screws, pins, shrapnel remnants, aneurysm clips, artificial heart valves, inner ear (cochlear) implants, artificial joints, and vascular stents) Electronic or magnetic implants, such as pacemakers Permanent makeup or tattoos with metallic dyes Currently pregnant A self-reported history of loss of consciousness (greater than 10 minutes) Physical disabilities that prohibit task performance (such as blindness or deafness) Psychotic disorders (e.g., schizophrenia) Any other condition that the investigator believes might put the participant at risk", "candidate_expression": "((Any other condition that the investigator believes might put the participant at risk) AND (Claustrophobia) AND (Magnetic metallic implants) AND (Major) AND (Physical disabilities that prohibit task performance) AND (Psychotic disorders) AND (cochlear implants) AND (greater than 10 minutes) AND (history of loss of consciousness) AND (inability to lie still in a confined space) AND (medical disorders) AND (metallic dyes) AND (pacemakers) AND (pregnant) AND (schizophrenia) AND (self-reported) AND ((aneurysm clips) OR (artificial heart valves) OR (artificial joints) OR (inner ear implants) OR (pins) OR (screws) OR (shrapnel remnants) OR (vascular stents)) AND ((Electronic implants) OR (magnetic implants)) AND ((Permanent makeup) OR (tattoos)) AND ((blindness) OR (deafness)) AND ((HIV) OR (cancer)))"}
{"candidate_id": "LLM06365", "doc_id": "NCT00379366_exc", "case_bucket": "other", "source_criterion": "contra-indications of radiotherapy angioplasty with stenting", "candidate_expression": "((angioplasty with stenting) AND (contra-indications) AND (radiotherapy))"}
{"candidate_id": "LLM06366", "doc_id": "NCT03460002_inc", "case_bucket": "other", "source_criterion": "Children aged 0-59 months living with families registered in the rural Bandim Health Project Health and Demographic Surveillance Site are included, provided a parent/guardian consent.", "candidate_expression": "((0-59 months) AND (Children) AND (Person Surveillance Site) AND (aged) AND (living with families registered in the rural Bandim Health Project Health))"}
{"candidate_id": "LLM06367", "doc_id": "NCT02733159_exc", "case_bucket": "or", "source_criterion": "Untreated symptomatic brain or leptomeningeal metastatic disease. Medical or psychiatric conditions comprising informed consent. Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol. Radiotherapy within 4 weeks of trial entry. Active autoimmune disease that has required systemic treatment in past 2 years Chronic usage of steroids or other immunosuppressant medication. Previous history of pneumonitis. Any evidence of clinical autoimmunity.", "candidate_expression": "((Active) AND (Any evidence of clinical autoimmunity) AND (Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol.) AND (Chronic usage) AND (Medical conditions) AND (Medical or psychiatric conditions comprising informed consent) AND (Radiotherapy) AND (Untreated) AND (autoimmune disease) AND (autoimmunity) AND (history) AND (immunosuppressant medication) AND (in past 2 years) AND (pneumonitis) AND (psychiatric conditions) AND (steroids) AND (symptomatic brain metastatic disease) AND (symptomatic leptomeningeal metastatic disease) AND (systemic treatment) AND (trial entry) AND (within 4 weeks of trial entry))"}
{"candidate_id": "LLM06368", "doc_id": "NCT02408120_inc", "case_bucket": "or", "source_criterion": "Subjects admitted to the hospital with acute or chronic medical illnesses or for elective and emergency surgical illness or trauma Known history of Type 2 diabetes mellitus for >3 months Treated with either diet alone, any combination of oral antidiabetic agents, non-insulin injectables or insulin therapy Blood glucose levels between >140 mg and <400 mg/dL without laboratory evidence of diabetic ketoacidosis", "candidate_expression": "((Blood glucose levels >140 mg and <400 mg/dL) AND (Type 2 diabetes mellitus >3 months) AND (admitted to the hospital) AND (medical illnesses) AND NOT (diabetic ketoacidosis laboratory evidence) AND ((diet) OR (insulin) OR (non-insulin injectables therapy) OR (oral antidiabetic agents)) AND ((acute) OR (chronic)) AND ((surgical illness) OR (trauma)) AND ((elective) OR (emergency)))"}
{"candidate_id": "LLM06369", "doc_id": "NCT03297944_exc", "case_bucket": "or", "source_criterion": "using daily medication for chronic condition acute narrow angle glaucoma previous adverse experience with study drugs experiences motion sickness in response to driving simulator BMI > 30 women who are pregnant, lactating, or planning on becoming pregnant regular use of tobacco products current substance use disorder clinically significant ECG current ongoing psychiatric disorder", "candidate_expression": "((> 30) AND (BMI) AND (ECG) AND (acute) AND (adverse experience) AND (chronic condition) AND (clinically significant) AND (current) AND (daily) AND (lactating) AND (medication) AND (motion sickness) AND (narrow angle glaucoma) AND (ongoing) AND (planning on becoming) AND (pregnant) AND (previous) AND (psychiatric disorder) AND (regular) AND (study drugs) AND (substance use disorder) AND (use of tobacco products) AND (women))"}
{"candidate_id": "LLM06370", "doc_id": "NCT02464813_exc", "case_bucket": "or", "source_criterion": "Other spinal pathology or other associated medical condition Major neurologic developmental delay Need for anterior surgery or for vertebral column resection. Preoperative opioid use Inability to use PCA", "candidate_expression": "((Inability to use) AND (Major neurologic developmental delay) AND (PCA) AND (opioid Preoperative) AND ((associated medical condition) OR (spinal pathology)) AND ((anterior surgery Need for) OR (vertebral column resection)))"}
{"candidate_id": "LLM06371", "doc_id": "NCT03355469_exc", "case_bucket": "or", "source_criterion": "Morbidly obese patients (BMI >47 kg/m2) and overweight/lean patients (BMI <27 kg/m2) Evidence of type 1 diabetes and diabetics requiring insulin therapy. Subjects who have not been weight stable (>2 kg weight change in past 3 months) Subjects who have been recently active (>30 min of moderate/high intensity exercise, 2 times/week). Subjects who are smokers or who have quit smoking <5 years ago Subjects prescribed metformin or have taken metformin within 1 year. Subjects with abnormal estimated glomerular filtration rate (eGFR). Hypertriglyceridemic (>400 mg/dl) and hypercholesterolemic (>260 mg/dl) subjects Hypertensive (>160/100 mmHg) Subjects currently taking medications that affect heart rate and rhythm (i.e. Ca++ channel blockers, nitrates, alpha- or beta-blockers). Subjects with a history of significant metabolic, cardiac, congestive heart failure, cerebrovascular, hematological, pulmonary, gastrointestinal, liver, renal, or endocrine disease or cancer that in the investigator's opinion would interfere with or alter the outcome measures, or impact subject safety. Pregnant (as evidenced by positive pregnancy test) or nursing women Subjects with contraindications to participation in an exercise training program Currently taking active weight suppression medication (e.g. phentermine,orlistat, lorcaserin, naltrexone-bupropion in combination, liraglutide, benzephetamine, diethylpropion, phendimetrazine) Known hypersensitivity to perflutren (contained in Definity)", "candidate_expression": "((2 times/week) AND (<27 kg/m2) AND (<5 years ago) AND (>160/100 mmHg) AND (>2 kg) AND (>260 mg/dl) AND (>30 min) AND (>400 mg/dl) AND (>47 kg/m2) AND (BMI) AND (Definity) AND (Hypertensive) AND (Hypertriglyceridemic) AND (Morbidly obese) AND (abnormal) AND (active) AND (active weight suppression medication) AND (cholesterol) AND (congestive heart failure) AND (contraindications) AND (estimated glomerular filtration rate (eGFR)) AND (history) AND (hypersensitivity) AND (in past 3 months) AND (insulin) AND (insulin therapy) AND (medications) AND (moderate/high intensity exercise) AND (not) AND (participation in an exercise training program) AND (perflutren) AND (positive) AND (pregnancy test) AND (recently) AND (requiring insulin therapy) AND (significant) AND (that affect heart rate) AND (that affect heart rhythm) AND (weight change) AND (weight stable) AND (within 1 year) AND (women) AND ((diabetics) OR (type 1 diabetes)) AND ((quit smoking) OR (smokers)) AND ((metformin)) AND ((Hypertriglyceridemic) OR (hypercholesterolemic)) AND ((lean) OR (overweight)) AND ((Ca++ channel blockers) OR (alpha- blockers) OR (beta-blockers) OR (nitrates)) AND ((cardiac) OR (cerebrovascular) OR (endocrine) OR (gastrointestinal) OR (hematological) OR (liver) OR (metabolic) OR (pulmonary) OR (renal)) AND ((cancer) OR (disease)) AND ((Pregnant) OR (nursing)) AND ((benzephetamine) OR (diethylpropion) OR (liraglutide) OR (lorcaserin) OR (naltrexone-bupropion in combination) OR (orlistat) OR (phendimetrazine) OR (phentermine)))"}
{"candidate_id": "LLM06372", "doc_id": "NCT02984475_exc", "case_bucket": "or", "source_criterion": "Patients with renal impairment (serum creatinine more than twice the upper limit of normal). Patients with heart failure. Patients with sepsis or active infection. Patients with diabetes mellitus (either primary or secondary to thalassemia). regular consumption of medication with potential hepatotoxicity. regular herbal medicine or antioxidant supplementation. patients with gastrointestinal conditions preventing adsorption of oral medication.", "candidate_expression": "((diabetes mellitus) AND (heart failure) AND (hepatotoxicity) AND (medication) AND (more than twice the upper limit of normal) AND (renal impairment) AND (serum creatinine) AND ((antioxidant supplementation) OR (herbal medicine)) AND ((active infection) OR (sepsis)) AND ((primary) OR (secondary to thalassemia)))"}
{"candidate_id": "LLM06373", "doc_id": "NCT02102243_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure or coronary artery disease Blood pressure averaging > 159/99 mmHg Serum creatinine > 1.5 mg/dL Diabetes mellitus or other systemic illness Left ventricular hypertrophy by echocardiography or ECG Pregnancy Hypersensitivity to spironolactone, chlorthalidone, amlodipine, human recombinant insulin or Definity Any history of substance abuse (other than tobacco) History of gouty arthritis Patients with right-to-left, bi-directional, or transient right-to-left cardiac shunts Hypersensitivity to perflutren, blood, blood products or albumin", "candidate_expression": "((> 1.5 mg/dL) AND (> 159/99 mmHg) AND (Blood pressure) AND (ECG) AND (Hypersensitivity) AND (Left ventricular hypertrophy) AND (Pregnancy) AND (Serum creatinine) AND (cardiac shunts) AND (echocardiography) AND (gouty arthritis) AND (other) AND (right-to-left) AND (substance abuse) AND (tobacco) AND (transient) AND ((Congestive heart failure) OR (coronary artery disease)) AND ((amlodipine) OR (chlorthalidone) OR (human recombinant insulin) OR (spironolactone)) AND ((bi-directional) OR (right-to-left,)) AND ((albumin) OR (blood) OR (blood products) OR (perflutren)) AND ((Diabetes mellitus) OR (systemic illness)))"}
{"candidate_id": "LLM06374", "doc_id": "NCT01793519_exc", "case_bucket": "or", "source_criterion": "Had dose increase of anti-TNF agent or DMARD in the last 6 months Had change of anti-TNF agent or DMARD in the last 6 months Treated currently with golimumab or certolizumab Treated with greater than 10 mg of prednisone (or equivalent) daily in the last 6 months Treated with greater than 5 mg of prednisone (or equivalent) daily in the last 3 months Treated with intramuscular or intravenous corticosteroids in the last 6 months for RA activity Treated with anakinra, abatacept, or tocilizumab in the last 6 months Treated with rituximab in the last 12 months Treated with an investigational RA drug in the last 6 months Pregnant (or anticipate pregnancy during the study period) or lactating women Absence of documentation in the medical record of clinical remission for the last 6 months Unwilling to discontinue anti-TNF agent Absence of documentation of negative tuberculin skin test, negative QuantiFERON-TB Gold test, or treatment for latent tuberculosis prior to starting treatment with the anti-TNF agent Treatment of solid malignancy or non-melanoma skin cancer within the past 5 years, or any history of melanoma or hematologic or lymphoproliferative malignancy Absence of documentation of age-appropriate cancer screening at the time of randomization Absence of documentation of negative hepatitis B serologies, absence of completion of treatment for chronic hepatitis B, or absence of suppressive antiviral treatment Unable to provide informed consent Anticipate not being available or able to comply with the schedule of study visits", "candidate_expression": "((Absence of) AND (Anticipate not being available or able to comply with the schedule of study visits) AND (DMARD) AND (Pregnant) AND (QuantiFERON-TB Gold test) AND (RA) AND (RA drug) AND (Unable to provide informed consent) AND (Unwilling) AND (abatacept) AND (absence) AND (absence of) AND (age-appropriate) AND (anakinra) AND (anti-TNF agent) AND (anticipate during the study period) AND (at the time of randomization) AND (cancer screening) AND (certolizumab) AND (change) AND (chronic hepatitis B) AND (clinical remission) AND (corticosteroids) AND (daily) AND (discontinue) AND (dose increase) AND (for the last 6 months) AND (golimumab) AND (greater than 10 mg) AND (greater than 5 mg) AND (hematologic) AND (hepatitis B serologies) AND (in the last 12 months) AND (in the last 3 months) AND (in the last 6 months) AND (intramuscular) AND (intravenous) AND (investigational) AND (lactating) AND (latent) AND (lymphoproliferative malignancy) AND (melanoma) AND (negative) AND (non-melanoma skin cancer) AND (prednisone) AND (pregnancy) AND (prior to starting treatment with the anti-TNF agent) AND (rituximab) AND (solid malignancy) AND (starting treatment with the anti-TNF agent) AND (suppressive antiviral treatment) AND (the time of randomization) AND (tocilizumab) AND (treatment) AND (treatment with the anti-TNF agent) AND (tuberculin skin test) AND (tuberculosis) AND (within the past 5 years) AND (women))"}
{"candidate_id": "LLM06375", "doc_id": "NCT03070847_inc", "case_bucket": "other", "source_criterion": "age > 18 y.o. American Society of Anesthesiologists Physical Status Classification (ASA) 1-2 signed informed consent form after reading the information about the study and talking with one of the investigators", "candidate_expression": "((1-2) AND (> 18 y.o) AND (ASA) AND (American Society of Anesthesiologists Physical Status Classification) AND (age) AND (signed informed consent form after reading the information about the study and talking with one of the investigators))"}
```
