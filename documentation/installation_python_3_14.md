[comment]: #Copyright_(c)_2025_Leon_Gattermeyer
[comment]: #This_file_is_part_of_mhbai.
[comment]: #Licensed_under_the_AGPL-3.0_License_See_LICENSE_file_in_the_project_root_for_full_license_information.

[comment]:  Description:_create_search_string_for_search_engine_from_course_information,_code_works_but_needs_to_be_polished,_use_lxml
[comment]: #Status:_VERSION_1.0
[comment]: #File_ID:_Do-su-0002

# Installation of Python3.14
In order to install python3.14, run following commands: 
1. sudo apt update
2. sudo apt install -y build-essential libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libsqlite3-dev libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev libffi-dev uuid-dev wget
3. wget https://www.python.org/ftp/python/3.14.0/Python-3.14.0.tgz
4. tar -xf Python-3.14.0.tgz
5. cd Python-3.14.0
6. ./configure --enable-optimizations
7. make -j$(nproc)
8. sudo make altinstall
