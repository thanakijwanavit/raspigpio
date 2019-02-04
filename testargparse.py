import argparse
import sys

try:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type = int, help="number of samples to take", default=10)
    parser.add_argument('--save_dir', type = str, default = 'saved_classifier/checkpoint.pth',
                    help = 'path to save the trained model')
    args = parser.parse_args()

    #print the square of user input from cmd line.
    print("take {samples} samples".format(samples=args.samples))

    #print all the sys argument passed from cmd line including the program name.
    #print (sys.argv)

    #print the second argument passed from cmd line; Note it starts from ZERO
    #print (sys.argv[1])
except:
    e = sys.exc_info()[0]
    print (e)
    
 