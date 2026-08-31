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
{"candidate_id": "LLM00951", "doc_id": "NCT02652637_inc", "case_bucket": "other", "source_criterion": "Patients undergoing colon resection", "candidate_expression": "(colon resection undergoing)"}
{"candidate_id": "LLM00952", "doc_id": "NCT03198910_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00953", "doc_id": "NCT03465397_inc", "case_bucket": "or", "source_criterion": "Adult men and women (=18 years). Receptors of a first kidney transplant from an incompatible HLA living donor (at least 1 mismatch HLA at any antigenic level). AB0 compatible transplant. Patients with a calculated PRA of 0% by solid phase technique and absence of anti-HLA class I and class II antibodies by single antigen test (Luminex®). Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study. Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial. Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy. Patients must agree not to donate blood during treatment with MMF and during the 6 subsequent weeks. Males should not make a sperm donation during MMF treatment and up to 90 days after completion.", "candidate_expression": "((Adult) AND (Patients who agree to participate in the Trial by signing the Specific Informed Consent of this study.) AND (Potentially fertile women should use high reliability contraceptive methods (Pearl-Index <1) in order to avoid pregnancy during the entire duration of the study and up to 6 weeks after the end of their treatment with Mycophenolate Mofetil (MMF). Potentially Fertile Women include any woman who has experienced menarche and who has not undergone successful surgical sterilization (hysterectomy, bilateral tubal ligation or bilateral oophorectomy) or who is not post-menopausal (defined as amenorrhea = 12 consecutive months, or women who are receiving hormone replacement therapy with a documented level of follicle stimulating hormone (FSH)> 35 mlU / ml). Potentially fertile women must have a pregnancy test with a negative result in the 72 hours prior to the start of the trial.) AND (Sexually active males (including vasectomized males) who are being treated with MMF must accept the use of barrier contraceptive methods during MMF treatment and for 90 days thereafter. Potentially fertile partners of these patients should use a reliable contraceptive method during the same period, in order to minimize the risk of pregnancy.) AND (absence of anti-HLA class I) AND (absence of class II) AND (calculated PRA 0% solid phase technique) AND (first kidney transplant incompatible HLA living donor mismatch HLA) AND (men) AND (single antigen test (Luminex®)) AND (transplant AB0 compatible) AND (women) AND (years =18 years))"}
{"candidate_id": "LLM00954", "doc_id": "NCT01997112_exc", "case_bucket": "or", "source_criterion": "History of ischaemic heart disease, cardiac failure, cerebrovascular disease, liver impairment (ALT/AST>50IU/L) or stage 3-5 chronic kidney disease. History of overdose or suicidal ideation Patients weighing <55kgs. Patients with chronic pain requiring treatment, with a known allergy to paracetamol, or concomitant use of non-steroidal anti-inflammatories , oral anticoagulants or corticosteroids.", "candidate_expression": "((3-5) AND (<55kgs) AND (>50IU/L) AND (chronic kidney disease) AND (chronic pain) AND (concomitant) AND (known allergy) AND (paracetamol) AND (requiring treatment) AND (weighing) AND ((overdose) OR (suicidal ideation)) AND ((cardiac failure) OR (cerebrovascular disease) OR (ischaemic heart disease) OR (liver impairment) OR (stage)) AND ((corticosteroids) OR (non-steroidal anti-inflammatories) OR (oral anticoagulants)) AND ((ALT) OR (AST)))"}
{"candidate_id": "LLM00955", "doc_id": "NCT01051414_exc", "case_bucket": "or", "source_criterion": "Subjects with evidence of liver cirrhosis Evidence of HCC Co-infection with hepatitis B virus, HIV", "candidate_expression": "((HCC Evidence) AND (HIV) AND (hepatitis B virus) AND (liver cirrhosis evidence))"}
{"candidate_id": "LLM00956", "doc_id": "NCT01373684_exc", "case_bucket": "or", "source_criterion": "Treatment with any investigational drug within 30 days of entry to this protocol Current treatment with Telbivudine Severe hepatitis activity as documented by ALT>10 x ULN History of decompensated cirrhosis (defined as jaundice in the presence of cirrhosis, ascites, bleeding gastric or esophageal varices or encephalopathy) Pre-existent neutropenia (neutrophils <1,500/mm3) or thrombocytopenia (platelets < 90,000/mm3) Co-infection with hepatitis C virus, hepatitis D virus or human immunodeficiency virus (HIV) Other acquired or inherited causes of liver disease: alcoholic liver disease, obesity induced liver disease, drug related liver disease, auto-immune hepatitis, hemochromatosis, Wilson's disease or alpha-1 antitrypsin deficiency Alpha fetoprotein > 50 ng/ml Hyper- or hypothyroidism (subjects requiring medication to maintain TSH levels in the normal range are eligible if all other inclusion/exclusion criteria are met) Immune suppressive treatment within the previous 6 months Contra-indications for alfa-interferon therapy like suspected hypersensitivity to interferon or Peginterferon or any known pre-existing medical condition that could interfere with the patient's participation in and completion of the study. Pregnancy, breast-feeding Other significant medical illness that might interfere with this study: significant pulmonary dysfunction in the previous 6 months, malignancy other than skin basocellular carcinoma in previous 5 years, immunodeficiency syndromes (e.g. HIV positivity, auto-immune diseases, organ transplants other than cornea and hair transplant) Any medical condition requiring, or likely to require chronic systemic administration of steroids, during the course of the study Substance abuse, such as alcohol (>80 g/day), I.V. drugs and inhaled drugs in the past 2 years. Any other condition which in the opinion of the investigator would make the patient unsuitable for enrollment, or could interfere with the patient participating in and completing the study", "candidate_expression": "((ALT >10 x ULN) AND (Alpha fetoprotein > 50 ng/ml) AND (Co-infection hepatitis C virus hepatitis D virus human immunodeficiency virus) AND (Contra-indications) AND (HIV positivity) AND (Hyper thyroidism) AND (Immune suppressive treatment within the previous 6 months) AND (Peginterferon) AND (Pregnancy, breast-feeding) AND (Substance abuse in the past 2 years. alcohol I.V. drugs inhaled drugs) AND (Telbivudine) AND (Treatment with any investigational drug within 30 days of entry to this protocol) AND (Wilson's disease) AND (alcoholic liver disease) AND (alfa-interferon therapy) AND (alpha-1 antitrypsin deficiency) AND (ascites) AND (auto-immune diseases) AND (auto-immune hepatitis) AND (bleeding gastric) AND (cirrhosis) AND (cirrhosis decompensated) AND (cornea transplant) AND (drug related liver disease) AND (encephalopathy) AND (esophageal varices) AND (hair transplant) AND (hemochromatosis) AND (hepatitis Severe) AND (hypersensitivity) AND (hypothyroidism) AND (immunodeficiency syndromes) AND (interferon) AND (jaundice) AND (liver disease HIV acquired inherited) AND (malignancy) AND (medical illness significant) AND (medication) AND (neutropenia Pre-existent) AND (neutrophils <1,500/mm3) AND (obesity induced liver disease) AND (organ transplants) AND (platelets < 90,000/mm3) AND (pulmonary dysfunction significant in the previous 6 months) AND (systemic steroids chronic during the course of the study) AND (thrombocytopenia) AND NOT (skin basocellular carcinoma))"}
{"candidate_id": "LLM00957", "doc_id": "NCT03444142_exc", "case_bucket": "or", "source_criterion": "Women with confirmed or suspected pregnancy Women under lactation and/or puerperium Hypersensibility to ingredients of intervention Physical impossibility for apply the drug Known pancreatic, renal, hepatic, heart or thyroid diseased Hypertension diagnosis Previous treatment for glucose Body Mass Index =39.9 kg/m2 Triglycerides =500 mg/dL Total cholesterol =300 mg/dL Night or rotating shift workers Blood Pressure =140/90 mmHg", "candidate_expression": "((Blood Pressure =140/90 mmHg) AND (Body Mass Index =39.9 kg/m2) AND (Hypersensibility) AND (Hypertension) AND (Total cholesterol =300 mg/dL) AND (Triglycerides =500 mg/dL) AND (Women) AND (ingredients of intervention) AND (pregnancy) AND (treatment for glucose Previous) AND ((heart disease) OR (hepatic disease) OR (pancreatic disease) OR (renal disease) OR (thyroid disease)) AND ((Night shift workers) OR (rotating shift workers)) AND ((confirmed) OR (suspected)) AND ((lactation) OR (puerperium)))"}
{"candidate_id": "LLM00958", "doc_id": "NCT02946918_exc", "case_bucket": "or", "source_criterion": "AJCC Stage III or greater Undifferentiated, Anaplastic or Medullary Thyroid Cancer Planned postoperative TSH goal other than 0.1-0.5 mU/L History of gastrointestinal malabsorption or gastric bypass surgery Pregnancy Use of medications that alter the absorption or metabolism of levothyroxine Prior use of levothyroxine", "candidate_expression": "((AJCC Stage III or greater) AND (Pregnancy) AND (TSH postoperative 0.1-0.5 mU/L) AND (levothyroxine) AND (levothyroxine Prior) AND (medications) AND ((gastric bypass surgery) OR (gastrointestinal malabsorption)) AND ((absorption of levothyroxine) OR (metabolism of levothyroxine)) AND ((Anaplastic Thyroid Cancer) OR (Medullary Thyroid Cancer) OR (Undifferentiated Thyroid Cancer)))"}
{"candidate_id": "LLM00959", "doc_id": "NCT03190304_exc", "case_bucket": "or", "source_criterion": "History of hypersensitivity or allergy to any of the study drugs, drugs of similar chemical classes, ACE inhibitors (ACEIs), angiotensin II receptor blockers (ARBs), or neprilysin inhibitors, as well as known or suspected contraindications to the study drugs. Previous history of intolerance to recommended target doses of ACEIs or ARBs. Known history of angioedema. Requirement for treatment with both ACEIs and ARBs. Current acute decompensated heart failure (exacerbation of chronic heart failure manifested by signs and symptoms that may require intravenous therapy). Symptomatic hypotension. Estimated glomerular filtration rate (eGFR) <30%. Serum potassium >5.4 mmol/L. Acute coronary syndrome, stroke, transient ischaemic attack, cardiac, carotid, or other major cardiovascular surgery, percutaneous coronary intervention, or carotid angioplasty within the 3 months. Coronary or carotid artery disease likely to require surgical or percutaneous intervention within the 6 months. Implantation of a cardiac resynchronization therapy (CRT) device within 3 months or intent to implant a CRT. History of heart transplant or on a transplant list or with left ventricular (LV) assistance device. History of severe pulmonary disease. Diagnosis of peripartum- or chemotherapy-induced cardiomyopathy within the 12 months. Documented untreated ventricular arrhythmia with syncopal episodes within the 3 months. Symptomatic bradycardia or second- or third-degree atrioventricular block without a pacemaker. Presence of haemodynamically significant mitral and/or aortic valve disease, except mitral regurgitation secondary to LV dilatation. Presence of other haemodynamically significant obstructive lesions of the LV outflow tract, including aortic and subaortic stenosis. Any surgical or medical condition which might significantly alter the absorption, distribution, metabolism, or excretion of study drugs, including, but not limited to, any of the following: History of active inflammatory bowel disease during the 12 months. Active duodenal or gastric ulcers during the 3 months. Evidence of hepatic disease as determined by any one of the following: aspartate aminotransferase or alanine aminotransferase values exceeding 2x upper limit of normal, history of hepatic encephalopathy, history of oesophageal varices, or history of porto-caval shunt. Current treatment with cholestyramine or colestipol resins. Presence of any other disease with a life expectancy of <5 years.", "candidate_expression": "((ACE inhibitors (ACEIs)) AND (ACEIs) AND (ARBs) AND (Acute coronary syndrome) AND (CRT) AND (Coronary artery disease) AND (Estimated glomerular filtration rate (eGFR) <30%) AND (Implantation within 3 months) AND (LV dilatation haemodynamically significant) AND (Serum potassium >5.4 mmol/L) AND (alanine aminotransferase) AND (allergy) AND (alter the absorption, distribution, metabolism, or excretion) AND (angioedema history) AND (angiotensin II receptor blockers (ARBs)) AND (aortic stenosis) AND (aortic valve disease) AND (aspartate aminotransferase) AND (atrioventricular block) AND (bradycardia second- degree third-degree) AND (cardiac) AND (cardiac resynchronization therapy (CRT) device) AND (cardiomyopathy within the 12 months) AND (carotid) AND (carotid angioplasty) AND (carotid artery disease) AND (chemotherapy) AND (cholestyramine resins) AND (chronic heart failure) AND (colestipol resins) AND (contraindications) AND (disease any other life expectancy) AND (duodenal ulcers) AND (exacerbation) AND (gastric ulcers) AND (heart failure acute decompensated) AND (heart transplant History) AND (hepatic disease Evidence) AND (hepatic encephalopathy history) AND (hypersensitivity) AND (hypotension Symptomatic) AND (implant intent) AND (inflammatory bowel disease active during the 12 months) AND (intolerance Previous history) AND (intravenous therapy) AND (left ventricular (LV) assistance device) AND (major cardiovascular surgery) AND (medical condition) AND (mitral valve disease) AND (neprilysin inhibitors known suspected) AND (obstructive lesions LV outflow tract) AND (oesophageal varices history) AND (on a transplant list) AND (percutaneous coronary intervention) AND (percutaneous intervention) AND (peripartum peripartum- induced chemotherapy-induced) AND (porto-caval shunt history) AND (severe pulmonary disease History) AND (signs) AND (stroke) AND (study drugs) AND (subaortic stenosis) AND (surgical condition) AND (surgical intervention) AND (symptoms) AND (syncopal episodes within the 3 months) AND (transient ischaemic attack) AND (treatment Current) AND (treatment Requirement for) AND (ventricular arrhythmia untreated) AND NOT (pacemaker) AND NOT (mitral regurgitation secondary to LV dilatation))"}
{"candidate_id": "LLM00960", "doc_id": "NCT03056287_inc", "case_bucket": "or", "source_criterion": "1) age 50-70 2) stroke within the past 6 to 60 months, 3) major depressive disorder (PHQ-9 > 10) and diagnosed using the Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV), 4) residual paresis in the lower extremity (Fugl-Meyer LE motor score <34), 5) ability to walk without assistance and without an AFO on the treadmill ≥ 30 seconds at speeds ranging from 0.2-0.8 m/s, 6) no antidepressant medications or clinically able to discontinue medications, 7) HRSD question #9 regarding suicide <2, 8) provision of informed consent. In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.", "candidate_expression": "((50-70) AND (<2) AND (<34) AND (> 10) AND (AFO on the treadmill) AND (Fugl-Meyer LE motor score) AND (HRSD question #9) AND (In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.) AND (PHQ-9) AND (Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV)) AND (ability to walk without assistance) AND (age) AND (antidepressant) AND (clinically able to discontinue medications) AND (from 0.2-0.8 m/s) AND (lower extremity) AND (major depressive disorder) AND (no) AND (residual paresis) AND (speeds) AND (stroke) AND (within the past 6 to 60 months) AND (without) AND (≥ 30 seconds))"}
{"candidate_id": "LLM00961", "doc_id": "NCT03305575_exc", "case_bucket": "or", "source_criterion": "Abdominal and complex cervical cerclage (e.g. bulging bag) Contraindication to neuraxial anesthesia Known hypersensitivity to chloroprocaine (a.k.a. Ester allergy), paraaminobenzoic acid (PABA) or bupivacaine (a.k.a. Amide allergy) Pseudocholinesterase deficiency Concomitant use with ergot-type oxytocic drugs", "candidate_expression": "((Amide allergy) AND (Contraindication) AND (Ester allergy) AND (PABA) AND (Pseudocholinesterase deficiency) AND (bupivacaine) AND (cervical cerclage Abdominal complex bulging bag) AND (chloroprocaine) AND (ergot-type oxytocic drugs Concomitant) AND (hypersensitivity) AND (neuraxial anesthesia) AND (paraaminobenzoic acid))"}
{"candidate_id": "LLM00962", "doc_id": "NCT02483715_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((any kind) AND (bleeding) AND (concomitant) AND (during the course of the ulcer) AND (gastric surgery) AND (history of) AND (hypersensitivity) AND (illness) AND (in the previous month) AND (malignant tumor) AND (previous) AND (serious) AND (test drugs) AND (woman) AND ((PPIs) OR (antibiotics) OR (bismuth salts)) AND ((nursing) OR (pregnant)))"}
{"candidate_id": "LLM00963", "doc_id": "NCT00351611_exc", "case_bucket": "or", "source_criterion": "Pre-existing eye diseases (glaucoma). Insufficient response to pregabalin in the treatment of partial seizure, or patients currently receiving pregabalin treatment.", "candidate_expression": "((eye diseases Pre-existing) AND (glaucoma) AND (partial seizure) AND (pregabalin) AND ((Insufficient response) OR (pregabalin)))"}
{"candidate_id": "LLM00964", "doc_id": "NCT02254668_exc", "case_bucket": "or", "source_criterion": "Renal insufficiency (> 265 µmol/l) Incapability to give informed consent Cardiogenic shock of patient with KILLIP III or IV pregnant or breast feeding females insufficient contraception (only for substudy 3)", "candidate_expression": "((Cardiogenic shock) AND (III or IV) AND (Incapability to give informed consent) AND (KILLIP) AND (Renal insufficiency) AND (breast feeding) AND (contraception) AND (females) AND (insufficient) AND (pregnant))"}
{"candidate_id": "LLM00965", "doc_id": "NCT02137538_inc", "case_bucket": "or", "source_criterion": "Current height less than 5th percentile AND/OR Predicted adult height (based on bone age) more than 10 cm below target height (mid parental height) Evidence of puberty: physical signs and serum luteinizing hormone > 0.3 IU/L and testosterone > 15 ng/dl", "candidate_expression": "((> 0.3 IU/L) AND (> 15 ng/dl) AND (Current) AND (Evidence of puberty) AND (Predicted adult height) AND (bone age) AND (height) AND (less than 5th percentile) AND (mid parental height) AND (more than 10 cm below target height) AND (physical signs) AND (serum luteinizing hormone) AND (testosterone))"}
{"candidate_id": "LLM00966", "doc_id": "NCT02361905_inc", "case_bucket": "other", "source_criterion": "hypoechoic uterine leiomyoma (echogenicity <3), intramural leiomyomas with an ultrasonographic size <20 cm but >4cm, indication to surgery (symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain or pelvic pressure", "candidate_expression": "((<20 cm but >4cm) AND (<3) AND (echogenicity) AND (hypoechoic) AND (indication to) AND (infertility) AND (intramural leiomyomas) AND (menometrorrhagia) AND (menstrual disorder) AND (pelvic pain) AND (pelvic pressure) AND (surgery) AND (ultrasonographic size) AND (uterine leiomyoma))"}
{"candidate_id": "LLM00967", "doc_id": "NCT00324363_exc", "case_bucket": "or", "source_criterion": "Have participated in this study previously, or any other study using exenatide or GLP-1 analogs. Have participated in an interventional, medical, surgical, or pharmaceutical study within 30 days of screening. Have characteristics contraindicating metformin or sulfonylurea use. Have been treated with exogenous insulin for more than 1 week within the 3 months prior to screening. Have used drugs for weight loss within 1 month of screening.", "candidate_expression": "((GLP-1 analogs) AND (any other study) AND (characteristics contraindicating) AND (drugs for weight loss within 1 month of screening) AND (exenatide) AND (exogenous insulin for more than 1 week within the 3 months prior to screening) AND (interventional study) AND (medical study) AND (metformin) AND (pharmaceutical study) AND (sulfonylurea) AND (surgical study) AND (this study))"}
{"candidate_id": "LLM00968", "doc_id": "NCT01117181_exc", "case_bucket": "or", "source_criterion": "Meets criteria for Major Depressive Episode, by Diagnostic Statistical Manual of Mental Disorder - IV (TR) criteria Clinically significant agitation /aggression for which either 1) the frequency of agitation /aggression as assessed by the NPI is 'Very frequently', or 2) the frequency of agitation /aggression as assessed by the NPI is 'Frequently' AND the severity of the agitation as assessed by the NPI is 'Moderate', or 'Marked' Clinically significant delusions for which either 1) the frequency of delusions as assessed by the NPI is 'Very frequently', or 2) the frequency of delusions as assessed by the NPI is 'Frequently' AND the severity of the delusions as assessed by the NPI is 'Moderate', or 'Marked' Clinically significant hallucinations for which either 1) the frequency of hallucinations as assessed by the NPI is 'Very frequently', or 2) the frequency of hallucinations as assessed by the NPI is 'Frequently' AND the severity of the hallucinations as assessed by the NPI is 'Moderate', or 'Marked' Treatment with psychotropic medications in the 2 weeks prior to randomization with the exception of approved treatments for dementia (ChEIs and memantine), selective serotonin reuptake inhibitor antidepressants, and trazodone (if used as an aid to facilitate sleep and not as an antidepressant); other psychotropics (with the exclusion of antipsychotics), if stable for 3 months, may be allowed only with Steering Committee approval on a case by case basis. Note that antipsychotics are expressly prohibited. Treatment with methylphenidate is contraindicated in the opinion of the study physician Failure of treatment with methylphenidate in the past for apathy after convincing evidence of an adequate trial as judged by study physician Treatment with a medication that would prohibit the safe concurrent use of methylphenidate such as monoamine oxidase inhibitors and tricyclic antidepressants Need for acute psychiatric hospitalization or is suicidal Uncontrolled hypertension (medication non-compliance or past 3 months with a diastolic reading of 105 as verified by compartment pressure of the rectus sheath (CPRS)) Symptomatic coronary artery disease deemed to be significant by study physician at the time of screening Lack of appetite that results in significant unintentional weight loss as determined by the study physician in the last three months Significant communicative impairments Current participation in a clinical trial or in any study that may add significant burden or affect study outcomes Hyperthyroidism, advanced arteriosclerosis, symptomatic cardiovascular disease, serious structural cardiac abnormalities, cardiomyopathy, serious heart rhythm abnormalities, or a family history of sudden death or death related to heart problems Glaucoma, pheochromocytoma, or known or suspected hypersensitivity to methylphenidate or its excipients Central Nervous System (CNS) abnormalities (e.g., cerebral aneurysm) and/or other vascular abnormalities such as vasculitis or pre-existing stroke, motor tics or a family history or diagnosis of Tourette's syndrome, seizures (convulsions, epilepsy), or abnormal EEGs Any condition that, in the opinion of the study physician, makes it medically inappropriate or risky for the patient to enroll in the trial", "candidate_expression": "((Any condition that, in the opinion of the study physician, makes it medically inappropriate or risky for the patient to enroll in the trial) AND (Central Nervous System (CNS) abnormalities) AND (ChEIs) AND (Current participation in a clinical trial or in any study that may add significant burden or affect study outcomes) AND (Diagnostic Statistical Manual of Mental Disorder - IV (TR) criteria Meets) AND (EEGs abnormal) AND (Glaucoma) AND (Hyperthyroidism) AND (Lack of appetite in the last three months at the time of screening) AND (Major Depressive Episode) AND (NPI Frequently severity of the agitation) AND (NPI Frequently severity of the delusions) AND (NPI Frequently severity of the hallucinations) AND (NPI Moderate Marked) AND (NPI Very frequently) AND (NPI Very frequently frequency of agitation /aggression) AND (Tourette's syndrome) AND (Uncontrolled hypertension Uncontrolled) AND (agitation) AND (agitation /aggression) AND (agitation /aggression Clinically significant frequency of agitation /aggression) AND (arteriosclerosis advanced) AND (as judged by study physician) AND (cardiomyopathy) AND (cardiovascular disease symptomatic) AND (cerebral aneurysm) AND (communicative impairments Significant) AND (compartment pressure of the rectus sheath (CPRS)) AND (convulsions) AND (coronary artery disease Symptomatic) AND (death related to heart problems related to heart problems) AND (delusions) AND (delusions Clinically significant) AND (delusions frequency of delusions) AND (dementia) AND (diagnosis) AND (diastolic reading 105 as verified by compartment pressure of the rectus sheath (CPRS)) AND (epilepsy) AND (family history) AND (hallucinations) AND (hallucinations Clinically significant frequency of hallucinations) AND (hallucinations frequency of hallucinations) AND (heart rhythm abnormalities serious) AND (hypersensitivity) AND (its excipients) AND (known) AND (medication non-compliance past 3 months) AND (medication that would prohibit the safe concurrent use of methylphenidate) AND (memantine) AND (methylphenidate) AND (methylphenidate or its excipients) AND (methylphenidate prohibit concurrent) AND (monoamine oxidase inhibitors) AND (motor tics) AND (other psychotropics stable) AND (pheochromocytoma) AND (psychiatric hospitalization Need for acute) AND (psychotropic medications in the 2 weeks prior to randomization) AND (seizures) AND (selective serotonin reuptake inhibitor antidepressants) AND (stroke pre-existing) AND (structural cardiac abnormalities serious) AND (sudden death) AND (suicidal) AND (suspected) AND (trazodone) AND (treatments for dementia) AND (tricyclic antidepressants) AND (unintentional weight loss significant as determined by the study physician) AND (vascular abnormalities) AND (vasculitis) AND NOT (antipsychotics))"}
{"candidate_id": "LLM00969", "doc_id": "NCT02632266_exc", "case_bucket": "or", "source_criterion": "Newborn infants <28 weeks and >34 weeks gestation, those with life threatening illness, congenital and chromosomal anomalies, gastrointestinal anomalies or necrotizing enterocolitis and fed premature formula", "candidate_expression": "((Newborn infants) AND (fed premature formula) AND (gestation <28 weeks and >34 weeks) AND ((anomalies congenital) OR (chromosomal anomalies) OR (gastrointestinal anomalies) OR (life threatening illness) OR (necrotizing enterocolitis)))"}
{"candidate_id": "LLM00970", "doc_id": "NCT02393287_inc", "case_bucket": "or", "source_criterion": "1. Age ≥ 18 years 2. Patient with breast cancer, histologically proven, metastatic or locally advanced 3. Patient treated by Eribulin between January and October 2014 (for the retrospective part) or between November 2014 and September 2015 (for the prospective part). 4. Patient with at least an assessment of the response to Eribulin", "candidate_expression": "((Age ≥ 18 years) AND (Eribulin) AND (Eribulin between January and October 2014 between November 2014 and September 2015) AND (assessment of the response) AND (breast cancer) AND (histologically proven metastatic locally advanced))"}
{"candidate_id": "LLM00971", "doc_id": "NCT03008005_exc", "case_bucket": "or", "source_criterion": "clinically significant medical or neurologic condition or neurocognitive dysfunction that would affect function and/or task performance and/or interfere with the study protocol any current (or within past 2 months) medical condition requiring medication that would interact with dronabinol or interfere with the study protocol risk of harm to self or others that requires immediate intervention presence of contraindications, current or past allergic or adverse reaction, or known sensitivity to cannabinoid-like substances (dronabinol/marijuana/cannabis/THC, cannabinoid oil, sesame oil, gelatin, glycerin, and titanium dioxide) lack of fluency in English positive drug screen or alcohol breathalyzer unwilling/unable to sign informed consent document currently pregnant (positive pregnancy test), planning pregnancy, or lactating (women) under 18 or over 50 years of age traumatic brain injury (as defined by The American Congress of Rehabilitation as a person who has had a traumatically induced physiological disruption of brain function (i.e., the head being struck, the head striking an object, and/or the brain undergoing an acceleration/deceleration movement (i.e., whiplash) without direct external trauma to the head), as manifested by at least one of the following: any loss of consciousness; any loss of memory for events immediately before or after the injury; any alteration in mental status at the time of the incident; or focal neurological deficits that may or may not be transient) inability to tolerate small, enclosed spaces without anxiety (e.g. claustrophobia), as determined by self-report and/or a preliminary session in a mock scanner left-handed; presence of ferrous-containing metals within the body (e.g., aneurysm clips, shrapnel/retained particles) anticipation of a required drug test in the 4 weeks following the study. current diagnosis of a mood, anxiety, or other disorder that is more clinically salient than PTSD current moderate or severe alcohol/drug use disorder or in the past 8 weeks current or past diagnosis of bipolar and other related disorders, schizophrenia spectrum, or other psychotic disorders concomitant treatments with medication known to have drug interactions with dronabinol, such as, central nervous system depressants (barbiturates, benzodiazepines, buspirone, lithium, etc) and anticholinergic agents (atropine, scopolamine, antihistamines, etc).", "candidate_expression": "((PTSD) AND (adverse reaction) AND (age under 18 or over 50 years) AND (allergic reaction) AND (cannabinoid-like substances) AND (claustrophobia) AND (dronabinol) AND (drug interactions) AND (drug test anticipation of in the 4 weeks following the study) AND (ferrous-containing metals) AND (left-handed) AND (medical condition current within past 2 months) AND (medication) AND (pregnancy test positive) AND (pregnant currently) AND (self-report) AND (traumatic brain injury) AND (treatments) AND (unwilling/unable to sign informed consent document) AND NOT (tolerate small, enclosed spaces without anxiety inability) AND ((dronabinol would interact with) OR (interfere with the study protocol)) AND ((contraindications) OR (sensitivity)) AND ((current) OR (past)) AND ((THC) OR (cannabinoid oil) OR (cannabis) OR (dronabinol) OR (gelatin) OR (glycerin) OR (marijuana) OR (sesame oil) OR (titanium dioxide)) AND ((medical condition) OR (neurocognitive dysfunction) OR (neurologic condition)) AND ((alcohol breathalyzer) OR (drug screen)) AND ((lactating) OR (pregnancy planning)) AND ((aneurysm clips) OR (retained particles) OR (shrapnel)) AND ((anxiety disorder) OR (disorder other) OR (mood disorder)) AND ((moderate) OR (severe)) AND ((alcohol use disorder) OR (drug use disorder)) AND ((bipolar) OR (psychotic disorders) OR (related disorders other) OR (schizophrenia spectrum)) AND ((barbiturates) OR (benzodiazepines) OR (buspirone) OR (lithium)) AND ((anticholinergic agents) OR (central nervous system depressants)) AND ((antihistamines) OR (atropine) OR (scopolamine)))"}
{"candidate_id": "LLM00972", "doc_id": "NCT03446885_exc", "case_bucket": "or", "source_criterion": "any medical condition that would contraindicate use of stimulant medication any prior adverse response to lisdexamfetamine dimesylate or other stimulant medication use of concurrent,non-stimulant psychoactive medication diagnosis of schizophrenia or presence of thought disorder symptoms autism spectrum disorder", "candidate_expression": "((adverse response prior) AND (autism spectrum disorder) AND (contraindicate) AND (lisdexamfetamine dimesylate) AND (medical condition) AND (non-stimulant psychoactive medication concurrent) AND (schizophrenia) AND (stimulant medication) AND (stimulant medication other) AND (thought disorder symptoms))"}
{"candidate_id": "LLM00973", "doc_id": "NCT03360981_exc", "case_bucket": "or", "source_criterion": "acute myocardial infarction, heart failure, neoplastic disease, chronic diseases that may affect the inflammatory profile both systemic and epicardial (cancer, chronic intestinal inflammation, hepatitis, AIDS); life expectancy < 6 months, previous CABG and/or other open heart surgery intervention, acute coronary syndrome", "candidate_expression": "((< 6 months) AND (chronic diseases) AND (may affect the inflammatory profile) AND (other) AND (previous) AND ((AIDS) OR (cancer) OR (chronic intestinal inflammation) OR (hepatitis)) AND ((CABG) OR (acute coronary syndrome) OR (acute myocardial infarction) OR (heart failure) OR (life expectancy) OR (neoplastic disease) OR (open heart surgery intervention)) AND ((epicardial) OR (systemic)))"}
{"candidate_id": "LLM00974", "doc_id": "NCT02810704_exc", "case_bucket": "or", "source_criterion": "Patients undergoing bilateral hip or knee replacement; Patients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement; Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban; Patients who have a contraindication to two or more of the three study prophylaxis regimens; Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery; Patients on chronic (longer than the prior 6 months) anticoagulation other than with antiplatelet medications; Patients with documented gastrointestinal, cerebral, or other hemorrhage within 3 months of the operation; Patients with a known diagnosis of defective hemostasis and past history of clinical bleeding requiring transfusion and treatment; Patients who have had an operative procedure involving the eye, ear, or central nervous system within one month; Patients with severe uncontrolled hypertension with systolic BP > 220mmHg or diastolic BP > 120mmHg; Patients with an absolute body weight of less than 41 kilograms (90.4 lbs) at baseline visit; Vulnerable patient populations including prisoners and institutionalized individuals.", "candidate_expression": "((90.4 lbs) AND (> 120mmHg) AND (> 220mmHg) AND (Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban) AND (Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery) AND (anticoagulation) AND (antiplatelet) AND (atients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement;) AND (bilateral) AND (bleeding) AND (body weight) AND (contraindication) AND (defective) AND (hemostasis) AND (hypertension) AND (less than 41 kilograms) AND (longer than the prior 6 months) AND (operation) AND (operative procedure) AND (other than) AND (severe) AND (transfusion) AND (treatment) AND (uncontrolled) AND (within 3 months of the operation) AND (within one month) AND ((cerebral hemorrhage) OR (gastrointestinal hemorrhage) OR (hemorrhage)) AND ((hip replacement) OR (knee replacement)) AND ((central nervous system) OR (ear) OR (eye)) AND ((diastolic BP) OR (systolic BP)) AND ((institutionalized) OR (prisoners)) AND ((total hip replacement) OR (total knee replacement)))"}
{"candidate_id": "LLM00975", "doc_id": "NCT02609698_inc", "case_bucket": "other", "source_criterion": "Patients aged 19 or older Patients who have submitted a written consent to participate in the clinical trial De novo lesion Patients scheduled for elective intervention to treat ischemic cardiovascular disease", "candidate_expression": "((19 or older) AND (De novo lesion) AND (Patients scheduled for elective intervention to treat ischemic cardiovascular disease) AND (Patients who have submitted a written consent to participate in the clinical trial) AND (aged))"}
```
