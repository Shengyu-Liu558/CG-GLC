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
{"candidate_id": "LLM00751", "doc_id": "NCT03177811_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((COPD exacerbation) AND (COPD very severe) AND (Comorbidities) AND (hypoxemia low altitude) AND ((coronary artery disease) OR (systemic arterial hypertension unstable)) AND ((OSA) OR (cardiovascular disease uncontrolled) OR (pneumothorax in the last 2 months) OR (stroke previous)) AND ((Internal disease) OR (heavy smoking >20 cigarettes per day) OR (neurologic disease) OR (psychiatric disease) OR (rheumatologic disease)) AND ((allergy) OR (renal failure)) AND ((acetazolamide) OR (sulfonamides)) AND ((FEV1 <40% predicted) OR (FEV1/FVC <0.7) OR (oxygen saturation room air <92% at 750 m)))"}
{"candidate_id": "LLM00752", "doc_id": "NCT01807897_exc", "case_bucket": "or", "source_criterion": "Hospitalization for acute decompensated HF within previous 30 days Hospitalization for myocardial infarction or cardiac surgery within previous 90 days Presence of a left ventricular assist device History of heart transplantation Poorly controlled hypertension (>170/>110) Poorly controlled diabetes (HbA1c > 9.0) Severe renal failure with estimated glomerular filtration rate <30 ml/min Prior stroke with functional impairment or other severe, uncontrolled medical problems that may impair ability to participate in the study exams, based on medical history and review of medical records Severe chronic insomnia, with reported usual sleep duration <4 hours Severe daytime sleepiness, defined as Epworth Sleepiness Scale score 18 or higher or a report of falling asleep driving during the previous year, and deemed a safety risk by study physician Awake resting oxyhemoglobin saturation <89% Pregnancy Smoking by subject or other person in the subject's bedroom, or other open flame in bedroom Current use of a positive airway pressure device (including continuous or bi-level positive airway pressure or adaptive servo-ventilation) or supplemental oxygen therapy", "candidate_expression": "((Epworth Sleepiness Scale score 18 or higher) AND (HbA1c > 9.0) AND (Hospitalization) AND (Hospitalization within previous 30 days) AND (Pregnancy) AND (acute decompensated HF) AND (chronic insomnia sleep duration) AND (daytime sleepiness) AND (diabetes Poorly controlled) AND (estimated glomerular filtration rate <30 ml/min) AND (functional impairment) AND (heart transplantation) AND (hypertension Poorly controlled) AND (left ventricular assist device) AND (oxyhemoglobin saturation Awake resting <89%) AND (renal failure Severe) AND (stroke) AND ((positive airway pressure device) OR (supplemental oxygen therapy)) AND ((adaptive servo-ventilation) OR (bi-level positive airway pressure) OR (continuous airway pressure)) AND ((cardiac surgery) OR (myocardial infarction)))"}
{"candidate_id": "LLM00753", "doc_id": "NCT01807897_exc", "case_bucket": "or", "source_criterion": "Hospitalization for acute decompensated HF within previous 30 days Hospitalization for myocardial infarction or cardiac surgery within previous 90 days Presence of a left ventricular assist device History of heart transplantation Poorly controlled hypertension (>170/>110) Poorly controlled diabetes (HbA1c > 9.0) Severe renal failure with estimated glomerular filtration rate <30 ml/min Prior stroke with functional impairment or other severe, uncontrolled medical problems that may impair ability to participate in the study exams, based on medical history and review of medical records Severe chronic insomnia, with reported usual sleep duration <4 hours Severe daytime sleepiness, defined as Epworth Sleepiness Scale score 18 or higher or a report of falling asleep driving during the previous year, and deemed a safety risk by study physician Awake resting oxyhemoglobin saturation <89% Pregnancy Smoking by subject or other person in the subject's bedroom, or other open flame in bedroom Current use of a positive airway pressure device (including continuous or bi-level positive airway pressure or adaptive servo-ventilation) or supplemental oxygen therapy", "candidate_expression": "((<30 ml/min) AND (<4 hours) AND (<89%) AND (> 9.0) AND (Awake) AND (Epworth Sleepiness Scale) AND (HbA1c) AND (Hospitalization) AND (Poorly controlled) AND (Pregnancy) AND (Severe) AND (acute decompensated HF) AND (chronic insomnia) AND (daytime sleepiness) AND (diabetes) AND (estimated glomerular filtration rate) AND (functional impairment) AND (heart transplantation) AND (hypertension) AND (left ventricular assist device) AND (oxyhemoglobin saturation) AND (renal failure) AND (resting) AND (score 18 or higher) AND (sleep duration) AND (stroke) AND (within previous 30 days) AND (within previous 90 days) AND ((positive airway pressure device) OR (supplemental oxygen therapy)) AND ((adaptive servo-ventilation) OR (bi-level positive airway pressure) OR (continuous airway pressure)) AND ((cardiac surgery) OR (myocardial infarction)))"}
{"candidate_id": "LLM00754", "doc_id": "NCT03352869_inc", "case_bucket": "or", "source_criterion": "Overweight and obese PCOS patients with newly diagnosed IGR; PCOS diagnosis based on 2003 Rotterdam criteria Overweight / obesity diagnostic criteria according to WHO-WPR Impaired glucose regulation diagnostic criteria according to 1998 WHO diagnostic criteria.", "candidate_expression": "((IGR newly diagnosed) AND (Impaired glucose regulation 1998 WHO diagnostic criteria) AND (PCOS) AND (PCOS 2003 Rotterdam criteria) AND ((Overweight) OR (obese)) AND ((Overweight) OR (obesity)))"}
{"candidate_id": "LLM00755", "doc_id": "NCT02689024_inc", "case_bucket": "other", "source_criterion": "adult patients aged = 55 years with a radiographically confirmed hip fracture", "candidate_expression": "((= 55 years) AND (adult) AND (aged) AND (hip fracture) AND (radiographically))"}
{"candidate_id": "LLM00756", "doc_id": "NCT02469610_exc", "case_bucket": "other", "source_criterion": "Previous thoracic operation in the same side.", "candidate_expression": "((Previous) AND (same side) AND (thoracic operation))"}
{"candidate_id": "LLM00757", "doc_id": "NCT02467686_exc", "case_bucket": "or", "source_criterion": "Women did not have breast cancer do not use tamoxifen or aromatase inhibitor not in menopause and not have hot flashes", "candidate_expression": "(NOT (breast cancer) AND (NOT (hot flashes) OR NOT (menopause)) AND ((aromatase inhibitor) OR (tamoxifen)))"}
{"candidate_id": "LLM00758", "doc_id": "NCT03354572_inc", "case_bucket": "other", "source_criterion": "Subjects scheduled for laparoscopic unilateral inguinal hernia repair ASA 1 or2. Age >18 years.", "candidate_expression": "((ASA 1 or2) AND (Age >18 years) AND (inguinal hernia repair scheduled laparoscopic unilateral))"}
{"candidate_id": "LLM00759", "doc_id": "NCT03497598_exc", "case_bucket": "or", "source_criterion": "UTIs = 12 within 1 year Pregnancy or Lactation Immune disease Lactose intolerance Urinary tract anomaly Systemic infection Newly started hormone therapy within the last 6 months Antibiotic prophylaxis within the last 6 months a-D-mannose intake within the last month Use of catheters Diabetes mellitus Participation to other studies", "candidate_expression": "((Antibiotic) AND (Antibiotic prophylaxis within the last 6 months) AND (Diabetes mellitus) AND (Immune disease) AND (Lactose) AND (Lactose intolerance) AND (Participation to other studies) AND (Systemic infection) AND (UTIs 12 within 1 year within 1 year) AND (Urinary tract anomaly) AND (a-D-mannose within the last month) AND (catheters) AND (hormone therapy Newly started within the last 6 months) AND (intolerance) AND ((Lactation) OR (Pregnancy)))"}
{"candidate_id": "LLM00760", "doc_id": "NCT03099408_exc", "case_bucket": "or", "source_criterion": "Presence of another vaginal infection or STD Allergy to metronidazole Pregnant or nursing Use of oral or intravaginal antibiotics within the past 2 weeks HIV or other chronic disease Inability to keep return appointments Contraindications for Lactobacillus Vaginal Suppositories(those without sexual history)", "candidate_expression": "((Allergy) AND (Contraindications) AND (HIV) AND (Inability to keep return appointments) AND (Lactobacillus Vaginal Suppositories) AND (Pregnant) AND (STD) AND (another) AND (chronic disease) AND (intravaginal antibiotics) AND (metronidazole) AND (nursing) AND (oral antibiotics) AND (other) AND (sexual history) AND (vaginal infection) AND (within the past 2 weeks) AND (without))"}
{"candidate_id": "LLM00761", "doc_id": "NCT02731794_inc", "case_bucket": "other", "source_criterion": "patients with severe left ventricle dysfunction with an ejection fraction (EF)=40%, being scheduled for revascularization.", "candidate_expression": "((=40%) AND (being scheduled for) AND (ejection fraction (EF)) AND (left ventricle dysfunction) AND (revascularization) AND (severe))"}
{"candidate_id": "LLM00762", "doc_id": "NCT02490839_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((any kind) AND (bleeding) AND (concomitant) AND (during the course of the ulcer) AND (gastric surgery) AND (history) AND (hypersensitivity) AND (illness) AND (in the previous month) AND (malignant tumor) AND (previous) AND (serious) AND (test drugs) AND (the ulcer) AND (ulcer) AND (woman) AND ((nursing) OR (pregnant)) AND ((PPIs) OR (antibiotics) OR (bismuth salts)))"}
{"candidate_id": "LLM00763", "doc_id": "NCT02849483_inc", "case_bucket": "other", "source_criterion": "20-70 yrs of age ASA(American Society of Anesthesiologists) physical status class I or II Scheduled for gynecological laparoscopic surgery", "candidate_expression": "((ASA physical status class I or II) AND (American Society of Anesthesiologists) AND (age 20-70 yrs) AND (laparoscopic surgery Scheduled gynecological))"}
{"candidate_id": "LLM00764", "doc_id": "NCT03336801_exc", "case_bucket": "or", "source_criterion": "American Association of Anesthesiology class 1-3 American Heart Association class >3 BMI >37 Insulin treated diabetes Pregnancy or breast feeding Sensistivity/allergy against anesthetic agents Inadequate understanding about the study Depressed kidney function and/or AKI Depressed liver function Genetic malignant hyperthermia", "candidate_expression": "((1-3) AND (>3) AND (>37) AND (AKI) AND (American Association of Anesthesiology class) AND (American Heart Association class) AND (BMI) AND (Depressed) AND (Depressed kidney function) AND (Depressed liver function) AND (Genetic) AND (Inadequate understanding about the study) AND (Insulin) AND (Insulin treated) AND (Pregnancy) AND (Sensistivity) AND (allergy) AND (anesthetic agents) AND (breast feeding) AND (diabetes) AND (kidney function) AND (liver function) AND (malignant hyperthermia))"}
{"candidate_id": "LLM00765", "doc_id": "NCT03416413_exc", "case_bucket": "or", "source_criterion": "Current DVT Recurrent varicose veins Arterial disease (ABPI<0.8) Vein diameter < 3mm Preference for one of the treatment options Patient who are unwilling to participate Inability or unwillingness to complete questionnaires Inability to attend follow-up appointments Patient currently included in a study of varicose vein treatment", "candidate_expression": "((ABPI <0.8) AND (Arterial disease) AND (DVT Current) AND (Inability to attend follow-up appointments) AND (Patient currently included in a study of varicose vein treatment) AND (Vein diameter < 3mm) AND (unwilling to participate) AND (varicose veins Recurrent) AND ((Inability to complete questionnaires) OR (unwillingness to complete questionnaires)))"}
{"candidate_id": "LLM00766", "doc_id": "NCT02893228_exc", "case_bucket": "or", "source_criterion": "Patient refusal Allergy to local anaesthesia Severe coagulopathy Contralateral phrenic nerve palsy Local infection Moderate to severe pulmonary dysfunction (GOLD II, II, IV)", "candidate_expression": "((Allergy) AND (Contralateral) AND (GOLD) AND (II, II, IV) AND (Local infection) AND (Patient refusal) AND (Severe) AND (coagulopathy) AND (local anaesthesia) AND (phrenic nerve palsy) AND (pulmonary dysfunction) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM00767", "doc_id": "NCT02202369_inc", "case_bucket": "other", "source_criterion": "Subjects undergoing a single level lumbar decompression and fusion > 18 years of age and < 70 years of age The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study", "candidate_expression": "((> 18 years and < 70 years) AND (The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study) AND (age) AND (lumbar decompression) AND (lumbar fusion) AND (single level))"}
{"candidate_id": "LLM00768", "doc_id": "NCT02145026_inc", "case_bucket": "or", "source_criterion": "Adult participants with low or intermediate-1 risk MDS No previous treatment with hematopoietic growth factors within 3 months prior to screening Symptomatic anemia (hemoglobin <10 g/dL) as determined by investigator Serum erythropoietin <500 milliunits/milliliter (mU/mL) within 14 days prior to the first dose of study treatment Require no red blood cell transfusion or dependent on <4 units within 8 weeks prior to screening Clinically stable for at least 1 month prior to entry into the study For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception", "candidate_expression": "((<10 g/dL) AND (<4 units) AND (<500 milliunits/milliliter) AND (Adult) AND (For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception) AND (MDS) AND (Serum erythropoietin) AND (Symptomatic) AND (anemia) AND (entry into the study) AND (for at least 1 month prior to entry into the study) AND (hematopoietic growth factors) AND (hemoglobin) AND (intermediate-1 risk) AND (low risk) AND (no) AND (red blood cell transfusion) AND (screening) AND (stable) AND (within 14 days prior to the first dose of study treatment) AND (within 3 months prior to screening) AND (within 8 weeks prior to screening))"}
{"candidate_id": "LLM00769", "doc_id": "NCT02277067_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((Women) AND (cesarean section) AND (gestation after 37 weeks) AND (singleton pregnancy))"}
{"candidate_id": "LLM00770", "doc_id": "NCT02951754_inc", "case_bucket": "other", "source_criterion": "White Brazilian of European descent Fulfillment of the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria for ADHD Eligibility to immediate-release MPH (IR-MPH) treatment", "candidate_expression": "((ADHD) AND (Brazilian) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria) AND (Eligibility) AND (European descent) AND (White) AND (immediate-release MPH (IR-MPH)))"}
{"candidate_id": "LLM00771", "doc_id": "NCT03288428_exc", "case_bucket": "other", "source_criterion": "can't understand patient controlled analgesia device refuse trial", "candidate_expression": "(can't understand patient controlled analgesia device refuse trial)"}
{"candidate_id": "LLM00772", "doc_id": "NCT01082549_exc", "case_bucket": "or", "source_criterion": "1. Prior treatment with gemcitabine, carboplatin (except in the adjuvant setting), or Iniparib. 2. Past or current history of neoplasm other than the entry diagnosis, with the exception of treated non-melanoma skin cancer or carcinoma in-situ of any primary site, or invasive cancers treated definitively, with treatment ending >5 years previously and no evidence of recurrences. 3. A history of cardiac disease, as defined by: Malignant hypertension Unstable angina Congestive heart failure Myocardial infarction within the previous 6 months Symptomatic, unstable or uncontrolled, cardiac arrhythmias. Patients who have stable, rate-controlled atrial fibrillation are eligible for study enrollment. 4. Active brain metastases. Patients with treated brain metastases are eligible, if (1) radiation therapy was completed at least 2 weeks prior to study entry; (2) follow-up scan shows no disease progression; and (3) patient does not require steroids. 5. Women who are pregnant or lactating. 6. Any serious, active infection (> Grade 2) at the time of treatment. 7. A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment. 8. A major surgical procedure, or significant traumatic injury ≤28 days of beginning treatment, or anticipation of the need for major surgery during the course of the study. 9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 10. History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 11. Known or suspected allergy/hypersensitivity to any agent given in the course of this trial. The above information is not intended to contain all considerations relevant to a patient's potential participation in a clinical trial.", "candidate_expression": "((9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment.) AND (Congestive heart failure) AND (History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (Iniparib Past current) AND (Known or suspected allergy/hypersensitivity to any agent given in the course of this trial) AND (Malignant hypertension) AND (Myocardial infarction within the previous 6 months Symptomatic unstable) AND (Unstable angina) AND (Women) AND (Women who are pregnant or lactating) AND (agent given in the course of this trial) AND (allergy Known suspected) AND (brain metastases Active) AND (brain metastases treated) AND (cancers invasive treated definitively) AND (carboplatin) AND (carcinoma in-situ) AND (cardiac arrhythmias uncontrolled) AND (cardiac disease history) AND (entry diagnosis) AND (follow-up scan) AND (gemcitabine) AND (hypersensitivity) AND (illness in the opinion of the investigator may increase the risks Uncontrolled intercurrent) AND (impair the ability of the patient to receive protocol treatment would) AND (in the opinion of the investigator may increase the risks) AND (infection serious active > Grade 2 > Grade 2) AND (laboratory) AND (laboratory abnormality) AND (lactating) AND (major) AND (major surgery need for during the course of the study the course of the study) AND (medical condition serious) AND (neoplasm history other than the entry diagnosis) AND (non-melanoma skin cancer treated) AND (pregnant) AND (psychiatric condition) AND (radiation therapy at least 2 weeks prior to study entry) AND (serious) AND (significant) AND (surgical procedure major) AND (traumatic injury significant ≤28 days of beginning treatment beginning treatment) AND (treated) AND (treated >5 years previously) AND NOT (evidence of recurrences) AND NOT (atrial fibrillation stable rate-controlled) AND NOT (disease progression) AND NOT (steroids require))"}
{"candidate_id": "LLM00773", "doc_id": "NCT02528604_inc", "case_bucket": "other", "source_criterion": "Patients with symptomatic persistent atrial fibrillation of less than 1-year duration. Patients must be over 65 years old. Patients give informed consent prior to participating in this study.", "candidate_expression": "((Patients give informed consent prior to participating in this study) AND (atrial fibrillation) AND (less than 1-year) AND (old) AND (over 65 years) AND (persistent) AND (symptomatic))"}
{"candidate_id": "LLM00774", "doc_id": "NCT01602081_exc", "case_bucket": "or", "source_criterion": "Patients with prior fistulotomy, fistulectomy, LIFT, cutting seton or advancement flap procedure Fistula with multiple tracts Recto-vaginal fistula Active infection in the anal fistula Physical allergies or cultural objections to porcine products Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician Previous diagnosis of collagen disorder History of Crohn's Disease, Irritable Bowel Syndrome, radiation therapy in the rectoanal region", "candidate_expression": "((Crohn's Disease) AND (Fistula multiple tracts) AND (Irritable Bowel Syndrome) AND (LIFT) AND (Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician) AND (Recto-vaginal fistula) AND (advancement flap procedure) AND (anal fistula) AND (collagen disorder) AND (cutting seton) AND (fistulectomy) AND (fistulotomy) AND (infection in the anal fistula) AND (radiation therapy rectoanal region))"}
{"candidate_id": "LLM00775", "doc_id": "NCT02431442_exc", "case_bucket": "or", "source_criterion": "Fasting blood glucose >126 mg/dL at screening. Heterozygous subjects will be excluded for a fasting blood glucose >140 mg/dL. Resting heart rate <45 bpm or >90 bpm at screening. Abnormal thyroid stimulating hormone (TSH) or thyroxine (T4) levels on screening. Elevated ALT or serum creatinine on screening or any clinically significant abnormalities on screening laboratory tests as determined by the Investigator. History of medically treated diabetes or of treated or medically diagnosed hypertension. Heterozygous subjects who have diagnosed hypertension and are well controlled on treatment (Refer to Exclusion Criteria 20 below), are eligible. . Presence of a skin lesion suspicious for malignancy, unless excised prior to Day 1. History of malignancy except for treated cervical carcinoma in situ in the past 5 years. Active or history of any clinically significant medical condition including renal, hepatic, pulmonary, gastrointestinal, cardiovascular, genitourinary, endocrine, immunologic, metabolic, neurologic, psychiatric or hematological disease, based on Investigator judgment. Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data. Positive hepatitis B surface antigen, positive hepatitis C antibody or positive HIV test at screening or a history of positive testing (e.g. liver biopsy, serology) suggesting acute or chronic hepatitis. Abnormal 12-lead electrocardiogram (ECG) at screening or pre-dose (Day -1 or Day 1), except minor deviations deemed to be of no clinical significance by the Investigator. Received any experimental drugs or devices within 30 days or 5 half lives, whichever is longer, prior to dosing. Ongoing participation in a prior clinical study at the time of screening. Blood donation within 60 days prior to screening or intent to donate within 60 days after Final Study Visit. Hospitalization for major surgery including but not limited to abdominal, thoracic, or cardiovascular surgery within the past 3 months prior to screening, or for a clinically significant non-surgical illness, based on Investigator judgment, within the past 3 months. Planned elective surgery within 30 days of the Final Study Visit. Poor venous access or inability to tolerate venipuncture. History of significant drug hypersensitivity or anaphylaxis. History of hypersensitivity to proteins (e.g., allergy shots). Use of prescription medications on a regular basis. The last use of any prescription medication must have been greater than 5 half-lives for the specific medication or at least 14 days prior to admission (Day -1), whichever is longer. Hormonal contraception is allowed for female subjects. Heterozygous cohorts: Use of prescription medications on a regular basis is not allowed with the following exceptions: Antihypertensives (<3 medications on a stable dose for ≥ 30 days); Statins (dose must be ≤ half the maximum dose; must be on a stable dose ≥3 months); Fibrates (must be on stable dose for ≥3 months); Niacin (must be on stable dose for ≥3 months); Thyroxin (stable dose for ≥ 30 days); The last use of any other prescription medication will need follow the criteria for all other cohorts, as outlined above. Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm. Use of a non-prescription drug and herbal substances during the study (through the Final Study Visit). The last dose of any non-prescription drug must have been taken greater than 5 half-lives for that drug before receiving study drug. Inability to attend all study visits or to comply with protocol requirements including fasting and restrictions on alcohol, caffeine, nicotine and concomitant medication intake. A significant history of drug/solvent abuse within 5 years of screening or a positive test for drugs of abuse test at screening or on Day -1. Positive alcohol (breath test) or nicotine screen at Screening Visit or Day 1 (positive nicotine screen does not apply to heterozygous cohort). History of alcohol abuse (defined as average intake of three or more units of alcohol per day) within 5 years of the Screening Visit. History of tobacco or tobacco product use unless abstinent for at least one year prior to the Screening Visit. This criterion does not apply to heterozygous subjects. Previously randomized and dosed in this study. This criterion does not apply to heterozygous subjects. Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.", "candidate_expression": "((12-lead electrocardiogram (ECG)) AND (<3 medications) AND (>126 mg/dL) AND (>140 mg/dL) AND (Abnormal) AND (Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data.) AND (Antihypertensives) AND (Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.) AND (Blood donation) AND (Day 1) AND (Elevated) AND (Fasting blood glucose) AND (Fibrates) AND (Final Study Visit) AND (Heterozygous) AND (History) AND (Hormonal contraception) AND (Niacin) AND (Planned) AND (Positive) AND (Resting heart rate) AND (Screening Visit) AND (Statins) AND (Thyroxin) AND (Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm.) AND (abnormalities) AND (abstinent) AND (admission) AND (alcohol) AND (alcohol abuse) AND (any non-prescription drug) AND (any prescription medication) AND (as determined by the Investigator) AND (at Screening Visit) AND (at pre-dose) AND (at screening) AND (based on Investigator judgment) AND (cervical carcinoma in situ) AND (clinically significant) AND (during the study) AND (elective surgery) AND (except for) AND (excised) AND (fasting blood glucose) AND (female) AND (for at least one year prior to the Screening Visit) AND (for ≥ 30 days) AND (greater than 5 half-lives before receiving study drug) AND (hematological disease) AND (history) AND (hypersensitivity to allergy shots) AND (hypersensitivity to proteins) AND (hypertension) AND (in the past 5 years) AND (intent to donate) AND (liver biopsy) AND (major) AND (malignancy) AND (medical condition) AND (medically treated) AND (nicotine screen) AND (on screening) AND (positive) AND (pre-dose) AND (prescription medications) AND (prior to Day 1) AND (regular basis) AND (screening) AND (serology) AND (significant) AND (skin lesion) AND (stable dose) AND (surgery) AND (suspicious for malignancy) AND (testing) AND (the Screening Visit) AND (three or more units per day) AND (treated) AND (treatment) AND (unless) AND (venipuncture) AND (well controlled) AND (within 30 days of the Final Study Visit) AND (within 5 years of screening) AND (within 5 years of the Screening Visit) AND (within 60 days after Final Study Visit) AND (within 60 days prior to screening) AND (within the past 3 months) AND (within the past 3 months prior to screening) AND (≤ half the maximum dose) AND (≥ 30 days) AND (≥3 months) AND ((acute hepatitis) OR (chronic hepatitis)) AND ((Day -1) OR (Day 1)) AND ((experimental devices) OR (experimental drugs)) AND ((within 30 days) OR (within 5 half lives)) AND ((Hospitalization) OR (non-surgical illness)) AND ((thyroid stimulating hormone (TSH)) OR (thyroxine (T4))) AND ((abdominal surgery) OR (cardiovascular surgery) OR (thoracic surgery)) AND ((Poor venous access) OR (inability to tolerate venipuncture)) AND ((drug anaphylaxis) OR (drug hypersensitivity)) AND ((at least 14 days prior to admission) OR (last use greater than 5 half-lives)) AND ((ALT) OR (laboratory tests) OR (serum creatinine)) AND ((herbal substances) OR (non-prescription drug)) AND ((drug/solvent abuse) OR (drugs of abuse test)) AND ((alcohol test) OR (breath test)) AND ((tobacco product use) OR (tobacco use)) AND ((diabetes) OR (hypertension)) AND ((medically) OR (medically treated)) AND ((medically) OR (treated)) AND ((Active) OR (history)) AND ((disease cardiovascular) OR (disease endocrine) OR (disease gastrointestinal) OR (disease genitourinary) OR (disease hepatic) OR (disease immunologic) OR (disease pulmonary) OR (disease renal) OR (metabolic disease) OR (neurologic disease) OR (psychiatric disease)) AND ((<45 bpm) OR (>90 bpm)) AND ((HIV test) OR (hepatitis B surface antigen) OR (hepatitis C antibody)))"}
```
