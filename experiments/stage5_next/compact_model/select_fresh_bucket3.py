"""Create a fresh, population-proportional cohort for a frozen confirmation."""
import json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_compact_model as selection

selection.BUCKETS=(3,)
selection.PER_BUCKET=500
samples,spec,excluded=selection.select_samples()
meta={'seed_split':selection.SPLIT_SEED,'seed_sample':selection.SAMPLE_SEED,'bucket':'3','size':len(samples),'spec':spec['3'],'previous_validation_ids_excluded':excluded}
(Path(__file__).resolve().parent/'sample_bucket3.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
print(json.dumps(meta,indent=2))
