__author__ = 'Giacomo Berardi <barnets@gmail.com>'

from setuptools import setup, find_packages

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pydexter',
      #version='0.1',
      description='A Python client for the Dexter REST API',
      long_description=readme(),
      classifiers=[
      #  'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Text Processing :: Linguistic',
      ],
      keywords=['dexter', 'entity linking', 'wikification'],
      url='http://github.com/giacbrd/pydexter',
      author='Giacomo Berardi',
      author_email='barnets@gmail.com',
      license='Apache',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      install_requires=[
          'requests',
      ],
      #test_suite='nose.collector',
      #tests_require=['nose', 'nose-cover3'],
      #entry_points={
      #    'console_scripts': ['funniest-joke=funniest.command_line:main'],
      #},
      include_package_data=True,
      zip_safe=False)
