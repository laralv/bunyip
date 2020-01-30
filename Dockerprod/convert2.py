import csv
import argparse
import subprocess
import shlex
import os
import json
import shutil
import pathlib
import extract_msg
import pendulum
import zmq

context = zmq.Context()
sink = context.socket(zmq.PUSH)
sink.connect("tcp://172.17.0.1:5558")

parser = argparse.ArgumentParser()
#parser.add_argument("-i", "--input", help="csv", action="store")
parser.add_argument("-n", "--number", help="conteinernummer", action="store")
parser.add_argument("-f", "--file", help="filnavn", action="store")
parser.add_argument("-t", "--test", help="antall", action="store", default="blah")
parser_args = parser.parse_args()

os.environ['TZ'] = 'Europe/Oslo'

#Testinstans
if parser_args.test != "blah":
#Testinstans
    input_csv = 'log/input/2.csv'
    number = 2
    log_dir = 'log'
    input_dir = 'dokumenter/09-hist/dir1'
    output_dir = 'test'
else:
    #Prod
    number = parser_args.number
    file = parser_args.file
    input_csv = f"/opt/log/input/{number}.csv"
    log_dir = '/opt/log'
    input_dir = '/mnt/disk1'
    output_dir = '/mnt/disk2'

#import logging
#pathlib.Path(f'{log_dir}/syslog/').mkdir(parents=True, exist_ok=True)
#logging.basicConfig(filename=f"{log_dir}/syslog/{number}.log", level=logging.DEBUG,
#                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
#logger=logging.getLogger(__name__)

def copy(old_file_name, file_path_new):
    if os.path.exists(old_file_name) is False:
#        global results
#        results['discrepancies'].append(old_file_name)
        print('ai')
    else:
        pathlib.Path(file_path_new).mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_file_name, file_path_new)

def siegfried(filename):
    siegfriedobjekt = csv.reader(subprocess.check_output(["sf", "-csv", f'{filename}']).decode('utf-8').splitlines(), delimiter=',')
    next(siegfriedobjekt)
    output_dict = {}
    for row in siegfriedobjekt:
        output_dict['filesize'] = row[1]
        output_dict['pronom'] = row[5]
        output_dict['pronom_name'] = row[6]
        break
    return output_dict

#with open(f'{log_dir}/syslogs/{number}.txt', 'w') as f:
#    with redirect_stdout(f):
#        print('it now prints to `help.text`')
pronom_type = json.loads(open(f'{log_dir}/pronomtyper.json').read())

#pathlib.Path(f'{log_dir}/output/lock/').mkdir(parents=True, exist_ok=True)
#if pathlib.Path(f'{log_dir}/output/lock/{number}').is_file is True:
#    os.remove(f'{log_dir}/output/lock/{number}')
#with open(f'{log_dir}/output/{number}.csv','w') as f:
#    writer = csv.writer(f)
#    writer.writerow(['filename_org', 'pronom_org', 'filename_new', 'pronom_new', 'filesize_new'])

#files = []
#with open(input_csv, newline='\n') as csvfile:
#    for row in csv.reader(csvfile):
#        files.append(row)
## Legge inn liste som holder styr på statistikk.
#antall = 0

args = {}
args['container'] = number
args['input'] = {}
args['output'] = {}
args['input']['filename'] = file
siegfriedobjekt_input = siegfried(f"{input_dir}/{args['input']['filename']}")
args['input']['filesize'] = siegfriedobjekt_input['filesize']
args['input']['pronom'] = siegfriedobjekt_input['pronom']
args['input']['pronom_name'] = siegfriedobjekt_input['pronom_name']
if args['input']['pronom'] not in pronom_type:
    pronom_type[args['input']['pronom']] = {'Name': f"IKKE REGISTERT TIDLIGERE - {args['input']['pronom_name']}", 'convert': 'skip'}
## KOPIERER
if pronom_type[args['input']['pronom']]['convert'] == 'skip':
#    copy(f"{input_dir}/{args['input']['filename']}", f"{output_dir}/{os.path.dirname(args['input']['filename'])}")
    args['output'] = args['input']
## Konverterer med libreoffice
if pronom_type[args['input']['pronom']]['convert'] == 'libreoffice':
    subprocess.run([f"libreoffice --headless --convert-to pdf --outdir {output_dir}/{os.path.dirname(args['input']['filename'])} {input_dir}/{args['input']['filename']}"], shell=True, stdout=subprocess.DEVNULL, timeout=180)
    args['output']['filename'] = f"{os.path.dirname(args['input']['filename'])}/{pathlib.Path(args['input']['filename']).stem}.pdf"
if pronom_type[args['input']['pronom']]['convert'] == 'email':
#        try:
    pathlib.Path(f"{output_dir}/{os.path.dirname(args['input']['filename'])}").mkdir(parents=True, exist_ok=True)
    msg = extract_msg.Message(f"{input_dir}/{args['input']['filename']}")
    args['output']['filename'] = f"{os.path.dirname(args['input']['filename'])}/{pathlib.Path(args['input']['filename']).stem}.txt"
    output_text =   '==============================================================================\n'
    output_text += f'Sendt:\t\t{msg.date} ({pendulum.parse(msg.date, strict=False).isoformat()})\n'
    output_text += f'Avsender:\t{msg.sender}\n'
    output_text += f'Mottaker(e):\t' + ', '.join([f'{x.name} <{x.email}>' for x in msg.recipients]) + '\n'
    output_text += f'Vedlegg:\t' + ', '.join([f'<{x.longFilename}>' for x in msg.attachments]) + '\n'
    output_text += f'Emne:\t{msg.subject}\n'
    output_text += f'==============================================================================\n{msg.body}'
    with open(f"{output_dir}/{args['output']['filename']}", 'w') as outlook_out:
        outlook_out.write(str(output_text.encode('utf8')))
#        except:
#            copy(f"{input_dir}/{args['input']['filename']}", f"{output_dir}/{os.path.dirname(args['input']['filename'])}")
#            args['output']['filename'] = args['input']['filename']
if pronom_type[args['input']['pronom']]['convert'] != 'skip':
    siegfriedobjekt_output = siegfried(f"{output_dir}/{args['output']['filename']}")
    args['output']['filesize'] = siegfriedobjekt_output['filesize']
    args['output']['pronom'] = siegfriedobjekt_output['pronom']
    args['output']['pronom_name'] = siegfriedobjekt_output['pronom_name']
sink.send_json(args)
#    print(args)
#    with open(f'{log_dir}/output/{number}.csv','a') as f:
#        writer = csv.writer(f)
#        writer.writerow([args['input']['filename'], args['input']['pronom'], args['output']['filename'], args['output']['pronom'], args['input']['filesize']])
#    sink.send_string(str(args['output']['filename']))
#with open(f'{log_dir}/output/lock/{number}','w') as f:
#    f.write(f'{str(antall)}')
