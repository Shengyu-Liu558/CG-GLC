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
{"candidate_id": "LLM00101", "doc_id": "NCT03176316_exc", "case_bucket": "or", "source_criterion": "Pregnancy, age < 18, nursing, or documented allergy to naloxone", "candidate_expression": "((Pregnancy) AND (age < 18) AND (allergy) AND (naloxone) AND (nursing))"}
{"candidate_id": "LLM00102", "doc_id": "NCT02704234_exc", "case_bucket": "other", "source_criterion": "pregnancy menopause interstitial cystitis irritable bowel syndrome untreated vaginitis cervicitis pelvic inflammatory disease any other pelvic pathology causing pain concomitant physical therapy concomitant biofeedback concomitant massage additional acupuncture", "candidate_expression": "((acupuncture) AND (biofeedback concomitant) AND (cervicitis) AND (interstitial cystitis) AND (irritable bowel syndrome) AND (massage concomitant) AND (menopause) AND (pelvic inflammatory disease) AND (pelvic pathology causing pain) AND (physical therapy concomitant) AND (pregnancy) AND (untreated vaginitis))"}
{"candidate_id": "LLM00103", "doc_id": "NCT02862314_exc", "case_bucket": "or", "source_criterion": "pregnancy, patients under legal custody, patients without health insurance, patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter, moribund patients, situation in which the procalcitonin concentration could be increased without correlation to an infectious process (poly-traumatised patients, surgical interventions within the last 4 days, cardiorespiratory arrest, administration of anti-thymocyte globulin, immunodepressed patients (bone marrow transplant patients, patients with severe neutropenia), patients with an absolute indication for administration of antibiotics at the moment of ICU admission (meningitis, pneumonia) or a chronic infection for which long-term antibiotic treatment is necessary (endocarditis, osteo-articular infections, mediastinitis, deep abscesses, pneumocystis infection, toxoplasmosis, tuberculosis) patients with haemodynamic instability of septic origin or a respiratory insufficiency (defined by a ratio Pa02/Fi02 = 200 mmHg and PEP = 5 cmH2O)", "candidate_expression": "((= 200 mmHg) AND (= 5 cmH2O) AND (ICU) AND (PEP) AND (Pa02/Fi02) AND (anti-thymocyte globulin) AND (antibiotic treatment) AND (antibiotics) AND (cardiorespiratory arrest) AND (chronic infection) AND (deep abscesses) AND (endocarditis) AND (health insurance) AND (immunodepressed) AND (increased) AND (indication) AND (last 4 days) AND (legal custody) AND (long-term) AND (mediastinitis) AND (moribund) AND (osteo-articular infections) AND (patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter) AND (pneumocystis infection) AND (poly-traumatised) AND (pregnancy) AND (procalcitonin concentration) AND (septic) AND (surgical interventions) AND (toxoplasmosis) AND (tuberculosis) AND (without) AND ((bone marrow transplant) OR (severe neutropenia)) AND ((meningitis) OR (pneumonia)) AND ((espiratory insufficiency) OR (haemodynamic instability)))"}
{"candidate_id": "LLM00104", "doc_id": "NCT03190304_exc", "case_bucket": "or", "source_criterion": "History of hypersensitivity or allergy to any of the study drugs, drugs of similar chemical classes, ACE inhibitors (ACEIs), angiotensin II receptor blockers (ARBs), or neprilysin inhibitors, as well as known or suspected contraindications to the study drugs. Previous history of intolerance to recommended target doses of ACEIs or ARBs. Known history of angioedema. Requirement for treatment with both ACEIs and ARBs. Current acute decompensated heart failure (exacerbation of chronic heart failure manifested by signs and symptoms that may require intravenous therapy). Symptomatic hypotension. Estimated glomerular filtration rate (eGFR) <30%. Serum potassium >5.4 mmol/L. Acute coronary syndrome, stroke, transient ischaemic attack, cardiac, carotid, or other major cardiovascular surgery, percutaneous coronary intervention, or carotid angioplasty within the 3 months. Coronary or carotid artery disease likely to require surgical or percutaneous intervention within the 6 months. Implantation of a cardiac resynchronization therapy (CRT) device within 3 months or intent to implant a CRT. History of heart transplant or on a transplant list or with left ventricular (LV) assistance device. History of severe pulmonary disease. Diagnosis of peripartum- or chemotherapy-induced cardiomyopathy within the 12 months. Documented untreated ventricular arrhythmia with syncopal episodes within the 3 months. Symptomatic bradycardia or second- or third-degree atrioventricular block without a pacemaker. Presence of haemodynamically significant mitral and/or aortic valve disease, except mitral regurgitation secondary to LV dilatation. Presence of other haemodynamically significant obstructive lesions of the LV outflow tract, including aortic and subaortic stenosis. Any surgical or medical condition which might significantly alter the absorption, distribution, metabolism, or excretion of study drugs, including, but not limited to, any of the following: History of active inflammatory bowel disease during the 12 months. Active duodenal or gastric ulcers during the 3 months. Evidence of hepatic disease as determined by any one of the following: aspartate aminotransferase or alanine aminotransferase values exceeding 2x upper limit of normal, history of hepatic encephalopathy, history of oesophageal varices, or history of porto-caval shunt. Current treatment with cholestyramine or colestipol resins. Presence of any other disease with a life expectancy of <5 years.", "candidate_expression": "((<30%) AND (<5 years) AND (>5.4 mmol/L) AND (Active) AND (CRT) AND (Current) AND (Estimated glomerular filtration rate (eGFR)) AND (Evidence) AND (History) AND (LV dilatation) AND (LV outflow tract) AND (Previous) AND (Requirement for) AND (Serum potassium) AND (Symptomatic) AND (active) AND (acute) AND (alter the absorption, distribution, metabolism, or excretion) AND (angioedema) AND (any other) AND (cardiac resynchronization therapy (CRT) device) AND (cardiomyopathy) AND (chemotherapy) AND (chronic heart failure) AND (contraindications) AND (decompensated) AND (disease) AND (during the 12 months) AND (during the 3 months) AND (exacerbation) AND (exceeding 2x upper limit of normal) AND (except) AND (haemodynamically significant) AND (heart failure) AND (hepatic disease) AND (history) AND (hypotension) AND (inflammatory bowel disease) AND (intent) AND (intolerance) AND (intravenous therapy) AND (life expectancy) AND (likely) AND (mitral regurgitation) AND (pacemaker) AND (peripartum) AND (secondary to LV dilatation) AND (severe pulmonary disease) AND (signs) AND (study drugs) AND (symptoms) AND (syncopal episodes) AND (treatment) AND (untreated) AND (ventricular arrhythmia) AND (within 3 months) AND (within the 12 months) AND (within the 3 months) AND (within the 6 months) AND (without) AND ((haemodynamically significant) OR (obstructive lesions)) AND ((aortic stenosis) OR (subaortic stenosis)) AND ((medical condition) OR (surgical condition)) AND ((duodenal ulcers) OR (gastric ulcers)) AND ((alanine aminotransferase) OR (aspartate aminotransferase)) AND ((hepatic encephalopathy) OR (oesophageal varices) OR (porto-caval shunt)) AND ((cholestyramine resins) OR (colestipol resins)) AND ((ACEIs) OR (ARBs)) AND ((allergy) OR (hypersensitivity)) AND ((Acute coronary syndrome) OR (cardiac) OR (carotid) OR (stroke) OR (transient ischaemic attack)) AND ((ACE inhibitors (ACEIs)) OR (angiotensin II receptor blockers (ARBs)) OR (neprilysin inhibitors) OR (study drugs)) AND ((carotid angioplasty) OR (major cardiovascular surgery) OR (percutaneous coronary intervention)) AND ((Coronary artery disease) OR (carotid artery disease)) AND ((percutaneous intervention) OR (surgical intervention)) AND ((Implantation) OR (implant)) AND ((heart transplant) OR (left ventricular (LV) assistance device) OR (on a transplant list)) AND ((chemotherapy-induced) OR (peripartum- induced)) AND ((atrioventricular block) OR (bradycardia)) AND ((second- degree) OR (third-degree)) AND ((known) OR (suspected)) AND ((aortic valve disease) OR (mitral valve disease)))"}
{"candidate_id": "LLM00105", "doc_id": "NCT02613039_inc", "case_bucket": "other", "source_criterion": "Female subjects aged =/> 18 years and of reproductive age. Capacity to give consent for study participation, after being adequately informed of the aims, benefits, risks, time and motion of the study.", "candidate_expression": "((=/> 18 years) AND (Female) AND (aged) AND (reproductive age))"}
{"candidate_id": "LLM00106", "doc_id": "NCT02477280_exc", "case_bucket": "or", "source_criterion": "Affected by alcohol or drugs during the last month. Untreated severe comorbid psychiatric or somatic illness. Bloodpressure 150/95 or higher. Irregular pulse, or pulse 100 or higher. No counter indications according to the Medikinet pill. Concurrent clinical diagnosis that significantly could affect test performance. Concurrent prescription of medicines for ADHD or medicines that significantly could affect test performance.", "candidate_expression": "((100 or higher) AND (150/95 or higher) AND (ADHD) AND (Bloodpressure) AND (Irregular) AND (Untreated) AND (alcohol) AND (comorbid) AND (drugs) AND (illness psychiatric) AND (last month) AND (medicines) AND (pulse) AND (severe) AND (somatic illness))"}
{"candidate_id": "LLM00107", "doc_id": "NCT01446094_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Possible pregnancy (confirmed by urine test) Women who are breastfeeding Severe claustrophobia Inability to lie flat for 20-30 minutes (the anticipated amount of time to complete the MRI procedure) Individuals with cochlear implants Individuals with non-MRI compatible aneurysm clips Potential contraindications to regadenoson use due to: Contraindication to administration of Gadolinium (Gd) based contrast agents (GBCA):", "candidate_expression": "((20-30 minutes) AND (Contraindication) AND (Gadolinium (Gd) based contrast agents (GBCA)) AND (Inability to give informed consent) AND (Inability to lie flat) AND (MRI compatible) AND (Possible) AND (Severe) AND (Women) AND (amount of time to complete the MRI procedure) AND (aneurysm clips) AND (breastfeeding) AND (claustrophobia) AND (cochlear implants) AND (confirmed) AND (non) AND (pregnancy) AND (urine test))"}
{"candidate_id": "LLM00108", "doc_id": "NCT02923700_inc", "case_bucket": "or", "source_criterion": "patients affected by mono-lateral symptomatic knee articular degenerative pathology with history of chronic (for at least 4 months) pain or swelling; imaging findings of degenerative changes of the joint (osteoarthritis or chondropathy with Kellgren Lawrence Score from 0 to 3 at X-ray evaluation).", "candidate_expression": "((Kellgren Lawrence Score) AND (X-ray) AND (chronic) AND (degenerative changes) AND (for at least 4 months) AND (from 0 to 3) AND (imaging) AND (knee articular degenerative pathology) AND (mono-lateral) AND (symptomatic) AND ((chondropathy) OR (osteoarthritis)) AND ((pain) OR (swelling)))"}
{"candidate_id": "LLM00109", "doc_id": "NCT02339844_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria patients: Substance abuse on a daily basis during the last 3 month or patients fulfilling the criteria of ongoing substance abuse due to ICD-10/DSM-IV/V, Treatment with antidepressant during the last 30 days, Head injury with more than 5 minutes of unconsciousness, Patients involuntarily admitted or treated, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness Exclusion criteria controls: First degree relatives with psychiatric disease, Substance abuse during the last 3 month or positive screening of drugs in urine-sample, Head injury with more than 5 minutes of unconsciousness, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness", "candidate_expression": "((Components of metal) AND (First degree relatives) AND (Head injury) AND (ICD-10/DSM-IV/V) AND (Pacemaker) AND (Pregnancy) AND (Severe physical illness) AND (Substance abuse) AND (antidepressant) AND (controls) AND (daily basis) AND (during the last 3 month) AND (during the last 30 days) AND (involuntarily admitted) AND (involuntarily treated) AND (more than 5 minutes) AND (ongoing) AND (patients) AND (positive) AND (psychiatric disease) AND (screening of drugs) AND (substance abuse) AND (unconsciousness) AND (urine-sample))"}
{"candidate_id": "LLM00110", "doc_id": "NCT03106389_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00111", "doc_id": "NCT02332291_inc", "case_bucket": "or", "source_criterion": "Age 60 years or older. Current diagnosis of major depressive disorder (DSM-IV-TR), single episode, recurrent or chronic, without psychotic features, as detected by MINI and clinical exam. Minimum MADRS score = 15. Mini-Mental State Exam = 24. Fluent in English.", "candidate_expression": "((Age 60 years or older) AND (DSM-IV-TR single episode recurrent chronic) AND (MADRS score Minimum = 15) AND (MINI) AND (Mini-Mental State Exam = 24) AND (clinical exam) AND (major depressive disorder) AND NOT (psychotic features))"}
{"candidate_id": "LLM00112", "doc_id": "NCT02637453_inc", "case_bucket": "other", "source_criterion": "No response to more than one antiarrhythmic drug, or unwilling to receive long-term drug treatment. Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures. Aged 18-80 years.", "candidate_expression": "((Aged 18-80 years) AND (Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures.) AND (antiarrhythmic drug more than one) AND NOT (response))"}
{"candidate_id": "LLM00113", "doc_id": "NCT02734173_inc", "case_bucket": "other", "source_criterion": "HCV RNA evidence of HCV infection Documented history of chronic HCV RNA infection with Genotype 1 Able to provide informed consent Available for ongoing follow-up if required", "candidate_expression": "((Able to provide informed consent) AND (Available for ongoing follow-up if required) AND (Genotype 1) AND (HCV RNA) AND (HCV infection) AND (chronic HCV infection))"}
{"candidate_id": "LLM00114", "doc_id": "NCT03089086_exc", "case_bucket": "other", "source_criterion": "Previous anaphylaxis following any component of Bexsero vaccine Previous receipt of meningococcal B vaccine (Bexsero) Known pregnancy", "candidate_expression": "((Bexsero) AND (Bexsero vaccine) AND (anaphylaxis Previous) AND (meningococcal B vaccine Previous) AND (pregnancy))"}
{"candidate_id": "LLM00115", "doc_id": "NCT00198913_exc", "case_bucket": "or", "source_criterion": "type 1 diabetic or non-diabetic", "candidate_expression": "((non-diabetic) OR (type 1 diabetic))"}
{"candidate_id": "LLM00116", "doc_id": "NCT02596555_exc", "case_bucket": "or", "source_criterion": "Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond History of hypersensitivity to the investigational medicinal product or to any drug with similar chemical structure or to any excipient present in the pharmaceutical form of the investigational medicinal product Participation in another clinical trial during the present clinical trial or within the last three months Medical or psychological condition that would not permit completion of the trial or signing of informed consent Use of a fibrinolytic agent, surgical thrombectomy, interventional (catheter-directed) thrombus aspiration or lysis, or use of a cava filter to treat the index episode of PE Treatment with any therapeutically dosed anticoagulant for more than 48 hours prior to enrolment Need for long-term treatment with a low molecular weight heparin, vitamin K antagonists or NOAC, for an indication other than the index PE episode, or for antiplatelet agents except acetylsalicylic acid at a dosage =100 mg/day; Active bleeding or known significant bleeding risk (e.g., gastrointestinal ulcer, malignant neoplasms, injuries or recent surgeries of the brain, spinal cord or eyes, recent intracranial bleedings, known or suspected esophagus varices, aneurysms or intraspinal or intracranial vascular abnormalities) Artificial heart valves requiring treatment with an anticoagulant Renal insufficiency with estimated creatinine clearance <30 ml/min/1.73m2 Chronic liver disease with aminotransferase levels two times or more above the local upper limit of normal range Concomitant administration of strong inhibitors of P-glycoprotein like ketoconazole, cyclosporin, itraconazole or dronedarone Unwillingness or inability to adhere to treatment or to the follow-up visits Life expectancy less than 6 months", "candidate_expression": "((Artificial heart valves) AND (Chronic liver disease) AND (Life expectancy less than 6 months) AND (Medical or psychological condition that would not permit completion of the trial or signing of informed consent) AND (PE) AND (Participation in another clinical trial during the present clinical trial or within the last three months) AND (Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation) AND (Renal insufficiency) AND (Unwillingness or inability to adhere to treatment or to the follow-up visits) AND (Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond) AND (aminotransferase two times or more above the local upper limit of normal range) AND (anticoagulant) AND (anticoagulant therapeutically more than 48 hours prior to enrolment) AND (antiplatelet agents =100 mg/day;) AND (estimated creatinine clearance <30 ml/min/1.73m2) AND (inhibitors of P-glycoprotein) AND NOT (PE episode index) AND NOT (acetylsalicylic acid) AND ((cava filter) OR (fibrinolytic agent) OR (surgical thrombectomy,) OR (thrombus aspiration) OR (thrombus lysis)) AND ((NOAC) OR (low molecular weight heparin) OR (vitamin K antagonists)) AND ((Active bleeding) OR (bleeding risk significant)) AND ((brain) OR (eyes) OR (spinal cord)) AND ((aneurysms) OR (esophagus varices) OR (gastrointestinal ulcer) OR (injuries) OR (intracranial bleedings) OR (malignant neoplasms) OR (surgeries) OR (vascular abnormalities))) AND ((intracranial) OR (intraspinal)) AND ((cyclosporin) OR (dronedarone) OR (itraconazole) OR (ketoconazole)))"}
{"candidate_id": "LLM00117", "doc_id": "NCT01373684_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B (HBsAg positive > 6 months) HBeAg negative within six months prior to initiation of peginterferon alfa-2a HBV DNA < 200 IU/ml during nucleos(t)ide analogue (except Telbivudine) treatment within one month prior to initiation of peginterferon alfa-2a Compensated liver disease Age > 18 years Written informed consent", "candidate_expression": "((Age > 18 years) AND (Chronic hepatitis B) AND (HBV DNA < 200 IU/ml during nucleos(t)ide analogue (except Telbivudine) treatment within one month prior to initiation of peginterferon alfa-2a) AND (HBeAg negative within six months prior to initiation of peginterferon alfa-2a) AND (HBsAg positive > 6 months) AND (Written informed consent) AND (liver disease Compensated) AND (nucleos(t)ide analogue) AND (peginterferon alfa-2a) AND NOT (Telbivudine))"}
{"candidate_id": "LLM00118", "doc_id": "NCT02664558_inc", "case_bucket": "or", "source_criterion": "1. Male or female, 18-75 years old. 2. Has a diagnosis of WHO Group 1 PAH. 3. Right heart catheterization performed at Screening with results that are: 1. Mean pulmonary arterial pressure ≥25 mmHg (at rest) and 2. Pulmonary venous hypertension (measured as pulmonary capillary wedge pressure (PCWP) ≤15 mmHg. If PCWP is not available, then mean left atrial pressure or left ventricular end-diastolic pressure ≤15 mmHg in the absence of left atrial obstruction. and 3. Pulmonary vascular resistance (PVR) ≥300 dyn•s/cm5 (3.75 Wood units) 4. Has WHO/NYHA-FC of II or III. 5. Be on stable dose of at least one of the following PAH-specific therapies: endothelin receptor antagonist, an agent acting on the nitric oxide pathway (phosphodiesterase type 5 inhibitor or soluble guanylate cyclase stimulator), and/or a prostacyclin or prostacyclin analog. 6. Has a 6-minute walk distance that is ≥150 and ≤500 meters. 7. Have a ventilation-perfusion scan that rules out thromboembolic disease.", "candidate_expression": "((1) AND (18-75 years) AND (3.75 Wood units) AND (6-minute walk distance) AND (II) AND (III) AND (Male) AND (Mean pulmonary arterial pressure) AND (PAH) AND (PAH-specific therapies) AND (Pulmonary vascular resistance (PVR)) AND (Pulmonary venous hypertension) AND (Right heart catheterization) AND (Screening) AND (WHO Group) AND (WHO/NYHA-FC) AND (absence) AND (agent acting on the nitric oxide pathway) AND (at least one) AND (at rest) AND (endothelin receptor antagonist) AND (female) AND (left atrial obstruction) AND (left ventricular end-diastolic pressure) AND (mean left atrial pressure) AND (performed at Screening) AND (phosphodiesterase type 5 inhibitor) AND (prostacyclin analog) AND (pulmonary capillary wedge pressure (PCWP)) AND (rules out) AND (soluble guanylate cyclase stimulator) AND (stable dose) AND (thromboembolic disease) AND (ventilation-perfusion scan) AND (years old) AND (≤15 mmHg) AND (≥150 and ≤500 meters) AND (≥25 mmHg) AND (≥300 dyn•s/cm5))"}
{"candidate_id": "LLM00119", "doc_id": "NCT02654912_inc", "case_bucket": "other", "source_criterion": "anyone not excluded and consenting", "candidate_expression": "(anyone not excluded and consenting)"}
{"candidate_id": "LLM00120", "doc_id": "NCT03097068_inc", "case_bucket": "other", "source_criterion": "Diagnosis of diabetes mellitus Best corrected visual acuity 20/32 - 20/320 Diabetic macular edema involving the center of the macula Optical coherence tomography central subfield thickness of at least 250 microns", "candidate_expression": "((20/32 - 20/320) AND (Best corrected visual acuity) AND (Diabetic macular edema) AND (Optical coherence tomography central subfield thickness) AND (at least 250 microns) AND (center of the macula) AND (diabetes mellitus))"}
{"candidate_id": "LLM00121", "doc_id": "NCT03247413_inc", "case_bucket": "or", "source_criterion": "patients with a diagnosis of either cervical, thoracic, or lumbar facet or sacroiliac joint pain who have responded to medial branch blocks and are already scheduled for bilateral radiofrequency ablations age greater than 18 years old English speaking", "candidate_expression": "((English speaking) AND (age) AND (bilateral radiofrequency ablations) AND (greater than 18 years old) AND (medial branch blocks) AND (responded) AND (scheduled for) AND ((cervical joint pain) OR (lumbar facet joint pain) OR (sacroiliac joint pain) OR (thoracic joint pain)))"}
{"candidate_id": "LLM00122", "doc_id": "NCT02571179_exc", "case_bucket": "or", "source_criterion": "a disease that might affect hepatic or renal function, contraindications to opioid analgesics, fetal growth retardation, signs of fetal asphyxia by cardiotocography, meconium stained amniotic fluid or placental insufficiency. The subjects should not have received fentanyl during the previous 14 days.", "candidate_expression": "((cardiotocography) AND (opioid analgesics) AND NOT (fentanyl during the previous 14 days) AND ((affect hepatic function) OR (affect renal function)) AND ((contraindications) OR (disease) OR (fetal asphyxia signs of) OR (fetal growth retardation) OR (meconium stained amniotic fluid) OR (placental insufficiency)))"}
{"candidate_id": "LLM00123", "doc_id": "NCT00324363_inc", "case_bucket": "or", "source_criterion": "Treated with a stable dose of one of the following for at least 3 months prior to screening: * >=1000 mg/day immediate-release metformin; or metformin >=1000 mg/day and sulfonylurea; or sulfonylurea/metformin combination therapy. HbA1c between 7.1% and 11.0%, inclusive. Body Mass Index (BMI) >21 kg/m^2 and <35 kg/m^2.", "candidate_expression": "((Body Mass Index (BMI) >21 kg/m^2 and <35 kg/m^2) AND (HbA1c between 7.1% and 11.0%, inclusive) AND (combination therapy) AND (immediate-release metformin >=1000 mg/day) AND (metformin) AND (metformin >=1000 mg/day) AND (sulfonylurea))"}
{"candidate_id": "LLM00124", "doc_id": "NCT00391690_exc", "case_bucket": "or", "source_criterion": "Prior treatment with a bisphosphonate Abnormal renal function as evidenced by a calculated creatinine clearance < 30 ml/minute. Corrected (adjusted for serum albumin) serum calcium concentration < 8.0 mg/dl (2.00 mmol/L) or ≥ 12.0 mg/dl (3.00 mmol/L). Patients with clinically symptomatic brain metastases History of diseases with influence on bone metabolism such as Paget's disease and primary hyperparathyroidism Severe physical or psychological concomitant diseases that might impair compliance with the provisions of the study protocol or that might impair the assessment of drug or patient safety, e.g. clinically significant ascites, cardiac failure, NYHA III or IV, clinically relevant pathologic findings in ECG Known hypersensitivity to zoledronic acid or other bisphosphonates Use of other investigational drugs 30 days prior to the date of randomization Known history or present abuse of alcohol or drugs Subjects who, in the opinion of the investigator, are unlikely to cooperate fully during the study Current active dental problems including infection of the teeth or jawbone (maxilla or mandibular); dental or fixture trauma, or a current or prior diagnosis of osteonecrosis of the jaw (ONJ), of exposed bone in the mouth, or of slow healing after dental procedures. Recent (within 6 weeks) or planned dental or jaw surgery (e.g. extraction, implants) Other protocol defined inclusion/exclusion criteria may apply.", "candidate_expression": "((30 days prior to the date of randomization) AND (< 30 ml/minute) AND (Abnormal) AND (Corrected serum calcium concentration) AND (Current) AND (History) AND (III or IV) AND (NYHA) AND (Prior) AND (bisphosphonate) AND (brain metastases) AND (calculated creatinine clearance) AND (clinically relevant) AND (clinically significant) AND (clinically symptomatic) AND (dental problems) AND (hypersensitivity) AND (other investigational drugs) AND (pathologic findings) AND (renal function) AND (within 6 weeks) AND ((Paget's disease) OR (diseases with influence on bone metabolism) OR (primary hyperparathyroidism)) AND ((physical diseases) OR (psychological diseases)) AND ((ECG) OR (ascites) OR (cardiac failure)) AND ((other bisphosphonates) OR (zoledronic acid)) AND ((history) OR (present)) AND ((abuse of alcohol) OR (abuse of drugs)) AND ((infection of the jawbone) OR (infection of the teeth)) AND ((infection of the mandibular) OR (infection of the maxilla)) AND ((dental trauma) OR (fixture trauma)) AND ((current) OR (prior)) AND ((exposed bone in the mouth) OR (osteonecrosis of the jaw (ONJ)) OR (slow healing after dental procedures)) AND ((Recent) OR (planned)) AND ((dental surgery) OR (jaw surgery)) AND ((extraction) OR (implants)) AND ((2.00 mmol/L) OR (3.00 mmol/L) OR (< 8.0 mg/dl) OR (≥ 12.0 mg/dl)))"}
{"candidate_id": "LLM00125", "doc_id": "NCT03213834_exc", "case_bucket": "or", "source_criterion": "age <18 years; Pregnancy inability to give informed written consent; previous thoracic surgery or thrombolytic therapy for pleural infection; medical thoracoscopy cannot be performed within 48 hours; inability to tolerate procedure due to hemodynamic instability or severe hypoxemia; inability to correct coagulopathy; presence of a homogeneously echogenic effusion on pleural US27 -", "candidate_expression": "((<18 years) AND (Pregnancy) AND (age) AND (cannot) AND (cannot be performed) AND (coagulopathy) AND (correct) AND (homogeneously echogenic effusion) AND (inability to) AND (inability to give informed written consent;) AND (inability to tolerate) AND (medical thoracoscopy) AND (pleural US) AND (pleural infection) AND (previous) AND (procedure) AND (severe) AND (within 48 hours) AND ((hemodynamic instability) OR (hypoxemia)) AND ((thoracic surgery) OR (thrombolytic therapy)))"}
```
