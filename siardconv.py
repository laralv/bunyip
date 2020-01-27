from lxml import etree
import zipfile

namespace = {'siard': 'http://www.bar.admin.ch/xmlns/siard/2/table.xsd', 'siard-metadata': 'http://www.bar.admin.ch/xmlns/siard/2/metadata.xsd', 'xml-schema': 'http://www.w3.org/2001/XMLSchema'}
siard_table = 'content/schema0/table102/table102.xml'
siard_filename = '09_hedmark_2003-2019_20191116.siard'

print('Unpacking SIARD-file')
zip = zipfile.ZipFile(siard_filename)
print('Processing SIARD, this might take a while...')
root = etree.parse(temp_dir + siard_table)

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
        logging('Could not find ' + file_name + ' (missing reference)')
        continue
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
