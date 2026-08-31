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
{"candidate_id": "LLM07651", "doc_id": "NCT02982577_inc", "case_bucket": "other", "source_criterion": "Age equal or superior to 18 years; Both genders; Lucid and without diagnosis of any psychiatric disorder; Diagnosed with head and neck cancer and treated for a period of up to 5 years with radiotherapy where the major salivary glands (parotid, submandibular and sublingual) were included in the radiation field; Primary Sjögren's syndrome with the diagnosis made by the American-European criteria.", "candidate_expression": "((5 years) AND (Age) AND (American-European criteria) AND (Lucid) AND (Primary Sjögren's syndrome) AND (equal or superior to 18 years) AND (genders) AND (head and neck cancer) AND (major salivary glands) AND (parotid) AND (psychiatric disorder) AND (radiotherapy) AND (sublingual) AND (submandibular) AND (without))"}
{"candidate_id": "LLM07652", "doc_id": "NCT01980680_exc", "case_bucket": "other", "source_criterion": "Patients with >14 follicles on day of trigger Previous hyperresponse with OHSS development Previous low response (less than 3 oocytes on a high dose of FSH stimulation) Endocrine disorders", "candidate_expression": "((Endocrine disorders) AND (follicles >14 on day of trigger) AND (high dose of FSH stimulation) AND (hyperresponse Previous OHSS development) AND (low response Previous) AND (oocytes less than 3))"}
{"candidate_id": "LLM07653", "doc_id": "NCT01098383_exc", "case_bucket": "or", "source_criterion": "an underlying infectious disease chromosomal abnormality metabolic disorder specific brain related disorder (such as tuberous sclerosis) history of fetal cytomegalovirus infection birth asphyxia a history of major head injury a chronic use of non-steroidal anti-inflammatory drugs, (NSAID) known brain damage Epilepsy Abnormal Electro-cardiogram (ECG) Epileptiform EEG Use of psychostimulants, anti-depressants, neuroleptics or anti-convulsive agents within the past month. Lack of cooperation in the screening phase", "candidate_expression": "((ECG) AND (EEG Epileptiform) AND (Electro-cardiogram Abnormal) AND (Epilepsy) AND (Lack of cooperation in the screening phase) AND (NSAID) AND (birth asphyxia) AND (brain damage) AND (chromosomal abnormality) AND (chronic use) AND (cytomegalovirus infection fetal) AND (disorder brain) AND (infectious disease underlying) AND (major head injury) AND (metabolic disorder) AND (non-steroidal anti-inflammatory drugs) AND (tuberous sclerosis) AND ((anti-convulsive agents) OR (anti-depressants) OR (neuroleptics) OR (psychostimulants)))"}
{"candidate_id": "LLM07654", "doc_id": "NCT02426944_exc", "case_bucket": "or", "source_criterion": "thrombus in the LA or LAA; mechanical valve prosthesis; mitral stenosis; previous LAA ligation during cardiac surgery; life expectancy less than 2 years; comorbidities other than AF, which present an indication for anticoagulation; patent foramen ovale with atrial septal aneurysm mobile plaque in the aorta; symptomatic atherosclerosis of the carotid artery; pericardial effusion greater than 10 mm; clinically significant bleeding within the 30 days prior to the scheduled procedure; stroke or other cardioembolic event within the 30 days prior to the scheduled procedure; acute coronary syndrome within the 90 days prior to the scheduled procedure, gravidity, significant valvular disease, creatinine clearance less than 30 ml/min", "candidate_expression": "((AF) AND (LA) AND (LAA) AND (LAA ligation) AND (acute coronary syndrome) AND (anticoagulation) AND (atherosclerosis) AND (atrial septal aneurysm) AND (bleeding) AND (cardiac surgery) AND (cardioembolic event) AND (clinically significant) AND (comorbidities) AND (creatinine clearance) AND (gravidity) AND (greater than 10 mm) AND (indication) AND (less than 2 years) AND (less than 30 ml/min) AND (life expectancy) AND (mechanical valve prosthesis) AND (mitral stenosis) AND (mobile plaque in the aorta) AND (of the carotid artery) AND (other) AND (other than) AND (patent foramen ovale) AND (pericardial effusion) AND (significant) AND (stroke) AND (symptomatic) AND (the scheduled procedure) AND (thrombus) AND (valvular disease) AND (within the 30 days prior to the scheduled procedure) AND (within the 90 days prior to the scheduled procedure))"}
{"candidate_id": "LLM07655", "doc_id": "NCT02601157_inc", "case_bucket": "other", "source_criterion": "Patients with de novo stenotic lesions who are suitable for coronary stenting with drug-eluting stent", "candidate_expression": "((coronary stenting) AND (de novo) AND (drug-eluting stent) AND (stenotic lesions) AND (suitable))"}
{"candidate_id": "LLM07656", "doc_id": "NCT01980680_exc", "case_bucket": "other", "source_criterion": "Patients with >14 follicles on day of trigger Previous hyperresponse with OHSS development Previous low response (less than 3 oocytes on a high dose of FSH stimulation) Endocrine disorders", "candidate_expression": "((>14) AND (Endocrine disorders) AND (OHSS development) AND (Previous) AND (day of trigger) AND (follicles) AND (high dose of FSH stimulation) AND (hyperresponse) AND (less than 3) AND (low response) AND (on day of trigger) AND (oocytes))"}
{"candidate_id": "LLM07657", "doc_id": "NCT02916342_exc", "case_bucket": "or", "source_criterion": "indication for catheter insertion; contraindications to brachial plexus block (e.g., allergy to local anaesthetics, malignancy or infection in the area); existing neurological deficit in the area to be blocked; pregnancy; history of neck surgery or radiotherapy; severe respiratory disease; chest deformity; inability to understand the informed consent and demands of the study; patient refusal.", "candidate_expression": "((allergy) AND (brachial plexus block) AND (catheter insertion indication) AND (chest deformity) AND (contraindications) AND (inability to understand the informed consent and demands of the study;) AND (infection in the area) AND (local anaesthetics) AND (malignancy in the area) AND (neck surgery) AND (neurological deficit existing area to be blocked) AND (patient refusal) AND (pregnancy) AND (radiotherapy) AND (respiratory disease severe))"}
{"candidate_id": "LLM07658", "doc_id": "NCT02203019_exc", "case_bucket": "or", "source_criterion": "Patients with documented allergies to propofol, dexmedetomidine, fentanyl, eggs or egg products, or soy or soy products. A heart rate less than 50 beats/minute or grade 2 or 3 AV heart block Mean arterial pressure less than 55 mmHg despite appropriate fluid resuscitation and vasopressor support. Current triglyceride level > 400 mg/dl", "candidate_expression": "((> 400 mg/dl) AND (AV heart block) AND (Mean arterial pressure) AND (allergies) AND (dexmedetomidine) AND (egg products) AND (eggs) AND (fentanyl) AND (fluid resuscitation) AND (grade 2) AND (grade 3) AND (heart rate) AND (less than 50 beats/minute) AND (less than 55 mmHg) AND (propofol) AND (soy) AND (soy products) AND (triglyceride level) AND (vasopressor))"}
{"candidate_id": "LLM07659", "doc_id": "NCT03247738_inc", "case_bucket": "other", "source_criterion": "Patients with STEMI undergoing primary PPCI Age > 18 years old", "candidate_expression": "((> 18 years old) AND (Age) AND (STEMI) AND (primary PPCI))"}
{"candidate_id": "LLM07660", "doc_id": "NCT02779374_exc", "case_bucket": "or", "source_criterion": "Abnormal karyotype Previous pelvic or abdominal radiotherapy Previous surgical management of ovarian pathology Chronic disease: renal, liver, cardiac, malignancy", "candidate_expression": "((Abnormal karyotype) AND (Chronic disease) AND (Previous) AND (ovarian pathology) AND (surgical management) AND ((cardiac malignancy) OR (liver malignancy) OR (renal malignancy)) AND ((abdominal radiotherapy) OR (pelvic radiotherapy)))"}
{"candidate_id": "LLM07661", "doc_id": "NCT02926235_exc", "case_bucket": "other", "source_criterion": "All patients who were wheelchair bound preoperatively All patients who cannot participate in an outpatient physical therapy program for 3 days per week after surgery", "candidate_expression": "((cannot) AND (for 3 days per week after surgery) AND (outpatient) AND (physical therapy) AND (preoperatively) AND (surgery) AND (wheelchair bound))"}
{"candidate_id": "LLM07662", "doc_id": "NCT02357654_exc", "case_bucket": "other", "source_criterion": "day 3 transfers", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07663", "doc_id": "NCT01118871_exc", "case_bucket": "or", "source_criterion": "current alcohol abuse or drug dependence pregnancy active opportunistic infection or significant co-morbidities current prohibited concomitant medication a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing", "candidate_expression": "((a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing) AND (alcohol abuse) AND (co-morbidities) AND (concomitant) AND (current) AND (drug dependence) AND (medication) AND (opportunistic infection) AND (pregnancy) AND (prohibited) AND (significant))"}
{"candidate_id": "LLM07664", "doc_id": "NCT01890759_inc", "case_bucket": "or", "source_criterion": "Male and female subjects aged 9 to 17 months on the day of inclusion Informed consent form has been signed and dated by the parent(s) or other legally acceptable representative(s) (if applicable) Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.", "candidate_expression": "((Subject and parent/legally acceptable representative (if applicable) able to attend all scheduled visits and to comply with all trial procedures.) AND (aged 9 to 17 months on the day of inclusion) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07665", "doc_id": "NCT01978028_inc", "case_bucket": "or", "source_criterion": "Patients with chronic heart failure of New York Heart Association Class II or III, a left ventricular ejection fraction of = 40% for patients in NYHA class II or = 45% for patients in NYHA class III, a hemoglobin level at the screening visit between 9.5-13.5 g/dl, and iron deficiency, which is defined as serum ferritin level < 100µg/l or between 100 and 299 µg/l, when transferring saturation is < 20%. Age =18 years Obtained informed consent Stable pharmacological therapy during the last 4 weeks (with the exception of diuretics)", "candidate_expression": "((Age =18 years) AND (NYHA class II) AND (NYHA class III) AND (New York Heart Association Class II or III) AND (Obtained informed consent) AND (chronic heart failure) AND (hemoglobin level at the screening visit between 9.5-13.5 g/dl) AND (iron deficiency) AND (left ventricular ejection fraction) AND (pharmacological therapy Stable during the last 4 weeks) AND (serum ferritin level) AND (transferring saturation < 20%) AND NOT (diuretics) AND ((< 100µg/l) OR (between 100 and 299 µg/l)))"}
{"candidate_id": "LLM07666", "doc_id": "NCT02631512_inc", "case_bucket": "or", "source_criterion": "Type I or II diabetes mellitus. Target ulcer area between 0.5 and 5 sqcm, and more than 4 weeks old. Ankle-brachial pressure index above 0.7.", "candidate_expression": "((Ankle-brachial pressure index) AND (Target ulcer area) AND (Type I diabetes mellitus) AND (Type II diabetes mellitus) AND (above 0.7) AND (between 0.5 and 5 sqcm) AND (more than 4 weeks old))"}
{"candidate_id": "LLM07667", "doc_id": "NCT03082573_inc", "case_bucket": "other", "source_criterion": "Fluent in reading and writing in English language. = 21 years of age at the time of participation.", "candidate_expression": "(age = 21 years at the time of participation)"}
{"candidate_id": "LLM07668", "doc_id": "NCT02982577_inc", "case_bucket": "other", "source_criterion": "Age equal or superior to 18 years; Both genders; Lucid and without diagnosis of any psychiatric disorder; Diagnosed with head and neck cancer and treated for a period of up to 5 years with radiotherapy where the major salivary glands (parotid, submandibular and sublingual) were included in the radiation field; Primary Sjögren's syndrome with the diagnosis made by the American-European criteria.", "candidate_expression": "((5 years) AND (Age) AND (American-European criteria) AND (Lucid) AND (Primary Sjögren's syndrome) AND (equal or superior to 18 years) AND (genders) AND (head and neck cancer) AND (major salivary glands) AND (parotid) AND (psychiatric disorder) AND (radiotherapy) AND (sublingual) AND (submandibular) AND (without))"}
{"candidate_id": "LLM07669", "doc_id": "NCT03015818_inc", "case_bucket": "or", "source_criterion": "age > 18 written informed consent SVD defined on echocardiography by an alteration of bioprosthesis leaflets function with a mean transvalvular gradient > 20 mmHg and maximal velocity = 3 m/s and effective orifice area =1.2 cm², and/or an aortic regurgitation more or equal to grade 2 on 4.", "candidate_expression": "((= 3 m/s) AND (=1.2 cm²) AND (> 18) AND (> 20 mmHg) AND (SVD) AND (age) AND (alteration of bioprosthesis leaflets function) AND (aortic regurgitation) AND (echocardiography) AND (effective orifice area) AND (grade) AND (maximal velocity) AND (mean transvalvular gradient) AND (more or equal to 2 on 4) AND (written informed consent))"}
{"candidate_id": "LLM07670", "doc_id": "NCT02455921_inc", "case_bucket": "other", "source_criterion": "Children undergoing ENT surgery under general anaesthesia.", "candidate_expression": "((Children) AND (ENT surgery) AND (general anaesthesia) AND (undergoing))"}
{"candidate_id": "LLM07671", "doc_id": "NCT01806558_exc", "case_bucket": "or", "source_criterion": "1. Are unable to understand and sign the consent form 2. Are pregnant or lactating 3. Are physically unable to sit upright and still for 40 minutes 4. Have undergone bilateral mastectomy 5. Are not scheduled to undergo conventional ultrasound", "candidate_expression": "((Are unable to understand and sign the consent form) AND (bilateral mastectomy) AND (physically unable to sit upright and still for 40 minutes) AND NOT (conventional ultrasound scheduled) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM07672", "doc_id": "NCT00576173_inc", "case_bucket": "or", "source_criterion": "Patients with a histologically, radiologically or haematologically confirmed malignancy whose pain is judged by the investigator to be caused by the malignancy Patients must have been on a stable daily dose of weak opioids or strong opioids for at least 72 hours prior to the start the study and must remain at the same dosage for the duration of the study Patients must have a VAS (Visual analog scale) >=40mm", "candidate_expression": "((>=40mm) AND (VAS (Visual analog scale)) AND (at least 72 hours prior to the start the study) AND (confirmed) AND (haematologically) AND (histologically) AND (malignancy) AND (pain) AND (radiologically) AND (strong opioids) AND (weak opioids))"}
{"candidate_id": "LLM07673", "doc_id": "NCT00279552_exc", "case_bucket": "or", "source_criterion": "Patients who were pregnant, nursing or not able to give written informed consent were excluded.", "candidate_expression": "((able to give written informed consent) AND (not) AND (nursing) AND (pregnant))"}
{"candidate_id": "LLM07674", "doc_id": "NCT00639795_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 Planned thoracoscopy with low probability(by surgeon estimate) of conversion to open procedure", "candidate_expression": "((Age greater than 18) AND (low probability(by surgeon estimate) of conversion to open procedure) AND (thoracoscopy low probability(by surgeon estimate) of conversion to open procedure))"}
{"candidate_id": "LLM07675", "doc_id": "NCT02535299_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes mellitus,presence of autoimmune diabetes indicated by antibodies to insulin, islet cells, and GAD; Gestational diabetes; patients with heart, liver, or renal function impairment;presence of severe infections or cerebrovascular disease;", "candidate_expression": "((Gestational diabetes GAD) AND (Type 1 diabetes mellitus) AND (antibodies insulin islet cells) AND (autoimmune diabetes) AND (cerebrovascular disease) AND (heart function impairment) AND (infections) AND (liver function impairment) AND (renal function impairment))"}
```
