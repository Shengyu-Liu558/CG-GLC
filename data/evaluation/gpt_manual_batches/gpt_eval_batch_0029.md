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
{"candidate_id": "LLM00701", "doc_id": "NCT01642875_inc", "case_bucket": "or", "source_criterion": "Primary periampullary tumor R0, R1 resection Chronic pancreatitis requiring pancreatoduodenectomy", "candidate_expression": "((Chronic pancreatitis) AND (Primary) AND (pancreatoduodenectomy) AND (periampullary tumor) AND (requiring) AND ((R0 resection) OR (R1 resection)))"}
{"candidate_id": "LLM00702", "doc_id": "NCT01440296_exc", "case_bucket": "other", "source_criterion": "any condition that would contra-indicate Magnetic Resonance Imaging or administration of contrast agent", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00703", "doc_id": "NCT03350659_inc", "case_bucket": "or", "source_criterion": "Age >=19 patients who complained of dizziness Orthostatic hypotension after 3-minute standing (systolic blood pressure drop >=20 or diastolic blood pressure drop >=10", "candidate_expression": "((Age >=19) AND (Orthostatic hypotension after 3-minute standing) AND (diastolic blood pressure drop >=10) AND (dizziness) AND (systolic blood pressure drop >=20))"}
{"candidate_id": "LLM00704", "doc_id": "NCT02152696_inc", "case_bucket": "or", "source_criterion": "Female with a persisting pregnancy of unknown location: A pregnancy of unknown location is defined as a pregnancy in a woman with a positive pregnancy test but no definitive signs of pregnancy in the uterus or adnexa on ultrasound imaging. A definitive sign of gestation includes ultrasound visualization of a gestational sac with a yolk sac (with or without an embryo) in the uterus or in the adnexa. Ultrasound must be performed within 7 days prior to randomization. Persistence of hCG is defined as at least 2 serial hCG values (over 2-14 days), showing < 15% rise per day, or < 50% fall between the first and last value. Patient is hemodynamically stable, hemoglobin >10 mg/dL Greater than or 18 years of age", "candidate_expression": "((>10 mg/dL) AND (Female) AND (Greater than or 18 years) AND (Persistence of hCG) AND (Ultrasound) AND (age) AND (at least 2) AND (hCG) AND (hemodynamically stable) AND (hemoglobin) AND (over 2-14 days) AND (positive) AND (pregnancy) AND (pregnancy test) AND (randomization) AND (unknown location) AND (within 7 days prior to randomization) AND (woman) AND ((< 15% rise per day) OR (< 50% fall between the first and last value.)))"}
{"candidate_id": "LLM00705", "doc_id": "NCT02874092_inc", "case_bucket": "scope", "source_criterion": "RA cohort: Receiving MTX at stable doses of 10 to 25 mg weekly for at least 12 weeks, Have a DAS28 of 3.2 or higher (The level of disease activity is considered to be low if the DAS28 is 3.2 or less) (Prevoo et al., 1995) OA cohort: Diagnosis of osteoarthritis made by physician.", "candidate_expression": "((10 to 25 mg weekly) AND (3.2 or higher) AND (DAS28) AND (MTX) AND (OA) AND (RA) AND (for at least 12 weeks) AND (made by physician) AND (osteoarthritis) AND (stable doses))"}
{"candidate_id": "LLM00706", "doc_id": "NCT02415257_exc", "case_bucket": "other", "source_criterion": "impaired decision making neurofibromatosis signs for central dysfunction remaining vestibular function Patients are advised not to participate in the gentamicin arm if hearing is better than 30 deciBel (dB) in pure tone average (500, 1000, 2000, 3-4000 Hz) and speech discrimination better than 70% the neurosurgeon aim at hearing preservation surgery and do not want to risk gentamicin associated hearing loss", "candidate_expression": "((500, 1000, 2000, 3-4000 Hz) AND (better than 30 deciBel (dB)) AND (better than 70%) AND (central dysfunction) AND (hearing) AND (impaired decision making) AND (neurofibromatosis) AND (pure tone average) AND (remaining vestibular function) AND (signs) AND (speech discrimination))"}
{"candidate_id": "LLM00707", "doc_id": "NCT02201316_inc", "case_bucket": "or", "source_criterion": "Male and females aged between 18 and 65 years of age inclusive, at the time of signing the informed consent. Healthy as determined by a responsible and experienced physician, based on a medical evaluation including medical history, physical examination, laboratory tests and cardiac monitoring. A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedures. Body weight >= 50 kilogram (kg) and body mass index within the range 19 - 24.9 kg/m^2 (inclusive). A female subject is eligible to participate if she is of: Non-childbearing potential defined as pre-menopausal females with a documented tubal ligation or hysterectomy for this definition, \"documented\" refers to the outcome of the investigator's/designee's review of the subject's medical history for study eligibility, as obtained via a verbal interview with the subject or from the subject's medical records; or postmenopausal defined as 12 months of spontaneous amenorrhea [in questionable cases a blood sample with simultaneous follicle stimulating hormone (FSH) > 40 milli-international units per milliliter (MlU/mL) and estradiol < 40 picograms per mililiter (pg/mL) [<147 picomole per liter] is confirmatory]. Females on hormone replacement therapy (HRT) and whose menopausal status is in doubt will be required to use one of the contraception methods if they wish to continue their HRT during the study. Otherwise, they must discontinue HRT to allow confirmation of post-menopausal status prior to study enrollment. For most forms of HRT, at least 2-4 weeks will elapse between the cessation of therapy and the blood draw; this interval depends on the type and dosage of HRT. Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point. Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle. Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol. This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit. Capable of giving written informed consent, which includes compliance with the requirements and restrictions listed in the consent form Alanine aminotransferase, alkaline phosphatase and bilirubin <=1.5x upper limit of normal (ULN) (isolated bilirubin >1.5xULN is acceptable if bilirubin is fractionated and direct bilirubin <35%). Based on single or averaged corrected QT interval (QTc) values of triplicate electrocardiograms obtained over a brief recording period: QTcF < 450 msec", "candidate_expression": "((A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedur) AND (Alanine aminotransferase) AND (Body weight >= 50 kilogram (kg)) AND (Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle.) AND (Females) AND (Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point.) AND (Healthy medical history as determined by a responsible and experienced physician) AND (Male) AND (Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol.) AND (QTcF < 450 msec) AND (This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit.) AND (age between 18 and 65 years) AND (aged between 18 and 65 years) AND (alkaline phosphatase) AND (as determined by a responsible and experienced physician) AND (bilirubin) AND (bilirubin >1.5xULN) AND (body mass index within the range 19 - 24.9 kg/m^2) AND (cardiac monitoring) AND (clinical abnormality) AND (corrected QT interval (QTc) < 450 msec) AND (direct bilirubin single averaged) AND (electrocardiograms over a brief recording period) AND (estradiol < 40 picograms per mililiter (pg/mL) <147 picomole per liter) AND (female) AND (females) AND (follicle stimulating hormone (FSH) > 40 milli-international units per milliliter (MlU/mL)) AND (hormone replacement therapy (HRT)) AND (hysterectomy) AND (laboratory parameter outside the reference range) AND (laboratory tests) AND (medical evaluation) AND (menopausal status in doubt) AND (physical examination) AND (postmenopausal) AND (pre-menopausal) AND (spontaneous amenorrhea 12 months) AND (tubal ligation) AND NOT (childbearing potential))"}
{"candidate_id": "LLM00708", "doc_id": "NCT01963754_exc", "case_bucket": "or", "source_criterion": "If smoking and/or other drug addiction is present If local anesthetic allergy is present Patient subjected to chemical or radiotherapy if Hepatic disease is present If immunodepression is present If Pregnancy is present If Diabetes is present If Heart disease is present", "candidate_expression": "((Diabetes) AND (Heart disease) AND (Hepatic disease) AND (Pregnancy) AND (allergy) AND (immunodepression) AND (local anesthetic) AND ((drug addiction) OR (smoking)) AND ((chemical) OR (radiotherapy)))"}
{"candidate_id": "LLM00709", "doc_id": "NCT03177837_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((COPD GOLD) AND (FEV1 40-80% predicted) AND (Male) AND (SpO2 =92% 750 m) AND (Written informed consent.) AND (age 18-75 yrs) AND (female) AND (living at low altitude <800m))"}
{"candidate_id": "LLM00710", "doc_id": "NCT02900443_inc", "case_bucket": "other", "source_criterion": "Probable or definite diagnosis of autoimmune hepatitis according to the International Autoimmune Hepatitis Study Group criteria First presentation of AIH requiring treatment according to the current EASL guidelines Age = 18 years Must provide informed consent and agree to comply with the trial protocol", "candidate_expression": "((AIH) AND (Age = 18 years) AND (EASL guidelines) AND (International Autoimmune Hepatitis Study Group criteria) AND (Must provide informed consent and agree to comply with the trial protocol) AND (autoimmune hepatitis) AND (treatment))"}
{"candidate_id": "LLM00711", "doc_id": "NCT00718952_exc", "case_bucket": "or", "source_criterion": "The other types of pulmonary hypertension. Subjects who refuse to subscribe written informed consents or can't cooperate with the trial well. Subjects with serious acute or chronic disease involved liver, kidney, and brain or have to use potent CYP3A4-inhibitor or nitrate to treat the underlying diseases. Subjects who are currently treated with sildenafil for PAH or taking sildenafil or tadalafil. Other contraindications in package insert.", "candidate_expression": "((CYP3A4-inhibitor) AND (PAH) AND (acute) AND (can't cooperate with the trial) AND (chronic disease involved brain) AND (chronic disease involved kidney) AND (chronic disease involved liver) AND (contraindications in package insert) AND (currently) AND (nitrate) AND (other types) AND (potent) AND (pulmonary hypertension) AND (refuse to subscribe written informed consents) AND (serious) AND (sildenafil) AND (tadalafil) AND (underlying diseases))"}
{"candidate_id": "LLM00712", "doc_id": "NCT02295202_exc", "case_bucket": "other", "source_criterion": "Smokers Patients under chronic use of medications Neurological diseases Coronary artery disease Acute heart failure Chronic renal failure (GFR < 30 ml/min) Chronic obstructive pulmonary disease Mild OSA and patients with BMI over 40 kg/m2.", "candidate_expression": "((Acute heart failure) AND (BMI over 40 kg/m2) AND (Coronary artery disease) AND (GFR < 30 ml/min) AND (Mild OSA) AND (Neurological diseases) AND (Smokers) AND (medications chronic use) AND (obstructive pulmonary disease Chronic) AND (renal failure Chronic))"}
{"candidate_id": "LLM00713", "doc_id": "NCT00970866_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age No more than 20 wk of gestation Given Ante-natal Cards of the Ghana Health Service Completed the initial routine ante-natal examination at the clinics HIV negative or status unknown (as from the Ante-natal card) Free from chronic disease e.g. malignancy requiring frequent medical attention (as from the Ante-natal card) Residing in the Manya Krobo or Yilo Krobo district Prepared to sign an informed consent Living in the area throughout the duration of the study Acceptance of home visitors", "candidate_expression": "((Acceptance of home visitors) AND (HIV status unknown) AND (Living in the area throughout the duration of the study the study) AND (Manya Krobo district) AND (Prepared to sign an informed consent) AND (Residing) AND (Yilo Krobo district) AND (age At least 18 years) AND (chronic disease) AND (clinics) AND (gestation) AND (gestation No more than 20 wk) AND (malignancy) AND (negative) AND (routine ante-natal examination))"}
{"candidate_id": "LLM00714", "doc_id": "NCT02429583_inc", "case_bucket": "other", "source_criterion": "Willing to receive three doses of an FDA-approved Hepatitis B vaccine Volunteer chronically infected with HCV (as demonstrated by serology and/or viral load laboratory studies) Healthy volunteer without significant medical problems", "candidate_expression": "((HCV infected chronically) AND (Willing to receive three doses of an FDA-approved Hepatitis B vaccine) AND (volunteer Healthy))"}
{"candidate_id": "LLM00715", "doc_id": "NCT03249311_exc", "case_bucket": "or", "source_criterion": "Lifetime personal history of diagnosis of major depressive disorder according to the DSM-V (American Psychiatric Association, 2013) using the Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition (SCID-5-RV for DSM-V; First et al., 2015) A history of suicidal ideation and behaviour, including self-harm and/or harm to others. A history of substance abuse and/or dependence. A positive drug screen for illicit drugs Substantial alcohol use Current use of Monoamine Oxidase Inhibitors (MAOIs), including the antibiotic linezolid and the thiazine dye methylthioninium chloride (methylene blue) Current use of serotonin-precursors (such as L-tryptophan, oxitriptan) Current use of serotonergic drugs (triptans, certain tricyclic antidepressants, lithium, tramadol, St. John's Wort) Concomitant use of NSAIDS, ASA, and other anticoagulants. Current use of Thioridazine Current use of CYP1A2 Inhibitors Current use of Triptans (5HT1 Agonists) Blood pressure greater than 140/90 and/or a pulse rate greater than 90 bpm Recent history of myocardial infarction, cerebrovascular accident, cardiac arrhythmias, or unstable heart disease. Evidence of significant physical illness contraindicating the use of levomilnacipran and duloxetine found on the physical exam or in the laboratory data obtained during the first week of the study Current use of medication that may affect voiding (ie- anticholinergics) History of obstructive urinary disorders and dysuria, prostatic hypertrophy, prostatitis, and other lower urinary tract obstructive disorders. History of Stevens-Johnson Syndrome and Erythema multiforme. Diabetes Type I and II Fructose intolerance, glucose-galactose malabsorption or sucrose-isomaltase insufficiency. Hepatic Impairment Uncontrolled narrow-angle glaucoma Severe renal impairment History of seizure disorder Anatomically narrow ocular angles. Osteoporosis or major risk for bone fractures.", "candidate_expression": "((5HT1 Agonists) AND (Anatomically narrow ocular angles) AND (Blood pressure greater than 140/90) AND (CYP1A2 Inhibitors) AND (Hepatic Impairment) AND (Monoamine Oxidase Inhibitors (MAOIs)) AND (Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition) AND (Substantial alcohol use) AND (Thioridazine) AND (Triptans) AND (affect voiding) AND (anticholinergics) AND (contraindicating) AND (drug screen for illicit drugs positive) AND (major depressive disorder DSM-V) AND (medication Current) AND (methylene blue) AND (methylthioninium chloride) AND (narrow-angle glaucoma Uncontrolled) AND (physical illness) AND (pulse rate greater than 90 bpm) AND (renal impairment Severe) AND (seizure disorder History) AND (serotonergic drugs) AND (serotonin-precursors) AND ((antibiotic linezolid) OR (thiazine dye)) AND ((L-tryptophan) OR (oxitriptan)) AND ((St. John's Wort) OR (lithium) OR (tramadol) OR (tricyclic antidepressant) OR (triptans)) AND ((ASA) OR (NSAIDS) OR (anticoagulants other)) AND ((cardiac arrhythmias) OR (cerebrovascular accident) OR (myocardial infarction) OR (unstable heart disease)) AND ((duloxetine) OR (levomilnacipran)) AND ((laboratory) OR (physical exam)) AND ((dysuria) OR (lower urinary tract obstructive disorders other) OR (obstructive urinary disorders) OR (prostatic hypertrophy) OR (prostatitis)) AND ((harm to others) OR (self-harm) OR (suicidal behaviour) OR (suicidal ideation)) AND ((Erythema multiforme) OR (Stevens-Johnson Syndrome)) AND ((Diabetes Type I) OR (Diabetes Type II)) AND ((Fructose intolerance) OR (glucose-galactose malabsorption) OR (sucrose-isomaltase insufficiency)) AND ((substance abuse) OR (substance dependence)) AND ((Osteoporosis) OR (bone fractures major risk)))"}
{"candidate_id": "LLM00716", "doc_id": "NCT01184638_inc", "case_bucket": "or", "source_criterion": "Patients with informed consents Without basal disorders of neurology and psychiatrics", "candidate_expression": "((Patients with informed consents) AND ((basal disorders of neurology) OR (basal disorders of psychiatrics)))"}
{"candidate_id": "LLM00717", "doc_id": "NCT02802644_exc", "case_bucket": "or", "source_criterion": "Left main disease Known hypersensitivity or contraindication to any of the following medications: Heparin, aspirin, clopidogrel, sirolimus, siptagliptin and statin Congestive heart failure (patients with LVEF <30% or cardiogenic shock) Uncontrolled myocardial ischemia (repeated chest pain or dyspnea after revascularization) Uncontrolled ventricular arrhythmia History of malignancy with chemotherapy Serious hematologic disease (e.g. CML, MDS) Current infectious disease needs antibiotics therapy Creatinine level >1.5 mg/dL or dependence on dialysis Other severe concurrent illness (e.g. active infection, malignancy). Life expectancy of less than one year Pregnancy or women with potential childbearing Type I DM Treatment with insulin History of pancreatitis Who cannot read the informed consent form (e.g. illiteracy, foreigner)", "candidate_expression": "((CML) AND (Congestive heart failure) AND (Creatinine level >1.5 mg/dL) AND (Heparin) AND (LVEF <30%) AND (Left main disease) AND (MDS) AND (Pregnancy or women with potential childbearing) AND (Type I DM) AND (Who cannot read the informed consent form (e.g. illiteracy, foreigner)) AND (active infection) AND (antibiotics) AND (aspirin) AND (cardiogenic shock) AND (chemotherapy) AND (chest pain) AND (clopidogrel) AND (contraindication) AND (dialysis) AND (dyspnea) AND (hematologic disease Serious) AND (hypersensitivity) AND (ife expectancy less than one year) AND (illness severe concurrent) AND (infectious disease) AND (insulin) AND (malignancy) AND (myocardial ischemia Uncontrolled) AND (pancreatitis) AND (revascularization) AND (siptagliptin) AND (sirolimus) AND (statin) AND (ventricular arrhythmia Uncontrolled))"}
{"candidate_id": "LLM00718", "doc_id": "NCT02735902_exc", "case_bucket": "or", "source_criterion": "The patient is participating in another study The patient is in an exclusion period determined by a previous study The patient or his/her representative refuses to sign the consent It is impossible to correctly inform the patient or his/her representative The patient is pregnant or breastfeeding The patient has a contraindication (or an incompatible drug association) for a treatment used in this study The patient had a coronary stent for less than 12 months The patient does not require treatment with aspirin or any other antiplatelet agent The patient has a history of aspirin allergy High bleeding risk; such as platelets <50,000 / mm3 during screening, Hb <8.5 g / dL, history of intracranial hemorrhage or subdural hematoma, major surgery, parenchymal organ biopsy or severe trauma within 30 days before inclusion, active gastrointestinal ulcer in the last 3 months; History of Stroke in the last 3 months; Moderate or severe liver affection associated with coagulopathy Active infectious endocarditis Active tumor treated at the time of inclusion associated with expected survival less than one year", "candidate_expression": "((<50,000 / mm3) AND (<8.5 g / dL) AND (Active) AND (Hb) AND (High) AND (History of) AND (It is impossible to correctly inform the patient or his/her representative) AND (Moderate) AND (Stroke) AND (The patient is participating in another study) AND (The patient is pregnant or breastfeeding) AND (The patient or his/her representative refuses to sign the consent) AND (active) AND (allergy) AND (antiplatelet agent) AND (aspirin) AND (associated with coagulopathy) AND (at the time of inclusion) AND (bleeding risk) AND (coagulopathy) AND (contraindication) AND (coronary stent) AND (expected survival) AND (gastrointestinal ulcer) AND (history of) AND (in the last 3 months) AND (infectious endocarditis) AND (intracranial hemorrhage) AND (last 3 months) AND (less than 12 months) AND (less than one year) AND (liver affection) AND (major surgery,) AND (not) AND (other) AND (parenchymal organ biopsy) AND (platelets) AND (require) AND (severe) AND (subdural hematoma) AND (trauma) AND (treated) AND (treatment) AND (tumor) AND (within 30 days))"}
{"candidate_id": "LLM00719", "doc_id": "NCT02673359_inc", "case_bucket": "or", "source_criterion": "Women with singleton pregnancy. History of preterm labor and/or midtrimester miscarriage in a previous pregnancy. Cervical length of 15-25 mm by transvaginal sonography (TVS) at 16-24 weeks of gestation.", "candidate_expression": "((Cervical length 15-25 mm) AND (Women) AND (gestation 16-24 weeks) AND (pregnancy previous) AND (singleton pregnancy) AND (transvaginal sonography (TVS) at 16-24 weeks of gestation) AND ((midtrimester miscarriage) OR (preterm labor)))"}
{"candidate_id": "LLM00720", "doc_id": "NCT03318874_exc", "case_bucket": "or", "source_criterion": "Glaucoma, Ocular allergy Autoimmune disease Contact lens-wear during study Current punctal plugging Pregnant/lactating Candidate for topical anti-inflammatory Cicatricial meibomian gland dysfunction", "candidate_expression": "((Autoimmune disease) AND (Contact lens-wear during study) AND (Glaucoma) AND (Ocular allergy) AND (meibomian gland dysfunction Cicatricial) AND (punctal plugging Current) AND (topical anti-inflammatory Candidate for) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM00721", "doc_id": "NCT02364648_inc", "case_bucket": "other", "source_criterion": "Stage 3 - 5 Chronic Kidney Disease", "candidate_expression": "((3 - 5) AND (Chronic Kidney Disease) AND (Stage))"}
{"candidate_id": "LLM00722", "doc_id": "NCT03097068_exc", "case_bucket": "or", "source_criterion": "History of anti-vascular endothelial growth factor treatment in the past 12 months Any diabetic macular edema treatment in the past 4 months Heart attack, stroke, transient ischemic attack or acute congestive heart failure within 4 months", "candidate_expression": "((anti-vascular endothelial growth factor in the past 12 months) AND (diabetic macular edema) AND (treatment in the past 4 months) AND ((Heart attack) OR (acute congestive heart failure within 4 months) OR (stroke) OR (transient ischemic attack)))"}
{"candidate_id": "LLM00723", "doc_id": "NCT02627560_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding known thromboembolic disease or with high risk of thromboembolism, warranting extra anticoagulation in connection with the procedure known allergy to tranexamic acid/Cyklokapron®", "candidate_expression": "((Cyklokapron) AND (allergy) AND (breastfeeding) AND (extra anticoagulation) AND (pregnant) AND (thromboembolic disease) AND (thromboembolism high risk of) AND (tranexamic acid))"}
{"candidate_id": "LLM00724", "doc_id": "NCT02656394_exc", "case_bucket": "or", "source_criterion": "1. Comorbidity with other severe or chronic eye conditions that in the judgment of the investigator will interfere with study assessments, such as corneal opacities and scars, dystrophies, epithelial scarring, infections, blood clots, etc. 2. Best corrected visual acuity (BCVA) at baseline <20/200. 3. Has a condition or history that, in the opinion of the investigator, may interfere significantly with the subject's participation in the study. 4. A woman who is pregnant, nursing an infant, or planning a pregnancy. 5. Has a known adverse reaction and/or sensitivity to the study drug or its components. 6. Routine use (more than twice a week) of a chlorinated swimming pool. 7. Unwilling or unable to cease using the following medications during the study period: Topical ocular cyclosporine (e.g. Restasis®), anti-histamines, antipsychotics, or eye gels. 8. Currently enrolled in an investigational drug or device study or have used an investigational drug or device within 30 days prior to Visit 1.", "candidate_expression": "((<20/200) AND (Best corrected visual acuity (BCVA)) AND (Restasis®) AND (Routine use) AND (Unwilling or unable) AND (Visit 1) AND (at baseline) AND (baseline) AND (chlorinated swimming pool) AND (during the study period) AND (eye conditions) AND (in the judgment of the investigator) AND (in the opinion of the investigator) AND (may interfere significantly) AND (more than twice a week) AND (study period) AND (will interfere with study assessments) AND (within 30 days prior to Visit 1) AND (woman) AND ((blood clots) OR (corneal opacities) OR (corneal scars) OR (dystrophies) OR (epithelial scarring) OR (infections)) AND ((nursing) OR (pregnancy) OR (pregnant)) AND ((adverse reaction to the study drug or its components) OR (sensitivity to the study drug or its components)) AND ((Topical ocular cyclosporine) OR (anti-histamines) OR (antipsychotics) OR (eye gels)) AND ((investigational device) OR (investigational drug)))"}
{"candidate_id": "LLM00725", "doc_id": "NCT01701219_inc", "case_bucket": "or", "source_criterion": "1. Presence of bacteremia due solely to: S. aureus on at least 1 blood culture within 72 hours of beginning study drug (Cohort A) OR MRSA on a baseline blood culture and on at least 1 additional blood culture after at least 72 hours of vancomycin and/or daptomycin treatment (Cohort B). 2. Male or female ≥ 18 years of age. 3. If female of childbearing potential must be willing to practice sexual abstinence or dual methods of contraception during treatment and for at least 30 days after the last dose of study drug. 4. Expectation of survival for at least 2 months.", "candidate_expression": "((Male) AND (age ≥ 18 years) AND (bacteremia) AND (blood culture MRSA baseline) AND (blood culture S. aureus at least 1 within 72 hours of beginning study drug) AND (blood culture at least 1 additional after at least 72 hours of vancomycin and/or daptomycin treatment) AND (childbearing potential) AND (daptomycin) AND (daptomycin treatment) AND (female) AND (methods of contraception dual the last dose of study drug) AND (practice sexual abstinence) AND (survival Expectation for at least 2 months) AND (vancomycin treatment) AND (vancomycin vancomycin and/or daptomycin treatment))"}
```
