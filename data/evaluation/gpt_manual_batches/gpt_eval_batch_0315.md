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
{"candidate_id": "LLM07851", "doc_id": "NCT02715518_inc", "case_bucket": "or", "source_criterion": "Symptoms of ischaemia. New or presumed new significant ST-T wave changes Development of pathological Q waves on ECG. Imaging evidence of new or presumed new loss of viable myocardium or regional wall motion abnormality.", "candidate_expression": "((ECG) AND (Imaging) AND (ST-T wave changes) AND (Symptoms) AND (evidence) AND (ischaemia) AND (pathological Q waves) AND (significant) AND ((new) OR (presumed new)) AND ((loss of viable myocardium) OR (regional wall motion abnormality)) AND ((New) OR (presumed new)))"}
{"candidate_id": "LLM07852", "doc_id": "NCT01959061_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women Patients with severe organ dysfunction or failure With severe cardiovascular disease, or mental Extraliver metastases", "candidate_expression": "((Extraliver metastases) AND (Pregnant) AND (cardiovascular disease) AND (disease mental) AND (lactating) AND (metastases Extraliver) AND (organ dysfunction) AND (organ failure) AND (women))"}
{"candidate_id": "LLM07853", "doc_id": "NCT03208465_inc", "case_bucket": "or", "source_criterion": "Men or women at least 19 years of age Type 2 diabetes mellitus Stable coronary artery disease Global myocardial perfusion reserve (MPR) index < 2.5 The patient or guardian agrees to the study protocol and the schedule of clinical and dynamic SPECT follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site.", "candidate_expression": "((< 2.5) AND (Global myocardial perfusion reserve (MPR) index) AND (Stable) AND (Type 2 diabetes mellitus) AND (age) AND (at least 19 years) AND (coronary artery disease) AND (informed, written consent) AND ((Men) OR (women)))"}
{"candidate_id": "LLM07854", "doc_id": "NCT02645474_inc", "case_bucket": "or", "source_criterion": "adult patients ASA class 1 to 3 patients patients scheduled for elective breast mastectomy or quadrantectomy", "candidate_expression": "((ASA class 1 to 3) AND (adult) AND (breast quadrantectomy) AND (mastectomy))"}
{"candidate_id": "LLM07855", "doc_id": "NCT03416413_exc", "case_bucket": "or", "source_criterion": "Current DVT Recurrent varicose veins Arterial disease (ABPI<0.8) Vein diameter < 3mm Preference for one of the treatment options Patient who are unwilling to participate Inability or unwillingness to complete questionnaires Inability to attend follow-up appointments Patient currently included in a study of varicose vein treatment", "candidate_expression": "((ABPI <0.8) AND (Arterial disease) AND (DVT Current) AND (Inability to attend follow-up appointments) AND (Inability to complete questionnaires) AND (Patient currently included in a study of varicose vein treatment) AND (Vein diameter < 3mm) AND (unwilling to participate) AND (unwillingness to complete questionnaires) AND (varicose veins Recurrent))"}
{"candidate_id": "LLM07856", "doc_id": "NCT01709981_exc", "case_bucket": "or", "source_criterion": "Plan for diagnostic-only coronary angiography On colchicine chronically History of intolerance to colchicine Glomerular filtration rate <30mL/minute or on dialysis Active malignancy or infection History of myelodysplasia High-dose statin load <24 hours prior to procedure Use of oral steroids or non-steroidal anti-inflammatory agents other than aspirin within 72 hours or 3 times the agent's half-life (whichever is longer) Use of strong CYP3A4/P-glycoprotein inhibitors (specifically ritonavir, ketoconazole, clarithromycin, cyclosporine, diltiazem and verapamil) Unable to consent Participating in a competing study", "candidate_expression": "((3 times the agent's half-life) AND (72 hours) AND (<24 hours prior to procedure) AND (<30mL/minute) AND (Active) AND (Glomerular filtration rate) AND (High-dose statin) AND (aspirin) AND (chronically) AND (clarithromycin) AND (colchicine) AND (coronary angiography) AND (cyclosporine) AND (diagnostic-only) AND (dialysis) AND (diltiazem) AND (infection) AND (intolerance) AND (ketoconazole) AND (malignancy) AND (myelodysplasia) AND (non-steroidal anti-inflammatory agents) AND (oral steroids) AND (other than) AND (procedure) AND (ritonavir) AND (strong CYP3A4/P-glycoprotein inhibitors) AND (verapamil) AND (within 3 times the agent's half-life) AND (within 72 hours))"}
{"candidate_id": "LLM07857", "doc_id": "NCT00586898_inc", "case_bucket": "or", "source_criterion": "-Patients residing in the following clinical states wit! be considered: A. Rising PSA: Patients with a history of localized disease who have undergone definitive radiation or surgery. These patients must demonstrate progression of disease biochemically as outlined below. Patients in this group may not have radiographically evident disease. B. Non-castrate metastatic: Patients must present with radiographic evidence of metastatic disease at the time of diagnosis or after treatment for localized disease. These patients must show newly detected disease or progressing disease in bone or in soft tissue. Biochemical progression is defined as: minimum no. of determinations: 3 Interval: >2 weeks Minimal Baseline PSA value (ng/ml): 2 Minimal % increase in range of values: 50% Diagnosis of prostate adenocarcinoma histologically confirmed at MSKCC. Patient must have level of serum testosterone above the lower limit of normal. Karnofskcy performance status (KPS) >_70%. Patients must have adequate organ function as defined by the following laboratory criteria: WBC >_3500/mm3, platelet count >_100,000/mm3. Bilirubin <2.0 mg/dl or SGOT <3.0 X the upper limit of normal. Creatinine <_1.6 mg/dl or creatinine clearance >_60 cc/min. Prior hormonal therapy is allowed as: 1. Neoadjuvant treatment prior to radiation therapy or radical prostatectomy, provided that the total duration of exposure does not exceed 10 months. 2. One cycle of intermittent therapy up to a maximum exposure of 10 months. Patients must be at least 18 years of age. Patients must have signed an informed consent document stating that they understand the investigational nature of the proposed treatment", "candidate_expression": "(((ng/ml): 2) AND (10 months) AND (3) AND (50%) AND (<2.0 mg/dl) AND (<3.0 X the upper limit of normal) AND (<_1.6 mg/dl) AND (>2 weeks) AND (>_100,000/mm3) AND (>_3500/mm3) AND (>_60 cc/min) AND (>_70%) AND (Biochemical progression) AND (Interval) AND (Karnofskcy performance status (KPS)) AND (Minimal % increase in range of values) AND (Minimal Baseline PSA value) AND (Neoadjuvant treatment) AND (Non-castrate) AND (One cycle) AND (PSA) AND (Prior) AND (Rising) AND (WBC) AND (above the lower limit of normal) AND (adequate) AND (adequate organ function) AND (age) AND (at least 18 years) AND (biochemically) AND (confirmed) AND (definitive) AND (disease) AND (does not exceed 10 months) AND (histologically) AND (histologically confirmed) AND (history of) AND (hormonal therapy) AND (intermittent therapy) AND (is allowed) AND (level of serum testosterone) AND (localized disease) AND (maximum exposure) AND (metastatic) AND (metastatic disease) AND (minimum no. of determinations) AND (newly detected) AND (organ function) AND (platelet count) AND (prior to radiation therapy or radical prostatectomy) AND (progression of disease) AND (prostate adenocarcinoma) AND (radiation therapy or radical prostatectomy) AND (radiographic) AND (radiographic evidence) AND (radiographically evident) AND (signed an informed consent document) AND (the time of diagnosis) AND (total duration of exposure) AND (treatment) AND (treatment for localized disease) AND ((after treatment for localized disease) OR (at the time of diagnosis)) AND ((disease in bone) OR (disease in soft tissue) OR (progressing disease in bone) OR (progressing disease in soft tissue)) AND ((Bilirubin) OR (SGOT)) AND ((Creatinine) OR (creatinine clearance)) AND ((radiation) OR (surgery)) AND ((radiation therapy) OR (radical prostatectomy)))"}
{"candidate_id": "LLM07858", "doc_id": "NCT03390933_inc", "case_bucket": "other", "source_criterion": "currently on hemodialysis at a CDC dialysis unit English speaking able to provide informed consent", "candidate_expression": "((CDC dialysis unit) AND (English speaking) AND (able to provide informed consent) AND (hemodialysis currently))"}
{"candidate_id": "LLM07859", "doc_id": "NCT00752310_exc", "case_bucket": "or", "source_criterion": "No positive HIV 1 or HIV 2 test at screening no history of significant skin disease such as, but not limited to rash or eruptions, drug allergies, food allergy, dermatitis, eczema, psoriasis, or urticaria no history of allergy to drugs such as, but not limited to, sulphonamides and penicillins no previously demonstrated clinically significant allergy or hypersensitivity to any of the excipients of the investigational medication administered in this trial no female subject of childbearing potential without use of effective nonhormonal birth control methods, or not willing to continue practicing these birth control methods for at least 30 days after the end of the treatment period no positive pregnancy test or breast feeding at screening", "candidate_expression": "((HIV 1 test) AND (HIV 2 test) AND (allergy) AND (at screening) AND (birth control methods) AND (breast feeding) AND (childbearing potential) AND (clinically significant) AND (dermatitis) AND (drug allergies) AND (eczema) AND (effective) AND (eruptions) AND (excipients of the investigational medication) AND (female) AND (food allergy) AND (for at least 30 days after the end of the treatment period) AND (history) AND (hypersensitivity) AND (nonhormonal birth control) AND (not) AND (penicillins) AND (positive) AND (pregnancy test) AND (previously) AND (psoriasis) AND (rash) AND (screening) AND (significant) AND (skin disease) AND (sulphonamides) AND (the end of the treatment period) AND (urticaria) AND (willing to continue practicing) AND (without))"}
{"candidate_id": "LLM07860", "doc_id": "NCT02365870_exc", "case_bucket": "other", "source_criterion": "Unstable medical disease of comorbid psychiatric disease Dementia Subjects with less than one year duration of Parkinson's Current treatment with a dopamine agonist", "candidate_expression": "((Current) AND (Dementia) AND (Parkinson's) AND (Unstable medical disease) AND (comorbid psychiatric disease) AND (dopamine agonist) AND (less than one year duration))"}
{"candidate_id": "LLM07861", "doc_id": "NCT03473132_exc", "case_bucket": "other", "source_criterion": "recent thrombotic event", "candidate_expression": "(thrombotic event recent)"}
{"candidate_id": "LLM07862", "doc_id": "NCT03537924_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((>20) AND (Allergy) AND (acetazolamide) AND (active) AND (active smoking) AND (altitude exposure) AND (cardiovascular disease) AND (cigarettes per day) AND (disease) AND (during the last 10 years) AND (heavy smoking) AND (hypoxia) AND (other) AND (pack-years) AND (regular use of alcohol) AND (relevant being) AND (requiring) AND (respiratory disease) AND (sulfonamides) AND (tolerance) AND (treatment))"}
{"candidate_id": "LLM07863", "doc_id": "NCT02734173_inc", "case_bucket": "other", "source_criterion": "HCV RNA evidence of HCV infection Documented history of chronic HCV RNA infection with Genotype 1 Able to provide informed consent Available for ongoing follow-up if required", "candidate_expression": "((Able to provide informed consent) AND (Available for ongoing follow-up if required) AND (HCV RNA) AND (HCV infection) AND (chronic HCV infection Genotype 1))"}
{"candidate_id": "LLM07864", "doc_id": "NCT02983214_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure, history of ventricular tachycardia, ventricular fibrillation or multifocal ventricular extrasystoles or QTc prolongation. Patients with atrial fibrillation taking any anticoagulant therapy or patients with a history of cardioembolic ischemic stroke or hemorrhagic stroke. Patients with a history (= 12 months) of acute coronary syndrome receiving dual antiplatelet therapy, or patients receiving monotherapy with aspirin. Patients with hepatic impairment (child-Pugh staging, calibration = 5) or renal impairment (creatinine clearance = 30ml / min), recent peptic ulcer, a history of hypersensitivity to cilostazol, cancer patients undergoing treatment.", "candidate_expression": "((= 12 months) AND (= 30ml / min) AND (acute coronary syndrome) AND (anticoagulant therapy) AND (aspirin) AND (atrial fibrillation) AND (calibration = 5) AND (cardioembolic) AND (child-Pugh staging) AND (cilostazol) AND (creatinine clearance) AND (dual antiplatelet therapy) AND (history) AND (history of) AND (monotherapy) AND (recent) AND (treatment) AND ((Congestive heart failure) OR (QTc prolongation) OR (multifocal ventricular extrasystoles) OR (ventricular fibrillation) OR (ventricular tachycardia)) AND ((hemorrhagic stroke) OR (ischemic stroke)) AND ((cancer) OR (hepatic impairment) OR (hypersensitivity) OR (peptic ulcer) OR (renal impairment)))"}
{"candidate_id": "LLM07865", "doc_id": "NCT02920177_exc", "case_bucket": "or", "source_criterion": "Established Osteoarthritis (Kellgren-Lawrence > 3) Minimum joint space > 2 mm as measured on AP radiograph Hip dysplasia (center edge angle < 20° on AP radiograph) Patients with clinically significant cardiovascular, renal, hepatic, endocrine disease, cancer or diabetes Patients with ongoing infection including HIV and Hepatitis Patient with history of osteomyelitis/septic arthritis Anticoagulation therapy Patients who are pregnant or breast feeding Patients with systemic, rheumatic or inflammatory disease of the knee or chondrocalcinosis, hemochromatosis, inflammatory arthritis, arthropathy of the knee associated with juxta-articular Paget's disease of the femur or tibia, hemophilic arthropathy, infectious arthritis, Charcot's knee joint, villonodular synovitis, and synovial chondromatosis Patients taking immunosuppressant medication Patients with abnormal hematology or serum chemistry lab results Patients receiving injection to treatment knee within 2 months of study enrollment BMI greater than 35 or less than 20", "candidate_expression": "((< 20°) AND (> 2 mm) AND (> 3) AND (AP radiograph) AND (Anticoagulation therapy) AND (BMI) AND (Charcot's knee joint) AND (HIV) AND (Hepatitis) AND (Hip dysplasia) AND (Kellgren-Lawrence) AND (Minimum joint space) AND (Osteoarthritis) AND (Paget's disease) AND (Patients who are pregnant or breast feeding) AND (abnormal) AND (arthropathy of the knee) AND (cancer) AND (cardiovascular disease) AND (center edge angle) AND (chondrocalcinosis) AND (diabetes) AND (endocrine disease) AND (femur) AND (greater than 35) AND (hematology lab) AND (hemochromatosis) AND (hemophilic arthropathy) AND (hepatic disease) AND (immunosuppressant medication) AND (infection) AND (infectious arthritis) AND (inflammatory arthritis) AND (inflammatory disease) AND (injection) AND (juxta-articular) AND (knee) AND (less than 20) AND (ongoing) AND (osteomyelitis) AND (renal disease) AND (rheumatic disease) AND (septic arthritis) AND (serum chemistry lab) AND (significant) AND (study enrollment) AND (synovial chondromatosis) AND (systemic disease) AND (tibia) AND (villonodular synovitis) AND (within 2 months of study enrollment))"}
{"candidate_id": "LLM07866", "doc_id": "NCT02589977_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria: coronary artery disease, diabetes mellitus, contraindications to cardiac magnetic resonance imaging (CMR), weight >350 lbs, inability to lie flat for imaging, anemia, contraindications to regadenoson or aminophylline HEALTHY: known cardiovascular disease, cardiac risk factors or use of cardiac medications HYPERTENSIVE: known cardiovascular disease or risk factors aside from hypertension or use of cardiac medications HFpEF: prior history of LVEF below 50%, acute decompensated HF, moderate or greater valvular disease, significant cardiac arrhythmias, pericardial disease, congenital heart disease, primary pulmonary hypertension", "candidate_expression": "((>350 lbs) AND (HEALTHY) AND (HFpEF) AND (HYPERTENSIVE) AND (acute) AND (aside from) AND (below 50%) AND (cardiac magnetic resonance imaging (CMR)) AND (cardiac medications) AND (cardiovascular risk factors from hypertension) AND (prior history of) AND (significant) AND ((aminophylline) OR (regadenoson)) AND ((cardiac medications) OR (cardiac risk factors) OR (cardiovascular disease)) AND ((cardiovascular disease) OR (cardiovascular risk factors)) AND ((LVEF) OR (cardiac arrhythmias) OR (congenital heart disease) OR (decompensated HF) OR (pericardial disease) OR (primary pulmonary hypertension) OR (valvular disease)) AND ((greater) OR (moderate)) AND ((anemia) OR (contraindications) OR (coronary artery disease) OR (diabetes mellitus) OR (inability to lie flat for imaging) OR (weight)))"}
{"candidate_id": "LLM07867", "doc_id": "NCT03340740_exc", "case_bucket": "other", "source_criterion": "Use of antihistamine within the past 72 hours Chronic Pulmonary Condition other than asthma Other contraindication to cetirizine Severe asthma exacerbation requiring resuscitation", "candidate_expression": "((Chronic Pulmonary Condition) AND (Severe) AND (antihistamine) AND (asthma) AND (asthma exacerbation) AND (cetirizine) AND (contraindication) AND (other) AND (resuscitation) AND (within the past 72 hours))"}
{"candidate_id": "LLM07868", "doc_id": "NCT02954029_exc", "case_bucket": "or", "source_criterion": "congenital or acquired bleeding tendency platelet count <50,000/ µL hypersensitivity to shrimps, lobsters or beetles", "candidate_expression": "((bleeding tendency congenital acquired) AND (hypersensitivity shrimps lobsters beetles) AND (platelet count <50,000/ µL))"}
{"candidate_id": "LLM07869", "doc_id": "NCT02705222_exc", "case_bucket": "or", "source_criterion": "Age < 45 or > 55 years. Blood disorders or coagulopathy. Diagnosed or suspected local gynecologic lesion (polyp, adenomyosis, myoma, malignancy or cervical pathology). Use intrauterine contraceptive device. Pregnancy related conditions.", "candidate_expression": "((< 45 or > 55 years) AND (Age) AND (Pregnancy) AND (Pregnancy related) AND (conditions) AND (intrauterine contraceptive device) AND (local gynecologic lesion) AND ((adenomyosis) OR (cervical pathology) OR (malignancy) OR (myoma) OR (polyp)) AND ((Blood disorders) OR (coagulopathy)) AND ((Diagnosed) OR (suspected)))"}
{"candidate_id": "LLM07870", "doc_id": "NCT02643381_exc", "case_bucket": "or", "source_criterion": "Children (<18 years old). Women who are known to be pregnant. Any patient who has been previously randomized in the EvK Trial. Patients who require endotracheal intubation without sedative medication. For example, patients in full cardiac arrest. Patients with a known allergy to ketamine or etomidate. Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial.", "candidate_expression": "((Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial) AND (Children) AND (Women) AND (allergy) AND (endotracheal intubation require) AND (etomidate) AND (full cardiac arrest) AND (ketamine) AND (old <18 years) AND (pregnant) AND (randomized previously) AND NOT (sedative medication))"}
{"candidate_id": "LLM07871", "doc_id": "NCT02939209_inc", "case_bucket": "scope", "source_criterion": "Age 18-65 scheduled to receive ISB and general anesthesia as a day surgery patient for rotator cuff repair and acromioplasty, as a part of planned routine care", "candidate_expression": "((Age 18-65) AND (ISB) AND (acromioplasty) AND (general anesthesia) AND (rotator cuff repair))"}
{"candidate_id": "LLM07872", "doc_id": "NCT02034019_inc", "case_bucket": "other", "source_criterion": "Has a cataract and is expected to undergo clear corneal cataract surgery with phacoemulsification and implantation of a posterior chamber intraocular lens Has a potential post-operative pinhole corrected Snellen VA of at least 20/200 or better in both eyes", "candidate_expression": "((at least 20/200 or better) AND (both eyes) AND (cataract) AND (clear corneal cataract surgery) AND (implantation of a posterior chamber intraocular lens) AND (pinhole corrected Snellen VA) AND (with phacoemulsification))"}
{"candidate_id": "LLM07873", "doc_id": "NCT02691793_exc", "case_bucket": "or", "source_criterion": "Patients with second primary cancer, except:adequately treated non-melanoma skin cancer, curatively treated in-situ cancer of the cervix, or other solid tumor curatively treated with no evidence of disease for <= 5 years. Has known active central nervous system(CNS) metastases Has an active infection requiring systemic therapy Pregnancy or breast feeding Patients with cardiac problem Any previous treatment with sunitinib", "candidate_expression": "((Pregnancy or breast feeding) AND (active infection) AND (cardiac problem) AND (in-situ cancer of the cervix treated) AND (metastases central nervous system CNS) AND (non-melanoma skin cancer treated) AND (primary cancer, second) AND (solid tumor) AND (sunitinib))"}
{"candidate_id": "LLM07874", "doc_id": "NCT02946918_exc", "case_bucket": "or", "source_criterion": "AJCC Stage III or greater Undifferentiated, Anaplastic or Medullary Thyroid Cancer Planned postoperative TSH goal other than 0.1-0.5 mU/L History of gastrointestinal malabsorption or gastric bypass surgery Pregnancy Use of medications that alter the absorption or metabolism of levothyroxine Prior use of levothyroxine", "candidate_expression": "((0.1-0.5 mU/L) AND (AJCC) AND (Pregnancy) AND (Prior) AND (Stage III or greater) AND (TSH) AND (alter) AND (levothyroxine) AND (medications) AND (other than) AND (postoperative) AND ((gastric bypass surgery) OR (gastrointestinal malabsorption)) AND ((absorption of levothyroxine) OR (metabolism of levothyroxine)) AND ((Anaplastic Thyroid Cancer) OR (Medullary Thyroid Cancer) OR (Undifferentiated Thyroid Cancer)))"}
{"candidate_id": "LLM07875", "doc_id": "NCT02687724_exc", "case_bucket": "or", "source_criterion": "Female subjects who are pregnant or breast-feeding or considering becoming pregnant during the study Patients aged <18 years of age Patients who cannot give informed consent, Pregnant patients or those who are breastfeeding will be deemed ineligible. Prior treatment with any anti-TNF agent Contra-indication to use of GLM (Hypersensitivity to the active substance or to any of the excipients; Active tuberculosis (TB), acute or chronic Hepatitis B infection or other severe infections such as sepsis and/or opportunistic infections including HIV infection; Moderate or severe heart failure (NYHA class III/IV) Have symptoms or signs suggestive of current active or latent TB upon medical history, physical examination and/or chest radiograph, or positive Mycobacterium tuberculosis antigen-specific interferon-gamma release assay (IGRA) Patients with a history of, or at imminent risk for, colectomy; who required gastrointestinal surgery within 2 months before screening; History of colonic mucosal dysplasia or adenomatous colonic polyps that were not removed Screening stool study positive for enteric pathogens or Clostridium difficile toxin. Oral corticosteroids at a dose >40 mg prednisone or its equivalent per day; receipt of cyclosporine, tacrolimus, sirolimus, or mycophenolate mofetil within 8 weeks before the first study agent injection; or use of an investigational agent within 5 half-lives of that agent before the first study agent injection. Patients in recent receipt of live vaccinations within 4 weeks prior to enrolment", "candidate_expression": "((Contra-indication) AND (Female subjects who are pregnant or breast-feeding or considering becoming pregnant during the study) AND (GLM) AND (HIV infection) AND (Mycobacterium tuberculosis antigen-specific interferon-gamma release assay (IGRA) positive) AND (NYHA class III/IV) AND (Pregnant patients or those who are breastfeeding will be deemed ineligible) AND (TB) AND (aged <18 years of age) AND (anti-TNF agent) AND (colectomy) AND (gastrointestinal surgery within 2 months before screening) AND (live vaccinations within 4 weeks prior to enrolment) AND (sepsis) AND (stool study positive) AND (treatment Prior) AND NOT (removed) AND ((active substance) OR (excipients)) AND ((acute) OR (chronic)) AND ((Hepatitis B infection) OR (Hypersensitivity) OR (heart failure) OR (opportunistic infections) OR (severe infections) OR (tuberculosis (TB) Active)) AND ((Moderate) OR (severe)) AND ((active current) OR (latent)) AND ((chest radiograph) OR (medical history) OR (physical examination)) AND ((history of) OR (imminent risk for)) AND ((adenomatous colonic polyps) OR (colonic mucosal dysplasia)) AND ((Clostridium difficile toxin) OR (enteric pathogens)) AND ((Oral corticosteroids >40 mg prednisone per day) OR (investigational agent within 5 half-lives before the first study agent injection)) AND ((cyclosporine) OR (mycophenolate mofetil) OR (sirolimus) OR (tacrolimus)))"}
```
