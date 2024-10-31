"""firefox_bypass.py

This script attempts to bypass DoH downgrades and measures the results, mimicking Firefox browser.
"""


import sys, os, shutil
import httpx
import logging, time
import domain_list, browsers
import random
from multiprocessing import Pool, TimeoutError


# User information
USERNAME = "YOUR_NAME_HERE"
API_KEY = "YOUR_KEY_HERE"
assert(USERNAME != "YOUR_NAME_HERE" and API_KEY != "YOUR_KEY_HERE")


Y = "YOUR_Y_HERE" # The probability of random connectivity checks between queries
assert(Y != "YOUR_Y_HERE")


# Country list
COUNTRY_LIST = ["YOUR", "COUNTRY CODE", "LIST"] # List of countries to test bypass strategies, in ISO 3166-1 alpha-2 format.
assert(COUNTRY_LIST != ["YOUR", "COUNTRY CODE", "LIST"])

# Constants
MAX_NUM_IP = 5000
EXP_NAME = "TFC_TEST"
TIMEOUT = 50.0
INTERVAL = 14400
REP_COUNT = 3


def firefox_tot_exp(num, country, API_KEY, TIMEOUT, main_logger, resolver, resolver_ip, resilient_resolver, resilient_resolver_ip, nysni, domains, method):
    """For concurrent execution, define a method for experimentation.

    Args:
        num: The integer for generating a port number.
        country: Country code (ISO 3166-1 alpha-2).
        API_KEY: API key for Proxyrack.
        TIMEOUT: Time to wait before the timeout exception, in seconds.
        main_logger: Python logger object.
        resolver: The domain name of a DoH resolver.
        resolver_ip: The IP address of a DoH resolver.
        resilient_resolver: The domain name of a resilient resolver.
        resilient_resolver_ip: The IP address of a resilient resolver.
        nysni: The resilient hostname to use.
        domains: The list of domain names to query.
        method: The HTTP method to use.
    
    Returns:
        The IP address of the connected host.
        "Not valid" | "IP not found" | "Duplicated IP, {ip}" | "{ip}"
    """
    port = num + 10000

    with httpx.Client(http1=False, http2=True, proxies=f"socks5://{USERNAME}-country-{country}:{API_KEY}@premium.residential.proxyrack.net:{port}", timeout=TIMEOUT, verify=False) as client:
        # Connectivity check - before queries
        validity = browsers.val_check(client, main_logger)

        if validity == "Not valid":
            return "Not valid"
        
        # Find IP and ISP using the session information
        ip, isp = browsers.get_IP_ISP(httpx.Client(http1=True, http2=False, proxies=f"socks5://{USERNAME}-country-{country}:{API_KEY}@premium.residential.proxyrack.net:{port}", timeout=TIMEOUT), port, main_logger)

        if ip == None or isp == None:
            return "IP not found"

        # Check duplicated IPs
        if os.path.exists(f"./{EXP_NAME}/{country}/{ip}"):
            return f"Duplicated IP, {ip}"
        
        # For recording, make directories
        try: 
            os.mkdir(f"{EXP_NAME}/{country}/{ip}")
            os.mkdir(f"{EXP_NAME}/{country}/{ip}/bl")
            os.mkdir(f"{EXP_NAME}/{country}/{ip}/rr")
            if resilient_resolver != None:
                os.mkdir(f"{EXP_NAME}/{country}/{ip}/sr")
            os.mkdir(f"{EXP_NAME}/{country}/{ip}/sni")
            if resilient_resolver != None:
                os.mkdir(f"{EXP_NAME}/{country}/{ip}/rrsr")
            os.mkdir(f"{EXP_NAME}/{country}/{ip}/rrsni")

        except:
            # Due to the concurrency, it might raise exceptions
            return f"Duplicated IP, {ip}"
        
        # BASELINE
        trial = 0
        for domain in domains:
            if random.randint(1, 100) <= Y:
                validity = browsers.val_check(client, main_logger)

                if validity == "Not valid":
                    shutil.rmtree(f"./{EXP_NAME}/{country}/{ip}")
                    return "Not valid"

            response = browsers.firefox_query(client, resolver, domain, main_logger, method)

            with open(f"./{EXP_NAME}/{country}/{ip}/bl/{trial}", 'wb') as output_file:
                output_file.write(response)
            
            trial += 1
        
        # Direct IP
        trial = 0
        for domain in domains:
            if random.randint(1, 100) <= Y:
                validity = browsers.val_check(client, main_logger)

                if validity == "Not valid":
                    shutil.rmtree(f"./{EXP_NAME}/{country}/{ip}")
                    return "Not valid"

            response = browsers.firefox_query(client, resolver, domain, main_logger, method, resolver_ip, None, None, None)

            with open(f"./{EXP_NAME}/{country}/{ip}/rr/{trial}", 'wb') as output_file:
                output_file.write(response)
            
            trial += 1
        
        # resilient IP resolution
        trial = 0
        for domain in domains:
            if resilient_resolver == None:
                break
            
            if random.randint(1, 100) <= Y:
                validity = browsers.val_check(client, main_logger)

                if validity == "Not valid":
                    shutil.rmtree(f"./{EXP_NAME}/{country}/{ip}")
                    return "Not valid"

            response = browsers.firefox_query(client, resolver, domain, main_logger, method, None, resilient_resolver, None, None)

            with open(f"./{EXP_NAME}/{country}/{ip}/sr/{trial}", 'wb') as output_file:
                output_file.write(response)
            
            trial += 1

        # resilient hostname resolution
        trial = 0
        for domain in domains:
            if random.randint(1, 100) <= Y:
                validity = browsers.val_check(client, main_logger)

                if validity == "Not valid":
                    shutil.rmtree(f"./{EXP_NAME}/{country}/{ip}")
                    return "Not valid"

            response = browsers.firefox_query(client, resolver, domain, main_logger, method, None, None, None, nysni)
            
            with open(f"./{EXP_NAME}/{country}/{ip}/sni/{trial}", 'wb') as output_file:
                output_file.write(response)
            
            trial += 1

        # Direct IP + resilient IP resolution
        trial = 0
        for domain in domains:
            if resilient_resolver == None:
                break

            if random.randint(1, 100) <= Y:
                validity = browsers.val_check(client, main_logger)

                if validity == "Not valid":
                    shutil.rmtree(f"./{EXP_NAME}/{country}/{ip}")
                    return "Not valid"

            response = browsers.firefox_query(client, resolver, domain, main_logger, method, None, resilient_resolver, resilient_resolver_ip, None)

            with open(f"./{EXP_NAME}/{country}/{ip}/rrsr/{trial}", 'wb') as output_file:
                output_file.write(response)
            
            trial += 1
        
        # Direct IP + resilient hostname resolution
        trial = 0
        for domain in domains:
            if random.randint(1, 100) <= Y:
                validity = browsers.val_check(client, main_logger)

                if validity == "Not valid":
                    shutil.rmtree(f"./{EXP_NAME}/{country}/{ip}")
                    return "Not valid"

            response = browsers.firefox_query(client, resolver, domain, main_logger, method, resolver_ip, None, None, nysni)

            with open(f"./{EXP_NAME}/{country}/{ip}/rrsni/{trial}", 'wb') as output_file:
                output_file.write(response)
            
            trial += 1

        # ISP recording
        with open(f"./{EXP_NAME}/{country}/{ip}/isp_{isp}", 'w') as output_file:
            output_file.write("")

        # Connectivity check - after queries
        validity = browsers.val_check(client, main_logger)

        if validity == "Not valid":
            shutil.rmtree(f"./{EXP_NAME}/{country}/{ip}")
            return "Not valid"

        return ip


if __name__ == '__main__':
    random.seed()

    if len(sys.argv) == 2: # python3 $name $EXP_NAME (depreciated)
        EXP_NAME = sys.argv[1]

    if len(sys.argv) == 7: # python3 $name $EXP_NAME $resolver $resolver_ip $nysni $domains $method
        EXP_NAME = sys.argv[1]
        resolver = sys.argv[2]
        resolver_ip = sys.argv[3]
        nysni = sys.argv[4]

        if sys.argv[5] == "example":
            domains = domain_list.example
        else:
            print("Wrong argument(s) found")
            exit()

        if sys.argv[6] == "POST":
            method = browsers.Methods.POST

        elif sys.argv[6] == "GET":
            method = browsers.Methods.GET

        else:
            print("Wrong argument(s) found")
            exit()

    if len(sys.argv) == 9: # python3 $name $EXP_NAME $resolver $resolver_ip $resilient_resolver $resilient_resolver_ip $nysni $domains $method
        EXP_NAME = sys.argv[1]
        resolver = sys.argv[2]
        resolver_ip = sys.argv[3]
        resilient_resolver = sys.argv[4]
        resilient_resolver_ip = sys.argv[5]
        nysni = sys.argv[6]

        if sys.argv[7] == "example":
            domains = domain_list.example
        else:
            print("Wrong argument(s) found")
            exit()

        if sys.argv[8] == "POST":
            method = browsers.Methods.POST

        elif sys.argv[8] == "GET":
            method = browsers.Methods.GET
        
        else:
            print("Wrong argument(s) found")
            exit()

    # Check duplicated experiments
    if os.path.exists(f"./{EXP_NAME}"):
        print(f"{EXP_NAME} already exists")
        exit()

    # Make an experiment directory
    os.mkdir(EXP_NAME)

    # For logging exceptions
    main_logger = logging.getLogger("main")
    main_logger.setLevel(logging.ERROR)

    main_logger.addHandler(logging.FileHandler(filename=f"./{EXP_NAME}/exceptions.log", encoding="utf-8", mode="w"))

    # For logging progresses
    prog_logger = logging.getLogger("main.progress")
    prog_logger.propagate=True
    prog_logger.setLevel(logging.INFO)

    prog_logger.addHandler(logging.FileHandler(filename=f"./{EXP_NAME}/progress.log", encoding="utf-8", mode="w"))

    # For logging failures
    fail_logger = logging.getLogger("main.failure")
    fail_logger.propagate=False
    fail_logger.setLevel(logging.INFO)

    fail_logger.addHandler(logging.FileHandler(filename=f"./{EXP_NAME}/fail.log", encoding="utf-8", mode="w"))

    # To restrict the number of IPs in each country, make sat_list which contains the names of countries have MAX_NUM_IP IPs
    sat_list = []

    exp_count = 1
    # Experiment loop
    while exp_count != REP_COUNT + 1:
        prog_logger.info(f"Experiemnt {exp_count} / {REP_COUNT} now begins")
        print(f"Experiemnt {exp_count} / {REP_COUNT} now begins")

        countries = COUNTRY_LIST
        
        # Exclude countries which already have more than MAX_NUM_IP IPs
        countries = sorted(list(set(countries) - set(sat_list)))

        if len(countries) == 0:
            print("No available countries left")
            exit()

        # Country loop 
        for country in countries:
            # Sanity check for country names
            if len(country) != 2: #type:ignore
                continue

            if country == "CN" and resolver == "dns.google": #type:ignore
                continue

            entering_time = time.time()

            # Get the number of available IPs with the country code
            try:
                num_ip = httpx.get(f"http://api.proxyrack.net/countries/{country}/count", proxies=f"socks5://{USERNAME}:{API_KEY}@premium.residential.proxyrack.net:9000", timeout=TIMEOUT).json()

            except:
                continue

            # If there is no avaiable IPs, skip
            if num_ip == 0:
                print(f"No avaiable IP: {country}")
                continue

            # Check whether this country hits the limit
            if os.path.exists(f"./{EXP_NAME}/{country}"):
                collected_num_ip = len(os.listdir(f"./{EXP_NAME}/{country}"))
                if collected_num_ip >= MAX_NUM_IP:
                    print(f"{country} hits the limit")
                    prog_logger.info(f"{country} hits the limit")
                    sat_list.append(country)
                    continue
                # Set num_ip correctly
                num_ip = min(num_ip, MAX_NUM_IP - collected_num_ip)
            else:
                num_ip = min(num_ip, MAX_NUM_IP)

                # Make a country directory
                os.mkdir(f"{EXP_NAME}/{country}")

            prog_logger.info(f"{country} will try to get {num_ip} IPs")
            print(f"Entering country: {country} with {num_ip} IPs")

            # For concurrent execution
            with Pool(processes=100) as pool:
                # Distributing works
                procs = []
                for num in range(1, num_ip + 1):
                    if len(sys.argv) == 7:
                        procs.append(pool.apply_async(firefox_tot_exp, (num, country, API_KEY, TIMEOUT, main_logger, resolver, resolver_ip, None, None, nysni, domains, method))) #type:ignore
                    elif len(sys.argv) == 9:
                        procs.append(pool.apply_async(firefox_tot_exp, (num, country, API_KEY, TIMEOUT, main_logger, resolver, resolver_ip, resilient_resolver, resilient_resolver_ip, nysni, domains, method))) #type:ignore
                    else:
                        raise Exception("WRONG EXPERIMENT INPUT")

                # Gathering results
                for proc in procs:
                    try:
                        if proc.ready():
                            print(f"Finished case: {proc.get(0)}")
                        else:
                            print(f"Finished case: {proc.get(TIMEOUT*3)}")
                    
                    except TimeoutError:
                        prog_logger.info("TimeoutError: Deadlock, or uncleared child process, whatever.")
                        print("TimeoutError")
                        continue
                    
                    except Exception as e:
                        prog_logger.exception('Hmmmm....')
                        print("Unknown error")
                        continue

            ending_time = time.time()
            prog_logger.info(f"{country} with {num_ip} IPs took {ending_time - entering_time} seconds.")
            
            actual_num = len(os.listdir(f"./{EXP_NAME}/{country}"))
            fail_logger.info(f"{country}-{num_ip - actual_num}")
            
            print(f"End of country: {country}")
        
        prog_logger.info(f"Experiemnt {exp_count} / {REP_COUNT} has ended")
        print(f"Experiemnt {exp_count} / {REP_COUNT} has ended")

        exp_count += 1

        if exp_count != REP_COUNT + 1:
            print(f"Sleep for {INTERVAL / 60} minutes before the next experiment")
            time.sleep(INTERVAL)