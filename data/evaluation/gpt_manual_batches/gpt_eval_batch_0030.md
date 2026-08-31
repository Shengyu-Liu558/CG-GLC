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
{"candidate_id": "LLM00726", "doc_id": "NCT02498483_inc", "case_bucket": "other", "source_criterion": "Apgar score at 5 minutes >7 birthweight greater than 2.4 kg Age of at least 10 hours At least one void.", "candidate_expression": "((>7) AND (Age) AND (Apgar score) AND (At least one) AND (at 5 minutes) AND (at least 10 hours) AND (birthweight) AND (greater than 2.4 kg) AND (void))"}
{"candidate_id": "LLM00727", "doc_id": "NCT02106624_exc", "case_bucket": "other", "source_criterion": "irreversible status of primary disease any history of malnutrition before enrollment history of steroid cortisol administration severe liver dysfunction (Child-Pugh Score C) pregnancy refuse to enrollment re-admission to ICU and has been enrolled during former admission to ICU", "candidate_expression": "((C) AND (Child-Pugh Score) AND (ICU) AND (before enrollment) AND (irreversible status) AND (liver dysfunction) AND (malnutrition) AND (pregnancy) AND (primary disease) AND (re-admission) AND (refuse to enrollment) AND (severe) AND (steroid cortisol))"}
{"candidate_id": "LLM00728", "doc_id": "NCT02830360_inc", "case_bucket": "or", "source_criterion": "Prior Myocardial Infarction and Sustained monomorphic VT documented on 12-lead ECG or rhythm strip terminated by pharmacologic means or DC cardioversion =3 episodes of VT treated with antitachycardia pacing (ATP), at least one of which was symptomatic = 5 episodes of VT treated with antitachycardia pacing (ATP) regardless of symptoms =1 appropriate ICD shocks, =3 VT episodes within 24 hours", "candidate_expression": "((ATP) AND (ICD shocks =1) AND (Myocardial Infarction) AND (VT 3 episodes symptomatic) AND (VT 3 episodes within 24 hours) AND (VT 5 episodes) AND (antitachycardia pacing) AND (monomorphic VT Sustained) AND ((12-lead ECG) OR (rhythm strip)) AND ((DC cardioversion) OR (pharmacologic means)))"}
{"candidate_id": "LLM00729", "doc_id": "NCT02323399_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00730", "doc_id": "NCT01856491_inc", "case_bucket": "or", "source_criterion": "Willing and capable of providing informed consent Has an indication for implantation of a single or dual chamber ICD or CRT-D system in their respective geography Subjects planned to be implanted with the RELIANCE 4-FRONT Passive Fixation Lead Willing and capable of participating in all testing/ visits associated with this clinical study at an approved clinical study center and at the intervals defined by this protocol Age 18 or above, or of legal age to give informed consent specific to state and national law", "candidate_expression": "((Age) AND (RELIANCE 4-FRONT Passive Fixation Lead) AND (Willing and capable of providing informed consent) AND (implanted with the RELIANCE 4-FRONT Passive Fixation Lead) AND (indication) AND (planned) AND ((18 or above) OR (of legal age)) AND ((CRT-D system implantation of a) OR (chamber ICD implantation of a single) OR (dual chamber ICD implantation of a)))"}
{"candidate_id": "LLM00731", "doc_id": "NCT02667730_inc", "case_bucket": "or", "source_criterion": "Acquired acute ankle injury (injured less than 48 hours ago); Clinical diagnosis of a Grade I or II ankle sprain Is eligible to receive comprehensive medical care from Garrison Petawawa", "candidate_expression": "((Acquired) AND (Grade I) AND (Grade II) AND (acute ankle injury) AND (ankle sprain) AND (less than 48 hours ago))"}
{"candidate_id": "LLM00732", "doc_id": "NCT02903407_exc", "case_bucket": "or", "source_criterion": "Exclusion criteria include patients following resuscitation from cardiac arrest who are treated on the cooling protocol patients who have suffered a neurologic event (seizure, stroke) or who have baseline dementia, both of which could limit delirium assessment patients with child class B and C liver disease patients with known allergy to study medications.", "candidate_expression": "((allergy) AND (child class) AND (liver disease) AND (resuscitation from cardiac arrest cooling protocol) AND (study medications) AND ((B) OR (C)) AND ((seizure) OR (stroke)) AND ((baseline dementia) OR (neurologic event)))"}
{"candidate_id": "LLM00733", "doc_id": "NCT01912677_exc", "case_bucket": "or", "source_criterion": "Indication for emergent cesarean or known fetal anomaly Anti-hypertensive therapy received in the past 12 hours History of eclampsia or other adverse CNS complication (e.g., stroke or PRES) in this pregnancy Actively wheezing at time of enrollment or history of asthma complications Known coronary artery disease or type I DM with microvascular complications or signs of heart failure or clinical dissection of the aorta", "candidate_expression": "((Anti-hypertensive therapy) AND (at time of enrollment) AND (emergent cesarean) AND (enrollment) AND (in this pregnancy) AND (microvascular complications) AND (past 12 hours) AND ((Indication) OR (fetal anomaly)) AND ((asthma complications) OR (wheezing)) AND ((coronary artery disease) OR (dissection of the aorta) OR (heart failure) OR (type I DM)) AND ((CNS complication) OR (eclampsia)) AND ((PRES) OR (stroke)))"}
{"candidate_id": "LLM00734", "doc_id": "NCT03168555_exc", "case_bucket": "or", "source_criterion": "small bowel resection right sided hemicolectomy known chronic diarrheal disease (celiac disease, lactose malabsorption, Inflammatory bowel diseases, incl microscopic colitis) pregnancy wish for pregnancy within next three months allergy to eggs allergy to constituents in Xenbilox (capsules with chenodeoxycholic acid) acute cholecystitis within two months chronic cholecystitis cirrhosis of the liver suspected obstructive choledocholithiasis icterus", "candidate_expression": "((Inflammatory bowel diseases) AND (acute cholecystitis) AND (allergy) AND (celiac disease) AND (chenodeoxycholic acid) AND (chronic cholecystitis) AND (chronic diarrheal disease) AND (cirrhosis of the liver) AND (constituents in Xenbilox) AND (eggs) AND (icterus) AND (lactose malabsorption) AND (microscopic colitis) AND (obstructive choledocholithiasis) AND (pregnancy) AND (right sided hemicolectomy) AND (small bowel resection) AND (suspected) AND (wish for) AND (within next three months) AND (within two months))"}
{"candidate_id": "LLM00735", "doc_id": "NCT02385045_inc", "case_bucket": "or", "source_criterion": "• All patients attending for a routine diagnostic endoscopic procedure at St Mary's Hospital NHS Trust for dyspepsia and abdominal pain", "candidate_expression": "((St Mary's Hospital NHS Trust) AND (diagnostic endoscopic procedure) AND ((abdominal pain) OR (dyspepsia)))"}
{"candidate_id": "LLM00736", "doc_id": "NCT02393287_inc", "case_bucket": "or", "source_criterion": "1. Age ≥ 18 years 2. Patient with breast cancer, histologically proven, metastatic or locally advanced 3. Patient treated by Eribulin between January and October 2014 (for the retrospective part) or between November 2014 and September 2015 (for the prospective part). 4. Patient with at least an assessment of the response to Eribulin", "candidate_expression": "((Age ≥ 18 years) AND (Eribulin) AND (assessment of the response) AND (breast cancer) AND ((between January and October 2014) OR (between November 2014 and September 2015)) AND ((histologically proven) OR (locally advanced) OR (metastatic)))"}
{"candidate_id": "LLM00737", "doc_id": "NCT02695992_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure Ischemic heart disease Hypotension (Systolic blood pressure <100 mmHg) Treatment with class I or III antiarrhythmic drugs Severe hepatic or renal failure Pregnancy or lactation Hypersensitivity or contradictions to study drugs Atrio-ventricular conduction disturbances Thyrotoxicosis Life limiting disease or substance abuse which may affect participation", "candidate_expression": "((<100 mmHg) AND (Atrio-ventricular conduction disturbances) AND (Congestive heart failure) AND (Hypotension) AND (Ischemic heart disease) AND (Severe) AND (Systolic blood pressure) AND (Thyrotoxicosis) AND (antiarrhythmic drugs) AND (may affect participation) AND (study drugs) AND ((hepatic failure) OR (renal failure)) AND ((Pregnancy) OR (lactation)) AND ((Hypersensitivity) OR (contradictions)) AND ((Life limiting disease) OR (substance abuse)) AND ((class I) OR (class III)))"}
{"candidate_id": "LLM00738", "doc_id": "NCT03472846_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus type 1 renal insufficiency III-V ° Cirrhosis hepatis (Child B or higher) Chronic alcohol abuse rheumatic disease (RA, SpA, SLE) Malignancies (<5 years) Eating Disorder (anorexia nervosa, bulimia) bone-specific pretreatment (DMAB, TPTD, strontium ranelate, SERMs) Bisphosphonate treatment is allowed", "candidate_expression": "((<5 years) AND (B or higher) AND (Child) AND (Child B or higher) AND (Chronic) AND (Cirrhosis hepatis) AND (Diabetes mellitus type 1) AND (Eating Disorder) AND (III-V °) AND (Malignancies) AND (alcohol abuse) AND (bone-specific pretreatment) AND (renal insufficiency) AND (rheumatic disease) AND ((RA) OR (SLE) OR (SpA)) AND ((anorexia nervosa) OR (bulimia)) AND ((DMAB) OR (SERMs) OR (TPTD) OR (strontium ranelate)))"}
{"candidate_id": "LLM00739", "doc_id": "NCT02797548_inc", "case_bucket": "or", "source_criterion": "Planned non-cardiac surgery at least after 12 months of implantation of drug eluting stent Low or intermediate risk level surgery Written informed consent", "candidate_expression": "((Planned) AND (Written informed consent) AND (at least after 12 months of implantation of drug eluting stent) AND (drug eluting stent) AND (implantation) AND (implantation of drug eluting stent) AND (intermediate risk level surgery) AND (non-cardiac surgery) AND (risk level surgery Low))"}
{"candidate_id": "LLM00740", "doc_id": "NCT02759861_exc", "case_bucket": "or", "source_criterion": "Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active. Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety. Malignancy diagnosed or treated within 5 years (recent localized treatment of squamous or non-invasive basal cell skin cancers is permitted; cervical carcinoma in situ is allowed if appropriately treated prior to screening); subjects under evaluation for a malignancy are not eligible. Infection with hepatitis B virus (HBV) or human immunodeficiency virus (HIV) Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit. Known hypersensitivity to LDV/SOF", "candidate_expression": "((LDV) AND (Malignancy within 5 years) AND (Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active.) AND (SOF) AND (Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety.) AND (Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit.) AND (hepatitis B virus (HBV)) AND (human immunodeficiency virus (HIV)) AND (hypersensitivity) AND (non-invasive basal cell skin cancer) AND (squamous cell skin cancer) AND (treated appropriately prior to screening) AND NOT (cervical carcinoma in situ) AND NOT (treatment localized recent))"}
{"candidate_id": "LLM00741", "doc_id": "NCT01991743_inc", "case_bucket": "other", "source_criterion": "Healthy patients age 18 and older Breech presentation Singleton gestation .scheduled for ECV desiring CSE.", "candidate_expression": "((Breech presentation) AND (CSE desiring) AND (ECV scheduled for) AND (Healthy) AND (Singleton gestation) AND (age 18 and older))"}
{"candidate_id": "LLM00742", "doc_id": "NCT02375295_inc", "case_bucket": "or", "source_criterion": "Male or Female. No age restriction. Diagnosed with an infection related stone. Medically fit for definitive surgical management of stone. Life expectancy greater than one year. Stone free after definitive surgical therapy defined as fragments less than 3mm.", "candidate_expression": "((Female) AND (Life expectancy greater than one year) AND (Male) AND (definitive surgical management Medically fit for) AND (definitive surgical therapy fragments less than 3mm) AND (stone) AND (stone infection related) AND NOT (Stone))"}
{"candidate_id": "LLM00743", "doc_id": "NCT02871206_exc", "case_bucket": "or", "source_criterion": "Anaphylactic reaction to a previous dose of influenza vaccine or to any of its components Known Immunoglobulin E (IgE)-mediated hypersensitivity to eggs manifested as hives, swelling of the mouth and throat, difficulty in breathing, hypotension, or shock Guillain- Barré syndrome within eight weeks of a previous influenza vaccine Use of aspirin or salicylate- containing products within 30 days before enrollment Household members of children in Group A", "candidate_expression": "((Anaphylactic reaction) AND (Group A) AND (Guillain- Barré syndrome) AND (Household members) AND (Immunoglobulin E (IgE)-mediated hypersensitivity) AND (a previous influenza vaccine) AND (aspirin) AND (children) AND (difficulty in breathing) AND (eggs) AND (hives) AND (hypotension) AND (influenza vaccine) AND (its components) AND (previous) AND (salicylate- containing products) AND (shock) AND (swelling of the mouth) AND (swelling of the throat) AND (within 30 days before enrollment) AND (within eight weeks of a previous influenza vaccine))"}
{"candidate_id": "LLM00744", "doc_id": "NCT03029078_inc", "case_bucket": "or", "source_criterion": "Patient harboring a GRE or CRE bacteria Colonization confirmed by our microbiology department, including at least 3 positives swabs in the last month", "candidate_expression": "((CRE bacteria) AND (Colonization confirmed by our microbiology department) AND (GRE bacteria) AND (swabs at least 3 positives in the last mont))"}
{"candidate_id": "LLM00745", "doc_id": "NCT03475589_exc", "case_bucket": "or", "source_criterion": "Confirmed allergy to apatinin and or its excipients; Hypertension (high blood pressure) that can not be controlled by drugs; A history of active hemorragge, ulcer, intestinal perforation, intestinal obstruction, or major surgery no older than 30 days; NYHA III-IV heart function, or severe hepatic or renal insufficiency (Grade 4); Presence of multiple factors that affect oral medications, such as difficulty swallowing, nausea, vomiting, chronic diarrhea and intestinal obstruction; Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study; Patients who have a history of psychotropics abuse and can not quit, or who have mental disorders; Participation in other drug clinical trial within the last 4 weeks; Prior therapy with VEGFR inhibitors such as sorafenib and sunitinib; Presence of comorbidities that seriously affect the patient's safety or ability to complete the study, in the investigator's judgment; Patients who can not tolerate apatinib treatment as judged by the investigator depending on the their medical history; Patients that are considered ineligible for this study by the investigator.", "candidate_expression": "((Hypertension controlled by drugs) AND (NYHA III-IV) AND (Participation in other drug clinical trial within the last 4 weeks;) AND (Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study;) AND (VEGFR inhibitors) AND (allergy) AND (apatinib) AND (drugs) AND (heart function) AND (hepatic insufficiency Grade 4) AND (high blood pressure) AND (psychotropics) AND (renal insufficiency) AND NOT (tolerate) AND ((hemorragge active) OR (intestinal obstruction) OR (intestinal perforation) OR (major surgery) OR (ulcer)) AND ((apatinin) OR (excipients)) AND ((chronic diarrhea) OR (difficulty swallowing) OR (intestinal obstruction) OR (nausea) OR (vomiting)) AND ((abuse history) OR (mental disorders)) AND ((sorafenib) OR (sunitinib)))"}
{"candidate_id": "LLM00746", "doc_id": "NCT00586898_exc", "case_bucket": "or", "source_criterion": "Clinically significant cardiac disease (New York Heart Association Class III/IV),or severe debilitating puhnonary disease. Uncontrolled serious active infection. Anticipated survival of less than 3 months. Active CNS or epiduraltumor Inability or unwillingness to comply with the treatment protocol, follow-up, or research tests.", "candidate_expression": "((Anticipated survival less than 3 months) AND (CNS tumor) AND (Inability) AND (New York Heart Association Class III/IV) AND (cardiac disease significant) AND (comply with the treatment protocol) AND (debilitating puhnonary disease severe) AND (epiduraltumor) AND (follow-up) AND (infection Uncontrolled serious) AND (research tests) AND (unwillingness))"}
{"candidate_id": "LLM00747", "doc_id": "NCT03364036_exc", "case_bucket": "or", "source_criterion": "Previous exposure to drugs such as fingolimod, natalizumab, alemtuzumab, mitoxantrone and ocrelizumab. Positive hepatitis C or hepatitis B surface antigen test and/or hepatits B core antibody test for immunoglobulin G (IgG) and/or immunoglobulin M (IgM). Current or previous history of immune deficiency disorders including a positive human immunodeficiency virus (HIV) result. Currently receiving immunosuppressive or myelosuppressive therapy with, for example, monoclonal antibodies, methotrexate, cyclophosphamide, cyclosporine or azathioprine, or chronic use of corticosteroids. History of tuberculosis , presence of active tuberculosis, or latent tuberculosis Evidence or suspect of Progressive Multifocal Leukoencephalopathy (PML) in Magnetic Resonance Imaging (MRI). Active malignancy or history of malignancy. Other protocol defined exclusion criteria could apply.", "candidate_expression": "((Magnetic Resonance Imaging (MRI)) AND (Progressive Multifocal Leukoencephalopathy (PML)) AND (alemtuzumab) AND (azathioprine) AND (corticosteroids chronic use) AND (cyclophosphamide) AND (cyclosporine) AND (drugs Previous) AND (fingolimod) AND (hepatitis B surface antigen test) AND (hepatitis C surface antigen test) AND (hepatits B core antibody test immunoglobulin G (IgG) immunoglobulin M (IgM)) AND (human immunodeficiency virus (HIV) positive) AND (immune deficiency disorders Current previous history) AND (immunosuppressive therapy) AND (malignancy Active) AND (malignancy history) AND (methotrexate) AND (mitoxantrone) AND (monoclonal antibodies) AND (myelosuppressive therapy) AND (natalizumab) AND (ocrelizumab) AND (tuberculosis History) AND (tuberculosis active) AND (tuberculosis latent Evidence suspect))"}
{"candidate_id": "LLM00748", "doc_id": "NCT03305666_exc", "case_bucket": "or", "source_criterion": "Allergy or hypersensitivity to bupivacaine Pregnancy Incarceration Age < 18 years Indwelling continuous thoracic epidural analgesia", "candidate_expression": "((< 18 years) AND (Age) AND (Allergy) AND (Incarceration) AND (Indwelling) AND (Pregnancy) AND (bupivacaine) AND (continuous) AND (hypersensitivity) AND (thoracic epidural analgesia))"}
{"candidate_id": "LLM00749", "doc_id": "NCT00401245_exc", "case_bucket": "or", "source_criterion": "History of a seizure disorder other than a single childhood febrile seizure. History or presence of clinically important hepatic or renal disease or other medical disease. Presence or recent history of major depressive disorder, bipolar disorder, psychotic disorder, or generalized anxiety disorder requiring therapy.", "candidate_expression": "((History) AND (childhood febrile seizure) AND (history) AND (other than) AND (requiring therapy) AND (seizure disorder) AND (single) AND ((bipolar disorder) OR (generalized anxiety disorder) OR (major depressive disorder) OR (psychotic disorder)) AND ((clinically important hepatic disease) OR (clinically important other medical disease) OR (clinically important renal disease)))"}
{"candidate_id": "LLM00750", "doc_id": "NCT03064867_exc", "case_bucket": "or", "source_criterion": "Prior treatment toxicities have not resolved to < Grade 2 according to NCI CTCAE Version 4.0 (except clinically insignificant toxicities such as alopecia). Subjects receiving any other investigational agents. Patients with active tumor lysis syndrome (TLS) either from laboratory or clinical changes. Patients with active central nervous system (CNS) disease defined as symptomatic meningeal lymphoma or known CNS parenchymal lymphoma. History of severe allergic reactions attributed to compounds of similar chemical or biologic composition to rituximab or other agents used in this study. Subjects with uncontrolled intercurrent illness . HIV-positive subjects on combination antiretroviral therapy are ineligible because of the potential for pharmacokinetic interactions with Venetoclax. In addition, these subjects are at increased risk of lethal infections when treated with marrow suppressive therapy. Appropriate studies will be undertaken in subjects receiving combination antiretroviral therapy when indicated. HIV testing prior to enrollment is not required for screening but strongly encouraged for patients with no documented prior HIV assessment. Presence of positive test results for hepatitis B virus (HBV), hepatitis B surface antigen (HBsAg), or hepatitis C (HCV) antibody. Patients who are positive for HCV antibody must be negative for HCV by polymerase chain reaction (PCR) to be eligible for study participation Patients with occult or prior HBV infection (defined as positive total hepatitis B core antibody [HBcAb] and negative HBsAg) may be included if HBV DNA is undetectable. These patients must be willing to undergo monthly DNA testing. Women who are pregnant or lactating Malabsorption syndrome or other condition that precludes enteral route of administration Chemotherapy or radiation within 3 weeks of the first scheduled study treatment. Less than 2-year disease free from another primary malignancy (other than squamous or basal cell carcinoma of the skin, \"in-situ\" carcinoma of the cervix or breast, superficial bladder carcinoma, or previously treated localized prostate cancer with normal prostate specific antigen (PSA) levels). Patients who have had completed all anti-cancer treatment for another primary malignancy more than 2 years prior to screening are eligible if they are not considered to have a \"currently active\" malignancy based on having less than a 30% risk of relapse. Major surgery, other than diagnostic surgery, within 2 weeks. Medical condition requiring chronic use of high dose systemic corticosteroids (i.e., doses of prednisone higher than 10 mg/day or equivalent). Brief (<15 days) treatment with glucocorticoids (prednisone 100 mg by mouth daily, or equivalent) is acceptable. Known allergy to both xanthine oxidase inhibitors and rasburicase. Use of warfarin is prohibited. Anticoagulation with low-molecular weight heparin (i.e. enoxaparin) or direct thrombin inhibitors is permitted. The following concomitant medications are not allowed from 7 days prior to the first dose of study drug and during venetoclax administration: Strong CYP3A4 inhibitors including but not limited to fluconazole, ketoconazole, and clarithromycin or strong CYP3A4 inducers included but not limited to rifampin, carbamazepine. Receipt of live-virus vaccines within 28 days prior to the initiation of study treatment or need for live-virus vaccines at any time during study treatment. Concomitant medications that fall into the categories below could potentially lead to adverse reactions and should be considered cautionary. Moderate/Weak CYP3A inducers such as efavirenz and oxcarbazepine CYP2C8 substrates such as thiazolidinediones (glitazones) and select statins (because of expected inhibition of the metabolism of CYP2C8 substrates) by venetoclax CYP2C9 substrates such as tolbutamide (because of expected inhibition of the metabolism of CYP2C9 substrates by venetoclax. It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin.", "candidate_expression": "((\"in-situ\" carcinoma of the cervix) AND (\"in-situ\" carcinoma of the cervix breast) AND (Anticoagulation) AND (CNS parenchymal lymphoma) AND (CYP2C8 substrates) AND (CYP2C9 substrates) AND (CYP2C9 substrates narrow therapeutic index) AND (Chemotherapy within 3 weeks of the first scheduled study treatment) AND (HBV DNA undetectable) AND (HBV infection) AND (HBsAg negative) AND (HCV antibody positive) AND (HCV negative) AND (HIV-positive) AND (It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin) AND (Major surgery within 2 weeks) AND (Malabsorption syndrome) AND (Medical condition) AND (Moderate CYP3A inducers) AND (Strong CYP3A4 inhibitors) AND (Weak CYP3A inducers) AND (Women) AND (allergic reactions severe) AND (allergy) AND (carbamazepine) AND (central nervous system (CNS) disease) AND (clarithromycin) AND (combination antiretroviral therapy) AND (compounds of similar chemical or biologic composition to other agents used in this study) AND (compounds of similar chemical or biologic composition to rituximab) AND (condition that precludes enteral route of administration) AND (direct thrombin inhibitors) AND (disease free Less than 2-year) AND (efavirenz) AND (enoxaparin) AND (fluconazole) AND (glitazones) AND (glucocorticoids <15 days) AND (hepatitis B surface antigen (HBsAg) positive) AND (hepatitis B virus (HBV) positive) AND (hepatitis C (HCV) antibody positive) AND (ketoconazole) AND (lactating) AND (live-virus vaccines any time during) AND (live-virus vaccines within 28 days prior) AND (localized prostate cancer) AND (low-molecular weight heparin) AND (meningeal lymphoma symptomatic) AND (need for) AND (oxcarbazepine) AND (phenytoin) AND (polymerase chain reaction (PCR)) AND (prednisone 100 mg daily) AND (prednisone higher than 10 mg/day) AND (pregnant) AND (primary malignancy another) AND (prostate specific antigen (PSA) levels normal) AND (radiation within 3 weeks of the first scheduled study treatment) AND (rasburicase) AND (rifampin) AND (squamous or basal cell carcinoma of the skin) AND (statins select) AND (strong CYP3A4 inducers) AND (superficial bladder carcinoma) AND (systemic corticosteroids chronic high dose) AND (thiazolidinediones) AND (tolbutamide) AND (total hepatitis B core antibody [HBcAb] positive) AND (tumor lysis syndrome (TLS)) AND (venetoclax 7 days prior) AND (venetoclax administration) AND (warfarin) AND (xanthine oxidase inhibitors) AND NOT (anti-cancer treatment more than 2 years prior) AND NOT (diagnostic surgery))"}
```
