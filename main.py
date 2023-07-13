import json
import os

import mapping
import editing
import ai_boosting

api_url = os.getenv('urodama_link')
api_key = os.getenv('urodama_pass')


def set_up_cats_after_migration():
    """
    Sets up the whole categories tree based on csv file. Meant to be used only once after migration to new Prestashop.
    :return:
    """
    mapping.create_category_dicts(csv_name='cats_pairing_init.csv', update_classification_dict=1)
    mapping.set_categories_tree(changes_file='cats_pairing_v_0.json')
    mapping.update_products_dict()
    mapping.update_cats_dict(update_cats_to_classify=1)
    mapping.update_brands_dict()


# set_up_cats_after_migration()

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

