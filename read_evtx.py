import os
import sys
from bs4 import BeautifulSoup
from Evtx.Evtx import Evtx
from utils import functions as own_functions
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv


class PasskeyLog:
    def __init__(self):
        self.userId = None
        self.transactionId = None
        self.type = None
        self.result = None
        self.timestamp = None
        self.computerName = None
        self.device = None
        self.website = None
        self.browser = None
        self.browserPath = None

    def set_event_type(self, value):
        self.type = value

    def set_timestamp(self, value):
        self.timestamp = value

    def set_transaction_id(self, value):
        self.transactionId = value

    def set_event_conclusion(self, value):
        self.result = value

    def set_user_id(self, value):
        self.userId = value

    def set_computer_name(self, value):
        self.computerName = value

    def set_device(self, value):
        self.device = value

    def set_website(self, value):
        self.website = value

    def set_browser(self, value):
        self.browser = value

    def set_browser_path(self, value):
        self.browserPath = value


def object_to_row(event):
    return [event.userId, event.transactionId, event.type, event.browser, event.browserPath,
            event.website, event.timestamp, event.computerName, event.device, event.result]


def read_evtx_file(evtx_file_path, report_folder, file_path, output_format):
    event_list = []
    print("---A iniciar a leitura do ficheiro evtx---")
    with Evtx(evtx_file_path) as evtx:
        for record in evtx.records():


            soup = BeautifulSoup(record.xml(), 'xml')

            event_id = soup.find("EventID")
            if event_id:
                event_id = event_id.text

            #####################################
            # 1000: Start Registration          #
            # 1001: Registration Success        #
            # 1002: Failed/Canceled             #
            # 1003: Start Authentication        #
            # 1004: Authentication Success      #
            # 1005: Failed/Canceled             #
            # 1006: Start sending Ctap Cmd      #
            # 1007: Success Ctap Cmd            #
            # 1008: Connection failed           #
            #####################################

            if event_id in ["1000", "1003"]:
                event = PasskeyLog()

                transaction_id = soup.find("Data", attrs={'Name': 'TransactionId'})
                if transaction_id:
                    event.set_transaction_id(transaction_id.text)

                event.set_timestamp(record.timestamp())

                computer_name = soup.find("System")
                computer_name = computer_name.find("Computer")
                if computer_name:
                    event.set_computer_name(computer_name.text)

                user_id = soup.find("Security")
                user_id = user_id.get('UserID')
                if user_id:
                    event.set_user_id(user_id)

                event.set_event_type("Authentication" if event_id == "1003" else "Registration")
                print('Operação encontrada: Tipo ', event.type, ' no dia ',  event.timestamp.strftime("%d de %B"))
            elif event_id in ["1001", "1004"]:
                event.set_event_conclusion("Success")
                event_list.append((event.userId, event.transactionId, event.type, event.browser, event.browserPath,
                                   event.website, event.timestamp, event.computerName, event.device, event.result))
                continue
            elif event_id in ["1002", "1005"]:
                event.set_event_conclusion("Incomplete")
                event_list.append((event.userId, event.transactionId, event.type, event.browser, event.browserPath,
                                   event.website, event.timestamp, event.computerName, event.device, event.result))
                continue

            if event_id == "2104" or event_id == "2106" or event_id == "1101" or event_id == "1103":
                event_data = soup.find("EventData")

                if event_data:
                    device = event_data.find("Data", attrs={'Name': 'DevicePath'})
                    rp_id = event_data.find("Data", attrs={'Name': 'RpId'})
                    image_name = event_data.find("Data", attrs={'Name': 'Name'})

                    if rp_id:
                        event.set_website(rp_id.text)
                    elif image_name:
                        if image_name.text == "ImageName":
                            data_value = event_data.find("Data", attrs={'Name': 'Value'})
                            if data_value:
                                event.set_browser_path(data_value.text)
                                event.set_browser(os.path.splitext(os.path.basename(event.browserPath))[0].capitalize())

                    if device and device.text:
                        event.set_device(device.text)
                    else:
                        event.set_device(computer_name.text + ' (This Device)')



        if output_format == 'csv':
            data_headers = (
                'userId', 'transaction_id', 'type', 'browser', 'browserPath', 'website', 'timestamp', 'computerName',
                'device', 'result')
            event_list.insert(0, data_headers)
            own_functions.write_csv(os.path.join(report_folder, 'passkey_logs.csv'), event_list)
            print('---Sucesso, foram registadas ' + str(len(event_list)) + ' operações Passkey---')


        elif output_format == 'html':
            if len(event_list) > 0:
                report = ArtifactHtmlReport('Passkeys - Event Log')
                report.start_artifact_report(report_folder, 'Passkeys - Event Log')
                report.add_script()
                data_headers = (
                'userId', 'transaction_id', 'type', 'browser', 'browserPath', 'website', 'timestamp', 'computerName',
                'device', 'result')

                report.write_artifact_data_table(data_headers, event_list, file_path)
                report.end_artifact_report()

                tsvname = f'Passkeys - Event Log'

                report_folder = os.path.join(report_folder, "passkeys") + '\\'
                tsv(report_folder, data_headers, event_list, tsvname)
                print('---Sucesso, foram registadas ' + str(len(event_list)) + ' operações Passkey---')
            else:
                logfunc('Passkeys - Event Log data available')


if __name__ == "__main__":
    # Replace 'path_to_evtx_file.evtx' with the actual path to your EVTX file
    # evtx_file_path1 = r'event-logs\antes\Microsoft-Windows-WebAuthN%4Operational.evtx'
    # evtx_file_path2 = r'event-logs\depois_depois\Microsoft-Windows-WebAuthN%4Operational.evtx'
    evtx_file_path3 = r'event-logs\2024-04-03_00.00\Microsoft-Windows-WebAuthN%4Operational.evtx'
    # evtx_file_path4 = r'event-logs\windows10\Microsoft-Windows-WebAuthN%4Operational.evtx'
    if len(sys.argv) == 2:
        read_evtx_file(sys.argv[1])
    else:
        # read_evtx_file(evtx_file_path1)
        # read_evtx_file(evtx_file_path2)
        read_evtx_file(evtx_file_path3)
        # read_evtx_file(evtx_file_path4)
