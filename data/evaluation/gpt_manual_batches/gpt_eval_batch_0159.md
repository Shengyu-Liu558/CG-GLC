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
{"candidate_id": "LLM03951", "doc_id": "NCT03282006_inc", "case_bucket": "or", "source_criterion": "E.coli in blood culture AND identical isolate in urine sample (>= 1.000 CFU) OR relevant clinical signs of UTI", "candidate_expression": "((CFU >= 1.000) AND (blood culture E.coli) AND ((UTI clinical signs) OR (urine sample identical isolate)))"}
{"candidate_id": "LLM03952", "doc_id": "NCT01806558_inc", "case_bucket": "or", "source_criterion": "1. Have a finding of a mass lesion on mammography or breast MRI (BIRADS 0, 4 or 5) that is >0.5 cm and < 2 cm in size and has had or will have additional workup with focused ultrasound. 2. Have a finding of a mass lesion on ultrasound (BIRADS 0, 4 or 5) that is > 0.5 cm and < 2 cm in size. 3. Have a positive finding on MBI that is < 2 cm in size and requires additional diagnostic workup with focused ultrasound.", "candidate_expression": "((BIRADS 0, 4 or 5) AND (MBI) AND (mass lesion) AND (positive finding) AND (requires additional diagnostic workup with focused ultrasound) AND (size < 2 cm) AND (size > 0.5 cm and < 2 cm) AND (size >0.5 cm and < 2 cm) AND (ultrasound) AND ((breast MRI) OR (mammography)))"}
{"candidate_id": "LLM03953", "doc_id": "NCT03168555_inc", "case_bucket": "other", "source_criterion": "planned elective cholecystectomy", "candidate_expression": "((cholecystectomy) AND (elective) AND (planned))"}
{"candidate_id": "LLM03954", "doc_id": "NCT03297125_exc", "case_bucket": "or", "source_criterion": "Optune compliance < 75%; they would be excluded from the final analyses. History of craniectomy or significant skull defect (contraindication to Optune). Active implantable medical device (i.e. DBS, spinal cord stimulator, pacemaker, defibrillator, vagus nerve stimulator, programmable shunt). Karnofsky Performance Status (KPS) < 60.", "candidate_expression": "((DBS) AND (KPS) AND (Karnofsky Performance Status < 60) AND (Optune) AND (Optune compliance < 75%) AND (contraindication) AND (craniectomy) AND (defibrillator) AND (implantable medical device Active) AND (pacemaker) AND (programmable shunt) AND (skull defect significant) AND (spinal cord stimulator) AND (vagus nerve stimulator))"}
{"candidate_id": "LLM03955", "doc_id": "NCT01942915_inc", "case_bucket": "other", "source_criterion": "Patients with hepatocirrhosis: according to the standard of child- pugh, liver functions to achieve class A or B patients, Including C class patients but can achieve B class after treatment", "candidate_expression": "(hepatocirrhosis)"}
{"candidate_id": "LLM03956", "doc_id": "NCT01391780_exc", "case_bucket": "or", "source_criterion": "neurological diseases previous pelvic surgeries diabetes cognitive difficulties vaginal and urinary infection", "candidate_expression": "((cognitive difficulties) AND (diabetes) AND (infection vaginal) AND (neurological diseases) AND (pelvic surgeries previous) AND (urinary infection))"}
{"candidate_id": "LLM03957", "doc_id": "NCT02473809_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Treatment with insulin Body weight > 140 kg HbA1c > 75 mmol/mol Treatment with GLP-1 analogues, Dipeptidyl peptidase-4 inhibitors, or glitazones Chronic kidney disease Hepatic disease Pancreatitis Inflammatory bowel disease Osteoporosis Family or personal history of medullary thyroid carcinoma Treatment with glucocorticoids Hormone replacement therapy Diabetic gastroparesis Pregnancy or lactation", "candidate_expression": "((Body weight > 140 kg) AND (Chronic kidney disease) AND (Diabetic gastroparesis) AND (Dipeptidyl peptidase-4 inhibitors) AND (Family) AND (GLP-1 analogues) AND (HbA1c > 75 mmol/mol) AND (Hepatic disease) AND (Hormone replacement therapy) AND (Inflammatory bowel disease) AND (Osteoporosis) AND (Pancreatitis) AND (Pregnancy) AND (Treatment) AND (Type 1 diabetes) AND (glitazones) AND (glucocorticoids) AND (insulin) AND (lactation) AND (medullary thyroid carcinoma) AND (personal history))"}
{"candidate_id": "LLM03958", "doc_id": "NCT02019628_exc", "case_bucket": "or", "source_criterion": "1. Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning. 2. Unable to consent to the study. 3. Women who are pregnant or are attempting conception, especially in the presence of a history of recurrent spontaneous abortion. 4. Other medical complications that might preclude one from participating in the study, i.e., recent heart attack or stroke or chronic kidney disease. 5. Currently taking immunomodulatory medication, i.e. interferon. 6. Currently taking other medications thought to have an impact on immune system functioning, i.e., chemotherapeutic agents. 7. Known allergy to rice, rice bran, or related food products. 8. Known allergy to mushrooms or related food products. 9. History of malignancies related to the NK cell line, including: NK cell leukemias and T-cell large granular lymphocyte leukemias, NK-cell lymphoproliferative disease of granular lymphocytes, and NK cell lymphomas, e.g., nasal and nasal-like NK/T-cell lymphomas. 10. Current smoker.", "candidate_expression": "((Current) AND (Currently) AND (Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning.) AND (History) AND (NK cell leukemias) AND (NK cell lymphomas) AND (NK-cell lymphoproliferative disease of granular lymphocytes) AND (Other) AND (T-cell large granular lymphocyte leukemias) AND (Unable to consent to the study.) AND (Women) AND (allergy to food products) AND (allergy to mushrooms) AND (allergy to rice) AND (allergy to rice bran) AND (chemotherapeutic agents) AND (chronic kidney disease) AND (heart attack) AND (immunomodulatory medication) AND (impact on immune system functioning) AND (interferon) AND (malignancies) AND (medical complications) AND (medications) AND (nasal NK/T-cell lymphomas) AND (nasal-like NK/T-cell lymphomas) AND (other) AND (participating in the study) AND (preclude) AND (pregnant) AND (recent) AND (recurrent) AND (related to the NK cell line) AND (rice) AND (rice bran) AND (smoker) AND (spontaneous abortion) AND (stroke))"}
{"candidate_id": "LLM03959", "doc_id": "NCT03446885_exc", "case_bucket": "or", "source_criterion": "any medical condition that would contraindicate use of stimulant medication any prior adverse response to lisdexamfetamine dimesylate or other stimulant medication use of concurrent,non-stimulant psychoactive medication diagnosis of schizophrenia or presence of thought disorder symptoms autism spectrum disorder", "candidate_expression": "((adverse response) AND (autism spectrum disorder) AND (concurrent) AND (contraindicate) AND (medical condition) AND (non-stimulant psychoactive medication) AND (other) AND (prior) AND (stimulant medication) AND (symptoms) AND ((schizophrenia) OR (thought disorder)) AND ((lisdexamfetamine dimesylate) OR (stimulant medication)))"}
{"candidate_id": "LLM03960", "doc_id": "NCT03500211_exc", "case_bucket": "or", "source_criterion": "Patients requiring emergent cesarean birth Patients allergic to lidocaine or adhesive Patients who have already received an epidural during this admission or requiring general anesthesia for cesarean birth Patients using chronic oral neuromodulators Patients with cardiac disease or using anti-arrhythmic agents Patients with fibromyalgia or chronic pain syndromes such as rheumatoid arthritis, osteoarthritis, or lupus. Daily narcotic or opiate use for greater than the 2 months prior to enrollment in the study.", "candidate_expression": "((Daily) AND (allergic) AND (cesarean birth) AND (chronic oral neuromodulators) AND (during this admission) AND (emergent cesarean birth) AND (enrollment in the study) AND (for greater than the 2 months prior to enrollment in the study) AND (requiring) AND ((anti-arrhythmic agents) OR (cardiac disease)) AND ((chronic pain syndromes) OR (fibromyalgia)) AND ((lupus) OR (osteoarthritis) OR (rheumatoid arthritis)) AND ((narcotic) OR (opiate)) AND ((adhesive) OR (lidocaine)) AND ((epidural) OR (general anesthesia)))"}
{"candidate_id": "LLM03961", "doc_id": "NCT02833623_exc", "case_bucket": "or", "source_criterion": "advanced chronic disease that would not allow the patient to complete the treatment or follow-up or attend visits allergy to any of the drugs used in this study previous Helicobacter Pylori eradication treatment pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study) taking antibiotics or PPIs or bismuth salts within four weeks previous gastrointestinal surgery", "candidate_expression": "((Helicobacter Pylori eradication treatment) AND (PPIs) AND (antibiotics) AND (bismuth salts) AND (gastrointestinal surgery) AND (pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study)) AND (within four weeks))"}
{"candidate_id": "LLM03962", "doc_id": "NCT03017053_exc", "case_bucket": "or", "source_criterion": "Inability to provide an informed consent Evidence of oral distant metastasis or other malignancies The patient has received prior surgery for primary tumor or lymph node ( except for biopsy ) Prior radiotherapy for primary tumor The patient has previously received anti-tumor biological targeted therapy The patient has received chemotherapy or immunotherapy for primary tumors Prior malignancy within the previous 5 years (except for cured skin basal cell carcinoma or cervical carcinoma in situ) With 3-4 grad Allergy to any drug in the treatment Peripheral neuropathy> 1 grade Any unstable systematic disease (including active infection, uncontrolled high blood pressure, unstable angina, onset of angina within the last 3 months, congestive heart failure, myocardial infarction within the previous 12 months, severe arrhythmia needing drug treatment, liver, kidney or metabolic disease) HIV positive Chronic diseases requiring immune agents or hormone therapy Pregnant or lactating women Drug/alcohol abuse, psychological or spiritual illness that may interfere compliance to the study Patients with epilepsy requiring medications (such as steroids or antiepileptic drugs) The patient has participated in other experimental therapy studies within 30 days Researchers believe that the situation is unsuitable for participation in the group", "candidate_expression": "((Allergy 3-4 grad) AND (Chronic diseases) AND (Drug/alcohol abuse, psychological or spiritual illness that may interfere compliance to the study) AND (HIV positive) AND (Peripheral neuropathy > 1 grade) AND (Pregnant) AND (angina) AND (anti-tumor biological targeted therapy previously) AND (antiepileptic drugs) AND (arrhythmia severe) AND (cervical carcinoma in situ) AND (chemotherapy) AND (congestive heart failure) AND (cured skin basal cell carcinoma) AND (drug) AND (drug any) AND (epilepsy) AND (high blood pressure uncontrolled) AND (hormone therapy) AND (immune agents) AND (immunotherapy) AND (infection) AND (kidney disease) AND (lactating) AND (liver disease) AND (lymph node) AND (malignancies other) AND (malignancy Prior within the previous 5 years) AND (medications) AND (metabolic disease) AND (metastasis oral distant) AND (myocardial infarction within the previous 12 months) AND (onset within the last 3 months) AND (primary tumors) AND (radiotherapy Prior) AND (steroids) AND (surgery prior) AND (systematic disease unstable) AND (treatment) AND (tumor) AND (tumor primary) AND (unstable angina) AND (women) AND NOT (biopsy))"}
{"candidate_id": "LLM03963", "doc_id": "NCT01322464_exc", "case_bucket": "or", "source_criterion": "Subjects were not to have a history or presence of significant cardiovascular, pulmonary, hepatic, renal, haematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease. Subjects were not to have any history or presence or family history of schizophrenia, other psychotic illness, severe personality disorder, depression, or other significant psychiatric disorder. Subjects were not to have a postural drop of 20 mmHg or more in systolic blood pressure at screening. Subjects were not to have participated in a previous clinical trial within 90 days prior to study initiation. Subjects were not to have donated plasma within 90 days prior to study initiation. Subjects were not to have donated blood within 90 days prior to study initiation. Subjects were not to have had an abnormal diet or substantial changes in eating habits within 30 days prior to study initiation. Subjects were not to have had treatment with any known enzyme-altering agents (barbiturates, phenothiazines, cimetidine etc.) within 30 days prior to or during the study. Subjects were to have no history of known hypersensitivity or idiosyncratic reaction to the study drug or related compounds. Subjects were not to use any prescription medication within 14 days prior to or during the study. Subjects were not to use any over-the-counter medication within 7 days prior to or during the study. Subjects were not to have a history of alcohol or drug abuse within 2 years prior to the study (subjects with a history of previous use of cannabis were not excluded unless they had used cannabis or cannabinoid based medicine within 30 days prior to study drug administration or were unwilling to abstain for the duration of the study).", "candidate_expression": "((depression) AND (enzyme-altering agents within 30 days prior to or during the study) AND (not excluded) AND (participated in a previous clinical trial 90 days prior to study initiation) AND (psychiatric disorder significant) AND (psychotic illness) AND (schizophrenia) AND (severe personality disorder) AND (study drug) AND (systolic blood pressure postural drop of 20 mmHg at screening) AND (use of cannabis) AND NOT (donated plasma within 90 days prior to study initiation) AND NOT (donated blood within 90 days prior to study initiation) AND NOT (hypersensitivity) AND NOT (idiosyncratic reaction) AND NOT (prescription medication) AND NOT (over-the-counter medication the study) AND ((family history) OR (history) OR (presence)) AND ((abnormal diet) OR (changes in eating habits substantial)) AND ((barbiturates) OR (cimetidine) OR (phenothiazines)) AND ((during the study) OR (within 14 days prior to the study)) AND ((during the study) OR (within 7 days prior to the study)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM03964", "doc_id": "NCT02056288_inc", "case_bucket": "other", "source_criterion": "Supracondylar fracture Age 2-17 years American Society of Anesthesiologists Status 1 -3 Scheduled for closed reduction with percutaneous pinning under general anesthesia", "candidate_expression": "((Age 2-17 years) AND (American Society of Anesthesiologists Status 1 -3) AND (Supracondylar fracture) AND (closed reduction with percutaneous pinning Scheduled for) AND (general anesthesia))"}
{"candidate_id": "LLM03965", "doc_id": "NCT00312429_exc", "case_bucket": "or", "source_criterion": "Undergoing Interleukin-2 (IL-2) therapy within 8 weeks of study entry Diagnosed with a medical or psychiatric illness that may interfere with study participation Pregnant", "candidate_expression": "((Interleukin-2 (IL-2) therapy within 8 weeks of study entry) AND (Pregnant) AND (illness that may interfere with study participation medical) AND (psychiatric illness that may interfere with study participation))"}
{"candidate_id": "LLM03966", "doc_id": "NCT02787863_exc", "case_bucket": "or", "source_criterion": "Vaccination against pneumococcal infection in anamnesis; Application of preparations of immune globulin or blood transfusion within last three months prior to clinical studies; Prolonged use (more than 14 days) immunosuppressants or other immunosuppressive drugs within 6 months prior to the start of the study; Any confirmed or suspected immunosuppressive or immunodeficient condition, including HIV infection; A history or currently hematologic and other cancers; A positive reaction for HIV infection, viral hepatitis B and hepatitis C; The presence of respiratory, cardio-vascular insufficiency, impaired liver and kidney function, established during a physical examination at visit number 1; Pronounced congenital defects or serious chronic diseases in the acute stage, including any clinically important exacerbation of chronic diseases of the liver, kidney, cardiovascular, nervous system, mental diseases or metabolic disorders, confirmed by the history or objective examination (pulmonary: cystic fibrosis, lung abscess, empyema, active tuberculosis; extra-pulmonary: congestive heart failure, malabsorption, chronic renal and hepatic failure, cirrhosis, malignancy, immunodeficiency, cirrhosis of the liver); Severe allergic reactions in anamnesis of autoimmune disease; The presence of acute infectious and/or communicable illnesses within 1 month prior to study; History of chronic alcohol abuse and/or drug use; Exacerbation of chronic diseases; Breastfeeding; Pregnancy; Participation in any other clinical study within the last 3 months.", "candidate_expression": "((Breastfeeding) AND (Exacerbation) AND (HIV infection) AND (Participation in clinical study) AND (Pregnancy) AND (Prolonged use) AND (Severe) AND (Vaccination) AND (active) AND (acute) AND (acute stage) AND (allergic reactions) AND (any other) AND (at visit number 1) AND (chronic) AND (chronic diseases) AND (clinically important) AND (communicable illnesses) AND (diseases of the cardiovascular system) AND (diseases of the kidney) AND (diseases of the liver) AND (diseases of the nervous system) AND (hepatic failure) AND (infectious illnesses) AND (more than 14 days) AND (other) AND (pneumococcal infection) AND (positive) AND (renal failure) AND (serious) AND (study) AND (within 1 month prior to study) AND (within 6 months prior to the start of the study) AND (within last three months prior to clinical studies) AND (within the last 3 months) AND ((immunodeficient condition) OR (immunosuppressive condition)) AND ((reaction for HIV infection) OR (reaction for hepatitis C) OR (reaction for viral hepatitis B)) AND ((cardio-vascular insufficiency) OR (impaired kidney function) OR (impaired liver) OR (respiratory insufficiency)) AND ((chronic diseases) OR (congenital defects)) AND ((exacerbation) OR (mental diseases) OR (metabolic disorders)) AND ((blood transfusion) OR (preparations of immune globulin)) AND ((cirrhosis) OR (cirrhosis of the liver) OR (congestive heart failure) OR (cystic fibrosis) OR (empyema) OR (immunodeficiency) OR (lung abscess) OR (malabsorption) OR (malignancy) OR (tuberculosis)) AND ((alcohol abuse) OR (drug use)) AND ((immunosuppressants) OR (immunosuppressive drugs)))"}
{"candidate_id": "LLM03967", "doc_id": "NCT02563535_exc", "case_bucket": "or", "source_criterion": "need for major amputation known before intervention allergy to Paclitaxel contraindication for combined antiplatelet treatment life expectancy <1 year hypersensitivity or contraindication to one of the study drugs lack of consent", "candidate_expression": "((<1 year) AND (Paclitaxel) AND (allergy) AND (combined antiplatelet treatment) AND (contraindication) AND (hypersensitivity) AND (lack of consent) AND (life expectancy) AND (major amputation) AND (one of) AND (study drugs))"}
{"candidate_id": "LLM03968", "doc_id": "NCT03500211_exc", "case_bucket": "or", "source_criterion": "Patients requiring emergent cesarean birth Patients allergic to lidocaine or adhesive Patients who have already received an epidural during this admission or requiring general anesthesia for cesarean birth Patients using chronic oral neuromodulators Patients with cardiac disease or using anti-arrhythmic agents Patients with fibromyalgia or chronic pain syndromes such as rheumatoid arthritis, osteoarthritis, or lupus. Daily narcotic or opiate use for greater than the 2 months prior to enrollment in the study.", "candidate_expression": "((Daily) AND (adhesive) AND (allergic) AND (anti-arrhythmic agents) AND (cardiac disease) AND (cesarean birth) AND (chronic oral neuromodulators) AND (chronic pain syndromes) AND (during this admission) AND (emergent cesarean birth) AND (enrollment in the study) AND (epidural) AND (fibromyalgia) AND (for greater than the 2 months prior to enrollment in the study) AND (general anesthesia) AND (lidocaine) AND (lupus) AND (narcotic) AND (opiate) AND (osteoarthritis) AND (requiring) AND (rheumatoid arthritis))"}
{"candidate_id": "LLM03969", "doc_id": "NCT03231982_inc", "case_bucket": "other", "source_criterion": "Adult male and female aged 19 to 75 years Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.", "candidate_expression": "((Voluntarily consented to participate in the study and signed the informed consent form after receiving the explanation of the objectives, methods and effects of the study.) AND (aged 19 to 75 years) AND (female) AND (male))"}
{"candidate_id": "LLM03970", "doc_id": "NCT02022709_exc", "case_bucket": "or", "source_criterion": "Having significant medical illnesses that would interfere with the conduct of the study Clinically significant abnormal laboratory finding Having comorbid psychiatric conditions according to the criteria set forth in the DSM-IV(administered by the Mini-International Neuropsychiatric Interview (MINI)) The current OCD symptoms are too severe that the patient cannot finish the evaluation or receive the ERP Being currently at risk for suicide Being pregnant or having the intention to be pregnant before the end of the study A history of having inadequate response to adequate SSRIs or CBT treatment Subjects who are unable to undergo the MRI", "candidate_expression": "((Being pregnant or having the intention to be pregnant before the end of the study) AND (CBT) AND (DSM-IV) AND (MRI) AND (OCD symptoms) AND (SSRIs) AND (comorbid) AND (inadequate) AND (psychiatric conditions) AND (response) AND (risk for suicide) AND (severe) AND (unable to))"}
{"candidate_id": "LLM03971", "doc_id": "NCT03461679_inc", "case_bucket": "other", "source_criterion": "Patients undergoing total knee arthroplasty under spinal anaesthesia 45y or older ASA 1-3 BMI 18-35", "candidate_expression": "((1-3) AND (18-35) AND (45 or older) AND (ASA) AND (BMI) AND (spinal anaesthesia) AND (total knee arthroplasty) AND (y))"}
{"candidate_id": "LLM03972", "doc_id": "NCT02735577_inc", "case_bucket": "or", "source_criterion": "Between the ages of 21-60 Right-handed Capable of giving informed consent and complying with study procedures Reports drinking a minimum of 5 standard drinks for men or 4 standard drinks for women on at least 4 days per week on average over the past 28 days Meets DSM-V criteria for current Alcohol Use Disorder Seeking treatment for Alcohol Use Disorder Agree to not seek additional treatment, apart from Alcoholics Anonymous Willing to attempt to abstain from alcohol completely for the duration of the study Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed.", "candidate_expression": "((Alcohol Use Disorder) AND (DSM-V criteria Meets) AND (Right-handed) AND (Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed) AND (abstain from alcohol Willing completely) AND (ages Between 21-60) AND (drinking over the past 28 days) AND (treatment Seeking) AND ((men minimum of 5 standard drinks on at least 4 days per week) OR (women 4 standard drinks on at least 4 days per week)))"}
{"candidate_id": "LLM03973", "doc_id": "NCT03344887_inc", "case_bucket": "other", "source_criterion": "All patients (excluding neonates) requiring one or more allogeneic RBC transfusions for the treatment of anemia will be included.", "candidate_expression": "((RBC transfusions) AND (allogeneic) AND (anemia) AND (excluding) AND (neonates) AND (one or more) AND (requiring) AND (treatment))"}
{"candidate_id": "LLM03974", "doc_id": "NCT02763007_exc", "case_bucket": "or", "source_criterion": "eGFR(Epidermal growth factor receptor) < 50mL/min AST(aspartate aminotransferase)/ALT(alanine aminotransaminase) >2.5 upper limit of normal Pregnant or lactating women Subject who the investigator deems inappropriate to participate in this study Patients with a history of bladder cancer or patients with active bladder cancer Patients with uninvestigated macroscopic hematuria Patients with cardiac failure or a history of cardiac failure (New York Heart Association [NYHA] Stages 3 to 4) Patients with genetic problems such as galactose intolerance, Lapp lactase deficiency or glucose-galactose malabsorption, since this study drug contains lactose", "candidate_expression": "((ALT) AND (AST) AND (Epidermal growth factor receptor) AND (Lapp lactase deficiency) AND (NYHA) AND (New York Heart Association Stages 3 to 4) AND (Pregnant or lactating women) AND (alanine aminotransaminase) AND (aspartate aminotransferase) AND (bladder cancer) AND (bladder cancer active) AND (cardiac failure) AND (eGFR < 50mL/min) AND (galactose intolerance) AND (genetic problems) AND (glucose-galactose malabsorption) AND (history of cardiac failure) AND (macroscopic hematuria uninvestigated))"}
{"candidate_id": "LLM03975", "doc_id": "NCT03260790_exc", "case_bucket": "other", "source_criterion": "Research exemption requested History of PCV-13 vaccination History of cochlear implant Cerebrospinal Fluid (CSF) leak Congestive Heart Failure (CHF) Diabetes Mellitus (DM) Chronic Kidney Disease (CKD) Human Immunodeficiency Virus (HIV) Common Variable Immune Deficiency (CVID) Patients who have received the PPSV23 vaccine in the last 5 years Women who are pregnant will also be excluded from the study by performing 2 point of care urine pregnancy tests ( prior to vaccinations)", "candidate_expression": "((2) AND (Cerebrospinal Fluid (CSF) leak) AND (Chronic Kidney Disease (CKD)) AND (Common Variable Immune Deficiency (CVID)) AND (Congestive Heart Failure (CHF)) AND (Diabetes Mellitus (DM)) AND (History) AND (Human Immunodeficiency Virus (HIV)) AND (PCV-13 vaccination) AND (PPSV23 vaccine) AND (Research exemption requested) AND (Women) AND (cochlear implant) AND (in the last 5 years) AND (point of care urine pregnancy tests) AND (pregnant) AND (prior to vaccinations) AND (vaccinations))"}
```
