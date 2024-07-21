import os
from dotenv import load_dotenv

load_dotenv()
api_url = os.getenv('PRESTASHOP_LINK')
api_key = os.getenv('PRESTASHOP_KEY')
openai_key = os.getenv('OPENAI_KEY')

php_credentials = {
    'host': os.getenv('PHP_HOST'),
    'port': 3306,
    'user': os.getenv('PHP_USER'),
    'db': os.getenv('PHP_DB'),
    'password': os.getenv('PHP_PASSWORD')
}

# app_logic

ai_params = dict(classify_ai=0, descriptions_ai=1, meta_ai=1)

mode_help = 'Mode to operate the system.'
param_help = 'Brand to explore or CSV filename.'
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

php_query_check_quantity = "SELECT `unit_price_ratio` FROM `pr_product_shop` WHERE `id_product` = %s AND `id_shop` = 1"

php_query_update_quantity = ("UPDATE `pr_product_shop` SET `unit_price_ratio` = %s, "
                             "`unity` = 'za mililitr' WHERE `id_product` = %s AND `id_shop` = 1;")

quantity_ml_pattern = r'(\d+)\s*ml'
quantity_pack_pattern = r'(\d+)\s*x\s*(\d+)'

# utils

xml_read = {
    'xml_feed_link': 'data/shop_a_feed.xml',
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

# ai_operations

cats_dict_filepath = 'data/cats_dict.json'
openai_default_model = 'gpt-3.5-turbo-0125'
openai_default_temp = 0.25
openai_default_role = "You are writing ecommerce product descriptions."

max_tokens_description = 1900
max_tokens_enrichment = 1500
max_tokens_meta = 400
max_tokens_classification = 400


ai_prompts = {

    'prompt_description': """
        Your task: Expand and improve SEO product descriptions for ecommerce.
        Rules: Everything must be in Polish language except the product name.
        Add relevant information to improve descriptions, but never invent cosmetic's effects nor active ingredients.
        Format the descriptions with appropriate HTML tags for paragraphs. Do not add any additional formatting.
        product_name: {product_name} (important! never include product quantity like 'ml' in descriptions)
        product base description: {product_desc}
        Instructions:
        1. Firstly write 1800 characters long product description. Start only with 'LONG DESCRIPTION:' as a headline.
        Start with the product name and bold claim/main usage and then elaborate on the benefits and characteristics.
        Explain why cosmetic is worthy of buying - how it solves certain skin type problem and makes the user feel good 
        about taking care of his/her skin with the best beauty product. Include very subtle call to action in this part.
        After few paragraphs add newline 'Właściwości i Zalety kosmetyku:' followed by a list of about 8 elements 
        (Each element from newline and start with '&' sign) that would summarize cosmetics formula 
        (light cream, serum, etc), recommended skin type, main benefits and other important info.
        Do not include active ingredients here. Do not include info about how to use the product.
        2. Secondly write short product description in form of 5 bullet points. This part never exceeds 670 characters.
        Start with 'SHORT DESCRIPTION:' as a headline and proceed with a list.
        Each element from python-style newline and start with '&' sign. No paragrapth html tags in this part.
        Bullet contents and order: 1 of product intro with main claim/selling point &with repeated product name
        (without quantity), 1 about recommended skin type, 3 about benefits, 
        1 about who should buy it and why (be specific)
        """,

    'prompt_description_enrichment': """
        Your task: Extract active ingredients and mode of use form the base product description and improve it.
        Rules: Everything must be in Polish language.
        Include only active ingredients that are mentioned in the base description.
        Format the descriptions with appropriate HTML tags for paragraphs.
        base product  description: {product_desc}
        Instructions:
        1. Firstly, extract active ingredients of the cosmetic and improve it. Start only with 'SKŁADNIKI:' 
        as a headline and proceed with a bullet-point list.
        Each element of this list always starts from newline and '&' sign; less than 300 characters each.
        Each bullet must contain ingredient name, hyphen and the most relevant description and 
        benefit of having this ingredient in the cosmetic's formula and why it helps with product's main claim.
        Include only active ingredients that are mentioned in the base product description.
        You can add more benefits of the ingredients if suitable but never invent ingredients that are not there.
        2. Secondly write less than 600 characters long mode of use. 
        Start only with 'SPOSÓB UŻYCIA:' as a headline and proceed with a description.
        You should base yourself on the base product description, but can expand upon common knowledge if needed.
        """,

    'prompt_meta': """
        Your task: Write meta title and meta description for ecommerce based on short product description.
        Rules: Everything must be in Polish language except the product name.
        Follow Google best practices for writing meta descriptions.
        Never exceed the maximum character count specified in instructions for each step.
        Never include product quantity like 'ml' in description nor title
        product_name: {product_name}
        product base description: {product_desc}
        Instructions:
        1. Firstly write meta title. Start only with 'META TITLE:' as a headline. Capitalise new words.
        Always start with full product name and then add main cosmetic characteristic/claim after w hyphen. 
        Never exceed 70 characters in total.
        2. Secondly write meta description. This part must never exceed 160 characters including whitespaces punctuation.
        Start directly with most important product benefits and Never mention product name in this part.
        Enlist only some claims without elaborating. Make sure this part is shorter than 160 characters.
        """,

    'prompt_classification': """
        Your task: classify the product into ecommerce categories based on its short description and general knowledge.
        Do it step by step as specified in the instructions below.
        Product description: {product_desc}
        1. Firstly, classify the product to one of the MAIN categories: {cats[cat_main]}
        2. If it's a face cosmetic classify to at least one FORM subcategory: {cats[cat_face_form]} & 
        also classify to at least one ACTION subcategory: {cats[cat_face_action]}
        3. If it's a body (not face) cosmetic than classify to 1-3 body subcategory: {cats[cat_body]}
        4. If it's a hair cosmetic than classify to one and only one hair subcategory: {cats[cat_hair]}
        
        IMPORTANT: YOU CAN ONLY USE GIVEN SUBCATEGORIES NAMES - remain case sensitive.
        VERY IMPORTANT: For face care cosmetics, ensure you select at least one MAIN category AND one FORM subcategory 
        AND one ACTION subcategory (a minimum of 3 classifications in total).
        For hair and body cosmetics, select at least one main category and the respective subcategory.
        Always respond with a comma-separated list of the selected subcategories without any additional characters, 
        new lines, or redundant signs like []. etc. It should be easy to use in Python.
        FORMAT EXAMPLE: Pielęgnacja Twarzy, Kremy do twarzy, Kosmetyki nawilżające
        """
}
