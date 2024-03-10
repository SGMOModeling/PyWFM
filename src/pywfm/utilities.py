import os
import requests

from io import BytesIO
from zipfile import ZipFile


def get_iwfm_url(iwfm_version):
    """
    Return the url for the IWFM version from CNRA Open Data Platform

    Parameters
    ----------
    iwfm_version : int or str
        IWFM version to obtain url from CKAN API

    Returns
    -------
    str
        url of IWFM Zip Archive
    """
    root_url = "https://data.cnra.ca.gov"

    # dataset name i.e. https://data.cnra.ca.gov/dataset/iwfm-integrated-water-flow-model
    dataset_id = "iwfm-integrated-water-flow-model"

    # create the url for the Open Data API request
    api_endpoint = f"{root_url}/api/3/action/package_show?id={dataset_id}"

    try:
        # Make GET request to the CKAN API
        response = requests.get(api_endpoint)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse JSON response
            data = response.json()

            # Extract resources from the response
            resources = data["result"]["resources"]

            # get resource names
            resource_urls = {
                resource["name"].split(" ")[0]: resource["url"]
                for resource in resources
                if resource["format"] == "ZIP"
            }

            match = [key for key in resource_urls.keys() if str(iwfm_version) in key]

            if not match:
                raise ValueError(
                    "IWFM version provided was not found. Please check the version and try again."
                )

            return resource_urls[match[0]]
        else:
            print(f"Failed to retrieve dataset. Status code: {response.status_code}")

    except requests.RequestException as e:
        print(f"Error fetching dataset: {e}")


def download_zip(url, out_path):
    """
    Download and extract zip file from url

    Parameters
    ----------
    url : str
        url to send get request to download zip

    out_path : str
        path to save zip contents

    Returns
    -------
    None
        extracts contents of zip archive to out_path
    """
    # create directory to store extracted contents of zip archive
    os.makedirs(out_path, exist_ok=True)

    # make GET request to the url
    response = requests.get(url)

    # if request is successful, extract contents of the zip archive
    if response.status_code == 200:
        zip_contents = BytesIO(response.content)
        with ZipFile(zip_contents, "r") as zip:
            zip.extractall(out_path)


def extract_all_zips(directory):
    """
    Recursively extract all zip files in a directory

    Parameters
    ----------
    directory : str
        relative or absolute path to search for zips to extract

    Returns
    -------
    None
        extracted zips are saved
    """
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith("zip"):
                zip_path = os.path.join(root, f)

                with ZipFile(zip_path, "r") as zf:
                    zf.extractall(root)

        for d in dirs:
            extract_all_zips(os.path.join(root, d))
