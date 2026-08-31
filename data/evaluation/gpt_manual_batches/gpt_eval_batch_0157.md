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
{"candidate_id": "LLM03901", "doc_id": "NCT02905890_exc", "case_bucket": "or", "source_criterion": "Currently pregnant or using a reliable contraception (e.g. injectables, intrauterine devices, implant, oral contraceptive pills) Desiring pregnancy in the next year History of tubal ligation or hysterectomy Contraindication to progestin-only contraceptives Unable to comprehend consent material because of language barrier or psychological difficulty", "candidate_expression": "((Currently pregnant or using a reliable contraception (e.g. injectables, intrauterine devices, implant, oral contraceptive pills)) AND (Desiring pregnancy in the next year) AND (Unable to comprehend consent material because of language barrier or psychological difficulty) AND (contraceptives) AND (hysterectomy) AND (progestin only) AND (tubal ligation))"}
{"candidate_id": "LLM03902", "doc_id": "NCT01816997_inc", "case_bucket": "other", "source_criterion": "Age 35-70 years old Fasting blood glucose 100-125 mg/dL", "candidate_expression": "((100-125 mg/dL) AND (35-70 years old) AND (Age) AND (Fasting blood glucose))"}
{"candidate_id": "LLM03903", "doc_id": "NCT01236417_exc", "case_bucket": "or", "source_criterion": "Inability to comply with study requirements. Metastatic breast cancer. Patients with orthopedic or neuromuscular disorders that preclude participation in exercise. Rheumatoid arthritis. History of MI, angina or congestive heart failure. Pregnant or lactating females. Patients that are high risk for moderate exercise based on ACSM risk classification. Patients who exceed minimal physical activity recommendations from the US Surgeon General's Report: Accumulation of 30 minutes or more of moderate physical activity on most days of the week. Morbidly obese with BMI ≥ 40", "candidate_expression": "((ACSM risk classification) AND (BMI ≥ 40) AND (Inability to comply with study requirements.) AND (MI) AND (Morbidly obese) AND (Pregnant) AND (Pregnant or lactating females.) AND (Rheumatoid arthritis) AND (angina) AND (breast cancer Metastatic) AND (congestive heart failure) AND (disorders orthopedic) AND (exceed minimal physical activity recommendations) AND (females) AND (lactating) AND (neuromuscular disorders) AND (risk for moderate exercise high))"}
{"candidate_id": "LLM03904", "doc_id": "NCT02858180_exc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection with Genotype 2 or 3 Amiodarone. Subjects previously treated with amiodarone must have stopped the amiodarone at least 60 days prior to day 1 of SOF/LDV FDC Carbamazepine, phenytoin, phenobarbital, oxcarbazepine Rifabutin, rifampin or rifapentine HIV regimens containing tenofovir or tipranavir/ritonavir St. John's wort Rosuvastatin Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance History of hepatic encephalopathy or variceal hemorrhage Hepatitis B surface antigen positive Hemoglobin (Hb) < 8 g/dL Platelets = 50,000/mm3 alanine aminotransferase (ALT), aspartase aminotransferase (AST), or alkaline phosphatase = 10 times upper limit of normal(ULN) Total bilirubin > 3 mg/dl Severe renal impairment creatinine clearance (CrCl), i.e. < 30 mL/min. History of major organ transplantation with an existing functional graft. History of clinically-significant drug allergy to nucleoside/nucleotide analogs. Pregnant women or women planning to become pregnant Women who are breastfeeding Active or recent history (= 1 year) of drug or alcohol abuse", "candidate_expression": "((< 30 mL/min) AND (< 8 g/dL) AND (= 1 year) AND (= 10 times upper limit of normal) AND (= 50,000/mm3) AND (> 3 mg/dl) AND (ALT) AND (AST) AND (Amiodarone) AND (Chronic HCV Infection) AND (CrCl) AND (Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance) AND (Hb) AND (Hemoglobin) AND (Hepatitis B surface antigen) AND (Platelets) AND (Pregnant women or women planning to become pregnant) AND (Rosuvastatin) AND (Severe) AND (St. John's wort) AND (Total bilirubin) AND (Women who are breastfeeding) AND (at least 60 days prior to day 1 of SOF/LDV FDC) AND (clinically-significant) AND (creatinine clearance) AND (day 1 of SOF/LDV FDC) AND (drug allergy) AND (existing functional graft) AND (major organ transplantation) AND (positive) AND (renal impairment) AND ((Rifabutin) OR (rifampin) OR (rifapentine)) AND ((tenofovir) OR (tipranavir/ritonavir)) AND ((Genotype 2) OR (Genotype 3)) AND ((hepatic encephalopathy) OR (variceal hemorrhage)) AND ((alanine aminotransferase) OR (alkaline phosphatase) OR (aspartase aminotransferase)) AND ((nucleoside) OR (nucleotide analogs)) AND ((alcohol abuse) OR (drug abuse)) AND ((Carbamazepine) OR (oxcarbazepine) OR (phenobarbital) OR (phenytoin)))"}
{"candidate_id": "LLM03905", "doc_id": "NCT02983214_inc", "case_bucket": "other", "source_criterion": "Patients aged =50 years with DM2 and symptomatic PAD diagnosed clinically (according to Fontaine criteria, stage IIa or IIb and III) and by measuring the <U+0391><U+0392><U+0399>.", "candidate_expression": "((DM2) AND (Fontaine criteria stage IIa or IIb and III) AND (PAD symptomatic) AND (aged =50 years))"}
{"candidate_id": "LLM03906", "doc_id": "NCT01742117_inc", "case_bucket": "or", "source_criterion": "Patient >18 years of age Patient presents with acute coronary syndrome (ACS) or stable coronary artery disease (CAD) Patient is eligible for PCI Patient is willing and able to provide informed written consent Patient not able to receive 12 months of dual anti-platelet therapy Failure of index PCI Patient or physician refusal to enroll in the study Patient with known CYP2C19 genotype prior to randomization Planned revascularization of any vessel within 30 days post-index procedure and/or of the target vessel(s) within 12 months post-procedure Anticipated discontinuation of clopidogrel or ticagrelor within the 12 month follow up period, example for elective surgery Serum creatinine >2.5 mg/dL within 7 days of index procedure Platelet count <80,000 or >700,000 cells/mm3, or white blood cell count <3,000 cells/mm3 if persistent (at least 2 abnormal values) within 7 days prior to index procedure. History of intracranial hemorrhage Known hypersensitivity to clopidogrel or ticagrelor or any of its components Patient is participating in an investigational drug or device clinical trial that has not reached its primary endpoint Patient previously enrolled in this study Patient is pregnant, lactating, or planning to become pregnant within 12 months Patient has received an organ transplant or is on a waiting list for an organ transplant Patient is receiving or scheduled to receive chemotherapy within 30 days before or after the procedure Patient is receiving immunosuppressive therapy or has known immunosuppressive or autoimmune disease (e.g., human immunodeficiency virus, systemic lupus erythematous, etc.) Patient is receiving chronic oral anticoagulation therapy (i.e., vitamin K antagonist, direct thrombin inhibitor, Factor Xa inhibitor) Concomitant use of simvastatin/lovastatin > 40 mg qd Concomitant use of potent CYP3A4 inhibitors (atazanavir, clarithromycin, indinavir, itraconazole, ketoconazole, nefazodone, nelfinavir, ritonavir, saquinavir, telithromycin and voriconazole) or inducers (carbamazepine, dexamethasone, phenobarbital, phenytoin, rifampin, and rifapentine) Non-cardiac condition limiting life expectancy to less than one year, per physician judgment (e.g. cancer) Known history of severe hepatic impairment Patient has a history of bleeding diathesis or coagulopathy or will refuse blood transfusions Patient has an active pathological bleeding, such as active gastrointestinal (GI) bleeding Inability to take aspirin at a dosage of 100 mg or less Current substance abuse (e.g., alcohol, cocaine, heroin, etc.)", "candidate_expression": "((ACS) AND (CAD) AND (CYP2C19 genotype prior to randomization) AND (Inability to take) AND (Non-cardiac condition life expectancy) AND (PCI Failure index) AND (PCI eligible) AND (Patient is willing and able to provide informed written consent) AND (Patient or physician refusal to enroll in the study) AND (Serum creatinine >2.5 mg/dL within 7 days of index procedure) AND (able to receive) AND (age >18 years) AND (any of its components) AND (aspirin 100 mg or less) AND (chemotherapy) AND (dual anti-platelet therapy 12 months) AND (elective surgery example for) AND (gastrointestinal (GI) bleeding active) AND (hepatic impairment severe) AND (hypersensitivity) AND (intracranial hemorrhage) AND (oral anticoagulation therapy chronic) AND (pathological bleeding active) AND (potent CYP3A4 inducers Concomitant) AND (potent CYP3A4 inhibitors Concomitant) AND (revascularization Planned) AND (substance abuse) AND ((bleeding diathesis) OR (blood transfusions will refuse) OR (coagulopathy)) AND ((any vessel within 30 days post-index procedure) OR (of the target vessel(s) within 12 months post-procedure)) AND ((acute coronary syndrome) OR (coronary artery disease stable)) AND ((clopidogrel) OR (ticagrelor)) AND ((Platelet count <80,000 or >700,000 cells/mm3) OR (white blood cell count <3,000 cells/mm3)) AND ((lactating) OR (pregnant) OR (pregnant planning to become within 12 months)) AND ((organ transplant) OR (organ transplant is on a waiting list)) AND ((is receiving) OR (scheduled to receive)) AND ((autoimmune disease) OR (immunosuppressive disease) OR (immunosuppressive therapy)) AND ((human immunodeficiency virus) OR (systemic lupus erythematous)) AND ((Factor Xa inhibitor) OR (direct thrombin inhibitor) OR (vitamin K antagonist)) AND ((lovastatin Concomitant > 40 mg qd) OR (simvastatin Concomitant > 40 mg qd)) AND ((atazanavir) OR (clarithromycin) OR (indinavir) OR (itraconazole) OR (ketoconazole) OR (nefazodone) OR (nelfinavir) OR (ritonavir) OR (saquinavir) OR (telithromycin) OR (voriconazole)) AND ((carbamazepine) OR (dexamethasone) OR (phenobarbital) OR (phenytoin) OR (rifampin) OR (rifapentine)))"}
{"candidate_id": "LLM03907", "doc_id": "NCT02473809_inc", "case_bucket": "other", "source_criterion": "Informed consent Diagnosis of type 2 diabetes (HbA1c > 48 mmol/mol) Age older than 30 years", "candidate_expression": "((Age older than 30 years) AND (HbA1c > 48 mmol/mol) AND (Informed consent) AND (type 2 diabetes))"}
{"candidate_id": "LLM03908", "doc_id": "NCT02283905_exc", "case_bucket": "other", "source_criterion": "The patient's data will be excluded if they die within 3 days of hospital admission.", "candidate_expression": "(die within 3 days of hospital admission)"}
{"candidate_id": "LLM03909", "doc_id": "NCT02375295_exc", "case_bucket": "other", "source_criterion": "Patients with medical comorbidities preventing them from definitive surgical therapy. Patients with persistent stone burden following definitive surgical therapy.", "candidate_expression": "((definitive surgical therapy) AND (definitive surgical therapy preventing them from) AND (medical comorbidities) AND (stone burden persistent following definitive surgical therapy definitive surgical therapy))"}
{"candidate_id": "LLM03910", "doc_id": "NCT02445339_inc", "case_bucket": "or", "source_criterion": "English or Spanish speaking* Emergency Department patient Aged 18-80 Have had >4 emergency department visits within 12 months for 2 consecutive 12-month periods. Period of time can be extended by up to 6 months if incarcerated or institutionalized for ≥ 6 months. Meet Diagnostic and Statistical Manual version IV (DSM-IV) criteria for alcohol dependence or & DSM-V criteria for alcohol use disorder, severe. Have ≥2 days/week of heavy drinking (>4 drinks/day) Capable of giving informed consent.", "candidate_expression": "((12-month periods) AND (18-80) AND (2 consecutive) AND (>4) AND (Aged) AND (Capable of giving) AND (DSM-V criteria) AND (Diagnostic and Statistical Manual version IV (DSM-IV) criteria) AND (Emergency Department) AND (alcohol dependence) AND (alcohol use disorder) AND (drinks/day) AND (emergency department visits) AND (extended by up to 6 months) AND (heavy drinking) AND (informed consent) AND (severe) AND (within 12 months) AND (≥2 days/week) AND ((English speaking) OR (Spanish speaking)) AND ((incarcerated) OR (institutionalized)))"}
{"candidate_id": "LLM03911", "doc_id": "NCT02992938_exc", "case_bucket": "or", "source_criterion": "Patients ASA III y IV Chronic pain history Drug and alcohol abuse Chronic use of opioid and sedatives Neuropsychiatric illness NSAID and other analgesics used the 48 hours previous to the surgery CMI > 30", "candidate_expression": "((48 hours previous to the surgery) AND (> 3) AND (ASA) AND (CMI) AND (Chronic pain) AND (Chronic use) AND (III y IV) AND (Neuropsychiatric illness) AND (other) AND (the surgery) AND ((NSAID) OR (analgesics)) AND ((Drug abuse) OR (alcohol abuse)) AND ((opioid) OR (sedatives)))"}
{"candidate_id": "LLM03912", "doc_id": "NCT02380118_inc", "case_bucket": "other", "source_criterion": "Accident & Emergency Department patients, requiring parenteral drug sedation (as determined by an emergency clinician) will be enrolled.", "candidate_expression": "((Accident & Emergency Department) AND (parenteral drug sedation) AND (requiring))"}
{"candidate_id": "LLM03913", "doc_id": "NCT02283905_exc", "case_bucket": "other", "source_criterion": "The patient's data will be excluded if they die within 3 days of hospital admission.", "candidate_expression": "((die) AND (hospital admission) AND (within 3 days of hospital admission))"}
{"candidate_id": "LLM03914", "doc_id": "NCT03134196_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03915", "doc_id": "NCT01579604_inc", "case_bucket": "or", "source_criterion": "Cervical spine injury with functional loss in the upper extremity Greater than 4 months out from C-spine injury Stable motor recovery Medically stable International Classification for Surgery of the Hand in Tetraplegia of 0-5 at 6 months Grade 0 finger/thumb extension at 6 months Subjects fluent in English or when not fluent, an appropriate translator is present", "candidate_expression": "((C-spine injury Greater than 4 month) AND (Cervical spine injury functional loss) AND (International Classification for Surgery of the Hand in Tetraplegia 0-5 at 6 months) AND (Subjects fluent in English or when not fluent, an appropriate translator is present) AND (extension Grade 0 at 6 months finger thumb) AND (motor recovery Stable) AND (stable Medically))"}
{"candidate_id": "LLM03916", "doc_id": "NCT02802644_exc", "case_bucket": "or", "source_criterion": "Left main disease Known hypersensitivity or contraindication to any of the following medications: Heparin, aspirin, clopidogrel, sirolimus, siptagliptin and statin Congestive heart failure (patients with LVEF <30% or cardiogenic shock) Uncontrolled myocardial ischemia (repeated chest pain or dyspnea after revascularization) Uncontrolled ventricular arrhythmia History of malignancy with chemotherapy Serious hematologic disease (e.g. CML, MDS) Current infectious disease needs antibiotics therapy Creatinine level >1.5 mg/dL or dependence on dialysis Other severe concurrent illness (e.g. active infection, malignancy). Life expectancy of less than one year Pregnancy or women with potential childbearing Type I DM Treatment with insulin History of pancreatitis Who cannot read the informed consent form (e.g. illiteracy, foreigner)", "candidate_expression": "((Congestive heart failure) AND (Left main disease) AND (Pregnancy or women with potential childbearing) AND (Type I DM) AND (Who cannot read the informed consent form (e.g. illiteracy, foreigner)) AND (antibiotics) AND (chemotherapy) AND (hematologic disease Serious) AND (ife expectancy less than one year) AND (illness severe concurrent) AND (infectious disease) AND (insulin) AND (malignancy) AND (myocardial ischemia Uncontrolled) AND (pancreatitis) AND (revascularization) AND (ventricular arrhythmia Uncontrolled) AND ((LVEF <30%) OR (cardiogenic shock)) AND ((chest pain) OR (dyspnea)) AND ((contraindication) OR (hypersensitivity)) AND ((CML) OR (MDS)) AND ((Creatinine level >1.5 mg/dL) OR (dialysis)) AND ((Heparin) OR (aspirin) OR (clopidogrel) OR (siptagliptin) OR (sirolimus) OR (statin)) AND ((active infection) OR (malignancy)))"}
{"candidate_id": "LLM03917", "doc_id": "NCT02476461_exc", "case_bucket": "other", "source_criterion": "previous treated dupuytrens contracture same hand more than tree fingers involvement we will not include thumbs other things affecting hand function ASA>3 expected to live under five years Tetracycline treatment within two weeks pregnancy nursing allergy to clostridium histolyticum participant in other trial", "candidate_expression": "((>3) AND (ASA) AND (Tetracycline) AND (affecting hand function) AND (allergy) AND (clostridium histolyticum) AND (dupuytrens contracture) AND (expected to live) AND (fingers involvement) AND (more than tree) AND (nursing) AND (other things) AND (participant in other trial) AND (pregnancy) AND (previous) AND (same hand) AND (treated) AND (under five years) AND (within two weeks))"}
{"candidate_id": "LLM03918", "doc_id": "NCT03537924_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((40-75 yrs) AND (Healthy) AND (Kyrgyz ethnicity) AND (Written informed consent.) AND (age) AND (living at <800m) AND (living at low altitude) AND (need of) AND (without) AND ((men) OR (women)) AND ((any disease) OR (medication)))"}
{"candidate_id": "LLM03919", "doc_id": "NCT00650312_inc", "case_bucket": "or", "source_criterion": "1. Age: 18 years and older. 2. Sex: Male and non-pregnant, non-lactating female 1. Women of childbearing potential must have negative serum (Beta HCG) pregnancy tests performed within 14 days prior to the start of the study and on the evening prior to each dose administration. If dosing is scheduled on Sunday or Monday, the HCG pregnancy test should be given within 48 hours prior to dosing of each study period. An additional serum (Beta HCG) pregnancy test will be performed upon completion of the study. 2. Women of childbearing potential must practice abstinence or be using an acceptable form of contraception throughout the duration of the study. Acceptable forms of contraception include the following: (1) intrauterine device in place for at least 3 months prior to the start of the study and remaining in place during the study period, or (2) barrier methods containing or used in conjunction with a spermicidal agent, or (3) postmenopausal accompanied with a documented postmenopausal course of at least one year or surgical sterility (tubal ligation, oophorectomy or hysterectomy). 3. During the course of the study, from study screen until study exit - including the washout period, women of childbearing potential must use a spermicide containing barrier method of contraception in addition to their current contraceptive device. This advice should be documented in the informed consent form. 3. Weight: At least 60 kg (132 lbs) for man and 48 kg (106 lbs) for women and within 15% of Ideal Body Weight (IBW), as referenced by the Table of \"\"Desirable Weights of Adults\"\" Metropolitan Life Insurance Company, 1999 (See Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 4. All subjects should be judged normal and healthy during a pre-study medical evaluation (physical examination, laboratory evaluation, 12-lead ECG, hepatitis B and hepatitis C tests, HIV test, and urine drug screen including amphetamine, barbiturates, benzodiazepine, cannabinoid, cocaine, opiates, phencyclidine, and methadone) performed within 14 days of the initial dose of study medication.", "candidate_expression": "((12-lead ECG) AND (18 years and older) AND (Age) AND (At least 106 lbs) AND (At least 132 lbs) AND (At least 48 kg) AND (At least 60 kg) AND (Beta HCG) AND (During the course of the study) AND (HIV test) AND (Weight) AND (Women) AND (acceptable form) AND (amphetamine) AND (at least one year) AND (barbiturates) AND (barrier methods) AND (benzodiazepine) AND (cannabinoid) AND (childbearing potential) AND (cocaine) AND (contraceptive device) AND (current) AND (each dose administration) AND (for at least 3 months prior to the start of the study) AND (healthy) AND (hepatitis B tests) AND (hepatitis C tests) AND (in addition to) AND (in place during the study period) AND (laboratory evaluation) AND (lactating) AND (methadone) AND (negative) AND (non) AND (normal) AND (on the evening prior to each dose administration) AND (opiates) AND (phencyclidine) AND (physical examination) AND (pre-study medical evaluation) AND (pregnant) AND (serum pregnancy tests) AND (spermicidal agent) AND (spermicide containing barrier method of contraception) AND (surgical sterility) AND (the initial dose of study medication) AND (the start of the study) AND (the study period) AND (throughout the duration of the study) AND (urine drug screen) AND (within 14 days of the initial dose of study medication) AND (within 14 days prior to the start of the study) AND (within 15% of Ideal Body Weight (IBW)) AND (women) AND ((man) OR (women)) AND ((Male) OR (female)) AND ((abstinence) OR (contraception)) AND ((intrauterine device) OR (postmenopausal)) AND ((hysterectomy) OR (oophorectomy) OR (tubal ligation)))"}
{"candidate_id": "LLM03920", "doc_id": "NCT03070847_exc", "case_bucket": "or", "source_criterion": "pregnancy known allergies for tranexamic acid or any other substance in Exacyl deep vein thrombosis Hormone Replacement Therapy or oral contraceptive usage anticoagulants usage obesity - BMI (body mass index) >30 kg/m2 renal disease, as glomerular filtration rate (GFR) <60 ml/min/1,73 m*m seizures or epilepsy in the past", "candidate_expression": "((BMI >30 kg/m2) AND (Exacyl) AND (GFR seizures epilepsy) AND (Hormone Replacement Therapy) AND (allergies) AND (anticoagulants) AND (body mass index) AND (deep vein thrombosis) AND (glomerular filtration rate <60 ml/min/1,73 m*m) AND (obesity) AND (oral contraceptive) AND (pregnancy) AND (renal disease) AND (tranexamic acid))"}
{"candidate_id": "LLM03921", "doc_id": "NCT02118467_exc", "case_bucket": "other", "source_criterion": "Cardiopulmonary arrest Pregnancy Severe right heart failure", "candidate_expression": "((Cardiopulmonary arrest) AND (Pregnancy) AND (Severe) AND (right heart failure))"}
{"candidate_id": "LLM03922", "doc_id": "NCT03070847_inc", "case_bucket": "other", "source_criterion": "age > 18 y.o. American Society of Anesthesiologists Physical Status Classification (ASA) 1-2 signed informed consent form after reading the information about the study and talking with one of the investigators", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists Physical Status Classification 1-2) AND (age > 18 y.o) AND (signed informed consent form after reading the information about the study and talking with one of the investigators))"}
{"candidate_id": "LLM03923", "doc_id": "NCT03355157_inc", "case_bucket": "or", "source_criterion": "Written informed consent prior to beginning specific protocol procedures, including expected cooperation of the patients for the treatment and follow-up, willingness and ability to complete collection of data via wearable device and study mobile must be obtained and documented according to the local regulatory requirements. Female or male patients. Age = 18 years old. Metastatic invasive hormone receptor positive and HER2 negative breast cancer (histologically confirmed). Patients who in the opinion of the treating physician are candidates suitable for randomization for mono-chemotherapy treatment, that has either an approved label in Europe and/or is supported by guidelines for the treatment of first-line advanced BC, which are based on evidence on safety and efficacy in this setting. Symptomatic or asymptomatic metastatic breast cancer. Resolution of all acute toxic effects of prior anti-cancer therapy or surgical procedures to NCI CTCAE version 4.0 grade = 1 (except alopecia or other toxicities not considered a safety risk for the patient at investigator's discretion). Life-expectancy > 6 months. For female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).", "candidate_expression": "((Age = 18 years old Metastatic invasive hormone receptor positive) AND (Female) AND (Life-expectancy > 6 months) AND (NCI CTCAE version 4.0 grade = 1) AND (acute toxic effects Resolution) AND (alopecia) AND (anti-cancer therapy) AND (breast cancer HER2 negative) AND (except) AND (male) AND (metastatic breast cancer Symptomatic asymptomatic) AND (or female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).) AND (surgical procedure))"}
{"candidate_id": "LLM03924", "doc_id": "NCT03555526_inc", "case_bucket": "other", "source_criterion": "H pylori infection failed after at least two eradication therapies aged 20 years or greater willingness to receive rescue therapy", "candidate_expression": "((20 years or greater) AND (H pylori infection) AND (aged) AND (at least two) AND (eradication therapies) AND (failed) AND (rescue therapy) AND (willingness))"}
{"candidate_id": "LLM03925", "doc_id": "NCT02671318_inc", "case_bucket": "or", "source_criterion": "Adult kidney transplant recipients > 18 y.o. Kidney Transplant recipients, after the first episode of cytomegalovirus infection, using the current immunosuppressive regimen: azathioprine or mycophenolate, tacrolimus and prednisone.", "candidate_expression": "((> 18) AND (Adult) AND (azathioprine) AND (cytomegalovirus infection) AND (immunosuppressive regimen) AND (kidney transplant) AND (mycophenolate) AND (prednisone) AND (tacrolimus) AND (y.o.))"}
```
