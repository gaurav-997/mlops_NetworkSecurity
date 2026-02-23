"""setup.py is used for packaging the application (the whole project can be
installed with pip) and defines project configuration (metadata,
dependencies, license). It will scan the project and treat folders that
contain an ``__init__.py`` as packages.

Deployment & CI: Used by build pipelines and Dockerfiles to install the
project into images or test environments.
"""

from setuptools import setup, find_packages


def project_requirements():
    requirments_list = []
    try:
        with open(file="requirements.txt") as file:
            line = file.readlines()
            for package in line:
                final_package = package.strip()
                if final_package != '-e .':
                    requirments_list.append(final_package)
                
    except Exception as e:
        raise e
    return requirments_list 

# setup metadata
setup(
    name="mlops-networksecurity",
    version="0.1.0",
    packages=find_packages(exclude=("notebooks",)),
    install_requires=project_requirements(),
    description="MLOps Network Security project",
)