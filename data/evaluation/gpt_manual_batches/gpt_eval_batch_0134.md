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
{"candidate_id": "LLM03326", "doc_id": "NCT01735955_inc", "case_bucket": "other", "source_criterion": "Patient is currently enrolled in a Novartis-sponsored, Oncology Clinical Development & Medical Affairs study receiving nilotinib and has fulfilled all their requirements in the parent study Patient is currently benefiting from the treatment with nilotinib, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study", "candidate_expression": "((Willingness to comply with scheduled visits) AND (Willingness to comply with treatment plans) AND (Written informed consent prior to enrolling in roll-over study) AND (ability to comply with scheduled visits) AND (compliance with the parent study protocol requirements) AND (enrolled in a Oncology Clinical Development & Medical Affairs study currently Novartis-sponsored) AND (nilotinib) AND (treatment currently))"}
{"candidate_id": "LLM03327", "doc_id": "NCT02488057_inc", "case_bucket": "other", "source_criterion": "Mexican-american Female BMI 30-42 willingness to complete protocol pre-diabetic English or Spanish literate", "candidate_expression": "((BMI 30-42) AND (Female) AND (Mexican-american) AND (pre-diabetic) AND (willingness to complete protocol))"}
{"candidate_id": "LLM03328", "doc_id": "NCT02511574_inc", "case_bucket": "other", "source_criterion": "gestational age between 20 weeks and 23 weeks and 6 days singleton pregnancies", "candidate_expression": "((between 20 weeks and 23 weeks and 6 days) AND (gestational age) AND (singleton pregnancies))"}
{"candidate_id": "LLM03329", "doc_id": "NCT02375295_inc", "case_bucket": "or", "source_criterion": "Male or Female. No age restriction. Diagnosed with an infection related stone. Medically fit for definitive surgical management of stone. Life expectancy greater than one year. Stone free after definitive surgical therapy defined as fragments less than 3mm.", "candidate_expression": "((Female) AND (Life expectancy) AND (Male) AND (Medically fit for) AND (Stone) AND (after definitive surgical therapy) AND (definitive surgical management) AND (definitive surgical therapy) AND (fragments less than 3mm) AND (free) AND (greater than one year) AND (infection related) AND (stone))"}
{"candidate_id": "LLM03330", "doc_id": "NCT02671318_inc", "case_bucket": "or", "source_criterion": "Adult kidney transplant recipients > 18 y.o. Kidney Transplant recipients, after the first episode of cytomegalovirus infection, using the current immunosuppressive regimen: azathioprine or mycophenolate, tacrolimus and prednisone.", "candidate_expression": "((Adult) AND (cytomegalovirus infection) AND (immunosuppressive regimen) AND (kidney transplant) AND (y.o. > 18) AND ((azathioprine) OR (mycophenolate) OR (prednisone) OR (tacrolimus)))"}
{"candidate_id": "LLM03331", "doc_id": "NCT03059069_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetic patients Age = 50 Glycemic control: HbA1c = 10.0% 10 = Beck Depression Inventory (BDI) <30 points Participants who can undergo contraception in case of being in childbearing period Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent", "candidate_expression": "((Age = 50) AND (Beck Depression Inventory (BDI) <30 points) AND (HbA1c = 10.0%) AND (Participants who can undergo contraception in case of being in childbearing period) AND (Type 2 diabetic) AND (Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent))"}
{"candidate_id": "LLM03332", "doc_id": "NCT02804126_inc", "case_bucket": "other", "source_criterion": "obtained consent singleton pregnancy subarachnoid anaesthesia", "candidate_expression": "((pregnancy) AND (singleton) AND (subarachnoid anaesthesia))"}
{"candidate_id": "LLM03333", "doc_id": "NCT02892968_exc", "case_bucket": "or", "source_criterion": "ED physicians who work casually (less than 0.25 Full Time Equivalent) ED Physicians who are routinely using U/S guided RA for hip fracture patients, or decline participation in the trial. Patients' age less than 65 years; Patients who are delirious on initial assessment by ED physician or severe dementia Patients with communication problems (critically ill, unconscious, language barrier despite use of secure telephone-based translation service) Patients with allergies to narcotics or local anesthetic; or anticoagulant use (e.g. warfarin, dabigatran, rivaroxaban). Patients with hip fractures not requiring surgery (e.g. greater trochanter avulsion) will also be excluded.", "candidate_expression": "((age less than 65 years) AND (allergies) AND (anticoagulant) AND (communication problems) AND (critically ill) AND (dabigatran) AND (delirious on initial assessment) AND (dementia severe) AND (greater trochanter avulsion) AND (hip fractures requiring surgery) AND (language barrier) AND (local anesthetic) AND (narcotics) AND (rivaroxaban) AND (surgery) AND (unconscious) AND (warfarin))"}
{"candidate_id": "LLM03334", "doc_id": "NCT02590822_inc", "case_bucket": "or", "source_criterion": "Capacity to provide informed consent before any trial-related activities Established T2DM (=3months) HbA1c = 9% if on triple therapy or = 10% on diet & exercise or monotherapy or dual therapy Current glucose lowering therapy either mono, dual or triple of any combination of metformin, sulphonylurea, DPP-IV inhibitor, GLP-1 therapy or an SGLT2 +/- diet and exercise Poorly managed diet controlled diabetes (with HbA1c > 6.5% , not currently taking any glucose lowering therapy, meeting BMI inclusion range) Body mass index > 30Kg/m2 or > 27.5 Kg/m2 (South Asian), Diagnosis of T2DM before the age of 60 years of age Age =18 and = 65 years", "candidate_expression": "((= 10%) AND (= 9%) AND (=18 and = 65 years) AND (=3months) AND (> 27.5 Kg/m2) AND (> 30Kg/m2) AND (> 6.5%) AND (Age) AND (Body mass index) AND (Capacity to provide informed consent before any trial-related activities) AND (DPP-IV inhibitor,) AND (GLP-1 therapy) AND (HbA1c) AND (SGLT2) AND (T2DM) AND (age) AND (before 60 years of age) AND (diabetes) AND (diet) AND (exercise) AND (glucose lowering therapy) AND (metformin) AND (not) AND (sulphonylurea))"}
{"candidate_id": "LLM03335", "doc_id": "NCT02531724_exc", "case_bucket": "other", "source_criterion": "Ongoing treatment with inotropic drugs (not norepinephrine) Central venous oxygen saturation (ScvO2) < 60% despite optimization of hematocrit and volume status Need of renal replacement therapy Ongoing bleeding Patient or next of kin does not consent with study participation", "candidate_expression": "((< 60%) AND (Central venous oxygen saturation (ScvO2)) AND (Need) AND (Ongoing) AND (Patient or next of kin does not consent with study participation) AND (bleeding) AND (despite) AND (inotropic drugs) AND (norepinephrine) AND (not) AND (optimization of hematocrit) AND (renal replacement therapy) AND (treatment) AND (volume status))"}
{"candidate_id": "LLM03336", "doc_id": "NCT03151603_exc", "case_bucket": "or", "source_criterion": "signs of complicated UTI (e. g. temperature > 38°C, loin tenderness) conditions that may lead to complicated infections (i.e. renal diseases, patients with urinary catheter) pregnancy/ breastfeeding current self-medication with UU preparations e.g. z.B. Cystinol®, Uvalysat®, Arctuvan® antibiotic use in the last 7 days previous UTI in the past 2 weeks history of pyelonephritis contraindications for trial drugs serious diseases inability to understand trial Information current participation in another clinical trial or participation in another clinical trial within the last 4 weeks", "candidate_expression": "((> 38°C) AND (Arctuvan®) AND (UTI) AND (UU preparations) AND (Uvalysat®) AND (antibiotic) AND (complicated UTI) AND (complicated infections) AND (conditions) AND (contraindications for) AND (diseases) AND (drugs) AND (inability to understand trial Information) AND (last 7 days) AND (loin tenderness) AND (past 2 weeks) AND (patients) AND (pregnancy/ breastfeeding) AND (pyelonephritis) AND (renal diseases) AND (self-medication) AND (serious) AND (temperature) AND (trial) AND (urinary catheter) AND (z.B. Cystinol®))"}
{"candidate_id": "LLM03337", "doc_id": "NCT02567214_exc", "case_bucket": "or", "source_criterion": "Respiratory exacerbation within the 2 months preceding the study Current diagnostic of asthma Significant O2 desaturation (SpO2 < 85%) at rest or during exercise Presence of another pathology that could influence exercise tolerance Use of home oxygen", "candidate_expression": "((< 85%) AND (Current) AND (O2 desaturation) AND (Respiratory exacerbation) AND (Significant) AND (SpO2) AND (another) AND (at rest) AND (diagnostic of asthma) AND (during exercise) AND (home oxygen) AND (influence exercise tolerance) AND (pathology) AND (the study) AND (within the 2 months preceding the study))"}
{"candidate_id": "LLM03338", "doc_id": "NCT02573597_inc", "case_bucket": "or", "source_criterion": "ASA I & II, Nulliparous and Multiparous, Spontaneous/Induced/Augmented Labor, Early active labor (cervix <5 cm (if known)), Pain (VPS) > 3, 18-45 years of age", "candidate_expression": "((ASA I & II) AND (Early active labor) AND (Multiparous) AND (Nulliparous) AND (Pain (VPS) > 3) AND (age 18-45 years) AND (cervix <5 cm) AND ((Augmented Labor) OR (Induced Labor) OR (Spontaneous Labor)))"}
{"candidate_id": "LLM03339", "doc_id": "NCT03337581_exc", "case_bucket": "or", "source_criterion": "allergic to dexmedetomidine, similar active ingredients or excipients G-6-PD deficiency a history of arrhythmia, bronchial and cardiovascular diseases, abnormal liver function and so on a history of use of alpha 2 receptor agonists or antagonists.", "candidate_expression": "((G-6-PD deficiency) AND (abnormal liver function) AND (allergic) AND (alpha 2 receptor agonists) AND (alpha 2 receptor antagonists) AND (arrhythmia) AND (bronchial diseases) AND (cardiovascular diseases) AND (dexmedetomidine) AND (excipients) AND (similar active ingredients))"}
{"candidate_id": "LLM03340", "doc_id": "NCT02959801_exc", "case_bucket": "or", "source_criterion": "presence of subacute or chronic DVT more than 21 days in duration, inability to lie in the prone position required for intervention, terminal systemic disease requiring palliative treatment, active bleeding (from a gastric/duodenal ulcer or the cerebrovascular system), a haemorrhagic stroke within the previous year, an impaired bleeding-clotting profile, and any haemophilic disorder, or pregnancy.", "candidate_expression": "((active) AND (more than 21 days in duration) AND (palliative treatment) AND (requiring) AND (within the previous year) AND ((cerebrovascular system) OR (duodenal ulcer) OR (gastric ulcer)) AND ((chronic) OR (subacute)) AND ((DVT) OR (bleeding) OR (haemophilic disorder) OR (haemorrhagic stroke) OR (impaired bleeding-clotting profile) OR (inability to lie in the prone position) OR (pregnancy) OR (terminal systemic disease)))"}
{"candidate_id": "LLM03341", "doc_id": "NCT02749617_exc", "case_bucket": "or", "source_criterion": "Concomitant antiplatelet or anticoagulant use Calculated creatinine clearance < 30 mL/min by Cockcroft-Gault formula Alanine aminotransferase (ALT) or aspartate aminotransferase (AST) > 3 times upper limit of normal (ULN) Total bilirubin > 2 x ULN Thrombocytopenia < 50 x 10 gigalitres (Gl) High bleeding risk or spontaneously prolonged prothrombin time or activated partial thromboplastin time > 1.5 x ULN Body weight <50 or >120 kg Concomitant use of CYP3A4 or p-glycoprotein inducers or inhibitors Use of Ginkgo biloba or St. John's Wort within 14 days before first dose of study drug Dexamethasone use within last 3 months Women of Childbearing potential without proper contraceptive measures, pregnancy or breast feeding Life expectancy less than 3 months Inability to swallow or issues with malabsorption Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion", "candidate_expression": "((< 30 mL/min) AND (< 50 x 10 gigalitres (Gl)) AND (> 1.5 x ULN) AND (> 2 x ULN) AND (> 3 times upper limit of normal (ULN)) AND (Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion) AND (Body weight) AND (Calculated creatinine clearance) AND (Cockcroft-Gault formula) AND (Concomitant) AND (Dexamethasone) AND (Life expectancy) AND (Thrombocytopenia) AND (Total bilirubin) AND (Women) AND (contraceptive measures) AND (first dose) AND (first dose of study drug) AND (less than 3 months) AND (spontaneously) AND (study drug) AND (within 14 days before first dose of study drug) AND (within last 3 months) AND (without) AND ((High bleeding risk) OR (activated partial thromboplastin time) OR (prolonged prothrombin time)) AND ((anticoagulant) OR (antiplatelet)) AND ((<50 kg) OR (>120 kg)) AND ((CYP3A4) OR (p-glycoprotein inducers) OR (p-glycoprotein inhibitors)) AND ((Ginkgo biloba) OR (St. John's Wort)) AND ((Childbearing potential) OR (breast feeding) OR (pregnancy)) AND ((Inability to swallow) OR (issues with malabsorption)) AND ((Alanine aminotransferase (ALT)) OR (aspartate aminotransferase (AST))))"}
{"candidate_id": "LLM03342", "doc_id": "NCT03624517_exc", "case_bucket": "or", "source_criterion": "Known upper gastrointestinal malignancy Bleeding from gastric varices, with or without esophageal varices Use of any other endoscopic method to stop GI bleeding beyond endoscopic band ligation Variceal bleeding in the last 90 days History of transjugular, intrahepatic, portosystemic shunt (TIPS) or vascular decompression surgery Pregnant females Incarcerated individuals Myocardial infarct, cerebrovascular accident, sepsis, respiratory failure, or severe intercurrent illness within the previous 6 weeks Non-cirrhotic portal hypertension causing esophageal varices Known or suspected allergy to octreotide", "candidate_expression": "((Bleeding) AND (GI bleeding) AND (History) AND (Incarcerated individuals) AND (Known) AND (Myocardial infarct) AND (Non-cirrhotic portal hypertension) AND (Pregnant) AND (Variceal bleeding) AND (allergy) AND (any other) AND (cerebrovascular accident) AND (endoscopic band ligation) AND (endoscopic method) AND (esophageal varices) AND (females) AND (gastric varices) AND (in the last 90 days) AND (intercurrent illness) AND (octreotide) AND (respiratory failure) AND (sepsis) AND (severe) AND (suspected) AND (transjugular, intrahepatic, portosystemic shunt (TIPS)) AND (upper gastrointestinal malignancy) AND (vascular decompression surgery) AND (within the previous 6 weeks))"}
{"candidate_id": "LLM03343", "doc_id": "NCT02872935_inc", "case_bucket": "other", "source_criterion": "Pregnant American Society of Anesthesiologists risk classification I and II Age > 18 years Non-laboring Patients with elective cesarean sections", "candidate_expression": "((> 18 years) AND (Age) AND (American Society of Anesthesiologists risk classification) AND (I and II) AND (Non-laboring) AND (Pregnant) AND (cesarean sections) AND (elective))"}
{"candidate_id": "LLM03344", "doc_id": "NCT03536520_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((Allergy) AND (acetazolamide) AND (altitude exposure) AND (cardiovascular disease) AND (disease other) AND (hypoxia) AND (respiratory disease) AND (sulfonamides) AND (tolerance relevant for) AND (treatment regular))"}
{"candidate_id": "LLM03345", "doc_id": "NCT03297125_exc", "case_bucket": "or", "source_criterion": "Optune compliance < 75%; they would be excluded from the final analyses. History of craniectomy or significant skull defect (contraindication to Optune). Active implantable medical device (i.e. DBS, spinal cord stimulator, pacemaker, defibrillator, vagus nerve stimulator, programmable shunt). Karnofsky Performance Status (KPS) < 60.", "candidate_expression": "((KPS) AND (Karnofsky Performance Status < 60) AND (Optune) AND (Optune compliance < 75%) AND (contraindication) AND (implantable medical device Active) AND ((DBS) OR (defibrillator) OR (pacemaker) OR (programmable shunt) OR (spinal cord stimulator) OR (vagus nerve stimulator)) AND ((craniectomy) OR (skull defect significant)))"}
{"candidate_id": "LLM03346", "doc_id": "NCT01312012_inc", "case_bucket": "other", "source_criterion": "pregnant women in 30 to 32 weeks of gestation, with positive HBsAg and HBeAg,serum viral load above 8log10 copies per mL", "candidate_expression": "((30 to 32 weeks) AND (HBeAg) AND (HBsAg) AND (above 8log10 copies per mL) AND (gestation) AND (positive) AND (pregnant) AND (serum viral load) AND (women))"}
{"candidate_id": "LLM03347", "doc_id": "NCT02656394_inc", "case_bucket": "or", "source_criterion": "1. Male or female of any race, at least 18 years of age at Visit 1 Screening. 2. Has provided verbal and written informed consent. 3. Be able and willing to follow instructions, including participation in all study assessments and visits. 4. Currently being treated for glaucoma using at least two medications, and be willing to continue on the same regime. 5. Suffers from at least two of the symptoms in the GLIA™ Glaucoma Medication Ocular Side Effect Symptoms Questionnaire at a severity of 2 (moderate) or more. 6. If a woman of childbearing potential, have a negative urine pregnancy test at Visit 1 and be using an adequate method of birth control throughout the study period.", "candidate_expression": "((Be able and willing to follow instructions, including participation in all study assessments and visits.) AND (GLIA™ Glaucoma Medication Ocular Side Effect Symptoms Questionnaire severity of 2 or more moderate) AND (Has provided verbal and written informed consent.) AND (adequate) AND (age at least 18 years at Visit 1 Screening) AND (childbearing potential) AND (glaucoma) AND (medications at least two) AND (method of birth control adequate throughout the study period) AND (symptoms at least two) AND (treated Currently) AND (urine pregnancy test negative at Visit 1) AND (woman) AND ((Male) OR (female)))"}
{"candidate_id": "LLM03348", "doc_id": "NCT02558504_exc", "case_bucket": "or", "source_criterion": "Aged under 18, Lack of informed consent signed, Radiofrequency treatment history, on going neoplastic history with a short prognosis, Concomitant participation in another clinical study Contraindication to general anesthesia, Patient with an esophageal location of scleroderma Presence of a cardiac pacemaker or stimulator Pregnant women or likely to be in the absence of effective contraception, Esophageal stenosis preventing the passage of an endoscope, Histology other than glandular neoplasia, History of or current history of esophageal cancer invading the submucosal layer of the esophagus or more, Surgical treatment history (except anti-reflux treatment) or esophageal radiotherapy, previous esophageal treatment by another method ablation: photodynamic therapy, argon plasma coagulation, laser, .... Esophageal varices observed in endoscopy, Coagulopathy or taking anticoagulants responsible an INR> 1.3 or a platelet count <75,000 per microL, Life expectancy of less than 3 years, due to intercurrent disease, especially neoplastic, Liver cirrhosis (Child-Pugh all stages) Respiratory failure: Renal failure (Cl Cr < 60 mL /min /1,73m), Heart attack within the last six months or progressive coronary artery disease, Severe distal arteriopathie > stage II of Leriche and Fontaine", "candidate_expression": "((< 60 mL /min /1,73m) AND (<75,000 per microL) AND (> 1.3) AND (> II) AND (Aged) AND (Child-Pugh) AND (Cl Cr) AND (Concomitant) AND (Contraindication) AND (Esophageal stenosis) AND (Esophageal varices) AND (Histology) AND (Lack of) AND (Liver cirrhosis) AND (Radiofrequency treatment) AND (Renal failure) AND (Respiratory failure) AND (Severe) AND (ablation) AND (all stages) AND (another method) AND (anti-reflux treatment) AND (distal arteriopathie) AND (endoscope) AND (endoscopy) AND (esophageal cancer) AND (esophageal location) AND (esophageal treatment) AND (except) AND (general anesthesia) AND (glandular neoplasia) AND (history) AND (in the absence of effective contraception) AND (informed consent signed) AND (intercurrent disease) AND (invading the submucosal layer of the esophagus) AND (likely to be) AND (neoplastic) AND (on going) AND (other than) AND (participation in another clinical study) AND (passage of an endoscope) AND (preventing the) AND (previous) AND (prognosis) AND (scleroderma) AND (short) AND (stage of Leriche and Fontaine) AND (the last six months) AND (under 18) AND (within the last six months) AND (women) AND ((cardiac pacemaker) OR (cardiac stimulator)) AND ((Pregnant)) AND ((History) OR (current)) AND ((Surgical treatment) OR (esophageal radiotherapy)) AND ((argon plasma coagulation) OR (laser) OR (photodynamic therapy)) AND ((Coagulopathy) OR (anticoagulants)) AND ((INR) OR (platelet count)) AND ((Life expectancy) OR (less than 3 years)) AND ((Heart attack) OR (progressive coronary artery disease)))"}
{"candidate_id": "LLM03349", "doc_id": "NCT00236340_inc", "case_bucket": "or", "source_criterion": "Pregnant women with abdomen discumfort and ultrasound diagnosis of polyhydramnios (AFI>25cm) Single or twin pregnancies", "candidate_expression": "((AFI >25cm) AND (Pregnant) AND (abdomen discumfort) AND (polyhydramnios) AND (pregnancies) AND (ultrasound diagnosis) AND (women) AND ((Single) OR (twin)))"}
{"candidate_id": "LLM03350", "doc_id": "NCT03407625_inc", "case_bucket": "or", "source_criterion": "37 weeks gestation or greater Living, singleton fetus No major fetal malformations Cephalic presentation No prior uterine scar Intact fetal membranes Qualifies for prostaglandin administration according to current Parkland protocol Have a cervical dilation of 2 centimeters or less, measured at the level of the internal os Have an indication for induction or attempted induction of labor according to Parkland protocol", "candidate_expression": "((2 centimeters or less) AND (37 weeks greater) AND (Cephalic presentation) AND (Intact) AND (Living) AND (No) AND (Parkland protocol) AND (attempted) AND (cervical dilation) AND (fetal membranes) AND (gestation) AND (indication) AND (internal os) AND (major fetal malformations) AND (prostaglandin administration) AND (singleton fetus) AND (uterine scar) AND ((induction) OR (induction of labor)))"}
```
