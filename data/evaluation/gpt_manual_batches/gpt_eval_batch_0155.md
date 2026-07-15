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
{"candidate_id": "LLM03851", "doc_id": "NCT02818816_exc", "case_bucket": "or", "source_criterion": "Patients having had an ophthalmic surgical procedure within 6 months of the beginning of the study. Patients with a diagnosis of glaucoma Any abnormality of the cornea which may prevent reliable applanation tonometry Known allergy/ hypersensitivity reaction to Brimonidine Contra-indication to Brimonidine including patients on monoamine oxidase inhibitors (MOA) Patients unwilling or unable to provide informed consent Patients with anticipated difficult airway management (as this may require medications and/or airway manipulations resulting in increased IOP)", "candidate_expression": "((Brimonidine) AND (Contra-indication) AND (MOA) AND (Patients unwilling or unable to provide informed consen) AND (abnormality) AND (allergy) AND (cornea) AND (difficult airway management) AND (glaucoma) AND (hypersensitivity) AND (monoamine oxidase inhibitors) AND (ophthalmic surgical procedure) AND (study) AND (within 6 months of the beginning of the study))"}
{"candidate_id": "LLM03852", "doc_id": "NCT02621489_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes (autoantibody positive). Any history of receiving GLP-1 analogues or dipeptidyl peptidase inhibitors within 6 months Known severe heart failure, classified as NYHA 4. Active myocarditis; malfunctioning artificial heart valve. History of ventricular tachycardia within 3 months before study entry; second- or third-degree atrioventricular block. Supine systolic blood pressure <85 mm Hg or >200 mm Hg at screening. Primary renal impairment, creatinine clearance < 45 ml/min if treated with metformin. Uncorrected hypokalemia or hyperkalemia (potassium <3.5 mmol/l or >5.5 mmol/l). Significant anemia (Hb < 90 g/l) Severe gastrointestinal disease, including gastroparesis. As judged by the Investigator. Body mass index (BMI) > 45 kg/m2. Malignant neoplasm requiring chemotherapy, surgery, radiation or palliative therapy in the previous 5 years. Patients with intraepithelial squamous cell carcinoma of the skin treated with topical 5FU and subjects with basal cell skin cancer are allowed to enter the trial. Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant. Current drug and alcohol abuse. History of acute or chronic pancreatitis Subjects considered by the Investigator to be unsuitable for the study.", "candidate_expression": "((Active myocarditis) AND (BMI) AND (Body mass index > 45 kg/m2) AND (Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant) AND (GLP-1 analogues) AND (Hb < 90 g/l) AND (Malignant neoplasm previous 5 years.) AND (NYHA 4) AND (Primary renal impairment) AND (Type 1 diabetes) AND (acute pancreatitis) AND (alcohol abuse) AND (anemia Significant) AND (artificial heart valve malfunctioning) AND (autoantibody positive) AND (basal cell skin cancer) AND (chemotherapy) AND (chronic pancreatitis) AND (creatinine clearance < 45 ml/min) AND (dipeptidyl peptidase inhibitors) AND (drug abuse) AND (gastrointestinal disease Severe) AND (gastroparesis) AND (heart failure severe) AND (hyperkalemia) AND (hypokalemia) AND (intraepithelial squamous cell carcinoma skin) AND (metformin) AND (palliative therapy) AND (potassium <3.5 mmol/l >5.5 mmol/l) AND (radiation) AND (second- degree atrioventricular block) AND (surgery) AND (systolic blood pressure Supine <85 mm Hg >200 mm Hg) AND (third-degree atrioventricular block) AND (topical 5FU) AND (ventricular tachycardia within 3 months))"}
{"candidate_id": "LLM03853", "doc_id": "NCT03351972_exc", "case_bucket": "other", "source_criterion": "dysphagia severe gastroparesis requiring endoscopic placement of capsule small bowel obstruction pregnancy", "candidate_expression": "((capsule) AND (dysphagia) AND (endoscopic placement requiring) AND (gastroparesis severe) AND (pregnancy) AND (small bowel obstruction))"}
{"candidate_id": "LLM03854", "doc_id": "NCT02152696_inc", "case_bucket": "or", "source_criterion": "Female with a persisting pregnancy of unknown location: A pregnancy of unknown location is defined as a pregnancy in a woman with a positive pregnancy test but no definitive signs of pregnancy in the uterus or adnexa on ultrasound imaging. A definitive sign of gestation includes ultrasound visualization of a gestational sac with a yolk sac (with or without an embryo) in the uterus or in the adnexa. Ultrasound must be performed within 7 days prior to randomization. Persistence of hCG is defined as at least 2 serial hCG values (over 2-14 days), showing < 15% rise per day, or < 50% fall between the first and last value. Patient is hemodynamically stable, hemoglobin >10 mg/dL Greater than or 18 years of age", "candidate_expression": "((< 15% rise per day) AND (< 50% fall between the first and last value.) AND (>10 mg/dL) AND (Female) AND (Greater than or 18 years) AND (Persistence of hCG) AND (Ultrasound) AND (age) AND (at least 2) AND (hCG) AND (hemodynamically stable) AND (hemoglobin) AND (over 2-14 days) AND (positive) AND (pregnancy) AND (pregnancy test) AND (randomization) AND (unknown location) AND (within 7 days prior to randomization) AND (woman))"}
{"candidate_id": "LLM03855", "doc_id": "NCT02344888_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulatory PCOS. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Oral hypoglycemic or hormonal therapy either currently or in the preceding 3 months. Metabolic or hormonal abnormalities", "candidate_expression": "((< 18.5 kg/m2 or > 25 kg/m2) AND (< 20 or > 35 years) AND (Age) AND (BMI) AND (Body mass index) AND (Metabolic abnormalities) AND (Oral) AND (anovulatory PCOS) AND (cytotoxic drugs) AND (exposure) AND (hormonal abnormalities) AND (hormonal therapy) AND (hypoglycemic therapy) AND (infertility factor) AND (one) AND (other than) AND (ovarian surgery) AND (ovary) AND (pelvic irradiation) AND (preceding 3 months) AND (surgical removal))"}
{"candidate_id": "LLM03856", "doc_id": "NCT02595190_exc", "case_bucket": "or", "source_criterion": "1. Patients with lumbar common diseases(e.g., Lumbar disc, Lumbar spinal stenosis, Lumbar slippage, etc) 2. Researchers think that Patients with disease may be interference results(e.g., Spinal deformity, spine fracture, ankylosing spondylitis, spinal tuberculosis and spinal infection, spinal tumor, pelvic inflammatory disease and other disease of department of gynaecology, etc) 3. Patients with other nervous system diseases(e.g., cerebral tumor, neurinoma, trigeminal neuralgia,etc) 4. Patients with Magnetic resonance imaging contraindication ,including claustrophobic syndrome patients 5. Patients with recent (less than 3 years) use chemical drugs or have obvious psychological problems 6. In the past 2 months involved in other drugs or devices clinical trials", "candidate_expression": "((In the past 2 months involved in other drugs or devices clinical trials) AND (Magnetic resonance imaging) AND (claustrophobic syndrome) AND (contraindication) AND (lumbar diseases) AND (nervous system diseases) AND ((cerebral tumor) OR (neurinoma) OR (trigeminal neuralgia)) AND ((Lumbar disc) OR (Lumbar slippage) OR (Lumbar spinal stenosis)) AND ((Spinal deformity) OR (ankylosing spondylitis) OR (pelvic inflammatory disease) OR (spinal infection) OR (spinal tuberculosis) OR (spinal tumor) OR (spine fracture,)))"}
{"candidate_id": "LLM03857", "doc_id": "NCT03034733_exc", "case_bucket": "or", "source_criterion": "severe coronary artery disease, heart failure, kidney failure insulin-dependent DM (diabetes mellitus), poorly controlled type II DM gastric/duodenal ulcer allergy/contra-indication for any drug used in the study corticosteroid use during last 3 months preoperative use of opioid drugs (excl. codeine, tramadol) neuropathy/sensory impairment of lower limbs lack of co-operation, e.g. inability to use a PCA (patient controlled analgesia)-device", "candidate_expression": "((PCA -device) AND (allergy) AND (codeine) AND (contra-indication) AND (coronary artery disease) AND (corticosteroid) AND (diabetes mellitus) AND (drug used in the study) AND (duodenal ulcer) AND (during last 3 months) AND (excl.) AND (gastric ulcer) AND (heart failure) AND (inability to use) AND (insulin-dependent DM) AND (kidney failure) AND (lack of co-operation) AND (lower limbs) AND (neuropathy) AND (opioid drugs) AND (poorly controlled) AND (preoperative) AND (sensory impairment) AND (severe) AND (tramadol) AND (type II DM))"}
{"candidate_id": "LLM03858", "doc_id": "NCT02257580_exc", "case_bucket": "or", "source_criterion": "Preoperative use of an anticoagulant (Plavix, warfarin, lovenox, etc.) History of hypersensitivity to EACA History of thromboembolic event (e.g., PE or DVT) History of renal insufficiency or failure Congenital or acquired coagulopathy as evidence by INR >1.4 or PTT > 1.4 times normal, or Platelets <150,000/mm3 on preoperative laboratory testing Use of hormone replacement therapy or hormonal contraceptive agents within days prior to surgery Use of acetylsalicylic acid (ASA), antiplatelet agents within 7 days prior to surgery Pregnant Breastfeeding Not received neuraxial anesthesia", "candidate_expression": "((ASA) AND (Breastfeeding) AND (DVT) AND (EACA) AND (INR >1.4 times normal) AND (PE) AND (PTT > 1.4 times normal) AND (Platelets <150,000/mm3) AND (Plavix) AND (Pregnant) AND (acetylsalicylic acid) AND (anticoagulant Preoperative) AND (antiplatelet agents) AND (coagulopathy) AND (hormonal contraceptive agents) AND (hormone replacement therapy) AND (hypersensitivity) AND (lovenox) AND (preoperative laboratory testing) AND (renal failure Congenital acquired) AND (renal insufficiency) AND (thromboembolic event) AND (warfarin) AND NOT (neuraxial anesthesia))"}
{"candidate_id": "LLM03859", "doc_id": "NCT03481894_inc", "case_bucket": "or", "source_criterion": "Male or female patients 2 to 16 years of age Patients who require at least 80% of their caloric intake as PN at study start, and in whom an indication for PN is expected for at least 5 days Patients who require a central venous line to receive PN or already have a central venous line in place for other reasons Written informed consent from legal representative(s)", "candidate_expression": "((Male) AND (PN) AND (PN at least 80% of caloric intake at study start) AND (Written informed consent from legal representative(s)) AND (age 2 to 16 years) AND (central venous line) AND (central venous line other reasons) AND (female) AND (indication for at least 5 days))"}
{"candidate_id": "LLM03860", "doc_id": "NCT02601157_inc", "case_bucket": "other", "source_criterion": "Patients with de novo stenotic lesions who are suitable for coronary stenting with drug-eluting stent", "candidate_expression": "((coronary stenting) AND (de novo) AND (drug-eluting stent) AND (stenotic lesions) AND (suitable))"}
{"candidate_id": "LLM03861", "doc_id": "NCT02267616_exc", "case_bucket": "other", "source_criterion": "Have history of female sterilization procedure Desire for conception in the next 12 months Not sexually active with a male partner", "candidate_expression": "((conception Desire in the next 12 months) AND (female sterilization procedure) AND NOT (sexually active male partner))"}
{"candidate_id": "LLM03862", "doc_id": "NCT02985242_inc", "case_bucket": "or", "source_criterion": "women and men between 18 - 80 years of age type 2 diabetes mellitus early to moderate stage diabetic retinopathy (ETDRS: 20 (microaneurysms only) to 35 (microaneurysms/ hemorrhages and/or hard exsudates)) in one or both eyes stable HbA1c (± 0.5%) for at least 12 weeks antidiabetic treatment with either diet, metformin, DPP4, GLP1, pioglitazone, acarbose, or respective combinations HbA1c = 6.5 and = 10.0 % body mass index < 46 kg/m2 office blood pressure = 150/95 mmHg (confirmed on a second day; 24h ambulatory blood pressure measurement (ABPM) is allowed to check accuracy of office values; inclusion with 24h mean blood pressure = 145/90 mm Hg is possible); patients with hypertension should be treated according to current treatment guidelines at least 6 weeks after surgical sterilization by bilateral tubal ligation or bilateral oophorectomy hysterectomy = 50 years and in postmenopausal state > 1 year < 50 years and in postmenopausal state > 1 year with serum follicle stimulating hormone (FSH) > 40 IU/l and serum estrogen < 30 ng/l or a negative estrogen test, both at screening or women of childbearing potential with a negative serum beta human chorionic gonadotropin (ß-hCG) pregnancy test at screening who agree to meet one of the following criteria from the time of screening, during the study and for a period of 4 days following the last administration of study medication: correct use of one of the following accepted contraception methods: hormonal contraceptives (combined oral contraceptives, implants, transdermal patches, hormonal vaginal devices or injections with prolonged release), intrauterine device (IUD/IUS) or a double barrier method, e.g. condom and occlusive cap (diaphragm or cervical/vault caps) with spermicide (foam, gel, film, cream or suppository) true abstinence (periodic abstinence and withdrawal are not acceptable methods of contraception) sexual relationship only with female partners sterile male partners signed written informed consent and willingness to comply with treatment and follow-up procedures capability of understanding the investigational nature, potential risks and benefits of the clinical trial", "candidate_expression": "((< 50 years and in postmenopausal state > 1 year with serum follicle stimulating hormone (FSH) > 40 IU/l and serum estrogen < 30 ng/l or a negative estrogen test, both at screening or women of childbearing potential with a negative serum beta human chorionic gonadotropin (ß-hCG) pregnancy test at screening who agree to meet one of the following criteria from the time of screening, during the study and for a period of 4 days following the last administration of study medication) AND (ETDRS) AND (HbA1c = 6.5 and = 10.0 %) AND (HbA1c ± 0.5% eyes) AND (age between 18 - 80 years) AND (antidiabetic treatment) AND (blood pressure = 150/95 mmHg) AND (body mass index < 46 kg/m2) AND (capability of understanding the investigational nature, potential risks and benefits of the clinical trial) AND (correct use of one of the following accepted contraception methods: hormonal contraceptives (combined oral contraceptives, implants, transdermal patches, hormonal vaginal devices or injections with prolonged release), intrauterine device (IUD/IUS) or a double barrier method, e.g. condom and occlusive cap (diaphragm or cervical/vault caps) with spermicide (foam, gel, film, cream or suppository)) AND (diabetic retinopathy) AND (hysterectomy) AND (postmenopausal state > 1 year) AND (signed written informed consent and willingness to comply with treatment and follow-up procedures) AND (surgical sterilization) AND (true abstinence (periodic abstinence and withdrawal are not acceptable methods of contraception)) AND (type 2 diabetes mellitus) AND (years = 50) AND ((20) OR (35)) AND ((men) OR (women)) AND ((DPP4) OR (GLP1) OR (acarbose) OR (diet) OR (metformin) OR (pioglitazone)) AND ((bilateral oophorectomy) OR (bilateral tubal ligation)) AND ((early) OR (moderate stage)))"}
{"candidate_id": "LLM03863", "doc_id": "NCT02429765_exc", "case_bucket": "other", "source_criterion": "A diagnosis of sleep disordered breathing; Nocturnal oxygen therapy.", "candidate_expression": "((Nocturnal oxygen therapy) AND (sleep disordered breathing))"}
{"candidate_id": "LLM03864", "doc_id": "NCT02952378_exc", "case_bucket": "or", "source_criterion": "Heart failure Signs of kidney injury/failure Severe allergies", "candidate_expression": "((Heart failure) AND (Severe) AND (Signs of) AND (allergies) AND (kidney failure) AND (kidney injury))"}
{"candidate_id": "LLM03865", "doc_id": "NCT02251249_exc", "case_bucket": "or", "source_criterion": "Allergy or contraindication to paracetamol, Prasugrel or Ticagrelor Paracetamol ingestion in the previous 48 hours Patient treated with drugs supposed to alter gastric emptying times (calcium antagonists, Alimentary tract treatments, opioid analgesics, tricyclic antidepressants, antibiotics). Conditions or pathologies supposed to alter gastric emptying times (Thyroid dysfunction, chronic renal failure, Parkinson's disease, scleroderma, amyloidosis, any gastrointestinal disease, any not cured malignancy, and any advanced psychiatric or neurological disease). Presence of vomiting Cardiogenic shock, ventricular arrhythmia or resuscitated cardiac arrest Hepatic insufficiency Severe respiratory disease Pregnant or breastfeeding women", "candidate_expression": "((Alimentary tract treatments) AND (Allergy) AND (Cardiogenic shock) AND (Conditions supposed to alter gastric emptying times) AND (Hepatic insufficiency) AND (Paracetamol) AND (Parkinson's disease) AND (Prasugrel) AND (Pregnant) AND (Severe) AND (Thyroid dysfunction) AND (Ticagrelor) AND (advanced) AND (amyloidosis) AND (antibiotics) AND (breastfeeding) AND (calcium antagonists) AND (cardiac arrest) AND (chronic renal failure) AND (contraindication) AND (drugs supposed to alter gastric emptying times) AND (gastrointestinal disease) AND (in the previous 48 hours) AND (malignancy) AND (neurological disease) AND (opioid analgesics) AND (paracetamol) AND (pathologies supposed to alter gastric emptying times) AND (psychiatric disease) AND (respiratory disease) AND (resuscitated) AND (scleroderma) AND (tricyclic antidepressants) AND (ventricular arrhythmia) AND (vomiting) AND (women))"}
{"candidate_id": "LLM03866", "doc_id": "NCT02644629_inc", "case_bucket": "other", "source_criterion": "Age 18-65 Diagnosis of MDD (Major Depressive Disorder), made or affirmed by a senior psychiatrist in Shalvata MADRS score > 20 Treated with conventional anti-depressant, administered within a formal psychiatric clinic or by a certified psychiatrist.", "candidate_expression": "((Age 18-65) AND (MADRS score > 20) AND (MDD) AND (Major Depressive Disorder) AND (Treated) AND (conventional anti-depressant))"}
{"candidate_id": "LLM03867", "doc_id": "NCT02427295_inc", "case_bucket": "other", "source_criterion": "Age 18 or older. Patients diagnosed with acromegaly with GH-secreting pituitary adenoma on sellar MRI, meeting the biochemical criteria outlined above (refer to 1. Diagnosis of acromegaly) and with typical acromegalic features. No prior use of somatostatin analogues. Adequate hepatic and renal function Provision of a signed written informed consent", "candidate_expression": "((Adequate hepatic function) AND (Adequate renal function) AND (Age 18 or older) AND (GH-secreting pituitary adenoma) AND (Provision of a signed written informed consent) AND (acromegalic features typical) AND (acromegaly biochemical criteria outlined above) AND (sellar MRI) AND NOT (somatostatin analogues prior))"}
{"candidate_id": "LLM03868", "doc_id": "NCT02951520_inc", "case_bucket": "other", "source_criterion": "Adult patients scheduled for arthroscopic knee ligament reconstruction", "candidate_expression": "((Adult) AND (arthroscopic knee ligament reconstruction) AND (scheduled))"}
{"candidate_id": "LLM03869", "doc_id": "NCT02600000_inc", "case_bucket": "scope", "source_criterion": "Diagnosis of Heart Failure; Lower left ventricular ejection fraction 45% (LVEF <45%) assessed by simple and recent echocardiogram; Functional Class II and III by the New York Heart Association (NYHA) Clinically stable; Ex-smokers over five years; Maximal inspiratory pressure (MIP) <70% of predicted; Forced expiratory volume/Forced vital capacity (FEV1 / FVC) > 70% of predicted;", "candidate_expression": "((Clinically stable) AND (Ex-smokers over five years) AND (Forced expiratory volume/Forced vital capacity (FEV1 / FVC) > 70% of predicted) AND (Heart Failure) AND (LVEF <45%) AND (Lower left ventricular ejection fraction 45%) AND (Maximal inspiratory pressure (MIP) <70% of predicted) AND (New York Heart Association (NYHA) Class II and III) AND (echocardiogram recent))"}
{"candidate_id": "LLM03870", "doc_id": "NCT02609698_inc", "case_bucket": "other", "source_criterion": "Patients aged 19 or older Patients who have submitted a written consent to participate in the clinical trial De novo lesion Patients scheduled for elective intervention to treat ischemic cardiovascular disease", "candidate_expression": "((19 or older) AND (De novo lesion) AND (Patients scheduled for elective intervention to treat ischemic cardiovascular disease) AND (Patients who have submitted a written consent to participate in the clinical trial) AND (aged))"}
{"candidate_id": "LLM03871", "doc_id": "NCT02851888_inc", "case_bucket": "scope", "source_criterion": "Scheduled for arthroscopic labral repair with or without osteoplasty of the hip. 18 to 50 years old American Society of Anesthesiologists Physical Status (ASA PS) score of I or II.", "candidate_expression": "((18 to 50 years) AND (ASA PS) AND (American Society of Anesthesiologists Physical Status score) AND (I or II) AND (Scheduled) AND (arthroscopic labral repair) AND (hip) AND (old) AND (osteoplasty))"}
{"candidate_id": "LLM03872", "doc_id": "NCT01117181_inc", "case_bucket": "or", "source_criterion": "Possible or probable Alzheimer's disease (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria), with Mini-Mental State Exam (MMSE) score of 10-26 inclusive; MMSE scores above 26 in those who nevertheless meet criteria for AD may be allowed with Steering Committee approval on a case by case basis Clinically significant apathy for at least four weeks for which either 1) the frequency of apathy as assessed by the Neuropsychiatric Inventory (NPI) is 'Very frequently', or 2) the frequency of apathy as assessed by the NPI is 'Frequently' or 'Often' AND the severity of apathy as assessed by the NPI is 'Moderate' or 'Marked' A medication for apathy is appropriate, in the opinion of the study physician Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments No change to AD medications within the month preceding randomization, including starting, stopping, or dosage modifications Treatment with stable doses of selective serotonin reuptake inhibitor antidepressants(SSRIs) is appropriate if stable for 3 months prior to randomization. Other psychotropics(with the exclusion of antipsychotics), if stable for 3 months, may be allowed only with Steering Committee approval on a case by case basis.", "candidate_expression": "((A medication for apathy is appropriate, in the opinion of the study physician) AND (AD) AND (AD medications) AND (Alzheimer's disease) AND (Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study) AND (Frequently) AND (MMSE) AND (Marked) AND (Mini-Mental State Exam (MMSE)) AND (Moderate) AND (NPI) AND (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria) AND (Neuropsychiatric Inventory (NPI)) AND (No) AND (Often) AND (Possible) AND (Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver) AND (Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments) AND (Treatment) AND (Very frequently) AND (apathy) AND (at least four weeks) AND (change to AD medications) AND (frequency of apathy) AND (medication for apathy) AND (probable) AND (randomization) AND (score of 10-26 inclusive) AND (scores above 26) AND (selective serotonin reuptake inhibitor antidepressants(SSRIs)) AND (severity of apathy) AND (stable doses) AND (within the month preceding randomization))"}
{"candidate_id": "LLM03873", "doc_id": "NCT02360631_exc", "case_bucket": "or", "source_criterion": "Renal impairment Evidence or history of clinically significant allergic reactions to varenicline A cardiovascular event in the past month History of alcohol or drug dependence in the past year Major depressive disorder in the last year requiring treatment History of panic disorder, psychosis, bipolar disorder, or eating disorders Use of tobacco products other than cigarettes in past 30 days Use of pharmacotherapy in the month prior to enrollment, including prior use of varenicline Pregnant, contemplating getting pregnant, or breastfeeding Plans to move from Kansas City during the treatment and follow-up phase Another household member enrolled in the study Evidence of current severe major depressive disorder or suicidal ideation", "candidate_expression": "((Major depressive disorder) AND (Pregnant, contemplating getting pregnant, or breastfeeding) AND (Renal impairment) AND (Use of tobacco) AND (alcohol dependence) AND (allergic) AND (bipolar disorder) AND (cardiovascular event) AND (cigarettes) AND (drug dependence) AND (eating disorders) AND (enrollment) AND (in the past month) AND (last year) AND (major depressive disorder) AND (month prior to enrollment) AND (other than) AND (panic disorder) AND (past 30 days) AND (pharmacotherapy) AND (psychosis) AND (severe) AND (suicidal ideation) AND (the past year) AND (treatment) AND (varenicline))"}
{"candidate_id": "LLM03874", "doc_id": "NCT03091881_exc", "case_bucket": "or", "source_criterion": "Contraindications for spinal anesthesia (like bleeding diathesis or regional infection at site of neuroaxial block) Known allergy to Granisetron or local anaesthetic (heavy bupivacaine, Marcaine Spinal 0.5% Heavy, 5mg/ml, AstraZeneca ampule) Pregnancy induced hypertension Congenital or rheumatic heart diseases Antepartum haemorrhage Fetal destress or gestational age < 36 week", "candidate_expression": "((Antepartum haemorrhage) AND (Contraindications) AND (Fetal destress) AND (Granisetron) AND (Marcaine Spinal 0.5% Heavy 5mg/ml AstraZeneca ampule) AND (Pregnancy) AND (allergy) AND (bleeding diathesis) AND (gestational age < 36 week) AND (heart diseases) AND (heavy bupivacaine) AND (hypertension Pregnancy induced Congenital rheumatic) AND (local anaesthetic) AND (regional infection) AND (spinal anesthesia))"}
{"candidate_id": "LLM03875", "doc_id": "NCT02888704_exc", "case_bucket": "or", "source_criterion": "Subjects who have systemic infection Subjects who have human Immunodeficiency virus (HIV), hepatitis B virus (HBV), and hepatitis C virus (HCV) Subjects who need to take the medicine which is prohibited during this study Subjects who have asthma Subjects who can not stop treatment with topical steroids (group 1~5), oral antibiotics, whole body photochemotherapy, immunosuppressive drug within 4 weeks before the treatment visit Pregnant, breast-feeding women or women who plan to become pregnant during this study (Females of childbearing potential must have a negative urine pregnancy test) Subjects who currently participate in other clinical trial or participated in other clinical trial within 30 days Subjects who had a serious adverse events during stem cell therapy Subjects who had a hypersensitivity to antibiotics or antimycotics Subjects who creatinine value is more than two times of the upper limit of the normal range at screening test Subjects who aspartate transaminase/alkaline transaminase (AST/ALT) value is more than three times of the upper limit of the normal range at screening test Subjects who have any other condition which the investigator judges would make patients unsuitable for study participation", "candidate_expression": "((Pregnant) AND (any other condition the investigator judges would make patients unsuitable for study participation) AND (aspartate transaminase/alkaline transaminase (AST/ALT) more than three times of the upper limit of the normal range at screening test) AND (asthma) AND (breast-feeding) AND (childbearing potential) AND (creatinine more than two times of the upper limit of the normal range at screening test) AND (hypersensitivity) AND (pregnant) AND (serious adverse events during) AND (stem cell therapy) AND (systemic infection) AND (the investigator judges would make patients unsuitable for study participation) AND (urine pregnancy test negative) AND ((immunosuppressive drug) OR (oral antibiotics) OR (topical steroids) OR (whole body photochemotherapy)) AND ((Females) OR (women)) AND ((hepatitis B virus (HBV)) OR (hepatitis C virus (HCV)) OR (human Immunodeficiency virus (HIV))) AND ((antibiotics) OR (antimycotics)))"}
```
