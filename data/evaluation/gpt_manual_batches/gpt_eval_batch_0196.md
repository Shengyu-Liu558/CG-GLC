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
{"candidate_id": "LLM04876", "doc_id": "NCT00806936_exc", "case_bucket": "or", "source_criterion": "Known or suspected allergy to trial product(s) or related products Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit Subjects who previously enrolled in this study Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods The receipt of any investigational product within 3 months prior to this trial", "candidate_expression": "((Females) AND (Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods) AND (Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit) AND (Subjects who previously enrolled in this study) AND (adequate) AND (allergy related products) AND (allergy to trial product(s)) AND (breast-feeding) AND (childbearing potential) AND (contraceptive methods) AND (intend to become) AND (investigational product) AND (not) AND (pregnant) AND (related products) AND (this trial) AND (trial product(s)) AND (within 3 months prior to this trial))"}
{"candidate_id": "LLM04877", "doc_id": "NCT03304496_exc", "case_bucket": "or", "source_criterion": "Pregnant. Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent. With acute myocardial infarction with ST segment elevation in the first 12 hours from the onset of symptoms. With any acute coronary syndrome complicated with acute pulmonary edema, cardiogenic shock and / or malignant ventricular arrhythmias. In which a cardiac catheterization is planned a priori to be performed via femoral, brachial or ulnar. Patients in whom first attempt of arterial puncture is performed by 2nd year interventional cardiology fellow or by physician in charge. Participating in another clinical trial. Be allergic or have contraindications to nitroglycerin or other nitrates. Any phosphodiesterase 5 inhibitor (sildenafil, tadalafil, avanafil, vardenafil) has been taken within 72 hours prior to the study.", "candidate_expression": "((Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent) AND (Pregnant) AND (ST segment elevation) AND (acute coronary syndrome) AND (acute myocardial infarction in the first 12 hours from the onset of symptoms) AND (cardiac catheterization) AND (phosphodiesterase 5 inhibitor within 72 hours prior to the study) AND ((brachial) OR (femoral) OR (ulnar)) AND ((allergic) OR (contraindications)) AND ((nitrates) OR (nitroglycerin)) AND ((avanafil) OR (sildenafil) OR (tadalafil) OR (vardenafil)) AND ((acute pulmonary edema) OR (cardiogenic shock) OR (ventricular arrhythmias malignant)))"}
{"candidate_id": "LLM04878", "doc_id": "NCT02953873_inc", "case_bucket": "other", "source_criterion": "At least 18 years of age Signed informed consent African American race History of a solitary renal transplant Stable tacrolimus dose for at least 2 weeks prior to randomization", "candidate_expression": "((African American) AND (At least 18 years) AND (Signed informed consent) AND (Stable dose) AND (age) AND (for at least 2 weeks prior to randomization) AND (race) AND (randomization) AND (renal transplant) AND (solitary) AND (tacrolimus))"}
{"candidate_id": "LLM04879", "doc_id": "NCT02924090_inc", "case_bucket": "or", "source_criterion": "Adults patients aged 18 to 85 years Diagnosed with Major Depressive Disorder, unipolar or bipolar depression Undergoing ECT for treatment of their symptoms Currently residing in Manitoba", "candidate_expression": "((Adults) AND (Currently residing) AND (ECT Undergoing) AND (Major Depressive Disorder) AND (Manitoba) AND (aged 18 to 85 years) AND (bipolar depression) AND (unipolar depression))"}
{"candidate_id": "LLM04880", "doc_id": "NCT02953873_inc", "case_bucket": "other", "source_criterion": "At least 18 years of age Signed informed consent African American race History of a solitary renal transplant Stable tacrolimus dose for at least 2 weeks prior to randomization", "candidate_expression": "((African American) AND (At least 18 years) AND (Signed informed consent) AND (Stable dose) AND (age) AND (for at least 2 weeks prior to randomization) AND (race) AND (randomization) AND (renal transplant) AND (solitary) AND (tacrolimus))"}
{"candidate_id": "LLM04881", "doc_id": "NCT01884337_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding Known or suspected, acquired or bleeding or coagulation disorder in the subject or a first degree relative Active bleeding or at high risk for bleeding. Brain, spinal, ophthalmologic, or major surgery or trauma within the past 90 days other than the elective knee/hip surgery Active hepatobiliary disease Hemoglobin <9 g/dL Platelet count <100,000/mm3 Creatinine clearance <30 mL/min", "candidate_expression": "((Creatinine clearance <30 mL/min) AND (Hemoglobin <9 g/dL) AND (Platelet count <100,000/mm3) AND (Women) AND (acquired disorder) AND (bleeding Active) AND (bleeding at high risk for Brain spinal ophthalmologic) AND (bleeding disorder) AND (breastfeeding Known suspected) AND (coagulation disorder) AND (elective hip surgery) AND (elective knee surgery) AND (first degree relative) AND (hepatobiliary disease Active) AND (in the subject) AND (pregnant) AND (surgery major) AND (trauma))"}
{"candidate_id": "LLM04882", "doc_id": "NCT00182520_exc", "case_bucket": "or", "source_criterion": "Any other primary DSM-IV diagnosis; DSM-IV criteria for body dysmorphic disorder, bipolar affective disorder, schizophrenia, psychotic disorder, current alcohol/substance abuse. A previous adequate trial of topiramate Comorbid major depressive disorder diagnosis which predates OCD diagnosis Cognitive behavioural therapy or additional psychotherapy in past four months Allergy or hypersensitivity to topiramate BMI < 20 History of kidney stones", "candidate_expression": "((< 20) AND (BMI) AND (Comorbid) AND (DSM-IV) AND (DSM-IV criteria) AND (History of) AND (OCD diagnosis) AND (additional) AND (diagnosis) AND (in past four months) AND (kidney stones) AND (major depressive disorder) AND (predates OCD diagnosis) AND (previous) AND (primary) AND (topiramate) AND ((alcohol abuse) OR (bipolar affective disorder) OR (body dysmorphic disorder) OR (psychotic disorder,) OR (schizophrenia) OR (substance abuse)) AND ((Cognitive behavioural therapy) OR (psychotherapy)) AND ((Allergy) OR (hypersensitivity)))"}
{"candidate_id": "LLM04883", "doc_id": "NCT03637946_exc", "case_bucket": "or", "source_criterion": "With severe systemic alteration; In the use of antibiotics and anti-inflammatories in the last three months; With periodontium with periodontal parameters different from those established in the inclusion criteria. Individuals with clinical signs of parafunctional habits; Smoking; Individuals who have performed other restorations in the last 12 months; Pregnant women and infants; Periodontal sites that presented bleeding during crevicular fluid collection or sites that prevent proper collection of clinical parameters.", "candidate_expression": "((Pregnant) AND (Smoking) AND (anti-inflammatories) AND (antibiotics) AND (clinical signs of parafunctional habits) AND (in the last 12 months) AND (in the last three months) AND (infants) AND (other restorations) AND (severe) AND (systemic alteration) AND (women))"}
{"candidate_id": "LLM04884", "doc_id": "NCT02968602_inc", "case_bucket": "or", "source_criterion": "DSM-IV or DSM-5 diagnosis of schizophrenia or schizoaffective disorder Male or Female Age: 18 to 65 years Caucasian or Non-Caucasian Smoke at least 10 cigarettes daily Urine cotinine level ? 100 ng/ml (NicAlert(r) reading ? 3) Agrees to wear a head mounted display (HMD) for up to 45 minutes Able to complete the Evaluation to Sign Consent (ESC) with minimum score of 80%", "candidate_expression": "((18 to 65 years) AND (? 100 ng/ml) AND (? 3) AND (Able to complete) AND (Age) AND (Agrees to wear) AND (Caucasian) AND (DSM-5) AND (DSM-IV) AND (Evaluation to Sign Consent (ESC)) AND (Female) AND (Male) AND (NicAlert(r)) AND (Non-Caucasian) AND (Smoke) AND (Urine cotinine level) AND (at least 10 cigarettes daily) AND (for up to 45 minutes) AND (head mounted display (HMD)) AND (minimum score of 80%) AND (schizoaffective disorder) AND (schizophrenia))"}
{"candidate_id": "LLM04885", "doc_id": "NCT03168178_exc", "case_bucket": "or", "source_criterion": "Known fetal anomaly Other indication for intrapartum antibiotics (endocarditis prophylaxis, other known maternal infection)", "candidate_expression": "((fetal anomaly) AND (indication) AND (intrapartum antibiotics) AND ((endocarditis prophylaxis) OR (maternal infection)))"}
{"candidate_id": "LLM04886", "doc_id": "NCT01866800_inc", "case_bucket": "other", "source_criterion": "Subject is 65 years old who is able and willing to give an informed consent. Patients undergoing planned trans-femoral TAVI. Calculated eGFR below 60ml/min/1.73m2 (MDRD)", "candidate_expression": "((Calculated eGFR below 60ml/min/1.73m2) AND (able and willing to give an informed consent) AND (old 65 years) AND (trans-femoral TAVI undergoing planned))"}
{"candidate_id": "LLM04887", "doc_id": "NCT03404804_exc", "case_bucket": "or", "source_criterion": "Children will be excluded if they have a history of developmental delay or inability to communicate the effects of an allergic reaction (non-verbal). Any contraindication to allergy testing will also result in exclusion (i.e. history of a severe allergic reaction to skin tests,, anaphylaxis in the past six weeks, pregnancy, child took any antihistamine in the past three days [including diphenhydramine (Benadryl®), cetirizine (Zyrtec®), loratadine (Claritin®), fexofenadine (Allegra®), levocetirizine (Xyzal®), and desloratadine (Clarinex®)] or child has a history of a condition that requires a beta blocker medicine for cardiac conditions, high blood pressure, migraine headaches, or eye drops for glaucoma (e.g. propranolol, metoprolol, atenolol and Timoptic®, or Betoptic® eye drops). Children who present to the PED with a rash, vomiting or current asthma symptoms including coughing, wheezing or breathing problems will also be excluded to ensure these do not mask reactions to an oral challenge. Patients being admitted to the hospital or those who are deemed too acutely ill for participation (triage level 1 or 2 or as determined by the ED patient care team) will be excluded from the study. During this pilot study, we will exclude non-English speaking families. However, in subsequent studies we will include the non-English speaking population. Children who are wards of the state, in foster care or police custody or detention will be excluded. Children with any basal condition (trauma, infection, minor accidents, etc..) will be able to participate in the study provided they and their family are willing and do not meet the above-mentioned exclusion criteria.", "candidate_expression": "((Allegra) AND (Benadryl) AND (Betoptic) AND (Children) AND (Clarinex) AND (Claritin) AND (PED) AND (Xyzal) AND (Zyrtec) AND (allergic reaction) AND (allergy testing) AND (anaphylaxis) AND (antihistamine) AND (basal condition) AND (beta blocker medicine) AND (contraindication) AND (current) AND (eye drops) AND (glaucoma) AND (history) AND (in the past six weeks) AND (in the past three days) AND (non-English speaking) AND (non-verbal) AND (pregnancy) AND (severe allergic reaction) AND (skin tests) AND ((cetirizine) OR (desloratadine) OR (diphenhydramine) OR (fexofenadine) OR (levocetirizine) OR (loratadine)) AND ((developmental delay) OR (inability to communicate the effects)) AND ((cardiac conditions) OR (high blood pressure) OR (migraine headaches)) AND ((Timoptic) OR (atenolol) OR (eye drops) OR (metoprolol) OR (propranolol)) AND ((asthma symptoms) OR (rash) OR (vomiting)) AND ((breathing problems) OR (coughing) OR (wheezing)) AND ((detention) OR (foster care) OR (police custody) OR (wards of the state)) AND ((infection) OR (minor accidents) OR (trauma)))"}
{"candidate_id": "LLM04888", "doc_id": "NCT01630954_inc", "case_bucket": "other", "source_criterion": "Ultrasound confirmed complete mole", "candidate_expression": "((Ultrasound) AND (complete mole))"}
{"candidate_id": "LLM04889", "doc_id": "NCT03282006_exc", "case_bucket": "or", "source_criterion": "Bacterial infection origin from another organ (e.g. pneumonia) Severe sepsis with multiorgan failure Perinephritic abscess Pyonephrosis requiring drainage Allergy to pivmecillinam E.coli isolate resistant to pivmecillinam Pregnancy/breastfeeding Severe neutropenia Prostatitis Severe kidney failure (eGFR<15 ml/min) Using valproate", "candidate_expression": "((<15 ml/min) AND (Allergy) AND (Bacterial infection) AND (E.coli isolate) AND (Perinephritic abscess) AND (Pregnancy) AND (Prostatitis) AND (Pyonephrosis) AND (Severe) AND (Severe sepsis) AND (another organ) AND (breastfeeding) AND (drainage) AND (eGFR) AND (kidney failure) AND (multiorgan failure) AND (neutropenia) AND (pivmecillinam) AND (pneumonia) AND (requiring) AND (resistant to pivmecillinam) AND (valproate))"}
{"candidate_id": "LLM04890", "doc_id": "NCT02893293_exc", "case_bucket": "or", "source_criterion": "Contraindications for magnetic resonance imaging Hemosiderosis/hemochromatosis ( patients can still be included in the non-ferumoxytol arm)", "candidate_expression": "((Contraindications) AND (magnetic resonance imaging) AND ((Hemosiderosis) OR (hemochromatosis)))"}
{"candidate_id": "LLM04891", "doc_id": "NCT00397215_inc", "case_bucket": "or", "source_criterion": "Subjects who the investigator believes that they can and will comply with the requirements of the protocol should be enrolled in the study. A male or female aged 61 years or above at the time of the first vaccination. Written informed consent obtained from the subject. Healthy subjects or subjects with well controlled underlying disease.", "candidate_expression": "((61 years or above) AND (Written informed consent) AND (aged) AND (can and will comply with the requirements of the protocol) AND (well controlled) AND ((Healthy) OR (underlying disease)) AND ((female) OR (male)))"}
{"candidate_id": "LLM04892", "doc_id": "NCT02287259_exc", "case_bucket": "or", "source_criterion": "don't have Diabetes and abnormal metabolism of sugar not noticed as bipolar disorder have an organic brain disease pregnant or breastfeeding women don't have heart disease have actively suicidal thought(Suicidal ideation score of MADRS is 6) who are judged by the investigator to should be excluded from the study", "candidate_expression": "((6) AND (Suicidal ideation score of MADRS) AND (actively suicidal thought) AND (bipolar disorder) AND (don't have) AND (heart disease) AND (judged by the investigator to should be excluded from the study) AND (not) AND (noticed) AND (organic brain disease) AND (women) AND ((breastfeeding) OR (pregnant)) AND ((Diabetes) OR (abnormal metabolism of sugar)))"}
{"candidate_id": "LLM04893", "doc_id": "NCT02600000_inc", "case_bucket": "scope", "source_criterion": "Diagnosis of Heart Failure; Lower left ventricular ejection fraction 45% (LVEF <45%) assessed by simple and recent echocardiogram; Functional Class II and III by the New York Heart Association (NYHA) Clinically stable; Ex-smokers over five years; Maximal inspiratory pressure (MIP) <70% of predicted; Forced expiratory volume/Forced vital capacity (FEV1 / FVC) > 70% of predicted;", "candidate_expression": "((45%) AND (<45%) AND (<70% of predicted) AND (> 70% of predicted) AND (Class II and III) AND (Clinically stable) AND (Ex-smokers) AND (Forced expiratory volume/Forced vital capacity (FEV1 / FVC)) AND (Heart Failure) AND (LVEF) AND (Lower left ventricular ejection fraction) AND (Maximal inspiratory pressure (MIP)) AND (New York Heart Association (NYHA)) AND (echocardiogram) AND (over five years) AND (recent))"}
{"candidate_id": "LLM04894", "doc_id": "NCT03506477_exc", "case_bucket": "or", "source_criterion": "Form of diagnosed psoriasis other than chronic plaque psoriasis (i.e. guttate, erythrodermic, pustular) Diagnosis of other active, ongoing skin diseases or skin infections that may interfere with examination of psoriasis lesions Ongoing use of other psoriasis treatment including but not limited to topical or systemic corticosteroids, other topical medications (i.e. coal tar), oral or biologic medications for the treatment of psoriasis, and UV therapy. The following washout periods will be required: 2 weeks for topical therapy; 2 weeks for phototherapy; 12 weeks for biologic or targeted therapies; 4 weeks for other systemic therapies Use of oral estrogen therapy, excluding oral contraceptive pills Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception. Patients unwilling to limit exposure to UV light Current significant medical problems that, in the discretion of the investigator, would put the patient at significant risk Patients with disorders of calcium metabolism and/or hypercalcemia Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer) History of allergy to any component of the IP", "candidate_expression": "((Ongoing) AND (UV therapy) AND (Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer)) AND (Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception.) AND (active) AND (allergy) AND (any component of the IP) AND (biologic medications) AND (chronic plaque psoriasis) AND (coal tar) AND (disorders of calcium metabolism) AND (erythrodermic) AND (excluding) AND (guttate) AND (hypercalcemia) AND (limit exposure to UV light) AND (ongoing) AND (oral contraceptive pills) AND (oral estrogen therapy) AND (oral medications) AND (other than) AND (psoriasis) AND (pustular) AND (skin diseases) AND (skin infections) AND (systemic corticosteroids) AND (topical corticosteroids) AND (topical medications) AND (treatment) AND (unwilling))"}
{"candidate_id": "LLM04895", "doc_id": "NCT03431831_exc", "case_bucket": "or", "source_criterion": "Inability to understand and read English. Women pregnant or lactating. persons with terminal illness", "candidate_expression": "((Inability to understand and read English) AND (Women) AND (lactating) AND (pregnant) AND (terminal illness))"}
{"candidate_id": "LLM04896", "doc_id": "NCT03297125_exc", "case_bucket": "or", "source_criterion": "Optune compliance < 75%; they would be excluded from the final analyses. History of craniectomy or significant skull defect (contraindication to Optune). Active implantable medical device (i.e. DBS, spinal cord stimulator, pacemaker, defibrillator, vagus nerve stimulator, programmable shunt). Karnofsky Performance Status (KPS) < 60.", "candidate_expression": "((< 60) AND (< 75%) AND (Active) AND (KPS) AND (Karnofsky Performance Status) AND (Optune) AND (Optune compliance) AND (contraindication) AND (implantable medical device) AND (significant) AND ((DBS) OR (defibrillator) OR (pacemaker) OR (programmable shunt) OR (spinal cord stimulator) OR (vagus nerve stimulator)) AND ((craniectomy) OR (skull defect)))"}
{"candidate_id": "LLM04897", "doc_id": "NCT00401245_inc", "case_bucket": "or", "source_criterion": "Generally healthy, postmenopausal woman who seeks treatment for hot flushes. Meets 1 of the following: At least 12 months of spontaneous amenorrhea; At least 6 months of spontaneous amenorrhea with serum follicle-stimulating hormone (FSH) levels > 40 mIU/mL; At least 6 weeks postsurgical bilateral oophorectomy (with or without hysterectomy). Hysterectomized without bilateral oophorectomy and with serum FSH levels >40 mIU/mL.", "candidate_expression": "((> 40 mIU/mL) AND (>40 mIU/mL) AND (At least 12 months) AND (At least 6 months) AND (At least 6 weeks postsurgical) AND (Hysterectomized) AND (Meets 1 of the following) AND (bilateral oophorectomy) AND (bilateral oophorectomy with hysterectomy) AND (bilateral oophorectomy without hysterectomy) AND (healthy) AND (hot flushes) AND (postmenopausal) AND (serum FSH levels) AND (serum follicle-stimulating hormone (FSH) levels) AND (spontaneous amenorrhea) AND (without) AND (woman))"}
{"candidate_id": "LLM04898", "doc_id": "NCT02742233_exc", "case_bucket": "or", "source_criterion": "Uncontrolled diabetes Ulcer infection Non-diabetic ulcers Orthopedic or neuromuscular pathologic conditions", "candidate_expression": "((Ulcer infection) AND (diabetes Uncontrolled) AND (ulcers Non-diabetic) AND ((Orthopedic pathologic conditions) OR (neuromuscular pathologic conditions)))"}
{"candidate_id": "LLM04899", "doc_id": "NCT02609425_exc", "case_bucket": "or", "source_criterion": "Any patient with esophageal cancer who is not deemed a surgical candidate or who is not deemed a candidate for the Ivor Lewis technique of esophagectomy (with intrathoracic anastomosis). Any patient less than 18 years of age", "candidate_expression": "((Ivor Lewis technique) AND (age) AND (esophageal cancer) AND (esophagectomy) AND (intrathoracic anastomosis) AND (less than 18 years) AND (not) AND (surgical) AND (with intrathoracic anastomosis) AND ((candidate)))"}
{"candidate_id": "LLM04900", "doc_id": "NCT02601157_exc", "case_bucket": "or", "source_criterion": "1. High risk profiles for ischemic adverse events such as A. ST-segment elevation myocardial infarction (STEMI) B. Patients with cardiogenic shock or concomitant severe decompensated heart failure C. Myocardial infarction or stent thrombosis in spite of the maintenance of antiplatelet therapy D. Restenosis in stented segments or previous sites of balloon angioplasty 2. Patients who cannot follow allocated DAPT schedule due to the planned surgery or elective procedure within 3 months after the stenting 3. Recent history of major surgery or evident events of gastrointestinal bleeding within 1 month from the procedure 4. Patients on anticoagulation therapy with warfarin or other anticoagulants 5. Life expectancy less than 1 year (such as malignancies or other chronic systemic diseases) 6. Pregnant women 7. Past history of allergy or other contraindications for the following medications/materials: aspirin, clopidogrel, heparin, cobalt chromium, sirolimus", "candidate_expression": "((High risk profiles) AND (Life expectancy) AND (Myocardial infarction) AND (Pregnant) AND (Restenosis) AND (ST-segment elevation myocardial infarction (STEMI)) AND (allergy) AND (anticoagulants) AND (anticoagulation therapy) AND (antiplatelet therapy) AND (aspirin) AND (cannot follow allocated DAPT schedule) AND (cardiogenic shock) AND (chronic systemic diseases) AND (clopidogrel) AND (cobalt chromium) AND (contraindications) AND (decompensated) AND (elective) AND (events of gastrointestinal bleeding) AND (heart failure) AND (heparin) AND (ischemic adverse events) AND (less than 1 year) AND (major surgery) AND (malignancies) AND (other) AND (planned) AND (procedure) AND (severe) AND (sirolimus) AND (stent thrombosis) AND (surgery) AND (warfarin) AND (within 1 month from the procedure) AND (within 3 months after the stenting) AND (women))"}
```
