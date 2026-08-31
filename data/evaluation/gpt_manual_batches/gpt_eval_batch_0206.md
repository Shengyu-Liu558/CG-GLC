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
{"candidate_id": "LLM05126", "doc_id": "NCT03064568_exc", "case_bucket": "or", "source_criterion": "Patient with contraindication to misoprostol or vasopressin, personal history or cardiac or pulmonary disease, history of prior myomectomy", "candidate_expression": "((contraindication) AND (disease cardiac) AND (history) AND (misoprostol) AND (myomectomy) AND (personal history) AND (prior) AND (pulmonary disease) AND (vasopressin))"}
{"candidate_id": "LLM05127", "doc_id": "NCT02053246_exc", "case_bucket": "or", "source_criterion": "Other causes of heart failure other than diastolic dysfunction, such as restrictive cardiomyopathy or infiltrative cardiomyopathy Women who are pregnant or nursing Liver cirrhosis, Primary valvular disease Acute coronary syndrome Causes of PH other than that of heart failure, such as: chronic thromboembolic PH, sickle-cell disease, or sarcoidosis Severe bradycardia or greater than 1st degree heart block Decompensated heart failure Current use of a third generation beta-blocker (nebivolol, carvedilol, or labetalol) or high dose of any beta-blockers (greater than 100 mg daily of metoprolol, or equivalent)", "candidate_expression": "((Acute coronary syndrome) AND (Causes of PH) AND (Decompensated) AND (Liver cirrhosis) AND (Primary valvular disease) AND (Severe) AND (Women) AND (any beta-blockers) AND (diastolic dysfunction) AND (greater than 100 mg daily) AND (greater than 1st degree) AND (heart failure) AND (high dose) AND (metoprolol) AND (other than) AND (third generation beta-blocker) AND ((nursing) OR (pregnant)) AND ((chronic thromboembolic PH) OR (sarcoidosis) OR (sickle-cell disease)) AND ((bradycardia) OR (heart block)) AND ((carvedilol) OR (labetalol) OR (nebivolol)) AND ((infiltrative cardiomyopathy) OR (restrictive cardiomyopathy)))"}
{"candidate_id": "LLM05128", "doc_id": "NCT03446885_exc", "case_bucket": "or", "source_criterion": "any medical condition that would contraindicate use of stimulant medication any prior adverse response to lisdexamfetamine dimesylate or other stimulant medication use of concurrent,non-stimulant psychoactive medication diagnosis of schizophrenia or presence of thought disorder symptoms autism spectrum disorder", "candidate_expression": "((adverse response) AND (autism spectrum disorder) AND (concurrent) AND (contraindicate) AND (lisdexamfetamine dimesylate) AND (medical condition) AND (non-stimulant psychoactive medication) AND (other) AND (prior) AND (schizophrenia) AND (stimulant medication) AND (symptoms) AND (thought disorder))"}
{"candidate_id": "LLM05129", "doc_id": "NCT02782702_exc", "case_bucket": "or", "source_criterion": "Hypersensibility to toxin or excipients Myastheny Deglutition's problems Past medical history of dysphagia or aspiration pneumonia Pregnancy (positive B-HCG test performed a maxima 72h before) or breastfeeding Mental , physical incapacity to fill in the questionnaires Guardianship patients Skin infections at the inclusion visit Application in the last 7 days at the site of injection of local treatments (apart emollients or antiseptics) or injections of botulism toxin or dynamic phototherapy or laser in the last 6 months. Systemic treatment with aminosides in the last 15 days Inclusion in another study in the last 2 months.", "candidate_expression": "((Application of local treatments in the last 7 days) AND (B-HCG test positive a maxima 72h before) AND (Deglutition's problems) AND (Hypersensibility) AND (Inclusion in another study) AND (Inclusion in another study in the last 2 months) AND (Mental incapacity) AND (Myastheny) AND (Pregnancy) AND (Skin infections at the inclusion visit) AND (Systemic treatment in the last 15 days) AND (aminosides) AND (antiseptics) AND (aspiration pneumonia) AND (botulism toxin) AND (breastfeeding) AND (dynamic phototherapy) AND (dysphagia) AND (emollients) AND (excipients) AND (fill in the questionnaires) AND (inclusion visit) AND (injections) AND (laser) AND (physical incapacity) AND (toxin))"}
{"candidate_id": "LLM05130", "doc_id": "NCT03340740_inc", "case_bucket": "other", "source_criterion": "History of allergic rhinitis Wheezing", "candidate_expression": "((Wheezing) AND (allergic rhinitis))"}
{"candidate_id": "LLM05131", "doc_id": "NCT02997215_exc", "case_bucket": "or", "source_criterion": "Open surgery; Patients allergic to lidocaine or other local anesthetics; Drug abuser.", "candidate_expression": "((Drug abuser) AND (Open surgery) AND (allergic) AND (other) AND ((lidocaine) OR (local anesthetics)))"}
{"candidate_id": "LLM05132", "doc_id": "NCT02041299_inc", "case_bucket": "or", "source_criterion": "Male or female = 2 years of age; Have sickle cell disease (confirmed by Hb electrophoresis or more specific tests) or other conditions with iron overload from repeated blood transfusions (see exclusion criteria for exceptions); Baseline LIC >7 mg/g dw (measured by MRI); Patients who have received no less than 20 transfusions of RBCs; Patients who have received at least 1 transfusion per year in the last 2 years and who are expected to have a continuing requirement (based on Investigator's judgement) during the duration of the trial", "candidate_expression": "((= 2 years) AND (>7 mg/g) AND (Baseline LIC) AND (MRI) AND (age) AND (at least 1 per year) AND (blood transfusions) AND (during the duration of the trial) AND (expected to have a continuing requirement) AND (in the last 2 years) AND (no less than 20) AND (repeated) AND (transfusion) AND (transfusions of RBCs) AND ((Male) OR (female)) AND ((other conditions with iron overload) OR (sickle cell disease)) AND ((Hb electrophoresis) OR (more specific tests)))"}
{"candidate_id": "LLM05133", "doc_id": "NCT02833116_exc", "case_bucket": "or", "source_criterion": "Patients with high intracranial pressure. Patients with Multiple Sclerosis. Patients with Guillain-Barré syndrome radiculopathy of vascular origin. Patients with previous lumbar surgery. Patients pregnant or lactating. Patients with allergy or intolerance to any of the drugs used. Patients with severe cognitive impairment. Patients with intrathecal injectio radiculalgia. Patients with poorly controlled major psychiatric pathology. Patients with type I diabetes or poorly controlled type II diabetes (Hb1Ac>8.5). Patients with glaucoma. Patients with caudal equine syndrome. Patients with pre-treatment with steroid injections/or local anesthetics. Patients with central canal stenosis. patients with chronic treatment with oral corticosteroids without stabilized pattern.", "candidate_expression": "((>8.5) AND (Guillain-Barré syndrome radiculopathy) AND (Hb1Ac) AND (Multiple Sclerosis) AND (Patients pregnant or lactating) AND (caudal equine syndrome) AND (central canal stenosis) AND (cognitive impairment) AND (drugs) AND (glaucoma) AND (high) AND (intracranial pressure) AND (intrathecal injectio radiculalgia) AND (lumbar surgery.) AND (major) AND (oral corticosteroids) AND (poorly controlled) AND (psychiatric pathology) AND (severe) AND (vascular) AND ((type I diabetes) OR (type II diabetes)) AND ((local anesthetics) OR (steroid injections)) AND ((allergy) OR (intolerance)))"}
{"candidate_id": "LLM05134", "doc_id": "NCT02607163_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05135", "doc_id": "NCT00962364_inc", "case_bucket": "or", "source_criterion": "acute myocardial infarction or ischemic cardiomyopathy with or without previous myocardial infarction or dilated cardiomyopathy due to valvular heart disease, hypertensive heart disease, history of myocarditis (no active myocardial infection present)", "candidate_expression": "((acute myocardial infarction) AND (dilated cardiomyopathy) AND (hypertensive heart disease) AND (ischemic cardiomyopathy) AND (myocardial infarction previous) AND (myocarditis history) AND (valvular heart disease) AND NOT (myocardial infection active))"}
{"candidate_id": "LLM05136", "doc_id": "NCT00965900_exc", "case_bucket": "or", "source_criterion": "Patients with systolic blood pressure <100 mmHg or basal heart rate <60/min Portal vein thrombosis Uncontrolled ascites or hepatic encephalopathy Severe coagulation disorder: prothrombin time <40% (or INR >1.7) or platelet count <30,000/mm3 Medium or large sized gastric or duodenal varices Coexisting malignancy Severe cardiovascular disorder, renal failure, peritonitis, sepsis Severe erosive esophagitis, severe esophageal stricture, active gastric or duodenal ulcer Contraindication to beta-blocker Pregnancy Refusal to give consent to participate in the trial", "candidate_expression": "((<100 mmHg) AND (<30,000/mm3) AND (<40%) AND (<60/min) AND (>1.7) AND (Coexisting) AND (Contraindication) AND (INR) AND (Medium) AND (Portal vein thrombosis) AND (Pregnancy) AND (Refusal to give consent to participate in the trial) AND (Severe) AND (Uncontrolled) AND (active) AND (ascites) AND (basal) AND (beta-blocker) AND (cardiovascular disorder) AND (coagulation disorder) AND (duodenal ulcer) AND (duodenal varices) AND (erosive esophagitis) AND (esophageal stricture) AND (gastric c) AND (gastric ulcer) AND (heart rate) AND (hepatic encephalopathy) AND (large) AND (malignancy) AND (peritonitis) AND (platelet count) AND (prothrombin time) AND (renal failure) AND (sepsis) AND (severe) AND (systolic blood pressure))"}
{"candidate_id": "LLM05137", "doc_id": "NCT02732080_inc", "case_bucket": "or", "source_criterion": "Patients presenting with ST-elevation acute myocardial infarction (STEMI) within 12 hours of their symptom onset in whom TIMI-3 flow was established in infarct related artery (IRA) after balloon angioplasty or thrombectomy.", "candidate_expression": "((ST-elevation acute myocardial infarction (STEMI) within 12 hours of their symptom onset) AND (TIMI-3 flow was established infarct related artery (IRA) after balloon angioplasty or thrombectomy) AND (balloon angioplasty) AND (thrombectomy))"}
{"candidate_id": "LLM05138", "doc_id": "NCT02284737_inc", "case_bucket": "or", "source_criterion": "Provision of informed consent prior to any study specific procedures; Men and women 18 years and older; Group I PAH, defined as a mPAP=25mmHg, PCWP<15mmHg and PVR[The PVR =(mPAP-PCWP)/CO]>3.0 Woods unit.", "candidate_expression": "(((mPAP-PCWP)/CO) AND (Men) AND (PAH Group I) AND (PCWP <15mmHg) AND (PVR) AND (mPAP =25mmHg) AND (women) AND (years 18 years and older))"}
{"candidate_id": "LLM05139", "doc_id": "NCT01717911_exc", "case_bucket": "or", "source_criterion": "Previous treated with anti-diabetic medication Pregnant or nursing women. Impaired liver function (ALT > 120 U/L) Impaired renal function (Serum creatinine >1.5 mg/dL in male, >1.4 mg/dL in female ) Recently suffered from MI or CVA. Patients are acute intercurrent illness. 2-hour C-peptide level < 1.8 ng/mL.", "candidate_expression": "((2-hour C-peptide level < 1.8 ng/mL) AND (ALT > 120 U/L) AND (Impaired liver function) AND (Impaired renal function) AND (Serum creatinine) AND (acute intercurrent illness) AND (anti-diabetic medication) AND (treated Previous) AND (women) AND ((female >1.4 mg/dL) OR (male >1.5 mg/dL)) AND ((CVA) OR (MI)) AND ((Pregnant) OR (nursing)))"}
{"candidate_id": "LLM05140", "doc_id": "NCT01217671_exc", "case_bucket": "or", "source_criterion": "FEV1 >= 80% or FEV1 < 20% of predicted value post-bronchodilator. FEV1/SVC>=70% History of lung transplant. Any lung surgery within the past two years. On any thoracic surgery waiting list. End of last exacerbation less than 6 weeks prior to screening/re-screening visit. Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor. Active smoking during the last 12 months from screening date. Pregnancy or lactation. Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator. Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol. Evidence of ongoing viral infection with HCV, HBV and/or HIV. Evidence of alcohol abuse or history of alcohol abuse or illegal and/or legally prescribed drugs. IgA Deficiency History of life threatening allergy, anaphylactic reaction, or systemic response to human plasma derived products. Participation in another clinical trial within 30 days prior to baseline visit. Inability to attend scheduled clinic visits and/or comply with the study protocol. Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.", "candidate_expression": "((< 20% of predicted value) AND (>= 80%) AND (>=70%) AND (AAT deficiency) AND (Active) AND (Active smoking) AND (Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.) AND (Clinically significant) AND (Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor.) AND (FEV1) AND (FEV1/SVC) AND (HBV) AND (HCV) AND (HIV) AND (History) AND (IgA Deficiency) AND (Inability to attend scheduled clinic visits and/or comply with the study protocol.) AND (Pregnancy) AND (Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol.) AND (Woman) AND (Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator.) AND (abuse illegal drugs) AND (abuse legally prescribed drugs) AND (adequate) AND (alcohol abuse) AND (anaphylactic reaction) AND (bronchodilator) AND (cardiac) AND (child-bearing potential) AND (contraception) AND (deemed reliable by the investigator) AND (during the last 12 months from screening date) AND (endocrine) AND (exacerbation) AND (except for) AND (hematological) AND (hepatic) AND (history) AND (human plasma derived) AND (immunological) AND (impair the patient's ability to give informed consent) AND (in the opinion of the investigator) AND (intercurrent illnesses) AND (lactation) AND (less than 6 weeks prior to screening/re-screening visit) AND (life threatening) AND (life threatening allergy) AND (liver disease) AND (lung surgery) AND (lung transplant) AND (mental disorder) AND (neoplastic) AND (neurological) AND (not) AND (ongoing) AND (other) AND (other medical disorder) AND (post-bronchodilator) AND (products) AND (psychiatric disorder) AND (renal) AND (respiratory disease) AND (screening date) AND (screening/re-screening visit) AND (secondary to AAT deficiency) AND (skeletal) AND (systemic response to human plasma derived products) AND (thoracic surgery) AND (thoracic surgery waiting list) AND (viral infection) AND (within the past two years))"}
{"candidate_id": "LLM05141", "doc_id": "NCT00312429_exc", "case_bucket": "or", "source_criterion": "Undergoing Interleukin-2 (IL-2) therapy within 8 weeks of study entry Diagnosed with a medical or psychiatric illness that may interfere with study participation Pregnant", "candidate_expression": "((Interleukin-2 (IL-2) therapy within 8 weeks of study entry) AND (Pregnant) AND ((illness that may interfere with study participation medical) OR (psychiatric illness that may interfere with study participation)))"}
{"candidate_id": "LLM05142", "doc_id": "NCT02765217_inc", "case_bucket": "or", "source_criterion": "Children receiving amoxicilline-clavulanic acid (50-90 mg/kg/day, twice daily) due to acute otitis media or acute sinusitis", "candidate_expression": "((Children) AND (acute otitis media) AND (acute sinusitis) AND (amoxicilline-clavulanic acid 50-90 mg/kg/day twice daily))"}
{"candidate_id": "LLM05143", "doc_id": "NCT02687178_exc", "case_bucket": "other", "source_criterion": "diabetes mellitus secondary hypertension pregnancy", "candidate_expression": "((diabetes mellitus) AND (pregnancy) AND (secondary hypertension))"}
{"candidate_id": "LLM05144", "doc_id": "NCT02245256_inc", "case_bucket": "or", "source_criterion": "Adult patients (18years old or older) undergoing living-donor or deceased-donor liver transplantation", "candidate_expression": "((18years old or older) AND (Adult) AND (deceased-donor liver transplantation) AND (living-donor liver transplantation) AND (years))"}
{"candidate_id": "LLM05145", "doc_id": "NCT02570321_exc", "case_bucket": "or", "source_criterion": "Evidence of concomitant infection on exam or gram stain (i.e. herpes, both bacteria and acanthamoeba on gram stain) Impending or frank perforation at recruitment Involvement of sclera at presentation Non-infectious or autoimmune keratitis History of corneal transplantation or recent intraocular surgery No light perception in the affected eye Pinhole visual acuity worse than 20/200 in the unaffected eye Participants who are decisionally and/or cognitively impaired", "candidate_expression": "((Involvement of sclera) AND (Non-infectious keratitis) AND (Pinhole visual acuity worse than 20/200) AND (autoimmune keratitis) AND (cognitively impaired) AND (concomitant infection) AND (corneal transplantation) AND (intraocular surgery) AND (perforation) AND NOT (light perception))"}
{"candidate_id": "LLM05146", "doc_id": "NCT02322203_inc", "case_bucket": "other", "source_criterion": "Males and females who are at least 18 years of age at time of enrollment. Subject understands the investigational nature of the study and provides written, informed consent.", "candidate_expression": "((Males) AND (Subject understands the investigational nature of the study and provides written, informed consent.) AND (age) AND (at least 18 years) AND (at time of enrollment) AND (females) AND (time of enrollment))"}
{"candidate_id": "LLM05147", "doc_id": "NCT02707809_exc", "case_bucket": "or", "source_criterion": "allergic history to dexmedetomidine refractory bradycardia < 60 bpm despite treatment severe atrioventricular block (2nd and 3rd degree) previous operation of tongue", "candidate_expression": "((< 60 bpm) AND (allergic) AND (atrioventricular block) AND (bradycardia) AND (despite treatment) AND (dexmedetomidine) AND (history) AND (operation of tongue) AND (previous) AND (refractory) AND (severe) AND (treatment) AND ((2nd degree) OR (3rd degree)))"}
{"candidate_id": "LLM05148", "doc_id": "NCT02256956_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((Alcohol abuse) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Heart disease) AND (Male Healthy) AND (Metabolic Equivalents >7) AND (Neurological disease) AND (Obstructive uropathy) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction Suspicion tested sites) AND (tested drugs) AND (treatment Ongoing) AND ((CYP3A inducers) OR (CYP3A inhibitors)))"}
{"candidate_id": "LLM05149", "doc_id": "NCT02952365_inc", "case_bucket": "other", "source_criterion": "Subjects age 21 and older Subjects with healthy eyes Subjects who have previously undergone LASIK surgery Subjects with residual refractive error.", "candidate_expression": "((21 and older) AND (LASIK surgery) AND (age) AND (healthy eyes) AND (previously) AND (residual refractive error))"}
{"candidate_id": "LLM05150", "doc_id": "NCT03619707_exc", "case_bucket": "or", "source_criterion": "Preexisting untreated medical condition (thyroid disease, diabetes mellitus, hypertension, pulmonary conditions, cardiac condition…) History of three or more consecutively failed In Vitro Fertilization (IVF) cycles after embryo transfer History of three or more miscarriages Previous allergy reactions to progesterone products", "candidate_expression": "((IVF) AND (In Vitro Fertilization) AND (Preexisting) AND (after embryo transfer) AND (allergy) AND (cardiac condition) AND (consecutively failed) AND (diabetes mellitus) AND (embryo transfer) AND (hypertension) AND (medical condition) AND (miscarriages) AND (progesterone products) AND (pulmonary conditions) AND (three or more) AND (thyroid disease) AND (untreated))"}
```
