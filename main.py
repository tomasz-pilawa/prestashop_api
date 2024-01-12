from src import config
from src.product_manager import ProductManager
from src.utils import load_parameters
from prestapyt import PrestaShopWebServiceDict


if __name__ == "__main__":
    api_connector = PrestaShopWebServiceDict(config.api_url, config.api_key)
    pm = ProductManager(api_connector)
    mode, param = load_parameters()
    pm.execute_operations(mode, param)
