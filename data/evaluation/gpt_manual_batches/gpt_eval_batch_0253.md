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
{"candidate_id": "LLM06301", "doc_id": "NCT03446885_inc", "case_bucket": "or", "source_criterion": "diagnosis of ADHD parental permission and/or teen consent/assent as appropriate between 16-25 years of age IQ greater than or equal to 70 permit or license to drive ability to read and understand English", "candidate_expression": "((16-25 years) AND (ADHD) AND (IQ) AND (ability to read English) AND (ability to understand English) AND (age) AND (greater than or equal to 70) AND (license to drive) AND (parental permission and/or teen consent/assent as appropriate) AND (permit to drive))"}
{"candidate_id": "LLM06302", "doc_id": "NCT00679341_exc", "case_bucket": "or", "source_criterion": "History of any chemotherapy for MBC. An interval of < 6 months from the completion of cytotoxic chemotherapy in the neo-adjuvant or adjuvant setting until the time of metastatic diagnosis. Trastuzumab ≤ 21 days prior to randomization. Hormone therapy < 7 days prior to randomization. Current peripheral neuropathy of Grade ≥ 3. History of other malignancy within the last 5 years, except for appropriately treated carcinoma in situ of the cervix, non-melanoma skin carcinoma, Stage I uterine cancer, or other cancers with a similar outcome as those previously mentioned. Previous radiotherapy for the treatment of unresectable, locally advanced or metastatic breast cancer is not allowed if more than 25% of marrow-bearing bone has been irradiated or the last fraction of radiotherapy has been administered within approximately 3 weeks prior to randomization. Brain metastases that are untreated, symptomatic, or require therapy to control symptoms or any radiation, surgery, or other therapy to control symptoms from brain metastases within 2 months prior to randomization. History of exposure to the following cumulative doses of anthracyclines: Doxorubicin or liposomal doxorubicin > 500 mg/m^2; epirubicin > 900 mg/m^2; mitoxantrone > 120mg/m^2 and idarubicin > 90 mg/m^2. Current unstable angina. History of symptomatic congestive heart failure, or ventricular arrhythmia requiring treatment. History of myocardial infarction within 6 months prior to randomization. Left ventricular ejection fraction (LVEF) below 50% within approximately 28 days prior to randomization. History of decreased LVEF or symptomatic congestive heart failure (CHF) with previous adjuvant trastuzumab treatment. Cardiac troponin I ≥ 0.2 ng/mL within 28 days of randomization. Severe dyspnea at rest because of complications of advanced malignancy or requiring current continuous oxygen therapy. Current severe, uncontrolled systemic disease (eg, clinically significant cardiovascular, pulmonary, or metabolic disease; wound healing disorders; ulcers; or bone fractures). Major surgical procedure or significant traumatic injury within approximately 28 days prior to randomization or anticipation of the need for major surgery during the course of study treatment. Current pregnancy or lactation. History of receiving any investigational treatment within approximately 28 days prior to randomization. Current known infection with human immunodeficiency virus (HIV), active hepatitis B and/or hepatitis C virus. History of intolerance (including Grade 3-4 infusion reaction) or hypersensitivity to trastuzumab, murine proteins, or docetaxel. Known hypersensitivity to any of the study drugs, including the excipients, or any drugs formulated in polysorbate 80. Assessed by the investigator to be unable or unwilling to comply with the requirements of the protocol.", "candidate_expression": "((Brain metastases untreated symptomatic require therapy) AND (Cardiac troponin I ≥ 0.2 ng/mL within 28 days of randomization) AND (Doxorubicin) AND (Grade 3-4) AND (Grade ≥ 3) AND (History) AND (Hormone therapy < 7 days prior to randomization) AND (LVEF History decreased) AND (Left ventricular ejection fraction (LVEF) below 50% within approximately 28 days prior to randomization) AND (MBC < 6 months) AND (Stage I) AND (Trastuzumab ≤ 21 days prior to randomization randomization) AND (advanced malignancy requiring current continuous oxygen therapy) AND (anthracyclines) AND (bone fractures) AND (brain metastases within 2 months prior to randomization randomization) AND (breast cancer metastatic) AND (carcinoma in situ of the cervix appropriately treated) AND (cardiovascular disease) AND (chemotherapy) AND (complications) AND (congestive heart failure (CHF) symptomatic) AND (congestive heart failure symptomatic) AND (continuous oxygen therapy current) AND (cytotoxic chemotherapy neo-adjuvant setting adjuvant setting) AND (docetaxel) AND (drugs formulated in polysorbate 80) AND (dyspnea Severe) AND (epirubicin > 900 mg/m^2) AND (hepatitis B virus) AND (hepatitis C virus) AND (human immunodeficiency virus (HIV) Current) AND (hypersensitivity) AND (idarubicin > 90 mg/m^2) AND (infusion reaction) AND (intolerance) AND (investigational treatment History of within approximately 28 days prior to randomization) AND (lactation) AND (liposomal doxorubicin) AND (major surgery anticipation of the need during the course of study treatment) AND (malignancy other within the last 5 years) AND (marrow-bearing bone irradiated more than 25%) AND (metabolic disease) AND (metastatic diagnosis) AND (mitoxantrone > 120mg/m^2) AND (murine proteins) AND (myocardial infarction within 6 months prior to randomization) AND (non-melanoma skin carcinoma) AND (other therapy to control symptoms) AND (peripheral neuropathy Current Grade ≥ 3) AND (pregnancy) AND (pulmonary disease) AND (radiation) AND (radiotherapy Previous unresectable locally advanced) AND (study drugs) AND (surgery) AND (surgical procedure Major) AND (systemic disease severe uncontrolled) AND (trastuzumab) AND (trastuzumab previous adjuvant) AND (traumatic injury significant) AND (treated) AND (treatment) AND (ulcers) AND (unable to comply with the requirements of the protocol) AND (unstable angina Current) AND (unwilling to comply with the requirements of the protocol) AND (uterine cancer) AND (ventricular arrhythmia requiring treatment) AND (wound healing disorders))"}
{"candidate_id": "LLM06303", "doc_id": "NCT03025620_inc", "case_bucket": "or", "source_criterion": "Elderly patients over 65 years old exhibiting clinical indices of cardiovascular disease Male or female Subjects who were hospitalized in the Geriatric Unit of the Emile Roux Hospital (AP-HP) MMSE (Mini Mental State Examination)score > or = 15 Supervision available for study medication Able to ingest oral diet", "candidate_expression": "((Able to ingest oral diet) AND (Elderly) AND (Geriatric Unit of the Emile Roux Hospital (AP-HP)) AND (MMSE (Mini Mental State Examination) score > or = 15) AND (old over 65 years) AND ((Male) OR (female)))"}
{"candidate_id": "LLM06304", "doc_id": "NCT02531971_inc", "case_bucket": "or", "source_criterion": "Men or non-pregnant women of any ethnic background between the age of 18 and 45 years old Subjects must be non-smokers (must have refrained from the use of nicotine-containing substances, including tobacco products (e.g. cigarettes, cigars, chewing tobacco, gum, patch or electronic cigarettes) over the previous 2 months and are not currently using tobacco products Provide written informed consent before initiation of any study procedures Available for follow-up for the planned duration of the study Able to communicate well with the investigators Able to adhere to the study protocol schedule, study restrictions and examination schedule Subjects who are within their ideal body weight (BMI between >17 and =28 kg/m2) Subjects deemed to be healthy as judged by the Medically Accountable Investigator (MAI) and determined by medical history, physical examination and medication history Subjects have no history of the following: ongoing acute or intermittent pain, postoperative pain, respiratory compromise, acute or severe asthma, or constipation (less than 1 bowel movement every 2 days) Negative urine drug screening test at the time of screening Have normal screening laboratories for white blood cells (WBC), hemoglobin (Hgb), platelets, sodium, potassium, chloride, bicarbonate, blood urea nitrogen (BUN), creatinine, ALT (liver function), AST (liver function) and bilirubin Have normal screening laboratories for urine protein and urine glucose Female subjects must be of non-childbearing potential (as defined as surgically sterile [i.e. history of hysterectomy or tubal ligation] or postmenopausal for more than 1 year [no bleeding for 12 consecutive months], or if of childbearing potential must be non-pregnant at the time of enrollment and on the morning of the first day of each study session, and must agree to use hormonal or barrier birth control such as implants, injectables, combined oral contraceptives, some intrauterine devices (IUDs), sexual abstinence or a vasectomized parter Agrees not to participate in another clinical study/trial during the study period or to participate in an investigational drug study for at least one month after last study session Agrees not to donate blood to a blood bank throughout participation in the study and for at least 3 months after last study day Have a normal ECG; must not have the following to be acceptable: pathologic Q wave abnormalities, significant ST-T wave changes, left ventricular hypertrophy, right bundle branch block, left bundle branch block. (sinus rhythm is between 55-100 beats per minute) Temperature 35-37.9°C (95-100.3°F) Systolic blood pressure 90-140 mmHg Diastolic blood pressure 60-90 mmHg Heart rate 55-100 beats per minute Respiration rate 12-18 breaths per minute", "candidate_expression": "((12-18 breaths per minute) AND (18 and 45 years old) AND (35-37.9°C) AND (55-100 beats per minute) AND (60-90 mmHg) AND (90-140 mmHg) AND (95-100.3°F) AND (ALT) AND (AST) AND (Able to adhere to the study protocol schedule, study restrictions and examination schedule) AND (Agrees not to participate in another clinical study/trial during the study period or to participate in an investigational drug study for at least one month after last study session) AND (Available for follow-up for the planned duration of the study) AND (BMI) AND (BUN) AND (Diastolic blood pressure) AND (ECG) AND (Female subjects must be of non-childbearing potential (as defined as surgically sterile [i.e. history of hysterectomy or tubal ligation] or postmenopausal for more than 1 year [no bleeding for 12 consecutive months], or if of childbearing potential must be non-pregnant at the time of enrollment and on the morning of the first day of each study session, and must agree to use hormonal or barrier birth control such as implants, injectables, combined oral contraceptives, some intrauterine devices (IUDs), sexual abstinence or a vasectomized parte) AND (Heart rate) AND (Hgb) AND (Negative) AND (Provide written informed consent before initiation of any study procedures) AND (Respiration rate) AND (ST-T wave changes) AND (Systolic blood pressure) AND (Temperature) AND (WBC) AND (age) AND (asthma) AND (between >17 and =28 kg/m2) AND (bicarbonate) AND (bilirubin) AND (blood urea nitrogen) AND (chloride) AND (constipation) AND (creatinine) AND (hemoglobin) AND (left bundle branch block) AND (left ventricular hypertrophy) AND (no) AND (non-pregnant) AND (non-smokers) AND (normal) AND (not) AND (pain) AND (pathologic Q wave abnormalities) AND (platelets) AND (postoperative) AND (potassium) AND (respiratory compromise) AND (right bundle branch block) AND (sodium) AND (urine drug screening test) AND (urine glucose) AND (urine protein) AND (white blood cells) AND ((Men) OR (women)) AND ((acute) OR (intermittent)) AND ((acute) OR (severe)))"}
{"candidate_id": "LLM06305", "doc_id": "NCT02946918_inc", "case_bucket": "or", "source_criterion": "Age > 18 years Presumed AJCC (American Joint Committee on Cancer) tumor Stage I or II Planned total or near-total thyroidectomy Planned goal TSH suppression 0.1-0.5 mU/L for at least 18 weeks postoperatively Normal serum TSH within 12 months preceding surgery", "candidate_expression": "((AJCC tumor Stage I) AND (Age > 18 years) AND (American Joint Committee on Cancer) AND (TSH suppression 0.1-0.5 mU/L at least 18 weeks postoperatively) AND (serum TSH Normal within 12 months preceding surgery) AND (thyroidectomy) AND ((near-total) OR (total)) AND ((I) OR (II)))"}
{"candidate_id": "LLM06306", "doc_id": "NCT02885909_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetic inpatient Fasting glucose >140 mg/dl or random glucose >180 mg/dl", "candidate_expression": "((Type 2 diabetic) AND (inpatient) AND ((Fasting glucose >140 mg/dl) OR (random glucose >180 mg/dl)))"}
{"candidate_id": "LLM06307", "doc_id": "NCT03624517_inc", "case_bucket": "or", "source_criterion": "Adult males and females who are 18 years of age or older. Evidence or suspicion of upper gastrointestinal bleed (GIB) Patient with known or suspected cirrhosis Upper GIB secondary to bleeding esophageal varices as show by esophageal endoscopy, requiring endoscopic band ligation (EBL) at presentation Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so", "candidate_expression": "((Adult 18 years of age or older) AND (Upper GIB secondary) AND (Willing and able to provide informed consent for study, or have a Legally authorized representative (LAR) provide consent if the patient is unable to do so) AND (cirrhosis) AND (endoscopic band ligation (EBL) requiring at presentation) AND (esophageal endoscopy) AND (esophageal varices bleeding) AND (upper gastrointestinal bleed (GIB)) AND ((known) OR (suspected)) AND ((females) OR (males)) AND ((Evidence) OR (suspicion)))"}
{"candidate_id": "LLM06308", "doc_id": "NCT02105090_inc", "case_bucket": "or", "source_criterion": "elective procedure weight over 40 kg American Society of Anesthesiology class I-III first upper GI endoscopy procedure finnish or/and swedish speaking", "candidate_expression": "((American Society of Anesthesiology class) AND (I-III) AND (elective procedure) AND (endoscopy procedure) AND (first) AND (over 40 kg) AND (upper GI) AND (weight) AND ((finnish speaking) OR (swedish speaking)))"}
{"candidate_id": "LLM06309", "doc_id": "NCT03122119_inc", "case_bucket": "other", "source_criterion": "Diagnosis of sacroiliitis Age 18 to 80 years old Chronic low back pain SI joint pathology is the predominant source of pain Positive Fortin Finger Test (PMT) Joint anatomy is identifiable using ultrasonography Patient has no other comorbidities that contraindicate the procedure Patient has attempted physical therapy and corticosteroid injections with local anesthetic -Previous injections of lidocaine and corticosteroid provided at least minor immediate relief Patient must not have had a corticosteroid injection in the SI joint within the last three months Patient must consent to the procedure", "candidate_expression": "((Age 18 to 80 years) AND (Chronic low back pain) AND (Fortin Finger Test (PMT) Positive) AND (SI joint pathology) AND (consent to the procedure) AND (corticosteroid injections) AND (ocal anesthetic) AND (physical therapy) AND (sacroiliitis) AND NOT (comorbidities that contraindicate the procedure other) AND NOT (corticosteroid injection SI joint within the last three months))"}
{"candidate_id": "LLM06310", "doc_id": "NCT02260206_exc", "case_bucket": "other", "source_criterion": "Hypersensitivity on Colchicine The existence of intra-cardiac thrombus on trans-esophageal echocardiography Pregnancy", "candidate_expression": "((Colchicine) AND (Hypersensitivity) AND (Pregnancy) AND (intra-cardiac thrombus) AND (trans-esophageal echocardiography))"}
{"candidate_id": "LLM06311", "doc_id": "NCT02571179_exc", "case_bucket": "or", "source_criterion": "a disease that might affect hepatic or renal function, contraindications to opioid analgesics, fetal growth retardation, signs of fetal asphyxia by cardiotocography, meconium stained amniotic fluid or placental insufficiency. The subjects should not have received fentanyl during the previous 14 days.", "candidate_expression": "((cardiotocography) AND (contraindications) AND (disease affect hepatic function affect renal function) AND (fetal asphyxia signs of) AND (fetal growth retardation) AND (meconium stained amniotic fluid) AND (opioid analgesics) AND (placental insufficiency) AND NOT (fentanyl during the previous 14 days))"}
{"candidate_id": "LLM06312", "doc_id": "NCT03513874_exc", "case_bucket": "or", "source_criterion": "History of any malignancy or other severe diseases Female patients who are pregnant or breastfeeding before or during the three-year follow-up Poor compliance or refusal to participate.", "candidate_expression": "((Female patients who are pregnant or breastfeeding before or during the three-year follow-up) AND ((malignancy) OR (severe diseases)) AND ((Poor compliance) OR (refusal to participate)))"}
{"candidate_id": "LLM06313", "doc_id": "NCT02668016_exc", "case_bucket": "or", "source_criterion": "History of neuropathy Regularly taking prescribed analgesia History of a chronic pain condition History of severe mental illness (as their experience of symptoms may already be altered) Current use of fibrates (because of the risk of interaction with statins but will not exclude participants taking ezetimibe). Severe previous reaction or reaction considered immunological, such as anaphylaxis, facial swelling, severe rash, muscle ache with rise in serum creatine kinase, inflammatory myopathy, rhabdomyolysis or liver function abnormalities (aspartate transaminase (AST) or alanine transaminase (ALT) greater than 3 times upper limit or normal). Side-effects taking longer than 2 weeks to develop (because in such participants much longer blocks of treatment would be required, if the present study is positive such studies will be planned for the future)*. History of statin intolerance with drug interaction to antiretroviral drugs. History of statin intolerance to any other drug. Pregnant or breast feeding. Side effects taking longer than 2 weeks to present. In clinical judgement of study doctor, participant should not participate.", "candidate_expression": "((ALT) AND (AST) AND (Pregnant or breast feeding) AND (analgesia Regularly) AND (antiretroviral drugs) AND (chronic pain) AND (fibrates) AND (intolerance) AND (mental illness severe) AND (neuropathy) AND (serum creatine kinase rise) AND (statin) AND ((alanine transaminase) OR (aspartate transaminase)) AND ((anaphylaxis) OR (facial swelling,) OR (inflammatory myopathy) OR (liver function abnormalities) OR (muscle ache) OR (rhabdomyolysis) OR (severe rash)))"}
{"candidate_id": "LLM06314", "doc_id": "NCT02715518_inc", "case_bucket": "or", "source_criterion": "Symptoms of ischaemia. New or presumed new significant ST-T wave changes Development of pathological Q waves on ECG. Imaging evidence of new or presumed new loss of viable myocardium or regional wall motion abnormality.", "candidate_expression": "((ECG) AND (Imaging) AND (ST-T wave changes significant) AND (evidence) AND (ischaemia Symptoms) AND (pathological Q waves) AND ((new) OR (presumed new)) AND ((loss of viable myocardium) OR (regional wall motion abnormality)) AND ((New) OR (presumed new)))"}
{"candidate_id": "LLM06315", "doc_id": "NCT02797548_inc", "case_bucket": "or", "source_criterion": "Planned non-cardiac surgery at least after 12 months of implantation of drug eluting stent Low or intermediate risk level surgery Written informed consent", "candidate_expression": "((Planned) AND (Written informed consent) AND (at least after 12 months of implantation of drug eluting stent) AND (drug eluting stent) AND (implantation) AND (implantation of drug eluting stent) AND (non-cardiac surgery) AND ((intermediate risk level surgery) OR (risk level surgery Low)))"}
{"candidate_id": "LLM06316", "doc_id": "NCT03084588_inc", "case_bucket": "other", "source_criterion": "All patients presenting for elective shoulder arthroscopic procedures will be eligible for enrollment.", "candidate_expression": "((elective) AND (shoulder arthroscopic procedures))"}
{"candidate_id": "LLM06317", "doc_id": "NCT02992938_exc", "case_bucket": "or", "source_criterion": "Patients ASA III y IV Chronic pain history Drug and alcohol abuse Chronic use of opioid and sedatives Neuropsychiatric illness NSAID and other analgesics used the 48 hours previous to the surgery CMI > 30", "candidate_expression": "((ASA III y IV) AND (CMI > 3) AND (Chronic pain) AND (Drug abuse) AND (NSAID) AND (Neuropsychiatric illness) AND (alcohol abuse) AND (analgesics other) AND (opioid) AND (sedatives))"}
{"candidate_id": "LLM06318", "doc_id": "NCT01991743_inc", "case_bucket": "other", "source_criterion": "Healthy patients age 18 and older Breech presentation Singleton gestation .scheduled for ECV desiring CSE.", "candidate_expression": "((18 and older) AND (Breech presentation) AND (CSE) AND (ECV) AND (Healthy) AND (Singleton gestation) AND (age) AND (desiring) AND (scheduled for))"}
{"candidate_id": "LLM06319", "doc_id": "NCT03619707_exc", "case_bucket": "or", "source_criterion": "Preexisting untreated medical condition (thyroid disease, diabetes mellitus, hypertension, pulmonary conditions, cardiac condition…) History of three or more consecutively failed In Vitro Fertilization (IVF) cycles after embryo transfer History of three or more miscarriages Previous allergy reactions to progesterone products", "candidate_expression": "((IVF) AND (In Vitro Fertilization) AND (Preexisting) AND (after embryo transfer) AND (allergy) AND (consecutively failed) AND (embryo transfer) AND (medical condition) AND (miscarriages) AND (progesterone products) AND (three or more) AND (untreated) AND ((cardiac condition) OR (diabetes mellitus) OR (hypertension) OR (pulmonary conditions) OR (thyroid disease)))"}
{"candidate_id": "LLM06320", "doc_id": "NCT02612181_exc", "case_bucket": "or", "source_criterion": "Age< 18 Pregnancy Bradycardia (HR<55bpm) Systolic Blood Pressure < 80 mmHg / Mean arterial pressure < 50 mmHg on maximal support Death imminent Unlikely to survive 90 days Acute liver failure Dementia High-grade block in the absence of a functioning pacemaker.", "candidate_expression": "((< 18) AND (< 50 mmHg) AND (< 80 mmHg) AND (<55bpm) AND (Acute liver failure) AND (Age) AND (Bradycardia) AND (Death) AND (Dementia) AND (HR) AND (High-grade block) AND (Pregnancy) AND (functioning) AND (imminent) AND (in the absence of) AND (on maximal support) AND (pacemaker) AND (support) AND ((Mean arterial pressure) OR (Systolic Blood Pressure)))"}
{"candidate_id": "LLM06321", "doc_id": "NCT03043495_inc", "case_bucket": "or", "source_criterion": "Patients undergoing surgeries in the upper limb (arm, forearm or hand)", "candidate_expression": "((surgeries) AND (upper limb) AND ((arm) OR (forearm) OR (hand)))"}
{"candidate_id": "LLM06322", "doc_id": "NCT03434951_exc", "case_bucket": "or", "source_criterion": "rearthroplasty ASA IV-V inadequate spoken finnish for reliable pain assessment Dementia or otherwise impaired cognition contraindication for any medication or substance used in survey protocol weight <50kg or BMI =35 kg/m2 preoperative SpO2 less than 93% clinical suspicion that subject can not use PCA adequately history of substance abuse or current excessive use of alcohol preoperative use of either pregabalin, gabapentin or strong opiates", "candidate_expression": "((ASA IV-V) AND (SpO2 preoperative less than 93%) AND (contraindication) AND (inadequate spoken finnish) AND (rearthroplasty) AND (reliable pain assessment) AND (subject can not use PCA adequately clinical suspicion) AND ((BMI =35 kg/m2) OR (weight <50kg)) AND ((excessive use of alcohol current) OR (substance abuse history)) AND ((gabapentin) OR (pregabalin) OR (strong opiates)) AND ((Dementia) OR (impaired cognition)) AND ((medication used in survey protocol) OR (substance used in survey protocol)))"}
{"candidate_id": "LLM06323", "doc_id": "NCT02315287_inc", "case_bucket": "or", "source_criterion": "HbA1c > 13.0 % No treatment with insulin or oral agents for 6 months 20 = Age < 80 years", "candidate_expression": "((> 13.0 %) AND (Age) AND (HbA1c) AND (No) AND (for 6 months) AND (treatment) AND ((insulin) OR (oral agents)) AND ((20 =) OR (< 80 years)))"}
{"candidate_id": "LLM06324", "doc_id": "NCT03129555_inc", "case_bucket": "or", "source_criterion": "A diagnosis of VTE in outpatient clinic or as discharge diagnosis after hospitalization. A claimed prescription of a NOAC from a Danish pharmacy within 14 days of discharge or outpatient clinic visit.", "candidate_expression": "((Danish pharmacy) AND (NOAC) AND (VTE) AND (after hospitalization) AND (claimed) AND (discharge or outpatient clinic visit) AND (hospitalization) AND (outpatient clinic) AND (prescription) AND (within 14 days of discharge or outpatient clinic visit) AND ((discharge) OR (outpatient clinic visit)) AND ((discharge diagnosis) OR (outpatient clinic)))"}
{"candidate_id": "LLM06325", "doc_id": "NCT02590653_inc", "case_bucket": "other", "source_criterion": "Signed Informed Consent Form Patients having physical and mental ability to participate in the study Patients of both sexes aged 35 to 65 years Presence of documented ST-elevation myocardial infarction confirmed by ECG, as well as troponin I and CK-MB levels. Presence of hemodynamically relevant stenosis of one artery (i.e., the infarct-related artery) confirmed by coronary angiography (CAG), with the occlusion of other arteries not exceeding 30%.", "candidate_expression": "((35 to 65 years) AND (CAG) AND (CK-MB) AND (ECG) AND (Patients having physical and mental ability to participate in the study) AND (ST-elevation myocardial infarction) AND (Signed Informed Consent Form) AND (aged) AND (both) AND (coronary angiography) AND (hemodynamically relevant) AND (infarct-related artery) AND (not exceeding 30%) AND (occlusion of other arteries) AND (one) AND (sexes) AND (stenosis of artery) AND (troponin I))"}
```
