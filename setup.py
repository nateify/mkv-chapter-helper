import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mkv-chapter-helper",
    version="0.2",
    author="nateify",
    author_email="nateify@users.noreply.github.com",
    description="Embed chapters into an MKV file with the ability to mix timecodes and chapter names from multiple sources",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nateify/mkv-chapter-helper",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'mkv-chapter-helper = scripts.main:cli'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
