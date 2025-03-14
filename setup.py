from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="pr_agent",
    version="0.1.0",
    author="Alex Metelli",
    author_email="alex-metelli@gmx.com",
    description="AI-powered code review assistant for GitHub Pull Requests",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ametel01/pr-agent/",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pr-agent=pr_agent.cli:main",
        ],
    },
) 