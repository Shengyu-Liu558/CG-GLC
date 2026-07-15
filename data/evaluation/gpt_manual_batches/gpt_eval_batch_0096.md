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
{"candidate_id": "LLM02376", "doc_id": "NCT03338855_exc", "case_bucket": "or", "source_criterion": "Involvement in the planning and conduct of the study (applies to both AstraZeneca staff and staff at third party vendor or at the investigational sites). Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator. History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study. Clinical diagnosis of Type 1 diabetes, maturity onset diabetes of the young, secondary diabetes or diabetes insipidus. Unstable/rapidly progressing renal disease or estimated Glomerular Filtration Rate < 60 mL/min (Cockcroft-Gault formula). Clinically significant out of range values of serum levels of either alanine aminotransferase (ALT), aspartate aminotransferase (AST) or alkaline phosphatase (ALP) in the Investigator's opinion. Contraindications to dapagliflozin according to the local label. Use of antidiabetic drugs other than metformin within 3 months prior to screening. Weight gain or loss > 5 kg in the last 3 months, ongoing weight-loss diet (hypocaloric diet) or use of weight loss agents. History of drug abuse or alcohol abuse in the past 12 months. Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk. Plasma donation within one month of screening or any blood donation/blood loss > 500 mL within 3 months prior to screening or during the study. Anemia defined as Hemoglobin (Hb) < 115 g/L (7.1 mM) in women and < 120 g/L (7.5 mM) in men. Use of anti-coagulant treatment such as heparin, warfarin, platelet inhibitors, thrombin and factor X inhibitors. Use of medication such as oral glucocorticoids, anti-estrogens or other medications that are known to markedly influence insulin sensitivity. Use of loop diuretics. Regular smoking and other regular nicotine use. Central nervous system aneurysm clip Implanted neural stimulator Implanted cardiac pacemaker of defibrillator Cochlear implant Metal containing corpora aliena in the eye or brain. Patients, who do not want to be informed about unexpected medical findings, or do not wish that their physician be informed about coincidental findings, cannot participate in the study.", "candidate_expression": "((7.1 mM) AND (7.5 mM) AND (< 115 g/L) AND (< 120 g/L) AND (< 3 months) AND (< 60 mL/min) AND (> 5 kg) AND (> 500 mL) AND (Anemia) AND (Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk.) AND (Central nervous system aneurysm clip) AND (Clinically significant) AND (Cochlear implant) AND (Cockcroft-Gault formula) AND (Contraindications) AND (Hemoglobin (Hb)) AND (History) AND (History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study) AND (Implanted neural stimulator) AND (Metal containing) AND (Plasma donation) AND (Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator.) AND (Regular) AND (anti-coagulant treatment) AND (antidiabetic drugs) AND (cardiovascular event) AND (clinically significant) AND (dapagliflozin) AND (disease) AND (disorder) AND (hypocaloric diet) AND (in the last 3 months) AND (in the past 12 months) AND (loop diuretics) AND (markedly influence insulin sensitivity) AND (metformin) AND (ongoing) AND (other) AND (other than) AND (out of range values) AND (recent) AND (regular) AND (screening) AND (within 3 months prior to screening) AND (within one month of screening) AND ((Type 1 diabetes) OR (diabetes insipidus) OR (maturity onset diabetes of the young) OR (secondary diabetes)) AND ((Unstable) OR (rapidly progressing)) AND ((estimated Glomerular Filtration Rate) OR (renal disease)) AND ((alanine aminotransferase (ALT)) OR (alkaline phosphatase (ALP)) OR (aspartate aminotransferase (AST))) AND ((Weight gain) OR (Weight loss)) AND ((weight loss agents) OR (weight-loss diet)) AND ((alcohol abuse) OR (drug abuse)) AND ((blood donation) OR (blood loss)) AND ((during the study) OR (within 3 months prior to screening)) AND ((men) OR (women)) AND ((factor X inhibitors) OR (heparin) OR (platelet inhibitors) OR (thrombin) OR (warfarin)) AND ((anti-estrogens) OR (medications) OR (oral glucocorticoids)) AND ((nicotine) OR (smoking)) AND ((cardiac pacemaker) OR (defibrillator)) AND ((corpora aliena in the brain) OR (corpora aliena in the eye)))"}
{"candidate_id": "LLM02377", "doc_id": "NCT02490839_inc", "case_bucket": "other", "source_criterion": "Participants having H. pylori related chronic gastritis with/without peptic ulcers who are aged greater than 20 years old and are willing to received eradication therapy.", "candidate_expression": "((H. pylori related) AND (aged) AND (chronic gastritis) AND (eradication therapy) AND (greater than 20 years old) AND (peptic ulcers) AND (willing to received))"}
{"candidate_id": "LLM02378", "doc_id": "NCT02863120_inc", "case_bucket": "or", "source_criterion": "Male or non-pregnant female between the ages of 18-65 Patients willing and able to sign the informed consent Patients able to comply with follow-up requirements including self-evaluations Patients requiring a primary total knee replacement Patients with a diagnosis of osteoarthritis, traumatic arthritis, or avascular necrosis", "candidate_expression": "((Male) AND (Patients willing and able to sign the informed consent) AND (ages 18-65) AND (atients able to comply with follow-up requirements including self-evaluations) AND (avascular necrosis) AND (female pregnant) AND (osteoarthritis) AND (primary total knee replacement) AND (traumatic arthritis))"}
{"candidate_id": "LLM02379", "doc_id": "NCT02620904_inc", "case_bucket": "other", "source_criterion": "Intrauterine fetal death as confirmed by absence of cardiac motion on ultrasound by Attending physician at the time of admission to the hospital. Estimated gestational age greater than 20 weeks Hemodynamically stable and appropriate for induction of labor as per primary clinical health team in house Women with one prior low transverse cesarean delivery", "candidate_expression": "((Estimated gestational age greater than 20 weeks) AND (Hemodynamically stable) AND (Intrauterine fetal death) AND (Women) AND (absence of cardiac motion) AND (induction of labor) AND (low transverse cesarean delivery one) AND (ultrasound at the time of admission to the hospital))"}
{"candidate_id": "LLM02380", "doc_id": "NCT02905734_exc", "case_bucket": "other", "source_criterion": "Lack of understanding of the study contra-indication to nicotine replacement therapy health status incompatible with detention in police cells serious mental disorder usual place of residence outside Seine-Saint-Denis", "candidate_expression": "((Lack of understanding of the study) AND (contra-indication) AND (incompatible with detention in police cells) AND (nicotine replacement therapy) AND (place of residence outside Seine-Saint-Denis) AND (serious mental disorder))"}
{"candidate_id": "LLM02381", "doc_id": "NCT01815580_inc", "case_bucket": "or", "source_criterion": "Adult men who have sex with men, and transgender women Unaware of HIV status at enrollment in follow-up cohort High risk for HIV infection Willing to test for HIV No prior ART, including prior administration of pre- and post-exposure prophylaxis in the last 30 days Willing to provide informed consent", "candidate_expression": "((Adult) AND (HIV infection) AND (HIV status) AND (High risk for) AND (No) AND (Unaware) AND (Unaware of HIV status) AND (Willing to) AND (Willing to provide) AND (at enrollment in follow-up cohort) AND (enrollment in follow-up cohort) AND (in the last 30 days) AND (informed consent) AND (prior) AND (test for HIV) AND ((ART) OR (administration)) AND ((post-exposure prophylaxis) OR (pre- exposure prophylaxis)) AND ((men who have sex with men) OR (transgender women)))"}
{"candidate_id": "LLM02382", "doc_id": "NCT03036462_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to the active substance, to FCM or any of its excipients Known serious hypersensitivity to other parenteral iron products Anaemia not attributed to iron deficiency, e.g. other microcytic anaemia Evidence of iron overload or disturbances in the utilisation of iron", "candidate_expression": "((Anaemia) AND (Hypersensitivity) AND (hypersensitivity serious) AND (iron) AND (microcytic anaemia other) AND (parenteral iron products) AND NOT (iron deficiency attributed to) AND ((disturbances in the utilisation of iron) OR (iron overload)) AND ((FCM) OR (active substance) OR (excipients)))"}
{"candidate_id": "LLM02383", "doc_id": "NCT03446885_inc", "case_bucket": "or", "source_criterion": "diagnosis of ADHD parental permission and/or teen consent/assent as appropriate between 16-25 years of age IQ greater than or equal to 70 permit or license to drive ability to read and understand English", "candidate_expression": "((16-25 years) AND (ADHD) AND (IQ) AND (age) AND (greater than or equal to 70) AND (parental permission and/or teen consent/assent as appropriate) AND ((license to drive) OR (permit to drive)) AND ((ability to read English) OR (ability to understand English)))"}
{"candidate_id": "LLM02384", "doc_id": "NCT03620526_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02385", "doc_id": "NCT02162433_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitivity reaction to dexmedetomidine Organ dysfunction (renal/hepatic failure or leukemia) Cardiac disease (congenital or acquired) Airway or thoracic malformation Cerebral palsy Hypotonia Need for premedication Current/recent upper respiratory infection (within four weeks prior to the surgery) Asthma Allergy or intolerance to clonidine Non-English speaking parents/patients.", "candidate_expression": "((Airway malformation) AND (Allergy) AND (Asthma) AND (Cardiac disease) AND (Cerebral palsy) AND (Current) AND (Hypotonia) AND (Need for) AND (Non-English speaking parents) AND (Non-English speaking patients) AND (Organ dysfunction) AND (acquired) AND (allergy) AND (clonidine) AND (congenital) AND (dexmedetomidine) AND (hepatic failure) AND (hypersensitivity) AND (intolerance) AND (leukemia) AND (premedication) AND (recent) AND (renal failure) AND (surgery) AND (the surgery) AND (thoracic malformation) AND (upper respiratory infection) AND (within four weeks prior to the surgery))"}
{"candidate_id": "LLM02386", "doc_id": "NCT02883400_exc", "case_bucket": "other", "source_criterion": "dual organ transplant", "candidate_expression": "((dual) AND (organ transplant))"}
{"candidate_id": "LLM02387", "doc_id": "NCT03228017_inc", "case_bucket": "or", "source_criterion": "Subjects with a history of moderate to severe psoriatic disease Group 2: Healthy subjects without known psoriatic disease or cardiovascular disease", "candidate_expression": "((Healthy) AND (psoriatic disease history) AND ((moderate) OR (severe)) AND ((cardiovascular disease) OR (psoriatic disease)))"}
{"candidate_id": "LLM02388", "doc_id": "NCT02871206_exc", "case_bucket": "or", "source_criterion": "Anaphylactic reaction to a previous dose of influenza vaccine or to any of its components Known Immunoglobulin E (IgE)-mediated hypersensitivity to eggs manifested as hives, swelling of the mouth and throat, difficulty in breathing, hypotension, or shock Guillain- Barré syndrome within eight weeks of a previous influenza vaccine Use of aspirin or salicylate- containing products within 30 days before enrollment Household members of children in Group A", "candidate_expression": "((Anaphylactic reaction) AND (Group A) AND (Guillain- Barré syndrome) AND (Household members) AND (Immunoglobulin E (IgE)-mediated hypersensitivity) AND (a previous influenza vaccine) AND (children) AND (eggs) AND (influenza vaccine) AND (previous) AND (within 30 days before enrollment) AND (within eight weeks of a previous influenza vaccine) AND ((difficulty in breathing) OR (hives) OR (hypotension) OR (shock) OR (swelling of the mouth) OR (swelling of the throat)) AND ((aspirin) OR (salicylate- containing products)) AND ((influenza vaccine) OR (its components)))"}
{"candidate_id": "LLM02389", "doc_id": "NCT02982577_exc", "case_bucket": "other", "source_criterion": "Sensitivity to pilocarpine Secondary Sjögren's syndrome; Type II diabetes mellitus; AIDS; pregnant or lactating women; Glaucoma; Uncontrolled asthma; Chronic obstructive pulmonary disease; Renal diseases; Severe cardiovascular diseases; Gastrointestinal disorders; Hepatic insufficiency.", "candidate_expression": "((AIDS) AND (Chronic obstructive pulmonary disease) AND (Gastrointestinal disorders) AND (Glaucoma) AND (Hepatic insufficiency) AND (Renal diseases) AND (Sensitivity) AND (Sjögren's syndrome Secondary) AND (Type II diabetes mellitus) AND (asthma Uncontrolled) AND (cardiovascular diseases Severe) AND (pilocarpine) AND (pregnant or lactating women))"}
{"candidate_id": "LLM02390", "doc_id": "NCT03192020_exc", "case_bucket": "or", "source_criterion": "recurrent contracture in the finger to be treated neurologic condition causing the loss of function of the finger to be treated contraindication for collagenase clostridium histolyticym (Xiapex/Xiaflex ®) pregnant or breast feeding TPED > 135° (Tubiana stage 4) in finger to be treated rheumatoid arthritis previous fracture in finger to be treated, which affects range of motion of MP or PIP joint age > 80 years", "candidate_expression": "((TPED > 135°) AND (Tubiana stage 4) AND (affects range of motion) AND (age > 80 years) AND (collagenase clostridium histolyticym) AND (contracture recurrent finger to be treated) AND (contraindication) AND (fracture previous finger to be treated) AND (loss of function finger to be treated) AND (neurologic condition) AND (rheumatoid arthritis) AND ((Xiaflex) OR (Xiapex)) AND ((breast feeding) OR (pregnant)) AND ((MP joint) OR (PIP joint)))"}
{"candidate_id": "LLM02391", "doc_id": "NCT03360214_exc", "case_bucket": "or", "source_criterion": "Allergy to narcotic medications Intake of any chronic opioids or pain medications preoperatively", "candidate_expression": "((Allergy) AND (any) AND (chronic) AND (narcotic medications) AND (preoperatively) AND ((opioids) OR (pain medications)))"}
{"candidate_id": "LLM02392", "doc_id": "NCT02612181_exc", "case_bucket": "or", "source_criterion": "Age< 18 Pregnancy Bradycardia (HR<55bpm) Systolic Blood Pressure < 80 mmHg / Mean arterial pressure < 50 mmHg on maximal support Death imminent Unlikely to survive 90 days Acute liver failure Dementia High-grade block in the absence of a functioning pacemaker.", "candidate_expression": "((Acute liver failure) AND (Age < 18) AND (Bradycardia) AND (Death imminent) AND (Dementia) AND (HR <55bpm) AND (High-grade block) AND (Pregnancy) AND (support) AND NOT (pacemaker functioning) AND ((Mean arterial pressure < 50 mmHg) OR (Systolic Blood Pressure < 80 mmHg)))"}
{"candidate_id": "LLM02393", "doc_id": "NCT02733159_inc", "case_bucket": "other", "source_criterion": "Histologically confirmed PD-L1 status defined NSCLC. Biopsy must be within 70 days of first treatment with pembrolizumab. ECOG performance status 2. Life expectancy > 12 weeks. Uni-dimensionally measurable disease according to Response Evaluation Criteria in Solid Tumours (RECIST) v1.1 Computerised Tomography (CT) scan of chest and abdomen within 28 days of starting pembrolizumab. Adequate haematological function: Platelet count ≥100 x 109 /L. Neutrophils ≥1.5 x 109/L. Haemoglobin ≥ 9g/dL. Adequate hepatic function: Serum bilirubin ≤1.5 x upper limit of normal (ULN). Serum transaminases ≤2.5 x ULN. Adequate renal function: Creatinine clearance <1.5 times ULN concurrent with creatinine clearance >50 ml/min. Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.", "candidate_expression": "((Biopsy within 70 days of first treatment) AND (Computerised Tomography (CT) scan of chest and abdomen within 28 days of starting pembrolizumab) AND (Creatinine clearance <1.5 times ULN concurrent) AND (ECOG performance status 2) AND (Haemoglobin ≥ 9g/dL) AND (Life expectancy) AND (NSCLC PD-L1 status) AND (Neutrophils ≥1.5 x 109/L) AND (Platelet count ≥100 x 109 /L) AND (Provision of signed and dated, written informed consent prior to any study specific procedures, sampling and analyses.) AND (Response Evaluation Criteria in Solid Tumours (RECIST) v1.1 Uni-dimensionally measurable) AND (Serum bilirubin ≤1.5 x upper limit of normal (ULN)) AND (Serum transaminases ≤2.5 x ULN) AND (creatinine clearance concurrent >50 ml/min) AND (disease) AND (pembrolizumab) AND (renal function Adequate))"}
{"candidate_id": "LLM02394", "doc_id": "NCT02678377_inc", "case_bucket": "or", "source_criterion": "Undergoing mid-urethral sling surgery Have symptoms of both stress and urgency urinary incontinence Able to consent, fill out study documents, and complete all study procedures and follow-up visits At least 18 years of age English speaking Be able and willing to learn clean intermittent self catheterization technique", "candidate_expression": "((Able to consent, fill out study documents, and complete all study procedures and follow-up visits) AND (At least 18 years) AND (age) AND (mid-urethral sling surgery) AND (stress urinary incontinence) AND (urgency urinary incontinence))"}
{"candidate_id": "LLM02395", "doc_id": "NCT03333655_inc", "case_bucket": "or", "source_criterion": "Response assessment of complete response (CR), partial response (PR), long stable disease (SD) for >3 months with a cancer immunotherapy treatment for metastatic cancer or hematologic malignancies either through a marketed CPI or through participation in a Roche/Genentech CPI clinical trial. Availability of tumor biopsy material extracted and preserved by the investigating site.", "candidate_expression": "((Response assessment) AND (cancer) AND (complete response (CR)) AND (for >3 months) AND (hematologic malignancies) AND (immunotherapy treatment) AND (long stable disease (SD)) AND (marketed CPI) AND (metastatic cancer) AND (partial response (PR)) AND (participation in a Roche/Genentech CPI clinical trial))"}
{"candidate_id": "LLM02396", "doc_id": "NCT02607748_exc", "case_bucket": "or", "source_criterion": "Age < 18 years Creatinine > 1.5 mg/dL History of severe allergy to Iodine contrast agents Pregnancy Active atrial fibrillation Multiple premature ventricular or atrial contractions Ejection fraction <35% Class III congestive heart failure", "candidate_expression": "((Age < 18 years) AND (Creatinine > 1.5 mg/dL) AND (Ejection fraction <35%) AND (Iodine contrast agents) AND (Multiple premature atrial contractions) AND (Multiple premature ventricular contractions) AND (Pregnancy) AND (allergy) AND (atrial fibrillation) AND (congestive heart failure Class III))"}
{"candidate_id": "LLM02397", "doc_id": "NCT03317197_exc", "case_bucket": "or", "source_criterion": "Pregnant women and young children aged <18 years; Patients with underlying disease cases without the possibility of resuscitation (e.g., terminal cancer); Patients with do-not-resuscitate (DNR) status; Death by excessive bleeding (e.g., abdominal main artery rupture); Patients who have experienced in-hospital CA; Patients previously treated with steroid, anti-cancer medicine, or immunosuppression treatment before CA; Patients already been registered with other studies; or Patients from whom informed consent cannot be obtained", "candidate_expression": "((CA) AND (CA in-hospital) AND (Death by excessive bleeding) AND (Patients already been registered with other studies; or) AND (Patients from whom informed consent cannot be obtained) AND (aged <18 years) AND (do-not-resuscitate (DNR) status) AND (hospital) AND (main artery rupture abdominal) AND (terminal cancer) AND (underlying disease without the possibility of resuscitation) AND (women) AND (young children) AND ((anti-cancer medicine) OR (steroid)) AND ((immunosuppression treatment before CA) OR (treated previously)))"}
{"candidate_id": "LLM02398", "doc_id": "NCT03339284_exc", "case_bucket": "or", "source_criterion": "age under 18y or over 85y diabetes type 1 with complications no co-operation or inadequate finnish language skills persistent pain for other reason severe hepatic insufficiency or paracetamol (acetaminophen) is contraindicated for other reason any type of steroid in regular use oxycodone contraindicated medications changing notably paracetamol (acetaminophen) and/or ropivacaine metabolism in regular use", "candidate_expression": "((acetaminophen) AND (age) AND (complications) AND (contraindicated) AND (diabetes type 1) AND (no) AND (other reason) AND (oxycodone) AND (paracetamol) AND (persistent pain) AND (regular use) AND (severe) AND (steroid) AND (under 18y or over 85y) AND ((contraindicated) OR (hepatic insufficiency)) AND ((paracetamol) OR (ropivacaine)) AND ((co-operation) OR (inadequate finnish language skills)))"}
{"candidate_id": "LLM02399", "doc_id": "NCT00718952_inc", "case_bucket": "or", "source_criterion": "Subjects aged 12-65. Confirmed idiopathic pulmonary hypertension, connective tissue disease associated pulmonary hypertension, congenital heart disease(with Eisenmenger syndrome) associated pulmonary hypertension. Baseline 6-minutes walking distance 150m-550m. WHO pulmonary hypertension function II-III with non-responder to calcium channel blockers. Documented written informed consent.", "candidate_expression": "((12-65) AND (150m-550m) AND (6-minutes walking distance) AND (Baseline) AND (Eisenmenger syndrome) AND (II-III) AND (WHO pulmonary hypertension function) AND (aged) AND (calcium channel blockers) AND (congenital heart disease) AND (connective tissue disease associated) AND (idiopathic pulmonary hypertension) AND (non-responder to calcium channel blockers) AND (pulmonary hypertension) AND (written informed consent))"}
{"candidate_id": "LLM02400", "doc_id": "NCT03624881_inc", "case_bucket": "or", "source_criterion": "Symptomatic paroxysmal AF who had at least one AF episode electrocardiographically documented within one (1) year prior to enrollment. Documentation may include electrocardiogram (ECG); Transtelephonic monitoring (TTM), Holter monitor or telemetry strip Failed at least one antiarrhythmic drug (AAD) (Class I or III antiarrhythmic drugs) as evidenced by recurrent symptomatic AF, or intolerable to the AAD Age 18 years or older Signed Patient Informed Consent Form (ICF) Able and willing to comply with all pre-, post-, and follow-up testing and requirements", "candidate_expression": "((AAD) AND (AF episode at least one electrocardiographically documented within one (1) year prior to enrollment) AND (Age 18 years or older) AND (Signed Patient Informed Consent Form (ICF)) AND (antiarrhythmic drug (AAD) at least one) AND (paroxysmal AF Symptomatic) AND ((Holter monitor) OR (Transtelephonic monitoring (TTM)) OR (electrocardiogram (ECG)) OR (electrocardiographically) OR (telemetry strip)) AND ((Class I antiarrhythmic drugs) OR (III antiarrhythmic drugs)) AND ((intolerable) OR (recurrent symptomatic AF)))"}
```
