# Oracle CNE Training Dataset - Concepts Guide

## Introduction & Overview

### Q1
**Question:** What is Oracle Cloud Native Environment?

**Answer:** Oracle Cloud Native Environment (Oracle CNE) is a fully integrated suite for the development and management of cloud native applications. It delivers a simplified framework for installations, updates, upgrades, and configuration of key features for orchestrating microservices. Oracle CNE uses Kubernetes to deploy and manage containers, automatically installing and configuring Kubernetes, CRI-O, runC, and Kata Containers on Kubernetes nodes.

### Q2
**Question:** What are the main components of Oracle CNE?

**Answer:** The main components of Oracle CNE are:
- Oracle CNE Command Line Interface (`ocne` CLI)
- Oracle CNE User Interface (UI)
- Oracle CNE application catalog
- Oracle Container Host for Kubernetes (OCK) images
- OCK Image Builder

## CLI Architecture & Components

### Q3
**Question:** What is the Oracle CNE CLI and what is it used for?

**Answer:** The Oracle CNE CLI is the command line tool (`ocne` command) used to create and manage Kubernetes clusters using available cluster providers. It's installed on Oracle Linux 8 or 9 and includes built-in default configuration for creating basic Kubernetes clusters, or can use configuration files to customize cluster deployments with specific parameters and options.

### Q4
**Question:** What are the key components in the CLI architecture?

**Answer:** The CLI architecture includes:
- CLI (`ocne` command) for creating and managing clusters
- Default configuration (YAML file for all `ocne` commands)
- Cluster configuration (YAML file for specific clusters)
- Cluster API template (YAML file with Cluster Resources for Kubernetes Cluster API)
- Container registry (for pulling OCK images, defaults to Oracle Container Registry)
- OCK image (used to create Kubernetes nodes)
- Control plane load balancer (for HA of control plane nodes)
- Control plane nodes
- Worker nodes

### Q5
**Question:** Can I use Kubernetes Cluster API templates?

**Answer:** When a cluster provider type uses the Kubernetes Cluster API, the CLI can use Cluster API templates to define clusters to finer specifications. These templates are used when a configuration option isn't available in a cluster configuration file but is available in the Cluster API provider.

## User Interface

### Q6
**Question:** What does the Oracle CNE UI provide?

**Answer:** The Oracle CNE UI provides a web-based interface to manage the maintenance and installation of Kubernetes cluster resources and applications. It runs in the Kubernetes cluster as a deployment named `ui` in the `ocne-system` namespace.

### Q7
**Question:** What is the UI based on?

**Answer:** The UI is based on the open source Kubernetes UI Headlamp application. For more information, you can refer to the upstream Headlamp documentation.

### Q8
**Question:** Where is the UI deployed to?

**Answer:** A deployment named `ocne-catalog` runs in the `ocne-system` namespace to serve the application catalog for the UI.

## Application Catalogs

### Q9
**Question:** What is an application catalog?

**Answer:** An application catalog is a searchable collection of software that can be installed into a Kubernetes cluster. Installed catalogs can be searched using both the Oracle CNE CLI and the UI. Catalogs can be added and removed, but not changed.

### Q10
**Question:** What types of application catalogs can I use?

**Answer:** There are two types of application catalogs, set up in two different flavors:

**Catalog types:**
1. Oracle catalog - A collection of cloud native application software provided by Oracle
2. External community catalog - External catalogs compatible with Artifact Hub

**Catalog flavors:**
1. Helm repository - The Oracle catalog is a Helm repository containing an `index.yaml` file and a set of tarballs
2. Service compatible with Artifact Hub - External catalogs typically point to artifacthub.io and are compatible with the Artifact Hub API

### Q12
**Question:** How can the Oracle catalog be accessed?

**Answer:** The Oracle catalog can be accessed in two ways:
1. Using the embedded version in the CLI (named `embedded`) which can be accessed without deploying a Kubernetes cluster
2. From the `ocne-catalog` application deployed to a Kubernetes cluster in the `ocne-system` namespace

### Q13
**Question:** How is the embedded Oracle catalog updated?

**Answer:** The embedded Oracle catalog is updated when you update the CLI. The Oracle catalog running as an application in the cluster can be updated using the `ocne application update` command. This means the catalog contents might differ between the embedded and deployed versions.

### Q14
**Question:** What is the deployed Oracle catalog composed of?

**Answer:** The deployed Oracle catalog includes a Helm repository and an instance of NGINX that serves the static content. The `ocne-catalog` application is deployed from the Oracle Container Registry to the cluster.

### Q15
**Question:** How are external catalogs added and what are they?

**Answer:** External catalogs are added using the `ocne catalog add` CLI command. They're added using a Kubernetes external service resource - the catalog isn't installed in the cluster but is referenced. The catalog data isn't served from the cluster. An example is the Artifact Hub catalog at https://artifacthub.io/.

## Oracle Container Host for Kubernetes Image

### Q16
**Question:** What is the Oracle Container Host for Kubernetes (OCK) image?

**Answer:** The OCK image is an OSTree-based container image that includes both the host Oracle Linux OS and the Kubernetes software distribution. It's deployed to hosts or Virtual Machines to create nodes in a Kubernetes cluster. The CLI manages the lifecycle of Kubernetes clusters using these OSTree-based container images.

### Q17
**Question:** What formats is the OCK image distributed in?

**Answer:** The OCK image is distributed in two formats on the Oracle Container Registry:
1. **Bootable image** (Qcow2 format) at `container-registry.oracle.com/olcne/ock` - Used to create boot media for virtualized platforms (libvirt, OCI, and Oracle Linux Virtualization Manager providers)
2. **OSTree image** at `container-registry.oracle.com/olcne/ock-ostree` - Used for customized installations with the Bring Your Own provider and for updating cluster nodes

### Q18
**Question:** How does the bootable OCK image work with different providers?

**Answer:** The bootable image is configured by default to work with the libvirt provider. When uploading the image for use with OCI or Oracle Linux Virtualization Manager, the CLI performs a conversion of the boot image to the appropriate format for those platforms.

### Q19
**Question:** What is the OSTree OCK image used for?

**Answer:** The OSTree OCK image is used as the basis for an OSTree archive for customized installations using the Bring Your Own provider. It's also used for updating cluster nodes to stage patch updates and to update to the next Kubernetes minor release.

### Q20
**Question:** How are OCK image versions labeled?

**Answer:** OCK images use the container label for the Kubernetes version they match. For example, an image labeled `1.33` matches Kubernetes Release 1.33.

## Configuration Files

### Q21
**Question:** How are Kubernetes clusters and applications configured in Oracle CNE?

**Answer:** Clusters and applications are configured through a layered set of YAML configuration files and `ocne` command line arguments. Each layer takes precedence over the previous layer, providing convenient reuse of parameters that would otherwise be duplicated.

### Q22
**Question:** What are the three hierarchical configuration methods for ocne subcommands?

**Answer:** The three hierarchical methods (in precedence order) are:
1. Global defaults in the default configuration file (`$HOME/.ocne/defaults.yaml`)
2. Kubernetes cluster configuration files (can be any name)
3. Options provided with the `ocne` command

Each level can override the previous level.

## Kubernetes Cluster API Templates

### Q23
**Question:** What are Kubernetes Cluster API templates used for?

**Answer:** Cluster API templates are used when cluster providers use the Kubernetes Cluster API for provisioning and managing clusters. They allow extra customization beyond default cluster settings. Templates are YAML files containing Cluster Resources for the Kubernetes Cluster API to create a cluster.

### Q24
**Question:** How do you create a Cluster API template?

**Answer:** Use the `ocne cluster template` command to create a cluster template. The command uses the default configuration and any cluster configuration you've set to generate the template. For providers like OCI, it may also automatically fetch information such as compute image OCIDs from the configured compartment. The resulting template can be included in a cluster configuration file.

## Cluster Providers Overview

### Q25
**Question:** What cluster providers are available in Oracle CNE?

**Answer:** Oracle CNE can create Kubernetes clusters on:
- Kernel-based Virtual Machines (KVM) using the `libvirt` provider
- Oracle Linux Virtualization Manager using the `olvm` provider
- Oracle Cloud Infrastructure (OCI) using the `oci` provider
- Custom installations for bare metal or other platforms using the `byo` (Bring Your Own) provider

### Q26
**Question:** What is the default cluster provider?

**Answer:** The `libvirt` provider is the default cluster provider. It uses KVM with libvirt, which is included by default with Oracle Linux.

## libvirt Provider

### Q27
**Question:** What is the libvirt provider and what are its use cases?

**Answer:** The libvirt provider provisions Kubernetes clusters using KVM on a single host. It's useful for creating and destroying Kubernetes clusters for testing and development. While it can deploy production-worthy cluster configurations, all cluster nodes run on a single host, so if the host goes down, all cluster nodes are affected.

### Q28
**Question:** What are the system requirements for creating libvirt clusters?

**Answer:** The system must be a 64-bit x86 or 64-bit ARM system running Oracle Linux 8 or 9, and must include the Unbreakable Enterprise Kernel Release 7 (UEK R7).

### Q29
**Question:** Can libvirt clusters be created across different architectures?

**Answer:** Single and multi-node clusters can be created on both 64-bit x86 and 64-bit ARM systems. Hybrid clusters aren't possible since all nodes run on a single host. However, you can use an ARM system to create a remote cluster on x86 hardware, and vice versa.

### Q30
**Question:** What are the key components in a libvirt cluster architecture?

**Answer:** Key components include the CLI, default configuration, cluster configuration, container registry, OCK image, control plane load balancer for HA, control plane nodes, and worker nodes. All components communicate with the libvirt infrastructure on a single host.

### Q31
**Question:** What is an ephemeral cluster?

**Answer:** An ephemeral cluster is a single-node cluster created with the libvirt provider that lives for a short time and is created and destroyed as needed by the CLI. It's used when provisioning clusters with some CLI commands. An existing cluster can also be used as an ephemeral cluster by including the location of a kubeconfig file as an option with CLI commands.

### Q32
**Question:** What libvirt connection does Oracle CNE use?

**Answer:** Oracle CNE implements a libvirt connection using the legacy single-socket client. For local libvirt clusters, the UNIX domain socket is used. For remote systems, you need to enable a remote transport mechanism for libvirt.

### Q33
**Question:** What's the recommended setup for creating remote libvirt clusters?

**Answer:** Oracle recommends setting up SSH key-based authentication to the remote system as a normal user, and configuring that user with privilege to run libvirt. While any libvirt remote transport options can be used, most remote deployments leverage the `qemu+ssh` transport, which uses SSH to tunnel the UNIX domain socket back to the CLI.

### Q34
**Question:** What port range does libvirt use for cluster access?

**Answer:** Clusters created with the libvirt provider create a tunnel for cluster access through a port on the host where the cluster is deployed. The port range starts at 6443 and increments from there. As clusters are deleted, ports are freed. For remote clusters, ensure this port range is accessible through the system firewall starting at 6443.

### Q35
**Question:** How many kubeconfig files are created for libvirt clusters with privileged access?

**Answer:** For clusters started on systems with access to privileged libvirt instances, two kubeconfig files are created: one for access to the local cluster, and one that can be used on the remote cluster host.

## Oracle Linux Virtualization Manager Provider

### Q36
**Question:** What is the Oracle Linux Virtualization Manager (OLVM) provider?

**Answer:** The `olvm` provider deploys Kubernetes clusters to Oracle Linux Virtualization Manager. It's an implementation of the Kubernetes Cluster API and uses the oVirt REST API to communicate with Oracle Linux Virtualization Manager.

### Q37
**Question:** What credentials are required to create an OLVM cluster?

**Answer:** Creating a cluster on Oracle Linux Virtualization Manager requires you to provide OAuth 2.0 credentials to an existing instance of Oracle Linux Virtualization Manager.

### Q38
**Question:** What Custom Resource Definitions does the OLVM provider implement?

**Answer:** The OLVM provider implements:
- An infrastructure Cluster controller (`OLVMCluster`) CRD
- An infrastructure Machine controller (`OLVMMachine`) CRD

For each cluster, one `OLVMCluster` Custom Resource is needed, plus `OLVMMachine` CRs for control plane nodes and worker nodes.

### Q39
**Question:** What is a management cluster?

**Answer:** A management cluster is a Kubernetes cluster that controls the lifecycle of other clusters (workload clusters). The controllers that implement the Kubernetes Cluster API run inside a management cluster. A workload cluster can be its own management cluster.

### Q40
**Question:** What happens if no management cluster is available when deploying with OLVM?

**Answer:** If no management cluster is available, a cluster is created automatically using the libvirt provider with the default configuration. This ephemeral cluster is used to bootstrap the deployment.

### Q41
**Question:** What is a self-managed cluster?

**Answer:** A self-managed cluster is a workload cluster that also acts as its own management cluster. When the workload cluster has been deployed, the Cluster API resources are migrated from the management cluster into the workload cluster itself.

### Q42
**Question:** Can the OLVM provider use IPv6?

**Answer:** The OLVM provider can be deployed using IPv4 IP addresses or as a dual stack configuration using both IPv4 and IPv6. IPv6 on its own cannot be used.

### Q43
**Question:** Can DHCP be used for IP address assignment in OLVM clusters?

**Answer:** No, Dynamic Host Configuration Protocol (DHCP) cannot be used to assign IP addresses to VMs used for Kubernetes nodes. Instead, you must provide a range of IP addresses for VMs to use as Kubernetes nodes and set an IP address for the built-in Keepalived and NGINX load balancer for control plane nodes (the virtual IP).

### Q44
**Question:** What are the key components in an OLVM cluster architecture?

**Answer:** Key components include the CLI, default and cluster configuration, container registry, Oracle Linux Virtualization Manager OCK image (created and uploaded by the CLI), ephemeral or management cluster, VM template, custom VM image, control plane load balancer, control plane nodes (VMs), and worker nodes (VMs).

## OCI Provider

### Q45
**Question:** What is the OCI provider?

**Answer:** The `oci` provider deploys Kubernetes clusters to Oracle Cloud Infrastructure (OCI) using the Kubernetes Cluster API Provider for OCI. This is an implementation of the Kubernetes Cluster API, which uses Kubernetes Custom Resources serviced by applications running in a Kubernetes cluster.

### Q46
**Question:** What credentials are required to create an OCI cluster?

**Answer:** Creating a cluster on OCI requires you to provide credentials to an existing tenancy. The required privileges depend on the cluster configuration - some deployments may only need privileges to create and destroy compute instances, while others may require more privileges.

### Q47
**Question:** What is required for OCI compartments?

**Answer:** The `oci` provider requires that a compartment is available. Compartments can be specified either by the Oracle Cloud Identifier (OCID) or by its path in the compartment hierarchy, for example `parentcompartment/mycompartment`.

### Q48
**Question:** What are the key components in an OCI cluster architecture?

**Answer:** Key components include the CLI, default and cluster configuration, Cluster API template, OCI CLI (installed on localhost with tenancy/compartment access), container registry, OCI OCK image (created and uploaded by CLI), ephemeral or management cluster, compartment, OCK images in Object Storage bucket, custom compute images, control plane load balancer, control plane nodes (compute instances), and worker nodes (compute instances).

### Q49
**Question:** How is the OCK image prepared for OCI?

**Answer:** The CLI creates an OCI OCK image based on the OCK image pulled from the container registry, then uploads this image to OCI. The image is loaded into an Object Storage bucket, and when the upload is complete, a custom compute image is created from the OCK image for use in creating compute nodes.

## Bring Your Own Provider

### Q50
**Question:** What is the Bring Your Own (BYO) provider?

**Answer:** The BYO (`byo`) provider allows custom installations of the OCK image on arbitrary platforms. This enables creating Kubernetes clusters using bare metal or other virtual instances not explicitly provided by Oracle CNE. It's useful for environments requiring manual installation of individual hosts or standardized golden images.

### Q51
**Question:** What installation technology does the BYO provider use?

**Answer:** BYO installations use OSTree archives with Anaconda and Kickstart to create bootable media. When the base OS installation is complete, Ignition is used to complete the first-boot configuration and provision Kubernetes services on the host.

### Q52
**Question:** What are the main CLI commands used in BYO installations?

**Answer:** The BYO installation uses several `ocne` commands:
- `ocne image create` - Downloads OSTree content and creates an OSTree archive server
- `ocne image upload` - Copies the OSTree archive server to a container registry
- `ocne cluster start` - Generates Ignition content for starting a new cluster
- `ocne cluster join` - Generates Ignition content to add nodes to an existing cluster

### Q53
**Question:** Where can the OSTree archive be served from in BYO installations?

**Answer:** The OSTree archive can be served from a container registry using `ocne image upload`, or you can use Podman to serve the OSTree archive locally if you don't want to use a container registry. The image can be loaded into any target available with Open Container Initiative transports and formats.

### Q54
**Question:** What are the key components in a BYO cluster architecture?

**Answer:** Key components include the CLI, default and cluster configuration, container registry, OCK OSTree image, ephemeral cluster, container registry or Podman (serving OSTree images), Oracle Linux ISO (for kernel and initrd), Ignition file and server, Kickstart file and server, control plane load balancer, control plane nodes, and worker nodes.

## Cluster Administration

### Q55
**Question:** What does the `ocne node update` command do?

**Answer:** The `ocne node update` command updates the Oracle Container Host for Kubernetes (OCK) image on nodes in the cluster. Updating the OCK image is used for patch updates and for minor Kubernetes updates.

### Q56
**Question:** How are updates delivered in Oracle CNE?

**Answer:** Oracle CNE delivers all updates through updated Oracle Container Host for Kubernetes (OCK) images. Updates are delivered through an OCK image specific to the Kubernetes minor version, for example for Kubernetes Release 1.33.

### Q57
**Question:** How do nodes check for updates?

**Answer:** Each node periodically polls the container registry to check for updates to the OCK image it's running, or for an image for the target Kubernetes version if upgrading Kubernetes. Patch updates are downloaded to each node automatically, while upgrade images need to be staged before a node update by setting the Kubernetes version.

### Q58
**Question:** What happens when you run `ocne node update` on a node?

**Answer:** Running `ocne node update` completes these actions:
1. The node is drained from the cluster (using `kubectl drain`), evicting pods
2. The host OCK image is installed on the node and the node is restarted
3. The node is returned to the cluster (using `kubectl uncordon`) and made available to run pods

### Q59
**Question:** What's the recommended order for updating nodes?

**Answer:** Update nodes sequentially, starting with the control plane nodes. You can start the update process as soon as one of the control plane nodes has been annotated as having an update available to save time.

### Q60
**Question:** Can you update a cluster without downtime?

**Answer:** Yes, you can update a Highly Available cluster without bringing it down. As one control plane node is taken offline, another takes control. For single control plane clusters, the control plane is offline briefly during the update. If applications run on multiple worker nodes, they remain available during updates.

## Cluster Backups

### Q61
**Question:** Why are cluster backups important?

**Answer:** Backups protect Kubernetes clusters against control plane node failures, especially for clusters with only one control plane node. Even high availability clusters need a fallback plan if resilience provided by replication and failover is exceeded.

### Q62
**Question:** What data is backed up in an Oracle CNE cluster backup?

**Answer:** The backup contains the etcd database, which maintains state for Kubernetes clusters and is shared between all Kubernetes API Server instances. Only the key containers required for the Kubernetes control plane nodes are backed up - no application containers are included.

### Q63
**Question:** What security considerations apply to cluster backups?

**Answer:** Backups typically contain sensitive data such as Kubernetes Secret objects, so care must be taken to store backups in a secure location. For disaster recovery strategies, backups must be stored in a location with integrity safeguards.

### Q64
**Question:** How do you back up an Oracle CNE cluster?

**Answer:** Use the `ocne cluster backup` command to back up the key containers and manifests for all control plane nodes in the cluster (the etcd database). You don't need to bring down the cluster to perform a backup.

### Q65
**Question:** Does Oracle CNE provide a restore command?

**Answer:** No, the CLI doesn't provide a command to restore a cluster from an etcd database backup. For information on restoring a cluster using the etcd backup, refer to the upstream Kubernetes documentation.

## Cluster Analysis & Console

### Q66
**Question:** What commands are used for cluster analysis?

**Answer:** The `ocne cluster dump` and `ocne cluster analyze` commands are used to create and analyze a dump of cluster and node data from a Kubernetes cluster. This is useful for debugging and getting detailed information about a cluster.

### Q67
**Question:** What is the `ocne cluster console` command used for?

**Answer:** The `ocne cluster console` command connects to the OS console of a node in a cluster. The console provides a method to connect to the host in a chrooted environment to perform debugging or inspection of the host's OS.

### Q68
**Question:** How can you access additional debugging tools in the OS console?

**Answer:** Start the console with the `--toolbox` option to include extra debugging tools for investigation and diagnosis purposes.

### Q69
**Question:** Can you run commands on a node without an interactive console session?

**Answer:** Yes, use the `ocne cluster console` command with the `--` option followed by your command. This runs commands on a node without directly interacting with the shell, which is helpful for returning information about a node.

### Q70
**Question:** What is the default working directory when starting a console session?

**Answer:** By default, the console session starts with the initial working directory set to root (`/`). To access services running on the node itself (like `ocne-update.service`), you can run `chroot /hostroot` to chroot to the local filesystem of the node, or start the session already chrooted using the `--direct` option.

### Q71
**Question:** When would you use SSH or serial console instead of `ocne cluster console`?

**Answer:** The `ocne cluster console` command is the standard method to access a node's OS in the cluster. You would only use other methods like SSH or serial console when the node can't be accessed using the console command.

## Glossary Terms

### Q72
**Question:** What is a cloud native application in Oracle CNE?

**Answer:** A cloud native application is software designed to take advantage of cluster resources and scaling capabilities that can be installed into a Kubernetes cluster.

### Q73
**Question:** What is an application template?

**Answer:** An application template contains configuration options for a specific application, consisting of Helm values. Templates can be extracted from an application catalog and viewed, saved to a file, or edited directly, then used to install the application with the provided configuration.

### Q74
**Question:** What is a workload cluster?

**Answer:** A workload cluster is a Kubernetes cluster whose lifecycle is controlled by a management cluster. A workload cluster might also be a management cluster itself (self-managed).

### Q75
**Question:** What is a node in Oracle CNE terminology?

**Answer:** A node is a single virtual or physical machine within a Kubernetes cluster.

### Q76
**Question:** What is the difference between the boot image and OSTree archive image?

**Answer:** The boot image is an OCK Virtual Machine image in Qcow2 format used to create cluster nodes for virtualized platforms. The OSTree archive image is a version of the OCK image converted to an OSTree archive and served over HTTP, used to update cluster nodes and generate customized installations using the Bring Your Own provider.

### Q77
**Question:** What is the relationship between management clusters and ephemeral clusters?

**Answer:** Management clusters control the lifecycle of workload clusters and run the Kubernetes Cluster API controllers. Management clusters can be ephemeral clusters (temporary single-node clusters created and destroyed as needed), or they can be persistent clusters, depending on the context.

### Q78
**Question:** How does Oracle CNE define the different provider types?

**Answer:** Provider types are defined by their target platform:
- `libvirt` provider: KVM-based clusters using libvirt (default)
- `olvm` provider: Oracle Linux Virtualization Manager clusters
- `oci` provider: Oracle Cloud Infrastructure clusters
- `byo` provider: Bring Your Own clusters on bare metal or other platforms