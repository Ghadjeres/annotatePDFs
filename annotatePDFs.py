# Command to get bounding boxes
#  pdftotext -layout -bbox -f 1 -l 1 test_file.pdf
from pathlib import Path
from xml.dom import minidom

import click
import yaml
from PyPDF2 import PdfFileReader, PdfFileWriter
from tempfile import NamedTemporaryFile
import os
import unicodedata


def get_bounding_box(word_dom, page_height, offset=1):
    xMin = float(word_dom.getAttribute('xMin'))
    xMax = float(word_dom.getAttribute('xMax'))
    yMin = float(word_dom.getAttribute('yMin'))
    yMax = float(word_dom.getAttribute('yMax'))
    return (xMin - offset, page_height - yMin + 2 * offset,
            xMax + offset, page_height - yMax - offset)


def normalize(string):
    return string.lower().lstrip().rstrip()


def getText(node):
    rc = []
    for text_node in node.childNodes:
        if text_node.nodeType == text_node.TEXT_NODE:
            rc.append(text_node.data)
    return unicodedata.normalize('NFKD',
                                 ''.join(rc).lower().lstrip().rstrip())
    # .encode(
    # 'utf8', 'ignore')


def load_url_dict(dict_yaml_file):
    dictionary = yaml.safe_load(open(dict_yaml_file))
    # lowercase
    normalized_dictionary = {}
    for k, v in dictionary.items():
        normalized_key = normalize(k)
        normalized_dictionary.update({normalized_key: v})
    dictionary = normalized_dictionary
    return dictionary


def _add_URI(input_file_name, output_file_name, dict_of_urls, border=True):
    """

    :param input_file_name: Path
    :param output_file_name: Path
    :param dict_of_urls:
    :param border:
    :return:
    """
    print(f'Processing {input_file_name}')
    input_file_name = str(input_file_name)
    output_file_name = str(output_file_name)
    # convert p
    # border argument
    if border:
        border = [1, 1, 1]
    else:
        border = [0, 0, 0]

    # input and output pdfs
    input = PdfFileReader(input_file_name)
    output = PdfFileWriter()

    for page_id in range(input.numPages):
        page = input.getPage(page_id)
        output.addPage(page=page)
        with NamedTemporaryFile() as tmp_file:
            # call pdftotext to compute bounding boxes
            xml_filepath = tmp_file.name
            command = 'pdftotext -f {} -l {} -bbox {} {}'.format(
                str(page_id + 1),
                str(page_id + 1),
                input_file_name,
                xml_filepath
            )
            os.system(command)

            try:
                # parse the html file
                e = minidom.parse(xml_filepath)
                # get page height
                page_dom = e.getElementsByTagName('page')[0]
                page_height = float(page_dom.getAttribute('height'))

                for word_dom in e.getElementsByTagName('word'):
                    text = getText(word_dom)
                    if text in dict_of_urls:
                        url_value = str(dict_of_urls[text])
                        # parse bounding boxes
                        bbox = get_bounding_box(word_dom,
                                                page_height)
                        # add URI
                        output.addURI(page_id, url_value, bbox,
                                      border=border)

            except Exception as e:
                print('Bounding boxes of {} page {} could not be parsed'.format(
                    input_file_name,
                    page_id
                ))
                print(f'Error: {e}')

    # write file
    s_out = open(output_file_name, 'wb')
    output.write(s_out)
    s_out.close()
    print(f'File {output_file_name} written')


@click.command()
@click.argument('input_file_or_dir',
                type=click.Path(exists=True, resolve_path=True))
@click.argument('yaml_dict_of_urls',
                type=click.Path(exists=True, resolve_path=True))
@click.option('--no-border',
              is_flag=True)
def annotate(input_file_or_dir, yaml_dict_of_urls, no_border=False):
    """

    :param input_file_or_dir:
    if it is a directory, creates a new directory called
    input_file_or_dir_annotated and add URIs to all pdfs files in it
    if it is a file, creates a new file called
    input_file_or_dir_annotated next to it
    :param yaml_dict_of_urls:
    :return:
    """
    # load dict:
    yaml_dict = load_url_dict(yaml_dict_of_urls)
    input_file_or_dir = Path(input_file_or_dir)

    if input_file_or_dir.is_dir():
        output_name = ''.join([input_file_or_dir.stem,
                               '_annotated',
                               input_file_or_dir.suffix]
                              )
        output_dir_name = input_file_or_dir.with_name(output_name)
        if not output_dir_name.exists():
            os.mkdir(output_dir_name)
        for pdf in input_file_or_dir.glob('*.pdf'):
            input_file = pdf
            output_name = ''.join([input_file.stem,
                                   # '_annotated',
                                   input_file.suffix]
                                  )
            output_file = output_dir_name / output_name
            _add_URI(input_file_name=input_file,
                     output_file_name=output_file,
                     dict_of_urls=yaml_dict,
                     border=not no_border
                     )


    elif input_file_or_dir.is_file():
        assert input_file_or_dir.suffix == '.pdf'
        output_name = ''.join([input_file_or_dir.stem,
                               '_annotated',
                               input_file_or_dir.suffix]
                              )
        output_file = input_file_or_dir.with_name(output_name)

        _add_URI(input_file_name=input_file_or_dir,
                 output_file_name=output_file,
                 border=not no_border,
                 dict_of_urls=yaml_dict
                 )
    else:
        raise NameError


if __name__ == '__main__':
    annotate()
