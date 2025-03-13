import os
import subprocess
import json
import sys
import re
import multiprocessing

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

    '''def trancodeMedia(self, mediaOutputDir):
        for mediaFile, existingCodec in self.mediaToTranscode:
            filePath = mediaFile
            trimmedFilePath = os.path.splitext(os.path.basename(filePath))[0]
            transcodedFilePath = os.path.join(mediaOutputDir, f"{trimmedFilePath} - transcoded AV1.mkv")

            print(f"Processing {filePath}")
            print(f"Output: {transcodedFilePath}")

            if existingCodec.lower() == "av1":
                print(f"{filePath} is already AV1")
                continue

            try:
                subprocess.run([
                    "ffmpeg", "-y", "-i", filePath, "-c:v", "libaom-av1",
                    "-crf", "30", "-b:v", "0", "-cpu-used", "4",
                    "-c:a", "copy", "-f", "matroska", transcodedFilePath
                ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Successfully transcoded: {transcodedFilePath}")
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg error: {e.stderr.decode()}")
'''

    '''def transcodeMedia(self, mediaOutputDir):
        for mediaFile, existingCodec in self.mediaToTranscode:
            filePath = mediaFile
            trimmedFilePath = os.path.splitext(os.path.basename(filePath))[0]
            transcodedFilePath = os.path.join(mediaOutputDir, f"{trimmedFilePath} - transcoded AV1.mkv")

            print(f"Processing {filePath}")
            print(f"Output: {transcodedFilePath}")

            if existingCodec.lower() == "av1":
                print(f"{filePath} is already AV1")
                continue

            try:
                process = subprocess.Popen([
                    "ffmpeg", "-y", "-i", filePath, "-c:v", "libaom-av1",
                    "-crf", "30", "-b:v", "0", "-cpu-used", "4",
                    "-c:a", "copy", "-f", "matroska", transcodedFilePath
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

                # Read and print ffmpeg progress in real-time
                for line in iter(process.stdout.readline, ''):
                    if "frame=" in line or "time=" in line or "bitrate=" in line:
                        print(line.strip())  # Print only relevant progress info

                process.stdout.close()
                process.wait()

                if process.returncode == 0:
                    print(f"Successfully transcoded: {transcodedFilePath}")
                else:
                    print(f"Transcoding failed for: {filePath}")

            except subprocess.CalledProcessError as e:
                print(f"FFmpeg error: {e.stderr.decode()}")
'''

    def transcode_single_file(mediaFile, existingCodec, mediaOutputDir):
        filePath = mediaFile
        trimmedFilePath = os.path.splitext(os.path.basename(filePath))[0]
        transcodedFilePath = os.path.join(mediaOutputDir, f"{trimmedFilePath} - transcoded AV1.mkv")

        print(f"Processing {filePath}")
        print(f"Output: {transcodedFilePath}")

        if existingCodec.lower() == "av1":
            print(f"{filePath} is already AV1")
            return

        # Get video duration using ffprobe
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", filePath],
                capture_output=True, text=True, check=True
            )
            total_duration = float(result.stdout.strip())  # Video duration in seconds
        except Exception:
            total_duration = None  # If duration cannot be determined, progress will be unknown

        try:
            # CPU mask: 0xFFFFFFF (24 cores, cores 0-23)
            taskset_command = [
                "taskset", "-c", "0-23", "ffmpeg", "-y", "-i", filePath, "-c:v", "libaom-av1",
                "-crf", "30", "-b:v", "0", "-cpu-used", "4",
                "-c:a", "copy", "-f", "matroska", transcodedFilePath
            ]

            process = subprocess.Popen(
                taskset_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            # Regex to extract progress time from ffmpeg logs
            time_pattern = re.compile(r"time=(\d+:\d+:\d+\.\d+)")

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break

                match = time_pattern.search(output)
                if match and total_duration:
                    # Convert HH:MM:SS.ms to seconds
                    time_str = match.group(1)
                    h, m, s = map(float, time_str.split(':'))
                    elapsed_time = h * 3600 + m * 60 + s
                    progress = (elapsed_time / total_duration) * 100

                    # Print progress on the same line
                    sys.stdout.write(f"\rProgress: {progress:.2f}%")
                    sys.stdout.flush()

            process.wait()

            print()  # Move to the next line after progress is done

            if process.returncode == 0:
                print(f"Successfully transcoded: {transcodedFilePath}")
            else:
                print(f"Transcoding failed for: {filePath}")

        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")

    def transcodeMedia(self, mediaOutputDir):
        # Creating a pool of processes to handle multiple files simultaneously
        with multiprocessing.Pool(processes=multiprocessing.cpu_count() - 4) as pool:
            # Use pool.starmap to pass arguments to the function, using a lambda to explicitly pass self
            pool.starmap(
                lambda mediaFile, existingCodec, mediaOutputDir: self.transcode_single_file(mediaFile, existingCodec,
                                                                                            mediaOutputDir),
                [(mediaFile, existingCodec, mediaOutputDir) for mediaFile, existingCodec in self.mediaToTranscode])

    def printMedia(self): # for debugging
        for mediaFile, existingCodec in self.mediaToTranscode:
            print(mediaFile)

# /mnt/ironwolf/testing/input

def main():
    mediaInputDir = input("Enter the directory to scan: ")
    os.makedirs(mediaInputDir, exist_ok=True)
    mediaOutputDir = input("Enter the directory to output transcoded media files: ")
    os.makedirs(mediaOutputDir, exist_ok=True)

    transcoder = MediaTranscoder()

    transcoder.scanMedia(mediaInputDir)
    transcoder.transcodeMedia(mediaOutputDir)
    #transcoder.printMedia() # for debugging

if __name__ == "__main__":
    main()