import requests
from openpyxl import Workbook
from datetime import datetime, timedelta, timezone

# -------------------- timezone --------------------
IST = timezone(timedelta(hours=5, minutes=30))  # India Standard Time

# -------------------- helpers --------------------

def login(base_url, username, password):
    r = requests.post(f"{base_url}/api/auth/login",
                      json={"username": username, "password": password})
    if r.status_code == 401:
        raise ValueError("Invalid credentials")
    r.raise_for_status()
    return r.json()['token']


def get_devices(base_url, jwt):
    headers = {"X-Authorization": f"Bearer {jwt}"}
    r = requests.get(f"{base_url}/api/tenant/deviceInfos?pageSize=500&page=0",
                     headers=headers)
    r.raise_for_status()
    return r.json()['data']


def get_device_keys(base_url, jwt, device_id):
    headers = {"X-Authorization": f"Bearer {jwt}"}
    r = requests.get(f"{base_url}/api/plugins/telemetry/DEVICE/{device_id}/keys/timeseries",
                     headers=headers)
    r.raise_for_status()
    return r.json()  # list of keys


def get_timeseries(base_url, jwt, device_id, keys, start_ts, end_ts, interval_min=3):
    """
    Fetch telemetry data dynamically adjusting the 'limit' based on duration and interval.
    No limit cap applied.
    """
    headers = {"X-Authorization": f"Bearer {jwt}"}

    # Calculate total days between timestamps
    total_days = (end_ts - start_ts) / (1000 * 60 * 60 * 24)

    # Each day = (24 * 60 / interval_min) data points
    points_per_day = (24 * 60) / interval_min
    dynamic_limit = int(points_per_day * total_days)

    params = {
        "keys": ",".join(keys),
        "startTs": start_ts,
        "endTs": end_ts,
        "interval": 0,
        "limit": dynamic_limit,
        "useStrictDataTypes": "false"
    }

    print(f"📊 Fetching telemetry for {device_id} | Days: {total_days:.2f} | Interval: {interval_min} min | Limit={dynamic_limit}")
    r = requests.get(
        f"{base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
        headers=headers, params=params)
    r.raise_for_status()
    return r.json()


def parse_dt(dt_str):
    """
    Parse a DDMMYYYY HH:MM AM/PM string as IST and return UTC milliseconds.
    """
    dt_str = dt_str.strip()
    dt_local = datetime.strptime(dt_str, "%d%m%Y %I:%M %p").replace(tzinfo=IST)
    return int(dt_local.astimezone(timezone.utc).timestamp() * 1000)


def prompt_with_retry(prompt_text, parser=lambda x: x, err_msg="Invalid input", max_tries=3, default=None):
    for i in range(max_tries):
        val = input(prompt_text)
        if not val and default is not None:
            return default
        try:
            return parser(val)
        except Exception:
            print(f"❌ {err_msg}. Attempt {i+1}/{max_tries}")
    print("Exceeded maximum attempts. Exiting.")
    exit(1)

# -------------------- main --------------------

def main():
    print("===== ThingsBoard Telemetry Exporter =====\n")

    base_url = prompt_with_retry(
        "Enter Base URL [Default: http://localhost:8080]: ",
        str, "Base URL required", default="http://localhost:8080"
    )
    username = prompt_with_retry("Enter Username [Default: tenant@thingsboard.org]: ",
                                 str, "Username required", default="tenant@thingsboard.org")
    password = prompt_with_retry("Enter Password [Default: tenant]: ",
                                 str, "Password required", default="tenant")

    try:
        jwt = login(base_url, username, password)
    except ValueError as e:
        print(f"❌ {e}")
        return

    devices = get_devices(base_url, jwt)
    print("\nAvailable Devices:")
    for d in devices:
        print(f"{d['name']} (ID: {d['id']['id']})")

    all_device_names = [d['name'] for d in devices]
    device_names = prompt_with_retry(
        "\nEnter device names separated by comma or 'all' [Default: all]: ",
        lambda s: all_device_names if s.strip().lower() == "all" or not s.strip()
                  else [x.strip() for x in s.split(',') if x.strip()],
        "Provide at least one device name"
    )

    keys_input = prompt_with_retry(
        "\nEnter telemetry keys separated by comma or 'all' [Default: all]: ",
        lambda s: None if not s.strip() or s.strip().lower() == "all"
                  else [x.strip() for x in s.split(',') if x.strip()],
        "Provide at least one key"
    )

    default_end = datetime.now(IST)
    default_start = default_end - timedelta(days=7)

    start_ts = prompt_with_retry(
        "Enter start date/time (DDMMYYYY HH:MM AM/PM) [Default: 7 days back]: ",
        parse_dt,
        "Invalid date/time format",
        default=int(default_start.astimezone(timezone.utc).timestamp() * 1000)
    )
    end_ts = prompt_with_retry(
        "Enter end date/time (DDMMYYYY HH:MM AM/PM) [Default: now]: ",
        parse_dt,
        "Invalid date/time format",
        default=int(default_end.astimezone(timezone.utc).timestamp() * 1000)
    )

    interval_min = prompt_with_retry(
        "\nEnter data interval in minutes [Default: 3]: ",
        lambda s: int(s) if s.strip() else 3,
        "Interval must be an integer"
    )

    wb = Workbook()
    wb.remove(wb.active)

    for dev_name in device_names:
        dev_info = next((d for d in devices if d['name'] == dev_name), None)
        ws = wb.create_sheet(dev_name[:31])
        if not dev_info:
            ws.append(["No such device"])
            continue

        dev_id = dev_info['id']['id']
        try:
            data = get_timeseries(base_url, jwt, dev_id,
                                  keys_input if keys_input else get_device_keys(base_url, jwt, dev_id),
                                  start_ts, end_ts, interval_min)
        except Exception as e:
            print(f"❌ Failed to fetch data for {dev_name}: {e}")
            ws.append(["Failed to fetch data"])
            continue

        if not any(data.values()):
            ws.append(["No data available for given time range"])
            print(f"ℹ️ No data for {dev_name}")
            continue

        keys_to_use = keys_input if keys_input else list(data.keys())
        ws.append(["Timestamp (IST)"] + keys_to_use)
        timestamps = sorted({item['ts'] for k in data for item in data[k]})
        for ts in timestamps:
            # Convert UTC timestamp back to IST for Excel
            row = [datetime.fromtimestamp(ts / 1000, IST).strftime('%Y-%m-%d %H:%M:%S')]
            for k in keys_to_use:
                val = next((i['value'] for i in data.get(k, []) if i['ts'] == ts), "")
                row.append(val)
            ws.append(row)

    now_str = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
    filename = f"telemetry_export_{now_str}.xlsx"
    wb.save(filename)
    print(f"\n✅ Export completed. File saved as {filename}")


if __name__ == "__main__":
    main()

