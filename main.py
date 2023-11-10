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
# e.select_products_xml(source='luminosa', mode='brands', print_info=1, data=['Mesoestetic'])
# e.select_products_xml(source='aleja', mode='brands', data=['Urgo', 'Xylogic'], print_info=1)


# Add simple version of selected products (preferably ID-based) & correct essential information (name, price, sku, ean)
def add_product_from_xml(select_source=None, select_mode=None, select_data=None, process_max_products=2):
    products = e.select_products_xml(source=select_source, mode=select_mode, data=select_data)
    products = e.process_products(products, max_products=process_max_products)
    e.add_with_photo(products)


# id_list = [4695, 4763, 4915, 5112, 5557]
# add_product_from_xml(select_source='aleja', select_mode='include', select_data=id_list, process_max_products=30)


def improve_products(fix_source=None, classify_ai=0, descriptions_ai=0, meta_ai=0, features_ai=0, inci_unit=0):

    product_ids = e.fix_products(source=fix_source)

    if classify_ai:
        ai_boosting.classify_categories(product_ids)
    if descriptions_ai:
        ai_boosting.write_descriptions_2(product_ids)
    if meta_ai:
        ai_boosting.write_meta(product_ids)
    if features_ai:
        # ai_boosting.configure_features(products_ids)
        pass
    if inci_unit:
        e.fill_inci(limit=20, product_ids=product_ids, source='aleja')
        e.set_unit_price_api_sql(limit=20, product_ids=product_ids)

    mapping.update_everything(product_ids=product_ids)


# new_id_list = [585, 670, 686, 687, 688, 689]
# improve_products(fix_source=new_id_list, classify_ai=0, descriptions_ai=1, meta_ai=0, inci_unit=0)


# Fixer
# prestashop.delete('products', [792, 793])
