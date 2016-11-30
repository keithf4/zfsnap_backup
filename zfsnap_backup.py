import argparse, logging, os, os.path, subprocess, sys, time
from datetime import timedelta

parser = argparse.ArgumentParser(description="Backup zfSnap 1.x snapshots to files.")
parser.add_argument('-b', '--backup_folder', help="Destination for backup files.")
parser.add_argument('-r', '--recipient', help="GPG encryption recipients. If multiple recipients are required, set a group alias in gpg.conf")
parser.add_argument('-l', '--logfile', help="Set the file to log the backup process output to. If not given, all output is sent to STDOUT.")
parser.add_argument('-m', '--mount_file', help="File that contains a return-separated list of mount points to backup snapshots for.")
parser.add_argument('--lock_file', default="/tmp/zfsnap_backup.py.lock", help="Lock file to prevent concurrent running of backups. Defaults to /tmp/zfsnap_backup.py.lock")
parser.add_argument('--debug', action="store_true", help="Give more verbose output of internal actions")

args = parser.parse_args()

# option to read a given file that contains a list of zfs mounts to backup snapshots for
# option for backup destination location
# option to select which expiration interval to use as the base backup (1m)
  # incremental snapshot should check its timestamp is after base that is being used
# option to gpg encrypt all files in given destination location
    # options for 

def check_lock(logging):
    if os.path.isfile(args.lock_file):
        logging.critical("ERROR: Lock file already exists (may get left if previous run failed): %s" % args.lock_file)
        if args.logfile != None:
            print("ERROR: Lock file already exists (may get left if previous run failed): %s" % args.lock_file)
        sys.exit(2)
        else:
            open(args.lock_file, 'w+').close()


def cleanup():
    if os.path.exists(args.lock_file):
        os.remove(args.lock_file)


def create_gpg_list(target_folder, logging):
    gpg_list = []
    files_to_encrypt = []
    file_list = [ os.path.join(target_folder,f) for f in os.listdir(target_folder) if os.path.isfile(os.path.join(target_folder,f)) ]
    if args.debug:
        logging.debug("\nFULL FILE LIST:")
        for f in file_list:
            logging.debug(f)
    for f in file_list:
        if re.search('\.gpg$', f):
            gpg_list.append(f)

    if args.debug:
        logging.debug("\nGPG FILE LIST: ")
        for f in gpg_list:
            logging.debug(f)
    for f in file_list:
        if re.search('\.gpg$', f):
            continue
        if (f + ".gpg") in gpg_list:
            # gpg file already exists for this file
            logging.debug("GPG FILE ALREADY EXISTS FOR: " + f)
            continue
        else:
#            mtime_date = time.strftime('%Y-%m-%d', time.localtime(os.stat(f).st_mtime))
#            now_date = time.strftime('%Y-%m-%d', time.localtime())
#            logging.debug("\nFILE MOD TIMES:")
#            logging.debug("file: " + f + ", mtime_date: " + mtime_date + ", now_date: " + now_date)
#            if mtime_date == now_date:
#                # Don't touch today's backup since it may still be running
#                continue
#            else:
            files_to_encrypt.append(f)

    if args.debug:
        logging.debug("\nFILES TO BE ENCRYPTED:")
        for f in files_to_encrypt:
            logging.debug(f)
    return(files_to_encrypt)


def encrypt_files(file_list, logging):
    for f in file_list:
        # If not using external shell call, the gpg key alias is not recognized. 
        # "f" is validated to be a real file, and quotes are added around filename, so should be minimal risk
        gpg_cmd = ["gpg --encrypt -r " + args.recipient + " \"" + f + "\""]
        logging.info("Encrypting file with command: " + str(gpg_cmd))
        if not args.dryrun:
            subprocess.check_call(gpg_cmd, shell=True)


def get_mount_list(logging):
    mount_list = []
    try:
        fh = open(args.mount_file, 'r', encoding='utf-8')
        for line in fh:
            if not line.strip().startswith('#'):
                mount_list.append(line.strip())
    except IOError as e:
        print("Cannot open mount file" + args.mount_file + ": " + e.strerror)
        sys.exit(2)
    return(mount_list)


def sigint_handler(signum, frame):
    cleanup()
    sys.exit(2)


if __name__ == "__main__":
    if args.debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO

    if args.logfile != None:
        logging.basicConfig(filename=args.logfile, level=loglevel, filemode='w', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    else:
        logging.basicConfig(level=loglevel, format='%(asctime)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info("Starting S3 Backup Sync...")
    check_lock(logging)
    signal.signal(signal.SIGINT, sigint_handler)
    # zfs sends done here
    files_to_encrypt = create_gpg_list(args.backup_folder, logging)
    encrypt_files(files_to_encrypt, logging)

    cleanup()
    logging.info("Done")


