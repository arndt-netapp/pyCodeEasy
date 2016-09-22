#!/usr/bin/env python

################################################################################
#
# Python CodeEasy (pyce)
#
# This sample code implements a number of storage operations around volume,
# snapshot, and flexclone management.  This is based off the Perl implementation
# of the NetApp CodeEasy framework of scripts.
#
# Requirements:
#   1. Configure pyceConfig.py with your storage system related details.
#   2. Install the NetApp python API modules in a directory named NMSDKpy.
#
# Run "./pyce.py -h" to see usage and examples.
#
################################################################################

import sys
sys.path.append("NMSDKpy")
from NaServer import *
from optparse import OptionParser
import pyceConfig
import datetime
version="1.0"

def NaConnect():

    s = NaServer(pyceConfig.ce_cluster, pyceConfig.ce_ontapi_major_version, pyceConfig.ce_ontapi_minor_version)
    s.set_server_type(pyceConfig.ce_server_type)

    # set communication style - typically just 'LOGIN'
    resp = s.set_style(pyceConfig.ce_style)
    if (resp and resp.results_errno() != 0) :
        r = resp.results_reason()
        print ("Failed to set authentication style " + r + "\n")
        sys.exit (2)

    # pass username/password for vserver ontapi application access
    s.set_admin_user(pyceConfig.ce_user, pyceConfig.ce_passwd)
    # set API transport type - HTTP is the default
    resp = s.set_transport_type(pyceConfig.ce_transport)
    if (resp and resp.results_errno() != 0) :
         r = resp.results_reason()
         print ("Unable to set HTTP transport " + r + "\n")
         sys.exit(2)

    # specify which vserver to access
    s.set_vserver(pyceConfig.ce_vserver)
    # set communication port
    s.set_port(pyceConfig.ce_port)

    # return storage object
    return s


def get_version(na):
    api = NaElement("system-get-version")
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)

    ontap_version = output.child_get_string("version")
    return ontap_version


def list_volumes(na, volume):

    # Get first set of mrecs (100) records
    print("Getting list of volumes that match: " + volume)
    print("")
    print("{:<24} {:<40} {:>10} {:>10} {:>10} {:>12}"\
    .format("Volume Name", "Junction Path", "Size (GB)", "Used (GB)", "Saved (GB)", "Logical (GB)"))
    print("---------------------------------------------------------------------------------------------------------------")
    mrecs = "100"
    api = NaElement("volume-get-iter")
    api.child_add_string("max-records", mrecs)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)

    # Set up to get next set of records
    tag = output.child_get_string("next-tag")

    # Loop through results and print as we go
    while True:
        # get list of volume-info attributes
        vollist = dict()
        vollist = output.child_get("attributes-list")
        if (vollist == None):
            break
    
        # Loop through list of volumes and print out desired attrs
        for vol in vollist.children_get():
            # get volume attributes (which includes volume name)
            id_attrs     = vol.child_get("volume-id-attributes")
            volname      = id_attrs.child_get_string("name")
            if volume in volname:
                junc_path    = id_attrs.child_get_string("junction-path")
                space_attrs   = vol.child_get("volume-space-attributes")
                sis_attrs     = vol.child_get("volume-sis-attributes")
                size          = space_attrs.child_get_string("size")
                used          = space_attrs.child_get_string("size-used")
                saved         = 0
                if str(sis_attrs) is not "None":
                    saved  = sis_attrs.child_get_string("total-space-saved")
                size  = int(size) / (1024*1024*1024)
                used  = int(used) / (1024*1024*1024)
                saved = int(saved) / (1024*1024*1024)
                logical = used + saved;
                print("{:<24} {:<40} {:>10} {:>10} {:>10} {:>12}".format(volname, junc_path, size, used, saved, logical))

        # get next set of records
        api = NaElement("volume-get-iter")
        api.child_add_string("max-records", mrecs)
        api.child_add_string("tag", tag)
        output = na.invoke_elem(api)
        if(output.results_status() == "failed"):
            r = output.results_reason()
            print("Failed: " + str(r))
            sys.exit(2)

        # Get next tag which indicates if there are more records
        tag = output.child_get_string("next-tag")
        if (tag == None):
            break


def create_volume(na, volume, junction_path):
    # Create the volume api structure
    api = NaElement("volume-create")
    api.child_add_string("volume", volume)
    api.child_add_string("junction-path", junction_path)
    for key in pyceConfig.ce_volume_create_options:
        value = pyceConfig.ce_volume_create_options[key]
        api.child_add_string(key, value)

    # Create the volume
    print("Creating volume: " + volume + " with junction-path " + junction_path)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Volume created succesfully.")

    # Set maxfiles if required
    try:
        pyceConfig.ce_vol_maxfiles
    except NameError:
      pyceConfig.ce_vol_maxfiles = "0"
    if int(pyceConfig.ce_vol_maxfiles) > 0:
        api = NaElement("volume-set-total-files")
        api.child_add_string("volume", volume)
        api.child_add_string("requested-total-files", pyceConfig.ce_vol_maxfiles)
        api.child_add_string("force", "true")
        print("Configuring maxfiles on volume " + volume + " with value " + pyceConfig.ce_vol_maxfiles)
        output = na.invoke_elem(api)
        if (output.results_status() == "failed"):
            r = output.results_reason()
            print("Failed: " + str(r))
            sys.exit(2)
        print("Maxfiles configured succesfully.")


def delete_volume(na, volume):
    # Unmount
    api = NaElement("volume-unmount")
    api.child_add_string("force", "true")
    api.child_add_string("volume-name", volume)

    print("Unmounting volume: " + volume)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Volume unmounted.")

    # Offline
    api = NaElement("volume-offline")
    api.child_add_string("name", volume)

    print("Offlining volume: " + volume)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Volume offline.")

    # Delete
    api = NaElement("volume-destroy")
    api.child_add_string("name", volume)

    print("Destroying volume: " + volume)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Volume destroyed.")


def remount_volume(na, volume, junction_path):
    # Unmount
    api = NaElement("volume-unmount")
    api.child_add_string("force", "true")
    api.child_add_string("volume-name", volume)

    print("Unmounting volume: " + volume)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Volume unmounted.")

    # Mount
    api = NaElement("volume-mount")
    api.child_add_string("volume-name", volume)
    api.child_add_string("junction-path", junction_path)

    print("Mounting volume: " + volume + " with junction of " + junction_path)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Volume mounted.")

def list_snapshots(na, volume):
    # Get snapshots
    print("Getting list of snapshots on volume: " + volume)
    api = NaElement("snapshot-list-info")
    api.child_add_string("volume", volume)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)

    # Print snapshot info as we loop through output 
    print("")
    print("{:<32} {:<32} {:<28}".format("Volume Name", "Snapshot Name", "Snapshot Date"))
    print("----------------------------------------------------------------------------------------------")
    snapshots = output.child_get("snapshots")
    if snapshots:
        for snapinfo in snapshots.children_get():
            snapname = snapinfo.child_get_string("name")
            access   = snapinfo.child_get_string("access-time")
            snaptime = datetime.datetime.fromtimestamp(float(access))
            print("{:<32} {:<32} {:<28}".format(snapname,volume,snaptime.strftime('%c')))


def create_snapshot(na, volume, snapshot):
    # Create snapshot
    api = NaElement("snapshot-create")
    api.child_add_string("volume", volume)
    api.child_add_string("snapshot", snapshot)

    print("Creating snapshot " + snapshot + " in volume " + volume)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Created snapshot.")


def delete_snapshot(na, volume, snapshot):
    # Delete snapshot
    api = NaElement("snapshot-delete")
    api.child_add_string("volume", volume)
    api.child_add_string("snapshot", snapshot)

    print("Deleting snapshot " + snapshot + " in volume " + volume)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Deleted snapshot.")


def list_clones(na, volume):
    # Print header
    print("")
    print("{:<24} {:<24} {:<24} {:<24}"\
    .format("Parent Volume", "Parent Snapshot", "FlexClone Volume", "FlexClone Junction"))
    print("----------------------------------------------------------------------------------------------------")

    #----------------------------------------
    # get FlexCone info iteratively - it will return a list
    #----------------------------------------
    # Get First Set of mrecs (100) records
    mrecs = "100"
    api = NaElement("volume-clone-get-iter")
    api.child_add_string("max-records", mrecs)
    output = na.invoke_elem(api)

    if(output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)

    # Set up to get next set of records
    tag = output.child_get_string("next-tag")

    # Add vollist results to list and then Get Following set of records
    # Break from loop when the vollist is None or next-tag is None
    while True:
        # get list of volume-info attributes
        vollist = output.child_get("attributes-list")
        if (vollist == None):
            break

        # for each clone entry
        for vol_data in vollist.children_get():
            volume_name    = vol_data.child_get_string("parent-volume");
            clone_name     = vol_data.child_get_string("volume");
            snapshot       = vol_data.child_get_string("parent-snapshot");
            jpath          = vol_data.child_get_string( "junction-path"  );

            if volume in clone_name:
              # print results
              print("{:<24} {:<24} {:<24} {:<24}"\
              .format(volume_name, snapshot, clone_name, jpath))
  
        # get next set of records
        api = NaElement("volume-get-iter")
        api.child_add_string("max-records", mrecs)
        api.child_add_string("tag", tag)
        output = na.invoke_elem(api)
        if(output.results_status() == "failed"):
            r = output.results_reason()
            print("Failed: " + str(r))
            sys.exit(2)
        
        # Get next tag which indicates if there are more records
        tag = output.child_get_string("next-tag")
        if (tag == None):
            break


def create_clone(na, volume, clone, snapshot, junction_path):
    # Create the volume clone api structure
    api = NaElement("volume-clone-create")
    api.child_add_string("parent-volume", volume)
    api.child_add_string("parent-snapshot", snapshot)
    api.child_add_string("volume", clone)
    api.child_add_string("junction-path", junction_path)
    api.child_add_string("space-reserve", "none")

    # Create the clone
    print("Creating clone volume " + clone + " of parent volume " + volume + " with snapshot " + snapshot + " and junction-path " + junction_path)
    output = na.invoke_elem(api)
    if (output.results_status() == "failed"):
        r = output.results_reason()
        print("Failed: " + str(r))
        sys.exit(2)
    print("Volume clone created succesfully.")


def help_text():
    help_text = """
  The following operation types are supported:
    list_volumes
    create_volume
    delete_volume
    remount_volume
    list_snapshots
    create_snapshot
    delete_snapshot
    list_clones
    create_clone

  Examples
    List all volumes with the string "build" in them:
    %> pyce.py -o list_volumes -v build

    Create a new volume named "build123" with a junction-path of "/builds/build123":
    %> pyce.py -o create_volume -v build123 -j /builds/build123

    Delete a volume or a clone named "build123":
    %> pyce.py -o delete_volume -v build123 

    Remount a volume named "build123" with a junction-path of "/builds/build_current"
    %> pyce.py -o remount_volume -v build123 -j /builds/build_current

    List all snapshots for volume "build123":
    %> pyce.py -o list_snapshots -v build123 
  
    Create a snapshot named "snap1" on volume "build123":
    %> pyce.py -o create_snapshot -v build123 -s snap1

    Delete a snapshot named "snap1" on volume "build123":
    %> pyce.py -o delete_snapshot -v build123 -s snap1

    List all clones with the string "clone" in them:
    %> pyce.py -o list_clones -c clone

    Create a new clone named "build123_clone" from volume "build", using
    snapshot "snap1", and use a junction-path of "/builds/build123_clone":
    %> pyce.py -o create_clone -c build123_clone -v build123 -s snap1 -j /builds/build123_clone
"""

    return help_text

# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

# Parse CLI options
help_text = help_text()
OptionParser.format_epilog = lambda self, formatter: self.epilog
parser = OptionParser(epilog=help_text, version=version)
parser.add_option("-o", dest="operation", help="operation type (see below)")
parser.add_option("-v", dest="volume", help="volume name")
parser.add_option("-j", dest="junction", help="junction path")
parser.add_option("-s", dest="snapshot", help="snapshot name")
parser.add_option("-c", dest="clone", help="clone name")
parser.add_option("-d", dest="debug", action="store_true", help="debug mode")
(options, args) = parser.parse_args()

# Check for a valid operation type.
op = options.operation
operations = ["list_volumes","create_volume","delete_volume","remount_volume",\
              "list_snapshots","create_snapshot","delete_snapshot",\
              "list_clones","create_clone"\
             ]
if not op:
    print("No operation type given.")
    print("Use -h to see usage and examples.")
    sys.exit(2)
if op not in operations:
    print("Invalid operation type: " + op)
    print("Use -h to see usage and examples.")
    sys.exit(2)

# Make sure we have the required arguments for each operation
if op == "list_volumes" or op == "delete_volume" or op == "list_snapshots":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "create_volume" or op == "remount_volume":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.junction:
        print("Missing junction path for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "create_snapshot" or op == "delete_snapshot":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.snapshot:
        print("Missing snapshot name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "list_clones":
    if not options.clone:
        print("Missing clone name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
if op == "create_clone":
    if not options.volume:
        print("Missing volume name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.snapshot:
        print("Missing snapshot name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.clone:
        print("Missing clone name for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)
    if not options.junction:
        print("Missing junction path for op: " + op)
        print("Use -h to see usage and examples.")
        sys.exit(2)

# If we get here, everything should be OK
# Connect to the storage system
print("Connecting to storage system.")
na = NaConnect()
ontap_ver = get_version(na)
print (ontap_ver)

# Call the requested operation
if op == "list_volumes":
    list_volumes(na, options.volume)

if op == "create_volume":
    create_volume(na, options.volume, options.junction)

if op == "delete_volume":
    delete_volume(na, options.volume)

if op == "remount_volume":
    remount_volume(na, options.volume, options.junction)

if op == "list_snapshots":
    list_snapshots(na, options.volume)
   
if op == "create_snapshot":
    create_snapshot(na, options.volume, options.snapshot)

if op == "delete_snapshot":
    delete_snapshot(na, options.volume, options.snapshot)

if op == "list_clones":
    list_clones(na, options.clone)

if op == "create_clone":
    create_clone(na, options.volume, options.clone, options.snapshot, options.junction)
