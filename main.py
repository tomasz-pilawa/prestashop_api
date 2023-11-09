import json
import os
import openai
from prestapyt import PrestaShopWebServiceDict

import mapping
import editing as e
import ai_boosting

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')
openai.api_key = os.getenv('openai_api')

prestashop = PrestaShopWebServiceDict(api_url, api_key)

# Update XML file from time to time
# mapping.get_xml_from_web(source='aleja')


# Check which products to introduce, get their ids and verify the initial data
# editing.select_products_xml(source='luminosa', mode='brands', print_info=1, data=['Mesoestetic'])
# editing.select_products_xml(source='ampari', mode='brands', data=['Colway'], print_info=1)


# Add simple version of selected products (preferably ID-based) & correct essential information (name, price, sku, ean)
def add_product_from_xml(select_source=None, select_mode=None, select_data=None, process_max_products=2):
    products = e.select_products_xml(source=select_source, mode=select_mode, data=select_data)
    products = e.process_products(products, max_products=process_max_products)
    e.add_with_photo(products)


# id_list = [620, 621, 624, 637, 639, 641, 643, 645, 653, 654, 655, 659, 663, 664, 666, 923, 1256, 2054, 2141, 2353]
# e.add_product_from_xml(select_source='ampari', select_mode='include', select_data=id_list, process_max_products=30)


# After adding or while editing only always use csv to improve specific products (works on ids too)
def improve_products(file_path_fix=None, classify_ai=0, descriptions_ai=0, meta_ai=0, features_ai=0):

    product_ids = e.fix_data_from_csv(file_path=file_path_fix)

    if classify_ai:
        ai_boosting.classify_categories(product_ids)
    if descriptions_ai:
        ai_boosting.write_descriptions_2(product_ids)
    if meta_ai:
        ai_boosting.write_meta(product_ids)
    if features_ai:
        # ai_boosting.configure_features(products_ids)
        pass

    mapping.update_everything(product_ids=product_ids)


# new_id_list = [811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822]
# editing.improve_products(file_path_fix='data/logs/adding_3_1.csv',
#                          classify_ai=0, descriptions_ai=1, features_ai=0)


# Fixer
# prestashop.delete('products', [792, 793])
