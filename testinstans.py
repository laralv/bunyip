import docker
import os

client = docker.from_env()
docker_image = 'laralv/ubuntu-libreoffice:latest'

output_dir = os.path.abspath('test')
input_dir = os.path.abspath('dokumenter/09-hist/dir1/')
log_dir = os.path.abspath('log')

test = client.containers.run(docker_image, '/bin/bash',
                            detach=True,
                            tty=True,
                            volumes={log_dir: {'bind': '/opt/log', 'mode': 'rw'},
                                input_dir: {'bind': '/mnt/disk1', 'mode': 'rw'},
                                output_dir: {'bind': '/mnt/disk2', 'mode': 'rw'},
                                },
                            working_dir='/mnt/disk1/')

test.exec_run(f"python3 /opt/log/convert.py -n 1", user='libreoffice')
