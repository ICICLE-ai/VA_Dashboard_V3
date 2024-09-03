import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.absolute()) + '/../..')
from text_to_query.pangu.ppod_api import PanguForPPOD

pangu = PanguForPPOD(llm_name='gpt-4o')
