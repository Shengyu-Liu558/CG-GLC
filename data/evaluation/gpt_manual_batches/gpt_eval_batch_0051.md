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
{"candidate_id": "LLM01251", "doc_id": "NCT03208465_exc", "case_bucket": "or", "source_criterion": "Contraindications to empagliflozin, Sitagliptin DPP4 inhibitors or Sodium-glucose cotransporter-2(SGLT2) inhibitors within the previous 4 weeks Insulin requiring diabetes Poor glucose control (HbA1C>10 %) Acute coronary syndrome Stent placement within the previous 6 months Previous coronary artery bypass graft surgery within the previous 6 months Planned revascularization within 6 months Heart failure requiring loop diuretics Severe left ventricular hypertrophy (left ventricular septal wall thickness > 13mm) Significant renal disease manifested by creatinine clearance of < 30 ml/min) Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (alanine transaminase or Aspartate Aminotransferase > 3 times upper limit of normal) Radiopaque material implanted in the chest wall (metal, silicone, etc.) Contraindication to adenosine stress test Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. Patient's pregnant or breast-feeding or child-bearing potential Expected life expectancy < 1 year Unwillingness or inability to comply with the procedures described in this protocol", "candidate_expression": "((Acute coronary syndrome) AND (Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study.) AND (Aspartate Aminotransferase) AND (Contraindication) AND (Contraindications) AND (DPP4 inhibitors) AND (Expected life expectancy < 1 year) AND (HbA1C >10 %) AND (Heart failure) AND (Hepatic disease) AND (Insulin) AND (Poor glucose control) AND (Radiopaque material chest wall) AND (Sitagliptin) AND (Sodium-glucose cotransporter-2(SGLT2) inhibitors) AND (Stent) AND (adenosine stress test) AND (alanine transaminase) AND (biliary tract obstruction) AND (breast-feeding) AND (child-bearing potential) AND (coronary artery bypass graft surgery Previous within the previous 6 months) AND (creatinine clearance < 30 ml/min) AND (diabetes) AND (empagliflozin) AND (hepatic enzyme elevation significant) AND (left ventricular hypertrophy Severe) AND (left ventricular septal wall thickness > 13mm) AND (loop diuretics) AND (placement within the previous 6 months) AND (pregnant) AND (renal disease Significant) AND (revascularization Planned within 6 months))"}
{"candidate_id": "LLM01252", "doc_id": "NCT01391780_inc", "case_bucket": "or", "source_criterion": "presence of stress urinary or urgency incontinence", "candidate_expression": "((stress urinary incontinence) OR (urgency incontinence))"}
{"candidate_id": "LLM01253", "doc_id": "NCT03004209_exc", "case_bucket": "or", "source_criterion": "Hemoglobin > 12g/dL Hematochrit >36% Thrombocytosis > 750K AST or ALT > 120 HIV (+) Allergic reaction upon erythropoietin Uncontrolled hypertension mRS before the autoimmune encephalitis > 3 Breast feeding or pregnancy History of ischemic stroke or pulmonary thrombosis Refuse to be enrolled", "candidate_expression": "((> 120) AND (> 12g/dL) AND (> 3) AND (> 750K) AND (>36%) AND (Allergic) AND (HIV (+)) AND (Hematochrit) AND (Hemoglobin) AND (History) AND (Refuse to be enrolled) AND (Thrombocytosis) AND (Uncontrolled hypertension) AND (autoimmune encephalitis) AND (before the autoimmune encephalitis) AND (erythropoietin) AND (mRS) AND (the autoimmune encephalitis) AND ((Breast feeding) OR (pregnancy)) AND ((ischemic stroke) OR (pulmonary thrombosis)) AND ((ALT) OR (AST)))"}
{"candidate_id": "LLM01254", "doc_id": "NCT02668978_exc", "case_bucket": "or", "source_criterion": "Traumatic pulmonary contusion or laceration Lung reduction surgery Planned removal of more than 10 lung lesions Pneumonectomy Known hypersensitivity to bovine protein Known hypersensitivity to Brilliant Blue FCF (E133) Presence of active infection", "candidate_expression": "((Brilliant Blue FCF (E133)) AND (Lung reduction surgery Planned) AND (Pneumonectomy) AND (active infection) AND (bovine protein) AND (hypersensitivity) AND (lung lesions more than 10) AND (removal) AND ((laceration) OR (pulmonary contusion)))"}
{"candidate_id": "LLM01255", "doc_id": "NCT02654912_exc", "case_bucket": "or", "source_criterion": "contraindications from manufacturer for medications including currently taking haloperidol, artane, Phenergan (Promethazine), chlorpromazine, erythromycin, Azithromycin, clarithromycin, Ketoconazole, fluconazole, mefloquine (as prophylaxis), lumefantrine (in Coartem), quinine, Septrin anyone seriously ill currently taking antimalarial medicines allergy to artemisinin drugs pregnant women in first trimester children under 3 months of age reported heart condition", "candidate_expression": "((Coartem) AND (Promethazine) AND (age under 3 months) AND (allergy) AND (antimalarial medicines) AND (artemisinin drugs) AND (children) AND (contraindications) AND (first trimester) AND (heart condition) AND (pregnant first trimester) AND (seriously ill) AND (women) AND ((Azithromycin) OR (Ketoconazole) OR (Phenergan) OR (Septrin) OR (artane) OR (chlorpromazine) OR (clarithromycin) OR (erythromycin) OR (fluconazole) OR (haloperidol) OR (lumefantrine) OR (mefloquine) OR (quinine)))"}
{"candidate_id": "LLM01256", "doc_id": "NCT03328052_exc", "case_bucket": "or", "source_criterion": "Diagnosis of a psychotic disorder. History of, or current, open head brain trauma. Candidates with any metal, shrapnel or other similar objects in the head that could affect the QEEG History of: craniotomy, cerebral metastases, cerebrovascular accident; current diagnosis of seizure disorder, schizophrenia, schizo-affective disorder, dementia, mental retardation, or major depression with psychotic features; or use of depot neuroleptics in last 12 months. Uncontrolled thyroid disorders. Known pregnancy and/or lactation, or intent to become pregnant during this study. Chronic or acute pain requiring prescription pain medication(s) (narcotic or synthetic narcotic) Participation in any other therapeutic drug study within 60 days preceding inclusion.", "candidate_expression": "((History) AND (Known pregnancy and/or lactation, or intent to become pregnant during this study.) AND (Participation in any other therapeutic drug study within 60 days preceding inclusion.) AND (QEEG) AND (Uncontrolled) AND (affect) AND (in last 12 months) AND (open head brain trauma) AND (pain) AND (prescription pain medication) AND (psychotic disorder) AND (psychotic features) AND (thyroid disorders) AND ((cerebral metastases) OR (cerebrovascular accident) OR (craniotomy) OR (dementia) OR (depot neuroleptics) OR (major depression) OR (mental retardation) OR (schizo-affective disorder) OR (schizophrenia) OR (seizure disorder)) AND ((Chronic) OR (acute)) AND ((narcotic) OR (synthetic narcotic)) AND ((History) OR (current)) AND ((metal) OR (objects in the head) OR (shrapnel)))"}
{"candidate_id": "LLM01257", "doc_id": "NCT02385448_inc", "case_bucket": "or", "source_criterion": "Good general health Older than the age of legal consent (i.e. 18 years old) Sonographic diagnosis of ovarian endometrioma with diameter at least 4cm on 2 separate scans at least 6 weeks apart No contraindication to use of progesterone or combined oral contraceptive pills Not attempting to conceive either at the time of study entry or for at least 2 years after surgery Willing and able to participate after the study has been explained", "candidate_expression": "((18 years old) AND (2 separate scans) AND (Good general health) AND (No) AND (Not) AND (Older than the age of legal consent) AND (Sonographic) AND (age) AND (at least 6 weeks apart) AND (attempting) AND (conceive) AND (contraindication) AND (diameter at least 4cm) AND (ovarian endometrioma) AND ((combined oral contraceptive pills) OR (progesterone)) AND ((at the time of study entry) OR (for at least 2 years after surgery)))"}
{"candidate_id": "LLM01258", "doc_id": "NCT03424733_exc", "case_bucket": "or", "source_criterion": "prior allergic reaction to interferon products, congestive heart failure, elevated liver enzymes", "candidate_expression": "((allergic reaction) AND (congestive heart failure) AND (elevated liver enzymes) AND (interferon products) AND (prior))"}
{"candidate_id": "LLM01259", "doc_id": "NCT02607319_exc", "case_bucket": "or", "source_criterion": "Evidence of low ovarian reserve by at least one of the following: AMH = 1,5 ng/mL and/or basal CD 3 FSH = 10 mIU/mL and/or basal CD 3 Estradiol = 60 ng/mL and/or previous egg collection yield = 3 oocytes. Preexisting medical condition (thyroid disease, diabetes mellitus, hypertension, pulmonary conditions, cardiac condition…). Severe male factor infertility (Total motile sperm count < 5 million/ml and/or normal WHO morphology <20%). Hypersensitivity to Heparin or its derivatives. Acquired thrombophilia. Active hemorrhage or increased risk of bleeding due to impairment of homeostasis. Severe impairment of liver or pancreatic function. Severe renal insufficiency (Creatinine Clearance < 30 ml/min). Injuries to or operations on the central nervous system, eyes and ears within the last 2 months. Disseminated Intravascular Coagulation (DIC) attributable to heparin-induced thrombocytopenia. Acute bacterial endocarditis and endocarditis lenta. Any organic lesion with high risk of bleeding (e.g.: active peptic ulcer, hemorrhagic stroke, cerebral aneurysm or cerebral neoplasms).", "candidate_expression": "((AMH = 1,5 ng/mL) AND (Active hemorrhage) AND (Acute bacterial endocarditis) AND (Creatinine Clearance < 30 ml/min) AND (DIC) AND (Disseminated Intravascular Coagulation) AND (Heparin) AND (Hypersensitivity) AND (Injuries) AND (Total motile sperm count < 5 million/ml) AND (active peptic ulcer) AND (basal CD 3 Estradiol = 60 ng/mL) AND (basal CD 3 FSH = 10 mIU/mL) AND (cardiac condition) AND (cerebral aneurysm) AND (cerebral neoplasms) AND (diabetes mellitus) AND (egg collection yield = 3 oocytes) AND (endocarditis lenta) AND (hemorrhagic stroke) AND (heparin-induced thrombocytopenia) AND (hypertension) AND (impairment of homeostasis) AND (impairment of liver) AND (impairment of pancreatic function) AND (low ovarian reserve) AND (male factor infertility Severe) AND (normal WHO morphology <20%) AND (operations central nervous system eyes ears) AND (organic lesion risk of bleeding) AND (pulmonary conditions) AND (renal insufficiency Severe) AND (risk of bleeding increased) AND (thrombophilia Acquired) AND (thyroid disease))"}
{"candidate_id": "LLM01260", "doc_id": "NCT03228654_inc", "case_bucket": "or", "source_criterion": "uterine size <12 weeks. presence of benign cause for the hysterectomy e.g. fibroid uterus, perimenopausal beeding not responding to medical treatment or complex endometrial hyperplasia without atypia. Absence of significant scarring in the pelvis from previous surgeries.", "candidate_expression": "((<12 weeks) AND (Absence) AND (atypia) AND (benign cause) AND (from previous surgeries) AND (hysterectomy) AND (medical treatment) AND (not) AND (pelvis) AND (previous) AND (responding to medical treatment) AND (significant scarring) AND (surgeries) AND (uterine size) AND (without) AND ((complex endometrial hyperplasia) OR (fibroid uterus) OR (perimenopausal beeding)))"}
{"candidate_id": "LLM01261", "doc_id": "NCT03263481_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01262", "doc_id": "NCT02314559_exc", "case_bucket": "other", "source_criterion": "Dementia. Gastroscopy planned at the same time. Allergies to propofol All cases were a 'full stomach' is suspected (gastric banding) Pregnancy", "candidate_expression": "((Allergies) AND (Dementia) AND (Gastroscopy planned at the same time) AND (Pregnancy) AND (propofol))"}
{"candidate_id": "LLM01263", "doc_id": "NCT01996436_inc", "case_bucket": "other", "source_criterion": "Adult patient, age 18-80 years old, with ruptured aneurysm(s) who experience cerebral vasospasm post operatively within 3-21 days.", "candidate_expression": "((18-80 years old) AND (Adult) AND (age) AND (cerebral vasospasm) AND (post operatively) AND (post operatively within 3-21 days) AND (ruptured aneurysm))"}
{"candidate_id": "LLM01264", "doc_id": "NCT01177891_exc", "case_bucket": "or", "source_criterion": "Blood donation of more than 450ml in the previous three months. Subject with an abnormal karyotype in favor of Turner syndrome or having a premutation of the FMR1 gene or a syndromic form Subject exclusion period in another study without direct individual benefit Subject refusing to sign the consent form", "candidate_expression": "((Blood donation) AND (Subject exclusion period in another study without direct individual benefit) AND (Subject refusing to sign the consent form) AND (Turner syndrome) AND (in the previous three months) AND (more than 450ml) AND (of more than 450ml) AND ((abnormal karyotype) OR (premutation of the FMR1 gene) OR (syndromic form)))"}
{"candidate_id": "LLM01265", "doc_id": "NCT02053246_inc", "case_bucket": "other", "source_criterion": "Adults (= 18 years of age) with World Health Organization Group 2 Pulmonary Hypertension (Mean pulmonary artery pressure = 25 mmHg and pulmonary capillary wedge pressure = 15 mmHg) New York Heart Association class II-IV symptoms Left ventricular ejection fraction (LVEF) = 45%", "candidate_expression": "(((Mean pulmonary artery pressure = 25 mmHg) AND (Adults) AND (Left ventricular ejection fraction (LVEF) = 45%) AND (New York Heart Association class II-IV) AND (Pulmonary Hypertension World Health Organization Group 2) AND (age = 18 years) AND (pulmonary capillary wedge pressure = 15 mmHg) AND (symptoms))"}
{"candidate_id": "LLM01266", "doc_id": "NCT01822262_exc", "case_bucket": "or", "source_criterion": "Gallbladder's wall >3mm, atrophied gallbladder,gallstone obstruct the Hartmann's pouch. Abdominal ultrasound display the contractibility of gallbladder is poor. The aged patients with bad heart and lung function. Patients who has acute cholecystitis,pancreatitis,pancreaticobiliary diseases, especially choledocholithiasis. Pregnant or lactational women.", "candidate_expression": "((>3mm) AND (Abdominal ultrasound) AND (Gallbladder's wall) AND (Hartmann's pouch) AND (Pregnant) AND (acute cholecystitis) AND (aged) AND (atrophied gallbladder) AND (bad heart function) AND (bad lung function) AND (choledocholithiasis) AND (contractibility of gallbladder) AND (gallstone obstruct) AND (lactational) AND (pancreaticobiliary diseases) AND (pancreatitis) AND (poor) AND (women))"}
{"candidate_id": "LLM01267", "doc_id": "NCT02287259_inc", "case_bucket": "or", "source_criterion": "major depressive episode in type2 bipolar disorder or bipolar disorder NOS.(MADRS more than 20 point) 18years to 65years subjects who sign the informed consent document", "candidate_expression": "((18years to 65years) AND (MADRS) AND (NOS) AND (major depressive episode) AND (more than 20 point) AND (sign the informed consent) AND (years) AND ((bipolar disorder) OR (type2 bipolar disorder)))"}
{"candidate_id": "LLM01268", "doc_id": "NCT02760251_inc", "case_bucket": "or", "source_criterion": "Informed consent as documented by signature (see informed consent form) Primary ITP according to the definition of Rodeghiero et al. (52) and a platelet count of <30x109/l Age range: 18-45 years Previously treated patients, with failure or intolerance to first-line therapy, or relapse after first-line therapy, i.e. corticosteroids, intravenous immunoglobulin (IVIG), or anti-D immunoglobulins", "candidate_expression": "((18-45 years) AND (<30x109/l) AND (Age) AND (IVIG) AND (Informed consent as documented by signature (see informed consent form)) AND (Previously treated) AND (Primary ITP) AND (after first-line therapy) AND (anti-D immunoglobulins) AND (corticosteroids) AND (definition of Rodeghiero) AND (failure) AND (first-line therapy) AND (intolerance) AND (intravenous immunoglobulin) AND (platelet count) AND (relapse))"}
{"candidate_id": "LLM01269", "doc_id": "NCT02366819_exc", "case_bucket": "or", "source_criterion": "Previous or concurrent malignancy, except for adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, or any other cancer for which the patient has been previously treated and the lifetime recurrence risk is less than 30% Inflammatory bowel disease that is uncontrolled or on active treatment (Crohn's disease, ulcerative colitis) Diarrhea, grade 1 or greater by the National Cancer Institute Common Terminology Criteria for Adverse Events (NCI-CTCAE, version [v] 4.0) Neuropathy, grade 2 or greater by NCI-CTCAE, v 4.0 Serious underlying medical or psychiatric illnesses that would, in the opinion of the treating physician, substantially increase the risk for complications related to treatment Active uncontrolled bleeding Pregnancy or breastfeeding Major surgery within 4 weeks Patients with any polymorphism in UGT1A1 other than *1 or *28 (e.g, *6) will be allowed and treated as in the *28/*28 dosing group", "candidate_expression": "((Diarrhea) AND (Inflammatory bowel disease) AND (Major surgery within 4 weeks) AND (NCI-CTCAE, v 4.0 grade 2 or greater) AND (NCI-CTCAE, version [v] 4.0) AND (National Cancer Institute Common Terminology Criteria for Adverse Events grade 1 or greater) AND (Neuropathy) AND (Pregnancy or breastfeeding) AND (bleeding Active uncontrolled) AND (cervical cancer in situ) AND (malignancy) AND ((treatment) OR (uncontrolled)) AND ((Crohn's disease) OR (ulcerative colitis)) AND ((Previous) OR (concurrent)) AND ((basal cell skin cancer) OR (squamous cell skin cancer)))"}
{"candidate_id": "LLM01270", "doc_id": "NCT00198913_exc", "case_bucket": "or", "source_criterion": "type 1 diabetic or non-diabetic", "candidate_expression": "((non-diabetic) OR (type 1 diabetic))"}
{"candidate_id": "LLM01271", "doc_id": "NCT01742117_inc", "case_bucket": "or", "source_criterion": "Patient >18 years of age Patient presents with acute coronary syndrome (ACS) or stable coronary artery disease (CAD) Patient is eligible for PCI Patient is willing and able to provide informed written consent Patient not able to receive 12 months of dual anti-platelet therapy Failure of index PCI Patient or physician refusal to enroll in the study Patient with known CYP2C19 genotype prior to randomization Planned revascularization of any vessel within 30 days post-index procedure and/or of the target vessel(s) within 12 months post-procedure Anticipated discontinuation of clopidogrel or ticagrelor within the 12 month follow up period, example for elective surgery Serum creatinine >2.5 mg/dL within 7 days of index procedure Platelet count <80,000 or >700,000 cells/mm3, or white blood cell count <3,000 cells/mm3 if persistent (at least 2 abnormal values) within 7 days prior to index procedure. History of intracranial hemorrhage Known hypersensitivity to clopidogrel or ticagrelor or any of its components Patient is participating in an investigational drug or device clinical trial that has not reached its primary endpoint Patient previously enrolled in this study Patient is pregnant, lactating, or planning to become pregnant within 12 months Patient has received an organ transplant or is on a waiting list for an organ transplant Patient is receiving or scheduled to receive chemotherapy within 30 days before or after the procedure Patient is receiving immunosuppressive therapy or has known immunosuppressive or autoimmune disease (e.g., human immunodeficiency virus, systemic lupus erythematous, etc.) Patient is receiving chronic oral anticoagulation therapy (i.e., vitamin K antagonist, direct thrombin inhibitor, Factor Xa inhibitor) Concomitant use of simvastatin/lovastatin > 40 mg qd Concomitant use of potent CYP3A4 inhibitors (atazanavir, clarithromycin, indinavir, itraconazole, ketoconazole, nefazodone, nelfinavir, ritonavir, saquinavir, telithromycin and voriconazole) or inducers (carbamazepine, dexamethasone, phenobarbital, phenytoin, rifampin, and rifapentine) Non-cardiac condition limiting life expectancy to less than one year, per physician judgment (e.g. cancer) Known history of severe hepatic impairment Patient has a history of bleeding diathesis or coagulopathy or will refuse blood transfusions Patient has an active pathological bleeding, such as active gastrointestinal (GI) bleeding Inability to take aspirin at a dosage of 100 mg or less Current substance abuse (e.g., alcohol, cocaine, heroin, etc.)", "candidate_expression": "((100 mg or less) AND (12 months) AND (<3,000 cells/mm3) AND (<80,000 or >700,000 cells/mm3) AND (> 40 mg qd) AND (>18 years) AND (>2.5 mg/dL) AND (ACS) AND (CAD) AND (CYP2C19 genotype) AND (Concomitant) AND (Failure) AND (Inability to take) AND (Non-cardiac condition) AND (PCI) AND (Patient is willing and able to provide informed written consent) AND (Patient or physician refusal to enroll in the study) AND (Planned) AND (Serum creatinine) AND (able to receive) AND (active) AND (age) AND (any of its components) AND (aspirin) AND (chemotherapy) AND (chronic) AND (dual anti-platelet therapy) AND (elective surgery) AND (eligible) AND (example for) AND (gastrointestinal (GI) bleeding) AND (hepatic impairment) AND (hypersensitivity) AND (index) AND (index procedure) AND (intracranial hemorrhage) AND (is on a waiting list) AND (less than one year) AND (life expectancy) AND (oral anticoagulation therapy) AND (pathological bleeding) AND (planning to become) AND (potent CYP3A4 inducers) AND (potent CYP3A4 inhibitors) AND (prior to randomization) AND (procedure) AND (randomization) AND (revascularization) AND (severe) AND (stable) AND (substance abuse) AND (the procedure) AND (will refuse) AND (within 12 months) AND (within 12 months post-procedure) AND (within 30 days before or after the procedure) AND (within 30 days post-index procedure) AND (within 7 days of index procedure) AND (within 7 days prior to index procedure) AND (within the 12 month follow up period) AND ((bleeding diathesis) OR (blood transfusions) OR (coagulopathy)) AND ((any vessel) OR (of the target vessel(s))) AND ((acute coronary syndrome) OR (coronary artery disease)) AND ((clopidogrel) OR (ticagrelor)) AND ((Platelet count) OR (white blood cell count)) AND ((lactating) OR (pregnant)) AND ((organ transplant)) AND ((is receiving) OR (scheduled to receive)) AND ((autoimmune disease) OR (immunosuppressive disease) OR (immunosuppressive therapy)) AND ((human immunodeficiency virus) OR (systemic lupus erythematous)) AND ((Factor Xa inhibitor) OR (direct thrombin inhibitor) OR (vitamin K antagonist)) AND ((lovastatin) OR (simvastatin)) AND ((atazanavir) OR (clarithromycin) OR (indinavir) OR (itraconazole) OR (ketoconazole) OR (nefazodone) OR (nelfinavir) OR (ritonavir) OR (saquinavir) OR (telithromycin) OR (voriconazole)) AND ((carbamazepine) OR (dexamethasone) OR (phenobarbital) OR (phenytoin) OR (rifampin) OR (rifapentine)))"}
{"candidate_id": "LLM01272", "doc_id": "NCT03209687_inc", "case_bucket": "other", "source_criterion": "Females undergoing Intra-Cytoplasmic Sperm Injection (ICSI) cycles Age between 20 and 40 years", "candidate_expression": "((Age between 20 and 40 years) AND (Females) AND (Intra-Cytoplasmic Sperm Injection (ICSI) cycles undergoing))"}
{"candidate_id": "LLM01273", "doc_id": "NCT03624881_exc", "case_bucket": "or", "source_criterion": "Previous surgical or catheter ablation for atrial fibrillation Previous cardiac surgery (including CABG) within the past 6 months (180 days) Valvular cardiac surgical/percutaneous procedure (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Any carotid stenting or endarterectomy Documented LA thrombus on imaging LA size > 50 mm (parasternal long axis view) LVEF < 40% Contraindication to anticoagulation (heparin or warfarin) History of blood clotting or bleeding abnormalities PCI/MI within the past 2 months (60 days) Documented thromboembolic event (including TIA) within the past 12 months (365 days) Rheumatic Heart Disease Uncontrolled heart failure or NYHA function class III or IV Severe mitral regurgitation (Regurgitant volume = 60 mL/beat, Regurgitant fraction = 50%, and/or Effective regurgitant orifice area = 0.40cm2) Awaiting cardiac transplantation or other cardiac surgery within the next 12 months (365 days) Unstable angina Acute illness or active systemic infection or sepsis AF secondary to electrolyte imbalance, thyroid disease, or reversible or non-cardiac cause. Presence of implanted ICD/CRT-D. Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or chronic obstructive pulmonary disease) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms. Gastroesophageal Reflux Disease (GERD; active requiring significant intervention not including OTC medication) Significant congenital anomaly or medical problem that in the opinion of the investigator would preclude enrollment in this study. Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Concurrent enrollment in an investigational study evaluating another device, biologic, or drug. Presence of intracardiac thrombus, myxoma, tumor, interatrial baffle or patch or other abnormality that precludes vascular access, or manipulation of the catheter. Life expectancy less than 12 months", "candidate_expression": "((Acute illness active) AND (CABG) AND (Concurrent enrollment in an investigational study evaluating another device, biologic, or drug.) AND (Contraindication) AND (GERD) AND (Gastroesophageal Reflux Disease) AND (LA size > 50 mm parasternal long axis view) AND (LA thrombus) AND (LVEF < 40%) AND (Life expectancy less than 12 months) AND (MI) AND (NYHA function class) AND (PCI) AND (Rheumatic Heart Disease) AND (TIA) AND (Unstable angina within the next 365 days) AND (Women) AND (anticoagulation) AND (atrial fibrillation) AND (cardiac surgery Previous within the past 6 months (180 days)) AND (chronic symptoms) AND (congenital anomaly) AND (electrolyte imbalance) AND (heart failure Uncontrolled) AND (imaging) AND (implanted ICD/CRT-D) AND (medical problem) AND (mitral regurgitation Severe) AND (pre-menopausal) AND (precludes) AND (pregnancy test) AND (pregnant) AND (pulmonary disease Significant) AND (sepsis) AND (significant intervention) AND (systemic infection) AND (thromboembolic event) AND NOT (OTC medication Significant) AND ((Valvular cardiac percutaneous procedure) OR (Valvular cardiac surgical procedure)) AND ((abnormality other) OR (interatrial baffle) OR (intracardiac thrombus) OR (myxoma) OR (patch) OR (tumor)) AND ((manipulation of the catheter) OR (vascular access)) AND ((atriotomy) OR (prosthetic valve) OR (valve repair) OR (valve replacement) OR (ventriculotomy)) AND ((carotid stenting) OR (endarterectomy)) AND ((ablation surgical) OR (catheter ablation)) AND ((heparin) OR (warfarin)) AND ((bleeding abnormalities) OR (blood clotting)) AND ((within the past 2 months) OR (within the past 60 days)) AND ((within the past 12 months) OR (within the past 365 days)) AND ((III) OR (IV)) AND ((Effective regurgitant orifice area = 0.40cm2) OR (Regurgitant fraction = 50%) OR (Regurgitant volume = 60 mL/beat)) AND ((cardiac surgery) OR (cardiac transplantation)) AND ((AF secondary) OR (non-cardiac cause reversible) OR (thyroid disease)) AND ((chronic obstructive pulmonary disease) OR (constrictive pulmonary disease) OR (restrictive pulmonary disease)) AND ((disease of the lungs) OR (disease of the respiratory system) OR (malfunction of the lungs)))"}
{"candidate_id": "LLM01274", "doc_id": "NCT02627521_exc", "case_bucket": "or", "source_criterion": "Anticoagulation therapy Prior CABG. Active bleeding or at high risk of bleeding Severe liver or renal disease. Hypersensitivity to ticagrelor History of intracranial hemorrhage", "candidate_expression": "((Anticoagulation therapy) AND (CABG Prior) AND (Hypersensitivity) AND (bleeding Active) AND (bleeding at high risk) AND (disease liver) AND (intracranial hemorrhage History) AND (renal disease) AND (ticagrelor))"}
{"candidate_id": "LLM01275", "doc_id": "NCT03221231_inc", "case_bucket": "other", "source_criterion": "Current DSM-IV diagnosis of cannabis dependence, >1 week detoxified and abstinent; Able to provide written informed consent and to comply with study procedures. Dutch speaking (Dutch as primary language).", "candidate_expression": "((>1 week) AND (DSM-IV) AND (abstinent) AND (cannabis dependence) AND (detoxified))"}
```
