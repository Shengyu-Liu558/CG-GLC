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
{"candidate_id": "LLM05701", "doc_id": "NCT03397914_exc", "case_bucket": "or", "source_criterion": "Age less than one year or over 18 years Patients with renal impairment Colistin use less than 72 hours", "candidate_expression": "((Age less than one year over 18 years) AND (Colistin less than 72 hours) AND (renal impairment))"}
{"candidate_id": "LLM05702", "doc_id": "NCT01997580_exc", "case_bucket": "or", "source_criterion": "DSM-IV-TR substance-related disorders (except nicotine) significant medical or neurological conditions mental retardation or organic brain damage", "candidate_expression": "((significant medical or neurological conditions) AND (substance-related disorders DSM-IV-TR) AND NOT (nicotine) AND ((mental retardation) OR (organic brain damage)))"}
{"candidate_id": "LLM05703", "doc_id": "NCT02858804_inc", "case_bucket": "or", "source_criterion": "age=65 years diagnosis with mantle cell lymphoma Ann Arbor stage II,III or IV ECOG=1 or if ECOG=2 but recover after pretreatment.", "candidate_expression": "((=1) AND (=2) AND (=65 years) AND (Ann Arbor stage) AND (after pretreatment) AND (age) AND (mantle cell lymphoma) AND (pretreatment) AND (recover) AND ((II) OR (III) OR (IV)) AND ((ECOG)))"}
{"candidate_id": "LLM05704", "doc_id": "NCT03064568_exc", "case_bucket": "or", "source_criterion": "Patient with contraindication to misoprostol or vasopressin, personal history or cardiac or pulmonary disease, history of prior myomectomy", "candidate_expression": "((contraindication) AND (disease cardiac) AND (misoprostol) AND (myomectomy history prior) AND (pulmonary disease) AND (vasopressin))"}
{"candidate_id": "LLM05705", "doc_id": "NCT02269137_exc", "case_bucket": "or", "source_criterion": "hypoglycemia SE;psychogenic SE;any other pseudo-SE", "candidate_expression": "((hypoglycemia SE) OR (pseudo-SE) OR (psychogenic SE))"}
{"candidate_id": "LLM05706", "doc_id": "NCT02635893_inc", "case_bucket": "or", "source_criterion": "Male and females between ages 18-85 years of age SCI ( =1 month of injury) ASIA A, B,C and D SCI above L5 Able to perform a visible contraction with dorsiflexor and hip flexor muscles (allowing testing of largely impaired patients) Able to ambulate a few steps with or without an assistive device Male and females between ages 18-85 years of age Able to walk and complete lower-limb tests with both legs", "candidate_expression": "((ASIA A, B,C and D) AND (Able to ambulate a few steps) AND (SCI =1 month of injury) AND (SCI above L5) AND (ages between 18-85 years of age) AND ((Male) OR (females)) AND ((females) OR (l)) AND ((with assistive device) OR (without an assistive device)) AND ((Able to complete lower-limb tests with both legs) OR (Able to walk)))"}
{"candidate_id": "LLM05707", "doc_id": "NCT03225469_exc", "case_bucket": "or", "source_criterion": "1. History of colorectal surgery 2. Suspected or known digestive tract obstruction, stricture, or perforation 3. Serious status of illness, such as severe renal failure whose creatinine clearance<30 ml/min, New York Heart Association grade III or grade IV congestive heart failure, or hemodynamic instability, etc. 4. Incapable of completing bowel preparation，such as dysphagia, allergy to purgatives, or impaired mental status, etc. 5. Pregnancy or breastfeeding 6. Incomplete colonoscopy due to causes except poor bowel preparation 7. Unable to give informed consent 8. Have participated in the study before.", "candidate_expression": "((Incapable of completing bowel preparation) AND (New York Heart Association grade III or grade IV) AND (Pregnancy) AND (Serious status of illness) AND (allergy) AND (breastfeeding) AND (colonoscopy Incomplete) AND (colorectal surgery History) AND (congestive heart failure) AND (creatinine clearance <30 ml/min) AND (digestive tract obstruction) AND (digestive tract perforation) AND (digestive tract stricture) AND (dysphagia) AND (hemodynamic instability) AND (impaired mental status) AND (informed consent) AND (purgatives) AND (renal failure severe) AND NOT (poor bowel preparation))"}
{"candidate_id": "LLM05708", "doc_id": "NCT02478515_exc", "case_bucket": "or", "source_criterion": "Previous treatment with anti-VEGF drugs or corticosteroid or grid laser photocoagulation (study eye) History of vitrectomy surgery, submacular surgery, or other surgical intervention for RVO Ocular disorders in the study eye that may confound interpretation of study results BCVA over 77 letters between screening and Day 0 The pregnant or lactating woman", "candidate_expression": "((BCVA over 77 letters) AND (RVO) AND (The pregnant or lactating woman) AND ((anti-VEGF drugs) OR (corticosteroid) OR (grid laser photocoagulation ()) AND ((submacular surgery) OR (surgical intervention) OR (vitrectomy surgery)))"}
{"candidate_id": "LLM05709", "doc_id": "NCT00343668_inc", "case_bucket": "or", "source_criterion": "Pathologically proven unresectable adenocarcinoma of stomach With uni-dimensionally measurable disease (at least longest diameter 2 cm on conventional CT scan, x-ray or physical examination, or 1cm on spiral CT scan) Age 18 to 70 years old Estimated life expectancy of more than 3 months ECOG performance status of 2 or lower Adequate bone marrow function(absolute neutrophil count [ANC] ≥1,500/µL, hemoglobin ≥9.0 g/dL,and platelets ≥100,000/µL) Adequate kidney function (serum creatinine < 1.5 mg/dL) Adequate liver function (serum total bilirubin < 2 times the upper normal limit (UNL); serum transaminases levels <3 times [<5 times for patients with liver metastasis] UNL) No prior chemotherapy but prior adjuvant chemotherapy finished at least 6 months before enrollment was allowed. (but, prior adjuvant chemotherapy with capecitabine or S-1 or camptothecin analogues was excluded) No prior radiation therapy for at least 4 weeks before enrollment in the study", "candidate_expression": "((18 to 70 years old) AND (2 or lower) AND (< 1.5 mg/dL) AND (< 2 times the upper normal limit (UNL)) AND (<5 times UNL) AND (Adequate) AND (Age) AND (ECOG performance status) AND (Estimated life expectancy) AND (No) AND (Pathologically) AND (adenocarcinoma of stomach) AND (adjuvant chemotherapy) AND (at least 1cm) AND (at least 2 cm) AND (at least 4 weeks before enrollment) AND (at least 6 months before enrollment) AND (bone marrow function) AND (chemotherapy) AND (disease) AND (enrollment) AND (excluded) AND (kidney function) AND (liver function) AND (longest diameter) AND (more than 3 months) AND (prior) AND (proven) AND (radiation therapy) AND (serum creatinine) AND (serum total bilirubin) AND (serum transaminases levels) AND (uni-dimensionally measurable) AND (unresectable) AND (was allowed) AND (≥1,500/µL) AND (≥100,000/µL) AND (≥9.0 g/dL) AND ((absolute neutrophil count [ANC]) OR (hemoglobin) OR (platelets)) AND ((<3 times UNL) OR (liver metastasis)) AND ((S-1) OR (camptothecin analogues) OR (capecitabine)) AND ((conventional CT scan) OR (physical examination) OR (spiral CT scan) OR (x-ray)))"}
{"candidate_id": "LLM05710", "doc_id": "NCT03381755_inc", "case_bucket": "scope", "source_criterion": "After half-dose ticagrelor (loading dose 90mg, and then 45mg bidpo.) treatment for 3 days, the platelet aggregation is effectively inhibited by light transmission aggregometry method and thromboela-stogram. planned to undergo PCI recently planned to DAPT for 1 year after PCI", "candidate_expression": "((DAPT planned to for 1 year after PCI) AND (PCI) AND (PCI planned to undergo) AND (light transmission aggregometry) AND (loading dose 90mg 45mg bidpo.) AND (platelet aggregation inhibited) AND (thromboela-stogram) AND (ticagrelor half-dose treatment for 3 days))"}
{"candidate_id": "LLM05711", "doc_id": "NCT02502734_exc", "case_bucket": "or", "source_criterion": "A history of life-threatening asthma defined for this protocol as an asthma episode that required intubation, hypercapnea requiring non-invasive ventilatory support, respiratory arrest, hypoxic seizures or asthma-related syncopal episode(s). Subjects with a history of asthma exacerbation requiring the use of systemic corticosteroids (tablets, suspension, or injection) for at least 3 days or a depot corticosteroid injection or emergency room attendance (within 3 months) or requiring hospitalization for asthma (within 6 months) prior to screening. Significant, non-reversible active pulmonary disease (e.g. cystic fibrosis, bronchiectasis, tuberculosis). Culture-documented or suspected bacterial or viral infection of the upper or lower respiratory tract, sinus or middle ear that is not resolved within 4 weeks of Visit 1 and led to a change in asthma management or, in the opinion of the Investigator, is expected to affect the subject's asthma status or the subject's ability to participate in the study. Any fracture in the leg to be measured within 6 months prior to the screening visit. Any metabolic disorders or other diseases that may impact on normal growth patterns. No major surgery requiring general anaesthesia for at least 3 months prior to the screening visit. No febrile illnesses with temperature >39 degree celsius for more than five consecutive days within the week preceding the Screening Visit. Any significant abnormality or medical condition identified at the screening medical assessment (including serious psychological disorder) that in the Investigator's opinion, preclude entry into the study due to risk to the subject or that may interfere with the outcome of the study. Clinical visual evidence of candidiasis at Visit 1 (Screening). Use of any of the prohibited medications listed in protocol. Strenuous physical exercise within 3 hours of Visit 1 (Screening) Drug allergies: Any adverse reaction including immediate or delayed hypersensitivity to any intranasal, inhaled, or systemic corticosteroid therapy. Known or suspected sensitivity to the constituents of the ELLIPTA Inhaler (i.e., lactose, FF). Milk Protein Allergy: History of severe milk protein allergy. The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 30 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer). Exposure to more than 4 investigational medicinal products within 12 months prior to the first dosing day. Unable to use the ELLIPTA inhaler and peak flow meter correctly. An affiliation with the Investigator site: the parents/guardians or child is an immediate family member of the participating Investigator, sub-Investigator, study coordinator, or employee of the participating Investigator. The Parent or Guardian has a history of psychiatric disease, intellectual deficiency, substance abuse or other condition (e.g. inability to read, comprehend or write) which may affect: validity of consent to participate in the study; adequate supervision of the subject during the study; compliance of subject with study medication and study procedures (e.g. completion of daily diary, attending scheduled clinic visits); subject safety and well-being. Children in care: Children who are wards of the government or state are not eligible for participation in this study.", "candidate_expression": "((Any significant abnormality or medical condition identified at the screening medical assessment (including serious psychological disorder) that in the Investigator's opinion, preclude entry into the study due to risk to the subject or that may interfere with the outcome of the study.) AND (Culture) AND (Drug allergies) AND (ELLIPTA inhaler) AND (FF) AND (Milk Protein Allergy) AND (Significant) AND (Strenuous physical exercise within 3 hours of Visit 1 (Screening)) AND (The Parent or Guardian has a history of psychiatric disease, intellectual deficiency, substance abuse or other condition (e.g. inability to read, comprehend or write) which may affect: validity of consent to participate in the study; adequate supervision of the subject during the study; compliance of subject with study medication and study procedures (e.g. completion of daily diary, attending scheduled clinic visits); subject safety and well-being.) AND (The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 30 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer).) AND (Unable to use the ELLIPTA inhaler and peak flow meter correctly.) AND (abnormality) AND (adverse reaction) AND (asthma) AND (asthma episode) AND (asthma exacerbation history) AND (asthma history life-threatening) AND (asthma management) AND (asthma-related syncopal episode) AND (bacterial infection of the lower respiratory tract) AND (bacterial infection of the middle ear) AND (bacterial infection of the sinus) AND (bacterial infection of the upper respiratory tract) AND (bronchiectasis) AND (candidiasis at Visit 1 (Screening)) AND (constituents of the ELLIPTA Inhaler) AND (cystic fibrosis) AND (delayed hypersensitivity) AND (depot corticosteroid injection) AND (emergency room attendance within 3 months) AND (fracture in the leg within 6 months prior to the screening visit) AND (general anaesthesia for at least 3 months prior to the screening visit) AND (hospitalization within 6 months) AND (hypercapnea) AND (hypoxic seizures) AND (immediate hypersensitivity) AND (in the opinion of the Investigator) AND (inhaled corticosteroid) AND (intranasal corticosteroid) AND (intubation) AND (investigational medicinal products more than 4 within 12 months prior to the first dosing day) AND (lactose) AND (may impact on normal growth patterns) AND (medical condition) AND (metabolic disorders) AND (milk protein allergy severe) AND (non-invasive ventilatory support) AND (other diseases) AND (peak flow meter) AND (prohibited medications listed in protocol) AND (pulmonary disease Significant non-reversible active) AND (respiratory arrest) AND (sensitivity) AND (significant) AND (subject's ability to participate in the study) AND (suspected) AND (systemic corticosteroid) AND (systemic corticosteroids for at least 3 days) AND (temperature >39 degree celsius for more than five consecutive days within the week preceding the Screening Visit) AND (tuberculosis) AND (viral infection of the lower respiratory tract) AND (viral infection of the middle ear) AND (viral infection of the sinus) AND (viral infection of the upper respiratory tract) AND (visual evidence) AND NOT (major surgery) AND NOT (febrile illnesses))"}
{"candidate_id": "LLM05712", "doc_id": "NCT02923700_inc", "case_bucket": "or", "source_criterion": "patients affected by mono-lateral symptomatic knee articular degenerative pathology with history of chronic (for at least 4 months) pain or swelling; imaging findings of degenerative changes of the joint (osteoarthritis or chondropathy with Kellgren Lawrence Score from 0 to 3 at X-ray evaluation).", "candidate_expression": "((Kellgren Lawrence Score) AND (X-ray) AND (chondropathy) AND (chronic) AND (degenerative changes) AND (for at least 4 months) AND (from 0 to 3) AND (imaging) AND (knee articular degenerative pathology) AND (mono-lateral) AND (osteoarthritis) AND (pain) AND (swelling) AND (symptomatic))"}
{"candidate_id": "LLM05713", "doc_id": "NCT00926523_exc", "case_bucket": "other", "source_criterion": "Subject are pregnant Subject is unable to perform tasks associated with study", "candidate_expression": "((Subject is unable to perform tasks associated with study) AND (pregnant))"}
{"candidate_id": "LLM05714", "doc_id": "NCT01799681_inc", "case_bucket": "other", "source_criterion": "diagnosed with PD by a neurologist (Fahn and Elton, 1987); aged 30 to 85 years; at modified Hoehn and Yahr (H&Y) stage 1.5 to 3 (Hoehn and Yahr ,1967; Goetz et al., 2004); able and willing to give written consent for participation in the study; living at home in the community; able to walk independently for 30 metres with or without an assistive device.", "candidate_expression": "((PD by a neurologist) AND (able and willing to give written consent for participation in the study;) AND (able to walk independently with or without an assistive device for 30 metres) AND (aged 30 to 85 years) AND (living at home in the community) AND (modified Hoehn and Yahr (H&Y) stage 1.5 to 3))"}
{"candidate_id": "LLM05715", "doc_id": "NCT03164096_exc", "case_bucket": "or", "source_criterion": "Patients with coagulopathy or under anti-coagulation therapy. Gastrointestinal disease, motion sickness. diabetes mellitus. Patients with preeclampsia,", "candidate_expression": "((Gastrointestinal disease) AND (diabetes mellitus) AND (motion sickness) AND (preeclampsia) AND ((anti-coagulation therapy) OR (coagulopathy)))"}
{"candidate_id": "LLM05716", "doc_id": "NCT00425789_inc", "case_bucket": "other", "source_criterion": "The study will include 40 post-deep peel women (exoderm), older than 18 years old, treated by the same dermatologist (dr. Landau). The treatment group will receive 5 consecutive daily hyperbaric treatments, 1 hours long each, at 2 ATF, starting from day 7 to peel. Prior to treatment, each patient will be signed on informed consent and will have complete physical examination. The control group will be matched by the following parameters: age, skin color and type, and indication for peeling, and will be picked up by the dermatologist.", "candidate_expression": "((age) AND (control group) AND (deep peel) AND (exoderm) AND (old) AND (older than 18 years) AND (skin color) AND (type) AND (women))"}
{"candidate_id": "LLM05717", "doc_id": "NCT02872090_inc", "case_bucket": "other", "source_criterion": "patients with FEV1 / FVC <70%", "candidate_expression": "((<70%) AND (FEV1 / FVC))"}
{"candidate_id": "LLM05718", "doc_id": "NCT02705222_exc", "case_bucket": "or", "source_criterion": "Age < 45 or > 55 years. Blood disorders or coagulopathy. Diagnosed or suspected local gynecologic lesion (polyp, adenomyosis, myoma, malignancy or cervical pathology). Use intrauterine contraceptive device. Pregnancy related conditions.", "candidate_expression": "((< 45 or > 55 years) AND (Age) AND (Blood disorders) AND (Diagnosed) AND (Pregnancy) AND (Pregnancy related) AND (adenomyosis) AND (cervical pathology) AND (coagulopathy) AND (conditions) AND (intrauterine contraceptive device) AND (local gynecologic lesion) AND (malignancy) AND (myoma) AND (polyp) AND (suspected))"}
{"candidate_id": "LLM05719", "doc_id": "NCT03304496_exc", "case_bucket": "or", "source_criterion": "Pregnant. Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent. With acute myocardial infarction with ST segment elevation in the first 12 hours from the onset of symptoms. With any acute coronary syndrome complicated with acute pulmonary edema, cardiogenic shock and / or malignant ventricular arrhythmias. In which a cardiac catheterization is planned a priori to be performed via femoral, brachial or ulnar. Patients in whom first attempt of arterial puncture is performed by 2nd year interventional cardiology fellow or by physician in charge. Participating in another clinical trial. Be allergic or have contraindications to nitroglycerin or other nitrates. Any phosphodiesterase 5 inhibitor (sildenafil, tadalafil, avanafil, vardenafil) has been taken within 72 hours prior to the study.", "candidate_expression": "((Not have informed consent for the present clinical trial, or do not fully understand the meaning of informed consent) AND (Pregnant) AND (ST segment elevation) AND (acute coronary syndrome) AND (acute myocardial infarction) AND (cardiac catheterization) AND (in the first 12 hours from the onset of symptoms) AND (malignant) AND (phosphodiesterase 5 inhibitor) AND (study) AND (the onset of symptoms) AND (within 72 hours prior to the study) AND ((brachial) OR (femoral) OR (ulnar)) AND ((allergic) OR (contraindications)) AND ((nitrates) OR (nitroglycerin)) AND ((avanafil) OR (sildenafil) OR (tadalafil) OR (vardenafil)) AND ((acute pulmonary edema) OR (cardiogenic shock) OR (ventricular arrhythmias)))"}
{"candidate_id": "LLM05720", "doc_id": "NCT02152696_exc", "case_bucket": "or", "source_criterion": "Hemodynamically unstable in need of acute treatment Most recent hCG > 5000 mIU/mL Patient obtaining care in relation to a recently completed pregnancy (delivery, spontaneous or elective abortion) Diagnosis of gestational trophoblastic disease Subject unwilling or unable to comply with study procedures Known hypersensitivity to MTX Presence of clinical contraindications for treatment with MTX Prior medical or surgical management of this gestation Subject unwilling to accept a blood transfusion", "candidate_expression": "((> 5000 mIU/mL) AND (Hemodynamically unstable) AND (MTX) AND (Most recent) AND (Subject unwilling to accept a blood transfusion) AND (gestation) AND (gestational trophoblastic disease) AND (hCG) AND (hypersensitivity to MTX) AND (medical management) AND (surgical management))"}
{"candidate_id": "LLM05721", "doc_id": "NCT02831166_inc", "case_bucket": "or", "source_criterion": "ST-segment elevation acute myocardial infarction patients during the first 12 hours of sympton onset; Intention to perform primary percutaneous coronary intervention; Signed informed consent; Patient eligible for transradial and transfemoral primary percutaneous coronary intervention, being pre-requisites: (a) familiarity of the operator with the radial and femoral techniques using vascular closure devices, (b) agreement of the operator to use the access route determined by the randomization process.", "candidate_expression": "((Intention to perform) AND (ST-segment elevation) AND (acute myocardial infarction) AND (during the first 12 hours of sympton onset) AND (eligible for) AND (percutaneous coronary intervention) AND (primary) AND ((transfemoral) OR (transradial)))"}
{"candidate_id": "LLM05722", "doc_id": "NCT02664558_exc", "case_bucket": "or", "source_criterion": "Exclusions Related to Cardiovascular Disease 1. History of uncontrolled hypertension 2. Persistent hypotension at Screening. 3. Evidence or history of left-sided heart disease and/or clinically significant cardiac disease in which pulmonary hypertension is more likely WHO Group 2. 4. Acute decompensated heart failure within 1 month of Screening. 5. Recent initiation (<8 weeks from Screening) or planned initiation of cardiopulmonary rehabilitation exercise program. Exclusions Related to Pulmonary Disease 6. Newly diagnosed with PAH and not on PAH-specific therapy. 7. Pulmonary hypertension due to: 1. Uncorrected congenital systemic-to-pulmonary shunt. 2. Pulmonary veno-occlusive disease and/or pulmonary capillary hemangiomatosis 3. Persistent pulmonary hypertension of the newborn 4. WHO clinical classification Groups 2-5 8. Evidence of significant airway and/or parenchymal lung disease. 9. Chronic infection related to tuberculosis or fungal or mycobacterial disease. Exclusions Based on Other Medical Conditions 10. Chronic infections including, but not limited to tuberculosis (TB), hepatitis B virus (HBV) or hepatitis C virus (HCV). 11. History of portal hypertension or chronic liver disease, including positive serology for infection with HCV and/or HBV. 12. Evidence of active infection requiring intravenous or oral antibiotics within 4 weeks of Screening. 13. Body mass index ≥35.0 at Screening. 14. History of obstructive sleep apnea. 15. History of malignancy within the last 5 years, except nonmelanoma skin cancer and cervical carcinoma in situ treated with curative intent. 16. Neuropsychiatric disorders/symptoms or psychological conditions. 17. Pregnancy or breast-feeding 18. Prior treatment with B cell or lymphocyte-depleting agents (eg, rituximab, Campath) Exclusions Based on Concomitant Medication Use 19. Concurrent regular use of another leukotriene pathway inhibitor, including over-the-counter medications or herbal remedies. Exclusions Based on Laboratory Values 20. Significant/chronic renal insufficiency. 21. Transaminases (alanine transaminase, aspartate transaminase) levels >3 × upper limit of normal (ULN) and/or bilirubin level >2 × ULN. 22. Absolute neutrophil count <1500 mm3. 23. Hemoglobin concentration <9 g/dL at Screening. 24. Hepatic dysfunction as defined by Child-Pugh Class B or C", "candidate_expression": "((Absolute neutrophil count <1500 mm3) AND (Body mass index ≥35.0 at Screening) AND (Child-Pugh Class B or C) AND (Hemoglobin concentration <9 g/dL at Screening) AND (Hepatic dysfunction) AND (PAH Newly diagnosed) AND (Persistent hypotension at Screening) AND (Significant) AND (Transaminases levels >3 × upper limit of normal (ULN)) AND (WHO Group 2) AND (WHO clinical classification Groups 2-5) AND (alanine transaminase) AND (aspartate transaminase) AND (bilirubin level >2 × ULN) AND (cardiopulmonary rehabilitation exercise program) AND (chronic renal insufficiency Significant) AND (clinically significant) AND (congenital systemic-to-pulmonary shunt Uncorrected) AND (heart failure Acute decompensated within 1 month of Screening <8 weeks from Screening) AND (hypertension History uncontrolled) AND (infection Chronic) AND (infection requiring antibiotics) AND (infection requiring antibiotics within 4 weeks of Screening) AND (infections Chronic) AND (leukotriene pathway inhibitor Concurrent regular use another) AND (malignancy History within the last 5 years) AND (obstructive sleep apnea History) AND (pulmonary hypertension of the newborn Persistent) AND (significant) AND (treated curative intent) AND NOT (nonmelanoma skin cancer) AND NOT (cervical carcinoma in situ) AND ((Neuropsychiatric disorders) OR (Neuropsychiatric symptoms) OR (psychological conditions)) AND ((Pregnancy) OR (breast-feeding)) AND ((B cell -depleting agents) OR (lymphocyte-depleting agents)) AND ((Campath) OR (rituximab)) AND ((cardiac disease clinically significant) OR (left-sided heart disease) OR (pulmonary hypertension)) AND ((Recent) OR (planned)) AND ((PAH-specific therapy) OR (not)) AND ((Pulmonary veno-occlusive disease) OR (pulmonary capillary hemangiomatosis)) AND ((airway disease) OR (parenchymal lung disease)) AND ((fungal disease) OR (mycobacterial disease) OR (tuberculosis)) AND ((hepatitis B virus (HBV)) OR (hepatitis C virus (HCV)) OR (tuberculosis (TB))) AND ((chronic liver disease) OR (portal hypertension)) AND ((serology for infection HBV positive) OR (serology for infection with HCV positive)))"}
{"candidate_id": "LLM05723", "doc_id": "NCT02055053_exc", "case_bucket": "other", "source_criterion": "Conversion from laparoscopic to open surgery History of Chronic pain or ongoing treatment for chronic pain Age less than 18 yrs Allergy to local anesthetics", "candidate_expression": "((Age less than 18 yrs) AND (Allergy) AND (Chronic pain History) AND (chronic pain) AND (local anesthetics) AND (treatment ongoing))"}
{"candidate_id": "LLM05724", "doc_id": "NCT01959061_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed colorectal adenocarcinoma Disease limited to the liver Unresectable disease by surgery or other local therapies Age >18 years ECOG performance status 0-2,Child pugh A or B Expected survival = 3 months Adequate hematological, hepatic, and renal function", "candidate_expression": "((0-2) AND (= 3 months) AND (>18 years) AND (A) AND (Adequate) AND (Age) AND (B) AND (Child pugh) AND (Disease limited to the liver) AND (ECOG performance status) AND (Expected survival) AND (Histologically) AND (Histologically confirmed) AND (Unresectable disease) AND (colorectal adenocarcinoma) AND (hematological function) AND (hepatic function) AND (local therapies) AND (other) AND (renal function) AND (surgery))"}
{"candidate_id": "LLM05725", "doc_id": "NCT02760251_exc", "case_bucket": "or", "source_criterion": "Adults older than 45 and children younger than 18 years Platelet count higher than 30x109/l at time of screening Suspicion of secondary ITP Positive family history for ITP Presence or history of autoimmune disease as judged by the investigator Hepatosplenomegaly Presence or history of relevant hepatic disease as judged by the investigator Presence or history of thromboembolic disease as judged by the investigator Patients with splenectomy Women who are pregnant or breast feeding Intention to become pregnant during the course of the study Lack of safe double contraception (see 7.1) Any vaccination 2 weeks prior start of the study Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center Known or suspected non-compliance, drug or alcohol abuse Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject Participation in another study with investigational drug within the 30 days preceding and during the present study Previous enrolment into the current study Previous treatment with romiplostim or eltrombopag Hypersensitivity to the active substance or to any of the excipients or to E. coli derived proteins Enrolment of the investigator, his/her family members, employees and other dependent persons", "candidate_expression": "((Adults older than 45) AND (Drugs with a known impact on the immune system or on platelet function must be recorded and an exclusion of the study should be discussed with the study center) AND (Hepatosplenomegaly) AND (Hypersensitivity) AND (Inability to follow the procedures of the study, e.g. due to language problems, psychological disorders, dementia of the study subject) AND (Intention to become pregnant during the course of the study) AND (Lack of safe double contraception (see 7.1)) AND (Platelet count higher than 30x109/l at time of screening) AND (Women who are pregnant or breast feeding) AND (alcohol abuse) AND (as judged by the investigator) AND (autoimmune disease) AND (children younger than 18 years) AND (drug abuse) AND (eltrombopag) AND (family history for ITP) AND (hepatic disease relevant) AND (romiplostim) AND (secondary ITP) AND (splenectomy) AND (thromboembolic disease) AND (vaccination 2 weeks prior start of the study))"}
```
