# Installation of panos-conf

`python3`, `pip3` and `git` is required.

1. Clone repository:

    https://github.com/ateanorge/panos-conf.git

2. Install requirements:

    pip3 install -r requirements.txt

3. Copy configuration files, and edit as required:

    cp configs/panos-api-parameters.yml.dist configs/panos-api-parameters.yml
    cp configs/panos-conf.yml.dist configs/panos-conf.yml

4. Check help for valid arguments:

    python panos-conf.py -h
    python panos-conf.py --help
    
