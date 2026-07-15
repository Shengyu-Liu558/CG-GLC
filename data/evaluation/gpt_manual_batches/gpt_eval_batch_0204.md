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
{"candidate_id": "LLM05076", "doc_id": "NCT02548013_exc", "case_bucket": "other", "source_criterion": "1. Patient with equivocal diagnosis of rupture of membranes 2. advanced labor 3. intrauterine infection 4. vaginal bleeding or 5. non reassuring fetal heart rate.", "candidate_expression": "((advanced labor) AND (equivocal) AND (fetal heart rate) AND (intrauterine infection) AND (non reassuring) AND (rupture of membranes) AND (vaginal bleeding))"}
{"candidate_id": "LLM05077", "doc_id": "NCT00183885_exc", "case_bucket": "or", "source_criterion": "Patients who have received prior chemotherapy for unresectable disease Patients with any active or uncontrolled infection, including known HIV infection. (Patients with active hepatitis B will be placed on lamivudine. Patients with active hepatitis C will be eligible if liver tests qualify (5.1.9) Patients with psychiatric disorders that would interfere with consent or follow-up. Pregnant or lactating women. Men and women of reproductive potential may not participate unless they have agreed to use an effective contraceptive method. Patients with any other severe concurrent disease, which in the judgment of the investigator, would make the patient inappropriate for entry into this study.", "candidate_expression": "((HIV infection) AND (active) AND (chemotherapy) AND (concurrent disease) AND (effective contraceptive method) AND (entry into this study) AND (hepatitis B) AND (hepatitis C) AND (inappropriate for) AND (infection) AND (lamivudine) AND (liver tests) AND (psychiatric disorders) AND (qualify) AND (reproductive potential) AND (severe) AND (uncontrolled) AND (unresectable disease) AND (women) AND ((interfere with consent) OR (interfere with follow-up)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM05078", "doc_id": "NCT03355469_exc", "case_bucket": "or", "source_criterion": "Morbidly obese patients (BMI >47 kg/m2) and overweight/lean patients (BMI <27 kg/m2) Evidence of type 1 diabetes and diabetics requiring insulin therapy. Subjects who have not been weight stable (>2 kg weight change in past 3 months) Subjects who have been recently active (>30 min of moderate/high intensity exercise, 2 times/week). Subjects who are smokers or who have quit smoking <5 years ago Subjects prescribed metformin or have taken metformin within 1 year. Subjects with abnormal estimated glomerular filtration rate (eGFR). Hypertriglyceridemic (>400 mg/dl) and hypercholesterolemic (>260 mg/dl) subjects Hypertensive (>160/100 mmHg) Subjects currently taking medications that affect heart rate and rhythm (i.e. Ca++ channel blockers, nitrates, alpha- or beta-blockers). Subjects with a history of significant metabolic, cardiac, congestive heart failure, cerebrovascular, hematological, pulmonary, gastrointestinal, liver, renal, or endocrine disease or cancer that in the investigator's opinion would interfere with or alter the outcome measures, or impact subject safety. Pregnant (as evidenced by positive pregnancy test) or nursing women Subjects with contraindications to participation in an exercise training program Currently taking active weight suppression medication (e.g. phentermine,orlistat, lorcaserin, naltrexone-bupropion in combination, liraglutide, benzephetamine, diethylpropion, phendimetrazine) Known hypersensitivity to perflutren (contained in Definity)", "candidate_expression": "((2 times/week) AND (<27 kg/m2) AND (<5 years ago) AND (>160/100 mmHg) AND (>2 kg) AND (>260 mg/dl) AND (>30 min) AND (>400 mg/dl) AND (>47 kg/m2) AND (BMI) AND (Ca++ channel blockers) AND (Definity) AND (Hypertensive) AND (Hypertriglyceridemic) AND (Morbidly obese) AND (Pregnant) AND (abnormal) AND (active) AND (active weight suppression medication) AND (alpha- blockers) AND (benzephetamine) AND (beta-blockers) AND (cancer) AND (cardiac) AND (cerebrovascular) AND (cholesterol) AND (congestive heart failure) AND (contraindications) AND (diabetics) AND (diethylpropion) AND (disease) AND (endocrine) AND (estimated glomerular filtration rate (eGFR)) AND (gastrointestinal) AND (hematological) AND (history) AND (hypercholesterolemic) AND (hypersensitivity) AND (in past 3 months) AND (insulin) AND (insulin therapy) AND (lean) AND (liraglutide) AND (liver) AND (lorcaserin) AND (medications) AND (metabolic) AND (metformin) AND (moderate/high intensity exercise) AND (naltrexone-bupropion in combination) AND (nitrates) AND (not) AND (nursing) AND (orlistat) AND (overweight) AND (participation in an exercise training program) AND (perflutren) AND (phendimetrazine) AND (phentermine) AND (positive) AND (pregnancy test) AND (pulmonary) AND (quit smoking) AND (recently) AND (renal) AND (requiring insulin therapy) AND (significant) AND (smokers) AND (that affect heart rate) AND (that affect heart rhythm) AND (type 1 diabetes) AND (weight change) AND (weight stable) AND (within 1 year) AND (women))"}
{"candidate_id": "LLM05079", "doc_id": "NCT01911650_exc", "case_bucket": "or", "source_criterion": "1. bilateral AT 2. insertional AT 3. local steroid injection within 6 weeks or physical therapy within 4 weeks 4. inability to comply with follow-up criteria 5. history of surgery on the Achilles tendon or systemic diseases (general inflammatory diseases such as rheumatologic disorders and diabetes) 6. daily use of opioids for pain 7. anticoagulation or immunosuppressive therapy 8. intent to use NSAIDs or steroids 9. self-reported pregnancy", "candidate_expression": "((NSAIDs) AND (anticoagulation therapy) AND (bilateral AT) AND (daily) AND (diabetes) AND (general inflammatory diseases) AND (history) AND (immunosuppressive therapy) AND (inability to comply with follow-up criteria) AND (insertional AT) AND (local steroid injection) AND (opioids) AND (pain) AND (physical therapy) AND (pregnancy) AND (rheumatologic disorders) AND (steroids) AND (surgery on the Achilles tendon) AND (systemic diseases) AND (within 4 weeks) AND (within 6 weeks))"}
{"candidate_id": "LLM05080", "doc_id": "NCT03089086_exc", "case_bucket": "other", "source_criterion": "Previous anaphylaxis following any component of Bexsero vaccine Previous receipt of meningococcal B vaccine (Bexsero) Known pregnancy", "candidate_expression": "((Bexsero) AND (Bexsero vaccine) AND (Previous) AND (anaphylaxis) AND (meningococcal B vaccine) AND (pregnancy))"}
{"candidate_id": "LLM05081", "doc_id": "NCT02691793_inc", "case_bucket": "or", "source_criterion": "Provision of fully informed consent prior to study specific procedures. Patients must be >= 19 years of age RET fusion positive or FGFR2 fusion/other FGFR mutation Refractory solid tumor and/or specific sensitivity to Sunitinib by Avatar scan that has progressed following standard therapy or that has not responded to standard therapy or for which there is no standard therapy. ECOG Performance status0-2 Have measurable or evaluated disease based on RECIST 1.1 as determined by investigator. Absolute neutrophil count >= 1.5 x 109/L, Hemoglobin >= 9g/dL, Platelets>=100 x 109/L Bilirubin <= 1.5 x upper limit of normal AST/ALT <= 2.5 X upper limit of normal(5.0 x upper limit of normal, for subject with liver metastases) Creatinine<= 1.5 X UNL Patients of child-bearing potential should be using adequate contraceptive measures should not be breast feeding and must have a negative pregnancy test prior to start of dosing Adequate heart function", "candidate_expression": "((0-2) AND (5.0 x upper limit of normal) AND (<= 1.5 X UNL) AND (<= 1.5 x upper limit of normal) AND (<= 2.5 X upper limit of normal() AND (>= 1.5 x 109/L) AND (>= 19 years) AND (>= 9g/dL,) AND (>=100 x 109/L) AND (ALT) AND (AST) AND (Absolute neutrophil count) AND (Adequate) AND (Adequate heart function) AND (Bilirubin) AND (Creatinine) AND (ECOG Performance status) AND (FGFR mutation) AND (FGFR2 fusion) AND (Hemoglobin) AND (Platelets) AND (Provision of fully informed consent prior to study specific procedures) AND (RET fusion) AND (Refractory) AND (Sunitinib) AND (adequate contraceptive measures) AND (age) AND (breast feeding) AND (child-bearing potential) AND (heart function) AND (liver metastases) AND (negative) AND (not be) AND (positive) AND (pregnancy test) AND (prior to start of dosing) AND (sensitivity) AND (solid tumor) AND (start of dosing))"}
{"candidate_id": "LLM05082", "doc_id": "NCT02226887_inc", "case_bucket": "other", "source_criterion": "Patients undergoing a loop ileostomy closure", "candidate_expression": "(loop ileostomy closure)"}
{"candidate_id": "LLM05083", "doc_id": "NCT02251249_exc", "case_bucket": "or", "source_criterion": "Allergy or contraindication to paracetamol, Prasugrel or Ticagrelor Paracetamol ingestion in the previous 48 hours Patient treated with drugs supposed to alter gastric emptying times (calcium antagonists, Alimentary tract treatments, opioid analgesics, tricyclic antidepressants, antibiotics). Conditions or pathologies supposed to alter gastric emptying times (Thyroid dysfunction, chronic renal failure, Parkinson's disease, scleroderma, amyloidosis, any gastrointestinal disease, any not cured malignancy, and any advanced psychiatric or neurological disease). Presence of vomiting Cardiogenic shock, ventricular arrhythmia or resuscitated cardiac arrest Hepatic insufficiency Severe respiratory disease Pregnant or breastfeeding women", "candidate_expression": "((Hepatic insufficiency) AND (Paracetamol) AND (Severe) AND (advanced) AND (drugs supposed to alter gastric emptying times) AND (in the previous 48 hours) AND (respiratory disease) AND (resuscitated) AND (vomiting) AND (women) AND ((Allergy) OR (contraindication)) AND ((Alimentary tract treatments) OR (antibiotics) OR (calcium antagonists) OR (opioid analgesics) OR (tricyclic antidepressants)) AND ((Parkinson's disease) OR (Thyroid dysfunction) OR (amyloidosis) OR (chronic renal failure) OR (gastrointestinal disease) OR (malignancy) OR (scleroderma)) AND ((neurological disease) OR (psychiatric disease)) AND ((Cardiogenic shock) OR (cardiac arrest) OR (ventricular arrhythmia)) AND ((Pregnant) OR (breastfeeding)) AND ((Conditions supposed to alter gastric emptying times) OR (pathologies supposed to alter gastric emptying times)) AND ((Prasugrel) OR (Ticagrelor) OR (paracetamol)))"}
{"candidate_id": "LLM05084", "doc_id": "NCT02787070_exc", "case_bucket": "other", "source_criterion": "General danger signs or symptoms of severe malaria Anaemia, defined as Hb <9g/dl G6PD deficiency (as determined by FST) Pregnant women as determined by Urine ß-HCG pregnancy test Known hypersensitivity to any of the drugs given", "candidate_expression": "((<9g/dl) AND (Anaemia) AND (G6PD deficiency) AND (Hb) AND (Pregnant women as determined by Urine ß-HCG pregnancy test) AND (drugs) AND (hypersensitivity) AND (malaria) AND (severe))"}
{"candidate_id": "LLM05085", "doc_id": "NCT02301962_inc", "case_bucket": "or", "source_criterion": "Subject or subject's legally acceptable representative has provided informed consent. Male or female >=18 years of age. Histologically or cytologically confirmed diagnosis of adenocarcinoma of the colon or rectum. Wild-type KRAS (without mutation in exon 2 [codons 12 and 13], exon 3 [codons 59 and 61], and exon 4 [codons 117 and 146]) and wild-type NRAS (without mutation in exon 2 [codons 12 and 13], exon 3 [codons 59 and 61], and exon 4 [codons 117 and 146]) tumor status. Eastern Cooperative Oncology Group (ECOG) performance status of 0, 1 or 2. Measurable or non-measurable disease per RECIST Version 1.1. Must have failed after fluoropyrimidine-, oxaliplatin-, and irinotecan-containing chemotherapy regimens for metastatic disease. Failure is defined as either disease progression (clinical or radiological) or intolerance to the regimen. Metastatic relapse within 6 months after completing adjuvant chemotherapy (with either an irinotecan or oxaliplatin containing regimen) will also be considered as treatment failure of a prior regimen for metastatic disease. Laboratory: Adequate baseline organ function defined by (<=7 days prior to first dose of study treatment). Hematologic function, as follows: Absolute neutrophil count (ANC) >=1.5 x 10^9/Liter (L), Platelet count >=75 x 10^9/L, Hemoglobin >=8.0 gram/deciliter (g/dL). Renal function, as follows: Creatinine <=1.5 x upper limit of normal (ULN). Hepatic function, as follows: Aspartate aminotransferase (AST) <=3 x ULN, Alanine aminotransferase (ALT) <=3 x ULN, Total Bilirubin <=1.5 x ULN. Metabolic function, as follows: Serum Magnesium within normal limits. Serum Calcium within normal limits. Serum Potassium within normal limits. All prior treatment related toxicities common terminology criteria for adverse events (CTCAE) version 4.03 <=Grade 1 at the time of enrollment. Women of childbearing potential must have a negative serum pregnancy test within 7 days of first dose of study treatment and agree to use adequate contraception, during the study and for 2 months following the last dose of study treatment. Men with a female partner of childbearing potential must have either had a prior vasectomy or agree to use adequate contraception, from time of signing informed consent until 5 months after the last dose of study treatment.", "candidate_expression": "((0, 1 or 2) AND (<=1.5 x ULN) AND (<=1.5 x upper limit of normal (ULN)) AND (<=3 x ULN) AND (<=7 days prior to first dose of study treatment) AND (>=1.5 x 10^9/Liter (L)) AND (>=18 years) AND (>=75 x 10^9/L) AND (>=8.0 gram/deciliter (g/dL)) AND (Absolute neutrophil count (ANC)) AND (Adequate baseline organ function) AND (Alanine aminotransferase (ALT)) AND (Creatinine) AND (Eastern Cooperative Oncology Group (ECOG) performance status) AND (Hemoglobin) AND (Histologically) AND (Male) AND (Measurable disease) AND (Metastatic relapse) AND (Platelet count) AND (RECIST Version 1.1) AND (Serum Calcium) AND (Serum Magnesium) AND (Serum Potassium) AND (Subject or subject's legally acceptable representative has provided informed consent.) AND (Total Bilirubin) AND (Women of childbearing potential must have a negative serum pregnancy test within 7 days of first dose of study treatment and agree to use adequate contraception, during the study and for 2 months following the last dose of study treatment. Men with a female partner of childbearing potential must have either had a prior vasectomy or agree to use adequate contraception, from time of signing informed consent until 5 months after the last dose of study treatment.) AND (adenocarcinoma) AND (after completing adjuvant chemotherapy) AND (age) AND (colon) AND (confirmed) AND (cytologically) AND (disease progression) AND (failed) AND (female) AND (first dose of study treatment) AND (fluoropyrimidine- containing chemotherapy) AND (intolerance) AND (irinotecan containing regimen) AND (irinotecan-containing chemotherapy) AND (metastatic disease) AND (non-measurable disease) AND (oxaliplatin containing regimen) AND (oxaliplatin- containing chemotherapy) AND (rectum) AND (spartate aminotransferase (AST)) AND (the regimen) AND (within 6 months after completing adjuvant chemotherapy) AND (within normal limits))"}
{"candidate_id": "LLM05086", "doc_id": "NCT02715518_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05087", "doc_id": "NCT02695992_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure Ischemic heart disease Hypotension (Systolic blood pressure <100 mmHg) Treatment with class I or III antiarrhythmic drugs Severe hepatic or renal failure Pregnancy or lactation Hypersensitivity or contradictions to study drugs Atrio-ventricular conduction disturbances Thyrotoxicosis Life limiting disease or substance abuse which may affect participation", "candidate_expression": "((Atrio-ventricular conduction disturbances) AND (Congestive heart failure) AND (Hypersensitivity) AND (Hypotension) AND (Ischemic heart disease) AND (Life limiting disease) AND (Pregnancy) AND (Systolic blood pressure <100 mmHg class I class III) AND (Thyrotoxicosis) AND (antiarrhythmic drugs) AND (contradictions) AND (hepatic failure) AND (lactation) AND (renal failure) AND (study drugs) AND (substance abuse))"}
{"candidate_id": "LLM05088", "doc_id": "NCT02426944_inc", "case_bucket": "or", "source_criterion": "history of significant bleeding (i.e. bleeding which required intervention or hospitalization), even in the absence of anticoagulation treatment at the time of the bleeding event, or a cardioembolic event, which occurred on anticoagulation, or a high risk profile of the patient, defined as a CHA2DS2-VASc score = 3 and a HAS-BLED score = 2", "candidate_expression": "((CHA2DS2-VASc score = 3) AND (HAS-BLED score = 2) AND (anticoagulation) AND (bleeding) AND (bleeding significant) AND (cardioembolic event occurred on anticoagulation) AND (high risk profile) AND (hospitalization) AND (intervention))"}
{"candidate_id": "LLM05089", "doc_id": "NCT03168555_exc", "case_bucket": "or", "source_criterion": "small bowel resection right sided hemicolectomy known chronic diarrheal disease (celiac disease, lactose malabsorption, Inflammatory bowel diseases, incl microscopic colitis) pregnancy wish for pregnancy within next three months allergy to eggs allergy to constituents in Xenbilox (capsules with chenodeoxycholic acid) acute cholecystitis within two months chronic cholecystitis cirrhosis of the liver suspected obstructive choledocholithiasis icterus", "candidate_expression": "((acute cholecystitis within two months) AND (allergy) AND (chenodeoxycholic acid) AND (chronic cholecystitis) AND (chronic diarrheal disease) AND (cirrhosis of the liver) AND (constituents in Xenbilox) AND (eggs) AND (icterus) AND (obstructive choledocholithiasis suspected) AND (pregnancy) AND (pregnancy wish for within next three months) AND (right sided hemicolectomy) AND (small bowel resection) AND ((Inflammatory bowel diseases) OR (celiac disease) OR (lactose malabsorption) OR (microscopic colitis)))"}
{"candidate_id": "LLM05090", "doc_id": "NCT02618057_exc", "case_bucket": "or", "source_criterion": "Immunosuppresant host Chronic cardiovascular/pulmonary disease Hospital acquired infection", "candidate_expression": "((Chronic) AND (Hospital acquired infection) AND (Immunosuppresant host) AND ((cardiovascular disease) OR (pulmonary disease)))"}
{"candidate_id": "LLM05091", "doc_id": "NCT03099863_inc", "case_bucket": "or", "source_criterion": "Adult women at least 18 years of age Elective Female Pelvic Medicine and Reconstructive Surgery or Gynecologic Minimally Invasive surgeries including hysterectomy, suburethral sling, and pelvic organ prolapse repair that require cystoscopy.", "candidate_expression": "((Adult) AND (Elective) AND (Female Pelvic) AND (Gynecologic) AND (Minimally Invasive) AND (age) AND (at least 18 years) AND (cystoscopy) AND (require) AND (surgeries) AND (women) AND ((hysterectomy) OR (pelvic organ prolapse repair) OR (suburethral sling)) AND ((Medicine) OR (Reconstructive Surgery)))"}
{"candidate_id": "LLM05092", "doc_id": "NCT02912182_exc", "case_bucket": "or", "source_criterion": "tinnitus or hearing loss with same debut as vertigo history of bleeding peptic ulcer glaucoma pregnancy or non-acceptance to use anticonception measures during 13 days after debut high blood pressure >180 systolic, 105, diastolic ketoacidosis with a Base Excess >=2 psychic disorder (not including mild depression) serious infection (neutropenia, tuberculosis) chronic otitis history of vertiginous disease; Ménière, Vertiginous migraine, atypical BPPV", "candidate_expression": "((Base Excess >=2) AND (Ménière) AND (Vertiginous migraine) AND (atypical BPPV) AND (bleeding) AND (blood pressure diastolic 105) AND (blood pressure systolic >180) AND (chronic otitis) AND (glaucoma) AND (hearing loss) AND (infection serious) AND (ketoacidosis) AND (neutropenia) AND (peptic ulcer) AND (pregnancy or non-acceptance to use anticonception measures during 13 days after debut) AND (psychic disorder) AND (tinnitus) AND (tuberculosis) AND (vertiginous disease) AND (vertigo) AND NOT (mild depression))"}
{"candidate_id": "LLM05093", "doc_id": "NCT02894645_inc", "case_bucket": "other", "source_criterion": "Confirmed diagnosis of non-Burkitt B-lineage ALL 1 to 17 years of age (before 18th birthday) Renal function within normal range for age Liver function within normal range for age Able to participate in the full 2 years of treatment", "candidate_expression": "((Able to participate) AND (Liver function within normal range for age) AND (Renal function within normal range for age) AND (age 1 to 17 years) AND (non-Burkitt B-lineage ALL Confirmed) AND (treatment full 2 years))"}
{"candidate_id": "LLM05094", "doc_id": "NCT02858180_inc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection of Genotype 1, 4, 5, or 6 HCV RNA > 103 IU/mL at screening 18 years of age or older Diagnosis of chronic HCV infection, defined as positive HCV antibody or HCV RNA more than 6 months prior to screening OR an assessment of fibrosis F2 or greater prior to screening. NYHA Class III: Subjects with cardiac disease resulting in marked limitation of physical activity. They are comfortable at rest. Less than ordinary physical activity causes fatigue, palpitation, dyspnea, or anginal pain. NYHA Class IV: Patient with cardiac disease resulting in inability to carry on any physical activity without discomfort. Symptoms of cardiac insufficiency or of the anginal syndrome may be present even at rest. If any physical activity is undertaken, discomfort is increased. ejection fraction = 30% hospitalized for heart failure in last 12 months ILD criteria: diagnosis of interstitial lung disease with chronic supplemental oxygen requirement at rest and/or with exertion. Forced expiratory volume (FEV1)< 30% predicted OR any FEV1 with chronic supplemental oxygen requirement at rest and/or with exertion OR any FEV1 with chronic hypercapnia (baseline partial pressure of arterial carbon dioxide [PaCO2] > 45)", "candidate_expression": "((< 30% predicted) AND (= 30%) AND (> 103 IU/mL) AND (> 45) AND (Chronic HCV Infection) AND (Class III) AND (Class IV) AND (F2 or greater) AND (FEV1) AND (Forced expiratory volume) AND (HCV RNA) AND (ILD criteria) AND (NYHA) AND (PaCO2) AND (age) AND (assessment of fibrosis) AND (at screening) AND (chronic HCV infection) AND (chronic hypercapnia) AND (chronic supplemental oxygen requirement) AND (ejection fraction) AND (heart failure) AND (hospitalized) AND (in last 12 months) AND (interstitial lung disease) AND (more than 6 months prior to screening) AND (older 18 years) AND (partial pressure of arterial carbon dioxide) AND (positive) AND (prior to screening) AND (screening) AND ((HCV RNA) OR (HCV antibody)) AND ((Genotype 1) OR (Genotype 4) OR (Genotype 5) OR (Genotype 6)) AND ((at rest) OR (with exertion)))"}
{"candidate_id": "LLM05095", "doc_id": "NCT03228238_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05096", "doc_id": "NCT03589105_inc", "case_bucket": "or", "source_criterion": "Age >/=18 years at screening Patients with relapsing forms of multiple sclerosis (RMS) with active disease defined by clinical or imaging features: (i) at least one clinical relapse over a 6-month period prior to screening; (ii) AND/OR at least one T1 gadolinium-enhancing lesion or new and/or enlarging T2 lesion as detected by brain Magnetic Resonance Imaging (MRI) performed over a 3 months period prior to screening with no change of Disease-Modifying Treatment(s) (DMT) compared to a previous MRI performed within 24 months before screening For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab Participants should be beneficiary of healthcare coverage under the social security system", "candidate_expression": "((>/=18 years) AND (Age) AND (Disease-Modifying Treatment(s) (DMT)) AND (For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab) AND (active disease) AND (at least one over a 3 months period) AND (at least one over a 6-month period) AND (at screening) AND (beneficiary of healthcare coverage) AND (brain Magnetic Resonance Imaging (MRI)) AND (change of) AND (clinical relapse) AND (multiple sclerosis (RMS)) AND (no) AND (prior to screening) AND (relapsing forms) AND ((T1 gadolinium-enhancing lesion) OR (T2 lesion)) AND ((enlarging) OR (new)) AND ((clinical features) OR (imaging features)))"}
{"candidate_id": "LLM05097", "doc_id": "NCT02916342_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-III; 18-85 years of age, inclusive; surgery less than 3 hours.", "candidate_expression": "((ASA physical status I-III) AND (age 18-85 years , inclusive) AND (surgery less than 3 hours))"}
{"candidate_id": "LLM05098", "doc_id": "NCT02760251_exc", "case_bucket": "or", "source_criterion": "Adults older than 45 and children younger than 18 years Platelet count higher than 30x109/l at time of screening Suspicion of secondary ITP Positive family history for ITP Presence or history of autoimmune disease as judged by the investigator Hepatosplenomegaly Presence or history of relevant hepatic disease as judged by the investigator Presence or history of thromboembolic disease as judged by the investigator Patients with splenectomy Women who are pregnant or breast feeding Intention to become pregnant during the course of the study Lack of safe double contraception (see 7.1) Any vaccination 2 weeks prior start of the study Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center Known or suspected non-compliance, drug or alcohol abuse Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject Participation in another study with investigational drug within the 30 days preceding and during the present study Previous enrolment into the current study Previous treatment with romiplostim or eltrombopag Hypersensitivity to the active substance or to any of the excipients or to E. coli derived proteins Enrolment of the investigator, his/her family members, employees and other dependent persons", "candidate_expression": "((2 weeks prior start of the study) AND (Adults) AND (Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center) AND (Hepatosplenomegaly) AND (Hypersensitivity) AND (Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject) AND (Intention to become pregnant during the course of the study) AND (Lack of safe double contraception (see 7.1)) AND (Platelet count) AND (Women who are pregnant or breast feeding) AND (alcohol abuse) AND (as judged by the investigator) AND (at time of screening) AND (autoimmune disease) AND (children) AND (drug abuse) AND (eltrombopag) AND (family history for ITP) AND (hepatic disease) AND (higher than 30x109/l) AND (non-compliance) AND (older than 45) AND (relevant) AND (romiplostim) AND (screening) AND (secondary ITP) AND (splenectomy) AND (start of the study) AND (thromboembolic disease) AND (vaccination) AND (younger than 18 years))"}
{"candidate_id": "LLM05099", "doc_id": "NCT01846507_exc", "case_bucket": "or", "source_criterion": "1. Active thromboembolic disease, history of thromboembolic disease (including retinal vein or artery occlusion), known inherited thrombophilia, or family history of thrombosis in a first degree relative 2. Subject has a severe medical or psychiatric illness that, in the opinion of the Investigator, would affect subject safety or compliance 3. Clinical evidence of severe bleeding disorder. Patients with mild bleeding disorders such as type 1 von Willebrand disease, mild platelet function defects such as platelet storage pool or release defects, and patients with bleeding due to Ehlers Danlos syndrome WILL be eligible to participate in the study. 4. Pregnancy within the past 6 months and/or breast-feeding 5. Use of hormonal contraception (estrogen and progestin) within 3 months of study entry, or anticipated need to initiate estrogen-containing hormonal contraception during the study period 6. Use of systemic steroids within 1 month of study entry 7. History of subarachnoid hemorrhage 8. History of Hepatitis B, C, or HIV 9. Baseline creatinine >20% above the upper limit of normal for age 10. Severe anemia (hemoglobin <8 g/dL) 11. Systolic blood pressure <85 or diastolic blood pressure <55 12. Heart rate <50 at time of screening 13. Use of intranasal DDAVP during menses will be permitted, but only if the patient has a history of using DDAVP consistently for ≥3 menstrual cycles prior to study enrollment, so that change in menstrual blood loss due to addition of Lysteda can be assessed. Use of one-time DDAVP during a DDAVP/Stimate challenge is also permitted during the study period, as is use of DDAVP in the event of severe epistaxis, trauma, or surgical procedures during the study period.", "candidate_expression": "((<50) AND (<55) AND (<8 g/dL) AND (<85) AND (>20% above the upper limit of normal for age) AND (Active) AND (Baseline) AND (Ehlers Danlos syndrome) AND (HIV) AND (Heart rate) AND (Hepatitis B) AND (Hepatitis C) AND (History) AND (Pregnancy) AND (Severe) AND (Systolic blood pressure) AND (age) AND (anemia) AND (anticipated need) AND (artery occlusion) AND (at time of screening) AND (bleeding) AND (bleeding disorder) AND (bleeding disorders) AND (breast-feeding) AND (creatinine) AND (diastolic blood pressure) AND (during menses) AND (during the study period) AND (estrogen) AND (estrogen-containing) AND (estrogen-containing hormonal contraception) AND (family history) AND (hemoglobin) AND (history) AND (hormonal contraception) AND (in a first degree relative) AND (in the opinion of the Investigator, would affect subject safety or compliance) AND (inherited thrombophilia) AND (intranasal DDAVP) AND (medical illness) AND (menses) AND (mild) AND (mild platelet function defects) AND (platelet release defects) AND (platelet storage pool defects) AND (progestin) AND (psychiatric illness) AND (retinal vein) AND (severe) AND (study entry) AND (subarachnoid hemorrhage) AND (systemic steroids) AND (the study period) AND (thromboembolic disease) AND (thrombosis) AND (time of screening) AND (type 1 von Willebrand disease) AND (within 1 month of study entry) AND (within 3 months of study entry) AND (within the past 6 months))"}
{"candidate_id": "LLM05100", "doc_id": "NCT03013790_inc", "case_bucket": "other", "source_criterion": "Non-ventilated Patients over the age of 65", "candidate_expression": "((Non) AND (age) AND (over 65) AND (ventilated))"}
```
