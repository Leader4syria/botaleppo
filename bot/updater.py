import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import time
from panel.utils import db
from panel.config import ORANOS_API_URL, API_TOKEN

def sync_api_services():
    """
    Fetches all API-linked services from the local DB,
    gets the latest data from the Oranos API, and syncs prices and availability.
    """
    print("Starting API services sync...")
    if not ORANOS_API_URL or not API_TOKEN:
        print("Updater: ORANOS_API_URL and API_TOKEN must be set in environment variables.")
        return

    try:
        # 1. Get all services from our DB that are linked to the API
        local_services = db.get_api_linked_services()
        if not local_services:
            print("Updater: No API-linked services to sync.")
            return

        # 2. Get fresh data from Oranos API
        headers = {"api-token": API_TOKEN}
        response = requests.get(ORANOS_API_URL, headers=headers, timeout=15)
        response.raise_for_status()
        remote_services_raw = response.json()

        if not isinstance(remote_services_raw, list):
            print("Updater: API response is not a list. Aborting sync.")
            return

        # Create a map for easy lookup
        remote_services_map = {str(s['id']): s for s in remote_services_raw if isinstance(s, dict) and 'id' in s}

        update_count = 0
        # 3. Compare and update
        for local_service in local_services:
            api_id = str(local_service.get('api_service_id'))
            remote_service = remote_services_map.get(api_id)

            if remote_service:
                # Service found in remote API, check for differences
                # Use .get with a default to avoid errors if keys are missing
                local_price = float(local_service.get('price', 0.0))
                remote_price = float(remote_service.get('price', local_price))
                local_available = local_service.get('available', False)
                remote_available = remote_service.get('available', local_available)

                # Check for changes
                if local_price != remote_price or local_available != remote_available:
                    print(f"Updater: Updating service ID {local_service['id']} (API ID: {api_id})...")
                    print(f"  - Price: {local_price} -> {remote_price}")
                    print(f"  - Available: {local_available} -> {remote_available}")
                    db.update_service_from_api(local_service['id'], remote_price, remote_available)
                    update_count += 1
            else:
                # Service not found in remote API, mark as unavailable if it's currently available
                if local_service.get('available', False):
                    print(f"Updater: Service ID {local_service['id']} (API ID: {api_id}) not found in API. Marking as unavailable.")
                    db.update_service_from_api(local_service['id'], local_service.get('price', 0.0), False)
                    update_count += 1

        if update_count > 0:
            print(f"Updater: Sync complete. Updated {update_count} services.")
        else:
            print("Updater: Sync complete. No changes detected.")

    except requests.RequestException as e:
        print(f"Updater: Error fetching from Oranos API: {e}")
    except Exception as e:
        print(f"Updater: An unexpected error occurred during service sync: {e}")


def run_periodic_sync():
    """
    A worker function that runs the sync process in a loop.
    """
    while True:
        sync_api_services()
        # Wait for 60 seconds before the next sync
        time.sleep(60)
