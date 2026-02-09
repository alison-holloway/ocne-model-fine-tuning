# Oracle CNE Training Dataset - Quick Start Guide

## Installation & Setup

### Q1
**Question:** How do I install the Oracle CNE CLI?

**Answer:** You can install the Oracle CNE CLI using either the Oracle Linux Yum Server or the Unbreakable Linux Network (ULN).

**Using Oracle Linux Yum Server:**

Oracle Linux 9:
```bash
sudo dnf install -y oracle-ocne-release-el9
sudo dnf config-manager --enable ol9_ocne
sudo dnf install -y ocne
```

Oracle Linux 8:
```bash
sudo dnf install -y oracle-ocne-release-el8
sudo dnf config-manager --enable ol8_ocne
sudo dnf install -y ocne
```

**Using ULN:**

For systems registered with ULN, use the ULN web interface to subscribe to the appropriate channel:
- Oracle Linux 9: Subscribe to ol9_x86_64_ocne or ol9_aarch64_ocne
- Oracle Linux 8: Subscribe to ol8_x86_64_ocne or ol8_aarch64_ocne

Then install the CLI:
```bash
sudo dnf install -y ocne
```

### Q2
**Question:** What are the ULN channel subscription requirements for installing Oracle CNE CLI?

**Answer:** For systems registered with the Unbreakable Linux Network (ULN), you need to subscribe to the appropriate Oracle CNE channel using the ULN web interface based on your Oracle Linux version and architecture:

**Oracle Linux 9:**
- x86_64 architecture: Subscribe to ol9_x86_64_ocne
- aarch64 (ARM) architecture: Subscribe to ol9_aarch64_ocne

**Oracle Linux 8:**
- x86_64 architecture: Subscribe to ol8_x86_64_ocne
- aarch64 (ARM) architecture: Subscribe to ol8_aarch64_ocne

After subscribing to the appropriate channel, install the CLI:
```bash
sudo dnf install -y ocne
```



## libvirt Provider Setup

### Q4
**Question:** What's the recommended KVM stack for Oracle CNE and what are the UEK requirements?

**Answer:** Oracle recommends using the Oracle KVM stack, which is available in Oracle Linux 8 or 9 with the Unbreakable Enterprise Kernel (UEK). For Oracle Linux 9, you must have UEK Release 7 (UEK R7) installed. For Oracle Linux 8, either UEK R6 or UEK R7 is required.

### Q5
**Question:** How do I install the Oracle KVM stack?

**Answer:** The installation process differs between Oracle Linux versions.

**Oracle Linux 9:**

First remove any existing default KVM stack, then install the Oracle KVM stack and start the virtualization daemons:
```bash
sudo dnf remove -y libvirt qemu-kvm edk2
sudo dnf config-manager --enable ol9_kvm_utils
sudo dnf group install -y "Virtualization Host"
sudo dnf install -y virt-install virt-viewer

for drv in qemu network nodedev nwfilter secret storage interface proxy; do
  sudo systemctl enable virt${drv}d.service
  sudo systemctl enable virt${drv}d{,-ro,-admin}.socket
  sudo systemctl start virt${drv}d{,-ro,-admin}.socket
done
```

**Oracle Linux 8:**

Remove the existing default KVM stack, then install and enable the Oracle KVM stack:
```bash
sudo dnf module remove -y virt --all
sudo dnf module reset virt
sudo dnf config-manager --enable ol8_kvm_appstream
sudo dnf module enable virt:kvm_utils3
sudo dnf module install -y virt:kvm_utils3
sudo systemctl enable --now libvirtd.service
```



### Q7
**Question:** How do I validate that my host is properly set up for KVM virtualization in Oracle CNE?

**Answer:** Use the virt-host-validate command to verify hardware virtualization support:
```bash
virt-host-validate qemu
```

### Q8
**Question:** What user configuration is required to use libvirt with Oracle CNE?

**Answer:** The user needs privileged access to libvirt. Add the user to the libvirt and qemu groups:
```bash
sudo usermod -a -G libvirt,qemu $USER
```
After running this command, log out and log back in to enable the change.

### Q9
**Question:** When do I need to open firewall ports for libvirt clusters, and how do I do it?

**Answer:** You only need to open firewall ports if installing libvirt on a remote host to access cluster nodes from localhost. Open a range starting from port 6443:
```bash
sudo firewall-cmd --add-port 6443-6463/tcp
sudo firewall-cmd --add-port 6443-6463/tcp --permanent
sudo systemctl restart firewalld.service
```
Replace *`6463`* with your desired end range (for example, opening 20 ports for a larger cluster).

### Q10
**Question:** Can I change KVM stacks if I already have existing Virtual Machines?

**Answer:** Existing Virtual Machines created with one KVM stack might not be compatible and might not start after switching to another KVM stack. You should be aware of this before migrating between the default KVM stack and the Oracle KVM stack.

## Cluster Creation

### Q11
**Question:** What is the libvirt provider and when should I use it?

**Answer:** The libvirt provider creates virtualized Kubernetes clusters on a single host using KVM. It's the default cluster provider and the fastest method to create clusters with Oracle CNE. It's useful for testing and development, though it can deploy production-worthy cluster configurations. The key limitation is that all cluster nodes run on a single host, so if the host goes down, all cluster nodes are affected.

### Q12
**Question:** What's the basic command to create a default libvirt cluster?

**Answer:** To create a libvirt cluster using all default settings:
```bash
ocne cluster start
```
This creates a single-node cluster on the localhost.

### Q13
**Question:** How do I create a libvirt cluster with a specific number of control plane and worker nodes?

**Answer:** Use the `--control-plane-nodes` and `--worker-nodes` options:
```bash
ocne cluster start --control-plane-nodes 3 --worker-nodes 5
```

### Q14
**Question:** How do I create a libvirt cluster with a virtual IP address?

**Answer:** Use the `--virtual-ip` option to specify the virtual IP:
```bash
ocne cluster start --control-plane-nodes 3 --worker-nodes 5 --virtual-ip 192.168.0.100
```

### Q15
**Question:** How do I create a libvirt cluster using a configuration file?

**Answer:** Use the `--config` option to specify a cluster configuration file:
```bash
ocne cluster start --config myconfig.yaml
```

### Q16
**Question:** What's an example cluster configuration file for libvirt?

**Answer:** A cluster configuration file contains cluster-specific settings. Example:
```yaml
provider: libvirt
name: mycluster
workerNodes: 2
controlPlaneNodes: 1
providers:
  libvirt:
    controlPlaneNode:
      cpu: 2
      memory: 8Gi
      storage: 20Gi
    workerNode:
      cpu: 2
      memory: 8Gi
      storage: 20Gi
```
The `provider` field specifies the cluster provider, `name` sets the cluster name, `workerNodes` and `controlPlaneNodes` define the number of each node type, and the `providers.libvirt` section configures resource allocations for `controlPlaneNode` and `workerNode`.

### Q17
**Question:** How do I create a cluster on a remote libvirt host?

**Answer:** Use the `--session` option with the qemu+ssh URI format:
```bash
ocne cluster start --session qemu+ssh://myuser@myhost.example.com/system --config myconfig.yaml
```
Replace *`myuser`* and *`myhost.example.com`* with your actual username and remote host.

### Q18
**Question:** What's the full syntax for the `ocne cluster start` command?

**Answer:** The complete syntax for `ocne cluster start` is:
```bash
ocne cluster start \
  [{-u|--auto-start-ui} {true|false}] \
  [{-o|--boot-volume-container-image} URI] \
  [{-C|--cluster-name} name] \
  [{-c|--config} path] \
  [{-n|--control-plane-nodes} integer] \
  [{-i|--key} path] \
  [--load-balancer address] \
  [{-P|--provider} provider] \
  [{-s|--session} URI] \
  [{-v|--version} version] \
  [--virtual-ip IP] \
  [{-w|--worker-nodes} integer]
```

## Connecting to Clusters

### Q19
**Question:** What kubeconfig files are created after creating a libvirt cluster?

**Answer:** Two kubeconfig files are created:
1. `$HOME/.kube/kubeconfig.<cluster_name>.local` - Provides direct access to the Kubernetes API server endpoint. Can be used for localhost or remote libvirt clusters.
2. `$HOME/.kube/kubeconfig.<cluster_name>.vm` - Provides access through a dedicated SLiRP tunnel for remote systems.

Replace `<cluster_name>` with the name you used when creating the cluster.

### Q20
**Question:** How do I connect to a cluster running on localhost?

**Answer:** Install `kubectl` and set the KUBECONFIG environment variable using `ocne cluster show`:
```bash
sudo dnf install kubectl
export KUBECONFIG=$(ocne cluster show --cluster-name cluster-name)
```
Then verify the connection:
```bash
kubectl get deployments --all-namespaces
```

### Q21
**Question:** How do I access a cluster created on a remote system from that remote system?

**Answer:** Copy the kubeconfig file ending in `.vm` from the localhost to the remote system. The file is located at `$HOME/.kube/kubeconfig.<cluster_name>.vm` on localhost (replace `<cluster_name>` with your actual cluster name). If you copy it to `$HOME/.kube/config` on the remote system, you won't need to set the `KUBECONFIG` environment variable.

### Q22
**Question:** How do I persist the KUBECONFIG environment variable?

**Answer:** Add it to your `.bashrc` file:
```bash
echo 'export KUBECONFIG=$(ocne cluster show --cluster-name <cluster-name>)' >> $HOME/.bashrc
```
Replace `<cluster-name>` with your actual cluster name.

### Q23
**Question:** What's the default cluster name if I don't specify one?

**Answer:** The default cluster name is "ocne".

## UI Access & Authentication

### Q24
**Question:** How do I create an access token to authenticate with the Oracle CNE UI?

**Answer:** The UI service runs in the ocne-system namespace. Create a token using:
```bash
kubectl --namespace ocne-system create token ui
```
Save this token securely as you'll need it to authenticate when accessing the UI.

### Q25
**Question:** How do I expose the UI using port forwarding for development?

**Answer:** Set up port forwarding to expose the UI service:
```bash
kubectl port-forward --namespace ocne-system service/ui 8443:443
```
Keep this command running while you need UI access. Access the UI at https://127.0.0.1:8443

### Q26
**Question:** Is port forwarding recommended for production UI access?

**Answer:** No, port forwarding is not recommended for production environments. It's convenient for debugging and troubleshooting in development environments only.

### Q27
**Question:** How can I access the UI on localhost from a remote machine?

**Answer:** Use SSH local port forwarding from the remote machine:
```bash
ssh -L 9898:127.0.0.1:8443 myuser@myhost.example.com
```
This enables incoming connections to localhost on port 9898 from the remote machine. Replace *`myuser`* and *`myhost.example.com`* with your actual username and hostname.

### Q28
**Question:** What namespace does the Oracle CNE UI run in?

**Answer:** The UI runs as a Kubernetes deployment and service, both named *`ui`*, in the *`ocne-system`* namespace.

## Application Management

### Q29
**Question:** How do I search for all applications in the Oracle catalog using the CLI?

**Answer:** Use the `ocne catalog search` command:
```bash
ocne catalog search
```

### Q30
**Question:** How do I search for applications in the embedded Oracle catalog?

**Answer:** Use the `--name` option to specify the embedded catalog:
```bash
ocne catalog search --name embedded
```

### Q31
**Question:** How do I search for applications matching a specific pattern?

**Answer:** Use the `--pattern` option with a search string:
```bash
ocne catalog search --pattern 'ingress-*'
```

### Q32
**Question:** How do I install an application from the default catalog using the CLI?

**Answer:** Use the `ocne application install` command with the required parameters:
```bash
ocne application install --release ingress-nginx --namespace ingress-nginx --name ingress-nginx
```

### Q33
**Question:** What's the full syntax for the `ocne application install` command?

**Answer:** The complete syntax for `ocne application install` is:
```bash
ocne application install \
  {-b|--built-in-catalog} \
  [{-c|--catalog} name] \
  {-N|--name} name \
  [{-n|--namespace} namespace] \
  {-r|--release} name \
  [{-u|--values} URI] \
  [{-v|--version} version]
```

### Q34
**Question:** How do I search for applications using the UI?

**Answer:** In the navigation menu, select Apps. The Applications page displays all available applications in the default catalog. Use the Search field to filter applications by entering characters - only applications whose names contain those characters will be displayed.

### Q35
**Question:** How do I install an application using the UI?

**Answer:** In the navigation menu, select Apps, use the Search field to find your application, then select Install. A dialog appears with a YAML configuration editor and mandatory fields (Release Name, Namespaces, Versions, Release Description). Edit the YAML as needed and select Install. You'll receive confirmation messages when the installation request is accepted and when the release is created successfully.

## Architecture & Concepts

### Q36
**Question:** What virtualization technology does the libvirt provider use?

**Answer:** The libvirt provider uses Kernel-based Virtual Machines (KVM) with the default KVM stack that includes libvirt, which is included by default with Oracle Linux.

### Q37
**Question:** What happens if the host running a libvirt cluster goes down?

**Answer:** Since all libvirt cluster nodes run on a single host, if that host goes down, all the cluster nodes are affected and become unavailable. This is an important consideration when using libvirt clusters.

### Q38
**Question:** Is the libvirt provider suitable for production?

**Answer:** The libvirt provider can deploy production-worthy cluster configurations, but it's primarily useful for testing and development. The single-host limitation means it lacks the high availability characteristics typical of production deployments.

### Q39
**Question:** What does the Oracle CNE CLI do?

**Answer:** The Oracle CNE CLI (`ocne` command) is the command-line tool used to create and manage Kubernetes clusters in Oracle CNE. It includes a help system to show all command options and uses configuration files at various levels to configure environments and clusters.

### Q40
**Question:** What's included in a basic Oracle CNE Quick Start setup?

**Answer:** A Quick Start setup includes:
1. Installing the CLI on an Oracle Linux host (8 or 9)
2. Setting up KVM on the host
3. Creating a Kubernetes cluster using the libvirt provider
4. Generating a Kubernetes access token for the UI
5. Exposing the UI using port forwarding
6. Installing applications from the default catalog

## Troubleshooting & Validation

### Q41
**Question:** How do I verify my cluster connection is working?

**Answer:** Use `kubectl` to query the cluster:
```bash
kubectl get deployments --all-namespaces
```
If this returns deployment information, your connection is working correctly.

### Q42
**Question:** Where can I find information about other cluster providers besides libvirt?

**Answer:** Information on other providers is available in the Oracle Cloud Native Environment: Kubernetes Clusters documentation. The Quick Start focuses on libvirt, which is the fastest method to create clusters.

### Q43
**Question:** What's the difference between using command options vs a configuration file for cluster creation?

**Answer:** You can customize cluster creation either by using command-line options with `ocne cluster start` (like `--control-plane-nodes`, `--worker-nodes`, `--virtual-ip`) or by creating a cluster configuration file and using `--config`. Configuration files are better for complex setups or when you want to version control your cluster definitions.

### Q44
**Question:** Can I customize node resources in a libvirt cluster?

**Answer:** Yes, use a cluster configuration file to specify CPU, memory, and storage for control plane and worker nodes. For example, you can set different resources for `controlPlaneNode` and `workerNode` under the `providers.libvirt` section.

### Q45
**Question:** What authentication method does the UI use?

**Answer:** The UI uses Kubernetes access tokens for authentication. You create a token using kubectl and enter it in the ID token field on the Security page when accessing the UI.

## Additional Technical Details

### Q46
**Question:** What system architectures are supported for Oracle CNE on ULN?

**Answer:** Oracle CNE supports both x86_64 and aarch64 (ARM) architectures on Oracle Linux 8 and 9, with separate ULN channels for each: ol8_x86_64_ocne, ol8_aarch64_ocne, ol9_x86_64_ocne, and ol9_aarch64_ocne.

### Q47
**Question:** What happens when I run `ocne cluster start` without any options?

**Answer:** Running `ocne cluster start` without options creates a default single-node cluster on localhost using the libvirt provider with all default settings. The UI is deployed by default.

### Q48
**Question:** How does the session URI format work for remote clusters?

**Answer:** The session URI uses the format `qemu+ssh://`*`user`*`@`*`host`*`/system` where *`user`* is your SSH username and *`host`* is the hostname or IP address of the remote system. For example: `qemu+ssh://myuser@myhost.example.com/system`

### Q49
**Question:** What's the default port for the Kubernetes API server in libvirt clusters?

**Answer:** Based on the firewall configuration examples, the Kubernetes API server uses port 6443 by default, which is the standard Kubernetes API server port.

### Q50
**Question:** Is the UI automatically installed in Oracle CNE clusters?

**Answer:** Yes, the UI is deployed by default in the cluster as a Kubernetes deployment in the ocne-system namespace. You can control this with the `--auto-start-ui` option when creating clusters.
