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
{"candidate_id": "LLM03726", "doc_id": "NCT03236246_inc", "case_bucket": "or", "source_criterion": "Estimated glomerular filtration rate =20 mL/min and <60 mL/min Hgb =8.5 g/dL and =11.5 g/dL Serum ferritin =500 ng/mL and transferrin saturation (TSAT) =25% Serum intact parathyroid hormone =600 pg/mL", "candidate_expression": "((Estimated glomerular filtration rate =20 mL/min and <60 mL/min) AND (Hgb =8.5 g/dL and =11.5 g/dL) AND (Serum intact parathyroid hormone =600 pg/mL) AND (TSAT) AND ((Serum ferritin =500 ng/mL) OR (transferrin saturation =25%)))"}
{"candidate_id": "LLM03727", "doc_id": "NCT02456129_exc", "case_bucket": "or", "source_criterion": "Incompletely cured pre-existing diseases for which it can be assumed that the absorption, distribution, metabolism, elimination or effects of the study drugs will not be normal Known or suspected liver diseases Clinically relevant findings(e.g. blood pressure, electrocardiogram(ECG); physical and gynecological examination, laboratory examination)", "candidate_expression": "((Clinically relevant) AND (Incompletely cured) AND (Known) AND (blood pressure) AND (can be assumed) AND (electrocardiogram(ECG)) AND (findings) AND (gynecological examination) AND (laboratory examination) AND (liver diseases) AND (physical examination) AND (pre-existing diseases) AND (suspected))"}
{"candidate_id": "LLM03728", "doc_id": "NCT01888965_inc", "case_bucket": "or", "source_criterion": "Patients with a confirmed diagnosis of: 1. Stage 4 colon cancer either s/p metastasectomy or post-initial chemotherapy or maintenance \"standard of care\", either involving 5-fluorouracil/leucovorin (5-FU/LV) alone or continual bevacizumab alone. Patients in maintenance cohort must have had 2 consecutive CT scans showing stable disease and not be experiencing significant prior treatment-related toxicity above Grade 1. 2. Pancreas cancer, either s/p resection and adjuvant chemotherapy or locally advanced pancreas cancer s/p chemotherapy and radiation. Initial chemotherapy or radiation therapy may have been stopped between 2 weeks and 2 months prior to study start, and patients must have recovered from prior treatment related toxicity to grade 1 or less. Prior surgery, including tumor resection or metastasectomy must have been performed at least 4 weeks prior to study enrollment. No concomitant anti-cancer treatment is allowed Age >/= 18 years Performance status of 0-1 Adequate hepatic, bone marrow, and renal function Partial thromboplastin time (PTT) must be </= 1.5 x upper normal limit of institution's normal range and INR (International Normalized Ratio) < 1.5. Life expectancy >/= 4 months for maintenance cohorts and >/= 6 months for adjuvant cohorts Women of childbearing potential must have a negative serum pregnancy test within 14 days prior to initiation of treatment and must not be lactating. Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent", "candidate_expression": "((0-1) AND (2) AND (< 1.5) AND (</= 1.5 x upper normal limit) AND (>/= 18 years) AND (>/= 4 months) AND (>/= 6 months) AND (Adequate) AND (Age) AND (CT scans) AND (INR (International Normalized Ratio)) AND (Life expectancy) AND (No concomitant anti-cancer treatment is allowed) AND (Pancreas cancer) AND (Partial thromboplastin time (PTT)) AND (Performance status) AND (Prior) AND (Stage 4) AND (Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent) AND (Women) AND (adjuvant chemotherapy) AND (at least 4 weeks prior to study enrollment) AND (between 2 weeks and 2 months prior to study start) AND (bone marrow function) AND (chemotherapy) AND (childbearing potential) AND (colon cancer) AND (disease) AND (function hepatic) AND (initiation of treatment) AND (lactating) AND (locally advanced) AND (may have been stopped) AND (metastasectomy) AND (negative) AND (not) AND (pancreas cancer) AND (prior) AND (radiation) AND (recovered from prior treatment) AND (renal function) AND (resection) AND (s/p adjuvant chemotherapy) AND (s/p chemotherapy) AND (s/p radiation) AND (s/p resection) AND (serum pregnancy test) AND (stable) AND (study enrollment) AND (study start) AND (surgery) AND (treatment) AND (treatment-related toxicity) AND (within 14 days prior to initiation of treatment) AND ((maintenance \"standard of care\") OR (post-initial chemotherapy) OR (s/p metastasectomy)) AND ((chemotherapy) OR (radiation therapy)) AND ((metastasectomy) OR (tumor resection)) AND ((adjuvant cohorts) OR (maintenance cohorts)) AND ((5-fluorouracil/leucovorin (5-FU/LV)) OR (bevacizumab)))"}
{"candidate_id": "LLM03729", "doc_id": "NCT02762851_inc", "case_bucket": "other", "source_criterion": "Age = 18 years and NYHA (New York Heart Association) functional class II, III and IV", "candidate_expression": "((Age = 18 years) AND (NYHA (New York Heart Association) functional class II, III and IV))"}
{"candidate_id": "LLM03730", "doc_id": "NCT00351611_exc", "case_bucket": "or", "source_criterion": "Pre-existing eye diseases (glaucoma). Insufficient response to pregabalin in the treatment of partial seizure, or patients currently receiving pregabalin treatment.", "candidate_expression": "((Insufficient response) AND (eye diseases Pre-existing) AND (glaucoma) AND (partial seizure) AND (pregabalin))"}
{"candidate_id": "LLM03731", "doc_id": "NCT03382106_inc", "case_bucket": "other", "source_criterion": "Between the age of 25 to 65 at baseline Be willing to participate in a smoking cessation program Be willing to attend all clinic visits Must be currently smoking at least ½ pack/day at baseline (confirmed with cotinine level and CO Smokerlyzer >5 pack-year history of smoking Global Initiative for Chronic Obstructive Lung Disease (GOLD) 0: FEV1=0.80 and FEV1/FVC>0.70 Forced Expiratory Volume in 1 second (FEV1), Forced Vital Capacity (FVC) GOLD 1: FEV1=0.80 and FEV1/FVC < 0.70 GOLD 2: 0.50=FEV1<0.80 and FEV1/FVC < 0.70 Be willing to abstain from using any nicotine patches, e-cigarettes, or marijuana for the duration of the study.", "candidate_expression": "((0) AND (0.50= <0.80) AND (1) AND (2) AND (< 0.70) AND (=0.80) AND (>0.70) AND (>5) AND (Between 25 to 65) AND (CO Smokerlyzer) AND (FEV1) AND (FEV1/FVC) AND (GOLD) AND (Global Initiative for Chronic Obstructive Lung Disease (GOLD)) AND (age) AND (at baseline) AND (at least ½) AND (cotinine level) AND (pack-year) AND (pack/day) AND (smoking) AND (smoking cessation program) AND (willing to participate))"}
{"candidate_id": "LLM03732", "doc_id": "NCT01963754_exc", "case_bucket": "or", "source_criterion": "If smoking and/or other drug addiction is present If local anesthetic allergy is present Patient subjected to chemical or radiotherapy if Hepatic disease is present If immunodepression is present If Pregnancy is present If Diabetes is present If Heart disease is present", "candidate_expression": "((Diabetes) AND (Heart disease) AND (Hepatic disease) AND (Pregnancy) AND (allergy) AND (chemical) AND (drug addiction) AND (immunodepression) AND (local anesthetic) AND (radiotherapy) AND (smoking))"}
{"candidate_id": "LLM03733", "doc_id": "NCT02882113_inc", "case_bucket": "other", "source_criterion": "19 years old and above. Patients who previously have received a liver transplant over the last six months and within last three years. Patients who are on Tacrolimus immunosuppressive therapy twice a day for at least two weeks. Patients who have normal liver function and renal function. Patients who have been monitored without complication such as acute rejection. Patients willing to sign his/her consent.", "candidate_expression": "((19 years and above) AND (Patients willing to sign his/her consent) AND (Tacrolimus) AND (acute rejection) AND (at least two weeks) AND (complication) AND (last six months and within last three years) AND (liver function) AND (liver transplant) AND (normal) AND (old) AND (renal function) AND (twice a day) AND (without))"}
{"candidate_id": "LLM03734", "doc_id": "NCT01491295_inc", "case_bucket": "or", "source_criterion": "HBsAg-positive for more than 6 months (HBeAg-positive or HBeAg-negative). Age > 20 y/o. Under lamivudine/adefovir treatment for more than 1 year due to previous lamivudine resistance (LAM-R), current HBV DNA is undetectable (< 20 IU/ml) during enrollment.", "candidate_expression": "((Age > 20 y/o) AND (HBV DNA undetectable < 20 IU/ml during enrollment) AND (HBeAg negative) AND (HBeAg positive) AND (HBsAg positive more than 6 months) AND (LAM-R) AND (adefovir) AND (lamivudine))"}
{"candidate_id": "LLM03735", "doc_id": "NCT02749617_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of multiple myeloma according to criteria of the International Myeloma Working Group Patients in whom a LEN-DEX-based treatment regimen is indicated Adult patients ≥ 19 years of age who are able to freely provide informed consent", "candidate_expression": "((Adult) AND (DEX) AND (LEN) AND (LEN-DEX-based) AND (able to freely provide informed consent) AND (age) AND (criteria of the International Myeloma Working Group) AND (is indicated) AND (multiple myeloma) AND (treatment regimen) AND (≥ 19 years))"}
{"candidate_id": "LLM03736", "doc_id": "NCT03400735_inc", "case_bucket": "other", "source_criterion": "The diagnosis of chronic bronchitis The diagnosis of community-acquired pneumoniae FEV1 value = 30-80% The diagnosis of mild-severe acute exacerbation of chronic bronchitis (AECB) Oxygen saturation < 90%", "candidate_expression": "((< 90%) AND (= 30-80%) AND (AECB) AND (FEV1 value) AND (Oxygen saturation) AND (acute) AND (chronic bronchitis) AND (community-acquired pneumoniae) AND (exacerbation of chronic bronchitis) AND (mild-severe))"}
{"candidate_id": "LLM03737", "doc_id": "NCT03304496_inc", "case_bucket": "or", "source_criterion": "Men and women older than 18 years, scheduled consecutively to perform a coronary procedure in the department of hemodynamics of the National Institute of Cardiology \"Ignacio Chavez\". Patients may have any of the following indications for cardiac catheterization: Thoracic pain under study. Stable chronic coronary disease. Acute myocardial infarction with ST segment elevation, not perfused (without timely reperfusion therapy) with less than 4 weeks of evolution. Acute myocardial infarction with ST-segment elevation, successful thrombolytic therapy, which will undergo drug-invasive therapy. Acute myocardial infarction without ST segment elevation. Unstable angina. Any acute coronary syndrome, to intervene non-infarct-related artery. Disease of any heart valve. Myocarditis or pericarditis. Dilated cardiomyopathy. Patients in renal or cardiac transplantation protocol for any etiology. Congenital heart disease that requires knowing the coronary anatomy prior to surgical correction. The planned procedure can be any of the following: For diagnostic purposes (coronary angiography only, left catheterization, left and right catheterization). For therapeutic purposes: percutaneous coronary intervention (PCI), with or without stent placement. A priori access must be right or left radial artery. Radial arterial pulse may be present or absent by palpation. Modified Allen or Barbeau test should be positive (presence of collateral palmar flow).", "candidate_expression": "((Dilated) AND (PCI) AND (Radial arterial) AND (ST segment elevation) AND (ST-segment elevation) AND (Stable) AND (access) AND (artery) AND (cardiac catheterization) AND (collateral palmar flow) AND (coronary procedure) AND (department of hemodynamics) AND (diagnostic) AND (drug-invasive therapy) AND (evolution) AND (heart valve) AND (indications) AND (intervene) AND (knowing the coronary anatomy) AND (left catheterization) AND (non-infarct-related) AND (older than 18) AND (only) AND (palpation) AND (percutaneous coronary intervention) AND (positive) AND (presence) AND (prior to surgical correction.) AND (priori) AND (procedure) AND (pulse) AND (reperfusion therapy) AND (right catheterization) AND (scheduled) AND (stent placement) AND (successful) AND (surgical correction) AND (the National Institute of Cardiology \"Ignacio Chavez\") AND (therapeutic) AND (thrombolytic therapy) AND (timely) AND (will undergo) AND (with less than 4 weeks of evolution) AND (without) AND (years) AND ((Men) OR (women)) AND ((Acute myocardial infarction) OR (Congenital heart disease) OR (Disease) OR (Myocarditis) OR (Thoracic pain) OR (Unstable angina) OR (acute coronary syndrome) OR (cardiac transplantation) OR (cardiomyopathy) OR (chronic coronary disease) OR (pericarditis) OR (renal transplantation)) AND ((coronary angiography)) AND ((left radial artery) OR (right radial artery)) AND ((absent) OR (present)) AND ((Barbeau test) OR (Modified Allen test)))"}
{"candidate_id": "LLM03738", "doc_id": "NCT03530124_inc", "case_bucket": "other", "source_criterion": "=32 weeks gestational age at birth =6 weeks postnatal age at randomization Remains hospitalized after birth (has never been discharged home) Treating clinician deems infant eligible to receive 2-month vaccines English- or Spanish-speaking parent(s)/legally authorized representative(s) (LAR(s)) Not planned for discharge within 60 hours of study entry The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process", "candidate_expression": "((2-month vaccines) AND (=32 weeks) AND (=6 weeks) AND (Not) AND (The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process) AND (after birth) AND (at randomization) AND (birth) AND (discharge) AND (eligible) AND (gestational age at birth) AND (hospitalized) AND (planned) AND (postnatal age) AND (study entry) AND (within 60 hours of study entry))"}
{"candidate_id": "LLM03739", "doc_id": "NCT03156855_inc", "case_bucket": "or", "source_criterion": "children and teenagers aged less than 20 years, history of gastrectomy, gastric malignancy, including adenocarcinoma and lymphoma, previous allergic reaction to antibiotics (bismuth, amoxicillin, metronidazole, clarithromycin, tetracycline) and PPI (esomeprazole), contraindication to treatment drugs, pregnant or lactating women, severe concurrent disease, concomitant use of clopidogrel, or (9) Unwilling to accept random assignment of subjects", "candidate_expression": "((Unwilling to accept random assignment of subjects) AND (aged less than 20 years) AND (allergic reaction previous) AND (clopidogrel concomitant) AND (contraindication) AND (disease severe concurrent) AND (esomeprazole) AND (gastrectomy history) AND (gastric malignancy) AND (treatment drugs) AND (women) AND ((children) OR (teenagers)) AND ((amoxicillin) OR (bismuth) OR (clarithromycin) OR (metronidazole) OR (tetracycline)) AND ((PPI) OR (antibiotics)) AND ((lactating) OR (pregnant)) AND ((adenocarcinoma) OR (lymphoma)))"}
{"candidate_id": "LLM03740", "doc_id": "NCT02256956_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((>7) AND (Alcohol abuse) AND (CYP3A inducers) AND (CYP3A inhibitors) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Healthy) AND (Heart disease) AND (Male) AND (Metabolic Equivalents) AND (Neurological disease) AND (Obstructive uropathy) AND (Ongoing) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Suspicion) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction) AND (tested drugs) AND (tested sites) AND (treatment))"}
{"candidate_id": "LLM03741", "doc_id": "NCT03259243_exc", "case_bucket": "or", "source_criterion": "Patient with history of allergy in any kind anesthetic drug Patient who pregnant Patient who sign for single port gynecologic laparoscopic surgery or NOTE surgery Patient whom the surgery is withhold or canceled Patient whom the surgery is converted to laparotomy", "candidate_expression": "((NOTE surgery) AND (allergy) AND (anesthetic drug) AND (any kind) AND (canceled) AND (converted to) AND (gynecologic laparoscopic surgery) AND (history) AND (laparotomy) AND (pregnant) AND (single port) AND (surgery) AND (withhold))"}
{"candidate_id": "LLM03742", "doc_id": "NCT03168178_exc", "case_bucket": "or", "source_criterion": "Known fetal anomaly Other indication for intrapartum antibiotics (endocarditis prophylaxis, other known maternal infection)", "candidate_expression": "((endocarditis prophylaxis) AND (fetal anomaly) AND (indication) AND (intrapartum antibiotics) AND (maternal infection))"}
{"candidate_id": "LLM03743", "doc_id": "NCT02384850_inc", "case_bucket": "or", "source_criterion": "1. Patients with histologically confirmed diagnosis of colorectal cancer presenting with unresectable stage IV (UICC) disease (primary tumor may be present) 2. Patients who are feasible for treatment with FOLFOX (prior adjuvant or palliative treatment is allowed) 3. ECOG Performance status ≤ 1 4. Life expectancy > 3 months 5. Age ≥18 years 6. Haematologic function as follows (5% deviation allowed): ANC ≥ 1.5 x 109/L platelets ≥ 100 x109/L hemoglobin ≥ 9 g/dl or 5.59 mmol/l 7. Adequate liver function as follows (10% deviation allowed) serum alanine transaminase (ALT) ≤ 2.5 x ULN (in case of liver metastases < 5 x ULN) total bilirubin ≤ 1.5 x ULN (patients with Gilbert's syndrome total bilirubin ≤2.5 x ULN) 8. Adequate renal function as follows (10% deviation allowed) · creatinine ≤ 1.5 x ULN 9. Signed written informed consent 10. Women of child-bearing potential must have a negative pregnancy test", "candidate_expression": "((ANC ≥ 1.5 x 109/L) AND (Age ≥18 years) AND (ECOG Performance status ≤ 1) AND (FOLFOX) AND (Life expectancy > 3 months) AND (Signed written informed consent) AND (Women) AND (child-bearing potential) AND (colorectal cancer) AND (creatinine ≤ 1.5 x ULN) AND (disease unresectable stage IV (UICC) IV) AND (hemoglobin) AND (liver function Adequate) AND (liver metastases < 5 x ULN) AND (platelets ≥ 100 x109/L) AND (pregnancy test negative) AND (renal function Adequate) AND (serum alanine transaminase (ALT) ≤ 2.5 x ULN) AND (total bilirubin ≤2.5 x ULN) AND ((confirmed) OR (histologically)) AND ((adjuvant treatment) OR (palliative treatment)) AND ((≥ 5.59 mmol/l) OR (≥ 9 g/dl)) AND ((Gilbert's syndrome) OR (total bilirubin ≤ 1.5 x ULN)))"}
{"candidate_id": "LLM03744", "doc_id": "NCT03624517_inc", "case_bucket": "or", "source_criterion": "Adult males and females who are 18 years of age or older. Evidence or suspicion of upper gastrointestinal bleed (GIB) Patient with known or suspected cirrhosis Upper GIB secondary to bleeding esophageal varices as show by esophageal endoscopy, requiring endoscopic band ligation (EBL) at presentation Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so", "candidate_expression": "((Adult) AND (Upper GIB secondary) AND (Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so) AND (cirrhosis suspected) AND (endoscopic band ligation (EBL) requiring at presentation) AND (esophageal endoscopy) AND (esophageal varices bleeding) AND (females 18 years of age or older Evidence) AND (males) AND (upper gastrointestinal bleed (GIB) suspicion known))"}
{"candidate_id": "LLM03745", "doc_id": "NCT00787254_inc", "case_bucket": "or", "source_criterion": "The patient was on nonsteroid anti-inflammatory drug (NSAID) treatment on the day when consent was obtained, and requires the long-term continuous treatment even after treatment with the investigational drug is started. The patient was confirmed to have a history of gastric ulcer or duodenal ulcer.", "candidate_expression": "((consent) AND (duodenal ulcer) AND (gastric ulcer) AND (history) AND (nonsteroid anti-inflammatory drug (NSAID)) AND (on the day when consent was obtained) AND (the day when consent was obtained))"}
{"candidate_id": "LLM03746", "doc_id": "NCT02092467_exc", "case_bucket": "or", "source_criterion": "Current or recent infection Clinically significant laboratory abnormalities Pregnancy", "candidate_expression": "((Pregnancy) AND (infection) AND (laboratory) AND (laboratory abnormalities Clinically significant) AND ((Current) OR (recent)))"}
{"candidate_id": "LLM03747", "doc_id": "NCT01959061_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed colorectal adenocarcinoma Disease limited to the liver Unresectable disease by surgery or other local therapies Age >18 years ECOG performance status 0-2,Child pugh A or B Expected survival = 3 months Adequate hematological, hepatic, and renal function", "candidate_expression": "((Age >18 years) AND (Child pugh A B) AND (Disease limited to the liver) AND (ECOG performance status 0-2) AND (Expected survival = 3 months) AND (Histologically) AND (Unresectable disease) AND (colorectal adenocarcinoma Histologically confirmed) AND (hematological function) AND (hepatic function) AND (local therapies other) AND (renal function) AND (surgery))"}
{"candidate_id": "LLM03748", "doc_id": "NCT02755701_exc", "case_bucket": "or", "source_criterion": "Child-Pugh score > 12 Having been diagnosed as HCC within the past 5 years Serum creatinine > 1.5mg/dl Serum bilirubin > 5.0mg/dl Presence of such complications as SBP, or hepatic encephalopathy(West Haven grade = 3) Patients who experienced organ failure by acute exacerbation of liver cirrhosis within the past 1 month Presence of serious cardiac or respiratory disease Contraindicated to either diuretics or BCAA Having commenced anti-viral treatment against hepatitis C, B within the past 1 month Pregnant or lactating women Chronic alcohol taker Woman patients who do not agree to the contraception from baseline to 12 month Unsuitable patients judged by investigator Patients participating in another clinical trial within 1 month", "candidate_expression": "((Child-Pugh score > 12) AND (Contraindicated) AND (HCC past 5 years) AND (Patients participating in another clinical trial within 1 month) AND (Pregnant or lactating women) AND (Serum bilirubin > 5.0mg/d) AND (Serum creatinine > 1.5mg/dl) AND (West Haven grade = 3) AND (Woman patients who do not agree to the contraception from baseline to 12 month) AND (acute exacerbation of liver cirrhosis past 1 month) AND (alcohol taker Chronic) AND (anti-viral treatment past 1 month) AND (complications) AND (organ failure) AND ((SBP) OR (hepatic encephalopathy)) AND ((cardiac disease) OR (respiratory disease)) AND ((BCAA) OR (diuretics)) AND ((hepatitis B) OR (hepatitis C)))"}
{"candidate_id": "LLM03749", "doc_id": "NCT01680081_exc", "case_bucket": "or", "source_criterion": "Contraindication of CT Known allergy to iodinated contrast media or history of contrast-induced nephropathy Decreased renal function: elevated serum creatinine(>1.5mg/dl) Contraindication to beta-blockers Severe arrhythmia: arterial fibrillation or uncontrolled tachyarrhythmia, or advanced atrioventricular block (second or third degree heart block) Contraindication of MRI Claustrophobia Metallic hazards Pacemaker implant eGFR<30 ml/min Unstable or uncooperative patients Limited life expectancy due to cancer or end-stage renal or liver disease Evidence of severe symptomatic heart failure (NYHA Class III or IV) Previous myocardial infarction, coronary artery intervention, coronary artery bypass surgery, or other cardiac surgery", "candidate_expression": "((Contraindication) AND (Contraindication of CT) AND (MRI) AND (NYHA Class III or IV) AND (Unstable patients) AND (arrhythmia Severe) AND (beta-blockers) AND (heart failure severe symptomatic) AND (iodinated contrast media) AND (life expectancy Limited) AND (renal function Decreased) AND (serum creatinine elevated >1.5mg/dl) AND (uncooperative patients) AND ((advanced atrioventricular block) OR (arterial fibrillation) OR (uncontrolled tachyarrhythmia)) AND ((second degree heart block) OR (third degree heart block)) AND ((Known allergy) OR (contrast-induced nephropathy)) AND ((Claustrophobia) OR (Metallic hazards) OR (Pacemaker implant) OR (eGFR <30 ml/min)) AND ((cancer) OR (end-stage renal disease) OR (liver disease)) AND ((coronary artery bypass surgery) OR (coronary artery intervention) OR (myocardial infarction) OR (other cardiac surgery)))"}
{"candidate_id": "LLM03750", "doc_id": "NCT03211741_inc", "case_bucket": "or", "source_criterion": "Age = 18 years of either gender Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed Visual impairment predominantly due to abnormal new vessel ingrowth and/or macular edema. The presence of fluid (intraretinal, subretinal or sub-RPE) detected clinically or on the ocular coherence tomography.", "candidate_expression": "((Age = 18 years) AND (Visual impairment) AND (Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed) AND (either gender) AND (fluid) AND (ocular coherence tomography) AND ((abnormal new vessel ingrowth) OR (macular edema)) AND ((intraretinal) OR (sub-RPE) OR (subretinal)))"}
```
