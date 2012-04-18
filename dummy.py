from __future__ import print_function

def main():
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('Interrupted by user')
    sys.exit(1)
