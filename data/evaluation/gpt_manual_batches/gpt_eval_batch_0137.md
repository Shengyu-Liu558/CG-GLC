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
{"candidate_id": "LLM03401", "doc_id": "NCT03347513_exc", "case_bucket": "or", "source_criterion": "Severe Iron deficiency anemia (hemoglobin < 8.0 g/dL). Parasitic worm infection e.g. schistosomiasis, and hook worm by stool analysis. Any cases giving clinical symptoms of gastritis e.g. nausea, vomiting, dull aching pain or soreness in the epigastrium. Cases with history of gastric ulcer diagnosed by upper endoscopy. Cases complaining of hematemesis.", "candidate_expression": "((< 8.0 g/dL) AND (Iron deficiency anemia) AND (Parasitic worm infection) AND (Severe) AND (clinical symptoms) AND (dull aching pain) AND (gastric ulcer) AND (gastritis) AND (hematemesis) AND (hemoglobin) AND (history) AND (hook worm) AND (nausea) AND (schistosomiasis) AND (soreness in the epigastrium) AND (stool analysis) AND (upper endoscopy) AND (vomiting))"}
{"candidate_id": "LLM03402", "doc_id": "NCT03424733_exc", "case_bucket": "or", "source_criterion": "prior allergic reaction to interferon products, congestive heart failure, elevated liver enzymes", "candidate_expression": "((interferon products) AND ((allergic reaction prior) OR (congestive heart failure) OR (elevated liver enzymes)))"}
{"candidate_id": "LLM03403", "doc_id": "NCT02019160_inc", "case_bucket": "other", "source_criterion": "Kindergarteners who have joined our outreach dental service will be invited to join this study. Preschool children aged 3-4 years who have tooth decay and are attending the first year of kindergarten will be invited to join this study.", "candidate_expression": "((Kindergarteners) AND (Preschool children) AND (aged 3-4 years) AND (tooth decay))"}
{"candidate_id": "LLM03404", "doc_id": "NCT02022709_inc", "case_bucket": "or", "source_criterion": "Having been diagnosed with primary OCD as defined by the Diagnostic and Statistical Manual of Mental Disorders (DSM-IV-) criteria;Cleaning or checking as primary OCD symptoms Yale-Brown Obsessive-Compulsive Scale (Y-BOCS) score of = 16 Never receiving adequate treatment or stop receiving treatment for at least 8 weeks Having an education degree of high school or above Accepting to participate in the study", "candidate_expression": "((DSM-IV) AND (Diagnostic and Statistical Manual of Mental Disorders) AND (Never) AND (Y-BOCS) AND (Yale-Brown Obsessive-Compulsive Scale) AND (adequate) AND (ccepting to participate in the study) AND (degree of high school) AND (for at least 8 weeks) AND (primary OCD) AND (score of = 16) AND (stop) AND (treatment))"}
{"candidate_id": "LLM03405", "doc_id": "NCT03194074_exc", "case_bucket": "or", "source_criterion": "Patients with cardiac, pulmonary, hepatic, or renal dysfunction, epilepsy, or uncontrolled hypertension, or those taking medications that influence the central nervous system, are excluded from the study. Patients who show obvious alteration of mental status, or refuse to participate, are also excluded from the study.", "candidate_expression": "((alteration of mental status) AND (cardiac dysfunction) AND (epilepsy) AND (hepatic dysfunction) AND (hypertension uncontrolled) AND (medications that influence the central nervous system) AND (pulmonary dysfunction) AND (refuse to participate) AND (renal dysfunction))"}
{"candidate_id": "LLM03406", "doc_id": "NCT02701881_inc", "case_bucket": "or", "source_criterion": "Age 19 years of older Moderate or severe claudication (Rutherford category 2 or 3) Critical limb ischemia (Rutherford category 4 or 5) Patients with signed informed consent Target lesion length =150 mm by angiographic estimation Stenosis of more than 50% in femoropopliteal artery At least one patent (less than 50 percent stenosed) tibioperoneal runoff vessel.", "candidate_expression": "((19 years of older) AND (2 or 3) AND (4 or 5) AND (=150 mm) AND (Age) AND (At least one) AND (Critical) AND (Moderate) AND (Rutherford category) AND (Stenosis) AND (Target lesion) AND (angiographic) AND (claudication) AND (femoropopliteal artery) AND (length) AND (limb ischemia) AND (more than 50%) AND (patent tibioperoneal runoff vessel) AND (severe))"}
{"candidate_id": "LLM03407", "doc_id": "NCT02222272_inc", "case_bucket": "or", "source_criterion": "All adult patients with chronic myeloid leukaemia in any phase (chronic, accelerated or blastic) who undergo allogeneic stem cell transplantation between 01/01/2010 and 30/09/2013 and have been previously treated with Nilotinib or Dasatinib, regardless of their response to these drugs.", "candidate_expression": "((adult) AND (allogeneic stem cell transplantation between 01/01/2010 and 30/09/2013) AND (chronic myeloid leukaemia any phase) AND ((Dasatinib) OR (Nilotinib)) AND ((accelerated) OR (blastic) OR (chronic)))"}
{"candidate_id": "LLM03408", "doc_id": "NCT02973035_exc", "case_bucket": "or", "source_criterion": "Unwillingness or inability to comply with the procedures described in this protocol Planned cardiac surgery or planned major non-cardiac surgery within the study period. Stroke or coronary revascularization in the past 6 months. Clinically significant pulmonary disease. Untreated hyperthyroidism, or hypothyroidism. A diagnosis of cancer (other than superficial squamous or basal cell skin cancer) in the past 3 years or current treatment for the active cancer. Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. LV ejection fraction < 50%. Significant renal disease manifested by serum creatinine > 2.5 mg/dL Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (ALT or AST > 3 times upper limit of normal). History of intolerance to ARB or amlodipine. Hypertrophic or restrictive cardiomyopathy. Moderate or severe valvular disease. Constrictive pericarditis Atrial fibrillation with a heart rate > 120/min. Sitting systolic BP < 100 mmHg", "candidate_expression": "((ALT) AND (ARB) AND (AST) AND (Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study) AND (Atrial fibrillation) AND (Constrictive pericarditis) AND (Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding) AND (Hepatic disease) AND (Hypertrophic cardiomyopathy Moderate severe) AND (LV ejection fraction < 50%) AND (Stroke revascularization) AND (Unwillingness or inability to comply with the procedures described in this protocol) AND (amlodipine) AND (basal cell skin cancer) AND (biliary tract obstruction) AND (cancer) AND (cancer active) AND (cardiac surgery Planned) AND (coronary revascularization) AND (heart rate > 120/min) AND (hepatic enzyme elevation significant) AND (hyperthyroidism) AND (hypothyroidism) AND (intolerance) AND (pulmonary disease Clinically significant) AND (renal disease Significant) AND (restrictive cardiomyopathy) AND (serum creatinine > 2.5 mg/dL) AND (superficial squamous skin cancer) AND (surgery planned major cardiac) AND (systolic BP Sitting < 100 mmHg) AND (treatment) AND (valvular disease))"}
{"candidate_id": "LLM03409", "doc_id": "NCT03400735_inc", "case_bucket": "other", "source_criterion": "The diagnosis of chronic bronchitis The diagnosis of community-acquired pneumoniae FEV1 value = 30-80% The diagnosis of mild-severe acute exacerbation of chronic bronchitis (AECB) Oxygen saturation < 90%", "candidate_expression": "((< 90%) AND (= 30-80%) AND (AECB) AND (FEV1 value) AND (Oxygen saturation) AND (acute) AND (chronic bronchitis) AND (community-acquired pneumoniae) AND (exacerbation of chronic bronchitis) AND (mild-severe))"}
{"candidate_id": "LLM03410", "doc_id": "NCT03484091_inc", "case_bucket": "other", "source_criterion": "Symptomatic primary knee osteoarthritis with failed conservative treatment at least 3 months Kellgren-Lawrence grade I-III Gave informed consent Can do questionnaires", "candidate_expression": "((Can do questionnaires) AND (Gave informed consent) AND (I-III) AND (Kellgren-Lawrence grade) AND (Symptomatic) AND (at least 3 months) AND (conservative treatment) AND (failed) AND (knee) AND (osteoarthritis) AND (primary))"}
{"candidate_id": "LLM03411", "doc_id": "NCT02701881_inc", "case_bucket": "or", "source_criterion": "Age 19 years of older Moderate or severe claudication (Rutherford category 2 or 3) Critical limb ischemia (Rutherford category 4 or 5) Patients with signed informed consent Target lesion length =150 mm by angiographic estimation Stenosis of more than 50% in femoropopliteal artery At least one patent (less than 50 percent stenosed) tibioperoneal runoff vessel.", "candidate_expression": "((Age 19 years of older) AND (Rutherford category 2 or 3) AND (Rutherford category 4 or 5) AND (Stenosis more than 50% femoropopliteal artery) AND (Target lesion) AND (angiographic) AND (claudication) AND (length =150 mm) AND (limb ischemia Critical) AND (patent tibioperoneal runoff vessel At least one) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM03412", "doc_id": "NCT02430740_inc", "case_bucket": "other", "source_criterion": "female infertile patients eligible for IVF treatment", "candidate_expression": "((IVF treatment) AND (eligible) AND (female) AND (infertile))"}
{"candidate_id": "LLM03413", "doc_id": "NCT03199560_inc", "case_bucket": "or", "source_criterion": "Women above 18 years of age with biopsy proven, clinically stage 1 or 2 breast cancer who will be undergoing partial mastectomy with SLNBx at Memorial Health", "candidate_expression": "((SLNBx) AND (Women above 18 years) AND (age) AND (at Memorial Health) AND (biopsy) AND (breast cancer) AND (partial mastectomy will be undergoing) AND ((stage 1) OR (stage 2)))"}
{"candidate_id": "LLM03414", "doc_id": "NCT02242188_inc", "case_bucket": "or", "source_criterion": "Term singleton infants (>37 weeks gestational age) Birth weight > 2500g Healthy at inclusion Breastfed exclusively or predominantly (>50% meals) at inclusion No previous iron supplementation No previous blood transfusion Informed consent given", "candidate_expression": "((> 2500g) AND (>37 weeks) AND (>50% meals) AND (Birth weight) AND (Breastfed) AND (Healthy) AND (Informed consent given) AND (No) AND (at inclusion) AND (blood transfusion) AND (gestational age) AND (iron supplementation) AND (previous) AND ((exclusively) OR (predominantly)) AND ((Term infants) OR (singleton infants)))"}
{"candidate_id": "LLM03415", "doc_id": "NCT02565277_exc", "case_bucket": "or", "source_criterion": "Have not received influenza vaccination in the past or cannot be vaccinated due to previous severe reaction to influenza vaccine, egg, latex, or thimerosol allergies, or refusal of vaccination Participant has received a community available influenza vaccine within <6 months History of Guillain-Barré syndrome Immunosuppressive disorders or medications (including oral prednisone >10 mg daily, recent chemotherapy treatment) Emergency cases as determined by the investigator or physician", "candidate_expression": "((Guillain-Barré syndrome) AND (influenza vaccine within <6 months) AND NOT (influenza vaccination) AND ((chemotherapy) OR (oral prednisone >10 mg daily)) AND ((Immunosuppressive disorders) OR (Immunosuppressive medications)))"}
{"candidate_id": "LLM03416", "doc_id": "NCT03177837_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((18-75 yrs) AND (40-80% predicted) AND (750 m) AND (<800m) AND (=92%) AND (COPD) AND (FEV1) AND (GOLD) AND (SpO2) AND (Written informed consent.) AND (age) AND (living at low altitude) AND ((Male) OR (female)))"}
{"candidate_id": "LLM03417", "doc_id": "NCT02483715_inc", "case_bucket": "other", "source_criterion": "Participants having H. pylori related chronic gastritis with/without peptic ulcers who are aged greater than 20 years old and are willing to received eradication therapy.", "candidate_expression": "((aged greater than 20 years old) AND (chronic gastritis H. pylori related) AND (eradication therapy willing to receive) AND (peptic ulcers))"}
{"candidate_id": "LLM03418", "doc_id": "NCT02281643_exc", "case_bucket": "or", "source_criterion": "Known intolerance to the doxycycline Body weight <40 kg Pregnancy or breastfeeding History of severe allergic reaction or anaphylaxis Alcohol or drug abuse", "candidate_expression": "((doxycycline) AND ((Alcohol abuse) OR (drug abuse)) AND ((Body weight <40 kg) OR (Pregnancy) OR (breastfeeding) OR (intolerance to the doxycycline)) AND ((allergic reaction severe) OR (anaphylaxis)))"}
{"candidate_id": "LLM03419", "doc_id": "NCT01890759_exc", "case_bucket": "or", "source_criterion": "Participation in the 4 weeks preceding inclusion or planned participation during the present trial period in another clinical trial investigating a vaccine, drug, medical device, or medical procedure. Receipt of any vaccine in the 4 weeks preceding each trial vaccination or planned receipt of any vaccine in the 4 weeks following each trial vaccination, except for: (i) influenza vaccination, which may be received at least 2 weeks before study vaccines. (ii) measles (M) or measles, mumps, rubella (MMR) routine vaccination, which can be administered concomitantly with the first dose of study vaccine as per routine immunization schedule (iii) for subjects enrolled at Indian sites: oral poliomyelitis vaccine (OPV) received during National Immunization Days (NIDs) and supplementary immunization activity days (SIADs) Previous vaccination against meningococcal disease with either the study vaccine or another meningococcal vaccine Receipt of immune globulins, blood or blood-derived products in the past 3 months Known or suspected congenital or acquired immunodeficiency; or receipt of immunosuppressive therapy, such as anti-cancer chemotherapy or radiation therapy, within the preceding 6 months; or long-term systemic corticosteroid therapy (prednisone or equivalent for more than 2 consecutive weeks within the past 3 months) History of meningococcal diseases, confirmed either clinically, serologically, or microbiologically At high risk, in the opinion of the Investigator, for meningococcal disease during the trial Known or suspected systemic hypersensitivity to any of the vaccine components, or history of a life-threatening reaction to the vaccine used in the trial or to a vaccine containing any of the same substances Known thrombocytopenia, contraindicating intramuscular vaccination Bleeding disorder, or receipt of anticoagulants in the 3 weeks preceding inclusion, contraindicating intramuscular vaccination In an emergency setting, or hospitalized involuntarily Chronic illness that, in the opinion of the investigator, is at a stage where it might interfere with trial conduct or completion For subjects enrolled at Indian sites: Moderate or severe acute illness/infection (according to investigator judgment) on the day of vaccination or febrile illness (temperature ≥ 38.0°C). For subjects enrolled at Russian sites: Acute disease of any severity on the day of vaccination or febrile illness (axillary temperature ≥ 37.0°C). A prospective subject should not be included in the study until the condition has resolved or the febrile event has subsided. Receipt of oral or injectable antibiotic therapy within 72 hours prior to the first blood draw Identified as a natural or adopted child of the Investigator or employee with direct involvement in the proposed study Personal history of Guillain-Barré Syndrome.", "candidate_expression": "((Acute disease on the day of vaccination) AND (At high risk, in the opinion of the Investigator, for meningococcal disease during the trial) AND (Bleeding disorder) AND (Chronic illness that, in the opinion of the investigator, is at a stage where it might interfere with trial conduct or completion) AND (Guillain-Barré Syndrome history) AND (Indian sites) AND (Indian sites Moderate severe) AND (Known) AND (Participation in the 4 weeks preceding inclusion or planned participation during the present trial period in another clinical trial investigating a vaccine, drug, medical device, or medical procedure.) AND (Russian sites) AND (according to investigator judgment) AND (acquired immunodeficiency) AND (acute illness) AND (acute infection) AND (another meningococcal vaccine) AND (anti-cancer chemotherapy) AND (antibiotic therapy within 72 hours prior to the first blood draw oral injectable) AND (anticoagulants) AND (axillary temperature ≥ 37.0°C) AND (blood) AND (blood-derived products) AND (congenital immunodeficiency) AND (contraindicating) AND (emergency setting) AND (except for) AND (febrile illness) AND (febrile illness on the day of vaccination) AND (history) AND (hospitalized involuntarily) AND (immune globulins) AND (immunosuppressive therapy within the preceding 6 months) AND (influenza vaccination at least 2 weeks before study vaccines) AND (intramuscular vaccination) AND (life-threatening reaction) AND (measles (M) vaccination) AND (measles, mumps, rubella (MMR) vaccination) AND (meningococcal diseases) AND (microbiologically confirmed) AND (oral poliomyelitis vaccine (OPV) during National Immunization Days (NIDs) during supplementary immunization activity days (SIADs)) AND (planned participation 4 weeks preceding inclusion inclusion) AND (prednisone for more than 2 consecutive weeks within the past 3 months) AND (radiation therapy) AND (serologically confirmed) AND (study vaccine) AND (suspected) AND (systemic corticosteroid therapy long-term) AND (systemic hypersensitivity) AND (temperature ≥ 38.0°C) AND (thrombocytopenia) AND (vaccination against meningococcal disease) AND (vaccine) AND (vaccine components) AND (vaccine in the 4 weeks preceding each trial vaccination) AND (vaccine planned receipt) AND (vaccine used in the trial))"}
{"candidate_id": "LLM03420", "doc_id": "NCT00425789_inc", "case_bucket": "other", "source_criterion": "The study will include 40 post-deep peel women (exoderm), older than 18 years old, treated by the same dermatologist (dr. Landau). The treatment group will receive 5 consecutive daily hyperbaric treatments, 1 hours long each, at 2 ATF, starting from day 7 to peel. Prior to treatment, each patient will be signed on informed consent and will have complete physical examination. The control group will be matched by the following parameters: age, skin color and type, and indication for peeling, and will be picked up by the dermatologist.", "candidate_expression": "((age) AND (deep peel) AND (exoderm) AND (old older than 18 years) AND (skin color) AND (type) AND (women))"}
{"candidate_id": "LLM03421", "doc_id": "NCT02361892_inc", "case_bucket": "other", "source_criterion": "submucosal, intramural or subserosal leiomyomas, symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain", "candidate_expression": "((infertility) AND (intramural leiomyomas) AND (menometrorrhagia) AND (menstrual disorder) AND (pelvic pain) AND (submucosal) AND (subserosal leiomyomas) AND (symptoms))"}
{"candidate_id": "LLM03422", "doc_id": "NCT02056626_exc", "case_bucket": "or", "source_criterion": "abnormal renal function currently pregnant, or trying to become pregnant being treated with a beta-blocker use of illicit drugs", "candidate_expression": "((abnormal renal function) AND (beta-blocker) AND (currently) AND (illicit drugs) AND (pregnant) AND (treated) AND (trying to become))"}
{"candidate_id": "LLM03423", "doc_id": "NCT01261832_exc", "case_bucket": "or", "source_criterion": "The patient has a known hypersensitivity or contraindication to any of the following medications: Heparin, Aspirin, Clopidogrel, Cilostazol Uncontrolled hypertension History of bleeding diathesis or known coagulopathy (including heparin-induced thrombocytopenia), or refuses blood transfusions. Baseline hemogram with Hb<10g/dL or PLT count<100,000/μL Patients already taking warfarin, cilostazol or any other type of anti-platelet agents except aspirin and clopidogrel Gastrointestinal or genitourinary bleeding within the prior 3 months, or major surgery within 2 months. Pregnancy", "candidate_expression": "((<100,000/μL) AND (<10g/dL) AND (Baseline) AND (History) AND (Pregnancy) AND (Uncontrolled) AND (blood transfusions) AND (except) AND (hemogram) AND (heparin-induced thrombocytopenia) AND (hypertension) AND (major surgery) AND (within 2 months) AND (within the prior 3 months) AND ((bleeding diathesis) OR (coagulopathy) OR (refuses blood transfusions)) AND ((Hb) OR (PLT count)) AND ((contraindication) OR (hypersensitivity)) AND ((anti-platelet agents) OR (cilostazol) OR (warfarin)) AND ((aspirin) OR (clopidogrel)) AND ((Aspirin) OR (Cilostazol) OR (Clopidogrel) OR (Heparin)) AND ((Gastrointestinal bleeding) OR (genitourinary bleeding)))"}
{"candidate_id": "LLM03424", "doc_id": "NCT02766530_exc", "case_bucket": "or", "source_criterion": "Estimated GFR (eGFR) < 60 mL/min/1.73 m2 and blood glucose > 135 mg/dl; Past or present history of acute renal failure, renal dialysis, diabetes mellitus. Women who received metallic fixation, coronary artery stent in recent 3 months; or women who received mechanical valve replacement that is not compatible with MR magnet; or women with aneurysmal clips, pacemakers. Past history of claustrophobia. Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low) Past history of breast cancer within recent 5 years before the currently diagnosed breast cancer. Women who received chemotherapy for other disease entity in recent 1 year. Women who cannot cooperate with the examinations.", "candidate_expression": "((Estimated GFR < 60 mL/min/1.73 m2) AND (Women) AND (Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low)) AND (Women who cannot cooperate with the examinations) AND (acute renal failure) AND (aneurysmal clips) AND (blood glucose > 135 mg/dl) AND (breast cancer recent 5 years before the currently diagnosed breast cancer) AND (chemotherapy recent 1 year) AND (claustrophobia) AND (coronary artery stent) AND (diabetes mellitus) AND (eGFR) AND (mechanical valve replacement) AND (metallic fixation) AND (pacemakers) AND (renal dialysis) AND (women))"}
{"candidate_id": "LLM03425", "doc_id": "NCT02481518_inc", "case_bucket": "or", "source_criterion": "Age > 18 years Eastern Cooperative Oncology Group score 0-2 First Diagnosed Head and neck cancer and plan for treatment with cisplatin Serum creatinine =1.5 mg/dl or eGFR=60(ml/min/1.73 m2)", "candidate_expression": "((=1.5 mg/dl) AND (=60(ml/min/1.73 m2)) AND (> 18 years) AND (Age) AND (Eastern Cooperative Oncology Group) AND (Head and neck cancer) AND (Serum creatinine) AND (cisplatin) AND (eGFR) AND (plan) AND (score 0-2))"}
```
