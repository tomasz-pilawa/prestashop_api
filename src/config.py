import os
from dotenv import load_dotenv

load_dotenv()
api_url = os.getenv('URODAMA_LINK')
api_key = os.getenv('URODAMA_KEY')
openai_key = os.getenv('OPENAI_KEY')

ai_params = dict(classify_ai=0, descriptions_ai=0, meta_ai=0, inci_unit=0)
