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
{"candidate_id": "LLM05726", "doc_id": "NCT03329456_inc", "case_bucket": "other", "source_criterion": ". Inclusion criteria are American Society of Anesthesiologists (ASA) physical status I-III, age between 18 and 70 years and body mass index (BMI) between 20 and 35 kg/m2.", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists physical status) AND (BMI) AND (I-III) AND (age) AND (between 18 and 70 years) AND (between 20 and 35 kg/m2) AND (body mass index))"}
{"candidate_id": "LLM05727", "doc_id": "NCT03196843_inc", "case_bucket": "or", "source_criterion": "Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent. Histopathologic confirmed squamous cell carcinoma of head and neck ,including oral cavity, oropharynx, larynx, or hypopharynx. Ages=65 years,Not limited to gender. ECOG performance status =2. Patients with surgical contraindication or reject to surgery. Postoperative TNM(primary tumor,regional nodes,metastasis) staging III~IV, positive surgical margin. without evidence of distant metastases. No contraindication to chemoradiotherapy. Life expectancy > 3 months. Available Organ function: white blood cell=3.5×109/L, Neutrophils =1.5×109/L, Hemoglobin =80g/L, Blood platelet>100×109/L; Alanine aminotransferase (ALT) and Aspartate aminotransferase (AST)= 2.5 upper limit of normal(ULN); Total bilirubin (TBIL) <1.5 ULN;serum creatinine=1.5 ULN; creatinine clearance of = 50ml/min", "candidate_expression": "((<1.5 ULN) AND (= 2.5 upper limit of normal(ULN)) AND (= 50ml/min) AND (=1.5 ULN) AND (=1.5×109/L) AND (=2) AND (=3.5×109/L) AND (=65 years) AND (=80g/L) AND (> 3 months) AND (>100×109/L) AND (Ages) AND (Alanine aminotransferase (ALT)) AND (Aspartate aminotransferase (AST)) AND (Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent.) AND (Blood platelet) AND (ECOG performance status) AND (Hemoglobin) AND (Histopathologic) AND (Histopathologic confirmed) AND (III~IV,) AND (Life expectancy) AND (Neutrophils) AND (No) AND (Postoperative) AND (TNM staging) AND (Total bilirubin (TBIL)) AND (chemoradiotherapy) AND (contraindication) AND (creatinine clearance) AND (distant metastases) AND (evidence) AND (head and neck) AND (hypopharynx) AND (larynx) AND (oral cavity) AND (oropharynx) AND (positive) AND (reject) AND (serum creatinine) AND (squamous cell carcinoma) AND (surgery) AND (surgical) AND (surgical margin) AND (white blood cell) AND (without))"}
{"candidate_id": "LLM05728", "doc_id": "NCT03236246_exc", "case_bucket": "other", "source_criterion": "Serum phosphate <3.0 mg/dL Intravenous (IV) iron administered within 4 weeks prior to Screening Erythropoiesis-stimulating agents (ESA) administered within 4 weeks prior to Screening Blood transfusion within 4 weeks prior to Screening", "candidate_expression": "((<3.0 mg/dL) AND (Blood transfusion) AND (ESA) AND (Erythropoiesis-stimulating agents) AND (IV) AND (Intravenous) AND (Screening) AND (Serum phosphate) AND (iron) AND (within 4 weeks prior to Screening))"}
{"candidate_id": "LLM05729", "doc_id": "NCT03043495_inc", "case_bucket": "or", "source_criterion": "Patients undergoing surgeries in the upper limb (arm, forearm or hand)", "candidate_expression": "((surgeries upper limb) AND ((arm) OR (forearm) OR (hand)))"}
{"candidate_id": "LLM05730", "doc_id": "NCT00445029_inc", "case_bucket": "other", "source_criterion": "For both groups: Patients aged from 18 to 65 years old. Both genders eligible for study. Female participants must use a contraceptive method. Feasibility of patch testing. Participants must be able to understand and sign the Informed Consent, and comply with all aspects of the protocol. Patients must be registered in a social security system or with a health insurance coverage  First group: allergic patients Patients with allergic contact dermatitis to para-phenylenediamine (PPD) based on a history of PPD contact dermatitis and positive PPD patch tests.  Second group : healthy volunteers No history of PPD allergic contact dermatitis, with a negative PPD patch test.", "candidate_expression": "((Both genders) AND (Feasibility of) AND (Female) AND (No) AND (PPD) AND (PPD patch test) AND (PPD patch tests) AND (aged) AND (allergic) AND (allergic contact dermatitis) AND (be able to) AND (comply with all aspects of the protocol) AND (contact dermatitis) AND (contraceptive method) AND (from 18 to 65 years old) AND (health insurance coverage) AND (healthy) AND (negative) AND (para-phenylenediamine (PPD)) AND (patch testing) AND (positive) AND (registered in a social security system) AND (understand and sign the Informed Consent))"}
{"candidate_id": "LLM05731", "doc_id": "NCT02385448_exc", "case_bucket": "or", "source_criterion": "Operative findings not suggestive of endometriotic cyst Contraindications to progestogens or oral contraceptive pills Unwillingness to tolerate menstrual irregularity Planning pregnancy within 2 years of study Cannot understand English, Cantonese or Putonghua", "candidate_expression": "((Contraindications) AND (Operative findings) AND (Planning) AND (Unwillingness to tolerate) AND (endometriotic cyst) AND (menstrual irregularity) AND (not) AND (oral contraceptive pills) AND (pregnancy) AND (progestogens) AND (suggestive) AND (within 2 years of study))"}
{"candidate_id": "LLM05732", "doc_id": "NCT02890719_exc", "case_bucket": "or", "source_criterion": "Genotype 2, 3, 5 or 6 infection. Decompensated cirrhosis defined by the presence of actual or previous history of clinical decompensation including ascites, hepatic encephalopathy, variceal bleeding or spontaneous bacterial peritonitis, or a Child-Pugh B or C. Hepatocellular carcinoma after liver transplantation. Total bilirubin > 3 mg/dL. Immunosuppression with cyclosporine or an mTOR inhibitor (everolimus or sirolimus). Severe extrahepatic diseases: cardiovascular, respiratory, cerebrovascular and poorly controlled diabetes. Platelets < 75 x 109 cells/L. Neutrophil count < 0.5 x 109 cells/L. Hemoglobin < 9 g/dL. Albumin < 3g/dL. HIV infection. Hepatitis B infection. Active intake of toxic amounts of alcohol or recreational drugs. Females who are pregnant, become to be pregnant or breastfeeding or males whose partners are pregnant, become to be pregnant or breastfeeding. Intake of disallowed medications including(but not limited to): 1. Antibiotics: clarithromycin, erythromycin, telithromycin, nafcillin, rifampin 2. Antifungals: itraconazole, ketoconazole, voriconazole 3. Antihypertensives: nifedipine 4. Anticonvulsants: carbamazepine, phenytoin, phenobarbital 5. Bosentan 6. Modafinil 7. St.Jonh's Wort 8. Immunosuppressants: cyclosporin, everolimus, sirolimus 9. Diabetes agents: glibenclamide, glyburide 10. Lipid lowering agents: gemfibrozil 11. Eltrombopag 12. Lapatinib 13. HIV medications: efavirenz, etravirine, all ritonavir boosted and unboosted HIV protease inhibitors 14. Statins: simvastatin, fluvastatin, rosuvastatin at doses greater than 10 mg/d, atorvastatin at doses greater than 10 mg/d.", "candidate_expression": "((Albumin < 3g/dL) AND (Bosentan) AND (Eltrombopag) AND (Females) AND (Genotype 2, 3, 5 or 6) AND (HIV infection) AND (Hemoglobin < 9 g/dL) AND (Hepatitis B infection) AND (Hepatocellular carcinoma after liver transplantation) AND (Immunosuppression) AND (Lapatinib) AND (Modafinil) AND (Neutrophil count < 0.5 x 109 cells/L) AND (Platelets < 75 x 109 cells/L) AND (Severe) AND (St.Jonh's Wort) AND (Total bilirubin > 3 mg/dL) AND (breastfeeding) AND (carbamazepine) AND (cirrhosis Decompensated) AND (clinical decompensation) AND (disallowed medications) AND (extrahepatic diseases Severe) AND (gemfibrozil) AND (infection) AND (liver transplantation) AND (males) AND (nifedipine) AND (phenobarbital) AND (phenytoin) AND (pregnant) AND (pregnant become) AND (ritonavir) AND ((cyclosporin) OR (everolimus) OR (sirolimus)) AND ((glibenclamide) OR (glyburide)) AND ((HIV protease inhibitors) OR (efavirenz) OR (etravirine)) AND ((ritonavir boosted) OR (ritonavir unboosted)) AND ((atorvastatin doses greater than 10 mg/d) OR (fluvastatin) OR (rosuvastatin doses greater than 10 mg/d) OR (simvastatin)) AND ((Child-Pugh B or C) OR (ascites) OR (hepatic encephalopathy) OR (spontaneous bacterial peritonitis) OR (variceal bleeding)) AND ((actual) OR (previous)) AND ((cyclosporine) OR (mTOR inhibitor)) AND ((everolimus) OR (sirolimus)) AND ((cardiovascular) OR (cerebrovascular) OR (diabetes poorly controlled) OR (respiratory)) AND ((alcohol Active intake toxic amounts) OR (recreational drugs Active intake)) AND ((clarithromycin) OR (erythromycin) OR (nafcillin) OR (rifampin) OR (telithromycin)) AND ((itraconazole) OR (ketoconazole) OR (voriconazole)))"}
{"candidate_id": "LLM05733", "doc_id": "NCT03338296_inc", "case_bucket": "or", "source_criterion": "Healthy male or female adolescents, age 12 to 17 years (inclusive) at Screening, with a body mass index (BMI) that is greater than or equal to the United States-weighted mean of the 95th percentile based on age and sex with a body weight greater than 60 kilograms (kg). Participants with Type 2 diabetes mellitus (T2DM) may have a pre-existing or new diagnosis of T2DM. HbA1c =6.5% fasting plasma glucose (FPG) =126 mg/dL (7.0 mmol/L) Participants and their families not planning to move away from the area for the duration of the study Participants able and willing to comply with all aspects of the study, including a standardized, reduced calorie diet and an age appropriate, increased physical activity program Participants considered in stable health in the opinion of the investigator Able and willing to support and supervise study participation in the opinion of the investigator, including consideration of any existing physical, medical, or mental condition that prevents compliance with the protocol Able and willing to personally comply with and execute all aspects of the study requirements for the caregivers or guardians", "candidate_expression": "((12 to 17 years) AND (7.0 mmol/L) AND (=126 mg/dL) AND (=6.5%) AND (Able to personally comply) AND (HbA1c) AND (Healthy) AND (able to comply) AND (adolescents) AND (age) AND (age appropriate) AND (at Screening) AND (based on age) AND (based on sex) AND (body mass index (BMI)) AND (body weight) AND (fasting plasma glucose (FPG)) AND (for the duration of the study) AND (greater than 60 kilograms (kg)) AND (greater than or equal to the 95th percentile) AND (greater than or equal to the United States-weighted mean of the 95th percentile) AND (increased physical activity program) AND (not) AND (planning to move away) AND (reduced calorie diet) AND (stable health) AND (standardized) AND (the study) AND (willing to comply) AND (willing to personally comply) AND ((female) OR (male)) AND ((caregivers) OR (guardians)))"}
{"candidate_id": "LLM05734", "doc_id": "NCT02678962_inc", "case_bucket": "other", "source_criterion": "Age from 40 to 80 years old, either gender; Patients with bilateral age related cataracts, require bilateral cataract phacoemulsification combined Intraocular Lens implantation; Willing to undergo second eye surgery within 7 days after first eye surgery; The potential postoperative visual acuity of 20/40 or better in both eyes; Preoperative measurement of corneal astigmatism indicate the subjects are suitable for multifocal intraocular lenses implantation; Capability to understand the informed consent and willing and able to attend study", "candidate_expression": "((Age from 40 to 80 years old) AND (Capability to understand the informed consent and willing and able to attend study) AND (Intraocular Lens implantation) AND (cataract phacoemulsification) AND (cataracts bilateral age related) AND (measurement of corneal astigmatism Preoperative suitable) AND (multifocal intraocular lenses implantation))"}
{"candidate_id": "LLM05735", "doc_id": "NCT03115151_inc", "case_bucket": "other", "source_criterion": "Adult subjects aged 18 years or older Scheduled for elective posterior lumbar spinal fusion surgery between 1 and 3 levels", "candidate_expression": "((18 years or older) AND (Adult) AND (Scheduled for) AND (aged) AND (between 1 and 3 levels) AND (elective) AND (posterior lumbar spinal fusion surgery))"}
{"candidate_id": "LLM05736", "doc_id": "NCT01117181_inc", "case_bucket": "or", "source_criterion": "Possible or probable Alzheimer's disease (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria), with Mini-Mental State Exam (MMSE) score of 10-26 inclusive; MMSE scores above 26 in those who nevertheless meet criteria for AD may be allowed with Steering Committee approval on a case by case basis Clinically significant apathy for at least four weeks for which either 1) the frequency of apathy as assessed by the Neuropsychiatric Inventory (NPI) is 'Very frequently', or 2) the frequency of apathy as assessed by the NPI is 'Frequently' or 'Often' AND the severity of apathy as assessed by the NPI is 'Moderate' or 'Marked' A medication for apathy is appropriate, in the opinion of the study physician Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments No change to AD medications within the month preceding randomization, including starting, stopping, or dosage modifications Treatment with stable doses of selective serotonin reuptake inhibitor antidepressants(SSRIs) is appropriate if stable for 3 months prior to randomization. Other psychotropics(with the exclusion of antipsychotics), if stable for 3 months, may be allowed only with Steering Committee approval on a case by case basis.", "candidate_expression": "((A medication for apathy is appropriate, in the opinion of the study physician) AND (AD) AND (AD medications) AND (Alzheimer's disease Possible probable) AND (Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study) AND (MMSE scores above 26) AND (Mini-Mental State Exam (MMSE) score of 10-26 inclusive) AND (NPI Frequently Often) AND (NPI Moderate Marked) AND (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria) AND (Neuropsychiatric Inventory (NPI) Very frequently) AND (Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver) AND (Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments) AND (Treatment) AND (apathy) AND (at least four weeks) AND (frequency of apathy) AND (medication for apathy) AND (selective serotonin reuptake inhibitor antidepressants(SSRIs) stable doses) AND (severity of apathy) AND NOT (change to AD medications within the month preceding randomization))"}
{"candidate_id": "LLM05737", "doc_id": "NCT02763007_inc", "case_bucket": "or", "source_criterion": "Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations. Male, or female, 19 years to 75 years. Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study Subjects completed PEAK can be included within 30 days after End Of the Study Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study.", "candidate_expression": "((Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations) AND (Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study) AND (Male) AND (Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study) AND (Subjects completed PEAK can be included within 30 days after End Of the Study) AND (female) AND (years 19 years to 75))"}
{"candidate_id": "LLM05738", "doc_id": "NCT00483106_exc", "case_bucket": "other", "source_criterion": "Psychosis Tourette syndrome Intelligence quotient (IQ) < 70 Pervasive developmental disorder (PDD)", "candidate_expression": "((< 70) AND (IQ) AND (Intelligence quotient) AND (PDD) AND (Pervasive developmental disorder) AND (Psychosis) AND (Tourette syndrome))"}
{"candidate_id": "LLM05739", "doc_id": "NCT02456532_inc", "case_bucket": "other", "source_criterion": "DSM-5 diagnosis of insomnia", "candidate_expression": "((DSM-5) AND (insomnia))"}
{"candidate_id": "LLM05740", "doc_id": "NCT03182114_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities hypertensive disorders of pregnancy peripartum bleeding baseline systolic blood pressure (SBP) < 100 mmHg body mass index > 35", "candidate_expression": "((< 100 mmHg) AND (> 35) AND (Cardiac morbidities) AND (SBP) AND (baseline) AND (body mass index) AND (hypertensive disorders of pregnancy) AND (peripartum bleeding) AND (systolic blood pressure))"}
{"candidate_id": "LLM05741", "doc_id": "NCT00317148_inc", "case_bucket": "other", "source_criterion": "Healthy postmenopausal women with 50 or more moderate to severe hot flushes. Women between 40 to 70 years of age.", "candidate_expression": "((Healthy) AND (Women) AND (age between 40 to 70 years) AND (moderate to severe hot flushes) AND (postmenopausal) AND (women 50 or more))"}
{"candidate_id": "LLM05742", "doc_id": "NCT00061308_inc", "case_bucket": "or", "source_criterion": "Have had one prior platinum-based chemotherapy regimen for the treatment of primary disease. At least 4 weeks since last surgery or radiation therapy. Must have had a treatment-free interval of greater than 6 months following response to platinum. ECOG performance status of 0,1, or 2.", "candidate_expression": "((At least 4 weeks since last surgery or radiation therapy) AND (ECOG performance status) AND (a treatment-free interval) AND (greater than 6 months following response to platinum) AND (platinum) AND (platinum-based chemotherapy regimen) AND (primary disease) AND (prior) AND (response to platinum) AND ((.) OR (0) OR (0,1)) AND ((last surgery) OR (radiation therapy)))"}
{"candidate_id": "LLM05743", "doc_id": "NCT02245256_exc", "case_bucket": "or", "source_criterion": "Pediatric patients (under 18 years) Pregnancy Patients who are unresponsive at baseline, who have neurologic deficits at baseline, or who are allergic to dexmedetomidine", "candidate_expression": "((Pediatric) AND (Pregnancy) AND (at baseline) AND (dexmedetomidine) AND (under 18 years) AND (years) AND ((allergic) OR (neurologic deficits) OR (unresponsive)))"}
{"candidate_id": "LLM05744", "doc_id": "NCT00728156_exc", "case_bucket": "or", "source_criterion": "Contraindication to Clopidogrel Smoking (current smokers and patients who quit smoking less than six months) Malignancy(diagnosed or under investigation) Haematological disorders (Anaemia, malignancy, bleeding disorders) Women of child-bearing potential Use of corticosteroids/other antithrombotic agents(warfarin) Chronic liver disease (Cirrhosis, malignancy and patients with more than twice the upper limit of liver function tests) Unable to consent. Use of other investigational study drugs within 1 year prior to study entry Previous participation in this study", "candidate_expression": "((Chronic liver disease) AND (Clopidogrel) AND (Contraindication) AND (Haematological disorders) AND (Malignancy) AND (Previous) AND (Smoking) AND (Unable to consent.) AND (Women) AND (child-bearing potential) AND (current) AND (investigational study drugs) AND (less than six months) AND (more than twice the upper limit) AND (participation in this study) AND (quit smoking) AND (smokers) AND (warfarin) AND (within 1 year prior to study entry) AND ((Anaemia) OR (bleeding disorders) OR (malignancy)) AND ((antithrombotic agents) OR (corticosteroids)) AND ((Cirrhosis) OR (liver function tests) OR (malignancy)) AND ((diagnosed) OR (under investigation)))"}
{"candidate_id": "LLM05745", "doc_id": "NCT02247128_exc", "case_bucket": "or", "source_criterion": "Need for long-term oral anticoagulation; Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to aspirin or clopidogrel. Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to (N)OAC or clopidogrel.", "candidate_expression": "((Bare-metal stent) AND (Drug-eluting stent) AND (Need for) AND (TAVI procedure) AND (implantation) AND (long-term oral anticoagulation) AND (within 1 month prior to TAVI procedure) AND (within 3 months prior to TAVI procedure) AND ((Allergy) OR (intolerance)) AND ((aspirin) OR (clopidogrel)) AND (((N)OAC) OR (clopidogrel)))"}
{"candidate_id": "LLM05746", "doc_id": "NCT02650024_inc", "case_bucket": "or", "source_criterion": "Adult (= 18 years old) subjects with chronic genotype 1 HCV and NCI with a GDS greater than or equal to 0.5 (n=60). Presence of chronic HCV infection based on chart review will be defined as positive for anti-HCV antibody or HCV RNA at least 6 months before screening. For the HIV/HCV co-infected group only, subjects must have HIV. HIV status will be obtained through self report. Self report will be confirmed at screening using a HIV-1 point of care test. In the event that point of care test and self-report are discordant, then HIV status will be confirmed by a licensed Western blot or a second antibody test. HIV/HCV co-infected subjects (n=12) must also have a HIV RNA measurement <50 copies/mL at the pre-treatment visit. Platelets >150,000 Aspartate aminotransferase (AST)/Alanine aminotransferase (ALT) <10x upper limit of normal Creatinine clearance >30 milliliters/minute/1.73 centimeter squared", "candidate_expression": "((Adult) AND (Alanine aminotransferase (ALT) <10x upper limit of normal) AND (Aspartate aminotransferase (AST) <10x upper limit of normal) AND (Creatinine clearance >30 milliliters/minute/1.73 centimeter squared) AND (GDS greater than or equal to 0.5) AND (HCV) AND (HCV RNA) AND (HCV infection chronic) AND (HIV) AND (HIV RNA measurement <50 copies/mL at the pre-treatment visit) AND (NCI) AND (Platelets >150,000) AND (anti-HCV antibody) AND (co-infected) AND (old = 18 years old))"}
{"candidate_id": "LLM05747", "doc_id": "NCT03008005_inc", "case_bucket": "other", "source_criterion": "Able to give informed consent Right-handed Age between 18-50 years old, Physically and neurologically healthy [confirmed by a comprehensive medical history] Current PTSD diagnosis", "candidate_expression": "((Able to give informed consent) AND (Age) AND (Current) AND (PTSD) AND (Right-handed) AND (between 18-50 years old) AND (comprehensive medical history) AND (healthy Physically) AND (neurologically healthy))"}
{"candidate_id": "LLM05748", "doc_id": "NCT03115151_exc", "case_bucket": "or", "source_criterion": "Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators. Immunocompromised subject Coagulopathy Severe liver and renal dysfunction Preoperative neurological deficits The dura damage during surgery Inability to follow directions or comprehend the English language. Females who are pregnant as determined by positive pregnancy test on or before the day of surgery. Prisoners. Patient refusal to provide informed consent. Allergy to amide local anesthetics (lidocaine, bupivacaine, ropivacaine) or opioid (fentanyl).", "candidate_expression": "((Allergy) AND (Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators.) AND (Coagulopathy) AND (Females who are pregnant as determined by positive pregnancy test on or before the day of surgery) AND (Immunocompromised) AND (Inability to follow directions or comprehend the English language) AND (Patient refusal to provide informed consent) AND (Preoperative) AND (Prisoners) AND (Severe) AND (amide local anesthetics) AND (bupivacaine) AND (dura damage) AND (fentanyl) AND (lidocaine) AND (liver dysfunction) AND (neurological deficits) AND (opioid) AND (renal dysfunction) AND (ropivacaine) AND (surgery))"}
{"candidate_id": "LLM05749", "doc_id": "NCT02908919_inc", "case_bucket": "or", "source_criterion": "Subjects referred to diagnostic or therapeutic colonoscopy.", "candidate_expression": "((colonoscopy) AND ((diagnostic) OR (therapeutic)))"}
{"candidate_id": "LLM05750", "doc_id": "NCT00543712_exc", "case_bucket": "or", "source_criterion": "Systemic therapy or radiotherapy within 4 weeks prior to Day 1 Prior therapy with agents targeting the DR5 apoptosis pathway Major surgical procedure, open biopsy, or significant traumatic injury within 4 weeks prior to Day 1, or anticipation of need for major surgical procedure during the course of the study Other invasive malignancies within 5 years prior to Day 1 Known active brain metastases Uncontrolled intercurrent illness, including but not limited to ongoing or active infection requiring parenteral antibiotics at enrollment Clinically significant, symptomatic cardiovascular disease, New York Heart Association (NYHA) Grade II or greater congestive heart failure, serious cardiac arrhythmia, Grade II or greater peripheral vascular disease, or history of major heart surgery within 6 months of Day 1, or any situation that would likely limit compliance with study requirements Known to be positive for hepatitis C or hepatitis B surface antigen History of other disease, metabolic dysfunction, physical examination finding, or clinical laboratory finding giving reasonable suspicion of a disease or condition that contraindicates use of an investigational drug or that might affect interpretation of the results of the study or render the patient at high risk for treatment complications Use of anticoagulation therapy Participation in clinical trials or undergoing other investigational procedures within 30 days prior to Day 1 Pregnancy or breast feeding Known sensitivity to any of the products administered during the study Any disorder that compromises the ability of the patient to give written informed consent and/or comply with study procedures", "candidate_expression": "((Clinically significant) AND (Day 1) AND (Grade II or greater) AND (History) AND (Major) AND (New York Heart Association (NYHA)) AND (Other) AND (Uncontrolled) AND (active) AND (anticipation of need) AND (anticoagulation) AND (anticoagulation therapy) AND (any of the products administered during the study) AND (at enrollment) AND (brain metastases) AND (cardiac arrhythmia) AND (cardiovascular disease) AND (clinical laboratory) AND (clinical laboratory finding) AND (compromises the ability of) AND (congestive heart failure) AND (contraindicates) AND (disease) AND (disorder) AND (enrollment) AND (history of) AND (infection) AND (intercurrent illness) AND (invasive malignancies) AND (investigational drug) AND (limit compliance) AND (major) AND (metabolic dysfunction) AND (other) AND (parenteral antibiotics) AND (physical examination) AND (physical examination finding) AND (positive) AND (prior to Day 1) AND (sensitivity) AND (serious) AND (significant) AND (surgical procedure) AND (suspicion of) AND (symptomatic) AND (treatment complications) AND (within 30 days prior to Day 1) AND (within 5 years prior to Day 1) AND (within 6 months of Day 1) AND ((Systemic therapy) OR (radiotherapy)) AND ((open biopsy) OR (surgical procedure) OR (traumatic injury)) AND ((during the course of the study) OR (the study)) AND ((active) OR (ongoing)) AND ((Day 1) OR (within 4 weeks prior to Day 1)) AND ((heart surgery) OR (peripheral vascular disease)) AND ((hepatitis B surface antigen) OR (hepatitis C)) AND ((Prior) OR (agents targeting the DR5 apoptosis pathway) OR (therapy)) AND ((condition) OR (disease)) AND ((affect interpretation of the results) OR (render the patient at high risk)) AND ((Participation in clinical trials) OR (undergoing other investigational procedures)) AND ((Pregnancy) OR (breast feeding)) AND ((comply with study procedures) OR (give written informed consent)))"}
```
