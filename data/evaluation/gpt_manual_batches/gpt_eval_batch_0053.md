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
{"candidate_id": "LLM01301", "doc_id": "NCT02498483_inc", "case_bucket": "other", "source_criterion": "Apgar score at 5 minutes >7 birthweight greater than 2.4 kg Age of at least 10 hours At least one void.", "candidate_expression": "((Age at least 10 hours) AND (Apgar score at 5 minutes >7) AND (birthweight greater than 2.4 kg) AND (void At least one))"}
{"candidate_id": "LLM01302", "doc_id": "NCT03056287_exc", "case_bucket": "or", "source_criterion": "1. Unable to ambulate at least 150 feet prior to stroke, or experienced intermittent claudication while walking; 2. history of congestive heart failure, unstable cardiac arrhythmias, hypertrophic cardiomyopathy, severe aortic stenosis, angina or dyspnea at rest or during ADL's; 3. History of oxygen dependence; 4. Preexisting neurological disorders, dementia or previous stroke; 5. History of major head trauma; 6. Legal blindness or severe visual impairment; 7. history of psychosis or other Axis I disorder that is primary; 8. Life expectancy <1 yr.; 9. Severe arthritis or other problems that limit passive range of motion; 10. History of DVT or pulmonary embolism within 6 months; 11. Uncontrolled diabetes with recent weight loss, diabetic coma, or frequent insulin reactions; 12. Severe hypertension with systolic >200 mmHg and diastolic >110 mmHg at rest; 13. attempt of suicide in the last 2 years or at suicidal risk assessed by SCID interview; 14. Previous or current enrollment in a clinical trial to enhance motor recovery; 15) currently exercising ≥ 2 times per week (≥20 minutes); 16) Presence of non-MR compatible implants, pregnancy or severe claustrophobia.", "candidate_expression": "((Life expectancy <1 yr) AND (SCID interview) AND (Severe hypertension) AND (diastolic >110 mmHg) AND (history) AND (major head trauma History) AND (oxygen dependence History) AND (stroke) AND (systolic >200 mmHg) AND ((Unable to ambulate at least 150 feet prior) OR (intermittent claudication while walking)) AND ((angina) OR (congestive heart failure) OR (dyspnea at rest) OR (dyspnea during ADL's) OR (hypertrophic cardiomyopathy) OR (severe aortic stenosis) OR (unstable cardiac arrhythmias)) AND ((dementia Preexisting) OR (neurological disorders Preexisting) OR (stroke previous)) AND ((Legal blindness) OR (severe visual impairment)) AND ((Axis I disorder history primary) OR (psychosis history)) AND ((Severe arthritis) OR (problems that limit passive range of motion)) AND ((DVT) OR (pulmonary embolism within 6 months)) AND ((diabetes Uncontrolled) OR (diabetic coma) OR (insulin reactions frequent) OR (weight loss)) AND ((at suicidal risk) OR (attempt of suicide in the last 2 years)) AND ((claustrophobia severe) OR (non-MR compatible implants) OR (pregnancy)))"}
{"candidate_id": "LLM01303", "doc_id": "NCT02145026_exc", "case_bucket": "or", "source_criterion": "Contraindications and/or known hypersensitivity to the active substance and/or any of the excipients of epoetin beta treatment Poorly controlled hypertension as assessed by the investigator History of Acute Myeloid Leukemia (AML) or high risk for AML Administration of another investigational drug within 1 month before screening or planned during the study period Previously documented evidence of Pure Red Cell Aplasia (PRCA)", "candidate_expression": "((AML) AND (Administration of another investigational drug within 1 month before screening or planned during the study period) AND (PRCA) AND (Poorly controlled) AND (Pure Red Cell Aplasia) AND (epoetin beta treatment) AND (high) AND (hypertension) AND ((Contraindications) OR (hypersensitivity)) AND ((Acute Myeloid Leukemia) OR (risk for AML)))"}
{"candidate_id": "LLM01304", "doc_id": "NCT00785213_inc", "case_bucket": "or", "source_criterion": "Healthy adults 18-45 years of age Non-smoking Non-pregnant (post-menopausal, surgically sterile or using effective contraceptive measures) Body mass index (BMI) less than or equal to 32 Medically healthy on the basis of medical history and physical examination Hemoglobin > or = to 11.5g/dL Completion of the screening process within 28 days prior to dosing Provision of voluntary written informed consent", "candidate_expression": "((18-45 years of age) AND (> or = to 11.5g/dL) AND (Body mass index (BMI)) AND (Healthy) AND (Hemoglobin) AND (Medically healthy) AND (Non) AND (Provision of voluntary written informed consent) AND (adults) AND (dosing) AND (effective) AND (less than or equal to 32) AND (medical history) AND (of age) AND (physical examination) AND (pregnant) AND (screening process) AND (smoking) AND (surgically) AND (within 28 days prior to dosing) AND ((contraceptive measures) OR (post-menopausal) OR (surgically sterile)))"}
{"candidate_id": "LLM01305", "doc_id": "NCT02312089_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Moderate) AND (Myoma) AND (Uterine abnormalities) AND (endometriosis) AND (severe) AND (uterine surgery))"}
{"candidate_id": "LLM01306", "doc_id": "NCT02437045_exc", "case_bucket": "or", "source_criterion": "Patient not expected to survive more than 4 days Patient allergic to a penicillin or a carbapenem Patient with significant polymicrobial bacteraemia (that is, a Gram positive skin contaminant in one set of blood cultures is not regarded as significant polymicrobial bacteraemia). Treatment is not with the intent to cure the infection (that is, palliative care is an exclusion). Pregnancy or breast-feeding. Use of concomitant antimicrobials in the first 4 days after enrolment with known activity against Gram-negative bacilli (except trimethoprim/sulphamethoxazole may be continued as Pneumocystis prophylaxis). Severe acute illness as defined by Pitt bacteraemia score of >4 Likely source to be from (proven or suspected at the time of randomisation) the central nervous system, e.g. brain abscess, post-surgical meningitis, shunt infection (due to concerns over CNS penetration of piperacillin/tazobactam)", "candidate_expression": "((>4) AND (Gram-negative bacilli) AND (Pitt bacteraemia score) AND (Pregnancy or breast-feeding) AND (allergic) AND (antimicrobials) AND (bacteraemia) AND (concomitant) AND (enrolment) AND (except) AND (first 4 days after enrolment) AND (more than 4 days) AND (not) AND (polymicrobial) AND (post-surgical) AND (rimethoprim/sulphamethoxazole) AND (survive) AND ((brain abscess) OR (meningitis) OR (shunt infection)) AND ((carbapenem) OR (penicillin)))"}
{"candidate_id": "LLM01307", "doc_id": "NCT02781610_exc", "case_bucket": "or", "source_criterion": "Previous randomization in this study Treatment with IV antibiotics in the 6 weeks prior to Visit 1 Admission to the intensive care unit for current pulmonary exacerbation in the two weeks prior to Visit 2, unless admission was due to a desensitization protocol Pneumothorax in the two weeks prior to Visit 2 Primary diagnosis for current hospitalization is unrelated to worsening lower respiratory symptoms (e.g., pulmonary clean out, distal intestinal obstruction syndrome (DIOS), sinusitis) Massive hemoptysis defined as > 250 cc in a 24 hour period or 100 cc/day over 4 consecutive days occurring in the two weeks prior to Visit 2 Current pulmonary exacerbation thought to be due to allergic bronchopulmonary aspergillosis (ABPA) At Visit 1, receiving ongoing treatment with a duration of more than 2 weeks with prednisone equivalent to >10mg/day History of solid organ transplantation Receiving antimicrobial therapy to treat non-tuberculous mycobacterium (e.g., M. abscessus, M. avium complex) in the two weeks prior to Visit 2", "candidate_expression": "((100 cc/day) AND (> 250 cc) AND (>10mg/day) AND (ABPA) AND (Admission to the intensive care unit) AND (At Visit 1 more than 2 weeks) AND (DIOS) AND (IV antibiotics) AND (M. abscessus) AND (M. avium complex) AND (Massive) AND (Pneumothorax) AND (Primary diagnosis) AND (Visit 1) AND (Visit 2) AND (allergic bronchopulmonary aspergillosis) AND (antimicrobial therapy) AND (current hospitalization) AND (desensitization protocol) AND (distal intestinal obstruction syndrome) AND (hemoptysis) AND (in a 24 hour period) AND (in the 6 weeks prior to Visit 1) AND (in the two weeks prior to Visit 2) AND (intensive care unit) AND (lower respiratory symptoms) AND (non-tuberculous mycobacterium) AND (over 4 consecutive days) AND (prednisone) AND (pulmonary clean out) AND (pulmonary exacerbation) AND (sinusitis) AND (solid organ transplantation) AND (unless) AND (unrelated) AND (worsening))"}
{"candidate_id": "LLM01308", "doc_id": "NCT02984228_inc", "case_bucket": "other", "source_criterion": "English speaking/literate Age 18-100 years Visual analog score pain >= 5 Greater than or equal to 3 months of pain after onset of symptoms that has failed conservative treatments Confirmation of glenohumeral OA via imaging Transient relief of symptoms after diagnostic intra-articular injection into the glenohumeral joint", "candidate_expression": "((18-100 years) AND (>= 5) AND (Age) AND (English speaking/literate) AND (Greater than or equal to 3 months) AND (Transient) AND (Visual analog score pain) AND (after onset of symptoms) AND (conservative treatments) AND (failed) AND (glenohumeral OA) AND (glenohumeral joint) AND (imaging) AND (intra-articular injection) AND (onset of symptoms) AND (pain) AND (relief of symptoms))"}
{"candidate_id": "LLM01309", "doc_id": "NCT02940912_exc", "case_bucket": "or", "source_criterion": "Atypical Parkinsonian Syndromes Parkinson's disease with hallucinations Parkinson's disease with impulse Control disorder (ICD) Parkinson's disease already treated with APOMORPHINE pump or justifying the use of the pump continuously day and night Another obvious severe disease explaining insomnia Exclusion for monitoring difficulties (mutation, insufficient motivation, priority associated pathology in care) Patient unwilling to accept a pump Patient not accepting polysomnography and multiple sleep latency test Patient with health problems or a skin disease precluding continuous subcutaneous infusion Female parturient or nursing Cardiac dysrhythmia precluding treatment with domperidone or apomorphine (increased QTc = 440 ms in men, QTc = 450 ms in women) antiemetic neuroleptics Tetrabenazine Excessive alcohol consumption Hypersensitivity to apomorphine or one of the excipients Respiratory Depression Hepatic impairment Intellectual Disability Dementia", "candidate_expression": "((= 440 ms) AND (= 450 ms) AND (APOMORPHINE) AND (Atypical) AND (Cardiac dysrhythmia) AND (Dementia) AND (Excessive alcohol consumption) AND (Female) AND (Hepatic impairment) AND (Hypersensitivity) AND (Intellectual Disability) AND (Parkinson's disease) AND (Parkinsonian Syndromes) AND (QTc) AND (Respiratory Depression) AND (Tetrabenazine) AND (antiemetic neuroleptics) AND (apomorphine) AND (continuous subcutaneous infusion) AND (domperidone) AND (excipients) AND (hallucinations) AND (health problems) AND (impulse Control disorder (ICD)) AND (insomnia) AND (men) AND (multiple sleep latency test) AND (not) AND (not accepting) AND (nursing) AND (parturient) AND (polysomnography) AND (precluding) AND (pump) AND (severe disease) AND (skin disease) AND (unwilling) AND (unwilling to accept) AND (women))"}
{"candidate_id": "LLM01310", "doc_id": "NCT03045562_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01311", "doc_id": "NCT02979561_inc", "case_bucket": "or", "source_criterion": "Men and women aged > 18 years Angiographically confirmed acute massive pulmonary embolism with involvement of Central pulmonary arteries. endovascular mechanical thrombus fragmentation + thrombolytic therapy (using recombinant tissue activator of plasminogen), performed for treatment of the above-mentioned pulmonary embolism in less than 48 hours before randomization. The patient should be randomized no earlier than 24 hours after procedures endovascular mechanical thrombus fragmentation + thrombolytic therapy Written informed consent signed by patient.", "candidate_expression": "((Angiographically) AND (Men) AND (aged > 18 years) AND (endovascular mechanical thrombus fragmentation) AND (involvement of Central pulmonary arteries) AND (pulmonary embolism) AND (pulmonary embolism Angiographically confirmed acute massive) AND (recombinant tissue activator of plasminogen) AND (ritten informed consent signed by patient) AND (thrombolytic therapy) AND (treatment in less than 48 hours before randomization) AND (women))"}
{"candidate_id": "LLM01312", "doc_id": "NCT02637076_exc", "case_bucket": "or", "source_criterion": "use of any sedative hypnotics, tranquilizers, anticonvulsants, antihistamines (except non-sedating), benzodiazepines, clonidine or any medication known to affect dopamine at start of baseline period significant unstable or uncontrolled medical/psychiatric disease significant history of head trauma/surgery or seizure disorder radiation exposure exceeding 20mSv in last 12 months pregnancy substance abuse/dependence (including alcohol) have sleep apnea, or are shift workers on a sodium-restricted diet has ever taken Xyrem / sodium oxybate / GHB at any time claustrophobia metal implants / objects in the body that may interfere with MRI succinic semialdehyde dehydrogenase deficiency", "candidate_expression": "((GHB) AND (MRI) AND (Xyrem) AND (alcohol) AND (anticonvulsants) AND (antihistamines) AND (at start of baseline period) AND (benzodiazepines) AND (claustrophobia) AND (clonidine) AND (ever) AND (exceeding 20mSv) AND (except) AND (head surgery) AND (head trauma) AND (history) AND (in last 12 months) AND (may interfere with) AND (medical disease) AND (medication known to affect dopamine) AND (metal implants) AND (metal objects) AND (non-sedating) AND (pregnancy) AND (psychiatric disease) AND (radiation exposure) AND (sedative hypnotics) AND (seizure disorder) AND (shift workers) AND (significant) AND (sleep apnea) AND (sodium oxybate) AND (sodium-restricted diet) AND (substance abuse) AND (substance dependence) AND (succinic semialdehyde dehydrogenase deficiency) AND (tranquilizers) AND (uncontrolled) AND (unstable))"}
{"candidate_id": "LLM01313", "doc_id": "NCT01890759_inc", "case_bucket": "or", "source_criterion": "Male and female subjects aged 9 to 17 months on the day of inclusion Informed consent form has been signed and dated by the parent(s) or other legally acceptable representative(s) (if applicable) Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.", "candidate_expression": "((9 to 17 months) AND (Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.) AND (aged) AND (on the day of inclusion) AND (the day of inclusion) AND ((Male) OR (female)))"}
{"candidate_id": "LLM01314", "doc_id": "NCT02613039_exc", "case_bucket": "or", "source_criterion": "Participation in another clinical trial. Known or suspected (or history of) malignancy or chronic illness. Serious organic or mental disease diagnosed by a psychiatrist (e.g., major depression currently treated with antidepressant medication) suspected on the basis of the medical history and/or clinical examination. Conditions that may affect the compliance to the study. Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).", "candidate_expression": "((Conditions that may affect the compliance to the study.) AND (Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).) AND (antidepressant medication) AND (currently) AND (diagnosed by a psychiatrist) AND (history of) AND (major depression) AND (suspected) AND (treated) AND ((clinical examination) OR (medical history)) AND ((Known) OR (suspected)) AND ((chronic illness) OR (malignancy)) AND ((mental disease) OR (organic disease)))"}
{"candidate_id": "LLM01315", "doc_id": "NCT03513757_inc", "case_bucket": "other", "source_criterion": "All children scheduled for outpatient MRI scans with expected duration of scan between 30 minutes and 75 minutes.", "candidate_expression": "((MRI scans) AND (between 30 minutes and 75 minutes) AND (expected duration of scan) AND (outpatient))"}
{"candidate_id": "LLM01316", "doc_id": "NCT02774317_inc", "case_bucket": "or", "source_criterion": "Nonsurgical neonates and babies up to age 6 months with INR 1.5 or more who are deemed clinically to need plasma infusion.", "candidate_expression": "((1.5 or more) AND (INR) AND (Nonsurgical) AND (age) AND (babies) AND (need) AND (neonates) AND (plasma infusion) AND (up to age 6 months))"}
{"candidate_id": "LLM01317", "doc_id": "NCT01944800_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01318", "doc_id": "NCT01098383_inc", "case_bucket": "or", "source_criterion": "A formal diagnosis of Autism or Pervasive Developmental Disorder not otherwise specified (PDD-NOS), given by a child neurologist. Age: 10-18 years. A signed parental consent form.", "candidate_expression": "((10-18 years) AND (A signed parental consent form) AND (Age) AND (PDD-NOS) AND ((Autism) OR (Pervasive Developmental Disorder not otherwise specified)))"}
{"candidate_id": "LLM01319", "doc_id": "NCT03216967_inc", "case_bucket": "other", "source_criterion": "Adult patients Kidney transplant recipients Patients treated by a calcineurin inhibitor and mycophenolic acid Viremia >= 3 log UI/ml Patients who have given written informed consent Negative pregnancy test (blood ß-HCG dosage)", "candidate_expression": "((Adult) AND (Kidney transplant) AND (Patients who have given written informed consent) AND (Viremia >= 3 log UI/ml) AND (blood ß-HCG dosage) AND (calcineurin inhibitor) AND (mycophenolic acid) AND (pregnancy test Negative))"}
{"candidate_id": "LLM01320", "doc_id": "NCT02502734_inc", "case_bucket": "or", "source_criterion": "Aged 5 years to less than 12 years at Visit 1. At least 15 (25%) children of the total study population must be aged 5 to less than 8 years. Male or pre-menarchial female subjects. Subjects must be pre-adolescent without any signs of puberty (Tanner Stage 1). Normal range for their height and weight. Weight and height measurements should fall within the percentile range 3-97% of normal values for age according to Danish growth charts. Have a documented diagnosis of persistent asthma, as defined by the National Institutes of Health for at least 3 months prior to the Screening Visit. A pre-bronchodilatory forced expiratory flow in 1 second (FEV1) at Visit 1 (Screening) >=80% predicted. There should be no Short acting beta-agonist (SABA) use within 4 hours of this measurement. Using one of the following asthma therapies prior to entry into the study: SABA inhaler alone (e.g. salbutamol) on an as required basis and/or Regular non-inhaled corticosteroid (ICS) controller medications for asthma (e.g. cromones or leukotriene receptor antagonists) and/or Previously treated with ICS (equipotent to inhaled budesonide <=400 micrograms (mcg) total daily dose). There must be no ICS use within 2 weeks of Visit 1 (Screening). Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study. Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement. The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC). (2) Subject and their legal guardian(s) understand that the study requires them to be treated on an outpatient basis. (3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.", "candidate_expression": "(((3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.) AND (1) AND (5 years to less than 12 years) AND (<=400 micrograms (mcg)) AND (>=80% predicted) AND (Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study.) AND (Aged) AND (ICS) AND (Male) AND (Normal range) AND (SABA) AND (SABA inhaler) AND (Screening Visit) AND (Short acting beta-agonist (SABA)) AND (Tanner Stage) AND (The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC).) AND (Visit 1) AND (Visit 1 (Screening)) AND (Weight) AND (Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement.) AND (as defined by the National Institutes of Health) AND (asthma therapies) AND (at Visit 1) AND (at Visit 1 (Screening)) AND (at least 3 months prior to the Screening Visit) AND (budesonide) AND (cromones) AND (entry into the study) AND (female) AND (forced expiratory flow in 1 second (FEV1)) AND (height) AND (leukotriene receptor antagonists) AND (no) AND (persistent asthma) AND (pre-adolescent) AND (pre-bronchodilatory) AND (pre-menarchial) AND (prior to entry into the study) AND (rescue SABA) AND (salbutamol) AND (signs of puberty) AND (this measurement) AND (weight) AND (within 2 weeks of Visit 1 (Screening)) AND (within 4 hours of this measurement) AND (within the percentile range 3-97%) AND (without any))"}
{"candidate_id": "LLM01321", "doc_id": "NCT03259243_inc", "case_bucket": "other", "source_criterion": "Patient who undergoing gynecologic laparoscopic surgery Patient who agrees to participate in this study Patient able to speak and understand Thai Patient able to complete the questionnaire", "candidate_expression": "((Patient able to speak and understand Thai) AND (Patient who agrees to participate in this study) AND (able to complete the questionnaire) AND (able to speak and understand Thai) AND (agrees to participate in this study) AND (gynecologic laparoscopic surgery))"}
{"candidate_id": "LLM01322", "doc_id": "NCT02858804_inc", "case_bucket": "or", "source_criterion": "age=65 years diagnosis with mantle cell lymphoma Ann Arbor stage II,III or IV ECOG=1 or if ECOG=2 but recover after pretreatment.", "candidate_expression": "((Ann Arbor stage) AND (age =65 years) AND (mantle cell lymphoma) AND (pretreatment) AND (recover after pretreatment) AND ((II) OR (III) OR (IV)) AND ((ECOG =1) OR (ECOG =2)))"}
{"candidate_id": "LLM01323", "doc_id": "NCT03088280_exc", "case_bucket": "other", "source_criterion": "PRA > 50% DSA > 1500 MFI Retransplantation Patients who are planning to receive mycophenolate instead of everolimus Patients who have planning for follow-up in another center", "candidate_expression": "((> 1500 MFI) AND (> 50%) AND (DSA) AND (PRA) AND (Retransplantation) AND (another center) AND (everolimus) AND (follow-up) AND (instead of) AND (mycophenolate) AND (planning for) AND (planning to))"}
{"candidate_id": "LLM01324", "doc_id": "NCT02780427_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitive reaction to dexmedetomidine Organ dysfunction, and significant developmental delays or behavior problems Cardiac arrhythmia Known. acyanotic congenital heart disease or children after cardiac interventional procedures for follow-up examination.", "candidate_expression": "((Cardiac arrhythmia) AND (Organ dysfunction) AND (acyanotic congenital heart disease) AND (after cardiac interventional procedures) AND (allergy) AND (behavior problems) AND (cardiac interventional procedures) AND (children) AND (developmental delays) AND (dexmedetomidine) AND (follow-up examination) AND (for follow-up examination) AND (hypersensitive) AND (significant))"}
{"candidate_id": "LLM01325", "doc_id": "NCT02822001_exc", "case_bucket": "or", "source_criterion": "Patients unable to give informed consent. Any patient whose condition will not allow for placement of the electrode PadSet. Patients whose tracheas were not extubated in OR or PACU. Patients with Impaired Renal Function with a have a known estimated CrCl<30 ml/min Patients using oral contraception.", "candidate_expression": "((Impaired Renal Function) AND (OR) AND (PACU) AND (Patients unable to give informed consent) AND (condition) AND (electrode PadSet) AND (estimated CrCl <30 ml/min) AND (oral contraception) AND (placement allow) AND NOT (extubated tracheas))"}
```
