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
{"candidate_id": "LLM01551", "doc_id": "NCT03420638_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo bilateral palatine tonsillectomy as the only procedure", "candidate_expression": "((palatine tonsillectomy Scheduled to undergo bilateral only procedure) AND (procedure))"}
{"candidate_id": "LLM01552", "doc_id": "NCT02714725_inc", "case_bucket": "or", "source_criterion": "Adult patients aged (>18), males and females, undergoing elective coronary artery bypass graft (CABG) surgery with cardiopulmonary bypass (CPB).", "candidate_expression": "((CABG) AND (CPB) AND (aged >18) AND (cardiopulmonary bypass) AND (surgery coronary artery bypass graft elective) AND ((females) OR (males)))"}
{"candidate_id": "LLM01553", "doc_id": "NCT02637076_inc", "case_bucket": "or", "source_criterion": "current diagnosis of narcolepsy with cataplexy OR healthy control", "candidate_expression": "((cataplexy) AND ((healthy) OR (narcolepsy)))"}
{"candidate_id": "LLM01554", "doc_id": "NCT03195153_inc", "case_bucket": "or", "source_criterion": "diabetic patient; therapy with aspirin and insulin; patient well responders", "candidate_expression": "((diabetic) AND (well responders) AND ((aspirin) OR (insulin)))"}
{"candidate_id": "LLM01555", "doc_id": "NCT03079141_exc", "case_bucket": "or", "source_criterion": "Any previous treatments for active CSC; Previous prescription of mineralocorticoid receptor antagonists, for cCSC or for other diseases; Current treatment with corticosteroids (topical or systemic), corticosteroid use within 3 months before possible start of trial treatment, or anticipated start of corticosteroid treatment within the first 2 years from the start of the trial period; Evidence of another diagnosis that can explain serous SRF or visual loss; Best-corrected visual acuity < 20/200 (Snellen equivalent); Profound chorioretinal atrophy in central macular area on ophthalmoscopy and OCT; Myopia > 6D; Visual loss and/or serous detachment on OCT < 6 weeks; Continuous and/or progressive visual loss > 18 months or serous detachment on OCT > 18 months; No hyperfluorescence on ICGA; Intraretinal edema on OCT; (relative) Contraindications for FA or ICGA; (relative) Contraindications for photodynamic treatment (pregnancy, porphyria, severely disturbed liver function). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening (relative) Known contraindications for initiation of eplerenone treatment (hyperkalemia, abnormal renal clearance, severe hepatic insufficiency (Child-Pugh C), type 2 diabetes mellitus with microalbuminuria, concomitant use of potassium supplements, potassium-sparing diuretics, strong CYP3A4 inhibitors, or the combination of an ACE-inhibitor and an angiotensin receptor blocking agent). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening; Soft drusen in treated eye or fellow eye, signs of choroidal neovascularization on ophthalmoscopy and/or FA/ICGA of the study eye.", "candidate_expression": "((ACE-inhibitor) AND (Best-corrected visual acuity < 20/200) AND (CSC active) AND (Child-Pugh C) AND (Contraindications) AND (FA) AND (ICGA) AND (ICGA hyperfluorescence) AND (Intraretinal edema) AND (Myopia > 6D) AND (OCT) AND (OCT < 6 weeks Continuous) AND (OCT > 18 months) AND (Soft drusen treated eye fellow eye) AND (Visual loss) AND (abnormal renal clearance) AND (angiotensin receptor blocking agent) AND (cCSC) AND (chorioretinal atrophy Profound central macular area) AND (choroidal neovascularization) AND (contraindications) AND (corticosteroid treatment anticipated within the first 2 years from the start of the trial period) AND (corticosteroid use within 3 months before possible start of trial treatment) AND (corticosteroids Current topical systemic) AND (disturbed liver function severely) AND (eplerenone) AND (hyperkalemia) AND (microalbuminuria) AND (mineralocorticoid receptor antagonists Previous) AND (ophthalmoscopy) AND (other diseases) AND (photodynamic treatment) AND (porphyria) AND (potassium supplements) AND (potassium-sparing diuretics) AND (pregnancy) AND (renal clearance abnormal) AND (serous detachment) AND (severe hepatic insufficiency) AND (strong CYP3A4 inhibitors) AND (treatments previous) AND (type 2 diabetes mellitus) AND (visual loss > 18 months progressive))"}
{"candidate_id": "LLM01556", "doc_id": "NCT00483106_exc", "case_bucket": "other", "source_criterion": "Psychosis Tourette syndrome Intelligence quotient (IQ) < 70 Pervasive developmental disorder (PDD)", "candidate_expression": "((IQ) AND (Intelligence quotient < 70) AND (PDD) AND (Pervasive developmental disorder) AND (Psychosis) AND (Tourette syndrome))"}
{"candidate_id": "LLM01557", "doc_id": "NCT02692651_exc", "case_bucket": "or", "source_criterion": "Patients with severe-complicated disease that would compromise oral therapy (hypotenstion or shock, ileus or bowel obstruction, megacolon). Patients with an allergy to oral vancomycin or fidaxomicin. Patients anticipated to receive metronidazole after enrollment. Patients who already received oral vancomycin or metronidazole (either oral or intravenous) for > 24 hours within the preceding 72 hours at the time of enrollment. Patients anticipated to receive adjunctive C. difficile therapy (rifaxamin, nitazoxanide, tigecycline) after enrollment.", "candidate_expression": "((> 24 hours) AND (C. difficile therapy) AND (allergy) AND (anticipated) AND (bowel obstruction) AND (enrollment) AND (fidaxomicin) AND (hypotenstion) AND (ileus) AND (megacolon) AND (metronidazole) AND (nitazoxanide) AND (oral) AND (preceding 72 hours at the time of enrollment.) AND (rifaxamin) AND (shock) AND (tigecycline) AND (vancomycin))"}
{"candidate_id": "LLM01558", "doc_id": "NCT01217671_inc", "case_bucket": "or", "source_criterion": "Diagnosis of emphysema confirmed by CT scan. If a report of past CT scan is not available at site documenting then a CT scan is to be performed at screening Male or female patients at least 18 years of age. Able and willing to sign an informed consent. Patient with record of congenital AAT deficiency of phenotype PiZZ (homozygote) or other rare phenotypes related to AAT deficiency and with AAT serum level ≤ 11 micromole. For patients receiving IV AAT augmentation therapy the serum AAT level threshold does not apply. FEV1/SVC <70% of predicted value post bronchodilator (SVC is slow VC) and FEV1 < 80% of predicted value post-bronchodilator History of at least two moderate or severe exacerbations that required change in treatment (antibiotics, systemic steroids, hospitalization) in the last 18 months prior to date of screening , with at least one of these occurring within the last 12 months prior to screening. Ability to comply with completion of electronic diary. Ability to self-administer inhaled AAT. No significant abnormalities in serum hematology, serum chemistry and serum inflammatory / immunogenic markers according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency. No significant abnormalities in urinalysis according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency. No significant abnormalities in ECG per investigator judgment. Negative for HBsAg and for antibodies to HCV, HIV-1. AAT deficient patients who are either naïve (not receiving IV augmentation therapy) or AAT deficient patients (receiving IV augmentation therapy), if they have been stable on regular therapy for at least 3 months prior to the screening visit and are willing to continue the same regime throughout this trial. Note that only sites in Germany can recruit patients who are currently being treated with IV AAT.Patients who stopped IV augmentation treatment 6 months prior to screening date and will not re-start this treatment for the course of the study will be considered Naïve. Non-pregnant, non-lactating female patients, whose screening pregnancy test is negative and who are using contraceptive methods deemed reliable by the investigator, or who are at least 2 years post-menopausal or surgically sterilized.", "candidate_expression": "((AAT deficient) AND (AAT serum level ≤ 11 micromole) AND (Ability to comply with completion of electronic diary.) AND (Ability to self-administer inhaled AAT.) AND (Able and willing to sign an informed consent.) AND (CT scan) AND (CT scan at screening) AND (ECG) AND (FEV1 < 80% of predicted value post-bronchodilator) AND (FEV1/SVC <70% of predicted value post bronchodilator) AND (HBsAg Negative) AND (HIV-1 Negative) AND (IV AAT augmentation therapy) AND (IV augmentation therapy) AND (Male screening) AND (No significant abnormalities in ECG per investigator judgment.) AND (No significant abnormalities in serum hematology, serum chemistry and serum inflammatory / immunogenic markers according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency.) AND (No significant abnormalities in urinalysis according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency.) AND (age at least 18 years) AND (antibiotics) AND (antibodies to HCV Negative) AND (bronchodilator) AND (bronchodilator moderate) AND (comply with completion of electronic diary) AND (congenital AAT deficiency of phenotype PiZZ (homozygote)) AND (contraceptive methods deemed reliable by the investigator) AND (deemed reliable by the investigator) AND (emphysema) AND (exacerbations at least two required change in treatment severe) AND (female) AND (hospitalization) AND (naïve) AND (post-menopausal) AND (pregnancy test negative) AND (rare phenotypes related to AAT deficiency) AND (report of past CT scan) AND (self-administer inhaled AAT) AND (surgically) AND (surgically sterilized) AND (systemic steroids systemic) AND (therapy stable for at least 3 months prior to the screening) AND (treatment) AND (willing to continue throughout this trial) AND NOT (CT scan past) AND NOT (abnormalities in ECG significant) AND NOT (IV augmentation therapy) AND NOT (pregnant) AND NOT (lactating))"}
{"candidate_id": "LLM01559", "doc_id": "NCT00483106_inc", "case_bucket": "other", "source_criterion": "ADHD", "candidate_expression": "(ADHD)"}
{"candidate_id": "LLM01560", "doc_id": "NCT03351972_exc", "case_bucket": "other", "source_criterion": "dysphagia severe gastroparesis requiring endoscopic placement of capsule small bowel obstruction pregnancy", "candidate_expression": "((capsule) AND (dysphagia) AND (endoscopic placement) AND (gastroparesis) AND (pregnancy) AND (requiring) AND (severe) AND (small bowel obstruction))"}
{"candidate_id": "LLM01561", "doc_id": "NCT03255044_inc", "case_bucket": "other", "source_criterion": "older than 18 years (of both sexes) diagnosed with stable chronic heart failure NYHA class II-III ejection fraction < 40 % as assessed by 2D echocardiography who have been optimized on Guideline Directed treatment for heart failure for at least a month prior to enrolling.", "candidate_expression": "((2D echocardiography) AND (NYHA class II-III) AND (both sexes) AND (chronic heart failure stable) AND (ejection fraction < 40 %) AND (years older than 18))"}
{"candidate_id": "LLM01562", "doc_id": "NCT02908919_exc", "case_bucket": "or", "source_criterion": "ileus known or suspected bowel obstruction active bowel inflammation pregnancy any presence of serious medical conditions ( esp. cardiac, renal, liver diseases) history of prior colonic or rectal surgery inability to obtain valid data from", "candidate_expression": "((active) AND (bowel inflammation) AND (bowel obstruction) AND (history of) AND (ileus) AND (pregnancy) AND (prior) AND (serious medical conditions) AND ((cardiac diseases) OR (liver diseases) OR (renal diseases)) AND ((colonic surgery) OR (rectal surgery)) AND ((known) OR (suspected)))"}
{"candidate_id": "LLM01563", "doc_id": "NCT02935855_exc", "case_bucket": "other", "source_criterion": "patients with cancer patients with chronic inflammation diseases", "candidate_expression": "((cancer) AND (chronic inflammation diseases))"}
{"candidate_id": "LLM01564", "doc_id": "NCT02156999_inc", "case_bucket": "other", "source_criterion": "Osteoporosis", "candidate_expression": "(Osteoporosis)"}
{"candidate_id": "LLM01565", "doc_id": "NCT02961764_inc", "case_bucket": "other", "source_criterion": "Presents to the Emergency Department (ED) and meets the clinical definition for Acute Bacterial Skin and Skin Structure Infections (ABSSSI) Known or suspected gram-positive infection.", "candidate_expression": "((ABSSSI) AND (Acute Bacterial Skin and Skin Structure Infections) AND (Emergency Department (ED)) AND (gram-positive) AND (infection))"}
{"candidate_id": "LLM01566", "doc_id": "NCT02282319_inc", "case_bucket": "other", "source_criterion": "ASA (American Society of Anesthesiologists) class 1 & 2, undergoing day-case knee arthroscopy", "candidate_expression": "((ASA) AND (class 1 & 2) AND (knee arthroscopy))"}
{"candidate_id": "LLM01567", "doc_id": "NCT02541955_exc", "case_bucket": "or", "source_criterion": "Prior treatment with Acthar in the past 2mos Meet one of the above RA flare requirements Subjects who have received live or live attenuated vaccines within 6 weeks prior to the first dose of study drug (or the zoster vaccine)", "candidate_expression": "((Acthar in the past 2mos) AND (RA flare requirements one of) AND (live attenuated vaccines) AND (live vaccines) AND (study drug first dose) AND (treatment Prior) AND (zoster vaccine))"}
{"candidate_id": "LLM01568", "doc_id": "NCT01322464_inc", "case_bucket": "or", "source_criterion": "Healthy males between 18 and 45 years of age (inclusive). Body mass index to be between 18 to 30 kg/m2 (inclusive) as calculated by weight(Kg)/height(m2). Subjects were to have no clinically significant abnormal findings on physical examination, ECG, medical history, or clinical laboratory results during screening. Subjects were to, in the opinion of the investigator, have no clinically significant abnormal findings of renal and hepatic function as determined by serum creatinine, total bilirubin, and transaminase levels. Subjects were to be non-users of tobacco products (minimum of 6 months prior to the start of the study). Subjects were to have a negative screen for HIV I and II, HBsAg, and antibody to Hepatitis C virus. Subjects were to have a negative urine screen for alcohol, drugs of abuse (screening only), and cotinine. Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug. Subjects were able to comply with the protocol and the restrictions and assessments therein. Subjects were to give voluntary written informed consent to participate in the trial.", "candidate_expression": "((Body mass index between 18 to 30 kg/m2) AND (HBsAg negative) AND (Healthy) AND (Subjects were able to comply with the protocol and the restrictions and assessments therein.) AND (Subjects were to give voluntary written informed consent to participate in the trial) AND (Subjects were to use an appropriate barrier method of contraception (condom and spermicide) in addition to having their female partner use another form of barrier contraception (e.g.female condom or occlusive cap with spermicide) during the study and for 3 months following administration of the study drug.) AND (age between 18 and 45 years) AND (antibody to Hepatitis C virus negative) AND (hepatic function) AND (in the opinion of the investigator) AND (renal function) AND (screen for HIV I negative) AND (screen for HIV II negative) AND (serum creatinine) AND (total bilirubin) AND (transaminase levels) AND (urine screen for alcohol negative) AND (urine screen for cotinine negative) AND (urine screen for drugs of abuse negative) AND NOT (abnormal findings clinically significant) AND NOT (users of tobacco products minimum of 6 months prior to the start of the study the start of the study) AND NOT (abnormal findings clinically significant during screening) AND ((ECG) OR (clinical laboratory) OR (medical history) OR (physical examination)))"}
{"candidate_id": "LLM01569", "doc_id": "NCT03156855_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01570", "doc_id": "NCT00650312_inc", "case_bucket": "or", "source_criterion": "1. Age: 18 years and older. 2. Sex: Male and non-pregnant, non-lactating female 1. Women of childbearing potential must have negative serum (Beta HCG) pregnancy tests performed within 14 days prior to the start of the study and on the evening prior to each dose administration. If dosing is scheduled on Sunday or Monday, the HCG pregnancy test should be given within 48 hours prior to dosing of each study period. An additional serum (Beta HCG) pregnancy test will be performed upon completion of the study. 2. Women of childbearing potential must practice abstinence or be using an acceptable form of contraception throughout the duration of the study. Acceptable forms of contraception include the following: (1) intrauterine device in place for at least 3 months prior to the start of the study and remaining in place during the study period, or (2) barrier methods containing or used in conjunction with a spermicidal agent, or (3) postmenopausal accompanied with a documented postmenopausal course of at least one year or surgical sterility (tubal ligation, oophorectomy or hysterectomy). 3. During the course of the study, from study screen until study exit - including the washout period, women of childbearing potential must use a spermicide containing barrier method of contraception in addition to their current contraceptive device. This advice should be documented in the informed consent form. 3. Weight: At least 60 kg (132 lbs) for man and 48 kg (106 lbs) for women and within 15% of Ideal Body Weight (IBW), as referenced by the Table of \"\"Desirable Weights of Adults\"\" Metropolitan Life Insurance Company, 1999 (See Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 4. All subjects should be judged normal and healthy during a pre-study medical evaluation (physical examination, laboratory evaluation, 12-lead ECG, hepatitis B and hepatitis C tests, HIV test, and urine drug screen including amphetamine, barbiturates, benzodiazepine, cannabinoid, cocaine, opiates, phencyclidine, and methadone) performed within 14 days of the initial dose of study medication.", "candidate_expression": "((12-lead ECG) AND (Age 18 years and older) AND (Beta HCG) AND (HIV test) AND (Weight within 15% of Ideal Body Weight (IBW) At least 132 lbs At least 106 lbs) AND (Women) AND (barrier methods) AND (childbearing potential) AND (contraceptive device current) AND (healthy) AND (hepatitis B tests) AND (hepatitis C tests) AND (laboratory evaluation) AND (methadone) AND (normal) AND (phencyclidine) AND (physical examination) AND (pre-study medical evaluation within 14 days of the initial dose of study medication) AND (serum pregnancy tests negative within 14 days prior to the start of the study on the evening prior to each dose administration) AND (spermicidal agent) AND (spermicide containing barrier method of contraception in addition to) AND (surgical sterility) AND (urine drug screen amphetamine barbiturates benzodiazepine cannabinoid cocaine opiates) AND (women) AND NOT (pregnant) AND NOT (lactating) AND ((man At least 60 kg) OR (women At least 48 kg)) AND ((Male) OR (female)) AND ((abstinence) OR (contraception acceptable form)) AND ((intrauterine device for at least 3 months prior to the start of the study in place during the study period) OR (postmenopausal at least one year)) AND ((hysterectomy) OR (oophorectomy) OR (tubal ligation)))"}
{"candidate_id": "LLM01571", "doc_id": "NCT00527826_exc", "case_bucket": "or", "source_criterion": "Known other respiratory disorders or signs for other respiratory disorders (e.g. asthma, lung cancer, sarcoidosis, tuberculosis, lung fibrosis, cystic fibrosis, bronchoectasis). Known history of significant inflammatory disease, other than COPD (e.g. rheumatoid arthritis and systemic lupus erythematosus). Known to be severely alpha-1-antitrypsin deficient (PI SZ or ZZ) Having undergone lung surgery (e.g. lung resection including lung volume reduction surgery, lung transplant) or subjects scheduled for surgery. Concurrent medication from Visit 1 and for the duration of the study with any of the prohibited medications: monoamine oxidase inhibitors and tricyclic antidepressants, and ritonavir (a highly potent cytochrome P450 3A4 inhibitor). Subjects receiving chronic or prophylactic antibiotic therapy. Serious, uncontrolled disease (including serious psychological disorders) likely to interfere with the study or impact on subject safety. Have, in the opinion of the investigator, evidence of alcohol, drug or solvent abuse. History of depression. History or presence of clinically significant drug sensitivity or clinically significant allergic reaction to corticosteroids or salmeterol. Moderate or severe COPD exacerbation (requiring corticosteroids or increased dosage of corticosteroids and/or antibiotics or hospitalization) within the 4 weeks prior to Visit 1 Lower respiratory tract infection within the 4 weeks prior to Visit 1 . Pregnant or lactating female and female of childbearing potential. Subject is a participating investigator, sub-investigator, study coordinator, or other employee of a participating investigator, or is an immediate family member of the before mentioned. Subject is an employee of GlaxoSmithKline (GSK). Subject participated in an investigational drug study within 30 days prior to Visit 1", "candidate_expression": "((COPD exacerbation within the 4 weeks prior to Visit 1) AND (Lower respiratory tract infection within the 4 weeks prior to Visit 1) AND (alpha-1-antitrypsin deficient severely) AND (corticosteroids) AND (cytochrome P450 3A4 inhibitor) AND (depression History of) AND (female) AND (inflammatory disease) AND (lung resection) AND (medication from Visit 1) AND (participated in an investigational drug study within 30 days prior to Visit 1) AND (psychological disorders) AND (scheduled) AND (uncontrolled disease) AND NOT (COPD) AND ((respiratory disorders) OR (signs for respiratory disorders)) AND ((rheumatoid arthritis) OR (systemic lupus erythematosus)) AND ((lung surgery) OR (surgery)) AND ((lung transplant) OR (lung volume reduction surgery)) AND ((monoamine oxidase inhibitors) OR (ritonavir) OR (tricyclic antidepressants)) AND ((asthma) OR (bronchoectasis) OR (cystic fibrosis) OR (lung cancer) OR (lung fibrosis) OR (sarcoidosis) OR (tuberculosis)) AND ((chronic antibiotic therapy) OR (prophylactic antibiotic therapy)) AND ((alcohol abuse) OR (drug abuse) OR (solvent abuse)) AND ((allergic reaction) OR (drug sensitivity)) AND ((corticosteroids) OR (salmeterol)) AND ((Moderate) OR (severe)) AND ((antibiotics) OR (corticosteroids increased dosage) OR (hospitalization)) AND ((Pregnant) OR (childbearing potential) OR (lactating)))"}
{"candidate_id": "LLM01572", "doc_id": "NCT01891383_exc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. History of penetrating brain injury 2. History of disabling neurological or psychiatric condition such as epilepsy (besides posttraumatic epilepsy), multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia Controls (without a history of TBI): History of disabling neurological or psychiatric condition such as epilepsy, multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia", "candidate_expression": "((History) AND (besides) AND (disabling neurological condition) AND (disabling psychiatric condition) AND (penetrating brain injury) AND (posttraumatic epilepsy) AND ((cortical stroke) OR (encephalitis) OR (epilepsy) OR (hypoxic-ischemic encephalopathy) OR (multiple sclerosis) OR (schizophrenia)) AND ((condition disabling neurological) OR (psychiatric condition disabling)))"}
{"candidate_id": "LLM01573", "doc_id": "NCT02579733_exc", "case_bucket": "or", "source_criterion": "Patients with azathioprine or biologics therapy", "candidate_expression": "((therapy) AND ((azathioprine) OR (biologics)))"}
{"candidate_id": "LLM01574", "doc_id": "NCT01793519_inc", "case_bucket": "or", "source_criterion": "Age greater than or equal to 18 years Have RA, as defined by the 1987 revised American College of Rheumatology criteria In sustained clinical remission for the last 6 months while receiving treatment with either etanercept, infliximab, or adalimumab, and greater than or equal to 1 DMARD (methotrexate, hydroxychloroquine, sulfasalazine, leflunomide, minocycline, cyclosporine, azathioprine, gold, penicillamine). DAS28 should be less than 2.6 on each visit over the preceding 6 months, with at least one visit 2-4 months before enrollment. If there is no visit 6 months before enrollment, the nearest visit in the 6-12 month period before enrollment should be considered and have a DAS28 less than 2.6.", "candidate_expression": "((1987 revised American College of Rheumatology criteria) AND (2-4 months before enrollment) AND (Age) AND (DAS28) AND (DMARD) AND (RA) AND (at least one) AND (for the last 6 months) AND (greater than or equal to 1) AND (greater than or equal to 18 years) AND (less than 2.6) AND (on each visit) AND (over the preceding 6 months) AND (sustained clinical remission) AND (visit) AND ((azathioprine) OR (cyclosporine) OR (gold) OR (hydroxychloroquine) OR (leflunomide) OR (methotrexate) OR (minocycline) OR (penicillamine) OR (sulfasalazine)) AND ((adalimumab) OR (etanercept) OR (infliximab)))"}
{"candidate_id": "LLM01575", "doc_id": "NCT02528604_exc", "case_bucket": "or", "source_criterion": "Paroxysmal atrial fibrillation. Long-standing persistent or permanent atrial fibrillation. Previous pacemaker implantation. Previous atrial ablation. Patient is unable to take warfarin or other oral anti-coagulant medication. Patient is suffering with unstable angina in last one week. Patient has had a myocardial infarction within last two months. Patient is expecting or has had major cardiac surgery within last two months. Patient is participating in a conflicting study. Patient is unable to perform exercise testing. Patient is mentally incapacitated and cannot consent or comply with follow-up. Patient has New York Heart Association (NYHA) class III/IV heart failure. Patient has left ventricular ejection fraction (LVEF) less than 35% not secondary to tachycardia. Pregnancy. Patient suffers with other cardiac rhythm disorders. Recent coronary artery intervention or other factors suggesting clinical instability (ECG, clinical or laboratory findings).", "candidate_expression": "((LVEF) AND (NYHA) AND (New York Heart Association class III/IV) AND (Paroxysmal atrial fibrillation persistent) AND (Patient is mentally incapacitated and cannot consent or comply with follow-up) AND (Patient is participating in a conflicting study) AND (Patient is unable to perform exercise testing) AND (Pregnancy) AND (atrial ablation) AND (atrial fibrillation permanent) AND (cardiac rhythm disorders other) AND (coronary artery intervention) AND (heart failure) AND (left ventricular ejection fraction less than 35%) AND (major cardiac surgery last two months) AND (myocardial infarction last two months) AND (oral anti-coagulant medication) AND (pacemaker implantation) AND (tachycardia not secondary to) AND (unstable angina last one week) AND (warfarin))"}
```
