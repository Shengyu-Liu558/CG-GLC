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
{"candidate_id": "LLM07201", "doc_id": "NCT02201316_inc", "case_bucket": "or", "source_criterion": "Male and females aged between 18 and 65 years of age inclusive, at the time of signing the informed consent. Healthy as determined by a responsible and experienced physician, based on a medical evaluation including medical history, physical examination, laboratory tests and cardiac monitoring. A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedures. Body weight >= 50 kilogram (kg) and body mass index within the range 19 - 24.9 kg/m^2 (inclusive). A female subject is eligible to participate if she is of: Non-childbearing potential defined as pre-menopausal females with a documented tubal ligation or hysterectomy for this definition, \"documented\" refers to the outcome of the investigator's/designee's review of the subject's medical history for study eligibility, as obtained via a verbal interview with the subject or from the subject's medical records; or postmenopausal defined as 12 months of spontaneous amenorrhea [in questionable cases a blood sample with simultaneous follicle stimulating hormone (FSH) > 40 milli-international units per milliliter (MlU/mL) and estradiol < 40 picograms per mililiter (pg/mL) [<147 picomole per liter] is confirmatory]. Females on hormone replacement therapy (HRT) and whose menopausal status is in doubt will be required to use one of the contraception methods if they wish to continue their HRT during the study. Otherwise, they must discontinue HRT to allow confirmation of post-menopausal status prior to study enrollment. For most forms of HRT, at least 2-4 weeks will elapse between the cessation of therapy and the blood draw; this interval depends on the type and dosage of HRT. Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point. Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle. Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol. This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit. Capable of giving written informed consent, which includes compliance with the requirements and restrictions listed in the consent form Alanine aminotransferase, alkaline phosphatase and bilirubin <=1.5x upper limit of normal (ULN) (isolated bilirubin >1.5xULN is acceptable if bilirubin is fractionated and direct bilirubin <35%). Based on single or averaged corrected QT interval (QTc) values of triplicate electrocardiograms obtained over a brief recording period: QTcF < 450 msec", "candidate_expression": "((12 months) AND (< 40 picograms per mililiter (pg/mL)) AND (< 450 msec) AND (<147 picomole per liter) AND (<=1.5x upper limit of normal (ULN)) AND (> 40 milli-international units per milliliter (MlU/mL)) AND (>1.5xULN) AND (>= 50 kilogram (kg)) AND (A subject with a clinical abnormality or laboratory parameter(s) which is/are not specifically listed in the inclusion or exclusion criteria, outside the reference range for the population being studied may be included only if the Investigator in consultation with the GSK Medical Monitor if required agree and document that the finding is unlikely to introduce additional risk factors and will not interfere with the study procedur) AND (Alanine aminotransferase) AND (Body weight) AND (Female subjects must agree to use contraception until the follow-up contact visit; OR has only same-sex partners, when this is her preferred and usual lifestyle.) AND (Females) AND (Following confirmation of their post-menopausal status, they can resume use of HRT during the study without use of a contraceptive method; Child-bearing potential with negative pregnancy test as determined by serum human chorionic gonadotrophin (hCG) test at screening or prior to dosing AND; Agrees to use one of the contraception methods listed in protocol for an appropriate period of time (as determined by the product label or investigator) prior to the start of dosing to sufficiently minimize the risk of pregnancy at that point.) AND (Healthy) AND (Male subjects with female partners of child-bearing potential must agree to use one of the contraception methods listed in Protocol.) AND (Non) AND (QTcF) AND (This criterion must be followed from the time of the first dose of study medication until the follow-up contact visit.) AND (alkaline phosphatase) AND (as determined by a responsible and experienced physician) AND (at the time of signing the informed consent) AND (between 18 and 65 years) AND (bilirubin) AND (body mass index) AND (cardiac monitoring) AND (childbearing potential) AND (clinical abnormality) AND (corrected QT interval (QTc)) AND (direct bilirubin) AND (electrocardiograms) AND (estradiol) AND (female) AND (females) AND (follicle stimulating hormone (FSH)) AND (hormone replacement therapy (HRT)) AND (in doubt) AND (laboratory parameter) AND (laboratory tests) AND (medical evaluation) AND (medical history) AND (menopausal status) AND (outside the reference range) AND (over a brief recording period) AND (physical examination) AND (postmenopausal) AND (pre-menopausal) AND (signing the informed consent) AND (spontaneous amenorrhea) AND (within the range 19 - 24.9 kg/m^2) AND ((Male) OR (females)) AND ((hysterectomy) OR (tubal ligation)) AND ((age) OR (aged)) AND ((averaged) OR (single)))"}
{"candidate_id": "LLM07202", "doc_id": "NCT02704754_inc", "case_bucket": "other", "source_criterion": "Physically healthy adults age 18-55 who meet DSM-5 criteria for insomnia and Criterion A (exposure to a traumatic event) for PTSD. The index trauma must have occurred within the past 5 years and at least 3 months before enrolling, and insomnia symptoms must have started or worsened after the exposure to the index trauma", "candidate_expression": "((PTSD Criterion A) AND (adults healthy) AND (age 18-55) AND (insomnia DSM-5) AND (trauma index the past 5 years and at least 3 months))"}
{"candidate_id": "LLM07203", "doc_id": "NCT02859480_exc", "case_bucket": "or", "source_criterion": "Taking other drugs which can influence the lipid profile (eg. Niacin, Fibrates; Serum creatinine level > 2.0 mg/dL Serum aspartate transaminase > 3 times upper limit of normal Serum alanine transaminase > 3 times upper limit of normal Having anaphylactic reaction for Rosuvastatin; Having the other contraindications for Rosuvastatin; Having plan to be pregnant; Having life expectancy less than 1 year", "candidate_expression": "((> 2.0 mg/dL) AND (> 3 times upper limit of normal) AND (Rosuvastatin) AND (Serum alanine transaminase) AND (Serum aspartate transaminase) AND (Serum creatinine level) AND (anaphylactic reaction) AND (can influence the lipid profile) AND (contraindications) AND (drugs) AND (less than 1 year) AND (life expectancy) AND (lipid profile) AND (other) AND (plan) AND (pregnant) AND ((Fibrates) OR (Niacin)))"}
{"candidate_id": "LLM07204", "doc_id": "NCT02838810_exc", "case_bucket": "or", "source_criterion": "Patients with liver cirrhosis, Hepatocellular Carcinoma or AFP >2 ULN or other malignancies. Patients with other factors causing liver diseases. Pregnant and lactating women. Patients with concomitant HIV infection or congenital immune deficiency diseases. Patients with diabetes, autoimmune diseases. Patients with important organ dysfunctions. Patients with serious complications (e.g., infection, hepatic encephalopathy, hepatorenal syndrome, gastrointestinal bleeding.) Patients who receive antineoplastic or immunomodulatory therapy in the past 12 months. Patients with a previous use of IFN anti hepatitis B virus treatment or have NAs drug resistance. Patients who can't come back to clinic for follow-up on schedule.", "candidate_expression": "((NAs drug) AND (Patients who can't come back to clinic for follow-up on schedule) AND (Pregnant and lactating women) AND (complications serious) AND (liver diseases) AND (organ dysfunctions important) AND ((autoimmune diseases) OR (diabetes)) AND ((gastrointestinal bleeding) OR (hepatic encephalopathy) OR (hepatorenal syndrome) OR (infection)) AND ((antineoplastic therapy) OR (immunomodulatory therapy)) AND ((IFN anti hepatitis B virus) OR (resistance)) AND ((AFP >2 ULN) OR (Hepatocellular Carcinoma) OR (liver cirrhosis) OR (malignancies)) AND ((HIV infection concomitant) OR (congenital immune deficiency diseases)))"}
{"candidate_id": "LLM07205", "doc_id": "NCT02003339_exc", "case_bucket": "or", "source_criterion": "Invasive hepatocellular carcinoma without any isolated tumor Disease needing 2 injections of Therasphere Thrombosis extending into the porta(thrombosis of one of left or right branch authorized), extra hepatic metastasis Previous treatment by chemoembolization, radiofrequency less than 3 months before radioembolization No antiangiogenic concomitant treatment, 15 days before and 15 days after radioembolization, including Sorafenib Associated disease which could prevent patient from receiving treatment RMI contre-indication(particle or metal prosthesis, pacemaker, claustrophobia) or contrast product contre-indication (allergy) Patient already participating in an other therapeutic trial with an experimental drug Pregnant or childbearing potential women or breastfeeding women minors, persons deprived of liberty or protected adults (maintenance of justice, guardianship or supervision) Unable to comply with trial medical follow-up for geographical, social or psychological reasons Unable to sign an informed consent", "candidate_expression": "((Associated disease could prevent patient from receiving treatment) AND (Pregnant) AND (RMI) AND (RMI contre-indication) AND (Sorafenib) AND (Thrombosis extending into the porta) AND (Unable to sign an informed consent) AND (breastfeeding) AND (chemoembolization) AND (childbearing potential) AND (extra hepatic metastasis) AND (hepatocellular carcinoma Invasive) AND (minors) AND (radiofrequency) AND (women) AND NOT (antiangiogenic treatment 15 days before radioembolization 15 days after radioembolization) AND NOT (isolated tumor) AND NOT (thrombosis left branch right branch))"}
{"candidate_id": "LLM07206", "doc_id": "NCT03088280_inc", "case_bucket": "other", "source_criterion": "Primary kidney transplant recipients, adults", "candidate_expression": "((Primary) AND (adults) AND (kidney transplant))"}
{"candidate_id": "LLM07207", "doc_id": "NCT02580630_exc", "case_bucket": "or", "source_criterion": "Earlier operations in the foot and leg, that is judged to complicate training known arthritis. known diabetes Leg ulcerations or infections in the foot. Judged unable to comply with the training protocol. Daily use of pain killers Glucocorticosteroid injection to the diseased achilles tendon within the last 6 months. Earlier allergic reactions to glucocorticosteroid or local anesthetic. Pregnancy or planning to become pregnant BMI above 30.", "candidate_expression": "((BMI) AND (Daily) AND (Earlier) AND (Glucocorticosteroid) AND (Judged unable to comply with the training protocol.) AND (above 30) AND (allergic reactions) AND (arthritis) AND (diabetes) AND (diseased achilles tendon) AND (injection) AND (pain killers) AND (planning to become) AND (within the last 6 months) AND ((glucocorticosteroid) OR (local anesthetic)) AND ((Pregnancy) OR (pregnant)) AND ((Leg ulcerations) OR (infections in the foot)))"}
{"candidate_id": "LLM07208", "doc_id": "NCT03339284_exc", "case_bucket": "or", "source_criterion": "age under 18y or over 85y diabetes type 1 with complications no co-operation or inadequate finnish language skills persistent pain for other reason severe hepatic insufficiency or paracetamol (acetaminophen) is contraindicated for other reason any type of steroid in regular use oxycodone contraindicated medications changing notably paracetamol (acetaminophen) and/or ropivacaine metabolism in regular use", "candidate_expression": "((acetaminophen) AND (age under 18y or over 85y) AND (complications) AND (contraindicated) AND (diabetes type 1) AND (hepatic insufficiency severe) AND (inadequate finnish language skills) AND (oxycodone) AND (paracetamol) AND (persistent pain other reason) AND (ropivacaine) AND (steroid regular use) AND NOT (co-operation))"}
{"candidate_id": "LLM07209", "doc_id": "NCT03045562_inc", "case_bucket": "other", "source_criterion": "Informed consent must be obtained prior to any study procedure. Age>18 years. Subjects of STEMI who underwent primary PCI within the first 12 hours.", "candidate_expression": "((Age >18 years.) AND (Informed consent must be obtained prior to any study procedure) AND (STEMI) AND (primary PCI within the first 12 hours.))"}
{"candidate_id": "LLM07210", "doc_id": "NCT01799681_exc", "case_bucket": "or", "source_criterion": "any neurological conditions other than PD; significant musculoskeletal or cardiopulmonary diseases; other disorders that may affect balance or locomotion; taken any structured behavioral or exercise programs in the past 3 months or they are receiving regular physical rehabilitation at present; unstable condition on anti-parkinsonian medications; surgical interventions for PD; communication or cognitive deficits with mini-mental state examination, (MMSE) <24/30 (Folstein et al., 1975); a history of more than two falls in the previous 12 months.", "candidate_expression": "((<24/30) AND (PD) AND (anti-parkinsonian medications) AND (at present) AND (disorders that may affect balance or locomotion) AND (falls) AND (history) AND (in the past 3 months) AND (in the previous 12 months) AND (mini-mental state examination, (MMSE)) AND (more than two) AND (neurological conditions) AND (other than) AND (regular physical rehabilitation) AND (significant) AND (surgical interventions for PD) AND (unstable condition) AND ((structured behavioral programs) OR (structured exercise programs)) AND ((cognitive deficits) OR (communication deficits)) AND ((cardiopulmonary diseases) OR (musculoskeletal diseases)))"}
{"candidate_id": "LLM07211", "doc_id": "NCT03297944_inc", "case_bucket": "other", "source_criterion": "valid driver's license english-speaking and literate", "candidate_expression": "((english-speaking) AND (literate) AND (valid driver's license))"}
{"candidate_id": "LLM07212", "doc_id": "NCT02368743_inc", "case_bucket": "or", "source_criterion": "Patient aged 18 years or older. Patient suffering from mild to moderate active proctitis or distal proctosigmoiditis (MAYO score ≥ 3 and ≤ 10) at inclusion based on clinical and endoscopic findings within 6 months before study inclusion. Patient with evidence of endoscopic active proctitis or distal proctosigmoiditis (Montreal classification E1 or E2 defined by an involvement not exceeding 25 cm from the anal margin) within 6 months before study inclusion. Treatment of the current flare with Pentasa® to induce a remission initiated by the patient, the general practitioner or the gastroenterologist, during the inclusion visit or during the week before the inclusion visit. Patient having received oral and written information on the study, without any objections for the use of his/her personal data, and having signed a written Informed Consent Form.", "candidate_expression": "((18 years or older) AND (E1 or E2) AND (MAYO score) AND (Montreal classification) AND (Pentasa) AND (Treatment) AND (active proctitis) AND (aged) AND (at inclusion) AND (distal proctosigmoiditis) AND (during the inclusion visit) AND (during the week before the inclusion visit) AND (endoscopic) AND (flare) AND (inclusion) AND (inclusion visit) AND (involvement not exceeding 25 cm from the anal margin) AND (mild to moderate) AND (study inclusion) AND (the week before the inclusion visit) AND (within 6 months before study inclusion) AND (≥ 3 and ≤ 10))"}
{"candidate_id": "LLM07213", "doc_id": "NCT01866800_exc", "case_bucket": "or", "source_criterion": "History of acute coronary syndrome in the past 30 days. History of congesting heart failure with left ventricular ejection fraction <30% or exacerbation in the past 30 days. Current dialysis treatment. Known furosemide hypersensitivity. Contraindications to placement of a Foley catheter in the bladder.", "candidate_expression": "((<30%) AND (Contraindications) AND (Current) AND (acute coronary syndrome) AND (bladder) AND (congesting heart failure) AND (dialysis treatment) AND (furosemide) AND (hypersensitivity) AND (in the past 30 days) AND (placement of a Foley catheter) AND ((exacerbation) OR (left ventricular ejection fraction)))"}
{"candidate_id": "LLM07214", "doc_id": "NCT02137538_inc", "case_bucket": "or", "source_criterion": "Current height less than 5th percentile AND/OR Predicted adult height (based on bone age) more than 10 cm below target height (mid parental height) Evidence of puberty: physical signs and serum luteinizing hormone > 0.3 IU/L and testosterone > 15 ng/dl", "candidate_expression": "((Evidence of puberty) AND (Predicted adult height bone age more than 10 cm below target height) AND (height Current less than 5th percentile) AND (physical signs) AND (serum luteinizing hormone > 0.3 IU/L) AND (testosterone > 15 ng/dl))"}
{"candidate_id": "LLM07215", "doc_id": "NCT02920177_inc", "case_bucket": "scope", "source_criterion": "Patients with symptomatic FAI Clinical and radiographic evidence of FAI Patients able to provide consent to study participation Completion of 6 weeks of physical therapy program", "candidate_expression": "((FAI) AND (FAI symptomatic Clinical evidence radiographic evidence) AND (Patients able to provide consent to study participation) AND (physical therapy program 6 weeks))"}
{"candidate_id": "LLM07216", "doc_id": "NCT02003339_exc", "case_bucket": "or", "source_criterion": "Invasive hepatocellular carcinoma without any isolated tumor Disease needing 2 injections of Therasphere Thrombosis extending into the porta(thrombosis of one of left or right branch authorized), extra hepatic metastasis Previous treatment by chemoembolization, radiofrequency less than 3 months before radioembolization No antiangiogenic concomitant treatment, 15 days before and 15 days after radioembolization, including Sorafenib Associated disease which could prevent patient from receiving treatment RMI contre-indication(particle or metal prosthesis, pacemaker, claustrophobia) or contrast product contre-indication (allergy) Patient already participating in an other therapeutic trial with an experimental drug Pregnant or childbearing potential women or breastfeeding women minors, persons deprived of liberty or protected adults (maintenance of justice, guardianship or supervision) Unable to comply with trial medical follow-up for geographical, social or psychological reasons Unable to sign an informed consent", "candidate_expression": "((Associated disease could prevent patient from receiving treatment) AND (RMI) AND (RMI contre-indication) AND (Sorafenib) AND (Unable to sign an informed consent) AND (extra hepatic metastasis) AND (hepatocellular carcinoma Invasive) AND (minors) AND (women) AND NOT (antiangiogenic treatment 15 days before radioembolization 15 days after radioembolization) AND NOT (isolated tumor) AND ((chemoembolization) OR (radiofrequency)) AND ((Pregnant) OR (breastfeeding) OR (childbearing potential)) AND ((Thrombosis extending into the porta) OR NOT (thrombosis)) AND ((left branch) OR (right branch)))"}
{"candidate_id": "LLM07217", "doc_id": "NCT01711801_inc", "case_bucket": "or", "source_criterion": "Healthy male volunteers, 18 to 45 years of age, inclusive. Healthy status is defined by absence of evidence of any active or chronic disease following a detailed medical and surgical history, a complete physical examination including vital signs, 12-lead ECG, hematology, blood chemistry, serology and urinalysis Body mass index (BMI) 18 to 30 kg/m2 inclusive Male subjects (whether surgically sterilized or not) with female partners of child-bearing potential must use two forms of contraception, one of which must be a barrier method, for the duration of the study and for 77 days after the last dose", "candidate_expression": "((12-lead ECG) AND (Body mass index (BMI) 18 to 30 kg/m2 inclusive) AND (Healthy) AND (Male) AND (age 18 to 45 years , inclusive) AND (barrier method) AND (blood chemistry) AND (child-bearing potential) AND (female) AND (forms of contraception two for the duration of the study for 77 days after the last dose) AND (hematology) AND (male) AND (physical examination) AND (serology) AND (urinalysis) AND (vital signs) AND NOT (evidence of any active or chronic disease) AND ((surgically sterilized) OR NOT (surgically sterilized)) AND ((medical history) OR (surgical history)))"}
{"candidate_id": "LLM07218", "doc_id": "NCT02186782_inc", "case_bucket": "or", "source_criterion": "Infertile women with eugonadotrophic anovulation/oligoovulation. Unexplained infertility.", "candidate_expression": "((Infertile) AND (infertility Unexplained) AND (women) AND ((anovulation) OR (oligoovulation)))"}
{"candidate_id": "LLM07219", "doc_id": "NCT03198910_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07220", "doc_id": "NCT02219880_inc", "case_bucket": "or", "source_criterion": "Aged between 18-70 years Meets the Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria for generalised anxiety disorder (GAD) based on structured interview (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]. Note that while the MINI-Plus 6 uses the DSM-IV criteria, the same criteria are used in the DSM-V). Presents with anxiety (Hamilton Anxiety Rating Scale = 18) at the time of study entry Fluent in written and spoken English Provides a signed copy of the consent form Primary diagnosis other than GAD Presentation of moderate to severe depressive symptoms (Montgomery-Asberg Rating Scale: MADRS = 18 at time of study entry or = 24 at any time during study) Presentation of suicidal ideation (= 3 on MADRS suicidal thoughts domain at time of study entry or at any time during study) Current diagnosis of bipolar disorder or schizophrenia on structured interview (MINI Plus) Current substance/alcohol use disorder on structured interview (MINI Plus) Page 21 of 39 Commercial-in-Confidence Currently taking an antidepressant, mood stabiliser, antipsychotic, anticonvulsant, warfarin or thyroxin, or current regular use (more than 2 days per week) of a benzodiazepine or opioid-based analgesic Current use of a psychotropic nutraceutical (e.g. St John's wort) Previous intolerance to kava Three or more failed trials of pharmacotherapy for the current GAD episode Recently commenced psychotherapy (within four weeks of study entry) Known or suspected clinically unstable systemic medical disorder Diagnosed hepato-biliary disease/inflammation Elevated liver enzymes at baseline blood test Pregnancy or breastfeeding, or trying to conceive Not using medically approved contraception (including abstinence) if female and of childbearing age Unable to participate in all scheduled visits, treatment plan, or other trial procedures according to the protocol (except for the optional genetic component)", "candidate_expression": "((Aged between 18-70 years) AND (Diagnostic and Statistical Manual (DSM) IV and DSM-V diagnostic criteria) AND (GAD) AND (GAD episode current) AND (Hamilton Anxiety Rating Scale = 18) AND (MADRS = 18 = 24) AND (MADRS suicidal thoughts domain = 3 at time of study entry at any time during study) AND (MINI Plus) AND (Mini International Neuropsychiatric Interview-Plus 6 [MINI-Plus 6]) AND (Montgomery-Asberg Rating Scale) AND (Pregnancy) AND (Primary diagnosis) AND (St John's wort) AND (abstinence) AND (age childbearing) AND (alcohol use disorder) AND (anticonvulsant) AND (antidepressant) AND (antipsychotic) AND (anxiety at the time of study entry) AND (benzodiazepine) AND (bipolar disorder) AND (blood test baseline) AND (breastfeeding) AND (childbearing age) AND (depressive symptoms moderate to severe) AND (female) AND (generalised anxiety disorder) AND (hepato-biliary disease) AND (hepato-biliary inflammation) AND (intolerance Previous) AND (kava) AND (liver enzymes Elevated) AND (medical disorder clinically unstable systemic) AND (mood stabiliser) AND (opioid-based analgesic) AND (psychotherapy Recently within four weeks of study entry Known suspected) AND (psychotropic nutraceutical) AND (scheduled visits) AND (schizophrenia) AND (structured interview) AND (substance use disorder) AND (suicidal ideation) AND (taking Currently) AND (thyroxin) AND (treatment plan) AND (trial procedures) AND (trials of pharmacotherapy Three or more failed) AND (trying to conceive) AND (use Current) AND (use current regular more than 2 days per week) AND (warfarin) AND NOT (GAD) AND NOT (contraception medically approved))"}
{"candidate_id": "LLM07221", "doc_id": "NCT03168555_inc", "case_bucket": "other", "source_criterion": "planned elective cholecystectomy", "candidate_expression": "(cholecystectomy planned elective)"}
{"candidate_id": "LLM07222", "doc_id": "NCT02175186_exc", "case_bucket": "or", "source_criterion": "Pregnant or breast feeding History of Stomach or esophagus surgery Peptic ulcer or reflux esophagitis Zollinger-Ellison syndrome or primary esophageal motility disorders Malignant tumor Bleeding tendency or coagulopathy Contraindication of ALBIS Long term use of aspirin or P2Y12 receptor antagonist within 1month Patients who tool medicine such as PPI, APA,H2blocker, Muscarine receptor antagonist, anti-gastic agent, antacid, anticaogulant, Bisphosphonate agents, Cytotoxic drug, NSAID, adrenal cortex hormone agents (topical treatment is allowed) Terminal patient", "candidate_expression": "((ALBIS) AND (APA) AND (Bisphosphonate agents) AND (Bleeding tendency) AND (Contraindication) AND (Cytotoxic drug) AND (H2blocker) AND (Malignant tumor) AND (Muscarine receptor antagonist) AND (NSAID) AND (P2Y12 receptor antagonist) AND (PPI) AND (Peptic ulcer) AND (Pregnant or breast feeding) AND (Stomach surgery) AND (Zollinger-Ellison syndrome) AND (adrenal cortex hormone agents) AND (antacid) AND (anti-gastic agent) AND (anticaogulant) AND (aspirin) AND (coagulopathy) AND (esophagus surgery) AND (patient Terminal) AND (primary esophageal motility disorders) AND (reflux esophagitis) AND NOT (topical treatment))"}
{"candidate_id": "LLM07223", "doc_id": "NCT02624908_inc", "case_bucket": "other", "source_criterion": "use of basal-bolus insulin onset of diabetes after age 30 BMI less than 35 eGFR at least 60 ml/mn Hb A1c 7.0-10.0% willingness to perform home glucose monitoring willingness to transmit glucose and medication information weekly", "candidate_expression": "((7.0-10.0%) AND (BMI) AND (Hb A1c) AND (after age 30) AND (at least 60 ml/mn) AND (basal-bolus insulin) AND (eGFR) AND (less than 35) AND (onset of diabetes))"}
{"candidate_id": "LLM07224", "doc_id": "NCT02859480_exc", "case_bucket": "or", "source_criterion": "Taking other drugs which can influence the lipid profile (eg. Niacin, Fibrates; Serum creatinine level > 2.0 mg/dL Serum aspartate transaminase > 3 times upper limit of normal Serum alanine transaminase > 3 times upper limit of normal Having anaphylactic reaction for Rosuvastatin; Having the other contraindications for Rosuvastatin; Having plan to be pregnant; Having life expectancy less than 1 year", "candidate_expression": "((Rosuvastatin) AND (Serum alanine transaminase > 3 times upper limit of normal) AND (Serum aspartate transaminase > 3 times upper limit of normal) AND (Serum creatinine level > 2.0 mg/dL) AND (anaphylactic reaction) AND (contraindications) AND (drugs other can influence the lipid profile) AND (life expectancy less than 1 year) AND (lipid profile) AND (pregnant plan) AND ((Fibrates) OR (Niacin)))"}
{"candidate_id": "LLM07225", "doc_id": "NCT02893228_inc", "case_bucket": "or", "source_criterion": "Patients undergoing surgery on shoulder, humerus, or clavicle", "candidate_expression": "((surgery) AND ((clavicle) OR (humerus) OR (shoulder)))"}
```
