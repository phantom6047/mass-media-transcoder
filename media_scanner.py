import os



def main():
    mediaInputDir = input("Enter the directory to scan: ")
    os.makedirs(mediaInputDir, exist_ok=True)
    mediaOutputDir = input("Enter the directory to output transcoded media files: ")
    os.makedirs(mediaOutputDir, exist_ok=True)



if __name__ == "__main__":
    main()