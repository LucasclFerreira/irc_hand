from setuptools import setup, find_packages
import os

# Lê o conteúdo do README.md para usar como descrição longa do pacote
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="irc-hand",  # Nome do projeto (pode conter hífen, mas o pacote no código usa underline)
    version="0.1.0",
    author="Seu Nome",
    author_email="seu.email@exemplo.com",
    description="Pacote para processamento geoespacial e cálculo dos valores HAND",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LucasclFerreira/irc_hand",
    packages=find_packages(),  # Encontra automaticamente os pacotes (no seu caso, deverá encontrar "irc_hand")
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",  # Ajuste a versão mínima do Python conforme necessário
    install_requires=[
        "earthengine-api>=1.5.1",
        "geopandas>=1.0.1",
        "geopy>=2.4.1",
        "pandas>=2.2.3",
        "shapely>=2.0.7",
    ],
    entry_points={
        "console_scripts": [
            # Define o comando de linha de comando "hand-calculator" que invoca o método run_from_cli
            "hand-calculator=irc_hand.hand_application:run_from_cli",
        ],
    },
)
