# No longer in production use. Archived here for historical purpose.

Galaxy ChIP-exo - The Center for Eukaryotic Gene Regulation
===========================================================

This repository contains the Galaxy-cegr pre-processing pipeline used by the
labs in the Center for Eukaryotic Gene Regulation at the Pennsylvania State
University.  This pipeline is one of the components contained within the
Galaxy-cegr Science Gateway environment desscribed within this article:
http://www.huck.psu.edu/content/about/news-archive/announcing-new-galaxy-based-science-gateways-penn-state

Galaxy-cegr Pre-processing Pipeline
===================================

The Galaxy-cegr pre-processing pipeline can be installed by cloning this
repository and configuring the pipeline for use within the file system into
which it has been installed.  This pipeline is used to retrieve raw sequenced
datasets from a remote server, convert tehm to fastqsanger data format, import
them into Galaxy data libraries, and use them as the inputs to the ChIP-exo
workflows (contained within the Galaxy ChIP-exo instance), automatically
executing the workflows for every sample in the run.

Note: any reference to a ~/ file location in the text below implies the
root installation directory of a clone of this repository.

Configuring the pipeline
========================

The pipeline configuration file is located ~/config/cegr_config.ini.sample,
and the sample included with the repository should be copied to
~/config/cegr_config.ini, which is then used as the pipeline's configuration
file.  The file system configuration settings within this file allow for the
pipeline to easily be moved to new environments over time if necessary.

These configuration settings are used by each of the components of the
pipeline, and we'll categorize these components as follows.

1. Remote server configuration settings for retrieving the raw sequenced data.
  The following settings are used primarly by the copy_raw_data.py script.  The
  exception is the REMOTE_WORKFLOW_CONFIG_DIR_NAME setting, which is used by the
  start_workflows.py script.

  RAW_DATA_LOGIN - the login information for the remote server.

  RAW_DATA_DIR - the location for retrieving the raw sequenced data from the
  remote server.

  REMOTE_RUN_COMPLETE_FILE - The file named RunCompletionStatus.xml, which
  is produced by the Illumina sequencer.  This file name configuration setting
  can be changed if different sequencers are used over time.

  REMOTE_RUN_INFO_FILE - the full path to the cegr_run_info.txt on the remote
  server.  This file is produced for each run, and is the configuration engine
  used by the pipeline for each run.  This file is retrieved from the remote
  server by the copy_raw_data.py script and stored locally within the ~/config
  directory.

  REMOTE_WORKFLOW_CONFIG_DIR_NAME - This is the name of the directory that
  contains the XML files for each run.  This value cannot be a full path, but
  must be restricted to the directory name (e.g., cegr_config).

2. Local file system configuration settings.  The follwoing settings are used
  primarily by the bcl2fastq.py and the send_data_to_galaxy.py scripts.

  ANALYSIS_PREP_LOG_FILE_DIR - the local directory where the pre-processing
  pipeline will generate and store all log files.  This is typically ~/log

  BCL2FASTQ_BINARY - the name of the bcl2fastq package - this cannot be a full
  path.

  BCL2FASTQ_REPORT_DIR - the full path to the location that the bcl2fastq
  package will generate its reports.

  FASTQ_VALIDATOR_BINARY - the full path to the installed fastQValidator package.
  The fastQValidator package is available here:
  http://genome.sph.umich.edu/w/images/2/20/FastQValidatorLibStatGen.0.1.1a.tgz
  Due to the way bcl2fastq compresses files (it does not include an end of file
  block), this enhancement was added manually to the ~/src/FastQValidator.cpp
  file: 
  https://github.com/statgen/fastQValidator/commit/0b7decb8b502cd8d9d6bf27dbd9e319ed8478b53.
  The package was then compiled normally.

  RUN_INFO_FILE - the full path to the local cegr_run_info.txt file.

  SAMPLE_SHEET - the full path to the sample sheet file produced by the
  bcl2fastq.py script.

  LIBRARY_PREP_DIR - the full path to the files that have been converted by the
  bcl2fastq. py script into fastqsanger data format.  This path is used by the
  send_data_to_galaxy.py script to import the files into Galaxy data libraries.

  BLACKLIST_FILTER_LIBRARY_NAME - the name of the Galaxy data library that
  contains all of the blacklist filter datasets used by the ChIP-exo workflows.

3. Galaxy ChIP-exo instance and bioblend API configuration settings.

  GALAXY_HOME - the full path to the Galaxy installation root directory.

  GALAXY_BASE_URL - the Galaxy URL, including port.

  API_KEY - the Galaxy api key associated with the user that executes the
  ChIP-exo workflows for each run.

The pipeline's four custom programs
===================================

The pipeline consists of four primary custom programs that perform it's tasks.
Each of these programs includes quality assurance components that automatically
halt processing if errors occur, logging the details for review and correction.
Each program can be executed independently (assuming that the previous program
in the pipeline has completed successfully) allowing for a certain step to be
re-executed after corrections are made.

These programs are loacted in ~/scripts/api and are executed in the following
order.  The programs are executed via the start_processing.sh shell script
located in the same directory.

1. ~/scripts/api/copy_raw_data.py - This script copies a directory of raw data
files produced by the sequencer from a remote host to a local directory.

2. ~/scripts/api/bcl2fastq.py - This script reads a local directory of raw
sequenced datasets and executes the bcl2fastq converter on each file,
converting the raw sequenced data into the fastqsanger format.

3. ~/scripts/api/send_data_to_galaxy.py - This script uses the bioblend API
to create and populate Galaxy data libraries with the data produced by the
bcl2fastq.py script.

4. ~/scripts/api/start_workflows.py - This script parses the cegr_run_info.txt
file to automatically execute a selected workflow for each dbkey defined for
every sample in the defined run.  This script retrieves data library datasets
that were imported by the send_data_to_galaxy.py script and imports them into
a new Galaxy history for each workflow execution.  The history is named with a
combination of the workflow name (e.g., sacCer3_cegr_paired), the workflow
version (e.g., 001) the sample (e.g., 02) and the history name id (e.g., 001).
Using these examples, the complete history name is
sacCer3_cegr_paired_001-02_001.  The values of both the workflow version and
the history name id can be passed as command line parameters if desired.

Executing these scripts requires logging into the file system unless cron is
ued to execute them automatically.  The scripts are executed by executing the
~/scripts/api/start_processing.sh shell script (e.g., sh start_processing.sh).
This script can be executed manually from the command line or cron can be
configured to execute it at a specified time.

When the copy_raw_data.py script is executed, it will first check the remote
server (specified by the RAW_DATA_LOGIN configuration setting) to see if the
file specified by the REMOTE_RUN_COMPLETE_FILE configuration setting exists.
If it does, the script will continue.  If it does ot. the script will sleep
for 5 minutes and check again.  This polling process will continue until the
REMOTE_RUN_COMPLETE_FILE is found, at which time the script will stop polling
and continue its execution.

Each of these scripts, at its conclusion, will produce a file named the same
as the script, but with a .complete extension.  These files are created in
the ~/log directory.  For example, when the ~/scripts/api/copy_raw_data.py
script finishes, it creates the file ~/log/copy_raw_data.py.complete.  The
~/scripts/api/start_processing.sh shell script looks for these files, and
does not execute a script if an associated .complete file exists for it.  This
allows a user (or cron) to execute certain steps in the pipeline while skipping
others.  This is very useful when an error occurs within a step, requiring that
step to be re-executed without having to execute the previous steps in the
pipeline since they completed successfully.  It is also very useful to use this
feature to keep downstream steps in the pipeline from executing if you want to
check the results of the current step before allowing the next step to start.

When all 4 of these scripts have completed, the
~/scripts/api/start_processing.sh script will delete each of the .complete
files created in the ~/log directory by each of the scripts, allowing the next
run to start

Details for the Center for Eukaryotic Gene Regulation
=====================================================

This section provides the details that describe how the CEGR labs use this
pipeline.  The pipeline is used to achieve 2 primary goals; process raw
sequenced data for new runs, and process raw sequenced data for runs that
were done in the past.  The details for each of these is provided below.

There are several operating system aliases that help the user navigate the
file system.

cdcegr - change directory to the root directory where this repository has
been cloned.

cddatasets - change directory to the root directory of all Galaxy datasets.

cdgalaxy - change directory to the Galaxy installation root directory.

cdoldraw - change directory to the location where the raw datasets produced
by runs that occurred in the past are stored.

cdprep - change directory to the the location that contains the directory
defined by the LIBRARY_PREP_DIR configuration setting.

cdraw - change directory to the location where the raw sequenced files for
new runs have been retrieved from the remote server by the copy_raw_data.py
script.

cdscripts - change directory to ~/scripts/api

1. Processing new runs
  Since the raw data from new runs is delivered to a remote server, it must be
  retrieved from that server, so all 4 steps in the pre-processing pipeline must
  be executed.  Here are the general steps for manually processing new runs
  (i.e., cron is not being used) after logging into the system.

  a. cdcegr

  b. cd log

  c. If you want to execute each step while not allowing any downstream steps to
    execute, make sure a .complete file exists for each downstream step:
    - ~/log/bcl2fastq.py.complete
    - ~/log/send_data_to_galaxy.py.complete
    - ~/log/start_workflows.py.complete

  d. sh start_processing.sh and wait for the ~/scripts/api/copy_raw_data.py
    script to finish

  e. Check the log for the current day to make sure there were no errors

  f. Delete the ~/log/bcl2fastq.py.complete file (3 .complete files should
    remain)

  g. sh start_processing.sh and wait for the ~/scripts/api/bcl2fastq.py script
    to finish

  h. Check the log for the current day to make sure there were no errors

  i. Delete the ~/log/send_data_to_galaxy.py.complete file (3 .complete files
    should remain)

  j. sh start_processing.sh and wait for the ~/scripts/api/send_data_to_galaxy.py
    script to finish

  k. Check the log for the current day to make sure there were no errors

  l. Delete the ~/log/start_workflows.py.complete file (3 .complete files
    should remain)

  m. sh start_processing.sh and wait for the ~/scripts/api/start_workflows.py
    script to finish

2. Processing runs that occurred in the past
  Since the raw data for runs that occurred in the past are stored locally, the
  copy_raw_data.py script does not need to be execute in this case.  Here are the
  general steps for manually processing runs that occurred in the past after
  logging into the system.

  a. cdcegr

  b. cd config

  c. Make sure there is not a cegr_run_info.txt file in this directory.  If there
    is one, move it to ~/config/archive, nameing it with the correct .<run>.complete
    extension

  d. Get the name of the directory that contains the raw sequenced files for the
    old run.  The file that associates the directory name with the run is
    ~/doc/run_id_map.txt.  For example, if you are processing run 156, the
    directory that contains that run is 150423_NS500168_0070_AH7J2MBGXX.

  e. cdoldraw

  f. cd to the directory determine in b (e.g., cd 150423_NS500168_0070_AH7J2MBGXX).

  g. copy the full path to the current directory into your clipboard.

  h. cdcegr

  i. cd config

  j. cp <paste clipboard>/cegr_run_info.txt .

  k. cd ~/log

  l. Make sure that the ~/log/copy_raw_data.py.complete file exists.

  m. If you want to execute each step while not allowing any downstream steps to
    execute, make sure a .complete file exists (in addition to the
    copy_raw_data.py.complete file, which must always exist for these old runs) for
    each downstream step:
    - ~/log/copy_raw_data.py.complete
    - ~/log/send_data_to_galaxy.py.complete
    - ~/log/start_workflows.py.complete

  n. sh start_processing.sh and wait for the ~/scripts/api/bcl2fastq.py
    script to finish

  o. Check the log for the current day to make sure there were no errors

  p. Delete the ~/log/send_data_to_galaxy.py.complete file (3 .complete files
    should remain)

  q. sh start_processing.sh and wait for the ~/scripts/api/send_data_to_galaxy.py
    script to finish

  r. Check the log for the current day to make sure there were no errors

  s. Delete the ~/log/start_workflows.py.complete file (3 .complete files
    should remain)

  t. sh start_processing.sh and wait for the ~/scripts/api/start_workflows.py
    script to finish

  u. When all of the scripts have completed successfully, delete the directory
    containing the old raw data files.

Python Standards
================

1. Galaxy follows PEP-8, with particular emphasis on the parts about knowing
when to be consistent, and readability being the ultimate goal.  One divergence
from PEP-8 is line length. Logical (non-comment) lines should be formatted for
readability, recognizing the existence of wide screens and scroll bars
(sometimes a 200 character line is more readable, though rarely).

2. Use spaces, not tabs for indenting!  4 spaces per indent.

3. File names must never include capital letters, and words must be separated
by underscore.  For example, thisIsWrong.py and this_is_right.py.

4. Comments and documentation comments should follow the 79 character per line
rule.

5. Python docstrings need to be reStructured Text (RST) and Sphinx markup
compatible. See https://wiki.galaxyproject.org/Develop/SourceDoc for more
information.

6. Avoid from module import *. It can cause name collisions that are tedious
to track down.

Meta-standards
==============

If you want to add something here, submit is as a Merge Request so that another
developer can review it before it is incorporated.
.
These are best practices. They are not rigid. There are no enforcers.

Author
======

Greg Von Kuster

R & D Engineer

Institute for CyberScience

Penn State University
