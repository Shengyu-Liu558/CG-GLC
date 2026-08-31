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
{"candidate_id": "LLM06276", "doc_id": "NCT03404804_inc", "case_bucket": "other", "source_criterion": "Children aged 3-16 with a parent/guardian (hereafter termed parent) reported history of allergy to a penicillin antibiotic in which the reported allergic reaction occurred at least six months prior to the current PED visit. Only children well enough to be discharged to home at the conclusion of the PED visit are eligible.", "candidate_expression": "((Children) AND (PED) AND (aged 3-16) AND (allergic reaction at least six months prior to the current PED visit) AND (allergy) AND (penicillin antibiotic) AND (well enough to be discharged to home at the conclusion of the PED visit))"}
{"candidate_id": "LLM06277", "doc_id": "NCT02774317_inc", "case_bucket": "or", "source_criterion": "Nonsurgical neonates and babies up to age 6 months with INR 1.5 or more who are deemed clinically to need plasma infusion.", "candidate_expression": "((1.5 or more) AND (INR) AND (Nonsurgical) AND (age) AND (need) AND (plasma infusion) AND (up to age 6 months) AND ((babies) OR (neonates)))"}
{"candidate_id": "LLM06278", "doc_id": "NCT03187639_exc", "case_bucket": "or", "source_criterion": "Atrial fibrillation of new onset or when rate control has been difficult Known bigemini/trigeminy Prior CABG surgery Allergic to contrast Advanced renal impairment Significant valve disease (severe aortic stenosis or regurgitation; severe mitral regurgitation) Life expectancy <12 months Inclusion in another trial without prior agreement with CI", "candidate_expression": "((Advanced renal impairment) AND (Allergic) AND (Atrial fibrillation new onset) AND (CABG surgery Prior) AND (Inclusion in another trial without prior agreement with CI) AND (Life expectancy <12 months) AND (aortic stenosis) AND (bigemini) AND (contrast) AND (mitral regurgitation severe) AND (rate control has been difficult) AND (regurgitation) AND (trigeminy) AND (valve disease))"}
{"candidate_id": "LLM06279", "doc_id": "NCT03280017_exc", "case_bucket": "other", "source_criterion": "History of morphine allergy History of bupivacaine allergy Contraindication for ketamine infusion Contraindication for thoracic paravertebral block Anticipated postoperative positive pressure ventilation Body mass index more than 35 Any known psychiatric disorder", "candidate_expression": "((Body mass index more than 35) AND (Contraindication) AND (allergy History) AND (bupivacaine) AND (ketamine) AND (ketamine infusion) AND (morphine) AND (paravertebral block thoracic) AND (positive pressure ventilation postoperative) AND (psychiatric disorder))"}
{"candidate_id": "LLM06280", "doc_id": "NCT02985710_exc", "case_bucket": "or", "source_criterion": "Subjects with cognitive, psychiatric, or other problems that preclude informed consent. Patients with history of glucose intolerance or diabetes. Patient on chemotherapy People with any open or bleeding wounds at any sensor plate contact surface location People with any type of implantable device People with missing hand(s) and/or leg(s) Pregnant women or women who are uncertain about a possible pregnancy Patients sensitive to chemicals used to induce sweating Patients with heat intolerance Patients with bleeding disorders Patients on current anticoagulant therapy Patients with keloids on the intended biopsy site People with hypersensitivity to local amide-type anesthetics", "candidate_expression": "((Pregnant) AND (anticoagulant therapy current) AND (bleeding disorders) AND (bleeding wounds at any sensor plate contact surface location) AND (chemotherapy) AND (cognitive problems) AND (diabetes history) AND (glucose intolerance history) AND (heat intolerance) AND (hypersensitivity) AND (implantable device) AND (keloids on the intended biopsy site) AND (local amide-type anesthetics) AND (missing hand) AND (missing leg) AND (open wounds at any sensor plate contact surface location) AND (other problems that preclude informed consent) AND (possible pregnancy) AND (psychiatric problems) AND (sensitive to chemicals used to induce sweating))"}
{"candidate_id": "LLM06281", "doc_id": "NCT03208998_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Active) AND (Psychiatric disease) AND (autoimmune hepatitis) AND (consumption of alcohol) AND (drugs consumption of) AND (hepatitis C virus) AND (hepatitis D virus) AND (human immunodeficiency virus) AND (liver) AND (neoplastic diseases))"}
{"candidate_id": "LLM06282", "doc_id": "NCT00351611_inc", "case_bucket": "other", "source_criterion": "Epilepsy partial seizure subjects. Currently taking 1 to 3 antiepileptic drugs.", "candidate_expression": "((1 to 3) AND (Epilepsy) AND (antiepileptic drugs) AND (partial seizure))"}
{"candidate_id": "LLM06283", "doc_id": "NCT03228017_exc", "case_bucket": "or", "source_criterion": "Unable to speak Spanish or English Active smoking (within the past year) Autoimmune, rheumatologic or inflammatory disease which are not psoriasis or psoriatic arthritis Known active cancer receiving treatment Pregnancy Anemia (hemoglobin < 9 mg/dl) or thrombocytopenia (Platelet count <75), or thrombocytosis (Platelet count >600) A history of severe bleeding or bleeding disorders Current medication use which interact with either aspirin or atorvastatin Chronic kidney disease (CrCl < 30ml/min) Congestive heart failure Currently taking aspirin or a statin. NSAID use within the past 48 hours", "candidate_expression": "((Chronic kidney disease) AND (Congestive heart failure) AND (CrCl < 30ml/min) AND (NSAID within the past 48 hours) AND (Platelet count <75) AND (Platelet count >600) AND (Pregnancy) AND (aspirin) AND (bleeding disorders) AND (bleeding severe) AND (cancer active) AND (hemoglobin < 9 mg/dl) AND (interact) AND (medication Current) AND (smoking Active within the past year) AND (statin) AND (treatment) AND ((Anemia) OR (thrombocytopenia) OR (thrombocytosis)) AND ((aspirin) OR (atorvastatin)) AND ((disease Autoimmune) OR (disease rheumatologic) OR (inflammatory disease)) AND ((psoriasis) OR (psoriatic arthritis)))"}
{"candidate_id": "LLM06284", "doc_id": "NCT02787863_inc", "case_bucket": "or", "source_criterion": "Individuals of both sexes from 18 years with a diagnosis of community-acquired pneumonia, COPD or Bronchial Asthma; The presence of signed and dated informed consent to participate in a clinical study; The ability to perform the requirements of the Protocol; For women of childbearing age is a negative result of a pregnancy test before vaccination. community-acquired pneumonia: the presence of radiologically confirmed infiltration of the lung tissue; the presence of at least two of the following clinical signs: acute fever early in the disease (temperature > 38.0°C), cough with sputum, the physical signs of pneumonia (focus of crepitate and/or fine bubble rales, bronchial breathing hard, shortening of percussion sounds), leukocytosis > 10*10 9 /l and/or stab shift > 10%; the occurrence of the disease outside the hospital and the organized groups (such as nursing homes, sanatoriums, etc.). COPD: dyspnea: progressive (worsens over time), increases with exertion, persistent; chronic cough (may appear sporadically and may be unproductive); chronic expectoration; the impact of risk factors in the medical history (Smoking, occupational dust pollutants and chemicals); widespread wheeze on auscultation of the chest and/or distant wheezing in the chest; family history of COPD; spirometric data confirming the presence of fixed bronchial obstruction.", "candidate_expression": "((Bronchial Asthma) AND (COPD) AND (COPD family history) AND (For women of childbearing age is a negative result of a pregnancy test before vaccination.) AND (Smoking) AND (The ability to perform the requirements of the Protocol;) AND (acute fever early in the disease) AND (both sexes) AND (bronchial breathing hard) AND (chronic cough persistent) AND (chronic expectoration) AND (community-acquired pneumonia) AND (cough with sputum) AND (crepitate rales) AND (distant wheezing in the chest) AND (dyspnea progressive worsens over time increases with exertion) AND (fine bubble rales) AND (fixed bronchial obstruction) AND (from 18 years from 18 years) AND (infiltration of the lung tissue radiologically confirmed) AND (leukocytosis > 10*10 9 /l) AND (occupational dust pollutants and chemicals) AND (physical signs) AND (pneumonia) AND (radiologically) AND (risk factors) AND (shortening of percussion sounds) AND (spirometric) AND (stab shift > 10%) AND (temperature > 38.0°C) AND (wheeze on auscultation of the chest widespread))"}
{"candidate_id": "LLM06285", "doc_id": "NCT02894372_exc", "case_bucket": "other", "source_criterion": "Purulent infection Refusal to participate Allergy to tested material", "candidate_expression": "((Allergy tested material) AND (Purulent infection) AND (Refusal to participate) AND (tested material))"}
{"candidate_id": "LLM06286", "doc_id": "NCT00965900_inc", "case_bucket": "or", "source_criterion": "Liver cirrhosis Age between 18 and 70 years Esophageal varices with high bleeding risk: more than F2 and red color sign No previous history of upper gastrointestinal bleeding No previous history of endoscopic, radiologic, or surgical therapy for varices or ascites Do not take beta-blocker, ACE inhibitor, or nitrate Child-Pugh score <12", "candidate_expression": "((Age between 18 and 70 years) AND (Child-Pugh score <12) AND (Esophageal varices high bleeding risk) AND (F2 more than) AND (Liver cirrhosis) AND (red color sign) AND NOT (upper gastrointestinal bleeding) AND ((ascites) OR (varices)) AND ((endoscopic therapy) OR (radiologic therapy) OR (surgical therapy)) AND ((ACE inhibitor) OR (beta-blocker) OR (nitrate)))"}
{"candidate_id": "LLM06287", "doc_id": "NCT02647788_exc", "case_bucket": "or", "source_criterion": "ASA> 3; Coagulopathy; Renal disease, Liver disease, History of recent gastro-intestinal bleeding Pregnancy. Diagnosis of chronic pain currently taking opioid pain medication or with a history of drug abuse. Patients with a self-described allergy to ASA, acetaminophen, NSAIDS and codeine. All patients receiving a brachial plexus block for anesthesia and/or analgesia", "candidate_expression": "((ASA) AND (ASA > 3) AND (Coagulopathy) AND (Liver disease) AND (NSAIDS) AND (Pregnancy) AND (Renal disease) AND (acetaminophen) AND (allergy) AND (brachial plexus block) AND (chronic pain) AND (codeine) AND (drug abuse history of) AND (gastro-intestinal bleeding recent) AND (opioid pain medication))"}
{"candidate_id": "LLM06288", "doc_id": "NCT02570347_inc", "case_bucket": "other", "source_criterion": "Age 18-65 years History of snake bite with features of local envenomation with/without systemic features Less than 24 hours since bite, AND No prior antibiotic treatment", "candidate_expression": "((Age 18-65 years) AND (bite) AND (local envenomation features of) AND (snake bite) AND (systemic features Less than 24 hours since bite) AND NOT (antibiotic treatment prior))"}
{"candidate_id": "LLM06289", "doc_id": "NCT02652637_exc", "case_bucket": "or", "source_criterion": "Emergency surgery needed Bowel obstruction Colonoscopy scheduled to be undertaken peroperatively Other reason indicating mechanical preparation or contradicting it Allergy to used drugs (PEG, neomycin, metronidazole)", "candidate_expression": "((Allergy) AND (Bowel obstruction) AND (Colonoscopy) AND (Emergency surgery needed) AND (PEG) AND (contradicting) AND (drugs) AND (mechanical preparation) AND (metronidazole) AND (neomycin) AND (undertaken scheduled peroperatively))"}
{"candidate_id": "LLM06290", "doc_id": "NCT03119766_inc", "case_bucket": "or", "source_criterion": "Men and women aged 18-45 years. Diagnosis of functional dyspepsia, based on the Rome IV criteria (2016). GIS score of at least 6. Negative H. pylori test . Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial. Patients who agree to use an effective method of contraception throughout the clinical trial.", "candidate_expression": "((Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial) AND (GIS score at least 6) AND (H. pylori test Negative) AND (Patients who agree to use an effective method of contraception throughout the clinical trial.) AND (Rome IV criteria (2016)) AND (aged 18-45 years) AND (functional dyspepsia) AND ((Men) OR (women)))"}
{"candidate_id": "LLM06291", "doc_id": "NCT02334722_inc", "case_bucket": "or", "source_criterion": "Adult (>18 years of age and older) patients who have or will have undergone surgical resection or biopsy of a supratentorial brain tumor and are able to consent for themselves. Able to be randomized prior to or up to 48 hours after surgery.", "candidate_expression": "((Adult) AND (age) AND (and older >18 years) AND (are able to consent for themselves) AND (biopsy) AND (supratentorial brain tumor) AND (surgical resection) AND (will have undergone))"}
{"candidate_id": "LLM06292", "doc_id": "NCT03149887_exc", "case_bucket": "or", "source_criterion": "Pregnancy, coagulopathy, allergy to bupivacaine, renal failure, hepatic insufficiency, and/or inappropriate candidate for usual therapy (specifically, if unable to receive the usual preoperative interscalene nerve block: preexisting nerve injury on side of surgery, refusal of nerve block, infection at site of nerve block).", "candidate_expression": "((Pregnancy) AND (allergy) AND (bupivacaine) AND (coagulopathy) AND (hepatic insufficiency) AND (inappropriate candidate) AND (infection) AND (nerve injury) AND (preexisting) AND (preoperative interscalene nerve block) AND (refusal of nerve block) AND (renal failure) AND (side of surgery) AND (site of nerve block) AND (unable to receive) AND (usual therapy))"}
{"candidate_id": "LLM06293", "doc_id": "NCT03388840_inc", "case_bucket": "other", "source_criterion": "male patients with androgenetic alopecia between 18 years and 60 years", "candidate_expression": "((androgenetic alopecia) AND (between 18 years and 60 years) AND (male) AND (years))"}
{"candidate_id": "LLM06294", "doc_id": "NCT02643381_exc", "case_bucket": "or", "source_criterion": "Children (<18 years old). Women who are known to be pregnant. Any patient who has been previously randomized in the EvK Trial. Patients who require endotracheal intubation without sedative medication. For example, patients in full cardiac arrest. Patients with a known allergy to ketamine or etomidate. Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial.", "candidate_expression": "((<18 years) AND (Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial) AND (Children) AND (Women) AND (allergy) AND (endotracheal intubation) AND (full cardiac arrest) AND (old) AND (pregnant) AND (previously) AND (randomized) AND (require) AND (sedative medication) AND (without) AND ((etomidate) OR (ketamine)))"}
{"candidate_id": "LLM06295", "doc_id": "NCT02186600_inc", "case_bucket": "other", "source_criterion": "Women who are in their first 5 years of menopause Have a T score between -1 and -2.49 at the femoral neck, total hip, or L1-L4 spine Be 19 years of age or older Have their health care provider's permission to enroll in the study.", "candidate_expression": "((T score between -1 and -2.49 femoral neck total hip L1-L4 spine) AND (Women n their first 5 years of menopause) AND (age 19 years of age or older) AND (menopause menopause))"}
{"candidate_id": "LLM06296", "doc_id": "NCT01680081_exc", "case_bucket": "or", "source_criterion": "Contraindication of CT Known allergy to iodinated contrast media or history of contrast-induced nephropathy Decreased renal function: elevated serum creatinine(>1.5mg/dl) Contraindication to beta-blockers Severe arrhythmia: arterial fibrillation or uncontrolled tachyarrhythmia, or advanced atrioventricular block (second or third degree heart block) Contraindication of MRI Claustrophobia Metallic hazards Pacemaker implant eGFR<30 ml/min Unstable or uncooperative patients Limited life expectancy due to cancer or end-stage renal or liver disease Evidence of severe symptomatic heart failure (NYHA Class III or IV) Previous myocardial infarction, coronary artery intervention, coronary artery bypass surgery, or other cardiac surgery", "candidate_expression": "((<30 ml/min) AND (>1.5mg/dl) AND (Class III or IV) AND (Claustrophobia) AND (Contraindication) AND (Contraindication of CT) AND (Decreased) AND (Known allergy) AND (Limited) AND (MRI) AND (Metallic hazards) AND (NYHA) AND (Pacemaker implant) AND (Previous) AND (Severe) AND (Unstable patients) AND (advanced atrioventricular block) AND (arrhythmia) AND (arterial fibrillation) AND (beta-blockers) AND (cancer) AND (contrast-induced nephropathy) AND (coronary artery bypass surgery) AND (coronary artery intervention) AND (eGFR) AND (elevated) AND (end-stage renal disease) AND (heart failure) AND (iodinated contrast media) AND (life expectancy) AND (liver disease) AND (myocardial infarction) AND (other cardiac surgery) AND (renal function) AND (second degree heart block) AND (serum creatinine) AND (severe) AND (symptomatic) AND (third degree heart block) AND (uncontrolled tachyarrhythmia) AND (uncooperative patients))"}
{"candidate_id": "LLM06297", "doc_id": "NCT02245256_inc", "case_bucket": "or", "source_criterion": "Adult patients (18years old or older) undergoing living-donor or deceased-donor liver transplantation", "candidate_expression": "((Adult) AND (deceased-donor liver transplantation) AND (living-donor liver transplantation) AND (years 18years old or older))"}
{"candidate_id": "LLM06298", "doc_id": "NCT03247413_exc", "case_bucket": "or", "source_criterion": "patient not previously scheduled for radiofrequency ablation of the cervical, thoracic, or lumbar facets, or sacroiliac joints on anticoagulation have a pacemaker age less than 18 years old non-English speaking", "candidate_expression": "((English speaking) AND (age) AND (anticoagulation) AND (less than 18 years old) AND (non) AND (not) AND (pacemaker) AND (previously) AND (radiofrequency ablation) AND (scheduled for) AND ((cervical facets) OR (lumbar facets) OR (sacroiliac joints) OR (thoracic facets)))"}
{"candidate_id": "LLM06299", "doc_id": "NCT02573909_exc", "case_bucket": "or", "source_criterion": "Planned surgery under regional anesthesia contraindication to the study drug contraindication to the lumbar puncture Contraindication to oxycodone Pregnancy or lactation no informed consent", "candidate_expression": "((Contraindication) AND (Planned) AND (Pregnancy) AND (contraindication) AND (lactation) AND (lumbar puncture) AND (oxycodone) AND (regional anesthesia) AND (study drug) AND (surgery))"}
{"candidate_id": "LLM06300", "doc_id": "NCT03045562_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
