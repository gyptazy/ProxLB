# Contributing to ProxLB (PLB)

Thank you for considering contributing to ProxLB! We appreciate your help in improving the efficiency and performance of Proxmox clusters. Below are guidelines for contributing to the project.

## Table of Contents

- [Contributing to ProxLB (PLB)](#contributing-to-proxlb-plb)
  - [Table of Contents](#table-of-contents)
  - [Creating an Issue](#creating-an-issue)
  - [Running Linting](#running-linting)
  - [Running Tests](#running-tests)
  - [Add Changelogs](#add-changelogs)
  - [Submitting a Pull Request](#submitting-a-pull-request)
  - [Code of Conduct](#code-of-conduct)
  - [Getting Help](#getting-help)

## Creating an Issue

If you encounter a bug, have a feature request, or have any suggestions, please create an issue in our GitHub repository. To create an issue:

1. **Go to the [Issues](https://github.com/gyptazy/proxlb/issues) section of the repository.**
2. **Click on the "New issue" button.**
3. **Select the appropriate issue template (Bug Report, Feature Request, or Custom Issue).**
4. **Provide a clear and descriptive title.**
5. **Fill out the necessary details in the issue template.** Provide as much detail as possible to help us understand and reproduce the issue or evaluate the feature request.

## Running Linting
Before submitting a pull request, ensure that your changes sucessfully perform the lintin. ProxLB uses [flake8] for running tests. Follow these steps to run tests locally:

1. **Install pytest if you haven't already:**
   ```sh
   pip install flake8
   ```

2. **Run the lintin:**
   ```sh
   python3 -m flake8 proxlb
   ```

Linting will also be performed for each PR. Therefore, it might make sense to test this before pushing locally.

## Running Tests

Before submitting a pull request, ensure that your changes do not break existing functionality. ProxLB uses [pytest](https://docs.pytest.org/en/stable/) for running tests. Follow these steps to run tests locally:

1. **Install pytest if you haven't already:**
   ```sh
   pip install pytest
   ```

2. **Run the tests:**
   ```sh
   pytest
   ```

Ensure all tests pass before submitting your changes.

## Add Changelogs
ProxLB uses the [Changelog Fragments Creator](https://github.com/gyptazy/changelog-fragments-creator) for creating the overall `CHANGELOG.md` file. This changelog file is being generated from the files placed in the https://github.com/gyptazy/ProxLB/tree/main/.changelogs/ directory. Each release is represented by its version number where additional yaml files are being placed and parsed by the CFC tool. Such files look like:

```
added:
  - Add option to rebalance by assigned VM resources to avoid overprovisioning. [#16]
```

Every PR should contain such a file describing the change to ensure this is also stated in the changelog file.

## Submitting a Pull Request

We welcome your contributions! Follow these steps to submit a pull request:

1. **Fork the repository to your GitHub account.**
2. **Clone your forked repository to your local machine:**
   ```sh
   git clone https://github.com/gyptazy/proxlb.git
   cd proxlb
   ```

Please prefix your PR regarding its type. It might be:
* doc
* feature
* fix

It should also provide the issue id to which it is related.

1. **Create a new branch for your changes:**
   ```sh
   git checkout -b feature/10-add-new-cool-stuff
   ```

2. **Make your changes and commit them with a descriptive commit message:**
   ```sh
   git add .
   git commit -m "feature: Adding new cool stuff"
   ```

3. **Push your changes to your forked repository:**
   ```sh
   git push origin feature/10-add-new-cool-stuff
   ```

4. **Create a pull request from your forked repository:**
   - Go to the original repository on GitHub.
   - Click on the "New pull request" button.
   - Select the branch you pushed your changes to and create the pull request.

Please ensure that your pull request:

- Follows the project's coding style and guidelines.
- Includes tests for any new functionality.
- Updates the documentation as necessary.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it to understand the expected behavior and responsibilities when interacting with the community.

## Getting Help

If you need help or have any questions, feel free to reach out by creating an issue or by joining our [discussion forum](https://github.com/gyptazy/proxlb/discussions). You can also refer to our [documentation](https://github.com/gyptazy/ProxLB/tree/main/docs) for more information about the project or join our [chat room](https://matrix.to/#/#proxlb:gyptazy.com) in Matrix.

Thank you for contributing to ProxLB! Together, we can enhance the efficiency and performance of Proxmox clusters.