import os
import json
import csv
from prestapyt import PrestaShopWebServiceDict
import openai
import requests

api_url = os.getenv('quelinda_link')
api_key = os.getenv('quelinda_pass')

prestashop = PrestaShopWebServiceDict(api_url, api_key)

openai.api_key = os.getenv('openai_api')

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


# default_product_values = {'state': '1',
#                           'low_stock_alert': '0',
#                           'active': '0',
#                           'redirect_type': '404',
#                           'condition': 'new',
#                           'show_price': '1',
#                           'indexed': '1',
#                           'visibility': 'both'}


# with open('default_product_values.json', 'w') as file:
#     json.dump(default_product_values, file)


link_product = 'https://alejazdrowia.pl/product_info.php?products_id=28'
desc_product = 'Kolagen naturalny to żel otrzymywany z ryb słodkowodnych, znakomicie przyswajalny i o szerokim spektrum zastosowań. Jest to wynalazek, który pojawia się raz na ćwierćwiecze, którego istnieniu jeszcze towarzyszy niedowierzanie, ale już wzbudza olbrzymie pożądanie. Kolagen firmy Colway ma strukturę 5-26 co oznacza, że jego struktura komórkowa zachowuje swoje właściwości w przedziale temperatur 5-26 stopni C. Nie wyprodukowano dotychczas preparatu, o podobnej trwałości. Oddajemy w Wasze ręce preparat, który przerasta efektami działania tysiące kosmetyków wytwarzanych na całym świecie. Preparat występuje w 3 odmianach: PLATINUM, SILVER i GRAPHITE- są to 3 stopnie finalnego oczyszczenia i we wszystkich stopniach zachowują te same właściwości. Kolagen Naturalny to szansa na spełnienie się jednego z najstarszych marzeń ludzkości- zatrzymania młodości. KOLAGEN NATURANNY PLATINUM: Twarz, szyja, oczy i inne delikatne partie ciała. Skuteczny w zabiegach rewitalizujących cerę dojrzałą, w nieinwazyjnym liftingu twarzy, po zabiegach chirurgii plastycznej, wygładzenie zmarszczek, zapobieganie zmarszczkom, po opalaniu i jako podkład pod maseczki i makijaż. KOLAGEN NATURALNY SILVER: Piersi, pośladki, całe ciało. Wspomaga leczenie cellulitu, wyprysków skórnych, żylaków, liftinguje skórę. Ujędrnia skórę i zapobiega jej zwiotczeniu. Do masażu leczniczego, po depilacjach, solarium, peelingach. KOLAGEN NATURALNY GRAPHITE: Włosy, paznokcie, pięty, stwardniały naskórek, do kąpieli perełkowych Można stosować kolagen zamiennie, nie tylko wg. powyższych zaleceń, np. SILVER na twarz. Poręczny dozownik ułatwia utrzymanie higieny i czystości, a specjalne termoizolacyjne opakowanie zapewnia bezpieczny transport. Kolagen po zastosowaniu na skórze tworzy siateczkę proteinową, która zatrzymuje zarówno wodę jak i substancje lipofilowe, co umożliwia ich selektywne uwalnianie. W ten sposób obniżona zostaje transepidermalna utrata wody, co powoduje, że skóra staje się gładsza. Cząsteczki kolagenu, a także polipeptydy i aminokwasy wnikają w głąb skóry, gdzie pobudzają komórki do produkcji własnego kolagenu. Efekty stosowania Kolagenu Naturalnego: &#8226; głęboko nawilżona i ujędrniona skóra &#8226; wyraźnie wygładzone zmarszczki &#8226; spowolniony proces starzenia się skóry &#8226; regeneracja skóry i wyraźnie jej odmłodzenie &#8226; wyraźne wygładzenie zmarszczek oraz zapobieganie powstawaniu nowych &#8226; pomoc w leczeniu skóry z trądzikiem młodzieńczym i różowatym &#8226; zmiękczenie i wygładzenie blizn &#8226; rewelacyjnie szybkie gojenie ran, otarć i podrażnień &#8226; regeneracja włosów i paznokci &#8226; łagodzenie oparzeń skóry (np. po opalaniu) &#8226; znaczna redukcja cellulitu i rozstępów &#8226; likwiduje rozszerzenia naczyń włosowatych i "pajączki" &#8226; łagodzi objawowo bóle kręgosłupa i "korzonkowe" &#8226; jest najlepszym na świecie balsamem po goleniu i depilacji &#8226; i wiele innych. Sposób stosowania: Na dokładnie umytą , wilgotną skórę nakładamy cienką warstwę Kolagenu Naturalnego. Nie stosujemy bezpośrednio po zmyciu twarzy tonikiem lub mleczkiem, ponieważ kolagen jest białkiem, a to nie lubi kwaśnego odczynu kosmetyków. Kolagen naturalny to preparat wyjątkowy i bardzo wydajny. Koszt kolagenowej kuracji przeciwzmarszczkowej i antycelulitowej to ułamek kosztów, które ponoszą kobiety kupując kremy, kosmetyki i korzystając z różnego rodzaju zabiegów. Efekt jest zaskakujący. Przeciwskazania: &#8226; dieta niskobiałkowa &#8226; ciężkie choroby nerek &#8226; chemioterapia &#8226; alergie białkowe &#8226; uczulenie na białko rybie Opakowanie: 200 ml'
name_product = 'Kolagen Naturalny Colway PLATINUM 200ml'
# print(list(x['id'] for x in openai.Model.list()['data']))

aleja_xml = 'http://alejazdrowia.pl/pliki/ceneo.xml'


def test_response(data):
    prompt = f"Make 400 characters short product description for ecommerce for {data}" \
             f"It should be in Polish, in 5 bullet points saying what the product is, for which skin, " \
             f"and what are the benefits, with possible mentioning of active ingredients, without product name"
    model = "text-davinci-003"
    response = openai.Completion.create(engine=model, prompt=prompt, max_tokens=500)

    generated_text = response.choices[0].text
    print(generated_text)
    print(len(generated_text))
    print(type(generated_text))


# print(test_response(link_product))
# print(test_response(desc_product))
# print(test_response(name_product))

image_url = "https://luminosa.pl/img/p/8/0/7/807.jpg"
filename = "807.jpg"

response = requests.get(image_url)
response.raise_for_status()

with open(filename, "wb") as file:
    file.write(response.content)

print("Image downloaded successfully!")



