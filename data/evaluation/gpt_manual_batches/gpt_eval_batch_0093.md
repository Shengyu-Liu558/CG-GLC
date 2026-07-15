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
{"candidate_id": "LLM02301", "doc_id": "NCT02958072_exc", "case_bucket": "or", "source_criterion": "Hemoglobin concentration under 6.5 mmol/l screening HBA1c more than 108 mmol/l Non-compliant with blood-letting Clinically infected ulcer Patient planned for or has had a revascularization procedure in the affected leg within the last 8 weeks The ulcer have been treated with growth factors in the last 8 weeks History of deep venous insufficiency, chronic venous leg ulcer or stasis dermatitis Breast-feeding women or fertile women not agreeing to use an effective method of contraception Participation in another clinical ulcer-healing study within the last 4 weeks Patient has previously been randomized in this study Judgement by the investigator that the patient is not able to participate in the study", "candidate_expression": "((Breast-feeding) AND (HBA1c) AND (Hemoglobin concentration) AND (History) AND (Judgement by the investigator that the patient is not able to participate in the study) AND (Non-compliant) AND (affected leg) AND (agreeing to use an effective method of contraception) AND (blood-letting) AND (chronic venous leg ulcer) AND (deep venous insufficiency) AND (fertile) AND (growth factors) AND (has had) AND (in the last 8 weeks) AND (infected ulcer) AND (more than 108 mmol/l) AND (not) AND (planned) AND (revascularization procedure) AND (stasis dermatitis) AND (treated) AND (ulcer) AND (under 6.5 mmol/l) AND (within the last 8 weeks) AND (women))"}
{"candidate_id": "LLM02302", "doc_id": "NCT03226080_inc", "case_bucket": "other", "source_criterion": "ASA I-IV Age 55 or older Scheduled for operative repair of isolated intertrochanteric hip fracture", "candidate_expression": "((ASA I-IV) AND (Age 55 or older) AND (intertrochanteric hip fracture isolated) AND (operative repair Scheduled for isolated))"}
{"candidate_id": "LLM02303", "doc_id": "NCT03479502_exc", "case_bucket": "or", "source_criterion": "allergy to Doxycycline or Methylprednisolone, pregnancy, diagnosis, Inflammatory arthritis or diabetes, secondary adhesive capsulitis (history of significant trauma, rotator cuff tear injury, stroke) evidence of arthritis on x-ray, current infectious disease, and any previous treatment for the for adhesive capsulitis of the affected shoulder.", "candidate_expression": "((adhesive capsulitis affected shoulder) AND (adhesive capsulitis secondary) AND (allergy) AND (arthritis evidence of) AND (diagnosis) AND (infectious disease current) AND (pregnancy) AND (treatment any previous) AND (x-ray) AND ((Doxycycline) OR (Methylprednisolone)) AND ((rotator cuff tear injury) OR (stroke) OR (trauma significant)) AND ((Inflammatory arthritis) OR (diabetes)))"}
{"candidate_id": "LLM02304", "doc_id": "NCT03305575_exc", "case_bucket": "or", "source_criterion": "Abdominal and complex cervical cerclage (e.g. bulging bag) Contraindication to neuraxial anesthesia Known hypersensitivity to chloroprocaine (a.k.a. Ester allergy), paraaminobenzoic acid (PABA) or bupivacaine (a.k.a. Amide allergy) Pseudocholinesterase deficiency Concomitant use with ergot-type oxytocic drugs", "candidate_expression": "((Amide allergy) AND (Contraindication) AND (Ester allergy) AND (PABA) AND (Pseudocholinesterase deficiency) AND (cervical cerclage Abdominal complex bulging bag) AND (ergot-type oxytocic drugs Concomitant) AND (hypersensitivity) AND (neuraxial anesthesia) AND ((bupivacaine) OR (chloroprocaine) OR (paraaminobenzoic acid)))"}
{"candidate_id": "LLM02305", "doc_id": "NCT02225548_exc", "case_bucket": "or", "source_criterion": "Subject unwilling to cease use of any treatment for erectile dysfunction during the study, including oral medication, vacuum devices, constrictive devices, injections, urethral suppositories, gels, any over-the-counter or nonprescription medications, and products purchased via the internet Subject receiving dopamine agonists, nitrates, alpha-receptor blocking agents, or antihypertensive medication (see other exclusionary medications listed below) Subject with a history of syncope within the last 6 months prior to screening Subject with symptomatic postural hypotension (severe dizziness or fainting Subject with hypotension and a resting systolic blood pressure of < 90 mmHG or hypertension with a resting systolic blood pressure > 170 mmHG or a resting diastolic blood pressure > 110 mmHG Subject with any underlying cardiovascular condition, including unstable angina pectoris, which preclude sexual activity Subject with a history of myocardial infarction, stroke or life-threatening arrhythmia within 6 months prior to screening Subject with uncontrolled atrial fibrillation/flutter at screening (defined as ventricular response rate = 100 bpm) Subject with a bleeding disorder Subject with a history of prostatectomy because of prostate cancer, including nerve sparing techniques. Subjects with a history of surgical procedures for the treatment of benign prostate hypertrophy are permitted, with the exception of cryosurgery, cryotherapy or cryoablation Subject with hereditary degenerative retinal disorders such as retinitis pigmentosa Subject with a history of loss of vision because of non-arteritic anterior ischemic optic neuropathy (NAION), history of temporary or permanent loss of vision, including unilateral loss of vision Subject with a history of congenital QT prolongation Subject with a penile anatomical abnormality (e.g., penile fibrosis, fractures, or Peyronie's disease) which, in the investigator's opinion, could significantly impair sexual performance. This will be based on subject's reported medical history (penile exam not required) Subject with primary hypoactive sexual desire. Subject with a spinal cord injury Subject with a severe chronic or acute liver disease, history of moderate (Child-Pugh B), or severe (Child-Pugh C) hepatic impairment Subject with clinically significant chronic hematological disease which could lead to priapism such as sickle cell anemia, multiple myeloma, and leukemia Subject with active peptic ulceration Subject with a history of malignancy within the past 5 years (other than squamous or basal cell skin cancer) Subject with a history of a positive test for Hepatitis B surface antigen (HbsAg) or Hepatitis C Subject with a known hypersensitivity to any component of the investigational medications, monoamine oxidase inhibitors, phosphodiesterase type 5 inhibitors or phenylethylamines Subjects with a history of drug or alcohol abuse within the past 6 months Subjects currently consuming =5 units of alcohol per day Subject who is illiterate or unable to understand the Informed Consent Form, questionnaires or subject diary Subject who, in the opinion of the investigator, will be noncompliant with the visit schedule or study procedures Subject with any unstable medical, psychiatric, or substance abuse disorder that in the opinion of the investigator is likely to affect the subject's ability to complete the study or preclude the subject's participation in the study Diagnosis of any other neurologic disease Uncontrolled Diabetes (Hemoglobin A1C > 7.5)", "candidate_expression": "((Child-Pugh B) AND (Child-Pugh C) AND (Diabetes Uncontrolled) AND (Hemoglobin A1C > 7.5) AND (NAION temporary) AND (Peyronie's disease)) AND (acute liver disease) AND (alcohol abuse) AND (alpha-receptor blocking agents) AND (antihypertensive medication) AND (arrhythmia life-threatening) AND (atrial fibrillation) AND (atrial flutter) AND (basal cell skin cancer) AND (benign prostate hypertrophy) AND (bleeding disorder) AND (cardiovascular condition) AND (chronic liver disease) AND (congenital QT prolongation history of) AND (constrictive devices) AND (consuming alcohol per day currently =5 units) AND (cryoablation) AND (cryosurgery) AND (cryotherapy) AND (diastolic blood pressure > 110 mmHG) AND (dizziness) AND (dopamine agonists) AND (drug abuse) AND (erectile dysfunction) AND (fainting) AND (gels over-the-counter nonprescription) AND (hematological disease clinically significant chronic could lead to priapism) AND (hepatic impairment moderate) AND (hepatic impairment severe) AND (hereditary degenerative retinal disorders) AND (hypersensitivity) AND (hypertension) AND (hypotension) AND (impair sexual performance) AND (injections) AND (leukemia) AND (loss of vision history of) AND (loss of vision permanent) AND (loss of vision unilateral) AND (malignancy history of within the past 5 years) AND (medical disorder likely to affect the subject's ability to complete the study) AND (medications) AND (medications investigational) AND (monoamine oxidase inhibitors) AND (multiple myeloma) AND (myocardial infarction) AND (nerve sparing techniques) AND (neurologic disease any other) AND (nitrates) AND (non-arteritic anterior ischemic optic neuropathy) AND (noncompliant with the visit schedule or study procedure) AND (oral medication) AND (penile anatomical abnormality could significantly impair sexual performance) AND (penile exam) AND (penile fibrosis) AND (penile fractures) AND (peptic ulceration active) AND (phenylethylamines) AND (phosphodiesterase type 5 inhibitors) AND (postural hypotension symptomatic) AND (preclude the subject's participation in the study) AND (priapism) AND (primary hypoactive sexual desire) AND (prostate cancer) AND (prostatectomy) AND (psychiatric disorder) AND (retinitis pigmentosa) AND (sickle cell anemia) AND (spinal cord injury) AND (squamous skin cancer) AND (stroke) AND (substance abuse disorder) AND (syncope within the last 6 months prior to screening) AND (systolic blood pressure < 90 mmHG) AND (systolic blood pressure > 170 mmHG) AND (test for Hepatitis B surface antigen (HbsAg)) AND (test for Hepatitis C) AND (treatment cease use of during the study) AND (understand the Informed Consent Form) AND (understand the questionnaires) AND (understand the subject diary) AND (unstable angina pectoris) AND (urethral suppositories) AND (vacuum devices) AND (ventricular response rate = 100 bpm) AND NOT (surgical procedures history of))"}
{"candidate_id": "LLM02306", "doc_id": "NCT01009359_exc", "case_bucket": "or", "source_criterion": "Current unstable medical condition (e.g. unstable angina, myocardial infarction or coronary revascularization in the preceding 12 months, cardiac failure, chronic renal failure, chronic hepatic disease, severe pulmonary disease, blood disorders, poorly controlled diabetes, chronic infection)", "candidate_expression": "((blood disorders) AND (cardiac failure chronic) AND (chronic hepatic disease) AND (chronic infection) AND (chronic renal failure chronic) AND (coronary revascularization in the preceding 12 months) AND (diabetes controlled chronic) AND (myocardial infarction in the preceding 12 months) AND (pulmonary disease severe) AND (unstable angina) AND (unstable medical condition Current unstable))"}
{"candidate_id": "LLM02307", "doc_id": "NCT02652637_inc", "case_bucket": "other", "source_criterion": "Patients undergoing colon resection", "candidate_expression": "((colon resection) AND (undergoing))"}
{"candidate_id": "LLM02308", "doc_id": "NCT01959061_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women Patients with severe organ dysfunction or failure With severe cardiovascular disease, or mental Extraliver metastases", "candidate_expression": "((Extraliver) AND (Extraliver metastases) AND (Pregnant) AND (cardiovascular disease) AND (disease mental) AND (lactating) AND (metastases) AND (organ dysfunction) AND (organ failure) AND (severe) AND (women))"}
{"candidate_id": "LLM02309", "doc_id": "NCT00806936_inc", "case_bucket": "other", "source_criterion": "After the investigator has taken the decision to use human insulin or insulin analogues to treat the subject, any type 2 diabetic previously inadequately controlled with two or more OADs is eligible for the study The selection of the subjects will be at the discretion of the individual investigator", "candidate_expression": "((OADs two or more) AND (type 2 diabetic inadequately controlled))"}
{"candidate_id": "LLM02310", "doc_id": "NCT03299517_inc", "case_bucket": "or", "source_criterion": "Adult men and women> 18 years old Presence of sustained ventricular tachycardia with HR> 120 bpm Systolic blood pressure> 90 mmHg No signs of poor peripheral perfusion Absence of dyspnea Absence of severe angina Signed consent form", "candidate_expression": "((> 120 bpm) AND (> 18 years old) AND (> 90 mmHg) AND (Absence of) AND (Adult) AND (HR) AND (No) AND (Signed consent form) AND (Systolic blood pressure) AND (angina) AND (dyspnea) AND (men) AND (old) AND (poor peripheral perfusion) AND (severe) AND (signs of) AND (sustained) AND (ventricular tachycardia) AND (women))"}
{"candidate_id": "LLM02311", "doc_id": "NCT02062489_inc", "case_bucket": "or", "source_criterion": "The patients signed the written informed consent The patients present with operable unilateral invasive breast cancers without distant metastasis(stage I, II, and III) The breast tumor's positive ER/PR rate is <1%, and positive ER-beta1 rate is =10% by IHC. The patients have no history of neoadjuvant hormone therapy. The patients have normal cardiac functions by echocardiography. The patients' ECOG scores are =0-2. Female patient who is = 18yrs, and = 65yrs. The patients are non-pregnant, and disposed to practice contraception during the whole trial. The patients underwent neoadjuvant chemotherapy plus surgery or directly modified radical mastectomy or breast-conserving surgery (plus sentinel lymph node biopsy or axillary lymph node dissection) after diagnosis of breast cancer. The patients underwent chemotherapy, radiation therapy or targeted therapy(herceptin) after surgery according to the 2013 NCCN guideline. The results of patients' blood tests are as follows:", "candidate_expression": "((2013 NCCN guideline) AND (<1%) AND (= 18yrs) AND (= 65yrs) AND (=0-2) AND (=10%) AND (ECOG scores) AND (Female) AND (I, II, and III) AND (IHC) AND (The patients are non-pregnant, and disposed to practice contraception during the whole trial.) AND (after diagnosis of breast cancer) AND (after surgery) AND (breast cancers) AND (breast tumor) AND (diagnosis of breast cancer) AND (directly modified) AND (distant metastasis) AND (echocardiography) AND (herceptin) AND (invasive) AND (neoadjuvant chemotherapy) AND (neoadjuvant hormone therapy) AND (no history) AND (normal cardiac functions) AND (operable) AND (positive ER-beta1 rate) AND (positive ER/PR rate) AND (stage) AND (surgery) AND (unilateral) AND (without) AND ((breast-conserving surgery) OR (radical mastectomy)) AND ((axillary lymph node dissection) OR (sentinel lymph node biopsy)) AND ((chemotherapy) OR (radiation therapy) OR (targeted therapy)))"}
{"candidate_id": "LLM02312", "doc_id": "NCT01890759_inc", "case_bucket": "or", "source_criterion": "Male and female subjects aged 9 to 17 months on the day of inclusion Informed consent form has been signed and dated by the parent(s) or other legally acceptable representative(s) (if applicable) Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.", "candidate_expression": "((Male) AND (Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.) AND (aged 9 to 17 months on the day of inclusion) AND (female))"}
{"candidate_id": "LLM02313", "doc_id": "NCT02631512_exc", "case_bucket": "or", "source_criterion": "Ulcers due to non-diabetic etiology. Uncontrolled diabetes defined as HbA1c above 70 mmol/mol and insufficient nutritional status. Ulcers older than 1 year. Any of gangrene, osteomyelitis, cellulitis, or Charcot osteoarthropathy.", "candidate_expression": "((Any of) AND (HbA1c) AND (Ulcers) AND (Uncontrolled diabetes) AND (above 70 mmol/mol) AND (insufficient nutritional status) AND (non-diabetic) AND (older than 1 year) AND ((Charcot osteoarthropathy) OR (cellulitis) OR (gangrene) OR (osteomyelitis)))"}
{"candidate_id": "LLM02314", "doc_id": "NCT02557412_exc", "case_bucket": "or", "source_criterion": "Apnea-hypopnea index of less than 5 h-1 or greater than 30 h-1. Predominance of central apneas and hypopneas, defined as more than 25% of all respiratory events. Professional drivers, risk profession or respiratory failure (according to criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing). Very excessive daytime sleepiness (Epworth Sleepiness Scale> 18). Morbid obesity (BMI> 40 kg / m2). Prior treatment with CPAP.", "candidate_expression": "((Apnea-hypopnea index less than 5 h-1 or greater than 30 h-1) AND (BMI > 40 kg / m2) AND (CPAP Prior) AND (Epworth Sleepiness Scale > 18) AND (Morbid obesity) AND (Predominance) AND (all respiratory events more than 25%) AND (central apneas and hypopneas) AND (criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing) AND (daytime sleepiness Very excessive) AND ((Professional drivers) OR (respiratory failure) OR (risk profession)))"}
{"candidate_id": "LLM02315", "doc_id": "NCT00061308_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential that do not practice adequate contraception. Pregnant or lactating. Received more than one primary chemotherapy regimen. Concomitant or previous malignancies with the exception of adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, incidental carcinoid, or other cancer from which the patient has been disease free for 5 years. Active uncontrolled infection requiring antibiotics. Concurrent severe medical problems unrelated to the malignancy which would limit full compliance with the study. Received radiation to more than 10% of bone. Prior treatment with topotecan or gemcitabine. Hypersensitivity to camptothecin or nucleoside analogues. Use of an investigational agent within 30 days.", "candidate_expression": "((Active uncontrolled) AND (Concurrent) AND (Hypersensitivity) AND (Prior) AND (Women) AND (adequate contraception) AND (adequately treated) AND (antibiotics) AND (bone) AND (child-bearing potential) AND (do not) AND (for 5 years) AND (has been disease free) AND (infection) AND (investigational agent) AND (limit full compliance with the study) AND (malignancies) AND (malignancy) AND (medical problems) AND (more than 10%) AND (more than one) AND (primary chemotherapy regimen) AND (radiation) AND (severe) AND (the exception of) AND (treatment) AND (unrelated to the malignancy) AND (within 30 days) AND ((Concomitant) OR (previous)) AND ((basal cell skin cancer) OR (in situ cervical cancer) OR (incidental carcinoid) OR (other cancer) OR (squamous cell skin cancer)) AND ((gemcitabine) OR (topotecan)) AND ((camptothecin) OR (nucleoside analogues)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM02316", "doc_id": "NCT01088750_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02317", "doc_id": "NCT03063866_inc", "case_bucket": "or", "source_criterion": "Patients aged between 40 and 60 years old. With Child score B or C Presented for elective gastrointestinal endoscopy", "candidate_expression": "((Child score) AND (aged) AND (between 40 and 60 years old) AND (elective) AND (gastrointestinal endoscopy) AND ((B) OR (C)))"}
{"candidate_id": "LLM02318", "doc_id": "NCT03473132_exc", "case_bucket": "other", "source_criterion": "recent thrombotic event", "candidate_expression": "((recent) AND (thrombotic event))"}
{"candidate_id": "LLM02319", "doc_id": "NCT03217409_inc", "case_bucket": "or", "source_criterion": "Subjects = 19 or = 75 years of age Subjects undergoing treatment for type 2 diabetes Subjects undergoing treatment of statin for hypercholesterolemia Fasting LDL-C = 250mg/dL at the screening visit Fasting LDL-C =70mg/dL or = 160mg/dL at the randomization visit Fasting TG<500mg/dL", "candidate_expression": "((<500mg/dL) AND (= 160mg/dL) AND (= 19 or = 75 years) AND (= 250mg/dL) AND (=70mg/dL) AND (Fasting LDL-C) AND (Fasting TG) AND (age) AND (at the randomization visit) AND (at the screening visit) AND (hypercholesterolemia) AND (statin) AND (treatment) AND (type 2 diabetes))"}
{"candidate_id": "LLM02320", "doc_id": "NCT00050349_inc", "case_bucket": "or", "source_criterion": "Patients with biopsy-proven metastatic carcinoid tumors or other neuroendocrine tumors (Islet cell, Gastrinomas and VIPomas) with at least one measurable lesion (other than bone) that has either not been previously irradiated or if previously irradiated has demonstrated progression since the radiation therapy The patient has no major impairment of renal or hepatic function, as defined by the following laboratory parameters: total bilirubin <1.5 X ULN; AST, ALT<2.5X ULN (<5 X ULN if liver metastases are present) Patients on Sandostatin Lar (long acting somatostatin analogue) must be on a stable dose for 30 days prior to study entry and short acting somatostatin analogues must be judged to be on a clinically stable dose by the investigator prior to study entry Must have a life expectancy of greater than three (3) months Karnofsky Performance Status > 60 Female patients must have a negative serum pregnancy test at screening. (Not applicable to patients with bilateral oophorectomy and/or hysterectomy or to those patients who are postmenopausal.)", "candidate_expression": "((<1.5 X ULN) AND (<2.5X ULN) AND (<5 X ULN) AND (> 60) AND (ALT) AND (AST) AND (Female) AND (Gastrinomas) AND (Islet cell) AND (Karnofsky Performance Status) AND (Sandostatin Lar) AND (VIPomas) AND (at screening) AND (bilateral oophorectomy) AND (biopsy) AND (bone) AND (clinically stable dose) AND (for 30 days prior to study entry) AND (greater than three (3) months) AND (hysterectomy) AND (irradiated) AND (life expectancy) AND (liver metastases) AND (long acting somatostatin analogue) AND (major impairment of hepatic function) AND (major impairment of renal function) AND (measurable lesion) AND (metastatic carcinoid tumors) AND (negative) AND (no) AND (not been) AND (other neuroendocrine tumors) AND (other than) AND (postmenopausal) AND (prior to study entry) AND (progression) AND (proven) AND (radiation therapy) AND (serum pregnancy test) AND (short acting somatostatin analogues) AND (since the radiation therapy) AND (stable dose) AND (total bilirubin))"}
{"candidate_id": "LLM02321", "doc_id": "NCT02281643_exc", "case_bucket": "or", "source_criterion": "Known intolerance to the doxycycline Body weight <40 kg Pregnancy or breastfeeding History of severe allergic reaction or anaphylaxis Alcohol or drug abuse", "candidate_expression": "((<40 kg) AND (Alcohol abuse) AND (Body weight) AND (History of) AND (Pregnancy) AND (allergic reaction) AND (anaphylaxis) AND (breastfeeding) AND (doxycycline) AND (drug abuse) AND (intolerance to the doxycycline) AND (severe))"}
{"candidate_id": "LLM02322", "doc_id": "NCT03196843_inc", "case_bucket": "or", "source_criterion": "Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent. Histopathologic confirmed squamous cell carcinoma of head and neck ,including oral cavity, oropharynx, larynx, or hypopharynx. Ages=65 years,Not limited to gender. ECOG performance status =2. Patients with surgical contraindication or reject to surgery. Postoperative TNM(primary tumor,regional nodes,metastasis) staging III~IV, positive surgical margin. without evidence of distant metastases. No contraindication to chemoradiotherapy. Life expectancy > 3 months. Available Organ function: white blood cell=3.5×109/L, Neutrophils =1.5×109/L, Hemoglobin =80g/L, Blood platelet>100×109/L; Alanine aminotransferase (ALT) and Aspartate aminotransferase (AST)= 2.5 upper limit of normal(ULN); Total bilirubin (TBIL) <1.5 ULN;serum creatinine=1.5 ULN; creatinine clearance of = 50ml/min", "candidate_expression": "((<1.5 ULN) AND (= 2.5 upper limit of normal(ULN)) AND (= 50ml/min) AND (=1.5 ULN) AND (=1.5×109/L) AND (=2) AND (=3.5×109/L) AND (=65 years) AND (=80g/L) AND (> 3 months) AND (>100×109/L) AND (Ages) AND (Alanine aminotransferase (ALT)) AND (Aspartate aminotransferase (AST)) AND (Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent.) AND (Blood platelet) AND (ECOG performance status) AND (Hemoglobin) AND (Histopathologic) AND (Histopathologic confirmed) AND (III~IV,) AND (Life expectancy) AND (Neutrophils) AND (No) AND (Postoperative) AND (TNM staging) AND (Total bilirubin (TBIL)) AND (chemoradiotherapy) AND (contraindication) AND (creatinine clearance) AND (distant metastases) AND (evidence) AND (head and neck) AND (positive) AND (serum creatinine) AND (squamous cell carcinoma) AND (surgery) AND (surgical) AND (surgical margin) AND (white blood cell) AND (without) AND ((contraindication) OR (reject)) AND ((hypopharynx) OR (larynx) OR (oral cavity) OR (oropharynx)))"}
{"candidate_id": "LLM02323", "doc_id": "NCT01711801_exc", "case_bucket": "or", "source_criterion": "History or presence of any clinically significant disease or disorder Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator History of clinically significant hypersensitivity or allergic drug reactions Any suspicion or history of alcohol abuse and/or consumption of other drugs of abuse Regular smoker (> 5 cigarettes, > 1 pipeful or > 1 cigar per day) Positive for hepatitis B, hepatitis C or HIV infection Dietary restrictions that would prohibit the consumption of standardized meals Participation in an investigational drug or device study within 90 days prior to screening, as calculated from the follow-up from the previous study", "candidate_expression": "((Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator) AND (Dietary restrictions would prohibit the consumption of standardized meals) AND (Regular smoker) AND (clinically significant) AND (clinically significant disease or disorder) AND (would prohibit the consumption of standardized meals) AND ((allergic drug reactions) OR (hypersensitivity clinically significant)) AND ((alcohol abuse) OR (consumption of other drugs of abuse)) AND ((history) OR (suspicion)) AND ((clinically significant disease History clinically significant) OR (clinically significant disorder History clinically significant)) AND ((cigar > 1 per day) OR (cigarettes > 5) OR (pipeful > 1)) AND ((HIV infection) OR (hepatitis B Positive) OR (hepatitis C Positive)))"}
{"candidate_id": "LLM02324", "doc_id": "NCT01967420_exc", "case_bucket": "other", "source_criterion": "Active substance dependency History of severe head injury", "candidate_expression": "((History) AND (severe head injury) AND (substance dependency))"}
{"candidate_id": "LLM02325", "doc_id": "NCT02833623_exc", "case_bucket": "or", "source_criterion": "advanced chronic disease that would not allow the patient to complete the treatment or follow-up or attend visits allergy to any of the drugs used in this study previous Helicobacter Pylori eradication treatment pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study) taking antibiotics or PPIs or bismuth salts within four weeks previous gastrointestinal surgery", "candidate_expression": "((Helicobacter Pylori eradication treatment) AND (gastrointestinal surgery) AND (pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study)) AND (within four weeks) AND ((PPIs) OR (antibiotics) OR (bismuth salts)))"}
```
