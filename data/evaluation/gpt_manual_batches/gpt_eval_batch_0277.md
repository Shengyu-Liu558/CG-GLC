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
{"candidate_id": "LLM06901", "doc_id": "NCT02437084_inc", "case_bucket": "other", "source_criterion": "Healthy adults 30- 65 years old, BMI 25-35 kg/m2, nondiabetic as defined by fasting plasma glucose <126 mg/dL Lipids: one group with an LDL =/>130 and Triglycerides < 150 mg/dL The 2nd group will have and LDL=/>130 mg/dL and Triglycerides =/>150 mg/dL but less than 400 mg/dL.", "candidate_expression": "((25-35 kg/m2) AND (30- 65 years old) AND (< 150 mg/dL) AND (<126 mg/dL) AND (=/>130) AND (BMI) AND (Healthy) AND (LDL) AND (Triglycerides) AND (adults) AND (fasting plasma glucose) AND (nondiabetic) AND (old))"}
{"candidate_id": "LLM06902", "doc_id": "NCT01700790_inc", "case_bucket": "or", "source_criterion": "Antiretroviral naive Taking Kaletra containing regimen with suppressed viral load. Taking an NNRTI or integrase containing regimen without prior history of use of PI for more than 2 weeks Taking an NNRTI or integrase containing regimen with prior exposure to PI greater than 2 weeks. It must be clearly stated in the source document that PI was switched to another agent for convenience. Taking another PI containing regimens with suppressed viral load. It must be clearly stated in source document that if another PI was used for greater than 2 weeks the regimen was switched to another agent for convenience. Subjects with prior history of PI use may be enrolled, if there is a genotype showing no resistance to Kaletra Other Inclusion criteria Be at least 18 years of age and able to give informed consent. Diagnosed with TB by criteria per Brazilian Ministry of Health Have a good clinical response to TB. Tolerating tuberculosis therapy containing rifampin for the 2 weeks prior to screening,except for persons taking protease inhibitors at time of diagnosis of TB.,. Subjects taking protease inhibitors will be screened and initiate visit 1 within 3 days of starting TB medication HIV positive with documentation present in source document. Have a CD4 cell count greater than 50 cells/mm3if not taking ART. Persons with cd4 < 50 may be enrolled, if it is felt that in the best interest of the patient, that enrollment in the study will allow for quicker initiation of antiretroviral therapy than referral to another treatment center.", "candidate_expression": "((ART) AND (Antiretroviral) AND (CD4 cell count) AND (HIV) AND (HIV positive) AND (Kaletra) AND (PI) AND (TB) AND (able to give informed consent) AND (age) AND (at least 18 years) AND (at time of diagnosis of TB) AND (criteria per Brazilian Ministry of Health) AND (except) AND (for more than 2 weeks) AND (for the 2 weeks prior to screening) AND (good clinical response) AND (greater than 2 weeks) AND (greater than 50 cells/mm3) AND (naive) AND (not) AND (positive) AND (prior) AND (protease inhibitors) AND (regimen) AND (regimens) AND (rifampin) AND (screening) AND (suppressed) AND (time of diagnosis of TB) AND (tuberculosis) AND (tuberculosis therapy) AND (viral load) AND (without) AND ((NNRTI) OR (integrase)))"}
{"candidate_id": "LLM06903", "doc_id": "NCT02429583_exc", "case_bucket": "or", "source_criterion": "Received any vaccine within a month prior to study vaccine Positive serum antibody against Hep B surface antigen and/or core Hep B core antigen HIV positive For HCV-negative, healthy volunteers: History of HCV infection or positive HCV antibody test Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol Any clinically significant abnormality or medical history or physical examination including history of immunodeficiency or autoimmune disease (in addition to HCV infection, for HCV group) Currently taking systemic steroids or other immunomodulatory medications including anticancer medications and antiviral medications Any clinically significant acute or chronic medical condition requiring care by a primary care provider (e.g., diabetes, coronary artery disease, rheumatologic illness, malignancy, substance abuse) that, in the opinion of the investigator, would preclude participation Unable to continue participation for 156 weeks History of previous Hepatitis B vaccination(s) Male or female < 18 and > 62 years of age Is pregnant or lactating History of Hepatitis B infection Clinical, laboratory, or biopsy evidence of cirrhosis", "candidate_expression": "((HCV negative) AND (HIV positive) AND (Hepatitis B infection) AND (Hepatitis B vaccination) AND (History of HCV infection) AND (In the opinion of the investigator, the volunteer is unlikely to comply with the study protocol) AND (Is pregnant or lactating) AND (Participation in another clinical study of an investigational product currently or within the past 90 days, or expected participation during this study) AND (Unable to continue participation for 156 weeks) AND (age < 18 and > 62 years) AND (cirrhosis) AND (serum antibody Positive) AND (vaccine within a month prior to study vaccine) AND NOT (HCV infection) AND ((autoimmune disease) OR (immunodeficiency)) AND ((immunomodulatory medications) OR (systemic steroids)) AND ((anticancer medications) OR (antiviral medications)) AND ((coronary artery disease) OR (diabetes) OR (malignancy) OR (rheumatologic illness) OR (substance abuse)) AND ((Male) OR (female)) AND ((Hep B surface antige) OR (core Hep B core antigen)))"}
{"candidate_id": "LLM06904", "doc_id": "NCT03390933_exc", "case_bucket": "or", "source_criterion": "on hemodialysis for less than 3 months comorbid psychotic, bipolar, substance use dependence, Alzheimer's or dementia", "candidate_expression": "((hemodialysis for less than 3 months) AND ((Alzheimer's) OR (bipolar) OR (dementia) OR (psychotic) OR (substance use dependence)))"}
{"candidate_id": "LLM06905", "doc_id": "NCT03019562_exc", "case_bucket": "or", "source_criterion": "Allergic to study drugs Patient with asthma or COPD, patient who is severely respiratory depressed Renal of hepatic insufficiency Epileptic status Intracranial lesion associated with increased intracranial pressure Acute abdomen, patient who has diagnosed paralytic ileus or suspicious ileus Pregnant or lactating women", "candidate_expression": "((Acute abdomen) AND (Allergic) AND (COPD) AND (Epileptic status) AND (Intracranial lesion) AND (Pregnant) AND (Renal insufficiency) AND (asthma) AND (hepatic insufficiency) AND (intracranial pressure increased) AND (lactating) AND (paralytic ileus) AND (respiratory depressed severely) AND (study drugs) AND (suspicious ileus) AND (wome))"}
{"candidate_id": "LLM06906", "doc_id": "NCT03473132_inc", "case_bucket": "other", "source_criterion": "LVAD on warfarin requiring temporary interruption of anticoagulation for procedures", "candidate_expression": "((LVAD) AND (warfarin requiring temporary interruption of anticoagulation for procedures))"}
{"candidate_id": "LLM06907", "doc_id": "NCT02536976_inc", "case_bucket": "or", "source_criterion": "Aged 25-80 at screening. Subjects older than 80 will be allowed at the discretion of the PI. Ambulatory (defined as able to ambulate at least 10 meters, with or without assistance). Clinical Diagnosis of PD based on the United Kingdom Brain Bank diagnostic criteria for PD. At least 8 micturitions per 24 hours and At least 3 urgency episodes per 3-day diary. A MoCA score between 19 and 28 (inclusive) at screening. For those on cognitive enhancers (donepezil, rivastigmine, memantine, galantamine) a MoCA score between 19 and 29 (inclusive) at screening. Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care. Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent. Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks. Be on a stable regimen of antiparkinson's medications at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study. If taking cognitive enhancers (donepezil, rivastigmine, memantine, galantamine), must be on stable dose at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study.", "candidate_expression": "((Aged 25-80) AND (Ambulatory) AND (Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks) AND (Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent) AND (MoCA score between 19 and 28) AND (MoCA score between 19 and 29) AND (PD) AND (Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care) AND (United Kingdom Brain Bank diagnostic criteria) AND (antiparkinson's medications at least 30 days prior to screening) AND (cognitive enhancers) AND (cognitive enhancers stable dose at least 30 days prior to screening) AND (micturitions At least 8 per 24 hours) AND (urgency episodes At least 3 per 3-day diary.) AND ((donepezil) OR (galantamine) OR (memantine) OR (rivastigmine)))"}
{"candidate_id": "LLM06908", "doc_id": "NCT02573168_exc", "case_bucket": "or", "source_criterion": "Patients posing a serious suicidal risk and/or violence as judged by the investigator; Delirium Dementia Amnestic and other cognitive disorder; Patients with a history of hypothyroidism unless taking a stable dose of thyroid medication and asymptomatic or euthyroid for 6 months; Patients who meet DSM-IV-TR criteria for any significant current substance abuse; hepatic insufficiency (three times the upper limit of normal (ULN) for aspartate aminotransferase (AST) and/or alanine aminotransferase (ALT)); liver transplant recipient; cirrhosis of the liver; malignancy (except basal cell carcinoma) and/or chemotherapy within 1 year prior to screening; malignancy more than 1 year prior to screening must have been local and without metastasis and/or recurrence, and if treated with chemotherapy, without nervous system complications; significant unstable medical condition or life threatening disease with anticipated survival of less than 6 months; need for therapies that may obscure the results of treatment and/or of the study Participation in another clinical trial within 30 days of the screening visit; Anticipated inability to attend scheduled study visits; Patients who in the judgment of the Investigator may be unreliable or uncooperative with the evaluation procedure outlined in this protocol; Patients with a history of prior pharmacogenomic testing; Any change in psychotropic medication (including change in dosage) between screening and baseline; Patients who are known to be pregnant or lactating; Patients with a history of gastric bypass surgery.", "candidate_expression": "((ALT) AND (AST) AND (Amnestic disorder) AND (Anticipated inability to attend scheduled study visits) AND (DSM-IV-TR) AND (Delirium) AND (Dementia) AND (Participation in another clinical trial within 30 days of the screening visit) AND (Patients who are known to be pregnant or lactating) AND (Patients with a history of prior pharmacogenomic testing) AND (alanine aminotransferase) AND (aspartate aminotransferase) AND (chemotherapy within 1 year prior to screening) AND (cirrhosis of the liver) AND (cognitive disorder) AND (gastric bypass surgery) AND (hepatic insufficiency) AND (hypothyroidism) AND (life threatening disease) AND (liver transplant) AND (malignancy) AND (malignancy more than 1 year local) AND (medical condition unstable) AND (metastasis) AND (psychotropic medication) AND (recurrence) AND (substance abuse) AND (suicidal risk) AND (violence) AND NOT (basal cell carcinoma) AND NOT (thyroid medication))"}
{"candidate_id": "LLM06909", "doc_id": "NCT02227992_exc", "case_bucket": "or", "source_criterion": "Subjects with known intolerance to blood products or to one of the components of the study product or is unwilling to receive blood products; Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing; Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor; Subjects who are known, current alcohol and/or drug abusers Subjects admitted for trauma surgery Subjects with any pre or intra-operative findings identified by the surgeon that may preclude conduct of the study procedure. Subject with TBS in an actively infected field (Class III Contaminated or Class IV Dirty or Infected) TBS is from large defects in arteries or veins where the injured vascular wall requires repair with maintenance of vessel patency and which would result in persistent exposure of the EVARREST™ or SURGICEL® to blood flow and pressure during healing and absorption of the product; TBS with major arterial bleeding requiring suture or mechanical ligation; Bleeding site is in, around, or in proximity to foramina in bone, or areas of bony confine.", "candidate_expression": "((Class III Contaminated) AND (Class IV Dirty or Infected) AND (Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing) AND (Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor) AND (TBS) AND (alcohol abusers) AND (blood products) AND (drug abusers) AND (intolerance) AND (major arterial bleeding) AND (mechanical ligation) AND (suture) AND (trauma surgery))"}
{"candidate_id": "LLM06910", "doc_id": "NCT02735577_inc", "case_bucket": "or", "source_criterion": "Between the ages of 21-60 Right-handed Capable of giving informed consent and complying with study procedures Reports drinking a minimum of 5 standard drinks for men or 4 standard drinks for women on at least 4 days per week on average over the past 28 days Meets DSM-V criteria for current Alcohol Use Disorder Seeking treatment for Alcohol Use Disorder Agree to not seek additional treatment, apart from Alcoholics Anonymous Willing to attempt to abstain from alcohol completely for the duration of the study Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed.", "candidate_expression": "((Alcohol Use Disorder) AND (DSM-V criteria Meets) AND (Right-handed) AND (Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed) AND (abstain from alcohol Willing completely) AND (ages Between 21-60) AND (drinking over the past 28 days) AND (men minimum of 5 standard drinks on at least 4 days per week) AND (treatment Seeking) AND (women 4 standard drinks on at least 4 days per week))"}
{"candidate_id": "LLM06911", "doc_id": "NCT03177837_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((18-75 yrs) AND (40-80% predicted) AND (750 m) AND (<800m) AND (=92%) AND (COPD) AND (FEV1) AND (GOLD) AND (Male) AND (SpO2) AND (Written informed consent.) AND (age) AND (female) AND (living at low altitude))"}
{"candidate_id": "LLM06912", "doc_id": "NCT02301962_exc", "case_bucket": "or", "source_criterion": "History or known presence of central nervous system metastases. History of another malignancy except: Malignancy treated with curative intent and with no known active disease present for >=5 years prior to enrolment and felt to be at low risk for recurrence by the treating physician; Adequately treated non-melanomatous skin cancer or lentigo maligna without evidence of disease; Adequately treated cervical carcinoma in situ without evidence of disease; Prostatic intraepithelial neoplasia without evidence of prostate cancer. Known immediate or delayed hypersensitivity reaction or idiosyncrasy to drugs chemically related to panitumumab or excipients that contraindicates their participation. Prior anti-epidermal growth factor receptor (EGFr) antibody therapy (e.g., panitumumab or cetuximab) or treatment with small molecule EGFr inhibitors (e.g., gefitinib, erlotinib, lapatinib). Antitumor therapy (e.g., chemotherapy, hormonal therapy, immunotherapy, antibody therapy, radiotherapy), or investigational agent or therapy <=30 days before first dose of study treatment or not recovered from any acute toxicity. Other investigational procedure <=30 days before study entry. History of interstitial lung disease (ILD) e.g., interstitial pneumonitis, pulmonary fibrosis or evidence of ILD on baseline chest computer tomography. Subject previously enrolled to this study. History of keratitis, ulcerative keratitis or severe dry eye. Major surgery (e.g., requiring general anesthesia) <=30 days before first dose of study treatment. Subjects must have recovered from any surgery related toxicities. Minor surgical procedure (e.g., open biopsy) <=7 days before first dose of study treatment, or not yet recovered from prior minor surgery Note: uncomplicated placement of vascular access device, fine needle aspiration, thoracocentesis or paracentesis >=3 days prior to first dose of study treatment is acceptable. Clinically significant cardiovascular disease (including myocardial infarction, unstable angina, symptomatic congestive heart failure, serious uncontrolled cardiac arrhythmia) <=6 months prior to enrolment. History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results. Unstable pulmonary embolism, deep vein thrombosis, or other significant arterial/venous thromboembolic event <=30 days before first dose of study treatment. If on anticoagulation, subject must be on stable therapeutic dose prior to first dose of study treatment. Subject who is pregnant or breast feeding, or planning to become pregnant during treatment and within 2 months after the discontinuation of study treatment. Known positive test(s) for human immunodeficiency virus infection (testing is not required in the absence of clinical suspicion). Active infection requiring systemic treatment or any uncontrolled infection <=14 days prior to first dose of study treatment (with the exception of uncomplicated urinary tract infection or upper respiratory tract infection). Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.", "candidate_expression": "((<=14 days prior to first dose of study treatment) AND (<=30 days before first dose of study treatment) AND (<=30 days before study entry) AND (<=6 months prior to enrolment) AND (<=7 days before first dose of study treatment) AND (Active) AND (Adequately) AND (EGFr) AND (History of any medical or psychiatric condition or laboratory abnormality that in the opinion of the investigator may increase the risk associated with the study participation or investigational product administration, compliance with the study procedures or may interfere with the interpretation of the results.) AND (ILD) AND (Major surgery) AND (Other) AND (Subject has any kind of disorder that compromises the ability of the subject to give written informed consent and/or to comply with study procedures or is unwilling or unable to comply with study requirements.) AND (Unstable) AND (active disease) AND (another) AND (anticoagulation) AND (any) AND (baseline) AND (central nervous system metastases) AND (disease) AND (during treatment) AND (enrolment) AND (evidence of) AND (evidence of disease) AND (except) AND (felt to be at low risk) AND (first dose of study treatment) AND (for >=5 years prior to enrolment) AND (general anesthesia) AND (idiosyncrasy) AND (interstitial lung disease) AND (investigational procedure) AND (malignancy) AND (minor surgery) AND (no) AND (not recovered from any acute toxicity) AND (not yet) AND (open biopsy) AND (other) AND (planning to) AND (positive) AND (prior) AND (prostate cancer) AND (recurrence) AND (serious) AND (severe) AND (significant) AND (stable) AND (symptomatic) AND (systemic treatment) AND (test(s) for human immunodeficiency virus infection) AND (the discontinuation of study treatment) AND (therapeutic dose) AND (treated) AND (treated with curative intent) AND (treatment) AND (uncomplicated) AND (uncontrolled) AND (with the exception of) AND (within 2 months after the discontinuation of study treatment) AND (without) AND ((deep vein thrombosis) OR (pulmonary embolism)) AND ((arterial thromboembolic event) OR (venous thromboembolic event)) AND ((first dose of study treatment) OR (prior to first dose of study treatment)) AND ((become pregnant) OR (breast feeding) OR (pregnant)) AND ((infection) OR (uncontrolled infection)) AND ((upper respiratory tract infection) OR (urinary tract infection)) AND ((lentigo maligna) OR (non-melanomatous skin cancer)) AND ((Prostatic intraepithelial neoplasia) OR (cervical carcinoma in situ)) AND ((delayed hypersensitivity reaction) OR (immediate hypersensitivity reaction)) AND ((drugs chemically related to panitumumab) OR (drugs chemically related to panitumumab excipients)) AND ((anti-epidermal growth factor receptor antibody therapy) OR (treatment with small molecule EGFr inhibitors)) AND ((cetuximab) OR (panitumumab)) AND ((Malignancy) OR (treated)) AND ((erlotinib) OR (gefitinib) OR (lapatinib)) AND ((Antitumor therapy) OR (investigational agent) OR (therapy)) AND ((antibody therapy) OR (chemotherapy) OR (hormonal therapy) OR (immunotherapy) OR (radiotherapy)) AND ((chest computer tomography) OR (interstitial pneumonitis) OR (pulmonary fibrosis)) AND ((dry eye) OR (keratitis) OR (ulcerative keratitis)) AND ((Minor surgical procedure) OR (recovered)) AND ((Clinically significant) OR (cardiovascular disease)) AND ((cardiac arrhythmia) OR (congestive heart failure) OR (myocardial infarction) OR (unstable angina)))"}
{"candidate_id": "LLM06913", "doc_id": "NCT02755701_exc", "case_bucket": "or", "source_criterion": "Child-Pugh score > 12 Having been diagnosed as HCC within the past 5 years Serum creatinine > 1.5mg/dl Serum bilirubin > 5.0mg/dl Presence of such complications as SBP, or hepatic encephalopathy(West Haven grade = 3) Patients who experienced organ failure by acute exacerbation of liver cirrhosis within the past 1 month Presence of serious cardiac or respiratory disease Contraindicated to either diuretics or BCAA Having commenced anti-viral treatment against hepatitis C, B within the past 1 month Pregnant or lactating women Chronic alcohol taker Woman patients who do not agree to the contraception from baseline to 12 month Unsuitable patients judged by investigator Patients participating in another clinical trial within 1 month", "candidate_expression": "((BCAA) AND (Child-Pugh score > 12) AND (Contraindicated) AND (HCC past 5 years) AND (Patients participating in another clinical trial within 1 month) AND (Pregnant or lactating women) AND (SBP) AND (Serum bilirubin > 5.0mg/d) AND (Serum creatinine > 1.5mg/dl) AND (West Haven grade = 3) AND (Woman patients who do not agree to the contraception from baseline to 12 month) AND (acute exacerbation of liver cirrhosis past 1 month) AND (alcohol taker Chronic) AND (anti-viral treatment past 1 month) AND (cardiac disease) AND (complications) AND (diuretics) AND (hepatic encephalopathy) AND (hepatitis B) AND (hepatitis C) AND (organ failure) AND (respiratory disease))"}
{"candidate_id": "LLM06914", "doc_id": "NCT02437045_inc", "case_bucket": "or", "source_criterion": "Bloodstream infection with Enterobacter spp., Serratia marcescens, Providencia spp., Morganella morganii or Citrobacter freundii (i.e. likely AmpC-producer), and susceptibility to 3rd generation cephalosporins (i.e. ceftriaxone, cefotaxime or ceftazidime), meropenem and piperacillin-tazobactam from at least one blood culture draw. This will be determined in accordance with laboratory methods and susceptibility breakpoints defined by protocols used in the recruiting site laboratories.. No more than 72 hours has elapsed since the first positive blood culture collection. Patient is aged 18 years and over (>=21y in Singapore).", "candidate_expression": "((3rd generation cephalosporins () AND (Bloodstream infection Enterobacter spp. Serratia marcescens Providencia spp. Morganella morganii) AND (Citrobacter freundii) AND (No more than 72 hours since the first positive blood culture collection) AND (Singapore >=21y) AND (aged 18 years and over) AND (blood culture at least one) AND (blood culture collection positive the first positive blood culture collection) AND (cefotaxime) AND (ceftazidime) AND (ceftriaxone) AND (meropenem) AND (piperacillin-tazobactam))"}
{"candidate_id": "LLM06915", "doc_id": "NCT01942915_inc", "case_bucket": "other", "source_criterion": "Patients with hepatocirrhosis: according to the standard of child- pugh, liver functions to achieve class A or B patients, Including C class patients but can achieve B class after treatment", "candidate_expression": "(hepatocirrhosis)"}
{"candidate_id": "LLM06916", "doc_id": "NCT02267616_exc", "case_bucket": "other", "source_criterion": "Have history of female sterilization procedure Desire for conception in the next 12 months Not sexually active with a male partner", "candidate_expression": "((Desire) AND (Not) AND (conception) AND (female sterilization procedure) AND (in the next 12 months) AND (male partner) AND (sexually active))"}
{"candidate_id": "LLM06917", "doc_id": "NCT03413891_exc", "case_bucket": "other", "source_criterion": "Subjects with any condition that as judged by the Investigator would place the subject at increased risk of harm if he/she participated in the study. Pregnancy or lactation Known allergic reaction to tranexamic acid", "candidate_expression": "((Pregnancy or lactation) AND (allergic) AND (tranexamic acid))"}
{"candidate_id": "LLM06918", "doc_id": "NCT01997580_inc", "case_bucket": "or", "source_criterion": "DSM-IV-TR major depressive disorder aged between 20 and 80 durg-naive or drug-free", "candidate_expression": "((aged between 20 and 80) AND (major depressive disorder DSM-IV-TR) AND NOT (durg) AND NOT (drug))"}
{"candidate_id": "LLM06919", "doc_id": "NCT02429765_inc", "case_bucket": "scope", "source_criterion": "Moderate to severe COPD (post-bronchodilator forced expiratory volume in 1 s (FEV1) 30-79%predicted); Resting functional residual capacity (FRC) >120% predicted; Clinically stable and on stable triple therapy with an ICS/LABA and tiotropium; Symptomatic: Baseline Dyspnea Index =8 and answer \"in the morning\" when asked about what time of day their COPD symptoms are worst.", "candidate_expression": "((Baseline Dyspnea Index =8) AND (COPD Moderate to severe) AND (Clinically stable) AND (ICS/LABA) AND (Resting functional residual capacity (FRC) >120% predicted) AND (forced expiratory volume in 1 s (FEV1) post-bronchodilator 30-79%predicted) AND (stable triple therapy) AND (tiotropium) AND (what time of day their COPD symptoms are worst in the morning))"}
{"candidate_id": "LLM06920", "doc_id": "NCT03472495_inc", "case_bucket": "or", "source_criterion": ">/= 18 years old Atrial fibrillation or flutter on electrocardiogram Heart rate >110 beats/min Systolic blood pressure >/= 90 mmHg", "candidate_expression": "((Heart rate >110 beats/min) AND (Systolic blood pressure >/= 90 mmHg) AND (electrocardiogram) AND (old >/= 18 years old) AND ((Atrial fibrillation) OR (Atrial flutter)))"}
{"candidate_id": "LLM06921", "doc_id": "NCT03033745_inc", "case_bucket": "or", "source_criterion": "Male or female on stable dose of IgPro20 (Hizentra) therapy. Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening. Subjects with PID, eg, with a diagnosis of common variable immunodeficiency or X-linked agammaglobulinemia, as defined by the Pan American Group for Immune Deficiency and the European Society of Immune Deficiencies. With infusion parameters as specified below: Experience with pump-assisted infusions of IgPro20 at the tolerated flow rate of 25 mL/h per injection site for at least 1 month prior to Day 1. Total weekly IgPro20 dose of = 50 mL (= 10 g). Experience with pump-assisted infusions of IgPro20 at tolerated volumes of 25 mL/injection site for at least 1 month prior to Day 1. Experience with frequent (2-7 times per week) infusions of IgPro20 at the tolerated flow rate of approximately 0.5 mL/min (equivalent of 25-30 mL/h) per injection site for at least 1 month prior to Day 1. The dose (volume) per injection site should not exceed 25 mL.", "candidate_expression": "((Hizentra) AND (IgPro20 frequent 2-7 times per week per injection site flow rate of approximately 0.5 mL/min for at least 1 month prior to Day 1 exceed 25 mL. 25-30 mL/h) AND (IgPro20 pump-assisted infusions flow rate of 25 mL/h per injection site for at least 1 month prior to Day 1) AND (IgPro20 pump-assisted infusions volumes of 25 mL/injection site for at least 1 month prior to Day 1) AND (IgPro20 stable dose) AND (IgPro20 weekly = 50 mL = 10 g) AND (PID) AND (Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening) AND ((Male) OR (female)) AND ((European Society of Immune Deficiencies) OR (Pan American Group for Immune Deficiency)) AND ((X-linked agammaglobulinemia) OR (common variable immunodeficiency)))"}
{"candidate_id": "LLM06922", "doc_id": "NCT02959580_exc", "case_bucket": "other", "source_criterion": "Breast Carcinoma", "candidate_expression": "(Breast Carcinoma)"}
{"candidate_id": "LLM06923", "doc_id": "NCT03317197_inc", "case_bucket": "other", "source_criterion": "The group of patients who participated in the study included adults aged at least 19 years among the atraumatic CA outpatients who came to the ER and received CPR.", "candidate_expression": "((CPR) AND (ER) AND (adults) AND (aged) AND (at least 19 years) AND (atraumatic CA) AND (outpatients))"}
{"candidate_id": "LLM06924", "doc_id": "NCT03325023_exc", "case_bucket": "or", "source_criterion": "Ovarian cancer, adrenal gland tumor, endometrial cancer, cervical cancer, breast cancer Congenital adrenal hyperplasia (17-OH-progesterone> 2.5 ng / mL) Clinically diagnosed Cushing's disease, acromegaly, gigantism Type I or II diabetes Unexplained bleeding from the genital tract Hormone treatment within the last 2 months", "candidate_expression": "((17-OH-progesterone > 2.5 ng / mL) AND (Congenital adrenal hyperplasia) AND (Cushing's disease) AND (Hormone) AND (Hormone treatment within the last 2 months) AND (Ovarian cancer) AND (Type I diabetes) AND (Type II diabetes) AND (Unexplained bleeding genital tract) AND (acromegaly) AND (adrenal gland tumor) AND (breast cancer) AND (cervical cancer) AND (endometrial cancer) AND (gigantism))"}
{"candidate_id": "LLM06925", "doc_id": "NCT03208127_exc", "case_bucket": "or", "source_criterion": "Pregnant or nursing (lactating) women HIV positivity Need for dual organ transplant Any contra-indication to liver transplantation per center protocol", "candidate_expression": "((HIV positivity) AND (contra-indication) AND (dual organ transplant Need for) AND (lactating) AND (liver transplantation) AND (women) AND ((Pregnant) OR (nursing)))"}
```
