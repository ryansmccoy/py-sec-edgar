import logging

logger = logging.getLogger(__name__)

import os
import re

import chardet
import lxml.html

from .parse.header import header_parser
from .utilities import file_size, format_filename, uudecode


def extract(filing_json):
    """
    Extracts the contents of a complete submission filing
    """
    filing_contents = {}

    if not os.path.exists(filing_json['extracted_filing_directory']) and not os.path.exists(filing_json['extracted_filing_directory'] + ".zip"):

        logger.info("\n\n\n\n\tExtracting Filing Documents:\n")

        try:

            filing_contents = extract_complete_submission_filing(filing_json['filing_filepath'], output_directory=filing_json['extracted_filing_directory'])

        except UnicodeDecodeError as E:
            logger.error(f"\n\n\n\nError Decoding \n\n{E}")

        logger.info("\n\n\n\n\tExtraction Complete\n")

    return filing_contents


def extract_complete_submission_filing(filepath, output_directory=None):
    """
    Given a filepath
    :param filepath:
    :param output_directory:
    :return:
    """

    elements_list = [('FILENAME', './/filename'), ('TYPE', './/type'),
                     ('SEQUENCE', './/sequence'), ('DESCRIPTION', './/description')]

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    else:
        logger.info(f"Folder Already Exists {output_directory}")
        return

    logger.info(f"extracting documents to {output_directory}")

    xbrl_doc = re.compile(r'<DOCUMENT>(.*?)</DOCUMENT>', re.DOTALL)
    xbrl_text = re.compile(r'<(TEXT|text)>(.*?)</(TEXT|text)>', re.MULTILINE | re.DOTALL)

    try:
        # or codecs.open on Python 2
        raw_text = open(filepath, "rb").read()
        result = chardet.detect(raw_text)
        charenc = result['encoding']

        with open(filepath, encoding=charenc) as f:
            raw_text = f.read()

    except:
        with open(filepath, "rb") as f:
            raw_bytes = f.read()
            # Decode bytes to string for regex processing
            try:
                raw_text = raw_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    raw_text = raw_bytes.decode('latin-1')
                except UnicodeDecodeError:
                    raw_text = raw_bytes.decode('utf-8', errors='ignore')

    filing_header = header_parser(raw_text)

    header_filepath = os.path.join(output_directory, f"{os.path.basename(output_directory)}_FILING_HEADER.csv")

    filing_header.to_csv(header_filepath)

    documents = xbrl_doc.findall(raw_text)

    filing_documents = {}

    for i, document in enumerate(documents, start=1):
        uue_filepath = None
        filing_document = {}

        lxml_html = lxml.html.fromstring(document)
        root = lxml_html.getroottree()

        for (element, element_path) in elements_list:
            try:
                filing_document[f"{element}"] = root.xpath(f"{element_path}")[0].text.strip()
            except:
                filing_document[f"{element}"] = ""

        raw_text = xbrl_text.findall(document)
        raw_text = raw_text[0][1].replace("<XBRL>", "").replace("</XBRL>", "").strip()
        raw_text = raw_text.replace("<XML>", "").replace("</XML>", "").strip()

        if raw_text.lower().startswith("begin") or document.lower().startswith("begin"):

            uue_filepath = os.path.join(output_directory, filing_document['FILENAME'] + ".uue")
            output_filepath = os.path.join(output_directory, uue_filepath.replace(".uue", ""))
            output_filename = os.path.basename(output_filepath)

            with open(uue_filepath, 'w', encoding=charenc) as f:
                f.write(raw_text)

            uudecode(uue_filepath, out_file=output_filepath)

        else:
            doc_num = f"{int(filing_document['SEQUENCE'])}".zfill(4)

            try:
                output_filename = f"{doc_num}-({filing_document['TYPE']}) {filing_document['DESCRIPTION']} {filing_document['FILENAME']}"
            except:
                output_filename = f"{doc_num}-({filing_document['TYPE']}) {filing_document['FILENAME']}".replace(" ", "_").replace(":", "").replace("__", "_")

            output_filename = output_filename.replace(" ", "_").replace(":", "").replace("__", "_")

            output_filename = format_filename(output_filename)
            output_filepath = os.path.join(output_directory, output_filename)

            with open(output_filepath, 'w', encoding=charenc) as f:
                f.write(raw_text)

        filing_document['RELATIVE_FILEPATH'] = os.path.join(os.path.basename(output_directory), output_filepath)
        filing_document['DESCRIPTIVE_FILEPATH'] = output_filename

        filing_document['FILE_SIZE'] = file_size(output_filepath)
        filing_document['FILE_SIZE_BYTES'] = os.stat(output_filepath).st_size

        filing_documents[i] = filing_document

        if uue_filepath:
            os.remove(uue_filepath)

    return filing_documents
