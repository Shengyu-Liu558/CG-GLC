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
{"candidate_id": "LLM02326", "doc_id": "NCT02277041_exc", "case_bucket": "or", "source_criterion": "women undergoing caesarean section at less than 37 weeks of gestation. Hypertension with pregnancy. Cardiac and coronary diseases with pregnancy", "candidate_expression": "((Cardiac diseases) AND (Hypertension) AND (caesarean section undergoing) AND (coronary diseases) AND (gestation less than 37 weeks) AND (pregnancy) AND (women))"}
{"candidate_id": "LLM02327", "doc_id": "NCT02974686_inc", "case_bucket": "or", "source_criterion": "Kidney transplant recipients at Washington University/Barnes-Jewish Hospital Experiencing GI toxicity from MPA as determined by the treating physician within 12 months post-renal transplant On standard immunosuppression with tacrolimus and prednisone", "candidate_expression": "((GI toxicity) AND (Kidney transplant) AND (MPA) AND (Washington University/Barnes-Jewish Hospital) AND (standard immunosuppression) AND ((prednison) OR (tacrolimus)))"}
{"candidate_id": "LLM02328", "doc_id": "NCT03335904_inc", "case_bucket": "or", "source_criterion": "normotensive forced expiratory volume in 1s : forced vital capacity ratio > 0.75 no medical history of cardiovascular and respiratory disease not taking medications other than oral contraceptives free from sleep apnea body mass index less than 30 kg/m2", "candidate_expression": "((> 0.75) AND (body mass index) AND (forced expiratory volume in 1s : forced vital capacity ratio) AND (free from) AND (less than 30 kg/m2) AND (medical history) AND (medications) AND (no) AND (normotensive) AND (not) AND (oral contraceptives) AND (other than) AND (sleep apnea) AND ((cardiovascular disease) OR (respiratory disease)))"}
{"candidate_id": "LLM02329", "doc_id": "NCT02892968_inc", "case_bucket": "other", "source_criterion": "At the cluster level, ED physicians practicing at a participating site will be eligible. At the patient level, all hip fractures seen by a participating ED physician will be eligible", "candidate_expression": "(hip fracture)"}
{"candidate_id": "LLM02330", "doc_id": "NCT03181984_inc", "case_bucket": "other", "source_criterion": "Age range: 14 to 65 years-old; Clinically diagnosed of Port-wine Stain; Patients receiving hemoporfin based upon the clinical judgment of the investigator; Written informed consent signed and agreed to receive periodic follow-up", "candidate_expression": "((14 to 65 years-old) AND (Age) AND (Port-wine Stain) AND (Written informed consent signed and agreed to receive periodic follow-up) AND (hemoporfin))"}
{"candidate_id": "LLM02331", "doc_id": "NCT02883400_exc", "case_bucket": "other", "source_criterion": "dual organ transplant", "candidate_expression": "((dual) AND (organ transplant))"}
{"candidate_id": "LLM02332", "doc_id": "NCT02077556_exc", "case_bucket": "or", "source_criterion": "Pregnancy Tuberculosis Hepatitis B or C carrier status Human immunodeficiency virus-positive status Retransplantation or multiorgan transplantation History of rheumatoid arthritis Use of drugs that might have enhanced or inhibited CYP3A4 or P-gp activity", "candidate_expression": "((Hepatitis B carrier) AND (Hepatitis C carrier) AND (Human immunodeficiency virus) AND (Pregnancy) AND (Retransplantation) AND (Tuberculosis) AND (multiorgan) AND (positive) AND (rheumatoid arthritis) AND (transplantation))"}
{"candidate_id": "LLM02333", "doc_id": "NCT02964715_exc", "case_bucket": "or", "source_criterion": "eGFR <45 ml/min structural and functional urogenital abnormalities, that predispose for urogenital infections Investigational product use in the last 6 months SGLT2 inhibitor, TZD, DPP4 inhibitor and GLP1 RA use within the past 6 months DKA(Diabetic Ketoacidosis) or HHS(Hyperosmoloar Hyperglycaemic Syndrome) within the last 6 months Pregnancy Presence of major contraindications to magnetic resonance imaging (cardiac pacemakers, claustrophobia, foreign bodies and implanted medical devices with ferromagnetic properties). Liver cirrhosis Type 1 diabetes Severe uncorrected insulin insufficiency Significant alcohol intake HIV infection Use of Traditional Chinese Medication or alternative therapies Coexisting causes of chronic liver disease - chronic viral hepatitis(B & C), autoimmune liver disease, hemochromatosis, Wilson's etc. Use of medications associated with steatosis eg. Methotrexate, anticonvulsants, antiretroviral therapy etc. h/o stroke Steroid therapy Endogenous Cushing's Familial hypertriglyceridemia", "candidate_expression": "((<45 ml/min) AND (Cushing's) AND (DKA) AND (DPP4 inhibitor) AND (Diabetic Ketoacidosis) AND (Endogenous) AND (Familial hypertriglyceridemi) AND (GLP1 RA) AND (HHS) AND (HIV infection) AND (Hyperosmoloar Hyperglycaemic Syndrome) AND (Investigational product use) AND (Liver cirrhosis) AND (Methotrexate) AND (Pregnancy) AND (SGLT2 inhibitor) AND (Severe) AND (Significant) AND (Steroid therapy) AND (TZD) AND (Traditional Chinese Medication) AND (Type 1 diabetes) AND (Wilson's) AND (alcohol intake) AND (alternative therapies) AND (anticonvulsants) AND (antiretroviral therapy) AND (autoimmune liver disease) AND (cardiac pacemakers) AND (chronic liver disease) AND (chronic viral hepatitis B) AND (chronic viral hepatitis C) AND (claustrophobia) AND (eGFR) AND (ferromagnetic properties) AND (foreign bodies) AND (functional) AND (hemochromatosis) AND (implanted medical devices) AND (in the last 6 months) AND (insulin insufficiency) AND (magnetic resonance imaging) AND (major contraindications) AND (medications) AND (predispose for urogenital infections) AND (steatosis) AND (stroke) AND (structural) AND (uncorrected) AND (urogenital abnormalities) AND (urogenital infections) AND (within the last 6 months) AND (within the past 6 months))"}
{"candidate_id": "LLM02334", "doc_id": "NCT02457442_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02335", "doc_id": "NCT01809041_inc", "case_bucket": "or", "source_criterion": "major elective gastrointestinal, gynecological, prostate or bladder surgery patients who are = 60 years old. the surgery is laparoscopic surgery and is expected to last for = 2 hours under general anesthesia and the patient will stay in hospital for at least 7 days after surgery. lack of serious hearing and vision impairment and be able to read so that neurobehavioral tests can be performed.", "candidate_expression": "((able to read) AND (laparoscopic surgery) AND (last expected = 2 hour under general anesthesia) AND (neurobehavioral tests can be performed) AND (old = 60 years old) AND (stay in hospital will at least 7 days after surgery) AND ((hearing impairment) OR (vision impairment)) AND ((bladder surgery) OR (gastrointestinal surgery) OR (gynecological surgery) OR (prostate surgery)))"}
{"candidate_id": "LLM02336", "doc_id": "NCT02557386_exc", "case_bucket": "other", "source_criterion": "Chronic pain more than 3 months Drug abuse Chronic use of analgesic drugs (more than 3 months) Psychiatric illness Peripheral neuropathy Drug allergy Severe gastroesophageal reflux disease", "candidate_expression": "((Chronic pain more than 3 months) AND (Drug) AND (Drug abuse) AND (Peripheral neuropathy) AND (Psychiatric illness) AND (allergy) AND (analgesic drugs Chronic more than 3 months) AND (gastroesophageal reflux disease Severe))"}
{"candidate_id": "LLM02337", "doc_id": "NCT02882113_inc", "case_bucket": "other", "source_criterion": "19 years old and above. Patients who previously have received a liver transplant over the last six months and within last three years. Patients who are on Tacrolimus immunosuppressive therapy twice a day for at least two weeks. Patients who have normal liver function and renal function. Patients who have been monitored without complication such as acute rejection. Patients willing to sign his/her consent.", "candidate_expression": "((19 years and above) AND (Patients willing to sign his/her consent) AND (Tacrolimus) AND (acute rejection) AND (at least two weeks) AND (complication) AND (last six months and within last three years) AND (liver function) AND (liver transplant) AND (normal) AND (old) AND (renal function) AND (twice a day) AND (without))"}
{"candidate_id": "LLM02338", "doc_id": "NCT03209687_exc", "case_bucket": "or", "source_criterion": "Females who have high response (estradiol at time of ovulation trigger is > 5000 pg/ml or more than 15 oocytes are retrieved)", "candidate_expression": "((Females) AND (high response) AND ((estradiol at time of ovulation trigger > 5000 pg/ml) OR (oocytes retrieved more than 15)))"}
{"candidate_id": "LLM02339", "doc_id": "NCT02277041_inc", "case_bucket": "other", "source_criterion": "Women with a singleton pregnancy undergoing cesarean section after 37 weeks of gestation.", "candidate_expression": "((after 37 weeks) AND (cesarean section) AND (gestation) AND (singleton pregnancy))"}
{"candidate_id": "LLM02340", "doc_id": "NCT03623789_exc", "case_bucket": "or", "source_criterion": "Preoperative Hemoglobin <U+2266>11 g/dl History of infection or intraarticular fracture of the affective hip Renal function deficiency (GFR <30 ml/min/1.73m2) Elevated liver enzyme (aspartate transaminase (AST)/ alanine transaminase(ALT) level are more than twice normal range) , history of liver cirrhosis, impaired liver function(elevated total bilirubin level) and coagulopathy (including long-term use anticoagulant) History of deep vein thrombosis, ischemic heart disease or stroke Contraindications of tranexamic acid, floseal, or rivaroxaban Allergy to tranexamic acid, floseal, rivaroxaban, or the excipients History of heparin-induced thrombocytopenia (HIT) Coagulopathy or bleeding tendency caused by organ dysfunction, such as cirrhosis, bone marrow suppression etc. Patient who have active bleeding disorder, such as intracranial hemorrhage, upper gastrointestinal bleeding, hematuria. Patients with known allergies to materials of bovine origin.", "candidate_expression": "((<30 ml/min/1.73m2) AND (<U+2266>11 g/dl) AND (Allergy) AND (Coagulopathy) AND (Contraindications) AND (Elevated) AND (GFR) AND (Hemoglobin) AND (History) AND (Preoperative) AND (Renal function deficiency) AND (active) AND (affective hip) AND (allergies) AND (anticoagulant) AND (aspartate transaminase (AST)/ alanine transaminase(ALT) level) AND (bleeding disorder) AND (bleeding tendency) AND (bone marrow suppression) AND (cirrhosis) AND (coagulopathy) AND (deep vein thrombosis) AND (elevated) AND (excipients) AND (floseal) AND (hematuria) AND (heparin-induced thrombocytopenia (HIT)) AND (history) AND (impaired liver function) AND (infection) AND (intraarticular fracture) AND (intracranial hemorrhage) AND (ischemic heart disease) AND (liver cirrhosis) AND (liver enzyme) AND (long-term use) AND (materials of bovine origin) AND (more than twice normal range) AND (organ dysfunction) AND (rivaroxaban) AND (stroke) AND (total bilirubin level) AND (tranexamic acid) AND (upper gastrointestinal bleeding))"}
{"candidate_id": "LLM02341", "doc_id": "NCT00886158_inc", "case_bucket": "other", "source_criterion": "Age from birth to 21 years All solid organ transplant recipients receiving their care at Seattle Children's Hospital Signed consent, and when age appropriate, signed assent", "candidate_expression": "((Age) AND (Seattle Children's Hospital) AND (Signed consent, and when age appropriate, signed assent) AND (from birth to 21 years) AND (solid organ transplant))"}
{"candidate_id": "LLM02342", "doc_id": "NCT02726009_inc", "case_bucket": "other", "source_criterion": "Has given written informed consent before any study-related activity is performed Advanced hormone-dependent prostate cancer for which androgen deprivation therapy is indicated, and independently from this trial, Firmagon® is intended to be used for treatment Age greater than or equal to 18 years and less than 80 years Advanced hormone-dependent prostate cancer without any other clinically significant disorder Easten Cooperative Oncology Group score = 2 PSA = 2 ng/mL at screening Life expectancy of at least 12 months as per the investigator's judgement", "candidate_expression": "((= 2) AND (= 2 ng/mL) AND (Advanced) AND (Age) AND (Easten Cooperative Oncology Group score) AND (Firmagon) AND (Has given written informed consent before any study-related activity is performed) AND (Life expectancy) AND (PSA) AND (androgen deprivation therapy) AND (at least 12 months) AND (greater than or equal to 18 years and less than 80 years) AND (hormone-dependent) AND (intended) AND (prostate cancer))"}
{"candidate_id": "LLM02343", "doc_id": "NCT02979561_exc", "case_bucket": "or", "source_criterion": "Signs of hemodynamic instability (i.e. systolic blood pressure <100 mm Hg.St. or episode of systolic blood pressure fall for =40 mm Hg. / or heart rate > 110 lasting more than 15 min) or need for ventilatory support within 12 hours prior to randomisation. The indication for oral anticoagulation, associated with others disease. malignant neoplasm of any location Contraindications to warfarin or pradaxa according to Russian Instructions for medical use of these drugs Indications for concomitant treatment with antiplatelet agents Any stroke within 6 months before randomization Intracranial hemorrhage in anamnesis Active bleeding, bleeding diathesis. Clinically significant bleeding within the last 30 days. Trauma or extensive surgery within 1 month before randomization or surgery planned in the next 6 months after randomization. Intracranial pathology: tumor, arteriovenous fistula or aneurysm. Gastrointestinal bleeding in the previous 3 months. Gastric ulcer or duodenal ulcer with clinical manifestations or endoscopically identified acute ulcer without signs of scarring during previous 30 days. Uncontrolled hypertension (systolic blood pressure> 180 mm Hg. and / or diastolic blood pressure> 100 mm.hg in patients receiving antihypertensive drugs). Pregnancy, lactation. Life expectancy <6 months. Clinically significant liver disease. Creatinine clearance (estimated by Cockcroft-Gault) <30 ml / min. hemoglobin level <90 g/l), thrombocytopenia <100x10^9 / L. Patients who, in the opinion of the researcher, are not suitable for inclusion in the study, for example, due to the low likelihood of doctor's recommendations following. Long-term use of NSAIDs Current participation in another clinical study. Allergic to contrast substance or radioisotope drugs used in procedures to assess endpoints of the study, which according to researchers, may be a contraindication to the implementation of these research methods.", "candidate_expression": "((Allergic) AND (Contraindications Russian Instructions for medical use) AND (Creatinine clearance Cockcroft-Gault <30 ml / min) AND (Gastric ulcer) AND (Gastrointestinal bleeding in the previous 3 months) AND (Intracranial hemorrhage) AND (Intracranial pathology) AND (Life expectancy <6 months) AND (NSAIDs Long-term use) AND (Pregnancy) AND (Trauma) AND (acute ulcer endoscopically identified during previous 30 days) AND (anamnesis) AND (aneurysm) AND (antihypertensive drugs) AND (antiplatelet agents Indications concomitant) AND (arteriovenous fistula) AND (bleeding Active) AND (bleeding Clinically significant within the last 30 days) AND (bleeding diathesis) AND (clinical manifestations) AND (contrast substance) AND (diastolic blood pressure > 100 mm.hg) AND (duodenal ulcer) AND (endoscopically) AND (extensive surgery) AND (heart rate > 110 lasting more than 15 min) AND (hemodynamic instability) AND (hemoglobin level <90 g/l) AND (hypertension Uncontrolled) AND (lactation) AND (liver disease Clinically significant) AND (neoplasm malignant) AND (oral anticoagulation indication for) AND (pradaxa) AND (radioisotope drugs) AND (stroke within 6 months before randomization) AND (surgery planned in the next 6 months after randomization) AND (systolic blood pressure <100 mm Hg.St.) AND (systolic blood pressure > 180 mm Hg) AND (systolic blood pressure fall =40 mm Hg) AND (thrombocytopenia <100x10^9 / L) AND (tumor) AND (ventilatory support need for within 12 hours prior to randomisation) AND (warfarin) AND NOT (signs of scarring))"}
{"candidate_id": "LLM02344", "doc_id": "NCT00862446_inc", "case_bucket": "other", "source_criterion": "Infants in the newborn intensive care unit TPN cholestasis of at least 2.5 mg/dl Anticipated TPN treatment for at least one month signed informed consent", "candidate_expression": "((Infants) AND (TPN cholestasis) AND (TPN treatment) AND (at least 2.5 mg/dl) AND (for at least one month) AND (newborn intensive care unit) AND (signed informed consent))"}
{"candidate_id": "LLM02345", "doc_id": "NCT03637946_inc", "case_bucket": "or", "source_criterion": "Over 18 years of age; Systemically healthy; Non-smoking; With good oral hygiene; Absent irreversible pulpal alteration; With the presence of a non-carious cervical lesion (LCNCs) that needs to be restored. This lesion should be non-carious, non-retentive, with at least 1 mm and up to 3 mm depth, should involve both enamel and dentin of vital teeth without mobility, and present hypersensitivity; Presence a natural tooth of the same position of the restored tooth, but in the opposite arch of the same jaw to be considered for the positive control; Periodontal parameters : Depth Probing (PS), Visible Plaque Index (IPV), Gingival Index (GI) and Probing Bleed Index (SS). The normal included were: PS = 1 to 3 mm, GI = 0, IPV = score 0 e SS = score 0.", "candidate_expression": "((Depth Probing (PS)) AND (GI = 0) AND (Gingival Index (GI)) AND (IPV score 0) AND (Non-smoking) AND (PS = 1 to 3 mm) AND (Probing Bleed Index (SS)) AND (SS score 0) AND (Systemically healthy) AND (Visible Plaque Index (IPV)) AND (age Over 18 years) AND (depth at least 1 mm and up to 3 mm) AND (good oral hygiene) AND (hypersensitivity) AND (lesion non-carious non-retentive involve both enamel and dentin) AND (non-carious cervical lesion (LCNCs)) AND (restored needs to be) AND NOT (irreversible pulpal alteration))"}
{"candidate_id": "LLM02346", "doc_id": "NCT00639795_exc", "case_bucket": "or", "source_criterion": "Age less than 18 Clinical or laboratory evidence of systemic infection Current pregnancy as assessed by preoperative urine HCG test Serious, uncontrolled, non-malignant illness Malignant illness requiring systemic chemotherapy in the last 6 months Documented allergy to oxycodone, morphine sulfate or acetaminophen Contraindication to peripheral nerve blockade or general anesthesia including: 1. patient refusal 2. active infection at site of planned block 3. documented allergy to any local or general anesthetic medications 4. significant coagulopathy( prothrombin time >15 seconds, INR>1.5 5. pre-existing neuropathy and medical conditions or deformities which would compromise block or anesthetic safety Planned pleurodesis Current use of high dose inhaled or systemic steroids Current use of Amiodarone (Cordarone) Morbid obesity (BMI=40kg/m2) Patients with clinically significant mental health issues such as psychosis requiring treatment with antipsychotic medications. Patients unable to consent Patients with active infections requiring antibiotics within one month of registration Participation in other clinical trials that may interfere with this study", "candidate_expression": "((40kg/m2) AND (>1.5) AND (>15 seconds) AND (Age) AND (Amiodarone) AND (BMI) AND (Cordarone) AND (Current) AND (INR) AND (Malignant illness) AND (Morbid obesity) AND (Serious) AND (active) AND (allergy) AND (antibiotics) AND (antipsychotic medications) AND (clinically significant) AND (coagulopathy) AND (high dose) AND (in the last 6 months) AND (infections) AND (less than 18) AND (mental health issues) AND (neuropathy) AND (non-malignant illness) AND (pleurodesis) AND (pre-existing) AND (pregnancy) AND (preoperative) AND (prothrombin time) AND (psychosis) AND (significant) AND (steroids) AND (systemic chemotherapy) AND (treatment) AND (uncontrolled) AND (urine HCG test) AND (within one month of registration) AND ((acetaminophen) OR (morphine sulfate) OR (oxycodone)) AND ((Contraindication to general anesthesia) OR (Contraindication to peripheral nerve blockade)) AND ((inhaled) OR (systemic)))"}
{"candidate_id": "LLM02347", "doc_id": "NCT02678663_inc", "case_bucket": "other", "source_criterion": "Subjects over the age of 18 years who agree informed consent and who have at least one polyp of eligible size (6-10mm)", "candidate_expression": "((18 years over) AND (6-10mm) AND (age) AND (agree informed consent) AND (at least one) AND (eligible size) AND (polyp))"}
{"candidate_id": "LLM02348", "doc_id": "NCT02904785_exc", "case_bucket": "or", "source_criterion": "History of spinal cord stenosis or clinical symptoms of lumbar radiculopathy; History or onset neurological diseases; Generalized pain or fibromyalgia; Inability to walk; History of knee surgery in the target knee; Secondary causes of osteoarthritis; Use of statins and quinolones in the previous year; Uncontrolled and ongoing psychiatric diseases; Invasive knee treatments with hyaluronic acid infusion, corticosteroids and anaesthetics, in the target knee, up to 6 months previous to study inclusion.", "candidate_expression": "((Generalized pain) AND (History) AND (Inability to walk) AND (Invasive knee treatments) AND (Secondary causes) AND (Uncontrolled) AND (anaesthetics) AND (clinical symptoms) AND (corticosteroids) AND (fibromyalgia) AND (hyaluronic acid) AND (hyaluronic acid infusion) AND (in the previous year) AND (knee surgery) AND (lumbar radiculopathy) AND (neurological diseases) AND (ongoing) AND (onset) AND (osteoarthritis) AND (psychiatric diseases) AND (quinolones) AND (spinal cord stenosis) AND (statins) AND (study inclusion) AND (target knee) AND (up to 6 months previous))"}
{"candidate_id": "LLM02349", "doc_id": "NCT02384850_exc", "case_bucket": "or", "source_criterion": "adequately controlled with appropriate therapy or would compromise the patient's ability to tolerate this therapy; 2. Treatment with any systemic anticancer therapy ≤ 3 weeks prior to cycle 1 day 1 3. Uncontrolled active infection (Hepatitis B and C infection are NOT exclusion criteria) and/or known HIV infection; 4. Renal failure requiring haemodialysis or peritoneal dialysis; 5. Patients who are pregnant or breast-feeding; 6. Patients with significantly diseased or obstructed gastrointestinal tract, malabsorption, uncontrolled vomiting or diarrhea resulting in inability to swallow oral medications; 7. Presence of symptomatic CNS metastasis 8. Unresolved toxicity from previous anti-cancer therapy or incomplete recovery from surgery, in particular oxaliplatin-induced peripheral neuropathy > grade 1. 9. Any of the following within the 12 months prior to study drug administration: myocardial infarction, severe/unstable angina, coronary/peripheral artery bypass graft, symptomatic congestive heart failure, cerebrovascular accident or transient ischemic attack, pulmonary embolism, deep vein thrombosis, or other thromboembolic event.", "candidate_expression": "((CNS metastasis symptomatic) AND (HIV infection) AND (Renal failure) AND (Unresolved toxicity) AND (adequately controlled with appropriate therapy or would compromise the patient's ability to tolerate this therapy; 2.) AND (anti-cancer therapy previous) AND (breast-feeding significantly) AND (cerebrovascular accident) AND (coronary artery bypass graft) AND (deep vein thrombosis) AND (diarrhea) AND (diseased gastrointestinal tract) AND (haemodialysis) AND (inability to swallow oral medications) AND (incomplete recovery) AND (infection Uncontrolled active) AND (malabsorption) AND (myocardial infarction study drug administration) AND (obstructed gastrointestinal tract) AND (other thromboembolic event) AND (oxaliplatin) AND (peripheral artery bypass graft) AND (peripheral neuropathy oxaliplatin-induced) AND (peritoneal dialysis) AND (pregnant) AND (pulmonary embolism) AND (severe angina) AND (significantly) AND (surgery) AND (symptomatic congestive heart failure) AND (systemic anticancer therapy ≤ 3 weeks prior to cycle 1) AND (transient ischemic attack) AND (unstable angina) AND (vomiting uncontrolled) AND NOT (Hepatitis B infection) AND NOT (Hepatitis C infection))"}
{"candidate_id": "LLM02350", "doc_id": "NCT00396734_exc", "case_bucket": "or", "source_criterion": "use more than 2g a day; 5 times a week to everyday Subjects who are diagnosed as suffering from psychotic illness according to DSM-IV (Axis 1)22, or with a history of CNS disease, a history of infection that might affect CNS (HIV, syphilis, cytomegalovirus, herpes), or a history of head injury with loss of consciousness,pregnant women.", "candidate_expression": "((CNS disease) AND (DSM-IV Axis 1) AND (HIV) AND (cytomegalovirus) AND (head injury) AND (herpes) AND (history) AND (infection affect CNS) AND (loss of consciousness) AND (more than 2g a day 5 times a week to everyday) AND (pregnant) AND (psychotic illness) AND (syphilis))"}
```
