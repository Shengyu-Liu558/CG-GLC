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
{"candidate_id": "LLM06726", "doc_id": "NCT02570230_exc", "case_bucket": "or", "source_criterion": "allergy to morphine or ketamine contraindicate to ketamine remain intubated in the postoperative period", "candidate_expression": "((allergy) AND (contraindicate) AND (in the postoperative period) AND (intubated) AND (ketamine) AND (morphine) AND (postoperative period))"}
{"candidate_id": "LLM06727", "doc_id": "NCT01531257_inc", "case_bucket": "or", "source_criterion": "1. Male and female recipients of all races, ≥18 years of age. 2. Patients undergoing primary or subsequent deceased-donor or living donor kidney transplantation. 3. Subject and/or guardian must be able to provide informed consent. 4. Subject and/or guardian must be able to comply with the study protocol.", "candidate_expression": "((Subject and/or guardian must be able to comply with the study protocol.) AND (Subject and/or guardian must be able to provide informed consent.) AND (age ≥18 years) AND ((Male) OR (female)) AND ((primary) OR (subsequent)) AND ((deceased-donor kidney transplantation) OR (living donor kidney transplantation)))"}
{"candidate_id": "LLM06728", "doc_id": "NCT02330757_exc", "case_bucket": "or", "source_criterion": "PCOS or polycystic ovary on ultrasound scan. Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (endometriosis) AND (ultrasound scan) AND (uterine surgery Previous) AND ((PCOS) OR (polycystic ovary)) AND ((Uterine abnormalities) OR (myoma)) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM06729", "doc_id": "NCT02974660_inc", "case_bucket": "other", "source_criterion": "patients who underwent successful TAVI with any approved TAVI device via transfemoral access with use of any of the approved vascular closure devices provided written informed consent", "candidate_expression": "((TAVI) AND (TAVI device) AND (provided written informed consent) AND (successful) AND (transfemoral access) AND (vascular closure devices))"}
{"candidate_id": "LLM06730", "doc_id": "NCT00787254_exc", "case_bucket": "or", "source_criterion": "Endoscopically confirmed gastric and/or duodenal ulcers on Day 1. Endoscopically confirmed active upper gastrointestinal hemorrhage on Day 1. Current or past history of aspirin-induced asthma or hypersensitivity to NSAIDs. Past or planned surgery affecting gastric acid secretion. Clinically significant hepatic or renal disorder. Serious cardiac dysfunction, hypertension, or hematological disorder.", "candidate_expression": "((Clinically significant) AND (Day 1) AND (Endoscopically) AND (Endoscopically confirmed) AND (NSAIDs) AND (Past) AND (Serious) AND (active) AND (affecting gastric acid secretion) AND (aspirin) AND (aspirin-induced) AND (on Day 1) AND (planned) AND (surgery) AND (upper gastrointestinal hemorrhage) AND ((duodenal ulcers) OR (gastric)) AND ((asthma) OR (hypersensitivity to NSAIDs)) AND ((Current) OR (past history)) AND ((hepatic disorder) OR (renal disorder)) AND ((cardiac dysfunction) OR (hematological disorder) OR (hypertension)))"}
{"candidate_id": "LLM06731", "doc_id": "NCT01856491_inc", "case_bucket": "or", "source_criterion": "Willing and capable of providing informed consent Has an indication for implantation of a single or dual chamber ICD or CRT-D system in their respective geography Subjects planned to be implanted with the RELIANCE 4-FRONT Passive Fixation Lead Willing and capable of participating in all testing/ visits associated with this clinical study at an approved clinical study center and at the intervals defined by this protocol Age 18 or above, or of legal age to give informed consent specific to state and national law", "candidate_expression": "((Age 18 or above of legal age) AND (CRT-D system implantation of a) AND (RELIANCE 4-FRONT Passive Fixation Lead) AND (Willing and capable of providing informed consent) AND (chamber ICD implantation of a single) AND (dual chamber ICD implantation of a) AND (implanted with the RELIANCE 4-FRONT Passive Fixation Lead) AND (planned))"}
{"candidate_id": "LLM06732", "doc_id": "NCT02763007_inc", "case_bucket": "or", "source_criterion": "Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations. Male, or female, 19 years to 75 years. Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study Subjects completed PEAK can be included within 30 days after End Of the Study Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study.", "candidate_expression": "((19 years to 75) AND (Completed \"ALO-IIT-012(PEAK study)\", without major protocol deviations) AND (Female with childbearing potential who has a negative urine pregnancy test result at study start and willing to continue practice appropriate birth control during the entire duration of study) AND (Male) AND (Subjects completed PEAK can be included if their treatment is the same as randomized even after 30 days of End Of the Study) AND (Subjects completed PEAK can be included within 30 days after End Of the Study) AND (female) AND (years))"}
{"candidate_id": "LLM06733", "doc_id": "NCT03389061_inc", "case_bucket": "other", "source_criterion": "Patients with SOF/VEL treatment for the treatment of chronic HCV genotype 1 through 6. Patient is at least 18 at the day of screening. Patient is able and willing to sign the Informed Consent Form. Patient is able and willing to follow protocol requirements.", "candidate_expression": "((1 through 6) AND (HCV genotype) AND (Patient is able and willing to follow protocol requirements) AND (Patient is able and willing to sign the Informed Consent Form) AND (SOF/VEL treatment) AND (at least 18 at the day of screening) AND (chronic) AND (screening))"}
{"candidate_id": "LLM06734", "doc_id": "NCT02429765_inc", "case_bucket": "scope", "source_criterion": "Moderate to severe COPD (post-bronchodilator forced expiratory volume in 1 s (FEV1) 30-79%predicted); Resting functional residual capacity (FRC) >120% predicted; Clinically stable and on stable triple therapy with an ICS/LABA and tiotropium; Symptomatic: Baseline Dyspnea Index =8 and answer \"in the morning\" when asked about what time of day their COPD symptoms are worst.", "candidate_expression": "((Baseline Dyspnea Index =8) AND (COPD Moderate to severe) AND (Clinically stable) AND (ICS/LABA) AND (Resting functional residual capacity (FRC) >120% predicted) AND (forced expiratory volume in 1 s (FEV1) post-bronchodilator 30-79%predicted) AND (stable triple therapy) AND (tiotropium) AND (what time of day their COPD symptoms are worst in the morning))"}
{"candidate_id": "LLM06735", "doc_id": "NCT02316886_exc", "case_bucket": "or", "source_criterion": "Patients in whom the preferred treatment is CABG(Coronary artery bypass grafting) Stented lesion Bypass graft lesion The patients who have more than or equal to 3 target lesions 2 target lesions in the same coronary territory Heavily calcified or angulated lesion Bifurcation lesion requiring 2 stenting technique Contraindication to or planned discontinuation of dual antiplatelet therapy within 1 year Life expectancy less than 2 years Planned cardiac surgery or planned major non cardiac surgery Woman who are breastfeeding, pregnant or planning to become pregnant during the course of the study", "candidate_expression": "((Bifurcation lesion) AND (Bypass graft) AND (CABG) AND (Contraindication planned discontinuation) AND (Coronary artery bypass grafting) AND (Life expectancy less than 2 years) AND (Stented) AND (Woman) AND (breastfeeding) AND (cardiac surgery Planned) AND (dual antiplatelet therapy within 1 year) AND (lesion) AND (lesion angulated) AND (non cardiac surgery planned major) AND (pregnant) AND (pregnant planning to become) AND (stenting technique 2) AND (target lesions 2 in the same coronary territory Heavily calcified) AND (target lesions more than or equal to 3))"}
{"candidate_id": "LLM06736", "doc_id": "NCT03355326_exc", "case_bucket": "or", "source_criterion": "Neurological Congenital malformations and/or those known to impair intestinal motility Additional congenital gastrointestinal abnormalities requiring surgical intervention Congenital Cyanotic heart disease Surgical Closure of abdominal wall defect with prosthetic material (e.g. prosthetic or bio-prosthetic mesh)", "candidate_expression": "((Cyanotic heart disease Congenital) AND (Surgical Closure) AND (abdominal wall defect) AND (gastrointestinal abnormalities Additional congenital) AND (prosthetic material) AND (surgical intervention requiring) AND ((Neurological Congenital malformations) OR (impair intestinal motility)) AND ((bio-prosthetic mesh) OR (prosthetic mesh)))"}
{"candidate_id": "LLM06737", "doc_id": "NCT02092467_inc", "case_bucket": "or", "source_criterion": "Moderate to severe rheumatoid arthritis Taking methotrexate without adequate control of symptoms Have at least one cardiovascular risk factor (eg, current smoker, high blood pressure, high cholesterol levels, diabetes mellitus, history of heart attack, family history of coronary heart disease, extra-articular RA disease)", "candidate_expression": "((RA disease extra-articular) AND (cardiovascular risk factor at least one) AND (coronary heart disease family history) AND (diabetes mellitus) AND (heart attack history) AND (high blood pressure) AND (high cholesterol levels) AND (methotrexate) AND (rheumatoid arthritis Moderate to severe) AND (smoker current) AND NOT (adequate control of symptoms))"}
{"candidate_id": "LLM06738", "doc_id": "NCT00094861_inc", "case_bucket": "or", "source_criterion": "Patients with a histologically or cytologically proven diagnosis of NSCLC Unresectable (locally advanced) stage IIIa or IIIb disease Initial radiotherapy field of treatment to encompass greater than or equal to 30% of the esophagus Life expectancy greater than or equal to 6 months Estimated weight loss less than or equal to 10% in the 3 months before study randomization Measurable disease 18 years of age or older Eastern Cooperative Oncology Group (ECOG) performance status of 0 - 2 Hemoglobin (hgb) greater than or equal to 10 g/dL without transfusional support or growth factor use in the 4 weeks before study randomization Absolute neutrophil count (ANC) greater than or equal to 1.5 x 10^9/L without growth factor use in the 2 weeks before study randomization Platelet count greater than or equal to 100 x 10^9/L Serum bilirubin less than or equal to 1.5 x institutional upper limit of normal (ULN) Serum creatinine less than or equal to 2.0 mg/dL (Note: Patients with a serum creatinine greater than or equal to 1.4 and less than or equal to 2.0 mg/dL must demonstrate a 24-hour urinary creatinine clearance greater than or equal to 50 mL/min) Females of childbearing potential: negative serum or urine pregnancy test Patient must give written informed consent before participating in any study-specific procedure, randomization, or receiving investigational product. Patients with reproductive capability must agree to practice adequate contraception methods.", "candidate_expression": "((0 - 2) AND (18 years or older) AND (24-hour urinary creatinine clearance) AND (3 months before study randomization) AND (ANC) AND (Absolute neutrophil count) AND (ECOG) AND (Eastern Cooperative Oncology Group performance status) AND (Estimated weight loss) AND (Females) AND (Hemoglobin) AND (Initial) AND (Life expectancy) AND (Measurable disease) AND (NSCLC) AND (Platelet count) AND (Serum bilirubin) AND (Serum creatinine) AND (Unresectable) AND (adequate) AND (age) AND (before participating in any study-specific procedure, randomization, or receiving investigational product) AND (childbearing potential) AND (contraception methods) AND (esophagus) AND (growth factor use) AND (hgb) AND (in the 2 weeks before study randomization) AND (in the 4 weeks before study randomization) AND (informed consent) AND (less than) AND (locally advanced) AND (negative) AND (participating in any study-specific procedure, randomization, or receiving investigational product) AND (radiotherapy) AND (reproductive capability) AND (serum creatinine) AND (study randomization) AND (without) AND ((equal to 30%) OR (greater than 30)) AND ((equal to 6 months) OR (greater than 6 months)) AND ((cytologically proven) OR (histologically proven)) AND ((equal to 10%) OR (less than 10%)) AND ((equal to 10 g/dL) OR (greater than 10 g/dL)) AND ((growth factor use) OR (transfusional support)) AND ((equal to 1.5 x 10^9/L) OR (greater than 1.5 x 10^9/L)) AND ((equal to 100 x 10^9/L) OR (greater than 100 x 10^9/L)) AND ((equal to 1.5 x institutional upper limit of normal (ULN)) OR (less than 1.5 x institutional upper limit of normal (ULN))) AND ((stage IIIa disease) OR (stage IIIb disease)) AND ((2.0 mg/dL) OR (equal to 2.0 mg/dL)) AND ((equal to 1.4 mg/dL) OR (greater than 1.4 mg/dL)) AND ((equal to 2.0 mg/dL) OR (less than 2.0 mg/dL)) AND ((equal to 50 mL/min) OR (greater than 50 mL/min)) AND ((serum pregnancy test) OR (urine pregnancy test)) AND ((investigational product) OR (procedure) OR (randomization) OR (study-specific)))"}
{"candidate_id": "LLM06739", "doc_id": "NCT00679341_inc", "case_bucket": "or", "source_criterion": "Histologically or cytologically confirmed adenocarcinoma of the breast with locally advanced or metastatic disease, and a candidate for chemotherapy. Human epidermal growth factor receptor 2 (HER2)-positive. No prior chemotherapy for their metastatic breast cancer (MBC). Measurable disease. Age ≥ 18 years. For women of childbearing potential and men with partners of childbearing potential, agreement to use a highly effective, non-hormonal form of contraception or 2 effective forms of non-hormonal contraception by the patient and/or partner. Contraception use must continue for the duration of study treatment and for at least 6 months after the last dose of study treatment. Male patients whose partners are pregnant should use condoms for the duration of the study.", "candidate_expression": "((Age ≥ 18 years) AND (Contraception continue for the duration of study treatment for at least 6 months after the last dose of study treatment) AND (Human epidermal growth factor receptor 2 (HER2) positive) AND (Male) AND (Measurable disease) AND (adenocarcinoma of the breast) AND (candidate for chemotherapy) AND (chemotherapy) AND (childbearing potential) AND (condoms for the duration of the study) AND (disease locally advanced) AND (men) AND (metastatic breast cancer (MBC)) AND (metastatic disease) AND (partners are pregnant) AND (with partners of childbearing potential) AND (women) AND NOT (chemotherapy prior) AND ((Histologically confirmed) OR (cytologically confirmed)) AND ((contraception highly effective non-hormonal) OR (non-hormonal contraception 2)))"}
{"candidate_id": "LLM06740", "doc_id": "NCT03198910_inc", "case_bucket": "or", "source_criterion": "Patients with pulmonary arterial hypertension (PAH) Patients with chronic thromboembolic pulmonary hypertension (CTEPH) All prevalent patients (diagnosed >12 month ago) with PAH or distal CTEPH who had a consultation at the PH centre in Zurich between November 2015 and November 2016)", "candidate_expression": "((>12 month ago) AND (Zurich) AND (between November 2015 and November 2016) AND (chronic thromboembolic pulmonary hypertension (CTEPH)) AND (consultation at the PH centre) AND (distal) AND (pulmonary arterial hypertension (PAH)) AND ((CTEPH) OR (PAH)))"}
{"candidate_id": "LLM06741", "doc_id": "NCT03185130_exc", "case_bucket": "other", "source_criterion": "Pregnant Meningeal signs are present Acute angle closure glaucoma is suspected Head trauma within the previous two weeks Lumbar puncture within the previous two weeks Thunderclap onset of the headache Known allergy to one of the study drugs History of intracranial hypertension Is a prisoner Patient declined informed consent Non-English speaking patient or parent/guardian for pediatric patients Attending provider excludes patient Severe Dehydration", "candidate_expression": "((Acute angle closure glaucoma suspected) AND (Dehydration Severe) AND (Head trauma within the previous two weeks) AND (Lumbar puncture within the previous two weeks) AND (Meningeal signs) AND (Pregnant) AND (Thunderclap onset) AND (allergy) AND (declined) AND (headache) AND (informed consent) AND (intracranial hypertension History) AND (prisoner) AND (study drugs))"}
{"candidate_id": "LLM06742", "doc_id": "NCT01824537_exc", "case_bucket": "or", "source_criterion": "Volunteers must not have been vaccinated against HPV-Gardasil-9 (both partners) Any history of cervical, penile, oral or anal cancers Being pregnant or plan on immediately becoming pregnant", "candidate_expression": "((Any history) AND (HPV-Gardasil-9) AND (anal cancers) AND (cancers cervical) AND (have been) AND (not) AND (oral cancers) AND (penile cancers) AND (plan on immediately becoming) AND (pregnant) AND (vaccinated))"}
{"candidate_id": "LLM06743", "doc_id": "NCT03213834_inc", "case_bucket": "or", "source_criterion": "CPPE along with evidence of septated pleural effusion on pleural ultrasonography and/or chest CT scan empyema.", "candidate_expression": "((CPPE) AND (chest CT scan) AND (empyema) AND (pleural ultrasonography) AND (septated pleural effusion evidence of))"}
{"candidate_id": "LLM06744", "doc_id": "NCT03335436_exc", "case_bucket": "or", "source_criterion": "use illicit drugs or relapse during the last trimester of pregnancy positive drug screen at the time of delivery allergies to any medications used in the study taking prescribed gabapentin at the time of admission for CD contraindications to neuraxial anesthesia or require general anesthesia for CD designated ASA physical status 4 or above", "candidate_expression": "((4 or above) AND (ASA physical status) AND (CD) AND (admission) AND (admission for CD) AND (allergies) AND (at the time of admission for CD) AND (at the time of delivery) AND (contraindications) AND (delivery) AND (drug screen) AND (during the last trimester of pregnancy) AND (gabapentin) AND (general anesthesia) AND (illicit drugs) AND (last trimester) AND (medications used in the study) AND (neuraxial anesthesia) AND (positive) AND (pregnancy) AND (prescribed) AND (relapse) AND (require) AND (the last trimester of pregnancy) AND (the time of delivery))"}
{"candidate_id": "LLM06745", "doc_id": "NCT03323047_inc", "case_bucket": "or", "source_criterion": "Healthy patients aged 3-13 years Level I or level II on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) obstructive sleep apnea or recurrent throat infections undergoing elective tonsillectomy with or without adenoidectomy Parents who agree to complete documentation and follow up at 14 days post-operation.", "candidate_expression": "((American Society of Anesthesiologists (ASA) physical status Level I or level II) AND (Healthy) AND (Parents who agree to complete documentation and follow up at 14 days post-operation.) AND (adenoidectomy) AND (aged 3-13 years) AND (tonsillectomy elective) AND ((obstructive sleep apnea) OR (throat infections recurrent)))"}
{"candidate_id": "LLM06746", "doc_id": "NCT02645474_exc", "case_bucket": "or", "source_criterion": "patients' refusal contraindication to regional anaesthesia (coagulopathies, concurrent anticoagulant therapy, allergy to local anaesthetics, infection at puncture site)", "candidate_expression": "((allergy) AND (anticoagulant therapy) AND (coagulopathies) AND (contraindication) AND (infection puncture site) AND (local anaesthetics) AND (patients' refusal) AND (regional anaesthesia ())"}
{"candidate_id": "LLM06747", "doc_id": "NCT02877485_exc", "case_bucket": "or", "source_criterion": "Intranasal steroid use within the last three months Current systemic steroid use Prior septal surgery Individuals who are pregnant or actively breastfeeding", "candidate_expression": "((Current) AND (Intranasal) AND (Intranasal steroid use) AND (Prior) AND (actively) AND (septal surgery) AND (steroid) AND (systemic) AND (systemic steroid use) AND (within the last three months) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM06748", "doc_id": "NCT02034019_inc", "case_bucket": "other", "source_criterion": "Has a cataract and is expected to undergo clear corneal cataract surgery with phacoemulsification and implantation of a posterior chamber intraocular lens Has a potential post-operative pinhole corrected Snellen VA of at least 20/200 or better in both eyes", "candidate_expression": "((cataract) AND (clear corneal cataract surgery with phacoemulsification implantation of a posterior chamber intraocular lens) AND (pinhole corrected Snellen VA at least 20/200 or better))"}
{"candidate_id": "LLM06749", "doc_id": "NCT02871206_inc", "case_bucket": "other", "source_criterion": "Healthy children aged 6 months to 72 months", "candidate_expression": "((Healthy) AND (aged 6 months to 72 months) AND (children))"}
{"candidate_id": "LLM06750", "doc_id": "NCT03506750_exc", "case_bucket": "or", "source_criterion": "previous retinal vein occlusion. any intraocular surgery within the previous 12 months. myopia of > or = to 8 diopters. active ocular or periocular infection treatment with an investigational agent for any condition 60 days prior to enrollment. evidence of severe cardiac disease. clinically significant peripheral vascular disease (previous surgery, amputation, or symptoms of claudication) uncontrolled hypertension (treated systolic blood pressure > 155 mmHg or diastolic blood pressure > 95 mmHg) stroke within the preceding 12 months.", "candidate_expression": "((cardiac disease evidence of severe) AND (hypertension uncontrolled) AND (intraocular surgery within the previous 12 months) AND (myopia > or = to 8 diopters) AND (peripheral vascular disease clinically significant) AND (retinal vein occlusion previous) AND (stroke within the preceding 12 months) AND (treatment with an investigational agent for any condition 60 days prior to enrollment) AND ((amputation) OR (previous surgery) OR (symptoms of claudication)) AND ((diastolic blood pressure > 95 mmHg) OR (systolic blood pressure > 155 mmHg)) AND ((ocular infection) OR (periocular infection)))"}
```
