from setuptools import setup, find_packages


setup(
    name='skip-pydjamodb',
    version='0.1.1',
    description="Django interface to PyDjamoDB.",
    keywords='django, DynamoDB, PyDjamoDB',
    author='Lubos Matl',
    author_email='matllubos@gmail.com',
    url='https://github.com/skip-pay/pydjamodb',
    license='MIT',
    package_dir={'pydjamodb': 'pydjamodb'},
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: Czech',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    install_requires=[
        'django>=4.2',
    ],
    zip_safe=False
)
