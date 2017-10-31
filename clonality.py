#!/usr/bin/python
import configparser
import copy
import csv
import glob
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns
import subprocess
import sys
import time


def main():
    """Perform clonality analysis"""
    # Remove old error log files
    delete_old_files(errorlog=True)

    # Prep sample list, metadata, and config from command line
    samples_list, metadata_dict, cfg_file, arblist = prep_files(metadatafilename='metadata.tsv', configfilename='config.cfg')

    # check and return a configuration dictionary
    config_dict = config_checker(cfg_file)

    # Remove old output files
    if config_dict['config_overwrite'] == True:
        delete_old_files(post=True)

    # parse the data
    parsed_clonality, parsed_tcell, reproduction_clonality, reproduction_tcell = get_data(samples_list, metadata_dict)

    # Parse the arbitrary data if arblist has anything in it
    if len(arblist) > 0:
        arb_names = copy.deepcopy(arblist)
        arb_dicts = parse_arbitrary(metadata_dict, arblist)
    else:
        arb_dicts = []

    # Do stats and plotting if there are data in the dictionaries
    # Clonality:
    if len(parsed_clonality) > 0:
        file_name_var = 'clonality'
        # Clean data
        clonality_data = clean_data(parsed_clonality, file_name_var)
        # Do statistics
        if config_dict['config_overwrite'] == True:
            do_stats(clonality_data, file_name_var, config_dict, reproduction_clonality)
        # Plot the data
        plot_graph(clonality_data,
                   file_name_var,
                   config_dict=config_dict,
                   y_label="CLONALITY",
                   graph_name="CLONALITY.png")

    # %T Cell
    try:
        if len(parsed_tcell) > 0:
            file_name_var = 'tcell'
            # Clean Data
            tcell_data = clean_data(parsed_tcell, file_name_var)
            # Do statistics
            if config_dict['config_overwrite'] == True:
                do_stats(tcell_data, file_name_var, config_dict, reproduction_tcell)
            # Plot the data
            plot_graph(tcell_data,
                       file_name_var,
                       config_dict=config_dict,
                       y_label="% T CELL RECEPTOR",
                       graph_name="TCELL_GRAPH.png")
    except ValueError:
        pass

    # Do stats and plotting if there is data in the arbitrary dicitonaries
    if len(arb_dicts) > 0:
        file_name_var = 'arb'
        # Clean data
        arb_data = clean_data(arb_dicts, file_name_var)
        # Do statistics
        if config_dict['config_overwrite'] == True:
            do_stats(arb_data, file_name_var, config_dict, reproduction_data=arb_data)
        # Plot the data
        for i, arb in enumerate(arblist):
            if len(arb) > 0:
                file_name_var = 'arb' + str(i + 1)
                plot_graph(arb_data[i],
                           file_name_var,
                           config_dict=config_dict,
                           y_label=arb_names[i].upper(),
                           graph_name=arb_names[i].upper() + '.png')

    # Combine stats files or separate them?
    create_master_file(config_dict['config_masterfile'])
    # Remove unnecessary files (pre_stats)
    delete_old_files(pre=True)


def parse_arbitrary(metadata_dict, arblist):
    """Rewrite list elements into dictionaries"""
    # arblist becomes a list of dictionaries in this function
    for i, arb in enumerate(arblist):
        arblist[i] = {}

    for key, value in metadata_dict.items():
        # loops through each individual values (j = list element, v = value)
        for j, v in enumerate(value):
            # Add each value to its dictionary in arblist
            try:
                if value[j] is not '':
                    arblist[j][key] = value[j]
                else:
                    continue
            except IndexError:
                arblist = [{(key): value[j]}]

    return arblist


def clean_data(parsed_data, file_name_var):
    """Clean out None types from data"""
    if 'clonality' in file_name_var or 'tcell' in file_name_var:
        # In this case, parsed_data will be a dicitonary
        for value in parsed_data.values():
            value[:] = (x for x in value if x is not None)
        parsed_data = dict((k, v) for k, v in parsed_data.items() if v)


    # Clean out bad values in arbitrary data (non-numbers)
    # In this case, data will be a list of dictionaries
    elif 'arb' in file_name_var:
        parsed_data = [x for x in parsed_data if len(x) > 0]

        # loop through the list of dicts
        for arbdict in parsed_data:
            # loop through each dict
            for key, value in arbdict.items():
                # If the value is not a number, set to None
                try:
                    float(value)
                    arbdict[key] = float(value)

                except ValueError:
                    arbdict[key] = None
    return parsed_data


def prep_files(metadatafilename='metadata.tsv', configfilename='config.cfg'):
    """Return parsed and cleaned data/metadata/config data"""
    # Parse command line or search locally
    args = sys.argv
    if len(args) == 1:
        args = os.listdir('.')
    if metadatafilename is None:
        metadatafilename = 'Metadata file'

    # Look in CLI for metadata, then look in local folder
    try:
        assert metadatafilename in args
        metadata, arblist = prep_meta(metadatafilename)
    except AssertionError:
        local_dir = os.listdir('.')
        try:
            assert metadatafilename in local_dir
            metadata, arblist = prep_meta(metadatafilename)
        except AssertionError:
            error_log('Attention: ' + metadatafilename + ' not found. The program requires a metadata.tsv.')
            sys.exit()

    # Check sys args for config
    try:
        assert configfilename in args
        cfg_file = configfilename
    except AssertionError:
        error_log('Note: No config.cfg file specified, searching local directory for one...')
        # Check local directory for config
        local_dir = os.listdir('.')
        try:
            assert configfilename in local_dir
            error_log('Found ' + configfilename + ' in the local directory.')
            cfg_file = configfilename
        except AssertionError:
            error_log("Config file not found. Creating config.cfg with default options...")
            # make a new default config
            createConfig()
            cfg_file = 'config.cfg'

    # Sort arguments into sample files
    samples_list = []
    try:
        for arg in args:
            if ".tsv" in arg and "metadata" not in arg:
                samples_list.append(arg)
        assert len(samples_list) >= 2
    # If CLI arguments dont have enough sample files, look in the local directory
    except AssertionError:
        # If only one sample file is specified
        if len(samples_list) == 1:
            error_log("Attention: Not enough sample files specified explicitly. " + str(
                samples_list) + " is all we found and we need more than one.")
            sys.exit()

        elif len(samples_list) == 0:
            error_log("Note: No sample files were specified explicitly, searching local directory for sample files...")
            # Search local directory
            args = os.listdir()

            for arg in args:
                if ".tsv" in arg and "metadata" not in arg:
                    samples_list.append(arg)
            # If the local directory doesn't have sample files, sys.exit
            if len(samples_list) < 2:
                error_log("Attention: Searched local directory for sample files and found none.")
                sys.exit()
            else:
                error_log("Found sample files in the local directory.")

    return samples_list, metadata, cfg_file, arblist


def prep_meta(meta_file_to_prep='metadata.tsv'):
    """Return  metadata and arbitrary dictionaries"""
    # initialize lists and dictionaries
    meta_dictionary = {}

    # Populate dictionary with metadata
    try:
        with open(meta_file_to_prep, 'r') as meta_file:
            # Save the metadata header and check for empty headers
            header = meta_file.readline().split("\t")
            if '' in header or '\n' in header:
                error_log(
                    "There is a missing header in the metadata file. Every column should have a header. Column one is reserved for GROUPS, column two for SAMPLE FILES, and any additional columns need Custom Names for headers.")
                sys.exit()
            if len(header[0]) < 1:
                error_log(
                    "Problem with metadata column 1: \n\t\t - Make sure the first row of each column has a header/name. \n\t\t - Column one should be named GROUPS. \n\t\t - Make sure there are no blank cells in the column.")
                sys.exit()
            if len(header) < 2:
                error_log(
                    "Problem with metadata column 2: \n\t\t - Make sure the first row of each column has a header/name. \n\t\t - Column two should be named SAMPLE FILES. \n\t\t - Make sure there are no blank cells in the column.")
                sys.exit()

            # Remove whitespace characters
            try:
                header.remove("\n")
            except ValueError:
                for i, head in enumerate(header):
                    header[i] = head.strip()

            arblist = header[2:]
            numArbs = len(header[2:])

            # Remove illegal characters
            for i, arb in enumerate(arblist):
                arblist[i] = arb.translate({ord(c): "" for c in '/\:*?"<>|'})

            # Add data to meta_dictioanry
            for line in meta_file:
                try:
                    group, sampleId, arbitrary = line.split("\t", 2)
                    if group is '':
                        error_log("Blank cells in metadata.tsv GROUP column (Column one).")
                        sys.exit()
                    if sampleId is '':
                        error_log("Blank cells in the metadata.tsv SAMPLE FILE column (Column two).")
                        sys.exit()
                    arbitrary = arbitrary.strip()
                    meta_dictionary[(group.upper().strip(), sampleId.strip())] = arbitrary.split("\t", numArbs)

                # When there is no arbitrary
                except ValueError:
                    try:
                        group, sampleId = line.strip().split("\t")
                        if group is '' and sampleId is not '':
                            error_log("2 Blank cells in metadata.tsv GROUPS column (Column one).")
                            sys.exit()
                        elif group is not '' and sampleId is '':
                            error_log("Blank cells in metadata.tsv SAMPLE FILES column (Column two).")
                            sys.exit()
                        elif group is '' and sampleId is '':
                            continue

                        meta_dictionary[(group.upper(), sampleId)] = []
                    # Probably a blank row.
                    except ValueError:
                        error_log(
                            "Found blank cells in " + meta_file_to_prep + ". Please remove those rows entirely or fill in the information.")
                        continue


    except FileNotFoundError:
        error_log('Metadata file, "' + meta_file_to_prep + '" not found.')
        sys.exit()

    # Make sure there's more than one group, if not sys.exit
    groups = [g for (g, s) in meta_dictionary.keys()]
    if len(set(groups)) < 2:
        error_log(
            "Couldn't find enough groups in the metadata. \n\t\tYou need at least two different groups to compare.")
        sys.exit()
    return meta_dictionary, arblist


def config_checker(cfg_file):
    """Return dictionary of config options"""
    config_dict = {}
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read(cfg_file)

    try:
        config_correction = config.get('statistics', 'Correction')
        # If it looks good add it to the dict
        assert "none" in config_correction.lower() or "bh" in config_correction.lower() or "bonferroni" in config_correction.lower()
        config_dict['config_correction'] = config_correction
    except AssertionError:
        # If it's invalid set to default
        config_dict['config_correction'] = 'None'
        # Print to error log that this option was set to default
        error_log(
            '"' + config_correction + '"' + ' is not a valid option for Correction. The defualt "None" was used. Multiple correction options are Bonferroni, BH, or None.')

    try:
        config_masterfile = config.get('output', 'Masterfile')
        assert "true" in config_masterfile.lower() or "false" in config_masterfile.lower()
        config_masterfile = config.getboolean('output', 'Masterfile')
        config_dict['config_masterfile'] = config_masterfile
    except AssertionError:
        config_dict['config_masterfile'] = False
        error_log(
            '"' + config_masterfile + '"' + ' is not a valid option for masterfile. The defualt "True" was used. Master file options are True or False.')

    try:
        config_output_verbose = config.get('statistics', 'Verbose')
        assert "true" in config_output_verbose.lower() or "false" in config_output_verbose.lower()
        config_output_verbose = config.getboolean('statistics', 'Verbose')
        config_dict['config_output_verbose'] = config_output_verbose
    except AssertionError:
        config_dict['config_output_verbose'] = False
        error_log(
            '"' + config_output_verbose + '"' + ' is not a valid option for verbose. The defualt "False" was used. Verbose options are True or False.')

    try:
        config_error_log = config.get('output', 'Error log')
        assert "true" in config_error_log.lower() or "false" in config_error_log.lower()
        config_error_log = config.getboolean('output', 'Error Log')
        config_dict['config_error_log'] = config_error_log
    except AssertionError:
        config_dict['config_error_log'] = True
        error_log(
            '"' + config_error_log + '"' + ' is not a valid option for Error Log. The defualt "True" was used. Error Log options are True or False.')

    try:
        config_overwrite = config.get('output', 'Overwrite')
        assert "true" in config_overwrite.lower() or "false" in config_overwrite.lower()
        config_overwrite = config.getboolean('output', 'Overwrite')
        config_dict['config_overwrite'] = config_overwrite
    except AssertionError:
        config_dict['config_overwrite'] = True
        error_log(
            '"' + config_overwrite + '"' + ' is not a valid option for Overwrite. The defualt "True" was used. Options are True or False.')

    # Can be blank, doesn't matter, doesn't need to be checked,... maybe
    config_title = config.get('graph_options', 'Title')
    config_dict['config_title'] = config_title

    try:
        config_order = config.get('graph_options', 'Custom Order')
        assert "false" in config_order.lower() or "true" in config_order.lower()
        config_order = config.getboolean('graph_options', 'Custom Order')
        config_dict['config_order'] = config_order
        if config_order == True:
            config_dict['config_masterfile'] = False
            error_log(
                'Note: Since overwrite is set to True, Masterfile has automatically been set to False to prevent FileNotFound errors.')
    except AssertionError:
        config_dict['config_order'] = False
        error_log(
            '"' + config_order + '"' + ' is not a valid option for Custom Order. The defualt "False" was used. Custom Order options are True or False.')

    try:
        config_xrotation = config.get('graph_options', 'X-label rotation')
        config_xrotation = int(config_xrotation)
        assert config_xrotation >= -90 and config_xrotation <= 90
        config_dict['config_xrotation'] = config_xrotation
    except AssertionError as error:
        config_dict['config_xrotation'] = 0
        error_log(str(error) + ' "' + str(
            config_xrotation) + '"' + ' is not a valid option for X-Label rotation. Value must be an integer between -90 and +90. The defualt 0 was used.')

    try:
        config_boxplots = config.get('graph_options', 'Boxplots')
        config_boxplots = config.getboolean('graph_options', 'Boxplots')
        config_dict['config_boxplots'] = config_boxplots
    except AssertionError:
        config_dict['config_boxplots'] = True
        error_log(
            '"' + config_boxplots + '"' + ' is not a valid option for boxplots. The defualt "True" was used. Boxplot options are True or False.')

    try:
        config_boxcolors = config.get('graph_options', 'Box colors')
        assert "false" in config_boxcolors.lower() or "true" in config_boxcolors.lower()
        config_boxcolors = config.getboolean('graph_options', 'Box colors')
        config_dict['config_boxcolors'] = config_boxcolors
    except AssertionError:
        config_dict['config_boxcolors'] = True
        error_log(
            '"' + config_boxcolors + '"' + ' is not a valid option for boxcolors. The defualt "True" was used. Boxplot color options are True or False.')

    config_boxpalette = config.get('graph_options', 'Box color palette')
    if 'none' in config_boxpalette.lower():
        config_dict['config_boxpalette'] = None
    else:
        try:
            # Convert string from config file into a list of integers
            config_boxpalette = [int(i) - 1 for i in config_boxpalette.split(",")]
            config_dict['config_boxpalette'] = config_boxpalette
        except ValueError:
            error_log(
                "Value Error: Couldn't convert " + config_boxpalette + " into a list of integers for the box plot color palette. Make sure you are using integers separated by a single comma e.g. 1,2,3,4,5,6 \nUsing default Adaptive colors' ")
            config_dict['config_boxpalette'] = None

    try:
        config_stripplots = config.get('graph_options', 'Strip plots')
        assert "false" in config_stripplots.lower() or "true" in config_stripplots.lower()
        config_stripplots = config.getboolean('graph_options', 'Strip plots')
        config_dict['config_stripplots'] = config_stripplots
    except AssertionError:
        config_dict['config_stripplots'] = True
        error_log(
            '"' + config_stripplots + '"' + ' is not a valid option for stripplots. The defualt "True" was used. Strip plot options are True or False.')

    try:
        config_dotcolors = config.get('graph_options', 'Dot colors')
        assert "false" in config_dotcolors.lower() or "true" in config_dotcolors.lower()
        config_dotcolors = config.getboolean('graph_options', 'Dot colors')
        config_dict['config_dotcolors'] = config_dotcolors
    except AssertionError:
        config_dict['config_dotcolors'] = True
        error_log(
            '"' + config_dotcolors + '"' + ' is not a valid option for dotcolors. The defualt "True" was used. Dot color options are True or False.')

    config_dotpalette = config.get('graph_options', 'Dot color palette')
    if 'none' in config_dotpalette.lower():
        config_dict['config_dotpalette'] = None
    else:
        try:
            # Convert string from config file into a list of integers
            config_dotpalette = [int(i) - 1 for i in config_dotpalette.split(",")]
            config_dict['config_dotpalette'] = config_dotpalette
        except ValueError:
            error_log(
                "Value Error: Couldn't convert " + config_dotpalette + " into a list of integers for the dot color palette. Make sure you are using integers separated by a single comma e.g. 1,2,3,4,5,6 \nUsing default Adaptive colors' ")
            config_dict['config_dotpalette'] = None

    try:
        config_jitter = config.get('graph_options', 'Jitter')
        assert "false" in config_jitter.lower() or "true" in config_jitter.lower()
        config_jitter = config.getboolean('graph_options', 'Jitter')
        config_dict['config_jitter'] = config_jitter
    except AssertionError:
        config_dict['config_jitter'] = True
        error_log(
            '"' + config_jitter + '"' + ' is not a valid option for jitter. The defualt "True" was used. Jitter options are True or False.')

    try:
        config_meanbars = config.get('graph_options', 'Meanbars')
        assert "false" in config_meanbars.lower() or "true" in config_meanbars.lower()
        config_meanbars = config.getboolean('graph_options', 'Meanbars')
        config_dict['config_meanbars'] = config_meanbars
    except AssertionError:
        config_dict['config_meanbars'] = False
        error_log(
            '"' + config_meanbars + '"' + ' is not a valid option for meanbars. The defualt "False" was used. Mean bar options are True or False.')

    try:
        config_errorbars = config.get('graph_options', 'Errorbars')
        assert "none" in config_errorbars.lower() or "sem" in config_errorbars.lower() or "sd" in config_errorbars.lower()
        config_dict['config_errorbars'] = config_errorbars.lower()
    except AssertionError:
        config_dict['config_errorbars'] = 'None'
        error_log(
            '"' + config_errorbars + '"' + ' is not a valid option for errorbars. The defualt "None" was used. Error bar options are SD, SEM, or None')

    try:
        config_logscale = config.get('graph_options', 'Logscale')
        assert "false" in config_logscale.lower() or "true" in config_logscale.lower()
        config_logscale = config.getboolean('graph_options', 'Logscale')
        config_dict['config_logscale'] = config_logscale
    except AssertionError:
        config_dict['config_logscale'] = False
        error_log(
            '"' + config_logscale + '"' + ' is not a valid option for logscale. The defualt "False" was used. Log scale options are True or False.')

    try:
        config_annotation = config.get('graph_options', 'Annotation')
        assert "false" in config_annotation.lower() or "true" in config_annotation.lower()
        config_annotation = config.getboolean('graph_options', 'Annotation')
        config_dict['config_annotation'] = config_annotation
    except AssertionError:
        config_dict['config_annotation'] = True
        error_log(
            '"' + config_annotation + '"' + ' is not a valid option for annotation. The defualt "False" was used. Significance annotation options are True or False.')

    try:
        config_dpi = config.get('graph_options', 'DPI')
        config_dpi = int(config_dpi)
        assert config_dpi >= 300 and config_dpi <= 600
        config_dict['config_dpi'] = int(config_dpi)
    except (AssertionError, ValueError):
        config_dict['config_dpi'] = int(600)
        error_log('"' + str(
            config_dpi) + '"' + ' is not a valid option for dpi. The defualt "600" was used. DPI options are any integer between 300 and 600.')

    try:
        config_width = config.get('graph_options', 'Width')
        config_width = float(config_width)
        assert config_width >= 1
        config_dict['config_width'] = float(config_width)
    except AssertionError:
        config_dict['config_width'] = 8
        error_log('"' + str(config_width) + '"' + ' is not a valid option for width. The defualt  was used.')

    try:
        config_height = config.get('graph_options', 'Height')
        config_height = float(config_height)
        assert config_height >= 1
        config_dict['config_height'] = float(config_height)
    except AssertionError:
        config_dict['config_height'] = 5
        error_log('"' + str(config_height) + '"' + ' is not a valid option for width. The defualt 5" was used.')

    return config_dict


def createConfig(configFile='config.cfg',
                 correction=None,
                 verbose=False,
                 masterfile=True,
                 error_log=True,
                 overwrite=True,
                 title='ImmunoSEQ Analyzer',
                 custom_order=False,
                 xrotation=0,
                 boxplots=True,
                 boxcolors=True,
                 boxpalette='None',
                 stripplots=True,
                 dotcolors=True,
                 dotpalette='None',
                 jitter=True,
                 meanbars=False,
                 errorbars=None,
                 logscale=False,
                 annotation=True,
                 dpi=600,
                 width=8,
                 height=5):
    """Create a default configuration file"""
    # Write to file
    with open(configFile, 'w') as cfg:
        cfg.write('[statistics]\n')
        cfg.write('Correction = ' + str(correction) + '\n')
        cfg.write('Verbose = ' + str(verbose) + "\n\n")

        cfg.write('[output]\n')
        cfg.write('Masterfile = ' + str(masterfile) + "\n")
        cfg.write('Error log = ' + str(error_log) + "\n")
        cfg.write('Overwrite = ' + str(overwrite) + "\n\n")

        cfg.write('[graph_options]\n')
        cfg.write('Title = ' + title + "\n")
        cfg.write('Custom Order = ' + str(custom_order) + "\n")
        cfg.write('X-label rotation = ' + str(xrotation) + "\n\n")

        cfg.write('Boxplots = ' + str(boxplots) + "\n")
        cfg.write('Box colors = ' + str(boxcolors) + "\n")
        cfg.write('Box color palette = ' + str(boxpalette) + "\n\n")

        cfg.write('Strip plots = ' + str(stripplots) + "\n")
        cfg.write('Dot colors = ' + str(dotcolors) + "\n")
        cfg.write('Dot color palette = ' + str(dotpalette) + "\n")
        cfg.write('Jitter = ' + str(jitter) + "\n\n")

        cfg.write('Meanbars = ' + str(meanbars) + "\n")
        cfg.write('Errorbars = ' + str(errorbars) + "\n\n")

        cfg.write('Logscale = ' + str(logscale) + "\n")
        cfg.write('Annotation = ' + str(annotation) + "\n")
        cfg.write('DPI = ' + str(dpi) + "\n")
        cfg.write('Width = ' + str(width) + "\n")
        cfg.write('Height = ' + str(height) + "\n")


def get_data(samples_list, metadata_dict):
    """Return values from sample files"""
    # Initialize dictionaries to return
    parsed_clonality = dict()
    parsed_tcell = dict()
    reproduction_clonality = dict()
    reproduction_tcell = dict()

    # Dictonary to reference samples to the groups they belong
    meta_sample_to_group = {sampleId: group for group, sampleId in metadata_dict.keys()}

    # List of samples
    meta_samples = [sampleId for group, sampleId in metadata_dict.keys()]

    # Dictionaries to store parsed values
    for group in meta_sample_to_group.values():
        parsed_clonality[group] = []
        parsed_tcell[group] = []
    # Dictionaries to store data for reproducing graphs
    for sample, group in meta_sample_to_group.items():
        reproduction_clonality[(group, sample)] = []
        reproduction_tcell[(group, sample)] = []

    # Iterate through the sample files from sysarg
    for sample in samples_list:
        # Check to make sure it's in metadata before doing anything
        if sample in meta_samples:
            # Parse the desired value out of each sample file
            clonality, tcell = parse_file(sample)
            # Convert non-numbers and out of range numbers to None
            if type(clonality) is str:
                clonality = float(clonality)
                if clonality < 0 or clonality > 1:
                    error_log(sample + ' not used in clonality analysis...')
                    # Set to none
                    clonality = None
            elif clonality is None:
                error_log(sample + ' not used in clonality analysis...')

            if type(tcell) is str:
                tcell = float(tcell)
                if tcell < 0 or tcell > 1:
                    error_log(sample + ' not used in tcell analysis...')
                    # Set to none
                    tcell = None
            elif tcell is None:
                error_log(sample + ' not used in tcell analysis...')

            # Get the group associated with the sample
            group = meta_sample_to_group[sample]

            # Store the values in the dictionary for whichever group it belongs
            parsed_clonality[group].append(clonality)
            parsed_tcell[group].append(tcell)
            reproduction_clonality[(group, sample)] = clonality
            reproduction_tcell[(group, sample)] = tcell


        else:
            # If it's a standard output file just ignore it
            outputfiles = ['post_stats_complete.tsv', 'post_stats_clonality.tsv', 'post_stats_tcell.tsv']
            if sample in outputfiles:
                continue
            # Else send it to the errorlog()
            else:
                error_log(sample + ' was omitted from analysis because it is not in the metadata.')
                continue

    return parsed_clonality, parsed_tcell, reproduction_clonality, reproduction_tcell


def parse_file(sample):
    """Return Clonality and %Tcell values from individual sample files"""
    clonality, tcell = None, None
    samplefile = sample
    with open(sample, 'r') as sample:
        for line in sample:
            if line.startswith('#clonality'):
                # Clean up the value and put it in group/sample dictionary
                clonality = line.strip().split('=')[-1]

                # Discard any clonality values that are not between 0 and 1
                if 'NA' in clonality or clonality is '':
                    error_log(samplefile + ' -  Clonality Value: " ' + clonality + ' "')
                    clonality = None

                elif float(clonality) < 0 or float(clonality) > 1:
                    error_log(samplefile + ' -  Clonality Value: "' + clonality + '" out of range')
                    clonality = None

            elif line.startswith('#percentReceptor'):
                # Clean up the value and put it in group/sample dictionary
                tcell = line.strip().split('=')[-1]
                if 'NA' in tcell or tcell == '':
                    error_log(samplefile + ' -  Tcell Value: " ' + tcell + ' "')
                    tcell = None
                elif float(tcell) < 0 or float(tcell) > 1:
                    error_log(samplefile + ' -  Tcell Value: "' + tcell + '" out of range')
                    tcell = None

                break

    return clonality, tcell


def parse_SEM(file_name_var):
    """Return mean, SEM, and SD"""
    means = []
    SEM = []
    sd = []

    try:
        with open('post_stats_' + file_name_var + '.tsv', 'r') as lines:
            for line in lines:
                if line.startswith('"#SUMMARYmean"'):
                    # Clean up the value and put it in group/sample dictionary
                    means = line.strip().split("\t")[1:]

                elif line.startswith('"#SDvalue"'):
                    # Cealn up the value and put it in group/sample dictionary
                    sd = line.strip().split("\t")[1:]

                elif line.startswith('"#SEMvalue"'):
                    # Clean up the value and put it in group/sample dictionary
                    SEM = line.strip().split("\t")[1:]
                    break

            # Remove quotes and NAs, None's are cool
            try:
                means = [float(i.strip('"')) for i in means]
            except ValueError:
                means = [i.strip('"') for i in means]
                for i, thing in enumerate(means):
                    if thing == 'NA':
                        means[i] = None
                    else:
                        means[i] = float(thing)
            try:
                SEM = [float(i.strip('"')) for i in SEM]
            except ValueError:
                SEM = [i.strip('"') for i in SEM]
                for i, thing in enumerate(SEM):
                    if thing == 'NA':
                        SEM[i] = None
                    else:
                        SEM[i] = float(thing)
            try:
                sd = [float(i.strip('"')) for i in sd]
            except ValueError:
                sd = [i.strip('"') for i in sd]
                for i, thing in enumerate(sd):
                    if thing == 'NA':
                        sd[i] = None
                    else:
                        sd[i] = float(thing)
    except FileNotFoundError as error:
        error_log(str(
            error) + ': File not found, please change Overwrite option to True and re-run.\n If you need to edit the output files take these steps:\n 1) Set Overwrite to True\n 3) Re-run the clonality tool\n 4) Set Overwrite option to False -- You should be able to edit the output files now.')
        sys.exit()

    return means, SEM, sd


def do_stats(parsed_data, file_name_var, config_dict, reproduction_data):
    """Call R script to perform stats"""
    # just a note: file_name_var tells R if the data is clonality or %Tcell
    correction = config_dict['config_correction']
    verbose = config_dict['config_output_verbose']

    # In this case the data will come as a single dictionary
    if 'clonality' in file_name_var or 'tcell' in file_name_var:

        # Write dict to tsv
        with open("pre_stats.tsv", 'w', newline='') as outfile:
            writer = csv.writer(outfile, delimiter='\t')
            writer.writerow(("Group", "Value", file_name_var, correction, verbose))
            # Add clonality or %T Cells data points
            for key, values in parsed_data.items():
                for value in values:
                    writer.writerow((key, value))

        with open("pre_repro.tsv", 'w', newline='') as outfile2:
            writer = csv.writer(outfile2, delimiter='\t')
            writer.writerow(("Sample", "Group", "Value"))
            # add the reproducable data
            for (group, sample), value in reproduction_data.items():
                writer.writerow((sample, group, value))

        # Run R script
        cmd = 'Rscript'
        script = 'clonality.R'
        subprocess.call([cmd, script])


    # In this case, data will be as a list of dicitonaries
    elif 'arb' in file_name_var:
        # loop through the list of dictionaries
        for i, arbdict in enumerate(parsed_data):

            with open('pre_stats.tsv', 'w', newline='') as outfile:
                writer = csv.writer(outfile, delimiter='\t')
                writer.writerow(("Group", "Value", file_name_var + str(i + 1), correction, verbose))

                # Loop through the individual dictionary
                for (group, sample), value in arbdict.items():
                    writer.writerow((group, value))

            with open('pre_repro.tsv', 'w', newline='')  as outfile2:
                writer = csv.writer(outfile2, delimiter='\t')
                writer.writerow(("Sample", "Group", "Value"))
                # Loop through the list of arb dictonaries
                for (group, sample), value in reproduction_data[i].items():
                    writer.writerow((sample, group, value))

            # Run R script
            cmd = 'Rscript'
            script = 'clonality.R'
            subprocess.call([cmd, script])


def plot_graph(parsed_data,
               file_name_var,
               y_label,
               config_dict,
               graph_name="plot.png"):
    """Create data plots"""
    # Set the config options
    config_correction = config_dict['config_correction']

    config_title = config_dict['config_title']
    config_order = config_dict['config_order']
    config_xrotation = config_dict['config_xrotation']

    config_boxplots = config_dict['config_boxplots']
    config_boxcolors = config_dict['config_boxcolors']
    config_boxpalette = config_dict['config_boxpalette']

    config_stripplots = config_dict['config_stripplots']
    config_dotcolors = config_dict['config_dotcolors']
    config_dotpalette = config_dict['config_dotpalette']
    config_jitter = config_dict['config_jitter']

    config_meanbars = config_dict['config_meanbars']
    config_errorbars = config_dict['config_errorbars']

    config_logscale = config_dict['config_logscale']
    config_annotation = config_dict['config_annotation']
    config_dpi = config_dict['config_dpi']
    config_width = config_dict['config_width']
    config_height = config_dict['config_height']

    # Ensure default matplotlib settings
    plt.rcParams.update(plt.rcParamsDefault)

    # Filter out empty elements from data
    filtered = {}
    if 'clonality' in file_name_var or 'tcell' in file_name_var:
        for value in parsed_data.values():
            value[:] = (x for x in value if x is not None)
        filtered = {group: value for group, value in parsed_data.items() if len(value) > 0}

    # Arbitrary data gets filtered, None's removed, and empty groups removed in this step
    elif 'arb' in file_name_var:
        # Make empty groups
        for (group, sampleid), value in parsed_data.items():
            filtered[group] = []
        # Add values to groups
        for (group, sampleid), value in parsed_data.items():
            if value is not None:
                filtered[group].append(value)
                parsed_data = filtered
        filtered = {group: value for group, value in parsed_data.items() if len(value) > 0}

    # Create a data frame for the parsed data
    parsedDataFrame = pd.DataFrame.from_dict(parsed_data, orient='index', dtype=None)

    # Transpose the dataframe
    parsedDataFrame = parsedDataFrame.transpose()

    # Sort the data for plotting in alphabetical order
    if config_order != True:
        alphabeticalOrder = sorted(filtered, reverse=False)
        plotOrder = alphabeticalOrder

    # This is alphabetical ordering but strips off the first character from groupname:
    elif config_order == True:
        # Start with alphabetical order
        alphabeticalOrder = sorted(filtered, reverse=False)

        # create custom list
        customOrder = []

        # Strip the first characters off from the plot order
        for i, dat in enumerate(alphabeticalOrder):
            customOrder.append(dat[1:])
        plotOrder = customOrder

        # strip first chracters off of column names so that they match the plot Order
        parsedDataFrame.columns = parsedDataFrame.columns.str[1:]

    # Make a translator dicitonary for group name to x coordinate
    translator = {}
    for each in plotOrder:
        translator[each] = plotOrder.index(each)

    # Get the max value from the data for plotting purposes
    maxnumbers = []
    maxnumbers.append(parsedDataFrame.replace('None', np.nan).astype("float").max().max())
    maxvalue = max(maxnumbers)

    # Get the min for plotting purposes (e.g. don't plot below zero)
    minnumbers = []
    minnumbers.append(parsedDataFrame.replace('None', np.nan).astype("float").min().min())
    minvalue = min(minnumbers)

    # Get the range of the plot based on min and maxvalues
    rangevalue = maxvalue - minvalue

    if len(parsed_data) <= 2:
        test = 'utest'
    if len(parsed_data) > 2:
        test = 'dunntest'

    ####################### Graph parameters #################################
    # Adaptive colors
    adaptiveColors = ["#f27a63", "#9693db", "#a0c55b", "#59b8d0", "#f29d57", "#c281d1", "#60c57d", "#5e889e", "#82bfec",
                      "#f594bf", "#cdc35f", "#a4bfb8", "#ff8b8c", "#7aa6ff", "#64cfbc", "#ffca60", "#cf9b60", "#c96552",
                      "#7d7ab6", "#85a44c", "#4a99ad", "#c98248", "#a16bae", "#50a468", "#94908d", "#6c9fc4", "#cc7b9f",
                      "#aaa24f", "#889f99", "#d47474", "#658ad4", "#53ac9c", "#d4a850", "#ac8150"]

    # Adaptive colors 10% darker
    adaptiveColors2 = ["#D9614A", "#7D7AC2", "#87AC42", "#409FB7", "#D9843E", "#A968B8", "#47AC64", "#456F85",
                       "#69A6D3", "#DC7BA6", "#B4AA46", "#8BA69F", "#E67273", "#7AA6FF", "#4BB6A3", "#E6B147",
                       "#E6B147", "#B04C39", "#64619D", "#6C8B33", "#318094", "#B0692F", "#885295", "#378B4F",
                       "#7B7774", "#5386AB", "#B36286", "#918936", "#6F8680", "#BB5B5B", "#4C71BB", "#3A9383",
                       "#BB8F37", "#AC8150"]

    boxColorOrder = []
    if config_boxpalette != None:
        for each in config_boxpalette:
            boxColorOrder.append(adaptiveColors[each])
    else:
        boxColorOrder = adaptiveColors

    dotColorOrder = []
    if config_dotpalette != None:
        for each in config_dotpalette:
            dotColorOrder.append(adaptiveColors2[each])
    else:
        dotColorOrder = adaptiveColors2

    sns.set(context='notebook',
            style='whitegrid',
            font_scale=1)  # font='Open Sans Semibold'

    sns.utils.axlabel(xlabel="SAMPLE GROUP",
                      ylabel=y_label,
                      fontsize=16)

    sns.plt.title(config_title)

    # Colored boxplots
    if config_boxplots is True and config_boxcolors is True:
        if 'utest' in test:
            boxplot1 = sns.boxplot(data=parsedDataFrame,
                                   whis=np.inf,
                                   order=plotOrder,
                                   palette=boxColorOrder,
                                   width=0.15,
                                   linewidth=2)

        if 'dunntest' in test:
            boxplot1 = sns.boxplot(data=parsedDataFrame,
                                   whis=np.inf,
                                   order=plotOrder,
                                   palette=boxColorOrder,
                                   width=0.3,
                                   linewidth=2)
            # X-label rotation
            plt.xticks(rotation=config_xrotation)

    # Blank box plots
    if config_boxplots is True and config_boxcolors is False:
        boxplot1 = sns.boxplot(data=parsedDataFrame,
                               whis=np.inf,
                               order=plotOrder,
                               width=0.3)
        plt.setp(boxplot1.artists,
                 linewidth=2,
                 fill=False)

    # Colored dots
    if config_stripplots is True and config_dotcolors is True:
        # Strip plot looks beest with a bunch of data points
        sns.stripplot(data=parsedDataFrame,
                      size=7,
                      linewidth=1,
                      jitter=config_jitter,
                      edgecolor="gray",
                      order=plotOrder,
                      palette=dotColorOrder,
                      clip_on=True)
    # Black dots
    if config_stripplots is True and config_dotcolors is False:
        # Strip plot looks beest with a bunch of data points
        sns.stripplot(data=parsedDataFrame,
                      size=5,
                      color='k',
                      edgecolor="grey",
                      linewidth=0.25,
                      jitter=config_jitter,
                      order=plotOrder,
                      clip_on=True)

    # Significance annotation
    if config_annotation is True:
        # If Utest
        if 'utest' in test:
            # Open stats files from R, look for the test type
            try:
                with open('post_stats_' + file_name_var + '.tsv') as csvfile:
                    reader = csv.reader(csvfile, delimiter='\t')
                    # Scan each row for the type of test that was done (Utest or Dunntest)
                    for row in reader:
                        if 'utest' in row and 'TRUE' in row:
                            # Turn the row into a dataframe
                            df = pd.DataFrame(row).transpose()
                            df.columns = ["test", "correction", "comparison", "pvalue", "significant"]
                            df["pvalue"] = float(df["pvalue"])
                            df["significant"] = bool('True')

                            # set the rowsoftruth
                            rowsoftruth = df
                            rowsoftruth = rowsoftruth.reset_index(drop=True)

                            # initialize a dicitonary to store y coordinates for the annotations
                            ycoord = dict()
                            # Make an empty significance bar for each true significnace column
                            for i in range(len(rowsoftruth)):
                                ycoord[i] = ''

                            # Calculate and store y-coordinates
                            for bar in ycoord:
                                # make the first bar a little higher than the highest data point
                                if bar is 0:
                                    ycoord[bar] = maxvalue + (rangevalue * 0.05)
                                # make each bar 10% higher than the last one
                                else:
                                    oldbar = bar - 1
                                    ycoord[bar] = ycoord[oldbar] + (rangevalue * 0.1)

                            # Get groups from plotOrder
                            groups = [x for x in plotOrder]
                            # translate group names into X coordinates
                            x1 = translator[groups[0]] + 0.05  # + for a little offset
                            x2 = translator[groups[1]] - 0.05  # - for offset
                            # Set y coordinates for vertical ticks

                            y1 = ycoord[i] - rangevalue * 0.01
                            y2 = ycoord[i]
                            # set asterisk position
                            asterisk = (x1 + x2) / 2

                            # Plot significance annotation
                            plt.plot([x1, x1, x2, x2],
                                     [y1, y2, y2, y1],
                                     color='k',
                                     linewidth=1)

                            # Asterisks (based on significance), centered above the bar
                            if rowsoftruth['pvalue'][i] <= 0.05:
                                plt.annotate('* * *', xy=(asterisk, ycoord[i]))
                            elif rowsoftruth['pvalue'][i] <= 0.05:
                                plt.annotate('* *', xy=(asterisk, ycoord[i]))
                            elif rowsoftruth['pvalue'][i] <= 0.05:
                                plt.annotate('*', xy=(asterisk, ycoord[i]))

            except FileNotFoundError as e:
                error_log("Could not plot significance annotations because " + str(e))


        # if Dunntest and only three groups do it this way (Sized differently for 3 groups)
        elif 'dunntest' in test and len(filtered) == 3:
            rowsoftruth = pd.DataFrame()
            # Open stats files from R, look for the test type
            try:
                csvfile = open('post_stats_' + file_name_var + '.tsv')
                reader = csv.reader(csvfile, delimiter='\t')
                # Scan each row for the type of test that was done (Utest or Dunntest)
                for row in reader:
                    if 'dunntest' in row and 'TRUE' in row:
                        # Turn the row into a dataframe
                        df = pd.DataFrame(row).transpose()
                        df.columns = ["test", "correction", "comparison", "pvalue", "significant"]
                        df["pvalue"] = float(df["pvalue"])
                        df["significant"] = bool('True')
                        rowsoftruth = rowsoftruth.append(df)
                    try:
                        rowsoftruth = rowsoftruth.ix[rowsoftruth['correction'] == config_correction, :]
                        # reset the index numbers
                        rowsoftruth = rowsoftruth.reset_index(drop=True)
                    except KeyError:
                        pass  # rowsoftruth is empty (maybe becasue there were no significant values)
            except FileNotFoundError as e:
                error_log("Could not plot significance annotation because " + str(e))
            finally:
                csvfile.close()
            # initialize a dicitonary to store y coordinates for the annotations
            ycoord = dict()

            # Make an empty significance bar for each true significnace column
            for i in range(len(rowsoftruth)):
                ycoord[i] = ''

            # Calculate and store y-coordinates
            for bar in ycoord:
                # make the first bar a little higher than the highest data point
                if bar is 0:
                    ycoord[bar] = maxvalue + (rangevalue * 0.05)
                # make each bar 10% higher than the last one
                else:
                    oldbar = bar - 1
                    ycoord[bar] = ycoord[oldbar] + (rangevalue * 0.1)

            # Initialize a list to store the comparison groups from R
            splitcomp = []
            # Loop through the rows that are TRUE if there are any
            try:
                for i, comparison in enumerate(rowsoftruth['comparison']):
                    # Split the comparison columns into group names and sort
                    splitcomp = sorted(comparison.split(" - "))
                    # translate group names into X coordinates
                    x1 = translator[splitcomp[0]] + 0.1  # + for a little offset
                    x2 = translator[splitcomp[1]] - 0.1  # - for offset
                    y1 = ycoord[i] - rangevalue * 0.01
                    y2 = ycoord[i]
                    yasterisk = ycoord[i] - rangevalue * 0.015
                    asterisk = (x1 + x2) / 2
                    # Plot significance annotation
                    plt.plot([x1, x1, x2, x2],
                             [y1, y2, y2, y1],
                             color='k',
                             linewidth=1,
                             alpha=1)
                    # Asterisks (based on significance), centered above the bar
                    if float(rowsoftruth['pvalue'][i]) <= 0.001:
                        plt.annotate('* * *', xy=(asterisk, yasterisk))
                    elif float(rowsoftruth['pvalue'][i]) <= 0.01:
                        plt.annotate('* *', xy=(asterisk, yasterisk))
                    elif float(rowsoftruth['pvalue'][i]) <= 0.05:
                        plt.annotate('*', xy=(asterisk, yasterisk))
            except KeyError:
                pass  # rowsoftruth is empty (maybe becasue there were no significant values)


        # If there are more than three groups, do it this way (sized differently)
        elif "dunntest" in test and len(filtered) >= 4:

            df = pd.read_csv('post_stats_' + file_name_var + '.tsv', sep="\t", header=None, index_col=None,
                             true_values=['TRUE'], false_values=['FALSE'], na_values=['', ' '], na_filter=False)
            # Parse the test rows
            df = df[(df.ix[:, 0] == test)]
            # Parse the the values from config_correction method
            df = df[(df.ix[:, 1] == config_correction)]

            # Remove extra columns
            df.drop(df.columns[5:], axis=1, inplace=True)
            # get the test rows with true significance
            rowsoftruth = df[(df[4] == "TRUE")]
            # Set the column names
            rowsoftruth.columns = ["test", "correction", "comparison", "pvalue", "significant"]
            # reset the index numbers
            rowsoftruth = rowsoftruth.reset_index(drop=True)

            # initialize a dicitonary to store y coordinates for the annotations
            ycoord = dict()
            # Make an empty significance bar for each true significnace column
            for i in range(len(rowsoftruth)):
                ycoord[i] = ''

            # Calculate and store y-coordinates
            for bar in ycoord:
                # make the first bar a little higher than the highest data point
                if bar is 0:
                    ycoord[bar] = maxvalue + (rangevalue * 0.05)
                # make each bar 10% higher than the last one
                else:
                    oldbar = bar - 1
                    ycoord[bar] = ycoord[oldbar] + (rangevalue * 0.1)

            # Initialize a list to store the comparison groups from R
            splitcomp = []

            # Loop through the rows that are TRUE
            for i, comparison in enumerate(rowsoftruth['comparison']):

                # Split the comparison columns into group names and sort
                splitcomp = sorted(comparison.split(" - "))
                # Strip first character from group name
                if config_order == True:
                    splitcomp = [comp[1:] for comp in splitcomp]

                # translate group names into X coordinates
                x1 = translator[splitcomp[0]] + 0.1  # + for a little offset
                x2 = translator[splitcomp[1]] - 0.1  # - for offset
                y1 = ycoord[i] - rangevalue * 0.01
                y2 = ycoord[i]
                yasterisk = ycoord[i] - rangevalue * 0.015
                asterisk = (x1 + x2) / 2

                # Plot significance annotation
                plt.plot([x1, x1, x2, x2],
                         [y1, y2, y2, y1],
                         color='k',
                         linewidth=1,
                         alpha=1)
                # Asterisks (based on significance), centered above the bar
                if float(rowsoftruth['pvalue'][i]) <= 0.001:
                    plt.annotate('* * *', xy=(asterisk, yasterisk))
                elif float(rowsoftruth['pvalue'][i]) <= 0.01:
                    plt.annotate('* *', xy=(asterisk, yasterisk))
                elif float(rowsoftruth['pvalue'][i]) <= 0.05:
                    plt.annotate('*', xy=(asterisk, yasterisk))

    # Mean bars
    if config_meanbars is True:
        # Get mean and SEM from post_stats files
        means, SEM, sd = parse_SEM(file_name_var)

        # Create dictionaries for mean bars
        means_data = dict(zip(plotOrder, means))
        # Make a sorted list and loop through it
        n = len(means)
        count = 1
        for group in plotOrder:
            value = means_data[group]

            if 'utest' in test:
                # Set the right and left positions
                right = (count / n)
                right_offset = right - 1 / n * 0.35
                left = right - (1 / n)
                left_offset = left + 1 / n * 0.35
                plt.axhline(y=value,
                            xmin=left_offset,
                            xmax=right_offset,
                            color='k',
                            linewidth=3,
                            zorder=100)

            if 'dunntest' in test:
                # Set the right and left positions
                right = (count / n)
                right_offset = right - 1 / n * 0.25
                left = right - (1 / n)
                left_offset = left + 1 / n * 0.25
                plt.axhline(y=value,
                            xmin=left_offset,
                            xmax=right_offset,
                            color='k',
                            linewidth=3,
                            zorder=100)
            count += 1

    # Black standard deviation bars
    if 'sd' in config_errorbars:

        # Get mean and sd from post_stats files (get SEM too, but don't use it here)
        means, SEM, sd = parse_SEM(file_name_var)

        # Create dictionaries for mean and SEM bars
        means_data = dict(zip(plotOrder, means))
        sd_data = dict(zip(plotOrder, sd))

        # Loop through the plotOrder and use them as keys
        for key in plotOrder:

            # Set the Standard deviation
            error = sd_data[key]

            # Use U-test sized bars
            if 'utest' in test:

                # Plot the error bar
                plt.errorbar(x=translator[key],
                             y=means_data[key],
                             yerr=error,
                             marker=None,
                             capthick=1,
                             capsize=15,
                             alpha=1,
                             linewidth=1,
                             barsabove=True,
                             zorder=100,  # zorder makes the bars render on top
                             color='k')

            # Use Dunn test-sized bars
            elif 'dunntest' in test:
                # Plot the error bar
                plt.errorbar(x=translator[key],
                             y=means_data[key],
                             yerr=error,
                             marker=None,
                             capthick=1,
                             capsize=8,
                             alpha=1,
                             linewidth=1,
                             barsabove=True,
                             zorder=100,  # zorder makes the bars render on top
                             color='k')

    # Black standard error of mean bars
    if 'sem' in config_errorbars:

        # Get mean and SEM from post_stats files
        means, SEM, sd = parse_SEM(file_name_var)
        # Create dictionaries for mean and SEM bars
        means_data = dict(zip(plotOrder, means))
        sem_data = dict(zip(plotOrder, SEM))

        # oop through the plotOrder and use them as keys
        for key in plotOrder:
            # Set the SEM
            error = sem_data[key]

            # Use U-test sized bars
            if 'utest' in test:
                # Plot the error bar
                plt.errorbar(x=translator[key],
                             y=means_data[key],
                             yerr=error,
                             marker=None,
                             capthick=1,
                             capsize=15,
                             alpha=1,
                             linewidth=1,
                             barsabove=True,
                             zorder=100,  # zorder makes the bars render on top
                             color='k')
            # Use Dunn test-sized bars
            elif 'dunntest' in test:
                # Plot the error bar
                plt.errorbar(x=translator[key],
                             y=means_data[key],
                             yerr=error,
                             marker=None,
                             capthick=1,
                             capsize=8,
                             alpha=1,
                             linewidth=1,
                             barsabove=True,
                             zorder=100,  # zorder makes the bars render on top
                             color='k')

    # Set the plot scale for clonality/tcell based on the file_name_var
    if file_name_var is 'clonality' or file_name_var is 'tcell':
        if minvalue > 0.1 and maxvalue < 0.9:
            plt.autoscale(enable=True, axis='y', tight=True)
        if minvalue <= 0.1:
            plt.ylim(ymin=0)
        if maxvalue >= 0.9:
            plt.ylim(ymax=1)
        # Save the graph
        try:
            fig = plt.gcf()
            fig.set_size_inches(config_width, config_height)
            fig.savefig(graph_name, bbox_inches="tight", dpi=config_dpi)
            plt.show()
            plt.close()
        except PermissionError:
            if '\\' in graph_name:
                error_log(
                    "Permission Error in plt.savefig(). Make sure the metadata headers contain only valid characters and that the file is not in use by another program.")
                pass

    # Set the plot scale for arbitrary data based on the file_name_var
    if 'arb' in file_name_var:
        plt.autoscale(enable=True, axis='y', tight=True)

        if config_logscale is True:
            plt.yscale('log', subsy=[2, 3, 4, 5, 6, 7, 8, 9])
            plt.autoscale(enable=True, axis='y', tight=True)
            plt.grid(which='minor')

        # Save the graph
        try:
            fig = plt.gcf()
            fig.set_size_inches(config_width, config_height)
            plt.savefig(graph_name, bbox_inches="tight", dpi=config_dpi)
            plt.show()
            plt.close()
        except PermissionError:
            if '\\' in graph_name:
                error_log(
                    "Permission Error in plt.savefig(). Make sure the metadata headers contain only valid characters and that the file is not in use by another program.")
                pass


def delete_old_files(pre=False, post=False, errorlog=False):
    """Remove old files before running"""
    if pre == True:
        # Remove pre_stat files
        try:
            pre_files = glob.glob("pre_*.tsv")
            for f in pre_files:
                os.remove(f)
        except FileNotFoundError:
            # The file doesn't exist so don't worry about deleting it
            pass

    if post == True:
        # Remove old post file
        try:
            post_files = glob.glob("post_*.tsv")
            for f in post_files:
                os.remove(f)
        except FileNotFoundError:
            # The file doesn't exist so don't worry about deleting it
            pass

    if errorlog == True:
        # Remove error log
        try:
            os.remove('error.log')
        except FileNotFoundError:
            # File doesn't exist
            pass


def create_master_file(config_masterfile):
    """Concatenate output files into one file if the option is true"""
    if config_masterfile is True:
        read_files = glob.glob("post_stats_*.tsv")
        with open("post_stats_complete.tsv", "w") as outfile:
            for f in read_files:
                with open(f, "r") as infile:
                    metric_name = (f.strip(".tsv").split("_")[2])
                    outfile.write(metric_name.upper() + "\n" + infile.read() + "\n")


def error_log(errornote):
    """Write errors and exceptions to a log file"""
    errortime = time.strftime('%Y%m%d %H:%M:%S')
    errorstring = str(errortime + ' -- ' + errornote + "\n")
    with open("error.log", "a") as error_log:
        error_log.write(errorstring)



if __name__ == "__main__":
    main()
