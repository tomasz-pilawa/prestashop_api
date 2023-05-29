import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)

# USEFUL COMMANDS ###

# prestashop.add('addresses', address_data)
# prestashop.delete('addresses', 15318)
# prestashop.edit('addresses', modified_ad)

# WORKING FLOW OF EDITING PARAMETERS

# modified_ad = prestashop.get('addresses', 15317)

# for k, v in modified_ad['address'].items():
#     print(f"'{k}': '{v}',")

# modified_ad['address'].update({'lastname': 'Modyfikowalinski'})
# prestashop.edit('addresses', modified_ad)

# CREATING NEW ADDRESS WORKFLOW ###

# address_data = prestashop.get('addresses', options={'schema': 'blank'})
# for k in address_data['address'].keys():
#     print(f"'{k}': '',")

# data_from_schema = prestashop.get('addresses', options={'schema': 'blank'})
#
# data_from_schema['address'].update({  # 'id': '15318', zabroniony przy dodawaniu nowego
#                                     'id_customer': '0',
#                                     'id_manufacturer': '0',
#                                     'id_supplier': '0',
#                                     'id_warehouse': '0',
#                                     'id_country': '14',
#                                     'id_state': '0',
#                                     'alias': 'rand',
#                                     'company': 'comp',
#                                     'lastname': 'Pil',
#                                     'firstname': 'Tom',
#                                     'vat_number': '',
#                                     'address1': 'asdas',
#                                     'address2': '',
#                                     'postcode': '11-121',
#                                     'city': 'Kupkowo',
#                                     'other': '',
#                                     'phone': '',
#                                     'phone_mobile': '897123543',
#                                     'dni': '',
#                                     'deleted': '',
#                                     'date_add': '',
#                                     'date_upd': ''})

# prestashop.add('addresses', data_from_schema)
# prestashop.delete('addresses', 15320)


# blank_product = prestashop.get('products', 37)
# # blank_product_2 = prestashop.get('products', options={'schema': 'blank'})
#
# for k, v in blank_product['product'].items():
#     print(f"'{k}': '{v}',")
#
# print(blank_product)

# features = prestashop.search('product_feature_values')
# print(features)
# print(len(features))

# ft = prestashop.get('product_feature_values', 47)
# print(ft)


# default_product_values = {'state': ' 1',
#                           'low_stock_alert': '0',
#                           'active': '0',
#                           'redirect_type': '404',
#                           'condition': 'new',
#                           'show_price': '1',
#                           'indexed': '1',
#                           'visibility': 'both'}


# with open('default_product_values.json', 'w') as file:
#     json.dump(default_product_values, file)
