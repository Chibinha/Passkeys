from regipy.registry import RegistryHive
from regipy.utils import convert_wintime
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc
import os
from utils import functions as own_functions


SEARCH_PATH = fr"S-1-5-20\Software\Microsoft\Cryptography\FIDO"


def read_registry_file(registry_file_path, report_folder, output_format):

    reg = RegistryHive(registry_file_path)
    fido_list = {}
    linked_devices = []  # [[<user_id>, <device_name>, <last_modified>, <isCorrupted>, <device_data>], ...]
    logfunc("---Analyzing Registry file---")

    try:
        for sk in reg.get_key(SEARCH_PATH).iter_subkeys():
            fido_list[sk.name] = None

        for fido_sk in fido_list:
            device_list = {}

            path = SEARCH_PATH
            path += f'\\' + str(fido_sk) + rf'\LinkedDevices'
            for device_sk in reg.get_key(path).iter_subkeys():
                device_list[device_sk.name] = None

            fido_list[fido_sk] = device_list.copy()
    except:
        logfunc('---No associated devices found---')
        return

    try:
        for fido in fido_list:
            # print(fido)  # User ID
            linked_device = [fido, None, None, None, None]  # [<user_id>, <device_name>, <last_modified>, <is_corrupted>, <device_data>]

            for device in fido_list[fido]:

                path = SEARCH_PATH
                path += f'\\' + str(fido) + rf'\LinkedDevices'
                path += f'\\' + str(device)
                data = reg.get_key(path)

                for i in data.get_values():
                    # print("\t\t" + str(i))
                    if i.name == "Name":
                        linked_device[1] = i.value
                        logfunc(f'\tDevice found: {i.value}')
                    if i.name == "Data" and i.value_type == 'REG_BINARY':
                        linked_device[4] = i.value.hex().upper()
                    linked_device[3] = i.is_corrupted

                linked_device[2] = convert_wintime(data.header.last_modified, as_json=False).strftime("%Y-%m-%d %H:%M:%S")

                linked_devices.append(linked_device.copy())
    except:
        logfunc('---Error extracting data---')
        return  
    
    data_headers = ('User ID', 'Device Name', 'Last Modified','Is Corrupted', 'Device Data')

    if output_format == 'csv':
        linked_devices.insert(0, data_headers)
        own_functions.write_csv(os.path.join(report_folder, 'linked_devices.csv'), linked_devices)
        logfunc('---Sucess, ' + str(len(linked_devices)) + ' associated devices found---')

    elif output_format == 'html':
        if len(linked_devices) > 0:
            report = ArtifactHtmlReport('Passkeys - Registry')
            report.start_artifact_report(report_folder, 'Passkeys - Registry')
            report.add_script()

            report.write_artifact_data_table(data_headers, linked_devices, registry_file_path)
            report.end_artifact_report()

            logfunc('---Sucess, ' + str(len(linked_devices)) + ' associated devices found---')
        else:
            logfunc('Passkeys - registry data available')
    
    elif output_format == 'xlsx':
        linked_devices.insert(0, data_headers)
        own_functions.write_excel(os.path.join(report_folder, 'passkeys_artifacts_data.xlsx'), 'Linked Devices', linked_devices, is_rewrite=False)
        logfunc('---Sucess, ' + str(len(linked_devices)) + ' associated devices found---')

