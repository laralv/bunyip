import glob
import docker
import argparse
import csv
import os
import pathlib
import random
import time
import pendulum
import zmq

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.bind("tcp://*:5558")

client = docker.from_env()
docker_image = 'laralv/ubuntu-libreoffice:latest'
# Gjøres om til et dockerimage som kan pulles

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help="Mappen som skal konverteres", action="store")
parser.add_argument("-o", "--output", help="Mappen dokumentene skal flyttes til", action="store")
parser.add_argument("-l", "--logging", help="Mappen der konverteringsloggene skal", action="store")
parser.add_argument("-c", "--cpukjerner", help="Antall dockerinstanser som skal settes opp (defaultverdi er antall CPU-kjerner)", default=os.cpu_count())

args = parser.parse_args()
cpu_workers = int(args.cpukjerner)
output_dir = os.path.abspath(args.output)
input_dir = os.path.abspath(args.input)
log_dir = os.path.abspath(args.logging)

pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

## Lager opp ett csvdokument for hver dockerinstans.
input_filelist = []
for filename in glob.iglob(input_dir + '/**/*', recursive=True):
    if os.path.isfile(filename) is True:
        input_filelist.append(os.path.relpath(filename, input_dir))

#random.shuffle(input_filelist)
#pathlib.Path(log_dir + '/input').mkdir(parents=True, exist_ok=True)
#chunksize = round(len(input_filelist) / cpu_workers)
#antall = 1

#for i in range(0, len(input_filelist), chunksize):
#    with open(log_dir + f'/input/{antall}.csv','w') as f:
#        writer = csv.writer(f)
#        for x in input_filelist[i:i+chunksize]:
#            writer.writerow([x])
#    antall += 1
input_number_of_files = len(input_filelist)
#input_filelist = ''

## Setter opp dockerinstanser

containers = {}
locked_dict = {}
for container in range(1, cpu_workers+1):
    containers[container] = client.containers.run(docker_image, '/bin/bash',
                                                                detach=True,
                                                                tty=True,
                                                                volumes={log_dir: {'bind': '/opt/log', 'mode': 'rw'},
                                                                    input_dir: {'bind': '/mnt/disk1', 'mode': 'rw'},
                                                                    output_dir: {'bind': '/mnt/disk2', 'mode': 'rw'},
                                                                    },
                                                                working_dir='/mnt/disk1/',
#                                                                ports={'5558/tcp': 5558},
                                                                )
#    containers[container].exec_run('sf -update')
# Middlertidig hjem i /opt/
#    containers[container].exec_run('pip3 install zmq')
#    containers[container].exec_run(f"python3 /opt/log/convert.py -n {container}", user='libreoffice', detach=True)
    locked_dict[container] = False
    print(f'Container {container} is running')

## NYTT SCRIPT
output = []
dt = pendulum.now()
i = 0
# kan være en for-loop
while i < input_number_of_files:
    for x in locked_dict:
        if i < input_number_of_files:
            if locked_dict[x] is False:
                containers[x].exec_run(f"python3 /opt/log/convert2.py -n {x} -f {input_filelist[i]}", user='libreoffice', detach=True)
                locked_dict[x] = True
                i += 1
    test = receiver.recv_json()
    if 'container' in test:
        locked_dict[int(test['container'])] = False
        output.append(test)
        print(f"{pendulum.now()}\t{i} / {input_number_of_files} - {test['output']['filename']} ({test['input']['pronom']} to {test['output']['pronom']}) ({test['container']})")

#    for y in test:
#        print(y['container'])
#        print(y['output'])
## GAMMELT SCRIPT

#lock = {}
#for y in range(1, cpu_workers+1):
#    lock[y] = 'running'
#while not all(value == 'done' for value in lock.values()):
#    test = receiver.recv()
#    print(test)
#    for x in lock:
#        if pathlib.Path(f'{log_dir}/output/lock/{x}').is_file is True:
#            lock[x] = 'done'
#    output_filecounter = 0
#    for filename in glob.iglob(output_dir + '/**/*', recursive=True):
#        if os.path.isfile(filename) is True:
#            output_filecounter += 1
#    print(f'{pendulum.now().format("YYYY-MM-DD HH:mm:ss")}\t{output_filecounter} of {input_number_of_files}')
#    print(lock)
#    time.sleep(10)

# python3 /home/lars/politipilot/git/controller.py -i dokumenter/09-hist/dir1 -o test/ -l log/
# docker kill $(docker ps -q)
