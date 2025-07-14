import multiprocessing
import vehicle_detection
import green_time_signal

if __name__ == "__main__":
    processes = [
        multiprocessing.Process(target=vehicle_detection.main),
        multiprocessing.Process(target=green_time_signal.main),
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join()