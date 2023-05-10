from setuptools import setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()


setup(
    name="chat_any_site",
    version="0.1.0",
    packages=["."],
    entry_points={
        "console_scripts": [
            "chatanysite=main:main",
        ],
    },
    install_requires=requirements,
)
