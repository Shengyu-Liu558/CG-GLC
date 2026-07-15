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
{"candidate_id": "LLM02051", "doc_id": "NCT03275584_inc", "case_bucket": "other", "source_criterion": "Adult patient being referred for clinically indicated positron emission tomography myocardial perfusion imaging at the Centre hospitalier de l'Université de Montréal", "candidate_expression": "((Adult) AND (Centre hospitalier de l'Université de Montréal) AND (clinically indicated) AND (positron emission tomography myocardial perfusion imaging))"}
{"candidate_id": "LLM02052", "doc_id": "NCT02731794_exc", "case_bucket": "other", "source_criterion": "myocardial infarction within the preceding 4 weeks severe valve disease requiring valve replacement cardiac reoperations", "candidate_expression": "((cardiac reoperations) AND (myocardial infarction within the preceding 4 weeks) AND (valve disease severe requiring valve replacement) AND (valve replacement))"}
{"candidate_id": "LLM02053", "doc_id": "NCT02195024_inc", "case_bucket": "or", "source_criterion": "Approved clinical indication for pectoral pacemaker exchange (e.g. elective replacement indication (ERI), end of service (EOS)) a single or dual chamber MRI conditional pacemaker (BSCI) or Any comparable successor IPG (MRI conditional system, BSCI) compatible with Implanted Fineline-II-leads (BSCI), MRI conditional The ascertained lead impedance is between 200 and 1500 Ohm. All pacing capture thresholds (PCT) do not exceed 2.0 V @0.4 or 0.5 ms in pacemaker dependent patients Male or female 18 years or older Understand the nature of the procedure Give written informed consent Able to complete all testing required by the clinical protocol Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms Patient body height greater or equal to 140 cm Pectoral implanted device Subjects who are able and willing to undergo elective cardiac magnetic resonance (MR) scanning without sedation (MRI-group) Subjects who are geographically stable and available for follow-up at the study center for the length of the study", "candidate_expression": "((Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms) AND (Able to complete all testing required by the clinical protocol) AND (BSCI) AND (Give written informed consent) AND (Implanted Fineline-II-leads) AND (MR) AND (PCT) AND (Pectoral implanted device) AND (ascertained lead impedance between 200 and 1500 Ohm) AND (at the study center for the length of the study) AND (available for follow-up) AND (body height greater or equal to 140 cm) AND (cardiac magnetic resonance scanning willing to undergo elective without sedation) AND (clinical indication) AND (geographically stable) AND (pacemaker MRI conditional) AND (pacemaker dependent) AND (pacing capture thresholds) AND (pectoral pacemaker exchange) AND (successor IPG comparable) AND (years or older 18 years or older) AND ((BSCI) OR (MRI conditional system)) AND ((elective replacement indication (ERI)) OR (end of service (EOS))) AND ((Male) OR (female)) AND ((dual chamber) OR (single chamber)))"}
{"candidate_id": "LLM02054", "doc_id": "NCT03079141_inc", "case_bucket": "other", "source_criterion": "Age of = 18 years of age and able to give written informed consent; Active chronic central serous chorioretinopathy (cCSC); Subjective visual loss > 6 weeks, interpreted as onset of active disease; Foveal subretinal fluid (SRF), on optical coherence tomography (OCT), at Baseline Examination; =1 ill-defined hyperfluorescent leakage areas on fluorescein angiography (FA) with retinal pigment epithelial window defect(s) that are compatible with cCSC; Hyperfluorescent areas on indocyanine green angiography (ICGA).", "candidate_expression": "((Age = 18 years) AND (Foveal subretinal fluid (SRF)) AND (Hyperfluorescent areas) AND (Subjective visual loss > 6 weeks) AND (able to give written informed consent) AND (central serous chorioretinopathy (cCSC) Active chronic) AND (fluorescein angiography (FA)) AND (hyperfluorescent leakage areas =1 ill-defined) AND (indocyanine green angiography (ICGA)) AND (optical coherence tomography (OCT) at Baseline Examination) AND (retinal pigment epithelial window defect(s)))"}
{"candidate_id": "LLM02055", "doc_id": "NCT03196843_inc", "case_bucket": "or", "source_criterion": "Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent. Histopathologic confirmed squamous cell carcinoma of head and neck ,including oral cavity, oropharynx, larynx, or hypopharynx. Ages=65 years,Not limited to gender. ECOG performance status =2. Patients with surgical contraindication or reject to surgery. Postoperative TNM(primary tumor,regional nodes,metastasis) staging III~IV, positive surgical margin. without evidence of distant metastases. No contraindication to chemoradiotherapy. Life expectancy > 3 months. Available Organ function: white blood cell=3.5×109/L, Neutrophils =1.5×109/L, Hemoglobin =80g/L, Blood platelet>100×109/L; Alanine aminotransferase (ALT) and Aspartate aminotransferase (AST)= 2.5 upper limit of normal(ULN); Total bilirubin (TBIL) <1.5 ULN;serum creatinine=1.5 ULN; creatinine clearance of = 50ml/min", "candidate_expression": "((Ages =65 years oropharynx larynx hypopharynx) AND (Alanine aminotransferase (ALT) = 2.5 upper limit of normal(ULN)) AND (Aspartate aminotransferase (AST) = 2.5 upper limit of normal(ULN)) AND (Before participate in the study, patients must understand the treatment plan and willing to participate in the study. Patients must have signed an approved informed consent.) AND (Blood platelet >100×109/L) AND (ECOG performance status =2) AND (Hemoglobin =80g/L) AND (Histopathologic) AND (Life expectancy > 3 months) AND (Neutrophils =1.5×109/L) AND (TNM staging Postoperative III~IV,) AND (Total bilirubin (TBIL) <1.5 ULN) AND (chemoradiotherapy) AND (contraindication) AND (creatinine clearance = 50ml/min) AND (reject) AND (serum creatinine =1.5 ULN) AND (squamous cell carcinoma Histopathologic confirmed head and neck oral cavity) AND (surgery) AND (surgical) AND (surgical margin positive) AND (white blood cell =3.5×109/L) AND NOT (distant metastases evidence) AND NOT (contraindication))"}
{"candidate_id": "LLM02056", "doc_id": "NCT01717911_inc", "case_bucket": "other", "source_criterion": "Recently diagnosed type 2 diabetic patients. Fasting plasma glucose between 200-300 mg/dl (A1C level between 7% and 10%). Those who age between 30 and 80 years old and can inject insulin by themselves.", "candidate_expression": "((A1C level between 7% and 10%) AND (Fasting plasma glucose between 200-300 mg/dl) AND (age between 30 and 80 years old) AND (inject insulin can) AND (type 2 diabetic Recently diagnosed))"}
{"candidate_id": "LLM02057", "doc_id": "NCT02112734_inc", "case_bucket": "other", "source_criterion": "Healthy, term, breastfeeding infants who will be predominately breastfed for at least 6-months. This will be determined by answering yes/no to question 'do you intend to breastfeed until your infant is at least 6 months of age.'", "candidate_expression": "((Healthy) AND (breastfeeding) AND (for at least 6-months) AND (infants) AND (predominately breastfed) AND (term))"}
{"candidate_id": "LLM02058", "doc_id": "NCT01991743_exc", "case_bucket": "or", "source_criterion": "Refusal Contraindication to neuraxial (coagulopathy, anticoagulant use, local infection, sepsis etc) .Rupture of membranes. Drop-out: Patients may choose to drop-out of the study at any time. The physicians involved in this study may choose to end a patient's involvement in the study at their discretion.", "candidate_expression": "((Contraindication) AND (Rupture of membranes) AND (anticoagulant) AND (coagulopathy) AND (local infection) AND (neuraxial) AND (sepsis))"}
{"candidate_id": "LLM02059", "doc_id": "NCT02838810_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or AFP >2 ULN or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients with a previous use of IFN anti hepatitis B virus treatment or have NAs drug resistance. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((>2 ULN) AND (AFP) AND (HIV infection) AND (Hepatocellular Carcinoma) AND (IFN) AND (NAs drug) AND (Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (anti hepatitis B virus) AND (antineoplastic therapy) AND (autoimmune diseases) AND (complications) AND (concomitant) AND (congenital immune deficiency diseases) AND (diabetes) AND (gastrointestinal bleeding) AND (hepatic encephalopathy) AND (hepatorenal syndrome) AND (immunomodulatory therapy) AND (important) AND (infection) AND (liver cirrhosis) AND (liver diseases) AND (malignancies) AND (organ dysfunctions) AND (past 12 months) AND (resistance) AND (serious))"}
{"candidate_id": "LLM02060", "doc_id": "NCT03077204_inc", "case_bucket": "or", "source_criterion": "Age>18 years Scheduled 1 or 2-level ACDF spine surgery The capacity to provide informed consent. Degenerative Disc Disease (as defined by neck pain of discogenic origin with degeneration of the disc confirmed by patient history and radiographic studies) Trauma (including fractures) Tumors Deformities or curvatures (including kyphosis, lordosis, or scoliosis) Pseudoarthrosis Failed previous fusion Decompression of the spinal cord following total or partial cervical vertebrectomy Spondylolisthesis Spinal stenosis Patients with current or recent history of malignancy or infectious disease. The inability to provide informed consent. Subject has marked local inflammation Subject has any mental or neuromuscular disorder which would create an unacceptable risk of fixation failure or complications in postoperative care. Subject has a bone stock compromised by disease, infection or prior implantation which cannot provide adequate support and/or fixation to the devices. Subject has bone abnormalities preventing safe screw fixation. Subject has any open wounds. Subject has rapid joint disease, bone absorption, osteopenia, osteomalacia, and/or osteoporosis. Osteoporosis or osteopenia are relative contraindications, since this condition may limit the degree of obtainable correction and/or the amount of mechanical fixation. Subject has a documented or suspected metal sensitivity. Subject is pregnant. Subject has anatomical structures or physiological performance that would interfere with implant utilization. Subject has inadequate tissue coverage over the operative site. Subject has other medical or surgical conditions which would preclude the potential benefit of surgery, such as congenital abnormalities, immunosuppressive disease, elevation of sedimentation rate unexplained by other diseases, elevation of white blood count (WBC), or marked left shift in the WBC differential count. Note: The Aviator Anterior Cervical Plating System is not approved or intended for screw attachment to the posterior elements (pedicles) of the cervical, thoracic, or lumbar spine. The surgeon must consider the levels of implantation, patient weight, patient activity level, and other patient conditions which may impact on the performance of the system.", "candidate_expression": "((1 -level) AND (2-level) AND (>18 years) AND (ACDF spine surgery) AND (Age) AND (Decompression of the spinal cord) AND (Deformities) AND (Degenerative Disc Disease) AND (Failed) AND (Osteoporosis) AND (Pseudoarthrosis) AND (Spinal stenosis) AND (Spondylolisthesis) AND (Trauma) AND (Tumors) AND (WBC differential count) AND (adequate support) AND (anatomical structures) AND (bone abnormalities) AND (bone absorption) AND (bone stock compromised) AND (cannot) AND (complications) AND (congenital abnormalities) AND (contraindications) AND (current) AND (curvatures) AND (degeneration of the disc) AND (discogenic origin) AND (disease) AND (documented) AND (elevation) AND (fixation failure) AND (fixation to the devices) AND (fractures) AND (fusion) AND (history) AND (immunosuppressive disease) AND (implant) AND (implantation) AND (inadequate tissue coverage) AND (infection) AND (infectious disease) AND (interfere with utilization) AND (kyphosis) AND (left shift) AND (local inflammation) AND (lordosis) AND (malignancy) AND (marked) AND (medical conditions) AND (mental disorder) AND (metal) AND (neck pain) AND (neuromuscular disorder) AND (open wounds) AND (operative site) AND (osteomalacia) AND (osteopenia) AND (osteoporosis) AND (partial cervical vertebrectomy) AND (patient history) AND (physiological performance) AND (preclude) AND (pregnant) AND (preventing) AND (previous) AND (prior) AND (radiographic studies) AND (rapid joint disease) AND (recent) AND (relative) AND (risk of) AND (safe) AND (scoliosis) AND (screw fixation) AND (sedimentation rate) AND (sensitivity) AND (surgery) AND (surgical conditions) AND (suspected) AND (total cervical vertebrectomy) AND (unacceptable) AND (unexplained by other diseases) AND (white blood count (WBC)))"}
{"candidate_id": "LLM02061", "doc_id": "NCT02504203_inc", "case_bucket": "other", "source_criterion": "Children born outside the cluster, and returning more than 72 hours after the delivery Children that the nurse evaluates to die within the next 24 hours.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02062", "doc_id": "NCT02527512_inc", "case_bucket": "other", "source_criterion": "Age 3 to 18 years on day of surgery diagnosis of spinal deformity undergoing elective posterior spine multi-level instrumentation surgery", "candidate_expression": "((3 to 18 years) AND (Age) AND (elective) AND (multi-level instrumentation surgery) AND (on day of surgery) AND (posterior spine) AND (spinal deformity) AND (undergoing))"}
{"candidate_id": "LLM02063", "doc_id": "NCT02205931_inc", "case_bucket": "other", "source_criterion": "Age between 1 month and 24 months of age (not beyond second birthday at baseline). Diagnosis of epilepsy confirmed. At least an average of 4 seizures/week in baseline period. Failed response to previous trial of two anti-epileptic drugs. In the case of infantile spasms this could include a trial of corticosteroids. Children with written informed consent from parent/guardian.", "candidate_expression": "((Age) AND (At least an average of 4 /week) AND (Children with written informed consent from parent/guardian) AND (Failed) AND (anti-epileptic drugs) AND (between 1 month and 24 months of age) AND (corticosteroids) AND (epilepsy) AND (response) AND (seizures) AND (two))"}
{"candidate_id": "LLM02064", "doc_id": "NCT02940912_inc", "case_bucket": "or", "source_criterion": "Idiopathic Parkinson's disease ( Hughes AJ et al. 2001) Patients with motor fluctuations Chronic Insomnia disorder criteria according to the criteria of DMS- V ( American Psychiatric Association, 2013) and insomnia severity index > 15 Able to use independently the device required for treatment by apomorphine Collection of written informed consent (legal obligation for any project under the public health law , bioethics laws and / or CNIL) . Affiliate to social security or beneficiary of such a regime", "candidate_expression": "((Chronic Insomnia disorder criteria of DMS- V) AND (Parkinson's disease Idiopathic) AND (apomorphine) AND (device) AND (insomnia severity index > 15) AND (motor fluctuations) AND ((Affiliate to social security) OR (social security beneficiary)))"}
{"candidate_id": "LLM02065", "doc_id": "NCT02783859_inc", "case_bucket": "or", "source_criterion": "Hospitalised children aged 3-mo to 5-yrs (in Darwin, children have to be Indigenous) Have features of severe pneumonia on admission (temperature >37.5 celsius or a history of fever at home or observed at the referring clinic, age-adjusted tachypnoea [respiratory rate>50 if <12-months; respiratory rate>40 if >12-months] with chest wall recession and/or oxygen saturation <92% in air), and consolidation on chest X-ray as diagnosed by treating clinician After 1-3 days of IV antibiotics, are afebrile, with improved respiratory symptoms and signs, oxygen saturation>90% in air and are ready to be switched to oral amoxicillin-clavulanate, and Have symptoms of no longer than 7 days at point of hospitalisation.", "candidate_expression": "((3-mo to 5-yrs) AND (<12-months) AND (<92% in air) AND (>12-months) AND (>37.5 celsius) AND (>40) AND (>50) AND (Hospitalised) AND (age) AND (aged) AND (chest X-ray) AND (chest wall recession) AND (children) AND (consolidation) AND (hospitalisation) AND (no longer than 7 days at point of hospitalisation) AND (oxygen saturation) AND (pneumonia) AND (respiratory rate) AND (severe) AND (symptoms) AND (tachypnoea) AND (temperature))"}
{"candidate_id": "LLM02066", "doc_id": "NCT02743598_inc", "case_bucket": "other", "source_criterion": "HIV controlled on therapy for at least 12 weeks Viral load < 200 copies BMI >27 to 45 Diagnosis of DM type 2 with A1-C >7 to 15 Participants must be willing to comply with all study related procedures", "candidate_expression": "((A1-C >7 to 15) AND (BMI >27 to 45) AND (DM type 2) AND (HIV controlled at least 12 weeks) AND (Participants must be willing to comply with all study related procedures) AND (Viral load < 200 copies))"}
{"candidate_id": "LLM02067", "doc_id": "NCT03103204_inc", "case_bucket": "or", "source_criterion": "Moderate to advanced generalized chronic periodontitis Body mass index: > 18.5 kg/m2 Minimum of 12 natural teeth Smokers, non-smokers or former-smokers", "candidate_expression": "((> 18.5 kg/m2) AND (Body mass index) AND (Minimum of 12) AND (Moderate to advanced) AND (generalized chronic periodontitis) AND (natural teeth) AND ((Smokers) OR (former-smokers) OR (non-smokers)))"}
{"candidate_id": "LLM02068", "doc_id": "NCT01116973_inc", "case_bucket": "or", "source_criterion": "Subject's ability to lay in a supine position with their hands at their sides during CVP measurements A consent form signed by the patient or patient's representative Subjects that are age 18-90 Subjects that have an indwelling CICC and are transitioning to a PICC for long-term IV access CICC placed in the internal jugular vein or subclavian vein position", "candidate_expression": "((A consent form signed by the patient or patient's representative) AND (CICC placed in the internal jugular vein position in the subclavian vein position) AND (CVP measurements) AND (PICC) AND (ability to lay in a supine position with their hands at their sides during CVP measurements) AND (age 18-90) AND (indwelling CICC) AND (transitioning to a PICC))"}
{"candidate_id": "LLM02069", "doc_id": "NCT02298504_exc", "case_bucket": "or", "source_criterion": "Teeth with clinical symptoms of irriversible pulpitis or pulp necrosis or acute dental infection Children with systemic illness that contraindicated vital pulp treatment such a sickle cell disease Teeth that are not restorable", "candidate_expression": "((Teeth) AND (Teeth that are not restorable) AND (acute dental infection) AND (contraindicated) AND (irriversible pulpitis) AND (pulp necrosis) AND (sickle cell disease) AND (systemic illness) AND (vital pulp treatment))"}
{"candidate_id": "LLM02070", "doc_id": "NCT03231982_exc", "case_bucket": "or", "source_criterion": "The difference in blood pressure between the selected arm versus non-selected arm is = 20 mmHg for siSBP and = 10 mmHg for siDBP at Visit 1 (screening). Blood pressure taken at screening and randomization is = 180 mmHg for siSBP or = 110 mmHg for siDBP. Diagnosed with secondary hypertension or suspected of secondary hypertension [e.g., renovascular disease, adrenal medullary and cortical hyperfunction, coarctation of the aorta, hyperaldosteronism, unilateral or bilateral renal artery stenosis, Cushing's syndrome, pheochromocytoma, polycystic kidney disease, etc.] Patients with symptomatic orthostatic hypertension (the difference in the blood pressures between measured at supine position and measured at standing position is = 20 mmHg for siSBP and = 10 mmHg for siDBP) Diagnosis of type 1 diabetes mellitus (DM) or uncontrolled DM (patients on insulin therapy or with HbA1c > 9%) Patients with severe cardiac conditions: heart failure (NYHA Class 3 or 4), history of ischemic cardiac disease (unstable angina, myocardial infarction), peripheral vascular diseases, percutaneous transluminal angioplasty or coronary artery bypass graft within recent 6 months. Patients with clinically significant ventricular tachycardia, atrial fibrillation, atrial flutter or other clinically significant arrhythmia at the discretion of the investigator Patients with hypertrophic occlusive myocardiopathy, severe occlusive coronary artery disease, aortic stenosis, hemodynamically significant aortic valve or mitral valve stenosis History of cardiogenic shock Presence of severe cerebrovascular disorders (diagnosis of stroke, cerebral infarction or cerebral hemorrhage within recent 6 months) History or current evidence of wasting, autoimmune (such as rheumatoid arthritis and systemic lupus erythematosus) or connective tissue diseases Known diagnosis of moderate or malignant retinopathy (including retinal hemorrhage, visual disturbance and retinal microaneurysm within 6 months) Patients with surgical or medical intestinal diseases or having received surgeries that could interfere with drug absorption distribution, metabolism and elimination History of malignancy including leukemia and lymphoma within recent 5 years except for localized basal cell carcinoma of the skin) Patients with any inflammatory diseases requiring chronic anti-inflammatory therapy Renal failure on dialysis AST or ALT >2 x upper limit of normal (ULN) Serum creatinine > 1.5 x ULN Serum potassium < 3.5 mmol/L or >5.5 mmol/L Needs for co-administration of non-study antihypertensive agents or contraindicated medications during the study History of hypersensitivity to ARBs or dihydropyridines History of angioedema to treatment with ACE inhibitors or ARBs Pregnant or lactating women and female volunteers of childbearing potential (except for women who are surgically sterile) who are not willing to use an adequate method of contraception (oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening. History of drug or alcohol abuse within recent 1 year Patients having received any other investigational product within recent 12 weeks Conditions which render a subject ineligible for the study at the discretion of the investigator", "candidate_expression": "(((oral contraceptives, intrauterine device, condom, etc.) during the study. Women of childbearing potential who are not surgically sterile will be allowed to participate in the study only if they have negative pregnancy test at Visit 1 (screening) and should continue to use medically acceptable method of contraception (basic body temperature method and rhythm method will not be allowed). Women with no menses for = 12 months will be considered as postmenopausal state and method of contraception using hormonal contraception such as oral contraceptive should be initiated from or prior to the screening.) AND (ACE inhibitors) AND (ALT) AND (ARBs) AND (AST) AND (Blood pressure at randomization at screening) AND (Cushing's syndrome) AND (DM uncontrolled) AND (HbA1c > 9%) AND (History current) AND (NYHA Class 3 or 4) AND (Pregnant) AND (Renal failure) AND (Serum creatinine > 1.5 x ULN) AND (Serum potassium < 3.5 mmol/L >5.5 mmol/L) AND (adequate method of contraception willing to) AND (adrenal medullary hyperfunction) AND (alcohol abuse) AND (angioedema History of) AND (anti-inflammatory therapy) AND (anti-inflammatory therapy chronic) AND (antihypertensive agents co-administration during the study non-study) AND (aortic stenosis) AND (aortic valve stenosis) AND (arrhythmia clinically significant) AND (atrial fibrillation) AND (atrial flutter) AND (autoimmune diseases moderate) AND (cardiac conditions severe) AND (cardiogenic shock History) AND (cerebral hemorrhage) AND (cerebral infarction) AND (cerebrovascular disorders severe) AND (childbearing potential) AND (coarctation of the aorta) AND (connective tissue diseases) AND (contraindicated medications co-administration during the study) AND (coronary artery bypass graft) AND (cortical hyperfunction) AND (dialysis) AND (difference in blood pressure selected arm versus non-selected arm at Visit 1) AND (difference in the blood pressures measured at supine position and measured at standing position) AND (dihydropyridines) AND (drug abuse) AND (female) AND (heart failure) AND (hyperaldosteronism unilateral bilateral) AND (hypersensitivity History of) AND (hypertension secondary) AND (hypertension suspected secondary) AND (hypertrophic occlusive myocardiopathy) AND (inflammatory diseases) AND (insulin therapy) AND (intestinal diseases medical) AND (ischemic cardiac disease history) AND (lactating) AND (leukemia) AND (lymphoma) AND (malignancy History of within recent 5 years) AND (mitral valve stenosis) AND (myocardial infarction) AND (occlusive coronary artery disease severe) AND (orthostatic hypertension symptomatic) AND (other investigational product within recent 12 weeks) AND (percutaneous transluminal angioplasty) AND (peripheral vascular diseases) AND (pheochromocytoma) AND (polycystic kidney disease) AND (renal artery stenosis) AND (renovascular disease) AND (retinal hemorrhage) AND (retinal microaneurysm surgical) AND (retinopathy malignant) AND (rheumatoid arthritis) AND (siDBP = 10 mmHg) AND (siDBP = 110 mmHg) AND (siSBP = 180 mmHg) AND (siSBP = 20 mmHg) AND (stroke) AND (surgeries could interfere with drug absorption distribution could interfere with drug metabolism could interfere with drug elimination) AND (systemic lupus erythematosus) AND (treatment) AND (type 1 diabetes mellitus (DM)) AND (unstable angina) AND (ventricular tachycardia) AND (visual disturbance) AND (wasting) AND (women) AND NOT (localized basal cell carcinoma of the skin))"}
{"candidate_id": "LLM02071", "doc_id": "NCT02968342_inc", "case_bucket": "other", "source_criterion": "Menopausal status Sexually active", "candidate_expression": "((Menopausal) AND (Sexually active))"}
{"candidate_id": "LLM02072", "doc_id": "NCT03282006_inc", "case_bucket": "or", "source_criterion": "E.coli in blood culture AND identical isolate in urine sample (>= 1.000 CFU) OR relevant clinical signs of UTI", "candidate_expression": "((>= 1.000) AND (CFU) AND (E.coli) AND (UTI) AND (blood culture) AND (clinical signs) AND (identical isolate) AND (urine sample))"}
{"candidate_id": "LLM02073", "doc_id": "NCT00749112_exc", "case_bucket": "or", "source_criterion": "Current viral or bacterial infection. Positive serology for HIV, HCV, HBV.", "candidate_expression": "((bacterial infection) AND (infection viral) AND (serology for HBV) AND (serology for HCV) AND (serology for HIV))"}
{"candidate_id": "LLM02074", "doc_id": "NCT02231892_inc", "case_bucket": "or", "source_criterion": "Subjects must: 1. Be able to give valid informed consent 2. Be 18 55 years of age. 1. Justification: Many neural processes change with age, and these changes could introduce unwanted variability in both behavioral and MRI signals. In addition, the risk of difficult-to-detect medical abnormalities such as silent cerebral infarcts increases with age. 2. Screening tool: History. Government-issued forms of identification (e.g. driver s license, birth certificate) will be required when participant appears to be out of age range. 3. Be in good health. 1. Justification: Many illnesses may alter neural functioning as well as fMRI signals. 2. Screening tools: Medical Assessment, Medical History and Physical Examination. Medical assessments include: Vital Signs, EKG, oral HIV test, height/weight measurements, urinalysis and blood sample. Tests on the blood sample include CBC, complete metabolic profile, TSH, ESR, STS and HIV (if needed to confirm a positive salivary test for HIV). The following individual laboratory results will independently disqualify individuals: Cholesterol >250 mg/dl, Hemoglobin < 10.5 g/dl, WBC < 2400/microl, LFTs > 3Xnormal, HCG positive, Casual serum glucose > 200 mg/dl, Urine protein > 1+. The MAI will retain discretion to exclude at less extreme values, depending on the clinical presentation. (Serum glucose over 140 mg/dl will be followed up with a fasting serum glucose assessment. Those with fasting glucose below 100 mg/dl may be considered for the protocol. Others will be rejected and referred for work-up.) MAI will make the final judgment on any questionable lab results. 4. Right-handed. 1. Justification: Using right-handed individuals will reduce variability in BOLD MRI data. 2. Screening tool: Edinburgh Handedness Inventory. 5. Estimated IQ greater than or equal to 85 1. Justification: Subjects must be able to perform a cognitively challenging task to a high standard. 2. Screening tool: Wechsler Abbreviated Scale of Intelligence.", "candidate_expression": "((18 55 years) AND (< 10.5 g/dl) AND (< 2400/microl) AND (> 1+) AND (> 200 mg/dl) AND (> 3Xnormal) AND (>250 mg/dl) AND (Be able to give valid informed consent) AND (CBC) AND (EKG) AND (ESR) AND (Edinburgh Handedness Inventory) AND (Estimated IQ) AND (HIV) AND (History) AND (Medical Assessment) AND (Medical History) AND (Physical Examination) AND (Right-handed) AND (STS) AND (Serum glucose) AND (TSH) AND (The MAI will retain discretion to exclude at less extreme values, depending on the clinical presentation.) AND (Vital Signs) AND (Wechsler Abbreviated Scale of Intelligence) AND (age) AND (blood sample) AND (complete metabolic profile) AND (disqualify) AND (fasting serum glucose assessment) AND (good health) AND (greater than or equal to 85) AND (height measurement) AND (oral HIV test) AND (over 140 mg/dl) AND (positive) AND (salivary test for HIV) AND (urinalysis) AND (weight measurement) AND ((Cholesterol) OR (HCG) OR (Hemoglobin) OR (LFTs) OR (Urine protein) OR (WBC) OR (serum glucose)))"}
{"candidate_id": "LLM02075", "doc_id": "NCT01803828_inc", "case_bucket": "or", "source_criterion": "age 35-75 years; Diagnosis of Type 2 Diabetes from at least 3 years; HbA1c < 10%; normal blood pressure or controlled hypertension; BMI < 40;", "candidate_expression": "((BMI < 40) AND (HbA1c < 10%) AND (Type 2 Diabetes at least 3 years) AND (age 35-75 years) AND ((controlled hypertension) OR (normal blood pressure)))"}
```
