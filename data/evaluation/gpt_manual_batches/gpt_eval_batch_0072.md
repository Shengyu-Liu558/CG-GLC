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
{"candidate_id": "LLM01776", "doc_id": "NCT02780427_inc", "case_bucket": "other", "source_criterion": "Children, aged between one and 24 months. classified as (American Society of Anesthesiologists) ASA physical status I or II, undergoing TEE were enrolled in the study.", "candidate_expression": "((ASA physical status I or II) AND (American Society of Anesthesiologists) AND (Children) AND (TEE) AND (aged between one and 24 months))"}
{"candidate_id": "LLM01777", "doc_id": "NCT02361905_inc", "case_bucket": "other", "source_criterion": "hypoechoic uterine leiomyoma (echogenicity <3), intramural leiomyomas with an ultrasonographic size <20 cm but >4cm, indication to surgery (symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain or pelvic pressure", "candidate_expression": "((echogenicity <3) AND (infertility) AND (intramural leiomyomas) AND (menometrorrhagia) AND (menstrual disorder) AND (pelvic pain) AND (pelvic pressure) AND (surgery indication to) AND (ultrasonographic size <20 cm but >4cm) AND (uterine leiomyoma hypoechoic))"}
{"candidate_id": "LLM01778", "doc_id": "NCT02833116_inc", "case_bucket": "or", "source_criterion": "Unilateral leg pain secondary to lateral stenosis, disc protrusion or herniated disc. Age between 18 and 80 years. Moderate to severe pain (NVS>4). Right proficient oral and written language.", "candidate_expression": "((Age between 18 and 80 years) AND (NVS >4)) AND (Right proficient oral and written language) AND (Unilateral leg pain) AND (disc protrusion) AND (herniated disc) AND (lateral stenosis) AND (pain Moderate severe))"}
{"candidate_id": "LLM01779", "doc_id": "NCT02303171_inc", "case_bucket": "other", "source_criterion": "Pregnant women with APS diagnosed according to the revised classification criteria for APS in 2006 in Sydney, Australia Early pregnancy body weight is 50-90 Kg", "candidate_expression": "((50-90 Kg) AND (APS) AND (Early pregnancy) AND (Pregnant) AND (body weight) AND (revised classification criteria for APS in 2006 in Sydney, Australia) AND (women))"}
{"candidate_id": "LLM01780", "doc_id": "NCT02186782_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulation/oligoovulation. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Metabolic or hormonal abnormalities.", "candidate_expression": "((Age) AND (BMI) AND (Body mass index) AND (cytotoxic drugs) AND (infertility factor) AND (one) AND (other than) AND (ovary) AND (pelvic irradiation) AND ((anovulation) OR (oligoovulation)) AND ((ovarian surgery) OR (surgical removal)) AND ((< 20) OR (> 35 years)) AND ((Metabolic abnormalities) OR (hormonal abnormalities)) AND ((< 18.5 kg/m2) OR (> 25 kg/m2)))"}
{"candidate_id": "LLM01781", "doc_id": "NCT02777580_exc", "case_bucket": "or", "source_criterion": "1. Expected performance of PCI < 60 minutes from diagnosis (qualifying ECG) or inability to arrive at the catheterisation laboratory within 3 hours Previous CABG Left bundle branch block or ventricular pacing Patients with cardiogenic shock - Killip Class 4 Patients with a body weight < 55 kg (known or estimated) Uncontrolled hypertension, defined as sustained blood pressure = 180/110 mm Hg (systolic BP = 180 mm Hg and/or diastolic BP = 110 mm Hg) prior to randomisation Known prior stroke or TIA Recent administration of any i.v. or s.c. anticoagulation within 12 hours, including unfractionated heparin, enoxaparin, and/or bivalirudin or current use of oral anticoagulation (i.e. warfarin or a NOACs) Active bleeding or known bleeding disorder/diathesis Known history of central nervous system damage (i.e. neoplasm, aneurysm, intracranial or spinal surgery) or recent trauma to the head or cranium (i.e. < 3 months) Major surgery, biopsy of a parenchymal organ, or significant trauma within the past 2 months (this includes any trauma associated with the current myocardial infarction) Clinical diagnosis associated with increased risk of bleeding including known active peptic ulceration and/or neoplasm with increased bleeding risk Prolonged cardiopulmonary resuscitation (> 2 minutes) within the past 2 weeks Known acute pericarditis and/or subacute bacterial endocarditis Known acute pancreatitis or known severe hepatic dysfunction, including hepatic failure, cirrhosis, portal hypertension (oesophageal varices) and active hepatitis Dementia Known severe renal insufficiency Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days Known allergic reactions to tenecteplase, clopidogrel, enoxaparin and aspirin Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated.", "candidate_expression": "((Active bleeding) AND (CABG) AND (Dementia) AND (Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated) AND (Killip Class 4) AND (Left bundle branch block) AND (Major surgery) AND (NOACs) AND (PCI < 60 minutes from diagnosis) AND (Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days) AND (TIA) AND (active hepatitis) AND (acute pancreatitis) AND (acute pericarditis) AND (allergic reactions) AND (aneurysm) AND (anticoagulation within 12 hours) AND (aspirin) AND (biopsy parenchymal organ) AND (bivalirudin) AND (bleeding disorder) AND (blood pressure = 180/110 mm Hg) AND (body weight < 55 kg) AND (cardiogenic shock) AND (cardiopulmonary resuscitation Prolonged past 2 weeks) AND (central nervous system damage) AND (cirrhosis) AND (clopidogrel) AND (diastolic BP = 110 mm Hg) AND (diathesis) AND (enoxaparin) AND (hepatic dysfunction severe) AND (hepatic failure) AND (hypertension Uncontrolled) AND (intracranial surgery) AND (myocardial infarction) AND (neoplasm) AND (oesophageal varices) AND (oral anticoagulation) AND (peptic ulceration active) AND (portal hypertension) AND (renal insufficiency severe) AND (risk of bleeding increased) AND (spinal surgery) AND (stroke) AND (subacute bacterial endocarditis) AND (systolic BP = 180 mm Hg) AND (tenecteplase) AND (trauma < 3 months head cranium) AND (trauma significant) AND (unfractionated heparin) AND (ventricular pacing) AND (warfarin))"}
{"candidate_id": "LLM01782", "doc_id": "NCT01929434_exc", "case_bucket": "or", "source_criterion": "Intracranial infection. Severe respiratory and circulatory system diseases. Hematologic malignancies. Positive serological tests such as AIDS, hepatitis B virus, hepatitis C virus and syphilis （antigen or antibody）. Tumors. Genetic and metabolic diseases.", "candidate_expression": "((AIDS) AND (Genetic diseases) AND (Hematologic malignancies) AND (Intracranial infection) AND (Tumors) AND (circulatory system disease) AND (hepatitis B virus) AND (hepatitis C virus) AND (metabolic diseases) AND (respiratory system disease) AND (syphilis))"}
{"candidate_id": "LLM01783", "doc_id": "NCT03208244_exc", "case_bucket": "other", "source_criterion": "Sensitization (i.e. PRA >20%) Any liver disease in recipient Albumin < 3g/dl or platelet count < 75 x 103/mL Need for dual organ transplant", "candidate_expression": "((Albumin < 3g/dl) AND (PRA >20%) AND (Sensitization) AND (dual organ transplant Need for) AND (liver disease) AND (platelet count < 75 x 103/mL))"}
{"candidate_id": "LLM01784", "doc_id": "NCT00305097_inc", "case_bucket": "other", "source_criterion": "Aged at least 18 years with an ability and willingness to give written informed consent. Body mass index 25-35 kg/m2 Users of at least 2 cups of caffeinated coffee per day who are willing to be randomized to any of the interventions. Non-smoking", "candidate_expression": "((25-35 kg/m2) AND (Aged) AND (Body mass index) AND (Non-smoking) AND (ability to give written informed consent) AND (at least 18 years) AND (at least 2 cups per day) AND (caffeinated coffee) AND (willing to be randomized) AND (willingness to give written informed consent))"}
{"candidate_id": "LLM01785", "doc_id": "NCT03275584_exc", "case_bucket": "or", "source_criterion": "Pregnant women Claustrophobic patient unable to undergo the examination Breastfeeding women unwilling to temporarily stop breastfeeding Patient with contra-indication to: dipyridamole, aminophylline, dobutamine or exercise stress test (depending on the method of cardiovascular stress test chosen)", "candidate_expression": "((Claustrophobic) AND (Pregnant) AND (aminophylline) AND (contra-indication) AND (dipyridamole) AND (dobutamine) AND (exercise stress test) AND (women) AND NOT (examination))"}
{"candidate_id": "LLM01786", "doc_id": "NCT02200978_exc", "case_bucket": "or", "source_criterion": "Patients who have coma, convulsion or paralysis due to intracranial hemorrhage or central nervous system leukemia at diagnosis.", "candidate_expression": "(((coma) OR (convulsion) OR (paralysis)) AND ((intracranial hemorrhage) OR (leukemia central nervous system)))"}
{"candidate_id": "LLM01787", "doc_id": "NCT02360631_inc", "case_bucket": "other", "source_criterion": "Self-identified African American Smokes = 1 cigarette per day (cpd) Smoke on = 25 days of the past 30 days Functioning telephone Interested in quitting smoking Interested in taking 3 months of varenicline Willing to complete all study visits", "candidate_expression": "((African American) AND (Interested in quitting smoking) AND (Interested in taking 3 months of varenicline) AND (Smoke = 25 days of the past 30 days) AND (Smokes = 1 cigarette per day) AND (Willing to complete all study visits) AND (quitting smoking Interested))"}
{"candidate_id": "LLM01788", "doc_id": "NCT03382106_inc", "case_bucket": "other", "source_criterion": "Between the age of 25 to 65 at baseline Be willing to participate in a smoking cessation program Be willing to attend all clinic visits Must be currently smoking at least ½ pack/day at baseline (confirmed with cotinine level and CO Smokerlyzer >5 pack-year history of smoking Global Initiative for Chronic Obstructive Lung Disease (GOLD) 0: FEV1=0.80 and FEV1/FVC>0.70 Forced Expiratory Volume in 1 second (FEV1), Forced Vital Capacity (FVC) GOLD 1: FEV1=0.80 and FEV1/FVC < 0.70 GOLD 2: 0.50=FEV1<0.80 and FEV1/FVC < 0.70 Be willing to abstain from using any nicotine patches, e-cigarettes, or marijuana for the duration of the study.", "candidate_expression": "((0) AND (0.50= <0.80) AND (1) AND (2) AND (< 0.70) AND (=0.80) AND (>0.70) AND (>5) AND (Between 25 to 65) AND (CO Smokerlyzer) AND (FEV1) AND (FEV1/FVC) AND (GOLD) AND (Global Initiative for Chronic Obstructive Lung Disease (GOLD)) AND (age) AND (at baseline) AND (at least ½) AND (cotinine level) AND (pack-year) AND (pack/day) AND (smoking) AND (smoking cessation program) AND (willing to participate))"}
{"candidate_id": "LLM01789", "doc_id": "NCT01581749_exc", "case_bucket": "or", "source_criterion": "implanted hardware or other material that would prohibit treatment planning or delivery chemotherapy for a malignancy within the previous 5 years history of an invasive malignancy (other than this prostate cancer,or basal or squamous skin cancers) within prior 5 years hormone ablation for 2 months prior to treatment or during treatment", "candidate_expression": "((basal skin cancers) AND (chemotherapy) AND (during treatment) AND (for 2 months prior to treatment) AND (hormone ablation) AND (invasive malignancy) AND (malignancy) AND (other than) AND (prostate cancer) AND (squamous skin cancers) AND (treatment) AND (within prior 5 years) AND (within the previous 5 years))"}
{"candidate_id": "LLM01790", "doc_id": "NCT02995291_inc", "case_bucket": "other", "source_criterion": "18 years of age or older capable of providing informed consent", "candidate_expression": "((18 years of or older) AND (age) AND (capable of providing informed consent))"}
{"candidate_id": "LLM01791", "doc_id": "NCT02330757_inc", "case_bucket": "scope", "source_criterion": "Women without PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((PCOS) AND (Rotterdam criteria) AND (at least 2) AND (cleavage-stage embryo) AND (cleavage-stage embryos) AND (cryopreserved) AND (few to no cytoplasmic fragments) AND (good quality) AND (have blastomeres of fairly equal size) AND (stage-specific cell division) AND (without))"}
{"candidate_id": "LLM01792", "doc_id": "NCT02571881_exc", "case_bucket": "or", "source_criterion": "age less than 18 years allergy to study drugs substance misuse other contraindication to used study drugs no informed consent", "candidate_expression": "((age less than 18 years) AND (allergy) AND (contraindication) AND (study drugs) AND (substance misuse))"}
{"candidate_id": "LLM01793", "doc_id": "NCT03249311_exc", "case_bucket": "or", "source_criterion": "Lifetime personal history of diagnosis of major depressive disorder according to the DSM-V (American Psychiatric Association, 2013) using the Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition (SCID-5-RV for DSM-V; First et al., 2015) A history of suicidal ideation and behaviour, including self-harm and/or harm to others. A history of substance abuse and/or dependence. A positive drug screen for illicit drugs Substantial alcohol use Current use of Monoamine Oxidase Inhibitors (MAOIs), including the antibiotic linezolid and the thiazine dye methylthioninium chloride (methylene blue) Current use of serotonin-precursors (such as L-tryptophan, oxitriptan) Current use of serotonergic drugs (triptans, certain tricyclic antidepressants, lithium, tramadol, St. John's Wort) Concomitant use of NSAIDS, ASA, and other anticoagulants. Current use of Thioridazine Current use of CYP1A2 Inhibitors Current use of Triptans (5HT1 Agonists) Blood pressure greater than 140/90 and/or a pulse rate greater than 90 bpm Recent history of myocardial infarction, cerebrovascular accident, cardiac arrhythmias, or unstable heart disease. Evidence of significant physical illness contraindicating the use of levomilnacipran and duloxetine found on the physical exam or in the laboratory data obtained during the first week of the study Current use of medication that may affect voiding (ie- anticholinergics) History of obstructive urinary disorders and dysuria, prostatic hypertrophy, prostatitis, and other lower urinary tract obstructive disorders. History of Stevens-Johnson Syndrome and Erythema multiforme. Diabetes Type I and II Fructose intolerance, glucose-galactose malabsorption or sucrose-isomaltase insufficiency. Hepatic Impairment Uncontrolled narrow-angle glaucoma Severe renal impairment History of seizure disorder Anatomically narrow ocular angles. Osteoporosis or major risk for bone fractures.", "candidate_expression": "((5HT1 Agonists) AND (ASA) AND (Anatomically narrow ocular angles) AND (Blood pressure) AND (CYP1A2 Inhibitors) AND (Concomitant) AND (Current) AND (DSM-V) AND (Diabetes Type I) AND (Diabetes Type II) AND (Erythema multiforme) AND (Fructose intolerance) AND (Hepatic Impairment) AND (History) AND (L-tryptophan) AND (Monoamine Oxidase Inhibitors (MAOIs)) AND (NSAIDS) AND (Osteoporosis) AND (Recent) AND (Severe) AND (St. John's Wort) AND (Stevens-Johnson Syndrome) AND (Structured Clinical Interview for DSM-V Axis I Disorders, Research Version, Non-patient Edition) AND (Substantial alcohol use) AND (Thioridazine) AND (Triptans) AND (Uncontrolled) AND (affect voiding) AND (antibiotic linezolid) AND (anticholinergics) AND (anticoagulants) AND (bone fractures) AND (cardiac arrhythmias) AND (cerebrovascular accident) AND (contraindicating) AND (drug screen for illicit drugs) AND (duloxetine) AND (during the first week of the study) AND (dysuria) AND (glucose-galactose malabsorption) AND (greater than 140/90) AND (greater than 90 bpm) AND (harm to others) AND (history) AND (laboratory) AND (levomilnacipran) AND (lithium) AND (lower urinary tract obstructive disorders) AND (major depressive disorder) AND (major risk) AND (medication) AND (methylene blue) AND (methylthioninium chloride) AND (myocardial infarction) AND (narrow-angle glaucoma) AND (obstructive urinary disorders) AND (other) AND (oxitriptan) AND (physical exam) AND (physical illness) AND (positive) AND (prostatic hypertrophy) AND (prostatitis) AND (pulse rate) AND (renal impairment) AND (seizure disorder) AND (self-harm) AND (serotonergic drugs) AND (serotonin-precursors) AND (substance abuse) AND (substance dependence) AND (sucrose-isomaltase insufficiency) AND (suicidal behaviour) AND (suicidal ideation) AND (thiazine dye) AND (tramadol) AND (tricyclic antidepressant) AND (triptans) AND (unstable heart disease))"}
{"candidate_id": "LLM01794", "doc_id": "NCT01770340_inc", "case_bucket": "or", "source_criterion": "Localized intermediate-risk or high-risk prostate cancer cT3 Gleason score = 7 (3+4 and/or 4+3) and/or PSA = 20 ng/ml intact preoperative erectile function with an IIEF = 21 (IIEF-6).", "candidate_expression": "((Gleason score = 7 3+4) AND (IIEF = 21) AND (IIEF-6) AND (PSA = 20 ng/ml 4+3) AND (intact erectile function preoperative) AND (prostate cancer cT3 intermediate-risk high-risk))"}
{"candidate_id": "LLM01795", "doc_id": "NCT03043495_exc", "case_bucket": "or", "source_criterion": "Coagulopathies (with prothrombin concentration less than 60% or INR more than 1.5) In-ability to postpone anti-coagulation medications. Infection or injury or a lesion at the block site. Suspected cervical vertebral column injury necessitating using a neck collar. A compromised lung on the contralateral side of the block (Pneumothorax, hemothorax or Pneumonectomy). Traumatic vascular injuries or operative interventions (Surgical harvesting) involving arteries of the upper limb on the operative side. Patients with communication difficulties. Hypersensitivity to local anesthetics and/or Dexamethasone. Patients on perioperative intravenous (IV) steroids.", "candidate_expression": "((Coagulopathies) AND (Hypersensitivity) AND (Surgical harvesting) AND (anti-coagulation medications In-ability to postpone) AND (cervical vertebral column injury Suspected) AND (communication difficulties) AND (compromised lung contralateral side of the block) AND (intravenous (IV) steroids perioperative) AND ((Pneumonectomy) OR (Pneumothorax) OR (hemothorax)) AND ((Traumatic vascular injuries) OR (operative interventions)) AND ((Dexamethasone) OR (local anesthetics)) AND ((INR more than 1.5) OR (prothrombin concentration less than 60%)) AND ((Infection) OR (injury) OR (lesion)))"}
{"candidate_id": "LLM01796", "doc_id": "NCT02749617_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of multiple myeloma according to criteria of the International Myeloma Working Group Patients in whom a LEN-DEX-based treatment regimen is indicated Adult patients ≥ 19 years of age who are able to freely provide informed consent", "candidate_expression": "((Adult) AND (DEX) AND (LEN) AND (able to freely provide informed consent) AND (age ≥ 19 years) AND (criteria of the International Myeloma Working Group) AND (multiple myeloma) AND (treatment regimen LEN-DEX-based is indicated))"}
{"candidate_id": "LLM01797", "doc_id": "NCT03282006_exc", "case_bucket": "or", "source_criterion": "Bacterial infection origin from another organ (e.g. pneumonia) Severe sepsis with multiorgan failure Perinephritic abscess Pyonephrosis requiring drainage Allergy to pivmecillinam E.coli isolate resistant to pivmecillinam Pregnancy/breastfeeding Severe neutropenia Prostatitis Severe kidney failure (eGFR<15 ml/min) Using valproate", "candidate_expression": "((Allergy) AND (Bacterial infection another organ) AND (E.coli isolate resistant to pivmecillinam) AND (Perinephritic abscess) AND (Prostatitis) AND (Pyonephrosis) AND (Severe sepsis) AND (drainage requiring) AND (eGFR <15 ml/min) AND (kidney failure Severe) AND (multiorgan failure) AND (neutropenia Severe) AND (pivmecillinam) AND (pneumonia) AND (valproate) AND ((Pregnancy) OR (breastfeeding)))"}
{"candidate_id": "LLM01798", "doc_id": "NCT02380118_inc", "case_bucket": "other", "source_criterion": "Accident & Emergency Department patients, requiring parenteral drug sedation (as determined by an emergency clinician) will be enrolled.", "candidate_expression": "((Accident & Emergency Department) AND (parenteral drug sedation) AND (requiring))"}
{"candidate_id": "LLM01799", "doc_id": "NCT01349413_inc", "case_bucket": "other", "source_criterion": "Patients with functional dyspepsia that fulfill Rome III criteria with inadequate relief of dyspeptic symptoms Age >18 Provision of written consent", "candidate_expression": "((>18) AND (Age) AND (Provision of written consent) AND (Rome III criteria) AND (dyspeptic symptoms) AND (functional dyspepsia) AND (inadequate relief))"}
{"candidate_id": "LLM01800", "doc_id": "NCT01322464_inc", "case_bucket": "or", "source_criterion": "Healthy males between 18 and 45 years of age (inclusive). Body mass index to be between 18 to 30 kg/m2 (inclusive) as calculated by weight(Kg)/height(m2). Subjects were to have no clinically significant abnormal findings on physical examination, ECG, medical history, or clinical laboratory results during screening. Subjects were to, in the opinion of the investigator, have no clinically significant abnormal findings of renal and hepatic function as determined by serum creatinine, total bilirubin, and transaminase levels. Subjects were to be non-users of tobacco products (minimum of 6 months prior to the start of the study). Subjects were to have a negative screen for HIV I and II, HBsAg, and antibody to Hepatitis C virus. Subjects were to have a negative urine screen for alcohol, drugs of abuse (screening only), and cotinine. Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug. Subjects were able to comply with the protocol and the restrictions and assessments therein. Subjects were to give voluntary written informed consent to participate in the trial.", "candidate_expression": "((Body mass index between 18 to 30 kg/m2) AND (ECG) AND (HBsAg negative) AND (Healthy) AND (Subjects were able to comply with the protocol and the restrictions and assessments therein.) AND (Subjects were to give voluntary written informed consent to participate in the trial) AND (Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug.) AND (age between 18 and 45 years) AND (antibody to Hepatitis C virus negative) AND (clinical laboratory) AND (hepatic function) AND (in the opinion of the investigator) AND (medical history) AND (physical examination) AND (renal function) AND (screen for HIV I negative) AND (screen for HIV II negative) AND (serum creatinine) AND (total bilirubin) AND (transaminase levels) AND (urine screen for alcohol negative) AND (urine screen for cotinine negative) AND (urine screen for drugs of abuse negative) AND NOT (abnormal findings clinically significant) AND NOT (users of tobacco products minimum of 6 months prior to the start of the study the start of the study) AND NOT (abnormal findings clinically significant during screening))"}
```
