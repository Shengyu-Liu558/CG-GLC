$ErrorActionPreference = "Stop"

python src/criteria_boolean/prepare_llm_eval_dataset.py --full-dataset
python src/criteria_boolean/export_gpt_eval_batches.py --batch-size 25
python src/criteria_boolean/generate_human_eval_sample.py --sample-size 50
