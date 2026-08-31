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
{"candidate_id": "LLM05101", "doc_id": "NCT03297944_inc", "case_bucket": "other", "source_criterion": "valid driver's license english-speaking and literate", "candidate_expression": "((english-speaking) AND (literate) AND (valid driver's license))"}
{"candidate_id": "LLM05102", "doc_id": "NCT03113253_exc", "case_bucket": "or", "source_criterion": "Subjects with a history of hypercoagulopathy, deep vein thrombosis (DVT), pulmonary embolism Renal impairment Subjects with known hypersensitivity to tranexamic acid Consecutive fibrinolytic states to coagulopathy History of convulsions", "candidate_expression": "((DVT) AND (History) AND (Renal impairment) AND (coagulopathy) AND (convulsions) AND (fibrinolytic states) AND (history) AND (hypersensitivity) AND (tranexamic acid) AND ((deep vein thrombosis) OR (hypercoagulopathy) OR (pulmonary embolism)))"}
{"candidate_id": "LLM05103", "doc_id": "NCT03537924_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((Healthy) AND (Kyrgyz ethnicity) AND (Written informed consent.) AND (age 40-75 yrs) AND (any disease) AND (living at <800m) AND (living at low altitude) AND (medication need of) AND (men) AND (women))"}
{"candidate_id": "LLM05104", "doc_id": "NCT03190304_exc", "case_bucket": "or", "source_criterion": "History of hypersensitivity or allergy to any of the study drugs, drugs of similar chemical classes, ACE inhibitors (ACEIs), angiotensin II receptor blockers (ARBs), or neprilysin inhibitors, as well as known or suspected contraindications to the study drugs. Previous history of intolerance to recommended target doses of ACEIs or ARBs. Known history of angioedema. Requirement for treatment with both ACEIs and ARBs. Current acute decompensated heart failure (exacerbation of chronic heart failure manifested by signs and symptoms that may require intravenous therapy). Symptomatic hypotension. Estimated glomerular filtration rate (eGFR) <30%. Serum potassium >5.4 mmol/L. Acute coronary syndrome, stroke, transient ischaemic attack, cardiac, carotid, or other major cardiovascular surgery, percutaneous coronary intervention, or carotid angioplasty within the 3 months. Coronary or carotid artery disease likely to require surgical or percutaneous intervention within the 6 months. Implantation of a cardiac resynchronization therapy (CRT) device within 3 months or intent to implant a CRT. History of heart transplant or on a transplant list or with left ventricular (LV) assistance device. History of severe pulmonary disease. Diagnosis of peripartum- or chemotherapy-induced cardiomyopathy within the 12 months. Documented untreated ventricular arrhythmia with syncopal episodes within the 3 months. Symptomatic bradycardia or second- or third-degree atrioventricular block without a pacemaker. Presence of haemodynamically significant mitral and/or aortic valve disease, except mitral regurgitation secondary to LV dilatation. Presence of other haemodynamically significant obstructive lesions of the LV outflow tract, including aortic and subaortic stenosis. Any surgical or medical condition which might significantly alter the absorption, distribution, metabolism, or excretion of study drugs, including, but not limited to, any of the following: History of active inflammatory bowel disease during the 12 months. Active duodenal or gastric ulcers during the 3 months. Evidence of hepatic disease as determined by any one of the following: aspartate aminotransferase or alanine aminotransferase values exceeding 2x upper limit of normal, history of hepatic encephalopathy, history of oesophageal varices, or history of porto-caval shunt. Current treatment with cholestyramine or colestipol resins. Presence of any other disease with a life expectancy of <5 years.", "candidate_expression": "((CRT) AND (Estimated glomerular filtration rate (eGFR) <30%) AND (LV dilatation) AND (Serum potassium >5.4 mmol/L) AND (alter the absorption, distribution, metabolism, or excretion) AND (angioedema history) AND (cardiac resynchronization therapy (CRT) device) AND (cardiomyopathy within the 12 months) AND (chemotherapy) AND (chronic heart failure) AND (contraindications) AND (disease any other life expectancy) AND (exacerbation) AND (heart failure acute decompensated) AND (hepatic disease Evidence) AND (hypotension Symptomatic) AND (inflammatory bowel disease active during the 12 months) AND (intolerance Previous history) AND (intravenous therapy) AND (peripartum) AND (severe pulmonary disease History) AND (signs) AND (study drugs) AND (symptoms) AND (syncopal episodes within the 3 months) AND (treatment Current) AND (treatment Requirement for) AND (ventricular arrhythmia untreated) AND NOT (pacemaker) AND NOT (mitral regurgitation secondary to LV dilatation) AND ((haemodynamically significant) OR (obstructive lesions LV outflow tract)) AND ((aortic stenosis) OR (subaortic stenosis)) AND ((medical condition) OR (surgical condition)) AND ((duodenal ulcers) OR (gastric ulcers)) AND ((alanine aminotransferase) OR (aspartate aminotransferase)) AND ((hepatic encephalopathy history) OR (oesophageal varices history) OR (porto-caval shunt history)) AND ((cholestyramine resins) OR (colestipol resins)) AND ((ACEIs) OR (ARBs)) AND ((allergy) OR (hypersensitivity)) AND ((Acute coronary syndrome) OR (cardiac) OR (carotid) OR (stroke) OR (transient ischaemic attack)) AND ((ACE inhibitors (ACEIs)) OR (angiotensin II receptor blockers (ARBs)) OR (neprilysin inhibitors) OR (study drugs)) AND ((carotid angioplasty) OR (major cardiovascular surgery) OR (percutaneous coronary intervention)) AND ((Coronary artery disease) OR (carotid artery disease)) AND ((percutaneous intervention) OR (surgical intervention)) AND ((Implantation within 3 months) OR (implant intent)) AND ((heart transplant History) OR (left ventricular (LV) assistance device) OR (on a transplant list)) AND ((chemotherapy-induced) OR (peripartum- induced)) AND ((atrioventricular block) OR (bradycardia)) AND ((second- degree) OR (third-degree)) AND ((known) OR (suspected)) AND ((aortic valve disease) OR (mitral valve disease)))"}
{"candidate_id": "LLM05105", "doc_id": "NCT02755701_inc", "case_bucket": "or", "source_criterion": "Age = 19 and = 70 years; Presence of liver cirrhosis Serum albumin level = 3.5g/dl, ultrasound or CT scan confirmed ascites (=Grade 1) No administration of diuretics and BCAA within the past 1 week Voluntary consent to take part in this trial", "candidate_expression": "((= 19 and = 70 years) AND (= 3.5g/dl) AND (Age) AND (BCAA) AND (CT scan) AND (Grade 1) AND (No) AND (Serum albumin) AND (Voluntary consent to take part in this trial) AND (ascites) AND (diuretics) AND (liver cirrhosis) AND (past 1 week) AND (ultrasound))"}
{"candidate_id": "LLM05106", "doc_id": "NCT02833623_inc", "case_bucket": "or", "source_criterion": "outpatients aged 18-70 years confirmed diagnosis of H. pylori infection by at least one of the following methods: 13C-urea breath test, histology, rapid urease test or bacterial culture an intention of H. pylori eradication treatment and have written inform consent ability to read short messages on the mobile phone", "candidate_expression": "((13C-urea breath test) AND (18-70 years) AND (H. pylori infection) AND (ability to read short messages on the mobile phone) AND (aged) AND (an intention of H. pylori eradication treatment and have written inform consent) AND (bacterial culture) AND (histology) AND (outpatients) AND (rapid urease test))"}
{"candidate_id": "LLM05107", "doc_id": "NCT00324363_exc", "case_bucket": "or", "source_criterion": "Have participated in this study previously, or any other study using exenatide or GLP-1 analogs. Have participated in an interventional, medical, surgical, or pharmaceutical study within 30 days of screening. Have characteristics contraindicating metformin or sulfonylurea use. Have been treated with exogenous insulin for more than 1 week within the 3 months prior to screening. Have used drugs for weight loss within 1 month of screening.", "candidate_expression": "((characteristics contraindicating) AND (drugs for weight loss) AND (exogenous insulin) AND (for more than 1 week) AND (screening) AND (within 1 month of screening) AND (within 30 days of screening) AND (within the 3 months prior to screening) AND ((GLP-1 analogs) OR (exenatide)) AND ((metformin) OR (sulfonylurea)) AND ((any other study) OR (this study)) AND ((interventional study) OR (medical study) OR (pharmaceutical study) OR (surgical study)))"}
{"candidate_id": "LLM05108", "doc_id": "NCT02818816_inc", "case_bucket": "other", "source_criterion": "Males aged 18 years and above Patients with a diagnosis of prostatic carcinoma requiring prostate surgery", "candidate_expression": "((Males) AND (aged 18 years and above) AND (prostate surgery) AND (prostatic carcinoma))"}
{"candidate_id": "LLM05109", "doc_id": "NCT02254668_inc", "case_bucket": "other", "source_criterion": "Patients with heart transplantation Patient with coronary artery disease Age between 18 and 80 years", "candidate_expression": "((Age) AND (between 18 and 80 years) AND (coronary artery disease) AND (heart transplantation))"}
{"candidate_id": "LLM05110", "doc_id": "NCT02621541_exc", "case_bucket": "or", "source_criterion": "vulnerable study subjects such as described in Finnish law concerning clinical studies (disabled, children, pregnant or breast-feeding women, prisoners) will not be included.", "candidate_expression": "((breast-feeding) AND (children) AND (disabled) AND (pregnant) AND (prisoners) AND (vulnerable Finnish law concerning clinical studies) AND (women))"}
{"candidate_id": "LLM05111", "doc_id": "NCT02035800_exc", "case_bucket": "other", "source_criterion": "Patients not capable or willing to provide informed consent Patients starting Adalimumab less than five half-lives after the interruption of a previous anti-TNF therapy.", "candidate_expression": "((Adalimumab) AND (anti-TNF therapy) AND (less than five half-lives after the interruption of a previous anti-TNF therapy) AND (previous) AND (the interruption of a previous anti-TNF therapy))"}
{"candidate_id": "LLM05112", "doc_id": "NCT02141061_inc", "case_bucket": "other", "source_criterion": "1. Speak, read, and understand English or Spanish and is willing and able to provide written informed consent on an IRB-approved form prior to the initiation of any study procedures; 2. Healthy, premenopausal female age 18-47; 3. History of menstrual events that occur in regular cycles 4. Agreement not to attempt to become pregnant 5. Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication. Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide; 6. Has a negative pregnancy test at the Screening visit. An exception for the pregnancy test requirement will be granted for subjects reporting surgical sterilization in medical history 7. Normal laboratory values or clinically insignificant findings at screening as determined by the Investigator; 8. Subject is willing to remain in the clinic overnight for PK assessment on Days 0 and 8 9. Ability to complete the study procedures in compliance with the protocol.", "candidate_expression": "((18-47) AND (Ability to complete the study procedures in compliance with the protocol.) AND (Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide;) AND (Agreement not to attempt to become pregnant) AND (Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication.) AND (Healthy) AND (History) AND (Normal) AND (Normal laboratory values) AND (Screening visit) AND (age) AND (as determined by the Investigator) AND (at screening) AND (at the Screening visit) AND (clinically insignificant) AND (female) AND (findings) AND (laboratory) AND (menstrual events that occur in regular cycles) AND (negative) AND (pregnancy test) AND (premenopausal) AND (screening))"}
{"candidate_id": "LLM05113", "doc_id": "NCT02357654_inc", "case_bucket": "or", "source_criterion": "women undergoing IVF/ICSI or frozen embryo transfers (FET) that less than 40 years old.", "candidate_expression": "((old less than 40 years) AND (women) AND ((ICSI) OR (IVF) OR (frozen embryo transfers (FET))))"}
{"candidate_id": "LLM05114", "doc_id": "NCT02201316_inc", "case_bucket": "or", "source_criterion": "Male and females aged between 18 and 65 years of age inclusive, at the time of signing the informed consent. Healthy as determined by a responsible and experienced physician, based on a medical evaluation including medical history, physical examination, laboratory tests and cardiac monitoring. A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedures. Body weight >= 50 kilogram (kg) and body mass index within the range 19 - 24.9 kg/m^2 (inclusive). A female subject is eligible to participate if she is of: Non-childbearing potential defined as pre-menopausal females with a documented tubal ligation or hysterectomy for this definition, \"documented\" refers to the outcome of the investigator's/designee's review of the subject's medical history for study eligibility, as obtained via a verbal interview with the subject or from the subject's medical records; or postmenopausal defined as 12 months of spontaneous amenorrhea [in questionable cases a blood sample with simultaneous follicle stimulating hormone (FSH) > 40 milli-international units per milliliter (MlU/mL) and estradiol < 40 picograms per mililiter (pg/mL) [<147 picomole per liter] is confirmatory]. Females on hormone replacement therapy (HRT) and whose menopausal status is in doubt will be required to use one of the contraception methods if they wish to continue their HRT during the study. Otherwise, they must discontinue HRT to allow confirmation of post-menopausal status prior to study enrollment. For most forms of HRT, at least 2-4 weeks will elapse between the cessation of therapy and the blood draw; this interval depends on the type and dosage of HRT. Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point. Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle. Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol. This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit. Capable of giving written informed consent, which includes compliance with the requirements and restrictions listed in the consent form Alanine aminotransferase, alkaline phosphatase and bilirubin <=1.5x upper limit of normal (ULN) (isolated bilirubin >1.5xULN is acceptable if bilirubin is fractionated and direct bilirubin <35%). Based on single or averaged corrected QT interval (QTc) values of triplicate electrocardiograms obtained over a brief recording period: QTcF < 450 msec", "candidate_expression": "((A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedur) AND (Alanine aminotransferase) AND (Body weight >= 50 kilogram (kg)) AND (Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle.) AND (Females) AND (Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point.) AND (Healthy medical history as determined by a responsible and experienced physician) AND (Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol.) AND (This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit.) AND (alkaline phosphatase) AND (as determined by a responsible and experienced physician) AND (bilirubin) AND (bilirubin >1.5xULN) AND (body mass index within the range 19 - 24.9 kg/m^2) AND (cardiac monitoring) AND (clinical abnormality) AND (direct bilirubin) AND (electrocardiograms over a brief recording period) AND (estradiol < 40 picograms per mililiter (pg/mL) <147 picomole per liter) AND (female) AND (females) AND (follicle stimulating hormone (FSH) > 40 milli-international units per milliliter (MlU/mL)) AND (hormone replacement therapy (HRT)) AND (laboratory parameter outside the reference range) AND (laboratory tests) AND (medical evaluation) AND (menopausal status in doubt) AND (physical examination) AND (postmenopausal) AND (pre-menopausal) AND (spontaneous amenorrhea 12 months) AND ((QTcF < 450 msec) AND (corrected QT interval (QTc) < 450 msec)) AND NOT (childbearing potential) AND ((Male) OR (females)) AND ((hysterectomy) OR (tubal ligation)) AND ((age between 18 and 65 years) OR (aged between 18 and 65 years)) AND ((averaged) OR (single)))"}
{"candidate_id": "LLM05115", "doc_id": "NCT03464552_inc", "case_bucket": "other", "source_criterion": "Females 18-65 years old who undergoing colposcopic directed biopsy", "candidate_expression": "((18-65 years) AND (Females) AND (colposcopic directed biopsy) AND (old) AND (undergoing))"}
{"candidate_id": "LLM05116", "doc_id": "NCT02858180_inc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection of Genotype 1, 4, 5, or 6 HCV RNA > 103 IU/mL at screening 18 years of age or older Diagnosis of chronic HCV infection, defined as positive HCV antibody or HCV RNA more than 6 months prior to screening OR an assessment of fibrosis F2 or greater prior to screening. NYHA Class III: Subjects with cardiac disease resulting in marked limitation of physical activity. They are comfortable at rest. Less than ordinary physical activity causes fatigue, palpitation, dyspnea, or anginal pain. NYHA Class IV: Patient with cardiac disease resulting in inability to carry on any physical activity without discomfort. Symptoms of cardiac insufficiency or of the anginal syndrome may be present even at rest. If any physical activity is undertaken, discomfort is increased. ejection fraction = 30% hospitalized for heart failure in last 12 months ILD criteria: diagnosis of interstitial lung disease with chronic supplemental oxygen requirement at rest and/or with exertion. Forced expiratory volume (FEV1)< 30% predicted OR any FEV1 with chronic supplemental oxygen requirement at rest and/or with exertion OR any FEV1 with chronic hypercapnia (baseline partial pressure of arterial carbon dioxide [PaCO2] > 45)", "candidate_expression": "((Chronic HCV Infection) AND (FEV1) AND (Forced expiratory volume < 30% predicted) AND (HCV RNA > 103 IU/mL at screening) AND (ILD criteria) AND (NYHA Class III) AND (NYHA Class IV) AND (PaCO2) AND (age older 18 years) AND (assessment of fibrosis F2 or greater prior to screening) AND (chronic HCV infection) AND (chronic hypercapnia) AND (chronic supplemental oxygen requirement) AND (ejection fraction = 30%) AND (heart failure) AND (hospitalized in last 12 months) AND (interstitial lung disease) AND (partial pressure of arterial carbon dioxide > 45) AND ((HCV RNA more than 6 months prior to screening) OR (HCV antibody positive more than 6 months prior to screening)) AND ((Genotype 1) OR (Genotype 4) OR (Genotype 5) OR (Genotype 6)) AND ((at rest) OR (with exertion)))"}
{"candidate_id": "LLM05117", "doc_id": "NCT03181984_inc", "case_bucket": "other", "source_criterion": "Age range: 14 to 65 years-old; Clinically diagnosed of Port-wine Stain; Patients receiving hemoporfin based upon the clinical judgment of the investigator; Written informed consent signed and agreed to receive periodic follow-up", "candidate_expression": "((14 to 65 years-old) AND (Age) AND (Port-wine Stain) AND (Written informed consent signed and agreed to receive periodic follow-up) AND (hemoporfin))"}
{"candidate_id": "LLM05118", "doc_id": "NCT02969876_inc", "case_bucket": "or", "source_criterion": "Meets Diagnostic and Statistical Manual of Mental Disorders (Versions 4 and 5) criteria for and Major Depressive Disorder. Hamilton Depression Rating Scale-17 score greater than 18. Men and women between ages >=18 and 65.", "candidate_expression": "((Diagnostic and Statistical Manual of Mental Disorders criteria) AND (Hamilton Depression Rating Scale) AND (Major Depressive Disorder) AND (ages) AND (between 18 and 65) AND (greater than 18) AND ((Men) OR (women)) AND ((Versions 4) OR (Versions 5)))"}
{"candidate_id": "LLM05119", "doc_id": "NCT03337503_inc", "case_bucket": "or", "source_criterion": "Written informed consent Adult patients (older than 18 years of age), male and female, with chronic non-cancer and cancer pain (at least 3 months in duration) Patients experiencing an average weekly pain intensity score greater than 4 on a 11 points NRS Subject agreed to follow the protocol Naïve cannabis patients with chronic non-cancer and cancer pain (not used cannabis in any presentation in the last 12 weeks) Patients receiving opioids and other concomitant pain medications should have a stable dose for the last 15 days. Normal cognitive status according to MiniCog Normal liver function (defined as aspartate aminotransferase 10-40 U/L and alanine aminotransferase 7-56 U/L) Normal renal function (defined as serum creatinine level <133 µmol/L and Estimated Glomerular Filtration Rate (eGFR) greater than or equal to 60) Negative result on ßhuman chorionic gonadotropin pregnancy test (if applicable) Ability to read and respond to questions in French or English. A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.", "candidate_expression": "((A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.) AND (Adult) AND (Estimated Glomerular Filtration Rate (eGFR) greater than or equal to 60 Negative) AND (MiniCog) AND (Naïve cannabis non-cancer) AND (Normal cognitive status) AND (Normal liver function) AND (Normal renal function) AND (Subject agreed to follow the protocol) AND (Written informed consent) AND (age older than 18 years) AND (alanine aminotransferase 7-56 U/L) AND (aspartate aminotransferase 10-40 U/L) AND (average weekly pain intensity score on a 11 points NRS greater than 4) AND (cannabis in the last 12 weeks) AND (female non-cancer) AND (male) AND (not) AND (opioids) AND (pain chronic cancer) AND (pain chronic cancer at least 3 months in duration) AND (pain medications other) AND (serum creatinine level <133 µmol/L) AND (ßhuman chorionic gonadotropin pregnancy test))"}
{"candidate_id": "LLM05120", "doc_id": "NCT00787254_inc", "case_bucket": "or", "source_criterion": "The patient was on nonsteroid anti-inflammatory drug (NSAID) treatment on the day when consent was obtained, and requires the long-term continuous treatment even after treatment with the investigational drug is started. The patient was confirmed to have a history of gastric ulcer or duodenal ulcer.", "candidate_expression": "((consent) AND (duodenal ulcer) AND (gastric ulcer) AND (nonsteroid anti-inflammatory drug (NSAID) on the day when consent was obtained))"}
{"candidate_id": "LLM05121", "doc_id": "NCT01770340_exc", "case_bucket": "or", "source_criterion": "IIEF < 21 Operations in the past 6 months which could limit the erectile function Erectile dysfunction in the history or current medication for erectile dysfunction Current involvement in another comparable study.", "candidate_expression": "((< 21) AND (Current involvement in another comparable study.) AND (IIEF) AND (Operations) AND (current) AND (erectile dysfunction) AND (history) AND (in the past 6 months) AND (limit the erectile function) AND ((Erectile dysfunction) OR (medication)))"}
{"candidate_id": "LLM05122", "doc_id": "NCT02804646_inc", "case_bucket": "or", "source_criterion": "1) histologically confirmed (patients not receiving a single sputum cytology diagnosis) non-small cell lung cancer patients,with wild-type EGFR and ALK-negative; 2) According to IASLC2009 new TNM staging of lung cancer stage <U+2162>B or <U+2163>, previously untreated or relapsed after 1 year of lung cancer resection; 3) have at least one evaluable lesions,according to version 1.1 of the standard in accordance with a judgment RECIST(longest diameter on a spiral CT at least 10mm,on a regular CT longest diameter at least 20mm); 4) Male or female, aged 18 to 75 years; 5) ECOG PS 0 or 1; 6) expected survival at least 3 months; 7) adequate hematological function: absolute neutrophil count (ANC) at least 2×10^9/L and platelet count at least 100×10^9/L and hemoglobin at least 9 g/dL; 8) adequate liver function: total bilirubin less than upper limit of normal (ULN); AST and ALT less than 2.5 times upper limit of normal (ULN); alkaline phosphatase less than 5 times the upper limit of normal (ULN); 9) adequate renal function: serum creatinine less than upper limit of normal (ULN) or calculated creatinine clearance at least 60 mL/min; 10) ECG is normal, there is no non-healing wounds on the body; 11) had not received previous treatment anticancer drugs, or had only received for previous non-metastatic tumors adjuvant or neoadjuvant chemotherapy, but when you start to study treatment has ended more than 6 months; 12) have conducted previous surgery patients required to study treatment was started more than four weeks, and the patient had recovered; 13) have an intact uterus in women prior to enrollment in the study must have a negative pregnancy test result (unless it is already 24 months of amenorrhea) within 28 days. If the pregnancy test from the first administration more than seven days, urine pregnancy test is required for authentication (less than 7 days before the first dose); 14) previous to biological agents, particularly E.coli genetically engineered products without serious allergic reactions; 15) signed informed consent.", "candidate_expression": "((ALT less than 2.5 times upper limit of normal (ULN)) AND (AST less than 2.5 times upper limit of normal (ULN)) AND (ECG normal) AND (ECOG PS 0 or 1) AND (IASLC2009 new TNM staging stage <U+2162>B or <U+2163>) AND (absolute neutrophil count (ANC) at least 2×10^9/L) AND (adequate hematological function) AND (adequate liver function) AND (adequate renal function) AND (aged 18 to 75 years) AND (alkaline phosphatase less than 5 times the upper limit of normal (ULN)) AND (evaluable lesions at least one) AND (expected survival at least 3 months) AND (have an intact uterus in women prior to enrollment in the study must have a negative pregnancy test result (unless it is already 24 months of amenorrhea) within 28 days. If the pregnancy test from the first administration more than seven days, urine pregnancy test is required for authentication (less than 7 days before the first dose);) AND (hemoglobin at least 9 g/dL) AND (longest diameter at least 10mm) AND (longest diameter at least 20mm) AND (lung cancer after 1 year of lung cancer resection) AND (non-metastatic tumors previous) AND (non-small cell lung cancer histologically confirmed wild-type EGFR ALK-negative) AND (platelet count at least 100×10^9/L) AND (regular CT) AND (spiral CT) AND (total bilirubin less than upper limit of normal (ULN)) AND NOT (non-healing wounds on the body) AND ((Male) OR (female)) AND ((calculated creatinine clearance at least 60 mL/min) OR (serum creatinine less than upper limit of normal (ULN))) AND ((adjuvant) OR (neoadjuvant)) AND ((chemotherapy ended more than 6 months) OR NOT (anticancer drugs)) AND ((relapsed) OR (untreated)))"}
{"candidate_id": "LLM05123", "doc_id": "NCT02689817_inc", "case_bucket": "other", "source_criterion": "Patients undergoing an operation that is scheduled to last more than 2 hours", "candidate_expression": "((last more than 2 hours) AND (operation) AND (scheduled to last more than 2 hours))"}
{"candidate_id": "LLM05124", "doc_id": "NCT03187379_inc", "case_bucket": "other", "source_criterion": "bariatric surgery patients laparoscopic roux-en-y gastric bypass use of EEA stapler anastomosis", "candidate_expression": "((EEA stapler anastomosis) AND (bariatric surgery) AND (laparoscopic) AND (roux-en-y gastric bypass))"}
{"candidate_id": "LLM05125", "doc_id": "NCT03063866_inc", "case_bucket": "or", "source_criterion": "Patients aged between 40 and 60 years old. With Child score B or C Presented for elective gastrointestinal endoscopy", "candidate_expression": "((Child score) AND (aged between 40 and 60 years old) AND (gastrointestinal endoscopy elective) AND ((B) OR (C)))"}
```
