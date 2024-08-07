import argparse
import read_evtx
import read_registry
from scripts.ilapfuncs import logfunc, OutputParameters, logfunc
from time import process_time, gmtime, strftime
from scripts.report import generate_report
import os
import datetime
from utils import functions as own_functions


REGISTRY_FILE = 'NTUSER.DAT'
EVTX_FILE = 'Microsoft-Windows-WebAuthN%4Operational.evtx'


def main(data):
    start = process_time()

    startdate = data.startdate
    enddate = data.enddate
    output_format = data.format
    output_folder = data.output

    if output_folder:
        output_folder = os.path.abspath(data.output)
    else:
        output_folder = os.getcwd()

    out_params = OutputParameters(output_folder, output_format)
    logfunc()
    input_path = ''


    terminate = [False, False] # flag to terminate if no files are found

    eventlog_file = data.eventlog
    if eventlog_file:
        eventlog_file = os.path.abspath(data.eventlog)
        if os.path.isdir(eventlog_file):
            eventlog_file = os.path.join(eventlog_file, EVTX_FILE)
            if not os.path.exists(eventlog_file):
                logfunc(f'ERROR: File {EVTX_FILE} not found.')
                terminate[0] = True
            else:
                input_path += eventlog_file

    registry_file = data.registry
    if registry_file:
        registry_file = os.path.abspath(data.registry)
        if os.path.isdir(registry_file):
            registry_file = os.path.join(registry_file, REGISTRY_FILE)
            if not os.path.exists(registry_file):
                logfunc(f'ERROR: File {REGISTRY_FILE} not found.')
                terminate[1] = True
            else:
                input_path += "; " + registry_file
        
    if all(terminate):
        logfunc(f'ERROR: No files to process, terminating.')
        return
    

    # ======================= File Processing =======================

    logfunc(f'- PASSKEY EVENT ANALYSER - {strftime("%d/%m/%Y %H:%M:%S")}')
    if data.eventlog:
        read_evtx.read_evtx_file(eventlog_file, out_params.report_folder_base, output_format, startdate, enddate)

    if data.registry:
        read_registry.read_registry_file(registry_file, out_params.report_folder_base, output_format)

    print('DONE - the output is in the folder:', out_params.report_folder_base)
    # ======================= Terminate Report =======================

    end = process_time()
    run_time_secs = end - start
    run_time_HMS = strftime('%H:%M:%S', gmtime(run_time_secs))

    logfunc(f'Elapsed time : {run_time_HMS} ({run_time_secs:.4f} seconds)')

    if output_format == 'html':
        generate_report(out_params.report_folder_base, run_time_secs, run_time_HMS, input_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='PEA',
        description='''
            Passkey Event Analyzer is a tool to extract and 
            analyze FIDO2 keys from Windows Event Logs and Registry''',
        epilog='Developed by: Pedro Chen and Bruno Correia')

    parser.add_argument(
        "-l",
        "--eventlog",
        help="Event log file, or path with event log file",
        required=False,
        type=str)

    parser.add_argument(
        "-r",
        "--registry",
        help="Registry file, or path with registry file",
        required=False,
        type=str)
    
    parser.add_argument(
        "-s",
        "--startdate",
        help="Start date filter of the event log (ISOformat - YYYY-MM-DD:HH:mm:ss)",
        required=False,
        type=datetime.datetime.fromisoformat
    )

    parser.add_argument(
        "-e",
        "--enddate",
        help="End date filter of the event log (ISOformat - YYYY-MM-DD:HH:mm:ss)",
        required=False,
        type=datetime.datetime.fromisoformat
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output folder",
        required=False,
        type=str)

    parser.add_argument(
        "-f",
        "--format",
        help="Output format",
        required=True,
        type=str,
        choices=['csv', 'html', 'xlsx'])

    args = parser.parse_args()

    # argument validation

    if args.eventlog is None and args.registry is None:
        parser.error("at least one of the following arguments must be provided: -l/--eventlog, -r/--registry")
    
    if args.eventlog is not None:
        if not os.path.exists(args.eventlog):
            parser.error(f"the file {args.eventlog} does not exist")

    if args.registry is not None:
        if not os.path.exists(args.registry):
            parser.error(f"the file {args.registry} does not exist")

    main(args)
