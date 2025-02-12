import livekit.api
from dotenv import load_dotenv
import os

load_dotenv()

# AIRTABLE STUFF
AIRTABLE_API_KEY = os.environ['AIRTABLE_API_KEY']
AIRTABLE_BASE_ID = os.environ.get('AIRTABLE_BASE_ID', "appdIEjhUyzmHq8fY")
AIRTABLE_TABLE_ID = os.environ.get('AIRTABLE_TABLE_ID', "tblY0psVwc9jQNJJd")
BREEZY_ROCKETDEVS_EMAIL = os.environ['BREEZY_ROCKETDEVS_USERNAME']
BREEZY_ROCKETDEVS_PASSWORD = os.environ['BREEZY_ROCKETDEVS_PASSWORD']
BREEZY_HIVEMINDS_EMAIL = os.environ['BREEZY_HIVEMINDS_USERNAME']
BREEZY_HIVEMINDS_PASSWORD = os.environ['BREEZY_HIVEMINDS_PASSWORD']


def to_livekit():
    return livekit.api.S3Upload(
        # bucket=os.environ['S3_BUCKET'],
        access_key=os.environ['S3_ACCESS_KEY'],
        secret=os.environ['S3_SECRET_KEY'],
        region=os.environ['S3_REGION'],
        endpoint=os.environ['S3_ENDPOINT'],
        force_path_style=True,
    )
