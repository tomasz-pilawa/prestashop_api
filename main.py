import json
import os

import mapping
import editing
import ai_boosting

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

# mapping.get_init_brand_dict()
# mapping.get_init_sku_dict()
# mapping.get_manufacturers_dict()
# mapping.get_categories_dict()


# NEW STAGE (CLEANING CODE)

# only use when new csv is provided (rollback database to 22/06) - needs to uncomment add and fix delete
# mapping.create_category_dicts(csv_name='cats_pairing_init.csv', update_classification_dict=1)
# mapping.set_categories_tree(changes_file='cats_pairing_v_0.json')

# mapping.update_products_json(max_products=30, brand_update='Filorga')
# mapping.update_products_json(max_products=30)
# mapping.update_brands_dict()


editing.add_product(file_name='luminosa_feed.xml', mode='print', max_products=5, edit_presta=0,
                    brand='Germaine de Capuccini')
