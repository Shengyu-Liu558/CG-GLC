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
{"candidate_id": "LLM07276", "doc_id": "NCT02604459_inc", "case_bucket": "other", "source_criterion": "Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board, Hip fracture surgery scheduled under general anesthesia Subject is 65 years or older on the day of surgery", "candidate_expression": "((65 years or older) AND (Hip fracture surgery) AND (Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board,) AND (general anesthesia) AND (older) AND (on the day of surgery) AND (surgery) AND (the day of surgery))"}
{"candidate_id": "LLM07277", "doc_id": "NCT03228498_inc", "case_bucket": "or", "source_criterion": "1. Cognitive impairment from mild to moderate degree defined by a Clinical Deterioration Rating (CDR) score range between 0.5 and 2.0. 2. Evidence on brain MRI of white matter hyperintensities (leukoaraiosis of moderate or severe degree according to the modified Fazekas visual scale and/or presence of lacunar infarcts). 3. Consent to participation in the study.", "candidate_expression": "((Clinical Deterioration Rating (CDR) score) AND (Cognitive impairment) AND (brain MRI) AND (lacunar infarcts) AND (leukoaraiosis) AND (mild to moderate) AND (moderate or severe degree) AND (modified Fazekas visual scale) AND (range between 0.5 and 2.0) AND (white matter hyperintensities))"}
{"candidate_id": "LLM07278", "doc_id": "NCT03124329_inc", "case_bucket": "or", "source_criterion": "Male and female individuals between ages of 18 to 70 years old Multiple contiguous gingival recession defects on a minimum of two adjacent teeth, exhibiting 3mm or more recession on at least one of those teeth No prior surgical treatment in the sites planned for therapy Minimum of 2 mm of keratinized gingiva Absence of cervical restorations extending to the CEJ Miller class 1, 2 and 3 recession defects will be included Availability to undergo treatment and return for follow up visits at specified post-operative intervals", "candidate_expression": "((3mm or more) AND (Absence) AND (Minimum of 2 mm) AND (Multiple) AND (No) AND (ages) AND (at least one) AND (between 18 to 70 years old) AND (cervical restorations extending to the CEJ) AND (gingival recession defects) AND (keratinized gingiva) AND (minimum of two) AND (recession) AND (recession defects) AND (surgical treatment) AND ((Miller) OR (class 1, 2 and 3)))"}
{"candidate_id": "LLM07279", "doc_id": "NCT03117608_inc", "case_bucket": "or", "source_criterion": "Patients provided written informed consent; Patients aged between 18 and 75 years; Knee symptomatic OA (Kellgren-Lawrence grade 1-4) Failure of conservative treatment for at least 3 months; Patients agreed to actively participate in the rehabilitation protocol and follow-up program; Male or female patients; Women of childbearing age had to use a proven method to prevent pregnancy, before the surgical treatment.", "candidate_expression": "((Kellgren-Lawrence grade 1-4) AND (OA Knee symptomatic) AND (Women) AND (aged between 18 and 75 years) AND (agreed to actively participate in the follow-up program) AND (agreed to actively participate in the rehabilitation protocol) AND (childbearing age) AND (conservative treatment Failure) AND (provided written informed consent) AND (surgical treatment) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07280", "doc_id": "NCT03122119_inc", "case_bucket": "other", "source_criterion": "Diagnosis of sacroiliitis Age 18 to 80 years old Chronic low back pain SI joint pathology is the predominant source of pain Positive Fortin Finger Test (PMT) Joint anatomy is identifiable using ultrasonography Patient has no other comorbidities that contraindicate the procedure Patient has attempted physical therapy and corticosteroid injections with local anesthetic -Previous injections of lidocaine and corticosteroid provided at least minor immediate relief Patient must not have had a corticosteroid injection in the SI joint within the last three months Patient must consent to the procedure", "candidate_expression": "((18 to 80 years) AND (Age) AND (Chronic low back pain) AND (Fortin Finger Test (PMT)) AND (Positive) AND (SI joint) AND (SI joint pathology) AND (comorbidities that contraindicate the procedure) AND (consent to the procedure) AND (corticosteroid injection) AND (corticosteroid injections) AND (no) AND (not) AND (ocal anesthetic) AND (other) AND (physical therapy) AND (sacroiliitis) AND (within the last three months))"}
{"candidate_id": "LLM07281", "doc_id": "NCT02332291_exc", "case_bucket": "or", "source_criterion": "Current or past diagnoses of other Axis I psychiatric disorders, except for generalized anxiety disorder (GAD) symptoms occurring during a depressive episode History of alcohol or drug dependence or abuse in the last three years History of developmental disorder or IQ score < 70 Presence of acute suicidality Acute grief (< 1 month) Current or past psychosis Primary neurological disorder, including but not limited to dementia, stroke, brain tumors, epilepsy, Parkinson's disease, or demyelinating diseases MRI contraindications Any physical or intellectual disability adversely affecting ability to complete assessments Electroconvulsive therapy in last 6 months Use of antidepressant medications or other psychotropic medications in the last 4 weeks (or the last 6 weeks for fluoxetine). Occasional use of benzodiazepines or non-benzodiazepine sedatives (such as zolpidem, eszopiclone, or zaleplon) during this period is allowable. A failed therapeutic trial of escitalopram in the current depressive episode (defined as at least 6 weeks of treatment at a daily dose of 10mg or higher) Known allergy or hypersensitivity to escitalopram or bupropion Current or planned psychotherapy", "candidate_expression": "((< 1 month) AND (< 70) AND (Acute grief) AND (Axis I psychiatric disorders) AND (Current) AND (Electroconvulsive therapy) AND (IQ score) AND (MRI) AND (Occasional use) AND (Parkinson's disease) AND (Primary neurological disorder) AND (acute suicidality) AND (alcohol abuse) AND (alcohol dependence) AND (allergy) AND (antidepressant medications) AND (at least 6 weeks of treatment) AND (benzodiazepines sedatives) AND (brain tumors) AND (bupropion) AND (contraindications) AND (daily dose of 10mg or higher) AND (dementia) AND (demyelinating diseases) AND (depressive episode) AND (developmental disorder) AND (drug abuse) AND (drug dependence) AND (during a depressive episode) AND (epilepsy) AND (escitalopram) AND (eszopiclone) AND (except for) AND (failed) AND (fluoxetine) AND (generalized anxiety disorder (GAD)) AND (hypersensitivity) AND (in last 6 months) AND (in the current depressive episode) AND (in the last 4 weeks) AND (in the last 6 weeks) AND (in the last three years) AND (intellectual disability) AND (is allowable) AND (non-benzodiazepine sedatives) AND (other) AND (past) AND (physical disability) AND (planned) AND (psychosis) AND (psychotherapy) AND (psychotropic medications) AND (stroke) AND (therapeutic trial) AND (zaleplon) AND (zolpidem))"}
{"candidate_id": "LLM07282", "doc_id": "NCT02477280_exc", "case_bucket": "or", "source_criterion": "Affected by alcohol or drugs during the last month. Untreated severe comorbid psychiatric or somatic illness. Bloodpressure 150/95 or higher. Irregular pulse, or pulse 100 or higher. No counter indications according to the Medikinet pill. Concurrent clinical diagnosis that significantly could affect test performance. Concurrent prescription of medicines for ADHD or medicines that significantly could affect test performance.", "candidate_expression": "((ADHD) AND (Bloodpressure 150/95 or higher) AND (alcohol) AND (drugs Untreated severe) AND (illness psychiatric comorbid) AND (medicines) AND (pulse 100 or higher) AND (pulse Irregular) AND (somatic illness))"}
{"candidate_id": "LLM07283", "doc_id": "NCT03387059_inc", "case_bucket": "or", "source_criterion": "All infertile women treated with intracytoplasmic sperm injection (ICSI)/Fertilization in Vitro and Embryo Transfer (FIVET) Less than or equal to (<=) 1 previous failed embryo transfer Eumenorrheic normo-gonadotropic women Basal follicle-stimulating hormone (FSH) <=12 International unit per liter (IU/L) Anti-mullerian hormone (AMH) greater than (>) 1.1 nanogram per milliliter (ng/mL) Ovarian Reserve: number of antral follicles 2 millimeter (mm) between 6 <= antral follicle count (AFC) <= 16 Follicles > 16 mm at the triggering day between 5-14 Body Mass Index (BMI) between 18 <= BMI <= 27 kilogram per meter square (kg/m^2) Indication for Fresh Embryo transfer Normal uterine cavity on ultrasound exam (e.g., no presence of hydrosalpinx) Undergoing Assisted Reproductive Technique (ART) and oocyte maturation by human chorionic gonadotropin (HCG) triggering Progesterone (P4) serum level at the HCG triggering day <= 1.5 ng/mL (Day O/Randomization) Estradiol (E2) <= 3000 picogram/milliliter (pg/mL) at the human chorionic gonadotropin (HCG) triggering day (Day 0/Randomization) Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care Other protocol defined inclusion criteria could apply", "candidate_expression": "((<= 1.5 ng/mL) AND (<= 3000 picogram/milliliter (pg/mL)) AND (<=12 International unit per liter (IU/L)) AND (Anti-mullerian hormone (AMH)) AND (Assisted Reproductive Technique (ART)) AND (Basal follicle-stimulating hormone (FSH)) AND (Body Mass Index (BMI)) AND (Day 0/Randomization) AND (Day O/Randomization) AND (Estradiol (E2)) AND (Eumenorrheic) AND (Follicles > 16 mm) AND (Fresh Embryo transfer) AND (Indication for) AND (Less than or equal to (<=) 1) AND (Normal uterine cavity) AND (Progesterone (P4) serum level) AND (Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care) AND (Undergoing) AND (at the HCG triggering day) AND (at the human chorionic gonadotropin (HCG) triggering day) AND (at the triggering day) AND (between 18 <= BMI <= 27 kilogram per meter square (kg/m^2)) AND (between 5-14) AND (between 6 <= antral follicle count (AFC) <= 16) AND (greater than (>) 1.1 nanogram per milliliter (ng/mL)) AND (human chorionic gonadotropin (HCG) triggering) AND (hydrosalpinx) AND (infertile) AND (no presence of) AND (normo-gonadotropic) AND (number of antral follicles 2 millimeter (mm)) AND (oocyte maturation) AND (previous failed embryo transfer) AND (the HCG triggering day) AND (the human chorionic gonadotropin (HCG) triggering day) AND (ultrasound exam) AND (women) AND ((Fertilization in Vitro and Embryo Transfer (FIVET)) OR (intracytoplasmic sperm injection (ICSI))))"}
{"candidate_id": "LLM07284", "doc_id": "NCT02968342_inc", "case_bucket": "other", "source_criterion": "Menopausal status Sexually active", "candidate_expression": "((Menopausal) AND (Sexually active))"}
{"candidate_id": "LLM07285", "doc_id": "NCT02966236_inc", "case_bucket": "scope", "source_criterion": "Complex kidney stone (staghorn calculi GUYS III and IV)", "candidate_expression": "((Complex kidney stone) AND (GUYS) AND (III and IV) AND (staghorn calculi))"}
{"candidate_id": "LLM07286", "doc_id": "NCT03297125_inc", "case_bucket": "other", "source_criterion": "Newly diagnosed glioblastoma (GBM), WHO grade IV.", "candidate_expression": "((GBM) AND (Newly diagnosed) AND (WHO) AND (glioblastoma) AND (grade IV))"}
{"candidate_id": "LLM07287", "doc_id": "NCT01907230_inc", "case_bucket": "or", "source_criterion": "Age : from 20 to 90 y/o. HBsAg-positive for more than 6 months and HBV DNA < 2000 IU/ml (Subgroup 1)or HBsAg-negative but anti-HBc positive with HBV DNA < 2000 IU/ml (Subgroup 2). Inflammatory arthritis patients who plan to treat with biological agents, including Humira or Enbrel or Simponi or Orencia or Mabthera or Actemra; as first line biologic treatment is indicated.", "candidate_expression": "((20 to 90 y/o) AND (< 2000 IU/ml) AND (Age) AND (HBV DNA) AND (HBsAg) AND (Inflammatory arthritis) AND (anti-HBc) AND (biological agents) AND (more than 6 months) AND (negative) AND (positive) AND ((Actemra) OR (Enbrel) OR (Humira) OR (Mabthera) OR (Orencia) OR (Simponi)))"}
{"candidate_id": "LLM07288", "doc_id": "NCT01098383_exc", "case_bucket": "or", "source_criterion": "an underlying infectious disease chromosomal abnormality metabolic disorder specific brain related disorder (such as tuberous sclerosis) history of fetal cytomegalovirus infection birth asphyxia a history of major head injury a chronic use of non-steroidal anti-inflammatory drugs, (NSAID) known brain damage Epilepsy Abnormal Electro-cardiogram (ECG) Epileptiform EEG Use of psychostimulants, anti-depressants, neuroleptics or anti-convulsive agents within the past month. Lack of cooperation in the screening phase", "candidate_expression": "((Abnormal) AND (ECG) AND (EEG) AND (Electro-cardiogram) AND (Epilepsy) AND (Epileptiform) AND (Lack of cooperation in the screening phase) AND (NSAID) AND (anti-convulsive agents) AND (anti-depressants) AND (birth asphyxia) AND (brain) AND (brain damage) AND (chromosomal abnormality) AND (chronic use) AND (cytomegalovirus infection) AND (disorder) AND (fetal) AND (infectious disease) AND (major head injury) AND (metabolic disorder) AND (neuroleptics) AND (non-steroidal anti-inflammatory drugs) AND (psychostimulants) AND (tuberous sclerosis) AND (underlying) AND (within the past month))"}
{"candidate_id": "LLM07289", "doc_id": "NCT01806558_inc", "case_bucket": "or", "source_criterion": "1. Have a finding of a mass lesion on mammography or breast MRI (BIRADS 0, 4 or 5) that is >0.5 cm and < 2 cm in size and has had or will have additional workup with focused ultrasound. 2. Have a finding of a mass lesion on ultrasound (BIRADS 0, 4 or 5) that is > 0.5 cm and < 2 cm in size. 3. Have a positive finding on MBI that is < 2 cm in size and requires additional diagnostic workup with focused ultrasound.", "candidate_expression": "((0, 4 or 5) AND (< 2 cm) AND (> 0.5 cm and < 2 cm) AND (>0.5 cm and < 2 cm) AND (BIRADS) AND (MBI) AND (breast MRI) AND (mammography) AND (mass lesion) AND (positive finding) AND (requires additional diagnostic workup with focused ultrasound) AND (size) AND (ultrasound))"}
{"candidate_id": "LLM07290", "doc_id": "NCT02334722_inc", "case_bucket": "or", "source_criterion": "Adult (>18 years of age and older) patients who have or will have undergone surgical resection or biopsy of a supratentorial brain tumor and are able to consent for themselves. Able to be randomized prior to or up to 48 hours after surgery.", "candidate_expression": "((Adult) AND (age and older >18 years) AND (are able to consent for themselves) AND (biopsy) AND (supratentorial brain tumor) AND (surgical resection))"}
{"candidate_id": "LLM07291", "doc_id": "NCT03212352_inc", "case_bucket": "or", "source_criterion": "a crown-rump length = 6mm and no cardiac activity OR a crown-rump length <6mm and no fetal growth at least one week later OR At least one week after diagnosis OR a discrepancy of at least one week between crown-rump length and calendar gestational age Intra-uterine pregnancy Women aged above 16 years Hemodynamic stable patient No signs of infection No signs of incomplete abortion No contraindications for mifepristone or misoprostol", "candidate_expression": "((Hemodynamic stable) AND (Intra-uterine pregnancy) AND (Women) AND (aged above 16 years) AND (crown-rump length <6mm) AND (crown-rump length = 6mm) AND (discrepancy at least one week between crown-rump length and calendar gestational age) AND (mifepristone) AND (misoprostol) AND NOT (signs of infection) AND NOT (signs of incomplete abortion) AND NOT (cardiac activity) AND NOT (fetal growth))"}
{"candidate_id": "LLM07292", "doc_id": "NCT03140488_exc", "case_bucket": "or", "source_criterion": "Non-reassuring fetal assessment at the time of recruitment Previous cervical ripening agents (cytotec, cervidil, cervical Foley Balloon) <18 years of age Prisoners Any patients contraindicated for vaginal delivery Multiple gestations History of previous cesarean delivery Patients with history of significant cardiac disease Fetal demise Estimated fetal weight greater than 4500 grams in diabetic and 5000 grams in non-diabetic mother Ruptured membranes Spontaneous labor (latent or active phase) Augmentation of labor (latent or active phase)", "candidate_expression": "((Augmentation of labor) AND (Estimated fetal weight) AND (Fetal demise) AND (Multiple gestations) AND (Prisoners) AND (Ruptured membranes) AND (Spontaneous labor) AND (age <18 years) AND (cardiac disease history significant) AND (cervical ripening agents Previous) AND (cesarean delivery History previous) AND (contraindicated) AND (diabetic greater than 4500 grams) AND (fetal assessment Non-reassuring at the time of recruitment) AND (vaginal delivery) AND NOT (diabetic 5000 grams) AND ((active phase) OR (latent phase)) AND ((cervical Foley Balloon) OR (cervidil) OR (cytotec)))"}
{"candidate_id": "LLM07293", "doc_id": "NCT02952365_exc", "case_bucket": "or", "source_criterion": "Subjects under the age of 21. Subjects with excessively thin corneas. Subjects with topographic evidence of keratoconus. Subjects with ectatic eye disorders. Subjects with autoimmune diseases. Subjects who are pregnant or nursing.", "candidate_expression": "((age under the age of 21) AND (autoimmune diseases) AND (ectatic eye disorders) AND (excessively thin corneas) AND (keratoconus) AND (nursing) AND (pregnant) AND (topographic evidence))"}
{"candidate_id": "LLM07294", "doc_id": "NCT03416413_inc", "case_bucket": "or", "source_criterion": "Adults over 18 years of age Symptomatic GSV or SSV vein reflux > 0.5 seconds on colour Duplex Varicose vein tributary requiring treatment", "candidate_expression": "((> 0.5 seconds) AND (Adults) AND (GSV vein reflux) AND (SSV vein reflux) AND (Varicose vein tributary) AND (age) AND (colour Duplex) AND (over 18 years of age) AND (requiring) AND (treatment))"}
{"candidate_id": "LLM07295", "doc_id": "NCT02664558_inc", "case_bucket": "or", "source_criterion": "1. Male or female, 18-75 years old. 2. Has a diagnosis of WHO Group 1 PAH. 3. Right heart catheterization performed at Screening with results that are: 1. Mean pulmonary arterial pressure ≥25 mmHg (at rest) and 2. Pulmonary venous hypertension (measured as pulmonary capillary wedge pressure (PCWP) ≤15 mmHg. If PCWP is not available, then mean left atrial pressure or left ventricular end-diastolic pressure ≤15 mmHg in the absence of left atrial obstruction. and 3. Pulmonary vascular resistance (PVR) ≥300 dyn•s/cm5 (3.75 Wood units) 4. Has WHO/NYHA-FC of II or III. 5. Be on stable dose of at least one of the following PAH-specific therapies: endothelin receptor antagonist, an agent acting on the nitric oxide pathway (phosphodiesterase type 5 inhibitor or soluble guanylate cyclase stimulator), and/or a prostacyclin or prostacyclin analog. 6. Has a 6-minute walk distance that is ≥150 and ≤500 meters. 7. Have a ventilation-perfusion scan that rules out thromboembolic disease.", "candidate_expression": "((1) AND (18-75 years) AND (3.75 Wood units) AND (6-minute walk distance) AND (Mean pulmonary arterial pressure) AND (PAH) AND (PAH-specific therapies) AND (Pulmonary vascular resistance (PVR)) AND (Pulmonary venous hypertension) AND (Right heart catheterization) AND (Screening) AND (WHO Group) AND (WHO/NYHA-FC) AND (absence) AND (at least one) AND (at rest) AND (left atrial obstruction) AND (performed at Screening) AND (pulmonary capillary wedge pressure (PCWP)) AND (rules out) AND (stable dose) AND (thromboembolic disease) AND (ventilation-perfusion scan) AND (years old) AND (≤15 mmHg) AND (≥150 and ≤500 meters) AND (≥25 mmHg) AND (≥300 dyn•s/cm5) AND ((Male) OR (female)) AND ((left ventricular end-diastolic pressure) OR (mean left atrial pressure)) AND ((II) OR (III)) AND ((agent acting on the nitric oxide pathway) OR (endothelin receptor antagonist) OR (prostacyclin analog)) AND ((phosphodiesterase type 5 inhibitor) OR (soluble guanylate cyclase stimulator)))"}
{"candidate_id": "LLM07296", "doc_id": "NCT03532620_exc", "case_bucket": "or", "source_criterion": "Past history of hypersensitivity to the study drug; Diagnosed diabetes; Severe liver disease (including ALT or AST=2.5-fold the normal upper limit), biliary obstruction; Ongoing treatment with cyclosporine within 2 weeks; Renal dysfunction, including endogenous creatinine clearance male<120ml/min, female<105ml/min, serum creatinine=2mg/dl (186umol/L), Renal function progressive decline, GFR<30ml•min-1•1.73m-2; Diagnosed or past history of ASCVD (including ACS, SCAD, revascularization, ICM, ischemic stroke, TIA, PASD, etc. SBP=180mmHg, or DBP=110mmHg; Ongoing treatment with Beta blockers, Diuretic; Secondary hypertension, including SAS, PA, RAS, pheochromocytoma, Cushing's syndrome, aorta diseases, drug induced hypertension; Ongoing treatment with statins, fibrates, and/or cation exchange resins within 2 weeks; Pancreatic disease; History of gastrectomy, short bowel syndrome; Ongoing hormone replacement therapy; Diagnosed or suspected malignant tumor; Familial hypercholesterolemia; Any diseases may limit the efficacy or safety of the study; Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation; IFG impaired fast glucose, FPG fasting plasma glucose, IGT impaired glucose tolerance, OGTT oral glucose tolerance test, PG plasma glucose, HbA1C hemoglobin A1C, LDL-C low-density lipoprotein cholesterol, TG triglycerides, SBP systolic blood pressure, DBP diastolic blood pressure, ALT alanine aminotransferase, AST aspartate aminotransferase, GFR glomerular filtration rate, ASCVD arteriosclerotic cardiovascular disease, ACS acute coronary syndrome, SCAD stable coronary artery disease, ICM ischemic cardiomyopathy, TIA transient ischemic attack, PASD peripheral atherosclerotic disease, SAS sleep apnea syndrome, PA primary aldosteronism, RAS renal arterial stenosis", "candidate_expression": "((186umol/L) AND (<105ml/min) AND (<120ml/min) AND (<30ml•min-1•1.73m-2) AND (=110mmHg) AND (=180mmHg) AND (=2.5-fold the normal upper limit) AND (=2mg/dl) AND (ASCVD) AND (Familial hypercholesterolemia) AND (History) AND (Ongoing) AND (Pancreatic disease) AND (Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation) AND (Renal dysfunction) AND (Secondary hypertension) AND (Severe) AND (biliary obstruction) AND (cyclosporine) AND (diabetes) AND (drug induced) AND (hormone replacement therapy) AND (hypersensitivity) AND (liver disease) AND (malignant tumor) AND (progressive decline) AND (study drug) AND (treatment) AND (within 2 weeks) AND ((female) OR (male)) AND ((GFR) OR (Renal function) OR (endogenous creatinine clearance) OR (serum creatinine)) AND ((ACS) OR (ICM) OR (PASD) OR (SCAD) OR (TIA) OR (ischemic stroke) OR (revascularization)) AND ((DBP) OR (SBP)) AND ((Beta blockers) OR (Diuretic)) AND ((Cushing's syndrome) OR (PA) OR (RAS) OR (SAS) OR (aorta diseases) OR (hypertension) OR (pheochromocytoma)) AND ((cation exchange resins) OR (fibrates) OR (statins)) AND ((gastrectomy) OR (short bowel syndrome)) AND ((ALT) OR (AST)) AND ((Diagnosed) OR (suspected)))"}
{"candidate_id": "LLM07297", "doc_id": "NCT02777424_exc", "case_bucket": "other", "source_criterion": "Concomitant use with oral anticoagulant drugs Acquired deficiency of coagulation factors whose treatment is established Hypersensitivity to a PCC History of thrombocytopenia induced by heparin Disseminated intravascular coagulation Extracranial active bleeding Hypersensitivity to vitamin K", "candidate_expression": "((Acquired deficiency of coagulation factors whose treatment is established) AND (Disseminated intravascular coagulation) AND (Extracranial bleeding active) AND (Hypersensitivity) AND (PCC) AND (heparin) AND (oral anticoagulant drugs Concomitant) AND (thrombocytopenia) AND (vitamin K))"}
{"candidate_id": "LLM07298", "doc_id": "NCT02535299_inc", "case_bucket": "or", "source_criterion": "Newly dignosised type 2 diabetes according to WHO criteria.glycated hemoglobin (HbA1c) was more than 10%; Seronegative for antibodies against insulin, islet cells and glutamic acid decarboxylase (GAD);", "candidate_expression": "((Newly dignosised) AND (Seronegative) AND (WHO criteria) AND (antibodies) AND (glycated hemoglobin (HbA1c)) AND (more than 10%) AND (type 2 diabetes) AND ((glutamic acid decarboxylase (GAD)) OR (insulin) OR (islet cells)))"}
{"candidate_id": "LLM07299", "doc_id": "NCT02781610_inc", "case_bucket": "or", "source_criterion": "Male or female =18 years of age at Visit 1 Documentation of a CF diagnosis Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR) prior to Visit 1 (US sites only) At the time of Visit 1, there is a plan to initiate IV antibiotics for a pulmonary exacerbation Performed spirometry at Visit 1 and Visit 2 and willing to perform spirometry at Visit 3 Completed the CRISS questionnaire at Visit 1 and Visit 2 and willing to complete the Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire at Visit 3 Willing to adhere to a specific treatment duration determined by initial response to treatment and subsequent randomization Willing to return for follow up Visit 3 Written informed consent obtained from the subject or subject's legal representative", "candidate_expression": "((CF) AND (CRISS questionnaire at Visit 1) AND (Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire willing to complete at Visit 3 Willing to) AND (IV antibiotics At the time of Visit 1) AND (US sites Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR)) AND (Written informed consent) AND (age =18 years at Visit 1) AND (follow up Visit 3 Willing to) AND (pulmonary exacerbation) AND (spirometry at Visit 1 at Visit 2) AND (spirometry willing to perform at Visit 3) AND ((Male) OR (female)) AND ((Visit 2) OR (at Visit 2)) AND ((from the subject) OR (from the subject's legal representative)))"}
{"candidate_id": "LLM07300", "doc_id": "NCT02755701_inc", "case_bucket": "or", "source_criterion": "Age = 19 and = 70 years; Presence of liver cirrhosis Serum albumin level = 3.5g/dl, ultrasound or CT scan confirmed ascites (=Grade 1) No administration of diuretics and BCAA within the past 1 week Voluntary consent to take part in this trial", "candidate_expression": "((Age = 19 and = 70 years) AND (Serum albumin = 3.5g/dl) AND (Voluntary consent to take part in this trial) AND (ascites Grade 1) AND (liver cirrhosis) AND ((BCAA) OR (diuretics)) AND ((CT scan) OR (ultrasound)))"}
```
