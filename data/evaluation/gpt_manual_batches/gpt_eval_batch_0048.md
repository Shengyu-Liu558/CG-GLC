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
{"candidate_id": "LLM01176", "doc_id": "NCT02464865_inc", "case_bucket": "other", "source_criterion": "obese : weight for height > median + 3 standard deviations simple obesity", "candidate_expression": "((obese) AND (simple obesity) AND (weight for height > median + 3 standard deviations))"}
{"candidate_id": "LLM01177", "doc_id": "NCT02589691_exc", "case_bucket": "or", "source_criterion": "contra-indication to inhalational induction (full stomach) contra-indication to the use of rocuronium American Society of Anesthesiologists score (ASA) III or IV intracranial surgery parental refusal absence of affiliation to social security", "candidate_expression": "((American Society of Anesthesiologists score (ASA)) AND (absence) AND (affiliation to social security) AND (contra-indication) AND (full stomach) AND (inhalational induction) AND (intracranial surgery) AND (parental refusal) AND (rocuronium) AND ((III) OR (IV)))"}
{"candidate_id": "LLM01178", "doc_id": "NCT02015923_inc", "case_bucket": "or", "source_criterion": "colorectal cancer above to 12 cm from the anal verge unresectable synchronous metastases no contraindications for chemotherapy absence of peritoneal carcinomatosis, central nervous system o bone metastasis. performance status ECOG = 2 (Eastern Cooperative Oncology Group) uncontrolled concomitant medical conditions that may compromise to chemotherapy significant symptomatic cardiac disease not pregnancy or breastfeeding", "candidate_expression": "((= 2) AND (Eastern Cooperative Oncology Group) AND (above to 12 cm from the anal verge) AND (absence) AND (cardiac disease) AND (chemotherapy) AND (colorectal cancer) AND (concomitant) AND (contraindications) AND (medical conditions that may compromise to chemotherapy) AND (metastases) AND (no) AND (not) AND (significant) AND (symptomatic) AND (synchronous) AND (uncontrolled) AND (unresectable) AND ((bone metastasis) OR (central nervous system metastasis) OR (peritoneal carcinomatosis)) AND ((ECOG) OR (performance status)) AND ((breastfeeding) OR (pregnancy)))"}
{"candidate_id": "LLM01179", "doc_id": "NCT03404479_exc", "case_bucket": "or", "source_criterion": "Secondary knee osteoarthritis Other inflammatory Knee Osteoarthritis (e.g. gout, rheumatoid arthritis, etc.) Patients presenting with gastroesophageal reflux disease, peptic ulcer. Helicobacter infected patients who have not been treated for eradication (recruitment if negative in re-examination after treatment). Short bowel syndrome that can cause inflammatory bowel disease (ulcerative colitis, Crohn's disease) and drug absorption disorder. Intestinal obstruction syndrome Unexplained abdominal pain ALT(Alanine aminotransferase) level of liver function test exceeded 5 times of reference range Total bilirubin level exceeded 2 mg / dL Serum albumin level less than 2 g / dL Ascites Hepatic encephalopathy Hepatitis B, hepatitis C (excluding healthy carriers) or HIV positive MDRD(Modification of Diet in Renal Disease) Estimated Glomerular filtration rate less than 60 mL / m2 Patients with hyperkalemia (over 5.5 meq / L) history of asthma, acute rhinitis, nasal polyps, angioedema, urticaria or allergic reactions to aspirin or other non-steroidal anti-inflammatory drugs(including COX-2 inhibitors). Malignant tumors other than basal cell or squamous cell carcinoma of the skin, CIN(Cervical Intraepitherial Neoplasia) and CIS(Carcinoma in situ) of the cervix, and intraepithelial carcinoma of other areas Within 5 years of consent date. Medical history of hypersensitivity to the components of the investigational products. (The components of test drug 1 and 2, including the Rhein-based drug) Patients with an allergic reaction to sulfonamide. Patients with galactose intolerance, lapp lactase deficiency or glucose-galactose malabsorption. Subjects who have not reached the prescribed period after receiving contraindicated medication or treatment before participation in this clinical trial. Patients receiving contraindicated medication. Alcohol and other drug abuse cases based on 6 months before screening. Pregnant women or nursing mothers who are not willing to stop breastfeeding. (1) Menopause (non-therapy-induced amenorrhea of more than 12 months) Female (2) Female infertility due to surgery (no ovaries and / or uterus) (3) If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization. (4) Female subjects who agreed to abstinence during the clinical trial period. If the subject is assured of an abstinence throughout the trial period.(e.g. clergy) However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence. (5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial: Oral contraceptive The contraceptive patch Intra uterine device (IUD) contraceptive implant contraceptive injection intrauterine hormonal apparatus Tubal ligation and infertility surgery If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials. Patients who are scheduled for surgery during the clinical trial period or who have difficulties in completing the protocol during this clinical trial due to other reasons. In addition to the above, other diseases that the investigator judges to be inappropriate.", "candidate_expression": "(((5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial:) AND (6 months before screening) AND (ALT(Alanine aminotransferase) level) AND (Alcohol abuse) AND (Ascites) AND (CIN(Cervical Intraepitherial Neoplasia)) AND (CIS(Carcinoma in situ) of the cervix) AND (COX-2 inhibitors) AND (Crohn's disease) AND (Estimated Glomerular filtration rate) AND (Female) AND (Female subjects who agreed to abstinence during the clinical trial period) AND (HIV positive) AND (Helicobacter infected) AND (Hepatic encephalopathy) AND (Hepatitis B) AND (However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence) AND (If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials.) AND (If the subject is assured of an abstinence throughout the trial period.(e.g. clergy)) AND (If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization.) AND (Intestinal obstruction syndrome) AND (Intra uterine device (IUD)) AND (MDRD(Modification of Diet in Renal Disease)) AND (Malignant tumors) AND (Menopause) AND (Oral contraceptive) AND (Other) AND (Pregnant women or nursing mothers who are not willing to stop breastfeeding) AND (Rhein-based drug) AND (Secondary) AND (Serum albumin level) AND (Short bowel syndrome) AND (Total bilirubin level) AND (Tubal ligation) AND (Unexplained) AND (Within 5 years of consent date) AND (abdominal pain) AND (acute rhinitis) AND (allergic reaction) AND (allergic reactions) AND (amenorrhea) AND (angioedema) AND (aspirin) AND (asthma) AND (basal cell carcinoma of the skin) AND (can cause) AND (components of test drug 1) AND (components of test drug 2) AND (components of the investigational products) AND (consent date) AND (contraceptive implant) AND (contraceptive injection) AND (contraceptive patch) AND (contraindicated medication) AND (drug absorption disorder) AND (drug abuse) AND (due to surgery) AND (ess than 2 g / dL) AND (exceeded 2 mg / dL) AND (exceeded 5 times of reference range) AND (excluding) AND (galactose intolerance) AND (gastroesophageal reflux disease) AND (glucose-galactose malabsorption) AND (gout) AND (healthy carriers) AND (hepatitis C) AND (hyperkalemia) AND (hypersensitivity) AND (infertility) AND (infertility surgery) AND (inflammatory Knee Osteoarthritis) AND (inflammatory bowel disease) AND (intraepithelial carcinoma) AND (intrauterine hormonal apparatus) AND (knee osteoarthritis) AND (lapp lactase deficiency) AND (less than 60 mL / m2) AND (liver function test) AND (more than 12 months) AND (nasal polyps) AND (no ovaries) AND (no uterus) AND (non-steroidal anti-inflammatory drugs) AND (non-therapy-induced) AND (not) AND (other) AND (other than) AND (over 5.5 meq / L) AND (peptic ulcer) AND (rheumatoid arthritis) AND (squamous cell carcinoma of the skin) AND (sulfonamide) AND (that can cause inflammatory bowel disease) AND (treated for eradication) AND (ulcerative colitis) AND (urticaria))"}
{"candidate_id": "LLM01180", "doc_id": "NCT01967420_inc", "case_bucket": "or", "source_criterion": "Non-affective psychosis Premorbid IQ of over 70 A service user of the early intervention service Aged 18 or over (up to the age of 35 which is the limit for the early intervention service) Psychiatrically stable enough to attend to completion (no hospitalisations or medication changes in last 4 weeks)", "candidate_expression": "((Aged 18 or over up to the age of 35) AND (Non-affective psychosis) AND (Premorbid IQ over 70) AND (Psychiatrically stable) AND (hospitalisations) AND (medication changes))"}
{"candidate_id": "LLM01181", "doc_id": "NCT03376763_exc", "case_bucket": "or", "source_criterion": "Subject who showed medically significant adverse events or intolerance with aripiprazole during screening period or as prior experiences. Subjects with a current DSM-<U+2163>-TR or 5 diagnosis other than schizophrenia, including schizoaffective disorder, major depressive disorder, bipolar disorder, delirium, dementia, amnesia, Borderline, Paranoid, Histrionic, Schizotypal, Schizoid, Antisocial or other cognitive or personality disorders. Subjects with diseases of the central nervous system that may impact the assessment of the psychotic symptoms as per investigator's opinion. Subjects who have been treated with clozapine or long-acting injectable antipsychotic drugs within 3 months prior to the screening. Subjects who have been treated over maximum maintenance dose (as specified in each label) of oral antipsychotics at screening. (e.g. Aripiprazole>30mg/day, Olanzapine>20mg/day, Risperidone > 6mg/day, Quetiapine > 750mg/day) Subjects with a significant risk of violent behaviour or a significant risk of committing suicide based on history or investigator's judgment. Subjects had a history of seizures, neuroleptic malignant syndrome, clinically significant tardive dyskinesia, or other medical condition that would expose them to undue risk or interfere with study assessments. Significant history of drug abuse disorder (including alcohol, as defined in DSM-5 substance use disorder or in the opinion of the investigator) within the last 6 months prior to screening. Subjects participating another interventional clinical trial within 30 days prior to screening. Women who are pregnant, nursing, or who plan to become pregnant while in the trial. Subjects having any other clinically significant finding of the physical examination or laboratory value that make investigator consider that it would be inappropriate to participate in this study.", "candidate_expression": "((> 6mg/day) AND (> 750mg/day) AND (>20mg/day) AND (>30mg/day) AND (Significant history of drug abuse disorder (including alcohol, as defined in DSM-5 substance use disorder or in the opinion of the investigator) within the last 6 months prior to screening.) AND (Subjects having any other clinically significant finding of the physical examination or laboratory value that make investigator consider that it would be inappropriate to participate in this study.) AND (Subjects participating another interventional clinical trial within 30 days prior to screening.) AND (Subjects with diseases of the central nervous system that may impact the assessment of the psychotic symptoms as per investigator's opinion.) AND (Women who are pregnant, nursing, or who plan to become pregnant while in the trial.) AND (aripiprazole) AND (at screening) AND (clinically significant) AND (history) AND (maximum maintenance dose) AND (medically significant) AND (oral antipsychotics) AND (other) AND (other than) AND (schizophrenia) AND (significant risk) AND (the screening) AND (within 3 months prior to the screening) AND ((DSM- 5) OR (DSM-<U+2163>-TR)) AND ((adverse events) OR (intolerance)) AND ((Antisocial disorders) OR (Borderline disorders) OR (Histrionic disorders) OR (Paranoid disorders) OR (Schizoid disorders) OR (Schizotypal disorders) OR (amnesia) OR (bipolar disorder) OR (cognitive disorders) OR (delirium) OR (dementia) OR (major depressive disorder) OR (personality disorders) OR (schizoaffective disorder)) AND ((clozapine) OR (long-acting injectable antipsychotic drugs)) AND ((Aripiprazole) OR (Olanzapine) OR (Quetiapine) OR (Risperidone)) AND ((committing suicide) OR (violent behaviour)) AND ((neuroleptic malignant syndrome) OR (seizures) OR (tardive dyskinesia)) AND ((as prior experiences) OR (during screening period)))"}
{"candidate_id": "LLM01182", "doc_id": "NCT02732080_inc", "case_bucket": "or", "source_criterion": "Patients presenting with ST-elevation acute myocardial infarction (STEMI) within 12 hours of their symptom onset in whom TIMI-3 flow was established in infarct related artery (IRA) after balloon angioplasty or thrombectomy.", "candidate_expression": "((ST-elevation acute myocardial infarction (STEMI)) AND (TIMI-3 flow was established) AND (after balloon angioplasty or thrombectomy) AND (balloon angioplasty) AND (balloon angioplasty or thrombectomy) AND (infarct related artery (IRA)) AND (their symptom onset) AND (thrombectomy) AND (within 12 hours of their symptom onset))"}
{"candidate_id": "LLM01183", "doc_id": "NCT00609531_inc", "case_bucket": "or", "source_criterion": "Ambulatory status (outpatient) at time of consent Age 10-55 years Clinical diagnosis of Autism Spectrum Disorder IQ greater than or equal to 70 Score greater than 8 on Children's Yale-Brown Obsessive Compulsive Scale Free of psychoactive medication for at least: one month for fluoxetine; two weeks for other SSRIs and neuroleptics; and five days for stimulants prior to MRI scanning [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder]", "candidate_expression": "((Age 10-55 years) AND (Ambulatory status at time of consent) AND (Autism Spectrum Disorder Clinical diagnosis) AND (Children's Yale-Brown Obsessive Compulsive Scale greater than 8) AND (IQ greater than or equal to 70) AND (SSRIs) AND (fluoxetine at least one month) AND (neuroleptics) AND (outpatient) AND (seizure disorder) AND (stimulants at least five days greater than three months) AND NOT (psychoactive medication) AND NOT (anticonvulsant medication stable doses))"}
{"candidate_id": "LLM01184", "doc_id": "NCT02396420_exc", "case_bucket": "or", "source_criterion": "History of prostate, bladder, or rectal cancer History of transurethral resection of the prostate (TURP), open prostate surgery, or radiofrequency or microwave therapies History of open bladder, rectosigmoid colon, or other pelvic surgery Patient is unwilling to discontinue alpha blockers 1 month after study treatment Patient is unwilling to discontinue 5-alph reductase inhibitors 1 month after study treatment Neurogenic bladder or other neurologic disorder impacting bladder function such as Parkinson's disease, multiple sclerosis, cerebral vascular accident or diabetes Any other confounding bladder or urethral pathology, including urethral stricture, bladder neck contracture, or bladder atonia Active prostatitis or urinary tract infection Cystolithiasis within the past 3 months Serum creatinine > 1.7mg/dL Inability to discontinue oral anticoagulant 2-5 days prior to study treatment Coagulation disturbances not normalized by medical treatment Iodinated contrast allergy that, in the opinion of the Investigator, cannot be adequately premedicated Gelatin allergy Known severe peripheral vascular disease or major iliac arterial occlusive disease Interest in future fertility Clinically significant cardiac arrhythmia or other cardiac disease (including congestive heart failure), uncontrolled diabetes mellitus, clinically significant respiratory disease, or known immunosuppression Other condition that the Investigator believes puts the patient at risk for a complication during the procedure", "candidate_expression": "((5-alph reductase inhibitors 1 month after study treatment) AND (Coagulation disturbances normalized) AND (Cystolithiasis within the past 3 months) AND (Gelatin) AND (Interest in future fertility) AND (Iodinated contrast) AND (Other condition that the Investigator believes puts the patient at risk for a complication during the procedure) AND (Serum creatinine > 1.7mg/dL) AND (allergy) AND (alpha blockers 1 month after study treatment) AND (clinically significant) AND (congestive heart failure) AND (major) AND (medical treatment) AND (neurologic disorder impacting bladder function) AND (open bladder surgery) AND (oral anticoagulant 2-5 days prior to study treatment) AND (pelvic surgery) AND (rectosigmoid colon surgery) AND (severe) AND ((Neurogenic bladder) OR (Parkinson's disease) OR (cerebral vascular accident) OR (diabetes) OR (multiple sclerosis)) AND ((bladder cancer) OR (prostate cancer) OR (rectal cancer)) AND ((bladder atonia) OR (bladder neck contracture) OR (urethral stricture)) AND ((bladder pathology) OR (urethral pathology)) AND ((prostatitis Active) OR (urinary tract infection Active)) AND ((iliac arterial occlusive disease major) OR (peripheral vascular disease severe)) AND ((cardiac arrhythmia) OR (cardiac disease) OR (diabetes mellitus uncontrolled) OR (immunosuppression) OR (respiratory disease clinically significant)) AND ((microwave therapies) OR (open prostate surgery) OR (radiofrequency) OR (transurethral resection of the prostate (TURP))))"}
{"candidate_id": "LLM01185", "doc_id": "NCT02112734_exc", "case_bucket": "or", "source_criterion": "Infants who have already received postnatal vitamin D supplementation prematurity (<37 weeks)/low birthweight <2500 g poor health due to a current or past significant disease state or congenital abnormality.", "candidate_expression": "((Infants) AND (birthweight <2500 g) AND (congenital abnormality) AND (low birthweight) AND (poor health current past) AND (postnatal vitamin D supplementation) AND (prematurity) AND (significant disease state) AND (vitamin D))"}
{"candidate_id": "LLM01186", "doc_id": "NCT02209545_exc", "case_bucket": "or", "source_criterion": "Patients who have had a prior abdominal myomectomy Post-menopausal women Patients with known bleeding/clotting disorders Patients with a history of gynecologic malignancy History of allergic reactions attributed to compounds of similar chemical or biologic composition to misoprostol Any cases converted to abdominal hysterectomy or other additional elective surgical procedures performed at time of abdominal myomectomy will be excluded from data analysis Uncontrolled intercurrent illness including, but not limited to, ongoing or active infection, symptomatic congestive heart failure, unstable angina pectoris, cardiac arrhythmia, or psychiatric illness/social situations that would limit compliance with study requirements.", "candidate_expression": "((Post-menopausal) AND (abdominal hysterectomy converted to) AND (abdominal myomectomy) AND (abdominal myomectomy prior) AND (allergic reactions History) AND (cardiac arrhythmia) AND (clotting disorders) AND (compounds of similar chemical or biologic composition to misoprostol) AND (congestive heart failure symptomatic) AND (disorders bleeding) AND (gynecologic malignancy history) AND (infection ongoing active) AND (intercurrent illness Uncontrolled) AND (misoprostol) AND (psychiatric illness) AND (social situations that would limit compliance with study requirements) AND (surgical procedures other additional elective at time of abdominal myomectomy) AND (unstable angina pectoris) AND (women))"}
{"candidate_id": "LLM01187", "doc_id": "NCT02334631_inc", "case_bucket": "other", "source_criterion": "Patients undergoing small bowel video capsule endoscopy", "candidate_expression": "(small bowel video capsule endoscopy)"}
{"candidate_id": "LLM01188", "doc_id": "NCT01891383_exc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. History of penetrating brain injury 2. History of disabling neurological or psychiatric condition such as epilepsy (besides posttraumatic epilepsy), multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia Controls (without a history of TBI): History of disabling neurological or psychiatric condition such as epilepsy, multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia", "candidate_expression": "((History) AND (disabling neurological condition) AND (disabling psychiatric condition) AND (penetrating brain injury History) AND NOT (posttraumatic epilepsy) AND ((cortical stroke) OR (encephalitis) OR (epilepsy) OR (hypoxic-ischemic encephalopathy) OR (multiple sclerosis) OR (schizophrenia)) AND ((condition disabling neurological) OR (psychiatric condition disabling)))"}
{"candidate_id": "LLM01189", "doc_id": "NCT02269137_exc", "case_bucket": "or", "source_criterion": "hypoglycemia SE;psychogenic SE;any other pseudo-SE", "candidate_expression": "((hypoglycemia SE) AND (pseudo-SE) AND (psychogenic SE))"}
{"candidate_id": "LLM01190", "doc_id": "NCT03344887_inc", "case_bucket": "other", "source_criterion": "All patients (excluding neonates) requiring one or more allogeneic RBC transfusions for the treatment of anemia will be included.", "candidate_expression": "((RBC transfusions requiring one or more allogeneic) AND (anemia) AND (treatment) AND NOT (neonates))"}
{"candidate_id": "LLM01191", "doc_id": "NCT01424020_exc", "case_bucket": "or", "source_criterion": "Unable to participate for administrative reasons Psychiatric troubles Pain at rest or critical limb ischemia Unable to walk (ex: wheelchair subjects)", "candidate_expression": "((Pain at rest) AND (Psychiatric troubles) AND (Unable to participate) AND (Unable to walk) AND (administrative reasons) AND (critical limb ischemia) AND (wheelchair subjects))"}
{"candidate_id": "LLM01192", "doc_id": "NCT03373669_exc", "case_bucket": "or", "source_criterion": "Presence of a significant medical or psychiatric condition (Examples include: Diagnosis and treatment of tuberculosis (TB) or HIV; renal insufficiency; hepatic disease; oral or parenteral medication known to affect the immune function, such as corticosteroids, other immunosuppressant drugs; or behavioural or memory issues) Ever having received oral cholera vaccine. Receipt of an investigational product (within 30 days before vaccination). History of diarrhoea in 7 days prior to first dose of vaccine (defined as =3 unformed loose stools in 24 hours). History of chronic diarrhea (lasting for more than 2 weeks in the past 6 months) Current use of laxatives, antacids, or other agents to lower stomach acidity? Planning to become pregnant in the next 2 years.", "candidate_expression": "((=3) AND (HIV) AND (History) AND (Planning to become pregnant in the next 2 years.) AND (Receipt of an investigational product (within 30 days before vaccination).) AND (agents to lower stomach acidity) AND (antacids) AND (behavioural issues) AND (chronic diarrhea) AND (corticosteroids) AND (diarrhoea) AND (first dose of vaccine) AND (hepatic disease) AND (immunosuppressant drugs) AND (in 7 days prior to first dose of vaccine) AND (in the past 6 months) AND (known to affect the immune function) AND (lasting for more than 2 weeks) AND (laxatives) AND (medical condition) AND (memory issues) AND (oral cholera vaccine) AND (oral medication) AND (other) AND (parenteral medication) AND (psychiatric condition) AND (renal insufficiency) AND (significant) AND (treatment) AND (tuberculosis (TB)) AND (unformed loose stools in 24 hours))"}
{"candidate_id": "LLM01193", "doc_id": "NCT02643381_inc", "case_bucket": "or", "source_criterion": "Adult patient (male or female) requiring emergency endotracheal intubation.", "candidate_expression": "((Adult) AND (emergency endotracheal intubation) AND ((female) OR (male)))"}
{"candidate_id": "LLM01194", "doc_id": "NCT02618057_exc", "case_bucket": "or", "source_criterion": "Immunosuppresant host Chronic cardiovascular/pulmonary disease Hospital acquired infection", "candidate_expression": "((Hospital acquired infection) AND (Immunosuppresant host) AND ((cardiovascular disease) OR (pulmonary disease)))"}
{"candidate_id": "LLM01195", "doc_id": "NCT02604459_exc", "case_bucket": "or", "source_criterion": "Inability to follow directions or comprehend the English language Severe uncorrected visual or auditory handicaps Delirium at screening or baseline Emergency surgery", "candidate_expression": "((Delirium at screening at baseline) AND (Emergency surgery) AND (Inability to comprehend the English language) AND (Inability to follow directions) AND (auditory handicaps) AND (handicaps visual))"}
{"candidate_id": "LLM01196", "doc_id": "NCT03190304_exc", "case_bucket": "or", "source_criterion": "History of hypersensitivity or allergy to any of the study drugs, drugs of similar chemical classes, ACE inhibitors (ACEIs), angiotensin II receptor blockers (ARBs), or neprilysin inhibitors, as well as known or suspected contraindications to the study drugs. Previous history of intolerance to recommended target doses of ACEIs or ARBs. Known history of angioedema. Requirement for treatment with both ACEIs and ARBs. Current acute decompensated heart failure (exacerbation of chronic heart failure manifested by signs and symptoms that may require intravenous therapy). Symptomatic hypotension. Estimated glomerular filtration rate (eGFR) <30%. Serum potassium >5.4 mmol/L. Acute coronary syndrome, stroke, transient ischaemic attack, cardiac, carotid, or other major cardiovascular surgery, percutaneous coronary intervention, or carotid angioplasty within the 3 months. Coronary or carotid artery disease likely to require surgical or percutaneous intervention within the 6 months. Implantation of a cardiac resynchronization therapy (CRT) device within 3 months or intent to implant a CRT. History of heart transplant or on a transplant list or with left ventricular (LV) assistance device. History of severe pulmonary disease. Diagnosis of peripartum- or chemotherapy-induced cardiomyopathy within the 12 months. Documented untreated ventricular arrhythmia with syncopal episodes within the 3 months. Symptomatic bradycardia or second- or third-degree atrioventricular block without a pacemaker. Presence of haemodynamically significant mitral and/or aortic valve disease, except mitral regurgitation secondary to LV dilatation. Presence of other haemodynamically significant obstructive lesions of the LV outflow tract, including aortic and subaortic stenosis. Any surgical or medical condition which might significantly alter the absorption, distribution, metabolism, or excretion of study drugs, including, but not limited to, any of the following: History of active inflammatory bowel disease during the 12 months. Active duodenal or gastric ulcers during the 3 months. Evidence of hepatic disease as determined by any one of the following: aspartate aminotransferase or alanine aminotransferase values exceeding 2x upper limit of normal, history of hepatic encephalopathy, history of oesophageal varices, or history of porto-caval shunt. Current treatment with cholestyramine or colestipol resins. Presence of any other disease with a life expectancy of <5 years.", "candidate_expression": "((<30%) AND (<5 years) AND (>5.4 mmol/L) AND (ACE inhibitors (ACEIs)) AND (ACEIs) AND (ARBs) AND (Active) AND (Acute coronary syndrome) AND (CRT) AND (Coronary artery disease) AND (Current) AND (Estimated glomerular filtration rate (eGFR)) AND (Evidence) AND (History) AND (Implantation) AND (LV dilatation) AND (LV outflow tract) AND (Previous) AND (Requirement for) AND (Serum potassium) AND (Symptomatic) AND (active) AND (acute) AND (alanine aminotransferase) AND (allergy) AND (alter the absorption, distribution, metabolism, or excretion) AND (angioedema) AND (angiotensin II receptor blockers (ARBs)) AND (any other) AND (aortic stenosis) AND (aortic valve disease) AND (aspartate aminotransferase) AND (atrioventricular block) AND (bradycardia) AND (cardiac) AND (cardiac resynchronization therapy (CRT) device) AND (cardiomyopathy) AND (carotid) AND (carotid angioplasty) AND (carotid artery disease) AND (chemotherapy) AND (chemotherapy-induced) AND (cholestyramine resins) AND (chronic heart failure) AND (colestipol resins) AND (contraindications) AND (decompensated) AND (disease) AND (duodenal ulcers) AND (during the 12 months) AND (during the 3 months) AND (exacerbation) AND (exceeding 2x upper limit of normal) AND (except) AND (gastric ulcers) AND (haemodynamically significant) AND (heart failure) AND (heart transplant) AND (hepatic disease) AND (hepatic encephalopathy) AND (history) AND (hypersensitivity) AND (hypotension) AND (implant) AND (inflammatory bowel disease) AND (intent) AND (intolerance) AND (intravenous therapy) AND (known) AND (left ventricular (LV) assistance device) AND (life expectancy) AND (likely) AND (major cardiovascular surgery) AND (medical condition) AND (mitral regurgitation) AND (mitral valve disease) AND (neprilysin inhibitors) AND (obstructive lesions) AND (oesophageal varices) AND (on a transplant list) AND (pacemaker) AND (percutaneous coronary intervention) AND (percutaneous intervention) AND (peripartum) AND (peripartum- induced) AND (porto-caval shunt) AND (second- degree) AND (secondary to LV dilatation) AND (severe pulmonary disease) AND (signs) AND (stroke) AND (study drugs) AND (subaortic stenosis) AND (surgical condition) AND (surgical intervention) AND (suspected) AND (symptoms) AND (syncopal episodes) AND (third-degree) AND (transient ischaemic attack) AND (treatment) AND (untreated) AND (ventricular arrhythmia) AND (within 3 months) AND (within the 12 months) AND (within the 3 months) AND (within the 6 months) AND (without))"}
{"candidate_id": "LLM01197", "doc_id": "NCT03333655_exc", "case_bucket": "or", "source_criterion": "Participants taking CPI combination therapies with chemotherapy are not permitted. Pregnant, lactating, or intending to become pregnant during the study.", "candidate_expression": "((CPI combination therapies) AND (chemotherapy) AND ((Pregnant) OR (lactating) OR (pregnant intending to become during the study)))"}
{"candidate_id": "LLM01198", "doc_id": "NCT02186600_exc", "case_bucket": "or", "source_criterion": "Have osteoporosis Have a 10 yr probability of hip fracture >3% or major fracture >20% based on results of the FRAX tool Currently take bisphosphonates, estrogen replacement therapy, glucocorticosteroids, or other drugs affecting bone Currently participate in a resistance training or high impact weight bearing exercise program two or more times weekly Weigh >300 lbs Have abnormal results for the following laboratory tests: serum 25(OH)D; serum creatinine; serum calcium; PTH; TSH Have Paget's disease, heart disease, uncontrolled hypertension, renal disease, or other concomitant conditions that prohibit participation in exercises, risedronate therapy, or use of CaD supplements.", "candidate_expression": "((10 yr probability of hip fracture >3%) AND (10 yr probability of major fracture >20%) AND (CaD supplements) AND (PTH abnormal results) AND (Paget's disease) AND (TSH abnormal results) AND (Weigh >300 lbs) AND (bisphosphonates) AND (drugs affecting bone) AND (estrogen replacement therapy) AND (glucocorticosteroids) AND (heart disease) AND (hip fracture) AND (major fracture) AND (osteoporosis) AND (other concomitant conditions that prohibit participation in exercises) AND (participate in a resistance training two or more times weekly) AND (participate in high impact weight bearing exercise two or more times weekly) AND (renal disease) AND (risedronate therapy) AND (serum 25(OH)D abnormal results) AND (serum calcium abnormal results) AND (serum creatinine abnormal results) AND (uncontrolled hypertension))"}
{"candidate_id": "LLM01199", "doc_id": "NCT02958566_inc", "case_bucket": "or", "source_criterion": "Males or females above the age of 18 Patients undergoing laparoscopic or robotic colorectal resections", "candidate_expression": "((Males) AND (age above the age of 18 laparoscopic) AND (colorectal resections robotic) AND (females))"}
{"candidate_id": "LLM01200", "doc_id": "NCT02019160_inc", "case_bucket": "other", "source_criterion": "Kindergarteners who have joined our outreach dental service will be invited to join this study. Preschool children aged 3-4 years who have tooth decay and are attending the first year of kindergarten will be invited to join this study.", "candidate_expression": "((Kindergarteners) AND (Preschool children) AND (aged 3-4 years) AND (tooth decay))"}
```
