# from config import *
# from Utils.utils import *
import json
import logging
from urllib.parse import urlparse
import datetime
import requests
from config import API_PATH  # اگر API_PATH در config.py هست، به '/api/v2/admin/user/' تغییر بدید
import Utils

# Document: Based on Hiddify Manager API v2 (compatible with version 11)
# Changes: Updated endpoint to /api/v2/admin/user/, fixed date format validation, added handling for new fields like 'enable'

# Assume API_PATH is now '/api/v2/admin/user/' in config.py
# If not, update config.py: API_PATH = '/api/v2/admin/user/'

def select(url, endpoint=""):
    try:
        full_endpoint = endpoint or API_PATH
        response = requests.get(url + full_endpoint)
        res = Utils.utils.dict_process(url, Utils.utils.users_to_dict(response.json()))
        return res
    except Exception as e:
        logging.error("API error: %s" % e)
        return None

def find(url, uuid, endpoint=""):
    try:
        full_endpoint = endpoint or API_PATH
        response = requests.get(url + full_endpoint, params={"uuid": uuid})  # Changed to params for query string
        jr = response.json()
        if len(jr) != 1:
            # Search for uuid
            for user in jr:
                if user['uuid'] == uuid:
                    return user
            return None
        return jr[0]
    except Exception as e:
        logging.error("API error: %s" % e)
        return None

def insert(url, name, usage_limit_GB, package_days, last_reset_time=None, added_by_uuid=None, mode="no_reset",
            last_online="0001-01-01T00:00:00Z", telegram_id=None,  # Updated to ISO format for v2
            comment=None, current_usage_GB=0, start_date=None, enable=True, endpoint=""):  # Added 'enable' field for v2 compatibility
    import uuid
    uuid_str = str(uuid.uuid4())
    added_by_uuid = urlparse(url).path.split('/')[2] if not added_by_uuid else added_by_uuid
    last_reset_time = datetime.datetime.now().isoformat()[:10] if not last_reset_time else last_reset_time  # ISO YYYY-MM-DD

    data = {
        "uuid": uuid_str,
        "name": name,
        "usage_limit_GB": usage_limit_GB,
        "package_days": package_days,
        "added_by_uuid": added_by_uuid,
        "last_reset_time": last_reset_time,
        "mode": mode,
        "last_online": last_online,
        "telegram_id": telegram_id,
        "comment": comment,
        "current_usage_GB": current_usage_GB,
        "start_date": start_date,
        "enable": enable  # New field in v2 for user status
    }
    jdata = json.dumps(data)
    try:
        full_endpoint = endpoint or API_PATH
        response = requests.post(url + full_endpoint, data=jdata, headers={'Content-Type': 'application/json'})
        if response.status_code in (200, 201):
            return uuid_str
        else:
            logging.error(f"API insert error: {response.text}")
            return None
    except Exception as e:
        logging.error("API error: %s" % e)
        return None

def update(url, uuid, endpoint="", **kwargs):
    try:
        full_endpoint = endpoint or API_PATH
        user = find(url, uuid, full_endpoint)
        if not user:
            return None
        for key in kwargs:
            user[key] = kwargs[key]
        # Ensure date formats are ISO
        if 'last_reset_time' in user:
            user['last_reset_time'] = datetime.datetime.strptime(user['last_reset_time'], "%Y-%m-%d").isoformat()[:10]
        response = requests.post(url + full_endpoint, data=json.dumps(user),
                                 headers={'Content-Type': 'application/json'})  # POST for upsert in v2
        if response.status_code in (200, 201):
            return uuid
        else:
            logging.error(f"API update error: {response.text}")
            return None
    except Exception as e:
        logging.error("API error: %s" % e)
        return None
