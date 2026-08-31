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
{"candidate_id": "LLM04951", "doc_id": "NCT03156855_inc", "case_bucket": "or", "source_criterion": "children and teenagers aged less than 20 years, history of gastrectomy, gastric malignancy, including adenocarcinoma and lymphoma, previous allergic reaction to antibiotics (bismuth, amoxicillin, metronidazole, clarithromycin, tetracycline) and PPI (esomeprazole), contraindication to treatment drugs, pregnant or lactating women, severe concurrent disease, concomitant use of clopidogrel, or (9) Unwilling to accept random assignment of subjects", "candidate_expression": "((Unwilling to accept random assignment of subjects) AND (aged) AND (allergic reaction) AND (clopidogrel) AND (concomitant) AND (concurrent) AND (contraindication) AND (disease) AND (esomeprazole) AND (gastrectomy) AND (gastric malignancy) AND (history) AND (less than 20 years) AND (previous) AND (severe) AND (treatment drugs) AND (women) AND ((children) OR (teenagers)) AND ((amoxicillin) OR (bismuth) OR (clarithromycin) OR (metronidazole) OR (tetracycline)) AND ((PPI) OR (antibiotics)) AND ((lactating) OR (pregnant)) AND ((adenocarcinoma) OR (lymphoma)))"}
{"candidate_id": "LLM04952", "doc_id": "NCT03012984_exc", "case_bucket": "or", "source_criterion": "Preoperative history of schizophrenia, epilepsy, parkinsonism or myasthenia gravis; Preoperative radio- or chemotherapy; Inability to communicate in the preoperative period because of coma, profound dementia or language barrier; Preoperative obstructive sleep apnea (previously diagnosed as obstructive sleep apnea, or a STOP-Bang score >= 3); Brain trauma or neurosurgery; Preoperative left ventricular ejection fraction < 30%, sick sinus syndrome, severe sinus bradycardia (< 50 beats per minute), or second-degree or above atrioventricular block without pacemaker; Severe hepatic dysfunction (Child-Pugh class C) or severe renal dysfunction (requirement of renal replacement therapy before surgery); ASA classification >= IV.", "candidate_expression": "((< 30%) AND (< 50 beats per minute) AND (>= 3) AND (>= IV) AND (ASA classification) AND (Brain trauma) AND (Child-Pugh) AND (Inability to communicate) AND (Preoperative) AND (STOP-Bang score) AND (Severe) AND (atrioventricular block) AND (before surgery) AND (chemotherapy) AND (class C) AND (coma) AND (dementia) AND (epilepsy) AND (hepatic dysfunction) AND (history) AND (language barrier) AND (left ventricular ejection fraction) AND (myasthenia gravis) AND (neurosurgery) AND (obstructive sleep apnea) AND (pacemaker) AND (parkinsonism) AND (preoperative period) AND (profound) AND (renal dysfunction) AND (renal replacement therapy) AND (schizophrenia) AND (second-degree or above) AND (severe) AND (sick sinus syndrome) AND (sinus bradycardia) AND (surgery) AND (therapy radio) AND (without))"}
{"candidate_id": "LLM04953", "doc_id": "NCT02385448_exc", "case_bucket": "or", "source_criterion": "Operative findings not suggestive of endometriotic cyst Contraindications to progestogens or oral contraceptive pills Unwillingness to tolerate menstrual irregularity Planning pregnancy within 2 years of study Cannot understand English, Cantonese or Putonghua", "candidate_expression": "((Contraindications) AND (Operative findings) AND (endometriotic cyst suggestive) AND (menstrual irregularity Unwillingness to tolerate) AND (oral contraceptive pills) AND (pregnancy Planning within 2 years of study) AND (progestogens))"}
{"candidate_id": "LLM04954", "doc_id": "NCT01816997_exc", "case_bucket": "or", "source_criterion": "A1C >7.0% 2hr glucose during OGTT >200 mg/dL Total cholesterol >280 mg/dL Previous diabetic history, coronary artery disease Allergy to rosuvastatin or parvastatin Baseline ALT more than 3 times UNL Serum Cr > 2.0 mg/dL Pregnancy, breast feeding or plan to be pregnant woman.", "candidate_expression": "((2hr glucose during OGTT >200 mg/dL) AND (A1C >7.0%) AND (ALT Baseline more than 3 times UNL) AND (Allergy) AND (Pregnancy) AND (Serum Cr > 2.0 mg/dL) AND (Total cholesterol >280 mg/dL) AND (breast feeding) AND (coronary artery disease) AND (diabetic Previous history) AND (parvastatin) AND (pregnant plan to be) AND (rosuvastatin) AND (woman))"}
{"candidate_id": "LLM04955", "doc_id": "NCT02953873_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04956", "doc_id": "NCT03018171_inc", "case_bucket": "other", "source_criterion": "Written maternal informed consent Singleton pregnancy Gestational age = 37 weeks, ASA I BMI < 30 fetus in cephalic presentation", "candidate_expression": "((< 30) AND (= 37 weeks) AND (ASA) AND (BMI) AND (Gestational age) AND (I) AND (Singleton pregnancy) AND (Written maternal informed consent) AND (cephalic presentatio))"}
{"candidate_id": "LLM04957", "doc_id": "NCT03209011_inc", "case_bucket": "or", "source_criterion": "HBsAg and HBeAg positive for more than 6 months, HBV DNA detectable with ALT level abnormal lasted for three months and at least time190 IU/L or liver puncture biopsy demonstrated apparent inflammation, never treated before enrolled.", "candidate_expression": "((ALT level abnormal 190 IU/L) AND (inflammation) AND NOT (treated before enrolled) AND ((HBeAg positive) OR (HBsAg positive)) AND ((HBV DNA detectable) OR (liver puncture biopsy)))"}
{"candidate_id": "LLM04958", "doc_id": "NCT02277067_exc", "case_bucket": "other", "source_criterion": "Women undergoing cesarean section with general anesthesia will be excluded, because carbetocin is licensed for use with regional anaesthesia only. women undergoing cesarean section at less than 37 weeks of gestation.", "candidate_expression": "((Women) AND (cesarean section) AND (general anesthesia) AND (gestation) AND (less than 37 weeks) AND (women))"}
{"candidate_id": "LLM04959", "doc_id": "NCT01709981_exc", "case_bucket": "or", "source_criterion": "Plan for diagnostic-only coronary angiography On colchicine chronically History of intolerance to colchicine Glomerular filtration rate <30mL/minute or on dialysis Active malignancy or infection History of myelodysplasia High-dose statin load <24 hours prior to procedure Use of oral steroids or non-steroidal anti-inflammatory agents other than aspirin within 72 hours or 3 times the agent's half-life (whichever is longer) Use of strong CYP3A4/P-glycoprotein inhibitors (specifically ritonavir, ketoconazole, clarithromycin, cyclosporine, diltiazem and verapamil) Unable to consent Participating in a competing study", "candidate_expression": "((High-dose statin <24 hours prior to procedure) AND (colchicine) AND (colchicine chronically) AND (coronary angiography diagnostic-only) AND (intolerance) AND (myelodysplasia) AND (strong CYP3A4/P-glycoprotein inhibitors) AND NOT (aspirin) AND ((infection) OR (malignancy Active)) AND ((non-steroidal anti-inflammatory agents) OR (oral steroids)) AND ((within 3 times the agent's half-life 3 times the agent's half-life) OR (within 72 hours 72 hours)) AND ((clarithromycin) OR (cyclosporine) OR (diltiazem) OR (ketoconazole) OR (ritonavir) OR (verapamil)) AND ((Glomerular filtration rate <30mL/minute) OR (dialysis)))"}
{"candidate_id": "LLM04960", "doc_id": "NCT03131050_exc", "case_bucket": "or", "source_criterion": "Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug. Current Axis I primary psychiatric diagnosis other than major depressive disorder. Organic mental disease, including mental retardation. History of clinically significant disease, including any cardiovascular, hepatic, renal, respiratory, hematologic, endocrinologic, or neurologic disease, or clinically significant laboratory abnormality that is not stabilized or is anticipated to require treatment during the study. Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening. Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures. Use of antipsychotics or mood stabilizers within 5 days prior to screening. Has received depot antipsychotic medication within one cycle prior to screening. Known allergy or lack of response to mirtazapine. Has received ECT or MECT within 3 months prior to screening. History of anticholinergic drug allergy or complications (allergic reaction, skin rash, urticaria and other allergic reactions which caused by drugs). Smokers. Significant risk of suicidal and/or self-harm behaviors", "candidate_expression": "((Axis I) AND (Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug.) AND (Organic mental disease) AND (Smokers) AND (Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening.) AND (Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures.) AND (allergy) AND (anticholinergic drug) AND (anticipated to require) AND (clinically significant) AND (depot antipsychotic medication) AND (drugs) AND (during the study) AND (major depressive disorder) AND (mental retardation) AND (mirtazapine) AND (neurologic disease) AND (not) AND (other) AND (other than) AND (primary) AND (psychiatric diagnosis) AND (risk of) AND (screening) AND (within 3 months prior to screening) AND (within 5 days prior to screening) AND (within one cycle prior to screening) AND ((cardiovascular disease) OR (disease) OR (endocrinologic disease) OR (hematologic disease) OR (hepatic disease) OR (laboratory abnormality) OR (renal disease) OR (respiratory disease)) AND ((stabilized) OR (treatment)) AND ((antipsychotics) OR (mood stabilizers)) AND ((allergy) OR (lack of response)) AND ((ECT) OR (MECT)) AND ((allergic reaction) OR (allergic reactions) OR (skin rash) OR (urticaria)) AND ((self-harm behaviors) OR (suicidal behaviors)))"}
{"candidate_id": "LLM04961", "doc_id": "NCT03262038_exc", "case_bucket": "or", "source_criterion": "Inability to use verbal or pictorial pain scoring scales hypersensitivity to selective 5-HT receptor antagonists diagnosed congenital long QT syndrome severe hepatic impairment pregnancy or nursing mothers", "candidate_expression": "((Inability) AND (congenital long QT syndrome) AND (hepatic impairment severe) AND (hypersensitivity) AND (selective 5-HT receptor antagonists) AND ((pictorial pain scoring scales) OR (verbal pain scoring scales)) AND ((nursing) OR (pregnancy)))"}
{"candidate_id": "LLM04962", "doc_id": "NCT02426944_inc", "case_bucket": "or", "source_criterion": "history of significant bleeding (i.e. bleeding which required intervention or hospitalization), even in the absence of anticoagulation treatment at the time of the bleeding event, or a cardioembolic event, which occurred on anticoagulation, or a high risk profile of the patient, defined as a CHA2DS2-VASc score = 3 and a HAS-BLED score = 2", "candidate_expression": "((= 2) AND (= 3) AND (CHA2DS2-VASc score) AND (HAS-BLED score) AND (anticoagulation) AND (bleeding) AND (cardioembolic event) AND (high risk profile) AND (hospitalization) AND (intervention) AND (occurred on anticoagulation) AND (significant))"}
{"candidate_id": "LLM04963", "doc_id": "NCT02301039_inc", "case_bucket": "or", "source_criterion": "Age ≥ 18 years (Age ≥ 12 years for patients with bone sarcomas). Histologically confirmed diagnosis of unresectable, recurrent, and/or metastatic high grade soft-tissue or bone sarcoma of one of the following subtypes: soft tissue sarcomas (leiomyosarcoma, poorly differentiated/de-differentiated liposarcoma, high grade pleomorphic undifferentiated sarcoma/MFH and synovial sarcoma), and bone sarcomas (Ewing sarcoma, osteosarcoma, and chondrosarcoma [de-differentiated or mesenchymal]). ECOG Performance Status of 0 or 1. At least one site of measurable disease on CT/MRI scans as defined by RECIST 1.1. Baseline imaging must be performed within 30 days of dosing. At least one site of accessible disease for pre- and post-treatment core biopsies for at least 20 patients per arm on the expansion cohorts. Patients may have received 1-3 prior systemic therapies in the metastatic setting. Adequate organ function within 14 days of dosing Must be willing to provide and have available archival tissue for PD-L1 testing. Written, voluntary informed consent. Fertile men and women of childbearing potential must agree to use an effective method of birth control from providing signed consent and for 120 days after last study drug administration. Women of childbearing potential include pre-menopausal women and women within the first 2 years of the onset of menopause. Women of childbearing potential must have a negative pregnancy test ≤ 72 hours prior to Day 1 of study. Effective methods of birth control include: surgically sterile, barrier device (condom, diaphragm), contraceptive coil, intrauterine device (IUD), and abstinence. Life expectancy of >12 weeks. Patients with central nervous system disease are eligible for enrollment if they have received prior radiotherapy or surgery to sites of CNS metastatic disease and are without evidence of clinical progression for at least 4 weeks prior to screening, have no evidence of new or enlarging brain metastases, and are off steroids for at least 7 days before first dose of pembrolizumab.", "candidate_expression": "((0 or 1) AND (1-3) AND (>12 weeks) AND (Adequate organ function) AND (Age) AND (Baseline) AND (CNS metastatic disease) AND (Day 1) AND (ECOG Performance Status) AND (Histologically) AND (Life expectancy) AND (Women) AND (Written, voluntary informed consent.) AND (birth control) AND (brain metastases) AND (central nervous system disease) AND (childbearing potential) AND (clinical progression) AND (confirmed) AND (dosing) AND (first dose of pembrolizumab) AND (for 120 days after last study drug administration) AND (for at least 4 weeks prior to screening) AND (for at least 7 days before first dose of pembrolizumab) AND (from providing signed consent) AND (high grade) AND (imaging) AND (last study drug administration) AND (leiomyosarcoma) AND (liposarcoma) AND (measurable disease) AND (metastatic setting) AND (negative) AND (no) AND (off) AND (pembrolizumab) AND (pleomorphic) AND (pre-menopausal) AND (pregnancy test) AND (prior) AND (providing signed consent) AND (screening) AND (steroids) AND (synovial sarcoma) AND (systemic therapies) AND (the onset of menopause) AND (undifferentiated) AND (within 14 days of dosing) AND (within 30 days of dosing) AND (within the first 2 years of the onset of menopause) AND (without) AND (women) AND (≤ 72 hours prior to Day 1) AND (≥ 12 years) AND (≥ 18 years) AND ((Age) OR (bone sarcomas)) AND ((radiotherapy) OR (surgery)) AND ((enlarging) OR (new)) AND ((bone sarcoma) OR (soft-tissue sarcoma)) AND ((de-differentiated) OR (poorly differentiated)) AND ((MFH) OR (sarcoma)) AND ((bone sarcomas) OR (soft tissue sarcomas)) AND ((Ewing sarcoma) OR (chondrosarcoma) OR (osteosarcoma)) AND ((de-differentiated) OR (mesenchymal)) AND ((CT scans) OR (MRI scans)) AND ((men) OR (women)) AND ((high grade) OR (metastatic) OR (recurrent) OR (unresectable)) AND ((condom) OR (diaphragm)) AND ((abstinence) OR (barrier device) OR (contraceptive coil) OR (intrauterine device (IUD)) OR (surgically sterile)))"}
{"candidate_id": "LLM04964", "doc_id": "NCT02762851_exc", "case_bucket": "or", "source_criterion": "Anaphylactic reaction to a previous dose of TIV(trivalent influenza vaccine) Known IgE( Immunoglobulin E)-mediated hypersensitivity to eggs manifested as hives, swelling of the mouth and throat, difficulty in breathing, hypotension, or shock Guillain-Barré syndrome within eight weeks of a previous influenza vaccine Anaphylactic reaction to neomycin Patients who have had influenza vaccine in two of the three previous years", "candidate_expression": "((Anaphylactic reaction) AND (Guillain-Barré syndrome) AND (IgE( Immunoglobulin E)-mediated hypersensitivity) AND (TIV) AND (a previous influenza vaccine) AND (difficulty in breathing) AND (eggs) AND (hives) AND (hypotension) AND (in two of the three previous years) AND (influenza vaccine) AND (neomycin) AND (previous) AND (shock) AND (swelling of the mouth and throat) AND (trivalent influenza vaccine) AND (within eight weeks of a previous influenza vaccine))"}
{"candidate_id": "LLM04965", "doc_id": "NCT03134196_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04966", "doc_id": "NCT00812344_inc", "case_bucket": "other", "source_criterion": "body mass index (BMI) between 19 to 30 kg/m2 and body weight between 50 to 100 kg inclusive", "candidate_expression": "((50 to 100 kg inclusive) AND (between 19 to 30 kg/m2) AND (body mass index (BMI)) AND (body weight))"}
{"candidate_id": "LLM04967", "doc_id": "NCT01943409_inc", "case_bucket": "or", "source_criterion": "Patients with PN during their hospitalization Patients hospitalized in medical, surgical or ICU wards Signed informed consent either from the patient, their legally authorized representative or a direct family member", "candidate_expression": "((PN) AND (Signed informed consent either from the patient, their legally authorized representative or a direct family member) AND (during their hospitalization) AND (hospitalization) AND (hospitalized) AND (their hospitalization) AND ((ICU wards) OR (medical wards) OR (surgical wards)))"}
{"candidate_id": "LLM04968", "doc_id": "NCT03381755_exc", "case_bucket": "or", "source_criterion": "taken adenosine diphosphate (ADP) receptor antagonists within 2 weeks Platelet count <100g/L; A history of bleeding tendency; Aspirin, ticagrelor or clopidogrel allergies; Severe liver injury.", "candidate_expression": "((<100g/L) AND (Platelet count) AND (Severe) AND (adenosine diphosphate (ADP) receptor antagonists) AND (allergies) AND (bleeding tendency) AND (history) AND (liver injury) AND (within 2 weeks) AND ((Aspirin) OR (clopidogrel) OR (ticagrelor)))"}
{"candidate_id": "LLM04969", "doc_id": "NCT03040024_exc", "case_bucket": "or", "source_criterion": "Emergency surgery Monitored Anesthesia Care (i.e., regional anesthesia alone without plans for general anesthesia) Surgery involving the eye, eyebrow, forehead, or frontal scalp near the sensor placement Poor health literacy Allergy, or have experienced any drug reaction to ketamine Pregnant or lactating Currently in active alcohol withdrawal", "candidate_expression": "((Allergy) AND (Currently) AND (Emergency) AND (Emergency surgery) AND (Monitored Anesthesia Care) AND (Poor health literacy) AND (Pregnant) AND (Surgery) AND (active) AND (alcohol withdrawal) AND (alone) AND (drug reaction) AND (eye) AND (eyebrow) AND (forehead) AND (frontal scalp) AND (general anesthesia) AND (ketamine) AND (lactating) AND (plans for) AND (regional anesthesia) AND (without))"}
{"candidate_id": "LLM04970", "doc_id": "NCT02957305_exc", "case_bucket": "or", "source_criterion": "patients who do not wish to participate in the project; patients with ectopic pregnancy; patients with comorbidities (heart failure congestive, chronic obstructive pulmonary disease); patients with hypovolemic shock; patients with cervical incompetence; patients with infected miscarriage/abortion (presence of fever, pus from the cervix, leukocytosis [> 14000]); patients with twin pregnancy; patients with Marfan syndrome; patients allergic to misoprostol; patients with coagulopathy; patients with opening of cervical internal os (4 mm of dilatation at the time of consultation); patients with previous surgery of the cervix (conization); patients with concomitant use of IUDs.", "candidate_expression": "((IUDs) AND (Marfan syndrome) AND (allergic) AND (cervical incompetence) AND (coagulopathy) AND (comorbidities) AND (conization) AND (ectopic pregnancy) AND (hypovolemic shock) AND (misoprostol) AND (opening of cervical internal os 4 mm of dilatation) AND (patients who do not wish to participate in the project) AND (pregnancy twin) AND (surgery cervix) AND ((abortion) OR (miscarriage)) AND ((fever) OR (leukocytosis > 14000) OR (pus from the cervix)) AND ((chronic obstructive pulmonary disease) OR (heart failure congestive)))"}
{"candidate_id": "LLM04971", "doc_id": "NCT02219880_inc", "case_bucket": "or", "source_criterion": "Aged between 18-70 years Meets the Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria for generalised anxiety disorder (GAD) based on structured interview (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]. Note that while the MINI-Plus 6 uses the DSM-IV criteria, the same criteria are used in the DSM-V). Presents with anxiety (Hamilton Anxiety Rating Scale = 18) at the time of study entry Fluent in written and spoken English Provides a signed copy of the consent form Primary diagnosis other than GAD Presentation of moderate to severe depressive symptoms (Montgomery-Asberg Rating Scale: MADRS = 18 at time of study entry or = 24 at any time during study) Presentation of suicidal ideation (= 3 on MADRS suicidal thoughts domain at time of study entry or at any time during study) Current diagnosis of bipolar disorder or schizophrenia on structured interview (MINI Plus) Current substance/alcohol use disorder on structured interview (MINI Plus) Page 21 of 39 Commercial-in-Confidence Currently taking an antidepressant, mood stabiliser, antipsychotic, anticonvulsant, warfarin or thyroxin, or current regular use (more than 2 days per week) of a benzodiazepine or opioid-based analgesic Current use of a psychotropic nutraceutical (e.g. St John's wort) Previous intolerance to kava Three or more failed trials of pharmacotherapy for the current GAD episode Recently commenced psychotherapy (within four weeks of study entry) Known or suspected clinically unstable systemic medical disorder Diagnosed hepato-biliary disease/inflammation Elevated liver enzymes at baseline blood test Pregnancy or breastfeeding, or trying to conceive Not using medically approved contraception (including abstinence) if female and of childbearing age Unable to participate in all scheduled visits, treatment plan, or other trial procedures according to the protocol (except for the optional genetic component)", "candidate_expression": "((Aged between 18-70 years) AND (Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria) AND (GAD) AND (GAD episode current) AND (Hamilton Anxiety Rating Scale = 18) AND (MADRS) AND (MADRS suicidal thoughts domain = 3) AND (MINI Plus) AND (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]) AND (Montgomery-Asberg Rating Scale) AND (Primary diagnosis) AND (St John's wort) AND (abstinence) AND (age childbearing) AND (anxiety at the time of study entry) AND (blood test baseline) AND (childbearing age) AND (depressive symptoms moderate to severe) AND (female) AND (generalised anxiety disorder) AND (intolerance Previous) AND (kava) AND (liver enzymes Elevated) AND (medical disorder clinically unstable systemic) AND (more than 2 days per week) AND (psychotherapy Recently within four weeks of study entry) AND (psychotropic nutraceutical) AND (structured interview) AND (suicidal ideation) AND (trials of pharmacotherapy Three or more failed) AND (use Current) AND NOT (GAD) AND NOT (contraception medically approved) AND ((scheduled visits) OR (treatment plan) OR (trial procedures)) AND ((= 18 at time of study entry) OR (= 24 at any time during study)) AND ((at any time during study) OR (at time of study entry)) AND ((bipolar disorder) OR (schizophrenia)) AND ((alcohol use disorder) OR (substance use disorder)) AND ((taking Currently) OR (use current regular)) AND ((anticonvulsant) OR (antidepressant) OR (antipsychotic) OR (mood stabiliser) OR (thyroxin) OR (warfarin)) AND ((benzodiazepine) OR (opioid-based analgesic)) AND ((Known) OR (suspected)) AND ((hepato-biliary disease) OR (hepato-biliary inflammation)) AND ((Pregnancy) OR (breastfeeding) OR (trying to conceive)))"}
{"candidate_id": "LLM04972", "doc_id": "NCT03216967_exc", "case_bucket": "or", "source_criterion": "Known proved BKV nephropathy Hypersensitivity to everolimus, sirolimus or excipient Concomitant treatment by leflunomide, cidofovir, sirolimus, Millepertuis (Hypericum Perforatum) Pregnant or lactating women Women of child bearing potential unless they are using a birth control method", "candidate_expression": "((BKV nephropathy proved) AND (Hypericum Perforatum) AND (Hypersensitivity) AND (Women) AND (child bearing potential) AND (women) AND NOT (birth control method) AND ((Millepertuis) OR (cidofovir) OR (leflunomide) OR (sirolimus)) AND ((Pregnant) OR (lactating)) AND ((everolimus) OR (excipient) OR (sirolimus)))"}
{"candidate_id": "LLM04973", "doc_id": "NCT02042287_inc", "case_bucket": "other", "source_criterion": "> 18 years old Acute symptomatic BV Signed informed consent Insufficient knowledge of German Illiteracy Pregnancy Acute illness Known allergies against ingredients of the investigational products", "candidate_expression": "((Acute illness) AND (BV Acute symptomatic) AND (Illiteracy) AND (Insufficient knowledge of German) AND (Pregnancy) AND (Signed informed consent) AND (allergies) AND (ingredients of the investigational products) AND (old 18 years))"}
{"candidate_id": "LLM04974", "doc_id": "NCT02858804_exc", "case_bucket": "or", "source_criterion": "with centre neural system involvement serious complications such as uncontrolled diabetes, gastric ulcer or other serious angiocardiopathy determined by the physician HIV positive or active HBV infection or other uncontrolled systematic infection clinical central nervous dysfunction serious surgery within 30 days pregnancy or baby nursing period or un-contracepted child bearing period woman.", "candidate_expression": "((HIV positive) AND (active HBV infection) AND (angiocardiopathy serious) AND (baby nursing period) AND (central nervous dysfunction) AND (centre neural system involvement) AND (child bearing period) AND (complications serious) AND (determined by the physician) AND (diabetes uncontrolled) AND (gastric ulcer) AND (pregnancy) AND (surgery serious within 30 days) AND (systematic infection uncontrolled) AND (woman) AND NOT (contracepted))"}
{"candidate_id": "LLM04975", "doc_id": "NCT02654912_exc", "case_bucket": "or", "source_criterion": "contraindications from manufacturer for medications including currently taking haloperidol, artane, Phenergan (Promethazine), chlorpromazine, erythromycin, Azithromycin, clarithromycin, Ketoconazole, fluconazole, mefloquine (as prophylaxis), lumefantrine (in Coartem), quinine, Septrin anyone seriously ill currently taking antimalarial medicines allergy to artemisinin drugs pregnant women in first trimester children under 3 months of age reported heart condition", "candidate_expression": "((Azithromycin) AND (Coartem) AND (Ketoconazole) AND (Phenergan) AND (Promethazine) AND (Septrin) AND (age) AND (allergy) AND (antimalarial medicines) AND (artane) AND (artemisinin drugs) AND (children) AND (chlorpromazine) AND (clarithromycin) AND (contraindications) AND (erythromycin) AND (first trimester) AND (fluconazole) AND (haloperidol) AND (heart condition) AND (lumefantrine) AND (mefloquine) AND (pregnant) AND (quinine) AND (seriously ill) AND (under 3 months) AND (women))"}
```
