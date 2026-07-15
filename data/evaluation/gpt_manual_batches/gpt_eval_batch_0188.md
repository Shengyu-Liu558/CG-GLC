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
{"candidate_id": "LLM04676", "doc_id": "NCT02620904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04677", "doc_id": "NCT03620526_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04678", "doc_id": "NCT02805504_exc", "case_bucket": "or", "source_criterion": "Pregnant and/or nursing mothers. Allergy to bupivacaine. History of drug/alcohol abuse. Severe cardiovascular, hepatic, renal disease or neurological impairment.", "candidate_expression": "((Allergy) AND (bupivacaine) AND (drug/alcohol abuse History) AND ((Pregnant) OR (nursing)) AND ((disease cardiovascular) OR (hepatic disease) OR (neurological impairment) OR (renal disease)))"}
{"candidate_id": "LLM04679", "doc_id": "NCT01765231_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with lymphoma HBsAg negative/HBcAb positive/hepatitis B virus DNA negative at baseline treated with chemotherapy and/or immunosuppressive therapy life expectancy of more than 3 months", "candidate_expression": "((HBcAb) AND (HBsAg) AND (at baseline) AND (chemotherapy) AND (hepatitis B virus DNA) AND (immunosuppressive therapy) AND (life expectancy) AND (lymphoma) AND (more than 3 months) AND (negative) AND (positive) AND (treatment-naive))"}
{"candidate_id": "LLM04680", "doc_id": "NCT02488057_inc", "case_bucket": "other", "source_criterion": "Mexican-american Female BMI 30-42 willingness to complete protocol pre-diabetic English or Spanish literate", "candidate_expression": "((30-42) AND (BMI) AND (Female) AND (Mexican-american) AND (pre-diabetic) AND (willingness to complete protocol))"}
{"candidate_id": "LLM04681", "doc_id": "NCT03138577_exc", "case_bucket": "or", "source_criterion": "Patient refusal for supraclavicular block Inability to give informed consent Allergy to local anesthetics Hemidiaphragmatic dysfunction, suspected or known PNP Neuromuscular disease Obstructive or restrictive pulmonary disease Medical or anatomic contraindication to supraclavicular blockade as judged by clinician Pregnancy", "candidate_expression": "((Allergy) AND (Inability to give informed consent) AND (Neuromuscular disease) AND (Patient refusal) AND (Pregnancy) AND (contraindication) AND (local anesthetics) AND (supraclavicular block) AND (supraclavicular blockade) AND ((Obstructive pulmonary disease) OR (restrictive pulmonary disease)) AND ((Medical) OR (anatomic)) AND ((Hemidiaphragmatic dysfunction) OR (PNP)) AND ((known) OR (suspected)))"}
{"candidate_id": "LLM04682", "doc_id": "NCT02226887_inc", "case_bucket": "other", "source_criterion": "Patients undergoing a loop ileostomy closure", "candidate_expression": "(loop ileostomy closure)"}
{"candidate_id": "LLM04683", "doc_id": "NCT02638935_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women Women with breast implants on the same side as the lesion Women that underwent local radiation or chemotherapy within the last 12 months Women with history of breast cancer or breast surgery in the same quadrant Lesions in or close to scar tissue (< 1cm) Skin lesions or lesions that have been biopsied previously Lesion larger than 4 cm in the longest dimension No lesion should be included when more than 50% of the lesion is further down than 4 cm beneath the skin level.", "candidate_expression": "((Lesion) AND (Lesions in or close to scar tissue) AND (Pregnant) AND (Skin lesions) AND (Women) AND (beneath the skin level further down than 4 cm) AND (biopsied previously) AND (breast cancer same quadrant) AND (breast implants same side as the lesion) AND (breast surgery same quadrant) AND (chemotherapy within the last 12 months) AND (lactating) AND (lesion more than 50% of the lesion) AND (lesions) AND (local radiation within the last 12 months) AND (longest dimension larger than 4 cm) AND (women))"}
{"candidate_id": "LLM04684", "doc_id": "NCT02269137_inc", "case_bucket": "or", "source_criterion": "30 min or more of (1) continuous clinical seizure activities or (2) recurrent seizure activities without recovery(returning to baseline)between seizures; clinical data is complete.", "candidate_expression": "((seizure continuous 30 min or more) AND (seizure recurrent without recovery))"}
{"candidate_id": "LLM04685", "doc_id": "NCT01996436_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent from patient or patients kin Pregnant women less than 18 years of age of more than 80 years of age Hunt Hess Grade 5 SAH", "candidate_expression": "((5) AND (Hunt Hess Grade) AND (Inability to obtain consent from patient or patients kin) AND (Pregnant women) AND (SAH) AND (less than 18 years) AND (more than 80 years) AND ((age)))"}
{"candidate_id": "LLM04686", "doc_id": "NCT03079141_exc", "case_bucket": "or", "source_criterion": "Any previous treatments for active CSC; Previous prescription of mineralocorticoid receptor antagonists, for cCSC or for other diseases; Current treatment with corticosteroids (topical or systemic), corticosteroid use within 3 months before possible start of trial treatment, or anticipated start of corticosteroid treatment within the first 2 years from the start of the trial period; Evidence of another diagnosis that can explain serous SRF or visual loss; Best-corrected visual acuity < 20/200 (Snellen equivalent); Profound chorioretinal atrophy in central macular area on ophthalmoscopy and OCT; Myopia > 6D; Visual loss and/or serous detachment on OCT < 6 weeks; Continuous and/or progressive visual loss > 18 months or serous detachment on OCT > 18 months; No hyperfluorescence on ICGA; Intraretinal edema on OCT; (relative) Contraindications for FA or ICGA; (relative) Contraindications for photodynamic treatment (pregnancy, porphyria, severely disturbed liver function). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening (relative) Known contraindications for initiation of eplerenone treatment (hyperkalemia, abnormal renal clearance, severe hepatic insufficiency (Child-Pugh C), type 2 diabetes mellitus with microalbuminuria, concomitant use of potassium supplements, potassium-sparing diuretics, strong CYP3A4 inhibitors, or the combination of an ACE-inhibitor and an angiotensin receptor blocking agent). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening; Soft drusen in treated eye or fellow eye, signs of choroidal neovascularization on ophthalmoscopy and/or FA/ICGA of the study eye.", "candidate_expression": "((ACE-inhibitor) AND (Best-corrected visual acuity < 20/200) AND (CSC active) AND (Child-Pugh C) AND (Contraindications) AND (ICGA hyperfluorescence) AND (Intraretinal edema) AND (Myopia > 6D) AND (OCT) AND (OCT < 6 weeks) AND (Soft drusen) AND (abnormal renal clearance) AND (angiotensin receptor blocking agent) AND (chorioretinal atrophy Profound central macular area) AND (choroidal neovascularization) AND (contraindications) AND (eplerenone) AND (microalbuminuria) AND (mineralocorticoid receptor antagonists Previous topical) AND (ophthalmoscopy) AND (photodynamic treatment) AND (serous detachment) AND (systemic) AND (treatments previous) AND (type 2 diabetes mellitus) AND ((corticosteroid treatment anticipated within the first 2 years from the start of the trial period) OR (corticosteroid use within 3 months before possible start of trial treatment) OR (corticosteroids Current)) AND ((Visual loss) OR (serous detachment)) AND ((Continuous) OR (progressive)) AND ((OCT > 18 months) OR (visual loss > 18 months)) AND ((FA) OR (ICGA)) AND ((disturbed liver function severely) OR (porphyria) OR (pregnancy)) AND ((hyperkalemia) OR (renal clearance abnormal) OR (severe hepatic insufficiency)) AND ((cCSC) OR (other diseases)) AND ((potassium supplements) OR (potassium-sparing diuretics) OR (strong CYP3A4 inhibitors)) AND ((fellow eye) OR (treated eye)) AND ((FA) OR (ICGA) OR (ophthalmoscopy)))"}
{"candidate_id": "LLM04687", "doc_id": "NCT02707809_exc", "case_bucket": "or", "source_criterion": "allergic history to dexmedetomidine refractory bradycardia < 60 bpm despite treatment severe atrioventricular block (2nd and 3rd degree) previous operation of tongue", "candidate_expression": "((allergic history) AND (atrioventricular block severe) AND (bradycardia refractory < 60 bpm despite treatment) AND (dexmedetomidine) AND (operation of tongue previous) AND (treatment) AND ((2nd degree) OR (3rd degree)))"}
{"candidate_id": "LLM04688", "doc_id": "NCT00943865_exc", "case_bucket": "or", "source_criterion": "diabetes ischemic heart disease or any abnormality on treadmill stress test inflammatory or chronic disorder pregnancy lactation creatinine level of 1,5 mg/dL or more gastrointestinal problems or musculoskeletal disorders that would prevent them to follow the test diets or exercise interventions liver dysfunction with a factor of at least 3 above the upper limit of normal in AST and ALT levels thyroid dysfunction, with serum TSH out of normal limits use of immunosuppressive drugs, corticosteroids or anorexigen", "candidate_expression": "((1,5 mg/dL or more) AND (ALT levels) AND (AST levels) AND (abnormality) AND (anorexigen) AND (chronic disorder) AND (corticosteroids) AND (creatinine level) AND (diabetes) AND (disorder inflammatory) AND (exercise interventions) AND (factor of at least 3 above the upper limit of normal) AND (gastrointestinal problems) AND (immunosuppressive drugs) AND (ischemic heart disease) AND (lactation) AND (liver dysfunction) AND (musculoskeletal disorders) AND (out of normal limits) AND (pregnancy) AND (prevent) AND (serum TSH) AND (test diets) AND (thyroid dysfunction) AND (treadmill stress test))"}
{"candidate_id": "LLM04689", "doc_id": "NCT02632318_exc", "case_bucket": "other", "source_criterion": "Regular cigarette smoker Alcohol abuse Drug abuse", "candidate_expression": "((Alcohol abuse) AND (Drug abuse) AND (Regular cigarette smoker))"}
{"candidate_id": "LLM04690", "doc_id": "NCT01228279_inc", "case_bucket": "other", "source_criterion": "Adult (age 18 years and older) Patients with end-stage renal disease(ESRD)/chronic kidney disease(CKD)stage 5", "candidate_expression": "((18 years and older) AND (Adult) AND (CKD) AND (ESRD) AND (age) AND (chronic kidney disease) AND (end-stage renal disease) AND (stage 5))"}
{"candidate_id": "LLM04691", "doc_id": "NCT02918409_inc", "case_bucket": "or", "source_criterion": "Male or female = 18 years of age at Visit 1. Sweat chloride equal or greater than 60 mEq/L by quantitative pilocarpine iontophoresis test. Two well-characterized mutations in the cystic fibrosis transmembrane conductance regulator (CFTR) gene Abnormal nasal potential difference (NPD) as measured by a change in NPD in response to a low chloride solution and isoproterenol of less than -5 mV. Documentation of the presence of an acute pulmonary exacerbation, based on CF Foundation guidelines, as diagnosed by a faculty member of the Denver Adult CF Program. Respiratory culture(s) demonstrating evidence of Pseudomonas aeruginosa or Achromobacter species airway infection. Subject is able to produce sputum, undergo phlebotomy, and provide written consent. The subject's treating physician has determined that they should receive either tobramycin or colistin intravenously as one of the designated agents for their APE treatment. Subjects who are able to receive either tobramycin or colistin as part of their antibiotic regimen will be randomized into one of three arms. If a treating physician deems that a subject cannot receive tobramycin due to vestibular toxicity, ototoxicity or bacterial resistance, the subject will be randomized to either standard or PK-adjusted colistin.", "candidate_expression": "((CF Foundation guidelines) AND (CFTR) AND (NPD) AND (Respiratory culture(s)) AND (Subject is able to produce sputum, undergo phlebotomy, and provide written consent.) AND (Sweat chloride equal or greater than 60 mEq/L) AND (The subject's treating physician has determined that they should receive either tobramycin or colistin intravenously as one of the designated agents for their APE treatment. Subjects who are able to receive either tobramycin or colistin as part of their antibiotic regimen will be randomized into one of three arms. If a treating physician deems that a subject cannot receive tobramycin due to vestibular toxicity, ototoxicity or bacterial resistance, the subject will be randomized to either standard or PK-adjusted colistin) AND (acute pulmonary exacerbation) AND (age = 18 years at Visit 1.) AND (airway infection) AND (cystic fibrosis transmembrane conductance regulator gene) AND (mutations Two) AND (nasal potential difference Abnormal less than -5 mV) AND (quantitative pilocarpine iontophoresis test) AND ((Male) OR (female)) AND ((Achromobacter species) OR (Pseudomonas aeruginosa)))"}
{"candidate_id": "LLM04692", "doc_id": "NCT03444142_exc", "case_bucket": "or", "source_criterion": "Women with confirmed or suspected pregnancy Women under lactation and/or puerperium Hypersensibility to ingredients of intervention Physical impossibility for apply the drug Known pancreatic, renal, hepatic, heart or thyroid diseased Hypertension diagnosis Previous treatment for glucose Body Mass Index =39.9 kg/m2 Triglycerides =500 mg/dL Total cholesterol =300 mg/dL Night or rotating shift workers Blood Pressure =140/90 mmHg", "candidate_expression": "((Blood Pressure =140/90 mmHg) AND (Body Mass Index =39.9 kg/m2) AND (Hypersensibility) AND (Hypertension) AND (Night shift workers) AND (Total cholesterol =300 mg/dL) AND (Triglycerides =500 mg/dL) AND (Women) AND (Women confirmed suspected) AND (heart disease) AND (hepatic disease) AND (ingredients of intervention) AND (lactation) AND (pancreatic disease) AND (pregnancy) AND (puerperium) AND (renal disease) AND (rotating shift workers) AND (thyroid disease) AND (treatment for glucose Previous))"}
{"candidate_id": "LLM04693", "doc_id": "NCT02920177_inc", "case_bucket": "scope", "source_criterion": "Patients with symptomatic FAI Clinical and radiographic evidence of FAI Patients able to provide consent to study participation Completion of 6 weeks of physical therapy program", "candidate_expression": "((6 weeks) AND (Clinical evidence) AND (FAI) AND (Patients able to provide consent to study participation) AND (physical therapy program) AND (radiographic evidence) AND (symptomatic))"}
{"candidate_id": "LLM04694", "doc_id": "NCT02361892_inc", "case_bucket": "other", "source_criterion": "submucosal, intramural or subserosal leiomyomas, symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain", "candidate_expression": "((infertility) AND (intramural leiomyomas) AND (menometrorrhagia) AND (menstrual disorder) AND (pelvic pain) AND (submucosal) AND (subserosal leiomyomas) AND (symptoms))"}
{"candidate_id": "LLM04695", "doc_id": "NCT02226887_inc", "case_bucket": "other", "source_criterion": "Patients undergoing a loop ileostomy closure", "candidate_expression": "(loop ileostomy closure)"}
{"candidate_id": "LLM04696", "doc_id": "NCT02862912_exc", "case_bucket": "or", "source_criterion": "Any contraindication to neuraxial anesthesia (history of neurologic disease (e.g., multiple sclerosis, spinal stenosis, central or peripheral neuropathy) Pre-existing/chronic back pain Ester local anesthetic allergy, PABA allergy History of atypical cholinesterase (CP is metabolized by cholinesterase)", "candidate_expression": "((Ester local anesthetic) AND (History) AND (PABA) AND (atypical cholinesterase) AND (back pain) AND (contraindication) AND (history) AND (neuraxial anesthesia) AND (neurologic disease) AND ((Pre-existing) OR (chronic)) AND ((allergy)) AND ((central neuropathy) OR (multiple sclerosis) OR (peripheral neuropathy) OR (spinal stenosis)))"}
{"candidate_id": "LLM04697", "doc_id": "NCT01614041_inc", "case_bucket": "or", "source_criterion": "18-65 years old Male or female Diagnosed with GAD according to DSM-IV HAMA score=17 Provide with written informed consent Agree to be washed-out for two weeks if receiving SSRI, SNRI or NASA.", "candidate_expression": "((DSM-IV) AND (GAD) AND (HAMA score =17) AND (Male) AND (NASA) AND (Provide with written informed consent) AND (SNRI) AND (SSRI) AND (female) AND (washed-out for two weeks) AND (years old 18-65))"}
{"candidate_id": "LLM04698", "doc_id": "NCT03499639_inc", "case_bucket": "other", "source_criterion": "patients were 18 years old or more, naive to HCV treatment, HCV genotype 4, compensated liver disease.", "candidate_expression": "((18 years old or more) AND (4) AND (HCV genotype) AND (HCV treatment) AND (compensated) AND (liver disease) AND (naive) AND (old))"}
{"candidate_id": "LLM04699", "doc_id": "NCT02101554_exc", "case_bucket": "or", "source_criterion": "Columbia-Suicide Severity Rating Scale (C-SSRS) for suicidal ideation and behavior in past year. Hypersensitivity to morphine, naltrexone. A life expectancy (assessed by investigator) of less than 6 months or is no longer capable of taking medication orally. Undergone surgery within 3 days prior to the first day of dosing.", "candidate_expression": "((C-SSRS) AND (Columbia-Suicide Severity Rating Scale) AND (Hypersensitivity) AND (first day of dosing) AND (in past year) AND (less than 6 months) AND (life expectancy) AND (surgery) AND (within 3 days prior to the first day of dosing) AND ((suicidal behavior) OR (suicidal ideation)) AND ((morphine) OR (naltrexone)))"}
{"candidate_id": "LLM04700", "doc_id": "NCT02673359_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Congenital uterine malformation. Multifetal pregnancy. Known major fetal structural or chromosomal abnormality. Known allergy or contraindication (relative or absolute) to progesterone therapy. Presence of contraindication to cervical cerclage. Medical conditions complicating pregnancy. Vaginal bleeding.", "candidate_expression": "((< 20) AND (> 35 years) AND (Age) AND (Congenital uterine malformation) AND (Medical conditions) AND (Multifetal pregnancy) AND (Vaginal bleeding) AND (absolute) AND (allergy) AND (cervical cerclage) AND (chromosomal abnormality) AND (complicating pregnancy) AND (contraindication) AND (fetal structural) AND (major) AND (progesterone therapy) AND (relative))"}
```
