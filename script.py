import math
import sys
from PIL import Image
from urllib import request
from math import cos, sin, pi, log, atan, exp, floor
from urllib import request
from PIL import Image

EARTHRADIUS = 6378137
MINLAT = -85.05112878
MAXLAT = 85.05112878
MINLON = -180.0
MAXLON = 180.0
MAXLEVEL = 23

def clip(n, minVal, maxVal):
    return min(max(n, minVal), maxVal);

def map_size(levelOfDetail):
    return 256 << levelOfDetail

def ground_resolution(lat, levelOfDetail):
    lat = clip(lat, MINLAT, MAXLAT)
    return cos(lat * pi / 180) * 2 * pi * EARTHRADIUS / map_size(levelOfDetail)

def mapScale(lat, levelOfDetail, screenDpi):
    return ground_resolution(lat, levelOfDetail) * screenDpi / 0.0254;

def lat_long_to_pixelXY(lat, lon, levelOfDetail):
    lat = clip(lat, MINLAT, MAXLAT)
    lon = clip(lon, MINLON, MAXLON)
    x = (lon + 180) / 360;
    sinLat = sin(lat * pi / 180)
    y = 0.5 - log((1 + sinLat) / (1 - sinLat)) / (4 * pi)
    mapSize = map_size(levelOfDetail)
    pixelX = floor(clip(x * mapSize + 0.5, 0, mapSize - 1))
    pixelY = floor(clip(y * mapSize + 0.5, 0, mapSize - 1))
    return pixelX, pixelY

def pixelXY_to_lat_long(pixelX, pixelY, levelOfDetail):
    mapSize = map_size(levelOfDetail)
    x = (clip(pixelX, 0, mapSize - 1) / mapSize) - 0.5
    y = 0.5 - (clip(pixelY, 0, mapSize - 1) / mapSize)
    lat = 90 - 360 * atan(exp(-y * 2 * pi)) / pi
    lon = 360 * x
    return lat, lon

def pixelXY_to_tileXY(pixelX, pixelY):
    tileX = floor(pixelX / 256)
    tileY = floor(pixelY / 256)
    return tileX, tileY

def tileXY_to_pixelXY(tileX, tileY):
    pixelX = tileX * 256
    pixelY = tileY * 256
    return pixelX, pixelY

def tileXY_to_quad_key(tileX, tileY, levelOfDetail):
    quad_key = ""
    i = levelOfDetail
    while (i > 0):
        digit = '0'
        mask = 1 << (i - 1)
        if ((tileX & mask) != 0):
            digit = chr(ord(digit) + 1)
        if ((tileY & mask) != 0):
            digit = chr(ord(digit) + 1)
            digit = chr(ord(digit) + 1)
        quad_key+=digit
        i-=1
    return quad_key

def quad_key_to_tileXY(quad_key, tileX, tileY):
    tileX = 0
    tileY = 0
    levelOfDetail = len(quad_key)
    i = levelOfDetail
    while (i > 0):
        mask = 1 << (i - 1)
        if (quad_key[levelOfDetail - i] == '0'):
            continue
        elif (quad_key[levelOfDetail - i] == '1'):
            tileX |= mask
        elif (quad_key[levelOfDetail - i] == '2'):
            tileY |= mask
        elif (quad_key[levelOfDetail - i] == '3'):
            tileX |= mask
            tileY |= mask
        i-=1

def get_image(quadkey):
    url= "http://h0.ortho.tiles.virtualearth.net/tiles/h%s.jpeg?g=131&" % (quadkey)
    with request.urlopen(url) as file:
        return Image.open(file)

def find_aerial_image(box_lat_lon, tilediff):
    currLevel = 0
    while (currLevel < 23):
        x_pixel1, y_pixel1 = lat_long_to_pixelXY(box_lat_lon[0][0], box_lat_lon[0][1], currLevel)
        x_pixel2, y_pixel2 = lat_long_to_pixelXY(box_lat_lon[1][0], box_lat_lon[1][1], currLevel)
        min_x_pixel = min(x_pixel1, x_pixel2)
        max_x_pixel = max(x_pixel1, x_pixel2)
        min_y_pixel = min(y_pixel1, y_pixel2)
        max_y_pixel = max(y_pixel1, y_pixel2)
        x_tile1, y_tile1 = pixelXY_to_tileXY(min_x_pixel, min_y_pixel)
        x_tile2, y_tile2 = pixelXY_to_tileXY(max_x_pixel, max_y_pixel)
        if (abs(x_tile1 - x_tile2) >= tilediff and abs(y_tile1 - y_tile2) >= tilediff):
            stitch_and_crop_image(box_lat_lon, [[min_x_pixel, min_y_pixel], [max_x_pixel, max_y_pixel]], x_tile1, y_tile1, x_tile2, y_tile2, currLevel, tilediff)
            break
        currLevel += 1

def stitch_and_crop_image(box_lat_lon, pixels, x_tile1, y_tile1, x_tile2, y_tile2, level, tilediff):
    min_x_tile = min(x_tile1, x_tile2)
    max_x_tile = max(x_tile1, x_tile2)
    min_y_tile = min(y_tile1, y_tile2)
    max_y_tile = max(y_tile1, y_tile2)
    final_image = Image.new('RGB', ((max_x_tile - min_x_tile + 1) * 256, (max_y_tile - min_y_tile + 1) * 256))
    for i in range(min_x_tile, max_x_tile+1):
        for j in range(min_y_tile, max_y_tile+1):
            quad_key = tileXY_to_quad_key(i, j, level)
            image = get_image(quad_key)
            if (image == Image.open('./empty_image.png') and tilediff > 1):
                print("Missing Image with Tile Diff: " + str(tilediff) + ", moving to lower resolution.")
                find_aerial_image(box_lat_lon, tilediff-1)
                return
            else:
                final_image.paste(image, ((i - min_x_tile) * 256, (j - min_y_tile) * 256))

    tilePixelX, tilePixelY = tileXY_to_pixelXY(min_x_tile, min_y_tile)
    cropped_image = final_image.crop((pixels[0][0] - tilePixelX, pixels[0][1] - tilePixelY , pixels[1][0] - tilePixelX, pixels[1][1] - tilePixelY))
    cropped_image.show()
    return cropped_image

if __name__ == '__main__':
    if (len(sys.argv) < 5):
        print("Please supply the lat lon box. Usage: python3 script.py [lat1] [lon1] [lat2] [lon2] [tilediff]")
        exit(0)
    box_lat_lon = [[float(sys.argv[1]), float(sys.argv[2])], [float(sys.argv[3]), float(sys.argv[4])]]
    tiles = 5
    if (len(sys.argv) > 5):
        tiles = int(sys.argv[5])
    find_aerial_image(box_lat_lon, tiles)
