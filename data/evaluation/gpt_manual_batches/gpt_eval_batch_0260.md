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
{"candidate_id": "LLM06476", "doc_id": "NCT02916342_exc", "case_bucket": "or", "source_criterion": "indication for catheter insertion; contraindications to brachial plexus block (e.g., allergy to local anaesthetics, malignancy or infection in the area); existing neurological deficit in the area to be blocked; pregnancy; history of neck surgery or radiotherapy; severe respiratory disease; chest deformity; inability to understand the informed consent and demands of the study; patient refusal.", "candidate_expression": "((brachial plexus block) AND (catheter insertion indication) AND (chest deformity) AND (contraindications) AND (inability to understand the informed consent and demands of the study;) AND (local anaesthetics) AND (neurological deficit existing area to be blocked) AND (patient refusal) AND (pregnancy) AND (respiratory disease severe) AND ((neck surgery) OR (radiotherapy)) AND ((allergy) OR (infection in the area) OR (malignancy in the area)))"}
{"candidate_id": "LLM06477", "doc_id": "NCT02837783_exc", "case_bucket": "or", "source_criterion": "Patient has history of loose or watery stools Patient has both clinically significant findings and unexplained clinically significant alarm symptoms Patient has symptoms of or been diagnosed with a medical condition that may contribute to abdominal pain Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments", "candidate_expression": "((Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments) AND (abdominal pain protocol-excluded clinically significant) AND (clinically significant alarm symptoms unexplained) AND (clinically significant findings) AND (loose stools) AND (medical condition may contribute to abdominal pain) AND (medical history) AND (surgical history) AND (watery stools))"}
{"candidate_id": "LLM06478", "doc_id": "NCT03159507_exc", "case_bucket": "or", "source_criterion": "Allergy known to fish Pregnant women who breast-feed or test positive for pregnancy", "candidate_expression": "((Allergy) AND (Pregnant) AND (breast-feed) AND (fish) AND (positive) AND (test for pregnancy) AND (women))"}
{"candidate_id": "LLM06479", "doc_id": "NCT02269137_inc", "case_bucket": "or", "source_criterion": "30 min or more of (1) continuous clinical seizure activities or (2) recurrent seizure activities without recovery(returning to baseline)between seizures; clinical data is complete.", "candidate_expression": "((30 min or more) AND (continuous) AND (recurrent) AND (seizure) AND ((seizure) OR (without recovery)))"}
{"candidate_id": "LLM06480", "doc_id": "NCT00183885_exc", "case_bucket": "or", "source_criterion": "Patients who have received prior chemotherapy for unresectable disease Patients with any active or uncontrolled infection, including known HIV infection. (Patients with active hepatitis B will be placed on lamivudine. Patients with active hepatitis C will be eligible if liver tests qualify (5.1.9) Patients with psychiatric disorders that would interfere with consent or follow-up. Pregnant or lactating women. Men and women of reproductive potential may not participate unless they have agreed to use an effective contraceptive method. Patients with any other severe concurrent disease, which in the judgment of the investigator, would make the patient inappropriate for entry into this study.", "candidate_expression": "((HIV infection) AND (chemotherapy) AND (concurrent disease severe entry into this study) AND (effective contraceptive method) AND (hepatitis B active) AND (hepatitis C active) AND (infection uncontrolled) AND (lamivudine) AND (liver tests qualify) AND (psychiatric disorders interfere with follow-up interfere with consent) AND (reproductive potential) AND (unresectable disease active) AND (women) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM06481", "doc_id": "NCT02416869_exc", "case_bucket": "or", "source_criterion": "Heavy tobacco smokers Drug and / or alcohol abusers", "candidate_expression": "((Heavy tobacco smokers) AND ((Drug abusers) OR (alcohol abusers)))"}
{"candidate_id": "LLM06482", "doc_id": "NCT02205502_exc", "case_bucket": "or", "source_criterion": "contraindication to ketamine and lidocaine patients involved to other studies more or equal to American Society of Anesthesiologist (ASA) class III not alert", "candidate_expression": "((American Society of Anesthesiologist (ASA) class) AND (III more or equal to) AND (contraindication) AND (ketamine) AND (lidocaine) AND (not alert) AND (patients involved to other studies))"}
{"candidate_id": "LLM06483", "doc_id": "NCT01997112_inc", "case_bucket": "or", "source_criterion": "=18 years old, men or post-menopausal women (women with no periods for 12 months or more, or those who have had a surgical menopause) Treated hypertensive patients with an average daytime ambulatory blood pressure measurement (ABPM) <150/95mmHg on stable doses of one or more antihypertensive medication (at least one of which should be; an ACE inhibitor, angiotensin receptor blocker or diuretic) for 3 months, or untreated hypertensive patients with an average daytime ABPM =135/85 but <150/95.", "candidate_expression": "((<150/95mmHg) AND (=135/85 but <150/95) AND (=18) AND (ACE inhibitor) AND (Treated) AND (angiotensin receptor blocker) AND (antihypertensive medication) AND (at least one) AND (average daytime ABPM) AND (average daytime ambulatory blood pressure measurement (ABPM)) AND (diuretic) AND (for 12 months or more) AND (for 3 months) AND (hypertensive) AND (hypertensive patients) AND (men) AND (menopause) AND (no periods) AND (one or more) AND (post-menopausal) AND (stable doses) AND (surgical) AND (untreated) AND (women) AND (years old))"}
{"candidate_id": "LLM06484", "doc_id": "NCT02678663_exc", "case_bucket": "or", "source_criterion": "Anticoagulant therapy during the past 1 week of the procedure Known coagulopathy History of liver cirrhosis, chronic kidney disease, malignancy, inflammatory bowel disease, significant infectious disease, polyposis syndrome", "candidate_expression": "((Anticoagulant during the past 1 week) AND (coagulopathy) AND (procedure) AND ((chronic kidney disease) OR (inflammatory bowel disease) OR (liver cirrhosis) OR (malignancy) OR (polyposis syndrome) OR (significant infectious disease)))"}
{"candidate_id": "LLM06485", "doc_id": "NCT03176316_inc", "case_bucket": "other", "source_criterion": "Patients will be included if they are having an in-patient spinal fusion procedure, are 18 years or older, post and post-operative pain control plan includes opioid medications.", "candidate_expression": "((18 years or older) AND (in-patient) AND (opioid) AND (pain control plan) AND (post-operative) AND (spinal fusion procedure) AND (years))"}
{"candidate_id": "LLM06486", "doc_id": "NCT02912182_inc", "case_bucket": "other", "source_criterion": "definite unilateral vestibulopathy no pathological HINTS (examination criteria in acute vestibular syndrome) capable of making their own decisions", "candidate_expression": "((acute vestibular syndrome) AND (capable of making their own decisions) AND (vestibulopathy unilateral) AND NOT (HINTS pathological))"}
{"candidate_id": "LLM06487", "doc_id": "NCT01757717_inc", "case_bucket": "other", "source_criterion": "Patients must have histologic proof of a malignancy suitable for radiation therapy. Patients must have received prior external beam radiation therapy to the region proposed for HDR brachytherapy treatment; evaluation of doses previously delivered to spinal cord/cauda equine, pelvis, and other critical structures (bowel, kidneys, rectum) will be taken into consideration. If repeat irradiation would exceed any normal tissue constraint set by MSKCC Radiation Oncology Department dose constraint criteria, the patient will potentially be eligible. If the total prior radiation dose to the cord or pelvis exceeds 100 Gy BED equivalent, the patient will be potentially eligible, where a total of 100 BED Gy equivalent is determined by the biological equivalent dose (BED) calculation; BED = nd(1 + d/α/β), where n = number of fractions and d = dose per fraction; α/β is the constant for spinal cord late effect and equals 2. [Rades 2005, Nieder 2005, Sahgal 2012] KPS ≥ 60 Age ≥ 18 years old", "candidate_expression": "((Age ≥ 18 years old) AND (HDR brachytherapy) AND (KPS ≥ 60) AND (MSKCC Radiation Oncology Department dose constraint criteria exceed any normal tissue constraint) AND (external beam radiation therapy prior to the region proposed for HDR brachytherapy treatment) AND (histologic proof) AND (malignancy suitable for radiation therapy) AND (radiation therapy) AND (repeat irradiation) AND (suitable for radiation therapy))"}
{"candidate_id": "LLM06488", "doc_id": "NCT00676273_inc", "case_bucket": "other", "source_criterion": "Are at least 18 years of age Demonstrate a positive cough stress test during complex multi-channel urodynamic testing Demonstrate impact of stress urinary incontinence on quality of life questionnaire Are able to comprehend and sign a written informed consent Understand and are willing to comply with the study requirements, including agreeing to be available for the follow-up evaluations Are psychologically stable and suitable for interventions determined by the investigator Are ambulatory and able to use a toilet independently", "candidate_expression": "((Understand the study requirements) AND (able to comprehend a written informed consent) AND (able to sign a written informed consent) AND (able to use a toilet independently) AND (age) AND (ambulatory) AND (at least 18 years) AND (complex multi-channel urodynamic testing) AND (cough stress test) AND (determined by the investigator) AND (positive) AND (psychologically stable) AND (quality of life questionnaire) AND (stress urinary incontinence) AND (suitable for interventions) AND (willing to comply with the study requirements))"}
{"candidate_id": "LLM06489", "doc_id": "NCT02937779_exc", "case_bucket": "other", "source_criterion": "Women refusing HBs Ag test HIV co-infection HCV co-infection HBV treatment ongoing at the day of inclusion Creatinine clearance < 30 mL/min Severe gravidic disease present at inclusion involving life threatening to the mother and/or the child Evidence of pre-existing fetal anomalies incompatible with the child's life Imminent child's birth defined as cervix dilatation up to 7 centimeters Intention to deliver in a maternity not linked to the study Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study. Concurrent participation in any other clinical trial without written agreement of the two study teams", "candidate_expression": "((Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study) AND (Concurrent participation in any other clinical trial without written agreement of the two study teams) AND (Creatinine clearance < 30 mL/min) AND (HBV treatment) AND (Imminent child's birth) AND (Intention to deliver in a maternity not linked to the study) AND (cervix dilatation 7 centimeters) AND (co-infection HCV) AND (co-infection HIV) AND (fetal anomalies) AND (gravidic disease Severe life threatening) AND NOT (HBs Ag test))"}
{"candidate_id": "LLM06490", "doc_id": "NCT03495609_exc", "case_bucket": "or", "source_criterion": "History of allergic reaction to compounds of similar chemical or biologic composition to hCG receiving medication that could interfere with the study protocol objectives (hormonal contraceptives, androgens, prednisone, thyroid hormones, insulin) previous treatment with follicle stimulating hormone for assisted reproduction uncontrolled intercurrent illness Heart disease Severe cognitive decline Psychiatric desease HIV positive Hepatitis B or C infection", "candidate_expression": "((HIV positive) AND (Heart disease) AND (Psychiatric desease) AND (allergic reaction History) AND (assisted reproduction) AND (cognitive decline Severe) AND (compounds of similar chemical or biologic composition to hCG) AND (follicle stimulating hormone) AND (hCG) AND (intercurrent illness uncontrolled) AND (medication receiving could interfere with the study protocol objectives) AND (treatment previous) AND ((Hepatitis B infection) OR (Hepatitis C infection)) AND ((androgens) OR (hormonal contraceptives) OR (insulin) OR (prednisone) OR (thyroid hormones)))"}
{"candidate_id": "LLM06491", "doc_id": "NCT02416765_exc", "case_bucket": "or", "source_criterion": "1. Clinically significant microvascular complications: nephropathy (estimated glomerular filtration rate below 40 ml/min), neuropathy (especially diagnosed gastroparesis) or severe proliferative retinopathy as judged by the investigator. 2. Recent (< 3 months) acute macrovascular event e.g. acute coronary syndrome or cardiac surgery. 3. Ongoing pregnancy. 4. Severe hypoglycemic episode within 1 month of screening. 5. Agents affecting gastric emptying (Motilium®, Prandase®, Victoza®, Byetta® and Symlin®) as well as oral anti-diabetic agents (Metformin, SGLT-2 inhibitors and DPP-4 inhibitors) if not at a stable dose for 3 months. Otherwise, these medications are acceptable and will be kept stable during the entire protocol. 6. Oral steroids unless patients present a low stable dose (e.g. 10 mg or less of prednisone per day or physiological doses, less than 35 mg/day, of hydrocortisone Cortef®). Inhale steroids at stable dose in the last month are acceptable. 7. Other serious medical illness likely to interfere with study participation or with the ability to complete the trial by the judgment of the investigator (e.g. unstable psychiatric condition). 8. Failure to comply with team's recommendations (e.g. not willing to change pump parameters, follow algorithm's suggestions, etc). 9. Living or planned travel outside Montreal (> 1h of driving) area during closed-loop procedures.", "candidate_expression": "((10 mg or less per day) AND (< 3 months) AND (Agents affecting gastric emptying) AND (Byetta) AND (Cortef) AND (DPP-4 inhibitors) AND (Inhale steroids) AND (Metformin) AND (Motilium) AND (Ongoing) AND (Oral steroids) AND (Other medical illness) AND (Prandase) AND (Recent) AND (SGLT-2 inhibitors) AND (Severe) AND (Symlin) AND (Victoza) AND (acute coronary syndrome) AND (acute macrovascular event) AND (as judged by the investigator) AND (below 40 ml/min) AND (by the judgment of the investigator) AND (cardiac surgery) AND (closed-loop procedures) AND (during closed-loop procedures) AND (estimated glomerular filtration rate) AND (for 3 months) AND (gastroparesis) AND (hydrocortisone) AND (hypoglycemic episode) AND (in the last month) AND (less than 35 mg/day) AND (low dose) AND (microvascular complications) AND (nephropathy) AND (neuropathy) AND (not) AND (oral anti-diabetic agents) AND (physiological doses) AND (prednisone) AND (pregnancy) AND (psychiatric condition) AND (serious) AND (severe proliferative retinopathy) AND (stable dose) AND (unless) AND (unstable) AND (within 1 month of screening))"}
{"candidate_id": "LLM06492", "doc_id": "NCT02201316_exc", "case_bucket": "or", "source_criterion": "Current or chronic history of liver disease, or known hepatic or biliary abnormalities (with the exception of Gilbert's syndrome or asymptomatic gallstones). History of regular alcohol consumption within 6 months of the study defined as: An average weekly intake of >21 units for males or >14 units for females. One unit is equivalent to 8 gram of alcohol: a half-pint (approximately 240 milliliter [mL]) of beer, 1 glass (100 mL) of wine or 1 (25 mL) measure of spirits. History of sensitivity to heparin or heparin-induced thrombocytopenia. History of sensitivity to any of the study medications, or components thereof or a history of drug or other allergy that, in the opinion of the investigator or GSK Medical Monitor, contraindicates their participation. Gastrointestinal disease or with gastrointestinal surgical history which can affect the absorption of the investigational product. A positive pre-study Hepatitis B surface antigen or positive Hepatitis C antibody result within 3 months of screening Urinary cotinine levels indicative of smoking or history or regular use of tobacco- or nicotine-containing products within 6 months prior to screening. A positive pre-study drug/alcohol screen. A positive test for Human Immunodeficiency Virus (HIV) antibody. Pregnant females as determined by positive serum hCG test at screening or prior to dosing. Where participation in the study would result in donation of blood or blood products in excess of 500 mL within a 90 day period. Lactating females. The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer). Exposure to more than four new chemical entities within 12 months prior to the first dosing day.", "candidate_expression": "((Gastrointestinal disease) AND (Hepatitis B surface antigen positive pre-study) AND (Hepatitis C antibody positive) AND (History) AND (Human Immunodeficiency Virus (HIV) antibody positive) AND (Lactating) AND (Pregnant) AND (The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer).) AND (Urinary cotinine levels) AND (alcohol screen) AND (allergy) AND (average weekly intake) AND (biliary abnormalities) AND (contraindicates their participation) AND (drug allergy) AND (drug screen) AND (females) AND (females >14 units) AND (gastrointestinal surgical) AND (gastrointestinal surgical history affect the absorption of the investigational product) AND (heparin) AND (heparin-induced thrombocytopenia) AND (hepatic abnormalities) AND (in the opinion of the investigator or GSK Medical Monitor) AND (liver disease history Current chronic) AND (males >21 units) AND (new chemical entities more than four within 12 months prior to the first dosing day) AND (regular alcohol consumption History within 6 months of the study) AND (regular use of nicotine-containing products history) AND (regular use of tobacco history) AND (sensitivity to any of the study medications) AND (sensitivity to heparin heparin-induced) AND (serum hCG test positive at screening prior to dosing) AND (smoking) AND (study medications) AND NOT (gallstones asymptomatic) AND NOT (Gilbert's syndrome))"}
{"candidate_id": "LLM06493", "doc_id": "NCT02042287_inc", "case_bucket": "other", "source_criterion": "> 18 years old Acute symptomatic BV Signed informed consent Insufficient knowledge of German Illiteracy Pregnancy Acute illness Known allergies against ingredients of the investigational products", "candidate_expression": "((18 years) AND (Acute) AND (Acute illness) AND (BV) AND (Illiteracy) AND (Insufficient knowledge of German) AND (Pregnancy) AND (Signed informed consent) AND (allergies) AND (ingredients of the investigational products) AND (old) AND (symptomatic))"}
{"candidate_id": "LLM06494", "doc_id": "NCT02707874_exc", "case_bucket": "or", "source_criterion": "Patients who undergo iliac crest bone graft harvesting as part of their surgery Preexisting neurological deficits or peripheral neuropathy in the distribution of the sciatic nerve Local infection Contraindication to regional anesthesia e.g. bleeding diathesis, coagulopathy Chronic pain disorders History of use of over 30mg oxycodone or equivalent per day Allergy to local anesthetics History of significant psychiatric conditions that may affect patient assessment Pregnancy Inability to provide informed consent", "candidate_expression": "((Allergy) AND (Chronic pain) AND (Contraindication) AND (Inability to provide informed consent) AND (Local infection) AND (Pregnancy) AND (bleeding diathesis) AND (coagulopathy) AND (iliac crest bone graft harvesting) AND (local anesthetics) AND (neurological deficits) AND (oxycodone) AND (oxycodone equivalent) AND (peripheral neuropathy) AND (regional anesthesia))"}
{"candidate_id": "LLM06495", "doc_id": "NCT02902120_exc", "case_bucket": "or", "source_criterion": "Documented positive hepatitis B (HBV) surface antigen, and/or HBV DNA prior to enrollment Any prior exposure to HCV protease inhibitor therapy HIV co-infection if on a protease inhibitor based regimen Increase in creatinine of 15% or greater within one month (30 days) of the screening visit Evidence of hepatocellular carcinoma at the time of enrollment Liver disease caused by an etiology other than HCV F4 or decompensated cirrhotic patients Child Pugh class B or C AST or ALT >350 within 6 months prior to enrollment Albumin < 3g/dL at the time of enrollment Platelet count < 75 at the time of enrollment History of clinically significant allergy or adverse event with protease inhibitors Evidence of the acquisition of HCV at the time of or after transplantation Pregnant or breastfeeding women Cyclosporine; St. John's Wort; Efavirenz; Phenytoin; Carbamazepine; Bosentan; HIV protease inhibitors; modafinil; ketoconazole; or rifampin use within 7 days of enrollment Coadministration of more than 20 mg atorvastatin; 10 mg rosuvastatin; 20 mg of fluvastatin, lovastatin or simvastatin", "candidate_expression": "((Albumin < 3g/dL) AND (Child Pugh class B or C) AND (HCV protease inhibitor therapy) AND (HIV co-infection) AND (Liver disease) AND (Platelet count < 75) AND (Pregnant or breastfeeding women) AND (acquisition of HCV at the time of or after transplantation) AND (creatinine Increase of 15% or greater within one month 30 days) AND (hepatocellular carcinoma) AND (protease inhibitor) AND (protease inhibitors) AND NOT (HCV) AND ((F4) OR (decompensated cirrhotic)) AND ((ALT) OR (AST)) AND ((HBV DNA) OR (hepatitis B surface antigen)) AND ((adverse event) OR (allergy)) AND ((Bosentan) OR (Carbamazepine) OR (Cyclosporine) OR (Efavirenz) OR (HIV protease inhibitors) OR (Phenytoin) OR (St. John's Wort) OR (ketoconazole) OR (modafinil) OR (rifampin)) AND ((atorvastatin more than 20 mg) OR (rosuvastatin more than 10 mg)) AND ((fluvastatin) OR (lovastatin) OR (simvastatin)))"}
{"candidate_id": "LLM06496", "doc_id": "NCT03067740_exc", "case_bucket": "or", "source_criterion": "The diagnosis of developmental delay, attention deficit disorder, chronic pain, psychiatric illness, previous open abdominal surgery, the presence of a gastrostomy, ventricular-peritoneal shunt or other abdominal prosthesis, immunosuppression, and those allergic to any of the medications.", "candidate_expression": "((abdominal prosthesis) AND (allergic) AND (any of the medications) AND (attention deficit disorder) AND (chronic pain) AND (developmental delay) AND (gastrostomy) AND (immunosuppression) AND (open abdominal surgery) AND (previous) AND (psychiatric illness) AND (ventricular-peritoneal shunt))"}
{"candidate_id": "LLM06497", "doc_id": "NCT02926989_inc", "case_bucket": "other", "source_criterion": "Acutely ill hospitalised children Need for intravenous fluid therapy", "candidate_expression": "((Acutely ill) AND (Need for) AND (children) AND (hospitalised) AND (intravenous fluid therapy))"}
{"candidate_id": "LLM06498", "doc_id": "NCT03476850_inc", "case_bucket": "other", "source_criterion": "Patients undergoing laparoscopic assisted donor nephrectomy Patients that have elected to have a nerve block 18 years of age or older Patients of ASA status I - III", "candidate_expression": "((18 years or older) AND (ASA status) AND (I - III) AND (age) AND (elected to have) AND (laparoscopic assisted donor nephrectomy) AND (nerve block))"}
{"candidate_id": "LLM06499", "doc_id": "NCT03252249_inc", "case_bucket": "other", "source_criterion": "Aged =18 years Clinical diagnosis of acute coronary syndrome In the opinion of the attending clinician requires dual anti-platelet therapy with aspirin and a P2Y12 receptor antagonist Resident in Scotland with a Community Health Index (CHI) number The attending clinician has equipoise regarding the duration of therapy Provision of informed consent", "candidate_expression": "((Aged =18 years) AND (P2Y12 receptor antagonist) AND (Provision of informed consent) AND (Resident) AND (Scotland) AND (acute coronary syndrome) AND (aspirin) AND (dual anti-platelet therapy requires))"}
{"candidate_id": "LLM06500", "doc_id": "NCT01757717_exc", "case_bucket": "or", "source_criterion": "Patients who may receive therapeutically effective doses via an external beam approach to the lesion of interest as specified by MSKCC Radiation Oncology Department dose constraint criteria. Patients with kyphoplasty cement or hardware that would preclude effective catheter placement. Patients with paraspinal extension of disease with visceral involvement. Abnormal complete blood count. Any of the following: Platelet count < 75,000/ml Hb level < 9gm/dl WBC < 3.5/ml Abnormal coagulation profile: INR > 2.5 and/or PTT > 80 Patients who are on anticoagulation medication that may not be safely held for the procedure (≥ 5 days for antiplatelet agents and warfarin; ≥ 24 hours for low-molecular weight heparin formulations) will be excluded. Contraindications to general anesthesia", "candidate_expression": "((< 3.5/ml) AND (< 75,000/ml) AND (< 9gm/dl) AND (> 2.5) AND (> 80) AND (Abnormal) AND (Abnormal coagulation profile) AND (Abnormal complete blood count) AND (Contraindications to general anesthesia) AND (Hb level) AND (MSKCC Radiation Oncology Department dose constraint criteria) AND (Platelet count) AND (WBC) AND (anticoagulation medication) AND (antiplatelet agents) AND (coagulation profile) AND (complete blood count) AND (doses) AND (external beam) AND (general anesthesia) AND (low-molecular weight heparin) AND (may not be safely held for the procedure) AND (may receive therapeutically effective doses via an external beam approach to the lesion of interest) AND (paraspinal extension of disease) AND (preclude effective catheter placement) AND (therapeutically effective) AND (visceral involvement) AND (warfarin) AND (≥ 24 hours) AND (≥ 5 days) AND ((INR) OR (PTT)) AND ((kyphoplasty cement) OR (kyphoplasty hardware)))"}
```
