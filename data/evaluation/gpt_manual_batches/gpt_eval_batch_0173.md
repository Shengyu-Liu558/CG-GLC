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
{"candidate_id": "LLM04301", "doc_id": "NCT03388840_inc", "case_bucket": "other", "source_criterion": "male patients with androgenetic alopecia between 18 years and 60 years", "candidate_expression": "((androgenetic alopecia) AND (male) AND (years between 18 years and 60 years))"}
{"candidate_id": "LLM04302", "doc_id": "NCT03146390_inc", "case_bucket": "other", "source_criterion": "Systemically healthy adults. Minimum of 24 permanent teeth. No gingivitis (Community Periodontal Index score = 0). No periodontitis (Community Periodontal Index score = 0). Absence of untreated caries.", "candidate_expression": "((= 0) AND (Absence) AND (Community Periodontal Index score) AND (Minimum of 24) AND (No) AND (Systemically) AND (adults) AND (caries) AND (gingivitis) AND (healthy) AND (periodontitis) AND (permanent teeth) AND (untreated))"}
{"candidate_id": "LLM04303", "doc_id": "NCT02298504_inc", "case_bucket": "other", "source_criterion": "Pediatric patients with deep dental decay in primary molars Teeth with signs and symptoms of reversible pulpitis", "candidate_expression": "((Pediatric) AND (Teeth) AND (deep dental decay) AND (primary molars) AND (reversible pulpitis))"}
{"candidate_id": "LLM04304", "doc_id": "NCT02780427_inc", "case_bucket": "other", "source_criterion": "Children, aged between one and 24 months. classified as (American Society of Anesthesiologists) ASA physical status I or II, undergoing TEE were enrolled in the study.", "candidate_expression": "((ASA physical status I or II) AND (American Society of Anesthesiologists) AND (Children) AND (TEE) AND (aged between one and 24 months))"}
{"candidate_id": "LLM04305", "doc_id": "NCT02456129_exc", "case_bucket": "or", "source_criterion": "Incompletely cured pre-existing diseases for which it can be assumed that the absorption, distribution, metabolism, elimination or effects of the study drugs will not be normal Known or suspected liver diseases Clinically relevant findings(e.g. blood pressure, electrocardiogram(ECG); physical and gynecological examination, laboratory examination)", "candidate_expression": "((Clinically relevant) AND (blood pressure) AND (can be assumed) AND (electrocardiogram(ECG)) AND (findings Clinically relevant) AND (gynecological examination) AND (laboratory examination) AND (liver diseases Known suspected) AND (physical examination) AND (pre-existing diseases Incompletely cured) AND (suspected))"}
{"candidate_id": "LLM04306", "doc_id": "NCT02701777_inc", "case_bucket": "or", "source_criterion": "Male and females between ages 18-85 years Right handed Able to complete precision grips with both hands Able to complete full wrist flexion-extension bilaterally Able to walk unassisted Able to complete full ankle flexion-extension bilaterally Male and females between ages 18-85 years SCI ( 2 months of injury) Spinal Cord injury at or above L5 The ability to produce a visible precision grip force with one hand Able to perform some small wrist flexion and extension The ability to perform a small visible contraction with dorsiflexion and hip flexor muscles No subjects will be excluded based on their race, religion, ethnicity, gender or HIV status. ASIA A,B,C, or D", "candidate_expression": "((ASIA A,B,C, or D) AND (Male) AND (Right handed) AND (SCI 2 months of injury) AND (Spinal Cord injury at or above L5) AND (ages between 18-85 years) AND (complete full ankle flexion-extension bilaterally Able to) AND (complete full wrist flexion-extension bilaterally Able to Able to) AND (complete precision grips with both hands Able to) AND (females) AND (produce a visible precision grip force with one hand The ability to) AND (small visible contraction with dorsiflexion and hip flexor muscles The ability to) AND (small wrist flexion and extension Able to) AND (walk unassisted))"}
{"candidate_id": "LLM04307", "doc_id": "NCT02885909_exc", "case_bucket": "other", "source_criterion": "incooperative for glucose monitor refusal of insulin pregnancy", "candidate_expression": "((glucose monitor) AND (incooperative) AND (insulin) AND (pregnancy) AND (refusal))"}
{"candidate_id": "LLM04308", "doc_id": "NCT03262038_exc", "case_bucket": "or", "source_criterion": "Inability to use verbal or pictorial pain scoring scales hypersensitivity to selective 5-HT receptor antagonists diagnosed congenital long QT syndrome severe hepatic impairment pregnancy or nursing mothers", "candidate_expression": "((Inability) AND (congenital long QT syndrome) AND (hepatic impairment) AND (hypersensitivity) AND (nursing) AND (pictorial pain scoring scales) AND (pregnancy) AND (selective 5-HT receptor antagonists) AND (severe) AND (verbal pain scoring scales))"}
{"candidate_id": "LLM04309", "doc_id": "NCT02726009_exc", "case_bucket": "or", "source_criterion": "Previous or concurrent hormonal management of prostate cancer Contraindication for prescription of Firmagon® Concurrent treatment with a 5-a-reductase inhibitor Considered as a candidate for curative therapy History of severe untreated asthma, anaphylactic reactions or severe urticaria and/or angioedema QTc interval over 450 msec or risk factors for torsades de pointes or on Class IA and Class III anti arrhythmic medications Cancer within the last 5 years except prostate cancer and surgically removed basal or squamous cell carcinoma of the skin Known or suspected hepatic, symptomatic biliary disease (this includes moderate to severe chronic hepatic impairment) Patients with clinically significant laboratory abnormalities / disorders other than prostate cancer Patient with Hepatitis B Virus (HBV), Hepatitis C Virus (HCV) and Human Immunodeficiency Virus (HIV) infections", "candidate_expression": "((5-a-reductase inhibitor) AND (Cancer last 5 years) AND (Class IA anti arrhythmic medications) AND (Class III anti arrhythmic medications) AND (Contraindication) AND (Firmagon) AND (HBV) AND (HCV) AND (HIV) AND (Hepatitis B Virus infections) AND (Hepatitis C Virus infections) AND (Human Immunodeficiency Virus infections) AND (QTc interval over 450 msec) AND (anaphylactic reactions) AND (angioedema) AND (asthma severe untreated) AND (basal cell carcinoma of the skin) AND (biliary disease) AND (chronic hepatic impairment) AND (curative therapy) AND (hepatic disease moderate severe) AND (hormonal management) AND (prostate cancer) AND (risk factors for torsades de pointes) AND (squamous cell carcinoma of the skin) AND (surgically) AND (urticaria severe))"}
{"candidate_id": "LLM04310", "doc_id": "NCT02558504_exc", "case_bucket": "or", "source_criterion": "Aged under 18, Lack of informed consent signed, Radiofrequency treatment history, on going neoplastic history with a short prognosis, Concomitant participation in another clinical study Contraindication to general anesthesia, Patient with an esophageal location of scleroderma Presence of a cardiac pacemaker or stimulator Pregnant women or likely to be in the absence of effective contraception, Esophageal stenosis preventing the passage of an endoscope, Histology other than glandular neoplasia, History of or current history of esophageal cancer invading the submucosal layer of the esophagus or more, Surgical treatment history (except anti-reflux treatment) or esophageal radiotherapy, previous esophageal treatment by another method ablation: photodynamic therapy, argon plasma coagulation, laser, .... Esophageal varices observed in endoscopy, Coagulopathy or taking anticoagulants responsible an INR> 1.3 or a platelet count <75,000 per microL, Life expectancy of less than 3 years, due to intercurrent disease, especially neoplastic, Liver cirrhosis (Child-Pugh all stages) Respiratory failure: Renal failure (Cl Cr < 60 mL /min /1,73m), Heart attack within the last six months or progressive coronary artery disease, Severe distal arteriopathie > stage II of Leriche and Fontaine", "candidate_expression": "((Aged under 18) AND (Child-Pugh all stages) AND (Cl Cr < 60 mL /min /1,73m) AND (Contraindication) AND (Esophageal stenosis) AND (Esophageal varices) AND (Histology) AND (Liver cirrhosis) AND (Radiofrequency treatment history) AND (Renal failure) AND (Respiratory failure) AND (ablation another method) AND (distal arteriopathie Severe) AND (endoscope) AND (endoscopy) AND (esophageal cancer invading the submucosal layer of the esophagus) AND (esophageal treatment previous) AND (general anesthesia) AND (glandular neoplasia other than) AND (intercurrent disease) AND (neoplastic) AND (neoplastic on going history) AND (participation in another clinical study Concomitant) AND (passage of an endoscope preventing the) AND (prognosis short) AND (scleroderma esophageal location) AND (stage of Leriche and Fontaine > II) AND (women) AND NOT (anti-reflux treatment) AND NOT (informed consent signed) AND ((cardiac pacemaker) OR (cardiac stimulator)) AND ((Pregnant) OR (Pregnant likely to be in the absence of effective contraception)) AND ((History) OR (current)) AND ((Surgical treatment history) OR (esophageal radiotherapy)) AND ((argon plasma coagulation) OR (laser) OR (photodynamic therapy)) AND ((Coagulopathy) OR (anticoagulants)) AND ((INR > 1.3) OR (platelet count <75,000 per microL)) AND ((Life expectancy) OR (less than 3 years)) AND ((Heart attack within the last six months) OR (progressive coronary artery disease)))"}
{"candidate_id": "LLM04311", "doc_id": "NCT02822001_inc", "case_bucket": "other", "source_criterion": "Patients undergoing surgery with general anesthesia, Patients weighing = 80 pounds who are not -intubated prior to surgery, Patients who are able to give informed consent.", "candidate_expression": "((Patients who are able to give informed consent) AND (general anesthesia) AND (surgery) AND (surgery undergoing general anesthesia) AND (weighing = 80 pounds) AND NOT (intubated prior to surgery))"}
{"candidate_id": "LLM04312", "doc_id": "NCT02968602_exc", "case_bucket": "or", "source_criterion": "History of organic brain disease DSM-IV diagnosis of Alcohol or Substance Dependence within the last six months (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) DSM-IV diagnosis of Alcohol or Substance Abuse within the last one month (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) Pregnancy or lactation Severe liver dysfunction (LFT 3X upper limit of normal) Previous known hypersensitivity to tetracyclines Current treatment with tetracycline or derivative Treatment with oral contraceptives (unless a second form of birth control is used and documented) Treatment with cholestyramine or colestipol Treatment with Urinary alkalinizers (e.g., sodium lactate, potassium citrate) Treatment with warfarin Treatment with bupropion, varenicline, or nicotine replacement products in the month prior to study inclusion Less than two months treatment of adjunctive medications AND less than one month on same dose: beta blockers, antidepressants, mood stabilizers, antianxiety medications. Medical condition whose pathology or treatment would significantly increase the risk associated with the proposed protocol. History of head injury, seizures, or stroke Positive urine toxicology screen for substances of non-therapeutic use prior to craving assessments", "candidate_expression": "((3X upper limit of normal) AND (Alcohol Abuse) AND (Alcohol Dependence) AND (Current) AND (DSM-5) AND (DSM-IV) AND (History) AND (History of) AND (LFT) AND (Less than two months) AND (Medical condition) AND (Positive) AND (Pregnancy) AND (Previous) AND (Severe) AND (Substance Abuse) AND (Substance Dependence) AND (Substance Use Disorder) AND (Treatment) AND (Urinary alkalinizers) AND (adjunctive medications) AND (antianxiety medications) AND (antidepressants) AND (beta blockers) AND (birth control) AND (bupropion) AND (cholestyramine) AND (colestipol) AND (craving assessments) AND (except) AND (head injury) AND (hypersensitivity) AND (in the last six months) AND (in the month prior to study inclusion) AND (lactation) AND (less than one month) AND (liver dysfunction) AND (mood stabilizers) AND (nicotine) AND (nicotine replacement products) AND (oral contraceptives) AND (organic brain disease) AND (potassium citrate) AND (prior to craving assessments) AND (same dose) AND (second form) AND (seizures) AND (sodium lactate) AND (stroke) AND (study inclusion) AND (substances of non-therapeutic use) AND (tetracycline) AND (tetracycline derivative) AND (tetracyclines) AND (treatment) AND (unless) AND (urine toxicology screen) AND (varenicline) AND (warfarin) AND (within the last one month) AND (within the last six months) AND (would significantly increase the risk associated with the proposed protocol))"}
{"candidate_id": "LLM04313", "doc_id": "NCT01803438_inc", "case_bucket": "scope", "source_criterion": "Subject has been diagnosed with symptomatic paroxysmal atrial fibrillation as defined above and at least two symptomatic episodes in the last six months prior to inclusion. At least one episode of AF must be documented during the prior year by any kind of ECG recording. Subject has structural normal heart with an LVEF = 50%, thickness of the inter-ventricular septum =12 mm and left atrium diameters (short axis) < 46 mm obtained by transthoracic echocardiography. Subject has normal ECG parameters (QRS width in the 12 channel surface ECG =120 ms, QTc - interval < 440 ms, PQ - interval = 210 ms; all parameters should be measured at sinus rhythm). Subject is at least 18 and not older than 75years old. Subject is able and willing to give informed consent.", "candidate_expression": "((12 channel surface ECG) AND (< 440 ms) AND (< 46 mm) AND (= 210 ms) AND (= 50%,) AND (=12 mm) AND (=120 ms) AND (AF) AND (At least one) AND (ECG) AND (LVEF) AND (PQ - interval) AND (QRS width) AND (QTc - interval) AND (Subject is able and willing to give informed consent) AND (at least 18 and not older than 75years) AND (at least two) AND (episode) AND (episodes) AND (heart) AND (inclusion) AND (last six months prior to inclusion) AND (left atrium diameters) AND (normal) AND (old) AND (paroxysmal atrial fibrillation) AND (prior year) AND (short axis) AND (sinus rhythm) AND (structural) AND (symptomatic) AND (thickness of the inter-ventricular septum) AND (transthoracic echocardiography))"}
{"candidate_id": "LLM04314", "doc_id": "NCT02867618_exc", "case_bucket": "or", "source_criterion": "1. Prior Therapy Exposure to chemotherapy or radiotherapy within 2 weeks prior to entering the study or those who have not recovered from adverse events due to agents administered more than 2 weeks earlier. Systemic steroids that have not been stabilized (≥ 5 days) to the equivalent of ≤10 mg/day prednisone prior to the start of the study drugs. No other investigational agents are allowed. 2. History of allergic reactions to TGR-1202 or carfilzomib 3. Uncontrolled inter-current illness 4. Pregnant women 5. Nursing women 6. Current malignancy or history of a prior malignancy 7. Patient known to be Human Immunodeficiency Virus (HIV)-positive 8. Active Hepatitis A, Hepatitis B, or Hepatitis C infection", "candidate_expression": "((Human Immunodeficiency Virus (HIV) positive) AND (Nursing) AND (Pregnant) AND (Systemic steroids stabilized) AND (adverse events) AND (agents more than 2 weeks earlier) AND (allergic reactions History Uncontrolled) AND (due to) AND (inter-current illness inter-current) AND (other investigational agents) AND (prednisone ≤10 mg/day) AND (women) AND NOT (recovered) AND ((chemotherapy) OR (radiotherapy)) AND ((TGR-1202) OR (carfilzomib)) AND ((malignancy Current) OR (malignancy history of a prior)) AND ((Hepatitis A) OR (Hepatitis B) OR (Hepatitis C)))"}
{"candidate_id": "LLM04315", "doc_id": "NCT01793519_inc", "case_bucket": "or", "source_criterion": "Age greater than or equal to 18 years Have RA, as defined by the 1987 revised American College of Rheumatology criteria In sustained clinical remission for the last 6 months while receiving treatment with either etanercept, infliximab, or adalimumab, and greater than or equal to 1 DMARD (methotrexate, hydroxychloroquine, sulfasalazine, leflunomide, minocycline, cyclosporine, azathioprine, gold, penicillamine). DAS28 should be less than 2.6 on each visit over the preceding 6 months, with at least one visit 2-4 months before enrollment. If there is no visit 6 months before enrollment, the nearest visit in the 6-12 month period before enrollment should be considered and have a DAS28 less than 2.6.", "candidate_expression": "((Age greater than or equal to 18 years) AND (DAS28 less than 2.6 on each visit over the preceding 6 months) AND (DMARD greater than or equal to 1) AND (RA 1987 revised American College of Rheumatology criteria) AND (adalimumab) AND (azathioprine) AND (cyclosporine) AND (etanercept) AND (gold) AND (hydroxychloroquine) AND (infliximab) AND (leflunomide) AND (methotrexate) AND (minocycline) AND (penicillamine) AND (sulfasalazine) AND (sustained clinical remission for the last 6 months) AND (visit) AND (visit at least one 2-4 months before enrollment))"}
{"candidate_id": "LLM04316", "doc_id": "NCT02969876_inc", "case_bucket": "or", "source_criterion": "Meets Diagnostic and Statistical Manual of Mental Disorders (Versions 4 and 5) criteria for and Major Depressive Disorder. Hamilton Depression Rating Scale-17 score greater than 18. Men and women between ages >=18 and 65.", "candidate_expression": "((Diagnostic and Statistical Manual of Mental Disorders criteria) AND (Hamilton Depression Rating Scale greater than 18) AND (Major Depressive Disorder) AND (ages between 18 and 65) AND ((Men) OR (women)) AND ((Versions 4) OR (Versions 5)))"}
{"candidate_id": "LLM04317", "doc_id": "NCT02415257_exc", "case_bucket": "other", "source_criterion": "impaired decision making neurofibromatosis signs for central dysfunction remaining vestibular function Patients are advised not to participate in the gentamicin arm if hearing is better than 30 deciBel (dB) in pure tone average (500, 1000, 2000, 3-4000 Hz) and speech discrimination better than 70% the neurosurgeon aim at hearing preservation surgery and do not want to risk gentamicin associated hearing loss", "candidate_expression": "((central dysfunction signs) AND (hearing better than 30 deciBel (dB) pure tone average) AND (impaired decision making) AND (neurofibromatosis) AND (remaining vestibular function) AND (speech discrimination better than 70% 500, 1000, 2000, 3-4000 Hz))"}
{"candidate_id": "LLM04318", "doc_id": "NCT00500500_inc", "case_bucket": "other", "source_criterion": "female or male of 50 to 85 years old with a care giver Mini Mental Status (MMS) test between 16 to 26 inclusive Clinical Dementia Rating (CDR) test inferior or equal to 1 National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test positive for an Alzheimer's disease Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test positive for dementia", "candidate_expression": "((50 to 85 years) AND (Clinical Dementia Rating (CDR) test) AND (Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test) AND (Mini Mental Status (MMS) tes) AND (National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test) AND (between 16 to 26 inclusive) AND (inferior or equal to 1) AND (old) AND (positive))"}
{"candidate_id": "LLM04319", "doc_id": "NCT02555163_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed at the out-patient cystoscopy with papillary bladder tumour will be legible for inclusion", "candidate_expression": "((cystoscopy) AND (out-patient) AND (papillary bladder tumour))"}
{"candidate_id": "LLM04320", "doc_id": "NCT02893293_exc", "case_bucket": "or", "source_criterion": "Contraindications for magnetic resonance imaging Hemosiderosis/hemochromatosis ( patients can still be included in the non-ferumoxytol arm)", "candidate_expression": "((Contraindications) AND (Hemosiderosis) AND (hemochromatosis) AND (magnetic resonance imaging))"}
{"candidate_id": "LLM04321", "doc_id": "NCT03083197_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to tetracycline, doxycycline or azithromycin Administration of doxycycline, azithromycin, chloramphenicol, rifampicin, or tetracycline during the preceding 7 days Pregnancy or breast-feeding Patients with myasthenia gravis or systemic lupus erythematosus Patients with an established infection (diagnostic test required) e.g. acute malaria, dengue, leptospirosis, typhoid, Japanese encephalitis etc. Current TB or TB treatment in = 6 months (contain active antibiotics against Orientia spp.) Current HAART use for HIV, long term use of immunosuppressants (e.g. steroids, chemotherapy, TNF-inhibitors and related agents) Patients with severe disease whom the clinical team feel their condition necessitates the need for additional scrub typhus treatment beyond the allocated antibiotic treatment assigned at randomization (e.g. IV chloramphenicol and/or PO/NG rifampicin)", "candidate_expression": "((HAART) AND (HIV) AND (Japanese encephalitis) AND (Pregnancy) AND (TB) AND (TB treatment) AND (TNF-inhibitors) AND (acute malaria) AND (azithromycin) AND (breast-feeding) AND (chemotherapy) AND (chloramphenicol) AND (dengue) AND (diagnostic test) AND (doxycycline) AND (during the preceding 7 days) AND (hypersensitivity) AND (immunosuppressants) AND (in = 6 months) AND (infection) AND (leptospirosis) AND (long term use) AND (myasthenia gravis) AND (rifampicin) AND (steroids) AND (systemic lupus erythematosus) AND (tetracycline) AND (typhoid))"}
{"candidate_id": "LLM04322", "doc_id": "NCT02937779_inc", "case_bucket": "other", "source_criterion": ">= 18 years old the day of inclusion Pregnancy Positive HBs Ag Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusion", "candidate_expression": "((HBs Ag Positive) AND (Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusio) AND (Pregnancy) AND (old >= 18 years))"}
{"candidate_id": "LLM04323", "doc_id": "NCT02816164_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed primary breast cancer Planned to start docetaxel component of FEC-D or AC-D, or first cycle of; dose-dense AC-T, TC, FEC-D or TAC chemotherapy =19 years of age Able to provide verbal consent", "candidate_expression": "((=19 years) AND (AC-D) AND (Able to provide verbal consent) AND (FEC-D) AND (Histologically) AND (Histologically confirmed) AND (Planned to start) AND (TAC chemotherapy) AND (TC) AND (age) AND (docetaxel) AND (dose-dense AC-T) AND (first cycle of) AND (primary breast cancer))"}
{"candidate_id": "LLM04324", "doc_id": "NCT02747940_exc", "case_bucket": "or", "source_criterion": "history of major systemic illness, including uncontrolled hypertension, diabetes, chronic renal insufficiency, autoimmune diseases or malignancies history of neurological disorders which might affect sensation such as previous stroke or peripheral neuropathy history of substance abuse (except painkillers) heavy smokers (with a daily consumption >20 cigarettes) pregnancy or lactation any contraindication for magnetic resonance imaging (MRI) and any obvious infection or inflammation over a period of at least 1 month before the study.", "candidate_expression": "((MRI) AND (affect sensation) AND (autoimmune diseases) AND (chronic renal insufficiency,) AND (cigarettes daily consumption >20) AND (contraindication) AND (diabetes) AND (hypertension uncontrolled) AND (infection) AND (inflammation) AND (magnetic resonance imaging) AND (malignancies) AND (neurological disorders) AND (peripheral neuropathy) AND (pregnancy or lactation) AND (smokers heavy) AND (stroke) AND (substance abuse) AND (systemic illness major) AND NOT (painkillers))"}
{"candidate_id": "LLM04325", "doc_id": "NCT02396420_exc", "case_bucket": "or", "source_criterion": "History of prostate, bladder, or rectal cancer History of transurethral resection of the prostate (TURP), open prostate surgery, or radiofrequency or microwave therapies History of open bladder, rectosigmoid colon, or other pelvic surgery Patient is unwilling to discontinue alpha blockers 1 month after study treatment Patient is unwilling to discontinue 5-alph reductase inhibitors 1 month after study treatment Neurogenic bladder or other neurologic disorder impacting bladder function such as Parkinson's disease, multiple sclerosis, cerebral vascular accident or diabetes Any other confounding bladder or urethral pathology, including urethral stricture, bladder neck contracture, or bladder atonia Active prostatitis or urinary tract infection Cystolithiasis within the past 3 months Serum creatinine > 1.7mg/dL Inability to discontinue oral anticoagulant 2-5 days prior to study treatment Coagulation disturbances not normalized by medical treatment Iodinated contrast allergy that, in the opinion of the Investigator, cannot be adequately premedicated Gelatin allergy Known severe peripheral vascular disease or major iliac arterial occlusive disease Interest in future fertility Clinically significant cardiac arrhythmia or other cardiac disease (including congestive heart failure), uncontrolled diabetes mellitus, clinically significant respiratory disease, or known immunosuppression Other condition that the Investigator believes puts the patient at risk for a complication during the procedure", "candidate_expression": "((1 month after study treatment) AND (2-5 days prior to study treatment) AND (5-alph reductase inhibitors) AND (> 1.7mg/dL) AND (Active) AND (Coagulation disturbances) AND (Cystolithiasis) AND (Gelatin) AND (Interest in future fertility) AND (Iodinated contrast) AND (Neurogenic bladder) AND (Other condition that the Investigator believes puts the patient at risk for a complication during the procedure) AND (Parkinson's disease) AND (Serum creatinine) AND (allergy) AND (alpha blockers) AND (bladder atonia) AND (bladder cancer) AND (bladder neck contracture) AND (bladder pathology) AND (cardiac arrhythmia) AND (cardiac disease) AND (cerebral vascular accident) AND (clinically significant) AND (congestive heart failure) AND (diabetes) AND (diabetes mellitus) AND (iliac arterial occlusive disease) AND (immunosuppression) AND (major) AND (medical treatment) AND (microwave therapies) AND (multiple sclerosis) AND (neurologic disorder impacting bladder function) AND (normalized) AND (not) AND (open bladder surgery) AND (open prostate surgery) AND (oral anticoagulant) AND (pelvic surgery) AND (peripheral vascular disease) AND (prostate cancer) AND (prostatitis) AND (radiofrequency) AND (rectal cancer) AND (rectosigmoid colon surgery) AND (respiratory disease) AND (severe) AND (study treatment) AND (transurethral resection of the prostate (TURP)) AND (uncontrolled) AND (urethral pathology) AND (urethral stricture) AND (urinary tract infection) AND (within the past 3 months))"}
```
