import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="intersection-proximity-nchowder",
    version="0.0.9",
    author="Neil Chowdhury",
    author_email="neil.chowdhury@outlook.com",
    description="Compute the proximity from any point to a street intersection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ProjectSidewalk/intersection-proximity",
    packages=['intersection_proximity'],
    install_requires=[
        'dbfread>=2.0.7', 
        'geojson>=2.4.1',
        'numpy>=1.16.4',
        'pandas>=0.24.2',
        'pyproj>=1.9.6',
        'python-dateutil>=2.8.0',
        'pytz>=2019.1',
        'Rtree>=0.8.3',
        'Shapely>=1.6.4.post2',
        'six>=1.12.0',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True
)
