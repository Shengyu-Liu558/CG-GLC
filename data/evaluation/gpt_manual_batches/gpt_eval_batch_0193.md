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
{"candidate_id": "LLM04801", "doc_id": "NCT00440245_inc", "case_bucket": "or", "source_criterion": "asthma or COPD", "candidate_expression": "((COPD) OR (asthma))"}
{"candidate_id": "LLM04802", "doc_id": "NCT02668978_inc", "case_bucket": "or", "source_criterion": "Patients over the age of 18 years who are able to give their informed consent Lobar and sublobar resections Open, video-assisted thoracoscopic or robotic surgeries Diagnostic or therapeutic procedures", "candidate_expression": "((Diagnostic procedures) AND (Lobar resections) AND (able to give their informed consent) AND (over the age of 18 years) AND (robotic surgeries) AND (sublobar resections) AND (therapeutic procedures) AND (thoracoscopic surgeries) AND (video-assisted))"}
{"candidate_id": "LLM04803", "doc_id": "NCT00576173_inc", "case_bucket": "or", "source_criterion": "Patients with a histologically, radiologically or haematologically confirmed malignancy whose pain is judged by the investigator to be caused by the malignancy Patients must have been on a stable daily dose of weak opioids or strong opioids for at least 72 hours prior to the start the study and must remain at the same dosage for the duration of the study Patients must have a VAS (Visual analog scale) >=40mm", "candidate_expression": "((VAS (Visual analog scale) >=40mm) AND (malignancy) AND (pain) AND ((haematologically) OR (histologically) OR (radiologically)) AND ((strong opioids) OR (weak opioids)))"}
{"candidate_id": "LLM04804", "doc_id": "NCT02859480_inc", "case_bucket": "other", "source_criterion": "Patients underwent percutaneous coronary intervention with drug-eluting stent;", "candidate_expression": "((drug-eluting stent) AND (percutaneous coronary intervention))"}
{"candidate_id": "LLM04805", "doc_id": "NCT01491295_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, HDV coinfection. Uncontrolled HCC, malignancy or decompensated liver cirrhosis (CTP score = 7). Uremia patients or Creatinine = 2 mg/dl.", "candidate_expression": "((CTP score = 7) AND ((HCV coinfection) OR (HDV coinfection) OR (coinfection HIV)) AND ((Creatinine = 2 mg/dl) OR (Uremia)) AND ((HCC Uncontrolled) OR (liver cirrhosis decompensated) OR (malignancy)))"}
{"candidate_id": "LLM04806", "doc_id": "NCT01735955_inc", "case_bucket": "other", "source_criterion": "Patient is currently enrolled in a Novartis-sponsored, Oncology Clinical Development & Medical Affairs study receiving nilotinib and has fulfilled all their requirements in the parent study Patient is currently benefiting from the treatment with nilotinib, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study", "candidate_expression": "((Willingness to comply with scheduled visits) AND (Willingness to comply with treatment plans) AND (Written informed consent prior to enrolling in roll-over study) AND (ability to comply with scheduled visits) AND (compliance with the parent study protocol requirements) AND (enrolled in a Oncology Clinical Development & Medical Affairs study currently Novartis-sponsored) AND (nilotinib) AND (treatment currently))"}
{"candidate_id": "LLM04807", "doc_id": "NCT01824537_inc", "case_bucket": "other", "source_criterion": "Couple must have been in a new relationship that started no more than six months prior to study entry Both partners plan on remaining in Montreal for at least 1 year Plan on having continued sexual contact with partner Be willing to comply with study procedures", "candidate_expression": "((Be willing to comply with study procedures) AND (having continued sexual contact with partner Plan on) AND (new relationship no more than six months prior to study entry) AND (remaining in Montreal plan on for at least 1 year))"}
{"candidate_id": "LLM04808", "doc_id": "NCT02510404_exc", "case_bucket": "or", "source_criterion": "1. Patients with other uncontrolled infections (see 2.3.2 for definitions) 2. Patients who received ATG, Campath, or other T cell immunosuppressive monoclonal antibodies in the last 28 days 3. Received donor lymphocyte infusion in last 28 days 4. Diagnosis of Omenn's syndrome or MHC class I deficiency 5. Active and uncontrolled malignancy 6. Pregnant or lactating 7. Unable to wean steroids to ≤0.5 mg/kg/day prednisone. 8. Patients with Grade 3 hyperbilirubinemia", "candidate_expression": "((Active) AND (Grade 3) AND (Unable) AND (donor lymphocyte infusion) AND (hyperbilirubinemia) AND (in last 28 days) AND (in the last 28 days) AND (malignancy) AND (other uncontrolled infections) AND (prednisone) AND (steroids) AND (uncontrolled) AND (wean) AND (≤0.5 mg/kg/day) AND ((ATG) OR (Campath) OR (T cell immunosuppressive monoclonal antibodies)) AND ((MHC class I deficiency) OR (Omenn's syndrome)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM04809", "doc_id": "NCT03225469_exc", "case_bucket": "or", "source_criterion": "1. History of colorectal surgery 2. Suspected or known digestive tract obstruction, stricture, or perforation 3. Serious status of illness, such as severe renal failure whose creatinine clearance<30 ml/min, New York Heart Association grade III or grade IV congestive heart failure, or hemodynamic instability, etc. 4. Incapable of completing bowel preparation，such as dysphagia, allergy to purgatives, or impaired mental status, etc. 5. Pregnancy or breastfeeding 6. Incomplete colonoscopy due to causes except poor bowel preparation 7. Unable to give informed consent 8. Have participated in the study before.", "candidate_expression": "((Incapable of completing bowel preparation) AND (New York Heart Association grade III or grade IV) AND (Serious status of illness) AND (colonoscopy Incomplete) AND (colorectal surgery History) AND (creatinine clearance <30 ml/min) AND (informed consent) AND (purgatives) AND NOT (poor bowel preparation) AND ((congestive heart failure) OR (hemodynamic instability) OR (renal failure severe)) AND ((allergy) OR (dysphagia) OR (impaired mental status)) AND ((Pregnancy) OR (breastfeeding)) AND ((digestive tract obstruction) OR (digestive tract perforation) OR (digestive tract stricture)))"}
{"candidate_id": "LLM04810", "doc_id": "NCT02760459_inc", "case_bucket": "other", "source_criterion": "Age > 40 years (45) Primary knee osteoarthritis diagnosed using the American College of Rheumatology criteria (46) Undergoing elective, primary and unilateral total knee arthroplasty American Society of Anesthesiology (ASA) physical status class 1-3 BMI < 40 kg/m2", "candidate_expression": "((ASA) AND (Age > 40 years) AND (American Society of Anesthesiology physical status class 1-3) AND (BMI < 40 kg/m2) AND (Primary knee osteoarthritis American College of Rheumatology criteria) AND (total knee arthroplasty elective primary unilateral))"}
{"candidate_id": "LLM04811", "doc_id": "NCT03034837_exc", "case_bucket": "other", "source_criterion": "Can not cooperate with the treatment Can not obtain the child's parental consent", "candidate_expression": "((Can not obtain the child's parental consent) AND NOT (cooperate with the treatment) AND NOT (child's parental consent))"}
{"candidate_id": "LLM04812", "doc_id": "NCT03360981_inc", "case_bucket": "or", "source_criterion": "patients aged >18, <75, left ventricle ejection fraction (LVEF) >50%, multivessel coronary disease detected by coronarography, indication to receive a CABG, stable CAD. All diabetics and non diabetics.", "candidate_expression": "((>18, <75) AND (>50%) AND (LVEF) AND (indication to receive) AND (multivessel coronary disease) AND (stable) AND ((CABG) OR (CAD) OR (aged) OR (coronarography) OR (diabetics) OR (left ventricle ejection fraction) OR (non diabetics)))"}
{"candidate_id": "LLM04813", "doc_id": "NCT02779374_inc", "case_bucket": "scope", "source_criterion": "Women with POI: For the purpose of the research women is considered to have POI if she is aged less than 40 years and has amenorrhea of at least 4 month with FSH level above 25 IU/L (repeated twice >4 weeks apart).", "candidate_expression": "((>4 weeks apart) AND (FSH level) AND (POI) AND (Women) AND (above 25 IU/L) AND (aged) AND (amenorrhea) AND (at least 4 month) AND (less than 40 years) AND (repeated twice))"}
{"candidate_id": "LLM04814", "doc_id": "NCT02590653_inc", "case_bucket": "other", "source_criterion": "Signed Informed Consent Form Patients having physical and mental ability to participate in the study Patients of both sexes aged 35 to 65 years Presence of documented ST-elevation myocardial infarction confirmed by ECG, as well as troponin I and CK-MB levels. Presence of hemodynamically relevant stenosis of one artery (i.e., the infarct-related artery) confirmed by coronary angiography (CAG), with the occlusion of other arteries not exceeding 30%.", "candidate_expression": "((35 to 65 years) AND (CAG) AND (CK-MB) AND (ECG) AND (Patients having physical and mental ability to participate in the study) AND (ST-elevation myocardial infarction) AND (Signed Informed Consent Form) AND (aged) AND (both) AND (coronary angiography) AND (hemodynamically relevant) AND (infarct-related artery) AND (not exceeding 30%) AND (occlusion of other arteries) AND (one) AND (sexes) AND (stenosis of artery) AND (troponin I))"}
{"candidate_id": "LLM04815", "doc_id": "NCT03129555_inc", "case_bucket": "or", "source_criterion": "A diagnosis of VTE in outpatient clinic or as discharge diagnosis after hospitalization. A claimed prescription of a NOAC from a Danish pharmacy within 14 days of discharge or outpatient clinic visit.", "candidate_expression": "((NOAC Danish pharmacy within 14 days of discharge or outpatient clinic visit) AND (VTE) AND (discharge) AND (hospitalization) AND (outpatient clinic) AND (outpatient clinic discharge diagnosis) AND (outpatient clinic visit) AND (prescription claimed))"}
{"candidate_id": "LLM04816", "doc_id": "NCT00426751_exc", "case_bucket": "or", "source_criterion": "Subjects not able to give informed consent Left Bundle Branch Block Thrombolytic therapy within 24 hours before randomization Oral anticoagulation with International Normalized Ratio (INR) > 2 Known platelets < 100.000/µl or known hemorrhagic diathesis Stroke or Transient Ischemic Attack (TIA) within the past 6 months or any permanent residual neurological defect Evidence of an active gastrointestinal or urogenital bleeding Major surgery within 6 weeks History of allergic reaction to abciximab or eptifibatide or any component used in the study (including contrast media) Known severe renal (creatinine clearance <30ml/min) or hepatic insufficiency as well as Alanine transaminase (ALT)/aspartate transaminase (AST) elevations = 3xUpper limit normal (ULN); isolated AST-elevation is not considered an exclusion criteria from study participation Severe concomitant disease with life expectation < 1 year Subject has participated in any study using an investigational drug or device within 30 days or within 5 half-lives of the investigational drug (whichever is longer) of entry into this study. Subjects who will be inaccessible due to geographic or social factors during treatment or follow-up In France, a subject is neither affiliated with nor a beneficiary of a social security category.", "candidate_expression": "((3xUpper limit normal (ULN)) AND (< 1 year) AND (< 100.000/µl) AND (<30ml/min) AND (> 2) AND (Alanine transaminase (ALT)) AND (History) AND (International Normalized Ratio (INR)) AND (Left Bundle Branch Block) AND (Major surgery) AND (Oral anticoagulation) AND (Severe disease) AND (Stroke) AND (Thrombolytic therapy) AND (Transient Ischemic Attack (TIA)) AND (abciximab) AND (able to) AND (active) AND (allergic reaction) AND (aspartate transaminase (AST)) AND (component used in the study) AND (concomitant) AND (contrast media) AND (creatinine clearance) AND (device) AND (during treatment or follow-up) AND (elevations) AND (eptifibatide) AND (follow-up) AND (gastrointestinal bleeding) AND (give informed consent) AND (hemorrhagic diathesis) AND (hepatic insufficiency) AND (inaccessible) AND (investigational drug) AND (life expectation) AND (not) AND (of the investigational drug) AND (of the investigational drug within 30 days) AND (participated in any study) AND (platelets) AND (randomization) AND (renal insufficiency) AND (residual neurological defect) AND (severe) AND (treatment) AND (urogenital bleeding) AND (within 24 hours before randomization) AND (within 5 half-lives of the investigational drug) AND (within 6 weeks) AND (within the past 6 months))"}
{"candidate_id": "LLM04817", "doc_id": "NCT00061308_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential that do not practice adequate contraception. Pregnant or lactating. Received more than one primary chemotherapy regimen. Concomitant or previous malignancies with the exception of adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, incidental carcinoid, or other cancer from which the patient has been disease free for 5 years. Active uncontrolled infection requiring antibiotics. Concurrent severe medical problems unrelated to the malignancy which would limit full compliance with the study. Received radiation to more than 10% of bone. Prior treatment with topotecan or gemcitabine. Hypersensitivity to camptothecin or nucleoside analogues. Use of an investigational agent within 30 days.", "candidate_expression": "((Hypersensitivity) AND (Women) AND (antibiotics) AND (child-bearing potential) AND (infection Active uncontrolled) AND (investigational agent within 30 days) AND (malignancies) AND (malignancy) AND (medical problems Concurrent severe unrelated to the malignancy limit full compliance with the study) AND (primary chemotherapy regimen more than one) AND (radiation bone) AND (treatment Prior) AND NOT (adequate contraception) AND ((Concomitant) OR (previous)) AND ((basal cell skin cancer) OR (in situ cervical cancer) OR (incidental carcinoid) OR (other cancer) OR (squamous cell skin cancer)) AND ((gemcitabine) OR (topotecan)) AND ((camptothecin) OR (nucleoside analogues)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM04818", "doc_id": "NCT02118467_exc", "case_bucket": "other", "source_criterion": "Cardiopulmonary arrest Pregnancy Severe right heart failure", "candidate_expression": "((Cardiopulmonary arrest) AND (Pregnancy) AND (right heart failure Severe))"}
{"candidate_id": "LLM04819", "doc_id": "NCT01715584_exc", "case_bucket": "or", "source_criterion": "patient refusal age less than 40 or over 80 years combined surgical procedures emergency surgery Left ventricular ejection fraction less than 50 per cent calculated creatinine clearance less than 60 mL per minute", "candidate_expression": "((Left ventricular ejection fraction) AND (age) AND (calculated creatinine clearance) AND (combined surgical procedures) AND (emergency surgery) AND (less than 40) AND (less than 50 per cent) AND (less than 60 mL per minute) AND (over 80 years) AND (patient refusal))"}
{"candidate_id": "LLM04820", "doc_id": "NCT02527512_exc", "case_bucket": "or", "source_criterion": "Documented renal failure documented allergy to iodine or shellfish previous spine fusion surgery undergoing elective posterior spine single-level instrumentation surgery undergoing anterior spine multi-level instrumentation surgery current antibiotic use.", "candidate_expression": "((allergy) AND (anterior spine) AND (antibiotic use) AND (current) AND (elective) AND (multi-level instrumentation surgery) AND (posterior spine) AND (previous) AND (renal failure) AND (single-level instrumentation surgery) AND (spine fusion surgery) AND (undergoing) AND ((iodine) OR (shellfish)))"}
{"candidate_id": "LLM04821", "doc_id": "NCT02691793_inc", "case_bucket": "or", "source_criterion": "Provision of fully informed consent prior to study specific procedures. Patients must be >= 19 years of age RET fusion positive or FGFR2 fusion/other FGFR mutation Refractory solid tumor and/or specific sensitivity to Sunitinib by Avatar scan that has progressed following standard therapy or that has not responded to standard therapy or for which there is no standard therapy. ECOG Performance status0-2 Have measurable or evaluated disease based on RECIST 1.1 as determined by investigator. Absolute neutrophil count >= 1.5 x 109/L, Hemoglobin >= 9g/dL, Platelets>=100 x 109/L Bilirubin <= 1.5 x upper limit of normal AST/ALT <= 2.5 X upper limit of normal(5.0 x upper limit of normal, for subject with liver metastases) Creatinine<= 1.5 X UNL Patients of child-bearing potential should be using adequate contraceptive measures should not be breast feeding and must have a negative pregnancy test prior to start of dosing Adequate heart function", "candidate_expression": "((ALT 5.0 x upper limit of normal) AND (ALT <= 2.5 X upper limit of normal() AND (AST 5.0 x upper limit of normal) AND (AST <= 2.5 X upper limit of normal() AND (Absolute neutrophil count >= 1.5 x 109/L) AND (Adequate heart function) AND (Bilirubin <= 1.5 x upper limit of normal) AND (Creatinine <= 1.5 X UNL) AND (ECOG Performance status 0-2) AND (Hemoglobin >= 9g/dL,) AND (Platelets >=100 x 109/L) AND (Provision of fully informed consent prior to study specific procedures) AND (adequate contraceptive measures) AND (age >= 19 years) AND (child-bearing potential) AND (heart function Adequate) AND (liver metastases) AND (pregnancy test negative prior to start of dosing) AND NOT (breast feeding) AND ((RET fusion positive) OR (Sunitinib sensitivity) OR (solid tumor Refractory)) AND ((FGFR mutation) OR (FGFR2 fusion)))"}
{"candidate_id": "LLM04822", "doc_id": "NCT03134196_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04823", "doc_id": "NCT03511521_exc", "case_bucket": "or", "source_criterion": "Patients with 2 or more doses of methylprednisolone/prednisone per day Steroids other than methylprednisolone or prednisone Pregnancy estimated glomerular filtration rate (eGFR) < 45 ml/min/1.73m2", "candidate_expression": "((2 or more doses per day) AND (< 45 ml/min/1.73m2) AND (Pregnancy) AND (Steroids) AND (estimated glomerular filtration rate (eGFR)) AND (methylprednisolone) AND (other than) AND (prednisone))"}
{"candidate_id": "LLM04824", "doc_id": "NCT02456129_exc", "case_bucket": "or", "source_criterion": "Incompletely cured pre-existing diseases for which it can be assumed that the absorption, distribution, metabolism, elimination or effects of the study drugs will not be normal Known or suspected liver diseases Clinically relevant findings(e.g. blood pressure, electrocardiogram(ECG); physical and gynecological examination, laboratory examination)", "candidate_expression": "((Clinically relevant) AND (can be assumed) AND (findings Clinically relevant) AND (liver diseases) AND (pre-existing diseases Incompletely cured) AND (suspected) AND ((blood pressure) OR (electrocardiogram(ECG)) OR (gynecological examination) OR (laboratory examination) OR (physical examination)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM04825", "doc_id": "NCT01793831_inc", "case_bucket": "or", "source_criterion": "Moderate to severe CD define as HBI score > 4. Montreal classification: no limitation, except age> 6.", "candidate_expression": "((CD Moderate severe) AND (HBI score > 4))"}
```
