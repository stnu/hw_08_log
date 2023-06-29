import argparse
import json
import os.path
import re
from datetime import datetime

parser = argparse.ArgumentParser(description='Process access.log')

parser.add_argument('-f', dest='target', action='store', help='Path to log')
args = parser.parse_args()

target_files = []

if os.path.isfile(args.target):
    target_files.append(args.target)
else:
    files = os.listdir(args.target)
    for item in files:
        if item.endswith(".log"):
            target_files.append(os.path.join(args.target, item))

for target_file in target_files:
    result = {
        "file": target_file,
        "top_3_ip": {},
        "top_3_longest": [],
        "all_requests": {
            "GET": 0,
            "HEAD": 0,
            "POST": 0,
            "PUT": 0,
            "DELETE": 0,
            "OPTIONS": 0
        }
    }
    all_requests_by_all_ips = {}

    with open(target_file) as file:
        idx = 0

        for line in file:
            idx += 1

            ip_match = re.search("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", line)
            date_match = re.search(
                "\d\d/(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/\d\d\d\d:\d\d:\d\d:\d\d \+\d\d\d\d",
                line)
            method_match = re.search('] \"(GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH)', line)
            url_match = re.search('"(GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH) (\S+) +HTTP', line)
            timing_str = line.split(" ")[-1]

            if ip_match and date_match and method_match and url_match:
                ip = ip_match.group()
                date = date_match.group()
                method = method_match.group(1)
                url = url_match.group(2)
            else:
                continue

            try:
                timing = int(timing_str)
            except ValueError:
                continue

            result["all_requests"][method.upper()] += 1

            if len(result["top_3_longest"]) < 3:
                result["top_3_longest"].append([ip, date, method, url, timing])
            else:
                minimal = min(result["top_3_longest"][0][-1], result["top_3_longest"][1][-1],
                              result["top_3_longest"][2][-1])

                if timing > minimal:
                    if result["top_3_longest"][0][-1] == minimal:
                        result["top_3_longest"].remove(result["top_3_longest"][0])
                    elif result["top_3_longest"][1][-1] == minimal:
                        result["top_3_longest"].remove(result["top_3_longest"][1])
                    elif result["top_3_longest"][2][-1] == minimal:
                        result["top_3_longest"].remove(result["top_3_longest"][2])

                    result["top_3_longest"].append([ip, date, method, url, timing])

            if ip in all_requests_by_all_ips:
                all_requests_by_all_ips[ip] += 1
            else:
                all_requests_by_all_ips[ip] = 1

        sorted_keys = sorted(all_requests_by_all_ips, key=all_requests_by_all_ips.get, reverse=True)
        for i in range(3):
            result["top_3_ip"][sorted_keys[i]] = all_requests_by_all_ips[sorted_keys[i]]

        result["total_requests"] = idx

    print(json.dumps(result, indent=4))

    with open(
            f"result_{os.path.basename(target_file).replace('.', '_')}_{datetime.now().strftime('%d-%m-%Y_%H.%M.%S')}.json",
            "w") as f:
        f.write(json.dumps(result, indent=4))
