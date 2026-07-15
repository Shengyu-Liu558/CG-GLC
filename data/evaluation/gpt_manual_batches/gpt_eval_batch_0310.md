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
{"candidate_id": "LLM07726", "doc_id": "NCT02783859_exc", "case_bucket": "or", "source_criterion": "Current wheeze Underlying chronic illness other than asthma (e.g. bronchiectasis, cyanotic congenital heart disease or cardiac failure, neuromuscular disorders, immunodeficiency) that could potentially influence the current illness Severe malnutrition (weight-for-height Z-score <-3) Complicated (effusion, empyema or abscess) pneumonia, including tuberculosis Extra-pulmonary infection requiring antibiotic therapy (e.g. meningitis) Beta-lactam allergy Previously enrolled Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months", "candidate_expression": "((Beta-lactam) AND (Complicated pneumonia) AND (Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months) AND (Previously enrolled) AND (abscess) AND (allergy) AND (antibiotic therapy) AND (bronchiectasis) AND (cardiac failure) AND (chronic illness) AND (cyanotic congenital heart disease) AND (effusion) AND (empyema) AND (immunodeficiency) AND (infection Extra-pulmonary) AND (malnutrition Severe) AND (meningitis) AND (neuromuscular disorders) AND (tuberculosis) AND (weight-for-height Z-score <-3) AND (wheeze) AND NOT (asthma))"}
{"candidate_id": "LLM07727", "doc_id": "NCT01322464_inc", "case_bucket": "or", "source_criterion": "Healthy males between 18 and 45 years of age (inclusive). Body mass index to be between 18 to 30 kg/m2 (inclusive) as calculated by weight(Kg)/height(m2). Subjects were to have no clinically significant abnormal findings on physical examination, ECG, medical history, or clinical laboratory results during screening. Subjects were to, in the opinion of the investigator, have no clinically significant abnormal findings of renal and hepatic function as determined by serum creatinine, total bilirubin, and transaminase levels. Subjects were to be non-users of tobacco products (minimum of 6 months prior to the start of the study). Subjects were to have a negative screen for HIV I and II, HBsAg, and antibody to Hepatitis C virus. Subjects were to have a negative urine screen for alcohol, drugs of abuse (screening only), and cotinine. Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug. Subjects were able to comply with the protocol and the restrictions and assessments therein. Subjects were to give voluntary written informed consent to participate in the trial.", "candidate_expression": "((Body mass index) AND (HBsAg) AND (Healthy) AND (Subjects were able to comply with the protocol and the restrictions and assessments therein.) AND (Subjects were to give voluntary written informed consent to participate in the trial) AND (Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug.) AND (abnormal findings) AND (age) AND (antibody to Hepatitis C virus) AND (between 18 and 45 years) AND (between 18 to 30 kg/m2) AND (clinically significant) AND (during screening) AND (hepatic function) AND (in the opinion of the investigator) AND (minimum of 6 months prior to the start of the study) AND (negative) AND (no) AND (non) AND (renal function) AND (screen for HIV I) AND (screen for HIV II) AND (serum creatinine) AND (the start of the study) AND (total bilirubin) AND (transaminase levels) AND (urine screen for alcohol) AND (urine screen for cotinine) AND (urine screen for drugs of abuse) AND (users of tobacco products) AND ((ECG) OR (clinical laboratory) OR (medical history) OR (physical examination)))"}
{"candidate_id": "LLM07728", "doc_id": "NCT02224040_inc", "case_bucket": "or", "source_criterion": "Blood culture-proven typhoid fever (S. typhi or S. paratyphi) Signed informed consent to participate in the study.", "candidate_expression": "((Blood culture proven) AND (S. paratyphi) AND (S. typhi) AND (Signed informed consent to participate in the study.) AND (typhoid fever))"}
{"candidate_id": "LLM07729", "doc_id": "NCT02415257_inc", "case_bucket": "other", "source_criterion": "Vestibular schwannoma advised to surgical treatment No measurable remaining vestibular function", "candidate_expression": "((Vestibular schwannoma) AND (surgical treatment advised) AND NOT (remaining vestibular function))"}
{"candidate_id": "LLM07730", "doc_id": "NCT01765231_exc", "case_bucket": "or", "source_criterion": "younger than 18 years old HBsAg positive or HBcAb negative or hepatitis B virus DNA positive at baseline pregnant or lactating women", "candidate_expression": "((old younger than 18 years) AND (women) AND ((HBcAb negative) OR (HBsAg positive) OR (hepatitis B virus DNA positive)) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM07731", "doc_id": "NCT02186600_exc", "case_bucket": "or", "source_criterion": "Have osteoporosis Have a 10 yr probability of hip fracture >3% or major fracture >20% based on results of the FRAX tool Currently take bisphosphonates, estrogen replacement therapy, glucocorticosteroids, or other drugs affecting bone Currently participate in a resistance training or high impact weight bearing exercise program two or more times weekly Weigh >300 lbs Have abnormal results for the following laboratory tests: serum 25(OH)D; serum creatinine; serum calcium; PTH; TSH Have Paget's disease, heart disease, uncontrolled hypertension, renal disease, or other concomitant conditions that prohibit participation in exercises, risedronate therapy, or use of CaD supplements.", "candidate_expression": "((10 yr probability of hip fracture) AND (10 yr probability of major fracture) AND (>20%) AND (>3%) AND (>300 lbs) AND (CaD supplements) AND (PTH) AND (Paget's disease) AND (TSH) AND (Weigh) AND (abnormal results) AND (bisphosphonates) AND (drugs affecting bone) AND (estrogen replacement therapy) AND (glucocorticosteroids) AND (heart disease) AND (hip fracture) AND (major fracture) AND (osteoporosis) AND (other concomitant conditions that prohibit participation in exercises) AND (participate in a resistance training) AND (participate in high impact weight bearing exercise) AND (renal disease) AND (risedronate therapy) AND (serum 25(OH)D) AND (serum calcium) AND (serum creatinine) AND (two or more times weekly) AND (uncontrolled hypertension))"}
{"candidate_id": "LLM07732", "doc_id": "NCT02985242_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes uncontrolled diabetes mellitus type 2 with fasting glucose > 13.3 mmol/l confirmed on a second day known or suspected hypersensitivity to empagliflozin, glimepiride, or any excipients; and / or known or suspected hypersensitivity to sulfonylureas, sulfonamides or SGLT2 inhibitors in general history of multiple severe hypoglycemic episodes within the last two years use of Insulin, SGLT2-inhibitor, sulfonylurea derivate or a glinide within past 3 months clinical significant macular edema in both eyes and indication for intravitreal anti-VEGF treatment for both eyes at screening or baseline visit. Eyes with a small amount of intraretinal or subretinal fluid (seen in OCT) but no need for intravitreal treatment as judged by the investigator (according to current practice patterns) may be included. Eyes with a history of intravitreal treatment of macular edema which do not need ongoing intravitreal treatment at the time of screening may be included. eye diseases or pathologies that prevent clear ophthalmoscopy and evaluation of study parameters, thus not allowing study participation according to the investigator´s judgment, such as (but not only) vitreous hemorrhage, mature cataract, macular pathologies other than diabetic maculopathy history of ketoacidosis or metabolic acidosis use of loop diuretics history of > 1 urogenital infection/year any history of stroke, transient ischemic attack (TIA), instable angina pectoris or myocardial infarction within last 3 months prior to baseline visit congestive heart failure New York Heart Association (NYHA) III and IV severe valvular or left ventricular outflow obstruction disease needing intervention; atrial fibrillation/flutter with a mean ventricular response rate at rest >100 beats per minute chronic lower urinary tract infections (but not simple asymptomatic bacteriuria) eGFR < 60 ml/min/1,73 m2 (MDRD-formula, confirmed on a second day) chronic diarrhea, any clinical signs of volume depletion or a hematocrit > 48 % (women) and > 53 % (men) elevated risk for volume depletion, e.g. history of severe volume depletion that required medical therapy chronic liver disease (including known active hepatitis) and/or screening alanine transaminase (ALT) or aspartate transaminase (AST) > 3 x upper limit of normal (ULN) (confirmed on a second day) Subjects with known seropositivity to human immunodeficiency virus. acute illness at screening or randomization according to judgement by the investigator or patient drug or alcohol abuse psychosomatic or psychiatric diseases requiring hospitalization during the last 12 months clinical evidence of current malignancy with exception of basal cell or squamous cell carcinoma of the skin, and cervical intraepithelial neoplasia (5 years prior to randomization) any medical or surgical intervention planned for the next 13 months after randomization not allowing study participation according to the investigator´s judgment current participation in any other clinical trial or participation in another clinical trial within 30 days before screening", "candidate_expression": "((5 years prior to randomization) AND (< 60 ml/min/1,73 m2) AND (> 1 /year) AND (> 13.3 mmol/l) AND (> 3 x upper limit of normal) AND (> 48 %) AND (> 53 %) AND (>100 beats per minute) AND (ALT) AND (AST) AND (III and IV) AND (NYHA) AND (New York Heart Association) AND (TIA) AND (Type 1 diabetes) AND (active hepatitis) AND (asymptomatic bacteriuria) AND (at rest) AND (baseline visit) AND (both eyes) AND (chronic) AND (chronic liver disease) AND (congestive heart failure) AND (current participation in any other clinical trial or participation in another clinical trial within 30 days before screening) AND (diabetes mellitus type 2) AND (diabetic maculopathy) AND (eGFR) AND (elevated) AND (exception) AND (fasting glucose) AND (hospitalization) AND (human immunodeficiency virus) AND (hypoglycemic episodes) AND (instable) AND (intervention) AND (intravitreal anti-VEGF treatment) AND (last 12 months) AND (last 3 months prior to baseline visit) AND (last two years) AND (loop diuretics) AND (lower urinary tract infections) AND (macular edema) AND (malignancy) AND (mean ventricular response rate) AND (men) AND (multiple) AND (not) AND (ophthalmoscopy) AND (other) AND (past 3 months) AND (prevent) AND (randomization) AND (risk for volume depletion,) AND (seropositivity) AND (severe) AND (uncontrolled) AND (urogenital infection) AND (women) AND ((basal cell carcinoma of the skin) OR (cervical intraepithelial neoplasia) OR (squamous cell carcinoma of the skin)) AND ((SGLT2 inhibitors) OR (sulfonamides) OR (sulfonylureas)) AND ((Insulin) OR (SGLT2-inhibitor) OR (glinide) OR (sulfonylurea derivate)) AND ((macular pathologies) OR (mature cataract) OR (vitreous hemorrhage)) AND ((ketoacidosis) OR (metabolic acidosis)) AND ((angina pectoris) OR (myocardial infarction) OR (stroke) OR (transient ischemic attack)) AND ((left ventricular outflow obstruction) OR (valvular disease)) AND ((hypersensitivity)) AND ((atrial fibrillation) OR (atrial flutter)) AND ((empagliflozin) OR (glimepiride)) AND ((chronic diarrhea) OR (volume depletion)) AND ((hematocrit)) AND ((alanine transaminase) OR (aspartate transaminase)) AND ((alcohol abuse) OR (drug abuse)) AND ((psychiatric diseases) OR (psychosomatic diseases)))"}
{"candidate_id": "LLM07733", "doc_id": "NCT00806273_inc", "case_bucket": "other", "source_criterion": "ASA 1 ASA 2 Pts have current treatment plan at OHSU for extraction of some or all of remaining teeth and scheduled for delivery of a removable appliance post extraction Teeth used are able to be isolated with rubber dam Understand and sign consent form", "candidate_expression": "((ASA 1) AND (ASA 2) AND (Understand and sign consent form) AND (scheduled for) AND (treatment plan at OHSU))"}
{"candidate_id": "LLM07734", "doc_id": "NCT03639519_exc", "case_bucket": "or", "source_criterion": "Allergy to ascorbic acid Asthma COPD Allergy to opioids Previous history of chemical dependence Prior cardiac surgery Known hyperoxaluria History of renal calculi History of allergic or hypersensitivity reaction to ascorbic acid products Currently taking 1 g or more of ascorbic acid supplementation daily", "candidate_expression": "((1 g or more) AND (Allergy) AND (Asthma) AND (COPD) AND (History) AND (Previous) AND (Prior) AND (allergic) AND (ascorbic acid) AND (cardiac surgery) AND (chemical dependence) AND (history) AND (hyperoxaluria) AND (hypersensitivity) AND (opioids) AND (renal calculi))"}
{"candidate_id": "LLM07735", "doc_id": "NCT03104816_inc", "case_bucket": "or", "source_criterion": "ASA I-III patients scheduled for elective one or two level minimally invasive lumbar fusions", "candidate_expression": "((ASA) AND (I-III) AND (elective) AND (minimally invasive lumbar fusions) AND (scheduled) AND ((one level) OR (two level)))"}
{"candidate_id": "LLM07736", "doc_id": "NCT00401245_inc", "case_bucket": "or", "source_criterion": "Generally healthy, postmenopausal woman who seeks treatment for hot flushes. Meets 1 of the following: At least 12 months of spontaneous amenorrhea; At least 6 months of spontaneous amenorrhea with serum follicle-stimulating hormone (FSH) levels > 40 mIU/mL; At least 6 weeks postsurgical bilateral oophorectomy (with or without hysterectomy). Hysterectomized without bilateral oophorectomy and with serum FSH levels >40 mIU/mL.", "candidate_expression": "((Hysterectomized) AND (bilateral oophorectomy) AND (bilateral oophorectomy with hysterectomy) AND (bilateral oophorectomy without hysterectomy) AND (healthy) AND (hot flushes Meets 1 of the following) AND (postmenopausal) AND (serum FSH levels >40 mIU/mL) AND (serum follicle-stimulating hormone (FSH) levels > 40 mIU/mL) AND (spontaneous amenorrhea At least 12 months) AND (spontaneous amenorrhea At least 6 months) AND (woman) AND NOT (bilateral oophorectomy))"}
{"candidate_id": "LLM07737", "doc_id": "NCT03159507_inc", "case_bucket": "other", "source_criterion": "Participant aged 19 or over Available for the entire duration of the study and willing to participate on the basis of the information provided in the FIU duly read and signed.", "candidate_expression": "((19 or over) AND (Available for the entire duration of the study and willing to participate on the basis of the information provided in the FIU duly read and signed.) AND (aged))"}
{"candidate_id": "LLM07738", "doc_id": "NCT02995291_inc", "case_bucket": "other", "source_criterion": "18 years of age or older capable of providing informed consent", "candidate_expression": "((age 18 years of or older) AND (capable of providing informed consent))"}
{"candidate_id": "LLM07739", "doc_id": "NCT02321202_inc", "case_bucket": "other", "source_criterion": "The cirrhotic malnourished patients who were diagnosed as liver cancer preoperatively and underwent hepatectomy were consecutively enrolled.", "candidate_expression": "((cirrhotic) AND (hepatectomy) AND (liver cancer) AND (malnourished) AND (preoperatively))"}
{"candidate_id": "LLM07740", "doc_id": "NCT02957877_exc", "case_bucket": "or", "source_criterion": "History of intolerance to LMWHs during HD Receiving warfarin or other oral anticoagulant Pregnant patients", "candidate_expression": "((HD) AND (LMWHs) AND (Pregnant) AND (during HD) AND (intolerance) AND (oral anticoagulant) AND (other) AND (warfarin))"}
{"candidate_id": "LLM07741", "doc_id": "NCT03318874_inc", "case_bucket": "other", "source_criterion": "Meibomian Gland Dysfunction Eligible for heat treatment Ocular Surface Disease Index (OSDI) >12 Quality or expressibility score =20 years old: >1 or >20 years old: =1 Non-invasive tear film break-up time (NITBUT) <10 s in at least one eye Schirmer-1 test >5 mm after 5 min", "candidate_expression": "((<10 s) AND (>12) AND (>5 mm) AND (Eligible for) AND (Meibomian Gland Dysfunction) AND (Non-invasive tear film break-up time (NITBUT)) AND (OSDI) AND (Ocular Surface Disease Index) AND (Schirmer-1 test) AND (after 5 min) AND (at least one) AND (expressibility score) AND (eye) AND (heat treatment) AND (score Quality))"}
{"candidate_id": "LLM07742", "doc_id": "NCT03351608_inc", "case_bucket": "or", "source_criterion": "Be categorized as American Society of Anesthesiologists (ASA) Physical Status Class 1, 2, or 3. Have a planned non-emergent surgical procedure or clinical situation (e.g., intubation) that requires moderate or deep NMB with either rocuronium or vecuronium. Have a planned surgical procedure or clinical situation that would allow objective neuromuscular monitoring techniques to be applied with access to the arm for neuromuscular transmission monitoring. Age between 2 to <17 years at Visit 2. If female, may participate if she is not pregnant, not breastfeeding, and at least one of the following: 1) Not a woman of childbearing potential (WOCBP); or 2) A WOCBP who agrees to follow the study contraceptive guidance during the treatment period and for at least 7 days after the last dose of study treatment.", "candidate_expression": "((1) AND (2) AND (3) AND (Age) AND (American Society of Anesthesiologists (ASA) Physical Status Class) AND (NMB) AND (Not) AND (WOCBP) AND (at Visit 2) AND (at least one) AND (between 2 to <17 years) AND (breastfeeding) AND (clinical situation) AND (contraceptive guidance) AND (deep) AND (during the treatment period) AND (female) AND (for at least 7 days after the last dose of study treatment) AND (intubation) AND (moderate) AND (non-emergent) AND (not) AND (objective neuromuscular monitoring techniques) AND (planned) AND (pregnant) AND (rocuronium) AND (surgical procedure) AND (that would allow objective neuromuscular monitoring techniques to be applied) AND (the last dose of study treatment) AND (the treatment period) AND (vecuronium) AND (woman of childbearing potential (WOCBP)))"}
{"candidate_id": "LLM07743", "doc_id": "NCT02003339_inc", "case_bucket": "or", "source_criterion": "Early, intermediate, advanced, non metastatic Hepatocellular Carcinoma. Indication for radioembolization validated after pluridisciplinary committee meeting. Isolated target on initial imagery (invasive hepatocellular carcinoma excluded) WHO (World Health organization) Performance status: 0, 1 or 2 If cirrhosis, Child A score with total bilirubin less than 30 micromoles per liter Creatinine clearance more or equal to 30 mL/min Patient informed and consent signature obtained", "candidate_expression": "((0, 1 or 2) AND (A) AND (Child score) AND (Creatinine clearance) AND (Hepatocellular Carcinoma) AND (Indication) AND (Patient informed and consent signature obtained) AND (WHO (World Health organization) Performance status) AND (cirrhosis) AND (less than 30 micromoles per liter) AND (metastatic) AND (more or equal to 30 mL/min) AND (non) AND (radioembolization) AND (total bilirubin) AND ((Early) OR (advanced) OR (intermediate)))"}
{"candidate_id": "LLM07744", "doc_id": "NCT02222272_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07745", "doc_id": "NCT02872090_exc", "case_bucket": "other", "source_criterion": "beta blocker supraventricular rhythm disorder previous history of respiratory disease other than COPD diabetes autonomic dysfunction dysautonomia renal failure long-term oxygen therapy history of psychiatric illness", "candidate_expression": "((autonomic dysfunction) AND (beta blocker) AND (diabetes) AND (dysautonomia) AND (long-term oxygen therapy) AND (psychiatric illness history) AND (renal failure) AND (respiratory disease previous history) AND (supraventricular rhythm disorder) AND NOT (COPD))"}
{"candidate_id": "LLM07746", "doc_id": "NCT01228279_inc", "case_bucket": "other", "source_criterion": "Adult (age 18 years and older) Patients with end-stage renal disease(ESRD)/chronic kidney disease(CKD)stage 5", "candidate_expression": "((Adult) AND (CKD) AND (ESRD) AND (age 18 years and older) AND (chronic kidney disease stage 5) AND (end-stage renal disease))"}
{"candidate_id": "LLM07747", "doc_id": "NCT03026088_exc", "case_bucket": "or", "source_criterion": "Acute coronary syndrome (ACS) within 3 months. Under beta-blocker treatment for the last 2 weeks. Under other medicine treatment which may affect heart rate, like Non-dihydropyridine calcium channel blockers (NDHP-CCBs) or ivabradine for the last 2 weeks; Under Digoxin treatment [more than (>) 0.125 milligram (mg)]. Uncontrolled Diabetes [hemoglobin A1c, (HbA1c) >7.5%]. Severe or uncontrolled hypertension [resting Systolic Blood Pressure (SBP) >180 millimeters of mercury (mmHg), or resting Diastolic Blood Pressure (DBP) >110mmHg at screening period]. Severe hypotension [resting SBP less than (<) 90mmHg, or resting DBP<50mmHg]. Resting heart rate <60 beat per minute (bpm). Any contradiction to Bisoprolol according to label, including: Acute heart failure or during episodes of heart failure decompensation requiring intravenous inotropic therapy. Cardiogenic shock. Atrioventricular block of second or third degree (without a pacemaker). Sick sinus syndrome. Sinoatrial block. Slowed heart rate, causing symptoms (symptomatic bradycardia), Decreased blood pressure, causing symptoms (symptomatic hypotension), Severe bronchial asthma or severe chronic obstructive pulmonary disease. Sever forms of peripheral arterial occlusive disease and Raynaud's syndrome. Untreated phaeochromocytoma. Metabolic acidosis. Hypersensitivity to bisoprolol or to any of the excipients. Severe Arrhythmia including atrial fibrillation, atrial flutter, ventricular fibrillation, ventricular flutter or ventricular tachycardia. Significant valvular heart disease, congenital heart disease, pulmonary heart disease or perinatal heart disease. Acute pulmonary edema. Severe hepatic dysfunction, defined as: Serum Alanine Aminotransferase (ALT) > triple the upper limit of the normal range; and/or Serum Aspartate Aminotransferase (AST) > triple the upper limit of the normal value range and/or Severe renal dysfunction, defined as: Serum creatinine > twice the upper limit of the normal range Chronic Kidney Disease (glomerular filtration rate <45 Milliliter per minute). Hyperthyroidism or hypothyroidism. Severe infectious disease, example (eg) Human Immunodeficiency Virus positive or active tuberculosis. Severe autoimmune disease, e.g. lupus erythematosus, multiple sclerosis. Severe respiratory, digestive, hematological disease (including Anemia of Hb < 100 gram per litre) or tumor. Known to be hypersensitivity to Bisoprolol, or any of the excipient. Substance or alcohol abuse. Received heart transplantation or pacemaker implantation; revascularization treatment within 3 months; or plan to receive above treatment in 6 months. Currently undertaking other treatment that may affect the safety and/or efficacy evaluation, e.g. beta receptors agonists, et cetera. No legal ability or legal ability is limited. Subjects unlikely to cooperate in the study or with inability or unwillingness to give informed consent. Child-bearing period women without effective contraceptive measures, pregnancy and lactation. Participation in another clinical trial within the past 90 days. Other significant condition that in the Investigator's opinion would exclude the subject from the trial.", "candidate_expression": "((ACS) AND (ALT) AND (AST) AND (Acute coronary syndrome within 3 months) AND (Acute heart failure) AND (Acute pulmonary edema) AND (Anemia) AND (Arrhythmia Severe) AND (Atrioventricular block of second degree) AND (Atrioventricular block of third degree) AND (Bisoprolol) AND (Cardiogenic shock) AND (Child-bearing period women without effective contraceptive measures, pregnancy and lactation) AND (Chronic Kidney Disease) AND (DBP) AND (DBP resting <50mmHg) AND (Diabetes Uncontrolled) AND (Diastolic Blood Pressure resting >110mmHg) AND (Digoxin more than 0.125 milligram > 0.125 mg) AND (Hb < 100 gram per litre) AND (HbA1c Severe uncontrolled) AND (Human Immunodeficiency Virus positive) AND (Hypersensitivity) AND (Hyperthyroidism) AND (Metabolic acidosis) AND (NDHP-CCBs) AND (No legal ability or legal ability is limited) AND (Non-dihydropyridine calcium channel blockers) AND (Other significant condition that in the Investigator's opinion would exclude the subject from the trial) AND (Raynaud's syndrome) AND (SBP >180 mmHg) AND (SBP resting less than 90mmHg) AND (Serum Alanine Aminotransferase > triple the upper limit of the normal range) AND (Serum Aspartate Aminotransferase > triple the upper limit of the normal value range) AND (Serum creatinine > twice the upper limit of the normal range) AND (Sick sinus syndrome) AND (Sinoatrial block) AND (Substance abuse) AND (Systolic Blood Pressure resting >180 millimeters of mercury) AND (alcohol abuse) AND (atrial fibrillation) AND (atrial flutter) AND (autoimmune disease Severe) AND (beta receptors agonists) AND (beta-blocker for the last 2 weeks) AND (bisoprolol) AND (blood pressure Decreased) AND (bradycardia symptomatic) AND (bronchial asthma Severe) AND (chronic obstructive pulmonary disease severe) AND (congenital heart disease) AND (contradiction) AND (digestive disease) AND (excipient any) AND (excipients any) AND (glomerular filtration rate <45 Milliliter per minute) AND (heart failure decompensation) AND (heart rate Resting <60 beat per minute <60 bpm) AND (heart rate Slowed) AND (heart transplantation) AND (hematological disease) AND (hemoglobin A1c >7.5%) AND (hepatic dysfunction Severe) AND (hypersensitivity) AND (hypertension) AND (hypotension Severe) AND (hypotension symptomatic) AND (hypothyroidism) AND (infectious disease Severe) AND (intravenous inotropic therapy) AND (ivabradine) AND (lupus erythematosus) AND (multiple sclerosis) AND (pacemaker implantation) AND (perinatal heart disease) AND (peripheral arterial occlusive disease) AND (phaeochromocytoma Untreated) AND (pulmonary heart disease) AND (renal dysfunction Severe) AND (respiratory disease) AND (revascularization) AND (symptoms) AND (tuberculosis active) AND (tumor) AND (ubjects unlikely to cooperate in the study or with inability or unwillingness to give informed consent) AND (valvular heart disease) AND (ventricular fibrillation) AND (ventricular flutter) AND (ventricular tachycardia) AND NOT (pacemaker))"}
{"candidate_id": "LLM07748", "doc_id": "NCT03058835_exc", "case_bucket": "or", "source_criterion": "Active alcohol or drug use or dependence which may interfere with adherence to study requirements HIV-infected at screening or enrollment Estimated CrCl < 60 mL/min Past participation in an HIV vaccine study Positive Hepatitis B surface antigen test Underlying medical condition with survival unlikely during follow-up period Any condition that in the opinion of study staff would make participation in the study unsafe or interfere with achieving study objectives Pregnant or breast feeding Actively trying to achieve pregnancy", "candidate_expression": "((< 60 mL/min) AND (Active alcohol or drug use or dependence which may interfere with adherence to study requirements) AND (Actively trying to achieve pregnanc) AND (Estimated CrCl) AND (HIV-infected) AND (Hepatitis B surface antigen test) AND (Positive) AND (Pregnant) AND (at enrollment) AND (at screening) AND (breast feeding) AND (condition) AND (interfere with achieving study objectives) AND (make participation in the study unsafe) AND (medical condition) AND (survival unlikely))"}
{"candidate_id": "LLM07749", "doc_id": "NCT02535299_inc", "case_bucket": "or", "source_criterion": "Newly dignosised type 2 diabetes according to WHO criteria.glycated hemoglobin (HbA1c) was more than 10%; Seronegative for antibodies against insulin, islet cells and glutamic acid decarboxylase (GAD);", "candidate_expression": "((glycated hemoglobin (HbA1c) more than 10%) AND (type 2 diabetes Newly dignosised WHO criteria) AND NOT (antibodies) AND ((glutamic acid decarboxylase (GAD)) OR (insulin) OR (islet cells)))"}
{"candidate_id": "LLM07750", "doc_id": "NCT03056287_inc", "case_bucket": "or", "source_criterion": "1) age 50-70 2) stroke within the past 6 to 60 months, 3) major depressive disorder (PHQ-9 > 10) and diagnosed using the Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV), 4) residual paresis in the lower extremity (Fugl-Meyer LE motor score <34), 5) ability to walk without assistance and without an AFO on the treadmill ≥ 30 seconds at speeds ranging from 0.2-0.8 m/s, 6) no antidepressant medications or clinically able to discontinue medications, 7) HRSD question #9 regarding suicide <2, 8) provision of informed consent. In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.", "candidate_expression": "((Fugl-Meyer LE motor score <34) AND (HRSD question #9 <2) AND (In addition, all subjects who meet criteria for the training portion must complete an exercise tolerance test and be cleared for participation by the study cardiologist.) AND (PHQ-9 > 10) AND (Structured Clinical Interview for Depression (SCID) according to the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV)) AND (ability to walk without assistance) AND (age 50-70) AND (clinically able to discontinue medications) AND (major depressive disorder) AND (residual paresis lower extremity) AND (stroke within the past 6 to 60 months) AND NOT (AFO on the treadmill ≥ 30 seconds speeds) AND ((clinically able to discontinue medications) OR NOT (antidepressant)))"}
```
