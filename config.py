import os
from dotenv import load_dotenv

load_dotenv()
api_url = os.getenv('PRESTASHOP_LINK')
api_key = os.getenv('PRESTASHOP_KEY')
openai_key = os.getenv('OPENAI_KEY')

# app_logic

ai_params = dict(classify_ai=0, descriptions_ai=0, meta_ai=0, inci_unit=0)

mode_help = "Mode to operate the system."
param_help = "Brand to explore or CSV filename."
default_mode = 'explore'
default_brand = 'Mesoestetic'
csv_path = 'data/logs'

# processors

default_source_shop = 'shop_a'
product_ideas_path = 'data/logs/_product_ideas.csv'
product_indexes_path = 'data/logs/product_indexes.json'

net_price_factor = 1.87
default_prestashop_product_data = {"state": "1", "low_stock_alert": "0", "active": "0", "redirect_type": "404",
                                   "condition": "new", "show_price": "1", "indexed": "1", "visibility": "both"}
image_url_suffix = "-kosmetyki-urodama.jpg"

inci_header = '<p></p><p><strong>Skład INCI:</strong></p><p>'



# utils

xml_read = {
    'xml_feed_link': '../data/shop_a_feed.xml',
    'missing_tag': "MISSING",
    'tags': {
        'name': 'name',
        'desc': 'desc',
        'img_url': 'imgs/main'},
    'attrs': ['Producent', 'Kod_producenta', 'EAN']
}

brand_dict_path = 'data/brands_dict.json'

lang_format_fields = ['meta_description', 'meta_title', 'link_rewrite', 'name', 'description', 'description_short']
default_lang_format = {'language': {'attrs': {'id': '2'}}}
