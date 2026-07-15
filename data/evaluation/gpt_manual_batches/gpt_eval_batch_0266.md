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
{"candidate_id": "LLM06626", "doc_id": "NCT03199560_exc", "case_bucket": "or", "source_criterion": "Women under the age of 18, Clinically positive axillary nodes Neoadjuvant therapy for current breast cancer diagnosis Women with previous SLNBx or axillary node dissection Pregnant women Women with previous radiation above the diaphragm, and below the neck", "candidate_expression": "((Neoadjuvant therapy) AND (Pregnant women) AND (Women) AND (age 18 under) AND (axillary nodes positive) AND (breast cancer) AND (radiation previous above the diaphragm below the neck) AND ((SLNBx) OR (axillary node dissection)))"}
{"candidate_id": "LLM06627", "doc_id": "NCT03208465_inc", "case_bucket": "or", "source_criterion": "Men or women at least 19 years of age Type 2 diabetes mellitus Stable coronary artery disease Global myocardial perfusion reserve (MPR) index < 2.5 The patient or guardian agrees to the study protocol and the schedule of clinical and dynamic SPECT follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site.", "candidate_expression": "((< 2.5) AND (Global myocardial perfusion reserve (MPR) index) AND (Men) AND (Stable) AND (Type 2 diabetes mellitus) AND (age) AND (at least 19 years) AND (coronary artery disease) AND (informed, written consent) AND (women))"}
{"candidate_id": "LLM06628", "doc_id": "NCT02885909_exc", "case_bucket": "other", "source_criterion": "incooperative for glucose monitor refusal of insulin pregnancy", "candidate_expression": "((glucose monitor) AND (incooperative) AND (insulin) AND (pregnancy) AND (refusal))"}
{"candidate_id": "LLM06629", "doc_id": "NCT03389061_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06630", "doc_id": "NCT00396734_exc", "case_bucket": "or", "source_criterion": "use more than 2g a day; 5 times a week to everyday Subjects who are diagnosed as suffering from psychotic illness according to DSM-IV (Axis 1)22, or with a history of CNS disease, a history of infection that might affect CNS (HIV, syphilis, cytomegalovirus, herpes), or a history of head injury with loss of consciousness,pregnant women.", "candidate_expression": "((5 times a week to everyday) AND (Axis 1) AND (CNS disease) AND (DSM-IV) AND (affect CNS) AND (head injury) AND (infection) AND (loss of consciousness) AND (more than 2g a day) AND ((HIV) OR (cytomegalovirus) OR (herpes) OR (syphilis)) AND ((history) OR (pregnant) OR (psychotic illness)))"}
{"candidate_id": "LLM06631", "doc_id": "NCT03198910_inc", "case_bucket": "or", "source_criterion": "Patients with pulmonary arterial hypertension (PAH) Patients with chronic thromboembolic pulmonary hypertension (CTEPH) All prevalent patients (diagnosed >12 month ago) with PAH or distal CTEPH who had a consultation at the PH centre in Zurich between November 2015 and November 2016)", "candidate_expression": "((>12 month ago) AND (CTEPH) AND (PAH) AND (Zurich) AND (between November 2015 and November 2016) AND (chronic thromboembolic pulmonary hypertension (CTEPH)) AND (consultation at the PH centre) AND (distal) AND (pulmonary arterial hypertension (PAH)))"}
{"candidate_id": "LLM06632", "doc_id": "NCT02859480_inc", "case_bucket": "other", "source_criterion": "Patients underwent percutaneous coronary intervention with drug-eluting stent;", "candidate_expression": "((drug-eluting stent) AND (percutaneous coronary intervention))"}
{"candidate_id": "LLM06633", "doc_id": "NCT03560310_inc", "case_bucket": "or", "source_criterion": "Written informed consent Age =18 years Has undergone first time isolated CABG due to an episode of acute coronary syndrome (STEMI, NSTEMI, unstable angina) within 6 weeks before surgery", "candidate_expression": "((=18 years) AND (Age) AND (NSTEMI) AND (STEMI) AND (Written informed consent) AND (acute coronary syndrome) AND (first time) AND (isolated CABG) AND (surgery) AND (unstable angina) AND (within 6 weeks before surgery))"}
{"candidate_id": "LLM06634", "doc_id": "NCT02584140_inc", "case_bucket": "or", "source_criterion": "Female at birth and identifies as female gender Age 18 years or older Able to understand and provide consent in English or Spanish HIV negative by 4th generation test (Ag/Ab test) or combination of enzymeimmunoassay (EIA) and HIV RNA Creatinine clearance = 60 ml/min (via Cockcroft-Gault formula) Condomless sex in the last 3 months with one or more male partners of unknown HIV status known to be at substantial risk of HIV infection (IDU, bisexual, sex for goods, recently incarcerated, from a country with HIV prevalence >1%, interpersonal Partner Violence); STI (rectal or vaginal gonorrhea or syphilis) diagnosis during the last 6 months. Previous post-exposure prophylaxis (PEP) use during the last 12 months. Has at least one HIV-infected sexual partner for =4 weeks. Sex for exchange of money, goods or services", "candidate_expression": "((18 years or older) AND (= 60 ml/min) AND (=4 weeks) AND (Able to understand and provide consent in English or Spanish) AND (Ag/Ab test) AND (Age) AND (Cockcroft-Gault formula) AND (Condomless sex) AND (Creatinine clearance) AND (EIA) AND (Female) AND (HIV 4th generation test) AND (HIV RNA) AND (HIV infection) AND (HIV-infected) AND (IDU) AND (PEP) AND (STI) AND (Sex for exchange of money, goods or services) AND (at birth) AND (at least one) AND (birth) AND (bisexual) AND (during the last 12 months) AND (during the last 6 months) AND (enzymeimmunoassay) AND (female) AND (from a country with HIV prevalence >1%) AND (gender) AND (in the last 3 months) AND (interpersonal Partner Violence) AND (male partners) AND (negative) AND (one or more) AND (post-exposure prophylaxis use) AND (recently incarcerated) AND (sex for goods) AND (sexual partner) AND (substantial risk of HIV infection) AND (unknown HIV status) AND ((rectal gonorrhea) OR (syphilis) OR (vaginal gonorrhea)))"}
{"candidate_id": "LLM06635", "doc_id": "NCT02550769_exc", "case_bucket": "other", "source_criterion": "Do not sign informed consent Pregnant patients Liver cirrhosis Undifferentiated adenocarcinoma. cT4 Metastatic disease (M1) chronic renal failure on dialysis ASA IV BMI <18 and> 35 kg / m2", "candidate_expression": "((ASA IV) AND (BMI <18 and> 35 kg / m2) AND (Do not sign informed consent) AND (Liver cirrhosis) AND (Metastatic disease (M1)) AND (Pregnant) AND (adenocarcinoma Undifferentiated) AND (cT4) AND (chronic renal failure) AND (dialysis))"}
{"candidate_id": "LLM06636", "doc_id": "NCT02141061_exc", "case_bucket": "or", "source_criterion": "1. Subject is a post-menopausal woman, defined as either; six (6) months or more (immediately prior to screening visit) without a menstrual period, or prior hysterectomy and/or oophorectomy 2. Subject is pregnant or lactating or is attempting or expecting to become pregnant during the study 3. Women with abnormally high liver enzymes or liver disease. (ALT or AST exceeding 2.0 x ULN AND total bilirubin exceeding 1.5 x ULN at screening and confirmed on repeat). 4. Received an investigational drug in the 30 days prior to the screening for this study 5. Women with a history of PCOS 6. Concurrent use of any testosterone, progestin, androgen, estrogen, anabolic steroids, DHEA or hormonal products for at least 2 weeks prior to screening and during the study. 7. Use of oral contraceptives in the preceding 2 weeks. Use of Depo-Provera® in the preceding 10 months. 8. Has an IUD in place 9. Women currently using narcotics 10. Women currently taking spironolactone 11. Infectious disease screen is positive for HIV or Hepatitis A, B or C. 12. Clinically significant abnormal findings on screening examination or any condition which in the opinion of the investigator would interfere with the participant's ability to comply with the study instructions or endanger the participant if she took part in the study", "candidate_expression": "((Depo-Provera® in the preceding 10 months) AND (IUD) AND (PCOS history) AND (Women) AND (investigational drug in the 30 days prior to the screening) AND (is attempting or expecting to become pregnant during the study) AND (narcotics) AND (oral contraceptives in the preceding 2 weeks) AND (post-menopausal) AND (spironolactone) AND (total bilirubin exceeding 1.5 x ULN at screening) AND (woman six (6) months or more) AND ((hysterectomy prior) OR (oophorectomy) OR NOT (menstrual period)) AND ((lactating) OR (pregnant)) AND ((liver disease) OR (liver enzymes high)) AND ((ALT) OR (AST)) AND ((DHEA) OR (anabolic steroids) OR (androgen) OR (estrogen) OR (hormonal products) OR (progestin) OR (testosterone)) AND ((HIV) OR (Hepatitis A) OR (Hepatitis B) OR (Hepatitis C)))"}
{"candidate_id": "LLM06637", "doc_id": "NCT01891513_exc", "case_bucket": "or", "source_criterion": "Failure to provide informed consent Inability to complete 400 m walk within 15 minutes without sitting or interpersonal assistance, as an indicator of disablement and likely inability to fully engage in the exercise intervention Primary indication for ACE inhibitor use, i.e. Congestive Heart Failure, CAD, diabetes Known hypersensitivity to ACE inhibitors Resistant hypertension, defined as BP > 140/90, despite the use of three or more anti-hypertensive drugs Office or average home SBP > 180 mm Hg or DBP > 110 mm Hg (Average home BP in any seven day period during trial) Primary renal disease Serum creatinine >2.5 mg/dL in men, or >2.0 mg/dL in women Serum potassium >5.0 molar equivalent/L Urinary protein > 1 on dipstick Abnormal liver enzymes (Aspartate transaminase (AST), Alanine transaminase (ALT), or alkaline phosphatase > 2.5 times the upper limit of normal) Severe cardiac disease, including New York Heart Association Class III or IV congestive heart failure, clinically significant aortic stenosis, history of cardiac arrest, use of a cardiac defibrillator, or uncontrolled angina Acute myocardial infarction identified by ECG Lives in a nursing home (persons living in assisted or independent housing will not be excluded) Significant cognitive impairment, defined as a known diagnosis of dementia or a Mini-Mental State Examination exam score < 24 Unable to communicate because of severe hearing loss or speech disorder Severe visual impairment, which would preclude completion of the assessments and/or intervention Other significant co-morbid disease that would prevent participation in exercise Planning to move out of the area during the study time frame Simultaneous participation in another intervention trial", "candidate_expression": "((> 1) AND (> 110 mm Hg) AND (> 140/90) AND (> 180 mm Hg) AND (> 2.5 times the upper limit of normal) AND (>2.0 mg/dL) AND (>2.5 mg/dL) AND (>5.0 molar equivalent/L) AND (ACE inhibitor) AND (ACE inhibitors) AND (Abnormal) AND (Acute myocardial infarction) AND (Alanine transaminase (ALT)) AND (Aspartate transaminase (AST)) AND (BP) AND (CAD) AND (Class III or IV) AND (Congestive Heart Failure) AND (DBP) AND (ECG) AND (Inability to complete 400 m walk within 15 minutes without sitting) AND (Lives in a nursing home) AND (Mini-Mental State Examination) AND (New York Heart Association) AND (New York Heart Association Class III or IV) AND (Primary indication for ACE inhibitor use) AND (Primary renal disease) AND (Resistant) AND (SBP) AND (Serum creatinine) AND (Serum potassium) AND (Severe) AND (Significant) AND (Unable to communicate) AND (Urinary protein on dipstick) AND (alkaline phosphatase) AND (anti-hypertensive drugs) AND (aortic stenosis) AND (cardiac arrest) AND (cardiac defibrillator) AND (cardiac disease) AND (clinically significant) AND (co-morbid disease) AND (cognitive impairment) AND (congestive heart failure) AND (dementia) AND (despite the use of three or more anti-hypertensive drugs) AND (diabetes) AND (history) AND (hypersensitivity to ACE inhibitors) AND (hypertension) AND (interpersonal assistance Inability to complete 400 m walk within 15 minutes without) AND (liver enzymes) AND (men) AND (score < 24) AND (severe hearing loss) AND (significant) AND (speech disorder) AND (that would prevent participation in exercise) AND (three or more) AND (uncontrolled angina) AND (visual impairment) AND (women))"}
{"candidate_id": "LLM06638", "doc_id": "NCT00461136_inc", "case_bucket": "scope", "source_criterion": "Male and/or female patients from 30-80 years of age with a diagnosis of Type 2 diabetes (WHO criteria). Incipient and established diabetic nephropathy (urinary albumin excretion ≥ 100 mg/day but ≤ 2000 mg/day). Glomerular filtration rate (GFR) ≥ 40 ml/min (estimated using Modification of Diet in Renal Disease (MDRD) formula) in the last 4 months. Female patients must be postmenopausal or must have had a bilateral oophorectomy or must have been surgically sterilized or hysterectomized at least 6 months prior to screening. To be eligible patients must fulfill the following criteria: Patients on ongoing hypertensive therapy must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1) AND patients must be on stable antihypertensive medications for at least 8 weeks prior to baseline (Day -1).; Newly diagnosed hypertensive patients must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1). Patients must be on stable hypoglycemic medications for at least 8 weeks prior to Visit 2 ( Day -1). Patients must be willing and medically able to discontinue all Angiotensin-converting enzyme inhibitor (ACEI), Angiotensin receptor blocker (ARB), aldosterone receptor antagonist and potassium sparing diuretic medications for the duration of the study. Oral body temperature within the range 35.0-37.5 °C Able to provide written informed consent prior to study participation. . Able to communicate well with the investigator and comply with the requirements of the study.", "candidate_expression": "((Able to communicate well) AND (Female) AND (Glomerular filtration rate (GFR) ≥ 40 ml/min Modification of Diet in Renal Disease (MDRD) formula in the last 4 months) AND (Oral body temperature 35.0-37.5 °C) AND (Type 2 diabetes) AND (antihypertensive medications stable at least 8 weeks prior to baseline) AND (bilateral oophorectomy) AND (blood pressure at baseline (Day -1) ≥ 135/85 mm Hg lower than 170/105 mm Hg) AND (blood pressure ≥ 135/85 mm Hg lower than 170/105 mm Hg) AND (comply with the requirements of the study) AND (diabetic nephropathy) AND (hypertensive patients Newly diagnosed) AND (hypertensive therapy) AND (hypoglycemic medications stable at least 8 weeks prior to Visit 2) AND (hysterectomized) AND (of age 30-80 years) AND (postmenopausal) AND (surgically sterilized) AND (urinary albumin excretion ≥ 100 mg/day ≤ 2000 mg/day) AND (written informed consent prior to study participation))"}
{"candidate_id": "LLM06639", "doc_id": "NCT00926523_exc", "case_bucket": "other", "source_criterion": "Subject are pregnant Subject is unable to perform tasks associated with study", "candidate_expression": "((Subject is unable to perform tasks associated with study) AND (pregnant))"}
{"candidate_id": "LLM06640", "doc_id": "NCT03211741_inc", "case_bucket": "or", "source_criterion": "Age = 18 years of either gender Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed Visual impairment predominantly due to abnormal new vessel ingrowth and/or macular edema. The presence of fluid (intraretinal, subretinal or sub-RPE) detected clinically or on the ocular coherence tomography.", "candidate_expression": "((= 18 years) AND (Age) AND (Visual impairment) AND (Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed) AND (either gender) AND (fluid) AND (ocular coherence tomography) AND ((abnormal new vessel ingrowth) OR (macular edema)) AND ((intraretinal) OR (sub-RPE) OR (subretinal)))"}
{"candidate_id": "LLM06641", "doc_id": "NCT01980680_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 40 Normal menstrual cycles: 25-34 days Oligomenorrhea/amenorrhea or polycystic syndrome (defined according to the Rotterdam criteria 2004) BMI >18 and <35 kg/m2", "candidate_expression": "((Age between 20 and 40) AND (BMI >18 and <35 kg/m2) AND (Normal menstrual cycles 25-34 days) AND ((Oligomenorrhea) OR (amenorrhea) OR (polycystic syndrome Rotterdam criteria 2004)))"}
{"candidate_id": "LLM06642", "doc_id": "NCT02689089_exc", "case_bucket": "or", "source_criterion": "Suspected or confirmed active TB disease Known allergies to any of the study medications by participant self-report have a positive pregnancy test at screening, or are not willing to use a reliable method of barrier contraception during the study, or are breastfeeding hormonal contraception HIV infected participants who are on anti-retroviral drugs other drugs that interact with 3HP (see Table 1) Known contact with an INH or rifampin resistant case Weight < 10 kg Evidence of possible liver damage defined by an aspartate transaminase (AST) level that is more than 3x the upper limit of normal in an asymptomatic patient Porphyria reported by patient Inability to adhere to protocol. Patients may be excluded from the study for other reasons, at the investigator's discretion with detailed documentation.", "candidate_expression": "((< 10 kg) AND (AST) AND (HIV infected) AND (Inability to adhere to protocol) AND (Porphyria) AND (Weight) AND (active TB) AND (allergies) AND (anti-retroviral drugs) AND (are breastfeeding) AND (are not willing to use a reliable method of barrier contraception during the study) AND (aspartate transaminase) AND (have a positive pregnancy test at screening) AND (hormonal contraception) AND (liver damage) AND (more than 3x the upper limit of normal) AND (resistant) AND ((INH) OR (rifampin)))"}
{"candidate_id": "LLM06643", "doc_id": "NCT03138577_inc", "case_bucket": "other", "source_criterion": "Undergoing right upper extremity surgery with supraclavicular block as the primary anesthetic Age greater than or equal to 18 years of age American Society of Anesthesiologists (ASA) physical status 1 to 3 Able to give informed consent", "candidate_expression": "((1 to 3) AND (Able to give informed consent) AND (Age) AND (American Society of Anesthesiologists (ASA) physical status) AND (Undergoing) AND (greater than or equal to 18 years) AND (primary anesthetic) AND (right upper extremity surgery) AND (supraclavicular block))"}
{"candidate_id": "LLM06644", "doc_id": "NCT01410890_inc", "case_bucket": "or", "source_criterion": "The patient and/or the patient's parent/legal guardian is willing and able to provide signed informed consent. The patient has a confirmed GAA enzyme deficiency from skin, blood, or muscle tissue and/or 2 confirmed GAA gene mutations. Infant and toddler Pompe disease patients can be included in the study only under condition (minimal body weight) that the trial-related blood loss (including any losses in the maneuver) will not exceed 3 percent of the total blood volume during a period of 4 weeks and will not exceed 1 percent at any single time. The patient, if female and of childbearing potential, must have a negative pregnancy test (urine beta-human chorionic gonadotropin) at screening. Note: All female patients of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study. For patients previously treated with alglucosidase alfa the patient has received alglucosidase alfa for at least 6 months.", "candidate_expression": "((2) AND (GAA enzyme deficiency) AND (GAA gene mutations) AND (Infant) AND (Pompe disease) AND (The patient and/or the patient's parent/legal guardian is willing and able to provide signed informed consent) AND (The patient, if female and of childbearing potential, must have a negative pregnancy test (urine beta-human chorionic gonadotropin) at screening. Note: All female patients of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study) AND (alglucosidase alfa) AND (blood) AND (for at least 6 months) AND (muscle tissue) AND (skin) AND (toddler))"}
{"candidate_id": "LLM06645", "doc_id": "NCT00894712_exc", "case_bucket": "or", "source_criterion": "Visible skin pathology, excessive freckles, or skin blemishes in the test area. History of skin disease or hypersensitivity and repeated contact allergies. Sarcoma or squamous cell histology. Metastatic disease to the breast. Current tobacco use.", "candidate_expression": "((Metastatic disease to the breast) AND (contact allergies) AND (histology) AND (hypersensitivity) AND (skin disease) AND (tobacco use Current) AND ((freckles excessive) OR (skin blemishes) OR (skin pathology)) AND ((Sarcoma) OR (squamous cell)))"}
{"candidate_id": "LLM06646", "doc_id": "NCT02396732_exc", "case_bucket": "or", "source_criterion": "Presence of VTE upon admission Pregnant or nursing Inability to give informed consent by patient or healthcare proxy Contraindication to enoxaparin Contraindication to aspirin Epidural or subdural hematoma Presence, or removal within the last 12 hours, of an epidural or spinal catheter, or recent (within the last 12 hours) epidural or spinal anesthesia/procedures", "candidate_expression": "((Contraindication) AND (Epidural hematoma) AND (Inability to give informed consent) AND (Inability to give informed consent by patient or healthcare proxy) AND (Pregnant) AND (Presence of a spinal catheter) AND (Presence of an epidural) AND (VTE) AND (aspirin) AND (enoxaparin) AND (epidural anesthesia) AND (nursing) AND (recent) AND (removal of a spinal catheter) AND (removal of an epidural) AND (spinal anesthesia) AND (subdural hematoma) AND (upon admission) AND (within the last 12 hours))"}
{"candidate_id": "LLM06647", "doc_id": "NCT02379156_exc", "case_bucket": "or", "source_criterion": "Evidence of sympathetic integrity below the lesion level by the skin axon-reflex vasodilatation (SkARV) test; Known allergies to midodrine hydrochloride; PMH of diagnosed heart, kidney, peripheral vascular, or cerebral vascular disease, or diabetes mellitus; Hypertension (BP>140/90 mmHg); Untreated thyroid disease; Acute illness or infection; Current smoker; Pregnancy.", "candidate_expression": "((>140/90 mmHg) AND (Acute) AND (BP) AND (Hypertension) AND (Pregnancy) AND (SkARV) AND (Untreated) AND (allergies) AND (below the lesion level) AND (midodrine hydrochloride) AND (smoker) AND (sympathetic integrity) AND (test skin axon-reflex vasodilatation) AND (thyroid disease) AND ((illness) OR (infection)) AND ((cerebral vascular disease) OR (diabetes mellitus) OR (heart disease) OR (kidney disease) OR (peripheral vascular, disease)))"}
{"candidate_id": "LLM06648", "doc_id": "NCT02541955_inc", "case_bucket": "other", "source_criterion": "Patient must meet 1987 ACR criteria Age > 18 years of age Baseline DAS28/Erythrocyte Sedimentation Rate (ESR) >=3.2 Stable concomitant Disease Modifying Anti-Rheumatic Drugs (DMARDs) Stable prednisone <10mg or equivalent Power Doppler score of >=10", "candidate_expression": "((1987 ACR criteria) AND (Age > 18 years of age) AND (DAS28/Erythrocyte Sedimentation Rate (ESR) Baseline >=3.2) AND (Disease Modifying Anti-Rheumatic Drugs (DMARDs) Stable concomitant) AND (Power Doppler score >=10) AND (prednisone Stable <10mg))"}
{"candidate_id": "LLM06649", "doc_id": "NCT03431831_inc", "case_bucket": "or", "source_criterion": "Overweight/Obese Adult patients (age 19 years -65) eligible based on WALI screening tool", "candidate_expression": "((Adult) AND (Obese) AND (Overweight) AND (WALI screening tool eligible) AND (age 19 years -65))"}
{"candidate_id": "LLM06650", "doc_id": "NCT02369211_exc", "case_bucket": "or", "source_criterion": "Chronic opiate use Liver disease (known history of hepatitis B or C, cirrhosis, nonalcoholic steatohepatitis, history of alcoholism, ALT/AST greater than 3 times upper limit of normal in the past 3 months) Allergy/hypersensitivity to acetaminophen Patients with baseline dementia Chronic diathesis Chronic kidney disease", "candidate_expression": "((Chronic) AND (Liver disease) AND (acetaminophen) AND (baseline) AND (dementia) AND (diathesis) AND (greater than 3 times upper limit of normal) AND (history) AND (in the past 3 months) AND (kidney disease) AND (opiate) AND ((ALT/AST) OR (alcoholism) OR (cirrhosis) OR (nonalcoholic steatohepatitis)) AND ((Allergy) OR (hypersensitivity)) AND ((hepatitis B) OR (hepatitis C)))"}
```
