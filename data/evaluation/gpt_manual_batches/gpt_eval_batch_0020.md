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
{"candidate_id": "LLM00476", "doc_id": "NCT00867958_inc", "case_bucket": "other", "source_criterion": "1. Patient is over 18 years old. 2. Patient is scheduled for a non-emergency procedure. 3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.", "candidate_expression": "((3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.) AND (non-emergency procedure scheduled non-emergency) AND (years old over 18 years old))"}
{"candidate_id": "LLM00477", "doc_id": "NCT01373684_exc", "case_bucket": "or", "source_criterion": "Treatment with any investigational drug within 30 days of entry to this protocol Current treatment with Telbivudine Severe hepatitis activity as documented by ALT>10 x ULN History of decompensated cirrhosis (defined as jaundice in the presence of cirrhosis, ascites, bleeding gastric or esophageal varices or encephalopathy) Pre-existent neutropenia (neutrophils <1,500/mm3) or thrombocytopenia (platelets < 90,000/mm3) Co-infection with hepatitis C virus, hepatitis D virus or human immunodeficiency virus (HIV) Other acquired or inherited causes of liver disease: alcoholic liver disease, obesity induced liver disease, drug related liver disease, auto-immune hepatitis, hemochromatosis, Wilson's disease or alpha-1 antitrypsin deficiency Alpha fetoprotein > 50 ng/ml Hyper- or hypothyroidism (subjects requiring medication to maintain TSH levels in the normal range are eligible if all other inclusion/exclusion criteria are met) Immune suppressive treatment within the previous 6 months Contra-indications for alfa-interferon therapy like suspected hypersensitivity to interferon or Peginterferon or any known pre-existing medical condition that could interfere with the patient's participation in and completion of the study. Pregnancy, breast-feeding Other significant medical illness that might interfere with this study: significant pulmonary dysfunction in the previous 6 months, malignancy other than skin basocellular carcinoma in previous 5 years, immunodeficiency syndromes (e.g. HIV positivity, auto-immune diseases, organ transplants other than cornea and hair transplant) Any medical condition requiring, or likely to require chronic systemic administration of steroids, during the course of the study Substance abuse, such as alcohol (>80 g/day), I.V. drugs and inhaled drugs in the past 2 years. Any other condition which in the opinion of the investigator would make the patient unsuitable for enrollment, or could interfere with the patient participating in and completing the study", "candidate_expression": "((ALT >10 x ULN) AND (Alpha fetoprotein > 50 ng/ml) AND (Co-infection) AND (Contra-indications) AND (Immune suppressive treatment within the previous 6 months) AND (Pregnancy, breast-feeding) AND (Substance abuse in the past 2 years.) AND (Telbivudine) AND (Treatment with any investigational drug within 30 days of entry to this protocol) AND (alfa-interferon therapy) AND (ascites) AND (cirrhosis) AND (cirrhosis decompensated) AND (hepatitis Severe) AND (hypersensitivity) AND (jaundice) AND (liver disease HIV) AND (malignancy) AND (medical illness significant) AND (medication) AND (neutrophils <1,500/mm3) AND (organ transplants) AND (platelets < 90,000/mm3) AND (systemic steroids chronic during the course of the study) AND NOT (skin basocellular carcinoma) AND ((bleeding gastric) OR (encephalopathy) OR (esophageal varices)) AND ((neutropenia Pre-existent) OR (thrombocytopenia)) AND ((hepatitis C virus) OR (hepatitis D virus) OR (human immunodeficiency virus)) AND ((acquired) OR (inherited)) AND ((Wilson's disease) OR (alcoholic liver disease) OR (alpha-1 antitrypsin deficiency) OR (auto-immune hepatitis) OR (drug related liver disease) OR (hemochromatosis) OR (obesity induced liver disease)) AND ((Hyper thyroidism) OR (hypothyroidism)) AND ((Peginterferon) OR (interferon)) AND ((immunodeficiency syndromes) OR (pulmonary dysfunction significant in the previous 6 months)) AND ((HIV positivity) OR (auto-immune diseases)) AND ((cornea transplant) OR (hair transplant)) AND ((I.V. drugs) OR (alcohol >80 g/day) OR (inhaled drugs)))"}
{"candidate_id": "LLM00478", "doc_id": "NCT03247738_exc", "case_bucket": "or", "source_criterion": "Inability to provide written informed consent Known history of prior intracranial bleeding On treatment with a P2Y12 receptor antagonist (ticlopidine, clopidogrel, prasugrel, ticagrelor) in the prior 10 days Known allergies to aspirin, ticagrelor or cangrelor On treatment with oral anticoagulant Treatment with glycoprotein IIb/IIIa inhibitors Fibrinolytics within 24 hours Active bleeding High risk of bleeding Known platelet count <80x106/mL Known hemoglobin <10 g/dL Intubated patients (prior to randomization) Known creatinine clearance <30 mL/minute or on hemodialysis. Known severe hepatic dysfunction Patients with sick sinus syndrome (SSS) or high degree AV block without pacemaker protection Current treatment with drugs interfering with CYP3A4 metabolism (to avoid interaction with ticagrelor): Ketoconazole, itraconazole, voriconazole, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, and telithromizycin. Pregnant or lactating females.", "candidate_expression": "((AV block high degree) AND (Active bleeding) AND (CYP3A4 metabolism interfering with) AND (Fibrinolytics within 24 hours) AND (Inability to provide written informed consent) AND (Intubated prior to randomization) AND (Ketoconazole) AND (P2Y12 receptor antagonist prior 10 days) AND (Pregnant) AND (SSS) AND (allergies) AND (anticoagulant oral) AND (aspirin) AND (atazanavir) AND (bleeding High risk) AND (cangrelor) AND (clarithromycin) AND (clopidogrel) AND (creatinine clearance <30 mL/minute) AND (drugs) AND (females) AND (glycoprotein IIb/IIIa inhibitors) AND (hemodialysis) AND (hemoglobin <10 g/dL) AND (hepatic dysfunction severe) AND (indinavir) AND (intracranial bleeding prior) AND (itraconazole) AND (lactating) AND (nefazodone) AND (nelfinavir) AND (platelet count <80x106/mL) AND (prasugrel) AND (ritonavir) AND (saquinavir) AND (sick sinus syndrome) AND (telithromizycin) AND (ticagrelor) AND (ticlopidine) AND (voriconazole) AND NOT (pacemaker))"}
{"candidate_id": "LLM00479", "doc_id": "NCT02762851_exc", "case_bucket": "or", "source_criterion": "Anaphylactic reaction to a previous dose of TIV(trivalent influenza vaccine) Known IgE( Immunoglobulin E)-mediated hypersensitivity to eggs manifested as hives, swelling of the mouth and throat, difficulty in breathing, hypotension, or shock Guillain-Barré syndrome within eight weeks of a previous influenza vaccine Anaphylactic reaction to neomycin Patients who have had influenza vaccine in two of the three previous years", "candidate_expression": "((Anaphylactic reaction) AND (Guillain-Barré syndrome within eight weeks of a previous influenza vaccine) AND (IgE( Immunoglobulin E)-mediated hypersensitivity) AND (TIV) AND (eggs) AND (influenza vaccine in two of the three previous years) AND (influenza vaccine previous) AND (neomycin) AND (trivalent influenza vaccine) AND ((difficulty in breathing) OR (hives) OR (hypotension) OR (shock) OR (swelling of the mouth and throat)))"}
{"candidate_id": "LLM00480", "doc_id": "NCT00500500_exc", "case_bucket": "or", "source_criterion": "patient already treated by medicines which could interfere with the study low level of vitamin B12 and folate which are considered as clinically relevant clinically relevant pathologies (eg: pulmonary illness, cardiovascular illness; evolutive cancer, neurological illness, blood illness….)", "candidate_expression": "((blood illness) AND (cardiovascular illness) AND (evolutive cancer) AND (folate level of low) AND (level of vitamin B12 low) AND (neurological illness) AND (pulmonary illness))"}
{"candidate_id": "LLM00481", "doc_id": "NCT02590315_exc", "case_bucket": "other", "source_criterion": "Personal history of breast cancer A terminal illness Patients who are unable to give informed consent Breast implants", "candidate_expression": "((Breast implants) AND (Personal history) AND (breast cancer) AND (terminal illness) AND (unable to give informed consent))"}
{"candidate_id": "LLM00482", "doc_id": "NCT03146390_exc", "case_bucket": "or", "source_criterion": "Smoker or former smoker. Presence of dental prostheses. Presence of orthodontic devices. Antibiotic treatment or routine use of oral antiseptics in the previous 3 months. Presence of any systemic disease that could alter the production or composition of saliva.", "candidate_expression": "((Antibiotic) AND (could alter the production or composition of saliva) AND (dental prostheses) AND (in the previous 3 months) AND (oral antiseptics) AND (orthodontic devices) AND (routine use) AND (systemic disease) AND ((Smoker) OR (former smoker)))"}
{"candidate_id": "LLM00483", "doc_id": "NCT02894268_inc", "case_bucket": "other", "source_criterion": "A positive 13 C-urea breath test Formal H.pylori treatment more than two times Age >18 years", "candidate_expression": "((13 C-urea breath test) AND (>18 years) AND (Age) AND (H.pylori treatment) AND (more than two times) AND (positive))"}
{"candidate_id": "LLM00484", "doc_id": "NCT02950558_exc", "case_bucket": "or", "source_criterion": "Unable to give informed consent in English Unable to complete surveys in English Unable to understand instructions for using pump in English Unavailable for followup Polytrauma; undergoing other surgeries or having other orthopedic injuries related to the precipitating cause of the ankle fracture Infection Peripheral vascular disease Diabetes Currently undergoing chemotherapy Pregnancy Currently lactating Heart disease or heart rhythm disorder or taking anti-arrhythmic drugs Severe renal impairment (Class 3 or worse kidney disease) Liver disease (cirrhosis or liver failure) Prior allergic reaction to any type of local anesthetic Taking therapeutic doses of anti-coagulants or anti-platelet therapy (prophylactic doses started because of hospital admission are not an exclusion) Currently taking antidepressants or other psychiatric medications Single shot local nerve block prior to surgery was ineffective Selected for neuraxial anesthesia rather than general anesthesia for the open reduction surgery Already receiving chronic analgesic therapy for a separate chronic pain condition", "candidate_expression": "((Currently lactating) AND (Diabetes) AND (Infection) AND (Liver disease) AND (Peripheral vascular disease) AND (Polytrauma) AND (Pregnancy) AND (Severe renal impairment) AND (Single shot) AND (Unable to complete surveys in English) AND (Unable to give informed consent in English) AND (Unable to understand instructions for using pump in English) AND (Unavailable for followup) AND (allergic reaction) AND (analgesic therapy) AND (ankle fracture) AND (chemotherapy) AND (chronic) AND (chronic pain) AND (general anesthesia) AND (local anesthetic) AND (local nerve block) AND (neuraxial anesthesia) AND (not) AND (open reduction surgery) AND (prior to surgery) AND (prophylactic) AND (rather than) AND (separate) AND (surgery) AND (therapeutic) AND ((Heart disease) OR (anti-arrhythmic drugs) OR (heart rhythm disorder)) AND ((cirrhosis) OR (liver failure)) AND ((anti-coagulants) OR (anti-platelet therapy)) AND ((antidepressants) OR (psychiatric medications)) AND ((other orthopedic injuries) OR (other surgeries)))"}
{"candidate_id": "LLM00485", "doc_id": "NCT00806273_inc", "case_bucket": "other", "source_criterion": "ASA 1 ASA 2 Pts have current treatment plan at OHSU for extraction of some or all of remaining teeth and scheduled for delivery of a removable appliance post extraction Teeth used are able to be isolated with rubber dam Understand and sign consent form", "candidate_expression": "((ASA 1) AND (ASA 2) AND (Understand and sign consent form) AND (scheduled for) AND (treatment plan at OHSU))"}
{"candidate_id": "LLM00486", "doc_id": "NCT02334722_inc", "case_bucket": "or", "source_criterion": "Adult (>18 years of age and older) patients who have or will have undergone surgical resection or biopsy of a supratentorial brain tumor and are able to consent for themselves. Able to be randomized prior to or up to 48 hours after surgery.", "candidate_expression": "((Adult) AND (age and older >18 years) AND (are able to consent for themselves) AND (supratentorial brain tumor) AND ((biopsy) OR (surgical resection)))"}
{"candidate_id": "LLM00487", "doc_id": "NCT03397914_inc", "case_bucket": "or", "source_criterion": "Age between one year and 18 years Sepsis due to MDR or minimally susceptible gram-negative bacteria History of MDR gram-negative infection or sepsis due to organisms sensitive to colistin. Culture result consistent with MDR gram negative for this febrile neutropenic episode. Patient in sepsis and colistin was administered empirically to increase antibiotic coverage.", "candidate_expression": "((Age) AND (MDR) AND (Sepsis) AND (administered empirically) AND (between one year and 18 years) AND (colistin) AND (gram negative) AND (minimally susceptible gram-negative bacteria) AND (organisms) AND (sensitive to colistin) AND (sepsis) AND ((gram-negative infection) OR (sepsis)))"}
{"candidate_id": "LLM00488", "doc_id": "NCT01346436_inc", "case_bucket": "other", "source_criterion": "women proven pelvic floor dysfunction informed consent", "candidate_expression": "((nformed consent) AND (pelvic floor dysfunction) AND (women))"}
{"candidate_id": "LLM00489", "doc_id": "NCT02760459_inc", "case_bucket": "other", "source_criterion": "Age > 40 years (45) Primary knee osteoarthritis diagnosed using the American College of Rheumatology criteria (46) Undergoing elective, primary and unilateral total knee arthroplasty American Society of Anesthesiology (ASA) physical status class 1-3 BMI < 40 kg/m2", "candidate_expression": "((1-3) AND (< 40 kg/m2) AND (> 40 years) AND (ASA) AND (Age) AND (American College of Rheumatology criteria) AND (American Society of Anesthesiology physical status class) AND (BMI) AND (Primary knee osteoarthritis) AND (elective) AND (primary) AND (total knee arthroplasty) AND (unilateral))"}
{"candidate_id": "LLM00490", "doc_id": "NCT02283996_inc", "case_bucket": "other", "source_criterion": "Patient must be 18 years or older Must meet the following definition for adhesive capsulitis as defined by the American Academy of Orthopedic Surgeons: Self-limiting condition resulting from any inflammatory process about the shoulder in which capsular scar tissue is produced, resulting in pain and limited range of motion; also called frozen shoulder Must be amenable to randomization into either cohort", "candidate_expression": "((American Academy of Orthopedic Surgeons) AND (Must be amenable to randomization into either cohort) AND (adhesive capsulitis) AND (years 18 or older))"}
{"candidate_id": "LLM00491", "doc_id": "NCT03372265_inc", "case_bucket": "or", "source_criterion": "Age = 18 years American Society of Anesthesiologists Classification I-III Normal cognitive function in order to sign written, informed consent and to understand trial protocol Agreement to the trial protocol, including the randomized manner", "candidate_expression": "((Age = 18 years) AND (Agreement to the randomized manner) AND (Agreement to the trial protocol) AND (American Society of Anesthesiologists Classification I-III) AND (cognitive function Normal))"}
{"candidate_id": "LLM00492", "doc_id": "NCT01816997_inc", "case_bucket": "other", "source_criterion": "Age 35-70 years old Fasting blood glucose 100-125 mg/dL", "candidate_expression": "((Age 35-70 years old) AND (Fasting blood glucose 100-125 mg/dL))"}
{"candidate_id": "LLM00493", "doc_id": "NCT02952378_exc", "case_bucket": "or", "source_criterion": "Heart failure Signs of kidney injury/failure Severe allergies", "candidate_expression": "((Heart failure) AND (allergies Severe) AND (kidney failure) AND (kidney injury))"}
{"candidate_id": "LLM00494", "doc_id": "NCT03318874_exc", "case_bucket": "or", "source_criterion": "Glaucoma, Ocular allergy Autoimmune disease Contact lens-wear during study Current punctal plugging Pregnant/lactating Candidate for topical anti-inflammatory Cicatricial meibomian gland dysfunction", "candidate_expression": "((Autoimmune disease) AND (Candidate for) AND (Cicatricial) AND (Contact lens-wear) AND (Current) AND (Glaucoma) AND (Ocular allergy) AND (during study) AND (meibomian gland dysfunction) AND (punctal plugging) AND (topical anti-inflammatory) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM00495", "doc_id": "NCT02321202_exc", "case_bucket": "or", "source_criterion": "Contraindication for hepatectomy, including gastrointestinal hemorrhage, severe hemorrhagic disorders, explicit acute nonspecific infectious lesion, overt ascites, Child-Pugh Score C, indocyanine green retention rate at 15min (ICGR15)＞30%(12), serum hepatitis B virus (HBV)-DNA＞126 copies/ml and serum alanine aminotransferase (ALT) ＞ 2×ULN, serum triglycerides＞2.0 mmol/L, circulatory shock, stroke, acute myocardial infarction, renal failure, coma of unknown cause Pregnancy Age of＜18y or＞75y Performed intraoperative ablation Unresectable tumor during operation Allergic reactions against fish or egg proteins", "candidate_expression": "((Age) AND (Allergic reactions) AND (C) AND (Contraindication for hepatectomy) AND (Pregnancy) AND (Unresectable tumor) AND (acute) AND (hepatectomy) AND (intraoperative ablation) AND (nonspecific) AND (overt) AND (severe) AND (unknown cause) AND (＜18y or＞75y) AND (＞ 2×ULN) AND (＞126 copies/ml) AND (＞2.0 mmol/L) AND (＞30%) AND ((Child-Pugh Score) OR (acute myocardial infarction) OR (ascites) OR (circulatory shock) OR (coma) OR (gastrointestinal hemorrhage) OR (hemorrhagic disorders) OR (indocyanine green retention rate at 15min (ICGR15)) OR (infectious lesion) OR (renal failure) OR (serum alanine aminotransferase (ALT)) OR (serum hepatitis B virus (HBV)-DNA) OR (serum triglycerides) OR (stroke)) AND ((egg proteins) OR (fish proteins)))"}
{"candidate_id": "LLM00496", "doc_id": "NCT02904785_inc", "case_bucket": "or", "source_criterion": "Clinical and radiologic diagnosis of primary knee osteoarthritis (Kellgren & Lawrence I, II or III); Capability to understand the Informed Consent Form; Chronic pain for at least 3 months prior to inclusion, measured by VAS. (VAS 4 or above); Absence of skin injures, infections or tumor in the target knee; Availability to comply with the visits.", "candidate_expression": "((4 or above) AND (Absence) AND (Availability to comply with the visits) AND (Capability to understand the Informed Consent Form;) AND (Chronic pain) AND (Clinical diagnosis) AND (I, II or III) AND (Kellgren & Lawrence) AND (VAS) AND (at least 3 months prior) AND (inclusion) AND (measured by VAS) AND (primary knee osteoarthritis) AND (radiologic diagnosis) AND (target knee) AND ((infections) OR (skin injures) OR (tumor)))"}
{"candidate_id": "LLM00497", "doc_id": "NCT02550028_exc", "case_bucket": "or", "source_criterion": "Babies who have been close to death Seizure occurred by metabolic factors (hypoglycemia, hypocalcemia, electrolyte disorder) Babies who have received phenobarbitone or any other anticonvulsive medication before hospitalization Abnormal renal function", "candidate_expression": "((Abnormal) AND (Abnormal renal function) AND (Babies) AND (Seizure) AND (anticonvulsive medication) AND (any other) AND (before hospitalization) AND (close to death) AND (electrolyte disorder) AND (have been) AND (hospitalization) AND (hypocalcemia) AND (hypoglycemia) AND (metabolic factors) AND (phenobarbitone) AND (renal function))"}
{"candidate_id": "LLM00498", "doc_id": "NCT00943865_exc", "case_bucket": "or", "source_criterion": "diabetes ischemic heart disease or any abnormality on treadmill stress test inflammatory or chronic disorder pregnancy lactation creatinine level of 1,5 mg/dL or more gastrointestinal problems or musculoskeletal disorders that would prevent them to follow the test diets or exercise interventions liver dysfunction with a factor of at least 3 above the upper limit of normal in AST and ALT levels thyroid dysfunction, with serum TSH out of normal limits use of immunosuppressive drugs, corticosteroids or anorexigen", "candidate_expression": "((1,5 mg/dL or more) AND (ALT levels) AND (AST levels) AND (abnormality) AND (creatinine level) AND (diabetes) AND (factor of at least 3 above the upper limit of normal) AND (lactation) AND (liver dysfunction) AND (out of normal limits) AND (pregnancy) AND (prevent) AND (serum TSH) AND (thyroid dysfunction) AND ((gastrointestinal problems) OR (musculoskeletal disorders)) AND ((exercise interventions) OR (test diets)) AND ((ischemic heart disease) OR (treadmill stress test)) AND ((anorexigen) OR (corticosteroids) OR (immunosuppressive drugs)) AND ((chronic disorder) OR (disorder inflammatory)))"}
{"candidate_id": "LLM00499", "doc_id": "NCT03297944_exc", "case_bucket": "or", "source_criterion": "using daily medication for chronic condition acute narrow angle glaucoma previous adverse experience with study drugs experiences motion sickness in response to driving simulator BMI > 30 women who are pregnant, lactating, or planning on becoming pregnant regular use of tobacco products current substance use disorder clinically significant ECG current ongoing psychiatric disorder", "candidate_expression": "((> 30) AND (BMI) AND (ECG) AND (acute) AND (adverse experience) AND (chronic condition) AND (clinically significant) AND (current) AND (daily) AND (medication) AND (motion sickness) AND (narrow angle glaucoma) AND (ongoing) AND (planning on becoming) AND (previous) AND (psychiatric disorder) AND (regular) AND (study drugs) AND (substance use disorder) AND (use of tobacco products) AND (women) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM00500", "doc_id": "NCT00576173_exc", "case_bucket": "or", "source_criterion": "Patients who have taken either morphine with daily dose more than 120mg or Fentanyl with daily dose more than 50ug/hr Patients with significant abnormalities in hepatic or renal function which would, in the opinion of the investigator, prevent the patients involvement in the study Patients with significant clinical abnormalities in CNS, respiratory or cardiovascular function, which in the investigators judgement prevents participation in the study Patients who have taken antidepressants or anti-epileptic drugs, sedative hypnotics, selective serotonin reuptake inhibitor, short-acting analgesics, topical medications and anesthetics and/or muscle relaxants when taking Tramadol/Acetaminophen", "candidate_expression": "((Acetaminophen) AND (Fentanyl) AND (Tramadol) AND (abnormalities in CNS) AND (abnormalities in cardiovascular function) AND (abnormalities in hepatic function) AND (abnormalities in renal function) AND (abnormalities in respiratory function) AND (anesthetics) AND (anti-epileptic drugs) AND (antidepressants) AND (daily dose more than 120mg) AND (daily dose more than 50ug/hr) AND (morphine) AND (muscle relaxants) AND (sedative hypnotics) AND (selective serotonin reuptake inhibitor) AND (short-acting analgesics) AND (taking Tramadol/Acetaminophen) AND (topical medications) AND (when taking Tramadol/Acetaminophen))"}
```
