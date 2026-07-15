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
{"candidate_id": "LLM07751", "doc_id": "NCT00235170_exc", "case_bucket": "or", "source_criterion": "1. Congestive heart failure; 2. CABG or Percutaneous Coronary Intervention (PCI) procedure; 3. Planned need for major surgery (e.g. valve surgery or resection of aortic or left ventricular aneurysm, carotid end-arterectomy, abdominal aortic aneurysm surgery etc.); 4. Congenital heart disease; 5. Transmural myocardial infarction within the previous seven days and CK has not returned to normal; 6. Chest pain lasting longer than 30 minutes within 12 hours pre-procedure, if CK enzymes positive (≥ 2x the normal upper limit). 7. History of any cerebrovascular accident; 8. Left main stenosis of 50% or more; 9. Intention to treat more than 1 totally occluded major epicardial vessel; 10. Single vessel (single territory) disease.", "candidate_expression": "((50% or more) AND (CK) AND (CK enzymes) AND (Chest pain) AND (Congenital heart disease) AND (Congestive heart failure) AND (History of) AND (Intention to) AND (Left main stenosis) AND (Single vessel disease) AND (Transmural myocardial infarction) AND (any cerebrovascular accident) AND (has not returned) AND (lasting longer than 30 minutes) AND (more than 1) AND (normal) AND (positive) AND (single territory disease) AND (totally occluded major epicardial vessel) AND (treat) AND (within 12 hours pre-procedure) AND (within the previous seven days) AND (≥ 2x the normal upper limit) AND ((CABG) OR (Percutaneous Coronary Intervention (PCI))) AND ((abdominal aortic aneurysm surgery) OR (carotid end-arterectomy) OR (major surgery) OR (resection of aortic aneurysm) OR (resection of left ventricular aneurysm) OR (valve surgery)))"}
{"candidate_id": "LLM07752", "doc_id": "NCT02969187_inc", "case_bucket": "or", "source_criterion": "Fulfills NIH criteria for bariatric surgery Planned operation of laparoscopic Roux-en Y gastric bypass (LRYGB) or laparoscopic sleeve gastrectomy (LSG) as primary bariatric procedure", "candidate_expression": "((Fulfills) AND (NIH criteria) AND (bariatric surgery) AND (laparoscopic Roux-en Y gastric bypass (LRYGB)) AND (laparoscopic sleeve gastrectomy (LSG)) AND (primary))"}
{"candidate_id": "LLM07753", "doc_id": "NCT02299947_exc", "case_bucket": "or", "source_criterion": "Prior trombosis or myocardial infarction, congenital coagulation disorder, use of anti-coagulants prior to surgery, prior thoracic surgery, pregnancy, pre-operative fibrinogen concentration <1g/L", "candidate_expression": "((<1g/L) AND (Prior) AND (pre-operative) AND (prior) AND (prior to surgery) AND ((anti-coagulants) OR (congenital coagulation disorder) OR (fibrinogen concentration) OR (myocardial infarction) OR (pregnancy) OR (thoracic surgery) OR (trombosis)))"}
{"candidate_id": "LLM07754", "doc_id": "NCT01078051_inc", "case_bucket": "or", "source_criterion": "Patients with angina or silent ischemia and documented ischemia Patients who are eligible for intracoronary stenting Age > 18 years De novo lesion CTO Reference vessel size 2.5 mm by visual estimation At least one CTO lesions located in proximal or mid epicardial coronary artery. (If the patient has two CTO lesions, one CTO lesion should be located in proximal or mid epicardial coronary artery) Angiographically defined total occlusion over 3 months If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)", "candidate_expression": "((2.5 mm) AND (3 months) AND (> 18 years) AND (Age) AND (Angiographically defined) AND (At least one) AND (CTO) AND (CTO lesions) AND (De novo lesion) AND (If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)) AND (Reference vessel size by visual estimation) AND (coronary artery) AND (documented) AND (intracoronary stenting) AND (silent) AND (total occlusion) AND ((angina) OR (ischemia)) AND ((in proximal coronary artery) OR (mid epicardial coronary artery)))"}
{"candidate_id": "LLM07755", "doc_id": "NCT02386800_exc", "case_bucket": "other", "source_criterion": "Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy. Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up.", "candidate_expression": "((Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy) AND (Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test.) AND (Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up))"}
{"candidate_id": "LLM07756", "doc_id": "NCT00356148_exc", "case_bucket": "or", "source_criterion": "Ductal carcinoma in situ (DCIS; stage 0 cancer), Advanced or distant metastatic stage, Receiving any neoadjuvant therapy, History of receiving any antibiotics within prior 3 months, History of immunodeficiency, Having a remote infection, History of reaction to study antibiotics, Denial of signing the consent form.", "candidate_expression": "((0) AND (Denial of) AND (Ductal carcinoma in situ) AND (History) AND (antibiotics) AND (immunodeficiency) AND (neoadjuvant therapy) AND (reaction) AND (remote infection) AND (signing the consent form) AND (stage) AND (study antibiotics) AND (within prior 3 months) AND ((DCIS) OR (cancer)) AND ((Advanced metastatic) OR (distant metastatic)))"}
{"candidate_id": "LLM07757", "doc_id": "NCT02251249_inc", "case_bucket": "or", "source_criterion": "Patient over 18 years weighing between 65 and 85 Kg Referred for STEMI within 6 hours from beginning of chest pain or stable coronary artery disease requiring a loading dose of Prasugrel or Ticagrelor according to the international recommendations. No previous treatment with Clopidogrel, Prasugrel or Ticagrelor. Patient fasting for at least 6 hours. Affiliate or receiving a social security system. Written informed consent.", "candidate_expression": "((Clopidogrel) AND (Prasugrel) AND (STEMI within 6 hours from beginning of chest pain) AND (Ticagrelor) AND (Written informed consent) AND (chest pain) AND (coronary artery disease stable) AND (fasting for at least 6 hours.) AND (weighing between 65 and 85 Kg) AND (years over 18) AND NOT (treatment previous))"}
{"candidate_id": "LLM07758", "doc_id": "NCT03047538_inc", "case_bucket": "or", "source_criterion": "a very high cardiovascular risk and LDL-cholesterol> 1.8 mmol / l a high cardiovascular risk and LDL-cholesterol> 2.5 mmol / l Patient with a high or very high cardiovascular risk treated by lipidlowering therapy with statin", "candidate_expression": "((> 1.8 mmol / l) AND (> 2.5 mmol / l) AND (LDL-cholesterol) AND (cardiovascular risk) AND (high) AND (lipidlowering therapy) AND (stati) AND (very high) AND ((high) OR (very high)))"}
{"candidate_id": "LLM07759", "doc_id": "NCT02515773_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have had exposure to a total daily dose of MET 1000 mg bid for at least 2 weeks in the past 3 months; Patients will be excluded if they could not tolerate MET during the recommended titration schedule outlined in the protocol; Major neurological or medical illnesses that affect weight gain (e.g., unstable thyroid disease) or require a systemic medication that might impact weight or glucose regulation (e.g., diabetes mellitus [insulin], chronic renal failure [steroids]); Fasting glucose = 126 mg/dL on 2 occasions during screening indicating need for prompt treatment; If lab results are available in the last 6 months, then a serum creatinine =1.3 mg/dL on 2 occasions during screening and/or follow-up, indicating potential impairment of renal functioning; Pregnant or breast feeding; Children and caregivers who are unable to complete assessments for any reason;", "candidate_expression": "((1000 mg bid) AND (2) AND (2 o) AND (= 126 mg/dL) AND (=1.3 mg/dL) AND (Children and caregivers who are unable to complete assessments for any reason) AND (Fasting glucose) AND (MET) AND (Pregnant or breast feeding) AND (at least 2 weeks in the past 3 months) AND (not tolerate) AND (serum creatinine) AND (unstable) AND ((chronic renal failure) OR (diabetes mellitus) OR (insulin) OR (steroids) OR (thyroid disease)))"}
{"candidate_id": "LLM07760", "doc_id": "NCT03430284_exc", "case_bucket": "or", "source_criterion": "type 1 diabetes,specific types of diabetes,gestational diabetes or pregestational diabetes; acute cardiovascular or cerebrovascular accidents within past 3 months; severe hepatic or renal dysfunction; malignant tumor; allergic history or contraindication for any drugs in trials; taking part in other clinical trials; obviously poor compliance.", "candidate_expression": "((drugs in trials any) AND (malignant tumor) AND (poor compliance obviously) AND (taking part in other clinical trials) AND ((hepatic dysfunction) OR (renal dysfunction)) AND ((allergic history) OR (contraindication)) AND ((diabetes specific types) OR (gestational diabetes) OR (pregestational diabetes) OR (type 1 diabetes)) AND ((accidents cardiovascular) OR (cerebrovascular accidents)))"}
{"candidate_id": "LLM07761", "doc_id": "NCT03056391_inc", "case_bucket": "other", "source_criterion": "1. Patient age ≥ 12 years 2. Presence of P. knowlesi malaria, confirmed by positive blood smear with asexual forms of P. knowlesi. 3. Temperature >38C on admission or fever during the preceding 48 hours 4. Enrolled within 18 hours of commencing antimalarial treatment 5. Written informed consent from patient or attending relative able to and willing to give informed consent. Consent form and information sheets will be translated into Malay and copies provided to the patient.", "candidate_expression": "((>38C) AND (Enrolled) AND (P. knowlesi malaria) AND (Temperature) AND (Written informed consent from patient or attending relative able to and willing to give informed consent.) AND (age) AND (antimalarial treatment) AND (blood smear) AND (commencing antimalarial treatment) AND (positive) AND (with asexual forms of P. knowlesi) AND (within 18 hours) AND (≥ 12 years))"}
{"candidate_id": "LLM07762", "doc_id": "NCT02162433_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitivity reaction to dexmedetomidine Organ dysfunction (renal/hepatic failure or leukemia) Cardiac disease (congenital or acquired) Airway or thoracic malformation Cerebral palsy Hypotonia Need for premedication Current/recent upper respiratory infection (within four weeks prior to the surgery) Asthma Allergy or intolerance to clonidine Non-English speaking parents/patients.", "candidate_expression": "((Asthma) AND (Cardiac disease) AND (Cerebral palsy) AND (Hypotonia) AND (Need for) AND (Organ dysfunction) AND (clonidine) AND (dexmedetomidine) AND (premedication) AND (surgery) AND (the surgery) AND (upper respiratory infection) AND (within four weeks prior to the surgery) AND ((allergy) OR (hypersensitivity)) AND ((acquired) OR (congenital)) AND ((Airway malformation) OR (thoracic malformation)) AND ((Current) OR (recent)) AND ((Allergy) OR (intolerance)) AND ((Non-English speaking parents) OR (Non-English speaking patients)) AND ((hepatic failure) OR (leukemia) OR (renal failure)))"}
{"candidate_id": "LLM07763", "doc_id": "NCT02205931_inc", "case_bucket": "other", "source_criterion": "Age between 1 month and 24 months of age (not beyond second birthday at baseline). Diagnosis of epilepsy confirmed. At least an average of 4 seizures/week in baseline period. Failed response to previous trial of two anti-epileptic drugs. In the case of infantile spasms this could include a trial of corticosteroids. Children with written informed consent from parent/guardian.", "candidate_expression": "((Age between 1 month and 24 months of age) AND (Children with written informed consent from parent/guardian) AND (anti-epileptic drugs two) AND (corticosteroids) AND (epilepsy) AND (response Failed) AND (seizures At least an average of 4 /week))"}
{"candidate_id": "LLM07764", "doc_id": "NCT02957305_exc", "case_bucket": "or", "source_criterion": "patients who do not wish to participate in the project; patients with ectopic pregnancy; patients with comorbidities (heart failure congestive, chronic obstructive pulmonary disease); patients with hypovolemic shock; patients with cervical incompetence; patients with infected miscarriage/abortion (presence of fever, pus from the cervix, leukocytosis [> 14000]); patients with twin pregnancy; patients with Marfan syndrome; patients allergic to misoprostol; patients with coagulopathy; patients with opening of cervical internal os (4 mm of dilatation at the time of consultation); patients with previous surgery of the cervix (conization); patients with concomitant use of IUDs.", "candidate_expression": "((4 mm of dilatation) AND (> 14000) AND (IUDs) AND (Marfan syndrome) AND (allergic) AND (cervical incompetence) AND (cervix) AND (coagulopathy) AND (comorbidities) AND (conization) AND (ectopic pregnancy) AND (hypovolemic shock) AND (infected) AND (misoprostol) AND (opening of cervical internal os) AND (patients who do not wish to participate in the project) AND (pregnancy) AND (surgery) AND (twin) AND ((abortion) OR (miscarriage)) AND ((fever) OR (leukocytosis) OR (pus from the cervix)) AND ((chronic obstructive pulmonary disease) OR (heart failure congestive)))"}
{"candidate_id": "LLM07765", "doc_id": "NCT03131050_inc", "case_bucket": "or", "source_criterion": "Has given written informed consent. Male or female outpatients aged at least 18 years and not more than 45 years. Has a diagnosis of major depressive disorder by Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria. Current HAMD-17 score = 20 and the duration of the index episode is greater than or equal to four weeks.", "candidate_expression": "((HAMD-17 Current score = 20) AND (Has given written informed consent.) AND (Male) AND (aged at least 18 years and not more than 45 years) AND (female) AND (index episode greater than or equal to four weeks) AND (major depressive disorder Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria) AND (outpatients))"}
{"candidate_id": "LLM07766", "doc_id": "NCT02886962_exc", "case_bucket": "or", "source_criterion": "Formal indication to oral anticoagulation beside atrial fibrillation (mechanic heart valves, recurrent thrombophlebitis, antiphospholipid syndrome) Life expectancy < 6 months (e.g., terminal cancer) Live donor transplantation scheduled within 6 months Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women Women of child bearing potential, unless they are using an effective method of birth control Patient under legal guardianship Patients under law protection Known hypersensibility to coumadin or indoine derivatives or to any excipients (CI to oral AVK) Severe liver failure (CI to oral AVK)", "candidate_expression": "((Life expectancy < 6 months) AND (Live donor transplantation scheduled within 6 months) AND (Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women) AND (Women of child bearing potential, unless they are using an effective method of birth control) AND (antiphospholipid syndrome) AND (atrial fibrillation) AND (coumadin) AND (hypersensibility) AND (indication) AND (indoine) AND (liver failure Severe) AND (mechanic heart valves) AND (oral anticoagulation) AND (recurrent thrombophlebitis) AND (terminal cancer))"}
{"candidate_id": "LLM07767", "doc_id": "NCT02570230_exc", "case_bucket": "or", "source_criterion": "allergy to morphine or ketamine contraindicate to ketamine remain intubated in the postoperative period", "candidate_expression": "((allergy) AND (contraindicate) AND (in the postoperative period) AND (intubated) AND (ketamine) AND (postoperative period) AND ((ketamine) OR (morphine)))"}
{"candidate_id": "LLM07768", "doc_id": "NCT02746900_exc", "case_bucket": "or", "source_criterion": "Multiple pregnancy Prior spontaneous preterm birth or second trimester losses between 16(0) and 36(6) weeks Cerclage in situ Painful regular uterine contraction and/or preterm labor Ruptured membranes Major fetal defects Active vaginal bleeding Placenda previa and/or accreta Cervical dilation >1.5 cm and/or visible membranes by pelvic exam Suspicion of chorioamnionitis", "candidate_expression": "((>1.5 cm) AND (Active vaginal bleeding) AND (Cerclage in situ) AND (Major fetal defects) AND (Multiple pregnancy) AND (Prior) AND (Ruptured membranes) AND (Suspicion of) AND (between 16(0) and 36(6) weeks) AND (chorioamnionitis) AND (second trimester) AND (visible membranes) AND ((Placenda previa) OR (accreta)) AND ((Cervical dilation) OR (pelvic exam)) AND ((losses) OR (spontaneous preterm birth)) AND ((Painful regular uterine contraction) OR (preterm labor)))"}
{"candidate_id": "LLM07769", "doc_id": "NCT02041299_exc", "case_bucket": "or", "source_criterion": "Thalassemia syndromes; Myelodysplastic syndrome (MDS) or myelofibrosis; Diamond Blackfan anemia; Primary bone marrow failure; Baseline LIC >30 mg/g dw (measured by MRI); Unable or unwilling to undergo a 7 day washout period if currently being treated with deferiprone or deferoxamine or deferasirox; Previous discontinuation of treatment with deferiprone or deferoxamine due to adverse events; History or presence of hypersensitivity or idiosyncratic reaction to deferiprone or deferoxamine; Treated with hydroxyurea within 30 days; History of malignancy; Evidence of abnormal liver function (serum ALT level(s) > 5 times upper limit of normal at screening or creatinine levels >2 times upper limit of normal at screening); A serious, unstable illness, as judged by the Investigator, during the past 3 months before screening/baseline visit including but not limited to: hepatic, renal, gastro-enterologic, respiratory, cardiovascular, endocrinologic, neurologic or immunologic disease; Clinically significant abnormal 12-lead ECG findings; Cardiac MRI T2* <10ms; Myocardial infarction, cardiac arrest or cardiac failure within 1 year before screening/baseline visit; Unable to undergo MRI Presence of metallic objects such as artificial joints, inner ear (cochlear) implants, brain aneurysm clips, pacemakers, and metallic foreign bodies in the eye or other body areas that would prevent use of MRI imaging", "candidate_expression": "((12-lead ECG) AND (Cardiac MRI T2* <10ms) AND (Diamond Blackfan anemia) AND (LIC Baseline >30 mg/g) AND (MRI) AND (MRI measured by) AND (Myelodysplastic syndrome (MDS)) AND (Myocardial infarction) AND (Presence of metallic objects such as artificial joints, inner ear (cochlear) implants, brain aneurysm clips, pacemakers, and metallic foreign bodies in the eye or other body areas that would prevent use of MRI imaging) AND (Primary bone marrow failure) AND (Thalassemia syndromes) AND (Unable or unwilling to undergo a 7 day washout period if currently being treated with deferiprone or deferoxamine or deferasirox) AND (Unable to undergo) AND (cardiac arrest) AND (cardiac failure) AND (cardiovascular disease) AND (creatinine levels >2 times upper limit of normal at screening) AND (deferiprone) AND (deferoxamine) AND (discontinuation of treatment) AND (endocrinologic disease) AND (findings Clinically significant abnormal) AND (gastro-enterologic disease) AND (hepatic disease) AND (hydroxyurea within 30 days) AND (hypersensitivity) AND (idiosyncratic reaction) AND (immunologic disease) AND (liver function abnormal) AND (malignancy) AND (myelofibrosis) AND (neurologic disease) AND (renal disease) AND (respiratory disease) AND (serum ALT level(s) > 5 times upper limit of normal at screening) AND (unstable illness serious during the past 3 months before screening/baseline visit))"}
{"candidate_id": "LLM07770", "doc_id": "NCT01214096_exc", "case_bucket": "or", "source_criterion": "1. Atrial fibrillation; 2. Subject underwent cardiac pacemaker treatment; 3. Subject underwent metal graft treatment; 4. Claustrophobia; 5. Acute myocardial infarction, cardiac ischemia indicated by 6-minute walk test, hypertrophic cardiomyopathy, constrictive pericarditis, significant valve disease or congenital heart disease, severe pulmonary hypertension; 6. Ischemic heart failure without the revascularization or undergone the revascularization within last 6 months; 7. Subject underwent cardiac surgery or cerebrovascular events within the previous six months; 8. Subjects who plan to have cardiac transplantation; 9. Severe hepatic and renal insufficiency (serum creatinine>2.0 mg /dl, AST or ALT is five times higher than the upper limit of normal range); 10. Subject needs mechanical ventilation; 11. Systolic blood pressure < 90mmHg, or > 160mmHg; 12. Chronic heart failure complicated with acute hemodynamic disturbance or acute decompensation within last 1 month; 13. Mobitz Type II or III° atrial ventricular block，severe ventricular arrhythmia (polymorphic and frequent premature ventricular beats, frequent non-sustained ventricular tachycardia); 14. Serum potassium<3.2mmol/L, or>5.5mmol/L; 15. Female subject is pregnant or plan to become pregnant 16. Childbearing-aged female subject who is unmarried or dose not bear child; 17. Subject with life expectancy less than 6 months as assessed by investigators; 18. Subject participated in any other clinical trial within the previous three months; 19. Subject with previous history of tumor, or current tumor patient, or subject with pre-cancerous disease manifested by pathological examination (such as ductal carcinoma in situ or cervical epithelial dysplasia) 20. Examinations (physical examination, X-ray examination, type-B ultrasonic detection or other methods) reveal that the subject has malignant mass, gland hyperplasia or adenoma with endocrine activity, or impact on heart, or endocrine function (such as pheochromocytoma, thyroid enlargement); 21. The Investigator deemed for whatever reason that the subject is not likely to complete the study or comply with the study procedures (due to administration or any other reason).", "candidate_expression": "((6-minute walk test) AND (< 90mmHg) AND (<3.2mmol/L) AND (> 160mmHg) AND (>2.0 mg /dl) AND (>5.5mmol/L) AND (ALT) AND (AST) AND (Acute myocardial infarction) AND (Atrial fibrillation) AND (Chronic heart failure) AND (Claustrophobia) AND (Examinations) AND (Female) AND (Ischemic heart failure) AND (Mobitz) AND (Serum potassium) AND (The Investigator deemed for whatever reason that the subject is not likely to complete the study or comply with the study procedures (due to administration or any other reason).) AND (Type II or III) AND (X-ray examination) AND (acute decompensation) AND (acute hemodynamic disturbance) AND (adenoma) AND (atrial ventricular block) AND (bear child) AND (blood pressure) AND (cardiac ischemia) AND (cardiac pacemaker) AND (cardiac pacemaker treatment) AND (cardiac surgery) AND (cardiac transplantation) AND (cerebrovascular events) AND (cervical epithelial dysplasia) AND (congenital) AND (congenital heart disease) AND (constrictive pericarditis) AND (current) AND (ductal carcinoma in situ) AND (endocrine activity) AND (female) AND (five times higher than the upper limit of normal range) AND (frequent) AND (gland hyperplasia) AND (hepatic insufficiency) AND (hypertrophic cardiomyopathy) AND (impact on endocrine function) AND (impact on heart) AND (less than 6 months) AND (life expectancy) AND (malignant mass) AND (mechanical ventilation) AND (metal graft) AND (metal graft treatment) AND (non-sustained) AND (not) AND (other methods) AND (pathological examination) AND (pheochromocytoma) AND (physical examination) AND (plan) AND (polymorphic) AND (pre-cancerous disease) AND (pregnant) AND (premature ventricular beats) AND (previous history) AND (renal insufficiency) AND (revascularization) AND (serum creatinine) AND (severe) AND (severe pulmonary hypertension) AND (significant) AND (thyroid enlargement) AND (tumor) AND (type-B ultrasonic detection) AND (unmarried) AND (valve disease) AND (ventricular arrhythmia) AND (ventricular tachycardia) AND (with endocrine activity) AND (within last 1 month) AND (within last 6 months) AND (within the previous six months) AND (without))"}
{"candidate_id": "LLM07771", "doc_id": "NCT03497598_exc", "case_bucket": "or", "source_criterion": "UTIs = 12 within 1 year Pregnancy or Lactation Immune disease Lactose intolerance Urinary tract anomaly Systemic infection Newly started hormone therapy within the last 6 months Antibiotic prophylaxis within the last 6 months a-D-mannose intake within the last month Use of catheters Diabetes mellitus Participation to other studies", "candidate_expression": "((Antibiotic) AND (Antibiotic prophylaxis within the last 6 months) AND (Diabetes mellitus) AND (Immune disease) AND (Lactation) AND (Lactose) AND (Lactose intolerance) AND (Participation to other studies) AND (Pregnancy) AND (Systemic infection) AND (UTIs 12 within 1 year within 1 year) AND (Urinary tract anomaly) AND (a-D-mannose within the last month) AND (catheters) AND (hormone therapy Newly started within the last 6 months) AND (intolerance))"}
{"candidate_id": "LLM07772", "doc_id": "NCT02566928_exc", "case_bucket": "or", "source_criterion": "The patient is unwilling to provide informed consent acutely sick (for example, crying, wheezing, bleeding, screaming or shaken) unable to participate in a discussion about the study", "candidate_expression": "((The patient is unwilling to provide informed consent) AND (acutely sick) AND (bleeding) AND (crying) AND (screaming) AND (shaken) AND (wheezing))"}
{"candidate_id": "LLM07773", "doc_id": "NCT03444142_exc", "case_bucket": "or", "source_criterion": "Women with confirmed or suspected pregnancy Women under lactation and/or puerperium Hypersensibility to ingredients of intervention Physical impossibility for apply the drug Known pancreatic, renal, hepatic, heart or thyroid diseased Hypertension diagnosis Previous treatment for glucose Body Mass Index =39.9 kg/m2 Triglycerides =500 mg/dL Total cholesterol =300 mg/dL Night or rotating shift workers Blood Pressure =140/90 mmHg", "candidate_expression": "((=140/90 mmHg) AND (=300 mg/dL) AND (=39.9 kg/m2) AND (=500 mg/dL) AND (Blood Pressure) AND (Body Mass Index) AND (Hypersensibility) AND (Hypertension) AND (Night shift workers) AND (Previous) AND (Total cholesterol) AND (Triglycerides) AND (Women) AND (confirmed) AND (heart disease) AND (hepatic disease) AND (ingredients of intervention) AND (lactation) AND (pancreatic disease) AND (pregnancy) AND (puerperium) AND (renal disease) AND (rotating shift workers) AND (suspected) AND (thyroid disease) AND (treatment for glucose))"}
{"candidate_id": "LLM07774", "doc_id": "NCT03424993_exc", "case_bucket": "or", "source_criterion": "Abnormal resting ECG Current abnormal blood panel (assessed by comprehensive metabolic panel, lipid panel and complete blood count). Hypertension (currently taking anti-hypertensive medications or resting blood pressure >140/90 mmHg) Medical history of cardiovascular disease, malignant cancer, diabetes or kidney disease Obesity (Body Mass Index > 30) Current pregnancy Unable to provide consent", "candidate_expression": "((Body Mass Index > 30) AND (Hypertension) AND (Obesity) AND (Unable to provide consent) AND (blood panel Current abnormal) AND (complete blood count) AND (lipid panel) AND (metabolic panel) AND (pregnancy Current) AND (resting ECG Abnormal) AND ((anti-hypertensive medications) OR (resting blood pressure >140/90 mmHg)) AND ((cardiovascular disease) OR (diabetes) OR (kidney disease) OR (malignant cancer)))"}
{"candidate_id": "LLM07775", "doc_id": "NCT02589977_inc", "case_bucket": "or", "source_criterion": "estimated glomerular filtration rate (eGFR) > 60 ml/min preserved left ventricular ejection fraction (>= 50%) on echocardiography HEALTHY: normal cardiac structure and function on echocardiography, BP < 140/90 HYPERTENSIVE: history of BP >140/90, 1 or more antihypertensive medications, LV ejection fraction (LVEF) at least 50%, current BP < 160/90 HFpEF: physician-confirmed diagnosis of HF, symptomatic HF, LVEF at least 50%, elevated LV filling pressure by catheterization, echocardiographic criteria or B-type-natriuretic peptide > 100, current BP < 160/90", "candidate_expression": "((1 or more) AND (< 140/90) AND (< 160/90) AND (> 100) AND (> 60 ml/min) AND (>140/90) AND (>= 50%) AND (B-type-natriuretic peptide) AND (BP) AND (HEALTHY) AND (HF) AND (HFpEF) AND (HYPERTENSIVE) AND (LV ejection fraction (LVEF)) AND (LV filling pressure) AND (LVEF) AND (antihypertensive medications) AND (at least 50%) AND (catheterization) AND (current) AND (current BP) AND (echocardiography) AND (elevated) AND (estimated glomerular filtration rate (eGFR)) AND (history) AND (left ventricular ejection fraction) AND (physician-confirmed) AND (preserved) AND (symptomatic) AND ((normal cardiac function) OR (normal cardiac structure)))"}
```
