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
{"candidate_id": "LLM07626", "doc_id": "NCT03249272_exc", "case_bucket": "or", "source_criterion": "Decompensated heart failure or hemodynamic instability Prior coronary revascularization (PCI or CABG) or myocardial infarction (as evidenced by previously elevated CPK-MB or troponin levels) Accelerating angina or unstable angina Inability to physically tolerate MRI or implanted objects that are MRI incompatible Inability to provide written informed consent obtained at time of study enrollment. Severe claustrophobia Advanced heart block or sinus node dysfunction Hypersensitivity or allergic reaction to regadenoson or adenosine Hypotension Active bronchospasm or history of hospitalization due to bronchospasm History of seizures Recent cerebrovascular accident Use of dipyridamole within the last 5 days Contraindication to aminophylline Severe renal insufficiency with estimated glomerular filtration rate <30 ml/min/ 1.73 m2 Pregnant or nursing", "candidate_expression": "((<30 ml/min/ 1.73 m2) AND (Active) AND (Advanced) AND (Contraindication) AND (Decompensated) AND (History) AND (Hypotension) AND (Inability to physically tolerate) AND (Inability to provide written informed consent obtained at time of study enrollment.) AND (MRI incompatible) AND (Prior) AND (Recent) AND (Severe) AND (aminophylline) AND (bronchospasm) AND (cerebrovascular accident) AND (claustrophobia) AND (dipyridamole) AND (elevated) AND (estimated glomerular filtration rate) AND (history) AND (previously) AND (renal insufficiency) AND (seizures) AND (within the last 5 days) AND ((Accelerating angina) OR (unstable angina)) AND ((MRI) OR (implanted objects)) AND ((heart failure) OR (hemodynamic instability)) AND ((heart block) OR (sinus node dysfunction)) AND ((Hypersensitivity) OR (allergic)) AND ((adenosine) OR (regadenoson)) AND ((bronchospasm) OR (hospitalization)) AND ((coronary revascularization) OR (myocardial infarction)) AND ((Pregnant) OR (nursing)) AND ((CABG) OR (PCI)) AND ((CPK-MB levels) OR (troponin levels)))"}
{"candidate_id": "LLM07627", "doc_id": "NCT02833623_inc", "case_bucket": "or", "source_criterion": "outpatients aged 18-70 years confirmed diagnosis of H. pylori infection by at least one of the following methods: 13C-urea breath test, histology, rapid urease test or bacterial culture an intention of H. pylori eradication treatment and have written inform consent ability to read short messages on the mobile phone", "candidate_expression": "((H. pylori infection) AND (ability to read short messages on the mobile phone) AND (aged 18-70 years) AND (an intention of H. pylori eradication treatment and have written inform consent) AND (outpatients) AND ((13C-urea breath test) OR (bacterial culture) OR (histology) OR (rapid urease test)))"}
{"candidate_id": "LLM07628", "doc_id": "NCT02015923_exc", "case_bucket": "or", "source_criterion": "Cases of rectal tumours below 12cm from anal verge, or locally advanced tumours invading blood vessels, nerves or bone. Multiple bone metastasis or central nervous system metastasis Other neoplastic disease in the 5 previous years, except squamous or basal cell skin carcinoma or cervical \"in situ\" carcinoma Significant heart disease (chronic congestive heart failure, symptomatic coronary disease) or myocardial infarction in the previous 6 months Peripheral neuropathy Patients who do not give informed consent", "candidate_expression": "((Peripheral neuropathy) AND (heart disease Significant) AND (myocardial infarction in the previous 6 months) AND (neoplastic disease Other in the 5 previous years) AND ((basal cell skin carcinoma) OR (cervical \"in situ\" carcinoma) OR (squamous cell skin carcinoma)) AND ((chronic congestive heart failure) OR (symptomatic coronary disease)) AND ((locally advanced tumours) OR (rectal tumours below 12cm from anal verge)) AND ((bone invading) OR (invading blood vessels) OR (nerves invading)) AND ((Multiple bone metastasis) OR (central nervous system metastasis)))"}
{"candidate_id": "LLM07629", "doc_id": "NCT02546856_inc", "case_bucket": "other", "source_criterion": "Patient with \"de novo\" heart Failure and LVEF <= 40% admitted in hospital, without contraindications for BB prescription with cardiologist up-titration prescription and without having achieved BB target dose previous discharge and signing informed consent.", "candidate_expression": "((BB) AND (LVEF <= 40%) AND (admitted) AND (heart Failure de novo) AND (hospital) AND NOT (contraindications))"}
{"candidate_id": "LLM07630", "doc_id": "NCT02348918_exc", "case_bucket": "or", "source_criterion": "Active proliferative diabetic retinopathy (PDR) in the study eye such as NVE, NVD, vitreous hemorrhage, or neovascular glaucoma. Uncontrolled hypertension defined as systolic >180 mmHg or > 160 mmHg on 2 consecutive measurements or diastolic > 100 mmHg on optimal medical regimen Screening HgA1c blood test > 10.0 Focal laser photocoagulation or intravitreal/periocular steroids of any type in the study eye within the last 90 days prior to study enrollment. A history of intravitreal anti-VEGF injection of any type in the study eye within the last 45 days prior to study enrollment. History of rhegmatogenous retinal detachment, retinal tear(s), or traction retinal detachments in the study eye. Epiretinal membrane and/or vitreomacular traction in the study eye as determined by the central reading center. Previous pars plana vitrectomy in the study eye Any intraocular surgery in the study eye within the last 90 days prior to study enrollment. YAG laser treatment in the study eye in last 30 days prior to study enrollment. High myopia in the study eye, with a spherical equivalent of >8.00D at screening Other ocular pathologies that in the investigator's opinion would interfere with the subject's vision in the study eye. Chronic or recurrent uveitis. Ongoing ocular infection or inflammation in either eye. A history of cataract surgery complications/vitreous loss in the study eye. Congenital eye malformations in the study eye. A history of penetrating ocular trauma in the study eye. Mentally handicapped. Pregnant female, as determined for women less than 60 years old by a positive urine pregnancy test during the screening window. Nursing female. Currently participating in any other clinical research study. Contraindication to the study medication.", "candidate_expression": "((Active proliferative diabetic retinopathy (PDR) in the study eye) AND (Congenital eye malformations in the study eye) AND (Contraindication) AND (Currently participating in any other clinical research study.) AND (Epiretinal membrane traction) AND (Focal laser photocoagulation) AND (HgA1c blood test Screening > 10.0) AND (High myopia in the study eye at screening) AND (Mentally handicapped) AND (NVD) AND (NVE) AND (Nursing) AND (Pregnant) AND (Uncontrolled hypertension) AND (YAG laser treatment in the study eye in last 30 days prior to study enrollment) AND (anti-VEGF injection history of intravitreal in the study eye within the last 45 days prior to study enrollment) AND (cataract surgery) AND (cataract surgery complications) AND (diastolic > 100 mmHg on optimal medical regimen) AND (female) AND (intraocular surgery in the study eye within the last 90 days prior to study enrollment) AND (intravitreal/periocular steroids) AND (neovascular glaucoma) AND (ocular infection) AND (ocular inflammation in either eye) AND (ocular pathologies Other would interfere with the subject's vision in the study eye) AND (old less than 60 years) AND (optimal medical regimen) AND (pars plana vitrectomy Previous in the study eye) AND (penetrating ocular trauma history of in the study eye) AND (retinal tear(s)) AND (rhegmatogenous retinal detachment) AND (spherical equivalent >8.00D) AND (study medication) AND (systolic >180 mmHg > 160 mmHg) AND (traction retinal detachments) AND (urine pregnancy test positive during the screening window) AND (uveitis Chronic recurrent Ongoing) AND (vitreomacular traction) AND (vitreous hemorrhage) AND (vitreous loss) AND (women))"}
{"candidate_id": "LLM07631", "doc_id": "NCT01709981_inc", "case_bucket": "other", "source_criterion": "Patients must be more than 18 years of age and referred for coronary angiography", "candidate_expression": "((age) AND (coronary angiography) AND (more than 18 years) AND (referred for))"}
{"candidate_id": "LLM07632", "doc_id": "NCT02926989_inc", "case_bucket": "other", "source_criterion": "Acutely ill hospitalised children Need for intravenous fluid therapy", "candidate_expression": "((Acutely ill) AND (Need for) AND (children) AND (hospitalised) AND (intravenous fluid therapy))"}
{"candidate_id": "LLM07633", "doc_id": "NCT01850147_exc", "case_bucket": "or", "source_criterion": "Pre-existing hemoptysis of a severity > grade 3 by NCI CTCAE criteria within 4 weeks prior to study entry Uncontrolled hypertension CHF, angina or arrhythmias LVEF < 1 UNL Existing a second malignancy within 5 years Infected with HIV", "candidate_expression": "((< 1 UNL) AND (> grade 3) AND (HIV) AND (LVEF) AND (NCI CTCAE criteria) AND (Uncontrolled) AND (hemoptysis) AND (hypertension) AND (second malignancy) AND (severity) AND (study entry) AND (within 4 weeks prior to study entry) AND (within 5 years) AND ((CHF) OR (angina) OR (arrhythmias)))"}
{"candidate_id": "LLM07634", "doc_id": "NCT03631355_inc", "case_bucket": "other", "source_criterion": "Patients undergoing a high tibial osteotomy (HTO) Patients undergoing tibial tubercle osteotomy (TTO) with or without medial patello-femoral ligament (MPFL) reconstruction", "candidate_expression": "((high tibial osteotomy (HTO) undergoing) AND (medial patello-femoral ligament (MPFL) reconstruction) AND (tibial tubercle osteotomy (TTO) undergoing))"}
{"candidate_id": "LLM07635", "doc_id": "NCT03058835_exc", "case_bucket": "or", "source_criterion": "Active alcohol or drug use or dependence which may interfere with adherence to study requirements HIV-infected at screening or enrollment Estimated CrCl < 60 mL/min Past participation in an HIV vaccine study Positive Hepatitis B surface antigen test Underlying medical condition with survival unlikely during follow-up period Any condition that in the opinion of study staff would make participation in the study unsafe or interfere with achieving study objectives Pregnant or breast feeding Actively trying to achieve pregnancy", "candidate_expression": "((< 60 mL/min) AND (Active alcohol or drug use or dependence which may interfere with adherence to study requirements) AND (Actively trying to achieve pregnanc) AND (Estimated CrCl) AND (HIV-infected) AND (Hepatitis B surface antigen test) AND (Positive) AND (condition) AND (medical condition) AND (survival unlikely) AND ((Pregnant) OR (breast feeding)) AND ((interfere with achieving study objectives) OR (make participation in the study unsafe)) AND ((at enrollment) OR (at screening)))"}
{"candidate_id": "LLM07636", "doc_id": "NCT02477280_inc", "case_bucket": "other", "source_criterion": "18 years old or older. ADHD is diagnosed according to Diagnostic and Statistical Manual of Mental Disorders, fifth edition (DSM-5 criteria). Substance Use Disorder is diagnosed according to DSM-5 criteria. Qb-score 1.3 or higher on at least one of the weighted summary parameters QbActivity, QbInattention or QbImpulsivity on the QbTest. Participants are given their written informed consent to participate in the study.", "candidate_expression": "((1.3 or higher) AND (18 years or older) AND (ADHD) AND (DSM-5) AND (Participants are given their written informed consent to participate in the study) AND (Qb-score) AND (Substance Use Disorder) AND (old))"}
{"candidate_id": "LLM07637", "doc_id": "NCT02833116_inc", "case_bucket": "or", "source_criterion": "Unilateral leg pain secondary to lateral stenosis, disc protrusion or herniated disc. Age between 18 and 80 years. Moderate to severe pain (NVS>4). Right proficient oral and written language.", "candidate_expression": "((Age between 18 and 80 years) AND (NVS >4)) AND (Right proficient oral and written language) AND (Unilateral leg pain) AND (pain) AND ((Moderate) OR (severe)) AND ((disc protrusion) OR (herniated disc) OR (lateral stenosis)))"}
{"candidate_id": "LLM07638", "doc_id": "NCT02322203_exc", "case_bucket": "or", "source_criterion": "Subjects taking any lipid modification therapy, including but not limited to statins, fibrates and bile acid sequestrants. Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study. Subjects with acute liver disease or active peptic ulcer disease. Subjects with elevated uric acid levels greater than 10 mg/dL or gout Pregnancy or women currently breastfeeding. Female subjects taking hormonal contraceptives or hormone replacement therapy may be included in this study only if they have been on a stable dose for at least 3 months. BMI less than 18.5 Subjects with weight that varies greater than 20% over the past 3 months. Subjects taking the following medications for at least six weeks, which may interfere with the study, will be excluded: BAS, antibiotics, anticoagulants, anticonvulsants, antiarrhythmic, Cyclosporine, Mycophenolate and Synthroid. Subjects with chronic diarrhea, gastric bypass or lap band procedures, ostomies, bowel motility problems, or other conditions that could affect intestinal fat absorption. Subjects initiating new medications or patients on multiple medications may also be excluded. Inability to swallow capsules Patients with a history of type I or type II diabetes or HbA1c greater than 6.5%. Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.", "candidate_expression": "((BAS) AND (BMI) AND (Cyclosporine) AND (Female) AND (HbA1c) AND (Inability to swallow capsules) AND (Mycophenolate) AND (Pregnancy) AND (Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study.) AND (Synthroid) AND (Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.) AND (active) AND (acute liver disease) AND (antiarrhythmic) AND (antibiotics) AND (anticoagulants) AND (anticonvulsants) AND (bile acid sequestrants) AND (bowel motility problems) AND (breastfeeding) AND (chronic diarrhea) AND (conditions that could affect intestinal fat absorption) AND (elevated) AND (fibrates) AND (fish oil) AND (for at least 3 months) AND (for at least six weeks) AND (gastric bypass) AND (gout) AND (greater than 10 mg/dL) AND (greater than 6.5%) AND (history) AND (hormonal contraceptives) AND (hormone replacement therapy) AND (lap band procedures) AND (less than 18.5) AND (lipid modification therapy) AND (ostomies) AND (over the past 3 months) AND (peptic ulcer disease) AND (stable dose) AND (statins) AND (type I diabetes) AND (type II diabetes) AND (uric acid levels) AND (varies greater than 20%) AND (weight) AND (women))"}
{"candidate_id": "LLM07639", "doc_id": "NCT03275584_exc", "case_bucket": "or", "source_criterion": "Pregnant women Claustrophobic patient unable to undergo the examination Breastfeeding women unwilling to temporarily stop breastfeeding Patient with contra-indication to: dipyridamole, aminophylline, dobutamine or exercise stress test (depending on the method of cardiovascular stress test chosen)", "candidate_expression": "((Claustrophobic) AND (Pregnant) AND (contra-indication) AND (examination) AND (unable) AND (women) AND ((aminophylline) OR (dipyridamole) OR (dobutamine) OR (exercise stress test)))"}
{"candidate_id": "LLM07640", "doc_id": "NCT03536520_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((40-75 yr) AND (Healthy) AND (Written informed consent) AND (age) AND (any) AND (disease) AND (medication) AND (men) AND (without) AND (women))"}
{"candidate_id": "LLM07641", "doc_id": "NCT01846507_inc", "case_bucket": "or", "source_criterion": "1. Menstruating females 10-19 years of age 2. Non-smoker 3. Physician and patient have agreed to initiate Lysteda 4. Diagnosis of HMB based on the medical judgment of the principal or site investigator 5. Subjects must report menstrual periods occurring within 21-60 days from the start of one period to the start of the next menstrual period 6. Negative pregnancy test 7. Informed consent obtained and signed 8. Informed assent obtained and signed 9. Understanding of study procedures 10. Ability to comply with study procedures for the entire length of the study 11. Subjects should be either sexually inactive (abstinent) or agree to use a barrier method with spermicide in the event of sexual activity throughout the study period", "candidate_expression": "((10-19 years) AND (Ability to comply with study procedures for the entire length of the study) AND (HMB) AND (Informed assent obtained and signed) AND (Informed consent obtained and signed) AND (Lysteda) AND (Menstruating) AND (Negative) AND (Non-smoker) AND (Understanding of study procedures) AND (age) AND (agree to use) AND (based on the medical judgment of the principal or site investigator) AND (females) AND (menstrual periods) AND (pregnancy test) AND (sexually abstinent) AND (the start of one period) AND (within 21-60 days from the start of one period) AND ((barrier method with spermicide) OR (sexually inactive)))"}
{"candidate_id": "LLM07642", "doc_id": "NCT02959801_inc", "case_bucket": "other", "source_criterion": "proven acute deep venous thrombosis, less than 21 days and who were referred to the interventional radiology department.", "candidate_expression": "((deep venous thrombosis proven acute less than 21 days) AND (interventional radiology department referred to))"}
{"candidate_id": "LLM07643", "doc_id": "NCT02732080_exc", "case_bucket": "or", "source_criterion": "Recanalized (TIMI I-III flow) IRA at coronary angiography. Patients in whom TIMI-3 flow was not able to be established after wire crossing, balloon angioplasty or thrombectomy. STEMI due to bypass-graft occlusion Severe heart failure or cardiogenic shock", "candidate_expression": "((IRA) AND (Recanalized TIMI I-III flow) AND (STEMI) AND (bypass-graft) AND (cardiogenic shock) AND (coronary angiography) AND (heart failure) AND (occlusion))"}
{"candidate_id": "LLM07644", "doc_id": "NCT03430284_inc", "case_bucket": "other", "source_criterion": "35-75 years old; diagnosed as type 2 diabetes according to the criteria of the World Health Organization in 1999.", "candidate_expression": "((35-75 years old) AND (criteria of the World Health Organization in 1999) AND (old) AND (type 2 diabetes))"}
{"candidate_id": "LLM07645", "doc_id": "NCT01942109_exc", "case_bucket": "other", "source_criterion": "uncontrolled hypertension uncontrolled diabetes creatinine > 2,5 mg/dl potassium > 6 mg/dl acute coronary syndrome hypertrophic cardiomyopathy", "candidate_expression": "((> 2,5 mg/dl) AND (> 6 mg/dl) AND (acute coronary syndrome) AND (creatinine) AND (diabetes) AND (hypertension) AND (hypertrophic cardiomyopathy) AND (potassium) AND (uncontrolled))"}
{"candidate_id": "LLM07646", "doc_id": "NCT01944800_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07647", "doc_id": "NCT02566928_inc", "case_bucket": "or", "source_criterion": "between 7 to 70 years of age fluent in English or Spanish plans to receive care in the Community Health Center during the next year presents with signs and symptoms of a SSTI willing/able to provide informed consent", "candidate_expression": "((Community Health Center) AND (SSTI) AND (age) AND (between 7 to 70 years) AND (during the next year) AND (fluent in English) AND (fluent in Spanish) AND (plans to) AND (receive care) AND (willing/able to provide informed consent) AND ((signs) OR (symptoms)))"}
{"candidate_id": "LLM07648", "doc_id": "NCT03059069_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes, Secondary diabetes, gestational diabetes Ongoing dementia treatment or anti-depressive disorder medication Uncontrolled psychiatric disorder BDI = 30 points Heavy alcoholics Underlying chronic liver disease (hemochromatosis, liver cell carcinoma, autoimmune liver disease, liver cirrhosis, chronic viral hepatitis) Allergy or hypersensitivity to target medication or any of its components Renal failure, moderate or severe renal impairment (estimated glomerular filtration rate < 30 mL/min/1.73 m2), or ongoing dialysis Abnormal liver function (AST/ALT > x3 upper normal limit) History of alcohol or drug abuse in the previous 3 months Premenopausal women who are nursing or pregnant Human immunodeficiency virus (HIV) or human immunodeficiency virus (AIDS) chronic pancreatitis or pancreatic cancer", "candidate_expression": "((AST/ALT > x3 upper normal limit) AND (Allergy) AND (BDI = 30 points) AND (Human immunodeficiency virus (HIV)) AND (Premenopausal) AND (Renal failure moderate severe) AND (Secondary diabetes) AND (Type 1 diabetes) AND (alcohol abuse) AND (alcoholics Heavy) AND (anti-depressive disorder medication Uncontrolled) AND (autoimmune liver disease) AND (chronic liver disease) AND (chronic pancreatitis) AND (chronic viral hepatitis) AND (dementia) AND (dialysis ongoing) AND (drug abuse) AND (estimated glomerular filtration rate < 30 mL/min/1.73 m2) AND (gestational diabetes) AND (hemochromatosis) AND (human immunodeficiency virus (AIDS)) AND (hypersensitivity) AND (liver cell carcinoma) AND (liver cirrhosis) AND (liver function Abnormal) AND (nursing) AND (pancreatic cancer) AND (pregnant) AND (renal impairment) AND (target medication) AND (treatment Ongoing) AND (women))"}
{"candidate_id": "LLM07649", "doc_id": "NCT03445949_inc", "case_bucket": "scope", "source_criterion": "successful left atrial appendage occlusion with Amulet device within 37 days prior to randomization. treatment with dual antiplatelet therapy (clopidogrel and acetylsalicylic acid) between left atrial appendage closure and randomization participant's age 18 years or older at the time of signing the informed consent form participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable participant is willing to sign the study informed consent form", "candidate_expression": "((Amulet device) AND (acetylsalicylic acid between left atrial appendage closure and randomization left atrial appendage closure) AND (age 18 years or older at the time of signing the informed consent form) AND (clopidogrel) AND (dual antiplatelet therapy) AND (left atrial appendage closure randomization) AND (left atrial appendage occlusion successful within 37 days prior to randomization) AND (participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable) AND (participant is willing to sign the study informed consent form))"}
{"candidate_id": "LLM07650", "doc_id": "NCT02844907_inc", "case_bucket": "or", "source_criterion": "Body Mass Index (BMI) = 35 kg/m2 HbA1c = 5.7% Ability to speak and understand English", "candidate_expression": "((Ability to speak English) AND (Ability to understand English) AND (Body Mass Index (BMI) = 35 kg/m2) AND (HbA1c = 5.7%))"}
```
