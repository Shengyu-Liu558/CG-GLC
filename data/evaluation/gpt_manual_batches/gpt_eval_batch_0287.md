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
{"candidate_id": "LLM07151", "doc_id": "NCT02375295_exc", "case_bucket": "other", "source_criterion": "Patients with medical comorbidities preventing them from definitive surgical therapy. Patients with persistent stone burden following definitive surgical therapy.", "candidate_expression": "((definitive surgical therapy) AND (definitive surgical therapy preventing them from) AND (medical comorbidities) AND (stone burden persistent following definitive surgical therapy definitive surgical therapy))"}
{"candidate_id": "LLM07152", "doc_id": "NCT02584140_exc", "case_bucket": "or", "source_criterion": "Pregnancy at enrollment. Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder). Use of prohibited medications, in particular, agents known to be nephrotoxic or drugs slow in renal excretion. Previous participation in an HIV vaccine trial. Participants that were documented to have received only placebo are not excluded. Signs or symptoms suspicious for Primary HIV Infection (PHI).", "candidate_expression": "((Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder)) AND (HIV vaccine trial) AND (PHI) AND (Participants) AND (Pregnancy) AND (Previous) AND (Primary HIV Infection) AND (Signs) AND (agents) AND (at enrollment) AND (drugs) AND (enrollment) AND (nephrotoxic) AND (not) AND (participation) AND (placebo) AND (slow in renal excretion) AND (symptoms))"}
{"candidate_id": "LLM07153", "doc_id": "NCT02056301_inc", "case_bucket": "other", "source_criterion": "Patients age 8- 18 years 2) Patients undergoing minimally invasive pectus excavatum repair via Nuss procedure 3) American Society of Anesthesiology Status I-III", "candidate_expression": "((8- 18 years) AND (American Society of Anesthesiology Status) AND (I-III) AND (Nuss procedure) AND (age) AND (minimally invasive pectus excavatum repair))"}
{"candidate_id": "LLM07154", "doc_id": "NCT01959425_exc", "case_bucket": "or", "source_criterion": "OAT required for reasons not related to AF (i.e., prosthetic valve, PV stenosis, previous pulmonary embolism, presence of spontaneous echo contrast [SEC] at standard echo performed at 3-months follow-up). Any cardiac surgery within the past 60 days (2 months) or valvular cardiac surgical procedure at any time (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Previous myocardial infarction (MI) or a percutaneous coronary intervention PCI within the past 3 months Awaiting cardiac transplantation or other cardiac surgery within the next 365 days (12 months) Documented left atrial thrombus Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or COPD) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms Significant medical problem that in the opinion of the investigator would preclude enrollment in this study Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Acute illness or active systemic infection or sepsis Unstable angina Contraindication to anticoagulation (i.e., heparin, warfarin or another commercially available anticoagulation medication) History of blood clotting or bleeding abnormalities Life expectancy less than 360 days (12 months) Uncontrolled Heart Failure or NYHA Class III or IV heart failure Enrollment in a clinical study evaluating another device or drug, within the past 6 months Unable or unwilling to comply with protocol requirements", "candidate_expression": "((COPD) AND (Contraindication) AND (Enrollment in a clinical study evaluating another device or drug, within the past 6 months) AND (Heart Failure Uncontrolled NYHA Class III NYHA Class IV) AND (Life expectancy less than 360 days less than 12 months) AND (MI) AND (OAT AF) AND (PCI within the past 3 months) AND (PV stenosis) AND (Unable or unwilling to comply with protocol requirements) AND (Unstable angina) AND (Women who are pregnant (as evidenced by pregnancy test if pre-menopausal)) AND (anticoagulation) AND (atriotomy) AND (bleeding abnormalities) AND (blood clotting abnormalities) AND (cardiac surgery within 12 months) AND (cardiac surgery within the past 60 days 2 months) AND (cardiac transplantation) AND (heart failure) AND (heparin) AND (left atrial thrombus) AND (myocardial infarction) AND (percutaneous coronary intervention) AND (prosthetic valve) AND (prosthetic valve)) AND (pulmonary disease Significant) AND (pulmonary embolism) AND (restrictive pulmonary disease) AND (sepsis) AND (standard echo spontaneous echo contrast 3-months follow-up SEC) AND (systemic infection) AND (valve repair) AND (valve replacement) AND (valvular cardiac surgical) AND (ventriculotomy) AND (warfarin))"}
{"candidate_id": "LLM07155", "doc_id": "NCT02489045_exc", "case_bucket": "or", "source_criterion": "Females who are pregnant or nursing. Patients not scheduled for trans-jugular liver biopsy Patients who have received an investigational drug in the 30 days before study drug administration, or will receive one within 72 h afterwards,. Patients with known or suspected right-to-left, bi-directional, or transient right-to-left cardiac shunts Patients with pulmonary hypertension or unstable cardiopulmonary conditions Patients currently on chemotherapy or with other primary cancers requiring systemic or hepatic loco-regional treatment. Patients who are medically unstable, patients who are seriously or terminally ill, and patients whose clinical course is unpredictable. For example: Patients on life support or in a critical care unit. Patients with unstable occlusive disease (e.g., crescendo angina) Patients with clinically unstable cardiac arrhythmias, such as recurrent ventricular tachycardia. Patients with uncontrolled congestive heart failure (NYHA Class IV) Patients with recent cerebral hemorrhage. Patients who have undergone surgery within 24 hours prior to the study sonographic examination. Patients with a history of anaphylactic allergy to eggs or egg products, manifested by one or more of the following symptoms: generalized urticaria, difficulty in breathing, swelling of the mouth and throat, hypotension, or shock. (Subjects with nonanaphylactic allergies to eggs or egg products may be enrolled in the study, but must be watched carefully for 1 h following the administration of SONAZOID). Patients with congenital heart defects. Patients with severe emphysema, pulmonary vasculitis, or a history of pulmonary emboli. Patients with respiratory distress syndrome Patients with thrombosis within the hepatic, portal, or mesenteric veins.", "candidate_expression": "((Females) AND (NYHA Class IV) AND (anaphylactic allergy) AND (bi-directional cardiac shunts) AND (cardiac arrhythmias clinically unstable) AND (cerebral hemorrhage recent) AND (chemotherapy) AND (clinical course is unpredictable) AND (congenital heart defects) AND (congestive heart failure uncontrolled) AND (critical care unit) AND (difficulty in breathing) AND (egg products) AND (eggs) AND (emphysema severe) AND (generalized urticaria) AND (hepatic loco-regional treatment) AND (hypotension) AND (known) AND (life support) AND (medically unstable) AND (nursing) AND (pregnant) AND (primary cancers other) AND (pulmonary emboli) AND (pulmonary hypertension) AND (pulmonary vasculitis) AND (respiratory distress syndrome) AND (right-to-left cardiac shunts) AND (seriously ill) AND (shock) AND (sonographic examination) AND (surgery within 24 hours prior to the study sonographic examination) AND (suspected) AND (swelling of the mouth) AND (swelling of the throat) AND (systemic loco-regional treatment) AND (terminally ill) AND (thrombosis hepatic veins portal veins mesenteric veins) AND (trans-jugular liver biopsy scheduled) AND (transient right-to-left cardiac shunts) AND (unstable cardiopulmonary conditions) AND (unstable occlusive disease) AND (ventricular tachycardia recurrent))"}
{"candidate_id": "LLM07156", "doc_id": "NCT01228279_inc", "case_bucket": "other", "source_criterion": "Adult (age 18 years and older) Patients with end-stage renal disease(ESRD)/chronic kidney disease(CKD)stage 5", "candidate_expression": "((18 years and older) AND (Adult) AND (CKD) AND (ESRD) AND (age) AND (chronic kidney disease) AND (end-stage renal disease) AND (stage 5))"}
{"candidate_id": "LLM07157", "doc_id": "NCT03431831_inc", "case_bucket": "or", "source_criterion": "Overweight/Obese Adult patients (age 19 years -65) eligible based on WALI screening tool", "candidate_expression": "((19 years -65) AND (Adult) AND (Obese) AND (Overweight) AND (WALI screening tool) AND (age) AND (eligible))"}
{"candidate_id": "LLM07158", "doc_id": "NCT02781610_exc", "case_bucket": "or", "source_criterion": "Previous randomization in this study Treatment with IV antibiotics in the 6 weeks prior to Visit 1 Admission to the intensive care unit for current pulmonary exacerbation in the two weeks prior to Visit 2, unless admission was due to a desensitization protocol Pneumothorax in the two weeks prior to Visit 2 Primary diagnosis for current hospitalization is unrelated to worsening lower respiratory symptoms (e.g., pulmonary clean out, distal intestinal obstruction syndrome (DIOS), sinusitis) Massive hemoptysis defined as > 250 cc in a 24 hour period or 100 cc/day over 4 consecutive days occurring in the two weeks prior to Visit 2 Current pulmonary exacerbation thought to be due to allergic bronchopulmonary aspergillosis (ABPA) At Visit 1, receiving ongoing treatment with a duration of more than 2 weeks with prednisone equivalent to >10mg/day History of solid organ transplantation Receiving antimicrobial therapy to treat non-tuberculous mycobacterium (e.g., M. abscessus, M. avium complex) in the two weeks prior to Visit 2", "candidate_expression": "((ABPA) AND (Admission to the intensive care unit) AND (DIOS) AND (IV antibiotics in the 6 weeks prior to Visit 1) AND (Pneumothorax in the two weeks prior to Visit 2) AND (Primary diagnosis current hospitalization) AND (allergic bronchopulmonary aspergillosis) AND (antimicrobial therapy non-tuberculous mycobacterium in the two weeks prior to Visit 2 M. abscessus M. avium complex) AND (hemoptysis Massive in the two weeks prior to Visit 2 in a 24 hour period over 4 consecutive days) AND (intensive care unit) AND (lower respiratory symptoms worsening) AND (prednisone At Visit 1 more than 2 weeks >10mg/day) AND (pulmonary exacerbation) AND (pulmonary exacerbation in the two weeks prior to Visit 2) AND (solid organ transplantation) AND (unrelated) AND NOT (desensitization protocol) AND ((distal intestinal obstruction syndrome) OR (pulmonary clean out) OR (sinusitis)) AND ((100 cc/day) OR (> 250 cc)))"}
{"candidate_id": "LLM07159", "doc_id": "NCT01078051_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07160", "doc_id": "NCT02886962_inc", "case_bucket": "or", "source_criterion": "Adult patients (= 18 years) Patient on hemodialysis treatment for at least 1 month Patient with a history of, or presenting a new episode of atrial fibrillation (either permanent or paroxysmal). Patient with a CHADS2VASC score =2 Patient with high risk of bleeding as defined by (1) HASBLED score =3 OR (2) HASBLED = CHADS2VASC score, OR (3) recent history of severe bleeding (type 3a, 3b, 3c), particularly cerebral or gastrointestinal, OR (4) prior recurrent (>2) history of falls. Patient capable of understanding information about the study and of giving his/her consent Patient informed of the preliminary medical exam results Patient with healthcare insurance Written consent signed", "candidate_expression": "((= 18) AND (=2) AND (=3) AND (>2) AND (Adult) AND (CHADS2VASC score) AND (HASBLED score) AND (Patient capable of understanding information about the study and of giving his/her consent) AND (Patient informed of the preliminary medical exam results) AND (Written consent signed) AND (at least 1 month) AND (atrial fibrillation) AND (falls) AND (hemodialysis) AND (high) AND (new episode) AND (recurrent) AND (risk of bleeding) AND (severe bleeding) AND (type 3a, 3b, 3c) AND (years) AND ((cerebral) OR (gastrointestinal)))"}
{"candidate_id": "LLM07161", "doc_id": "NCT02344888_inc", "case_bucket": "other", "source_criterion": "Infertile lean women with PCOS as defined by the Rotterdam criteria. CC resistance (defined as failure of ovulation after receiving 150 mg/day of CC for 5 consecutive days per cycle, for at least 3 consecutive cycles).", "candidate_expression": "((CC) AND (Infertile) AND (PCOS) AND (Rotterdam criteria) AND (resistance) AND (women))"}
{"candidate_id": "LLM07162", "doc_id": "NCT00527826_inc", "case_bucket": "or", "source_criterion": "Subject must have a diagnosis of COPD based on the American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria. Male or female subjects, aged >=40 years. Females must be of Non Child Bearing Potential. The definition of Non Child Bearing Potential is as following: Females, regardless of their age, with functioning ovaries and who have a current documented tubal ligation or hysterectomy, or females who are post-menopausal. Have diagnosed COPD stage III or IV according to GOLD criteria: a baseline post-bronchodilator Forced Expiratory Volume, measured at 1 second (FEV1) <50% of predicted normal and a baseline post- bronchodilator FEV1/Inspiratory Vital Capacity (IVC) ratio <70%. Have experienced at least 2 moderate or severe COPD exacerbations leading to medical consultation (requiring oral corticosteroids or increasing dosage of oral corticosteroids and/or antibiotics or hospitalization) within the 12 months preceding Visit 1. Have stable COPD medication within 4 weeks prior to Visit 1 (no new medication added and no dosage changes in medication). Current or ex-smokers with a smoking history of at least 10 pack years (number of pack years = [number of cigarettes per day / 20] x number of years smoked, e.g., 20 cigarettes per day for 10 years, or 10 cigarettes per day for 20 years). Are currently managed at home (outpatients), are ambulatory and able to travel to the clinic. Subjects can be treated with all relevant COPD medication. This includes vaccines, inhaled short-acting beta-2-agonists as needed, short-acting or long-acting anticholinergics (tiotropium), systemic beta-2-agonists, theophylline, mucolytics, antioxidants, beta-1-agonists (for cardiovascular indication), non-invasive ventilation, long term oxygen therapy and can have Cor Pulmonale. A signed and dated written informed consent is obtained prior to participation. Able to comply with the requirements of the protocol and be available for study visits over 52 weeks.", "candidate_expression": "((Able to comply with the requirements of the protocol) AND (American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria) AND (COPD) AND (COPD exacerbations at least 2 within the 12 months preceding Visit 1 severe) AND (COPD medication) AND (COPD medication stable within 4 weeks prior to Visit 1) AND (Cor Pulmonale) AND (FEV1/Inspiratory Vital Capacity (IVC) ratio post- bronchodilator <70% moderate) AND (Females) AND (Forced Expiratory Volume, measured at 1 second (FEV1) post-bronchodilator <50% of predicted normal) AND (GOLD criteria stage III or IV) AND (Male) AND (able to travel to the clinic) AND (aged >=40 years) AND (ambulatory) AND (antibiotics) AND (antioxidants) AND (at home) AND (available for study visits over 52 weeks) AND (beta-1-agonists) AND (cardiovascular indication) AND (ex) AND (female) AND (females) AND (functioning ovaries) AND (hospitalization) AND (hysterectomy) AND (inhaled short-acting beta-2-agonists) AND (long-acting anticholinergics) AND (managed) AND (managed at home) AND (mucolytics) AND (non-invasive ventilation) AND (oral corticosteroids) AND (oral corticosteroids increasing dosage) AND (outpatients) AND (oxygen) AND (oxygen therapy long term) AND (post-menopausal) AND (short-acting) AND (smokers Current) AND (smoking history 10 pack years) AND (study visits) AND (systemic beta-2-agonists) AND (theophylline) AND (tiotropium) AND (tubal ligation) AND (vaccines) AND (written informed consent prior to participation) AND NOT (Child Bearing Potential))"}
{"candidate_id": "LLM07163", "doc_id": "NCT03066440_inc", "case_bucket": "or", "source_criterion": "Age between 0 and 18 years Venous pH less than 7.25 Ketonuria as confirmed on urine point-of-care testing or urinalysis Hyperglycemia (Serum glucose > 200 mg/dl) Serum bicarbonate <15 mmol/L PICU admission", "candidate_expression": "((<15 mmol/L) AND (> 200 mg/dl) AND (Age) AND (Hyperglycemia) AND (Ketonuria) AND (PICU) AND (Serum bicarbonate) AND (Serum glucose) AND (Venous pH) AND (admission) AND (between 0 and 18 years) AND (less than 7.25) AND ((urinalysis) OR (urine point-of-care testing)))"}
{"candidate_id": "LLM07164", "doc_id": "NCT03103204_inc", "case_bucket": "or", "source_criterion": "Moderate to advanced generalized chronic periodontitis Body mass index: > 18.5 kg/m2 Minimum of 12 natural teeth Smokers, non-smokers or former-smokers", "candidate_expression": "((Body mass index > 18.5 kg/m2) AND (Smokers) AND (former-smokers) AND (generalized chronic periodontitis Moderate to advanced) AND (natural teeth Minimum of 12) AND (non-smokers))"}
{"candidate_id": "LLM07165", "doc_id": "NCT03296488_inc", "case_bucket": "or", "source_criterion": "Male or female who is among 20 to 80 years of age at screening. Scheduled to electively undergo open-laparotomy. American Society of Anesthesiology Physical Class 1-3. Ability and willingness to provide informed consent", "candidate_expression": "((Ability and willingness to provide informed consent) AND (American Society of Anesthesiology Physical Class 1-3) AND (Male) AND (age 20 to 80 years at screening) AND (female) AND (open-laparotomy Scheduled electively))"}
{"candidate_id": "LLM07166", "doc_id": "NCT02260700_exc", "case_bucket": "or", "source_criterion": "Participant has a clinically significant abnormal physical examination, vital signs or 12 lead ECG (including QTc greater than (>) 450msec, Left Bundle Branch Block, permanent pacemaker or implantable cardioverter defibrillator) at Screening or admission Participant has a history of or current liver or renal insufficiency; significant cardiac, vascular, pulmonary, gastrointestinal, endocrine, neurologic, hematologic, rheumatologic, psychiatric, or metabolic disturbances Use of any prescription or over-the-counter medication, herbal medication, vitamins, or mineral supplements within 14 days prior to study drug administration (not including paracetamol). Medication for chronic use in age related disease will be allowed after approval by both the investigator and to the sponsor. No change in dose or regimen will be permitted during the study that is, from the Screening visit until the follow-up visit Participant has a history of spontaneous, prolonged or severe bleeding of unclear origin Participant has a history of epilepsy or fits or unexplained black-outs other than vasovagal collapse", "candidate_expression": "((Left Bundle Branch Block) AND (Medication chronic use) AND (QTc greater than (>) 450msec) AND (abnormal 12 lead ECG) AND (abnormal physical examination) AND (abnormal vital signs) AND (age related disease) AND (any prescription) AND (approval by both the investigator and to the sponsor) AND (black-outs unexplained) AND (bleeding history unclear origin spontaneous prolonged severe) AND (cardiac disturbances) AND (endocrine disturbances) AND (epilepsy) AND (fits) AND (gastrointestinal disturbances) AND (hematologic disturbances) AND (herbal medication) AND (implantable cardioverter defibrillator Screening admission) AND (liver insufficiency) AND (metabolic disturbances) AND (mineral supplements) AND (neurologic disturbances) AND (over-the-counter medication) AND (permanent pacemaker) AND (psychiatric disturbances) AND (pulmonary disturbances) AND (renal insufficiency) AND (rheumatologic disturbances) AND (significant) AND (vascular disturbances) AND (vitamins) AND NOT (paracetamol) AND NOT (vasovagal collapse))"}
{"candidate_id": "LLM07167", "doc_id": "NCT02678728_inc", "case_bucket": "other", "source_criterion": "Patients undergoing thoracic aorta surgery with hypothermic circulatory arrest, over 20-of age", "candidate_expression": "((age) AND (hypothermic circulatory arrest) AND (over 20) AND (surgery) AND (thoracic aorta))"}
{"candidate_id": "LLM07168", "doc_id": "NCT01032109_inc", "case_bucket": "other", "source_criterion": "choroidal neovascularization caused by age-related macula degeneration no previous treatment a follow-up at least 12 months a baseline visual acuity ranging from a letter score of 0 to 70 on the Early Treatment Diabetic Retinopathy Study chart", "candidate_expression": "((Early Treatment Diabetic Retinopathy Study chart) AND (choroidal neovascularization) AND (follow-up at least 12 months) AND (macula degeneration age-related) AND (visual acuity baseline letter score of 0 to 70) AND NOT (treatment previous))"}
{"candidate_id": "LLM07169", "doc_id": "NCT02844907_exc", "case_bucket": "or", "source_criterion": "Rheumatoid arthritis Diabetes or immediate family history of diabetes Coronary artery disease Congestive heart failure Pulmonary disorders, including COPD and asthma Malabsorptive GI disease, such as celiac disease, or gastric bypass Significant hepatic disease Renal insufficiency (eGFR < 60 mL/kg/min) Anemia (hematocrit < 34%) as measured at screening visit Pregnant females Consumption of daily medications that alter glucose metabolism of GI function (glucocorticoids, psychotropics, narcotics, metoclopramide) Consumption or injection of insulin Apparent sensitivity to any of the study peptides as determined by the skin test Diagnosis or h/o PTSD, depression, substance use, mental health problems, sleep disorders, HPA disruption and/or TBI", "candidate_expression": "((< 34%) AND (< 60 mL/kg/min) AND (Anemia) AND (Congestive heart failure) AND (Coronary artery disease) AND (Malabsorptive GI disease) AND (Pregnant) AND (Pulmonary disorders) AND (Renal insufficiency) AND (Rheumatoid arthritis) AND (Significant) AND (daily) AND (eGFR) AND (females) AND (hematocrit) AND (hepatic disease) AND (immediate family history) AND (injection) AND (medications) AND (screening visit) AND (sensitivity) AND (skin test) AND (study peptides) AND (that alter glucose metabolism of GI function) AND ((celiac disease) OR (gastric bypass)) AND ((Diabetes) OR (diabetes)) AND ((glucocorticoids) OR (metoclopramide) OR (narcotics) OR (psychotropics)) AND ((insulin)) AND ((HPA disruption) OR (PTSD) OR (TBI) OR (depression) OR (mental health problems) OR (sleep disorders) OR (substance use)) AND ((COPD) OR (asthma)))"}
{"candidate_id": "LLM07170", "doc_id": "NCT02589353_inc", "case_bucket": "other", "source_criterion": "self-reported healthy adults between the ages of 18-60 who are fluent in English.", "candidate_expression": "((adults) AND (ages between 18-60) AND (fluent in English) AND (healthy self-reported))"}
{"candidate_id": "LLM07171", "doc_id": "NCT03190304_inc", "case_bucket": "or", "source_criterion": "Symptomatic patients with heart failure (men and women) aged >18 years, Functional class II, III or IV by the New York Heart Association (NYHA) Left ventricular ejection fraction <35% Ischemic and nonischemic etiology Type B natriuretic peptide (BNP) >150 pg/ml (or pro-BNP [N-terminal-proBNP] = 600 pg / ml) or if the patient was hospitalized for cardiac decompensation within the preceding 12 months, BNP >100 pg/ml (or N-terminal-proBNP = 400 pg / ml)", "candidate_expression": "((<35%) AND (= 400 pg / ml) AND (= 600 pg / ml) AND (>100 pg/ml) AND (>150 pg/ml) AND (>18 years) AND (BNP) AND (Functional class II, III or IV) AND (Ischemic etiology) AND (Left ventricular ejection fraction) AND (N-terminal-proBNP) AND (New York Heart Association (NYHA)) AND (Symptomatic) AND (Type B natriuretic peptide (BNP)) AND (aged) AND (cardiac decompensation) AND (heart failure) AND (hospitalized) AND (men) AND (nonischemic etiology) AND (pro-BNP [N-terminal-proBNP]) AND (within the preceding 12 months) AND (women))"}
{"candidate_id": "LLM07172", "doc_id": "NCT03125057_exc", "case_bucket": "or", "source_criterion": "Therapy area located outside of head and neck; Other skin diseases that might interfere with the efficacy evaluation; Therapy area was previously received isotope or PDT or other treatment which might interfere with the efficacy evaluation; Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Immunocompromised conditions; Electrocardiographic abnormalities or organic heart diseases; Coagulation disorders; Hepatic or renal functions abnormal (alanine aminotransferase or aspartate transaminase or total bilirubin > 1.5 upper limit of normal [ULN], or serum creatinine or blood urea nitrogen > 1.5 ULN); Psychiatric diseases; Severe endocrinopathies; Previous therapy of PWS within the last 4 weeks; Participation in any clinical studies within the last 4 weeks; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((Allergy) AND (Coagulation disorders) AND (Electrocardiographic) AND (Immunocompromised conditions) AND (PWS) AND (Participation in any clinical studies within the last 4 weeks) AND (Psychiatric diseases) AND (Scar diathesis) AND (endocrinopathies Severe) AND (skin diseases interfere with the efficacy evaluation) AND (therapy Previous within the last 4 weeks) AND (treatment might interfere with the efficacy evaluation) AND ((analogues) OR (porphyrins)) AND ((Allergic constitution) OR (Photosensitivity) OR (Porphyria)) AND ((Electrocardiographic abnormalities) OR (heart diseases organic)) AND ((Hepatic functions abnormal) OR (renal functions abnormal)) AND ((alanine aminotransferase) OR (aspartate transaminase) OR (total bilirubin)) AND ((blood urea nitrogen) OR (serum creatinine)) AND ((PDT) OR (isotope)))"}
{"candidate_id": "LLM07173", "doc_id": "NCT02805504_inc", "case_bucket": "other", "source_criterion": "Patients undergoing urologic surgery.", "candidate_expression": "(urologic surgery)"}
{"candidate_id": "LLM07174", "doc_id": "NCT02939209_exc", "case_bucket": "or", "source_criterion": "Allergy, sensitivity, or absolute contraindications to any of the medications involved in the study preexisting CNS depression, or taking regularly medication that cause CNS depression preexisting cognitive deficits, dementia, or delirium severe respiratory comorbidities (e.g. chronic obstructive pulmonary disease, pneumonia, respiratory failure) sleep disordered breathing (diagnosed OSA, obesity hypoventilation syndrome) pregnancy and breast feeding history of chronic pain or regular (at least once daily) opioid use preoperatively renal impairment - CrCl =60 mL/minute not fluent in English to be able to participate in the study process, including consent and phone interview Body Mass Index >35 inability to take oral medication.", "candidate_expression": "((=60 mL/minute) AND (>35) AND (Allergy) AND (Body Mass Index) AND (CNS depression) AND (CrCl) AND (OSA) AND (at least once daily) AND (chronic obstructive pulmonary disease) AND (chronic pain) AND (cognitive deficits) AND (contraindications) AND (delirium) AND (dementia) AND (inability) AND (medication) AND (medications) AND (not fluent in English to be able to participate in the study process, including consent and phone interview) AND (obesity hypoventilation syndrome) AND (opioid) AND (oral medication) AND (pneumonia) AND (pregnancy and breast feeding) AND (preoperatively) AND (renal impairment) AND (respiratory comorbidities) AND (respiratory failure) AND (sensitivity) AND (severe) AND (sleep disordered breathing) AND (study))"}
{"candidate_id": "LLM07175", "doc_id": "NCT02650024_inc", "case_bucket": "or", "source_criterion": "Adult (= 18 years old) subjects with chronic genotype 1 HCV and NCI with a GDS greater than or equal to 0.5 (n=60). Presence of chronic HCV infection based on chart review will be defined as positive for anti-HCV antibody or HCV RNA at least 6 months before screening. For the HIV/HCV co-infected group only, subjects must have HIV. HIV status will be obtained through self report. Self report will be confirmed at screening using a HIV-1 point of care test. In the event that point of care test and self-report are discordant, then HIV status will be confirmed by a licensed Western blot or a second antibody test. HIV/HCV co-infected subjects (n=12) must also have a HIV RNA measurement <50 copies/mL at the pre-treatment visit. Platelets >150,000 Aspartate aminotransferase (AST)/Alanine aminotransferase (ALT) <10x upper limit of normal Creatinine clearance >30 milliliters/minute/1.73 centimeter squared", "candidate_expression": "((<10x upper limit of normal) AND (<50 copies/mL) AND (= 18 years old) AND (>150,000) AND (>30 milliliters/minute/1.73 centimeter squared) AND (Adult) AND (Alanine aminotransferase (ALT)) AND (Aspartate aminotransferase (AST)) AND (Creatinine clearance) AND (GDS) AND (HCV) AND (HCV RNA) AND (HCV infection) AND (HIV) AND (HIV RNA measurement) AND (NCI) AND (Platelets) AND (anti-HCV antibody) AND (at least 6 months before screening) AND (at the pre-treatment visit) AND (chronic) AND (co-infected) AND (genotype 1) AND (greater than or equal to 0.5) AND (old) AND (positive))"}
```
