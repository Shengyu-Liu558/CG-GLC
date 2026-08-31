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
{"candidate_id": "LLM00551", "doc_id": "NCT02432404_inc", "case_bucket": "or", "source_criterion": "=18-40 year old women BV+ by Amsel criteria and Nugent score OR history of BV in the prior 6 months Willing to use the NuvaRing as directed Not intending or wishing to become pregnant over the course of the study Capable of providing written informed consent", "candidate_expression": "((Amsel criteria) AND (BV) AND (BV in the prior 6 months) AND (Not intending or wishing to become pregnant over the course of the study) AND (Nugent score) AND (NuvaRing) AND (Willing to use) AND (old 18-40 year) AND (women) AND ((Capable of providing written informed consent) OR (written informed consent)))"}
{"candidate_id": "LLM00552", "doc_id": "NCT02726009_exc", "case_bucket": "or", "source_criterion": "Previous or concurrent hormonal management of prostate cancer Contraindication for prescription of Firmagon® Concurrent treatment with a 5-a-reductase inhibitor Considered as a candidate for curative therapy History of severe untreated asthma, anaphylactic reactions or severe urticaria and/or angioedema QTc interval over 450 msec or risk factors for torsades de pointes or on Class IA and Class III anti arrhythmic medications Cancer within the last 5 years except prostate cancer and surgically removed basal or squamous cell carcinoma of the skin Known or suspected hepatic, symptomatic biliary disease (this includes moderate to severe chronic hepatic impairment) Patients with clinically significant laboratory abnormalities / disorders other than prostate cancer Patient with Hepatitis B Virus (HBV), Hepatitis C Virus (HCV) and Human Immunodeficiency Virus (HIV) infections", "candidate_expression": "((5-a-reductase inhibitor) AND (Cancer) AND (Class IA anti arrhythmic medications) AND (Class III anti arrhythmic medications) AND (Contraindication) AND (Firmagon) AND (HBV) AND (HCV) AND (HIV) AND (Hepatitis B Virus infections) AND (Hepatitis C Virus infections) AND (Human Immunodeficiency Virus infections) AND (QTc interval) AND (anaphylactic reactions) AND (angioedema) AND (asthma) AND (basal cell carcinoma of the skin) AND (biliary disease) AND (chronic hepatic impairment) AND (curative therapy) AND (except) AND (hepatic disease) AND (hormonal management) AND (last 5 years) AND (moderate) AND (over 450 msec) AND (prostate cancer) AND (risk factors for torsades de pointes) AND (severe) AND (squamous cell carcinoma of the skin) AND (surgically) AND (untreated) AND (urticaria))"}
{"candidate_id": "LLM00553", "doc_id": "NCT01696617_inc", "case_bucket": "or", "source_criterion": "Age : 18-65 Patients with major depressive disorder according to DSM-IV criteria that have lasted >8 weeks MADRS total score of 18 or higher Patients who responded inadequately (a score of >18 on the MADRS) to first-line antidepressant treatment of 4 week duration Current use of standard antidepressant treatment in monotherapy or combination of 2 antidepressants : escitalopram (10 - 20mg/d), fluoxetine(20 - 40mg/d), paroxetine CR(25 - 50mg/d), sertraline(100 - 150mg/d), mirtazapine (15 - 45mg/d), duloxetine (30 - 60mg/d) or venlafaxine ER(150-225mg/d)", "candidate_expression": "((10 - 20mg/d) AND (100 - 150mg/d) AND (15 - 45mg/d) AND (150-225mg/d) AND (18-65) AND (2) AND (20 - 40mg/d) AND (25 - 50mg/d) AND (30 - 60mg/d) AND (Age) AND (DSM-IV criteria) AND (MADRS) AND (antidepressant) AND (duloxetine) AND (escitalopram) AND (first-line) AND (fluoxetine) AND (lasted >8 weeks) AND (major depressive disorder) AND (mirtazapine) AND (monotherapy) AND (of 4 week) AND (paroxetine CR) AND (responded inadequately) AND (score of 18 or higher) AND (score of >18) AND (sertraline) AND (standard) AND (venlafaxine ER) AND ((antidepressant) OR (antidepressants)))"}
{"candidate_id": "LLM00554", "doc_id": "NCT03320057_inc", "case_bucket": "or", "source_criterion": "Women seeking medication abortion through 70 days gestation Eligible for Mifeprex(r) at a study clinical site English or Spanish speaking Willing and able to participate in the study, including willing to go to the study pharmacy to obtain mifepristone", "candidate_expression": "((Eligible for) AND (Mifeprex(r)) AND (Willing and able to participate in the study) AND (Women) AND (medication abortion) AND (mifepristone) AND (study clinical site) AND (through 70 days gestation) AND (to obtain) AND (willing to go to the study pharmacy) AND ((English speaking) OR (Spanish speaking)))"}
{"candidate_id": "LLM00555", "doc_id": "NCT02385045_inc", "case_bucket": "or", "source_criterion": "• All patients attending for a routine diagnostic endoscopic procedure at St Mary's Hospital NHS Trust for dyspepsia and abdominal pain", "candidate_expression": "((St Mary's Hospital NHS Trust) AND (abdominal pain) AND (diagnostic endoscopic procedure) AND (dyspepsia))"}
{"candidate_id": "LLM00556", "doc_id": "NCT03620526_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00557", "doc_id": "NCT02245256_inc", "case_bucket": "or", "source_criterion": "Adult patients (18years old or older) undergoing living-donor or deceased-donor liver transplantation", "candidate_expression": "((18years old or older) AND (Adult) AND (years) AND ((deceased-donor liver transplantation) OR (living-donor liver transplantation)))"}
{"candidate_id": "LLM00558", "doc_id": "NCT02426034_inc", "case_bucket": "or", "source_criterion": "Age: 18 to75 years old; Pathologically diagnosed with advanced gastric cancer (including adenocarcinoma of the gastroesophageal junction) with measurable metastases outside the stomach (measuring = 10mm on spiral CT scan, satisfying the criteria in RECIST 1.1); Failure of prior therapy (during or after treatment) in patients who have received at least two prior chemotherapy regimens; ECOG PS of 0-2; HB = 90g / L ANC = 1.5 × 109 / L PLT = 80 × 109 / L Bilirubin <1.25 times the upper limit of normal (ULN) ALT and AST <2.5 × ULN; liver metastases, if any, the ALT and AST<5 × ULN Serum Cr = 1 × ULN endogenous creatinine clearance>50ml/min (Cockcroft-Gault formula) An expected survival of = 3 months; Patient received apatinib treatment regimen at investigators' discretion; Patient has to voluntarily join the study and sign the Informed Consent Form for the study; Pregnancy test (serum or urine) has to be performed for woman of childbearing age within 7 days before enrolment and the test result must be negative. They shall take appropriate methods for contraception during the study until the 8th week post the last administration of study drug. For men, (previous surgical sterilization accepted), shall agree to take appropriate methods of contraception during the study until the 8th week post the last administration of study drug.", "candidate_expression": "((ALT) AND (ALT <2.5 × ULN) AND (ANC = 1.5 × 109 / L) AND (AST) AND (AST <2.5 × ULN) AND (Age 18 to75 years old) AND (Bilirubin <1.25 times the upper limit of normal) AND (ECOG PS 0-2) AND (HB = 90g / L) AND (PLT = 80 × 109 / L) AND (Patient has to voluntarily join the study and sign the Informed Consent Form for the study;) AND (Pregnancy test (serum or urine) has to be performed for woman of childbearing age within 7 days before enrolment and the test result must be negative. They shall take appropriate methods for contraception during the study until the 8th week post the last administration of study drug. For men, (previous surgical sterilization accepted), shall agree to take appropriate methods of contraception during the study until the 8th week post the last administration of study drug) AND (adenocarcinoma gastroesophageal junction) AND (apatinib) AND (chemotherapy Failure at least two) AND (expected survival = 3 months) AND (liver metastases) AND ((advanced gastric cancer) OR (metastases stomach)) AND ((Serum Cr = 1 × ULN) OR (endogenous creatinine clearance >50ml/min)))"}
{"candidate_id": "LLM00559", "doc_id": "NCT02926235_inc", "case_bucket": "other", "source_criterion": "All patients will be undergoing a primary unilateral total knee arthroplasty for a diagnosis of osteoarthritis", "candidate_expression": "((osteoarthritis) AND (primary) AND (unilateral total knee arthroplasty))"}
{"candidate_id": "LLM00560", "doc_id": "NCT02426944_inc", "case_bucket": "or", "source_criterion": "history of significant bleeding (i.e. bleeding which required intervention or hospitalization), even in the absence of anticoagulation treatment at the time of the bleeding event, or a cardioembolic event, which occurred on anticoagulation, or a high risk profile of the patient, defined as a CHA2DS2-VASc score = 3 and a HAS-BLED score = 2", "candidate_expression": "((= 2) AND (= 3) AND (CHA2DS2-VASc score) AND (HAS-BLED score) AND (anticoagulation) AND (bleeding) AND (cardioembolic event) AND (high risk profile) AND (occurred on anticoagulation) AND (significant) AND ((hospitalization) OR (intervention)))"}
{"candidate_id": "LLM00561", "doc_id": "NCT03192020_exc", "case_bucket": "or", "source_criterion": "recurrent contracture in the finger to be treated neurologic condition causing the loss of function of the finger to be treated contraindication for collagenase clostridium histolyticym (Xiapex/Xiaflex ®) pregnant or breast feeding TPED > 135° (Tubiana stage 4) in finger to be treated rheumatoid arthritis previous fracture in finger to be treated, which affects range of motion of MP or PIP joint age > 80 years", "candidate_expression": "((> 135°) AND (> 80 years) AND (TPED) AND (Tubiana) AND (affects range of motion) AND (age) AND (collagenase clostridium histolyticym) AND (contracture) AND (contraindication) AND (finger to be treated) AND (fracture) AND (loss of function) AND (neurologic condition) AND (previous) AND (recurrent) AND (rheumatoid arthritis) AND (stage 4) AND ((Xiaflex) OR (Xiapex)) AND ((breast feeding) OR (pregnant)) AND ((MP joint) OR (PIP joint)))"}
{"candidate_id": "LLM00562", "doc_id": "NCT02502734_inc", "case_bucket": "or", "source_criterion": "Aged 5 years to less than 12 years at Visit 1. At least 15 (25%) children of the total study population must be aged 5 to less than 8 years. Male or pre-menarchial female subjects. Subjects must be pre-adolescent without any signs of puberty (Tanner Stage 1). Normal range for their height and weight. Weight and height measurements should fall within the percentile range 3-97% of normal values for age according to Danish growth charts. Have a documented diagnosis of persistent asthma, as defined by the National Institutes of Health for at least 3 months prior to the Screening Visit. A pre-bronchodilatory forced expiratory flow in 1 second (FEV1) at Visit 1 (Screening) >=80% predicted. There should be no Short acting beta-agonist (SABA) use within 4 hours of this measurement. Using one of the following asthma therapies prior to entry into the study: SABA inhaler alone (e.g. salbutamol) on an as required basis and/or Regular non-inhaled corticosteroid (ICS) controller medications for asthma (e.g. cromones or leukotriene receptor antagonists) and/or Previously treated with ICS (equipotent to inhaled budesonide <=400 micrograms (mcg) total daily dose). There must be no ICS use within 2 weeks of Visit 1 (Screening). Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study. Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement. The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC). (2) Subject and their legal guardian(s) understand that the study requires them to be treated on an outpatient basis. (3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.", "candidate_expression": "(((3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.) AND (Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study.) AND (Aged 5 years to less than 12 years) AND (ICS) AND (Male) AND (SABA) AND (SABA inhaler) AND (Tanner Stage 1) AND (The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC).) AND (Weight) AND (Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement.) AND (asthma therapies prior to entry into the study) AND (budesonide <=400 micrograms (mcg)) AND (cromones) AND (female) AND (forced expiratory flow in 1 second (FEV1) pre-bronchodilatory at Visit 1 (Screening) >=80% predicted Visit 1 (Screening)) AND (height Normal range) AND (height within the percentile range 3-97%) AND (leukotriene receptor antagonists) AND (persistent asthma as defined by the National Institutes of Health at least 3 months prior to the Screening Visit) AND (pre-adolescent) AND (pre-menarchial) AND (rescue SABA) AND (salbutamol) AND (weight Normal range) AND NOT (signs of puberty) AND NOT (Short acting beta-agonist (SABA) within 4 hours of this measurement) AND NOT (ICS within 2 weeks of Visit 1 (Screening)))"}
{"candidate_id": "LLM00563", "doc_id": "NCT03299517_exc", "case_bucket": "or", "source_criterion": "Pregnancy Hemodynamic instability Body mass index greater than 40 kg / m2 Use of intravenous amiodarone or lidocaine in the last 24 hours Acute coronary syndrome Presence of tachycardia with irregular or supraventricular RR Contraindications to study drugs", "candidate_expression": "((Acute coronary syndrome) AND (Body mass index greater than 40 kg / m2) AND (Contraindications) AND (Hemodynamic instability) AND (Pregnancy) AND (study drugs) AND (tachycardia) AND ((irregular RR) OR (supraventricular RR)) AND ((amiodarone) OR (lidocaine)))"}
{"candidate_id": "LLM00564", "doc_id": "NCT03296488_exc", "case_bucket": "or", "source_criterion": "Body mass index less than 18 kg/m2 or greater than 30 kg/m2. History of previous open-laparotomy. Surgery with major complication, or need blood transfusion. History of hypersensitivity or adverse reaction to local anesthetics, opioid, or any ingredient of the medications administered in this study. Severe comorbidity. Chronic preoperative opioid consumption. Pregnant or breastfeeding. Inability to use the PCA device.", "candidate_expression": "((Body mass index less than 18 kg/m2 greater than 30 kg/m2) AND (Inability) AND (Pregnant) AND (Surgery) AND (adverse reaction) AND (blood transfusion need) AND (breastfeeding) AND (comorbidity Severe) AND (hypersensitivity) AND (ingredient of the medications administered in this study) AND (local anesthetics) AND (major complication) AND (open-laparotomy History previous) AND (opioid) AND (opioid Chronic preoperative) AND (use the PCA))"}
{"candidate_id": "LLM00565", "doc_id": "NCT02186600_inc", "case_bucket": "other", "source_criterion": "Women who are in their first 5 years of menopause Have a T score between -1 and -2.49 at the femoral neck, total hip, or L1-L4 spine Be 19 years of age or older Have their health care provider's permission to enroll in the study.", "candidate_expression": "((19 years of age or older) AND (L1-L4 spine) AND (T score) AND (Women) AND (age) AND (between -1 and -2.49) AND (femoral neck) AND (menopause) AND (n their first 5 years of menopause) AND (total hip))"}
{"candidate_id": "LLM00566", "doc_id": "NCT02357654_exc", "case_bucket": "other", "source_criterion": "day 3 transfers", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00567", "doc_id": "NCT00970866_exc", "case_bucket": "or", "source_criterion": "Known asthmatic or history of allergy towards peanut or milk products Concurrent participation in another clinical trial Severe illness warranting hospital referral", "candidate_expression": "((allergy history) AND (asthmatic) AND (hospital referral warranting) AND (illness Severe) AND (milk products) AND (participation in another clinical trial) AND (peanut))"}
{"candidate_id": "LLM00568", "doc_id": "NCT00344318_inc", "case_bucket": "or", "source_criterion": "Male or female between, and including, 6-12 weeks (42 to 90 days) of age at the time of the first vaccination. Subjects for whom the investigator believes that their parents/guardians can and will comply with the requirements of the protocol Written informed consent obtained from the parent or guardian of the subject. Free of obvious health problems as established by medical history and clinical examination before entering into the study. Born after a gestation period between 36 and 42 weeks.", "candidate_expression": "((Born) AND (Free) AND (Written informed consent) AND (at the time of the first vaccination) AND (between 36 and 42 weeks) AND (between 42 to 90 days) AND (between 6-12 weeks) AND (gestation period) AND (health problems) AND (obvious) AND (of age) AND ((guardian) OR (parent)))"}
{"candidate_id": "LLM00569", "doc_id": "NCT02851888_exc", "case_bucket": "or", "source_criterion": "Current or planned pregnancy History of neuropathic pain, chronic pain syndrome, or preoperative use of narcotic or neuropathic pain medicine Radiographic signs of osteoarthritis (> Tonis grade 1) Inability to attend follow up visits Documented allergy to local anesthetic", "candidate_expression": "((> 1) AND (Current) AND (History) AND (Inability) AND (Radiographic) AND (Radiographic signs) AND (Tonis grade) AND (allergy) AND (attend follow up visits) AND (chronic pain syndrome) AND (local anesthetic) AND (narcotic medicine) AND (neuropathic pain) AND (neuropathic pain medicine) AND (osteoarthritis) AND (planned) AND (pregnancy) AND (preoperative))"}
{"candidate_id": "LLM00570", "doc_id": "NCT02431442_inc", "case_bucket": "or", "source_criterion": "Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures. Healthy obese male and female volunteers aged 18 to 55 years, inclusive. Heterozygous subjects may be 18 to 65 years inclusive. In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities. Body Mass Index of 30-40 kg/m2, inclusive. Heterozygous subjects may have a broader BMI range; to be eligible heterozygous subjects may have a BMI 27 -55 kg/ m2, inclusive. Stable body weight during the previous 6 months, based on Investigator judgment. Blood pressure <140/90 mmHg at Screening and D-1. Measurement may be repeated within 24 hours, based on Investigator judgment. Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1. Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD. Hormonal contraception must have started at least 3 months prior to screening. A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception. Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution. Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study. Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit. Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time. Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.", "candidate_expression": "((18 to 55 years, inclusive) AND (18 to 65 years inclusive) AND (27 -55 kg/ m2, inclusive) AND (30-40 kg/m2, inclusive) AND (<140/90 mmHg) AND (A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception.) AND (Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures.) AND (BMI) AND (Blood pressure) AND (Body Mass Index) AND (Females) AND (Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1.) AND (Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD.) AND (Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study.) AND (Healthy) AND (Heterozygous) AND (Hormonal contraception) AND (In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities.) AND (Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit.) AND (Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time.) AND (Measurement may be repeated within 24 hours, based on Investigator judgment.) AND (Screening and D-1) AND (Stable) AND (Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (aged) AND (at Screening and D-1) AND (at least 3 months prior to screening) AND (at the Screening Visit and Day -1) AND (based on Investigator judgment) AND (body weight) AND (childbearing potential) AND (during the previous 6 months) AND (female) AND (good general health) AND (heterozygous) AND (male) AND (negative) AND (not) AND (obese) AND (pregnant) AND (screening) AND (serum pregnancy test) AND (the Screening Visit and Day -1))"}
{"candidate_id": "LLM00571", "doc_id": "NCT03431831_exc", "case_bucket": "or", "source_criterion": "Inability to understand and read English. Women pregnant or lactating. persons with terminal illness", "candidate_expression": "((Inability to understand and read English) AND (Women) AND (lactating) AND (pregnant) AND (terminal illness))"}
{"candidate_id": "LLM00572", "doc_id": "NCT03318393_inc", "case_bucket": "or", "source_criterion": "Age 1 day to less than 18 years Cared for in the pediatric intensive care unit or pediatric cardiac intensive care unit receiving venovenous or venoarterial ECMO", "candidate_expression": "((Age 1 day to less than 18 years) AND (pediatric cardiac intensive care unit) AND (pediatric intensive care unit) AND (venoarterial ECMO) AND (venovenous ECMO))"}
{"candidate_id": "LLM00573", "doc_id": "NCT03463564_inc", "case_bucket": "or", "source_criterion": "T1DM for at least 12 months persistent HbA1c levels = 7.5% (58 mmol/mol) despite optimized education therapy, recurrent severe hypoglycemic episodes or high glucose variability willingness to wear the insulin pump", "candidate_expression": "((HbA1c levels persistent = 7.5% 58 mmol/mol) AND (T1DM for at least 12 months) AND (insulin pump) AND (optimized education therapy) AND (wear the insulin pump willingness) AND ((high glucose variability) OR (hypoglycemic episodes)))"}
{"candidate_id": "LLM00574", "doc_id": "NCT03064568_inc", "case_bucket": "other", "source_criterion": "Female age 20-50 y/o who plan to undergo abdominal myomectomy for symptomatic myomatous uterus", "candidate_expression": "((Female) AND (abdominal myomectomy plan to undergo) AND (age 20-50 y/o) AND (myomatous uterus symptomatic))"}
{"candidate_id": "LLM00575", "doc_id": "NCT02562456_inc", "case_bucket": "or", "source_criterion": "Children aging between 3 and 6 years presenting good health conditions whose parents or legal guardians accept and sign the consent form with at least one occlusal or occlusal proximal caries lesion in primary molars only occlusal and/or occlusal-proximal surfaces with caries lesions with dentin involvement", "candidate_expression": "((Children) AND (aging) AND (at least one) AND (between 3 and 6 years) AND (caries lesion) AND (caries lesions) AND (dentin involvement) AND (good health conditions) AND (primary molars) AND (whose parents or legal guardians accept and sign the consent form) AND ((occlusal surfaces) OR (occlusal-proximal surfaces)) AND ((occlusal) OR (occlusal proximal)))"}
```
