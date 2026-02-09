# Oracle CNE Training Dataset - CLI Reference

## CLI Usage Basics

### Q1
**Question:** How do I get help with `ocne` command syntax?

**Answer:** You can get help in several ways:
- Run `ocne` without options to display general help
- Use `--help` or `-h` with any command: `ocne cluster --help`
- Use the help command: `ocne help cluster`

All commands include built-in help showing syntax and available options.

### Q2
**Question:** Can I use abbreviations for `ocne` commands?

**Answer:** Yes, you can use prefix matching for any unambiguous prefix of an `ocne` command. For example:
- `ocne cl s` instead of `ocne cluster start`
- `ocne clu star` instead of `ocne cluster start`
- `ocne ap l` instead of `ocne application list`
- `ocne ca l` instead of `ocne catalog list`

### Q3
**Question:** How do I set up command line completion for `ocne`?

**Answer:** Generate a command line completion script for your shell and save it to the appropriate location. For Bash on Oracle Linux:
```bash
ocne completion bash | sudo tee /etc/bash_completion.d/ocne
```
Then start a new shell session. This requires the `bash-completion` package to be installed.

### Q4
**Question:** What shells support `ocne` command completion?

**Answer:** The `ocne completion` command supports generating completion scripts for Bash, Zsh, fish, and PowerShell shells. Use `ocne completion <shell>` to generate the appropriate script.

### Q5
**Question:** What environment variables can I use with the `ocne` CLI?

**Answer:** The `ocne` CLI supports these environment variables:
- `KUBECONFIG` - Sets the kubeconfig file location (same as `--kubeconfig` option)
- `EDITOR` - Sets the default document editor (e.g., `/usr/bin/vim`)
- `OCNE_DEFAULTS` - Overrides the default config file location (default: `$HOME/.ocne/defaults.yaml`)
- `OCNE_OLVM_USERNAME` - Sets username for Oracle Linux Virtualization Manager
- `OCNE_OLVM_PASSWORD` - Sets password for Oracle Linux Virtualization Manager
- `OCNE_OLVM_SCOPE` - Sets authorization scope for Oracle Linux Virtualization Manager

### Q6
**Question:** How do I view the values of `ocne` environment variables?

**Answer:** Use the `ocne info` command to display CLI version information and the values of all environment variables that the CLI uses.

## Configuration Files

### Q7
**Question:** How does configuration layering work in Oracle CNE?

**Answer:** Oracle CNE uses three hierarchical configuration layers (in precedence order):
1. Global defaults in `$HOME/.ocne/defaults.yaml`
2. Kubernetes cluster configuration files (any name)
3. Options provided with the `ocne` command

Each layer can override the previous layer, with command-line options having the highest precedence.

### Q8
**Question:** Where is the default configuration file located?

**Answer:** The default configuration file is located at `$HOME/.ocne/defaults.yaml`. This file isn't created when you install the CLI, so you must create it manually to use it. You can override this location with the `OCNE_DEFAULTS` environment variable.

### Q9
**Question:** What format must configuration files use?

**Answer:** All Oracle CNE configuration files must be in YAML format. This applies to the default configuration file (`$HOME/.ocne/defaults.yaml`) and cluster-specific configuration files.

### Q10
**Question:** How do I set the UI to not automatically start when creating a cluster?

**Answer:** Set the `autoStartUI` option in your configuration file:
```yaml
autoStartUI: false
```
By default, a tunnel to the UI service is created and the default browser loads the UI when a cluster starts.

### Q11
**Question:** How do I specify a custom OCK image in the configuration file?

**Answer:** Use the `bootVolumeContainerImage` option to specify the container registry and tag:
```yaml
bootVolumeContainerImage: container-registry.oracle.com/olcne/ock:1.33
```
The default is the Oracle Container Registry OCK image.

### Q12
**Question:** How do I specify which CNI to install?

**Answer:** Use the `cni` option in your configuration file:
```yaml
cni: flannel
```
Or set it to `none` if you plan to deploy another CNI manually or using an application catalog. Note that Multus cannot be used as the primary CNI - it's available as an application in the catalog.

### Q13
**Question:** How do I configure the cluster to not install the UI?

**Answer:** Set the `headless` option to `true` in your configuration file:
```yaml
headless: true
```
The default is `false`, which installs the UI.

### Q14
**Question:** How do I configure the Kubernetes API server port?

**Answer:** Use the `kubeApiServerBindPort` option (default is 6443):
```yaml
kubeApiServerBindPort: 6443
```
For HA clusters using the Keepalived and NGINX load balancer, also set `kubeApiServerBindPortAlt` (default is 6444):
```yaml
kubeApiServerBindPortAlt: 6444
```

### Q15
**Question:** How do I set the kube-proxy mode?

**Answer:** Use the `kubeProxyMode` option with either `iptables` or `ipvs`:
```yaml
kubeProxyMode: ipvs
```
The default is `iptables`.

### Q16
**Question:** How do I specify a specific Kubernetes version?

**Answer:** Use the `kubernetesVersion` option in your configuration file:
```yaml
kubernetesVersion: 1.33
```
The default is the latest version.

### Q17
**Question:** How do I configure proxy settings for the cluster?

**Answer:** Use the `proxy` option with `httpProxy`, `httpsProxy`, and `noProxy` fields:
```yaml
proxy:
  httpsProxy: http://myproxy.example.com:2138
  httpProxy: http://myproxy.example.com:2138
  noProxy: .example.com,127.0.0.1,localhost,169.254.169.254,10.96.0.0/12,10.244.0.0/16
```
This information is configured on the Kubernetes nodes.

### Q18
**Question:** How do I set SSH public key authentication in the configuration?

**Answer:** You can use either `sshPublicKey` to include the key inline or `sshPublicKeyPath` to specify a path:
```yaml
sshPublicKeyPath: /home/username/.ssh/id_rsa.ocne
```
Or inline:
```yaml
sshPublicKey: | 
  ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA...
```
This key is used for the OCK image user (`ocne`).

### Q19
**Question:** How do I set a hashed password for cluster nodes?

**Answer:** Use the `password` option with a hashed password:
```yaml
password: $6$jfkldjfsd$n1YMnpdxlGXO...
```
You can generate a hashed password using OpenSSL:
```bash
openssl passwd -6 password
```
Or with a specific salt:
```bash
openssl passwd -6 -salt saltphrase password
```

### Q20
**Question:** How do I configure pod and service subnets?

**Answer:** Use `podSubnet` and `serviceSubnet` options:
```yaml
podSubnet: 10.244.0.0/16
serviceSubnet: 10.96.0.0/12
```
The CNI is automatically configured to use these subnets. The service subnet default is `10.96.0.0/12`.

## libvirt Provider Configuration

### Q21
**Question:** How do I configure control plane node resources for libvirt?

**Answer:** Use the `providers.libvirt.controlPlaneNode` section:
```yaml
providers:
  libvirt:
    controlPlaneNode:
      cpu: 2
      memory: 16Gi
      storage: 8Gi
```
Sizes can use M (megabytes), G (gigabytes), Mi (mebibytes), or Gi (gibibytes).

### Q22
**Question:** How do I specify a custom libvirt network?

**Answer:** Use the `providers.libvirt.network` option:
```yaml
providers:
  libvirt:
    network: bridge-1
```

### Q23
**Question:** How do I configure a remote libvirt connection?

**Answer:** Use the `providers.libvirt.uri` option:
```yaml
providers:
  libvirt:
    uri: qemu+ssh://user@host/system
```
For local connections:
```yaml
providers:
  libvirt:
    uri: qemu:///system
```

## Application Commands

### Q24
**Question:** How do I install an application from the default catalog?

**Answer:** Use `ocne application install` with the release name, namespace, and application name:
```bash
ocne application install --release ingress-nginx --namespace ingress-nginx --name ingress-nginx
```

### Q25
**Question:** How do I install an application with custom configuration?

**Answer:** Use the `--values` option to provide configuration (Helm values):
```bash
ocne application install --release prometheus --namespace prometheus --name prometheus --values mytemplate.yaml
```
Or pipe configuration inline:
```bash
ocne application install --release prometheus --namespace prometheus --name prometheus --values - << EOF
<configuration>
EOF
```

### Q26
**Question:** How do I install the Oracle application catalog?

**Answer:** Use the `--built-in-catalog` option:
```bash
ocne application install --built-in-catalog
```
This installs the `ocne-catalog` into the `ocne-system` namespace in environments where it isn't installed by default.

### Q27
**Question:** How do I list all installed applications?

**Answer:** Use `ocne application list` with the `--all` flag to see applications in all namespaces:
```bash
ocne application list --all
```
Or list applications in a specific namespace:
```bash
ocne application list --namespace prometheus
```

### Q28
**Question:** How do I view details about an installed application?

**Answer:** Use `ocne application show` with the release name:
```bash
ocne application show --namespace kube-flannel --release flannel --computed
```
The `--computed` flag shows the complete configuration including both custom and default values.

### Q29
**Question:** How do I generate a template for an application?

**Answer:** Use `ocne application template`:
```bash
ocne application template --name prometheus > mytemplate.yaml
```
Or use `--interactive` to open it in your editor:
```bash
ocne application template --name prometheus --interactive
```

### Q30
**Question:** How do I update an application?

**Answer:** Use `ocne application update` with the release name and any new values:
```bash
ocne application update --release prometheus --namespace prometheus --values mytemplate.yaml
```
Use `--reset-values` to reset to chart defaults.

### Q31
**Question:** How do I uninstall an application?

**Answer:** Use `ocne application uninstall` with the release name:
```bash
ocne application uninstall --release prometheus --namespace prometheus
```

## Catalog Commands

### Q32
**Question:** How do I add an external catalog?

**Answer:** Use `ocne catalog add` with the protocol, name, and URI:
```bash
ocne catalog add --protocol artifacthub --name artifacthub --uri https://artifacthub.io
```
The protocol can be `helm` or `artifacthub`.

### Q33
**Question:** How do I list all configured catalogs?

**Answer:** Use `ocne catalog list` or `ocne catalog ls`:
```bash
ocne catalog list
```

### Q34
**Question:** How do I search for applications in a catalog?

**Answer:** Use `ocne catalog search`:
```bash
ocne catalog search
```
For the embedded catalog:
```bash
ocne catalog search --name embedded
```
To search with a pattern:
```bash
ocne catalog search --pattern 'ingress-*'
```

### Q35
**Question:** How do I mirror a catalog to a private registry?

**Answer:** Use `ocne catalog mirror` with destination and push:
```bash
ocne catalog mirror --destination myregistry.example.io --push
```
To mirror only specific applications listed in a config file:
```bash
ocne catalog mirror --destination myregistry.example.io --config mycluster.yaml --push
```

### Q36
**Question:** How do I download catalog images to an archive file?

**Answer:** Use `ocne catalog mirror` with the `--download` option:
```bash
ocne catalog mirror --download
```
This saves to `$HOME/.ocne/downloaded-images.tgz` by default. Specify a custom location with `--archive`:
```bash
ocne catalog mirror --download --archive $HOME/myimages.tgz
```

### Q37
**Question:** How do I remove a catalog?

**Answer:** Use `ocne catalog remove` with the catalog name:
```bash
ocne catalog remove --name artifacthub
```

## Cluster Management Commands

### Q38
**Question:** How do I create a default libvirt cluster?

**Answer:** Simply run:
```bash
ocne cluster start
```
This creates a single-node cluster using all default settings and installs the UI and application catalog.

### Q39
**Question:** How do I create a cluster with specific numbers of nodes?

**Answer:** Use the `--control-plane-nodes` and `--worker-nodes` options:
```bash
ocne cluster start --control-plane-nodes 3 --worker-nodes 5
```

### Q40
**Question:** How do I create a cluster with a virtual IP?

**Answer:** Use the `--virtual-ip` option:
```bash
ocne cluster start --control-plane-nodes 3 --worker-nodes 5 --virtual-ip 192.168.0.100
```
If not set, a virtual IP is automatically assigned using the subnet of the control plane nodes.

### Q41
**Question:** How do I create a cluster using a configuration file?

**Answer:** Use the `--config` option:
```bash
ocne cluster start --config myconfig.yaml
```

### Q42
**Question:** How do I create a cluster on a specific provider?

**Answer:** Use the `--provider` option with `libvirt` (default), `oci`, `olvm`, `byo`, or `none`:
```bash
ocne cluster start --provider oci
```
Or:
```bash
ocne cluster start --provider olvm
```

### Q43
**Question:** How do I create a remote libvirt cluster?

**Answer:** Use the `--session` option with the qemu+ssh URI:
```bash
ocne cluster start --session qemu+ssh://myuser@myhost.example.com/system --config myconfig.yaml
```

### Q44
**Question:** How do I list all known clusters?

**Answer:** Use `ocne cluster list` or `ocne cluster ls`:
```bash
ocne cluster list
```

### Q45
**Question:** How do I get the kubeconfig file location for a cluster?

**Answer:** Use `ocne cluster show` with the cluster name:
```bash
ocne cluster show --cluster-name mycluster
```
For the default cluster:
```bash
ocne cluster show
```

### Q46
**Question:** How do I view the full configuration of a cluster?

**Answer:** Use `ocne cluster show` with the `--all` flag:
```bash
ocne cluster show --cluster-name mycluster --all
```

### Q47
**Question:** How do I view a specific configuration field?

**Answer:** Use `ocne cluster show` with the `--field` option:
```bash
ocne cluster show --cluster-name mycluster --field config.providerconfig.libvirt
```

### Q48
**Question:** How do I delete a cluster?

**Answer:** Use `ocne cluster delete`:
```bash
ocne cluster delete --cluster-name mycluster
```
For the default cluster:
```bash
ocne cluster delete
```
This only works for clusters created using local virtualization, not bare metal or cloud provider clusters.

### Q49
**Question:** How do I generate a cluster template?

**Answer:** Use `ocne cluster template` and pipe to a file:
```bash
ocne cluster template > mytemplate.yaml
```
Specify a provider:
```bash
ocne cluster template --provider oci > oci-template.yaml
```

## Cluster Updates and Backups

### Q50
**Question:** How do I stage a Kubernetes version update?

**Answer:** Use `ocne cluster stage` with the target version:
```bash
ocne cluster stage --version 1.33
```
Nodes will poll the container registry to pull and stage the OCK image. After staging, use `ocne node update` to install and reboot nodes.

### Q51
**Question:** How do I update a node to a staged OCK image?

**Answer:** Use `ocne node update` with the node name:
```bash
ocne node update --node mynode
```
This drains the node, installs the staged image, reboots, and returns the node to the cluster.

### Q52
**Question:** What happens during a node update?

**Answer:** The `ocne node update` command performs these actions:
1. Drains the node from the cluster using `kubectl drain` (evicting pods)
2. Installs the host OCK image and restarts the node
3. Returns the node to the cluster using `kubectl uncordon` and makes it available for pods

### Q53
**Question:** How do I back up a cluster?

**Answer:** Use `ocne cluster backup` with an output location:
```bash
ocne cluster backup --out mybackup.db
```
This backs up the etcd database containing cluster state. The backup is saved in etcd database format.

### Q54
**Question:** How do I restore a cluster from backup?

**Answer:** The CLI doesn't provide a restore command. For information on restoring a cluster using the etcd backup, refer to the upstream Kubernetes documentation.

## Cluster Analysis and Debugging

### Q55
**Question:** How do I dump cluster information for analysis?

**Answer:** Use `ocne cluster dump` with an output directory:
```bash
ocne cluster dump --output-directory $HOME/dump
```
By default, all cluster resources are included except Secrets and ConfigMaps.

### Q56
**Question:** How do I create a cluster dump archive file?

**Answer:** Use `ocne cluster dump` with the `--generate-archive` option:
```bash
ocne cluster dump --generate-archive $HOME/dump/cluster_dump.tgz
```

### Q57
**Question:** How do I dump only specific namespaces or nodes?

**Answer:** Use the `--namespaces` or `--nodes` options:
```bash
ocne cluster dump --output-directory $HOME/dump --namespaces kube-system,default
```
Or for specific nodes:
```bash
ocne cluster dump --output-directory $HOME/dump --nodes mynode1,mynode2
```

### Q58
**Question:** How do I analyze a cluster dump?

**Answer:** Use `ocne cluster analyze` with the dump directory:
```bash
ocne cluster analyze --dump-directory $HOME/dump/
```
For more detailed output:
```bash
ocne cluster analyze --dump-directory $HOME/dump/ --verbose
```

### Q59
**Question:** How do I analyze a live cluster?

**Answer:** Use `ocne cluster analyze` without the dump directory option:
```bash
ocne cluster analyze
```
To skip node data:
```bash
ocne cluster analyze --skip-nodes
```

### Q60
**Question:** How do I get cluster and node information?

**Answer:** Use `ocne cluster info`:
```bash
ocne cluster info
```
To skip node data:
```bash
ocne cluster info --skip-nodes
```

## OS Console Access

### Q61
**Question:** How do I access a node's OS console?

**Answer:** Use `ocne cluster console` with the node name:
```bash
ocne cluster console --node mynode
```

### Q62
**Question:** How do I start a console with debugging tools?

**Answer:** Use the `--toolbox` option:
```bash
ocne cluster console --node mynode --toolbox
```
This includes tools like strace, tcpdump, traceroute, and sos.

### Q63
**Question:** How do I start a console chrooted to the node's filesystem?

**Answer:** Use the `--direct` option:
```bash
ocne cluster console --direct --node mynode
```

### Q64
**Question:** How do I run a command on a node without an interactive console?

**Answer:** Use the `--` option followed by your command:
```bash
ocne cluster console --direct --node mynode -- ls /proc
```
The console connection closes after the command completes.

## Image Management

### Q65
**Question:** How do I create an OCK image for OCI?

**Answer:** Use `ocne image create` with the architecture:
```bash
ocne image create --type oci --arch amd64
```
The image is saved to `$HOME/.ocne/images/`.

### Q66
**Question:** How do I create an OSTree image for BYO deployments?

**Answer:** Use `ocne image create` with type `ostree`:
```bash
ocne image create --type ostree --arch arm64
```

### Q67
**Question:** How do I upload an OCK image to OCI?

**Answer:** Use `ocne image upload` with the compartment and file path:
```bash
ocne image upload --compartment ocid1.compartment.oc1..UniqueID --file $HOME/.ocne/images/boot.qcow2-1.33-amd64.oci --arch amd64
```

### Q68
**Question:** How do I upload an OSTree image to a container registry?

**Answer:** Use `ocne image upload` with the destination:
```bash
ocne image upload --type ostree --file $HOME/.ocne/images/ock-1.33-amd64-ostree.tar --destination docker://myregistry.example.com/ock-ostree:latest --arch amd64
```

### Q69
**Question:** How do I upload an OCK image to Oracle Linux Virtualization Manager?

**Answer:** Use `ocne image upload` with the olvm type and configuration file:
```bash
ocne image upload --type olvm --file $HOME/.ocne/images/boot.qcow2-1.33-amd64.olvm --arch amd64 --config myconfig.yaml
```

## Cluster Join Operations

### Q70
**Question:** How do I migrate a node to another BYO cluster?

**Answer:** Use `ocne cluster join` with source kubeconfig and destination:
```bash
ocne cluster join --kubeconfig $HOME/.kube/kubeconfig.mycluster --provider byo --node source-worker-1 --destination $HOME/.kube/kubeconfig.targetcluster
```

### Q71
**Question:** How do I migrate a node as a control plane node?

**Answer:** Add the `--role-control-plane` option:
```bash
ocne cluster join --kubeconfig $HOME/.kube/kubeconfig.mycluster --provider byo --node source-worker-1 --destination $HOME/.kube/kubeconfig.targetcluster --role-control-plane
```

### Q72
**Question:** How do I generate an Ignition file for joining a worker node?

**Answer:** Use `ocne cluster join` and redirect output:
```bash
ocne cluster join --kubeconfig $HOME/.kube/kubeconfig.mycluster --config byo.yaml > worker.ign
```

### Q73
**Question:** How do I generate an Ignition file for a control plane node?

**Answer:** Use `ocne cluster join` with `--role-control-plane`:
```bash
ocne cluster join --kubeconfig $HOME/.kube/kubeconfig.mycluster --config byo.yaml --role-control-plane > control_plane.ign
```

## Advanced Configuration

### Q74
**Question:** How do I configure an ephemeral cluster?

**Answer:** Use the `ephemeralCluster` option to customize short-lived clusters:
```yaml
ephemeralCluster:
  name: mycluster
  preserve: true
  node:
    cpus: 2
    memory: 4GB
    storage: 15GB
```
Setting `preserve: true` prevents automatic deletion after use.

### Q75
**Question:** How do I add custom Ignition configuration?

**Answer:** Use `extraIgnition` or `extraIgnitionInline`:
```yaml
extraIgnition: /home/username/.ocne/ignition.ign
```
Or inline:
```yaml
extraIgnitionInline: |
  key1: value1
  key2: value2
```
Configuration must comply with Ignition specification v3.4.0 in Butane Fedora CoreOS Specification v1.5.0 format.

### Q76
**Question:** How do I use a custom kubeconfig for operations?

**Answer:** Use the `kubeconfig` option in your configuration file or the `--kubeconfig` command option:
```yaml
kubeconfig: /home/username/.kube/kubeconfig.utilitycluster
```
This applies to operations requiring a running cluster.

### Q77
**Question:** How do I configure a custom container registry?

**Answer:** Use the `registry` option:
```yaml
registry: myregistry.example.com
```
The default is `container-registry.oracle.com`.

### Q78
**Question:** How do I enable the Artifact Hub catalog?

**Answer:** Set `communityCatalog` to `true`:
```yaml
communityCatalog: true
```
The default is `false`.

### Q79
**Question:** How do I reduce CLI output messages?

**Answer:** Set the `quiet` option to `true`:
```yaml
quiet: true
```
Or use the global `--log-level` flag:
```bash
ocne cluster start --log-level error
```

### Q80
**Question:** What log levels are available?

**Answer:** The `--log-level` global flag supports four levels:
- `error` - Only error messages
- `info` - Informational messages (default)
- `debug` - Debug information
- `trace` - Detailed trace information

Use with any command:
```bash
ocne cluster start --log-level debug
```