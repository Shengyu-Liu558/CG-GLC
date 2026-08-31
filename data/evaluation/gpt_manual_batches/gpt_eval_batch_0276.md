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
{"candidate_id": "LLM06876", "doc_id": "NCT03259243_inc", "case_bucket": "other", "source_criterion": "Patient who undergoing gynecologic laparoscopic surgery Patient who agrees to participate in this study Patient able to speak and understand Thai Patient able to complete the questionnaire", "candidate_expression": "((Patient able to speak and understand Thai) AND (Patient who agrees to participate in this study) AND (able to complete the questionnaire) AND (able to speak and understand Thai) AND (agrees to participate in this study) AND (gynecologic laparoscopic surgery))"}
{"candidate_id": "LLM06877", "doc_id": "NCT03100513_exc", "case_bucket": "or", "source_criterion": "Patients with active GIT bleeding. Patients with history of bowel obstruction, perforation. Patients with history of allergy to PEG. Treatment with rifaximin or neomycin in the previous 7 days. Patients with major psychiatric illness. Patients receiving benzodiazepines and narcotics. Patients with compromised renal. Patients receiving medications highly bound to plasma proteins eg. Warfarin. Pregnant or lactating women. Fulminant hepatic failure.", "candidate_expression": "((GIT bleeding active) AND (PEG) AND (Pregnant) AND (Warfarin) AND (allergy history) AND (benzodiazepines) AND (bowel obstruction) AND (bowel perforation) AND (compromised renal) AND (hepatic failure Fulminant) AND (lactating) AND (major psychiatric illness) AND (medications highly bound to plasma proteins) AND (narcotics) AND (neomycin) AND (rifaximin) AND (women))"}
{"candidate_id": "LLM06878", "doc_id": "NCT03084588_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure requiring dialysis Poorly controlled pulmonary disease (severe asthma or COPD) -Contraindication to regional anesthesia (recent anticoagulant use) Sleep apnea or morbid obesity with possible sleep apnea Allergy to methadone Significant preoperative pain requiring treatment with high doses of opioids (more than 6-8 Norco tablets or equivalence per day) or recent history of opioid abuse", "candidate_expression": "((Allergy) AND (COPD) AND (Contraindication) AND (Norco tablets) AND (Poorly controlled) AND (Preoperative) AND (Significant) AND (Sleep apnea) AND (anticoagulant) AND (asthma) AND (dialysis) AND (equivalence) AND (high doses) AND (history) AND (methadone) AND (morbid obesity) AND (more than 6-8 per day) AND (opioid abuse) AND (opioids) AND (possible) AND (preoperative pain) AND (pulmonary disease) AND (recent) AND (regional anesthesia) AND (renal failure) AND (requiring) AND (severe) AND (sleep apnea))"}
{"candidate_id": "LLM06879", "doc_id": "NCT03168178_inc", "case_bucket": "other", "source_criterion": "Pregnant women between 34-42 weeks gestation Singleton fetus Admitted for labor management & develops a fever of 100.4 F or greater", "candidate_expression": "((100.4 F or greater) AND (Admitted for) AND (Pregnant) AND (Singleton fetus) AND (between 34-42 weeks) AND (fever) AND (gestation) AND (labor management) AND (women))"}
{"candidate_id": "LLM06880", "doc_id": "NCT03315975_exc", "case_bucket": "or", "source_criterion": "are allergic to influenza vaccination have received influenza vaccination within the past 6 months require prednisone, methotrexate, or other immunosuppressing medications have HIV infection have a history of solid organ or bone marrow transplant require combination immunotherapy are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study", "candidate_expression": "((HIV infection) AND (allergic) AND (are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study) AND (bone marrow transplant) AND (combination immunotherapy) AND (history) AND (immunosuppressing medications) AND (influenza vaccination) AND (methotrexate) AND (other) AND (prednisone) AND (require) AND (solid organ transplant) AND (within the past 6 months))"}
{"candidate_id": "LLM06881", "doc_id": "NCT03083197_inc", "case_bucket": "or", "source_criterion": "Age = 15 years old Hospitalization with acute undifferentiated fever (temperature > 37.5 C, tympanic) =14 days or patients admitted to hospital with a history of fever = 14 days who subsequently develop fever within 24 hours of admission Clinically suspected scrub typhus: defined as acute undifferentiated fever with no clear focus of infection and negative malaria blood smear and/or negative malaria RDT. Patients may have one, none, or a combination of other clinical findings such as eschar, rash, lymphadenopathy, headache, myalgia, cough, nausea and abdominal discomfort. A positive scrub typhus RDT (Scrub Typhus IgM RDT, InBios International, Seattle, WA, USA) and/or positive PCR-based detection of O. tsutsugamushi DNA from the admission blood sample Written informed consent and/or, written informed assent as required Able to take oral medication", "candidate_expression": "((Able to take oral medication) AND (Age = 15 years old) AND (Hospitalization =14 days) AND (PCR positive O. tsutsugamushi DNA admission blood sample) AND (Scrub Typhus IgM RDT) AND (Written informed consent) AND (abdominal discomfort) AND (acute undifferentiated fever) AND (admitted to hospital) AND (cough) AND (eschar) AND (fever history = 14 days) AND (fever within 24 hours of admission) AND (headache) AND (lymphadenopathy) AND (malaria RDT negative one none a combination of) AND (malaria blood smear negative) AND (myalgia) AND (nausea) AND (oral medication) AND (rash) AND (scrub typhus) AND (scrub typhus RDT positive) AND (temperature > 37.5 C) AND (tympanic) AND (written informed assent) AND NOT (focus of infection))"}
{"candidate_id": "LLM06882", "doc_id": "NCT01581749_inc", "case_bucket": "or", "source_criterion": "histologically proven prostate adenocarcinoma within 1 year of enrollment Low risk: Gleason <or=6 & PSA <or=10 & Clinical Stage T1b-T2a,Nx or N0, Mx or M0 Intermediate risk:Gleason <or=6 & PSA<or=10 & Clinical Stage T2b OR Gleason=7 & PSA<or=10 & Clinical Stage T1b-T2b OR Gleason <or=6 & PSA > 10 & < or =20 & Clinical Stage T1b- T2b, Nx or NO, Mx or M0 ECOG Performance Status 0-1 No prior prostate radiation or other definitive therapy", "candidate_expression": "((0-1) AND (<or=10) AND (<or=6) AND (=7) AND (> 10 & < or =20) AND (Clinical Stage) AND (ECOG Performance Status) AND (Gleason) AND (Intermediate risk) AND (Low risk) AND (No) AND (PSA) AND (T1b- T2b) AND (T1b-T2a) AND (T1b-T2b) AND (T2b) AND (enrollment) AND (histologically proven) AND (prostate adenocarcinoma) AND (within 1 year of enrollment) AND ((M0) OR (Mx)) AND ((N0) OR (Nx)) AND ((NO) OR (Nx)) AND ((definitive therapy) OR (prostate radiation)))"}
{"candidate_id": "LLM06883", "doc_id": "NCT01942109_inc", "case_bucket": "other", "source_criterion": "heart failure NYHA II-IV previous treatment with diuretics age>18 years", "candidate_expression": "((NYHA II-IV) AND (age >18 years) AND (diuretics) AND (heart failure) AND (treatment previous))"}
{"candidate_id": "LLM06884", "doc_id": "NCT02464865_exc", "case_bucket": "or", "source_criterion": "pathological obesity chronic diseases e.g. cerebral palsy, metabolic disease, etc. diseases of red blood cells on medication e.g. steroid, multivitamins, thiamine-containing vitamins, diuretic drugs hemodialysis or peritoneal dialysis bariatric surgery", "candidate_expression": "((bariatric surgery) AND (chronic diseases) AND (diseases of red blood cells) AND (pathological obesity) AND ((diuretic drugs) OR (multivitamins) OR (steroid) OR (thiamine-containing vitamins)) AND ((hemodialysis) OR (peritoneal dialysis)) AND ((cerebral palsy) OR (metabolic disease)))"}
{"candidate_id": "LLM06885", "doc_id": "NCT03211741_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding (pregnancy defined as the state of a female after conception until the termination of gestation, confirmed by a positive human chorionic gonadotropin laboratory test (> 5mIU/mL) Women of child bearing potential must be practicing effective contraception implemented during the trial and for at least 28 days following the last dose of study medication Tromboembolic event (CVA or transient ischemic attack, AMI) less than 3 months prior to the intravitreal injection of bevacizumab History of hypersensitivity for bevacizumab.", "candidate_expression": "((Tromboembolic event less than 3 months prior to the intravitreal injection of bevacizumab) AND (Women) AND (bevacizumab) AND (child bearing potential) AND (contraception effective during the trial for at least 28 days following the last dose of study medication) AND (human chorionic gonadotropin laboratory test > 5mIU/mL) AND (human chorionic gonadotropin positive) AND (hypersensitivity History) AND (intravitreal injection) AND (study medication last dose) AND ((AMI) OR (CVA) OR (transient ischemic attack)) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM06886", "doc_id": "NCT02579200_inc", "case_bucket": "or", "source_criterion": "Previous diagnoses of COPD and HF under optimized clinical treatment as judged by the accompanying physician Reduced left ventricular ejection fraction (<50%) Non-reversible airway obstruction (post-bronchodilator FEV1/FVC < 0.7 and FEV1 < 80 %) Respiratory muscle weakness (Pi,max < 70cmH2O) Persistent dyspnea on daily life (Baseline Dyspnea Index focal score <or= 8).", "candidate_expression": "((COPD) AND (Dyspnea Index focal score Baseline <or= 8) AND (FEV1 post-bronchodilator < 80 %) AND (FEV1/FVC post-bronchodilator < 0.7) AND (HF) AND (Pi,max < 70cmH2O) AND (Respiratory muscle weakness) AND (airway obstruction Non-reversible) AND (clinical treatment optimized) AND (dyspnea on daily life Persistent) AND (left ventricular ejection fraction Reduced <50%))"}
{"candidate_id": "LLM06887", "doc_id": "NCT01118871_inc", "case_bucket": "or", "source_criterion": "HIV-1 infected males or females over 18 years of age signed informed consent currently receiving a stable antiretroviral regimen comprising of: two or more licensed NRTIs one licensed NNRTI or boosted protease inhibitor no previous protease inhibitor resistance documented on HIV-1 genotypic resistance testing failure of current antiretroviral regimen due to: toxicity, intolerance or virological failure if receiving an NNRTI containing regimen at screening toxicity or intolerance if receiving a boosted-protease inhibitor regimen at screening (with plasma HIV RNA < 400 copies/mL at screening) willing to modify antiretroviral therapy, in accordance with the randomisation assignment no previous exposure to etravirine subjects in good health upon medical history, physical exam, and laboratory testing in the opinion of the investigator have no serologic evidence of active HBV infection evidenced by negative hepatitis B surface antigen female subjects who are heterosexually active and of childbearing potential (i.e., not surgically sterile or at least two years post menopausal) must practice contraception as follows from screening through completion of the study: barrier contraceptives (condom, diaphragm with spermicide) IUD or Depo PLUS a barrier contraceptive female subjects of childbearing potential must have a negative pregnancy test.", "candidate_expression": "((< 400 copies/mL) AND (HBV infection) AND (HIV-1) AND (HIV-1 genotypic resistance) AND (HIV-1 genotypic resistance testing) AND (HIV-1 infected) AND (NNRTI) AND (NNRTI containing regimen) AND (NRTI) AND (age) AND (antiretroviral regimen) AND (antiretroviral therapy) AND (at least two years) AND (at screening) AND (barrier contraceptive) AND (barrier contraceptives) AND (boosted-protease inhibitor regimen) AND (childbearing potential) AND (contraception) AND (current) AND (etravirine) AND (failure of current antiretroviral regimen) AND (female) AND (female subjects who are heterosexually active and of childbearing potential (i.e., not surgically sterile or at least two years post menopausal) must practice contraception as follows from screening through completion of the study:) AND (good health) AND (hepatitis B surface antigen) AND (heterosexually active) AND (laboratory testing) AND (licensed) AND (medical history) AND (negative) AND (no) AND (not) AND (one) AND (over 18 years) AND (physical exam) AND (plasma HIV RNA) AND (pregnancy test) AND (previous) AND (protease inhibitor) AND (protease inhibitor resistance) AND (serologic evidence of active HBV infection) AND (signed informed consent) AND (surgically) AND (two or more) AND (willing) AND (with spermicide) AND ((NNRTI) OR (boosted protease inhibitor)) AND ((intolerance) OR (toxicity) OR (virological failure)) AND ((females) OR (males)) AND ((intolerance) OR (toxicity)) AND ((post menopausal) OR (surgically sterile)) AND ((condom) OR (diaphragm)) AND ((Depo) OR (IUD)))"}
{"candidate_id": "LLM06888", "doc_id": "NCT02499185_inc", "case_bucket": "other", "source_criterion": "= 18 years High risk patients: General Surgery AKI Risk Index Class III, IV or V Major abdominal surgery", "candidate_expression": "((= 18 years) AND (Class III, IV or V) AND (General Surgery AKI Risk Index) AND (High risk) AND (Major abdominal surgery))"}
{"candidate_id": "LLM06889", "doc_id": "NCT00527826_exc", "case_bucket": "or", "source_criterion": "Known other respiratory disorders or signs for other respiratory disorders (e.g. asthma, lung cancer, sarcoidosis, tuberculosis, lung fibrosis, cystic fibrosis, bronchoectasis). Known history of significant inflammatory disease, other than COPD (e.g. rheumatoid arthritis and systemic lupus erythematosus). Known to be severely alpha-1-antitrypsin deficient (PI SZ or ZZ) Having undergone lung surgery (e.g. lung resection including lung volume reduction surgery, lung transplant) or subjects scheduled for surgery. Concurrent medication from Visit 1 and for the duration of the study with any of the prohibited medications: monoamine oxidase inhibitors and tricyclic antidepressants, and ritonavir (a highly potent cytochrome P450 3A4 inhibitor). Subjects receiving chronic or prophylactic antibiotic therapy. Serious, uncontrolled disease (including serious psychological disorders) likely to interfere with the study or impact on subject safety. Have, in the opinion of the investigator, evidence of alcohol, drug or solvent abuse. History of depression. History or presence of clinically significant drug sensitivity or clinically significant allergic reaction to corticosteroids or salmeterol. Moderate or severe COPD exacerbation (requiring corticosteroids or increased dosage of corticosteroids and/or antibiotics or hospitalization) within the 4 weeks prior to Visit 1 Lower respiratory tract infection within the 4 weeks prior to Visit 1 . Pregnant or lactating female and female of childbearing potential. Subject is a participating investigator, sub-investigator, study coordinator, or other employee of a participating investigator, or is an immediate family member of the before mentioned. Subject is an employee of GlaxoSmithKline (GSK). Subject participated in an investigational drug study within 30 days prior to Visit 1", "candidate_expression": "((COPD) AND (COPD exacerbation) AND (History of) AND (Lower respiratory tract infection) AND (Moderate) AND (Pregnant) AND (Visit 1) AND (alcohol abuse) AND (allergic reaction) AND (alpha-1-antitrypsin deficient) AND (antibiotics) AND (asthma) AND (bronchoectasis) AND (childbearing potential) AND (chronic antibiotic therapy) AND (corticosteroids) AND (cystic fibrosis) AND (cytochrome P450 3A4 inhibitor) AND (depression) AND (drug abuse) AND (drug sensitivity) AND (female) AND (hospitalization) AND (increased dosage) AND (inflammatory disease) AND (lactating) AND (lung cancer) AND (lung fibrosis) AND (lung resection) AND (lung surgery) AND (lung transplant) AND (lung volume reduction surgery) AND (medication from Visit 1) AND (monoamine oxidase inhibitors) AND (other than) AND (participated in an investigational drug study) AND (prophylactic antibiotic therapy) AND (psychological disorders) AND (respiratory disorders) AND (rheumatoid arthritis) AND (ritonavir) AND (salmeterol) AND (sarcoidosis) AND (scheduled) AND (severe) AND (severely) AND (significant) AND (signs for respiratory disorders) AND (solvent abuse) AND (surgery) AND (systemic lupus erythematosus) AND (tricyclic antidepressants) AND (tuberculosis) AND (uncontrolled disease) AND (within 30 days prior to Visit 1) AND (within the 4 weeks prior to Visit 1))"}
{"candidate_id": "LLM06890", "doc_id": "NCT03407625_inc", "case_bucket": "or", "source_criterion": "37 weeks gestation or greater Living, singleton fetus No major fetal malformations Cephalic presentation No prior uterine scar Intact fetal membranes Qualifies for prostaglandin administration according to current Parkland protocol Have a cervical dilation of 2 centimeters or less, measured at the level of the internal os Have an indication for induction or attempted induction of labor according to Parkland protocol", "candidate_expression": "((Cephalic presentation) AND (Parkland protocol) AND (cervical dilation 2 centimeters or less internal os) AND (fetal membranes Intact) AND (gestation 37 weeks greater) AND (indication) AND (induction attempted) AND (induction of labor) AND (prostaglandin administration) AND (singleton fetus Living) AND NOT (major fetal malformations) AND NOT (uterine scar))"}
{"candidate_id": "LLM06891", "doc_id": "NCT01217671_inc", "case_bucket": "or", "source_criterion": "Diagnosis of emphysema confirmed by CT scan. If a report of past CT scan is not available at site documenting then a CT scan is to be performed at screening Male or female patients at least 18 years of age. Able and willing to sign an informed consent. Patient with record of congenital AAT deficiency of phenotype PiZZ (homozygote) or other rare phenotypes related to AAT deficiency and with AAT serum level ≤ 11 micromole. For patients receiving IV AAT augmentation therapy the serum AAT level threshold does not apply. FEV1/SVC <70% of predicted value post bronchodilator (SVC is slow VC) and FEV1 < 80% of predicted value post-bronchodilator History of at least two moderate or severe exacerbations that required change in treatment (antibiotics, systemic steroids, hospitalization) in the last 18 months prior to date of screening , with at least one of these occurring within the last 12 months prior to screening. Ability to comply with completion of electronic diary. Ability to self-administer inhaled AAT. No significant abnormalities in serum hematology, serum chemistry and serum inflammatory / immunogenic markers according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency. No significant abnormalities in urinalysis according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency. No significant abnormalities in ECG per investigator judgment. Negative for HBsAg and for antibodies to HCV, HIV-1. AAT deficient patients who are either naïve (not receiving IV augmentation therapy) or AAT deficient patients (receiving IV augmentation therapy), if they have been stable on regular therapy for at least 3 months prior to the screening visit and are willing to continue the same regime throughout this trial. Note that only sites in Germany can recruit patients who are currently being treated with IV AAT.Patients who stopped IV augmentation treatment 6 months prior to screening date and will not re-start this treatment for the course of the study will be considered Naïve. Non-pregnant, non-lactating female patients, whose screening pregnancy test is negative and who are using contraceptive methods deemed reliable by the investigator, or who are at least 2 years post-menopausal or surgically sterilized.", "candidate_expression": "((AAT deficient) AND (AAT serum level ≤ 11 micromole) AND (Ability to comply with completion of electronic diary.) AND (Ability to self-administer inhaled AAT.) AND (Able and willing to sign an informed consent.) AND (CT scan) AND (CT scan at screening screening) AND (ECG) AND (FEV1 < 80% of predicted value post-bronchodilator) AND (FEV1/SVC <70% of predicted value post bronchodilator) AND (HBsAg Negative) AND (HIV-1 Negative) AND (IV AAT augmentation therapy) AND (No significant abnormalities in ECG per investigator judgment.) AND (No significant abnormalities in serum hematology, serum chemistry and serum inflammatory / immunogenic markers according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency.) AND (No significant abnormalities in urinalysis according to the Principal Investigator's judgment, taking into considerations the potential effects of the AAT deficiency.) AND (age at least 18 years) AND (antibodies to HCV Negative) AND (bronchodilator) AND (comply with completion of electronic diary) AND (deemed reliable by the investigator) AND (emphysema) AND (exacerbations at least two required change in treatment) AND (female) AND (report of past CT scan) AND (self-administer inhaled AAT) AND (surgically) AND (therapy stable for at least 3 months prior to the screening) AND (treatment) AND (willing to continue throughout this trial) AND NOT (CT scan past) AND NOT (abnormalities in ECG significant) AND NOT (IV augmentation therapy) AND NOT (pregnant) AND NOT (lactating) AND ((Male) OR (female)) AND ((congenital AAT deficiency of phenotype PiZZ (homozygote)) OR (rare phenotypes related to AAT deficiency)) AND ((moderate) OR (severe)) AND ((antibiotics) OR (hospitalization) OR (systemic steroids systemic)) AND ((IV augmentation therapy) OR (naïve)) AND ((contraceptive methods deemed reliable by the investigator) OR (pregnancy test negative)) AND ((post-menopausal) OR (surgically sterilized)))"}
{"candidate_id": "LLM06892", "doc_id": "NCT02344888_inc", "case_bucket": "other", "source_criterion": "Infertile lean women with PCOS as defined by the Rotterdam criteria. CC resistance (defined as failure of ovulation after receiving 150 mg/day of CC for 5 consecutive days per cycle, for at least 3 consecutive cycles).", "candidate_expression": "((CC) AND (Infertile Rotterdam criteria) AND (PCOS) AND (resistance) AND (women))"}
{"candidate_id": "LLM06893", "doc_id": "NCT01669369_inc", "case_bucket": "or", "source_criterion": "histologically diagnosed primary classical osteosarcoma in extremities staging IIB MRI showing no skip lesion receive standard neo-adjuvant chemotherapy, adjuvant chemotherapy,and standard surgical treatment", "candidate_expression": "((MRI skip lesion staging IIB) AND (classical osteosarcoma primary in extremities) AND (histologically) AND ((adjuvant chemotherapy) OR (standard neo-adjuvant chemotherapy) OR (standard surgical treatment)))"}
{"candidate_id": "LLM06894", "doc_id": "NCT03328052_exc", "case_bucket": "or", "source_criterion": "Diagnosis of a psychotic disorder. History of, or current, open head brain trauma. Candidates with any metal, shrapnel or other similar objects in the head that could affect the QEEG History of: craniotomy, cerebral metastases, cerebrovascular accident; current diagnosis of seizure disorder, schizophrenia, schizo-affective disorder, dementia, mental retardation, or major depression with psychotic features; or use of depot neuroleptics in last 12 months. Uncontrolled thyroid disorders. Known pregnancy and/or lactation, or intent to become pregnant during this study. Chronic or acute pain requiring prescription pain medication(s) (narcotic or synthetic narcotic) Participation in any other therapeutic drug study within 60 days preceding inclusion.", "candidate_expression": "((Known pregnancy and/or lactation, or intent to become pregnant during this study.) AND (Participation in any other therapeutic drug study within 60 days preceding inclusion.) AND (QEEG) AND (affect) AND (open head brain trauma) AND (pain) AND (prescription pain medication) AND (psychotic disorder) AND (psychotic features) AND (thyroid disorders Uncontrolled) AND ((cerebral metastases) OR (cerebrovascular accident) OR (craniotomy) OR (dementia) OR (depot neuroleptics in last 12 months) OR (major depression) OR (mental retardation) OR (schizo-affective disorder) OR (schizophrenia) OR (seizure disorder)) AND ((Chronic) OR (acute)) AND ((narcotic) OR (synthetic narcotic)) AND ((History) OR (current)) AND ((metal) OR (objects in the head) OR (shrapnel)))"}
{"candidate_id": "LLM06895", "doc_id": "NCT02464813_exc", "case_bucket": "or", "source_criterion": "Other spinal pathology or other associated medical condition Major neurologic developmental delay Need for anterior surgery or for vertebral column resection. Preoperative opioid use Inability to use PCA", "candidate_expression": "((Inability to use) AND (Major neurologic developmental delay) AND (Need for) AND (PCA) AND (Preoperative) AND (opioid) AND ((associated medical condition) OR (spinal pathology)) AND ((anterior surgery) OR (vertebral column resection)))"}
{"candidate_id": "LLM06896", "doc_id": "NCT02965027_inc", "case_bucket": "or", "source_criterion": "Male and female Active-duty SMs or Veterans aged 18 or older who are in good general health. History of blast and/or impact head trauma mTBI meeting Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria, which define mTBI as an injury to the head causing at least one of the following: alteration in consciousness (for up to 24 hours after the injury), loss of consciousness 0-30 minutes, and/or post-traumatic amnesia up to 1 day post-injury. If available, the Glasgow Coma Scale score must be 13-15, and head imaging findings (if imaging was performed) must be negative. Frequent HAs that started within 3months after a head injury. The HAs either 1) must last 4 or more hours a day and reach a moderate to severe intensity at any point during the headache, or 2) may be of any severity or duration if the participant takes a triptan or ergotamine. HAs meeting these criteria must have been present on average at least 8 days per 4-week period, starting within 30 days after head injury and occurring by self-report for at least 3 months prior to the Initial Screening Visit. The 4-week HA frequency/severity criteria must be confirmed during the Preliminary Screening Period. Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study. Participants must have English fluency sufficient to complete study measures.", "candidate_expression": "((Active-duty SMs) AND (Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria meeting) AND (Glasgow Coma Scale 13-15) AND (HAs Frequent within 3months after a head injury) AND (HAs at least 8 days per 4-week period within 30 days after head injury at least 3 months prior to the Initial Screening Visit last 4 or more hours a day moderate to severe intensity) AND (Male) AND (Veterans) AND (Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study.) AND (aged 18 or older) AND (alteration in consciousness for up to 24 hours after the injury) AND (ergotamine) AND (female) AND (good general health) AND (head imaging) AND (impact head trauma History of blast) AND (loss of consciousness 0-30 minutes) AND (post-traumatic amnesia up to 1 day post-injury) AND (triptan) AND NOT (findings))"}
{"candidate_id": "LLM06897", "doc_id": "NCT02958072_exc", "case_bucket": "or", "source_criterion": "Hemoglobin concentration under 6.5 mmol/l screening HBA1c more than 108 mmol/l Non-compliant with blood-letting Clinically infected ulcer Patient planned for or has had a revascularization procedure in the affected leg within the last 8 weeks The ulcer have been treated with growth factors in the last 8 weeks History of deep venous insufficiency, chronic venous leg ulcer or stasis dermatitis Breast-feeding women or fertile women not agreeing to use an effective method of contraception Participation in another clinical ulcer-healing study within the last 4 weeks Patient has previously been randomized in this study Judgement by the investigator that the patient is not able to participate in the study", "candidate_expression": "((Breast-feeding) AND (HBA1c more than 108 mmol/l) AND (Hemoglobin concentration under 6.5 mmol/l) AND (Judgement by the investigator that the patient is not able to participate in the study) AND (Non-compliant) AND (blood-letting) AND (fertile) AND (growth factors) AND (infected ulcer) AND (revascularization procedure affected leg within the last 8 weeks) AND (treated in the last 8 weeks) AND (ulcer) AND ((has had) OR (planned)) AND ((chronic venous leg ulcer) OR (deep venous insufficiency) OR (stasis dermatitis)) AND ((women) OR (women agreeing to use an effective method of contraception)))"}
{"candidate_id": "LLM06898", "doc_id": "NCT02957305_inc", "case_bucket": "other", "source_criterion": "All patients admitted at the Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre scheduled for uterine evacuation with <12 weeks of gestation.", "candidate_expression": "((Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre) AND (gestation <12 weeks) AND (uterine evacuation))"}
{"candidate_id": "LLM06899", "doc_id": "NCT00344318_exc", "case_bucket": "or", "source_criterion": "Use of any investigational or non-registered product (drug or vaccine) other than the study vaccine(s) within 30 days preceding the first dose of study vaccine, or planned use during the study period Chronic administration (defined as more than 14 days) of immunosuppressants or other immune-modifying drugs within six months prior to the first vaccine dose. Planned administration/ administration of a vaccine not foreseen by the study protocol during the period starting one month before each dose of vaccine(s) and ending 7 days after dose 1 and dose 2 or 1 month after dose 3. Previous vaccination against diphtheria, tetanus, pertussis, polio, hepatitis B, Haemophilus influenzae type b, and/or S. pneumoniae with the exception of vaccines where the first dose can be given within the first two weeks of life according to the national recommendations History of or intercurrent diphtheria, tetanus, pertussis, hepatitis B, polio, and Haemophilus influenzae type b diseases. History of allergic disease or reactions likely to be exacerbated by any component of the vaccines. History of seizures (this criterion does not apply to subjects who have had a single, uncomplicated febrile convulsion in the past) or neurological disease. Acute disease at the time of enrolment Any confirmed or suspected immunosuppressive or immunodeficient condition based on medical history and physical A family history of congenital or hereditary immunodeficiency. Major congenital defects or serious chronic illness. Administration of immunoglobulins and/or any blood products since birth or planned administration during the active phase of the study.", "candidate_expression": "((Acute disease at the time of enrolment) AND (History) AND (Planned) AND (congenital immunodeficiency) AND (dose 3) AND (family history) AND (hereditary immunodeficiency) AND (planned use during the study period more than 14 days) AND (vaccination) AND (vaccine not foreseen by the study protocol period starting one month before each dose of vaccine(s)) AND NOT (vaccines first dose can be given) AND NOT (febrile convulsion single uncomplicated) AND ((immunosuppressants) OR (other immune-modifying drugs)) AND ((non-registered product any other than the study vaccine(s)) OR (product any investigational other than the study vaccine(s))) AND ((1 month after dose 3 dose 3) OR (ending 7 days after dose 1 and dose 2 dose 1 and dose 2)) AND ((dose 1) OR (dose 2)) AND ((drug) OR (vaccine)) AND ((Haemophilus influenzae type b) OR (S. pneumoniae) OR (diphtheria) OR (hepatitis B) OR (pertussis) OR (polio) OR (tetanus)) AND ((Haemophilus influenzae type b) OR (diphtheria) OR (hepatitis B) OR (pertussis) OR (polio) OR (tetanus)) AND ((allergic disease) OR (reactions allergic)) AND ((neurological disease) OR (seizures)) AND ((immunodeficient condition) OR (immunosuppressive condition)) AND ((Major congenital defects) OR (serious chronic illness)) AND ((any blood products) OR (immunoglobulins)) AND ((planned during the active phase of the study) OR (since birth birth)))"}
{"candidate_id": "LLM06900", "doc_id": "NCT02969876_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
