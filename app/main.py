import time

def allocate_memory():
    print("Starting application...")
    # Allocate a large list to consume memory
    large_list = []
    print("Allocating memory...")
    try:
        # Create blocks of memory continuously to trigger OOM
        while True:
            large_list.append(' ' * 10**7) # 10MB blocks
            time.sleep(0.1)
    except MemoryError:
        print("Out of memory error!")
        raise

if __name__ == "__main__":
    allocate_memory()
