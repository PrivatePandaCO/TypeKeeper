from setuptools import setup

setup(
    name="typekeeper",
    version="0.0.2",
    description="An extensive drop-in argument validator.",
    author="Parth Mittal",
    author_email="parth@privatepanda.co",
    url="https://www.github.com/PrivatePandaCO/typekeeper",
    license="MIT",
    packages=["typekeeper"],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    project_urls={
        "Documentation": "https://github.com/PrivatePandaCO/typekeeper/blob/master/README.md",
        "Github": "https://github.com/PrivatePandaCO/typekeeper",
        "Changelog": "https://github.com/PrivatePandaCO/typekeeper/blob/master/Changelog.md"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
