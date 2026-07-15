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
{"candidate_id": "LLM04226", "doc_id": "NCT02443844_exc", "case_bucket": "other", "source_criterion": "Patients who have previous prostate surgery Patients who have muscle invasive bladder cancer", "candidate_expression": "((bladder cancer muscle invasive) AND (prostate surgery previous))"}
{"candidate_id": "LLM04227", "doc_id": "NCT03084588_inc", "case_bucket": "other", "source_criterion": "All patients presenting for elective shoulder arthroscopic procedures will be eligible for enrollment.", "candidate_expression": "((elective) AND (shoulder arthroscopic procedures))"}
{"candidate_id": "LLM04228", "doc_id": "NCT03404479_inc", "case_bucket": "other", "source_criterion": "Subjects who voluntarily consented, after listening enough explanation for this study and investigational product. Adult over 50 years of age. At least one of the knee pain VAS score is 40mm or more. Patients who require medication for more than 12 weeks due to osteoarthritis symptoms. Those who are able to follow the requirements of this clinical trial, such as being able to trace during the clinical trial period and to read and write the VAS questionnaire. Those who weigh more than 40kg", "candidate_expression": "((40mm or more) AND (Adult) AND (At least one) AND (Subjects who voluntarily consented, after listening enough explanation for this study and investigational product.) AND (VAS score) AND (age) AND (knee pain) AND (medication) AND (more than 12 weeks) AND (more than 40kg) AND (osteoarthritis symptoms) AND (over 50 years) AND (weigh))"}
{"candidate_id": "LLM04229", "doc_id": "NCT02604459_inc", "case_bucket": "other", "source_criterion": "Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board, Hip fracture surgery scheduled under general anesthesia Subject is 65 years or older on the day of surgery", "candidate_expression": "((65 years or older) AND (Hip fracture surgery) AND (Subject or legal representative has voluntarily signed the informed consent approved by the Institutional Review Board,) AND (general anesthesia) AND (older) AND (on the day of surgery) AND (surgery) AND (the day of surgery))"}
{"candidate_id": "LLM04230", "doc_id": "NCT03500211_exc", "case_bucket": "or", "source_criterion": "Patients requiring emergent cesarean birth Patients allergic to lidocaine or adhesive Patients who have already received an epidural during this admission or requiring general anesthesia for cesarean birth Patients using chronic oral neuromodulators Patients with cardiac disease or using anti-arrhythmic agents Patients with fibromyalgia or chronic pain syndromes such as rheumatoid arthritis, osteoarthritis, or lupus. Daily narcotic or opiate use for greater than the 2 months prior to enrollment in the study.", "candidate_expression": "((allergic) AND (cesarean birth) AND (chronic oral neuromodulators) AND (emergent cesarean birth) AND ((anti-arrhythmic agents) OR (cardiac disease)) AND ((chronic pain syndromes) OR (fibromyalgia)) AND ((lupus) OR (osteoarthritis) OR (rheumatoid arthritis)) AND ((narcotic) OR (opiate)) AND ((adhesive) OR (lidocaine)) AND ((epidural during this admission) OR (general anesthesia requiring)))"}
{"candidate_id": "LLM04231", "doc_id": "NCT03360214_exc", "case_bucket": "or", "source_criterion": "Allergy to narcotic medications Intake of any chronic opioids or pain medications preoperatively", "candidate_expression": "((Allergy) AND (narcotic medications) AND ((opioids any chronic) OR (pain medications preoperatively)))"}
{"candidate_id": "LLM04232", "doc_id": "NCT01793831_exc", "case_bucket": "or", "source_criterion": "Diagnosis as CD first time or first year. No history of using 5-ASA, biological or immunomodulatory therapy", "candidate_expression": "((CD) AND ((first time) OR (first year)) AND ((5-ASA) OR (immunomodulatory therapy) OR (therapy biological)))"}
{"candidate_id": "LLM04233", "doc_id": "NCT00917891_inc", "case_bucket": "or", "source_criterion": "1. Women 18 to 40 years of age inclusive who can give written informed consent 2. Available for all visits and consent to follow all procedures scheduled for the study 3. Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method 4. Healthy and self-reported sexually active 5. HIV-negative as determined by a HIV rapid test at time of enrollment 6. On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment 7. In the absence of the use of exogenous hormone(s), have a self-reported regular menstrual cycle defined as having a minimum of 21 days and a maximum of 36 days between menses 8. Upon pelvic/speculum examination and colposcopy at the time of enrollment, the cervix and vagina appear normal as determined by the investigator 9. Asymptomatic for genital infections at the time of enrollment 10. Willing to refrain from use of vaginal products or objects within 14 days prior to enrollment and for the duration of the study 11. Willing to answer acceptability and adherence questionnaires throughout the study 12. Willing to refrain from participation in any other research study for the duration of this study 13. Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures", "candidate_expression": "((Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method) AND (Available for all visits and consent to follow all procedures scheduled for the study) AND (HIV negative) AND (HIV rapid test at time of enrollment time of enrollment) AND (HIV-negative) AND (Healthy) AND (On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment) AND (Willing to answer acceptability and adherence questionnaires throughout the study) AND (Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures) AND (Willing to refrain from participation in any other research study for the duration of this study) AND (Women) AND (acceptability questionnaires the study) AND (adherence questionnaires) AND (age 18 to 40 years) AND (as determined by the investigator) AND (can give written informed consent) AND (cervix normal) AND (enrollment) AND (gel daily) AND (genital infections Asymptomatic at the time of enrollment) AND (menstrual cycle regular) AND (monitoring daily) AND (regular menstrual cycle minimum of 21 days maximum of 36 days) AND (self-reported) AND (sexually active self-reported) AND (vagina normal normal) AND NOT (exogenous hormone) AND ((colposcopy) OR (pelvic examination) OR (speculum examination)) AND ((objects vaginal) OR (vaginal products)))"}
{"candidate_id": "LLM04234", "doc_id": "NCT01696617_exc", "case_bucket": "or", "source_criterion": "Past history of hypersensitivity to aripiprazole Primary diagnosis of MDD with psychotic feature, bipolar disorder, schizophrenia, schizoaffective disorder, other psychotic disorder or anxiety disorder, a history of alcohol/ drug abuse within the past 12 months, or a diagnosis of dementia Clinically significant current Axis II (DSM-IV-TR) diagnosis A significant risk of suicide corroborated by a score of =5 on item 10(suicidal thoughts) on the MADRS scale or by clinical judgment of the investigator Pregnancy or in breast-feeding Presence of a serious medical illness including cardiac, hepatic, renal, respiratory, endocrinologic, neurologic, or hematologic disease or physical disorder judged to significantly affect central nervous system function Patients taking antipsychotics, mood stabilizer or any psychotropic medications besides antidepressants, except benzodiazepines or beta blockers or hypnotics Patients with past treatment failures of aripiprazole", "candidate_expression": "((Axis II) AND (DSM-IV-TR) AND (MADRS scale) AND (Pregnancy or in breast-feeding) AND (antidepressants) AND (aripiprazole) AND (besides) AND (cardiac) AND (diagnosis) AND (endocrinologic) AND (except) AND (hematologic disease) AND (hepatic) AND (hypersensitivity) AND (medical illness) AND (neurologic) AND (other) AND (physical disorder) AND (psychotropic medications) AND (renal) AND (respiratory) AND (risk of suicide) AND (score of =5 on item 10) AND (serious) AND (significant) AND (treatment failures) AND (within the past 12 months) AND ((alcohol abuse) OR (drug abuse)) AND ((MDD) OR (anxiety disorder,) OR (bipolar disorder) OR (dementia) OR (psychotic disorder) OR (psychotic feature) OR (schizoaffective disorder) OR (schizophrenia)) AND ((antipsychotics) OR (mood stabilizer)) AND ((benzodiazepines) OR (beta blockers) OR (hypnotics)))"}
{"candidate_id": "LLM04235", "doc_id": "NCT02483715_inc", "case_bucket": "other", "source_criterion": "Participants having H. pylori related chronic gastritis with/without peptic ulcers who are aged greater than 20 years old and are willing to received eradication therapy.", "candidate_expression": "((H. pylori related) AND (aged) AND (chronic gastritis) AND (eradication therapy) AND (greater than 20 years old) AND (peptic ulcers) AND (willing to receive))"}
{"candidate_id": "LLM04236", "doc_id": "NCT02745704_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((HIV infection) AND (Hepatocellular Carcinoma) AND (Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (antineoplastic therapy) AND (autoimmune diseases) AND (complications) AND (concomitant) AND (congenital immune deficiency diseases.) AND (diabetes) AND (gastrointestinal bleeding) AND (hepatic encephalopathy) AND (hepatorenal syndrome) AND (immunomodulatory therapy) AND (infection) AND (liver cirrhosis) AND (malignancies) AND (organ dysfunctions) AND (past 12 months) AND (serious))"}
{"candidate_id": "LLM04237", "doc_id": "NCT00500500_inc", "case_bucket": "other", "source_criterion": "female or male of 50 to 85 years old with a care giver Mini Mental Status (MMS) test between 16 to 26 inclusive Clinical Dementia Rating (CDR) test inferior or equal to 1 National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test positive for an Alzheimer's disease Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test positive for dementia", "candidate_expression": "((50 to 85 years) AND (Clinical Dementia Rating (CDR) test) AND (Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test) AND (Mini Mental Status (MMS) tes) AND (National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test) AND (between 16 to 26 inclusive) AND (inferior or equal to 1) AND (old) AND (positive))"}
{"candidate_id": "LLM04238", "doc_id": "NCT02701881_exc", "case_bucket": "or", "source_criterion": "Acute critical limb ischemia Severe critical limb ischemia (Rutherford category 6) Major bleeding history within prior 2 months Known hypersensitivity or contraindication to any of the following medications: heparin, aspirin, clopidogrel or contrast agents Age > 85 years Severe hepatic dysfunction (> 3 times normal reference values) Significant renal dysfunction (Serum creatinine > 2.0 mg/dl Significant leucopenia, neutropenia, thrombocytopenia, anemia, or known bleeding diathesis LVEF <40% or clinically overt congestive heart failure Pregnant women or women with potential childbearing Life expectancy <1 year due to comorbidity Previous bypass surgery or stenting of the superficial femoral artery Untreated inflow disease of the ipsilateral pelvic arteries (more than 50%stenosis or or occlusion Popliteal artery stenosis >50% at P2 or P3 segment", "candidate_expression": "((Age > 85 years) AND (LVEF <40%) AND (Life expectancy <1 year) AND (Major bleeding history within prior 2 months) AND (Popliteal artery stenosis >50% P2 or P3 segment) AND (Pregnant) AND (Rutherford category 6) AND (Serum creatinine > 2.0 mg/dl) AND (anemia) AND (aspirin) AND (bleeding diathesis) AND (bypass surgery Previous) AND (clopidogrel) AND (comorbidity) AND (congestive heart failure clinically overt) AND (contraindication) AND (contrast agents) AND (heparin) AND (hepatic dysfunction Severe) AND (hypersensitivity) AND (inflow disease Untreated ipsilateral pelvic arteries) AND (leucopenia) AND (limb ischemia) AND (limb ischemia Acute critical Severe critical) AND (neutropenia) AND (potential childbearing) AND (renal dysfunction Significant) AND (stenosis more than 50% occlusion) AND (stenting of the superficial femoral artery Previous) AND (thrombocytopenia) AND (women))"}
{"candidate_id": "LLM04239", "doc_id": "NCT01929434_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of cerebral palsy. Patients' curator must be able to give voluntary consent.", "candidate_expression": "((Patients' curator must be able to give voluntary consent) AND (cerebral palsy))"}
{"candidate_id": "LLM04240", "doc_id": "NCT02970773_inc", "case_bucket": "other", "source_criterion": "Motor complete tetraplegia for at least 3 months Age from 18 to 74 years Body mass index (BMI) from 18 to 35kg/m2 Informed consent as documented by signature", "candidate_expression": "((Age) AND (BMI) AND (Body mass index) AND (at least 3 months) AND (complete) AND (from 18 to 35kg/m2) AND (from 18 to 74 years) AND (nformed consent as documented by signature) AND (tetraplegia))"}
{"candidate_id": "LLM04241", "doc_id": "NCT03472508_inc", "case_bucket": "or", "source_criterion": "(1)= 45 years old; (2)A diagnosis or previous diagnosis of essential hypertension, including anyone currently taking antihypertensive drugs; or for those who have not taken antihypertensive drugs within the last 2 weeks, two consecutive examinations were conducted at least one day apart, and both sitting blood pressure (mean value of 3 measurements) met the following criteria: diastolic blood pressure (DBP) =90 mmHg or systolic blood pressure (SBP) =140 mmHg (the second blood pressure was measured at V1); (3)If a study participant is a woman of childbearing age, she agrees to use a reliable contraceptive method during the trial; (4)Voluntarily participates and has signed an informed consent form. (1)Completed MTHFR C677T gene polymorphism detection in run-in period or MTHFR C677T genotype already known in advance; (2)Exhibited good tolerance to enalapril and good overall medication compliance (>80%) in run-in period or previously exhibited good tolerance and adherence to ACEI drugs in previous medication history. (3)Voluntarily continues to participate in this study.", "candidate_expression": "((ACEI drugs) AND (Voluntarily participates) AND (antihypertensive drugs currently) AND (childbearing age) AND (continues to participate in this study Voluntarily) AND (diastolic blood pressure (DBP) =90 mmHg) AND (enalapril) AND (essential hypertension) AND (gene polymorphism detection MTHFR C677T) AND (genotype already known MTHFR C677T) AND (good adherence to ACEI drugs) AND (good tolerance to ACEI drugs) AND (good tolerance to enalapril) AND (old = 45 years diagnosis previous) AND (overall medication compliance good >80%) AND (signed an informed consent) AND (sitting blood pressure two consecutive at least one day apart) AND (systolic blood pressure (SBP) =140 mmHg) AND (woman) AND NOT (antihypertensive drugs within the last 2 weeks))"}
{"candidate_id": "LLM04242", "doc_id": "NCT02370069_exc", "case_bucket": "or", "source_criterion": "immunization with PPV23 within the last year any confirmed or suspected immunodeficiency condition, including human immunodeficiency virus (HIV) infection, haematological malignancy, or a congenital immunodeficiency history of allergic disease or reactions likely to be exacerbated by any component of the vaccine history of allergic disease likely to be stimulated by the vaccination history or records of immunosuppressive therapy (with the exception of topical corticosteroids) for more than 14 days and within 6 months of vaccination history or evidence of administration of immunoglobulins and/or any blood products during the study period or within the three months preceding the study vaccine use of any other investigational or non-registered drug or vaccine during the study period or within 30 days preceding the study vaccine administration of a vaccine during the period starting one month before the dose of vaccine and ending one month after pregnancy", "candidate_expression": "((HIV) AND (PPV23) AND (allergic disease) AND (confirmed) AND (during the period starting one month before the dose of vaccine and ending one month after) AND (exacerbated by any component of the vaccine) AND (exception) AND (for more than 14 days of vaccination) AND (immunization) AND (immunodeficiency condition) AND (immunosuppressive therapy) AND (pregnancy) AND (stimulated by the vaccination) AND (study period) AND (study vaccine) AND (suspected) AND (the dose of vaccine) AND (topical corticosteroids) AND (vaccination) AND (vaccine) AND (within 6 months of vaccination) AND (within the last year) AND ((congenital immunodeficiency) OR (haematological malignancy) OR (human immunodeficiency virus infection)) AND ((allergic disease) OR (allergic reactions)) AND ((blood products) OR (immunoglobulins)) AND ((during the study period) OR (within the three months preceding the study vaccine)) AND ((drug) OR (vaccine)) AND ((investigational) OR (non-registered)) AND ((during the study period) OR (within 30 days preceding the study vaccine)))"}
{"candidate_id": "LLM04243", "doc_id": "NCT02966236_exc", "case_bucket": "or", "source_criterion": "Coronary artery disease - stent Severe chronic renal failure Congenital or acquired thrombophilia/thrombosis event Known or suspected allergy", "candidate_expression": "((Severe) AND (allergy) AND (chronic) AND (renal failure) AND ((Coronary artery disease) OR (stent)) AND ((Known) OR (suspected)) AND ((Congenital) OR (acquired)) AND ((thrombophilia) OR (thrombosis event)))"}
{"candidate_id": "LLM04244", "doc_id": "NCT03034096_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years American Society of Anesthesiologist Class 5 Projected life expectancy less than 30 days Known or suspected hypersensitivity to either propofol, e.g. egg or soy allergy, or volatile general anesthetic agents Known or suspected history of malignant hyperthermia", "candidate_expression": "((5) AND (Age) AND (American Society of Anesthesiologist Class) AND (Projected life expectancy) AND (history) AND (less than 18 years) AND (less than 30 days) AND (malignant hyperthermia) AND ((propofol) OR (volatile general anesthetic agents)) AND ((egg) OR (soy)) AND ((allergy) OR (hypersensitivity)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM04245", "doc_id": "NCT02632760_inc", "case_bucket": "or", "source_criterion": "Patients with anaemia (males Hb <130 g/L, females <120 g/L) undergoing elective cardiac surgery, and available to receive trial drug 1- 10 weeks prior to surgery", "candidate_expression": "((1- 10 weeks prior to surgery) AND (<120 g/L) AND (<130 g/L) AND (Hb) AND (anaemia) AND (available to receive) AND (cardiac surgery) AND (elective) AND (surgery) AND (trial drug) AND ((females) OR (males)))"}
{"candidate_id": "LLM04246", "doc_id": "NCT02527512_exc", "case_bucket": "or", "source_criterion": "Documented renal failure documented allergy to iodine or shellfish previous spine fusion surgery undergoing elective posterior spine single-level instrumentation surgery undergoing anterior spine multi-level instrumentation surgery current antibiotic use.", "candidate_expression": "((allergy) AND (antibiotic use current) AND (multi-level instrumentation surgery undergoing anterior spine) AND (renal failure) AND (single-level instrumentation surgery undergoing elective posterior spine) AND (spine fusion surgery previous) AND ((iodine) OR (shellfish)))"}
{"candidate_id": "LLM04247", "doc_id": "NCT02256956_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04248", "doc_id": "NCT02406885_inc", "case_bucket": "or", "source_criterion": "Men or women, 18 to 65 years old with a BMI of 35 kg/m2 or greater who will be undergoing bariatric surgery (VSG and RYGB) Signed written informed consent Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug Women must not be breastfeeding", "candidate_expression": "((BMI 35 kg/m2 or greater) AND (RYGB) AND (Signed written informed consent) AND (VSG) AND (Women must not be breastfeeding) AND (Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug) AND (bariatric surgery) AND (old 18 to 65 years) AND ((Men) OR (women)))"}
{"candidate_id": "LLM04249", "doc_id": "NCT02707809_exc", "case_bucket": "or", "source_criterion": "allergic history to dexmedetomidine refractory bradycardia < 60 bpm despite treatment severe atrioventricular block (2nd and 3rd degree) previous operation of tongue", "candidate_expression": "((2nd degree) AND (3rd degree) AND (< 60 bpm) AND (allergic) AND (atrioventricular block) AND (bradycardia) AND (despite treatment) AND (dexmedetomidine) AND (history) AND (operation of tongue) AND (previous) AND (refractory) AND (severe) AND (treatment))"}
{"candidate_id": "LLM04250", "doc_id": "NCT02396732_exc", "case_bucket": "or", "source_criterion": "Presence of VTE upon admission Pregnant or nursing Inability to give informed consent by patient or healthcare proxy Contraindication to enoxaparin Contraindication to aspirin Epidural or subdural hematoma Presence, or removal within the last 12 hours, of an epidural or spinal catheter, or recent (within the last 12 hours) epidural or spinal anesthesia/procedures", "candidate_expression": "((Contraindication) AND (Inability to give informed consent) AND (Inability to give informed consent by patient or healthcare proxy) AND (Pregnant) AND (VTE upon admission) AND (aspirin) AND (enoxaparin) AND (nursing) AND (within the last 12 hours) AND ((Epidural hematoma) OR (subdural hematoma)) AND ((Presence of a spinal catheter) OR (Presence of an epidural) OR (removal of a spinal catheter) OR (removal of an epidural)) AND ((epidural anesthesia) OR (spinal anesthesia)))"}
```
