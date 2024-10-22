from setuptools import setup, find_packages

setup(
    name="CMOS-orchestrator",
    version="0.1",
    # The "" key represents the root package; packages are in "src/main/python"
    package_dir={"": "src/main/python"},
    license='GNU General Public License v3.0',
    install_requires=[
        'textual==0.83.0',
        'rich-pixels==3.0.1',
        # If psutil is preinstalled on the OS this can cause issues.
        'psutil >=5.9, <6'
    ],
    entry_points={
        'console_scripts': [
            'CMOS=textual_ui.main:run',
            'cmos=textual_ui.main:run',
        ],
    }
)
