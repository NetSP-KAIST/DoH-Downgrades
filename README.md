# DoH Downgrades
This repository serves as a platform for sharing source code related to the investigation of current global practices of DNS-over-HTTPS (DoH) downgrades.

## Data Collection Code
The data collection scripts are primarily written in Python, requiring the user to install the appropriate version of Python (`3.10.6`). Additionally, the user must install all the required packages listed in the `requirements.txt` file.

### Code Structures
To facilitate understanding amidst the various scripts available, here is a brief explanation of their structures:

* **`browsers.py`**: This script contains essential methods used to conduct experiments, simulating the behavior of major browsers when sending DoH queries.
* **`domain_list.py`**: This file contains the list of domain names that will be queried during the experiments.
* **`chromium_baseline.py`**: This script measures the baseline downgrade behavior, mimicking Chromium-like browsers. The user must provide the username along with the API key for Proxyrack.
* **`chromium_bypass.py`**: This script attempts to bypass DoH downgrades and measures the results, mimicking Chromium-like browsers. The user must provide the username along with the API key for Proxyrack.
* **`firefox_baseline.py`**: This script measures the baseline downgrade behavior, mimicking Firefox browser. The user must provide the username along with the API key for Proxyrack.
* **`firefox_bypass.py`**: This script attempts to bypass DoH downgrades and measures the results, mimicking Firefox browser. The user must provide the username along with the API key for Proxyrack.

Please ensure that you follow the necessary instructions and provide the required API key before executing the respective scripts.

## Known Issues
The scripts may not function properly on operating systems besides Linux. For Windows users, it is recommnded to utilize the Windows Subsystem for Linux (WSL).

## Updates
As several crucial libraries have been updated by accommodating our suggestions, we have accordingly revised our script to align with these updates.

## Acknowledgement
This repository is part of the following work:  
Jinseo Lee, David Mohaisen, and Min Suk Kang. 2024. **Measuring DNS-over-HTTPS Downgrades: Prevalence, Techniques, and Bypass Strategies**. *Proc. ACM Netw.* 2, CoNEXT4, Article 28 (December 2024), 22 pages. https://doi.org/10.1145/3696385

Please cite this work if you use our scripts.