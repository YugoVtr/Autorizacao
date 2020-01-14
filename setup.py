# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name         = 'oniAutorizacao',
    version      = '1.0',
    packages     = find_packages(),
    package_data={
        'oniAutorizacao': ['resources/formularios/*.json']
    },
    entry_points = {'scrapy': ['settings = oniAutorizacao.settings']},
)
