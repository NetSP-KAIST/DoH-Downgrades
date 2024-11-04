# DoH Downgrades
This repository serves as a platform for sharing source code related to the investigation of current global practices of DNS-over-HTTPS (DoH) downgrades.

## Data Collection
The data collection scripts are measuring DoH downgrades from globally distributed vantage points in Proxyrack. It requires a Linux-based operating systems, an API key for Proxyrack, and a stable Internet connection. Users can obtain raw measurement data (i.e., DoH query results) by running the provided scripts.

## Installation
Install `Python 3.10.6` and the required Python packages listed in `requirements.txt`. Replace `YOUR_X_HERE` in `browsers.py` and `YOUR_Y_HERE` in the measurement scripts with appropriate values. Update `YOUR_NAME_HERE` and `YOUR_KEY_HERE` in the measurement scripts with your Proxyrack username and API key (for "Premium Residential Proxies"). Update `COUNTRY_LIST` in the bypass scripts with the list of countries where bypass measurements should be performed. Define the domain lists for your measurements in `domain_list.py`. 

## Evaluation and Expected Results
To perform baseline measurements (i.e., without bypassing downgrades) mimicking Chromium-like browsers, the user should run `chromium_baseline.py` with four additional arguments: a measurement index (an arbitrary string), DoH resolver domain name, domain list ID (as defined in `domain_list.py`), and the HTTP method (`POST` or `GET`). The results will be saved in a directory named after the provided measurement index, with country codes and IP addresses as subdirectory names.

For bypass measurements mimicking Chromium-like browsers, the user should run `chromium_bypass.py` with eight additional arguments: a measurement index, DoH resolver domain name, DoH resolver IP address, domain name of the fuzzy IP address, fuzzy IP address, fuzzy hostname, domain list ID, and the HTTP method. The results will be saved in a directory named after the provided measurement index, with country codes, IP addresses, and bypass methodologies as subdirectory names.

To conduct similar measurements mimicking Firefox browsers, the user should run `firefox_baseline.py` and `firefox_bypass.py`.

For baseline measurements, each IP address directory will contain six items: `0`, `1`, `2`, `3`, `4`, and `Isp_{nameofISP}`. For bypass measurements, each IP address directory will contain one item and four or six subdirectories: `baseline`, `directIP`, `directIPfuzzyHost`, `fuzzyHost`, [`fuzzyIP`, `fuzzyIPfuzzyHost`,] and `Isp_{nameofISP}`. Each subdirectory will include five items: `0`, `1`, `2`, `3`, and `4`. Since all results (i.e., `0` to `4`) are raw DoH responses, users can easily validate each query result. For example, in Python, a user can extract a return code of a response as follows:
```
with open("0", "rb") as response:
    resp = response.read()
    rcode = dns.message.from_wire(resp).rcode()
```

### Code Structures
To facilitate understanding amidst the various scripts available, here is a brief explanation of their structures:

* **`browsers.py`**: This script contains essential methods used to conduct experiments, simulating the behavior of major browsers when sending DoH queries.
* **`domain_list.py`**: This file contains the list of domain names that will be queried during the experiments.
* **`chromium_baseline.py`**: This script measures the baseline downgrade behavior, mimicking Chromium-like browsers. The user must provide the username along with the API key for Proxyrack.
* **`chromium_bypass.py`**: This script attempts to bypass DoH downgrades and measures the results, mimicking Chromium-like browsers. The user must provide the username along with the API key for Proxyrack.
* **`firefox_baseline.py`**: This script measures the baseline downgrade behavior, mimicking Firefox browser. The user must provide the username along with the API key for Proxyrack.
* **`firefox_bypass.py`**: This script attempts to bypass DoH downgrades and measures the results, mimicking Firefox browser. The user must provide the username along with the API key for Proxyrack.

Please ensure that you follow the necessary instructions and provide the required API key before executing the respective scripts.

### Customization
* `MAX_NUM_IP`: The maximum number of vantage points per country.
* `TIMEOUT`: The duration to wait before a timeout, in seconds.
* `INTERVAL`: The duration to wait before starting the next consecutive measurement, in seconds.
* `REP_COUNT`: The number of times to repeat the measurement (e.g., 3 means performing the measurement 3 times consecutively).

## Known Issues
The scripts may not function properly on operating systems besides Linux. For Windows users, it is recommnded to utilize the Windows Subsystem for Linux (WSL).

## Updates
As several crucial libraries have been updated by accommodating our suggestions, we have accordingly revised our script to align with these updates.

## Acknowledgement
This repository is part of the following work:  
Jinseo Lee, David Mohaisen, and Min Suk Kang. 2024. **Measuring DNS-over-HTTPS Downgrades: Prevalence, Techniques, and Bypass Strategies**. *Proc. ACM Netw.* 2, CoNEXT4, Article 28 (December 2024), 22 pages. https://doi.org/10.1145/3696385

Please cite this work if you use our scripts.