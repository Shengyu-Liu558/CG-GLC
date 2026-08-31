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
{"candidate_id": "LLM00901", "doc_id": "NCT03056391_exc", "case_bucket": "or", "source_criterion": "1. Patient or relatives unable or unwilling to give informed consent 2. Contraindication or allergy to paracetamol or artesunate therapy 3. Known cirrhosis, or >6 standard alcoholic drinks/day 4. Pregnancy", "candidate_expression": "((>6 standard alcoholic drinks/day) AND (Contraindication) AND (Patient or relatives unable or unwilling to give informed consent) AND (Pregnancy) AND (allergy) AND (artesunate) AND (cirrhosis) AND (paracetamol))"}
{"candidate_id": "LLM00902", "doc_id": "NCT02580630_inc", "case_bucket": "or", "source_criterion": "Midsubstance pain in the achilles tendon Symptoms for at least 3 months Ultrasound scanning at the first visit shows thickness of the achilles tendon above 7 mm or 20% thicker than the contralateral. Patient can read and understand danish", "candidate_expression": "((Midsubstance pain achilles tendon) AND (Symptoms for at least 3 months) AND (Ultrasound scanning at the first visit) AND (thickness of the achilles tendon) AND ((20% thicker than the contralateral) OR (above 7 mm)))"}
{"candidate_id": "LLM00903", "doc_id": "NCT03497598_exc", "case_bucket": "or", "source_criterion": "UTIs = 12 within 1 year Pregnancy or Lactation Immune disease Lactose intolerance Urinary tract anomaly Systemic infection Newly started hormone therapy within the last 6 months Antibiotic prophylaxis within the last 6 months a-D-mannose intake within the last month Use of catheters Diabetes mellitus Participation to other studies", "candidate_expression": "((12 within 1 year) AND (Antibiotic) AND (Antibiotic prophylaxis) AND (Diabetes mellitus) AND (Immune disease) AND (Lactation) AND (Lactose) AND (Lactose intolerance) AND (Newly started) AND (Participation to other studies) AND (Pregnancy) AND (Systemic infection) AND (UTIs) AND (Urinary tract anomaly) AND (a-D-mannose) AND (catheters) AND (hormone therapy) AND (intolerance) AND (within 1 year) AND (within the last 6 months) AND (within the last month))"}
{"candidate_id": "LLM00904", "doc_id": "NCT01631058_exc", "case_bucket": "or", "source_criterion": "Allergy to any of proposed medications Patients with any active infection including HBV, HCV and HIV.", "candidate_expression": "((Allergy) AND (HBV) AND (HCV) AND (HIV) AND (active infection) AND (proposed medications))"}
{"candidate_id": "LLM00905", "doc_id": "NCT03151603_inc", "case_bucket": "or", "source_criterion": "Women (18-75 years) with suspected UTI at least two symptoms of UTI (dysuria, urgency of micturition, frequency, lower abdominal pain) Written informed consent", "candidate_expression": "((UTI suspected) AND (Women) AND (Written informed consent) AND (symptoms of UTI at least two) AND (years 18-75) AND ((dysuria) OR (frequency) OR (lower abdominal pain) OR (urgency of micturition)))"}
{"candidate_id": "LLM00906", "doc_id": "NCT03045562_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00907", "doc_id": "NCT03495557_inc", "case_bucket": "or", "source_criterion": "Age = 18 years Laparoscopic cholecystectomy Emergent/elective =2 risk factors: diabetes mellitus, age =70 years, BMI =30, fascial enlargement", "candidate_expression": "((= 18 years) AND (=2) AND (=30) AND (=70 years) AND (Age) AND (BMI) AND (Emergent) AND (Laparoscopic) AND (age) AND (cholecystectomy) AND (diabetes mellitus) AND (elective) AND (fascial enlargement) AND (risk factors))"}
{"candidate_id": "LLM00908", "doc_id": "NCT02983214_inc", "case_bucket": "other", "source_criterion": "Patients aged =50 years with DM2 and symptomatic PAD diagnosed clinically (according to Fontaine criteria, stage IIa or IIb and III) and by measuring the <U+0391><U+0392><U+0399>.", "candidate_expression": "((DM2) AND (Fontaine criteria stage IIa or IIb and III) AND (PAD symptomatic) AND (aged =50 years))"}
{"candidate_id": "LLM00909", "doc_id": "NCT00576173_exc", "case_bucket": "or", "source_criterion": "Patients who have taken either morphine with daily dose more than 120mg or Fentanyl with daily dose more than 50ug/hr Patients with significant abnormalities in hepatic or renal function which would, in the opinion of the investigator, prevent the patients involvement in the study Patients with significant clinical abnormalities in CNS, respiratory or cardiovascular function, which in the investigators judgement prevents participation in the study Patients who have taken antidepressants or anti-epileptic drugs, sedative hypnotics, selective serotonin reuptake inhibitor, short-acting analgesics, topical medications and anesthetics and/or muscle relaxants when taking Tramadol/Acetaminophen", "candidate_expression": "(((anesthetics) OR (anti-epileptic drugs) OR (antidepressants) OR (muscle relaxants) OR (sedative hypnotics) OR (selective serotonin reuptake inhibitor) OR (short-acting analgesics) OR (topical medications)) AND ((Acetaminophen) OR (Tramadol)) AND ((Fentanyl daily dose more than 50ug/hr) OR (morphine daily dose more than 120mg)) AND ((abnormalities in hepatic function) OR (abnormalities in renal function)) AND ((abnormalities in CNS) OR (abnormalities in cardiovascular function) OR (abnormalities in respiratory function)))"}
{"candidate_id": "LLM00910", "doc_id": "NCT03169127_inc", "case_bucket": "other", "source_criterion": "Need of lower third molar surgeries", "candidate_expression": "(surgeries lower third molar)"}
{"candidate_id": "LLM00911", "doc_id": "NCT02858804_inc", "case_bucket": "or", "source_criterion": "age=65 years diagnosis with mantle cell lymphoma Ann Arbor stage II,III or IV ECOG=1 or if ECOG=2 but recover after pretreatment.", "candidate_expression": "((Ann Arbor stage II III) AND (ECOG =1 IV) AND (ECOG =2) AND (age =65 years) AND (mantle cell lymphoma) AND (pretreatment) AND (recover after pretreatment))"}
{"candidate_id": "LLM00912", "doc_id": "NCT03344887_exc", "case_bucket": "other", "source_criterion": "Patients that do not have a valid Ontario Health Insurance Plan (OHIP) number at time of first transfusion Patients that require emergent release of a RBC transfusion and in whom emergency randomization could not be completed Patients with complex antibody profile in which it is impossible to match RBC units", "candidate_expression": "((RBC transfusion require emergent release) AND (complex antibody profile) AND (impossible to match RBC units) AND (transfusion first) AND NOT (have a valid Ontario Health Insurance Plan (OHIP) number at time of first transfusion) AND NOT (emergency randomization))"}
{"candidate_id": "LLM00913", "doc_id": "NCT02707809_inc", "case_bucket": "other", "source_criterion": "kidney transplant recipient", "candidate_expression": "(kidney transplant)"}
{"candidate_id": "LLM00914", "doc_id": "NCT02901106_inc", "case_bucket": "or", "source_criterion": "patient 18 years old and more with multiple sclerosis according to the criteria of Mac Donald 2010 : relapsing-remitting (RR), secondary-progressive (SP) or primary-progressive (PP) for which treatment with dimethyl-fumarate has been prescribed followed at the Rothschild Foundation in the Neurology Department having given written consent to participation in the study", "candidate_expression": "((PP) AND (RR) AND (Rothschild Foundation in the Neurology Department) AND (SP) AND (and more 18 years) AND (criteria of Mac Donald 2010) AND (dimethyl-fumarate) AND (having given written consent to participation in the study) AND (multiple sclerosis) AND (old) AND ((primary-progressive) OR (relapsing-remitting) OR (secondary-progressive)))"}
{"candidate_id": "LLM00915", "doc_id": "NCT00480129_exc", "case_bucket": "other", "source_criterion": "Ongoing allergen immunotherapy upper respiratory tract infection Pregnancy Clinical history of lactose-intolerance or allergies to cow-milk", "candidate_expression": "((Pregnancy) AND (allergen immunotherapy) AND (allergies to cow-milk) AND (lactose-intolerance) AND (upper respiratory tract infection))"}
{"candidate_id": "LLM00916", "doc_id": "NCT02882113_exc", "case_bucket": "or", "source_criterion": "Patients who have Tacrolimus trough level resulted as 2 ng/mg at the baseline. Patients who are on steroid therapy due to positive result of acute rejection test before the baseline. Patients who have received a transplant besides liver. Patients who are allergic to IP or macrolide compounds. Patients who are on cyclosporine, bosentan, or potassium sparing diuretic. Patients with genetic diseases such as galactose intolerance, Lapp lactase deficiency, or glucose-galactose malabsorption. Pregnant or lactating women. Patients not willing to adhere to study procedures/treatments.", "candidate_expression": "((IP) AND (Lapp lactase deficiency) AND (Patients not willing to adhere to study procedures/treatments) AND (Pregnant or lactating women) AND (Tacrolimus 2 ng/mg) AND (acute rejection test positive) AND (allergic) AND (bosentan) AND (cyclosporine) AND (galactose intolerance) AND (genetic diseases) AND (glucose-galactose malabsorption) AND (macrolide) AND (potassium sparing diuretic) AND (steroid) AND (transplant liver))"}
{"candidate_id": "LLM00917", "doc_id": "NCT03648021_inc", "case_bucket": "or", "source_criterion": "18-year or older patients Patient hospitalized in neuro-critical care for: Arachnoid hemorrhage Intra parenchymatous hematoma stroke Acute brain Severe injury Post-operative complication of an act of neurosurgery or programmed neuroradiology Sedation and mechanical ventilation planned > 2 days Monitoring of intracranial temperature and pressure by intraparenchymal sensor (Sophysa®) Brain temperature > 38.5°C for more than 30 minutes", "candidate_expression": "((Acute brain Severe injury) AND (Arachnoid hemorrhage) AND (Brain temperature > 38.5°C for more than 30 minutes) AND (Post-operative complication) AND (Sedation) AND (Sophysa®) AND (hematoma Intra parenchymatous) AND (hospitalized) AND (intraparenchymal sensor) AND (mechanical ventilation) AND (neuro-critical care) AND (neuroradiology) AND (neurosurgery) AND (old 18-year or older) AND (stroke) AND ((of an act of neurosurgery) OR (of an act of programmed neuroradiology)) AND ((intracranial pressure) OR (intracranial temperature)))"}
{"candidate_id": "LLM00918", "doc_id": "NCT02893228_inc", "case_bucket": "or", "source_criterion": "Patients undergoing surgery on shoulder, humerus, or clavicle", "candidate_expression": "(surgery shoulder humerus clavicle)"}
{"candidate_id": "LLM00919", "doc_id": "NCT03424993_inc", "case_bucket": "other", "source_criterion": "Habitual dietary sodium intake > 3400mg per day", "candidate_expression": "((> 3400mg per day) AND (dietary sodium intake))"}
{"candidate_id": "LLM00920", "doc_id": "NCT02299063_exc", "case_bucket": "or", "source_criterion": "recent surgery (< 3 months) previous chemotherapy previous transfusion of blood products neurodevelopmental disorders (including Trisomy 21) supplemental oxygen requirement (< 3 months) asthma requiring regular therapy obstructive sleep apnea the presence of concurrent infection or inflammation a known allergy to dexmedetomidine hydrochloride", "candidate_expression": "((< 3 months) AND (Trisomy 21) AND (allergy) AND (asthma) AND (chemotherapy) AND (concurrent) AND (dexmedetomidine hydrochloride) AND (neurodevelopmental disorders) AND (obstructive sleep apnea) AND (previous) AND (recent) AND (regular therapy) AND (requirement) AND (supplemental oxygen) AND (surgery) AND (transfusion of blood products) AND ((infection) OR (inflammation)))"}
{"candidate_id": "LLM00921", "doc_id": "NCT03376763_inc", "case_bucket": "or", "source_criterion": "Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week). Male and female aged =19 and < 65 years. Subjects diagnosed of schizophrenia as defined by Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria, and a history of illness for at least for 3 years prior to screening. Subjects who take atypical antipsychotic drugs, and should be maintained on current antipsychotic drugs (including atypical antipsychotic drugs) and dose for at least 4 weeks prior to the screening. Subjects who need antipsychotic treatment (other than clozapine), and would be stable when switching to long-acting injectable aripiprazole in the investigator's judgement. Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.", "candidate_expression": "((=19 and < 65 years) AND (Diagnostic and Statistical Manual of Mental Disorders, 4th edition text revision or 5th edition (DSM-<U+2163>-TR or 5) criteria) AND (Subjects must be capable of providing signed and dated written informed consent by date of Visit 0 (-2 week).) AND (Subjects must exhibit willingness, physiologic capability, and an educational level sufficient to comply with all protocol procedures.) AND (aged) AND (atypical antipsychotic drugs) AND (for at least for 3 years) AND (history of illness) AND (prior to screening) AND (schizophrenia) AND ((Male) OR (female)))"}
{"candidate_id": "LLM00922", "doc_id": "NCT02620904_inc", "case_bucket": "other", "source_criterion": "Intrauterine fetal death as confirmed by absence of cardiac motion on ultrasound by Attending physician at the time of admission to the hospital. Estimated gestational age greater than 20 weeks Hemodynamically stable and appropriate for induction of labor as per primary clinical health team in house Women with one prior low transverse cesarean delivery", "candidate_expression": "((Estimated gestational age) AND (Hemodynamically stable) AND (Intrauterine fetal death) AND (Women) AND (absence of cardiac motion) AND (admission to the hospital) AND (at the time of admission to the hospital) AND (greater than 20 weeks) AND (induction of labor) AND (low transverse cesarean delivery) AND (one) AND (ultrasound))"}
{"candidate_id": "LLM00923", "doc_id": "NCT01184638_exc", "case_bucket": "other", "source_criterion": "With the history of cognitive disorders With chronic neurological disorders Cannot communicate with investigators Cannot stand general anesthesia", "candidate_expression": "((Cannot communicate) AND (Cannot stand) AND (chronic neurological disorders) AND (cognitive disorders) AND (general anesthesia))"}
{"candidate_id": "LLM00924", "doc_id": "NCT02859480_inc", "case_bucket": "other", "source_criterion": "Patients underwent percutaneous coronary intervention with drug-eluting stent;", "candidate_expression": "((drug-eluting stent) AND (percutaneous coronary intervention))"}
{"candidate_id": "LLM00925", "doc_id": "NCT01084993_inc", "case_bucket": "or", "source_criterion": "At least two of the following additional criteria At least 70 yrs old Female gender Diabetes Creatinine clearance <60mL/min History of gastro-intestinal or other organ bleeding Baseline anemia Current treatment with glycoproteins IIb-IIIa inhibitors", "candidate_expression": "((Creatinine clearance <60mL/min) AND (Diabetes) AND (Female) AND (anemia Baseline) AND (gastro-intestinal bleeding) AND (glycoproteins IIb-IIIa inhibitors) AND (old At least 70 yrs At least two) AND (organ bleeding other) AND (treatment Current))"}
```
