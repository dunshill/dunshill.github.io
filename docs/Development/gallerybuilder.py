import sys
from json import loads, dumps
from os import path, listdir, makedirs
from os.path import join, isfile, exists
from PIL import Image
import datetime
import functools

# stolen from https://stackoverflow.com/a/30462851/3447936
def image_transpose_exif(im):
    """
        Apply Image.transpose to ensure 0th row of pixels is at the visual
        top of the image, and 0th column is the visual left-hand side.
        Return the original image if unable to determine the orientation.
        As per CIPA DC-008-2012, the orientation field contains an integer,
        1 through 8. Other values are reserved.
    """

    exif_orientation_tag = 0x0112
    exif_transpose_sequences = [                   # Val  0th row  0th col
        [],                                        #  0    (reserved)
        [],                                        #  1   top      left
        [Image.FLIP_LEFT_RIGHT],                   #  2   top      right
        [Image.ROTATE_180],                        #  3   bottom   right
        [Image.FLIP_TOP_BOTTOM],                   #  4   bottom   left
        [Image.FLIP_LEFT_RIGHT, Image.ROTATE_90],  #  5   left     top
        [Image.ROTATE_270],                        #  6   right    top
        [Image.FLIP_TOP_BOTTOM, Image.ROTATE_90],  #  7   right    bottom
        [Image.ROTATE_90],                         #  8   left     bottom
    ]

    try:
        seq = exif_transpose_sequences[im._getexif()[exif_orientation_tag]]
        # print(seq)
    except Exception:
        return im.copy()
    else:
        return functools.reduce(type(im).transpose, seq, im.copy())


def main():
    if (len(sys.argv) != 3):
        print("gallerybuilder <inpath> <outpath>")
        return

    # get options
    inpath = sys.argv[1]
    outpath = sys.argv[2]

    # get files
    files = [f for f in listdir(inpath) if isfile(join(inpath, f))]

    # create imagedata array for PIG
    image_data = []

    # process files
    for file in files:

        # create image object
        try:
            image = Image.open(join(inpath, file))
        except Exception:
            print(f"{file} is not an image")
            continue

        # create various image heights (20, 100, 250, 500, full)
        # save in outdir
        aspect_ratio = None
        for size in [20, 100, 250, 500, 1024]:
            ratio = size / image.height
            # print(ratio)
            # get transposed copy
            resized = image_transpose_exif(image)
            aspect_ratio = resized.width/resized.height
            resized.thumbnail((image.width * ratio, image.height * ratio), Image.ANTIALIAS)
            resizedpath = join(outpath, f'img/{size}/')
            if not exists(resizedpath):
                makedirs(resizedpath)
            resized.save(join(resizedpath, file))

        # append file info for image_data
        image_data.append({'filename': file, 'aspectRatio':aspect_ratio})

        # create full size image file
        try:
            image_date = datetime.datetime.strptime(image._getexif()[36867], "%Y:%m:%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            image_date = ""
            continue
        full_size_html = \
            f'---\n' \
            f'layout: post\n' \
            f'title: "{file}"\n' \
            f'date: "{image_date}"\n' \
            f'exclude: true\n' \
            f'---\n' \
            f'<img src="/assets/img/1024/{file}"></img>'
        if not exists(join(outpath, 'html')):
            makedirs(join(outpath, 'html'))
        full_size_html_file = open(join(outpath, f'html/{file}.html'), 'w')
        full_size_html_file.write(full_size_html)
        full_size_html_file.close()


    # create PIG data and instance
    gallery_data = f"var imageData = {dumps(image_data)};"

    # create gallery_data include file
    out_html = open(join(outpath, 'gallery_data.html'), 'w')
    out_html.write(gallery_data)
    out_html.close()


if __name__ == "__main__":
    main()