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
{"candidate_id": "LLM04926", "doc_id": "NCT02476461_inc", "case_bucket": "other", "source_criterion": "symptomatic Dupuytrens contracture with palpable cord, involving MCP, total contracture size over 30 degrees", "candidate_expression": "((Dupuytrens contracture) AND (involving MCP) AND (over 30 degrees) AND (palpable cord) AND (symptomatic) AND (total contracture size))"}
{"candidate_id": "LLM04927", "doc_id": "NCT03513874_inc", "case_bucket": "or", "source_criterion": "Type 1 diabetes according to ADA criterias <5 years. Age= 18 years and less than 70 years. Non-obese: defined as BMI less than 28 kg/m2 Positive for at least one of the anti-islet autoantibodies: GADA, IA2A, ZnT8A Fasting or postprandial plasma C-peptide more than 100 pmol/L Written informed consent from the patient or family representative.", "candidate_expression": "((<5 years) AND (= 18 years and less than 70 years) AND (ADA criterias) AND (Age) AND (BMI) AND (Fasting plasma C-peptide) AND (GADA) AND (IA2A) AND (Non) AND (Type 1 diabetes) AND (Written informed consent from the patient or family representative.) AND (ZnT8A) AND (anti-islet autoantibodies) AND (at least one) AND (less than 28 kg/m2) AND (more than 100 pmol/L) AND (obese) AND (postprandial plasma C-peptide))"}
{"candidate_id": "LLM04928", "doc_id": "NCT01793831_inc", "case_bucket": "or", "source_criterion": "Moderate to severe CD define as HBI score > 4. Montreal classification: no limitation, except age> 6.", "candidate_expression": "((> 4) AND (CD) AND (HBI score) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM04929", "doc_id": "NCT02519777_exc", "case_bucket": "or", "source_criterion": "Major depressive disorder with psychotic features Traumatic Brain Injury (TBI) with a clear impact on activities of daily living Developmental delay, intellectual deficit, and/or severe educational disability resulting in some dependence for activities of daily living Ongoing substance use disorder with significant impact on activities of daily living. Difficult or impossible to determine whether cognitive or functional decline is due to substance use or HIV, or both Evidence of intoxication or withdrawal during the screening evaluation Central nervous system (CNS) infections or opportunistic conditions: brain abscess (bacterial, mycobacterial, fungal or Toxoplasma), meningitis with persistent neurologic impairment, primary CNS lymphoma, progressive multifocal leukoencephalopathy (PML), or another structural brain lesion with neurological sequelae Other CNS conditions: non-opportunistic primary or metastatic brain tumors, uncontrolled seizure disorder, progressive multiple sclerosis, stroke with neurological sequelae, or dementia due to causes other than HIV (eg, Alzheimer's disease) Constitutional illness (eg, persistent unexplained fever, diarrhea, significant weight loss, disabling weakness) within 30 days of screening Known untreated B12 deficiency or malnutrition (body mass index [BMI] less than 18) at screening Evidence of current hepatitis C virus infection (HCV) (ie, HCV antibody [Ab] positive within 90 days prior to study entry unless also shown to be plasma HCV RNA negative within the same time period) Unstable and advanced liver disease (as defined by the presence of at least one of the following: ascites, encephalopathy, coagulopathy, hypoalbuminemia, esophageal or gastric varices, or persistent jaundice) Prior or current use of any CCR5 antagonist (such as MVC and cenicriviroc [CVC]) and integrase inhibitor (such as RAL, DTG, and elvitegravir [EVG]) Current use of any medication, including antiretrovirals, prohibited in the study (refer to the A5324 protocol-specific web page [PSWP] for the prohibited medications) Breastfeeding Presence of an AIDS-defining opportunistic infection within 6 months prior to entry. Note: Refer to the A5324 Manual of Operations (MOPS) for the list of AIDS-defining opportunistic infections. Active syphilis or treatment for syphilis within 90 days prior to study entry. NOTE: Active syphilis is defined as four-fold increase in serum rapid plasma reagin (RPR) or venereal disease research laboratory (VDRL) tests in an individual with past syphilis, or newly reactive serum RPR or VDRL with a reactive confirmatory test (enzyme immunoassays [EIA] or chemiluminescent assay [CIA], T. pallidum particle agglutination [TP-PA], or fluorescent treponemal antibody absorbed [FTA-ABS]). Known allergy/sensitivity or any hypersensitivity to components of study drugs or their formulation", "candidate_expression": "((AIDS-defining opportunistic infection within 6 months prior to entry) AND (Alzheimer's disease) AND (Breastfeeding) AND (CNS conditions Other) AND (Constitutional illness within 30 days of screening) AND (Major depressive disorder) AND (Traumatic Brain Injury (TBI)) AND (antiretrovirals) AND (body mass index [BMI] less than 18) AND (components of study drugs) AND (dependence for activities of daily living) AND (hepatitis C virus infection (HCV) Evidence current) AND (impact on activities of daily living) AND (liver disease Unstable advanced) AND (medication Current prohibited in the study) AND (neurologic impairment persistent) AND (neurological sequelae) AND (reactive confirmatory test) AND (substance use disorder Ongoing) AND (syphilis) AND (syphilis Active) AND (syphilis past) AND NOT (HIV) AND ((DTG) OR (RAL) OR (elvitegravir [EVG])) AND ((syphilis Active) OR (treatment within 90 days prior to study entry)) AND ((serum rapid plasma reagin (RPR)) OR (venereal disease research laboratory (VDRL))) AND ((VDRL) OR (serum RPR)) AND ((T. pallidum particle agglutination [TP-PA]) OR (chemiluminescent assay [CIA]) OR (enzyme immunoassays [EIA]) OR (fluorescent treponemal antibody absorbed [FTA-ABS])) AND ((allergy) OR (hypersensitivity) OR (sensitivity)) AND ((intoxication) OR (withdrawal)) AND ((Central nervous system (CNS) infections) OR (Central nervous system (CNS) opportunistic conditions)) AND ((Toxoplasma) OR (bacterial) OR (fungal) OR (mycobacterial)) AND ((CNS lymphoma primary) OR (brain abscess) OR (meningitis) OR (progressive multifocal leukoencephalopathy (PML)) OR (structural brain lesion another)) AND ((metastatic) OR (primary)) AND ((brain tumors non-opportunistic) OR (dementia) OR (progressive multiple sclerosis) OR (seizure disorder uncontrolled) OR (stroke)) AND ((Developmental delay) OR (evere educational disability) OR (intellectual deficit)) AND ((diarrhea) OR (disabling weakness) OR (unexplained fever persistent) OR (weight loss significant)) AND ((B12 deficiency) OR (malnutrition)) AND ((HCV antibody [Ab] positive within 90 days prior to study entry) OR (plasma HCV RNA negative within the same time period)) AND ((ascites) OR (coagulopathy) OR (encephalopathy) OR (esophageal varices) OR (gastric varices) OR (hypoalbuminemia) OR (jaundice persistent)) AND ((Prior) OR (current)) AND ((CCR5 antagonist) OR (integrase inhibitor)) AND ((MVC) OR (cenicriviroc [CVC])))"}
{"candidate_id": "LLM04930", "doc_id": "NCT02950558_exc", "case_bucket": "or", "source_criterion": "Unable to give informed consent in English Unable to complete surveys in English Unable to understand instructions for using pump in English Unavailable for followup Polytrauma; undergoing other surgeries or having other orthopedic injuries related to the precipitating cause of the ankle fracture Infection Peripheral vascular disease Diabetes Currently undergoing chemotherapy Pregnancy Currently lactating Heart disease or heart rhythm disorder or taking anti-arrhythmic drugs Severe renal impairment (Class 3 or worse kidney disease) Liver disease (cirrhosis or liver failure) Prior allergic reaction to any type of local anesthetic Taking therapeutic doses of anti-coagulants or anti-platelet therapy (prophylactic doses started because of hospital admission are not an exclusion) Currently taking antidepressants or other psychiatric medications Single shot local nerve block prior to surgery was ineffective Selected for neuraxial anesthesia rather than general anesthesia for the open reduction surgery Already receiving chronic analgesic therapy for a separate chronic pain condition", "candidate_expression": "((Currently lactating) AND (Diabetes) AND (Heart disease) AND (Infection) AND (Liver disease) AND (Peripheral vascular disease) AND (Polytrauma) AND (Pregnancy) AND (Severe renal impairment) AND (Unable to complete surveys in English) AND (Unable to give informed consent in English) AND (Unable to understand instructions for using pump in English) AND (Unavailable for followup) AND (allergic reaction) AND (analgesic therapy chronic) AND (ankle fracture) AND (anti-arrhythmic drugs) AND (anti-coagulants) AND (anti-platelet therapy) AND (antidepressants) AND (chemotherapy) AND (chronic pain separate) AND (cirrhosis) AND (general anesthesia) AND (heart rhythm disorder) AND (liver failure) AND (local anesthetic) AND (local nerve block Single shot prior to surgery) AND (neuraxial anesthesia) AND (not) AND (open reduction surgery) AND (other orthopedic injuries) AND (other surgeries) AND (psychiatric medications) AND (rather than))"}
{"candidate_id": "LLM04931", "doc_id": "NCT02566226_inc", "case_bucket": "other", "source_criterion": "physical status I - III patients scheduled to undergo hip arthroplasty", "candidate_expression": "((hip arthroplasty scheduled to undergo) AND (physical status I - III))"}
{"candidate_id": "LLM04932", "doc_id": "NCT00480129_exc", "case_bucket": "other", "source_criterion": "Ongoing allergen immunotherapy upper respiratory tract infection Pregnancy Clinical history of lactose-intolerance or allergies to cow-milk", "candidate_expression": "((Pregnancy) AND (allergen immunotherapy) AND (allergies to cow-milk) AND (lactose-intolerance) AND (upper respiratory tract infection))"}
{"candidate_id": "LLM04933", "doc_id": "NCT02566863_inc", "case_bucket": "other", "source_criterion": "patients classified with American Society of Anesthesiologists Physical Status Classification System as 1 or 2 status planned eye surgery under sedation", "candidate_expression": "((eye surgery planned under sedation) AND (sedation) AND (status American Society of Anesthesiologists Physical Status Classification System 1 or 2))"}
{"candidate_id": "LLM04934", "doc_id": "NCT03345589_exc", "case_bucket": "other", "source_criterion": "Autoimmune hepatitis Primary sclerosing cholangitis", "candidate_expression": "((Autoimmune hepatitis) AND (Primary sclerosing cholangitis))"}
{"candidate_id": "LLM04935", "doc_id": "NCT01078051_inc", "case_bucket": "or", "source_criterion": "Patients with angina or silent ischemia and documented ischemia Patients who are eligible for intracoronary stenting Age > 18 years De novo lesion CTO Reference vessel size 2.5 mm by visual estimation At least one CTO lesions located in proximal or mid epicardial coronary artery. (If the patient has two CTO lesions, one CTO lesion should be located in proximal or mid epicardial coronary artery) Angiographically defined total occlusion over 3 months If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)", "candidate_expression": "((2.5 mm) AND (3 months) AND (> 18 years) AND (Age) AND (Angiographically defined) AND (At least one) AND (CTO) AND (CTO lesions) AND (De novo lesion) AND (If no definite symptom with total occlusion, two experienced operators decide CTO in consideration of angiographical morphology (degree of calcification, bridging collaterals, non-tapered stump, angiographic filling from collaterals)) AND (Reference vessel size by visual estimation) AND (angina) AND (coronary artery) AND (documented) AND (in proximal coronary artery) AND (intracoronary stenting) AND (ischemia) AND (mid epicardial coronary artery) AND (silent) AND (total occlusion))"}
{"candidate_id": "LLM04936", "doc_id": "NCT02649114_inc", "case_bucket": "other", "source_criterion": "satisfying DSM-V criteria for ED and for half of the patients in addition have a history of childhood trauma.", "candidate_expression": "((DSM-V criteria) AND (ED) AND (childhood trauma) AND (history) AND (satisfying))"}
{"candidate_id": "LLM04937", "doc_id": "NCT03012984_inc", "case_bucket": "other", "source_criterion": "Age >= 65 years, < 90 years; Scheduled to undergo surgery for primary solid organ cancer under general anesthesia, with an expected duration of surgery >=2 hours; Planned to use patient-controlled intravenous analgesia after surgery; Provide written informed consent.", "candidate_expression": "((Age >= 65 years, < 90 years) AND (Provide written informed consent) AND (general anesthesia) AND (intravenous analgesia patient-controlled after surgery) AND (solid organ cancer primary) AND (surgery) AND (surgery Scheduled))"}
{"candidate_id": "LLM04938", "doc_id": "NCT03402945_exc", "case_bucket": "or", "source_criterion": "On systemic antibiotics or with an active bacterial infection at the time of surgery Patients previously enrolled in this trial Patients known to be colonized with Methicillin-resistant S. aureus (MRSA)(unethical not to administer glycopeptides), beta-lactam or vancomycin allergy precluding the use of cefazolin or vancomycin, respectively, or to silver precluding the use of Prevena Participation in other studies that may interfere with this trial", "candidate_expression": "((Participation in other studies that may interfere with this trial) AND (allergy) AND (colonized Methicillin-resistant S. aureus (MRSA)) AND (previously enrolled in this trial) AND (surgery) AND ((beta-lactam) OR (cefazolin) OR (silver) OR (vancomycin)) AND ((bacterial infection active at the time of surgery) OR (systemic antibiotics)))"}
{"candidate_id": "LLM04939", "doc_id": "NCT01857167_exc", "case_bucket": "or", "source_criterion": "1. Deny to sign the informed consent; 2. type 1 diabetes; 3. Family history of hypertriglyceridemia or fasting triglyceride>4.56 mmol/L; 4. Have severe liver disease, kidney disease or cancer; 5. Participating in the other clinical trial within 30 days; 6. Other diseases or conditions, for which the doctor of the patients do not agree his or her participating.", "candidate_expression": "((>4.56 mmol/L) AND (Deny to sign the informed consent;) AND (Family history) AND (Other conditions) AND (Other diseases) AND (cancer) AND (fasting triglyceride) AND (for which the doctor of the patients do not agree his or her participating) AND (for which the doctor of the patients do not agree his or her participating.) AND (hypertriglyceridemia) AND (kidney disease) AND (liver disease) AND (severe) AND (type 1 diabetes))"}
{"candidate_id": "LLM04940", "doc_id": "NCT00527826_exc", "case_bucket": "or", "source_criterion": "Known other respiratory disorders or signs for other respiratory disorders (e.g. asthma, lung cancer, sarcoidosis, tuberculosis, lung fibrosis, cystic fibrosis, bronchoectasis). Known history of significant inflammatory disease, other than COPD (e.g. rheumatoid arthritis and systemic lupus erythematosus). Known to be severely alpha-1-antitrypsin deficient (PI SZ or ZZ) Having undergone lung surgery (e.g. lung resection including lung volume reduction surgery, lung transplant) or subjects scheduled for surgery. Concurrent medication from Visit 1 and for the duration of the study with any of the prohibited medications: monoamine oxidase inhibitors and tricyclic antidepressants, and ritonavir (a highly potent cytochrome P450 3A4 inhibitor). Subjects receiving chronic or prophylactic antibiotic therapy. Serious, uncontrolled disease (including serious psychological disorders) likely to interfere with the study or impact on subject safety. Have, in the opinion of the investigator, evidence of alcohol, drug or solvent abuse. History of depression. History or presence of clinically significant drug sensitivity or clinically significant allergic reaction to corticosteroids or salmeterol. Moderate or severe COPD exacerbation (requiring corticosteroids or increased dosage of corticosteroids and/or antibiotics or hospitalization) within the 4 weeks prior to Visit 1 Lower respiratory tract infection within the 4 weeks prior to Visit 1 . Pregnant or lactating female and female of childbearing potential. Subject is a participating investigator, sub-investigator, study coordinator, or other employee of a participating investigator, or is an immediate family member of the before mentioned. Subject is an employee of GlaxoSmithKline (GSK). Subject participated in an investigational drug study within 30 days prior to Visit 1", "candidate_expression": "((COPD exacerbation within the 4 weeks prior to Visit 1) AND (Lower respiratory tract infection within the 4 weeks prior to Visit 1) AND (Pregnant) AND (alcohol abuse) AND (allergic reaction) AND (alpha-1-antitrypsin deficient severely) AND (antibiotics) AND (asthma) AND (bronchoectasis) AND (childbearing potential) AND (chronic antibiotic therapy) AND (corticosteroids) AND (corticosteroids increased dosage) AND (cystic fibrosis) AND (cytochrome P450 3A4 inhibitor) AND (depression History of) AND (drug abuse) AND (drug sensitivity) AND (female) AND (hospitalization) AND (inflammatory disease) AND (lactating) AND (lung cancer) AND (lung fibrosis) AND (lung resection) AND (lung surgery) AND (lung transplant) AND (lung volume reduction surgery) AND (medication from Visit 1) AND (monoamine oxidase inhibitors) AND (participated in an investigational drug study within 30 days prior to Visit 1) AND (prophylactic antibiotic therapy) AND (psychological disorders) AND (respiratory disorders) AND (rheumatoid arthritis) AND (ritonavir) AND (salmeterol Moderate severe) AND (sarcoidosis) AND (scheduled) AND (signs for respiratory disorders) AND (solvent abuse) AND (surgery) AND (systemic lupus erythematosus) AND (tricyclic antidepressants) AND (tuberculosis) AND (uncontrolled disease) AND NOT (COPD))"}
{"candidate_id": "LLM04941", "doc_id": "NCT02680054_exc", "case_bucket": "other", "source_criterion": "HbA1c greater than 75 mmol/mol (9.0%) Child unwilling to agree to second insulin injection at a meal-time Untreated coeliac disease or other concomitant condition likely to affect BG control Food allergies (other than controlled Coeliac Disease) Vegetarians, vegans or patients with religious dietary restrictions (as the standard meal contains meat) Participant taking any glucose-containing medication concurrently", "candidate_expression": "((Child unwilling to agree to second insulin injection at a meal-time) AND (Food allergies) AND (HbA1c greater than 75 mmol/mol 9.0%) AND (Vegetarians) AND (coeliac disease Untreated) AND (glucose-containing medication) AND NOT (Coeliac Disease))"}
{"candidate_id": "LLM04942", "doc_id": "NCT03089086_inc", "case_bucket": "or", "source_criterion": "South Australian secondary school students in years 10, 11, and 12 in 2017 Written parental consent for those under the age of 18 Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves) Available at school for at least the first pharyngeal swab and willing to comply with study procedures", "candidate_expression": "((South Australian) AND (Written parental consent for those under the age of 18) AND (Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves)) AND (comply with study procedures) AND (first) AND (in 2017) AND (pharyngeal swab) AND (secondary school students) AND (willing to) AND (years 10) AND (years 11) AND (years 12))"}
{"candidate_id": "LLM04943", "doc_id": "NCT01000155_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sickle cell disease Clinically significant disease defined as at least 1 painful episode per year averaged over the previous 3 years or a history of priapism, stroke, acute chest syndrome, avascular necrosis, multi-organ failure or the need for chronic narcotic medications for pain from sickle cell disease Must have failed a previous attempt at treatment with hydroxyurea defined as the inability to achieve a significant absolute increase in % fetal hemoglobin or the inability to tolerate hydroxyurea treatment due to severe side effects such as but not limited to myelosuppression, gastrointestinal symptoms, edema or hepatic enzyme elevations or have contraindications to hydroxyurea 18 years of age or older Hematologic laboratory values as outlined in the protocol Non-hematologic laboratory values as outlined in the protocol Must agree not to donate blood or other bodily fluid while taking the study drug and for 28 days thereafter Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment Women of child-bearing potential and men must agree to use 2 forms of adequate contraception prior to study entry and for the duration of study participation", "candidate_expression": "((Clinically significant disease) AND (WCBP) AND (Women) AND (Women of child-bearing potential (WCBP) must have a negative serum pregnancy test 72 hours or less prior to starting treatment) AND (acute chest syndrome) AND (age 18 years or older) AND (avascular necrosis) AND (child-bearing potential) AND (contraception must agree to 2 forms adequate prior to study entry for the duration of study participation study entry study participation) AND (donate blood Must agree to) AND (donate bodily fluid Must agree to while taking the study drug taking the study drug) AND (men) AND (multi-organ failure need for chronic) AND (narcotic medications chronic) AND (pain) AND (painful episode per year averaged over the previous 3 years at least 1 averaged over the previous 3 years the previous 3 years) AND (priapism history) AND (serum pregnancy test negative 72 hours or less prior to starting treatment) AND (sickle cell disease) AND (sickle cell disease Diagnosis Clinically significant) AND (stroke) AND (study drug for 28 days thereafter) AND (treatment starting treatment))"}
{"candidate_id": "LLM04944", "doc_id": "NCT00989261_exc", "case_bucket": "or", "source_criterion": "1. Patients over the age of 85 years except at the discretion of the Investigator and with agreement of the Sponsor. 2. Diagnosis of acute promyelocytic leukemia 3. Diagnosis of chronic myelogenous leukemia (CML) in blast crisis 4. AML in relapse or refractory after 3 or more previous lines of chemotherapy (and/or HSCT) treatment 5. AML or antecedent MDS secondary to prior chemotherapy 6. Persistent clinically significant non-hematological toxicity that is Grade >1 by NCI CTCAE v4 from prior chemotherapy 7. Patients who have had HSCT and are within 100 days of transplant and/or are still taking immunosuppressive drugs and/or have clinically significant graft-versus-host disease requiring treatment and/or have >Grade 1 persistent non hematological toxicity related to the transplant 8. Clinically active central nervous system (CNS) leukemia. Patients with CNS leukemia, which is controlled, but who are still receiving IT therapy at study entry may be considered eligible and continue receive IT therapy at the discretion of the Investigator and with agreement of the Sponsor. 9. Patients who have previously received AC220 10. Disseminated intravascular coagulation (DIC) (diagnosis by laboratory or clinical assessment) 11. Major surgery within 4 weeks prior to enrollment in the study 12. Radiation therapy within 4 weeks prior to, or concurrent with study 13. Use of concomitant drugs that prolong QT/QTc interval and/or are CYP3A4 inhibitors are prohibited with the exception of antibiotics, antifungals, and other antimicrobials that are used as standard of care to prevent or treat infections and other such drugs that are considered absolutely essential for the care of the patient. 14. Uncontrolled or significant cardiovascular disease 15. Women who are pregnant, lactating, or unwilling to use contraception if of childbearing potential 16. Men who are unwilling to use contraception if their partners are of childbearing potential 17. Active, uncontrolled infection 18. Human immunodeficiency virus positivity 19. Active hepatitis B or C or other active liver disease 20. History of cancer, except Stage 1 cervix or nonmelanotic skin cancer, with the possible exception of patients in complete remission", "candidate_expression": "((3 or more) AND (>Grade 1) AND (AC220) AND (AML) AND (Active) AND (CYP3A4 inhibitors) AND (Disseminated intravascular coagulation (DIC)) AND (Grade >1) AND (Grade >1 by NCI CTCAE v4) AND (HSCT) AND (History) AND (Human immunodeficiency virus) AND (MDS) AND (Major surgery) AND (Men) AND (NCI CTCAE v4) AND (Patients over the age of 85 years except at the discretion of the Investigator and with agreement of the Sponsor.) AND (Radiation therapy) AND (Stage 1 cervix) AND (Uncontrolled) AND (active) AND (acute promyelocytic leukemia) AND (after 3 or more previous lines of chemotherapy) AND (age) AND (antecedent) AND (antibiotics) AND (antifungals) AND (antimicrobials) AND (at the discretion of the Investigator) AND (blast crisis) AND (cancer) AND (cardiovascular disease) AND (central nervous system (CNS) leukemia) AND (chemotherapy) AND (childbearing potential) AND (chronic myelogenous leukemia (CML)) AND (clinically significant) AND (concurrent with study) AND (contraception) AND (drugs that prolong QT/QTc interval) AND (enrollment) AND (except) AND (graft-versus-host disease) AND (have had) AND (hepatitis B) AND (hepatitis C) AND (immunosuppressive drugs) AND (in relapse) AND (infection) AND (lactating) AND (lines of chemotherapy) AND (liver disease) AND (non hematological) AND (non-hematological) AND (nonmelanotic) AND (over the age of 85 years) AND (persistent) AND (positivity) AND (pregnant) AND (previous) AND (prior) AND (prolong QT/QTc interval) AND (refractory) AND (requiring) AND (significant) AND (skin cancer) AND (still) AND (study) AND (that prolong QT/QTc interval) AND (their partners are of childbearing potential) AND (toxicity) AND (transplant) AND (treatment) AND (uncontrolled) AND (unwilling) AND (with the exception of) AND (within 100 days of transplant) AND (within 4 weeks prior to enrollment) AND (within 4 weeks prior to study))"}
{"candidate_id": "LLM04945", "doc_id": "NCT03253796_inc", "case_bucket": "or", "source_criterion": "Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication Has chronic back pain of =3 months duration by history Has physician-diagnosed active nr-axSpA with disease duration <= 5 years • Inflammatory back pain • Arthritis (physician-diagnosed) • Enthesitis (heel) physician-diagnosed (spontaneous pain or tenderness at examination of the site of the insertion of the Achilles tendon or plantar fascia) • Dactylitis (physician-diagnosed) • Psoriasis (physician-diagnosed) • History of physician-diagnosed inflammatory bowel disease (IBD) • History of uveitis confirmed by an ophthalmologist • Good response to nonsteroidal anti-inflammatory drugs (NSAID) • Family history of SpA (presence of ankylosing spondylitis, psoriasis, acute uveitis, reactive arthritis, or IBD) • Elevated CRP • Human leukocyte antigen B27 (HLA-B27)+ gene Has a HLA-B27+ gene and 2 or more of the SpA characteristics listed above Has elevated CRP at Screening or evidence of active inflammation in the sacroiliac joints on MRI Has an ASDAS >= 2.1 at Screening Shows high disease activity at Screening and Baseline of both a Total Back Pain score of =4 and a Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score of >= 4 Has an acceptable history of NSAID use Has no history of untreated latent or active tuberculosis (TB) prior to Screening Has had no recent close contact with a person with active TB or, if there has been such contact, will undergo additional evaluations and receive appropriate treatment for latent TB", "candidate_expression": "(((HLA-B27)+) AND (ASDAS >= 2.1 at Screening) AND (Arthritis) AND (Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score >= 4) AND (CRP Elevated) AND (CRP elevated at Screening) AND (Dactylitis plantar fascia) AND (Enthesitis heel) AND (Good response) AND (HLA-B27+) AND (IBD) AND (Inflammatory back pain) AND (Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication) AND (MRI) AND (NSAID acceptable history latent) AND (Psoriasis) AND (SpA 2 or more) AND (SpA Family history) AND (Total Back Pain score =4) AND (acute uveitis) AND (ankylosing spondylitis) AND (chronic back pain =3 months duration history) AND (close contact recent) AND (disease duration <= 5 years) AND (duration =3 months) AND (gene Human leukocyte antigen B27) AND (high disease activity at Screening and Baseline) AND (inflammation active sacroiliac joints) AND (inflammatory bowel disease (IBD) History) AND (nonsteroidal anti-inflammatory drugs (NSAID)) AND (nr-axSpA active disease duration <= 5 years) AND (pain) AND (person with active TB) AND (psoriasis) AND (reactive arthritis) AND (tenderness site of the insertion of the Achilles tendon) AND (tuberculosis (TB) history untreated active) AND (uveitis History))"}
{"candidate_id": "LLM04946", "doc_id": "NCT00676273_exc", "case_bucket": "or", "source_criterion": "Patients: Who are pregnant or planning to become pregnant during the study or in the future With a elevated post-void residual (defined as PVR > 100cc) With a bleeding condition or on anti-coagulant therapy With immunosuppression (i.e. HIV, lymphoma) With multiple sclerosis or other progressive neurological disease With evidence of a local or systemic infection, including urinary tract infection With evidence of intrinsic sphincter deficiency as defined by a maximal urethral closure pressure of <20 cm H2O Previous sub-urethral sling Predominant overactive bladder symptoms", "candidate_expression": "((HIV) AND (PVR > 100cc) AND (anti-coagulant therapy) AND (bleeding condition) AND (immunosuppression) AND (intrinsic sphincter deficiency) AND (local infection) AND (lymphoma) AND (maximal urethral closure pressure <20 cm H2O) AND (multiple sclerosis) AND (overactive bladder) AND (overactive bladder symptoms Predominant) AND (post-void residual elevated) AND (pregnant) AND (pregnant planning to become during the study in the future) AND (progressive neurological disease) AND (sub-urethral sling Previous) AND (systemic infection) AND (urinary tract infection))"}
{"candidate_id": "LLM04947", "doc_id": "NCT00343668_inc", "case_bucket": "or", "source_criterion": "Pathologically proven unresectable adenocarcinoma of stomach With uni-dimensionally measurable disease (at least longest diameter 2 cm on conventional CT scan, x-ray or physical examination, or 1cm on spiral CT scan) Age 18 to 70 years old Estimated life expectancy of more than 3 months ECOG performance status of 2 or lower Adequate bone marrow function(absolute neutrophil count [ANC] ≥1,500/µL, hemoglobin ≥9.0 g/dL,and platelets ≥100,000/µL) Adequate kidney function (serum creatinine < 1.5 mg/dL) Adequate liver function (serum total bilirubin < 2 times the upper normal limit (UNL); serum transaminases levels <3 times [<5 times for patients with liver metastasis] UNL) No prior chemotherapy but prior adjuvant chemotherapy finished at least 6 months before enrollment was allowed. (but, prior adjuvant chemotherapy with capecitabine or S-1 or camptothecin analogues was excluded) No prior radiation therapy for at least 4 weeks before enrollment in the study", "candidate_expression": "((18 to 70 years old) AND (2 or lower) AND (< 1.5 mg/dL) AND (< 2 times the upper normal limit (UNL)) AND (<3 times UNL) AND (<5 times UNL) AND (Adequate) AND (Age) AND (ECOG performance status) AND (Estimated life expectancy) AND (No) AND (Pathologically) AND (S-1) AND (absolute neutrophil count [ANC]) AND (adenocarcinoma of stomach) AND (adjuvant chemotherapy) AND (at least 1cm) AND (at least 2 cm) AND (at least 4 weeks before enrollment) AND (at least 6 months before enrollment) AND (bone marrow function) AND (camptothecin analogues) AND (capecitabine) AND (chemotherapy) AND (conventional CT scan) AND (disease) AND (enrollment) AND (excluded) AND (hemoglobin) AND (kidney function) AND (liver function) AND (liver metastasis) AND (longest diameter) AND (more than 3 months) AND (physical examination) AND (platelets) AND (prior) AND (proven) AND (radiation therapy) AND (serum creatinine) AND (serum total bilirubin) AND (serum transaminases levels) AND (spiral CT scan) AND (uni-dimensionally measurable) AND (unresectable) AND (was allowed) AND (x-ray) AND (≥1,500/µL) AND (≥100,000/µL) AND (≥9.0 g/dL))"}
{"candidate_id": "LLM04948", "doc_id": "NCT02312076_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Myoma Previous) AND (Uterine abnormalities) AND (endometriosis) AND (uterine surgery) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM04949", "doc_id": "NCT03047538_inc", "case_bucket": "or", "source_criterion": "a very high cardiovascular risk and LDL-cholesterol> 1.8 mmol / l a high cardiovascular risk and LDL-cholesterol> 2.5 mmol / l Patient with a high or very high cardiovascular risk treated by lipidlowering therapy with statin", "candidate_expression": "((> 1.8 mmol / l) AND (> 2.5 mmol / l) AND (LDL-cholesterol) AND (cardiovascular risk) AND (high) AND (lipidlowering therapy) AND (stati) AND (very high))"}
{"candidate_id": "LLM04950", "doc_id": "NCT03252249_inc", "case_bucket": "other", "source_criterion": "Aged =18 years Clinical diagnosis of acute coronary syndrome In the opinion of the attending clinician requires dual anti-platelet therapy with aspirin and a P2Y12 receptor antagonist Resident in Scotland with a Community Health Index (CHI) number The attending clinician has equipoise regarding the duration of therapy Provision of informed consent", "candidate_expression": "((=18 years) AND (Aged) AND (P2Y12 receptor antagonist) AND (Provision of informed consent) AND (Resident) AND (Scotland) AND (acute coronary syndrome) AND (aspirin) AND (dual anti-platelet therapy) AND (requires))"}
```
