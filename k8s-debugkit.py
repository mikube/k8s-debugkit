from flask import Flask, jsonify, request
import os
import subprocess
from psutil import virtual_memory
import requests
import re
import sys

app = Flask(__name__)


@app.route("/")
def index():
    """
    Get all endpoints
    """
    res = {
        "endpoints": [
            "/info/all",
            "/info/common",
            "/info/hostname", "/info/ip", "/info/cpu", "/info/mem",
            "/info/hosts", "/info/resolv", "/info/envs",
            "/exec/echo",
            "/exec/ping/<dst>",
            "/exec/dig/<dst>",
            "/exec/traceroute/<dst>",
            "/exec/get/<path:dst>",
            "/exec/ls/<path:path>",
            "/exec/getenv/<name>",
            "/exec/log/<path:contents>?<mode>"]
    }
    return jsonify(res)


def __all():
    return {
        "hostname": __hostname(),
        "ip": __ip(),
        "cpu": __cpu(),
        "mem": __mem(),
        "hosts": __hosts(),
        "resolv": __resolv(),
        "envs": __envs(),
        "common": __common()
    }


@app.route("/info/all")
def all():
    """
    Get all info in JSON format
    """
    return jsonify(__all())


def __common():
    return {
        "method": request.method,
        "url": request.url,
        "baseUrl": request.base_url,
        "path": request.path,
        "queryString": request.query_string.decode(),
        "sourceIp": request.remote_addr,
        "referrer": request.referrer,
        "headers": dict(request.headers)
    }


@app.route("/info/common")
def common():
    """
    Get common info based on request context
    """
    res = {
        "common": __common()
    }
    return jsonify(res)


def __hostname():
    res = subprocess.run(["hostname"], capture_output=True)
    hostname = res.stdout
    return {
        "hostname": hostname.decode().strip()
    }


@app.route("/info/hostname")
def hostname():
    """
    Get hostname
    hostname in container means container id or pod name on k8s
    """
    return jsonify(__hostname())


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


@app.route("/info/ip")
def ip():
    """
    Get local nic info and global ip
    """
    return jsonify(__ip())


def __cpu():
    return {
        "numOfCpus": os.cpu_count(),
        "numOfSchedCpus": len(os.sched_getaffinity(0))
    }


@app.route("/info/cpu")
def cpu():
    """
    Get the number of cpus
    """
    return jsonify(__cpu())


def __mem():
    return {
        "availableMemory": virtual_memory().total
    }


@app.route("/info/mem")
def mem():
    """
    Get the amount of available memory
    """
    return jsonify(__mem())


def __hosts():
    with open("/etc/hosts", "r") as f:
        return {
            "hosts": [l.strip() for l in f.readlines()]
        }


@app.route("/info/hosts")
def hosts():
    """
    Get /etc/hosts
    """
    return jsonify(__hosts())


def __resolv():
    with open("/etc/resolv.conf", "r") as f:
        return {
            "resolv": [l.strip() for l in f.readlines()]
        }


@app.route("/info/resolv")
def resolv():
    """
    Get /etc/resolv.conf
    """
    return jsonify(__resolv())


def __envs():
    return dict(os.environ)


@app.route("/info/envs")
def envs():
    """
    Get all environmental values
    """
    return jsonify(__envs())


@app.route("/exec/echo", methods=["POST"])
def echo():
    """
    echo POST data
    """
    return request.data


@app.route("/exec/ping/<dst>")
def ping(dst=None):
    """
    ping to dst
    """
    res = subprocess.run(
        ["ping", "-W", "2", "-c", "1", dst], capture_output=True)
    ping = res.stdout
    return jsonify({
        "hostname": __hostname(),
        "ping": ping.decode().strip().split("\n")
    })


@app.route("/exec/dig/<dst>")
def dig(dst=None):
    """
    Resolve name by default name server
    """
    res = subprocess.run(
        ["dig", "+time=2", "+tries=2", dst], capture_output=True)
    return jsonify({
        "hostname": __hostname(),
        "dig": res.stdout.decode().strip().split("\n") +
        res.stderr.decode().strip().split("\n")
    })


@app.route("/exec/traceroute/<dst>")
def traceroute(dst=None):
    """
    traceroute to dst
    """
    res = subprocess.run(
        ["traceroute", "-w", "2", dst], capture_output=True)
    return jsonify({
        "hostname": __hostname(),
        "traceroute": res.stdout.decode().strip().split("\n") +
        res.stderr.decode().strip().split("\n")
    })


@app.route("/exec/get/<path:dst>")
def get(dst=None):
    """
    Exec a http get request to dst
    """
    res = requests.get(dst, timeout=(2, 2))
    return jsonify({
        "hostname": __hostname(),
        "statusCode": res.status_code,
        "headers": dict(res.headers),
        "body": res.text
    })


@app.route("/exec/ls/<path:path>")
def ls(path=None):
    """
    List files
    """
    res = subprocess.run(["ls", "-al", "/"+path], capture_output=True)
    ls = res.stdout
    return jsonify({
        "hostname": __hostname(),
        "ls": ls.decode().strip().split("\n")
    })


@app.route("/exec/getenv/<name>")
def env(name=None):
    """
    Get an environmental value by name
    """
    return jsonify({
        "hostname": __hostname(),
        name: os.getenv(name)
    })


@app.route("/exec/log/<path:contents>")
def log(contents=None):
    """
    Print log
    """
    mode = request.args.get("mode", default="debug")
    if mode == "debug":
        app.logger.debug(contents)
    elif mode == "info":
        app.logger.info(contents)
    elif mode == "warn":
        app.logger.warn(contents)
    elif mode == "error":
        app.logger.error(contents)
    elif mode == "critical":
        app.logger.critical(contents)
    else:
        mode = "debug"
        app.logger.debug(contents)
    return jsonify({
        "hostname": __hostname(),
        "log": contents,
        "mode": mode
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
