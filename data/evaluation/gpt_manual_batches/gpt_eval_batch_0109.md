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
{"candidate_id": "LLM02701", "doc_id": "NCT02531971_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session Smokers (current use or use over the previous 2 months of nicotine-containing substances, including tobacco products (e.g. cigarettes, cigars, chewing tobacco, gum, patch or electronic cigarettes) Participation in any ongoing investigational drug trial/study or clinical drug trial/study History of chronic obstructive pulmonary disease or cor pulmonale, or substantially decreased respiratory reserve, hypoxia, hypercapnia or pre-existing respiratory depression Active positive Hepatitis B, C and HIV serologies Positive urine drug screening test Use of any prescription medication during the session 0 to 30 days or over-the counter medication e.g. antihistamines or topical corticosteroids (vitamin, herbal supplements and birth control medications not included) during the session 0 to 3 days before entry to the study Use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator with 72 hours prior to dosing (e.g. antihistamines, systemic or topical corticosteroids (within 3 weeks prior to dosing), cyclosporine, tacrolimus, cytotoxic drugs, immune globulin, Bacillus Calmette-Guerin (BCG), monoclonal antibodies, radiation therapy) Use of monoamine oxidase inhibitors 21 days prior to study Current use of mixed agonist/antagonist (such as pentazocine, nalbuphine or butorphanol) and partial agonist (buprenorphine) analgesics Current use of anticholinergics or other medications with anticholinergic activity Consumption of beverages containing alcohol, grapefruit juice, Seville oranges, or quinine (e.g. tonic water) or foods containing poppy seeds in the last 72 hours. Donation or loss of greater than one pint of blood within 60 days of entry to the study Any prior serious adverse reaction or hypersensitivity to fentanyl, morphine, codeine, hydrocodone, hydromorphone, oxycodone, oxymorphone, naltrexone or naloxone or any of the inactive ingredients in the TDDS (polyester/ethyl vinyl acetate, polyacrylate adhesive, silicone adhesive, dimethicone NF, or polyolefin) Have a diagnosis of schizophrenia or other major psychiatric diagnosis or mental illness (e.g. major depression) Medical history of personal drug or alcohol addiction or abuse Any condition that would, in the opinion of the MAI, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol Inability to communicate or cooperate with the investigators Subject has an obvious difference in skin color between arms or the presence of a skin condition, excessive hair at the application site (upper arm), sunburn, raised moles and scars, open sore, scar tissue, tattoo, or coloration that would interfere with placement of test articles, skin assessment, or reactions to drug Failure to pass opioid dependence challenge test on the first day study day of any study session (i.e., before taking the first dose of naltrexone hydrochloride). Each subject will be injected subcutaneously with naloxone hydrochloride (0.8 mg injection) and will be observed for 45 minutes for signs and symptoms of opioid withdrawal. Within 4 weeks prior to dosing, use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator", "candidate_expression": "((21 days prior to study) AND (HIV serologies) AND (Hepatitis B serologies) AND (Hepatitis C serologies) AND (Inability to communicate or cooperate with the investigators) AND (Participation in any ongoing investigational drug trial/study or clinical drug trial/study) AND (Positive) AND (Smokers) AND (TDDS) AND (Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session) AND (abuse) AND (addiction) AND (alcohol) AND (anticholinergics) AND (buprenorphine) AND (butorphanol) AND (chronic obstructive pulmonary disease) AND (codeine) AND (cor pulmonale,) AND (decreased respiratory reserve) AND (dimethicone NF) AND (drug) AND (fentanyl) AND (hydrocodone) AND (hydromorphone) AND (hypercapnia) AND (hypersensitivity) AND (hypoxia) AND (major depression) AND (major psychiatric diagnosis) AND (mental illness) AND (monoamine oxidase inhibitors) AND (morphine) AND (nalbuphine) AND (naloxone) AND (naltrexone) AND (oxycodone) AND (oxymorphone) AND (pentazocine) AND (polyacrylate adhesive) AND (polyester/ethyl vinyl acetate) AND (polyolefin) AND (positive) AND (respiratory depression) AND (schizophrenia) AND (silicone adhesive) AND (study) AND (urine drug screening test))"}
{"candidate_id": "LLM02702", "doc_id": "NCT02745704_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative and anti-HBeAg positive. Hepatitis B surface antigen (HBsAg) positive and <1500 IU/mL. Hepatitis B virus DNA not detectable(Roche Cobas).", "candidate_expression": "((<1500 IU/mL) AND (CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen) AND (Hepatitis B surface antigen) AND (Hepatitis B virus DNA) AND (NAs) AND (anti-HBeAg) AND (more than 12 months.) AND (negative) AND (not detectable) AND (positive))"}
{"candidate_id": "LLM02703", "doc_id": "NCT03304496_exc", "case_bucket": "or", "source_criterion": "Pregnant. Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent. With acute myocardial infarction with ST segment elevation in the first 12 hours from the onset of symptoms. With any acute coronary syndrome complicated with acute pulmonary edema, cardiogenic shock and / or malignant ventricular arrhythmias. In which a cardiac catheterization is planned a priori to be performed via femoral, brachial or ulnar. Patients in whom first attempt of arterial puncture is performed by 2nd year interventional cardiology fellow or by physician in charge. Participating in another clinical trial. Be allergic or have contraindications to nitroglycerin or other nitrates. Any phosphodiesterase 5 inhibitor (sildenafil, tadalafil, avanafil, vardenafil) has been taken within 72 hours prior to the study.", "candidate_expression": "((Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent) AND (Pregnant) AND (ST segment elevation) AND (acute coronary syndrome) AND (acute myocardial infarction in the first 12 hours from the onset of symptoms) AND (acute pulmonary edema) AND (allergic) AND (avanafil) AND (cardiac catheterization femoral brachial ulnar) AND (cardiogenic shock) AND (contraindications) AND (nitrates) AND (nitroglycerin) AND (phosphodiesterase 5 inhibitor within 72 hours prior to the study) AND (sildenafil) AND (tadalafil) AND (vardenafil) AND (ventricular arrhythmias malignant))"}
{"candidate_id": "LLM02704", "doc_id": "NCT02555163_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed at the out-patient cystoscopy with papillary bladder tumour will be legible for inclusion", "candidate_expression": "((cystoscopy) AND (out-patient) AND (papillary bladder tumour))"}
{"candidate_id": "LLM02705", "doc_id": "NCT02109081_exc", "case_bucket": "or", "source_criterion": "1) preoperative diagnosis of delirium or dementia; 2) MMSE score of = 20 out of 30 on preoperative testing (more than mild cognitive impairment) or delirium on preoperative CAM testing; 3) language barriers that would preclude testing; 4) preoperative steroid use within 3 days of surgery; or 5) anticipation of postoperative intubation.", "candidate_expression": "((= 20 out of 30) AND (CAM testing) AND (MMSE score) AND (anticipation) AND (cognitive impairment) AND (delirium) AND (intubation) AND (language barriers) AND (more than mild) AND (postoperative) AND (preoperative) AND (steroid) AND (surgery) AND (within 3 days of surgery) AND ((delirium) OR (dementia)))"}
{"candidate_id": "LLM02706", "doc_id": "NCT02940912_inc", "case_bucket": "or", "source_criterion": "Idiopathic Parkinson's disease ( Hughes AJ et al. 2001) Patients with motor fluctuations Chronic Insomnia disorder criteria according to the criteria of DMS- V ( American Psychiatric Association, 2013) and insomnia severity index > 15 Able to use independently the device required for treatment by apomorphine Collection of written informed consent (legal obligation for any project under the public health law , bioethics laws and / or CNIL) . Affiliate to social security or beneficiary of such a regime", "candidate_expression": "((> 15) AND (Affiliate to social security) AND (Chronic Insomnia disorder) AND (Idiopathic) AND (Parkinson's disease) AND (apomorphine) AND (criteria of DMS- V) AND (device) AND (insomnia severity index) AND (motor fluctuations) AND (social security beneficiary))"}
{"candidate_id": "LLM02707", "doc_id": "NCT01857167_inc", "case_bucket": "or", "source_criterion": "1. Fasting glucose > 7.0 or have diabetes medication; 2. Male, 35-80 years; female, postmenopausal to 80 years; 3. Agree to participant in the trial.", "candidate_expression": "((35-80 years 35-80 years) AND (Agree to participant in the trial.) AND (Fasting glucose > 7.0) AND (Male 35-80 years) AND (diabetes) AND (diabetes medication) AND (female) AND (postmenopausal) AND (to 80 years))"}
{"candidate_id": "LLM02708", "doc_id": "NCT03226080_inc", "case_bucket": "other", "source_criterion": "ASA I-IV Age 55 or older Scheduled for operative repair of isolated intertrochanteric hip fracture", "candidate_expression": "((ASA I-IV) AND (Age 55 or older) AND (intertrochanteric hip fracture isolated) AND (operative repair Scheduled for isolated))"}
{"candidate_id": "LLM02709", "doc_id": "NCT01963754_inc", "case_bucket": "or", "source_criterion": "Single unit implant rehabilitation Maxilla and mandible Must accept treatment plan Must sign informed consent dental extraction performed at least 3 month prior Must have at least 6 mm of residual bone Absence of oral lesions keratinized tissue must be present", "candidate_expression": "((Absence) AND (Maxilla) AND (Must accept treatment plan) AND (Must sign informed consent) AND (Single unit implant rehabilitation) AND (at least 3 month prior) AND (at least 6 mm) AND (dental extraction) AND (keratinized tissue must be present) AND (mandible) AND (oral lesions) AND (residual bone))"}
{"candidate_id": "LLM02710", "doc_id": "NCT02371200_exc", "case_bucket": "other", "source_criterion": "1. Does not have a documented history of generalized seizures. 2. Has not had a GTC seizure within the last year AND is not expected to have a reduction of anti-epileptic drugs during their hospital admission. 3. Intracranial EEG electrodes are being used 4. The subject's upper arm circumference not adequate for proper fit of the EMG monitor (less than 14cm). 5. Pregnant female. 6. Subject/Caregiver is unable to provide consent.", "candidate_expression": "((GTC seizure) AND (Intracranial EEG electrodes) AND (Pregnant) AND (Subject/Caregiver is unable to provide consent.) AND (adequate for proper fit of the EMG monitor) AND (anti-epileptic drugs) AND (during their hospital admission) AND (female) AND (generalized seizures) AND (history) AND (hospital admission) AND (less than 14cm) AND (not) AND (reduction of anti-epileptic drugs) AND (upper arm circumference) AND (within the last year))"}
{"candidate_id": "LLM02711", "doc_id": "NCT02894645_inc", "case_bucket": "other", "source_criterion": "Confirmed diagnosis of non-Burkitt B-lineage ALL 1 to 17 years of age (before 18th birthday) Renal function within normal range for age Liver function within normal range for age Able to participate in the full 2 years of treatment", "candidate_expression": "((1 to 17 years) AND (Able to participate) AND (Confirmed) AND (Liver function) AND (Renal function) AND (age) AND (full 2 years) AND (non-Burkitt B-lineage ALL) AND (treatment) AND (within normal range for age))"}
{"candidate_id": "LLM02712", "doc_id": "NCT02464813_inc", "case_bucket": "or", "source_criterion": "Adolescent (10-21 years) undergoing spinal fusion for idiopathic scoliosis, spondylolisthesis or Scheuermann kyphosis. Posterior spinal fusion No contraindication for Pregabalin use ASA I-III Written informed consent", "candidate_expression": "((ASA I-III) AND (Adolescent) AND (Posterior spinal fusion) AND (Pregabalin) AND (Scheuermann kyphosis) AND (Written informed consent) AND (idiopathic scoliosis) AND (spinal fusion) AND (spondylolisthesis) AND (years 10-21 years) AND NOT (contraindication))"}
{"candidate_id": "LLM02713", "doc_id": "NCT02175186_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 80 years Patients undergoing percutaneous coronary intervention and need to take dual antiplatelet therapy continuously at least 12weeks Modified Lanza Score grade 0-1 measured by upper gastrointestinal endoscopy mild gastrointestinal symptom Creatinen in blood = 3mg/dl BUN = 50mg/dl Birilubin = 3mg/dl AST and ALT = 80U/L", "candidate_expression": "((ALT) AND (AST) AND (Age between 20 and 80 years) AND (BUN = 50mg/dl) AND (Birilubin = 3mg/dl) AND (Creatinen = 3mg/dl) AND (Modified Lanza Score grade 0-1) AND (gastrointestinal symptom mild) AND (upper gastrointestinal endoscopy) AND ((dual antiplatelet therapy continuously at least 12weeks) OR (percutaneous coronary intervention)))"}
{"candidate_id": "LLM02714", "doc_id": "NCT02863120_exc", "case_bucket": "or", "source_criterion": "Revision total knee arthroplasty Bilateral total knee arthroplasty Patients with inflammatory arthritis Patients with a body mass index (BMI) > 40 Allergy to ropivacaine, bupivacaine, or other local anesthetic agents Current use of opioid drugs Patients with a history of total or unicompartmental reconstruction of the affected joint Patients that have had a high tibial osteotomy or femoral osteotomy Patients with neuromuscular or neurosensory deficiency, which would limit the ability to assess pain levels Patients with a systemic or metabolic disorder leading to progressive bone deterioration Patients that are immunologically compromised, or receiving chronic steroids (>30 days), excluding inhalers Patients' bone stock is compromised by disease or infection, which cannot provide adequate support and/or fixation to the prosthesis Patients with knee fusion to the affected joint Patients with an active or suspected latent infection in or about the knee joint Patients that are prisoners", "candidate_expression": "((> 40) AND (>30 days) AND (Allergy) AND (BMI) AND (Bilateral total knee arthroplasty) AND (Revision total knee arthroplasty) AND (affected joint) AND (body mass index) AND (bone deterioration) AND (chronic) AND (excluding) AND (infection) AND (inflammatory arthritis) AND (inhalers) AND (knee fusion) AND (knee joint) AND (opioid) AND (prisoners) AND (progressive) AND (reconstruction) AND ((total) OR (unicompartmental)) AND ((femoral osteotomy) OR (high tibial osteotomy)) AND ((neuromuscular deficiency) OR (neurosensory deficiency)) AND ((metabolic disorder) OR (systemic disorder)) AND ((immunologically compromised) OR (steroids)) AND ((bupivacaine) OR (local anesthetic agents) OR (ropivacaine)))"}
{"candidate_id": "LLM02715", "doc_id": "NCT01993836_inc", "case_bucket": "other", "source_criterion": "Surgical patients 60 years of age or older Surgery scheduled to last at least 2 hours (including time for anesthesia induction, etc) English speaking ability. Ability to give informed consent", "candidate_expression": "((Ability to give informed consent) AND (English speaking ability) AND (Surgery scheduled to last at least 2 hours) AND (age 60 years or older))"}
{"candidate_id": "LLM02716", "doc_id": "NCT02680054_exc", "case_bucket": "other", "source_criterion": "HbA1c greater than 75 mmol/mol (9.0%) Child unwilling to agree to second insulin injection at a meal-time Untreated coeliac disease or other concomitant condition likely to affect BG control Food allergies (other than controlled Coeliac Disease) Vegetarians, vegans or patients with religious dietary restrictions (as the standard meal contains meat) Participant taking any glucose-containing medication concurrently", "candidate_expression": "((9.0%) AND (Child unwilling to agree to second insulin injection at a meal-time) AND (Coeliac Disease) AND (Food allergies) AND (HbA1c) AND (Untreated) AND (Vegetarians) AND (coeliac disease) AND (glucose-containing medication) AND (greater than 75 mmol/mol) AND (other))"}
{"candidate_id": "LLM02717", "doc_id": "NCT02705222_inc", "case_bucket": "or", "source_criterion": "Perimenopausal women complaining of abnormal uterine bleeding (menorrhagia, metrorrhagia, polymenorrhoea or polymenorrhagia) without local gynecological cause. Failure of medical treatment for at least 3 months.", "candidate_expression": "((Perimenopausal) AND (abnormal uterine bleeding) AND (medical treatment Failure) AND (women) AND NOT (local gynecological cause) AND ((menorrhagia) OR (metrorrhagia) OR (polymenorrhagia) OR (polymenorrhoea)))"}
{"candidate_id": "LLM02718", "doc_id": "NCT00718952_inc", "case_bucket": "or", "source_criterion": "Subjects aged 12-65. Confirmed idiopathic pulmonary hypertension, connective tissue disease associated pulmonary hypertension, congenital heart disease(with Eisenmenger syndrome) associated pulmonary hypertension. Baseline 6-minutes walking distance 150m-550m. WHO pulmonary hypertension function II-III with non-responder to calcium channel blockers. Documented written informed consent.", "candidate_expression": "((12-65) AND (150m-550m) AND (6-minutes walking distance) AND (Baseline) AND (Eisenmenger syndrome) AND (II-III) AND (WHO pulmonary hypertension function) AND (aged) AND (calcium channel blockers) AND (congenital heart disease) AND (connective tissue disease associated) AND (non-responder to calcium channel blockers) AND (written informed consent) AND ((idiopathic pulmonary hypertension) OR (pulmonary hypertension)))"}
{"candidate_id": "LLM02719", "doc_id": "NCT01497639_inc", "case_bucket": "or", "source_criterion": "ages of 7 and 75 years marked disability owing to primary generalized or segmental dystonia, despite optimal pharmacologic treatment disease duration of at least 5 years.", "candidate_expression": "((ages 7 and 75 years) AND (disability generalized) AND (disease duration at least 5 years) AND (dystonia primary segmental) AND (pharmacologic treatment optimal))"}
{"candidate_id": "LLM02720", "doc_id": "NCT02365870_inc", "case_bucket": "other", "source_criterion": "Diagnosis of DSM 5 Anxiety Disorder Stable medical history and general health On stable anti-parkinsonian therapy for 2 weeks before enrollment", "candidate_expression": "((DSM 5 Anxiety Disorder) AND (Stable general health) AND (Stable medical history) AND (anti-parkinsonian therapy) AND (before enrollment) AND (for 2 weeks) AND (stable))"}
{"candidate_id": "LLM02721", "doc_id": "NCT02056626_exc", "case_bucket": "or", "source_criterion": "abnormal renal function currently pregnant, or trying to become pregnant being treated with a beta-blocker use of illicit drugs", "candidate_expression": "((abnormal renal function) AND (beta-blocker) AND (illicit drugs) AND (pregnant currently) AND (pregnant trying to become) AND (treated))"}
{"candidate_id": "LLM02722", "doc_id": "NCT02781610_inc", "case_bucket": "or", "source_criterion": "Male or female =18 years of age at Visit 1 Documentation of a CF diagnosis Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR) prior to Visit 1 (US sites only) At the time of Visit 1, there is a plan to initiate IV antibiotics for a pulmonary exacerbation Performed spirometry at Visit 1 and Visit 2 and willing to perform spirometry at Visit 3 Completed the CRISS questionnaire at Visit 1 and Visit 2 and willing to complete the Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire at Visit 3 Willing to adhere to a specific treatment duration determined by initial response to treatment and subsequent randomization Willing to return for follow up Visit 3 Written informed consent obtained from the subject or subject's legal representative", "candidate_expression": "((=18 years) AND (At the time of Visit 1) AND (CF) AND (CRISS questionnaire) AND (Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire) AND (Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR)) AND (IV antibiotics) AND (US sites) AND (Visit 1) AND (Visit 2) AND (Visit 3) AND (Willing to) AND (Written informed consent) AND (age) AND (at Visit 1) AND (at Visit 2) AND (at Visit 3) AND (follow up Visit 3) AND (prior to Visit 1) AND (pulmonary exacerbation) AND (spirometry) AND (willing to complete) AND (willing to perform) AND ((Male) OR (female)) AND ((Visit 2) OR (at Visit 2)) AND ((from the subject) OR (from the subject's legal representative)))"}
{"candidate_id": "LLM02723", "doc_id": "NCT03444142_inc", "case_bucket": "other", "source_criterion": "Patients both sexes Age between 31 and 60 years Diagnosis of diabetes according ADA criteria:", "candidate_expression": "((Age) AND (between 31 and 60 years) AND (both sexes) AND (diabetes ADA criteria))"}
{"candidate_id": "LLM02724", "doc_id": "NCT02953873_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02725", "doc_id": "NCT00500500_exc", "case_bucket": "or", "source_criterion": "patient already treated by medicines which could interfere with the study low level of vitamin B12 and folate which are considered as clinically relevant clinically relevant pathologies (eg: pulmonary illness, cardiovascular illness; evolutive cancer, neurological illness, blood illness….)", "candidate_expression": "((folate level of low) AND (level of vitamin B12 low) AND ((blood illness) OR (cardiovascular illness) OR (evolutive cancer) OR (neurological illness) OR (pulmonary illness)))"}
```
