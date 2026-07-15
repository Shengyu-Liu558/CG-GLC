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
{"candidate_id": "LLM01726", "doc_id": "NCT02974686_inc", "case_bucket": "or", "source_criterion": "Kidney transplant recipients at Washington University/Barnes-Jewish Hospital Experiencing GI toxicity from MPA as determined by the treating physician within 12 months post-renal transplant On standard immunosuppression with tacrolimus and prednisone", "candidate_expression": "((GI toxicity) AND (Kidney transplant) AND (MPA) AND (Washington University/Barnes-Jewish Hospital) AND (prednison) AND (standard immunosuppression) AND (tacrolimus))"}
{"candidate_id": "LLM01727", "doc_id": "NCT02464865_inc", "case_bucket": "other", "source_criterion": "obese : weight for height > median + 3 standard deviations simple obesity", "candidate_expression": "((obese) AND (simple obesity) AND (weight for height > median + 3 standard deviations))"}
{"candidate_id": "LLM01728", "doc_id": "NCT02256956_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((Alcohol abuse) AND (CYP3A inducers) AND (CYP3A inhibitors) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Heart disease) AND (Male Healthy) AND (Metabolic Equivalents >7) AND (Neurological disease) AND (Obstructive uropathy) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction Suspicion tested sites) AND (tested drugs) AND (treatment Ongoing))"}
{"candidate_id": "LLM01729", "doc_id": "NCT02606565_inc", "case_bucket": "other", "source_criterion": "Newborns weighing 1.5kg or more at birth", "candidate_expression": "((1.5kg or more) AND (Newborns) AND (at birth) AND (weighing))"}
{"candidate_id": "LLM01730", "doc_id": "NCT02713087_exc", "case_bucket": "or", "source_criterion": "Age younger than 18 yrs. or older than 75 yrs. Pregnancy or nursing (negative pregnancy blood test) History of allergic reactions to phenylephrine or ephedrine eGFR < 60ml/min/1.73m2", "candidate_expression": "((< 60ml/min/1.73m2) AND (Age) AND (History) AND (allergic reactions) AND (eGFR) AND (negative) AND (pregnancy blood test) AND (younger than 18 yrs. or older than 75 yrs.) AND ((ephedrine) OR (phenylephrine)) AND ((Pregnancy) OR (nursing)))"}
{"candidate_id": "LLM01731", "doc_id": "NCT01639664_inc", "case_bucket": "other", "source_criterion": "All patients admitted to the ICU in septic shock All patients that develop septic shock while in the ICU", "candidate_expression": "((ICU) AND (admitted) AND (septic shock) AND (septic shock while in the ICU))"}
{"candidate_id": "LLM01732", "doc_id": "NCT02260206_inc", "case_bucket": "or", "source_criterion": "Patients needed to pericardiocentesis during RFCA for paroxysmal or persistent atrial fibrillation.", "candidate_expression": "((RFCA paroxysmal persistent) AND (atrial fibrillation) AND (pericardiocentesis during RFCA))"}
{"candidate_id": "LLM01733", "doc_id": "NCT02884115_inc", "case_bucket": "other", "source_criterion": "Early Syphilis Cases Determined to Be Serofast at 6 Months after Initial Treatment", "candidate_expression": "((6 Months after Initial Treatment) AND (Early Syphilis) AND (Initial) AND (Initial Treatment) AND (Serofast) AND (Treatment))"}
{"candidate_id": "LLM01734", "doc_id": "NCT02399033_inc", "case_bucket": "or", "source_criterion": "Age: 20-70 years old; Gender: male or female; clinical or pathological diagnosis of hepatocellular carcinoma (HCC) in previously untreated patients; The expected survival> 3 months; Child-Pugh grade in A-level; KPS score with 50-100 points; BCLC stage of 0-B; conform to the indications of hepatectomy; Viable tumor resection confirmed by two highly qualified surgical doctors; No other surgical contraindications. women in the reproductive period must be completely contraception in 28 days before treatment, during the treatment process and in 28 days after treatment; Men must be completely contraception and prohibited donation and sperm donation during the treatment process and in 28 days after treatment; All patients must be prohibited donation during the treatment process and in 28 days after treatment; In addition to the subjects, prohibitting other people taking this product. patients have a good understanding and could coordinate with investigators for the trial. Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial.", "candidate_expression": "((Age 20-70 years old) AND (BCLC stage 0-B) AND (Child-Pugh grade A) AND (Gender) AND (HCC) AND (KPS score 50-100 points) AND (Men in 28 days after treatment during the treatment process) AND (Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial) AND (Viable tumor resection confirmed by two highly qualified surgical doctors) AND (contraception during the treatment process in 28 days before treatment) AND (expected survival > 3 months) AND (hepatectomy) AND (hepatocellular carcinoma clinical or pathological diagnosis untreated) AND (indications of hepatectomy) AND (patients have a good understanding and could coordinate with investigators for the trial) AND (reproductive period) AND (women) AND ((contraception) AND NOT (sperm donation) AND NOT (donation)) AND NOT (other surgical contraindications) AND NOT (donation in 28 days after treatment during the treatment process in 28 days after treatmen) AND ((female) OR (male)))"}
{"candidate_id": "LLM01735", "doc_id": "NCT02746900_exc", "case_bucket": "or", "source_criterion": "Multiple pregnancy Prior spontaneous preterm birth or second trimester losses between 16(0) and 36(6) weeks Cerclage in situ Painful regular uterine contraction and/or preterm labor Ruptured membranes Major fetal defects Active vaginal bleeding Placenda previa and/or accreta Cervical dilation >1.5 cm and/or visible membranes by pelvic exam Suspicion of chorioamnionitis", "candidate_expression": "((Active vaginal bleeding) AND (Cerclage in situ) AND (Major fetal defects) AND (Multiple pregnancy) AND (Ruptured membranes) AND (chorioamnionitis Suspicion of) AND (visible membranes) AND ((Placenda previa) OR (accreta)) AND ((Cervical dilation >1.5 cm) OR (pelvic exam)) AND ((losses second trimester between 16(0) and 36(6) weeks) OR (spontaneous preterm birth)) AND ((Painful regular uterine contraction) OR (preterm labor)))"}
{"candidate_id": "LLM01736", "doc_id": "NCT02897856_inc", "case_bucket": "or", "source_criterion": "Children 6 month to 14 years who will be presented to the pediatric emergency or attended by emergency medical service who have active seizure and had no intravenous access would be eligible for the study.", "candidate_expression": "((Children) AND (seizure active) AND (years 6 month to 14 years) AND NOT (intravenous access) AND ((attended by emergency medical service) OR (pediatric emergency)))"}
{"candidate_id": "LLM01737", "doc_id": "NCT02303171_exc", "case_bucket": "other", "source_criterion": "Women with systemic lupus erythematosus (SLE) Women with active thromboembolic disorders Women with history of previous thromboembolic disorders", "candidate_expression": "((Women) AND (active) AND (history) AND (previous) AND (systemic lupus erythematosus (SLE)) AND (thromboembolic disorders))"}
{"candidate_id": "LLM01738", "doc_id": "NCT02969187_exc", "case_bucket": "or", "source_criterion": "BMI <35 and > 60 kg/m2 Inability to walk (bed-bound or wheelchair dependence) open abdominal surgeries except simple appendectomy and common OB/GYN procedures in the pelvis (hysterectomy, C-section, and oophorectomy, tubal ligation) laparoscopic bowel or solid organ resection except laparoscopic cholecystectomy ventral hernia repair with mesh Preoperative chronic opiate use for chronic pain defined as opiate usage at least 60 mg/day of morphine equivalent for = 3 months (as defined by International Association for the Study of Pain22) in the one year period prior to the bariatric surgery The American Society of Anesthesiologists (ASA) score > 3 History of hypersensitivity or adverse reaction to bupivacaine or narcotics Inability to speak English ventral hernia repair Cholecystectomy hiatal hernia repair with posterior cruroplasty extensive lysis of adhesions other procedures that mandate addition of \"trocar(s)\" or \"feeding tube\" Addition of trocar(s) or conversion of surgery to hand-assisted or open", "candidate_expression": "((<35 and > 60 kg/m2) AND (> 3) AND (Addition of) AND (American Society of Anesthesiologists (ASA) score) AND (BMI) AND (Cholecystectomy) AND (Inability to walk) AND (Preoperative) AND (at least 60 mg/day of morphine equivalent) AND (bariatric surgery) AND (chronic) AND (chronic pain) AND (common OB/GYN procedures) AND (except) AND (extensive) AND (for = 3 months) AND (hiatal hernia) AND (in the one year period prior to the bariatric surgery) AND (laparoscopic cholecystectomy) AND (lysis of adhesions) AND (open abdominal surgeries) AND (opiate) AND (pelvis) AND (posterior cruroplasty) AND (repair) AND (repair with mesh) AND (simple appendectomy) AND (surgery) AND (the bariatric surgery) AND (ventral hernia) AND ((C-section) OR (hysterectomy) OR (oophorectomy) OR (tubal ligation)) AND ((laparoscopic bowel resection) OR (solid organ resection)) AND ((adverse reaction) OR (hypersensitivity)) AND ((bupivacaine) OR (narcotics)) AND ((bed-bound) OR (wheelchair dependence)) AND ((conversion of surgery) OR (trocar)) AND ((hand-assisted) OR (open)))"}
{"candidate_id": "LLM01739", "doc_id": "NCT02590653_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01740", "doc_id": "NCT03027115_exc", "case_bucket": "or", "source_criterion": "Intolerability of tamsulosin or related drugs Investigator discretion Unwillingness or inability to comply with protocol procedures and assessments", "candidate_expression": "((Intolerability) AND (Unwillingness or inability to comply with protocol procedures and assessments) AND (related drugs) AND (tamsulosin))"}
{"candidate_id": "LLM01741", "doc_id": "NCT02958566_exc", "case_bucket": "or", "source_criterion": "History of constipation Pre-existing use of narcotics or opioids Pre-existing renal or hepatic failure Mental illness, mental retardation, or inability to participate in informed consent due to mental status Pre-existing dementia Allergy to any protocol medication Emergency operation Subjects who are incarcerated or wards of the state Minors Subjects with inflammatory bowel disease, active colitis, or pre-existing intra-abdominal inflammation. Diverticulitis without active infection/inflammation will not be excluded.", "candidate_expression": "((Allergy) AND (Minors) AND (constipation) AND (dementia Pre-existing) AND (mental status) AND (operation Emergency) AND NOT (Diverticulitis) AND ((Mental illness) OR (inability to participate in informed consent) OR (mental retardation)) AND ((narcotics) OR (opioids)) AND ((colitis active) OR (inflammatory bowel disease) OR (intra-abdominal inflammation pre-existing)) AND ((infection) OR (inflammation)) AND ((hepatic failure) OR (renal failure)))"}
{"candidate_id": "LLM01742", "doc_id": "NCT02964416_exc", "case_bucket": "or", "source_criterion": "Patients with a history of allergy or hypersensitivity to tramadol. History of epilepsy or convulsions due to any reason. Chronic usage of analgesic drugs. Patients using monoamine oxidase inhibitors. Patients with clinical signs of raised ICP. Obesity (women with a body mass index >35 kg/m2 or men with a body mass index >42 kg/m2) Language barrier. Patients taking B-blockers or Ca channel blockers. Patients above 65 years of age ( Physiology difference)", "candidate_expression": "((>35 kg/m2) AND (>42 kg/m2) AND (ICP) AND (Language barrier) AND (Obesity) AND (above 65 years) AND (age) AND (analgesic drugs) AND (men) AND (monoamine oxidase inhibitors) AND (raised) AND (tramadol) AND (women) AND ((allergy) OR (hypersensitivity)) AND ((body mass index)) AND ((B-blockers) OR (Ca channel blockers)) AND ((convulsions) OR (epilepsy)))"}
{"candidate_id": "LLM01743", "doc_id": "NCT03115320_inc", "case_bucket": "other", "source_criterion": "- Patient with IVF cycle and therefore having frozen-thawed embryos Regular menstruation cycle Patient's willingness to participate in the study", "candidate_expression": "((IVF cycle) AND (Patient's willingness to participate in the study) AND (Regular menstruation cycle) AND (frozen-thawed embryos))"}
{"candidate_id": "LLM01744", "doc_id": "NCT02564471_inc", "case_bucket": "or", "source_criterion": "Provide signed and dated informed consent form. Willing to comply with all study procedures and be available for the duration of the study. Male or female, aged = 18 to = 60 years on day of inclusion. In good general health based on medical history and physical exam", "candidate_expression": "((= 18 to = 60 years) AND (Male) AND (Willing to comply with all study procedures and be available for the duration of the study.) AND (aged) AND (female) AND (good general health) AND (medical history) AND (on day of inclusion) AND (physical exam))"}
{"candidate_id": "LLM01745", "doc_id": "NCT02894645_exc", "case_bucket": "or", "source_criterion": "Age less than one year or age greater than/equals to 18 years Previous treatment with cytotoxic agents or high-dose steroids Mixed phenotype acute leukemia (MPAL) ALL as secondary malignancy Abnormal renal or liver function Doubtful compliance or unable to afford full course of therapy", "candidate_expression": "((ALL) AND (MPAL) AND (Mixed phenotype acute leukemia) AND (malignancy secondary) AND (treatment Previous) AND ((Age less than one year) OR (age greater than/equals to 18 years)) AND ((Abnormal liver function) OR (Abnormal renal function)) AND ((Doubtful compliance) OR (unable to afford full course of therapy)) AND ((cytotoxic agents) OR (high-dose steroids)))"}
{"candidate_id": "LLM01746", "doc_id": "NCT03018171_inc", "case_bucket": "other", "source_criterion": "Written maternal informed consent Singleton pregnancy Gestational age = 37 weeks, ASA I BMI < 30 fetus in cephalic presentation", "candidate_expression": "((ASA I) AND (BMI < 30) AND (Gestational age = 37 weeks) AND (Singleton pregnancy) AND (Written maternal informed consent) AND (cephalic presentatio))"}
{"candidate_id": "LLM01747", "doc_id": "NCT02430740_inc", "case_bucket": "other", "source_criterion": "female infertile patients eligible for IVF treatment", "candidate_expression": "((IVF treatment eligible) AND (female) AND (infertile))"}
{"candidate_id": "LLM01748", "doc_id": "NCT03424733_inc", "case_bucket": "or", "source_criterion": "diagnosed any form of MS (relapsing remitting, primary progressive, secondary progressive), any EDSS (expanded stability status scale) score", "candidate_expression": "((MS) AND (any) AND (any form) AND (expanded stability status scale) AND (score EDSS) AND ((primary progressive) OR (relapsing remitting) OR (secondary progressive)))"}
{"candidate_id": "LLM01749", "doc_id": "NCT00445029_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women. Evolutive skin disease on the testing zone (lower back). Patients with a clinically significant disease (chronic, recurrent or active). Systemic corticotherapy or immunosuppressive treatment during the previous month, or local corticoid treatment the week before the patch testing. Local or systemic drug use which interacts with the outcome measures. Exposure to sun or UV radiations, 15 days before the patch testing. Patients deprived of their civic rights, in custody, or subject to a tutorial, judiciary or administrative decision. Patients subject to a protection measure. Patients in a critical medical situation. Patients with a personal situation judged by the investigator as unlikely to be compatible with optimal participation in the study, or which could constitute a risk for the patient. Linguistic barrier or psychological profile preventing the patient from signing the consent form. Patient still in an exclusion period following the participation in another clinical trial. Patients having earned more than 4500€ in indemnities for participation in clinical trials during the previous 12 months, including this study.", "candidate_expression": "((Evolutive skin disease testing zone lower back) AND (critical medical situation) AND (disease clinically significant) AND (drug interacts with the outcome measures) AND (earned more than 4500€ in indemnities) AND (local corticoid treatment the week before) AND (participation in another clinical trial still in an exclusion period following) AND (participation in clinical trials during the previous 12 months) AND (personal situation) AND (subject to a protection measure) AND (women) AND NOT (signing the consent form) AND ((Pregnant) OR (lactating)) AND ((Exposure to UV radiations) OR (Exposure to sun)) AND ((deprived of their civic rights) OR (in custody) OR (subject to a judiciary decision) OR (subject to a tutorial) OR (subject to administrative decision)) AND ((active) OR (chronic) OR (recurrent)) AND ((Local) OR (systemic)) AND ((Linguistic barrier) OR (psychological profile)) AND ((Systemic corticotherapy) OR (immunosuppressive treatment)))"}
{"candidate_id": "LLM01750", "doc_id": "NCT02531724_exc", "case_bucket": "other", "source_criterion": "Ongoing treatment with inotropic drugs (not norepinephrine) Central venous oxygen saturation (ScvO2) < 60% despite optimization of hematocrit and volume status Need of renal replacement therapy Ongoing bleeding Patient or next of kin does not consent with study participation", "candidate_expression": "((Central venous oxygen saturation (ScvO2) < 60% despite) AND (Patient or next of kin does not consent with study participation) AND (bleeding Ongoing) AND (inotropic drugs) AND (optimization of hematocrit) AND (renal replacement therapy Need) AND (treatment Ongoing) AND NOT (norepinephrine))"}
```
