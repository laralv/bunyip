import subprocess
import csv
import pathlib
import shlex
import os
import glob
import pathlib
#import threading
from itertools import islice
import pendulum
#import multiprocessing
import docker
import time
import shutil
import extract_msg
import argparse
import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--siardinput", help="Filstien til den opprinnelige siardfilen", action="store")
parser.add_argument("-o", "--output", help="Mappen der dokumentene skal lastes opp til", action="store")
parser.add_argument("-l", "--loging", help="Mappen der konverteringsloggene skal")
parser.add_argument("-d", "--dokmappe", help="Filstien til rotmappen for dokumenter", action="store")
parser.add_argument("-c", "--cpukjerner", help="Antall dockerinstanser som skal settes opp (defaultverdi er en for hver kjerne i CPUen)", default=os.cpu_count())
args = parser.parse_args()
print(args)
client = docker.from_env()

def conversion_stats(pronom_name, process_name, file_name_old, file_name_new):
    global results
    csv_writer = csv.writer(open(log_dir + '/logfile.csv','a'))
#    if process_name != 'converted' or process_name != 'unconverted':
#        if pronom_name not in results[process_name]:
#            results[process_name][pronom_name] = {file_name_old: file_name_new}
#        else:
#            results[process_name][pronom_name][file_name_old] = file_name_new
    csv_writer.writerow([file_name_old, file_name_new, process_name, pendulum.now().format('YYYY-MM-DD HH:mm:ss')])
    results['stats'][process_name] += 1

def logging(tekst):
    log_file = open(log_dir + '/logfile.txt','a')
    date = pendulum.now().format('YYYY-MM-DD HH:mm:ss')
#    print(date + '\t' + tekst)
    log_file.write(date + '\t' + tekst + '\n')
    log_file.close()

def copy(old_file_name, file_path_new):
    if os.path.exists(old_file_name) is False:
        global results
        results['discrepancies'].append(old_file_name)
    else:
        pathlib.Path(file_path_new).mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_file_name, file_path_new)

pronom_type = json.loads(open('pronomtyper.json').read())

results = {}
results['converted'] = {}
results['unconverted'] = {}
results['new unconverted'] = []
results['discrepancies'] = []
results['timedout'] = []
results['stats'] = {}
results['stats']['converted'] = 0
results['stats']['unconverted'] = 0
results['stats']['new unconverted'] = 0
results['stats']['timedout'] = 0

## SIARD stuff
namespace = {'siard': 'http://www.bar.admin.ch/xmlns/siard/2/table.xsd', 'siard-metadata': 'http://www.bar.admin.ch/xmlns/siard/2/metadata.xsd', 'xml-schema': 'http://www.w3.org/2001/XMLSchema'}
siard_table = 'content/schema0/table102/table102.xml'
tablelob = 'schema0/table102/lob2'
##

temp_dir = 'siard'
output_dir = temp_dir + '/test'
output_dir = os.path.abspath(args.output)
log_dir = os.path.abspath(args.loging)
pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)
document_dir = os.path.abspath(args.dokmappe)
subfolders = [f.path for f in os.scandir(document_dir) if f.is_dir() ]
pronom_list = {}
logging('Processing Siegfried, this might take a while...')
pbar = tqdm.tqdm(total=len(subfolders))
for subfolder in subfolders:
    pbar.set_postfix(file=pathlib.Path(subfolder).name, refresh=False)
    pbar.update(1)
    siegfriedobjekt_old = csv.reader(subprocess.check_output(["sf", "-csv", shlex.quote(subfolder)]).decode('utf-8').splitlines(), delimiter=',')
    next(siegfriedobjekt_old)
    for row in siegfriedobjekt_old:
        if row[5] not in pronom_list:
            pronom_list[row[5]] = [row[0]]
        else:
            pronom_list[row[5]].append(row[0])
logging('Siegfried processed')
pbar.close()
## pronomliste gjennomgang

cmds_list = []
email_list = []
convertable_files = 0
for pronom in pronom_list:
    convertable_files += len(pronom_list[pronom])
print('Teller opp filer med Siegfried...')
pbar = tqdm.tqdm(total=convertable_files)
for pronom in pronom_list:
    if pronom not in pronom_type:
        pronom_type[pronom] = {'Name': 'unknown...', 'convert': 'skip'}
        results['new unconverted'].append(pronom)
    if pronom_type[pronom]['convert'] == 'libreoffice':
        for files in pronom_list[pronom]:
#            cmds_list.append('libreoffice --headless --convert-to pdf --outdir ' + shlex.quote(output_dir + '/' + os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir))))) + ' ' + shlex.quote(files))
            cmds_list.append(['libreoffice --headless --convert-to pdf --outdir ' + shlex.quote('/mnt/disk2/' + os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir))))) + ' ' + shlex.quote(os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir)))) + '/' + pathlib.Path(files).name),
            os.path.relpath(output_dir + '/' + os.path.dirname((os.path.relpath(files, document_dir)))) + '/' + pathlib.Path(files).stem + '.pdf',
            pronom,
            files])
    if pronom_type[pronom]['convert'] == 'email':
        for files in pronom_list[pronom]:
            email_list.append([shlex.quote(files),
                                output_dir + '/' + os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir)))) + '/' + pathlib.Path(files).stem + '.txt',
                                pronom,
                                output_dir + '/' + os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir)))) + '/' + pathlib.Path(files).name])
    if pronom_type[pronom]['convert'] == 'skip':
        for files in pronom_list[pronom]:
            copy(shlex.quote(files), output_dir + '/' + os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir)))) + '/')
            logging(output_dir + '/' + os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir)))) + '/' + pathlib.Path(files).name + '\t(copied)')
            conversion_stats(pronom, 'unconverted', files, os.path.relpath(os.path.dirname((os.path.relpath(files, document_dir)))) + '/' + pathlib.Path(files).name)
            pbar.set_postfix(file=pathlib.Path(files).name + ' (copied)', refresh=False)
            pbar.update(1)
#docker
max_workers = args.cpukjerner
containers = {}
locked_dict = {}
for container in range(max_workers):
    containers[container] = client.containers.run('laralv/ubuntu-libreoffice_2019-12-04:latest', '/bin/bash', detach=True, tty=True, volumes={document_dir: {'bind': '/mnt/disk1', 'mode': 'rw'}, output_dir: {'bind': '/mnt/disk2', 'mode': 'rw'}}, working_dir='/mnt/disk1/')
    locked_dict[container] = {'file_out': ''}

dt = pendulum.now()
i = 0
while i < len(cmds_list):
    for x in locked_dict:
        if i < len(cmds_list):
            if locked_dict[x]['file_out'] == '':
                containers[x].exec_run(cmds_list[i][0], user='libreoffice', detach=True)
                locked_dict[x]['file_out'] = cmds_list[i][1]
                locked_dict[x]['pronom'] = cmds_list[i][2]
                locked_dict[x]['old_file'] = cmds_list[i][3]
                locked_dict[x]['ts'] = pendulum.now()
                i += 1
            else:
                if os.path.exists(locked_dict[x]['file_out']) is True:
                    conversion_stats(locked_dict[x]['pronom'], 'converted', locked_dict[x]['old_file'], locked_dict[x]['file_out'])
                    logging(locked_dict[x]['file_out'] + '\t(converted ' + locked_dict[x]['pronom'] + ')')
                    pbar.set_postfix(file=pathlib.Path(locked_dict[x]['file_out']).name + ' (converted)', refresh=False)
                    pbar.update(1)
                    locked_dict[x] = {'file_out': ''}
        else:
            break
        if i % 1000 == 0 and i != 0:
            dt_local = pendulum.now()
            for x in locked_dict:
                if locked_dict[x]['file_out'] != '':
                    if dt_local.diff(locked_dict[x]['ts']).in_seconds() > 900:
                        locked_dict[x] = {'file_out': ''}
                        logging(locked_dict[x]['old_file'] + '\t(NOT CONVERTED TIMED OUT ' + locked_dict[x]['pronom'] + ')')
                        results['timedout'].append(pronom)
                        results['stats']['timedout'] += 1
time.sleep(60)
for cmd in cmds_list:
    if os.path.exists(cmd[1]) is False:
        print(cmd)
for container in containers:
    containers[container].stop()
###
for email in email_list:
    try:
        msg = extract_msg.Message(email[0])
        output_text = '==============================================================================\n'
        output_text += f'Sendt:\t\t{msg.date} ({pendulum.parse(msg.date, strict=False).isoformat()})\n'
        output_text += f'Avsender:\t{msg.sender}\n'
        output_text += f'Mottaker(e):\t' + ', '.join([f'{x.name} <{x.email}>' for x in msg.recipients]) + '\n'
        output_text += f'Vedlegg:\t' + ', '.join([f'<{x.longFilename}>' for x in msg.attachments]) + '\n'
        output_text += f'Emne:\t{msg.subject}\n'
        output_text += f'==============================================================================\n{msg.body}'
        with open(email[1], 'w') as outlook_out:
            outlook_out.write(output_text)
        conversion_stats(email[2], 'converted', email[0], email[1])
        logging(email[1] + '\t(converted)')
        pbar.set_postfix(file=pathlib.Path(email[0]).name + ' (converted)', refresh=False)
        pbar.update(1)
    except:
        copy(email[0], os.path.dirname(email[3]))
        conversion_stats(email[2], 'unconverted', email[0], email[3])
        logging(email[3] + '\t(unconverted)')
        pbar.set_postfix(file=pathlib.Path(email[0]).name + ' (copied)', refresh=False)
        pbar.update(1)
pbar.close()

print(results)
