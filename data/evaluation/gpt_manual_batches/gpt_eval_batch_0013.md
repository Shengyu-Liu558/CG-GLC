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
{"candidate_id": "LLM00301", "doc_id": "NCT02821819_inc", "case_bucket": "other", "source_criterion": "Premenopausal women 18-35 years old FSH levels < 10 mIU/ml AFC> 10 Regular cycles BMI < 28 Signed informed consent", "candidate_expression": "((AFC > 10) AND (BMI < 28) AND (FSH levels < 10 mIU/ml) AND (Premenopausal) AND (Regular cycles) AND (Signed informed consent) AND (old 18-35 years) AND (women))"}
{"candidate_id": "LLM00302", "doc_id": "NCT02579733_inc", "case_bucket": "other", "source_criterion": "Ulcerative colitis patients with moderate to severe activity who achieved a clinical remission by the first course of corticosteroids Newly diagnosed or without steroid use during last 1 year Endoscopic Mayo subscore >0", "candidate_expression": "((>0) AND (Endoscopic Mayo subscore) AND (Ulcerative colitis) AND (by the first course of corticosteroids) AND (clinical remission) AND (corticosteroids) AND (during last 1 year) AND (first course) AND (first course of corticosteroids) AND (moderate to severe) AND (steroid) AND (without))"}
{"candidate_id": "LLM00303", "doc_id": "NCT03132259_inc", "case_bucket": "other", "source_criterion": "Age18-65 ASA 1-2 Elective TNTS resection of Pituitary Tumor No narcotic before surgery as premedication Able to Extubate", "candidate_expression": "((ASA 1-2) AND (Age 18-65) AND (Extubate Able to) AND (Pituitary Tumor) AND (TNTS resection Elective) AND (surgery) AND NOT (narcotic before surgery))"}
{"candidate_id": "LLM00304", "doc_id": "NCT03062358_exc", "case_bucket": "or", "source_criterion": "Is currently participating or has participated in a study with an investigational agent or using an investigational device within 4 weeks of the first dose of study medication Has received sorafenib or oxaliplatin-based chemotherapy within 14 days of first dose of study medication Has had esophageal or gastric variceal bleeding within the last 6 months Has clinically apparent ascites on physical examination Has portal vein invasion at the main portal branch (Vp4), inferior vena cava, or cardiac involvement of HCC based on imaging Has had clinically diagnosed hepatic encephalopathy in the last 6 months Has had a solid organ or hematologic transplant Has had prior systemic therapy for HCC in the advanced (incurable) setting other than sorafenib or oxaliplatin-based chemotherapy, prior to start of study medication Has an active autoimmune disease that has required systemic treatment in the past 2 years. Replacement therapy is not considered a form of systemic treatment. Has a diagnosis of immunodeficiency or is receiving systemic steroid therapy or any other form of immunosuppressive therapy within 7 days prior to the first dose of study medication Has received locoregional therapy to liver (transcatheter chemoembolization [TACE], transcatheter embolization [TAE], hepatic arterial infusion [HAI], radiation, radioembolization, or ablation) or other site within 4 weeks prior to the first dose of study medication Has had major surgery to liver or other site within 4 weeks prior to the first dose of study medication Has had a minor surgery ≤7 days prior to the first dose of study medication Has not recovered adequately (i.e., Grade ≤1 or baseline) from the toxicity and/or complications from any intervention prior to study start Has a diagnosed additional malignancy within 3 years prior to first dose of study medication with the exception of curatively treated basal cell carcinoma of the skin, squamous cell carcinoma of the skin and/or curatively resected in situ cancers Has a known history of, or any evidence of, central nervous system (CNS) metastases and/or carcinomatous meningitis Has a history of (non-infectious) pneumonitis that required steroids or current pneumonitis Has an active infection requiring systemic therapy Is pregnant or breast feeding or expecting to conceive or father starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication Has received prior immunotherapy with an anti-Programmed Cell Death Receptor 1 (PD-1), Programmed Cell Death Receptor Ligand 1 (anti-PD-L1), or anti- Programmed Cell Death Receptor Ligand 2 (PD-L2) or has previously participated in clinical studies with pembrolizumab Has a known history of human immunodeficiency virus (HIV) Has untreated active Hepatitis B Has hepatitis C in which participants received therapy for HCV <4 weeks prior to receiving pembrolizumab Has received a live vaccine within 30 days prior to the first dose of study therapy", "candidate_expression": "((HCC) AND (Hepatitis B untreated active) AND (Programmed Cell Death Receptor Ligand 1 (anti-PD-L1)) AND (ablation other site) AND (anti- Programmed Cell Death Receptor Ligand 2 (PD-L2)) AND (anti-Programmed Cell Death Receptor 1 (PD-1)) AND (ascites) AND (autoimmune disease active in the past 2 years) AND (basal cell carcinoma of the skin curatively treated) AND (breast feeding) AND (carcinomatous meningitis) AND (cardiac involvement) AND (central nervous system (CNS) metastases) AND (chemotherapy sorafenib or oxaliplatin-based within 14 days) AND (esophageal variceal bleeding) AND (expecting to conceive) AND (expecting to father starting from the first dose of study medication throughout the study period) AND (for up to 120 days after the last dose of study medication the last dose of study medication) AND (gastric variceal bleeding) AND (hematologic transplant) AND (hepatic arterial infusion [HAI]) AND (hepatic encephalopathy in the last 6 months) AND (hepatitis C) AND (human immunodeficiency virus (HIV) history) AND (imaging) AND (immunodeficiency) AND (immunosuppressive therapy) AND (immunotherapy) AND (in situ cancers curatively resected) AND (infection active requiring systemic therapy) AND (live vaccine 30 days prior) AND (locoregional therapy liver within 4 weeks prior) AND (major surgery liver within 4 weeks prior other site) AND (malignancy additional within 3 years prior to first dose of study medication) AND (minor surgery ≤7 days prior) AND (non-infectious) pneumonitis history) AND (oxaliplatin) AND (participated in clinical studies with pembrolizumab) AND (pembrolizumab) AND (pneumonitis current) AND (portal vein invasion main portal branch (Vp4) inferior vena cava) AND (pregnant) AND (radiation) AND (radioembolization) AND (recovered adequately) AND (resected curatively) AND (solid organ transplant) AND (sorafenib) AND (squamous cell carcinoma of the skin) AND (steroids) AND (systemic steroid therapy) AND (systemic therapy) AND (systemic treatment) AND (therapy for HCV <4 weeks prior) AND (transcatheter chemoembolization [TACE]) AND (transcatheter embolization [TAE]) AND (treated curatively) AND NOT (chemotherapy sorafenib or oxaliplatin-based))"}
{"candidate_id": "LLM00305", "doc_id": "NCT03624881_inc", "case_bucket": "or", "source_criterion": "Symptomatic paroxysmal AF who had at least one AF episode electrocardiographically documented within one (1) year prior to enrollment. Documentation may include electrocardiogram (ECG); Transtelephonic monitoring (TTM), Holter monitor or telemetry strip Failed at least one antiarrhythmic drug (AAD) (Class I or III antiarrhythmic drugs) as evidenced by recurrent symptomatic AF, or intolerable to the AAD Age 18 years or older Signed Patient Informed Consent Form (ICF) Able and willing to comply with all pre-, post-, and follow-up testing and requirements", "candidate_expression": "((18 years or older) AND (AAD) AND (AF episode) AND (Age) AND (Class I antiarrhythmic drugs) AND (Holter monitor) AND (III antiarrhythmic drugs) AND (Signed Patient Informed Consent Form (ICF)) AND (Symptomatic) AND (Transtelephonic monitoring (TTM)) AND (antiarrhythmic drug (AAD)) AND (at least one) AND (electrocardiogram (ECG)) AND (electrocardiographically) AND (electrocardiographically documented) AND (enrollment) AND (intolerable) AND (paroxysmal AF) AND (recurrent symptomatic AF) AND (telemetry strip) AND (within one (1) year prior to enrollment))"}
{"candidate_id": "LLM00306", "doc_id": "NCT02630628_inc", "case_bucket": "or", "source_criterion": "Biopsy-proven LN Class III/IV±V (ISN/RPS 2003), with biopsy performed within 12 weeks of randomization. Positive anti-dsDNA. Active LN with proteinuria (urine protein/creatinine ratio >1.0 or 24-hr urine protein >1.0 g at baseline), with or without hematuria. Both 'incident' (i.e. new) patients and 'flare' patients can be included.", "candidate_expression": "((24-hr urine protein >1.0 g) AND (LN Active) AND (LN Class III/IV±V) AND (anti-dsDNA Positive) AND (biopsy within 12 weeks) AND (hematuria) AND (proteinuria) AND (urine protein/creatinine ratio >1.0))"}
{"candidate_id": "LLM00307", "doc_id": "NCT02595190_inc", "case_bucket": "or", "source_criterion": "1. Diagnosed with symptomatic sacral perineurial cysts(e.g., lumbosacral or perineal pain, fecal or urinary functions change, sexual function change, lower limb radiation pain, muscle abate, paresthesia, etc) 2. Visual analog scale more than or equal to 4 3. Signed the informed consent 4. Years, range 18-60 5. Self-rating anxiety scale (SAS) and self-rating depression scale (SDS) scores < 50 6. No Congenital,Mental and other Nervous system diseases 7. No Serious Cardiac,Pulmonary,Hepatic and Nephritic disease 8. No history of drug allergy 9. No pain(including dysmenorrhea) or drug use (e.g., antipyretics,sleeping pills) within the last month 10. MRI finding of sacral perineurial cysts, but without any clinical symptoms, included in the negative control group 11. MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group", "candidate_expression": "((Cardiac) AND (Congenital diseases) AND (Hepatic) AND (MRI finding healthy volunteers don't have sacral perineurial cysts, included in the negative control groupblank control group) AND (Mental disease) AND (Nephritic disease) AND (Nervous system diseases) AND (Pulmonary) AND (SAS) AND (SDS) AND (Self-rating anxiety scale) AND (Signed the informed consent) AND (Visual analog scale more than or equal to 4) AND (Years 18-60) AND (allergy) AND (drug last month) AND (dysmenorrhea) AND (functions change, fecal) AND (lower limb radiation pain) AND (lumbosacral pain) AND (muscle abate) AND (paresthesia) AND (perineal pain) AND (sacral perineurial cysts( symptomatic) AND (self-rating depression scale) AND (sexual function change) AND (urinary functions change) AND NOT (drug) AND NOT (Cardiac,Pulmonary,Hepatic) AND NOT (pain))"}
{"candidate_id": "LLM00308", "doc_id": "NCT03360981_inc", "case_bucket": "or", "source_criterion": "patients aged >18, <75, left ventricle ejection fraction (LVEF) >50%, multivessel coronary disease detected by coronarography, indication to receive a CABG, stable CAD. All diabetics and non diabetics.", "candidate_expression": "((CABG indication to receive) AND (CAD stable) AND (LVEF) AND (aged >18, <75) AND (coronarography) AND (diabetics) AND (left ventricle ejection fraction >50%) AND (multivessel coronary disease) AND (non diabetics))"}
{"candidate_id": "LLM00309", "doc_id": "NCT03099863_exc", "case_bucket": "or", "source_criterion": "Surgeries that include: intradetrusor Botox, vaginal mesh excision, and fistula repair Pregnancy History of nephrolithiasis Allergy to study medications Congenital urogenital anomaly Neurogenic bladder", "candidate_expression": "((Allergy) AND (Congenital) AND (History) AND (Neurogenic bladder) AND (Pregnancy) AND (intradetrusor) AND (nephrolithiasis) AND (study medications) AND (urogenital anomaly) AND (vaginal mesh) AND ((Botox) OR (fistula repair) OR (vaginal mesh excision)))"}
{"candidate_id": "LLM00310", "doc_id": "NCT03400735_inc", "case_bucket": "other", "source_criterion": "The diagnosis of chronic bronchitis The diagnosis of community-acquired pneumoniae FEV1 value = 30-80% The diagnosis of mild-severe acute exacerbation of chronic bronchitis (AECB) Oxygen saturation < 90%", "candidate_expression": "((AECB) AND (FEV1 value = 30-80%) AND (Oxygen saturation < 90%) AND (chronic bronchitis) AND (community-acquired pneumoniae) AND (exacerbation of chronic bronchitis mild-severe acute))"}
{"candidate_id": "LLM00311", "doc_id": "NCT03099408_exc", "case_bucket": "or", "source_criterion": "Presence of another vaginal infection or STD Allergy to metronidazole Pregnant or nursing Use of oral or intravaginal antibiotics within the past 2 weeks HIV or other chronic disease Inability to keep return appointments Contraindications for Lactobacillus Vaginal Suppositories(those without sexual history)", "candidate_expression": "((Allergy) AND (Contraindications) AND (Inability to keep return appointments) AND (Lactobacillus Vaginal Suppositories) AND (another) AND (metronidazole) AND (other) AND (sexual history) AND (within the past 2 weeks) AND (without) AND ((HIV) OR (chronic disease)) AND ((STD) OR (vaginal infection)) AND ((Pregnant) OR (nursing)) AND ((intravaginal antibiotics) OR (oral antibiotics)))"}
{"candidate_id": "LLM00312", "doc_id": "NCT02408120_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00313", "doc_id": "NCT01743755_exc", "case_bucket": "or", "source_criterion": "Immunocompromised patients: Patients with a known congenital or acquired immunodeficiency. Patients who received chemotherapy less than 6 weeks ago. Patients who received corticosteroids in the last 6 weeks. Patients who received immunosuppressive medication in the last 6 weeks (e.g. cyclosporin, cyclophosphamide, azathioprine). Patients with chronic obstructive pulmonary disease who are on systemic corticosteroids. Patients who require intensive care unit treatment. Patients with tropical worm infection. Patients with dexamethasone intolerance. Pregnant and breastfeeding women.", "candidate_expression": "((Immunocompromised) AND (Pregnant and breastfeeding women) AND (chemotherapy less than 6 weeks ago) AND (chronic obstructive pulmonary disease) AND (corticosteroids in the last 6 weeks) AND (dexamethasone) AND (immunodeficiency) AND (immunosuppressive medication in the last 6 weeks) AND (intensive care unit) AND (intolerance) AND (systemic corticosteroids) AND (tropical worm infection) AND ((azathioprine) OR (cyclophosphamide) OR (cyclosporin)) AND ((acquired) OR (congenital)))"}
{"candidate_id": "LLM00314", "doc_id": "NCT03305575_inc", "case_bucket": "other", "source_criterion": "ASA classification II or III females Age: 18-45 years old BMI = 50 kg/m2 Singleton pregnancy Simple prophylactic cervical cerclage Planning neuraxial anesthesia", "candidate_expression": "((ASA classification II or III) AND (Age 18-45 years old) AND (BMI = 50 kg/m2) AND (Singleton pregnancy) AND (cervical cerclage Simple prophylactic) AND (females) AND (neuraxial anesthesia Planning))"}
{"candidate_id": "LLM00315", "doc_id": "NCT02593409_inc", "case_bucket": "other", "source_criterion": "age =18 at screening not intending to move away from the clinic's catchment area for the next 2 years HIV-1 antibody negative reports commercial sex work contact information is provided written informed consent", "candidate_expression": "((=18) AND (HIV-1 antibody) AND (age) AND (commercial sex work) AND (contact information is provided) AND (negative) AND (written informed consent))"}
{"candidate_id": "LLM00316", "doc_id": "NCT03228017_exc", "case_bucket": "or", "source_criterion": "Unable to speak Spanish or English Active smoking (within the past year) Autoimmune, rheumatologic or inflammatory disease which are not psoriasis or psoriatic arthritis Known active cancer receiving treatment Pregnancy Anemia (hemoglobin < 9 mg/dl) or thrombocytopenia (Platelet count <75), or thrombocytosis (Platelet count >600) A history of severe bleeding or bleeding disorders Current medication use which interact with either aspirin or atorvastatin Chronic kidney disease (CrCl < 30ml/min) Congestive heart failure Currently taking aspirin or a statin. NSAID use within the past 48 hours", "candidate_expression": "((< 30ml/min) AND (< 9 mg/dl) AND (<75) AND (>600) AND (Active) AND (Anemia) AND (Chronic kidney disease) AND (Congestive heart failure) AND (CrCl) AND (Current) AND (NSAID) AND (Platelet count) AND (Pregnancy) AND (active) AND (aspirin) AND (atorvastatin) AND (bleeding) AND (bleeding disorders) AND (cancer) AND (disease Autoimmune) AND (disease rheumatologic) AND (hemoglobin) AND (history) AND (inflammatory disease) AND (interact) AND (medication) AND (not) AND (psoriasis) AND (psoriatic arthritis) AND (severe) AND (smoking) AND (statin) AND (thrombocytopenia) AND (thrombocytosis) AND (treatment) AND (within the past 48 hours) AND (within the past year))"}
{"candidate_id": "LLM00317", "doc_id": "NCT03299517_exc", "case_bucket": "or", "source_criterion": "Pregnancy Hemodynamic instability Body mass index greater than 40 kg / m2 Use of intravenous amiodarone or lidocaine in the last 24 hours Acute coronary syndrome Presence of tachycardia with irregular or supraventricular RR Contraindications to study drugs", "candidate_expression": "((Acute coronary syndrome) AND (Body mass index) AND (Contraindications) AND (Hemodynamic instability) AND (Pregnancy) AND (amiodarone) AND (greater than 40 kg / m2) AND (in the last 24 hours) AND (intravenous) AND (irregular RR) AND (lidocaine) AND (study drugs) AND (supraventricular RR) AND (tachycardia))"}
{"candidate_id": "LLM00318", "doc_id": "NCT02106624_exc", "case_bucket": "other", "source_criterion": "irreversible status of primary disease any history of malnutrition before enrollment history of steroid cortisol administration severe liver dysfunction (Child-Pugh Score C) pregnancy refuse to enrollment re-admission to ICU and has been enrolled during former admission to ICU", "candidate_expression": "((C) AND (Child-Pugh Score) AND (ICU) AND (before enrollment) AND (irreversible status) AND (liver dysfunction) AND (malnutrition) AND (pregnancy) AND (primary disease) AND (re-admission) AND (refuse to enrollment) AND (severe) AND (steroid cortisol))"}
{"candidate_id": "LLM00319", "doc_id": "NCT03479502_inc", "case_bucket": "other", "source_criterion": "18 years of age and older, diagnosis of stage II adhesive capsulitis as determined by clinical examination of the treating physician, and absence of abnormal findings on X-ray.", "candidate_expression": "((X-ray) AND (adhesive capsulitis stage II as determined by clinical examination) AND (age 18 years and older) AND (clinical examination) AND NOT (abnormal findings))"}
{"candidate_id": "LLM00320", "doc_id": "NCT02933671_exc", "case_bucket": "or", "source_criterion": "ASA 4 or 5 revision hip arthroplasty diagnosis of chronic pain daily chronic opioid use (over 3 months of continuous opioid use) inability to communicate pain scores or need for analgesia acute hip fracture Infection at the site of block placement Age under 18 years old or greater than 75 years old Pregnant women Intolerance/allergy to local anesthetics Weight <50 kg Suspected, or known addiction to or abuse of illicit drug(s), prescription medicine(s), or alcohol within the past 2 years. Uncontrolled anxiety, schizophrenia, or other psychiatric disorder that, in the opinion of the investigator, may interfere with study assessments or compliance Current or historical evidence of any clinically significant disease or condition that, in the opinion of the investigator, may increase the risk of surgery or complicate the subject's postoperative course.", "candidate_expression": "((4 or 5) AND (<50 kg) AND (ASA) AND (Age) AND (Infection) AND (Pregnant women) AND (Weight) AND (acute) AND (chronic) AND (chronic pain) AND (hip fracture) AND (inability to communicate pain scores or need for analgesia) AND (local anesthetics) AND (opioid) AND (over 3 months) AND (past 2 years) AND (revision hip arthroplasty) AND (site of block placement) AND (under 18 years old or greater than 75 years old) AND ((Intolerance) OR (allergy)) AND ((abuse) OR (addiction)) AND ((alcohol) OR (illicit drug) OR (prescription medicine)) AND ((anxiety) OR (psychiatric disorder) OR (schizophrenia)))"}
{"candidate_id": "LLM00321", "doc_id": "NCT01051414_exc", "case_bucket": "or", "source_criterion": "Subjects with evidence of liver cirrhosis Evidence of HCC Co-infection with hepatitis B virus, HIV", "candidate_expression": "((Evidence) AND (HCC) AND (evidence) AND (liver cirrhosis) AND ((HIV) OR (hepatitis B virus)))"}
{"candidate_id": "LLM00322", "doc_id": "NCT01064752_inc", "case_bucket": "other", "source_criterion": "1. HIV infection with plasma and CSF HIV RNA concentrations (using Roche Amplicor assay) > 1,000 copies/ mL (available after baseline LP). 2. Off antiretroviral therapy (ART) for > 6 weeks before the study and no plans to begin treatment for the study duration. (The decision of whether or not a subject takes antiretroviral therapy will be made by the subject in consultation with his/her primary care provider prior to screening for this study.) 3. Predicted adherence to the medication. 4. Capable of providing informed consent. 5. > 18 years old 6. CD4 cell counts >150 cells/μL (though likely most, if not all, will be >250 cells/μL). 7. When available, subjects will be screened for stability of blood CD4 and HIV RNA levels.", "candidate_expression": "((18 years) AND (> 1,000 copies/ mL) AND (> 6 weeks before the study) AND (>150 cells/μL) AND (>250 cells/μL) AND (CD4 cell counts) AND (CSF HIV RNA concentration) AND (Capable of providing informed consent.) AND (HIV infection) AND (Off antiretroviral therapy (ART)) AND (Roche Amplicor assay) AND (antiretroviral therapy (ART)) AND (for the study duration) AND (no) AND (old) AND (plans to begin) AND (plasma concentration) AND (study) AND (the study) AND (treatment))"}
{"candidate_id": "LLM00323", "doc_id": "NCT01891513_inc", "case_bucket": "or", "source_criterion": "Age 65 years and older Hypertension - untreated (Systolic Blood Pressure (SBP) ≥ 140 mm Hg or Diastolic Blood Pressure (DBP) ≥ 90 mm Hg) or treated Physical limitations evidenced by either: Score ≤ 10 on the Short Physical Performance Battery OR Walking speed < 1.2 m/sec during 400 m usual-paced test Sedentary lifestyle, defined as <150 min/wk of moderate physical activity as assessed by CHAMPS questionnaire Willingness to participate in all study procedures", "candidate_expression": "((400 m usual-paced test) AND (65 years and older) AND (< 1.2 m/sec) AND (<150 min/wk) AND (Age) AND (CHAMPS questionnaire) AND (Hypertension) AND (Score ≤ 10) AND (≥ 140 mm Hg) AND (≥ 90 mm Hg) AND ((treated) OR (untreated)) AND ((Short Physical Performance Battery) OR (Walking speed)) AND ((Sedentary lifestyle) OR (moderate physical activity)) AND ((Diastolic Blood Pressure (DBP)) OR (Systolic Blood Pressure (SBP))))"}
{"candidate_id": "LLM00324", "doc_id": "NCT02773173_inc", "case_bucket": "other", "source_criterion": "Patients older than 18 years Classification of the American Society of Anesthesiologists (ASA I-III) No cognitive deficits Signed informed consent prior to surgery", "candidate_expression": "((ASA) AND (Classification of the American Society of Anesthesiologists) AND (I-III) AND (No) AND (Signed informed consent prior to surgery) AND (cognitive deficits) AND (older than 18) AND (years))"}
{"candidate_id": "LLM00325", "doc_id": "NCT02056626_exc", "case_bucket": "or", "source_criterion": "abnormal renal function currently pregnant, or trying to become pregnant being treated with a beta-blocker use of illicit drugs", "candidate_expression": "((abnormal renal function) AND (beta-blocker) AND (illicit drugs) AND (treated) AND ((pregnant currently) OR (pregnant trying to become)))"}
```
