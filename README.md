```
Python CodeEasy (pyce)

This sample code implements a number of storage operations around volume,
snapshot, and flexclone management.  This is based off the Perl implementation
of the NetApp CodeEasy framework of scripts.

Requirements:
  1. Configure pyceConfig.py with your storage system related details.
  2. Install the NetApp python API modules in a directory named NMSDKpy.

Run "./pyce.py -h" to see usage and examples.

Usage: pyce.py [options]

Options:
  --version     show program's version number and exit
  -h, --help    show this help message and exit
  -o OPERATION  operation type (see below)
  -v VOLUME     volume name
  -j JUNCTION   junction path
  -s SNAPSHOT   snapshot name
  -c CLONE      clone name
  -d            debug mode

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
```
