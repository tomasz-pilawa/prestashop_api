import requests
import xml.etree.ElementTree as ET

xml_url_luminosa = 'https://feed-d.baselinker.com/feed/3007509/2475/6592c40515e118741ac4b492bfaa5946/ceneo.xml'


def get_xml(url='', name='random_feed', from_web=0):

    if from_web == 1:
        response = requests.get(url)
        if response.status_code == 200:
            with open(f'{name}.xml', 'wb') as file:
                file.write(response.content)
            print("File saved successfully!")
        else:
            print("Failed to fetch the XML file!")

    tree = ET.parse(f'{name}.xml')
    root = tree.getroot()

    # new = ET.tostring(root, encoding='utf-8').decode('utf-8')
    # print(new)

    # single_object = root.find('o')
    # print(ET.tostring(single_object, encoding='unicode', method='xml'))

    brand = "Germaine de Capuccini"
    selected_products = []

    for o in root.findall('o'):
        producent = o.find("./attrs/a[@name='Producent']").text
        if producent == brand:
            selected_products.append(o)

    for product in selected_products:
        name = product.find('name').text
        sku = product.find("attrs/a[@name='Kod_producenta']").text
        print(name)
        print(sku)

    # print(ET.tostring(selected_products[3], encoding='unicode', method='xml'))


get_xml(name='luminosa_feed', from_web=0)
