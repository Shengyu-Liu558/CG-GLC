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
{"candidate_id": "LLM07426", "doc_id": "NCT02427295_exc", "case_bucket": "or", "source_criterion": "Severe co-morbid illness such as untreatable other malignancy and/or active infections. Pregnant or lactating women Hypersensitivity to Sandostatin or any component of the formulation.", "candidate_expression": "((Hypersensitivity) AND (Pregnant) AND (Sandostatin) AND (co-morbid illness Severe) AND (component of the formulation) AND (infections active) AND (lactating) AND (malignancy untreatable other) AND (women))"}
{"candidate_id": "LLM07427", "doc_id": "NCT02920177_inc", "case_bucket": "scope", "source_criterion": "Patients with symptomatic FAI Clinical and radiographic evidence of FAI Patients able to provide consent to study participation Completion of 6 weeks of physical therapy program", "candidate_expression": "((6 weeks) AND (Clinical evidence) AND (FAI) AND (Patients able to provide consent to study participation) AND (physical therapy program) AND (radiographic evidence) AND (symptomatic))"}
{"candidate_id": "LLM07428", "doc_id": "NCT02968602_inc", "case_bucket": "or", "source_criterion": "DSM-IV or DSM-5 diagnosis of schizophrenia or schizoaffective disorder Male or Female Age: 18 to 65 years Caucasian or Non-Caucasian Smoke at least 10 cigarettes daily Urine cotinine level ? 100 ng/ml (NicAlert(r) reading ? 3) Agrees to wear a head mounted display (HMD) for up to 45 minutes Able to complete the Evaluation to Sign Consent (ESC) with minimum score of 80%", "candidate_expression": "((18 to 65 years) AND (? 100 ng/ml) AND (? 3) AND (Able to complete) AND (Age) AND (Agrees to wear) AND (Evaluation to Sign Consent (ESC)) AND (NicAlert(r)) AND (Smoke) AND (Urine cotinine level) AND (at least 10 cigarettes daily) AND (for up to 45 minutes) AND (head mounted display (HMD)) AND (minimum score of 80%) AND ((Caucasian) OR (Non-Caucasian)) AND ((DSM-5) OR (DSM-IV)) AND ((schizoaffective disorder) OR (schizophrenia)) AND ((Female) OR (Male)))"}
{"candidate_id": "LLM07429", "doc_id": "NCT02318446_inc", "case_bucket": "other", "source_criterion": "Diagnosed epileptic patients of either sex with age between 10-19 yrs (<19yrs), coming to the medicine Out Patient /In Patient Departments and undergoing AED therapy for more than 6 months. Epileptics with high homocysteine levels i.e. > 10.9 µmol/L (Normal homocysteine levels are 4.3-9.9 µmol/L for male and 3.3-7.2 µmol/L for female adolescent and a high homocysteine concentration is deaned as at least 11.4 µmol/L for male and at least 10.4 µmol/L for female. Gender mean of high homocysteine concentration is 10.9 µmol/L) [5]", "candidate_expression": "((AED therapy for more than 6 months) AND (In Patient Departments) AND (Out Patient Departments) AND (age between 10-19 yrs <19yrs) AND (epileptic) AND (homocysteine levels high > 10.9 µmol/L))"}
{"candidate_id": "LLM07430", "doc_id": "NCT00235170_exc", "case_bucket": "or", "source_criterion": "1. Congestive heart failure; 2. CABG or Percutaneous Coronary Intervention (PCI) procedure; 3. Planned need for major surgery (e.g. valve surgery or resection of aortic or left ventricular aneurysm, carotid end-arterectomy, abdominal aortic aneurysm surgery etc.); 4. Congenital heart disease; 5. Transmural myocardial infarction within the previous seven days and CK has not returned to normal; 6. Chest pain lasting longer than 30 minutes within 12 hours pre-procedure, if CK enzymes positive (≥ 2x the normal upper limit). 7. History of any cerebrovascular accident; 8. Left main stenosis of 50% or more; 9. Intention to treat more than 1 totally occluded major epicardial vessel; 10. Single vessel (single territory) disease.", "candidate_expression": "((CABG) AND (CK enzymes positive ≥ 2x the normal upper limit) AND (CK normal) AND (Chest pain lasting longer than 30 minutes within 12 hours pre-procedure) AND (Congenital heart disease) AND (Congestive heart failure) AND (History of) AND (Left main stenosis 50% or more) AND (Percutaneous Coronary Intervention (PCI)) AND (Single vessel disease) AND (Transmural myocardial infarction within the previous seven days) AND (abdominal aortic aneurysm surgery) AND (any cerebrovascular accident) AND (carotid end-arterectomy) AND (major surgery) AND (resection of aortic aneurysm) AND (resection of left ventricular aneurysm) AND (single territory disease) AND (treat Intention to totally occluded major epicardial vessel) AND (valve surgery))"}
{"candidate_id": "LLM07431", "doc_id": "NCT02649114_exc", "case_bucket": "other", "source_criterion": "current suicidal risk current psychosis ongoing trauma (e.g. current involvement in an abusive relationship).", "candidate_expression": "((involvement in an abusive relationship current) AND (psychosis current) AND (suicidal risk current) AND (trauma ongoing))"}
{"candidate_id": "LLM07432", "doc_id": "NCT02371200_inc", "case_bucket": "or", "source_criterion": "1. Subject has a history of GTC seizures, either primary GTC or partial onset seizures with secondary generalization. 2. Is being admitted to a hospital for routine vEEG monitoring related to seizures. 3. Male or female between the ages of 2-99. 4. Has an upper arm circumference which is adequate for proper fit of the EMG monitor (at least 14cm). 5. If female and of childbearing potential, has a negative pregnancy test. 6. Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments. 7. Subject and/or Primary Caregiver must be competent to follow all study procedures. 8. Is able to read, speak, and understand English.", "candidate_expression": "((Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments.) AND (GTC seizures history) AND (Subject and/or Primary Caregiver must be competent to follow all study procedures.) AND (admitted to a hospital) AND (childbearing potential) AND (female at least 14cm) AND (pregnancy test negative) AND (secondary generalization) AND (seizures) AND (the ages between 2-99) AND (upper arm circumference adequate for proper fit of the EMG monitor) AND (vEEG monitoring) AND ((partial onset seizures) OR (primary GTC)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07433", "doc_id": "NCT02101554_inc", "case_bucket": "or", "source_criterion": "Children 7-17 with moderate to severe pain requiring around the clock treatment with an opioid analgesic. Be an experienced opioid user, defined as any subject treated with opioid therapy, equivalent or equal to >20 mg per day of morphine, for a period of 3 consecutive days immediately prior to first day of dosing.", "candidate_expression": "((3 consecutive days immediately prior to first day of dosing) AND (>20 mg per day) AND (Children) AND (around the clock treatment) AND (equivalent) AND (first day of dosing) AND (moderate) AND (morphine) AND (opioid analgesic) AND (opioid therapy) AND (pain) AND (severe))"}
{"candidate_id": "LLM07434", "doc_id": "NCT01236417_inc", "case_bucket": "or", "source_criterion": "Post menopausal women with a history of estrogen positive breast cancer who are receiving aromatase inhibitors for at least one month. Patients must complain of mild to moderate arthralgia. Ability to understand and sign informed consent. Patients meet criteria for low to moderate risk for moderate exercise based oon the ACSM guidelines.", "candidate_expression": "((ACSM guidelines) AND (Ability to understand and sign informed consent.) AND (Post menopausal) AND (aromatase inhibitors) AND (arthralgia) AND (breast cancer) AND (estrogen positive) AND (for at least one month) AND (history) AND (low) AND (mild) AND (moderate) AND (risk for moderate exercise) AND (women))"}
{"candidate_id": "LLM07435", "doc_id": "NCT03513757_exc", "case_bucket": "or", "source_criterion": "Inpatient status, airway abnormalities, allergy to any study medications, eggs and soy, and mitochondrial disorders. All subjects with any cardiac disease or history of cardiac arrhythmias will be excluded.", "candidate_expression": "((Inpatient status) AND (airway abnormalities) AND (allergy) AND (cardiac arrhythmias history) AND (cardiac disease) AND (eggs) AND (mitochondrial disorders) AND (soy) AND (study medications))"}
{"candidate_id": "LLM07436", "doc_id": "NCT02457442_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07437", "doc_id": "NCT03388840_inc", "case_bucket": "other", "source_criterion": "male patients with androgenetic alopecia between 18 years and 60 years", "candidate_expression": "((androgenetic alopecia) AND (between 18 years and 60 years) AND (male) AND (years))"}
{"candidate_id": "LLM07438", "doc_id": "NCT02715466_inc", "case_bucket": "or", "source_criterion": "Male or female patients = 18 and = 85 years of age Women of child bearing potential must test negative on standard pregnancy test (urine or serum) Patients with body weight = 55 kg and = 140 kg and body mass index (BMI) = 18 kg/m2 Patients diagnosed severe sepsis / septic shock at admission on Intensive Care Unit who can be enrolled within 90 min after admission OR patients diagnosed severe sepsis / septic shock during Intensive Care Unit stay who can be enrolled within 90 min after diagnosis Patients where antibiotic therapy has already been started (prior to randomization) Patient who are fluid responsive. Fluid responsiveness is defined as increase of > 10% in mean arterial pressure (MAP) after passive leg raising (PLR) Signed informed consent by patient, legal representative or authorized person or deferred consent", "candidate_expression": "((= 18 and = 85 years) AND (= 18 kg/m2) AND (= 55 kg and = 140 kg) AND (> 10%) AND (Male) AND (Signed informed consent by patient, legal representative or authorized person or deferred consent) AND (Women) AND (admission on Intensive Care Unit) AND (after passive leg raising (PLR)) AND (age) AND (antibiotic therapy) AND (at admission on Intensive Care Unit) AND (body mass index (BMI)) AND (body weight) AND (child bearing potential) AND (female) AND (fluid responsive) AND (mean arterial pressure (MAP)) AND (negative) AND (prior to randomization) AND (randomization) AND (septic shock) AND (serum) AND (severe sepsis) AND (standard pregnancy test) AND (urine))"}
{"candidate_id": "LLM07439", "doc_id": "NCT01768195_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with B-cell lymphoma HBsAg positive at baseline treated with rituximab-based immunochemotherapy life expectancy of more than 3 months", "candidate_expression": "((B-cell lymphoma) AND (HBsAg positive) AND (at baseline) AND (immunochemotherapy) AND (life expectancy) AND (more than 3 months) AND (naive) AND (rituximab) AND (rituximab-based) AND (treatment))"}
{"candidate_id": "LLM07440", "doc_id": "NCT02944604_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07441", "doc_id": "NCT02593409_exc", "case_bucket": "or", "source_criterion": "HIV infection at screening participation in previous or concurrent HIV vaccine trials lactating, pregnant or planning pregnancy renal function impairment (serum creatinine >1.5 mg/dl), Fanconi syndrome abnormal liver function tests (AST/ALT > 43 U/L), liver disease, viral hepatitis, hepatitis B virus (HBV) infection serum phosphorus <2.2mg/dl, osteoporosis known sensitivity to components of the Truvada® formulation any immunosuppressive treatment, such as systemic corticosteroids assumption of medication that interacts with Truvada® high likelihood of poor adherence to PREP and clinic attendance any condition that in the opinion of the attending physician could endanger the health of the participant or render her unsuitable to participate in the trial", "candidate_expression": "((<2.2mg/dl) AND (> 43 U/L) AND (>1.5 mg/dl) AND (Fanconi syndrome) AND (HIV infection) AND (Truvada) AND (abnormal) AND (actating, pregnant or planning pregnancy) AND (high likelihood of poor adherence to PREP and clinic attendanc) AND (immunosuppressive treatment) AND (osteoporosis) AND (participation in previous or concurrent HIV vaccine trials) AND (renal function impairment) AND (sensitivity) AND (serum creatinine) AND (serum phosphorus) AND (systemic corticosteroids) AND ((ALT) OR (AST)) AND ((hepatitis B virus (HBV) infection) OR (liver disease) OR (liver function tests) OR (viral hepatitis)))"}
{"candidate_id": "LLM07442", "doc_id": "NCT03464552_inc", "case_bucket": "other", "source_criterion": "Females 18-65 years old who undergoing colposcopic directed biopsy", "candidate_expression": "((Females) AND (colposcopic directed biopsy undergoing) AND (old 18-65 years))"}
{"candidate_id": "LLM07443", "doc_id": "NCT02959801_inc", "case_bucket": "other", "source_criterion": "proven acute deep venous thrombosis, less than 21 days and who were referred to the interventional radiology department.", "candidate_expression": "((acute) AND (deep venous thrombosis) AND (interventional radiology department) AND (less than 21 days) AND (proven) AND (referred to))"}
{"candidate_id": "LLM07444", "doc_id": "NCT01631058_inc", "case_bucket": "or", "source_criterion": "All renal (only) male and female recipients aged = 60, years undergoing kidney transplantation from a living or deceased donor, including Expanded Criteria Donors (ECD). Panel Reactive Antibody (PRA) < 30%. Patients who consented to participate in the study by signing the informed consent form before the transplant surgery to the 1st post-operative day).", "candidate_expression": "((Panel Reactive Antibody (PRA) < 30%) AND (Patients who consented to participate in the study by signing the informed consent form before the transplant surgery to the 1st post-operative day)) AND (aged = 60) AND (female) AND (kidney transplantation living donor deceased donor Expanded Criteria Donors (ECD)) AND (male) AND (recipients renal))"}
{"candidate_id": "LLM07445", "doc_id": "NCT00236340_exc", "case_bucket": "other", "source_criterion": "Multiple pregnancy (more than 3 fetuses) Maternal history of placental abruptio Fetus with IUGR Pregnancy complicated with pre-eclampsia Unability to give informed consent", "candidate_expression": "((Fetus) AND (IUGR) AND (Maternal history of) AND (Multiple pregnancy) AND (Pregnancy) AND (Unability to) AND (fetuses) AND (give informed consent) AND (more than 3) AND (placental abruptio) AND (pre-eclampsia))"}
{"candidate_id": "LLM07446", "doc_id": "NCT02035904_inc", "case_bucket": "or", "source_criterion": "F; age 18 to 70 American Society of Anesthesiologists (ASA) I e II; breast cancer ( DIN 2 e 3, o LIN 2 e 3 sec. Tavassoli) scheduled for nipple-sparing mastectomy, simple mastectomy, skin-sparing mastectomy, skin-reducing mastectomy c, lymphnode biopsy and axillary dissection; immediate sub-pectoral prosthetic reconstruction; signed informed consent.", "candidate_expression": "((American Society of Anesthesiologists (ASA) I e II) AND (F) AND (age 18 to 70) AND (sub-pectoral prosthetic reconstruction immediate) AND ((axillary dissection) OR (breast cancer) OR (lymphnode biopsy) OR (nipple-sparing mastectomy scheduled for) OR (simple mastectomy) OR (skin-reducing mastectomy) OR (skin-sparing mastectomy)) AND ((DIN 2 e 3) OR (LIN 2 e 3 sec)))"}
{"candidate_id": "LLM07447", "doc_id": "NCT02686021_exc", "case_bucket": "or", "source_criterion": "simultaneous both sided extraction or only upper third molar extraction general anesthesia known or presumed abnormal coagulation status known or presumed liver or renal dysfunction contraindication against metamizole known or suspected (known or suspected allergy against novalgin or other pyrazolones, anaphylactic reaction against NSAIDS, decreased bone marrow function or hematopoesis, hepatic porphyria, glucose-6-phosphate dehydrogenase deficiency, and pregnancy/breastfeeding) contraindication against ibuprofen (known or suspected allergy against ibuprofen, anaphylactic reaction against Nonsteroidal anti-inflammatory drugs (NSAID), active or recurrent stomach or duodenal ulcera or bleeding, severe liver or renal insufficiency, inflammatory bowel syndrome, and pregnancy/breastfeeding) pregnancy and breast feeding mothers", "candidate_expression": "((NSAIDS) AND (Nonsteroidal anti-inflammatory drugs (NSAID)) AND (abnormal coagulation status) AND (contraindication) AND (decreased) AND (general anesthesia) AND (ibuprofen) AND (metamizole) AND (molar extraction) AND (other) AND (simultaneous) AND ((liver dysfunction) OR (renal dysfunction)) AND ((known) OR (suspected)) AND ((both sided) OR (only upper third)) AND ((allergy) OR (anaphylactic reaction)) AND ((novalgin) OR (pyrazolones)) AND ((bone marrow function) OR (hematopoesis)) AND ((breastfeeding) OR (glucose-6-phosphate dehydrogenase deficiency) OR (hepatic porphyria) OR (pregnancy)) AND ((allergy) OR (anaphylactic reaction) OR (breastfeeding) OR (inflammatory bowel syndrome) OR (pregnancy) OR (severe liver insufficiency) OR (severe renal insufficiency)) AND ((active) OR (recurrent)) AND ((bleeding) OR (ulcera)) AND ((duodenal) OR (stomach)) AND ((breast feeding) OR (pregnancy)) AND ((known) OR (presumed)))"}
{"candidate_id": "LLM07448", "doc_id": "NCT01088750_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07449", "doc_id": "NCT02301039_exc", "case_bucket": "or", "source_criterion": "Prior systemic therapy targeting PD-1: PD-L1 axis. Patients who are curable by conventional multidisciplinary management. Patients with severe and/or uncontrolled concurrent medical disease that in the opinion of the investigator could cause unacceptable safety risks or compromise compliance with the protocol. Patients who have received wide field radiotherapy ≤ 4 weeks or limited field radiation for palliation < 2 weeks prior to screening or who have not recovered adequately from side effects of such therapy. Patients who have active infections requiring therapy. Patients that are known to be positive for Human Immunodeficiency Virus (HIV) (HIV 1/2 antibodies), active Hepatitis B (HBsAg reactive), or Hepatitis C (HCV RNA [qualitative] is detected); patients with negative Hepatitis C antibody testing may not need RNA testing. Patients that have a known psychiatric or substance abuse disorder that would interfere with cooperation with the requirements of the trial. Patients who received systemic anti-cancer treatment prior to the first dose of study drug within the following time frames: Patients with active autoimmune disease or a documented history of autoimmune disease or syndrome that requires systemic steroids or immunosuppressive agents. Patients with vitiligo or resolved childhood asthma/atopy would be exception to this rule. Patients that require inhaled steroids or local steroid injections would not be excluded from the study. Patients with hypothyroidism not from autoimmune disease that is stable on hormone replacement will not be excluded from the study. Women who are pregnant or nursing/breastfeeding. Known hypersensitivity to pembrolizumab or another mAb. Has a history of (non-infectious) pneumonitis that required steroids or current pneumonitis. Patients with untreated central nervous system disease. Patients with controlled treated CNS lesions who have undergone surgery or stereotactic radiosurgery and stable for 4 weeks are eligible. Inability to comply with protocol required procedures. Patients with medical conditions that require chronic systemic corticosteroid therapy or require any other form of immunosuppressive medication. However, patients using physiologic replacement doses of hydrocortisone, or its equivalent, will be considered eligible for this study: up to 20 mg hydrocortisone (or 5 mg of prednisone) in the morning and 10 mg hydrocortisone (or 2.5 mg prednisone) in the evening. Patients with the risk factors for bowel obstruction or bowel perforation (examples include but not limited to a history of acute diverticulitis, intra-abdominal abscess, abdominal carcinomatosis). Patients who have received a live vaccine within 30 days prior to the first dose of trial treatment.", "candidate_expression": "((10 mg) AND (2.5 mg) AND (5 mg) AND (< 2 weeks prior to screening) AND (CNS lesions) AND (HBsAg) AND (HCV RNA [qualitative]) AND (HIV 1/2 antibodies) AND (Hepatitis C) AND (Hepatitis C antibody) AND (Human Immunodeficiency Virus (HIV)) AND (Inability to comply with protocol required procedures.) AND (Patients that have a known psychiatric or substance abuse disorder that would interfere with cooperation with the requirements of the trial.) AND (Women) AND (abdominal carcinomatosis) AND (active) AND (active Hepatitis B) AND (acute diverticulitis) AND (adequately) AND (atopy) AND (autoimmune disease) AND (bowel obstruction) AND (bowel perforation) AND (breastfeeding) AND (central nervous system disease) AND (childhood asthma) AND (chronic) AND (concurrent) AND (controlled) AND (conventional multidisciplinary management) AND (curable) AND (current) AND (detected) AND (for 4 weeks) AND (history) AND (hormone replacement) AND (hydrocortisone) AND (hypersensitivity to mAb) AND (hypersensitivity to pembrolizumab) AND (hypothyroidism) AND (immunosuppressive agents) AND (immunosuppressive medication) AND (in the evening) AND (in the morning) AND (in the opinion of the investigator) AND (infections) AND (intra-abdominal abscess) AND (limited field radiation for palliation) AND (live vaccine) AND (mAb) AND (medical conditions) AND (medical disease) AND (negative) AND (not) AND (nursing) AND (pembrolizumab) AND (physiologic replacement doses) AND (pneumonitis) AND (positive) AND (prednisone) AND (pregnant) AND (prior to the first dose of study drug) AND (psychiatric disorder) AND (reactive) AND (recovered) AND (require chronic systemic corticosteroid therapy) AND (require immunosuppressive medication) AND (required steroids) AND (requiring therapy) AND (resolved) AND (risk factors for bowel obstruction) AND (risk factors for bowel perforation) AND (screening) AND (severe) AND (side effects of such therapy) AND (stable) AND (stable on hormone replacement) AND (stereotactic radiosurgery) AND (steroids) AND (substance abuse disorder) AND (such therapy) AND (surgery) AND (syndrome that requires immunosuppressive agents) AND (syndrome that requires systemic steroids) AND (systemic anti-cancer treatment) AND (systemic corticosteroid therapy) AND (systemic steroids) AND (systemic therapy targeting PD-1: PD-L1 axis) AND (the first dose of study drug) AND (the first dose of trial treatment) AND (therapy) AND (treated) AND (uncontrolled) AND (untreated) AND (up to 20 mg) AND (vitiligo) AND (wide field radiotherapy) AND (within 30 days prior to the first dose of trial treatment) AND (≤ 4 weeks))"}
{"candidate_id": "LLM07450", "doc_id": "NCT02592980_inc", "case_bucket": "other", "source_criterion": "Only patients with atrial fibrillation, above 18 years, and with TTR <50% based on the last three values of INR will be included in this study.", "candidate_expression": "((TTR <50% based on the last three values of INR) AND (atrial fibrillation) AND (years above 18 years))"}
```
