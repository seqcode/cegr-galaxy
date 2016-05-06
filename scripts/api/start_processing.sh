#!/bin/sh

# Exit immediately if a sub-command exits with a non-zero status.
set -e

cd `dirname $0`
# Create the log directory if it doesn't exist.
mkdir -p ../../log

COPY_RAW_DATA_SCRIPT="./copy_raw_data.py"
COPY_RAW_DATA_COMPLETE="../../log/copy_raw_data.py.complete"

BCL2FASTQ_SCRIPT="./bcl2fastq.py"
BCL2FASTQ_COMPLETE="../../log/bcl2fastq.py.complete"

SEND_DATA_TO_GALAXY_SCRIPT="./send_data_to_galaxy.py"
SEND_DATA_TO_GALAXY_COMPLETE="../../log/send_data_to_galaxy.py.complete"

START_WORKFLOWS_SCRIPT="./start_workflows.py"
START_WORKFLOWS_COMPLETE="../../log/start_workflows.py.complete"

if [ ! -f $COPY_RAW_DATA_COMPLETE ];
then
    echo "########################"
    date
    echo $COPY_RAW_DATA_SCRIPT " starting..."
    python $COPY_RAW_DATA_SCRIPT
    echo $COPY_RAW_DATA_SCRIPT " finished..."
    date
fi

if [ ! -f $BCL2FASTQ_COMPLETE ];
then
    echo "########################"
    date
    echo $BCL2FASTQ_SCRIPT " starting..."
    python $BCL2FASTQ_SCRIPT
    echo $BCL2FASTQ_SCRIPT " finished..."
    date
fi

if [ ! -f $SEND_DATA_TO_GALAXY_COMPLETE ];
then
    echo "########################"
    date
    echo $SEND_DATA_TO_GALAXY_SCRIPT " starting..."
    python $SEND_DATA_TO_GALAXY_SCRIPT
    echo $SEND_DATA_TO_GALAXY_SCRIPT " finished..."
    date
fi

if [ ! -f $START_WORKFLOWS_COMPLETE ];
then
    echo "########################"
    date
    echo $START_WORKFLOWS_SCRIPT " starting..."
    python $START_WORKFLOWS_SCRIPT
    echo $START_WORKFLOWS_SCRIPT " finished..."
    date
fi

echo "########################"
if [ -f $COPY_RAW_DATA_COMPLETE ];
then
    echo "Removing " $COPY_RAW_DATA_COMPLETE
    rm $COPY_RAW_DATA_COMPLETE
fi
if [ -f $BCL2FASTQ_COMPLETE ];
then
    echo "Removing " $BCL2FASTQ_COMPLETE
    rm $BCL2FASTQ_COMPLETE
fi
if [ -f $SEND_DATA_TO_GALAXY_COMPLETE ];
then
    echo "Removing " $SEND_DATA_TO_GALAXY_COMPLETE
    rm $SEND_DATA_TO_GALAXY_COMPLETE
fi
if [ -f $START_WORKFLOWS_COMPLETE ];
then
    echo "Removing " $START_WORKFLOWS_COMPLETE
    rm $START_WORKFLOWS_COMPLETE
fi
echo "Finished processing..."
date
