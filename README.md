<h1 align="center">k8s-debugkit</h1>

All-in-one docker image for debugging on Kubernetes and Docker

**Note: Insecure, only for debugging**


# :soon: Use cases
```sh
kubectl create deploy --image=mikube/k8s-debugkit debugkit
kubectl expose --port=80 --type={type you need} deploy debugkit
```

or

```sh
kubectl apply -f k8s-debugkit.yaml # Default svc type: NodePort
```

And then, access to the debugkit via k8s Service, `kubectl port-forward`, or IP addr directly (Need specific env such as microk8s or telepresence)


## (1) Want to know which global ip is used
```
wget http://{debugkit's ip addr}/info/ip
```

```json
{
  "globalIp": "XXX.XXX.XXX.XXX",
  "ip": [
    "1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000",
    "    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00",
    "    inet 127.0.0.1/8 scope host lo",
    "       valid_lft forever preferred_lft forever",
    "    inet6 ::1/128 scope host ",
    "       valid_lft forever preferred_lft forever",
    "3: eth0@if42: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default ",
    "    link/ether 92:8b:f7:b2:9f:df brd ff:ff:ff:ff:ff:ff link-netnsid 0",
    "    inet 10.1.1.16/24 scope global eth0",
    "       valid_lft forever preferred_lft forever",
    "    inet6 fe80::908b:f7ff:feb2:9fdf/64 scope link ",
    "       valid_lft forever preferred_lft forever"
  ]
}
```
A global ip k8s environment uses by default is `XXX.XXX.XXX.XXX`


## (2) Want to know which pod you're actually accessing (Good for accessing via a load balancer)
```
wget http://{debugkit's ip addr}/info/hostname
```

```json
{
  "hostname": "debugkit-798cb977b-zjvfz"
}
```
hostname means pod name on k8s


## (3) Want to check if the default name server is working or not
```
wget http://{debugkit's ip addr}/exec/dig/google.com
```

```json
{
  "dig": [
    "; <<>> DiG 9.10.3-P4-Debian <<>> google.com",
    ";; global options: +cmd",
    ";; Got answer:",
    ";; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 29948",
    ";; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1",
    "",
    ";; OPT PSEUDOSECTION:",
    "; EDNS: version: 0, flags:; udp: 512",
    ";; QUESTION SECTION:",
    ";google.com.\t\t\tIN\tA",
    "",
    ";; ANSWER SECTION:",
    "google.com.\t\t185\tIN\tA\t172.217.26.46",
    "",
    ";; Query time: 40 msec",
    ";; SERVER: 10.152.183.10#53(10.152.183.10)",
    ";; WHEN: Mon May 06 07:42:12 UTC 2019",
    ";; MSG SIZE  rcvd: 55"
  ],
  "hostname": {
    "hostname": "debugkit-798cb977b-zjvfz"
  }
}
```
Working! Succeeded in resolving `google.com`


# :trident: Features
## HTTP Server
k8s-debugkit provides a HTTP server returning information and executing some commands from pod (container).
You can check a lot of pod information by using just HTTP GET.

### Information
#### `/info/all`
Get all information

#### `/info/commmon`
Get common info based on request context

#### `/info/hostname`
Get hostname.
hostname in container means container id or pod name on k8s.

#### `/info/ip`
Get local nic info and global ip

#### `/info/cpu`
Get the number of cpus

#### `/info/mem`
Get the amount of available memory

#### `/info/hosts`
Get `/etc/hosts`

#### `/info/resolv`
Get `/etc/resolv.conf`

#### `/info/envs`
Get all environmental values

### Command execution
You can execute commands (from container!) via HTTP GET

#### `/exec/ping/{dst}`
ping to dst

#### `/exec/dig/{dst}`
Resolve name by default name server

#### `/exec/traceroute/{dst}`
traceroute to dst

#### `/exec/get/{dst}`
Exec a http get request to dst

#### `/exec/ls/{path}`
List files

#### `/exec/cat/{path}`
Get file contents

#### `/exec/getenv/{name}`
Get an environmental value by name

#### `/exec/log/{msg}?{stderr}`
Print log to stdout. If set stderr, output to stderr.

* `stderr`: Default `False`

#### `/exec/explode?{signal}&{explode_after}`
Explode the container by `signal` after `explode_after`

* `signal`: Default `9`
* `explode_after`: Default `5`

#### `/exec/echo/<dst>`
echo POST data


## CLI Tools
You can directly use the CLI tools below on container by `kubectl exec -it {pod_name} bash` or `docker exec -it {container_name} bash`

* `kubectl`
  * You need pass auth info such as `.kube/config`. e.g. `kubectl cp ~/.kube/config {pod_name}:~/.kube/config`
* `ping`
* `curl`
* `wget`
* `dig`
* `nslookup`
* `traceroute`


## Options
* `K8S_DEBUGKIT_DISABLE_DEBUG_MODE`
  * If set, run in production mode
