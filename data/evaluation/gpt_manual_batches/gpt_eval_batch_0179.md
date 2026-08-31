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
{"candidate_id": "LLM04451", "doc_id": "NCT01518946_inc", "case_bucket": "or", "source_criterion": "1. Male and female subjects must be 18 years of age or older and ambulatory. 2. Females of child-bearing potential (FOCP) must have a negative serum beta human chorionic gonadotropin (HCG) pregnancy test. 3. A documented history of severe Symptomatic Orthostatic Hypotension (SOH) that, in the judgment of the treating physician, has required treatment with midodrine HCl , and has been at a stable dose for at least 3 months. 4. The subject has manifested at least 1 of the following symptoms while standing or had a medical history of 1 of the following when not treated for orthostatic hypotension (OH): dizziness, lightheadedness, feeling faint, or feeling like they might black out.", "candidate_expression": "((1) AND (18 years or older) AND (Females) AND (Male) AND (Symptomatic Orthostatic Hypotension (SOH)) AND (age) AND (ambulatory) AND (at least 1) AND (child-bearing potential) AND (dizziness) AND (feeling faint) AND (feeling like they might black out) AND (female) AND (for at least 3 months) AND (lightheadedness) AND (midodrine HCl) AND (negative) AND (not) AND (orthostatic hypotension (OH)) AND (serum beta human chorionic gonadotropin (HCG) pregnancy test) AND (severe) AND (stable dose) AND (treated))"}
{"candidate_id": "LLM04452", "doc_id": "NCT02267616_inc", "case_bucket": "other", "source_criterion": "Women age 18-45 Within 6 months of expiration or beyond the end of the FDA-approved duration of use of the levonorgestrel intrauterine device (LNG-IUD = 5 years) OR the etonogestrel-releasing subdermal implant (ENG implant = 3 years) Able to consent in English or Spanish. Not pregnant at the time of enrollment", "candidate_expression": "((Able to consent in English or Spanish) AND (Women) AND (age 18-45) AND NOT (pregnant at the time of enrollment))"}
{"candidate_id": "LLM04453", "doc_id": "NCT03064867_exc", "case_bucket": "or", "source_criterion": "Prior treatment toxicities have not resolved to < Grade 2 according to NCI CTCAE Version 4.0 (except clinically insignificant toxicities such as alopecia). Subjects receiving any other investigational agents. Patients with active tumor lysis syndrome (TLS) either from laboratory or clinical changes. Patients with active central nervous system (CNS) disease defined as symptomatic meningeal lymphoma or known CNS parenchymal lymphoma. History of severe allergic reactions attributed to compounds of similar chemical or biologic composition to rituximab or other agents used in this study. Subjects with uncontrolled intercurrent illness . HIV-positive subjects on combination antiretroviral therapy are ineligible because of the potential for pharmacokinetic interactions with Venetoclax. In addition, these subjects are at increased risk of lethal infections when treated with marrow suppressive therapy. Appropriate studies will be undertaken in subjects receiving combination antiretroviral therapy when indicated. HIV testing prior to enrollment is not required for screening but strongly encouraged for patients with no documented prior HIV assessment. Presence of positive test results for hepatitis B virus (HBV), hepatitis B surface antigen (HBsAg), or hepatitis C (HCV) antibody. Patients who are positive for HCV antibody must be negative for HCV by polymerase chain reaction (PCR) to be eligible for study participation Patients with occult or prior HBV infection (defined as positive total hepatitis B core antibody [HBcAb] and negative HBsAg) may be included if HBV DNA is undetectable. These patients must be willing to undergo monthly DNA testing. Women who are pregnant or lactating Malabsorption syndrome or other condition that precludes enteral route of administration Chemotherapy or radiation within 3 weeks of the first scheduled study treatment. Less than 2-year disease free from another primary malignancy (other than squamous or basal cell carcinoma of the skin, \"in-situ\" carcinoma of the cervix or breast, superficial bladder carcinoma, or previously treated localized prostate cancer with normal prostate specific antigen (PSA) levels). Patients who have had completed all anti-cancer treatment for another primary malignancy more than 2 years prior to screening are eligible if they are not considered to have a \"currently active\" malignancy based on having less than a 30% risk of relapse. Major surgery, other than diagnostic surgery, within 2 weeks. Medical condition requiring chronic use of high dose systemic corticosteroids (i.e., doses of prednisone higher than 10 mg/day or equivalent). Brief (<15 days) treatment with glucocorticoids (prednisone 100 mg by mouth daily, or equivalent) is acceptable. Known allergy to both xanthine oxidase inhibitors and rasburicase. Use of warfarin is prohibited. Anticoagulation with low-molecular weight heparin (i.e. enoxaparin) or direct thrombin inhibitors is permitted. The following concomitant medications are not allowed from 7 days prior to the first dose of study drug and during venetoclax administration: Strong CYP3A4 inhibitors including but not limited to fluconazole, ketoconazole, and clarithromycin or strong CYP3A4 inducers included but not limited to rifampin, carbamazepine. Receipt of live-virus vaccines within 28 days prior to the initiation of study treatment or need for live-virus vaccines at any time during study treatment. Concomitant medications that fall into the categories below could potentially lead to adverse reactions and should be considered cautionary. Moderate/Weak CYP3A inducers such as efavirenz and oxcarbazepine CYP2C8 substrates such as thiazolidinediones (glitazones) and select statins (because of expected inhibition of the metabolism of CYP2C8 substrates) by venetoclax CYP2C9 substrates such as tolbutamide (because of expected inhibition of the metabolism of CYP2C9 substrates by venetoclax. It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin.", "candidate_expression": "((\"in-situ\" carcinoma of the cervix) AND (\"in-situ\" carcinoma of the cervix breast) AND (100 mg daily) AND (7 days prior) AND (<15 days) AND (Anticoagulation) AND (CNS parenchymal lymphoma) AND (CYP2C8 substrates) AND (CYP2C9 substrates) AND (Chemotherapy) AND (HBV DNA) AND (HBV infection) AND (HBsAg) AND (HCV) AND (HCV antibody) AND (HIV-positive) AND (It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin) AND (Less than 2-year) AND (Major surgery) AND (Malabsorption syndrome) AND (Medical condition) AND (Moderate CYP3A inducers) AND (Strong CYP3A4 inhibitors) AND (Weak CYP3A inducers) AND (Women) AND (allergic reactions) AND (allergy) AND (another) AND (anti-cancer treatment) AND (any time during) AND (are eligible) AND (carbamazepine) AND (central nervous system (CNS) disease) AND (chronic) AND (clarithromycin) AND (combination antiretroviral therapy) AND (compounds of similar chemical or biologic composition to other agents used in this study) AND (compounds of similar chemical or biologic composition to rituximab) AND (condition that precludes enteral route of administration) AND (diagnostic surgery) AND (direct thrombin inhibitors) AND (disease free) AND (efavirenz) AND (enoxaparin) AND (first dose of study drug) AND (fluconazole) AND (glitazones) AND (glucocorticoids) AND (hepatitis B surface antigen (HBsAg)) AND (hepatitis B virus (HBV)) AND (hepatitis C (HCV) antibody) AND (high dose) AND (higher than 10 mg/day) AND (ketoconazole) AND (lactating) AND (live-virus vaccines) AND (localized prostate cancer) AND (low-molecular weight heparin) AND (meningeal lymphoma) AND (more than 2 years prior) AND (narrow therapeutic index) AND (need for) AND (negative) AND (normal) AND (other than) AND (oxcarbazepine) AND (phenytoin) AND (polymerase chain reaction (PCR)) AND (positive) AND (prednisone) AND (pregnant) AND (primary malignancy) AND (prostate specific antigen (PSA) levels) AND (radiation) AND (rasburicase) AND (rifampin) AND (screening) AND (select) AND (severe) AND (squamous or basal cell carcinoma of the skin) AND (statins) AND (strong CYP3A4 inducers) AND (study treatment) AND (superficial bladder carcinoma) AND (symptomatic) AND (systemic corticosteroids) AND (the first scheduled study treatment) AND (the initiation of study treatment) AND (thiazolidinediones) AND (tolbutamide) AND (total hepatitis B core antibody [HBcAb]) AND (tumor lysis syndrome (TLS)) AND (undetectable) AND (venetoclax) AND (venetoclax administration) AND (warfarin) AND (within 2 weeks) AND (within 28 days prior) AND (within 3 weeks of the first scheduled study treatment) AND (xanthine oxidase inhibitors))"}
{"candidate_id": "LLM04454", "doc_id": "NCT03381755_exc", "case_bucket": "or", "source_criterion": "taken adenosine diphosphate (ADP) receptor antagonists within 2 weeks Platelet count <100g/L; A history of bleeding tendency; Aspirin, ticagrelor or clopidogrel allergies; Severe liver injury.", "candidate_expression": "((<100g/L) AND (Aspirin) AND (Platelet count) AND (Severe) AND (adenosine diphosphate (ADP) receptor antagonists) AND (allergies) AND (bleeding tendency) AND (clopidogrel) AND (history) AND (liver injury) AND (ticagrelor) AND (within 2 weeks))"}
{"candidate_id": "LLM04455", "doc_id": "NCT02431442_inc", "case_bucket": "or", "source_criterion": "Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures. Healthy obese male and female volunteers aged 18 to 55 years, inclusive. Heterozygous subjects may be 18 to 65 years inclusive. In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities. Body Mass Index of 30-40 kg/m2, inclusive. Heterozygous subjects may have a broader BMI range; to be eligible heterozygous subjects may have a BMI 27 -55 kg/ m2, inclusive. Stable body weight during the previous 6 months, based on Investigator judgment. Blood pressure <140/90 mmHg at Screening and D-1. Measurement may be repeated within 24 hours, based on Investigator judgment. Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1. Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD. Hormonal contraception must have started at least 3 months prior to screening. A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception. Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution. Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study. Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit. Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time. Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.", "candidate_expression": "((18 to 55 years, inclusive) AND (18 to 65 years inclusive) AND (27 -55 kg/ m2, inclusive) AND (30-40 kg/m2, inclusive) AND (<140/90 mmHg) AND (A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception.) AND (Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures.) AND (BMI) AND (Blood pressure) AND (Body Mass Index) AND (Females) AND (Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1.) AND (Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD.) AND (Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study.) AND (Healthy) AND (Heterozygous) AND (Hormonal contraception) AND (In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities.) AND (Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit.) AND (Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time.) AND (Measurement may be repeated within 24 hours, based on Investigator judgment.) AND (Screening and D-1) AND (Stable) AND (Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (aged) AND (at Screening and D-1) AND (at least 3 months prior to screening) AND (at the Screening Visit and Day -1) AND (based on Investigator judgment) AND (body weight) AND (childbearing potential) AND (during the previous 6 months) AND (good general health) AND (heterozygous) AND (negative) AND (not) AND (obese) AND (pregnant) AND (screening) AND (serum pregnancy test) AND (the Screening Visit and Day -1) AND ((female) OR (male)))"}
{"candidate_id": "LLM04456", "doc_id": "NCT03296488_exc", "case_bucket": "or", "source_criterion": "Body mass index less than 18 kg/m2 or greater than 30 kg/m2. History of previous open-laparotomy. Surgery with major complication, or need blood transfusion. History of hypersensitivity or adverse reaction to local anesthetics, opioid, or any ingredient of the medications administered in this study. Severe comorbidity. Chronic preoperative opioid consumption. Pregnant or breastfeeding. Inability to use the PCA device.", "candidate_expression": "((Body mass index) AND (Inability) AND (Surgery) AND (comorbidity Severe) AND (open-laparotomy History previous) AND (opioid Chronic preoperative) AND (use the PCA) AND ((blood transfusion need) OR (major complication)) AND ((adverse reaction) OR (hypersensitivity)) AND ((ingredient of the medications administered in this study) OR (local anesthetics) OR (opioid)) AND ((Pregnant) OR (breastfeeding)) AND ((greater than 30 kg/m2) OR (less than 18 kg/m2)))"}
{"candidate_id": "LLM04457", "doc_id": "NCT02888704_inc", "case_bucket": "or", "source_criterion": "Of either gender, aged ≥19 and ≤70 years Atopic dermatitis subjects who are coincident with Hanifin and Rajka diagnosis criteria Subacute and chronic atopic subjects who have atopic dermatitis symptoms continually at least 6 months Subjects with over moderate atopic dermatitis (SCORAD score > 20) Subjects who understand and voluntarily sign an informed consent form", "candidate_expression": "((> 20) AND (Atopic dermatitis) AND (Hanifin and Rajka diagnosis criteria) AND (SCORAD score) AND (Subacute) AND (Subjects who understand and voluntarily sign an informed consent form) AND (aged) AND (atopic dermatitis) AND (chronic) AND (continually at least 6 months) AND (dermatitis symptoms) AND (over moderate) AND (≥19 and ≤70 years))"}
{"candidate_id": "LLM04458", "doc_id": "NCT02406885_exc", "case_bucket": "or", "source_criterion": "History of documented clotting/coagulation disorder History of cancer (within the last year) Any diagnosis requiring anti-coagulation History of hypersensitivity reaction to apixaban Active clinically significant bleeding Creatinine > 1.5 mg/dL Participants currently receiving any type of anticoagulation or blood thinning medications, including heparin, low molecular weight heparins, Plavix, aspirin, NSAIDS Combined P-glycoprotein and strong cytochrome P450 (CYP) 3A4 inhibitor Combined P-glycoprotein and moderate CYP 3A4 inhibitor Combined P-glycoprotein inducer and strong CYP 3A4 inducer Inducers of p-glycoprotein Strong inducers of CYP 3A4", "candidate_expression": "((CYP 3A4 inducer strong) AND (CYP 3A4 inhibitor moderate) AND (Creatinine > 1.5 mg/dL) AND (Inducers of p-glycoprotein) AND (NSAIDS) AND (P-glycoprotein inducer) AND (P-glycoprotein inhibitor) AND (Plavix) AND (anti-coagulation) AND (anticoagulation) AND (apixaban) AND (aspirin) AND (bleeding Active significant) AND (blood thinning medications) AND (cancer last year) AND (clotting disorder) AND (coagulation disorder) AND (cytochrome P450 3A4 inhibitor strong) AND (heparin) AND (hypersensitivity) AND (inducers of CYP 3A4 Strong) AND (low molecular weight heparins))"}
{"candidate_id": "LLM04459", "doc_id": "NCT02644629_inc", "case_bucket": "other", "source_criterion": "Age 18-65 Diagnosis of MDD (Major Depressive Disorder), made or affirmed by a senior psychiatrist in Shalvata MADRS score > 20 Treated with conventional anti-depressant, administered within a formal psychiatric clinic or by a certified psychiatrist.", "candidate_expression": "((18-65) AND (> 20) AND (Age) AND (MADRS score) AND (MDD) AND (Major Depressive Disorder) AND (Treated) AND (conventional anti-depressant))"}
{"candidate_id": "LLM04460", "doc_id": "NCT01639664_exc", "case_bucket": "or", "source_criterion": "Age less than 14 years Pregnancy Estimated life expectancy (due to comorbidities) less than 90 days Presence of relative or absolute contraindications to CPFA Admission from an other ICU where the patient remained for more than 24 hours Absence of informed consent", "candidate_expression": "((Absence of informed consent) AND (Admission) AND (Age less than 14 years) AND (CPFA) AND (Estimated life expectancy less than 90 days) AND (Pregnancy) AND (absolute contraindications) AND (an other ICU patient remained) AND (relative contraindications))"}
{"candidate_id": "LLM04461", "doc_id": "NCT02339974_inc", "case_bucket": "scope", "source_criterion": "Patients must be at least 21 years old. The patient must have severe, symptomatic (ACC/AHA Stage D symptoms) tricuspid regurgitation (TR) as assessed by 2D echocardiogram with evidence of peripheral and central venous congestion (specifically lower extremity edema and abdominal ascites requiring diuretics.) The patient must be evaluated by a \"heart team\" of physicians including an interventional cardiologist, cardiothoracic surgeon, heart failure specialist, and imaging specialist, and presented for review at a local multi-disciplinary conference. By consensus, the heart team must agree (and verify in the case review process) that valve implantation will likely benefit the patient. The heart team must agree that medical factors preclude operation, based on a conclusion that the probability of death or serious, irreversible morbidity exceeds the probability of meaningful improvement. Also, other factors which may increase the patients perceived surgical risk for inclusion in the trial will be clearly delineated if they are present. These include, but are not limited to the following as defined by VARC 2: Frailty, Hostile chest, porcelain aorta, IMA or other critical conduit crossing the midline or adherent to the posterior table of sternum, severe right ventricular (RV) dysfunction. The surgeons' consultation notes shall specify the medical or anatomic factors leading to that conclusion. At least one of the cardiac surgeon assessors must have interviewed and examined the patient. The study patient provides informed consent and agrees to comply with all required post-procedure follow-up visits, including annual visits up to 5 years.", "candidate_expression": "((2D echocardiogram) AND (ACC/AHA Stage D) AND (TR) AND (The study patient provides informed consent and agrees to comply with all required post-procedure follow-up visits, including annual visits up to 5 years.) AND (abdominal ascites) AND (central venous congestion) AND (diuretics) AND (lower extremity edema) AND (old at least 21 years) AND (peripheral venous congestion) AND (tricuspid regurgitation severe symptomatic))"}
{"candidate_id": "LLM04462", "doc_id": "NCT03340740_exc", "case_bucket": "other", "source_criterion": "Use of antihistamine within the past 72 hours Chronic Pulmonary Condition other than asthma Other contraindication to cetirizine Severe asthma exacerbation requiring resuscitation", "candidate_expression": "((Chronic Pulmonary Condition) AND (Severe) AND (antihistamine) AND (asthma) AND (asthma exacerbation) AND (cetirizine) AND (contraindication) AND (other) AND (resuscitation) AND (within the past 72 hours))"}
{"candidate_id": "LLM04463", "doc_id": "NCT02553226_exc", "case_bucket": "or", "source_criterion": "Unable to read and understand the Danish language or to give informed consent Cervical dilatation > 4 cm Non-cephalic presentation Multiple gestation Pathological fetal heart rate pattern (cardiotocogram, CTG) before Syntocinon® initiation Fetal weight estimation > 4500 g (clinical or ultrasonic) Subject declines participation Gestational age less than 37 completed weeks", "candidate_expression": "((> 4 cm) AND (> 4500 g) AND (Cervical dilatation) AND (Fetal weight estimation) AND (Gestational age) AND (Multiple gestation) AND (Non-cephalic presentation) AND (Pathological fetal heart rate pattern) AND (Subject declines participation) AND (Syntocinon®) AND (Syntocinon® initiation) AND (before Syntocinon® initiation) AND (less than 37 completed weeks) AND ((CTG) OR (cardiotocogram)) AND ((clinical) OR (ultrasonic)) AND ((Unable to give informed consent) OR (Unable to read) OR (Unable to understand the Danish language)))"}
{"candidate_id": "LLM04464", "doc_id": "NCT02905734_inc", "case_bucket": "other", "source_criterion": "Arrestees examined by a physician during detention in police cells aged 18 or older smoking at least 10 cigarettes per day giving written consent to participate in the study health status compatible with detention in police cells", "candidate_expression": "((18 or older) AND (Arrestees) AND (aged) AND (at least 10 cigarettes per day) AND (compatible with detention in police cells) AND (detention in police cells) AND (during detention in police cells) AND (examined by a physician) AND (giving written consent to participate in the study) AND (health status) AND (smoking))"}
{"candidate_id": "LLM04465", "doc_id": "NCT01614041_exc", "case_bucket": "or", "source_criterion": "Serious suicidal tendency The score of the sixth item of HAMA =3 The score of HAMD =21 Pregnant or lactating women History of allergic or hypersensitivity to tandospirone Serious or unstable cardiac, renal, neurologic, cerebrovascular, metabolic, or pulmonary disease Secondary anxiety disorders Drug or alcohol dependence within 1 year Patients currently taking benzodiazepine drugs Drivers and dangerous machine operators Participated in other clinical studies in the last 30 days Patients with clinically significant ECG or laboratory abnormalities Patients with a history of epilepsy Patients with abnormal TSH concentration", "candidate_expression": "((Drivers) AND (Drug dependence) AND (ECG) AND (ECG abnormalities) AND (Participated in other clinical studies the last 30 days) AND (Pregnant) AND (Secondary anxiety disorders) AND (TSH abnormal) AND (alcohol dependence) AND (allergic) AND (benzodiazepine drugs currently) AND (cardiac disease) AND (cerebrovascular disease) AND (dangerous machine operators) AND (epilepsy) AND (hypersensitivity) AND (laboratory) AND (laboratory abnormalities) AND (lactating) AND (metabolic disease) AND (neurologic disease) AND (pulmonary disease) AND (renal disease) AND (score of HAMD =21) AND (score of the sixth item of HAMA =3) AND (suicidal tendency) AND (tandospirone Serious unstable) AND (women))"}
{"candidate_id": "LLM04466", "doc_id": "NCT02019160_exc", "case_bucket": "or", "source_criterion": "Children who are uncooperative and difficult to manage, have major systemic diseases, or are on long-term medication will be excluded.", "candidate_expression": "((difficult to manage) AND (major) AND (uncooperative) AND ((medication long-term) OR (systemic diseases major)))"}
{"candidate_id": "LLM04467", "doc_id": "NCT02260206_exc", "case_bucket": "other", "source_criterion": "Hypersensitivity on Colchicine The existence of intra-cardiac thrombus on trans-esophageal echocardiography Pregnancy", "candidate_expression": "((Colchicine) AND (Hypersensitivity) AND (Pregnancy) AND (intra-cardiac thrombus) AND (trans-esophageal echocardiography))"}
{"candidate_id": "LLM04468", "doc_id": "NCT02632760_exc", "case_bucket": "or", "source_criterion": "Pregnancy Known hypersensitivity to study drug (ferric carboxymaltose or equivalent) or its excipients Known or suspected haemoglobinopathy/thalassaemia Bone marrow disease Haemochromatosis Renal dialysis Erythropoietin or IV iron in the previous 4 weeks", "candidate_expression": "((Bone marrow disease) AND (Erythropoietin) AND (Haemochromatosis) AND (IV iron in the previous 4 weeks) AND (Pregnancy) AND (Renal dialysis) AND (ferric carboxymaltose Known) AND (haemoglobinopathy suspected) AND (hypersensitivity) AND (study drug) AND (thalassaemia))"}
{"candidate_id": "LLM04469", "doc_id": "NCT01440296_inc", "case_bucket": "or", "source_criterion": "male and female patients over the age of 18 years. written informed consent (approved by the Institutional Review Board [IRB]/Independent Ethics Committee [IEC]) obtained prior to any study specific procedures. patient with mild to severe carotid artery disease", "candidate_expression": "((age) AND (carotid artery disease) AND (female) AND (male) AND (mild) AND (over 18 years) AND (severe))"}
{"candidate_id": "LLM04470", "doc_id": "NCT01602081_inc", "case_bucket": "or", "source_criterion": "Persistent primary or recurrent trans-sphincteric anal fistula", "candidate_expression": "((primary) AND (recurrent) AND (trans-sphincteric anal fistula))"}
{"candidate_id": "LLM04471", "doc_id": "NCT03171987_exc", "case_bucket": "or", "source_criterion": "Known or suspected serious spinal pathology and spinal implants Lumbar spinal surgery within the preceding six months Serious comorbidities preventing prescription of paracetamol Alternative treatment for low back pain in previous two weeks Chronic neurological lesion Chronic musculoskeletal lesion Active cancer Pregnancy Use of pain medication (except paracetamol) within 3 days Treatment site has active skin lesion or inflammation Known allergy to skin patch", "candidate_expression": "((Active) AND (Alternative) AND (Chronic musculoskeletal lesion) AND (Chronic neurological lesion) AND (Known or suspected) AND (Lumbar spinal surgery) AND (Pregnancy) AND (Serious) AND (active) AND (allergy) AND (cancer) AND (comorbidities) AND (except) AND (in previous two weeks) AND (low back pain) AND (pain medication) AND (paracetamol) AND (preventing) AND (serious) AND (skin patch) AND (treatment) AND (within 3 days) AND (within the preceding six months) AND ((spinal implants) OR (spinal pathology)) AND ((inflammation) OR (skin lesion)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM04472", "doc_id": "NCT03333655_exc", "case_bucket": "or", "source_criterion": "Participants taking CPI combination therapies with chemotherapy are not permitted. Pregnant, lactating, or intending to become pregnant during the study.", "candidate_expression": "((CPI combination therapies) AND (chemotherapy) AND (during the study) AND (intending to become) AND ((Pregnant) OR (lactating) OR (pregnant)))"}
{"candidate_id": "LLM04473", "doc_id": "NCT01932996_exc", "case_bucket": "or", "source_criterion": "Use of smoking cessation medications or interventions in last 30 days Unstable medical illness that requires immediate medical care AUDIT score of < 5 or > 26 Pregnancy or other Nicotine Replacement Therapy (NRT) contraindications Current history or in past 6 months of psychotic disorder or major depressive disorders that is not stable on treatment for past 3 months Cognitive impairment", "candidate_expression": "((AUDIT) AND (Cognitive impairment) AND (NRT) AND (Nicotine Replacement Therapy) AND (for past 3 months) AND (in last 30 days) AND (not stable) AND (past 6 months) AND (score of < 5 or > 26) AND (smoking cessation) AND ((major depressive disorders) OR (psychotic disorder)) AND ((interventions) OR (medications)) AND ((Pregnancy) OR (contraindications)))"}
{"candidate_id": "LLM04474", "doc_id": "NCT01236417_exc", "case_bucket": "or", "source_criterion": "Inability to comply with study requirements. Metastatic breast cancer. Patients with orthopedic or neuromuscular disorders that preclude participation in exercise. Rheumatoid arthritis. History of MI, angina or congestive heart failure. Pregnant or lactating females. Patients that are high risk for moderate exercise based on ACSM risk classification. Patients who exceed minimal physical activity recommendations from the US Surgeon General's Report: Accumulation of 30 minutes or more of moderate physical activity on most days of the week. Morbidly obese with BMI ≥ 40", "candidate_expression": "((ACSM risk classification) AND (BMI) AND (History) AND (Inability to comply with study requirements.) AND (Metastatic) AND (Morbidly obese) AND (Pregnant or lactating females.) AND (Rheumatoid arthritis) AND (breast cancer) AND (exceed minimal physical activity recommendations) AND (females) AND (high) AND (risk for moderate exercise) AND (≥ 40) AND ((Pregnant) OR (lactating)) AND ((disorders orthopedic) OR (neuromuscular disorders)) AND ((MI) OR (angina) OR (congestive heart failure)))"}
{"candidate_id": "LLM04475", "doc_id": "NCT01604187_exc", "case_bucket": "or", "source_criterion": "A previous history of intolerance to the study drug or related compounds and additives History of alcoholism, drug abuse, psychiatric, psychological or other emotional problems that are likely to invalidate informed consent Sleep apnoea Chronic obstructive pulmonary disease BMI = 35 or weight < 50 kg SpO2 < 90 % Concomitant drug therapy known to cause significant enzyme induction or inhibition of CYP 3A4. Pregnancy or nursing.", "candidate_expression": "((Chronic obstructive pulmonary disease) AND (Sleep apnoea) AND (SpO2 < 90 %) AND (alcoholism) AND (drug abuse) AND (drug therapy Concomitant) AND (intolerance previous history) AND ((emotional problems) OR (psychiatric problems) OR (psychological problems)) AND ((BMI = 35) OR (weight < 50 kg)) AND ((enzyme induction of CYP 3A4) OR (enzyme inhibition of CYP 3A4)) AND ((Pregnancy) OR (nursing)) AND ((related compounds) OR (study drug)))"}
```
