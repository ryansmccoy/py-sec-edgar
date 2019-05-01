import pytest

from click.testing import CliRunner
import py_sec_edgar

from py_sec_edgar.filing import SecEdgar

filing = {
    'CIK': 104169,
    'Company Name': 'Walmart Inc.',
    'Date Filed': '2019-03-28',
    'Filename': 'edgar/data/104169/0000104169-19-000016.txt',
    'Form Type': '10-K',
    'cik_directory': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\',
    'extracted_filing_directory': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\000010416919000016',
    'filing_filepath': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\0000104169-19-000016.txt',
    'filing_folder': '000010416919000016',
    'filing_url': 'https://www.sec.gov/Archives/edgar/data/104169/0000104169-19-000016.txt',
    'filing_zip_filepath': 'C:\\sec_gov\\Archives\\edgar\\data\\104169\\0000104169-19-000016.zip',
    'published': '2019-03-28',
    'url': 'https://www.sec.gov/Archives/edgar/data/104169/0000104169-19-000016.txt'
}

def test_filing():
    sec_filing = SecEdgar(filing, download=False, load=False, parse_header=False, process_filing=False)
    sec_filing.download()
    assert sec_filing.is_downloaded == True
    sec_filing.load()
    assert sec_filing.is_loaded == True
    sec_filing.parse_header()
    assert sec_filing.is_parsed_header == True
