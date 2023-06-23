import api_products as ap
import mapping as mp
import json
import add_product as add_p
import csv
import os
import categories

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

# mp.get_init_brand_dict()
# mp.get_init_sku_dict()
# mp.get_manufacturers_dict()
# mp.get_categories_dict()

# brand_test = 'Filorga'
# ap.get_products_2(brand_test)

# product_test = 'random_product.csv'
# add_p.add_product_from_csv(product_test)

# categories.create_json_from_csv_cats(csv_name='cats_pairing_init.csv', dump_cats_classify=1)
