import json
import os

import mapping
import editing
import ai_boosting

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')


# Update XML file from time to time
# mapping.get_xml_from_web(source='luminosa')


# Check which products to introduce, get their ids and verify the initial data
# editing.select_products_xml(source='ampari', mode='brands', data=['Helen Seward'], print_info=1)


# Add simple version of selected products (preferably ID-based) & correct essential information (name, price, sku, ean)
id_list = []
# editing.add_product_from_xml(select_source='luminosa', select_mode='include',
#                              select_data=id_list, process_max_products=2)


# After adding or while editing only always use csv to improve specific products (works on ids too)
# editing.improve_products(file_path_fix='data/logs/__dummy_testing_change.csv',
#                          classify_ai=0, descriptions_ai=0, features_ai=0)

