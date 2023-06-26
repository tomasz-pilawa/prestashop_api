import mapping
import json
import editing
import csv
import os
import categories

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

# mapping.get_init_brand_dict()
# mapping.get_init_sku_dict()
# mapping.get_manufacturers_dict()
# mapping.get_categories_dict()

# product_test = 'random_product.csv'
# editing.add_product(product_test)


# NEW STAGE (CLEANING CODE)

# mapping.create_category_dicts(csv_name='cats_pairing_init.csv', update_classification_dict=1)

# only use when new csv is provided (rollback database to 22/06) - needs to uncomment add and fix delete
# mapping.set_categories_tree(changes_file='cats_pairing_v_0.json')

# mapping.update_products_json(max_products=30, brand_update='Filorga')
