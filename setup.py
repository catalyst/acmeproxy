from setuptools import find_packages, setup

requirements = ["django~=2.2.0", "tabulate"]


packages = find_packages(where="./", include=["acmeproxy", "acmeproxy.*"],)
if not packages:
    raise ValueError("No packages detected.")

setup(
    name="acmeproxy",
    version="0.1",
    description="PowerDNS backend for serving ACME dns-01 challenge responses",
    url="https://github.com/catalyst/acmeproxy/",
    author="Catalyst.net.nz Ltd.",
    author_email="opsdev@catalyst.net.nz",
    python_requires=">=3.6",
    license="GPLv3",
    package_dir={"acmeproxy": "acmeproxy"},
    packages=packages,
    install_requires=requirements,
    zip_safe=False,
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
