from PIL import Image
import os
from pathlib import Path
import sys

def compress_image(image_path):
    """Compress an image using PIL's lossless compression."""
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary (for PNG files)
            if img.mode == 'RGBA':
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = background
            
            # Get original file size
            original_size = os.path.getsize(image_path)
            
            # Save with optimization
            img.save(image_path, 'PNG', optimize=True)
            
            # Get new file size
            new_size = os.path.getsize(image_path)
            
            # Calculate compression percentage
            compression = ((original_size - new_size) / original_size) * 100
            
            return True, compression
    except Exception as e:
        return False, str(e)

def process_directory(directory):
    """Process all PNG images in a directory."""
    image_paths = list(Path(directory).rglob('*.png'))
    total_images = len(image_paths)
    processed = 0
    total_saved = 0
    failed = []

    print(f"\nFound {total_images} PNG images to process...")
    
    for image_path in image_paths:
        try:
            success, result = compress_image(image_path)
            if success:
                processed += 1
                total_saved += result
                print(f"Compressed {image_path.name}: {result:.1f}% reduction")
            else:
                failed.append((image_path.name, result))
                print(f"Failed to compress {image_path.name}: {result}")
        except Exception as e:
            failed.append((image_path.name, str(e)))
            print(f"Error processing {image_path.name}: {str(e)}")

    # Print summary
    print(f"\nCompression Summary:")
    print(f"Total images processed: {processed}/{total_images}")
    if processed > 0:
        print(f"Average space saved: {total_saved/processed:.1f}%")
    if failed:
        print(f"\nFailed images ({len(failed)}):")
        for name, error in failed:
            print(f"- {name}: {error}")

def main():
    static_dir = Path('static/images')
    if not static_dir.exists():
        print(f"Error: Directory {static_dir} does not exist!")
        sys.exit(1)

    print("Starting image compression...")
    print("Processing player images...")
    process_directory(static_dir / 'players')
    
    print("\nProcessing flag images...")
    process_directory(static_dir / 'flags')

if __name__ == "__main__":
    main() 