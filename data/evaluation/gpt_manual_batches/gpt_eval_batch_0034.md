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
{"candidate_id": "LLM00826", "doc_id": "NCT03064568_inc", "case_bucket": "other", "source_criterion": "Female age 20-50 y/o who plan to undergo abdominal myomectomy for symptomatic myomatous uterus", "candidate_expression": "((Female) AND (abdominal myomectomy plan to undergo) AND (age 20-50 y/o) AND (myomatous uterus symptomatic))"}
{"candidate_id": "LLM00827", "doc_id": "NCT03159507_exc", "case_bucket": "or", "source_criterion": "Allergy known to fish Pregnant women who breast-feed or test positive for pregnancy", "candidate_expression": "((Allergy) AND (Pregnant) AND (breast-feed) AND (fish) AND (test for pregnancy positive) AND (women))"}
{"candidate_id": "LLM00828", "doc_id": "NCT03134196_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00829", "doc_id": "NCT03173092_inc", "case_bucket": "other", "source_criterion": "Participants must have completed 3 cycles of a bortezomib-based induction regimen (as defined by current NCCN guidelines) and have no evidence of disease progression as defined by IMWG criteria. Participants with light chain and free light chain (FLC) only may be enrolled if they meet all the criteria for a diagnosis of MM. Participants must be considered by their physician eligible to receiving the IRD regimen. Eastern Cooperative Oncology Group (ECOG) performance status and/or other performance status 0, 1, or 2 at time of enrollment.", "candidate_expression": "((0, 1, or 2) AND (3 cycles) AND (Eastern Cooperative Oncology Group (ECOG) performance status) AND (IMWG criteria) AND (IRD regimen) AND (NCCN guidelines) AND (all) AND (at time of enrollment) AND (bortezomib) AND (criteria for a diagnosis of MM) AND (eligible to) AND (induction regimen) AND (light chain and free light chain (FLC)) AND (no evidence of disease progression))"}
{"candidate_id": "LLM00830", "doc_id": "NCT03026465_exc", "case_bucket": "or", "source_criterion": "Target lesion located in the left main stem STEMI Restenosis Cardiogenic shock Malignancies or other comorbid conditions with life expectancy less than 12 months or that may result in protocol noncompliance Known allergy to the study medications (probucol, sirolimus, zotarolimus) Pregnancy (present, suspected, or planned)", "candidate_expression": "((Cardiogenic shock) AND (Malignancies) AND (Pregnancy present suspected planned) AND (Restenosis) AND (STEMI) AND (Target lesion left main stem) AND (allergy) AND (comorbid conditions other) AND (life expectancy less than 12 months) AND (probucol) AND (protocol noncompliance may) AND (sirolimus) AND (study medications) AND (zotarolimus))"}
{"candidate_id": "LLM00831", "doc_id": "NCT03080493_inc", "case_bucket": "other", "source_criterion": "15 weeks 0 days gestational age - 23 weeks 5 days gestational age at time of dilator insertion Able to read and write in English Active cell phone with text messaging capability Ride home from dilator insertion clinic appointment", "candidate_expression": "((Able to read and write in English) AND (Active cell phone with text messaging capability) AND (Ride home) AND (dilator insertion) AND (gestational age 15 weeks 0 days - 23 weeks 5 days at time of dilator insertion))"}
{"candidate_id": "LLM00832", "doc_id": "NCT02650388_inc", "case_bucket": "or", "source_criterion": "Age = 75 years, Severe, symptomatic aortic stenosis, High risk for cardiac surgery (STS and logistic Euroscore ), According multidisciplinary (heart) team decision TAVI is preferable, Willing to participate", "candidate_expression": "((= 75 years) AND (Age) AND (High risk) AND (STS) AND (Severe) AND (Willing to participate) AND (aortic stenosis) AND (cardiac surgery) AND (logistic Euroscore) AND (symptomatic))"}
{"candidate_id": "LLM00833", "doc_id": "NCT03196843_exc", "case_bucket": "or", "source_criterion": "Patients with a history of any other malignancy. Concomitant treatment with any other anticancer therapy. Patient have contraindication to chemotherapy(eg.uncontrolled coronarism and heart failure; History of myocardial infarction within the past 6 months, Chronic obstructive pulmonary, uncontrolled epileptic attack and other disease that investigator consider it unsuitable for the chemotherapy)", "candidate_expression": "((Chronic obstructive pulmonary) AND (anticancer therapy any other) AND (chemotherapy) AND (contraindication) AND (coronarism) AND (disease other) AND (epileptic attack uncontrolled) AND (heart failure) AND (malignancy history any other) AND (myocardial infarction History within the past 6 months) AND (treatment Concomitant) AND (unsuitable for the chemotherapy))"}
{"candidate_id": "LLM00834", "doc_id": "NCT03012984_exc", "case_bucket": "or", "source_criterion": "Preoperative history of schizophrenia, epilepsy, parkinsonism or myasthenia gravis; Preoperative radio- or chemotherapy; Inability to communicate in the preoperative period because of coma, profound dementia or language barrier; Preoperative obstructive sleep apnea (previously diagnosed as obstructive sleep apnea, or a STOP-Bang score >= 3); Brain trauma or neurosurgery; Preoperative left ventricular ejection fraction < 30%, sick sinus syndrome, severe sinus bradycardia (< 50 beats per minute), or second-degree or above atrioventricular block without pacemaker; Severe hepatic dysfunction (Child-Pugh class C) or severe renal dysfunction (requirement of renal replacement therapy before surgery); ASA classification >= IV.", "candidate_expression": "((ASA classification >= IV) AND (Brain trauma) AND (Child-Pugh class C) AND (Inability to communicate preoperative period) AND (STOP-Bang score >= 3) AND (atrioventricular block second-degree or above) AND (chemotherapy) AND (coma) AND (dementia profound) AND (epilepsy) AND (hepatic dysfunction Severe) AND (language barrier) AND (left ventricular ejection fraction Preoperative < 30%) AND (myasthenia gravis) AND (neurosurgery) AND (obstructive sleep apnea) AND (obstructive sleep apnea Preoperative) AND (parkinsonism) AND (renal dysfunction severe) AND (renal replacement therapy before surgery) AND (schizophrenia) AND (sick sinus syndrome) AND (sinus bradycardia severe < 50 beats per minute) AND (surgery) AND (therapy radio) AND NOT (pacemaker))"}
{"candidate_id": "LLM00835", "doc_id": "NCT01642875_inc", "case_bucket": "or", "source_criterion": "Primary periampullary tumor R0, R1 resection Chronic pancreatitis requiring pancreatoduodenectomy", "candidate_expression": "((Chronic pancreatitis requiring) AND (R0 resection) AND (R1 resection) AND (pancreatoduodenectomy) AND (periampullary tumor Primary))"}
{"candidate_id": "LLM00836", "doc_id": "NCT00959569_exc", "case_bucket": "other", "source_criterion": "previous unusual response to esmolol inclusion in other randomized studies esmolol administration in the previous 30 days emergency operation", "candidate_expression": "((esmolol) AND (esmolol in the previous 30 days) AND (inclusion in other randomized studies) AND (operation emergency) AND (unusual response))"}
{"candidate_id": "LLM00837", "doc_id": "NCT01581749_exc", "case_bucket": "or", "source_criterion": "implanted hardware or other material that would prohibit treatment planning or delivery chemotherapy for a malignancy within the previous 5 years history of an invasive malignancy (other than this prostate cancer,or basal or squamous skin cancers) within prior 5 years hormone ablation for 2 months prior to treatment or during treatment", "candidate_expression": "((chemotherapy within the previous 5 years) AND (hormone ablation) AND (invasive malignancy) AND (malignancy) AND ((during treatment treatment) OR (for 2 months prior to treatment treatment)) AND ((basal skin cancers) OR (prostate cancer) OR (squamous skin cancers)))"}
{"candidate_id": "LLM00838", "doc_id": "NCT02905734_exc", "case_bucket": "other", "source_criterion": "Lack of understanding of the study contra-indication to nicotine replacement therapy health status incompatible with detention in police cells serious mental disorder usual place of residence outside Seine-Saint-Denis", "candidate_expression": "((Lack of understanding of the study) AND (contra-indication) AND (incompatible with detention in police cells) AND (nicotine replacement therapy) AND (outside Seine-Saint-Denis) AND (place of residence) AND (serious mental disorder))"}
{"candidate_id": "LLM00839", "doc_id": "NCT02631512_inc", "case_bucket": "or", "source_criterion": "Type I or II diabetes mellitus. Target ulcer area between 0.5 and 5 sqcm, and more than 4 weeks old. Ankle-brachial pressure index above 0.7.", "candidate_expression": "((Ankle-brachial pressure index above 0.7) AND (Target ulcer area between 0.5 and 5 sqcm more than 4 weeks old) AND (Type I diabetes mellitus) AND (Type II diabetes mellitus))"}
{"candidate_id": "LLM00840", "doc_id": "NCT00867958_exc", "case_bucket": "or", "source_criterion": "1. Patient has an allergy to nickel. 2. Patient has a diagnosis of bowel obstruction, bowel strangulation, peritonitis, bowel perforation, local or systemic infection, ischemic bowel, carcinomatosis or extensively spread inflammatory bowel disease. 3. Patient is participating in another clinical trial which may affect this study's outcomes. 4. Patient has been taking regular steroid medication. 5. Patient has contraindications to general anesthesia. 6. Patient has preexisting sphincter problems or evidence of extensive local disease in the pelvis.", "candidate_expression": "((Patient is participating in another clinical trial which may affect this study's outcomes.) AND (allergy to nickel) AND (contraindications to general anesthesia) AND (general anesthesia) AND (nickel) AND (steroid medication regular) AND ((local disease in the pelvis evidence of extensive) OR (sphincter problems)) AND ((bowel obstruction) OR (bowel perforation) OR (bowel strangulation) OR (carcinomatosis) OR (inflammatory bowel disease extensively spread) OR (ischemic bowel) OR (local infection) OR (peritonitis) OR (systemic infection)))"}
{"candidate_id": "LLM00841", "doc_id": "NCT03356834_exc", "case_bucket": "or", "source_criterion": "Co-infected with HCV, HIV or other viral hepatitis, Diagnosis of HCC", "candidate_expression": "((Co-infected) AND (HCC) AND (HCV) AND (HIV) AND (other) AND (viral hepatitis))"}
{"candidate_id": "LLM00842", "doc_id": "NCT01822262_inc", "case_bucket": "other", "source_criterion": "Clinical diagnosis of calculous cholecystitis.", "candidate_expression": "((Clinical diagnosis) AND (calculous cholecystitis))"}
{"candidate_id": "LLM00843", "doc_id": "NCT03445949_inc", "case_bucket": "scope", "source_criterion": "successful left atrial appendage occlusion with Amulet device within 37 days prior to randomization. treatment with dual antiplatelet therapy (clopidogrel and acetylsalicylic acid) between left atrial appendage closure and randomization participant's age 18 years or older at the time of signing the informed consent form participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable participant is willing to sign the study informed consent form", "candidate_expression": "((Amulet device) AND (acetylsalicylic acid between left atrial appendage closure and randomization left atrial appendage closure) AND (age 18 years or older at the time of signing the informed consent form) AND (clopidogrel) AND (dual antiplatelet therapy) AND (left atrial appendage closure randomization) AND (left atrial appendage occlusion successful within 37 days prior to randomization) AND (participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable) AND (participant is willing to sign the study informed consent form))"}
{"candidate_id": "LLM00844", "doc_id": "NCT01794793_inc", "case_bucket": "other", "source_criterion": "Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives Patient is currently benefiting from the treatment with pasireotide, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness", "candidate_expression": "((Patient is currently participating in a Novartis Oncology sponsored study receiving pasireotide (LAR and/or s.c.) and has fulfilled all required assessments in the parent study (unless the study is being terminated) and patients that are benefiting from the study drug have no other alternatives) AND (Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures) AND (Written informed consent obtained prior to enrolling in roll-over study and receiving study medication • If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness))"}
{"candidate_id": "LLM00845", "doc_id": "NCT01774019_inc", "case_bucket": "or", "source_criterion": "Age 18 or older Willing and able to comply with the study procedures and provide written informed consent to participate in the study Diagnosis of probable pancreatic cancer, distal common bile duct (CBD) cholangiocarcinoma and other periampullary cancers (histology not required) Biliary obstructive symptoms or signs Bilirubin level at/above 100 umol per liter (5.8 mg/dL) Distal biliary obstruction consistent with pancreatic cancer, distal CBD cholangiocarcinoma or other periampullary malignancy Location of distal biliary obstruction is such that it would allow the proximal end of a stent to be positioned at least 2cm from the hilum Patients deemed as resectable by pancreatic protocol CT or MRI Surgical candidate per pancreatobiliary surgeon after multi-disciplinary discussion Surgery intent within 4 weeks Endoscopic and surgical treatment to be provided by same team", "candidate_expression": "((18 or older) AND (Age) AND (Biliary obstructive signs) AND (Biliary obstructive symptoms) AND (Bilirubin level) AND (Distal biliary obstruction) AND (Endoscopic treatment) AND (Surgery) AND (Surgical candidate) AND (at least 2cm from the hilum) AND (at/above 100 umol per liter) AND (at/above 5.8 mg/dL) AND (deemed as resectable) AND (distal CBD cholangiocarcinoma) AND (distal biliary obstruction) AND (distal common bile duct (CBD) cholangiocarcinoma) AND (intent) AND (other) AND (pancreatic cancer) AND (pancreatic protocol CT) AND (pancreatic protocol MRI) AND (per pancreatobiliary surgeon) AND (periampullary cancers) AND (periampullary malignancy) AND (probable) AND (stent) AND (surgical treatment) AND (within 4 weeks) AND (would allow))"}
{"candidate_id": "LLM00846", "doc_id": "NCT02408120_inc", "case_bucket": "or", "source_criterion": "Subjects admitted to the hospital with acute or chronic medical illnesses or for elective and emergency surgical illness or trauma Known history of Type 2 diabetes mellitus for >3 months Treated with either diet alone, any combination of oral antidiabetic agents, non-insulin injectables or insulin therapy Blood glucose levels between >140 mg and <400 mg/dL without laboratory evidence of diabetic ketoacidosis", "candidate_expression": "((>140 mg and <400 mg/dL) AND (>3 months) AND (Blood glucose levels) AND (Type 2 diabetes mellitus) AND (acute) AND (admitted to the hospital) AND (chronic) AND (diabetic ketoacidosis) AND (diet) AND (elective) AND (emergency) AND (insulin) AND (laboratory evidence) AND (medical illnesses) AND (non-insulin injectables therapy) AND (oral antidiabetic agents) AND (surgical illness) AND (trauma) AND (without))"}
{"candidate_id": "LLM00847", "doc_id": "NCT02301039_exc", "case_bucket": "or", "source_criterion": "Prior systemic therapy targeting PD-1: PD-L1 axis. Patients who are curable by conventional multidisciplinary management. Patients with severe and/or uncontrolled concurrent medical disease that in the opinion of the investigator could cause unacceptable safety risks or compromise compliance with the protocol. Patients who have received wide field radiotherapy ≤ 4 weeks or limited field radiation for palliation < 2 weeks prior to screening or who have not recovered adequately from side effects of such therapy. Patients who have active infections requiring therapy. Patients that are known to be positive for Human Immunodeficiency Virus (HIV) (HIV 1/2 antibodies), active Hepatitis B (HBsAg reactive), or Hepatitis C (HCV RNA [qualitative] is detected); patients with negative Hepatitis C antibody testing may not need RNA testing. Patients that have a known psychiatric or substance abuse disorder that would interfere with cooperation with the requirements of the trial. Patients who received systemic anti-cancer treatment prior to the first dose of study drug within the following time frames: Patients with active autoimmune disease or a documented history of autoimmune disease or syndrome that requires systemic steroids or immunosuppressive agents. Patients with vitiligo or resolved childhood asthma/atopy would be exception to this rule. Patients that require inhaled steroids or local steroid injections would not be excluded from the study. Patients with hypothyroidism not from autoimmune disease that is stable on hormone replacement will not be excluded from the study. Women who are pregnant or nursing/breastfeeding. Known hypersensitivity to pembrolizumab or another mAb. Has a history of (non-infectious) pneumonitis that required steroids or current pneumonitis. Patients with untreated central nervous system disease. Patients with controlled treated CNS lesions who have undergone surgery or stereotactic radiosurgery and stable for 4 weeks are eligible. Inability to comply with protocol required procedures. Patients with medical conditions that require chronic systemic corticosteroid therapy or require any other form of immunosuppressive medication. However, patients using physiologic replacement doses of hydrocortisone, or its equivalent, will be considered eligible for this study: up to 20 mg hydrocortisone (or 5 mg of prednisone) in the morning and 10 mg hydrocortisone (or 2.5 mg prednisone) in the evening. Patients with the risk factors for bowel obstruction or bowel perforation (examples include but not limited to a history of acute diverticulitis, intra-abdominal abscess, abdominal carcinomatosis). Patients who have received a live vaccine within 30 days prior to the first dose of trial treatment.", "candidate_expression": "((CNS lesions controlled treated stable) AND (HBsAg reactive) AND (HCV RNA [qualitative] detected) AND (Hepatitis C) AND (Hepatitis C antibody negative) AND (Human Immunodeficiency Virus (HIV) positive HIV 1/2 antibodies) AND (Inability to comply with protocol required procedures.) AND (Patients that have a known psychiatric or substance abuse disorder that would interfere with cooperation with the requirements of the trial.) AND (Women) AND (abdominal carcinomatosis) AND (active Hepatitis B) AND (acute diverticulitis) AND (atopy) AND (autoimmune disease active) AND (autoimmune disease history) AND (bowel obstruction) AND (bowel perforation) AND (breastfeeding) AND (central nervous system disease untreated) AND (childhood asthma resolved) AND (conventional multidisciplinary management severe uncontrolled) AND (hormone replacement) AND (hydrocortisone 10 mg in the evening) AND (hydrocortisone physiologic replacement doses) AND (hydrocortisone up to 20 mg in the morning) AND (hypersensitivity to mAb) AND (hypersensitivity to pembrolizumab) AND (hypothyroidism stable on hormone replacement) AND (immunosuppressive agents) AND (immunosuppressive medication) AND (in the opinion of the investigator) AND (infections requiring therapy) AND (intra-abdominal abscess) AND (limited field radiation for palliation < 2 weeks prior to screening) AND (live vaccine within 30 days prior to the first dose of trial treatment) AND (mAb) AND (medical conditions require chronic systemic corticosteroid therapy) AND (medical disease concurrent) AND (nursing) AND (pembrolizumab) AND (pneumonitis current) AND (pneumonitis history required steroids) AND (prednisone 2.5 mg) AND (prednisone 5 mg) AND (pregnant) AND (psychiatric disorder) AND (risk factors for bowel obstruction) AND (risk factors for bowel perforation) AND (side effects of such therapy) AND (stereotactic radiosurgery) AND (steroids) AND (substance abuse disorder) AND (such therapy) AND (surgery) AND (syndrome that requires immunosuppressive agents) AND (syndrome that requires systemic steroids) AND (systemic anti-cancer treatment prior to the first dose of study drug) AND (systemic corticosteroid therapy chronic require immunosuppressive medication) AND (systemic steroids) AND (systemic therapy targeting PD-1: PD-L1 axis curable) AND (therapy) AND (vitiligo) AND (wide field radiotherapy ≤ 4 weeks) AND NOT (recovered adequately) AND NOT (autoimmune disease))"}
{"candidate_id": "LLM00848", "doc_id": "NCT02498483_exc", "case_bucket": "other", "source_criterion": "Newborns of substance abusing mothers. Newborns with any contraindications to routine circumcision, anatomical or hematologic.", "candidate_expression": "((Newborns) AND (circumcision) AND (contraindications) AND (mothers) AND (substance abusing))"}
{"candidate_id": "LLM00849", "doc_id": "NCT01991743_inc", "case_bucket": "other", "source_criterion": "Healthy patients age 18 and older Breech presentation Singleton gestation .scheduled for ECV desiring CSE.", "candidate_expression": "((18 and older) AND (Breech presentation) AND (CSE) AND (ECV) AND (Healthy) AND (Singleton gestation) AND (age) AND (desiring) AND (scheduled for))"}
{"candidate_id": "LLM00850", "doc_id": "NCT02838810_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received single NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative. Hepatitis B surface antigen (HBsAg) positive and <1000 IU/mL. Hepatitis B virus DNA <100 IU/mL.", "candidate_expression": "((<100 IU/mL) AND (<1000 IU/mL) AND (CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen) AND (Hepatitis B surface antigen) AND (Hepatitis B virus DNA) AND (NAs) AND (more than 12 months) AND (negative) AND (positive) AND (single))"}
```
