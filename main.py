import api_products as ap
import json

brands = ap.get_all_manufacturers()

print(brands)

# extracted_products_1 = ap.get_products(ap.get_products_indexes(50), brands[3])
#
# for extr in extracted_products_1:
#     print(extr['name']['language']['value'])
#     print(extr['manufacturer_name']['value'])
#     print(extr)

brand_test = 'Filorga'

with open('brands_mapped.json') as file:
    data = json.load(file)
    product_indexes = data[brand_test]

print(product_indexes)

extracted_products_2 = ap.get_products(product_indexes, brand_test)

for extr in extracted_products_2:
    print(extr['name']['language']['value'])
    print(extr)

