from pathlib import Path
from setuptools import find_packages,setup
root=Path(__file__).parent
setup(name="cf-copilot",version="1.0.0",
 description="Invoice payment timing, cash-flow forecasts and collection drafts",python_requires=">=3.10",
 packages=find_packages(),install_requires=[line for line in (root/"requirements.txt").read_text().splitlines() if line],
 include_package_data=True)
