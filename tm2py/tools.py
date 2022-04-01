"""Tools module for common resources / shared code and "utilities" in the tm2py package."""
import multiprocessing
from multiprocessing.sharedctypes import Value
import os
import re

from typing import Union


def parse_num_processors(value: Union[str, int, float]):
    """Convert input value (parse if string) to number of processors.
    Args:
        value: an int, float or string; string value can be "X" or "MAX-X"
    Returns:
        An int of the number of processors to use

    Raises:
        Exception: Input value exceeds number of available processors
        Exception: Input value less than 1 processors
    """
    max_processors = multiprocessing.cpu_count()
    if isinstance(value, str):
        result = value.upper()
        if result == "MAX":
            return max_processors
        if re.match("^[0-9]+$", value):
            return int(value)
        result = re.split(r"^MAX[\s]*-[\s]*", result)
        if len(result) == 2:
            return max(max_processors - int(result[1]), 1)
        raise Exception(f"Input value {value} is an int or string as 'MAX-X'")

    result = int(value)
    if result > max_processors:
        raise Exception(f"Input value {value} greater than available processors")
    if result < 1:
        raise Exception(f"Input value {value} less than 1 processors")
    return value


def _download(url,target_destination):
    """Download fie with redirects (i.e. box)

    Args:
        url (_type_): _description_
        target_destination (_type_): _description_

    Raises:
        ValueError: _description_
    """    
    import urllib.request
    _request = urllib.request.Request(url)
    # Handle Redirects using solution shown by user: metatoaster on StackOverflow
    # https://stackoverflow.com/questions/62384020/python-3-7-urllib-request-doesnt-follow-redirect-url
    try:
        _response = urllib.request.urlopen(_request)
    except urllib.error.HTTPError as e:
        if e.status != 307:
            raise  ValueError(f"HTTP Error {e.status}")
        _redirected_url = urllib.parse.urljoin(url, e.headers['Location'])
        _response = urllib.request.urlopen(_redirected_url)
    with open(target_destination, 'wb') as f:
        f.write(_response.read())

def download_unzip(
    url: str, out_base_dir: str, target_dir: str, zip_filename: str = "test_data.zip"
) -> None:
    """Downloads and unzips a file from a URL.

    Args:
        url (str): Full URL do download from.
        out_base_dir (str): Where to unzip the file.
        target_dir (str): What to unzip the file as.
        zip_filename (str, optional): Filename to store zip file as. Defaults to "test_data.zip".
    """
    import urllib.request

    target_zip = os.path.join(out_base_dir, zip_filename)

    if not os.path.isdir(out_base_dir):
        os.makedirs(out_base_dir)

    _request = urllib.request.Request(url)

    target_zip = _download(url,target_zip)

    import zipfile

    with zipfile.ZipFile(target_zip, "r") as zip_ref:
        zip_ref.extractall(target_dir)
    os.remove(target_zip)
