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
{"candidate_id": "LLM00801", "doc_id": "NCT02273791_inc", "case_bucket": "other", "source_criterion": "Women with PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((PCOS) AND (Rotterdam criteria) AND (Women) AND (cleavage-stage embryo at least 2 cryopreserved good))"}
{"candidate_id": "LLM00802", "doc_id": "NCT02986659_inc", "case_bucket": "or", "source_criterion": "Age 65 - 79 History of coronary artery disease (MI/heart attack, stroke, heart failure, or peripheral artery disease) Cancer, with no active treatment in the last year MCI (MoCA >18<26 -inclusive of 1 point if <12 years of education Group 2 Decline physical function (walking speed < 1 m/s) Group 3 (Either or both) Abdominal obesity (>88cm women, >102cm men) AND hypertension (treated or resting blood pressure >140/90 Abdominal obesity (>88cm women, >102cm men) AND hyperlipidemia (treated or fasting total cholesterol >240 English literacy Willing to provide informed consent", "candidate_expression": "((Abdominal) AND (Abdominal obesity) AND (Age 65 - 79) AND (Cancer) AND (Decline physical function) AND (English literacy) AND (MCI) AND (MoCA >18<26) AND (coronary artery disease History) AND (hyperlipidemia) AND (hypertension) AND (provide informed consent Willing to) AND (walking speed < 1 m/s) AND NOT (active treatment in the last year) AND ((men >102cm) OR (women >88cm)) AND ((resting blood pressure >140/90) OR (treated)) AND ((fasting total cholesterol >240) OR (treated)) AND ((MI) OR (heart attack) OR (heart failure) OR (peripheral artery disease) OR (stroke)))"}
{"candidate_id": "LLM00803", "doc_id": "NCT03138577_exc", "case_bucket": "or", "source_criterion": "Patient refusal for supraclavicular block Inability to give informed consent Allergy to local anesthetics Hemidiaphragmatic dysfunction, suspected or known PNP Neuromuscular disease Obstructive or restrictive pulmonary disease Medical or anatomic contraindication to supraclavicular blockade as judged by clinician Pregnancy", "candidate_expression": "((Allergy) AND (Hemidiaphragmatic dysfunction) AND (Inability to give informed consent) AND (Medical) AND (Neuromuscular disease) AND (Obstructive pulmonary disease) AND (PNP) AND (Patient refusal) AND (Pregnancy) AND (anatomic) AND (contraindication) AND (known) AND (local anesthetics) AND (restrictive pulmonary disease) AND (supraclavicular block) AND (supraclavicular blockade) AND (suspected))"}
{"candidate_id": "LLM00804", "doc_id": "NCT02035800_exc", "case_bucket": "other", "source_criterion": "Patients not capable or willing to provide informed consent Patients starting Adalimumab less than five half-lives after the interruption of a previous anti-TNF therapy.", "candidate_expression": "((Adalimumab less than five half-lives after the interruption of a previous anti-TNF therapy) AND (anti-TNF therapy previous))"}
{"candidate_id": "LLM00805", "doc_id": "NCT03499639_exc", "case_bucket": "or", "source_criterion": "Patients with combined HCV/HBV co-infection hepatocellular carcinoma (HCC) decompensated liver cirrhosis (Child-Pugh score above 6) non-genotype 4", "candidate_expression": "((Child-Pugh score) AND (above 6) AND (decompensated) AND (genotype 4) AND (hepatocellular carcinoma (HCC)) AND (liver cirrhosis) AND (non) AND ((HBV infection) OR (HCV infection)))"}
{"candidate_id": "LLM00806", "doc_id": "NCT02543710_exc", "case_bucket": "or", "source_criterion": "Patients who will not get surgical treatment for their endometrial cancer Patients not suffering from endometrial or epithelial ovarian cancer Patients who do not agree to the proposed treatment or will receive (part of) the treatment in a non-participating centre Patients who cannot or do not want to give informed consent (including language barriers)", "candidate_expression": "((agree to the proposed treatment) AND (cannot) AND (do not want to) AND (endometrial cancer) AND (endometrial ovarian cancer) AND (epithelial ovarian cancer) AND (give informed consent) AND (language barriers) AND (non-participating centre) AND (not) AND (surgical treatment) AND (treatment))"}
{"candidate_id": "LLM00807", "doc_id": "NCT02457442_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00808", "doc_id": "NCT02715466_inc", "case_bucket": "or", "source_criterion": "Male or female patients = 18 and = 85 years of age Women of child bearing potential must test negative on standard pregnancy test (urine or serum) Patients with body weight = 55 kg and = 140 kg and body mass index (BMI) = 18 kg/m2 Patients diagnosed severe sepsis / septic shock at admission on Intensive Care Unit who can be enrolled within 90 min after admission OR patients diagnosed severe sepsis / septic shock during Intensive Care Unit stay who can be enrolled within 90 min after diagnosis Patients where antibiotic therapy has already been started (prior to randomization) Patient who are fluid responsive. Fluid responsiveness is defined as increase of > 10% in mean arterial pressure (MAP) after passive leg raising (PLR) Signed informed consent by patient, legal representative or authorized person or deferred consent", "candidate_expression": "((Signed informed consent by patient, legal representative or authorized person or deferred consent) AND (Women) AND (age = 18 and = 85 years) AND (antibiotic therapy prior to randomization) AND (body mass index (BMI) = 18 kg/m2) AND (body weight = 55 kg and = 140 kg) AND (child bearing potential) AND (fluid responsive) AND (mean arterial pressure (MAP) > 10% after passive leg raising (PLR)) AND (standard pregnancy test negative) AND ((Male) OR (female)) AND ((serum) OR (urine)) AND ((septic shock at admission on Intensive Care Unit) OR (severe sepsis at admission on Intensive Care Unit)))"}
{"candidate_id": "LLM00809", "doc_id": "NCT02733159_exc", "case_bucket": "or", "source_criterion": "Untreated symptomatic brain or leptomeningeal metastatic disease. Medical or psychiatric conditions comprising informed consent. Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol. Radiotherapy within 4 weeks of trial entry. Active autoimmune disease that has required systemic treatment in past 2 years Chronic usage of steroids or other immunosuppressant medication. Previous history of pneumonitis. Any evidence of clinical autoimmunity.", "candidate_expression": "((Any evidence of clinical autoimmunity) AND (Any medical condition which in the opinion of the investigator would compromise the ability of the patient to participate in the trial or which would jeopardise compliance with the protocol.) AND (Medical conditions) AND (Medical or psychiatric conditions comprising informed consent) AND (Radiotherapy within 4 weeks of trial entry) AND (autoimmune disease Active) AND (autoimmunity) AND (immunosuppressant medication Chronic usage) AND (pneumonitis history) AND (psychiatric conditions) AND (steroids Chronic usage) AND (symptomatic brain metastatic disease) AND (symptomatic leptomeningeal metastatic disease Untreated Untreated) AND (systemic treatment in past 2 years))"}
{"candidate_id": "LLM00810", "doc_id": "NCT02564471_exc", "case_bucket": "or", "source_criterion": "Subject is pregnant, or lactating, or of childbearing potential (to be considered of non-childbearing potential, a female must be post-menopausal for at least 1 year, surgically sterile, or using an effective method of contraception or abstinence from at least 4 weeks prior to the first vaccination and until at least 4 weeks after the last vaccination. Participation in the 4 weeks preceding the first trial vaccination, or planned participation during the present trial period, in another clinical trial investigating a vaccine, drug, medical device, or medical procedure. Previous history of receiving the rabies vaccine. Previous history of receiving rabies immune globulin. Any major psychiatric disorder, such as severe depression, severe anxiety disorder, psychosis, schizophrenia, other major psychiatric disorders, or seizures. History of mild depression or anxiety disorder that are well controlled are not exclusion criteria. Use of any immunosuppressive drug at the time of the study or 30 days previously. Topical steroids will not be considered an immunosuppressive drug and their use will not be considered an exclusion criteria. Any immunosuppressive disorder, such as HIV infection, common variable immunodeficiency, active cancers or chemotherapy. History of renal insufficiency or requiring dialysis. Have any condition that would, in the opinion of the site investigator, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol. Identified as an employee of the Investigator or study center, with direct involvement in the proposed study or other studies under the direction of that Investigator or study center, as well as family members (i.e., immediate, husband, wife and their children, adopted or natural) of the employee or the Investigator. Previous adverse reaction to any of the antimalarial drugs used in this study.", "candidate_expression": "((HIV infection) AND (Have any condition that would, in the opinion of the site investigator, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol.) AND (Identified as an employee of the Investigator or study center, with direct involvement in the proposed study or other studies under the direction of that Investigator or study center, as well as family members (i.e., immediate, husband, wife and their children, adopted or natural) of the employee or the Investigator.) AND (Subject is pregnant, or lactating, or of childbearing potential (to be considered of non-childbearing potential, a female must be post-menopausal for at least 1 year, surgically sterile, or using an effective method of contraception or abstinence from at least 4 weeks prior to the first vaccination and until at least 4 weeks after the last vaccination.) AND (adverse reaction Previous) AND (antimalarial drugs used in this study) AND (anxiety disorder) AND (anxiety disorder severe) AND (cancers) AND (chemotherapy) AND (common variable immunodeficiency) AND (depression) AND (depression severe) AND (dialysis requiring) AND (immunosuppressive disorder) AND (immunosuppressive drug at the time of the study 30 days previously) AND (major psychiatric disorder) AND (major psychiatric disorders other) AND (psychosis) AND (rabies immune globulin Previous history) AND (rabies vaccine Previous history) AND (renal insufficiency) AND (schizophrenia) AND (seizures) AND NOT (Topical steroids))"}
{"candidate_id": "LLM00811", "doc_id": "NCT01078051_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00812", "doc_id": "NCT03212352_inc", "case_bucket": "or", "source_criterion": "a crown-rump length = 6mm and no cardiac activity OR a crown-rump length <6mm and no fetal growth at least one week later OR At least one week after diagnosis OR a discrepancy of at least one week between crown-rump length and calendar gestational age Intra-uterine pregnancy Women aged above 16 years Hemodynamic stable patient No signs of infection No signs of incomplete abortion No contraindications for mifepristone or misoprostol", "candidate_expression": "((<6mm) AND (= 6mm) AND (Hemodynamic stable) AND (Intra-uterine pregnancy) AND (No) AND (Women) AND (above 16 years) AND (aged) AND (at least one week between crown-rump length and calendar gestational age) AND (calendar gestational age) AND (cardiac activity) AND (contraindications for) AND (crown-rump length) AND (diagnosis) AND (discrepancy) AND (fetal growth) AND (no) AND (signs of incomplete abortion) AND (signs of infection) AND ((At least one week after diagnosis) OR (at least one week later)) AND ((mifepristone) OR (misoprostol)))"}
{"candidate_id": "LLM00813", "doc_id": "NCT03506009_inc", "case_bucket": "other", "source_criterion": "18-80 years old; Diagnosis of posterior circulation ischemic stroke; Time from onset to treatment =6 hours; NIHSS: 4-25; Signed informed consent by patient self or legally authorized representatives.", "candidate_expression": "((NIHSS 4-25) AND (Signed informed consent by patient self or legally authorized representatives.) AND (Time from onset to treatment =6 hours) AND (old 18-80 years old) AND (posterior circulation ischemic stroke))"}
{"candidate_id": "LLM00814", "doc_id": "NCT02504203_inc", "case_bucket": "other", "source_criterion": "Children born outside the cluster, and returning more than 72 hours after the delivery Children that the nurse evaluates to die within the next 24 hours.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00815", "doc_id": "NCT03260881_exc", "case_bucket": "or", "source_criterion": "Patients with a personal or family history of medullary thyroid carcinoma or patients with Multiple Endocrine Neoplasia syndrome type 2 Patients with a prior serious hypersensitivity reaction to liraglutide Other contra-indications to liraglutide in accordance with risks and safety information included in the latest updated prescribing information Type 1 diabetes, as defined by ADA criteria Current use of other GLP-1A, dipeptidyl peptidase 4 (DPP4) or Sodium Glucose transporters 2 (SGLT2) inhibitors, thiazolidinediones (TZDs), pramlintide and fixed prandial insulin. Patients with unstable CAD, assessed by the Cardiology team and defined as new onset angina, rest angina, rapidly increasing or crescendo angina History of diabetic ketoacidosis, pancreas or beta-cell transplantation, or diabetes secondary to pancreatitis or pancreatectomy; acute or chronic infective diseases, cancer or chemotherapy, history of pulmonary, renal or liver diseases, and drug abuse Patients with chronic and acute inflammatory conditions such as sepsis, rheumatoid arthritis, ectopic dermatitis, asthma, ulcerative colitis. Current use of systemic corticosteroids in the 3 months prior this study. Pregnant or breast-feeding women Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)", "candidate_expression": "((Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)) AND (GLP-1A other) AND (Multiple Endocrine Neoplasia syndrome type 2) AND (Pregnant) AND (Sodium Glucose transporters 2 (SGLT2) inhibitors) AND (Type 1 diabetes ADA criteria) AND (asthma) AND (beta-cell transplantation) AND (breast-feeding women) AND (cancer) AND (chemotherapy) AND (contra-indications Other) AND (crescendo angina) AND (diabetes secondary to) AND (diabetic ketoacidosis) AND (dipeptidyl peptidase 4 (DPP4) inhibitors) AND (drug abuse chronic acute) AND (ectopic dermatitis) AND (family history) AND (hypersensitivity reaction prior serious) AND (infective diseases) AND (inflammatory conditions) AND (liraglutide) AND (liver diseases) AND (medullary thyroid carcinoma) AND (new onset angina) AND (pancreas transplantation) AND (pancreatectomy acute chronic) AND (pancreatitis) AND (personal history) AND (pramlintide) AND (prandial insulin) AND (pulmonary diseases) AND (rapidly increasing angina) AND (renal diseases) AND (rest angina) AND (rheumatoid arthritis) AND (sepsis) AND (systemic corticosteroids Current in the 3 months prior this study) AND (thiazolidinediones (TZDs)) AND (ulcerative colitis) AND (unstable CAD))"}
{"candidate_id": "LLM00816", "doc_id": "NCT03208465_exc", "case_bucket": "or", "source_criterion": "Contraindications to empagliflozin, Sitagliptin DPP4 inhibitors or Sodium-glucose cotransporter-2(SGLT2) inhibitors within the previous 4 weeks Insulin requiring diabetes Poor glucose control (HbA1C>10 %) Acute coronary syndrome Stent placement within the previous 6 months Previous coronary artery bypass graft surgery within the previous 6 months Planned revascularization within 6 months Heart failure requiring loop diuretics Severe left ventricular hypertrophy (left ventricular septal wall thickness > 13mm) Significant renal disease manifested by creatinine clearance of < 30 ml/min) Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (alanine transaminase or Aspartate Aminotransferase > 3 times upper limit of normal) Radiopaque material implanted in the chest wall (metal, silicone, etc.) Contraindication to adenosine stress test Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. Patient's pregnant or breast-feeding or child-bearing potential Expected life expectancy < 1 year Unwillingness or inability to comply with the procedures described in this protocol", "candidate_expression": "((Acute coronary syndrome) AND (Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study.) AND (Contraindication) AND (Contraindications) AND (Expected life expectancy < 1 year) AND (HbA1C >10 %) AND (Heart failure) AND (Insulin) AND (Poor glucose control) AND (Radiopaque material chest wall) AND (Stent) AND (adenosine stress test) AND (coronary artery bypass graft surgery Previous within the previous 6 months) AND (creatinine clearance < 30 ml/min) AND (diabetes) AND (left ventricular hypertrophy Severe) AND (loop diuretics) AND (placement within the previous 6 months) AND (renal disease Significant) AND (revascularization Planned within 6 months) AND ((Sitagliptin) OR (empagliflozin)) AND ((> 13mm) OR (left ventricular septal wall thickness)) AND ((Hepatic disease) OR (biliary tract obstruction) OR (hepatic enzyme elevation significant)) AND ((Aspartate Aminotransferase) OR (alanine transaminase)) AND ((DPP4 inhibitors) OR (Sodium-glucose cotransporter-2(SGLT2) inhibitors)) AND ((breast-feeding) OR (child-bearing potential) OR (pregnant)))"}
{"candidate_id": "LLM00817", "doc_id": "NCT02277067_exc", "case_bucket": "other", "source_criterion": "Women undergoing cesarean section with general anesthesia will be excluded, because carbetocin is licensed for use with regional anaesthesia only. women undergoing cesarean section at less than 37 weeks of gestation.", "candidate_expression": "((Women) AND (cesarean section) AND (cesarean section general anesthesia) AND (gestation less than 37 weeks) AND (women))"}
{"candidate_id": "LLM00818", "doc_id": "NCT01346436_exc", "case_bucket": "other", "source_criterion": "Age <18 years old Patient unable to communicate or to understand the study Patient refusing to participate to the study contraindication to laparoscopy", "candidate_expression": "((Age <18 years old) AND (Patient refusing to participate to the study) AND (Patient unable to communicate or to understand the study) AND (contraindication) AND (laparoscopy))"}
{"candidate_id": "LLM00819", "doc_id": "NCT02426944_inc", "case_bucket": "or", "source_criterion": "history of significant bleeding (i.e. bleeding which required intervention or hospitalization), even in the absence of anticoagulation treatment at the time of the bleeding event, or a cardioembolic event, which occurred on anticoagulation, or a high risk profile of the patient, defined as a CHA2DS2-VASc score = 3 and a HAS-BLED score = 2", "candidate_expression": "((CHA2DS2-VASc score = 3) AND (HAS-BLED score = 2) AND (anticoagulation) AND (bleeding) AND (bleeding significant) AND (cardioembolic event occurred on anticoagulation) AND (high risk profile) AND ((hospitalization) OR (intervention)))"}
{"candidate_id": "LLM00820", "doc_id": "NCT03194074_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for laser laryngeal surgery under general anesthesia with either Propofol or desflurane based technique.", "candidate_expression": "((Propofol) AND (desflurane) AND (general anesthesia) AND (laser laryngeal surgery) AND (scheduled))"}
{"candidate_id": "LLM00821", "doc_id": "NCT02196285_exc", "case_bucket": "or", "source_criterion": "Serious adverse reaction to any vaccination, as respiratory difficulty, angioedema and anaphylaxis; Acute or chronic disease, as diabetes, heart disease, systemic arterial hypertension; Use of anti-allergic with antigen injections in a maximum timeline of 14 days before the vaccination; Use of immunoglobulin in the past 12 months before the study vaccination; Use of blood products within 12 months before the vaccination; Use of any vaccine type within 30 days before the vaccination of the study; Chronic use of any medication, except homeopathy, and trivial ones, as nasal physiologic solution and vitamins; Previous immunosuppressive or cytotoxic medication, in the last 6 months. Individuals who have made use of this kind of medication in non-immunosuppressant doses, as nasal corticosteroid for allergic rhinitis of topic corticosteroid for non-complicated dermatitis, for more than 14 days, are allowed to be included in the study. Use of any kind of medication under investigation within one year before the vaccination. Unstable asthma or which may have required urgent care, hospitalization or intubation within the last 2 years, or which requires use of oral or intravenous corticosteroid. Coagulopathies diagnosed by a physician or report of capillary fragility (ex: bruises or bleedings without justifiable cause; Convulsions, except the ones caused by fever, before 2 years old; Psychiatric disease which difficults the adherence to the protocol, such as psychosis, obsessive-compulsive disorders, bipolar disease under treatment, diseases which require treatment with lithium and suicidal ideas in the last 5 years from the inclusion; Active malignant (p.e. any kind of cancer) or treated disease, to which the individual may relapse during the study; Asplenia (absence of spleen or its removal); Positive HIV in the screening examination of history of any immunosuppressant disease; Positive serology for C hepatitis in the screening evaluation; Positive Antigen HBs in the screening evaluation; Alcoholism (CAGE criteria), used for detection of abusive drinkers or alcoholic, validated in the Brazilian population with sensibility of 88% and specificity of 83%, if two or more answers, among four possible, are afirmative(Mansur and Monteiro, 1983), or according to medical decision; Abuse of illicit drugs, according to medical decision; Acquired or congenital immunodeficiency; Allergy to the vaccine compounds, as egg, neomycin and gelatin.", "candidate_expression": "((Abuse of illicit drugs) AND (Alcoholism) AND (Allergy to the vaccine compounds) AND (Antigen HBs Positive in the screening evaluation screening evaluation) AND (Asplenia the study screening examination) AND (CAGE criteria Alcoholism) AND (Coagulopathies) AND (Convulsions caused by fever before 2 years old) AND (Psychiatric disease difficults the adherence to the protocol) AND (Unstable asthma) AND (according to medical decision) AND (adverse reaction) AND (anaphylaxis) AND (angioedema) AND (anti-allergic maximum timeline of 14 days before the vaccination) AND (antigen injections) AND (any medication Chronic use) AND (any vaccine type within 30 days before the vaccination of the study) AND (bipolar disease under treatment) AND (blood products within 12 months before the vaccination) AND (cancer any kind malignant treated) AND (capillary fragility) AND (difficults the adherence to the protocol) AND (diseases which require treatment with lithium) AND (fever 2 years old) AND (homeopathy) AND (hospitalization) AND (immunoglobulin in the past 12 months before the study vaccination) AND (intravenous corticosteroid) AND (intubation) AND (lithium) AND (medication under investigation within one year before the vaccination) AND (obsessive-compulsive disorders) AND (oral corticosteroid) AND (psychosis) AND (respiratory difficulty) AND (serology for C hepatitis Positive in the screening evaluation screening evaluation) AND (suicidal ideas in the last 5 years from the inclusion the inclusion) AND (to which the individual may relapse during the study) AND (treated) AND (treatment) AND (treatment with lithium) AND (trivial ones) AND (urgent care) AND (vaccination) AND (vaccine compounds) AND ((diabetes) OR (heart disease) OR (systemic arterial hypertension)) AND ((spleen removal) OR NOT (spleen)) AND ((HIV Positive in the screening examination) OR (immunosuppressant disease)) AND ((Acute disease) OR (chronic disease)) AND ((Acquired immunodeficiency) OR (congenital immunodeficiency)) AND ((egg) OR (gelatin) OR (neomycin)) AND ((nasal physiologic solution) OR (vitamins)) AND ((cytotoxic medication) OR (immunosuppressive medication)) AND ((required hospitalization) OR (required intubation) OR (required urgent care)) AND ((requires use of intravenous corticosteroid) OR (requires use of oral corticosteroid)) AND ((bleedings without justifiable cause) OR (bruises without justifiable cause)) AND ((malignant disease Active) OR (treated disease)))"}
{"candidate_id": "LLM00822", "doc_id": "NCT03034733_exc", "case_bucket": "or", "source_criterion": "severe coronary artery disease, heart failure, kidney failure insulin-dependent DM (diabetes mellitus), poorly controlled type II DM gastric/duodenal ulcer allergy/contra-indication for any drug used in the study corticosteroid use during last 3 months preoperative use of opioid drugs (excl. codeine, tramadol) neuropathy/sensory impairment of lower limbs lack of co-operation, e.g. inability to use a PCA (patient controlled analgesia)-device", "candidate_expression": "((PCA -device) AND (corticosteroid) AND (diabetes mellitus) AND (drug used in the study) AND (during last 3 months) AND (excl.) AND (inability to use) AND (insulin-dependent DM) AND (lack of co-operation) AND (lower limbs) AND (opioid drugs) AND (poorly controlled) AND (preoperative) AND (severe) AND (type II DM) AND ((duodenal ulcer) OR (gastric ulcer)) AND ((allergy) OR (contra-indication)) AND ((coronary artery disease) OR (heart failure) OR (kidney failure)) AND ((codeine) OR (tramadol)) AND ((neuropathy) OR (sensory impairment)))"}
{"candidate_id": "LLM00823", "doc_id": "NCT03305575_inc", "case_bucket": "other", "source_criterion": "ASA classification II or III females Age: 18-45 years old BMI = 50 kg/m2 Singleton pregnancy Simple prophylactic cervical cerclage Planning neuraxial anesthesia", "candidate_expression": "((18-45 years old) AND (= 50 kg/m2) AND (ASA classification) AND (Age) AND (BMI) AND (II or III) AND (Planning) AND (Simple) AND (Singleton pregnancy) AND (cervical cerclage) AND (females) AND (neuraxial anesthesia) AND (prophylactic))"}
{"candidate_id": "LLM00824", "doc_id": "NCT03182114_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women scheduled for elective cesarean delivery", "candidate_expression": "((cesarean delivery scheduled for elective) AND (full term singleton) AND (pregnant) AND (women))"}
{"candidate_id": "LLM00825", "doc_id": "NCT02464865_exc", "case_bucket": "or", "source_criterion": "pathological obesity chronic diseases e.g. cerebral palsy, metabolic disease, etc. diseases of red blood cells on medication e.g. steroid, multivitamins, thiamine-containing vitamins, diuretic drugs hemodialysis or peritoneal dialysis bariatric surgery", "candidate_expression": "((bariatric surgery) AND (cerebral palsy) AND (chronic diseases) AND (diseases of red blood cells) AND (diuretic drugs) AND (hemodialysis) AND (metabolic disease) AND (multivitamins) AND (pathological obesity) AND (peritoneal dialysis) AND (steroid) AND (thiamine-containing vitamins))"}
```
