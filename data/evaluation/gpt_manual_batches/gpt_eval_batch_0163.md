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
{"candidate_id": "LLM04051", "doc_id": "NCT00317148_exc", "case_bucket": "or", "source_criterion": "Body mass index (BMI) of 35 kg/m2 or more. Significant metabolic and endocrine diseases. Diagnosis of cancer. Use of steroids or drugs that interfere with the metabolism of estrogen. Use of any systemic estrogen, progestin, or DHEA in the eight weeks prior to randomization. Use of alternative therapies or natural products to treat postmenopausal symptoms in the four weeks prior to randomization. Palpable fibroids or uterine prolapse: Grade 2 or 3. Cigarette smoking", "candidate_expression": "((Body mass index (BMI) 35 kg/m2 or more) AND (Cigarette smoking) AND (DHEA) AND (Grade 2 or 3) AND (Palpable fibroids) AND (alternative therapies) AND (cancer) AND (drugs that interfere with the metabolism of estrogen) AND (endocrine diseases) AND (metabolic diseases) AND (natural products) AND (postmenopausal symptoms) AND (steroids) AND (systemic estrogen) AND (systemic progestin) AND (uterine prolapse))"}
{"candidate_id": "LLM04052", "doc_id": "NCT02789111_exc", "case_bucket": "other", "source_criterion": "More than three doses of any opioid within one week of surgery Pregnancy Prisoners Unable to provide consent Emergency surgery Chronic kidney disease stage 5 (GFR < 15 ml/min) Severe hepatic impairment Recent myocardial infarction (within the last 3 months)", "candidate_expression": "((< 15 ml/min)) AND (Chronic kidney disease) AND (Emergency surgery) AND (GFR) AND (More than three doses) AND (Pregnancy) AND (Prisoners) AND (Severe) AND (Unable to provide consent) AND (hepatic impairment) AND (myocardial infarction) AND (opioid) AND (stage 5) AND (surgery) AND (the last 3 months) AND (within one week of surgery))"}
{"candidate_id": "LLM04053", "doc_id": "NCT02845427_exc", "case_bucket": "other", "source_criterion": "Revision cases Uncontrolled bleeding tendency (prothrombin conc. Less than 70%) History of deep venous thrombosis Sever liver impairment (liver failure) Sever renal impairment (S. creatinine more than 3)", "candidate_expression": "((Revision cases) AND (bleeding tendency Uncontrolled) AND (creatinine more than 3) AND (deep venous thrombosis History) AND (liver failure) AND (liver impairment Sever) AND (prothrombin Less than 70%) AND (renal impairment Sever))"}
{"candidate_id": "LLM04054", "doc_id": "NCT03113253_inc", "case_bucket": "or", "source_criterion": "Subjects undergoing burn excision surgery for standard of care purposes Male or female >= 18 years of age Subject or subject's medical decision maker agrees to participate in this study and provides informed consent", "candidate_expression": "((Male) AND (Subject or subject's medical decision maker agrees to participate in this study and provides informed consent) AND (age >= 18 years) AND (burn excision surgery undergoing) AND (female))"}
{"candidate_id": "LLM04055", "doc_id": "NCT02939872_exc", "case_bucket": "or", "source_criterion": "Contraindication to antiplatelet therapy Need to continue clopidogrel due to stroke, peripheral disease, significant carotid disease or recent acute coronary syndrome Major bleeding history or bleeding diathesis Pregnancy", "candidate_expression": "((Contraindication) AND (Pregnancy) AND (acute coronary syndrome recent) AND (antiplatelet therapy) AND (bleeding Major history) AND (bleeding diathesis) AND (carotid disease significant) AND (clopidogrel continue) AND (peripheral disease) AND (stroke))"}
{"candidate_id": "LLM04056", "doc_id": "NCT02966236_inc", "case_bucket": "scope", "source_criterion": "Complex kidney stone (staghorn calculi GUYS III and IV)", "candidate_expression": "((Complex kidney stone) AND (GUYS III and IV) AND (staghorn calculi))"}
{"candidate_id": "LLM04057", "doc_id": "NCT02632266_inc", "case_bucket": "or", "source_criterion": "Inborn preterm infants born between 28 0/7 and 34 0/7 weeks gestation and fed either mother's own milk or donor human milk", "candidate_expression": "((Inborn) AND (between 28 0/7 and 34 0/7 weeks) AND (donor human milk fed) AND (fed mother's own milk) AND (gestation) AND (infants) AND (preterm))"}
{"candidate_id": "LLM04058", "doc_id": "NCT02570321_inc", "case_bucket": "or", "source_criterion": "Corneal ulcer that is smear positive for either bacteria or filamentous fungus Pinhole visual acuity worse than 20/70 in the affected eye Not treated already with antimicrobial medications at presentation Age over 18 years Basic understanding of the study as determined by the physician Commitment to return for follow up visits", "candidate_expression": "((Age over 18 years) AND (Commitment to return for follow up visits) AND (Corneal ulcer) AND (Pinhole visual acuity worse than 20/70) AND (antimicrobial medications) AND (smear positive bacteria filamentous fungus))"}
{"candidate_id": "LLM04059", "doc_id": "NCT02464813_inc", "case_bucket": "or", "source_criterion": "Adolescent (10-21 years) undergoing spinal fusion for idiopathic scoliosis, spondylolisthesis or Scheuermann kyphosis. Posterior spinal fusion No contraindication for Pregabalin use ASA I-III Written informed consent", "candidate_expression": "((10-21 years) AND (ASA) AND (Adolescent) AND (I-III) AND (No) AND (Posterior spinal fusion) AND (Pregabalin) AND (Scheuermann kyphosis) AND (Written informed consent) AND (contraindication) AND (idiopathic scoliosis) AND (spinal fusion) AND (spondylolisthesis) AND (years))"}
{"candidate_id": "LLM04060", "doc_id": "NCT02106598_exc", "case_bucket": "or", "source_criterion": "Known pregnancy or breast-feeding. Medical illness unrelated to the tumor which in the opinion of the attending physician and principal investigator will preclude administration of the agent. This includes patients with uncontrolled infection, chronic renal insufficiency, myocardial infarction within the past 6 months, unstable angina, cardiac arrhythmias other than chronic atrial fibrillation and chronic active or persistent hepatitis, or New York Heart Association Classification III or IV heart disease.", "candidate_expression": "((Classification III or IV) AND (Medical illness unrelated to the tumor) AND (New York Heart Association) AND (other than) AND (which in the opinion of the attending physician and principal investigator will preclude administration of the agent) AND (within the past 6 months) AND ((cardiac arrhythmias) OR (chronic renal insufficiency) OR (myocardial infarction) OR (uncontrolled infection) OR (unstable angina)) AND ((breast-feeding) OR (pregnancy)) AND ((chronic active hepatitis) OR (chronic atrial fibrillation) OR (heart disease) OR (persistent hepatitis)))"}
{"candidate_id": "LLM04061", "doc_id": "NCT03236246_inc", "case_bucket": "or", "source_criterion": "Estimated glomerular filtration rate =20 mL/min and <60 mL/min Hgb =8.5 g/dL and =11.5 g/dL Serum ferritin =500 ng/mL and transferrin saturation (TSAT) =25% Serum intact parathyroid hormone =600 pg/mL", "candidate_expression": "((=20 mL/min and <60 mL/min) AND (=25%) AND (=500 ng/mL) AND (=600 pg/mL) AND (=8.5 g/dL and =11.5 g/dL) AND (Estimated glomerular filtration rate) AND (Hgb) AND (Serum ferritin) AND (Serum intact parathyroid hormone) AND (TSAT) AND (transferrin saturation))"}
{"candidate_id": "LLM04062", "doc_id": "NCT03364036_inc", "case_bucket": "or", "source_criterion": "Highly active RMS as defined by: One relapse in the previous year and at least 1 T1 Gadolinium (Gd)+ lesion or 9 or more T2 lesions, while on therapy with other disease modifying drugs (DMDs) Two or more relapses in the previous year, whether on DMD treatment or not. Expanded Disability Status Scale (EDSS) score less than equals to (<=) 5.0. Other protocol defined inclusion criteria could apply.", "candidate_expression": "((9 or more) AND (Expanded Disability Status Scale (EDSS) score) AND (Highly active) AND (One) AND (Other protocol defined inclusion criteria could apply.) AND (RMS) AND (T1 Gadolinium (Gd)+) AND (T2 lesions) AND (Two or more) AND (at least 1) AND (disease modifying drugs (DMDs)) AND (in the previous year) AND (lesion) AND (less than equals to (<=) 5.0) AND (other) AND (relapse) AND (relapses) AND (therapy) AND (while on therapy))"}
{"candidate_id": "LLM04063", "doc_id": "NCT03495557_inc", "case_bucket": "or", "source_criterion": "Age = 18 years Laparoscopic cholecystectomy Emergent/elective =2 risk factors: diabetes mellitus, age =70 years, BMI =30, fascial enlargement", "candidate_expression": "((Age = 18 years) AND (BMI =30) AND (age =70 years) AND (cholecystectomy Laparoscopic Emergent elective) AND (diabetes mellitus) AND (fascial enlargement) AND (risk factors =2))"}
{"candidate_id": "LLM04064", "doc_id": "NCT03350659_inc", "case_bucket": "or", "source_criterion": "Age >=19 patients who complained of dizziness Orthostatic hypotension after 3-minute standing (systolic blood pressure drop >=20 or diastolic blood pressure drop >=10", "candidate_expression": "((>=10) AND (>=19) AND (>=20) AND (Age) AND (Orthostatic hypotension) AND (after 3-minute standing) AND (dizziness) AND ((diastolic blood pressure drop) OR (systolic blood pressure drop)))"}
{"candidate_id": "LLM04065", "doc_id": "NCT02277041_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((after 37 weeks) AND (cesarean section) AND (gestation) AND (singleton pregnancy))"}
{"candidate_id": "LLM04066", "doc_id": "NCT03131050_inc", "case_bucket": "or", "source_criterion": "Has given written informed consent. Male or female outpatients aged at least 18 years and not more than 45 years. Has a diagnosis of major depressive disorder by Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria. Current HAMD-17 score = 20 and the duration of the index episode is greater than or equal to four weeks.", "candidate_expression": "((Current) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria) AND (HAMD-17) AND (Has given written informed consent.) AND (Male) AND (aged) AND (at least 18 years and not more than 45 years) AND (female) AND (greater than or equal to four weeks) AND (index episode) AND (major depressive disorder) AND (outpatients) AND (score = 20))"}
{"candidate_id": "LLM04067", "doc_id": "NCT03404479_inc", "case_bucket": "other", "source_criterion": "Subjects who voluntarily consented, after listening enough explanation for this study and investigational product. Adult over 50 years of age. At least one of the knee pain VAS score is 40mm or more. Patients who require medication for more than 12 weeks due to osteoarthritis symptoms. Those who are able to follow the requirements of this clinical trial, such as being able to trace during the clinical trial period and to read and write the VAS questionnaire. Those who weigh more than 40kg", "candidate_expression": "((40mm or more) AND (Adult) AND (At least one) AND (Subjects who voluntarily consented, after listening enough explanation for this study and investigational product.) AND (VAS score) AND (age) AND (knee pain) AND (medication) AND (more than 12 weeks) AND (more than 40kg) AND (osteoarthritis symptoms) AND (over 50 years) AND (weigh))"}
{"candidate_id": "LLM04068", "doc_id": "NCT01978028_exc", "case_bucket": "or", "source_criterion": "Hemochromatosis, iron overload, defined as TSAT > 45% Known hypersensitivity to Ferinject®. Known active infection, CRP>20 mg/L, clinically significant bleeding, active malignancy. Chronic liver disease and/or screening alanine transaminase (ALT) or aspartate transaminase (AST) above three times the upper limit of the normal range. Immunosuppressive therapy or renal dialysis (current or planned within the next 6 months). History of erythropoietin, i. v. or oral iron therapy, and blood transfusion in previous 12 weeks and/or such therapy planned within the next 6 months. Unstable angina pectoris as judged by the investigator, clinically significant uncorrected valvular disease or left ventricular outflow obstruction, obstructive cardiomyopathy, poorly controlled fast atrial fibrillation or flutter, poorly controlled symptomatic brady- or tachyarrhythmias. Acute myocardial infarction or acute coronary syndrome, transient ischemic attack or stroke within the last 3 months. Coronary-artery bypass graft, percutaneous intervention (e.g. cardiac, cerebrovascular, aortic; diagnostic catheters are allowed) or major surgery, including thoracic and cardiac surgery, within the last 3 months. Participation in a CHF training program. Known HIV/AIDS. Inability to fully comprehend and/or perform study procedures in the investigator's opinion. Vitamin B12 and/or serum folate deficiency according to the laboratory (re-screening is possible after substitution therapy). Pregnancy or lactation. Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study. Anticoagulation", "candidate_expression": "((AIDS) AND (Acute myocardial infarction) AND (Anticoagulation) AND (CRP >20 mg/L) AND (Chronic liver disease) AND (Coronary-artery bypass graft) AND (Ferinject®) AND (Hemochromatosis) AND (Immunosuppressive therapy) AND (Inability to fully comprehend and/or perform study procedures in the investigator's opinion) AND (Known HIV) AND (Participation in another clinical trial within previous 30 days and/or anticipated participation in another trial during this study.) AND (Pregnancy) AND (TSAT > 45%) AND (Unstable angina pectoris the next 6 months clinically significant) AND (Vitamin B12 deficiency) AND (active infection) AND (acute coronary syndrome) AND (alanine transaminase (ALT)) AND (aspartate transaminase (AST)) AND (bleeding clinically significant) AND (blood transfusion in previous 12 weeks within the next 6 months) AND (brady-) AND (cardiac surgery) AND (erythropoietin) AND (fast atrial fibrillation) AND (fast atrial flutter) AND (hypersensitivity) AND (i. v. iron therapy) AND (iron overload) AND (lactation) AND (left ventricular outflow obstruction) AND (major surgery) AND (malignancy active) AND (obstructive cardiomyopathy) AND (oral iron therapy) AND (percutaneous intervention) AND (renal dialysis current planned) AND (serum folate deficiency) AND (stroke) AND (tachyarrhythmias) AND (thoracic surgery) AND (transient ischemic attack) AND (valvular disease))"}
{"candidate_id": "LLM04069", "doc_id": "NCT02961582_inc", "case_bucket": "or", "source_criterion": "An average defecation frequency (DF) of <3 per week based on a 3-week defecation diary (patient-reported) Meet at least one other criterion of the Rome-IV criteria for idiopathic constipation based on the 3-week defecation diary (1) Refractory to conservative treatment Age: 14-80 years Straining during =25% of defecations Lumpy or hard stools in =25% of defecations Sensation of incomplete evacuation for =25% of defecations Sensation of anorectal obstruction/blockage for =25% of defecations Manual manoeuvres to facilitate =25% of defecations", "candidate_expression": "((3-week defecation diary) AND (3-week defecation diary patient-reported) AND (Age 14-80 years) AND (DF) AND (Manual manoeuvres) AND (Rome-IV criteria for idiopathic constipation) AND (Sensation of incomplete evacuation) AND (Straining) AND (average defecation frequency <3 per week) AND (conservative treatment Refractory) AND (criterion at least one other) AND (defecations =25%) AND (idiopathic constipation) AND ((Lumpy stools) OR (hard stools)) AND ((Sensation of anorectal blockage) OR (Sensation of anorectal obstruction)))"}
{"candidate_id": "LLM04070", "doc_id": "NCT03213834_inc", "case_bucket": "or", "source_criterion": "CPPE along with evidence of septated pleural effusion on pleural ultrasonography and/or chest CT scan empyema.", "candidate_expression": "((CPPE) AND (chest CT scan) AND (empyema) AND (evidence of) AND (pleural ultrasonography) AND (septated pleural effusion))"}
{"candidate_id": "LLM04071", "doc_id": "NCT02202369_exc", "case_bucket": "or", "source_criterion": "Patients with liver disease (documented liver function test abnormality) Patients with renal disease (documented glomerular filtration rate < 60mL/min/1.73m2) Patients with a baseline (pre-operative) opioid use greater than 30 mg of morphine equivalents/day. Patients with active alcohol dependence Patients with active illicit drug dependence Patients < 18 years of age and >70 years of age Patients allergic to any medication given in either arm (list medications) Patients who have a seizure disorder", "candidate_expression": "((age < 18 years) AND (age >70 years) AND (alcohol dependence) AND (allergic) AND (glomerular filtration rate < 60mL/min/1.73m2) AND (illicit drug dependence) AND (liver disease) AND (liver function test abnormality) AND (medication) AND (opioid baseline greater than 30 mg of morphine equivalents/day pre-operative) AND (renal disease) AND (seizure disorder))"}
{"candidate_id": "LLM04072", "doc_id": "NCT02959580_exc", "case_bucket": "other", "source_criterion": "Breast Carcinoma", "candidate_expression": "(Breast Carcinoma)"}
{"candidate_id": "LLM04073", "doc_id": "NCT03223909_exc", "case_bucket": "or", "source_criterion": "Subjects with topical and/or systemic medication or mechanical devices that interfere determinedly on the results of the study (such as topical immunomodulators, punctal plugs, corticosteroids, preservative artificial tears, contact lenses). Subjects (females) with active sexual life that do not use a contraceptive method. Female subjects who are pregnant or lactating Female subjects with a positive urine pregnancy test Positive drug addictions* (verbal interrogatory) Subjects who have participated on any other research clinical trials on the last 40 days Subjects legal or mentally disabled to give an informed consent for participating on this study Subjects who can't comply with the appointments or with every protocol requirement. Serious tear film dysfunction syndrome TBUT < 5 s Schirmer: < 4 mm OSDI > 30 pints Corneal staining > grade III on the Oxford scale Non perforated corneal ulcer Perforated corneal ulcer Autoimmune corneal ulcer Ocular surface scarring diseases Ocular surface or annexes metaplastic lesions Fibro vascular proliferation lesions on the conjunctival and/or corneal surface (i.e.: pterygium) Concomitant chronic inflammatory diseases on any ocular structure Acute or infectious inflammatory disease Corneal disease potentially requiring a treatment during the following 3 months Use of topical or systemic drug products classified as forbidden Ocular surgical procedures 3 months before the protocol inclusion Treatments or procedures indicated on the tear film dysfunction treatment, as punctal silicone plugs. Posterior segment diseases requiring a treatment or threatening the visual prognosis Retinal diseases potentially requiring treatment during the following 3 months History of penetrating keratoplasty. Soft or hard contact lenses use during the last month from inclusion day", "candidate_expression": "((Corneal disease) AND (Corneal staining > grade III Oxford scale) AND (Female) AND (Fibro vascular proliferation lesions conjunctival corneal surface pterygium) AND (OSDI > 30 pints) AND (Ocular surface scarring diseases) AND (Ocular surgical procedures 3 months before the protocol inclusion 3 months before the protocol inclusion) AND (Positive drug addictions) AND (Posterior segment diseases) AND (Retinal diseases) AND (Schirmer < 4 mm) AND (Serious tear film dysfunction syndrome) AND (Soft contact lenses) AND (Subjects legal or mentally disabled to give an informed consent for participating on this study) AND (Subjects who have participated on any other research clinical trials on the last 40 days) AND (TBUT < 5 s) AND (Treatments) AND (active sexual life) AND (annexes metaplastic lesions Ocular) AND (chronic inflammatory diseases Concomitant ocular structure Acute) AND (contact lenses) AND (corneal ulcer Autoimmune) AND (corneal ulcer Non perforated) AND (corneal ulcer Perforated) AND (corticosteroids) AND (females) AND (hard contact lenses) AND (inflammatory disease infectious) AND (lactating) AND (legal disabled) AND (lesions Ocular surface) AND (mechanical devices) AND (mentally disabled) AND (penetrating keratoplasty History) AND (pregnant) AND (preservative artificial tears) AND (procedures) AND (punctal plugs) AND (punctal silicone plugs) AND (systemic medication) AND (tear film dysfunction treatment) AND (threatening the visual prognosis) AND (topical immunomodulators) AND (topical medication) AND (treatment potentially requiring during the following 3 months) AND (treatment requiring) AND (treatment requiring during the following 3 months) AND (urine pregnancy test positive) AND (verbal interrogatory) AND NOT (contraceptive method))"}
{"candidate_id": "LLM04074", "doc_id": "NCT03034837_inc", "case_bucket": "other", "source_criterion": "generally healthy grade 1-2 school children with written parental consent with at least 1 sound and fully erupted permanent first molar", "candidate_expression": "((children) AND (generally healthy) AND (grade 1-2 school) AND (permanent first molar at least 1 sound fully erupted) AND (with written parental consent))"}
{"candidate_id": "LLM04075", "doc_id": "NCT03262038_inc", "case_bucket": "or", "source_criterion": "3-17 years weight </= 100kg scheduled for urologic or orthopedic procedure necessitating intrathecal morphine ability to use verbal or pictorial pain assessment tools and techniques informed consent and (if applicable) assent", "candidate_expression": "((3-17 years) AND (</= 100kg) AND (ability) AND (informed consent and (if applicable) assent) AND (intrathecal) AND (morphine) AND (weight) AND ((pictorial pain assessment tools and techniques) OR (verbal pain assessment tools and techniques)) AND ((orthopedic procedure) OR (urologic procedure)))"}
```
