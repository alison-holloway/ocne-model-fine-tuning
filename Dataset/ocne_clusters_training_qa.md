# Oracle CNE Training Dataset - Kubernetes Clusters

## Overview & Configuration

### Q1
**Question:** What provider types can I use to create Kubernetes clusters in Oracle CNE?

**Answer:** Oracle CNE supports four provider types:
- `libvirt` - Creates KVM-based clusters (default provider)
- `olvm` - Creates clusters on Oracle Linux Virtualization Manager
- `oci` - Creates clusters on Oracle Cloud Infrastructure
- `byo` - Creates custom clusters on bare metal or other platforms (Bring Your Own)

Each provider uses the OCK image to provision nodes in a cluster.

### Q2
**Question:** How do I deploy applications automatically when creating a cluster?

**Answer:** Use the `applications` option in your cluster configuration file:
```yaml
applications:
  - name: istio-ingress
    release: my-istio-ingress
    catalog: embedded
  - name: prometheus
    release: my-prometheus
    catalog: embedded
    config: git://gitlab.example.com/configs/prometheus.yaml
```
Applications are deployed after the cluster is instantiated.

### Q3
**Question:** How do I add catalogs automatically when creating a cluster?

**Answer:** Use the `catalogs` option in your cluster configuration file:
```yaml
catalogs:
  - name: mycatalog
    uri: https://mycatalog.example.com/catalog
```
The `name` field is used by Oracle CNE interfaces to refer to the catalog, and `uri` sets the source.

### Q4
**Question:** What load balancer options are available for control plane HA?

**Answer:** You have two options for High Availability of control plane nodes:
1. **External load balancer** - Specify using the `loadBalancer` option with hostname or IP address
2. **Internal load balancer** - Use built-in Keepalived and NGINX by specifying a `virtualIp` address (or let it be auto-assigned from the control plane subnet)

Use one option or the other, not both.

## OCK Image

### Q5
**Question:** What credentials does the OCK image user use by default?

**Answer:** The OCK image has a predefined `ocne` user that authenticates via SSH using an RSA public key at `$HOME/.ssh/id_rsa.pub` by default. You can configure alternative authentication using:
- `sshPublicKey` or `sshPublicKeyPath` for different SSH keys
- `password` for hashed password authentication (generated with `openssl passwd -6`)

### Q6
**Question:** What happens when I SSH into a node?

**Answer:** When you SSH into a node as the `ocne` user, it returns the node's kubeconfig file and the SSH connection immediately closes. Full access to the node is only possible using its console via `ocne cluster console`.

### Q7
**Question:** How do I create a custom OCK image?

**Answer:** Use `ocne image create` with the appropriate type:
```bash
ocne image create --type oci --arch amd64
ocne image create --type olvm --arch amd64
ocne image create --type ostree --arch arm64
```
Images are saved to `$HOME/.ocne/images/`. Creating images requires access to a Kubernetes cluster (existing or ephemeral).

### Q8
**Question:** What storage should I allocate for image conversion?

**Answer:** Image conversion requires significant space. Allocate at least 20GB of storage to cluster nodes. Configure this in your defaults file:
```yaml
ephemeralCluster:
  node:
    storage: 20G
providers:
  libvirt:
    workerNode:
      storage: 20G
    controlPlaneNode:
      storage: 20G
```

## Proxy Configuration

### Q9
**Question:** How do I configure proxy settings for the CLI?

**Answer:** Set environment variables on the host where the CLI is installed:
```bash
export HTTPS_PROXY=https://proxy.example.com:3128
export NO_PROXY=.example.com,127.0.0.1,localhost,169.254.169.254
```
The `169.254.169.254` IP is reserved by cloud providers for instance metadata access.

### Q10
**Question:** How do I configure proxy settings for the Kubernetes cluster?

**Answer:** Use the `proxy` option in your configuration file:
```yaml
proxy:
  httpsProxy: http://myproxy.example.com:2138
  httpProxy: http://myproxy.example.com:2138
  noProxy: .example.com,127.0.0.1,localhost,169.254.169.254,10.96.0.0/12,10.244.0.0/16
```
Include the service subnet (`10.96.0.0/12`) and pod network (`10.244.0.0/16`) in `noProxy`.

### Q11
**Question:** How do I configure proxy settings for the UI when using external catalogs?

**Answer:** Create a proxy configuration YAML file and update the `ui` application:
```yaml
env:
  - name: https_proxy
    value: http://myproxy.example.com:2138
  - name: http_proxy
    value: http://myproxy.example.com:2138
  - name: no_proxy
    value: ".example.com,127.0.0.1,localhost,169.254.169.254,10.96.0.0/12,10.244.0.0/16"
```
Then: `ocne application update --namespace ocne-system --release ui --values myproxy.yaml`

## libvirt Provider

### Q12
**Question:** What are the system requirements for libvirt clusters?

**Answer:** The system must be:
- 64-bit x86 or 64-bit ARM
- Running Oracle Linux 8 or 9
- Include Unbreakable Enterprise Kernel Release 7 (UEK R7)

Oracle recommends using the Oracle KVM stack (requires UEK R7 for OL9, UEK R6 or R7 for OL8).

### Q13
**Question:** Can I create hybrid x86/ARM libvirt clusters?

**Answer:** No, because all cluster nodes run on a single host, hybrid clusters aren't possible. However, you can use an ARM system to create a remote cluster on x86 hardware, and vice versa.

### Q14
**Question:** What kubeconfig files are created for libvirt clusters?

**Answer:** Two kubeconfig files are created:
1. `$HOME/.kube/kubeconfig.<cluster_name>.local` - Direct access to the Kubernetes API server (works for localhost or remote)
2. `$HOME/.kube/kubeconfig.<cluster_name>.vm` - Access through SLiRP tunnel for remote systems

Copy the `.vm` file to the remote system if you want to access the cluster from there.

### Q15
**Question:** What port range does libvirt use for cluster access?

**Answer:** Clusters create a tunnel starting at port 6443 and incrementing. Ports are freed when clusters are deleted. For remote clusters, ensure ports starting at 6443 are accessible through the firewall. Open a range like:
```bash
sudo firewall-cmd --add-port 6443-6463/tcp --permanent
```

## Oracle Linux Virtualization Manager Provider

### Q16
**Question:** What is the oVirt CSI driver and how is it used?

**Answer:** The oVirt CSI driver is automatically installed in OLVM clusters and enables persistent storage for Kubernetes applications using PersistentVolumes backed by Oracle Linux Virtualization Manager storage disks. When creating a StorageClass, set:
- `provisioner: csi.ovirt.org`
- `storageDomainName: <storage_domain_name>`
- `thinProvisioning: true` or `false`
- `fsType: ext4` (or desired filesystem)

### Q17
**Question:** What environment variables are required for OLVM provider setup?

**Answer:** Set these OAuth 2.0 connection variables:
```bash
export OCNE_OLVM_USERNAME=admin@internal
export OCNE_OLVM_PASSWORD=password
export OCNE_OLVM_SCOPE=ovirt-app-api
```
The username must have the `@internal` suffix.

### Q18
**Question:** How do I obtain the CA Certificate for Oracle Linux Virtualization Manager?

**Answer:** Use `wget` to download the CA Certificate:
```bash
wget --output-document ca.crt https://<fqdn>/ovirt-engine/services/pki-resource?resource=ca-certificate&format=X509-PEM-CA
```
Replace `<fqdn>` with your OLVM instance's fully qualified domain name. Use only the second certificate returned.

### Q19
**Question:** Can I use DHCP for IP assignment in OLVM clusters?

**Answer:** No, DHCP cannot be used to assign IP addresses to VMs used for Kubernetes nodes. You must provide a range of IP addresses for nodes and set a virtual IP for the Keepalived and NGINX load balancer.

### Q20
**Question:** What are the mandatory configuration options for OLVM clusters?

**Answer:** Minimum required configuration:
```yaml
provider: olvm
name: <cluster_name>
virtualIp: <IP_address>
providers:
  olvm:
    olvmDatacenterName: <datacenter_name>
    olvmOvirtAPIServer:
      serverURL: <URL>
      serverCAPath: <path>
    olvmOCK:
      storageDomainName: <domain_name>
      diskName: <image_name>
      diskSize: <size>
    controlPlaneMachine: <options>
    workerMachine: <options>
```

### Q21
**Question:** How do I create a VM template for OLVM?

**Answer:** After uploading the OCK image to Oracle Linux Virtualization Manager:
1. Create a VM in the console with OS set to "Oracle CNE - OCK x64"
2. Attach the uploaded boot.qcow2 image and select OS (boot) checkbox
3. After VM creation completes, select "Make Template"
4. Name the template to match `vmTemplateName` in your config file
5. Delete the VM (but don't remove its disk - it's used by the template)

### Q22
**Question:** How do I monitor an OLVM cluster installation?

**Answer:** View logs and status in the management cluster:
```bash
kubectl get events --namespace olvm
kubectl get machine --namespace olvm
kubectl get olvmmachine --namespace olvm
kubectl logs --namespace capi-system core-capi-controller-manager-<pod>
kubectl logs --namespace cluster-api-provider-olvm olvm-capi-controller-manager-<pod>
```
Check that Machine objects show `PHASE: Running` and OLVMMachine objects show `READY: true`.

### Q23
**Question:** How do I scale worker nodes in an OLVM cluster?

**Answer:** Use `kubectl scale` on the machinedeployment:
```bash
kubectl get machinedeployments --namespace olvm
kubectl scale machinedeployment <name> --replicas 3 --namespace olvm
```
Wait for the cluster to stabilize before other operations: `watch kubectl get nodes -A`

### Q24
**Question:** How do I scale control plane nodes in an OLVM cluster?

**Answer:** Use `kubectl scale` on the kubeadmcontrolplane:
```bash
kubectl get kubeadmcontrolplane --namespace olvm
kubectl scale kubeadmcontrolplane <name> --replicas 3 --namespace olvm
```
Control plane nodes must be an odd number (1, 3, 5) to avoid split-brain scenarios.

### Q25
**Question:** How do I upgrade an OLVM cluster to a new Kubernetes minor version?

**Answer:** Process involves creating new nodes with updated OCK image:
1. Create and upload new OCK image with updated K8s version
2. Create new VM template using the updated image
3. Edit cluster config to reference new template name
4. Run `ocne cluster stage --version 1.33 --config mycluster.yaml`
5. Patch KubeadmControlPlane using command from stage output
6. Wait for control plane nodes to reprovision
7. Patch MachineDeployment for worker nodes
8. Verify all nodes show new version with `kubectl get nodes`

## OCI Provider

### Q26
**Question:** What setup is required for the OCI provider?

**Answer:** You need to:
1. Install and configure the OCI CLI with key pair and config file
2. Create an Object Storage bucket named `ocne-images` (or specify a different name in config)
3. Set required configuration: compartment OCID/path, optionally VCN and subnets for load balancer
4. Have a management cluster available (or localhost set up for ephemeral cluster)

### Q27
**Question:** How do I specify an OCI compartment?

**Answer:** Compartments can be specified by OCID or by path:
```yaml
providers:
  oci:
    compartment: ocid1.compartment.oc1..UniqueID
```
Or:
```yaml
providers:
  oci:
    compartment: parentcompartment/mycompartment
```

### Q28
**Question:** What is a Cluster API template and when do I use it?

**Answer:** A Cluster API template is a YAML file containing Cluster Resources for the Kubernetes Cluster API to create a cluster. Use templates when you need customization beyond what's available in cluster configuration files. Generate with:
```bash
ocne cluster template --provider oci > mytemplate.yaml
```
Edit the template, then reference it in your cluster config.

### Q29
**Question:** How do I use an existing VCN for an OCI cluster?

**Answer:** In your Cluster API template, modify the `OCICluster` spec to reference your existing VCN and subnets instead of creating new ones. Set the `networkSpec` with your VCN OCID and subnet OCIDs for control plane and workers.

### Q30
**Question:** How do I upload an OCK image to OCI?

**Answer:** First create the image, then upload:
```bash
ocne image create --type oci --arch amd64
ocne image upload --compartment <OCID> --file $HOME/.ocne/images/boot.qcow2-1.33-amd64.oci --arch amd64
```
The image is loaded into Object Storage and a custom compute image is created.

### Q31
**Question:** How do I create a self-managed OCI cluster?

**Answer:** Set `selfManaged: true` in your config:
```yaml
providers:
  oci:
    selfManaged: true
```
After deployment, Cluster API resources are migrated from the management cluster into the workload cluster itself.

### Q32
**Question:** How do I scale an OCI cluster?

**Answer:** Similar to OLVM, use `kubectl scale`:

For workers:
```bash
kubectl scale machinedeployment <name> --replicas 5 --namespace <namespace>
```

For control plane:
```bash
kubectl scale kubeadmcontrolplane <name> --replicas 3 --namespace <namespace>
```

### Q33
**Question:** How do I upgrade an OCI cluster to a new Kubernetes version?

**Answer:** In-place upgrade using `ocne node update`:
1. Create and upload new OCK image for new K8s version
2. Run `ocne cluster stage --version 1.33`
3. Update control plane nodes: `ocne node update --node <control-plane-node>`
4. Verify each control plane node before updating next
5. Update worker nodes: `ocne node update --node <worker-node>`
6. Verify with `kubectl get nodes`

## Bring Your Own Provider

### Q34
**Question:** What is an OSTree archive image and when is it used?

**Answer:** An OSTree archive image is the OCK image converted to OSTree archive format and served over HTTP. It's required for BYO deployments because Anaconda needs OSTree content in this specific format to install onto the host's root filesystem. Create with:
```bash
ocne image create --type ostree --arch amd64
```

### Q35
**Question:** Where can I serve the OSTree archive image?

**Answer:** Copy to any target supporting Open Container Initiative transports:
```bash
ocne image upload --type ostree --file <path> --destination docker://myregistry.example.com/ock-ostree:latest --arch amd64
```
Or use Podman to serve locally:
```bash
ocne image upload --type ostree --file <path> --destination dir:ock-ostree --arch amd64
```

### Q36
**Question:** What network interface configuration is required for BYO provider?

**Answer:** The `networkInterface` option is mandatory for BYO provider:
```yaml
providers:
  byo:
    networkInterface: enp1s0
```
This sets the interface to which CNI and Kubernetes services bind.

### Q37
**Question:** What components are needed for a BYO installation?

**Answer:** BYO installations require:
- OCK OSTree image (in container registry or Podman)
- Oracle Linux ISO (for kernel and initrd)
- Ignition file (generated by CLI, served via Ignition server)
- Kickstart file (references OSTree image and Ignition file, served via Kickstart server)
- Load balancer (internal or external) for control plane HA
- Ephemeral cluster for generating materials

### Q38
**Question:** How do I generate Ignition files for BYO clusters?

**Answer:** For a new cluster:
```bash
ocne cluster start --provider byo > cluster.ign
```

To join worker nodes:
```bash
ocne cluster join --provider byo --kubeconfig <path> > worker.ign
```

To join control plane nodes:
```bash
ocne cluster join --provider byo --kubeconfig <path> --role-control-plane > control.ign
```

### Q39
**Question:** How do I migrate nodes between BYO clusters?

**Answer:** Use `ocne cluster join` to migrate preprovisioned nodes:
```bash
ocne cluster join --kubeconfig <source> --provider byo --node <node-name> --destination <target-kubeconfig>
```
Add `--role-control-plane` to migrate as a control plane node instead of worker.

## UI Management

### Q40
**Question:** How do I add the UI to an existing cluster that doesn't have it?

**Answer:** Use `ocne cluster start` with the `none` provider:
```bash
ocne cluster start --provider none --kubeconfig $HOME/.kube/kubeconfig.mycluster
```
This installs the UI and application catalog into the existing cluster.

### Q41
**Question:** How do I expose the UI using port forwarding?

**Answer:** Set up port forwarding (for development only, not production):
```bash
kubectl port-forward --namespace ocne-system service/ui 8443:443
```
Keep the command running and access at https://127.0.0.1:8443. Use an access token for authentication:
```bash
kubectl --namespace ocne-system create token ui
```

## Cluster Updates

### Q42
**Question:** What are the best practices for cluster updates?

**Answer:** Follow these practices:
- Always back up etcd before updates
- Update control plane nodes first, sequentially
- Wait for each control plane node to be ready before updating next
- Update worker nodes after all control plane nodes
- Don't update multiple nodes simultaneously
- Verify cluster health between updates
- Use `ocne cluster info` to check update availability

### Q43
**Question:** What's the difference between patch updates and minor updates?

**Answer:** **Patch updates** include errata, CVE fixes, and patch-level Kubernetes updates. They're downloaded automatically to nodes and applied with `ocne node update`.

**Minor updates** upgrade to the next Kubernetes minor version (e.g., 1.32 to 1.33). They require:
1. Creating new OCK image with target version
2. Staging the update with `ocne cluster stage --version 1.33`
3. Updating nodes with `ocne node update`

### Q44
**Question:** How do patch updates get downloaded?

**Answer:** Each node periodically polls the container registry to check for updates to its OCK image. Patch updates are downloaded automatically to each node and don't need manual staging. Updates are applied when you run `ocne node update`.

### Q45
**Question:** How do I install a Kubernetes patch release?

**Answer:** Process:
1. Check for updates: `ocne cluster info`
2. Verify updates are available and staged
3. Update control plane nodes first: `ocne node update --node <control-plane-node>`
4. Wait for node to return to Ready state
5. Update remaining control plane nodes sequentially
6. Update worker nodes: `ocne node update --node <worker-node>`

### Q46
**Question:** What does `ocne cluster stage` do?

**Answer:** `ocne cluster stage` sets the target Kubernetes version for the cluster and all nodes:
```bash
ocne cluster stage --version 1.33
```
Nodes are then configured to poll the registry and pull/stage the OCK image for that version. After staging completes, use `ocne node update` to install.

### Q47
**Question:** What happens during `ocne node update`?

**Answer:** The command:
1. Drains the node (evicts pods using `kubectl drain`)
2. Installs the staged OCK image on the node
3. Reboots the node
4. Returns the node to the cluster (using `kubectl uncordon`)
5. Makes the node available to run pods

### Q48
**Question:** Can I update an HA cluster without downtime?

**Answer:** Yes, for HA clusters with multiple control plane nodes. As one control plane node goes offline, another takes control. Applications running on multiple worker nodes remain available during updates. Single control plane clusters have brief control plane downtime during updates.

## Cluster Backups

### Q49
**Question:** What does `ocne cluster backup` back up?

**Answer:** The command backs up the etcd database containing cluster state, plus key containers and manifests for all control plane nodes. Application containers are NOT backed up. Usage:
```bash
ocne cluster backup --out mybackup.db
```
The backup is in etcd database format.

### Q50
**Question:** Why are cluster backups important?

**Answer:** Backups protect against control plane node failures, especially for single control plane clusters. Even HA clusters need fallback plans if resilience is exceeded. The etcd database maintains all cluster state shared between Kubernetes API Server instances. Regular backups are critical for disaster recovery.

### Q51
**Question:** What security considerations apply to cluster backups?

**Answer:** Backups contain sensitive data including Kubernetes Secret objects. You must:
- Store backups in a secure location
- Implement integrity safeguards
- Protect backup storage with appropriate access controls
- Consider encryption for backup storage

### Q52
**Question:** Do I need to shut down the cluster to back it up?

**Answer:** No, you don't need to bring down the cluster to perform a backup as part of disaster recovery. The `ocne cluster backup` command can run on a live cluster.

## Cluster Analysis & Console

### Q53
**Question:** How do I create a cluster dump?

**Answer:** Use `ocne cluster dump`:
```bash
ocne cluster dump --output-directory $HOME/dump
```
Or create an archive:
```bash
ocne cluster dump --generate-archive $HOME/cluster_dump.tgz
```
By default, includes all resources except Secrets and ConfigMaps.

### Q54
**Question:** How do I include ConfigMaps in a cluster dump?

**Answer:** Use the `--include-configmaps` option:
```bash
ocne cluster dump --output-directory $HOME/dump --include-configmaps
```
This option is not valid when using `--curated-resources`.

### Q55
**Question:** How do I dump only specific namespaces?

**Answer:** Use the `--namespaces` option with a comma-separated list:
```bash
ocne cluster dump --output-directory $HOME/dump --namespaces kube-system,default,ocne-system
```

### Q56
**Question:** How do I analyze a cluster dump?

**Answer:** Use `ocne cluster analyze` with the dump directory:
```bash
ocne cluster analyze --dump-directory $HOME/dump/
```
For more detail:
```bash
ocne cluster analyze --dump-directory $HOME/dump/ --verbose
```

### Q57
**Question:** How do I access a node's OS console?

**Answer:** Use `ocne cluster console`:
```bash
ocne cluster console --node <nodename>
```
The console provides chrooted access to the node's OS for debugging. The node name must match output from `kubectl get nodes`.

### Q58
**Question:** What debugging tools are available in the console?

**Answer:** Start the console with `--toolbox` to include additional tools:
```bash
ocne cluster console --node <nodename> --toolbox
```
This adds tools like strace, tcpdump, traceroute, and sos useful for system diagnosis.

### Q59
**Question:** How do I run a command on a node without interactive console?

**Answer:** Use the `--` option:
```bash
ocne cluster console --direct --node <nodename> -- ls /proc
```
The connection closes after the command completes. The `--direct` option starts chrooted to the node's filesystem.

### Q60
**Question:** How do I access node services like `ocne-update.service`?

**Answer:** Either chroot manually in the console:
```bash
chroot /hostroot
```
Or start the console already chrooted:
```bash
ocne cluster console --direct --node <nodename>
```

## Advanced Topics

### Q61
**Question:** What is a management cluster?

**Answer:** A management cluster is a Kubernetes cluster that controls the lifecycle of other clusters (workload clusters). It runs the Kubernetes Cluster API controllers. Any running cluster can be used as a management cluster. If none is specified, an ephemeral cluster is created automatically.

### Q62
**Question:** What is a self-managed cluster?

**Answer:** A self-managed cluster is a workload cluster that also acts as its own management cluster. After the workload cluster is deployed, Cluster API resources are migrated from the management/ephemeral cluster into the workload cluster itself.

### Q63
**Question:** How do I specify which cluster to use as the management cluster?

**Answer:** Set using:
- `KUBECONFIG` environment variable
- `--kubeconfig` option with `ocne` commands
- `kubeconfig` option in configuration file

If not set, an ephemeral cluster is created using libvirt with default config.

### Q64
**Question:** What happens to the ephemeral cluster after deployment?

**Answer:** By default, ephemeral clusters are automatically deleted after the work is complete. To preserve for debugging:
```yaml
ephemeralCluster:
  preserve: true
```

### Q65
**Question:** How do I customize the ephemeral cluster?

**Answer:** Use the `ephemeralCluster` option:
```yaml
ephemeralCluster:
  name: mycustom-ephemeral
  preserve: true
  node:
    cpus: 2
    memory: 4GB
    storage: 20GB
```

### Q66
**Question:** Can I use IPv6 with Oracle CNE clusters?

**Answer:** The OLVM provider supports IPv4 only or dual stack (IPv4 + IPv6). IPv6 alone cannot be used. Other providers may have different IPv6 support.

### Q67
**Question:** How do I set extra Ignition configuration?

**Answer:** Use `extraIgnition` or `extraIgnitionInline`:
```yaml
extraIgnition: /home/username/.ocne/ignition.ign
```
Or inline:
```yaml
extraIgnitionInline: |
  variant: fcos
  version: 1.5.0
  storage:
    files:
      - path: /etc/myconfig
        contents:
          inline: "config data"
```
Must comply with Ignition spec v3.4.0 in Butane FCOS spec v1.5.0 format.

### Q68
**Question:** What CRDs does the OLVM provider implement?

**Answer:** The OLVM provider implements two Cluster API controllers:
- `OLVMCluster` - Infrastructure Cluster controller CRD
- `OLVMMachine` - Infrastructure Machine controller CRD

Each cluster needs one OLVMCluster CR and OLVMMachine CRs for control plane and worker nodes.

### Q69
**Question:** What CRDs are used for scaling clusters?

**Answer:** For scaling:
- `MachineDeployment` - Controls worker node replicas
- `KubeadmControlPlane` - Controls control plane node replicas

Use `kubectl scale` on these resources to add/remove nodes.

### Q70
**Question:** How do I monitor Cluster API operations?

**Answer:** Check key pods in the management cluster:
```bash
kubectl logs -n capi-system core-capi-controller-manager-<pod>
kubectl logs -n capi-kubeadm-control-plane-system control-plane-capi-controller-manager-<pod>
kubectl logs -n capi-kubeadm-bootstrap-system bootstrap-capi-controller-manager-<pod>
```
For provider-specific: `cluster-api-provider-oci` or `cluster-api-provider-olvm` namespaces.

## Troubleshooting

### Q71
**Question:** Where are OCK images stored after creation?

**Answer:** Created images are stored in `$HOME/.ocne/images/` directory on the localhost. The filename indicates the type, version, and architecture (e.g., `boot.qcow2-1.33-amd64.oci`).

### Q72
**Question:** How do I verify KVM virtualization is working?

**Answer:** Use `virt-host-validate`:
```bash
virt-host-validate qemu
```
This validates the host is set up for hardware virtualization and can be used as a KVM host.

### Q73
**Question:** Why am I getting "disk full" errors during image creation?

**Answer:** Image conversion requires significant space (at least 20GB). Increase storage for ephemeral and libvirt clusters in your config:
```yaml
ephemeralCluster:
  node:
    storage: 20G
providers:
  libvirt:
    controlPlaneNode:
      storage: 20G
    workerNode:
      storage: 20G
```

### Q74
**Question:** How do I check if a node update is available?

**Answer:** Use `ocne cluster info`:
```bash
ocne cluster info
```
This displays cluster information and whether updated OCK images are staged and ready to install on nodes.

### Q75
**Question:** What should I do if a node update fails?

**Answer:** The update process includes draining (which can fail if pods can't be evicted). Use options with `ocne node update`:
- `--delete-emptydir-data` - Delete pods using emptyDir during drain
- `--disable-eviction` - Force pod deletion, bypassing PodDisruptionBudget
- `--timeout <minutes>` - Increase timeout (default 30 minutes)

### Q76
**Question:** How do I check cluster deletion progress?

**Answer:** Monitor in a separate terminal with kubeconfig set to management cluster:
```bash
export KUBECONFIG=$(ocne cluster show --cluster-name <mgmt-cluster>)
kubectl get cluster -A
```
The cluster object shows `deleting` state. When it's gone, deletion is complete.

### Q77
**Question:** What if I can't access the node console?

**Answer:** The `ocne cluster console` command is the primary method. Only use SSH or serial console when the node can't be accessed via console command. SSH credentials are documented per cluster type in the provider documentation.

### Q78
**Question:** How do I view Machine objects for debugging?

**Answer:** In the management cluster:
```bash
kubectl get machine --namespace <namespace>
kubectl describe machine --namespace <namespace> <machine-name>
```
Check the `PHASE` column shows `Running`. Use `describe` for detailed status and events.

### Q79
**Question:** How do I skip the preupdate process?

**Answer:** Use `--pre-update-mode` with `ocne node update`:
- `default` - Run preupdate and update (default)
- `only` - Run preupdate but skip updating nodes
- `skip` - Skip preupdate entirely

Example:
```bash
ocne node update --node <nodename> --pre-update-mode skip
```

### Q80
**Question:** What should I check if cluster creation hangs?

**Answer:** Check:
1. Management/ephemeral