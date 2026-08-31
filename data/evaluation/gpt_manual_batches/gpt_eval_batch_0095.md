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
{"candidate_id": "LLM02351", "doc_id": "NCT02257580_inc", "case_bucket": "scope", "source_criterion": "Scheduled for bilateral varus rotational osteotomy (VRO) with or without associated soft tissue and osseous procedures", "candidate_expression": "((Scheduled for) AND (VRO) AND (bilateral) AND (osseous procedures) AND (procedures soft tissue) AND (varus rotational osteotomy))"}
{"candidate_id": "LLM02352", "doc_id": "NCT00182520_inc", "case_bucket": "or", "source_criterion": "Outpatient with primary DSM- IV OCD Completion of a 14-week open label trial of one the following SRI's: fluoxetine 80 mg/day, paroxetine 60 mg/day, fluvoxamine 300 mg/day, clomipramine 250 mg/day, sertraline 200 mg/day, citalopram 60 mg/day, escitalopram 30 mg/day and demonstrating a non or partial responses to SRI treatment (CGI-I of 3 or 4, Y-BOCS reduction of < 35%) Stable (8 wks or longer) concurrent medications including benzodiazepines, sedative hypnotics, antipsychotics, and antidepressants.", "candidate_expression": "((14-week) AND (200 mg/day) AND (250 mg/day) AND (30 mg/day) AND (300 mg/day) AND (60 mg/day) AND (8 wks or longer) AND (80 mg/day) AND (DSM- IV) AND (OCD) AND (Outpatient) AND (SRI treatment) AND (Stable) AND (concurrent) AND (medications) AND (one the following) AND (primary) AND (reduction of < 35%) AND (responses to) AND ((antidepressants) OR (antipsychotics) OR (benzodiazepines) OR (sedative hypnotics)) AND ((citalopram) OR (clomipramine) OR (escitalopram) OR (fluoxetine) OR (fluvoxamine) OR (paroxetine) OR (sertraline)) AND ((CGI-I) OR (Y-BOCS)) AND ((3) OR (4)))"}
{"candidate_id": "LLM02353", "doc_id": "NCT00445029_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women. Evolutive skin disease on the testing zone (lower back). Patients with a clinically significant disease (chronic, recurrent or active). Systemic corticotherapy or immunosuppressive treatment during the previous month, or local corticoid treatment the week before the patch testing. Local or systemic drug use which interacts with the outcome measures. Exposure to sun or UV radiations, 15 days before the patch testing. Patients deprived of their civic rights, in custody, or subject to a tutorial, judiciary or administrative decision. Patients subject to a protection measure. Patients in a critical medical situation. Patients with a personal situation judged by the investigator as unlikely to be compatible with optimal participation in the study, or which could constitute a risk for the patient. Linguistic barrier or psychological profile preventing the patient from signing the consent form. Patient still in an exclusion period following the participation in another clinical trial. Patients having earned more than 4500€ in indemnities for participation in clinical trials during the previous 12 months, including this study.", "candidate_expression": "((15 days before the patch testing) AND (Evolutive skin disease) AND (clinically significant) AND (critical medical situation) AND (disease) AND (drug) AND (during the previous 12 months) AND (during the previous month) AND (earned more than 4500€ in indemnities) AND (interacts with the outcome measures) AND (local corticoid treatment) AND (lower back) AND (participation in another clinical trial) AND (participation in clinical trials) AND (personal situation) AND (preventing) AND (signing the consent form) AND (still in an exclusion period following) AND (subject to a protection measure) AND (testing zone) AND (the patch testing) AND (the previous 12 months) AND (the week before) AND (women) AND ((Pregnant) OR (lactating)) AND ((Exposure to UV radiations) OR (Exposure to sun)) AND ((deprived of their civic rights) OR (in custody) OR (subject to a judiciary decision) OR (subject to a tutorial) OR (subject to administrative decision)) AND ((active) OR (chronic) OR (recurrent)) AND ((Local) OR (systemic)) AND ((Linguistic barrier) OR (psychological profile)) AND ((Systemic corticotherapy) OR (immunosuppressive treatment)))"}
{"candidate_id": "LLM02354", "doc_id": "NCT02117986_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding patients patient with a history of hypersensitivity to colistin", "candidate_expression": "((colistin) AND (hypersensitivity history of) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM02355", "doc_id": "NCT03335436_inc", "case_bucket": "other", "source_criterion": "singleton, term pregnancy currently on buprenorphine maintenance therapy scheduled for elective CD under spinal anesthesia", "candidate_expression": "((CD) AND (buprenorphine) AND (buprenorphine maintenance therapy) AND (currently) AND (elective) AND (pregnancy) AND (scheduled for) AND (singleton) AND (spinal anesthesia) AND (term))"}
{"candidate_id": "LLM02356", "doc_id": "NCT02041299_exc", "case_bucket": "or", "source_criterion": "Thalassemia syndromes; Myelodysplastic syndrome (MDS) or myelofibrosis; Diamond Blackfan anemia; Primary bone marrow failure; Baseline LIC >30 mg/g dw (measured by MRI); Unable or unwilling to undergo a 7 day washout period if currently being treated with deferiprone or deferoxamine or deferasirox; Previous discontinuation of treatment with deferiprone or deferoxamine due to adverse events; History or presence of hypersensitivity or idiosyncratic reaction to deferiprone or deferoxamine; Treated with hydroxyurea within 30 days; History of malignancy; Evidence of abnormal liver function (serum ALT level(s) > 5 times upper limit of normal at screening or creatinine levels >2 times upper limit of normal at screening); A serious, unstable illness, as judged by the Investigator, during the past 3 months before screening/baseline visit including but not limited to: hepatic, renal, gastro-enterologic, respiratory, cardiovascular, endocrinologic, neurologic or immunologic disease; Clinically significant abnormal 12-lead ECG findings; Cardiac MRI T2* <10ms; Myocardial infarction, cardiac arrest or cardiac failure within 1 year before screening/baseline visit; Unable to undergo MRI Presence of metallic objects such as artificial joints, inner ear (cochlear) implants, brain aneurysm clips, pacemakers, and metallic foreign bodies in the eye or other body areas that would prevent use of MRI imaging", "candidate_expression": "((12-lead ECG) AND (<10ms) AND (> 5 times upper limit of normal) AND (>2 times upper limit of normal) AND (>30 mg/g) AND (Baseline) AND (Cardiac MRI T2*) AND (Clinically significant) AND (Diamond Blackfan anemia) AND (LIC) AND (MRI) AND (Presence of metallic objects such as artificial joints, inner ear (cochlear) implants, brain aneurysm clips, pacemakers, and metallic foreign bodies in the eye or other body areas that would prevent use of MRI imaging) AND (Primary bone marrow failure) AND (Thalassemia syndromes) AND (Unable or unwilling to undergo a 7 day washout period if currently being treated with deferiprone or deferoxamine or deferasirox) AND (Unable to undergo) AND (abnormal) AND (as judged by the Investigator) AND (at screening) AND (discontinuation of treatment) AND (during the past 3 months before screening/baseline visit) AND (findings) AND (hydroxyurea) AND (liver function) AND (malignancy) AND (measured by) AND (serious) AND (unstable illness) AND (within 1 year before screening/baseline visit) AND (within 30 days) AND ((deferiprone) OR (deferoxamine)) AND ((hypersensitivity) OR (idiosyncratic reaction)) AND ((Myelodysplastic syndrome (MDS)) OR (myelofibrosis)) AND ((creatinine levels) OR (serum ALT level(s))) AND ((cardiovascular disease) OR (endocrinologic disease) OR (gastro-enterologic disease) OR (hepatic disease) OR (immunologic disease) OR (neurologic disease) OR (renal disease) OR (respiratory disease)) AND ((Myocardial infarction) OR (cardiac arrest) OR (cardiac failure)))"}
{"candidate_id": "LLM02357", "doc_id": "NCT00317148_exc", "case_bucket": "or", "source_criterion": "Body mass index (BMI) of 35 kg/m2 or more. Significant metabolic and endocrine diseases. Diagnosis of cancer. Use of steroids or drugs that interfere with the metabolism of estrogen. Use of any systemic estrogen, progestin, or DHEA in the eight weeks prior to randomization. Use of alternative therapies or natural products to treat postmenopausal symptoms in the four weeks prior to randomization. Palpable fibroids or uterine prolapse: Grade 2 or 3. Cigarette smoking", "candidate_expression": "((Body mass index (BMI) 35 kg/m2 or more) AND (Cigarette smoking) AND (Grade 2 or 3) AND (cancer) AND (postmenopausal symptoms) AND ((DHEA) OR (systemic estrogen) OR (systemic progestin)) AND ((alternative therapies) OR (natural products)) AND ((Palpable fibroids) OR (uterine prolapse)) AND ((endocrine diseases) OR (metabolic diseases)) AND ((drugs that interfere with the metabolism of estrogen) OR (steroids)))"}
{"candidate_id": "LLM02358", "doc_id": "NCT03445949_inc", "case_bucket": "scope", "source_criterion": "successful left atrial appendage occlusion with Amulet device within 37 days prior to randomization. treatment with dual antiplatelet therapy (clopidogrel and acetylsalicylic acid) between left atrial appendage closure and randomization participant's age 18 years or older at the time of signing the informed consent form participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable participant is willing to sign the study informed consent form", "candidate_expression": "((18 years or older) AND (Amulet device) AND (acetylsalicylic acid) AND (age) AND (at the time of signing the informed consent form) AND (between left atrial appendage closure and randomization) AND (clopidogrel) AND (dual antiplatelet therapy) AND (left atrial appendage closure) AND (left atrial appendage occlusion) AND (participant is willing to follow all study procedures; especially randomized antiplatelet treatment regimen and follow-up visits with transesophageal echocardiography when applicable) AND (participant is willing to sign the study informed consent form) AND (randomization) AND (signing the informed consent form) AND (successful) AND (within 37 days prior to randomization))"}
{"candidate_id": "LLM02359", "doc_id": "NCT03208127_inc", "case_bucket": "other", "source_criterion": "Recipient is Age = 18 years Met MGH transplant center criteria, listed for liver transplant HCV naive Able to sign informed consent", "candidate_expression": "((Able to sign informed consent) AND (Age = 18 years) AND (HCV naive) AND (liver transplant MGH transplant center criteria))"}
{"candidate_id": "LLM02360", "doc_id": "NCT01000155_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sickle cell disease Clinically significant disease defined as at least 1 painful episode per year averaged over the previous 3 years or a history of priapism, stroke, acute chest syndrome, avascular necrosis, multi-organ failure or the need for chronic narcotic medications for pain from sickle cell disease Must have failed a previous attempt at treatment with hydroxyurea defined as the inability to achieve a significant absolute increase in % fetal hemoglobin or the inability to tolerate hydroxyurea treatment due to severe side effects such as but not limited to myelosuppression, gastrointestinal symptoms, edema or hepatic enzyme elevations or have contraindications to hydroxyurea 18 years of age or older Hematologic laboratory values as outlined in the protocol Non-hematologic laboratory values as outlined in the protocol Must agree not to donate blood or other bodily fluid while taking the study drug and for 28 days thereafter Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment Women of child-bearing potential and men must agree to use 2 forms of adequate contraception prior to study entry and for the duration of study participation", "candidate_expression": "((18 years or older) AND (2 forms) AND (72 hours or less prior to starting treatment) AND (Clinically significant) AND (Clinically significant disease) AND (Diagnosis) AND (Must agree to) AND (WCBP) AND (Women) AND (Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment) AND (adequate) AND (age) AND (averaged over the previous 3 years) AND (child-bearing potential) AND (chronic) AND (contraception) AND (donate blood) AND (donate bodily fluid) AND (for 28 days thereafter) AND (for the duration of study participation) AND (history) AND (must agree to) AND (need for) AND (negative) AND (not) AND (pain) AND (per year averaged over the previous 3 years at least 1) AND (prior to study entry) AND (serum pregnancy test) AND (sickle cell disease) AND (starting treatment) AND (study drug) AND (study entry) AND (study participation) AND (taking the study drug) AND (the previous 3 years) AND (treatment) AND (while taking the study drug) AND ((acute chest syndrome) OR (avascular necrosis) OR (multi-organ failure) OR (narcotic medications) OR (painful episode) OR (priapism) OR (stroke)) AND ((Women) OR (men)))"}
{"candidate_id": "LLM02361", "doc_id": "NCT03339284_inc", "case_bucket": "other", "source_criterion": "patients with renal cancer coming to the laparoscopic radical nephrectomy", "candidate_expression": "((laparoscopic) AND (radical nephrectomy) AND (renal cancer))"}
{"candidate_id": "LLM02362", "doc_id": "NCT03345589_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed with primary biliary cholangitis Treated with Ursodeoxycholic Acid in West China Hospital for at least 6 month and suboptimal response to Ursodeoxycholic Acid", "candidate_expression": "((Ursodeoxycholic Acid) AND (West China Hospital) AND (for at least 6 month) AND (primary biliary cholangitis) AND (suboptimal response))"}
{"candidate_id": "LLM02363", "doc_id": "NCT03115151_inc", "case_bucket": "other", "source_criterion": "Adult subjects aged 18 years or older Scheduled for elective posterior lumbar spinal fusion surgery between 1 and 3 levels", "candidate_expression": "((Adult) AND (aged 18 years or older) AND (posterior lumbar spinal fusion surgery Scheduled for elective between 1 and 3 levels))"}
{"candidate_id": "LLM02364", "doc_id": "NCT03404479_exc", "case_bucket": "or", "source_criterion": "Secondary knee osteoarthritis Other inflammatory Knee Osteoarthritis (e.g. gout, rheumatoid arthritis, etc.) Patients presenting with gastroesophageal reflux disease, peptic ulcer. Helicobacter infected patients who have not been treated for eradication (recruitment if negative in re-examination after treatment). Short bowel syndrome that can cause inflammatory bowel disease (ulcerative colitis, Crohn's disease) and drug absorption disorder. Intestinal obstruction syndrome Unexplained abdominal pain ALT(Alanine aminotransferase) level of liver function test exceeded 5 times of reference range Total bilirubin level exceeded 2 mg / dL Serum albumin level less than 2 g / dL Ascites Hepatic encephalopathy Hepatitis B, hepatitis C (excluding healthy carriers) or HIV positive MDRD(Modification of Diet in Renal Disease) Estimated Glomerular filtration rate less than 60 mL / m2 Patients with hyperkalemia (over 5.5 meq / L) history of asthma, acute rhinitis, nasal polyps, angioedema, urticaria or allergic reactions to aspirin or other non-steroidal anti-inflammatory drugs(including COX-2 inhibitors). Malignant tumors other than basal cell or squamous cell carcinoma of the skin, CIN(Cervical Intraepitherial Neoplasia) and CIS(Carcinoma in situ) of the cervix, and intraepithelial carcinoma of other areas Within 5 years of consent date. Medical history of hypersensitivity to the components of the investigational products. (The components of test drug 1 and 2, including the Rhein-based drug) Patients with an allergic reaction to sulfonamide. Patients with galactose intolerance, lapp lactase deficiency or glucose-galactose malabsorption. Subjects who have not reached the prescribed period after receiving contraindicated medication or treatment before participation in this clinical trial. Patients receiving contraindicated medication. Alcohol and other drug abuse cases based on 6 months before screening. Pregnant women or nursing mothers who are not willing to stop breastfeeding. (1) Menopause (non-therapy-induced amenorrhea of more than 12 months) Female (2) Female infertility due to surgery (no ovaries and / or uterus) (3) If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization. (4) Female subjects who agreed to abstinence during the clinical trial period. If the subject is assured of an abstinence throughout the trial period.(e.g. clergy) However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence. (5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial: Oral contraceptive The contraceptive patch Intra uterine device (IUD) contraceptive implant contraceptive injection intrauterine hormonal apparatus Tubal ligation and infertility surgery If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials. Patients who are scheduled for surgery during the clinical trial period or who have difficulties in completing the protocol during this clinical trial due to other reasons. In addition to the above, other diseases that the investigator judges to be inappropriate.", "candidate_expression": "(((5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial:) AND (ALT(Alanine aminotransferase) level exceeded 5 times of reference range) AND (Ascites) AND (COX-2 inhibitors) AND (Estimated Glomerular filtration rate MDRD(Modification of Diet in Renal Disease) less than 60 mL / m2) AND (Female) AND (Female subjects who agreed to abstinence during the clinical trial period) AND (Helicobacter infected) AND (Hepatic encephalopathy) AND (However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence) AND (If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials.) AND (If the subject is assured of an abstinence throughout the trial period.(e.g. clergy)) AND (If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization.) AND (Intestinal obstruction syndrome) AND (Intra uterine device (IUD)) AND (Menopause) AND (Oral contraceptive) AND (Pregnant women or nursing mothers who are not willing to stop breastfeeding) AND (Serum albumin level ess than 2 g / dL) AND (Short bowel syndrome that can cause inflammatory bowel disease) AND (Total bilirubin level exceeded 2 mg / dL) AND (abdominal pain Unexplained) AND (allergic reaction) AND (amenorrhea non-therapy-induced more than 12 months) AND (components of the investigational products) AND (contraceptive implant) AND (contraceptive injection) AND (contraceptive patch) AND (contraindicated medication 6 months before screening) AND (drug absorption disorder) AND (hyperkalemia over 5.5 meq / L) AND (hypersensitivity) AND (infertility due to surgery) AND (inflammatory Knee Osteoarthritis Other) AND (inflammatory bowel disease can cause) AND (intrauterine hormonal apparatus) AND (knee osteoarthritis Secondary) AND (liver function test) AND (sulfonamide) AND NOT (treated for eradication) AND NOT (healthy carriers) AND ((Tubal ligation) OR (infertility surgery)) AND ((Crohn's disease) OR (ulcerative colitis)) AND ((HIV positive) OR (Hepatitis B) OR (hepatitis C)) AND ((acute rhinitis) OR (allergic reactions) OR (angioedema) OR (asthma) OR (nasal polyps) OR (urticaria)) AND ((gout) OR (rheumatoid arthritis)) AND ((aspirin) OR (non-steroidal anti-inflammatory drugs other)) AND ((basal cell carcinoma of the skin) OR (squamous cell carcinoma of the skin)) AND ((CIN(Cervical Intraepitherial Neoplasia)) OR (CIS(Carcinoma in situ) of the cervix) OR (Malignant tumors) OR (intraepithelial carcinoma)) AND ((Rhein-based drug) OR (components of test drug 1) OR (components of test drug 2)) AND ((galactose intolerance) OR (glucose-galactose malabsorption) OR (lapp lactase deficiency)) AND ((Alcohol abuse) OR (drug abuse)) AND ((gastroesophageal reflux disease) OR (peptic ulcer)) AND ((no ovaries) OR (no uterus)))"}
{"candidate_id": "LLM02365", "doc_id": "NCT00965900_inc", "case_bucket": "or", "source_criterion": "Liver cirrhosis Age between 18 and 70 years Esophageal varices with high bleeding risk: more than F2 and red color sign No previous history of upper gastrointestinal bleeding No previous history of endoscopic, radiologic, or surgical therapy for varices or ascites Do not take beta-blocker, ACE inhibitor, or nitrate Child-Pugh score <12", "candidate_expression": "((<12) AND (ACE inhibitor) AND (Age) AND (Child-Pugh score) AND (Do not) AND (Esophageal varices) AND (F2) AND (Liver cirrhosis) AND (No) AND (ascites) AND (beta-blocker) AND (between 18 and 70 years) AND (endoscopic therapy) AND (high bleeding risk) AND (more than) AND (nitrate) AND (radiologic therapy) AND (red color sign) AND (surgical therapy) AND (upper gastrointestinal bleeding) AND (varices))"}
{"candidate_id": "LLM02366", "doc_id": "NCT02106624_inc", "case_bucket": "or", "source_criterion": "need mechanical ventilation for more than 2 days mean blood pressure more than 60mmHg predicted ICU stay more than 7 days tolerance of parenteral or enteral nutrition", "candidate_expression": "((ICU) AND (for more than 2 days) AND (mean blood pressure) AND (mechanical ventilation) AND (more than 60mmHg) AND (more than 7 days) AND (need) AND (predicted ICU stay) AND (tolerance) AND ((enteral nutrition) OR (parenteral nutrition)))"}
{"candidate_id": "LLM02367", "doc_id": "NCT02902120_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age at the time of screening Have stable renal function for one month (30 days) prior to enrollment Have Chronic HCV infection prior to transplantation with documented HCV viremia = 1,000 IU/ml at screening and either documented HCV Ab positivity or HCV viremia = 1,000 IU/ml at least 6 months prior to enrollment. Documented genotype 1 HCV infection prior to enrollment and after their transplant in the post-transplantation cohort HCV disease staging within 12 months prior to enrollment by liver biopsy, transient elastography, or biochemical testing Be able to give informed consent and comply with study guidelines Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment. On the transplant waiting list followed by the University of Maryland's nephrology clinic or the Baltimore VA's nephrology clinic On chronic hemodialysis not yet on the transplant list and followed in the University's hemodialysis center or in the University's nephrology clinic Have chronic kidney disease with GFR <50", "candidate_expression": "((<50) AND (= 1,000 IU/ml) AND (At least 18 years) AND (Be able to give informed consent and comply with study guidelines) AND (Chronic HCV infection) AND (GFR) AND (HCV) AND (HCV Ab) AND (HCV infection) AND (HCV viremia) AND (Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment.) AND (after their transplant i) AND (age) AND (at least 6 months prior to enrollment.) AND (biochemical testing) AND (chronic) AND (chronic kidney disease) AND (disease staging) AND (enrollment) AND (genotype 1) AND (hemodialysis) AND (liver biopsy) AND (one month (30 days) prior to enrollment) AND (positivity) AND (prior to enrollment) AND (prior to transplantation) AND (renal function) AND (stable) AND (transient elastography) AND (transplant) AND (transplantation) AND (within 12 months prior to enrollment))"}
{"candidate_id": "LLM02368", "doc_id": "NCT02548013_inc", "case_bucket": "other", "source_criterion": "1. PPROM with gestational age between 27 to 34 weeks 2. Cephalic presentation 3. Clear amniotic fluid 4. Oral temperature > 38 C 5. Near distance from the hospital (the patient can reach hospital within one hour ) 6. Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home . 7. Maternal and fetal condition remain stable after hospitalization for 72 hours", "candidate_expression": "((Cephalic presentation) AND (Clear amniotic fluid) AND (Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home .) AND (Maternal condition) AND (Near distance from the hospital (the patient can reach hospital within one hour )) AND (Oral temperature > 38 C) AND (PPROM) AND (fetal condition) AND (gestational age between 27 to 34 weeks))"}
{"candidate_id": "LLM02369", "doc_id": "NCT03475589_exc", "case_bucket": "or", "source_criterion": "Confirmed allergy to apatinin and or its excipients; Hypertension (high blood pressure) that can not be controlled by drugs; A history of active hemorragge, ulcer, intestinal perforation, intestinal obstruction, or major surgery no older than 30 days; NYHA III-IV heart function, or severe hepatic or renal insufficiency (Grade 4); Presence of multiple factors that affect oral medications, such as difficulty swallowing, nausea, vomiting, chronic diarrhea and intestinal obstruction; Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study; Patients who have a history of psychotropics abuse and can not quit, or who have mental disorders; Participation in other drug clinical trial within the last 4 weeks; Prior therapy with VEGFR inhibitors such as sorafenib and sunitinib; Presence of comorbidities that seriously affect the patient's safety or ability to complete the study, in the investigator's judgment; Patients who can not tolerate apatinib treatment as judged by the investigator depending on the their medical history; Patients that are considered ineligible for this study by the investigator.", "candidate_expression": "((Hypertension controlled by drugs) AND (NYHA III-IV) AND (Participation in other drug clinical trial within the last 4 weeks;) AND (Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study;) AND (VEGFR inhibitors) AND (abuse history) AND (allergy) AND (apatinib) AND (apatinin) AND (chronic diarrhea) AND (difficulty swallowing) AND (drugs) AND (excipients) AND (heart function) AND (hemorragge active) AND (hepatic insufficiency Grade 4) AND (high blood pressure) AND (intestinal obstruction) AND (intestinal perforation) AND (major surgery) AND (mental disorders) AND (nausea) AND (psychotropics) AND (renal insufficiency) AND (sorafenib) AND (sunitinib) AND (ulcer) AND (vomiting) AND NOT (tolerate))"}
{"candidate_id": "LLM02370", "doc_id": "NCT03015818_inc", "case_bucket": "or", "source_criterion": "age > 18 written informed consent SVD defined on echocardiography by an alteration of bioprosthesis leaflets function with a mean transvalvular gradient > 20 mmHg and maximal velocity = 3 m/s and effective orifice area =1.2 cm², and/or an aortic regurgitation more or equal to grade 2 on 4.", "candidate_expression": "((SVD) AND (age > 18) AND (alteration of bioprosthesis leaflets function) AND (aortic regurgitation) AND (echocardiography) AND (effective orifice area =1.2 cm²) AND (grade more or equal to 2 on 4) AND (maximal velocity = 3 m/s) AND (mean transvalvular gradient > 20 mmHg) AND (written informed consent))"}
{"candidate_id": "LLM02371", "doc_id": "NCT03177837_exc", "case_bucket": "or", "source_criterion": "COPD exacerbation, very severe COPD with hypoxemia at low altitude (FEV1/FVC <0.7, FEV1 <40% predicted, oxygen saturation on room air <92% at 750 m). Comorbidities such as uncontrolled cardiovascular disease, i.e., unstable systemic arterial hypertension, coronary artery disease; previous stroke; OSA; pneumothorax in the last 2 months. Internal, neurologic, rheumatologic or psychiatric disease including current heavy smoking (>20 cigarettes per day) Known renal failure or allergy to acetazolamide and other sulfonamides", "candidate_expression": "((COPD exacerbation) AND (COPD very severe) AND (Comorbidities) AND (FEV1 <40% predicted) AND (FEV1/FVC <0.7) AND (OSA) AND (acetazolamide other) AND (allergy) AND (cardiovascular disease uncontrolled) AND (cigarettes per day >20) AND (coronary artery disease) AND (disease rheumatologic psychiatric) AND (hypoxemia low altitude) AND (oxygen saturation room air <92% 750 m) AND (pneumothorax in the last 2 months Internal neurologic) AND (renal failure) AND (smoking heavy) AND (stroke previous) AND (sulfonamides) AND (systemic arterial hypertension unstable))"}
{"candidate_id": "LLM02372", "doc_id": "NCT02858180_inc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection of Genotype 1, 4, 5, or 6 HCV RNA > 103 IU/mL at screening 18 years of age or older Diagnosis of chronic HCV infection, defined as positive HCV antibody or HCV RNA more than 6 months prior to screening OR an assessment of fibrosis F2 or greater prior to screening. NYHA Class III: Subjects with cardiac disease resulting in marked limitation of physical activity. They are comfortable at rest. Less than ordinary physical activity causes fatigue, palpitation, dyspnea, or anginal pain. NYHA Class IV: Patient with cardiac disease resulting in inability to carry on any physical activity without discomfort. Symptoms of cardiac insufficiency or of the anginal syndrome may be present even at rest. If any physical activity is undertaken, discomfort is increased. ejection fraction = 30% hospitalized for heart failure in last 12 months ILD criteria: diagnosis of interstitial lung disease with chronic supplemental oxygen requirement at rest and/or with exertion. Forced expiratory volume (FEV1)< 30% predicted OR any FEV1 with chronic supplemental oxygen requirement at rest and/or with exertion OR any FEV1 with chronic hypercapnia (baseline partial pressure of arterial carbon dioxide [PaCO2] > 45)", "candidate_expression": "((Chronic HCV Infection Genotype 1 Genotype 4 Genotype 5 Genotype 6) AND (FEV1) AND (Forced expiratory volume < 30% predicted) AND (HCV RNA > 103 IU/mL at screening) AND (HCV RNA more than 6 months prior to screening) AND (HCV antibody positive more than 6 months prior to screening) AND (ILD criteria) AND (NYHA Class III) AND (NYHA Class IV) AND (PaCO2) AND (age older 18 years) AND (assessment of fibrosis F2 or greater prior to screening) AND (chronic HCV infection) AND (chronic hypercapnia) AND (chronic supplemental oxygen requirement at rest with exertion) AND (ejection fraction = 30%) AND (heart failure) AND (hospitalized in last 12 months) AND (interstitial lung disease) AND (partial pressure of arterial carbon dioxide > 45))"}
{"candidate_id": "LLM02373", "doc_id": "NCT03004261_exc", "case_bucket": "or", "source_criterion": "Patients receiving prednisone = 1mg/kg/d for the treatment of acute GVHD or mild, severe chronic GVHD. Recipient < 14years of age Donor is sero-positive in HBV/HCV/HIV or RPR.", "candidate_expression": "((age < 14years) AND (prednisone = 1mg/kg/d) AND ((sero-positive in HBV) OR (sero-positive in HCV) OR (sero-positive in HIV) OR (sero-positive in RPR)) AND ((mild) OR (severe)) AND ((GVHD chronic) OR (acute GVHD)))"}
{"candidate_id": "LLM02374", "doc_id": "NCT01967420_exc", "case_bucket": "other", "source_criterion": "Active substance dependency History of severe head injury", "candidate_expression": "((History) AND (severe head injury) AND (substance dependency))"}
{"candidate_id": "LLM02375", "doc_id": "NCT01346436_inc", "case_bucket": "other", "source_criterion": "women proven pelvic floor dysfunction informed consent", "candidate_expression": "((nformed consent) AND (pelvic floor dysfunction) AND (women))"}
```
