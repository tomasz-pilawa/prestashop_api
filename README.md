
# Prestashop_API

Prestashop_API stands as a robust tool for refining PrestaShop product management workflow. The core functionality of this script revolves around harnessing the capabilities of artificial intelligence, particularly OpenAI's GPT-3.5, to elevate your product descriptions, categories classification, and metadata.

## Core Features

- **CSV File Processing:** The script supports the processing of product data sourced from CSV files. This flexibility enables users to seamlessly integrate product information from other shops directly into their PrestaShop environment.


- **AI-Powered Enhancement:** The script seamlessly integrates OpenAI's GPT-3.5 to enhance the quality of the product data. It does so by applying sophisticated algorithms to improve product descriptions, classifications, and metadata.


- **API-driven Product Improvement:** The script facilitates the direct enhancement of existing products within your PrestaShop store through API calls. This means that you can optimize your product listings without the need for manual intervention, ensuring efficiency in the product management process.




## Getting Started

Before diving into the script, make sure you have the necessary credentials and dependencies in place. 

To run this project, you will need to add the following environment variables to your .env file

`URODAMA_LINK` & `URODAMA_KEY`- PrestaShop Webservice API credentials

`OPENAI_KEY` - OpenAI API key

If you're adding products, prepare a CSV file with the necessary information. Set the filename in the params dictionary.



## Deployment

The script necessitates the setup of environment variables, including PrestaShop API credentials (`URODAMA_LINK` and `URODAMA_KEY`) and the OpenAI API key (`OPENAI_KEY`). Additionally, ensure the existence of a CSV file containing the requisite product information for processing

Ensure your environment variables are correctly set and that you've installed the required Python packages listed in the requirements.txt file.
    
Execute the script with Python, adjusting parameters in the script to align with your specific requirements:

```bash
  python prestashop_api.py
```


## Usage Modes

`Explore Mode`

Use explore mode to gather insights about a specific brand from the CSV file, here exemplified with 'Phyris'. Get the csv file that helps you understand existing products under that brand and serves a first step towards preprocessing potential products to add in the second step.

`Add Mode`

In add mode, the script reads product information from a CSV file and adds them to your PrestaShop store using the provided API credentials.

`Improve Mode`

Opt for improve mode to apply artificial intelligence enhancements to your existing products. This includes classifying products, generating descriptions, and optimizing metadata. This mode aims to refine your product listings for better visibility and engagement.



## Tech Stack

- **Python 3.10:** The core programming language used for script development.
- **pymysql:** A Python library for connecting to MySQL databases, facilitating database operations.
- **xml.etree.ElementTree:** A Python module for parsing and manipulating XML data, essential for handling XML files in PrestaShop.
- **OpenAI GPT-3.5:** OpenAI's state-of-the-art natural language processing model for AI-driven enhancements in product descriptions, classifications, and metadata.
- **dotenv:** A Python library for reading variables from `.env` files, ensuring secure management of API keys and sensitive information.
