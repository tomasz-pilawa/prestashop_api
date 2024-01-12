import argparse
import glob
import os


def load_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", help="Mode to operate the system.", type=str, default='explore', required=False)
    parser.add_argument("--param", help="Brand to explore or CSV filename.", type=str, default=None)
    args = parser.parse_args()

    if args.mode == 'explore':
        return args.mode, args.param or 'Mesoestetic'
    elif args.mode == 'add':
        if not args.param:
            args.param = get_newest_csv_name()
        return args.mode, args.param
    else:
        raise ValueError(f"Unknown mode '{args.mode}'.")


def get_newest_csv_name():

    base_dir = os.path.abspath(os.path.dirname(__file__))
    parent_dir = os.path.abspath(os.path.join(base_dir, os.pardir))
    csv_folder = os.path.join(parent_dir, 'data', 'logs')
    csv_filenames = sorted(glob.glob(os.path.join(csv_folder, '*.csv')), reverse=True)
    csv_filename = csv_filenames[0] if csv_filenames else None
    basename = os.path.basename(csv_filename)
    filename, ext = os.path.splitext(basename)

    return filename

