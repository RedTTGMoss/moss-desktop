import json

from colorama import Fore, Back
from slashr import SlashR
from rm_api import API, check_file_exists, get_file

with open('../config.json', 'r') as f:
    config = json.load(f)

api = API(uri=config['uri'], discovery_uri=config['discovery_uri'], token_file_path='../token', sync_file_path='../sync')
api.debug = True
api.check_for_document_storage()

_, files = get_file(api, api.get_root()['hash'])
with SlashR(False) as sr:
    for i, file in enumerate(files):
        _, sub_files = get_file(api, file.hash)
        for j, sub_file in enumerate(sub_files):
            if not check_file_exists(api, sub_file.hash):
                print(f"File {sub_file.uuid} is missing -> {sub_file.hash}")
            else:
                sr.print(
                    f"{Back.LIGHTBLACK_EX}{Fore.YELLOW}"
                    f"[{i:^7}/{len(files):^7}]"
                    f"{Fore.MAGENTA}"
                    f"[{j:^7}/{len(sub_files):^7}]"
                    f"{Fore.GREEN} "
                    f"File {sub_file.hash} is present"
                    f"{Fore.RESET}{Back.RESET}")
    sr.print(f'{Back.LIGHTBLACK_EX}{Fore.GREEN}DONE!{Fore.RESET}{Back.RESET}')
