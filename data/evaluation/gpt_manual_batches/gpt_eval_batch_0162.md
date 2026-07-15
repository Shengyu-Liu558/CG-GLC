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
{"candidate_id": "LLM04026", "doc_id": "NCT01497639_inc", "case_bucket": "or", "source_criterion": "ages of 7 and 75 years marked disability owing to primary generalized or segmental dystonia, despite optimal pharmacologic treatment disease duration of at least 5 years.", "candidate_expression": "((7 and 75 years) AND (ages) AND (at least 5 years) AND (disability) AND (disease duration) AND (dystonia) AND (optimal) AND (pharmacologic treatment) AND (primary) AND ((generalized) OR (segmental)))"}
{"candidate_id": "LLM04027", "doc_id": "NCT01424020_inc", "case_bucket": "other", "source_criterion": "French Native language 18 years old or older Signed consent Covered by the French social care system", "candidate_expression": "((18 years or older) AND (Covered by the French social care system) AND (French Native language) AND (Signed consent) AND (old))"}
{"candidate_id": "LLM04028", "doc_id": "NCT03209011_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Psychiatric disease) AND (autoimmune hepatitis History) AND (neoplastic diseases Evidence of liver) AND ((consumption of alcohol) OR (drugs consumption of)) AND ((hepatitis C virus) OR (hepatitis D virus) OR (human immunodeficiency virus)))"}
{"candidate_id": "LLM04029", "doc_id": "NCT03228654_exc", "case_bucket": "or", "source_criterion": "Suspected or known gynecological malignancy. uterine size >12 weeks. Endometriosis Presence of adnexal mass. cervix flushed with the vagina. presence of significant scarring in the pelvic area from previous surgery.", "candidate_expression": "((Endometriosis) AND (adnexal mass) AND (cervix flushed with the vagina) AND (gynecological malignancy Suspected known) AND (significant scarring pelvic area from previous surgery) AND (surgery previous) AND (uterine size >12 weeks))"}
{"candidate_id": "LLM04030", "doc_id": "NCT01890759_exc", "case_bucket": "or", "source_criterion": "Participation in the 4 weeks preceding inclusion or planned participation during the present trial period in another clinical trial investigating a vaccine, drug, medical device, or medical procedure. Receipt of any vaccine in the 4 weeks preceding each trial vaccination or planned receipt of any vaccine in the 4 weeks following each trial vaccination, except for: (i) influenza vaccination, which may be received at least 2 weeks before study vaccines. (ii) measles (M) or measles, mumps, rubella (MMR) routine vaccination, which can be administered concomitantly with the first dose of study vaccine as per routine immunization schedule (iii) for subjects enrolled at Indian sites: oral poliomyelitis vaccine (OPV) received during National Immunization Days (NIDs) and supplementary immunization activity days (SIADs) Previous vaccination against meningococcal disease with either the study vaccine or another meningococcal vaccine Receipt of immune globulins, blood or blood-derived products in the past 3 months Known or suspected congenital or acquired immunodeficiency; or receipt of immunosuppressive therapy, such as anti-cancer chemotherapy or radiation therapy, within the preceding 6 months; or long-term systemic corticosteroid therapy (prednisone or equivalent for more than 2 consecutive weeks within the past 3 months) History of meningococcal diseases, confirmed either clinically, serologically, or microbiologically At high risk, in the opinion of the Investigator, for meningococcal disease during the trial Known or suspected systemic hypersensitivity to any of the vaccine components, or history of a life-threatening reaction to the vaccine used in the trial or to a vaccine containing any of the same substances Known thrombocytopenia, contraindicating intramuscular vaccination Bleeding disorder, or receipt of anticoagulants in the 3 weeks preceding inclusion, contraindicating intramuscular vaccination In an emergency setting, or hospitalized involuntarily Chronic illness that, in the opinion of the investigator, is at a stage where it might interfere with trial conduct or completion For subjects enrolled at Indian sites: Moderate or severe acute illness/infection (according to investigator judgment) on the day of vaccination or febrile illness (temperature ≥ 38.0°C). For subjects enrolled at Russian sites: Acute disease of any severity on the day of vaccination or febrile illness (axillary temperature ≥ 37.0°C). A prospective subject should not be included in the study until the condition has resolved or the febrile event has subsided. Receipt of oral or injectable antibiotic therapy within 72 hours prior to the first blood draw Identified as a natural or adopted child of the Investigator or employee with direct involvement in the proposed study Personal history of Guillain-Barré Syndrome.", "candidate_expression": "((4 weeks preceding inclusion) AND (Acute disease) AND (At high risk, in the opinion of the Investigator, for meningococcal disease during the trial) AND (Chronic illness that, in the opinion of the investigator, is at a stage where it might interfere with trial conduct or completion) AND (Guillain-Barré Syndrome) AND (Indian sites) AND (National Immunization Days (NIDs)) AND (Participation in the 4 weeks preceding inclusion or planned participation during the present trial period in another clinical trial investigating a vaccine, drug, medical device, or medical procedure.) AND (Russian sites) AND (according to investigator judgment) AND (another meningococcal vaccine) AND (antibiotic therapy) AND (at least 2 weeks before study vaccines) AND (axillary temperature) AND (concomitantly with the first dose of study vaccine) AND (confirmed) AND (contraindicating) AND (during National Immunization Days (NIDs)) AND (during supplementary immunization activity days (SIADs)) AND (each trial vaccination) AND (except for) AND (febrile illness) AND (for more than 2 consecutive weeks) AND (history) AND (hospitalized) AND (in the 3 weeks preceding inclusion) AND (in the 4 weeks following each trial vaccination) AND (in the 4 weeks preceding each trial vaccination) AND (in the past 3 months) AND (inclusion) AND (influenza vaccination) AND (intramuscular vaccination) AND (involuntarily) AND (life-threatening reaction) AND (long-term) AND (meningococcal diseases) AND (microbiologically) AND (on the day of vaccination) AND (oral poliomyelitis vaccine (OPV)) AND (planned participation) AND (planned receipt) AND (prednisone) AND (serologically) AND (study vaccine) AND (study vaccines) AND (supplementary immunization activity days (SIADs)) AND (systemic hypersensitivity) AND (temperature) AND (the day of vaccination) AND (the first blood draw) AND (the first dose of study vaccine) AND (thrombocytopenia) AND (used in the trial) AND (vaccination against meningococcal disease) AND (vaccine) AND (vaccine components) AND (within 72 hours prior to the first blood draw) AND (within the past 3 months) AND (within the preceding 6 months) AND (≥ 37.0°C) AND (≥ 38.0°C) AND ((injectable) OR (oral)) AND ((measles (M) vaccination) OR (measles, mumps, rubella (MMR) vaccination)) AND ((blood) OR (blood-derived products) OR (immune globulins)) AND ((acquired immunodeficiency) OR (congenital immunodeficiency)) AND ((immunosuppressive therapy) OR (systemic corticosteroid therapy)) AND ((anti-cancer chemotherapy) OR (radiation therapy)) AND ((Known) OR (suspected)) AND ((Bleeding disorder) OR (anticoagulants)) AND ((emergency setting) OR (hospitalized involuntarily)) AND ((Moderate) OR (severe)) AND ((acute illness) OR (acute infection)))"}
{"candidate_id": "LLM04031", "doc_id": "NCT02745704_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (antineoplastic therapy) AND (complications serious) AND (immunomodulatory therapy) AND (organ dysfunctions) AND ((autoimmune diseases) OR (diabetes)) AND ((gastrointestinal bleeding) OR (hepatic encephalopathy) OR (hepatorenal syndrome) OR (infection)) AND ((Hepatocellular Carcinoma) OR (liver cirrhosis) OR (malignancies)) AND ((HIV infection concomitant) OR (congenital immune deficiency diseases.)))"}
{"candidate_id": "LLM04032", "doc_id": "NCT02944292_exc", "case_bucket": "other", "source_criterion": "Contraindication for propofol administration Contraindication for IAP measurement in supine position with head-of-bed at 0° Other intervention for reduction of IAP planned Previous propofol infusion rate >4 mg/kg/h", "candidate_expression": "((>4 mg/kg/h) AND (Contraindication) AND (IAP measurement) AND (Other) AND (Previous) AND (head-of-bed at 0°) AND (intervention for reduction of IAP) AND (planned) AND (propofol) AND (propofol infusion rate) AND (supine position))"}
{"candidate_id": "LLM04033", "doc_id": "NCT01346436_inc", "case_bucket": "other", "source_criterion": "women proven pelvic floor dysfunction informed consent", "candidate_expression": "((nformed consent) AND (pelvic floor dysfunction) AND (women))"}
{"candidate_id": "LLM04034", "doc_id": "NCT02964416_exc", "case_bucket": "or", "source_criterion": "Patients with a history of allergy or hypersensitivity to tramadol. History of epilepsy or convulsions due to any reason. Chronic usage of analgesic drugs. Patients using monoamine oxidase inhibitors. Patients with clinical signs of raised ICP. Obesity (women with a body mass index >35 kg/m2 or men with a body mass index >42 kg/m2) Language barrier. Patients taking B-blockers or Ca channel blockers. Patients above 65 years of age ( Physiology difference)", "candidate_expression": "((ICP raised) AND (Language barrier) AND (Obesity) AND (age above 65 years) AND (analgesic drugs) AND (men) AND (monoamine oxidase inhibitors) AND (tramadol) AND (women) AND ((allergy) OR (hypersensitivity)) AND ((body mass index >35 kg/m2) OR (body mass index >42 kg/m2)) AND ((B-blockers) OR (Ca channel blockers)) AND ((convulsions) OR (epilepsy)))"}
{"candidate_id": "LLM04035", "doc_id": "NCT01891513_exc", "case_bucket": "or", "source_criterion": "Failure to provide informed consent Inability to complete 400 m walk within 15 minutes without sitting or interpersonal assistance, as an indicator of disablement and likely inability to fully engage in the exercise intervention Primary indication for ACE inhibitor use, i.e. Congestive Heart Failure, CAD, diabetes Known hypersensitivity to ACE inhibitors Resistant hypertension, defined as BP > 140/90, despite the use of three or more anti-hypertensive drugs Office or average home SBP > 180 mm Hg or DBP > 110 mm Hg (Average home BP in any seven day period during trial) Primary renal disease Serum creatinine >2.5 mg/dL in men, or >2.0 mg/dL in women Serum potassium >5.0 molar equivalent/L Urinary protein > 1 on dipstick Abnormal liver enzymes (Aspartate transaminase (AST), Alanine transaminase (ALT), or alkaline phosphatase > 2.5 times the upper limit of normal) Severe cardiac disease, including New York Heart Association Class III or IV congestive heart failure, clinically significant aortic stenosis, history of cardiac arrest, use of a cardiac defibrillator, or uncontrolled angina Acute myocardial infarction identified by ECG Lives in a nursing home (persons living in assisted or independent housing will not be excluded) Significant cognitive impairment, defined as a known diagnosis of dementia or a Mini-Mental State Examination exam score < 24 Unable to communicate because of severe hearing loss or speech disorder Severe visual impairment, which would preclude completion of the assessments and/or intervention Other significant co-morbid disease that would prevent participation in exercise Planning to move out of the area during the study time frame Simultaneous participation in another intervention trial", "candidate_expression": "((ACE inhibitor) AND (ACE inhibitors) AND (Acute myocardial infarction) AND (Alanine transaminase (ALT)) AND (Aspartate transaminase (AST)) AND (BP > 140/90) AND (CAD) AND (Congestive Heart Failure) AND (DBP > 110 mm Hg) AND (ECG) AND (Inability to complete 400 m walk within 15 minutes without sitting) AND (Lives in a nursing home) AND (Mini-Mental State Examination score < 24) AND (New York Heart Association Class III or IV) AND (Primary indication for ACE inhibitor use) AND (Primary renal disease) AND (SBP > 180 mm Hg) AND (Serum creatinine) AND (Serum potassium >5.0 molar equivalent/L) AND (Unable to communicate) AND (Urinary protein on dipstick > 1) AND (alkaline phosphatase) AND (anti-hypertensive drugs three or more) AND (aortic stenosis clinically significant) AND (cardiac arrest history) AND (cardiac defibrillator) AND (cardiac disease Severe) AND (co-morbid disease significant that would prevent participation in exercise) AND (cognitive impairment Significant) AND (congestive heart failure New York Heart Association Class III or IV) AND (dementia) AND (diabetes) AND (hypersensitivity to ACE inhibitors) AND (hypertension Resistant) AND (interpersonal assistance Inability to complete 400 m walk within 15 minutes without) AND (liver enzymes Abnormal) AND (men >2.5 mg/dL) AND (severe hearing loss) AND (speech disorder) AND (that would prevent participation in exercise) AND (uncontrolled angina) AND (visual impairment Severe) AND (women >2.0 mg/dL))"}
{"candidate_id": "LLM04036", "doc_id": "NCT02430740_inc", "case_bucket": "other", "source_criterion": "female infertile patients eligible for IVF treatment", "candidate_expression": "((IVF treatment eligible) AND (female) AND (infertile))"}
{"candidate_id": "LLM04037", "doc_id": "NCT02571179_inc", "case_bucket": "other", "source_criterion": "healthy parturients with uncomplicated, single gestation pregnancies, full term (38-42 weeks of gestation) pregnancy, agreed to participate", "candidate_expression": "((38-42) AND (agreed to participate) AND (full term) AND (healthy) AND (parturients) AND (pregnancies) AND (pregnancy) AND (single gestation) AND (uncomplicated) AND (weeks of gestation))"}
{"candidate_id": "LLM04038", "doc_id": "NCT00812344_exc", "case_bucket": "or", "source_criterion": "Significant illness, trauma or surgical procedures. Clinically significant laboratory abnormalities. Clinically significant medical history", "candidate_expression": "((Clinically significant) AND (Significant) AND (laboratory) AND (laboratory abnormalities) AND (medical history) AND ((illness) OR (surgical procedures) OR (trauma)))"}
{"candidate_id": "LLM04039", "doc_id": "NCT01000155_exc", "case_bucket": "or", "source_criterion": "Subjects with hemoglobin SC or SB+ thalassemia Subjects on chronic transfusion program Subjects who have received RBC transfusions cannot have >15% adult hemoglobin Known positive status for HIV, active hepatitis B or hepatitis C Pregnant or breast feeding women Individuals with a history of malignancy are ineligible except for the following circumstances. Individuals with a history of malignancy are eligible if they have been disease-free for at least 5 years and are deemed by the investigator to be at low risk for recurrence of that malignancy. Individuals with the following cancer are eligible if diagnosed and adequately treated within the past 5 years: cervical or breast cancer in situ, and basal cell or squamous cell carcinoma of the skin Subjects with a history of thrombosis or other reason (other than sickle cell disease) for enhanced thrombotic risk Subjects with unresolved infections Severe or uncontrolled medical conditions that could compromise study participation Subjects on fetal hemoglobin inducing agents Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy Known allergic reaction to a histone deacetylase inhibitor Subjects who have received valproic acid for treatment of epilepsy within 30 days of enrollment Subjects who have received any HDAC inhibitors other than valproic acid", "candidate_expression": "((HDAC inhibitors) AND (Severe or uncontrolled medical conditions that could compromise study participation) AND (Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy) AND (allergic reaction) AND (are eligible) AND (deemed by the investigator) AND (disease-free for at least 5 years) AND (epilepsy within 30 days of enrollment) AND (fetal hemoglobin inducing agents fetal) AND (histone deacetylase inhibitor) AND (infections unresolved) AND (malignancy history) AND (medical conditions compromise study participation) AND (recurrence of that malignancy low risk) AND (that malignancy) AND (thrombotic) AND (transfusion program chronic chronic) AND (treated adequately within the past 5 years diagnosed adequately treated) AND (treatment) AND (valproic acid) AND (women) AND NOT (sickle cell disease) AND NOT (RBC transfusions >15% adult hemoglobin) AND NOT (valproic acid) AND ((Pregnant) OR (breast feeding)) AND ((SB+ thalassemia) OR (hemoglobin SC)) AND ((basal cell carcinoma of the skin) OR (breast cancer in situ) OR (cervical cancer in situ) OR (squamous cell carcinoma of the skin)) AND ((thrombosis history) OR (thrombotic risk enhanced risk)) AND ((HIV) OR (hepatitis B active) OR (hepatitis C active)))"}
{"candidate_id": "LLM04040", "doc_id": "NCT02816164_exc", "case_bucket": "other", "source_criterion": "Contraindication to Filgrastim", "candidate_expression": "((Contraindication) AND (Filgrastim))"}
{"candidate_id": "LLM04041", "doc_id": "NCT02780427_inc", "case_bucket": "other", "source_criterion": "Children, aged between one and 24 months. classified as (American Society of Anesthesiologists) ASA physical status I or II, undergoing TEE were enrolled in the study.", "candidate_expression": "((ASA physical status) AND (American Society of Anesthesiologists) AND (Children) AND (I or II) AND (TEE) AND (aged) AND (between one and 24 months))"}
{"candidate_id": "LLM04042", "doc_id": "NCT03223909_inc", "case_bucket": "or", "source_criterion": ">18 to < 90 years old Both sexes Mild to moderate tear film dysfunction clinical diagnose TBUT > 5 sec. and < 10 sec. Schirmer: > 4 mm and < 14 mm OSDI < 30 points Corneal staining < grade III on the Oxford scale Availability to go to each revision when indicated.", "candidate_expression": "((Availability to go to each revision when indicated.) AND (Both sexes Mild moderate) AND (Corneal staining < grade III) AND (OSDI < 30 points) AND (Schirmer > 4 mm and < 14 mm) AND (TBUT > 5 sec. and < 10 sec) AND (old >18 to < 90 years) AND (tear film dysfunction))"}
{"candidate_id": "LLM04043", "doc_id": "NCT02954029_inc", "case_bucket": "or", "source_criterion": "age 18 years or older patients undergoing invasive procedures via the radial or femoral arteries", "candidate_expression": "((18 years or older) AND (age) AND (femoral arteries) AND (invasive procedures) AND (radial arteries) AND (undergoing))"}
{"candidate_id": "LLM04044", "doc_id": "NCT00904202_exc", "case_bucket": "or", "source_criterion": "1. Had a neurological condition other than that associated with their pain diagnosis which, in the opinion of the investigator, would interfere with their ability to participate in the study 2. Were taking a lidocaine-containing product that could not be discontinued while receiving lidocaine 3. Were taking class 1 anti-arrhythmic drugs (e.g., mexiletine, tocainide)", "candidate_expression": "((class 1 anti-arrhythmic drugs) AND (lidocaine while receiving lidocaine receiving lidocaine) AND (lidocaine-containing product could not be discontinued) AND (mexiletine) AND (neurological condition associated with their pain diagnosis) AND (other than associated with their pain diagnosis) AND (pain diagnosis) AND (tocainide))"}
{"candidate_id": "LLM04045", "doc_id": "NCT02992938_exc", "case_bucket": "or", "source_criterion": "Patients ASA III y IV Chronic pain history Drug and alcohol abuse Chronic use of opioid and sedatives Neuropsychiatric illness NSAID and other analgesics used the 48 hours previous to the surgery CMI > 30", "candidate_expression": "((48 hours previous to the surgery) AND (> 3) AND (ASA) AND (CMI) AND (Chronic pain) AND (Chronic use) AND (Drug abuse) AND (III y IV) AND (NSAID) AND (Neuropsychiatric illness) AND (alcohol abuse) AND (analgesics) AND (opioid) AND (other) AND (sedatives) AND (the surgery))"}
{"candidate_id": "LLM04046", "doc_id": "NCT03082573_inc", "case_bucket": "other", "source_criterion": "Fluent in reading and writing in English language. = 21 years of age at the time of participation.", "candidate_expression": "(age = 21 years at the time of participation)"}
{"candidate_id": "LLM04047", "doc_id": "NCT02802644_inc", "case_bucket": "other", "source_criterion": "Non-ST segement elevation acute coronary syndrome", "candidate_expression": "((Non-ST segement elevation) AND (acute coronary syndrome))"}
{"candidate_id": "LLM04048", "doc_id": "NCT03208127_inc", "case_bucket": "other", "source_criterion": "Recipient is Age = 18 years Met MGH transplant center criteria, listed for liver transplant HCV naive Able to sign informed consent", "candidate_expression": "((= 18 years) AND (Able to sign informed consent) AND (Age) AND (HCV) AND (HCV naive) AND (MGH transplant center criteria) AND (liver transplant) AND (naive))"}
{"candidate_id": "LLM04049", "doc_id": "NCT03070847_exc", "case_bucket": "or", "source_criterion": "pregnancy known allergies for tranexamic acid or any other substance in Exacyl deep vein thrombosis Hormone Replacement Therapy or oral contraceptive usage anticoagulants usage obesity - BMI (body mass index) >30 kg/m2 renal disease, as glomerular filtration rate (GFR) <60 ml/min/1,73 m*m seizures or epilepsy in the past", "candidate_expression": "((BMI >30 kg/m2) AND (GFR) AND (allergies) AND (anticoagulants) AND (body mass index) AND (deep vein thrombosis) AND (glomerular filtration rate <60 ml/min/1,73 m*m) AND (obesity) AND (pregnancy) AND (renal disease) AND ((epilepsy) OR (seizures)) AND ((Exacyl) OR (tranexamic acid)) AND ((Hormone Replacement Therapy) OR (oral contraceptive)))"}
{"candidate_id": "LLM04050", "doc_id": "NCT00917891_exc", "case_bucket": "or", "source_criterion": "1. Currently pregnant or last pregnancy outcome within 3 months prior to enrolment 2. Currently breast-feeding 3. Participated in any other research study within 60 days prior to screening 4. Previously participated in any HIV vaccine study 5. Untreated urogenital infections (either symptomatic or asymptomatic) within 2 weeks prior to enrollment 6. Presence of abnormal physical finding on the vulva, vaginal walls or cervix during pelvic/speculum examination and/or colposcopy 7. History of significant urogenital or uterine prolapse, undiagnosed vaginal bleeding, urethral obstruction 8. Pap smear result at screening that requires cryotherapy, biopsy, treatment (other than for infection), or further evaluation 9. Any Grade 2, 3 or 4 baseline haematology, chemistry or urinalysis laboratory abnormality according to the DAIDS Table for Grading Adverse Experiences 10. Unexplained, undiagnosed abnormal bleeding per vagina, bleeding per vagina during or following vaginal intercourse, or gynaecologic surgery within 90 days prior to enrollment 11. Any history of anaphylaxis or severe allergy resulting in angioedema; or a history of sensitivity/allergy to latex 12. Any serious acute, chronic or progressive disease 13. Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives", "candidate_expression": "((Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives) AND (Any serious acute, chronic or progressive disease) AND (DAIDS Table for Grading Adverse Experiences Grade 2, 3 or 4 baseline Unexplained undiagnosed) AND (Pap smear at screening) AND (abnormal physical finding on the cervix) AND (abnormal physical finding on the vaginal walls) AND (abnormal physical finding on the vulva) AND (allergy severe) AND (allergy to latex) AND (anaphylaxis) AND (angioedema) AND (asymptomatic) AND (biopsy) AND (bleeding per vagina abnormal) AND (bleeding per vagina during vaginal intercourse following vaginal intercourse) AND (breast-feeding Currently) AND (chemistry) AND (chemistry abnormality) AND (colposcopy) AND (cryotherapy requires cryotherapy requires biopsy requires treatment requires further evaluation) AND (disease progressive) AND (further evaluation) AND (gynaecologic surgery within 90 days prior to enrollment) AND (haematology) AND (haematology abnormality) AND (laboratory) AND (laboratory abnormality) AND (pelvic examination) AND (pregnancy outcome last within 3 months prior to enrolment enrolment) AND (pregnant Currently last) AND (sensitivity to latex serious acute chronic) AND (significant) AND (speculum examination) AND (symptomatic) AND (treatment) AND (urethral obstruction) AND (urinalysis) AND (urinalysis abnormality) AND (urogenital infections Untreated within 2 weeks prior to enrollment) AND (urogenital prolapse) AND (uterine prolapse) AND (vaginal bleeding undiagnosed))"}
```
