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
{"candidate_id": "LLM01051", "doc_id": "NCT03146390_inc", "case_bucket": "other", "source_criterion": "Systemically healthy adults. Minimum of 24 permanent teeth. No gingivitis (Community Periodontal Index score = 0). No periodontitis (Community Periodontal Index score = 0). Absence of untreated caries.", "candidate_expression": "((Community Periodontal Index score = 0) AND (adults) AND (healthy Systemically) AND (permanent teeth Minimum of 24) AND NOT (periodontitis) AND NOT (caries untreated) AND NOT (gingivitis))"}
{"candidate_id": "LLM01052", "doc_id": "NCT01312012_exc", "case_bucket": "or", "source_criterion": "major systemic disease Pregnant woman with infection of human immunodeficiency virus or hepatitis C virus Pregnant woman is receiving any drug with antiviral activity or any form of drug therapy for hepatitis B virus Pregnant woman whose ultrasonographic examination reveals congenital anomaly of the fetus Pregnant woman whose amniocentesis reveals any genetic abnormality", "candidate_expression": "((Pregnant) AND (amniocentesis) AND (congenital anomaly of the fetus) AND (genetic abnormality) AND (hepatitis B virus) AND (major systemic disease) AND (ultrasonographic examination) AND (woman) AND ((hepatitis C virus) OR (human immunodeficiency virus)) AND ((drug therapy) OR (drug with antiviral activity)))"}
{"candidate_id": "LLM01053", "doc_id": "NCT03264911_inc", "case_bucket": "other", "source_criterion": "3 -15 years old Clinical symptoms suggestive of pharyngitis with MC Isaac score =3 Rapid-antigen detection test (RADT) positive for GAS- Signed informed parental/patient consent form", "candidate_expression": "((MC Isaac score =3) AND (RADT) AND (Rapid-antigen detection test positive) AND (Signed informed parental/patient consent form) AND (old 3 -15 years) AND (pharyngitis Clinical symptoms suggestive of))"}
{"candidate_id": "LLM01054", "doc_id": "NCT02415257_exc", "case_bucket": "other", "source_criterion": "impaired decision making neurofibromatosis signs for central dysfunction remaining vestibular function Patients are advised not to participate in the gentamicin arm if hearing is better than 30 deciBel (dB) in pure tone average (500, 1000, 2000, 3-4000 Hz) and speech discrimination better than 70% the neurosurgeon aim at hearing preservation surgery and do not want to risk gentamicin associated hearing loss", "candidate_expression": "((central dysfunction signs) AND (hearing better than 30 deciBel (dB) pure tone average) AND (impaired decision making) AND (neurofibromatosis) AND (remaining vestibular function) AND (speech discrimination better than 70% 500, 1000, 2000, 3-4000 Hz))"}
{"candidate_id": "LLM01055", "doc_id": "NCT01684501_exc", "case_bucket": "or", "source_criterion": "score level D on the SIGAM mobility grade have experienced 1 or more falls in the last month before the study have a residual limb length which does not allow for seven inches clearance of bracket attachment for the PowerFoot the residual limb must be stable in volume (no change in socket or socket padding in last 6 months) and without pain that limits function the sound-side (contralateral) lower extremity must be free of impediments that affect gait, range of motion, or limb muscle activity Any diagnosed cardiovascular, pulmonary, neurological, and/ or orthopedic conditions that would interfere with subject participation", "candidate_expression": "((1 or more) AND (SIGAM mobility grade) AND (cardiovascular conditions) AND (does not) AND (does not allow for seven inches clearance of bracket attachment) AND (falls) AND (free) AND (impediments that affect gait) AND (impediments that affect limb muscle activity) AND (impediments that affect range of motion) AND (in the last month before the study) AND (interfere with subject participation) AND (last month before the study) AND (level D) AND (lower extremity) AND (neurological conditions) AND (orthopedic conditions) AND (pulmonary conditions) AND (residual limb length))"}
{"candidate_id": "LLM01056", "doc_id": "NCT02798237_exc", "case_bucket": "or", "source_criterion": "cognitive impairment (Mini-Mental Status Examination score: illiterate 13 points; elementary and middle school 18 points; and high-school 26 points; or inability to respond to verbal command); inability to walk independently for at least 10 minutes, with or without walking devices; pain or other disorders precluding their participation.", "candidate_expression": "((Mini-Mental Status Examination score) AND (cognitive impairment) AND (inability to walk independently at least 10 minutes) AND (pain or other disorders precluding their participation) AND (walking devices) AND ((other disorders) OR (pain)) AND ((elementary) OR (middle school)) AND ((high-school 26 points) OR (illiterate 13 points) OR (inability to respond to verbal command)))"}
{"candidate_id": "LLM01057", "doc_id": "NCT02805504_exc", "case_bucket": "or", "source_criterion": "Pregnant and/or nursing mothers. Allergy to bupivacaine. History of drug/alcohol abuse. Severe cardiovascular, hepatic, renal disease or neurological impairment.", "candidate_expression": "((Allergy) AND (History) AND (bupivacaine) AND (drug/alcohol abuse) AND ((Pregnant) OR (nursing)) AND ((disease cardiovascular) OR (hepatic disease) OR (neurological impairment) OR (renal disease)))"}
{"candidate_id": "LLM01058", "doc_id": "NCT02055053_exc", "case_bucket": "other", "source_criterion": "Conversion from laparoscopic to open surgery History of Chronic pain or ongoing treatment for chronic pain Age less than 18 yrs Allergy to local anesthetics", "candidate_expression": "((Age) AND (Allergy) AND (Chronic pain) AND (History) AND (chronic pain) AND (less than 18 yrs) AND (local anesthetics) AND (ongoing) AND (treatment))"}
{"candidate_id": "LLM01059", "doc_id": "NCT02747940_exc", "case_bucket": "or", "source_criterion": "history of major systemic illness, including uncontrolled hypertension, diabetes, chronic renal insufficiency, autoimmune diseases or malignancies history of neurological disorders which might affect sensation such as previous stroke or peripheral neuropathy history of substance abuse (except painkillers) heavy smokers (with a daily consumption >20 cigarettes) pregnancy or lactation any contraindication for magnetic resonance imaging (MRI) and any obvious infection or inflammation over a period of at least 1 month before the study.", "candidate_expression": "((MRI) AND (affect sensation) AND (cigarettes daily consumption >20) AND (contraindication) AND (magnetic resonance imaging) AND (neurological disorders) AND (pregnancy or lactation) AND (smokers heavy) AND (substance abuse) AND (systemic illness major) AND NOT (painkillers) AND ((peripheral neuropathy) OR (stroke)) AND ((infection) OR (inflammation)) AND ((autoimmune diseases) OR (chronic renal insufficiency,) OR (diabetes) OR (hypertension uncontrolled) OR (malignancies)))"}
{"candidate_id": "LLM01060", "doc_id": "NCT02570230_exc", "case_bucket": "or", "source_criterion": "allergy to morphine or ketamine contraindicate to ketamine remain intubated in the postoperative period", "candidate_expression": "((allergy) AND (contraindicate) AND (intubated) AND (intubated in the postoperative period) AND (ketamine) AND (morphine))"}
{"candidate_id": "LLM01061", "doc_id": "NCT01996436_inc", "case_bucket": "other", "source_criterion": "Adult patient, age 18-80 years old, with ruptured aneurysm(s) who experience cerebral vasospasm post operatively within 3-21 days.", "candidate_expression": "((18-80 years old) AND (Adult) AND (age) AND (cerebral vasospasm) AND (post operatively) AND (post operatively within 3-21 days) AND (ruptured aneurysm))"}
{"candidate_id": "LLM01062", "doc_id": "NCT03536520_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((40-75 yr) AND (Healthy) AND (Written informed consent) AND (age) AND (any) AND (disease) AND (medication) AND (without) AND ((men) OR (women)))"}
{"candidate_id": "LLM01063", "doc_id": "NCT02996916_exc", "case_bucket": "or", "source_criterion": "Secondary hypertension or malignant hypertension Diabetes mellitus History or evidence of a stroke Hepatic or hematologic abnormality Mild Cognitive Impairment or Dementia Serum potassium level = 5.5 mEq/L Serum creatinine level = 3.0 mg/dL Acute or chronic disease Allergy to any drugs Pregnancy", "candidate_expression": "((= 3.0 mg/dL) AND (= 5.5 mEq/L) AND (Acute disease) AND (Allergy) AND (Dementia) AND (Diabetes mellitus) AND (Hepatic abnormality) AND (History) AND (Mild Cognitive Impairment) AND (Pregnancy) AND (Secondary hypertension) AND (Serum creatinine level) AND (Serum potassium level) AND (any drugs) AND (chronic disease) AND (evidence) AND (hematologic abnormality) AND (malignant hypertension) AND (stroke))"}
{"candidate_id": "LLM01064", "doc_id": "NCT02366819_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed locally advanced gastric (primary endpoint includes proximal and mid-body stomach) or esophagogastric adenocarcinoma; distal gastric (antral) adenocarcinomas are eligible for enrolment but will not be included in the primary analysis Locally advanced disease as determined by endoscopic ultrasound (EUS) stage > primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx) All patients must have diagnostic laparoscopy with diagnostic washings for cytology; both cytology positive and negative patients are eligible for enrolment, but only cytology negative patients will be included in the primary analyses; gross peritoneal disease is not eligible Eastern Cooperative Oncology Group (ECOG) performance status =< 1 Eligible for surgery with curative intent Absolute neutrophil count (ANC) >= 1250/ul Hemoglobin >= 9 g/dL Platelets >= 100,000/ul Total bilirubin < 1.5 x upper limit of normal Serum glutamic oxaloacetic transaminase (SGOT) and serum glutamate pyruvate transaminase (SGPT) < 2.5 x upper limit of normal for patients without liver metastases OR SGOT and SGPT < 5 x upper limit of normal for patients with liver metastases Creatinine =< 1.5 x upper limit of normal Measurable or non-measurable disease by Response Evaluation Criteria in Solid Tumor (RECIST) 1.1 will be allowed Women of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately Patients taking substrates, inhibitors, or inducers of cytochrome P450, family 3, subfamily A, polypeptide 4 (CYP3A4) should be encouraged to switch to alternative drugs whenever possible, given the potential for drug-drug interactions with irinotecan Signed informed consent", "candidate_expression": "((ANC) AND (Absolute neutrophil count >= 1250/ul) AND (Creatinine =< 1.5 x upper limit of normal) AND (ECOG) AND (EUS) AND (Eastern Cooperative Oncology Group performance status =< 1) AND (Hemoglobin >= 9 g/dL) AND (Platelets >= 100,000/ul) AND (RECIST) AND (Response Evaluation Criteria in Solid Tumor 1.1) AND (SGOT) AND (SGPT) AND (Serum glutamic oxaloacetic transaminase) AND (Signed informed consent) AND (Total bilirubin < 1.5 x upper limit of normal) AND (adenocarcinomas distal gastric antral) AND (cytology) AND (disease Locally advanced) AND (endoscopic ultrasound > primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx)) AND (laparoscopy diagnostic) AND (liver metastases) AND (omen of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately) AND (serum glutamate pyruvate transaminase) AND (surgery curative) AND (washings for cytology) AND NOT (liver metastases) AND ((adenocarcinoma gastric) OR (esophagogastric adenocarcinoma)) AND ((negative) OR (positive)) AND ((mid-body stomach) OR (proximal stomach)))"}
{"candidate_id": "LLM01065", "doc_id": "NCT03407625_exc", "case_bucket": "other", "source_criterion": "latex allergy non-reassuring fetal status HIV active herpes outbreak Prior uterine scar Contraindication to prostaglandins according to current Parkland protocol Contraindication to vaginal delivery", "candidate_expression": "((Contraindication) AND (HIV) AND (Parkland protocol) AND (allergy) AND (fetal status non-reassuring) AND (herpes active) AND (latex) AND (prostaglandins) AND (uterine scar) AND (vaginal delivery))"}
{"candidate_id": "LLM01066", "doc_id": "NCT02805504_inc", "case_bucket": "other", "source_criterion": "Patients undergoing urologic surgery.", "candidate_expression": "(urologic surgery)"}
{"candidate_id": "LLM01067", "doc_id": "NCT03424733_exc", "case_bucket": "or", "source_criterion": "prior allergic reaction to interferon products, congestive heart failure, elevated liver enzymes", "candidate_expression": "((interferon products) AND (prior) AND ((allergic reaction) OR (congestive heart failure) OR (elevated liver enzymes)))"}
{"candidate_id": "LLM01068", "doc_id": "NCT03280017_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist physical status 1-3 Scheduled for elective video-assisted thoracic surgery Able to operate a patient-controlled analgesia device (PCA)", "candidate_expression": "((1-3) AND (American Society of Anesthesiologist physical status) AND (PCA) AND (Scheduled for) AND (elective) AND (patient-controlled analgesia device) AND (video-assisted thoracic surgery))"}
{"candidate_id": "LLM01069", "doc_id": "NCT03159507_inc", "case_bucket": "other", "source_criterion": "Participant aged 19 or over Available for the entire duration of the study and willing to participate on the basis of the information provided in the FIU duly read and signed.", "candidate_expression": "((Available for the entire duration of the study and willing to participate on the basis of the information provided in the FIU duly read and signed.) AND (aged 19 or over))"}
{"candidate_id": "LLM01070", "doc_id": "NCT03280017_exc", "case_bucket": "other", "source_criterion": "History of morphine allergy History of bupivacaine allergy Contraindication for ketamine infusion Contraindication for thoracic paravertebral block Anticipated postoperative positive pressure ventilation Body mass index more than 35 Any known psychiatric disorder", "candidate_expression": "((Anticipated) AND (Body mass index) AND (Contraindication) AND (History) AND (allergy) AND (bupivacaine) AND (ketamine) AND (ketamine infusion) AND (more than 35) AND (morphine) AND (paravertebral block) AND (positive pressure ventilation) AND (postoperative) AND (psychiatric disorder) AND (thoracic))"}
{"candidate_id": "LLM01071", "doc_id": "NCT02995291_exc", "case_bucket": "or", "source_criterion": "contra-indications for regular dental treatment medical history that contraindicates the use of epinephrine participant taken an opioid or an opioid like analgesic within 24 hours pregnant", "candidate_expression": "((contra-indications) AND (contraindicates) AND (epinephrine) AND (medical history) AND (opioid) AND (opioid like analgesic) AND (pregnant) AND (regular dental treatment) AND (within 24 hours))"}
{"candidate_id": "LLM01072", "doc_id": "NCT03472495_inc", "case_bucket": "or", "source_criterion": ">/= 18 years old Atrial fibrillation or flutter on electrocardiogram Heart rate >110 beats/min Systolic blood pressure >/= 90 mmHg", "candidate_expression": "((Atrial fibrillation) AND (Atrial flutter) AND (Heart rate >110 beats/min) AND (Systolic blood pressure >/= 90 mmHg) AND (electrocardiogram) AND (old >/= 18 years old))"}
{"candidate_id": "LLM01073", "doc_id": "NCT02804646_exc", "case_bucket": "or", "source_criterion": "1) pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;2) existing severe acute infection and is not controlled; or purulent and chronic infection, delayed healing wounds; 3) the original severe heart disease, including congestive heart failure, uncontrolled high-risk arrhythmias, unstable angina, myocardial infarction, severe heart valve disease and resistant hypertension; 4) suffering from neurological and psychiatric diseases or mental disorders is not easy to control, poor compliance, and can not be described with treatment responders; primary brain or central nervous metastasis disease has not been controlled, with significant cranial hypertension or neuropsychiatric symptoms; 5) have bleeding tendencies; 6) other researchers believe that patients should not participate in the present trial.", "candidate_expression": "((bleeding tendencies) AND (delayed healing wounds) AND (heart disease severe) AND (infection purulent chronic) AND (infection severe acute not controlled) AND (pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;) AND ((arrhythmias uncontrolled high-risk) OR (congestive heart failure) OR (heart valve disease severe) OR (hypertension resistant) OR (myocardial infarction) OR (unstable angina)) AND ((mental disorders) OR (neurological diseases) OR (poor compliance) OR (psychiatric diseases)) AND ((central nervous metastasis disease) OR (primary brain disease)) AND ((cranial hypertension) OR (neuropsychiatric symptoms)))"}
{"candidate_id": "LLM01074", "doc_id": "NCT02564471_exc", "case_bucket": "or", "source_criterion": "Subject is pregnant, or lactating, or of childbearing potential (to be considered of non-childbearing potential, a female must be post-menopausal for at least 1 year, surgically sterile, or using an effective method of contraception or abstinence from at least 4 weeks prior to the first vaccination and until at least 4 weeks after the last vaccination. Participation in the 4 weeks preceding the first trial vaccination, or planned participation during the present trial period, in another clinical trial investigating a vaccine, drug, medical device, or medical procedure. Previous history of receiving the rabies vaccine. Previous history of receiving rabies immune globulin. Any major psychiatric disorder, such as severe depression, severe anxiety disorder, psychosis, schizophrenia, other major psychiatric disorders, or seizures. History of mild depression or anxiety disorder that are well controlled are not exclusion criteria. Use of any immunosuppressive drug at the time of the study or 30 days previously. Topical steroids will not be considered an immunosuppressive drug and their use will not be considered an exclusion criteria. Any immunosuppressive disorder, such as HIV infection, common variable immunodeficiency, active cancers or chemotherapy. History of renal insufficiency or requiring dialysis. Have any condition that would, in the opinion of the site investigator, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol. Identified as an employee of the Investigator or study center, with direct involvement in the proposed study or other studies under the direction of that Investigator or study center, as well as family members (i.e., immediate, husband, wife and their children, adopted or natural) of the employee or the Investigator. Previous adverse reaction to any of the antimalarial drugs used in this study.", "candidate_expression": "((Have any condition that would, in the opinion of the site investigator, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol.) AND (History) AND (Identified as an employee of the Investigator or study center, with direct involvement in the proposed study or other studies under the direction of that Investigator or study center, as well as family members (i.e., immediate, husband, wife and their children, adopted or natural) of the employee or the Investigator.) AND (Previous) AND (Previous history) AND (Subject is pregnant, or lactating, or of childbearing potential (to be considered of non-childbearing potential, a female must be post-menopausal for at least 1 year, surgically sterile, or using an effective method of contraception or abstinence from at least 4 weeks prior to the first vaccination and until at least 4 weeks after the last vaccination.) AND (Topical steroids) AND (active) AND (adverse reaction) AND (antimalarial drugs) AND (immunosuppressive disorder) AND (immunosuppressive drug) AND (major psychiatric disorder) AND (mild) AND (not) AND (other) AND (rabies immune globulin) AND (rabies vaccine) AND (requiring) AND (severe) AND (used in this study) AND (well controlled) AND ((anxiety disorder) OR (depression) OR (major psychiatric disorders) OR (psychosis) OR (schizophrenia) OR (seizures)) AND ((anxiety disorder) OR (depression)) AND ((30 days previously) OR (at the time of the study)) AND ((HIV infection) OR (common variable immunodeficiency)) AND ((cancers) OR (chemotherapy)) AND ((dialysis) OR (renal insufficiency)))"}
{"candidate_id": "LLM01075", "doc_id": "NCT00718952_exc", "case_bucket": "or", "source_criterion": "The other types of pulmonary hypertension. Subjects who refuse to subscribe written informed consents or can't cooperate with the trial well. Subjects with serious acute or chronic disease involved liver, kidney, and brain or have to use potent CYP3A4-inhibitor or nitrate to treat the underlying diseases. Subjects who are currently treated with sildenafil for PAH or taking sildenafil or tadalafil. Other contraindications in package insert.", "candidate_expression": "((PAH) AND (acute) AND (contraindications in package insert) AND (currently) AND (other types) AND (potent) AND (pulmonary hypertension) AND (serious) AND (underlying diseases) AND ((sildenafil) OR (tadalafil)) AND ((can't cooperate with the trial) OR (refuse to subscribe written informed consents)) AND ((chronic disease involved brain) OR (chronic disease involved kidney) OR (chronic disease involved liver)) AND ((CYP3A4-inhibitor) OR (nitrate)))"}
```
