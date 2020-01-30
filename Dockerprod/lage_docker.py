import docker
import os
import pendulum
client = docker.from_env()

test = client.containers.run('ubuntu:latest', '/bin/bash', detach=True, tty=True, volumes={os.path.realpath('.'): {'bind': '/mnt/disk1', 'mode': 'rw'}}, working_dir='/mnt/disk1/')
test.exec_run('adduser --home=/home/libreoffice --disabled-password --gecos "" --shell=/bin/bash libreoffice')
test.exec_run('apt update')
test.exec_run('apt upgrade -y')
test.exec_run('apt-get install -y software-properties-common fonts-liberation fonts-droid-fallback fonts-freefont-ttf')
test.exec_run('add-apt-repository ppa:libreoffice/ppa')
test.exec_run('apt update')
test.exec_run('apt-get install -y libreoffice')
test.exec_run('libreoffice --headless --cat "test"', user='libreoffice')
## legg inn egen som laster inn registrymodifciations og pronom-json
test.exec_run('cp /mnt/disk1/registrymodifications.xcu /home/libreoffice/.config/libreoffice/4/user/', user='libreoffice')
test.exec_run('cp /mnt/disk1/pronomtyper.json /opt/', user='libreoffice')
## Installere siegfried
test.exec_run('apt-key adv --fetch-keys https://bintray.com/user/downloadSubjectPublicKey?username=bintray')
test.exec_run("add-apt-repository 'deb http://dl.bintray.com/siegfried/debian wheezy main'")
test.exec_run('apt-get install -y siegfried')
test.exec_run('apt-get install -y python3-pip')
test.exec_run('apt-get install -y net-tools')
test.exec_run('pip3 install extract_msg')
test.exec_run('pip3 install pendulum')
test.exec_run('pip3 install zmq')
instansnavn = f"laralv/ubuntu-libreoffice"
test.commit(instansnavn)
print(instansnavn)


#test.exec_run('libreoffice --headless -convert-to pdf --outdir test dokumenter/09-hist/dir00000/00000003.doc && libreoffice --headless -convert-to pdf --outdir test dokumenter/09-hist/dir00000/00000049.doc', user='libreoffice')
