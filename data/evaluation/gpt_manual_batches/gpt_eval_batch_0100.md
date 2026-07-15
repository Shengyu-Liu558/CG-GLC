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
{"candidate_id": "LLM02476", "doc_id": "NCT03029078_inc", "case_bucket": "or", "source_criterion": "Patient harboring a GRE or CRE bacteria Colonization confirmed by our microbiology department, including at least 3 positives swabs in the last month", "candidate_expression": "((CRE bacteria) AND (Colonization) AND (GRE bacteria) AND (at least 3) AND (confirmed by our microbiology department) AND (in the last mont) AND (positives) AND (swabs))"}
{"candidate_id": "LLM02477", "doc_id": "NCT03169127_exc", "case_bucket": "or", "source_criterion": "Presence of systemic diseases; Presence of local inflammation and/or infection; Any history of allergic reaction to local anesthetics, gastrointestinal bleeding or ulceration; Cardiovascular, kidney or hepatic diseases; Patients who are making use of antidepressants, diuretics or anticoagulants; Asthma and allergy to aspirin, ibuprofen or any other nonsteroidal antiinflammatory drug; Regular use of any nonsteroidal antiinflammatory drug, Pregnancy or breast feeding.", "candidate_expression": "((Regular use) AND (any other) AND (history) AND (local anesthetics) AND (nonsteroidal antiinflammatory drug) AND (systemic diseases) AND ((Cardiovascular diseases) OR (hepatic diseases) OR (kidney diseases)) AND ((anticoagulants) OR (antidepressants) OR (diuretics)) AND ((Asthma) OR (allergy)) AND ((aspirin) OR (ibuprofen) OR (nonsteroidal antiinflammatory drug)) AND ((Pregnancy) OR (breast feeding)) AND ((local infection) OR (local inflammation)) AND ((allergic reaction) OR (gastrointestinal bleeding) OR (gastrointestinal ulceration)))"}
{"candidate_id": "LLM02478", "doc_id": "NCT02542956_inc", "case_bucket": "or", "source_criterion": "Undergoing abdominoplasty or TRAM flap breast reconstruction", "candidate_expression": "((TRAM flap breast reconstruction) OR (abdominoplasty))"}
{"candidate_id": "LLM02479", "doc_id": "NCT01908465_exc", "case_bucket": "or", "source_criterion": "IBS subtype with constipation medication: antidepressants or H1-receptor antagonists pregnancy, breast feeding co-morbidity: severe kidney- and/or liver disease or other gastrointestinal diseases", "candidate_expression": "((IBS subtype) AND (constipation) AND (severe) AND ((gastrointestinal diseases) OR (kidney disease) OR (liver disease)) AND ((H1-receptor antagonists) OR (antidepressants)) AND ((breast feeding) OR (pregnancy)))"}
{"candidate_id": "LLM02480", "doc_id": "NCT02488057_exc", "case_bucket": "other", "source_criterion": "pregnant 30 min or more of moderate to vigorous activity more than 3 times per week cardiovascular disease physical limitations that might be aggravated by moderate physical activity planning to move in next 12-24 months diabetic", "candidate_expression": "((30 min or more) AND (aggravated by physical activity) AND (cardiovascular disease) AND (diabetic) AND (in next 12-24 months) AND (moderate) AND (moderate to vigorous activity) AND (more than 3 times per week) AND (physical limitations) AND (planning to move) AND (pregnant))"}
{"candidate_id": "LLM02481", "doc_id": "NCT00752310_inc", "case_bucket": "or", "source_criterion": "Non-smoking, or smoking no more than 10 cigarettes, or 2 cigars, or 2 pipes per day for at least 3 months prior to selection Normal weight as defined by a Body Mass Index (BMI, weight in kg divided by the square of height in meters) of 18.0 to 30.0 kg/m2, extremes included Able to comply with protocol requirements. Healthy on the basis of a medical evaluation that reveals the absence of any clinically relevant abnormality and includes a physical examination, medical history, electrocardiogram (ECG), vital signs, and the results of blood biochemistry, blood coagulation, and hematology tests and a urinalysis carried out at screening.", "candidate_expression": "((Able to comply with protocol requirements) AND (Body Mass Index 18.0 to 30.0 kg/m2, extremes included) AND (ECG) AND (Healthy) AND (Normal weight selection) AND (blood biochemistry tests) AND (blood coagulation tests) AND (electrocardiogram) AND (hematology tests) AND (medical evaluation at screening) AND (medical history) AND (physical examination) AND (urinalysis) AND (vital signs) AND NOT (abnormality clinically relevant) AND ((BMI) OR (weight in kg divided by the square of height in meters)) AND ((smoking for at least 3 months prior to selection) OR NOT (smoking)) AND ((cigarettes no more than 10 per day) OR (cigars no more than 2 per day) OR (pipes no more than 2 per day)))"}
{"candidate_id": "LLM02482", "doc_id": "NCT03388840_exc", "case_bucket": "or", "source_criterion": "Patients with Non-androgenetic causes of hair loss. Female patients with androgenetic alopecia. Patients who received anti-hair loss treatment within the past six months. Patients with history of bleeding disorders or on anticoagulant therapy. Patients with history of chronic liver disease, cancer or connective tissue disorders. Patients with current scalp infection.", "candidate_expression": "((Female) AND (Non-androgenetic causes of hair loss) AND (androgenetic alopecia) AND (anti-hair loss treatment) AND (current) AND (history) AND (scalp infection) AND (within the past six months) AND ((anticoagulant therapy) OR (bleeding disorders)) AND ((cancer) OR (chronic liver disease) OR (connective tissue disorders)))"}
{"candidate_id": "LLM02483", "doc_id": "NCT01217671_inc", "case_bucket": "or", "source_criterion": "Diagnosis of emphysema confirmed by CT scan. If a report of past CT scan is not available at site documenting then a CT scan is to be performed at screening Male or female patients at least 18 years of age. Able and willing to sign an informed consent. Patient with record of congenital AAT deficiency of phenotype PiZZ (homozygote) or other rare phenotypes related to AAT deficiency and with AAT serum level ≤ 11 micromole. For patients receiving IV AAT augmentation therapy the serum AAT level threshold does not apply. FEV1/SVC <70% of predicted value post bronchodilator (SVC is slow VC) and FEV1 < 80% of predicted value post-bronchodilator History of at least two moderate or severe exacerbations that required change in treatment (antibiotics, systemic steroids, hospitalization) in the last 18 months prior to date of screening , with at least one of these occurring within the last 12 months prior to screening. Ability to comply with completion of electronic diary. Ability to self-administer inhaled AAT. No significant abnormalities in serum hematology, serum chemistry and serum inflammatory / immunogenic markers according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency. No significant abnormalities in urinalysis according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency. No significant abnormalities in ECG per investigator judgment. Negative for HBsAg and for antibodies to HCV, HIV-1. AAT deficient patients who are either naïve (not receiving IV augmentation therapy) or AAT deficient patients (receiving IV augmentation therapy), if they have been stable on regular therapy for at least 3 months prior to the screening visit and are willing to continue the same regime throughout this trial. Note that only sites in Germany can recruit patients who are currently being treated with IV AAT.Patients who stopped IV augmentation treatment 6 months prior to screening date and will not re-start this treatment for the course of the study will be considered Naïve. Non-pregnant, non-lactating female patients, whose screening pregnancy test is negative and who are using contraceptive methods deemed reliable by the investigator, or who are at least 2 years post-menopausal or surgically sterilized.", "candidate_expression": "((< 80% of predicted value) AND (<70% of predicted value) AND (AAT deficient) AND (AAT serum level) AND (Ability to comply with completion of electronic diary.) AND (Ability to self-administer inhaled AAT.) AND (Able and willing to sign an informed consent.) AND (CT scan) AND (ECG) AND (FEV1) AND (FEV1/SVC) AND (HBsAg) AND (HIV-1) AND (IV AAT augmentation therapy) AND (IV augmentation therapy) AND (Negative) AND (No) AND (No significant abnormalities in ECG per investigator judgment.) AND (No significant abnormalities in serum hematology, serum chemistry and serum inflammatory / immunogenic markers according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency.) AND (No significant abnormalities in urinalysis according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency.) AND (Non) AND (abnormalities in ECG) AND (age) AND (antibodies to HCV) AND (at least 18 years) AND (at least 2 years) AND (at least one) AND (at least two) AND (at screening) AND (bronchodilator) AND (change in treatment) AND (comply with completion of electronic diary) AND (date of screening) AND (deemed reliable by the investigator) AND (emphysema) AND (exacerbations) AND (female) AND (for at least 3 months prior to the screening) AND (in the last 18 months prior to date of screening) AND (lactating) AND (negative) AND (non) AND (not available) AND (not receiving) AND (past) AND (post bronchodilator) AND (post-bronchodilator) AND (pregnant) AND (report of past CT scan) AND (required change in treatment) AND (screening) AND (self-administer inhaled AAT) AND (significant) AND (stable) AND (surgically) AND (systemic) AND (the screening) AND (therapy) AND (this trial) AND (throughout this trial) AND (treatment) AND (willing to continue) AND (within the last 12 months prior to screening) AND (≤ 11 micromole) AND ((Male) OR (female)) AND ((congenital AAT deficiency of phenotype PiZZ (homozygote)) OR (rare phenotypes related to AAT deficiency)) AND ((moderate) OR (severe)) AND ((antibiotics) OR (hospitalization) OR (systemic steroids)) AND ((IV augmentation therapy) OR (naïve)) AND ((contraceptive methods) OR (pregnancy test)) AND ((post-menopausal) OR (surgically sterilized)))"}
{"candidate_id": "LLM02484", "doc_id": "NCT02825290_inc", "case_bucket": "other", "source_criterion": "20-40 years old women Spontaneously ovulating women Treated in our IVF unit for frozen-thawed embryo transfer At least one top quality embryo", "candidate_expression": "((20-40 years) AND (At least one) AND (Spontaneously ovulating) AND (frozen-thawed embryo transfer) AND (old) AND (our IVF unit) AND (top quality embryo) AND (women))"}
{"candidate_id": "LLM02485", "doc_id": "NCT01205334_inc", "case_bucket": "or", "source_criterion": "Histopathological verification of glioblastoma multiforme (GBM: WHO grade IV) in remission (Group A) or with active disease (Group B). CMV-positive GBM CMV seropositive Life expectancy 6 weeks or greater Karnofsky/Lansky score 50 or greater Patient or parent/guardian capable of providing informed consent Bilirubin less than 1.5x upper limit of normal, AST less than 3x upper limit of normal, serum creatinine less than 1.5x normal and Hgb 8.0 g/dL or greater Pulse oximetry of 90% or greater on room air Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom. Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study. Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.", "candidate_expression": "((6 weeks or greater) AND (90% or greater) AND (AST) AND (Bilirubin) AND (CMV) AND (CMV seropositive) AND (CMV-positive) AND (GBM) AND (Group A) AND (Group B) AND (Histopathological) AND (Histopathological verification) AND (Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.) AND (Karnofsky/Lansky) AND (Life expectancy) AND (Patient or parent/guardian capable of providing informed consent) AND (Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study.) AND (Pulse oximetry) AND (Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom.) AND (WHO) AND (active) AND (antineoplastic therapy) AND (been off) AND (entry in this study) AND (for one month prior to entry in this study) AND (glioblastoma multiforme) AND (grade IV) AND (in remission) AND (less than 1.5x upper limit of normal) AND (less than 3x upper limit of normal) AND (on room air) AND (score 50 or greater) AND (with active disease))"}
{"candidate_id": "LLM02486", "doc_id": "NCT02883400_inc", "case_bucket": "other", "source_criterion": "liver transplant", "candidate_expression": "(liver transplant)"}
{"candidate_id": "LLM02487", "doc_id": "NCT02957877_exc", "case_bucket": "or", "source_criterion": "History of intolerance to LMWHs during HD Receiving warfarin or other oral anticoagulant Pregnant patients", "candidate_expression": "((HD) AND (LMWHs during HD) AND (Pregnant) AND (intolerance) AND (oral anticoagulant other) AND (warfarin))"}
{"candidate_id": "LLM02488", "doc_id": "NCT02937779_exc", "case_bucket": "other", "source_criterion": "Women refusing HBs Ag test HIV co-infection HCV co-infection HBV treatment ongoing at the day of inclusion Creatinine clearance < 30 mL/min Severe gravidic disease present at inclusion involving life threatening to the mother and/or the child Evidence of pre-existing fetal anomalies incompatible with the child's life Imminent child's birth defined as cervix dilatation up to 7 centimeters Intention to deliver in a maternity not linked to the study Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study. Concurrent participation in any other clinical trial without written agreement of the two study teams", "candidate_expression": "((Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study) AND (Concurrent participation in any other clinical trial without written agreement of the two study teams) AND (Creatinine clearance < 30 mL/min) AND (HBV treatment) AND (Imminent child's birth) AND (Intention to deliver in a maternity not linked to the study) AND (cervix dilatation 7 centimeters) AND (co-infection HCV) AND (co-infection HIV) AND (fetal anomalies) AND (gravidic disease Severe life threatening) AND NOT (HBs Ag test))"}
{"candidate_id": "LLM02489", "doc_id": "NCT03212352_inc", "case_bucket": "or", "source_criterion": "a crown-rump length = 6mm and no cardiac activity OR a crown-rump length <6mm and no fetal growth at least one week later OR At least one week after diagnosis OR a discrepancy of at least one week between crown-rump length and calendar gestational age Intra-uterine pregnancy Women aged above 16 years Hemodynamic stable patient No signs of infection No signs of incomplete abortion No contraindications for mifepristone or misoprostol", "candidate_expression": "((Hemodynamic stable) AND (Intra-uterine pregnancy) AND (Women) AND (aged above 16 years) AND (crown-rump length <6mm) AND (crown-rump length = 6mm) AND (discrepancy at least one week between crown-rump length and calendar gestational age) AND NOT (signs of infection) AND NOT (signs of incomplete abortion) AND NOT (cardiac activity) AND NOT (fetal growth) AND ((mifepristone) OR (misoprostol)))"}
{"candidate_id": "LLM02490", "doc_id": "NCT00679341_exc", "case_bucket": "or", "source_criterion": "History of any chemotherapy for MBC. An interval of < 6 months from the completion of cytotoxic chemotherapy in the neo-adjuvant or adjuvant setting until the time of metastatic diagnosis. Trastuzumab ≤ 21 days prior to randomization. Hormone therapy < 7 days prior to randomization. Current peripheral neuropathy of Grade ≥ 3. History of other malignancy within the last 5 years, except for appropriately treated carcinoma in situ of the cervix, non-melanoma skin carcinoma, Stage I uterine cancer, or other cancers with a similar outcome as those previously mentioned. Previous radiotherapy for the treatment of unresectable, locally advanced or metastatic breast cancer is not allowed if more than 25% of marrow-bearing bone has been irradiated or the last fraction of radiotherapy has been administered within approximately 3 weeks prior to randomization. Brain metastases that are untreated, symptomatic, or require therapy to control symptoms or any radiation, surgery, or other therapy to control symptoms from brain metastases within 2 months prior to randomization. History of exposure to the following cumulative doses of anthracyclines: Doxorubicin or liposomal doxorubicin > 500 mg/m^2; epirubicin > 900 mg/m^2; mitoxantrone > 120mg/m^2 and idarubicin > 90 mg/m^2. Current unstable angina. History of symptomatic congestive heart failure, or ventricular arrhythmia requiring treatment. History of myocardial infarction within 6 months prior to randomization. Left ventricular ejection fraction (LVEF) below 50% within approximately 28 days prior to randomization. History of decreased LVEF or symptomatic congestive heart failure (CHF) with previous adjuvant trastuzumab treatment. Cardiac troponin I ≥ 0.2 ng/mL within 28 days of randomization. Severe dyspnea at rest because of complications of advanced malignancy or requiring current continuous oxygen therapy. Current severe, uncontrolled systemic disease (eg, clinically significant cardiovascular, pulmonary, or metabolic disease; wound healing disorders; ulcers; or bone fractures). Major surgical procedure or significant traumatic injury within approximately 28 days prior to randomization or anticipation of the need for major surgery during the course of study treatment. Current pregnancy or lactation. History of receiving any investigational treatment within approximately 28 days prior to randomization. Current known infection with human immunodeficiency virus (HIV), active hepatitis B and/or hepatitis C virus. History of intolerance (including Grade 3-4 infusion reaction) or hypersensitivity to trastuzumab, murine proteins, or docetaxel. Known hypersensitivity to any of the study drugs, including the excipients, or any drugs formulated in polysorbate 80. Assessed by the investigator to be unable or unwilling to comply with the requirements of the protocol.", "candidate_expression": "((Brain metastases) AND (Cardiac troponin I ≥ 0.2 ng/mL within 28 days of randomization) AND (Grade 3-4) AND (Grade ≥ 3) AND (History) AND (Hormone therapy < 7 days prior to randomization) AND (LVEF History decreased) AND (Left ventricular ejection fraction (LVEF) below 50% within approximately 28 days prior to randomization) AND (MBC < 6 months) AND (Stage I) AND (Trastuzumab ≤ 21 days prior to randomization randomization) AND (advanced malignancy) AND (anthracyclines) AND (brain metastases within 2 months prior to randomization randomization) AND (breast cancer) AND (chemotherapy) AND (congestive heart failure (CHF) symptomatic) AND (continuous oxygen therapy current) AND (cytotoxic chemotherapy neo-adjuvant setting adjuvant setting) AND (dyspnea Severe) AND (epirubicin > 900 mg/m^2) AND (hypersensitivity) AND (idarubicin > 90 mg/m^2) AND (infusion reaction) AND (investigational treatment History of within approximately 28 days prior to randomization) AND (major surgery anticipation of the need during the course of study treatment) AND (malignancy other within the last 5 years) AND (marrow-bearing bone irradiated more than 25%) AND (metastatic diagnosis) AND (mitoxantrone > 120mg/m^2) AND (myocardial infarction within 6 months prior to randomization) AND (peripheral neuropathy Current Grade ≥ 3) AND (radiotherapy Previous) AND (systemic disease severe uncontrolled) AND (trastuzumab previous adjuvant) AND (treated) AND (treatment) AND (unstable angina Current) AND ((complications) OR (requiring current continuous oxygen therapy)) AND ((lactation) OR (pregnancy)) AND ((hepatitis B virus) OR (hepatitis C virus) OR (human immunodeficiency virus (HIV) Current)) AND ((hypersensitivity) OR (intolerance)) AND ((docetaxel) OR (murine proteins) OR (trastuzumab)) AND ((cardiovascular disease) OR (metabolic disease) OR (pulmonary disease)) AND ((bone fractures) OR (ulcers) OR (wound healing disorders)) AND ((drugs formulated in polysorbate 80) OR (study drugs)) AND ((unable to comply with the requirements of the protocol) OR (unwilling to comply with the requirements of the protocol)) AND ((surgical procedure Major) OR (traumatic injury significant)) AND ((carcinoma in situ of the cervix appropriately treated) OR (non-melanoma skin carcinoma) OR (uterine cancer)) AND ((locally advanced) OR (metastatic) OR (unresectable)) AND ((require therapy) OR (symptomatic) OR (untreated)) AND ((other therapy to control symptoms) OR (radiation) OR (surgery)) AND ((Doxorubicin) OR (liposomal doxorubicin)) AND ((congestive heart failure symptomatic) OR (ventricular arrhythmia requiring treatment)))"}
{"candidate_id": "LLM02491", "doc_id": "NCT03096613_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older, male or female. Systolic heart failure with New York Heart Association (NYHA) class II-III. Left ventricular ejection fraction (LVEF) less than 40% by echocardiography during screening and randomization. SCH (TSH: upper limits of normal (ULN) -10mIU/L, and FT4 level within reference range). Having received standard HF therapy for at least 2 weeks, having reached target dose or max tolerable dose. Provided informed consent.", "candidate_expression": "((18 years or older) AND (Aged) AND (FT4 level) AND (Left ventricular ejection fraction (LVEF)) AND (New York Heart Association (NYHA)) AND (SCH) AND (Systolic heart failure) AND (TSH) AND (class II-III) AND (during screening and randomization) AND (echocardiography) AND (female) AND (for at least 2 weeks) AND (less than 40%) AND (male) AND (max tolerable dose) AND (standard HF therapy) AND (target dose) AND (upper limits of normal (ULN) -10mIU/L) AND (within reference range))"}
{"candidate_id": "LLM02492", "doc_id": "NCT00236340_inc", "case_bucket": "or", "source_criterion": "Pregnant women with abdomen discumfort and ultrasound diagnosis of polyhydramnios (AFI>25cm) Single or twin pregnancies", "candidate_expression": "((AFI >25cm Single) AND (Pregnant) AND (abdomen discumfort) AND (polyhydramnios) AND (pregnancies twin) AND (ultrasound diagnosis) AND (women))"}
{"candidate_id": "LLM02493", "doc_id": "NCT02821819_inc", "case_bucket": "other", "source_criterion": "Premenopausal women 18-35 years old FSH levels < 10 mIU/ml AFC> 10 Regular cycles BMI < 28 Signed informed consent", "candidate_expression": "((18-35 years) AND (< 10 mIU/ml) AND (< 28) AND (> 10) AND (AFC) AND (BMI) AND (FSH levels) AND (Premenopausal) AND (Regular cycles) AND (Signed informed consent) AND (old) AND (women))"}
{"candidate_id": "LLM02494", "doc_id": "NCT00954850_inc", "case_bucket": "or", "source_criterion": "Adults (18 and older) with physiologically confirmed SA or mild-moderate asthma and followed by an asthma specialist for at least 6 months. Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma). Must have good compliance with medications Patients with asthma and COPD.", "candidate_expression": "((18 and older 18 and older) AND (Adults) AND (Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma).) AND (SA) AND (asthma) AND (followed by an asthma specialist for at least 6 months) AND (good compliance) AND (medications) AND ((COPD) OR (asthma)) AND ((mild) OR (moderate)))"}
{"candidate_id": "LLM02495", "doc_id": "NCT03373669_exc", "case_bucket": "or", "source_criterion": "Presence of a significant medical or psychiatric condition (Examples include: Diagnosis and treatment of tuberculosis (TB) or HIV; renal insufficiency; hepatic disease; oral or parenteral medication known to affect the immune function, such as corticosteroids, other immunosuppressant drugs; or behavioural or memory issues) Ever having received oral cholera vaccine. Receipt of an investigational product (within 30 days before vaccination). History of diarrhoea in 7 days prior to first dose of vaccine (defined as =3 unformed loose stools in 24 hours). History of chronic diarrhea (lasting for more than 2 weeks in the past 6 months) Current use of laxatives, antacids, or other agents to lower stomach acidity? Planning to become pregnant in the next 2 years.", "candidate_expression": "((=3) AND (History) AND (Planning to become pregnant in the next 2 years.) AND (Receipt of an investigational product (within 30 days before vaccination).) AND (chronic diarrhea) AND (diarrhoea) AND (first dose of vaccine) AND (in 7 days prior to first dose of vaccine) AND (in the past 6 months) AND (known to affect the immune function) AND (lasting for more than 2 weeks) AND (oral cholera vaccine) AND (other) AND (significant) AND (unformed loose stools in 24 hours) AND ((oral medication) OR (parenteral medication)) AND ((corticosteroids) OR (immunosuppressant drugs)) AND ((behavioural issues) OR (memory issues)) AND ((medical condition) OR (psychiatric condition)) AND ((agents to lower stomach acidity) OR (antacids) OR (laxatives)) AND ((HIV) OR (hepatic disease) OR (renal insufficiency) OR (treatment) OR (tuberculosis (TB))))"}
{"candidate_id": "LLM02496", "doc_id": "NCT00319748_exc", "case_bucket": "or", "source_criterion": "Had/have the following prior/concurrent therapy: Systemic corticosteroids (oral or injectable) within 7 days of first dose of 852A (topical or inhaled steroids are allowed) Investigational drugs/agents within 14 days of first dose of 852A Immunosuppressive therapy, including cytotoxic agents within 14 days of first dose of 852A (nitrosoureas within 30 days of first dose) Drugs known to induce QT interval prolongation and/or induce Torsades de pointes unless best available drug required to treat life-threatening conditions Radiotherapy within 3 weeks of the first dose of 852A Hematopoietic cell transplantation within 4 weeks of first dose of 852A Evidence of active infection within 3 days of first dose of 852A Active fungal infection or pulmonary infiltrates (prior treated disease stable for 2 weeks is allowable) Cardiac ischemia, cardiac arrhythmias or congestive heart failure uncontrolled by medication History of, or clinical evidence of, a condition which, in the opinion of the investigator, could confound the results of the study or put the subject at undue risk Uncontrolled intercurrent or chronic illness Active autoimmune disease requiring immunosuppressive therapy within 30 days Active coagulation disorder not controlled with medication Pregnant or lactating Concurrent malignancy (if in remission, at least 5 years disease free) except for localized (in-situ) disease, basal carcinomas and cutaneous squamous cell carcinomas that have been adequately treated Any history of brain metastases or any other active central nervous system (CNS) disease", "candidate_expression": "((852A) AND (Cardiac ischemia) AND (Drugs known to induce QT interval prolongation) AND (Drugs known to induce Torsades de pointes) AND (Evidence within 3 days of first dose) AND (Hematopoietic cell transplantation within 4 weeks of first dose) AND (History) AND (Immunosuppressive therapy within 14 days of first dose) AND (Investigational drugs/agents within 14 days of first dose) AND (Pregnant) AND (Radiotherapy within 3 weeks of the first dose) AND (Systemic corticosteroids within 7 days of first dose oral injectable) AND (active infection) AND (any other central nervous system (CNS) disease active) AND (autoimmune disease Active requiring) AND (basal carcinomas) AND (brain metastases) AND (cardiac arrhythmias) AND (chronic illness) AND (clinical evidence) AND (coagulation disorder Active controlled with medication) AND (congestive heart failure uncontrolled by medication) AND (could confound the results of the study or put the subject at undue risk a condition which Uncontrolled) AND (cutaneous squamous cell carcinomas) AND (cytotoxic agents) AND (fungal infection) AND (history of) AND (immunosuppressive therapy) AND (inhaled steroids) AND (intercurrent illness) AND (lactating) AND (localized (in-situ) disease) AND (malignancy Concurrent in remission) AND (nitrosoureas within 30 days of first dose) AND (pulmonary infiltrates) AND (topical steroids) AND NOT (prior treated disease stable))"}
{"candidate_id": "LLM02497", "doc_id": "NCT02208739_exc", "case_bucket": "or", "source_criterion": "Patients who had history of systemic antibiotic usage over the previous 4 months Patients who were pregnant Patients who had received non-surgical periodontal treatment within the past 6 months Patients who had received surgical periodontal treatment within the past 12 months Patients who were smokers Patients with a history of stroke or an acute cardiovascular event over the previous 12 months.", "candidate_expression": "((non-surgical periodontal treatment within the past 6 months) AND (pregnant) AND (smokers) AND (surgical periodontal treatment within the past 12 months) AND (systemic antibiotic history over the previous 4 months) AND ((acute cardiovascular event over the previous 12 months) OR (stroke)))"}
{"candidate_id": "LLM02498", "doc_id": "NCT02361892_inc", "case_bucket": "other", "source_criterion": "submucosal, intramural or subserosal leiomyomas, symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain", "candidate_expression": "((infertility) AND (intramural leiomyomas) AND (menometrorrhagia symptoms) AND (menstrual disorder) AND (pelvic pain) AND (submucosal) AND (subserosal leiomyomas))"}
{"candidate_id": "LLM02499", "doc_id": "NCT02609698_exc", "case_bucket": "or", "source_criterion": "Patients with any contraindications or hypersensitivity related to antiplatelet therapy Patients with Acute Myocardial Infarction (ST elevation myocardial infarction, Non ST elevation myocardial infarction) Patients who are anticipated to receive treatment or surgery that may require desisting the administration of antiplatelet therapy for 2 weeks or longer during the period of the clinical trial Chronic total occlusion (CTO) lesions, in-stent restenosis (ISR) Patients experiencing cardiogenic shock Women who are breastfeeding, pregnant, or desiring pregnancy Patients with findings of hemorrhage Patients with a life expectancy of less than 1 year Patients who have received a drug-eluting stent (DES) procedure within the past 6 months Any other patients judged by the investigator to be unsuitable for the trial", "candidate_expression": "((Acute Myocardial Infarction) AND (CTO) AND (DES) AND (ISR) AND (Women who are breastfeeding, pregnant, or desiring pregnancy) AND (antiplatelet therapy) AND (antiplatelet therapy for 2 weeks or longer) AND (cardiogenic shock) AND (drug-eluting stent procedure past 6 months) AND (hemorrhage) AND (life expectancy less than 1 year) AND ((contraindications) OR (hypersensitivity)) AND ((surgery) OR (treatment)) AND ((Chronic total occlusion) OR (in-stent restenosis)) AND ((Non ST elevation myocardial infarction) OR (ST elevation myocardial infarction)))"}
{"candidate_id": "LLM02500", "doc_id": "NCT02312960_inc", "case_bucket": "other", "source_criterion": "Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial", "candidate_expression": "(Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial)"}
```
