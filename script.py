import math
from math import cos, sin, pi, log, atan, exp, floor
from urllib import request
from PIL import Image

EARTHRADIUS = 6378137
MINLAT = -85.05112878
MAXLAT = 85.05112878
MINLON = -180.0
MAXLON = 180.0

def clip(n, minVal, maxVal):
    return min(max(n, minVal), maxVal);

def map_size(levelOfDetail):
    return 256 << level

def ground_resolution(lat, levelOfDetail):
    lat = clip(lat, MINLAT, MAXLAT)
    return cos(lat * pi / 180) * 2 * pi * EARTHRADIUS / map_size(levelOfDetail)

def mapScale(lat, levelOfDetail, screenDpi):
    return ground_resolution(lat, levelOfDetail) * screenDpi / 0.0254;

def lat_long_to_pixelXY(lat, lon, levelOfDetail):
    lat = Clip(lat, MINLAT, MAXLAT)
    lon = Clip(lon, MINLON, MAXLON)
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
        
def download_image(quadkey):
    url= "http://h0.ortho.tiles.virtualearth.net/tiles/h%s.jpeg?g=131&" % (quadkey)
    with request.urlopen(url) as file:
            return Image.open(file)
        
        
 def main():
    lat1,lon1,lat2,lon2 = float(sys.argv[0]),float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3])
