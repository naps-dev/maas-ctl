# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Removed

### Fixed

### Security

### Deprecated

### Breaking


## [0.7.0] - 2023-06-28

### Added
- Experimental support for renaming network interfaces based on tags set in MaaS. This is done by adding a tag to the network interface of the machine in MaaS. This feature only supports the tag `capture` and renames the tagged interface to `capture0`.

## [0.6.0] - 2023-06-14

### Added
- Deploying clusters now adds node labels with the machine tier to each node. The label name is `cnaps.io/node-type` and the value is set via the corresponding label from MAAS. (e.g. "Tier-1")
- Taints and tolerations are now added to RKE cluster based on tags setup in MaaS

## [0.5.0] - 2023-05-10

### Added

- Function to retrieve a kubeconfig from a kubernetes cluster using scp
  ```sh
  mctl machines get-kubeconfig <machine_name>
  ```
- Workflow to build and push the poetry docker image to GCR
  
### Changed

 - Poetry version is now set in the `Makefile`

### Removed
- Removed the Poetry build step from the `build` and `checks` workflows, the poetry container is now pulled from the GCR registry

## [0.4.0] - 2023-04-25

### Added

- First release of the `mctl` cli tool
- Workflow to build and push the cli docker image to GCR
- Workflow to run code quality checks on the cli code
 
[unreleased]: https://github.com/naps-dev/maas-ctl/compare/v0.6.0...HEAD
[0.7.0]: https://github.com/naps-dev/maas-ctl/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/naps-dev/maas-ctl/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/naps-dev/maas-ctl/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/naps-dev/maas-ctl/releases/tag/v0.4.0
