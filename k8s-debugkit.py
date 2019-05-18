import responder
import os
import sys
import signal
import subprocess
from psutil import virtual_memory
import requests
import re

api = responder.API()


@api.route("/")
def index(req, res):
    """
    Get all endpoints
    """
    res.media = {
        "endpoints": [
            "/info/all",
            "/info/common",
            "/info/hostname", "/info/ip", "/info/cpu", "/info/mem",
            "/info/hosts", "/info/resolv", "/info/envs",
            "/exec/ping/{dst}",
            "/exec/dig/{dst}",
            "/exec/traceroute/{dst}",
            "/exec/get/{dst}",
            "/exec/ls/{path}",
            "/exec/getenv/{name}",
            "/exec/log/{msg}?{mode}",
            "/exec/echo"]
    }


def __all(req):
    return {
        "hostname": __hostname(),
        "ip": __ip(),
        "cpu": __cpu(),
        "mem": __mem(),
        "hosts": __hosts(),
        "resolv": __resolv(),
        "envs": __envs(),
        "common": __common(req)
    }


@api.route("/info/all")
def all(req, res):
    """
    Get all info in JSON format
    """
    res.media = __all(req)


def __common(req):
    return {
        "method": req.method,
        "url": req.url,
        "fullUrl": req.full_url,
        "params": req.params,
        "cookies": req.cookies,
        "headers": dict(req.headers)
    }


@api.route("/info/common")
def common(req, res):
    """
    Get common info based on request context
    """
    res.media = {
        "common": __common(req)
    }


def __hostname():
    res = subprocess.run(["hostname"], capture_output=True)
    hostname = res.stdout
    return {
        "hostname": hostname.decode().strip()
    }


@api.route("/info/hostname")
def hostname(req, res):
    """
    Get hostname
    hostname in container means container id or pod name on k8s
    """
    res.media = __hostname()


def __ip():
    res_ip = subprocess.run(["ip", "a"], capture_output=True)
    ip = res_ip.stdout
    res_global_ip = subprocess.run(
        ["dig", "@8.8.8.8", "-t", "txt", "o-o.myaddr.l.google.com",
            "+short", "+time=2", "+tries=2"],
        capture_output=True)
    global_ips = res_global_ip.stdout.decode().strip().split("\n")
    filtered_global_ips = [ip for ip in global_ips if "client-subnet" in ip]
    global_ip = "Failed to get global ip"
    if len(filtered_global_ips) == 1:
        str_global_ip = filtered_global_ips[0]
        m = re.search(r"client-subnet (.+)/", str_global_ip)
        if m:
            global_ip = m.group(1)
    return {
        "globalIp": global_ip,
        "ip": ip.decode().strip().split("\n")
    }


@api.route("/info/ip")
def ip(req, res):
    """
    Get local nic info and global ip
    """
    res.media = __ip()


def __cpu():
    return {
        "numOfCpus": os.cpu_count(),
        "numOfSchedCpus": len(os.sched_getaffinity(0))
    }


@api.route("/info/cpu")
def cpu(req, res):
    """
    Get the number of cpus
    """
    res.media = __cpu()


def __mem():
    return {
        "availableMemory": virtual_memory().total
    }


@api.route("/info/mem")
def mem(req, res):
    """
    Get the amount of available memory
    """
    res.media = __mem()


def __hosts():
    with open("/etc/hosts", "r") as f:
        return {
            "hosts": [l.strip() for l in f.readlines()]
        }


@api.route("/info/hosts")
def hosts(req, res):
    """
    Get /etc/hosts
    """
    res.media = __hosts()


def __resolv():
    with open("/etc/resolv.conf", "r") as f:
        return {
            "resolv": [l.strip() for l in f.readlines()]
        }


@api.route("/info/resolv")
def resolv(req, res):
    """
    Get /etc/resolv.conf
    """
    res.media = __resolv()


def __envs():
    return dict(os.environ)


@api.route("/info/envs")
def envs(req, res):
    """
    Get all environmental values
    """
    res.media = __envs()


@api.route("/exec/echo")
async def echo(req, res):
    """
    echo POST data
    """
    if req.method != "post":
        res.media = {
            "error": "POST only"
        }
        res.status_code = 405
        return

    res.media = await req.media()


@api.route("/exec/ping/{dst}")
def ping(req, res, *, dst):
    """
    ping to dst
    """
    result = subprocess.run(
        ["ping", "-W", "2", "-c", "1", dst], capture_output=True)
    res.media = {
        "hostname": __hostname(),
        "ping": result.stdout.decode().strip().split("\n")
    }


@api.route("/exec/dig/{dst}")
def dig(req, res, *, dst):
    """
    Resolve name by default name server
    """
    result = subprocess.run(
        ["dig", "+time=2", "+tries=2", dst], capture_output=True)
    res.media = {
        "hostname": __hostname(),
        "dig": result.stdout.decode().strip().split("\n") +
        result.stderr.decode().strip().split("\n")
    }


@api.route("/exec/traceroute/{dst}")
def traceroute(req, res, *, dst):
    """
    traceroute to dst
    """
    result = subprocess.run(
        ["traceroute", "-w", "2", dst], capture_output=True)
    res.media = {
        "hostname": __hostname(),
        "traceroute": result.stdout.decode().strip().split("\n") +
        result.stderr.decode().strip().split("\n")
    }


@api.route("/exec/get/{dst}")
def get(req, res, *, dst):
    """
    Exec a http get request to dst
    """
    result = requests.get(dst, timeout=(2, 2))
    res.media = {
        "hostname": __hostname(),
        "statusCode": result.status_code,
        "headers": dict(result.headers),
        "body": result.text
    }


@api.route("/exec/ls/{path}")
def ls(req, res, *, path):
    """
    List files
    """
    result = subprocess.run(["ls", "-al", "/"+path], capture_output=True)
    res.media = {
        "hostname": __hostname(),
        "ls": result.stdout.decode().strip().split("\n")
    }


@api.route("/exec/getenv/{name}")
def env(req, res, *, name):
    """
    Get an environmental value by name
    """
    res.media = {
        "hostname": __hostname(),
        name: os.getenv(name)
    }


@api.route("/exec/log/{msg}")
def log(req, res, *, msg):
    """
    Print log
    """
    stderr = req.params.get("stderr")
    if stderr == None:
        print(msg, flush=True)
    else:
        print(msg, flush=True, file=sys.stderr)
    res.media = {
        "log": {
                "msg": msg,
                "stderr": stderr != None
            }
        }


if __name__ == "__main__":
    disable_debug = os.getenv("K8S_DEBUGKIT_DISABLE_DEBUG_MODE")
    api.run(debug=False if disable_debug != None else True, address="0.0.0.0", port=80)
