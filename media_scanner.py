import os
import subprocess
import json

class MediaTranscoder:
    def __init__(self):
        self.mediaToTranscode = []

    def getCodec(self, mediaPath):
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name", "-of",
                 "json", mediaPath],
                capture_output=True,
                text=True,
                check=True
            )

            data = json.loads(result.stdout)
            if 'streams' in data and data['streams']:
                return data['streams'][0]['codec_name']

        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
            print(f"Error analyzing {mediaPath}: {e}")

        return None

    #update to scan recusively later
    def scanMedia(self, inputDir):
        self.mediaToTranscode = []

        for mediaFolder in os.listdir(inputDir):
            mediaPath = os.path.join(inputDir, mediaFolder)

            if os.path.isdir(mediaPath):  # Ensure it's a directory
                for subDir in os.listdir(mediaPath):
                    subDirPath = os.path.join(mediaPath, subDir)

                    if os.path.isdir(subDirPath):  # Ensure it's a directory
                        for file in os.listdir(subDirPath):
                            if file.endswith(".mkv"):
                                filePath = os.path.join(subDirPath, file)
                                self.mediaToTranscode.append([filePath, self.getCodec(filePath)])
                                #print(filePath) # for debugging


    def printMedia(self): # for debugging
        for mediaFile in self.mediaToTranscode:
            print(mediaFile)



def main():
    mediaInputDir = input("Enter the directory to scan: ")
    os.makedirs(mediaInputDir, exist_ok=True)
    #mediaOutputDir = input("Enter the directory to output transcoded media files: ")
    #os.makedirs(mediaOutputDir, exist_ok=True)

    transcoder = MediaTranscoder()

    transcoder.scanMedia(mediaInputDir)
    transcoder.printMedia() # for debugging

if __name__ == "__main__":
    main()