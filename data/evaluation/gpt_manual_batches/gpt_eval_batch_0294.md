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
{"candidate_id": "LLM07326", "doc_id": "NCT00527826_inc", "case_bucket": "or", "source_criterion": "Subject must have a diagnosis of COPD based on the American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria. Male or female subjects, aged >=40 years. Females must be of Non Child Bearing Potential. The definition of Non Child Bearing Potential is as following: Females, regardless of their age, with functioning ovaries and who have a current documented tubal ligation or hysterectomy, or females who are post-menopausal. Have diagnosed COPD stage III or IV according to GOLD criteria: a baseline post-bronchodilator Forced Expiratory Volume, measured at 1 second (FEV1) <50% of predicted normal and a baseline post- bronchodilator FEV1/Inspiratory Vital Capacity (IVC) ratio <70%. Have experienced at least 2 moderate or severe COPD exacerbations leading to medical consultation (requiring oral corticosteroids or increasing dosage of oral corticosteroids and/or antibiotics or hospitalization) within the 12 months preceding Visit 1. Have stable COPD medication within 4 weeks prior to Visit 1 (no new medication added and no dosage changes in medication). Current or ex-smokers with a smoking history of at least 10 pack years (number of pack years = [number of cigarettes per day / 20] x number of years smoked, e.g., 20 cigarettes per day for 10 years, or 10 cigarettes per day for 20 years). Are currently managed at home (outpatients), are ambulatory and able to travel to the clinic. Subjects can be treated with all relevant COPD medication. This includes vaccines, inhaled short-acting beta-2-agonists as needed, short-acting or long-acting anticholinergics (tiotropium), systemic beta-2-agonists, theophylline, mucolytics, antioxidants, beta-1-agonists (for cardiovascular indication), non-invasive ventilation, long term oxygen therapy and can have Cor Pulmonale. A signed and dated written informed consent is obtained prior to participation. Able to comply with the requirements of the protocol and be available for study visits over 52 weeks.", "candidate_expression": "((10 pack years) AND (<50% of predicted normal) AND (<70%) AND (>=40 years) AND (Able to comply with the requirements of the protocol) AND (American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria) AND (COPD) AND (COPD exacerbations) AND (COPD medication) AND (Child Bearing Potential) AND (Cor Pulmonale) AND (Current) AND (FEV1/Inspiratory Vital Capacity (IVC) ratio) AND (Females) AND (Forced Expiratory Volume, measured at 1 second (FEV1)) AND (GOLD criteria) AND (Male) AND (Non) AND (able to travel to the clinic) AND (aged) AND (ambulatory) AND (antibiotics) AND (antioxidants) AND (at home) AND (at least 2) AND (available for study visits) AND (beta-1-agonists) AND (cardiovascular indication) AND (ex) AND (female) AND (females) AND (functioning ovaries) AND (hospitalization) AND (hysterectomy) AND (increasing dosage) AND (inhaled short-acting beta-2-agonists) AND (long term) AND (long-acting anticholinergics) AND (managed) AND (managed at home) AND (moderate) AND (mucolytics) AND (non-invasive ventilation) AND (oral corticosteroids) AND (outpatients) AND (over 52 weeks) AND (oxygen) AND (oxygen therapy) AND (post- bronchodilator) AND (post-bronchodilator) AND (post-menopausal) AND (prior to participation) AND (severe) AND (short-acting) AND (smokers) AND (smoking history) AND (stable) AND (stage III or IV) AND (study visits) AND (systemic beta-2-agonists) AND (theophylline) AND (tiotropium) AND (tubal ligation) AND (vaccines) AND (within 4 weeks prior to Visit 1) AND (within the 12 months preceding Visit 1) AND (written informed consent))"}
{"candidate_id": "LLM07327", "doc_id": "NCT03471117_inc", "case_bucket": "or", "source_criterion": "CKD patients classified as Stage 3 and 4 of National Kidney Foundation Classification with estimated glomerular filtration rate (GFR) between 15 and 59 mL/min/1.73 m2 according to the Modification of Diet in Renal Disease (MDRD) formula based on serum creatinine, age, gender, and race. Men and women 35 to 70 years of age", "candidate_expression": "((CKD Stage 3 Stage 4) AND (Men) AND (National Kidney Foundation Classification) AND (age 35 to 70 years) AND (estimated glomerular filtration rate (GFR) between 15 and 59 mL/min/1.73 m2 Modification of Diet in Renal Disease (MDRD) formula) AND (women))"}
{"candidate_id": "LLM07328", "doc_id": "NCT02270970_inc", "case_bucket": "or", "source_criterion": "Patients who meet 1987 ACR criteria for SLE with 1996 modifications SLEDAI >/= 6 at screening visit Positive ANA OR anti-dsDNA within one year of screening In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease", "candidate_expression": "((1987 ACR criteria with 1996 modifications) AND (In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease) AND (SLE) AND (SLEDAI >/= 6 at screening visit) AND ((ANA Positive within one year of screening) OR (anti-dsDNA Positive within one year of screening)))"}
{"candidate_id": "LLM07329", "doc_id": "NCT02563535_inc", "case_bucket": "other", "source_criterion": "age>18 years critical limb ischemia (Rutherford class 4-6) angiographic stenosis>50% or occlusion of at least one tibial vessel of at least 40mm for which an interventional treatment is scheduled", "candidate_expression": "((Rutherford class 4-6) AND (age >18 years) AND (angiographic stenosis >50%) AND (interventional treatment scheduled) AND (limb ischemia critical) AND (occlusion tibial vessel))"}
{"candidate_id": "LLM07330", "doc_id": "NCT03541980_exc", "case_bucket": "or", "source_criterion": "Patient with fever (38C or 100.4F) Patient less than age 4 years Patient greater than age 16 years Patient with hypersensitivity/allergy to either morphine, NSAIDs, or acetaminophen Patient received acetaminophen within the past 4 hours Patient with known liver disease or renal disease Patient not requiring IV morphine (pain score 5/10 or less) Patient enrolled in the study within the past 72 hours", "candidate_expression": "((5/10 or less) AND (IV morphine) AND (acetaminophen) AND (age) AND (enrolled in the study) AND (fever) AND (greater than 16 years) AND (less than 4 years) AND (not) AND (pain score) AND (requiring) AND (within the past 4 hours) AND (within the past 72 hours) AND ((allergy) OR (hypersensitivity)) AND ((NSAIDs) OR (acetaminophen) OR (morphine)) AND ((liver disease) OR (renal disease)) AND ((100.4F) OR (38C)))"}
{"candidate_id": "LLM07331", "doc_id": "NCT03354572_exc", "case_bucket": "or", "source_criterion": "Pregnancy or lactating Allergy to NAC History of chronic pain Use of opioids or neuropathic analgesics Use of NAC prior to trial (< 1 month of planned surgery) Alcoholism Diabetes Mellitus (insulin therapy) Asthma or Chronic Obstructive pulmonary Disease Known renal function disorders (MDRD <ô0) Known liver failure (bilirubin >1.Sx upper limit of normal) No written lC by patient", "candidate_expression": "((< 1 month) AND (<ô0) AND (>1.Sx upper limit of normal) AND (Alcoholism) AND (Allergy) AND (Asthma) AND (Chronic Obstructive pulmonary Disease) AND (Diabetes Mellitus) AND (History) AND (MDRD) AND (NAC) AND (No written lC by patient) AND (Pregnancy) AND (bilirubin) AND (chronic pain) AND (insulin) AND (lactating) AND (liver failure) AND (neuropathic analgesics) AND (opioids) AND (planned) AND (prior to trial) AND (renal function disorders) AND (surgery) AND (trial))"}
{"candidate_id": "LLM07332", "doc_id": "NCT03140488_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy = 37 weeks gestation Patient presented for induction of labor who is determined to be a candidate for oxytocin Cephalic presentation Reassuring fetal health assessment (no abnormal findings in fetal assessment, see below) Meeting one of the following BMI category:", "candidate_expression": "((Cephalic presentation) AND (Singleton pregnancy) AND (candidate for oxytocin) AND (fetal assessment) AND (fetal health assessment Reassuring) AND (gestation = 37 weeks) AND (induction of labor presented for) AND (oxytocin) AND NOT (abnormal findings))"}
{"candidate_id": "LLM07333", "doc_id": "NCT02830360_inc", "case_bucket": "or", "source_criterion": "Prior Myocardial Infarction and Sustained monomorphic VT documented on 12-lead ECG or rhythm strip terminated by pharmacologic means or DC cardioversion =3 episodes of VT treated with antitachycardia pacing (ATP), at least one of which was symptomatic = 5 episodes of VT treated with antitachycardia pacing (ATP) regardless of symptoms =1 appropriate ICD shocks, =3 VT episodes within 24 hours", "candidate_expression": "((12-lead ECG) AND (3 episodes) AND (5 episodes) AND (=1) AND (ATP) AND (DC cardioversion) AND (ICD shocks) AND (Myocardial Infarction) AND (Sustained) AND (VT) AND (antitachycardia pacing) AND (at least one) AND (monomorphic VT) AND (pharmacologic means) AND (rhythm strip) AND (symptomatic) AND (within 24 hours))"}
{"candidate_id": "LLM07334", "doc_id": "NCT02833116_exc", "case_bucket": "or", "source_criterion": "Patients with high intracranial pressure. Patients with Multiple Sclerosis. Patients with Guillain-Barré syndrome radiculopathy of vascular origin. Patients with previous lumbar surgery. Patients pregnant or lactating. Patients with allergy or intolerance to any of the drugs used. Patients with severe cognitive impairment. Patients with intrathecal injectio radiculalgia. Patients with poorly controlled major psychiatric pathology. Patients with type I diabetes or poorly controlled type II diabetes (Hb1Ac>8.5). Patients with glaucoma. Patients with caudal equine syndrome. Patients with pre-treatment with steroid injections/or local anesthetics. Patients with central canal stenosis. patients with chronic treatment with oral corticosteroids without stabilized pattern.", "candidate_expression": "((Guillain-Barré syndrome radiculopathy vascular) AND (Hb1Ac >8.5) AND (Multiple Sclerosis) AND (Patients pregnant or lactating) AND (allergy) AND (caudal equine syndrome) AND (central canal stenosis) AND (cognitive impairment severe) AND (drugs) AND (glaucoma) AND (intolerance) AND (intracranial pressure high) AND (intrathecal injectio radiculalgia) AND (local anesthetics) AND (lumbar surgery.) AND (oral corticosteroids) AND (psychiatric pathology poorly controlled major) AND (steroid injections) AND (type I diabetes) AND (type II diabetes poorly controlled))"}
{"candidate_id": "LLM07335", "doc_id": "NCT03064867_inc", "case_bucket": "or", "source_criterion": "Histological confirmation of relapsed/refractory diffuse large B-cell lymphoma after prior rituximab and anthracycline-containing systemic treatment regimen such as R-CHOP (rituximab, cyclophosphamide, doxorubicin, vincristine, and prednisone), R-EPOCH (rituximab, etoposide phosphate, prednisone, vincristine sulfate, cyclophosphamide, doxorubicin hydrochloride), R-HyperCVAD (rituximab, cyclophosphamide, vincristine sulfate, doxorubicin hydrochloride, dexamethasone) etc. Subjects must have received no more than 2 prior systemic therapies for lymphoma. Prior therapy with systemic rituximab monotherapy or conventional chemotherapy (i.e. bendamustine, CVP (Cyclophosphamide, Vincristine Sulfate, Prednisone) or other) ± rituximab for indolent non-Hodgkin's lymphoma (NHL) ± maintenance/extended-use rituximab will count as 1 line of systemic therapy. Eastern Cooperative Oncology Group (ECOG) Performance status ≤ 2 Subjects must have normal organ and marrow function as defined below: Hemoglobin ≥ 8.0 g/dl Absolute neutrophil count ≥ 1,000/mcL Platelet count ≥ 75,000/mcL Total bilirubin ≤ 1.5 X the upper limit of normal (ULN) unless a known history of impaired bilirubin conjugation such as Gilbert's, for whom the maximum will be 2.5 ULN. Aspartate transaminase (AST) (SGOT) ≤ 2.5 X institutional ULN Alanine transaminase (ALT) (SGPT) ≤ 2.5 X institutional ULN International normalized ratio (INR) > 1.5 ×ULN Patients must have a calculated serum creatinine clearance > 50 mL/min using Cockcroft-Gault calculation or based on 24-hour urine collection performed within 7 days prior to treatment. Specific guidelines will be followed regarding inclusion of relapsed/refractory DLBCL based on Hepatitis B serological testing as follow: HBsAg negative, HBcAb negative, HBsAb positive patients are eligible. Patients who test positive for HBsAg are ineligible Patients with HBsAg negative, but HBcAb positive (regardless of HBsAb status) should have a HBV DNA testing performed and protocol eligibility determined as follow: If HBV DNA is positive, the subject is ineligible. If HBV DNA is negative, the subject may be included but must undergo HBV DNA PCR testing monthly x 3 months beginning from the start of treatment Subjects must have the ability to understand and the willingness to sign a written informed consent document. For women of childbearing potential: agreement to remain abstinent (refrain from heterosexual intercourse) or use a contraceptive method with a failure rate of < 1% per year during the treatment period and for at least 30 days after the last dose of venetoclax or 18 months after the last dose of rituximab, whichever is longer. A woman is considered to be of childbearing potential if she is postmenarcheal, has not reached a postmenopausal state (< 12 continuous months of amenorrhea with no identified cause other than menopause), and has not undergone surgical sterilization (removal of ovaries and/or uterus). For men: agreement to remain abstinent (refrain from heterosexual intercourse) or use contraceptive measures, and agreement to refrain from donating sperm, as defined below: With female partners of childbearing potential, men must remain abstinent or use a condom plus an additional contraceptive method that together result in a failure rate of < 1% per year during the treatment period and for at least 6 months after the last dose of rituximab. Men must refrain from donating sperm during this same period. With pregnant female partners, men must remain abstinent or use a condom during the treatment period and for at least 6 months after the last dose of rituximab to avoid exposing the embryo.", "candidate_expression": "((Absolute neutrophil count ≥ 1,000/mcL) AND (Alanine transaminase (ALT) (SGPT) ≤ 2.5 X institutional ULN) AND (Aspartate transaminase (AST) (SGOT) ≤ 2.5 X institutional ULN) AND (B-cell lymphoma diffuse large) AND (Cyclophosphamide) AND (Eastern Cooperative Oncology Group (ECOG) Performance status ≤ 2) AND (For men: agreement to remain abstinent (refrain from heterosexual intercourse) or use contraceptive measures, and agreement to refrain from donating sperm, as defined below) AND (For women of childbearing potential: agreement to remain abstinent (refrain from heterosexual intercourse) or use a contraceptive method with a failure rate of < 1% per year during the treatment period and for at least 30 days after the last dose of venetoclax or 18 months after the last dose of rituximab, whichever is longer.) AND (Gilbert's) AND (HBV DNA negative) AND (HBV DNA positive) AND (HBV DNA testing) AND (HBcAb negative) AND (HBcAb positive) AND (HBsAb positive) AND (HBsAg negative) AND (HBsAg positive) AND (Hemoglobin ≥ 8.0 g/dl) AND (Histological confirmation after) AND (International normalized ratio (INR) > 1.5 ×ULN) AND (Platelet count ≥ 75,000/mcL) AND (Prednisone) AND (R-CHOP) AND (R-EPOCH) AND (R-HyperCVAD) AND (Total bilirubin) AND (Vincristine Sulfate) AND (With female partners of childbearing potential, men must remain abstinent or use a condom plus an additional contraceptive method that together result in a failure rate of < 1% per year during the treatment period and for at least 6 months after the last dose of rituximab.) AND (anthracycline) AND (cyclophosphamide) AND (dexamethasone) AND (doxorubicin) AND (doxorubicin hydrochloride) AND (etoposide phosphate) AND (impaired bilirubin conjugation) AND (non-Hodgkin's lymphoma (NHL) indolent) AND (prednisone) AND (rituximab) AND (rituximab and anthracycline-containing systemic treatment regimen) AND (serum creatinine clearance > 50 mL/min within 7 days prior) AND (systemic therapies for lymphoma no more than 2 prior Prior) AND (vincristine) AND (vincristine sulfate) AND ((conventional chemotherapy) OR (systemic monotherapy)) AND ((CVP) OR (bendamustine)) AND ((extended-use) OR (maintenance)) AND ((normal marrow function) OR (normal organ function)) AND ((maximum 2.5 ULN) OR (≤ 1.5 X the upper limit of normal (ULN))) AND ((24-hour urine collection) OR (Cockcroft-Gault calculation)))"}
{"candidate_id": "LLM07336", "doc_id": "NCT01807897_inc", "case_bucket": "or", "source_criterion": "Veteran receiving care within the Veterans Health Administration healthcare system Age 18 years Physician diagnosis of chronic heart failure, American Heart Association Stage C-D LVEF <45% No change in active cardiac medications for 4 weeks prior to randomization Ability to provide informed consent Moderate to severe central or mixed central and obstructive sleep apnea, defined as an apnea-hypopnea index (AHI) 15 events per hour, with a central AHI >5 events/hour", "candidate_expression": "((AHI) AND (Ability to provide informed consent) AND (Age 18 years) AND (American Heart Association Stage C-D) AND (LVEF <45%) AND (Veteran) AND (Veterans Health Administration healthcare system) AND (apnea-hypopnea index 15 events per hour,) AND (cardiac medications change for 4 weeks prior to randomization) AND (central AHI >5 events/hour) AND (central sleep apnea Moderate severe) AND (chronic heart failure) AND (mixed central sleep apnea) AND (obstructive sleep apnea))"}
{"candidate_id": "LLM07337", "doc_id": "NCT01774019_exc", "case_bucket": "or", "source_criterion": "Biliary strictures caused by confirmed benign tumors Biliary strictures caused by malignancies other than pancreatic cancer, distal CBD cholangiocarcinoma and other periampullary cancers Surgically altered biliary tract anatomy, not including prior cholecystectomy Neoadjuvant chemotherapy for current malignancy Palliative indication due to reasons other than surgical candidate status Previous biliary drainage by ERCP/PTC Patients for whom endoscopic techniques are contraindicated Participation in another investigational trial within 90 days Pregnancy", "candidate_expression": "((Biliary strictures) AND (Neoadjuvant chemotherapy) AND (Pregnancy) AND (Previous) AND (Surgically altered biliary tract anatomy) AND (benign tumors) AND (biliary drainage by ERCP/PTC) AND (cholecystectomy) AND (confirmed) AND (contraindicated) AND (distal CBD cholangiocarcinoma) AND (endoscopic techniques) AND (malignancies) AND (malignancy) AND (not) AND (other periampullary cancers) AND (other than) AND (pancreatic cancer) AND (prior))"}
{"candidate_id": "LLM07338", "doc_id": "NCT02904785_exc", "case_bucket": "or", "source_criterion": "History of spinal cord stenosis or clinical symptoms of lumbar radiculopathy; History or onset neurological diseases; Generalized pain or fibromyalgia; Inability to walk; History of knee surgery in the target knee; Secondary causes of osteoarthritis; Use of statins and quinolones in the previous year; Uncontrolled and ongoing psychiatric diseases; Invasive knee treatments with hyaluronic acid infusion, corticosteroids and anaesthetics, in the target knee, up to 6 months previous to study inclusion.", "candidate_expression": "((Inability to walk) AND (Invasive knee treatments) AND (Secondary causes) AND (anaesthetics) AND (corticosteroids) AND (hyaluronic acid) AND (hyaluronic acid infusion) AND (knee surgery History target knee) AND (lumbar radiculopathy) AND (neurological diseases) AND (osteoarthritis) AND (psychiatric diseases Uncontrolled ongoing) AND (quinolones in the previous year) AND (statins in the previous year) AND ((clinical symptoms) OR (spinal cord stenosis History)) AND ((History) OR (onset)) AND ((Generalized pain) OR (fibromyalgia)))"}
{"candidate_id": "LLM07339", "doc_id": "NCT01997580_inc", "case_bucket": "or", "source_criterion": "DSM-IV-TR major depressive disorder aged between 20 and 80 durg-naive or drug-free", "candidate_expression": "((aged between 20 and 80) AND (major depressive disorder DSM-IV-TR) AND (NOT (durg) OR NOT (drug)))"}
{"candidate_id": "LLM07340", "doc_id": "NCT03140423_inc", "case_bucket": "other", "source_criterion": "Inclusion criteria includes all U.S. HCA hospitals with an adult ICU; Note: Unit of randomization is the hospital, but the participants are hospital adult ICUs All patients within adult ICUs are included, including rare patients <18 years and >=12 years.", "candidate_expression": "((HCA hospitals) AND (U.S.) AND (adult) AND (adult ICU) AND (adult ICUs) AND (rare patients) AND (year <18 years and >=12 years))"}
{"candidate_id": "LLM07341", "doc_id": "NCT03637946_exc", "case_bucket": "or", "source_criterion": "With severe systemic alteration; In the use of antibiotics and anti-inflammatories in the last three months; With periodontium with periodontal parameters different from those established in the inclusion criteria. Individuals with clinical signs of parafunctional habits; Smoking; Individuals who have performed other restorations in the last 12 months; Pregnant women and infants; Periodontal sites that presented bleeding during crevicular fluid collection or sites that prevent proper collection of clinical parameters.", "candidate_expression": "((Pregnant) AND (Smoking) AND (clinical signs of parafunctional habits) AND (in the last 12 months) AND (in the last three months) AND (infants) AND (other restorations) AND (severe) AND (systemic alteration) AND (women) AND ((anti-inflammatories) OR (antibiotics)))"}
{"candidate_id": "LLM07342", "doc_id": "NCT02366819_exc", "case_bucket": "or", "source_criterion": "Previous or concurrent malignancy, except for adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, or any other cancer for which the patient has been previously treated and the lifetime recurrence risk is less than 30% Inflammatory bowel disease that is uncontrolled or on active treatment (Crohn's disease, ulcerative colitis) Diarrhea, grade 1 or greater by the National Cancer Institute Common Terminology Criteria for Adverse Events (NCI-CTCAE, version [v] 4.0) Neuropathy, grade 2 or greater by NCI-CTCAE, v 4.0 Serious underlying medical or psychiatric illnesses that would, in the opinion of the treating physician, substantially increase the risk for complications related to treatment Active uncontrolled bleeding Pregnancy or breastfeeding Major surgery within 4 weeks Patients with any polymorphism in UGT1A1 other than *1 or *28 (e.g, *6) will be allowed and treated as in the *28/*28 dosing group", "candidate_expression": "((Crohn's disease) AND (Diarrhea) AND (Inflammatory bowel disease uncontrolled) AND (Major surgery within 4 weeks) AND (NCI-CTCAE, v 4.0 grade 2 or greater) AND (NCI-CTCAE, version [v] 4.0) AND (National Cancer Institute Common Terminology Criteria for Adverse Events grade 1 or greater) AND (Neuropathy) AND (Pregnancy or breastfeeding) AND (basal cell skin cancer) AND (bleeding Active uncontrolled) AND (cervical cancer in situ) AND (malignancy Previous concurrent) AND (squamous cell skin cancer) AND (treatment) AND (ulcerative colitis))"}
{"candidate_id": "LLM07343", "doc_id": "NCT03477851_inc", "case_bucket": "other", "source_criterion": "Patients with foot fracture scheduled for surgical repair in spinal anesthesia Informed consent", "candidate_expression": "((Informed consent) AND (foot fracture) AND (spinal anesthesia) AND (surgical repair scheduled for))"}
{"candidate_id": "LLM07344", "doc_id": "NCT03467750_exc", "case_bucket": "other", "source_criterion": "Known coagulation defect Patients on longstanding NSAID therapy Known renal impairment Patients may also be excluded at the discretion of the investigator", "candidate_expression": "((NSAID therapy) AND (coagulation defect) AND (longstanding) AND (renal impairment))"}
{"candidate_id": "LLM07345", "doc_id": "NCT02804646_inc", "case_bucket": "or", "source_criterion": "1) histologically confirmed (patients not receiving a single sputum cytology diagnosis) non-small cell lung cancer patients,with wild-type EGFR and ALK-negative; 2) According to IASLC2009 new TNM staging of lung cancer stage <U+2162>B or <U+2163>, previously untreated or relapsed after 1 year of lung cancer resection; 3) have at least one evaluable lesions,according to version 1.1 of the standard in accordance with a judgment RECIST(longest diameter on a spiral CT at least 10mm,on a regular CT longest diameter at least 20mm); 4) Male or female, aged 18 to 75 years; 5) ECOG PS 0 or 1; 6) expected survival at least 3 months; 7) adequate hematological function: absolute neutrophil count (ANC) at least 2×10^9/L and platelet count at least 100×10^9/L and hemoglobin at least 9 g/dL; 8) adequate liver function: total bilirubin less than upper limit of normal (ULN); AST and ALT less than 2.5 times upper limit of normal (ULN); alkaline phosphatase less than 5 times the upper limit of normal (ULN); 9) adequate renal function: serum creatinine less than upper limit of normal (ULN) or calculated creatinine clearance at least 60 mL/min; 10) ECG is normal, there is no non-healing wounds on the body; 11) had not received previous treatment anticancer drugs, or had only received for previous non-metastatic tumors adjuvant or neoadjuvant chemotherapy, but when you start to study treatment has ended more than 6 months; 12) have conducted previous surgery patients required to study treatment was started more than four weeks, and the patient had recovered; 13) have an intact uterus in women prior to enrollment in the study must have a negative pregnancy test result (unless it is already 24 months of amenorrhea) within 28 days. If the pregnancy test from the first administration more than seven days, urine pregnancy test is required for authentication (less than 7 days before the first dose); 14) previous to biological agents, particularly E.coli genetically engineered products without serious allergic reactions; 15) signed informed consent.", "candidate_expression": "((0 or 1) AND (18 to 75 years) AND (ALK-negative) AND (ALT) AND (AST) AND (ECG) AND (ECOG PS) AND (IASLC2009 new TNM staging) AND (Male) AND (absolute neutrophil count (ANC)) AND (adequate hematological function) AND (adequate liver function) AND (adequate renal function) AND (adjuvant) AND (after 1 year of lung cancer resection) AND (aged) AND (alkaline phosphatase) AND (anticancer drugs) AND (at least 100×10^9/L) AND (at least 10mm) AND (at least 20mm) AND (at least 2×10^9/L) AND (at least 3 months) AND (at least 60 mL/min) AND (at least 9 g/dL) AND (at least one) AND (calculated creatinine clearance) AND (chemotherapy) AND (ended more than 6 months) AND (evaluable lesions) AND (expected survival) AND (female) AND (have an intact uterus in women prior to enrollment in the study must have a negative pregnancy test result (unless it is already 24 months of amenorrhea) within 28 days. If the pregnancy test from the first administration more than seven days, urine pregnancy test is required for authentication (less than 7 days before the first dose);) AND (hemoglobin) AND (histologically confirmed) AND (less than 2.5 times upper limit of normal (ULN)) AND (less than 5 times the upper limit of normal (ULN)) AND (less than upper limit of normal (ULN)) AND (longest diameter) AND (lung cancer) AND (lung cancer resection) AND (neoadjuvant) AND (no) AND (non-healing wounds on the body) AND (non-metastatic tumors) AND (non-small cell lung cancer) AND (normal) AND (not received) AND (platelet count) AND (previous) AND (regular CT) AND (relapsed) AND (serum creatinine) AND (spiral CT) AND (stage <U+2162>B or <U+2163>) AND (total bilirubin) AND (untreated) AND (wild-type EGFR))"}
{"candidate_id": "LLM07346", "doc_id": "NCT02314559_inc", "case_bucket": "other", "source_criterion": "All patients subjected to deep sedation in ambulant care, having a colonoscopy ASA 1-3", "candidate_expression": "((ASA 1-3) AND (ambulant) AND (colonoscopy) AND (deep sedation))"}
{"candidate_id": "LLM07347", "doc_id": "NCT02755701_exc", "case_bucket": "or", "source_criterion": "Child-Pugh score > 12 Having been diagnosed as HCC within the past 5 years Serum creatinine > 1.5mg/dl Serum bilirubin > 5.0mg/dl Presence of such complications as SBP, or hepatic encephalopathy(West Haven grade = 3) Patients who experienced organ failure by acute exacerbation of liver cirrhosis within the past 1 month Presence of serious cardiac or respiratory disease Contraindicated to either diuretics or BCAA Having commenced anti-viral treatment against hepatitis C, B within the past 1 month Pregnant or lactating women Chronic alcohol taker Woman patients who do not agree to the contraception from baseline to 12 month Unsuitable patients judged by investigator Patients participating in another clinical trial within 1 month", "candidate_expression": "((= 3) AND (> 1.5mg/dl) AND (> 12) AND (> 5.0mg/d) AND (Child-Pugh score) AND (Chronic) AND (Contraindicated) AND (HCC) AND (Patients participating in another clinical trial within 1 month) AND (Pregnant or lactating women) AND (Serum bilirubin) AND (Serum creatinine) AND (West Haven grade) AND (Woman patients who do not agree to the contraception from baseline to 12 month) AND (acute exacerbation of liver cirrhosis) AND (alcohol taker) AND (anti-viral treatment) AND (complications) AND (organ failure) AND (past 1 month) AND (past 5 years) AND (serious) AND ((SBP) OR (hepatic encephalopathy)) AND ((cardiac disease) OR (respiratory disease)) AND ((BCAA) OR (diuretics)) AND ((hepatitis B) OR (hepatitis C)))"}
{"candidate_id": "LLM07348", "doc_id": "NCT02531971_inc", "case_bucket": "or", "source_criterion": "Men or non-pregnant women of any ethnic background between the age of 18 and 45 years old Subjects must be non-smokers (must have refrained from the use of nicotine-containing substances, including tobacco products (e.g. cigarettes, cigars, chewing tobacco, gum, patch or electronic cigarettes) over the previous 2 months and are not currently using tobacco products Provide written informed consent before initiation of any study procedures Available for follow-up for the planned duration of the study Able to communicate well with the investigators Able to adhere to the study protocol schedule, study restrictions and examination schedule Subjects who are within their ideal body weight (BMI between >17 and =28 kg/m2) Subjects deemed to be healthy as judged by the Medically Accountable Investigator (MAI) and determined by medical history, physical examination and medication history Subjects have no history of the following: ongoing acute or intermittent pain, postoperative pain, respiratory compromise, acute or severe asthma, or constipation (less than 1 bowel movement every 2 days) Negative urine drug screening test at the time of screening Have normal screening laboratories for white blood cells (WBC), hemoglobin (Hgb), platelets, sodium, potassium, chloride, bicarbonate, blood urea nitrogen (BUN), creatinine, ALT (liver function), AST (liver function) and bilirubin Have normal screening laboratories for urine protein and urine glucose Female subjects must be of non-childbearing potential (as defined as surgically sterile [i.e. history of hysterectomy or tubal ligation] or postmenopausal for more than 1 year [no bleeding for 12 consecutive months], or if of childbearing potential must be non-pregnant at the time of enrollment and on the morning of the first day of each study session, and must agree to use hormonal or barrier birth control such as implants, injectables, combined oral contraceptives, some intrauterine devices (IUDs), sexual abstinence or a vasectomized parter Agrees not to participate in another clinical study/trial during the study period or to participate in an investigational drug study for at least one month after last study session Agrees not to donate blood to a blood bank throughout participation in the study and for at least 3 months after last study day Have a normal ECG; must not have the following to be acceptable: pathologic Q wave abnormalities, significant ST-T wave changes, left ventricular hypertrophy, right bundle branch block, left bundle branch block. (sinus rhythm is between 55-100 beats per minute) Temperature 35-37.9°C (95-100.3°F) Systolic blood pressure 90-140 mmHg Diastolic blood pressure 60-90 mmHg Heart rate 55-100 beats per minute Respiration rate 12-18 breaths per minute", "candidate_expression": "((ALT) AND (AST) AND (Able to adhere to the study protocol schedule, study restrictions and examination schedule) AND (Agrees not to participate in another clinical study/trial during the study period or to participate in an investigational drug study for at least one month after last study session) AND (Available for follow-up for the planned duration of the study) AND (BMI between >17 and =28 kg/m2) AND (BUN) AND (Diastolic blood pressure 60-90 mmHg) AND (ECG normal) AND (Female subjects must be of non-childbearing potential (as defined as surgically sterile [i.e. history of hysterectomy or tubal ligation] or postmenopausal for more than 1 year [no bleeding for 12 consecutive months], or if of childbearing potential must be non-pregnant at the time of enrollment and on the morning of the first day of each study session, and must agree to use hormonal or barrier birth control such as implants, injectables, combined oral contraceptives, some intrauterine devices (IUDs), sexual abstinence or a vasectomized parte) AND (Heart rate 55-100 beats per minute) AND (Hgb) AND (Provide written informed consent before initiation of any study procedures) AND (Respiration rate 12-18 breaths per minute) AND (ST-T wave changes) AND (Systolic blood pressure 90-140 mmHg) AND (Temperature 35-37.9°C 95-100.3°F) AND (WBC) AND (age 18 and 45 years old) AND (asthma) AND (bicarbonate) AND (bilirubin) AND (blood urea nitrogen) AND (chloride) AND (constipation) AND (creatinine) AND (hemoglobin) AND (left bundle branch block) AND (left ventricular hypertrophy) AND (non-smokers) AND (pain) AND (pain postoperative) AND (pathologic Q wave abnormalities) AND (platelets) AND (potassium) AND (respiratory compromise) AND (right bundle branch block) AND (sodium) AND (urine drug screening test Negative) AND (urine glucose) AND (urine protein) AND (white blood cells) AND ((Men) OR (women non-pregnant)) AND ((acute) OR (intermittent)) AND ((acute) OR (severe)))"}
{"candidate_id": "LLM07349", "doc_id": "NCT02019160_exc", "case_bucket": "or", "source_criterion": "Children who are uncooperative and difficult to manage, have major systemic diseases, or are on long-term medication will be excluded.", "candidate_expression": "((difficult to manage) AND (long-term) AND (major) AND (medication) AND (systemic diseases) AND (uncooperative))"}
{"candidate_id": "LLM07350", "doc_id": "NCT02590315_inc", "case_bucket": "other", "source_criterion": "Asymptomatic women 45-68 years, residents in the Piedmont Region, attending the regional breast cancer screening program", "candidate_expression": "((Piedmont Region) AND (regional breast cancer screening program) AND (women 45-68 years Asymptomatic))"}
```
