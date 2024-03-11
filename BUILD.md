# Building and Uploading PyWFM

This guide provides a description of how to build PyWFM and upload the built package to Conda for public distribution

## Building a Conda Package

1. Set-up an account on anaconda.org
2. Download and install anaconda or miniconda distribution
3. Open Anaconda Prompt and create a conda environment

```
conda create -n <env-name>
```

For example if you want the environment to be called build_pkg

```
conda create -n build_pkg
```

---

**Note:**

if you have an environment created to build conda packages, you can view existing environments by:

```
conda info --envs
```

or

```
conda env list
```

---
