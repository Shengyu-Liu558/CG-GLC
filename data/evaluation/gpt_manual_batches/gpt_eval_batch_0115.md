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
{"candidate_id": "LLM02851", "doc_id": "NCT02015494_exc", "case_bucket": "or", "source_criterion": "Use of any investigational or non-registered drug or vaccine product within 30 days preceding the administration of the study vaccine or planned use within the first six weeks of the study period Has received any licensed or other investigational influenza vaccine within 3 months prior to enrollment in this study or expected receipt of any influenza vaccination before the Day 21 blood collection History of excessive alcohol use, drug abuse or significant psychiatric illness Tobacco use within 3 months of enrollment and throughout first 6 months of the study Has a chronic illness (e.g., liver or kidney disease), receiving a concomitant therapy or have any other condition that could interfere with the subject's participation in the study or in the interpretation of the study results Clinically significant abnormal liver function tests at screening Positive serology for HBsAg, HCV or HIV antibodies Pregnant or lactating female Having cancer or have received treatment for cancer within three years (persons with a history of cancer who are disease-free without treatment for three years or more are eligible), excluding minor skin cancers, which are allowed unless located at the vaccination site Persons with impaired immune responsiveness (of any cause), including diabetes mellitus and autoimmune disorders Persons presently receiving or having a recent history of receiving (within the past six months) any medication or therapeutic modality that affects the immune system such as allergy shots, immune globulin, interferon, immunomodulators, radiation therapy, cytotoxic drugs or drugs known to be frequently associated with significant major organ toxicity, or systemic corticosteroids (oral or injectable). Inhaled and topical corticosteroids are allowed. Persons with a history of severe allergic reaction after previous vaccinations or hypersensitivity to any seasonal influenza vaccine component Persons with a history of Guillain-Barré Syndrome Receipt of blood or blood products 8 weeks prior to vaccination or planned administration during the three week study period following vaccination Donation of blood or blood products within 8 weeks prior to vaccination or during the three week study period following An oral temperature >100.4° or acute disease within 72 hours prior to vaccination, defined as the presence of a moderate or severe illness (as determined by the investigator through medical history and physical examination; for example, those requiring an absence from work) with or without fever. Body Mass Index >29.9 Any disorder of coagulation A clinical diagnosis of influenza within the previous 12 months Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study", "candidate_expression": "((8 weeks prior to vaccination) AND (>100.4°) AND (>29.9) AND (Any other condition or circumstance which, in the opinion of the Principal Investigator, poses an unacceptable risk for participation in the study) AND (Body Mass Index) AND (Clinically significant) AND (Day 21) AND (Donation of blood) AND (Donation of blood products) AND (Guillain-Barré Syndrome) AND (HBsAg antibodies) AND (HCV antibodies) AND (HIV antibodies) AND (History) AND (Positive) AND (Pregnant) AND (Receipt of blood) AND (Receipt of blood products) AND (Tobacco use) AND (abnormal) AND (acute disease) AND (affects the immune system) AND (after previous vaccinations) AND (allergic reaction) AND (allergy shots) AND (any influenza vaccination) AND (any medication) AND (any other condition) AND (at screening) AND (autoimmune disorders) AND (before the Day 21) AND (cancer) AND (chronic illness) AND (concomitant) AND (could interfere with the subject's participation in the study) AND (cytotoxic drugs) AND (diabetes mellitus) AND (disease-free) AND (disorder of coagulation) AND (drug) AND (drug abuse) AND (drugs known to be frequently associated with significant major organ toxicity) AND (during the three week study period) AND (during the three week study period following vaccination) AND (enrollment) AND (enrollment in this study) AND (excessive alcohol use) AND (expected receipt) AND (female) AND (for three years or more) AND (history) AND (hypersensitivity to any seasonal influenza vaccine component) AND (immune globulin) AND (immunomodulators) AND (impaired immune responsiveness) AND (influenza) AND (influenza vaccine) AND (injectable) AND (interferon) AND (investigational) AND (kidney disease) AND (known to be frequently associated with significant major organ toxicity) AND (lactating) AND (licensed) AND (liver disease) AND (liver function tests) AND (moderate illness) AND (non-registered) AND (oral) AND (oral temperature) AND (other investigational) AND (planned administration) AND (planned use) AND (previous vaccinations) AND (psychiatric illness) AND (radiation therapy) AND (screening) AND (seasonal influenza vaccine component) AND (severe) AND (severe illness) AND (significant) AND (systemic corticosteroids) AND (the administration of the study vaccine) AND (the study) AND (the study period) AND (the three week study period) AND (therapeutic modality) AND (therapy) AND (three week study period following vaccination) AND (throughout first 6 months of the study) AND (treatment) AND (treatment for cancer) AND (vaccination) AND (vaccine product) AND (within 3 months of enrollment) AND (within 3 months prior to enrollment in this study) AND (within 30 days preceding the administration of the study vaccine) AND (within 72 hours prior to vaccination) AND (within 8 weeks prior to vaccination) AND (within the first six weeks of the study period) AND (within the past six months) AND (within the previous 12 months) AND (within three years) AND (without))"}
{"candidate_id": "LLM02852", "doc_id": "NCT01728194_inc", "case_bucket": "or", "source_criterion": "Age: 60-85 years, right-handed; Diagnosis: Major depression, unipolar (by Structured Clinical Interview for Diagnostic and Statistical Manual (DSM)IV (SCID-R) and DSM-IV criteria); Age of onset of first episode = 50 years with up to three depressive episodes; Severity of depression: A 24-Item Hamilton Depression Rating Scale (HDRS) = 20.", "candidate_expression": "((24-Item Hamilton Depression Rating Scale) AND (60-85 years) AND (= 20) AND (= 50 years) AND (Age) AND (DSM-IV criteria)) AND (HDRS) AND (IV Structured Clinical Interview for Diagnostic and Statistical Manual) AND (Major depression) AND (depression) AND (depressive episodes) AND (onset of first episode) AND (right-handed) AND (three) AND (unipolar) AND ((DSM) OR (SCID)))"}
{"candidate_id": "LLM02853", "doc_id": "NCT03044561_inc", "case_bucket": "other", "source_criterion": "(1) cases of infertility, older than 20 years of age and not older than 40 years. (2) Body mass index (BMI):20-29. (3) women have experienced two or more implantation failure attributed to inadequate endometrial development.", "candidate_expression": "((BMI) AND (Body mass index 20-29) AND (age older than 20 years not older than 40 years) AND (implantation two or more failure) AND (inadequate endometrial development attributed to) AND (infertility) AND (women))"}
{"candidate_id": "LLM02854", "doc_id": "NCT02584140_inc", "case_bucket": "or", "source_criterion": "Female at birth and identifies as female gender Age 18 years or older Able to understand and provide consent in English or Spanish HIV negative by 4th generation test (Ag/Ab test) or combination of enzymeimmunoassay (EIA) and HIV RNA Creatinine clearance = 60 ml/min (via Cockcroft-Gault formula) Condomless sex in the last 3 months with one or more male partners of unknown HIV status known to be at substantial risk of HIV infection (IDU, bisexual, sex for goods, recently incarcerated, from a country with HIV prevalence >1%, interpersonal Partner Violence); STI (rectal or vaginal gonorrhea or syphilis) diagnosis during the last 6 months. Previous post-exposure prophylaxis (PEP) use during the last 12 months. Has at least one HIV-infected sexual partner for =4 weeks. Sex for exchange of money, goods or services", "candidate_expression": "((Able to understand and provide consent in English or Spanish) AND (Ag/Ab test) AND (Age 18 years or older) AND (Cockcroft-Gault formula) AND (Condomless sex in the last 3 months) AND (Creatinine clearance = 60 ml/min) AND (EIA) AND (Female at birth) AND (HIV 4th generation test negative) AND (HIV RNA) AND (HIV infection) AND (HIV-infected) AND (IDU) AND (PEP) AND (STI) AND (Sex for exchange of money, goods or services) AND (bisexual) AND (enzymeimmunoassay) AND (from a country with HIV prevalence >1%) AND (gender female) AND (interpersonal Partner Violence) AND (male partners one or more) AND (post-exposure prophylaxis use during the last 12 months) AND (recently incarcerated) AND (rectal gonorrhea) AND (sex for goods) AND (sexual partner at least one =4 weeks) AND (syphilis during the last 6 months) AND (unknown HIV status substantial risk of HIV infection) AND (vaginal gonorrhea))"}
{"candidate_id": "LLM02855", "doc_id": "NCT02445339_inc", "case_bucket": "or", "source_criterion": "English or Spanish speaking* Emergency Department patient Aged 18-80 Have had >4 emergency department visits within 12 months for 2 consecutive 12-month periods. Period of time can be extended by up to 6 months if incarcerated or institutionalized for ≥ 6 months. Meet Diagnostic and Statistical Manual version IV (DSM-IV) criteria for alcohol dependence or & DSM-V criteria for alcohol use disorder, severe. Have ≥2 days/week of heavy drinking (>4 drinks/day) Capable of giving informed consent.", "candidate_expression": "((Aged 18-80) AND (Emergency Department) AND (English speaking) AND (Spanish speaking) AND (alcohol dependence Diagnostic and Statistical Manual version IV (DSM-IV) criteria) AND (alcohol use disorder DSM-V criteria severe) AND (drinks/day >4) AND (emergency department visits >4 within 12 months 12-month periods) AND (heavy drinking ≥2 days/week) AND (incarcerated) AND (informed consent Capable of giving) AND (institutionalized))"}
{"candidate_id": "LLM02856", "doc_id": "NCT02631512_inc", "case_bucket": "or", "source_criterion": "Type I or II diabetes mellitus. Target ulcer area between 0.5 and 5 sqcm, and more than 4 weeks old. Ankle-brachial pressure index above 0.7.", "candidate_expression": "((Ankle-brachial pressure index above 0.7) AND (Target ulcer area between 0.5 and 5 sqcm more than 4 weeks old) AND ((Type I diabetes mellitus) OR (Type II diabetes mellitus)))"}
{"candidate_id": "LLM02857", "doc_id": "NCT02601157_exc", "case_bucket": "or", "source_criterion": "1. High risk profiles for ischemic adverse events such as A. ST-segment elevation myocardial infarction (STEMI) B. Patients with cardiogenic shock or concomitant severe decompensated heart failure C. Myocardial infarction or stent thrombosis in spite of the maintenance of antiplatelet therapy D. Restenosis in stented segments or previous sites of balloon angioplasty 2. Patients who cannot follow allocated DAPT schedule due to the planned surgery or elective procedure within 3 months after the stenting 3. Recent history of major surgery or evident events of gastrointestinal bleeding within 1 month from the procedure 4. Patients on anticoagulation therapy with warfarin or other anticoagulants 5. Life expectancy less than 1 year (such as malignancies or other chronic systemic diseases) 6. Pregnant women 7. Past history of allergy or other contraindications for the following medications/materials: aspirin, clopidogrel, heparin, cobalt chromium, sirolimus", "candidate_expression": "((High risk profiles) AND (Life expectancy less than 1 year) AND (Myocardial infarction) AND (Pregnant) AND (Restenosis) AND (ST-segment elevation myocardial infarction (STEMI)) AND (allergy) AND (anticoagulants other) AND (anticoagulation therapy) AND (antiplatelet therapy) AND (aspirin) AND (cannot follow allocated DAPT schedule) AND (cardiogenic shock) AND (chronic systemic diseases other) AND (clopidogrel) AND (cobalt chromium) AND (contraindications other) AND (events of gastrointestinal bleeding) AND (heart failure severe decompensated) AND (heparin) AND (ischemic adverse events) AND (major surgery) AND (malignancies) AND (procedure elective) AND (sirolimus) AND (stent thrombosis) AND (surgery) AND (warfarin) AND (women))"}
{"candidate_id": "LLM02858", "doc_id": "NCT02807857_inc", "case_bucket": "other", "source_criterion": "Willing and able to provide written informed consent and accept study procedures and time schedule. Age = 18 years. Patients suffering from chronic heart failure (the heart failure diagnosis must have been made or confirmed by a cardiologist and/or hospital physician at any time in the patient's medical history). Patients with reduced ejection fraction (= 40%) as confirmed at any time point in the patient's medical history.", "candidate_expression": "((= 18 years) AND (= 40%) AND (Age) AND (Willing and able to provide written informed consent and accept study procedures and time schedule.) AND (chronic heart failure) AND (ejection fraction))"}
{"candidate_id": "LLM02859", "doc_id": "NCT02202369_exc", "case_bucket": "or", "source_criterion": "Patients with liver disease (documented liver function test abnormality) Patients with renal disease (documented glomerular filtration rate < 60mL/min/1.73m2) Patients with a baseline (pre-operative) opioid use greater than 30 mg of morphine equivalents/day. Patients with active alcohol dependence Patients with active illicit drug dependence Patients < 18 years of age and >70 years of age Patients allergic to any medication given in either arm (list medications) Patients who have a seizure disorder", "candidate_expression": "((alcohol dependence) AND (allergic) AND (glomerular filtration rate < 60mL/min/1.73m2) AND (illicit drug dependence) AND (liver disease) AND (liver function test abnormality) AND (medication) AND (opioid baseline greater than 30 mg of morphine equivalents/day pre-operative) AND (renal disease) AND (seizure disorder) AND ((age < 18 years) OR (age >70 years)))"}
{"candidate_id": "LLM02860", "doc_id": "NCT02946918_inc", "case_bucket": "or", "source_criterion": "Age > 18 years Presumed AJCC (American Joint Committee on Cancer) tumor Stage I or II Planned total or near-total thyroidectomy Planned goal TSH suppression 0.1-0.5 mU/L for at least 18 weeks postoperatively Normal serum TSH within 12 months preceding surgery", "candidate_expression": "((AJCC tumor Stage I I II total) AND (Age > 18 years) AND (American Joint Committee on Cancer) AND (TSH suppression 0.1-0.5 mU/L at least 18 weeks postoperatively) AND (serum TSH Normal within 12 months preceding surgery) AND (thyroidectomy near-total))"}
{"candidate_id": "LLM02861", "doc_id": "NCT02101554_inc", "case_bucket": "or", "source_criterion": "Children 7-17 with moderate to severe pain requiring around the clock treatment with an opioid analgesic. Be an experienced opioid user, defined as any subject treated with opioid therapy, equivalent or equal to >20 mg per day of morphine, for a period of 3 consecutive days immediately prior to first day of dosing.", "candidate_expression": "((Children moderate) AND (around the clock treatment) AND (morphine >20 mg per day) AND (morphine equivalent >20 mg per day) AND (opioid analgesic) AND (opioid therapy 3 consecutive days immediately prior to first day of dosing) AND (pain severe))"}
{"candidate_id": "LLM02862", "doc_id": "NCT01929434_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of cerebral palsy. Patients' curator must be able to give voluntary consent.", "candidate_expression": "((Patients' curator must be able to give voluntary consent) AND (cerebral palsy))"}
{"candidate_id": "LLM02863", "doc_id": "NCT02704234_inc", "case_bucket": "other", "source_criterion": "women previously diagnosed with generalized vulvodynia women previously diagnosed with localized vestibulodynia,", "candidate_expression": "((generalized vulvodynia) AND (localized vestibulodynia) AND (women))"}
{"candidate_id": "LLM02864", "doc_id": "NCT02281643_inc", "case_bucket": "other", "source_criterion": "M. perstans mg-positive status Good general health without any clinical condition requiring long-term medication. Normal renal and hepatic laboratory profiles", "candidate_expression": "((Good general health) AND (M. perstans mg) AND (Normal) AND (clinical condition requiring long-term medication) AND (hepatic laboratory profile) AND (long-term medication) AND (positive) AND (renal laboratory profile) AND (requiring long-term medication) AND (without))"}
{"candidate_id": "LLM02865", "doc_id": "NCT02531971_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session Smokers (current use or use over the previous 2 months of nicotine-containing substances, including tobacco products (e.g. cigarettes, cigars, chewing tobacco, gum, patch or electronic cigarettes) Participation in any ongoing investigational drug trial/study or clinical drug trial/study History of chronic obstructive pulmonary disease or cor pulmonale, or substantially decreased respiratory reserve, hypoxia, hypercapnia or pre-existing respiratory depression Active positive Hepatitis B, C and HIV serologies Positive urine drug screening test Use of any prescription medication during the session 0 to 30 days or over-the counter medication e.g. antihistamines or topical corticosteroids (vitamin, herbal supplements and birth control medications not included) during the session 0 to 3 days before entry to the study Use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator with 72 hours prior to dosing (e.g. antihistamines, systemic or topical corticosteroids (within 3 weeks prior to dosing), cyclosporine, tacrolimus, cytotoxic drugs, immune globulin, Bacillus Calmette-Guerin (BCG), monoclonal antibodies, radiation therapy) Use of monoamine oxidase inhibitors 21 days prior to study Current use of mixed agonist/antagonist (such as pentazocine, nalbuphine or butorphanol) and partial agonist (buprenorphine) analgesics Current use of anticholinergics or other medications with anticholinergic activity Consumption of beverages containing alcohol, grapefruit juice, Seville oranges, or quinine (e.g. tonic water) or foods containing poppy seeds in the last 72 hours. Donation or loss of greater than one pint of blood within 60 days of entry to the study Any prior serious adverse reaction or hypersensitivity to fentanyl, morphine, codeine, hydrocodone, hydromorphone, oxycodone, oxymorphone, naltrexone or naloxone or any of the inactive ingredients in the TDDS (polyester/ethyl vinyl acetate, polyacrylate adhesive, silicone adhesive, dimethicone NF, or polyolefin) Have a diagnosis of schizophrenia or other major psychiatric diagnosis or mental illness (e.g. major depression) Medical history of personal drug or alcohol addiction or abuse Any condition that would, in the opinion of the MAI, place the subject at an unacceptable risk of injury or render the subject unable to meet the requirements of the protocol Inability to communicate or cooperate with the investigators Subject has an obvious difference in skin color between arms or the presence of a skin condition, excessive hair at the application site (upper arm), sunburn, raised moles and scars, open sore, scar tissue, tattoo, or coloration that would interfere with placement of test articles, skin assessment, or reactions to drug Failure to pass opioid dependence challenge test on the first day study day of any study session (i.e., before taking the first dose of naltrexone hydrochloride). Each subject will be injected subcutaneously with naloxone hydrochloride (0.8 mg injection) and will be observed for 45 minutes for signs and symptoms of opioid withdrawal. Within 4 weeks prior to dosing, use of medications or treatments that would significantly influence or exaggerate responses to the test product or that would alter inflammatory or immune response to the product or agents deemed to be immunosuppressive as determined by physician investigator", "candidate_expression": "((21 days prior to study) AND (Inability to communicate or cooperate with the investigators) AND (Participation in any ongoing investigational drug trial/study or clinical drug trial/study) AND (Positive) AND (Smokers) AND (Women who are pregnant, lactating or breast feeding or have a positive serum pregnancy test at enrollment or positive urine pregnancy test on the morning of the first day of any study session) AND (anticholinergics) AND (hypersensitivity) AND (major depression) AND (monoamine oxidase inhibitors) AND (positive) AND (study) AND (urine drug screening test) AND ((HIV serologies) OR (Hepatitis B serologies) OR (Hepatitis C serologies)) AND ((buprenorphine) OR (butorphanol) OR (nalbuphine) OR (pentazocine)) AND ((TDDS) OR (codeine) OR (fentanyl) OR (hydrocodone) OR (hydromorphone) OR (morphine) OR (naloxone) OR (naltrexone) OR (oxycodone) OR (oxymorphone)) AND ((chronic obstructive pulmonary disease) OR (cor pulmonale,) OR (decreased respiratory reserve) OR (hypercapnia) OR (hypoxia) OR (respiratory depression)) AND ((dimethicone NF) OR (polyacrylate adhesive) OR (polyester/ethyl vinyl acetate) OR (polyolefin) OR (silicone adhesive)) AND ((major psychiatric diagnosis) OR (mental illness) OR (schizophrenia)) AND ((abuse) OR (addiction)) AND ((alcohol) OR (drug)))"}
{"candidate_id": "LLM02866", "doc_id": "NCT03619707_inc", "case_bucket": "or", "source_criterion": "Normal uterine cavity Normal Hormonal investigation: TSH,PRL,FBS Frozen embryo transfer cycles: at least 2 embryos Primary or secondary infertility: tubal occlusion, male factor, unexplained, endometriosis, ovarian factors… Body mass index (BMI) =18 to =30 kg/m2", "candidate_expression": "((=18 to =30 kg/m2) AND (BMI) AND (Body mass index) AND (FBS) AND (Frozen embryo transfer cycles) AND (Hormonal investigation) AND (Normal) AND (PRL) AND (Primary infertility) AND (TSH) AND (at least 2) AND (embryos) AND (endometriosis) AND (male factor) AND (ovarian factors) AND (secondary infertility) AND (tubal occlusion) AND (unexplained factors) AND (uterine cavity))"}
{"candidate_id": "LLM02867", "doc_id": "NCT02231892_exc", "case_bucket": "or", "source_criterion": "1. Personal history of stroke, brain lesions, previous neurosurgery, any personal history of seizure or fainting episode of unknown cause, or head trauma resulting in loss of consciousness, lasting over 30 minutes or with sequela lasting longer than two days. Justification: Stroke or head trauma can lower the seizure threshold, and are therefore contra-indications for TMS. Fainting episodes or syncope of unknown cause could indicate an undiagnosed condition associated with seizures. Screening tool: TMS adult safety questionnaire, Medical History. 2. First-degree family history of any neurological disorder with a potentially hereditary basis, including migraines, epilepsy, or multiple sclerosis. 1. Justification: Neurological disorders can lower the seizure threshold, and are therefore contra-indications for TMS. First-degree family history of certain neurological disorders with a hereditary component increases the risk of the subject having an undiagnosed condition that is associated with lowered seizure threshold. 2. Screening tool: TMS adult safety screening, Medical History. 3. Cardiac pacemakers, neural stimulators, implantable defibrillator, implanted medication pumps, intracardiac lines, or acute, unstable cardiac disease, with intracranial implants (e.g. aneurysm clips, shunts, stimulators, cochlear implants, or electrodes) or any other metal object within or near the head that precludes MRI scanning. 1. Justification: Any metal around the head is a contraindication for both MRI and TMS, as both methods involve exposure to a relatively strong magnetic field. 2. Screening tool: TMS adult safety screening, MRI safety screening, Medical History. 4. Noise-induced hearing loss or tinnitus. 1. Justification: individuals with noise-induced hearing problems may be particularly vulnerable to the acoustic noise generated by TMS and MRI equipment. 2. Screening tools: TMS adult safety screening. 5. Current use (any use in the past 4 weeks, chronic use within 6 past six months) of any investigational drug or of any medications with psychotropic, anti or pro-convulsive action. 1. Justification: The use of certain medications or drugs can lower seizure threshold and is therefore contra-indicated for TMS. 2. Screening tools: MRI safety screening questionnaire, Medical history, Medical Assessments: Urine toxicology analyzes for presence of a broad range of prescription and nonprescription drugs. 6. Lifetime history of major depressive disorder, schizophrenia, bipolar disorder, mania, or hypomania. 1. Justification: The population of interest here is a healthy control population with no psychiatric disorders. In subjects with depression, bipolar disorder, mania or hypomania, there is a small chance that TMS can trigger (hypo)manic symptoms. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counsellor. 7. Meet current DSM V criteria for moderate to severe substance use disorder (excluding nicotine), smoke daily, or urine toxicology positive for any illicit substance inconsistent with history given. 1. Justification: The population of interest here is a healthy control population with no substance use disorder. Current use of illicit substances could impact on seizure threshold and is therefore contra-indicated for TMS. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counsellor, Drug Use Survey (DUS), Substance Use Disorder Evaluation, Medical Assessments: urine qualitative drug screen is performed for methadone, benzodiazepines, cocaine, amphetamine/methamphetamine, opiates, barbiturates, and tetrahydrocannabinol. 8. Have met DSM V criteria for moderate to severe substance use disorder (excluding nicotine, alcohol and cannabis) in the past, or have met DSM V criteria for moderate to severe substance use disorder for cannabis or alcohol in the past 5 years. 1. Justification: the population of interest here is a healthy control population with no present or past substance use disorder. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counselor. Drug Use Survey (DUS), Substance Use Disorder Evaluation. 9. History of myocardial infarction, angina, congestive heart failure, cardiomyopathy, stroke or transient ischemic attack, or any heart condition currently under medical care. 1. Justifications: the risk of TMS for individuals with a heart condition is unknown. 2. Screening tool: physical assessment (EKG), medical history. 10. Pregnant women or women with reproductive potential who are sexually active and not using an acceptable form of contraception. 1. Justification: it is unknown whether TMS poses a risk to fetuses. 2. Screening tool: Medical assessments (urine pregnancy test) at the beginning of each visit that involves TMS or MRI. 11. History of learning disability or current ADHD 1. Justification: Subjects should be able to perform cognitive tasks to a high degree of accuracy, both in the MRI scanner and outside the scanner. Subjects with ADHD/LD may engage different neural circuitry even if they can perform the tasks. 2. Screening tool: Wechsler Abbreviated Scale of Intelligence, Medical history, Adult ADHD Self-Report Scale. 12. Participation in an rTMS session less than two weeks ago. 1. Justification: in order to limit exposure to TMS, we will not enroll subjects who have received TMS less than two weeks ago. 2. Screening tool: TMS safety screening questionnaire.", "candidate_expression": "((ADHD) AND (Adult ADHD Self-Report Scale) AND (DSM V criteria Meet) AND (DSM V criteria met) AND (Drug Use Survey (DUS)) AND (LD) AND (MRI) AND (MRI safety screening) AND (MRI safety screening questionnaire) AND (Medical History) AND (Medical assessments at the beginning of each visit) AND (Medical history) AND (Potential diagnoses will be further evaluated by a counselor.) AND (Pregnant) AND (SCID Screen Patient Questionnaire) AND (Screening) AND (Substance Use Disorder Evaluation) AND (TMS adult safety questionnaire) AND (TMS adult safety screening) AND (TMS adult safety screening Current use) AND (TMS safety screening questionnaire) AND (Urine toxicology analyzes) AND (Wechsler Abbreviated Scale of Intelligence) AND (acceptable form of) AND (drugs) AND (heart condition under medical care) AND (illicit substance inconsistent with history) AND (inconsistent with history) AND (intracranial implants) AND (lasting longer than two days) AND (neurological disorder potentially hereditary basis) AND (rTMS session less than two weeks ago) AND (reproductive potential) AND (safety screening questionnaire) AND (sexually active) AND (substance use disorder moderate to severe) AND (substance use disorder moderate to severe in the past 5 years) AND (transient ischemic attack) AND (urine pregnancy test) AND (women) AND NOT (nicotine) AND NOT (alcohol) AND NOT (cannabis) AND NOT (MRI scanning) AND NOT (contraception acceptable form of) AND ((smoke daily) OR (urine toxicology positive)) AND ((DSM V criteria met) OR (substance use disorder moderate to severe in the past)) AND ((alcohol) OR (cannabis)) AND ((brain lesions) OR (neurosurgery previous) OR (stroke)) AND ((fainting episode unknown cause) OR (head trauma resulting in loss of consciousness) OR (seizure)) AND ((lasting over 30 minutes) OR (sequela)) AND ((epilepsy) OR (migraines) OR (multiple sclerosis)) AND ((Cardiac pacemakers) OR (cardiac disease acute unstable) OR (implantable defibrillator) OR (implanted medication pumps) OR (intracardiac lines) OR (metal object within or near the head precludes MRI scanning) OR (neural stimulators)) AND ((aneurysm clips) OR (cochlear implants) OR (electrodes) OR (shunts) OR (stimulators)) AND ((Noise-induced hearing loss) OR (tinnitus)) AND ((any use in the past 4 weeks) OR (chronic use within 6 past six months)) AND ((investigational drug) OR (medications)) AND ((pro-convulsive action) OR (psychotropic action)) AND ((nonprescription) OR (prescription)) AND ((bipolar disorder) OR (hypomania) OR (major depressive disorder) OR (mania) OR (schizophrenia)) AND ((ADHD current) OR (learning disability History)) AND ((MRI) OR (TMS)) AND ((angina) OR (cardiomyopathy) OR (congestive heart failure) OR (myocardial infarction) OR (stroke)))"}
{"candidate_id": "LLM02868", "doc_id": "NCT02137538_exc", "case_bucket": "other", "source_criterion": "Bone age reading more than 14.0 years Follicle stimulating hormone > 20 IU/L", "candidate_expression": "((Bone age more than 14.0 years) AND (Follicle stimulating hormone > 20 IU/L))"}
{"candidate_id": "LLM02869", "doc_id": "NCT03132259_exc", "case_bucket": "or", "source_criterion": "GCS less than 15 Preoperative Heart Rate less than 50 beat/min No Beta-Blockers Pregnant patients Take any Alpha-Methyldopa, Clonodine, Other Alpha-2 Adrenergic Agonist Hemodynamic unstable Systolic BP more than 160mmHg CAD Renal insuffuciency Allergy in dexmedethomidine and opioid BMI more than 30 Denied consent", "candidate_expression": "((Allergy) AND (BMI more than 30) AND (CAD) AND (Denied consent) AND (GCS less than 15) AND (Hemodynamic unstable) AND (Pregnant) AND (Preoperative Heart Rate less than 50 beat/min) AND (Renal insuffuciency) AND (Systolic BP more than 160mmHg) AND NOT (Beta-Blockers) AND ((Alpha-2 Adrenergic Agonist Other) OR (Alpha-Methyldopa) OR (Clonodine)) AND ((dexmedethomidine) OR (opioid)))"}
{"candidate_id": "LLM02870", "doc_id": "NCT01680081_inc", "case_bucket": "or", "source_criterion": "Men and women patients, with age ranging 40-80. Suspected coronary artery disease who are supposed to undergo invasive coronary angiography with appropriate clinical indications Patients who are willing to sign the informed consent form", "candidate_expression": "((Patients who are willing to sign the informed consent form) AND (Suspected) AND (age) AND (coronary artery disease) AND (invasive coronary angiography) AND (ranging 40-80) AND (supposed to undergo) AND ((Men) OR (women)))"}
{"candidate_id": "LLM02871", "doc_id": "NCT02952378_exc", "case_bucket": "or", "source_criterion": "Heart failure Signs of kidney injury/failure Severe allergies", "candidate_expression": "((Heart failure) AND (allergies Severe) AND ((kidney failure) OR (kidney injury)))"}
{"candidate_id": "LLM02872", "doc_id": "NCT02965443_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetes Age 18 - 75 years Anti-GAD antibodies negative (Glutamic Acid Decarboxylase) C-peptide levels = 1.5 ng/mL Fasting blood glucose > 126 mg/dl HbA1c 8.0 - 10.5 % BMI 25.0 - 45.0 kg/m2 Previous therapy with BBIT (basal insulin and at least once daily bolus insulin)", "candidate_expression": "((Age 18 - 75 years) AND (Anti-GAD antibodies (Glutamic Acid Decarboxylase) negative) AND (BBIT) AND (BMI 25.0 - 45.0 kg/m2) AND (C-peptide levels = 1.5 ng/mL) AND (Fasting blood glucose > 126 mg/dl) AND (HbA1c 8.0 - 10.5 %) AND (Type 2 diabetes) AND (basal insulin and at least once daily bolus insulin) AND (therapy Previous))"}
{"candidate_id": "LLM02873", "doc_id": "NCT02678377_exc", "case_bucket": "other", "source_criterion": "History of recurrent UTI (defined as three culture proven UTIs within last 12 months) Systemic neuromuscular disease known to affect the lower urinary tract Undergoing concomitant prolapse surgery Previous incontinence surgery Treatment with anticholinergic medication in the last 2 months Previous bladder injection with onabotulinumtoxinA Prisoner Status Pregnancy", "candidate_expression": "((Pregnancy) AND (Prisoner) AND (anticholinergic medication) AND (bladder injection) AND (culture) AND (incontinence surgery) AND (last 2 month) AND (neuromuscular disease) AND (onabotulinumtoxinA) AND (prolapse surgery) AND (recurrent UTI) AND (three) AND (within last 12 months))"}
{"candidate_id": "LLM02874", "doc_id": "NCT02257580_exc", "case_bucket": "or", "source_criterion": "Preoperative use of an anticoagulant (Plavix, warfarin, lovenox, etc.) History of hypersensitivity to EACA History of thromboembolic event (e.g., PE or DVT) History of renal insufficiency or failure Congenital or acquired coagulopathy as evidence by INR >1.4 or PTT > 1.4 times normal, or Platelets <150,000/mm3 on preoperative laboratory testing Use of hormone replacement therapy or hormonal contraceptive agents within days prior to surgery Use of acetylsalicylic acid (ASA), antiplatelet agents within 7 days prior to surgery Pregnant Breastfeeding Not received neuraxial anesthesia", "candidate_expression": "((<150,000/mm3) AND (> 1.4 times normal) AND (>1.4 times normal) AND (ASA) AND (Breastfeeding) AND (Congenital) AND (DVT) AND (EACA) AND (INR) AND (Not received) AND (PE) AND (PTT) AND (Platelets) AND (Plavix) AND (Pregnant) AND (Preoperative) AND (acetylsalicylic acid) AND (acquired) AND (anticoagulant) AND (antiplatelet agents) AND (coagulopathy) AND (hormonal contraceptive agents) AND (hormone replacement therapy) AND (hypersensitivity) AND (lovenox) AND (neuraxial anesthesia) AND (preoperative laboratory testing) AND (renal failure) AND (renal insufficiency) AND (surgery) AND (thromboembolic event) AND (warfarin) AND (within 7 days prior to surgery) AND (within days prior to surgery))"}
{"candidate_id": "LLM02875", "doc_id": "NCT02550028_exc", "case_bucket": "or", "source_criterion": "Babies who have been close to death Seizure occurred by metabolic factors (hypoglycemia, hypocalcemia, electrolyte disorder) Babies who have received phenobarbitone or any other anticonvulsive medication before hospitalization Abnormal renal function", "candidate_expression": "((Abnormal renal function) AND (Babies) AND (Seizure metabolic factors) AND (anticonvulsive medication any other) AND (close to death have been) AND (electrolyte disorder) AND (hospitalization) AND (hypocalcemia) AND (hypoglycemia) AND (phenobarbitone) AND (renal function Abnormal))"}
```
