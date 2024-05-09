import os
from dotenv import load_dotenv

load_dotenv()
api_url = os.getenv('PRESTASHOP_LINK')
api_key = os.getenv('PRESTASHOP_KEY')
openai_key = os.getenv('OPENAI_KEY')

ai_params = dict(classify_ai=0, descriptions_ai=0, meta_ai=0, inci_unit=0)

# editing

xml_feed_link = 'data/{}_feed.xml'
json_helper = 'data/brands_dict.json'
product_ideas_path = 'data/logs/_product_ideas.csv'

net_price_factor = 1.87