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
{"candidate_id": "LLM05551", "doc_id": "NCT02893228_exc", "case_bucket": "or", "source_criterion": "Patient refusal Allergy to local anaesthesia Severe coagulopathy Contralateral phrenic nerve palsy Local infection Moderate to severe pulmonary dysfunction (GOLD II, II, IV)", "candidate_expression": "((Allergy) AND (Contralateral) AND (GOLD) AND (II, II, IV) AND (Local infection) AND (Moderate) AND (Patient refusal) AND (Severe) AND (coagulopathy) AND (local anaesthesia) AND (phrenic nerve palsy) AND (pulmonary dysfunction) AND (severe))"}
{"candidate_id": "LLM05552", "doc_id": "NCT01942109_exc", "case_bucket": "other", "source_criterion": "uncontrolled hypertension uncontrolled diabetes creatinine > 2,5 mg/dl potassium > 6 mg/dl acute coronary syndrome hypertrophic cardiomyopathy", "candidate_expression": "((> 2,5 mg/dl) AND (> 6 mg/dl) AND (acute coronary syndrome) AND (creatinine) AND (diabetes) AND (hypertension) AND (hypertrophic cardiomyopathy) AND (potassium) AND (uncontrolled))"}
{"candidate_id": "LLM05553", "doc_id": "NCT01078051_inc", "case_bucket": "or", "source_criterion": "Patients with angina or silent ischemia and documented ischemia Patients who are eligible for intracoronary stenting Age > 18 years De novo lesion CTO Reference vessel size 2.5 mm by visual estimation At least one CTO lesions located in proximal or mid epicardial coronary artery. (If the patient has two CTO lesions, one CTO lesion should be located in proximal or mid epicardial coronary artery) Angiographically defined total occlusion over 3 months If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)", "candidate_expression": "((Age > 18 years) AND (CTO De novo lesion) AND (CTO lesions At least one) AND (If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)) AND (Reference vessel size by visual estimation 2.5 mm) AND (coronary artery) AND (intracoronary stenting) AND (total occlusion Angiographically defined 3 months) AND ((angina) OR (ischemia documented) OR (ischemia silent)) AND ((in proximal coronary artery) OR (mid epicardial coronary artery)))"}
{"candidate_id": "LLM05554", "doc_id": "NCT01856491_exc", "case_bucket": "or", "source_criterion": "Known or suspected sensitivity to Dexamethasone Acetate (DXA) Mechanical tricuspid heart valve Subject is enrolled in any other concurrent study without prior written approval from Boston Scientific (BSC), with the exception of local mandatory governmental registries and observational studies/registries that are not in conflict and do not affect the following: Schedule of procedures for the RELIANCE 4-Front Study (i.e. should not cause additional or missed visits); RELIANCE 4-Front Study outcome (i.e. involve medications that could affect the heart rate of the subject); Conduct of the RELIANCE 4-Front Study per Good Clinical Practice (GCP)/ International Organization for Standardization (ISO) 14155:2011/ 21 CFR 812/ local regulations Currently on the active heart transplant list Documented life expectancy of less than 12 months Women of childbearing potential who are or might be pregnant at the time of study enrollment (method of assessment upon physician discretion) Currently requiring chronic dialysis", "candidate_expression": "((Dexamethasone Acetate (DXA)) AND (Known) AND (Mechanical tricuspid heart valve) AND (Women) AND (active heart transplant list) AND (childbearing potential) AND (chronic dialysis) AND (life expectancy less than 12 months) AND (pregnant are or might be at the time of study enrollment) AND (requiring chronic dialysis Currently) AND (sensitivity to Dexamethasone Acetate (DXA)) AND (suspected))"}
{"candidate_id": "LLM05555", "doc_id": "NCT01994382_inc", "case_bucket": "or", "source_criterion": "Phase 1 Specific Patient at least 18yrs of age with histologically confirmed CLL/SLL or B-cell Non-Hodgkin lymphoma (DLBCL, FL, MCL, MZL, lymphoplasmacytic lymphoma). Phase 2a Inclusion Histological evidence: FL Grade 1-3A/iNHL, with relapsed or refractory disease (iNHL includes LPL/WM, MZL); aNHL, defined as DLBCL, FL Grade 3B, MCL, and transformed NHL with relapsed disease; CLL/SLL, PTCL, or CTCL (with MF/SS) with relapsed or refractory. Received BCR and/or BCL2 inhibitors were intolerant or had relapsed/refractory disease afterwards. Prior treatment for lymphoid malignancy for progressive /refractory disease ≥ 1 prior regimen (min 2 cycles) with antibody conjugate, cytotoxic chemotherapy, or TKI alone or in combination. Measureable disease defined as: ≥ 1 lesion ≥ 1.5 cm single dimension via CT, CT/PET with nodal or mass lesions; Quantifiable circulating tumor cells; or for Waldenström's macroglobulinemia presence of IgM l > 2X ULN; For CTCL: mSWAT > 0 Ability to provide diagnostic reports General Inclusion ECOG Score of 0 or 1. Hematologic ANC > 1000/uL and platelet > 75,000/uL, Serum creatinine of < 1.5 ULN or calculated CrCl of > 50 mL/min Bilirubin < 20.0mg/dL (if Gilberts then < 2.5 mg/dL) and AST/AST < 2.5 ULN", "candidate_expression": "((AST/AST < 2.5 ULN) AND (B-cell Non-Hodgkin lymphoma) AND (BCL2 inhibitors) AND (BCR inhibitors) AND (Bilirubin < 20.0mg/dL) AND (CLL) AND (CT) AND (CT/PET) AND (CTCL) AND (DLBCL) AND (ECOG Score 0 or 1) AND (FL) AND (Gilberts < 2.5 mg/dL) AND (Grade 1-3A) AND (Grade 3B) AND (Hematologic ANC > 1000/uL) AND (Histological) AND (IgM l > 2X ULN) AND (LPL) AND (MCL) AND (MF) AND (MZL) AND (Measureable disease ≥ 1 lesion) AND (PTCL) AND (SLL) AND (SS) AND (Serum creatinine < 1.5 ULN) AND (TKI) AND (WM) AND (Waldenström's macroglobulinemia) AND (aNHL) AND (age at least 18yrs) AND (antibody conjugate) AND (calculated CrCl > 50 mL/min) AND (circulating tumor cells) AND (cytotoxic chemotherapy) AND (histologically confirmed) AND (iNHL) AND (intolerant) AND (lymphoid malignancy) AND (lymphoplasmacytic lymphoma) AND (mSWAT > 0) AND (mass lesions) AND (nodal lesions) AND (platelet > 75,000/uL) AND (progressive disease) AND (refractory disease) AND (refractory disease Prior) AND (relapsed) AND (relapsed disease) AND (transformed NHL) AND (treatment) AND (≥ 1.5 cm single dimension ≥ 1.5 cm))"}
{"candidate_id": "LLM05556", "doc_id": "NCT03185130_exc", "case_bucket": "other", "source_criterion": "Pregnant Meningeal signs are present Acute angle closure glaucoma is suspected Head trauma within the previous two weeks Lumbar puncture within the previous two weeks Thunderclap onset of the headache Known allergy to one of the study drugs History of intracranial hypertension Is a prisoner Patient declined informed consent Non-English speaking patient or parent/guardian for pediatric patients Attending provider excludes patient Severe Dehydration", "candidate_expression": "((Acute angle closure glaucoma suspected) AND (Dehydration Severe) AND (Head trauma within the previous two weeks) AND (Lumbar puncture within the previous two weeks) AND (Meningeal signs) AND (Pregnant) AND (Thunderclap onset) AND (allergy) AND (declined) AND (headache) AND (informed consent) AND (intracranial hypertension History) AND (prisoner) AND (study drugs))"}
{"candidate_id": "LLM05557", "doc_id": "NCT02934269_exc", "case_bucket": "or", "source_criterion": "Exposure/treatment to an investigational (new chemical entity) or marketed drug or biologic within 30 days preceding the first dose administration, or five half-lives of that investigational drug or biologic, if known (whichever is longer). Donation blood or serum within 8 weeks before the first dose administration to a blood bank or blood donation center. History of alcohol or drug abuse (as defined by the current version of the DSM) within 2 years before the first dose administration, or positive alcohol or drug screen. Vaccination within 30 days prior to the first dose administration or has plans to receive a vaccination during the course of the study (including the follow phone call on Day 105).", "candidate_expression": "((History) AND (current version of the DSM) AND (during the course) AND (first dose administration) AND (plans) AND (positive) AND (study) AND (the first dose administration) AND (within 2 years before) AND (within 30 days prior) AND (within 8 weeks before) AND ((alcohol screen) OR (drug screen)) AND ((Vaccination) OR (vaccination)) AND ((Donation blood) OR (Donation serum)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM05558", "doc_id": "NCT03073603_exc", "case_bucket": "or", "source_criterion": "Any MS relapse in the last five years, as determined at the screen visit by the PI Any new or definitely enlarging T2/FLAIR lesion or new gadolinium-enhancing lesion within the past three years (at least two scans separated by at least three years must be reviewed) on brain or spine MRI scan. Lesions must be 3mm or larger to be exclusionary. Significant (as defined by the PI) intolerance of presently-used DMT Use of inhaled or topical steroids are not an exclusion criteria. Use of oral steroids for no greater than 14 days given for a non-MS condition is not exclusionary. alemtuzumab, mitoxantrone, cyclophosphamide, methotrexate, cyclosporine, or rituximab Prior use of any experimental agent used as a DMT for MS in the last five years uncontrolled hypertension, uncontrolled diabetes, uncontrolled asthma, or uncontrolled depression Cancers other than basal cell skin cancers within the last 5 years Unable to give informed consent or follow the protocol Unable to undergo brain MRI Unwilling to be randomized per this protocol History of other chronic neurological illnesses that might mimic MS with chronic or intermittent symptoms (i.e. ALS, myasthenia gravis, chronic neuropathy, etc.)", "candidate_expression": "((ALS) AND (Cancers) AND (DMT presently-used) AND (Lesions 3mm or larger) AND (MS) AND (T2/FLAIR lesion) AND (Unwilling to be randomized per this protocol) AND (alemtuzumab) AND (asthma uncontrolled) AND (brain MRI Unable to undergo) AND (brain MRI scan) AND (chronic neurological illnesses mimic MS) AND (chronic neuropathy) AND (cyclophosphamide) AND (cyclosporine) AND (depression uncontrolled) AND (diabetes uncontrolled) AND (gadolinium) AND (hypertension uncontrolled) AND (inhaled steroids) AND (intolerance Significant) AND (lesion gadolinium-enhancing) AND (methotrexate) AND (mitoxantrone) AND (myasthenia gravis) AND (non-MS condition) AND (not) AND (relapse in the last five years) AND (rituximab) AND (scans at least two separated by at least three years) AND (spine MRI scan) AND (topical steroids) AND NOT (oral steroids no greater than 14 days) AND NOT (basal cell skin cancers within the last 5 years))"}
{"candidate_id": "LLM05559", "doc_id": "NCT01218737_exc", "case_bucket": "or", "source_criterion": "Surgery and/or previous ocular pathology (presence of scar/change in the cornea, glaucoma, retinopathies, etc.). Patient has diabetes or is immunodepressed. Any systemic infection during the study. Signs and/or symptoms of ocular inflammation/infection (bacterial, viral, fungal, caused by Chlamydia, by Mycobacterium, Acanthamoeba or of allergic etiology). Have used any systemic or topical antibiotics for ocular infection in the previous 14 days. Patient has known hypersensitivity to any of the components of the formulations used in the study.", "candidate_expression": "((Acanthamoeba) AND (Chlamydia caused by Chlamydia caused by Mycobacterium caused by Acanthamoeba) AND (Mycobacterium) AND (Surgery) AND (allergic etiology systemic) AND (change in the cornea) AND (diabetes) AND (glaucoma) AND (hypersensitivity components of the formulations) AND (immunodepressed) AND (infection systemic during the study) AND (ocular infection) AND (ocular infection bacterial etiology viral etiology fungal etiology) AND (ocular inflammation) AND (ocular pathology previous) AND (retinopathies) AND (scar) AND (systemic antibiotics) AND (topical antibiotics topical))"}
{"candidate_id": "LLM05560", "doc_id": "NCT01639664_exc", "case_bucket": "or", "source_criterion": "Age less than 14 years Pregnancy Estimated life expectancy (due to comorbidities) less than 90 days Presence of relative or absolute contraindications to CPFA Admission from an other ICU where the patient remained for more than 24 hours Absence of informed consent", "candidate_expression": "((Absence of informed consent) AND (Admission) AND (Age) AND (CPFA) AND (Estimated life expectancy) AND (Pregnancy) AND (an other ICU) AND (for more than 24 hours) AND (less than 14 years) AND (less than 90 days) AND (patient remained) AND ((absolute contraindications) OR (relative contraindications)))"}
{"candidate_id": "LLM05561", "doc_id": "NCT02609425_exc", "case_bucket": "or", "source_criterion": "Any patient with esophageal cancer who is not deemed a surgical candidate or who is not deemed a candidate for the Ivor Lewis technique of esophagectomy (with intrathoracic anastomosis). Any patient less than 18 years of age", "candidate_expression": "((age less than 18 years) AND (esophageal cancer) AND (esophagectomy Ivor Lewis technique with intrathoracic anastomosis) AND (intrathoracic anastomosis) AND (surgical) AND NOT (candidate))"}
{"candidate_id": "LLM05562", "doc_id": "NCT03351608_inc", "case_bucket": "or", "source_criterion": "Be categorized as American Society of Anesthesiologists (ASA) Physical Status Class 1, 2, or 3. Have a planned non-emergent surgical procedure or clinical situation (e.g., intubation) that requires moderate or deep NMB with either rocuronium or vecuronium. Have a planned surgical procedure or clinical situation that would allow objective neuromuscular monitoring techniques to be applied with access to the arm for neuromuscular transmission monitoring. Age between 2 to <17 years at Visit 2. If female, may participate if she is not pregnant, not breastfeeding, and at least one of the following: 1) Not a woman of childbearing potential (WOCBP); or 2) A WOCBP who agrees to follow the study contraceptive guidance during the treatment period and for at least 7 days after the last dose of study treatment.", "candidate_expression": "((Age between 2 to <17 years at Visit 2) AND (American Society of Anesthesiologists (ASA) Physical Status Class) AND (NMB) AND (WOCBP) AND (clinical situation) AND (contraceptive guidance) AND (female) AND (intubation) AND (objective neuromuscular monitoring techniques) AND (surgical procedure planned non-emergent) AND NOT (pregnant) AND NOT (breastfeeding) AND NOT (woman of childbearing potential (WOCBP)) AND ((deep) OR (moderate)) AND ((rocuronium) OR (vecuronium)) AND ((1) OR (2) OR (3)) AND ((clinical situation) OR (surgical procedure planned)) AND ((during the treatment period the treatment period) OR (for at least 7 days after the last dose of study treatment the last dose of study treatment)))"}
{"candidate_id": "LLM05563", "doc_id": "NCT02186600_inc", "case_bucket": "other", "source_criterion": "Women who are in their first 5 years of menopause Have a T score between -1 and -2.49 at the femoral neck, total hip, or L1-L4 spine Be 19 years of age or older Have their health care provider's permission to enroll in the study.", "candidate_expression": "((T score between -1 and -2.49 femoral neck total hip L1-L4 spine) AND (Women n their first 5 years of menopause) AND (age 19 years of age or older) AND (menopause menopause))"}
{"candidate_id": "LLM05564", "doc_id": "NCT02951520_exc", "case_bucket": "other", "source_criterion": "BMI > 30 kg.m-2, ASA physical state >II Allergy to the used local anesthetics Infection at the injection site age <18y", "candidate_expression": "((ASA physical state >II) AND (Allergy) AND (BMI > 30 kg.m-2) AND (Infection injection site) AND (age <18y) AND (local anesthetics))"}
{"candidate_id": "LLM05565", "doc_id": "NCT00236340_exc", "case_bucket": "other", "source_criterion": "Multiple pregnancy (more than 3 fetuses) Maternal history of placental abruptio Fetus with IUGR Pregnancy complicated with pre-eclampsia Unability to give informed consent", "candidate_expression": "((Fetus) AND (IUGR) AND (Maternal history of) AND (Multiple pregnancy) AND (Pregnancy) AND (Unability to) AND (fetuses) AND (give informed consent) AND (more than 3) AND (placental abruptio) AND (pre-eclampsia))"}
{"candidate_id": "LLM05566", "doc_id": "NCT02101554_exc", "case_bucket": "or", "source_criterion": "Columbia-Suicide Severity Rating Scale (C-SSRS) for suicidal ideation and behavior in past year. Hypersensitivity to morphine, naltrexone. A life expectancy (assessed by investigator) of less than 6 months or is no longer capable of taking medication orally. Undergone surgery within 3 days prior to the first day of dosing.", "candidate_expression": "((C-SSRS) AND (Columbia-Suicide Severity Rating Scale) AND (Hypersensitivity) AND (life expectancy less than 6 months) AND (morphine) AND (naltrexone) AND (suicidal behavior) AND (suicidal ideation) AND (surgery within 3 days prior to the first day of dosing))"}
{"candidate_id": "LLM05567", "doc_id": "NCT02810704_exc", "case_bucket": "or", "source_criterion": "Patients undergoing bilateral hip or knee replacement; Patients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement; Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban; Patients who have a contraindication to two or more of the three study prophylaxis regimens; Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery; Patients on chronic (longer than the prior 6 months) anticoagulation other than with antiplatelet medications; Patients with documented gastrointestinal, cerebral, or other hemorrhage within 3 months of the operation; Patients with a known diagnosis of defective hemostasis and past history of clinical bleeding requiring transfusion and treatment; Patients who have had an operative procedure involving the eye, ear, or central nervous system within one month; Patients with severe uncontrolled hypertension with systolic BP > 220mmHg or diastolic BP > 120mmHg; Patients with an absolute body weight of less than 41 kilograms (90.4 lbs) at baseline visit; Vulnerable patient populations including prisoners and institutionalized individuals.", "candidate_expression": "((90.4 lbs) AND (> 120mmHg) AND (> 220mmHg) AND (Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban) AND (Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery) AND (anticoagulation) AND (antiplatelet) AND (atients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement;) AND (bilateral) AND (bleeding) AND (body weight) AND (central nervous system) AND (cerebral hemorrhage) AND (contraindication) AND (defective) AND (diastolic BP) AND (ear) AND (eye) AND (gastrointestinal hemorrhage) AND (hemorrhage) AND (hemostasis) AND (hip replacement) AND (hypertension) AND (institutionalized) AND (knee replacement) AND (less than 41 kilograms) AND (longer than the prior 6 months) AND (operation) AND (operative procedure) AND (other than) AND (prisoners) AND (severe) AND (systolic BP) AND (total hip replacement) AND (total knee replacement) AND (transfusion) AND (treatment) AND (uncontrolled) AND (within 3 months of the operation) AND (within one month))"}
{"candidate_id": "LLM05568", "doc_id": "NCT02714725_exc", "case_bucket": "or", "source_criterion": "Patient refusal. Emergency surgeries Redo surgeries Pregnancy Vasculitis Inflammation or infection at the study site History of allergic reaction to study medications", "candidate_expression": "((Emergency surgeries) AND (Patient refusal) AND (Pregnancy) AND (Redo surgeries) AND (Vasculitis) AND (allergic) AND (study site) AND ((Inflammation) OR (infection)))"}
{"candidate_id": "LLM05569", "doc_id": "NCT02299947_inc", "case_bucket": "other", "source_criterion": "Elective surgery for thoracic aneurysm", "candidate_expression": "((Elective surgery) AND (thoracic aneurysm))"}
{"candidate_id": "LLM05570", "doc_id": "NCT02370069_inc", "case_bucket": "or", "source_criterion": "Males and females of 18 years of age or older at the time of the vaccination Severe chronic kidney disease (Stage 4 and 5)", "candidate_expression": "((age 18 years or older at the time of the vaccination) AND (chronic kidney disease Severe) AND (vaccination) AND ((Males) OR (females)) AND ((Stage 4 chronic kidney disease) OR (Stage 5 chronic kidney disease)))"}
{"candidate_id": "LLM05571", "doc_id": "NCT01963754_exc", "case_bucket": "or", "source_criterion": "If smoking and/or other drug addiction is present If local anesthetic allergy is present Patient subjected to chemical or radiotherapy if Hepatic disease is present If immunodepression is present If Pregnancy is present If Diabetes is present If Heart disease is present", "candidate_expression": "((Diabetes) AND (Heart disease) AND (Hepatic disease) AND (Pregnancy) AND (allergy) AND (chemical) AND (drug addiction) AND (immunodepression) AND (local anesthetic) AND (radiotherapy) AND (smoking))"}
{"candidate_id": "LLM05572", "doc_id": "NCT02743598_inc", "case_bucket": "other", "source_criterion": "HIV controlled on therapy for at least 12 weeks Viral load < 200 copies BMI >27 to 45 Diagnosis of DM type 2 with A1-C >7 to 15 Participants must be willing to comply with all study related procedures", "candidate_expression": "((< 200 copies) AND (>27 to 45) AND (>7 to 15) AND (A1-C) AND (BMI) AND (DM type 2) AND (HIV) AND (Participants must be willing to comply with all study related procedures) AND (Viral load) AND (at least 12 weeks) AND (controlled))"}
{"candidate_id": "LLM05573", "doc_id": "NCT03018171_exc", "case_bucket": "or", "source_criterion": "Suspect or certainty of fetal malformation, Presence of conditions such as preeclampsia, multiparity, preterm labor History of adverse reaction to a-2 adrenergic agonists Nicotine addiction Chronic use of opioid", "candidate_expression": "((Nicotine addiction) AND (a-2 adrenergic agonists) AND (adverse reaction) AND (fetal malformation) AND (opioi Chronic use) AND ((Suspect) OR (certainty)) AND ((multiparity) OR (preeclampsia) OR (preterm labor)))"}
{"candidate_id": "LLM05574", "doc_id": "NCT02283905_inc", "case_bucket": "scope", "source_criterion": "All adult patients 18 years of age or older admitted to the intensive care units of St. Boniface General Hospital with a diagnosis of acute pulmonary blastomycosis requiring mechanical ventilation.", "candidate_expression": "((St. Boniface General Hospital) AND (acute pulmonary blastomycosis) AND (admitted) AND (adult) AND (age 18 years or older) AND (intensive care units) AND (mechanical ventilation))"}
{"candidate_id": "LLM05575", "doc_id": "NCT02316886_inc", "case_bucket": "or", "source_criterion": "Age 18 years or older Symptomatic or asymptomatic coronary artery disease patients MLA(minimal luminal area)<4mm2 plaque burden>70% Lipid-rich plaque on NIRS(Intracoronary Near-Infrared Spectroscopy) (defined as maxLCBI4mm>315) 2 target vulnerable lesions Eligible for percutaneous coronary intervention with Absorb Bioresorbable Vascular Scaffold or Everolimus Eluting Stent Willing and able to provide informed written consent Reference vessel diameter 2.75-4.0 Lesion length = 40", "candidate_expression": "((Age 18 years or older) AND (Intracoronary Near-Infrared Spectroscopy) AND (Lesion length = 40) AND (Lipid-rich plaque) AND (MLA <4mm2) AND (NIRS) AND (Reference vessel diameter 2.75-4.0) AND (Willing and able to provide informed written consent) AND (coronary artery disease) AND (maxLCBI4mm >315) AND (minimal luminal area) AND (percutaneous coronary intervention Eligible for) AND (plaque burden >70%) AND (target vulnerable lesions 2) AND ((Absorb Bioresorbable Vascular Scaffold) OR (Everolimus Eluting Stent)) AND ((Symptomatic) OR (asymptomatic)))"}
```
