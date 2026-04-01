import argparse
from launch_ft import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('N', action="store", default=1, type=int,
                        help="Number of cores used for simulation multiprocessing")
    args = parser.parse_args()

    main(args.N, part='1')
