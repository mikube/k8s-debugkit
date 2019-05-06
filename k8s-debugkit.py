from flask import Flask, jsonify, request
import os
import subprocess
from psutil import virtual_memory
import requests

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
            "/exec/get/<path:dst>",
            "/exec/ls/<path:path>",
            "/exec/getenv/<name>"]
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
    res_global_ip = requests.get(
        "http://ifconfig.io", headers={'User-Agent': 'curl'})
    return {
        "globalIp": res_global_ip.text.strip(),
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
    `ping` to dst
    """
    res = subprocess.run(
        ["ping", "-c", "1", dst], capture_output=True)
    ping = res.stdout
    return jsonify({
        "ping": ping.decode().strip().split("\n")
    })


@app.route("/exec/dig/<dst>")
def dig(dst=None):
    """
    Resolve name by default name server
    """
    res = subprocess.run(
        ["dig", dst], capture_output=True)
    dig = res.stdout
    return jsonify({
        "dig": dig.decode().strip().split("\n")
    })


@app.route("/exec/get/<path:dst>")
def get(dst=None):
    """
    Exec a http get request to dst
    """
    res = requests.get(dst)
    return jsonify({
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
        "ls": ls.decode().strip().split("\n")
    })


@app.route("/exec/getenv/<name>")
def env(name=None):
    """
    Get an environmental value by name
    """
    return jsonify({
        name: os.getenv(name)
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)
