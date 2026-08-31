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
{"candidate_id": "LLM01076", "doc_id": "NCT00679341_inc", "case_bucket": "or", "source_criterion": "Histologically or cytologically confirmed adenocarcinoma of the breast with locally advanced or metastatic disease, and a candidate for chemotherapy. Human epidermal growth factor receptor 2 (HER2)-positive. No prior chemotherapy for their metastatic breast cancer (MBC). Measurable disease. Age ≥ 18 years. For women of childbearing potential and men with partners of childbearing potential, agreement to use a highly effective, non-hormonal form of contraception or 2 effective forms of non-hormonal contraception by the patient and/or partner. Contraception use must continue for the duration of study treatment and for at least 6 months after the last dose of study treatment. Male patients whose partners are pregnant should use condoms for the duration of the study.", "candidate_expression": "((2) AND (Age) AND (Contraception) AND (Histologically confirmed) AND (Human epidermal growth factor receptor 2 (HER2)) AND (Male) AND (Measurable disease) AND (No) AND (adenocarcinoma of the breast) AND (candidate for chemotherapy) AND (chemotherapy) AND (childbearing potential) AND (condoms) AND (continue for the duration of study treatment) AND (contraception) AND (cytologically confirmed) AND (disease locally advanced) AND (for at least 6 months after the last dose of study treatment) AND (for the duration of the study) AND (highly effective) AND (men) AND (metastatic breast cancer (MBC)) AND (metastatic disease) AND (non-hormonal) AND (non-hormonal contraception) AND (partners are pregnant) AND (positive) AND (prior) AND (study treatment) AND (the last dose of study treatment) AND (with partners of childbearing potential) AND (women) AND (≥ 18 years))"}
{"candidate_id": "LLM01077", "doc_id": "NCT02490839_inc", "case_bucket": "other", "source_criterion": "Participants having H. pylori related chronic gastritis with/without peptic ulcers who are aged greater than 20 years old and are willing to received eradication therapy.", "candidate_expression": "((H. pylori related) AND (aged) AND (chronic gastritis) AND (eradication therapy) AND (greater than 20 years old) AND (peptic ulcers) AND (willing to received))"}
{"candidate_id": "LLM01078", "doc_id": "NCT02390973_exc", "case_bucket": "or", "source_criterion": "pregnancy past esophageal, gastric or bariatric surgery irritable bowel, unexplained intermittent vomiting, severe abdominal pain, chronic diarrhea or constipation history of gastric or duodenal ulcers pre-operatory hypoalbuminemy history of renal, hepatic, cardiac or pulmonary severe disease taken of corticosteroid in the last month evidence of psycological problem that may affect the capacity to understand the project and to comply with the medical recommandations history of drug use or alcool abuse in the last 12 months history of gastro-intestinal inflammatory diseases", "candidate_expression": "((abdominal pain) AND (alcool abuse) AND (bariatric surgery) AND (cardiac disease) AND (chronic) AND (constipation) AND (corticosteroid) AND (diarrhea) AND (drug use) AND (duodenal ulcers) AND (esophageal surgery) AND (gastric surgery) AND (gastric ulcers) AND (gastro-intestinal inflammatory diseases) AND (hepatic disease) AND (hypoalbuminemy) AND (intermittent) AND (irritable bowel) AND (last 12 months) AND (last month) AND (pre-operatory) AND (pregnancy) AND (pulmonary disease) AND (renal disease) AND (severe) AND (vomiting))"}
{"candidate_id": "LLM01079", "doc_id": "NCT02339974_exc", "case_bucket": "or", "source_criterion": "Heart Team assessment of operability (the heart team considers the patient to be a good surgical candidate). Evidence of an acute myocardial infarction = 1 month (30 days) before the intended treatment [defined as: Q wave MI, or non-Q wave MI with total CK elevation of CK-MB = twice normal in the presence of MB elevation and/or troponin level elevation (WHO definition)]. Untreated, severe, left sided valvular heart disease including mitral regurgitation or stenosis, and aortic regurgitation or stenosis. Mean pulmonary artery pressures =40mmHG and PVR >4 woods units as assessed by right heart catheterization. Any therapeutic invasive cardiac procedure resulting in a permanent implant that is performed within 30 days of the index procedure. Examples of permanent implant would include any new heart valve. Implantation of a permanent pacemaker is excluded. Patients with planned concomitant surgical or transcatheter ablation for Atrial Fibrillation. Leukopenia (WBC < 3000 cell/mL), acute anemia (Hgb < 9 g/dL), Thrombocytopenia (Plt < 50,000 cell/mL). Hemodynamic or respiratory instability requiring inotropic support, mechanical ventilation or mechanical heart assistance within 30 days of screening evaluation. Need for emergency surgery for any reason. Left ventricular ejection fraction <40%. Echocardiographic evidence of intracardiac mass, thrombus or vegetation. Active upper GI bleeding within 3 months (90 days) prior to procedure. A known contraindication or hypersensitivity to all anticoagulation regimens, or inability to be anticoagulated for the study procedure. Recent CVA clinically confirmed (by neurologist) or neuroimaging confirmed stroke or transient ischemic attack (TIA) within 6 months (180 days) of the procedure. Estimated life expectancy < 1 year from conditions other than TR. Expectation that patient will not improve despite treatment of tricuspid regurgitation Currently participating in another investigational cardiac device study or any other clinical trial, including drugs or biologics. Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials. Active bacterial endocarditis within 6 months (180 days) of procedure. Patients with signs or symptoms of SVC syndrome, or hepatic cirrhosis not felt due to passive congestion from TR.", "candidate_expression": "((Atrial Fibrillation) AND (CVA clinically confirmed (by neurologist)) AND (Echocardiographic) AND (Estimated life expectancy < 1 year) AND (Heart Team assessment of operability) AND (Hgb < 9 g/dL) AND (Left ventricular ejection fraction <40%) AND (Mean pulmonary artery pressures =40mmHG) AND (PVR >4 woods units) AND (Plt < 50,000 cell/mL) AND (WBC < 3000 cell/mL) AND (acute myocardial infarction = 1 month (30 days) before the intended treatment) AND (anticoagulated) AND (anticoagulation regimens) AND (bacterial endocarditis Active within 6 months (180 days) of procedure) AND (cardiac procedure therapeutic invasive within 30 days of the index procedure) AND (emergency surgery Need for) AND (heart team considers the patient to be a good surgical candidate) AND (heart valve) AND (inability for the study procedure) AND (neuroimaging confirmed within 6 months (180 days) of the procedure) AND (passive congestion from TR) AND (permanent implant) AND (right heart catheterization) AND (upper GI bleeding Active within 3 months (90 days) prior to procedure) AND (valvular heart disease Untreated severe left sided) AND NOT (permanent pacemaker) AND ((aortic regurgitation) OR (aortic stenosis) OR (mitral regurgitation) OR (mitral stenosis)) AND ((surgical ablation) OR (transcatheter ablation)) AND ((Leukopenia) OR (Thrombocytopenia) OR (acute anemia)) AND ((inotropic support) OR (mechanical heart assistance) OR (mechanical ventilation)) AND ((Hemodynamic instability) OR (respiratory instability)) AND ((intracardiac mass) OR (intracardiac thrombus) OR (intracardiac vegetation)) AND ((contraindication) OR (hypersensitivity)) AND ((stroke) OR (transient ischemic attack (TIA))) AND ((SVC syndrome) OR (hepatic cirrhosis)))"}
{"candidate_id": "LLM01080", "doc_id": "NCT03168555_exc", "case_bucket": "or", "source_criterion": "small bowel resection right sided hemicolectomy known chronic diarrheal disease (celiac disease, lactose malabsorption, Inflammatory bowel diseases, incl microscopic colitis) pregnancy wish for pregnancy within next three months allergy to eggs allergy to constituents in Xenbilox (capsules with chenodeoxycholic acid) acute cholecystitis within two months chronic cholecystitis cirrhosis of the liver suspected obstructive choledocholithiasis icterus", "candidate_expression": "((Inflammatory bowel diseases) AND (acute cholecystitis within two months) AND (allergy) AND (celiac disease) AND (chenodeoxycholic acid) AND (chronic cholecystitis) AND (chronic diarrheal disease) AND (cirrhosis of the liver) AND (constituents in Xenbilox) AND (eggs) AND (icterus) AND (lactose malabsorption) AND (microscopic colitis) AND (obstructive choledocholithiasis suspected) AND (pregnancy) AND (pregnancy wish for within next three months) AND (right sided hemicolectomy) AND (small bowel resection))"}
{"candidate_id": "LLM01081", "doc_id": "NCT03119766_inc", "case_bucket": "or", "source_criterion": "Men and women aged 18-45 years. Diagnosis of functional dyspepsia, based on the Rome IV criteria (2016). GIS score of at least 6. Negative H. pylori test . Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial. Patients who agree to use an effective method of contraception throughout the clinical trial.", "candidate_expression": "((Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial) AND (GIS score at least 6) AND (H. pylori test Negative) AND (Men) AND (Patients who agree to use an effective method of contraception throughout the clinical trial.) AND (Rome IV criteria (2016)) AND (aged 18-45 years) AND (functional dyspepsia) AND (women))"}
{"candidate_id": "LLM01082", "doc_id": "NCT03164096_inc", "case_bucket": "other", "source_criterion": "adult female partner aged 18 to 40 years. scheduled for elective cesarean section.", "candidate_expression": "((18 to 40 years) AND (adult) AND (aged) AND (cesarean section) AND (elective) AND (female) AND (female partner) AND (scheduled for))"}
{"candidate_id": "LLM01083", "doc_id": "NCT03056391_inc", "case_bucket": "other", "source_criterion": "1. Patient age ≥ 12 years 2. Presence of P. knowlesi malaria, confirmed by positive blood smear with asexual forms of P. knowlesi. 3. Temperature >38C on admission or fever during the preceding 48 hours 4. Enrolled within 18 hours of commencing antimalarial treatment 5. Written informed consent from patient or attending relative able to and willing to give informed consent. Consent form and information sheets will be translated into Malay and copies provided to the patient.", "candidate_expression": "((Enrolled within 18 hours) AND (P. knowlesi malaria) AND (Temperature >38C) AND (Written informed consent from patient or attending relative able to and willing to give informed consent.) AND (age ≥ 12 years) AND (antimalarial treatment) AND (blood smear positive))"}
{"candidate_id": "LLM01084", "doc_id": "NCT00625742_inc", "case_bucket": "other", "source_criterion": "1. Are referred to the Cachexia Clinic with involuntary weight loss of >5% of their premorbid weight within the previous 6 months. 2. Are 18 years of age or older 3. Have a Karnofsky performance score of 60 or higher. 4. Can maintain oral food intake during the study 5. Can understand the study procedures and can sign an informed consent form. 6. Are not currently taking melatonin. 7. Are taking megestrol acetate and continue to lose weight despite at least 2 weeks of therapy. 8. Have a calculated creatinine clearance of >/= 60 cc/min.", "candidate_expression": "((18 years or older) AND (60 or higher) AND (>/= 60 cc/min) AND (>5% of their premorbid weight) AND (Are taking) AND (Cachexia Clinic) AND (Karnofsky performance score) AND (at least 2 weeks) AND (calculated creatinine clearance) AND (continue) AND (currently) AND (involuntary weight loss) AND (lose weight) AND (megestrol acetate) AND (melatonin) AND (not) AND (of age) AND (therapy) AND (within the previous 6 months))"}
{"candidate_id": "LLM01085", "doc_id": "NCT02953873_inc", "case_bucket": "other", "source_criterion": "At least 18 years of age Signed informed consent African American race History of a solitary renal transplant Stable tacrolimus dose for at least 2 weeks prior to randomization", "candidate_expression": "((Signed informed consent) AND (age At least 18 years) AND (race African American) AND (renal transplant solitary) AND (tacrolimus Stable dose for at least 2 weeks prior to randomization))"}
{"candidate_id": "LLM01086", "doc_id": "NCT02105090_exc", "case_bucket": "or", "source_criterion": "amide and/or esther local anaesthetic allergy paraben allergy Child-Pugh grade B/C liver failure renal insufficiency (calculated glomerular filtration rate under 60 ml/min/1.73 m2 according to Cockcroft-Gault scale ) dementia those presenting with swallowing problem chronic pain condition chronic use of pain medication pregnancy lactation", "candidate_expression": "((Child-Pugh grade B C) AND (allergy) AND (amide local anaesthetic) AND (calculated glomerular filtration rate under 60 ml/min/1.73 m2 Cockcroft-Gault scale) AND (chronic pain condition) AND (dementia) AND (esther local anaesthetic) AND (lactation) AND (liver failure) AND (pain medication chronic use) AND (paraben) AND (pregnancy) AND (renal insufficiency) AND (swallowing problem))"}
{"candidate_id": "LLM01087", "doc_id": "NCT03624517_exc", "case_bucket": "or", "source_criterion": "Known upper gastrointestinal malignancy Bleeding from gastric varices, with or without esophageal varices Use of any other endoscopic method to stop GI bleeding beyond endoscopic band ligation Variceal bleeding in the last 90 days History of transjugular, intrahepatic, portosystemic shunt (TIPS) or vascular decompression surgery Pregnant females Incarcerated individuals Myocardial infarct, cerebrovascular accident, sepsis, respiratory failure, or severe intercurrent illness within the previous 6 weeks Non-cirrhotic portal hypertension causing esophageal varices Known or suspected allergy to octreotide", "candidate_expression": "((Bleeding) AND (GI bleeding) AND (Incarcerated individuals) AND (Non-cirrhotic portal hypertension) AND (Pregnant) AND (Variceal bleeding in the last 90 days) AND (allergy) AND (endoscopic method) AND (esophageal varices) AND (females) AND (gastric varices) AND (octreotide) AND (upper gastrointestinal malignancy) AND NOT (endoscopic band ligation) AND ((transjugular, intrahepatic, portosystemic shunt (TIPS)) OR (vascular decompression surgery)) AND ((Myocardial infarct) OR (cerebrovascular accident) OR (intercurrent illness severe) OR (respiratory failure) OR (sepsis)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM01088", "doc_id": "NCT02543710_inc", "case_bucket": "or", "source_criterion": "All patients referred to a participating research centre with suspicion of or confirmed endometrial cancer. Patients with endometrial or epithelial ovarian cancer who following routine clinical guidelines are offered weekly taxane (paclitaxel) treatment. This will often be a third or fourth line treatment, i.e. patients with advanced disease. Technical possibility to obtain a new tissue biopsy to determine stathmin level in the tumour recurrence.", "candidate_expression": "((Technical possibility to obtain) AND (endometrial cancer) AND (paclitaxel) AND (participating research centre) AND (taxane) AND (tissue biopsy) AND (treatment) AND (tumour recurrence) AND (weekly) AND ((confirmed) OR (suspicion of)) AND ((endometrial ovarian cancer) OR (epithelial ovarian cancer)))"}
{"candidate_id": "LLM01089", "doc_id": "NCT03397914_inc", "case_bucket": "or", "source_criterion": "Age between one year and 18 years Sepsis due to MDR or minimally susceptible gram-negative bacteria History of MDR gram-negative infection or sepsis due to organisms sensitive to colistin. Culture result consistent with MDR gram negative for this febrile neutropenic episode. Patient in sepsis and colistin was administered empirically to increase antibiotic coverage.", "candidate_expression": "((Age between one year and 18 years) AND (Sepsis MDR) AND (administered empirically) AND (colistin) AND (gram negative MDR) AND (minimally susceptible gram-negative bacteria) AND (organisms sensitive to colistin) AND (sepsis) AND ((gram-negative infection) OR (sepsis)))"}
{"candidate_id": "LLM01090", "doc_id": "NCT02570321_exc", "case_bucket": "or", "source_criterion": "Evidence of concomitant infection on exam or gram stain (i.e. herpes, both bacteria and acanthamoeba on gram stain) Impending or frank perforation at recruitment Involvement of sclera at presentation Non-infectious or autoimmune keratitis History of corneal transplantation or recent intraocular surgery No light perception in the affected eye Pinhole visual acuity worse than 20/200 in the unaffected eye Participants who are decisionally and/or cognitively impaired", "candidate_expression": "((Involvement of sclera) AND (No) AND (Pinhole visual acuity) AND (cognitively impaired) AND (concomitant infection) AND (light perception) AND (perforation) AND (worse than 20/200) AND ((Non-infectious keratitis) OR (autoimmune keratitis)) AND ((corneal transplantation) OR (intraocular surgery)))"}
{"candidate_id": "LLM01091", "doc_id": "NCT02437084_inc", "case_bucket": "other", "source_criterion": "Healthy adults 30- 65 years old, BMI 25-35 kg/m2, nondiabetic as defined by fasting plasma glucose <126 mg/dL Lipids: one group with an LDL =/>130 and Triglycerides < 150 mg/dL The 2nd group will have and LDL=/>130 mg/dL and Triglycerides =/>150 mg/dL but less than 400 mg/dL.", "candidate_expression": "((BMI 25-35 kg/m2) AND (Healthy) AND (LDL =/>130) AND (Triglycerides < 150 mg/dL) AND (adults) AND (fasting plasma glucose <126 mg/dL) AND (nondiabetic) AND (old 30- 65 years old))"}
{"candidate_id": "LLM01092", "doc_id": "NCT03360214_exc", "case_bucket": "or", "source_criterion": "Allergy to narcotic medications Intake of any chronic opioids or pain medications preoperatively", "candidate_expression": "((Allergy) AND (narcotic medications) AND (opioids any chronic) AND (pain medications preoperatively))"}
{"candidate_id": "LLM01093", "doc_id": "NCT01803438_inc", "case_bucket": "scope", "source_criterion": "Subject has been diagnosed with symptomatic paroxysmal atrial fibrillation as defined above and at least two symptomatic episodes in the last six months prior to inclusion. At least one episode of AF must be documented during the prior year by any kind of ECG recording. Subject has structural normal heart with an LVEF = 50%, thickness of the inter-ventricular septum =12 mm and left atrium diameters (short axis) < 46 mm obtained by transthoracic echocardiography. Subject has normal ECG parameters (QRS width in the 12 channel surface ECG =120 ms, QTc - interval < 440 ms, PQ - interval = 210 ms; all parameters should be measured at sinus rhythm). Subject is at least 18 and not older than 75years old. Subject is able and willing to give informed consent.", "candidate_expression": "((AF) AND (ECG) AND (ECG normal) AND (LVEF = 50%,) AND (PQ - interval = 210 ms) AND (QRS width 12 channel surface ECG =120 ms) AND (QTc - interval < 440 ms) AND (Subject is able and willing to give informed consent) AND (episode At least one prior year) AND (episodes at least two symptomatic last six months prior to inclusion) AND (heart structural normal) AND (left atrium diameters < 46 mm) AND (old at least 18 and not older than 75years) AND (paroxysmal atrial fibrillation symptomatic) AND (short axis) AND (sinus rhythm) AND (thickness of the inter-ventricular septum =12 mm) AND (transthoracic echocardiography))"}
{"candidate_id": "LLM01094", "doc_id": "NCT01440296_inc", "case_bucket": "or", "source_criterion": "male and female patients over the age of 18 years. written informed consent (approved by the Institutional Review Board [IRB]/Independent Ethics Committee [IEC]) obtained prior to any study specific procedures. patient with mild to severe carotid artery disease", "candidate_expression": "((age) AND (carotid artery disease) AND (over 18 years) AND ((female) OR (male)) AND ((mild) OR (severe)))"}
{"candidate_id": "LLM01095", "doc_id": "NCT03192020_exc", "case_bucket": "or", "source_criterion": "recurrent contracture in the finger to be treated neurologic condition causing the loss of function of the finger to be treated contraindication for collagenase clostridium histolyticym (Xiapex/Xiaflex ®) pregnant or breast feeding TPED > 135° (Tubiana stage 4) in finger to be treated rheumatoid arthritis previous fracture in finger to be treated, which affects range of motion of MP or PIP joint age > 80 years", "candidate_expression": "((TPED > 135°) AND (Tubiana stage 4) AND (Xiaflex) AND (Xiapex) AND (affects range of motion MP joint PIP joint) AND (age > 80 years) AND (breast feeding) AND (collagenase clostridium histolyticym) AND (contracture recurrent finger to be treated) AND (contraindication) AND (fracture previous finger to be treated) AND (loss of function finger to be treated) AND (neurologic condition) AND (pregnant) AND (rheumatoid arthritis))"}
{"candidate_id": "LLM01096", "doc_id": "NCT03416413_inc", "case_bucket": "or", "source_criterion": "Adults over 18 years of age Symptomatic GSV or SSV vein reflux > 0.5 seconds on colour Duplex Varicose vein tributary requiring treatment", "candidate_expression": "((Adults) AND (age over 18 years of age) AND (colour Duplex) AND (treatment Varicose vein tributary requiring) AND ((GSV vein reflux) OR (SSV vein reflux)))"}
{"candidate_id": "LLM01097", "doc_id": "NCT01118871_inc", "case_bucket": "or", "source_criterion": "HIV-1 infected males or females over 18 years of age signed informed consent currently receiving a stable antiretroviral regimen comprising of: two or more licensed NRTIs one licensed NNRTI or boosted protease inhibitor no previous protease inhibitor resistance documented on HIV-1 genotypic resistance testing failure of current antiretroviral regimen due to: toxicity, intolerance or virological failure if receiving an NNRTI containing regimen at screening toxicity or intolerance if receiving a boosted-protease inhibitor regimen at screening (with plasma HIV RNA < 400 copies/mL at screening) willing to modify antiretroviral therapy, in accordance with the randomisation assignment no previous exposure to etravirine subjects in good health upon medical history, physical exam, and laboratory testing in the opinion of the investigator have no serologic evidence of active HBV infection evidenced by negative hepatitis B surface antigen female subjects who are heterosexually active and of childbearing potential (i.e., not surgically sterile or at least two years post menopausal) must practice contraception as follows from screening through completion of the study: barrier contraceptives (condom, diaphragm with spermicide) IUD or Depo PLUS a barrier contraceptive female subjects of childbearing potential must have a negative pregnancy test.", "candidate_expression": "((Depo) AND (HBV infection) AND (HIV-1) AND (HIV-1 genotypic resistance) AND (HIV-1 genotypic resistance testing) AND (HIV-1 infected) AND (IUD) AND (NNRTI) AND (NNRTI containing regimen at screening) AND (NRTI two or more licensed) AND (age over 18 years) AND (antiretroviral regimen) AND (antiretroviral regimen current) AND (antiretroviral therapy willing) AND (barrier contraceptive) AND (barrier contraceptives) AND (boosted protease inhibitor) AND (boosted-protease inhibitor regimen at screening) AND (childbearing potential) AND (condom) AND (contraception) AND (diaphragm with spermicide) AND (failure of current antiretroviral regimen) AND (female) AND (female subjects who are heterosexually active and of childbearing potential (i.e., not surgically sterile or at least two years post menopausal) must practice contraception as follows from screening through completion of the study:) AND (females) AND (good health) AND (hepatitis B surface antigen negative) AND (heterosexually active) AND (intolerance) AND (laboratory testing) AND (males) AND (medical history) AND (physical exam) AND (plasma HIV RNA < 400 copies/mL at screening) AND (pregnancy test negative) AND (protease inhibitor) AND (protease inhibitor resistance) AND (serologic evidence of active HBV infection) AND (signed informed consent) AND (surgically) AND (toxicity) AND (virological failure) AND NOT (etravirine previous) AND NOT (surgically sterile) AND NOT (post menopausal at least two years))"}
{"candidate_id": "LLM01098", "doc_id": "NCT03296488_exc", "case_bucket": "or", "source_criterion": "Body mass index less than 18 kg/m2 or greater than 30 kg/m2. History of previous open-laparotomy. Surgery with major complication, or need blood transfusion. History of hypersensitivity or adverse reaction to local anesthetics, opioid, or any ingredient of the medications administered in this study. Severe comorbidity. Chronic preoperative opioid consumption. Pregnant or breastfeeding. Inability to use the PCA device.", "candidate_expression": "((Body mass index) AND (Chronic) AND (History) AND (Inability) AND (Severe) AND (Surgery) AND (comorbidity) AND (need) AND (open-laparotomy) AND (opioid) AND (preoperative) AND (previous) AND (use the PCA) AND ((blood transfusion) OR (major complication)) AND ((adverse reaction) OR (hypersensitivity)) AND ((ingredient of the medications administered in this study) OR (local anesthetics) OR (opioid)) AND ((Pregnant) OR (breastfeeding)) AND ((greater than 30 kg/m2) OR (less than 18 kg/m2)))"}
{"candidate_id": "LLM01099", "doc_id": "NCT02923700_exc", "case_bucket": "or", "source_criterion": "age > 80 years; Kellgren-Lawrence score at X-ray evaluation > 3; major axial deviation (varus >5° , valgus > 5°), systemic disorders such as diabetes, rheumatoid arthritis, haematological diseases (coagulopathy), severe cardiovascular diseases, infections, immunodepression; patients in therapy with anticoagulants or antiaggregants; use of NSAIDs in the 5 days before blood donation; patients with Hb values < 11 g/dl and platelet values < 150,000/mmc.", "candidate_expression": "((< 11 g/dl) AND (< 150,000/mmc) AND (> 3) AND (> 5°) AND (> 80 years) AND (>5°) AND (Hb) AND (Kellgren-Lawrence score) AND (NSAIDs) AND (X-ray evaluation) AND (age) AND (antiaggregants) AND (anticoagulants) AND (cardiovascular diseases) AND (coagulopathy) AND (diabetes) AND (haematological diseases) AND (immunodepression) AND (in the 5 days before blood donation) AND (infections) AND (major axial deviation) AND (platelet) AND (rheumatoid arthritis) AND (severe) AND (systemic disorders) AND (therapy) AND (valgus) AND (varus))"}
{"candidate_id": "LLM01100", "doc_id": "NCT02473809_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Treatment with insulin Body weight > 140 kg HbA1c > 75 mmol/mol Treatment with GLP-1 analogues, Dipeptidyl peptidase-4 inhibitors, or glitazones Chronic kidney disease Hepatic disease Pancreatitis Inflammatory bowel disease Osteoporosis Family or personal history of medullary thyroid carcinoma Treatment with glucocorticoids Hormone replacement therapy Diabetic gastroparesis Pregnancy or lactation", "candidate_expression": "((> 140 kg) AND (> 75 mmol/mol) AND (Body weight) AND (Chronic kidney disease) AND (Diabetic gastroparesis) AND (Dipeptidyl peptidase-4 inhibitors) AND (Family) AND (GLP-1 analogues) AND (HbA1c) AND (Hepatic disease) AND (Hormone replacement therapy) AND (Inflammatory bowel disease) AND (Osteoporosis) AND (Pancreatitis) AND (Pregnancy) AND (Treatment) AND (Type 1 diabetes) AND (glitazones) AND (glucocorticoids) AND (insulin) AND (lactation) AND (medullary thyroid carcinoma) AND (personal history))"}
```
