from setuptools import setup

version = '0.11.dev0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'enum34',
    'gdal',
    'lxml >= 3.3.4',  # Source line numbers above 65535
    'setuptools',
    ],

tests_require = [
    'coverage',
    'nose',
    ]

setup(name='ribxlib',
      version=version,
      description="Parser for .ribx files",
      long_description=long_description,
      # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[],
      keywords=[],
      author='Jackie Leng',
      author_email='jackie.leng@nelen-schuurmans.nl',
      url='',
      license='GPL',
      packages=['ribxlib'],
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      tests_require=tests_require,
      extras_require={'test': tests_require},
      entry_points={
          'console_scripts': [
              'ribxdebug = ribxlib.script:main',
          ]},
      )
