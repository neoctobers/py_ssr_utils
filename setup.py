# coding:utf-8
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ssr-utils",
    version="7.1.0",
    author="@neoctobers",
    author_email="neoctobers@gmail.com",
    description="Shadowsocks(R) utils.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/neoctobers/py_ssr_utils",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'profig',
        'requests-cache',
        'cli-print',
        'ip-query',
        'qwert',
        'proxy-fn',
        'common-patterns',
        'proxychains-conf-generator',
    ],
)

