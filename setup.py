from setuptools import setup, find_packages

data = exec(open("mew_pl/version.py").read())

setup(
    name='mew_pl',
    version=__version__,
    install_requires=[
        'colorama'
    ],
    include=['ply', 'targets'],
    entry_points = {
        'console_scripts': [
            'mew = mew_pl.__main__:main'
        ]
    },
    packages=find_packages(),
    package_dir={'mew_pl': 'mew_pl'},
    package_data={
        'mew_pl': [
            'targets/linux/*'
        ],
    },
    py_modules=[]
)
