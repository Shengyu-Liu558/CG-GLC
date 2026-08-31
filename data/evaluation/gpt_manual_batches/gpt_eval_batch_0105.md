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
{"candidate_id": "LLM02601", "doc_id": "NCT01669369_inc", "case_bucket": "or", "source_criterion": "histologically diagnosed primary classical osteosarcoma in extremities staging IIB MRI showing no skip lesion receive standard neo-adjuvant chemotherapy, adjuvant chemotherapy,and standard surgical treatment", "candidate_expression": "((MRI) AND (adjuvant chemotherapy) AND (classical osteosarcoma) AND (histologically) AND (in extremities) AND (no) AND (primary) AND (skip lesion) AND (staging IIB) AND (standard neo-adjuvant chemotherapy) AND (standard surgical treatment))"}
{"candidate_id": "LLM02602", "doc_id": "NCT03181984_inc", "case_bucket": "other", "source_criterion": "Age range: 14 to 65 years-old; Clinically diagnosed of Port-wine Stain; Patients receiving hemoporfin based upon the clinical judgment of the investigator; Written informed consent signed and agreed to receive periodic follow-up", "candidate_expression": "((Age 14 to 65 years-old) AND (Port-wine Stain) AND (Written informed consent signed and agreed to receive periodic follow-up) AND (hemoporfin))"}
{"candidate_id": "LLM02603", "doc_id": "NCT01491763_inc", "case_bucket": "or", "source_criterion": "Patients with Ph (BCR/ABL) positive de novo < 55 years old (it is advisable to include patients over 55 years LAL07OPH protocol). Performance status 0-2 (Appendix B) may include patients with performance status > 2 attributable to LAL. Patients without functional impairment of organs: liver function: total bilirubin, AST, ALT, alfa-GT and alkaline phosphatase less than 3 times the upper limit of normal laboratory renal function: serum creatinine < 2 mg/dL or clearance creatinine > 30 ml/min (except renal function attributable to LAL) cardiac function (Appendix B) normal: ventricular EF > 50%, absence of severe chronic respiratory disease. In the event that alterations are secondary to the disease is at the discretion of the investigator to determine if the patient can be included in the trial.", "candidate_expression": "((ALT) AND (AST) AND (Performance status 0-2) AND (Ph (BCR/ABL) positive de novo) AND (alfa-GT) AND (alkaline phosphatase) AND (cardiac function normal) AND (clearance creatinine > 30 ml/min) AND (old < 55 years) AND (serum creatinine < 2 mg/dL) AND (total bilirubin) AND (ventricular EF > 50%) AND NOT (functional impairment of organs) AND NOT (severe chronic respiratory disease))"}
{"candidate_id": "LLM02604", "doc_id": "NCT02957305_exc", "case_bucket": "or", "source_criterion": "patients who do not wish to participate in the project; patients with ectopic pregnancy; patients with comorbidities (heart failure congestive, chronic obstructive pulmonary disease); patients with hypovolemic shock; patients with cervical incompetence; patients with infected miscarriage/abortion (presence of fever, pus from the cervix, leukocytosis [> 14000]); patients with twin pregnancy; patients with Marfan syndrome; patients allergic to misoprostol; patients with coagulopathy; patients with opening of cervical internal os (4 mm of dilatation at the time of consultation); patients with previous surgery of the cervix (conization); patients with concomitant use of IUDs.", "candidate_expression": "((4 mm of dilatation) AND (> 14000) AND (IUDs) AND (Marfan syndrome) AND (abortion) AND (allergic) AND (cervical incompetence) AND (cervix) AND (chronic obstructive pulmonary disease) AND (coagulopathy) AND (comorbidities) AND (conization) AND (ectopic pregnancy) AND (fever) AND (heart failure congestive) AND (hypovolemic shock) AND (infected) AND (leukocytosis) AND (miscarriage) AND (misoprostol) AND (opening of cervical internal os) AND (patients who do not wish to participate in the project) AND (pregnancy) AND (pus from the cervix) AND (surgery) AND (twin))"}
{"candidate_id": "LLM02605", "doc_id": "NCT02015494_exc", "case_bucket": "or", "source_criterion": "Use of any investigational or non-registered drug or vaccine product within 30 days preceding the administration of the study vaccine or planned use within the first six weeks of the study period Has received any licensed or other investigational influenza vaccine within 3 months prior to enrollment in this study or expected receipt of any influenza vaccination before the Day 21 blood collection History of excessive alcohol use, drug abuse or significant psychiatric illness Tobacco use within 3 months of enrollment and throughout first 6 months of the study Has a chronic illness (e.g., liver or kidney disease), receiving a concomitant therapy or have any other condition that could interfere with the subject's participation in the study or in the interpretation of the study results Clinically significant abnormal liver function tests at screening Positive serology for HBsAg, HCV or HIV antibodies Pregnant or lactating female Having cancer or have received treatment for cancer within three years (persons with a history of cancer who are disease-free without treatment for three years or more are eligible), excluding minor skin cancers, which are allowed unless located at the vaccination site Persons with impaired immune responsiveness (of any cause), including diabetes mellitus and autoimmune disorders Persons presently receiving or having a recent history of receiving (within the past six months) any medication or therapeutic modality that affects the immune system such as allergy shots, immune globulin, interferon, immunomodulators, radiation therapy, cytotoxic drugs or drugs known to be frequently associated with significant major organ toxicity, or systemic corticosteroids (oral or injectable). Inhaled and topical corticosteroids are allowed. Persons with a history of severe allergic reaction after previous vaccinations or hypersensitivity to any seasonal influenza vaccine component Persons with a history of Guillain-Barré Syndrome Receipt of blood or blood products 8 weeks prior to vaccination or planned administration during the three week study period following vaccination Donation of blood or blood products within 8 weeks prior to vaccination or during the three week study period following An oral temperature >100.4° or acute disease within 72 hours prior to vaccination, defined as the presence of a moderate or severe illness (as determined by the investigator through medical history and physical examination; for example, those requiring an absence from work) with or without fever. Body Mass Index >29.9 Any disorder of coagulation A clinical diagnosis of influenza within the previous 12 months Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study", "candidate_expression": "((>100.4°) AND (>29.9) AND (Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study) AND (Body Mass Index) AND (Clinically significant) AND (Day 21) AND (Guillain-Barré Syndrome) AND (History) AND (Positive) AND (Tobacco use) AND (abnormal) AND (affects the immune system) AND (after previous vaccinations) AND (any other condition) AND (at screening) AND (before the Day 21) AND (cancer) AND (chronic illness) AND (concomitant) AND (could interfere with the subject's participation in the study) AND (disease-free) AND (disorder of coagulation) AND (during the three week study period following vaccination) AND (enrollment) AND (enrollment in this study) AND (expected receipt) AND (female) AND (for three years or more) AND (history) AND (impaired immune responsiveness) AND (influenza) AND (known to be frequently associated with significant major organ toxicity) AND (liver function tests) AND (planned use) AND (previous vaccinations) AND (screening) AND (seasonal influenza vaccine component) AND (severe) AND (significant) AND (the administration of the study vaccine) AND (the study) AND (the study period) AND (the three week study period) AND (therapy) AND (three week study period following vaccination) AND (throughout first 6 months of the study) AND (treatment) AND (vaccination) AND (within 3 months of enrollment) AND (within 3 months prior to enrollment in this study) AND (within 72 hours prior to vaccination) AND (within the past six months) AND (within the previous 12 months) AND (within three years) AND (without) AND ((drug) OR (vaccine product)) AND ((Receipt of blood) OR (Receipt of blood products)) AND ((8 weeks prior to vaccination) OR (planned administration)) AND ((Donation of blood) OR (Donation of blood products)) AND ((during the three week study period) OR (within 8 weeks prior to vaccination)) AND ((acute disease) OR (oral temperature)) AND ((moderate illness) OR (severe illness)) AND ((licensed) OR (other investigational)) AND ((any influenza vaccination) OR (influenza vaccine)) AND ((drug abuse) OR (excessive alcohol use) OR (psychiatric illness)) AND ((investigational) OR (non-registered)) AND ((kidney disease) OR (liver disease)) AND ((HBsAg antibodies) OR (HCV antibodies) OR (HIV antibodies)) AND ((Pregnant) OR (lactating)) AND ((within 30 days preceding the administration of the study vaccine) OR (within the first six weeks of the study period)) AND ((cancer) OR (treatment for cancer)) AND ((autoimmune disorders) OR (diabetes mellitus)) AND ((any medication) OR (therapeutic modality)) AND ((allergy shots) OR (cytotoxic drugs) OR (drugs known to be frequently associated with significant major organ toxicity) OR (immune globulin) OR (immunomodulators) OR (interferon) OR (radiation therapy) OR (systemic corticosteroids)) AND ((injectable) OR (oral)) AND ((allergic reaction) OR (hypersensitivity to any seasonal influenza vaccine component)))"}
{"candidate_id": "LLM02606", "doc_id": "NCT03123562_exc", "case_bucket": "or", "source_criterion": "Epilepsy Hydrocephalus with ventricular drain Coagulation disorders Allergy to anesthetic agents Severe health conditions such as cancer, failure of heart, lung, liver or kidney Active infections", "candidate_expression": "((Active) AND (Allergy) AND (Coagulation disorders) AND (Epilepsy) AND (Hydrocephalus) AND (Severe health conditions) AND (anesthetic agents) AND (infections) AND (ventricular drain) AND ((cancer) OR (failure of heart) OR (failure of kidney) OR (failure of liver) OR (failure of lung)))"}
{"candidate_id": "LLM02607", "doc_id": "NCT03034096_inc", "case_bucket": "or", "source_criterion": "Lobectomy or pneumonectomy Esophagectomy Radical (total) cystectomy Pancreatectomy Partial hepatectomy Hyperthermic intraperitoneal chemotherapy (HIPEC) Gastrectomy (subtotal or total) Cholecystectomy or bile duct resection", "candidate_expression": "((Esophagectomy) AND (Gastrectomy) AND (HIPEC) AND (Hyperthermic intraperitoneal chemotherapy) AND (Pancreatectomy) AND (Partial hepatectomy) AND (Radical cystectomy) AND (total cystectomy) AND ((Lobectomy) OR (pneumonectomy)) AND ((subtotal) OR (total)) AND ((Cholecystectomy) OR (bile duct resection)))"}
{"candidate_id": "LLM02608", "doc_id": "NCT02467686_inc", "case_bucket": "or", "source_criterion": "Menopausal women with breast cancer treated and using tamoxifen or aromatase inhibitor. With hot flashes and with or without active sexual life.", "candidate_expression": "((Menopausal) AND (aromatase inhibitor) AND (breast cancer) AND (hot flashes) AND (tamoxifen) AND (treated) AND (with active sexual life) AND (without active sexual life) AND (women))"}
{"candidate_id": "LLM02609", "doc_id": "NCT02862314_exc", "case_bucket": "or", "source_criterion": "pregnancy, patients under legal custody, patients without health insurance, patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter, moribund patients, situation in which the procalcitonin concentration could be increased without correlation to an infectious process (poly-traumatised patients, surgical interventions within the last 4 days, cardiorespiratory arrest, administration of anti-thymocyte globulin, immunodepressed patients (bone marrow transplant patients, patients with severe neutropenia), patients with an absolute indication for administration of antibiotics at the moment of ICU admission (meningitis, pneumonia) or a chronic infection for which long-term antibiotic treatment is necessary (endocarditis, osteo-articular infections, mediastinitis, deep abscesses, pneumocystis infection, toxoplasmosis, tuberculosis) patients with haemodynamic instability of septic origin or a respiratory insufficiency (defined by a ratio Pa02/Fi02 = 200 mmHg and PEP = 5 cmH2O)", "candidate_expression": "((= 200 mmHg) AND (= 5 cmH2O) AND (ICU) AND (PEP) AND (Pa02/Fi02) AND (anti-thymocyte globulin) AND (antibiotic treatment) AND (antibiotics) AND (bone marrow transplant) AND (cardiorespiratory arrest) AND (chronic infection) AND (deep abscesses) AND (endocarditis) AND (espiratory insufficiency) AND (haemodynamic instability) AND (health insurance) AND (immunodepressed) AND (increased) AND (indication) AND (last 4 days) AND (legal custody) AND (long-term) AND (mediastinitis) AND (meningitis) AND (moribund) AND (osteo-articular infections) AND (patients included in another interventional clinical study involving infections or antibiotics and having the same primary parameter) AND (pneumocystis infection) AND (pneumonia) AND (poly-traumatised) AND (pregnancy) AND (procalcitonin concentration) AND (septic) AND (severe neutropenia) AND (surgical interventions) AND (toxoplasmosis) AND (tuberculosis) AND (without))"}
{"candidate_id": "LLM02610", "doc_id": "NCT00455663_exc", "case_bucket": "or", "source_criterion": "History of significant head trauma, seizure disorder, or mental retardation History of alcohol or drug abuse or dependence within 1 month prior to study entry History of violence within 6 months prior to study entry", "candidate_expression": "((History) AND (History violence) AND (abuse alcohol) AND (dependence alcohol) AND (dependence drug) AND (drug abuse) AND (head trauma) AND (mental retardation) AND (seizure disorder))"}
{"candidate_id": "LLM02611", "doc_id": "NCT01630954_exc", "case_bucket": "or", "source_criterion": "Partial mole History of treatment for molar pregnancy like prior evacuation or chemotherapy Women requiring hysterectomy for treatment of H Mole", "candidate_expression": "((H Mole) AND (Partial mole) AND (Women) AND (chemotherapy) AND (evacuation) AND (hysterectomy) AND (molar pregnancy) AND (treatment))"}
{"candidate_id": "LLM02612", "doc_id": "NCT02260700_exc", "case_bucket": "or", "source_criterion": "Participant has a clinically significant abnormal physical examination, vital signs or 12 lead ECG (including QTc greater than (>) 450msec, Left Bundle Branch Block, permanent pacemaker or implantable cardioverter defibrillator) at Screening or admission Participant has a history of or current liver or renal insufficiency; significant cardiac, vascular, pulmonary, gastrointestinal, endocrine, neurologic, hematologic, rheumatologic, psychiatric, or metabolic disturbances Use of any prescription or over-the-counter medication, herbal medication, vitamins, or mineral supplements within 14 days prior to study drug administration (not including paracetamol). Medication for chronic use in age related disease will be allowed after approval by both the investigator and to the sponsor. No change in dose or regimen will be permitted during the study that is, from the Screening visit until the follow-up visit Participant has a history of spontaneous, prolonged or severe bleeding of unclear origin Participant has a history of epilepsy or fits or unexplained black-outs other than vasovagal collapse", "candidate_expression": "((Medication) AND (age related disease) AND (approval by both the investigator and to the sponsor) AND (at Screening or admission) AND (bleeding) AND (chronic use) AND (clinically significant) AND (greater than (>) 450msec) AND (history) AND (not) AND (other than) AND (paracetamol) AND (significant) AND (study drug administration) AND (unclear origin) AND (unexplained) AND (vasovagal collapse) AND (within 14 days prior to study drug administration) AND ((Screening) OR (admission)) AND ((liver insufficiency) OR (renal insufficiency)) AND ((cardiac disturbances) OR (endocrine disturbances) OR (gastrointestinal disturbances) OR (hematologic disturbances) OR (metabolic disturbances) OR (neurologic disturbances) OR (psychiatric disturbances) OR (pulmonary disturbances) OR (rheumatologic disturbances) OR (vascular disturbances)) AND ((any prescription) OR (herbal medication) OR (mineral supplements) OR (over-the-counter medication) OR (vitamins)) AND ((prolonged) OR (severe) OR (spontaneous)) AND ((abnormal 12 lead ECG) OR (abnormal physical examination) OR (abnormal vital signs)) AND ((black-outs) OR (epilepsy) OR (fits)) AND ((Left Bundle Branch Block) OR (QTc) OR (implantable cardioverter defibrillator) OR (permanent pacemaker)))"}
{"candidate_id": "LLM02613", "doc_id": "NCT03288428_exc", "case_bucket": "other", "source_criterion": "can't understand patient controlled analgesia device refuse trial", "candidate_expression": "(can't understand patient controlled analgesia device refuse trial)"}
{"candidate_id": "LLM02614", "doc_id": "NCT03639545_exc", "case_bucket": "or", "source_criterion": "diagnosed advanced heart, kidney or liver failure benign prostatic hyperplasia prostatic carcinoma frequent urinary tract infections non-type 1 diabetes mellitus", "candidate_expression": "((benign prostatic hyperplasia) AND (non-type 1 diabetes mellitus) AND (prostatic carcinoma) AND (urinary tract infections frequent) AND ((advanced heart failure) OR (kidney failure) OR (liver failure)))"}
{"candidate_id": "LLM02615", "doc_id": "NCT02566863_exc", "case_bucket": "or", "source_criterion": "patient's refusal contraindications to dexmedetomidine diseases/drugs that influence on autonomic nervous system activity", "candidate_expression": "((contraindications) AND (dexmedetomidine) AND (diseases influence on autonomic nervous system activity) AND (drugs influence on autonomic nervous system activity) AND (patient's refusal))"}
{"candidate_id": "LLM02616", "doc_id": "NCT02303171_exc", "case_bucket": "other", "source_criterion": "Women with systemic lupus erythematosus (SLE) Women with active thromboembolic disorders Women with history of previous thromboembolic disorders", "candidate_expression": "((Women) AND (systemic lupus erythematosus (SLE)) AND (thromboembolic disorders active) AND (thromboembolic disorders history previous))"}
{"candidate_id": "LLM02617", "doc_id": "NCT00970866_exc", "case_bucket": "or", "source_criterion": "Known asthmatic or history of allergy towards peanut or milk products Concurrent participation in another clinical trial Severe illness warranting hospital referral", "candidate_expression": "((Severe) AND (allergy) AND (asthmatic) AND (history) AND (hospital referral) AND (illness) AND (milk products) AND (participation in another clinical trial) AND (peanut) AND (warranting))"}
{"candidate_id": "LLM02618", "doc_id": "NCT02912182_exc", "case_bucket": "or", "source_criterion": "tinnitus or hearing loss with same debut as vertigo history of bleeding peptic ulcer glaucoma pregnancy or non-acceptance to use anticonception measures during 13 days after debut high blood pressure >180 systolic, 105, diastolic ketoacidosis with a Base Excess >=2 psychic disorder (not including mild depression) serious infection (neutropenia, tuberculosis) chronic otitis history of vertiginous disease; Ménière, Vertiginous migraine, atypical BPPV", "candidate_expression": "((105) AND (>180) AND (>=2) AND (Base Excess) AND (Ménière) AND (Vertiginous migraine) AND (atypical BPPV) AND (bleeding) AND (blood pressure diastolic) AND (blood pressure systolic) AND (chronic otitis) AND (glaucoma) AND (hearing loss) AND (infection) AND (ketoacidosis) AND (mild depression) AND (neutropenia) AND (not) AND (peptic ulcer) AND (pregnancy or non-acceptance to use anticonception measures during 13 days after debut) AND (psychic disorder) AND (serious) AND (tinnitus) AND (tuberculosis) AND (vertiginous disease) AND (vertigo))"}
{"candidate_id": "LLM02619", "doc_id": "NCT00455663_inc", "case_bucket": "or", "source_criterion": "Diagnosis of schizophrenia or schizoaffective disorder If entering the study as an inpatient, hospitalization was recent Currently receiving treatment with an atypical antipsychotic and continuation on the medication has been recommended Assumes primary responsibility for taking medication Currently living in a stable environment", "candidate_expression": "((atypical antipsychotic) AND (continuation on the medication recommended) AND (hospitalization recent) AND (inpatient) AND (living in a stable environment) AND (schizoaffective disorder) AND (schizophrenia) AND (treatment Currently))"}
{"candidate_id": "LLM02620", "doc_id": "NCT02283996_inc", "case_bucket": "other", "source_criterion": "Patient must be 18 years or older Must meet the following definition for adhesive capsulitis as defined by the American Academy of Orthopedic Surgeons: Self-limiting condition resulting from any inflammatory process about the shoulder in which capsular scar tissue is produced, resulting in pain and limited range of motion; also called frozen shoulder Must be amenable to randomization into either cohort", "candidate_expression": "((18 or older) AND (American Academy of Orthopedic Surgeons) AND (Must be amenable to randomization into either cohort) AND (adhesive capsulitis) AND (years))"}
{"candidate_id": "LLM02621", "doc_id": "NCT00527826_inc", "case_bucket": "or", "source_criterion": "Subject must have a diagnosis of COPD based on the American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria. Male or female subjects, aged >=40 years. Females must be of Non Child Bearing Potential. The definition of Non Child Bearing Potential is as following: Females, regardless of their age, with functioning ovaries and who have a current documented tubal ligation or hysterectomy, or females who are post-menopausal. Have diagnosed COPD stage III or IV according to GOLD criteria: a baseline post-bronchodilator Forced Expiratory Volume, measured at 1 second (FEV1) <50% of predicted normal and a baseline post- bronchodilator FEV1/Inspiratory Vital Capacity (IVC) ratio <70%. Have experienced at least 2 moderate or severe COPD exacerbations leading to medical consultation (requiring oral corticosteroids or increasing dosage of oral corticosteroids and/or antibiotics or hospitalization) within the 12 months preceding Visit 1. Have stable COPD medication within 4 weeks prior to Visit 1 (no new medication added and no dosage changes in medication). Current or ex-smokers with a smoking history of at least 10 pack years (number of pack years = [number of cigarettes per day / 20] x number of years smoked, e.g., 20 cigarettes per day for 10 years, or 10 cigarettes per day for 20 years). Are currently managed at home (outpatients), are ambulatory and able to travel to the clinic. Subjects can be treated with all relevant COPD medication. This includes vaccines, inhaled short-acting beta-2-agonists as needed, short-acting or long-acting anticholinergics (tiotropium), systemic beta-2-agonists, theophylline, mucolytics, antioxidants, beta-1-agonists (for cardiovascular indication), non-invasive ventilation, long term oxygen therapy and can have Cor Pulmonale. A signed and dated written informed consent is obtained prior to participation. Able to comply with the requirements of the protocol and be available for study visits over 52 weeks.", "candidate_expression": "((10 pack years) AND (<50% of predicted normal) AND (<70%) AND (>=40 years) AND (Able to comply with the requirements of the protocol) AND (American Thoracic Society (ATS)/ European Respiratory Society (ERS) criteria) AND (COPD) AND (COPD exacerbations) AND (COPD medication) AND (Child Bearing Potential) AND (FEV1/Inspiratory Vital Capacity (IVC) ratio) AND (Females) AND (Forced Expiratory Volume, measured at 1 second (FEV1)) AND (GOLD criteria) AND (Non) AND (able to travel to the clinic) AND (aged) AND (ambulatory) AND (at home) AND (at least 2) AND (available for study visits) AND (beta-1-agonists) AND (cardiovascular indication) AND (females) AND (functioning ovaries) AND (increasing dosage) AND (long term) AND (managed) AND (managed at home) AND (outpatients) AND (over 52 weeks) AND (oxygen) AND (post- bronchodilator) AND (post-bronchodilator) AND (post-menopausal) AND (prior to participation) AND (smokers) AND (smoking history) AND (stable) AND (stage III or IV) AND (study visits) AND (tiotropium) AND (within 4 weeks prior to Visit 1) AND (within the 12 months preceding Visit 1) AND (written informed consent) AND ((hysterectomy) OR (tubal ligation)) AND ((moderate) OR (severe)) AND ((antibiotics) OR (hospitalization) OR (oral corticosteroids)) AND ((Male) OR (female)) AND ((Current) OR (ex)) AND ((COPD medication) OR (antioxidants) OR (inhaled short-acting beta-2-agonists) OR (long-acting anticholinergics) OR (mucolytics) OR (short-acting) OR (systemic beta-2-agonists) OR (theophylline) OR (vaccines)) AND ((Cor Pulmonale) OR (non-invasive ventilation) OR (oxygen therapy)))"}
{"candidate_id": "LLM02622", "doc_id": "NCT02077556_inc", "case_bucket": "other", "source_criterion": "De novo kidney transplants 20 - 65 years old aspartate aminotransferase/alanine aminotransferase within 2 times the upper limit of normal range", "candidate_expression": "((alanine aminotransferase) AND (aspartate aminotransferase) AND (kidney transplants De novo) AND (old 20 - 65 years))"}
{"candidate_id": "LLM02623", "doc_id": "NCT03256864_exc", "case_bucket": "or", "source_criterion": "Patients who are recipients of multiple solid organ or islet cell tissue transplants, or have previously received an organ or tissue transplant. Patients who have a combined liver-kidney transplant. History of malignancy of any organ system (other than localized basal cell carcinoma of the skin), treated or untreated, within the past 5 years, regardless of whether there is evidence of local recurrence or metastases. Existence of any surgical, medical or mental conditions, other than the current transplantation, which, in the opinion of the investigator, might interfere with the objectives of the study. Pregnant or nursing (lactating) women.", "candidate_expression": "((History) AND (Pregnant) AND (any organ system) AND (combined liver-kidney transplant) AND (current) AND (islet cell tissue transplants) AND (lactating) AND (localized basal cell carcinoma of the skin) AND (malignancy) AND (medical conditions) AND (mental conditions) AND (might interfere with the objectives of the study) AND (multiple) AND (nursing) AND (organ transplant) AND (other than) AND (previously) AND (solid organ transplants) AND (surgical conditions) AND (tissue transplant) AND (transplantation) AND (treated) AND (untreated) AND (within the past 5 years) AND (women))"}
{"candidate_id": "LLM02624", "doc_id": "NCT03561753_exc", "case_bucket": "or", "source_criterion": "Tuberculosis resistant to any of the study drugs (isoniazid, rifampin, EMB, PZA, CFZ, Pto) Unable to take oral medications. History of allergy or intolerance to any of the study drugs Serum aminotransferase (AST or ALT) 3x upper limit of normal or higher Pregnant or nursing females, or plan to become pregnant or nurse during the study period Males planning to conceive a child during the study or within 6 months of cessation of treatment. Any treatment directed against active tuberculosis within 6 months preceding initiation of study drugs. Suspected or documented tuberculosis involving the central nervous system and/or bones and/or joints, and/or miliary tuberculosis and/or pericardial tuberculosis. HIV infected HBV infected or HCV infected (these increase the risk of TB-drug induced hepatotoxicity) Weight less than 40.0 kg. Known allergy or intolerance to any of the study medications. Individuals will be excluded from enrollment if, at the time of enrollment, their M. tuberculosis isolate is already known to be resistant to any of the study drugs. QTcF > 500 msec Other medical conditions, that, in the investigator's judgment, make study participation not in the individual's best interest. Current or planned incarceration or other involuntary detention Having participated in other clinical studies with dosing of investigational agents within 8 weeks prior to trial start or currently enrolled in an investigational study that includes treatment with medicinal agents. Subjects who are participating in observational studies or who are in a follow up period of a trial that included drug therapy may be considered for inclusion.", "candidate_expression": "((3x upper limit of normal or higher) AND (> 500 msec) AND (HIV infected) AND (History) AND (M. tuberculosis isolate) AND (Males) AND (QTcF) AND (Serum aminotransferase) AND (Tuberculosis) AND (Unable to take oral medications) AND (Weight) AND (active) AND (cessation of treatment) AND (conceive a child) AND (currently) AND (during the study period) AND (enrolled in an investigational study) AND (females) AND (investigational agents) AND (less than 40.0 kg) AND (medicinal agents) AND (participated in other clinical studies) AND (plan to) AND (planning to) AND (resistant to) AND (resistant to any of the study drugs) AND (study drugs) AND (study medications) AND (the study) AND (treatment) AND (trial start) AND (tuberculosis) AND (within 6 months preceding initiation of study drugs) AND (within 8 weeks prior to trial start) AND ((allergy) OR (intolerance)) AND ((ALT) OR (AST)) AND ((Pregnant) OR (nursing)) AND ((become pregnant) OR (nurse)) AND ((during the study) OR (within 6 months of cessation of treatment)) AND ((bones) OR (central nervous system) OR (joints) OR (miliary tuberculosis) OR (pericardial tuberculosis)) AND ((Suspected) OR (documented)) AND ((HBV infected) OR (HCV infected)) AND ((Current) OR (planned)) AND ((incarceration) OR (involuntary detention)) AND ((CFZ) OR (EMB) OR (PZA) OR (Pto) OR (isoniazid) OR (rifampin)))"}
{"candidate_id": "LLM02625", "doc_id": "NCT02638935_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women Women with breast implants on the same side as the lesion Women that underwent local radiation or chemotherapy within the last 12 months Women with history of breast cancer or breast surgery in the same quadrant Lesions in or close to scar tissue (< 1cm) Skin lesions or lesions that have been biopsied previously Lesion larger than 4 cm in the longest dimension No lesion should be included when more than 50% of the lesion is further down than 4 cm beneath the skin level.", "candidate_expression": "((< 1cm) AND (Lesion) AND (Lesions) AND (Pregnant) AND (Skin lesions) AND (Women) AND (beneath the skin level) AND (biopsied) AND (breast cancer) AND (breast implants) AND (breast surgery) AND (chemotherapy) AND (further down than 4 cm) AND (in or close to scar tissue) AND (lactating) AND (larger than 4 cm) AND (lesion) AND (lesions) AND (local radiation) AND (longest dimension) AND (more than 50% of the lesion) AND (previously) AND (same quadrant) AND (same side as the lesion) AND (the lesion) AND (within the last 12 months) AND (women))"}
```
