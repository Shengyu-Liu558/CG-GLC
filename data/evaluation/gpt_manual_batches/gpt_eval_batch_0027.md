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
{"candidate_id": "LLM00651", "doc_id": "NCT01912651_inc", "case_bucket": "or", "source_criterion": "all adult patients with a nasal or facial skin/soft tissue defect requiring reconstruction limited to or including a full-thickness skin graft", "candidate_expression": "((facial skin/soft tissue defect) AND (full-thickness skin graft) AND (nasal skin/soft tissue defect) AND (reconstruction) AND (requiring))"}
{"candidate_id": "LLM00652", "doc_id": "NCT02745704_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative and anti-HBeAg positive. Hepatitis B surface antigen (HBsAg) positive and <1500 IU/mL. Hepatitis B virus DNA not detectable(Roche Cobas).", "candidate_expression": "((<1500 IU/mL) AND (CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen) AND (Hepatitis B surface antigen) AND (Hepatitis B virus DNA) AND (NAs) AND (anti-HBeAg) AND (more than 12 months.) AND (negative) AND (not detectable) AND (positive))"}
{"candidate_id": "LLM00653", "doc_id": "NCT01184638_exc", "case_bucket": "other", "source_criterion": "With the history of cognitive disorders With chronic neurological disorders Cannot communicate with investigators Cannot stand general anesthesia", "candidate_expression": "((Cannot communicate) AND (Cannot stand) AND (chronic neurological disorders) AND (cognitive disorders) AND (general anesthesia))"}
{"candidate_id": "LLM00654", "doc_id": "NCT02985242_inc", "case_bucket": "or", "source_criterion": "women and men between 18 - 80 years of age type 2 diabetes mellitus early to moderate stage diabetic retinopathy (ETDRS: 20 (microaneurysms only) to 35 (microaneurysms/ hemorrhages and/or hard exsudates)) in one or both eyes stable HbA1c (± 0.5%) for at least 12 weeks antidiabetic treatment with either diet, metformin, DPP4, GLP1, pioglitazone, acarbose, or respective combinations HbA1c = 6.5 and = 10.0 % body mass index < 46 kg/m2 office blood pressure = 150/95 mmHg (confirmed on a second day; 24h ambulatory blood pressure measurement (ABPM) is allowed to check accuracy of office values; inclusion with 24h mean blood pressure = 145/90 mm Hg is possible); patients with hypertension should be treated according to current treatment guidelines at least 6 weeks after surgical sterilization by bilateral tubal ligation or bilateral oophorectomy hysterectomy = 50 years and in postmenopausal state > 1 year < 50 years and in postmenopausal state > 1 year with serum follicle stimulating hormone (FSH) > 40 IU/l and serum estrogen < 30 ng/l or a negative estrogen test, both at screening or women of childbearing potential with a negative serum beta human chorionic gonadotropin (ß-hCG) pregnancy test at screening who agree to meet one of the following criteria from the time of screening, during the study and for a period of 4 days following the last administration of study medication: correct use of one of the following accepted contraception methods: hormonal contraceptives (combined oral contraceptives, implants, transdermal patches, hormonal vaginal devices or injections with prolonged release), intrauterine device (IUD/IUS) or a double barrier method, e.g. condom and occlusive cap (diaphragm or cervical/vault caps) with spermicide (foam, gel, film, cream or suppository) true abstinence (periodic abstinence and withdrawal are not acceptable methods of contraception) sexual relationship only with female partners sterile male partners signed written informed consent and willingness to comply with treatment and follow-up procedures capability of understanding the investigational nature, potential risks and benefits of the clinical trial", "candidate_expression": "((20) AND (35) AND (< 46 kg/m2) AND (< 50 years and in postmenopausal state > 1 year with serum follicle stimulating hormone (FSH) > 40 IU/l and serum estrogen < 30 ng/l or a negative estrogen test, both at screening or women of childbearing potential with a negative serum beta human chorionic gonadotropin (ß-hCG) pregnancy test at screening who agree to meet one of the following criteria from the time of screening, during the study and for a period of 4 days following the last administration of study medication) AND (= 150/95 mmHg) AND (= 50) AND (= 6.5 and = 10.0 %) AND (> 1 year) AND (DPP4) AND (ETDRS) AND (GLP1) AND (HbA1c) AND (acarbose) AND (age) AND (antidiabetic treatment) AND (at least 12 weeks) AND (at least 6 weeks) AND (between 18 - 80 years) AND (bilateral oophorectomy) AND (bilateral tubal ligation) AND (blood pressure) AND (body mass index) AND (capability of understanding the investigational nature, potential risks and benefits of the clinical trial) AND (correct use of one of the following accepted contraception methods: hormonal contraceptives (combined oral contraceptives, implants, transdermal patches, hormonal vaginal devices or injections with prolonged release), intrauterine device (IUD/IUS) or a double barrier method, e.g. condom and occlusive cap (diaphragm or cervical/vault caps) with spermicide (foam, gel, film, cream or suppository)) AND (diabetic retinopathy) AND (diet) AND (early) AND (eyes) AND (hysterectomy) AND (men) AND (metformin) AND (moderate stage) AND (pioglitazone) AND (postmenopausal state) AND (signed written informed consent and willingness to comply with treatment and follow-up procedures) AND (surgical sterilization) AND (true abstinence (periodic abstinence and withdrawal are not acceptable methods of contraception)) AND (type 2 diabetes mellitus) AND (women) AND (years) AND (± 0.5%))"}
{"candidate_id": "LLM00655", "doc_id": "NCT00391690_exc", "case_bucket": "or", "source_criterion": "Prior treatment with a bisphosphonate Abnormal renal function as evidenced by a calculated creatinine clearance < 30 ml/minute. Corrected (adjusted for serum albumin) serum calcium concentration < 8.0 mg/dl (2.00 mmol/L) or ≥ 12.0 mg/dl (3.00 mmol/L). Patients with clinically symptomatic brain metastases History of diseases with influence on bone metabolism such as Paget's disease and primary hyperparathyroidism Severe physical or psychological concomitant diseases that might impair compliance with the provisions of the study protocol or that might impair the assessment of drug or patient safety, e.g. clinically significant ascites, cardiac failure, NYHA III or IV, clinically relevant pathologic findings in ECG Known hypersensitivity to zoledronic acid or other bisphosphonates Use of other investigational drugs 30 days prior to the date of randomization Known history or present abuse of alcohol or drugs Subjects who, in the opinion of the investigator, are unlikely to cooperate fully during the study Current active dental problems including infection of the teeth or jawbone (maxilla or mandibular); dental or fixture trauma, or a current or prior diagnosis of osteonecrosis of the jaw (ONJ), of exposed bone in the mouth, or of slow healing after dental procedures. Recent (within 6 weeks) or planned dental or jaw surgery (e.g. extraction, implants) Other protocol defined inclusion/exclusion criteria may apply.", "candidate_expression": "((2.00 mmol/L) AND (3.00 mmol/L) AND (30 days prior to the date of randomization) AND (< 30 ml/minute) AND (< 8.0 mg/dl) AND (Abnormal) AND (Corrected serum calcium concentration) AND (Current) AND (ECG) AND (History) AND (III or IV) AND (NYHA) AND (Paget's disease) AND (Prior) AND (Recent) AND (abuse of alcohol) AND (abuse of drugs) AND (ascites) AND (bisphosphonate) AND (brain metastases) AND (calculated creatinine clearance) AND (cardiac failure) AND (clinically relevant) AND (clinically significant) AND (clinically symptomatic) AND (current) AND (dental problems) AND (dental surgery) AND (dental trauma) AND (diseases with influence on bone metabolism) AND (exposed bone in the mouth) AND (extraction) AND (fixture trauma) AND (history) AND (hypersensitivity) AND (implants) AND (infection of the jawbone) AND (infection of the mandibular) AND (infection of the maxilla) AND (infection of the teeth) AND (jaw surgery) AND (osteonecrosis of the jaw (ONJ)) AND (other bisphosphonates) AND (other investigational drugs) AND (pathologic findings) AND (physical diseases) AND (planned) AND (present) AND (primary hyperparathyroidism) AND (prior) AND (psychological diseases) AND (renal function) AND (slow healing after dental procedures) AND (within 6 weeks) AND (zoledronic acid) AND (≥ 12.0 mg/dl))"}
{"candidate_id": "LLM00656", "doc_id": "NCT03532620_inc", "case_bucket": "or", "source_criterion": "Age 18-80 years old; IFG: 5.6mmol/L (100mg/dl)=FPG<7.0mmol/L (126mg/dl), or IGT: 7.8mmol/L (140mg/dl)=OGTT 2-h PG<11.1mmol/L (200mg/dl), or HbA1C 5.7-6.4% (39-47mmol/mol); 2.6mmol/L (100mg/dl)=LDL-C=5.2mmol/L (200mg/dl), and TG<5.7mmol/L (500mg/dl); 130mmHg=SBP<180mmHg, or 80mmHg=DBP<110mmHg or ongoing anti-hypertensive therapy; Patients volunteered for the study and signed informed consent.", "candidate_expression": "((Age 18-80 years old) AND (DBP 80mmHg= <110mmHg) AND (FPG 5.6mmol/L <7.0mmol/L 126mg/dl) AND (HbA1C 5.7-6.4% 39-47mmol/mol) AND (IFG 100mg/dl) AND (IGT 140mg/dl) AND (LDL-C 2.6mmol/L 5.2mmol/L 100mg/dl 200mg/dl) AND (OGTT 2-h PG 7.8mmol/L <11.1mmol/L 200mg/dl) AND (Patients volunteered for the study and signed informed consent.) AND (SBP 130mmHg <180mmHg) AND (TG <5.7mmol/L 500mg/dl) AND (anti-hypertensive therapy ongoing))"}
{"candidate_id": "LLM00657", "doc_id": "NCT01401335_inc", "case_bucket": "other", "source_criterion": "100 orphans/vulnerable youth aged 15 to 25 will be recruited through their participation at the day care center, on a voluntary basis.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00658", "doc_id": "NCT03017053_exc", "case_bucket": "or", "source_criterion": "Inability to provide an informed consent Evidence of oral distant metastasis or other malignancies The patient has received prior surgery for primary tumor or lymph node ( except for biopsy ) Prior radiotherapy for primary tumor The patient has previously received anti-tumor biological targeted therapy The patient has received chemotherapy or immunotherapy for primary tumors Prior malignancy within the previous 5 years (except for cured skin basal cell carcinoma or cervical carcinoma in situ) With 3-4 grad Allergy to any drug in the treatment Peripheral neuropathy> 1 grade Any unstable systematic disease (including active infection, uncontrolled high blood pressure, unstable angina, onset of angina within the last 3 months, congestive heart failure, myocardial infarction within the previous 12 months, severe arrhythmia needing drug treatment, liver, kidney or metabolic disease) HIV positive Chronic diseases requiring immune agents or hormone therapy Pregnant or lactating women Drug/alcohol abuse, psychological or spiritual illness that may interfere compliance to the study Patients with epilepsy requiring medications (such as steroids or antiepileptic drugs) The patient has participated in other experimental therapy studies within 30 days Researchers believe that the situation is unsuitable for participation in the group", "candidate_expression": "((Allergy 3-4 grad) AND (Chronic diseases) AND (Drug/alcohol abuse, psychological or spiritual illness that may interfere compliance to the study) AND (HIV positive) AND (Peripheral neuropathy > 1 grade) AND (anti-tumor biological targeted therapy previously) AND (drug) AND (drug any) AND (epilepsy) AND (malignancy Prior within the previous 5 years) AND (medications) AND (onset within the last 3 months) AND (primary tumors) AND (radiotherapy Prior) AND (surgery prior) AND (systematic disease unstable) AND (treatment) AND (tumor primary) AND (women) AND NOT (biopsy) AND ((lymph node) OR (tumor)) AND ((chemotherapy) OR (immunotherapy)) AND ((cervical carcinoma in situ) OR (cured skin basal cell carcinoma)) AND ((angina) OR (arrhythmia severe) OR (congestive heart failure) OR (high blood pressure uncontrolled) OR (infection) OR (kidney disease) OR (liver disease) OR (metabolic disease) OR (myocardial infarction within the previous 12 months) OR (unstable angina)) AND ((malignancies other) OR (metastasis oral distant)) AND ((hormone therapy) OR (immune agents)) AND ((Pregnant) OR (lactating)) AND ((antiepileptic drugs) OR (steroids)))"}
{"candidate_id": "LLM00659", "doc_id": "NCT03463564_exc", "case_bucket": "or", "source_criterion": "previous use of insulin pump pregnancy or planning to become pregnant in the next 2 years, lack of ability to use the study devices history of severe chronic diseases recent or concomitant use of corticosteroids drug or alcohol abuse psychiatric complaints that interfere with the correct use of the devices", "candidate_expression": "((ability to use the study devices) AND (chronic diseases) AND (correct use of the devices) AND (corticosteroids) AND (history) AND (in the next 2 years) AND (insulin pump) AND (interfere with) AND (lack of) AND (planning to become) AND (psychiatric complaints) AND (severe) AND (study devices) AND ((concomitant) OR (recent)) AND ((alcohol abuse) OR (drug abuse)) AND ((pregnancy) OR (pregnant)))"}
{"candidate_id": "LLM00660", "doc_id": "NCT03624881_exc", "case_bucket": "or", "source_criterion": "Previous surgical or catheter ablation for atrial fibrillation Previous cardiac surgery (including CABG) within the past 6 months (180 days) Valvular cardiac surgical/percutaneous procedure (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Any carotid stenting or endarterectomy Documented LA thrombus on imaging LA size > 50 mm (parasternal long axis view) LVEF < 40% Contraindication to anticoagulation (heparin or warfarin) History of blood clotting or bleeding abnormalities PCI/MI within the past 2 months (60 days) Documented thromboembolic event (including TIA) within the past 12 months (365 days) Rheumatic Heart Disease Uncontrolled heart failure or NYHA function class III or IV Severe mitral regurgitation (Regurgitant volume = 60 mL/beat, Regurgitant fraction = 50%, and/or Effective regurgitant orifice area = 0.40cm2) Awaiting cardiac transplantation or other cardiac surgery within the next 12 months (365 days) Unstable angina Acute illness or active systemic infection or sepsis AF secondary to electrolyte imbalance, thyroid disease, or reversible or non-cardiac cause. Presence of implanted ICD/CRT-D. Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or chronic obstructive pulmonary disease) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms. Gastroesophageal Reflux Disease (GERD; active requiring significant intervention not including OTC medication) Significant congenital anomaly or medical problem that in the opinion of the investigator would preclude enrollment in this study. Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Concurrent enrollment in an investigational study evaluating another device, biologic, or drug. Presence of intracardiac thrombus, myxoma, tumor, interatrial baffle or patch or other abnormality that precludes vascular access, or manipulation of the catheter. Life expectancy less than 12 months", "candidate_expression": "((< 40%) AND (= 0.40cm2) AND (= 50%) AND (= 60 mL/beat) AND (> 50 mm) AND (AF) AND (Acute illness) AND (CABG) AND (Concurrent enrollment in an investigational study evaluating another device, biologic, or drug.) AND (Contraindication) AND (Effective regurgitant orifice area) AND (GERD) AND (Gastroesophageal Reflux Disease) AND (History) AND (III) AND (IV) AND (LA size) AND (LA thrombus) AND (LVEF) AND (Life expectancy) AND (MI) AND (NYHA function class) AND (OTC medication) AND (PCI) AND (Previous) AND (Regurgitant fraction) AND (Regurgitant volume) AND (Rheumatic Heart Disease) AND (Severe) AND (Significant) AND (TIA) AND (Uncontrolled) AND (Unstable angina) AND (Valvular cardiac percutaneous procedure) AND (Valvular cardiac surgical procedure) AND (Women) AND (ablation surgical) AND (abnormality) AND (active) AND (anticoagulation) AND (any other) AND (atrial fibrillation) AND (atriotomy) AND (bleeding abnormalities) AND (blood clotting) AND (cardiac surgery) AND (cardiac transplantation) AND (carotid stenting) AND (catheter ablation) AND (chronic obstructive pulmonary disease) AND (chronic symptoms) AND (congenital anomaly) AND (constrictive pulmonary disease) AND (disease of the lungs) AND (disease of the respiratory system) AND (electrolyte imbalance) AND (endarterectomy) AND (heart failure) AND (heparin) AND (imaging) AND (implanted ICD/CRT-D) AND (interatrial baffle) AND (intracardiac thrombus) AND (less than 12 months) AND (malfunction of the lungs) AND (manipulation of the catheter) AND (medical problem) AND (mitral regurgitation) AND (myxoma) AND (non-cardiac cause) AND (not) AND (other) AND (parasternal long axis view) AND (patch) AND (pre-menopausal) AND (precludes) AND (pregnancy test) AND (pregnant) AND (prosthetic valve) AND (pulmonary disease) AND (restrictive pulmonary disease) AND (reversible) AND (secondary) AND (sepsis) AND (significant intervention) AND (systemic infection) AND (thromboembolic event) AND (thyroid disease) AND (tumor) AND (valve repair) AND (valve replacement) AND (vascular access) AND (ventriculotomy) AND (warfarin) AND (within the next 12 months) AND (within the next 365 days) AND (within the past 12 months) AND (within the past 2 months) AND (within the past 365 days) AND (within the past 6 months (180 days)) AND (within the past 60 days))"}
{"candidate_id": "LLM00661", "doc_id": "NCT03315975_inc", "case_bucket": "or", "source_criterion": "adults capable of providing consent have a diagnosis of locally advanced or metastatic melanoma", "candidate_expression": "((adults) AND (capable of providing consent) AND (melanoma locally advanced metastatic))"}
{"candidate_id": "LLM00662", "doc_id": "NCT02339844_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria patients: Substance abuse on a daily basis during the last 3 month or patients fulfilling the criteria of ongoing substance abuse due to ICD-10/DSM-IV/V, Treatment with antidepressant during the last 30 days, Head injury with more than 5 minutes of unconsciousness, Patients involuntarily admitted or treated, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness Exclusion criteria controls: First degree relatives with psychiatric disease, Substance abuse during the last 3 month or positive screening of drugs in urine-sample, Head injury with more than 5 minutes of unconsciousness, Components of metal implanted by operation, Pacemaker, Pregnancy, Severe physical illness", "candidate_expression": "((controls) AND (patients) AND (unconsciousness more than 5 minutes) AND ((Components of metal) OR (Head injury) OR (Pacemaker) OR (Pregnancy) OR (Severe physical illness) OR (Substance abuse daily basis during the last 3 month) OR (antidepressant during the last 30 days) OR (involuntarily admitted) OR (involuntarily treated) OR (substance abuse ongoing ICD-10/DSM-IV/V)) AND ((Components of metal) OR (Head injury) OR (Pacemaker) OR (Pregnancy) OR (Severe physical illness) OR (Substance abuse during the last 3 month) OR (psychiatric disease First degree relatives) OR (screening of drugs positive urine-sample)))"}
{"candidate_id": "LLM00663", "doc_id": "NCT02604459_exc", "case_bucket": "or", "source_criterion": "Inability to follow directions or comprehend the English language Severe uncorrected visual or auditory handicaps Delirium at screening or baseline Emergency surgery", "candidate_expression": "((Delirium) AND (Emergency surgery) AND (Severe) AND (uncorrected) AND ((Inability to comprehend the English language) OR (Inability to follow directions)) AND ((auditory handicaps) OR (handicaps visual)) AND ((at baseline) OR (at screening)))"}
{"candidate_id": "LLM00664", "doc_id": "NCT02579733_exc", "case_bucket": "or", "source_criterion": "Patients with azathioprine or biologics therapy", "candidate_expression": "((azathioprine) AND (biologics) AND (therapy))"}
{"candidate_id": "LLM00665", "doc_id": "NCT03247738_inc", "case_bucket": "other", "source_criterion": "Patients with STEMI undergoing primary PPCI Age > 18 years old", "candidate_expression": "((Age > 18 years old) AND (STEMI) AND (primary PPCI))"}
{"candidate_id": "LLM00666", "doc_id": "NCT02951520_inc", "case_bucket": "other", "source_criterion": "Adult patients scheduled for arthroscopic knee ligament reconstruction", "candidate_expression": "((Adult) AND (arthroscopic knee ligament reconstruction scheduled))"}
{"candidate_id": "LLM00667", "doc_id": "NCT02437045_inc", "case_bucket": "or", "source_criterion": "Bloodstream infection with Enterobacter spp., Serratia marcescens, Providencia spp., Morganella morganii or Citrobacter freundii (i.e. likely AmpC-producer), and susceptibility to 3rd generation cephalosporins (i.e. ceftriaxone, cefotaxime or ceftazidime), meropenem and piperacillin-tazobactam from at least one blood culture draw. This will be determined in accordance with laboratory methods and susceptibility breakpoints defined by protocols used in the recruiting site laboratories.. No more than 72 hours has elapsed since the first positive blood culture collection. Patient is aged 18 years and over (>=21y in Singapore).", "candidate_expression": "((18 years and over) AND (3rd generation cephalosporins () AND (>=21y) AND (Bloodstream infection) AND (Citrobacter freundii) AND (Enterobacter spp.) AND (Morganella morganii) AND (No more than 72 hours since the first positive blood culture collection) AND (Providencia spp.) AND (Serratia marcescens) AND (Singapore) AND (aged) AND (at least one) AND (blood culture) AND (blood culture collection) AND (cefotaxime) AND (ceftazidime) AND (ceftriaxone) AND (meropenem) AND (piperacillin-tazobactam) AND (positive) AND (the first positive blood culture collection))"}
{"candidate_id": "LLM00668", "doc_id": "NCT02985242_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes uncontrolled diabetes mellitus type 2 with fasting glucose > 13.3 mmol/l confirmed on a second day known or suspected hypersensitivity to empagliflozin, glimepiride, or any excipients; and / or known or suspected hypersensitivity to sulfonylureas, sulfonamides or SGLT2 inhibitors in general history of multiple severe hypoglycemic episodes within the last two years use of Insulin, SGLT2-inhibitor, sulfonylurea derivate or a glinide within past 3 months clinical significant macular edema in both eyes and indication for intravitreal anti-VEGF treatment for both eyes at screening or baseline visit. Eyes with a small amount of intraretinal or subretinal fluid (seen in OCT) but no need for intravitreal treatment as judged by the investigator (according to current practice patterns) may be included. Eyes with a history of intravitreal treatment of macular edema which do not need ongoing intravitreal treatment at the time of screening may be included. eye diseases or pathologies that prevent clear ophthalmoscopy and evaluation of study parameters, thus not allowing study participation according to the investigator´s judgment, such as (but not only) vitreous hemorrhage, mature cataract, macular pathologies other than diabetic maculopathy history of ketoacidosis or metabolic acidosis use of loop diuretics history of > 1 urogenital infection/year any history of stroke, transient ischemic attack (TIA), instable angina pectoris or myocardial infarction within last 3 months prior to baseline visit congestive heart failure New York Heart Association (NYHA) III and IV severe valvular or left ventricular outflow obstruction disease needing intervention; atrial fibrillation/flutter with a mean ventricular response rate at rest >100 beats per minute chronic lower urinary tract infections (but not simple asymptomatic bacteriuria) eGFR < 60 ml/min/1,73 m2 (MDRD-formula, confirmed on a second day) chronic diarrhea, any clinical signs of volume depletion or a hematocrit > 48 % (women) and > 53 % (men) elevated risk for volume depletion, e.g. history of severe volume depletion that required medical therapy chronic liver disease (including known active hepatitis) and/or screening alanine transaminase (ALT) or aspartate transaminase (AST) > 3 x upper limit of normal (ULN) (confirmed on a second day) Subjects with known seropositivity to human immunodeficiency virus. acute illness at screening or randomization according to judgement by the investigator or patient drug or alcohol abuse psychosomatic or psychiatric diseases requiring hospitalization during the last 12 months clinical evidence of current malignancy with exception of basal cell or squamous cell carcinoma of the skin, and cervical intraepithelial neoplasia (5 years prior to randomization) any medical or surgical intervention planned for the next 13 months after randomization not allowing study participation according to the investigator´s judgment current participation in any other clinical trial or participation in another clinical trial within 30 days before screening", "candidate_expression": "((ALT) AND (AST) AND (NYHA) AND (New York Heart Association III and IV) AND (TIA) AND (Type 1 diabetes) AND (active hepatitis) AND (chronic liver disease) AND (congestive heart failure) AND (current participation in any other clinical trial or participation in another clinical trial within 30 days before screening) AND (diabetes mellitus type 2 uncontrolled) AND (eGFR < 60 ml/min/1,73 m2) AND (fasting glucose > 13.3 mmol/l) AND (hospitalization last 12 months) AND (human immunodeficiency virus seropositivity) AND (hypoglycemic episodes multiple severe last two years) AND (intervention) AND (intravitreal anti-VEGF treatment both eyes) AND (loop diuretics) AND (lower urinary tract infections chronic) AND (macular edema both eyes) AND (malignancy 5 years prior to randomization) AND (mean ventricular response rate at rest >100 beats per minute) AND (men) AND (risk for volume depletion, elevated) AND (urogenital infection > 1 /year) AND (women) AND NOT (ophthalmoscopy) AND NOT (diabetic maculopathy) AND NOT (asymptomatic bacteriuria) AND ((basal cell carcinoma of the skin) OR (cervical intraepithelial neoplasia) OR (squamous cell carcinoma of the skin)) AND ((SGLT2 inhibitors) OR (sulfonamides) OR (sulfonylureas)) AND ((Insulin) OR (SGLT2-inhibitor) OR (glinide) OR (sulfonylurea derivate)) AND ((macular pathologies) OR (mature cataract) OR (vitreous hemorrhage)) AND ((ketoacidosis) OR (metabolic acidosis)) AND ((angina pectoris instable) OR (myocardial infarction) OR (stroke) OR (transient ischemic attack)) AND ((left ventricular outflow obstruction) OR (valvular disease)) AND ((hypersensitivity)) AND ((atrial fibrillation) OR (atrial flutter)) AND ((empagliflozin) OR (glimepiride)) AND ((chronic diarrhea) OR (volume depletion)) AND ((hematocrit > 48 %) OR (hematocrit > 53 %)) AND ((alanine transaminase) OR (aspartate transaminase)) AND ((alcohol abuse) OR (drug abuse)) AND ((psychiatric diseases) OR (psychosomatic diseases)))"}
{"candidate_id": "LLM00669", "doc_id": "NCT02419378_exc", "case_bucket": "or", "source_criterion": "Participation in another clinical trial at present or within 4 weeks of study entry. There may be exceptions at the discretion of the Investigator. Has any progressive form of MS Hypersensitivity to the active substance, or to any of the excipients of Lemtrada® Medical, psychiatric, cognitive, or other conditions that, in the Investigator's opinion, compromise the patient's ability to understand the patient information, to give informed consent, to comply with the trial protocol, or to complete the study Any disability acquired from trauma or another illness that could interfere with evaluation of disability due to MS Major systemic disease or other illness that would, in the opinion of the Investigator, compromise patient safety or interfere with the interpretation of study results, e.g., current peptic ulcer disease or other conditions that may predispose to hemorrhage Known bleeding disorder (e.g,. dysfibrinogenemia, factor IX deficiency, hemophilia, Von Willebrand's disease, disseminated intravascular coagulation (DIC), fibrinogen deficiency, or clotting factor deficiency) Significant autoimmune disease including but not limited to immune cytopenias, rheumatoid arthritis, systemic lupus erythematosus, other connective tissue disorders, vasculitis, inflammatory bowel disease, severe psoriasis History of malignancy, except basal skin cell carcinoma Major psychiatric disorder that is not adequately controlled by treatment Epileptic seizures that are not adequately controlled by Treatment Active infection, e.g., deep-tissue infection, that the Investigator considers sufficiently serious to preclude study participation In the Investigator's opinion, is at high risk for infection (e.g., indwelling catheter, dysphagia with aspiration, decubitus ulcer, history of prior aspiration pneumonia or recurrent urinary tract infection) Seropositivity for human immunodeficiency virus (HIV) Infection with hepatitis C Virus Past or present hepatitis B infection (positive hepatitis B serology) Active infection with human cytomegaly virus (HCMV), Epstein-Barr virus (EBV), varicella-zoster virus (VZV) Latent tuberculosis unless effective anti-tuberculosis therapy has been completed, or active tuberculosis. Invasive fungal infections in history and at present Cervical cytology other than PAP I or PAP II (Papanicolaou) or cervical high risk human papillomavirus (HPV) positivity Any other illness or infection (latent or active) that, in the Investigator's opinion, could be exacerbated by study medication Differential blood count < lower limit of normal (LLN) at Screening Confirmed platelet count < the LLN of the evaluating laboratory at Screening or documented at <100,000/µL within the past year on a sample without platelet clumping Presence (i.e., above the ULN) of anti-thyroid stimulating hormone receptor antibodies (anti-TSHR) and anti-thyroid peroxidase antibody (anti-TPO) Vaccination less than 6 weeks prior to treatment with Lemtrada. Treatment with antineoplastic or immunosuppressive drugs within 8 weeks prior to study inclusion Intolerance of pulsed corticosteroids, especially a history of steroid psychosis Inability to undergo MRI with gadolinium administration Of childbearing potential with a positive serum pregnancy test, pregnant or lactating Female patients of childbearing potential: Unwilling to agree to use a reliable and acceptable contraceptive method (Pearl index <1) throughout the study period. These methods include: hormone releasing intrauterine device (IUD), hormonal-based contraception, surgical sterilization, abstinence, or double-barrier contraception (condom and occlusive cap [diaphragm or cervical cap combined with spermicide]).", "candidate_expression": "((Any disability acquired from trauma or another illness that could interfere with evaluation of disability due to MS) AND (Cervical cytology positivity PAP I PAP II Papanicolaou) AND (DIC) AND (Differential blood count < lower limit of normal (LLN) at Screening) AND (Epileptic seizures adequately controlled) AND (Female) AND (HIV) AND (Hypersensitivity) AND (Inability to undergo MRI) AND (Infection hepatitis C Virus) AND (Intolerance) AND (Latent tuberculosis EBV varicella-zoster virus VZV) AND (Lemtrada) AND (MRI Inability to) AND (MS progressive) AND (Major systemic disease or other illness that would, in the opinion of the Investigator, compromise patient safety or interfere with the interpretation of study results, e.g., current peptic ulcer disease or other conditions that may predispose to hemorrhage) AND (Medical, psychiatric, cognitive, or other conditions that, in the Investigator's opinion, compromise the patient's ability to understand the patient information, to give informed consent, to comply with the trial protocol, or to complete the study) AND (Participation) AND (Treatment) AND (Unwilling to agree to use a reliable and acceptable contraceptive method (Pearl index <1) throughout the study period. These methods include: hormone releasing intrauterine device (IUD), hormonal-based contraception, surgical sterilization, abstinence, or double-barrier contraception (condom and occlusive cap [diaphragm or cervical cap combined with spermicide])) AND (Vaccination less than 6 weeks prior to treatment with Lemtrada) AND (Von Willebrand's disease) AND (above the ULN) AND (active tuberculosis) AND (anti-thyroid peroxidase antibody (anti-TPO)) AND (anti-thyroid stimulating hormone receptor antibodies (anti-TSHR)) AND (anti-tuberculosis therapy completed) AND (antineoplastic drugs within 8 weeks prior to study inclusion) AND (articipation in another clinical trial at present or within 4 weeks of study entry. There may be exceptions at the discretion of the Investigator) AND (aspiration) AND (aspiration pneumonia) AND (autoimmune disease) AND (bleeding disorder) AND (childbearing potential) AND (clotting factor deficiency) AND (connective tissue disorders) AND (decubitus ulcer) AND (deep-tissue infection) AND (disseminated intravascular coagulation) AND (dysfibrinogenemia) AND (dysphagia) AND (factor IX deficiency) AND (fibrinogen deficiency) AND (fungal infections Invasive) AND (gadolinium) AND (hemophilia) AND (hepatitis B infection) AND (hepatitis B serology positive) AND (human immunodeficiency virus Seropositivity) AND (illness human papillomavirus HPV) AND (immune cytopenias,) AND (immunosuppressive drugs) AND (indwelling catheter) AND (infection Active) AND (infection Active human cytomegaly virus HCMV Epstein-Barr virus) AND (infection latent active active) AND (inflammatory bowel disease) AND (lactating) AND (malignancy) AND (platelet count Confirmed sample without platelet clumping < the LLN of the evaluating laboratory <100,000/µL) AND (pregnant) AND (psoriasis severe) AND (psychiatric disorder Major adequately controlled) AND (pulsed corticosteroids) AND (rheumatoid arthritis,) AND (risk for infection high) AND (serum pregnancy test positive) AND (steroid psychosis history of) AND (study medication) AND (systemic lupus erythematosus) AND (treatment) AND (urinary tract infection recurrent) AND (vasculitis) AND NOT (basal skin cell carcinoma))"}
{"candidate_id": "LLM00670", "doc_id": "NCT00425789_inc", "case_bucket": "other", "source_criterion": "The study will include 40 post-deep peel women (exoderm), older than 18 years old, treated by the same dermatologist (dr. Landau). The treatment group will receive 5 consecutive daily hyperbaric treatments, 1 hours long each, at 2 ATF, starting from day 7 to peel. Prior to treatment, each patient will be signed on informed consent and will have complete physical examination. The control group will be matched by the following parameters: age, skin color and type, and indication for peeling, and will be picked up by the dermatologist.", "candidate_expression": "((age) AND (deep peel) AND (exoderm) AND (old older than 18 years) AND (skin color) AND (type) AND (women))"}
{"candidate_id": "LLM00671", "doc_id": "NCT03193684_inc", "case_bucket": "other", "source_criterion": "eGFR>60 ml/min healthy volunteers type 2 diabetes patients who otherwise healthy", "candidate_expression": "((eGFR >60 ml/min) AND (healthy) AND (type 2 diabetes))"}
{"candidate_id": "LLM00672", "doc_id": "NCT03297021_exc", "case_bucket": "or", "source_criterion": "Patients with allergies or contraindications to study medications", "candidate_expression": "((study medications) AND ((allergies) OR (contraindications)))"}
{"candidate_id": "LLM00673", "doc_id": "NCT02974686_exc", "case_bucket": "or", "source_criterion": "Dual organ or kidney after another solid organ transplant Presence of a preexisting significant GI condition that does not have a presumed causal relationship with MPA Evidence of any GI disorder induced by an infection, underlying medical condition, or concomitant medication other than MPA eGFR<40 ml/min at time of possible conversion Proteinuria >1 gram/day at time of possible conversion Hemoglobin <10 g/dL WBC <3 K/cumm Platelets <100 K/cumm Wound healing issues at time of possible conversion (eg, wound dehiscence, wound infection, incisional hernia, lymphocele, seroma) Elevated total cholesterol (>350 mg/dL) and/or triglycerides (>500 ng/dL) at time of possible conversion Hypersensitivity to everolimus, sirolimus, or other rapamycin deriviatives", "candidate_expression": "((<10 g/dL) AND (<100 K/cumm) AND (<3 K/cumm) AND (<40 ml/min) AND (>1 gram/day) AND (>350 mg/dL) AND (>500 ng/dL) AND (Dual kidney) AND (Dual organ) AND (Elevated) AND (GI condition) AND (GI disorder) AND (Hemoglobin) AND (Hypersensitivity) AND (MPA) AND (Platelets) AND (Proteinuria) AND (WBC) AND (Wound healing issues) AND (at time of possible conversion) AND (eGFR) AND (everolimus) AND (incisional hernia) AND (induced by an infection) AND (infection) AND (lymphocele) AND (medication) AND (other than) AND (preexisting) AND (rapamycin) AND (seroma) AND (significant) AND (sirolimus) AND (solid organ transplant) AND (total cholesterol) AND (triglycerides) AND (underlying medical condition) AND (wound dehiscence) AND (wound infection))"}
{"candidate_id": "LLM00674", "doc_id": "NCT02933671_inc", "case_bucket": "other", "source_criterion": "English speaking between 18 and 75 years old American Society of Anesthesiologists (ASA) 1-3 patients undergoing primary total hip arthroplasty", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists 1-3) AND (old between 18 and 75 years) AND (primary total hip arthroplasty))"}
{"candidate_id": "LLM00675", "doc_id": "NCT02571881_exc", "case_bucket": "or", "source_criterion": "age less than 18 years allergy to study drugs substance misuse other contraindication to used study drugs no informed consent", "candidate_expression": "((age) AND (allergy) AND (less than 18 years) AND (study drugs) AND ((contraindication) OR (substance misuse)))"}
```
