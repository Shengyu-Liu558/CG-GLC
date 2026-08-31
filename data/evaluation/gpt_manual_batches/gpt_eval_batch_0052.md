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
{"candidate_id": "LLM01276", "doc_id": "NCT02380118_exc", "case_bucket": "or", "source_criterion": "known hypersensitivity or contraindication to the study drugs reversible aetiology for agitation (e.g. hypotension, hypoxia, hypoglycaemia) known pregnancy acute alcohol withdrawal patients aged>75 years.", "candidate_expression": "((>75 years) AND (acute alcohol withdrawal) AND (aged) AND (agitation) AND (pregnancy) AND (reversible aetiology) AND (study drugs) AND ((contraindication) OR (hypersensitivity)) AND ((hypoglycaemia) OR (hypotension) OR (hypoxia)))"}
{"candidate_id": "LLM01277", "doc_id": "NCT03329456_exc", "case_bucket": "or", "source_criterion": "Exclusion criteria are pregnancy, patients with contraindications to regional anesthesia, allergy to LAs, patients taking opioids regularly due to chronic pain, use of anticoagulation drugs other than acetylsalicylic acid or dipyridamole, atrioventricular block, diabetes.", "candidate_expression": "((LAs) AND (acetylsalicylic acid) AND (allergy) AND (anticoagulation drugs) AND (atrioventricular block) AND (chronic pain) AND (contraindications) AND (diabetes) AND (dipyridamole) AND (opioids) AND (other than) AND (pregnancy) AND (regional anesthesia) AND (regularly))"}
{"candidate_id": "LLM01278", "doc_id": "NCT02686021_exc", "case_bucket": "or", "source_criterion": "simultaneous both sided extraction or only upper third molar extraction general anesthesia known or presumed abnormal coagulation status known or presumed liver or renal dysfunction contraindication against metamizole known or suspected (known or suspected allergy against novalgin or other pyrazolones, anaphylactic reaction against NSAIDS, decreased bone marrow function or hematopoesis, hepatic porphyria, glucose-6-phosphate dehydrogenase deficiency, and pregnancy/breastfeeding) contraindication against ibuprofen (known or suspected allergy against ibuprofen, anaphylactic reaction against Nonsteroidal anti-inflammatory drugs (NSAID), active or recurrent stomach or duodenal ulcera or bleeding, severe liver or renal insufficiency, inflammatory bowel syndrome, and pregnancy/breastfeeding) pregnancy and breast feeding mothers", "candidate_expression": "((NSAIDS) AND (Nonsteroidal anti-inflammatory drugs (NSAID)) AND (abnormal coagulation status) AND (active) AND (allergy) AND (anaphylactic reaction) AND (bleeding) AND (bone marrow function) AND (both sided) AND (breast feeding) AND (breastfeeding) AND (contraindication) AND (decreased) AND (duodenal) AND (general anesthesia) AND (glucose-6-phosphate dehydrogenase deficiency) AND (hematopoesis) AND (hepatic porphyria) AND (ibuprofen) AND (inflammatory bowel syndrome) AND (known) AND (liver dysfunction) AND (metamizole) AND (molar extraction) AND (novalgin) AND (only upper third) AND (other) AND (pregnancy) AND (presumed) AND (pyrazolones) AND (recurrent) AND (renal dysfunction) AND (severe liver insufficiency) AND (severe renal insufficiency) AND (simultaneous) AND (stomach) AND (suspected) AND (ulcera))"}
{"candidate_id": "LLM01279", "doc_id": "NCT03195153_exc", "case_bucket": "other", "source_criterion": "not diabetic patient; patients in dual antiplatelet therapy; patient with severe renal failure; patient poor responders", "candidate_expression": "((dual antiplatelet therapy) AND (poor responders) AND (renal failure severe) AND NOT (diabetic))"}
{"candidate_id": "LLM01280", "doc_id": "NCT02072811_exc", "case_bucket": "other", "source_criterion": "No informed consent for participation in the study, mental illness, which don't allow to obtain informed consent and conduct the treatment according to the protocol Pregnancy HIV infection Active cancer Active hepatitis virus infection", "candidate_expression": "((HIV infection) AND (Pregnancy) AND (cancer Active) AND (hepatitis virus infection Active))"}
{"candidate_id": "LLM01281", "doc_id": "NCT02637076_inc", "case_bucket": "or", "source_criterion": "current diagnosis of narcolepsy with cataplexy OR healthy control", "candidate_expression": "((cataplexy) AND (healthy) AND (narcolepsy))"}
{"candidate_id": "LLM01282", "doc_id": "NCT02145026_exc", "case_bucket": "or", "source_criterion": "Contraindications and/or known hypersensitivity to the active substance and/or any of the excipients of epoetin beta treatment Poorly controlled hypertension as assessed by the investigator History of Acute Myeloid Leukemia (AML) or high risk for AML Administration of another investigational drug within 1 month before screening or planned during the study period Previously documented evidence of Pure Red Cell Aplasia (PRCA)", "candidate_expression": "((AML) AND (Acute Myeloid Leukemia) AND (Administration of another investigational drug within 1 month before screening or planned during the study period) AND (Contraindications) AND (PRCA) AND (Poorly controlled) AND (Pure Red Cell Aplasia) AND (epoetin beta treatment) AND (high) AND (hypersensitivity) AND (hypertension) AND (risk for AML))"}
{"candidate_id": "LLM01283", "doc_id": "NCT02951520_exc", "case_bucket": "other", "source_criterion": "BMI > 30 kg.m-2, ASA physical state >II Allergy to the used local anesthetics Infection at the injection site age <18y", "candidate_expression": "((<18y) AND (> 30 kg.m-2) AND (>II) AND (ASA physical state) AND (Allergy) AND (BMI) AND (Infection) AND (age) AND (injection site) AND (local anesthetics))"}
{"candidate_id": "LLM01284", "doc_id": "NCT02782702_inc", "case_bucket": "or", "source_criterion": "Confirmed diagnosis (clinical and histological features) of Hailey Hailey or Darier diseases. Moderate to very severe lesions located in large folds Patient aged 18 ans or more Patient with health coverage Patient who have signed the consent form Patient proficient into filling out the questionnaires.", "candidate_expression": "((Darier disease) AND (Hailey Hailey disease) AND (Patient proficient into filling out the questionnaires.) AND (Patient who have signed the consent form) AND (aged 18 ans or more) AND (health coverage) AND (histological) AND (lesions very severe) AND (very severe))"}
{"candidate_id": "LLM01285", "doc_id": "NCT02810704_exc", "case_bucket": "or", "source_criterion": "Patients undergoing bilateral hip or knee replacement; Patients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement; Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban; Patients who have a contraindication to two or more of the three study prophylaxis regimens; Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery; Patients on chronic (longer than the prior 6 months) anticoagulation other than with antiplatelet medications; Patients with documented gastrointestinal, cerebral, or other hemorrhage within 3 months of the operation; Patients with a known diagnosis of defective hemostasis and past history of clinical bleeding requiring transfusion and treatment; Patients who have had an operative procedure involving the eye, ear, or central nervous system within one month; Patients with severe uncontrolled hypertension with systolic BP > 220mmHg or diastolic BP > 120mmHg; Patients with an absolute body weight of less than 41 kilograms (90.4 lbs) at baseline visit; Vulnerable patient populations including prisoners and institutionalized individuals.", "candidate_expression": "((Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban) AND (Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery) AND (anticoagulation longer than the prior 6 months) AND (atients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement;) AND (bleeding) AND (body weight less than 41 kilograms 90.4 lbs) AND (cerebral hemorrhage) AND (contraindication) AND (diastolic BP > 120mmHg) AND (gastrointestinal hemorrhage) AND (hemorrhage) AND (hemostasis defective) AND (hip replacement) AND (hypertension severe uncontrolled) AND (institutionalized) AND (knee replacement) AND (operative procedure within one month eye ear central nervous system) AND (prisoners) AND (systolic BP > 220mmHg) AND (total hip replacement) AND (total knee replacement) AND (transfusion) AND (treatment) AND NOT (antiplatelet))"}
{"candidate_id": "LLM01286", "doc_id": "NCT02469610_inc", "case_bucket": "other", "source_criterion": "Thoracoscopic surgery candidate. Over 18 years old. No known allergy to Bupivacaine. Patient is able to read understand and singe an inform consent.", "candidate_expression": "((Bupivacaine) AND (No) AND (Over 18 years old) AND (Thoracoscopic surgery) AND (able to read) AND (allergy) AND (candidate) AND (old) AND (singe) AND (understand))"}
{"candidate_id": "LLM01287", "doc_id": "NCT01261832_inc", "case_bucket": "other", "source_criterion": "Acute Myocardial Infarction Undergoing Primary percutaneous coronary intervention.", "candidate_expression": "((Acute Myocardial Infarction) AND (Primary percutaneous coronary intervention))"}
{"candidate_id": "LLM01288", "doc_id": "NCT02968602_exc", "case_bucket": "or", "source_criterion": "History of organic brain disease DSM-IV diagnosis of Alcohol or Substance Dependence within the last six months (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) DSM-IV diagnosis of Alcohol or Substance Abuse within the last one month (except nicotine) or DSM-5 diagnosis of Substance Use Disorder in the last six months (except nicotine) Pregnancy or lactation Severe liver dysfunction (LFT 3X upper limit of normal) Previous known hypersensitivity to tetracyclines Current treatment with tetracycline or derivative Treatment with oral contraceptives (unless a second form of birth control is used and documented) Treatment with cholestyramine or colestipol Treatment with Urinary alkalinizers (e.g., sodium lactate, potassium citrate) Treatment with warfarin Treatment with bupropion, varenicline, or nicotine replacement products in the month prior to study inclusion Less than two months treatment of adjunctive medications AND less than one month on same dose: beta blockers, antidepressants, mood stabilizers, antianxiety medications. Medical condition whose pathology or treatment would significantly increase the risk associated with the proposed protocol. History of head injury, seizures, or stroke Positive urine toxicology screen for substances of non-therapeutic use prior to craving assessments", "candidate_expression": "((Alcohol Abuse) AND (Alcohol Dependence) AND (LFT 3X upper limit of normal) AND (Medical condition would significantly increase the risk associated with the proposed protocol) AND (Pregnancy) AND (Substance Abuse) AND (Substance Dependence) AND (Substance Use Disorder DSM-5 in the last six months) AND (Treatment) AND (Treatment birth control) AND (Urinary alkalinizers) AND (adjunctive medications) AND (antianxiety medications) AND (antidepressants) AND (beta blockers) AND (bupropion) AND (cholestyramine) AND (colestipol) AND (head injury) AND (hypersensitivity Previous) AND (lactation) AND (liver dysfunction Severe) AND (mood stabilizers) AND (nicotine replacement products) AND (oral contraceptives) AND (organic brain disease History of) AND (potassium citrate) AND (seizures) AND (sodium lactate) AND (stroke) AND (tetracycline) AND (tetracycline derivative) AND (tetracyclines) AND (treatment Current) AND (treatment Less than two months same dose) AND (urine toxicology screen Positive substances of non-therapeutic use prior to craving assessments) AND (varenicline) AND (warfarin) AND NOT (Substance Use Disorder DSM-5 in the last six months) AND NOT (nicotine))"}
{"candidate_id": "LLM01289", "doc_id": "NCT01424020_inc", "case_bucket": "other", "source_criterion": "French Native language 18 years old or older Signed consent Covered by the French social care system", "candidate_expression": "((Covered by the French social care system) AND (French Native language) AND (Signed consent) AND (old 18 years or older))"}
{"candidate_id": "LLM01290", "doc_id": "NCT02959580_inc", "case_bucket": "other", "source_criterion": "Idiopathic Granulomatous Mastitis", "candidate_expression": "(Idiopathic Granulomatous Mastitis)"}
{"candidate_id": "LLM01291", "doc_id": "NCT02573909_exc", "case_bucket": "or", "source_criterion": "Planned surgery under regional anesthesia contraindication to the study drug contraindication to the lumbar puncture Contraindication to oxycodone Pregnancy or lactation no informed consent", "candidate_expression": "((Contraindication) AND (Planned) AND (contraindication) AND (lumbar puncture) AND (oxycodone) AND (regional anesthesia) AND (study drug) AND (surgery) AND ((Pregnancy) OR (lactation)))"}
{"candidate_id": "LLM01292", "doc_id": "NCT03100513_exc", "case_bucket": "or", "source_criterion": "Patients with active GIT bleeding. Patients with history of bowel obstruction, perforation. Patients with history of allergy to PEG. Treatment with rifaximin or neomycin in the previous 7 days. Patients with major psychiatric illness. Patients receiving benzodiazepines and narcotics. Patients with compromised renal. Patients receiving medications highly bound to plasma proteins eg. Warfarin. Pregnant or lactating women. Fulminant hepatic failure.", "candidate_expression": "((Fulminant) AND (GIT bleeding) AND (PEG) AND (Pregnant) AND (Warfarin) AND (active) AND (allergy) AND (benzodiazepines) AND (bowel obstruction) AND (bowel perforation) AND (compromised renal) AND (hepatic failure) AND (history) AND (in the previous 7 days) AND (lactating) AND (major psychiatric illness) AND (medications highly bound to plasma proteins) AND (narcotics) AND (neomycin) AND (rifaximin) AND (women))"}
{"candidate_id": "LLM01293", "doc_id": "NCT03260790_inc", "case_bucket": "other", "source_criterion": "Diagnosis of asthma", "candidate_expression": "(asthma)"}
{"candidate_id": "LLM01294", "doc_id": "NCT02821819_exc", "case_bucket": "other", "source_criterion": "PCOS patients Allergy to gonadotrophins Concomitant participation in other trial", "candidate_expression": "((Allergy) AND (Concomitant participation in other trial) AND (PCOS) AND (gonadotrophins))"}
{"candidate_id": "LLM01295", "doc_id": "NCT03008005_exc", "case_bucket": "or", "source_criterion": "clinically significant medical or neurologic condition or neurocognitive dysfunction that would affect function and/or task performance and/or interfere with the study protocol any current (or within past 2 months) medical condition requiring medication that would interact with dronabinol or interfere with the study protocol risk of harm to self or others that requires immediate intervention presence of contraindications, current or past allergic or adverse reaction, or known sensitivity to cannabinoid-like substances (dronabinol/marijuana/cannabis/THC, cannabinoid oil, sesame oil, gelatin, glycerin, and titanium dioxide) lack of fluency in English positive drug screen or alcohol breathalyzer unwilling/unable to sign informed consent document currently pregnant (positive pregnancy test), planning pregnancy, or lactating (women) under 18 or over 50 years of age traumatic brain injury (as defined by The American Congress of Rehabilitation as a person who has had a traumatically induced physiological disruption of brain function (i.e., the head being struck, the head striking an object, and/or the brain undergoing an acceleration/deceleration movement (i.e., whiplash) without direct external trauma to the head), as manifested by at least one of the following: any loss of consciousness; any loss of memory for events immediately before or after the injury; any alteration in mental status at the time of the incident; or focal neurological deficits that may or may not be transient) inability to tolerate small, enclosed spaces without anxiety (e.g. claustrophobia), as determined by self-report and/or a preliminary session in a mock scanner left-handed; presence of ferrous-containing metals within the body (e.g., aneurysm clips, shrapnel/retained particles) anticipation of a required drug test in the 4 weeks following the study. current diagnosis of a mood, anxiety, or other disorder that is more clinically salient than PTSD current moderate or severe alcohol/drug use disorder or in the past 8 weeks current or past diagnosis of bipolar and other related disorders, schizophrenia spectrum, or other psychotic disorders concomitant treatments with medication known to have drug interactions with dronabinol, such as, central nervous system depressants (barbiturates, benzodiazepines, buspirone, lithium, etc) and anticholinergic agents (atropine, scopolamine, antihistamines, etc).", "candidate_expression": "((PTSD) AND (adverse reaction) AND (age) AND (allergic reaction) AND (anticipation of) AND (cannabinoid-like substances) AND (claustrophobia) AND (clinically significant) AND (current) AND (currently) AND (dronabinol) AND (drug interactions) AND (drug test) AND (ferrous-containing metals) AND (in the 4 weeks following the study) AND (in the past 8 weeks) AND (inability) AND (left-handed) AND (medical condition) AND (medication) AND (more clinically salient than PTSD) AND (other) AND (planning) AND (positive) AND (pregnancy test) AND (pregnant) AND (self-report) AND (tolerate small, enclosed spaces without anxiety) AND (traumatic brain injury) AND (treatments) AND (under 18 or over 50 years) AND (unwilling/unable to sign informed consent document) AND (within past 2 months) AND (would interact with) AND ((dronabinol) OR (interfere with the study protocol)) AND ((contraindications) OR (sensitivity)) AND ((current) OR (past)) AND ((THC) OR (cannabinoid oil) OR (cannabis) OR (dronabinol) OR (gelatin) OR (glycerin) OR (marijuana) OR (sesame oil) OR (titanium dioxide)) AND ((medical condition) OR (neurocognitive dysfunction) OR (neurologic condition)) AND ((alcohol breathalyzer) OR (drug screen)) AND ((lactating) OR (pregnancy)) AND ((aneurysm clips) OR (retained particles) OR (shrapnel)) AND ((anxiety disorder) OR (disorder) OR (mood disorder)) AND ((moderate) OR (severe)) AND ((alcohol use disorder) OR (drug use disorder)) AND ((bipolar) OR (psychotic disorders) OR (related disorders) OR (schizophrenia spectrum)) AND ((barbiturates) OR (benzodiazepines) OR (buspirone) OR (lithium)) AND ((anticholinergic agents) OR (central nervous system depressants)) AND ((antihistamines) OR (atropine) OR (scopolamine)))"}
{"candidate_id": "LLM01296", "doc_id": "NCT01630954_exc", "case_bucket": "or", "source_criterion": "Partial mole History of treatment for molar pregnancy like prior evacuation or chemotherapy Women requiring hysterectomy for treatment of H Mole", "candidate_expression": "((H Mole) AND (Partial mole) AND (Women) AND (chemotherapy) AND (evacuation) AND (hysterectomy) AND (molar pregnancy) AND (treatment))"}
{"candidate_id": "LLM01297", "doc_id": "NCT00867958_exc", "case_bucket": "or", "source_criterion": "1. Patient has an allergy to nickel. 2. Patient has a diagnosis of bowel obstruction, bowel strangulation, peritonitis, bowel perforation, local or systemic infection, ischemic bowel, carcinomatosis or extensively spread inflammatory bowel disease. 3. Patient is participating in another clinical trial which may affect this study's outcomes. 4. Patient has been taking regular steroid medication. 5. Patient has contraindications to general anesthesia. 6. Patient has preexisting sphincter problems or evidence of extensive local disease in the pelvis.", "candidate_expression": "((Patient is participating in another clinical trial which may affect this study's outcomes.) AND (allergy to nickel) AND (contraindications to general anesthesia) AND (evidence of) AND (extensive) AND (extensively spread) AND (general anesthesia) AND (nickel) AND (regular) AND (steroid medication) AND ((local disease in the pelvis) OR (sphincter problems)) AND ((bowel obstruction) OR (bowel perforation) OR (bowel strangulation) OR (carcinomatosis) OR (inflammatory bowel disease) OR (ischemic bowel) OR (local infection) OR (peritonitis) OR (systemic infection)))"}
{"candidate_id": "LLM01298", "doc_id": "NCT03126214_exc", "case_bucket": "or", "source_criterion": "Uncontrolled hypertension (defined as average SBP = 160 mmHg [2 readings taken at time of screening]). End stage renal disease (CrCl < 15 ml/min) Valvular Heart Disease including those with prosthetic valve, mitral stenosis (moderate to severe) or valve repair. Excess alcohol intake (males: = 28 units/week, females: = 21 units/week. One unit of alcohol = 8 oz beer, 1 oz hard liquor or 4 oz wine). Intracranial bleed at any point. History of \"Major Bleeding\" at any point (defined as overt bleeding at a critical site including intracranial, intraspinal, intraocular, pericardial, or retroperitoneal; or bleed requiring hospitalization). Foreshortened life-expectancy or severe comorbidities precluding study follow-up period Unable to read/understand English Severe cognitive impairment (defined as score = 5 on the Short Portable Mental Status Questionnaire)", "candidate_expression": "((2 readings) AND (< 15 ml/min) AND (= 160 mmHg) AND (= 21 units/week) AND (= 28 units/week) AND (= 5) AND (CrCl) AND (End stage renal disease) AND (Excess) AND (Foreshortened) AND (History) AND (Intracranial bleed) AND (Major Bleeding) AND (Severe) AND (Short Portable Mental Status Questionnaire) AND (Uncontrolled) AND (Valvular Heart Disease) AND (alcohol intake) AND (at any point) AND (at time of screening) AND (average SBP) AND (bleed) AND (cognitive impairment) AND (critical site) AND (females) AND (hospitalization) AND (hypertension) AND (intracranial) AND (intraocular) AND (intraspinal) AND (life-expectancy) AND (males) AND (mitral stenosis) AND (moderate) AND (overt bleeding) AND (pericardial) AND (prosthetic valve) AND (retroperitoneal) AND (screening) AND (severe) AND (severe comorbidities) AND (valve repair))"}
{"candidate_id": "LLM01299", "doc_id": "NCT02939209_exc", "case_bucket": "or", "source_criterion": "Allergy, sensitivity, or absolute contraindications to any of the medications involved in the study preexisting CNS depression, or taking regularly medication that cause CNS depression preexisting cognitive deficits, dementia, or delirium severe respiratory comorbidities (e.g. chronic obstructive pulmonary disease, pneumonia, respiratory failure) sleep disordered breathing (diagnosed OSA, obesity hypoventilation syndrome) pregnancy and breast feeding history of chronic pain or regular (at least once daily) opioid use preoperatively renal impairment - CrCl =60 mL/minute not fluent in English to be able to participate in the study process, including consent and phone interview Body Mass Index >35 inability to take oral medication.", "candidate_expression": "((Body Mass Index >35) AND (CrCl =60 mL/minute) AND (medication) AND (medications study) AND (not fluent in English to be able to participate in the study process, including consent and phone interview) AND (oral medication inability) AND (pregnancy and breast feeding) AND (renal impairment) AND (respiratory comorbidities severe) AND (sleep disordered breathing) AND ((Allergy) OR (contraindications) OR (sensitivity)) AND ((cognitive deficits) OR (delirium) OR (dementia)) AND ((chronic obstructive pulmonary disease) OR (pneumonia) OR (respiratory failure)) AND ((OSA) OR (obesity hypoventilation syndrome)) AND ((chronic pain) OR (opioid at least once daily preoperatively)) AND ((CNS depression)))"}
{"candidate_id": "LLM01300", "doc_id": "NCT03336801_inc", "case_bucket": "other", "source_criterion": "Scheduled back surgery", "candidate_expression": "((Scheduled) AND (back surgery))"}
```
