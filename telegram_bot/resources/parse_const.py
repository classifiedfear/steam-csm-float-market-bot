import os
from pathlib import Path

current_directory = Path(__file__).resolve().parent.parent

extensions = (
    str(current_directory) + '/steam/additions/extensions/CSGOFloat-Market-Checker.crx',
    str(current_directory) + '/steam/additions/extensions/Free-VPN-for-ChromeTroywell-VPN.crx'
)



float_checker_select_menu = """
            return document.querySelector('csgofloat-utility-belt')
            .shadowRoot.querySelector('csgofloat-page-size')
            """

float_checker_select_index = """
            {}.shadowRoot.querySelector("option[value='100']")
            """

button_for_next_page = 'searchResults_btn_next'

driver_root_edge = str(current_directory) + '/steam/additions/msedgedriver.exe'

headless_browser = '--headless=new'

msg_table_error = 'market_listing_table_message'

request_exception_str = "You've made too many requests recently. Please wait and try your request again later."
no_item_str = "There are no listings for this item."