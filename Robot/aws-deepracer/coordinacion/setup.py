from setuptools import setup

package_name = 'coordinacion'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Santiago Hernandez',
    maintainer_email='shdeza12@gmail.com',
    description='Nodo de coordinacion y protocolo de relevo entre niveles.',
    license='Apache 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'coordinador = coordinacion.coordinador:main',
        ],
    },
)
