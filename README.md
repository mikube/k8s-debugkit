# k8s-debugkit
All-in-one docker image for debugging on Kubernetes and Docker

Note: Insecure, only for development


## Use case
```sh
kubectl create deploy --image=amaya382/k8s-debugkit debugkit
kubectl expose --port=80 --type={type you need} deploy debugkit
```

### Want to know which global ip is used
wget http://{debugkit's ip addr}/info/ip

### Want to check if default name server is working or not
wget http://{debugkit's ip addr}/exec/dig/google.com


## HTTP Server
k8s-debugkit provides HTTP server returning information and executing some commands from pod (container).
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
You can execute commands via HTTP GET

#### `/exec/ping/<dst>`
echo POST data

#### `/exec/dig/<dst>`
Resolve name by default name server

#### `/exec/get/<dst>`
Exec a http get request to dst

#### `/exec/ls/<path>`
List files

#### `/exec/getenv/<name>`
Get an environmental value by name


## CLI Tools
You can use CLI tools below on pod (container)

* `kubectl`
* `ping`
* `curl`
* `wget`
* `dig`
* `nslookup`
* `traceroute`
