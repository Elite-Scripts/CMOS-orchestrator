from setuptools import setup, find_packages

setup(
    name="CMOS-orchestrator",
    version="0.1",
    # The "" key represents the root package; packages are in "src/main/python"
    package_dir={"": "src/main/python"},
    package_data={'CMOS_orchestrator': ['resources/*']},
    include_package_data=True,
    license='GNU General Public License v3.0',
    install_requires=[
        'textual==0.86.3',
        'rich-pixels==3.0.1',
        # If psutil is preinstalled on the OS this can cause issues.
        'psutil >=5.9, <6',
        'setuptools>70',
        'WoeUSB-ng @ git+https://github.com/Elite-Scripts/WoeUSB-ng.git@cf688d3d466739f13a7d917a2a32104120cc76f0#egg=WoeUSB-ng'
    ],
    entry_points={
        'console_scripts': [
            'CMOS=CMOS_orchestrator.textual_ui.main:run',
            'cmos=CMOS_orchestrator.textual_ui.main:run',
        ],
    }
)
