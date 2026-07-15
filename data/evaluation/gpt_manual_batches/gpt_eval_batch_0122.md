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
{"candidate_id": "LLM03026", "doc_id": "NCT02242188_exc", "case_bucket": "or", "source_criterion": "preterm delivery (<37 weeks of gestation) birth weight < 2500 g multiple pregnancy major illness or congenital anomaly being <50% breastfed at the time of inclusion food allergy anaemia (Hb <105 g/L [10.5 g/dL]) at inclusion, lack of informed consent", "candidate_expression": "((10.5 g/dL) AND (< 2500 g) AND (<105 g/L) AND (<37 weeks) AND (<50%) AND (Hb) AND (anaemia) AND (at inclusion) AND (at the time of inclusion) AND (birth weight) AND (breastfed) AND (food allergy) AND (gestation) AND (lack of informed consent) AND (multiple pregnancy) AND (preterm delivery) AND ((congenital anomaly) OR (major illness)))"}
{"candidate_id": "LLM03027", "doc_id": "NCT03561753_inc", "case_bucket": "or", "source_criterion": "Newly diagnosed and untreated sputum smear positive tuberculosis patient Pulmonary lesion consistent with TB by radiological examination Positive sputum culture, identification of bacterial type confirmed Mycobacterium tuberculosis. MGIT drug sensitivity test (DST) results are sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol). Age 18 years-65 years old Males or non-pregnant, non-nursing females Serum or plasma aminotransferases (AST, ALT) less than 3 times the upper limit of normal Serum or plasma total bilirubin less than or equal to 2.5 times the upper limit of normal Serum or plasma creatinine level less than or equal to 2 times the upper limit of normal Serum or plasma potassium level greater than or equal to 3.5 meq/L Hemoglobin level of 7.0 g/dL or greater Platelet count of 100,000/mm3 or greater For women of childbearing potential, a negative pregnancy test is required during screening Provides written informed consent Willingness and ability to attend scheduled follow-up visits and undergo study assessments.", "candidate_expression": "((100,000/mm3 or greater) AND (18 years-65 years old) AND (7.0 g/dL or greater) AND (ALT) AND (AST) AND (Age) AND (Hemoglobin level) AND (MGIT drug sensitivity test (DST)) AND (Males) AND (Mycobacterium tuberculosis) AND (Newly diagnosed) AND (Platelet count) AND (Positive) AND (Pulmonary lesion) AND (Serum) AND (Serum aminotransferases) AND (TB) AND (ability to attend scheduled follow-up visits) AND (ability to undergo study assessments) AND (bacterial type) AND (childbearing potential) AND (consistent with TB) AND (creatinine level) AND (during screening) AND (ethambutol) AND (females) AND (first-line drugs) AND (greater than or equal to 3.5 meq/L) AND (isoniazid) AND (less than 3 times the upper limit of normal) AND (less than or equal to 2 times the upper limit of normal) AND (less than or equal to 2.5 times the upper limit of normal) AND (negative) AND (non-) AND (nursing) AND (plasma) AND (plasma aminotransferases) AND (positive) AND (potassium level) AND (pregnancy test) AND (pregnant) AND (radiological examination) AND (rifampicin) AND (screening) AND (sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol)) AND (sputum culture) AND (sputum smear) AND (streptomycin) AND (to attend scheduled follow-up visits Willingness) AND (to undergo study assessments Willingness) AND (total bilirubin) AND (tuberculosis) AND (untreated) AND (women) AND (written informed consent))"}
{"candidate_id": "LLM03028", "doc_id": "NCT02477280_exc", "case_bucket": "or", "source_criterion": "Affected by alcohol or drugs during the last month. Untreated severe comorbid psychiatric or somatic illness. Bloodpressure 150/95 or higher. Irregular pulse, or pulse 100 or higher. No counter indications according to the Medikinet pill. Concurrent clinical diagnosis that significantly could affect test performance. Concurrent prescription of medicines for ADHD or medicines that significantly could affect test performance.", "candidate_expression": "((ADHD) AND (Bloodpressure 150/95 or higher Untreated severe comorbid) AND (medicines) AND ((alcohol) OR (drugs)) AND ((pulse 100 or higher) OR (pulse Irregular)) AND ((illness psychiatric) OR (somatic illness)))"}
{"candidate_id": "LLM03029", "doc_id": "NCT02340169_inc", "case_bucket": "or", "source_criterion": "Patients aged 7 years and older must have provided written assent accompanied by written informed consent from patient's representative Clinical diagnosis of stable plaque psoriasis with involvement of = 10% body surface area (excluding face and scalp) Physicians Global Assessment score of 3 or 4 at baseline", "candidate_expression": "((7 years and older) AND (= 10%) AND (Physicians Global Assessment score) AND (aged) AND (at baseline) AND (body surface area) AND (excluding) AND (must have provided written assent accompanied by written informed consent from patient's representative) AND (plaque psoriasis) AND (stable) AND ((3) OR (4)) AND ((face) OR (scalp)))"}
{"candidate_id": "LLM03030", "doc_id": "NCT02566863_inc", "case_bucket": "other", "source_criterion": "patients classified with American Society of Anesthesiologists Physical Status Classification System as 1 or 2 status planned eye surgery under sedation", "candidate_expression": "((1 or 2) AND (eye surgery) AND (planned) AND (sedation) AND (status American Society of Anesthesiologists Physical Status Classification System) AND (under sedation))"}
{"candidate_id": "LLM03031", "doc_id": "NCT02668016_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older Previously taken one or more statins Withdrawn from statins because of perceived side effects Developed side effects within 2 weeks of initiation Clinical indication for statins for primary or secondary prevention of cardiovascular disease or dyslipidaemia, on either no medication or non-statin lipid lowering therapy (e.g, ezetimibe)", "candidate_expression": "((18 years or older) AND (Aged) AND (dyslipidaemia) AND (indication) AND (initiation) AND (one or more) AND (prevention of cardiovascular disease) AND (primary) AND (secondary) AND (side effects) AND (statins) AND (within 2 weeks of initiation))"}
{"candidate_id": "LLM03032", "doc_id": "NCT02426034_inc", "case_bucket": "or", "source_criterion": "Age: 18 to75 years old; Pathologically diagnosed with advanced gastric cancer (including adenocarcinoma of the gastroesophageal junction) with measurable metastases outside the stomach (measuring = 10mm on spiral CT scan, satisfying the criteria in RECIST 1.1); Failure of prior therapy (during or after treatment) in patients who have received at least two prior chemotherapy regimens; ECOG PS of 0-2; HB = 90g / L ANC = 1.5 × 109 / L PLT = 80 × 109 / L Bilirubin <1.25 times the upper limit of normal (ULN) ALT and AST <2.5 × ULN; liver metastases, if any, the ALT and AST<5 × ULN Serum Cr = 1 × ULN endogenous creatinine clearance>50ml/min (Cockcroft-Gault formula) An expected survival of = 3 months; Patient received apatinib treatment regimen at investigators' discretion; Patient has to voluntarily join the study and sign the Informed Consent Form for the study; Pregnancy test (serum or urine) has to be performed for woman of childbearing age within 7 days before enrolment and the test result must be negative. They shall take appropriate methods for contraception during the study until the 8th week post the last administration of study drug. For men, (previous surgical sterilization accepted), shall agree to take appropriate methods of contraception during the study until the 8th week post the last administration of study drug.", "candidate_expression": "((0-2) AND (18 to75 years old) AND (<1.25 times the upper limit of normal) AND (<2.5 × ULN) AND (<5 × ULN) AND (= 1 × ULN) AND (= 1.5 × 109 / L) AND (= 3 months) AND (= 80 × 109 / L) AND (= 90g / L) AND (>50ml/min) AND (ALT) AND (ANC) AND (AST) AND (Age) AND (Bilirubin) AND (ECOG PS) AND (Failure) AND (HB) AND (PLT) AND (Patient has to voluntarily join the study and sign the Informed Consent Form for the study;) AND (Pregnancy test (serum or urine) has to be performed for woman of childbearing age within 7 days before enrolment and the test result must be negative. They shall take appropriate methods for contraception during the study until the 8th week post the last administration of study drug. For men, (previous surgical sterilization accepted), shall agree to take appropriate methods of contraception during the study until the 8th week post the last administration of study drug) AND (adenocarcinoma) AND (apatinib) AND (at least two) AND (chemotherapy) AND (expected survival) AND (gastroesophageal junction) AND (liver metastases) AND (outside) AND (stomach) AND ((advanced gastric cancer) OR (metastases)) AND ((Serum Cr) OR (endogenous creatinine clearance)))"}
{"candidate_id": "LLM03033", "doc_id": "NCT02566226_exc", "case_bucket": "other", "source_criterion": "planned surgical duration more than 3 hours contraindication to spinal anaesthesia severe respiratory disease patient known and treated for sleep apnea syndrome", "candidate_expression": "((contraindication) AND (planned surgical duration more than 3 hours) AND (respiratory disease severe) AND (sleep apnea syndrome) AND (spinal anaesthesia) AND (treated))"}
{"candidate_id": "LLM03034", "doc_id": "NCT00749112_exc", "case_bucket": "or", "source_criterion": "Current viral or bacterial infection. Positive serology for HIV, HCV, HBV.", "candidate_expression": "((Current) AND (Positive) AND (bacterial infection) AND (infection viral) AND (serology for HBV) AND (serology for HCV) AND (serology for HIV))"}
{"candidate_id": "LLM03035", "doc_id": "NCT02254668_inc", "case_bucket": "other", "source_criterion": "Patients with heart transplantation Patient with coronary artery disease Age between 18 and 80 years", "candidate_expression": "((Age between 18 and 80 years) AND (coronary artery disease) AND (heart transplantation))"}
{"candidate_id": "LLM03036", "doc_id": "NCT02256943_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03037", "doc_id": "NCT01501201_exc", "case_bucket": "other", "source_criterion": "Contraindication to bariatric surgery Pregnancy Affiliation of health care assurance Psychiatric disorders", "candidate_expression": "((Affiliation of health care assurance) AND (Contraindication) AND (Pregnancy) AND (Psychiatric disorders) AND (bariatric surgery))"}
{"candidate_id": "LLM03038", "doc_id": "NCT03477851_inc", "case_bucket": "other", "source_criterion": "Patients with foot fracture scheduled for surgical repair in spinal anesthesia Informed consent", "candidate_expression": "((Informed consent) AND (foot fracture) AND (spinal anesthesia) AND (surgical repair scheduled for))"}
{"candidate_id": "LLM03039", "doc_id": "NCT02195024_exc", "case_bucket": "or", "source_criterion": "Pacing threshold(s) (at 0.4 or 0.5 ms) and/or sensing amplitude(s) and/or impedance(s) are not measurable Meet one or more of the contraindications for MRI including Psychiatric disorders, anxiety, claustrophobia Cardiac disorders that represent a contraindication to MRI Cardiac surgery already scheduled in the next three months Have other medical implants that may interact with MRI, e.g. abandoned implantable cardioverter defibrillator (ICD) leads or pacemaker leads other than MRI conditional, lead extensions, other active medical devices, non-MRI compatible devices, mechanical valve Have other metallic artifacts/components in body that may interact with MRI Subjects for whom a single dose of 1.0 milligram (mg) dexamethasone acetate may be contraindicated Subjects who require a legally authorized representative to obtain consent Subjects who are immediate candidates for an ICD Subjects with medical conditions that preclude the testing required by the protocol or limit study participation Subjects who are enrolled or intend to participate in another clinical trial (of an investigational drug or device, new indication for an approved drug or device, or requirement of additional testing beyond standard clinical practice) during this clinical study Being pregnant Have a life expectancy of less than three months Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)", "candidate_expression": "((Cardiac disorders) AND (Cardiac surgery scheduled in the next three months) AND (ICD immediate candidates for) AND (MRI) AND (Pacing threshold at 0.4 or 0.5 ms) AND (Psychiatric disorders) AND (Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)) AND (abandoned implantable cardioverter defibrillator (ICD) leads) AND (active medical devices other) AND (anxiety) AND (claustrophobia) AND (contraindicated) AND (contraindication) AND (contraindications one or more) AND (dexamethasone acetate single dose of 1.0 milligram (mg)) AND (impedance) AND (interact) AND (interact with MRI) AND (lead extensions) AND (life expectancy less than three months) AND (limit study participation) AND (mechanical valve) AND (medical conditions) AND (medical implants) AND (metallic artifacts) AND (metallic components) AND (non-MRI compatible devices) AND (not measurable) AND (pacemaker leads) AND (preclude) AND (pregnant) AND (sensing amplitude) AND (testing required by the protoco) AND NOT (MRI conditional))"}
{"candidate_id": "LLM03040", "doc_id": "NCT03446885_inc", "case_bucket": "or", "source_criterion": "diagnosis of ADHD parental permission and/or teen consent/assent as appropriate between 16-25 years of age IQ greater than or equal to 70 permit or license to drive ability to read and understand English", "candidate_expression": "((ADHD) AND (IQ greater than or equal to 70) AND (ability to read English) AND (ability to understand English) AND (age 16-25 years) AND (license to drive) AND (parental permission and/or teen consent/assent as appropriate) AND (permit to drive))"}
{"candidate_id": "LLM03041", "doc_id": "NCT02982577_inc", "case_bucket": "other", "source_criterion": "Age equal or superior to 18 years; Both genders; Lucid and without diagnosis of any psychiatric disorder; Diagnosed with head and neck cancer and treated for a period of up to 5 years with radiotherapy where the major salivary glands (parotid, submandibular and sublingual) were included in the radiation field; Primary Sjögren's syndrome with the diagnosis made by the American-European criteria.", "candidate_expression": "((Age equal or superior to 18 years) AND (Lucid) AND (Primary Sjögren's syndrome American-European criteria) AND (genders) AND (head and neck cancer 5 years) AND (radiotherapy major salivary glands parotid submandibular sublingual) AND NOT (psychiatric disorder))"}
{"candidate_id": "LLM03042", "doc_id": "NCT00787254_inc", "case_bucket": "or", "source_criterion": "The patient was on nonsteroid anti-inflammatory drug (NSAID) treatment on the day when consent was obtained, and requires the long-term continuous treatment even after treatment with the investigational drug is started. The patient was confirmed to have a history of gastric ulcer or duodenal ulcer.", "candidate_expression": "((consent) AND (nonsteroid anti-inflammatory drug (NSAID) on the day when consent was obtained) AND ((duodenal ulcer) OR (gastric ulcer)))"}
{"candidate_id": "LLM03043", "doc_id": "NCT00183885_inc", "case_bucket": "other", "source_criterion": "Unresectable, histologically confirmed hepatocellular carcinoma with evident disease limited to liver. Tissue from tumor must be available. This may be paraffin embedded tissue from previous biopsy/resection or if it is not available, a repeat biopsy must be performed. The requirement for biopsy may be waived if alpha-fetoprotein is greater than 500 ng/mL and in the investigators opinion not explained by a concurrent hepatic inflammatory process. Patients must agree to have a 20 cc blood sample drawn in addition to routine labs with each cycle of chemotherapy. Patients must have measurable disease. If prior radiation therapy was administered, measurable disease must be outside the radiation field. Patients must have a Zubrod performance status of 0-2. Patients must have a predicted life expectancy of at least 12 weeks. Patients must have a pre-treatment granulocyte count (i.e., segmented neutrophils + bands) of greater than or equal to 1,500/mm3, a hemoglobin level of greater than or equal to 9 gm/dl, and platelet count greater than or equal to 50,000/mm3. The granulocyte requirement may be waived if in the investigator's opinion the lower count reflects hypersplenism with adequate bone marrow reserves. Patients must have adequate renal function as documented by a calculated creatinine clearance ≥ 60. Patients must have adequate hepatic function as documented by a serum bilirubin less than or equal to 2x the institutional upper limit of normal, regardless of whether patients have liver involvement secondary to tumor. Patients may not have ascites or the ascites must be responsive to diuretics.", "candidate_expression": "((Zubrod performance status 0-2) AND (agree to) AND (alpha-fetoprotein greater than 500 ng/mL) AND (ascites responsive to diuretics) AND (biopsy) AND (blood sample drawn 20 cc) AND (calculated creatinine clearance ≥ 60) AND (granulocyte count greater than or equal to 1,500/mm3) AND (hemoglobin level greater than or equal to 9 gm/dl) AND (hepatic function adequate) AND (hepatocellular carcinoma Unresectable disease limited to liver) AND (histologically confirmed) AND (platelet count greater than or equal to 50,000/mm3) AND (predicted life expectancy at least 12 weeks) AND (radiation therapy measurable disease measurable disease) AND (renal function adequate) AND (routine labs) AND (segmented neutrophils + bands) AND (serum bilirubin less than or equal to 2x the institutional upper limit of normal) AND NOT (ascites))"}
{"candidate_id": "LLM03044", "doc_id": "NCT02830360_inc", "case_bucket": "or", "source_criterion": "Prior Myocardial Infarction and Sustained monomorphic VT documented on 12-lead ECG or rhythm strip terminated by pharmacologic means or DC cardioversion =3 episodes of VT treated with antitachycardia pacing (ATP), at least one of which was symptomatic = 5 episodes of VT treated with antitachycardia pacing (ATP) regardless of symptoms =1 appropriate ICD shocks, =3 VT episodes within 24 hours", "candidate_expression": "((3 episodes) AND (5 episodes) AND (=1) AND (ATP) AND (ICD shocks) AND (Myocardial Infarction) AND (Sustained) AND (VT) AND (antitachycardia pacing) AND (at least one) AND (monomorphic VT) AND (symptomatic) AND (within 24 hours) AND ((12-lead ECG) OR (rhythm strip)) AND ((DC cardioversion) OR (pharmacologic means)))"}
{"candidate_id": "LLM03045", "doc_id": "NCT02510404_inc", "case_bucket": "or", "source_criterion": "1. Diagnosis of primary immunodeficiency with established plan to undergo myeloablative or non-myeloablative allogeneic hematopoietic stem cell transplant for treatment thereof or diagnosis of a form of primary immunodeficiency for which hematopoietic stem cell transplantation is not indicated. 2. Active infection with EBV, CMV, and/or Adenovirus, unable to be successfully controlled with standard therapy. 3. Steroids less than 0.5 mg/kg/day prednisone 4. Karnofsky/Lansky score of ≥ 50 5. ANC greater than 500/µL. 6. Bilirubin <2x, AST <3x, Serum creatinine <2x upper limit of normal, Hgb >8.0 7. Pulse oximetry of > 90% on room air 8. Negative pregnancy test (if female of childbearing potential) 9. Patient or parent/guardian capable of providing informed consent.", "candidate_expression": "((<2x) AND (<2x upper limit of normal) AND (<3x) AND (> 90%) AND (>8.0) AND (ANC) AND (AST) AND (Adenovirus) AND (Bilirubin) AND (CMV) AND (EBV) AND (Hgb) AND (Karnofsky/Lansky score) AND (Negative) AND (Patient or parent/guardian capable of providing informed consent) AND (Pulse oximetry on room air) AND (Serum creatinine) AND (Steroids) AND (allogeneic hematopoietic stem cell transplant myeloablative) AND (childbearing potential) AND (female) AND (greater than 500/µL) AND (hematopoietic stem cell transplantation) AND (less than 0.5 mg/kg/day) AND (non-myeloablative allogeneic hematopoietic stem cell transplant) AND (not indicated) AND (prednisone) AND (pregnancy test) AND (primary immunodeficiency) AND (standard therapy) AND (unable to be controlled) AND (≥ 50))"}
{"candidate_id": "LLM03046", "doc_id": "NCT03084588_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure requiring dialysis Poorly controlled pulmonary disease (severe asthma or COPD) -Contraindication to regional anesthesia (recent anticoagulant use) Sleep apnea or morbid obesity with possible sleep apnea Allergy to methadone Significant preoperative pain requiring treatment with high doses of opioids (more than 6-8 Norco tablets or equivalence per day) or recent history of opioid abuse", "candidate_expression": "((Allergy) AND (COPD) AND (Contraindication) AND (Norco tablets more than 6-8 per day) AND (Sleep apnea) AND (anticoagulant recent) AND (asthma) AND (dialysis requiring) AND (equivalence) AND (methadone) AND (morbid obesity) AND (opioid abuse recent history) AND (opioids requiring high doses) AND (preoperative pain Significant) AND (pulmonary disease Poorly controlled) AND (regional anesthesia) AND (renal failure Preoperative) AND (sleep apnea possible))"}
{"candidate_id": "LLM03047", "doc_id": "NCT03177811_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((COPD exacerbation) AND (COPD very severe) AND (Comorbidities) AND (FEV1 <40% predicted) AND (FEV1/FVC <0.7) AND (Internal disease) AND (OSA) AND (acetazolamide) AND (allergy) AND (cardiovascular disease uncontrolled) AND (coronary artery disease) AND (heavy smoking >20 cigarettes per day) AND (hypoxemia low altitude) AND (neurologic disease) AND (oxygen saturation room air <92% at 750 m) AND (pneumothorax in the last 2 months) AND (psychiatric disease) AND (renal failure) AND (rheumatologic disease) AND (stroke previous) AND (sulfonamides) AND (systemic arterial hypertension unstable))"}
{"candidate_id": "LLM03048", "doc_id": "NCT03181984_exc", "case_bucket": "or", "source_criterion": "Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((Be judged not suitable to participate the study by the investigators) AND (Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application) AND (Scar diathesis) AND ((porphyrins) OR (porphyrins analogues)) AND ((Allergic constitution) OR (Allergy) OR (Photosensitivity) OR (Porphyria)))"}
{"candidate_id": "LLM03049", "doc_id": "NCT02746900_inc", "case_bucket": "other", "source_criterion": "18-50 ages Singleton pregnancy Cervical length <=25mm between 18(0) and 23(6) weeks", "candidate_expression": "((18-50) AND (<=25mm) AND (Cervical length) AND (Singleton pregnancy) AND (ages) AND (between 18(0) and 23(6) weeks))"}
{"candidate_id": "LLM03050", "doc_id": "NCT02106598_inc", "case_bucket": "or", "source_criterion": "18 years of age or older Histologically confirmed diagnosis of melanoma, breast cancer or gynecologic cancer at MSKCC Have one of the following disease histories: Newly-diagnosed or recurrent (local, regional, metastatic) malignant melanoma or breast cancer patients in whom SLN mapping is indicated Residual clinically or radiographically evident tumor, including primary cutaneous and mucosal melanomas Prior radiation therapy, chemotherapy, or surgery in patients requiring flap reconstruction in the head and neck region. Newly diagnosed patients with previous excisional biopsy. OR Newly-diagnosed gynecologic cancer patients in whom SLN mapping and surgical excision is indicated OR Normal baseline cardiac function based upon pre-operative evaluation At the discretion of the operating surgeon, ANC>1000/mcl and platelets>100,000/mcl. At the discretion of the operating surgeon, Bilirubin level of < 2.0 mg/dl in the absence of a history of Gilbert's disease (or pattern consistent with Gilbert's). For melanoma patients, If patients have a history of malignancy other than melanoma, and other skin cancers in the past five years, their inclusion is up to the discretion of the physician. All patients of childbearing and child-creating age must be using an acceptable form of birth control Women who are pre-menopausal must have a negative serum pregnancy test", "candidate_expression": "((18 years or older) AND (< 2.0 mg/dl) AND (>100,000/mcl) AND (>1000/mcl) AND (ANC) AND (All patients of childbearing and child-creating age must be using an acceptable form of birth control) AND (At the discretion of the operating surgeon) AND (Bilirubin level) AND (Gilbert's disease) AND (Histologically) AND (MSKCC) AND (Newly-diagnosed) AND (Normal) AND (Prior) AND (Residual) AND (SLN mapping) AND (SLN mapping is indicated) AND (Women) AND (age) AND (baseline) AND (breast cancer) AND (cardiac function) AND (chemotherapy) AND (clinically) AND (confirmed) AND (evident) AND (excisional biopsy) AND (flap reconstruction) AND (gynecologic cancer) AND (head and neck region) AND (history) AND (in the absence of) AND (in the past five years) AND (local) AND (malignancy) AND (malignant melanoma) AND (melanoma) AND (metastatic) AND (mucosal melanomas) AND (negative) AND (other than) AND (platelets) AND (pre-menopausal) AND (pre-operative) AND (pre-operative evaluation) AND (previous) AND (primary cutaneous) AND (radiation therapy) AND (radiographically) AND (recurrent) AND (regional) AND (requiring flap reconstruction) AND (serum pregnancy test) AND (skin cancers) AND (surgery) AND (surgical excision) AND (surgical excision is indicated) AND (tumor) AND (up to the discretion of the physician))"}
```
