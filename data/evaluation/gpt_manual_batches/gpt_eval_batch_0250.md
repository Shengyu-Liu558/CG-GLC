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
{"candidate_id": "LLM06226", "doc_id": "NCT03420638_exc", "case_bucket": "or", "source_criterion": "Presence of severe systemic disease Presence of coagulation disorders Current or previous history of analgesic dependence Allergy to any of the drugs used in the study Women pregnant or lactating, or women planning to become pregnant Presence of hearing loss Presence of cardiovascular comorbidities Presence of hepatic comorbidities Presence of kidney comorbidities Presence of cognitive disabilities", "candidate_expression": "((Allergy) AND (Women) AND (analgesic) AND (analgesic dependence history) AND (cardiovascular comorbidities) AND (coagulation disorders Current previous) AND (cognitive disabilities) AND (drugs used in the study) AND (hearing loss) AND (hepatic comorbidities) AND (kidney comorbidities) AND (lactating) AND (pregnant) AND (pregnant planning to become) AND (systemic disease severe) AND (women))"}
{"candidate_id": "LLM06227", "doc_id": "NCT02112734_inc", "case_bucket": "other", "source_criterion": "Healthy, term, breastfeeding infants who will be predominately breastfed for at least 6-months. This will be determined by answering yes/no to question 'do you intend to breastfeed until your infant is at least 6 months of age.'", "candidate_expression": "((Healthy) AND (breastfeeding) AND (infants) AND (predominately breastfed for at least 6-months) AND (term))"}
{"candidate_id": "LLM06228", "doc_id": "NCT01696617_exc", "case_bucket": "or", "source_criterion": "Past history of hypersensitivity to aripiprazole Primary diagnosis of MDD with psychotic feature, bipolar disorder, schizophrenia, schizoaffective disorder, other psychotic disorder or anxiety disorder, a history of alcohol/ drug abuse within the past 12 months, or a diagnosis of dementia Clinically significant current Axis II (DSM-IV-TR) diagnosis A significant risk of suicide corroborated by a score of =5 on item 10(suicidal thoughts) on the MADRS scale or by clinical judgment of the investigator Pregnancy or in breast-feeding Presence of a serious medical illness including cardiac, hepatic, renal, respiratory, endocrinologic, neurologic, or hematologic disease or physical disorder judged to significantly affect central nervous system function Patients taking antipsychotics, mood stabilizer or any psychotropic medications besides antidepressants, except benzodiazepines or beta blockers or hypnotics Patients with past treatment failures of aripiprazole", "candidate_expression": "((MADRS scale score of =5 on item 10) AND (Pregnancy or in breast-feeding) AND (aripiprazole) AND (aripiprazole treatment failures) AND (cardiac) AND (diagnosis Axis II DSM-IV-TR) AND (endocrinologic) AND (hematologic disease) AND (hepatic) AND (hypersensitivity) AND (medical illness serious) AND (neurologic) AND (physical disorder) AND (psychotropic medications) AND (renal) AND (respiratory) AND (risk of suicide significant) AND NOT (antidepressants) AND ((alcohol abuse) OR (drug abuse)) AND ((MDD) OR (anxiety disorder,) OR (bipolar disorder) OR (dementia) OR (psychotic disorder other) OR (psychotic feature) OR (schizoaffective disorder) OR (schizophrenia)) AND ((antipsychotics) OR (mood stabilizer)) AND ((benzodiazepines) OR (beta blockers) OR (hypnotics)))"}
{"candidate_id": "LLM06229", "doc_id": "NCT03407625_exc", "case_bucket": "other", "source_criterion": "latex allergy non-reassuring fetal status HIV active herpes outbreak Prior uterine scar Contraindication to prostaglandins according to current Parkland protocol Contraindication to vaginal delivery", "candidate_expression": "((Contraindication) AND (HIV) AND (Parkland protocol) AND (allergy) AND (fetal status non-reassuring) AND (herpes active) AND (latex) AND (prostaglandins) AND (uterine scar) AND (vaginal delivery))"}
{"candidate_id": "LLM06230", "doc_id": "NCT02106624_exc", "case_bucket": "other", "source_criterion": "irreversible status of primary disease any history of malnutrition before enrollment history of steroid cortisol administration severe liver dysfunction (Child-Pugh Score C) pregnancy refuse to enrollment re-admission to ICU and has been enrolled during former admission to ICU", "candidate_expression": "((Child-Pugh Score C) AND (ICU) AND (liver dysfunction severe) AND (malnutrition before enrollment) AND (pregnancy) AND (primary disease irreversible status) AND (re-admission) AND (refuse to enrollment) AND (steroid cortisol))"}
{"candidate_id": "LLM06231", "doc_id": "NCT02555163_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed at the out-patient cystoscopy with papillary bladder tumour will be legible for inclusion", "candidate_expression": "((cystoscopy) AND (out-patient) AND (papillary bladder tumour))"}
{"candidate_id": "LLM06232", "doc_id": "NCT02330705_inc", "case_bucket": "or", "source_criterion": "Mild male factor infertility or unexplained infertility.", "candidate_expression": "((Mild) AND (male factor infertility) AND (unexplained infertility))"}
{"candidate_id": "LLM06233", "doc_id": "NCT02979561_inc", "case_bucket": "or", "source_criterion": "Men and women aged > 18 years Angiographically confirmed acute massive pulmonary embolism with involvement of Central pulmonary arteries. endovascular mechanical thrombus fragmentation + thrombolytic therapy (using recombinant tissue activator of plasminogen), performed for treatment of the above-mentioned pulmonary embolism in less than 48 hours before randomization. The patient should be randomized no earlier than 24 hours after procedures endovascular mechanical thrombus fragmentation + thrombolytic therapy Written informed consent signed by patient.", "candidate_expression": "((> 18 years) AND (Angiographically) AND (Angiographically confirmed) AND (Men) AND (acute) AND (aged) AND (endovascular mechanical thrombus fragmentation) AND (in less than 48 hours before randomization) AND (involvement of Central pulmonary arteries) AND (massive) AND (pulmonary embolism) AND (recombinant tissue activator of plasminogen) AND (ritten informed consent signed by patient) AND (thrombolytic therapy) AND (treatment) AND (women))"}
{"candidate_id": "LLM06234", "doc_id": "NCT02394158_exc", "case_bucket": "or", "source_criterion": "Established pre-existing diabetes (including unrecognised diabetes defined as a fasting plasma glucose = 7.0mmol/L and/ or HbA1c = 48mmol/mol); Contraindications to metformin therapy (creatinine = 130µmol/L/ alanine transaminase = 2.0 x upper limit normal/ previous intolerance to metformin) Planned continued antenatal care/ delivery at centre not included in trial Planned fast for cultural/ religious reasons e.g. Ramadan", "candidate_expression": "((= 130µmol/L/) AND (= 2.0 x upper limit normal) AND (= 48mmol/mol)) AND (= 7.0mmol/L) AND (Contraindications) AND (Planned continued antenatal care/ delivery at centre not included in trial) AND (diabetes) AND (metformin) AND ((alanine transaminase) OR (creatinine) OR (intolerance)) AND ((HbA1c) OR (fasting plasma glucose)))"}
{"candidate_id": "LLM06235", "doc_id": "NCT02283905_inc", "case_bucket": "scope", "source_criterion": "All adult patients 18 years of age or older admitted to the intensive care units of St. Boniface General Hospital with a diagnosis of acute pulmonary blastomycosis requiring mechanical ventilation.", "candidate_expression": "((St. Boniface General Hospital) AND (acute pulmonary blastomycosis) AND (admitted) AND (adult) AND (age 18 years or older) AND (intensive care units) AND (mechanical ventilation))"}
{"candidate_id": "LLM06236", "doc_id": "NCT02974686_exc", "case_bucket": "or", "source_criterion": "Dual organ or kidney after another solid organ transplant Presence of a preexisting significant GI condition that does not have a presumed causal relationship with MPA Evidence of any GI disorder induced by an infection, underlying medical condition, or concomitant medication other than MPA eGFR<40 ml/min at time of possible conversion Proteinuria >1 gram/day at time of possible conversion Hemoglobin <10 g/dL WBC <3 K/cumm Platelets <100 K/cumm Wound healing issues at time of possible conversion (eg, wound dehiscence, wound infection, incisional hernia, lymphocele, seroma) Elevated total cholesterol (>350 mg/dL) and/or triglycerides (>500 ng/dL) at time of possible conversion Hypersensitivity to everolimus, sirolimus, or other rapamycin deriviatives", "candidate_expression": "((Dual kidney) AND (Dual organ) AND (GI condition preexisting significant) AND (GI disorder induced by an infection) AND (Hemoglobin <10 g/dL) AND (Hypersensitivity) AND (Platelets <100 K/cumm) AND (Proteinuria >1 gram/day at time of possible conversion) AND (WBC <3 K/cumm) AND (Wound healing issues at time of possible conversion) AND (eGFR <40 ml/min at time of possible conversion) AND (everolimus) AND (incisional hernia) AND (infection) AND (lymphocele) AND (medication) AND (rapamycin) AND (seroma) AND (sirolimus) AND (solid organ transplant) AND (total cholesterol Elevated >350 mg/dL) AND (triglycerides >500 ng/dL at time of possible conversion) AND (underlying medical condition) AND (wound dehiscence) AND (wound infection) AND NOT (MPA))"}
{"candidate_id": "LLM06237", "doc_id": "NCT03125057_inc", "case_bucket": "other", "source_criterion": "Children with clinical diagnosis of PWS; Age range: 7 to 14 years-old; Voluntarily participated and Written informed consent signed", "candidate_expression": "((7 to 14 years-old) AND (Age) AND (Children) AND (PWS) AND (Voluntarily participated) AND (Written informed consent signed) AND (clinical diagnosis))"}
{"candidate_id": "LLM06238", "doc_id": "NCT03541980_inc", "case_bucket": "other", "source_criterion": "Any patient age 4-16 years with sickle cell disease who presents the Pediatric ER with acute sickle cell pain crisis with a pain of 6/10 or higher", "candidate_expression": "((Pediatric ER) AND (acute sickle cell pain crisis) AND (age 4-16 years) AND (pain 6/10 or higher) AND (sickle cell disease))"}
{"candidate_id": "LLM06239", "doc_id": "NCT02150590_inc", "case_bucket": "other", "source_criterion": "chronic obstructive pulmonary disease (COPD), GOLD grade 2-3 residents at low altitude (<800 m)", "candidate_expression": "((COPD) AND (GOLD grade 2-3) AND (chronic obstructive pulmonary disease))"}
{"candidate_id": "LLM06240", "doc_id": "NCT02118467_exc", "case_bucket": "other", "source_criterion": "Cardiopulmonary arrest Pregnancy Severe right heart failure", "candidate_expression": "((Cardiopulmonary arrest) AND (Pregnancy) AND (Severe) AND (right heart failure))"}
{"candidate_id": "LLM06241", "doc_id": "NCT03337503_inc", "case_bucket": "or", "source_criterion": "Written informed consent Adult patients (older than 18 years of age), male and female, with chronic non-cancer and cancer pain (at least 3 months in duration) Patients experiencing an average weekly pain intensity score greater than 4 on a 11 points NRS Subject agreed to follow the protocol Naïve cannabis patients with chronic non-cancer and cancer pain (not used cannabis in any presentation in the last 12 weeks) Patients receiving opioids and other concomitant pain medications should have a stable dose for the last 15 days. Normal cognitive status according to MiniCog Normal liver function (defined as aspartate aminotransferase 10-40 U/L and alanine aminotransferase 7-56 U/L) Normal renal function (defined as serum creatinine level <133 µmol/L and Estimated Glomerular Filtration Rate (eGFR) greater than or equal to 60) Negative result on ßhuman chorionic gonadotropin pregnancy test (if applicable) Ability to read and respond to questions in French or English. A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.", "candidate_expression": "((10-40 U/L) AND (7-56 U/L) AND (<133 µmol/L) AND (A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.) AND (Adult) AND (Estimated Glomerular Filtration Rate (eGFR)) AND (MiniCog) AND (Naïve cannabis) AND (Negative) AND (Normal cognitive status) AND (Normal liver function) AND (Normal renal function) AND (Subject agreed to follow the protocol) AND (Written informed consent) AND (age) AND (alanine aminotransferase) AND (aspartate aminotransferase) AND (at least 3 months in duration) AND (average weekly pain intensity score on a 11 points NRS) AND (cannabis) AND (chronic) AND (for the last 15 days) AND (greater than 4) AND (greater than or equal to 60) AND (in the last 12 weeks) AND (not) AND (older than 18 years) AND (other) AND (pain) AND (serum creatinine level) AND (stable dose) AND (ßhuman chorionic gonadotropin pregnancy test) AND ((cancer) OR (non-cancer)) AND ((opioids) OR (pain medications)) AND ((female) OR (male)))"}
{"candidate_id": "LLM06242", "doc_id": "NCT01581749_exc", "case_bucket": "or", "source_criterion": "implanted hardware or other material that would prohibit treatment planning or delivery chemotherapy for a malignancy within the previous 5 years history of an invasive malignancy (other than this prostate cancer,or basal or squamous skin cancers) within prior 5 years hormone ablation for 2 months prior to treatment or during treatment", "candidate_expression": "((basal skin cancers) AND (chemotherapy within the previous 5 years) AND (hormone ablation for 2 months prior to treatment during treatment) AND (invasive malignancy) AND (malignancy) AND (prostate cancer) AND (squamous skin cancers))"}
{"candidate_id": "LLM06243", "doc_id": "NCT02621541_exc", "case_bucket": "or", "source_criterion": "vulnerable study subjects such as described in Finnish law concerning clinical studies (disabled, children, pregnant or breast-feeding women, prisoners) will not be included.", "candidate_expression": "((vulnerable Finnish law concerning clinical studies) AND ((breast-feeding) OR (children) OR (disabled) OR (pregnant) OR (prisoners) OR (women)))"}
{"candidate_id": "LLM06244", "doc_id": "NCT02550028_inc", "case_bucket": "or", "source_criterion": "Male or female term baby with gestational >37 weeks and postnatal age < or= 28 days Birthweight >2500g Written informed consent of parent or guardian", "candidate_expression": "((Birthweight >2500g) AND (Male) AND (Written informed consent of parent or guardian) AND (baby) AND (female) AND (gestational >37 weeks) AND (postnatal age < or= 28 days) AND (term))"}
{"candidate_id": "LLM06245", "doc_id": "NCT01579604_exc", "case_bucket": "or", "source_criterion": "Unstable patient Joint contracture Spasticity Loss of function is expected to be improved by reliable tendon transfer, tenodesis or arthrodesis that is available Evidence of recovering finger/thumb extension at 4-6 months Greater than 12 months from spinal cord injury Subject not fluent in English or an appropriate translator not available", "candidate_expression": "((Joint contracture) AND (Loss of function) AND (Spasticity) AND (Subject not fluent in English or an appropriate translator not available) AND (patient Unstable) AND (recovering extension at 4-6 months) AND (spinal cord injury Greater than 12 months) AND ((finger) OR (thumb)) AND ((arthrodesis) OR (tendon transfer) OR (tenodesis)))"}
{"candidate_id": "LLM06246", "doc_id": "NCT01261832_exc", "case_bucket": "or", "source_criterion": "The patient has a known hypersensitivity or contraindication to any of the following medications: Heparin, Aspirin, Clopidogrel, Cilostazol Uncontrolled hypertension History of bleeding diathesis or known coagulopathy (including heparin-induced thrombocytopenia), or refuses blood transfusions. Baseline hemogram with Hb<10g/dL or PLT count<100,000/μL Patients already taking warfarin, cilostazol or any other type of anti-platelet agents except aspirin and clopidogrel Gastrointestinal or genitourinary bleeding within the prior 3 months, or major surgery within 2 months. Pregnancy", "candidate_expression": "((Pregnancy) AND (blood transfusions) AND (hemogram Baseline) AND (heparin-induced thrombocytopenia) AND (hypertension Uncontrolled) AND (major surgery within 2 months) AND ((bleeding diathesis History) OR (coagulopathy) OR (refuses blood transfusions)) AND ((Hb <10g/dL) OR (PLT count <100,000/μL)) AND ((contraindication) OR (hypersensitivity)) AND ((anti-platelet agents) OR (cilostazol) OR (warfarin)) AND ((aspirin) OR (clopidogrel)) AND ((Aspirin) OR (Cilostazol) OR (Clopidogrel) OR (Heparin)) AND ((Gastrointestinal bleeding) OR (genitourinary bleeding)))"}
{"candidate_id": "LLM06247", "doc_id": "NCT02885909_exc", "case_bucket": "other", "source_criterion": "incooperative for glucose monitor refusal of insulin pregnancy", "candidate_expression": "((glucose monitor) AND (incooperative) AND (insulin) AND (pregnancy) AND (refusal))"}
{"candidate_id": "LLM06248", "doc_id": "NCT02579200_exc", "case_bucket": "or", "source_criterion": "Inability to perform exercise tests Diagnosed psychiatric or cognitive disorders Progressive neurological or neuromuscular disorders having a major impact on exercise capacity", "candidate_expression": "((Inability to perform) AND (cognitive disorders) AND (disorders Progressive neurological) AND (exercise tests) AND (impact on exercise capacity) AND (neuromuscular disorders Progressive) AND (psychiatric disorders))"}
{"candidate_id": "LLM06249", "doc_id": "NCT02548013_inc", "case_bucket": "other", "source_criterion": "1. PPROM with gestational age between 27 to 34 weeks 2. Cephalic presentation 3. Clear amniotic fluid 4. Oral temperature > 38 C 5. Near distance from the hospital (the patient can reach hospital within one hour ) 6. Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home . 7. Maternal and fetal condition remain stable after hospitalization for 72 hours", "candidate_expression": "((> 38 C) AND (Cephalic presentation) AND (Clear amniotic fluid) AND (Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home .) AND (Maternal condition) AND (Near distance from the hospital (the patient can reach hospital within one hour )) AND (Oral temperature) AND (PPROM) AND (after hospitalization for 72 hours) AND (between 27 to 34 weeks) AND (fetal condition) AND (gestational age) AND (hospitalization) AND (stable))"}
{"candidate_id": "LLM06250", "doc_id": "NCT01942915_exc", "case_bucket": "other", "source_criterion": "1. Patients with C class by child-pugh score 2. Patients in the acute phase of severe hepatitis 3. Patients have been diagnosed with cancer of the liver 4. Patients with severe cardiopulmonary cerebral disease, and in the failure state 5. Patients in Highly allergic constitution 6. Patients with moderately severe mental disease", "candidate_expression": "((C class) AND (Highly allergic constitution) AND (acute phase) AND (cancer of the liver) AND (cardiopulmonary cerebral disease) AND (child-pugh score) AND (mental disease) AND (moderately severe) AND (severe) AND (severe hepatitis))"}
```
