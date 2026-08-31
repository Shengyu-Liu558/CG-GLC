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
{"candidate_id": "LLM07301", "doc_id": "NCT02613039_exc", "case_bucket": "or", "source_criterion": "Participation in another clinical trial. Known or suspected (or history of) malignancy or chronic illness. Serious organic or mental disease diagnosed by a psychiatrist (e.g., major depression currently treated with antidepressant medication) suspected on the basis of the medical history and/or clinical examination. Conditions that may affect the compliance to the study. Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).", "candidate_expression": "((Conditions that may affect the compliance to the study.) AND (Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).) AND (antidepressant medication) AND (history of) AND (major depression suspected) AND (treated currently) AND ((clinical examination) OR (medical history)) AND ((Known) OR (suspected)) AND ((chronic illness) OR (malignancy)) AND ((mental disease) OR (organic disease)))"}
{"candidate_id": "LLM07302", "doc_id": "NCT03221231_inc", "case_bucket": "other", "source_criterion": "Current DSM-IV diagnosis of cannabis dependence, >1 week detoxified and abstinent; Able to provide written informed consent and to comply with study procedures. Dutch speaking (Dutch as primary language).", "candidate_expression": "((>1 week) AND (DSM-IV) AND (abstinent) AND (cannabis dependence) AND (detoxified))"}
{"candidate_id": "LLM07303", "doc_id": "NCT02243553_inc", "case_bucket": "other", "source_criterion": "1. Signed informed consent 2. Healthy subjects aged between 18 years and 45 years inclusive 3. Weighing at least 50 kg 4. Volunteers must be hospitalized on Days 1-4, 7-9, and 17-20 for pharmacokinetic assessments for each biomarker and TPV/r (Days 7-9 and 17-20) 5. Volunteers must be willing to complete all study-related activities 6. Each volunteer must have a valid social security number 7. Each volunteer must have acceptable medical history, physical examination and laboratory test", "candidate_expression": "((Each volunteer must have a valid social security number) AND (Each volunteer must have acceptable medical history, physical examination and laboratory test) AND (Healthy) AND (Signed informed consent) AND (Volunteers must be hospitalized on Days 1-4, 7-9, and 17-20 for pharmacokinetic assessments for each biomarker and TPV/r (Days 7-9 and 17-20)) AND (Volunteers must be willing to complete all study-related activities) AND (Weighing) AND (aged) AND (at least 50 kg) AND (between 18 years and 45 years inclusive) AND (laboratory test) AND (medical history) AND (physical examination))"}
{"candidate_id": "LLM07304", "doc_id": "NCT02858804_exc", "case_bucket": "or", "source_criterion": "with centre neural system involvement serious complications such as uncontrolled diabetes, gastric ulcer or other serious angiocardiopathy determined by the physician HIV positive or active HBV infection or other uncontrolled systematic infection clinical central nervous dysfunction serious surgery within 30 days pregnancy or baby nursing period or un-contracepted child bearing period woman.", "candidate_expression": "((HIV positive) AND (active HBV infection) AND (angiocardiopathy) AND (baby nursing period) AND (central nervous dysfunction) AND (centre neural system involvement) AND (child bearing period) AND (complications) AND (contracepted) AND (determined by the physician) AND (diabetes) AND (gastric ulcer) AND (pregnancy) AND (serious) AND (surgery) AND (systematic infection) AND (un-) AND (uncontrolled) AND (within 30 days) AND (woman))"}
{"candidate_id": "LLM07305", "doc_id": "NCT02379156_exc", "case_bucket": "or", "source_criterion": "Evidence of sympathetic integrity below the lesion level by the skin axon-reflex vasodilatation (SkARV) test; Known allergies to midodrine hydrochloride; PMH of diagnosed heart, kidney, peripheral vascular, or cerebral vascular disease, or diabetes mellitus; Hypertension (BP>140/90 mmHg); Untreated thyroid disease; Acute illness or infection; Current smoker; Pregnancy.", "candidate_expression": "((BP >140/90 mmHg) AND (Hypertension) AND (Pregnancy) AND (SkARV) AND (allergies) AND (cerebral vascular disease) AND (diabetes mellitus) AND (heart disease) AND (illness) AND (infection) AND (kidney disease) AND (midodrine hydrochloride) AND (peripheral vascular, disease) AND (smoker) AND (test skin axon-reflex vasodilatation sympathetic integrity) AND (thyroid disease Untreated))"}
{"candidate_id": "LLM07306", "doc_id": "NCT03373318_inc", "case_bucket": "other", "source_criterion": "Adult patients (> 18 years) scheduled for cardiopulmonary bypass surgery with Glomerular Filtration Rate (GFR) greater than or equal to 60 and left ventricular ejection fraction greater than or equal to 40%", "candidate_expression": "((Adult) AND (Glomerular Filtration Rate (GFR) greater than or equal to 60) AND (cardiopulmonary bypass surgery scheduled for) AND (left ventricular ejection fraction greater than or equal to 40%) AND (years > 18 years))"}
{"candidate_id": "LLM07307", "doc_id": "NCT02635893_exc", "case_bucket": "or", "source_criterion": "Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease, Any debilitating disease prior to the SCI that caused exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke, Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold such as antipsychotic drugs (chlorpromazine, clozapine) or tricyclic antidepressants. Pregnant females, and Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida or herniated cervical disk. Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease, Any debilitating disease that causes exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke, Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold such as antipsychotic drugs (chlorpromazine, clozapine) or tricyclic antidepressants. Pregnant females, and Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida or herniated cervical disk.", "candidate_expression": "((Metal plate in skull) AND (Pregnant) AND (altered cognitive status) AND (antipsychotic drugs) AND (cardiovascular disease) AND (chlorpromazine) AND (clozapine) AND (cord compression) AND (debilitating disease) AND (debilitating disease prior to the SCI) AND (drugs acting primarily on the central nervous system lower the seizure threshold) AND (exercise intolerance) AND (females) AND (head injury History) AND (head injury History of) AND (herniated cervical disk) AND (major depression) AND (medical problems Uncontrolled) AND (orthopedic disease) AND (psychosis) AND (pulmonary disease) AND (seizures) AND (seizures History of) AND (spina bifida) AND (spinal cord disease) AND (spinal stenosis) AND (stroke History) AND (stroke History of) AND (syrinx spinal cord) AND (tricyclic antidepressants))"}
{"candidate_id": "LLM07308", "doc_id": "NCT03100513_exc", "case_bucket": "or", "source_criterion": "Patients with active GIT bleeding. Patients with history of bowel obstruction, perforation. Patients with history of allergy to PEG. Treatment with rifaximin or neomycin in the previous 7 days. Patients with major psychiatric illness. Patients receiving benzodiazepines and narcotics. Patients with compromised renal. Patients receiving medications highly bound to plasma proteins eg. Warfarin. Pregnant or lactating women. Fulminant hepatic failure.", "candidate_expression": "((GIT bleeding active) AND (PEG) AND (Warfarin) AND (allergy history) AND (compromised renal) AND (hepatic failure Fulminant) AND (major psychiatric illness) AND (medications highly bound to plasma proteins) AND (women) AND ((neomycin) OR (rifaximin)) AND ((benzodiazepines) OR (narcotics)) AND ((Pregnant) OR (lactating)) AND ((bowel obstruction) OR (bowel perforation)))"}
{"candidate_id": "LLM07309", "doc_id": "NCT02145026_inc", "case_bucket": "or", "source_criterion": "Adult participants with low or intermediate-1 risk MDS No previous treatment with hematopoietic growth factors within 3 months prior to screening Symptomatic anemia (hemoglobin <10 g/dL) as determined by investigator Serum erythropoietin <500 milliunits/milliliter (mU/mL) within 14 days prior to the first dose of study treatment Require no red blood cell transfusion or dependent on <4 units within 8 weeks prior to screening Clinically stable for at least 1 month prior to entry into the study For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception", "candidate_expression": "((Adult low risk) AND (For female participants of childbearing potential and male participants with partners of childbearing potential, agreement (by participants and/or partner) to use highly effective form(s) of contraception) AND (MDS intermediate-1 risk) AND (Serum erythropoietin <500 milliunits/milliliter within 14 days prior to the first dose of study treatment) AND (anemia Symptomatic) AND (hematopoietic growth factors within 3 months prior to screening) AND (hemoglobin <10 g/dL) AND (stable for at least 1 month prior to entry into the study) AND NOT (red blood cell transfusion <4 units within 8 weeks prior to screening))"}
{"candidate_id": "LLM07310", "doc_id": "NCT03620526_inc", "case_bucket": "or", "source_criterion": "presence of typical HF symptoms and signs LV ejection fraction = 50 elevated levels of NT-proBNP (at least >125 pg/ml) echocardiographic structural (a left atrial volume index > 34 mL/m2 or a left ventricular mass index =115 g/m2 for males and =95 g/m2 for females) or functional alterations (E/e'=13 and a mean e' septal and lateral wall < 9 cm/s).", "candidate_expression": "((E/e' =13) AND (HF signs) AND (HF symptoms) AND (LV ejection fraction = 50) AND (NT-proBNP elevated at least >125 pg/ml) AND (echocardiographic structural) AND (females) AND (functional alterations) AND (males) AND (mean e' septal and lateral wall < 9 cm/s) AND ((left atrial volume inde > 34 mL/m2) OR (left ventricular mass index =115 g/m2) OR (left ventricular mass index =95 g/m2)))"}
{"candidate_id": "LLM07311", "doc_id": "NCT02590315_inc", "case_bucket": "other", "source_criterion": "Asymptomatic women 45-68 years, residents in the Piedmont Region, attending the regional breast cancer screening program", "candidate_expression": "((45-68 years) AND (Asymptomatic) AND (Piedmont Region) AND (regional breast cancer screening program) AND (women))"}
{"candidate_id": "LLM07312", "doc_id": "NCT02361905_exc", "case_bucket": "other", "source_criterion": "submucosal leiomyoma, endometrial hyperplasia with atypia, history of uterine surgery", "candidate_expression": "((endometrial hyperplasia with atypia) AND (submucosal leiomyoma) AND (uterine surgery history))"}
{"candidate_id": "LLM07313", "doc_id": "NCT00720031_exc", "case_bucket": "or", "source_criterion": "Cardio-vascular pathologies, evoluting and uncontrolled, (severe HTA), cardiac deficiency, severe angor, severe arrhythmia. Infectious pathologies evoluting and requiring antibiotherapy. Patients HIV+. Transplanted patients or patients suffering from severe auto-immune disease. Psychiatric troubles that do not allow the protocol follow-up. Pregnant or breast-feeding women. No contraception.", "candidate_expression": "((+) AND (Cardio-vascular pathologies) AND (HIV) AND (HIV+) AND (HTA) AND (Infectious pathologies) AND (No) AND (Pregnant) AND (Psychiatric troubles) AND (Transplanted) AND (angor) AND (antibiotherapy) AND (arrhythmia) AND (breast-feeding) AND (cardiac deficiency) AND (contraception) AND (do not allow the protocol follow-up) AND (evoluting) AND (requiring antibiotherapy) AND (severe) AND (severe auto-immune disease) AND (uncontrolled) AND (women))"}
{"candidate_id": "LLM07314", "doc_id": "NCT01866800_inc", "case_bucket": "other", "source_criterion": "Subject is 65 years old who is able and willing to give an informed consent. Patients undergoing planned trans-femoral TAVI. Calculated eGFR below 60ml/min/1.73m2 (MDRD)", "candidate_expression": "((65 years) AND (Calculated eGFR) AND (able and willing to give an informed consent) AND (below 60ml/min/1.73m2) AND (old) AND (planned) AND (trans-femoral TAVI) AND (undergoing))"}
{"candidate_id": "LLM07315", "doc_id": "NCT02946892_exc", "case_bucket": "or", "source_criterion": "The use of beta blockers within 2 months of randomization Patients actively listed for transplantation at time of entry into the study or anticipated to undergo heart transplantation, interventional catheterization, or corrective cardiac surgery during the 7 months following entry into the study Sustained or symptomatic ventricular dysrhythmias uncontrolled by drug therapy or the use of an implantable defibrillator, and/or significant cardiac conduction defects, e.g., 2nd degree or 3rd degree AV block, or sick sinus syndrome, unless a functioning pacemaker is in place Uncorrected obstructive or severe regurgitant valve disease, nondilated cardiomyopathy, or significant systemic ventricular outflow obstruction Known renovascular hypertension or evidence of pulmonary hypertension (pulmonary vascular resistance > 6 Wood units) unresponsive to vasodilator agents such as oxygen, nitroprusside, or nitric oxide History or current clinical evidence of moderate-to-severe fixed obstructive pulmonary disease or severe reactive airway diseases (e.g., asthma) requiring hospitalization within the past 2 years or patient currently using long-term inhaled bronchodilators Renal, hepatic, gastrointestinal, or biliary disorder that could impair absorption, metabolism or excretion of orally administered medication Concurrent terminal illness or other severe disease (e.g., active neoplasm) or other significant laboratory value(s) which, in the opinion of the investigator, could preclude participation or survival Endocrine disorders such as primary aldosteronism, pheochromocytoma, hyper- or hypothyroidism, insulin-dependent diabetes mellitus Unwillingness or inability to cooperate, or for the parents or guardians to give consent, or for the child to give assent, or any condition of sufficient severity to impair cooperation in the study Pregnancy or possible pregnancy at time of randomization, or female of child bearing potential who are lactating, or sexually active and not taking adequate contraceptive precautions (e.g., intrauterine device or oral contraceptives for 3 months prior to entry into the study) Use of an investigational drug within 30 days of randomization, or within 5 half-lives of the investigational drug (the longer period will apply) History of drug sensitivity or allergic reaction to alpha-blockers or beta-blockers Use of any of the following medications within two weeks of randomization: MAO inhibitors, Calcium channel blockers, alpha blockers, beta blockers, disopyramide, flecainide, encainide, moricizine, propafenone, sotalol, or beta adrenergic agonists Hospital admission for protein losing enteropathy or plastic bronchitis within 3 months of randomization Active and/or chronic protein losing enteropathy or plastic bronchitis (on inhaled medication to control the plastic bronchitis). Hypoalbuminemia defined as serum albumin <2.0g/dL Renal dysfunction defined as serum creatinine >2.0mg/dL Hepatic dysfunction defined as serum AST and/or ALT> 3 times upper limit of normal (approximately 120 IU/L however, will vary depending on age), Significant anemia or polycythemia defined as hemoglobin >18gm/dL or hemoglobin <7gm/dL Severely elevated serum BNP defined as BNP>300pg/ml", "candidate_expression": "((<2.0g/dL) AND (<7gm/dL) AND (> 3 times upper limit of normal) AND (> 6 Wood units) AND (>18gm/dL) AND (>2.0mg/dL) AND (>300pg/ml) AND (BNP) AND (Concurrent) AND (Endocrine disorders) AND (Hepatic dysfunction) AND (History) AND (Hospital admission) AND (Hypoalbuminemia) AND (Renal dysfunction) AND (Severely elevated) AND (Significant) AND (Uncorrected) AND (active) AND (adequate) AND (anticipated to undergo) AND (approximately 120 IU/L) AND (asthma) AND (at time of entry into the study) AND (at time of randomization) AND (beta blockers) AND (cardiac conduction defects) AND (child bearing potential) AND (clinical evidence of) AND (contraceptive precautions) AND (currently) AND (disorder) AND (drug) AND (drug therapy) AND (during the 7 months following entry into the study) AND (entry into the study) AND (evidence of) AND (female) AND (fixed) AND (for 3 months prior to entry into the study) AND (functioning) AND (impair absorption) AND (impair excretion) AND (impair metabolism) AND (implantable defibrillator) AND (inhaled medication) AND (insulin-dependent) AND (investigational drug) AND (laboratory) AND (lactating) AND (listed for transplantation) AND (moderate-to-severe) AND (neoplasm) AND (not) AND (obstructive pulmonary disease) AND (orally administered medication) AND (other) AND (pacemaker) AND (possible) AND (pulmonary hypertension) AND (pulmonary vascular resistance) AND (randomization) AND (reactive airway diseases) AND (renovascular hypertension) AND (requiring) AND (serum BNP) AND (serum albumin) AND (serum creatinine) AND (severe) AND (sexually active) AND (significant) AND (the past 2 years) AND (time of randomization) AND (transplantation) AND (unless) AND (unresponsive to vasodilator agents) AND (vasodilator agents) AND (ventricular dysrhythmias) AND (within 2 months of randomization) AND (within 3 months of randomization) AND (within the past 2 years) AND (within two weeks of randomization) AND ((diabetes mellitus) OR (hyper thyroidism) OR (hypothyroidism) OR (pheochromocytoma) OR (primary aldosteronism)) AND ((corrective cardiac surgery) OR (heart transplantation) OR (interventional catheterization)) AND ((Unwillingness for the guardians to give consent) OR (Unwillingness for the parents to give consent) OR (Unwillingness to cooperate) OR (inability for the guardians to give consent) OR (inability for the parents to give consent) OR (inability to cooperate)) AND ((Pregnancy) OR (pregnancy)) AND ((intrauterine device) OR (oral contraceptives)) AND ((within 30 days of randomization) OR (within 5 half-lives of the investigational drug)) AND ((allergic reaction) OR (drug sensitivity)) AND ((alpha-blockers) OR (beta-blockers)) AND ((Calcium channel blockers) OR (MAO inhibitors) OR (alpha blockers) OR (beta adrenergic agonists) OR (beta blockers) OR (disopyramide) OR (encainide) OR (flecainide) OR (moricizine) OR (propafenone) OR (sotalol)) AND ((Sustained) OR (symptomatic)) AND ((plastic bronchitis) OR (protein losing enteropathy)) AND ((Active) OR (chronic)) AND ((serum ALT) OR (serum AST)) AND ((uncontrolled by drug therapy) OR (uncontrolled by the use of an implantable defibrillator)) AND ((anemia) OR (polycythemia)) AND ((hemoglobin)) AND ((2nd degree AV block) OR (3rd degree AV block) OR (sick sinus syndrome)) AND ((nondilated cardiomyopathy) OR (obstructive valve disease) OR (regurgitant valve disease) OR (systemic ventricular outflow obstruction)) AND ((nitric oxide) OR (nitroprusside) OR (oxygen)) AND ((History) OR (current)) AND ((hospitalization) OR (long-term inhaled bronchodilators)) AND ((Renal) OR (biliary) OR (gastrointestinal) OR (hepatic)) AND ((severe disease) OR (significant laboratory value(s)) OR (terminal illness)))"}
{"candidate_id": "LLM07316", "doc_id": "NCT03181984_exc", "case_bucket": "or", "source_criterion": "Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((Allergic constitution) AND (Allergy) AND (Be judged not suitable to participate the study by the investigators) AND (Photosensitivity) AND (Porphyria) AND (Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application) AND (Scar diathesis) AND (porphyrins) AND (porphyrins analogues))"}
{"candidate_id": "LLM07317", "doc_id": "NCT02365870_inc", "case_bucket": "other", "source_criterion": "Diagnosis of DSM 5 Anxiety Disorder Stable medical history and general health On stable anti-parkinsonian therapy for 2 weeks before enrollment", "candidate_expression": "((DSM 5 Anxiety Disorder) AND (Stable general health) AND (Stable medical history) AND (anti-parkinsonian therapy stable for 2 weeks before enrollment))"}
{"candidate_id": "LLM07318", "doc_id": "NCT00502567_inc", "case_bucket": "or", "source_criterion": "histologically confirmed metastatic cancer that is not amenable to surgery or radiation therapy with curative intent measurable lesion by CT or other techniques according to RECIST", "candidate_expression": "((CT) AND (histologically confirmed) AND (measurable lesion) AND (metastatic cancer) AND (radiation therapy not amenable) AND (surgery not amenable))"}
{"candidate_id": "LLM07319", "doc_id": "NCT03082573_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07320", "doc_id": "NCT02894268_exc", "case_bucket": "or", "source_criterion": "Bismuth compounds, acid inhibitor, or antibiotics during 4 weeks before the patient is enrolled Allergic to the medications Upper gastrointestinal surgery history Serious heart insufficiency, liver insufficiency, renal insufficiency and other serious medical problems Evidence of blood dyscrasia Pregnant and lactating women Can't express his complain correctly and can't cooperate with the researcher", "candidate_expression": "((Allergic) AND (Upper gastrointestinal surgery history) AND (blood dyscrasia Evidence) AND (medications) AND (women) AND ((Bismuth compounds) OR (acid inhibitor) OR (antibiotics)) AND ((heart insufficiency Serious) OR (liver insufficiency) OR (renal insufficiency) OR (serious medical problems other)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM07321", "doc_id": "NCT03351972_inc", "case_bucket": "other", "source_criterion": "Adult outpatients (18 years or older) routinely referred for small bowel video capsule endoscopy (CE)", "candidate_expression": "((Adult 18 years or older) AND (outpatients) AND (small bowel video capsule endoscopy routinely referred))"}
{"candidate_id": "LLM07322", "doc_id": "NCT03539718_inc", "case_bucket": "or", "source_criterion": "Patients on regular hemodialysis 3sessions/wk. Recent catheter insertion at beginning of the study. Both males and females. Age group = 18 ys.", "candidate_expression": "((3sessions/wk) AND (= 18 ys) AND (Age group) AND (Recent) AND (at beginning of the study) AND (beginning of the study) AND (catheter insertion) AND (regular hemodialysis) AND ((females) OR (males)))"}
{"candidate_id": "LLM07323", "doc_id": "NCT03431831_exc", "case_bucket": "or", "source_criterion": "Inability to understand and read English. Women pregnant or lactating. persons with terminal illness", "candidate_expression": "((Inability to understand and read English) AND (Women) AND (terminal illness) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM07324", "doc_id": "NCT02245256_inc", "case_bucket": "or", "source_criterion": "Adult patients (18years old or older) undergoing living-donor or deceased-donor liver transplantation", "candidate_expression": "((Adult) AND (years 18years old or older) AND ((deceased-donor liver transplantation) OR (living-donor liver transplantation)))"}
{"candidate_id": "LLM07325", "doc_id": "NCT03088904_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
