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
{"candidate_id": "LLM01676", "doc_id": "NCT02939209_exc", "case_bucket": "or", "source_criterion": "Allergy, sensitivity, or absolute contraindications to any of the medications involved in the study preexisting CNS depression, or taking regularly medication that cause CNS depression preexisting cognitive deficits, dementia, or delirium severe respiratory comorbidities (e.g. chronic obstructive pulmonary disease, pneumonia, respiratory failure) sleep disordered breathing (diagnosed OSA, obesity hypoventilation syndrome) pregnancy and breast feeding history of chronic pain or regular (at least once daily) opioid use preoperatively renal impairment - CrCl =60 mL/minute not fluent in English to be able to participate in the study process, including consent and phone interview Body Mass Index >35 inability to take oral medication.", "candidate_expression": "((=60 mL/minute) AND (>35) AND (Body Mass Index) AND (CrCl) AND (at least once daily) AND (inability) AND (medication) AND (medications) AND (not fluent in English to be able to participate in the study process, including consent and phone interview) AND (oral medication) AND (pregnancy and breast feeding) AND (preoperatively) AND (renal impairment) AND (respiratory comorbidities) AND (severe) AND (sleep disordered breathing) AND (study) AND ((Allergy) OR (contraindications) OR (sensitivity)) AND ((cognitive deficits) OR (delirium) OR (dementia)) AND ((chronic obstructive pulmonary disease) OR (pneumonia) OR (respiratory failure)) AND ((OSA) OR (obesity hypoventilation syndrome)) AND ((chronic pain) OR (opioid)) AND ((CNS depression)))"}
{"candidate_id": "LLM01677", "doc_id": "NCT02550769_exc", "case_bucket": "other", "source_criterion": "Do not sign informed consent Pregnant patients Liver cirrhosis Undifferentiated adenocarcinoma. cT4 Metastatic disease (M1) chronic renal failure on dialysis ASA IV BMI <18 and> 35 kg / m2", "candidate_expression": "((ASA IV) AND (BMI <18 and> 35 kg / m2) AND (Do not sign informed consent) AND (Liver cirrhosis) AND (Metastatic disease (M1)) AND (Pregnant) AND (adenocarcinoma Undifferentiated) AND (cT4) AND (chronic renal failure) AND (dialysis))"}
{"candidate_id": "LLM01678", "doc_id": "NCT02974660_exc", "case_bucket": "or", "source_criterion": "no consent periprocedural complications requiring continuation of heparin or administration of protamine sulfate alergy to fish, protamine, protamine derivates, history of Humulin N, Novolin N, Novolin NPH, Gensulin N, SciLin N, NPH Iletin II and isophane insulin intake", "candidate_expression": "((alergy) AND (no consent) AND (periprocedural complications) AND ((Gensulin N) OR (Humulin N) OR (NPH Iletin II) OR (Novolin N) OR (Novolin NPH) OR (SciLin N) OR (isophane insulin)) AND ((heparin) OR (protamine sulfate)) AND ((fish) OR (protamine) OR (protamine derivates)))"}
{"candidate_id": "LLM01679", "doc_id": "NCT03463564_exc", "case_bucket": "or", "source_criterion": "previous use of insulin pump pregnancy or planning to become pregnant in the next 2 years, lack of ability to use the study devices history of severe chronic diseases recent or concomitant use of corticosteroids drug or alcohol abuse psychiatric complaints that interfere with the correct use of the devices", "candidate_expression": "((ability to use the study devices) AND (alcohol abuse) AND (chronic diseases) AND (concomitant) AND (correct use of the devices) AND (corticosteroids) AND (drug abuse) AND (history) AND (in the next 2 years) AND (insulin pump) AND (interfere with) AND (lack of) AND (planning to become) AND (pregnancy) AND (pregnant) AND (psychiatric complaints) AND (recent) AND (severe) AND (study devices))"}
{"candidate_id": "LLM01680", "doc_id": "NCT02884401_inc", "case_bucket": "or", "source_criterion": "Participants must present a diagnosis of osteoporosis based on DXA measurement of the bone mineral density at the femur neck and/or total hip and/or lumbar spine (T value 2.5 SD or more below the young female adult mean) within the past 24 months. Not in treatment with anti-resorptive agents (like bisphosphonates and denosumab) for more than 4 consecutive years, in order to reduce the risk of medication-related osteonecrosis of the jaws (Lo et al., 2010). = 50 years old. In self-reported menopause, defined as the permanent cessation of ovulation, for at least one year (Soules et al., 2001). Edentulous area involving a maximum of two teeth (wisdom teeth and second molars are excluded) and presenting at least one neighbouring tooth (e.g. gap in the area of a second premolar and first molar, with first premolar in place). Residual alveolar width = 4 mm (Milinkovic and Cordaro, 2014), residual alveolar height >8 mm, enough inter-arch space for a crown (at least 5 mm) and a minimum distance of 7 mm from the adjacent teeth (Shah and Lum, 2008). The width and height will be confirmed after x-ray examination in Visit 2. Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth). Willingness to replace the missing tooth/teeth with dental implants Registration with a GDP", "candidate_expression": "((DXA) AND (Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth)) AND (Residual alveolar width = 4 mm) AND (T value 2.5 SD or more below the young female adult mean) AND (Willingness to replace the missing tooth/teeth with dental implants) AND (bone mineral density) AND (cessation of ovulation permanent) AND (menopause at least one year) AND (old = 50 years) AND (osteoporosis past 24 months) AND (residual alveolar height >8 mm) AND NOT (anti-resorptive agents more than 4 consecutive years,) AND ((bisphosphonates) OR (denosumab)) AND ((femur neck) OR (lumbar spine) OR (total hip)))"}
{"candidate_id": "LLM01681", "doc_id": "NCT01373684_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B (HBsAg positive > 6 months) HBeAg negative within six months prior to initiation of peginterferon alfa-2a HBV DNA < 200 IU/ml during nucleos(t)ide analogue (except Telbivudine) treatment within one month prior to initiation of peginterferon alfa-2a Compensated liver disease Age > 18 years Written informed consent", "candidate_expression": "((Age > 18 years) AND (Chronic hepatitis B) AND (HBV DNA < 200 IU/ml during nucleos(t)ide analogue (except Telbivudine) treatment within one month prior to initiation of peginterferon alfa-2a) AND (HBeAg negative within six months prior to initiation of peginterferon alfa-2a) AND (HBsAg positive > 6 months) AND (Written informed consent) AND (liver disease Compensated) AND (nucleos(t)ide analogue) AND (peginterferon alfa-2a) AND NOT (Telbivudine))"}
{"candidate_id": "LLM01682", "doc_id": "NCT02675153_exc", "case_bucket": "or", "source_criterion": "Allergic to sirolimus or serious side effects Need emergency surgery Accompanied with other severe disease (involve C.diff infection) Follow-up less than 1 year", "candidate_expression": "((C.diff infection) AND (Follow-up less than 1 year) AND (emergency surgery Need) AND (severe disease) AND (sirolimus) AND ((Allergic) OR (side effects serious)))"}
{"candidate_id": "LLM01683", "doc_id": "NCT02630628_exc", "case_bucket": "or", "source_criterion": "Renal disease unrelated to SLE (e.g. diabetes mellitus, other glomerular or tubulointerstitial disease, renovascular disease), or transplanted kidney. Estimated glomerular filtration rate (eGFR by MDRD) =20 mL/min per 1.73 m2 or serum creatinine >300 micromol/L (3.39 mg/dL) at screening. Renal biopsy showing cellular or fibrocellular crescent in more than 25% of glomeruli. CNS or other severe organ manifestation of lupus that necessitate aggressive immunosuppressive therapy on its own. Co-morbidities that require corticosteroid therapy (e.g. asthma, inflammatory bowel disease). Treatment with prednisolone (or prednisone, or equivalent) at >20 mg/D for over 4 weeks within the past 3 months. Treatment with MMF at >1.5 g/D for over 4 weeks within the past 3 months. Known hypersensitivity or intolerability to prednisolone (or prednisone, or equivalent), TAC, or MMF at a dose of 1.25 g or below per day. Subjects who are already on treatment with TAC, cyclosporine or any other calcineurin inhibitor for over 4 weeks within the past 12 months. Treatment with cyclophosphamide, leflunomide, or methotrexate for over 2 weeks, or use of biological agent(s) regardless of duration, within the past 6 months (Note: prior use of azathioprine, mizoribine, intravenous immunoglobulins and anti-malarials is allowed). Uncontrolled hypertension with systolic BP >160 mmHg or diastolic BP >95 mmHg. Women who are pregnant or breastfeeding. Women with childbearing potential or their male partners, who refuse to use an effective birth control method", "candidate_expression": "((Co-morbidities) AND (Estimated glomerular filtration rate =20 mL/min per 1.73 m2) AND (MMF 1.25 g or below per day) AND (MMF >1.5 g/D for over 4 weeks past 3 months) AND (Renal biopsy) AND (Renal disease) AND (TAC) AND (Women who are pregnant or breastfeeding) AND (Women with childbearing potential or their male partners, who refuse to use an effective birth control method) AND (anti-malarials) AND (asthma) AND (azathioprine) AND (biological agent) AND (calcineurin inhibitor) AND (cellular crescent CNS) AND (corticosteroid therapy) AND (cyclophosphamide) AND (cyclosporine) AND (diabetes mellitus) AND (diastolic BP >95 mmHg) AND (eGFR) AND (fibrocellular crescent) AND (glomerular disease) AND (hypersensitivity) AND (hypertension Uncontrolled) AND (immunoglobulins) AND (immunosuppressive therapy) AND (inflammatory bowel disease) AND (intolerability) AND (leflunomide) AND (lupus organ manifestation) AND (methotrexate) AND (mizoribine) AND (prednisolone) AND (prednisone) AND (prednisone equivalent) AND (renovascular disease) AND (serum creatinine >300 micromol/L 3.39 mg/dL) AND (systolic BP >160 mmHg) AND (transplanted kidney) AND (tubulointerstitial disease) AND NOT (SLE))"}
{"candidate_id": "LLM01684", "doc_id": "NCT01064752_exc", "case_bucket": "or", "source_criterion": "1. Taking a tetracycline within 6 months or history of adverse reaction to minocycline or another tetracycline. 2. Enhanced risk from lumbar puncture, including documented or suspected cerebral mass lesion predisposing to brain herniation or bleeding diathesis. 3. Pregnancy or expectation of pregnancy during the study. 4. Active opportunistic infection or active neurological disease that might confound evaluation. 5. ADC Stage > 1. 6. Hemoglobin < 10 Gms/dL. 7. BUN or creatine above the normal limits. 8. Taking other drugs known to reduce the metabolism of minocycline and thus increase the probability of toxicity.", "candidate_expression": "((ADC Stage > 1) AND (Hemoglobin < 10 Gms/dL) AND (adverse reaction history) AND (cerebral mass lesion predisposing to brain herniation or bleeding diathesis) AND (lumbar puncture Enhanced risk) AND (minocycline) AND (opportunistic) AND (tetracycline within 6 months) AND ((bleeding diathesis) OR (brain herniation)) AND ((documented) OR (suspected)) AND ((Pregnancy) OR (pregnancy expectation)) AND ((neurological disease active) OR (opportunistic infection Active)) AND ((BUN) OR (creatine)) AND ((minocycline) OR (tetracycline)))"}
{"candidate_id": "LLM01685", "doc_id": "NCT02790593_inc", "case_bucket": "or", "source_criterion": "Age >18 years old 1cm squared surface area Venous incompetence confirmed by clinical assessment and duplex ultrasound scan No evidence of arterial disease (Arterial Duplex or Ankle Brachial Pressure Index >0.9) Patients able to complete trial procedures Patients with a life expectancy of greater than 1 year", "candidate_expression": "((Age >18 years old) AND (Patients able to complete trial procedures) AND (Venous incompetence) AND (clinical assessment) AND (duplex ultrasound scan) AND (life expectancy greater than 1 year) AND (surface area 1cm squared) AND NOT (arterial disease) AND ((Ankle Brachial Pressure Index >0.9) OR (Arterial Duplex)))"}
{"candidate_id": "LLM01686", "doc_id": "NCT02734173_inc", "case_bucket": "other", "source_criterion": "HCV RNA evidence of HCV infection Documented history of chronic HCV RNA infection with Genotype 1 Able to provide informed consent Available for ongoing follow-up if required", "candidate_expression": "((Able to provide informed consent) AND (Available for ongoing follow-up if required) AND (Genotype 1) AND (HCV RNA) AND (HCV infection) AND (chronic HCV infection))"}
{"candidate_id": "LLM01687", "doc_id": "NCT01082549_exc", "case_bucket": "or", "source_criterion": "1. Prior treatment with gemcitabine, carboplatin (except in the adjuvant setting), or Iniparib. 2. Past or current history of neoplasm other than the entry diagnosis, with the exception of treated non-melanoma skin cancer or carcinoma in-situ of any primary site, or invasive cancers treated definitively, with treatment ending >5 years previously and no evidence of recurrences. 3. A history of cardiac disease, as defined by: Malignant hypertension Unstable angina Congestive heart failure Myocardial infarction within the previous 6 months Symptomatic, unstable or uncontrolled, cardiac arrhythmias. Patients who have stable, rate-controlled atrial fibrillation are eligible for study enrollment. 4. Active brain metastases. Patients with treated brain metastases are eligible, if (1) radiation therapy was completed at least 2 weeks prior to study entry; (2) follow-up scan shows no disease progression; and (3) patient does not require steroids. 5. Women who are pregnant or lactating. 6. Any serious, active infection (> Grade 2) at the time of treatment. 7. A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment. 8. A major surgical procedure, or significant traumatic injury ≤28 days of beginning treatment, or anticipation of the need for major surgery during the course of the study. 9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 10. History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 11. Known or suspected allergy/hypersensitivity to any agent given in the course of this trial. The above information is not intended to contain all considerations relevant to a patient's potential participation in a clinical trial.", "candidate_expression": "((9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (> Grade 2) AND (>5 years previously) AND (A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment.) AND (Active) AND (Congestive heart failure) AND (History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (Known or suspected allergy/hypersensitivity to any agent given in the course of this trial) AND (Malignant hypertension) AND (Myocardial infarction) AND (Prior) AND (Unstable angina) AND (Women) AND (Women who are pregnant or lactating) AND (active) AND (agent given in the course of this trial) AND (are eligible) AND (at least 2 weeks prior to study entry) AND (atrial fibrillation) AND (beginning treatment) AND (brain metastases) AND (cardiac arrhythmias) AND (cardiac disease) AND (disease progression) AND (during the course of the study) AND (entry diagnosis) AND (evidence of recurrences) AND (follow-up scan) AND (history) AND (illness) AND (impair the ability of the patient to receive protocol treatment) AND (in the opinion of the investigator may increase the risks) AND (infection) AND (invasive) AND (laboratory) AND (major) AND (medical condition) AND (need for) AND (neoplasm) AND (no) AND (not) AND (other than the entry diagnosis) AND (radiation therapy) AND (rate-controlled) AND (require) AND (serious) AND (significant) AND (stable) AND (steroids) AND (study entry) AND (the course of the study) AND (treated) AND (treated definitively) AND (with the exception of) AND (within the previous 6 months) AND (would) AND (≤28 days of beginning treatment) AND ((allergy) OR (hypersensitivity)) AND ((Known) OR (suspected)) AND ((cancers) OR (carcinoma in-situ) OR (non-melanoma skin cancer)) AND ((Past) OR (current)) AND ((Iniparib) OR (carboplatin) OR (gemcitabine)) AND ((Symptomatic) OR (uncontrolled) OR (unstable)) AND ((lactating) OR (pregnant)) AND ((major surgery) OR (surgical procedure) OR (traumatic injury)) AND ((Uncontrolled) OR (intercurrent)) AND ((laboratory abnormality) OR (psychiatric condition)))"}
{"candidate_id": "LLM01688", "doc_id": "NCT02643381_inc", "case_bucket": "or", "source_criterion": "Adult patient (male or female) requiring emergency endotracheal intubation.", "candidate_expression": "((Adult) AND (emergency endotracheal intubation) AND (female) AND (male))"}
{"candidate_id": "LLM01689", "doc_id": "NCT02364648_exc", "case_bucket": "other", "source_criterion": "History of cardiovascular disease; Current pregnancy; Uncontrolled hypertension; Uncontrolled hyperlipidemia; Current hormone replacement therapy; Current use of tobacco products; Elevated liver enzymes; Current autoimmune disease; Daily use of of antioxidants >300mg", "candidate_expression": "((>300mg) AND (Current) AND (Daily use) AND (Elevated liver enzymes) AND (History) AND (Uncontrolled) AND (antioxidants) AND (autoimmune disease) AND (cardiovascular disease) AND (hormone replacement therapy) AND (hyperlipidemia) AND (hypertension) AND (pregnancy) AND (use of tobacco products))"}
{"candidate_id": "LLM01690", "doc_id": "NCT03228498_exc", "case_bucket": "or", "source_criterion": "1. Absence of objectionable cognitive impairment or presence of dementia of severe degree defined by CDR score > 2.0. 2. Unavailability of brain MRI (in case of absolute contraindications, the use of cranial CT is allowed). 3. Expected poor compliance with the study protocol. 4. Past diagnosis of major depression, schizophrenia, major anxiety syndrome, or manic- depressive illness. 5. Diagnosis of degenerative cognitive impairment based on clinical and/or neuroradiological findings (i.e., patients with prevailing memory impairment, or with medial temporal atrophy on brain MRI in absence of evident vascular abnormalities; i.e., Alzheimer disease as defined using the National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria, Parkinson disease, Huntington disease, frontotemporal dementia). 6. Diagnosis of cognitive impairment from other causes (i.e., vitamine B12 and folic acid deficiency, thyroid disorders, metabolic diseases, head trauma, tumor or infections of the central nervous system, normal pressure hydrocephalus). 7. Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status. 8. Clinically relevant cardiac or pulmonary insufficiency. 9. Relevant electrocardiograph abnormalities; bradycardia (50 bpm) or tachycardia (120 bpm) under resting conditions. 10. Myocardial infarction within the past 6 months. 11. Stroke still requiring neurological rehabilitation. 12. Severe/untreated blood pressure (systolic 180 mm Hg, diastolic 95 mm Hg). 13. Clinically relevant liver function impairment. 14. Insulin-dependent diabetes mellitus. 15. Idiopathic epilepsy and anti-epileptic treatment. 16. Severe anemia (Hb <10 mg/dL). 17. Severe gastrointestinal disease. 18. Cancer. 19. Known intolerance to study drugs. 20. Coexistent serious illnesses that would imply a drop-out before the end of the trial.", "candidate_expression": "((120 bpm) AND (180 mm Hg) AND (50 bpm) AND (95 mm Hg) AND (<10 mg/dL) AND (> 2.0) AND (Absence) AND (CDR score) AND (Cancer) AND (Clinically relevant) AND (Hb) AND (Idiopathic epilepsy) AND (Insulin-dependent diabetes mellitus) AND (Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status.) AND (Myocardial infarction) AND (National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria) AND (Past diagnosis) AND (Relevant) AND (Severe) AND (Stroke) AND (Unavailability) AND (abnormalities) AND (absence) AND (absolute contraindications) AND (anemia) AND (anti-epileptic treatment) AND (blood pressure) AND (brain MRI) AND (clinical and/or neuroradiological findings) AND (cognitive impairment) AND (degenerative cognitive impairment) AND (diastolic) AND (electrocardiograph) AND (evident) AND (gastrointestinal disease) AND (intolerance) AND (liver function impairment) AND (neurological rehabilitation) AND (objectionable) AND (other causes) AND (requiring) AND (severe degree) AND (study drugs) AND (systolic) AND (under resting conditions) AND (vascular abnormalities) AND (within the past 6 months) AND ((Severe) OR (untreated)) AND ((cognitive impairment) OR (dementia)) AND ((brain MRI) OR (cranial CT)) AND ((major anxiety syndrome) OR (major depression) OR (manic- depressive illness) OR (schizophrenia)) AND ((medial temporal atrophy) OR (memory impairment)) AND ((Alzheimer disease) OR (Huntington disease) OR (Parkinson disease) OR (frontotemporal dementia)) AND ((folic acid deficiency) OR (head trauma) OR (infections of the central nervous system) OR (metabolic diseases) OR (normal pressure hydrocephalus) OR (thyroid disorders) OR (tumor of the central nervous system) OR (vitamine B12 deficiency)) AND ((cardiac insufficiency) OR (pulmonary insufficiency)) AND ((bradycardia) OR (tachycardia)))"}
{"candidate_id": "LLM01691", "doc_id": "NCT02816164_exc", "case_bucket": "other", "source_criterion": "Contraindication to Filgrastim", "candidate_expression": "((Contraindication) AND (Filgrastim))"}
{"candidate_id": "LLM01692", "doc_id": "NCT03372265_inc", "case_bucket": "or", "source_criterion": "Age = 18 years American Society of Anesthesiologists Classification I-III Normal cognitive function in order to sign written, informed consent and to understand trial protocol Agreement to the trial protocol, including the randomized manner", "candidate_expression": "((Age = 18 years) AND (American Society of Anesthesiologists Classification I-III) AND (cognitive function Normal) AND ((Agreement to the randomized manner) OR (Agreement to the trial protocol)))"}
{"candidate_id": "LLM01693", "doc_id": "NCT03113253_inc", "case_bucket": "or", "source_criterion": "Subjects undergoing burn excision surgery for standard of care purposes Male or female >= 18 years of age Subject or subject's medical decision maker agrees to participate in this study and provides informed consent", "candidate_expression": "((>= 18 years) AND (Subject or subject's medical decision maker agrees to participate in this study and provides informed consent) AND (age) AND (burn excision surgery) AND (undergoing) AND ((Male) OR (female)))"}
{"candidate_id": "LLM01694", "doc_id": "NCT03305666_exc", "case_bucket": "or", "source_criterion": "Allergy or hypersensitivity to bupivacaine Pregnancy Incarceration Age < 18 years Indwelling continuous thoracic epidural analgesia", "candidate_expression": "((< 18 years) AND (Age) AND (Incarceration) AND (Indwelling) AND (Pregnancy) AND (bupivacaine) AND (continuous) AND (thoracic epidural analgesia) AND ((Allergy) OR (hypersensitivity)))"}
{"candidate_id": "LLM01695", "doc_id": "NCT02106598_exc", "case_bucket": "or", "source_criterion": "Known pregnancy or breast-feeding. Medical illness unrelated to the tumor which in the opinion of the attending physician and principal investigator will preclude administration of the agent. This includes patients with uncontrolled infection, chronic renal insufficiency, myocardial infarction within the past 6 months, unstable angina, cardiac arrhythmias other than chronic atrial fibrillation and chronic active or persistent hepatitis, or New York Heart Association Classification III or IV heart disease.", "candidate_expression": "((Medical illness unrelated to the tumor) AND (New York Heart Association Classification III or IV) AND (which in the opinion of the attending physician and principal investigator will preclude administration of the agent) AND ((cardiac arrhythmias) OR (chronic renal insufficiency) OR (myocardial infarction within the past 6 months) OR (uncontrolled infection) OR (unstable angina)) AND ((breast-feeding) OR (pregnancy)) AND ((chronic active hepatitis) OR (heart disease) OR (persistent hepatitis) OR NOT (chronic atrial fibrillation)))"}
{"candidate_id": "LLM01696", "doc_id": "NCT02062489_inc", "case_bucket": "or", "source_criterion": "The patients signed the written informed consent The patients present with operable unilateral invasive breast cancers without distant metastasis(stage I, II, and III) The breast tumor's positive ER/PR rate is <1%, and positive ER-beta1 rate is =10% by IHC. The patients have no history of neoadjuvant hormone therapy. The patients have normal cardiac functions by echocardiography. The patients' ECOG scores are =0-2. Female patient who is = 18yrs, and = 65yrs. The patients are non-pregnant, and disposed to practice contraception during the whole trial. The patients underwent neoadjuvant chemotherapy plus surgery or directly modified radical mastectomy or breast-conserving surgery (plus sentinel lymph node biopsy or axillary lymph node dissection) after diagnosis of breast cancer. The patients underwent chemotherapy, radiation therapy or targeted therapy(herceptin) after surgery according to the 2013 NCCN guideline. The results of patients' blood tests are as follows:", "candidate_expression": "((ECOG scores =0-2) AND (Female = 18yrs = 65yrs) AND (IHC) AND (The patients are non-pregnant, and disposed to practice contraception during the whole trial.) AND (breast cancers operable unilateral invasive) AND (breast tumor) AND (echocardiography) AND (herceptin) AND (neoadjuvant chemotherapy) AND (normal cardiac functions) AND (positive ER-beta1 rate =10%) AND (positive ER/PR rate <1%) AND (stage I, II, and III) AND (surgery) AND NOT (neoadjuvant hormone therapy) AND NOT (distant metastasis) AND ((breast-conserving surgery) OR (radical mastectomy directly modified)) AND ((axillary lymph node dissection) OR (sentinel lymph node biopsy)) AND ((chemotherapy) OR (radiation therapy) OR (targeted therapy)))"}
{"candidate_id": "LLM01697", "doc_id": "NCT02414399_inc", "case_bucket": "other", "source_criterion": "Age 1-59 months, Plan to remain in study area greater than 6 months Discharged from hospital following non-trauma related admission", "candidate_expression": "((Age 1-59 months) AND (Discharged from hospital) AND (hospital) AND (non-trauma related admission) AND (remain in study area Plan greater than 6 months))"}
{"candidate_id": "LLM01698", "doc_id": "NCT03096613_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older, male or female. Systolic heart failure with New York Heart Association (NYHA) class II-III. Left ventricular ejection fraction (LVEF) less than 40% by echocardiography during screening and randomization. SCH (TSH: upper limits of normal (ULN) -10mIU/L, and FT4 level within reference range). Having received standard HF therapy for at least 2 weeks, having reached target dose or max tolerable dose. Provided informed consent.", "candidate_expression": "((Aged 18 years or older) AND (FT4 level within reference range) AND (Left ventricular ejection fraction (LVEF) less than 40%) AND (New York Heart Association (NYHA) class II-III) AND (SCH) AND (Systolic heart failure) AND (TSH upper limits of normal (ULN) -10mIU/L) AND (echocardiography during screening and randomization) AND (female) AND (male) AND (standard HF therapy for at least 2 weeks target dose max tolerable dose))"}
{"candidate_id": "LLM01699", "doc_id": "NCT03305575_exc", "case_bucket": "or", "source_criterion": "Abdominal and complex cervical cerclage (e.g. bulging bag) Contraindication to neuraxial anesthesia Known hypersensitivity to chloroprocaine (a.k.a. Ester allergy), paraaminobenzoic acid (PABA) or bupivacaine (a.k.a. Amide allergy) Pseudocholinesterase deficiency Concomitant use with ergot-type oxytocic drugs", "candidate_expression": "((Abdominal) AND (Amide allergy) AND (Concomitant) AND (Contraindication) AND (Ester allergy) AND (PABA) AND (Pseudocholinesterase deficiency) AND (bulging bag) AND (cervical cerclage) AND (complex) AND (ergot-type oxytocic drugs) AND (hypersensitivity) AND (neuraxial anesthesia) AND ((bupivacaine) OR (chloroprocaine) OR (paraaminobenzoic acid)))"}
{"candidate_id": "LLM01700", "doc_id": "NCT02368743_inc", "case_bucket": "or", "source_criterion": "Patient aged 18 years or older. Patient suffering from mild to moderate active proctitis or distal proctosigmoiditis (MAYO score ≥ 3 and ≤ 10) at inclusion based on clinical and endoscopic findings within 6 months before study inclusion. Patient with evidence of endoscopic active proctitis or distal proctosigmoiditis (Montreal classification E1 or E2 defined by an involvement not exceeding 25 cm from the anal margin) within 6 months before study inclusion. Treatment of the current flare with Pentasa® to induce a remission initiated by the patient, the general practitioner or the gastroenterologist, during the inclusion visit or during the week before the inclusion visit. Patient having received oral and written information on the study, without any objections for the use of his/her personal data, and having signed a written Informed Consent Form.", "candidate_expression": "((18 years or older) AND (E1 or E2) AND (MAYO score) AND (Montreal classification) AND (Pentasa) AND (Treatment) AND (aged) AND (at inclusion) AND (endoscopic) AND (flare) AND (inclusion) AND (inclusion visit) AND (involvement not exceeding 25 cm from the anal margin) AND (mild to moderate) AND (study inclusion) AND (the week before the inclusion visit) AND (within 6 months before study inclusion) AND (≥ 3 and ≤ 10) AND ((during the inclusion visit) OR (during the week before the inclusion visit)) AND ((active proctitis) OR (distal proctosigmoiditis)))"}
```
