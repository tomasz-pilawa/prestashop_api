from src import config
from src.product_manager import ProductManager
from prestapyt import PrestaShopWebServiceDict


if __name__ == "__main__":
    api_connector = PrestaShopWebServiceDict(config.api_url, config.api_key)
    pm = ProductManager(api_connector)
    pm.execute_operations()
