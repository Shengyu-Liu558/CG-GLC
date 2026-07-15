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
{"candidate_id": "LLM02876", "doc_id": "NCT03497598_inc", "case_bucket": "or", "source_criterion": "Women = 3 UTIs within the last 12 months or = 2 UTIs within the last 6 months; Laboratory urine culture: <103 CFUs Age > 18 years", "candidate_expression": "((Age > 18 years) AND (Laboratory urine culture <103 CFUs) AND (Women) AND ((UTIs = 2 within the last 6 months) OR (UTIs = 3 within the last 12 months)))"}
{"candidate_id": "LLM02877", "doc_id": "NCT02747940_inc", "case_bucket": "or", "source_criterion": "Control: devoid of any systemic or neurological diseases Chronic migraine: by ICHD-III (International Classification of Headache Disorder) criteria Fibromyalgia: by ACR (American College of Rheumatology) 2010 criteria", "candidate_expression": "((Chronic migraine ICHD-III International Classification of Headache Disorder) AND (Fibromyalgia ACR 2010 criteria American College of Rheumatology) AND ((neurological diseases) OR (systemic diseases)))"}
{"candidate_id": "LLM02878", "doc_id": "NCT02242188_exc", "case_bucket": "or", "source_criterion": "preterm delivery (<37 weeks of gestation) birth weight < 2500 g multiple pregnancy major illness or congenital anomaly being <50% breastfed at the time of inclusion food allergy anaemia (Hb <105 g/L [10.5 g/dL]) at inclusion, lack of informed consent", "candidate_expression": "((10.5 g/dL) AND (< 2500 g) AND (<105 g/L) AND (<37 weeks) AND (<50%) AND (Hb) AND (anaemia) AND (at inclusion) AND (at the time of inclusion) AND (birth weight) AND (breastfed) AND (congenital anomaly) AND (food allergy) AND (gestation) AND (lack of informed consent) AND (major illness) AND (multiple pregnancy) AND (preterm delivery))"}
{"candidate_id": "LLM02879", "doc_id": "NCT02339974_exc", "case_bucket": "or", "source_criterion": "Heart Team assessment of operability (the heart team considers the patient to be a good surgical candidate). Evidence of an acute myocardial infarction = 1 month (30 days) before the intended treatment [defined as: Q wave MI, or non-Q wave MI with total CK elevation of CK-MB = twice normal in the presence of MB elevation and/or troponin level elevation (WHO definition)]. Untreated, severe, left sided valvular heart disease including mitral regurgitation or stenosis, and aortic regurgitation or stenosis. Mean pulmonary artery pressures =40mmHG and PVR >4 woods units as assessed by right heart catheterization. Any therapeutic invasive cardiac procedure resulting in a permanent implant that is performed within 30 days of the index procedure. Examples of permanent implant would include any new heart valve. Implantation of a permanent pacemaker is excluded. Patients with planned concomitant surgical or transcatheter ablation for Atrial Fibrillation. Leukopenia (WBC < 3000 cell/mL), acute anemia (Hgb < 9 g/dL), Thrombocytopenia (Plt < 50,000 cell/mL). Hemodynamic or respiratory instability requiring inotropic support, mechanical ventilation or mechanical heart assistance within 30 days of screening evaluation. Need for emergency surgery for any reason. Left ventricular ejection fraction <40%. Echocardiographic evidence of intracardiac mass, thrombus or vegetation. Active upper GI bleeding within 3 months (90 days) prior to procedure. A known contraindication or hypersensitivity to all anticoagulation regimens, or inability to be anticoagulated for the study procedure. Recent CVA clinically confirmed (by neurologist) or neuroimaging confirmed stroke or transient ischemic attack (TIA) within 6 months (180 days) of the procedure. Estimated life expectancy < 1 year from conditions other than TR. Expectation that patient will not improve despite treatment of tricuspid regurgitation Currently participating in another investigational cardiac device study or any other clinical trial, including drugs or biologics. Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials. Active bacterial endocarditis within 6 months (180 days) of procedure. Patients with signs or symptoms of SVC syndrome, or hepatic cirrhosis not felt due to passive congestion from TR.", "candidate_expression": "((< 1 year) AND (< 3000 cell/mL) AND (< 50,000 cell/mL) AND (< 9 g/dL) AND (<40%) AND (= 1 month (30 days) before the intended treatment) AND (=40mmHG) AND (>4 woods units) AND (Active) AND (Atrial Fibrillation) AND (CVA) AND (Echocardiographic) AND (Estimated life expectancy) AND (Heart Team assessment of operability) AND (Hgb) AND (Left ventricular ejection fraction) AND (Mean pulmonary artery pressures) AND (Need for) AND (PVR) AND (Plt) AND (Untreated) AND (WBC) AND (acute myocardial infarction) AND (anticoagulated) AND (anticoagulation regimens) AND (bacterial endocarditis) AND (cardiac procedure) AND (clinically confirmed (by neurologist)) AND (concomitant) AND (confirmed) AND (emergency surgery) AND (excluded) AND (for the study procedure) AND (heart team considers the patient to be a good surgical candidate) AND (heart valve) AND (inability) AND (invasive) AND (left sided) AND (neuroimaging) AND (of procedure) AND (passive congestion from TR) AND (permanent implant) AND (permanent pacemaker) AND (planned) AND (procedure) AND (right heart catheterization) AND (screening evaluation) AND (severe) AND (study procedure) AND (the index procedure) AND (the procedure) AND (therapeutic) AND (upper GI bleeding) AND (valvular heart disease) AND (within 3 months (90 days) prior to procedure) AND (within 30 days of screening evaluation) AND (within 30 days of the index procedure) AND (within 6 months (180 days) of procedure) AND (within 6 months (180 days) of the procedure) AND ((aortic regurgitation) OR (aortic stenosis) OR (mitral regurgitation) OR (mitral stenosis)) AND ((surgical ablation) OR (transcatheter ablation)) AND ((Leukopenia) OR (Thrombocytopenia) OR (acute anemia)) AND ((inotropic support) OR (mechanical heart assistance) OR (mechanical ventilation)) AND ((Hemodynamic instability) OR (respiratory instability)) AND ((intracardiac mass) OR (intracardiac thrombus) OR (intracardiac vegetation)) AND ((contraindication) OR (hypersensitivity)) AND ((stroke) OR (transient ischemic attack (TIA))) AND ((SVC syndrome) OR (hepatic cirrhosis)))"}
{"candidate_id": "LLM02880", "doc_id": "NCT01491295_inc", "case_bucket": "or", "source_criterion": "HBsAg-positive for more than 6 months (HBeAg-positive or HBeAg-negative). Age > 20 y/o. Under lamivudine/adefovir treatment for more than 1 year due to previous lamivudine resistance (LAM-R), current HBV DNA is undetectable (< 20 IU/ml) during enrollment.", "candidate_expression": "((< 20 IU/ml) AND (> 20 y/o) AND (Age) AND (HBV DNA) AND (HBeAg) AND (HBsAg) AND (LAM-R) AND (adefovir) AND (during enrollment) AND (enrollment) AND (lamivudine) AND (lamivudine resistance) AND (more than 1 year) AND (more than 6 months) AND (negative) AND (positive) AND (undetectable))"}
{"candidate_id": "LLM02881", "doc_id": "NCT02350439_inc", "case_bucket": "scope", "source_criterion": "1. Age 18-80 years 2. Patients with at least 1 ≥50% stenosis in a coronary vessel, subjected to FFR assessment, who exhibit variation in Pd / Pa ratio ≥ 0.05 (e.g. difference of max Pd/Pa minus min Pd/Pa) during steady state hyperaemia (determined by visual assessment). 3. Written informed consent", "candidate_expression": "((18-80 years) AND (Age) AND (FFR assessment) AND (Pd / Pa ratio) AND (at least 1) AND (hyperaemia) AND (max Pd/Pa) AND (min Pd/Pa) AND (steady state) AND (stenosis in a coronary vessel) AND (variation in Pd / Pa ratio) AND (visual assessment) AND (≥ 0.05) AND (≥50%))"}
{"candidate_id": "LLM02882", "doc_id": "NCT01715584_exc", "case_bucket": "or", "source_criterion": "patient refusal age less than 40 or over 80 years combined surgical procedures emergency surgery Left ventricular ejection fraction less than 50 per cent calculated creatinine clearance less than 60 mL per minute", "candidate_expression": "((Left ventricular ejection fraction) AND (age) AND (calculated creatinine clearance) AND (combined surgical procedures) AND (emergency surgery) AND (less than 50 per cent) AND (less than 60 mL per minute) AND (patient refusal) AND ((less than 40) OR (over 80 years)))"}
{"candidate_id": "LLM02883", "doc_id": "NCT03519568_inc", "case_bucket": "or", "source_criterion": "aged = 6 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures the subjects have completed the basic immunization of 2 needle recombinant hepatitis B vaccine, there is no inoculation history of EV71 vaccine, and no history of EV71 infection the last vaccination intervals = 14 days temperature = 37<U+2103> aged = 6 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days temperature = 37<U+2103> aged = 8 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days and the last attenuated live vaccine intervals=28days temperature = 37<U+2103> aged = 8 months sign the informed consent form the legal guardians participate in all the planned follow-up and be able to comply with all research procedures there is no inoculation history of EV71 vaccine, and there is no history of EV71 infection the last vaccination intervals = 14 days and the last attenuated live vaccine intervals = 28 days temperature = 37<U+2103>", "candidate_expression": "((2) AND (= 14 days) AND (= 28 days) AND (= 37<U+2103>) AND (= 6 months) AND (= 8 months) AND (=28days) AND (EV71 infection) AND (EV71 vaccine) AND (aged) AND (history) AND (inoculation) AND (last attenuated live vaccine intervals) AND (last vaccination intervals) AND (no) AND (sign the informed consent form) AND (temperature) AND (the legal guardians participate in all the planned follow-up and be able to comply with all research procedures) AND ((EV71 infection) OR (inoculation) OR (needle recombinant hepatitis B vaccine)))"}
{"candidate_id": "LLM02884", "doc_id": "NCT03106389_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02885", "doc_id": "NCT00094861_exc", "case_bucket": "or", "source_criterion": "Metastatic disease (M1)/stage 4 NSCLC Pleural or pericardial effusion greater than 100 ml in volume as documented by appropriate imaging (positron emission tomography [PET], computed tomography [CT] scan or ultrasound). If an effusion greater than 100 ml is documented by cytology to be free from malignancy and the investigator feels the patient is capable of receiving chemo/radiotherapy for their primary disease/ NSCLC, the investigator should discuss the patient with the study physician at Amgen. Effusions smaller than 100 ml would be acceptable, unless the investigator suspects that the effusion is malignant, in which case the effusions should be evaluated by cytology. Sponsor approval must be obtained before patient is randomized. Plan to remove the tumor surgically before completing the protocol chemo/radiotherapy course Shielding of any part of the esophagus during radiotherapy (including posterior spinal cord shielding) Prior chemotherapy, radiotherapy, or surgery for NSCLC Prior invasive malignancy during the past 3 years other than non-melanomatous skin cancer. Note: Patients with prior surgically-cured malignancies [eg, stage I breast cancer or prostate cancer, in-situ carcinoma of the cervix, etc] are not excluded; however, sponsor approval must be obtained before patient is randomized. Presence or history of dysphagia or conditions predisposing to dysphagia (eg, uncontrolled gastroesophageal reflux disease [GERD], dyspepsia, etc) History of pancreatitis Four weeks or less since completion of treatment using an investigational product/device in another clinical study or presence of any unresolved toxicity from previous treatment Previous treatment on this study or with a fibroblast growth factor Known to be sero-positive for human immunodeficiency virus (HIV), hepatitis C virus (HCV), or hepatitis B virus (HBV) Pregnant or breastfeeding women Known sensitivity to E. coli derived products Compromised ability of the patient to give written informed consent and/or to comply with study procedures Refusal to sign an informed consent form to participate in this study, and sign the hospital information release form, if applicable Unwilling or unable to complete the patient reported outcome (PRO) questionnaires Psychological, social, familial, or geographical reasons that would prevent regular follow-up", "candidate_expression": "(((M1)/stage 4) AND (CT) AND (Compromised ability) AND (E. coli derived) AND (Four weeks or less since completion of treatment) AND (GERD) AND (History of) AND (Metastatic disease NSCLC) AND (NSCLC) AND (PET) AND (Plan to remove the tumor surgically) AND (Pleural effusion) AND (Pregnant) AND (Previous) AND (Prior) AND (Refusal to) AND (Shielding) AND (another clinical study) AND (any part of) AND (are not) AND (before completing the protocol chemo/radiotherapy course) AND (breastfeeding) AND (chemotherapy) AND (completion of treatment) AND (computed tomography scan) AND (conditions predisposing to dysphagia) AND (during the past 3 years) AND (dyspepsia) AND (dysphagia) AND (esophagus) AND (fibroblast growth factor) AND (gastroesophageal reflux disease) AND (give written informed consent) AND (greater than 100 ml in volume) AND (hepatitis B virus (HBV)) AND (hepatitis C virus (HCV)) AND (history of) AND (human immunodeficiency virus (HIV)) AND (invasive) AND (investigational device) AND (investigational product) AND (malignancy) AND (non-melanomatous skin cancer) AND (other than) AND (pancreatitis) AND (pericardial effusion) AND (positron emission tomography) AND (posterior spinal cord shielding) AND (previous) AND (products) AND (radiotherapy) AND (sensitivity) AND (sero-positive) AND (sero-positive for hepatitis B virus (HBV)) AND (sero-positive for hepatitis C virus (HCV)) AND (sero-positive for human immunodeficiency virus (HIV)) AND (sign an informed consent form) AND (sign the hospital information release form) AND (surgery) AND (surgically-cured malignancies) AND (toxicity) AND (treatment) AND (ultrasound) AND (uncontrolled) AND (unresolved) AND (women))"}
{"candidate_id": "LLM02886", "doc_id": "NCT01850147_inc", "case_bucket": "or", "source_criterion": "Histologic or cytologic diagnosis of stage IIIB/IV NSCLC ECOG PS: 0,1 Unidimensional or bi-dimensional measurable disease Receive prior treatment including first-line platinum-based chemotherapy, standard second-line chemotherapy and 1 EGF/EGFR inhibitor Evidence of disease progression Life expectancy >12 weeks Neutrophils > 1.5 109/l, Platelets > 100 109/l, Hemoglobin > 9g/dl, Total bilirubin < 1.5 UNL, AST (SGOT) and ALT (SGPT) < 2.5 UNL, Alkaline phosphatases < 5 UNL, Creatinine < 1 UNL", "candidate_expression": "((0,1) AND (< 1 UNL) AND (< 1.5 UNL) AND (< 2.5 UNL) AND (< 5 UNL) AND (> 1.5 109/l) AND (> 100 109/l) AND (> 9g/dl) AND (>12 weeks) AND (ALT (SGPT)) AND (AST (SGOT)) AND (Alkaline phosphatases) AND (Creatinine) AND (ECOG PS) AND (Evidence) AND (Evidence of disease progression) AND (Hemoglobin) AND (Histologic) AND (Life expectancy) AND (NSCLC) AND (Neutrophils) AND (Platelets) AND (Total bilirubin) AND (cytologic) AND (disease progression) AND (measurable) AND (stage IIIB/IV) AND (standard) AND (treatment) AND ((1 EGF/EGFR inhibitor) OR (platinum-based chemotherapy) OR (second-line chemotherapy)))"}
{"candidate_id": "LLM02887", "doc_id": "NCT02557386_inc", "case_bucket": "scope", "source_criterion": "Male sex ASA status I or II BMI between 20 and 34 kg/m2 Cruciate ligament of the knee reconstructive surgery No contraindications to general and regional anesthesia", "candidate_expression": "((ASA status I or II) AND (BMI between 20 and 34 kg/m2) AND (Male) AND (general anesthesia) AND (reconstructive surgery Cruciate ligament of the knee) AND (regional anesthesia) AND NOT (contraindications))"}
{"candidate_id": "LLM02888", "doc_id": "NCT03500211_inc", "case_bucket": "or", "source_criterion": "Pregnant patients who require a scheduled or non-urgent cesarean birth Patient able to receive neuraxial analgesia Patient able to give verbal and written consent for both cesarean birth and study", "candidate_expression": "((Patient able to give verbal and written consent for both cesarean birth and study) AND (Pregnant) AND (able to receive) AND (cesarean birth) AND (neuraxial analgesia) AND ((non-urgent) OR (scheduled)))"}
{"candidate_id": "LLM02889", "doc_id": "NCT03096613_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older, male or female. Systolic heart failure with New York Heart Association (NYHA) class II-III. Left ventricular ejection fraction (LVEF) less than 40% by echocardiography during screening and randomization. SCH (TSH: upper limits of normal (ULN) -10mIU/L, and FT4 level within reference range). Having received standard HF therapy for at least 2 weeks, having reached target dose or max tolerable dose. Provided informed consent.", "candidate_expression": "((18 years or older) AND (Aged) AND (FT4 level) AND (Left ventricular ejection fraction (LVEF)) AND (New York Heart Association (NYHA)) AND (SCH) AND (Systolic heart failure) AND (TSH) AND (class II-III) AND (during screening and randomization) AND (echocardiography) AND (for at least 2 weeks) AND (less than 40%) AND (standard HF therapy) AND (upper limits of normal (ULN) -10mIU/L) AND (within reference range) AND ((max tolerable dose) OR (target dose)) AND ((female) OR (male)))"}
{"candidate_id": "LLM02890", "doc_id": "NCT02637076_inc", "case_bucket": "or", "source_criterion": "current diagnosis of narcolepsy with cataplexy OR healthy control", "candidate_expression": "((cataplexy) AND (healthy) AND (narcolepsy))"}
{"candidate_id": "LLM02891", "doc_id": "NCT03120728_inc", "case_bucket": "or", "source_criterion": "Healthy, women ages 18 to 39yo with BMI <30 Regular menstrual cycles with duration between 24-35 days Completion of screening visit where ovulation will be assessed with blood draw for progesterone level (must be 5ng/mL or greater) Not seeking pregnancy during the study period Use of a non-hormonal form of contraception, such as: sterilization (tubal ligation, Essure), copper IUD (intrauterine device), barrier methods or abstinence Must speak English or Spanish", "candidate_expression": "((18 to 39yo) AND (5ng/mL or greater) AND (<30) AND (BMI) AND (Essure) AND (Healthy) AND (Not seeking pregnancy during the study period) AND (Regular menstrual cycles) AND (abstinence) AND (ages) AND (barrier methods) AND (between 24-35 days) AND (copper IUD) AND (duration) AND (intrauterine device) AND (non-hormonal form of contraception) AND (progesterone level) AND (sterilization) AND (tubal ligation) AND (women))"}
{"candidate_id": "LLM02892", "doc_id": "NCT00343668_exc", "case_bucket": "or", "source_criterion": "Other tumor type than adenocarcinoma Central nervous system (CNS) metastases or prior radiation for CNS metastases Gastric outlet obstruction or intestinal obstruction Evidence of gastrointestinal bleeding The patient has bony lesions as the sole evaluable disease. Past or concurrent history of neoplasm other than stomach cancer, except for curatively treated non-melanoma skin cancer or in situ carcinoma of the cervix uteri Pregnant or lactating women, women of childbearing potential not employing adequate contraception Other serious illness or medical conditions Unstable cardiac disease despite treatment, myocardial infarction within 6 months prior to study entry History of significant neurologic or psychiatric disorders including dementia or seizures Active uncontrolled infection Other serious underlying medical conditions which could impair the ability of the patient to participate in the study Concomitant administration of any other experimental drug under investigation, or concomitant chemotherapy, hormonal therapy, or immunotherapy concomitant drug medication; The following drugs cause drug interaction with S-1. i. Warfarin, phenprocoumon: increase bleeding tendency ii. Increase blood concentration of phenytoin iii. sorivudine: inhibit DPD -> increase toxicity according to fluoropyrimidine iv. allopurinol : decrease activity of S-1", "candidate_expression": "((Active) AND (CNS metastases) AND (Central nervous system (CNS) metastases) AND (Concomitant) AND (Evidence of) AND (Gastric outlet obstruction) AND (History) AND (Increase) AND (Other) AND (Pregnant) AND (Unstable cardiac disease) AND (Warfarin) AND (ability of the patient to participate) AND (adenocarcinoma) AND (allopurinol) AND (bleeding tendency) AND (blood concentration of phenytoin) AND (bony lesions) AND (chemotherapy) AND (childbearing potential) AND (concomitant) AND (contraception) AND (curatively) AND (dementia) AND (drug) AND (evaluable disease) AND (except for) AND (experimental drug) AND (fluoropyrimidine) AND (gastrointestinal bleeding) AND (history of) AND (hormonal therapy) AND (immunotherapy) AND (in situ carcinoma of the cervix uteri) AND (increase) AND (infection) AND (intestinal obstruction) AND (lactating) AND (medical conditions) AND (medication) AND (myocardial infarction) AND (neoplasm) AND (neurologic disorders) AND (non-melanoma skin cancer) AND (not employing) AND (other than) AND (phenprocoumon) AND (psychiatric disorders) AND (radiation) AND (seizures) AND (serious illness) AND (serious medical conditions) AND (sorivudine) AND (stomach cancer) AND (the sole) AND (treated) AND (treatment) AND (tumor) AND (uncontrolled) AND (within 6 months prior to study entry) AND (women))"}
{"candidate_id": "LLM02893", "doc_id": "NCT01410890_exc", "case_bucket": "other", "source_criterion": "The patient is participating in another clinical study using an investigational product. The patient, in the opinion of the Investigator, is unable to adhere to the requirements of the study.", "candidate_expression": "(The patient is participating in another clinical study using an investigational product)"}
{"candidate_id": "LLM02894", "doc_id": "NCT00461136_inc", "case_bucket": "scope", "source_criterion": "Male and/or female patients from 30-80 years of age with a diagnosis of Type 2 diabetes (WHO criteria). Incipient and established diabetic nephropathy (urinary albumin excretion ≥ 100 mg/day but ≤ 2000 mg/day). Glomerular filtration rate (GFR) ≥ 40 ml/min (estimated using Modification of Diet in Renal Disease (MDRD) formula) in the last 4 months. Female patients must be postmenopausal or must have had a bilateral oophorectomy or must have been surgically sterilized or hysterectomized at least 6 months prior to screening. To be eligible patients must fulfill the following criteria: Patients on ongoing hypertensive therapy must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1) AND patients must be on stable antihypertensive medications for at least 8 weeks prior to baseline (Day -1).; Newly diagnosed hypertensive patients must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1). Patients must be on stable hypoglycemic medications for at least 8 weeks prior to Visit 2 ( Day -1). Patients must be willing and medically able to discontinue all Angiotensin-converting enzyme inhibitor (ACEI), Angiotensin receptor blocker (ARB), aldosterone receptor antagonist and potassium sparing diuretic medications for the duration of the study. Oral body temperature within the range 35.0-37.5 °C Able to provide written informed consent prior to study participation. . Able to communicate well with the investigator and comply with the requirements of the study.", "candidate_expression": "((30-80 years) AND (35.0-37.5 °C) AND (Able to communicate well) AND (Female) AND (Glomerular filtration rate (GFR)) AND (Modification of Diet in Renal Disease (MDRD) formula) AND (Newly diagnosed) AND (Oral body temperature) AND (Type 2 diabetes) AND (Visit 2) AND (antihypertensive medications) AND (at baseline (Day -1)) AND (at least 6 months prior to screening) AND (at least 8 weeks prior to Visit 2) AND (at least 8 weeks prior to baseline) AND (baseline) AND (baseline (Day -1)) AND (bilateral oophorectomy) AND (blood pressure) AND (comply with the requirements of the study) AND (diabetic nephropathy) AND (hypertensive patients) AND (hypertensive therapy) AND (hypoglycemic medications) AND (hysterectomized) AND (in the last 4 months) AND (lower than 170/105 mm Hg) AND (of age) AND (postmenopausal) AND (prior to study participation) AND (stable) AND (study participation) AND (surgically sterilized) AND (urinary albumin excretion) AND (written informed consent) AND (≤ 2000 mg/day) AND (≥ 100 mg/day) AND (≥ 135/85 mm Hg) AND (≥ 40 ml/min))"}
{"candidate_id": "LLM02895", "doc_id": "NCT02764476_exc", "case_bucket": "or", "source_criterion": "Nonfluency or inability to communicate in English spoken language Inability to participate or attend biweekly 30 minute session over 14 weeks Frank psychosis Active self harm urges Serious medical illness Active substance or alcohol use or dependence that could interfere with participation Diagnoses of mental retardation, dementia or delirium Pregnant women", "candidate_expression": "((Pregnant) AND (Serious) AND (alcohol use or dependence) AND (delirium) AND (dementia) AND (medical illness Serious) AND (mental retardation) AND (psychosis Frank Active) AND (self harm urges) AND (substance use or dependence) AND (that could interfere with participation) AND (women))"}
{"candidate_id": "LLM02896", "doc_id": "NCT02942303_inc", "case_bucket": "other", "source_criterion": "Consecutive 30 female patients presenting to our clinic for brow lifting with botulinum toxin will be randomized to receive one of the two injection techniques", "candidate_expression": "((botulinum toxin) AND (brow lifting) AND (female 30))"}
{"candidate_id": "LLM02897", "doc_id": "NCT01807897_exc", "case_bucket": "or", "source_criterion": "Hospitalization for acute decompensated HF within previous 30 days Hospitalization for myocardial infarction or cardiac surgery within previous 90 days Presence of a left ventricular assist device History of heart transplantation Poorly controlled hypertension (>170/>110) Poorly controlled diabetes (HbA1c > 9.0) Severe renal failure with estimated glomerular filtration rate <30 ml/min Prior stroke with functional impairment or other severe, uncontrolled medical problems that may impair ability to participate in the study exams, based on medical history and review of medical records Severe chronic insomnia, with reported usual sleep duration <4 hours Severe daytime sleepiness, defined as Epworth Sleepiness Scale score 18 or higher or a report of falling asleep driving during the previous year, and deemed a safety risk by study physician Awake resting oxyhemoglobin saturation <89% Pregnancy Smoking by subject or other person in the subject's bedroom, or other open flame in bedroom Current use of a positive airway pressure device (including continuous or bi-level positive airway pressure or adaptive servo-ventilation) or supplemental oxygen therapy", "candidate_expression": "((Epworth Sleepiness Scale score 18 or higher) AND (HbA1c > 9.0) AND (Hospitalization) AND (Hospitalization within previous 30 days) AND (Pregnancy) AND (acute decompensated HF) AND (adaptive servo-ventilation) AND (bi-level positive airway pressure) AND (cardiac surgery) AND (chronic insomnia sleep duration) AND (continuous airway pressure) AND (daytime sleepiness) AND (diabetes Poorly controlled) AND (estimated glomerular filtration rate <30 ml/min) AND (functional impairment) AND (heart transplantation) AND (hypertension Poorly controlled) AND (left ventricular assist device) AND (myocardial infarction) AND (oxyhemoglobin saturation Awake resting <89%) AND (positive airway pressure device) AND (renal failure Severe) AND (stroke) AND (supplemental oxygen therapy))"}
{"candidate_id": "LLM02898", "doc_id": "NCT02560766_exc", "case_bucket": "or", "source_criterion": "History of a primary sleep disorder other than RLS that may significantly affect the symptoms of RLS. Serum ferritin level < 20 ng/mL at screening. History of allergy, hypersensitivity, or intolerance to HORIZANT or any other gabapentin products (eg, Neurontin®, Gralise®). Suffering from a movement disorder that could mimic or confound the accurate diagnosis of RLS (eg, Tourette's syndrome, tic disorder, periodic limb movement disorder [PLMD], sleep disorders). Currently meet Diagnostic and Statistical Manual of Mental Disorders - Fifth Edition (DSM-5) criteria for substance use disorder, or history thereof, within 12 months before dosing. Current or past history of any significant psychiatric disorder including, but not limited to, depression (treatment with antidepressants), bipolar disorder, or schizophrenia. Diagnosis of attention-deficit hyperactivity disorder (ADHD) is allowed, provided the patient is not receiving medication(s) known to affect the assessment of RLS. History of suicidal behavior or suicidal ideation as indicated by the C-SSRS, administered at screening (the questionnaire is provided in Appendix 4), and as per investigator's judgment. History of seizure disorder or at increased risk for development of a seizure disorder including, but not limited to, complicated febrile seizure and history of significant head injury. Medical condition or disorder that would interfere with the action, absorption, distribution, metabolism, or excretion of gabapentin enacarbil, or, in the investigator's judgment is considered to be clinically significant and may pose a safety concern, or, could interfere with the accurate assessment of safety or efficacy, or could potentially affect a patient's safety or study outcome. Clinically significant abnormal laboratory result or physical examination finding not resolved by the time of baseline assessments.", "candidate_expression": "((ADHD) AND (DSM-5) AND (Diagnostic and Statistical Manual of Mental Disorders - Fifth Edition) AND (Gralise) AND (HORIZANT) AND (Neurontin) AND (PLMD) AND (Serum ferritin < 20 ng/mL) AND (Tourette's syndrome) AND (allergy) AND (allowed) AND (antidepressants) AND (attention-deficit hyperactivity disorder) AND (bipolar disorder) AND (complicated febrile seizure) AND (depression) AND (gabapentin) AND (head injury) AND (hypersensitivity) AND (intolerance) AND (movement disorder) AND (periodic limb movement disorder) AND (primary sleep disorder) AND (psychiatric disorder significant) AND (schizophrenia) AND (seizure disorder) AND (sleep disorders) AND (substance use disorder within 12 months) AND (suicidal behavior) AND (suicidal ideation) AND (tic disorder) AND NOT (RLS))"}
{"candidate_id": "LLM02899", "doc_id": "NCT03387059_inc", "case_bucket": "or", "source_criterion": "All infertile women treated with intracytoplasmic sperm injection (ICSI)/Fertilization in Vitro and Embryo Transfer (FIVET) Less than or equal to (<=) 1 previous failed embryo transfer Eumenorrheic normo-gonadotropic women Basal follicle-stimulating hormone (FSH) <=12 International unit per liter (IU/L) Anti-mullerian hormone (AMH) greater than (>) 1.1 nanogram per milliliter (ng/mL) Ovarian Reserve: number of antral follicles 2 millimeter (mm) between 6 <= antral follicle count (AFC) <= 16 Follicles > 16 mm at the triggering day between 5-14 Body Mass Index (BMI) between 18 <= BMI <= 27 kilogram per meter square (kg/m^2) Indication for Fresh Embryo transfer Normal uterine cavity on ultrasound exam (e.g., no presence of hydrosalpinx) Undergoing Assisted Reproductive Technique (ART) and oocyte maturation by human chorionic gonadotropin (HCG) triggering Progesterone (P4) serum level at the HCG triggering day <= 1.5 ng/mL (Day O/Randomization) Estradiol (E2) <= 3000 picogram/milliliter (pg/mL) at the human chorionic gonadotropin (HCG) triggering day (Day 0/Randomization) Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care Other protocol defined inclusion criteria could apply", "candidate_expression": "((<= 1.5 ng/mL) AND (<= 3000 picogram/milliliter (pg/mL)) AND (<=12 International unit per liter (IU/L)) AND (Anti-mullerian hormone (AMH)) AND (Assisted Reproductive Technique (ART)) AND (Basal follicle-stimulating hormone (FSH)) AND (Body Mass Index (BMI)) AND (Day 0/Randomization) AND (Day O/Randomization) AND (Estradiol (E2)) AND (Eumenorrheic) AND (Fertilization in Vitro and Embryo Transfer (FIVET)) AND (Follicles > 16 mm) AND (Fresh Embryo transfer) AND (Indication for) AND (Less than or equal to (<=) 1) AND (Normal uterine cavity) AND (Progesterone (P4) serum level) AND (Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care) AND (Undergoing) AND (at the HCG triggering day) AND (at the human chorionic gonadotropin (HCG) triggering day) AND (at the triggering day) AND (between 18 <= BMI <= 27 kilogram per meter square (kg/m^2)) AND (between 5-14) AND (between 6 <= antral follicle count (AFC) <= 16) AND (greater than (>) 1.1 nanogram per milliliter (ng/mL)) AND (human chorionic gonadotropin (HCG) triggering) AND (hydrosalpinx) AND (infertile) AND (intracytoplasmic sperm injection (ICSI)) AND (no presence of) AND (normo-gonadotropic) AND (number of antral follicles 2 millimeter (mm)) AND (oocyte maturation) AND (previous failed embryo transfer) AND (the HCG triggering day) AND (the human chorionic gonadotropin (HCG) triggering day) AND (ultrasound exam) AND (women))"}
{"candidate_id": "LLM02900", "doc_id": "NCT02245256_exc", "case_bucket": "or", "source_criterion": "Pediatric patients (under 18 years) Pregnancy Patients who are unresponsive at baseline, who have neurologic deficits at baseline, or who are allergic to dexmedetomidine", "candidate_expression": "((Pediatric) AND (Pregnancy) AND (allergic) AND (at baseline) AND (dexmedetomidine) AND (neurologic deficits) AND (under 18 years) AND (unresponsive) AND (years))"}
```
