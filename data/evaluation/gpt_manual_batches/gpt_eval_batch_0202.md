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
{"candidate_id": "LLM05026", "doc_id": "NCT03193684_inc", "case_bucket": "other", "source_criterion": "eGFR>60 ml/min healthy volunteers type 2 diabetes patients who otherwise healthy", "candidate_expression": "((>60 ml/min) AND (eGFR) AND (healthy) AND (type 2 diabetes))"}
{"candidate_id": "LLM05027", "doc_id": "NCT01604187_exc", "case_bucket": "or", "source_criterion": "A previous history of intolerance to the study drug or related compounds and additives History of alcoholism, drug abuse, psychiatric, psychological or other emotional problems that are likely to invalidate informed consent Sleep apnoea Chronic obstructive pulmonary disease BMI = 35 or weight < 50 kg SpO2 < 90 % Concomitant drug therapy known to cause significant enzyme induction or inhibition of CYP 3A4. Pregnancy or nursing.", "candidate_expression": "((BMI = 35) AND (Chronic obstructive pulmonary disease) AND (Pregnancy) AND (Sleep apnoea) AND (SpO2 < 90 %) AND (alcoholism) AND (drug abuse) AND (drug therapy Concomitant) AND (emotional problems) AND (enzyme induction of CYP 3A4) AND (enzyme inhibition of CYP 3A4) AND (intolerance previous history) AND (nursing) AND (psychiatric problems) AND (psychological problems) AND (related compounds) AND (study drug) AND (weight < 50 kg))"}
{"candidate_id": "LLM05028", "doc_id": "NCT03099863_exc", "case_bucket": "or", "source_criterion": "Surgeries that include: intradetrusor Botox, vaginal mesh excision, and fistula repair Pregnancy History of nephrolithiasis Allergy to study medications Congenital urogenital anomaly Neurogenic bladder", "candidate_expression": "((Allergy) AND (Neurogenic bladder) AND (Pregnancy) AND (nephrolithiasis History) AND (study medications) AND (urogenital anomaly Congenital) AND (vaginal mesh) AND ((Botox intradetrusor) OR (fistula repair) OR (vaginal mesh excision)))"}
{"candidate_id": "LLM05029", "doc_id": "NCT02590653_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05030", "doc_id": "NCT02106598_inc", "case_bucket": "or", "source_criterion": "18 years of age or older Histologically confirmed diagnosis of melanoma, breast cancer or gynecologic cancer at MSKCC Have one of the following disease histories: Newly-diagnosed or recurrent (local, regional, metastatic) malignant melanoma or breast cancer patients in whom SLN mapping is indicated Residual clinically or radiographically evident tumor, including primary cutaneous and mucosal melanomas Prior radiation therapy, chemotherapy, or surgery in patients requiring flap reconstruction in the head and neck region. Newly diagnosed patients with previous excisional biopsy. OR Newly-diagnosed gynecologic cancer patients in whom SLN mapping and surgical excision is indicated OR Normal baseline cardiac function based upon pre-operative evaluation At the discretion of the operating surgeon, ANC>1000/mcl and platelets>100,000/mcl. At the discretion of the operating surgeon, Bilirubin level of < 2.0 mg/dl in the absence of a history of Gilbert's disease (or pattern consistent with Gilbert's). For melanoma patients, If patients have a history of malignancy other than melanoma, and other skin cancers in the past five years, their inclusion is up to the discretion of the physician. All patients of childbearing and child-creating age must be using an acceptable form of birth control Women who are pre-menopausal must have a negative serum pregnancy test", "candidate_expression": "((ANC >1000/mcl) AND (All patients of childbearing and child-creating age must be using an acceptable form of birth control) AND (At the discretion of the operating surgeon) AND (Bilirubin level < 2.0 mg/dl) AND (Histologically confirmed) AND (MSKCC) AND (SLN mapping) AND (SLN mapping is indicated) AND (Women) AND (age 18 years or older) AND (baseline) AND (cardiac function Normal) AND (excisional biopsy previous) AND (flap reconstruction head and neck region) AND (gynecologic cancer) AND (melanoma) AND (platelets >100,000/mcl) AND (pre-menopausal) AND (pre-operative evaluation pre-operative) AND (requiring flap reconstruction) AND (serum pregnancy test negative) AND (surgical excision) AND (surgical excision is indicated) AND (tumor Prior) AND (up to the discretion of the physician) AND NOT (Gilbert's disease history) AND NOT (melanoma) AND ((breast cancer) OR (malignant melanoma)) AND ((local) OR (metastatic) OR (regional)) AND ((Newly-diagnosed) OR (recurrent)) AND ((clinically Residual) OR (radiographically evident)) AND ((mucosal melanomas) OR (primary cutaneous)) AND ((chemotherapy) OR (radiation therapy) OR (surgery)) AND ((breast cancer) OR (gynecologic cancer) OR (melanoma)) AND ((malignancy history) OR (skin cancers history in the past five years)))"}
{"candidate_id": "LLM05031", "doc_id": "NCT03354572_exc", "case_bucket": "or", "source_criterion": "Pregnancy or lactating Allergy to NAC History of chronic pain Use of opioids or neuropathic analgesics Use of NAC prior to trial (< 1 month of planned surgery) Alcoholism Diabetes Mellitus (insulin therapy) Asthma or Chronic Obstructive pulmonary Disease Known renal function disorders (MDRD <ô0) Known liver failure (bilirubin >1.Sx upper limit of normal) No written lC by patient", "candidate_expression": "((< 1 month) AND (<ô0) AND (>1.Sx upper limit of normal) AND (Alcoholism) AND (Allergy) AND (Diabetes Mellitus) AND (History) AND (MDRD) AND (NAC) AND (No written lC by patient) AND (bilirubin) AND (chronic pain) AND (insulin) AND (liver failure) AND (planned) AND (prior to trial) AND (renal function disorders) AND (surgery) AND (trial) AND ((Pregnancy) OR (lactating)) AND ((Asthma) OR (Chronic Obstructive pulmonary Disease)) AND ((neuropathic analgesics) OR (opioids)))"}
{"candidate_id": "LLM05032", "doc_id": "NCT02509949_exc", "case_bucket": "or", "source_criterion": "Patients with a history of drug abuse; preoperative history of schizophrenia, epilepsy, parkinsonism, use of cholinesterase inhibitor, inability to communicate in the preoperative period (coma, profound dementia, or language barrier).", "candidate_expression": "((cholinesterase inhibitor) AND (coma) AND (drug abuse) AND (epilepsy) AND (history) AND (inability to communicate) AND (language barrier) AND (parkinsonism) AND (preoperative) AND (profound dementia) AND (schizophrenia))"}
{"candidate_id": "LLM05033", "doc_id": "NCT01228279_exc", "case_bucket": "or", "source_criterion": "Diabetes Mellitus Acute coronary syndrome in the past 6 months Cardiac arrhythmias (2nd and 3rd degree heart block or premature ventricular complexes in Lown classes 4 or 5) Symptoms suggestive of obstructive or central sleep apnea (with a score of > 10 on Epworth sleepiness scale) Patients taking Clonidine Body mass index (BMI) > 34 Patients unable to give consent Pregnant women Patients with leg injury involving nerve damage Patients taking anticoagulant medication Patients with significant bleeding disorder or liver disorder Hemoglobin <1.05 g/dl at the time of initiation of therapy patients with unilateral or bilateral nephrectomy Planned kidney transplant in the next 4 months Life expectancy under 6 months Oliguria (urine output less than 400 ml per day)", "candidate_expression": "((Acute coronary syndrome in the past 6 months) AND (BMI) AND (Body mass index > 34) AND (Cardiac arrhythmia) AND (Clonidine) AND (Diabetes Mellitus) AND (Epworth sleepiness scale score of > 10) AND (Hemoglobin <1.05 g/dl at the time of initiation of therapy) AND (Life expectancy under 6 months) AND (Oliguria) AND (Patients unable to give consent) AND (Pregnant women) AND (anticoagulant) AND (kidney transplant Planned in the next 4 months) AND (leg injury) AND (nephrectomy) AND (nerve damage) AND (premature ventricular complexes) AND (urine output less than 400 ml per day) AND ((central sleep apnea) OR (obstructive sleep apnea)) AND ((bleeding disorder significant) OR (liver disorder)) AND ((bilateral) OR (unilateral)) AND ((2nd degree heart block) OR (3rd degree heart block)) AND ((Lown classes 4) OR (Lown classes 5)))"}
{"candidate_id": "LLM05034", "doc_id": "NCT02573909_inc", "case_bucket": "other", "source_criterion": "Planned gynecological lower abdomen surgery with epidural pain treatment Informed consent obtained", "candidate_expression": "((epidural pain treatment) AND (gynecological lower abdomen surgery Planned))"}
{"candidate_id": "LLM05035", "doc_id": "NCT02918409_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05036", "doc_id": "NCT03305666_inc", "case_bucket": "other", "source_criterion": "Patients undergoing SSRF at Denver Health Medical Center", "candidate_expression": "((Denver Health Medical Center) AND (SSRF))"}
{"candidate_id": "LLM05037", "doc_id": "NCT02301039_inc", "case_bucket": "or", "source_criterion": "Age ≥ 18 years (Age ≥ 12 years for patients with bone sarcomas). Histologically confirmed diagnosis of unresectable, recurrent, and/or metastatic high grade soft-tissue or bone sarcoma of one of the following subtypes: soft tissue sarcomas (leiomyosarcoma, poorly differentiated/de-differentiated liposarcoma, high grade pleomorphic undifferentiated sarcoma/MFH and synovial sarcoma), and bone sarcomas (Ewing sarcoma, osteosarcoma, and chondrosarcoma [de-differentiated or mesenchymal]). ECOG Performance Status of 0 or 1. At least one site of measurable disease on CT/MRI scans as defined by RECIST 1.1. Baseline imaging must be performed within 30 days of dosing. At least one site of accessible disease for pre- and post-treatment core biopsies for at least 20 patients per arm on the expansion cohorts. Patients may have received 1-3 prior systemic therapies in the metastatic setting. Adequate organ function within 14 days of dosing Must be willing to provide and have available archival tissue for PD-L1 testing. Written, voluntary informed consent. Fertile men and women of childbearing potential must agree to use an effective method of birth control from providing signed consent and for 120 days after last study drug administration. Women of childbearing potential include pre-menopausal women and women within the first 2 years of the onset of menopause. Women of childbearing potential must have a negative pregnancy test ≤ 72 hours prior to Day 1 of study. Effective methods of birth control include: surgically sterile, barrier device (condom, diaphragm), contraceptive coil, intrauterine device (IUD), and abstinence. Life expectancy of >12 weeks. Patients with central nervous system disease are eligible for enrollment if they have received prior radiotherapy or surgery to sites of CNS metastatic disease and are without evidence of clinical progression for at least 4 weeks prior to screening, have no evidence of new or enlarging brain metastases, and are off steroids for at least 7 days before first dose of pembrolizumab.", "candidate_expression": "((Adequate organ function within 14 days of dosing) AND (Age ≥ 12 years) AND (Age ≥ 18 years) AND (CNS metastatic disease) AND (CT scans) AND (ECOG Performance Status 0 or 1) AND (Ewing sarcoma) AND (Histologically confirmed unresectable recurrent) AND (Life expectancy >12 weeks) AND (MFH) AND (MRI scans) AND (Women) AND (Written, voluntary informed consent.) AND (abstinence) AND (barrier device) AND (birth control) AND (birth control from providing signed consent for 120 days after last study drug administration) AND (bone sarcoma) AND (bone sarcomas) AND (central nervous system disease) AND (childbearing potential) AND (chondrosarcoma de-differentiated mesenchymal) AND (condom) AND (contraceptive coil) AND (diaphragm) AND (imaging Baseline within 30 days of dosing) AND (intrauterine device (IUD)) AND (leiomyosarcoma poorly differentiated de-differentiated) AND (liposarcoma high grade pleomorphic) AND (measurable disease) AND (men) AND (osteosarcoma) AND (pembrolizumab) AND (pre-menopausal) AND (pregnancy test negative ≤ 72 hours prior to Day 1) AND (radiotherapy) AND (sarcoma undifferentiated) AND (soft tissue sarcomas) AND (soft-tissue sarcoma metastatic high grade) AND (surgery) AND (surgically sterile) AND (synovial sarcoma) AND (systemic therapies 1-3 prior metastatic setting) AND (women) AND (women within the first 2 years of the onset of menopause) AND NOT (clinical progression for at least 4 weeks prior to screening) AND NOT (brain metastases new enlarging) AND NOT (steroids for at least 7 days before first dose of pembrolizumab))"}
{"candidate_id": "LLM05038", "doc_id": "NCT02944292_inc", "case_bucket": "other", "source_criterion": "Age 18 years or older Mechanical ventilation IAP between 12 and 20 mmHg in at least two consecutive measurements within 1-12 h Spontaneous breathing activity of at least 6 breaths/minute RASS score between 0 and -4 Physician-led sedation (if sedated; as opposed to nurse-led protocol)", "candidate_expression": "((18 years or older) AND (Age) AND (IAP) AND (Mechanical ventilation) AND (Physician-led) AND (RASS score) AND (Spontaneous breathing activity) AND (as opposed to) AND (at least 6 breaths/minute) AND (at least two consecutive measurements) AND (between 0 and -4) AND (between 12 and 20 mmHg) AND (nurse-led protocol) AND (sedation) AND (within 1-12 h))"}
{"candidate_id": "LLM05039", "doc_id": "NCT02222272_inc", "case_bucket": "or", "source_criterion": "All adult patients with chronic myeloid leukaemia in any phase (chronic, accelerated or blastic) who undergo allogeneic stem cell transplantation between 01/01/2010 and 30/09/2013 and have been previously treated with Nilotinib or Dasatinib, regardless of their response to these drugs.", "candidate_expression": "((Dasatinib) AND (Nilotinib) AND (adult) AND (allogeneic stem cell transplantation between 01/01/2010 and 30/09/2013) AND (chronic myeloid leukaemia any phase chronic accelerated blastic))"}
{"candidate_id": "LLM05040", "doc_id": "NCT02707874_exc", "case_bucket": "or", "source_criterion": "Patients who undergo iliac crest bone graft harvesting as part of their surgery Preexisting neurological deficits or peripheral neuropathy in the distribution of the sciatic nerve Local infection Contraindication to regional anesthesia e.g. bleeding diathesis, coagulopathy Chronic pain disorders History of use of over 30mg oxycodone or equivalent per day Allergy to local anesthetics History of significant psychiatric conditions that may affect patient assessment Pregnancy Inability to provide informed consent", "candidate_expression": "((Allergy) AND (Chronic pain) AND (Contraindication) AND (Inability to provide informed consent) AND (Local infection) AND (Pregnancy) AND (bleeding diathesis) AND (coagulopathy) AND (iliac crest bone graft harvesting) AND (local anesthetics) AND (neurological deficits) AND (over 30mg per day) AND (oxycodone) AND (oxycodone equivalent) AND (peripheral neuropathy) AND (regional anesthesia) AND (sciatic nerve))"}
{"candidate_id": "LLM05041", "doc_id": "NCT02565277_exc", "case_bucket": "or", "source_criterion": "Have not received influenza vaccination in the past or cannot be vaccinated due to previous severe reaction to influenza vaccine, egg, latex, or thimerosol allergies, or refusal of vaccination Participant has received a community available influenza vaccine within <6 months History of Guillain-Barré syndrome Immunosuppressive disorders or medications (including oral prednisone >10 mg daily, recent chemotherapy treatment) Emergency cases as determined by the investigator or physician", "candidate_expression": "((>10 mg daily) AND (Guillain-Barré syndrome) AND (Immunosuppressive disorders) AND (Immunosuppressive medications) AND (chemotherapy) AND (influenza vaccination) AND (influenza vaccine) AND (not) AND (oral prednisone) AND (within <6 months))"}
{"candidate_id": "LLM05042", "doc_id": "NCT03620526_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05043", "doc_id": "NCT02632266_exc", "case_bucket": "or", "source_criterion": "Newborn infants <28 weeks and >34 weeks gestation, those with life threatening illness, congenital and chromosomal anomalies, gastrointestinal anomalies or necrotizing enterocolitis and fed premature formula", "candidate_expression": "((<28 weeks and >34 weeks) AND (Newborn infants) AND (anomalies congenital) AND (chromosomal anomalies) AND (fed premature formula) AND (gastrointestinal anomalies) AND (gestation) AND (life threatening illness) AND (necrotizing enterocolitis))"}
{"candidate_id": "LLM05044", "doc_id": "NCT02315287_exc", "case_bucket": "or", "source_criterion": "Contraindication to sitagliptin or metformin or thiazolidinedione Pregnant or breast feeding women Type 1 diabetes, gestational diabetes, or secondary forms of diabetes Not appropriate for oral antidiabetic agent Medication which affect glycemic control Disease which affect efficacy and safety of drugs Any major illness (Liver disease, Renal failure, Heart disease, Cancer, etc)", "candidate_expression": "((Cancer) AND (Contraindication) AND (Disease affect efficacy safety of drugs) AND (Heart disease) AND (Liver disease) AND (Medication) AND (Pregnant) AND (Renal failure) AND (Type 1 diabetes) AND (affect glycemic control) AND (breast) AND (gestational diabetes) AND (major illness) AND (metformin) AND (oral antidiabetic agent) AND (secondary forms of diabetes) AND (sitagliptin) AND (thiazolidinedione) AND NOT (appropriate))"}
{"candidate_id": "LLM05045", "doc_id": "NCT02890719_exc", "case_bucket": "or", "source_criterion": "Genotype 2, 3, 5 or 6 infection. Decompensated cirrhosis defined by the presence of actual or previous history of clinical decompensation including ascites, hepatic encephalopathy, variceal bleeding or spontaneous bacterial peritonitis, or a Child-Pugh B or C. Hepatocellular carcinoma after liver transplantation. Total bilirubin > 3 mg/dL. Immunosuppression with cyclosporine or an mTOR inhibitor (everolimus or sirolimus). Severe extrahepatic diseases: cardiovascular, respiratory, cerebrovascular and poorly controlled diabetes. Platelets < 75 x 109 cells/L. Neutrophil count < 0.5 x 109 cells/L. Hemoglobin < 9 g/dL. Albumin < 3g/dL. HIV infection. Hepatitis B infection. Active intake of toxic amounts of alcohol or recreational drugs. Females who are pregnant, become to be pregnant or breastfeeding or males whose partners are pregnant, become to be pregnant or breastfeeding. Intake of disallowed medications including(but not limited to): 1. Antibiotics: clarithromycin, erythromycin, telithromycin, nafcillin, rifampin 2. Antifungals: itraconazole, ketoconazole, voriconazole 3. Antihypertensives: nifedipine 4. Anticonvulsants: carbamazepine, phenytoin, phenobarbital 5. Bosentan 6. Modafinil 7. St.Jonh's Wort 8. Immunosuppressants: cyclosporin, everolimus, sirolimus 9. Diabetes agents: glibenclamide, glyburide 10. Lipid lowering agents: gemfibrozil 11. Eltrombopag 12. Lapatinib 13. HIV medications: efavirenz, etravirine, all ritonavir boosted and unboosted HIV protease inhibitors 14. Statins: simvastatin, fluvastatin, rosuvastatin at doses greater than 10 mg/d, atorvastatin at doses greater than 10 mg/d.", "candidate_expression": "((2, 3, 5 or 6) AND (< 0.5 x 109 cells/L) AND (< 3g/dL) AND (< 75 x 109 cells/L) AND (< 9 g/dL) AND (> 3 mg/dL) AND (Active intake) AND (Albumin) AND (B or C) AND (Bosentan) AND (Decompensated) AND (Eltrombopag) AND (Females) AND (Genotype) AND (HIV infection) AND (Hemoglobin) AND (Hepatitis B infection) AND (Hepatocellular carcinoma) AND (Immunosuppression) AND (Lapatinib) AND (Modafinil) AND (Neutrophil count) AND (Platelets) AND (Severe) AND (St.Jonh's Wort) AND (Total bilirubin) AND (after liver transplantation) AND (become) AND (breastfeeding) AND (carbamazepine) AND (cirrhosis) AND (clinical decompensation) AND (disallowed medications) AND (doses greater than 10 mg/d) AND (extrahepatic diseases) AND (gemfibrozil) AND (infection) AND (liver transplantation) AND (males) AND (nifedipine) AND (phenobarbital) AND (phenytoin) AND (poorly controlled) AND (pregnant) AND (ritonavir) AND (toxic amounts) AND ((cyclosporin) OR (everolimus) OR (sirolimus)) AND ((glibenclamide) OR (glyburide)) AND ((HIV protease inhibitors) OR (efavirenz) OR (etravirine)) AND ((ritonavir boosted) OR (ritonavir unboosted)) AND ((atorvastatin) OR (fluvastatin) OR (rosuvastatin) OR (simvastatin)) AND ((Child-Pugh) OR (ascites) OR (hepatic encephalopathy) OR (spontaneous bacterial peritonitis) OR (variceal bleeding)) AND ((actual) OR (previous)) AND ((cyclosporine) OR (mTOR inhibitor)) AND ((everolimus) OR (sirolimus)) AND ((cardiovascular) OR (cerebrovascular) OR (diabetes) OR (respiratory)) AND ((alcohol) OR (recreational drugs)) AND ((clarithromycin) OR (erythromycin) OR (nafcillin) OR (rifampin) OR (telithromycin)) AND ((itraconazole) OR (ketoconazole) OR (voriconazole)))"}
{"candidate_id": "LLM05046", "doc_id": "NCT03064867_inc", "case_bucket": "or", "source_criterion": "Histological confirmation of relapsed/refractory diffuse large B-cell lymphoma after prior rituximab and anthracycline-containing systemic treatment regimen such as R-CHOP (rituximab, cyclophosphamide, doxorubicin, vincristine, and prednisone), R-EPOCH (rituximab, etoposide phosphate, prednisone, vincristine sulfate, cyclophosphamide, doxorubicin hydrochloride), R-HyperCVAD (rituximab, cyclophosphamide, vincristine sulfate, doxorubicin hydrochloride, dexamethasone) etc. Subjects must have received no more than 2 prior systemic therapies for lymphoma. Prior therapy with systemic rituximab monotherapy or conventional chemotherapy (i.e. bendamustine, CVP (Cyclophosphamide, Vincristine Sulfate, Prednisone) or other) ± rituximab for indolent non-Hodgkin's lymphoma (NHL) ± maintenance/extended-use rituximab will count as 1 line of systemic therapy. Eastern Cooperative Oncology Group (ECOG) Performance status ≤ 2 Subjects must have normal organ and marrow function as defined below: Hemoglobin ≥ 8.0 g/dl Absolute neutrophil count ≥ 1,000/mcL Platelet count ≥ 75,000/mcL Total bilirubin ≤ 1.5 X the upper limit of normal (ULN) unless a known history of impaired bilirubin conjugation such as Gilbert's, for whom the maximum will be 2.5 ULN. Aspartate transaminase (AST) (SGOT) ≤ 2.5 X institutional ULN Alanine transaminase (ALT) (SGPT) ≤ 2.5 X institutional ULN International normalized ratio (INR) > 1.5 ×ULN Patients must have a calculated serum creatinine clearance > 50 mL/min using Cockcroft-Gault calculation or based on 24-hour urine collection performed within 7 days prior to treatment. Specific guidelines will be followed regarding inclusion of relapsed/refractory DLBCL based on Hepatitis B serological testing as follow: HBsAg negative, HBcAb negative, HBsAb positive patients are eligible. Patients who test positive for HBsAg are ineligible Patients with HBsAg negative, but HBcAb positive (regardless of HBsAb status) should have a HBV DNA testing performed and protocol eligibility determined as follow: If HBV DNA is positive, the subject is ineligible. If HBV DNA is negative, the subject may be included but must undergo HBV DNA PCR testing monthly x 3 months beginning from the start of treatment Subjects must have the ability to understand and the willingness to sign a written informed consent document. For women of childbearing potential: agreement to remain abstinent (refrain from heterosexual intercourse) or use a contraceptive method with a failure rate of < 1% per year during the treatment period and for at least 30 days after the last dose of venetoclax or 18 months after the last dose of rituximab, whichever is longer. A woman is considered to be of childbearing potential if she is postmenarcheal, has not reached a postmenopausal state (< 12 continuous months of amenorrhea with no identified cause other than menopause), and has not undergone surgical sterilization (removal of ovaries and/or uterus). For men: agreement to remain abstinent (refrain from heterosexual intercourse) or use contraceptive measures, and agreement to refrain from donating sperm, as defined below: With female partners of childbearing potential, men must remain abstinent or use a condom plus an additional contraceptive method that together result in a failure rate of < 1% per year during the treatment period and for at least 6 months after the last dose of rituximab. Men must refrain from donating sperm during this same period. With pregnant female partners, men must remain abstinent or use a condom during the treatment period and for at least 6 months after the last dose of rituximab to avoid exposing the embryo.", "candidate_expression": "((24-hour urine collection) AND (> 1.5 ×ULN) AND (> 50 mL/min) AND (Absolute neutrophil count) AND (Alanine transaminase (ALT) (SGPT)) AND (Aspartate transaminase (AST) (SGOT)) AND (B-cell lymphoma) AND (CVP) AND (Cockcroft-Gault calculation) AND (Cyclophosphamide) AND (Eastern Cooperative Oncology Group (ECOG) Performance status) AND (For men: agreement to remain abstinent (refrain from heterosexual intercourse) or use contraceptive measures, and agreement to refrain from donating sperm, as defined below) AND (For women of childbearing potential: agreement to remain abstinent (refrain from heterosexual intercourse) or use a contraceptive method with a failure rate of < 1% per year during the treatment period and for at least 30 days after the last dose of venetoclax or 18 months after the last dose of rituximab, whichever is longer.) AND (Gilbert's) AND (HBV DNA) AND (HBV DNA testing) AND (HBcAb) AND (HBsAb) AND (HBsAg) AND (Hemoglobin) AND (Histological) AND (International normalized ratio (INR)) AND (Platelet count) AND (Prednisone) AND (Prior) AND (R-CHOP) AND (R-EPOCH) AND (R-HyperCVAD) AND (Total bilirubin) AND (Vincristine Sulfate) AND (With female partners of childbearing potential, men must remain abstinent or use a condom plus an additional contraceptive method that together result in a failure rate of < 1% per year during the treatment period and for at least 6 months after the last dose of rituximab.) AND (after) AND (anthracycline) AND (bendamustine) AND (confirmation) AND (conventional chemotherapy) AND (cyclophosphamide) AND (dexamethasone) AND (diffuse) AND (doxorubicin) AND (doxorubicin hydrochloride) AND (etoposide phosphate) AND (extended-use) AND (impaired bilirubin conjugation) AND (indolent) AND (large) AND (maintenance) AND (maximum 2.5 ULN) AND (negative) AND (no more than 2) AND (non-Hodgkin's lymphoma (NHL)) AND (normal marrow function) AND (normal organ function) AND (positive) AND (prednisone) AND (prior) AND (prior rituximab and anthracycline-containing systemic treatment regimen) AND (rituximab) AND (rituximab and anthracycline-containing systemic treatment regimen) AND (serum creatinine clearance) AND (systemic monotherapy) AND (systemic therapies for lymphoma) AND (treatment) AND (vincristine) AND (vincristine sulfate) AND (within 7 days prior) AND (≤ 1.5 X the upper limit of normal (ULN)) AND (≤ 2) AND (≤ 2.5 X institutional ULN) AND (≥ 1,000/mcL) AND (≥ 75,000/mcL) AND (≥ 8.0 g/dl))"}
{"candidate_id": "LLM05047", "doc_id": "NCT02396420_inc", "case_bucket": "or", "source_criterion": "Patient has provided signed informed consent Patient is aged greater than or equal to 40 and less than or equal to 89 years of age Patient has a prostate size between 90g and 200g, as determined by MRI Patient has experienced lower urinary tract symptoms (LUTS) for at least 6 months prior to study enrollment Patient has an IPSS score of at least 13 at baseline Patient is either: refractory to medical treatment, contraindicated to medical treatment, OR refuses medical treatment Patient either: refuses surgical treatment OR is contraindicated for surgical treatment Patient meets ONE of the following criteria: baseline PSA < 4.0ng/mL (no prostate biopsy required) OR baseline PSA >/= 4 ng/mL AND a negative prostate biopsy (minimum 12 core biopsy) within the prior 12 months", "candidate_expression": "((IPSS score at least 13 at baseline) AND (MRI) AND (PSA baseline < 4.0ng/mL) AND (PSA baseline >/= 4 ng/mL) AND (aged greater than or equal to 40 less than or equal to 89 years) AND (contraindicated for surgical treatment) AND (contraindicated to medical treatment) AND (core biopsy minimum 12) AND (lower urinary tract symptoms (LUTS) at least 6 months prior to study enrollment) AND (prostate biopsy negative) AND (prostate size between 90g and 200g) AND (refractory to medical treatment) AND (refuses medical treatment) AND (refuses surgical treatment) AND (signed informed consent))"}
{"candidate_id": "LLM05048", "doc_id": "NCT03262038_exc", "case_bucket": "or", "source_criterion": "Inability to use verbal or pictorial pain scoring scales hypersensitivity to selective 5-HT receptor antagonists diagnosed congenital long QT syndrome severe hepatic impairment pregnancy or nursing mothers", "candidate_expression": "((Inability) AND (congenital long QT syndrome) AND (hepatic impairment severe) AND (hypersensitivity) AND (nursing) AND (pictorial pain scoring scales) AND (pregnancy) AND (selective 5-HT receptor antagonists) AND (verbal pain scoring scales))"}
{"candidate_id": "LLM05049", "doc_id": "NCT02303171_inc", "case_bucket": "other", "source_criterion": "Pregnant women with APS diagnosed according to the revised classification criteria for APS in 2006 in Sydney, Australia Early pregnancy body weight is 50-90 Kg", "candidate_expression": "((APS revised classification criteria for APS in 2006 in Sydney, Australia) AND (Pregnant) AND (body weight Early pregnancy 50-90 Kg) AND (women))"}
{"candidate_id": "LLM05050", "doc_id": "NCT02361892_exc", "case_bucket": "or", "source_criterion": "endometrial hyperplasia with atypia, estrogen-progestin therapy in the 2 months before enrollment, autoimmune diseases, chronic, metabolic, systemic and endocrine disorders, including hyperandrogenism, hyperprolactinemia, diabetes mellitus and thyroid disease, hypogonadotropic hypogonadism, majors clinical conditions", "candidate_expression": "((atypia) AND (autoimmune diseases) AND (chronic disorders) AND (diabetes mellitus) AND (endocrine disorders) AND (endometrial hyperplasia) AND (estrogen-progestin therapy in the 2 months before enrollment) AND (hyperandrogenism) AND (hyperprolactinemia) AND (hypogonadotropic hypogonadism) AND (majors clinical conditions) AND (metabolic disorders) AND (systemic disorders) AND (thyroid disease))"}
```
