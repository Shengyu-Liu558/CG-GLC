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
{"candidate_id": "LLM06676", "doc_id": "NCT02966236_exc", "case_bucket": "or", "source_criterion": "Coronary artery disease - stent Severe chronic renal failure Congenital or acquired thrombophilia/thrombosis event Known or suspected allergy", "candidate_expression": "((Congenital) AND (Coronary artery disease) AND (Known) AND (Severe) AND (acquired) AND (allergy) AND (chronic) AND (renal failure) AND (stent) AND (suspected) AND (thrombophilia) AND (thrombosis event))"}
{"candidate_id": "LLM06677", "doc_id": "NCT03297944_exc", "case_bucket": "or", "source_criterion": "using daily medication for chronic condition acute narrow angle glaucoma previous adverse experience with study drugs experiences motion sickness in response to driving simulator BMI > 30 women who are pregnant, lactating, or planning on becoming pregnant regular use of tobacco products current substance use disorder clinically significant ECG current ongoing psychiatric disorder", "candidate_expression": "((BMI > 30) AND (ECG clinically significant) AND (adverse experience previous) AND (chronic condition) AND (medication daily) AND (motion sickness) AND (narrow angle glaucoma acute) AND (psychiatric disorder current ongoing) AND (study drugs) AND (substance use disorder current) AND (use of tobacco products regular) AND (women) AND ((lactating) OR (pregnant) OR (pregnant planning on becoming)))"}
{"candidate_id": "LLM06678", "doc_id": "NCT03475589_inc", "case_bucket": "or", "source_criterion": "Age of 18 and over, male or female; Patients with histologically confirmed advanced (stage IV) gastric cancer, NSCLC, breast cancer or ovarian cancer, who choose monotherapy of oral vascular targeting drug (apatinib) due to intolerability or inappropriateness of other therapies; Presence of measurable lesions (=10mm on spiral CT scan) subject to RECIST 1.1; Blood pressured controlled at 150/100 mHg following drug administration; An ECOG PS score of between 0 and 1; A life expectancy of at least 3 months; Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.", "candidate_expression": "((Age 18 and over) AND (Blood pressured controlled 150/100 mHg) AND (ECOG PS between 0 and 1) AND (Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.) AND (apatinib) AND (histologically stage IV) AND (life expectancy at least 3 months) AND (measurable lesions RECIST 1.1) AND (monotherapy) AND (oral vascular targeting drug) AND (spiral CT scan =10mm) AND ((NSCLC) OR (breast cancer) OR (gastric cancer) OR (ovarian cancer)) AND ((female) OR (male)))"}
{"candidate_id": "LLM06679", "doc_id": "NCT00198913_exc", "case_bucket": "or", "source_criterion": "type 1 diabetic or non-diabetic", "candidate_expression": "((non-diabetic) AND (type 1 diabetic))"}
{"candidate_id": "LLM06680", "doc_id": "NCT00356148_inc", "case_bucket": "scope", "source_criterion": "Women at any age with early stage breast cancer (stage I-II) and American Society of Anesthesiologists (ASA) score of I-II.", "candidate_expression": "((American Society of Anesthesiologists (ASA) score I-II) AND (Women) AND (any age) AND (breast cancer) AND (stage I-II) AND (stage early))"}
{"candidate_id": "LLM06681", "doc_id": "NCT03259243_inc", "case_bucket": "other", "source_criterion": "Patient who undergoing gynecologic laparoscopic surgery Patient who agrees to participate in this study Patient able to speak and understand Thai Patient able to complete the questionnaire", "candidate_expression": "((Patient able to speak and understand Thai) AND (Patient who agrees to participate in this study) AND (able to complete the questionnaire) AND (able to speak and understand Thai) AND (agrees to participate in this study) AND (gynecologic laparoscopic surgery))"}
{"candidate_id": "LLM06682", "doc_id": "NCT02944929_exc", "case_bucket": "other", "source_criterion": "Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate. Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator. Un-controlled progressive pathology. Osteoarticular lesion which contraindicates part of the rehabilitation involved in the study. Patients with other interventions planned prior to the end of the study period (orthosis, surgery etc.). Surgery to the treated limb less than 6 months previously. Pregnant woman.", "candidate_expression": "((Osteoarticular lesion) AND (Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate) AND (Pregnant woman) AND (Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator) AND (Surgery) AND (less than 6 months) AND (treated limb))"}
{"candidate_id": "LLM06683", "doc_id": "NCT01846507_exc", "case_bucket": "or", "source_criterion": "1. Active thromboembolic disease, history of thromboembolic disease (including retinal vein or artery occlusion), known inherited thrombophilia, or family history of thrombosis in a first degree relative 2. Subject has a severe medical or psychiatric illness that, in the opinion of the Investigator, would affect subject safety or compliance 3. Clinical evidence of severe bleeding disorder. Patients with mild bleeding disorders such as type 1 von Willebrand disease, mild platelet function defects such as platelet storage pool or release defects, and patients with bleeding due to Ehlers Danlos syndrome WILL be eligible to participate in the study. 4. Pregnancy within the past 6 months and/or breast-feeding 5. Use of hormonal contraception (estrogen and progestin) within 3 months of study entry, or anticipated need to initiate estrogen-containing hormonal contraception during the study period 6. Use of systemic steroids within 1 month of study entry 7. History of subarachnoid hemorrhage 8. History of Hepatitis B, C, or HIV 9. Baseline creatinine >20% above the upper limit of normal for age 10. Severe anemia (hemoglobin <8 g/dL) 11. Systolic blood pressure <85 or diastolic blood pressure <55 12. Heart rate <50 at time of screening 13. Use of intranasal DDAVP during menses will be permitted, but only if the patient has a history of using DDAVP consistently for ≥3 menstrual cycles prior to study enrollment, so that change in menstrual blood loss due to addition of Lysteda can be assessed. Use of one-time DDAVP during a DDAVP/Stimate challenge is also permitted during the study period, as is use of DDAVP in the event of severe epistaxis, trauma, or surgical procedures during the study period.", "candidate_expression": "((Ehlers Danlos syndrome) AND (HIV) AND (Heart rate <50 at time of screening) AND (Hepatitis B) AND (Hepatitis C) AND (Pregnancy within the past 6 months) AND (Systolic blood pressure <85) AND (age) AND (anemia Severe) AND (artery occlusion) AND (bleeding) AND (bleeding disorder severe) AND (bleeding disorders mild) AND (breast-feeding within the past 6 months) AND (creatinine Baseline >20% above the upper limit of normal for age) AND (diastolic blood pressure <55) AND (estrogen) AND (estrogen-containing hormonal contraception anticipated need estrogen-containing during the study period) AND (hemoglobin <8 g/dL) AND (hormonal contraception) AND (inherited thrombophilia) AND (intranasal DDAVP during menses) AND (medical illness) AND (mild platelet function defects) AND (platelet release defects) AND (platelet storage pool defects) AND (progestin within 3 months of study entry) AND (psychiatric illness) AND (retinal vein) AND (subarachnoid hemorrhage History) AND (systemic steroids within 1 month of study entry) AND (thromboembolic disease Active) AND (thromboembolic disease history) AND (thrombosis family history) AND (type 1 von Willebrand disease))"}
{"candidate_id": "LLM06684", "doc_id": "NCT02689817_inc", "case_bucket": "other", "source_criterion": "Patients undergoing an operation that is scheduled to last more than 2 hours", "candidate_expression": "(operation scheduled to last more than 2 hours last more than 2 hours)"}
{"candidate_id": "LLM06685", "doc_id": "NCT02195024_inc", "case_bucket": "or", "source_criterion": "Approved clinical indication for pectoral pacemaker exchange (e.g. elective replacement indication (ERI), end of service (EOS)) a single or dual chamber MRI conditional pacemaker (BSCI) or Any comparable successor IPG (MRI conditional system, BSCI) compatible with Implanted Fineline-II-leads (BSCI), MRI conditional The ascertained lead impedance is between 200 and 1500 Ohm. All pacing capture thresholds (PCT) do not exceed 2.0 V @0.4 or 0.5 ms in pacemaker dependent patients Male or female 18 years or older Understand the nature of the procedure Give written informed consent Able to complete all testing required by the clinical protocol Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms Patient body height greater or equal to 140 cm Pectoral implanted device Subjects who are able and willing to undergo elective cardiac magnetic resonance (MR) scanning without sedation (MRI-group) Subjects who are geographically stable and available for follow-up at the study center for the length of the study", "candidate_expression": "((18 years or older) AND (Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms) AND (Able to complete all testing required by the clinical protocol) AND (BSCI) AND (Give written informed consent) AND (Implanted Fineline-II-leads) AND (MR) AND (MRI conditional) AND (MRI conditional system) AND (Male) AND (PCT) AND (Pectoral implanted device) AND (ascertained lead impedance) AND (at the study center) AND (available for follow-up) AND (between 200 and 1500 Ohm) AND (body height) AND (cardiac magnetic resonance scanning) AND (clinical indication) AND (comparable) AND (do not exceed 2.0 V @0.4 or 0.5 ms) AND (dual chamber) AND (elective) AND (elective replacement indication (ERI)) AND (end of service (EOS)) AND (female) AND (for the length of the study) AND (geographically stable) AND (greater or equal to 140 cm) AND (pacemaker) AND (pacemaker dependent) AND (pacing capture thresholds) AND (pectoral pacemaker exchange) AND (single chamber) AND (successor IPG) AND (willing to undergo) AND (without sedation) AND (years or older))"}
{"candidate_id": "LLM06686", "doc_id": "NCT02698969_exc", "case_bucket": "or", "source_criterion": "Clinical diagnosis of hepatic or renal disease Clinical diagnosis of chronic or acute alcoholism History of allergy or hypersensitivity to Sugammadex and/or atropine or Neostigmine Current medications with CNS effects History of neurologic disease Diaphragmatic palsy Pregnancy or nursing History of malignant arrhythmias", "candidate_expression": "((CNS effects) AND (Diaphragmatic palsy) AND (Neostigmine) AND (Pregnancy) AND (Sugammadex) AND (alcoholism Clinical diagnosis acute) AND (allergy) AND (atropine) AND (hepatic disease chronic) AND (hypersensitivity) AND (malignant arrhythmias History) AND (medications) AND (neurologic disease History) AND (nursing) AND (renal disease))"}
{"candidate_id": "LLM06687", "doc_id": "NCT03297125_inc", "case_bucket": "other", "source_criterion": "Newly diagnosed glioblastoma (GBM), WHO grade IV.", "candidate_expression": "((GBM) AND (WHO grade IV) AND (glioblastoma Newly diagnosed))"}
{"candidate_id": "LLM06688", "doc_id": "NCT03044093_inc", "case_bucket": "other", "source_criterion": "healthy no allergy known to these drugs second trimester abortion", "candidate_expression": "((abortion second trimester) AND (healthy) AND (these drugs) AND NOT (allergy))"}
{"candidate_id": "LLM06689", "doc_id": "NCT02872935_inc", "case_bucket": "other", "source_criterion": "Pregnant American Society of Anesthesiologists risk classification I and II Age > 18 years Non-laboring Patients with elective cesarean sections", "candidate_expression": "((Age > 18 years Non-laboring) AND (American Society of Anesthesiologists risk classification I and II) AND (Pregnant) AND (cesarean sections elective))"}
{"candidate_id": "LLM06690", "doc_id": "NCT03177811_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((COPD) AND (FEV1 40-80% predicted) AND (GOLD) AND (SpO2 =92% at 750 m) AND (Written informed consent) AND (age 18-75 yrs) AND ((Male) OR (female)))"}
{"candidate_id": "LLM06691", "doc_id": "NCT03333655_inc", "case_bucket": "or", "source_criterion": "Response assessment of complete response (CR), partial response (PR), long stable disease (SD) for >3 months with a cancer immunotherapy treatment for metastatic cancer or hematologic malignancies either through a marketed CPI or through participation in a Roche/Genentech CPI clinical trial. Availability of tumor biopsy material extracted and preserved by the investigating site.", "candidate_expression": "((Response assessment) AND (immunotherapy treatment cancer) AND ((hematologic malignancies) OR (metastatic cancer)) AND ((marketed CPI) OR (participation in a Roche/Genentech CPI clinical trial)) AND ((complete response (CR)) OR (long stable disease (SD)) OR (partial response (PR))))"}
{"candidate_id": "LLM06692", "doc_id": "NCT00426751_exc", "case_bucket": "or", "source_criterion": "Subjects not able to give informed consent Left Bundle Branch Block Thrombolytic therapy within 24 hours before randomization Oral anticoagulation with International Normalized Ratio (INR) > 2 Known platelets < 100.000/µl or known hemorrhagic diathesis Stroke or Transient Ischemic Attack (TIA) within the past 6 months or any permanent residual neurological defect Evidence of an active gastrointestinal or urogenital bleeding Major surgery within 6 weeks History of allergic reaction to abciximab or eptifibatide or any component used in the study (including contrast media) Known severe renal (creatinine clearance <30ml/min) or hepatic insufficiency as well as Alanine transaminase (ALT)/aspartate transaminase (AST) elevations = 3xUpper limit normal (ULN); isolated AST-elevation is not considered an exclusion criteria from study participation Severe concomitant disease with life expectation < 1 year Subject has participated in any study using an investigational drug or device within 30 days or within 5 half-lives of the investigational drug (whichever is longer) of entry into this study. Subjects who will be inaccessible due to geographic or social factors during treatment or follow-up In France, a subject is neither affiliated with nor a beneficiary of a social security category.", "candidate_expression": "((Alanine transaminase (ALT) elevations) AND (History) AND (International Normalized Ratio (INR) > 2) AND (Left Bundle Branch Block) AND (Major surgery within 6 weeks) AND (Oral anticoagulation) AND (Severe disease concomitant) AND (Stroke) AND (Thrombolytic therapy within 24 hours before randomization) AND (Transient Ischemic Attack (TIA)) AND (abciximab) AND (allergic reaction) AND (aspartate transaminase (AST) elevations 3xUpper limit normal (ULN)) AND (component used in the study) AND (contrast media) AND (creatinine clearance <30ml/min) AND (device of the investigational drug within 30 days within 5 half-lives of the investigational drug) AND (eptifibatide) AND (gastrointestinal bleeding) AND (hemorrhagic diathesis) AND (hepatic insufficiency severe) AND (inaccessible during treatment or follow-up treatment follow-up) AND (investigational drug) AND (life expectation < 1 year) AND (participated in any study) AND (platelets < 100.000/µl) AND (renal insufficiency severe) AND (residual neurological defect) AND (urogenital bleeding) AND NOT (give informed consent able to))"}
{"candidate_id": "LLM06693", "doc_id": "NCT02884115_exc", "case_bucket": "other", "source_criterion": "Human immunodeficiency virus (HIV)-infected Baseline serology showed a nonreactive RPR test follow-up is inadequate Allergic to penicillin Pregnant woman", "candidate_expression": "((Allergic) AND (Baseline) AND (Human immunodeficiency virus (HIV)-infected) AND (Pregnant) AND (RPR test) AND (follow-up is inadequate) AND (nonreactive) AND (penicillin) AND (serology) AND (woman))"}
{"candidate_id": "LLM06694", "doc_id": "NCT02747940_exc", "case_bucket": "or", "source_criterion": "history of major systemic illness, including uncontrolled hypertension, diabetes, chronic renal insufficiency, autoimmune diseases or malignancies history of neurological disorders which might affect sensation such as previous stroke or peripheral neuropathy history of substance abuse (except painkillers) heavy smokers (with a daily consumption >20 cigarettes) pregnancy or lactation any contraindication for magnetic resonance imaging (MRI) and any obvious infection or inflammation over a period of at least 1 month before the study.", "candidate_expression": "((MRI) AND (affect sensation) AND (at least 1 month before the study) AND (autoimmune diseases) AND (chronic renal insufficiency,) AND (cigarettes) AND (contraindication) AND (daily consumption >20) AND (diabetes) AND (except) AND (heavy) AND (hypertension) AND (infection) AND (inflammation) AND (magnetic resonance imaging) AND (major) AND (malignancies) AND (neurological disorders) AND (obvious) AND (painkillers) AND (peripheral neuropathy) AND (pregnancy or lactation) AND (smokers) AND (stroke) AND (study) AND (substance abuse) AND (systemic illness) AND (uncontrolled))"}
{"candidate_id": "LLM06695", "doc_id": "NCT00718952_inc", "case_bucket": "or", "source_criterion": "Subjects aged 12-65. Confirmed idiopathic pulmonary hypertension, connective tissue disease associated pulmonary hypertension, congenital heart disease(with Eisenmenger syndrome) associated pulmonary hypertension. Baseline 6-minutes walking distance 150m-550m. WHO pulmonary hypertension function II-III with non-responder to calcium channel blockers. Documented written informed consent.", "candidate_expression": "((6-minutes walking distance Baseline 150m-550m) AND (Eisenmenger syndrome) AND (WHO pulmonary hypertension function II-III) AND (aged 12-65) AND (calcium channel blockers) AND (idiopathic pulmonary hypertension) AND (non-responder to calcium channel blockers) AND (pulmonary hypertension) AND (pulmonary hypertension connective tissue disease associated congenital heart disease) AND (written informed consent))"}
{"candidate_id": "LLM06696", "doc_id": "NCT02408120_inc", "case_bucket": "or", "source_criterion": "Subjects admitted to the hospital with acute or chronic medical illnesses or for elective and emergency surgical illness or trauma Known history of Type 2 diabetes mellitus for >3 months Treated with either diet alone, any combination of oral antidiabetic agents, non-insulin injectables or insulin therapy Blood glucose levels between >140 mg and <400 mg/dL without laboratory evidence of diabetic ketoacidosis", "candidate_expression": "((>140 mg and <400 mg/dL) AND (>3 months) AND (Blood glucose levels) AND (Type 2 diabetes mellitus) AND (admitted to the hospital) AND (diabetic ketoacidosis) AND (laboratory evidence) AND (medical illnesses) AND (without) AND ((diet) OR (insulin) OR (non-insulin injectables therapy) OR (oral antidiabetic agents)) AND ((acute) OR (chronic)) AND ((surgical illness) OR (trauma)) AND ((elective) OR (emergency)))"}
{"candidate_id": "LLM06697", "doc_id": "NCT02584140_exc", "case_bucket": "or", "source_criterion": "Pregnancy at enrollment. Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder). Use of prohibited medications, in particular, agents known to be nephrotoxic or drugs slow in renal excretion. Previous participation in an HIV vaccine trial. Participants that were documented to have received only placebo are not excluded. Signs or symptoms suspicious for Primary HIV Infection (PHI).", "candidate_expression": "((Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder)) AND (PHI) AND (Participants Previous HIV vaccine trial not) AND (Pregnancy at enrollment) AND (Primary HIV Infection) AND (Signs) AND (agents nephrotoxic) AND (drugs slow in renal excretion) AND (participation Previous HIV vaccine trial) AND (placebo) AND (symptoms))"}
{"candidate_id": "LLM06698", "doc_id": "NCT03639545_inc", "case_bucket": "other", "source_criterion": "diabetes mellitus type 1", "candidate_expression": "(diabetes mellitus type 1)"}
{"candidate_id": "LLM06699", "doc_id": "NCT02862912_inc", "case_bucket": "or", "source_criterion": "ASA I and II women 18-45 yrs old Singleton pregnancy Cervical cerclage 1st or 2nd trimester of pregnancy undergoing with spinal anesthesia Height 150 - 180 cm BMI = 40 kg/m2.", "candidate_expression": "((ASA I and II) AND (BMI = 40 kg/m2) AND (Cervical cerclage) AND (Height 150 - 180 cm) AND (Singleton pregnancy) AND (old 18-45 yrs) AND (pregnancy) AND (spinal anesthesia) AND (women) AND ((1st trimester) OR (2nd trimester)))"}
{"candidate_id": "LLM06700", "doc_id": "NCT02849483_exc", "case_bucket": "or", "source_criterion": "Allergic to study drugs Antiemetics or steroids use within 24 hrs prior to surgery Dependence upon opioids Insulin dependent Diabetes Mellitus Cardiovascular or pulmonary disease Renal or hepatic insufficiency BMI>=35kg/m2 History of motion sickness or PONV Cigarette smoker Conversion to open laparotomy from laparoscopic surgery Pregnants", "candidate_expression": "((>=35kg/m2) AND (Allergic) AND (BMI) AND (Cigarette smoker) AND (Conversion) AND (Dependence upon opioids) AND (Diabetes Mellitus) AND (History) AND (Insulin) AND (Insulin dependent) AND (Pregnants) AND (laparoscopic surgery) AND (open laparotomy) AND (study drugs) AND (surgery) AND (within 24 hrs prior to surgery) AND ((Cardiovascular disease) OR (pulmonary disease)) AND ((Renal insufficiency) OR (hepatic insufficiency)) AND ((PONV) OR (motion sickness)) AND ((Antiemetics) OR (steroids use)))"}
```
