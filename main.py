import json
import os
import openai
import mapping
import editing
import ai_boosting

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')
openai.api_key = os.getenv('openai_api')


# Update XML file from time to time
# mapping.get_xml_from_web(source='ampari')


# Check which products to introduce, get their ids and verify the initial data
# editing.select_products_xml(source='luminosa', mode='brands', print_info=1, data=['Mesoestetic'])
# editing.select_products_xml(source='ampari', mode='brands', data=['Colway'], print_info=1)


# Add simple version of selected products (preferably ID-based) & correct essential information (name, price, sku, ean)
id_list = [620, 621, 624, 637, 639, 641, 643, 645, 653, 654, 655, 659, 663, 664, 666, 923, 1256, 2054, 2141, 2353]
# editing.add_product_from_xml(select_source='ampari', select_mode='include',
#                              select_data=id_list, process_max_products=30)

# new_id_list = [803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822]
# After adding or while editing only always use csv to improve specific products (works on ids too)
# editing.improve_products(file_path_fix='data/logs/adding_2_5.csv',
#                          classify_ai=1, descriptions_ai=1, features_ai=0)

