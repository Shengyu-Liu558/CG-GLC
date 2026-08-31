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
{"candidate_id": "LLM06001", "doc_id": "NCT02321839_exc", "case_bucket": "or", "source_criterion": "Total lesion area of >12 DA or >30.5 mm2 The existence of subretinal hemorrhage area constituting =50% of total lesion area The existence of scar or fibrosis area constituting =50% of total lesion area The existence of RPE tear Prior treatment for wet AMD History of vitrectomy surgery, submacular surgery, or other surgical intervention for AMD The pregnant or lactating woman", "candidate_expression": "((AMD) AND (RPE tear Prior) AND (Total lesion area) AND (subretinal hemorrhage area =50% of total lesion area) AND (treatment) AND (woman) AND ((submacular surgery) OR (surgical intervention other) OR (vitrectomy surgery)) AND ((>12 DA) OR (>30.5 mm2)) AND ((lactating) OR (pregnant)) AND ((fibrosis area) OR (scar area)))"}
{"candidate_id": "LLM06002", "doc_id": "NCT02942303_exc", "case_bucket": "or", "source_criterion": "Patients with previous periorbital/forehead surgery Patients who plucked the upper eyebrow margin Patients with eyebrow tatoos Patients with upper face botulinum toxin injection in the past 12 months Patients with resorbable upper face fillers injection in the past 12 months Patients with previous permanent upper face fillers injection Pregnant patients Lactating patients Patients with preexisting neuromuscular conditions (myasthenia gravis, Eaton Lambert syndrome) Patients using medication that could potentiate the effect of botulinum (ex: aminoglycoside antibiotics) Patients with sensitivity to botulinum toxin or human albumin", "candidate_expression": "((Eaton Lambert syndrome) AND (Lactating) AND (Pregnant) AND (aminoglycoside antibiotics) AND (botulinum) AND (botulinum toxin) AND (botulinum toxin injection upper face in the past 12 months) AND (eyebrow tatoos) AND (forehead surgery) AND (human albumin) AND (medication) AND (myasthenia gravis) AND (neuromuscular conditions) AND (periorbital surgery) AND (permanent fillers injection upper face) AND (plucked the upper eyebrow margin) AND (potentiate the effect) AND (resorbable fillers injection upper face in the past 12 months) AND (sensitivity))"}
{"candidate_id": "LLM06003", "doc_id": "NCT00351611_inc", "case_bucket": "other", "source_criterion": "Epilepsy partial seizure subjects. Currently taking 1 to 3 antiepileptic drugs.", "candidate_expression": "((1 to 3) AND (Epilepsy) AND (antiepileptic drugs) AND (partial seizure))"}
{"candidate_id": "LLM06004", "doc_id": "NCT02201316_exc", "case_bucket": "or", "source_criterion": "Current or chronic history of liver disease, or known hepatic or biliary abnormalities (with the exception of Gilbert's syndrome or asymptomatic gallstones). History of regular alcohol consumption within 6 months of the study defined as: An average weekly intake of >21 units for males or >14 units for females. One unit is equivalent to 8 gram of alcohol: a half-pint (approximately 240 milliliter [mL]) of beer, 1 glass (100 mL) of wine or 1 (25 mL) measure of spirits. History of sensitivity to heparin or heparin-induced thrombocytopenia. History of sensitivity to any of the study medications, or components thereof or a history of drug or other allergy that, in the opinion of the investigator or GSK Medical Monitor, contraindicates their participation. Gastrointestinal disease or with gastrointestinal surgical history which can affect the absorption of the investigational product. A positive pre-study Hepatitis B surface antigen or positive Hepatitis C antibody result within 3 months of screening Urinary cotinine levels indicative of smoking or history or regular use of tobacco- or nicotine-containing products within 6 months prior to screening. A positive pre-study drug/alcohol screen. A positive test for Human Immunodeficiency Virus (HIV) antibody. Pregnant females as determined by positive serum hCG test at screening or prior to dosing. Where participation in the study would result in donation of blood or blood products in excess of 500 mL within a 90 day period. Lactating females. The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer). Exposure to more than four new chemical entities within 12 months prior to the first dosing day.", "candidate_expression": "((>14 units) AND (>21 units) AND (Current) AND (Gastrointestinal disease) AND (Gilbert's syndrome) AND (Hepatitis B surface antigen) AND (Hepatitis C antibody) AND (History) AND (Human Immunodeficiency Virus (HIV) antibody) AND (Lactating) AND (Pregnant) AND (The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer).) AND (Urinary cotinine levels) AND (affect the absorption of the investigational product) AND (alcohol screen) AND (allergy) AND (asymptomatic) AND (at screening) AND (average weekly intake) AND (biliary abnormalities) AND (chronic) AND (contraindicates their participation) AND (dosing) AND (drug allergy) AND (drug screen) AND (exception) AND (females) AND (gallstones) AND (gastrointestinal surgical) AND (gastrointestinal surgical history) AND (heparin) AND (heparin-induced) AND (heparin-induced thrombocytopenia) AND (hepatic abnormalities) AND (history) AND (in the opinion of the investigator or GSK Medical Monitor) AND (liver disease) AND (males) AND (more than four) AND (new chemical entities) AND (positive) AND (pre-study) AND (prior to dosing) AND (regular alcohol consumption) AND (regular use of nicotine-containing products) AND (regular use of tobacco) AND (screening) AND (sensitivity to any of the study medications) AND (sensitivity to heparin) AND (serum hCG test) AND (smoking) AND (study medications) AND (the first dosing day) AND (the study) AND (within 12 months prior to the first dosing day) AND (within 3 months of screening) AND (within 6 months of the study) AND (within 6 months prior to screening))"}
{"candidate_id": "LLM06005", "doc_id": "NCT03004261_inc", "case_bucket": "or", "source_criterion": "Any allogeneic stem cell transplant recipient = 14 years of age and = 60 years of age Bilirubin/ SGOT/SGPT < 5 × upper normal limits. Creatinine < 2 × upper normal limits. Ejection fraction = 50%, no severe arrhythmia. Estimated life expectancy = 6 months. Patients' CMV-DNA = 1000cp/ml in treatment group and being negative in prophylactic group.", "candidate_expression": "((< 2 × upper normal limits) AND (< 5 × upper normal limits) AND (= 1000cp/ml) AND (= 14 years) AND (= 50%) AND (= 6 months) AND (= 60 years) AND (Bilirubin) AND (CMV-DNA) AND (Creatinine) AND (Estimated life expectancy) AND (SGOT) AND (SGPT) AND (age) AND (allogeneic stem cell transplant) AND (negative) AND (no) AND (severe) AND ((Ejection fraction) OR (arrhythmia)) AND ((prophylactic group) OR (treatment group)))"}
{"candidate_id": "LLM06006", "doc_id": "NCT03328052_inc", "case_bucket": "or", "source_criterion": "Patients with a clinical diagnosis of depression who in the judgement of their physician require medication management may be eligible for enrollment. A score of 10 or more on the PHQ-9 instrument will be required for enrollment. Some practices utilize the PHQ-2 and PHQ-9 are part of routine screening for depression. If the tests are performed routinely, they do not need to be repeated for study eligibility, and may be performed prior to informed consent for this study. If, however, the PHQ-9 is not routinely performed, informed consent must be performed prior to administration. Patients with a score below 10 will be considered screen failures and will not be enrolled or offered the MYnd testing. Patients with non-psychotic comorbid conditions may be included. Patients must be either medication treatment naïve for behavioral illnesses or have no active medication treatments for at least 1 month prior to enrollment. Prohibited medications at the time of enrollment will include stimulants, benzodiazepines and THC. Prior therapy with these agents is permitted with a washout of >30 days. Patients must have private medical insurance coverage through Horizon Blue Cross Blue Shield. This is limited to insured commercial members, including HMO, and excluding, for the avoidance of doubt, members of self-insured customers or Medicare or Medicaid programs.", "candidate_expression": "((PHQ-9) AND (active) AND (behavioral illnesses) AND (depression) AND (for at least 1 month prior to enrollment) AND (medication) AND (naïve) AND (no) AND (non-psychotic conditions) AND (score of 10 or more) AND ((THC) OR (benzodiazepines) OR (stimulants)))"}
{"candidate_id": "LLM06007", "doc_id": "NCT01735955_exc", "case_bucket": "or", "source_criterion": "Patient has been permanently discontinued from nilotinib treatment in the parent study due to unacceptable toxicity, non-compliance to study procedures, withdrawal of consent or any other reason Patient has participated in a Novartis sponsored combination trial where nilotinib was dispensed in combination with another study medication and patient is still receiving combination therapy Patients who are currently receiving treatment with any medications that have the potential to prolong the QT interval or inducing Torsade de Pointes and the treatment cannot be either safely discontinued at least one week prior to nilotinib treatment or switched to a different medication prior to start of nilotinib treatment and for the duration of the study Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hcG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception during the study and for 30 days after the final dose of nilotinib.", "candidate_expression": "((Pregnant hcG laboratory test) AND (Women) AND (any medications have the potential to prolong the QT interval inducing Torsade de Pointes) AND (any other reason Novartis sponsored) AND (child-bearing potential) AND (lactating) AND (nilotinib) AND (non-compliance) AND (nursing) AND (participated in a combination trial) AND (physiologically capable of becoming pregnant) AND (study procedures) AND (treatment currently) AND (unacceptable toxicity) AND (women) AND NOT (contraception highly effective methods during the study for 30 days after the final dose of nilotinib) AND NOT (treatment) AND NOT (consent))"}
{"candidate_id": "LLM06008", "doc_id": "NCT03099863_inc", "case_bucket": "or", "source_criterion": "Adult women at least 18 years of age Elective Female Pelvic Medicine and Reconstructive Surgery or Gynecologic Minimally Invasive surgeries including hysterectomy, suburethral sling, and pelvic organ prolapse repair that require cystoscopy.", "candidate_expression": "((Adult) AND (Elective) AND (Female Pelvic) AND (Gynecologic) AND (Medicine) AND (Minimally Invasive) AND (Reconstructive Surgery) AND (age) AND (at least 18 years) AND (cystoscopy) AND (hysterectomy) AND (pelvic organ prolapse repair) AND (require) AND (suburethral sling) AND (surgeries) AND (women))"}
{"candidate_id": "LLM06009", "doc_id": "NCT01806558_exc", "case_bucket": "or", "source_criterion": "1. Are unable to understand and sign the consent form 2. Are pregnant or lactating 3. Are physically unable to sit upright and still for 40 minutes 4. Have undergone bilateral mastectomy 5. Are not scheduled to undergo conventional ultrasound", "candidate_expression": "((Are unable to understand and sign the consent form) AND (bilateral mastectomy) AND (conventional ultrasound) AND (for 40 minutes) AND (lactating) AND (not) AND (physically unable to sit upright and still) AND (pregnant) AND (scheduled))"}
{"candidate_id": "LLM06010", "doc_id": "NCT03236246_exc", "case_bucket": "other", "source_criterion": "Serum phosphate <3.0 mg/dL Intravenous (IV) iron administered within 4 weeks prior to Screening Erythropoiesis-stimulating agents (ESA) administered within 4 weeks prior to Screening Blood transfusion within 4 weeks prior to Screening", "candidate_expression": "((Blood transfusion within 4 weeks prior to Screening) AND (ESA within 4 weeks prior to Screening) AND (Erythropoiesis-stimulating agents) AND (Serum phosphate <3.0 mg/dL) AND (iron Intravenous within 4 weeks prior to Screening IV))"}
{"candidate_id": "LLM06011", "doc_id": "NCT01801072_inc", "case_bucket": "or", "source_criterion": "Adult (=18 years) Presence of intracranial aneurysm (with or without rupture) Treating surgeon has recommended surgical repair of the aneurysm", "candidate_expression": "((Adult) AND (aneurysm) AND (intracranial aneurysm) AND (surgical repair recommended) AND (years =18 years) AND ((with rupture) OR (without rupture)))"}
{"candidate_id": "LLM06012", "doc_id": "NCT02330705_inc", "case_bucket": "or", "source_criterion": "Mild male factor infertility or unexplained infertility.", "candidate_expression": "((male factor infertility Mild) OR (unexplained infertility))"}
{"candidate_id": "LLM06013", "doc_id": "NCT02525991_exc", "case_bucket": "or", "source_criterion": "Patient diagnosed with dementia. Patients with serious and unstable illnesses including current hepatic, renal, gastroenterologic, respiratory, cardiovascular (including ischemic heart disease and congestive heart failure), endocrinologic, neurologic (including stroke, transient ischemic attack, subarachnoidal bleeding, brain tumor, encephalopathy, and meningitis). Patients with a history of allergic reactions to loxapine or amoxapine Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded. Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device.", "candidate_expression": "((Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device) AND (Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded) AND (allergic reactions) AND (amoxapine) AND (brain tumor) AND (cardiovascular) AND (congestive heart failure) AND (dementia) AND (encephalopathy) AND (endocrinologic) AND (gastroenterologic) AND (hepatic) AND (ischemic heart disease) AND (loxapine) AND (meningitis) AND (neurologic) AND (renal) AND (respiratory) AND (serious) AND (stroke) AND (subarachnoidal bleeding) AND (transient ischemic attack) AND (unstable))"}
{"candidate_id": "LLM06014", "doc_id": "NCT01078051_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06015", "doc_id": "NCT03407625_inc", "case_bucket": "or", "source_criterion": "37 weeks gestation or greater Living, singleton fetus No major fetal malformations Cephalic presentation No prior uterine scar Intact fetal membranes Qualifies for prostaglandin administration according to current Parkland protocol Have a cervical dilation of 2 centimeters or less, measured at the level of the internal os Have an indication for induction or attempted induction of labor according to Parkland protocol", "candidate_expression": "((Cephalic presentation) AND (Parkland protocol) AND (cervical dilation 2 centimeters or less internal os) AND (fetal membranes Intact) AND (gestation 37 weeks greater) AND (indication) AND (prostaglandin administration) AND (singleton fetus Living) AND NOT (major fetal malformations) AND NOT (uterine scar) AND ((induction attempted) OR (induction of labor)))"}
{"candidate_id": "LLM06016", "doc_id": "NCT02548013_inc", "case_bucket": "other", "source_criterion": "1. PPROM with gestational age between 27 to 34 weeks 2. Cephalic presentation 3. Clear amniotic fluid 4. Oral temperature > 38 C 5. Near distance from the hospital (the patient can reach hospital within one hour ) 6. Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home . 7. Maternal and fetal condition remain stable after hospitalization for 72 hours", "candidate_expression": "((Cephalic presentation) AND (Clear amniotic fluid) AND (Home environment safe and amenable to rest , availability of family support such as a sister or mother who will help the patient at home .) AND (Maternal condition) AND (Near distance from the hospital (the patient can reach hospital within one hour )) AND (Oral temperature > 38 C) AND (PPROM) AND (fetal condition) AND (gestational age between 27 to 34 weeks))"}
{"candidate_id": "LLM06017", "doc_id": "NCT03388840_exc", "case_bucket": "or", "source_criterion": "Patients with Non-androgenetic causes of hair loss. Female patients with androgenetic alopecia. Patients who received anti-hair loss treatment within the past six months. Patients with history of bleeding disorders or on anticoagulant therapy. Patients with history of chronic liver disease, cancer or connective tissue disorders. Patients with current scalp infection.", "candidate_expression": "((Female) AND (Non-androgenetic causes of hair loss) AND (androgenetic alopecia) AND (anti-hair loss treatment within the past six months) AND (anticoagulant therapy) AND (bleeding disorders) AND (cancer) AND (chronic liver disease) AND (connective tissue disorders) AND (scalp infection current))"}
{"candidate_id": "LLM06018", "doc_id": "NCT02959801_exc", "case_bucket": "or", "source_criterion": "presence of subacute or chronic DVT more than 21 days in duration, inability to lie in the prone position required for intervention, terminal systemic disease requiring palliative treatment, active bleeding (from a gastric/duodenal ulcer or the cerebrovascular system), a haemorrhagic stroke within the previous year, an impaired bleeding-clotting profile, and any haemophilic disorder, or pregnancy.", "candidate_expression": "((DVT) AND (active) AND (bleeding) AND (cerebrovascular system) AND (chronic) AND (duodenal ulcer) AND (gastric ulcer) AND (haemophilic disorder) AND (haemorrhagic stroke) AND (impaired bleeding-clotting profile) AND (inability to lie in the prone position) AND (more than 21 days in duration) AND (palliative treatment) AND (pregnancy) AND (requiring) AND (subacute) AND (terminal systemic disease) AND (within the previous year))"}
{"candidate_id": "LLM06019", "doc_id": "NCT03124329_exc", "case_bucket": "or", "source_criterion": "Molar teeth Milller Class 4 recession defects Pregnancy (Self-reported) Smoking Uncontrolled local or systemic diseases that affects wound healing (diabetes, autoimmune or inflammatory disorders) Past history of systemic steroid use over 2 weeks within the last 2 years Poor oral hygiene on a non-compliant individual Ibuprofen Allergy/interlerance Anticoagulant therapy (e.g. Warfarin, Plavix, etc.), will not be automatic exclusion but patients will be required to have INR test performed and have values between 2.0 to 3. Physician consultation will be requested to determine whether anticoagulant therapy can be discontinued for 3 days prior to surgery. Objection to blood draw or application of blood products Students and staff from USC Ostrow school of Dentistry will not be recruited for this study", "candidate_expression": "((Allergy) AND (Anticoagulant therapy) AND (INR test between 2.0 to 3) AND (Ibuprofen) AND (Milller Class 4) AND (Molar teeth) AND (Plavix) AND (Poor oral hygiene) AND (Pregnancy) AND (Smoking) AND (Warfarin) AND (anticoagulant therapy) AND (autoimmune disorders) AND (diabetes) AND (diseases local) AND (inflammatory disorders) AND (interlerance) AND (non-compliant) AND (recession defects) AND (systemic diseases) AND (systemic steroid Past history over 2 weeks within the last 2 years))"}
{"candidate_id": "LLM06020", "doc_id": "NCT01815580_exc", "case_bucket": "or", "source_criterion": "Prior receipt of investigational anti-HIV vaccine Ongoing therapy with any of the following: Systemic corticosteroids. Short course less than or equal to 21 days of corticosteroids is allowed; Systemic chemotherapeutic agents; Nephrotoxic systemic agents, including aminoglycosides, amphotericin B, cidofovir, cisplatin, foscarnet, pentamidine; Immunomodulatory treatments including Interleukin-2; Investigational agents Known allergy/sensitivity or any hypersensitivity to components of study drugs (ART) or their formulations Active drug or alcohol use or dependence that would interfere with adherence to study requirements Serious medical or psychiatric illness that would interfere with the ability to adhere to study requirements Chronic or acute hepatitis B infection Use of female hormonal products based on estrogen or derivatives", "candidate_expression": "((ART) AND (Chronic hepatitis B infection) AND (Immunomodulatory treatments) AND (Interleukin-2) AND (Investigational agents) AND (Nephrotoxic systemic agents) AND (Systemic chemotherapeutic agents) AND (Systemic corticosteroids less than or equal to 21 days) AND (acute hepatitis B infection) AND (alcohol dependence) AND (alcohol use) AND (allergy) AND (aminoglycosides) AND (amphotericin B) AND (anti-HIV vaccine Prior investigational) AND (cidofovir) AND (cisplatin) AND (components of study drugs) AND (drug dependence) AND (female hormonal products estrogen estrogen derivatives) AND (foscarnet) AND (hypersensitivity) AND (medical illness) AND (or their formulations) AND (pentamidine) AND (psychiatric illness) AND (sensitivity) AND (therapy Ongoing) AND (use) AND NOT (corticosteroids Short course))"}
{"candidate_id": "LLM06021", "doc_id": "NCT02231892_exc", "case_bucket": "or", "source_criterion": "1. Personal history of stroke, brain lesions, previous neurosurgery, any personal history of seizure or fainting episode of unknown cause, or head trauma resulting in loss of consciousness, lasting over 30 minutes or with sequela lasting longer than two days. Justification: Stroke or head trauma can lower the seizure threshold, and are therefore contra-indications for TMS. Fainting episodes or syncope of unknown cause could indicate an undiagnosed condition associated with seizures. Screening tool: TMS adult safety questionnaire, Medical History. 2. First-degree family history of any neurological disorder with a potentially hereditary basis, including migraines, epilepsy, or multiple sclerosis. 1. Justification: Neurological disorders can lower the seizure threshold, and are therefore contra-indications for TMS. First-degree family history of certain neurological disorders with a hereditary component increases the risk of the subject having an undiagnosed condition that is associated with lowered seizure threshold. 2. Screening tool: TMS adult safety screening, Medical History. 3. Cardiac pacemakers, neural stimulators, implantable defibrillator, implanted medication pumps, intracardiac lines, or acute, unstable cardiac disease, with intracranial implants (e.g. aneurysm clips, shunts, stimulators, cochlear implants, or electrodes) or any other metal object within or near the head that precludes MRI scanning. 1. Justification: Any metal around the head is a contraindication for both MRI and TMS, as both methods involve exposure to a relatively strong magnetic field. 2. Screening tool: TMS adult safety screening, MRI safety screening, Medical History. 4. Noise-induced hearing loss or tinnitus. 1. Justification: individuals with noise-induced hearing problems may be particularly vulnerable to the acoustic noise generated by TMS and MRI equipment. 2. Screening tools: TMS adult safety screening. 5. Current use (any use in the past 4 weeks, chronic use within 6 past six months) of any investigational drug or of any medications with psychotropic, anti or pro-convulsive action. 1. Justification: The use of certain medications or drugs can lower seizure threshold and is therefore contra-indicated for TMS. 2. Screening tools: MRI safety screening questionnaire, Medical history, Medical Assessments: Urine toxicology analyzes for presence of a broad range of prescription and nonprescription drugs. 6. Lifetime history of major depressive disorder, schizophrenia, bipolar disorder, mania, or hypomania. 1. Justification: The population of interest here is a healthy control population with no psychiatric disorders. In subjects with depression, bipolar disorder, mania or hypomania, there is a small chance that TMS can trigger (hypo)manic symptoms. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counsellor. 7. Meet current DSM V criteria for moderate to severe substance use disorder (excluding nicotine), smoke daily, or urine toxicology positive for any illicit substance inconsistent with history given. 1. Justification: The population of interest here is a healthy control population with no substance use disorder. Current use of illicit substances could impact on seizure threshold and is therefore contra-indicated for TMS. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counsellor, Drug Use Survey (DUS), Substance Use Disorder Evaluation, Medical Assessments: urine qualitative drug screen is performed for methadone, benzodiazepines, cocaine, amphetamine/methamphetamine, opiates, barbiturates, and tetrahydrocannabinol. 8. Have met DSM V criteria for moderate to severe substance use disorder (excluding nicotine, alcohol and cannabis) in the past, or have met DSM V criteria for moderate to severe substance use disorder for cannabis or alcohol in the past 5 years. 1. Justification: the population of interest here is a healthy control population with no present or past substance use disorder. 2. Screening tools: SCID Screen Patient Questionnaire. Potential diagnoses will be further evaluated by a counselor. Drug Use Survey (DUS), Substance Use Disorder Evaluation. 9. History of myocardial infarction, angina, congestive heart failure, cardiomyopathy, stroke or transient ischemic attack, or any heart condition currently under medical care. 1. Justifications: the risk of TMS for individuals with a heart condition is unknown. 2. Screening tool: physical assessment (EKG), medical history. 10. Pregnant women or women with reproductive potential who are sexually active and not using an acceptable form of contraception. 1. Justification: it is unknown whether TMS poses a risk to fetuses. 2. Screening tool: Medical assessments (urine pregnancy test) at the beginning of each visit that involves TMS or MRI. 11. History of learning disability or current ADHD 1. Justification: Subjects should be able to perform cognitive tasks to a high degree of accuracy, both in the MRI scanner and outside the scanner. Subjects with ADHD/LD may engage different neural circuitry even if they can perform the tasks. 2. Screening tool: Wechsler Abbreviated Scale of Intelligence, Medical history, Adult ADHD Self-Report Scale. 12. Participation in an rTMS session less than two weeks ago. 1. Justification: in order to limit exposure to TMS, we will not enroll subjects who have received TMS less than two weeks ago. 2. Screening tool: TMS safety screening questionnaire.", "candidate_expression": "((ADHD) AND (ADHD current) AND (Adult ADHD Self-Report Scale) AND (Cardiac pacemakers) AND (DSM V criteria Meet) AND (DSM V criteria met) AND (Drug Use Survey (DUS)) AND (LD) AND (MRI) AND (MRI safety screening) AND (MRI safety screening questionnaire) AND (Medical History) AND (Medical assessments at the beginning of each visit) AND (Medical history) AND (Noise-induced hearing loss) AND (Potential diagnoses will be further evaluated by a counselor.) AND (Pregnant) AND (SCID Screen Patient Questionnaire) AND (Screening) AND (Substance Use Disorder Evaluation) AND (TMS) AND (TMS adult safety questionnaire) AND (TMS adult safety screening) AND (TMS adult safety screening Current use any use chronic use) AND (TMS safety screening questionnaire) AND (Urine toxicology analyzes prescription) AND (Wechsler Abbreviated Scale of Intelligence) AND (acceptable form of) AND (alcohol) AND (aneurysm clips) AND (angina) AND (bipolar disorder) AND (brain lesions) AND (cannabis) AND (cardiac disease acute unstable) AND (cardiomyopathy) AND (cochlear implants) AND (congestive heart failure) AND (drugs nonprescription) AND (electrodes) AND (epilepsy) AND (fainting episode unknown cause) AND (head trauma resulting in loss of consciousness lasting over 30 minutes) AND (heart condition under medical care) AND (hypomania) AND (illicit substance inconsistent with history) AND (implantable defibrillator) AND (implanted medication pumps) AND (inconsistent with history) AND (intracardiac lines) AND (intracranial implants) AND (investigational drug) AND (lasting longer than two days) AND (learning disability History) AND (major depressive disorder) AND (mania) AND (medications psychotropic action pro-convulsive action) AND (metal object within or near the head precludes MRI scanning) AND (migraines) AND (multiple sclerosis) AND (myocardial infarction) AND (neural stimulators) AND (neurological disorder potentially hereditary basis) AND (neurosurgery previous) AND (rTMS session less than two weeks ago) AND (reproductive potential) AND (safety screening questionnaire) AND (schizophrenia) AND (seizure) AND (sequela) AND (sexually active) AND (shunts) AND (smoke daily) AND (stimulators) AND (stroke) AND (substance use disorder moderate to severe) AND (substance use disorder moderate to severe in the past) AND (substance use disorder moderate to severe in the past 5 years) AND (tinnitus) AND (transient ischemic attack) AND (urine pregnancy test) AND (urine toxicology positive) AND (women) AND NOT (nicotine) AND NOT (alcohol) AND NOT (cannabis) AND NOT (MRI scanning) AND NOT (contraception acceptable form of))"}
{"candidate_id": "LLM06022", "doc_id": "NCT02299947_exc", "case_bucket": "or", "source_criterion": "Prior trombosis or myocardial infarction, congenital coagulation disorder, use of anti-coagulants prior to surgery, prior thoracic surgery, pregnancy, pre-operative fibrinogen concentration <1g/L", "candidate_expression": "((anti-coagulants prior to surgery) AND (congenital coagulation disorder) AND (fibrinogen concentration pre-operative <1g/L) AND (myocardial infarction) AND (pregnancy) AND (thoracic surgery prior) AND (trombosis Prior))"}
{"candidate_id": "LLM06023", "doc_id": "NCT03356834_exc", "case_bucket": "or", "source_criterion": "Co-infected with HCV, HIV or other viral hepatitis, Diagnosis of HCC", "candidate_expression": "((HCC) AND (HCV) AND (HIV) AND (viral hepatitis other))"}
{"candidate_id": "LLM06024", "doc_id": "NCT02759861_exc", "case_bucket": "or", "source_criterion": "Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active. Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety. Malignancy diagnosed or treated within 5 years (recent localized treatment of squamous or non-invasive basal cell skin cancers is permitted; cervical carcinoma in situ is allowed if appropriately treated prior to screening); subjects under evaluation for a malignancy are not eligible. Infection with hepatitis B virus (HBV) or human immunodeficiency virus (HIV) Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit. Known hypersensitivity to LDV/SOF", "candidate_expression": "((LDV) AND (Malignancy) AND (Pregnant women and nursing mothers are ineligible due to the possible risk of adverse effects in the newborn. Eligible patients of reproductive potential should use adequate contraception if sexually active.) AND (SOF) AND (Serious concurrent medical illness which would jeopardize the ability of the subject to receive the therapy as outlined in this protocol with reasonable safety.) AND (Use of any prohibited concomitant medications within 30 days of the Baseline/Day 1 visit.) AND (allowed) AND (appropriately) AND (cervical carcinoma in situ) AND (hepatitis B virus (HBV)) AND (human immunodeficiency virus (HIV)) AND (hypersensitivity) AND (localized) AND (non-invasive basal cell skin cancer) AND (permitted) AND (prior to screening) AND (recent) AND (squamous cell skin cancer) AND (treated) AND (treatment) AND (within 5 years))"}
{"candidate_id": "LLM06025", "doc_id": "NCT02566863_exc", "case_bucket": "or", "source_criterion": "patient's refusal contraindications to dexmedetomidine diseases/drugs that influence on autonomic nervous system activity", "candidate_expression": "((contraindications) AND (dexmedetomidine) AND (patient's refusal) AND ((diseases influence on autonomic nervous system activity) OR (drugs influence on autonomic nervous system activity)))"}
```
