import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="intersection-proximity",
    version="0.0.1",
    author="Neil Chowdhury",
    author_email="neil.chowdhury@outlook.com",
    description="Compute the proximity from any point to a street intersection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ProjectSidewalk/intersection-proximity",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)