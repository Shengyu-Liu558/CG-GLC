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
{"candidate_id": "LLM07601", "doc_id": "NCT02350439_exc", "case_bucket": "or", "source_criterion": "1. Left main disease (angiographically> 50%) 2. Cardiogenic shock / hemodynamic instability 3. Previous CABG 4. Increased risk of bradycardia on investigator clinical judgment 5. Severe chronic obstructive pulmonary disease 6. Coronary vessels with tortuosity or extremely calcified 7. Severe left ventricular hypertrophy or severe valvular disease 8. STEMI or non-STEMI within the past five days 9. Previous myocardial infarction in the distribution of the target vessel for the FFR 10. Acute decompensated heart failure.", "candidate_expression": "((> 50%) AND (Acute decompensated heart failure) AND (CABG) AND (Cardiogenic shock) AND (Increased risk) AND (Left main disease) AND (Previous) AND (Severe) AND (bradycardia) AND (chronic obstructive pulmonary disease) AND (hemodynamic instability) AND (in the distribution of the target vessel) AND (investigator clinical judgment) AND (myocardial infarction) AND (within the past five days) AND ((Coronary vessel extremely calcified) OR (Coronary vessel tortuosity)) AND ((left ventricular hypertrophy) OR (severe) OR (valvular disease)) AND ((STEMI) OR (non-STEMI)))"}
{"candidate_id": "LLM07602", "doc_id": "NCT02974660_exc", "case_bucket": "or", "source_criterion": "no consent periprocedural complications requiring continuation of heparin or administration of protamine sulfate alergy to fish, protamine, protamine derivates, history of Humulin N, Novolin N, Novolin NPH, Gensulin N, SciLin N, NPH Iletin II and isophane insulin intake", "candidate_expression": "((Gensulin N) AND (Humulin N) AND (NPH Iletin II) AND (Novolin N) AND (Novolin NPH) AND (SciLin N) AND (alergy) AND (fish) AND (heparin) AND (isophane insulin) AND (no consent) AND (periprocedural complications) AND (protamine) AND (protamine derivates) AND (protamine sulfate))"}
{"candidate_id": "LLM07603", "doc_id": "NCT01700790_inc", "case_bucket": "or", "source_criterion": "Antiretroviral naive Taking Kaletra containing regimen with suppressed viral load. Taking an NNRTI or integrase containing regimen without prior history of use of PI for more than 2 weeks Taking an NNRTI or integrase containing regimen with prior exposure to PI greater than 2 weeks. It must be clearly stated in the source document that PI was switched to another agent for convenience. Taking another PI containing regimens with suppressed viral load. It must be clearly stated in source document that if another PI was used for greater than 2 weeks the regimen was switched to another agent for convenience. Subjects with prior history of PI use may be enrolled, if there is a genotype showing no resistance to Kaletra Other Inclusion criteria Be at least 18 years of age and able to give informed consent. Diagnosed with TB by criteria per Brazilian Ministry of Health Have a good clinical response to TB. Tolerating tuberculosis therapy containing rifampin for the 2 weeks prior to screening,except for persons taking protease inhibitors at time of diagnosis of TB.,. Subjects taking protease inhibitors will be screened and initiate visit 1 within 3 days of starting TB medication HIV positive with documentation present in source document. Have a CD4 cell count greater than 50 cells/mm3if not taking ART. Persons with cd4 < 50 may be enrolled, if it is felt that in the best interest of the patient, that enrollment in the study will allow for quicker initiation of antiretroviral therapy than referral to another treatment center.", "candidate_expression": "((ART) AND (Antiretroviral) AND (CD4 cell count) AND (HIV) AND (HIV positive) AND (Kaletra) AND (NNRTI) AND (PI) AND (TB) AND (able to give informed consent) AND (age) AND (at least 18 years) AND (at time of diagnosis of TB) AND (criteria per Brazilian Ministry of Health) AND (except) AND (for more than 2 weeks) AND (for the 2 weeks prior to screening) AND (good clinical response) AND (greater than 2 weeks) AND (greater than 50 cells/mm3) AND (integrase) AND (naive) AND (not) AND (positive) AND (prior) AND (protease inhibitors) AND (regimen) AND (regimens) AND (rifampin) AND (screening) AND (suppressed) AND (time of diagnosis of TB) AND (tuberculosis) AND (tuberculosis therapy) AND (viral load) AND (without))"}
{"candidate_id": "LLM07604", "doc_id": "NCT03323047_inc", "case_bucket": "or", "source_criterion": "Healthy patients aged 3-13 years Level I or level II on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) obstructive sleep apnea or recurrent throat infections undergoing elective tonsillectomy with or without adenoidectomy Parents who agree to complete documentation and follow up at 14 days post-operation.", "candidate_expression": "((3-13 years) AND (American Society of Anesthesiologists (ASA) physical status) AND (Healthy) AND (Level I or level II) AND (Parents who agree to complete documentation and follow up at 14 days post-operation.) AND (adenoidectomy) AND (aged) AND (elective) AND (obstructive sleep apnea) AND (recurrent) AND (throat infections) AND (tonsillectomy))"}
{"candidate_id": "LLM07605", "doc_id": "NCT03247413_inc", "case_bucket": "or", "source_criterion": "patients with a diagnosis of either cervical, thoracic, or lumbar facet or sacroiliac joint pain who have responded to medial branch blocks and are already scheduled for bilateral radiofrequency ablations age greater than 18 years old English speaking", "candidate_expression": "((English speaking) AND (age) AND (bilateral radiofrequency ablations) AND (cervical joint pain) AND (greater than 18 years old) AND (lumbar facet joint pain) AND (medial branch blocks) AND (responded) AND (sacroiliac joint pain) AND (scheduled for) AND (thoracic joint pain))"}
{"candidate_id": "LLM07606", "doc_id": "NCT00894712_inc", "case_bucket": "or", "source_criterion": "Must have pathologically confirmed invasive adenocarcinoma or ductal carcinoma in situ of the breast. Patients must have undergone segmental mastectomy (i.e., lumpectomy). Patients must not have received prior radiation therapy to the breast. Patients must not have active local-regional disease prior to registration. Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy. Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment. All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.", "candidate_expression": "((All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.) AND (Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy.) AND (Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment.) AND (active) AND (confirmed) AND (ductal carcinoma in situ) AND (invasive adenocarcinoma) AND (local-regional disease) AND (lumpectomy) AND (not) AND (of the breast) AND (pathologically) AND (radiation therapy) AND (segmental mastectomy))"}
{"candidate_id": "LLM07607", "doc_id": "NCT03129555_exc", "case_bucket": "or", "source_criterion": "A prescription of a NOAC within 90 days prior to hospitalization or outpatient clinic visit for VTE. Patients with NOAC preference apart from preference consistent with current cluster randomized NOAC. Other contraindications mentioned in the \"Summary of Product Characteristics\" for the respective NOAC.", "candidate_expression": "((NOAC) AND (NOAC preference) AND (NOAC within 90 days prior to hospitalization or outpatient clinic visit for VTE) AND (VTE) AND (contraindications Other Summary of Product Characteristics) AND (hospitalization) AND (outpatient clinic) AND ((hospitalization) OR (outpatient clinic visit)))"}
{"candidate_id": "LLM07608", "doc_id": "NCT02779374_inc", "case_bucket": "scope", "source_criterion": "Women with POI: For the purpose of the research women is considered to have POI if she is aged less than 40 years and has amenorrhea of at least 4 month with FSH level above 25 IU/L (repeated twice >4 weeks apart).", "candidate_expression": "((FSH level above 25 IU/L repeated twice) AND (POI) AND (Women) AND (aged less than 40 years) AND (amenorrhea at least 4 month))"}
{"candidate_id": "LLM07609", "doc_id": "NCT00886158_exc", "case_bucket": "other", "source_criterion": "Lack of consent", "candidate_expression": "(Lack of consent)"}
{"candidate_id": "LLM07610", "doc_id": "NCT02117986_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding patients patient with a history of hypersensitivity to colistin", "candidate_expression": "((breastfeeding) AND (colistin) AND (hypersensitivity history of) AND (pregnant))"}
{"candidate_id": "LLM07611", "doc_id": "NCT01175044_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo revision total knee arthroplasty", "candidate_expression": "(revision total knee arthroplasty)"}
{"candidate_id": "LLM07612", "doc_id": "NCT02701777_exc", "case_bucket": "or", "source_criterion": "Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease Any debilitating disease prior to the SCI that caused exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold (see appendix 2) Pregnant females Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida, MS, or herniated disk Individuals with scalp shrapnel, cochlear implants, or aneurysm clips.", "candidate_expression": "((History) AND (MS) AND (Metal plate in skull) AND (Pregnant) AND (Premorbid) AND (Uncontrolled) AND (altered cognitive status) AND (aneurysm clips) AND (cardiovascular disease) AND (cochlear implants) AND (cord compression) AND (debilitating disease) AND (drugs acting primarily on the central nervous system) AND (exercise intolerance) AND (females) AND (head injury) AND (herniated disk) AND (lower the seizure threshold) AND (major depression) AND (medical problems) AND (ongoing) AND (orthopedic disease) AND (prior to the SCI) AND (psychosis) AND (pulmonary disease) AND (scalp shrapnel) AND (seizures) AND (spina bifida) AND (spinal cord) AND (spinal cord disease) AND (spinal stenosis) AND (stroke) AND (syrinx) AND (the SCI))"}
{"candidate_id": "LLM07613", "doc_id": "NCT01711801_exc", "case_bucket": "or", "source_criterion": "History or presence of any clinically significant disease or disorder Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator History of clinically significant hypersensitivity or allergic drug reactions Any suspicion or history of alcohol abuse and/or consumption of other drugs of abuse Regular smoker (> 5 cigarettes, > 1 pipeful or > 1 cigar per day) Positive for hepatitis B, hepatitis C or HIV infection Dietary restrictions that would prohibit the consumption of standardized meals Participation in an investigational drug or device study within 90 days prior to screening, as calculated from the follow-up from the previous study", "candidate_expression": "((> 1) AND (> 1 per day) AND (> 5) AND (Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator) AND (Dietary restrictions) AND (HIV infection) AND (History) AND (Positive) AND (Regular smoker) AND (alcohol abuse) AND (allergic drug reactions) AND (cigar) AND (cigarettes) AND (clinically significant) AND (clinically significant disease) AND (clinically significant disease or disorder) AND (clinically significant disorder) AND (consumption of other drugs of abuse) AND (hepatitis B) AND (hepatitis C) AND (history) AND (hypersensitivity) AND (pipeful) AND (suspicion) AND (would prohibit the consumption of standardized meals))"}
{"candidate_id": "LLM07614", "doc_id": "NCT00931983_inc", "case_bucket": "or", "source_criterion": "Children between the ages of 4-18 with incomplete ASIA C or D spinal cord injuries at least 12 months before study enrolment Non-ambulatory or 'exercise only' ambulators with or without assistive devices Normal motor and cognitive development up to time of injury Medical Stability", "candidate_expression": "((4-18) AND (ASIA) AND (C or D) AND (Children) AND (Medical Stability) AND (Normal) AND (ages) AND (assistive devices) AND (at least 12 months before study enrolment) AND (cognitive development) AND (incomplete) AND (motor development) AND (spinal cord injuries) AND (study enrolment) AND (time of injury) AND (up to time of injury) AND (('exercise only' ambulators) OR (Non-ambulatory)))"}
{"candidate_id": "LLM07615", "doc_id": "NCT00894712_inc", "case_bucket": "or", "source_criterion": "Must have pathologically confirmed invasive adenocarcinoma or ductal carcinoma in situ of the breast. Patients must have undergone segmental mastectomy (i.e., lumpectomy). Patients must not have received prior radiation therapy to the breast. Patients must not have active local-regional disease prior to registration. Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy. Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment. All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.", "candidate_expression": "((All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.) AND (Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy.) AND (Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment.) AND (lumpectomy) AND (pathologically confirmed) AND (segmental mastectomy) AND NOT (local-regional disease active) AND NOT (radiation therapy) AND ((ductal carcinoma in situ of the breast) OR (invasive adenocarcinoma of the breast)))"}
{"candidate_id": "LLM07616", "doc_id": "NCT02763007_exc", "case_bucket": "or", "source_criterion": "eGFR(Epidermal growth factor receptor) < 50mL/min AST(aspartate aminotransferase)/ALT(alanine aminotransaminase) >2.5 upper limit of normal Pregnant or lactating women Subject who the investigator deems inappropriate to participate in this study Patients with a history of bladder cancer or patients with active bladder cancer Patients with uninvestigated macroscopic hematuria Patients with cardiac failure or a history of cardiac failure (New York Heart Association [NYHA] Stages 3 to 4) Patients with genetic problems such as galactose intolerance, Lapp lactase deficiency or glucose-galactose malabsorption, since this study drug contains lactose", "candidate_expression": "((3 to 4) AND (< 50mL/min) AND (>2.5 upper limit of normal) AND (ALT) AND (AST) AND (Epidermal growth factor receptor) AND (NYHA) AND (New York Heart Association Stages) AND (Pregnant or lactating women) AND (active) AND (alanine aminotransaminase) AND (aspartate aminotransferase) AND (eGFR) AND (genetic problems) AND (macroscopic hematuria) AND (uninvestigated) AND ((bladder cancer)) AND ((cardiac failure) OR (history of cardiac failure)) AND ((Lapp lactase deficiency) OR (galactose intolerance) OR (glucose-galactose malabsorption)))"}
{"candidate_id": "LLM07617", "doc_id": "NCT02872935_inc", "case_bucket": "other", "source_criterion": "Pregnant American Society of Anesthesiologists risk classification I and II Age > 18 years Non-laboring Patients with elective cesarean sections", "candidate_expression": "((> 18 years) AND (Age) AND (American Society of Anesthesiologists risk classification) AND (I and II) AND (Non-laboring) AND (Pregnant) AND (cesarean sections) AND (elective))"}
{"candidate_id": "LLM07618", "doc_id": "NCT02984228_inc", "case_bucket": "other", "source_criterion": "English speaking/literate Age 18-100 years Visual analog score pain >= 5 Greater than or equal to 3 months of pain after onset of symptoms that has failed conservative treatments Confirmation of glenohumeral OA via imaging Transient relief of symptoms after diagnostic intra-articular injection into the glenohumeral joint", "candidate_expression": "((Age 18-100 years) AND (English speaking/literate) AND (Visual analog score pain >= 5) AND (conservative treatments failed) AND (glenohumeral OA) AND (imaging) AND (intra-articular injection glenohumeral joint) AND (pain Greater than or equal to 3 months after onset of symptoms) AND (relief of symptoms Transient))"}
{"candidate_id": "LLM07619", "doc_id": "NCT03211741_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding (pregnancy defined as the state of a female after conception until the termination of gestation, confirmed by a positive human chorionic gonadotropin laboratory test (> 5mIU/mL) Women of child bearing potential must be practicing effective contraception implemented during the trial and for at least 28 days following the last dose of study medication Tromboembolic event (CVA or transient ischemic attack, AMI) less than 3 months prior to the intravitreal injection of bevacizumab History of hypersensitivity for bevacizumab.", "candidate_expression": "((> 5mIU/mL) AND (AMI) AND (CVA) AND (History) AND (Tromboembolic event) AND (Women) AND (bevacizumab) AND (breastfeeding) AND (child bearing potential) AND (contraception) AND (during the trial) AND (effective) AND (for at least 28 days following the last dose of study medication) AND (human chorionic gonadotropin) AND (human chorionic gonadotropin laboratory test) AND (hypersensitivity) AND (intravitreal injection) AND (last dose) AND (less than 3 months prior to the intravitreal injection of bevacizumab) AND (positive) AND (pregnant) AND (study medication) AND (the intravitreal injection of bevacizumab) AND (the last dose of study medication) AND (transient ischemic attack))"}
{"candidate_id": "LLM07620", "doc_id": "NCT03345589_exc", "case_bucket": "other", "source_criterion": "Autoimmune hepatitis Primary sclerosing cholangitis", "candidate_expression": "((Autoimmune hepatitis) AND (Primary sclerosing cholangitis))"}
{"candidate_id": "LLM07621", "doc_id": "NCT00599924_exc", "case_bucket": "other", "source_criterion": "Prior treatment with more than 6 cycles of traditional alkylating agent-based chemotherapy regimens Prior treatment with more than 2 cycles of carboplating-based chemotherapy regimens For colorectal cancer patients in the expanded cohorts, prior treatment with more than 2 systemic chemotherapy regimens in the metastatic setting", "candidate_expression": "((chemotherapy regimens Prior alkylating agent-based) AND (chemotherapy regimens Prior carboplating-based) AND (colorectal cancer) AND (systemic chemotherapy regimens prior metastatic) AND (treatment more than 2) AND (treatment more than 2 cycles) AND (treatment more than 6 cycles))"}
{"candidate_id": "LLM07622", "doc_id": "NCT00994786_inc", "case_bucket": "scope", "source_criterion": "Must be an outpatient with a primary DSM-IV Obsessive-Compulsive Disorder. Patients must have a score of greater than 20 on the Yale-Brown Obsessive Compulsive Scale (Y-BOCS; Goodman et al., 1989b). Diagnosis of comorbid DSM-IV major depressive episode will be allowed in the study provided that the diagnosis is secondary to OCD, they have a baseline Montgomery Depression Rating Scale (MADRS) score of less than or equal to 19, and the onset of OCD predates the onset of the current episode of depression by five or more years. The ability to comprehend and comply with protocol requirements. Written consent must be provided prior to study entry. All women of childbearing potential (WOCBP) must be practicing a medically acceptable method of birth control All female subjects of childbearing potential (WOCBP), including those who are practicing a medically acceptable method of birth control, must have a negative serum pregnancy test within 72 hours prior to the start of study medication.", "candidate_expression": "((All female subjects of childbearing potential (WOCBP), including those who are practicing a medically acceptable method of birth control, must have a negative serum pregnancy test within 72 hours prior to the start of study medication) AND (DSM-IV) AND (MADRS) AND (Montgomery Depression Rating Scale) AND (OCD) AND (Obsessive-Compulsive Disorder) AND (The ability to comprehend and comply with protocol requirements) AND (WOCBP) AND (Written consent must be provided prior to study entry.) AND (Y-BOCS) AND (Yale-Brown Obsessive Compulsive Scale) AND (baseline) AND (birth control) AND (childbearing potential) AND (comorbid) AND (major depressive episode) AND (medically acceptable) AND (onset of OCD) AND (onset of the current episode of depression) AND (outpatient) AND (predates the onset of the current episode of depression by five or more years) AND (primary) AND (score of greater than 20) AND (score of less than or equal to 19) AND (women))"}
{"candidate_id": "LLM07623", "doc_id": "NCT02420015_inc", "case_bucket": "other", "source_criterion": "Currently smoke at least ten cigarettes a day Have been smoking for at least one year Meet criteria for schizophrenia, schizoaffective disorder, or another psychotic disorder based on structured clinical interview Can speak and write fluent conversational English Are between 18 and 70 years of age Are willing to make a smoking cessation attempt Score 26 or higher on the Montreal Cognitive Assessment", "candidate_expression": "((Are willing to make a smoking cessation attempt) AND (Montreal Cognitive Assessment 26 or higher) AND (age between 18 and 70 years) AND (psychotic disorder) AND (schizoaffective disorder) AND (schizophrenia) AND (smoke at least ten cigarettes a day) AND (smoking at least one year))"}
{"candidate_id": "LLM07624", "doc_id": "NCT02186782_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulation/oligoovulation. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Metabolic or hormonal abnormalities.", "candidate_expression": "((< 18.5 kg/m2) AND (< 20) AND (> 25 kg/m2) AND (> 35 years) AND (Age) AND (BMI) AND (Body mass index) AND (Metabolic abnormalities) AND (anovulation) AND (cytotoxic drugs) AND (hormonal abnormalities) AND (infertility factor) AND (oligoovulation) AND (one) AND (other than) AND (ovarian surgery) AND (ovary) AND (pelvic irradiation) AND (surgical removal))"}
{"candidate_id": "LLM07625", "doc_id": "NCT02961582_inc", "case_bucket": "or", "source_criterion": "An average defecation frequency (DF) of <3 per week based on a 3-week defecation diary (patient-reported) Meet at least one other criterion of the Rome-IV criteria for idiopathic constipation based on the 3-week defecation diary (1) Refractory to conservative treatment Age: 14-80 years Straining during =25% of defecations Lumpy or hard stools in =25% of defecations Sensation of incomplete evacuation for =25% of defecations Sensation of anorectal obstruction/blockage for =25% of defecations Manual manoeuvres to facilitate =25% of defecations", "candidate_expression": "((14-80 years) AND (3-week defecation diary) AND (<3 per week) AND (=25%) AND (Age) AND (DF) AND (Manual manoeuvres) AND (Refractory) AND (Rome-IV criteria for idiopathic constipation) AND (Sensation of incomplete evacuation) AND (Straining) AND (at least one) AND (average defecation frequency) AND (conservative treatment) AND (criterion) AND (defecations) AND (idiopathic constipation) AND (other) AND (patient-reported) AND ((Lumpy stools) OR (hard stools)) AND ((Sensation of anorectal blockage) OR (Sensation of anorectal obstruction)))"}
```
