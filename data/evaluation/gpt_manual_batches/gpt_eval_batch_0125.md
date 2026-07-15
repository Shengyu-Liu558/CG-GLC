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
{"candidate_id": "LLM03101", "doc_id": "NCT03354572_inc", "case_bucket": "other", "source_criterion": "Subjects scheduled for laparoscopic unilateral inguinal hernia repair ASA 1 or2. Age >18 years.", "candidate_expression": "((ASA 1 or2) AND (Age >18 years) AND (inguinal hernia repair scheduled laparoscopic unilateral))"}
{"candidate_id": "LLM03102", "doc_id": "NCT01850147_inc", "case_bucket": "or", "source_criterion": "Histologic or cytologic diagnosis of stage IIIB/IV NSCLC ECOG PS: 0,1 Unidimensional or bi-dimensional measurable disease Receive prior treatment including first-line platinum-based chemotherapy, standard second-line chemotherapy and 1 EGF/EGFR inhibitor Evidence of disease progression Life expectancy >12 weeks Neutrophils > 1.5 109/l, Platelets > 100 109/l, Hemoglobin > 9g/dl, Total bilirubin < 1.5 UNL, AST (SGOT) and ALT (SGPT) < 2.5 UNL, Alkaline phosphatases < 5 UNL, Creatinine < 1 UNL", "candidate_expression": "((1 EGF/EGFR inhibitor) AND (ALT (SGPT) < 2.5 UNL) AND (AST (SGOT) < 2.5 UNL) AND (Alkaline phosphatases < 5 UNL) AND (Creatinine < 1 UNL) AND (ECOG PS 0,1 measurable) AND (Evidence) AND (Evidence of disease progression) AND (Hemoglobin > 9g/dl) AND (Histologic) AND (Life expectancy >12 weeks) AND (NSCLC stage IIIB/IV) AND (Neutrophils > 1.5 109/l) AND (Platelets > 100 109/l) AND (Total bilirubin < 1.5 UNL) AND (cytologic) AND (disease progression) AND (measurable) AND (platinum-based chemotherapy) AND (second-line chemotherapy standard) AND (treatment))"}
{"candidate_id": "LLM03103", "doc_id": "NCT02858180_exc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection with Genotype 2 or 3 Amiodarone. Subjects previously treated with amiodarone must have stopped the amiodarone at least 60 days prior to day 1 of SOF/LDV FDC Carbamazepine, phenytoin, phenobarbital, oxcarbazepine Rifabutin, rifampin or rifapentine HIV regimens containing tenofovir or tipranavir/ritonavir St. John's wort Rosuvastatin Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance History of hepatic encephalopathy or variceal hemorrhage Hepatitis B surface antigen positive Hemoglobin (Hb) < 8 g/dL Platelets = 50,000/mm3 alanine aminotransferase (ALT), aspartase aminotransferase (AST), or alkaline phosphatase = 10 times upper limit of normal(ULN) Total bilirubin > 3 mg/dl Severe renal impairment creatinine clearance (CrCl), i.e. < 30 mL/min. History of major organ transplantation with an existing functional graft. History of clinically-significant drug allergy to nucleoside/nucleotide analogs. Pregnant women or women planning to become pregnant Women who are breastfeeding Active or recent history (= 1 year) of drug or alcohol abuse", "candidate_expression": "((ALT) AND (AST) AND (Amiodarone at least 60 days prior to day 1 of SOF/LDV FDC) AND (Carbamazepine) AND (Chronic HCV Infection Genotype 2 Genotype 3) AND (CrCl) AND (Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance) AND (Hb) AND (Hemoglobin < 8 g/dL) AND (Hepatitis B surface antigen positive) AND (Platelets = 50,000/mm3) AND (Pregnant women or women planning to become pregnant) AND (Rifabutin) AND (Rosuvastatin) AND (St. John's wort) AND (Total bilirubin > 3 mg/dl) AND (Women who are breastfeeding) AND (alanine aminotransferase) AND (alcohol abuse) AND (alkaline phosphatase) AND (aspartase aminotransferase) AND (creatinine clearance < 30 mL/min) AND (drug abuse) AND (drug allergy clinically-significant) AND (hepatic encephalopathy) AND (major organ transplantation existing functional graft) AND (nucleoside) AND (nucleotide analogs) AND (oxcarbazepine) AND (phenobarbital) AND (phenytoin) AND (renal impairment Severe) AND (rifampin) AND (rifapentine) AND (tenofovir) AND (tipranavir/ritonavir) AND (variceal hemorrhage))"}
{"candidate_id": "LLM03104", "doc_id": "NCT02695992_inc", "case_bucket": "scope", "source_criterion": "Above 18 years of age Symptomatic, permanent AF of at least three months duration Resting heart rate =80 bpm Signed informed consent", "candidate_expression": "((AF at least three months duration permanent) AND (Resting heart rate =80 bpm) AND (Signed informed consent) AND (age Above 18 years Symptomatic))"}
{"candidate_id": "LLM03105", "doc_id": "NCT02390973_inc", "case_bucket": "or", "source_criterion": "BMI = 35 type 2 diabetes HbA1c = 6,5 % or fasting glycemia =7mmol/l or non-fasting glycemia =11mmol/l able to consent", "candidate_expression": "((BMI = 35) AND (able to consent) AND (type 2 diabetes) AND ((HbA1c = 6,5 %) OR (fasting glycemia =7mmol/l) OR (non-fasting glycemia =11mmol/l)))"}
{"candidate_id": "LLM03106", "doc_id": "NCT03373318_exc", "case_bucket": "other", "source_criterion": "Patients who do not meet the inclusion criteria and those who have a history of allergic reactions to human albumin, as well as those who have received iodinated contrast during the 7 days prior to surgery and pregnant women, will be excluded from the study.", "candidate_expression": "((allergic history) AND (human albumin) AND (iodinated contrast during the 7 days prior to surgery) AND (pregnant) AND (surgery) AND (women) AND NOT (meet the inclusion criteria))"}
{"candidate_id": "LLM03107", "doc_id": "NCT02385045_inc", "case_bucket": "or", "source_criterion": "• All patients attending for a routine diagnostic endoscopic procedure at St Mary's Hospital NHS Trust for dyspepsia and abdominal pain", "candidate_expression": "((St Mary's Hospital NHS Trust) AND (abdominal pain) AND (diagnostic endoscopic procedure) AND (dyspepsia))"}
{"candidate_id": "LLM03108", "doc_id": "NCT03168555_inc", "case_bucket": "other", "source_criterion": "planned elective cholecystectomy", "candidate_expression": "((cholecystectomy) AND (elective) AND (planned))"}
{"candidate_id": "LLM03109", "doc_id": "NCT02384850_inc", "case_bucket": "or", "source_criterion": "1. Patients with histologically confirmed diagnosis of colorectal cancer presenting with unresectable stage IV (UICC) disease (primary tumor may be present) 2. Patients who are feasible for treatment with FOLFOX (prior adjuvant or palliative treatment is allowed) 3. ECOG Performance status ≤ 1 4. Life expectancy > 3 months 5. Age ≥18 years 6. Haematologic function as follows (5% deviation allowed): ANC ≥ 1.5 x 109/L platelets ≥ 100 x109/L hemoglobin ≥ 9 g/dl or 5.59 mmol/l 7. Adequate liver function as follows (10% deviation allowed) serum alanine transaminase (ALT) ≤ 2.5 x ULN (in case of liver metastases < 5 x ULN) total bilirubin ≤ 1.5 x ULN (patients with Gilbert's syndrome total bilirubin ≤2.5 x ULN) 8. Adequate renal function as follows (10% deviation allowed) · creatinine ≤ 1.5 x ULN 9. Signed written informed consent 10. Women of child-bearing potential must have a negative pregnancy test", "candidate_expression": "((ANC ≥ 1.5 x 109/L) AND (Age ≥18 years) AND (ECOG Performance status ≤ 1) AND (FOLFOX) AND (Gilbert's syndrome) AND (Life expectancy > 3 months) AND (Signed written informed consent) AND (Women) AND (adjuvant treatment) AND (child-bearing potential) AND (colorectal cancer) AND (creatinine ≤ 1.5 x ULN) AND (disease unresectable stage IV (UICC) IV) AND (hemoglobin ≥ 9 g/dl ≥ 5.59 mmol/l) AND (histologically confirmed) AND (liver function Adequate) AND (liver metastases < 5 x ULN) AND (palliative treatment) AND (platelets ≥ 100 x109/L) AND (pregnancy test negative) AND (renal function Adequate) AND (serum alanine transaminase (ALT) ≤ 2.5 x ULN) AND (total bilirubin ≤ 1.5 x ULN) AND (total bilirubin ≤2.5 x ULN))"}
{"candidate_id": "LLM03110", "doc_id": "NCT00679341_inc", "case_bucket": "or", "source_criterion": "Histologically or cytologically confirmed adenocarcinoma of the breast with locally advanced or metastatic disease, and a candidate for chemotherapy. Human epidermal growth factor receptor 2 (HER2)-positive. No prior chemotherapy for their metastatic breast cancer (MBC). Measurable disease. Age ≥ 18 years. For women of childbearing potential and men with partners of childbearing potential, agreement to use a highly effective, non-hormonal form of contraception or 2 effective forms of non-hormonal contraception by the patient and/or partner. Contraception use must continue for the duration of study treatment and for at least 6 months after the last dose of study treatment. Male patients whose partners are pregnant should use condoms for the duration of the study.", "candidate_expression": "((Age ≥ 18 years) AND (Contraception continue for the duration of study treatment for at least 6 months after the last dose of study treatment) AND (Human epidermal growth factor receptor 2 (HER2) positive) AND (Male) AND (Measurable disease) AND (adenocarcinoma of the breast Histologically confirmed cytologically confirmed) AND (candidate for chemotherapy) AND (chemotherapy) AND (childbearing potential) AND (condoms for the duration of the study) AND (contraception highly effective non-hormonal) AND (disease locally advanced) AND (men) AND (metastatic breast cancer (MBC)) AND (metastatic disease) AND (non-hormonal contraception 2) AND (partners are pregnant) AND (with partners of childbearing potential) AND (women) AND NOT (chemotherapy prior))"}
{"candidate_id": "LLM03111", "doc_id": "NCT02982577_exc", "case_bucket": "other", "source_criterion": "Sensitivity to pilocarpine Secondary Sjögren's syndrome; Type II diabetes mellitus; AIDS; pregnant or lactating women; Glaucoma; Uncontrolled asthma; Chronic obstructive pulmonary disease; Renal diseases; Severe cardiovascular diseases; Gastrointestinal disorders; Hepatic insufficiency.", "candidate_expression": "((AIDS) AND (Chronic obstructive pulmonary disease) AND (Gastrointestinal disorders) AND (Glaucoma) AND (Hepatic insufficiency) AND (Renal diseases) AND (Secondary) AND (Sensitivity) AND (Severe) AND (Sjögren's syndrome) AND (Type II diabetes mellitus) AND (Uncontrolled) AND (asthma) AND (cardiovascular diseases) AND (pilocarpine) AND (pregnant or lactating women))"}
{"candidate_id": "LLM03112", "doc_id": "NCT02426944_exc", "case_bucket": "or", "source_criterion": "thrombus in the LA or LAA; mechanical valve prosthesis; mitral stenosis; previous LAA ligation during cardiac surgery; life expectancy less than 2 years; comorbidities other than AF, which present an indication for anticoagulation; patent foramen ovale with atrial septal aneurysm mobile plaque in the aorta; symptomatic atherosclerosis of the carotid artery; pericardial effusion greater than 10 mm; clinically significant bleeding within the 30 days prior to the scheduled procedure; stroke or other cardioembolic event within the 30 days prior to the scheduled procedure; acute coronary syndrome within the 90 days prior to the scheduled procedure, gravidity, significant valvular disease, creatinine clearance less than 30 ml/min", "candidate_expression": "((LAA ligation) AND (acute coronary syndrome within the 90 days prior to the scheduled procedure) AND (anticoagulation) AND (atherosclerosis symptomatic of the carotid artery) AND (atrial septal aneurysm) AND (bleeding clinically significant within the 30 days prior to the scheduled procedure) AND (cardiac surgery) AND (cardioembolic event other) AND (comorbidities) AND (creatinine clearance less than 30 ml/min) AND (gravidity) AND (indication) AND (life expectancy less than 2 years) AND (mechanical valve prosthesis) AND (mitral stenosis) AND (mobile plaque in the aorta) AND (patent foramen ovale) AND (pericardial effusion greater than 10 mm) AND (stroke) AND (thrombus LA LAA) AND (valvular disease significant) AND NOT (AF))"}
{"candidate_id": "LLM03113", "doc_id": "NCT03532620_inc", "case_bucket": "or", "source_criterion": "Age 18-80 years old; IFG: 5.6mmol/L (100mg/dl)=FPG<7.0mmol/L (126mg/dl), or IGT: 7.8mmol/L (140mg/dl)=OGTT 2-h PG<11.1mmol/L (200mg/dl), or HbA1C 5.7-6.4% (39-47mmol/mol); 2.6mmol/L (100mg/dl)=LDL-C=5.2mmol/L (200mg/dl), and TG<5.7mmol/L (500mg/dl); 130mmHg=SBP<180mmHg, or 80mmHg=DBP<110mmHg or ongoing anti-hypertensive therapy; Patients volunteered for the study and signed informed consent.", "candidate_expression": "((100mg/dl) AND (126mg/dl) AND (130mmHg) AND (140mg/dl) AND (18-80 years old) AND (2.6mmol/L) AND (200mg/dl) AND (39-47mmol/mol) AND (5.2mmol/L) AND (5.6mmol/L) AND (5.7-6.4%) AND (500mg/dl) AND (7.8mmol/L) AND (80mmHg=) AND (<11.1mmol/L) AND (<110mmHg) AND (<180mmHg) AND (<5.7mmol/L) AND (<7.0mmol/L) AND (Age) AND (DBP) AND (FPG) AND (HbA1C) AND (IFG) AND (IGT) AND (LDL-C) AND (OGTT 2-h PG) AND (Patients volunteered for the study and signed informed consent.) AND (SBP) AND (TG) AND (anti-hypertensive therapy) AND (ongoing))"}
{"candidate_id": "LLM03114", "doc_id": "NCT02905734_exc", "case_bucket": "other", "source_criterion": "Lack of understanding of the study contra-indication to nicotine replacement therapy health status incompatible with detention in police cells serious mental disorder usual place of residence outside Seine-Saint-Denis", "candidate_expression": "((Lack of understanding of the study) AND (contra-indication) AND (incompatible with detention in police cells) AND (nicotine replacement therapy) AND (outside Seine-Saint-Denis) AND (place of residence) AND (serious mental disorder))"}
{"candidate_id": "LLM03115", "doc_id": "NCT03056391_exc", "case_bucket": "or", "source_criterion": "1. Patient or relatives unable or unwilling to give informed consent 2. Contraindication or allergy to paracetamol or artesunate therapy 3. Known cirrhosis, or >6 standard alcoholic drinks/day 4. Pregnancy", "candidate_expression": "((Patient or relatives unable or unwilling to give informed consent) AND (Pregnancy) AND ((artesunate) OR (paracetamol)) AND ((>6 standard alcoholic drinks/day) OR (cirrhosis)) AND ((Contraindication) OR (allergy)))"}
{"candidate_id": "LLM03116", "doc_id": "NCT02790593_inc", "case_bucket": "or", "source_criterion": "Age >18 years old 1cm squared surface area Venous incompetence confirmed by clinical assessment and duplex ultrasound scan No evidence of arterial disease (Arterial Duplex or Ankle Brachial Pressure Index >0.9) Patients able to complete trial procedures Patients with a life expectancy of greater than 1 year", "candidate_expression": "((1cm squared) AND (>0.9) AND (>18 years old) AND (Age) AND (No) AND (Patients able to complete trial procedures) AND (Venous incompetence) AND (arterial disease) AND (clinical assessment) AND (duplex ultrasound scan) AND (greater than 1 year) AND (life expectancy) AND (surface area) AND ((Ankle Brachial Pressure Index) OR (Arterial Duplex)))"}
{"candidate_id": "LLM03117", "doc_id": "NCT02862314_exc", "case_bucket": "or", "source_criterion": "pregnancy, patients under legal custody, patients without health insurance, patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter, moribund patients, situation in which the procalcitonin concentration could be increased without correlation to an infectious process (poly-traumatised patients, surgical interventions within the last 4 days, cardiorespiratory arrest, administration of anti-thymocyte globulin, immunodepressed patients (bone marrow transplant patients, patients with severe neutropenia), patients with an absolute indication for administration of antibiotics at the moment of ICU admission (meningitis, pneumonia) or a chronic infection for which long-term antibiotic treatment is necessary (endocarditis, osteo-articular infections, mediastinitis, deep abscesses, pneumocystis infection, toxoplasmosis, tuberculosis) patients with haemodynamic instability of septic origin or a respiratory insufficiency (defined by a ratio Pa02/Fi02 = 200 mmHg and PEP = 5 cmH2O)", "candidate_expression": "((ICU) AND (PEP = 5 cmH2O) AND (Pa02/Fi02 = 200 mmHg) AND (anti-thymocyte globulin) AND (antibiotic treatment long-term) AND (antibiotics) AND (bone marrow transplant) AND (cardiorespiratory arrest) AND (chronic infection) AND (deep abscesses) AND (endocarditis) AND (espiratory insufficiency) AND (haemodynamic instability) AND (immunodepressed) AND (indication) AND (legal custody) AND (mediastinitis) AND (meningitis) AND (moribund) AND (osteo-articular infections) AND (patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter) AND (pneumocystis infection) AND (pneumonia) AND (poly-traumatised) AND (pregnancy) AND (procalcitonin concentration increased) AND (septic) AND (severe neutropenia) AND (surgical interventions last 4 days) AND (toxoplasmosis) AND (tuberculosis) AND NOT (health insurance))"}
{"candidate_id": "LLM03118", "doc_id": "NCT00343668_exc", "case_bucket": "or", "source_criterion": "Other tumor type than adenocarcinoma Central nervous system (CNS) metastases or prior radiation for CNS metastases Gastric outlet obstruction or intestinal obstruction Evidence of gastrointestinal bleeding The patient has bony lesions as the sole evaluable disease. Past or concurrent history of neoplasm other than stomach cancer, except for curatively treated non-melanoma skin cancer or in situ carcinoma of the cervix uteri Pregnant or lactating women, women of childbearing potential not employing adequate contraception Other serious illness or medical conditions Unstable cardiac disease despite treatment, myocardial infarction within 6 months prior to study entry History of significant neurologic or psychiatric disorders including dementia or seizures Active uncontrolled infection Other serious underlying medical conditions which could impair the ability of the patient to participate in the study Concomitant administration of any other experimental drug under investigation, or concomitant chemotherapy, hormonal therapy, or immunotherapy concomitant drug medication; The following drugs cause drug interaction with S-1. i. Warfarin, phenprocoumon: increase bleeding tendency ii. Increase blood concentration of phenytoin iii. sorivudine: inhibit DPD -> increase toxicity according to fluoropyrimidine iv. allopurinol : decrease activity of S-1", "candidate_expression": "((Active) AND (CNS metastases) AND (Concomitant) AND (Evidence of) AND (History) AND (Increase) AND (Other) AND (ability of the patient to participate) AND (adenocarcinoma) AND (bleeding tendency) AND (blood concentration of phenytoin) AND (bony lesions) AND (childbearing potential) AND (concomitant) AND (contraception) AND (curatively) AND (evaluable disease) AND (except for) AND (experimental drug) AND (gastrointestinal bleeding) AND (history of) AND (increase) AND (infection) AND (neoplasm) AND (not employing) AND (other than) AND (serious medical conditions) AND (stomach cancer) AND (the sole) AND (treated) AND (treatment) AND (tumor) AND (uncontrolled) AND (within 6 months prior to study entry) AND (women) AND ((in situ carcinoma of the cervix uteri) OR (non-melanoma skin cancer)) AND ((Pregnant) OR (lactating)) AND ((medical conditions) OR (serious illness)) AND ((Central nervous system (CNS) metastases) OR (radiation)) AND ((Unstable cardiac disease) OR (myocardial infarction)) AND ((neurologic disorders) OR (psychiatric disorders)) AND ((dementia) OR (seizures)) AND ((chemotherapy) OR (hormonal therapy) OR (immunotherapy)) AND ((drug) OR (medication)) AND ((Warfarin) OR (phenprocoumon)) AND ((Gastric outlet obstruction) OR (intestinal obstruction)) AND ((allopurinol) OR (fluoropyrimidine) OR (sorivudine)))"}
{"candidate_id": "LLM03119", "doc_id": "NCT01032109_exc", "case_bucket": "or", "source_criterion": "choroidal neovascularization caused by other eye diseases ocular surgery within the past 3 mouths history of uveitis intraocular pressure higher than 25 mmHg, or glaucoma history of systemic or ocular thromboembolic events.", "candidate_expression": "((choroidal neovascularization) AND (higher than 25 mmHg) AND (history) AND (ocular surgery) AND (other) AND (other eye diseases) AND (thromboembolic events) AND (uveitis) AND (within the past 3 mouths) AND ((glaucoma) OR (intraocular pressure)) AND ((ocular) OR (systemic)))"}
{"candidate_id": "LLM03120", "doc_id": "NCT03177837_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((750 m) AND (<0.7) AND (<40% predicted) AND (<92%) AND (>20) AND (COPD) AND (COPD exacerbation) AND (Comorbidities) AND (FEV1) AND (FEV1/FVC) AND (Internal) AND (OSA) AND (acetazolamide) AND (allergy) AND (cardiovascular disease) AND (cigarettes per day) AND (coronary artery disease) AND (current) AND (disease) AND (heavy) AND (hypoxemia) AND (in the last 2 months) AND (low altitude) AND (neurologic) AND (other) AND (oxygen saturation) AND (pneumothorax) AND (previous) AND (psychiatric) AND (renal failure) AND (rheumatologic) AND (room air) AND (smoking) AND (stroke) AND (sulfonamides) AND (systemic arterial hypertension) AND (uncontrolled) AND (unstable) AND (very severe))"}
{"candidate_id": "LLM03121", "doc_id": "NCT02953873_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03122", "doc_id": "NCT01967420_inc", "case_bucket": "or", "source_criterion": "Non-affective psychosis Premorbid IQ of over 70 A service user of the early intervention service Aged 18 or over (up to the age of 35 which is the limit for the early intervention service) Psychiatrically stable enough to attend to completion (no hospitalisations or medication changes in last 4 weeks)", "candidate_expression": "((18 or over) AND (Aged) AND (Non-affective psychosis) AND (Premorbid IQ) AND (Psychiatrically stable) AND (in last 4 weeks) AND (no) AND (over 70) AND (up to the age of 35) AND ((hospitalisations) OR (medication changes)))"}
{"candidate_id": "LLM03123", "doc_id": "NCT02845427_inc", "case_bucket": "other", "source_criterion": "Primary total hip arthroplasty (THA)", "candidate_expression": "((Primary) AND (THA) AND (total hip arthroplasty))"}
{"candidate_id": "LLM03124", "doc_id": "NCT02208739_exc", "case_bucket": "or", "source_criterion": "Patients who had history of systemic antibiotic usage over the previous 4 months Patients who were pregnant Patients who had received non-surgical periodontal treatment within the past 6 months Patients who had received surgical periodontal treatment within the past 12 months Patients who were smokers Patients with a history of stroke or an acute cardiovascular event over the previous 12 months.", "candidate_expression": "((acute cardiovascular event over the previous 12 months) AND (non-surgical periodontal treatment within the past 6 months) AND (pregnant) AND (smokers) AND (stroke) AND (surgical periodontal treatment within the past 12 months) AND (systemic antibiotic history over the previous 4 months))"}
{"candidate_id": "LLM03125", "doc_id": "NCT02604459_exc", "case_bucket": "or", "source_criterion": "Inability to follow directions or comprehend the English language Severe uncorrected visual or auditory handicaps Delirium at screening or baseline Emergency surgery", "candidate_expression": "((Delirium) AND (Emergency surgery) AND ((Inability to comprehend the English language) OR (Inability to follow directions)) AND ((auditory handicaps) OR (handicaps visual)) AND ((at baseline) OR (at screening)))"}
```
