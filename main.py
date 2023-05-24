import api_products as ap

brands = ap.get_all_manufacturers()

print(brands)

extracted_products_1 = ap.get_products(ap.get_products_indexes(50), brands[3])

for extr in extracted_products_1:
    print(extr['name']['language']['value'])
    print(extr['manufacturer_name']['value'])
    print(extr)

