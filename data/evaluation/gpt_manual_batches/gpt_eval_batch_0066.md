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
{"candidate_id": "LLM01626", "doc_id": "NCT00730301_exc", "case_bucket": "or", "source_criterion": "Prior endobronchial treatment for emphysema Pleural or interstitial disease that precludes surgery. Prior lung transplant, LVRS, median sternotomy, bullectomy or lobectomy. Clinically significant bronchiectasis Pulmonary nodule requiring surgery History of recurrent respiratory infections (> 3 hospitalization in the last year) Clinically significant (> 4 Tablespoons per day) sputum production Fever, elevated white cell count, or other evidence of active infection Dysrhythmia that might pose a risk during exercise or training Congestive heart failure within 6 mo and LVEF < 45% Evidence or history of Cor Pulmonale Resting bradycardia (< 50 beats/min), frequent multifocal PVCs, complex ventricular arrhythmia, sustained SVT History of exercise-related syncope MI within 6 mo and LVEF < 45% Evidence of systemic disease or neoplasia expected to compromise survival during 5-yr period Any disease or condition that interferes with completion of initial or follow-up assessments Patient is currently enrolled in another clinical trial Patient is unable to complete 3 minutes of unloaded peddling on cycle ergometer Alpha-1-Antitrypsin Deficiency", "candidate_expression": "((Alpha-1-Antitrypsin Deficiency) AND (Congestive heart failure within 6 mo) AND (Cor Pulmonale) AND (Dysrhythmia) AND (Fever) AND (LVEF < 45%) AND (LVEF < 45% Evidence) AND (LVRS) AND (MI within 6 mo) AND (Pleural disease) AND (Pulmonary nodule) AND (Resting bradycardia < 50 beats/min) AND (active infection evidence) AND (bronchiectasis Clinically significant) AND (bullectomy) AND (complex ventricular arrhythmia) AND (condition) AND (disease) AND (emphysema) AND (endobronchial treatment Prior) AND (enrolled in another clinical trial currently) AND (history) AND (hospitalization > 3 in the last year) AND (interstitial disease) AND (lobectomy) AND (lung transplant) AND (median sternotomy) AND (multifocal PVCs frequent) AND (neoplasia) AND (pose a risk during exercise during training exercise training) AND (respiratory infections History recurrent) AND (sputum production Clinically significant > 4 Tablespoons per day) AND (surgery) AND (sustained SVT) AND (syncope History exercise-related) AND (systemic disease) AND (unable to complete 3 minutes of unloaded peddling on cycle ergometer) AND (white cell count elevated) AND NOT (surgery))"}
{"candidate_id": "LLM01627", "doc_id": "NCT03216447_inc", "case_bucket": "other", "source_criterion": "Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure Patient is a primary liver transplant recipient Patient is 20 to 70 years of age Patient should be clearly conscious, fully understand and able to answer questionnaire", "candidate_expression": "((20 to 70 years) AND (Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure) AND (Patient should be clearly conscious, fully understand and able to answer questionnaire) AND (age) AND (primary liver transplant) AND (recipient))"}
{"candidate_id": "LLM01628", "doc_id": "NCT01907230_inc", "case_bucket": "or", "source_criterion": "Age : from 20 to 90 y/o. HBsAg-positive for more than 6 months and HBV DNA < 2000 IU/ml (Subgroup 1)or HBsAg-negative but anti-HBc positive with HBV DNA < 2000 IU/ml (Subgroup 2). Inflammatory arthritis patients who plan to treat with biological agents, including Humira or Enbrel or Simponi or Orencia or Mabthera or Actemra; as first line biologic treatment is indicated.", "candidate_expression": "((20 to 90 y/o) AND (< 2000 IU/ml) AND (Actemra) AND (Age) AND (Enbrel) AND (HBV DNA) AND (HBsAg) AND (Humira) AND (Inflammatory arthritis) AND (Mabthera) AND (Orencia) AND (Simponi) AND (anti-HBc) AND (biological agents) AND (more than 6 months) AND (negative) AND (positive))"}
{"candidate_id": "LLM01629", "doc_id": "NCT02773173_exc", "case_bucket": "or", "source_criterion": "Emergency surgery Pregnancy or lactation Immune disorders Kidney or liver disease or advanced-stage cardiopulmonary Patient refusal to participate in the study Patients under 18 years or inability to consent Associated neuromuscular disorders, contraindication for the use of rocuronium/ sugammadex, allergy or hypersensitivity to rocuronium / sugammadex", "candidate_expression": "((Emergency surgery) AND (Immune disorders) AND (Patient refusal to participate in the study) AND (contraindication) AND (inability to consent) AND (neuromuscular disorders) AND ((inability to consent) OR (years under 18)) AND ((rocuronium) OR (sugammadex)) AND ((allergy) OR (hypersensitivity)) AND ((Pregnancy) OR (lactation)) AND ((Kidney disease) OR (advanced-stage cardiopulmonary) OR (liver disease)))"}
{"candidate_id": "LLM01630", "doc_id": "NCT02282319_exc", "case_bucket": "other", "source_criterion": "micturition problems, neurological history or previous lower abdominal surgery with an abnormal micturition", "candidate_expression": "((abnormal) AND (lower abdominal surgery) AND (micturition) AND (neurological history))"}
{"candidate_id": "LLM01631", "doc_id": "NCT02499185_exc", "case_bucket": "other", "source_criterion": "Ongoing acute kidney injury Stage 2/3 History of kidney transplant", "candidate_expression": "((2/3) AND (History) AND (Stage) AND (acute kidney injury) AND (kidney transplant))"}
{"candidate_id": "LLM01632", "doc_id": "NCT03500211_inc", "case_bucket": "or", "source_criterion": "Pregnant patients who require a scheduled or non-urgent cesarean birth Patient able to receive neuraxial analgesia Patient able to give verbal and written consent for both cesarean birth and study", "candidate_expression": "((Patient able to give verbal and written consent for both cesarean birth and study) AND (Pregnant) AND (able to receive) AND (cesarean birth) AND (neuraxial analgesia) AND (non-urgent) AND (scheduled))"}
{"candidate_id": "LLM01633", "doc_id": "NCT02312960_inc", "case_bucket": "other", "source_criterion": "Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial", "candidate_expression": "(Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial)"}
{"candidate_id": "LLM01634", "doc_id": "NCT02900443_exc", "case_bucket": "or", "source_criterion": "Overlap syndrome with Primary Sclerosing Cholangitis (PSC) or Primary Biliary Cholangitis (PBC) (Paris criteria, strong positive Anti-Mitochondrial Antibodies (AMA), past liver biopsy or cholangiographic findings compatible with PBC or PSC). Presentation with acute liver failure, defined as presence of hepatic encephalopathy and coagulopathy (INR > 1.5) Current treatment with prednisone/prednisolone and/or immunosuppressive medication for an indication other than autoimmune hepatitis Current systemic infection Other clinically significant medical conditions that could interfere with the trial If female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures. History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain", "candidate_expression": "((AMA) AND (Anti-Mitochondrial Antibodies strong positive) AND (History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate) AND (INR > 1.5) AND (Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain) AND (Overlap syndrome) AND (PBC) AND (PSC) AND (Paris criteria,) AND (acute liver failure) AND (coagulopathy) AND (f female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures) AND (hepatic encephalopathy) AND (indication) AND (systemic infection) AND NOT (autoimmune hepatitis) AND ((cholangiographic findings) OR (liver biopsy)) AND ((immunosuppressive medication) OR (prednisolone) OR (prednisone)) AND ((Primary Biliary Cholangitis) OR (Primary Sclerosing Cholangitis)))"}
{"candidate_id": "LLM01635", "doc_id": "NCT03434951_exc", "case_bucket": "or", "source_criterion": "rearthroplasty ASA IV-V inadequate spoken finnish for reliable pain assessment Dementia or otherwise impaired cognition contraindication for any medication or substance used in survey protocol weight <50kg or BMI =35 kg/m2 preoperative SpO2 less than 93% clinical suspicion that subject can not use PCA adequately history of substance abuse or current excessive use of alcohol preoperative use of either pregabalin, gabapentin or strong opiates", "candidate_expression": "((<50kg) AND (=35 kg/m2) AND (ASA) AND (IV-V) AND (SpO2) AND (clinical suspicion) AND (contraindication) AND (current) AND (history) AND (inadequate spoken finnish) AND (less than 93%) AND (preoperative) AND (rearthroplasty) AND (reliable pain assessment) AND (subject can not use PCA adequately) AND ((BMI) OR (weight)) AND ((excessive use of alcohol) OR (substance abuse)) AND ((gabapentin) OR (pregabalin) OR (strong opiates)) AND ((Dementia) OR (impaired cognition)) AND ((medication used in survey protocol) OR (substance used in survey protocol)))"}
{"candidate_id": "LLM01636", "doc_id": "NCT02783859_inc", "case_bucket": "or", "source_criterion": "Hospitalised children aged 3-mo to 5-yrs (in Darwin, children have to be Indigenous) Have features of severe pneumonia on admission (temperature >37.5 celsius or a history of fever at home or observed at the referring clinic, age-adjusted tachypnoea [respiratory rate>50 if <12-months; respiratory rate>40 if >12-months] with chest wall recession and/or oxygen saturation <92% in air), and consolidation on chest X-ray as diagnosed by treating clinician After 1-3 days of IV antibiotics, are afebrile, with improved respiratory symptoms and signs, oxygen saturation>90% in air and are ready to be switched to oral amoxicillin-clavulanate, and Have symptoms of no longer than 7 days at point of hospitalisation.", "candidate_expression": "((3-mo to 5-yrs) AND (<12-months) AND (<92% in air) AND (>12-months) AND (>37.5 celsius) AND (>40) AND (>50) AND (Hospitalised) AND (aged) AND (chest X-ray) AND (children) AND (consolidation) AND (hospitalisation) AND (no longer than 7 days at point of hospitalisation) AND (pneumonia) AND (respiratory rate) AND (severe) AND (symptoms) AND (tachypnoea) AND (temperature) AND ((age)) AND ((chest wall recession) OR (oxygen saturation)))"}
{"candidate_id": "LLM01637", "doc_id": "NCT02499185_inc", "case_bucket": "other", "source_criterion": "= 18 years High risk patients: General Surgery AKI Risk Index Class III, IV or V Major abdominal surgery", "candidate_expression": "((= 18 years) AND (Class III, IV or V) AND (General Surgery AKI Risk Index) AND (High risk) AND (Major abdominal surgery))"}
{"candidate_id": "LLM01638", "doc_id": "NCT02715466_exc", "case_bucket": "or", "source_criterion": "Administration of HES, dextrane solutions or > 500 ml of Gelatin solutions within the 24 h prior to randomization Death expected within the next 48 h (moribund patients as defined by ASA = class V) Patients whose medical condition does preclude the PLR manoeuvre Patients for whom the need of pressure infusions are expected Requirement for renal support (either continuous or discontinuous techniques, including intermittent haemodialysis, haemofiltration and haemodiafiltration) Patients receiving therapeutic heparin medication due to chronic coagulation disease / anticoagulation medication (i.e. partial thromboplastin time > 60 sec) Acutely burned patients Contraindications according to summary of product characteristics of investigational test and reference product Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)", "candidate_expression": "((ASA = class V) AND (Acutely burned) AND (Death expected within the next 48 h) AND (heparin) AND (moribund) AND (partial thromboplastin time > 60 sec) AND (renal support Requirement for) AND ((anticoagulation medication) OR (chronic coagulation disease)) AND ((Gelatin solutions > 500 ml) OR (HES) OR (dextrane solutions)))"}
{"candidate_id": "LLM01639", "doc_id": "NCT00954850_exc", "case_bucket": "or", "source_criterion": "Malignancy and other significant medical conditions that will impact follow up within this program. Those less than 18 years of age. Concomitant interstitial lung disease, sarcoidosis, other significant lung disease. Those who have had a transplant. Significant travel with work. Unable to make appointments (every three to six months over 2 years). Those residing in another country or planned absence for more than one month.", "candidate_expression": "((Malignancy) AND (Unable to make appointments (every three to six months over 2 years).) AND (age less than 18 years) AND (interstitial lung disease) AND (lung disease) AND (medical conditions significant) AND (sarcoidosis) AND (transplant))"}
{"candidate_id": "LLM01640", "doc_id": "NCT02542956_inc", "case_bucket": "or", "source_criterion": "Undergoing abdominoplasty or TRAM flap breast reconstruction", "candidate_expression": "((TRAM flap breast reconstruction) AND (abdominoplasty))"}
{"candidate_id": "LLM01641", "doc_id": "NCT01743755_inc", "case_bucket": "or", "source_criterion": "18 years or older Chest radiograph showing new opacities. Cough Production of sputum Temp >38,0 °C or <36,0 °C Audible abnormalities by chest examination compatible with pneumonia Leukocytosis (>10.000 cells/mm3), leftward shift (>10%) or leucopenia (<4000 cells/mm3) C-reactive protein > 15 mg/l (three fold higher than the upper limit of normal)", "candidate_expression": "((18 or older) AND (<4000 cells/mm3) AND (> 15 mg/l) AND (>10.000 cells/mm3) AND (Audible abnormalities) AND (C-reactive protein) AND (Chest radiograph) AND (Cough) AND (Temp) AND (chest examination) AND (leftward shift >10%) AND (new) AND (opacities) AND (pneumonia) AND (sputum) AND (three fold higher than the upper limit of normal) AND (years) AND ((<36,0 °C) OR (>38,0 °C)) AND ((Leukocytosis) OR (leucopenia)))"}
{"candidate_id": "LLM01642", "doc_id": "NCT03016741_inc", "case_bucket": "or", "source_criterion": "Have diagnosis of prostate cancer and have received treatment with GnRH agonist or antagonist therapy for at least 1 month prior to enrollment. Willing and able to complete survey questionnaires in English without assistance through the duration of the study. This stipulation is in place because not all of the proposed quality of life or cognitive tests are available or validated in other languages. Age = 18 years. Ability to understand and the willingness to sign a written informed consent document written in English that is approved by an institutional review board. Have either newly diagnosed metastatic hormone sensitive prostate cancer (mHSPC) or castration-resistant metastatic prostate cancer (mCRPC) and eligible to undergo treatment with abiraterone acetate (mHSPC or mCRPC) or enzalutamide (mCRPC) Patients may have received the following prior AR directed therapy prior to enrollment: bicalutamide, ketoconazole. Prior to enrollment, patients may have received treatment with abiraterone acetate or enzalutamide for no more than 14 days before completing baseline studies. Patients may have received chemotherapy for hormone-sensitive metastatic prostate cancer only, but it must not have lasted for more than 6 months. At least 12 months must have elapsed since completion of chemotherapy. Patients may have received prior definitive radiation therapy or surgery. At least 60 days must have elapsed since completion of definitive radiation therapy or surgery and patient must have only grade 2 or less adverse effects at the time of registration. Enrollment during palliative radiation of = 10 days, or radiation of = 10 days during the duration of the study is allowed. Patients must be able to take oral medication.", "candidate_expression": "((Age = 18 years) AND (GnRH agonist) AND (GnRH antagonist) AND (abiraterone acetate) AND (adverse effects grade 2 or less at the time of registration) AND (chemotherapy) AND (chemotherapy lasted for more than 6 months At least 12 months must have elapsed since completion of chemotherapy) AND (enzalutamide) AND (mCRPC) AND (mHSPC) AND (prostate cancer) AND (prostate cancer castration-resistant metastatic) AND (prostate cancer hormone-sensitive metastatic) AND (prostate cancer metastatic hormone sensitive) AND (radiation therapy) AND (radiation therapy definitive) AND (surgery) AND (treatment) AND (treatment for at least 1 month prior to enrollment))"}
{"candidate_id": "LLM01643", "doc_id": "NCT03472846_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus type 1 renal insufficiency III-V ° Cirrhosis hepatis (Child B or higher) Chronic alcohol abuse rheumatic disease (RA, SpA, SLE) Malignancies (<5 years) Eating Disorder (anorexia nervosa, bulimia) bone-specific pretreatment (DMAB, TPTD, strontium ranelate, SERMs) Bisphosphonate treatment is allowed", "candidate_expression": "((Child B or higher) AND (Cirrhosis hepatis Child B or higher) AND (Diabetes mellitus type 1) AND (Eating Disorder) AND (Malignancies <5 years) AND (alcohol abuse Chronic) AND (bone-specific pretreatment) AND (renal insufficiency III-V °) AND (rheumatic disease) AND ((RA) OR (SLE) OR (SpA)) AND ((anorexia nervosa) OR (bulimia)) AND ((DMAB) OR (SERMs) OR (TPTD) OR (strontium ranelate)))"}
{"candidate_id": "LLM01644", "doc_id": "NCT03445949_exc", "case_bucket": "or", "source_criterion": "indications to dual antiplatelet therapy other than atrial fibrillation or left atrial appendage occlusion at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. coronary artery disease) indications to anticoagulation at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. pulmonary embolism) known allergy to clopidogrel or acetylsalicylic acid precluding its administration as specified by the protocol any known inborn or acquired coagulation disorders poor tolerance of or technical difficulties with performing transesophageal echocardiography peridevice leak >5mm on transesophageal echocardiography study preceding enrollment left atrial thrombus on transesophageal echocardiography study performed after successful left atrial appendage closure but before enrollment life expectancy of less than 18months participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months chronic kidney disease stage IV and V women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women", "candidate_expression": "((acetylsalicylic acid) AND (allergy) AND (anticoagulation at the time of enrollment predicted appearance) AND (atrial fibrillation) AND (breast feeding) AND (chronic kidney disease stage IV stage V) AND (clopidogrel) AND (coagulation disorders) AND (coronary artery disease within the duration of the trial) AND (dual antiplatelet therapy) AND (indications) AND (left atrial appendage closure successful before enrollment enrollment) AND (left atrial appendage occlusion at the time of enrollment predicted appearance) AND (left atrial thrombus) AND (life expectancy less than 18months) AND (participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months) AND (peridevice leak >5mm) AND (poor tolerance) AND (pregnant) AND (pulmonary embolism within the duration of the trial) AND (technical difficulties) AND (transesophageal echocardiography) AND (transesophageal echocardiography after successful left atrial appendage closure) AND (transesophageal echocardiography study) AND (women) AND (women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women))"}
{"candidate_id": "LLM01645", "doc_id": "NCT03173092_inc", "case_bucket": "other", "source_criterion": "Participants must have completed 3 cycles of a bortezomib-based induction regimen (as defined by current NCCN guidelines) and have no evidence of disease progression as defined by IMWG criteria. Participants with light chain and free light chain (FLC) only may be enrolled if they meet all the criteria for a diagnosis of MM. Participants must be considered by their physician eligible to receiving the IRD regimen. Eastern Cooperative Oncology Group (ECOG) performance status and/or other performance status 0, 1, or 2 at time of enrollment.", "candidate_expression": "((0, 1, or 2) AND (3 cycles) AND (Eastern Cooperative Oncology Group (ECOG) performance status) AND (IMWG criteria) AND (IRD regimen) AND (NCCN guidelines) AND (all) AND (at time of enrollment) AND (bortezomib) AND (criteria for a diagnosis of MM) AND (eligible to) AND (induction regimen) AND (light chain and free light chain (FLC)) AND (no evidence of disease progression))"}
{"candidate_id": "LLM01646", "doc_id": "NCT01806558_exc", "case_bucket": "or", "source_criterion": "1. Are unable to understand and sign the consent form 2. Are pregnant or lactating 3. Are physically unable to sit upright and still for 40 minutes 4. Have undergone bilateral mastectomy 5. Are not scheduled to undergo conventional ultrasound", "candidate_expression": "((Are unable to understand and sign the consent form) AND (bilateral mastectomy) AND (conventional ultrasound) AND (for 40 minutes) AND (not) AND (physically unable to sit upright and still) AND (scheduled) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM01647", "doc_id": "NCT02872090_inc", "case_bucket": "other", "source_criterion": "patients with FEV1 / FVC <70%", "candidate_expression": "(FEV1 / FVC <70%)"}
{"candidate_id": "LLM01648", "doc_id": "NCT00812344_inc", "case_bucket": "other", "source_criterion": "body mass index (BMI) between 19 to 30 kg/m2 and body weight between 50 to 100 kg inclusive", "candidate_expression": "((body mass index (BMI) between 19 to 30 kg/m2) AND (body weight 50 to 100 kg inclusive))"}
{"candidate_id": "LLM01649", "doc_id": "NCT01765231_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with lymphoma HBsAg negative/HBcAb positive/hepatitis B virus DNA negative at baseline treated with chemotherapy and/or immunosuppressive therapy life expectancy of more than 3 months", "candidate_expression": "((HBcAb) AND (HBsAg) AND (at baseline) AND (chemotherapy) AND (hepatitis B virus DNA) AND (immunosuppressive therapy) AND (life expectancy) AND (lymphoma) AND (more than 3 months) AND (negative) AND (positive) AND (treatment-naive))"}
{"candidate_id": "LLM01650", "doc_id": "NCT02437045_exc", "case_bucket": "or", "source_criterion": "Patient not expected to survive more than 4 days Patient allergic to a penicillin or a carbapenem Patient with significant polymicrobial bacteraemia (that is, a Gram positive skin contaminant in one set of blood cultures is not regarded as significant polymicrobial bacteraemia). Treatment is not with the intent to cure the infection (that is, palliative care is an exclusion). Pregnancy or breast-feeding. Use of concomitant antimicrobials in the first 4 days after enrolment with known activity against Gram-negative bacilli (except trimethoprim/sulphamethoxazole may be continued as Pneumocystis prophylaxis). Severe acute illness as defined by Pitt bacteraemia score of >4 Likely source to be from (proven or suspected at the time of randomisation) the central nervous system, e.g. brain abscess, post-surgical meningitis, shunt infection (due to concerns over CNS penetration of piperacillin/tazobactam)", "candidate_expression": "((Pitt bacteraemia score >4) AND (Pregnancy or breast-feeding) AND (allergic) AND (antimicrobials concomitant first 4 days after enrolment Gram-negative bacilli) AND (bacteraemia polymicrobial) AND (brain abscess) AND (carbapenem) AND (meningitis post-surgical) AND (penicillin) AND (shunt infection) AND (survive more than 4 days) AND NOT (rimethoprim/sulphamethoxazole))"}
```
