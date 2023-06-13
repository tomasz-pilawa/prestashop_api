import xml.etree.ElementTree as ET
import random
import os
import openai


openai.api_key = os.getenv('openai_api')


cat_1 = ['Pielęgnacja twarzy', 'Pielęgnacja ciała', 'Pielęgnacja i stylizacja włosów', 'Zestawy kosmetyków']

# 8/6
cat_1_1 = ['Kremy do twarzy', 'Serum do twarzy', 'Oczyszczanie i pielęgnacja', 'Kosmetyki pod oczy',
           'Maseczki do twarzy', 'Peelingi do twarzy', 'Toniki i hydrolaty']

# 10
cat_1_1_1 = ['Kremy łagodzące', 'Kremy matujące', 'Kremy przeciwtrądzikowe', 'Kremy nawilżające', 'Kremy odżywcze',
             'Kremy przeciwzmarszczkowe', 'Kremy wygładzające', 'Kremy regenerujące', 'Kremy rozświetlające',
             'Kremy z filtrem UV', 'kremy na przebarwienia']

# 7
cat_1_1_2 = ['Serum wygładzające', 'Serum liftingujące', 'Serum rozjaśniające', 'Serum antyoksydacyjne',
             'Serum ujędrniające', 'Serum odmładzające', 'Serum rewitalizujące']

cat_1_2 = ['Kosmetyki do stóp', 'Peelingi do ciała', 'Wyszczuplanie i ujędrnianie', 'Koncentraty błotne',
           'Kosmetyki na cellulit']


cat_1_3 = ['Szampony do włosów', 'Odżywki do włosów', 'Maski do włosów', 'Kosmetyki do stylizacji włosów',
           'Olejki i serum do włosów', 'Ampułki do włosów']

cat_1_1t = cat_1_1_1 + cat_1_1_2 + cat_1_1[2:]

cats_all = cat_1_1t + cat_1_2 + cat_1_3


def simple_cat_classifier(file_name='luminosa_feed.xml', max_products=5, randomness=1):

    tree = ET.parse(file_name)
    root = tree.getroot()

    if randomness == 1:
        selected_products = random.sample(root.findall('o'), max_products)
    else:
        selected_products = root.findall('o')[:max_products]

    # print(f'\nThere are potentially {len(selected_products)} products to add from the XML file\n')
    # for p in selected_products:
    #     print(p.find('name').text)
    #     print(p.get('id'))
    #     print(p.find("attrs/a[@name='Kod_producenta']").text)

    for p in selected_products:
        p_name = p.find('name').text
        p_link = p.get('url')
        p_desc = p.find('desc')[:500]

        print(f'\n{p_name}')

        prompt = f"Classify the product {p_name} to one of the main categories: {cat_1}" \
                 f"and minimum number of relatable subcategories.\n" \
                 f"If it's not a set, than choose only from one subcategories set:" \
                 f"{cat_1_2}, {cat_1_3}, {cat_1_1}\n" \
                 f"Determine if it's a cream or a serum. " \
                 f"-If it's a cream, chose 1-3 most relevant only from this set: {cat_1_1_1}." \
                 f"-If it's a serum, chose 1-3 most relevant only from this set: {cat_1_1_2}.\n" \
                 f"If it's not a set, you can never have 'serum' and 'krem' subcategories together" \
                 f"If it's a set, you can classify more freely." \
                 f"\n IMPORTANT: It's better to classify to less categories, but more accurately AND " \
                 f"YOU CAN ONLY USE GIVEN SUBCATEGORIES NAMES\n" \
                 f"Respond with one comma separated list without additional characters"

        response = openai.Completion.create(engine='text-davinci-003', prompt=prompt, max_tokens=500, temperature=0)
        generated_text = response.choices[0].text

        x = generated_text.strip()
        lst = [part.strip().replace('\n', '').replace(':', '') for part in x.split(',')]
        lst_2 = [x for x in lst if x in cat_1+cats_all]

        print(lst_2)


simple_cat_classifier(max_products=3)