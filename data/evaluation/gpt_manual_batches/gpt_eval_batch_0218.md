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
{"candidate_id": "LLM05426", "doc_id": "NCT02596555_inc", "case_bucket": "or", "source_criterion": "Age =18 years Objectively confirmed diagnosis of acute PE by multidetector CT angiography, ventilation/perfusion lung scan, or selective invasive pulmonary angiography, according to established diagnostic criteria, with or without symptomatic deep vein thrombosis Absence of hemodynamic collapse, or decompensation, at presentation; Hemodynamic collapse or decompensation At least one sign of RV pressure overload/dysfunction on CT angiography or echocardiography Signs of myocardial injury as indicated by elevated troponin levels Signs of (RV) failure as indicated by NT-proBNP levels >600 pg/ml at baseline. Ability of the subject to understand the character and individual consequences of the clinical trial; signed and dated informed consent of the subject available before the start of any specific trial procedures", "candidate_expression": "((=18 years) AND (>600 pg/ml) AND (Ability of the subject to understand the character and individual consequences of the clinical trial; signed and dated informed consent of the subject available before the start of any specific trial procedures) AND (Absence) AND (Age) AND (At least one) AND (NT-proBNP levels) AND (PE) AND (RV) failure) AND (acute) AND (deep vein thrombosis) AND (elevated) AND (myocardial injury) AND (troponin levels) AND ((hemodynamic collapse) OR (hemodynamic decompensation)) AND ((sign of RV pressure dysfunction) OR (sign of RV pressure overload)) AND ((CT angiography) OR (echocardiography)) AND ((CT angiography) OR (invasive pulmonary angiography,) OR (ventilation/perfusion lung scan)))"}
{"candidate_id": "LLM05427", "doc_id": "NCT02653131_inc", "case_bucket": "or", "source_criterion": "patients receiving home parenteral nutrition (HPN) because of short bowel syndrome for at least 12 months stable metabolic status benign disease", "candidate_expression": "((benign disease) AND (home parenteral nutrition (HPN)) AND (metabolic status stable) AND (short bowel syndrome))"}
{"candidate_id": "LLM05428", "doc_id": "NCT02164734_exc", "case_bucket": "or", "source_criterion": "Weight < 800 g; Airway anomalies; Pulmonary air leaks; Craniofacial or cardiothoracic malformations", "candidate_expression": "((Airway anomalies) AND (Craniofacial malformations) AND (Pulmonary air leaks) AND (Weight < 800 g) AND (cardiothoracic malformations))"}
{"candidate_id": "LLM05429", "doc_id": "NCT02637453_exc", "case_bucket": "or", "source_criterion": "With acute diseases, such as acute phase after myocardial infarction (within 3 months), within 3 months after acute heart failure or new cerebral infarction; In the list of heart transplantation; Expected survival less than 1 year; With other hemorrhagic diseases and anticoagulant therapy is not allowed; Thrombosis in left atrium; Heart failure, New York Heart Association(NYHA) III/IV or eject fraction(EF)<40%; Patients with uncontrolled cancer; Significant hepatic or renal impairment (and/or alanine transaminase(ALT) or Aspartate transaminase(AST) >2 times upper limit of normal, creatinine clearance rate(CCr)<50%); Previous catheter radiofrequency ablation for AF or cardiac surgery; Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.", "candidate_expression": "((<40%) AND (<50%) AND (>2 times upper limit of normal) AND (AF) AND (Expected survival) AND (III/IV) AND (In the list) AND (Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.) AND (Significant) AND (Thrombosis) AND (acute diseases) AND (acute phase) AND (anticoagulant therapy) AND (cancer) AND (heart transplantation) AND (hemorrhagic diseases) AND (left atrium) AND (less than 1 year) AND (myocardial infarction) AND (not allowed) AND (other) AND (uncontrolled) AND (within 3 months) AND ((Heart failure) OR (New York Heart Association(NYHA)) OR (eject fraction(EF))) AND ((hepatic impairment) OR (renal impairment)) AND ((Aspartate transaminase(AST)) OR (alanine transaminase(ALT)) OR (creatinine clearance rate(CCr))) AND ((cardiac surgery) OR (catheter radiofrequency ablation)) AND ((acute heart failure) OR (cerebral infarction)))"}
{"candidate_id": "LLM05430", "doc_id": "NCT03464552_inc", "case_bucket": "other", "source_criterion": "Females 18-65 years old who undergoing colposcopic directed biopsy", "candidate_expression": "((Females) AND (colposcopic directed biopsy undergoing) AND (old 18-65 years))"}
{"candidate_id": "LLM05431", "doc_id": "NCT02671318_exc", "case_bucket": "or", "source_criterion": "Re-transplant; Patients with any panel reactive antibody (PRA) equal to or above 50%, class I or class II; Acute rejection episode in the last 30 days, or episode > 2A in the Banff criteria; GFR (MDRD) < 40 ml/min; Proteinuria > 0,5 g/l; Hemoglobin < 10 g/l and/or leucocytes < 4000 cels/mm3 and/or platelets < 150.000 cels/mm3; Triglycerides > 500 mg/dl with or without use of fibrate; Cholesterol total > 300 mg/dl with or without use of statin; Hepatic abnormalities; Significant periphery edema; Pulmonary abnormalities or breast x-ray abnormalities; Hyper sensibility to sirolimus formula;", "candidate_expression": "((Cholesterol total > 300 mg/dl) AND (GFR < 40 ml/min) AND (Hepatic abnormalities) AND (Hyper sensibility) AND (PRA) AND (Proteinuria > 0,5 g/l) AND (Pulmonary abnormalities) AND (Re-transplant) AND (Triglycerides > 500 mg/dl) AND (breast x-ray abnormalities) AND (fibrate) AND (panel reactive antibody) AND (periphery edema Significant) AND (sirolimus) AND (statin) AND ((Hemoglobin < 10 g/l) OR (leucocytes < 4000 cels/mm3) OR (platelets < 150.000 cels/mm3)) AND ((class I) OR (class II) OR (equal to or above 50%)) AND ((Acute rejection episode last 30 days) OR (Banff criteria > 2A)))"}
{"candidate_id": "LLM05432", "doc_id": "NCT02455921_exc", "case_bucket": "other", "source_criterion": "Parents refusal Cognitive impairment Difficulty in communication due to language issues Psychiatric disorder Severe systematic disorder Known allergy to any drug used", "candidate_expression": "((Cognitive impairment) AND (Difficulty in communication) AND (Known allergy) AND (Parents refusal) AND (Psychiatric disorder) AND (Severe systematic disorder) AND (any drug used) AND (language issues))"}
{"candidate_id": "LLM05433", "doc_id": "NCT00236340_inc", "case_bucket": "or", "source_criterion": "Pregnant women with abdomen discumfort and ultrasound diagnosis of polyhydramnios (AFI>25cm) Single or twin pregnancies", "candidate_expression": "((>25cm) AND (AFI) AND (Pregnant) AND (abdomen discumfort) AND (diagnosis) AND (polyhydramnios) AND (pregnancies) AND (ultrasound) AND (women) AND ((Single) OR (twin)))"}
{"candidate_id": "LLM05434", "doc_id": "NCT03350815_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05435", "doc_id": "NCT03500211_exc", "case_bucket": "or", "source_criterion": "Patients requiring emergent cesarean birth Patients allergic to lidocaine or adhesive Patients who have already received an epidural during this admission or requiring general anesthesia for cesarean birth Patients using chronic oral neuromodulators Patients with cardiac disease or using anti-arrhythmic agents Patients with fibromyalgia or chronic pain syndromes such as rheumatoid arthritis, osteoarthritis, or lupus. Daily narcotic or opiate use for greater than the 2 months prior to enrollment in the study.", "candidate_expression": "((adhesive) AND (allergic) AND (anti-arrhythmic agents) AND (cardiac disease) AND (cesarean birth) AND (chronic oral neuromodulators) AND (chronic pain syndromes) AND (emergent cesarean birth) AND (epidural during this admission) AND (fibromyalgia) AND (general anesthesia requiring) AND (lidocaine) AND (lupus) AND (narcotic) AND (opiate) AND (osteoarthritis) AND (rheumatoid arthritis))"}
{"candidate_id": "LLM05436", "doc_id": "NCT03373669_inc", "case_bucket": "other", "source_criterion": "Age =1 year, stratified into different age groups Living in the Waya Clinic Catchment Area Good health condition, without clinically significant medical history (by participant or guardian, in case of minor) Not pregnant for female subjects. Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening. Signed informed consent", "candidate_expression": "((Age =1 year) AND (Available to participate for the study duration, including all planned follow-up visits for up to 9 months from screening.) AND (Good health condition) AND (Living) AND (Signed informed consent) AND (Waya Clinic Catchment Area) AND (female) AND NOT (pregnant) AND NOT (medical history clinically significant))"}
{"candidate_id": "LLM05437", "doc_id": "NCT00317148_inc", "case_bucket": "other", "source_criterion": "Healthy postmenopausal women with 50 or more moderate to severe hot flushes. Women between 40 to 70 years of age.", "candidate_expression": "((50 or more) AND (Healthy) AND (Women) AND (age) AND (between 40 to 70 years) AND (moderate to severe hot flushes) AND (postmenopausal) AND (women))"}
{"candidate_id": "LLM05438", "doc_id": "NCT02083991_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus or plasma glucose >11,1 at admission. Receiving steroids at the time of transplantation or likely to need steroids after transplantation. Multiorgan transplants and/or previously transplanted with any other organ than kidney. Panel reacting antibodies(PRA) >25% in most recent test or considered to be of high risk for rejection which requires an enhanced immunosuppression. Renal transplants from HLA-identical sibling. Hypersensitivity to, or disability to take immunosuppressive drugs. Blood group(ABO)-incompatible transplants. Unlikely to comply with the study requirements. Transplant from donor positive for HIV, HBsAg, Hepatitis C. Female of childbearing potential planing/being pregnant or unwilling to use contraception.", "candidate_expression": "((Female of childbearing potential planing/being pregnant or unwilling to use contraception.) AND (Renal transplants HLA-identical sibling) AND (Transplant donor) AND (enhanced immunosuppression) AND (immunosuppressive drugs) AND (steroids) AND (transplants Blood group(ABO)-incompatible) AND ((Diabetes mellitus) OR (plasma glucose >11,1 at admission)) AND ((Multiorgan transplants) OR (transplanted with any other organ than kidney previously)) AND ((Panel reacting antibodies(PRA) >25% most recent test) OR (rejection considered to be of high risk)) AND ((Hypersensitivity) OR (disability)) AND ((positive for HBsAg) OR (positive for HIV) OR (positive for Hepatitis C)) AND ((Receiving at the time of transplantation) OR (steroids likely to need after transplantation)))"}
{"candidate_id": "LLM05439", "doc_id": "NCT03209687_inc", "case_bucket": "other", "source_criterion": "Females undergoing Intra-Cytoplasmic Sperm Injection (ICSI) cycles Age between 20 and 40 years", "candidate_expression": "((Age) AND (Females) AND (Intra-Cytoplasmic Sperm Injection (ICSI) cycles) AND (between 20 and 40 years) AND (undergoing))"}
{"candidate_id": "LLM05440", "doc_id": "NCT03532620_exc", "case_bucket": "or", "source_criterion": "Past history of hypersensitivity to the study drug; Diagnosed diabetes; Severe liver disease (including ALT or AST=2.5-fold the normal upper limit), biliary obstruction; Ongoing treatment with cyclosporine within 2 weeks; Renal dysfunction, including endogenous creatinine clearance male<120ml/min, female<105ml/min, serum creatinine=2mg/dl (186umol/L), Renal function progressive decline, GFR<30ml•min-1•1.73m-2; Diagnosed or past history of ASCVD (including ACS, SCAD, revascularization, ICM, ischemic stroke, TIA, PASD, etc. SBP=180mmHg, or DBP=110mmHg; Ongoing treatment with Beta blockers, Diuretic; Secondary hypertension, including SAS, PA, RAS, pheochromocytoma, Cushing's syndrome, aorta diseases, drug induced hypertension; Ongoing treatment with statins, fibrates, and/or cation exchange resins within 2 weeks; Pancreatic disease; History of gastrectomy, short bowel syndrome; Ongoing hormone replacement therapy; Diagnosed or suspected malignant tumor; Familial hypercholesterolemia; Any diseases may limit the efficacy or safety of the study; Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation; IFG impaired fast glucose, FPG fasting plasma glucose, IGT impaired glucose tolerance, OGTT oral glucose tolerance test, PG plasma glucose, HbA1C hemoglobin A1C, LDL-C low-density lipoprotein cholesterol, TG triglycerides, SBP systolic blood pressure, DBP diastolic blood pressure, ALT alanine aminotransferase, AST aspartate aminotransferase, GFR glomerular filtration rate, ASCVD arteriosclerotic cardiovascular disease, ACS acute coronary syndrome, SCAD stable coronary artery disease, ICM ischemic cardiomyopathy, TIA transient ischemic attack, PASD peripheral atherosclerotic disease, SAS sleep apnea syndrome, PA primary aldosteronism, RAS renal arterial stenosis", "candidate_expression": "((ACS) AND (ALT) AND (ASCVD) AND (AST) AND (Beta blockers) AND (Cushing's syndrome) AND (DBP =110mmHg) AND (Diuretic) AND (Familial hypercholesterolemia) AND (GFR <30ml•min-1•1.73m-2) AND (ICM) AND (PA) AND (PASD) AND (Pancreatic disease) AND (Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation) AND (RAS) AND (Renal dysfunction) AND (Renal function progressive decline) AND (SAS) AND (SBP =180mmHg) AND (SCAD) AND (Secondary hypertension) AND (TIA) AND (aorta diseases) AND (biliary obstruction) AND (cation exchange resins) AND (cyclosporine) AND (diabetes) AND (endogenous creatinine clearance) AND (female <105ml/min) AND (fibrates) AND (gastrectomy) AND (hormone replacement therapy Ongoing Diagnosed suspected) AND (hypersensitivity) AND (hypertension drug induced) AND (ischemic stroke) AND (liver disease Severe) AND (male <120ml/min) AND (malignant tumor) AND (pheochromocytoma) AND (revascularization) AND (serum creatinine =2mg/dl 186umol/L) AND (short bowel syndrome) AND (statins) AND (study drug) AND (treatment Ongoing) AND (treatment Ongoing within 2 weeks))"}
{"candidate_id": "LLM05441", "doc_id": "NCT01639664_exc", "case_bucket": "or", "source_criterion": "Age less than 14 years Pregnancy Estimated life expectancy (due to comorbidities) less than 90 days Presence of relative or absolute contraindications to CPFA Admission from an other ICU where the patient remained for more than 24 hours Absence of informed consent", "candidate_expression": "((Absence of informed consent) AND (Admission) AND (Age less than 14 years) AND (CPFA) AND (Estimated life expectancy less than 90 days) AND (Pregnancy) AND (an other ICU patient remained) AND ((absolute contraindications) OR (relative contraindications)))"}
{"candidate_id": "LLM05442", "doc_id": "NCT03355469_exc", "case_bucket": "or", "source_criterion": "Morbidly obese patients (BMI >47 kg/m2) and overweight/lean patients (BMI <27 kg/m2) Evidence of type 1 diabetes and diabetics requiring insulin therapy. Subjects who have not been weight stable (>2 kg weight change in past 3 months) Subjects who have been recently active (>30 min of moderate/high intensity exercise, 2 times/week). Subjects who are smokers or who have quit smoking <5 years ago Subjects prescribed metformin or have taken metformin within 1 year. Subjects with abnormal estimated glomerular filtration rate (eGFR). Hypertriglyceridemic (>400 mg/dl) and hypercholesterolemic (>260 mg/dl) subjects Hypertensive (>160/100 mmHg) Subjects currently taking medications that affect heart rate and rhythm (i.e. Ca++ channel blockers, nitrates, alpha- or beta-blockers). Subjects with a history of significant metabolic, cardiac, congestive heart failure, cerebrovascular, hematological, pulmonary, gastrointestinal, liver, renal, or endocrine disease or cancer that in the investigator's opinion would interfere with or alter the outcome measures, or impact subject safety. Pregnant (as evidenced by positive pregnancy test) or nursing women Subjects with contraindications to participation in an exercise training program Currently taking active weight suppression medication (e.g. phentermine,orlistat, lorcaserin, naltrexone-bupropion in combination, liraglutide, benzephetamine, diethylpropion, phendimetrazine) Known hypersensitivity to perflutren (contained in Definity)", "candidate_expression": "((BMI <27 kg/m2) AND (BMI >47 kg/m2) AND (Definity) AND (Hypertensive) AND (Hypertensive >160/100 mmHg) AND (Hypertriglyceridemic >400 mg/dl) AND (Morbidly obese) AND (active) AND (active weight suppression medication) AND (cholesterol >260 mg/dl) AND (congestive heart failure) AND (contraindications participation in an exercise training program) AND (estimated glomerular filtration rate (eGFR) abnormal) AND (hypersensitivity) AND (insulin) AND (insulin therapy) AND (medications that affect heart rhythm that affect heart rate) AND (moderate/high intensity exercise >30 min 2 times/week) AND (perflutren) AND (pregnancy test positive) AND (weight change >2 kg in past 3 months) AND (women) AND NOT (weight stable) AND ((diabetics requiring insulin therapy) OR (type 1 diabetes)) AND ((quit smoking <5 years ago) OR (smokers)) AND ((metformin) OR (metformin within 1 year)) AND ((Hypertriglyceridemic) OR (hypercholesterolemic)) AND ((lean) OR (overweight)) AND ((Ca++ channel blockers) OR (alpha- blockers) OR (beta-blockers) OR (nitrates)) AND ((cardiac) OR (cerebrovascular) OR (endocrine) OR (gastrointestinal) OR (hematological) OR (liver) OR (metabolic) OR (pulmonary) OR (renal)) AND ((cancer) OR (disease)) AND ((Pregnant) OR (nursing)) AND ((benzephetamine) OR (diethylpropion) OR (liraglutide) OR (lorcaserin) OR (naltrexone-bupropion in combination) OR (orlistat) OR (phendimetrazine) OR (phentermine)))"}
{"candidate_id": "LLM05443", "doc_id": "NCT02951754_inc", "case_bucket": "other", "source_criterion": "White Brazilian of European descent Fulfillment of the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria for ADHD Eligibility to immediate-release MPH (IR-MPH) treatment", "candidate_expression": "((ADHD Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria) AND (Brazilian) AND (European descent) AND (White) AND (immediate-release MPH (IR-MPH) Eligibility))"}
{"candidate_id": "LLM05444", "doc_id": "NCT03034837_exc", "case_bucket": "other", "source_criterion": "Can not cooperate with the treatment Can not obtain the child's parental consent", "candidate_expression": "((Can not obtain the child's parental consent) AND NOT (cooperate with the treatment) AND NOT (child's parental consent))"}
{"candidate_id": "LLM05445", "doc_id": "NCT02390973_exc", "case_bucket": "or", "source_criterion": "pregnancy past esophageal, gastric or bariatric surgery irritable bowel, unexplained intermittent vomiting, severe abdominal pain, chronic diarrhea or constipation history of gastric or duodenal ulcers pre-operatory hypoalbuminemy history of renal, hepatic, cardiac or pulmonary severe disease taken of corticosteroid in the last month evidence of psycological problem that may affect the capacity to understand the project and to comply with the medical recommandations history of drug use or alcool abuse in the last 12 months history of gastro-intestinal inflammatory diseases", "candidate_expression": "((corticosteroid last month) AND (gastro-intestinal inflammatory diseases) AND (hypoalbuminemy pre-operatory) AND (pregnancy) AND ((constipation) OR (diarrhea)) AND ((duodenal ulcers) OR (gastric ulcers)) AND ((cardiac disease) OR (hepatic disease severe severe severe) OR (pulmonary disease severe) OR (renal disease)) AND ((bariatric surgery) OR (esophageal surgery) OR (gastric surgery)) AND ((alcool abuse) OR (drug use)) AND ((abdominal pain severe) OR (irritable bowel) OR (vomiting intermittent)))"}
{"candidate_id": "LLM05446", "doc_id": "NCT02627560_inc", "case_bucket": "other", "source_criterion": "breast cancer undergoing unilateral mastectomy with or without axillary node dissection received adequate oral and written information about the study and signed an informed-consent form", "candidate_expression": "((axillary node dissection) AND (breast cancer) AND (received adequate oral and written information about the study and signed an informed-consent form) AND (undergoing) AND (unilateral mastectomy))"}
{"candidate_id": "LLM05447", "doc_id": "NCT03560310_exc", "case_bucket": "or", "source_criterion": "Previously enrolled in this study (i.e. patient now at repeat encounter) Concomitant surgical procedure other than CABG Anticoagulant treatment after the operation (e.g. warfarin, direct thrombin inhibitors (dabigatran), FXa inhibitors (rivaroxaban, apixaban, heparin, low-molecular weight heparin, fondaparinux) Discharge from the operating hospital to an ICU at another hospital Pregnancy or lactation Known intolerance or contraindication to ticagrelor or ASA Any disorder that may interfere with drug absorption Any condition other than coronary artery disease with a life expectancy <12 months Known chronic liver disease, renal disease requiring dialysis or bleeding disorder Atrioventricular block II and III in patients without pacemaker Any other indication for dual antiplatelet therapy, i.e. recent stent implantation Debilitating stroke within 90 days before inclusion Previous intracranial bleeding Treatment with immunosuppressants (e.g. cyclosporine and tacrolimus) Treatment with strong CYP3A4-inhibitors (e.g. ketoconazole, clarithromycin, nefazodone, ritonavir or atazanavir) Any condition that in the opinion of the investigator may interfere with adherence to trial protocol", "candidate_expression": "((<12 months) AND (ASA) AND (Anticoagulant treatment) AND (Atrioventricular block II) AND (Atrioventricular block III) AND (CABG) AND (Concomitant) AND (Debilitating) AND (Discharge) AND (FXa inhibitors) AND (ICU) AND (Pregnancy) AND (Previous) AND (Previously) AND (after the operation) AND (another) AND (apixaban) AND (atazanavir) AND (bleeding disorder) AND (chronic liver disease) AND (clarithromycin) AND (condition) AND (contraindication) AND (coronary artery disease) AND (cyclosporine) AND (dabigatran) AND (dialysis) AND (direct thrombin inhibitors) AND (disorder) AND (dual antiplatelet therapy) AND (enrolled in this study) AND (fondaparinux) AND (heparin) AND (hospital) AND (immunosuppressants) AND (indication) AND (intolerance) AND (intracranial bleeding) AND (ketoconazole) AND (lactation) AND (life expectancy) AND (low-molecular weight heparin) AND (may interfere with drug absorption) AND (nefazodone) AND (operating hospital) AND (operation) AND (other than) AND (pacemaker) AND (recent) AND (renal disease) AND (requiring) AND (ritonavir) AND (rivaroxaban) AND (stent implantation) AND (stroke) AND (strong CYP3A4-inhibitors) AND (surgical procedure) AND (tacrolimus) AND (the operation) AND (ticagrelor) AND (warfarin) AND (within 90 days before inclusion) AND (without))"}
{"candidate_id": "LLM05448", "doc_id": "NCT03404804_exc", "case_bucket": "or", "source_criterion": "Children will be excluded if they have a history of developmental delay or inability to communicate the effects of an allergic reaction (non-verbal). Any contraindication to allergy testing will also result in exclusion (i.e. history of a severe allergic reaction to skin tests,, anaphylaxis in the past six weeks, pregnancy, child took any antihistamine in the past three days [including diphenhydramine (Benadryl®), cetirizine (Zyrtec®), loratadine (Claritin®), fexofenadine (Allegra®), levocetirizine (Xyzal®), and desloratadine (Clarinex®)] or child has a history of a condition that requires a beta blocker medicine for cardiac conditions, high blood pressure, migraine headaches, or eye drops for glaucoma (e.g. propranolol, metoprolol, atenolol and Timoptic®, or Betoptic® eye drops). Children who present to the PED with a rash, vomiting or current asthma symptoms including coughing, wheezing or breathing problems will also be excluded to ensure these do not mask reactions to an oral challenge. Patients being admitted to the hospital or those who are deemed too acutely ill for participation (triage level 1 or 2 or as determined by the ED patient care team) will be excluded from the study. During this pilot study, we will exclude non-English speaking families. However, in subsequent studies we will include the non-English speaking population. Children who are wards of the state, in foster care or police custody or detention will be excluded. Children with any basal condition (trauma, infection, minor accidents, etc..) will be able to participate in the study provided they and their family are willing and do not meet the above-mentioned exclusion criteria.", "candidate_expression": "((Allegra) AND (Benadryl) AND (Betoptic) AND (Children) AND (Clarinex) AND (Claritin) AND (PED) AND (Xyzal) AND (Zyrtec) AND (allergic reaction) AND (allergy testing) AND (anaphylaxis in the past six weeks) AND (antihistamine in the past three days) AND (basal condition) AND (beta blocker medicine) AND (contraindication) AND (eye drops) AND (glaucoma) AND (non-English speaking) AND (pregnancy) AND (severe allergic reaction history) AND (skin tests) AND ((cetirizine) OR (desloratadine) OR (diphenhydramine) OR (fexofenadine) OR (levocetirizine) OR (loratadine)) AND ((developmental delay) OR (inability to communicate the effects non-verbal)) AND ((cardiac conditions) OR (high blood pressure) OR (migraine headaches)) AND ((Timoptic) OR (atenolol) OR (eye drops) OR (metoprolol) OR (propranolol)) AND ((asthma symptoms current) OR (rash) OR (vomiting)) AND ((breathing problems) OR (coughing) OR (wheezing)) AND ((detention) OR (foster care) OR (police custody) OR (wards of the state)) AND ((infection) OR (minor accidents) OR (trauma)))"}
{"candidate_id": "LLM05449", "doc_id": "NCT03096613_exc", "case_bucket": "or", "source_criterion": "Acute heart failure or acute exacerbation of chronic heart failure within the past 2 weeks. Scheduled cardiac resynchronization therapy or heart transplantation. History of malignant tumor or life expectancy under 12 months. Already on medications that may affect thyroid function (L-T4, carbimazole, propylthiouracil, amiodarone, lithium). Pregnancy and lactation period. Participation in another clinical trial within the past 30 days. Contraindication or intolerance to evidence-based therapy for CHF, such as beta-blocker, angiotensin-converting enzyme inhibitor or angiotensin receptor blocker. Known hypersensitivity to the trial treatment(s) or diluents (when applicable), including placebo or other comparator drug(s). Untreated adrenal insufficiency. Untreated pituitary insufficiency. Untreated thyrotoxicosis. Treatment with levothyroxine must not be initiated in patients with acute myocardial infarction, acute myocarditis, or acute pancarditis. Severe renal dysfunction (eGFR=30 ml/min/1.73m2). Significant hepatic impairment (Serum GPT > 120 U/L). Any disorder which, in the opinion of the investigator, might jeopardise subject's safety or compliance with the protocol.", "candidate_expression": "((Acute heart failure) AND (Any disorder which, in the opinion of the investigator, might jeopardise subject's safety or compliance with the protocol.) AND (CHF) AND (Contraindication) AND (L-T4) AND (Pregnancy) AND (Serum GPT > 120 U/L) AND (acute myocardial infarction) AND (acute myocarditis) AND (acute pancarditis) AND (adrenal insufficiency Untreated) AND (amiodarone) AND (angiotensin receptor blocker) AND (angiotensin-converting enzyme inhibitor) AND (beta-blocker) AND (carbimazole) AND (cardiac resynchronization therapy) AND (chronic heart failure) AND (comparator drug(s) other) AND (eGFR =30 ml/min/1.73m2) AND (evidence-based therapy) AND (exacerbation acute) AND (heart transplantation) AND (hepatic impairment Significant) AND (hypersensitivity) AND (intolerance) AND (lactation period) AND (levothyroxine) AND (life expectancy under 12 months) AND (lithium) AND (malignant tumor) AND (medications) AND (pituitary insufficiency Untreated) AND (placebo) AND (propylthiouracil) AND (renal dysfunction Severe) AND (thyroid function affect) AND (thyrotoxicosis Untreated) AND (trial diluents) AND (trial treatment(s)) AND NOT (Treatment))"}
{"candidate_id": "LLM05450", "doc_id": "NCT00250640_exc", "case_bucket": "or", "source_criterion": "Any condition that prevents participation in the study, including pregnancy and other contraindications for Ventavis treatment (as listed in the current Ventavis Summary of Product Characteristics and patient package insert)", "candidate_expression": "((Ventavis Summary of Product Characteristics and patient package insert) AND (Ventavis treatment) AND ((contraindications) OR (pregnancy)))"}
```
