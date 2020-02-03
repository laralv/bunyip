import subprocess
import os
import json
import shutil
import shlex
import zipfile
import pathlib
from lxml import etree
from lxml import builder
import glob
from datetime import datetime
import pprint
from hashlib import sha256
import extract_msg
import pendulum
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input", help="Siardinput", action="store")
parser.add_argument("-d", "--docs", help="Dokumentmappen", action="store")
args = parser.parse_args()

siard_filename = os.path.abspath(args.input)
document_dir = os.path.abspath(args.docs)
working_dir = os.path.abspath(os.getcwd())

pp = pprint.PrettyPrinter(indent=4)
namespace = {'siard': 'http://www.bar.admin.ch/xmlns/siard/2/table.xsd',
             'siard-metadata': 'http://www.bar.admin.ch/xmlns/siard/2/metadata.xsd',
             'xml-schema': 'http://www.w3.org/2001/XMLSchema'
            }
siard_table = 'content/schema0/table102/table102.xml'
temp_dir = 'temp/'
lobfolder = ''
tablelob_old = 'schema0/table102/lob1'
tablelob_new = 'schema0/table102/lob2'
segnr = 0
pathlib.Path(temp_dir).mkdir(parents=True, exist_ok=True)
log_file = open(temp_dir + 'logfile.txt','x')

def sha256sum(filename):
    hash = sha256()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
            hash.update(chunk)
    return hash.hexdigest()

def add_node(dict, nodename):
    node = etree.Element('{' + str(namespace['siard']) + '}' + nodename)
    node.text = dict['filename']
    return(node)

def add_node_metadataxml(nodename, lobfolder):
    node = etree.Element('{' + str(namespace['siard-metadata']) + '}' + 'column')
    etree.SubElement(node, '{' + str(namespace['siard-metadata']) + '}name').text = nodename
    etree.SubElement(node, '{' + str(namespace['siard-metadata']) + '}type').text = 'VARCHAR(255)'
    etree.SubElement(node, '{' + str(namespace['siard-metadata']) + '}typeOriginal').text = 'VARCHAR(255)'
    etree.SubElement(node, '{' + str(namespace['siard-metadata']) + '}nullable').text = 'true'
    return(node)

def add_node_xsd(nodename):
    node = etree.Element('{' + str(namespace['xml-schema']) + '}element')
    node.attrib['name'] = nodename
    node.attrib['minOccurs'] = '0'
    node.attrib['type'] = 'xs:string'
    return(node)

def siegfriedtest(sieg_filename):
    if os.path.isfile(sieg_filename) is True:
        siegfriedobjekt_ny = json.loads(subprocess.check_output(["sf", "-json", shlex.quote(sieg_filename)]))
        siegfried_output = {}
        siegfried_output['filename'] = sieg_filename
        siegfried_output['pronom'] = []
        siegfried_output['filesize'] = str(siegfriedobjekt_ny['files'][0]['filesize'])
        for file in siegfriedobjekt_ny['files']:
            for match in file['matches']:
                siegfried_output['pronom'].append(match['id'])
        siegfried_output['digest'] = sha256sum(sieg_filename)
    return siegfried_output

def conversion_stats(pronom_name, process_name, file_name):
    global results
    if pronom_name not in results[process_name]:
        results[process_name][pronom_name] = [file_name]
    else:
        results[process_name][pronom_name].append(file_name)
    results['stats'][process_name] += 1

def logging(tekst):
    global log_file
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(date + '\t' + tekst)
    log_file.write(date + '\t' + tekst + '\n')

def copy(old_file_name, file_path_new):
    pathlib.Path(file_path_new).mkdir(parents=True, exist_ok=True)
    shutil.copy2(old_file_name, file_path_new)

# Åpner Siardfil
#print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\tOpening SIARD-file')
##Utkommentert, siden dette blir tatt hånd om av 7z
zip = zipfile.ZipFile(siard_filename)
logging('Unpacking SIARD-file')
zip.extractall(temp_dir)
##Utkommentert, slutt

# Leser ut tabellen
logging('Processing SIARD, this might take a while...')
root = etree.parse(temp_dir + siard_table)
#root = etree.fromstring(content)
log_file.close()

pronom_type = {}
pronom_type['fmt/354'] = {'Name': 'Acrobat PDF/A - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/95']    = {'Name': 'Acrobat PDF/A - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/95']    = {'Name': 'Acrobat PDF/A - Portable Document Format 2b', 'convert': 'skip'}
pronom_type['fmt/479']   = {'Name': 'Acrobat PDF/A - Portable Document Format 3a', 'convert': 'skip'}
pronom_type['fmt/353']   = {'Name': 'Tagged Image File Format', 'convert': 'skip'}
pronom_type['fmt/11']    = {'Name': 'Portable Network Graphics', 'convert': 'skip'}
pronom_type['fmt/12']    = {'Name': 'Portable Network Graphics', 'convert': 'skip'}
pronom_type['fmt/13']    = {'Name': 'Portable Network Graphics', 'convert': 'skip'}
pronom_type['fmt/199']   = {'Name': 'MPEG-4 Media File', 'convert': 'skip'}
pronom_type['fmt/41']    = {'Name': 'Raw JPEG Stream', 'convert': 'skip'}
pronom_type['fmt/42']    = {'Name': 'JPEG File Interchange Format', 'convert': 'skip'}
pronom_type['fmt/43']    = {'Name': 'JPEG File Interchange Format', 'convert': 'skip'}
pronom_type['fmt/44']    = {'Name': 'JPEG File Interchange Format', 'convert': 'skip'}
pronom_type['fmt/45']    = {'Name': 'Rich Text Format 1.0-1.4', 'convert': 'skip'}
pronom_type['fmt/134']   = {'Name': 'MPEG 1/2 Audio Layer 3', 'convert': 'skip'}
pronom_type['x-fmt/111'] = {'Name': 'Plain Text File', 'convert': 'skip'}
pronom_type['x-fmt/18']  = {'Name': 'Comma Separated Values (nei...? men i praksis er dette et tekstformat...)', 'convert': 'skip'}
pronom_type['fmt/100']   = {'Name': 'Hypertext Markup Language', 'convert': 'skip'}
pronom_type['fmt/101']   = {'Name': 'Extensible Markup Language 1.0', 'convert': 'skip'}
pronom_type['fmt/102']   = {'Name': 'Extensible Hypertext Markup Language 1.1', 'convert': 'skip'}
pronom_type['fmt/103']   = {'Name': 'Extensible Hypertext Markup Language 1.1', 'convert': 'skip'}
pronom_type['fmt/91']    = {'Name': 'Scalable Vector Graphics 1.0', 'convert': 'skip'}
pronom_type['fmt/14']    = {'Name': 'Acrobat PDF 1.0 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/15']    = {'Name': 'Acrobat PDF 1.1 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/157']   = {'Name': 'Acrobat PDF/X - Portable Document Format - Exchange 1a:2001', 'convert': 'skip'}
pronom_type['fmt/158']   = {'Name': 'Acrobat PDF/X - Portable Document Format - Exchange 3:2002', 'convert': 'skip'}
pronom_type['fmt/16']    = {'Name': 'Acrobat PDF 1.2 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/17']    = {'Name': 'Acrobat PDF 1.3 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/18']    = {'Name': 'Acrobat PDF 1.4 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/19']    = {'Name': 'Acrobat PDF 1.5 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/20']    = {'Name': 'Acrobat PDF 1.6 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/276']   = {'Name': 'Acrobat PDF 1.7 - Portable Document Format', 'convert': 'skip'}
pronom_type['fmt/488']   = {'Name': 'Acrobat PDF/X - Portable Document Format - Exchange PDF/X-4', 'convert': 'skip'}

pronom_type['fmt/39']    = {'Name': 'Microsoft Word Document 6.0/95', 'convert': 'libreoffice'}
pronom_type['fmt/136']   = {'Name': 'OpenDocument Text 1.0', 'convert': 'libreoffice'}
pronom_type['fmt/214']   = {'Name': 'Microsoft Excel for Windows (lett rot...)', 'convert': 'libreoffice'}
pronom_type['fmt/126']   = {'Name': 'Microsoft Powerpoint Presentation', 'convert': 'libreoffice'}
pronom_type['fmt/215']   = {'Name': 'Microsoft Powerpoint for Windows', 'convert': 'libreoffice'}
pronom_type['fmt/487']   = {'Name': 'Macro Enabled Microsoft Powerpoint', 'convert': 'libreoffice'}
pronom_type['fmt/290']   = {'Name': 'OpenDocument Text (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/291']   = {'Name': 'OpenDocument Text (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/355']   = {'Name': 'Rich Text Format (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/40']    = {'Name': 'Microsoft Word Document (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/412']   = {'Name': 'Microsoft Word for Windows (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/445']   = {'Name': 'Microsoft Excel Macro-Enabled (rot, totalt ubrukelig, lang konverteringstid/hang seg)', 'convert': 'libreoffice'}
pronom_type['fmt/50']    = {'Name': 'Rich Text Format (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/523']   = {'Name': 'Macro enabled Microsoft Word Document OOXML (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/53']    = {'Name': 'Rich Text Format (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/61']    = {'Name': 'Microsoft Excel 97 Workbook (xls) (rot, som alle andre exceldokumenter)', 'convert': 'libreoffice'}
pronom_type['fmt/597']   = {'Name': 'Microsoft Word Template (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/598']   = {'Name': 'Microsoft Excel Template (ok)', 'convert': 'libreoffice'}
pronom_type['fmt/96']    = {'Name': 'Hypertext Markup Language (problemer med blanke sider?, signaturer, ser ut som libreoffice ikke liker å få beskjed om fonter den ikke har)', 'convert': 'libreoffice'}
pronom_type['fmt/99']    = {'Name': 'Hypertext Markup Language (problemer med blanke sider?, signaturer, ser ut som libreoffice ikke liker å få beskjed om fonter den ikke har)', 'convert': 'libreoffice'}
pronom_type['fmt/258']   = {'Name': 'Microsoft Works Word Processor 5-6', 'convert': 'libreoffice'}
pronom_type['fmt/609']   = {'Name': 'Microsoft Word (Generic) 6.0-2003', 'convert': 'libreoffice'}
pronom_type['fmt/38']    = {'Name': 'Microsoft Word for Windows Document 2.0', 'convert': 'libreoffice'}
pronom_type['fmt/595']   = {'Name': 'Microsoft Excel Non-XML Binary Workbook 2007 onwards', 'convert': 'libreoffice'}
pronom_type['fmt/59']    = {'Name': 'Microsoft Excel 5.0/95 Workbook (xls) 5/95', 'convert': 'libreoffice'}
pronom_type['x-fmt/88']  = {'Name': 'Microsoft Powerpoint Presentation 4.0', 'convert': 'libreoffice'}
pronom_type['fmt/295']   = {'Name': 'OpenDocument Spreadsheet 1.2', 'convert': 'libreoffice'}

pronom_type['fmt/116']   = {'Name': 'Windows Bitmap', 'convert': 'skip'}
pronom_type['fmt/3']     = {'Name': 'Graphics Interchange Format', 'convert': 'skip'}
pronom_type['fmt/4']     = {'Name': 'Graphics Interchange Format', 'convert': 'skip'}
pronom_type['fmt/117']   = {'Name': 'Windows Bitmap 3.0 NT', 'convert': 'skip'}
pronom_type['fmt/563']   = {'Name': 'Adobe Illustrator', 'convert': 'skip'}
pronom_type['fmt/583']   = {'Name': 'Vector Markup Language (feilakkreditert)', 'convert': 'skip'}
pronom_type['fmt/754']   = {'Name': 'Microsoft Word Document (Password Protected) (nope)', 'convert': 'skip'}
pronom_type['x-fmt/263'] = {'Name': 'ZIP Format', 'convert': 'skip'}
pronom_type['x-fmt/266'] = {'Name': 'GZIP Format', 'convert': 'skip'}
pronom_type['x-fmt/384'] = {'Name': 'Quicktime', 'convert': 'skip'}
pronom_type['x-fmt/45']  = {'Name': 'Microsoft Word Document Template', 'convert': 'skip'}
pronom_type['x-fmt/390'] = {'Name': 'Exchangeable Image File Format (Compressed)', 'convert': 'skip'}
pronom_type['x-fmt/391'] = {'Name': 'Exchangeable Image File Format (Compressed)', 'convert': 'skip'}
pronom_type['fmt/395']   = {'Name': 'vCard', 'convert': 'skip'}
pronom_type['fmt/645']   = {'Name': 'Exchangeable Image File Format (Compressed)', 'convert': 'skip'}
pronom_type['fmt/657']   = {'Name': 'Open XML Paper Specification', 'convert': 'skip'}
pronom_type['fmt/356']   = {'Name': 'Adaptive Multi-Rate Audio', 'convert': 'skip'}
pronom_type['x-fmt/454'] = {'Name': 'Microsoft Internet Shortcut', 'convert': 'skip'}
pronom_type['UNKNOWN']   = {'Name': 'Unknown', 'convert': 'skip'}
pronom_type['fmt/881']   = {'Name': 'Microsoft Document Imaging File Format', 'convert': 'skip'}
pronom_type['x-fmt/429'] = {'Name': 'Microsoft Web Archive', 'convert': 'skip'}
pronom_type['fmt/208']   = {'Name': 'Binary File', 'convert': 'skip'}
pronom_type['fmt/440']   = {'Name': 'Microsoft Project 2007', 'convert': 'skip'}
pronom_type['x-fmt/257'] = {'Name': 'Microsoft Publisher 2002', 'convert': 'skip'}
pronom_type['fmt/473']   = {'Name': 'Microsoft Office Owner File', 'convert': 'skip'}
pronom_type['fmt/132']   = {'Name': 'Windows Media Audio', 'convert': 'skip'}
pronom_type['fmt/133']   = {'Name': 'Windows Media Video', 'convert': 'skip'}
pronom_type['fmt/388']   = {'Name': 'Internet Calendar and Scheduling format', 'convert': 'skip'}
pronom_type['fmt/357']   = {'Name': '3GPP Audio/Video File', 'convert': 'skip'}
pronom_type['x-fmt/119'] = {'Name': 'Windows Metafile Image', 'convert': 'skip'}
pronom_type['fmt/561']   = {'Name': 'Adobe Illustrator 12.0', 'convert': 'skip'}
pronom_type['fmt/443']   = {'Name': 'Microsoft Visio Drawing 2003-2010', 'convert': 'skip'}

pronom_type['x-fmt/430'] = {'Name': '', 'convert': 'email'}

#Logging
results = {}
results['converted'] = {}
results['unconverted'] = {}
results['new unconverted'] = {}
results['discrepancies'] = []
results['timedout'] = []
results['stats'] = {}
results['stats']['converted'] = 0
results['stats']['unconverted'] = 0
results['stats']['new unconverted'] = 0
results['stats']['timedout'] = 0
#Konstruerer opp filnavn fra SIARD-filen.
for x in root.xpath('siard:row', namespaces=namespace):
    log_file = open(temp_dir + 'logfile.txt','a')
    args_output = {}
    file_name = document_dir
    if x.xpath('siard:c26', namespaces=namespace) != []:
        file_name += x.xpath('siard:c26', namespaces=namespace)[0].text + '/'
    else:
        file_name += '/'
    if x.xpath('siard:c27', namespaces=namespace) != []:
        file_name += x.xpath('siard:c27', namespaces=namespace)[0].text
    else:
        file_name += ''
    if x.xpath('siard:c28', namespaces=namespace) != []:
        file_name += x.xpath('siard:c28', namespaces=namespace)[0].text
    else:
        file_name += ''
    if x.xpath('siard:c29', namespaces=namespace) != []:
        file_name += '.' + x.xpath('siard:c29', namespaces=namespace)[0].text
    else:
        file_name += '.'
    if os.path.isfile(file_name) is False:
        results['discrepancies'].append(file_name)
#        logging('Could not find ' + file_name + ' (missing reference)')
        continue
    args_output['file_name'] = file_name
#siegfriedtest av ukonvertert
    args_output['gammel'] = siegfriedtest(file_name)
    args_output['gammel']['filename'] = os.path.relpath(file_name, working_dir)
    args_output['ny'] = {}
    for pronom_name in args_output['gammel']['pronom']:
        if pronom_name not in pronom_type:
            conversion_stats(pronom_name, 'new unconverted', args_output['gammel']['filename'])
            pronom_type[pronom_name] = {'Name': 'unknown...', 'convert': 'skip'}
        if pronom_type[pronom_name]['convert'] == 'skip':
            conversion_stats(pronom_name, 'unconverted', args_output['gammel']['filename'])
        if pronom_type[pronom_name]['convert'] == 'libreoffice':
            try:
                subprocess.run(['libreoffice --headless --convert-to pdf --outdir ' + shlex.quote(os.path.dirname(args_output['gammel']['filename'])) + ' ' + shlex.quote(file_name)], shell=True, stdout=subprocess.DEVNULL, timeout=600)
                args_output['ny']['filename'] = os.path.dirname(args_output['gammel']['filename']) + '/' + pathlib.Path(args_output['gammel']['filename']).stem + '.pdf'
                conversion_stats(pronom_name, 'converted', args_output['ny']['filename'])
            except subprocess.TimeoutExpired:
                conversion_stats(pronom_name, 'timedout', args_output['gammel']['filename'])
                conversion_stats(pronom_name, 'unconverted', args_output['gammel']['filename'])
                logging(f"Timed out {args_output['gammel']['filename']}\t ({args_output['gammel']['pronom']})")
                args_output['ny'] = {}
        if pronom_type[pronom_name]['convert'] == 'email':
            try:
                msg = extract_msg.Message(file_name)
                output_text = '==============================================================================\n'
                output_text += f'Sendt:\t\t{msg.date} ({pendulum.parse(msg.date, strict=False).isoformat()})\n'
                output_text += f'Avsender:\t{msg.sender}\n'
                output_text += f'Mottaker(e):\t' + ', '.join([f'{x.name} <{x.email}>' for x in msg.recipients]) + '\n'
                output_text += f'Vedlegg:\t' + ', '.join([f'<{x.longFilename}>' for x in msg.attachments]) + '\n'
                output_text += f'Emne:\t{msg.subject}\n'
                output_text += f'==============================================================================\n{msg.body}'
                args_output['ny']['filename'] = os.path.dirname(args_output['gammel']['filename']) + '/' + pathlib.Path(args_output['gammel']['filename']).stem + '.txt'
                with open(args_output['ny']['filename'], 'w') as outlook_out:
                    outlook_out.write(output_text)
                conversion_stats(pronom_name, 'converted', args_output['ny']['filename'])
            except:
                conversion_stats(pronom_name, 'unconverted', args_output['gammel']['filename'])
    if args_output['ny'] != {}:
        if os.path.isfile(args_output['ny']['filename']) is True:
            args_output['ny'] = siegfriedtest(args_output['ny']['filename'])
            logging(f"{results['stats']['converted']}/{results['stats']['unconverted']}\t{args_output['gammel']['filename']}\t ({args_output['gammel']['pronom']} to {args_output['ny']['pronom']})")
            x.append(add_node(args_output['ny'], 'c52'))
    else:
        if os.path.isfile(args_output['gammel']['filename']) is True:
            x.append(add_node(args_output['gammel'], 'c52'))
    log_file.close()
results_file = open(temp_dir + 'results.txt','w')
## results dump:
results_out = ''
for value in results['stats'].keys():
    results_out += f"{value}: {results['stats'][value]}\n"
results_out += '\n\n'
if results['discrepancies'] != []:
    results_out += f"Filreferanser som manglet filer:\n{', '.join(results['discrepancies'])}\n\n"
if results['timedout'] != []:
    results_out += f"Filer som timet ut i konverteringsprosessen:\n{', '.join(results['timedout'])}\n\n"
if results['new unconverted'] != {}:
    results_out += 'Nye pronomkoder som ikke har vært i bruk før:\n'
    for value in results['new unconverted']:
        results_out += f"{value}: {len(results['new unconverted'][value])} forekomster"
results_file.write(results_out)
results_file.close()

root.write(temp_dir+ siard_table, pretty_print=True, encoding='utf-8')
## Legger til felter i metadata.xml
root_metadata = etree.parse(temp_dir + "header/metadata.xml")
root_metadata_column = root_metadata.xpath('/siard-metadata:siardArchive/siard-metadata:schemas/siard-metadata:schema/siard-metadata:tables/siard-metadata:table/siard-metadata:folder[text()="table102"]/../siard-metadata:columns', namespaces=namespace)[0]
root_metadata.xpath('/siard-metadata:siardArchive/siard-metadata:schemas/siard-metadata:schema/siard-metadata:tables/siard-metadata:table/siard-metadata:folder[text()="table102"]/../siard-metadata:columns', namespaces=namespace)[0]
root_metadata_column.append(add_node_metadataxml('filreferanse', tablelob_old))
root_metadata.write(temp_dir + "header/metadata.xml", pretty_print=True, encoding='utf-8')

## Legger til i xsden til tabellen
root_xsd = etree.parse(temp_dir + siard_table[:-3] + 'xsd')
root_xsd_element = root_xsd.xpath('//xml-schema:complexType[@name = "recordType"]/xml-schema:sequence', namespaces=namespace)[0]
root_xsd_element.append(add_node_xsd('c52'))
root_xsd.write(temp_dir + siard_table[:-3] + 'xsd', pretty_print=True, encoding='utf-8')
