"""browsers.py

This script contains essential methods used to conduct experiments, simulating the behavior of major browsers when sending DoH queries.
"""


import string
import dns.message, dns.edns, base64
import random
from enum import Enum


class Methods(Enum):
    POST = 0
    GET = 1


X = "YOUR_X_HERE" # The probability of using GET method for connectivity checks (0-100)
assert(X != "YOUR_X_HERE")


def val_check(client, main_logger):
    """Check the validity of given host by accessing www.yahoo.com and www.bing.com.
    It will send an HTTP "HEAD" request with a (100 - X)% probability.
    Otherwise, it will send a "GET" HTTP request.

    Args:
        client: HTTPX client.
        main_logger: Python logger object.
    
    Returns:
        The validity of the host.
        "Valid" | "Not valid"
    """
    random.seed()

    try:
        if random.randint(1, 100) > X:
            validity = client.head("https://www.yahoo.com/").status_code
        else:
            validity = client.get("https://www.yahoo.com/").status_code

        if validity >= 400:
            validity = "TRY_AGAIN"

    except TimeoutError:
        main_logger.error("Request timeout in validity check")
        validity = "TRY_AGAIN"

    except Exception:
        main_logger.exception("During the validity check")
        validity = "TRY_AGAIN"

    if validity == "TRY_AGAIN":
        try:
            if random.randint(1, 100) > X:
                validity = client.head("https://www.bing.com/").status_code
            else:
                validity = client.get("https://www.bing.com/").status_code

            if validity >= 400:
                return "Not valid"
            
        except TimeoutError:
            main_logger.error("Request timeout in validity check")
            return "Not valid"

        except Exception:
            main_logger.exception("During the validity check")
            return "Not valid"
    
    return "Valid"


def get_IP_ISP(client, port, main_logger):
    """Get sessions then return IP and ISP.

    Args:
        client: HTTPX client.
        port: The port number to use.
        main_logger: Python logger object.
    
    Returns:
        (ip, isp), both are string or None.
    """

    ip = "init"
    isp = "init"

    ### For storing ISP names, make their names valid as the filename.
    def _into_filename(isp):
        valid_chars = f"_() {string.ascii_letters}{string.digits}"
        filename = ''.join(c for c in isp if c in valid_chars)
        filename = filename.replace(' ', '_')
        return filename
    
    try:
        sessions = client.get("http://api.proxyrack.net/sessions", headers={'accept': 'application/json'}).json()
        for session in sessions:
            if session['port'] == port:
                ip = session['proxy']['ip']
                isp = session['proxy']['isp']
                isp = _into_filename(isp)

                break
            
        # There was no given port in session list
        if ip == "init":
            return None, None
    
    except Exception:
        main_logger.exception("During getting sessions")
        return None, None

    return ip, isp


def firefox_query(
        client, 
        resolver, 
        domain, 
        main_logger, 
        method,
        resolver_ip= None,
        resilient_resolver= None,
        resilient_resolver_ip = None,
        nysni= None,
):
    """Send Firefox-like DoH query.

    Args:
        client: HTTPX client.
        resolver: The domain name of a DoH resolver.
        domain: The domain name to query.
        main_logger: Python logger object.
        method: The HTTP method to use.
        (optional) resolver_ip: The IP address of a DoH resolver.
        (optional) resilient_resolver: The domain name of a resilient resolver.
        (optional) resilient_resolver_ip: The IP address of a resilient resolver (i.e., fuzzy IP address).
        (optional) nysni: The fuzzy hostname to use.
    
    Returns:
        The response from the DoH resolver.
    """

    ### modes:
    ### 0 - Baseline, 1 - Direct IP, 2 - Fuzzy IP, 3 - Fuzzy hostname, 
    ### 4 - Fuzzy IP + fuzzy hostname, 5 - Direct IP + fuzzy hostname

    if resolver_ip == None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni == None:
        mode = 0
    elif resolver_ip != None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni == None:
        mode = 1
    elif resolver_ip == None and (resilient_resolver != None and resilient_resolver_ip == None) and nysni == None:
        mode = 2
    elif resolver_ip == None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni != None:
        mode = 3
    elif resolver_ip == None and (resilient_resolver != None and resilient_resolver_ip != None) and nysni != None:
        mode = 4
    elif resolver_ip != None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni != None:
        mode = 5
    else:
        print("Wrong configurations in firefox_query")
        exit()

    try:
        if method == Methods.POST:
            dns_query = dns.message.make_query(qname=domain, rdtype="A", rdclass="IN", id=0)
            csubnet = dns.edns.ECSOption("0.0.0.0", 0, 0)
            dns_query.use_edns(0, payload=4096, pad=128, options=[csubnet])

            if "User-Agent" in client.headers:
                del client.headers["User-Agent"]

            if mode == 0:
                response = client.post(
                    url=f"https://{resolver}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'accept-encoding': '',
                        'content-type': 'application/dns-message',
                        'cache-control': 'no-store, no-cache',
                        'pragma': 'no-cache',
                        'te': 'trailers'
                    }
                ).read()
            
            elif mode == 1:
                response = client.post(
                    url=f"https://{resolver_ip}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'accept-encoding': '',
                        'content-type': 'application/dns-message',
                        'cache-control': 'no-store, no-cache',
                        'pragma': 'no-cache',
                        'te': 'trailers'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()
            
            elif mode == 2:
                response = client.post(
                    url=f"https://{resilient_resolver}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()
            
            elif mode == 3:
                if 'cloudflare' in resolver:
                    response = client.post(
                        url=f"https://cloudflare-dns.com/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
                
                else:
                    response = client.post(
                        url=f"https://{resolver}/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                ).read()

            elif mode == 4:
                response = client.post(
                    url=f"https://{resilient_resolver_ip}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": nysni}
                ).read()
            
            else: # elif mode == 5:
                if 'cloudflare' in resolver:
                    response = client.post(
                        url=f"https://1.1.1.1/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
                else:
                    response = client.post(
                        url=f"https://{resolver_ip}/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
        
        else: # elif method == Methods.GET:
            dns_query = dns.message.make_query(qname=domain, rdtype="A", rdclass="IN", id=0)
            dns_query.use_edns(0, payload=4096, pad=113)

            if mode == 0:
                response = client.get(
                    url=f"https://{resolver}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    }
                ).read()
            
            elif mode == 1:
                response = client.get(
                    url=f"https://{resolver_ip}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()
            
            elif mode == 2:
                response = client.get(
                    url=f"https://{resilient_resolver}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()

            elif mode == 3:
                if 'cloudflare' in resolver:
                    response = client.get(
                        url=f"https://cloudflare-dns.com/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()

                else:
                    response = client.get(
                        url=f"https://{resolver}/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
            
            elif mode == 4:
                response = client.get(
                    url=f"https://{resilient_resolver_ip}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": nysni}
                ).read()

            else: # elif mode == 5:
                if 'cloudflare' in resolver:
                    response = client.get(
                        url=f"https://1.1.1.1/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
                
                else:
                    response = client.get(
                        url=f"https://{resolver_ip}/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
 
    except:
        main_logger.exception("During DoH querying")
        response = b""

    return response


def chromium_query(
        client, 
        resolver, 
        domain, 
        main_logger, 
        method,
        resolver_ip= None,
        resilient_resolver= None,
        resilient_resolver_ip = None,
        nysni= None,
):
    """Send Chromium-like DoH query.

    Args:
        client: HTTPX client.
        resolver: The domain name of a DoH resolver.
        domain: The domain name to query.
        main_logger: Python logger object.
        method: The HTTP method to use.
        (optional) resolver_ip: The IP address of a DoH resolver.
        (optional) resilient_resolver: The domain name of a resilient resolver.
        (optional) resilient_resolver_ip: The IP address of a resilient resolver (i.e., fuzzy IP address).
        (optional) nysni: The fuzzy hostname to use.
    
    Returns:
        The response from the DoH resolver.
    """

    ### modes:
    ### 0 - Baseline, 1 - Direct IP, 2 - Fuzzy IP, 3 - Fuzzy hostname, 
    ### 4 - Fuzzy IP + fuzzy hostname, 5 - Direct IP + fuzzy hostname
    if resolver_ip == None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni == None:
        mode = 0
    elif resolver_ip != None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni == None:
        mode = 1
    elif resolver_ip == None and (resilient_resolver != None and resilient_resolver_ip == None) and nysni == None:
        mode = 2
    elif resolver_ip == None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni != None:
        mode = 3
    elif resolver_ip == None and (resilient_resolver != None and resilient_resolver_ip != None) and nysni != None:
        mode = 4
    elif resolver_ip != None and (resilient_resolver == None and resilient_resolver_ip == None) and nysni != None:
        mode = 5
    else:
        print("Wrong configurations in chromium_query")
        exit()

    try:
        if method == Methods.POST:
            dns_query = dns.message.make_query(qname=domain, rdtype="A", rdclass="IN", id=0)
            dns_query.use_edns(0, payload=4096, pad=128)

            if mode == 0:
                response = client.post(
                    url=f"https://{resolver}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    }
                ).read()
            
            elif mode == 1:
                response = client.post(
                    url=f"https://{resolver_ip}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()
            
            elif mode == 2:
                response = client.post(
                    url=f"https://{resilient_resolver}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()
            
            elif mode == 3:
                if 'cloudflare' in resolver:
                    response = client.post(
                        url=f"https://cloudflare-dns.com/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
                
                else:
                    response = client.post(
                        url=f"https://{resolver}/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
            
            elif mode == 4:
                response = client.post(
                    url=f"https://{resilient_resolver_ip}/dns-query",
                    content=dns_query.to_wire(),
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": nysni}
                ).read()
            
            else: # elif mode == 5:
                if 'cloudflare' in resolver:
                    response = client.post(
                        url=f"https://1.1.1.1/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
                else:
                    response = client.post(
                        url=f"https://{resolver_ip}/dns-query",
                        content=dns_query.to_wire(),
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
        
        else: # elif method == Methods.GET:
            dns_query = dns.message.make_query(qname=domain, rdtype="A", rdclass="IN", id=0)
            dns_query.use_edns(0, payload=4096, pad=113)

            if mode == 0:
                response = client.get(
                    url=f"https://{resolver}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    }
                ).read()
            
            elif mode == 1:
                response = client.get(
                    url=f"https://{resolver_ip}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()
            
            elif mode == 2:
                response = client.get(
                    url=f"https://{resilient_resolver}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": resolver}
                ).read()

            elif mode == 3:
                if 'cloudflare' in resolver:
                    response = client.get(
                        url=f"https://cloudflare-dns.com/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()

                else:
                    response = client.get(
                        url=f"https://{resolver}/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
            
            elif mode == 4:
                response = client.get(
                    url=f"https://{resilient_resolver_ip}/dns-query",
                    params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                    headers={
                        'host': resolver,
                        'accept': 'application/dns-message',
                        'content-type': 'application/dns-message',
                        'accept-language': '*',
                        'user-agent': 'Chrome',
                        'accept-encoding': 'identity'
                    },
                    extensions={"sni_hostname": nysni}
                ).read()

            else: # elif mode == 5:
                if 'cloudflare' in resolver:
                    response = client.get(
                        url=f"https://1.1.1.1/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
                else:
                    response = client.get(
                        url=f"https://{resolver_ip}/dns-query",
                        params={"dns": base64.b64encode(dns_query.to_wire()).decode('ascii').rstrip("=")},
                        headers={
                            'host': resolver,
                            'accept': 'application/dns-message',
                            'content-type': 'application/dns-message',
                            'accept-language': '*',
                            'user-agent': 'Chrome',
                            'accept-encoding': 'identity'
                        },
                        extensions={"sni_hostname": nysni}
                    ).read()
 
    except:
        main_logger.exception("During DoH querying")
        response = b""

    return response