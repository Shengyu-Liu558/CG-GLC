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
{"candidate_id": "LLM07376", "doc_id": "NCT00250640_inc", "case_bucket": "or", "source_criterion": "The treating physician has chosen Ventavis as a suitable long-term treatment for the patient Patient with primary pulmonary hypertension (i.e. Idiopathic Pulmonary Arterial Hypertension or Familial Pulmonary Arterial Hypertension) and classified as NYHA functional class III (NYHA = New York Heart Association) No prior treatment with Ventavis or other active treatments for primary pulmonary hypertension within 6 weeks of date of study inclusion (unless otherwise advised by Bayer Schering Pharma)", "candidate_expression": "((III) AND (NYHA functional class) AND (No) AND (Ventavis) AND (for primary pulmonary hypertension) AND (long-term) AND (primary pulmonary hypertension) AND (within 6 weeks of date of study inclusion) AND ((Familial Pulmonary Arterial Hypertension) OR (Idiopathic Pulmonary Arterial Hypertension)) AND ((treatment with Ventavis) OR (treatments)))"}
{"candidate_id": "LLM07377", "doc_id": "NCT03134196_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07378", "doc_id": "NCT01942109_exc", "case_bucket": "other", "source_criterion": "uncontrolled hypertension uncontrolled diabetes creatinine > 2,5 mg/dl potassium > 6 mg/dl acute coronary syndrome hypertrophic cardiomyopathy", "candidate_expression": "((acute coronary syndrome) AND (creatinine > 2,5 mg/dl) AND (diabetes uncontrolled) AND (hypertension uncontrolled) AND (hypertrophic cardiomyopathy) AND (potassium > 6 mg/dl))"}
{"candidate_id": "LLM07379", "doc_id": "NCT02908919_inc", "case_bucket": "or", "source_criterion": "Subjects referred to diagnostic or therapeutic colonoscopy.", "candidate_expression": "((colonoscopy) AND (diagnostic) AND (therapeutic))"}
{"candidate_id": "LLM07380", "doc_id": "NCT00639795_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 Planned thoracoscopy with low probability(by surgeon estimate) of conversion to open procedure", "candidate_expression": "((Age) AND (greater than 18) AND (low probability(by surgeon estimate) of conversion to open procedure) AND (thoracoscopy))"}
{"candidate_id": "LLM07381", "doc_id": "NCT00527826_inc", "case_bucket": "or", "source_criterion": "Subject must have a diagnosis of COPD based on the American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria. Male or female subjects, aged >=40 years. Females must be of Non Child Bearing Potential. The definition of Non Child Bearing Potential is as following: Females, regardless of their age, with functioning ovaries and who have a current documented tubal ligation or hysterectomy, or females who are post-menopausal. Have diagnosed COPD stage III or IV according to GOLD criteria: a baseline post-bronchodilator Forced Expiratory Volume, measured at 1 second (FEV1) <50% of predicted normal and a baseline post- bronchodilator FEV1/Inspiratory Vital Capacity (IVC) ratio <70%. Have experienced at least 2 moderate or severe COPD exacerbations leading to medical consultation (requiring oral corticosteroids or increasing dosage of oral corticosteroids and/or antibiotics or hospitalization) within the 12 months preceding Visit 1. Have stable COPD medication within 4 weeks prior to Visit 1 (no new medication added and no dosage changes in medication). Current or ex-smokers with a smoking history of at least 10 pack years (number of pack years = [number of cigarettes per day / 20] x number of years smoked, e.g., 20 cigarettes per day for 10 years, or 10 cigarettes per day for 20 years). Are currently managed at home (outpatients), are ambulatory and able to travel to the clinic. Subjects can be treated with all relevant COPD medication. This includes vaccines, inhaled short-acting beta-2-agonists as needed, short-acting or long-acting anticholinergics (tiotropium), systemic beta-2-agonists, theophylline, mucolytics, antioxidants, beta-1-agonists (for cardiovascular indication), non-invasive ventilation, long term oxygen therapy and can have Cor Pulmonale. A signed and dated written informed consent is obtained prior to participation. Able to comply with the requirements of the protocol and be available for study visits over 52 weeks.", "candidate_expression": "((Able to comply with the requirements of the protocol) AND (American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria) AND (COPD) AND (COPD exacerbations at least 2 within the 12 months preceding Visit 1) AND (COPD medication stable within 4 weeks prior to Visit 1) AND (FEV1/Inspiratory Vital Capacity (IVC) ratio post- bronchodilator <70%) AND (Females) AND (Forced Expiratory Volume, measured at 1 second (FEV1) post-bronchodilator <50% of predicted normal) AND (GOLD criteria stage III or IV) AND (able to travel to the clinic) AND (aged >=40 years) AND (ambulatory) AND (at home) AND (available for study visits over 52 weeks) AND (beta-1-agonists) AND (cardiovascular indication) AND (females) AND (functioning ovaries) AND (managed) AND (managed at home) AND (outpatients) AND (oxygen) AND (post-menopausal) AND (smokers) AND (smoking history 10 pack years) AND (study visits) AND (tiotropium) AND (written informed consent prior to participation) AND NOT (Child Bearing Potential) AND ((hysterectomy) OR (tubal ligation)) AND ((moderate) OR (severe)) AND ((antibiotics) OR (hospitalization) OR (oral corticosteroids) OR (oral corticosteroids increasing dosage)) AND ((Male) OR (female)) AND ((Current) OR (ex)) AND ((COPD medication) OR (antioxidants) OR (inhaled short-acting beta-2-agonists) OR (long-acting anticholinergics) OR (mucolytics) OR (short-acting) OR (systemic beta-2-agonists) OR (theophylline) OR (vaccines)) AND ((Cor Pulmonale) OR (non-invasive ventilation) OR (oxygen therapy long term)))"}
{"candidate_id": "LLM07382", "doc_id": "NCT01665417_exc", "case_bucket": "or", "source_criterion": "Prior chemotherapy Prior treatment with gefitinib, erlotinib, or other drugs that target EGFR Patients must not be receiving any other investigational agents Any evidence of interstitial lung disease", "candidate_expression": "((Patients must not be receiving any other investigational agents) AND (chemotherapy Prior) AND (interstitial lung disease) AND (treatment Prior) AND ((drugs that target EGFR) OR (erlotinib) OR (gefitinib)))"}
{"candidate_id": "LLM07383", "doc_id": "NCT01118871_exc", "case_bucket": "or", "source_criterion": "current alcohol abuse or drug dependence pregnancy active opportunistic infection or significant co-morbidities current prohibited concomitant medication a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing", "candidate_expression": "((a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing) AND (co-morbidities) AND (medication current prohibited concomitant) AND (opportunistic infection significant) AND (pregnancy) AND ((alcohol abuse) OR (drug dependence)))"}
{"candidate_id": "LLM07384", "doc_id": "NCT02816762_inc", "case_bucket": "or", "source_criterion": "Subjects aged 18 to 80 years old Overweight or obesity (BMI =25 kg/m2) Previous diagnosis of type 2 diabetes, fulfilling at least one of the following criteria: 1) current treatment with oral antidiabetic drugs and/or insulin; 2) a fasting glucose value above 126 mg/dl on at least 2 occasions; 3) blood glucose level at 2 hours after an oral glucose tolerance test is equal to or more than 200 mg/dl; or 4) a glycated hemoglobin (HbA1c) level > 6.5 % Clinical diagnosis of diabetic nephropathy, with a urinary albumin/creatinine ratio >30 mg/g and an estimated glomerular filtration rate more than 20 ml/min per 1.73 m2. Treatment with stable doses of angiotensin-converting enzyme inhibitors, angiotensin II receptor blockers or anti-aldosterone agents in the last four weeks.", "candidate_expression": "((BMI =25 kg/m2) AND (aged 18 to 80 years old) AND (diabetic nephropathy) AND (estimated glomerular filtration rate more than 20 ml/min per 1.73 m2) AND (oral glucose tolerance test) AND (type 2 diabetes Previous) AND (urinary albumin/creatinine ratio >30 mg/g) AND ((insulin) OR (oral antidiabetic drugs)) AND ((blood glucose level at 2 hours after an oral glucose tolerance test equal to or more than 200 mg/dl) OR (fasting glucose above 126 mg/dl on at least 2 occasions) OR (glycated hemoglobin (HbA1c) level > 6.5 %)) AND ((angiotensin II receptor blockers) OR (angiotensin-converting enzyme inhibitors) OR (anti-aldosterone agents)) AND ((Overweight) OR (obesity)))"}
{"candidate_id": "LLM07385", "doc_id": "NCT01993836_exc", "case_bucket": "or", "source_criterion": "Inmate of a correctional facility (i.e. prisoners). Pregnancy Documented or suspected family or personal history of malignant hyperthermia. Patient unable to receive either propofol or isoflurane due to allergy or other specific contraindication.", "candidate_expression": "((Inmate of a correctional facility) AND (Pregnancy) AND (allergy) AND (history family) AND (isoflurane) AND (malignant hyperthermia) AND (personal history) AND (prisoners) AND (propofol) AND (unable to receive))"}
{"candidate_id": "LLM07386", "doc_id": "NCT02959801_exc", "case_bucket": "or", "source_criterion": "presence of subacute or chronic DVT more than 21 days in duration, inability to lie in the prone position required for intervention, terminal systemic disease requiring palliative treatment, active bleeding (from a gastric/duodenal ulcer or the cerebrovascular system), a haemorrhagic stroke within the previous year, an impaired bleeding-clotting profile, and any haemophilic disorder, or pregnancy.", "candidate_expression": "((palliative treatment requiring) AND ((cerebrovascular system) OR (duodenal ulcer) OR (gastric ulcer)) AND ((chronic) OR (subacute)) AND ((DVT more than 21 days in duration) OR (bleeding active) OR (haemophilic disorder) OR (haemorrhagic stroke within the previous year) OR (impaired bleeding-clotting profile) OR (inability to lie in the prone position) OR (pregnancy) OR (terminal systemic disease)))"}
{"candidate_id": "LLM07387", "doc_id": "NCT03491059_inc", "case_bucket": "or", "source_criterion": "males and females greater than or equal to 18 years of age current regular user of e-cigarettes (use at least once daily for the past 30 days) with nicotine strength > 6mg/ml health medical history abstinent from any tobacco/nicotine use for 4 hours prior to imaging", "candidate_expression": "((> 6mg/ml) AND (abstinent) AND (age) AND (at least once daily) AND (e-cigarettes) AND (for 4 hours prior to imaging) AND (for the past 30 days) AND (greater than or equal to 18 years) AND (health) AND (imaging) AND (medical history) AND (nicotine strength) AND (regular) AND (user) AND ((nicotine) OR (tobacco)) AND ((females) OR (males)))"}
{"candidate_id": "LLM07388", "doc_id": "NCT02092467_inc", "case_bucket": "or", "source_criterion": "Moderate to severe rheumatoid arthritis Taking methotrexate without adequate control of symptoms Have at least one cardiovascular risk factor (eg, current smoker, high blood pressure, high cholesterol levels, diabetes mellitus, history of heart attack, family history of coronary heart disease, extra-articular RA disease)", "candidate_expression": "((Moderate to severe) AND (adequate control of symptoms) AND (at least one) AND (cardiovascular risk factor) AND (current) AND (extra-articular) AND (family history) AND (history) AND (methotrexate) AND (rheumatoid arthritis) AND (without) AND ((RA disease) OR (coronary heart disease) OR (diabetes mellitus) OR (heart attack) OR (high blood pressure) OR (high cholesterol levels) OR (smoker)))"}
{"candidate_id": "LLM07389", "doc_id": "NCT02595190_exc", "case_bucket": "or", "source_criterion": "1. Patients with lumbar common diseases(e.g., Lumbar disc, Lumbar spinal stenosis, Lumbar slippage, etc) 2. Researchers think that Patients with disease may be interference results(e.g., Spinal deformity, spine fracture, ankylosing spondylitis, spinal tuberculosis and spinal infection, spinal tumor, pelvic inflammatory disease and other disease of department of gynaecology, etc) 3. Patients with other nervous system diseases(e.g., cerebral tumor, neurinoma, trigeminal neuralgia,etc) 4. Patients with Magnetic resonance imaging contraindication ,including claustrophobic syndrome patients 5. Patients with recent (less than 3 years) use chemical drugs or have obvious psychological problems 6. In the past 2 months involved in other drugs or devices clinical trials", "candidate_expression": "((In the past 2 months involved in other drugs or devices clinical trials) AND (Lumbar disc) AND (Lumbar slippage) AND (Lumbar spinal stenosis) AND (Magnetic resonance imaging) AND (Spinal deformity) AND (ankylosing spondylitis) AND (cerebral tumor) AND (claustrophobic syndrome) AND (contraindication) AND (lumbar diseases) AND (nervous system diseases) AND (neurinoma) AND (pelvic inflammatory disease) AND (spinal infection) AND (spinal tuberculosis) AND (spinal tumor) AND (spine fracture,) AND (trigeminal neuralgia))"}
{"candidate_id": "LLM07390", "doc_id": "NCT02478346_inc", "case_bucket": "or", "source_criterion": "Adult patients (age = 18) Diagnosed by preoperative imaging modalities to have a brain tumor (including metastatic brain tumors) or vascular lesions (aneurysm, arteriovenous malformation or arteriovenous fistula) requiring surgical intervention. The patient is determined by a board certified neurosurgeon to have a tumor or vascular lesion that would take up fluorescein Patient or legally authorized representative provides written informed consent to enroll in this study", "candidate_expression": "((Adult) AND (Patient or legally authorized representative provides written informed consent to enroll in this study) AND (age = 18) AND (aneurysm) AND (arteriovenous fistula) AND (arteriovenous malformation) AND (brain tumor) AND (fluorescein) AND (imaging modalities preoperative) AND (metastatic brain tumors) AND (surgical intervention) AND (tumor) AND (vascular lesion) AND (vascular lesions))"}
{"candidate_id": "LLM07391", "doc_id": "NCT02295202_exc", "case_bucket": "other", "source_criterion": "Smokers Patients under chronic use of medications Neurological diseases Coronary artery disease Acute heart failure Chronic renal failure (GFR < 30 ml/min) Chronic obstructive pulmonary disease Mild OSA and patients with BMI over 40 kg/m2.", "candidate_expression": "((< 30 ml/min) AND (Acute heart failure) AND (BMI) AND (Chronic) AND (Coronary artery disease) AND (GFR) AND (Mild OSA) AND (Neurological diseases) AND (Smokers) AND (chronic use) AND (medications) AND (obstructive pulmonary disease) AND (over 40 kg/m2) AND (renal failure))"}
{"candidate_id": "LLM07392", "doc_id": "NCT02678728_exc", "case_bucket": "other", "source_criterion": "Unstable vital sign before surgery Severe pulmonary disease requiring consistent treatment Illiterate Pregnancy", "candidate_expression": "((Illiterate) AND (Pregnancy) AND (consistent treatment requiring) AND (pulmonary disease Severe) AND (surgery) AND (vital sign Unstable before surgery))"}
{"candidate_id": "LLM07393", "doc_id": "NCT02951520_exc", "case_bucket": "other", "source_criterion": "BMI > 30 kg.m-2, ASA physical state >II Allergy to the used local anesthetics Infection at the injection site age <18y", "candidate_expression": "((<18y) AND (> 30 kg.m-2) AND (>II) AND (ASA physical state) AND (Allergy) AND (BMI) AND (Infection) AND (age) AND (injection site) AND (local anesthetics))"}
{"candidate_id": "LLM07394", "doc_id": "NCT02650388_exc", "case_bucket": "other", "source_criterion": "Died before TAVI Not willing to participate", "candidate_expression": "((Died before TAVI) AND (Not willing to participate))"}
{"candidate_id": "LLM07395", "doc_id": "NCT00625742_inc", "case_bucket": "other", "source_criterion": "1. Are referred to the Cachexia Clinic with involuntary weight loss of >5% of their premorbid weight within the previous 6 months. 2. Are 18 years of age or older 3. Have a Karnofsky performance score of 60 or higher. 4. Can maintain oral food intake during the study 5. Can understand the study procedures and can sign an informed consent form. 6. Are not currently taking melatonin. 7. Are taking megestrol acetate and continue to lose weight despite at least 2 weeks of therapy. 8. Have a calculated creatinine clearance of >/= 60 cc/min.", "candidate_expression": "((Cachexia Clinic) AND (Karnofsky performance score 60 or higher) AND (calculated creatinine clearance >/= 60 cc/min) AND (involuntary weight loss >5% of their premorbid weight within the previous 6 months) AND (lose weight continue) AND (megestrol acetate Are taking) AND (of age 18 years or older) AND (therapy at least 2 weeks) AND NOT (melatonin currently))"}
{"candidate_id": "LLM07396", "doc_id": "NCT02270970_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07397", "doc_id": "NCT01518946_exc", "case_bucket": "or", "source_criterion": "1. The subject is a pregnant or lactating female. 2. The subject has pre-existing sustained supine hypertension greater than 180mmHg systolic and 110mmHg diastolic BP or had these measurements at the Screening Visit. Sustained is defined as persistently greater at 2 separate measurements at least 5 minutes apart with the subject supine and at rest for the 5 minutes. 3. Subjects taking concomitant medications of interest are excluded unless those medications are reviewed and discussed with the Medical Monitor or Study Physician and documented prior to enrolling the subject. If agreement is reached between the Investigator and Sponsor for the subject to continue in the study, all allowed medications should be maintained at a constant dose throughout the study. 4. The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant 5. The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406). 6. Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures. 7. The subject has a concurrent chronic or acute illness, disability, or other condition (including significant unexpected laboratory or electrocardiogram [ECG] findings) that might confound the results of the tests and/or measurements administered in this study, or that might have increased the risk to the subject. 8. Known or suspected intolerance or hypersensitivity to the investigational product(s), closely-related compounds, or any of the stated ingredients. 9. Prior enrollment failure or randomization in this study. 10. History of alcohol abuse or other substance abuse within the last year.", "candidate_expression": "((BP greater than 180mmHg systolic 110mmHg diastolic at the Screening Visit) AND (Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures.) AND (The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant) AND (The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406).) AND (acute illness) AND (alcohol abuse) AND (chronic illness) AND (disability) AND (electrocardiogram [ECG]) AND (electrocardiogram [ECG] findings) AND (enrollment failure) AND (female) AND (laboratory findings) AND (lactating) AND (measurements 2 separate at least 5 minutes apart persistently greater) AND (medications of interest concomitant) AND (other condition) AND (pregnant) AND (substance abuse) AND (supine hypertension pre-existing sustained))"}
{"candidate_id": "LLM07398", "doc_id": "NCT02046395_exc", "case_bucket": "or", "source_criterion": "Pregnancy Patients with chronic kidney disease stage with eGFR < 30 ml/min (CKD stage IV and V) Nephrotic range proteinuria (urinary protein > 3.5 gm/day) History or renal transplantation History of multiple myeloma Known history of hypersensitivity reaction or intolerability to Ace Inh or ARB.", "candidate_expression": "((< 30 ml/min) AND (> 3.5 gm/day) AND (CKD) AND (History) AND (Nephrotic range) AND (Pregnancy) AND (chronic kidney disease) AND (eGFR) AND (history) AND (multiple myeloma) AND (proteinuria) AND (renal transplantation) AND (urinary protein) AND ((hypersensitivity reaction) OR (intolerability)) AND ((ARB) OR (Ace Inh)) AND ((stage IV) OR (stage V)))"}
{"candidate_id": "LLM07399", "doc_id": "NCT03104816_exc", "case_bucket": "or", "source_criterion": "Patients requiring surgery for neoplastic processes Allergy to acetaminophen Liver dysfunction and elevated Liver Function Tests (LFTs) Alcohol or drug dependency Mental retardation Less than 50 kg of weight regnant women Patients requiring long-acting opioid pain management (including fentanyl patch, oxycontin, etc) for over 3 weeks immediately prior to surgery", "candidate_expression": "((Allergy) AND (LFTs) AND (Liver Function Tests elevated) AND (Liver dysfunction) AND (Mental retardation) AND (acetaminophen) AND (long-acting opioid requiring for over 3 weeks immediately prior to surgery) AND (neoplastic processes) AND (regnant) AND (surgery) AND (weight Less than 50 kg) AND (women) AND ((Alcohol dependency) OR (drug dependency)) AND ((fentanyl patch) OR (oxycontin)))"}
{"candidate_id": "LLM07400", "doc_id": "NCT02942303_exc", "case_bucket": "or", "source_criterion": "Patients with previous periorbital/forehead surgery Patients who plucked the upper eyebrow margin Patients with eyebrow tatoos Patients with upper face botulinum toxin injection in the past 12 months Patients with resorbable upper face fillers injection in the past 12 months Patients with previous permanent upper face fillers injection Pregnant patients Lactating patients Patients with preexisting neuromuscular conditions (myasthenia gravis, Eaton Lambert syndrome) Patients using medication that could potentiate the effect of botulinum (ex: aminoglycoside antibiotics) Patients with sensitivity to botulinum toxin or human albumin", "candidate_expression": "((Eaton Lambert syndrome) AND (Lactating) AND (Pregnant) AND (aminoglycoside antibiotics) AND (botulinum) AND (botulinum toxin) AND (botulinum toxin injection) AND (eyebrow tatoos) AND (forehead surgery) AND (human albumin) AND (in the past 12 months) AND (medication) AND (myasthenia gravis) AND (neuromuscular conditions) AND (periorbital surgery) AND (permanent fillers injection) AND (plucked the upper eyebrow margin) AND (potentiate the effect) AND (resorbable fillers injection) AND (sensitivity) AND (upper face))"}
```
