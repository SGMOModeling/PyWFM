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

   > **Example**
   >
   > ```
   > conda create -n build_pkg
   > ```

   > **Note:**
   >
   > if you have an environment created to build conda packages, you can view existing environments by:
   >
   > ```
   > conda info --envs
   > ```
   >
   > or
   >
   > ```
   > conda env list
   > ```

4. Activate the new or existing conda environment

   ```
   conda activate <env-name>
   ```

5. Install [conda-build](https://docs.conda.io/projects/conda-build/en/stable/) and [anaconda-client](https://docs.anaconda.com/free/anacondaorg/user-guide/getting-started-with-anaconda-client/)

   ```
   conda install anaconda-client conda-build
   ```

6. Log-in to your anaconda account from anaconda prompt

   ```
   anaconda login
   ```

7. To create a conda package, you need to develop a conda recipe. For PyWFM, conda recipes can be found in the conda.recipe directory

   For more information about conda recipes, see the link to the docs:
   https://docs.conda.io/projects/conda-build/en/stable/concepts/recipe.html

   At a minimum, you will need a meta.yaml. For more complex builds, you may also need a build.bat and build.sh to support windows and linux/mac builds, respectively.

   > **Note**
   >
   > At this time, pywfm only supports Windows due to the binary dependency with the Windows IWFM DLL. Initial stages of development for a Linux version of the IWFM API are being explored.

8. Build the conda package

   Navigate to the conda recipe (meta.yaml)

   ```
   conda build --no-anaconda-upload .
   ```

9. Upload the built package to anaconda.org for distribution.

   > **Note**
   >
   > you need to provide the full path to the <package-name>.tar.bz2 file created by conda build.
   > Upon completion of the build process, the path will be provided to you.

   ```
   anaconda upload --user ORGANIZATION package.tar.bz2
   ```

   > **Example**
   >
   > ```
   > anaconda upload --user cadwr-sgmo C:\Users\hatch\.conda\envs\build_pkg\conda-bld\noarch\pywfm-0.1.3-pyh7b7c402_0.tar.bz2
   > ```
